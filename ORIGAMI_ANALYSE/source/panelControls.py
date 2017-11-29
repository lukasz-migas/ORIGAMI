# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
#    Copyright (C) 2017 Lukasz G. Migas <lukasz.migas@manchester.ac.uk>
# 
#	 GitHub : https://github.com/lukasz-migas/ORIGAMI
#	 University of Manchester IP : https://www.click2go.umip.com/i/s_w/ORIGAMI.html
#	 Cite : 10.1016/j.ijms.2017.08.014
#
#    This program is free software. Feel free to redistribute it and/or 
#    modify it under the condition you cite and credit the authors whenever 
#    appropriate. 
#    The program is distributed in the hope that it will be useful but is 
#    provided WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE
# -------------------------------------------------------------------------

import wx
import os
import wx.combo
from origamiStyles import *
from origamiConfig import OrigamiConfig
from numpy import float
from toolbox import *
from wx import EVT_BUTTON, ID_ANY
from ast import literal_eval
import sys
from dialogs import dlgBox

# import wx.lib.agw.foldpanelbar as fpb
import wx.lib.scrolledpanel

class panelControls ( wx.Panel ):
	
	def __init__( self, parent, config , icons):
		wx.Panel.__init__ ( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, 
						size = wx.Size( 300,600 ), style = wx.TAB_TRAVERSAL )
		
		#Extract size of screen
		self.displaysize = wx.GetDisplaySize()
		self.SetDimensions(0,0,320,self.displaysize[1]-50)
		
		# Set up config object
		self.config = config 
		self.parent = parent
		self.icons = icons
		self.importEvent = False
		
		
		# Main sizer for the panel
		mainSizer = wx.BoxSizer( wx.VERTICAL )
		
		# Prepare notebooks
		self.settingsBook = wx.Notebook( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )

		self.notebookSettings_paneML = wx.lib.scrolledpanel.ScrolledPanel(self.settingsBook, wx.ID_ANY,
																		  wx.DefaultPosition, wx.DefaultSize,
																		  wx.TAB_TRAVERSAL )
		
		self.notebookSettings_paneML.SetupScrolling()
		self.settingsBook.AddPage( self.notebookSettings_paneML, u"Process", False )
		
		self.origamiSettingsPane()
		# =====================================================================
		# Prepare PANE 2	
