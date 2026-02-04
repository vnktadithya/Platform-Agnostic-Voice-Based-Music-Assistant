import socketio
import logging

logger = logging.getLogger(__name__)

# Create a Socket.IO server
# async_mode='asgi' is important for FastAPI interaction
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')

# Create an ASGI application
socket_app = socketio.ASGIApp(sio)

@sio.event
async def connect(sid, environ):
    logger.info(f"Socket connected: {sid}")
    await sio.emit('status', {'state': 'IDLE', 'message': 'Connected to SAM'}, room=sid)

@sio.event
async def disconnect(sid):
    logger.info(f"Socket disconnected: {sid}")

async def emit_state(state: str, message: str = ""):
    """
    Helper to emit state changes to all clients.
    States: IDLE, LISTENING, THINKING, SPEAKING
    """
    await sio.emit('state_update', {'state': state, 'message': message})
