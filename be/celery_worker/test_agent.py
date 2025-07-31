from langchain_core.tools import tool
import os
import sys
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from typing import Literal, Optional, List
from langchain_community.callbacks import get_openai_callback
from langgraph.prebuilt import create_react_agent
import duckdb
from neo4j import GraphDatabase


class Filter(BaseModel):
    """Represents a filter condition on a field."""
    field: str = Field(..., description="The field/property name from the database schema or inferred from message to apply the filter on. Must match a name in the provided schemas.")
    operator: Literal['=', '!=', '>', '<', '>=', '<=', 'LIKE', 'IN'] = Field(..., description="The comparison operator.")
    value: str = Field(..., description="The value to compare against, can be text or number or float, anything. Eg. 'Iphone 14 Pro Max', 1000, 99.99 ...")

class CoreEntity(BaseModel):
    """Represents a core entity the user is interested in, with its filters."""
    entity_name: str = Field(..., description="The name of the entity/node/table (e.g., 'Product', 'Category'). Must exist in the database schemas. Set to None if no specific entity is targeted.")
    filters: List[Filter] = Field(default_factory=list, description="A list of filters to apply to this entity.")

class Calculation(BaseModel):
    """Represents a statistical or aggregate calculation required by the user."""
    calculation_type: Literal['COUNT', 'AVG', 'SUM', 'MIN', 'MAX'] = Field(..., description="The type of aggregation to perform.")
    target_entity: str = Field(..., description="The entity on which the calculation is performed (e.g., 'Product').")
    target_field: Optional[str] = Field(None, description="The specific field for the calculation (e.g., 'price_actual' for AVG). Not needed for COUNT(*). Must match a field in the schema.")
    group_by: Optional[str] = Field(None, description="The entity or field to group the results by (e.g., 'Category').")
    
class Relation(BaseModel):
    """Represents a relationship between two entities that needs to be traversed."""
    source: str = Field(..., description="The starting entity/node name (e.g., 'Product'). Must exist in the schemas.")
    target: str = Field(..., description="The ending entity/node name (e.g., 'Category'). Must exist in the schemas.")
    relation_name: str = Field(..., description="The name of the relationship (e.g., 'BELONGS_TO', 'SELLS'). Must exist in the Neo4j schema or be inferable from foreign keys in DuckDB.")

class QueryStructure(BaseModel):
    """
    A structured representation of the user's query, broken down into targets, calculations, and relations.
    This structure is designed to be the input for a subsequent decision-making module.
    """
    targets: List[CoreEntity] = Field(..., description="List of main entities the user wants to retrieve or filter on.")
    calculations: List[Calculation] = Field(default_factory=list, description="List of aggregate calculations requested by the user. This is a strong indicator for using an analytical database like DuckDB.")
    relations: List[Relation] = Field(default_factory=list, description="List of relationships to traverse. This is a strong indicator for using a graph database like Neo4j.")
    ultimate_goal: str = Field(..., description="A summary of the user's final objective in plain language.")

class Step(BaseModel):
    """Represents a single step in a multi-step execution plan."""
    step_id: int = Field(..., description="The sequential order of the step, starting from 1.")
    thought: str = Field(..., description="The reasoning behind why this step is necessary and why a specific tool was chosen.")
    tool_name: Literal['duckdb_query', 'neo4j_query'] = Field(..., description="The name of the tool to be used for this step.")
    tool_input: str = Field(..., description="A clear, natural language instruction for the tool. This will be used by another LLM to generate the actual SQL/Cypher query.")

class Plan(BaseModel):
    """A complete, step-by-step plan to fulfill the user's request."""
    steps: List[Step] = Field(..., description="The sequence of steps to execute.")
    ultimate_goal: str = Field(..., description="A summary of the user's final objective in plain language. This should match the ultimate goal in the QueryStructure.")

class GeneratedExecutableCode(BaseModel):
    """A container for the generated executable code."""
    chosen_tool: Literal['duckdb_query', 'neo4j_query'] = Field(..., description="The tool that will execute the code.") 
    code: str = Field(..., description="The actual code to be executed, either SQL for DuckDB or Cypher for Neo4j.")

duckdb_schema = """ 
{'categories': [('id', 'INTEGER'), ('name', 'VARCHAR')],
 'delivery': [('id', 'INTEGER'), ('name', 'VARCHAR'), ('w_date', 'VARCHAR')],
 'product_categories': [('product_id', 'INTEGER'), ('category_id', 'INTEGER')],
 'product_delivery': [('product_id', 'INTEGER'), ('delivery_id', 'INTEGER')],
 'products': [('id', 'INTEGER'), ('original_id', 'VARCHAR'),
              ('title', 'VARCHAR'), ('price_original', 'DECIMAL(15,2)'),
              ('specification', 'VARCHAR'), ('item_rating', 'DECIMAL(3,2)'),
              ('price_actual', 'DECIMAL(15,2)'), ('sitename', 'VARCHAR'),
              ('total_rating', 'BIGINT'), ('total_sold', 'BIGINT'),
              ('pict_link', 'VARCHAR'), ('favorite', 'INTEGER'),
              ('shop_id', 'INTEGER')],
 'shops': [('id', 'INTEGER'), ('seller_name', 'VARCHAR')]}
"""

