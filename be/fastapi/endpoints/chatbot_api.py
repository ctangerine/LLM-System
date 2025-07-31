import json
import os
import sys

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from celery_worker.celery_app import celery_app

class ChatRequest(BaseModel):
    message: str
    conversation_id: str


router = APIRouter()

@router.post("/chat")
async def handle_chat(request: Request):
    try:
        print('received request:', request )
        data = await request.json()
        message = data.get('message')
        if not message or not message.strip():
            raise HTTPException(status_code=400, detail="Missing or empty 'message' field")

        # Lấy conversation_id
        conversation_id = None

        # Thứ tự ưu tiên:
        # 1. Trực tiếp từ data['conversation_id'] hoặc data['new_conversation_id']
        if 'new_conversation_id' in data and str(data['new_conversation_id']).strip():
            conversation_id = str(data['new_conversation_id']).strip()
        elif 'conversation_id' in data and str(data['conversation_id']).strip():
            conversation_id = str(data['conversation_id']).strip()  
        # 2. Hoặc từ data['conversation'] (có thể là dict hoặc str JSON)
        elif 'conversation' in data:
            conversation = data['conversation']
            if isinstance(conversation, dict):
                conversation_id = (
                    str(conversation.get('new_conversation_id') or conversation.get('conversation_id') or '').strip()
                )
            elif isinstance(conversation, str):
                try:
                    parsed = json.loads(conversation)
                    if isinstance(parsed, dict):
                        conversation_id = (
                            str(parsed.get('new_conversation_id') or parsed.get('conversation_id') or '').strip()
                        )
                    else:
                        conversation_id = conversation.strip()
                except json.JSONDecodeError:
                    conversation_id = conversation.strip()

        # Kiểm tra cuối cùng
        if not conversation_id:
            raise HTTPException(status_code=400, detail="Missing or empty conversation ID")

        print("Conversation id:", conversation_id)

        # Gửi task tới Celery
        task = celery_app.send_task(
            'celery_worker.task.process_chatbot_request',
            args=[message.strip(), conversation_id]
        )

        return {
            "status": "processing",
            "task_id": task.id,
            "conversation_id": conversation_id
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
