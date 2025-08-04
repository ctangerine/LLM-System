import json
import uuid
import uvicorn
from fastapi import FastAPI

app = FastAPI(title="Chatbot LLM Backend")

from endpoints.helper.middleware import create_middleware 
app = create_middleware(app)
from fastapi.middleware.cors import CORSMiddleware

from endpoints import chatbot_api, authen_api
app.include_router(chatbot_api.router, prefix="/api", tags=["chat"])
app.include_router(authen_api.router, prefix="/api", tags=["auth"])

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

if __name__ == "__main__":
    print("Starting FastAPI server...")
    uvicorn.run("fastapi_main:app", host="0.0.0.0", port=8000, log_level="debug", reload=True)
