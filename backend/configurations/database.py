from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

DATABASE_URL = "sqlite:///./music_assistant.db"

# The engine is the entry point to our database.
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

# Each instance of SessionLocal will be a database session.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# This will be the base class our ORM models will inherit from.
Base = declarative_base()

# Dependency for FastAPI routes to get a DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()