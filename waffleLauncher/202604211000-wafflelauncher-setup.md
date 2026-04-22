# waffleLauncher 환경 설정

## 프로젝트 개요

waffleLauncher는 PyQt5 기반의 자동차(와플카) 원격 제어 GUI 애플리케이션이다.
카메라 스트리밍, LiDAR 데이터 수신, 차선 인식 알고리즘, Blockly 코드 편집기를 통합한다.

- **경로**: `C:\Users\x0011\OneDrive\바탕 화면\waffleLauncher_full`
- **진입점**: `main.py`
- **버전**: Waffle Launcher V2.93

---

## 의존 패키지 설치

### 설치 확인된 패키지

| 패키지 | 버전 | 용도 |
|---|---|---|
| `PyQt5` | 5.15.11 | GUI 프레임워크 |
| `opencv-python` | 4.12.0 | 영상 처리 |
| `numpy` | 2.2.6 | 수치 연산 |

### 추가 설치 필요 패키지

```bash
pip install PyQtWebEngine Pillow
```

| 패키지 | 이유 |
|---|---|
| `PyQtWebEngine` | `QWebEngineView`, `QWebChannel` (Blockly 에디터 렌더링에 필요) |
| `Pillow` | `from PIL import Image, ImageOps` (이미지 전처리) |

### 전체 설치 명령 (한 번에)

```bash
pip install PyQt5 PyQtWebEngine opencv-python numpy Pillow
```

---

## 실행 방법

```bash
cd "C:\Users\x0011\OneDrive\바탕 화면\waffleLauncher_full"
python main.py
```

---

## 프로젝트 구조

```
waffleLauncher_full/
├── main.py                  # 진입점, PyQt5 메인 윈도우
├── mainUI.py                # Qt Designer 생성 UI 코드
├── wafflecarUtil.py         # 차선 감지 유틸리티 함수
├── algorithm.py             # 사용자 작성 자율주행 알고리즘
├── algorithm_AutoCreated.py # Blockly에서 자동 생성된 알고리즘
├── waffleBlockly/           # Blockly 웹 에디터 (HTML/JS)
├── wafflecarServer/         # 와플카 서버 관련
├── savedImage/              # 녹화된 이미지 저장 폴더
├── cameraParams.txt         # 카메라 캘리브레이션 파라미터
└── savedBlocks.xml          # 저장된 Blockly 블록
```

---

## 아키텍처

### 주요 클래스

| 클래스 | 역할 |
|---|---|
| `waffleLauncher` | 메인 컨트롤러, UI 이벤트 처리 |
| `ImageStreamingThread` | 카메라 스트림 수신 (QThread) |
| `LiDARStreamingThread` | LiDAR 거리 데이터 수신 (QThread) |
| `SimulationThread` | 저장된 이미지로 시뮬레이션 (QThread) |
| `CallHandler` | JS ↔ Python 웹채널 통신 |

### 통신 방식

- **자동차 제어**: TCP 소켓, 포트 `19126`, IP `192.168.3.1`
- **카메라 스트리밍**: HTTP MJPEG, `http://<IP>:8080/?action=stream`
- **LiDAR**: TCP 소켓 (같은 소켓 재사용, recv 5bytes)

### 명령 포맷

```
L<angle><speed>E   예: L0150E  (직진, 속도 150)
S<value>E          예: S0150E  (서보모터 기본값 설정)
Q                  종료
```

---

## 이미지 처리 파이프라인

```
카메라 프레임
    → 카메라 왜곡 보정 (cv2.remap)
    → ROI 추출 (하단 180~360px)
    → 그레이스케일 변환
    → 가우시안 블러 (kernel 3)
    → Canny 에지 검출
    → Hough 변환 (직선 검출)
    → 접촉점(Contact Points) 추출
    → autoDrive_algorithm() 호출
    → 명령어 생성 → 와플카 전송
```

---

## 관련 문서

- [[202604211001-wafflelauncher-algorithm]] — 알고리즘 작성 방법
- [[202604211002-yolov8-training]] — YOLOv8 모델 학습
