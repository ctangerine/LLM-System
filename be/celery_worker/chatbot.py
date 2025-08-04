import os
import sys
from langchain.chat_models import init_chat_model
from langchain.schema import SystemMessage, HumanMessage

sys.path.append(os.path.join(os.path.dirname(__file__), '../'))
from core.config import settings 

class Chatbot:
    def __init__(self):
        self.model = init_chat_model(
            "gemini-2.0-flash", 
            model_provider="google_genai", 
            google_api_key=settings.GOOGLE_API_KEY
        )
        self.system_message = SystemMessage(
            content="You are a helpful Assistant, your task is to answer user questions the best you can."
        )

    def ask(self, user_input: str):
        messages = [
            self.system_message,
            HumanMessage(content=user_input)
        ]
        for chunk in self.model.stream(messages):
            yield chunk 



# import json
# import re
# import pandas as pd
# from tabulate import tabulate

# from langchain_core.messages import SystemMessage, HumanMessage
# from langchain_google_genai import ChatGoogleGenerativeAI
# from neo4j import GraphDatabase
# import duckdb

# driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "rikai123"))
# conn = duckdb.connect('shopee_ecommerce_final.db', read_only=True)

# class DataChatbot:
#     """
#     Một chatbot phân tích dữ liệu thông minh, có khả năng:
#     1. Lựa chọn giữa DuckDB và Neo4j để trả lời câu hỏi.
#     2. Tự động sinh và thực thi mã truy vấn.
#     3. Diễn giải kết quả thành ngôn ngữ tự nhiên.
#     """

#     # Zero -shot prompt template cho việc sinh mã truy vấn
    
#     _CODE_GENERATION_PROMPT_TEMPLATE = """
#     You are an expert data analyst and a master of both SQL (for DuckDB) and Cypher (for Neo4j).
#     Your mission is to act as a "Reasoning and Acting" agent.

#     **CONTEXT:**
#     You have access to two databases containing Shopee e-commerce data:
#     1.  **DuckDB (Relational/OLAP):** Extremely fast for analytical queries, aggregations, filtering, and calculations over large columns of data. USE THIS FOR questions about statistics, trends, counting, averaging, and filtering large sets.
#     2.  **Neo4j (Graph Database):** Perfect for understanding relationships, finding paths, discovering patterns, and answering questions about connections. USE THIS FOR questions about recommendations, community detection, fraud rings, or how things are connected.

#     **DATABASE SCHEMAS:**

#     **1. DuckDB Schema:**
#     - `products(id, original_id, title, price_actual, item_rating, total_sold, shop_id)`
#     - `shops(id, seller_name)`
#     - `categories(id, name)`
#     - `delivery(id, name, w_date)`
#     - `product_categories(product_id, category_id)`
#     - `product_delivery(product_id, delivery_id)`
#     * Note: `total_sold` and `item_rating` are clean numeric types.

#     **2. Neo4j Schema:**
#     - Nodes: `(:Product)`, `(:Shop)`, `(:Category)`, `(:Delivery)`
#     - Properties on nodes are the same as DuckDB columns (e.g., `Product` has `id`, `title`, `price_actual`, `item_rating`, `total_sold`).
#     - Relationships:
#         - `(:Shop)-[:SELLS]->(:Product)`
#         - `(:Product)-[:BELONGS_TO]->(:Category)`
#         - `(:Product)-[:DELIVERED_BY]->(:Delivery)`
#     * Note: `total_sold` and `item_rating` might be strings (e.g., '14.3k', 'No ratings yet'). You MUST handle this in your Cypher query using functions like `toFloat()`, `coalesce()`, and string manipulation.

#     **YOUR TASK:**
#     Given the user's question, you must:
#     1.  **Think:** Analyze the user's intent. Are they asking an analytical question (DuckDB) or a relational/path-finding question (Neo4j)?
#     2.  **Plan:** Formulate a plan.
#     3.  **Act:** Generate a single, executable query in the chosen language.
#     4.  **Respond:** Output ONLY a single JSON object in the following format. Do not add any other text or explanations outside the JSON block.

