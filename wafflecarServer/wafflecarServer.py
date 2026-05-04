import socket
import io
import time
import struct
import os
import onionGpio
import threading
import signal
import sys
from OmegaExpansion import onionI2C
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from command_parser import split_command, normalize_tokens

# Registers/etc:
PCA9685_ADDRESS    = 0x40
MODE1              = 0x00
MODE2              = 0x01
SUBADR1            = 0x02
SUBADR2            = 0x03
SUBADR3            = 0x04
PRESCALE           = 0xFE
LED0_ON_L          = 0x06
LED0_ON_H          = 0x07
LED0_OFF_L         = 0x08
LED0_OFF_H         = 0x09
ALL_LED_ON_L       = 0xFA
ALL_LED_ON_H       = 0xFB
ALL_LED_OFF_L      = 0xFC
ALL_LED_OFF_H      = 0xFD

# Bits:
RESTART            = 0x80
SLEEP              = 0x10
ALLCALL            = 0x01
INVRT              = 0x10
OUTDRV             = 0x04


class PCA9685(object):
    """PCA9685 PWM LED/servo controller."""

    def __init__(self, address=PCA9685_ADDRESS, i2c=None, **kwargs):
        """Initialize the PCA9685."""
        self._device = onionI2C.OnionI2C()
        self.set_all_pwm(0, 0)
        self._device.writeByte(0x40, MODE2, OUTDRV)
        self._device.writeByte(0x40, MODE1, ALLCALL)
        time.sleep(0.005)  # wait for oscillator
        mode1 = self._device.readBytes(0x40, MODE1, 1)
        mode1 = mode1[0]
        # print(mode1)
        mode1 = mode1 & ~SLEEP  # wake up (reset sleep)
        self._device.writeByte(0x40, MODE1, mode1)
        time.sleep(0.005)  # wait for oscillator

    def set_pwm_freq(self, freq_hz):
        """Set the PWM frequency to the provided value in hertz."""
        prescaleval = 25000000.0    # 25MHz
        prescaleval /= 4096.0       # 12-bit
        prescaleval /= float(freq_hz)
        prescaleval -= 1.0
        prescale = int(math.floor(prescaleval + 0.5))
        oldmode = self._device.readBytes(0x40, MODE1, 8)
        oldmode = oldmode[0]
        newmode = (oldmode & 0x7F) | 0x10    # sleep
        self._device.writeByte(0x40, MODE1, newmode)  # go to sleep
        self._device.writeByte(0x40, PRESCALE, prescale)
        self._device.writeByte(0x40, MODE1, oldmode)
        time.sleep(0.005)
        self._device.writeByte(0x40, MODE1, oldmode | 0x80)

    def set_pwm(self, channel, on, off):
        """Sets a single PWM channel."""
        self._device.writeByte(0x40, LED0_ON_L+4*channel, on & 0xFF)
        self._device.writeByte(0x40, LED0_ON_H+4*channel, on >> 8)
        self._device.writeByte(0x40, LED0_OFF_L+4*channel, off & 0xFF)
        self._device.writeByte(0x40, LED0_OFF_H+4*channel, off >> 8)

    def set_all_pwm(self, on, off):
        """Sets all PWM channels."""
        self._device.writeByte(0x40, ALL_LED_ON_L, on & 0xFF)
        self._device.writeByte(0x40, ALL_LED_ON_H, on >> 8)
        self._device.writeByte(0x40, ALL_LED_OFF_L, off & 0xFF)
        self._device.writeByte(0x40, ALL_LED_OFF_H, off >> 8)
        
        

server_address = ('192.168.3.1', 19126)
stopTimerVal= 0
i2c = onionI2C.OnionI2C()
pwm = PCA9685()
pwm.set_pwm_freq(50)

# DC motor Speed
# pwm.set_pwm(channel, 1750, 2048)	: very slow
# pwm.set_pwm(channel, 1500, 2048)	: slow
# pwm.set_pwm(channel, 900, 2048)	: normal
# pwm.set_pwm(channel, 100, 2048)	: fast
# pwm.set_pwm(channel, 4096, 0)		: very fast

