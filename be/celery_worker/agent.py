import os
import sys
from langchain.chat_models import init_chat_model
from langchain.schema import SystemMessage, HumanMessage
from neo4j import GraphDatabase
import duckdb
from pydantic import BaseModel, Field

sys.path.append(os.path.join(os.path.dirname(__file__), '../'))
from core.config import settings 

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "rikai123"))
conn = duckdb.connect(r'celery_worker\shopee_ecommerce_final.db')

# Tìm doanh số lớn nhất trong một tháng mà nhà vận chuyển

# get some data from conn
def get_data_from_conn(query: str):
    """
    Execute a query on the DuckDB connection and return the results.
    """
    try:
        result = conn.execute(query).fetchall()
        return result
    except Exception as e:
        print(f"Error executing query: {e}")
        return None
result = get_data_from_conn("SHOW TABLES")
print(result)

class Entity(BaseModel):
    entity: str = Field(..., description="Entity from user message, can be extracted/inferenced from data schema and map with data model and mapped back to the same data model, set to None if cannot be inferred")
    field: str = Field(..., description="Field of Entity extracted, can be extracted/inferenced from data schema map with data properties mapped back to the same model properties, set to None if cannot be inferred")
    requirements: str = Field(..., description="Condition or constraint or calculation or statistic of the field extracted from user message, used to comprehensive query, set to None if Entity or field cannot be mapped with data schema")

class Relation(BaseModel):
    source_entity: str = Field(..., description="The starting entity which user are looking for relation")
    related_entity: str = Field(..., description="The related entity that user wants to find relation with")
    relation: str = Field(..., description="The description of relation between source_entity and related_entity, can be extracted/inferenced from data schema, set to None if cannot be inferred")
    can_find: bool = Field(..., description="Whether the relation can be inferred to exist relation or not, set to False if cannot be inferred")

class MessageExtractor(BaseModel):
    entities: list[Entity] = Field(..., description="List of Entity extracted from user message")
    relations: list[Relation] = Field(..., description="List of Relation extracted from user message") 


class Chatbot:
    def __init__(self):
        self.model = init_chat_model(
            "gemini-2.0-flash", 
            model_provider="google_genai", 
            google_api_key="AIzaSyCnZQ9fBebxFrzYT9bgmba8OTQYqcfx1NY"
        )
        
   
        duckdb_schema = """ 
        {'categories': [
            {'Column': 'id', 'Type': 'INTEGER'},
            {'Column': 'name', 'Type': 'VARCHAR'}
        ],
        'delivery': [
            {'Column': 'id', 'Type': 'INTEGER'},
            {'Column': 'name', 'Type': 'VARCHAR'},
            {'Column': 'w_date', 'Type': 'VARCHAR'}
        ],
        'product_categories': [
            {'Column': 'product_id', 'Type': 'INTEGER'},
            {'Column': 'category_id', 'Type': 'INTEGER'}
        ],
        'product_delivery': [
            {'Column': 'product_id', 'Type': 'INTEGER'},
            {'Column': 'delivery_id', 'Type': 'INTEGER'}
        ],
        'products': [
            {'Column': 'id', 'Type': 'INTEGER'},
            {'Column': 'original_id', 'Type': 'VARCHAR'},
            {'Column': 'title', 'Type': 'VARCHAR'},
            {'Column': 'price_original', 'Type': 'DECIMAL(15,2)'}, - Original price of the product
            {'Column': 'specification', 'Type': 'VARCHAR'},
            {'Column': 'item_rating', 'Type': 'DECIMAL(3,2)'}, - Average rating of the product
            {'Column': 'price_actual', 'Type': 'DECIMAL(15,2)'}, - Actual price of the product after discount
            {'Column': 'sitename', 'Type': 'VARCHAR'},
            {'Column': 'total_rating', 'Type': 'BIGINT'},
            {'Column': 'total_sold', 'Type': 'BIGINT'}, - Total products had been sold by the shop
            {'Column': 'pict_link', 'Type': 'VARCHAR'},
            {'Column': 'favorite', 'Type': 'INTEGER'}, - Total favorite marked by users
            {'Column': 'shop_id', 'Type': 'INTEGER'}
        ],
        'shops': [
            {'Column': 'id', 'Type': 'INTEGER'},
            {'Column': 'seller_name', 'Type': 'VARCHAR'}
        ]
        """

        neo4j_schema = """ 
        {
            'nodes': [
                {'name': 'Shop', 'indexes': [], 'constraints': []}, 
                {'name': 'Category', 'indexes': [], 'constraints': []}, 
                {'name': 'Product', 'indexes': [], 'constraints': []}, 
                {'name': 'Delivery', 'indexes': [], 'constraints': []}
            ], 
            'relationships': [
                ({'name': 'Product', 'indexes': [], 'constraints': []}, 'DELIVERED_BY', {'name': 'Delivery', 'indexes': [], 'constraints': []}), 
                ({'name': 'Shop', 'indexes': [], 'constraints': []}, 'SELLS', {'name': 'Product', 'indexes': [], 'constraints': []}), 
                ({'name': 'Product', 'indexes': [], 'constraints': []}, 'BELONGS_TO', {'name': 'Category', 'indexes': [], 'constraints': []})
            ]
        """

        content=""" You are a helpful Data Analyst and Researcher. Given the neo4j and DuckDB database schema, 
                    your mission is to breakdown the message from user for comprehensive understanding, 
                    extract the entities and relations, and return them in a structured format. 

                    DuckDB schema: {duckdb_schema}

                    Neo4j schema: {neo4j_schema}
        """
        self.system_message = SystemMessage(
            content=content.format(duckdb_schema=duckdb_schema, neo4j_schema=neo4j_schema)
        )

        self.model = self.model.with_structured_output(MessageExtractor)

    # def ask(self, user_input: str):
    #     messages = [
    #         self.system_message,
    #         HumanMessage(content=user_input)
    #     ]
    #     for chunk in self.model.stream(messages):
    #         yield chunk 

    def ask(self, user_input: str):
        # Print out response 
        messages = [
            self.system_message,
            HumanMessage(content=user_input)
        ]
        response = self.model.invoke(messages)
          
        # Get token usage information
        if hasattr(response, 'response_metadata') and 'token_usage' in response.response_metadata:
            token_usage = response.response_metadata['token_usage']
            print(f"Token usage: {token_usage}")
        
        return MessageExtractor.model_validate(response)  # Validate and return structured response
    
# chatbot = Chatbot()

# response = chatbot.ask("Tôi đang xem cái 'Laptop Dell XPS 15'. Bạn tìm giúp tôi vài cái laptop khác cùng loại với nó, nhưng chỉ lấy từ những danh mục thực sự 'lớn' (tức là có nhiều sản phẩm ấy). Với mỗi cái laptop bạn gợi ý, cho tôi biết luôn giá trung bình của cả cái danh mục đó là bao nhiêu để tôi so sánh xem nó đắt hay rẻ so với mặt bằng chung")
# print(response)