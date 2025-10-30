from app import create_app
from app.ip_announcer import IPAnnouncer

app = create_app()

if __name__ == '__main__':
    print("\n" + "="*60)
    print("    AttendEase - Attendance Management System")
    print("="*60)
    
    # Create IP announcer
    announcer = IPAnnouncer(esp32_ip="192.168.4.1", flask_port=5000)
    
    print("\n📋 SETUP:")
    print("-" * 60)
    print("1. Make sure ESP32 is powered on and hotspot is active")
    print("2. Connect this laptop to: ClassAttendance_Prof001")
    print("3. This server will auto-announce its IP to ESP32")
    print("-" * 60)
    
    # Start announcing
    announcer.start()
    
    print("\n🚀 Starting Flask server on 0.0.0.0:5000...")
    print("="*60 + "\n")
    
    try:
        # Run Flask server
        app.run(host='0.0.0.0', port=5000, debug=True)
    finally:
        announcer.stop()