import PyIndi
import time
import os
import socket
import sys
from PyQt5.QtCore import (QCoreApplication, QObject, QRunnable, QThread, QThreadPool, pyqtSignal, )
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog, QTableWidgetItem, QTableWidget
from PyQt5.uic import loadUi
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QImage
from PyQt5.QtGui import QPixmap, QStandardItemModel, QStandardItem
from PyQt5 import QtGui
import csv
import datetime
import keyboard
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

#start the server with: "indiserver -v indi_eqmod_telescope indi_gpsd"


hostIndi = "localhost"
portIndi = 7624

class IndiClient(PyIndi.BaseClient):
	def __init__(self):
		super(IndiClient, self).__init__()
		self.sender = SenderObject()

	def newDevice(self, d):
		self.sender.newDevice.emit(d)

	def newProperty(self, p):
		self.sender.newProperty.emit(p)

	def removeProperty(self, p):
		self.sender.removeProperty.emit(p.getName(), p.getDeviceName())

	def newBLOB(self, bp):
		#self.sender.newBlob.emit(bp)
		self.sender.newPropertyValue(bp)

	def newSwitch(self, svp):
		#self.sender.newSwitch.emit(svp)
		self.sender.newPropertyValue(svp)

	def newNumber(self, nvp):
		#self.sender.newNumber.emit(nvp)
		self.sender.newPropertyValue(nvp)

	def newText(self, tvp):
		#self.sender.newText.emit(tvp)
		self.sender.newPropertyValue(tvp)

	def newLight(self, lvp):
		#self.sender.newLight.emit(lvp)
		self.sender.newPropertyValue(lvp)

	def newMessage(self, d, m):
		self.sender.newMessage.emit(d, m)

	def serverConnected(self):
		self.sender.serverConnected.emit(True)

	def serverDisconnected(self, code):
		self.sender.serverConnected.emit(False)


