# PyQt5(QtWebEngine)보다 먼저 PyTorch/YOLO를 로드해야 DLL 충돌이 없음
import os as _os
_YOLO_MODEL_GLOBAL = None
_yolo_model_path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'yolo_model.pt')
if _os.path.exists(_yolo_model_path):
    try:
        from ultralytics import YOLO as _YOLO
        _YOLO_MODEL_GLOBAL = _YOLO(_yolo_model_path)
        print('[YOLO] 모델 사전 로드 완료: %s' % _yolo_model_path)
        print('[YOLO] 클래스: %s' % _YOLO_MODEL_GLOBAL.names)
    except Exception as _e:
        print('[YOLO] 모델 로드 실패: %s' % _e)

from PyQt5 import QtCore, QtGui, QtWidgets
from mainUI import Ui_MainWindow

from PyQt5.QtCore import QThread
from PyQt5.QtCore import QWaitCondition
from PyQt5.QtCore import QMutex
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtCore import QObject
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import QUrl
from PyQt5.QtCore import QDir
# from PyQt5.QtWebEngineWidgets import QWebEnginePage

from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QWidget

import importlib
import webbrowser
from wafflecarUtil import *
# from waffleLocalHttpServer import *

import sys
import os
import cv2
import numpy
import socket
import time
import pickle
import glob
from datetime import datetime
import threading
import subprocess
# import pygame

# import tensorflow.keras
from PIL import Image, ImageOps

class ValvePopup(QWidget):
    def __init__(self):
        super().__init__()
        self.setupUI()

    def setupUI(self):
        self.setWindowTitle("Waffle Launcher V2.93")
        self.setGeometry(700,350,500,150)

        # self.label_9 = QtWidgets.QLabel(self.groupBox_11)
        # self.label_9.setGeometry(QtCore.QRect(190, 60, 61, 31))
        # self.label_9.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        # self.label_9.setObjectName("label_9")
        # self.label_9.setText(_translate("MainWindow", "오른쪽"))

        self.label = QtWidgets.QLabel("사용 기간이 만료되었습니다! (2022년 12월 만료)", self)
        self.label.move(50,30)
        self.label.resize(350, 20)

        self.btnClose = QtWidgets.QPushButton("확인", self)
        self.btnClose.move(50,70)
        self.btnClose.clicked.connect(self.btnClose_clicked)
    
    def btnClose_clicked(self):
        exit()
    # # Signal 선언부
    # send_valve_popup_signal = pyqtSignal(bool, name='sendValvePopupSignal')

    # # ==========================================================================
    # def __init__(self, parent=None):
    #     QWidget.__init__(self, parent)
    #     self.accept_button = QPushButton()
    #     self.cancel_button = QPushButton()
    #     self.init_ui()

    # # ==========================================================================
    # def init_ui(self):
    #     pass

    # # ==========================================================================
    # def show_popup_ok_cancel(self, title: str, content: str):
    #     msg = QMessageBox()
    #     msg.setWindowTitle(title)
    #     msg.setText(content)
    #     msg.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
    #     result = msg.exec_()
    #     if result == QMessageBox.Cancel:
    #         self.send_valve_popup_signal.emit(False)
    #     elif result == QMessageBox.Ok:
    #         self.send_valve_popup_signal.emit(True)
    # # ==========================================================================
    # def show_popup_ok(self, title: str, content: str):
    #     msg = QMessageBox()
    #     msg.setWindowTitle(title)
    #     msg.setText(content)
    #     msg.setStandardButtons(QMessageBox.Ok)
    #     result = msg.exec_()
    #     if result == QMessageBox.Ok:
    #         self.send_valve_popup_signal.emit(True)

class LiDARStreamingThread(QThread):
    streamingDistance = pyqtSignal(int)

    def __init__(self, sock):
        QThread.__init__(self)
        self.cond = QWaitCondition()
        self.mutex = QMutex()
        self.sock = sock
    
    def __del__(self):
        self.wait()

    def run(self):
        while True:
            try:
                self.mutex.lock()
                # LiDAR, addr = self.sock.recvfrom(5)
                LiDAR = self.sock.recv(5)
                self.streamingDistance.emit(int(LiDAR.decode()))
                self.mutex.unlock()
            except Exception as e:
                self.mutex.unlock()
                print('LIDAR THREAD ERROR: %s' % e)
                if getattr(e, 'errno', None) == 9:  # EBADF: socket closed
                    break
                # self.textBrowser_simulation.append('라이다 데이터가 누락되었습니다.')
                # self.textBrowser.append('라이다 데이터가 누락되었습니다.')

