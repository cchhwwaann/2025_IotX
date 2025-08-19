# main.py
import time
import threading
import subprocess

# Flask 서버 실행
def run_flask():
    # 'app.py'를 별도의 프로세스로 실행
    subprocess.run(["python", "app.py"])

# hand_detector 실행 함수
def run_hand_detector():
    from hand_detector import start_hand_detection
    start_hand_detection()

if __name__ == "__main__":
    # Flask 서버 스레드 시작
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Flask 서버가 시작될 시간 대기 (매우 중요)
    time.sleep(2)

    # hand_detector 스레드 시작
    hand_thread = threading.Thread(target=run_hand_detector)
    hand_thread.daemon = True
    hand_thread.start()

    # 메인 스레드는 계속 실행되도록 유지 (스레드가 종료되지 않게 함)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Program terminated.")