# DC motor Speed Ex
# pwm.set_pwm(3, 1750, 2048) : very slow
# pwm.set_pwm(2, 0, 4096)

# DC motor Channel
# Motor1 : Channel 4, 5 
# Motor2 : Channel 2, 3

def makeuint16(lsb, msb):
    return ((msb & 0xFF) << 8)  | (lsb & 0xFF)

def getDistance():
    try:
        i2c.writeByte(0x29, 0x000, 0x01)
        data = i2c.readBytes(0x29, 0x14, 12)
        distance = makeuint16(data[11], data[10])
        if distance < 20 or 2000 < distance:
            distance = 0
    except Exception as e:
        distance = 0
    return '%04d' % distance

def vehicle_backward():
    # Motor 1
    pwm.set_pwm(5, 1500, 2048)
    pwm.set_pwm(4, 0, 4096)
    
    # Motor 2
    pwm.set_pwm(3, 1500, 2048)
    pwm.set_pwm(2, 0, 4096)
    
    
def vehicle_forward():
    # Motor 1
    pwm.set_pwm(4, 1500, 2048)
    pwm.set_pwm(5, 0, 4096)
    
    # Motor 2
    pwm.set_pwm(2, 1500, 2048)
    pwm.set_pwm(3, 0, 4096)
    

def vehicle_stop():
    # Motor 1
    pwm.set_pwm(4, 0, 0)
    pwm.set_pwm(5, 0, 0)
    
    # Motor 2
    pwm.set_pwm(2, 0, 0)
    pwm.set_pwm(3, 0, 0)
        
    vehicle_turn(150)

def vehicle_steeringTest():
    pass

def vehicle_turn(angle):
    global servoDefaultValue

    # offset = 330 - servoDefaultValue
    # angle -= offset

    
    # servo_min = 440 # 100 is minimum
    # servo_mid = 480
    # servo_max = 520
    
    # input angle -> 110 ~ 190
    # if angle < 100:pkill -f wafflecarServer.py
    #     angle = 100
    # elif angle > 200:
    #     angle = 200

    # base 150
    if angle < 50:
        angle = 50

    elif angle > 250:
        angle = 250
    angle = angle + servoDefaultValue
        
    pwm.set_pwm(0, 0, angle)


    

def stopTimer():
    global stopTimerVal
    stopTimerVal += 1
    if stopTimerVal > 2:
        try:
            vehicle_stop()
            print('Stop timer is running during %ds..' % (stopTimerVal-2))
        except Exception as e:
            print('Error occured: ', e)
    timer = threading.Timer(1, stopTimer)
    timer.daemon = True
    timer.start()
    
def signal_handler(signal, frame):
    print('wafflecar server exit..')
    sys.exit(0)
    
    
########################
    


