from flask import Blueprint, request, jsonify, render_template, make_response
from . import services

bp = Blueprint('main', __name__)

# --- HTML Page Routes ---
@bp.route('/')
def index():
    """
    Homepage. This is the new captive portal landing page.
    It will grab the gateway_token from the URL.
    """
    return render_template('welcome.html')

@bp.route('/professor')
def professor_dashboard():
    return render_template('professor.html')

@bp.route('/student')
def student_portal():
    """
    This is the student portal with the register/mark forms.
    'home.html' is now served here.
    """
    return render_template('home.html')

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
    Handles new registration or re-binding an existing roll number
    to a new device with a professor's override code.
    """
    data = request.get_json()
    roll_no = data.get('roll_no', '').strip()
    override_code = data.get('override_code', '').strip()
    
    # Get the session token from the cookie
    gateway_token = request.cookies.get('gateway_token')

    if not roll_no:
        return jsonify({"success": False, "message": "Roll Number is required."}), 400

    if not gateway_token:
         return jsonify({"success": False, "message": "Not connected to session. Connect to the class Wi-Fi."}), 400

    # Call the updated service function
    result = services.register_student(roll_no, gateway_token, override_code)
    
    if not result["success"]:
        # This will return "Already registered" or "Invalid code"
        # The 'rebind' flag will be handled by the frontend
        return jsonify(result), 400
    
    # --- Success ---
    # This block runs for BOTH a new registration AND a successful rebind.
    # We set the new UUID as the cookie.
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
    Student marks attendance.
    """
    uuid_from_cookie = request.cookies.get('student_uuid')
    k_code = request.cookies.get('gateway_token')
    
    data = request.get_json()
    roll_no = data.get('roll_no', '').strip()
    
    if not all([uuid_from_cookie, roll_no, k_code]):
        return jsonify({
            "success": False,
            "message": "Missing data. You must register first and be connected to the class Wi-Fi."
        }), 400
    
    success, message = services.mark_attendance(uuid_from_cookie, roll_no, k_code)
    return jsonify({"success": success, "message": message})

@bp.route('/session/start', methods=['POST'])
def start_session():
    """
    Professor starts a new attendance session.
    """
    k_code = request.cookies.get('gateway_token')
    
    data = request.get_json()
    prof_id = data.get('prof_id', '').strip()
    class_code = data.get('class_code', '').strip()
    
    if not all([prof_id, class_code]):
        return jsonify({"success": False, "message": "Professor ID and Class Code are required."}), 400
    
    if not k_code:
        return jsonify({
            "success": False,
            "message": "Could not find gateway token. Are you connected to the ESP32 Wi-Fi?"
        }), 400
    
    services.start_new_session(prof_id, class_code, k_code)
    
    return jsonify({
        "success": True,
        "k_code": k_code, # This k_code is the gateway_token
        "message": f"Session started. Students can now mark attendance."
    })

@bp.route('/session/generate-override', methods=['POST'])
def generate_override():
    """
    Professor generates a one-time override code for re-registration.
    """
    gateway_token = request.cookies.get('gateway_token')
    
    if not gateway_token:
        return jsonify({"success": False, "message": "Not connected to session."}), 400

    code = services.generate_override_code(gateway_token)
    
    if not code:
        return jsonify({"success": False, "message": "No active session. Please start a session first."}), 400
        
    return jsonify({"success": True, "override_code": code})

@bp.route('/session/end', methods=['POST'])
def end_session():
    """
    Professor ends the session.
    """
    data = request.get_json()
    k_code = data.get('k_code', '').strip()
    
    if not k_code:
        return jsonify({"success": False, "message": "K-CODE (gateway_token) is required."}), 400
    
    success, message = services.end_session(k_code)
    return jsonify({"success": success, "message": message})

@bp.route('/attendance/manual-mark', methods=['POST'])
def manual_mark():
    """
    Professor manually marks a student present.
    """
    data = request.get_json()
    roll_no = data.get('roll_no', '').strip()
    k_code = data.get('k_code', '').strip()
    
    if not all([roll_no, k_code]):
        return jsonify({"success": False, "message": "Roll Number and K-CODE (gateway_token) are required."}), 400
    
    success, message = services.manual_mark_attendance(roll_no, k_code)
    return jsonify({"success": success, "message": message})

@bp.route('/session/attendance', methods=['GET'])
def get_attendance():
    """
    Return all active sessions and their attendees.
    """
    active_sessions = services.get_all_active_sessions()
    return jsonify(active_sessions)