class ImageStreamingThread(QThread):
    streamingImage = pyqtSignal(numpy.ndarray)

    def __init__(self, IPADDR):
        QThread.__init__(self)
        self.cond = QWaitCondition()
        self.mutex = QMutex()
        self.IPADDR = IPADDR
        self.camisOpened = self.camInit()

    def __del__(self):
        self.cam.release()
        self.wait()

    def camInit(self):
        streamingAddress = 'http://%s:8080/?action=stream' % self.IPADDR
        self.cam = cv2.VideoCapture(streamingAddress)
        if not self.cam.isOpened():
            return False
        return True

    def run(self):
        while True:
            try:
                self.mutex.lock()
                ret, frame = self.cam.read()
                if ret == True:
                    self.streamingImage.emit(frame)            
                self.mutex.unlock()
            except Exception as e:
                print('IMAGE THREAD ERROR: %s' % e)
                # self.textBrowser_simulation.append('카메라 이미지가 누락되었습니다.')
                # self.textBrowser.append('카메라 이미지가 누락되었습니다.')

class SimulationThread(QThread):
    simulationData = pyqtSignal(str)

    def __init__(self, images, timeInterval, frameIndex):
        QThread.__init__(self)
        self.cond = QWaitCondition()
        self.mutex = QMutex()
        self.images = images
        self.timeInterval = timeInterval
        self.frameIndex = frameIndex
    
    def __del__(self):
        self.wait()

    def run(self):
        while True:
            if self.frameIndex >= len(self.images):
                self.mutex.lock()
                self.simulationData.emit('0xFFFF')
                self.mutex.unlock()
                break
            else:
                self.mutex.lock()
                image = self.images[self.frameIndex]
                self.frameIndex += 1
                self.simulationData.emit(image)
                time.sleep(self.timeInterval)
                self.mutex.unlock()

class CallHandler(QObject):
    """
    콜 핸들러 클래스는 Js와 통신하는 부분을 분리 목적
    """
    
    get_data = pyqtSignal(str, name="getData")

    @pyqtSlot(str, name='sendData')
    def send_Data(self, data):
        # 파이썬에서 데이터 받는 핸들러
        if data[:3] == 'XML':
            fp = open('savedBlocks.xml', 'w', encoding='utf-8')
            fp.write(data[3:])
            fp.close()
        elif data[:4] == 'PYPY':
            fp = open('_algorithm_.py', 'w')
            fp.write(data[4:])
            fp.close()
            self.toAlgorithmFile()

    def toAlgorithmFile(self):
        original = open('_algorithm_.py', 'r')
        output = open('algorithm_AutoCreated.py', 'w')
        # output.write('import math\n\n')
        output.write('import math\nfrom wafflecarUtil import *\n\n')

        check = False

        for line in original:
            if check:
                if 'return _EB_AA_85_EB_A0_B9 and _EC_A3_BC_ED_96_89__EC_83_81_ED_83_9C' in line:
                    output.write(line.replace(' and', ','))
                else:
                    output.write(line)
            else:
                d = line.split('(')
                if d[0] == 'def _EC_95_8C_EA_B3_A0_EB_A6_AC_EC_A6_98':
                    check = True
                    output.write('def autoDrive_algorithm('+d[1])
        
        original.close()
        output.close()

        
        original = open('_algorithm_.py', 'r')
        output = open('AutoCreated.py', 'w')
        # output.write('import math\nfrom wafflecarUtil import *\n\n')
        output.write('import math\n\n')
        for line in original:
            output.write(line)

        original.close()
        output.close()
        os.remove('_algorithm_.py')

