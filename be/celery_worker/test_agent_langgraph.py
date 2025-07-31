import os
import sys
import json
import duckdb
from neo4j import GraphDatabase
from typing import TypedDict, Optional, List, Literal, Any

from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
# from langchain_google_genai import GoogleGenerativeAIError

# Set Langchain debug 
os.environ['LANGCHAIN_DEBUG'] = "true"

class Filter(BaseModel):
    field: str = Field(..., description="The field/property name from the database schema or inferred from message to apply the filter on. Must match a name in the provided schemas.")
    operator: Literal['=', '!=', '>', '<', '>=', '<=', 'LIKE', 'IN'] = Field(..., description="The comparison operator.")
    value: str = Field(..., description="The value to compare against, can be text or number or float, anything. Eg. 'Iphone 14 Pro Max', 1000, 99.99 ...")

class CoreEntity(BaseModel):
    entity_name: str = Field(..., description="The name of the entity/node/table (e.g., 'Product', 'Category'). Must exist in the database schemas. Set to None if no specific entity is targeted.")
    filters: List[Filter] = Field(default_factory=list, description="A list of filters to apply to this entity.")

class Calculation(BaseModel):
    calculation_type: Literal['COUNT', 'AVG', 'SUM', 'MIN', 'MAX'] = Field(..., description="The type of aggregation to perform.")
    target_entity: str = Field(..., description="The entity on which the calculation is performed (e.g., 'Product').")
    target_field: Optional[str] = Field(None, description="The specific field for the calculation (e.g., 'price_actual' for AVG). Not needed for COUNT(*). Must match a field in the schema.")
    group_by: Optional[str] = Field(None, description="The entity or field to group the results by (e.g., 'Category').")
    
class Relation(BaseModel):
    source: str = Field(..., description="The starting entity/node name (e.g., 'Product'). Must exist in the schemas.")
    target: str = Field(..., description="The ending entity/node name (e.g., 'Category'). Must exist in the schemas.")
    relation_name: str = Field(..., description="The name of the relationship (e.g., 'BELONGS_TO', 'SELLS'). Must exist in the Neo4j schema or be inferable from foreign keys in DuckDB.")

class QueryStructure(BaseModel):
    targets: List[CoreEntity] = Field(..., description="List of main entities the user wants to retrieve or filter on.")
    calculations: List[Calculation] = Field(default_factory=list, description="List of aggregate calculations requested by the user.")
    relations: List[Relation] = Field(default_factory=list, description="List of relationships to traverse.")
    ultimate_goal: str = Field(..., description="A summary of the user's final objective in plain language.")

class Step(BaseModel):
    step_id: int = Field(..., description="The sequential order of the step, starting from 1.")
    thought: str = Field(..., description="The reasoning behind why this step is necessary and why a specific tool was chosen.")
    tool_name: Literal['duckdb_query', 'neo4j_query'] = Field(..., description="The name of the tool to be used for this step.")
    tool_input: str = Field(..., description="A clear, natural language instruction for the tool. This will be used by another LLM to generate the actual SQL/Cypher query.")

class Plan(BaseModel):
    steps: List[Step] = Field(..., description="The sequence of steps to execute.")
    ultimate_goal: str = Field(..., description="A summary of the user's final objective in plain language.")

class GeneratedExecutableCode(BaseModel):
    """A container for the generated executable database query."""
    thought: str = Field(..., description="A brief thought process explaining why this specific query was generated to meet the user's goal.")
    chosen_tool: Literal['duckdb_query', 'neo4j_query'] = Field(..., description="The tool that will execute the query.") 
    query: str = Field(..., description="The actual query to be executed, either SQL for DuckDB or Cypher for Neo4j. This should NOT be a Python code block.")

