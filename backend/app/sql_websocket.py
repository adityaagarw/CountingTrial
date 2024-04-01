from fastapi_utils.inferring_router import InferringRouter
from fastapi import FastAPI, WebSocket
import psycopg2
from starlette.middleware import Middleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
import asyncio
from sqlalchemy.orm import sessionmaker
from db.db_service import DBService
from db.schema import Base, DetectionData
from sqlalchemy import create_engine


router = InferringRouter()

engine = DBService().get_engine()

# WebSocket route
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_json()
        # If you need to handle messages from frontend, add logic here
        print("Received message from client:", data)

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
                print("Received notification:", notify.payload)
            await asyncio.sleep(0.1)  # Adjust as needed
        except psycopg2.errors.OperationalError:
            print("Connection disconnected. Reconnecting...")
            conn = engine.raw_connection()
            conn.set_isolation_level(0)
            curs = conn.cursor()
            curs.execute('LISTEN detection_data_inserted')

# Background task to run notification listener
@router.on_event("startup")
async def startup():
    asyncio.create_task(listen_for_notifications())
