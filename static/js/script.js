// Get DOM elements
const loginPage = document.getElementById('loginPage');
const roomSelectionPage = document.getElementById('roomSelectionPage');
const deviceControlPage = document.getElementById('deviceControlPage');
const currentRoomTitle = document.getElementById('currentRoomTitle');
const usernameInput = document.getElementById('username');
const passwordInput = document.getElementById('password');
const entranceSection = document.getElementById('entranceSection');
const standardRoomSection = document.getElementById('standardRoomSection');
const cameraFeed = document.getElementById('cameraFeed');
const recordingStatusElement = document.getElementById('recordingStatus');

let isRecording = false;
let streamLoadTimeout = null;

// Login function
function login() {
    const username = usernameInput.value;
    const password = passwordInput.value;

    fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loginPage.classList.add('hidden');
            roomSelectionPage.classList.remove('hidden');
        } else {
            alert('Login failed: ' + (data.message || 'Invalid credentials'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Login failed. Please try again.');
    });
}


// Create a new RTCPeerConnection instance
let pc = new RTCPeerConnection();

// Function to send an offer request to the server
async function createOffer() {
    console.log("Sending offer request");

    // Fetch the offer from the server
    const offerResponse = await fetch("/offer", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            sdp: "",
            type: "offer",
        }),
    });

    // Parse the offer response
    const offer = await offerResponse.json();
    console.log("Received offer response:", offer);

    // Set the remote description based on the received offer
    await pc.setRemoteDescription(new RTCSessionDescription(offer));

    // Create an answer and set it as the local description
    const answer = await pc.createAnswer();
    await pc.setLocalDescription(answer);
}

// Trigger the process by creating and sending an offer
createOffer();

// Logout function
function logout() {
    // Stop stream if it's active
    // stopStream();

    fetch('/logout', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Reset pages
            loginPage.classList.remove('hidden');
            roomSelectionPage.classList.add('hidden');
            deviceControlPage.classList.add('hidden');

            // Clear input fields
            usernameInput.value = '';
            passwordInput.value = '';

            // Reset device states
            const deviceButtons = document.querySelectorAll('.device-button');
            deviceButtons.forEach(button => {
                button.classList.remove('on');
                button.classList.add('off');
                button.textContent = button.id.toUpperCase();
            });

            // Reset camera
            isRecording = false;
            recordingStatusElement.textContent = 'Start Recording';
            
            // Reset camera feed to placeholder
            cameraFeed.src = "{{ url_for('static', filename='images/placeholder.jpg') }}";
            
            // Hide stream buttons
            document.getElementById('startStreamBtn').style.display = 'block';
            document.getElementById('stopStreamBtn').style.display = 'none';
        }
    });
}

// Select room function
function selectRoom(room) {
    currentRoomTitle.textContent = room;
    roomSelectionPage.classList.add('hidden');
    deviceControlPage.classList.remove('hidden');

    // Special handling for Entrance
    if (room === 'Entrance') {
        entranceSection.classList.remove('hidden');
        standardRoomSection.classList.add('hidden');
    } else {
        entranceSection.classList.add('hidden');
        standardRoomSection.classList.remove('hidden');
    }
}

// Toggle device function
function toggleDevice(deviceId) {
    const device = document.getElementById(deviceId);
    device.classList.toggle('on');
    device.classList.toggle('off');
    device.textContent = device.classList.contains('on') ? 
        `${deviceId.toUpperCase()} ON` : 
        `${deviceId.toUpperCase()} OFF`;
}

// Toggle camera recording
function toggleCameraRecording() {
    fetch('/camera/toggle_recording', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            isRecording = !isRecording;
            if (isRecording) {
                recordingStatusElement.textContent = 'Stop Recording';
                recordingStatusElement.parentElement.classList.add('on');
            } else {
                recordingStatusElement.textContent = 'Start Recording';
                recordingStatusElement.parentElement.classList.remove('on');
            }
        }
    });
}

// Capture snapshot
function captureSnapshot() {
    fetch('/camera/snapshot', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Snapshot captured and saved!');
        } else {
            alert('Failed to capture snapshot');
        }
    })
    .catch(error => {
        console.error('Snapshot error:', error);
        alert('Error capturing snapshot');
    });
}

// Go back to rooms function
function goBack() {
    // Stop stream if it's active
    // stopStream();
    
    deviceControlPage.classList.add('hidden');
    roomSelectionPage.classList.remove('hidden');
}

// // Start stream function with improved error handling
// function startStream() {
//     fetch('/camera/start_stream', {
//         method: 'POST',
//         timeout: 10000  // 10-second timeout
//     })
//     .then(response => response.json())
//     .then(data => {
//         if (data.success) {
//             const streamUrl = "/video_feed?t=" + new Date().getTime();
            
//             // Create a timeout to handle slow streams
//             streamLoadTimeout = setTimeout(() => {
//                 alert('Stream took too long to load');
//                 stopStream();
//             }, 15000);  // 15-second timeout

//             cameraFeed.onload = function() {
//                 if (streamLoadTimeout) {
//                     clearTimeout(streamLoadTimeout);
//                 }
//             };

//             cameraFeed.onerror = function() {
//                 if (streamLoadTimeout) {
//                     clearTimeout(streamLoadTimeout);
//                 }
//                 alert('Failed to load camera stream');
//                 stopStream();
//             };

//             cameraFeed.src = streamUrl;
            
//             document.getElementById('startStreamBtn').style.display = 'none';
//             document.getElementById('stopStreamBtn').style.display = 'block';
//         } else {
//             alert('Stream start failed: ' + (data.message || 'Unknown error'));
//         }
//     })
//     .catch(error => {
//         console.error('Stream start error:', error);
//         alert('Stream initialization failed');
//     });
// }

// // Stop stream function with improved cleanup
// function stopStream() {
//     // Clear any existing timeout
//     if (streamLoadTimeout) {
//         clearTimeout(streamLoadTimeout);
//         streamLoadTimeout = null;
//     }

//     fetch('/camera/stop_stream', {
//         method: 'POST'
//     })
//     .then(response => response.json())
//     .then(data => {
//         if (data.success) {
//             // Reset camera feed to placeholder
//             cameraFeed.src = "{{ url_for('static', filename='images/placeholder.jpg') }}";
            
//             // Toggle button visibility
//             document.getElementById('startStreamBtn').style.display = 'block';
//             document.getElementById('stopStreamBtn').style.display = 'none';
//         }
//     })
//     .catch(error => {
//         console.error('Error stopping stream:', error);
//         alert('Failed to stop stream');
//     });
// }

// Setup login key press when DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    const loginInputs = [usernameInput, passwordInput];
    
    loginInputs.forEach(input => {
        input.addEventListener('keypress', function(event) {
            if (event.key === 'Enter') {
                event.preventDefault();
                login();
            }
        });
    });
});