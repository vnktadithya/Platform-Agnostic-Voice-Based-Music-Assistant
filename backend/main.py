from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.v1.adapter_routes import router as spotify_router
from backend.api.v1.voice_routes import router as voice_router
from backend.api.v1.chat_routes import router as chat_router
from backend.api.v1.user_routes import router as user_router
from backend.api.v1.search_routes import router as search_router
from backend.models import database_models 
from backend.configurations.database import engine 

database_models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(spotify_router, prefix = "/v1")
app.include_router(voice_router, prefix = "/v1")
app.include_router(chat_router, prefix = "/v1")
app.include_router(user_router, prefix = "/v1")
app.include_router(search_router, prefix = "/v1")

# CORS if you're using frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Voice Assistant Backend is Running 🚀"}
