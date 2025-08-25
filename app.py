from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# 엄지와 검지 손가락의 좌표를 저장할 전역 변수
hand_coordinates = {'thumb_x': 0, 'thumb_y': 0, 'index_x': 0, 'index_y': 0}

# 루트 URL (http://127.0.0.1:5000/)에 접속하면 index.html을 보여줍니다.
@app.route('/')
def index():
    return render_template('index.html')

# hand_tracking.py 스크립트가 엄지-검지 좌표를 보낼 라우팅
@app.route('/hand_coordinates', methods=['POST'])
def receive_coordinates():
    global hand_coordinates
    data = request.get_json()
    if data:
        # 엄지와 검지 좌표를 모두 받아 저장
        hand_coordinates['thumb_x'] = data.get('thumb_x')
        hand_coordinates['thumb_y'] = data.get('thumb_y')
        hand_coordinates['index_x'] = data.get('index_x')
        hand_coordinates['index_y'] = data.get('index_y')
        return jsonify({'status': 'success'}), 200
    return jsonify({'status': 'error'}), 400

# 프론트엔드가 좌표를 요청할 라우팅
@app.route('/get_coordinates', methods=['GET'])
def get_coordinates():
    global hand_coordinates
    return jsonify(hand_coordinates), 200

if __name__ == '__main__':
    # Flask 서버는 다른 스레드에서 실행되어야 hand_tracking.py와 동시에 동작할 수 있습니다.
    # 하지만 이 예제에서는 단순화를 위해 debug=True로 설정합니다.
    app.run(debug=True)