def startServer(connection, client_address, sendComm):
    global stopTimerVal
    global servoDefaultValue
    try:
        prevCmd = '0'
        while True:
            data = sendComm.recv(16)
            sendComm.sendall(getDistance())
            stopTimerVal = 0
                
            if data[0] == 'H':
                comm = normalize_tokens(split_command(data))
                # correct command input
                if comm[0] == 'H' and comm[4] == 'E':
                    
                    # power control
                    if comm[1][0] == 'F': # forward
                        # set right wheel speed (Motor 2)
                        if comm[1][1] == '1':
                            pwm.set_pwm(2, 900, 2048)
                            pwm.set_pwm(3, 0, 4096)
                        elif comm[1][1] == '2':
                            pwm.set_pwm(2, 100, 2048)
                            pwm.set_pwm(3, 0, 4096)
                        elif comm[1][1] == '3':
                            pwm.set_pwm(2, 4096, 0)
                            pwm.set_pwm(3, 0, 4096)
                        else:
                            pwm.set_pwm(2, 0, 0)
                            pwm.set_pwm(3, 0, 0)

                    if comm[2][0] == 'F': # forward
                        # set left wheel speed (Motor 1)
                        if comm[2][1] == '1':
                            pwm.set_pwm(4, 900, 2048)
                            pwm.set_pwm(5, 0, 4096)
                        elif comm[2][1] == '2':
                            pwm.set_pwm(4, 100, 2048)
                            pwm.set_pwm(5, 0, 4096)
                        elif comm[2][1] == '3':
                            pwm.set_pwm(4, 4096, 0)
                            pwm.set_pwm(5, 0, 4096)
                        else:
                            pwm.set_pwm(4, 0, 0)
                            pwm.set_pwm(5, 0, 0)
                            
                    if comm[1][0] == 'B': # backward
                        # set right wheel speed (Motor 2)
                        if comm[1][1] == '1':
                            pwm.set_pwm(3, 900, 2048)
                            pwm.set_pwm(2, 0, 4096)
                        elif comm[1][1] == '2':
                            pwm.set_pwm(3, 100, 2048)
                            pwm.set_pwm(2, 0, 4096)
                        elif comm[1][1] == '3':
                            pwm.set_pwm(3, 4096, 0)
                            pwm.set_pwm(2, 0, 4096)
                        else:
                            pwm.set_pwm(3, 0, 0)
                            pwm.set_pwm(2, 0, 0)
                    if comm[2][0] == 'B': # backward
                        # set left wheel speed (Motor 1)
                        if comm[2][1] == '1':
                            pwm.set_pwm(5, 900, 2048)
                            pwm.set_pwm(4, 0, 4096)
                        elif comm[2][1] == '2':
                            pwm.set_pwm(5, 100, 2048)
                            pwm.set_pwm(4, 0, 4096)
                        elif comm[2][1] == '3':
                            pwm.set_pwm(5, 4096, 0)
                            pwm.set_pwm(4, 0, 4096)
                        else:
                            pwm.set_pwm(5, 0, 0)
                            pwm.set_pwm(4, 0, 0)
                            
                    # steering wheel angle
                    vehicle_turn(int(comm[3]))
                    
                else: # incorrect command input
                    print('invalid command received', data)
                    
            # low level command protocol
            elif data[0] == 'L':
                # low level command protocol does not support wheel speed control.
                if len(data) is 6 and data[5] == 'E':
                    # power control
                    if data[1] == '0' and prevCmd != data[1]:
                        vehicle_stop()
                        prevCmd = data[1]
                    elif data[1] == '1' and prevCmd != data[1]:
                        vehicle_forward()
                        prevCmd = data[1]
                    elif data[1] == '2' and prevCmd != data[1]:
                        vehicle_backward()
                        prevCmd = data[1]
                    elif data[1] == '3' and prevCmd != data[1]:
                        vehicle_steeringTest()
                        prevCmd = data[1]
                        
                    vehicle_turn(int(data[2:5]))
                else:
                    print('invalid command received: ', data)

            # low level command protocol
            elif data[0] == 'Q':
                break

            # set servo angle
            elif data[0] == 'S':
                if len(data) is 5 and data[4] == 'E':
                    servoDefaultValue = int(data[1:4])
                    try:
                        f = open('servoDefaultValue.txt', 'w')
                        f.write('%d' % servoDefaultValue)
                    finally:
                        f.close()

    finally:
        print('[Server] Closing the connection...')
        connection.close()
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(server_address)

stopTimer()
signal.signal(signal.SIGINT, signal_handler)

# set default servo angle
servoDefaultValue = 0
try:
    f = open('/root/servoDefaultValue.txt', 'r')
    servoDefaultValue = int(f.read())
except:
    servoDefaultValue = 330
finally:
    f.close()

while True:
    print('[Server] ### Listening for connection...')
    server_socket.listen(1)
    connection, client_address = server_socket.accept()
    sendComm = connection
    connection = connection.makefile('wb')
    vehicle_stop()
    time.sleep(1) # GPIO warmup
    try:
        print('[Server] %s is now connected.' % client_address[0])
        startServer(connection, client_address, sendComm)
    except Exception as e:
        print('[Server] ERROR: %s' % e)
    finally:
        print('[Server] %s is now disconnected.' % client_address[0])
        time.sleep(2)

vehicle_stop()
server_socket.close()