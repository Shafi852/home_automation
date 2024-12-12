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

// Login function
function login() {
    const username = usernameInput.value;
    const password = passwordInput.value;

    // Simple login validation (replace with real authentication)
    if (username && password) {
        loginPage.classList.add('hidden');
        roomSelectionPage.classList.remove('hidden');
    } else {
        alert('Please enter username and password');
    }
}

// Add event listener for Enter key on login page
function setupLoginKeyPress() {
    const loginInputs = [usernameInput, passwordInput];
    
    loginInputs.forEach(input => {
        input.addEventListener('keypress', function(event) {
            if (event.key === 'Enter') {
                event.preventDefault();
                login();
            }
        });
    });
}

// Logout function
function logout() {
    // Reset all pages
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
    isRecording = !isRecording;
    if (isRecording) {
        recordingStatusElement.textContent = 'Stop Recording';
        recordingStatusElement.parentElement.classList.add('on');
    } else {
        recordingStatusElement.textContent = 'Start Recording';
        recordingStatusElement.parentElement.classList.remove('on');
    }
}

// Capture snapshot
function captureSnapshot() {
    alert('Snapshot captured and saved!');
    // In a real implementation, this would send the current camera feed to storage
}

// Go back to rooms function
function goBack() {
    deviceControlPage.classList.add('hidden');
    roomSelectionPage.classList.remove('hidden');
}

// Setup login key press when DOM is fully loaded
document.addEventListener('DOMContentLoaded', setupLoginKeyPress);