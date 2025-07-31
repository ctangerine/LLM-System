# socketio_main.py
import uvicorn
import asyncio
from server import sio, redis_listener
from socketio import ASGIApp

sio_asgi_app = ASGIApp(sio)

async def main():
    listener_task = asyncio.create_task(redis_listener(sio))
    
    config = uvicorn.Config(sio_asgi_app, host="0.0.0.0", port=9000, log_level="info")
    server = uvicorn.Server(config)
    
    await asyncio.gather(listener_task, server.serve())


if __name__ == "__main__":
    print("Starting Socket.IO server...")
    asyncio.run(main())