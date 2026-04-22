# YOLOv8 모델 학습 및 교체 가이드

## 모델 파일 형식

| 형식 | 확장자 | 설명 |
|---|---|---|
| PyTorch (기본) | `.pt` | YOLOv8 기본 저장 형식. 학습 결과물. **waffleLauncher에서 이 형식 사용** |
| ONNX | `.onnx` | 크로스플랫폼 변환 포맷 (선택사항) |
| TFLite | `.tflite` | 임베디드 기기용 (선택사항) |

**waffleLauncher는 `.pt` 파일만 지원한다.** 다른 형식은 변환 불필요.

---

## 전체 흐름

```
1. 데이터 수집 (waffleLauncher 녹화 기능)
        ↓
2. 이미지 레이블링 (Roboflow / LabelImg)
        ↓
3. YOLOv8 학습 (Python 스크립트)
        ↓
4. best.pt → yolo_model.pt 으로 복사 (프로젝트 루트)
        ↓
5. algorithm.py 클래스명 수정 (학습한 클래스와 일치)
        ↓
6. main.py 실행 → 자동 로드
```

---

## STEP 1 — 데이터 수집

waffleLauncher의 **"시뮬레이션 데이터 녹화"** 버튼으로 주행 영상을 수집한다.

저장 위치: `waffleLauncher_full/savedImage/`
파일명 형식: `<frame>-<lidar>.jpg` (예: `0001-0120.jpg`)

**권장 수집량**: 클래스당 최소 100장 이상 (다양한 조명/거리/각도)

---

## STEP 2 — 레이블링

### 도구 선택

| 도구 | 방법 | 특징 |
|---|---|---|
| **Roboflow** (권장) | 웹 업로드 | 자동 증강, YOLO 포맷 내보내기, 무료 플랜 |
| LabelImg | 로컬 실행 | 오프라인, 설치 필요 |

### Roboflow 사용법

1. [roboflow.com](https://roboflow.com) 회원가입
2. New Project → Object Detection
3. 이미지 업로드 (`savedImage/*.jpg`)
4. 각 이미지에 바운딩 박스 그리기 + 클래스명 입력
5. Export → YOLOv8 포맷 → Download ZIP

### 클래스 정의 예시

```
slow    → 서행 표지판/신호
stop    → 정지 표지판/신호
track   → 주행 가능 구간
```

> 클래스명은 영문 소문자 권장. 나중에 algorithm.py에서 동일하게 사용.

---

## STEP 3 — YOLOv8 학습

### 데이터셋 구조 (Roboflow 내보내기 결과물)

```
dataset/
├── data.yaml
├── images/
│   ├── train/   (학습 이미지)
│   └── val/     (검증 이미지)
└── labels/
    ├── train/   (YOLO TXT 레이블)
    └── val/
```

### data.yaml 예시

```yaml
path: ./dataset
train: images/train
val: images/val

nc: 3
names:
  0: slow
  1: stop
  2: track
```

### 학습 스크립트

```python
from ultralytics import YOLO

model = YOLO('yolov8n.pt')  # 사전학습 모델 (자동 다운로드)

results = model.train(
    data='dataset/data.yaml',
    epochs=100,
    imgsz=640,
    batch=16,
    device=0,          # GPU: 0, CPU: 'cpu'
    project='runs/train',
    name='wafflecar_v1'
)

print('학습 완료!')
print('모델 저장 위치: runs/train/wafflecar_v1/weights/best.pt')
```

실행:
```bash
cd waffleLauncher_full
python train.py
```

### 모델 크기 선택 (yolov8n / s / m / l)

| 모델 | 크기 | 추천 상황 |
|---|---|---|
| `yolov8n.pt` | 6MB | 실시간 빠른 추론 (권장) |
| `yolov8s.pt` | 22MB | 정확도 더 높게 |
| `yolov8m.pt` | 52MB | 충분한 GPU 있을 때 |

---

## STEP 4 — 모델 교체 (핵심)

### 방법: best.pt → yolo_model.pt 복사

```bash
# Windows 명령 프롬프트
copy "runs\train\wafflecar_v1\weights\best.pt" "yolo_model.pt"
```

또는 파일 탐색기에서:
```
runs/train/wafflecar_v1/weights/best.pt
        → waffleLauncher_full/yolo_model.pt  (복사 + 이름 변경)
```

**이것이 전부다.** main.py는 시작할 때 `yolo_model.pt`를 자동으로 로드한다.

```
[YOLO] 모델 로드 완료: C:\...\yolo_model.pt   ← 정상 로드 확인 메시지
```

---

## STEP 5 — algorithm.py 클래스명 수정

학습한 클래스명과 algorithm.py의 분기문을 일치시킨다.

```python
# algorithm.py
if yolo_detections:
    top_class = yolo_detections[0]['class']

    # ↓ 여기의 클래스명을 data.yaml names 와 동일하게 작성
    if top_class == 'slow':          # data.yaml의 0번 클래스
        command = 'H,F1,F1,150,E'
    elif top_class == 'stop':        # data.yaml의 1번 클래스
        command = 'H,F0,F0,150,E'
    elif top_class == 'track':       # data.yaml의 2번 클래스
        command = 'H,F3,F3,150,E'
```

> **클래스명 불일치 주의**: data.yaml에서 `Slow` (대문자)로 정의했으면
> algorithm.py에서도 `'Slow'`로 써야 한다.

---

## STEP 6 — 동작 확인

```bash
python main.py
```

1. `[YOLO] 모델 로드 완료` 메시지 확인
2. 와플카 연결 → 카메라 스트리밍 시작
3. 화면 좌상단에 탐지 클래스명 + 신뢰도 표시됨

---

## 모델 버전 관리

여러 학습 결과를 보관하고 싶으면 파일명을 바꿔 보관:

```
yolo_model.pt          ← 현재 사용 중 (main.py가 읽는 파일)
yolo_model_v1.pt       ← v1 보관
yolo_model_v2.pt       ← v2 보관
```

교체할 때는 원하는 버전을 `yolo_model.pt`로 복사하면 된다.

---

## 요약

| 단계 | 작업 |
|---|---|
| 수집 | waffleLauncher 녹화 → `savedImage/` |
| 레이블 | Roboflow 또는 LabelImg로 바운딩 박스 |
| 학습 | `python train.py` → `runs/train/.../best.pt` |
| 교체 | `best.pt` → `yolo_model.pt` 복사 |
| 클래스 | `algorithm.py` 분기문 클래스명 수정 |
| 실행 | `python main.py` → 자동 로드 |

---

## 관련 문서

- [[202604211030-yolov8-integration]] — 통합 아키텍처 설계
- [[202604211002-yolov8-training]] — 학습 파라미터 상세
- [[202604211001-wafflelauncher-full-analysis]] — 전체 시스템 분석
