// 파일명: arduino_control.ino
// 파이썬으로부터 서보 모터의 이동 방향을 받아 서서히 움직입니다.

#include <Servo.h>

Servo pan_servo;

// 서보 모터가 연결된 핀 번호
const int pan_servo_pin = 10;

// 서보 모터의 현재 각도
int current_angle = 90;
const int MIN_ANGLE = 0;
const int MAX_ANGLE = 180;
int direction = 0; // 파이썬으로부터 받을 이동 방향 (-1, 0, 1)

void setup() {
  Serial.begin(9600);
  pan_servo.attach(pan_servo_pin);
  // 초기 위치 설정
  pan_servo.write(current_angle);
  Serial.println("Arduino ready.");
}

void loop() {
  // 시리얼 통신으로 방향 값 수신
  if (Serial.available() > 0) {
    String received_data = Serial.readStringUntil('\n');
    direction = received_data.toInt();
    
    // Serial.print("New direction received: ");
    // Serial.println(direction);
  }

  // 받은 방향 값에 따라 현재 각도 변경
  if (direction == 1 && current_angle < MAX_ANGLE) {
    current_angle++;
  } else if (direction == -1 && current_angle > MIN_ANGLE) {
    current_angle--;
  }

  // 서보 모터를 새로운 각도로 이동시킴
  pan_servo.write(current_angle);
  
  // 20ms 동안 프로그램을 멈춰, 모터가 아주 부드럽게 움직이도록 만듭니다.
  delay(20);
}