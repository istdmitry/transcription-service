import sys
import os

# Add root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import SessionLocal
from app.models.user import User
from sqlalchemy import text

db = SessionLocal()
try:
    # Check User
    user = db.query(User).filter(User.email == 'ist.dmitry@gmail.com').first()
    if user:
        print(f"User Found: {user.email}")
        print(f"Is Admin: {user.is_admin}")
    else:
        print("User NOT found")

    # Check Columns
    print("\nTranscript Columns:")
    result = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'transcripts'"))
    cols = [r[0] for r in result]
    print(cols)
    
    expected = ['project_id', 'language', 'error_message', 'updated_at', 'gdrive_file_id']
    missing = [c for c in expected if c not in cols]
    if missing:
        print(f"\nMISSING COLUMNS: {missing}")
    else:
        print("\nAll expected columns present.")

finally:
    db.close()
