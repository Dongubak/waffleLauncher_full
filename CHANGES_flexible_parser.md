# 유연한 커맨드 파서 도입 — 수정 내역

브랜치: `feature/flexible-parser`

---

## 배경

기존 H-mode 커맨드 파싱은 쉼표(`,`)만을 구분자로 사용하고 대소문자를 구분하는
고정 방식이었다. 이로 인해 아래 형식의 입력은 파싱 실패 또는 오동작을 유발했다.

| 입력 예시 | 기존 결과 |
|-----------|-----------|
| `' H, F3, F3, 150, E'` | `split(',')` → `[' H', ' F3', ...]` (공백 포함) |
| `'H F3 F3 150 E'` | `split(',')` → `['H F3 F3 150 E']` (토큰 1개) |
| `'h,f3,F3,150,E'` | `comm[0] == 'H'` 불일치 |

또한 **`getAlignedWheelAngle`(wafflecarUtil.py)이 소켓 전송 전에 먼저 실행**되므로,
서버 측 파서를 고쳐도 유틸 단계에서 이미 오류가 발생하는 구조적 문제가 있었다.

---

## 수정 파일 목록

### 1. `command_parser.py` (신규)

파싱 전용 모듈. 3개 함수와 테스트 클래스(28개 케이스)를 포함한다.

#### `split_command(data: str) -> list[str]`
- 쉼표 또는 공백(연속 포함)을 구분자로 토큰 분리
- 앞뒤 공백 strip, 빈 토큰 제거
- 구현: `re.split(r'[,\s]+', data.strip())`

#### `normalize_tokens(tokens: list[str]) -> list[str]`
- 모든 토큰을 대문자로 통일
- 구현: `[t.upper() for t in tokens]`

#### `parse_h_command(data: str) -> dict | None`
- 위 두 함수를 조합해 H-mode 커맨드를 `dict`로 반환
- 유효하지 않으면 `None` 반환
- 반환 예시: `{'type': 'H', 'right_motor': 'F3', 'left_motor': 'F3', 'angle': 150}`

---

### 2. `wafflecarUtil.py`

**진입점 수정** — 유연한 입력이 처음 도달하는 지점.

#### import 추가 (line 4-8)
```python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from command_parser import split_command, normalize_tokens
```

#### `getAlignedWheelAngle` H-mode 분기 수정 (line 187-190)

| | 이전 | 이후 |
|--|------|------|
| 조건 | `command[0] == 'H'` | `normalize_tokens(split_command(command))[0] == 'H'` |
| 파싱 | `com = command.split(',')` | `com = normalize_tokens(split_command(command))` |
| 각도 | `com[3] = int(com[3]) + alignAlgle` | `com[3] = str(int(com[3]) + alignAlgle)` |
| 재조합 | `'H,%s,%s,%03d,E' % (com[1], com[2], com[3])` | `'H,%s,%s,%03d,E' % (com[1], com[2], int(com[3]))` |

이후 로직(각도 적용·커맨드 재조합)은 **변경 없음**.
출력은 항상 표준 형태 `'H,F1,F1,155,E'`로 고정되므로 하위 소켓 전송 코드에 영향 없음.

---

### 3. `wafflecarServer/wafflecarServer.py`

소켓 수신 측 안전망.

#### import 추가 (line 13-14)
```python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from command_parser import split_command, normalize_tokens
```

#### H-mode 파싱 수정 (line 222)

```python
# 이전
comm = data.split(',')

# 이후
comm = normalize_tokens(split_command(data))
```

이후 `comm[0]`, `comm[1][0]`, `comm[4]` 등 인덱스 접근 로직은 **변경 없음**.

---

## 지원 입력 형식 (H-mode)

| 입력 | 처리 결과 |
|------|-----------|
| `'H,F3,F3,150,E'` | 정상 (기존과 동일) |
| `' H, F3, F3, 150, E'` | 공백 무시 후 파싱 |
| `'H,F3, F3,150,E'` | 혼합 공백 무시 |
| `'h,f3,F3,150,E'` | 소문자 → 대문자 변환 |
| `'H F3 F3 150 E'` | 공백만 구분자로 파싱 |
| `' h, f3, f3, 150, e'` | 공백·소문자 동시 처리 |

---

## 테스트

```
python command_parser.py
```

총 28개 케이스, 전부 통과.

| 테스트 클래스 | 케이스 수 | 검증 대상 |
|---------------|-----------|-----------|
| `TestSplitCommand` | 6 | 구분자 분리 함수 |
| `TestNormalizeTokens` | 3 | 대문자 변환 함수 |
| `TestParseHCommand` | 12 | 통합 파싱 함수 |
| `TestGetAlignedWheelAngleFlexible` | 7 | 유틸 함수 유연성·각도 보정 |
