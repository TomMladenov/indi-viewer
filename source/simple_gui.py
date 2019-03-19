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

#INDI property list
#------------------------------
TELESCOPE_SIMPROP = "SIMULATION"
POLLING_PROP = "POLLING_PERIOD"
GPS_REFRESH_PROP = "GPS_REFRESH_PERIOD"
ACTIVE_DEVICES_PROP = "ACTIVE_DEVICES"
#------------------------------


#Global AZEQ mount parameters:
#------------------------------
mountName="EQMod Mount"
mountConnection = None
mountDevice = None
#------------------------------


#Global GPS parameters:
#------------------------------
gpsName="GPSD"
gpsConnection = None
gpsDevice = None
#------------------------------


hostIndi = "localhost"
portIndi = 7624

def strISState(s):
	if (s == PyIndi.ISS_OFF):
		return "Off"
	else:
		return "On"
def strIPState(s):
	if (s == PyIndi.IPS_IDLE):
		return "Idle"
	elif (s == PyIndi.IPS_OK):
		return "Ok"
	elif (s == PyIndi.IPS_BUSY):
		return "Busy"
	elif (s == PyIndi.IPS_ALERT):
		return "Alert"


class IndiClient(PyIndi.BaseClient):
	def __init__(self):
		super(IndiClient, self).__init__()
		self.sender = SenderObject()

	def newDevice(self, d):
		global mountDevice
		global gpsDevice
		if (d.getDeviceName()==mountName):
			mountDevice=d #We catch the mount device
		elif (d.getDeviceName()==gpsName):
			gpsDevice=d #We catch the gps device
		print("New device ", d.getDeviceName())
		self.sender.newDevice.emit(d)

	def newProperty(self, p):
		global mountName
		global mountConnection
		global gpsName
		global gpsConnection

		# we catch the "CONNECTION" property of the mount and the GPS
		if (p.getDeviceName()==mountName and p.getName() == "CONNECTION"):
			mountConnection=p.getSwitch()
		elif (p.getDeviceName()==gpsName and p.getName() == "CONNECTION"):
			gpsConnection=p.getSwitch()
		print("New property ", p.getName(), " for device ", p.getDeviceName())
		self.sender.newProperty.emit(p)

	def removeProperty(self, p):
		self.sender.removeProperty.emit(p.getName(), p.getDeviceName())

	def newBLOB(self, bp):
		self.sender.newBlob.emit(bp)

	def newSwitch(self, svp):
		self.sender.newSwitch.emit(svp)

	def newNumber(self, nvp):
		global newval
		global prop
		prop=nvp
		newval=True
		self.sender.newNumber.emit(nvp)

	def newText(self, tvp):
		self.sender.newText.emit(tvp)

	def newLight(self, lvp):
		self.sender.newLight.emit(lvp)

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
		self.setWindowTitle('INDI TELESCOPE DRIVER MONITORING')
		self.BUTTON_EXPANDALL.clicked.connect(self.expandAll)
		self.BUTTON_COLLAPSEALL.clicked.connect(self.collapseAll)
		#self.BUTTON_ENABLESIM.clicked.connect(self.enableSim)
		#self.BUTTON_DISABLESIM.clicked.connect(self.disableSim)
		#self.BUTTON_CONNECT.clicked.connect(self.connect)
		#self.BUTTON_DISCONNECT.clicked.connect(self.disconnect)

		self.model = QStandardItemModel()
		self.rootNode = self.model.invisibleRootItem()
		#self.treeview.setAlternatingRowColors(True)

		self.indiclient=IndiClient()
		self.indiclient.sender.newDevice.connect(self.newDevice)
		self.indiclient.sender.newProperty.connect(self.newProperty)
		self.indiclient.sender.removeProperty.connect(self.removeProperty)
		self.indiclient.sender.newBlob.connect(self.newBlob)
		self.indiclient.sender.newSwitch.connect(self.newSwitch)
		self.indiclient.sender.newNumber.connect(self.newNumber)
		self.indiclient.sender.newText.connect(self.newText)
		self.indiclient.sender.newLight.connect(self.newLight)
		self.indiclient.sender.newMessage.connect(self.newMessage)
		self.indiclient.sender.serverConnected.connect(self.serverConnected)

		self.indiclient.setServer(hostIndi, portIndi)
		#self.indiclient.watchDevice()
		self.indiclient.connectServer()

		#Wait until gps and mount connection propetries are available
		while not(mountConnection):
			time.sleep(0.05)

		while not(gpsConnection):
			time.sleep(0.05)

		self.enableSim() #Set mount to simulation mode
		self.connectDevice(mountDevice, mountConnection)
		self.setPolling(150.0) #Set polling of 150 ms

		self.connectDevice(gpsDevice, gpsConnection)
		self.setGpsUpdate(1.0) #Set gps updaterate to 1 second
		self.setSnoopDevices(mountDevice, "GPSD", "Dome Simulator") #Set mount to SNOOP properties from GPSD

	def expandAll(self):
		self.treeview.expandAll()

	def collapseAll(self):
		self.treeview.collapseAll()

	def enableSim(self):
		sim=mountDevice.getSwitch(TELESCOPE_SIMPROP)
		while not(sim):
			time.sleep(0.005)
			sim=mountDevice.getSwitch(TELESCOPE_SIMPROP)

		sim[0].s=PyIndi.ISS_ON  # the "ENABLE" switch
		sim[1].s=PyIndi.ISS_OFF # the "DISABLE" switch
		self.indiclient.sendNewSwitch(sim)

	def disableSim(self):
		sim=mountDevice.getSwitch(TELESCOPE_SIMPROP)
		while not(sim):
			time.sleep(0.005)
			sim=mountDevice.getSwitch(TELESCOPE_SIMPROP)

		sim[0].s=PyIndi.ISS_OFF  # the "ENABLE" switch
		sim[1].s=PyIndi.ISS_ON # the "DISABLE" switch
		self.indiclient.sendNewSwitch(sim)

	def connectDevice(self, deviceProperty, connectionProperty):
		if not(deviceProperty.isConnected()):
			connectionProperty[0].s=PyIndi.ISS_ON
			connectionProperty[1].s=PyIndi.ISS_OFF
			self.indiclient.sendNewSwitch(connectionProperty)

	def disconnectDevice(self, deviceProperty, connectionProperty):
		if 	deviceProperty.isConnected():
			connectionProperty[0].s=PyIndi.ISS_OFF
			connectionProperty[1].s=PyIndi.ISS_ON
			self.indiclient.sendNewSwitch(connectionProperty)

	def setPolling(self, float):
		p=mountDevice.getNumber(POLLING_PROP)
		while not(p):
			time.sleep(0.5)
			p=mountDevice.getNumber(POLLING_PROP)

		p[0].value=float  # the "ENABLE" switch
		self.indiclient.sendNewNumber(p)

	def setGpsUpdate(self, period):
		p=gpsDevice.getNumber(GPS_REFRESH_PROP)
		while not(p):
			time.sleep(0.5)
			p=gpsDevice.getNumber(GPS_REFRESH_PROP)

		p[0].value=period  # the "ENABLE" switch
		self.indiclient.sendNewNumber(p)

	def setSnoopDevices(self, mainDevice, snoop1, snoop2): #Not snoopdogg
		p=mainDevice.getText(ACTIVE_DEVICES_PROP)
		while not(p):
			time.sleep(0.01)
			p=mainDevice.getText(ACTIVE_DEVICES_PROP)

		p[0].text = snoop1
		p[1].text = snoop2
		self.indiclient.sendNewText(p)

	def newDevice(self, d):
		device = QStandardItem(d.getDeviceName())
		self.rootNode.appendRow([ device, None ])
		self.treeview.setModel(self.model)

	def newProperty(self, p):
		property = QStandardItem(p.getName())
		devices = self.model.findItems(p.getDeviceName(), QtCore.Qt.MatchExactly)
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
		if svp.device == gpsName:
			if svp.name == 'CONNECTION':
				if svp[0].s == PyIndi.ISS_ON:
					self.LABEL_GPSCONNECTED.setText("GPS ONLINE")
					self.LABEL_GPSCONNECTED.setStyleSheet("background-color: rgb(0, 255, 0);")
				else:
					self.LABEL_GPSCONNECTED.setText("GPS OFFLINE")
					self.LABEL_GPSCONNECTED.setStyleSheet("background-color: rgb(255, 0, 0);")

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

		if nvp.device == gpsName:
			if nvp.name == 'GEOGRAPHIC_COORD':
				self.LABEL_LATITUDE.setText('Latitude: ' + 	str(nvp[0].value) )
				self.LABEL_LONGITUDE.setText('Longitude: ' + str(nvp[1].value))
				self.LABEL_ELEVATION.setText('Elevation: ' + str(nvp[2].value))
			if nvp.name == 'CONNECTION':
				if nvp[0].value == 1:
					self.LABEL_GPSCONNECTED.setText("GPS ONLINE")
					self.LABEL_GPSCONNECTED.setStyleSheet("background-color: rgb(0, 255, 0);")
				else:
					self.LABEL_GPSCONNECTED.setText("GPS OFFLINE")
					self.LABEL_GPSCONNECTED.setStyleSheet("background-color: rgb(255, 0, 0);")



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

		if tvp.device == gpsName:
			if tvp.name == 'TIME_UTC':
				self.LABEL_UTCTIME.setText('UTC Time: ' + tvp[0].text)
				self.LABEL_UTCOFFSET.setText('UTC Offset: ' + tvp[1].text)
			if tvp.name == 'GPS_STATUS':
				if tvp[0].text == '3D FIX':
					self.LABEL_GPSFIX.setText("3D FIX")
					self.LABEL_GPSFIX.setStyleSheet("background-color: rgb(0, 255, 0);")
				else:
					self.LABEL_GPSFIX.setText("NO FIX")
					self.LABEL_GPSFIX.setStyleSheet("background-color: rgb(255, 0, 0);")

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

	def newMessage(self, d, m):
		self.LOGGING_MESSAGE.append("new Message "+ d.messageQueue(m))

	def serverConnected(self, status):
		if status:
			self.LABEL_SERVERSTATUS.setText("MAIN SERVER RUNNING")
			self.LABEL_SERVERSTATUS.setStyleSheet("background-color: rgb(0, 255, 0);")
			self.LABEL_IPINFO.setText(hostIndi + ":" + str(portIndi))
		else:
			self.LABEL_SERVERSTATUS.setText("MAIN SERVER DOWN")
			self.LABEL_SERVERSTATUS.setStyleSheet("background-color: rgb(255, 0, 0);")


class SenderObject(QtCore.QObject):
	newDevice = pyqtSignal(object)
	newProperty = pyqtSignal(object)
	removeProperty = pyqtSignal(str, str) #single object didnt work
	newBlob = pyqtSignal(object)
	newSwitch = pyqtSignal(object)
	newNumber = pyqtSignal(object)
	newText = pyqtSignal(object)
	newLight = pyqtSignal(object)
	newMessage = pyqtSignal(object, object)
	serverConnected = pyqtSignal(bool)


if __name__ == '__main__':
	app = QApplication(sys.argv)
	window = Main()
	window.show()
	sys.exit(app.exec_())
