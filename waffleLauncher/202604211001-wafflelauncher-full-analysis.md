# waffleLauncher_full 전체 분석

## 시스템 개요

waffleLauncher는 **WaffleCar** 로봇 자동차를 PC에서 원격 제어하는 시스템이다.
PC 측의 PyQt5 GUI(`main.py`)와 차량 탑재 서버(`wafflecarServer.py`, Onion Omega2)가 TCP 소켓으로 통신한다.

```
[PC - waffleLauncher]  ←── WiFi TCP ───→  [WaffleCar - Onion Omega2]
  main.py (GUI)                              wafflecarServer.py
  - 영상 처리                                - PCA9685 PWM 제어
  - 알고리즘 실행                            - 서보/DC모터 구동
  - 명령 전송                                - LiDAR 거리 응답
  - Blockly 편집기                           - mjpg-streamer 카메라
```

---

## 하드웨어 구성 (WaffleCar)

| 구성요소 | 내용 |
|---|---|
| 메인 보드 | Onion Omega2 (OpenWRT, Python 2.7) |
| 확장 보드 | WaffleBoard V3.0 |
| PWM 컨트롤러 | PCA9685 (I2C 주소 0x40) |
| 거리 센서 | LiDAR / ToF 센서 (I2C 주소 0x29) |
| 카메라 | USB 카메라 + mjpg-streamer |
| 모터 | DC 모터 2개 (좌우 독립 구동) |
| 조향 | 서보 모터 1개 (PCA9685 채널 0) |

### PCA9685 채널 배치

| 채널 | 역할 |
|---|---|
| 0 | 서보 모터 (조향) |
| 2, 3 | 오른쪽 DC모터 (Motor 2) |
| 4, 5 | 왼쪽 DC모터 (Motor 1) |

---

## 통신 프로토콜

### 네트워크

| 포트 | 용도 |
|---|---|
| `19126` TCP | 제어 명령 송수신 |
| `8080` HTTP | MJPEG 카메라 스트리밍 (`?action=stream`) |

### 명령 포맷

#### L 모드 (저수준 — 전진/후진/정지 + 조향)
```
L<motion><angle>E
```
| 필드 | 내용 |
|---|---|
| motion | `0`=정지, `1`=전진, `2`=후진, `3`=조향테스트 |
| angle | 3자리 숫자 (예: `150` = 중립) |

예시:
```
L0150E   → 정지, 조향 중립
L1150E   → 전진, 조향 중립
L1180E   → 전진, 우회전
```

#### H 모드 (고수준 — 좌우 바퀴 독립 제어)
```
H,<right_wheel>,<left_wheel>,<angle>,E
```
| 필드 | 내용 |
|---|---|
| wheel | `F0`=정지, `F1`=저속전진, `F2`=중속전진, `F3`=고속전진 |
| wheel | `B1/B2/B3`=후진 속도 |
| angle | 조향각 (숫자) |

예시:
```
H,F1,F1,150,E   → 좌우 저속 전진
H,F0,F0,150,E   → 정지
H,F3,F3,150,E   → 고속 전진
```

#### S 모드 (서보 기본값 설정)
```
S<value>E   예: S330E
```

#### Q (연결 종료)
```
Q
```

### 응답 (서버 → PC)
각 명령 수신 후 LiDAR 거리를 4자리 숫자 문자열로 응답:
```
0120   → 120mm
0000   → 감지 불가 (범위 초과: <20mm 또는 >2000mm)
```

---

## PC 측 소프트웨어 구조

### 파일 목록

