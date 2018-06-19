# -*- coding: utf-8 -*- 
"""
@author: Lukasz G. Migas
"""

# Load modules
from __future__ import division
from panelPlot import panelPlot
from panelMultipleIons import panelMultipleIons
from panelMultipleTextFiles import panelMultipleTextFiles
from panelMultipleML import panelMML
from panelDocumentTree import panelDocuments
from panelLinearDriftCell import panelLinearDriftCell
from panelCCScalibration import panelCCScalibration
from panelAbout import panelAbout
from panelExtraParameters import panelParametersEdit
from panelProcess import panelProcessData
import dialogs
from panelOutput import dlgOutputInteractive as panelInteractive
from dialogs import panelExportSettings, panelSequenceAnalysis, panelNotifyOpenDocuments
from panelLog import panelLog

# Load libraries
import wx
import os
import wx.aui
import psutil
import numpy as np
from numpy import ceil, floor, int, rot90, array, flipud, absolute, round
from numpy import max as np_max
import sys
from time import clock, gmtime, strftime, sleep
from ids import *
from wx.lib.pubsub import pub 
from wx import ID_SAVE, ID_ANY
from toolbox import findPeakMax, getNarrow1Ddata, randomIntegerGenerator,\
    convertRGB255to1, convertRGB1to255, detectPeaks1D
from styles import makeMenuItem
from massLynxFcns import _checkTextFile


class MyFrame(wx.Frame):

    def __init__(self, parent, config, helpInfo, icons, id=-1, title='ORIGAMI', 
                 pos=wx.DefaultPosition, size=(1200, 600),
                 style=wx.FULL_REPAINT_ON_RESIZE): # wx.DEFAULT_FRAME_STYLE): #
        wx.Frame.__init__(self, None, title=title)
        
        #Extract size of screen
        self.displaysize = wx.GetDisplaySize()
        self.SetDimensions(0,0,self.displaysize[0],self.displaysize[1]-50)
        # Setup config container
        self.config = config
        self.icons = icons
        self.help = helpInfo
        self.presenter = parent
        
        self.plot_data = {}
        self.plot_scale = {}
        
        self._fullscreen = False
        
        file_drop_target = DragAndDrop(self)
        self.SetDropTarget(file_drop_target)
        
        icon = wx.EmptyIcon()
        icon.CopyFromBitmap(self.icons.iconsLib['origamiLogoDark16'])
        self.SetIcon(icon)
        
        # View parameters
        self.mode = None
        self.xpos = None
        self.ypos = None
        self.startX = None
        
        self.config.startTime = (strftime("%H-%M-%S_%d-%m-%Y", gmtime()))
              
        # Bind commands to events
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wx.EVT_SIZE,self.OnSize)
        self.Bind(wx.EVT_IDLE,self.OnIdle)           
    
        # Setup Notebook manager
        self._mgr = wx.aui.AuiManager(self)
        self._mgr.SetDockSizeConstraint(1, 1)

        # Load panels
        self.panelDocuments = panelDocuments(self, self.config, self.icons, self.presenter)
        self.panelPlots = panelPlot(self, self.config, self.presenter) # Plots
        self.panelMultipleIons= panelMultipleIons(self, self.config, self.icons, self.help, self.presenter) # List of ions
        self.panelMultipleText = panelMultipleTextFiles(self, self.config, self.icons, self.presenter) # List of files
        self.panelMML = panelMML(self, self.config, self.icons, self.presenter) # List of ML files
        self.panelLinearDT = panelLinearDriftCell(self, self.config, self.icons, self.presenter)
        self.panelCCS = panelCCScalibration(self, self.config, self.icons, self.presenter) # calibration panel
        self.panelLog = panelLog(self, self.config, self.icons)
        
        # Toolbar
        self.makeToolbar()
        if self.config._windowSettings['Toolbar']['orientation'] == 'top':
            self._mgr.AddPane(self.mainToolbar_horizontal, wx.aui.AuiPaneInfo()
                              .Name("Toolbar_horizontal").Caption("Toolbar_horizontal").ToolbarPane().Top()
                              .Show(self.config._windowSettings['Toolbar']['show'])
                              .Gripper(self.config._windowSettings['Toolbar']['show'])
                              .Dockable())
        else:
            self._mgr.AddPane(self.mainToolbar_vertical, wx.aui.AuiPaneInfo()
                              .Name("Toolbar_vertical").Caption("Toolbar_vertical").ToolbarPane().Left().GripperTop()
                              .Show(self.config._windowSettings['Toolbar']['show'])
                              .Gripper(self.config._windowSettings['Toolbar']['show'])
                              .Dockable())
        
        # Panel to store document information
        self._mgr.AddPane(self.panelDocuments,  wx.aui.AuiPaneInfo().Left().Caption('Documents')
                          .MinSize((250,100)).GripperTop().BottomDockable(False).TopDockable(False)
                          .Show(self.config._windowSettings['Documents']['show'])
                          .CloseButton(self.config._windowSettings['Documents']['close_button'])
                          .CaptionVisible(self.config._windowSettings['Documents']['caption'])
                          .Gripper(self.config._windowSettings['Documents']['gripper']))
        
        self._mgr.AddPane(self.panelPlots,  wx.aui.AuiPaneInfo().CenterPane().Caption('Plot')
                          .Show(self.config._windowSettings['Plots']['show'])
                          .CloseButton(self.config._windowSettings['Plots']['close_button'])
                          .CaptionVisible(self.config._windowSettings['Plots']['caption'])
                          .Gripper(self.config._windowSettings['Plots']['gripper'])
                          ) 
        
        # Panel to extract multiple ions from ML files
        self._mgr.AddPane(self.panelMultipleIons,  wx.aui.AuiPaneInfo().Right().Caption('Peak list')
                          .MinSize((300,-1)).GripperTop().BottomDockable(False).TopDockable(False)
                          .Show(self.config._windowSettings['Peak list']['show'])
                          .CloseButton(self.config._windowSettings['Peak list']['close_button'])
                          .CaptionVisible(self.config._windowSettings['Peak list']['caption'])
                          .Gripper(self.config._windowSettings['Peak list']['gripper'])
                          )

        
        # Panel to operate on multiple text files
        self._mgr.AddPane(self.panelMultipleText,  wx.aui.AuiPaneInfo().Right().Caption('Text files')
                          .MinSize((300,-1)).GripperTop().BottomDockable(False).TopDockable(False)
                          .Show(self.config._windowSettings['Text files']['show'])
                          .CloseButton(self.config._windowSettings['Text files']['close_button'])
                          .CaptionVisible(self.config._windowSettings['Text files']['caption'])
                          .Gripper(self.config._windowSettings['Text files']['gripper'])
                          )
        
        # Panel to operate on multiple ML files
        self._mgr.AddPane(self.panelMML,  wx.aui.AuiPaneInfo().Right().Caption('Multiple files')
                          .MinSize((300,-1)).GripperTop().BottomDockable(False).TopDockable(False)
                          .Show(self.config._windowSettings['Multiple files']['show'])
                          .CloseButton(self.config._windowSettings['Multiple files']['close_button'])
                          .CaptionVisible(self.config._windowSettings['Multiple files']['caption'])
                          .Gripper(self.config._windowSettings['Multiple files']['gripper'])
                          )
        
        # Panel to analyse linear DT data (Synapt)
        self._mgr.AddPane(self.panelLinearDT,  wx.aui.AuiPaneInfo().Right().Caption('Linear Drift Cell')
                          .MinSize((300,-1)).GripperTop().BottomDockable(False).TopDockable(False)
                          .Show(self.config._windowSettings['Linear Drift Cell']['show'])
                          .CloseButton(self.config._windowSettings['Linear Drift Cell']['close_button'])
                          .CaptionVisible(self.config._windowSettings['Linear Drift Cell']['caption'])
                          .Gripper(self.config._windowSettings['Linear Drift Cell']['gripper'])
                          )
        
        # Panel to perform CCS calibration
        self._mgr.AddPane(self.panelCCS,  wx.aui.AuiPaneInfo().Right().Caption('CCS calibration')
                          .MinSize((320,-1)).GripperTop().BottomDockable(False).TopDockable(False)
                          .Show(self.config._windowSettings['CCS calibration']['show'])
                          .CloseButton(self.config._windowSettings['CCS calibration']['close_button'])
                          .CaptionVisible(self.config._windowSettings['CCS calibration']['caption'])
                          .Gripper(self.config._windowSettings['CCS calibration']['gripper'])
                          )
        
        self._mgr.AddPane(self.panelLog,  wx.aui.AuiPaneInfo().Bottom()
                          .Caption(self.config._windowSettings['Log']['title'])
                          .MinSize((320,-1)).GripperTop()
                          .BottomDockable(True).TopDockable(True)
                          .Show(self.config._windowSettings['Log']['show'])
                          .CloseButton(self.config._windowSettings['Log']['close_button'])
                          .CaptionVisible(self.config._windowSettings['Log']['caption'])
                          .Gripper(self.config._windowSettings['Log']['gripper'])
                          .Float()
                          )
        
                
        # Setup listeners
        pub.subscribe(self.OnMotion, 'newxy')
        pub.subscribe(self.Add2Table, 'add2table')
        pub.subscribe(self.Add2TableMSDT, 'add2tableMSDT')
        pub.subscribe(self.OnMotionRange, 'extractRange')
        pub.subscribe(self.OnDistance, 'startX')
        pub.subscribe(self.presenter.OnChangedRMSF, 'changedZoom')
        pub.subscribe(self.onMode, 'currentMode') # update statusbar

        # Load other parts
        self._mgr.Update()
        self.makeBindings()
        self.statusBar()
        self.makeMenubar()
        self.SetMenuBar(self.mainMenubar)
        self.makeShortcuts()
        self.Maximize(True)
        
        # bind events
        self.Bind(wx.aui.EVT_AUI_PANE_CLOSE, self.pageClosed)
        self.Bind(wx.aui.EVT_AUI_PANE_RESTORE, self.pageRestored)
        
        # Fire up a couple of events
        self._onUpdateWindowSettings()
        self.onPaneOnOff(evt=None)
        self._onToggleOnStart()
          
    def _onUpdateWindowSettings(self):
        self.config._windowSettings['Documents']['id'] = ID_window_documentList
        self.config._windowSettings['Peak list']['id'] = ID_window_ionList
        self.config._windowSettings['CCS calibration']['id'] = ID_window_ccsList
        self.config._windowSettings['Linear Drift Cell']['id'] = ID_window_multiFieldList
        self.config._windowSettings['Text files']['id'] = ID_window_textList
        self.config._windowSettings['Multiple files']['id'] = ID_window_multipleMLList
        self.config._windowSettings['Log']['id'] = ID_window_logWindow
        return None
    
    def _onToggleOnStart(self):
        panelDict = {'Documents':ID_window_documentList,
                     'Multiple files':ID_window_multipleMLList,
                     'Peak list':ID_window_ionList, 
                     'Text files':ID_window_textList,
                     'CCS calibration':ID_window_ccsList, 
                     'Linear Drift Cell':ID_window_multiFieldList,
                     'Log':ID_window_logWindow}
        
        for panel in [self.panelDocuments, 
                      self.panelMML, self.panelLog,
                      self.panelMultipleIons, self.panelMultipleText,
                      self.panelCCS, self.panelLinearDT]:
            if self._mgr.GetPane(panel).IsShown():
                self.onFindToggleBy_ID(find_id=panelDict[self._mgr.GetPane(panel).caption], check=True)    
    
    def _onUpdatePlotData(self, plot_type=None):
        if plot_type == '2D':
            _data = self.presenter._get_replot_data(data_format='2D')
            try:
                yshape, xshape = _data[0].shape
                _yscale = yshape/np_max(_data[2])
                _xscale = xshape/np_max(_data[1])
                self.plot_data['2D'] = _data[0]
                self.plot_scale['2D'] = [_yscale, _xscale]
            except: pass
        elif plot_type == 'DT/MS':
            _data = self.presenter._get_replot_data(data_format='DT/MS')
            yshape, xshape = _data[0].shape
            _yscale = yshape/np_max(_data[2])
            _xscale = xshape/np_max(_data[1])
            self.plot_data['DT/MS'] = _data[0]
            self.plot_scale['DT/MS'] = [_yscale, _xscale]
        elif plot_type == 'RMSF':
            _data = self.presenter._get_replot_data(data_format='RMSF')
            yshape, xshape = _data[0].shape
            _yscale = yshape/np_max(_data[2])
            _xscale = xshape/np_max(_data[1])
            self.plot_data['DT/MS'] = _data[0]
            self.plot_scale['DT/MS'] = [_yscale, _xscale]
    
    def pageClosed(self, evt):
        # Keep track of which window is closed
        self.config._windowSettings[evt.GetPane().caption]['show'] = False
        # fire-up events
        evtID = self.onCheckToggleID(panel=evt.GetPane().caption)
        self.onPaneOnOff(evt=evtID)

    def pageRestored(self, evt):
        # Keep track of which window is restored
        self.config._windowSettings[evt.GetPane().caption]['show'] = True
        evtID = self.onCheckToggleID(panel=evt.GetPane().caption)
        self.onPaneOnOff(evt=evtID)
        # fire-up events
                
        if evt != None:
            evt.Skip()
           
    def makeBindings(self):
        '''
        Collection of all bindings for various functions
        '''
#         self.Bind(wx.EVT_BUTTON, self.presenter.onExtract2DimsOverMZrange, self.panelControls.extractBtn)
#         self.Bind(wx.EVT_BUTTON, self.presenter.onDocumentColour, self.panelControls.colorBtn)
#         self.Bind(wx.EVT_BUTTON, self.presenter.onPickPeaks, self.panelControls.findPeaksBtn)
#         self.Bind(wx.EVT_BUTTON, self.presenter.onChangePlotStyle, self.panelControls.applyStyleBtn)   
#         self.Bind(wx.EVT_COMBOBOX, self.selectOverlayMethod, id=ID_selectOverlayMethod)
        self.Bind(wx.EVT_TOOL, self.presenter.on2DMultipleTextFiles, id=ID_openTextFiles)
        self.Bind(wx.EVT_TOOL, self.presenter.onProcessMultipleTextFiles, id=ID_processTextFiles)
        self.Bind(wx.EVT_TOOL, self.presenter.onOverlayMultipleIons, id=ID_overlayTextFromList)
