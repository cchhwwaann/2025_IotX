# app.py
from flask import Flask, request, render_template, jsonify
import logging

app = Flask(__name__)
current_zone = 0
last_clicked_zone = 0 # 마지막으로 클릭된 zone을 저장하는 변수

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app.route('/zone', methods=['POST'])
def handle_zone():
    global current_zone
    data = request.json
    zone = data.get('zone')
    
    if zone is not None:
        current_zone = zone
    
    if zone == 0:
        print("No zone detected.")
    else:
        print(f"Zone {zone} is active.")
    
    return "OK"

@app.route('/click', methods=['POST'])
def handle_click():
    global last_clicked_zone
    data = request.json
    zone = data.get('zone')
    last_clicked_zone = zone # 클릭된 zone 저장
    print(f"Zone {zone} is clicked.")
    
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
    last_clicked_zone = 0 # 신호를 한 번 보낸 후 초기화
    return jsonify({'zone': clicked_zone})

if __name__ == '__main__':
    # 서버 시작 메시지를 명시적으로 출력
    print("* Serving Flask app 'app'")
    print("* Debug mode: off")
    print("* Running on http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)