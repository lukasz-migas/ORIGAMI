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


import wx.combo
from origamiStyles import *
from toolbox import *


class panelControls ( wx.Panel ):
    
    def __init__( self, parent, presenter, config):
        wx.Panel.__init__ ( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, 
                        size = wx.Size(600,400), style = wx.TAB_TRAVERSAL)
        
        
        self.parent = parent 
        self.presenter = presenter
        self.config = config
        
        self.SetDimensions(0,0,400,290)
        
        # Main sizer for the panel
        mainSizer = wx.BoxSizer( wx.VERTICAL )
        
        # Prepare notebooks
        self.settingsBook = wx.Notebook( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
        
        self.settingsBook_pane1 = wx.Panel( self.settingsBook, wx.ID_ANY, 
                                        wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.settingsBook.AddPage( self.settingsBook_pane1, u"aIM-MS", False )
        self.origamiSettingsPane()
        self.onEnableDisable(evt=None)
        mainSizer.Add(self.settingsBook, 1, wx.EXPAND |wx.ALL, 5)
        self.SetSizer( mainSizer )
        self.Layout()
        
    def origamiSettingsPane(self):
        
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        
        # Gather sizers
        polarityBox = self.polaritySubPanel()
        activationZone = self.activationZoneSubPanel()
        activationType = self.activationTypeSubPanel()
        origamiParams = self.origamiParametersSubPanel() 
        buttons = self.buttonsSubPanel()
        
        mainGrid = wx.GridBagSizer(4,2)
        mainGrid.Add(polarityBox, (0,0), (1,1))
        mainGrid.Add(activationZone, (0,1), (1,1))
        mainGrid.Add(activationType, (1,0), (1,2))
        mainGrid.Add(origamiParams, (0,2), (2,4))
        mainGrid.Add(buttons, (2,0), (2,4))
        
        mainSizer.Add(mainGrid, wx.EXPAND |wx.ALL, 2)
        
        self.settingsBook_pane1.SetSizer(mainSizer)
        self.settingsBook_pane1.Layout()
        
        # Make bindings
        self.polarityBox.Bind(wx.EVT_RADIOBOX, self.onGetParameters)
        self.activationZone.Bind(wx.EVT_RADIOBOX, self.onGetParameters)
        self.activationType.Bind(wx.EVT_RADIOBOX, self.onGetParameters)
        self.spv_input.Bind(wx.EVT_TEXT, self.onGetParameters)
        self.scanTime_input.Bind(wx.EVT_TEXT, self.onGetParameters)
        self.startVoltage_input.Bind(wx.EVT_TEXT, self.onGetParameters)
        self.endVoltage_input.Bind(wx.EVT_TEXT, self.onGetParameters)
        self.stepVoltage_input.Bind(wx.EVT_TEXT, self.onGetParameters)
        self.exponentialPerct_input.Bind(wx.EVT_TEXT, self.onGetParameters)
        self.exponentialIncrm_input.Bind(wx.EVT_TEXT, self.onGetParameters)
        self.boltzmann_input.Bind(wx.EVT_TEXT, self.onGetParameters)
        
        self.loadCSVBtn.Bind(wx.EVT_BUTTON, self.presenter.onLoadCSVList)
               
    def polaritySubPanel(self):
               
        self.polarityBox = wx.RadioBox(self.settingsBook_pane1, wx.ID_ANY, "Ion Polarity", 
                                       choices=["Positive", "Negative"],
                                       majorDimension=1, style=wx.RA_SPECIFY_COLS)
        self.polarityBox.SetSelection(0)
        self.polarityBox.SetMinSize((100, -1))
        
        return self.polarityBox
    
    def activationZoneSubPanel(self):
 
        self.activationZone = wx.RadioBox(self.settingsBook_pane1, wx.ID_ANY, "Activation Type", 
                                       choices=["Cone", "Trap"],
                                       majorDimension=1, style=wx.RA_SPECIFY_COLS)
        self.activationZone.SetSelection(1)
        self.activationZone.SetMinSize((100, -1))
        
        return self.activationZone
        
    def activationTypeSubPanel(self):
 
        self.activationType = wx.RadioBox(self.settingsBook_pane1, wx.ID_ANY, "Activation Type", 
                                       choices=["Linear", "Exponential", "Boltzmann",
                                                "User-defined"],
                                       majorDimension=2, style=wx.RA_SPECIFY_COLS)
        self.activationType.SetSelection(0)
        self.activationType.SetMinSize((202, -1))
        
        return self.activationType
        
    def origamiParametersSubPanel(self):
        
        origamiBox = makeStaticBox(self.settingsBook_pane1, "ORIGAMI parameters", (330,-1), wx.BLUE)
        
        origamiMainSizer = wx.StaticBoxSizer(origamiBox, wx.HORIZONTAL)
        
        spv_label = makeStaticText(self.settingsBook_pane1, "Scans per Voltage")
        self.spv_input =  wx.TextCtrl(self.settingsBook_pane1, -1, "", size=(TXTBOX_SIZE, -1))
        
        scanTime_label = makeStaticText(self.settingsBook_pane1, "Scan time (s)")
        self.scanTime_input =  wx.TextCtrl(self.settingsBook_pane1, -1, "", size=(TXTBOX_SIZE, -1))
        
        startVoltage_label = makeStaticText(self.settingsBook_pane1, "Start voltage (V)")
        self.startVoltage_input =  wx.TextCtrl(self.settingsBook_pane1, -1, "", size=(TXTBOX_SIZE, -1))
        
        endVoltage_label = makeStaticText(self.settingsBook_pane1, "End voltage (V)")
        self.endVoltage_input =  wx.TextCtrl(self.settingsBook_pane1, -1, "", size=(TXTBOX_SIZE, -1))

        stepVoltage_label = makeStaticText(self.settingsBook_pane1, "Step voltage (V)")
        self.stepVoltage_input =  wx.TextCtrl(self.settingsBook_pane1, -1, "", size=(TXTBOX_SIZE, -1))
        
        exponentialPerct_label = makeStaticText(self.settingsBook_pane1, "Exponential (%)")
        self.exponentialPerct_input =  wx.TextCtrl(self.settingsBook_pane1, -1, "", size=(TXTBOX_SIZE, -1))
        
        exponentialIncrm_label = makeStaticText(self.settingsBook_pane1, "Exponential increment")
        self.exponentialIncrm_input =  wx.TextCtrl(self.settingsBook_pane1, -1, "", size=(TXTBOX_SIZE, -1))
        
        boltzmann_label = makeStaticText(self.settingsBook_pane1, "Boltzmann offset")
        self.boltzmann_input =  wx.TextCtrl(self.settingsBook_pane1, -1, "", size=(TXTBOX_SIZE, -1))
        
        
        userDefined_label = makeStaticText(self.settingsBook_pane1, "User-defined")
        self.loadCSVBtn = wx.Button(self.settingsBook_pane1, -1, "Load list", size=(60,-1))
        
        
        grid = wx.GridBagSizer(2,2)

        grid.Add(spv_label, wx.GBPosition(0,0), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
        grid.Add(self.spv_input, wx.GBPosition(0,1), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
        
        grid.Add(scanTime_label, wx.GBPosition(1,0), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
        grid.Add(self.scanTime_input, wx.GBPosition(1,1), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)        
        
        grid.Add(startVoltage_label, wx.GBPosition(2,0), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
        grid.Add(self.startVoltage_input, wx.GBPosition(2,1), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)

        grid.Add(endVoltage_label, wx.GBPosition(3,0), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
        grid.Add(self.endVoltage_input, wx.GBPosition(3,1), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
        
        grid.Add(stepVoltage_label, wx.GBPosition(4,0), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
        grid.Add(self.stepVoltage_input, wx.GBPosition(4,1), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)        

        grid.Add(exponentialPerct_label, wx.GBPosition(0,2), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
        grid.Add(self.exponentialPerct_input, wx.GBPosition(0,3), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
        
        grid.Add(exponentialIncrm_label, wx.GBPosition(1,2), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
        grid.Add(self.exponentialIncrm_input, wx.GBPosition(1,3), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)

        grid.Add(boltzmann_label, wx.GBPosition(2,2), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
        grid.Add(self.boltzmann_input, wx.GBPosition(2,3), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
        
        grid.Add(userDefined_label, wx.GBPosition(3,2), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
        grid.Add(self.loadCSVBtn, (3,3), flag=wx.ALIGN_CENTER|wx.ALIGN_CENTER_HORIZONTAL)
        

         
        origamiMainSizer.Add(grid, 0, wx.EXPAND|wx.ALL, 2)
        
        return origamiMainSizer
        
    def buttonsSubPanel(self):
        mainSizer = wx.StaticBoxSizer(wx.StaticBox(self.settingsBook_pane1, -1, "", size=(552,-1)),
                                      wx.VERTICAL)
        
        self.pathBtn = wx.Button(self.settingsBook_pane1, -1, "Set path", size=(80,-1))
        self.calculateBtn = wx.Button(self.settingsBook_pane1, -1, "Calculate", size=(80,-1))
        self.saveParametersBtn = wx.Button(self.settingsBook_pane1, -1, "Save parameters", size=(100,-1))
        self.goBtn = wx.Button(self.settingsBook_pane1, -1, "Go", size=(80,-1))
        self.stopBtn= wx.Button(self.settingsBook_pane1, -1, "Stop", size=(80,-1))
        
        path_label = makeStaticText(self.settingsBook_pane1, "Path:")
        self.path_value =  wx.TextCtrl(self.settingsBook_pane1, -1, "", size=(480, -1))
        self.path_value.SetEditable(False)
        
        grid = wx.GridBagSizer(5, 5)
        grid.Add(self.pathBtn, (0,1), flag=wx.ALIGN_CENTER|wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(self.calculateBtn, (0,2), flag=wx.ALIGN_CENTER|wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(self.saveParametersBtn, (0,3), flag=wx.ALIGN_CENTER|wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(self.goBtn, (0,4), flag=wx.ALIGN_CENTER|wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(self.stopBtn, (0,5), flag=wx.ALIGN_CENTER|wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(path_label, (1,0), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(self.path_value, (1,1), (1,7),flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_HORIZONTAL)
        
        # make bindings
        self.pathBtn.Bind(wx.EVT_BUTTON, self.presenter.onGetMassLynxPath)
        self.calculateBtn.Bind(wx.EVT_BUTTON, self.presenter.onCalculateParameters)
        self.goBtn.Bind(wx.EVT_BUTTON, self.presenter.onStartWREnSRun)
        self.stopBtn.Bind(wx.EVT_BUTTON, self.presenter.onStopWREnSRun)
        
        self.saveParametersBtn.Bind(wx.EVT_BUTTON, self.presenter.onExportParameters)

        mainSizer.Add(grid, 0, wx.ALIGN_CENTER|wx.ALL, 10)
        
        return mainSizer
    
#     def pathSubPanel(self):
#         mainSizer = wx.StaticBoxSizer(wx.StaticBox(self.settingsBook_pane1, -1, "", size=(552,-1)),
#                                       wx.VERTICAL)
# 
#         
#         mainSizer.Add(grid, 0, wx.ALIGN_CENTER|wx.ALL, 10)
#         return mainSizer
    
    def onGetParameters(self, evt):
        
        polarityID = self.polarityBox.GetStringSelection()
        if polarityID == "Positive": 
            self.config.iPolarity = 'POSITIVE'
        else: 
            self.config.iPolarity = 'NEGATIVE'
        
        activationID = self.activationZone.GetStringSelection()
        if activationID == "Cone": 
            self.config.iActivationZone = 'CONE'
        else: 
            self.config.iActivationZone = 'TRAP'
        
        self.config.iActivationMode = self.activationType.GetStringSelection()
        
        self.config.iSPV = str2int(self.spv_input.GetValue())
        self.config.iScanTime = str2int(self.scanTime_input.GetValue()) 
        self.config.iStartVoltage = str2num(self.startVoltage_input.GetValue()) 
        self.config.iEndVoltage = str2num(self.endVoltage_input.GetValue()) 
        self.config.iStepVoltage = str2num(self.stepVoltage_input.GetValue()) 
        self.config.iExponentPerct = str2num(self.exponentialPerct_input.GetValue()) 
        self.config.iExponentIncre = str2num(self.exponentialIncrm_input.GetValue())
        self.config.iBoltzmann = str2num(self.boltzmann_input.GetValue())
        
        self.onEnableDisable(evt=None)
  
    def importFromConfig(self, evt):
        print('Importing parameters from configuration file')
        self.spv_input.SetValue(str(self.config.iSPV))
        self.scanTime_input.SetValue(str(self.config.iScanTime))
        self.startVoltage_input.SetValue(str(self.config.iStartVoltage))
        self.endVoltage_input.SetValue(str(self.config.iEndVoltage))
        self.stepVoltage_input.SetValue(str(self.config.iStepVoltage))
        self.exponentialPerct_input.SetValue(str(self.config.iExponentPerct))
        self.exponentialIncrm_input.SetValue(str(self.config.iExponentIncre))
        self.boltzmann_input.SetValue(str(self.config.iBoltzmann))
        
        if self.config.iPolarity == 'POSITIVE': self.polarityBox.SetSelection(0)
        elif self.config.iPolarity == 'NEGATIVE': self.polarityBox.SetSelection(1)
        
        if self.config.iActivationZone == 'Cone': self.activationZone.SetSelection(0)
        elif self.config.iActivationZone == 'Trap': self.activationZone.SetSelection(1)
  
        if self.config.iActivationMode == 'Linear': self.activationType.SetSelection(0)
        elif self.config.iActivationMode == 'Exponential': self.activationType.SetSelection(1)
        elif self.config.iActivationMode == 'Boltzmann': self.activationType.SetSelection(2)
        elif self.config.iActivationMode == 'User-defined': self.activationType.SetSelection(3)
        
        self.onEnableDisable(evt=None)
  
    def onEnableDisable(self, evt):
        """ 
        This function enables/disables boxes, depending on the selection
        of the method
        """
        self.config.iActivationMode = self.activationType.GetStringSelection()
        if self.config.iActivationMode == "Linear":
            self.exponentialIncrm_input.Disable()
            self.exponentialPerct_input.Disable()
            self.boltzmann_input.Disable()
            self.loadCSVBtn.Disable()
        elif self.config.iActivationMode == "Exponential":
            self.exponentialIncrm_input.Enable()
            self.exponentialPerct_input.Enable()
            self.boltzmann_input.Disable()
            self.loadCSVBtn.Disable()
        elif self.config.iActivationMode == "Boltzmann":
            self.exponentialIncrm_input.Disable()
            self.exponentialPerct_input.Disable()
            self.boltzmann_input.Enable()
            self.loadCSVBtn.Disable()
        elif self.config.iActivationMode == "User-defined":
            self.exponentialIncrm_input.Disable()
            self.exponentialPerct_input.Disable()
            self.boltzmann_input.Disable()
            self.loadCSVBtn.Enable()
            
        # Since whenever we change the activation zone, polarity or activation
        # type, the wrensCMD is going to be incorrect. It needs to be cleared-up
        # to ensure it is te correct command.
        
        
        
        

        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        