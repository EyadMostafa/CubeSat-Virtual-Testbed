from logging import getLogger
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from contextlib import asynccontextmanager

from cvt.config.config import config, GeneralSettings
from cvt.backend.kernel.simulation_kernel import simulation_kernel
from cvt.backend.kernel.websocket_server import connection_manager

logger = getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Server starting up...")
    await simulation_kernel.start_simulation()
    yield
    logger.info("Server shutting down...")
    await simulation_kernel.stop_simulation()

app = FastAPI(lifespan=lifespan)

@app.get("/status")
async def get_status():
    """Returns the 'general' section of the config."""
    return config

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await connection_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info("Client disconnected gracefully.")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await connection_manager.disconnect(websocket)
        

