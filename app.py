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

# TODO: ADD A SIMPLE JSON HERE FOR DEVICE STATE
# TODO: TAKE UPDATE FOR SWITCHES FROM A ROUTE AND UPDATE USING SOCKET.IO FOR DYNAMIC BUTTON CHANGE

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.StreamHandler(sys.stdout),
                        logging.FileHandler('webcam_app.log')
                    ])
#Global Varaibles for States 
is_streaming = False
buffer = 0
is_recording = False
video_writer = None
recording_file_name = None


def generate_frames():
    global is_streaming, buffer, is_recording, video_writer

    camera = cv2.VideoCapture('rtsp://127.0.0.1:8554/stream')
    try:
        while is_streaming:
            success, frame = camera.read()
            if not success:
                time.sleep(0.1)
                continue

            # Encode the frame to JPEG for streaming
            ret, buffer = cv2.imencode('.jpg', frame)

            # If recording, write the frame to the video file
            if is_recording and video_writer is not None:
                video_writer.write(frame)

            # Send the frame to the client
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    except Exception as e:
        logging.error(f"Error in frame generation: {e}")
    finally:
        camera.release()
        is_streaming = False

# Flask App Integration
app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)

# Disable caching for video stream
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Allow RTSP stream URL configuration
# RTSP_STREAM_URL = 'rtsp://127.0.0.1:8554/stream'  # Replace with your RTSP URL if needed
# camera = WebCamera(RTSP_STREAM_URL)

@app.route('update_switch', method= ['POST'])
def update_switch():

    return Response(200)

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
    global buffer
    try:
        if buffer is not None:
            # Decode the encoded buffer back into a raw frame
            frame = cv2.imdecode(np.frombuffer(buffer, np.uint8), cv2.IMREAD_COLOR)
            
            # Ensure the decoded frame is valid
            if frame is None or frame.size == 0:
                raise ValueError("Decoded frame is invalid or empty")

            # Save the raw frame as an image
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            filename = f'snapshot_{timestamp}.jpg'
            cv2.imwrite(filename, frame)
            
            return jsonify({
                'success': True,
                'message': 'Snapshot captured',
                'filename': filename
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No valid frame available for snapshot'
            }), 400
    except Exception as e:
        logging.error(f"Snapshot error: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/camera/start_recording', methods=['POST'])
def start_recording():
    global is_recording, video_writer, recording_file_name

    if is_recording:
        return jsonify({'success': False, 'message': 'Recording is already in progress'}), 400

    try:
        # Generate a unique file name
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        recording_file_name = f'recording_{timestamp}.avi'

        # Define video codec and create VideoWriter object
        fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Change codec as needed (e.g., 'MP4V' for .mp4)
        frame_width = 640
        frame_height = 480
        fps = 30

        video_writer = cv2.VideoWriter(recording_file_name, fourcc, fps, (frame_width, frame_height))
        is_recording = True

        return jsonify({'success': True, 'message': 'Recording started', 'file_name': recording_file_name})
    except Exception as e:
        logging.error(f"Error starting recording: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    
@app.route('/camera/stop_recording', methods=['POST'])
def stop_recording():
    global is_recording, video_writer, recording_file_name

    if not is_recording:
        return jsonify({'success': False, 'message': 'No recording in progress'}), 400

    try:
        # Release the VideoWriter object
        if video_writer is not None:
            video_writer.release()

        is_recording = False
        file_name = recording_file_name
        recording_file_name = None

        return jsonify({'success': True, 'message': 'Recording stopped', 'file_name': file_name})
    except Exception as e:
        logging.error(f"Error stopping recording: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/camera/start_stream', methods=['POST'])
def start_stream():
    global is_streaming
    is_streaming = True
    return jsonify({'success': True, 'message': 'Stream started'})

@app.route('/camera/stop_stream', methods=['POST'])
def stop_stream():
    global is_streaming
    is_streaming = False
    return jsonify({'success': True, 'message': 'Stream stopped'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', threaded=True)