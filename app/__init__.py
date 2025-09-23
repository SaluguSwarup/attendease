# app/__init__.py
import os
import sqlite3
from flask import Flask

# --- Database Setup ---
def init_db(app):
    # The database will be created in the 'instance' folder
    db_path = os.path.join(app.instance_path, 'database.db')
    
    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db = sqlite3.connect(db_path)
    cursor = db.cursor()

    # Create the tables if they don't exist
    # [cite_start]1. working_table: Maps a student's permanent roll_no to a UID [cite: 47]
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS working_table (
        roll_no TEXT PRIMARY KEY,
        uid TEXT NOT NULL UNIQUE
    )''')

    # [cite_start]2. attendance_history: Stores a record of each successful attendance [cite: 48]
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendance_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        roll_no TEXT NOT NULL,
        course TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    # --- Pre-populate with sample data for the PoC ---
    sample_students = [
        ('2301001', 'uid_student_alpha'),
        ('2301002', 'uid_student_beta'),
        ('2301003', 'uid_student_gamma'),
        ('2301004', 'uid_student_delta'),
        ('2301005', 'uid_student_epsilon')
    ]
    # Use IGNORE to prevent errors if the data already exists
    cursor.executemany('INSERT OR IGNORE INTO working_table (roll_no, uid) VALUES (?, ?)', sample_students)

    db.commit()
    db.close()
    print("Database initialized and populated with sample data.")


# --- App Factory ---
def create_app():
    app = Flask(__name__)
    
    # Initialize the database
    with app.app_context():
        init_db(app)

    # Register the routes from routes.py
    from . import routes
    app.register_blueprint(routes.bp)

    return app
