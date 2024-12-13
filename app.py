import cv2
import numpy as np
from flask import Flask, render_template, request, jsonify, session, Response
import secrets
import threading
import time
import logging
import sys
from flask import send_from_directory

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.StreamHandler(sys.stdout),
                        logging.FileHandler('webcam_app.log')
                    ])

class WebCamera:
    def __init__(self):
        self.capture = None
        self.thread = None
        self.frame = None
        self.is_running = False
        self.lock = threading.Lock()

    def start(self):
        try:
            # Check if a webcam is available
            test_capture = cv2.VideoCapture(0)
            if not test_capture.isOpened():
                logging.error("No webcam found or unable to access webcam")
                test_capture.release()
                return False

            test_capture.release()

            if not self.is_running:
                self.is_running = True
                self.capture = cv2.VideoCapture(0)  
                
                # Verify capture is opened
                if not self.capture.isOpened():
                    logging.error("Failed to open webcam")
                    return False

                # Set camera properties 
                self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                
                self.thread = threading.Thread(target=self._stream_thread)
                self.thread.daemon = True
                self.thread.start()
                return True
            
            return False
        except Exception as e:
            logging.error(f"Error starting webcam: {e}")
            return False

    def stop(self):
        try:
            self.is_running = False
            if self.thread:
                self.thread.join(timeout=2)
            if self.capture:
                self.capture.release()
                self.capture = None
            logging.info("Webcam stream stopped")
        except Exception as e:
            logging.error(f"Error stopping webcam: {e}")

    def _stream_thread(self):
        logging.info("Webcam stream thread started")
        while self.is_running:
            try:
                if not self.capture or not self.capture.isOpened():
                    logging.error("Capture device not available")
                    break

                ret, frame = self.capture.read()
                if not ret:
                    logging.warning("Failed to read frame from webcam")
                    time.sleep(0.5)
                    continue

                # Flip frame horizontally 
                frame = cv2.flip(frame, 1)

                # Resize frame
                frame = cv2.resize(frame, (640, 480))
                
                with self.lock:
                    self.frame = frame

                # Small sleep to prevent high CPU usage
                time.sleep(0.01)

            except Exception as e:
                logging.error(f"Error in webcam stream thread: {e}")
                break

        logging.info("Webcam stream thread ended")
        self.is_running = False

    def get_frame(self):
        try:
            with self.lock:
                if self.frame is not None:
                    # Encode frame to JPEG
                    ret, jpeg = cv2.imencode('.jpg', self.frame)
                    if ret:
                        return jpeg.tobytes()
            return None
        except Exception as e:
            logging.error(f"Error getting frame: {e}")
            return None

# Flask App Integration
app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)

# Disable caching for video stream
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

camera = WebCamera()

@app.route('/video_feed')
def video_feed():
    def generate_frames():
        logging.info("Starting video feed generation")
        while True:
            try:
                frame = camera.get_frame()
                if frame is not None:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                else:
                    logging.warning("No frame available")
                    time.sleep(0.1)
            except Exception as e:
                logging.error(f"Error in frame generation: {e}")
                break
    
    return Response(generate_frames(), 
                    mimetype='multipart/x-mixed-replace; boundary=frame')

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
    try:
        current_frame = camera.get_frame()
        if current_frame:
            return jsonify({
                'success': True, 
                'message': 'Snapshot captured',
                'timestamp': time.strftime("%Y%m%d-%H%M%S")
            })
        else:
            return jsonify({
                'success': False, 
                'message': 'Failed to capture snapshot'
            }), 400
    except Exception as e:
        logging.error(f"Snapshot error: {e}")
        return jsonify({
            'success': False, 
            'message': str(e)
        }), 500

@app.route('/camera/toggle_recording', methods=['POST'])
def toggle_recording():
    return jsonify({
        'success': True, 
        'recording': True
    })

@app.route('/camera/start_stream', methods=['POST'])
def start_stream():
    success = camera.start()
    if success:
        return jsonify({'success': True, 'message': 'Stream started'})
    else:
        return jsonify({'success': False, 'message': 'Failed to start stream'}), 500

@app.route('/camera/stop_stream', methods=['POST'])
def stop_stream():
    camera.stop()
    return jsonify({'success': True, 'message': 'Stream stopped'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', threaded=True)