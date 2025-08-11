# main.py
import time
import threading
import subprocess
import os

# Flask 서버를 실행하는 함수
def run_flask():
    # 'app.py'를 별도의 프로세스로 실행
    # stdout과 stderr 옵션을 제거하여 로그가 터미널에 출력되도록 함
    subprocess.run(["python", "app.py"])

# 손 인식기를 실행하는 함수
def run_hand_detector():
    from hand_detector import start_hand_detection
    start_hand_detection()

if __name__ == "__main__":
    # Flask 서버 스레드 시작
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Flask 서버가 시작될 시간을 잠시 기다림 (매우 중요)
    time.sleep(2)

    # 손 인식기 스레드 시작
    hand_thread = threading.Thread(target=run_hand_detector)
    hand_thread.daemon = True
    hand_thread.start()

    # 메인 스레드는 계속 실행되도록 유지
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Program terminated.")