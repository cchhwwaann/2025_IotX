# app.py
from flask import Flask, request, render_template, jsonify
import logging

app = Flask(__name__)
current_zone = 1
last_clicked_zone = 0

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app.route('/zone', methods=['POST'])
def handle_zone():
    global current_zone
    data = request.json
    zone = data.get('zone')
    
    if zone is not None:
        current_zone = zone
    
    return "OK"

@app.route('/click', methods=['POST'])
def handle_click():
    global last_clicked_zone
    data = request.json
    zone = data.get('zone')
    last_clicked_zone = zone
    
    return "OK"

@app.route('/control', methods=['POST'])
def handle_control():
    data = request.json
    room_id = data.get('room_id')
    control_id = data.get('control_id')
    action = data.get('action')
    
    if control_id and action and room_id:
        print(f"Control command received: ID={control_id}, Action={action}")
    
    return "OK"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_zone', methods=['GET'])
def get_zone():
    global current_zone
    return jsonify({'zone': current_zone})

@app.route('/get_click', methods=['GET'])
def get_click():
    global last_clicked_zone
    clicked_zone = last_clicked_zone
    last_clicked_zone = 0
    return jsonify({'zone': clicked_zone})

if __name__ == '__main__':
    print("* Serving Flask app 'app'")
    print("* Debug mode: off")
    print("* Running on http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)