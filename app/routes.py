from flask import Blueprint, request, jsonify, render_template, make_response
from . import services

bp = Blueprint('main', __name__)

# --- HTML Page Routes ---
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
@bp.route('/api/login', methods=['POST'])
def student_login():
    # This function remains the same
    data = request.get_json()
    roll_no = data.get('roll_no')
    conn = services.get_db_connection()
    student = conn.execute('SELECT uid FROM working_table WHERE roll_no = ?', (roll_no,)).fetchone()
    conn.close()
    if not student:
        return jsonify({"success": False, "message": "Roll Number not found."}), 404
    uid = student['uid']
    response = make_response(jsonify({"success": True, "message": "Device registered successfully!", "uid": uid}))
    response.set_cookie('student_uid', uid, max_age=60*60*24*30, httponly=True, samesite='Lax')
    return response

@bp.route('/session/start', methods=['POST'])
def start_session():
    # Now accepts professor and class info
    data = request.get_json()
    prof_id = data.get('prof_id')
    class_code = data.get('class_code')
    if not prof_id or not class_code:
        return jsonify({"success": False, "message": "Professor ID and Class Code are required."}), 400
        
    k_code = services.start_new_session(prof_id, class_code)
    return jsonify({"success": True, "k_code": k_code})

@bp.route('/attendance/mark', methods=['POST'])
def mark_attendance():
    # Student now submits the raw K-CODE
    uid = request.cookies.get('student_uid')
    if not uid:
        return jsonify({"success": False, "message": "Authentication error. Please register device again."}), 401

    data = request.get_json()
    k_code = data.get('k_code')
    if not k_code:
        return jsonify({"success": False, "message": "Missing K-CODE."}), 400

    success, message = services.validate_and_mark_attendance(uid, k_code)
    return jsonify({"success": success, "message": message})

@bp.route('/session/attendance', methods=['GET'])
def get_attendance():
    # This now returns ALL active sessions
    active_sessions = services.get_all_active_sessions()
    return jsonify(active_sessions)
@bp.route('/attendance/manual-mark', methods=['POST'])
def manual_mark():
    data = request.get_json()
    roll_no = data.get('roll_no')
    k_code = data.get('k_code')

    if not roll_no or not k_code:
        return jsonify({"success": False, "message": "Roll number and K-CODE are required."}), 400

    success, message = services.manual_mark_attendance(roll_no, k_code)
    
    return jsonify({"success": success, "message": message})