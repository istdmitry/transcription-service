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
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS gdrive_email VARCHAR"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS delete_after TIMESTAMP WITH TIME ZONE"))
            
            # Transcript table updates
            conn.execute(text("ALTER TABLE transcripts ADD COLUMN IF NOT EXISTS project_id INTEGER REFERENCES projects(id)"))
            conn.execute(text("ALTER TABLE transcripts ADD COLUMN IF NOT EXISTS language VARCHAR DEFAULT 'en'"))
            conn.execute(text("ALTER TABLE transcripts ADD COLUMN IF NOT EXISTS gdrive_file_id VARCHAR"))
            conn.execute(text("ALTER TABLE transcripts ADD COLUMN IF NOT EXISTS gdrive_error_message VARCHAR"))
            conn.execute(text("ALTER TABLE transcripts ADD COLUMN IF NOT EXISTS error_message VARCHAR"))
            conn.execute(text("ALTER TABLE transcripts ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE"))

            # Projects table
            conn.execute(text("ALTER TABLE projects ADD COLUMN IF NOT EXISTS gdrive_email VARCHAR"))
            
            # Temporary: Grant admin to specific user
            conn.execute(text("UPDATE users SET is_admin = TRUE WHERE email = 'ist.dmitry@gmail.com'"))
            
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
    allow_origins=["*"],  # public API consumed with Bearer tokens
    allow_origin_regex=".*",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
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

@app.get("/debug-admin")
def debug_admin(email: str = "ist.dmitry@gmail.com"):
    from app.db.session import SessionLocal
    from app.models.user import User
    from sqlalchemy import text
    
    db = SessionLocal()
    try:
        # Check Columns
        result = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'transcripts'"))
        cols = [r[0] for r in result]
        
        # Check User
        user = db.query(User).filter(User.email == email).first()
        user_info = "Not Found"
        if user:
            user_info = {"id": user.id, "email": user.email, "is_admin": user.is_admin}
            
            # Force Fix
            if not user.is_admin:
                user.is_admin = True
                db.commit()
                db.refresh(user)
                user_info["fixed_is_admin"] = True
                
        return {
            "columns": cols,
            "user": user_info
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()