class waffleLauncher(Ui_MainWindow):

    def __init__(self, MainWindow):
        Ui_MainWindow.__init__(self)
        self.setupUi(MainWindow)
        self.userAlgorithm = None
        self.setAlgorithm()
        self.SimulationStatus = False
        self.WaffleCarStatus = False
        self.imageSaveStatus = False
        self.servoSettingStatus = False
        self.SERVER_ADDR = ('192.168.3.1', 19126)
        self.frame = None
        self.imageNameCnt = 0
        self.images = None
        self.setInitialValues()
        self.WHEELALIGN = 5
        self.watchdogTimer = 0

        # YOLO 모델 — PyQt5 로드 전에 미리 로드된 글로벌 인스턴스 사용
        self.yolo_model = _YOLO_MODEL_GLOBAL

        # pygame.init()
        # screen = pygame.display.set_mode((300,300))
        # pygame.display.set_caption("Key Event")

        # self.watchdog_Camera()

        try:
            with open('wafflelauncherParams.pkl', 'rb') as f:
                self.WHEELALIGN = pickle.load(f)
                self.horizontalSlider.setValue(self.WHEELALIGN)
        except Exception as e:
            pass

        # get align-slider's value
        self.horizontalSlider.valueChanged.connect(self.alignValue)
        

        # # web server thread start
        # self.webServerThread = localHttpServerThread()
        # self.webServerThread.start()

        # web viewer
        url = os.getcwd() + r'\waffleBlockly\demo\code\index.html'
        path = QUrl.fromLocalFile(url)
        self.webWidget = QWebEngineView(self.tab_4)
        self.webWidget.setGeometry(QtCore.QRect(10, 10, 1101, 591))
        self.webWidget.setObjectName("webWidget")

        # web channel
        channel = QWebChannel(self.webWidget.page())
        self.webWidget.page().setWebChannel(channel)
        self.handler = CallHandler()  # 반드시 인스턴스 변수로 사용해야 한다.
        channel.registerObject('handler', self.handler)  # js에서 불리울 이름


        # show web page
        self.webWidget.load(path)
        self.webWidget.show()

        # connect buttons
        self.btn_selectAlgorithm.clicked.connect(self.btn_selectAlgorithmClicked)
        self.btn_selectSimulationData.clicked.connect(self.btn_selectSimulationDataClicked)
        self.btn_startSimulation.clicked.connect(self.btn_startSimulationClicked)
        self.btn_startWafflecar.clicked.connect(self.btn_startWafflecarClicked)
        self.btn_saveImage.clicked.connect(self.btn_saveImageClicked)
        self.btn_blockInit.clicked.connect(self.btn_blockInitClicked)
        self.btn_blockLoad.clicked.connect(self.btn_blockLoadClicked)
        self.btn_blockSave.clicked.connect(self.btn_blockSaveClicked)
        self.btn_resize.clicked.connect(self.btn_resizeClicked)
        self.btn_servoValueSetup.clicked.connect(self.btn_servoValueSetupClicked)
        self.btn_runCode.clicked.connect(self.btn_runCodeClicked)
        self.btn_runBlock.clicked.connect(self.btn_runBlockClicked)
        self.btn_buy.clicked.connect(self.btn_buyCodeClicked)

        self.getCameraParams()
        MainWindow.show()


    def alignValue(self, value):
        self.WHEELALIGN = int(value)
        with open('wafflelauncherParams.pkl', 'wb') as f:
            pickle.dump(self.WHEELALIGN, f)

    def setAlgorithm(self):
        try:
            a1 = os.path.getmtime('algorithm.py')
            a2 = os.path.getmtime('algorithm_AutoCreated.py')
            if a1 > a2:
                self.userAlgorithm = importlib.import_module('algorithm')
            else:
                mod = importlib.import_module('algorithm_AutoCreated')
                if hasattr(mod, 'autoDrive_algorithm'):
                    self.userAlgorithm = mod
                else:
                    self.userAlgorithm = importlib.import_module('algorithm')
        except Exception as e:
            self.textBrowser_simulation.append('algorithm.py 파일에 오류가 있습니다. 자세한 내용은 프롬프트창을 확인해주세요.')
            self.textBrowser.append('algorithm.py 파일에 오류가 있습니다. 자세한 내용은 프롬프트창을 확인해주세요.')
    
    def setInitialValues(self):
        self.command = 'L0150E'
        self.status = ONSTRAIGHT
        self.LiDAR = 0

    def getCameraParams(self):
        try:
            params = np.loadtxt("cameraParams.txt", dtype=np.float64, delimiter=',')
            self.mtx = params[:9].reshape(3,3)
            self.dist = params[9:]
            self.mapx, self.mapy = cv2.initUndistortRectifyMap(self.mtx, self.dist, None, None, (640, 360), cv2.CV_32FC1) 
        except Exception as e:
            print("Can't open the parameter file..")
            self.mtx = None
            self.dist = None
    
    def btn_selectAlgorithmClicked(self):
        pass
    
    def btn_resizeClicked(self):
        width = self.verticalLayout.geometry().width() - 32
        height = self.verticalLayout.geometry().height() - 80
        self.webWidget.setGeometry(QtCore.QRect(10, 10, width, height))
    
    def btn_blockInitClicked(self):
        initBlocks = open('initBlocks.xml', 'rt', encoding='UTF8')
        xml = initBlocks.read()
        initBlocks.close()
        self.handler.getData.emit('LOAD'+xml)

    def btn_blockLoadClicked(self):        
        savedBlocks = open('savedBlocks.xml', 'rt', encoding='UTF8')
        xml = savedBlocks.read()
        savedBlocks.close()
        self.handler.getData.emit('LOAD'+xml)
        
    def btn_blockSaveClicked(self):
        self.handler.getData.emit('SAVE')

    def btn_selectSimulationDataClicked(self):
        try:
            # set file path
            self.filePath = str(QtWidgets.QFileDialog.getExistingDirectory(None, '폴더 선택', '.', QtWidgets.QFileDialog.ShowDirsOnly))
            self.textBrowser_simulation.append('시뮬레이션 데이터 위치: %s' % self.filePath)
            self.images = sorted(glob.glob('%s/*.jpg' % self.filePath), key=os.path.getctime)

            self.textBrowser_simulation.append('시뮬레이션 데이터 수: %d 프레임' % len(self.images))

        except FileNotFoundError:
            pass
    
    def setCannyThreshold(self):
        self.minThreshold = int(self.txt_minThreshold.toPlainText())
        self.maxThreshold = int(self.txt_maxThreshold.toPlainText())

    def btn_startSimulationClicked(self):
        if self.images == None:
            self.textBrowser_simulation.append('시뮬레이션 데이터를 선택해주세요.')
            return

        self.SimulationStatus = not self.SimulationStatus
        if self.SimulationStatus:
            self.btn_startSimulation.setText("시뮬레이션 정지")
        elif not self.SimulationStatus:
            self.btn_startSimulation.setText("시뮬레이션 시작")

        if self.SimulationStatus:
            if self.chk_iswafflecar.isChecked():
                # init wafflcar
                command = getAlignedWheelAngle('L0150E', (self.WHEELALIGN))  
                addr = self.txt_ipaddress.toPlainText()
                self.SERVER_ADDR = (addr, 19126)
                
                # UDP
                # self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                # self.sock.sendto(command.encode(), self.SERVER_ADDR)

                # TCP
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect(self.SERVER_ADDR)
                self.sock.sendall(command.encode())

                self.textBrowser_simulation.append("[알림] 와플카 연결")
                self.textBrowser_simulation.append("IP: %s / Port: %d" % (self.SERVER_ADDR[0], self.SERVER_ADDR[1]))
            self.setInitialValues()
            self.setCannyThreshold()
            self.chk_iswafflecar.setEnabled(False)
            
            # reload algorithm file
            try:
                importlib.reload(self.userAlgorithm)
            except Exception as e:
                self.textBrowser_simulation.append('algorithm.py 파일에 오류가 있습니다. 자세한 내용은 프롬프트창을 확인해주세요.')
                self.textBrowser.append('algorithm.py 파일에 오류가 있습니다. 자세한 내용은 프롬프트창을 확인해주세요.')
            
            self.textBrowser_simulation.append("[알림] 시뮬레이션 시작")
            timeInterval = self.txt_timeInterval.toPlainText()
            startFrame = self.txt_startFrame.toPlainText()
            # find start frame
            for idx, val in enumerate(self.images):
                fn = os.path.split(os.path.splitdrive(val)[1])[1]
                if int(fn[:-9]) == int(startFrame):
                    startFrame = idx
                    break

            self.simulationThread = SimulationThread(self.images, float(timeInterval), int(startFrame))
            self.simulationThread.simulationData.connect(self._simulationThread)
            self.simulationThread.start()
        elif not self.SimulationStatus:
            self.textBrowser_simulation.append("[알림] 시뮬레이션 종료")
            self.simulationThread.disconnect()
            self.chk_iswafflecar.setEnabled(True)
            
            try:
                self.sock.sendall('Q'.encode())
                self.sock.close()
            except Exception as e:
                print(e)

    def btn_saveImageClicked(self):        
        self.imageSaveStatus = not self.imageSaveStatus
        self.imageNameCnt = 0
        try:
            if not(os.path.isdir('savedImage')):
                os.makedirs(os.path.join('savedImage'))
        except OSError as e:
            print("Failed to create directory")
        if self.imageSaveStatus:
            self.btn_saveImage.setText("시뮬레이션 데이터 정지")
            self.btn_startWafflecar.setEnabled(False)
        elif not self.imageSaveStatus:
            self.btn_saveImage.setText("시뮬레이션 데이터 녹화")
            self.btn_startWafflecar.setEnabled(True)

        if self.imageSaveStatus:
            addr = self.txt_ipaddress.toPlainText()
            command = getAlignedWheelAngle('L0150E', (self.WHEELALIGN))  
            self.SERVER_ADDR = (addr, 19126)

            self.textBrowser_simulation.append("[알림] 녹화 시작")

            # init wafflcar             
            
            # UDP
            # self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # self.sock.sendto(command.encode(), self.SERVER_ADDR)

            # TCP
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect(self.SERVER_ADDR)
            self.sock.sendall(command.encode())

            self.textBrowser_simulation.append("[알림] 와플카 연결")
            self.textBrowser_simulation.append("IP: %s / Port: %d" % (self.SERVER_ADDR[0], self.SERVER_ADDR[1]))

            # Streaming Thread
            self.imageStreamingThread = ImageStreamingThread(addr)
            if not self.imageStreamingThread.camisOpened:
                self.textBrowser_simulation.append("[알림] 카메라 연결에 실패하였습니다. IP 주소를 확인해주세요.")
            self.imageStreamingThread.streamingImage.connect(self.runWaffleCar)
            self.imageStreamingThread.start()

            # Lidar Thread
            self.lidarStreamingThread = LiDARStreamingThread(self.sock)
            self.lidarStreamingThread.streamingDistance.connect(self.getDistanceThread_forSimulation)
            self.lidarStreamingThread.start()

        elif not self.WaffleCarStatus:
            self.textBrowser_simulation.append("[알림] 녹화 종료")
            self.imageStreamingThread.disconnect()
            self.lidarStreamingThread.disconnect()
            try:
                self.sock.sendall('Q'.encode())
                self.sock.close()
            except Exception as e:
                print(e)
        

    def btn_startWafflecarClicked(self):
        self.watchdogTimer = 0
        self.WaffleCarStatus = not self.WaffleCarStatus

        if self.WaffleCarStatus:
            self.btn_startWafflecar.setText("와플카 정지")
            self.btn_saveImage.setEnabled(False)
        elif not self.SimulationStatus:
            self.btn_startWafflecar.setText("와플카 시작")
            self.btn_saveImage.setEnabled(True)

        if self.WaffleCarStatus:
            # reload algorithm file
            try:
                importlib.reload(self.userAlgorithm)
            except Exception as e:
                self.textBrowser_simulation.append('algorithm.py 파일에 오류가 있습니다. 자세한 내용은 프롬프트창을 확인해주세요.')
                self.textBrowser.append('algorithm.py 파일에 오류가 있습니다. 자세한 내용은 프롬프트창을 확인해주세요.')
                
            self.textBrowser.append("[알림] 와플카 시작")
            addr = self.txt_ipaddress.toPlainText()
            self.SERVER_ADDR = (addr, 19126)
            

            # init wafflcar 
            command = getAlignedWheelAngle('L0150E', (self.WHEELALIGN))  

            # UDP
            # self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # self.sock.sendto(command.encode(), self.SERVER_ADDR)

            # TCP
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect(self.SERVER_ADDR)
            self.sock.sendall(command.encode())

            self.textBrowser.append("[알림] 와플카 연결")
            self.textBrowser.append("IP: %s / Port: %d" % (self.SERVER_ADDR[0], self.SERVER_ADDR[1]))
            self.setInitialValues()
            self.setCannyThreshold()

            # Streaming Thread
            self.imageStreamingThread = ImageStreamingThread(addr)
            # time.sleep(0.5)
            if not self.imageStreamingThread.camisOpened:
                self.textBrowser.append("[알림] 카메라 연결에 실패하였습니다. IP 주소를 확인해주세요.")
            self.imageStreamingThread.streamingImage.connect(self.runWaffleCar)
            self.imageStreamingThread.start()

            # Streaming Thread
            self.lidarStreamingThread = LiDARStreamingThread(self.sock)
            # time.sleep(0.5)
            self.lidarStreamingThread.streamingDistance.connect(self.getDistanceThread)
            self.lidarStreamingThread.start()

        elif not self.WaffleCarStatus:
            self.textBrowser.append("[알림] 와플카 정지")
            self.imageStreamingThread.disconnect()
            self.lidarStreamingThread.disconnect()
            try:
                self.sock.sendall('Q'.encode())
                self.sock.close()
            except Exception as e:
                print(e)


    def btn_servoValueSetupClicked(self):
        self.servoSettingStatus = True   

    
    def btn_runCodeClicked(self):
        try:
            os.chdir('src')
            codePath = self.txt_codePath.toPlainText()
            subprocess.call(['python', codePath])
            # exec(open(codePath, 'rt', encoding='UTF8').read())

        except Exception as e:
            print(e)
        finally:
            os.chdir('..')
        # codePath = 'src.' + self.txt_codePath.toPlainText().split('.')[0]
        # try:
        #     importlib.reload(codePath)
        # except Exception as e:
        #     importlib.import_module(codePath)
    
    def btn_runBlockClicked(self):
        try:
            subprocess.call(['python', 'AutoCreated.py'])
            # exec(open('AutoCreated.py', 'rt', encoding='UTF8').read())
        except Exception as e:
            print(e)


    def btn_buyCodeClicked(self):
        webbrowser.open("https://smartstore.naver.com/semodal/products/4975662394")
        
    
    def imageProcessing(self, image, LiDAR):
        try:
            try:
                # undist_image = cv2.undistort(image, self.mtx, self.dist, None, self.mtx)
                undist_image = cv2.remap(image, self.mapx, self.mapy, interpolation=cv2.INTER_LINEAR)
            except Exception as e:
                undist_image = image

            # set ROI 
            height, width = undist_image.shape[:2]
            ROI_image = undist_image[180:360, :]

            gray_img = cv2.cvtColor(ROI_image, cv2.COLOR_BGR2GRAY)
            blur_img = gaussian_blur(gray_img, 3)
            canny_img = canny(blur_img, self.minThreshold, self.maxThreshold)

            # Hough transform
            vertices = np.array([[(50,height),(width/2-45, height/2+60), (width/2+45, height/2+60), (width-50,height)]], dtype=np.int32)
            hough_img, lines = hough_lines(canny_img, 1, 1 * np.pi/180, 55, 20, 10)

            # convert color gray to bgr in order to detect edge
            canny_img = cv2.cvtColor(canny_img, cv2.COLOR_GRAY2BGR)

            # get contact points
            points = getContactPoints(canny_img)

            # draw contact points
            canny_img = drawContactPoints(canny_img, points)
            
            # draw cross line
            canny_img = draw_crossLines(canny_img)

            # draw hough lines
            hough_img = weighted_img(hough_img, canny_img)

            # grid Data
            H1LD = points['H1LD']
            H1RD = points['H1RD']
            H2LD = points['H2LD']
            H2RD = points['H2RD']
            H3LD = points['H3LD']
            H3RD = points['H3RD']
            V1D = points['V1D']
            V2D = points['V2D']
            V3D = points['V3D']
            V4D = points['V4D']
            V5D = points['V5D']
            V6D = points['V6D']
            V7D = points['V7D']

            # Lane Data
            leftLane, rightLane, frontLane = getLane(lines)

            # YOLO 탐지
            yolo_detections = []
            if self.yolo_model is not None:
                try:
                    yolo_results = self.yolo_model(undist_image, verbose=False)
                    if len(yolo_results[0].boxes) > 0:
                        for box in sorted(yolo_results[0].boxes, key=lambda b: float(b.conf), reverse=True):
                            yolo_detections.append({
                                'class': yolo_results[0].names[int(box.cls)],
                                'confidence': float(box.conf)
                            })
                except Exception as e:
                    print('[YOLO inference] %s' % e)

            # get drive command
            self.command, self.status = self.userAlgorithm.autoDrive_algorithm(undist_image, canny_img, H1LD, H1RD, H2LD, H2RD, H3LD, H3RD, V1D, V2D, V3D, V4D, V5D, V6D, V7D, leftLane, rightLane, frontLane, LiDAR, self.command, self.status, yolo_detections)

        except Exception as e:
            print('[imageProcessing function] %s in algorithm.py' % e)
            canny_img = None
            hough_img = None
            if self.userAlgorithm is not None:
                self.command, self.status = self.userAlgorithm.autoDrive_algorithm(undist_image, canny_img, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, [], [], [], LiDAR, self.command, self.status, [])
        
        return True, self.command, undist_image, canny_img, hough_img

    def _simulationThread(self, simData):
        try:
            if simData == '0xFFFF':
                self.textBrowser_simulation.append('시뮬레이션이 종료되었습니다. 시뮬레이션 종료 버튼을 눌러주세요.')
                return
            
            image = cv2.imread(simData)
            fn = os.path.split(os.path.splitdrive(simData)[1])[1]
            status, command, undist_image, canny_img, hough_img = self.imageProcessing(image, int(simData[-8:-4]))
            self.textBrowser_simulation.append('%d frame: %s' % (int(fn[:-9]), command))
            
            # if self.chk_iswafflecar.isChecked():
            #     command = getAlignedWheelAngle(command, (self.WHEELALIGN))  
            #     # self.sock.sendto(command.encode(), self.SERVER_ADDR)
            #     self.sock.sendall(command.encode())

            height, width, bytesPerComponent = undist_image.shape
            bytesPerLine = 3 * width
            qt_image = QtGui.QImage(undist_image.data, width, height, bytesPerLine, QtGui.QImage.Format_RGB888).rgbSwapped()
            self.originalImage_simulation.setPixmap(QtGui.QPixmap(qt_image))

            if hough_img is not None:
                height, width, bytesPerComponent = hough_img.shape
                bytesPerLine = 3 * width
                qt_image = QtGui.QImage(hough_img.data, width, height, bytesPerLine, QtGui.QImage.Format_RGB888).rgbSwapped()
                self.processedImage_simulation.setPixmap(QtGui.QPixmap(qt_image))

        except Exception as e:
            print('[_simulationThread function] %s' % e)


    def getDistanceThread(self, LiDAR):
        self.LiDAR = LiDAR
        
        try:
            status, command, undist_image, canny_img, hough_img = self.imageProcessing(self.frame, self.LiDAR)

            if self.servoSettingStatus:                
                val = self.txt_servoValue.toPlainText()
                command = 'S%sE' % val
                self.textBrowser.append('서보모터 기본값 변경!')
                self.sock.sendall(command.encode())
                self.servoSettingStatus = False
            else:
                self.textBrowser.append(command)
                command = getAlignedWheelAngle(command, (self.WHEELALIGN))
                self.sock.sendall(command.encode())

            height, width, bytesPerComponent = undist_image.shape
            bytesPerLine = 3 * width
            qt_image = QtGui.QImage(undist_image.data, width, height, bytesPerLine, QtGui.QImage.Format_RGB888).rgbSwapped()
            self.originalImage.setPixmap(QtGui.QPixmap(qt_image))

            if hough_img is not None:
                height, width, bytesPerComponent = hough_img.shape
                bytesPerLine = 3 * width
                qt_image = QtGui.QImage(hough_img.data, width, height, bytesPerLine, QtGui.QImage.Format_RGB888).rgbSwapped()
                self.processedImage.setPixmap(QtGui.QPixmap(qt_image))
        except Exception as e:
            print('[getDistanceThread function] %s' % e)
    
    def getDistanceThread_forSimulation(self, LiDAR):
        try:
            command = getAlignedWheelAngle('L0150E', (self.WHEELALIGN))  
            # self.sock.sendto(command.encode(), self.SERVER_ADDR)            
            self.sock.sendall(command.encode())
            filename = 'savedImage/%04d-%04d.jpg' % (self.imageNameCnt, LiDAR)
            cv2.imwrite(filename, self.frame)
            self.imageNameCnt += 1

            height, width, bytesPerComponent = self.frame.shape
            bytesPerLine = 3 * width
            qt_image = QtGui.QImage(self.frame.data, width, height, bytesPerLine, QtGui.QImage.Format_RGB888).rgbSwapped()
            self.originalImage_simulation.setPixmap(QtGui.QPixmap(qt_image))

        except Exception as e:
            print('[getDistanceThread_forSimulation function] %s' % e)

    def runWaffleCar(self, frame):
        # color_swapped_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.frame = frame

        if self.RBtn_NEW.isChecked():
            height, width, channel = frame.shape
            matrix = cv2.getRotationMatrix2D((width/2, height/2), 180, 1)
            self.frame = cv2.warpAffine(frame, matrix, (width, height))

        self.watchdogTimer = 0

    # def watchdog_Camera(self):
    #     self.watchdogTimer += 1
    #     if self.watchdogTimer > 2 and self.WaffleCarStatus:
    #         try:
    #             # self.textBrowser.append("[알림] 와플카 재시작")
    #             # self.btn_startWafflecarClicked()
    #             # time.sleep(1.5)
    #             # self.btn_startWafflecarClicked()
    #             try:
    #                 importlib.reload(self.userAlgorithm)
    #             except Exception as e:
    #                 self.textBrowser_simulation.append('algorithm.py 파일에 오류가 있습니다. 자세한 내용은 프롬프트창을 확인해주세요.')
    #                 self.textBrowser.append('algorithm.py 파일에 오류가 있습니다. 자세한 내용은 프롬프트창을 확인해주세요.')
                
    #             self.imageStreamingThread.disconnect()
    #             self.lidarStreamingThread.disconnect()
    #             self.watchdogTimer = 0
    #             time.sleep(0.5)

    #             self.textBrowser.append("[알림] 와플카 재시작")
    #             addr = self.txt_ipaddress.toPlainText()
    #             self.SERVER_ADDR = (addr, 19126)

                
    #             # init wafflcar 
    #             command = getAlignedWheelAngle('L0150E', (self.WHEELALIGN))

    #             # UDP
    #             # self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #             # self.sock.sendto(command.encode(), self.SERVER_ADDR)

    #             # TCP
    #             self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #             self.sock.connect(self.SERVER_ADDR)
    #             self.sock.sendall(command.encode())

    #             self.setInitialValues()
    #             self.setCannyThreshold()

    #             # Streaming Thread
    #             self.imageStreamingThread = ImageStreamingThread(addr)
                
    #             if not self.imageStreamingThread.camisOpened:
    #                 self.textBrowser.append("[알림] 카메라 연결에 실패하였습니다. IP 주소를 확인해주세요.")
    #             self.imageStreamingThread.streamingImage.connect(self.runWaffleCar)
    #             self.imageStreamingThread.start()

    #             # Streaming Thread
    #             self.lidarStreamingThread = LiDARStreamingThread(self.sock)
    #             # time.sleep(0.5)
    #             self.lidarStreamingThread.streamingDistance.connect(self.getDistanceThread)
    #             self.lidarStreamingThread.start()

                
    #         except Exception as e:
    #             self.textBrowser.append("[알림] 재시작에 실패하였습니다.")
                
    #             try:
    #                 self.sock.close()
    #             except Exception as e:
    #                 print(e)
        
    #     timer = threading.Timer(1, self.watchdog_Camera)
    #     timer.daemon = True
    #     timer.start()


def main():
    # sys.argv.append("--remote-debugging-port=8000")
    app = QtWidgets.QApplication(sys.argv)
    
    currentTime = datetime.now()

    if (currentTime.year + currentTime.month/12) <= 2099:
        MainWindow = QtWidgets.QMainWindow()
        ex = waffleLauncher(MainWindow)
    else:
        w = ValvePopup()
        w.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
