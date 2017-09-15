# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
#    Copyright (C) 2017 Lukasz G. Migas <lukasz.migas@manchester.ac.uk>

#    This program is free software. Feel free to redistribute it and/or 
#    modify it under the condition you cite and credit the authors whenever 
#    appropriate. 
#    The program is distributed in the hope that it will be useful but is 
#    provided WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE
# -------------------------------------------------------------------------

# Import libraries
import wx
import numpy as np
import os
import time
import sys
from time import clock, gmtime, strftime
from wx.lib.pubsub import setuparg1
import path
from subprocess import call, Popen
import webbrowser
from IDs import *



# Import ORIGAMI libraries
import mainWindow as mainWindow
import config as config
from toolbox import *
import dialogs as dialogs


class ORIGAMIMS(object):
    def __init__(self, *args, **kwargs):
        
        self.__wx_app = wx.App(redirect=False)
        self.run = None
        self.view = None
        self.init(*args, **kwargs)
        
    def start(self):
        self.view.Show()
        self.__wx_app.MainLoop()
        
    def quit(self):
        self.__wx_app.ProcessIdle()
        self.__wx_app.ExitMainLoop()
        self.view.Destroy()
        return True
    
    def endSession(self):
        wx.CallAfter(self.quit, force=True)
        
    def init(self, *args, **kwargs):

        self.config = config.config() 
        self.icons = config.IconContainer()
        
        self.view = mainWindow.MyFrame(self, config=self.config, 
                                       icons = self.icons, title="ORIGAMI-MS")
        self.wrensCMD = None
        self.wrensRun = None
        self.wrensReset = None
        self.currentPath = ""
        self.wrensInput = {'polarity':None,
                           'activationZone':None,
                           'method':None,
                           'command':None}
        self.logging = True


        self.config.startTime = (strftime("%H-%M-%S_%d-%m-%Y", gmtime()))
        self.__wx_app.SetTopWindow(self.view)
        self.__wx_app.SetAppName("ORIGAMI-MS")
        self.__wx_app.SetVendorName("Lukasz G Migas, University of Manchester")
        
        # Log all events to 
        if self.logging == True:
            sys.stdin = self.view.panelPlots.log
            sys.stdout = self.view.panelPlots.log
            sys.stderr = self.view.panelPlots.log
            
        self.importConfigFileOnStart(evt=None)
        
        
