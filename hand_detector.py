# hand_detector.py
import cv2
import mediapipe as mp
import pyautogui
import requests
import time

def start_hand_detection():
    """
    손 인식을 시작하고 Flask 서버로 zone 값을 전송하는 함수
    """
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(max_num_hands=1)
    cap = cv2.VideoCapture(0)
    screen_width, _ = pyautogui.size()
    
    # 각 구역의 경계 설정
    zone1_end = screen_width // 3
    zone2_end = (screen_width // 3) * 2
    
    server_url = "http://127.0.0.1:5000/command"
    active_zone = 0
    
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            continue

        image = cv2.flip(image, 1)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = hands.process(image_rgb)
        
        current_zone = 0
        
        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            
            # 검지 손가락 끝(랜드마크 8번)의 좌표 가져오기
            index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            
            current_x = int(index_finger_tip.x * screen_width)
            
            # 손의 위치에 따라 zone을 결정
            if current_x < zone1_end:
                current_zone = 1
            elif current_x < zone2_end:
                current_zone = 2
            else:
                current_zone = 3
        
        if current_zone != active_zone:
            try:
                data = {"zone": current_zone}
                requests.post(server_url, json=data)
            except requests.exceptions.ConnectionError:
                pass
            active_zone = current_zone
            
        time.sleep(0.01)

    cap.release()