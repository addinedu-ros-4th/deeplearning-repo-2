#include <Arduino.h>
#include <Adafruit_MotorShield.h>

#define F 2
#define B 8
#define S 5
#define L 4
#define R 6
#define LF 7
#define RF 9
#define LB 1
#define RB 3

#define CW 1
#define CCW 2

class Pinkla_SmartMobility {
  public:
    Pinkla_SmartMobility ();
	
	bool begin();
	
	void
		moveF(),
		moveF(uint16_t),
		moveL(),
		moveL(uint16_t),
		moveR(),
		moveR(uint16_t),
		moveB(),
		moveB(uint16_t),
		moveLF(),
		moveLF(uint16_t),
		moveRF(),
		moveRF(uint16_t),
		moveLB(),
		moveLB(uint16_t),
		moveRB(),
		moveRB(uint16_t),
		stopAll(),
		stopAll(uint16_t),
		 
		moveTo(uint8_t),   // 스모키의 이동 방향 제어(이동 방향)
		moveTo(uint8_t, uint16_t),   // 스모키의 이동 방향 제어(이동 방향, 시간)
	
		setMove(uint8_t),   // 스모키의 이동 방향 제어(이동 방향)
		setMove(uint8_t, uint16_t),   // 스모키의 이동 방향 제어(이동 방향, 시간)
    
		setSpeed(uint16_t),  // 모터 4개의 속도 제어(속도)
		setSpeed(uint8_t, uint16_t),  // 모터 1개의 속도 제어 (모터 번호, 속도)
			
		setMotor(uint8_t),  // 모터 4개의 방향 제어(방향)
		setMotor(uint8_t, uint8_t),  // 모터 1개의 방향 제어(모터 번호, 방향)
	
		rotate(uint8_t), // RC카 제자리 회전(방향)
		rotate(uint8_t, uint16_t), // RC카 제자리 회전(방향, 시간)
	
		drawRect(uint16_t, uint16_t, uint8_t), //  사각형 그리기(길이, 횟수, 방향)
		drawTriangle(uint16_t, uint16_t, uint8_t), //  삼각형 그리기(길이, 횟수, 방향)
		
		setUltrasonic(uint8_t, uint8_t);
		
	float getDistance();

  private:
    Adafruit_MotorShield AFMS;
    Adafruit_DCMotor *motor1;
    Adafruit_DCMotor *motor2;
    Adafruit_DCMotor *motor3;
    Adafruit_DCMotor *motor4;
	uint8_t trig;
	uint8_t echo;
};
