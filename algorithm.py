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


    return command, status
