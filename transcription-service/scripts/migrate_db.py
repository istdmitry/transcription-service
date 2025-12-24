import os
import sys

# Add directory to path to import app modules
sys.path.append(os.getcwd())

from sqlalchemy import text
from app.db.session import engine

def migrate_users_table():
    with engine.connect() as conn:
        print("Migrating users table...")
        try:
            # Add is_admin
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE"))
                print("Added is_admin column")
            except Exception as e:
                print(f"Skipping is_admin (might exist): {e}")

            # Add gdrive_creds
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN gdrive_creds TEXT"))
                print("Added gdrive_creds column")
            except Exception as e:
                print(f"Skipping gdrive_creds (might exist): {e}")

            # Add gdrive_folder
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN gdrive_folder VARCHAR"))
                print("Added gdrive_folder column")
            except Exception as e:
                print(f"Skipping gdrive_folder (might exist): {e}")

            conn.commit()
            print("Migration complete!")
        except Exception as e:
            print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate_users_table()
