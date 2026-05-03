import re
import cv2
import numpy as np
import sys
import os
# import pygame

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from command_parser import split_command, normalize_tokens

############################# Camera Parameter ##############################
mtx = np.array([[168.1683,   0.,         166.4460],
 [  0.,         167.7907, 115.1241],
 [  0.,           0.,           1.        ]])
dist = np.array([[-0.2870, 0.0631, 0 ,0, 0]])
#############################################################################

ONLEFT = 0
ONSTRAIGHT = 1
ONRIGHT = 2
ONSCORNER = 3

def grayscale(img):
    return cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

def canny(img, low_threshold, high_threshold):
    return cv2.Canny(img, low_threshold, high_threshold)

def gaussian_blur(img, kernel_size):
    return cv2.GaussianBlur(img, (kernel_size, kernel_size), 0)

def region_of_interest(img, vertices, color3=(255,255,255), color1=255):
	
    mask = np.zeros_like(img)
    
    if len(img.shape) > 2:
        color = color3
    else:
        color = color1
        
    cv2.fillPoly(mask, vertices, color)
    
    ROI_image = cv2.bitwise_and(img, mask)
    return ROI_image

def draw_crossLines(image):
    height, width = image.shape[:2]

    # draw horizontal lines
    image = cv2.line(image, (0, int(height/4)*1), (width , int(height/4)*1), (180, 180, 180), 1)
    image = cv2.line(image, (0, int(height/4)*2), (width , int(height/4)*2), (180, 180, 180), 1)
    image = cv2.line(image, (0, int(height/4)*3), (width , int(height/4)*3), (180, 180, 180), 1)

    # draw vertical lines
    image = cv2.line(image, (int(width/8)*1, 0), (int(width/8)*1, int(height)), (180, 180, 180), 1)
    image = cv2.line(image, (int(width/8)*2, 0), (int(width/8)*2, int(height)), (180, 180, 180), 1)
    image = cv2.line(image, (int(width/8)*3, 0), (int(width/8)*3, int(height)), (180, 180, 180), 1)
    image = cv2.line(image, (int(width/8)*4, 0), (int(width/8)*4, int(height)), (180, 180, 180), 1)
    image = cv2.line(image, (int(width/8)*5, 0), (int(width/8)*5, int(height)), (180, 180, 180), 1)
    image = cv2.line(image, (int(width/8)*6, 0), (int(width/8)*6, int(height)), (180, 180, 180), 1)
    image = cv2.line(image, (int(width/8)*7, 0), (int(width/8)*7, int(height)), (180, 180, 180), 1)

    return image

def getVerticalDistance(image, v):
    VD = -1
    height, width = image.shape[:2]

    # find vertical distance from bottom
    for y in range(height+1):
        b = image.item(height-1-y, v, 0)  
        g = image.item(height-1-y, v, 1)  
        r = image.item(height-1-y, v, 2)
        if b == 255 and g == 255 and r == 255:
            VD = y
            break
    return VD
        
def getHorizontalDistance(image, h):
    height, width = image.shape[:2]
    center = int(width/2)
    HLD = -1
    HRD = -1

    # find Horizontal Left Distance from center line
    for x in range(center+1):
        b = image.item(h, center-x, 0)  
        g = image.item(h, center-x, 1)  
        r = image.item(h, center-x, 2)

        if b == 255 and g == 255 and r == 255:
            HLD = x
            break

    # find Horizontal Right Distance from center line
    for x in range(center):
        b = image.item(h, center+x, 0)  
        g = image.item(h, center+x, 1)  
        r = image.item(h, center+x, 2)

        if b == 255 and g == 255 and r == 255:
            HRD = x
            break

    return HLD, HRD

