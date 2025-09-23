# app/services.py
import sqlite3
import random
import string
import hashlib
from flask import current_app
import os

# # [cite_start]--- Global variable to simulate session management --- [cite: 49]
# # In a real app, you'd use a more robust solution like Redis or a database table
# current_session = {
#     "k_code": None,
#     "used_x_codes": set()
# }

# def get_db_connection():
#     """Helper function to connect to the database."""
#     db_path = os.path.join(current_app.instance_path, 'database.db')
#     conn = sqlite3.connect(db_path)
#     conn.row_factory = sqlite3.Row
#     return conn

# def start_new_session():
#     """Generates a new K-CODE and resets the session."""
#     # [cite_start]K-CODE: A random, per-session code [cite: 17]
#     k_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
#     current_session["k_code"] = k_code
#     current_session["used_x_codes"] = set()
#     return k_code

# def get_current_k_code():
#     """Returns the active K-CODE."""
#     return current_session["k_code"]

# def validate_and_mark_attendance(uid, x_code):
#     """
#     Validates the X-CODE and marks attendance if successful.
#     Returns (success_boolean, message_string).
#     """
#     k_code = current_session["k_code"]
#     if not k_code:
#         return False, "No active attendance session."

#     # [cite_start]1. Check if X-CODE has already been used in this session [cite: 35]
#     if x_code in current_session["used_x_codes"]:
#         return False, "Attendance already marked with this code."

#     # [cite_start]2. Find the student's roll_no from their UID [cite: 35]
#     conn = get_db_connection()
#     student = conn.execute('SELECT roll_no FROM working_table WHERE uid = ?', (uid,)).fetchone()
#     if not student:
#         conn.close()
#         return False, "Invalid UID. Have you cleared cookies or switched devices?"

#     roll_no = student['roll_no']
    
#     # [cite_start]3. Re-create the X-CODE on the server and compare [cite: 32, 55]
#     # [cite_start]X-CODE is a hash of UID and K-CODE [cite: 18]
#     server_hash = hashlib.sha256((uid + k_code).encode()).hexdigest()

#     if server_hash != x_code:
#         conn.close()
#         return False, "Validation failed. Invalid X-CODE."
    
#     # 4. If everything is valid, mark attendance
#     conn.execute('INSERT INTO attendance_history (roll_no, course) VALUES (?, ?)', (roll_no, 'CS101'))
#     conn.commit()
#     conn.close()

#     # [cite_start]Add the used X-CODE to the set to prevent reuse [cite: 35]
#     current_session["used_x_codes"].add(x_code)
    
#     return True, f"Attendance marked successfully for {roll_no}."

# def get_session_attendance():
#     """Retrieves the list of students marked present in the current session."""
#     if not current_session["k_code"]:
#         return []
    
#     # In a more robust system, you'd filter by a session ID
#     # For this PoC, we'll just show the latest entries
#     conn = get_db_connection()
#     # We get the roll numbers from the `used_x_codes` after validation
#     # A better query would be to fetch from attendance_history based on session start time
    
#     # For simplicity, we will query based on the roll numbers associated with valid UIDs
#     # that have been processed. This is a bit of a shortcut for the PoC.
#     query = f"""
#         SELECT T1.roll_no
#         FROM working_table T1
#         INNER JOIN attendance_history T2 ON T1.roll_no = T2.roll_no
#         ORDER BY T2.timestamp DESC
#         LIMIT {len(current_session['used_x_codes'])}
#     """
#     attendees = conn.execute(query).fetchall()
#     conn.close()
    
#     return [attendee['roll_no'] for attendee in attendees]

# app/services.py
import sqlite3
import random
import string
import hashlib
from flask import current_app
import os

# --- Global variable to simulate session management ---
current_session = {
    "k_code": None,
    "used_x_codes": set()
}

def get_db_connection():
    """Helper function to connect to the database."""
    db_path = os.path.join(current_app.instance_path, 'database.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def start_new_session():
    """Generates a new K-CODE and resets the session."""
    # Add this line to tell Python you are modifying the global variable
    global current_session
    
    k_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    current_session["k_code"] = k_code
    current_session["used_x_codes"] = set()
    return k_code

def get_current_k_code():
    """Returns the active K-CODE."""
    # No 'global' needed here because we are only reading, not changing.
    return current_session["k_code"]

def validate_and_mark_attendance(uid, x_code):
    """
    Validates the X-CODE and marks attendance if successful.
    """
    # Add this line as well, since we modify the 'used_x_codes' set
    global current_session
    
    k_code = current_session["k_code"]
    if not k_code:
        return False, "No active attendance session."

    server_hash = hashlib.sha256(k_code.encode()).hexdigest()

    if server_hash != x_code:
        return False, "Validation failed. Invalid K-CODE hash."

    session_identifier = f"{uid}-{x_code}"
    if session_identifier in current_session["used_x_codes"]:
        return False, "Attendance already marked for this session."
    
    conn = get_db_connection()
    student = conn.execute('SELECT roll_no FROM working_table WHERE uid = ?', (uid,)).fetchone()
    if not student:
        conn.close()
        return False, "Invalid UID."

    roll_no = student['roll_no']
    
    conn.execute('INSERT INTO attendance_history (roll_no, course) VALUES (?, ?)', (roll_no, 'CS101'))
    conn.commit()
    conn.close()

    current_session["used_x_codes"].add(session_identifier)
    
    return True, f"Attendance marked successfully for {roll_no}."

def get_session_attendance():
    """Retrieves the list of students marked present in the current session."""
    if not current_session["k_code"]:
        return []
    
    # This simplified query is for the PoC
    query = f"""
        SELECT T1.roll_no
        FROM working_table T1
        INNER JOIN attendance_history T2 ON T1.roll_no = T2.roll_no
        ORDER BY T2.timestamp DESC
        LIMIT {len(current_session['used_x_codes'])}
    """
    conn = get_db_connection()
    attendees = conn.execute(query).fetchall()
    conn.close()
    
    return [attendee['roll_no'] for attendee in attendees]

def get_working_table_data():
    """Fetches all records from the working_table."""
    conn = get_db_connection()
    students = conn.execute('SELECT roll_no, uid FROM working_table ORDER BY roll_no').fetchall()
    conn.close()
    return students