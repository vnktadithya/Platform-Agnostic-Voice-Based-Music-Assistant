from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.v1.adapter_routes import router as adapter_router
from backend.api.v1.voice_routes import router as voice_router
from backend.api.v1.chat_routes import router as chat_router
from backend.api.v1.user_routes import router as user_router
from backend.api.v1.search_routes import router as search_router
from backend.models import database_models 
from backend.configurations.database import engine
import os
from starlette.middleware.sessions import SessionMiddleware
import logging

logger = logging.getLogger(__name__)
database_models.Base.metadata.create_all(bind=engine)
app = FastAPI()

logger.info("Voice Assistant Backend starting up")

# ✅ REQUIRED for OAuth (Authlib)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET_KEY", "dev-secret-change-this"),
)

app.include_router(adapter_router, prefix = "/v1")
app.include_router(voice_router, prefix = "/v1")
app.include_router(chat_router, prefix = "/v1")
app.include_router(user_router, prefix = "/v1")
app.include_router(search_router, prefix = "/v1")

logger.info("API routers registered (adapter, voice, chat, user, search)")

# CORS while using frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    logger.debug("Health check endpoint called")
    return {"message": "Voice Assistant Backend is Running 🚀"}
