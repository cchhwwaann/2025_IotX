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
    
    div_zone1_end = screen_width // 3
    div_zone2_end = (screen_width // 3) * 2
    
    server_url = "http://127.0.0.1:5000/command"
    prev_zone = -1

    while cap.isOpened():
        success, image = cap.read()
        if not success:
            continue

        image = cv2.flip(image, 1)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = hands.process(image_rgb)
        
        zone = 0
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                index_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_MCP]
                pinky_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_MCP]
                palm_center_x = (index_mcp.x + pinky_mcp.x) / 2
                x_screen = int(palm_center_x * screen_width)
                
                if x_screen < div_zone1_end:
                    zone = 1
                elif x_screen < div_zone2_end:
                    zone = 2
                else:
                    zone = 3
        
        # zone 값이 이전과 달라졌을 때만 서버에 POST 요청
        if zone != prev_zone:
            try:
                data = {"zone": zone}
                requests.post(server_url, json=data)
            except requests.exceptions.ConnectionError:
                # 서버 연결 오류 발생 시에도 터미널에 메시지를 출력하지 않음
                pass
            prev_zone = zone
            
        # CPU 사용량을 줄이기 위한 작은 딜레이
        time.sleep(0.01)

    cap.release()