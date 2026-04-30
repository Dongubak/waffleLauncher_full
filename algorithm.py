from wafflecarUtil import *


def autoDrive_algorithm(original_img, canny_img, H1LD, H1RD, H2LD, H2RD, H3LD, H3RD, V1D, V2D, V3D, V4D, V5D, V6D, V7D, leftLane, rightLane, frontLane, LiDAR, prevComm, status, yolo_detections=None):
    """
    자율주행 알고리즘

    Parameters
    ----------
    original_img   : 원본 카메라 이미지 (BGR, numpy array)
    canny_img      : Canny 처리 이미지
    H1LD ~ H3RD    : 수평 접촉점 거리 (좌/우, 3개 수평선)
    V1D ~ V7D      : 수직 접촉점 거리 (7개 수직선)
    leftLane       : 왼쪽 차선 직선 (x1,y1,x2,y2)
    rightLane      : 오른쪽 차선 직선
    frontLane      : 전방 횡단선 목록
    LiDAR          : LiDAR 거리 (mm), 0 = 감지 불가
    prevComm       : 이전 명령 문자열
    status         : 상태 (첫 호출 시 1, 이후 반환값 재사용)
    yolo_detections: YOLOv8 탐지 결과 리스트
                     [{'class': 'red_light', 'confidence': 0.95,
                       'distance_mm': 1240.0}, ...]
                     confidence 내림차순 정렬 / 탐지 없음 = []

    Returns
    -------
    command : 제어 명령 문자열
    status  : 갱신된 상태
    """
    command = prevComm

    if yolo_detections is None:
        yolo_detections = []

    # ──────────────────────────────────────────────────
    # YOLO 탐지 결과 활용
    # ──────────────────────────────────────────────────
    if yolo_detections:
        # 탐지된 객체를 화면에 그린다 (바운딩 박스 + 클래스 + 거리)
        drawYoloDetections(original_img, yolo_detections)

        # 가장 높은 confidence의 탐지 결과
        top = yolo_detections[0]
        top_class = top['class']          # 예: 'red_light'
        top_conf  = top['confidence']     # 예: 0.95  (0~1)
        top_dist  = top['distance_mm']    # 예: 1240.0 (mm), 추정 불가 시 None

        # 콘솔 출력
        dist_str = ('%.0fmm' % top_dist) if top_dist is not None else 'N/A'
        print('[YOLO] 탐지 %d건  최상위: %s  conf=%.1f%%  거리=%s' % (
            len(yolo_detections), top_class, top_conf * 100, dist_str))
        for i, det in enumerate(yolo_detections):
            d = det['distance_mm']
            print('  [%d] %s  conf=%.1f%%  거리=%s' % (
                i + 1, det['class'], det['confidence'] * 100,
                ('%.0fmm' % d) if d is not None else 'N/A'))

        # ── 여기에 클래스별 주행 명령을 작성하세요 ──────────────
        # 사용 가능한 변수:
        #   top_class  : 탐지된 클래스 이름 (문자열)
        #   top_conf   : 신뢰도 (0.0 ~ 1.0)
        #   top_dist   : 객체까지의 추정 거리 (mm), 없으면 None
        # 현재 클래스: 'STOP_SIGN', 'number_one',
        #              'green_light', 'red_light', 'yellow_light'
        if top_class == 'STOP_SIGN':
            pass  # TODO: 정지 명령 작성
        elif top_class == 'number_one':
            pass  # TODO: 속도 제한 명령 작성
        elif top_class == 'green_light':
            pass  # TODO: 전진 명령 작성
        elif top_class == 'red_light':
            pass  # TODO: 정지 명령 작성
        elif top_class == 'yellow_light':
            pass  # TODO: 감속 명령 작성

    else:
        print('[YOLO] 탐지 없음')

    # ──────────────────────────────────────────────────
    # LiDAR 장애물 회피 (거리 200mm 미만 → 강제 정지)
    # ─────────────────────────────────────────────────

    print('[상태] LiDAR=%d H2LD=%s H2RD=%s' % (LiDAR, H2LD, H2RD))
    return command, status
