from wafflecarUtil import *

def autoDrive_algorithm(original_img, canny_img, H1LD, H1RD, H2LD, H2RD, H3LD, H3RD, V1D, V2D, V3D, V4D, V5D, V6D, V7D, leftLane, rightLane, frontLane, LiDAR, prevComm, status, yolo_detections=None):
    command = prevComm
    top_class = ''
    if yolo_detections:
        top_class = yolo_detections[0]['class']
    else:
        top_class = 'Nothing'

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

    # ===== DEMO VISUALIZATION START (시연용 - 실습 전 삭제) =====
    if original_img is not None:
        _, w = original_img.shape[:2]

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

    type = '직진'
    # type은 직진, 직진_라이다, 표지판_이용, 신호등, 저속의 값으로 할 수 있어요

    if type == '직진':
        ## 직진 명령시 사용하세요
        if leftLane and rightLane:
            if H2LD > H2RD: ## pass를 지우고 command 값을 넣어주세요
                pass
            elif H2LD < H2RD:
                pass
            else: # H2LD == H2RD
                pass
                
    elif type == '직진_라이다':
        ## 직진시 라이다 이용해서 멈출때 사용하세요
        if 150 <= LiDAR <= 200: # 150mm 와 200mm 사이 거리인 경우 아래 블럭을 실행합니다.
            # 더 가까운 거리에서 멈춰볼까요?
            pass
        else:
            pass
        

    elif type == '표지판_이용':
        ## 직진시 표지판 이용해서 멈출때 사용하세요
        if top_class != 'Nothing' and top_class == 'STOP_SIGN': # 무엇인가 감지된 경우
            pass
        else: # 아무것도 감지 안된 경우
            pass

    elif type == '신호등':
        ## 빨간불에 멈출때 사용하세요
        if top_class != 'Nothing' and top_class == 'red_light':
            pass
        else:
            pass

    elif type == '저속':
        ## 저속 운용시 사용하세요
        if top_class != 'Nothing' and top_class == 'number_one':
            pass
        else:
            pass


    return command, status
