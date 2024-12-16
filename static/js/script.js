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

// Initialize room device states
const roomDeviceStates = {
    'Livingroom': {
        'light': false,
        'fan': false,
        'ac': false,
        'tv': false
    },
    'Bedroom': {
        'light': false,
        'fan': false,
        'ac': false,
        'tv': false
    },
    'Kitchen': {
        'light': false,
        'fan': false,
        'ac': false,
        'tv': false
    },
    'Bathroom': {
        'light': false,
        'fan': false,
        'ac': false,
        'tv': false
    },
    'Entrance': {
        'light': false,
        'fan': false,
        'ac': false,
        'tv': false
    }
};

let isRecording = false;
let streamLoadTimeout = null;
let currentRoom = null;
let socket = io();
socket.on('device_update', function(data) {
    // Convert room from server format to UI format
    const uiRoomName = data.room.charAt(0).toUpperCase() + data.room.slice(1);
    console.log(uiRoomName);

    // Check if the update is for any room
    if (roomDeviceStates[uiRoomName]) {
        // Update device state in roomDeviceStates
        roomDeviceStates[uiRoomName][data.device] = data.state;

        // If the update is for the current room, update UI
        if (currentRoom === uiRoomName) {
            const deviceElement = document.getElementById(data.device);

            if (deviceElement) {
                if (data.state) {
                    deviceElement.classList.remove('off');
                    deviceElement.classList.add('on');
                    deviceElement.textContent = `${data.device.toUpperCase()} ON`;
                } else {
                    deviceElement.classList.remove('on');
                    deviceElement.classList.add('off');
                    deviceElement.textContent = `${data.device.toUpperCase()} OFF`;
                }
            }
        }
    }
});
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

function logout() {
    fetch('/logout', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Reset visibility of all pages
            loginPage.classList.remove('hidden');
            roomSelectionPage.classList.add('hidden');
            deviceControlPage.classList.add('hidden');
            entranceSection.classList.add('hidden');
            standardRoomSection.classList.add('hidden');

            // Clear input fields
            usernameInput.value = '';
            passwordInput.value = '';

            // Reset device states
            Object.keys(roomDeviceStates).forEach(room => {
                Object.keys(roomDeviceStates[room]).forEach(device => {
                    roomDeviceStates[room][device] = false;
                });
            });

            // Reset camera state
            isRecording = false;
            recordingStatusElement.textContent = 'Start Recording';
            recordingStatusElement.parentElement.classList.remove('on');

            // Reset current room
            currentRoom = null;

            // Reset camera feed to placeholder
            cameraFeed.src = '';

            // Hide stream buttons
            document.getElementById('startStreamBtn').style.display = 'block';
            document.getElementById('stopStreamBtn').style.display = 'none';
        } else {
            alert('Logout failed. Please try again.');
        }
    })
    .catch(error => {
        console.error('Error during logout:', error);
        alert('An error occurred while logging out.');
    });
}


