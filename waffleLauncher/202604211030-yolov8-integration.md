# YOLOv8 통합 설계 — waffleLauncher

## 개요

기존 Keras/TensorFlow 기반 분류 모델을 **YOLOv8 객체 탐지**로 교체한다.
탐지는 `main.py`에서 수행하고, 결과를 `yolo_detections` 파라미터로 `algorithm.py`에 전달하여 **탐지와 주행 결정을 분리**한다.

---

## 아키텍처

```
main.py: imageProcessing()
    ├── 기존: 카메라 → 왜곡보정 → ROI → Canny → Hough → 접촉점 추출
    ├── 추가: undist_image → YOLO 추론 → yolo_detections 리스트 생성
    └── autoDrive_algorithm(..., yolo_detections) 호출
                │
                ▼
        algorithm.py: autoDrive_algorithm()
            ├── yolo_detections[0]['class'] 참조
            └── 명령 문자열 반환
```

---

## 변경된 파일

### main.py

#### 1. `__init__()` — YOLO 모델 로드

```python
self.userAlgorithm = None   # attribute 오류 방지용 초기화 추가

# YOLO 모델 로드 (yolo_model.pt 가 있을 때만)
self.yolo_model = None
yolo_model_path = os.path.join(os.getcwd(), 'yolo_model.pt')
if os.path.exists(yolo_model_path):
    from ultralytics import YOLO
    self.yolo_model = YOLO(yolo_model_path)
```

> 모델 파일명: **`yolo_model.pt`** (프로젝트 루트에 배치)
> 파일이 없으면 YOLO 추론 없이 그대로 동작 (기존 알고리즘 유지)

#### 2. `imageProcessing()` — YOLO 추론 및 파라미터 전달

```python
# YOLO 탐지 (confidence 내림차순 정렬)
yolo_detections = []
if self.yolo_model is not None:
    yolo_results = self.yolo_model(undist_image, verbose=False)
    if len(yolo_results[0].boxes) > 0:
        for box in sorted(yolo_results[0].boxes,
                          key=lambda b: float(b.conf), reverse=True):
            yolo_detections.append({
                'class': yolo_results[0].names[int(box.cls)],
                'confidence': float(box.conf)
            })

# 알고리즘 호출 (yolo_detections 추가)
self.command, self.status = self.userAlgorithm.autoDrive_algorithm(
    undist_image, canny_img,
    H1LD, H1RD, H2LD, H2RD, H3LD, H3RD,
    V1D, V2D, V3D, V4D, V5D, V6D, V7D,
    leftLane, rightLane, frontLane,
    LiDAR, self.command, self.status,
    yolo_detections          # ← 새로 추가된 파라미터
)
```

---

### algorithm.py — 새 함수 시그니처

```python
def autoDrive_algorithm(
    original_img, canny_img,
    H1LD, H1RD, H2LD, H2RD, H3LD, H3RD,
    V1D, V2D, V3D, V4D, V5D, V6D, V7D,
    leftLane, rightLane, frontLane,
    LiDAR, prevComm, status,
    yolo_detections=None    # ← 새로 추가 (기본값 None으로 하위 호환 유지)
):
```

#### yolo_detections 구조

```python
# 탐지된 경우 (confidence 내림차순)
yolo_detections = [
    {'class': 'slow',  'confidence': 0.92},
    {'class': 'track', 'confidence': 0.41},
]

# 탐지 없음
yolo_detections = []

# YOLO 모델 미사용 (yolo_model.pt 없음)
yolo_detections = None  # → 코드 내에서 []로 처리됨
```

#### 사용 예시

```python
if yolo_detections:
    top_class = yolo_detections[0]['class']
    top_conf  = yolo_detections[0]['confidence']

    if top_class == 'slow':
        command = 'H,F1,F1,150,E'
    elif top_class == 'stop':
        command = 'H,F0,F0,150,E'
    elif top_class == 'track':
        command = 'H,F3,F3,150,E'

# LiDAR 장애물 회피 (항상 우선)
if LiDAR > 0 and LiDAR < 200:
    command = 'H,F0,F0,150,E'
```

---

## YOLOv8 모델 적용 방법

### 1. 모델 학습 후 파일 복사

```bash
# 학습 완료 후 best.pt를 프로젝트 루트에 복사
copy runs\train\wafflecar_v1\weights\best.pt waffleLauncher_full\yolo_model.pt
```

### 2. labels.txt 대응

YOLOv8 클래스 이름은 `data.yaml`에서 정의한 `names`를 사용한다.
`algorithm.py`의 클래스 분기문과 일치시켜야 한다.

```yaml
# data.yaml 예시
names:
  0: slow
  1: stop
  2: track
```

```python
# algorithm.py에서 동일한 이름 사용
if top_class == 'slow':   ...
elif top_class == 'stop': ...
elif top_class == 'track': ...
```

### 3. 실행 확인

```
[YOLO] 모델 로드 완료: C:\...\yolo_model.pt   ← 이 메시지가 나오면 정상
```

---

## 기존 구조 대비 변경점 요약

| 항목 | 기존 (Keras) | 변경 후 (YOLOv8) |
|---|---|---|
| 탐지 위치 | `algorithm.py` 내부 | `main.py` (`imageProcessing`) |
| 모델 로딩 | `algorithm.py` 첫 호출 시 | `main.py` `__init__` |
| 결과 전달 | 없음 (algorithm 내부 처리) | `yolo_detections` 파라미터 |
| 의존 패키지 | `tensorflow` / `onnxruntime` | `ultralytics` |
| DLL 충돌 | 있음 (TF + Qt) | 없음 (PyTorch는 충돌 없음) |

---

## 관련 문서

- [[202604211002-yolov8-training]] — 모델 학습 방법
- [[202604211020-keras-model-pipeline]] — 기존 Keras 추론 파이프라인
- [[202604211010-algorithm-error-fix]] — 오류 해결 이력
