import cv2
import numpy as np
from flask import Flask, render_template, request, jsonify, session,Response
import secrets


# from flask import Flask, render_template, Response
import threading
import base64

class RTSPCamera:
    def __init__(self, rtsp_url):
        self.rtsp_url = rtsp_url
        self.capture = None
        self.thread = None
        self.frame = None
        self.is_running = False

    def start(self):
        self.is_running = True
        self.thread = threading.Thread(target=self._stream_thread)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join()
        if self.capture:
            self.capture.release()

    def _stream_thread(self):
        self.capture = cv2.VideoCapture(self.rtsp_url)
        while self.is_running:
            ret, frame = self.capture.read()
            if ret:
                # Resize frame if needed
                frame = cv2.resize(frame, (640, 480))
                self.frame = frame
            else:
                print("Failed to grab frame")
                break

    def get_frame(self):
        if self.frame is not None:
            # Encode frame to JPEG
            ret, jpeg = cv2.imencode('.jpg', self.frame)
            return jpeg.tobytes()
        return None

# Flask App Integration
app = Flask(__name__)

# Replace with your actual RTSP URL
RTSP_URL = 'rtsp://username:password@ip_address:port/stream'
camera = RTSPCamera(RTSP_URL)

@app.route('/video_feed')
def video_feed():
    def generate_frames():
        camera.start()
        try:
            while True:
                frame = camera.get_frame()
                if frame is not None:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        finally:
            camera.stop()

    return Response(generate_frames(), 
                    mimetype='multipart/x-mixed-replace; boundary=frame')
app.secret_key = secrets.token_hex(16)  # Secure secret key

# Simulated user database
USERS = {
    'admin': 'password123'
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    
    if username in USERS and USERS[username] == password:
        session['logged_in'] = True
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/camera/snapshot', methods=['POST'])
def capture_snapshot():
    # In a real app, this would interact with a camera
    return jsonify({
        'success': True, 
        'message': 'Snapshot captured',
        'timestamp': 'Current timestamp'
    })

@app.route('/camera/toggle_recording', methods=['POST'])
def toggle_recording():
    # Simulated recording toggle
    return jsonify({
        'success': True, 
        'recording': True
    })

if __name__ == '__main__':
    app.run(debug=True)