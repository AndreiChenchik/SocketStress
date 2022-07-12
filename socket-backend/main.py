from typing import List, Optional

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
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@app.get("/")
async def get():
    return HTMLResponse(html(location))


@app.websocket("/ws/{client_name}")
async def websocket_endpoint(websocket: WebSocket, client_name: str):
    await manager.connect(websocket)
    await manager.broadcast(f"{client_name} enters the chat")
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"{client_name}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"{client_name} left the chat")
