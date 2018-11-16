import sys
from PyQt5.QtWidgets import QApplication, QDialog, QMainWindow, QFileDialog, QWidget, QMessageBox, QTableWidget, QTableWidgetItem
from PyQt5.uic import loadUi
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QPixmap, QImage
import cv2
import json
import os

SIZE = None
FPS = None
MIN_DEPTH = None
MAX_DEPTH = None
COUNTDOWN_TIME = None
CONFIG_FILE = 'config.json'
SAMPLES_FILE = 'samples.json'
PATH = ""

people_dataset = []
current_person_ID = -1
current_movement = ''



class mainwindow(QMainWindow):
	def __init__(self):
		super(mainwindow,self).__init__(None)
		loadUi('mainwindow.ui',self)
		self.validate_path()
		self.get_dataset_info()
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
		self.cb_person.currentIndexChanged.connect(self.updateCurrentPerson)
		self.btn_addPerson.clicked.connect(self.addNewPerson)
		self.btn_addMovement.clicked.connect(self.addNewMovement)
		self.tb_movements.cellClicked.connect(self.set_currentMovement)

	def set_currentMovement(self, row, column):
		global current_movement		
		item = self.tb_movements.item(row, column)
		current_movement = item.text()
		
	def addNewMovement(self):
		global people_dataset
		newMovement = self.in_newMovement.text()
		for key in people_dataset.keys():
			people_dataset[key]["samples"][newMovement] = 0
		try:
			os.remove(SAMPLES_FILE)
		except:
			pass
		with open(SAMPLES_FILE, 'w') as f:
		    json.dump(people_dataset, f, indent=4) 
		self.updateCurrentPerson()

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
			os.remove(SAMPLES_FILE)
		except:
			pass
		with open(SAMPLES_FILE, 'w') as f:
		    json.dump(people_dataset, f, indent=4) 
		self.get_dataset_info()


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

	def stop_camera(self):
		self.timer.stop()
		self.capture.release()

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
			f=open(SAMPLES_FILE, 'r')
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



