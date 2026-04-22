# waffleLauncher 경량 배포 전략

## 문제 상황

`waffleLauncher_full/` 폴더의 실제 크기:

| 폴더 | 크기 | 내용 | 배포 필요? |
|---|---|---|---|
| `dist/` | 3.2G | PyInstaller 빌드 결과물 | **제외** |
| `savedImage/` | 524M | 주행 녹화 이미지 | **제외** |
| `copy/` | 285M | 소스 백업본 | **제외** |
| `coco/` | 271M | COCO 데이터셋 | **제외** |
| `src/` | 270M | 기타 소스 | 선택 |
| `build/` | 151M | PyInstaller 빌드 캐시 | **제외** |
| `darknet-master/` | 122M | 구버전 YOLO (미사용) | **제외** |
| **실제 소스코드** | **~수 MB** | `.py`, `.xml`, `.ui` 등 | **배포** |

전체 약 4.8GB → **소스코드만 수 MB** 로 줄일 수 있다.

---

## 배포 전략 — 소스 배포 (권장)

### 핵심 원칙

> 의존 패키지는 배포하지 않는다. 사용자가 직접 설치한다.

```
배포자: 소스 파일 + requirements.txt 제공 (수 MB)
사용자: pip install -r requirements.txt 실행 (패키지 자동 설치)
```

---

## 배포 대상 파일 목록 (필수)

```
waffleLauncher/              ← 이 폴더만 압축해서 배포
├── main.py                  ← 진입점
├── mainUI.py                ← Qt UI 클래스
├── main.ui                  ← Qt Designer UI 파일
├── wafflecarUtil.py         ← 유틸리티 함수
├── algorithm.py             ← 자율주행 알고리즘 (학생이 수정)
├── algorithm_AutoCreated.py ← Blockly 자동 생성 알고리즘
├── AutoCreated.py           ← Blockly 자동 생성 코드
├── waffleBlockly/           ← Blockly 에디터 HTML/JS (필수)
├── calibration/
│   └── calibration.py       ← 카메라 캘리브레이션
├── cameraParams.txt         ← 카메라 내부 파라미터
├── initBlocks.xml           ← Blockly 초기 블록 설정
├── waffleLauncher.ico       ← 아이콘
├── requirements.txt         ← 의존 패키지 목록 (새로 생성)
└── README.md                ← 설치 안내 (새로 생성)
```

### 선택적 포함

```
yolo_model.pt        ← YOLO 모델 (팀별로 학습한 것 사용, 없어도 실행됨)
```

### 제외 대상

```
dist/                ← PyInstaller 빌드 결과 (불필요)
build/               ← 빌드 캐시 (불필요)
copy/                ← 소스 백업 (불필요)
savedImage/          ← 녹화 이미지 (팀별 보유)
coco/                ← COCO 데이터셋 (학습 시만 필요)
darknet-master/      ← 구버전 YOLO (미사용)
src/                 ← 기타 테스트 파일 (불필요)
keras_model.h5       ← 구버전 모델 (YOLOv11로 대체됨)
keras_model.onnx     ← 구버전 모델 (YOLOv11로 대체됨)
labels.txt           ← 구버전 레이블 (algorithm.py로 대체됨)
__pycache__/         ← 파이썬 캐시 (자동 생성됨)
*.pkl                ← 런타임 생성 파일
savedBlocks.xml      ← 런타임 생성 파일
```

---

## requirements.txt

> **[중요] 버전 의존성이 매우 강하다.** `>=` 같은 느슨한 지정은 위험하다. 아래 검증된 버전으로 고정한다.

```
# 검증 환경: Python 3.11.9 / Windows 11 / 2026-04-22

PyQt5==5.15.11
PyQtWebEngine==5.15.7
opencv-python==4.12.0.88
numpy==2.2.6
ultralytics==8.4.40
```

### 주요 버전 충돌 이력

| 패키지 쌍 | 충돌 내용 |
|---|---|
| `PyQt5` ↔ `PyQtWebEngine` | 마이너 버전 불일치 시 런처 실행 불가. **5.15.x 끼리만 호환** |
| `numpy 2.x` ↔ `opencv` | numpy 2.0에서 C API 변경. 구버전 opencv와 충돌 가능 |
| `ultralytics` ↔ `torch` | ultralytics가 호환 torch 자동 설치. 임의로 torch 버전 변경 금지 |
| `PyQt5` ↔ `Python 3.12+` | 3.12에서 PyQt5 5.15 wheel 미제공 케이스 있음 → **Python 3.11 권장** |
| `PyQt5(QtWebEngine)` ↔ `torch` | DLL 초기화 순서 충돌. main.py 최상단에서 torch(YOLO) 먼저 로드해야 함 |

> `ultralytics`는 PyTorch를 자동으로 설치한다. `torch`는 requirements.txt에 명시하지 않는다.
> `yolo_model.pt` 파일이 없으면 YOLO 추론 없이 실행된다 (기존 알고리즘 유지).

### 플랫폼별 설치 명령

#### Windows

