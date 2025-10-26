import sqlite3
import random
import string
import hashlib
import os
import uuid
from flask import current_app

sessions = {}

def get_db_connection():
    db_path = os.path.join(current_app.instance_path, 'database.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def register_student(roll_no):
    """
    One-time registration: Creates a student with a UUID if they don't exist.
    Returns the UUID to be set as a permanent cookie.
    """
    conn = get_db_connection()
    student = conn.execute('SELECT uid FROM working_table WHERE roll_no = ?', (roll_no,)).fetchone()
    
    if student:
        # Student already registered
        conn.close()
        return {
            "success": True,
            "message": f"Welcome back! Roll Number {roll_no} is already registered.",
            "uid": student['uid']
        }
    
    # Create new student with unique UUID
    new_uid = f"{uuid.uuid4().hex[:12]}"
    conn.execute('INSERT INTO working_table (roll_no, uid) VALUES (?, ?)', (roll_no, new_uid))
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "message": f"Registration successful! Roll Number {roll_no} registered.",
        "uid": new_uid
    }

def start_new_session(prof_id, class_code):
    """
    Professor starts a session. Generates a K code that is written on whiteboard.
    K code is the only thing transmitted digitally (and locally over LAN).
    """
    k_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    sessions[k_code] = {
        "prof_id": prof_id,
        "class_code": class_code,
        "attendees": set(),
        "active": True
    }
    return k_code

def mark_attendance(uuid_from_cookie, roll_no_from_form, k_code):
    """
    Student marks attendance. Performs the 3-way check:
    1. Is the K-CODE valid and active?
    2. Does the UUID cookie match the roll number in the database?
    3. Is this student already marked for this session?
    
    If all checks pass, student is marked present.
    """
    # 1. Validate K-CODE
    if k_code not in sessions or not sessions[k_code]["active"]:
        return False, "Invalid or expired K-CODE. Check with your professor."
    
    # 2. Validate UUID matches roll number
    conn = get_db_connection()
    student = conn.execute('SELECT uid FROM working_table WHERE roll_no = ?', (roll_no_from_form,)).fetchone()
    
    if not student:
        conn.close()
        return False, f"Roll Number {roll_no_from_form} not found in system. Register first."
    
    if student['uid'] != uuid_from_cookie:
        conn.close()
        return False, "UUID mismatch. You cannot mark attendance for another student. (This would require their phone.)"
    
    # 3. Check if already marked
    if roll_no_from_form in sessions[k_code]["attendees"]:
        conn.close()
        return False, "You are already marked present for this session."
    
    # All checks passed: Mark attendance
    class_code = sessions[k_code]["class_code"]
    conn.execute(
        'INSERT INTO attendance_history (roll_no, course) VALUES (?, ?)',
        (roll_no_from_form, class_code)
    )
    conn.commit()
    conn.close()
    
    sessions[k_code]["attendees"].add(roll_no_from_form)
    return True, f"Attendance marked for {roll_no_from_form} in {class_code}. ✓"

def end_session(k_code):
    """
    Professor ends session. Locks the session and makes K-CODE invalid.
    Session data persists in attendance_history for permanent records.
    """
    if k_code not in sessions:
        return False, "Session not found."
    
    sessions[k_code]["active"] = False
    return True, f"Session {k_code} ended. Attendance locked. Data saved to permanent records."

def manual_mark_attendance(roll_no, k_code):
    """
    Professor can manually mark a student present (e.g., for late arrivals).
    """
    if k_code not in sessions or not sessions[k_code]["active"]:
        return False, "Invalid or expired K-CODE. Session not active."
    
    conn = get_db_connection()
    student = conn.execute('SELECT uid FROM working_table WHERE roll_no = ?', (roll_no,)).fetchone()
    
    if not student:
        conn.close()
        return False, f"Roll Number {roll_no} not found in system."
    
    if roll_no in sessions[k_code]["attendees"]:
        conn.close()
        return False, f"{roll_no} is already marked present."
    
    class_code = sessions[k_code]["class_code"]
    conn.execute(
        'INSERT INTO attendance_history (roll_no, course) VALUES (?, ?)',
        (roll_no, class_code)
    )
    conn.commit()
    conn.close()
    
    sessions[k_code]["attendees"].add(roll_no)
    return True, f"{roll_no} manually marked present."

def get_all_active_sessions():
    """
    Return all active sessions for the attendance dashboard.
    """
    result = {}
    for k, v in sessions.items():
        if v["active"]:
            result[k] = {
                "prof_id": v["prof_id"],
                "class_code": v["class_code"],
                "attendees": list(v["attendees"])
            }
    return result

def get_working_table_data():
    """
    Retrieve all students and their UIDs for the admin view.
    """
    conn = get_db_connection()
    students = conn.execute('SELECT roll_no, uid FROM working_table ORDER BY roll_no').fetchall()
    conn.close()
    return students