def getContactPoints(image):
    height, width = image.shape[:2]
    
    # get vertical lengths
    V1D = getVerticalDistance(image, int(width/8)*1)
    V2D = getVerticalDistance(image, int(width/8)*2)
    V3D = getVerticalDistance(image, int(width/8)*3)
    V4D = getVerticalDistance(image, int(width/8)*4)
    V5D = getVerticalDistance(image, int(width/8)*5)
    V6D = getVerticalDistance(image, int(width/8)*6)
    V7D = getVerticalDistance(image, int(width/8)*7)

    # get horizontal lenghts
    H1LD, H1RD = getHorizontalDistance(image, int(height/4)*1)
    H2LD, H2RD = getHorizontalDistance(image, int(height/4)*2)
    H3LD, H3RD = getHorizontalDistance(image, int(height/4)*3)

    return {'V1D':V1D, 'V2D':V2D, 'V3D':V3D, 'V4D':V4D, 'V5D':V5D, 'V6D':V6D, 'V7D':V7D, \
    'H1LD':H1LD, 'H1RD':H1RD, 'H2LD':H2LD, 'H2RD':H2RD, 'H3LD':H3LD, 'H3RD':H3RD}

def drawContactPoints(image, points):        
    height, width = image.shape[:2]        
    center = int(width/2)

    # draw vertical points
    image = cv2.circle(image, (center-points['H1LD'], int(height/4)*1), 1, (255, 0, 0), 2)
    image = cv2.circle(image, (center+points['H1RD']-1, int(height/4)*1), 1, (0, 0, 255), 2)
    image = cv2.circle(image, (center-points['H2LD'], int(height/4)*2), 1, (255, 0, 0), 2)
    image = cv2.circle(image, (center+points['H2RD']-1, int(height/4)*2), 1, (0, 0, 255), 2)
    image = cv2.circle(image, (center-points['H3LD'], int(height/4)*3), 1, (255, 0, 0), 2)
    image = cv2.circle(image, (center+points['H3RD']-1, int(height/4)*3), 1, (0, 0, 255), 2)

    # draw horizontal points
    image = cv2.circle(image, (int(width/8)*1, height-points['V1D']), 1, (0, 255, 255), 2)
    image = cv2.circle(image, (int(width/8)*2, height-points['V2D']), 1, (0, 255, 255), 2)
    image = cv2.circle(image, (int(width/8)*3, height-points['V3D']), 1, (0, 255, 255), 2)
    image = cv2.circle(image, (int(width/8)*4, height-points['V4D']), 1, (0, 255, 255), 2)
    image = cv2.circle(image, (int(width/8)*5, height-points['V5D']), 1, (0, 255, 255), 2)
    image = cv2.circle(image, (int(width/8)*6, height-points['V6D']), 1, (0, 255, 255), 2)
    image = cv2.circle(image, (int(width/8)*7, height-points['V7D']), 1, (0, 255, 255), 2)

    return image



# functions for the algorithm
def getLean(line):
    if line[0]-line[2] == 0:
        return 10000
    return (line[1]-line[3])/(line[0]-line[2])

def getIntercept(line):
    x = line[0]
    y = line[1]
    a = getLean(line)
    b = y-(a*x)
    return (120-b)/a

def draw_lines(img, lines, color=[0, 0, 255], thickness=2):
    for line in lines:
        for x1,y1,x2,y2 in line:
            cv2.line(img, (x1, y1), (x2, y2), color, thickness)

def hough_lines(img, rho, theta, threshold, min_line_len, max_line_gap): 
    lines = cv2.HoughLinesP(img, rho, theta, threshold, np.array([]), minLineLength=min_line_len, maxLineGap=max_line_gap)
    line_img = np.zeros((img.shape[0], img.shape[1], 3), dtype=np.uint8)
    draw_lines(line_img, lines)

    return line_img, lines
    
def weighted_img(img, initial_img, alpha=1, beta=1., gamma=0.):
    return cv2.addWeighted(initial_img, alpha, img, beta, gamma)

