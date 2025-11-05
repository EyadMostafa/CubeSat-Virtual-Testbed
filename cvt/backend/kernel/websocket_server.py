from __future__ import annotations

import logging
from typing import List
from fastapi import WebSocket

from cvt.backend.kernel.state_schema import SatelliteState

logger = logging.getLogger(__name__)

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

    async def connect(self, websocket: WebSocket):
        """
        Accepts and adds a new client connection to the list.
        Called by: run_server.py
        """
        try:
            await websocket.accept()
            self.active_connections.append(websocket)
            logger.info(f"New client connected. Total clients: {len(self.active_connections)}")
        except Exception as e:
            logger.debug(f"Error during websocket accept (ignorable): {e}")

    async def disconnect(self, websocket: WebSocket):
        """
        Removes a client connection from the list.
        Called by: run_server.py
        """
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
        json_data = state.model_dump_json()

        for connection in self.active_connections:
            try:
                await connection.send_text(json_data)
            except Exception as e:
                logger.warning(f"Failed to send message to client: {e}. Removing.")
                await self.disconnect(connection)

connection_manager = ConnectionManager()