from flask import Blueprint, request, jsonify, render_template, make_response
from . import services

bp = Blueprint('main', __name__)

# --- HTML Page Routes (No Changes) ---
@bp.route('/')
def index():
    return "Welcome! Navigate to /professor or /student."
@bp.route('/professor')
def professor_dashboard():
    return render_template('professor.html')
@bp.route('/student')
def student_portal():
    return render_template('student.html')
@bp.route('/working-table')
def working_table_page():
    student_data = services.get_working_table_data()
    return render_template('working_table.html', students=student_data)
@bp.route('/attendance')
def attendance_page():
    return render_template('attendance.html')

# --- API Endpoint Routes ---
@bp.route('/api/register-device', methods=['POST'])
def register_device():
    data = request.get_json()
    roll_no = data.get('roll_no')
    if not roll_no:
        return jsonify({"success": False, "message": "Roll Number is required."}), 400
    
    # This service function now returns the UID as well
    result = services.register_device_for_student(roll_no)
    device_token = result.get('device_token')
    message = result.get('message')
    uid = result.get('uid')

    if not device_token:
        return jsonify({"success": False, "message": message}), 404
    
    # Create a response that includes the token for localStorage
    response = make_response(jsonify({"success": True, "message": message, "device_token": device_token}))
    
    # ALSO set the secure HttpOnly cookie to log the user in
    response.set_cookie('student_uid', uid, max_age=60*60*24*30, httponly=True, samesite='Lax')
    
    return response

@bp.route('/attendance/mark', methods=['POST'])
def mark_attendance():
    # 1. Get UID from the secure cookie
    uid_from_cookie = request.cookies.get('student_uid')

    # 2. Get other details from the form submission
    data = request.get_json()
    roll_no_from_form = data.get('roll_no')
    device_token = data.get('device_token')
    k_code = data.get('k_code')

    if not all([uid_from_cookie, roll_no_from_form, device_token, k_code]):
        return jsonify({"success": False, "message": "Missing required data. You may need to log in or register your device."}), 400

    # 3. Pass everything to the service for the 3-way check
    success, message = services.validate_and_mark_attendance(
        uid_from_cookie, roll_no_from_form, device_token, k_code
    )
    return jsonify({"success": success, "message": message})

# --- All other routes remain the same ---
@bp.route('/session/start', methods=['POST'])
def start_session():
    data = request.get_json()
    prof_id = data.get('prof_id')
    class_code = data.get('class_code')
    k_code = services.start_new_session(prof_id, class_code)
    return jsonify({"success": True, "k_code": k_code})

@bp.route('/session/end', methods=['POST'])
def end_session():
    data = request.get_json()
    k_code = data.get('k_code')
    success, message = services.end_session(k_code)
    return jsonify({"success": success, "message": message})

@bp.route('/attendance/manual-mark', methods=['POST'])
def manual_mark():
    data = request.get_json()
    roll_no = data.get('roll_no')
    k_code = data.get('k_code')
    success, message = services.manual_mark_attendance(roll_no, k_code)
    return jsonify({"success": success, "message": message})

@bp.route('/session/attendance', methods=['GET'])
def get_attendance():
    active_sessions = services.get_all_active_sessions()
    return jsonify(active_sessions)