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

    if leftLane and rightLane:
        if H2LD > H2RD:
            comamnd = 'H,F3,F3,110,E'
        elif H2LD < H2RD:
            command = 'H,F3,F3,190,E'
        else: # H2LD == H2RD
            command = 'H,F3,F3,150,E'

    if not rightLane:
        if 90 < V4D < 120:
            command = 'H,F3,F3,210,E'
        elif V4D < 130:
            command = 'H,F3,F3,250,E'

    # ===== DEMO VISUALIZATION START (시연용 - 실습 전 삭제) =====
    if original_img is not None:
        _, w = original_img.shape[:2]

        # 상태 표시 (좌상단)
        status_labels = {1: 'STATUS 1: LANE FOLLOW', 2: 'STATUS 2: CURVE', 3: 'STATUS 3: LANE FOLLOW', 4: 'STATUS 4: STOP'}
        status_text = status_labels.get(status, 'STATUS: %d' % status)
        (tw, th), _ = cv2.getTextSize(status_text, cv2.FONT_HERSHEY_SIMPLEX, 0.65, 2)
        cv2.rectangle(original_img, (10, 8), (14 + tw, 22 + th), (50, 50, 50), -1)
        cv2.putText(original_img, status_text, (12, 20 + th - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

        # YOLO 감지 결과 표시 (우상단, 감지된 경우에만)
        if yolo_detections:
            top_det = yolo_detections[0]
            det_text = 'DETECT: %s (%.0f%%)' % (top_det['class'], top_det['confidence'] * 100)
            (dw, dh), _ = cv2.getTextSize(det_text, cv2.FONT_HERSHEY_SIMPLEX, 0.65, 2)
            x0 = w - dw - 14
            cv2.rectangle(original_img, (x0 - 4, 8), (w - 10, 22 + dh), (0, 180, 0), -1)
            cv2.putText(original_img, det_text, (x0, 20 + dh - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 0), 2)
    # ===== DEMO VISUALIZATION END =====

    return command, status
