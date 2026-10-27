import asyncio
from typing import Dict, List, Set
from fastapi import WebSocket
from app.core.logging import get_logger

logger = get_logger(__name__)

class SocketManager:
    def __init__(self):
        # 用户ID映射到其拥有的所有 WebSocket 连接 (支持多设备打开)
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        logger.info(f"[WS] Client connected: user_id={user_id}, total_clients={len(self.active_connections[user_id])}")

    def disconnect(self, user_id: str, websocket: WebSocket):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"[WS] Client disconnected: user_id={user_id}")

    async def broadcast_to_user(self, user_id: str, message: dict):
        """定向推送到指定用户的所有连接"""
        if user_id in self.active_connections:
            connections = list(self.active_connections[user_id])
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.warning(f"[WS] Failed to send message to user {user_id}: {e}")
                    self.active_connections[user_id].discard(connection)

    async def broadcast_all(self, message: dict):
        """全域广播 (例如系统维护通知)"""
        for user_id, connections in self.active_connections.items():
            for connection in list(connections):
                try:
                    await connection.send_json(message)
                except Exception:
                    self.active_connections[user_id].discard(connection)

socket_manager = SocketManager()