def getAlignedWheelAngle(command, alignAlgle):
    # 정렬 각도 오프셋 계산 (기존 로직 유지)
    alignAlgle = (alignAlgle * 5) - 25
    
    # ---------------------------------------------------------
    # 1. L 모드 처리 (기존 유지하되 최소한의 형식 검증 추가)
    # ---------------------------------------------------------
    if command.startswith('L'):
        try:
            steeringAngle = int(command[2:5]) + alignAlgle
            # L 모드에서도 범위 검증 컨벤션 적용
            if not (50 <= steeringAngle <= 250):
                print(f"[RANGE_ERR] Adjusted L-Angle {steeringAngle} out of range (50~250).")
                steeringAngle = max(50, min(250, steeringAngle))
            return command[:2] + '%03d' % steeringAngle + 'E'
        except ValueError:
            print(f"[TYPE_ERR] L-mode angle '{command[2:5]}' is not a valid integer.")
            return 'L0150E'

    # ---------------------------------------------------------
    # 2. H 모드 처리 (4단계 상세 검증 컨벤션 적용)
    # ---------------------------------------------------------
    tokens = split_command(command)
    
    # [1단계] 구조 검증: 토큰 개수
    if len(tokens) != 5:
        print(f"[LEN_ERR] Expected 5 tokens, but got {len(tokens)}.")
        return 'L0150E' # 에러 시 안전값 반환

    tokens = normalize_tokens(tokens)

    # [2단계] 마커 검증: 시작(H)과 끝(E)
    if tokens[0] != 'H' or tokens[4] != 'E':
        print(f"[MARK_ERR] Invalid Start/End marker. ('H', 'E' expected)")
        return 'L0150E'

    # [3단계] 형식 검증: 모터 및 각도 데이터 타입
    motor_pattern = re.compile(r'^([FB])(\d)$')
    
    # 모터 형식 및 범위 동시 검증
    for i, label in enumerate(['right_motor', 'left_motor'], start=1):
        match = motor_pattern.match(tokens[i])
        if not match:
            print(f"[TYPE_ERR] Invalid motor format '{tokens[i]}'. (F0~3, B0~3 expected)")
            return 'L0150E'
        
        # [4단계] 범위 검증: 모터 속도 (0~3)
        speed = int(match.group(2))
        if not (0 <= speed <= 3):
            print(f"[RANGE_ERR] Motor speed {speed} out of range (0~3).")
            return 'L0150E'

    # 각도 형식 및 범위 검증
    angle_str = tokens[3]
    if not angle_str.lstrip('-').isdigit():
        print(f"[TYPE_ERR] Angle '{angle_str}' is not a valid integer.")
        return 'L0150E'
    
    # [4단계] 범위 검증: 각도 (50~250)
    angle = int(angle_str) + alignAlgle
    if not (50 <= angle <= 250):
        print(f"[RANGE_ERR] Angle {angle} out of range (50~250).")
        angle = max(50, min(250, angle)) # 안전을 위해 범위를 제한함

    # 모든 검증 통과 시 H-mode 커맨드 재조립
    command = 'H,%s,%s,%03d,E' % (tokens[1], tokens[2], angle)
    return command

def getLane(lines):
    leftLanes = []
    rightLanes = []
    endLanes = []
    rightLane = []
    leftLane = []
    
    for line in lines.tolist():
        line = line[0]
        a = getLean(line)
        if a == 10000:
            pass
        elif a < -0.18 and line[2] < 360: # left lane
            leftLanes.append(line)
        elif a < 0.18: # end lane
            endLanes.append(line)
        elif line[0] > 300:
            rightLanes.append(line)

    for right in rightLanes:
        if len(rightLane) == 0:
            rightLane = right
        if getIntercept(right) < getIntercept(rightLane):
            rightLane = right
    for left in leftLanes:
        if len(leftLane) == 0:
            leftLane = left
        if getIntercept(left) > getIntercept(leftLane):
            leftLane = left
        
    return leftLane, rightLane, endLanes

def getMidPositionOfX(lines, width):
    sum = 0
    for line in lines:
        sum += (line[0] + line[2])/2
    sum /= len(lines)
    if sum < width/2:
        return False # means left
    else: return True # means right

def getCenterPoint(leftLane, rightLane):
    left_a = getLean(leftLane)
    left_b = leftLane[3] - left_a*leftLane[2]
    right_a = getLean(rightLane)
    right_b = rightLane[1] - right_a*rightLane[0]

    left_x = (30-left_b)/left_a
    right_x = (30-right_b)/right_a

    return left_x, right_x