```bash
python -m pip install -r requirements.txt
```

#### Mac (Apple Silicon / Intel)

```bash
pip3 install -r requirements.txt
```

Mac에서는 `PyQtWebEngine` 설치 시 추가 의존성이 필요할 수 있다:

```bash
brew install qt@5   # Homebrew로 Qt5 설치 (필요 시)
pip3 install -r requirements.txt
```

---

## 설치 및 실행 절차 (사용자 안내)

### 사전 조건

- Python 3.9 ~ 3.11 (3.12+ 에서 일부 패키지 미지원 가능)
- pip (Python 기본 포함)

### Windows

```bash
# 1. 소스 압축 해제
# 2. 터미널(PowerShell)에서 해당 폴더로 이동
cd waffleLauncher

# 3. 의존 패키지 설치
pip install -r requirements.txt

# 4. 실행
python main.py
```

### Mac

```bash
# 1. 소스 압축 해제
# 2. 터미널에서 해당 폴더로 이동
cd waffleLauncher

# 3. 의존 패키지 설치
pip3 install -r requirements.txt

# 4. 실행
python3 main.py
```

---

## 플랫폼별 주의사항

### Windows 특이사항

- **DLL 초기화 순서**: PyTorch(YOLO)는 반드시 PyQt5보다 **먼저** import해야 한다.
  - `main.py` 최상단에서 `yolo_model.pt` 로드 → PyQt5 import 순서 유지 필수
  - 임의로 import 순서 변경 금지
- **Python 경로에 한글 포함 금지**: TF/ONNX 변환 시 한글 경로 오류 발생 이력 있음 (현재 YOLOv11 사용으로 해당 없음)

### Mac 특이사항

- `PyQtWebEngine` 이 Windows용 바이너리로 빌드된 경우 Mac에서 재설치 필요
- Apple Silicon(M1/M2/M3)에서 PyTorch CPU 버전 자동 설치됨 → GPU 사용 불가 (추론 속도 영향 없음, YOLOv11n은 CPU에서도 실시간)
- 카메라 접근 권한: `시스템 환경설정 → 보안 및 개인 정보 → 카메라 → Terminal 허용`
- MJPEG 스트리밍 IP(`192.168.3.1`) 접속 시 Mac 방화벽 확인

### 공통

- Python 3.12+ 에서 `PyQt5` 설치 문제 발생 시 → Python 3.10 또는 3.11 사용
- `ultralytics` 설치 후 첫 실행 시 YOLOv11 기반 파일 자동 다운로드 (~6MB) 발생할 수 있음

---

## 배포 파일 생성 방법 (배포자 작업)

### 방법 1 — 수동 압축

1. `waffleLauncher_full/` 에서 필수 파일만 새 폴더 `waffleLauncher/` 로 복사
2. ZIP 압축: `waffleLauncher.zip` (수 MB)
3. `requirements.txt` 포함 확인

### 방법 2 — .gitignore 기반 Git 배포 (권장)

`.gitignore` 파일 생성:

```gitignore
# 빌드 결과물
dist/
build/
*.spec

# 대용량 데이터
savedImage/
coco/
darknet-master/
copy/
src/

# 구버전 모델
keras_model.h5
keras_model.onnx
labels.txt

# 런타임 생성 파일
__pycache__/
*.pkl
savedBlocks.xml
*.pyc

# YOLO 모델 (팀별 학습)
yolo_model.pt
```

Git 저장소에 push하면 자동으로 대용량 파일이 제외된다.
사용자는 `git clone` 후 `pip install -r requirements.txt` 만 실행하면 된다.

---

## YOLO 모델 배포 방법

`yolo_model.pt` 는 학습 결과물이므로 별도로 배포:

```
옵션 1: Google Drive / OneDrive 링크로 공유
옵션 2: Roboflow → Deploy → 다운로드 링크 제공
옵션 3: Git LFS (대용량 파일 Git 관리, 설정 복잡)
```

모델이 없어도 `main.py` 는 실행된다:
```
[YOLO] yolo_model.pt 없음 → YOLO 추론 없이 실행
```

---

## 버전 관리 권장 구조

```
waffleLauncher/        ← Git 저장소 루트
├── .gitignore
├── requirements.txt
├── README.md
├── main.py
├── algorithm.py       ← 팀별 수정
└── ...
```

팀별로 `algorithm.py` 를 수정해서 커밋 → 알고리즘 비교/관리 가능.

---

## 요약

| 현재 | 목표 |
|---|---|
| 전체 폴더 압축 (4.8GB) | 소스만 압축 (수 MB) |
| 패키지 포함 배포 | requirements.txt로 사용자 직접 설치 |
| Windows 전용 | Windows + Mac 지원 |
| 수동 패키지 관리 | pip install -r 한 줄로 완료 |

---

## 관련 문서

- [[202604211000-wafflelauncher-setup]] — 환경 설정 상세
- [[202604211031-yolov8-model-guide]] — YOLO 모델 학습 및 교체
- [[202604211001-wafflelauncher-full-analysis]] — 전체 시스템 분석
