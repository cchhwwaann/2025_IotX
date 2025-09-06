import cv2
import mediapipe as mp
import requests
import time
import serial
import sys
import threading
from flask import Flask, render_template, jsonify, request
import numpy as np

# Flask 서버 설정
app = Flask(__name__)

# 현재 손가락 좌표를 저장할 전역 변수
finger_pos = {
    "x": None,
    "y": None,
    "isPinch": False
}

# Flask 서버 엔드포인트 정의
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
            
            # 문자열을 bool 타입으로 변환
            if isinstance(data['isPinch'], str):
                finger_pos['isPinch'] = data['isPinch'].lower() == 'true'
            else:
                finger_pos['isPinch'] = data['isPinch']

            return jsonify({"status": "success"}), 200
    return jsonify({"status": "error", "message": "Invalid data format"}), 400

@app.route('/get_finger_pos')
def get_finger_pos():
    return jsonify(finger_pos)


# ----------------------------------------------------
## 단일 프로세스: 웹 서버 및 손/얼굴 인식 & 제어---
def run_combined_tracking_and_control():
    """하나의 프로세스에서 모든 트래킹 및 제어 기능을 실행하는 함수"""

    # 아두이노 시리얼 통신 설정 (포트 번호는 환경에 맞게 수정)
    try:
        arduino = serial.Serial('COM9', 9600, timeout=1)
        time.sleep(2)
        print("아두이노 연결 성공.")
    except serial.SerialException as e:
        print(f"아두이노 포트를 열 수 없습니다: {e}", file=sys.stderr)
        arduino = None

    # MediaPipe 솔루션 로드
    mp_hands = mp.solutions.hands
    mp_face = mp.solutions.face_detection
    mp_drawing = mp.solutions.drawing_utils

    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )
    face_detection = mp_face.FaceDetection(min_detection_confidence=0.5)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("웹캠을 열 수 없습니다. 프로그램을 종료합니다.", file=sys.stderr)
        return

    # 얼굴 중심 x 좌표를 서보 모터 각도로 매핑
    def calculate_servo_angle(face_center_x):
        angle = int((1 - face_center_x) * 180)
        if angle < 0: angle = 0
        elif angle > 180: angle = 180
        return angle

    # 손가락 핀치 제스처 감지
    def is_pinch(landmarks):
        thumb_tip = landmarks[mp_hands.HandLandmark.THUMB_TIP]
        index_tip = landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP]
        distance = np.sqrt((thumb_tip.x - index_tip.x)**2 + (thumb_tip.y - index_tip.y)**2)
        return distance < 0.05
    
    # 데이터 전송 주기를 위한 변수
    last_sent_time = time.time()
    send_interval = 0.1 # 0.1초 (100ms) 간격으로 데이터 전송

    print("통합 트래킹 및 제어 프로그램을 시작합니다. 'q'키를 눌러 종료하세요.")
    try:
        while True:
            success, image = cap.read()
            if not success:
                time.sleep(1)
                continue
            
            # 좌우 반전
            image = cv2.flip(image, 1)
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            h, w, c = image.shape
            
            # 얼굴 인식 (서보 모터 제어)
            face_results = face_detection.process(image_rgb)
            if face_results.detections:
                for detection in face_results.detections:
                    bboxC = detection.location_data.relative_bounding_box
                    face_center_x = bboxC.xmin + bboxC.width / 2
                    
                    if arduino:
                        target_angle = calculate_servo_angle(face_center_x)
                        arduino.write(f"{target_angle}\n".encode())
                        print(f"아두이노 제어: 서보 각도 = {target_angle}")
                        
                    center_point_x = int(face_center_x * w)
                    cv2.circle(image, (center_point_x, int(bboxC.ymin * h + bboxC.height * h / 2)), 10, (255, 0, 0), -1)
            
            # 손 인식 (웹 서버 제어)
            hand_results = hands.process(image_rgb)
            if hand_results.multi_hand_landmarks:
                for hand_landmarks in hand_results.multi_hand_landmarks:
                    thumb_tip_landmark = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
                    pinch_status = is_pinch(hand_landmarks.landmark)
                    
                    # 딜레이를 적용하여 데이터 전송
                    current_time = time.time()
                    if current_time - last_sent_time >= send_interval:
                        # 수정된 코드 (pinch_status를 문자열로 변환)
                        data = {
                            "x": thumb_tip_landmark.x,
                            "y": thumb_tip_landmark.y,
                            "isPinch": str(pinch_status) # True/False를 'True'/'False' 문자열로 변환
                        }
                        
                        try:
                            requests.post("http://127.0.0.1:5000/update_finger_pos", json=data)
                            print("웹 서버로 손 인식 데이터 전송 성공!")
                        except Exception as e:
                            print(f"웹 서버 통신 중 오류 발생: {e}")
                        
                        last_sent_time = current_time

                    thumb_x = int(thumb_tip_landmark.x * w)
                    thumb_y = int(thumb_tip_landmark.y * h)
                    cv2.circle(image, (thumb_x, thumb_y), 10, (0, 255, 0), -1)
                    mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            cv2.imshow('Integrated Tracking Control', image)
            
            if cv2.waitKey(5) & 0xFF == ord('q'):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
        if arduino:
            arduino.close()
        print("통합 프로그램을 종료합니다.")
        sys.exit(0)

# ----------------------------------------------------
## 메인 실행부---
if __name__ == '__main__':
    # 웹 서버를 별도의 스레드로 실행
    flask_thread = threading.Thread(target=app.run, kwargs={'host': '127.0.0.1', 'port': 5000, 'debug': False, 'use_reloader': False})
    flask_thread.daemon = True
    flask_thread.start()

    # 메인 스레드에서 모든 인식 및 제어 로직 실행
    run_combined_tracking_and_control()