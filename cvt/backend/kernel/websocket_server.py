from __future__ import annotations

from logging import getLogger
import asyncio
from typing import List
from fastapi import WebSocket

from cvt.backend.kernel.state_schema import SatelliteState

logger = getLogger(__name__)

class ConnectionManager:
    """
    Manages all active WebSocket connections.
    """
    def __init__(self):
        """
        Initializes the list of active connections.
        """
        self.active_connections: List[WebSocket] = []
        logger.info("ConnectionManager initialized.")

        self.lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        """
        Accepts and adds a new client connection to the list.
        Called by: run_server.py
        """
        try:
            await websocket.accept()
            async with self.lock:
                self.active_connections.append(websocket)
            logger.info(f"New client connected. Total clients: {len(self.active_connections)}")
        except Exception as e:
            logger.debug(f"Error during websocket accept (ignorable): {e}")

    async def disconnect(self, websocket: WebSocket):
        """
        Removes a client connection from the list.
        Called by: run_server.py
        """
        async with self.lock: 
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
                logger.info(f"Client disconnected. Total clients: {len(self.active_connections)}")
        try:
            await websocket.close()
        except Exception as e:
            logger.debug(f"Error during websocket close (ignorable): {e}")

    async def broadcast(self, state: SatelliteState):
        """
        Broadcasts the given state to all active connections.
        Called by: simulation_kernel.py
        """
        async def safe_send(connection, data):
            try:
                await connection.send_text(data)
            except Exception as e:
                logger.warning(f"Failed to send message: {e}. Removing.")
                await self.disconnect(connection)

        json_data = state.model_dump_json()

        tasks = []

        for connection in self.active_connections[:]:
            tasks.append(safe_send(connection, json_data))

        await asyncio.gather(*tasks)

connection_manager = ConnectionManager()