#         self.Bind(wx.EVT_COMBOBOX, self.selectTextOverlayMethod, id=ID_textSelectOverlayMethod)
        self.Bind(wx.EVT_TOOL, self.presenter.onExtractDToverMZrangeMultiple, id=ID_extractDriftVoltagesForEachIon)
        self.Bind(wx.EVT_TOOL, self.presenter.onOpenMultipleMLFiles, id=ID_openMassLynxFiles)
           
    def statusBar(self):
#         
#         self.mainStatusbar = ESB.EnhancedStatusBar(self, -1)
#         self.mainStatusbar.SetSize((-1, 22))
#         self.mainStatusbar.SetFieldsCount(6)
        self.mainStatusbar = self.CreateStatusBar(6, wx.ST_SIZEGRIP, wx.ID_ANY)
        # 0 = current x y pos
        # 1 = m/z range
        # 2 = MSMS mass
        # 3 = status information
        # 4 = present working file
        # 5 = tool
        # 6 = process
        self.mainStatusbar.SetStatusWidths([250,80,80,400,-1, 50])
        self.mainStatusbar.SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.NORMAL))
 
    def onMode(self, dataOut):
        shift, ctrl, alt, add2table, wheel, zoom = dataOut
        self.mode = ''
        myCursor = wx.StockCursor(wx.CURSOR_ARROW)
        if alt: 
            self.mode = 'Measure'
            myCursor = wx.StockCursor(wx.CURSOR_MAGNIFIER)
        elif ctrl: 
            self.mode = 'Add data'
            myCursor = wx.StockCursor(wx.CURSOR_CROSS)
        elif add2table: 
            self.mode = 'Add data'
            myCursor = wx.StockCursor(wx.CURSOR_CROSS)
        elif shift: 
            self.mode = 'Wheel zoom Y'
            myCursor= wx.StockCursor(wx.CURSOR_SIZENS)
        elif wheel:
            self.mode = 'Wheel zoom X'
            myCursor= wx.StockCursor(wx.CURSOR_SIZEWE)
        elif alt and ctrl: 
            self.mode = ''
        elif zoom:
            self.mode = 'Zooming'
            myCursor= wx.StockCursor(wx.CURSOR_MAGNIFIER)
        
        self.SetCursor(myCursor)
        self.SetStatusText("%s" % (self.mode), number=5)

    def makeMenubar(self):
        self.mainMenubar = wx.MenuBar()  
        
        # setup recent sub-menu
        self.menuRecent = wx.Menu()
        self.updateRecentFiles()
        
        # setup binary sub-menu
        openBinaryMenu = wx.Menu()
        openBinaryMenu.Append(ID_openMSFile, 'Open MS from MassLynx file (MS .1dMZ)\tCtrl+M')
        openBinaryMenu.Append(ID_open1DIMSFile, 'Open 1D IM-MS from MassLynx file (1D IM-MS, .1dDT)')
        openBinaryMenu.Append(ID_open2DIMSFile, 'Open 2D IM-MS from MassLynx file (2D IM-MS, .2dRTDT)\tCtrl+D')

        menuFile = wx.Menu()
        menuFile.AppendItem(makeMenuItem(parent=menuFile, id=ID_openDocument,
                                         text='Open ORIGAMI Document file (.pickle)\tCtrl+Shift+P', 
                                         bitmap=self.icons.iconsLib['open_project_16']))
        menuFile.AppendSeparator()
        menuFile.AppendItem(makeMenuItem(parent=menuFile, id=ID_openORIGAMIRawFile,
                                         text='Open ORIGAMI MassLynx (.raw) file [CIU]\tCtrl+R', 
                                         bitmap=self.icons.iconsLib['open_origami_16']))
        
        menuFile.AppendItem(makeMenuItem(parent=menuFile, id=ID_openMultipleORIGAMIRawFiles,
                                         text='Open multiple ORIGAMI MassLynx (.raw) files [CIU]\tCtrl+Shift+Q', 
                                         bitmap=self.icons.iconsLib['open_origamiMany_16']))
        menuFile.AppendSeparator()
        menuFile.AppendItem(makeMenuItem(parent=menuFile, id=ID_openMassLynxFiles,
                                         text='Open multiple MassLynx (.raw) files [CIU]\tCtrl+Shift+R', 
                                         bitmap=self.icons.iconsLib['open_masslynxMany_16']))
        
        menuFile.Append(ID_addCCScalibrantFile, 'Open Calibration MassLynx (.raw) file\tCtrl+C')
        menuFile.Append(ID_openLinearDTRawFile, 'Open Linear DT MassLynx (.raw) file\tCtrl+F')
        menuFile.Append(ID_openMassLynxFile, 'Open MassLynx (no IM-MS, .raw) file\tCtrl+Shift+M')
        menuFile.AppendMenu(ID_ANY, 'Open MassLynx...', openBinaryMenu)
        menuFile.AppendSeparator()
        menuFile.AppendItem(makeMenuItem(parent=menuFile, id=ID_addNewOverlayDoc,
                                         text='Create blank COMPARISON document [CIU]', 
                                         bitmap=self.icons.iconsLib['new_document_16']))
        menuFile.AppendItem(makeMenuItem(parent=menuFile, id=ID_addNewInteractiveDoc,
                                         text='Create blank INTERACTIVE document', 
                                         bitmap=self.icons.iconsLib['bokehLogo_16']))
        menuFile.AppendSeparator()
        menuFile.AppendItem(makeMenuItem(parent=menuFile, id=ID_openMStxtFile,
                                         text='Open MS Text file', 
                                         bitmap=None))
        menuFile.AppendItem(makeMenuItem(parent=menuFile, id=ID_openIMStxtFile,
                                         text='Open IM-MS Text file [CIU]\tCtrl+T', 
                                         bitmap=self.icons.iconsLib['open_text_16']))
        menuFile.AppendItem(makeMenuItem(parent=menuFile, id=ID_openTextFilesMenu,
                                         text='Open multiple IM-MS text files [CIU]\tCtrl+Shift+T', 
                                         bitmap=self.icons.iconsLib['open_textMany_16']))
        menuFile.AppendSeparator()
        menuFile.AppendItem(makeMenuItem(parent=menuFile, id=ID_getSpectrumFromClipboard,
                                         text='Grab MS spectrum from clipboard\tCtrl+V', 
                                         bitmap=self.icons.iconsLib['filelist_16']))
        menuFile.AppendSeparator()
        menuFile.AppendMenu(ID_fileMenu_openRecent, "Open Recent", self.menuRecent)
        menuFile.AppendSeparator()
        menuFile.AppendItem(makeMenuItem(parent=menuFile, id=ID_saveDocument,
                                         text='Save document (.pickle)\tCtrl+S', 
                                         bitmap=self.icons.iconsLib['save16']))
        menuFile.AppendItem(makeMenuItem(parent=menuFile, id=ID_saveAllDocuments,
                                         text='Save all documents (.pickle)', 
                                         bitmap=self.icons.iconsLib['pickle_16']))
        self.mainMenubar.Append(menuFile, '&File')
        
        # PROCESS
        menuProcess = wx.Menu()
        menuProcess.AppendItem(makeMenuItem(parent=menuProcess, id=ID_processSettings_ExtractData,
                                            text='Settings: &Extract data\tShift+1', 
                                            bitmap=self.icons.iconsLib['process_extract_16']))
        
        menuProcess.AppendItem(makeMenuItem(parent=menuProcess, id=ID_processSettings_ORIGAMI,
                                            text='Settings: &ORIGAMI\tShift+2', 
                                            bitmap=self.icons.iconsLib['process_origami_16']))
        
        menuProcess.AppendItem(makeMenuItem(parent=menuProcess, id=ID_processSettings_MS,
                                            text='Settings: &Process mass spectra\tShift+3', 
                                            bitmap=self.icons.iconsLib['process_ms_16']))
        
        menuProcess.AppendItem(makeMenuItem(parent=menuProcess, id=ID_processSettings_2D,
                                            text='Settings: Process &2D heatmaps\tShift+4', 
                                            bitmap=self.icons.iconsLib['process_2d_16']))
        
        menuProcess.AppendItem(makeMenuItem(parent=menuProcess, id=ID_processSettings_FindPeaks,
                                            text='Settings: Peak &fitting\tShift+5', 
                                            bitmap=self.icons.iconsLib['process_fit_16']))

        menuProcess.AppendItem(makeMenuItem(parent=menuProcess, id=ID_processSettings_UniDec,
                                            text='Settings: &UniDec\tShift+6', 
                                            bitmap=self.icons.iconsLib['process_unidec_16']))
        
        self.mainMenubar.Append(menuProcess, '&Process')
        
        # PLOT 
        menuPlot = wx.Menu()
        menuPlot.AppendItem(makeMenuItem(parent=menuPlot, id=ID_extraSettings_plot1D,
                                         text='Settings: Plot &1D', 
                                         bitmap=self.icons.iconsLib['panel_plot1D_16']))
        
        menuPlot.AppendItem(makeMenuItem(parent=menuPlot, id=ID_extraSettings_plot2D,
                                         text='Settings: Plot &2D', 
                                         bitmap=self.icons.iconsLib['panel_plot2D_16']))
        
        menuPlot.AppendItem(makeMenuItem(parent=menuPlot, id=ID_extraSettings_plot3D,
                                         text='Settings: Plot &3D', 
                                         bitmap=self.icons.iconsLib['panel_plot3D_16']))
        
        menuPlot.AppendItem(makeMenuItem(parent=menuPlot, id=ID_extraSettings_colorbar,
                                         text='Settings: &Colorbar', 
                                         bitmap=self.icons.iconsLib['panel_colorbar_16']))
        
        menuPlot.AppendItem(makeMenuItem(parent=menuPlot, id=ID_extraSettings_legend,
                                         text='Settings: &Legend', 
                                         bitmap=self.icons.iconsLib['panel_legend_16']))
        
        menuPlot.AppendItem(makeMenuItem(parent=menuPlot, id=ID_extraSettings_rmsd,
                                         text='Settings: &RMSD', 
                                         bitmap=self.icons.iconsLib['panel_rmsd_16']))
        
        menuPlot.AppendItem(makeMenuItem(parent=menuPlot, id=ID_extraSettings_waterfall,
                                         text='Settings: &Waterfall', 
                                         bitmap=self.icons.iconsLib['panel_waterfall_16']))

        menuPlot.AppendItem(makeMenuItem(parent=menuPlot, id=ID_extraSettings_general,
                                         text='Settings: &General', 
                                         bitmap=self.icons.iconsLib['panel_general2_16']))
        menuPlot.AppendSeparator()
        menuPlot.Append(ID_plots_showCursorGrid, 'Update plot parameters')
        menuPlot.Append(ID_plots_resetZoom, 'Reset zoom tool\tF12')
        self.mainMenubar.Append(menuPlot, '&Plot')
        
        # VIEW
        menuView = wx.Menu()
        menuView.AppendItem(makeMenuItem(parent=menuView, id=ID_clearAllPlots,
                                         text='&Clear all plots', 
                                         bitmap=self.icons.iconsLib['clear_16']))
        menuView.AppendItem(makeMenuItem(parent=menuView, id=ID_saveAsInteractive,
                                         text='Open &interactive output panel...\tShift+Z', 
                                         bitmap=self.icons.iconsLib['bokehLogo_16']))
        menuView.AppendSeparator()
        self.documentsPage = menuView.Append(ID_window_documentList, 'Panel: Documents\tCtrl+1', kind=wx.ITEM_CHECK)
        self.mzTable = menuView.Append(ID_window_ionList, 'Panel: Peak list\tCtrl+3', kind=wx.ITEM_CHECK)
        self.textTable = menuView.Append(ID_window_textList, 'Panel: Text list\tCtrl+4', kind=wx.ITEM_CHECK)
        self.multipleMLTable = menuView.Append(ID_window_multipleMLList, 'Panel: Multiple files\tCtrl+5', kind=wx.ITEM_CHECK)
        self.multifieldTable = menuView.Append(ID_window_multiFieldList, 'Panel: Linear DT-IMS\tCtrl+6', kind=wx.ITEM_CHECK)
        self.ccsTable = menuView.Append(ID_window_ccsList, 'Panel: CCS calibration\tCtrl+7', kind=wx.ITEM_CHECK)
        self.window_logWindow = menuView.Append(ID_window_logWindow, 'Panel: Log\tCtrl+8', kind=wx.ITEM_CHECK)
        menuView.AppendSeparator()
        menuView.Append(ID_window_all, 'Panel: Restore &all')
        menuView.AppendSeparator()
        self.toolbar_top = menuView.Append(ID_toolbar_top, 'Toolbar: &Top', kind=wx.ITEM_RADIO)
        self.toolbar_bottom = menuView.Append(ID_toolbar_bottom, 'Toolbar: &Bottom', kind=wx.ITEM_RADIO)
        self.toolbar_left = menuView.Append(ID_toolbar_left, 'Toolbar: &Left', kind=wx.ITEM_RADIO)
        self.toolbar_right = menuView.Append(ID_toolbar_right, 'Toolbar: &Right', kind=wx.ITEM_RADIO)
        menuView.AppendSeparator()
        menuView.AppendItem(makeMenuItem(parent=menuView, id=ID_windowMaximize,
                                         text='Maximize window', 
                                         bitmap=self.icons.iconsLib['maximize_16']))
        menuView.AppendItem(makeMenuItem(parent=menuView, id=ID_windowMinimize,
                                         text='Minimize window', 
                                         bitmap=self.icons.iconsLib['minimize_16']))
        menuView.AppendItem(makeMenuItem(parent=menuView, id=ID_windowFullscreen,
                                         text='Toggle fullscreen\tAlt+F11', 
                                         bitmap=self.icons.iconsLib['fullscreen_16']))
        self.mainMenubar.Append(menuView, '&View')
        
