# # app/routes.py
# from flask import Blueprint, request, jsonify, render_template
# from . import services

# # A Blueprint is a way to organize a group of related views and other code.
# bp = Blueprint('main', __name__)

# # --- HTML Page Routes ---

# @bp.route('/')
# def index():
#     return "Welcome to AttendEase! Navigate to /professor or /student."

# @bp.route('/professor')
# def professor_dashboard():
#     return render_template('professor.html')

# @bp.route('/student')
# def student_portal():
#     return render_template('student.html')


# # --- API Endpoint Routes ---

# @bp.route('/session/start', methods=['POST'])
# def start_session():
#     """Professor starts a session, generating a new K-CODE."""
#     k_code = services.start_new_session()
#     return jsonify({"success": True, "k_code": k_code})

# @bp.route('/attendance/mark', methods=['POST'])
# def mark_attendance():
#     """Student submits their UID and generated X-CODE."""
#     data = request.get_json()
#     uid = data.get('uid')
#     x_code = data.get('x_code')
    
#     if not uid or not x_code:
#         return jsonify({"success": False, "message": "Missing UID or X-CODE."}), 400

#     success, message = services.validate_and_mark_attendance(uid, x_code)
    
#     return jsonify({"success": success, "message": message})

# @bp.route('/session/attendance', methods=['GET'])
# def get_attendance():
#     """Professor dashboard polls this to get a live list of attendees."""
#     attendees = services.get_session_attendance()
#     k_code = services.get_current_k_code()
#     return jsonify({"k_code": k_code, "attendees": attendees})
    
# app/routes.py

from flask import Blueprint, request, jsonify, render_template, make_response
from . import services

bp = Blueprint('main', __name__)

# --- HTML Page Routes ---
# THIS IS THE MISSING SECTION
@bp.route('/')
def index():
    return "Welcome to AttendEase! Navigate to /professor or /student."

@bp.route('/professor')
def professor_dashboard():
    return render_template('professor.html')

@bp.route('/student')
def student_portal():
    return render_template('student.html')


# --- API Endpoint Routes ---

@bp.route('/api/login', methods=['POST'])
def student_login():
    data = request.get_json()
    roll_no = data.get('roll_no')
    
    conn = services.get_db_connection()
    student = conn.execute('SELECT uid FROM working_table WHERE roll_no = ?', (roll_no,)).fetchone()
    conn.close()

    if not student:
        return jsonify({"success": False, "message": "Roll Number not found."}), 404
        
    uid = student['uid']
    
    # response = make_response(jsonify({"success": True, "message": "Device registered successfully!"}))
    response = make_response(jsonify({"success": True, "message": "Device registered successfully!", "uid": uid}))
    response.set_cookie('student_uid', uid, max_age=60*60*24*30, httponly=True, samesite='Lax')
    
    return response


@bp.route('/attendance/mark', methods=['POST'])
def mark_attendance():
    uid = request.cookies.get('student_uid')
    if not uid:
        return jsonify({"success": False, "message": "Authentication error. Please register device again."}), 401

    data = request.get_json()
    x_code = data.get('x_code')
    
    if not x_code:
        return jsonify({"success": False, "message": "Missing X-CODE."}), 400

    success, message = services.validate_and_mark_attendance(uid, x_code)
    
    return jsonify({"success": success, "message": message})


@bp.route('/session/start', methods=['POST'])
def start_session():
    k_code = services.start_new_session()
    return jsonify({"success": True, "k_code": k_code})


@bp.route('/session/attendance', methods=['GET'])
def get_attendance():
    attendees = services.get_session_attendance()
    k_code = services.get_current_k_code()
    return jsonify({"k_code": k_code, "attendees": attendees})

@bp.route('/working-table')
def working_table_page():
    student_data = services.get_working_table_data()
    return render_template('working_table.html', students=student_data)

@bp.route('/attendance')
def attendance_page():
    return render_template('attendance.html')