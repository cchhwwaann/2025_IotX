# hand_detector.py
import cv2
import mediapipe as mp
import pyautogui
import requests
import time

def start_hand_detection():
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(max_num_hands=1)
    cap = cv2.VideoCapture(0)
    screen_width, _ = pyautogui.size()
    
    server_url_zone = "http://127.0.0.1:5000/zone"
    server_url_click = "http://127.0.0.1:5000/click"
    active_zone = 0
    
    # 핀치 제스처의 시작과 끝을 감지하기 위한 플래그
    is_pinching_started = False
    
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            continue

        image = cv2.flip(image, 1)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = hands.process(image_rgb)
        
        current_zone = 0
        is_pinching_this_frame = False
        
        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            
            index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
            
            pinch_distance = ((index_finger_tip.x - thumb_tip.x)**2 + 
                              (index_finger_tip.y - thumb_tip.y)**2)**0.5
            
            if pinch_distance < 0.05:
                is_pinching_this_frame = True

            current_x = int(index_finger_tip.x * screen_width)
            
            if current_x < screen_width // 3:
                current_zone = 1
            elif current_x < (screen_width // 3) * 2:
                current_zone = 2
            else:
                current_zone = 3
        
        # '집었다가 놓는' 클릭 감지 로직
        if is_pinching_this_frame:
            # 핀치 제스처가 시작되었음을 기록
            if not is_pinching_started:
                is_pinching_started = True
        else:
            # 핀치 제스처가 해제되었을 때 (놓았을 때) 클릭 이벤트 발생
            if is_pinching_started:
                try:
                    data = {"zone": active_zone}
                    requests.post(server_url_click, json=data)
                except requests.exceptions.ConnectionError:
                    pass
                is_pinching_started = False # 상태 초기화
        
        if current_zone != active_zone:
            try:
                data = {"zone": current_zone}
                requests.post(server_url_zone, json=data)
            except requests.exceptions.ConnectionError:
                pass
            active_zone = current_zone
            
        time.sleep(0.01)

    cap.release()   