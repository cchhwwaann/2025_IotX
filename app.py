# app.py

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import threading
import json
import math
import time
from hand_recognition_with_pinch import start_hand_recognition

app = Flask(__name__)
socketio = SocketIO(app)

BUTTON_AREAS = {}
current_highlight = None

# 타이머 관련 전역 변수
timer_running = False
timer_thread = None
current_duration = 0
stopwatch_start_time = 0
timer_mode = None

# 손 인식 스레드 관리 변수
hand_recognition_thread = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/timer')
def timer_page():
    global current_duration, timer_running
    current_duration = 0
    timer_running = False
    return render_template('timer.html')

@app.route('/recipebook')
def recipebook_page():
    return render_template('recipebook.html')

@socketio.on('connect')
def handle_connect():
    print("Client connected.")

@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected. Hand recognition thread continues running.")

@socketio.on('button_info')
def handle_button_info(data):
    global BUTTON_AREAS
    BUTTON_AREAS = {btn['id']: btn for btn in data}
    print("Received button information from client:", BUTTON_AREAS)

@app.route('/hand_position', methods=['POST'])
def handle_hand_position_post():
    global BUTTON_AREAS, current_highlight
    data = request.json
    x = data['x']
    y = data['y']
    new_highlight = None
    min_distance = float('inf')
    
    if BUTTON_AREAS: # <-- 이 조건문이 핵심입니다. BUTTON_AREAS가 비어있지 않을 때만 로직을 실행
        for btn_id, coords in BUTTON_AREAS.items():
            center_x = (coords['x_min'] + coords['x_max']) / 2
            center_y = (coords['y_min'] + coords['y_max']) / 2
            distance = math.sqrt((x - center_x)**2 + (y - center_y)**2)
            if distance < min_distance:
                min_distance = distance
                new_highlight = btn_id
                
    if new_highlight != current_highlight:
        current_highlight = new_highlight
        socketio.emit('highlight_button', {'button_name': current_highlight})
    return "OK"

@app.route('/click_event', methods=['POST'])
def handle_click_event():
    global current_highlight
    if current_highlight:
        print(f"Clicked on {current_highlight}")
        socketio.emit('click_button', {'button_name': current_highlight})
    return "OK"

# 타이머 스레드 함수
def start_stopwatch_thread():
    global timer_running, stopwatch_start_time
    timer_running = True
    stopwatch_start_time = time.time()
    while timer_running:
        elapsed_time = int(time.time() - stopwatch_start_time)
        socketio.emit('timer_update', {'time_left': elapsed_time})
        socketio.sleep(1)

def start_countdown_thread():
    global timer_running, timer_end_time
    timer_running = True
    timer_end_time = time.time() + current_duration
    while timer_running and time.time() < timer_end_time:
        remaining_time = max(0, int(timer_end_time - time.time()))
        socketio.emit('timer_update', {'time_left': remaining_time})
        socketio.sleep(1)
    if timer_running:
        socketio.emit('timer_end', {'message': '타이머 종료!'})
        timer_running = False

# 타이머 제어 이벤트 핸들러
@socketio.on('timer_action')
def handle_timer_action(data):
    global timer_running, timer_thread, current_duration, timer_mode
    action = data.get('action')
    if action == 'set_30s':
        current_duration += 30
        socketio.emit('timer_update', {'time_left': current_duration})
    elif action == 'set_1m':
        current_duration += 60
        socketio.emit('timer_update', {'time_left': current_duration})
    elif action == 'set_5m':
        current_duration += 300
        socketio.emit('timer_update', {'time_left': current_duration})
    elif action == 'set_10m':
        current_duration += 600
        socketio.emit('timer_update', {'time_left': current_duration})
    elif action == 'start':
        if not timer_running:
            if current_duration > 0:
                print(f"카운트다운 시작: {current_duration}초")
                timer_mode = 'countdown'
                timer_thread = threading.Thread(target=start_countdown_thread)
                timer_thread.daemon = True
                timer_thread.start()
            else:
                print("스톱워치 시작")
                timer_mode = 'stopwatch'
                timer_thread = threading.Thread(target=start_stopwatch_thread)
                timer_thread.daemon = True
                timer_thread.start()
    elif action == 'stop':
        print("타이머 정지")
        timer_running = False
        if timer_thread and timer_thread.is_alive():
            timer_thread.join()
    elif action == 'reset':
        print("타이머 리셋")
        timer_running = False
        current_duration = 0
        if timer_thread and timer_thread.is_alive():
            timer_thread.join()
        socketio.emit('timer_update', {'time_left': 0})

def run_app():
    global hand_recognition_thread
    hand_recognition_thread = threading.Thread(target=start_hand_recognition)
    hand_recognition_thread.daemon = True
    hand_recognition_thread.start()
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)

if __name__ == '__main__':
    run_app()