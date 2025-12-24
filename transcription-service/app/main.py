# Deployment trigger
import logging
from fastapi import FastAPI
from app.core.config import settings
from app.api import auth, transcripts, webhooks, logs, projects, admin
from app.db.base import Base
from app.db.session import engine
from app.core.logging_config import setup_logging
# Setup Logging
setup_logging()
logger = logging.getLogger(__name__)

print("Loading API routers...")
logger.info("Initializing API routes")

# Create tables (For production, use Alembic)
try:
    Base.metadata.create_all(bind=engine)
    
    # Auto-migration for missing columns
    from sqlalchemy import text
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS gdrive_creds TEXT"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS gdrive_folder VARCHAR"))
            conn.execute(text("ALTER TABLE transcripts ADD COLUMN IF NOT EXISTS project_id INTEGER REFERENCES projects(id)"))
            conn.commit()
            logger.info("Auto-migration completed: Added missing columns to users and transcripts tables")
        except Exception as e:
            logger.warning(f"Auto-migration skipped or failed: {e}")
            
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

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(transcripts.router, prefix="/transcripts", tags=["transcripts"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
app.include_router(logs.router, prefix="/logs", tags=["logs"])
app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
print(f"Routes registered: {[r.path for r in app.routes]}")

@app.get("/")
def read_root():
    return {"message": "Transcription Service API is running"}

@app.get("/health")
def health_check():
    import time
    return {"status": "ok", "version": "1.1.0", "timestamp": time.time()}
