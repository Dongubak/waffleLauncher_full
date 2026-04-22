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
    yolo_detections: YOLOv8 탐지 결과 리스트 (main.py에서 전달)
                     [{'class': 'Slowly', 'confidence': 0.92}, ...]
                     탐지 없음 = [] / YOLO 미사용 = None

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
    # yolo_detections는 confidence 내림차순 정렬된 리스트
    # ──────────────────────────────────────────────────
    if yolo_detections:
        top = yolo_detections[0]
        top_class = top['class']
        top_conf  = top['confidence']

        # 터미널 출력
        print('[YOLO] 탐지: %s (%.1f%%)' % (top_class, top_conf * 100))

        # 화면에 탐지 결과 표시
        label = '%s %.0f%%' % (top_class, top_conf * 100)
        cv2.putText(original_img, label, (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

        # ── 여기에 클래스별 주행 명령을 작성하세요 ──
        # 현재 클래스: 'circle of blue', 'circle of red'
        if top_class == 'circle of blue':
            pass  # 명령 미정 (prevComm 유지)
        elif top_class == 'circle of red':
            pass  # 명령 미정 (prevComm 유지)

    else:
        print('[YOLO] 탐지 없음')

    # ──────────────────────────────────────────────────
    # LiDAR 장애물 회피 (거리 200mm 미만 → 강제 정지)
    # ──────────────────────────────────────────────────
    if LiDAR > 0 and LiDAR < 200:
        command = 'H,F0,F0,150,E'

    print('[상태] LiDAR=%d H2LD=%s H2RD=%s' % (LiDAR, H2LD, H2RD))
    return command, status
