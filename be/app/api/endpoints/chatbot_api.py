from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.celery_worker.task import process_chatbot_request
import uuid

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    conversation_id: str

@router.post("/chat")
async def handle_chat(request: ChatRequest):
    print(request)
    if not request.message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
    if not request.conversation_id:
        return {"status": "error", "detail": "No conversation ID provided."}
    conv_id = request.conversation_id 

    task = process_chatbot_request.delay(
        message=request.message,
        conversation_id=conv_id
    )
    return {"status": "processing", "task_id": task.id, "conversation_id": conv_id}