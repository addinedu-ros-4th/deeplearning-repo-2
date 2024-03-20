# deeplearning-repo-2
딥러닝 프로젝트 2조. Segmentation 및 Object Detection 기반 자율주행

팀명 : 핑클라.👍(Pinkla.b)


## 1. 프로젝트 개요
- **주제 : Segmentation 및 Object Detection 기반 자율주행**
    - **부제 : 주행 경로 및 상황 판단이 가능한 자율주행 RC 카**
- 개발 목표
    - Segmentation + Object Detection
        - 트랙 경로 인식 및 자율 주행
        - 장애물 인식
        - 상황 판단
    - RC 카 제어(HW)
        - 인식 시스템의 output 값에 따른 RC 카 주행 제어
     
- 주제와 유사한 영상
  https://youtu.be/tZta6CqFBY4
  
- 예상 시나리오
  
  ![senario](https://github.com/addinedu-ros-4th/deeplearning-repo-2/assets/87963649/620f6497-cbe4-4a5a-83e3-d8ab19aed0d4)

  도로에 표기한 번호에 따라 시나리오 수행
  
  1 : 우측 통행을 기준으로 주행
  
  2 : 도로를 segmentation을 하여 통행 가능한 도로를 인지하고 주행 시작 (인도, 중앙선 침범 X)
  
  3 : 곡선인 도로를 만났을 때 주행 경로를 표시해준다.
  
  4 : 횡단보도를 만났을 때, 횡단하는 사람이 없다면 출발한다.
  
  5 : 교차로를 만났을 때, 주행 방향 화살표를 인지하고 주행 경로를 표시해준다.
  
  6 : 사람이 횡단보도를 다 건널 때까지 기다린 후 출발한다.
  
  7 : 정차된 차량을 발견하면 기다렸다가 일정 시간 이동을 하지 않는다면 추월
  
  8 : 교차로에서 직진 화살표를 보고 직진
  
  9 : 초기 시작 지점으로 복귀


## 2. 시스템 구성도
![Untitled (1)](https://github.com/addinedu-ros-4th/deeplearning-repo-2/assets/87963649/e143535e-2eb0-4079-9bdc-345238e88ccb)
![Untitled (2)](https://github.com/addinedu-ros-4th/deeplearning-repo-2/assets/87963649/f63f92a6-bed6-4662-8965-e0e7902662b8)


## 3. 기능 리스트
![image](https://github.com/addinedu-ros-4th/deeplearning-repo-2/assets/87963649/5e19c5ca-9178-438e-9319-c10db48c32be)


## 4. 개발 일정 및 역할 분담
- 개발 일정(예상) (~4/11)
    - 아이디어 선정 및 구체화 : 3/14 ~ 3/18
    - 관련 자료 조사 : 3/14 ~ 3/20
    - 오픈소스/모델 테스트  : 3/18 ~ 3/22
    - DB 및 데이터 저장 공간 구축 : 3/25
    - 데이터 수집 및 라벨링 : 3/25 ~ 3/26
    - 모델 학습 : 3/26 ~ 3/27
    - GUI 개발 : 3/27 ~ 3/28
    - RC카 제어 적용 : 3/27 ~
 
- 공통 업무
  - 데이터 라벨링 : 주행 경로 및 상황 인지 객체 라벨링 (contour, box)
    
- 개별 업무(계속 조율)

  ![image](https://github.com/addinedu-ros-4th/deeplearning-repo-2/assets/87963649/7a85cf8d-75e3-4dbc-8dce-1fdce8219d5c)