# --- Schemas ---
duckdb_schema = json.dumps({'categories': [('id', 'INTEGER'), ('name', 'VARCHAR')], 'delivery': [('id', 'INTEGER'), ('name', 'VARCHAR'), ('w_date', 'VARCHAR')], 'product_categories': [('product_id', 'INTEGER'), ('category_id', 'INTEGER')], 'product_delivery': [('product_id', 'INTEGER'), ('delivery_id', 'INTEGER')], 'products': [('id', 'INTEGER'), ('original_id', 'VARCHAR'), ('title', 'VARCHAR'), ('price_original', 'DECIMAL(15,2)'), ('specification', 'VARCHAR'), ('item_rating', 'DECIMAL(3,2)'), ('price_actual', 'DECIMAL(15,2)'), ('sitename', 'VARCHAR'), ('total_rating', 'BIGINT'), ('total_sold', 'BIGINT'), ('pict_link', 'VARCHAR'), ('favorite', 'INTEGER'), ('shop_id', 'INTEGER')], 'shops': [('id', 'INTEGER'), ('seller_name', 'VARCHAR')]}, indent=2)
neo4j_schema = json.dumps({'nodes': [{'name': 'Shop', 'properties': ['seller_name']}, {'name': 'Category', 'properties': ['name']}, {'name': 'Product', 'properties': ['title', 'price_actual']}], 'relationships': [('Shop', 'SELLS', 'Product'), ('Product', 'BELONGS_TO', 'Category')]}, indent=2)

class Extractor:
    def __init__(self, model):
        # Prompts and model are now passed in for better reusability
        self.model = model
        extractor_prompt="""You are an expert system that analyzes user requests about a database in Vietnamese.
            Your primary task is to deconstruct a user's message into a structured JSON format defined by the `QueryStructure` model.

            **Crucial Mapping Rules:**
            1.  **Semantic Search:** You MUST actively look for semantic similarities and synonyms between the user's query and the schema. Do not expect a direct 1:1 match.
            2.  **Use Descriptions:** Pay close attention to the `description` fields provided within the schemas. They contain vital clues and Vietnamese translations.
            3.  **Common Sense Mapping:** Use common knowledge. For example:
                - "đơn vị vận chuyển", "giao hàng", "shipping" -> map to the `delivery` table.
                - "sản phẩm", "mặt hàng", "item" -> map to the `products` table.
                - "cửa hàng", "người bán", "seller" -> map to the `shops` table.
                - "loại hàng", "danh mục" -> map to the `categories` table.
                ... Maybe you need to infer from context/message to map to the correct entity.
            4.  **Irrelevant Queries:** If the user's query is completely unrelated to products, sales, or categories (e.g., asking about the weather), the 'targets' list MUST be empty.

            **Database Schemas with Descriptions:**
            DuckDB Schema (for analytical queries, aggregations):
            {duckdb_schema}

            Neo4j Schema (for graph traversal, multi-hop relationships):
            {neo4j_schema}

            Your output MUST be a single, valid JSON object that conforms to the `QueryStructure` Pydantic model.
        """
        self.system_message = SystemMessage(
            content=extractor_prompt.format(duckdb_schema=duckdb_schema, neo4j_schema=neo4j_schema)
        )
        self.model = self.model.with_structured_output(QueryStructure)

    def ask(self, user_input: str):
        return self.model.invoke([self.system_message, HumanMessage(content=user_input)])

class Planner:
    def __init__(self, model):
        self.model = model
        planner_prompt = """You are an expert system that creates a step-by-step plan to fulfill a user's request, based on a structured `QueryStructure`.
            Your task is to generate a `Plan`.
            
            Guidelines:
            1.  **Analyze `QueryStructure`**: Understand the targets, calculations, and relations.
            2.  **Choose Tools**:
                - Use `duckdb_query` for aggregations (COUNT, AVG, SUM), filtering, and sorting on tabular data.
                - Use `neo4j_query` for traversing relationships (e.g., "products in a category", "shops that sell a product").
                - If a query is simple and can be done by both, prefer `duckdb_query`.
            3.  **Create Steps**: Break down the user's goal into logical steps. A simple query might only need one step.
            4.  **Tool Input**: The `tool_input` for each step should be a clear, natural language instruction for the CodeGenerator LLM.
            
            Your output MUST be a single, valid JSON object that conforms to the `Plan` Pydantic model.
        """
        self.system_message = SystemMessage(content=planner_prompt)
        self.model = self.model.with_structured_output(Plan)
        
    def ask(self, query_structure: QueryStructure):
        return self.model.invoke([self.system_message, HumanMessage(content=query_structure.model_dump_json())])