| 파일 | 역할 |
|---|---|
| `main.py` | 메인 진입점, GUI 컨트롤러 |
| `mainUI.py` | PyQt5 Designer 생성 UI (자동 생성, 수정 불필요) |
| `wafflecarUtil.py` | 차선 검출 유틸리티 함수 모음 |
| `algorithm.py` | 사용자 작성 자율주행 알고리즘 |
| `algorithm_AutoCreated.py` | Blockly에서 자동 생성된 알고리즘 |
| `AutoCreated.py` | Blockly 런타임용 (서버에 전송되지 않음) |
| `yoloTest.py` | YOLOv3 추론 테스트 스크립트 |
| `waffleBlockly/` | Blockly 웹 에디터 정적 파일 |
| `wafflecarServer/` | 차량 탑재 서버 파일 + 설정 가이드 |
| `cameraParams.txt` | 카메라 렌즈 왜곡 보정 파라미터 |
| `keras_model.h5` | TensorFlow/Keras 이미지 분류 모델 |
| `labels.txt` | Keras 모델 레이블 |

### GUI 탭 구성 (mainUI.py 기반)

| 탭 | 내용 |
|---|---|
| Tab 1 (와플카) | 실시간 카메라 + 와플카 시작/정지 |
| Tab 2 (시뮬레이션) | 저장된 이미지로 오프라인 시뮬레이션 |
| Tab 3 (설정) | IP, 슬라이더(조향 정렬), Canny 임계값 |
| Tab 4 (Blockly) | 웹 기반 블록 코딩 에디터 |

---

## 이미지 처리 파이프라인 (main.py)

```
1. 카메라 프레임 수신 (MJPEG 스트리밍)
2. 렌즈 왜곡 보정 (cv2.remap, cameraParams.txt)
3. ROI 추출 → 하단 180~360px (전방 도로 영역)
4. 그레이스케일 변환
5. 가우시안 블러 (kernel=3)
6. Canny 에지 검출 (사용자 설정 임계값)
7. Hough 직선 변환 (rho=1, theta=1°, threshold=55, minLen=20, gap=10)
8. 접촉점 추출 (수평 H1/H2/H3 × 좌우, 수직 V1~V7)
9. 차선 분류 (leftLane, rightLane, frontLane)
10. autoDrive_algorithm() 호출
11. 명령 문자열 생성 → TCP 전송
```

### 접촉점 좌표 체계

이미지 폭을 8등분(V1~V7), 높이를 4등분(H1~H3)하여 에지와의 거리 측정:

```
H1LD / H1RD  → height/4*1 수평선에서 중심까지 좌/우 거리
H2LD / H2RD  → height/4*2 수평선 (중간)
H3LD / H3RD  → height/4*3 수평선 (하단)
V1D ~ V7D    → 각 수직선에서 하단까지 에지 거리
```

---

## 알고리즘 (algorithm.py)

현재 알고리즘은 **TensorFlow/Keras 이미지 분류 모델**을 사용한다.

### 동작 방식

```
1. status==1 (초기화): keras_model.h5 로드, labels.txt 파싱
2. 매 프레임: 원본 이미지를 224×224로 리사이즈 + 정규화
3. 모델 추론 → 클래스 예측 (slow / stop / track)
4. 예측 결과에 따라 명령 생성:
   - slow  → H,F1,F1,150,E  (저속 전진)
   - stop  → H,F0,F0,150,E  (정지)
   - track → H,F3,F3,150,E  (고속 전진)
```

### autoDrive_algorithm() 함수 시그니처

```python
def autoDrive_algorithm(
    original_img,   # 원본 이미지 (BGR, numpy array)
    canny_img,      # Canny 처리된 이미지
    H1LD, H1RD,    # 수평선 1 좌/우 거리
    H2LD, H2RD,    # 수평선 2 좌/우 거리
    H3LD, H3RD,    # 수평선 3 좌/우 거리
    V1D ~ V7D,     # 수직 거리 7개
    leftLane,       # 왼쪽 차선 직선 (x1,y1,x2,y2)
    rightLane,      # 오른쪽 차선 직선
    frontLane,      # 전방 횡단선 목록
    LiDAR,          # LiDAR 거리 (mm)
    prevComm,       # 이전 명령
    status          # 상태 (int 또는 list)
) -> (command, status)
```

### 상태 전이 패턴