#         # UTILITIES
#         menuUtilities = wx.Menu()
#         menuUtilities.AppendItem(makeMenuItem(parent=menuUtilities, id=ID_sequence_openGUI,
#                                               text='Sequence analysis...', 
#                                               bitmap=None))
#         self.mainMenubar.Append(menuUtilities, '&Utilities')
#         
        # CONFIG
        menuConfig = wx.Menu()
        menuConfig.AppendItem(makeMenuItem(parent=menuConfig, id=ID_saveConfig,
                                           text='Export configuration XML file (default)\tCtrl+S', 
                                           bitmap=self.icons.iconsLib['export_config_16']))
        menuConfig.AppendItem(makeMenuItem(parent=menuConfig, id=ID_saveAsConfig,
                                           text='Export configuration XML file as...\tCtrl+Shift+S', 
                                           bitmap=None))
        menuConfig.AppendSeparator()
        menuConfig.AppendItem(makeMenuItem(parent=menuConfig, id=ID_openConfig,
                                           text='Import configuration XML file (default)\tCtrl+Shift+O', 
                                           bitmap=self.icons.iconsLib['import_config_16']))
        menuConfig.AppendItem(makeMenuItem(parent=menuConfig, id=ID_openAsConfig,
                                           text='Import configuration XML file from...', 
                                           bitmap=None))
        menuConfig.AppendSeparator()
        menuConfig.AppendItem(makeMenuItem(parent=menuConfig, id=ID_openCCScalibrationDatabse,
                                           text='Import CCS calibration database\tCtrl+Alt+C', 
                                           bitmap=self.icons.iconsLib['filelist_16']))
        menuConfig.AppendItem(makeMenuItem(parent=menuConfig, id=ID_selectCalibrant,
                                         text='Show CCS calibrants\tCtrl+Shift+C', 
                                         bitmap=self.icons.iconsLib['ccs_table_16']))
        menuConfig.AppendSeparator()
        menuConfig.AppendItem(makeMenuItem(parent=menuConfig, id=ID_importExportSettings_peaklist,
                                           text='Import parameters: Peaklist', 
                                           bitmap=None))
        menuConfig.AppendItem(makeMenuItem(parent=menuConfig, id=ID_importExportSettings_image,
                                           text='Export parameters: Image', 
                                           bitmap=None))
        menuConfig.AppendItem(makeMenuItem(parent=menuConfig, id=ID_importExportSettings_file,
                                           text='Export parameters: File', 
                                           bitmap=None))
        menuConfig.AppendSeparator()
        menuConfig.AppendItem(makeMenuItem(parent=menuConfig, id=ID_setDriftScopeDir,
                                           text='Set DriftScope path...', 
                                           bitmap=self.icons.iconsLib['driftscope_16']))
        self.mainMenubar.Append(menuConfig, '&Libraries')
        
        
        otherSoftwareMenu = wx.Menu()
        otherSoftwareMenu.AppendItem(makeMenuItem(parent=otherSoftwareMenu, id=ID_help_UniDecInfo,
                                                  text='About UniDec engine...', 
                                                  bitmap=self.icons.iconsLib['process_unidec_16']))
#         otherSoftwareMenu.Append(ID_open1DIMSFile, 'About CIDER...')
        
        helpPagesMenu = wx.Menu()
        helpPagesMenu.AppendItem(makeMenuItem(parent=helpPagesMenu, id=ID_help_page_dataLoading,
                                              text='Learn more: Loading data', 
                                              bitmap=self.icons.iconsLib['open16']))
        
        helpPagesMenu.AppendItem(makeMenuItem(parent=helpPagesMenu, id=ID_help_page_dataExtraction,
                                              text='Learn more: Data extraction', 
                                              bitmap=self.icons.iconsLib['extract16']))
        
        helpPagesMenu.AppendItem(makeMenuItem(parent=helpPagesMenu, id=ID_help_page_UniDec,
                                              text='Learn more: MS deconvolution using UniDec', 
                                              bitmap=self.icons.iconsLib['process_unidec_16']))
        
        helpPagesMenu.AppendItem(makeMenuItem(parent=helpPagesMenu, id=ID_help_page_ORIGAMI,
                                              text='Learn more: ORIGAMI-MS (Automated CIU)', 
                                              bitmap=self.icons.iconsLib['origamiLogoDark16']))
        
        helpPagesMenu.AppendItem(makeMenuItem(parent=helpPagesMenu, id=ID_help_page_multipleFiles,
                                              text='Learn more: Multiple files (Manual CIU)', 
                                              bitmap=self.icons.iconsLib['panel_mll__16']))
        
        helpPagesMenu.AppendItem(makeMenuItem(parent=helpPagesMenu, id=ID_help_page_overlay,
                                              text='Learn more: Overlay documents', 
                                              bitmap=self.icons.iconsLib['overlay16']))
        
#         helpPagesMenu.AppendItem(makeMenuItem(parent=helpPagesMenu, id=ID_help_page_linearDT,
#                                               text='Learn more: Linear Drift-time analysis', 
#                                               bitmap=self.icons.iconsLib['panel_dt_16']))
#         
#         helpPagesMenu.AppendItem(makeMenuItem(parent=helpPagesMenu, id=ID_help_page_CCScalibration,
#                                               text='Learn more: CCS calibration', 
#                                               bitmap=self.icons.iconsLib['panel_ccs_16']))
        
        helpPagesMenu.AppendItem(makeMenuItem(parent=helpPagesMenu, id=ID_help_page_Interactive,
                                              text='Learn more: Interactive output', 
                                              bitmap=self.icons.iconsLib['bokehLogo_16']))
        

        
        # HELP MENU
        menuHelp = wx.Menu()
        menuHelp.AppendMenu(ID_ANY, 'Help pages...', helpPagesMenu)
        menuHelp.AppendSeparator()
        menuHelp.AppendItem(makeMenuItem(parent=menuHelp, id=ID_helpGuide,
                                         text='Open User Guide... (web)\tF1', 
                                         bitmap=self.icons.iconsLib['web_access_16']))
        menuHelp.AppendItem(makeMenuItem(parent=menuHelp, id=ID_helpGuideLocal,
                                         text='Open User Guide... (local)\tF2', 
                                         bitmap=self.icons.iconsLib['file_pdf']))
        menuHelp.AppendItem(makeMenuItem(parent=menuHelp, id=ID_helpYoutube,
                                         text='Check out video guides... (web)', 
                                         bitmap=self.icons.iconsLib['youtube16'],
                                         help_text=self.help.link_youtube))
        menuHelp.AppendItem(makeMenuItem(parent=menuHelp, id=ID_helpNewVersion,
                                         text='Check for updates... (web)', 
                                         bitmap=self.icons.iconsLib['github16']))
        menuHelp.AppendItem(makeMenuItem(parent=menuHelp, id=ID_helpCite,
                                         text='Paper to cite... (web)', 
                                         bitmap=self.icons.iconsLib['cite_16']))
        menuHelp.AppendSeparator()
        menuHelp.AppendMenu(ID_ANY, 'About other software...', otherSoftwareMenu)
        menuHelp.AppendSeparator()
        menuHelp.AppendItem(makeMenuItem(parent=menuHelp, id=ID_helpNewFeatures,
                                         text='Request new features... (web)', 
                                         bitmap=self.icons.iconsLib['request_16']))
        menuHelp.AppendItem(makeMenuItem(parent=menuHelp, id=ID_helpReportBugs,
                                         text='Report bugs... (web)', 
                                         bitmap=self.icons.iconsLib['bug_16']))
        menuHelp.AppendSeparator()
