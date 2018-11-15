import sys
from PyQt5.QtWidgets import QApplication, QDialog, QMainWindow
from PyQt5.uic import loadUi
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QPixmap, QImage
import cv2

SIZE = None
FPS = None
MIN_DEPTH = None
MAX_DEPTH = None
COUNTDOWN_TIME = None


class mainwindow(QMainWindow):
	def __init__(self):
		super(mainwindow,self).__init__()
		loadUi('mainwindow.ui',self)
		self.fps = 24
		self.image = None
		self.btn_startcamera.clicked.connect(self.start_camera)
		self.btn_stopcamera.clicked.connect(self.stop_camera)
		self.in_countdownTime.valueChanged.connect(self.updateParameters)
		self.in_FPS.valueChanged.connect(self.updateParameters) 
		self.in_resolutionWidth.valueChanged.connect(self.updateParameters)
		self.in_resolutionHight.valueChanged.connect(self.updateParameters)
		self.in_minDepth.valueChanged.connect(self.updateParameters)
		self.in_maxDepth.valueChanged.connect(self.updateParameters)

	def updateParameters(self):
		global COUNTDOWN_TIME, FPS, MIN_DEPTH, MAX_DEPTH, SIZE
		COUNTDOWN_TIME = self.in_countdownTime.value()		
		FPS = self.in_FPS.value()
		SIZE = (self.in_resolutionWidth.value(), self.in_resolutionHight.value())
		MIN_DEPTH = self.in_minDepth.value()
		MAX_DEPTH = self.in_maxDepth.value()
		print(SIZE)

	def start_camera(self):
		self.capture = cv2.VideoCapture(0)
		#self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
		#self.capture.set(cv2.CAP_PROP_FRAME_ẂIDTH, 640)
		self.timer = QTimer(self)
		self.timer.timeout.connect(self.update_frame)
		self.timer.start(1000./self.fps)

	def update_frame(self):
		ret, self.image = self.capture.read()
		self.image = cv2.flip(self.image, 1)
		self.displayImage(self.image, 1)

	def displayImage(self, img, window=1):
		frame = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
		img = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
		pix = QPixmap.fromImage(img)
		self.lbl_video_frame.setPixmap(pix)

		# qFormat = QImage.Format_Indexed8
		# if(len(img.shape)==3):
		# 	if(img.shape[2]==4):
		# 		qFormat = QImage.Format_RGBA8888
		# 	else:
		# 		qFormat = QImage.Format_RGB888
		# outImage = QImage(img,img.shape[1],img.shape[0],img.strides[0],qFormat)
		# #BGR>>RGB
		# outImage = outImage.rgbSwapped()

		# if window==1:
		# 	self.lbl_video_frame.setPixmap(QPixmap.fromImage(outImage))
		# 	self.lbl_video_frame.setScaledContents(True)


	def stop_camera(self):
		self.timer.stop()
		self.capture.release()

if __name__ == "__main__":
	app = QApplication(sys.argv)
	ui = mainwindow()
	ui.setWindowTitle('Dataset Recorder')
	ui.show()
	sys.exit(app.exec_())
