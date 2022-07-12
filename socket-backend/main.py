from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseSettings

from html import html

app = FastAPI()

class Settings(BaseSettings):
    host: str
    port: Optional[str] = None

    class Config:
        env_prefix = "WS_"

settings = Settings()
location = settings.host

if settings.port:
    location += f":{settings.port}"

class ConnectionManager:
    active_connections: List[WebSocket]
    history: List[str]

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.history = []

    async def connect(self, connection: WebSocket):
        await connection.accept()
        self.active_connections.append(connection)
        
        for message in self.history:
            await connection.send_text(message)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        self.history.append(message)
        
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@app.get("/")
async def get():
    return HTMLResponse(html(location))


@app.websocket("/ws/{client_name}")
async def websocket_endpoint(websocket: WebSocket, client_name: str):
    await manager.connect(websocket)
    await manager.broadcast(f"{str(datetime.now())} {client_name} enters the chat")
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"{str(datetime.now())} {client_name}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"{str(datetime.now())} {client_name} left the chat")
