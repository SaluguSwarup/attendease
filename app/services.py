import sqlite3
import random
import string
import hashlib
from flask import current_app
import os

# This dictionary will hold all active sessions, keyed by K-CODE
sessions = {}

def get_db_connection():
    db_path = os.path.join(current_app.instance_path, 'database.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def start_new_session(prof_id, class_code):
    """Generates a K-CODE for a specific professor/class and stores it."""
    k_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    # Store session details in our new dictionary
    sessions[k_code] = {
        "prof_id": prof_id,
        "class_code": class_code,
        "attendees": set()  # Store roll numbers of attendees for this session
    }
    return k_code

def validate_and_mark_attendance(uid, k_code):
    """
    Validates a K-CODE and marks attendance for the specific session it belongs to.
    """
    # 1. Check if the K-CODE corresponds to an active session
    if k_code not in sessions:
        return False, "Invalid K-CODE. No active session found."

    # 2. Get the student's roll number from their UID
    conn = get_db_connection()
    student = conn.execute('SELECT roll_no FROM working_table WHERE uid = ?', (uid,)).fetchone()
    if not student:
        conn.close()
        return False, "Invalid UID."
        
    roll_no = student['roll_no']
    
    # 3. Check if this student has already marked attendance for this session
    if roll_no in sessions[k_code]["attendees"]:
        conn.close()
        return False, "Attendance already marked for this session."

    # 4. Mark attendance in the history table
    class_code = sessions[k_code]["class_code"]
    conn.execute('INSERT INTO attendance_history (roll_no, course) VALUES (?, ?)', (roll_no, class_code))
    conn.commit()
    conn.close()

    # 5. Add the student to the live session list
    sessions[k_code]["attendees"].add(roll_no)
    
    return True, f"Attendance marked for {roll_no} in class {class_code}."

def get_all_active_sessions():
    """Returns all active sessions and their attendees."""
    # Convert sets to lists so they can be sent as JSON
    active_sessions = {
        k_code: {**details, "attendees": list(details["attendees"])}
        for k_code, details in sessions.items()
    }
    return active_sessions
def get_working_table_data():
    """Fetches all records from the working_table."""
    conn = get_db_connection()
    students = conn.execute('SELECT roll_no, uid FROM working_table ORDER BY roll_no').fetchall()
    conn.close()
    return students
def manual_mark_attendance(roll_no, k_code):
    """Marks a student present manually for a given session."""
    # 1. Check if the session is valid
    if k_code not in sessions:
        return False, "Invalid K-CODE. The session is not active."

    # 2. Check if the roll number is valid
    conn = get_db_connection()
    student = conn.execute('SELECT uid FROM working_table WHERE roll_no = ?', (roll_no,)).fetchone()
    if not student:
        conn.close()
        return False, "This Roll Number does not exist in the system."

    # 3. Check if already marked
    if roll_no in sessions[k_code]["attendees"]:
        conn.close()
        return False, "This student is already marked present."

    # 4. Mark attendance in history and live session
    class_code = sessions[k_code]["class_code"]
    conn.execute('INSERT INTO attendance_history (roll_no, course) VALUES (?, ?)', (roll_no, class_code))
    conn.commit()
    conn.close()
    
    sessions[k_code]["attendees"].add(roll_no)
    
    return True, f"Successfully marked {roll_no} as present."