# 		self.settingsBook_pane2 = wx.Panel( self.settingsBook, wx.ID_ANY, 
# 										wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
# 		self.settingsBook.AddPage( self.settingsBook_pane2, u"CCS", False )
# 		# =====================================================================
# 		# Prepare PANE 3	
# 		self.settingsBook_pane3 = wx.Panel( self.settingsBook, wx.ID_ANY,
# 										 wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
# 		self.settingsBook.AddPage( self.settingsBook_pane3, u"Export", False )
		# =====================================================================
		# Prepare PANE 4	
		self.notebookSettings_paneProperties = wx.lib.scrolledpanel.ScrolledPanel(self.settingsBook, wx.ID_ANY,
										 wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		self.notebookSettings_paneProperties.SetupScrolling()
		self.settingsBook.AddPage( self.notebookSettings_paneProperties, u"Properties", False )
		
		self.parametersSettingsPane()		
		# =====================================================================

		
		###
		mainSizer.Add( self.settingsBook, 1, wx.EXPAND |wx.ALL, 5 )
# 		# Call config
		self.exportToConfig()
						
		self.SetSizer( mainSizer )
		self.Layout()
#===============================================================================
# PLOT CONTROL SETTINGS 
#===============================================================================

	def origamiSettingsPane (self):
		
		# Gather sizers
		peakFittingSubPanel = self.peakFittingSubPanel()
		fileMainSizer = self.fileSubPanel()
		origamiMainSizer = self.origamiSubPanel()
		extractMainSizer = self.extractSubPanel()
		processMainSizer = self.processSubPanel()
		plot2DMainSizer = self.plot2DSubPanel()
		plot1DMainSizer = self.plot1DSubPanel()
		plotComparisonSubPanel = self.plotComparisonSubPanel()
		
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		mainGrid = wx.GridBagSizer(1,1)
		mainGrid.Add(fileMainSizer, (0,0))
		mainGrid.Add(origamiMainSizer, (1,0))	
		mainGrid.Add(peakFittingSubPanel, (2,0))	
		mainGrid.Add(extractMainSizer, (3,0))	
		mainGrid.Add(processMainSizer, (4,0))
		mainGrid.Add(plot2DMainSizer, (5,0))
		mainGrid.Add(plot1DMainSizer, (6,0))
		mainGrid.Add(plotComparisonSubPanel, (7,0))
		
		# BIND TEXT BOXES : EVT_TEXT
		self.iBinSize.Bind(wx.EVT_TEXT, self.exportToConfig)
		self.iEndVoltage.Bind(wx.EVT_TEXT, self.exportToConfig)
		self.iExpIncrement.Bind(wx.EVT_TEXT, self.exportToConfig)
		self.iExpPercentage.Bind(wx.EVT_TEXT, self.exportToConfig)
		self.iFitScale.Bind(wx.EVT_TEXT, self.exportToConfig)
		self.iMZend.Bind(wx.EVT_TEXT, self.exportToConfig)
		self.iMZstart.Bind(wx.EVT_TEXT, self.exportToConfig)
		self.iSGpoly.Bind(wx.EVT_TEXT, self.exportToConfig)
		self.iSGwindow.Bind(wx.EVT_TEXT, self.exportToConfig)
		self.iSPV.Bind(wx.EVT_TEXT, self.exportToConfig)
		self.iStartScan.Bind(wx.EVT_TEXT, self.exportToConfig)
		self.iStepVoltage.Bind(wx.EVT_TEXT, self.exportToConfig)
		self.iThreshold.Bind(wx.EVT_TEXT, self.exportToConfig)
		self.iStartVoltage.Bind(wx.EVT_TEXT, self.exportToConfig)
		
		self.loadListBtn.Bind(wx.EVT_BUTTON, self.parent.presenter.onUserDefinedListImport)
		
		
# 		self.binMSEachCV_check.Bind(wx.EVT_CHECKBOX, self.enableDisableTxtBoxes)
		self.mzStart_value.Bind(wx.EVT_TEXT, self.enableDisableTxtBoxes)
		self.mzEnd_value.Bind(wx.EVT_TEXT, self.enableDisableTxtBoxes)
		self.mzBin_value.Bind(wx.EVT_TEXT, self.enableDisableTxtBoxes)
		
		self.mzStart_value.Bind(wx.EVT_TEXT, self.exportToConfig)
		self.mzEnd_value.Bind(wx.EVT_TEXT, self.exportToConfig)
		self.mzBin_value.Bind(wx.EVT_TEXT, self.exportToConfig)
		
		self.lineWidth_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.exportToConfig)
		self.detectMode.Bind(wx.EVT_CHOICE, self.exportToConfig)
		self.peakThreshold_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.exportToConfig)
		self.peakWindow_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.exportToConfig)
		self.peakWidth_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.exportToConfig)
		self.showRectanglesCheck.Bind(wx.EVT_CHECKBOX, self.exportToConfig)
		self.autoAddToTableCheck.Bind(wx.EVT_CHECKBOX, self.exportToConfig)
		self.smoothMSCheck.Bind(wx.EVT_CHECKBOX, self.enableDisableTxtBoxes)
		self.smoothMSCheck.Bind(wx.EVT_CHECKBOX, self.exportToConfig)
		self.smooth1D_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.exportToConfig)

		self.binDataCheck.Bind(wx.EVT_CHECKBOX, self.exportToConfig)
		self.binMSfromRT.Bind(wx.EVT_CHECKBOX, self.exportToConfig)		

		self.iMarkerSize.Bind(wx.EVT_TEXT, self.exportToConfig)
		self.annotTransparency_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.exportToConfig)
		self.comboMarkerChoice.Bind(wx.EVT_COMBOBOX, self.exportToConfig)
		self.colorAnnotBtn.Bind(wx.EVT_BUTTON, self.onChangeMarkerColor)
		self.itemWaterfallOffset.Bind(wx.EVT_TEXT, self.exportToConfig)
		self.comboPlotType.Bind(wx.EVT_COMBOBOX, self.enableDisableTxtBoxes)
		self.useColormap_check.Bind(wx.EVT_CHECKBOX, self.exportToConfig)
		self.usePrettyContour_check.Bind(wx.EVT_CHECKBOX, self.exportToConfig)
		self.colorbarWidth_value.Bind(wx.EVT_TEXT, self.exportToConfig)
		self.colorbarPad_value.Bind(wx.EVT_TEXT, self.exportToConfig)
		
		self.useWaterfall_check.Bind(wx.EVT_CHECKBOX, self.exportToConfig)
		self.minCmap_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.exportToConfig)
		self.midCmap_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.exportToConfig)
		self.maxCmap_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.exportToConfig)
		
		self.rmsdColorBtn.Bind(wx.EVT_BUTTON, self.onChangeRMSDColor)
		self.rmsd_fontSize.Bind(wx.EVT_SPINCTRLDOUBLE, self.exportToConfig)
		 
		self.useRestrictedAxis.Bind(wx.EVT_CHECKBOX, self.onUpdateXYaxisLimits)
		self.iXstartRange.Bind(wx.EVT_TEXT, self.exportToConfig)
		self.iXendRange.Bind(wx.EVT_TEXT, self.exportToConfig)
		self.iYstartRange.Bind(wx.EVT_TEXT, self.exportToConfig)
		self.iYendRange.Bind(wx.EVT_TEXT, self.exportToConfig)
		
		self.highResCheck.Bind(wx.EVT_CHECKBOX, self.enableDisableTxtBoxes)
		self.highResCheck.Bind(wx.EVT_CHECKBOX, self.exportToConfig)
		self.peakWidthNarrow_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.exportToConfig)
		self.peakThresholdNarrow_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.exportToConfig)
		self.peakWindowNarrow_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.exportToConfig)
		self.showIsotopesAssign.Bind(wx.EVT_CHECKBOX, self.exportToConfig)
		self.currentRangePeakFitCheck.Bind(wx.EVT_CHECKBOX, self.exportToConfig)

		# BIND COMBO
		self.comboAcqTypeSelect.Bind(wx.EVT_COMBOBOX, self.enableDisableTxtBoxes)
		self.comboSmoothSelect.Bind(wx.EVT_COMBOBOX, self.enableDisableTxtBoxes)
		self.comboCmapSelect.Bind(wx.EVT_COMBOBOX, self.setCmap)
		self.comboInterpolateSelect.Bind(wx.EVT_COMBOBOX, self.setInterp)
		self.normalizationSelect.Bind(wx.EVT_COMBOBOX, self.exportToConfig)
		
		# BIND TOGGLES
		self.colorbarTgl.Bind(wx.EVT_TOGGLEBUTTON, self.OnColorbarToggle)
		self.normalizeTgl.Bind(wx.EVT_TOGGLEBUTTON, self.OnNormalizeToggle)
		self.applyXYLimBtn.Bind(wx.EVT_BUTTON, self.parent.presenter.onZoom2D)
		
		mainSizer.Add(mainGrid, wx.EXPAND |wx.ALL, 2)
		self.notebookSettings_paneML.SetSizer(mainSizer)
		self.notebookSettings_paneML.Layout()
		
		self.enableDisableTxtBoxes(event=None)
		
	def extractSubPanel(self):
	
		extractBox = makeStaticBox(self.notebookSettings_paneML, "Extract Data", (285,-1), wx.BLUE)
		extractMainSizer = wx.StaticBoxSizer(extractBox, wx.HORIZONTAL)
		
		itemStartMZ_label = wx.StaticText(self.notebookSettings_paneML, wx.ID_ANY,
											 u"m/z range", wx.DefaultPosition, 
											 wx.DefaultSize, TEXT_STYLE_CV_R_L)
		
		itemMZSpacer_label = wx.StaticText(self.notebookSettings_paneML, wx.ID_ANY,
											 u"to", wx.DefaultPosition, 
											 wx.DefaultSize, TEXT_STYLE_CV_R_L)

		self.iMZstart = wx.TextCtrl(self.notebookSettings_paneML, -1, "", 
											size=(TXTBOX_SIZE, -1))
		
		self.iMZend = wx.TextCtrl(self.notebookSettings_paneML, -1, "", 
											size=(TXTBOX_SIZE, -1))
		
		itemStartRT_label = wx.StaticText(self.notebookSettings_paneML, wx.ID_ANY,
											 u"RT range", wx.DefaultPosition, 
											 wx.DefaultSize, TEXT_STYLE_CV_R_L)
		
		self.iRTstart = wx.TextCtrl(self.notebookSettings_paneML, -1, "", 
											size=(TXTBOX_SIZE, -1))
		self.iRTstart.Disable()

		itemRTSpacer_label = wx.StaticText(self.notebookSettings_paneML, wx.ID_ANY,
											 u"to", wx.DefaultPosition, 
											 wx.DefaultSize, TEXT_STYLE_CV_R_L)
		
		self.iRTend = wx.TextCtrl(self.notebookSettings_paneML, -1, "", 
											size=(TXTBOX_SIZE, -1))
		self.iRTend.Disable()


		self.extractBtn = wx.Button( self.notebookSettings_paneML, wx.ID_ANY,
								 u"Extract", wx.DefaultPosition, wx.Size( BTN_SIZE,-1 ), 0 )
		
		gridExtract = wx.GridBagSizer(1,1)
		
		gridExtract.Add(itemStartMZ_label, wx.GBPosition(0,0), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		gridExtract.Add(self.iMZstart, wx.GBPosition(0,1), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		gridExtract.Add(itemMZSpacer_label, wx.GBPosition(0,2), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		gridExtract.Add(self.iMZend, wx.GBPosition(0,3), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		
		gridExtract.Add(itemStartRT_label, wx.GBPosition(1,0), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		gridExtract.Add(self.iRTstart, wx.GBPosition(1,1), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		gridExtract.Add(itemRTSpacer_label, wx.GBPosition(1,2), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		gridExtract.Add(self.iRTend, wx.GBPosition(1,3), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		
		gridExtract.Add(self.extractBtn, wx.GBPosition(1,4), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		
		extractMainSizer.Add(gridExtract, 0, wx.EXPAND|wx.ALL, 2)
		
		return extractMainSizer
		
	def processSubPanel(self):
		
		processBox = makeStaticBox(self.notebookSettings_paneML, "Process aIM-MS Data (2D)", (285, -1), wx.BLUE)
		processMainSizer = wx.StaticBoxSizer(processBox, wx.HORIZONTAL)
		
		itemSmoothFcn_label = wx.StaticText(self.notebookSettings_paneML, wx.ID_ANY,
											 u"Smooth \n Function", wx.DefaultPosition, 
											 wx.DefaultSize, TEXT_STYLE_CV_R_L)
		
		self.comboSmoothSelect = wx.ComboBox( self.notebookSettings_paneML, wx.ID_ANY, 
											wx.EmptyString, wx.DefaultPosition, wx.Size( COMBO_SIZE,-1 ), 
											self.config.comboSmoothSelectChoices, COMBO_STYLE, wx.DefaultValidator )
		self.comboSmoothSelect.SetSelection(0) # Pre-sets the value to the first method
				
		self.sSGpoly_GaussSigma = wx.StaticText(self.notebookSettings_paneML, wx.ID_ANY,
											 u"Sav-Gol \n Polynomial", wx.DefaultPosition, 
											 wx.DefaultSize, TEXT_STYLE_CV_R_L)
		self.iSGpoly = wx.TextCtrl(self.notebookSettings_paneML, -1, "", 
											size=(TXTBOX_SIZE, -1)) # also used as sigma
		self.iSGpoly.SetValue(str(self.config.savGolPolyOrder))		


		self.itemSGWindow_label = wx.StaticText(self.notebookSettings_paneML, wx.ID_ANY,
											 u"Sav-Gol \n Window", wx.DefaultPosition, 
											 wx.DefaultSize, TEXT_STYLE_CV_R_L)
		self.iSGwindow = wx.TextCtrl(self.notebookSettings_paneML, -1, "", 
											size=(TXTBOX_SIZE, -1))
		self.iSGwindow.SetValue(str(self.config.savGolWindowSize))
		
		itemThreshold_label = wx.StaticText(self.notebookSettings_paneML, wx.ID_ANY,
											 u"Threshold", wx.DefaultPosition, 
											 wx.DefaultSize, TEXT_STYLE_CV_R_L)
		self.iThreshold = wx.TextCtrl(self.notebookSettings_paneML, -1, "", 
											size=(TXTBOX_SIZE, -1))	
		self.iThreshold.SetValue(str(self.config.threshold))	
		
		itemNormalize_label = wx.StaticText(self.notebookSettings_paneML, wx.ID_ANY,
											 u"Normalize", wx.DefaultPosition, 
											 wx.DefaultSize, TEXT_STYLE_CV_R_L)
		self.normalizationSelect = wx.ComboBox( self.notebookSettings_paneML, wx.ID_ANY, 
											wx.EmptyString, wx.DefaultPosition, wx.Size( COMBO_SIZE,-1 ), 
											self.config.normModeChoices, COMBO_STYLE, wx.DefaultValidator )
		self.normalizationSelect.SetSelection(0) # Pre-sets the value to the first method
		
		self.normalizeTgl = makeToggleBtn(self.notebookSettings_paneML, 'Off', wx.RED)

		gridProcess = wx.GridBagSizer(2,2)
		
		gridProcess.Add(itemSmoothFcn_label, wx.GBPosition(0,0), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		gridProcess.Add(self.comboSmoothSelect, wx.GBPosition(0,1), wx.GBSpan(1,2),ALL_CENTER_VERT,2)
# 		gridProcess.Add(self.processBtn, wx.GBPosition(0,3), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		
		gridProcess.Add(self.sSGpoly_GaussSigma, wx.GBPosition(1,0), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		gridProcess.Add(self.iSGpoly, wx.GBPosition(1,1), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		gridProcess.Add(self.itemSGWindow_label, wx.GBPosition(1,2), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		gridProcess.Add(self.iSGwindow, wx.GBPosition(1,3), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		
		gridProcess.Add(itemThreshold_label, wx.GBPosition(2,0), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		gridProcess.Add(self.iThreshold, wx.GBPosition(2,1), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		gridProcess.Add(itemNormalize_label, wx.GBPosition(3,0), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		gridProcess.Add(self.normalizationSelect, wx.GBPosition(3,1), wx.GBSpan(1,2), TEXT_STYLE_CV_R_L, 2)
		gridProcess.Add(self.normalizeTgl, wx.GBPosition(3,3), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		
		processMainSizer.Add(gridProcess, 0, wx.EXPAND|wx.ALL, 2)
		self.OnNormalizeToggle(event=None)
		
		return processMainSizer
		
	def origamiSubPanel(self):
				

		origamiBox = makeStaticBox(self.notebookSettings_paneML, "ORIGAMI Parameters", (285, -1), wx.BLUE)
		origamiMainSizer = wx.StaticBoxSizer(origamiBox, wx.HORIZONTAL)
		
		itemType_label = wx.StaticText(self.notebookSettings_paneML, wx.ID_ANY,
										 u"Aquisition \ntype", wx.DefaultPosition, 
										 wx.DefaultSize, TEXT_STYLE_CV_R_L)
		
		self.comboAcqTypeSelect = wx.ComboBox(self.notebookSettings_paneML, wx.ID_ANY, 
											wx.EmptyString, wx.DefaultPosition, wx.Size(COMBO_SIZE,-1), 
											self.config.comboAcqTypeSelectChoices, 
											COMBO_STYLE, wx.DefaultValidator )
		self.comboAcqTypeSelect.SetSelection(0) # Pre-sets the value to the first method
		
		self.loadListBtn = wx.Button( self.notebookSettings_paneML, wx.ID_ANY,
								 u"...", wx.DefaultPosition, wx.Size( 25,-1 ), 0 )
	
		itemStartScan_label = wx.StaticText(self.notebookSettings_paneML, wx.ID_ANY,
											 u"Start scan", wx.DefaultPosition, 
											 wx.DefaultSize, TEXT_STYLE_CV_R_L)
		self.iStartScan = wx.TextCtrl(self.notebookSettings_paneML, -1, "", 
											size=(TXTBOX_SIZE, -1),
											validator=validator('intPos'))
		
		itemSPV_label = wx.StaticText(self.notebookSettings_paneML, wx.ID_ANY,
											 u"SPV", wx.DefaultPosition, 
											 wx.DefaultSize, TEXT_STYLE_CV_R_L)
		itemSPV_label.SetToolTip(wx.ToolTip("SPV : Scans Per Voltage"))
		self.iSPV = wx.TextCtrl(self.notebookSettings_paneML, -1, "", 
											size=(TXTBOX_SIZE, -1),
											validator=validator('intPos'))	
		self.iSPV.SetToolTip(wx.ToolTip("Value of Scans Per Voltage. Integer"))
	
		itemStartV_label = wx.StaticText(self.notebookSettings_paneML, wx.ID_ANY,
											 u"Start Voltage", wx.DefaultPosition, 
											 wx.DefaultSize, TEXT_STYLE_CV_R_L)
		self.iStartVoltage = wx.TextCtrl(self.notebookSettings_paneML, -1, "", 
											size=(TXTBOX_SIZE, -1),
											validator=validator('floatPos'))
		
		itemEndV_label = wx.StaticText(self.notebookSettings_paneML, wx.ID_ANY,
											 u"End Voltage", wx.DefaultPosition, 
											 wx.DefaultSize, TEXT_STYLE_CV_R_L)
		self.iEndVoltage = wx.TextCtrl(self.notebookSettings_paneML, -1, "", 
											size=(TXTBOX_SIZE, -1),
											validator=validator('floatPos'))
		
		itemStepVoltage_label = wx.StaticText(self.notebookSettings_paneML, wx.ID_ANY,
											 u"Step \nVoltage", wx.DefaultPosition, 
											 wx.DefaultSize, TEXT_STYLE_CV_R_L)
		self.iStepVoltage = wx.TextCtrl(self.notebookSettings_paneML, -1, "", 
											size=(TXTBOX_SIZE, -1),
											validator=validator('floatPos'))
			
		itemExpPerc_label = wx.StaticText(self.notebookSettings_paneML, wx.ID_ANY,
											 u"Exponential \n%", wx.DefaultPosition, 
											 wx.DefaultSize, TEXT_STYLE_CV_R_L)
		self.iExpPercentage = wx.TextCtrl(self.notebookSettings_paneML, -1, "", 
											size=(TXTBOX_SIZE, -1),
											validator=validator('floatPos'))
		
		itemExpIncrement_label = wx.StaticText(self.notebookSettings_paneML, wx.ID_ANY,
											 u"Exponential \nIncrement", wx.DefaultPosition, 
											 wx.DefaultSize, TEXT_STYLE_CV_R_L)
		self.iExpIncrement = wx.TextCtrl(self.notebookSettings_paneML, -1, "", 
											size=(TXTBOX_SIZE, -1),
											validator=validator('floatPos'))
	
		itemBoltzman_label = wx.StaticText(self.notebookSettings_paneML, wx.ID_ANY,
											 u"Boltzmann \nOffset", wx.DefaultPosition, 
											 wx.DefaultSize, TEXT_STYLE_CV_R_L)
		self.iFitScale = wx.TextCtrl(self.notebookSettings_paneML, -1, "", 
											size=(TXTBOX_SIZE, -1),
											validator=validator('floatPos'))	

# 		self.binMSEachCV_check = makeCheckbox(self.notebookSettings_paneML, u"Extract MS for each CV")
# 		self.binMSEachCV_check.SetToolTip(wx.ToolTip("Tick to extract mass spectra for each collision voltage range."))
# 		self.binMSEachCV_check.SetValue(False)

# 		mzStart_label = wx.StaticText(self.notebookSettings_paneML, wx.ID_ANY,
# 											 u"Start", wx.DefaultPosition, 
# 											 wx.DefaultSize, TEXT_STYLE_CV_R_L)
# 		self.mzStart_value = wx.TextCtrl(self.notebookSettings_paneML, -1, "", 
# 											size=(TXTBOX_SIZE, -1),
# 											validator=validator('floatPos'))
# 		self.mzStart_value.SetValue(str(self.config.binMSstart))
# 		self.mzStart_value.Disable()
# 		
# 		mzEnd_label = wx.StaticText(self.notebookSettings_paneML, wx.ID_ANY,
# 											 u"End", wx.DefaultPosition, 
# 											 wx.DefaultSize, TEXT_STYLE_CV_R_L)
# 		self.mzEnd_value = wx.TextCtrl(self.notebookSettings_paneML, -1, "", 
# 											size=(TXTBOX_SIZE, -1),
# 											validator=validator('floatPos'))
# 		self.mzEnd_value.SetValue(str(self.config.binMSend))
# 		self.mzEnd_value.Disable()
# 		
# 		mzBin_label = wx.StaticText(self.notebookSettings_paneML, wx.ID_ANY,
# 											 u"Bin size", wx.DefaultPosition, 
# 											 wx.DefaultSize, TEXT_STYLE_CV_R_L)
# 		self.mzBin_value = wx.TextCtrl(self.notebookSettings_paneML, -1, "", 
# 											size=(TXTBOX_SIZE, -1),
# 											validator=validator('floatPos'))
# 		self.mzBin_value.SetValue(str(self.config.binMSbinsize))
# 		self.mzBin_value.Disable()

		
		gridOrigami = wx.GridBagSizer(2,2)
		gridOrigami.Add(itemType_label, wx.GBPosition(0,0), wx.GBSpan(1,1), 
					wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT, 2)
		gridOrigami.Add(self.comboAcqTypeSelect, wx.GBPosition(0,1), wx.GBSpan(1,2),
					wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT,2)
		gridOrigami.Add(self.loadListBtn, wx.GBPosition(0,3), wx.GBSpan(1,1),
					wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT,2)
		
		
		gridOrigami.Add(itemStartScan_label, wx.GBPosition(1,0), wx.GBSpan(1,1), 
					wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT, 2)
		gridOrigami.Add(itemSPV_label, wx.GBPosition(1,1), wx.GBSpan(1,1),
					 wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT, 2)
		gridOrigami.Add(itemStartV_label, wx.GBPosition(1,2), wx.GBSpan(1,1), 
					wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT, 2)
		gridOrigami.Add(itemEndV_label, wx.GBPosition(1,3), wx.GBSpan(1,1), 
					wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT, 2)
		
		gridOrigami.Add(self.iStartScan, wx.GBPosition(2,0), wx.GBSpan(1,1), 
					wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT, 2)
		gridOrigami.Add(self.iSPV, wx.GBPosition(2,1), wx.GBSpan(1,1), 
					wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT, 2)
		gridOrigami.Add(self.iStartVoltage, wx.GBPosition(2,2), wx.GBSpan(1,1), 
					wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT, 2)
		gridOrigami.Add(self.iEndVoltage, wx.GBPosition(2,3), wx.GBSpan(1,1), 
					wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT, 2)
 		
 		
		gridOrigami.Add(itemStepVoltage_label, wx.GBPosition(3,0), wx.GBSpan(1,1), 
					wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT, 2)
		gridOrigami.Add(itemBoltzman_label, wx.GBPosition(3,1), wx.GBSpan(1,1), 
					wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT, 2)
		gridOrigami.Add(itemExpPerc_label, wx.GBPosition(3,2), wx.GBSpan(1,1), 
					wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT, 2)
		gridOrigami.Add(itemExpIncrement_label, wx.GBPosition(3,3), wx.GBSpan(1,1), 
					wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT, 2)
		
		gridOrigami.Add(self.iStepVoltage, wx.GBPosition(4,0), wx.GBSpan(1,1), 
					wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT, 2)
		gridOrigami.Add(self.iFitScale, wx.GBPosition(4,1), wx.GBSpan(1,1), 
					wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT, 2)
		gridOrigami.Add(self.iExpPercentage, wx.GBPosition(4,2), wx.GBSpan(1,1), 
					wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT, 2)		
		gridOrigami.Add(self.iExpIncrement, wx.GBPosition(4,3), wx.GBSpan(1,1), 
					wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT, 2)

# 		gridOrigami.Add(self.binMSEachCV_check, wx.GBPosition(5,0), wx.GBSpan(1,3), 
# 					wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT, 2)

# 		gridOrigami.Add(mzStart_label, wx.GBPosition(6,0), wx.GBSpan(1,1), 
# 					wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT, 2)
# 		gridOrigami.Add(mzEnd_label, wx.GBPosition(6,1), wx.GBSpan(1,1), 
# 					wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT, 2)
# 		gridOrigami.Add(mzBin_label, wx.GBPosition(6,2), wx.GBSpan(1,1), 
# 					wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT, 2)
# 		
# 		gridOrigami.Add(self.mzStart_value, wx.GBPosition(7,0), wx.GBSpan(1,1), 
# 					wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT, 2)
# 		gridOrigami.Add(self.mzEnd_value, wx.GBPosition(7,1), wx.GBSpan(1,1), 
# 					wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT, 2)
# 		gridOrigami.Add(self.mzBin_value, wx.GBPosition(7,2), wx.GBSpan(1,1), 
# 					wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT, 2)		
		
		origamiMainSizer.Add(gridOrigami, 0, wx.EXPAND|wx.ALL, 2)
		
		
		return origamiMainSizer
	
	def plot2DSubPanel(self):
		
		plot2Dbox = makeStaticBox(self.notebookSettings_paneML, "Plot 2D Parameters", (285, -1), wx.BLUE)
		plot2DMainSizer = wx.StaticBoxSizer(plot2Dbox, wx.HORIZONTAL)
		
		iXstartRange = makeStaticText(self.notebookSettings_paneML, "Xmin")
		self.iXstartRange = wx.TextCtrl(self.notebookSettings_paneML, -1, "", 
											size=(40, -1),
											validator=validator('floatPos'))
		self.iXstartRange.SetFont(wx.SMALL_FONT)

		self.iXstartRange.SetToolTip(wx.ToolTip("Select range of values displayed in the 2D plot. Set bottom X-axis."))
		
		iXendRange = makeStaticText(self.notebookSettings_paneML, "Xmax")
		self.iXendRange = wx.TextCtrl(self.notebookSettings_paneML, -1, "", 
											size=(40, -1),
											validator=validator('floatPos'))
		self.iXendRange.SetFont(wx.SMALL_FONT)

		self.iXendRange.SetToolTip(wx.ToolTip("Select range of values displayed in the 2D plot. Set top X-axis."))
		
		iYstartRange = makeStaticText(self.notebookSettings_paneML, "Ymin")
		self.iYstartRange = wx.TextCtrl(self.notebookSettings_paneML, -1, "", 
											size=(40, -1),
											validator=validator('floatPos'))
		self.iYstartRange.SetFont(wx.SMALL_FONT)

		self.iYstartRange.SetToolTip(wx.ToolTip("Select range of values displayed in the 2D plot. Set bottom Y-axis."))
		
		iYendRange = makeStaticText(self.notebookSettings_paneML, "Ymax")
		self.iYendRange = wx.TextCtrl(self.notebookSettings_paneML, -1, "", 
											size=(40, -1),
											validator=validator('floatPos'))
		self.iYendRange.SetFont(wx.SMALL_FONT)

		self.iYendRange.SetToolTip(wx.ToolTip("Select range of values displayed in the 2D plot. Set top Y-axis."))
	
		self.useRestrictedAxis = makeCheckbox(self.notebookSettings_paneML, u"Use")
		self.useRestrictedAxis.SetToolTip(wx.ToolTip("Restrict the X/Y axis range"))
		self.useRestrictedAxis.SetValue(self.config.restrictXYrange)
		
		self.applyXYLimBtn = wx.Button( self.notebookSettings_paneML, wx.ID_ANY,
								 u"Apply", wx.DefaultPosition, wx.Size( 45,-1 ), 0 )
		
		
		itemInterpolate_label = wx.StaticText(self.notebookSettings_paneML, wx.ID_ANY,
											 u"2D Interpolation", wx.DefaultPosition, 
											 wx.DefaultSize, TEXT_STYLE_CV_R_L)
		
		self.comboInterpolateSelect = wx.ComboBox( self.notebookSettings_paneML, wx.ID_ANY, 
											wx.EmptyString, wx.DefaultPosition, wx.Size( COMBO_SIZE,-1 ), 
											self.config.comboInterpSelectChoices, COMBO_STYLE, wx.DefaultValidator )
		self.comboInterpolateSelect.SetSelection(0) # Pre-sets the value to the first method
		
		itemColormap_label = wx.StaticText(self.notebookSettings_paneML, wx.ID_ANY,
											 u"Colormap", wx.DefaultPosition, 
											 wx.DefaultSize, TEXT_STYLE_CV_R_L)
				
		self.comboCmapSelect = wx.ComboBox( self.notebookSettings_paneML, wx.ID_ANY, 
											wx.EmptyString, wx.DefaultPosition, wx.Size( COMBO_SIZE,-1 ), 
											self.config.cmaps2, COMBO_STYLE, wx.DefaultValidator )
		self.comboCmapSelect.SetStringSelection(self.config.currentCmap) # Pre-sets the value to the first method
	
		self.useColormap_check = makeCheckbox(self.notebookSettings_paneML, u"Override colormap")
		self.useColormap_check.SetToolTip(wx.ToolTip("If checked, the currently selected colormap will be used to plot 2D and 3D plots. If unchecked, the colormap associated with the document (and item) will be used instead.")) 
		self.useColormap_check.SetValue(self.config.useCurrentCmap)
		
		minCmap_label = makeStaticText(self.notebookSettings_paneML, u"Min %")
		self.minCmap_value = wx.SpinCtrlDouble(self.notebookSettings_paneML, wx.ID_ANY, 
											   value=str(self.config.minCmap),min=0, max=100,
                                               initial=0, inc=0.5, size=(60,-1))

		midCmap_label = makeStaticText(self.notebookSettings_paneML, u"Mid %")
		self.midCmap_value = wx.SpinCtrlDouble(self.notebookSettings_paneML, wx.ID_ANY, 
											   value=str(self.config.midCmap),min=0, max=100,
                                               initial=0, inc=0.5, size=(60,-1))
		
		maxCmap_label = makeStaticText(self.notebookSettings_paneML, u"Max %")
		self.maxCmap_value = wx.SpinCtrlDouble(self.notebookSettings_paneML, wx.ID_ANY, 
											   value=str(self.config.maxCmap),min=0, max=100,
                                               initial=0, inc=0.5, size=(60,-1))

		itemPlotType_label = wx.StaticText(self.notebookSettings_paneML, wx.ID_ANY,
											 u"2D Plot Type", wx.DefaultPosition, 
											 wx.DefaultSize, TEXT_STYLE_CV_R_L)
		
		self.comboPlotType = wx.ComboBox( self.notebookSettings_paneML, wx.ID_ANY, 
											wx.EmptyString, wx.DefaultPosition, wx.Size( COMBO_SIZE,-1 ), 
											self.config.imageType2D, COMBO_STYLE, wx.DefaultValidator )
		self.comboPlotType.SetStringSelection(self.config.plotType) # Pre-sets the value to the first method
		
		self.usePrettyContour_check = makeCheckbox(self.notebookSettings_paneML, u"Pretty")
		self.usePrettyContour_check.SetToolTip(wx.ToolTip("Use selected colormap for each 2D plot"))
		self.usePrettyContour_check.SetValue(self.config.prettyContour)
		self.usePrettyContour_check.Hide()

		itemColorbar_label = wx.StaticText(self.notebookSettings_paneML, wx.ID_ANY,
											 u"Colorbar", wx.DefaultPosition, 
											 wx.DefaultSize, TEXT_STYLE_CV_R_L)
		self.colorbarTgl = makeToggleBtn(self.notebookSettings_paneML, 'Off', wx.RED)
		
		self.colorbarWidth_value = wx.SpinCtrlDouble(self.notebookSettings_paneML, wx.ID_ANY, 
											   value=str(self.config.colorbarWidth),min=0.25, max=10,
                                               initial=0, inc=0.25, size=(50,-1))
		self.colorbarWidth_value.SetToolTip(wx.ToolTip("Colorbar width. Set as percentage of the 2D plot. \nDefault: 2"))
		
		self.colorbarPad_value = wx.SpinCtrlDouble(self.notebookSettings_paneML, wx.ID_ANY, 
											   value=str(self.config.colorbarPad),min=0.0, max=1,
                                               initial=0, inc=0.01, size=(50,-1))
		self.colorbarPad_value.SetToolTip(wx.ToolTip("Colorbar pad = distance between the plot and the colorbar. Set as fraction of the 2D plot. \nDefault: 0.03"))
		
		
		gridPlot2D = wx.GridBagSizer(2,2)
		gridPlot2D.Add(iXstartRange, wx.GBPosition(0,0), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		gridPlot2D.Add(iXendRange, wx.GBPosition(0,1), wx.GBSpan(1,1),ALL_CENTER_VERT,2)
		gridPlot2D.Add(iYstartRange, wx.GBPosition(0,2), wx.GBSpan(1,1),TEXT_STYLE_CV_R_L,2)
		gridPlot2D.Add(iYendRange, wx.GBPosition(0,3), wx.GBSpan(1,1),ALL_CENTER_VERT,2)
		
		gridPlot2D.Add(self.iXstartRange, wx.GBPosition(1,0), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		gridPlot2D.Add(self.iXendRange, wx.GBPosition(1,1), wx.GBSpan(1,1),ALL_CENTER_VERT,2)
		gridPlot2D.Add(self.iYstartRange, wx.GBPosition(1,2), wx.GBSpan(1,1),TEXT_STYLE_CV_R_L,2)
		gridPlot2D.Add(self.iYendRange, wx.GBPosition(1,3), wx.GBSpan(1,1),ALL_CENTER_VERT,2)
		gridPlot2D.Add(self.useRestrictedAxis, wx.GBPosition(0,4), wx.GBSpan(1,1),ALL_CENTER_VERT,2)
		gridPlot2D.Add(self.applyXYLimBtn, wx.GBPosition(1,4), wx.GBSpan(1,1),ALL_CENTER_VERT,2)
		
		gridPlot2D.Add(itemInterpolate_label, wx.GBPosition(2,0), wx.GBSpan(1,3), TEXT_STYLE_CV_R_L, 2)
		gridPlot2D.Add(self.comboInterpolateSelect, wx.GBPosition(3,0), wx.GBSpan(1,3),ALL_CENTER_VERT,2)
		
		gridPlot2D.Add(itemPlotType_label, wx.GBPosition(2,3), wx.GBSpan(1,3), TEXT_STYLE_CV_R_L, 2)
		gridPlot2D.Add(self.comboPlotType, wx.GBPosition(3,3), wx.GBSpan(1,3),ALL_CENTER_VERT,2)
		gridPlot2D.Add(self.usePrettyContour_check, wx.GBPosition(3,7), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		
		gridPlot2D.Add(itemColormap_label, wx.GBPosition(4,0), wx.GBSpan(1,3), TEXT_STYLE_CV_R_L, 2)
		gridPlot2D.Add(self.comboCmapSelect, wx.GBPosition(5,0), wx.GBSpan(1,3),ALL_CENTER_VERT,2)
		
		gridPlot2D.Add(self.useColormap_check, wx.GBPosition(5,3), wx.GBSpan(1,3), 
					wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT, 2)
  		
		gridPlot2D.Add(minCmap_label, wx.GBPosition(6,0), wx.GBSpan(1,2), wx.ALIGN_LEFT, 2)
		gridPlot2D.Add(self.minCmap_value, wx.GBPosition(7,0), wx.GBSpan(1,2), TEXT_STYLE_CV_R_L, 2)
   	
		gridPlot2D.Add(midCmap_label, wx.GBPosition(6,2), wx.GBSpan(1,2), wx.ALIGN_LEFT, 2)
		gridPlot2D.Add(self.midCmap_value, wx.GBPosition(7,2), wx.GBSpan(1,2), TEXT_STYLE_CV_R_L, 2)
   		
		gridPlot2D.Add(maxCmap_label, wx.GBPosition(6,4), wx.GBSpan(1,2), wx.ALIGN_LEFT, 2)
		gridPlot2D.Add(self.maxCmap_value, wx.GBPosition(7,4), wx.GBSpan(1,2), TEXT_STYLE_CV_R_L, 2)
   		
		gridPlot2D.Add(itemColorbar_label, wx.GBPosition(8,0), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		gridPlot2D.Add(self.colorbarTgl, wx.GBPosition(8,1), wx.GBSpan(1,1),ALL_CENTER_VERT,2)
		gridPlot2D.Add(self.colorbarWidth_value, wx.GBPosition(8,2), wx.GBSpan(1,2), 
					wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT,2)
		
		gridPlot2D.Add(self.colorbarPad_value, wx.GBPosition(8,4), wx.GBSpan(1,2), 
					wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT,2)

		self.OnColorbarToggle(event=None)
		self.onUpdateXYaxisLimits(evt=None)
		plot2DMainSizer.Add(gridPlot2D, 0, wx.EXPAND|wx.ALL, 2)
		
		return plot2DMainSizer
		
	def plot1DSubPanel(self):
		
		plot1Dbox = makeStaticBox(self.notebookSettings_paneML, "Plot 1D Parameters", (285, -1), wx.BLUE)
		plot1DMainSizer = wx.StaticBoxSizer(plot1Dbox, wx.HORIZONTAL)
		
		lineWidth_label = makeStaticText(self.notebookSettings_paneML, u"Line width and color")
		lineWidth_label.SetToolTip(wx.ToolTip("Select thickness and color of the lines in 1D plots. Note: Line thickness is divided by 10."))
		self.lineWidth_value = wx.SpinCtrlDouble(self.notebookSettings_paneML, wx.ID_ANY, 
                                                  value=str(self.config.lineWidth),min=1, max=100,
                                                  initial=self.config.lineWidth, inc=5, size=(50,-1))

		self.colorBtn = wx.Button( self.notebookSettings_paneML, wx.ID_ANY,
								 u"", wx.DefaultPosition, wx.Size( 26, 26 ), 0 )
		self.colorBtn.SetBackgroundColour(self.config.lineColour)
	

		annotTransparency_label = wx.StaticText(self.notebookSettings_paneML, wx.ID_ANY,
											u"Transparency and color", wx.DefaultPosition, 
											 wx.DefaultSize, TEXT_STYLE_CV_R_L)
		annotTransparency_label.SetToolTip(wx.ToolTip("Select transparency and color of the drawn rectangles on 1D plots. \nDefaults: color : blue, transparency : 40%"))
		
		self.annotTransparency_value = wx.SpinCtrlDouble(self.notebookSettings_paneML, wx.ID_ANY, 
                                                 		 value=str(self.config.annotTransparency),min=1, max=100,
                                                    	 initial=self.config.annotTransparency, inc=5, size=(50,-1))
		
		self.colorAnnotBtn = wx.Button( self.notebookSettings_paneML, wx.ID_ANY,
										u"", wx.DefaultPosition, wx.Size( 26, 26 ), 0 )
		rgb = (self.config.annotColor[0]*255, self.config.annotColor[1]*255,self.config.annotColor[2]*255)
		self.colorAnnotBtn.SetBackgroundColour(rgb)
		
		itemMarkerType = wx.StaticText(self.notebookSettings_paneML, wx.ID_ANY,
											 u"Marker size \nshape", wx.DefaultPosition, 
											 wx.DefaultSize, TEXT_STYLE_CV_R_L)
		
		self.comboMarkerChoice = wx.ComboBox( self.notebookSettings_paneML, wx.ID_ANY, 
											wx.EmptyString, wx.DefaultPosition, wx.Size( COMBO_SIZE,-1 ), 
											self.config.markerShapeDict.keys(), COMBO_STYLE, wx.DefaultValidator )
		self.comboMarkerChoice.SetStringSelection(self.config.markerShapeTXT)
		
		self.iMarkerSize = wx.TextCtrl(self.notebookSettings_paneML, -1, "", 
											size=(TXTBOX_SIZE, -1))
		self.iMarkerSize.SetValue(num2str(self.config.markerSize))
		
		itemWaterfallOffset_label = wx.StaticText(self.notebookSettings_paneML, wx.ID_ANY,
											 u"Waterfall \nOffset", wx.DefaultPosition, 
											 wx.DefaultSize, TEXT_STYLE_CV_R_L)
		self.itemWaterfallOffset = wx.TextCtrl(self.notebookSettings_paneML, -1, "", 
											size=(TXTBOX_SIZE, -1))
		self.itemWaterfallOffset.SetValue(num2str(self.config.waterfallOffset))
		self.itemWaterfallOffset.SetToolTip(wx.ToolTip("Offset between lines in the Y-axis. \nDefault: 0.05"))
		
		self.useWaterfall_check = makeCheckbox(self.notebookSettings_paneML, u"Plot waterfall")
		self.useWaterfall_check.SetToolTip(wx.ToolTip("Select whether ORIGAMI should add waterfall plot each time 2D \narray is plotted. \nRecommendation: Deselect for large files."))
		self.useWaterfall_check.SetValue(self.config.addWaterfall)
		

		gridPlot1D = wx.GridBagSizer(2,2)
		
		gridPlot1D.Add(lineWidth_label, wx.GBPosition(0,0), wx.GBSpan(1,2), TEXT_STYLE_CV_R_L, 2)
		gridPlot1D.Add(self.lineWidth_value, wx.GBPosition(1,0), wx.GBSpan(1,1),ALL_CENTER_VERT,2)	
		gridPlot1D.Add(self.colorBtn, wx.GBPosition(1,1), wx.GBSpan(1,1),wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT,2)
		
		gridPlot1D.Add(annotTransparency_label, wx.GBPosition(0,2), wx.GBSpan(1,2), TEXT_STYLE_CV_R_L, 2)
		gridPlot1D.Add(self.annotTransparency_value, wx.GBPosition(1,2), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		gridPlot1D.Add(self.colorAnnotBtn, wx.GBPosition(1,3), wx.GBSpan(1,1),wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT,2)

		gridPlot1D.Add(itemMarkerType, wx.GBPosition(2,0), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		gridPlot1D.Add(self.iMarkerSize, wx.GBPosition(2,1), wx.GBSpan(1,1),ALL_CENTER_VERT,2)
		gridPlot1D.Add(self.comboMarkerChoice, wx.GBPosition(2,2), wx.GBSpan(1,2),ALL_CENTER_VERT,2)
 
		gridPlot1D.Add(itemWaterfallOffset_label, wx.GBPosition(3,0), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		gridPlot1D.Add(self.itemWaterfallOffset, wx.GBPosition(3,1), wx.GBSpan(1,1),ALL_CENTER_VERT,2)
		gridPlot1D.Add(self.useWaterfall_check, wx.GBPosition(3,2), wx.GBSpan(1,2),ALL_CENTER_VERT,2)
					
		plot1DMainSizer.Add(gridPlot1D, 0, wx.EXPAND|wx.ALL, 2)
		plot1DMainSizer.Layout()
		
		return plot1DMainSizer
		
	def plotComparisonSubPanel(self):
		plot2Dbox = makeStaticBox(self.notebookSettings_paneML, "Comparison (RMSD) Parameters", (285, -1), wx.BLUE)
		plot2DMainSizer = wx.StaticBoxSizer(plot2Dbox, wx.HORIZONTAL)
		label_size = (30,30)
		rmsdLabel_label = makeStaticText(self.notebookSettings_paneML, u"Position of RMSD label")
		self.rmsdLabel_leftBottom = wx.ToggleButton(self.notebookSettings_paneML, ID_ANY,size=label_size)
		self.rmsdLabel_leftBottom.SetBitmap(self.icons.iconsLib['rmsdBottomLeft'])
		self.rmsdLabel_leftTop = wx.ToggleButton(self.notebookSettings_paneML, ID_ANY,size=label_size)
		self.rmsdLabel_leftTop.SetBitmap(self.icons.iconsLib['rmsdTopLeft'])
		self.rmsdLabel_rightTop = wx.ToggleButton(self.notebookSettings_paneML, ID_ANY,size=label_size)
		self.rmsdLabel_rightTop.SetBitmap(self.icons.iconsLib['rmsdTopRight'])
		self.rmsdLabel_rightBottom = wx.ToggleButton(self.notebookSettings_paneML, ID_ANY,size=label_size)
		self.rmsdLabel_rightBottom.SetBitmap(self.icons.iconsLib['rmsdBottomRight'])
		self.rmsdLabel_None = wx.ToggleButton(self.notebookSettings_paneML, ID_ANY,size=label_size)
		self.rmsdLabel_None.SetBitmap(self.icons.iconsLib['rmsdNone'])
		
		rmsdColorSize_label = makeStaticText(self.notebookSettings_paneML, u"Color and font size")
		self.rmsdColorBtn = wx.Button( self.notebookSettings_paneML, wx.ID_ANY,
								 u"", wx.DefaultPosition, wx.Size( 26, 26 ), 0 )
		rgb = (self.config.rmsdColor[0]*255, self.config.rmsdColor[1]*255,self.config.rmsdColor[2]*255)
		self.rmsdColorBtn.SetBackgroundColour(rgb)
		
		self.rmsd_fontSize = wx.SpinCtrlDouble(self.notebookSettings_paneML, wx.ID_ANY, 
                                                  value=str(self.config.lineWidth),min=8, max=32,
                                                  initial=self.config.rmsdFontSize, inc=1, size=(50,-1))
		self.rmsd_fontWeight = makeCheckbox(self.notebookSettings_paneML, u"Bold")
		self.rmsd_fontWeight.SetValue(self.config.rmsdFontWeight)
		self.rmsd_fontWeight.SetToolTip(makeTooltip(text="Enable/disable RMSD label font weight"))
		
		# RMSD matrix 
		rmsdMatrix_label = makeStaticText(self.notebookSettings_paneML, u"Rotation of RMSD Matrix labels")
		rmsdRotX_label = makeStaticText(self.notebookSettings_paneML, u"Rot X")
		self.rmsdRotX = wx.SpinCtrlDouble(self.notebookSettings_paneML, wx.ID_ANY, 
                                          value=str(self.config.rmsdRotX),min=0, max=360,
                                          initial=45, inc=45, size=(50,-1))
		self.rmsdRotX.SetToolTip(makeTooltip(text="Rotation angle of X-axis labels in the RMSD matrix plot"))
		
		rmsdRotY_label = makeStaticText(self.notebookSettings_paneML, u"Rot Y")
		self.rmsdRotY = wx.SpinCtrlDouble(self.notebookSettings_paneML, wx.ID_ANY, 
                                          value=str(self.config.rmsdRotY),min=0, max=360,
                                          initial=45, inc=45, size=(50,-1))
		self.rmsdRotY.SetToolTip(makeTooltip(text="Rotation angle of Y-axis labels in the RMSD matrix plot"))
		
		
		iXstartRange = makeStaticText(self.notebookSettings_paneML, "Xmin")
		self.iXstartRangeRMSD = wx.TextCtrl(self.notebookSettings_paneML, -1, "", 
											size=(55, -1), validator=validator('floatPos'))
		self.iXstartRangeRMSD.SetFont(wx.SMALL_FONT)
		
		iXendRange = makeStaticText(self.notebookSettings_paneML, "Xmax")
		self.iXendRangeRMSD = wx.TextCtrl(self.notebookSettings_paneML, -1, "", 
											size=(55, -1), validator=validator('floatPos'))
		self.iXendRangeRMSD.SetFont(wx.SMALL_FONT)

		iYstartRange = makeStaticText(self.notebookSettings_paneML, "Ymin")
		self.iYstartRangeRMSD = wx.TextCtrl(self.notebookSettings_paneML, -1, "", 
											size=(55, -1), validator=validator('floatPos'))
		self.iYstartRangeRMSD.SetFont(wx.SMALL_FONT)
		
		iYendRange = makeStaticText(self.notebookSettings_paneML, "Ymax")
		self.iYendRangeRMSD = wx.TextCtrl(self.notebookSettings_paneML, -1, "", 
											size=(55, -1), validator=validator('floatPos'))
		self.iYendRangeRMSD.SetFont(wx.SMALL_FONT)
		
		self.useRestrictedAxisRMSD = makeCheckbox(self.notebookSettings_paneML, u"Restrict RMSD range")
		self.useRestrictedAxisRMSD.SetToolTip(wx.ToolTip("Restrict the X/Y axis range in RMSD/F calculations"))
		self.useRestrictedAxisRMSD.SetValue(self.config.restrictXYrangeRMSD)
		
		# Bind toggle
		self.rmsdLabel_leftBottom.Bind(wx.EVT_TOGGLEBUTTON, self.OnRMSDLabelToggle)	
		self.rmsdLabel_leftTop.Bind(wx.EVT_TOGGLEBUTTON, self.OnRMSDLabelToggle)	
		self.rmsdLabel_rightTop.Bind(wx.EVT_TOGGLEBUTTON, self.OnRMSDLabelToggle)	
		self.rmsdLabel_rightBottom.Bind(wx.EVT_TOGGLEBUTTON, self.OnRMSDLabelToggle)
		self.rmsdLabel_None.Bind(wx.EVT_TOGGLEBUTTON, self.OnRMSDLabelToggle)	
		
		self.rmsd_fontWeight.Bind(wx.EVT_CHECKBOX, self.exportToConfig)
		
		self.rmsdRotX.Bind(wx.EVT_SPINCTRLDOUBLE, self.exportToConfig)
		self.rmsdRotY.Bind(wx.EVT_SPINCTRLDOUBLE, self.exportToConfig)
				
		self.useRestrictedAxisRMSD.Bind(wx.EVT_CHECKBOX, self.onUpdateXYaxisLimitsRMSD)
		
		self.iXstartRangeRMSD.Bind(wx.EVT_TEXT, self.exportToConfig)
		self.iXendRangeRMSD.Bind(wx.EVT_TEXT, self.exportToConfig)
		self.iYstartRangeRMSD.Bind(wx.EVT_TEXT, self.exportToConfig)
		self.iYendRangeRMSD.Bind(wx.EVT_TEXT, self.exportToConfig)
				
		grid = wx.GridBagSizer(2,2)
		
		y=0
		grid.Add(rmsdLabel_label, wx.GBPosition(y,0), 
				wx.GBSpan(1,5), TEXT_STYLE_CV_R_L, 2)
		y=y+1
		grid.Add(self.rmsdLabel_leftBottom, wx.GBPosition(y,0), 
				wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
 		grid.Add(self.rmsdLabel_leftTop, wx.GBPosition(y,1), 
				wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		grid.Add(self.rmsdLabel_rightTop, wx.GBPosition(y,2), 
				wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
 		grid.Add(self.rmsdLabel_rightBottom, wx.GBPosition(y,3), 
				wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
 		grid.Add(self.rmsdLabel_None, wx.GBPosition(y,4), 
				wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
  		y=y+1
  		grid.Add(rmsdColorSize_label, wx.GBPosition(y,0), 
				wx.GBSpan(1,5), TEXT_STYLE_CV_R_L, 2)
 		y=y+1
 		grid.Add(self.rmsdColorBtn, wx.GBPosition(y,0), 
				wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
  		grid.Add(self.rmsd_fontSize, wx.GBPosition(y,1), 
				wx.GBSpan(1,2), TEXT_STYLE_CV_R_L, 2)
  		grid.Add(self.rmsd_fontWeight, wx.GBPosition(y,3), 
				wx.GBSpan(1,2), TEXT_STYLE_CV_R_L, 2)
  		y=y+1
  		grid.Add(rmsdMatrix_label, wx.GBPosition(y,0), 
				wx.GBSpan(1,5), TEXT_STYLE_CV_R_L, 2)
  		y=y+1
   		grid.Add(rmsdRotX_label, wx.GBPosition(y,0), 
				wx.GBSpan(1,1), wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 2)
  		grid.Add(self.rmsdRotX, wx.GBPosition(y,1), 
				wx.GBSpan(1,2), TEXT_STYLE_CV_R_L, 2)
   		grid.Add(rmsdRotY_label, wx.GBPosition(y,3), 
				wx.GBSpan(1,1), wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 2)
  		grid.Add(self.rmsdRotY, wx.GBPosition(y,4), 
				wx.GBSpan(1,2), TEXT_STYLE_CV_R_L, 2)
 	
 		y=y+1
 		grid.Add(self.useRestrictedAxisRMSD, wx.GBPosition(y,0), wx.GBSpan(1,4), TEXT_STYLE_CV_R_L, 2)
 		
 		y=y+1
		grid.Add(iXstartRange, wx.GBPosition(y,0), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		grid.Add(self.iXstartRangeRMSD, wx.GBPosition(y,1), wx.GBSpan(1,2), TEXT_STYLE_CV_R_L, 2)
		grid.Add(iXendRange, wx.GBPosition(y,3), wx.GBSpan(1,1),ALL_CENTER_VERT,2)
		grid.Add(self.iXendRangeRMSD, wx.GBPosition(y,4), wx.GBSpan(1,2),ALL_CENTER_VERT,2)
		y=y+1
		grid.Add(iYstartRange, wx.GBPosition(y,0), wx.GBSpan(1,1),TEXT_STYLE_CV_R_L,2)
		grid.Add(self.iYstartRangeRMSD, wx.GBPosition(y,1), wx.GBSpan(1,2),TEXT_STYLE_CV_R_L,2)
		grid.Add(iYendRange, wx.GBPosition(y,3), wx.GBSpan(1,1),ALL_CENTER_VERT,2)
		grid.Add(self.iYendRangeRMSD, wx.GBPosition(y,4), wx.GBSpan(1,2),ALL_CENTER_VERT,2)

		plot2DMainSizer.Add(grid, 0, wx.EXPAND|wx.ALL, 2)
		
		self.onUpdateXYaxisLimitsRMSD(evt=None)
		
		return plot2DMainSizer
		
	def fileSubPanel(self):
	
		fileBox = makeStaticBox(self.notebookSettings_paneML, "Extraction Parameters", (285, -1), wx.BLUE)
		fileMainSizer = wx.StaticBoxSizer(fileBox, wx.HORIZONTAL)

		msExtract_label = wx.StaticText(self.notebookSettings_paneML, wx.ID_ANY,
											 u"MS", wx.DefaultPosition, 
											 wx.DefaultSize, TEXT_STYLE_CV_R_L)
				
		mzBin_label = wx.StaticText(self.notebookSettings_paneML, wx.ID_ANY,
											 u"Bin size", wx.DefaultPosition, 
											 wx.DefaultSize, TEXT_STYLE_CV_R_L)
		self.mzBin_value = wx.TextCtrl(self.notebookSettings_paneML, -1, "", 
											size=(TXTBOX_SIZE, -1),
											validator=validator('floatPos'))
		self.mzBin_value.SetValue(str(self.config.binMSbinsize))
		
		mzStart_label = wx.StaticText(self.notebookSettings_paneML, wx.ID_ANY,
											 u"Start", wx.DefaultPosition, 
											 wx.DefaultSize, TEXT_STYLE_CV_R_L)
		self.mzStart_value = wx.TextCtrl(self.notebookSettings_paneML, -1, "", 
											size=(TXTBOX_SIZE, -1),
											validator=validator('floatPos'))
		self.mzStart_value.SetValue(str(self.config.binMSstart))
		
		mzEnd_label = wx.StaticText(self.notebookSettings_paneML, wx.ID_ANY,
											 u"End", wx.DefaultPosition, 
											 wx.DefaultSize, TEXT_STYLE_CV_R_L)
		self.mzEnd_value = wx.TextCtrl(self.notebookSettings_paneML, -1, "", 
											size=(TXTBOX_SIZE, -1),
											validator=validator('floatPos'))
		self.mzEnd_value.SetValue(str(self.config.binMSend))
		
		msdtExtract_label = wx.StaticText(self.notebookSettings_paneML, wx.ID_ANY,
											 u"DT/MS", wx.DefaultPosition, 
											 wx.DefaultSize, TEXT_STYLE_CV_R_L)
		self.iBinSize = wx.TextCtrl(self.notebookSettings_paneML, -1, "", 
											size=(TXTBOX_SIZE, -1))	
		self.iBinSize.SetValue(num2str(self.config.binSizeMZDT))
		self.iBinSize.SetToolTip(wx.ToolTip("Spacing between m/z peaks in the two dimensional plot of mass spectrum vs drift time. The smaller the value, the higher number of points in the plot area (making it slower to process."))
		
		self.binDataCheck = makeCheckbox(self.notebookSettings_paneML, u"Bin MS on load (Multiple files)")
		self.binDataCheck.SetValue(self.config.binOnLoad)
		self.binDataCheck.SetToolTip(wx.ToolTip("Enable/disable to enforce binning of MS spectra upon loading multiple MassLynx files."))
		
	
		self.binMSfromRT = makeCheckbox(self.notebookSettings_paneML, u"Bin MS extracted from RT window")
		self.binMSfromRT.SetValue(self.config.binMSfromRT)
		self.binMSfromRT.SetToolTip(wx.ToolTip("Enable to bin MS extracted for specified region in the RT plot (limits the number of MS points) or extract MS to obtain optimal peak shape and less limited number of points."))
		
# 		itemMolWeight_label = wx.StaticText(self.notebookSettings_paneML, wx.ID_ANY,
# 											 u"Molecular \nweight", wx.DefaultPosition, 
#  											wx.DefaultSize, TEXT_STYLE_CV_R_L)
# 		self.iMolWeight = wx.TextCtrl(self.notebookSettings_paneML, -1, "", 
# 											size=(TXTBOX_SIZE, -1))	
# 		self.iMolWeight.SetToolTip(wx.ToolTip("Molecular weight of the intact ion. \nNote: Used with very crude deconvolution algorithm. Does not work for fragment ions, yet"))
# 		self.iMolWeight.Disable()
		
		gridFile = wx.GridBagSizer(2,2)
		n = 0
		gridFile.Add(mzStart_label, wx.GBPosition(n,2), wx.GBSpan(1,1), 
					wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT, 2)
		gridFile.Add(mzEnd_label, wx.GBPosition(n,3), wx.GBSpan(1,1), 
					wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT, 2)
		gridFile.Add(mzBin_label, wx.GBPosition(n,1), wx.GBSpan(1,1), 
					wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT, 2)
		n = n +1
		gridFile.Add(msExtract_label, wx.GBPosition(n,0), wx.GBSpan(1,1), 
					wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT, 2)
		gridFile.Add(self.mzStart_value, wx.GBPosition(n,2), wx.GBSpan(1,1), 
					wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT, 2)
		gridFile.Add(self.mzEnd_value, wx.GBPosition(n,3), wx.GBSpan(1,1), 
					wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT, 2)
		gridFile.Add(self.mzBin_value, wx.GBPosition(n,1), wx.GBSpan(1,1), 
					wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT, 2)
		n = n +1
		gridFile.Add(msdtExtract_label, wx.GBPosition(n,0), wx.GBSpan(1,1), 
					wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT, 2)
		gridFile.Add(self.iBinSize, wx.GBPosition(n,1), wx.GBSpan(1,1), 
					wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT, 2)
		
		n = n +1
		gridFile.Add(self.binDataCheck, wx.GBPosition(n,0), wx.GBSpan(1,5), 
					ALL_CENTER_VERT,2)
		n = n +1
		gridFile.Add(self.binMSfromRT, wx.GBPosition(n,0), wx.GBSpan(1,5), 
					ALL_CENTER_VERT,2)
		

		
#  		
# 		gridFile.Add(itemMolWeight_label, wx.GBPosition(0,3), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
# 		gridFile.Add(self.iMolWeight, wx.GBPosition(0,4), wx.GBSpan(1,1),ALL_CENTER_VERT,2)
		
		fileMainSizer.Add(gridFile, 0, wx.EXPAND|wx.ALL, 2)
		
		return fileMainSizer
#
#===============================================================================
# CANVAS SETTINGS - PLOT PROPERTIES
#===============================================================================

	def peakFittingSubPanel(self):
	
		fileBox = makeStaticBox(self.notebookSettings_paneML, "Peak Fitting", (285, -1), wx.BLUE)
		fileMainSizer = wx.StaticBoxSizer(fileBox, wx.HORIZONTAL)

		threshold_label = wx.StaticText(self.notebookSettings_paneML, wx.ID_ANY,
											 u"Threshold", wx.DefaultPosition, 
											 wx.DefaultSize, TEXT_STYLE_CV_R_L)
		self.peakThreshold_value = wx.SpinCtrlDouble(self.notebookSettings_paneML, 
												wx.ID_ANY, value=str(self.config.peakThreshold),
												min=0, max=1, initial=self.config.peakThreshold, 
												inc=0.05, size=(50,-1))
				
		window_label = wx.StaticText(self.notebookSettings_paneML, wx.ID_ANY,
											 u"Window size", wx.DefaultPosition, 
											 wx.DefaultSize, TEXT_STYLE_CV_R_L)
		self.peakWindow_value = wx.SpinCtrlDouble(self.notebookSettings_paneML, 
												wx.ID_ANY, value=str(self.config.peakWindow),
												min=1, max=10000, initial=self.config.peakWindow, 
												inc=50, size=(60,-1))

		peakWidth_label = wx.StaticText(self.notebookSettings_paneML, wx.ID_ANY,
										u"Peak width", wx.DefaultPosition, 
										wx.DefaultSize, TEXT_STYLE_CV_R_L)
		
		self.peakWidth_value = wx.SpinCtrlDouble(self.notebookSettings_paneML, 
												wx.ID_ANY, value=str(self.config.peakWidth),
												min=0, max=500, initial=self.config.peakWidth, 
												inc=1, size=(50,-1))
		
		detectMode_label = wx.StaticText(self.notebookSettings_paneML, wx.ID_ANY,
											 u"Fit plot", wx.DefaultPosition, 
											 wx.DefaultSize, TEXT_STYLE_CV_R_L)
		
		self.detectMode = wx.Choice(self.notebookSettings_paneML, wx.ID_ANY, 
								choices=self.config.detectModeChoices) 
		self.detectMode.SetToolTip(wx.ToolTip("Find peaks in MS, RT, MS/RT, DT or MS/DT window(s). For now only MS and RT work."))
		self.detectMode.SetSelection(0)
	
		self.findPeaksBtn = wx.Button( self.notebookSettings_paneML, wx.ID_ANY,
									u"Find Peaks", wx.DefaultPosition, wx.Size( 70,-1 ), 0 )
		
		self.showRectanglesCheck = makeCheckbox(self.notebookSettings_paneML, u"Show")
		self.showRectanglesCheck.SetToolTip(wx.ToolTip("Highlight on found peaks"))
		self.showRectanglesCheck.SetValue(self.config.showRectanges)

		self.currentRangePeakFitCheck = makeCheckbox(self.notebookSettings_paneML, u"Current X-limits")
		self.currentRangePeakFitCheck.SetToolTip(wx.ToolTip("Find peaks for current m/z range only"))

		
		# Charge detection 
		self.highResCheck = makeCheckbox(self.notebookSettings_paneML, u"High-Res")
		self.highResCheck.SetToolTip(wx.ToolTip(u"High-Res MS data. \nNote: Mostly used for small molecules"))
		self.highResCheck.SetValue(self.config.peakFittingHighRes)

		thresholdNarrow_label = wx.StaticText(self.notebookSettings_paneML, wx.ID_ANY,
											 u"Threshold", wx.DefaultPosition, 
											 wx.DefaultSize, TEXT_STYLE_CV_R_L)
		self.peakThresholdNarrow_value = wx.SpinCtrlDouble(self.notebookSettings_paneML, 
												wx.ID_ANY, value=str(self.config.peakThresholdAssign),
												min=0, max=1, initial=self.config.peakThresholdAssign, 
												inc=0.01, size=(50,-1))
				
		windowNarrow_label = wx.StaticText(self.notebookSettings_paneML, wx.ID_ANY,
											 u"Window size", wx.DefaultPosition, 
											 wx.DefaultSize, TEXT_STYLE_CV_R_L)
		self.peakWindowNarrow_value = wx.SpinCtrlDouble(self.notebookSettings_paneML, 
												wx.ID_ANY, value=str(self.config.peakWindowAssign),
												min=1, max=500, initial=self.config.peakWindowAssign, 
												inc=1, size=(60,-1))

		peakWidthNarrow_label = wx.StaticText(self.notebookSettings_paneML, wx.ID_ANY,
										u"Peak width", wx.DefaultPosition, 
										wx.DefaultSize, TEXT_STYLE_CV_R_L)
		
		self.peakWidthNarrow_value = wx.SpinCtrlDouble(self.notebookSettings_paneML, 
												wx.ID_ANY, value=str(self.config.peakWidthAssign),
												min=0, max=100, initial=self.config.peakWidthAssign, 
												inc=0.5, size=(50,-1))
		
		self.showIsotopesAssign = makeCheckbox(self.notebookSettings_paneML, u"Isotopes")
		self.showIsotopesAssign.SetToolTip(wx.ToolTip(u"Show found isotopes in the MS window."))
		self.showIsotopesAssign.SetValue(self.config.showIsotopes)

		
		###
		
		self.smoothMSCheck = makeCheckbox(self.notebookSettings_paneML, u"Smooth")
		self.smoothMSCheck.SetToolTip(wx.ToolTip("Smooth MS peak before peak detection. \nNote: Using Gaussian filter"))
		smooth1D_label = wx.StaticText(self.notebookSettings_paneML, wx.ID_ANY,
										u"Sigma", wx.DefaultPosition, 
										wx.DefaultSize, TEXT_STYLE_CV_R_L)
		self.smoothMSCheck.SetValue(self.config.smoothFitting)
		
		self.smooth1D_value = wx.SpinCtrlDouble(self.notebookSettings_paneML, 
												wx.ID_ANY, value=str(self.config.sigmaMS),
												min=0, max=100,
												initial=self.config.sigmaMS, 
												inc=1, size=(50,-1))
		
		
		self.autoAddToTableCheck = makeCheckbox(self.notebookSettings_paneML, u"Add to table")
		self.autoAddToTableCheck.SetToolTip(wx.ToolTip("Automatically add peaks to the table"))
		self.autoAddToTableCheck.SetValue(self.config.autoAddToTable)
		
		
		gridFile = wx.GridBagSizer(1,1)
		y = 0
		gridFile.Add(detectMode_label, wx.GBPosition(y,0), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		gridFile.Add(self.detectMode, wx.GBPosition(y,1), wx.GBSpan(1,1),ALL_CENTER_VERT,2)
		gridFile.Add(self.findPeaksBtn, wx.GBPosition(y,3), wx.GBSpan(1,1),ALL_CENTER_VERT,2)
		y = 1
		gridFile.Add(threshold_label, wx.GBPosition(y,0), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		gridFile.Add(window_label, wx.GBPosition(y,1), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		gridFile.Add(peakWidth_label, wx.GBPosition(y,2), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		gridFile.Add(self.showRectanglesCheck, wx.GBPosition(y,3), wx.GBSpan(1,1),ALL_CENTER_VERT,2)
		y = 2
		gridFile.Add(self.peakThreshold_value, wx.GBPosition(y,0), wx.GBSpan(1,1),ALL_CENTER_VERT,2)
		gridFile.Add(self.peakWindow_value, wx.GBPosition(y,1), wx.GBSpan(1,1),ALL_CENTER_VERT,2)
		gridFile.Add(self.peakWidth_value, wx.GBPosition(y,2), wx.GBSpan(1,1),ALL_CENTER_VERT,2)
		gridFile.Add(self.smoothMSCheck, wx.GBPosition(y,3), wx.GBSpan(1,1),ALL_CENTER_VERT,2)
		y = 3
		gridFile.Add(self.highResCheck, wx.GBPosition(y,0), wx.GBSpan(1,2), ALL_CENTER_VERT,2)
		gridFile.Add(smooth1D_label, wx.GBPosition(y,2), wx.GBSpan(1,1),ALL_CENTER_VERT,2)
		gridFile.Add(self.smooth1D_value, wx.GBPosition(y,3), wx.GBSpan(1,1),ALL_CENTER_VERT,2)
		y = 4
		gridFile.Add(thresholdNarrow_label, wx.GBPosition(y,0), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		gridFile.Add(windowNarrow_label, wx.GBPosition(y,1), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		gridFile.Add(peakWidthNarrow_label, wx.GBPosition(y,2), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		y = 5
		gridFile.Add(self.peakThresholdNarrow_value, wx.GBPosition(y,0), wx.GBSpan(1,1),ALL_CENTER_VERT,2)
		gridFile.Add(self.peakWindowNarrow_value, wx.GBPosition(y,1), wx.GBSpan(1,1),ALL_CENTER_VERT,2)
		gridFile.Add(self.peakWidthNarrow_value, wx.GBPosition(y,2), wx.GBSpan(1,1),ALL_CENTER_VERT,2)
		gridFile.Add(self.showIsotopesAssign, wx.GBPosition(y,3), wx.GBSpan(1,1),ALL_CENTER_VERT,2)
		y = 6
		gridFile.Add(self.currentRangePeakFitCheck, wx.GBPosition(y,0), wx.GBSpan(1,2),ALL_CENTER_VERT,2)
		gridFile.Add(self.autoAddToTableCheck, wx.GBPosition(y,2), wx.GBSpan(1,2),ALL_CENTER_VERT,2)

		fileMainSizer.Add(gridFile, 0, wx.EXPAND|wx.ALL, 2)
		
		return fileMainSizer

	def parametersSettingsPane(self):
		
		# Gather sizers
		documentTreeSubPanel = self.documentTreeSubPanel()
		ionListSubPanel = self.ionListSubPanel()
		fontSizer = self.fontSubPanel()
		exportImageSizer = self.exportImageSubPanel()
		exportDataSubPanel = self.exportDataSubPanel()
		advancedSubPanel = self.advancedSubPanel()
		
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		mainGrid = wx.GridBagSizer(2,2)
		mainGrid.Add(documentTreeSubPanel, (0,0))
		mainGrid.Add(ionListSubPanel, (1,0))
		mainGrid.Add(fontSizer, (2,0))
		mainGrid.Add(exportImageSizer, (3,0))
		mainGrid.Add(exportDataSubPanel, (4,0))
		mainGrid.Add(advancedSubPanel, (5,0))

		mainSizer.Add(mainGrid, wx.EXPAND |wx.ALL, 2)
		self.notebookSettings_paneProperties.SetSizer(mainSizer)
		self.notebookSettings_paneProperties.Layout()	
		self.Layout()	
		
		self.mzWindowSize.Bind(wx.EVT_SPINCTRLDOUBLE, self.exportToConfig)
		self.useInternalMZwindowCheck.Bind(wx.EVT_CHECKBOX, self.exportToConfig)
		
		self.titleSlider.Bind(wx.EVT_SPINCTRLDOUBLE, self.exportToConfig)
		self.labelSlider.Bind(wx.EVT_SPINCTRLDOUBLE, self.exportToConfig)
		self.tickSlider.Bind(wx.EVT_SPINCTRLDOUBLE, self.exportToConfig)
		self.notationSlider.Bind(wx.EVT_SPINCTRLDOUBLE, self.exportToConfig)
		self.resolutionSlider.Bind(wx.EVT_SPINCTRLDOUBLE, self.exportToConfig)
		self.formatType.Bind(wx.EVT_COMBOBOX, self.exportToConfig)
		self.transparentCheck.Bind(wx.EVT_CHECKBOX, self.exportToConfig)
		self.labelBoldCheck.Bind(wx.EVT_CHECKBOX, self.exportToConfig)
		self.titleBoldCheck.Bind(wx.EVT_CHECKBOX, self.exportToConfig)
		self.annotRotation.Bind(wx.EVT_COMBOBOX, self.exportToConfig)
		self.StyleSelect.Bind(wx.EVT_COMBOBOX, self.exportToConfig)
		
		self.delimiter_value.Bind(wx.EVT_COMBOBOX, self.exportToConfig)
		# Call config
		self.exportToConfig()
		
# 		

	def documentTreeSubPanel(self):
		mainBox = makeStaticBox(self.notebookSettings_paneProperties, "General parameters", (285,-1), wx.BLUE)
		
		mainSizer = wx.StaticBoxSizer(mainBox, wx.HORIZONTAL)
		
		# Make canvas parameters		
		self.quickDisplayCheck = makeCheckbox(self.notebookSettings_paneProperties, u"Instant plot from Document Tree")
		self.quickDisplayCheck.SetToolTip(wx.ToolTip("Enable/Disable instant plotting of items from the Document Tree. If ticked, plots will appear automatically upon selection in the Document Tree"))
		self.quickDisplayCheck.SetValue(self.config.quickDisplay)
		
		self.threadingCheck = makeCheckbox(self.notebookSettings_paneProperties, u"Multi-threading")
		self.threadingCheck.SetToolTip(wx.ToolTip("Enable/Disable multi-threading on your PC. If enabled, certain slow functions will be executed on separate CPU thread, meaning the GUI won't get locked and you can continue working"))
		self.threadingCheck.SetValue(self.config.threading)
			
		self.loggingCheck = makeCheckbox(self.notebookSettings_paneProperties, u"Log events to file")
		self.loggingCheck.SetToolTip(wx.ToolTip("Enable/Disable event logging. If enabled, each time you open ORIGAMI a new log file will appear in the folder which should contain any actions, warnings or errors."))
		self.loggingCheck.SetValue(self.config.logging)
				
		# bind
		self.quickDisplayCheck.Bind(wx.EVT_CHECKBOX, self.onUpdateDocumentTree)
		self.quickDisplayCheck.Bind(wx.EVT_CHECKBOX, self.parent.panelDocuments.topP.documents.onNotUseQuickDisplay)
		self.threadingCheck.Bind(wx.EVT_CHECKBOX, self.exportToConfig)
		self.threadingCheck.Bind(wx.EVT_CHECKBOX, self.onEnableDisableThreading)
		self.loggingCheck.Bind(wx.EVT_CHECKBOX, self.exportToConfig)
		self.loggingCheck.Bind(wx.EVT_CHECKBOX, self.onEnableDisableLogging)
		
				
		# Add to grid sizer
		grid = wx.GridBagSizer(2,2)
		grid.Add(self.quickDisplayCheck, wx.GBPosition(0,0), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		grid.Add(self.threadingCheck, wx.GBPosition(1,0), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		grid.Add(self.loggingCheck, wx.GBPosition(2,0), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		
		mainSizer.Add(grid, 0, wx.EXPAND|wx.ALL, 2)
		return mainSizer

	def ionListSubPanel(self):
		mainBox = makeStaticBox(self.notebookSettings_paneProperties, "Import ion list", (285,-1), wx.BLUE)
		
		mainSizer = wx.StaticBoxSizer(mainBox, wx.HORIZONTAL)
		
		# Make canvas parameters
		mzWindowSize = makeStaticText(self.notebookSettings_paneProperties, u"± m/z \n(Da)")
		self.mzWindowSize = wx.SpinCtrlDouble(self.notebookSettings_paneProperties, wx.ID_ANY, 
											  value=str(self.config.mzWindowSize),min=1, max=100,
                                              initial=self.config.mzWindowSize, inc=1, size=(50,-1))
				
		self.useInternalMZwindowCheck = makeCheckbox(self.notebookSettings_paneProperties, u"Use")
		self.useInternalMZwindowCheck.SetValue(self.config.useInternalMZwindow)

		# Add to grid sizer
		grid = wx.GridBagSizer(2,2)
		grid.Add(mzWindowSize, wx.GBPosition(0,0), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		grid.Add(self.mzWindowSize, wx.GBPosition(0,1), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		grid.Add(self.useInternalMZwindowCheck, wx.GBPosition(0,2), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)

		mainSizer.Add(grid, 0, wx.EXPAND|wx.ALL, 2)
		
		return mainSizer

	def fontSubPanel(self):
		mainBox = makeStaticBox(self.notebookSettings_paneProperties, "Styling properties", (285,-1), wx.BLUE)
		
		mainSizer = wx.StaticBoxSizer(mainBox, wx.HORIZONTAL)
		
		# Make canvas parameters
		titleFontSize = makeStaticText(self.notebookSettings_paneProperties, u"Title font size")
		self.titleSlider = wx.SpinCtrlDouble(self.notebookSettings_paneProperties, wx.ID_ANY, 
											 value=str(self.config.titleFontSize),min=8, max=32,
                                             initial=self.config.titleFontSize, inc=1, size=(50,-1))
		
		self.titleBoldCheck = makeCheckbox(self.notebookSettings_paneProperties, u"Bold")
		self.titleBoldCheck.SetValue(self.config.titleFontWeight)
		
		
		labelFontSize = makeStaticText(self.notebookSettings_paneProperties, u"Label font size")
		self.labelSlider = wx.SpinCtrlDouble(self.notebookSettings_paneProperties, wx.ID_ANY, 
											 value=str(self.config.labelFontSize),min=8, max=24,
                                             initial=self.config.labelFontSize, inc=1, size=(50,-1))

		self.labelBoldCheck = makeCheckbox(self.notebookSettings_paneProperties, u"Bold")
		self.labelBoldCheck.SetValue(self.config.labelFontWeight)
		
		
		tickFontSize = makeStaticText(self.notebookSettings_paneProperties, u"Tick font size")
		self.tickSlider = wx.SpinCtrlDouble(self.notebookSettings_paneProperties, wx.ID_ANY, 
											 value=str(self.config.tickFontSize),min=8, max=24,
                                             initial=self.config.tickFontSize, inc=1, size=(50,-1))

		
		notationFontSize = makeStaticText(self.notebookSettings_paneProperties, u"Annotation font size")
		self.notationSlider = wx.SpinCtrlDouble(self.notebookSettings_paneProperties, wx.ID_ANY, 
											 value=str(self.config.notationFontSize),min=6, max=32,
                                             initial=self.config.notationFontSize, inc=1, size=(50,-1)) 
		

		self.annotRotation = wx.Choice(self.notebookSettings_paneProperties, wx.ID_ANY, 
								choices=[u"0°",u"45°",u"90°",u"270°", u"315°"]) # for now only MS works
		self.annotRotation.SetToolTip(wx.ToolTip("Rotate annotation labels"))
		self.annotRotation.SetSelection(2)
	
		itemStyle_label = wx.StaticText(self.notebookSettings_paneProperties, wx.ID_ANY,
											 u"Style", wx.DefaultPosition, 
											 wx.DefaultSize, TEXT_STYLE_CV_R_L)
				
		self.StyleSelect = wx.ComboBox( self.notebookSettings_paneProperties, wx.ID_ANY, 
											wx.EmptyString, wx.DefaultPosition, wx.Size( COMBO_SIZE,-1 ), 
											self.config.styles, COMBO_STYLE, wx.DefaultValidator )
		self.StyleSelect.SetSelection(0)
		
		self.applyStyleBtn = wx.Button( self.notebookSettings_paneProperties, wx.ID_ANY,
									   u"Apply", wx.DefaultPosition, wx.Size( 50,-1 ), 0 )

		# Add to grid sizer
		grid = wx.GridBagSizer(2,2)
		grid.Add(titleFontSize, wx.GBPosition(0,0), wx.GBSpan(1,2), TEXT_STYLE_CV_R_L, 2)
		grid.Add(self.titleSlider, wx.GBPosition(1,0), wx.GBSpan(1,1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT, 2)
		grid.Add(self.titleBoldCheck, wx.GBPosition(1,1), wx.GBSpan(1,1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT, 2)
		
		grid.Add(labelFontSize, wx.GBPosition(0,2), wx.GBSpan(1,2), TEXT_STYLE_CV_R_L, 2)
		grid.Add(self.labelSlider, wx.GBPosition(1,2), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		grid.Add(self.labelBoldCheck, wx.GBPosition(1,3), wx.GBSpan(1,1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT, 2)
 		
		grid.Add(tickFontSize, wx.GBPosition(2,0), wx.GBSpan(1,2), TEXT_STYLE_CV_R_L, 2)
		grid.Add(self.tickSlider, wx.GBPosition(3,0), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
 		
		grid.Add(notationFontSize, wx.GBPosition(2,2), wx.GBSpan(1,2), TEXT_STYLE_CV_R_L, 2)
		grid.Add(self.notationSlider, wx.GBPosition(3,2), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		grid.Add(self.annotRotation, wx.GBPosition(3,3), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
 		
		grid.Add(itemStyle_label, wx.GBPosition(4,0), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		grid.Add(self.StyleSelect, wx.GBPosition(4,1), wx.GBSpan(1,2), TEXT_STYLE_CV_R_L, 2)
		grid.Add(self.applyStyleBtn, wx.GBPosition(4,3), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		
		
		mainSizer.Add(grid, 0, wx.EXPAND|wx.ALL, 2)
		
		return mainSizer

	def exportImageSubPanel(self):
		mainBox = makeStaticBox(self.notebookSettings_paneProperties, "Image properties", (285,-1), wx.BLUE)
		
		mainSizer = wx.StaticBoxSizer(mainBox, wx.HORIZONTAL)
		
		# Make canvas parameters
		imageResolution = makeStaticText(self.notebookSettings_paneProperties, "Resolution")
		self.resolutionSlider = wx.SpinCtrlDouble(self.notebookSettings_paneProperties, wx.ID_ANY, 
											 value=str(self.config.dpi),min=50, max=600,
                                             initial=self.config.dpi, inc=50, size=(50,-1)) 
		
		formatType = makeStaticText(self.notebookSettings_paneProperties, "Format")
		
		self.formatType = wx.ComboBox( self.notebookSettings_paneProperties, wx.ID_ANY, 
											wx.EmptyString, wx.DefaultPosition, wx.Size( COMBO_SIZE,-1 ), 
											self.config.imageFormatType, COMBO_STYLE, wx.DefaultValidator )
		self.formatType.SetStringSelection(self.config.imageFormat)
		self.formatType.SetToolTip(makeTooltip(text="Select output format. Default: png. \nNote: png is slow to save, tiff files are very large"))
		
		self.transparentCheck = makeCheckbox(self.notebookSettings_paneProperties, u"Transparent")
		self.transparentCheck.SetValue(self.config.transparent)

		self.resizeCheck = makeCheckbox(self.notebookSettings_paneProperties, u"Resize")
		self.resizeCheck.SetToolTip(makeTooltip(text="When checked, the image will be resized to specified size in inches (height x width)"))
		self.resizeCheck.SetValue(self.config.resize)
	
		
		self.resizeCheck.Bind(wx.EVT_CHECKBOX, self.exportToConfig)
		
		# Add to grid sizer
		grid = wx.GridBagSizer(2,2)
		grid.Add(imageResolution, wx.GBPosition(0,0), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		grid.Add(self.resolutionSlider, wx.GBPosition(0,1), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
			
		grid.Add(formatType, wx.GBPosition(1,0), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		grid.Add(self.formatType, wx.GBPosition(1,1), wx.GBSpan(1,2), TEXT_STYLE_CV_R_L, 2)

		grid.Add(self.transparentCheck, wx.GBPosition(2,0), wx.GBSpan(1,2), TEXT_STYLE_CV_R_L, 2)
		grid.Add(self.resizeCheck, wx.GBPosition(3,0), wx.GBSpan(1,2), TEXT_STYLE_CV_R_L, 2)
		
		mainSizer.Add(grid, 0, wx.EXPAND|wx.ALL, 2)
		
		return mainSizer
	
	def exportDataSubPanel(self):
		mainBox = makeStaticBox(self.notebookSettings_paneProperties, "Export properties", (285,-1), wx.BLUE)
		
		mainSizer = wx.StaticBoxSizer(mainBox, wx.HORIZONTAL)
		
		# Make canvas parameters
		delimiter_label = makeStaticText(self.notebookSettings_paneProperties, "Delimiter")
		self.delimiter_value = wx.ComboBox( self.notebookSettings_paneProperties, wx.ID_ANY, 
											wx.EmptyString, wx.DefaultPosition, wx.Size( COMBO_SIZE,-1 ), 
											self.config.textOutputDict.keys(), COMBO_STYLE, wx.DefaultValidator )
		self.delimiter_value.SetStringSelection(self.config.saveDelimiterTXT) # Pre-sets the value to the first method
		self.delimiter_value.SetToolTip(makeTooltip(text="Select output format. Default: csv."))
		
		self.normalizeMultipleMS = makeCheckbox(self.notebookSettings_paneProperties, u"Normalize multiple MS output")
		self.normalizeMultipleMS.SetValue(self.config.normalizeMultipleMS)
		
		
				
		self.normalizeMultipleMS.Bind(wx.EVT_CHECKBOX, self.exportToConfig)

		# Add to grid sizer
		grid = wx.GridBagSizer(2,2)
		grid.Add(delimiter_label, wx.GBPosition(0,0), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		grid.Add(self.delimiter_value, wx.GBPosition(0,1), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		grid.Add(self.normalizeMultipleMS, wx.GBPosition(1,0), wx.GBSpan(1,2), TEXT_STYLE_CV_R_L, 2)
		
		mainSizer.Add(grid, 0, wx.EXPAND|wx.ALL, 2)
		
		return mainSizer

	def advancedSubPanel(self):
		mainBox = makeStaticBox(self.notebookSettings_paneProperties, "Advanced properties", (285,-1), wx.BLUE)
		
		mainSizer = wx.StaticBoxSizer(mainBox, wx.HORIZONTAL)
		
		
		# Make canvas parameters
		self.showAdvancesCheck = makeCheckbox(self.notebookSettings_paneProperties, u"Enable advanced settings")
		self.showAdvancesCheck.SetValue(False)
		
		
		self.plotSelect_label = makeStaticText(self.notebookSettings_paneProperties, "Plot")
		self.plotSelect = wx.ComboBox( self.notebookSettings_paneProperties, wx.ID_ANY, 
											wx.EmptyString, wx.DefaultPosition, wx.Size( 90,-1 ), 
											self.config.availablePlotsList, COMBO_STYLE, wx.DefaultValidator )
		self.plotSelect.SetSelection(0)
# 				
		plotAxes_label = makeStaticText(self.notebookSettings_paneProperties, u"Plot sizes - proportion of the window")
		
		plotLeft_label = makeStaticText(self.notebookSettings_paneProperties, u"Left")
		self.plotLeft_value = wx.SpinCtrlDouble(self.notebookSettings_paneProperties, wx.ID_ANY, 
											   value=str(0),min=0, max=1,
                                               initial=0, inc=0.05, size=(50,-1))
		self.plotLeft_value.SetToolTip(makeTooltip(text="The distance between the edge and the plot. Small values might 'hide' labels"))
		
		
		plotBottom_label = makeStaticText(self.notebookSettings_paneProperties, u"Bottom")
		self.plotBottom_value = wx.SpinCtrlDouble(self.notebookSettings_paneProperties, wx.ID_ANY, 
											   value=str(0),min=0, max=1,
                                               initial=0, inc=0.05, size=(50,-1))
		self.plotBottom_value.SetToolTip(makeTooltip(text="The distance between the edge and the plot. Small values might 'hide' labels"))
			
		
		plotWidth_label = makeStaticText(self.notebookSettings_paneProperties, u"Width") 
		self.plotWidth_value = wx.SpinCtrlDouble(self.notebookSettings_paneProperties, wx.ID_ANY, 
											   value=str(0),min=0, max=1,
                                               initial=0, inc=0.05, size=(50,-1)) 
		self.plotWidth_value.SetToolTip(makeTooltip(text="The width of the plot. This value compliments the 'left' edge, when combined, it should not be larger than 1."))
											
		
		plotHeight_label = makeStaticText(self.notebookSettings_paneProperties, u"Height")
		self.plotHeight_value = wx.SpinCtrlDouble(self.notebookSettings_paneProperties, wx.ID_ANY, 
											   value=str(0),min=0, max=1,
                                               initial=0, inc=0.05, size=(50,-1))
		self.plotHeight_value.SetToolTip(makeTooltip(text="The height of the plot. This value compliments the 'bottom' edge, when combined, it should not be larger than 1."))
		
		self.resizingCheck = makeCheckbox(self.notebookSettings_paneProperties, u"Resizing")
		self.resizingCheck.SetToolTip(makeTooltip(text="When checked, the values below will be shown for plot sizes when saving an image. These can differ from the GUI sizes."))
		self.resizingCheck.SetValue(False)
		
		# Image size in inches
		plotSizes_label = makeStaticText(self.notebookSettings_paneProperties, u"Plot sizes - inches")
		imageHeight_label = makeStaticText(self.notebookSettings_paneProperties, "Height (in)")
		self.imageHeight_value = wx.SpinCtrlDouble(self.notebookSettings_paneProperties, wx.ID_ANY, 
											 value=str(0),min=1, max=20,
                                             initial=0, inc=0.5, size=(50,-1)) 
 
 
		imageWidth_label = makeStaticText(self.notebookSettings_paneProperties, "Width (in)")
		self.imageWidth_value = wx.SpinCtrlDouble(self.notebookSettings_paneProperties, wx.ID_ANY, 
											 value=str(0),min=1, max=20,
                                             initial=0, inc=0.5, size=(50,-1)) 
										 
		# Add to grid sizer
		grid = wx.GridBagSizer(2,2)
		grid.Add(self.showAdvancesCheck, wx.GBPosition(0,0), wx.GBSpan(1,4), TEXT_STYLE_CV_R_L, 2)
			
		grid.Add(self.plotSelect_label, wx.GBPosition(1,0), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		grid.Add(self.plotSelect, wx.GBPosition(1,1), wx.GBSpan(1,2), TEXT_STYLE_CV_R_L, 2)
		grid.Add(self.resizingCheck, wx.GBPosition(1,3), wx.GBSpan(1,2), TEXT_STYLE_CV_R_L, 2)	
		
		grid.Add(plotAxes_label, wx.GBPosition(2,0), wx.GBSpan(1,4), TEXT_STYLE_CV_R_L, 2)
		grid.Add(plotLeft_label, wx.GBPosition(3,0), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		grid.Add(plotBottom_label, wx.GBPosition(3,1), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		grid.Add(plotWidth_label, wx.GBPosition(3,2), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		grid.Add(plotHeight_label, wx.GBPosition(3,3), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		
		grid.Add(self.plotLeft_value, wx.GBPosition(4,0), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		grid.Add(self.plotBottom_value, wx.GBPosition(4,1), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		grid.Add(self.plotWidth_value, wx.GBPosition(4,2), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		grid.Add(self.plotHeight_value, wx.GBPosition(4,3), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		
		grid.Add(plotSizes_label, wx.GBPosition(5,0), wx.GBSpan(1,4), TEXT_STYLE_CV_R_L, 2)
		grid.Add(imageHeight_label, wx.GBPosition(6,0), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		grid.Add(imageWidth_label, wx.GBPosition(6,2), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)

		grid.Add(self.imageHeight_value, wx.GBPosition(6,1), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
		grid.Add(self.imageWidth_value, wx.GBPosition(6,3), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)


		self.showAdvancesCheck.Bind(wx.EVT_CHECKBOX, self.onShowAdvancedSettings)
		self.plotSelect.Bind(wx.EVT_COMBOBOX, self.onPopulateAdvancedSettings)
		self.resizingCheck.Bind(wx.EVT_CHECKBOX, self.onPopulateAdvancedSettings)
		
		self.plotLeft_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onUpdateAxesSizes)
		self.plotBottom_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onUpdateAxesSizes)
		self.plotWidth_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onUpdateAxesSizes)
		self.plotHeight_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onUpdateAxesSizes)
		self.imageHeight_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onUpdateAxesSizes)
		self.imageWidth_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onUpdateAxesSizes)
		

		self.onShowAdvancedSettings(evt=None)
		self.onPopulateAdvancedSettings(evt=None)
		
		mainSizer.Add(grid, 0, wx.EXPAND|wx.ALL, 2)
		
		return mainSizer

	def onShowAdvancedSettings(self, evt):
		"""
		Show/hide advanced settings
		"""
		updateList = [self.plotLeft_value, self.plotBottom_value, 
					self.plotWidth_value,self.plotHeight_value,
					self.plotSelect, self.imageHeight_value,
					self.imageWidth_value, self.resizingCheck]
		if self.showAdvancesCheck.GetValue():
			for item in updateList:
				item.Enable()
		else:
			for item in updateList:
				item.Disable()
			
		if evt != None:
			evt.Skip()

	def onPopulateAdvancedSettings(self, evt):
		
		# Get plot name
		plot = self.plotSelect.GetStringSelection()
		# Check if it should show resizing sizes
		resizingSizes = self.resizingCheck.GetValue()
		
		# Unpack values for plot
		if not resizingSizes:
			updateValues = self.config.plotSizes[plot]
		else:
			updateValues = self.config.savePlotSizes[plot]
			
		# Sizes
		updateSizes = self.config.plotResize[plot]
		updateValues = updateValues+updateSizes
		
		# Update list
		updateList = [self.plotLeft_value, 
					  self.plotBottom_value, 
					  self.plotWidth_value, 
					  self.plotHeight_value,
					  self.imageWidth_value,
					  self.imageHeight_value]
		
		for i, item in enumerate(updateList):
			item.SetValue(updateValues[i])
		
		if evt != None:
			evt.Skip()

	def onUpdateXYaxisLimits(self, evt):
		"""
		This function enables/disables and populates the values
		in the xy restriction boxes
		"""
		
		self.config.restrictXYrange = self.useRestrictedAxis.GetValue()
		restrictList = [self.iXstartRange, self.iXendRange, 
						self.iYstartRange, self.iYendRange]
		if self.config.restrictXYrange:
			self.applyXYLimBtn.Enable()
			for item in restrictList:
				item.Enable()
		else:
			self.applyXYLimBtn.Disable()
			for item in restrictList:
				item.Disable()
				
		xyLimits = self.config.xyLimits
		if len(xyLimits) == 4:
			for i, item in enumerate(restrictList):
				if xyLimits[i] == None: continue
				item.SetValue(num2str(xyLimits[i]))
				
		self.config.xyLimits = xyLimits
		if evt != None:
			evt.Skip()
			
	def onUpdateXYaxisLimitsRMSD(self, evt):
		"""
		This function limits the range of CVs calculated during RMSD/RMSF 
		calculation
		"""
		restrictList = [self.iXstartRangeRMSD, self.iXendRangeRMSD, 
						self.iYstartRangeRMSD, self.iYendRangeRMSD]
			
		self.config.restrictXYrangeRMSD = self.useRestrictedAxisRMSD.GetValue()
		if self.config.restrictXYrangeRMSD:
			for item in restrictList:
				item.Enable()
		else:
			for item in restrictList:
				item.Disable()
			
		xyLimits = self.config.xyLimitsRMSD
		if len(xyLimits) == 4:
			for i, item in enumerate(restrictList):
				if xyLimits[i] == None: continue
				item.SetValue(num2str(xyLimits[i]))

		if evt != None:
			evt.Skip()
			
	def onUpdateAxesSizes(self, evt):
				
		# Get plot name
		plot = self.plotSelect.GetStringSelection()
		# Check if it should show resizing sizes
		resizingSizes = self.resizingCheck.GetValue()
		
		updateList = [self.plotLeft_value, self.plotBottom_value, 
					self.plotWidth_value,self.plotHeight_value]
		updateValues = []
		
		# Check plot sizes
		for i, item in enumerate(updateList):
			value = item.GetValue()
			updateValues.append(value)
			
		if not resizingSizes:
			self.config.plotSizes[plot] = updateValues
		else:
			self.config.savePlotSizes[plot] = updateValues
			
		# Also check sizes in inches
		self.config.plotResize[plot] = [self.imageWidth_value.GetValue(), self.imageHeight_value.GetValue()]
		
		if evt != None:
			evt.Skip()
	
	def OnColorbarToggle(self, event):
		# TODO Change background colour to green/red
		val = self.colorbarTgl.GetValue()
		if val == True:
			self.colorbarTgl.SetLabel('On')
			self.config.colorbar = True
			self.colorbarTgl.SetForegroundColour(wx.WHITE)
			self.colorbarTgl.SetBackgroundColour(wx.BLUE)
		else:
			self.colorbarTgl.SetLabel('Off')
			self.config.colorbar = False
			self.colorbarTgl.SetForegroundColour(wx.WHITE)
			self.colorbarTgl.SetBackgroundColour(wx.RED)
	
	def OnNormalizeToggle(self, event):

		val = self.normalizeTgl.GetValue()
		if val == True:
			self.normalizeTgl.SetLabel('On')
			self.config.normalize = True
			self.normalizeTgl.SetForegroundColour(wx.WHITE)
			self.normalizeTgl.SetBackgroundColour(wx.BLUE)
			self.normalizationSelect.Enable()
		else:
			self.normalizeTgl.SetLabel('Off')
			self.config.normalize = False
			self.normalizeTgl.SetForegroundColour(wx.WHITE)
			self.normalizeTgl.SetBackgroundColour(wx.RED)
			self.normalizationSelect.Disable()
	
	def OnRMSDLabelToggle(self, event, loading=False):
		
		if loading:
			if self.config.rmsdLoc == 'leftTop':
				self.rmsdLabel_leftTop.SetValue(True)
			elif self.config.rmsdLoc == 'rightTop':
				self.rmsdLabel_rightTop.SetValue(True)
			elif self.config.rmsdLoc == 'leftBottom':
				self.rmsdLabel_leftBottom.SetValue(True)
			elif self.config.rmsdLoc == 'rightBottom':
				self.rmsdLabel_rightBottom.SetValue(True)
			elif self.config.rmsdLoc == 'None':
				self.rmsdLabel_None.SetValue(True)
				
				
		rmsdLabel_leftTop = self.rmsdLabel_leftTop.GetValue()
		rmsdLabel_rightTop = self.rmsdLabel_rightTop.GetValue()
		rmsdLabel_leftBottom = self.rmsdLabel_leftBottom.GetValue()
		rmsdLabel_rightBottom = self.rmsdLabel_rightBottom.GetValue()
		rmsdLabel_None = self.rmsdLabel_None.GetValue()
			
		color = wx.BLUE
		
		if rmsdLabel_leftTop:
			self.config.rmsdLoc = "leftTop"
			self.config.rmsdLocPos = (5, 95) 
			self.rmsdLabel_leftTop.SetBackgroundColour(color)
			otherList = [self.rmsdLabel_rightTop,self.rmsdLabel_leftBottom,
						self.rmsdLabel_rightBottom,self.rmsdLabel_None]
			for other in otherList:
				other.SetValue(False)
				other.SetBackgroundColour(wx.WHITE)
		if rmsdLabel_rightTop:
			self.config.rmsdLoc = "rightTop"
			self.config.rmsdLocPos = (75, 95) 
			self.rmsdLabel_rightTop.SetBackgroundColour(color)
			otherList = [self.rmsdLabel_leftTop,self.rmsdLabel_leftBottom,
						self.rmsdLabel_rightBottom,self.rmsdLabel_None]
			for other in otherList:
				other.SetValue(False)
				other.SetBackgroundColour(wx.WHITE)
		if rmsdLabel_leftBottom:
			self.config.rmsdLoc = "leftBottom"
			self.config.rmsdLocPos = (5, 5) 
			self.rmsdLabel_leftBottom.SetBackgroundColour(color)
			otherList = [self.rmsdLabel_rightTop,self.rmsdLabel_leftTop,
						self.rmsdLabel_rightBottom,self.rmsdLabel_None]
			for other in otherList:
				other.SetValue(False)
				other.SetBackgroundColour(wx.WHITE)
		if rmsdLabel_rightBottom:
			self.config.rmsdLoc = "rightBottom"
			self.config.rmsdLocPos = (75, 5) 
			self.rmsdLabel_rightBottom.SetBackgroundColour(color)
			otherList = [self.rmsdLabel_rightTop,self.rmsdLabel_leftBottom,
						self.rmsdLabel_leftTop,self.rmsdLabel_None]
			for other in otherList:
				other.SetValue(False)
				other.SetBackgroundColour(wx.WHITE)
		if rmsdLabel_None:
			self.config.rmsdLoc = "None"
			self.rmsdLabel_None.SetBackgroundColour(color)
			otherList = [self.rmsdLabel_rightTop,self.rmsdLabel_leftBottom,
						self.rmsdLabel_rightBottom,self.rmsdLabel_leftTop]
			for other in otherList:
				other.SetValue(False)
				other.SetBackgroundColour(wx.WHITE)
	
	def setCmap(self, event): 
		self.config.currentCmap = self.comboCmapSelect.GetValue()
		# Get current document
		document = self.parent.presenter.onUpdateColormap()
		if document == None: return
		else:
			document.colormap = self.comboCmapSelect.GetValue()
			#Update document
			self.parent.panelDocuments.topP.documents.addDocument(docData = document)  
		
	def setInterp(self, event):
		self.config.interpolation = self.comboInterpolateSelect.GetValue()
			
	def enableDisableTxtBoxes(self, event):
		# Checks what acquisition type was selected
		# Hides and shows various boxes depending on selection
		self.config.acqMode = self.comboAcqTypeSelect.GetValue()
		if self.config.acqMode == 'Linear':
			enableList  = [self.iSPV, self.iStartVoltage, self.iEndVoltage,
						   self.iStepVoltage]
			disableList = [self.iExpIncrement, self.iExpPercentage, self.iFitScale, self.loadListBtn]
		elif self.config.acqMode == 'Exponential':
			enableList  = [self.iSPV, self.iStartVoltage, self.iEndVoltage,
						   self.iStepVoltage, self.iExpIncrement, self.iExpPercentage,]
			disableList = [ self.iFitScale, self.loadListBtn]
		elif self.config.acqMode == 'Fitted':
			enableList  = [self.iSPV, self.iStartVoltage, self.iEndVoltage,
						   self.iStepVoltage, self.iFitScale]
			disableList = [self.iExpIncrement, self.iExpPercentage, self.loadListBtn]
		elif self.config.acqMode == 'User-defined':
			enableList  = [self.loadListBtn]
			disableList = [self.iExpIncrement, self.iExpPercentage, 
						   self.iSPV, self.iStartVoltage, self.iEndVoltage,
						   self.iStepVoltage, self.iFitScale]
		# Iterate over lists to enable/disable boxes
		for item in enableList:
			item.Enable()
		for item in disableList:
			item.Disable()

# 		if self.binMSEachCV_check.GetValue():
# 			self.mzStart_value.Enable()
# 			self.mzEnd_value.Enable()
# 			self.mzBin_value.Enable()
# 		else:
# 			self.mzStart_value.Disable()
# 			self.mzEnd_value.Disable()
# 			self.mzBin_value.Disable()
		
		# Depending on selection, hides and/or changes text
		self.config.smoothMode = self.comboSmoothSelect.GetValue()
		if self.config.smoothMode == 'Gaussian':
			self.iSGwindow.Disable()
			self.iSGpoly.Enable()
			self.sSGpoly_GaussSigma.SetLabel('Sigma\n')
		elif self.config.smoothMode == 'Savitzky-Golay':
			self.iSGwindow.Enable()
			self.iSGpoly.Enable()
			self.sSGpoly_GaussSigma.SetLabel('Sav-Gol \npolynomial')
		else: 
			self.iSGwindow.Disable()
			self.iSGpoly.Disable()
			self.sSGpoly_GaussSigma.SetLabel('Sav-Gol \npolynomial')
	
		# High-res
		self.config.peakFittingHighRes = self.highResCheck.GetValue()
		if self.config.peakFittingHighRes:
			self.peakThresholdNarrow_value.Enable()
			self.peakWidthNarrow_value.Enable()
			self.peakWindowNarrow_value.Enable()
			self.showIsotopesAssign.Enable()
		else:
			self.peakThresholdNarrow_value.Disable()
			self.peakWidthNarrow_value.Disable()
			self.peakWindowNarrow_value.Disable()
			self.showIsotopesAssign.Disable()
			
		# Pretty contour
		self.config.plotType = self.comboPlotType.GetStringSelection()
		if self.config.plotType == 'Image':
			self.usePrettyContour_check.Disable()
			self.comboInterpolateSelect.Enable()
		elif self.config.plotType == 'Contour':
			self.usePrettyContour_check.Enable()
			self.comboInterpolateSelect.Disable()
		else:
			self.usePrettyContour_check.Disable()
			self.comboInterpolateSelect.Enable()
		
 		self.config.smoothFitting = self.smoothMSCheck.GetValue()
 		if self.config.smoothFitting:
 			self.smooth1D_value.Enable()
 		else:
 			self.smooth1D_value.Disable()
 		
 		if event != None:
			event.Skip()
			
	def onPopulateOrigamiVars(self, parameters=None, evt=None):
		"""
		Populate parameter fields based on the parameters found in the 
		parameters dictionary
		"""
		# First get values
		method = parameters.get("method", "Linear")
		spv = parameters.get("spv", None)
		if spv == None or spv == "None": spv = ""
		
		startVoltage = parameters.get("startVoltage", None)
		if startVoltage == None or startVoltage == "None": startVoltage = ""
		
		endVoltage = parameters.get("endVoltage", None)
		if endVoltage == None or endVoltage == "None": endVoltage = ""
		
		stepVoltage = parameters.get("stepVoltage", None)
		if stepVoltage == None or stepVoltage == "None": stepVoltage = ""
		
		expIncrement = parameters.get("expIncrement", None)
		if expIncrement == None or expIncrement == "None": expIncrement = ""
		
		expPercentage = parameters.get("expPercentage", None)
		if expPercentage == None or expPercentage == "None": expPercentage = ""
		
		dx = parameters.get("dx", None)
		if dx == None or dx == "None": dx = ""
		
		
		# Set values
		self.comboAcqTypeSelect.SetStringSelection(method)
		self.iSPV.SetValue(str(spv))
		self.iStartVoltage.SetValue(str(startVoltage))
		self.iEndVoltage.SetValue(str(endVoltage))
		self.iStepVoltage.SetValue(str(stepVoltage))
		self.iExpIncrement.SetValue(str(expIncrement))
		self.iExpPercentage.SetValue(str(expPercentage))
		self.iFitScale.SetValue(str(dx))
		self.exportToConfig()
		self.enableDisableTxtBoxes(event=None)
		
	def onUpdateParams(self, evt=None):
		"""
		This function resets parameters from self.config to the GUI
		"""
		self.iMZstart.SetValue(num2str(self.config.mzStart))
		self.iMZend.SetValue(num2str(self.config.mzEnd))

	def importFromConfig(self, evt):

		self.importEvent = True # dirty way to stop evt refreshing
		self.iStartVoltage.SetValue(str(self.config.startVoltage))
		self.iEndVoltage.SetValue(str(self.config.endVoltage))
		self.iStepVoltage.SetValue(str(self.config.stepVoltage))
		self.iStartScan.SetValue(str(self.config.startScan))
		self.iSPV.SetValue(str(self.config.scansPerVoltage))
		self.iExpPercentage.SetValue(str(self.config.expPercentage))
		self.iExpIncrement.SetValue(str(self.config.expIncrement))
		self.iFitScale.SetValue(str(self.config.fittedScale))
		self.comboAcqTypeSelect.SetValue(self.config.acqMode)
		
		self.comboCmapSelect.SetStringSelection(self.config.currentCmap)
		
		self.iSGpoly.SetValue(str(self.config.savGolPolyOrder))
		self.iSGwindow.SetValue(str(self.config.savGolWindowSize))
		self.iThreshold.SetValue(str(self.config.threshold))
		self.iBinSize.SetValue(str(self.config.binSizeMZDT))
		self.mzStart_value.SetValue(str(self.config.binMSstart))
		self.mzEnd_value.SetValue(str(self.config.binMSend))
		self.mzBin_value.SetValue(str(self.config.binMSbinsize))
		
		

		self.notationSlider.SetValue(int(self.config.notationFontSize))
		self.tickSlider.SetValue(int(self.config.tickFontSize))
		self.labelSlider.SetValue(int(self.config.labelFontSize))
		self.labelBoldCheck.SetValue(self.config.labelFontWeight)
		self.titleSlider.SetValue(int(self.config.titleFontSize))
		self.titleBoldCheck.SetValue(self.config.titleFontWeight)
		
		self.lineWidth_value.SetValue(int(self.config.lineWidth*10))		
		self.iMarkerSize.SetValue(str(self.config.markerSize))
		for markerShape,item in self.config.markerShapeDict.iteritems():
			if item == self.config.markerShape:
				self.comboMarkerChoice.SetValue(markerShape)
		self.annotTransparency_value.SetValue(self.config.annotTransparency)
		
		rgb = (self.config.lineColour[0]*255, self.config.lineColour[1]*255,self.config.lineColour[2]*255)
		self.colorBtn.SetBackgroundColour(rgb)
		rgb = (self.config.annotColor[0]*255, self.config.annotColor[1]*255,self.config.annotColor[2]*255)
		self.colorAnnotBtn.SetBackgroundColour(rgb)
		
		self.resolutionSlider.SetValue(self.config.dpi)
		self.transparentCheck.SetValue(self.config.transparent)
		self.formatType.SetValue(self.config.imageFormat)
		self.comboPlotType.SetStringSelection(self.config.plotType)
		
		self.peakWindow_value.SetValue(self.config.peakWindow)
		self.peakThreshold_value.SetValue(self.config.peakThreshold)
		self.peakWidth_value.SetValue(self.config.peakWidth)
		self.showRectanglesCheck.SetValue(self.config.showRectanges)
		self.autoAddToTableCheck.SetValue(self.config.autoAddToTable)
		self.currentRangePeakFitCheck.SetValue(self.config.currentRangePeak)
		self.mzWindowSize.SetValue(self.config.mzWindowSize)
		self.useInternalMZwindowCheck.SetValue(self.config.useInternalMZwindow)
		
		self.peakThresholdNarrow_value.SetValue(self.config.peakThresholdAssign)
		self.peakWidthNarrow_value.SetValue(self.config.peakWidthAssign)
		self.peakWindowNarrow_value.SetValue(self.config.peakWindowAssign)
		self.highResCheck.SetValue(self.config.peakFittingHighRes)
		self.showIsotopesAssign.SetValue(self.config.showIsotopes)
		
		self.binDataCheck.SetValue(self.config.binOnLoad)
		self.binMSfromRT.SetValue(self.config.binMSfromRT)
		self.loggingCheck.SetValue(self.config.logging)
		self.threadingCheck.SetValue(self.config.threading)
		self.normalizeTgl.SetValue(self.config.normalize)
		self.colorbarTgl.SetValue(self.config.colorbar)
		self.colorbarWidth_value.SetValue(self.config.colorbarWidth)
		self.colorbarPad_value.SetValue(self.config.colorbarPad)
		self.resizeCheck.SetValue(self.config.resize)
		self.useWaterfall_check.SetValue(self.config.addWaterfall)
		self.normalizationSelect.SetStringSelection(self.config.normMode)
		self.rmsd_fontSize.SetValue(self.config.rmsdFontSize)
		self.rmsd_fontWeight.SetValue(self.config.rmsdFontWeight)
		self.rmsdRotX.SetValue(self.config.rmsdRotX)
		self.rmsdRotY.SetValue(self.config.rmsdRotY)
		self.normalizeMultipleMS.SetValue(self.config.normalizeMultipleMS)
		
				
		# Trigger toggles
		self.OnNormalizeToggle(event=None)
		self.OnColorbarToggle(event=None)
		self.OnRMSDLabelToggle(event=None, loading=True)
		self.enableDisableTxtBoxes(event=None)
		self.onEnableDisableLogging(evt=None)
# 		self.onUpdateDocumentTree()
		self.parent.panelDocuments.topP.documents.onNotUseQuickDisplay(evt=None)
		self.onEnableDisableThreading(evt=None)
		
		self.importEvent = False
		self.notebookSettings_paneML.Layout()
		self.notebookSettings_paneProperties.Layout()
		
	def exportToConfig(self, event=None):
		# This function calls all boxes and etc and populates the config object
		
		if self.importEvent: return
		# === ORIGAMI PARAMETERS === #
		self.config.startVoltage = str2num(self.iStartVoltage.GetValue())
		self.config.endVoltage = str2num(self.iEndVoltage.GetValue())
		self.config.stepVoltage = str2num(self.iStepVoltage.GetValue())
		self.config.startScan = str2int(self.iStartScan.GetValue())
		self.config.scansPerVoltage = str2int(self.iSPV.GetValue())
		self.config.expPercentage = str2num(self.iExpPercentage.GetValue())
		self.config.expIncrement = str2num(self.iExpIncrement.GetValue())
		self.config.fittedScale = str2num(self.iFitScale.GetValue())
		self.config.acqMode = self.comboAcqTypeSelect.GetValue()
		
		self.config.binMSstart = str2num(self.mzStart_value.GetValue())
		self.config.binMSend = str2num(self.mzEnd_value.GetValue())
		self.config.binMSbinsize = str2num(self.mzBin_value.GetValue())
		self.config.binSizeMZDT = str2num(self.iBinSize.GetValue())
		
# 		self.config.binCVdata = self.binMSEachCV_check.GetValue()
		
		# === ANALYSIS PARAMETERS === #
		self.config.mzStart = self.iMZstart.GetValue()
		self.config.mzEnd = self.iMZend.GetValue()
		self.config.rtStart = self.iRTstart.GetValue()
		self.config.rtEnd = self.iRTend.GetValue()
		
		self.config.savGolPolyOrder = self.iSGpoly.GetValue()
		self.config.savGolWindowSize = self.iSGwindow.GetValue()
		self.config.gaussSigma = self.iSGpoly.GetValue()
		self.config.threshold = self.iThreshold.GetValue()
		self.config.binSize = str2num(self.mzBin_value.GetValue())
		self.config.binOnLoad = self.binDataCheck.GetValue()
		self.config.binMSfromRT = self.binMSfromRT.GetValue() 
		self.config.normMode = self.normalizationSelect.GetStringSelection()
				
		# === STYLING PARAMETERS === #
		self.config.notationFontSize = str2num(self.notationSlider.GetValue())
		self.config.tickFontSize = str2num(self.tickSlider.GetValue())
		self.config.labelFontSize = str2num(self.labelSlider.GetValue())
		self.config.labelFontWeight = self.labelBoldCheck.GetValue()
		self.config.titleFontSize = str2num(self.titleSlider.GetValue())
		self.config.titleFontWeight = self.titleBoldCheck.GetValue()
		self.config.lineWidth = str2num(self.lineWidth_value.GetValue())/10 # increment by .1
		self.config.markerSize = str2num(self.iMarkerSize.GetValue())
		self.config.markerShapeTXT = self.comboMarkerChoice.GetStringSelection()
		self.config.markerShape = self.config.markerShapeDict[self.comboMarkerChoice.GetStringSelection()]
		self.config.annotTransparency = str2num(self.annotTransparency_value.GetValue())
		self.config.waterfallOffset = str2num(self.itemWaterfallOffset.GetValue())
		self.config.plotType = self.comboPlotType.GetStringSelection()
		self.config.currentStyle = self.StyleSelect.GetStringSelection()
		self.config.prettyContour = self.usePrettyContour_check.GetValue()
		self.config.useCurrentCmap = self.useColormap_check.GetValue()
		self.config.addWaterfall = self.useWaterfall_check.GetValue()
		self.config.colorbarWidth = str2num(self.colorbarWidth_value.GetValue())
		self.config.colorbarPad = str2num(self.colorbarPad_value.GetValue())
		self.config.saveDelimiterTXT = self.delimiter_value.GetStringSelection()
		self.config.saveDelimiter = self.config.textOutputDict[self.delimiter_value.GetStringSelection()]
		self.config.saveExtension = self.config.textExtensionDict[self.delimiter_value.GetStringSelection()]
		self.config.rmsdFontSize = str2num(self.rmsd_fontSize.GetValue())
		self.config.rmsdFontWeight = self.rmsd_fontWeight.GetValue()
		self.config.rmsdRotX = str2num(self.rmsdRotX.GetValue())
		self.config.rmsdRotY = str2num(self.rmsdRotY.GetValue())
		
		self.config.minCmap = str2num(self.minCmap_value.GetValue())
		self.config.midCmap = str2num(self.midCmap_value.GetValue())
		self.config.maxCmap = str2num(self.maxCmap_value.GetValue())
		
		# === EXPORT PARAMETERS === #
		self.config.dpi = str2num(self.resolutionSlider.GetValue())
		self.config.transparent = self.transparentCheck.GetValue()
		self.config.imageFormat = self.formatType.GetValue()
		self.config.resize = self.resizeCheck.GetValue()
		self.config.normalizeMultipleMS = self.normalizeMultipleMS.GetValue()
		
		xmin = str2num(self.iXstartRange.GetValue())
		xmax = str2num(self.iXendRange.GetValue())
		ymin = str2num(self.iYstartRange.GetValue())
		ymax = str2num(self.iYendRange.GetValue())
		
		self.config.xyLimits = [xmin, xmax, ymin, ymax]

		xmin = str2num(self.iXstartRangeRMSD.GetValue())
		xmax = str2num(self.iXendRangeRMSD.GetValue())
		ymin = str2num(self.iYstartRangeRMSD.GetValue())
		ymax = str2num(self.iYendRangeRMSD.GetValue())
		
		self.config.xyLimitsRMSD = [xmin, xmax, ymin, ymax]
		
		# === FITTING PARAMETERS === #
		detectVal = self.detectMode.GetSelection()	
		self.config.currentPeakFit = self.detectMode.GetString(detectVal)
		self.config.peakWindow = str2num(self.peakWindow_value.GetValue())
		self.config.peakThreshold = str2num(self.peakThreshold_value.GetValue())
		self.config.peakWidth = str2num(self.peakWidth_value.GetValue())
		self.config.showRectanges = self.showRectanglesCheck.GetValue()
		self.config.autoAddToTable = self.autoAddToTableCheck.GetValue()
		self.config.currentRangePeak = self.currentRangePeakFitCheck.GetValue()
		self.config.mzWindowSize = str2num(self.mzWindowSize.GetValue())
		self.config.useInternalMZwindow = self.useInternalMZwindowCheck.GetValue()
		self.config.smoothFitting = self.smoothMSCheck.GetValue()
		self.config.sigmaMS = str2num(self.smooth1D_value.GetValue())
		self.config.peakFittingHighRes = self.highResCheck.GetValue()
		self.config.peakThresholdAssign = str2num(self.peakThresholdNarrow_value.GetValue())
		self.config.peakWidthAssign = str2num(self.peakWidthNarrow_value.GetValue())
		self.config.peakWindowAssign = str2int(self.peakWindowNarrow_value.GetValue())
		self.config.showIsotopes = self.showIsotopesAssign.GetValue()
		
		# === GENERAL PARAMETERS === #
		self.config.quickDisplay = self.quickDisplayCheck.GetValue()		
		self.config.threading = self.threadingCheck.GetValue()
		self.config.logging = self.loggingCheck.GetValue()
		
		# Threshold value
		if self.config.threshold == '' or self.config.threshold == None: pass
		
		# Export smoothing parameters
		self.config.smoothMode = self.comboSmoothSelect.GetValue()
		if self.config.smoothMode == 'Gaussian':
			self.config.gaussSigma == str2int(self.iSGpoly.GetValue())
		elif self.config.smoothMode == 'Savitzky-Golay':
			self.config.savGolPolyOrder == str2int(self.iSGpoly.GetValue())
			self.config.savGolWindowSize == str2int(self.iSGwindow.GetValue())
		else: pass
		
		if event != None:
			event.Skip()
						
	def onUpdateDocumentTree(self, evt):
		self.exportToConfig()
		evt.Skip()
	
	def onChangeMarkerColor(self, evt):
		# Show dialog and get new colour
		dlg = wx.ColourDialog(self.parent)
		dlg.GetColourData().SetChooseFull(True)
		if dlg.ShowModal() == wx.ID_OK:
			data = dlg.GetColourData()
			newColour = list(data.GetColour().Get())
			self.config.annotColor = list([float(newColour[0])/255,
										   float(newColour[1])/255,
										   float(newColour[2])/255])
			dlg.Destroy()
		else:
			return
		self.colorAnnotBtn.SetBackgroundColour(newColour)
		
	def onChangeRMSDColor(self, evt):
		# Show dialog and get new colour
		dlg = wx.ColourDialog(self.parent)
		dlg.GetColourData().SetChooseFull(True)
		if dlg.ShowModal() == wx.ID_OK:
			data = dlg.GetColourData()
			newColour = list(data.GetColour().Get())
			self.config.rmsdColor = list([float(newColour[0])/255,
										   float(newColour[1])/255,
										   float(newColour[2])/255])
			dlg.Destroy()
		else:
			return
		self.rmsdColorBtn.SetBackgroundColour(newColour)

	def onEnableDisableLogging(self, evt):
		
		self.config.logging = self.loggingCheck.GetValue()
		if self.config.logging:
			sys.stdin = self.parent.panelPlots.log
			sys.stdout = self.parent.panelPlots.log
			sys.stderr = self.parent.panelPlots.log
			print('Logging events to file')
		else:
			print('Logging events to standard output')
			sys.stdin = self.config.stdin
			sys.stdout = self.config.stdout
			sys.stderr = self.config.stderr
		
		if evt != None:
			evt.Skip()
			
	def onEnableDisableThreading(self, evt):
		
		self.config.threading = self.threadingCheck.GetValue()
		if self.config.threading:
			print('Multi-threading was enabled')
			dlgBox(exceptionTitle="Warning", 
				exceptionMsg="Multi-threading is only an experimental feature for now! It might occasionally crash ORIGAMI, in which case you will lose your processed data!", 
				type="Warning")
		else:
			print('Multi-threading was disabled')
		
		if evt != None:
			evt.Skip()

	def __del__( self ):
		pass
	
		