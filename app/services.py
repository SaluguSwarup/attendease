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

def register_student(roll_no, gateway_token, override_code):
    """
    Handles new registration or re-binding of an existing student to a new device.
    """
    conn = get_db_connection()
    student = conn.execute('SELECT uid FROM working_table WHERE roll_no = ?', (roll_no,)).fetchone()
    
    if not student:
        # CASE 1: New student. Register them as normal.
        new_uid = f"{uuid.uuid4().hex[:12]}"
        conn.execute('INSERT INTO working_table (roll_no, uid) VALUES (?, ?)', (roll_no, new_uid))
        conn.commit()
        conn.close()
        return {
            "success": True,
            "message": f"Registration successful! Roll Number {roll_no} registered.",
            "uid": new_uid
        }

    # --- Student Already Exists ---

    if not override_code:
        # CASE 2: Existing student, first attempt.
        # Tell the frontend to ask for an override code.
        conn.close()
        return {
            "success": False,
            "message": f"{roll_no} is already registered. Ask professor for an Override Code to use this new device.",
            "rebind": True # Special flag for the frontend
        }
    
    # CASE 3 & 4: Existing student, attempting with an override code.
    
    # Check if the override code is valid for this session
    if (gateway_token not in sessions or 
        'override_code' not in sessions[gateway_token] or
        sessions[gateway_token]['override_code'] != override_code):
        
        conn.close()
        return {
            "success": False,
            "message": "Invalid or expired Override Code. Ask the professor for a new one."
        }

    # CASE 4: Success! The override code is valid.
    # We generate a NEW UID and overwrite the old one in the database.
    # This invalidates the old device's cookie.
    new_uid = f"{uuid.uuid4().hex[:12]}"
    conn.execute('UPDATE working_table SET uid = ? WHERE roll_no = ?', (new_uid, roll_no))
    conn.commit()
    conn.close()
    
    # Invalidate the used override code
    sessions[gateway_token].pop('override_code', None)
    
    return {
        "success": True,
        "message": f"Device re-bind successful! {roll_no} is now registered to this device.",
        "uid": new_uid
    }


def start_new_session(prof_id, class_code, k_code):
    """
    Professor starts a session.
    The K-CODE is the gateway_token from the ESP32.
    """
    sessions[k_code] = {
        "prof_id": prof_id,
        "class_code": class_code,
        "attendees": set(),
        "active": True
    }
    return k_code

def generate_override_code(gateway_token):
    """
    Generates a 6-digit code for device re-binding
    and stores it in the active session.
    """
    if gateway_token not in sessions or not sessions[gateway_token]["active"]:
        return None
    
    code = ''.join(random.choices(string.digits, k=6))
    sessions[gateway_token]["override_code"] = code
    return code

def mark_attendance(uuid_from_cookie, roll_no_from_form, k_code):
    """
    Student marks attendance. Performs the 3-way check.
    """
    # 1. Validate K-CODE (which is the gateway_token from the cookie)
    if k_code not in sessions or not sessions[k_code]["active"]:
        return False, "Invalid or expired session. Are you connected to the right Wi-Fi?"
    
    # 2. Validate UUID matches roll number
    conn = get_db_connection()
    student = conn.execute('SELECT uid FROM working_table WHERE roll_no = ?', (roll_no_from_form,)).fetchone()
    
    if not student:
        conn.close()
        return False, f"Roll Number {roll_no_from_form} not found in system. Register first."
    
    if student['uid'] != uuid_from_cookie:
        conn.close()
        # This error is now critical. It means their cookie is from an old device.
        return False, "UUID mismatch. Your device is not registered. Please re-register this device (you will need an Override Code from the professor)."
    
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
    Professor ends session. Locks the session.
    """
    if k_code not in sessions:
        return False, "Session not found."
    
    # Clear override code if one exists
    sessions[k_code].pop('override_code', None)
    sessions[k_code]["active"] = False
    
    return True, f"Session {k_code} ended. Attendance locked."

def manual_mark_attendance(roll_no, k_code):
    """
    Professor can manually mark a student present.
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