#         menuHelp.AppendItem(makeMenuItem(parent=menuHelp, id=ID_CHECK_VERSION,
#                                          text='Check version...', 
#                                          bitmap=self.icons.iconsLib['blank_16']))
        menuHelp.AppendItem(makeMenuItem(parent=menuHelp, id=ID_SHOW_ABOUT,
                                         text='About ORIGAMI\tCtrl+Shift+A', 
                                         bitmap=self.icons.iconsLib['origamiLogoDark16']))
        self.mainMenubar.Append(menuHelp, '&Help')
        
        self.SetMenuBar(self.mainMenubar)
        
        # Menu events
        self.Bind(wx.EVT_MENU_HIGHLIGHT_ALL, self.OnMenuHighlight)
        
        # Bind functions to menu
        # HELP MENU
        self.Bind(wx.EVT_MENU, self.onHelpAbout, id=ID_SHOW_ABOUT)
        self.Bind(wx.EVT_MENU, self.presenter.onCheckVersion, id=ID_CHECK_VERSION)
        self.Bind(wx.EVT_MENU, self.presenter.onLibraryLink, id=ID_helpGuide)
        self.Bind(wx.EVT_MENU, self.presenter.onOpenUserGuide, id=ID_helpGuideLocal)
        self.Bind(wx.EVT_MENU, self.presenter.onLibraryLink, id=ID_helpCite)
        self.Bind(wx.EVT_MENU, self.presenter.onLibraryLink, id=ID_helpYoutube)
        self.Bind(wx.EVT_MENU, self.presenter.onLibraryLink, id=ID_helpNewVersion)
        self.Bind(wx.EVT_MENU, self.presenter.onLibraryLink, id=ID_helpReportBugs)
        self.Bind(wx.EVT_MENU, self.presenter.onLibraryLink, id=ID_helpNewFeatures)
        self.Bind(wx.EVT_MENU, self.presenter.openHTMLViewer, id=ID_help_UniDecInfo)
        self.Bind(wx.EVT_MENU, self.presenter.onRebootWindow, id=ID_RESET_ORIGAMI)
        
        self.Bind(wx.EVT_MENU, self.presenter.openHTMLViewer, id=ID_help_page_dataLoading)
        self.Bind(wx.EVT_MENU, self.presenter.openHTMLViewer, id=ID_help_page_UniDec)
        self.Bind(wx.EVT_MENU, self.presenter.openHTMLViewer, id=ID_help_page_ORIGAMI)
        self.Bind(wx.EVT_MENU, self.presenter.openHTMLViewer, id=ID_help_page_overlay)
        self.Bind(wx.EVT_MENU, self.presenter.openHTMLViewer, id=ID_help_page_multipleFiles)
        self.Bind(wx.EVT_MENU, self.presenter.openHTMLViewer, id=ID_help_page_linearDT)
        self.Bind(wx.EVT_MENU, self.presenter.openHTMLViewer, id=ID_help_page_CCScalibration)
        self.Bind(wx.EVT_MENU, self.presenter.openHTMLViewer, id=ID_help_page_dataExtraction)
        self.Bind(wx.EVT_MENU, self.presenter.openHTMLViewer, id=ID_help_page_Interactive)
        
        # FILE MENU
        self.Bind(wx.EVT_MENU, self.presenter.onOrigamiRawDirectory, id=ID_openORIGAMIRawFile) 
        self.Bind(wx.EVT_MENU, self.presenter.onOrigamiRawDirectory, id=ID_openIRRawFile)
        self.Bind(wx.EVT_MENU, self.presenter.onOpenMultipleOrigamiFiles, id=ID_openMultipleORIGAMIRawFiles)
        self.Bind(wx.EVT_MENU, self.presenter.onCalibrantRawDirectory, id=ID_addCCScalibrantFile)
        self.Bind(wx.EVT_MENU, self.presenter.onLinearDTirectory, id=ID_openLinearDTRawFile)       
        self.Bind(wx.EVT_MENU, self.presenter.onMSDirectory, id=ID_openMSFile)
        self.Bind(wx.EVT_MENU, self.presenter.on1DIMSDirectory, id=ID_open1DIMSFile)
        self.Bind(wx.EVT_MENU, self.presenter.on2DIMSDirectory, id=ID_open2DIMSFile)
        self.Bind(wx.EVT_MENU, self.presenter.onMSbinaryFile, id=ID_openMSbinFile)
        self.Bind(wx.EVT_MENU, self.presenter.on1DbinaryFile, id=ID_open1DbinFile)
        self.Bind(wx.EVT_MENU, self.presenter.on2DbinaryFile, id=ID_open2DbinFile)
        self.Bind(wx.EVT_MENU, self.presenter.on2DTextFile, id=ID_openIMStxtFile)
        self.Bind(wx.EVT_MENU, self.presenter.on2DMultipleTextFiles, id=ID_openTextFilesMenu)
        self.Bind(wx.EVT_MENU, self.presenter.onOpenDocument, id=ID_openDocument)
        self.Bind(wx.EVT_MENU, self.presenter.onSaveDocument, id=ID_saveDocument)
        self.Bind(wx.EVT_MENU, self.presenter.onIRTextFile, id=ID_openIRTextile)
        self.Bind(wx.EVT_MENU, self.presenter.onOpenMS, id=ID_openMassLynxFile)
        self.Bind(wx.EVT_MENU, self.presenter.onAddBlankDocument, id=ID_addNewInteractiveDoc)
        self.Bind(wx.EVT_MENU, self.presenter.onMSTextFile, id=ID_openMStxtFile)
        self.Bind(wx.EVT_MENU, self.presenter.onMSFromClipboard, id=ID_getSpectrumFromClipboard)
        
        
        # PROCESS MENU
        self.Bind(wx.EVT_MENU, self.onProcessParameters, id=ID_processSettings_ExtractData) 
        self.Bind(wx.EVT_MENU, self.onProcessParameters, id=ID_processSettings_ORIGAMI) 
        self.Bind(wx.EVT_MENU, self.onProcessParameters, id=ID_processSettings_FindPeaks) 
        self.Bind(wx.EVT_MENU, self.onProcessParameters, id=ID_processSettings_MS) 
        self.Bind(wx.EVT_MENU, self.onProcessParameters, id=ID_processSettings_2D)
        self.Bind(wx.EVT_MENU, self.onProcessParameters, id=ID_processSettings_UniDec)  
        
        # PLOT
        self.Bind(wx.EVT_MENU, self.onPlotParameters, id=ID_extraSettings_plot1D)
        self.Bind(wx.EVT_MENU, self.onPlotParameters, id=ID_extraSettings_plot2D)
        self.Bind(wx.EVT_MENU, self.onPlotParameters, id=ID_extraSettings_plot3D)
        self.Bind(wx.EVT_MENU, self.onPlotParameters, id=ID_extraSettings_legend)
        self.Bind(wx.EVT_MENU, self.onPlotParameters, id=ID_extraSettings_colorbar)
        self.Bind(wx.EVT_MENU, self.onPlotParameters, id=ID_extraSettings_rmsd)
        self.Bind(wx.EVT_MENU, self.onPlotParameters, id=ID_extraSettings_waterfall)
        self.Bind(wx.EVT_MENU, self.onPlotParameters, id=ID_extraSettings_general)
        self.Bind(wx.EVT_MENU, self.presenter.onRebootZoom, id=ID_plots_resetZoom)
        self.Bind(wx.EVT_MENU, self.updatePlots, id=ID_plots_showCursorGrid)    
        
        # OUTPUT
        self.Bind(wx.EVT_MENU, self.panelPlots.save_images,id=ID_saveOverlayImage)
        self.Bind(wx.EVT_MENU, self.panelPlots.save_images,id=ID_saveMSImage)
        self.Bind(wx.EVT_MENU, self.panelPlots.save_images,id=ID_saveMZDTImage)
        self.Bind(wx.EVT_MENU, self.panelPlots.save_images,id=ID_saveRTImage)
        self.Bind(wx.EVT_MENU, self.panelPlots.save_images,id=ID_save1DImage)
        self.Bind(wx.EVT_MENU, self.panelPlots.save_images,id=ID_save2DImage)
        self.Bind(wx.EVT_MENU, self.panelPlots.save_images,id=ID_save3DImage)
        self.Bind(wx.EVT_MENU, self.panelPlots.save_images,id=ID_saveWaterfallImage)
        self.Bind(wx.EVT_MENU, self.panelPlots.save_images,id=ID_saveRMSDImage)
        self.Bind(wx.EVT_MENU, self.panelPlots.save_images,id=ID_saveRMSFImage)
        self.Bind(wx.EVT_MENU, self.panelPlots.save_images,id=ID_saveRMSDmatrixImage)
        # self.Bind(wx.EVT_MENU, self.saveFigures, id=ID_saveAllImages)
        self.Bind(wx.EVT_MENU, self.openSaveAsDlg, id=ID_saveAsInteractive)
                
        # UTILITIES
        self.Bind(wx.EVT_MENU, self.onSequenceEditor, id=ID_sequence_openGUI)
        
        # CONFIG MENU
        self.Bind(wx.EVT_MENU, self.presenter.onExportConfig, id=ID_saveConfig)
        self.Bind(wx.EVT_MENU, self.presenter.onExportConfig, id=ID_saveAsConfig)
        self.Bind(wx.EVT_MENU, self.presenter.onImportConfig, id=ID_openConfig)  
        self.Bind(wx.EVT_MENU, self.presenter.onImportConfig, id=ID_openAsConfig)  
        self.Bind(wx.EVT_MENU, self.presenter.onSetupDriftScope, id=ID_setDriftScopeDir)  
        self.Bind(wx.EVT_MENU, self.presenter.onSelectProtein, id=ID_selectCalibrant)  
        self.Bind(wx.EVT_MENU, self.presenter.onImportCCSDatabase, id=ID_openCCScalibrationDatabse)
        self.Bind(wx.EVT_MENU, self.onExportParameters, id=ID_importExportSettings_peaklist)
        self.Bind(wx.EVT_MENU, self.onExportParameters, id=ID_importExportSettings_image)
        self.Bind(wx.EVT_MENU, self.onExportParameters, id=ID_importExportSettings_file)
        
        # VIEW MENU
        self.Bind(wx.EVT_MENU, self.onPaneOnOff, id=ID_window_all)
        self.Bind(wx.EVT_MENU, self.onPaneOnOff, self.documentsPage)
        self.Bind(wx.EVT_MENU, self.onPaneOnOff, self.mzTable)
        self.Bind(wx.EVT_MENU, self.onPaneOnOff, self.multifieldTable)
        self.Bind(wx.EVT_MENU, self.onPaneOnOff, self.textTable)
        self.Bind(wx.EVT_MENU, self.onPaneOnOff, self.multipleMLTable)
        self.Bind(wx.EVT_MENU, self.onPaneOnOff, self.ccsTable)
        self.Bind(wx.EVT_MENU, self.onPaneOnOff, id=ID_window_logWindow)
        self.Bind(wx.EVT_MENU, self.onWindowMaximize, id=ID_windowMaximize)
        self.Bind(wx.EVT_MENU, self.onWindowIconize, id=ID_windowMinimize)
        self.Bind(wx.EVT_MENU, self.onWindowFullscreen, id=ID_windowFullscreen)
        self.Bind(wx.EVT_MENU, self.presenter.onClearAllPlots, id=ID_clearAllPlots)
        self.Bind(wx.EVT_MENU, self.onToolbarPosition, id=ID_toolbar_top)
        self.Bind(wx.EVT_MENU, self.onToolbarPosition, id=ID_toolbar_bottom)
        self.Bind(wx.EVT_MENU, self.onToolbarPosition, id=ID_toolbar_left)
        self.Bind(wx.EVT_MENU, self.onToolbarPosition, id=ID_toolbar_right)
        
    def OnMenuHighlight(self, evt):
        # Show how to get menu item info from this event handler
        itemID = evt.GetId()
        try:
            msg = self.GetMenuBar().FindItemById(itemID).GetHelp()
            self.SetStatusText(msg, number=4)
        except:
            self.SetStatusText("", number=4)

    def onWindowMaximize(self, evt):
        """Maximize app."""
        self.Maximize()
    # ----
    
    def onWindowIconize(self, evt):
        """Iconize app."""
        self.Iconize()
    # ----
    
    def onWindowFullscreen(self, evt):
        """Fullscreen app."""
        self._fullscreen = not self._fullscreen
        self.ShowFullScreen(self._fullscreen, style=wx.FULLSCREEN_ALL & ~(wx.FULLSCREEN_NOMENUBAR|wx.FULLSCREEN_NOSTATUSBAR))
    # ----
    
    def onHelpAbout(self, evt):
        """Show About mMass panel."""
        
        about = panelAbout(self, self.presenter, 
                           'About ORIGAMI', 
                           self.config,
                           self.icons)
        about.Centre()
        about.Show()
        about.SetFocus()
       
    def makeShortcuts(self):
        """
        Setup shortcuts for the GUI application
        """
        # Setup shortcuts. Format: 'KEY', 'FUNCTION', 'MODIFIER'
        ctrlkeys=[
            ["M", self.presenter.onMSDirectory, wx.ACCEL_CTRL],
            ["D", self.presenter.on2DIMSDirectory, wx.ACCEL_CTRL],
            ["M", self.presenter.onMSbinaryFile, wx.ACCEL_ALT],
            ["D", self.presenter.on2DbinaryFile, wx.ACCEL_ALT],
            ["I", self.panelDocuments.topP.documents.onOpenDocInfo, wx.ACCEL_CTRL],
            ["W", self.presenter.on2DMultipleTextFiles, wx.ACCEL_CTRL],
            ["L", self.presenter.onOpenPeakListCSV, wx.ACCEL_CTRL],
            ["Z", self.openSaveAsDlg, wx.ACCEL_SHIFT],
            ["G", self.presenter.openDirectory, wx.ACCEL_CTRL],
            ]
        keyIDs = [wx.NewId() for a in ctrlkeys]
        ctrllist = []
        for i , k in enumerate(ctrlkeys):
            self.Bind(wx.EVT_MENU, k[1], id=keyIDs[i])
            ctrllist.append((k[2], ord(k[0]), keyIDs[i])) 
            
        # Add more shortcuts with known IDs
        extraKeys = [
            ["E", self.presenter.onExtract2DimsOverMZrangeMultiple, wx.ACCEL_ALT, ID_extractAllIons],
            ["Q", self.presenter.onOverlayMultipleIons, wx.ACCEL_ALT, ID_overlayMZfromList],
            ["W", self.presenter.onOverlayMultipleIons, wx.ACCEL_ALT, ID_overlayTextFromList],
            ["D", self.presenter.onAddBlankDocument, wx.ACCEL_ALT, ID_addNewOverlayDoc],
            ["S", self.panelDocuments.topP.documents.onShowPlot, wx.ACCEL_ALT, ID_showPlotDocument],
            ["F", self.presenter.onPickPeaks, wx.ACCEL_ALT, ID_pickMSpeaksDocument],
            ["P", self.panelDocuments.topP.documents.onProcess, wx.ACCEL_ALT, ID_process2DDocument],
            ["C", self.presenter.onCombineCEvoltagesMultiple, wx.ACCEL_ALT, ID_combineCEscans],
            ["R", self.panelDocuments.topP.documents.onRenameItem, wx.ACCEL_ALT, ID_renameItem],
            ["X", self.panelDocuments.topP.documents.onShowPlot, wx.ACCEL_ALT, ID_showPlotMSDocument],
            ["Z", self.presenter.onChangeChargeState, wx.ACCEL_ALT, ID_assignChargeState],
            ["V", self.panelDocuments.topP.documents.onSaveCSV, wx.ACCEL_ALT, ID_saveDataCSVDocument],
            ]
        
        for item in extraKeys:
            self.Bind(wx.EVT_MENU, item[1], id=item[3])
            ctrllist.append((item[2], ord(item[0]), item[3])) 

            
        self.SetAcceleratorTable(wx.AcceleratorTable(ctrllist))
        pass
    
    def onSetupMenu(self, evt):
    
        if self.config._windowSettings['Toolbar']['orientation'] == 'top': self.toolbar_top.Check(True)
        elif self.config._windowSettings['Toolbar']['orientation'] == 'bottom': self.toolbar_bottom.Check(True)
        elif self.config._windowSettings['Toolbar']['orientation'] == 'left': self.toolbar_left.Check(True)
        elif self.config._windowSettings['Toolbar']['orientation'] == 'right': self.toolbar_right.Check(True)

    def onToolbarPosition(self, evt):
        
        evtID = evt.GetId()
        # Try hiding
        try:
            self._mgr.GetPane(self.mainToolbar_vertical).Hide()
        except: pass
        
        try:
            self._mgr.GetPane(self.mainToolbar_horizontal).Hide()
        except:
            pass
        
        if evtID == ID_toolbar_top: self.config._windowSettings['Toolbar']['orientation'] = 'top'
        elif evtID == ID_toolbar_bottom: self.config._windowSettings['Toolbar']['orientation'] = 'bottom'
        elif evtID == ID_toolbar_left: self.config._windowSettings['Toolbar']['orientation'] = 'left'
        elif evtID == ID_toolbar_right: self.config._windowSettings['Toolbar']['orientation'] = 'right'
        
        if evtID in [ID_toolbar_top, ID_toolbar_bottom]:
            self.makeToolbar()
            try:
                self._mgr.AddPane(self.mainToolbar_horizontal, wx.aui.AuiPaneInfo().
                                  Name("Toolbar_horizontal").Caption("Toolbar_horizontal").ToolbarPane().Top()
                                  .Show(self.config._windowSettings['Toolbar']['show'])
                                  .Gripper(self.config._windowSettings['Toolbar']['show'])
                                  .LeftDockable(self.config._windowSettings['Toolbar']['left_dockable'])
                                  .RightDockable(self.config._windowSettings['Toolbar']['right_dockable'])
                                  .TopDockable(self.config._windowSettings['Toolbar']['top_dockable'])
                                  .BottomDockable(self.config._windowSettings['Toolbar']['bottom_dockable']))
            except:
                self._mgr.GetPane(self.mainToolbar_horizontal).Show()
                try:
                    self._mgr.GetPane(self.mainToolbar_vertical).Hide()
                except: pass
                
            if evtID == ID_toolbar_top:
                self._mgr.GetPane(self.mainToolbar_horizontal).Top()
            else: 
                self._mgr.GetPane(self.mainToolbar_horizontal).Bottom()

        elif evtID in [ID_toolbar_left, ID_toolbar_right]:
            self.makeToolbar()
            try:
                self._mgr.AddPane(self.mainToolbar_vertical, wx.aui.AuiPaneInfo().
                                  Name("Toolbar_vertical").Caption("Toolbar_vertical").ToolbarPane().Left().GripperTop()
                                  .Show(self.config._windowSettings['Toolbar']['show'])
                                  .Gripper(self.config._windowSettings['Toolbar']['show'])
                                  .LeftDockable(self.config._windowSettings['Toolbar']['left_dockable'])
                                  .RightDockable(self.config._windowSettings['Toolbar']['right_dockable'])
                                  .TopDockable(self.config._windowSettings['Toolbar']['top_dockable'])
                                  .BottomDockable(self.config._windowSettings['Toolbar']['bottom_dockable']))
            except:
                self._mgr.GetPane(self.mainToolbar_vertical).Show()
                try:
                    self._mgr.GetPane(self.mainToolbar_horizontal).Hide()
                except: pass
                
            if evtID == ID_toolbar_left: 
                self._mgr.GetPane(self.mainToolbar_vertical).Left()
            else: 
                self._mgr.GetPane(self.mainToolbar_vertical).Right()

        self._onToggleOnStart()
        self._mgr.Update()
        
    def makeToolbar(self):
        
        # Bind events
        self.Bind(wx.EVT_TOOL, self.presenter.onOrigamiRawDirectory, id=ID_openORIGAMIRawFile)
        self.Bind(wx.EVT_TOOL, self.presenter.on2DTextFile, id=ID_openIMStxtFile)
        self.Bind(wx.EVT_TOOL, self.presenter.onOrigamiRawDirectory, id=ID_openMassLynxRawFile)
                
        if self.config._windowSettings['Toolbar']['orientation'] in ['top', 'bottom']:
            style =  wx.TB_HORIZONTAL | wx.TB_DOCKABLE | wx.TB_NODIVIDER | wx.TB_FLAT 
            self.mainToolbar_horizontal = wx.ToolBar(self, -1, wx.DefaultPosition, wx.DefaultSize, style)
            self.mainToolbar_horizontal.SetToolBitmapSize(wx.Size(16,16))             
            self.mainToolbar_horizontal.AddTool(ID_openDocument, self.icons.iconsLib['open_project_16'], shortHelpString="Open project file")
            self.mainToolbar_horizontal.AddTool(ID_saveDocument, self.icons.iconsLib['save16'], shortHelpString="Save project file")
            self.mainToolbar_horizontal.AddSeparator()
            self.mainToolbar_horizontal.AddTool(ID_openORIGAMIRawFile, self.icons.iconsLib['open_origami_16'], shortHelpString="Open ORIGAMI MassLynx file")
            self.mainToolbar_horizontal.AddTool(ID_openORIGAMIRawFile, self.icons.iconsLib['open_masslynx_16'], shortHelpString="Open MassLynx file (IM-MS)")
            self.mainToolbar_horizontal.AddTool(ID_openMassLynxFiles, self.icons.iconsLib['open_masslynxMany_16'], shortHelpString="Open multiple MassLynx files")
            self.mainToolbar_horizontal.AddSeparator()
            self.mainToolbar_horizontal.AddTool(ID_openIMStxtFile, self.icons.iconsLib['open_text_16'], shortHelpString="Open text file")
            self.mainToolbar_horizontal.AddTool(ID_openTextFiles, self.icons.iconsLib['open_textMany_16'], shortHelpString="Open multiple text files")
            self.mainToolbar_horizontal.AddSeparator()
            self.mainToolbar_horizontal.AddCheckTool(ID_window_documentList, self.icons.iconsLib['panel_doc_16'], shortHelp="Enable/Disable documents panel")
            self.mainToolbar_horizontal.AddCheckTool(ID_window_ionList, self.icons.iconsLib['panel_ion_16'], shortHelp="Enable/Disable multi ion panel")
            self.mainToolbar_horizontal.AddCheckTool(ID_window_textList, self.icons.iconsLib['panel_text_16'], shortHelp="Enable/Disable multi text panel")
            self.mainToolbar_horizontal.AddCheckTool(ID_window_multipleMLList, self.icons.iconsLib['panel_mll__16'], shortHelp="Enable/Disable multi MassLynx panel")
            self.mainToolbar_horizontal.AddCheckTool(ID_window_multiFieldList, self.icons.iconsLib['panel_dt_16'], shortHelp="Enable/Disable linear DT panel")
            self.mainToolbar_horizontal.AddCheckTool(ID_window_ccsList, self.icons.iconsLib['panel_ccs_16'], shortHelp="Enable/Disable CCS calibration panel")
            self.mainToolbar_horizontal.AddCheckTool(ID_window_logWindow, self.icons.iconsLib['panel_log_16'], shortHelp="Enable/Disable Log panel")
            self.mainToolbar_horizontal.AddSeparator()
            self.mainToolbar_horizontal.AddTool(ID_extraSettings_plot1D, self.icons.iconsLib['panel_plot1D_16'], shortHelpString="Settings: Plot 1D panel")
            self.mainToolbar_horizontal.AddTool(ID_extraSettings_plot2D, self.icons.iconsLib['panel_plot2D_16'], shortHelpString="Settings: Plot 2D panel")
            self.mainToolbar_horizontal.AddTool(ID_extraSettings_plot3D, self.icons.iconsLib['panel_plot3D_16'], shortHelpString="Settings: Plot 3D panel")
            self.mainToolbar_horizontal.AddTool(ID_extraSettings_colorbar, self.icons.iconsLib['panel_colorbar_16'], shortHelpString="Settings: Colorbar panel")
            self.mainToolbar_horizontal.AddTool(ID_extraSettings_legend, self.icons.iconsLib['panel_legend_16'], shortHelpString="Settings: Legend panel")
            self.mainToolbar_horizontal.AddTool(ID_extraSettings_rmsd, self.icons.iconsLib['panel_rmsd_16'], shortHelpString="Settings: RMSD panel")
            self.mainToolbar_horizontal.AddTool(ID_extraSettings_waterfall, self.icons.iconsLib['panel_waterfall_16'], shortHelpString="Settings: Waterfall panel")
            self.mainToolbar_horizontal.AddTool(ID_extraSettings_general, self.icons.iconsLib['panel_general2_16'], shortHelpString="Settings: General panel")                    
            self.mainToolbar_horizontal.AddSeparator()
            self.mainToolbar_horizontal.AddTool(ID_processSettings_ExtractData, self.icons.iconsLib['process_extract_16'], shortHelpString="Settings: &Extract data\tShift+1")
            self.mainToolbar_horizontal.AddTool(ID_processSettings_ORIGAMI, self.icons.iconsLib['process_origami_16'], shortHelpString="Settings: &ORIGAMI\tShift+2")
            self.mainToolbar_horizontal.AddTool(ID_processSettings_MS, self.icons.iconsLib['process_ms_16'], shortHelpString="Settings: &Process mass spectra\tShift+3")
            self.mainToolbar_horizontal.AddTool(ID_processSettings_2D, self.icons.iconsLib['process_2d_16'], shortHelpString="Settings: Process &2D heatmaps\tShift+4")
            self.mainToolbar_horizontal.AddTool(ID_processSettings_FindPeaks, self.icons.iconsLib['process_fit_16'], shortHelpString="Settings: Peak &fitting\tShift+5")
            self.mainToolbar_horizontal.AddTool(ID_processSettings_UniDec, self.icons.iconsLib['process_unidec_16'], shortHelpString="Settings: &UniDec\tShift+6")
            ID_processSettings_UniDec
            self.mainToolbar_horizontal.AddSeparator()
            self.mainToolbar_horizontal.AddTool(ID_saveAsInteractive, self.icons.iconsLib['bokehLogo_16'], shortHelpString="Open interactive output panel")
            self.mainToolbar_horizontal.Realize()
        else:
            style =  wx.TB_VERTICAL | wx.TB_DOCKABLE | wx.TB_NODIVIDER | wx.TB_FLAT 
            self.mainToolbar_vertical = wx.ToolBar(self, -1, wx.DefaultPosition, wx.DefaultSize, style)
            self.mainToolbar_vertical.SetToolBitmapSize(wx.Size(16,16)) 
            self.mainToolbar_vertical.AddTool(ID_openDocument, self.icons.iconsLib['open_project_16'], shortHelpString="Open project file")
            self.mainToolbar_vertical.AddTool(ID_saveDocument, self.icons.iconsLib['save16'], shortHelpString="Save project file")
            self.mainToolbar_vertical.AddSeparator()
            self.mainToolbar_vertical.AddTool(ID_openORIGAMIRawFile, self.icons.iconsLib['open_origami_16'], shortHelpString="Open ORIGAMI MassLynx file")
            self.mainToolbar_vertical.AddTool(ID_openORIGAMIRawFile, self.icons.iconsLib['open_masslynx_16'], shortHelpString="Open MassLynx file")
            self.mainToolbar_vertical.AddTool(ID_openMassLynxFiles, self.icons.iconsLib['open_masslynxMany_16'], shortHelpString="Open multiple MassLynx files")
            self.mainToolbar_vertical.AddSeparator()
            self.mainToolbar_vertical.AddTool(ID_openIMStxtFile, self.icons.iconsLib['open_text_16'], shortHelpString="Open text file")
            self.mainToolbar_vertical.AddTool(ID_openTextFiles, self.icons.iconsLib['open_textMany_16'], shortHelpString="Open multiple text files")
            self.mainToolbar_vertical.AddSeparator()
            self.mainToolbar_vertical.AddCheckTool(ID_window_documentList, self.icons.iconsLib['panel_doc_16'], shortHelp="Enable/Disable documents panel")
            self.mainToolbar_vertical.AddCheckTool(ID_window_ionList, self.icons.iconsLib['panel_ion_16'], shortHelp="Enable/Disable multi ion panel")
            self.mainToolbar_vertical.AddCheckTool(ID_window_textList, self.icons.iconsLib['panel_text_16'], shortHelp="Enable/Disable multi text panel")
            self.mainToolbar_vertical.AddCheckTool(ID_window_multipleMLList, self.icons.iconsLib['panel_mll__16'], shortHelp="Enable/Disable multi MassLynx panel")
            self.mainToolbar_vertical.AddCheckTool(ID_window_multiFieldList, self.icons.iconsLib['panel_dt_16'], shortHelp="Enable/Disable linear DT panel")
            self.mainToolbar_vertical.AddCheckTool(ID_window_ccsList, self.icons.iconsLib['panel_ccs_16'], shortHelp="Enable/Disable CCS calibration panel")
            self.mainToolbar_vertical.AddCheckTool(ID_window_logWindow, self.icons.iconsLib['panel_log_16'], shortHelp="Enable/Disable Log panel")
            self.mainToolbar_vertical.AddSeparator()
            self.mainToolbar_vertical.AddTool(ID_extraSettings_plot1D, self.icons.iconsLib['panel_plot1D_16'], shortHelpString="Settings: Plot 1D panel")
            self.mainToolbar_vertical.AddTool(ID_extraSettings_plot2D, self.icons.iconsLib['panel_plot2D_16'], shortHelpString="Settings: Plot 2D panel")
            self.mainToolbar_vertical.AddTool(ID_extraSettings_plot3D, self.icons.iconsLib['panel_plot3D_16'], shortHelpString="Settings: Plot 3D panel")
            self.mainToolbar_vertical.AddTool(ID_extraSettings_colorbar, self.icons.iconsLib['panel_colorbar_16'], shortHelpString="Settings: Colorbar panel")
            self.mainToolbar_vertical.AddTool(ID_extraSettings_legend, self.icons.iconsLib['panel_legend_16'], shortHelpString="Settings: Legend panel")
            self.mainToolbar_vertical.AddTool(ID_extraSettings_rmsd, self.icons.iconsLib['panel_rmsd_16'], shortHelpString="Settings: RMSD panel")
            self.mainToolbar_vertical.AddTool(ID_extraSettings_waterfall, self.icons.iconsLib['panel_waterfall_16'], shortHelpString="Settings: Waterfall panel")
            self.mainToolbar_vertical.AddTool(ID_extraSettings_general, self.icons.iconsLib['panel_general2_16'], shortHelpString="Settings: General panel")
            self.mainToolbar_vertical.AddSeparator()
            self.mainToolbar_vertical.AddTool(ID_processSettings_ExtractData, self.icons.iconsLib['process_extract_16'], shortHelpString="Settings: &Extract data\tShift+1")
            self.mainToolbar_vertical.AddTool(ID_processSettings_ORIGAMI, self.icons.iconsLib['process_origami_16'], shortHelpString="Settings: &ORIGAMI\tShift+2")
            self.mainToolbar_vertical.AddTool(ID_processSettings_MS, self.icons.iconsLib['process_ms_16'], shortHelpString="Settings: &Process mass spectra\tShift+3")
            self.mainToolbar_vertical.AddTool(ID_processSettings_2D, self.icons.iconsLib['process_2d_16'], shortHelpString="Settings: Process &2D heatmaps\tShift+4")
            self.mainToolbar_vertical.AddTool(ID_processSettings_FindPeaks, self.icons.iconsLib['process_fit_16'], shortHelpString="Settings: Peak &fitting\tShift+5")
            self.mainToolbar_vertical.AddTool(ID_processSettings_UniDec, self.icons.iconsLib['process_unidec_16'], shortHelpString="Settings: &UniDec\tShift+6")
            self.mainToolbar_vertical.AddSeparator()
            self.mainToolbar_vertical.AddTool(ID_saveAsInteractive, self.icons.iconsLib['bokehLogo_16'], shortHelpString="Open interactive output panel")
            self.mainToolbar_vertical.Realize()
        
    def saveFigures(self, e=None, fileExt=None, fileMod=None):
        """
        This function saves all figures in specified size with appropriate arguments
        and keywords
        """
        
         # Find the current document and determine its path
        self.currentDoc = self.panelDocuments.topP.documents.enableCurrentDocument()
        if self.currentDoc == 'Current documents': return     
        self.docs = self.presenter.documentsDict[self.currentDoc]
        figureDirectory = self.docs.path
        if figureDirectory == None or figureDirectory == '':
            print('Sorry, cannot find place to save figures.') 
            return
        if fileExt == None:
            fileExt = "png"
        
        # In case we would like to save as with a modified name
        if fileMod == None:
            fileMod = "\\" 
        else:
            fileMod = ''.join(["\\", fileMod])
            
        print(figureDirectory, fileExt, fileMod)
        
        tstart = clock()
        fileSaveName = ''.join([figureDirectory, fileMod, "Figure_MS.", fileExt])
        if self.panelPlots.plot1.plotflag == True:
            print(fileSaveName)
            self.panelPlots.plot1.saveFigure(path=fileSaveName, transparent=self.config.transparent,
                                              dpi=self.config.dpi)
            
        fileSaveName = ''.join([figureDirectory, fileMod, "Figure_RT.", fileExt])
        if self.panelPlots.plotRT.plotflag == True:
            print(fileSaveName)
            self.panelPlots.plotRT.saveFigure(path=fileSaveName, transparent=self.config.transparent,
                                              dpi=self.config.dpi)
            
        fileSaveName = ''.join([figureDirectory, fileMod, "Figure_1D.", fileExt])
        if self.panelPlots.plot1D.plotflag == True:
            print(fileSaveName)
            self.panelPlots.plot1D.saveFigure(path=fileSaveName, transparent=self.config.transparent,
                                              dpi=self.config.dpi)
            
        fileSaveName = ''.join([figureDirectory, fileMod, "Figure_2D.", fileExt])
        if self.panelPlots.plot2D.plotflag == True:
            print(fileSaveName)
            self.panelPlots.plot2D.saveFigure(path=fileSaveName, transparent=self.config.transparent,
                                              dpi=self.config.dpi)
            
        fileSaveName = ''.join([figureDirectory, fileMod, "Figure_WATERFALL.", fileExt])
        if self.panelPlots.plotWaterfallIMS.plotflag == True:
            print(fileSaveName)
            self.panelPlots.plotWaterfallIMS.saveFigure(path=fileSaveName, transparent=self.config.transparent,
                                                         dpi=self.config.dpi)
            
        fileSaveName = ''.join([figureDirectory, fileMod, "Figure_3D.", fileExt])
        if self.panelPlots.plot3D.plotflag == True:
            print(fileSaveName)
            self.panelPlots.plot3D.saveFigure(path=fileSaveName, transparent=self.config.transparent,
                                              dpi=self.config.dpi)
            
        fileSaveName = ''.join([figureDirectory, fileMod, "Figure_RMSD.", fileExt])
        if self.panelPlots.plotRMSD.plotflag == True:
            print(fileSaveName)
            self.panelPlots.plotRMSD.saveFigure(path=fileSaveName, transparent=self.config.transparent,
                                                 dpi=self.config.dpi)
                
        fileSaveName = ''.join([figureDirectory, fileMod, "Figure_MATRIX.", fileExt])
        if self.panelPlots.plotCompare.plotflag == True:
            print(fileSaveName)
            self.panelPlots.plotCompare.saveFigure(path=fileSaveName, transparent=self.config.transparent,
                                                    dpi=self.config.dpi)

        fileSaveName = ''.join([figureDirectory, fileMod, "Figure_RMSFD.", fileExt])
        if self.panelPlots.plotRMSF.plotflag == True:
            print(fileSaveName)
            self.panelPlots.plotRMSF.saveFigure(path=fileSaveName, transparent=self.config.transparent,
                                                 dpi=self.config.dpi)
        # Overlay methods 
        if self.config.textOverlayMethod == "Transparent" or self.config.overlayMethod == "Transparent":
            fileSaveName = ''.join([figureDirectory, fileMod, "Figure_OVERLAY_TRANSPARENT.", fileExt])
        elif self.config.textOverlayMethod == "Mask" or self.config.overlayMethod == "Mask":
            fileSaveName = ''.join([figureDirectory, fileMod, "Figure_OVERLAY_MASK.", fileExt])
        else:
            fileSaveName = ''.join([figureDirectory, fileMod, "Figure_OVERLAY_IONS.", fileExt])

        if self.panelPlots.plotOverlay.plotflag == True:
            print(fileSaveName)
            self.panelPlots.plotOverlay.saveFigure(path=fileSaveName, transparent=self.config.transparent,
                                                 dpi=self.config.dpi)
        
        tend = clock()
        print('Finished saving figures in %s with %s extension. It took %2gs' % (figureDirectory, fileExt, (tend-tstart)))
        
    def checkIfWindowsAreShown(self, evt):
        """ Check which windows are currently shown in the GUI"""
        
        if not self.panelDocuments.IsShown(): self.documentsPage.Check(False)
        if not self.panelMultipleIons.IsShown(): self.mzTable.Check(False)
        if not self.panelLinearDT.IsShown(): self.multifieldTable.Check(False)
        if not self.panelMultipleText.IsShown(): self.textTable.Check(False)
        if not self.panelMML.IsShown(): self.multipleMLTable.Check(False)