neo4j_schema = """ 
{'nodes': [{'name': 'Shop', 'properties': ['seller_name']}, {'name': 'Category', 'properties': ['name']}, {'name': 'Product', 'properties': ['title', 'price_actual']}], 
'relationships': [('Shop', 'SELLS', 'Product'), ('Product', 'BELONGS_TO', 'Category')]}
"""

class Extractor:
    def __init__(self):
        self.model = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=os.environ.get("GOOGLE_API_KEY"),
        )

        extractor_prompt="""You are an expert system that analyzes user requests about a database.
            Your task is to deconstruct a user's message into a structured JSON format defined by the `QueryStructure` model.
            Carefully map user intent to the provided database schemas. If a user's term cannot be confidently mapped to an entity, field, or relation in the schemas, you MUST set its value to None or an empty list.

            Database Schemas:
            DuckDB Schema (for analytical queries, aggregations):
            {duckdb_schema}

            Neo4j Schema (for graph traversal, multi-hop relationships):
            {neo4j_schema}

            Follow these steps:
            1.  **Identify Targets (`TargetEntity`)**: What are the main objects the user is asking about (e.g., 'Product', 'Category')? What specific conditions or filters (`Filter`) are applied to them (e.g., product title is 'Laptop Dell XPS 15')?
            2.  **Identify Calculations (`Calculation`)**: Does the user ask for statistics like "how many", "average", "total", "most popular"? Map these to `COUNT`, `AVG`, `SUM`, etc. Note what is being calculated (e.g., `Product`) and how it's grouped (e.g., by `Category`).
            3.  **Identify Relations (`Relation`)**: Does the user want to find things connected to other things (e.g., products 'in a' category, shops 'that sell' a product)? Map these to the relationships in the schemas.
            4.  **Summarize Goal (`ultimate_goal`)**: Briefly describe what the user wants to achieve in the end.

            Your output MUST be a single, valid JSON object that conforms to the `QueryStructure` Pydantic model.
        """

        self.system_message = SystemMessage(
            content=extractor_prompt.format(duckdb_schema=duckdb_schema, neo4j_schema=neo4j_schema)
        )

        self.model = self.model.with_structured_output(QueryStructure)

    def ask(self, user_input: str):
        messages = [
            self.system_message,
            HumanMessage(content=user_input)
        ]
        with get_openai_callback() as cb:
            response = self.model.invoke(messages)
            print(f"Prompt Tokens: {cb.prompt_tokens}")
            print(f"Completion Tokens: {cb.completion_tokens}")
            print(f"Total Tokens: {cb.total_tokens}")
            print(f"Total Cost (USD): ${cb.total_cost:.10f}")
            return response
        
class Planner:
    def __init__(self):
        self.model = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=os.environ.get("GOOGLE_API_KEY"),
        )

        planner_prompt = """You are an expert system that creates a step-by-step plan to fulfill a user's request about a database.
            Your task is to generate a `Plan` consisting of multiple `Step`s, each with a clear thought process and tool input.
            Carefully analyze the user's request and the provided `QueryStructure` to create a logical sequence of steps.

            Given you 2 schemas of datase:
            DuckDB Schema :
            {duckdb_schema}
            Neo4j Schema:
            {neo4j_schema}

            Follow these steps:
            1.  **Understand the Query Structure**: Analyze the `QueryStructure` provided by the extractor. Identify the targets, calculations, and relations.
            2.  **Break Down into Steps**: For each target, calculation, or relation, create a step that explains why it is necessary and what tool will be used.
            3.  **Choose Tools**: Decide whether to use DuckDB or Neo4j based on the nature of the step:
                - Use DuckDB for analytical queries, aggregations, and statistics.
                - Use Neo4j for traversing relationships and multi-hop queries.
                - If a step is simple, both of duckdb or neo4j can be used then choose duckdb.
                - On case you consider, choolse DuckDB
            4.  **Define Tool Inputs**: For each step, provide a clear instruction for the tool (DuckDB or Neo4j) that will be used to execute it.
            5.  **Ensure Logical Flow**: The steps should follow a logical order that builds towards fulfilling the user's ultimate goal.
            6.  **Reinform about the Ultimate Goal**: Each step should contribute towards achieving the user's ultimate goal, which should be summarized at the end of the plan.

            Your output MUST be a single, valid JSON object that conforms to the `Plan` Pydantic model.
        """

        self.system_message = SystemMessage(content=planner_prompt)
        self.model = self.model.with_structured_output(Plan)

    def ask(self, query_structure: QueryStructure):
        messages = [
            self.system_message,
            HumanMessage(content=query_structure.model_dump_json())
        ]
        with get_openai_callback() as cb:
            response = self.model.invoke(messages)
            print(f"Prompt Tokens: {cb.prompt_tokens}")
            print(f"Completion Tokens: {cb.completion_tokens}")
            print(f"Total Tokens: {cb.total_tokens}")
            print(f"Total Cost (USD): ${cb.total_cost:.10f}")
            return response
        
