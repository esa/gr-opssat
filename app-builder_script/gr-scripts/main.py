#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on 17/10/2019
Tom Mladenov, European Space Agency
"""

__author__ = 'Tom Mladenov, European Space Operations Centre ESA/ESOC'
__email__ = 'Tom.Mladenov@esa.int'

import os
import struct
import zmq
import sys
import time
from threading import Thread, Lock
from PyQt5.QtCore import (QCoreApplication, QObject, QRunnable, QThread, pyqtSignal, QEvent, Qt, QVariant, QTimer)
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog, QWidget, QListWidgetItem, QFileDialog, QTableWidgetItem
from PyQt5.uic import loadUi
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QImage, QIcon, QPixmap, QFont, QSyntaxHighlighter, QTextCharFormat, QColor, QBrush
import subprocess

import numpy as np
import argparse
import datetime
import collections
from crccheck.crc import Crc32c
import logging
import tempfile
import shutil
import requests
import json

SCRIPT = os.path.realpath(__file__)
HERE = os.path.dirname(SCRIPT)

NODES = {
			"1": "Nanomind",
			"2": "EPS dock",
			"3": "EPS ACU1",
			"4": "EPS ACU2",
			"5": "Nanocom",
			"6": "EPS PDU1",
			"7": "EPS PDU2"
}

api_bool = False
api_key = None

class Main(QMainWindow):


	def __init__(self, parent=None):
		super(Main, self).__init__(parent)
		eventLogger.info('Starting OPS-SAT UHF Desktop')
		gui = path + '/gui/gui.ui'
		eventLogger.info('Loading GUI file {GUI}'.format(GUI=gui))
		loadUi(gui, self)

		self.setWindowTitle('OPS-SAT Telemetry Desktop')
		self.setFixedSize(self.size())

		self.logo.setScaledContents(True)

		ops_sat_logo = QPixmap(path + '/gui/img/ESA_OPS_SAT.png')
		self.logo.setPixmap(ops_sat_logo)

		self.clear_tm_button.clicked.connect(self.clearTM)
  
		# code for buttons here
		self.start_uhf_reception_sample_button.clicked.connect(self.startUHFReceptionSample)
		self.uhf_process_sample = None
  
		self.start_uhf_reception_rtlsdr_button.clicked.connect(self.startUHFReceptionRTLSDR)
		self.uhf_process_rtlsdr = None

		self.start_uhf_reception_usrp_button.clicked.connect(self.startUHFReceptionUSRP)
		self.uhf_process_usrp = None
         
		self.start_demod_decode_button.clicked.connect(self.startDemodDecode)
		self.demod_process = None
		
		self.switch_api_button.clicked.connect(self.switchAPI)

		self.packet_history_table.setColumnCount(10)
		self.packet_history_table.setHorizontalHeaderLabels(['RX Time (UTC)', 'Type','Length', 'CRC OK', 'pri', 'src', 'dst', 'dst port', 'src port', 'flags'])
		packet_history_header = self.packet_history_table.horizontalHeader()
		packet_history_header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
		packet_history_header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
		packet_history_header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
		packet_history_header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
		packet_history_header.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeToContents)
		packet_history_header.setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeToContents)
		packet_history_header.setSectionResizeMode(6, QtWidgets.QHeaderView.ResizeToContents)
		packet_history_header.setSectionResizeMode(7, QtWidgets.QHeaderView.ResizeToContents)
		packet_history_header.setSectionResizeMode(8, QtWidgets.QHeaderView.ResizeToContents)
		packet_history_header.setSectionResizeMode(9, QtWidgets.QHeaderView.ResizeToContents)

		self.raw_history_table.setColumnCount(3)
		self.raw_history_table.setHorizontalHeaderLabels(['RX Time (UTC)', 'RAW data', 'Bytes'])
		raw_history_table_header = self.raw_history_table.horizontalHeader()
		raw_history_table_header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
		raw_history_table_header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
		raw_history_table_header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)


		self.adapter = TMadapter(self, "127.0.0.1", 38211)
		self.adapter.link.connect(self.updateLink)
		self.adapter.packet.connect(self.update)
		self.adapter.packet_count.connect(self.updatePacketCounter)
		self.adapter.start()

		self.host_label.setText(self.adapter.host)
		self.packet_counter_label.setText('Received packets: 0')

		eventLogger.info('GUI Thread started')


	def clearTM(self):
		self.adapter.recvd_packets = 0
		self.packet_history_table.clearContents()
		self.packet_history_table.setRowCount(0)
		self.raw_history_table.clearContents()
		self.raw_history_table.setRowCount(0)

		eventLogger.info('Telemetry counter has been reset to 0')


	def updatePacketCounter(self, count):
		self.packet_counter_label.setText('Received packets: ' + str(count))


	def updateLink(self, up):
		if up:
			self.link_label.setText('TM FLOW')
			self.link_label.setStyleSheet('background-color: rgb(0, 255, 0)')
		else:
			self.link_label.setText('NO TM')
			self.link_label.setStyleSheet('background-color: rgb(255, 0, 0)')


	def update(self, csp, crc):
		try:
			csp_crc = csp.getCRC32C() #calculate the CRC of the CSP packet
			sent_crc = int.from_bytes(crc, byteorder='big') #Check what was attached as a CRC

			if csp_crc == sent_crc: #Compare
				crc_ok = True

				if csp.isBeacon():
					temp_brd,\
					temp_pa,\
					last_rssi,\
					last_rferr,\
					tx_count,\
					rx_count,\
					tx_bytes,\
					rx_bytes,\
					active_conf,\
					boot_count,\
					boot_cause,\
					last_contact,\
					bgnd_rssi,\
					tx_duty,\
					tot_tx_count,\
					tot_rx_count,\
					tot_tx_bytes,\
					tot_rx_bytes =  csp.getBeaconContents()

					self.temp_brd_label.setText(str(temp_brd/10.0))
					self.temp_pa_label.setText(str(temp_pa/10.0))
					self.last_rssi_label.setText(str(last_rssi))
					self.last_rferr_label.setText(str(last_rferr))
					self.tx_count_label.setText(str(tx_count))
					self.rx_count_label.setText(str(rx_count))
					self.tx_bytes_label.setText(str(tx_bytes))
					self.rx_bytes_label.setText(str(rx_bytes))
					self.active_conf_label.setText(str(active_conf))
					self.boot_count_label.setText(str(boot_count))
					self.boot_cause_label.setText(str(boot_cause))
					self.last_contact_label.setText(str(last_contact))
					self.bgnd_rssi_label.setText(str(bgnd_rssi))
					self.tx_duty_label.setText(str(tx_duty))
					self.tot_tx_count_label.setText(str(tot_tx_count))
					self.tot_rx_count_label.setText(str(tot_rx_count))
					self.tot_tx_bytes_label.setText(str(tot_tx_bytes))
					self.tot_rx_bytes_label.setText(str(tot_rx_bytes))


					current_packet_count = self.packet_history_table.rowCount()
					self.packet_history_table.insertRow(current_packet_count)
					self.packet_history_table.setItem(current_packet_count, 0, QTableWidgetItem(str(datetime.datetime.utcnow())))
					self.packet_history_table.setItem(current_packet_count, 1, QTableWidgetItem('Beacon'))
					self.packet_history_table.setItem(current_packet_count, 2, QTableWidgetItem(str(csp.getLength())))
					self.packet_history_table.setItem(current_packet_count, 3, QTableWidgetItem(str(crc_ok)))
					self.packet_history_table.setItem(current_packet_count, 4, QTableWidgetItem(str(csp.priority)))
					self.packet_history_table.setItem(current_packet_count, 5, QTableWidgetItem(NODES[str(csp.source)]))
					self.packet_history_table.setItem(current_packet_count, 6, QTableWidgetItem(str(csp.destination)))
					self.packet_history_table.setItem(current_packet_count, 7, QTableWidgetItem(str(csp.dest_port)))
					self.packet_history_table.setItem(current_packet_count, 8, QTableWidgetItem(str(csp.source_port)))
					self.packet_history_table.setItem(current_packet_count, 9, QTableWidgetItem(str(csp.flags)))

					self.packet_history_table.item(current_packet_count, 3).setBackground(QtGui.QColor(0, 255, 0))
					self.packet_history_table.scrollToBottom()


					self.raw_history_table.insertRow(current_packet_count)
					self.raw_history_table.setItem(current_packet_count, 0, QTableWidgetItem(str(datetime.datetime.utcnow())))
					self.raw_history_table.setItem(current_packet_count, 1, QTableWidgetItem(str(csp.getHex())))
					self.raw_history_table.setItem(current_packet_count, 2, QTableWidgetItem(str(csp.getLength())))
					self.raw_history_table.scrollToBottom()

					parsed_data = '{iso_time},{temp_brd},{temp_pa},{last_rssi},{last_rferr},{tx_count},{rx_count},{tx_bytes},{rx_bytes},{active_conf},{boot_count},{boot_cause},{last_contact},{bgnd_rssi},{tx_duty},{tot_tx_count},{tot_rx_count},{tot_tx_bytes},{tot_rx_bytes}'.format(iso_time=datetime.datetime.utcnow().isoformat(),\
															temp_brd=temp_brd,\
															temp_pa=temp_pa,\
															last_rssi=last_rssi,\
															last_rferr=last_rferr,\
															tx_count=tx_count,\
															rx_count=rx_count,\
															tx_bytes=tx_bytes,\
															rx_bytes=rx_bytes,\
															active_conf=active_conf,\
															boot_count=boot_count,\
															boot_cause=boot_cause,\
															last_contact=last_contact,\
															bgnd_rssi=bgnd_rssi,\
															tx_duty=tx_duty,\
															tot_tx_count=tot_tx_count,\
															tot_rx_count=tot_rx_count,\
															tot_tx_bytes=tot_tx_bytes,\
															tot_rx_bytes=tot_rx_bytes)


					eventLogger.info('Received CSP beacon packet of length {LEN} bytes + 4 byte CRC32C check: OK'.format(LEN=csp.getLength()))
					raw_data = str(csp.getHex()) + str(crc.hex())
					raw_frame = '{iso_time},{data}'.format(iso_time=datetime.datetime.utcnow().isoformat(), data=raw_data)
					rawLogger.info(raw_frame)
					# API CALL
					if api_bool and (api_key is not None):
						try:
							api_url = 'https://opssat1.esoc.esa.int/frames-collector/add-frame/'
							api_token = api_key
							api_data = {'data': raw_frame}
							headers = {'Authorization': f'Token {api_token}', 'Content-Type': 'application/json'}
							response = requests.post(api_url, data=json.dumps(api_data), headers=headers)
							print(response.status_code)
							print(response.json())
						except Exception as e:
							print(f"Error sending raw data via api: {e}")
					parsedBeaconLogger.info(parsed_data)

				else:
					current_packet_count = self.packet_history_table.rowCount()
					self.packet_history_table.insertRow(current_packet_count)
					self.packet_history_table.setItem(current_packet_count, 0, QTableWidgetItem(str(datetime.datetime.utcnow())))
					self.packet_history_table.setItem(current_packet_count, 1, QTableWidgetItem('SPP over CSP'))
					self.packet_history_table.setItem(current_packet_count, 2, QTableWidgetItem(str(csp.getLength())))
					self.packet_history_table.setItem(current_packet_count, 3, QTableWidgetItem(str(crc_ok)))
					self.packet_history_table.setItem(current_packet_count, 4, QTableWidgetItem(str(csp.priority)))
					self.packet_history_table.setItem(current_packet_count, 5, QTableWidgetItem(NODES[str(csp.source)]))
					self.packet_history_table.setItem(current_packet_count, 6, QTableWidgetItem(str(csp.destination)))
					self.packet_history_table.setItem(current_packet_count, 7, QTableWidgetItem(str(csp.dest_port)))
					self.packet_history_table.setItem(current_packet_count, 8, QTableWidgetItem(str(csp.source_port)))
					self.packet_history_table.setItem(current_packet_count, 9, QTableWidgetItem(str(csp.flags)))

					self.packet_history_table.item(current_packet_count, 3).setBackground(QtGui.QColor(0, 255, 0))
					self.packet_history_table.scrollToBottom()

					self.raw_history_table.insertRow(current_packet_count)
					self.raw_history_table.setItem(current_packet_count, 0, QTableWidgetItem(str(datetime.datetime.utcnow())))
					self.raw_history_table.setItem(current_packet_count, 1, QTableWidgetItem(str(csp.getHex())))
					self.raw_history_table.setItem(current_packet_count, 2, QTableWidgetItem(str(csp.getLength())))
					self.raw_history_table.scrollToBottom()

					eventLogger.info('Received SPP over CSP packet of length {LEN} bytes + 4 byte CRC32C check: OK'.format(LEN=csp.getLength()))
					data = str(csp.getHex()) + str(crc.hex())
					raw_frame = '{iso_time},{data}'.format(iso_time=datetime.datetime.utcnow().isoformat(), data=data)
					rawLogger.info(raw_frame)
					# API CALL
					if api_bool and (api_key is not None):
						try:
							api_url = 'https://opssat1.esoc.esa.int/frames-collector/add-frame/'
							api_token = api_key
							api_data = {'data': raw_frame}
							headers = {'Authorization': f'Token {api_token}', 'Content-Type': 'application/json'}
							response = requests.post(api_url, data=json.dumps(api_data), headers=headers)
							print(response.status_code)
							print(response.json())
						except Exception as e:
							print(f"Error sending raw data via api: {e}")

			else:
				crc_ok = False

				current_packet_count = self.packet_history_table.rowCount()

				self.packet_history_table.insertRow(current_packet_count)
				self.packet_history_table.setItem(current_packet_count, 0, QTableWidgetItem(str(datetime.datetime.utcnow())))
				self.packet_history_table.setItem(current_packet_count, 1, QTableWidgetItem('--'))
				self.packet_history_table.setItem(current_packet_count, 2, QTableWidgetItem(str(csp.getLength())))
				self.packet_history_table.setItem(current_packet_count, 3, QTableWidgetItem(str(crc_ok)))
				self.packet_history_table.setItem(current_packet_count, 4, QTableWidgetItem(str(csp.priority)))
				self.packet_history_table.setItem(current_packet_count, 5, QTableWidgetItem(str(csp.source)))
				self.packet_history_table.setItem(current_packet_count, 6, QTableWidgetItem(str(csp.destination)))
				self.packet_history_table.setItem(current_packet_count, 7, QTableWidgetItem(str(csp.dest_port)))
				self.packet_history_table.setItem(current_packet_count, 8, QTableWidgetItem(str(csp.source_port)))
				self.packet_history_table.setItem(current_packet_count, 9, QTableWidgetItem(str(csp.flags)))
				self.packet_history_table.item(current_packet_count, 3).setBackground(QtGui.QColor(255, 0, 0))
				self.packet_history_table.scrollToBottom()

				self.raw_history_table.insertRow(current_packet_count)
				self.raw_history_table.setItem(current_packet_count, 0, QTableWidgetItem(str(datetime.datetime.utcnow())))
				self.raw_history_table.setItem(current_packet_count, 1, QTableWidgetItem(str(csp.getHex())))
				self.raw_history_table.setItem(current_packet_count, 2, QTableWidgetItem(str(csp.getLength())))
				self.raw_history_table.scrollToBottom()

				eventLogger.error('Received CSP packet of length {LEN} bytes - Failed CRC32C!'.format(LEN=str(csp.getLength())))
				#Don't write to any logs.
		except Exception as e:
			eventLogger.error('Error occured: {ERR}'.format(ERR=e))
   
	# -=-=-=- SAMPLE -=-=-=- 
	def startUHFReceptionSample(self):
		global api_bool
		if not api_bool:
			try:
				script_path = f'{HERE}/lib/uhf_rx_sample.py'
				self.uhf_process_sample = subprocess.Popen([f'{HERE}/../conda/bin/python', script_path])

				# Changer la couleur du bouton en vert uniquement si le processus démarre avec succès
				if self.uhf_process_sample.poll() is None:
					self.start_uhf_reception_sample_button.setStyleSheet('background-color: rgb(0, 255, 0);')
					eventLogger.info('UHF Reception started successfully.')
					self.checkProcessStatusUHF_sample()
				else:
					eventLogger.error('Failed to start UHF Reception process.')
					self.start_uhf_reception_sample_button.setStyleSheet('background-color: rgb(255, 0, 0);')
					
			except Exception as e:
				eventLogger.error('Error occurred while starting UHF Reception: {ERR}'.format(ERR=e))
				self.start_uhf_reception_sample_button.setStyleSheet('background-color: rgb(255, 0, 0);')
		else:
			eventLogger.error('Could not start reception simulation using sample while API output is active')

	def checkProcessStatusUHF_sample(self):
		if self.uhf_process_sample is not None and self.uhf_process_sample.poll() is None:
			QTimer.singleShot(1000, self.checkProcessStatusUHF_sample)
			self.start_uhf_reception_sample_button.setStyleSheet('background-color: rgb(0, 255, 0);')
		else:
			self.start_uhf_reception_sample_button.setStyleSheet('')
			self.uhf_process_sample = None

	# -=-=-=- RTL-SDR -=-=-=- 
	def startUHFReceptionRTLSDR(self):
		try:
			script_path = f'{HERE}/lib/uhf_rx_rtlsdr.py'
			self.uhf_process_rtlsdr = subprocess.Popen([f'{HERE}/../conda/bin/python', script_path])

			# Changer la couleur du bouton en vert uniquement si le processus démarre avec succès
			if self.uhf_process_rtlsdr.poll() is None:
				self.start_uhf_reception_rtlsdr_button.setStyleSheet('background-color: rgb(0, 255, 0);')
				eventLogger.info('UHF Reception started successfully.')
				self.checkProcessStatusUHF_rtlsdr()
			else:
				eventLogger.error('Failed to start UHF Reception process.')
				self.start_uhf_reception_rtlsdr_button.setStyleSheet('background-color: rgb(255, 0, 0);')
				
		except Exception as e:
			eventLogger.error('Error occurred while starting UHF Reception: {ERR}'.format(ERR=e))
			self.start_uhf_reception_rtlsdr_button.setStyleSheet('background-color: rgb(255, 0, 0);')

	def checkProcessStatusUHF_rtlsdr(self):
		if self.uhf_process_rtlsdr is not None and self.uhf_process_rtlsdr.poll() is None:
			QTimer.singleShot(1000, self.checkProcessStatusUHF_rtlsdr)
			self.start_uhf_reception_rtlsdr_button.setStyleSheet('background-color: rgb(0, 255, 0);')
		else:
			self.start_uhf_reception_rtlsdr_button.setStyleSheet('')
			self.uhf_process_rtlsdr = None

	# -=-=-=- USRP -=-=-=- 
	def startUHFReceptionUSRP(self):
		try:
			script_path = f'{HERE}/lib/uhf_rx_usrp.py'
			self.uhf_process_usrp = subprocess.Popen([f'{HERE}/../conda/bin/python', script_path])

			# Changer la couleur du bouton en vert uniquement si le processus démarre avec succès
			if self.uhf_process_usrp.poll() is None:
				self.start_uhf_reception_usrp_button.setStyleSheet('background-color: rgb(0, 255, 0);')
				eventLogger.info('UHF Reception started successfully.')
				self.checkProcessStatusUHF_usrp()
			else:
				eventLogger.error('Failed to start UHF Reception process.')
				self.start_uhf_reception_usrp_button.setStyleSheet('background-color: rgb(255, 0, 0);')
				
		except Exception as e:
			eventLogger.error('Error occurred while starting UHF Reception: {ERR}'.format(ERR=e))
			self.start_uhf_reception_usrp_button.setStyleSheet('background-color: rgb(255, 0, 0);')

	def checkProcessStatusUHF_usrp(self):
		if self.uhf_process_usrp is not None and self.uhf_process_usrp.poll() is None:
			QTimer.singleShot(1000, self.checkProcessStatusUHF_usrp)
			self.start_uhf_reception_usrp_button.setStyleSheet('background-color: rgb(0, 255, 0);')
		else:
			self.start_uhf_reception_usrp_button.setStyleSheet('')
			self.uhf_process_usrp = None

	# -=-=-=- DEMOD DECODE -=-=-=-
	def startDemodDecode(self):
		try:
			script_path = f'{HERE}/lib/demod_decode.py'
			self.demod_process = subprocess.Popen([f'{HERE}/../conda/bin/python', script_path])

			if self.demod_process.poll() is None:
				self.start_demod_decode_button.setStyleSheet('background-color: rgb(0, 255, 0);')
				eventLogger.info('Beacon demodulation/decoding script successfully started.')
				self.checkProcessStatusDEMOD()
			else:
				eventLogger.error('Failed to start demodulation/decoding script.')
				self.start_demod_decode_button.setStyleSheet('background-color: rgb(0, 255, 0);')
				
		except Exception as e:
			eventLogger.error('Error occurred while starting demodulation/decoding script: {ERR}'.format(ERR=e))
			self.start_demod_decode_button.setStyleSheet('background-color: rgb(255, 0, 0);')

	def checkProcessStatusDEMOD(self):
		if self.demod_process is not None and self.demod_process.poll() is None:
			QTimer.singleShot(1000, self.checkProcessStatusDEMOD)
			self.start_demod_decode_button.setStyleSheet('background-color: rgb(0, 255, 0);')
		else:
			self.start_demod_decode_button.setStyleSheet('')
			self.demod_process = None

	# -=-=-=- API -=-=-=-
	def switchAPI(self):
		global api_bool
		global api_key

		api_bool = not api_bool

		

		if api_bool and (self.uhf_process_sample == None):
			self.switch_api_button.setStyleSheet('background-color: rgb(0, 255, 0);')
			api_key = self.apikeyLineEdit.text()
			print(f'Sending output to API using api key: {api_key}')
		elif self.uhf_process_sample != None:
			eventLogger.error('Could not start API output if sample reception is ongoing')
		else:
			self.switch_api_button.setStyleSheet('')
			print(f'Turn OFF: Sending output to API')

class CSP(object):
	"""
	Reused from:
	https://github.com/daniestevez/gr-satellites/blob/master/python/csp_header.py
	"""

	def __init__(self, csp_bytes):
		if len(csp_bytes) < 4:
			raise ValueError("Malformed CSP packet (too short)")
		self.csp_bytes = csp_bytes
		csp = struct.unpack(">I", csp_bytes[0:4])[0]
		self.priority = (csp >> 30) & 0x3
		self.source = (csp >> 25) & 0x1f
		self.destination = (csp >> 20) & 0x1f
		self.dest_port = (csp >> 14) & 0x3f
		self.source_port = (csp >> 8) & 0x3f
		self.reserved = (csp >> 4) & 0xf
		self.hmac = (csp >> 3) & 1
		self.xtea = (csp >> 2) & 1
		self.rdp = (csp >> 1) & 1
		self.crc = csp & 1
		self.flags=int('{HMAC}{XTEA}{RDP}{CRC}'.format(HMAC=self.hmac, XTEA=self.xtea, RDP=self.rdp, CRC=self.crc))

	def toString(self):
		return ("""CSP header:
		Priority:\t\t{}
		Source:\t\t\t{}
		Destination:\t\t{}
		Destination port:\t{}
		Source port:\t\t{}
		Reserved field:\t\t{}
		HMAC:\t\t\t{}
		XTEA:\t\t\t{}
		RDP:\t\t\t{}
		CRC:\t\t\t{}""".format(
			self.priority, self.source, self.destination, self.dest_port,
			self.source_port, self.reserved, self.hmac, self.xtea, self.rdp,
			self.crc))

	def isBeacon(self):
		if self.priority == 3 and self.source == 5 and self.destination == 10 and self.dest_port == 31 and self.source_port==0 and self.getLength() == 58:
			return True
		else:
			return False

	def getCRC32C(self):
		calculated_CRC32C = Crc32c.calc(self.csp_bytes)
		return calculated_CRC32C

	def getLength(self):
		return len(self.csp_bytes)

	def getHex(self):
		return self.csp_bytes.hex()

	def getBeaconContents(self):
		if self.isBeacon():
			payload = struct.unpack('>4h 4I B H 2I h B 4I', self.csp_bytes[4:]) #nanocom beacon format
			return payload


class TMadapter(QThread):

	packet = pyqtSignal(object, object)
	link = pyqtSignal(bool)
	packet_count = pyqtSignal(int)

	recvd_packets = 0

	active = False
	host = None

	def __init__(self, parent, ip, port):
		QtCore.QThread.__init__(self, parent)
		self.parent = parent
		self.active = True

		self.context = zmq.Context()
		self.socket = self.context.socket(zmq.SUB)
		self.host = 'tcp://' + ip + ':' + str(port)
		self.socket.connect(self.host)
		self.socket.setsockopt_string(zmq.SUBSCRIBE, "")
		self.socket.setsockopt(zmq.RCVTIMEO, 15000) #Timeout set to 15s, beacon frame is radiated every 10s by the spacecraft

		eventLogger.info('Started listening on {HOST} for incoming packets from GR flowgraph'.format(HOST=self.host))

	def run(self):
		while self.active:
			try:
				data = self.socket.recv()
				crc = data[-4:] #4 last bytes are CRC32-C
				csp = CSP(data[:(len(data)-4)])#Everything but the last 4 bytes belongs to the CSP packet
				self.packet.emit(csp, crc)
				self.recvd_packets = self.recvd_packets + 1
				self.packet_count.emit(self.recvd_packets)
				self.link.emit(True)
			except Exception as e:
				eventLogger.warning('No packets received in the last 15 seconds...{ERR}'.format(ERR=e))
				self.link.emit(False)

def setup_logger(name, log_file, formatter, level=logging.INFO):
	fileHandler = logging.FileHandler(log_file)
	streamHandler = logging.StreamHandler()

	fileHandler.setFormatter(formatter)
	streamHandler.setFormatter(formatter)

	logger = logging.getLogger(name)
	logger.setLevel(level)
	logger.addHandler(fileHandler)
	logger.addHandler(streamHandler)

	return logger


if __name__ == '__main__':
    path = os.path.dirname(os.path.abspath(__file__))
    log_dir = tempfile.mkdtemp(prefix="log_OPSSAT")

    try:
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        eventLogger = setup_logger('first_logger', os.path.join(log_dir, 'gui_event.log'), formatter, level=logging.INFO)

        plainFormatter = logging.Formatter('%(message)s')
        rawLogger = setup_logger('second_logger', os.path.join(log_dir, 'raw.log'), plainFormatter, level=logging.INFO)
        parsedBeaconLogger = setup_logger('third_logger', os.path.join(log_dir, 'parsed_beacon.log'), plainFormatter, level=logging.INFO)
        

        a = QApplication(sys.argv)
        a.setWindowIcon(QIcon(os.path.join(log_dir, 'gui/img/1200px-ESA_logo_simple.png')))
        app = Main()
        app.show()
        a.exec_()
    finally:
        # Nettoyer les fichiers temporaires une fois que l'application est arrêtée
        shutil.rmtree(log_dir)
        os._exit(0)