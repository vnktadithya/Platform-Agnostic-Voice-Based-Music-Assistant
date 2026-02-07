from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import logging
import os
from backend.api.v1.adapter_routes import router as adapter_router
from backend.api.v1.voice_routes import router as voice_router
from backend.api.v1.chat_routes import router as chat_router
from backend.api.v1.user_routes import router as user_router
from backend.api.v1.search_routes import router as search_router
from backend.models import database_models 
from backend.configurations.database import engine
from backend.socket_manager import socket_app
from backend.utils.custom_exceptions import AuthenticationError, DeviceNotFoundException, ExternalAPIError
from fastapi.responses import JSONResponse
from fastapi import Request

# Configure centralized logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)

# Verify database schema existence
# database_models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Voice Assistant Backend", version="1.0.0")

app.mount("/socket.io", socket_app)
# Fallback mount if needed, though socket.io handles paths
app.mount("/ws", socket_app) 

logger.info("Voice Assistant Backend starting up")

# Load Session Secret
session_secret = os.getenv("SESSION_SECRET_KEY")
env = os.getenv("ENV", "development")

if not session_secret:
    if env == "production":
         logger.critical("SESSION_SECRET_KEY is missing in production!")
         raise ValueError("SESSION_SECRET_KEY must be set in .env for production.")
    else:
        logger.warning("SESSION_SECRET_KEY is missing. Using insecure default for dev.")
        session_secret = "dev-secret-change-this"

# Configure Session Middleware based on environment
secure_cookie = env == "production"
samesite_policy = "none" if env == "production" else "lax"

app.add_middleware(
    SessionMiddleware,
    secret_key=session_secret,
    https_only=secure_cookie,
    same_site=samesite_policy
)

app.include_router(adapter_router, prefix="/v1")
app.include_router(voice_router, prefix="/v1")
app.include_router(chat_router, prefix="/v1")
app.include_router(user_router, prefix="/v1")
app.include_router(search_router, prefix="/v1")

logger.info("API routers registered (adapter, voice, chat, user, search)")

@app.exception_handler(AuthenticationError)
async def auth_exception_handler(request: Request, exc: AuthenticationError):
    logger.warning(f"AuthenticationError caught: {exc.message}")
    return JSONResponse(
        status_code=401,
        content={"detail": exc.message, "code": "AUTHENTICATION_ERROR"},
    )

@app.exception_handler(DeviceNotFoundException)
async def device_not_found_handler(request: Request, exc: DeviceNotFoundException):
    logger.warning(f"DeviceNotFoundException caught: {exc.message}")
    return JSONResponse(
        status_code=409, # Conflict: Resource state prevents action
        content={"detail": exc.message, "code": "DEVICE_NOT_FOUND"},
    )

@app.exception_handler(ExternalAPIError)
async def external_api_error_handler(request: Request, exc: ExternalAPIError):
    logger.error(f"ExternalAPIError caught: {exc.message}")
    return JSONResponse(
        status_code=502, # Bad Gateway: Upstream service failed
        content={"detail": exc.message, "code": "EXTERNAL_API_ERROR"},
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception caught: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {str(exc)}", "type": str(type(exc).__name__)},
    )

# CORS Configuration
origins = [
    "http://localhost:5173",  # Vite Dev Server
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://sam-self-adaptive-music-intelligence.vercel.app",   # production
    "https://*.vercel.app" # Allow Vercel preview deployments
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    logger.debug("Health check endpoint called")
    return {"message": "Voice Assistant Backend is Running 🚀"}
