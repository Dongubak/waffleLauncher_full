"""
H-mode command parser with flexible delimiter and case support.

H-mode format: H, <right_motor>, <left_motor>, <angle>, E
  - right_motor / left_motor : F1~F3 (forward) or B1~B3 (backward)
  - angle                    : integer (e.g. 150)

Supported delimiters: comma(','), space(' '), or mixed
Supported case: uppercase / lowercase / mixed
"""

import re


# ──────────────────────────────────────────
# 함수 1: 구분자로 토큰 분리
# ──────────────────────────────────────────
def split_command(data: str) -> list[str]:
    """
    쉼표 또는 스페이스(연속 포함)를 구분자로 토큰을 분리한다.
    빈 토큰은 제거한다.

    예시:
        'H,F3,F3,150,E'      -> ['H', 'F3', 'F3', '150', 'E'] 
        ' H, F3, F3, 150, E' -> ['H', 'F3', 'F3', '150', 'E']
        'H F3 F3 150 E'      -> ['H', 'F3', 'F3', '150', 'E']
        'H, F3  F3 150,E'    -> ['H', 'F3', 'F3', '150', 'E']
    """
    tokens = re.split(r'[,\s]+', data.strip())
    return [t for t in tokens if t]


# ──────────────────────────────────────────
# 함수 2: 토큰 정규화 (대문자 변환)
# ──────────────────────────────────────────
def normalize_tokens(tokens: list[str]) -> list[str]:
    """
    모든 토큰을 대문자로 변환한다.
    숫자만 있는 토큰은 변환해도 무관하다.

    예시:
        ['h', 'f3', 'F3', '150', 'e'] -> ['H', 'F3', 'F3', '150', 'E']
    """
    return [t.upper() for t in tokens]


# ──────────────────────────────────────────
# 함수 3: H-mode 커맨드 파싱
# ──────────────────────────────────────────
def parse_h_command(data: str) -> dict | None:
    """
    H-mode 커맨드 문자열을 파싱해 dict로 반환한다.
    유효하지 않은 커맨드면 None을 반환한다.

    반환 형식:
        {
            'type'        : 'H',
            'right_motor' : 'F3',   # F1~F3 or B1~B3
            'left_motor'  : 'F3',
            'angle'       : 150,    # int
        }
    """
    tokens = normalize_tokens(split_command(data))

    if len(tokens) != 5:
        return None
    if tokens[0] != 'H' or tokens[4] != 'E':
        return None

    right_motor = tokens[1]
    left_motor  = tokens[2]
    angle_str   = tokens[3]

    # 모터 토큰 검증: F1~F3 또는 B1~B3
    motor_pattern = re.compile(r'^[FB][123]$')
    if not motor_pattern.match(right_motor):
        return None
    if not motor_pattern.match(left_motor):
        return None

    # 각도 검증: 정수여야 함
    if not angle_str.lstrip('-').isdigit():
        return None

    return {
        'type'       : 'H',
        'right_motor': right_motor,
        'left_motor' : left_motor,
        'angle'      : int(angle_str),
    }


# ══════════════════════════════════════════
# 테스트 케이스
# ══════════════════════════════════════════
import unittest

class TestSplitCommand(unittest.TestCase):
    """split_command 단위 테스트"""

    def test_comma_only(self):
        self.assertEqual(split_command('H,F3,F3,150,E'), ['H', 'F3', 'F3', '150', 'E'])

    def test_comma_with_spaces(self):
        self.assertEqual(split_command(' H, F3, F3, 150, E'), ['H', 'F3', 'F3', '150', 'E'])

    def test_mixed_spacing(self):
        self.assertEqual(split_command('H,F3, F3,150,E'), ['H', 'F3', 'F3', '150', 'E'])

    def test_space_only(self):
        self.assertEqual(split_command('H F3 F3 150 E'), ['H', 'F3', 'F3', '150', 'E'])

    def test_multiple_spaces(self):
        self.assertEqual(split_command('H  F3  F3  150  E'), ['H', 'F3', 'F3', '150', 'E'])

    def test_mixed_comma_and_space(self):
        self.assertEqual(split_command('H, F3 F3, 150 E'), ['H', 'F3', 'F3', '150', 'E'])


class TestNormalizeTokens(unittest.TestCase):
    """normalize_tokens 단위 테스트"""

    def test_all_lowercase(self):
        self.assertEqual(normalize_tokens(['h', 'f3', 'f3', '150', 'e']),
                         ['H', 'F3', 'F3', '150', 'E'])

    def test_mixed_case(self):
        self.assertEqual(normalize_tokens(['h', 'f3', 'F3', '150', 'E']),
                         ['H', 'F3', 'F3', '150', 'E'])

    def test_already_upper(self):
        self.assertEqual(normalize_tokens(['H', 'F3', 'F3', '150', 'E']),
                         ['H', 'F3', 'F3', '150', 'E'])


class TestParseHCommand(unittest.TestCase):
    """parse_h_command 통합 테스트"""

    # ── 정상 케이스 ──────────────────────
    def test_standard(self):
        result = parse_h_command('H,F3,F3,150,E')
        self.assertEqual(result, {'type': 'H', 'right_motor': 'F3', 'left_motor': 'F3', 'angle': 150})

    def test_spaces_around_commas(self):
        result = parse_h_command(' H, F3, F3, 150, E')
        self.assertEqual(result, {'type': 'H', 'right_motor': 'F3', 'left_motor': 'F3', 'angle': 150})

    def test_mixed_spacing(self):
        result = parse_h_command('H,F3, F3,150,E')
        self.assertEqual(result, {'type': 'H', 'right_motor': 'F3', 'left_motor': 'F3', 'angle': 150})

    def test_lowercase(self):
        result = parse_h_command('h,f3,F3,150,E')
        self.assertEqual(result, {'type': 'H', 'right_motor': 'F3', 'left_motor': 'F3', 'angle': 150})

    def test_space_delimiter(self):
        result = parse_h_command('H F3 F3 150 E')
        self.assertEqual(result, {'type': 'H', 'right_motor': 'F3', 'left_motor': 'F3', 'angle': 150})

    def test_backward_motor(self):
        result = parse_h_command('H,B2,B2,160,E')
        self.assertEqual(result, {'type': 'H', 'right_motor': 'B2', 'left_motor': 'B2', 'angle': 160})

    def test_asymmetric_motors(self):
        result = parse_h_command('H,F1,B3,145,E')
        self.assertEqual(result, {'type': 'H', 'right_motor': 'F1', 'left_motor': 'B3', 'angle': 145})

    # ── 비정상 케이스 (None 반환) ─────────
    def test_missing_end_marker(self):
        self.assertIsNone(parse_h_command('H,F3,F3,150'))

    def test_wrong_type(self):
        self.assertIsNone(parse_h_command('L,F3,F3,150,E'))

    def test_invalid_motor_token(self):
        self.assertIsNone(parse_h_command('H,F4,F3,150,E'))   # F4 는 없음

    def test_non_integer_angle(self):
        self.assertIsNone(parse_h_command('H,F3,F3,abc,E'))

    def test_empty_string(self):
        self.assertIsNone(parse_h_command(''))


if __name__ == '__main__':
    unittest.main(verbosity=2)
