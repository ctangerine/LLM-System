import json
import uuid
from fastapi import FastAPI
import asyncio
from app.api.endpoints import chatbot_api
from app.socket_server.server import sio, redis_listener
from app.core.config import Settings
import socketio
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(redis_listener(sio))
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

app = FastAPI(title="Chatbot LLM Backend", lifespan=lifespan)
app.include_router(chatbot_api.router, prefix="/api", tags=["chat"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    new_conversation_id = str(uuid.uuid4())
    return json.dumps({
        "message": "Welcome to the Chatbot LLM Backend",
        "new_conversation_id": new_conversation_id
    })
