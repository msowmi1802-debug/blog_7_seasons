import os
import sqlite3

# Project folder
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Create the instance folder if it doesn't exist
os.makedirs(os.path.join(BASE_DIR, "instance"), exist_ok=True)

# Database path
DATABASE = os.path.join(BASE_DIR, "instance", "secure_diary.db")


def get_connection():
    """Create and return a database connection."""
    conn = sqlite3.connect(DATABASE, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    """Create all required database tables."""

    conn = get_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        verified INTEGER DEFAULT 0
    )
    """)

    # OTP table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS otp_codes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        otp TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)
    cursor.execute("""
       CREATE TABLE IF NOT EXISTS posts (

         id INTEGER PRIMARY KEY AUTOINCREMENT,

         user_id INTEGER NOT NULL,

         title TEXT NOT NULL,

         content TEXT NOT NULL,

         category TEXT NOT NULL,

          visibility TEXT NOT NULL DEFAULT 'private',

         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

         updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 
         FOREIGN KEY(user_id)
         REFERENCES users(id)
        )
    """)     
    cursor.execute("""
       CREATE TABLE IF NOT EXISTS likes (

         id INTEGER PRIMARY KEY AUTOINCREMENT,

         user_id INTEGER NOT NULL,

         post_id INTEGER NOT NULL,

         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

         UNIQUE(user_id, post_id),

         FOREIGN KEY(user_id) REFERENCES users(id),

         FOREIGN KEY(post_id) REFERENCES posts(id)

        )
    """)
    cursor.execute("""
       CREATE TABLE IF NOT EXISTS comments (

         id INTEGER PRIMARY KEY AUTOINCREMENT,

         user_id INTEGER NOT NULL,

         post_id INTEGER NOT NULL,

         comment TEXT NOT NULL,

         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

         FOREIGN KEY(user_id) REFERENCES users(id),

         FOREIGN KEY(post_id) REFERENCES posts(id)

       )
    """)
    conn.commit()
    conn.close()
    