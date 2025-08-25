import cv2
import mediapipe as mp
import requests
import json

# MediaPipe hands 모델 초기화
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)
mp_draw = mp.solutions.drawing_utils

# Flask 서버의 주소
flask_server_url = "http://127.0.0.1:5000/hand_coordinates"

# 카메라 장치 열기 (0은 기본 웹캠을 의미)
cap = cv2.VideoCapture(0)

# 카메라가 정상적으로 열렸는지 확인
if not cap.isOpened():
    print("카메라를 열 수 없습니다.")
    exit()

print("카메라를 열었습니다. 'q'를 누르면 종료됩니다.")

try:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("프레임을 받을 수 없습니다.")
            break

        # 프레임을 좌우로 뒤집기
        frame = cv2.flip(frame, 1)

        # BGR 이미지를 RGB로 변환 (MediaPipe는 RGB 이미지를 사용)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 손 인식 처리
        results = hands.process(frame_rgb)
        
        # 인식 결과가 있다면
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # 검지 끝(랜드마크 8번)의 좌표 추출
                index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                
                # 좌표를 0.0 ~ 1.0 사이의 정규화된 값으로 전송
                x_normalized = index_finger_tip.x
                y_normalized = index_finger_tip.y
                
                # 좌표 출력 (디버깅용)
                print(f"정규화된 검지 끝 좌표: ({x_normalized:.2f}, {y_normalized:.2f})")

                # Flask 서버로 좌표 전송
                try:
                    data = {'x': x_normalized, 'y': y_normalized}
                    response = requests.post(flask_server_url, json=data, timeout=0.001)
                except requests.exceptions.RequestException as e:
                    # 서버 연결 오류나 타임아웃 발생 시
                    pass
                
                # 화면에 랜드마크와 연결 선 그리기
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
        else:
            # 손을 인식하지 못했을 때 메시지 출력 (디버깅용)
            print("손을 인식하지 못했습니다.")
                
        # 화면에 프레임 보여주기
        cv2.imshow('Hand Tracking', frame)
        
        # 'q' 키를 누르면 루프 종료
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # 모든 자원 해제
    cap.release()
    cv2.destroyAllWindows()