#         if not self.panelControls.IsShown(): self.settingsPage.Check(False)
        if not self.panelCCS.IsShown(): self.ccsTable.Check(False)
        
        if evt != None:
            evt.Skip()
     
    def onPaneOnOff(self, evt, check=None):
        
        if isinstance(evt, int):
            evtID = evt
        elif evt != None:
            evtID = evt.GetId()
        else:
            evtID = None        
            
        if evtID != None:
            if evtID == ID_window_documentList:
                if not self.panelDocuments.IsShown():
                    self._mgr.GetPane(self.panelDocuments).Show()
                    self.config._windowSettings['Documents']['show'] = True
                else:
                    self._mgr.GetPane(self.panelDocuments).Hide()
                    self.config._windowSettings['Documents']['show'] = False
                self.documentsPage.Check(self.config._windowSettings['Documents']['show'])
                self.onFindToggleBy_ID(find_id=evtID, check=self.config._windowSettings['Documents']['show'])
            elif evtID == ID_window_ccsList:
                if not self.panelCCS.IsShown() or check:
                    self._mgr.GetPane(self.panelCCS).Show()
                    self.config._windowSettings['CCS calibration']['show'] = True
                else:
                    self._mgr.GetPane(self.panelCCS).Hide()
                    self.config._windowSettings['CCS calibration']['show'] = False
                self.ccsTable.Check(self.config._windowSettings['CCS calibration']['show'])
                self.onFindToggleBy_ID(find_id=evtID, check=self.config._windowSettings['CCS calibration']['show'])
            elif evtID == ID_window_ionList:
                if not self.panelMultipleIons.IsShown() or check:
                    self._mgr.GetPane(self.panelMultipleIons).Show()
                    self.config._windowSettings['Peak list']['show'] = True
                else:
                    self._mgr.GetPane(self.panelMultipleIons).Hide()
                    self.config._windowSettings['Peak list']['show'] = False
                self.mzTable.Check(self.config._windowSettings['Peak list']['show'])
                self.onFindToggleBy_ID(find_id=evtID, check=self.config._windowSettings['Peak list']['show'])
            elif evtID == ID_window_multipleMLList:
                if not self.panelMML.IsShown() or check:
                    self._mgr.GetPane(self.panelMML).Show()
                    self.config._windowSettings['Multiple files']['show'] = True
                else:
                    self._mgr.GetPane(self.panelMML).Hide()
                    self.config._windowSettings['Multiple files']['show'] = False
                self.multipleMLTable.Check(self.config._windowSettings['Multiple files']['show'])
                self.onFindToggleBy_ID(find_id=evtID, check=self.config._windowSettings['Multiple files']['show'])
            elif evtID == ID_window_textList:
                if not self.panelMultipleText.IsShown() or check:
                    self._mgr.GetPane(self.panelMultipleText).Show()
                    self.config._windowSettings['Text files']['show'] = True
                else:
                    self._mgr.GetPane(self.panelMultipleText).Hide()
                    self.config._windowSettings['Text files']['show'] = False
                self.textTable.Check(self.config._windowSettings['Text files']['show'])
                self.onFindToggleBy_ID(find_id=evtID, check=self.config._windowSettings['Text files']['show'])
            elif evtID == ID_window_multiFieldList:
                if not self.panelLinearDT.IsShown() or check:
                    self._mgr.GetPane(self.panelLinearDT).Show()
                    self.config._windowSettings['Linear Drift Cell']['show'] = True
                else:
                    self._mgr.GetPane(self.panelLinearDT).Hide()
                    self.config._windowSettings['Linear Drift Cell']['show'] = False
                self.multifieldTable.Check(self.config._windowSettings['Linear Drift Cell']['show'])
                self.onFindToggleBy_ID(find_id=evtID, check=self.config._windowSettings['Linear Drift Cell']['show'])
            elif evtID == ID_window_logWindow:
                if not self.panelLog.IsShown():
                    self.panelLog.Show()
                    self._mgr.GetPane(self.panelLog).Show()
                    self.config._windowSettings['Log']['show'] = True
                else:
                    self._mgr.GetPane(self.panelLog).Hide()
                    self.panelLog.Hide()
                    self.config._windowSettings['Log']['show'] = False
                self.window_logWindow.Check(self.config._windowSettings['Log']['show'])
                self.onFindToggleBy_ID(find_id=evtID, check=self.config._windowSettings['Log']['show'])
            elif evtID == ID_window_all:
                for key in self.config._windowSettings:
                    self.config._windowSettings[key]['show'] = True
                
                self.onFindToggleBy_ID(check_all=True)
                    
                for panel in [self.panelDocuments, 
#                               self.panelControls, 
                              self.panelMML,
                              self.panelMultipleIons, self.panelMultipleText,
                              self.panelCCS, self.panelLinearDT]:
                    self._mgr.GetPane(panel).Show()
                    
                self.documentsPage.Check(self.config._windowSettings['Documents']['show']) 
                self.mzTable.Check(self.config._windowSettings['Peak list']['show'])  
                self.ccsTable.Check(self.config._windowSettings['CCS calibration']['show'])
                self.multifieldTable.Check(self.config._windowSettings['Linear Drift Cell']['show'])
                self.textTable.Check(self.config._windowSettings['Text files']['show'])
                self.multipleMLTable.Check(self.config._windowSettings['Multiple files']['show'])
                self.window_logWindow.Check(self.config._windowSettings['Log']['show'])
        # Checking at start of program
        else:
            if not self.panelDocuments.IsShown(): self.config._windowSettings['Documents']['show'] = False
            if not self.panelMML.IsShown(): self.config._windowSettings['Multiple files']['show'] = False
            if not self.panelMultipleIons.IsShown(): self.config._windowSettings['Peak list']['show'] = False
            if not self.panelCCS.IsShown(): self.config._windowSettings['CCS calibration']['show'] = False
            if not self.panelLinearDT.IsShown(): self.config._windowSettings['Linear Drift Cell']['show'] = False
            if not self.panelMultipleText.IsShown(): self.config._windowSettings['Text files']['show'] = False
            if not self.panelLog.IsShown(): self.config._windowSettings['Log']['show'] = False   
            
            self.documentsPage.Check(self.config._windowSettings['Documents']['show']) 