#     ```json
#     {
#       "database": "duckdb" | "neo4j",
#       "query": "The single, complete, executable SQL or Cypher query string.",
#       "explanation": "A brief, one-sentence explanation of why you chose this database for this specific question."
#     }
#     ```

#     **EXAMPLE 1:**
#     User Question: "What are the top 5 best-selling products?"
#     Your JSON Response:
#     ```json
#     {
#       "database": "duckdb",
#       "query": "SELECT title, total_sold FROM products ORDER BY total_sold DESC LIMIT 5;",
#       "explanation": "This is a classic ranking and aggregation task, which is extremely fast in an analytical database like DuckDB."
#     }
#     ```

#     **EXAMPLE 2:**
#     User Question: "Find products that are in the same category as 'iPhone 15 Pro Max' but sold by a different shop."
#     Your JSON Response:
#     ```json
#     {
#       "database": "neo4j",
#       "query": "MATCH (p1:Product {title: 'iPhone 15 Pro Max'})-[:BELONGS_TO]->(c:Category)<-[:BELONGS_TO]-(p2:Product) WHERE p1 <> p2 MATCH (s1:Shop)-[:SELLS]->(p1) MATCH (s2:Shop)-[:SELLS]->(p2) WHERE s1 <> s2 RETURN p2.title, s2.seller_name LIMIT 10;",
#       "explanation": "This question is about finding connected items through shared relationships (same category, different shop), which is a core strength of a graph database."
#     }
#     ```

#     Now, analyze the following user question and provide your JSON response.
#     """

#     # --- Prompt Template cho việc Diễn giải Kết quả ---
#     _SUMMARIZATION_PROMPT_TEMPLATE = """
#     You are a friendly and helpful data analyst.
#     Your task is to summarize the results of a database query in a clear, concise, and easy-to-understand way for a non-technical user.

#     **Original User Question:**
#     "{user_question}"

#     **Query Result Data (in JSON format, might be partial):**
#     "{query_result}"

#     **Your Response:**
#     Based on the data, provide a natural language summary.
#     - Start with a direct answer to the user's question.
#     - If there's a list, mention a few examples.
#     - Keep it brief and to the point.
#     - Do not mention the database or the query. Just present the facts from the data.
#     """

#     def __init__(self, neo4j_driver, duckdb_conn, llm_provider):
#         self.neo4j_driver = neo4j_driver
#         self.duckdb_conn = duckdb_conn
#         # Giả sử llm_provider là một đối tượng đã được khởi tạo, ví dụ:
#         # self.model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key="...")
#         self.model = llm_provider

#     def _extract_json(self, text: str) -> dict:
#         """Trích xuất khối JSON đầu tiên từ một chuỗi, kể cả khi có markdown."""
#         # Tìm khối JSON trong markdown ```json ... ```
#         match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
#         if match:
#             json_str = match.group(1)
#         else:
#             # Nếu không, giả sử toàn bộ chuỗi là JSON hoặc tìm khối JSON đầu tiên
#             match = re.search(r"(\{.*?\})", text, re.DOTALL)
#             if not match:
#                 raise ValueError("Không tìm thấy đối tượng JSON hợp lệ trong phản hồi của LLM.")
#             json_str = match.group(1)

#         return json.loads(json_str)
        
#     def _generate_query_plan(self, user_input: str) -> dict:
#         """
#         (Component 1) Yêu cầu LLM tạo kế hoạch và sinh mã.
#         """
#         prompt = self._CODE_GENERATION_PROMPT_TEMPLATE + "\nUser Question: " + user_input
#         messages = [HumanMessage(content=prompt)]
        
#         response = self.model.invoke(messages)
#         plan = self._extract_json(response.content)
#         return plan

