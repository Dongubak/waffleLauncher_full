# Keras 모델 추론 파이프라인 분석

> YOLOv8 마이그레이션 시 기존 코드 이해를 위한 참고 문서

---

## 모델 정보

| 항목 | 내용 |
|---|---|
| 원본 파일 | `keras_model.h5` |
| 변환 파일 | `keras_model.onnx` |
| 아키텍처 | MobileNet 기반 (DepthwiseConv2D 포함) |
| 학습 도구 | Google Teachable Machine |
| 입력 크기 | `(1, 224, 224, 3)` — 배치 1, 224×224 RGB |
| 출력 크기 | `(1, 5)` — 5개 클래스 확률 |

### 클래스 정의 (`labels.txt`)

| ID | 클래스명 | 의미 (추정) |
|---|---|---|
| 0 | Bohang | 보행자 구간 |
| 1 | Slowly | 서행 |
| 2 | Stopoo | 정지 |
| 3 | Gongsa | 공사 구간 |
| 4 | Driver | 주행 가능 |

---

## 추론 흐름 (algorithm.py)

### 1단계 — 초기화 (`status == 1` 일 때)

```python
# ONNX 세션 생성 (TF 대체)
session = ort.InferenceSession('keras_model.onnx', providers=['CPUExecutionProvider'])
input_name = session.get_inputs()[0].name   # 'input'

# 레이블 로드
names = {0: 'Bohang', 1: 'Slowly', 2: 'Stopoo', 3: 'Gongsa', 4: 'Driver'}

# 입력 배열 초기화
data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)

# 상태를 리스트로 저장 (다음 프레임에서 재사용)
status = [session, input_name, names, data, driving_stage]
```

> `autoDrive_algorithm()`은 매 프레임마다 호출된다. `status == 1`은 첫 호출만 해당.
> 이후에는 `status` 리스트에서 session 등을 꺼내 재사용한다.

### 2단계 — 이미지 전처리

```python
img = original_img  # BGR 형식 (OpenCV 기본)

# BGR → RGB 변환 (Teachable Machine은 RGB 학습)
cv2img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
image = Image.fromarray(cv2img)

# 224×224로 크롭+리사이즈
# ImageOps.fit: 이미지 비율 유지하며 중앙 크롭 후 지정 크기로 리사이즈
size = (224, 224)
image = ImageOps.fit(image, size, Image.LANCZOS)
# LANCZOS: Pillow 10+ 에서 ANTIALIAS 대체. 동일한 고품질 다운샘플링 필터.

# numpy 배열 변환
image_array = np.asarray(image)   # shape: (224, 224, 3), dtype: uint8
```

### 3단계 — 정규화

```python
# Teachable Machine 기본 정규화: [0, 255] → [-1, 1]
normalized_image_array = (image_array.astype(np.float32) / 127.0) - 1
# 0 → -1.0, 127 → 0.0, 255 → +1.0

data[0] = normalized_image_array   # shape: (1, 224, 224, 3)
```

> YOLOv8 전환 시 주의: YOLOv8은 `[0, 1]` 정규화 사용.
> `image / 255.0` 방식으로 변경 필요.

### 4단계 — 추론

```python
# ONNX 추론
prediction = session.run(None, {input_name: data})[0][0].tolist()
# session.run() 반환값: [출력배열] → [0]: 첫 번째 출력 → [0]: 배치 0번째
# prediction: [0.01, 0.85, 0.02, 0.03, 0.09] 형태 (클래스별 확률)

# 가장 높은 확률의 클래스 선택
index = prediction.index(max(prediction))
# index: 1 (Slowly)
```

### 5단계 — 명령 생성

```python
cv2.putText(img, names[index], (20, 50), ...)  # 화면에 클래스 표시

if names[index] == 'Slowly':
    command = 'H,F1,F1,150,E'    # 저속 전진
elif names[index] == 'Stopoo':
    command = 'H,F0,F0,150,E'    # 정지
elif names[index] == 'Driver':
    command = 'H,F3,F3,150,E'    # 고속 전진
# Bohang, Gongsa는 명령 미정의 → prevComm 유지
```

---

## 전체 파이프라인 다이어그램

```
카메라 프레임 (BGR, 640×360)
        │
        ▼
cv2.cvtColor(BGR → RGB)
        │
        ▼
ImageOps.fit(224×224, LANCZOS 크롭+리사이즈)
        │
        ▼
np.asarray() → (224,224,3) uint8
        │
        ▼
정규화: (x / 127.0) - 1  →  [-1, 1] float32
        │
        ▼
data[0] = normalized  →  (1,224,224,3) float32
        │
        ▼
session.run(None, {input_name: data})
        │
        ▼
prediction: [p0, p1, p2, p3, p4]  (5 클래스 확률)
        │
        ▼
index = argmax(prediction)
        │
        ▼
names[index] 비교 → 명령 문자열 생성
        │
        ▼
return command, status
```

---

## YOLOv8 전환 시 변경 포인트

| 항목 | 기존 Keras | YOLOv8 |
|---|---|---|
| 모델 로드 | `ort.InferenceSession('keras_model.onnx')` | `YOLO('best.pt')` |
| 입력 크기 | 224×224 고정 | 640×640 (기본) |
| 정규화 | `(x / 127.0) - 1` (범위: -1~1) | 내부 처리 (자동) |
| 추론 호출 | `session.run(None, {input_name: data})` | `model(img, verbose=False)` |
| 출력 | 분류 확률 배열 `[p0..p4]` | 바운딩박스 + 클래스 + confidence |
| 클래스 접근 | `names[index]` (직접 레이블 딕셔너리) | `results[0].names[cls_id]` |
| 태스크 유형 | **분류 (Classification)** | **객체 탐지 (Detection)** |

### algorithm.py 수정 예시 (YOLOv8)

```python
# 초기화 블록
from ultralytics import YOLO
model = YOLO('runs/train/wafflecar_v1/weights/best.pt')
status = [model]

# 추론 블록
model = status[0]
results = model(original_img, verbose=False)

command = prevComm
if len(results[0].boxes) > 0:
    best = results[0].boxes[results[0].boxes.conf.argmax()]
    cls_name = results[0].names[int(best.cls)]
    if cls_name == 'Slowly':
        command = 'H,F1,F1,150,E'
    elif cls_name == 'Stopoo':
        command = 'H,F0,F0,150,E'
    elif cls_name == 'Driver':
        command = 'H,F3,F3,150,E'
```

---

## 관련 문서

- [[202604211010-algorithm-error-fix]] — 오류 해결 과정
- [[202604211002-yolov8-training]] — YOLOv8 학습 및 전환
- [[202604211001-wafflelauncher-full-analysis]] — 전체 시스템 분석
