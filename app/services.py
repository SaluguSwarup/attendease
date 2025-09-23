import sqlite3
import random
import string
import hashlib
import os
from flask import current_app

sessions = {}

def get_db_connection():
    db_path = os.path.join(current_app.instance_path, 'database.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# In app/services.py

# In app/services.py

import uuid # Make sure to add this import at the top of your file

def register_device_for_student(roll_no):
    """
    Dynamically registers a student if they don't exist,
    then creates a secret token for their device.
    """
    conn = get_db_connection()
    student = conn.execute('SELECT uid FROM working_table WHERE roll_no = ?', (roll_no,)).fetchone()
    
    # --- THIS IS THE NEW LOGIC ---
    if not student:
        # If student does not exist, create them
        new_uid = f"uid_{uuid.uuid4().hex[:12]}" # Generate a new, unique UID
        conn.execute('INSERT INTO working_table (roll_no, uid) VALUES (?, ?)', (roll_no, new_uid))
        uid = new_uid
        print(f"New student created: {roll_no} -> {uid}")
    else:
        # If student exists, just get their UID
        uid = student['uid']
    # --- END OF NEW LOGIC ---

    device_token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    token_hash = hashlib.sha256(device_token.encode()).hexdigest()
    
    conn.execute('UPDATE working_table SET device_token_hash = ? WHERE roll_no = ?', (token_hash, roll_no))
    conn.commit()
    conn.close()
    
    return {
        "device_token": device_token, 
        "message": "Device registered successfully.",
        "uid": uid
    }

def validate_and_mark_attendance(uid_from_cookie, roll_no_from_form, device_token, k_code):
    """
    Performs a 3-way check:
    1. Does the cookie's UID match the form's Roll Number?
    2. Is the device token valid for that user?
    3. Is the K-CODE valid?
    """
    conn = get_db_connection()
    # 1. Check if cookie UID matches form Roll Number
    student = conn.execute('SELECT uid, device_token_hash FROM working_table WHERE roll_no = ?', (roll_no_from_form,)).fetchone()
    if not student or student['uid'] != uid_from_cookie:
        conn.close()
        return False, "Login mismatch. The logged-in user does not match the roll number provided."

    # 2. Check if device token is valid
    if not student['device_token_hash']:
        conn.close()
        return False, "Device not registered for this student."
        
    submitted_token_hash = hashlib.sha256(device_token.encode()).hexdigest()
    if submitted_token_hash != student['device_token_hash']:
        conn.close()
        return False, "Invalid Device for this Roll Number. Authentication failed."

    # 3. If all checks pass, validate K-CODE and mark attendance
    if k_code not in sessions:
        conn.close()
        return False, "Invalid K-CODE. No active session found."
    
    if roll_no_from_form in sessions[k_code]["attendees"]:
        conn.close()
        return False, "Attendance already marked for this session."

    class_code = sessions[k_code]["class_code"]
    conn.execute('INSERT INTO attendance_history (roll_no, course) VALUES (?, ?)', (roll_no_from_form, class_code))
    conn.commit()
    conn.close()
    
    sessions[k_code]["attendees"].add(roll_no_from_form)
    return True, f"Attendance marked for {roll_no_from_form} in class {class_code}."
# --- Keep all other functions the same ---
def start_new_session(prof_id, class_code):
    k_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    sessions[k_code] = { "prof_id": prof_id, "class_code": class_code, "attendees": set() }
    return k_code

def get_all_active_sessions():
    return {k: {**v, "attendees": list(v["attendees"])} for k, v in sessions.items()}

def get_working_table_data():
    conn = get_db_connection()
    students = conn.execute('SELECT roll_no, uid FROM working_table ORDER BY roll_no').fetchall()
    conn.close()
    return students

def end_session(k_code):
    if k_code in sessions:
        del sessions[k_code]
        return True, "Session has been successfully ended."
    return False, "Session not found or already ended."

def manual_mark_attendance(roll_no, k_code):
    if k_code not in sessions:
        return False, "Invalid K-CODE. The session is not active."
    conn = get_db_connection()
    student = conn.execute('SELECT uid FROM working_table WHERE roll_no = ?', (roll_no,)).fetchone()
    if not student:
        conn.close()
        return False, "This Roll Number does not exist in the system."
    if roll_no in sessions[k_code]["attendees"]:
        conn.close()
        return False, "This student is already marked present."
    class_code = sessions[k_code]["class_code"]
    conn.execute('INSERT INTO attendance_history (roll_no, course) VALUES (?, ?)', (roll_no, class_code))
    conn.commit()
    conn.close()
    sessions[k_code]["attendees"].add(roll_no)
    return True, f"Successfully marked {roll_no} as present."