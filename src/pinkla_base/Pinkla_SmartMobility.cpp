#include "Pinkla_SmartMobility.h"


Pinkla_SmartMobility::Pinkla_SmartMobility() {
}

bool Pinkla_SmartMobility::begin() {
	AFMS = Adafruit_MotorShield();

	motor1 = AFMS.getMotor(1); // FL
	motor2 = AFMS.getMotor(2); // FR
	motor3 = AFMS.getMotor(3); // RR
	motor4 = AFMS.getMotor(4); // RL

	return AFMS.begin();
}


void Pinkla_SmartMobility::setSpeed(uint16_t speed) {
	if(speed > 200){
		speed = 200;
	}
	motor1->setSpeed(speed);
	motor2->setSpeed(speed);
	motor3->setSpeed(speed);
	motor4->setSpeed(speed);
}


void Pinkla_SmartMobility::setSpeed(uint8_t id, uint16_t speed) {
	if(speed > 160){
		speed = 160;
	}
	
	if(id == 1){
		motor1->setSpeed(speed);	
	}else if(id == 2){
		motor2->setSpeed(speed);
	}else if(id == 3){
		motor3->setSpeed(speed);  
	}else if(id == 4){
		motor4->setSpeed(speed);  
	}
}

// Pinkla_SmartMobility move function
void Pinkla_SmartMobility::moveF(){
	motor1->run(FORWARD);
	motor2->run(FORWARD);
	motor3->run(FORWARD);
	motor4->run(FORWARD);
}

void Pinkla_SmartMobility::moveF(uint16_t length){
	moveF();
	delay(length);
	stopAll();
}

void Pinkla_SmartMobility::moveL(){
	motor1->run(BACKWARD);
	motor2->run(FORWARD);
	motor3->run(BACKWARD);
	motor4->run(FORWARD);
}

void Pinkla_SmartMobility::moveL(uint16_t length){
	moveL();
	delay(length);
	stopAll();
}

void Pinkla_SmartMobility::moveR(){
	motor1->run(FORWARD);
	motor2->run(BACKWARD);
	motor3->run(FORWARD);
	motor4->run(BACKWARD);
}

void Pinkla_SmartMobility::moveR(uint16_t length){
	moveR();
	delay(length);
	stopAll();
}

void Pinkla_SmartMobility::moveB(){
	motor1->run(BACKWARD);
	motor2->run(BACKWARD);
	motor3->run(BACKWARD);
	motor4->run(BACKWARD);
}

void Pinkla_SmartMobility::moveB(uint16_t length){
	moveB();
	delay(length);
	stopAll();
}

void Pinkla_SmartMobility::moveLF(){
	motor1->run(RELEASE);
	motor2->run(FORWARD);
	motor3->run(RELEASE);
	motor4->run(FORWARD);
}

void Pinkla_SmartMobility::moveLF(uint16_t length){
	moveLF();
	delay(length);
	stopAll();
}

void Pinkla_SmartMobility::moveRF(){
	motor1->run(FORWARD);
	motor2->run(RELEASE);
	motor3->run(FORWARD);
	motor4->run(RELEASE);
}

void Pinkla_SmartMobility::moveRF(uint16_t length){
	moveRF();
	delay(length);
	stopAll();
}

void Pinkla_SmartMobility::moveLB(){
	motor1->run(BACKWARD);
	motor2->run(RELEASE);
	motor3->run(BACKWARD);
	motor4->run(RELEASE);
}

void Pinkla_SmartMobility::moveLB(uint16_t length){
	moveLB();
	delay(length);
	stopAll();
}

void Pinkla_SmartMobility::moveRB(){
	motor1->run(RELEASE);
	motor2->run(BACKWARD);
	motor3->run(RELEASE);
	motor4->run(BACKWARD);
}

void Pinkla_SmartMobility::moveRB(uint16_t length){
	moveRB();
	delay(length);
	stopAll();
}

void Pinkla_SmartMobility::stopAll(){
	motor1->run(RELEASE);
	motor2->run(RELEASE);
	motor3->run(RELEASE);
	motor4->run(RELEASE);
}

void Pinkla_SmartMobility::stopAll(uint16_t length){
	stopAll();
	delay(length);
}