// Modify the selectRoom function to handle navigation correctly
// Modify selectRoom function to restore room-specific device states
// Select Room function
function selectRoom(room) {
    currentRoom = room;
    currentRoomTitle.textContent = room;
    roomSelectionPage.classList.add('hidden');
    deviceControlPage.classList.remove('hidden');

    // Restore device states for the current room
    const deviceButtons = document.querySelectorAll('.device-button');
    deviceButtons.forEach(button => {
        const deviceId = button.id;
        const deviceState = roomDeviceStates[room][deviceId];

        button.classList.remove('on', 'off');
        if (deviceState) {
            button.classList.add('on');
            button.textContent = `${deviceId.toUpperCase()} ON`;
        } else {
            button.classList.add('off');
            button.textContent = `${deviceId.toUpperCase()} OFF`;
        }
    });

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
    const newState = !device.classList.contains('on');

    // Send request to server with room information
    fetch(`/${currentRoom.toLowerCase().replace(' ', '')}/${deviceId}/${newState ? 'on' : 'off'}`, {
        method: 'GET'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Optimistically update the UI
            if (newState) {
                device.classList.remove('off');
                device.classList.add('on');
                device.textContent = `${deviceId.toUpperCase()} ON`;
            } else {
                device.classList.remove('on');
                device.classList.add('off');
                device.textContent = `${deviceId.toUpperCase()} OFF`;
            }

            // Update local state
            roomDeviceStates[currentRoom][deviceId] = newState;
        }
    })
    .catch(error => {
        console.error('Error toggling device:', error);
    });
}
// Toggle camera recording
function toggleCameraRecording() {
    if(!isRecording){
    fetch('/camera/start_recording', {
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
else if (isRecording){
    fetch('/camera/stop_recording', {
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

// Modify the goBack function to handle stream and navigation
function goBack() {
    // Stop camera stream if on Entrance page
    if (currentRoom === 'Entrance') {
        // Reset camera feed
        // cameraFeed.src = "{{ url_for('static', filename='images/placeholder.jpg') }}";

        // Reset recording status
        isRecording = false;
        recordingStatusElement.textContent = 'Start Recording';
        recordingStatusElement.parentElement.classList.remove('on');
    }

    // Reset room-specific states
    const deviceButtons = document.querySelectorAll('.device-button');
    deviceButtons.forEach(button => {
        button.classList.remove('on');
        button.classList.add('off');
        button.textContent = button.id.toUpperCase();
    });
       // Hide current pages
       deviceControlPage.classList.add('hidden');
       entranceSection.classList.add('hidden');
       standardRoomSection.classList.add('hidden');

       // Show room selection page
       roomSelectionPage.classList.remove('hidden');

       // Reset current room
       currentRoom = null;
   }


function stopStream() {
    // Clear any existing timeout
    if (streamLoadTimeout) {
        clearTimeout(streamLoadTimeout);
        streamLoadTimeout = null;
    }

    fetch('/camera/stop_stream', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Reset camera feed
            cameraFeed.src = ''; // Clear the source

            // Remove any error event listener to prevent repeated error messages
            cameraFeed.onerror = null;

            // Toggle button visibility
            document.getElementById('startStreamBtn').style.display = 'block';
            document.getElementById('stopStreamBtn').style.display = 'none';
        }
    })
    .catch(error => {
        console.error('Error stopping stream:', error);
    });
}

// Modify the startStream function to handle potential errors
function startStream() {
    fetch('/camera/start_stream', {
        method: 'POST',
        timeout: 10000  // 10-second timeout
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const streamUrl = "/video_feed?t=" + new Date().getTime();

            // Reset any previous error handlers
            cameraFeed.onerror = null;

            // Create a timeout to handle slow streams
            streamLoadTimeout = setTimeout(() => {
                alert('Stream took too long to load');
                stopStream();
            }, 15000);  // 15-second timeout

            cameraFeed.onload = function() {
                if (streamLoadTimeout) {
                    clearTimeout(streamLoadTimeout);
                }
            };

            cameraFeed.onerror = function(e) {
                if (streamLoadTimeout) {
                    clearTimeout(streamLoadTimeout);
                }
                // Only show error if streaming was intended to be active
                if (document.getElementById('stopStreamBtn').style.display === 'block') {
                    console.error('Stream loading error:', e);
                    stopStream();
                }
            };

            cameraFeed.src = streamUrl;

            document.getElementById('startStreamBtn').style.display = 'none';
            document.getElementById('stopStreamBtn').style.display = 'block';
        } else {
            alert('Stream start failed: ' + (data.message || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Stream start error:', error);
        alert('Stream initialization failed');
    });
}
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

// Additional safety measure for navigation
window.addEventListener('popstate', function() {
    // If somehow stuck on a page, return to room selection
    if (!roomSelectionPage.classList.contains('hidden')) return;

    goBack();
});