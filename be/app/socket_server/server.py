import socketio
import asyncio
import json 
from redis import asyncio as aioredis

from app.core.config import settings 

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')

@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")
    await sio.emit('status', {'status': 'connected'}, room=sid) 

@sio.on('join_room')
async def join_room(sid, data):
    conversation_id = data.get('conversation_id')
    if conversation_id:
        room_name = f"chat:{conversation_id}"
        sio.enter_room(sid, room_name)
        print(f"Client {sid} joined room: {room_name}")


@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")

async def redis_listener(sio_app):
    redis_conn = aioredis.from_url(settings.REDIS_URL)
    pubsub = redis_conn.pubsub()
    await pubsub.psubscribe("chat:*")
    print("Redis listener started...")
    while True: # listen to pubsub channel
        try:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message:
                channel = message['channel'].decode('utf-8')
                event_data = json.loads(message['data'].decode('utf-8'))
                await sio_app.emit(event_data['type'], event_data['data'], room=channel)
            await asyncio.sleep(0.01)
        except Exception as e:
            print(f"Redis listener error: {e}")
            await asyncio.sleep(1)