# algorithm.py 오류 원인 및 수정 기록

## 증상

`main.py` 실행 후 GUI에 다음 메시지 출력:
```
algorithm.py 파일에 오류가 있습니다. 자세한 내용은 프롬프트창을 확인해주세요.
```

---

## 원인 분석

`main.py`의 `setAlgorithm()` 함수에서 `importlib.import_module('algorithm')`을 호출할 때 예외가 발생한다.

```python
# main.py:setAlgorithm()
try:
    self.userAlgorithm = importlib.import_module('algorithm')
except Exception as e:
    self.textBrowser.append('algorithm.py 파일에 오류가 있습니다...')
```

### 오류 1 — tensorflow 미설치

```
ModuleNotFoundError: No module named 'tensorflow'
```

- **위치**: `algorithm.py:2` — `import tensorflow`
- **원인**: `tensorflow` 패키지가 설치되지 않은 환경

### 오류 2 — Image.ANTIALIAS 제거됨

```
AttributeError: module 'PIL.Image' has no attribute 'ANTIALIAS'
```

- **위치**: `algorithm.py:48` — `ImageOps.fit(image, size, Image.ANTIALIAS)`
- **원인**: Pillow 10.0.0에서 `Image.ANTIALIAS`가 공식 제거됨
  - Pillow 9.x: deprecated 경고
  - Pillow 10.0+: 완전 제거
  - 현재 설치된 Pillow: **12.2.0** → 해당 없음

---

## 수정 내용

### 1. tensorflow 설치

```bash
pip install tensorflow Pillow
```

설치된 버전:
- `tensorflow 2.21.0`
- `Pillow 12.2.0` (이미 설치됨)

### 2. algorithm.py 코드 수정

[algorithm.py:48](../../../바탕 화면/waffleLauncher_full/algorithm.py)

```diff
- image = ImageOps.fit(image, size, Image.ANTIALIAS)
+ image = ImageOps.fit(image, size, Image.LANCZOS)
```

`Image.LANCZOS`는 `Image.ANTIALIAS`와 동일한 고품질 다운샘플링 필터다.

---

### 3. TF DLL 충돌 — tensorflow import 지연 로딩으로 수정

```
[TensorFlow DLL Diagnostic]
[Error] Failed to load _pywrap_tensorflow_common.dll: INITIALIZATION FAILED (0x45A)
```

- **환경**: `python .\main.py` 실행 시 발생
- **원인**: PyQt5 + QtWebEngine이 먼저 DLL을 점유한 상태에서 모듈 레벨 `import tensorflow`가 실행되면 DLL 초기화 순서 충돌 발생
- **CPU**: i7-11850H (AVX2 지원) → CPU 문제 아님

**수정**: module 최상단의 `import tensorflow` 제거 → 함수 내 초기화 블록으로 이동 (지연 로딩)

```diff
- # 파일 최상단
- import tensorflow

  def autoDrive_algorithm(...):
      if status == 1:  # initialization
+         import tensorflow   ← 실제 사용 시점에만 로드
          model = tensorflow.keras.models.load_model('keras_model.h5')
```

---

## 수정 후 검증

```bash
cd waffleLauncher_full
python -c "import algorithm; print('OK')"
```

출력:
```
OK
```

> oneDNN 관련 `I0000` 로그는 TensorFlow 정보 메시지이며 오류가 아니다.
> 억제하려면: `set TF_ENABLE_ONEDNN_OPTS=0` 환경변수 설정

---

## 전체 의존 패키지 현황

| 패키지 | 버전 | 상태 |
|---|---|---|
| `PyQt5` | 5.15.11 | 정상 |
| `PyQtWebEngine` | — | 별도 설치 필요 (`pip install PyQtWebEngine`) |
| `opencv-python` | 4.12.0 | 정상 |
| `numpy` | 2.2.6 | 정상 |
| `Pillow` | 12.2.0 | 정상 |
| `tensorflow` | 2.21.0 | 설치 완료 |

---

---

## 오류 4 — TF DLL + PyQt5 충돌 → ONNX 변환으로 완전 해결

### 증상

```
[Error] Failed to load _pywrap_tensorflow_common.dll: INITIALIZATION FAILED (0x45A)
ImportError: DLL load failed while importing _pywrap_tensorflow_internal
```

- **환경**: `main.py` (PyQt5 + QtWebEngine) 실행 시
- **원인**: QtWebEngine이 먼저 DLL을 점유한 상태에서 TF DLL 초기화 충돌 → CPU(i7-11850H)의 AVX 지원 여부와 무관

### 추가 시도 — 지연 로딩

`import tensorflow`를 함수 내부로 이동 → 여전히 같은 DLL 충돌 발생.

### 최종 해결 — ONNX Runtime 교체

TF는 PyQt5+QtWebEngine 환경에서 근본적으로 사용 불가.
`keras_model.h5`를 ONNX 포맷으로 변환하고 `onnxruntime`으로 대체.

#### 설치

```bash
pip install tf2onnx onnxruntime tf-keras
```

#### 변환 (주의: 경로에 한글 불가 → 임시 경로 사용)

```python
# 한글 경로 문제 우회: 임시 경로에서 변환
import os
os.environ['TF_USE_LEGACY_KERAS'] = '1'
import tf_keras as keras
from tf_keras.layers import DepthwiseConv2D

class FixedDepthwiseConv2D(DepthwiseConv2D):
    @classmethod
    def from_config(cls, config):
        config.pop('groups', None)   # Keras 3.x 호환 패치
        return super().from_config(config)

model = keras.models.load_model(
    'keras_model.h5',
    custom_objects={'DepthwiseConv2D': FixedDepthwiseConv2D}
)
# 모델 정보: Input (None,224,224,3) → Output (None,5)

import tf2onnx, onnx, tensorflow as tf
input_sig = (tf.TensorSpec(model.input_shape, tf.float32, name='input'),)
model_proto, _ = tf2onnx.convert.from_keras(model, input_signature=input_sig, opset=13)
onnx.save(model_proto, 'keras_model.onnx')
```

**변환 시 발생한 추가 오류**:
- `ValueError: DepthwiseConv2D: {'groups': 1}` — Keras 3.x vs Teachable Machine 모델 API 불일치. `FixedDepthwiseConv2D`로 `groups` 파라미터 제거.
- `UnicodeDecodeError` — 경로의 한글(`바탕 화면`) 때문. `c:/tmp/waffleconv/` 임시 경로 사용.

#### algorithm.py 변경 (최종)

```diff
- import tensorflow
- from PIL import Image, ImageOps
+ from PIL import Image, ImageOps
+ import onnxruntime as ort

  def autoDrive_algorithm(...):
      if status == 1:
-         model = tensorflow.keras.models.load_model('keras_model.h5')
+         session = ort.InferenceSession('keras_model.onnx', providers=['CPUExecutionProvider'])
+         input_name = session.get_inputs()[0].name

-     prediction = model.predict(data)[0].tolist()
+     prediction = session.run(None, {input_name: data})[0][0].tolist()
```

---

## 향후 계획

현재 `algorithm.py`는 `keras_model.onnx` (Teachable Machine 변환 모델)를 사용한다.
기존 코드 동작 확인 후 **YOLOv8로 교체** 예정.

→ [[202604211002-yolov8-training]]

---

## 관련 문서

- [[202604211000-wafflelauncher-setup]] — 환경 설정
- [[202604211001-wafflelauncher-full-analysis]] — 전체 분석
