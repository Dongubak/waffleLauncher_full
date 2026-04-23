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
        # 전체 탐지 결과 출력
        print('[YOLO] 탐지 %d건:' % len(yolo_detections))
        for i, det in enumerate(yolo_detections):
            print('  [%d] %s  conf=%.1f%%' % (i + 1, det['class'], det['confidence'] * 100))

        top = yolo_detections[0]
        top_class = top['class']
        top_conf  = top['confidence']

        # 화면에 1위 탐지 결과 표시
        label = '%s %.0f%%' % (top_class, top_conf * 100)
        cv2.putText(original_img, label, (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

        # ── 여기에 클래스별 주행 명령을 작성하세요 ──
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
    # ──────────────────────────────────────────────────
    

    if status == 1:
        if leftLane and rightLane: # straight
            if H3RD < H2RD and H1RD != -1: # strange line
                pass
            elif H2LD < H2RD:
                command = 'H,F3,F3,170,E'
            elif H2LD > H2RD:
                command = 'H,F3,F3,130,E'
            else:
                command = 'H,F3,F3,150,E'

        if leftLane and not rightLane:
            status = 2
    if status == 2:
        if V4D < 70:
            command = 'H,F1,F1,250,E'
        elif V4D < 105:
            command = 'H,F1,F1,220,E'
        elif V4D < 140:
            command = 'H,F1,F1,180,E'
        else:
            command = 'H,F1,F1,150,E'
        
        if leftLane and rightLane and V4D > 130:
            status = 3

    if status == 3:
        if leftLane and rightLane: # straight
            # if H3RD < H2RD and H1RD != -1:
            if H3RD < H2RD:
                pass
            elif H2LD < H2RD:
                command = 'H,F3,F3,170,E'
            elif H2LD > H2RD:
                command = 'H,F3,F3,130,E'
            else:
                command = 'H,F3,F3,150,E'

        if leftLane and not rightLane:
            status = 4
    if status == 4:
        if V4D < 70:
            command = 'H,F1,F1,250,E'
        elif V4D < 105:
            command = 'H,F1,F1,230,E'
        elif V4D < 130:
            command = 'H,F1,F1,200,E'
        else:
            command = 'H,F1,F1,150,E'
        
        
        if leftLane and rightLane and V4D > 130:
            status = 5


    if status == 5:
        if leftLane and rightLane: # straight
            if H3RD < H2RD:
                command = 'H,F3,F3,170,E'
            elif H1LD > H1RD:
                command = 'H,F3,F3,130,E'
            else:
                command = 'H,F3,F3,150,E'

        if rightLane:
            status = 6
    
    if status == 6:
        if leftLane and rightLane: # straight
            # if H3RD < H2RD and H1RD != -1:
            if V3D == -1 or V6D == -1:
                pass
            if V3D < V6D:
                command = 'H,F3,F3,170,E'
            elif V3D > V6D:
                command = 'H,F3,F3,130,E'
            else:
                command = 'H,F3,F3,150,E'

        if H3RD != -1:
            status = 7


    

    if status == 7:
        if leftLane and rightLane: # straight
            if H3RD < H2RD and H1RD != -1: # strange line
                pass
            elif H2LD < H2RD:
                command = 'H,F3,F3,170,E'
            elif H2LD > H2RD:
                command = 'H,F3,F3,130,E'
            else:
                command = 'H,F3,F3,150,E'

        if leftLane and not rightLane:
            status = 8



    if status == 8:
        # command = 'H,F0,F0,150,E'
        if V4D < 70:
            command = 'H,F1,F1,250,E'
        elif V4D < 105:
            command = 'H,F1,F1,220,E'
        elif V4D < 140:
            command = 'H,F1,F1,180,E'
        else:
            command = 'H,F1,F1,150,E'
        
        if leftLane and rightLane and V4D > 130:
            status = 9

    if status == 9:
        if leftLane and rightLane: # straight
            if H3RD < H2RD and H1RD != -1: # strange line
                pass
            elif H2LD < H2RD:
                command = 'H,F3,F3,170,E'
            elif H2LD > H2RD:
                command = 'H,F3,F3,130,E'
            else:
                command = 'H,F3,F3,150,E'

        if leftLane and not rightLane:
            status = 10


    if status == 10:
        if leftLane and rightLane: # straight
            if H2LD < H2RD:
                command = 'H,F3,F3,170,E'
            elif H2LD > H2RD:
                command = 'H,F3,F3,130,E'
            else:
                command = 'H,F3,F3,150,E'

        if leftLane and H2RD != -1 and H3RD != -1 and rightLane:
            status = 11
        
    if status == 11:
        if leftLane and rightLane: # straight
            if H3RD < H2RD and H1RD != -1:
                pass
            elif H2LD < H2RD:
                command = 'H,F3,F3,170,E'
            elif H2LD > H2RD:
                command = 'H,F3,F3,130,E'
            else:
                command = 'H,F3,F3,150,E'

        if leftLane and not rightLane:
            status = 12

    if status == 12:
        if V4D < 70:
            command = 'H,F1,F1,250,E'
        elif V4D < 105:
            command = 'H,F1,F1,230,E'
        elif V4D < 130:
            command = 'H,F1,F1,200,E'
        else:
            command = 'H,F1,F1,150,E'
        if leftLane and rightLane and V4D > 130:
            status = 1
    
    if LiDAR <= 200 and LiDAR >= 150:
        command = 'H,F0,F0,150,E'


    return command, status
