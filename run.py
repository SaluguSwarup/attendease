# run.py
from app import create_app

app = create_app()

if __name__ == '__main__':
    # debug=True allows the server to auto-reload when you save changes
    app.run(host='0.0.0.0', port=5000, debug=True)
