# app/__init__.py
import os
import sqlite3
from flask import Flask

def init_db(app):
    db_path = os.path.join(app.instance_path, 'database.db')
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db = sqlite3.connect(db_path)
    cursor = db.cursor()

# --- THIS IS THE SIMPLIFIED TABLE STRUCTURE ---
# It no longer includes the device_token_hash column
    cursor.execute('''
CREATE TABLE IF NOT EXISTS working_table (
    roll_no TEXT PRIMARY KEY,
    uid TEXT NOT NULL UNIQUE
)''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendance_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        roll_no TEXT NOT NULL,
        course TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    sample_students = [
        ('2301001', 'uid_student_alpha'),
        ('2301002', 'uid_student_beta'),
        ('2301003', 'uid_student_gamma'),
        ('2301004', 'uid_student_delta'),
        ('2301005', 'uid_student_epsilon')
    ]
    cursor.executemany('INSERT OR IGNORE INTO working_table (roll_no, uid) VALUES (?, ?)', sample_students)

    db.commit()
    db.close()
    print("Database initialized and populated with sample data.")

def create_app():
    app = Flask(__name__)
    with app.app_context():
        init_db(app)
    from . import routes
    app.register_blueprint(routes.bp)
    return app