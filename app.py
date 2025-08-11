# app.py
from flask import Flask, request, render_template, jsonify
import logging

app = Flask(__name__)
current_zone = 0

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app.route('/command', methods=['POST'])
def handle_command():
    global current_zone
    data = request.json
    zone = data.get('zone')
    
    if zone is not None:
        current_zone = zone

    if zone == 1:
        print("Zone 1 is detected. It would send 'MOTOR_ON' command to Arduino.")
    elif zone == 2:
        print("Zone 2 is detected. It would send 'LED_ON' command to Arduino.")
    elif zone == 3:
        print("Zone 3 is detected. It would send 'SERVO_MOVE' command to Arduino.")
    else:
        print("No zone detected.")
    
    return "OK"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_zone', methods=['GET'])
def get_zone():
    global current_zone
    return jsonify({'zone': current_zone})

if __name__ == '__main__':
    # Flask 서버 주소를 명시적으로 출력
    print("* Serving Flask app 'app'")
    print("* Debug mode: off")
    print("* Running on http://127.0.0.1:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)