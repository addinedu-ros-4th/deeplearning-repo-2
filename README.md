# 경로 주행 및 상황 판단이 가능한 자율주행 모바일 로봇
> **부제 : Segmentation 및 Object Detection 기반 자율주행**
> 
> **팀명 : Pinkla👍(딥러닝 프로젝트 2조)**

## 0. 최종 시연 영상
> **자율주행 및 실시간 GUI 관제**

<div align="center">
  <a href="https://www.youtube.com/watch?v=h8wTT3QrS3Q">
    <img src="https://github.com/addinedu-ros-4th/deeplearning-repo-2/assets/103230856/65c96e64-1418-44d9-922d-a8f26018ec68" alt="pinkla b" width="100%" height="100%">
  </a>
</div>

## 1. 프로젝트 개요
### 1.1. 활용 기술
| 구분 | 상세 |
|------------------|-----------------------------------------------------------------------------------------|
| 개발 환경| <img src="https://img.shields.io/badge/ubuntu-E95420?style=for-the-badge&logo=ubuntu&logoColor=white"> <img src="https://img.shields.io/badge/python-3776AB?style=for-the-badge&logo=python&logoColor=white">|
| 딥러닝 및 영상처리 | ![image](https://github.com/addinedu-ros-4th/deeplearning-repo-2/assets/87963649/4b5eb6a3-0777-41c9-b498-2ea8e5a8daf5) <img src="https://img.shields.io/badge/opencv-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white"> <img src="https://img.shields.io/badge/pytorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white">|
| 데이터베이스| <img src="https://img.shields.io/badge/aws rds-527FFF?style=for-the-badge&logo=amazonaws&logoColor=white"> <img src="https://img.shields.io/badge/mysql-4479A1?style=for-the-badge&logo=mysql&logoColor=white">|
| GUI| <img src="https://img.shields.io/badge/qt-41CD52?style=for-the-badge&logo=qt&logoColor=white">|
| 통신| ![image](https://github.com/addinedu-ros-4th/deeplearning-repo-2/assets/87963649/9d587f25-a595-453d-baee-f5f034e5a1cf)|
| 하드웨어| <img src="https://img.shields.io/badge/raspberry pi 5-A22846?style=for-the-badge&logo=raspberrypi&logoColor=white"> <img src="https://img.shields.io/badge/arduino-00878F?style=for-the-badge&logo=arduino&logoColor=white">|
| 형상관리 및 협업| <img src="https://img.shields.io/badge/github-181717?style=for-the-badge&logo=github&logoColor=white"> <img src="https://img.shields.io/badge/notion-000000?style=for-the-badge&logo=notion&logoColor=white"> <img src="https://img.shields.io/badge/slack-4A154B?style=for-the-badge&logo=slack&logoColor=white">|

### 1.2. 프로젝트 목표
- **Segmentation 기반 차선 검출 및 주행**
    - 주행 경로 인식 및 판단 : 차선(외곽선, 중앙선, 교차로) 검출을 통한 주행 목표 위치 설정
    - 모바일 로봇 제어 : 목표 위치 이동을 위한 메카넘 휠 주행 제어
- **Object Detection 기반 교통 상황 판단**
    - 교통 객체 인식 : 신호등, 방향 지시, 정지선/횡단보도, 차량, 보행자 인식 및 거리 계산
    - 상황 판단 : 객체별 거리 및 객체간 상호 관계 조합을 통한 교통 상황별 제어

## 2. 기능 리스트



## 3. 시스템 구성
### 3.1. 구성도
![image](https://github.com/addinedu-ros-4th/deeplearning-repo-2/assets/87963649/f1946a1b-1d22-4cfe-859f-3b090325ab0c)
### 3.2. 차선 인식 시퀀스
### 3.3. 객체 인식 시퀀스
### 3.4. 전체 시나리오 시퀀스


## 4. 개발 일정 및 역할 분담
### 4.1. 이슈별 일정 관리
> 진행 기간 : 2024.03.15 ~ 2024.04.11

![image](https://github.com/addinedu-ros-4th/deeplearning-repo-2/assets/87963649/d096d41f-d745-400c-a2c2-63dd7c08e481)
### 4.2. 팀 구성원별 담당 사항
| 구분 | 이름 | 업무 |
|------|--------|-------------------------------------------------------------------------------------------|
| 팀장 | 김태형 [📧](mailto:gudxok911@gmail.com)| - 이슈 및 일정 관리, Github 및 Notion 관리<br>- GUI 전체 구성, 관제 ↔ 로봇 소켓 통신 구현<br>- 차선 검출 성능 개선 및 타겟 포인트 도출 구현<br>- 차선 주행 제어 및 교통 상황 별 동작 제어 구현 |
| 팀원 | 이지호 [📧](mailto:dlwlgh0106@gmail.com)| - 차선 검출 모델 테스트<br>- 차선 검출 성능 개선 및 중심점 도출 구현<br>- GUI ↔ AWS DB 연동<br>- 주행 및 교통 관련 데이터 시각화 구현 |
| 팀원 | 이정욱 [📧](mailto:leejungwook0211@gmail.com)| - 차선 검출 모델 테스트<br>- 교통 객체 검출 및 거리 측정 구현<br>- IO 하드웨어 및 교통 상황 별 IO 제어 구현 |
| 팀원 | 유동규 [📧](mailto:rdk5607@gmail.com)| - 차선 검출 모델 테스트<br>- 교통 객체 검출 및 거리 측정 테스트<br>- YOLOv8 학습 |
| 팀원 | 임수빈 [📧](mailto:lsv2620@gmail.com)| - 차선 검출 모델 테스트<br>- 교통 객체 검출 및 거리 측정 구현<br>- 교통 상황 인지 및 판단 구현<br>- YOLOv8 학습 |

## 5. 결과
### 5.1. 구현 결과
### 5.2. 개선 사항