class Main(QMainWindow):

	started = False

	def __init__(self, parent = None):
		super(Main, self).__init__(parent)
		loadUi('simple_gui.ui', self)
		self.setWindowTitle('indiviewer')
		self.BUTTON_EXPANDALL.clicked.connect(self.expandAll)
		self.BUTTON_COLLAPSEALL.clicked.connect(self.collapseAll)

		self.model = QStandardItemModel()
		self.rootNode = self.model.invisibleRootItem()
		self.treeview.setAlternatingRowColors(True)

		self.indiclient=IndiClient()
		self.indiclient.sender.newDevice.connect(self.newDevice)
		self.indiclient.sender.newProperty.connect(self.newProperty)
		self.indiclient.sender.removeProperty.connect(self.removeProperty)
		self.indiclient.sender.newPropertyValue.connect(self.newPropertyValue)
		#self.indiclient.sender.newBlob.connect(self.newBlob)
		#self.indiclient.sender.newSwitch.connect(self.newSwitch)
		#self.indiclient.sender.newNumber.connect(self.newNumber)
		#self.indiclient.sender.newText.connect(self.newText)
		#self.indiclient.sender.newLight.connect(self.newLight)
		self.indiclient.sender.newMessage.connect(self.newMessage)
		self.indiclient.sender.serverConnected.connect(self.serverConnected)

		self.indiclient.setServer(hostIndi, portIndi)
		self.indiclient.connectServer()

	def expandAll(self):
		self.treeview.expandAll()

	def collapseAll(self):
		self.treeview.collapseAll()

	def newDevice(self, d):
		device = QStandardItem(d.getDeviceName())
		self.rootNode.appendRow([device, None])
		self.treeview.setModel(self.model)

	def newProperty(self, p):
		#When we receive a new property from the SenderObject we first make a new QStandardItem
		property = QStandardItem(p.getName())
		#Then we check which device is related to the property and we look it up in the model
		devices = self.model.findItems(p.getDeviceName(), QtCore.Qt.MatchExactly)
		#There will only be one device result so we extract it from the list of results
		device = devices[0]

		if p.getType()==PyIndi.INDI_TEXT:
			tpy=p.getText()
			for t in tpy:
				property.appendRow([QStandardItem(t.name), QStandardItem(t.text)])
			device.appendRow([property,None])

		elif p.getType()==PyIndi.INDI_NUMBER:
			tpy=p.getNumber()
			for t in tpy:
				property.appendRow([QStandardItem(t.name),  QStandardItem(str(t.value))])
			device.appendRow([property,None])

		elif p.getType()==PyIndi.INDI_SWITCH:
			tpy=p.getSwitch()
			for t in tpy:
				property.appendRow([QStandardItem(t.name),  QStandardItem(str(t.s))])
			device.appendRow([property,None])

		elif p.getType()==PyIndi.INDI_LIGHT:
			tpy=p.getLight()
			for t in tpy:
				property.appendRow([QStandardItem(t.name),  QStandardItem(str(t.s))])
			device.appendRow([property,None])

		elif p.getType()==PyIndi.INDI_BLOB:
			tpy=p.getBLOB()
			for t in tpy:
				property.appendRow([QStandardItem(t.name),  QStandardItem(str(t.size))])
			device.appendRow([property,None])

		self.treeview.setModel(self.model)


	def removeProperty(self, name, device):
		devices = self.model.findItems(device, QtCore.Qt.MatchExactly)
		device = devices[0]
		for i in range(0, device.rowCount()):
			item = device.child(i, 0)
			if item != None:
				if item.text() == name:
					device.removeRow(i)
			self.treeview.setModel(self.model)

	'''
	def newBlob(self, bp):
		pass

	def newSwitch(self, svp):
		devices = self.model.findItems(svp.device, QtCore.Qt.MatchExactly)
		device = devices[0]
		j = 0
		for i in range(0, device.rowCount()):
			item = device.child(i, 0)
			if item != None:
				if item.text() == svp.name:
					for s in svp:
						item.setChild(j, 1, QStandardItem(str(s.s)))
						j = j + 1
		self.treeview.setModel(self.model)


	def newNumber(self, nvp):
		devices = self.model.findItems(nvp.device, QtCore.Qt.MatchExactly)
		device = devices[0]
		j = 0
		for i in range(0, device.rowCount()):
			item = device.child(i, 0)
			if item != None:
				if item.text() == nvp.name:
					for n in nvp:
						item.setChild(j, 1, QStandardItem(str(n.value)))

						j = j + 1
		self.treeview.setModel(self.model)


	def newText(self, tvp):
		devices = self.model.findItems(tvp.device, QtCore.Qt.MatchExactly)
		device = devices[0]
		j = 0
		for i in range(0, device.rowCount()):
			item = device.child(i, 0)
			if item != None:
				if item.text() == tvp.name:
					for t in tvp:
						item.setChild(j, 1, QStandardItem(str(t.text)))
						j = j + 1
		self.treeview.setModel(self.model)


	def newLight(self, lvp):
		devices = self.model.findItems(lvp.device, QtCore.Qt.MatchExactly)
		device = devices[0]
		j = 0
		for i in range(0, device.rowCount()):
			item = device.child(i, 0)
			if item != None:
				if item.text() == lvp.name:
					for l in lvp:
						item.setChild(j, 1, QStandardItem(str(l.s)))
						j = j + 1
		self.treeview.setModel(self.model)

		'''

	def newPropertyValue(self, pv):
		devices = self.model.findItems(pv.device, QtCore.Qt.MatchExactly)
		device = devices[0]
		j = 0
		for i in range(0, device.rowCount()):
			item = device.child(i, 0)
			if item != None:
				if item.text() == pv.name:
					for v in pv:
						if pv.getType == PyIndi.INDI_TEXT:
							item.setChild(j, 1, QStandardItem(str(v.text)))
						elif pv.getType == PyIndi.INDI_NUMBER:
							item.setChild(j, 1, QStandardItem(str(v.value)))
						elif pv.getType == PyIndi.INDI_SWITCH:
							item.setChild(j, 1, QStandardItem(str(v.s)))
						elif pv.getType ==PyIndi.INDI_LIGHT:
							item.setChild(j, 1, QStandardItem(str(v.s)))
						else:
							#We do not handle BLOBs
							pass

						j = j + 1
		#We update the treeview
		self.treeview.setModel(self.model)

	def newMessage(self, d, m):
		self.LOGGING_MESSAGE.append("new Message "+ d.messageQueue(m))

	def serverConnected(self, status):
		if status:
			self.LOGGING_MESSAGE.append("Connected to server!")
		else:
			self.LOGGING_MESSAGE.append("Disconnected from server!")


class SenderObject(QtCore.QObject):
	newDevice = pyqtSignal(object)
	newProperty = pyqtSignal(object)
	removeProperty = pyqtSignal(str, str) #single object didnt work for some reason
	newBlob = pyqtSignal(object)
	newSwitch = pyqtSignal(object)
	newNumber = pyqtSignal(object)
	newText = pyqtSignal(object)
	newLight = pyqtSignal(object)
	newMessage = pyqtSignal(object, object)
	serverConnected = pyqtSignal(bool)
	newPropertyValue = pyqtSignal(object)


if __name__ == '__main__':
	app = QApplication(sys.argv)
	window = Main()
	window.show()
	sys.exit(app.exec_())