class CodeGenerator:
    def __init__(self, model):
        self.model = model
        generator_prompt = f"""
            You are an expert SQL and Cypher query developer. Your task is to generate a database query based on a given Plan.

            - DuckDB schema: {duckdb_schema}
            - Neo4j schema: {neo4j_schema}

            Instructions:
            1.  Analyze the user's `ultimate_goal` from the provided `Plan`.
            2.  Examine the `steps` to understand the logic.
            3.  Choose the tool (`duckdb_query` or `neo4j_query`) specified in the FIRST step of the plan. For this system, assume only one step is needed.
            4.  Generate a single, valid JSON object conforming to the `GeneratedExecutableCode` Pydantic model.
            5.  The "query" field MUST contain ONLY the SQL or Cypher query string. It MUST NOT be a Python code block.
            6.  Ensure the entity, field, and relation names in your query EXACTLY match the provided schemas.
            7.  Ensure the query is executable, meaning it HAVE TO correct the syntax corresponding to DuckDB or Cypher Query. It cannot be wrong anyway.
        """
        self.system_message = SystemMessage(content=generator_prompt)
        self.model = self.model.with_structured_output(GeneratedExecutableCode)

    def ask(self, plan: Plan):
        return self.model.invoke([self.system_message, HumanMessage(content=plan.model_dump_json())])
    
class CodeFixer:
    def __init__(self, model):
        self.model = model
        fixer_prompt = (
            "You are an expert developer. Given a database query string (neo4j cypher query or dudckdb sql query) and its error message, "
            "your task is to fix the query so it no longer produces the error."
            "Respond ONLY with the corrected query string, nothing else."
        )
        self.system_message = SystemMessage(content=fixer_prompt)

    def ask(self, code, error):
        human_message = {
            'code': code,
            'error': error
        }
        return self.model.invoke([self.system_message, HumanMessage(content=json.dumps(human_message))])


class GraphState(TypedDict):
    """Represents the state of our graph."""
    user_query: str
    query_structure: Optional[QueryStructure]
    plan: Optional[Plan]
    generated_code: Optional[GeneratedExecutableCode]
    execution_result: Any
    final_answer: str
    error: str


def extract_node(state: GraphState):
    """Extracts structured information from the user query."""
    print("---NODE: EXTRACT---")
    user_query = state['user_query']
    query_structure = extractor.ask(user_query)
    print(f"Extracted Structure: \n{json.dumps(query_structure.model_dump(), indent=2, ensure_ascii=False)}")
    return {"query_structure": query_structure}

def plan_node(state: GraphState):
    """Generates a plan to answer the user query."""
    print("---NODE: PLAN---")
    query_structure = state['query_structure']
    plan = planner.ask(query_structure)
    print(f"Generated Plan: \n{json.dumps(plan.model_dump(), indent=2, ensure_ascii=False)}")
    return {"plan": plan}

def generate_code_node(state: GraphState):
    """Generates the database query."""
    print("---NODE: GENERATE CODE---")
    plan = state['plan']
    generated_code = code_generator.ask(plan)
    print(f"Generated Code: \n{json.dumps(generated_code.model_dump(), indent=2, ensure_ascii=False)}")
    return {"generated_code": generated_code}

def execute_code_node(state: GraphState):
    """Executes the query safely on the appropriate database."""
    print("---NODE: EXECUTE CODE---")
    code_to_run = state['generated_code']
    tool = code_to_run.chosen_tool
    query = code_to_run.query
    
    result = None
    error = None
    
    try:
        if tool == 'duckdb_query':
            print(f"Executing DuckDB Query: {query}")
            conn = duckdb.connect("celery_worker/shopee_ecommerce_final.db", read_only=True)
            result = conn.execute(query).df() # Fetch as pandas DataFrame
            conn.close()
            final_answer = f"Đây là kết quả từ truy vấn:\n{result.to_markdown()}"

        elif tool == 'neo4j_query':
            print(f"Executing Neo4j Query: {query}")
            driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "rikai123"))
            with driver.session() as session:
                query_result = session.run(query)
                # Convert Neo4j result to a more readable format
                result_list = [record.data() for record in query_result]
                result = json.dumps(result_list, indent=2, ensure_ascii=False)
            driver.close()
            final_answer = f"Đây là kết quả từ truy vấn:\n{result}"

        else:
            error = f"Lỗi: Công cụ '{tool}' không được hỗ trợ."

    except Exception as e:
        error = f"Đã xảy ra lỗi khi thực thi truy vấn: {e}"

    if error:
        print(f"Execution Error: {error}")
        return {"final_answer": error, "got_error": True}
    else:
        print(f"Execution Result:\n{result}")
        return {"execution_result": result, "final_answer": final_answer}
    
