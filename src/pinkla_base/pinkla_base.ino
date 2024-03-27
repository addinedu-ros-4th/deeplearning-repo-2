#include <SoftwareSerial.h>
#include <Wire.h>
#include "./Pinkla_SmartMobility.h"

enum AvoidanceState {
  NO_OBSTACLE,
  AVOIDING_BACK,
  AVOIDING_FRONT,
  AVOIDING_LEFT,
  AVOIDING_RIGHT,
  STOPPED
};
AvoidanceState avoidanceState = NO_OBSTACLE;

Pinkla_SmartMobility pinkla = Pinkla_SmartMobility();

int speed = 0;
int cmd = 0;

const int trigPinFront = 2;  // 앞
const int echoPinFront = 3;
const int trigPinRight = 4;  // 우
const int echoPinRight = 5;
const int trigPinBack = 6;  // 뒤
const int echoPinBack = 7;
const int trigPinLeft = 8;  // 좌
const int echoPinLeft = 9;

// 회피할 거리 (센티미터)
const int avoidanceDistance = 20;

void setup() {
  Serial.begin(9600);
  if (!pinkla.begin()) {
    Serial.println("모터 쉴드 연결을 다시 확인해주세요.");
    while (1)
      ;
  }
  speed = 100;
  pinkla.setSpeed(speed);
  pinkla.moveTo(5);
}


#define NUM_ITEMS 7

int value0, value1, value2;
int valuesArray[4];
int w1, w2, w3, w4;

void parseData(String data_str) {
  int data_arr[NUM_ITEMS];
  int i = 0;
  char* ptr = strtok((char*)data_str.c_str(), ",");

  while (ptr != NULL && i < NUM_ITEMS) {
    data_arr[i] = atoi(ptr);
    ptr = strtok(NULL, ",");
    i++;
  }

  value0 = data_arr[0];  // manual, cmd
  value1 = data_arr[1];  // manual speed
  value2 = data_arr[2];  // manual control

  Serial.print(data_arr[0]);
  Serial.print(", ");
  Serial.print(data_arr[1]);
  Serial.print(", ");
  Serial.print(data_arr[2]);
  Serial.print(", ");
  Serial.print(data_arr[3]);
  Serial.print(", ");
  Serial.print(data_arr[4]);
  Serial.print(", ");
  Serial.print(data_arr[5]);
  Serial.print(", ");
  Serial.println(data_arr[6]);

  for (int i = 0; i < NUM_ITEMS - 3; i++) {
    valuesArray[i] = data_arr[i + 3];
  }
}

void loop() {
  if (Serial.available() > 0) {
    String data_str = Serial.readStringUntil('\n');
    parseData(data_str);
  }


  int ctl_type = value0;
  if (ctl_type == 0) {
    if (speed != value1) {
      speed = value1;
      pinkla.setSpeed(speed);
    }

    cmd = value2;
    if (cmd <= 9) {
      pinkla.moveTo(cmd);
    }
    if (cmd == 66) {
      pinkla.rotate(1);
    } else if (cmd == 60) {
      pinkla.rotate(2);
    }
  } else if (ctl_type == 1) {
    w1 = valuesArray[0];
    w2 = valuesArray[1];
    w3 = valuesArray[2];
    w4 = valuesArray[3];

    pinkla.setSpeed(1, abs(w1));
    pinkla.setSpeed(2, abs(w2));
    pinkla.setSpeed(3, abs(w3));
    pinkla.setSpeed(4, abs(w4));

    if (w1 > 0) {
      pinkla.setMotor(1, 1);
    } else {
      pinkla.setMotor(1, 2);
    }
    if (w2 > 0) {
      pinkla.setMotor(2, 1);
    } else {
      pinkla.setMotor(2, 2);
    }
    if (w3 > 0) {
      pinkla.setMotor(3, 1);
    } else {
      pinkla.setMotor(3, 2);
    }
    if (w4 > 0) {
      pinkla.setMotor(4, 1);
    } else {
      pinkla.setMotor(4, 2);
    }
  }
}

float getDistance(int trigPin, int echoPin) {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  long duration = pulseIn(echoPin, HIGH);
  float distance = duration * 0.034 / 2;

  return distance;
}
int16_t offset[3] = { 32, 15, -12 };

void init_sensors_pinmode() {
  pinMode(trigPinFront, OUTPUT);
  pinMode(echoPinFront, INPUT);
  pinMode(trigPinBack, OUTPUT);
  pinMode(echoPinBack, INPUT);
  pinMode(trigPinLeft, OUTPUT);
  pinMode(echoPinLeft, INPUT);
  pinMode(trigPinRight, OUTPUT);
  pinMode(echoPinRight, INPUT);
}