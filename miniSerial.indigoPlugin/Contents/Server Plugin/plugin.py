#! /usr/bin/env python
# -*- coding: utf-8 -*-

import serial
import logging

class SerialPort:

    def __init__(self, name, serialUrl, baud_rate, stop_bits):
        self.logger = logging.getLogger("Plugin.SerialGateway")
        self.name = name
        self.serialUrl = serialUrl
        self.connSerial = None

        self.logger.debug(f"{self.name}: Serial Port URL is: {self.serialUrl}")

        try:
            self.connSerial = indigo.activePlugin.openSerial("miniSerial", serialUrl, baud_rate, stopbits=stop_bits, timeout=2, writeTimeout=1)
            if self.connSerial is None:
                self.logger.error(f"{self.name}: Failed to open serial port")
                return

        except Exception as e:
            self.logger.error(f"{self.name}: Exception opening serial port: {str(e)}")
            return

    def __del__(self):
        self.logger.debug("Serial stop called")
        if self.connSerial:
            self.connSerial.close()
            self.connSerial = None

    def send(self, cmd):
        self.logger.debug(f"Sending serial string: {cmd}")
        cmd = cmd + "\r"
        self.connSerial.write(cmd.encode())


class Plugin(indigo.PluginBase):

    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)

        pfmt = logging.Formatter('%(asctime)s.%(msecs)03d\t[%(levelname)8s] %(name)20s.%(funcName)-25s%(msg)s', datefmt='%Y-%m-%d %H:%M:%S')
        self.plugin_file_handler.setFormatter(pfmt)
        self.logLevel = int(self.pluginPrefs.get("logLevel", logging.INFO))
        self.indigo_log_handler.setLevel(self.logLevel)
        self.logger.debug(f"{self.logLevel =}")

        self.ports = {}

    ########################################
    # ConfigUI methods
    ########################################

    def closedPrefsConfigUi(self, valuesDict, userCancelled):
        if not userCancelled:
            self.logLevel = int(valuesDict.get("logLevel", logging.INFO))
            self.indigo_log_handler.setLevel(self.logLevel)
            self.logger.debug(f"{self.logLevel =}")

    ########################################
    # Device methods
    ########################################

    def deviceStartComm(self, dev):

        if dev.deviceTypeId == "serialPort":
            baud_rate = int(dev.pluginProps.get("baud_rate", 9600))
            stop_bits = int(dev.pluginProps.get("stop_bits", 1))
            port = SerialPort(dev.name, self.getSerialPortUrl(dev.pluginProps, "serialPort"), baud_rate, stop_bits)
            if port:
                self.ports[dev.id] = port
                dev.updateStateOnServer(key="status", value="Connected")
                dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
            else:
                self.dev.updateStateOnServer(key="status", value="Failed")
                self.dev.updateStateImageOnServer(indigo.kStateImageSel.SensorTripped)

        else:
            self.logger.error(f"{dev.name}: deviceStartComm: Unknown device type: {dev.deviceTypeId}")

    def deviceStopComm(self, dev):
        try:
            if dev.deviceTypeId == "serialPort":
                del self.ports[dev.id]
                dev.updateStateOnServer(key="status", value="None")
                dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
            else:
                self.logger.error(f"{dev.name}: deviceStopComm: Unknown device type: {dev.deviceTypeId}")
        except Exception as e:
            pass

    def validateDeviceConfigUi(self, valuesDict, typeId, devId):
        self.logger.debug(f"validateDeviceConfigUi: typeId = {typeId}, devId = {devId}")

        if typeId == "serialPort":
            valuesDict['address'] = self.getSerialPortUrl(valuesDict, 'serialPort')

        return True, valuesDict

    ########################################
    # Plugin Actions object callbacks (pluginAction is an Indigo plugin action instance)
    ########################################

    def sendString(self, pluginAction):
        sendString = indigo.activePlugin.substitute(pluginAction.props["sendString"])
        self.ports[pluginAction.deviceId].send(sendString)

