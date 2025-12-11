from fastapi import FastAPI
from app.core.config import settings
from app.api import auth, transcripts, webhooks, logs
from app.db.base import Base, engine
from app.core.logging_config import setup_logging
import logging

# Setup Logging
setup_logging()
logger = logging.getLogger(__name__)

# Create tables (For production, use Alembic)
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    logger.error(f"Error initializing database: {e}")

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.include_router(auth.router)
app.include_router(transcripts.router)
app.include_router(webhooks.router)
app.include_router(logs.router)

@app.get("/")
def read_root():
    return {"message": "Transcription Service API is running"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
