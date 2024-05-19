import base64
from pathlib import Path
import sys
from fastapi_utils.inferring_router import InferringRouter
from fastapi import FastAPI
import psycopg2
from starlette.middleware import Middleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
import asyncio
from sqlalchemy.orm import sessionmaker
from db.db_service import DBService
from db.schema import Base, DetectionData
from sqlalchemy import create_engine
from typing import Set
from fastapi import WebSocket, WebSocketDisconnect
import json
sys.path.append(str(Path(__file__).resolve().parents[2]))

# from connection_manager import ConnectionManager
# from websockets.exceptions import ConnectionClosed


router = InferringRouter()

engine = DBService().get_engine()

connected_clients: Set[WebSocket] = set()
connected_clients_stream: Set[WebSocket] = set()

messagesReceived = []

#manager = ConnectionManager()

# WebSocket route
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    print("Client connected", websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # If you need to handle messages from frontend, add logic here
            print("Received message from client:", data)
    except WebSocketDisconnect:
        connected_clients.remove(websocket)

# Listen for PostgreSQL notifications
async def listen_for_notifications():
    conn = engine.raw_connection()
    conn.set_isolation_level(0)
    curs = conn.cursor()
    curs.execute('LISTEN detection_data_inserted')
    while True:
        try:
            conn.poll()
            if conn.notifies:
                notify = conn.notifies.pop(0)

                message = json.loads(notify.payload)
                if not message['uuid'] in  messagesReceived:
                    messagesReceived.append(message['uuid'])
                    print("Received notification:", notify.payload)
                    await broadcast_notification(notify.payload)
            
            await asyncio.sleep(0.5)  # Adjust as needed
            
        except psycopg2.errors.OperationalError:
            print("Connection disconnected. Reconnecting...")
            conn = engine.raw_connection()
            conn.set_isolation_level(0)
            curs = conn.cursor()
            curs.execute('LISTEN detection_data_inserted')

async def broadcast_notification(payload: str):
    for client in connected_clients.copy():
        try:
            await client.send_json({"message": payload})
        except WebSocketDisconnect:
            connected_clients.remove(client)

async def broadcast_stream(image_bytes):
    for client in connected_clients_stream.copy():  
        try:
            await client.send_json(image_bytes)
        except WebSocketDisconnect:
            connected_clients_stream.remove(client)

# Background task to run notification listener
@router.on_event("startup")
async def startup():
    asyncio.create_task(listen_for_notifications())

@router.websocket("/stream")
async def stream_websocket_endpoint(streamsocket: WebSocket):
    await streamsocket.accept()
    connected_clients_stream.add(streamsocket)
    print("Stream Client connected", streamsocket)
    try:
        while True:
            data = await streamsocket.receive_json()
            # data_dict = json.loads(data)
            # image_data = data_dict['image']
            # image_bytes = base64.b64decode(image_data)

            await broadcast_stream(data)
    except WebSocketDisconnect:
        connected_clients_stream.remove(streamsocket)

    # await manager.connect(websocket)
    # try:
    #     while True:
    #         data = await websocket.receive_text()
    #         data_dict = json.loads(data)
    #         image_data = data_dict['image']
    #         image_bytes = base64.b64decode(image_data)
            
    #         await broadcast_notification(image_bytes)
    #         #await manager.send_personal_message(image_bytes, websocket)
    # except (WebSocketDisconnect, ConnectionClosed):
    #     manager.disconnect(websocket)
