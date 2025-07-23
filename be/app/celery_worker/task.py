from celery import shared_task
import redis 
from app.celery_worker.chatbot import Chatbot
from app.core.config import settings
import json
import time

redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
chatbot = Chatbot()

@shared_task(bind=True)
def process_chatbot_request(self, message: str, conversation_id: str):
    channel_name = f"chat:{conversation_id}"

    try:
        redis_client.publish(channel_name, json.dumps({
            "type": "status",
            "data": "processing",
        }))

        complete_response = ""

        for chunk in chatbot.ask(message):
            complete_response += chunk
            print(f"Chunk received: {chunk}")
            redis_client.publish(channel_name, json.dumps({"type": "gen_token", "data": chunk}))
            time.sleep(0.02)

        redis_client.publish(channel_name, json.dumps({
            "type": "status",
            "data": "completed",
            "response": complete_response
        }))
    except Exception as e:
        redis_client.publish(channel_name, json.dumps({
            "type": "status",
            "status": "error",
            "error": str(e)
        }))
    pass