#===============================================================================
# ACQUISITION FUNCTIONS
#===============================================================================
        
    def onLibraryLink(self, evt):
        """Open selected webpage."""

        # set link
        links = {ID_helpHomepage : 'home',
                 ID_helpGitHub : 'github',
                 ID_helpCite : 'cite',
                 ID_helpNewVersion : 'newVersion'}
        
        link = self.config.links[links[evt.GetId()]]
        
        # open webpage
        try: 
            webbrowser.open(link, autoraise=1)
        except: pass
        
    def onCheckParameters(self, evt):
        """
        This function checks that all variables are in correct format
        """        
        
        print("version", self.config.version)
        
        if isinstance(self.config.iSPV, ( int, long )): pass
        else: 
            msg = ("SPV value should be an integer!")
            dialogs.dlgBox(exceptionTitle='Mistake in the input', 
                           exceptionMsg= msg,
                           type="Error")
            return False
        
        if isinstance(self.config.iScanTime, ( int, float )): pass
        else: 
            msg = ("Scan time value should be an integer or float!")
            dialogs.dlgBox(exceptionTitle='Mistake in the input', 
                           exceptionMsg= msg,
                           type="Error")
            return False
        
        if isinstance(self.config.iStartVoltage, ( int, float )): pass
        else: 
            msg = ("Start voltage should be an integer or float!")
            dialogs.dlgBox(exceptionTitle='Mistake in the input', 
                           exceptionMsg= msg,
                           type="Error")
            return False
        
        if isinstance(self.config.iEndVoltage, ( int, float )): pass
        else: 
            msg = ("End voltage should be an integer or float!")
            dialogs.dlgBox(exceptionTitle='Mistake in the input', 
                           exceptionMsg= msg,
                           type="Error")
            return False
        
        if isinstance(self.config.iStepVoltage, ( int, float )): pass
        else: 
            msg = ("Step voltage should be an integer or float!")
            dialogs.dlgBox(exceptionTitle='Mistake in the input', 
                           exceptionMsg= msg,
                           type="Error")
            return False
        
        if self.config.iActivationMode == "Exponential":
            if isinstance(self.config.iExponentPerct, ( int, float )): pass
            else: 
                msg = ("Exponential % value should be an integer or float!")
                dialogs.dlgBox(exceptionTitle='Mistake in the input', 
                               exceptionMsg= msg,
                               type="Error")
                return False
            
            if isinstance(self.config.iExponentIncre, ( int, float )): pass
            else: 
                msg = ("Exponential increment value should be an float!")
                dialogs.dlgBox(exceptionTitle='Mistake in the input', 
                               exceptionMsg= msg,
                               type="Error")
                return False
            
        elif self.config.iActivationMode == "Boltzmann":
            if isinstance(self.config.iBoltzmann, ( int, float )): pass
            else: 
                msg = ("Boltzmann offset value should be an integer or float!")
                dialogs.dlgBox(exceptionTitle='Mistake in the input', 
                               exceptionMsg=msg ,
                               type="Error")
                return False
        
        
        if (abs(self.config.iEndVoltage) <= abs(self.config.iStartVoltage)):
            msg = ('End voltage has to be larger than starting voltage')
            dialogs.dlgBox(exceptionTitle='Mistake in the input', 
                           exceptionMsg=msg ,
                           type="Error")
            return
        
        if (abs(self.config.iEndVoltage) > 200):
            msg = ('The highest possible voltage is 200 V. Set to default: 200')
            dialogs.dlgBox(exceptionTitle='Mistake in the input', 
                           exceptionMsg=msg ,
                           type="Error")
            self.config.iEndVoltage = 200
            self.view.panelControls.endVoltage_input.SetValue(str(self.config.iEndVoltage))
        
        if (abs(self.config.iStartVoltage) < 0):
            msg = ('The lowest possible voltage is 0 V. Set to default: 0')
            dialogs.dlgBox(exceptionTitle='Mistake in the input', 
                           exceptionMsg=msg ,
                           type="Error")
            self.config.iStartVoltage = 0
            self.view.panelControls.startVoltage_input.SetValue(str(self.config.iStartVoltage))
            
        if self.config.iSPV <= 0:
            msg = ('SPV must be larger than 0! Set to default: 3')
            dialogs.dlgBox(exceptionTitle='Mistake in the input', 
                           exceptionMsg=msg ,
                           type="Error")
            self.config.iSPV = 3
            self.view.panelControls.spv_input.SetValue(str(self.config.iSPV))
        
        if self.config.iScanTime <= 0:
            msg = ('Scan time must be larger than 0! Set to default: 5')
            dialogs.dlgBox(exceptionTitle='Mistake in the input', 
                           exceptionMsg=msg ,
                           type="Error")
            self.config.iScanTime = 5
            self.view.panelControls.scanTime_input.SetValue(str(self.config.iScanTime))

        if self.config.iActivationMode == "Exponential":
            if self.config.iExponentPerct < 0:
                msg = ('Exponential % must be larger or equal to 0! Set to default: 0')
                dialogs.dlgBox(exceptionTitle='Mistake in the input', 
                               exceptionMsg=msg ,
                               type="Error")
                self.config.iExponentPerct = 0
            elif self.config.iExponentPerct >= 100:
                msg = ('Exponential % must be smaller than 100! Set to default: 0')
                dialogs.dlgBox(exceptionTitle='Mistake in the input', 
                               exceptionMsg=msg ,
                               type="Error")
                self.config.iExponentPerct = 0
            self.view.panelControls.exponentialPerct_input.SetValue(str(self.config.iExponentPerct))
            
            if self.config.iExponentIncre <= 0:
                msg = ('Exponential increment must be larger than 0! Set to default: 0.01')
                dialogs.dlgBox(exceptionTitle='Mistake in the input', 
                               exceptionMsg=msg ,
                               type="Error")
                self.config.iExponentIncre = 0.01
            elif self.config.iExponentIncre > 0.075:
                msg = ('Exponential increment must be smaller than 0.075! Set to default: 0.075')
                dialogs.dlgBox(exceptionTitle='Mistake in the input', 
                               exceptionMsg=msg ,
                               type="Error")
                self.config.iExponentIncre = 0.075
            self.view.panelControls.exponentialIncrm_input.SetValue(str(self.config.iExponentIncre))
        elif self.config.iActivationMode == "Boltzmann":
            if self.config.iBoltzmann < 10:
                msg = ('Boltzmann offset must be larger than 10! Set to default: 10')
                dialogs.dlgBox(exceptionTitle='Mistake in the input', 
                               exceptionMsg=msg,
                               type="Error")
                self.config.iBoltzmann = 10
            elif self.config.iBoltzmann >= 100:
                msg = ('Boltzmann offset must be smaller than 100! Set to default: 25')
                dialogs.dlgBox(exceptionTitle='Mistake in the input', 
                               exceptionMsg=msg,
                               type="Error")
                self.config.iBoltzmann = 25
            self.view.panelControls.boltzmann_input.SetValue(str(self.config.iBoltzmann))
            
        # All good
        return True
             
    def onCalculateParameters(self, evt):
        """
        This function is to be used to setup path to save origami parameters 
        """
        
        if not self.config.iActivationMode == "User-defined":
            if self.onCheckParameters(evt=None) == False: 
                print('Please fill in all necessary fields first!')
                return
            divisibleCheck = abs(self.config.iEndVoltage-self.config.iStartVoltage)/self.config.iStepVoltage
            divisibleCheck2 = divisibleCheck%1
            if divisibleCheck2 != 0:
                msg = "Are you sure your collision voltage range is divisible by your increment?"
                dialogs.dlgBox(exceptionTitle='Mistake in the input', 
                               exceptionMsg= msg,
                               type="Error")
                return
        else:
            if self.config.iScanTime == None or self.config.iScanTime == "": 
                msg = 'Please make sure you to fill in the scan time input box.'
                dialogs.dlgBox(exceptionTitle='Mistake in the input', 
                               exceptionMsg= msg,
                               type="Error")
                return
        
        if self.config.iActivationMode == "Linear":
            self.wrensInput, ColEnergyX, scanPerVoltageList, timeList, totalAcqTime = self.onPrepareLinearMethod()
        elif self.config.iActivationMode == "Exponential":
            self.wrensInput, ColEnergyX, scanPerVoltageList, timeList, totalAcqTime = self.onPrepareExponentialMethod()
        elif self.config.iActivationMode == "Boltzmann":
            self.wrensInput, ColEnergyX, scanPerVoltageList, timeList, totalAcqTime = self.onPrepareBoltzmannMethod()
        elif self.config.iActivationMode == "User-defined":
            self.wrensInput, ColEnergyX, scanPerVoltageList, timeList, totalAcqTime = self.onPrepareListMethod()            
        
        self.wrensCMD = self.wrensInput.get('command', None)
        # Setup status:
        self.view.SetStatusText(''.join(['Acq. time: ',str(totalAcqTime),' mins']), number=0)
        self.view.SetStatusText(''.join([str(len(scanPerVoltageList)), ' steps']), number=1)
        
        # Add wrensCMD to config file
        self.config.wrensCMD = self.wrensCMD
        
        self.onPlotSPV(ColEnergyX, scanPerVoltageList)
        self.onPlotTime(ColEnergyX, timeList)
        print(''.join(["Your submission code: ", self.wrensCMD]))
    
    def onPrepareLinearMethod(self):
        
        startScansPerVoltage = self.config.iSPV
        scanPerVoltageList, timeList = [], []
        timeFit=3
        
        numberOfCEsteps = (self.config.iEndVoltage-self.config.iStartVoltage)/self.config.iStepVoltage+1
        ColEnergyX = np.linspace(self.config.iStartVoltage,
                                 self.config.iEndVoltage,
                                 numberOfCEsteps)
        for i in range(int(numberOfCEsteps)):
            scanPerVoltageFit = startScansPerVoltage
            scanPerVoltageList.append(scanPerVoltageFit)
            timeFit = timeFit + scanPerVoltageFit
            timeList.append(timeFit*self.config.iScanTime)
        numberOfCEScans = (numberOfCEsteps*self.config.iSPV)
        timeOfCEScans = (numberOfCEScans+self.config.iSPV)*self.config.iScanTime
        totalAcqTime = round(float((6+numberOfCEScans+self.config.iSPV)*self.config.iScanTime)/60,2)
        if (totalAcqTime > 300):
            msg = "The acquisition will take more than 5 hours. Consider reducing " \
                  "your collision voltage range or adjusting the parameters!"
            dialogs.dlgBox(exceptionTitle='Very long acquisition warning', 
                           exceptionMsg= msg,
                           type="Warning")
        
        wrensCMD = ''.join([self.config.wrensLinearPath, 
                            self.config.iActivationZone,',', 
                            self.config.iPolarity,',',
                            str(self.config.iSPV),',',
                            str(self.config.iScanTime),',',
                            str(self.config.iStartVoltage),',',
                            str(self.config.iEndVoltage),',',
                            str(self.config.iStepVoltage),',',
                            str(totalAcqTime)])
        wrensInput = {'polarity':self.config.iPolarity,
                     'activationZone':self.config.iActivationZone,
                     'method':self.config.iActivationMode,
                     'command':wrensCMD}
        if self.config.iPolarity == 'POSITIVE': polarity = "+VE"
        else: polarity = "-VE"
        self.view.SetStatusText(''.join(["Current method: ",polarity,
                                         " mode in the ",self.config.iActivationZone,
                                         " using the ",self.config.iActivationMode, 
                                         " method"]), number=2)
        return wrensInput, ColEnergyX, scanPerVoltageList, timeList, totalAcqTime
            
    def onPrepareExponentialMethod(self):
        startScansPerVoltage = self.config.iSPV
        scanPerVoltageList, timeList = [], []
        timeFit=3
        expAccumulator = 0
        
        numberOfCEsteps = (self.config.iEndVoltage-self.config.iStartVoltage)/self.config.iStepVoltage+1
        ColEnergyX = np.linspace(self.config.iStartVoltage,
                                 self.config.iEndVoltage,
                                 numberOfCEsteps)
        for i in xrange(int(numberOfCEsteps)):
            if abs(ColEnergyX[i]) >= abs(self.config.iEndVoltage*self.config.iExponentPerct/100):
                expAccumulator=expAccumulator+self.config.iExponentIncre
                scanPerVoltageFit =  np.round(startScansPerVoltage*np.exp(expAccumulator),0)
            else:       
                scanPerVoltageFit = startScansPerVoltage

            scanPerVoltageList.append(scanPerVoltageFit)
            timeFit = timeFit + scanPerVoltageFit
            timeList.append(timeFit*self.config.iScanTime)


        numberOfCEScans = sum(scanPerVoltageList)
        timeOfCEScans = (numberOfCEScans+scanPerVoltageList[-1])*self.config.iScanTime
        totalAcqTime = round(float((6+numberOfCEScans+self.config.iSPV)*self.config.iScanTime)/60,2)
        if (totalAcqTime > 300):
            msg = "The acquisition will take more than 5 hours. Consider reducing " \
                  "your collision voltage range or adjusting the parameters!"
            dialogs.dlgBox(exceptionTitle='Very long acquisition warning', 
                           exceptionMsg= msg,
                           type="Warning")
        wrensCMD = ''.join([self.config.wrensExponentPath, 
                            self.config.iActivationZone,',', 
                            self.config.iPolarity,',',
                            str(self.config.iSPV),',',
                            str(self.config.iScanTime),',',
                            str(self.config.iStartVoltage),',',
                            str(self.config.iEndVoltage),',',
                            str(self.config.iStepVoltage),',',
                            str(self.config.iExponentPerct),',',
                            str(self.config.iExponentIncre),',',
                            str(totalAcqTime)])
        
        wrensInput = {'polarity':self.config.iPolarity,
                     'activationZone':self.config.iActivationZone,
                     'method':self.config.iActivationMode,
                     'command':wrensCMD}
        if self.config.iPolarity == 'POSITIVE': polarity = "+VE"
        else: polarity = "-VE"
        self.view.SetStatusText(''.join(["Current method: ",polarity,
                                         " mode in the ",self.config.iActivationZone,
                                         " using the ",self.config.iActivationMode, 
                                         " method"]), number=2)
        return wrensInput, ColEnergyX, scanPerVoltageList, timeList, totalAcqTime
    
    def onPrepareBoltzmannMethod(self):
        startScansPerVoltage = self.config.iSPV
        scanPerVoltageList, timeList = [], []
        timeFit=3
        A1 = 2
        A2 = 0.07
        x0 = 47  
        
        numberOfCEsteps = int((self.config.iEndVoltage-self.config.iStartVoltage)/self.config.iStepVoltage+1)
        ColEnergyX = np.linspace(self.config.iStartVoltage,
                                 self.config.iEndVoltage,
                                 numberOfCEsteps)
        for i in range(int(numberOfCEsteps)):
            scanPerVoltageFit = np.round(1/(A2+(A1-A2)/(1+np.exp((ColEnergyX[i]-x0)/self.config.iBoltzmann))),0)
            scanPerVoltageList.append(scanPerVoltageFit*startScansPerVoltage)
            timeFit = timeFit + scanPerVoltageFit
            timeList.append(timeFit*self.config.iScanTime)
        
        numberOfCEScans = sum(scanPerVoltageList)
        timeOfCEScans = (numberOfCEScans+scanPerVoltageList[-1])*self.config.iScanTime
        totalAcqTime = round(float((6+numberOfCEScans+self.config.iSPV)*self.config.iScanTime)/60,2)  
        if (totalAcqTime > 300):
            msg = "The acquisition will take more than 5 hours. Consider reducing " \
                  "your collision voltage range or adjusting the parameters!"
            dialogs.dlgBox(exceptionTitle='Very long acquisition warning', 
                           exceptionMsg= msg,
                           type="Warning")
              
        wrensCMD = ''.join([self.config.wrensBoltzmannPath, 
                            self.config.iActivationZone,',', 
                            self.config.iPolarity,',',
                            str(self.config.iSPV),',',
                            str(self.config.iScanTime),',',
                            str(self.config.iStartVoltage),',',
                            str(self.config.iEndVoltage),',',
                            str(self.config.iStepVoltage),',',
                            str(self.config.iBoltzmann),',',
                            str(totalAcqTime)])
        
        wrensInput = {'polarity':self.config.iPolarity,
                     'activationZone':self.config.iActivationZone,
                     'method':self.config.iActivationMode,
                     'command':wrensCMD}
        if self.config.iPolarity == 'POSITIVE': polarity = "+VE"
        else: polarity = "-VE"
        self.view.SetStatusText(''.join(["Current method: ",polarity,
                                         " mode in the ",self.config.iActivationZone,
                                         " using the ",self.config.iActivationMode, 
                                         " method"]), number=2)
        return wrensInput, ColEnergyX, scanPerVoltageList, timeList, totalAcqTime
    
    def onPrepareListMethod(self):
        
        if self.config.CSVFilePath == None: 
            msg = 'Please load a CSV file first.'
            dialogs.dlgBox(exceptionTitle='Mistake in the input', 
                           exceptionMsg= msg,
                           type="Error")
            return       
        if self.config.iScanTime == None or self.config.iScanTime == "": 
            msg = 'Please fill in appropriate fields. The scan time is empty or incorrect'
            dialogs.dlgBox(exceptionTitle='Mistake in the input', 
                           exceptionMsg= msg,
                           type="Error")
            return
        
        print(self.config.CSVFilePath)
        try:
            spvCVlist = np.genfromtxt(self.config.CSVFilePath, 
                                      skip_header=1, 
                                      delimiter=',', 
                                      filling_values=0)
        except: return
        # Read table
        scanPerVoltageList = spvCVlist[:, 0].astype(int)
        ColEnergyX = spvCVlist[:,1]
        
        timeFit=3
        timeList = []
        for i in scanPerVoltageList:
            timeFit = timeFit+i
            timeList.append(timeFit*self.config.iScanTime)
        
        if len(scanPerVoltageList) != len(ColEnergyX): return
        
        totalAcqTime = np.round((sum(scanPerVoltageList)*self.config.iScanTime)/60,2)
        if (totalAcqTime > 300):
            msg = "The acquisition will take more than 5 hours. Consider reducing " \
                  "your collision voltage range or adjusting the parameters!"
            dialogs.dlgBox(exceptionTitle='Very long acquisition warning', 
                           exceptionMsg= msg,
                           type="Warning")
        
        SPV_list = ' '.join(str(spv) for spv in scanPerVoltageList.tolist())
        SPV_list = ''.join(["[",SPV_list,"]"])
        CV_list = ' '.join(str(cv) for cv in ColEnergyX.tolist())
        CV_list = ''.join(["[",CV_list,"]"])
        
        self.config.SPVsList = scanPerVoltageList
        self.config.CVsList = ColEnergyX
        
        print(SPV_list, CV_list)
        
        wrensCMD = ''.join([self.config.wrensUserDefinedPath, 
                            self.config.iActivationZone,',', 
                            self.config.iPolarity,',',
                            str(self.config.iScanTime),',',
                            SPV_list,',',
                            CV_list])
        
        wrensInput = {'polarity':self.config.iPolarity,
                     'activationZone':self.config.iActivationZone,
                     'method':self.config.iActivationMode,
                     'command':wrensCMD}
        if self.config.iPolarity == 'POSITIVE': polarity = "+VE"
        else: polarity = "-VE"
        self.view.SetStatusText(''.join(["Current method: ",polarity,
                                         " mode in the ",self.config.iActivationZone,
                                         " using the ",self.config.iActivationMode, 
                                         " method"]), number=2)
        return wrensInput, ColEnergyX, scanPerVoltageList, timeList, totalAcqTime
          
    def onStartWREnSRun(self, evt):
        
        
        if self.wrensCMD == None: 
            msg = "Are you sure you filled in correct details or pressed calculate?"
            dialogs.dlgBox(exceptionTitle='Please complete all necessary fields and press Calculate', 
                           exceptionMsg= msg,
                           type="Error")
            return
        
        # A couple of checks to ensure the method in the settings is the one
        # currently available in memory..
        if self.wrensInput.get("polarity",None) != self.config.iPolarity: 
            msg = 'The polarity of the current method and the one in the window do not agree. Consider re-calculating.'
            dialogs.dlgBox(exceptionTitle='Mistake in the input', 
                           exceptionMsg= msg,
                           type="Error")
            return
        if self.wrensInput.get("activationZone",None) != self.config.iActivationZone: 
            msg = 'The activation zone of the current method and the one in the window do not agree. Consider re-calculating.'
            dialogs.dlgBox(exceptionTitle='Mistake in the input', 
                           exceptionMsg= msg,
                           type="Error")
            return
        if self.wrensInput.get("method",None) != self.config.iActivationMode:
            msg = 'The acquisition mode of the current method and the one in the window do not agree. Consider re-calculating.'
            dialogs.dlgBox(exceptionTitle='Mistake in the input', 
                           exceptionMsg= msg,
                           type="Error") 
            return
        if self.wrensInput.get("command",None) != self.wrensCMD:
            msg = 'The command in the memory and the current method and the one in the window do not agree. Consider re-calculating.'
            dialogs.dlgBox(exceptionTitle='Mistake in the input', 
                           exceptionMsg= msg,
                           type="Error") 
            return
        

        print(''.join(["Your code: ",self.wrensCMD]))
        
        self.wrensRun = Popen(self.wrensCMD)
        
    def onStopWREnSRun(self, evt):
        
        if self.wrensRun:
            print('Stopped acquisition and reset the property banks')
            self.wrensRun.kill()
            self.wrensReset = Popen(self.config.wrensResetPath)
            self.view.panelControls.goBtn.Enable()
        else: 
            print('You have to start acquisition first!')
        
    def onFillInDefaults(self, evt=None):    
        """
        This function fills in default values in case you are being lazy!
        """
        pass
        
    def onGetMassLynxPath(self, evt):
        """
        Select path to the MassLynx folder
        """
         
        dlg = wx.DirDialog(self.view, "Select MassLynx directory",
                           style=wx.DD_DEFAULT_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            print "You chose %s" % dlg.GetPath()
            self.view.panelControls.path_value.SetValue(dlg.GetPath())
            self.currentPath = dlg.GetPath()
        
    def importConfigFile(self, evt):
        """
        This function imports configuration file
        """
        dlg = wx.FileDialog(self.view, "Open Configuration File", wildcard = "*.ini" ,
                           style=wx.FD_DEFAULT_STYLE | wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            fileName=dlg.GetPath()
            self.config.importConfig(fileName=fileName,e=None)
            print(''.join(["WREnS runner path: ", self.config.wrensRunnerPath]))
            print(''.join(["Linear path: ", self.config.wrensLinearPath]))
            print(''.join(["Exponent path: ", self.config.wrensExponentPath]))
            print(''.join(["Boltzmann path: ", self.config.wrensBoltzmannPath]))
            print(''.join(["List path: ", self.config.wrensUserDefinedPath]))
            print(''.join(["Reset path: ", self.config.wrensResetPath]))
 
    def importConfigFileOnStart(self, evt):
        print("Importing origamiConfig.ini")
        self.config.importConfig(fileName="origamiConfig.ini",e=None)

        print(''.join(["WREnS runner path: ", self.config.wrensRunnerPath]))
        print(''.join(["Linear path: ", self.config.wrensLinearPath]))
        print(''.join(["Exponent path: ", self.config.wrensExponentPath]))
        print(''.join(["Boltzmann path: ", self.config.wrensBoltzmannPath]))
        print(''.join(["List path: ", self.config.wrensUserDefinedPath]))
        print(''.join(["Reset path: ", self.config.wrensResetPath]))
        
    def onExportConfig(self, evt): 
        """
        This function exports configuration file
        """
        dlg = wx.FileDialog(self.view, "Save As Configuration File", wildcard = "*.ini" ,
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            fileName=dlg.GetPath()
            self.config.exportConfig(fileName=fileName, e=None)
            
    def onExportParameters(self, evt):
        dlg = wx.FileDialog(self.view, "Save As ORIGAMI configuration File", wildcard = "*.conf" ,
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        dlg.SetFilename('origami.conf')
        if dlg.ShowModal() == wx.ID_OK:
            fileName=dlg.GetPath()
            self.config.exportOrigamiConfig(fileName=fileName, e=None)
            
    def onLoadCSVList(self, evt):
        """
        This function loads a two column list with Collision voltage | number of scans 
        """
        dlg = wx.FileDialog(self.view, "Choose a file:", wildcard = "*.txt; *.csv" ,
                           style=wx.FD_DEFAULT_STYLE | wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            print "You chose %s" % dlg.GetPath()
            self.config.CSVFilePath = dlg.GetPath()
                                                       
    def onPlotSPV(self, xvals, yvals):            
        self.view.panelPlots.plot1.clearPlot()
        self.view.panelPlots.plot1.plot1Ddata(xvals=xvals, yvals=yvals, 
                                              title="", 
                                              xlabel="Collision Voltage (V)",
                                              ylabel="SPV")
        # Show the mass spectrum
        self.view.panelPlots.plot1.repaint()
        
    def onPlotTime(self, xvals, yvals):            
        self.view.panelPlots.plot2.clearPlot()
        self.view.panelPlots.plot2.plot1Ddata(xvals=xvals, yvals=yvals, 
                                              title="", 
                                              xlabel="Collision Voltage (V)",
                                              ylabel="Accumulated Time (s)")
        # Show the mass spectrum
        self.view.panelPlots.plot2.repaint()
        


        
        
        
if __name__ == '__main__':
    app = ORIGAMIMS()
    app.start()