#             self.settingsPage.Check(self.config._windowSettings['Controls']['show'])
            self.mzTable.Check(self.config._windowSettings['Peak list']['show'])  
            self.ccsTable.Check(self.config._windowSettings['CCS calibration']['show'])
            self.multifieldTable.Check(self.config._windowSettings['Linear Drift Cell']['show'])
            self.textTable.Check(self.config._windowSettings['Text files']['show'])
            self.multipleMLTable.Check(self.config._windowSettings['Multiple files']['show'])
            self.window_logWindow.Check(self.config._windowSettings['Log']['show'])
        
        self._mgr.Update()
        
    def onFindToggleBy_ID(self, find_id=None, check=None, check_all=False):
        """
        Find toggle item by id in either horizontal/vertiacal toolbar
        """
        
        idList = [ID_window_documentList, ID_window_controls, ID_window_ccsList,
                  ID_window_ionList, ID_window_multipleMLList, ID_window_textList,
                  ID_window_multiFieldList]
        if self.config._windowSettings['Toolbar']['orientation'] in ['top', 'bottom']:
            for itemID in idList:
                if check_all:
                     self.mainToolbar_horizontal.ToggleTool(id=itemID, toggle=True)
                elif itemID == find_id: 
                    self.mainToolbar_horizontal.ToggleTool(id=find_id, toggle=check)
            if find_id == ID_window_all:
                self.mainToolbar_horizontal.ToggleTool(id=id, toggle=True)
                
        else:
            for itemID in idList: 
                if check_all:
                     self.mainToolbar_vertical.ToggleTool(id=itemID, toggle=True)
                elif itemID == find_id: 
                    self.mainToolbar_vertical.ToggleTool(id=find_id, toggle=check)
            if find_id == ID_window_all:
                self.mainToolbar_vertical.ToggleTool(id=id, toggle=True)
    
    def onCheckToggleID(self, panel):
        panelDict = {'Documents':ID_window_documentList,
                     'Controls':ID_window_controls, 
                     'Multiple files':ID_window_multipleMLList,
                     'Peak list':ID_window_ionList, 
                     'Text files':ID_window_textList,
                     'CCS calibration':ID_window_ccsList, 
                     'Linear Drift Cell':ID_window_multiFieldList,
                     'Log':ID_window_logWindow}
        return panelDict[panel]
                
    def OnClose(self, event):
        
        if len(self.presenter.documentsDict) > 0:
            if len(self.presenter.documentsDict) == 1: verb_form = "is"
            else: verb_form = "are"
            message = "There {} {} document(s) open.\n".format(verb_form, len(self.presenter.documentsDict)) + \
                     "Are you sure you want to continue?"
            msgDialog = panelNotifyOpenDocuments(self, self.presenter, message)
            dlg = msgDialog.ShowModal()
                  
