import sys
from PyQt5.QtWidgets import QApplication, QDialog, QMainWindow, QFileDialog, QWidget, QMessageBox, QTableWidget, QTableWidgetItem
from PyQt5.uic import loadUi
from PyQt5.QtCore import QTimer, QRegExp
from PyQt5.QtGui import QPixmap, QImage, QRegExpValidator
import numpy as np
import cv2
import json
import os
import pyrealsense2 as rs

SIZE = None
FPS = None
MIN_DEPTH = None
MAX_DEPTH = None
COUNTDOWN_TIME = None
CONFIG_FILE = 'config.json'
SAMPLES_FILE = '/samples.json'
PATH = ""

people_dataset = []
current_person_ID = -1
current_movement = ''
cTime = COUNTDOWN_TIME
SAVE_MP4 = False
PLAYING = False



class mainwindow(QMainWindow):
	def __init__(self):
		super(mainwindow,self).__init__(None)
		loadUi('mainwindow.ui',self)
		self.verifyCamera()		
		self.validate_path()
		self.getParameters()
		self.get_dataset_info()
		self.showMaximized()
		self.start_camera()
		self.fps = 24
		self.image = None		
		self.in_countdownTime.valueChanged.connect(self.updateParameters)
		self.in_FPS.valueChanged.connect(self.updateParameters) 
		self.in_resolutionWidth.valueChanged.connect(self.updateParameters)
		self.in_resolutionHight.valueChanged.connect(self.updateParameters)
		self.in_minDepth.valueChanged.connect(self.updateParameters)
		self.in_maxDepth.valueChanged.connect(self.updateParameters)
		self.cb_person.currentIndexChanged.connect(self.updateCurrentPerson)
		self.btn_addPerson.clicked.connect(self.addNewPerson)
		self.btn_addMovement.clicked.connect(self.addNewMovement)
		self.tb_movements.cellClicked.connect(self.set_currentMovement)
		self.btn_changePath.clicked.connect(self.changeDirectory)
		self.btn_startRecording.clicked.connect(self.startCountdown)
		self.btn_stopRecording.clicked.connect(self.stopRecord)
		self.btn_deleteRecord.clicked.connect(self.deleteRecord)
		self.btn_playRecord.clicked.connect(self.reproduceRecord)
		self.lbl_countdownTime.hide()
		self.lbl_recording.hide()
		self.lbl_playing.hide()
		self.lbl_noRecording.setStyleSheet('color: green')
		self.lbl_recording.setStyleSheet('color: red')
		self.lbl_playing.setStyleSheet('color: blue')
		self.btn_stopRecording.setEnabled(False)
		self.btn_deleteRecord.setEnabled(False)
		self.btn_playRecord.setEnabled(False)
		self.outRGB = []
		self.outDepth = []

		rx = QRegExp("[a-zA-Z0-9_]*")
		validator = QRegExpValidator(rx)
		self.in_newPerson.setValidator(validator)
		self.in_newMovement.setValidator(validator)

	def __del__(self):		
		self.stop_camera()

	
	def reproduceRecord(self):
		

	def enableUserInputs(self, boolSet):		
		self.btn_startRecording.setEnabled(boolSet)
		self.in_newPerson.setEnabled(boolSet)
		self.btn_addPerson.setEnabled(boolSet)
		self.in_newMovement.setEnabled(boolSet)
		self.btn_addMovement.setEnabled(boolSet)
		self.btn_changePath.setEnabled(boolSet)
		self.cb_person.setEnabled(boolSet)
		self.in_countdownTime.setEnabled(boolSet)
		self.in_FPS.setEnabled(boolSet)
		self.in_resolutionWidth.setEnabled(boolSet)
		self.in_resolutionHight.setEnabled(boolSet)
		self.in_minDepth.setEnabled(boolSet)
		self.in_maxDepth.setEnabled(boolSet)
		self.tb_movements.setEnabled(boolSet)
	
	def deleteRecord(self):
		self.updateSamplesFile(-1)
		sample_num = str(self.getSampleNumber())
		path_move = PATH+'/'+current_movement
		name = path_move+'/'+str(current_person_ID).zfill(2)+'_'+sample_num.zfill(4)
		if os.path.isfile(name + '_RGB.mp4'):
			os.remove(name + '_RGB.mp4')
		if os.path.isfile(name + '_D.mp4'):
			os.remove(name + '_D.mp4')


	def startCountdown(self):
		global cTime
		if current_person_ID==-1:
			choice = QMessageBox.warning(self, "Record Errror", "Please select person")
			return
		if current_movement=='':
			choice = QMessageBox.warning(self, "Record Errror", "Please select movement")
			return
		cTime = COUNTDOWN_TIME
		self.lbl_noRecording.hide()
		self.lbl_recording.hide()
		self.lbl_countdownTime.show()
		self.timerCountdown = QTimer(self)
		self.timerCountdown.timeout.connect(self.update_countdown)
		self.timerCountdown.start(1)
		self.enableUserInputs(False)
		self.btn_deleteRecord.setEnabled(False)
		self.btn_playRecord.setEnabled(False)

	def update_countdown(self):
		global cTime
		self.lbl_countdownTime.setText(str(cTime))		
		cTime -= 1
		if cTime == -1:
			self.lbl_countdownTime.hide()
			self.lbl_recording.show()
			self.timerCountdown.stop()
			self.lbl_countdownTime.setText("")
			self.startRecord()
		else:
			self.timerCountdown.start(1000)

	def stopRecord(self):
		global cTime, SAVE_MP4
		SAVE_MP4 = False
		cTime = COUNTDOWN_TIME
		self.timerCountdown.stop()
		self.lbl_countdownTime.hide()
		self.lbl_recording.hide()
		self.lbl_noRecording.show()
		self.enableUserInputs(True)
		if self.outRGB != []:
			self.outRGB.release()
		if self.outDepth != []:
			self.outDepth.release()
		self.updateSamplesFile(1)
		self.btn_deleteRecord.setEnabled(True)
		self.btn_stopRecording.setEnabled(False)
		self.btn_playRecord.setEnabled(True)

	def updateSamplesFile(self, add):
		global people_dataset
		for name in people_dataset.keys():
			if people_dataset[name]["ID"] == current_person_ID:
				people_dataset[name]["samples"][current_movement] += add
				break
		try:
			os.remove(PATH+SAMPLES_FILE)
		except:
			pass
		with open(PATH+SAMPLES_FILE, 'w') as f:
			json.dump(people_dataset, f, indent=4) 
		self.updateCurrentPerson()

	def getSampleNumber(self):
		global people_dataset
		for name in people_dataset.keys():
			if people_dataset[name]["ID"] == current_person_ID:
				samples = people_dataset[name]["samples"][current_movement]
				return samples


	def startRecord(self):
		global SAVE_MP4
		sample_num = str(self.getSampleNumber())
		path_move = PATH+'/'+current_movement
		if not os.path.exists(path_move):
			os.makedirs(path_move)
		name = path_move+'/'+str(current_person_ID).zfill(2)+'_'+sample_num.zfill(4)
		fourcc = cv2.VideoWriter_fourcc(*'DIVX')  # 'x264' doesn't work
		self.outRGB = cv2.VideoWriter(name + '_RGB.mp4',fourcc, FPS, (SIZE[0], SIZE[1]), True) 
		self.outDepth = cv2.VideoWriter(name + '_D.mp4',fourcc, FPS, (SIZE[0], SIZE[1]), False)
		SAVE_MP4 = True
		self.btn_stopRecording.setEnabled(True)
		

	def changeDirectory(self):
		global PATH
		self.stop_camera()
		PATH = QFileDialog.getExistingDirectory(self, "Select directory", "/home/")
		print(PATH)
		self.start_camera()
		with open(CONFIG_FILE, 'r') as f:
			data = json.load(f)
		data["capture parameters"]["path"] = PATH
		self.lbl_path.setText(PATH)
		os.remove(CONFIG_FILE)
		with open(CONFIG_FILE, 'w') as f:
			json.dump(data, f, indent=4)

	def set_currentMovement(self, row, column):
		global current_movement		
		item = self.tb_movements.item(row, column)
		current_movement = item.text()
		self.lbl_currMove.setText(current_movement)
		
	def addNewMovement(self):
		global people_dataset
		newMovement = self.in_newMovement.text()
		for key in people_dataset.keys():
			people_dataset[key]["samples"][newMovement] = 0
		try:
			os.remove(PATH+SAMPLES_FILE)
		except:
			pass
		with open(PATH+SAMPLES_FILE, 'w') as f:
			json.dump(people_dataset, f, indent=4) 
		self.updateCurrentPerson()
		self.in_newMovement.setText('')

	def addNewPerson(self):
		global people_dataset
		newPersonName = self.in_newPerson.text()
		people_dataset[newPersonName] = {}
		people_dataset[newPersonName]["ID"] = len(people_dataset)-1
		people_dataset[newPersonName]["samples"] = {}
		if len(people_dataset)>1:
			name = list(people_dataset.keys())[0]
			for key in people_dataset[name]["samples"].keys():
				people_dataset[newPersonName]["samples"][key] = 0
		try:
			os.remove(PATH+SAMPLES_FILE)
		except:
			pass
		with open(PATH+SAMPLES_FILE, 'w') as f:
			json.dump(people_dataset, f, indent=4) 
		self.get_dataset_info()
		self.in_newPerson.setText('')


	def updateCurrentPerson(self):
		global current_person_ID
		cPersonName = self.cb_person.currentText ()
		self.lbl_IDperson.setText('')
		if cPersonName != "Select":
			current_person_ID = people_dataset[cPersonName]["ID"]
			self.lbl_IDperson.setText(str(current_person_ID))
			self.tb_movements.clearContents()
			data = people_dataset[cPersonName]["samples"]
			self.tb_movements.setRowCount(len(data))
			self.tb_movements.setHorizontalHeaderLabels(['Movement','Samples'])     
			for n, key in enumerate(sorted(data.keys())):
				newitem = QTableWidgetItem(str(data[key]))
				self.tb_movements.setItem(n,1,newitem)
				newitem = QTableWidgetItem(key)
				self.tb_movements.setItem(n,0,newitem)


	def getParameters(self):
		global COUNTDOWN_TIME, FPS, MIN_DEPTH, MAX_DEPTH, SIZE, CONFIG_FILE
		with open(CONFIG_FILE, 'r') as f:
			data = json.load(f)
		COUNTDOWN_TIME = data["capture parameters"]["countdown time"]
		FPS = data["capture parameters"]["FPS"]
		SIZE = (data["capture parameters"]["resolution width"], data["capture parameters"]["resolution higth"])
		MIN_DEPTH = data["capture parameters"]["min depth"]
		MAX_DEPTH = data["capture parameters"]["max depth"]
		f.close()
		self.in_countdownTime.setValue(COUNTDOWN_TIME)
		self.in_FPS.setValue(FPS)
		self.in_resolutionWidth.setValue(SIZE[0])
		self.in_resolutionHight.setValue(SIZE[1])
		self.in_minDepth.setValue(MIN_DEPTH)
		self.in_maxDepth.setValue(MAX_DEPTH)

	def updateParameters(self):
		global COUNTDOWN_TIME, FPS, MIN_DEPTH, MAX_DEPTH, SIZE, CONFIG_FILE
		COUNTDOWN_TIME = self.in_countdownTime.value()		
		FPS = self.in_FPS.value()
		SIZE = (self.in_resolutionWidth.value(), self.in_resolutionHight.value())
		MIN_DEPTH = self.in_minDepth.value()
		MAX_DEPTH = self.in_maxDepth.value()
		#save capture parameters in config.json
		with open(CONFIG_FILE, 'r') as f:
			data = json.load(f)
			data["capture parameters"]["countdown time"] = COUNTDOWN_TIME
			data["capture parameters"]["FPS"] = FPS
			data["capture parameters"]["resolution width"] = SIZE[0]
			data["capture parameters"]["resolution higth"] = SIZE[1]
			data["capture parameters"]["min depth"] = MIN_DEPTH
			data["capture parameters"]["max depth"] = MAX_DEPTH
		os.remove(CONFIG_FILE)
		with open(CONFIG_FILE, 'w') as f:
			json.dump(data, f, indent=4)
		#print(SIZE)

	def verifyCamera(self):
		#Verify realsense is connected
		ctx = rs.context()
		if len(ctx.devices) == 0:
			choice = QMessageBox.warning(self, "Camera not found", "Please connect RealSense camera")
			sys.exit()

	def start_camera(self):				
		# Configure depth and color streams
		self.pipeline = rs.pipeline()
		config = rs.config()
		config.enable_stream(rs.stream.depth, SIZE[0], SIZE[1], rs.format.z16, FPS)
		config.enable_stream(rs.stream.color, SIZE[0], SIZE[1], rs.format.bgr8, FPS)
		#fourcc = cv2.VideoWriter_fourcc(*'DIVX')  # 'x264' doesn't work
		#self.outRGB = cv2.VideoWriter(name + '_rgb.mp4',fourcc, FPS, (SIZE[0], SIZE[1]), True) 
		#self.outDepth = cv2.VideoWriter(name + '_dpt.mp4',fourcc, FPS, (SIZE[0], SIZE[1]), False)
		# Start streaming
		self.pipeline.start(config)
		self.timer = QTimer(self)
		self.timer.timeout.connect(self.update_frame)
		self.timer.start(1000./FPS)


	def update_frame(self):
		if not PLAYING:
			frames = self.pipeline.wait_for_frames()
			depth_frame = frames.get_depth_frame()
			color_frame = frames.get_color_frame()
			if not depth_frame or not color_frame:
				return

			depth_image_temp = np.asanyarray(depth_frame.get_data())
			self.depth_image = cv2.convertScaleAbs(depth_image_temp, alpha=0.03)
			self.color_image = np.asanyarray(color_frame.get_data())

			self.depth_image[self.depth_image<MIN_DEPTH] = MAX_DEPTH
			self.depth_image[self.depth_image>MAX_DEPTH] = MAX_DEPTH
			self.depth_image -= MIN_DEPTH
			self.depth_image *= int((255/(MAX_DEPTH-MIN_DEPTH)))
			
			if SAVE_MP4:
				self.outRGB.write(self.color_image)
				self.outDepth.write(self.depth_image)
			
			self.displayImage(self.color_image, self.depth_image, 1)

	def displayImage(self, img_rgb, img_d, window=1):
		img = cv2.resize(img_rgb,(int(480),int(360)))
		frame = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)		
		img = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
		pix = QPixmap.fromImage(img)
		self.lbl_video_rgb.setPixmap(pix)
		img = cv2.resize(img_d,(int(480),int(360)))
		frame = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)		
		img = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
		pix = QPixmap.fromImage(img)
		self.lbl_video_depth.setPixmap(pix)


	def stop_camera(self):
		self.timer.stop()
		self.pipeline.stop()
		#self.outRGB.release()
		#self.outDepth.release()

		# frame = 255*np.zeros(self.color_image.shape)
		# img = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
		# pix = QPixmap.fromImage(img)
		# self.lbl_video_rgb.setPixmap(pix)	
		# self.lbl_video_depth.setPixmap(pix)	

	def validate_path(self):
		global PATH
		with open(CONFIG_FILE, 'r') as f:
			data = json.load(f)
			path_read = data["capture parameters"]["path"]
			if path_read == "":
				print("no path in config.json")
				PATH = self.ask2path("Have not cofigured yet a path for the dataset. ")
			else:
				if os.path.isdir(path_read):
					PATH = path_read
				else:
					PATH = self.ask2path("The readed path in config file does not exist. ")
		data["capture parameters"]["path"] = PATH
		self.lbl_path.setText(PATH)
		os.remove(CONFIG_FILE)
		with open(CONFIG_FILE, 'w') as f:
			json.dump(data, f, indent=4)

	def ask2path(self, msg_err):
		msg_err = msg_err + "Please select a directory."
		choice = QMessageBox.question(self, "Path for dataset", msg_err, QMessageBox.Yes | QMessageBox.No)
		if choice == QMessageBox.Yes:
			path_selected = QFileDialog.getExistingDirectory(self, "Select directory", "/home/")
			print(path_selected)
			return path_selected
		else:
			sys.exit()

	def get_dataset_info(self):
		global people_dataset
		try:
			f=open(PATH+SAMPLES_FILE, 'r')
		except:
			choice = QMessageBox.warning(self, "New dataset", "Please add a new person and movement to start a dataset")
			return 0
		people_dataset = json.load(f)
		f.close()
		self.cb_person.clear()
		if len(people_dataset) != 0:
			self.cb_person.addItems(["Select"]+list(people_dataset.keys()))


# 		# dialog = dialogPath(parent=self, msg_err=msg_err)
# 		# self.hide()
# 		# print("hide")
# 		# dialog.exec_()
# 		# print("esperando")
# 		# self.show()
# 		# path = dialog.path_selected
# 		# print(path)
# 		# return path

# class dialogPath(QDialog):
# 	def __init__(self, parent, msg_err):
# 		super(dialogPath,self).__init__(parent)
# 		loadUi('dialogPath.ui',self)
# 		self.lbl_msg_err.setText(msg_err)
# 		self.path_selected = None
# 		#self.buttonBox.accepted.connect(self.selectFolder)
# 		#self.buttonBox.rejected.connect(self.exit)
# 		#self.show()	
# 		print("dialogue")

# 	def selectFolder(self):
# 		self.path_selected = QFileDialog.getExistingDirectory(self, "Select directory", "/home/")

# 	def exit(self):
# 		sys.exit(app.exec_())


if __name__ == "__main__":
	app = QApplication(sys.argv)
	ui = mainwindow()
	ui.setWindowTitle('Dataset Recorder')
	ui.show()	
	sys.exit(app.exec_())



