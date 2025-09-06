import cv2
import mediapipe as mp
import requests
import time
import threading
from flask import Flask, render_template, jsonify, request
import multiprocessing
import sys

# Flask 서버 설정
app = Flask(__name__)

# 현재 손가락 좌표를 저장할 전역 변수 (스레드 간 동기화 필요)
finger_pos = {
    "x": None,
    "y": None,
    "isPinch": False
}

# ----------------------------------------------------
# *** Flask 웹 서버 함수 ***
# ----------------------------------------------------
def run_flask_server():
    """웹 서버를 실행하는 함수"""
    
    # 두 개의 엔드포인트 정의
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/update_finger_pos', methods=['POST'])
    def update_finger_pos():
        global finger_pos
        if request.is_json:
            data = request.get_json()
            if 'x' in data and 'y' in data and 'isPinch' in data:
                finger_pos['x'] = data['x']
                finger_pos['y'] = data['y']
                finger_pos['isPinch'] = data['isPinch']
                return jsonify({"status": "success"}), 200
        return jsonify({"status": "error", "message": "Invalid data format"}), 400

    @app.route('/get_finger_pos')
    def get_finger_pos():
        return jsonify(finger_pos)

    print("Flask 서버를 시작합니다.")
    app.run(host='127.0.0.1', port=5000)

# ----------------------------------------------------
# *** 손 인식 및 데이터 전송 함수 ***
# ----------------------------------------------------
def run_hand_tracking():
    """손 인식을 수행하고 서버로 데이터를 전송하는 함수"""
    
    # 서버 URL과 동일한지 확인
    SERVER_URL = "http://127.0.0.1:5000/update_finger_pos"

    # MediaPipe Hands 초기화
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )
    mp_drawing = mp.solutions.drawing_utils

    # 웹캠 설정
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("웹캠을 열 수 없습니다. 프로그램을 종료합니다.", file=sys.stderr)
        return

    # 핀치 제스처 감지 함수
    def is_pinch(landmarks):
        thumb_tip = landmarks[mp_hands.HandLandmark.THUMB_TIP]
        index_tip = landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP]
        distance = ((thumb_tip.x - index_tip.x)**2 + (thumb_tip.y - index_tip.y)**2)**0.5
        return distance < 0.05 # 임계값

    print("손 인식 프로그램을 시작합니다. 'q'키를 눌러 종료하세요.")
    try:
        while True:
            success, image = cap.read()
            if not success:
                print("웹캠 프레임을 가져오는 데 실패했습니다.")
                time.sleep(1)
                continue

            image = cv2.flip(image, 1)
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            results = hands.process(image_rgb)
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    thumb_tip_landmark = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
                    pinch_status = is_pinch(hand_landmarks.landmark)
                    
                    data = {
                        "x": thumb_tip_landmark.x,
                        "y": thumb_tip_landmark.y,
                        "isPinch": pinch_status
                    }
                    
                    try:
                        requests.post(SERVER_URL, json=data)
                        print(f"좌표 전송: x={data['x']:.2f}, y={data['y']:.2f}, Pinch={data['isPinch']}")
                    except requests.exceptions.ConnectionError:
                        print("서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
                    
                    mp_drawing.draw_landmarks(
                        image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            cv2.imshow('Hand Gesture Control', image)
            
            if cv2.waitKey(5) & 0xFF == ord('q'):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("손 인식 프로그램을 종료합니다.")

# ----------------------------------------------------
# *** 메인 실행부 ***
# ----------------------------------------------------
if __name__ == '__main__':
    # 두 함수를 각각의 프로세스로 실행
    p1 = multiprocessing.Process(target=run_flask_server)
    p2 = multiprocessing.Process(target=run_hand_tracking)
    
    p1.start()
    p2.start()

    # 두 프로세스가 종료될 때까지 대기
    p1.join()
    p2.join()
    
    print("모든 프로그램이 종료되었습니다.")