```python
if status == 1:   # 첫 프레임: 초기화
    # 모델 로드, 변수 초기화
    status = [model, data, ...]
else:             # 이후 프레임: 상태에서 변수 복원
    model = status[0]
    ...
return command, status
```

---

## 차량 탑재 서버 (wafflecarServer.py)

Onion Omega2에서 실행. Python 2.7 기반.

### 동작 흐름

```
1. TCP 서버 바인드 (0.0.0.0:19126)
2. 클라이언트 접속 대기
3. 접속 시 vehicle_stop() 실행 (안전)
4. startServer() 루프:
   a. recv(16)   → 명령 수신
   b. 명령 파싱 (H/L/Q/S)
   c. PCA9685 PWM 출력
   d. sendall(getDistance())   → LiDAR 응답
5. 'Q' 수신 시 연결 종료, 다시 대기
```

### 워치독 타이머
명령 수신이 2초 이상 없으면 자동 정지(`vehicle_stop()`) 실행.

### 서보 조향 계산
```
입력 angle: 50~250 (중립 150)
최종 PWM = angle + servoDefaultValue
servoDefaultValue: /root/servoDefaultValue.txt에서 로드 (기본 330)
```

---

## wafflecarUtil.py 핵심 함수

| 함수 | 설명 |
|---|---|
| `gaussian_blur(img, 3)` | 노이즈 제거 |
| `canny(img, low, high)` | 에지 검출 |
| `hough_lines(img, ...)` | 직선 검출 |
| `getContactPoints(img)` | 13개 접촉점 좌표 반환 |
| `getLane(lines)` | 좌/우/전방 차선 분류 |
| `getAlignedWheelAngle(cmd, align)` | 조향 오프셋 적용 |
| `getCenterPoint(left, right)` | 양 차선 중심점 계산 |

### getAlignedWheelAngle 계산
```python
alignAngle = (slider_value * 5) - 25   # slider 0~10 → -25~+25
# L 모드: angle += alignAngle
# H 모드: steering_value += alignAngle
```

---

## Blockly 통합

### 동작 방식
1. `QWebEngineView`로 `waffleBlockly/demo/code/index.html` 로드
2. `QWebChannel`을 통해 JS ↔ Python 양방향 통신
3. `CallHandler.send_Data()`: JS에서 Python으로 데이터 전달
   - `XML...` 접두사: 블록 레이아웃 저장 (`savedBlocks.xml`)
   - `PYPY...` 접두사: 생성된 Python 코드 저장 → `algorithm_AutoCreated.py` 변환
4. `CallHandler.get_data` 시그널: Python에서 JS로 데이터 전달
   - `LOAD<xml>`: 블록 불러오기
   - `SAVE`: 현재 블록 저장 요청

### 알고리즘 선택 로직
```python
# 두 파일 중 더 최근에 수정된 것을 사용
a1 = os.path.getmtime('algorithm.py')
a2 = os.path.getmtime('algorithm_AutoCreated.py')
if a1 > a2:
    load algorithm.py
else:
    load algorithm_AutoCreated.py
```

---

## YOLOv3 기존 구현 (yoloTest.py)

`savedImage/` 폴더의 이미지에 YOLOv3 추론을 수행하여 `_d.png`로 저장하는 배치 스크립트.

- 모델: `yolov3_2000.weights` + `yolov3.cfg`
- 클래스 파일: `classes.names`
- 추론: `cv2.dnn` (OpenCV DNN 백엔드)
- NMS 임계값: confidence 0.5, IoU 0.4

> **참고**: 이 스크립트는 독립 실행용이며 main.py와 직접 연동되지 않는다.
> 차량 탑재 서버(`wafflecarServer/`)에는 별도의 YOLOv3 가중치 파일이 있다.
> YOLOv8로 전환 예정이다 → [[202604211002-yolov8-training]]

---

## 관련 문서

- [[202604211000-wafflelauncher-setup]] — 환경 설정 및 패키지 설치
- [[202604211002-yolov8-training]] — YOLOv8 모델 학습
- [[202604211003-waffleboard-setup]] — Omega2 보드 초기 설정
