from wafflecarUtil import *

def autoDrive_algorithm(original_img, canny_img, H1LD, H1RD, H2LD, H2RD, H3LD, H3RD, V1D, V2D, V3D, V4D, V5D, V6D, V7D, leftLane, rightLane, frontLane, LiDAR, prevComm, status):
    command = prevComm
    
    # height, width = canny_img.shape[:2]
    # center = int(width/2) - 2
    
    # if H2LD is not -1 and H2RD is not -1:
    #     centerPoint = (640 - H2LD + H2RD)/2
    # elif H1LD is not -1 and H1RD is not -1:
    #     centerPoint = (640 - H1LD + H1RD)/2
    # else:
    #     centerPoint = 320
    
    # # print('Center position: ', centerPoint)

    # if centerPoint > center+10:
    #     if centerPoint > center+35:
    #         command = 'L1165E'
    #     elif centerPoint > center+25:
    #         command = 'L1150E'
    #     else:
    #         command = 'L1155E'
    # elif centerPoint < center-10:
    #     if centerPoint < center-35:
    #         command = 'L1135E'
    #     elif centerPoint < center-25:
    #         command = 'L1140E'
    #     else:
    #         command = 'L1145E'
    # else:
    #     command = 'L1150E'
    
    command = 'H,F0,F0,150,E'
    # print(LiDAR)

    if status == ONSTRAIGHT:
        status = {'SERVO':150, 'DC':0}

    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            pressed = pygame.key.get_pressed()
            if pressed[pygame.K_LEFT]:
                if status['SERVO'] > 110:
                    status['SERVO'] -= 10
            elif pressed[pygame.K_RIGHT]:
                if status['SERVO'] < 190:
                    status['SERVO'] += 10
            elif pressed[pygame.K_UP]:
                if status['DC'] < 3:
                    status['DC'] += 1
            elif pressed[pygame.K_DOWN]:
                if status['DC'] > -3:
                    status['DC'] -= 1
    if status['DC'] >= 0:
        command = 'H,F%d,F%d,%d,E' % (status['DC'],status['DC'],status['SERVO'])
    else:
        command = 'H,B%d,B%d,%d,E' % (-1*status['DC'],-1*status['DC'],status['SERVO'])

    return command, status