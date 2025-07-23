from langchain.chat_models import init_chat_model
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage, HumanMessage
from app.core.config import settings

class Chatbot:
    def __init__(self):
        self.model = init_chat_model(
            "gemini-2.0-flash", 
            model_provider="google_genai",
            google_api_key=settings.GOOGLE_API_KEY
        )
        self.system_message = SystemMessage(
            content="You are a helpful assistant in multiple languages. Always try to answer user's questions in the best way possible."
        )

    def ask(self, user_input: str):
        messages = [
            self.system_message,
            HumanMessage(content=user_input)
        ]
        for chunk in self.model.stream(messages):
            yield chunk