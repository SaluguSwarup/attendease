from flask import Blueprint, request, jsonify, render_template, make_response
from . import services

bp = Blueprint('main', __name__)

# --- HTML Page Routes ---
@bp.route('/')
def index():
    """
    Homepage. If student has UUID cookie, show attendance form.
    Otherwise, show registration form.
    """
    return render_template('home.html')

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

@bp.route('/api/register', methods=['POST'])
def register():
    """
    One-time registration. Student enters roll number.
    Server creates UUID and sets it as a permanent HttpOnly cookie.
    """
    data = request.get_json()
    roll_no = data.get('roll_no', '').strip()
    
    if not roll_no:
        return jsonify({"success": False, "message": "Roll Number is required."}), 400
    
    result = services.register_student(roll_no)
    
    if not result["success"]:
        return jsonify(result), 400
    
    # Set UUID as a permanent HttpOnly cookie
    response = make_response(jsonify({
        "success": True,
        "message": result["message"]
    }))
    response.set_cookie(
        'student_uuid',
        result['uid'],
        max_age=60*60*24*365,  # 1 year
        httponly=True,
        samesite='Lax'
    )
    
    return response

@bp.route('/attendance/mark', methods=['POST'])
def mark_attendance():
    """
    Student marks attendance. Server performs 3-way validation:
    1. UUID from cookie matches roll number
    2. K-CODE is valid and active
    3. Student not already marked
    """
    # Get UUID from secure cookie
    uuid_from_cookie = request.cookies.get('student_uuid')
    
    # Get form data
    data = request.get_json()
    roll_no = data.get('roll_no', '').strip()
    k_code = data.get('k_code', '').strip()
    
    if not all([uuid_from_cookie, roll_no, k_code]):
        return jsonify({
            "success": False,
            "message": "Missing data. You must register first and enter both Roll Number and K-CODE."
        }), 400
    
    success, message = services.mark_attendance(uuid_from_cookie, roll_no, k_code)
    return jsonify({"success": success, "message": message})

@bp.route('/session/start', methods=['POST'])
def start_session():
    """
    Professor starts a new attendance session.
    Returns a K-CODE to write on the whiteboard.
    """
    data = request.get_json()
    prof_id = data.get('prof_id', '').strip()
    class_code = data.get('class_code', '').strip()
    
    if not all([prof_id, class_code]):
        return jsonify({"success": False, "message": "Professor ID and Class Code are required."}), 400
    
    k_code = services.start_new_session(prof_id, class_code)
    return jsonify({
        "success": True,
        "k_code": k_code,
        "message": f"Session started. Write K-CODE '{k_code}' on the whiteboard."
    })

@bp.route('/session/end', methods=['POST'])
def end_session():
    """
    Professor ends the session. K-CODE becomes invalid.
    Attendance data is already persisted in database.
    """
    data = request.get_json()
    k_code = data.get('k_code', '').strip()
    
    if not k_code:
        return jsonify({"success": False, "message": "K-CODE is required."}), 400
    
    success, message = services.end_session(k_code)
    return jsonify({"success": success, "message": message})

@bp.route('/attendance/manual-mark', methods=['POST'])
def manual_mark():
    """
    Professor manually marks a student present (e.g., late arrival).
    """
    data = request.get_json()
    roll_no = data.get('roll_no', '').strip()
    k_code = data.get('k_code', '').strip()
    
    if not all([roll_no, k_code]):
        return jsonify({"success": False, "message": "Roll Number and K-CODE are required."}), 400
    
    success, message = services.manual_mark_attendance(roll_no, k_code)
    return jsonify({"success": success, "message": message})

@bp.route('/session/attendance', methods=['GET'])
def get_attendance():
    """
    Return all active sessions and their attendees.
    Used by the live attendance dashboard.
    """
    active_sessions = services.get_all_active_sessions()
    return jsonify(active_sessions)