// 스모키 움직임 함수(단독 명령어)
void Pinkla_SmartMobility::moveTo(uint8_t cmd){

	// 사선 좌측 후진 
	if(cmd == 1){ 
		moveLB();
	}
	//후진
	else if(cmd == 2){
		moveB();
	}
	// 사선 우측 후진 
	else if(cmd == 3){
		moveRB();
	}
	// 좌측 수평 이동
	else if(cmd == 4){
		moveL();
	}
	// 정지
	else if(cmd == 5){
		stopAll();
	}
	// 우측 수평 이동
	else if(cmd == 6){
		moveR();
	}
	// 사선 좌측 전진
	else if(cmd == 7){
		moveLF();
	}
	// 전진
	else if(cmd == 8){
		moveF();
	}
	// 사선 우측 전진
	else if(cmd == 9){
		moveRF();
	}
}


// 스모키 움직임 함수(단독 명령어)
void Pinkla_SmartMobility::moveTo(uint8_t cmd, uint16_t length){
	moveTo(cmd);
	delay(length);
	stopAll();
}


// 스모키 움직임 함수(단독 명령어)
void Pinkla_SmartMobility::setMove(uint8_t cmd){
	moveTo(cmd);
}

// 스모키 움직임 함수(단독 명령어)
void Pinkla_SmartMobility::setMove(uint8_t cmd, uint16_t length){
	moveTo(cmd);
	delay(length);
	stopAll();
}

// 스모키 모터 4개 동시 제어(회전 방향)
void Pinkla_SmartMobility::setMotor(uint8_t cmd){
	motor1->run(cmd);
	motor2->run(cmd);
	motor3->run(cmd);
	motor4->run(cmd);
}


// 모터 1개 제어(모터 번호, 회전 방향)
void Pinkla_SmartMobility::setMotor(uint8_t id, uint8_t cmd) {
	if(id == 1){
		motor1->run(cmd);
	}
	else if(id == 2){
		motor2->run(cmd);
	}
	else if(id == 3){
		motor3->run(cmd);
	}
	else if(id == 4){
		motor4->run(cmd);
	}  
}


// CW -> 시계방향(우회전) / CCW -> 반시계방향(좌회전)
void Pinkla_SmartMobility::rotate(uint8_t dir){
	if(dir == 1){
		motor1->run(BACKWARD);
		motor2->run(BACKWARD);
		motor3->run(FORWARD);
		motor4->run(FORWARD);
	}
	
	else if(dir == 2){
		motor1->run(FORWARD);
		motor2->run(FORWARD);
		motor3->run(BACKWARD);
		motor4->run(BACKWARD);		
	}
}

// CW -> 시계방향(우회전), CCW -> 반시계방향(좌회전) / length 회전 시간(ms) 
void Pinkla_SmartMobility::rotate(uint8_t dir, uint16_t length){
	if(dir == 1){
		motor1->run(BACKWARD);
		motor2->run(BACKWARD);
		motor3->run(FORWARD);
		motor4->run(FORWARD);
		delay(length);
		motor1->run(RELEASE);
		motor2->run(RELEASE);
		motor3->run(RELEASE);
		motor4->run(RELEASE);
	}
	
	else if(dir == 2){
		motor1->run(FORWARD);
		motor2->run(FORWARD);
		motor3->run(BACKWARD);
		motor4->run(BACKWARD);
		delay(length);
		motor1->run(RELEASE);
		motor2->run(RELEASE);
		motor3->run(RELEASE);
		motor4->run(RELEASE);		
	}
}


