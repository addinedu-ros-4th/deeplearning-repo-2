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

static float angle[3] = {
  0,
},
             vec;
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


#define NUM_ITEMS 6

int value0, value1;
int valuesArray[4];
int w1, w2, w3, w4;

void parseData(char* buffer) {
  char* token;
  char* tokens[NUM_ITEMS];
  token = strtok(buffer, ",");
  int index = 0;

  while (token != NULL && index < NUM_ITEMS) {
    tokens[index] = token;
    token = strtok(NULL, ",");
    index++;
  }

  value0 = atoi(tokens[0]);
  value1 = atoi(tokens[1]);

  for (int i = 0; i < NUM_ITEMS - 2; i++) {
    valuesArray[i] = atoi(tokens[i + 2]);
  }
}

void loop() {
  uint8_t buffer[256] = { 0 };

  char char_z_val[10];
  char char_humi[20];
  char char_temp[20];
  char char_sv[10];
  char char_dust[20];
  char merge_data[100];

  // sprintf(char_sv, "%d", sv);
  // dtostrf(dustDensity, 6, 2, char_dust);
  // sprintf(char_z_val, "%d", z_val);

  // sprintf(merge_data, "%s,%s,%s,%s,%s", char_temp, char_humi, char_sv, char_dust, char_z_val);
  // sprintf(merge_data, "%s,%s,%s", char_sv, char_dust, char_z_val);

  tcp_on();
  if (tcp_status) {
    // wifi.send((const uint8_t*)&merge_data, strlen(merge_data));
    uint32_t len = wifi.recv(buffer, sizeof(buffer), 10000);
    if (len > 0) {
      String receivedData = String((char*)buffer);
      parseData(buffer);
    }
  }
  tcp_off();


  int cmd_type = value0;
  if (cmd_type == 0) {
    cmd = value1;
    if (cmd <= 9) {
      pinkla.moveTo(cmd);
    }
    if (cmd == 66) {
      pinkla.rotate(1);
    } else if (cmd == 60) {
      pinkla.rotate(2);
    }
  } else if (cmd_type == 1) {
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
  pinMode(A4, INPUT);
  pinMode(V_LED, OUTPUT);
  pinMode(Vo, INPUT);
  pinMode(trigPinFront, OUTPUT);
  pinMode(echoPinFront, INPUT);
  pinMode(trigPinBack, OUTPUT);
  pinMode(echoPinBack, INPUT);
  pinMode(trigPinLeft, OUTPUT);
  pinMode(echoPinLeft, INPUT);
  pinMode(trigPinRight, OUTPUT);
  pinMode(echoPinRight, INPUT);
}