#! /usr/bin/env python
# -*- coding: utf-8 -*-

import serial
import logging

########################################
class SerialPort:
########################################

    def __init__(self, name, serialUrl):
        self.logger = logging.getLogger("Plugin.SerialGateway")
        self.name = name
        self.serialUrl = serialUrl
        self.connSerial = None

        self.logger.debug(u"{}: Serial Port URL is: {}".format(self.name, self.serialUrl))

        try:
            self.connSerial = indigo.activePlugin.openSerial(u"miniSerial", serialUrl, 9600, stopbits=1, timeout=2, writeTimeout=1)
            if self.connSerial is None:
                self.logger.error(u"{}: Failed to open serial port".format(self.name))
                return None

        except Exception, e:
            self.logger.error(u"{}: Exception opening serial port: {}".format(self.name, str(e)))
            return None

    def __del__(self):
        self.logger.debug(u"Serial stop called")
        if self.connSerial:
            self.connSerial.close()
            self.connSerial = None  
       
    def send(self, cmd):
        self.logger.debug(u"Sending serial string: %s" % cmd)
        cmd = cmd + "\r"
        self.connSerial.write(str(cmd))



class Plugin(indigo.PluginBase):

    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)

        pfmt = logging.Formatter('%(asctime)s.%(msecs)03d\t[%(levelname)8s] %(name)20s.%(funcName)-25s%(msg)s', datefmt='%Y-%m-%d %H:%M:%S')
        self.plugin_file_handler.setFormatter(pfmt)

        try:
            self.logLevel = int(self.pluginPrefs[u"logLevel"])
        except:
            self.logLevel = logging.INFO
        self.indigo_log_handler.setLevel(self.logLevel)
        self.logger.debug(u"logLevel = {}".format(self.logLevel))
        
        self.ports = {}
        
    def startup(self):
        self.logger.info(u"Starting up miniSerial")
                    
            
    def shutdown(self):
        self.logger.info(u"Shutting down Lutron")


    def deviceStartComm(self, dev):
                
        if dev.deviceTypeId == "serialPort":
            port = SerialPort(dev.name, self.getSerialPortUrl(dev.pluginProps, u"serialPort"))
            if port:
                self.ports[dev.id] = port           
                dev.updateStateOnServer(key="status", value="Connected")
                dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
            else:
                self.dev.updateStateOnServer(key="status", value="Failed")
                self.dev.updateStateImageOnServer(indigo.kStateImageSel.SensorTripped)
                      
        else:
            self.logger.error(u"{}: deviceStartComm: Unknown device type: {}".format(dev.name, dev.deviceTypeId))

    def deviceStopComm(self, dev):
        try:
            if dev.deviceTypeId == "serialPort":
                del self.ports[dev.id]
                dev.updateStateOnServer(key="status", value="None")
                dev.updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
            else:
                self.logger.error(u"{}: deviceStopComm: Unknown device type: {}".format(dev.name, dev.deviceTypeId))
        except:
            pass

              
    def validateDeviceConfigUi(self, valuesDict, typeId, devId):
        self.logger.debug(u"validateDeviceConfigUi: typeId = {}, devId = {}".format(typeId, devId))

        if typeId == "serialPort":
            valuesDict['address'] = self.getSerialPortUrl(valuesDict, 'serialPort') 
        
        return (True, valuesDict)


    ########################################
    # Plugin Actions object callbacks (pluginAction is an Indigo plugin action instance)
    ########################################

    def sendString(self, pluginAction):
        sendString =  indigo.activePlugin.substitute(pluginAction.props["sendString"])
        self.ports[pluginAction.deviceId].send(sendString)
                
