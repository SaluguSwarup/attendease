import sqlite3
import random
import string
import hashlib
import os
import uuid
from flask import current_app
# --- NEW IMPORTS ---
from werkzeug.security import generate_password_hash, check_password_hash

sessions = {}

# --- NEW PROFESSOR LOGIC ---
# Passwords are NOT stored. Only the HASH is stored.
PROFESSOR_CREDS = {
    'Swarup': generate_password_hash('12345'),
    'Prasenjit Chanak Sir': generate_password_hash('12345')
}

def verify_professor(name, password):
    """
    Securely checks the professor's name and password.
    """
    if name not in PROFESSOR_CREDS:
        return False
    
    # Check the provided password against the stored hash
    return check_password_hash(PROFESSOR_CREDS[name], password)

# --- END NEW PROFESSOR LOGIC ---


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
        conn.close()
        return {
            "success": False,
            "message": f"{roll_no} is already registered. Ask professor for an Override Code to use this new device.",
            "rebind": True # Special flag for the frontend
        }
    
    # CASE 3 & 4: Existing student, attempting with an override code.
    
    if (gateway_token not in sessions or 
        'override_code' not in sessions[gateway_token] or
        sessions[gateway_token]['override_code'] != override_code):
        
        conn.close()
        return {
            "success": False,
            "message": "Invalid or expired Override Code. Ask the professor for a new one."
        }

    # CASE 4: Success! The override code is valid.
    new_uid = f"{uuid.uuid4().hex[:12]}"
    conn.execute('UPDATE working_table SET uid = ? WHERE roll_no = ?', (new_uid, roll_no))
    conn.commit()
    conn.close()
    
    sessions[gateway_token].pop('override_code', None)
    
    return {
        "success": True,
        "message": f"Device re-bind successful! {roll_no} is now registered to this device.",
        "uid": new_uid
    }


def start_new_session(prof_id, class_code, k_code):
    """
    k_code is the gateway_token.
    """
    sessions[k_code] = {
        "prof_id": prof_id,
        "class_code": class_code,
        "attendees": set(),
        "active": True,
        "marked_gateways": set() # <-- FIX: Set to track used devices
    }
    return k_code

def generate_override_code(gateway_token):
    if gateway_token not in sessions or not sessions[gateway_token]["active"]:
        return None
    
    code = ''.join(random.choices(string.digits, k=6))
    sessions[gateway_token]["override_code"] = code
    return code

def mark_attendance(uuid_from_cookie, roll_no_from_form, k_code):
    """
    k_code is the gateway_token.
    """
    # 1. Validate Session
    if k_code not in sessions or not sessions[k_code]["active"]:
        return False, "Invalid or expired session. Are you connected to the right Wi-Fi?"
    
    # 2. FIX: Validate Device (One Mark Per Device)
    if k_code in sessions[k_code]["marked_gateways"]:
        return False, "This device has already marked attendance for this session."
    
    # 3. Validate Student
    conn = get_db_connection()
    student = conn.execute('SELECT uid FROM working_table WHERE roll_no = ?', (roll_no_from_form,)).fetchone()
    
    if not student:
        conn.close()
        return False, f"Roll Number {roll_no_from_form} not found in system. Register first."
    
    # 4. Validate UID
    if student['uid'] != uuid_from_cookie:
        conn.close()
        return False, "UUID mismatch. Your device is not registered. Please re-register this device (you will need an Override Code from the professor)."
    
    # 5. Validate for Duplicates (Student)
    if roll_no_from_form in sessions[k_code]["attendees"]:
        conn.close()
        return False, "You are already marked present for this session."
    
    # --- All Checks Passed ---
    
    # A. Mark attendance
    class_code = sessions[k_code]["class_code"]
    conn.execute(
        'INSERT INTO attendance_history (roll_no, course) VALUES (?, ?)',
        (roll_no_from_form, class_code)
    )
    conn.commit()
    conn.close()
    
    # B. Add to sets to prevent re-use
    sessions[k_code]["attendees"].add(roll_no_from_form)
    sessions[k_code]["marked_gateways"].add(k_code) # <-- FIX: "Use up" this device
    
    return True, f"Attendance marked for {roll_no_from_form} in {class_code}. ✓"

def end_session(k_code):
    if k_code not in sessions:
        return False, "Session not found."
    
    sessions[k_code].pop('override_code', None)
    sessions[k_code]["active"] = False
    
    return True, f"Session {k_code} ended. Attendance locked."

def manual_mark_attendance(roll_no, k_code):
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
    conn = get_db_connection()
    students = conn.execute('SELECT roll_no, uid FROM working_table ORDER BY roll_no').fetchall()
    conn.close()
    return students