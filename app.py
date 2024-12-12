from flask import Flask, render_template, request, jsonify, session
import secrets

app = Flask(__name__)
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