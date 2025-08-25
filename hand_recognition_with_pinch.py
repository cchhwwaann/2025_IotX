# hand_recognition_with_pinch.py

import cv2
import mediapipe as mp
import math
import time
import threading
import socketio

sio = socketio.Client()
FLASK_SERVER_URL = 'http://127.0.0.1:5000'

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

PINCH_THRESHOLD = 50 
pinch_state = "up"
last_pinch_time = 0
PINCH_COOLDOWN = 1.0

def start_hand_recognition():
    """웹캠 인식을 실행하고 WebSocket을 통해 데이터를 전송하는 함수"""
    try:
        sio.connect(FLASK_SERVER_URL)
        print("Hand recognition client connected to server.")
    except Exception as e:
        print(f"Could not connect to server: {e}")
        return

    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("카메라를 열 수 없습니다.")
        sio.disconnect()
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    try:
        with mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5) as hands:
            while cap.isOpened() and sio.connected:
                success, image = cap.read()
                if not success:
                    continue

                image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)
                image.flags.writeable = False
                results = hands.process(image)
                image.flags.writeable = True
                
                finger_coords = None
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        thumb_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
                        index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                        
                        h, w, c = image.shape
                        
                        thumb_x = int(thumb_finger_tip.x * w)
                        thumb_y = int(thumb_finger_tip.y * h)
                        finger_coords = {'x': thumb_x, 'y': thumb_y}
                        
                        distance = math.sqrt((index_finger_tip.x * w - thumb_x)**2 + (index_finger_tip.y * h - thumb_y)**2)
                        
                        global pinch_state, last_pinch_time
                        
                        if distance < PINCH_THRESHOLD:
                            if pinch_state == "up":
                                pinch_state = "down"
                        else:
                            if pinch_state == "down" and (time.time() - last_pinch_time) > PINCH_COOLDOWN:
                                pinch_state = "up"
                                last_pinch_time = time.time()
                                try:
                                    sio.emit('click_event', {'x': thumb_x, 'y': thumb_y})
                                except Exception:
                                    pass

                if finger_coords:
                    try:
                        sio.emit('hand_position', finger_coords)
                    except Exception:
                        pass
                
    finally:
        cap.release()
        sio.disconnect()
        print("Hand recognition thread stopped.")

if __name__ == '__main__':
    start_hand_recognition()