#             dlg = dialogs.dlgBox(exceptionTitle='Are you sure?', 
#                                  exceptionMsg= msg,
#                                  type="Question")
            if dlg == wx.ID_NO:
                print('Cancelled operation')
                return
        
        # Try saving configuration file
        try:
            path = os.path.join(self.config.cwd, 'configOut.xml')
            self.config.saveConfigXML(path=path, evt=None)
        except: 
            print("Could not save configuration file")
            pass
        
        # Try unsubscribing events
        try:
            self.publisherOff()
        except: 
            print("Could not disable publisher")
            pass
        
        # Try killing window manager
        try:
            self._mgr.UnInit()
        except: 
            print("Could not uninitilize window manager")
            pass
        
        # Clear-up dictionary
        try:
            for title in self.presenter.documentsDict:
                del self.presenter.documentsDict[title]
                print("Deleted {}".format(title))
        except:
            pass
        
        # Aggressive way to kill the ORIGAMI process (grrr)
        try:
            p = psutil.Process(self.config._processID)
            p.terminate()
        except:
            pass
        
        self.Destroy()
        
    def OnDistance(self, startX):
        # Simple way of setting the start point
        self.startX = startX
        pass
        
    def OnMotion(self, xpos, ypos, plotname):
        """
        Triggered by pubsub from plot windows. Reports text in Status Bar.
        :param xpos: x position fed from event
        :param ypos: y position fed from event
        :return: None
        """
        if xpos is not None and ypos is not None:
            # If measuring distance, additional fields are used to help user 
            # make observations
            if self.startX is not None:
                range = absolute(self.startX - xpos)
                charge = round(1.0/range,1)
                mass = (xpos+charge)*charge
                # If inside a plot area with MS, give out charge state
                if self.mode == 'Measure' and self.panelPlots.currentPage in ["MS",  "DT/MS"]:
                    self.SetStatusText(u"m/z=%.2f int=%.2f Δm/z=%.2f z=%.1f mw=%.1f" % (xpos, ypos, range, charge, mass), number=0)
                else:
                    if self.panelPlots.currentPage in ['MS']:
                        self.SetStatusText(u"m/z=%.2f int=%.2f Δm/z=%.2f" % (xpos, ypos, range), number=0)
                    elif  self.panelPlots.currentPage in ['DT/MS']:
                        self.SetStatusText(u"m/z=%.2f dt=%.2f Δm/z=%.2f" % (xpos, ypos, range), number=0)
                    elif self.panelPlots.currentPage in ['RT']:
                        self.SetStatusText(u"scan=%.0f int=%.2f Δscans=%.2f" % (xpos, ypos, range), number=0)
                    elif self.panelPlots.currentPage in ['1D']:
                        self.SetStatusText(u"dt=%.2f int=%.2f Δdt=%.2f" % (xpos, ypos, range), number=0)
                    elif self.panelPlots.currentPage in ['2D']:
                        self.SetStatusText(u"x=%.2f dt=%.2f Δx=%.2f" % (xpos, ypos, range), number=0)
                    else:
                        self.SetStatusText(u"x=%.2f y=%.2f Δx=%.2f" % (xpos, ypos, range), number=0)
            else:
                if self.panelPlots.currentPage in ['MS']:
                    self.SetStatusText("m/z=%.2f int=%.2f" % (xpos, ypos), number=0)
                elif  self.panelPlots.currentPage in ['DT/MS']:
                    if self.plot_data['DT/MS'] is not None and len(self.plot_scale['DT/MS']) == 2:
                        try:
                            yIdx = int(ypos*self.plot_scale['DT/MS'][0])-1
                            xIdx = int(xpos*self.plot_scale['DT/MS'][1])-1
                            int_value = self.plot_data['DT/MS'][yIdx, xIdx]
                        except:
                            int_value = 0.
                        self.SetStatusText("m/z={:.2f} dt={:.2f} int={:.2f}".format(xpos, ypos, int_value), number=0)
                    else:
                        self.SetStatusText("m/z=%.2f dt=%.2f" % (xpos, ypos), number=0)
                elif self.panelPlots.currentPage in ['RT']:
                    self.SetStatusText("scan=%.0f int=%.2f" % (xpos, ypos), number=0)
                elif self.panelPlots.currentPage in ['1D']:
                    self.SetStatusText("dt=%.2f int=%.2f" % (xpos, ypos), number=0)
                elif self.panelPlots.currentPage in ['2D']:
                    try:
                        if self.plot_data['2D'] is not None and len(self.plot_scale['2D']) == 2:
                            try:
                                yIdx = int(ypos*self.plot_scale['2D'][0])-1
                                xIdx = int(xpos*self.plot_scale['2D'][1])-1
                                int_value = self.plot_data['2D'][yIdx, xIdx]
                            except:
                                int_value = ""
                            self.SetStatusText("x=%.2f dt=%.2f int=%.2f" % (xpos, ypos, int_value), number=0)
                        else:
                            self.SetStatusText("x=%.2f dt=%.2f" % (xpos, ypos), number=0)
                    except:
                        self.SetStatusText("x=%.2f dt=%.2f" % (xpos, ypos), number=0)
                elif plotname == "zGrid":
                    self.SetStatusText("x=%.2f charge=%.0f" % (xpos, ypos), number=0)
                elif plotname == "mwDistribution":
                    self.SetStatusText("MW=%.2f intensity=%.2f" % (xpos, ypos), number=0)
                else:
                    self.SetStatusText("x=%.2f y=%.2f" % (xpos, ypos), number=0)
                    
        pass
    
    def OnMotionRange(self, dataOut):
        minx,maxx,miny,maxy = dataOut
        if self.mode == 'Add data':
            self.SetStatusText("Range X=%.2f-%.2f Y=%.2f-%.2f" % (minx,maxx,miny,maxy), number=4)
        else:
            self.SetStatusText("", number=4)
    
    def OnSize(self, event):
        self.resized = True # set dirty

    def OnIdle(self, event):
        if self.resized: 
            # take action if the dirty flag is set
            self.resized = False # reset the flag
             
    def getYvalue(self, msList, mzStart, mzEnd):
        """
        This helper function determines the maximum value of X-axis
        """
        msList = getNarrow1Ddata(data=msList, mzRange=(mzStart,mzEnd))
        mzYMax = round(findPeakMax(data=msList)*100, 1)
        return mzYMax
             
    def Add2TableMSDT(self, dataOut):
        xmin, xmax, ymin, ymax = dataOut
        if xmin == None or xmax == None or ymin == None or ymax == None:
            self.SetStatusText("Extraction range was from outside of the plot area. Try again", number=4)
            return
        xmin = round(xmin, 2)
        xmax = round(xmax, 2)
        ymin = int(round(ymin, 0))
        ymax = int(round(ymax, 0))
        
        # Reverse values if they are in the wrong order
        if xmax < xmin: xmax, xmin = xmin, xmax
        if ymax < ymin: ymax, ymin = ymin, ymax

        # Extract data
        self.presenter.onExtractRTforMZDTrange(xmin, xmax, ymin, ymax)
        self.SetStatusText("", number=4)
          
    def Add2Table(self, xvalsMin, xvalsMax, yvalsMax, currentView=None, currentDoc=""):
        self.currentPage = self.panelPlots.mainBook.GetPageText(self.panelPlots.mainBook.GetSelection())
        self.SetStatusText("", number=4)
        
        # get current document
        if currentDoc == "": currentDoc = self.presenter.currentDoc
            
        currentDocument = self.presenter.view.panelDocuments.topP.documents.enableCurrentDocument()
        if currentDocument == "Current documents":
            return
        
        document = self.presenter.documentsDict[currentDocument]
        
        if self.currentPage in ['RT', 'MS', '1D', '2D'] and document.dataType == 'Type: Interactive':
            args = ("Cannot extract data from Interactive document", 4)
            self.presenter.onThreading(None, args, action='updateStatusbar')
            return
        elif self.currentPage == '1D':
            if xvalsMin == None or xvalsMax == None: 
                args = ('Your extraction range was outside the window. Please try again', 4)
                self.presenter.onThreading(None, args, action='updateStatusbar')
                return
            dtStart = ceil(xvalsMin).astype(int)
            dtEnd = floor(xvalsMax).astype(int)
            # Check that values are in correct order
            if dtEnd < dtStart: dtEnd, dtStart = dtStart, dtEnd
            
            self.presenter.onExtractMSforDTrange(dtStart=dtStart, dtEnd=dtEnd)
            
        elif self.currentPage == "MS" or currentView == "MS":
            if xvalsMin == None or xvalsMax == None: 
                self.SetStatusText('Your extraction range was outside the window. Please try again',3)
                return
            mzStart = round(xvalsMin,2)
            mzEnd = round(xvalsMax,2)
            
            mzYMax = round(yvalsMax*100,1)
            # Check that values are in correct order
            if mzEnd < mzStart: mzEnd, mzStart = mzStart, mzEnd
            
            # Make sure the document has MS in first place (i.e. Text)
            if not self.presenter.documentsDict[currentDoc].gotMS: 
                return
            # Get MS data for specified region and extract Y-axis maximum
            ms = self.presenter.documentsDict[currentDoc].massSpectrum
