from __future__ import annotations

from typing import Dict, Set
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        """接受新的WebSocket连接"""
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        """断开WebSocket连接"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_message(self, message: dict):
        """向所有连接广播消息"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error broadcasting message: {e}")

    async def send_personal_message(self, websocket: WebSocket, message: dict):
        """向特定连接发送消息"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending personal message: {e}")

    def get_connection_count(self) -> int:
        """获取当前连接数"""
        return len(self.active_connections)

    def get_connections(self) -> Set[WebSocket]:
        """获取所有活动连接"""
        return self.active_connections


global_manager = ConnectionManager()