// length -> delay 시간 / iter -> 반복 횟수 / dir 1(CW) -> 시계방향, 2(CCW) -> 반시계방향
void Pinkla_SmartMobility::drawRect(uint16_t length, uint16_t iter, uint8_t dir){
	for(int i = 0; i < iter; i++){
		if(dir == 1){
			motor1->run(FORWARD);
			motor2->run(FORWARD);
			motor3->run(FORWARD);
			motor4->run(FORWARD);
			delay(length);
			
			motor1->run(RELEASE);
			motor2->run(RELEASE);
			motor3->run(RELEASE);
			motor4->run(RELEASE);
			delay(100);			
			
			motor1->run(FORWARD);
			motor2->run(BACKWARD);
			motor3->run(FORWARD);
			motor4->run(BACKWARD);
			delay(length);

			motor1->run(RELEASE);
			motor2->run(RELEASE);
			motor3->run(RELEASE);
			motor4->run(RELEASE);
			delay(100);			
			
			motor1->run(BACKWARD);
			motor2->run(BACKWARD);
			motor3->run(BACKWARD);
			motor4->run(BACKWARD);
			delay(length);
			
			motor1->run(RELEASE);
			motor2->run(RELEASE);
			motor3->run(RELEASE);
			motor4->run(RELEASE);
			delay(100);			
			
			motor1->run(BACKWARD);
			motor2->run(FORWARD);
			motor3->run(BACKWARD);
			motor4->run(FORWARD);
			delay(length);	
		}
		
		else if(dir == 2){
			motor1->run(FORWARD);
			motor2->run(BACKWARD);
			motor3->run(FORWARD);
			motor4->run(BACKWARD);
			delay(length);
			
			motor1->run(RELEASE);
			motor2->run(RELEASE);
			motor3->run(RELEASE);
			motor4->run(RELEASE);
			delay(100);			
			
			motor1->run(FORWARD);
			motor2->run(FORWARD);
			motor3->run(FORWARD);
			motor4->run(FORWARD);
			delay(length);
			
			motor1->run(RELEASE);
			motor2->run(RELEASE);
			motor3->run(RELEASE);
			motor4->run(RELEASE);
			delay(100);			
			
			motor1->run(BACKWARD);
			motor2->run(FORWARD);
			motor3->run(BACKWARD);
			motor4->run(FORWARD);
			delay(length);
			
			motor1->run(RELEASE);
			motor2->run(RELEASE);
			motor3->run(RELEASE);
			motor4->run(RELEASE);
			delay(100);			
			
			motor1->run(BACKWARD);
			motor2->run(BACKWARD);
			motor3->run(BACKWARD);
			motor4->run(BACKWARD);
			delay(length);	
		}
	}
	
	motor1->run(RELEASE);
	motor2->run(RELEASE);
	motor3->run(RELEASE);
	motor4->run(RELEASE);
}
	


// length -> delay 시간 / iter -> 반복 횟수 / dir 1(CW) -> 시계방향, 2(CCW) -> 반시계방향
void Pinkla_SmartMobility::drawTriangle(uint16_t length, uint16_t iter, uint8_t dir){
	for(int i = 0; i < iter; i++){
		if(dir == 1){
			motor1->run(FORWARD);
			motor2->run(RELEASE);
			motor3->run(FORWARD);
			motor4->run(RELEASE);
			delay(length);
			
			motor1->run(RELEASE);
			motor2->run(RELEASE);
			motor3->run(RELEASE);
			motor4->run(RELEASE);
			delay(100);
			
			motor1->run(RELEASE);
			motor2->run(BACKWARD);
			motor3->run(RELEASE);
			motor4->run(BACKWARD);
			delay(length);
			
			motor1->run(RELEASE);
			motor2->run(RELEASE);
			motor3->run(RELEASE);
			motor4->run(RELEASE);
			delay(100);
			
			motor1->run(BACKWARD);
			motor2->run(FORWARD);
			motor3->run(BACKWARD);
			motor4->run(FORWARD);
			delay(length * 1.1);	
		}
		
		else if(dir == 2){
			motor1->run(FORWARD);
			motor2->run(BACKWARD);
			motor3->run(FORWARD);
			motor4->run(BACKWARD);
			delay(length);
			
			motor1->run(RELEASE);
			motor2->run(RELEASE);
			motor3->run(RELEASE);
			motor4->run(RELEASE);
			delay(100);
			
			motor1->run(RELEASE);
			motor2->run(FORWARD);
			motor3->run(RELEASE);
			motor4->run(FORWARD);
			delay(length);
			
			motor1->run(RELEASE);
			motor2->run(RELEASE);
			motor3->run(RELEASE);
			motor4->run(RELEASE);
			delay(100);			
			
			motor1->run(BACKWARD);
			motor2->run(RELEASE);
			motor3->run(BACKWARD);
			motor4->run(RELEASE);
			delay(length * 1.1);
		}
	}
	
	motor1->run(RELEASE);
	motor2->run(RELEASE);
	motor3->run(RELEASE);
	motor4->run(RELEASE);
}


void Pinkla_SmartMobility::setUltrasonic(uint8_t t, uint8_t e){
	trig = t;
	echo = e;
	pinMode(trig, OUTPUT);
	pinMode(echo, INPUT);
}

float Pinkla_SmartMobility::getDistance(){
	digitalWrite(trig, LOW);
	digitalWrite(echo, LOW);
	delayMicroseconds(2);
	digitalWrite(trig, HIGH);
	delayMicroseconds(10);
	digitalWrite(trig, LOW);

	unsigned long duration = pulseIn(echo, HIGH);
	float dis = duration / 29.0 / 2.0;
	
	return dis;
}
