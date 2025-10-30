# app/ip_announcer.py (NEW FILE)
import socket
import requests
import threading
import time

class IPAnnouncer:
    def __init__(self, esp32_ip="192.168.4.1", flask_port=5000):
        self.esp32_ip = esp32_ip
        self.flask_port = flask_port
        self.my_ip = None
        self.running = False
        self.thread = None
    
    def get_my_ip(self):
        """Get the IP address assigned to this device on the ESP32 network"""
        try:
            # Get all network interfaces
            hostname = socket.gethostname()
            
            # Get IP addresses
            ip_list = socket.gethostbyname_ex(hostname)[2]
            
            # Find the one in 192.168.4.x range (ESP32's subnet)
            for ip in ip_list:
                if ip.startswith("192.168.4.") and ip != "192.168.4.1":
                    return ip
            
            # Fallback: connect to external address to determine local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            
            # Check if it's in ESP32 subnet
            if local_ip.startswith("192.168.4."):
                return local_ip
            
            return None
        except Exception as e:
            print(f"Error getting IP: {e}")
            return None
    
    def announce_to_esp32(self):
        """Send IP announcement to ESP32's /register-server endpoint"""
        if not self.my_ip:
            return False
        
        try:
            url = f"http://{self.esp32_ip}/register-server"
            data = {
                "server_ip": self.my_ip,
                "server_port": self.flask_port,
                "service": "AttendEase"
            }
            
            response = requests.post(url, json=data, timeout=2)
            
            if response.status_code == 200:
                print(f"✓ Successfully announced to ESP32: {self.my_ip}:{self.flask_port}")
                return True
            else:
                print(f"⚠ ESP32 responded with status {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"⚠ Could not reach ESP32 at {self.esp32_ip}: {e}")
            return False
    
    def announce_loop(self):
        """Continuously announce presence every 5 seconds until ESP32 acknowledges"""
        print(f"\n📡 Starting IP announcement to ESP32...")
        
        # Get our IP
        self.my_ip = self.get_my_ip()
        
        if not self.my_ip:
            print("⚠ Could not determine IP address on ESP32 network")
            print("   Make sure you're connected to the ESP32 hotspot!")
            return
        
        print(f"📍 My IP: {self.my_ip}")
        print(f"🎯 Announcing to ESP32 at: {self.esp32_ip}")
        
        # Try to announce immediately
        if self.announce_to_esp32():
            print("✓ ESP32 acknowledged our presence!")
            # Continue announcing every 30 seconds to maintain connection
            while self.running:
                time.sleep(30)
                self.announce_to_esp32()
        else:
            # ESP32 not ready yet, retry every 5 seconds
            print("⏳ ESP32 not responding yet, will retry every 5 seconds...")
            while self.running:
                time.sleep(5)
                if self.announce_to_esp32():
                    print("✓ ESP32 acknowledged our presence!")
                    # Switch to 30 second interval
                    while self.running:
                        time.sleep(30)
                        self.announce_to_esp32()
                    break
    
    def start(self):
        """Start announcing in background thread"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self.announce_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop announcing"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)


# ===== Updated run.py =====
# run.py
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