import cv2
import numpy as np
from aiortc import RTCPeerConnection, RTCSessionDescription
from flask import Flask, render_template, request, jsonify, session, Response
import secrets
import threading
import time
import logging
import sys
from flask import send_from_directory
import uuid
import asyncio


# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.StreamHandler(sys.stdout),
                        logging.FileHandler('webcam_app.log')
                    ])

# class WebCamera:
#     def __init__(self, stream_url=None):
#         self.stream_url = stream_url or 0
#         self.capture = None
#         self.thread = None
#         self.frame = None
#         self.is_running = False
#         self.lock = threading.Lock()
#         self.reconnect_interval = 5  # Seconds between reconnection attempts

#     def start(self):
#         try:
#             # Use different capture backends for more robust streaming
#             capture_backends = [
#                 cv2.CAP_FFMPEG,   # Recommended for network streams
#                 cv2.CAP_GSTREAMER,
#                 cv2.CAP_V4L2,     # Linux video capture
#                 cv2.CAP_DSHOW     # Windows DirectShow
#             ]

#             for backend in capture_backends:
#                 try:
#                     self.capture = cv2.VideoCapture(self.stream_url, backend)
                    
#                     # Additional timeout and parameter settings
#                     self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 3)
                    
#                     # Use read with timeout for verification
#                     ret, _ = self.capture.read()
#                     if ret:
#                         break
#                 except Exception as backend_err:
#                     logging.warning(f"Backend {backend} failed: {backend_err}")

#             if not self.capture or not self.capture.isOpened():
#                 logging.error(f"Failed to open stream with any backend: {self.stream_url}")
#                 return False

#             # Configure capture properties
#             self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
#             self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

#             self.is_running = True
#             self.thread = threading.Thread(target=self._stream_thread, daemon=True)
#             self.thread.start()
#             return True

#         except Exception as e:
#             logging.error(f"Stream initialization error: {e}")
#             return False

#     def _stream_thread(self):
#         consecutive_errors = 0
#         max_consecutive_errors = 5

#         while self.is_running:
#             try:
#                 if not self.capture or not self.capture.isOpened():
#                     logging.warning("Attempting to reconnect to stream...")
#                     self.capture = cv2.VideoCapture(self.stream_url)
#                     if not self.capture.isOpened():
#                         consecutive_errors += 1
#                         time.sleep(self.reconnect_interval)
#                         continue

#                 ret, frame = self.capture.read()
#                 if not ret:
#                     consecutive_errors += 1
#                     logging.warning(f"Frame read failed (attempts: {consecutive_errors})")
                    
#                     if consecutive_errors >= max_consecutive_errors:
#                         logging.critical("Maximum reconnection attempts exceeded")
#                         break
                    
#                     time.sleep(1)
#                     continue

#                 consecutive_errors = 0

#                 # Process frame
#                 frame = cv2.flip(frame, 1)
#                 frame = cv2.resize(frame, (640, 480))
                
#                 with self.lock:
#                     self.frame = frame

#                 time.sleep(0.01)

#             except Exception as e:
#                 logging.error(f"Stream thread error: {e}")
#                 break

#         self.is_running = False
#         logging.info("Camera stream thread ended")

#     def get_frame(self):
#         try:
#             with self.lock:
#                 if self.frame is not None:
#                     # Encode frame to JPEG
#                     ret, jpeg = cv2.imencode('.jpg', self.frame)
#                     if ret:
#                         return jpeg.tobytes()
#             return None
#         except Exception as e:
#             logging.error(f"Error getting frame: {e}")
#             return None


def generate_frames():
    camera = cv2.VideoCapture('rtsp://127.0.0.1:8554/stream')
    while True:
        start_time = time.time()
        success, frame = camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            # Concatenate frame and yield for streaming
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n') 
            elapsed_time = time.time() - start_time
            logging.debug(f"Frame generation time: {elapsed_time} seconds")

# Flask App Integration
app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)

# Disable caching for video stream
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Allow RTSP stream URL configuration
# RTSP_STREAM_URL = 'rtsp://127.0.0.1:8554/stream'  # Replace with your RTSP URL if needed
# camera = WebCamera(RTSP_STREAM_URL)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Simulated user database
USERS = {
    'admin': 'password123'
}

@app.route('/')
def index():
    return render_template('index.html')


# Asynchronous function to handle offer exchange
async def offer_async():
    params = await request.json
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    # Create an RTCPeerConnection instance
    pc = RTCPeerConnection()

    # Generate a unique ID for the RTCPeerConnection
    pc_id = "PeerConnection(%s)" % uuid.uuid4()
    pc_id = pc_id[:8]

    # Create a data channel named "chat"
    # pc.createDataChannel("chat")

    # Create and set the local description
    await pc.createOffer(offer)
    await pc.setLocalDescription(offer)

    # Prepare the response data with local SDP and type
    response_data = {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}

    return jsonify(response_data)

# Wrapper function for running the asynchronous offer function
def offer():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    future = asyncio.run_coroutine_threadsafe(offer_async(), loop)
    return future.result()

# Route to handle the offer request
@app.route('/offer', methods=['POST'])
def offer_route():
    return offer()


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