def fix_code_node(state: GraphState):
    """Fix the query string when error happen (syntax)"""
    print("---NODE: FIXING QUERY")
    error = state['error']
    code = state['generated_code']
    fixed_query = fixer.ask(code, error)
    print(f"Generated Code: \n{json.dumps(fixed_query.model_dump(), indent=2, ensure_ascii=False)}")
    return {"generated_code": fixed_query}


def handle_irrelevant_query_node(state: GraphState):
    """Handles queries that are not related to the database."""
    print("---NODE: HANDLE IRRELEVANT QUERY---")
    answer = "Xin lỗi, tôi là một trợ lý chuyên về dữ liệu sản phẩm và bán hàng. Tôi không thể tìm thấy nội dung liên quan đến câu hỏi này hoặc dữ liệu hiện tại không hỗ trợ các câu hỏi của bạn, vui lòng thử lại câu hỏi khác."
    return {"final_answer": answer}



def route_query(state: GraphState) -> Literal["plan", "handle_irrelevant"]:
    """
    Routes the query to the appropriate next step based on the extractor's output.
    """
    print("---ROUTER: route_query---")
    query_structure = state['query_structure']
    # If the extractor failed to identify any core entity, the query is likely irrelevant.
    if not query_structure.targets:
        print("Decision: Query is IRRELEVANT. Routing to handler.")
        return "handle_irrelevant"
    else:
        print("Decision: Query is RELEVANT. Routing to planner.")
        return "plan"


if __name__ == "__main__":
    # os.environ['GOOGLE_API_KEY'] = "AIzaSyC7O5-fnnmGHLMCZkW8DWeMqWobbHXZexc"
    os.environ['GOOGLE_API_KEY'] = "AIzaSyApW1tlHyEXjBMItv6TN7V-8U9L7azedWI"
    os.environ['LANGSMITH_PROJECT'] = "llm_system"
    os.environ['LANGSMITH_ENDPOINT'] = "https://api.smith.langchain.com"
    os.environ['LANGSMITH_API_KEY'] = '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'
    os.environ['LANGCHAIN_TRACING'] = "false"

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-lite", 
        temperature=0,
        timeout=30,  
    )

    extractor = Extractor(model=llm)
    planner = Planner(model=llm)
    code_generator = CodeGenerator(model=llm)
    fixer = CodeFixer(model=llm)

    workflow = StateGraph(GraphState)

    workflow.add_node("extract", extract_node)
    workflow.add_node("plan", plan_node)
    workflow.add_node("generate_code", generate_code_node)
    workflow.add_node("execute_code", execute_code_node)
    workflow.add_node("handle_irrelevant_query", handle_irrelevant_query_node)
    workflow.add_node("fix_code", fix_code_node)

    workflow.set_entry_point("extract")

    workflow.add_conditional_edges(
        "extract",
        route_query,
        {
            "plan": "plan",
            "handle_irrelevant": "handle_irrelevant_query",
        },
    )
    workflow.add_edge("plan", "generate_code")
    workflow.add_edge("generate_code", "execute_code")
    
    # End points
    workflow.add_conditional_edges(
        'execute_code',
        lambda state: 'fix_code' if state.get('got_error', False) else END,
        {
            'fix_code': 'fix_code',
            END: END,
        }
    )

    workflow.add_edge('fix_code', 'execute_code')

    workflow.add_edge("handle_irrelevant_query", END)


    # Compile the graph
    app = workflow.compile()

    # --- Run the graph with different queries ---
    print("\n\n" + "="*50)
    print("RUNNING TEST CASE 2: RELEVANT QUERY")
    print("="*50)
    # Lưu ý: Cần có file 'shopee_ecommerce_final.db' trong cùng thư mục
    relevant_query = "Danh sách sản phẩm là hàng Việt Nam (có Vietnam trong tên sản phẩm)"
    inputs = {"user_query": relevant_query}
    # Set a timeout for the LLM calls (in seconds)

    try:
        final_state = app.invoke(inputs, config={"timeout": 30})  # 60 seconds timeout
    except Exception as e:
        final_state = {"final_answer": f"Lỗi: Quá thời gian chờ của LLM. Chi tiết: {e}"}
    print("\n---FINAL ANSWER---")
    print(final_state['final_answer'])