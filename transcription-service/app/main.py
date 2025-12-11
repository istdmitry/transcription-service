from fastapi import FastAPI
from app.core.config import settings
from app.api import auth, transcripts, webhooks
from app.db.base import Base, engine

# Create tables (For production, use Alembic)
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION)

app.include_router(auth.router)
app.include_router(transcripts.router)
app.include_router(webhooks.router)

@app.get("/")
def read_root():
    return {"message": "Transcription Service API is running"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
