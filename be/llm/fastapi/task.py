import os
import sys
from celery import shared_task
import redis
from .chatbot import Chatbot
import json
import time
import traceback
    
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))
from core.config import settings 

redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
chatbot = Chatbot()

def extract_content_from_chunk(chunk):
    """Extract text content from different types of LangChain chunks"""
    if hasattr(chunk, 'content') and chunk.content:
        return chunk.content
    elif hasattr(chunk, 'text') and chunk.text:
        return chunk.text
    elif hasattr(chunk, 'delta') and hasattr(chunk.delta, 'content') and chunk.delta.content:
        return chunk.delta.content
    elif isinstance(chunk, str):
        return chunk
    else:
        chunk_str = str(chunk)
        print(f"Unknown chunk type: {type(chunk)}, content: {chunk_str}")
        return ""

@shared_task(bind=True)
def process_chatbot_request(self, message: str, conversation_id: str):
    channel_name = f"chat:{conversation_id}"
    print('celery received task:', message, conversation_id)

    try:
        redis_client.publish(channel_name, json.dumps({
            "type": "processing",
            "data": {} 
        }))

        complete_response = ""

        for chunk in chatbot.ask(message):
            chunk_content = extract_content_from_chunk(chunk)
            
            if chunk_content:
                complete_response += chunk_content

                redis_client.publish(channel_name, json.dumps({
                    "type": "gen_token", 
                    "data": {"data": chunk_content} 
                }))
            
            time.sleep(0.02)

        redis_client.publish(channel_name, json.dumps({
            "type": "completed",
            "data": {"response": complete_response}
        }))
        
        return {
            "status": "success",
            "response": complete_response,
            "conversation_id": conversation_id
        }
        
    except Exception as e:
        error_message = str(e)
        print(f"Error in process_chatbot_request: {error_message}")
        traceback.print_exc()
        
        redis_client.publish(channel_name, json.dumps({
            "type": "error",
            "data": {"error": error_message} 
        }))
        
        raise