#     def _execute_query(self, plan: dict) -> tuple[list | None, str | None]:
#         """
#         (Component 2) Thực thi mã từ kế hoạch và trả về kết quả.
#         """
#         db_choice = plan.get("database")
#         query = plan.get("query")
        
#         try:
#             if db_choice == "duckdb":
#                 print(f"Executing on DuckDB: {query}")
#                 cursor = self.duckdb_conn.execute(query)
#                 cols = [desc[0] for desc in cursor.description]
#                 # Chuyển kết quả thành list of dicts để đồng nhất
#                 result_data = [dict(zip(cols, row)) for row in cursor.fetchall()]
#                 return result_data, None
            
#             elif db_choice == "neo4j":
#                 print(f"Executing on Neo4j: {query}")
#                 with self.neo4j_driver.session() as session:
#                     result = session.run(query)
#                     # .data() đã trả về list of dicts
#                     return result.data(), None
#             else:
#                 return None, f"Lựa chọn CSDL không hợp lệ: '{db_choice}'"
#         except Exception as e:
#             return None, f"Lỗi thực thi truy vấn: {e}"

#     def _summarize_result(self, user_question: str, query_result: list) -> str:
#         """
#         (Component 3) Yêu cầu LLM chuyển đổi dữ liệu thành mô tả tự nhiên.
#         """
#         # Giới hạn dữ liệu gửi đi để không vượt quá context window
#         result_subset = query_result[:20] 
        
#         prompt = self._SUMMARIZATION_PROMPT_TEMPLATE.format(
#             user_question=user_question,
#             query_result=json.dumps(result_subset, indent=2, ensure_ascii=False)
#         )
#         messages = [HumanMessage(content=prompt)]
        
#         response = self.model.invoke(messages)
#         return response.content

#     def ask(self, user_input: str):
#         """
#         Hàm chính điều phối toàn bộ quy trình, sử dụng generator để trả về từng bước.
#         """
#         try:
#             # BƯỚC 1: SUY NGHĨ VÀ LẬP KẾ HOẠCH
#             yield "🤔 Đang suy nghĩ và lựa chọn CSDL phù hợp..."
#             plan = self._generate_query_plan(user_input)
            
#             explanation = plan.get('explanation', 'Không có giải thích.')
#             db_name = plan.get('database', 'Không rõ').upper()
#             yield f"\n✅ **Kế hoạch đã sẵn sàng!**\n- **CSDL:** {db_name}\n- **Lý do:** {explanation}\n"

#             # BƯỚC 2: HÀNH ĐỘNG - THỰC THI
#             yield "⚙️ Đang thực thi truy vấn..."
#             result_data, error = self._execute_query(plan)

#             if error:
#                 yield f"\n❌ **Đã xảy ra lỗi!**\n- {error}"
#                 return

#             if not result_data:
#                 yield "\n🤷‍♀️ Truy vấn đã chạy thành công nhưng không tìm thấy kết quả nào."
#                 return
                
#             yield f"\n📊 Đã tìm thấy {len(result_data)} kết quả. Đang tổng hợp..."

#             # BƯỚC 3: TỔNG HỢP VÀ TRẢ LỜI
#             summary = self._summarize_result(user_input, result_data)
            
#             # Trả về kết quả cuối cùng với cả tóm tắt và dữ liệu thô
#             df = pd.DataFrame(result_data)
#             table = tabulate(df.head(10), headers='keys', tablefmt='grid', showindex=False)
            
#             final_response = f"\n💬 **Câu trả lời dành cho bạn:**\n{summary}\n\n"
#             final_response += f"**🔍 Dữ liệu chi tiết (tối đa 10 dòng đầu):**\n```\n{table}\n```"
            
#             yield final_response

#         except Exception as e:
#             yield f"\n💥 Đã xảy ra lỗi không mong muốn trong quá trình xử lý: {e}"