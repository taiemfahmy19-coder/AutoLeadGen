"""AutoLeadGen V3 — WebSocket Connection Manager for real-time event broadcast."""
import json
import asyncio
import logging
from typing import List, Dict, Any

from fastapi import WebSocket

logger = logging.getLogger("AutoLeadGen")


class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, event_type: str, data: Dict[str, Any]):
        message = json.dumps({"event": event_type, "data": data}, default=str, ensure_ascii=False)
        dead = []
        for ws in list(self.active_connections):
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    def broadcast_sync(self, event_type: str, data: Dict[str, Any]):
        """Thread-safe broadcast from non-async context."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(self.broadcast(event_type, data), loop)
            else:
                loop.run_until_complete(self.broadcast(event_type, data))
        except Exception as e:
            logger.debug(f"WebSocket broadcast_sync skipped: {e}")


ws_manager = WebSocketManager()
