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
    hands = mp_hands.Hands(max_num_hands=2) # 두 손까지 인식하도록 설정
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
        
        # ###################### 수정된 로직: 가장 큰 손 선택 ######################
        if results.multi_hand_landmarks:
            largest_hand_landmarks = None
            max_hand_area = 0

            # 감지된 모든 손을 순회하며 가장 큰 손 찾기
            for hand_landmarks in results.multi_hand_landmarks:
                # 손 랜드마크의 x, y 좌표 범위를 계산하여 손의 크기(면적) 추정
                x_coords = [landmark.x for landmark in hand_landmarks.landmark]
                y_coords = [landmark.y for landmark in hand_landmarks.landmark]
                
                hand_width = max(x_coords) - min(x_coords)
                hand_height = max(y_coords) - min(y_coords)
                hand_area = hand_width * hand_height

                if hand_area > max_hand_area:
                    max_hand_area = hand_area
                    largest_hand_landmarks = hand_landmarks
            
            # 가장 큰 손의 좌표를 사용해 zone 계산
            if largest_hand_landmarks:
                index_mcp = largest_hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_MCP]
                pinky_mcp = largest_hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_MCP]
                palm_center_x = (index_mcp.x + pinky_mcp.x) / 2
                x_screen = int(palm_center_x * screen_width)
                
                if x_screen < div_zone1_end:
                    zone = 1
                elif x_screen < div_zone2_end:
                    zone = 2
                else:
                    zone = 3
        # ##########################################################################
        
        # zone 값이 이전과 달라졌을 때만 서버에 POST 요청
        if zone != prev_zone:
            try:
                data = {"zone": zone}
                requests.post(server_url, json=data)
            except requests.exceptions.ConnectionError:
                pass
            prev_zone = zone
            
        time.sleep(0.01)

    cap.release()