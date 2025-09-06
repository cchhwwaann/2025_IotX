// 파일명: arduino_control.ino
// 파이썬으로부터 목표 각도를 받아 서보 모터를 1도씩 서서히 이동시킵니다.

#include <Servo.h>

Servo pan_servo; 

// 서보 모터가 연결된 핀 번호
const int pan_servo_pin = 10;

// 서보 모터의 현재 각도와 목표 각도
int current_angle = 90;
int target_angle = 90;

void setup() {
  Serial.begin(9600);
  pan_servo.attach(pan_servo_pin);
  // 초기 위치 설정
  pan_servo.write(current_angle);
  Serial.println("Arduino ready.");
}

void loop() {
  // 시리얼 통신으로 목표 각도 수신
  if (Serial.available() > 0) {
    String received_data = Serial.readStringUntil('\n');
    int angle = received_data.toInt();
    
    // 유효한 각도 범위(0~180)인지 확인
    if (angle >= 0 && angle <= 180) {
      target_angle = angle;
      Serial.print("New target angle received: ");
      Serial.println(target_angle);
    }
  }

  // 현재 각도와 목표 각도가 다르면 1도씩 이동
  if (current_angle != target_angle) {
    if (current_angle < target_angle) {
      current_angle++;
    } else {
      current_angle--;
    }
    
    // 서보 모터를 새로운 각도로 이동시킴
    pan_servo.write(current_angle);
    
    // 이 딜레이가 핵심입니다.
    // 20ms 동안 프로그램을 멈춰, 모터가 아주 부드럽게 움직이도록 만듭니다.
    delay(20); 
  }
}