class CodeGenerator:
    def __init__(self):
        self.model = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=os.environ.get("GOOGLE_API_KEY"),
        )

        generator_prompt = """
            You are an expert developer who generates executable Python code to query either DuckDB or Neo4j, based on a structured plan.

            DuckDB schema: {duckdb_schema}
            Neo4j schema: {neo4j_schema}

            You are given two connection statements:
            - Neo4j: driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "rikai123"))
            - DuckDB: conn = duckdb.connect("celery_worker/shopee_ecommerce_final.db")

            Instructions:
            1. Analyze the provided Plan and select the appropriate database:
                - Use DuckDB for analytical/statistical queries.
                - Use Neo4j for relationship/path queries.
                - If the step is simple, not any complex aggregation or relationship traversal, prefer DuckDB.
                - In case consider, choose DuckDB.
            2. If you need statistics about the numerous data, call the `data_stat` tool. Eg: If user need to know average price of products, or the lowest price product can have, you this tool.
            3. Generate a single, valid JSON object conforming to the `GeneratedExecutableCode` Pydantic model.
            4. The "code" field should contain the full Python code block to execute the query without comments, including connection and execution, CANNOT be different in entities name, field, relations with provided schemas.
            5. The code output MUST be generated for solving the ultimate goal of the user's request, which is provided in the Plan.
            6. The code output's name of entities, fields, and relations MUST exactly match the names in the provided schemas.
        """

        self.system_message = SystemMessage(
            content=generator_prompt.format(duckdb_schema=duckdb_schema, neo4j_schema=neo4j_schema)
        )
        self.model = self.model.bind_tools([self.data_stat])
        self.model = self.model.with_structured_output(GeneratedExecutableCode)


    def ask(self, plan: Plan):
        messages = [
            self.system_message,
            HumanMessage(content=plan.model_dump_json())
        ]
        with get_openai_callback() as cb:
            response = self.model.invoke(messages)
            print(f"Prompt Tokens: {cb.prompt_tokens}")
            print(f"Completion Tokens: {cb.completion_tokens}")
            print(f"Total Tokens: {cb.total_tokens}")
            print(f"Total Cost (USD): ${cb.total_cost:.10f}")
            return response

    @tool
    def data_stat(self) -> str:
        """A tool to get statistics about the numerous data in the database. Needed when model needs to find statistics about the data."""
        import pandas as pd 

        df = pd.read_csv('shopee_clean.csv')

        numeric_columns = df.select_dtypes(include=['number']).columns.tolist()

        stats = df[numeric_columns].describe().to_dict()

        print(f"Data statistics: {stats}")

        return stats

if __name__ == "__main__":

    os.environ['GOOGLE_API_KEY'] = "AIzaSyC7O5-fnnmGHLMCZkW8DWeMqWobbHXZexc"
    os.environ['LANGSMITH_PROJECT'] = "llm_system"
    os.environ['LANGSMITH_ENDPOINT'] = "https://api.smith.langchain.com"
    os.environ['LANGSMITH_API_KEY'] = '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'
    os.environ['LANGCHAIN_TRACING'] = "true"
    
    extractor = Extractor()
    planner = Planner()
    code_generator = CodeGenerator()

    user_query = "Có bao nhiêu sản phẩm cùng được bán bởi 2 shop khác nhau? Tên của sản phẩm đó là gì và có bao nhiêu sản phẩm đó đã được bán ra bởi mỗi shop"

    structured_response = extractor.ask(user_query)
    planner_response = planner.ask(structured_response)
    generated_code = code_generator.ask(planner_response)
    
    import json
    print(json.dumps(structured_response.model_dump(), indent=2, ensure_ascii=False))
    print(json.dumps(planner_response.model_dump(), indent=2, ensure_ascii=False))
    print(json.dumps(generated_code.model_dump(), indent=2, ensure_ascii=False))

    code = generated_code.code
    exec(code)