#             ms = flipud(rot90(array([ms['xvals'], ms['yvals']])))
            ms = np.transpose([ms['xvals'], ms['yvals']])
            mzYMax = self.getYvalue(msList=ms, mzStart=mzStart, mzEnd=mzEnd)

            # predict charge state
            mzNarrow = getNarrow1Ddata(data=ms, mzRange=(mzStart, mzEnd))
            highResPeaks = detectPeaks1D(data=mzNarrow, 
                                         window=self.config.fit_highRes_window, 
                                         threshold=self.config.fit_highRes_threshold)
            peakDiffs = np.diff(highResPeaks[:,0])
            peakStd = np.std(peakDiffs)
            if len(peakDiffs) > 0 and peakStd <= 0.05: 
                charge = int(np.round(1/np.round(np.average(peakDiffs),4),0))
                print("Predicted charge state:{} | Standard deviation: {}".format(charge, peakStd))
            else:
                print("Failed to predict charge state. Standard deviation: {}".format(peakStd))
                charge = ""
                
            color = convertRGB255to1(self.config.customColors[randomIntegerGenerator(0,15)])
            if (document.dataType == 'Type: ORIGAMI' or 
                document.dataType == 'Type: MANUAL' or 
                document.dataType == 'Type: Infrared'):
                self.onPaneOnOff(evt=ID_window_ionList, check=True)
                # Check if value already present
                outcome = self.panelMultipleIons.topP.onCheckForDuplicates(mzStart=str(mzStart), 
                                                                           mzEnd=str(mzEnd))
                if outcome:
                    self.SetStatusText('Selected range already in the table',3)
                    if currentView == "MS":
                        return outcome
                    return
                self.panelMultipleIons.topP.peaklist.Append([mzStart,mzEnd, charge, mzYMax, color,
                                                             self.config.overlay_cmaps[randomIntegerGenerator(0,5)],
                                                             self.config.overlay_defaultMask,
                                                             self.config.overlay_defaultAlpha, 
                                                             "", "", currentDoc])
                self.panelMultipleIons.topP.peaklist.SetItemBackgroundColour(self.panelMultipleIons.topP.peaklist.GetItemCount()-1, 
                                                                             convertRGB1to255(color))
                if self.config.showRectanges:
                    self.presenter.addRectMS(mzStart, 0, (mzEnd-mzStart), 1.0, color=color, 
                                   alpha=(self.config.markerTransparency_1D),
                                   repaint=True)
            elif document.dataType == 'Type: Multifield Linear DT':
                self._mgr.GetPane(self.panelLinearDT).Show()
                self.multifieldTable.Check(True)
                self._mgr.Update()
                # Check if value already present
                outcome = self.panelLinearDT.bottomP.onCheckForDuplicates(mzStart=str(mzStart), 
                                                                           mzEnd=str(mzEnd))
                if outcome: return
                self.panelLinearDT.bottomP.peaklist.Append([mzStart, mzEnd,
                                                            mzYMax, "",
                                                            self.presenter.currentDoc])
                if self.config.showRectanges:
                    self.presenter.addRectMS(mzStart, 0, (mzEnd-mzStart), 1.0,
                                             color=self.config.annotColor, 
                                             alpha=(self.config.annotTransparency/100),
                                             repaint=True)
                
        if self.currentPage == "Calibration":
            # Check whether the current document is of correct type!
            if (document.fileFormat != 'Format: MassLynx (.raw)' or document.dataType != 'Type: CALIBRANT'): 
                print('Please select the correct document file in document window!')
                return
            mzVal = round((xvalsMax+xvalsMin)/2,2)
            # prevents extraction if value is below 50. This assumes (wrongly!)
            # that the m/z range will never be below 50.
            if xvalsMax < 50:  
                self.SetStatusText('Make sure you are extracting in the MS window.',3)
                return
            # Check if value already present
            outcome = self.panelCCS.topP.onCheckForDuplicates(mzCentre=str(mzVal))
            if outcome == True: return
            self._mgr.GetPane(self.panelCCS).Show()
            self.ccsTable.Check(True)
            self._mgr.Update()
            if yvalsMax<=1:
                tD = self.presenter.onAddCalibrant(path=document.path,
                                                   mzCentre=mzVal,
                                                   mzStart=round(xvalsMin,2),
                                                   mzEnd=round(xvalsMax,2), 
                                                   pusherFreq=document.parameters['pusherFreq'],
                                                   tDout=True)
                
                self.panelCCS.topP.peaklist.Append([currentDocument,
                                                    round(xvalsMin,2),
                                                    round(xvalsMax,2),
                                                    "","","",str(tD)])
                if self.config.showRectanges:
                    self.presenter.addRectMS(xvalsMin, 0, (xvalsMax-xvalsMin), 1.0, 
                                   color=self.config.annotColor, 
                                   alpha=(self.config.annotTransparency/100),
                                   repaint=True, plot='CalibrationMS')
            
                
        elif self.currentPage == "RT" and document.dataType == 'Type: Multifield Linear DT': 
            self._mgr.GetPane(self.panelLinearDT).Show()
            self.multifieldTable.Check(True)
            self._mgr.Update()
            xvalsMin = ceil(xvalsMin).astype(int)
            xvalsMax = floor(xvalsMax).astype(int)
            # Check that values are in correct order
            if xvalsMax < xvalsMin: xvalsMax, xvalsMin = xvalsMin, xvalsMax
            
            # Check if value already present
            outcome = self.panelLinearDT.topP.onCheckForDuplicates(rtStart=str(xvalsMin), 
                                                                   rtEnd=str(xvalsMax))
            if outcome == True: return
            xvalDiff = xvalsMax-xvalsMin.astype(int)
            self.panelLinearDT.topP.peaklist.Append([xvalsMin, xvalsMax,
                                                     xvalDiff, "",
                                                     self.presenter.currentDoc])
            
            self.presenter.addRectRT(xvalsMin, 0, (xvalsMax-xvalsMin), 1.0, 
                           color=self.config.annotColor, 
                           alpha=(self.config.annotTransparency/100),
                           repaint=True)
        elif self.currentPage == 'RT' and document.dataType != 'Type: Multifield Linear DT': 
            # Get values
            if xvalsMin == None or xvalsMax == None:
                self.SetStatusText("Extraction range was from outside of the plot area. Try again", number=4)
                return
            xvalsMin = ceil(xvalsMin).astype(int)
            xvalsMax = floor(xvalsMax).astype(int)
            # Check that values are in correct order
            if xvalsMax < xvalsMin: xvalsMax, xvalsMin = xvalsMin, xvalsMax

            # Check if difference between the two values is large enough
            if (xvalsMax - xvalsMin) < 1:
                self.SetStatusText('The scan range you selected was too small. Please choose wider range', 3)
                return
            # Extract data
            self.presenter.onExtractMSforRTrange(startScan=xvalsMin, 
                                                 endScan=xvalsMax)
            
        else:
            return

    def onPlotParameters(self, evt):
        if evt.GetId() == ID_extraSettings_colorbar: kwargs = {'window':'Colorbar'}
        elif evt.GetId() == ID_extraSettings_legend: kwargs = {'window':'Legend'}
        elif evt.GetId() == ID_extraSettings_plot1D: kwargs = {'window':'Plot 1D'}
        elif evt.GetId() == ID_extraSettings_plot2D: kwargs = {'window':'Plot 2D'}
        elif evt.GetId() == ID_extraSettings_plot3D: kwargs = {'window':'Plot 3D'}
        elif evt.GetId() == ID_extraSettings_rmsd: kwargs = {'window':'RMSD'}
        elif evt.GetId() == ID_extraSettings_waterfall: kwargs = {'window':'Waterfall'}
        elif evt.GetId() == ID_extraSettings_general: kwargs = {'window':'General'}
        
        if self.config.extraParamsWindow_on_off:
            args = ("An instance of this panel is already open - changing page to: %s" % kwargs['window'], 4)
            self.presenter.onThreading(evt, args, action='updateStatusbar')
            self.panelParametersEdit.onSetPage(**kwargs)
            return
        
        self.SetStatusText("", 4)
        
        
        try:
            self.config.extraParamsWindow_on_off = True
            self.panelParametersEdit = panelParametersEdit(self, 
                                                           self.presenter,
                                                           self.config, 
                                                           self.icons, 
                                                           **kwargs)
            self.panelParametersEdit.Show()
        except (ValueError, AttributeError, TypeError, KeyError), e:
            self.config.extraParamsWindow_on_off = False
            dialogs.dlgBox(exceptionTitle='Failed to open panel', 
                           exceptionMsg= str(e),
                           type="Error")
            return

    def onProcessParameters(self, evt, **pKwargs):
        
        # get evt id
        if isinstance(evt, int):
            evtID = evt
        else:
            evtID = evt.GetId()
        
        if evtID == ID_processSettings_ExtractData: 
            kwargs = {'window':'Extract'}
        elif evtID == ID_processSettings_MS: 
            kwargs = {'window':'MS'}
        elif evtID == ID_processSettings_2D: 
            kwargs = {'window':'2D'}
        elif evtID == ID_processSettings_ORIGAMI: 
            kwargs = {'window':'ORIGAMI'}
        elif evtID == ID_processSettings_FindPeaks: 
            kwargs = {'window':'Peak fitting'}
        elif evtID == ID_processSettings_UniDec: 
            kwargs = {'window':'UniDec'}
            
        kwargs['processKwargs'] = pKwargs
          
        if self.config.processParamsWindow_on_off:
            args = ("An instance of this panel is already open - changing page to: %s" % kwargs['window'], 4)
            self.presenter.onThreading(evt, args, action='updateStatusbar')
            self.panelProcessData.onSetPage(**kwargs)
            return
        self.SetStatusText("", 4)
          
        try:
            self.config.processParamsWindow_on_off = True
            self.panelProcessData = panelProcessData(self, 
                                                     self.presenter,
                                                     self.config, 
                                                     self.icons,
                                                     **kwargs)
            self.panelProcessData.Show()
        except (ValueError, AttributeError, TypeError, KeyError, wx._core.PyAssertionError), e:
            self.config.processParamsWindow_on_off = False
            dialogs.dlgBox(exceptionTitle='Failed to open panel', 
                           exceptionMsg= str(e),
                           type="Error")
            return

    def onExportParameters(self, evt):
        if evt.GetId() == ID_importExportSettings_image: kwargs = {'window':'Image'}
        elif evt.GetId() == ID_importExportSettings_file: kwargs = {'window':'Files'}
        elif evt.GetId() == ID_importExportSettings_peaklist: kwargs = {'window':'Peaklist'}
        
        if self.config.importExportParamsWindow_on_off:
            args = ("An instance of this panel is already open - changing page to: %s" % kwargs['window'], 4)
            self.presenter.onThreading(evt, args, action='updateStatusbar')
            self.panelImportExportParameters.onSetPage(**kwargs)
            return
         
        self.SetStatusText("", 4)
        
        
        try:
            self.config.importExportParamsWindow_on_off = True
            self.panelImportExportParameters = panelExportSettings(self, 
                                                             self.presenter,
                                                             self.config, 
                                                             self.icons, 
                                                             **kwargs)
            self.panelImportExportParameters.Show()
        except (ValueError, AttributeError, TypeError, KeyError), e:
            self.config.importExportParamsWindow_on_off = False
            dialogs.dlgBox(exceptionTitle='Failed to open panel', 
                           exceptionMsg= str(e),
                           type="Error")
            return

    def onSequenceEditor(self, evt):
        
        self.panelSequenceAnalysis = panelSequenceAnalysis(self, 
                                                                 self.presenter,
                                                                 self.config, 
                                                                 self.icons)
        self.panelSequenceAnalysis.Show()

    def openSaveAsDlg(self, evt):
        
#         if self.config.interactiveParamsWindow_on_off:
#             args = ("An instance of this panel is already open", 4)
#             self.presenter.onThreading(evt, args, action='updateStatusbar')
#             return
#         
#         try:
#             self.config.interactiveParamsWindow_on_off = True
        dlg = panelInteractive(self, self.icons, self.presenter, self.config)
        dlg.Show()
#         except (ValueError, AttributeError, TypeError, KeyError), e:
#             self.config.interactiveParamsWindow_on_off = False
#             dialogs.dlgBox(exceptionTitle='Failed to open panel', 
#                            exceptionMsg= str(e),
#                            type="Error")
#             return

    def updateRecentFiles(self, path=None):
        """
        path = dictionary {'file_path': path, 'file_type': file type}
        """

        if path:
            if path in self.config.previousFiles:
                del self.config.previousFiles[self.config.previousFiles.index(path)]
            self.config.previousFiles.insert(0, path)
            # make sure only 10 items are present in the list
            while len(self.config.previousFiles) > 10:
                del self.config.previousFiles[-1]
        
        # clear menu
        for item in self.menuRecent.GetMenuItems():
            self.menuRecent.Delete(item.GetId())

        # populate menu
        for i, __ in enumerate(self.config.previousFiles):
            ID = eval('ID_documentRecent'+str(i))
            path = self.config.previousFiles[i]['file_path']
            self.menuRecent.Insert(i, ID, path, "Open Document")
            self.Bind(wx.EVT_MENU, self.onDocumentRecent, id=ID)
            if not os.path.exists(path):
                self.menuRecent.Enable(ID, False)
        
        # append clear
        if len(self.config.previousFiles) > 0:
            self.menuRecent.AppendSeparator()
            
        self.menuRecent.Append(ID_fileMenu_clearRecent, "Clear Menu", "Clear recent items")
        self.Bind(wx.EVT_MENU, self.onDocumentClearRecent, id=ID_fileMenu_clearRecent)
        
    # ----
                      
    def onDocumentClearRecent(self, evt):
        """Clear recent items."""
        
        self.config.previousFiles = []
        self.updateRecentFiles()
        
    # ----
    
    def onDocumentRecent(self, evt):
        """Open recent document."""
        
        # get index
        indexes = {ID_documentRecent0:0, ID_documentRecent1:1, ID_documentRecent2:2, 
                   ID_documentRecent3:3, ID_documentRecent4:4, ID_documentRecent5:5, 
                   ID_documentRecent6:6, ID_documentRecent7:7, ID_documentRecent8:8, 
                   ID_documentRecent9:9}
        
        # get file information
        documentID = indexes[evt.GetId()]
        file_path = self.config.previousFiles[documentID]['file_path']
        file_type = self.config.previousFiles[documentID]['file_type']
        
        # open file
        if file_type == 'pickle':
            self.presenter.onOpenDocument(file_path=file_path, evt=None)
        elif file_type == 'MassLynx':
            self.presenter.onLoadOrigamiDataThreaded(path=file_path, evt=ID_openMassLynxRawFile)
        elif file_type == 'ORIGAMI':
            self.presenter.onLoadOrigamiDataThreaded(path=file_path, evt=ID_openORIGAMIRawFile)
        elif file_type == 'Infrared':
            self.presenter.onLoadOrigamiDataThreaded(path=file_path, evt=ID_openIRRawFile)
        elif file_type == 'Text':
            self.presenter.on2DTextFile(path=file_path, e=ID_openIMStxtFile)
        elif file_type == 'Text_MS':
            self.presenter.onMSTextFileFcn(path=file_path)
    
    def onOpenFile_DnD(self, file_path, file_extension):
        # open file
        if file_extension in ['.pickle', '.pkl']:
            self.presenter.onOpenDocument(file_path=file_path, evt=None)
        elif file_extension == '.raw':
            self.presenter.onLoadOrigamiDataThreaded(path=file_path, evt=ID_openORIGAMIRawFile)
        elif file_extension in ['.txt', '.csv', '.tab']:
            file_format = _checkTextFile(path=file_path)
            if file_format == "2D":
                self.presenter.on2DTextFile(path=file_path, e=ID_openIMStxtFile)
            else:
                self.presenter.onMSTextFile(path=file_path, e=ID_openIMStxtFile)
    
    def updateStatusbar(self, msg, position, delay=3, modify_msg=True):
        """
        Out of thread statusbar display
        ------
        @param msg (str): message to be displayed for specified amount of time
        @param position (int): which statusbar box the msg should be displayed in
        @param delay (int): number of seconds for which the msg should be displayed for
        """
        # modify message
        if modify_msg:
            msg = ">> %s <<" % msg
            
        try:
            self.SetStatusText(msg, number=position)
            sleep(delay)
            self.SetStatusText("", number=position)
        except:
            pass
        
    def updatePlots(self, evt):
        """
        build and update parameters in the zoom function
        """
        plot_parameters = {'grid_show':self.config._plots_grid_show,
                           'grid_color':self.config._plots_grid_color,
                           'grid_line_width':self.config._plots_grid_line_width,
                           'extract_color':self.config._plots_extract_color,
                           'extract_line_width':self.config._plots_extract_line_width,
                           'extract_crossover_sensitivity_1D':self.config._plots_extract_crossover_1D,
                           'extract_crossover_sensitivity_2D':self.config._plots_extract_crossover_2D,
                           'zoom_color_vertical':self.config._plots_zoom_vertical_color,
                           'zoom_color_horizontal':self.config._plots_zoom_horizontal_color,
                           'zoom_color_box':self.config._plots_zoom_box_color,
                           'zoom_line_width':self.config._plots_zoom_line_width,
                           'zoom_crossover_sensitivity':self.config._plots_zoom_crossover
                           }
        pub.sendMessage('plot_parameters', plot_parameters=plot_parameters)
        
        if evt != None:
            evt.Skip()
        
    def onEnableDisableLogging(self, evt):
        
        log_directory = os.path.join(self.config.cwd, "logs")
        if not os.path.exists(log_directory):
            print("Directory logs did not exist - created a new one in %s" % log_directory)
            os.makedirs(log_directory)

        # Generate filename
        if self.config.loggingFile_path is None:
            file_path = "ORIGAMI_%s.log" % self.config.startTime
            self.config.loggingFile_path = os.path.join(log_directory, file_path)
            if self.config.logging:
                print('\nGenerated log filename: %s' % self.config.loggingFile_path)
        
        if self.config.logging:
            sys.stdin = self.panelLog.log
            sys.stdout = self.panelLog.log
            sys.stderr = self.panelLog.log
#             sys.stdin = self.panelPlots.log
#             sys.stdout = self.panelPlots.log
#             sys.stderr = self.panelPlots.log
        else:
            sys.stdin = self.config.stdin
            sys.stdout = self.config.stdout
            sys.stderr = self.config.stderr
        
        if evt != None:
            evt.Skip()
            
    def onEnableDisableThreading(self, evt):
        
        if self.config.threading:
            dialogs.dlgBox(exceptionTitle="Warning",
                           exceptionMsg="Multi-threading is only an experimental feature for now! It might occasionally crash ORIGAMI, in which case you will lose your processed data!", 
                           type="Warning")

        
        if evt != None:
            evt.Skip()

class DragAndDrop(wx.FileDropTarget):
    
    #----------------------------------------------------------------------
    def __init__(self, window):
        """Constructor"""
        wx.FileDropTarget.__init__(self)
        self.window = window

    #----------------------------------------------------------------------
    
    def OnDropFiles(self, x, y, filenames):
        """
        When files are dropped, write where they were dropped and then
        the file paths themselves
        """
        for filename in filenames:
            print("Opening {} file...".format(filename))
            __, file_extension = os.path.splitext(filename)
            if file_extension in ['.raw', '.pickle', '.pkl', '.txt', '.csv', '.tab']:
                try:
                    self.window.onOpenFile_DnD(filename, file_extension)
                except:
                    print("Failed to open {}".format(filename))
                    continue
            else:
                print("Dropped file is not supported")
                continue
        






























