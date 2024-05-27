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
from datetime import datetime
from multiprocessing import shared_memory
import struct
import array
import numpy as np
import cv2

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

                    # Add the 'type': 'notification' field
                    message['type'] = 'notification'
                    
                    # Convert the updated message back to a JSON string
                    updated_payload = json.dumps(message)
                    
                    # Print the received notification
                    print("Received notification:", updated_payload)
                    
                    # Broadcast the updated notification
                    await broadcast_notification(updated_payload)
            
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

async def broadcast_stream(image_bytes, feed_id):
    if image_bytes is None:
        return

    for client in connected_clients_stream.copy():  
        try:
            await client.send_json({'feed_id': feed_id, "image": image_bytes, 'type': 'stream'})
        except WebSocketDisconnect:
            connected_clients_stream.remove(client)

# Background task to run notification listener
@router.on_event("startup")
async def startup():
    asyncio.create_task(listen_for_notifications())

def consume_data(buffer):
    while struct.unpack('i', buffer[:4])[0] != 0:
        pass
    
    buffer[:4] = array.array("i", [2]).tobytes()
    frame_length = struct.unpack('i', buffer[4:8])[0] # get frame length
    if frame_length == 0:
        # Unlock
        buffer[:4] = array.array("i", [0]).tobytes()
        return None

    frame_bytes = buffer[8:frame_length+8] # get frame bytes
    buffer[:4] = array.array("i", [0]).tobytes()

    frame_bytes_to_send = base64.b64encode(frame_bytes.tobytes()).decode()
    return frame_bytes_to_send
    

@router.websocket("/stream/{feed_id}")
async def stream_websocket_endpoint(streamsocket: WebSocket, feed_id: str):
    await streamsocket.accept()
    connected_clients_stream.add(streamsocket)

    shm_test = None

    flag = 0
    print("Stream Client connected", streamsocket)
    try:
        while True:
            if flag == 0:
                try:
                    shm_name = "avian_shm_" + feed_id
                    shm_test = shared_memory.SharedMemory(name=shm_name)
                    flag = 1
                except:
                    data = 0
                    await asyncio.sleep(0.1)
                    continue

            if flag == 1:
                if shm_test != None:
                    data = consume_data(shm_test.buf)
                
            await asyncio.sleep(0.1) #TBD: Reduce and check behaviour

            if data != 0 or data is not None:
                await broadcast_stream(data, feed_id)

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