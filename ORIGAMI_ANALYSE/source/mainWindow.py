# -*- coding: utf-8 -*- 
"""
@author: Lukasz G. Migas
"""

# Load modules
from panelControls import panelControls  
from panelPlot import panelPlot
from panelMultipleIons import panelMultipleIons
from panelMultipleTextFiles import panelMultipleTextFiles
from panelMultipleML import panelMML
from panelDocumentTree import panelDocuments
from panelLinearDriftCell import panelLinearDriftCell
from panelCCScalibration import panelCCScalibration
from panelInformation import panelDocumentInfo
from panelAbout import panelAbout

# Load dialogs
from panelOutput import dlgOutputInteractive

# Load libraries
import wx
import wx.aui
from numpy import ceil, floor, int, rot90, array, flipud, absolute, round
import sys
from time import clock, gmtime, strftime
from ids import *
from wx.lib.pubsub import pub 
from wx import ID_SAVE, ID_ANY
from toolbox import findPeakMax, getNarrow1Ddata
from origamiStyles import *

# Print OS version
print(sys.version)

class MyFrame(wx.Frame):

    def __init__(self, parent, config, icons, id=-1, title='ORIGAMI', 
                 pos=wx.DefaultPosition, size=(1200, 600),
                 style=wx.FULL_REPAINT_ON_RESIZE): # wx.DEFAULT_FRAME_STYLE): #
        wx.Frame.__init__(self, None, title=title)
        
        #Extract size of screen
        self.displaysize = wx.GetDisplaySize()
        self.SetDimensions(0,0,self.displaysize[0],self.displaysize[1]-50)
        # Setup config container
        self.config = config
        self.icons = icons
        self.presenter = parent
        
        try:
            icon = wx.Icon('icon.ico', wx.BITMAP_TYPE_ICO, 16, 16)
            self.SetIcon(icon)
        except: 
            print('Could not set icon')
            pass
        
        
        # View parameters
        self.docView = False
        self.settingsView = False
        self.masslynxView = True   
        self.peakView = True
        self.textView = True
        self.ccsView = True
        self.dtView = True
        
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

        self.panelDocuments = panelDocuments(self, self.config, self.icons, self.presenter)
        self.panelControls = panelControls(self, self.config, self.icons) # Settings
        self.panelPlots = panelPlot(self, self.config, self.presenter) # Plots
        self.panelMultipleIons= panelMultipleIons(self, self.config, self.icons, self.presenter) # List of ions
        self.panelMultipleText = panelMultipleTextFiles(self, self.config, self.icons, self.presenter) # List of files
        self.panelMML = panelMML(self, self.config, self.icons, self.presenter) # List of ML files
        self.panelLinearDT = panelLinearDriftCell(self, self.config, self.icons, self.presenter)
        self.panelCCS = panelCCScalibration(self, self.config, self.icons, self.presenter) # calibration panel

        # add the panes to the manager  
        self._mgr.AddPane(self.panelControls, wx.aui.AuiPaneInfo().Left().CloseButton(False)
                          .GripperTop().MinSize((320,450)).Gripper(False).BottomDockable(False)
                          .TopDockable(False).CaptionVisible(False)) 
        
        # Panel to store document information
        self._mgr.AddPane(self.panelDocuments,  wx.aui.AuiPaneInfo().Left().CloseButton(True)
                          .GripperTop().Gripper(False).MinSize((250,250)).BottomDockable(True)
                          .TopDockable(False).Show().Caption('Documents').CaptionVisible(True))
        
        self._mgr.AddPane(self.panelPlots,  wx.aui.AuiPaneInfo().Center().CloseButton(False)
                          .Gripper(False).Caption('Plots').CaptionVisible(False)) 
        
        # Panel to extract multiple ions from ML files
        self._mgr.AddPane(self.panelMultipleIons,  wx.aui.AuiPaneInfo().Right().CloseButton(True)
                          .GripperTop().Gripper(False).MinSize((350,-1)).BottomDockable(False)
                          .TopDockable(False).Hide().Caption('Peak list')
                          .CaptionVisible(True))
        
        # Panel to operate on multiple text files
        self._mgr.AddPane(self.panelMultipleText,  wx.aui.AuiPaneInfo().Right().CloseButton(True)
                          .GripperTop().Gripper(False).MinSize((400,-1)).BottomDockable(False)
                          .TopDockable(False).Hide().Caption('Text Files')
                          .CaptionVisible(True))
        
        # Panel to operate on multiple ML files
        self._mgr.AddPane(self.panelMML,  wx.aui.AuiPaneInfo().Right().CloseButton(True)
                          .GripperTop().Gripper(False).MinSize((350,-1)).BottomDockable(False)
                          .TopDockable(False).Hide().Caption('Combine Multiple MassLynx Files')
                          .CaptionVisible(True))
        
        # Panel to analyse linear DT data (Synapt)
        self._mgr.AddPane(self.panelLinearDT,  wx.aui.AuiPaneInfo().Right().CloseButton(True)
                          .GripperTop().Gripper(False).MinSize((350,-1)).BottomDockable(False)
                          .TopDockable(False).Hide().Caption('Linear Drift Cell').CaptionVisible(True))
        
        # Panel to perform CCS calibration
        self._mgr.AddPane(self.panelCCS,  wx.aui.AuiPaneInfo().Right().CloseButton(True)
                          .GripperTop().Gripper(False).MinSize((350,500)).BottomDockable(False)
                          .TopDockable(False).Hide().Caption('CCS calibration')
                          .CaptionVisible(True))
        

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
        self.makeToolbar()
        self.makeMenubar()
        self.SetMenuBar(self.mainMenubar)
        self.makeShortcuts()
        self.Maximize(True)
            
    def makeBindings(self):
        '''
        Collection of all bindings for various functions
        '''
        self.Bind(wx.EVT_BUTTON, self.presenter.onExtract2DimsOverMZrange, self.panelControls.extractBtn)
        self.Bind(wx.EVT_BUTTON, self.presenter.onDocumentColour, self.panelControls.colorBtn)
        self.Bind(wx.EVT_BUTTON, self.presenter.onPickPeaks, self.panelControls.findPeaksBtn)
        self.Bind(wx.EVT_BUTTON, self.presenter.onChangePlotStyle, self.panelControls.applyStyleBtn)   
        self.Bind(wx.EVT_COMBOBOX, self.selectOverlayMethod, id=ID_selectOverlayMethod)
        self.Bind(wx.EVT_TOOL, self.presenter.on2DMultipleTextFiles, id=ID_openTextFiles)
        self.Bind(wx.EVT_TOOL, self.presenter.onProcessMultipleTextFiles, id=ID_processTextFiles)
        self.Bind(wx.EVT_TOOL, self.presenter.onOverlayMultipleIons, id=ID_overlayTextFromList)
        self.Bind(wx.EVT_COMBOBOX, self.selectTextOverlayMethod, id=ID_textSelectOverlayMethod)
        self.Bind(wx.EVT_TOOL, self.presenter.onExtractDToverMZrangeMultiple, id=ID_extractDriftVoltagesForEachIon)
        self.Bind(wx.EVT_TOOL, self.presenter.onOpenMultipleMLFiles, id=ID_openMassLynxFiles)
           
    def statusBar(self):
        self.mainStatusbar = self.CreateStatusBar(6, wx.ST_SIZEGRIP, wx.ID_ANY)
        # 0 = current x y pos
        # 1 = m/z range
        # 2 = MSMS mass
        # 3 = status information
        # 4 = present working file
        # 5 = tool
        self.mainStatusbar.SetStatusWidths([225,125,110,400,-1,50])
        font = wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.NORMAL)
        self.mainStatusbar.SetFont(font)
                
    def onMode(self, dataOut):
        shift, ctrl, alt, add2table, wheel = dataOut
        self.mode = ''
        myCursor = wx.StockCursor(wx.CURSOR_ARROW)
        if alt: 
            self.mode = 'Measure' # Block zoom
#             myCursor= wx.StockCursor(wx.CURSOR_SIZEWE)
        elif ctrl: 
            self.mode = 'Add data'
#             myCursor= wx.StockCursor(wx.CURSOR_SPRAYCAN)
        elif add2table: 
            self.mode = 'Add data'
#             myCursor= wx.StockCursor(wx.CURSOR_SPRAYCAN)
        elif shift: 
            self.mode = 'Wheel zoom Y'
            myCursor= wx.StockCursor(wx.CURSOR_SIZENS)
        elif wheel:
            self.mode = 'Wheel zoom X'
            myCursor= wx.StockCursor(wx.CURSOR_SIZEWE)
        elif alt and ctrl: 
            self.mode = ''
        
        self.SetCursor(myCursor)
        self.SetStatusText("%s" % (self.mode), number=5)

    def makeMenubar(self):
        self.mainMenubar = wx.MenuBar()  
        
        # Binary sub-menu
        openBinaryMenu = wx.Menu()
        openBinaryMenu.Append(ID_openMSFile, 'Open MS from MassLynx file (MS .1dMZ)\tCtrl+M')
        openBinaryMenu.Append(ID_open1DIMSFile, 'Open 1D IM-MS from MassLynx file (1D IM-MS, .1dDT)')
        openBinaryMenu.Append(ID_open2DIMSFile, 'Open 2D IM-MS from MassLynx file (2D IM-MS, .2dRTDT)\tCtrl+D')
         
        menuFile = wx.Menu()
#         menuFile.Append(ID_openRawFile,'Open MassLynx IM-MS file (.raw)\tCtrl+O')
#         menuFile.Append(ID_openORIGAMIRawFile,'Open MassLynx IM-MS file (.raw)\tCtrl+O')
        menuFile.Append(ID_openORIGAMIRawFile, 'Open ORIGAMI MassLynx IM-MS file (.raw)\tCtrl+R')
        menuFile.Append(ID_openMultipleORIGAMIRawFiles, 'Open Multiple ORIGAMI MassLynx IM-MS file (.raw)\tCtrl+Shift+Q')
        menuFile.Append(ID_openMassLynxFiles,'Open Multiple MassLynx files\tCtrl+Shift+R')
        menuFile.Append(ID_addCCScalibrantFile, 'Open Calibration MassLynx file (.raw)\tCtrl+C')
        menuFile.Append(ID_openLinearDTRawFile, 'Open Linear DT MassLynx file (.raw)\tCtrl+F')
        menuFile.Append(ID_openMassLynxFile, 'Open MassLynx file (no IM-MS, .raw)\tCtrl+Shift+M')
        
        menuFile.AppendMenu(ID_ANY, 'Open MassLynx...', openBinaryMenu)
        menuFile.AppendSeparator()
        menuFile.Append(ID_openIMStxtFile, 'Open 2D Text file (.csv, .txt)\tCtrl+T')
        menuFile.Append(ID_openTextFilesMenu, 'Open multiple 2D Text files (.csv, .txt)\tCtrl+Shift+T')
#         menuFile.AppendSeparator()
        menuFile.Append(ID_openIRRawFile, 'Open MassLynx IR file (.raw)\tCtrl+X')
#         menuFile.Append(ID_openIRTextile, 'Open 2D IR Text file (.csv, .txt)\tCtrl+E')
        menuFile.AppendSeparator()
        menuFile.Append(ID_saveDocument, 'Save Current ORIGAMI Document file (.pickle)\tCtrl+P')
        menuFile.Append(ID_openDocument, 'Open ORIGAMI Document file (.pickle)\tCtrl+Shift+P')
        menuFile.AppendSeparator()
        self.mainMenubar.Append(menuFile, '&File')
        
        # VIEW
        menuView = wx.Menu()
        self.documentsPage = menuView.Append(ID_OnOff_docView, 'Enable/Disable documents panel...\tCtrl+1',
                                             kind=wx.ITEM_CHECK)
        
        self.settingsPage = menuView.Append(ID_OnOff_settingsView, 'Enable/Disable settings panel...\tCtrl+2', 
                                            kind=wx.ITEM_CHECK)
        
        self.mzTable = menuView.Append(ID_OnOff_ionView, 'Enable/Disable multi ion panel...\tCtrl+3',  
                                       kind=wx.ITEM_CHECK)
        
        self.textTable = menuView.Append(ID_OnOff_textView, 'Enable/Disable multi text panel...\tCtrl+4',  
                                         kind=wx.ITEM_CHECK)
        
        self.multipleMLTable = menuView.Append(ID_OnOff_mlynxView, 'Enable/Disable multi MassLynx panel...\tCtrl+5',  
                                               kind=wx.ITEM_CHECK)
        
        self.multifieldTable = menuView.Append(ID_OnOff_dtView, 'Enable/Disable linear DT panel...\tCtrl+6',  
                                               kind=wx.ITEM_CHECK)
         
        self.ccsTable = menuView.Append(ID_OnOff_ccsView, 'Enable/Disable CCS calibration panel...\tCtrl+7',  
                                               kind=wx.ITEM_CHECK)

        menuView.Append(ID_saveAsInteractive, 'Open interactive output panel...\tShift+Z')
        
        # Show documents and settings page
        self.documentsPage.Check(True)
        self.settingsPage.Check(True)
        self.mainMenubar.Append(menuView, '&View')
        
        # CONFIG
        menuConfig = wx.Menu()
        menuConfig.Append(ID_saveConfig, 'Export configuration XML file (default)\tCtrl+S')
        menuConfig.Append(ID_saveAsConfig, 'Export configuration XML file as...\tCtrl+Shift+S')
        menuConfig.AppendSeparator()
        menuConfig.Append(ID_openConfig, 'Import configuration XML file (default)\tCtrl+Shift+O')
        menuConfig.Append(ID_openAsConfig, 'Import configuration XML file from...')
        menuConfig.AppendSeparator()
        menuConfig.Append(ID_openCCScalibrationDatabse, 'Import CCS calibration database\tCtrl+Alt+C')
        menuConfig.Append(ID_selectCalibrant, 'Show CCS calibrants\tCtrl+Shift+C')
        menuConfig.AppendSeparator()
        menuConfig.Append(ID_setDriftScopeDir, 'Set DriftScope path...')
        self.mainMenubar.Append(menuConfig, '&Libraries')
        
        # WINDOW MENU
        menuWindow = wx.Menu()
        menuWindow.Append(ID_clearAllPlots, 'Clear all plots')
        menuWindow.AppendSeparator()
        menuWindow.Append(ID_windowMaximize, 'Maximize')
        menuWindow.Append(ID_windowMinimize, 'Minimize')
        
        self.mainMenubar.Append(menuWindow, '&Window')

        # HELP MENU
        menuHelp = wx.Menu()
#         menuHelp.Append(ID_RESET_ORIGAMI, 'Reinitilise ORIGAMI')
        menuHelp.Append(ID_RESET_PLOT_ZOOM, 'Reset Zoom Tool\tF12')
        menuHelp.AppendSeparator()
        menuHelp.Append(ID_helpGuide, 'User Guide... (web)\tF1')
        menuHelp.AppendItem(makeMenuItem(parent=menuHelp, id=ID_helpYoutube,
                                         text='Check out video guides... ', 
                                         bitmap=self.icons.iconsLib['youtube16']))
        
        menuHelp.AppendItem(makeMenuItem(parent=menuHelp, id=ID_helpNewVersion,
                                         text='Check for updates...', 
                                         bitmap=self.icons.iconsLib['github16']))
        menuHelp.Append(ID_helpCite, 'Paper to cite...')
        menuHelp.AppendSeparator()
        menuHelp.AppendItem(makeMenuItem(parent=menuHelp, id=ID_SHOW_ABOUT,
                                         text='About ORIGAMI\tCtrl+Shift+A', 
                                         bitmap=self.icons.iconsLib['origamiLogoDark16']))
        self.mainMenubar.Append(menuHelp, '&Help')
        
        self.SetMenuBar(self.mainMenubar)
        
        # Bind functions to menu
        # HELP MENU
        self.Bind(wx.EVT_MENU, self.onHelpAbout, id=ID_SHOW_ABOUT)
        self.Bind(wx.EVT_MENU, self.presenter.onLibraryLink, id=ID_helpGuide)
        self.Bind(wx.EVT_MENU, self.presenter.onLibraryLink, id=ID_helpCite)
        self.Bind(wx.EVT_MENU, self.presenter.onLibraryLink, id=ID_helpYoutube)
        self.Bind(wx.EVT_MENU, self.presenter.onLibraryLink, id=ID_helpNewVersion)
        self.Bind(wx.EVT_MENU, self.presenter.onRebootWindow, id=ID_RESET_ORIGAMI)
        self.Bind(wx.EVT_MENU, self.presenter.onRebootZoom, id=ID_RESET_PLOT_ZOOM) 
        
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
        
        
        
        
        # OUTPUT
        self.Bind(wx.EVT_MENU, self.presenter.saveImages2,id=ID_saveOverlayImage)
        self.Bind(wx.EVT_MENU, self.presenter.saveImages2,id=ID_saveMSImage)
        self.Bind(wx.EVT_MENU, self.presenter.saveImages2,id=ID_saveMZDTImage)
        self.Bind(wx.EVT_MENU, self.presenter.saveImages2,id=ID_saveRTImage)
        self.Bind(wx.EVT_MENU, self.presenter.saveImages2,id=ID_save1DImage)
        self.Bind(wx.EVT_MENU, self.presenter.saveImages2,id=ID_save2DImage)
        self.Bind(wx.EVT_MENU, self.presenter.saveImages2,id=ID_save3DImage)
        self.Bind(wx.EVT_MENU, self.presenter.saveImages2,id=ID_saveWaterfallImage)
        self.Bind(wx.EVT_MENU, self.presenter.saveImages2,id=ID_saveRMSDImage)
        self.Bind(wx.EVT_MENU, self.presenter.saveImages2,id=ID_saveRMSFImage)
        self.Bind(wx.EVT_MENU, self.presenter.saveImages2,id=ID_saveRMSDmatrixImage)
        self.Bind(wx.EVT_MENU, self.saveFigures, id=ID_saveAllImages)
        self.Bind(wx.EVT_MENU, self.openSaveAsDlg, id=ID_saveAsInteractive)
                
        # CONFIG MENU
        self.Bind(wx.EVT_MENU, self.presenter.onExportConfig, id=ID_saveConfig)
        self.Bind(wx.EVT_MENU, self.presenter.onExportConfig, id=ID_saveAsConfig)
        self.Bind(wx.EVT_MENU, self.presenter.onImportConfig, id=ID_openConfig)  
        self.Bind(wx.EVT_MENU, self.presenter.onImportConfig, id=ID_openAsConfig)  
        self.Bind(wx.EVT_MENU, self.presenter.onSetupDriftScope, id=ID_setDriftScopeDir)  
        self.Bind(wx.EVT_MENU, self.presenter.onSelectProtein, id=ID_selectCalibrant)  
        self.Bind(wx.EVT_MENU, self.presenter.onImportCCSDatabase, id=ID_openCCScalibrationDatabse)  
        
        # VIEW MENU
        self.Bind(wx.EVT_MENU, self.ToggleView, self.documentsPage)
        self.Bind(wx.EVT_MENU, self.ToggleView, self.mzTable)
        self.Bind(wx.EVT_MENU, self.ToggleView, self.multifieldTable)
        self.Bind(wx.EVT_MENU, self.ToggleView, self.textTable)
        self.Bind(wx.EVT_MENU, self.ToggleView, self.multipleMLTable)
        self.Bind(wx.EVT_MENU, self.ToggleView, self.settingsPage)
        self.Bind(wx.EVT_MENU, self.ToggleView, self.ccsTable)
        
        # WINDOW MENU
        self.Bind(wx.EVT_MENU, self.onWindowMaximize, id=ID_windowMaximize)
        self.Bind(wx.EVT_MENU, self.onWindowIconize, id=ID_windowMinimize)
        self.Bind(wx.EVT_MENU, self.presenter.onClearAllPlots, 
                  id=ID_clearAllPlots)
        
    def onWindowMaximize(self, evt):
        """Maximize app."""
        self.Maximize()
    # ----
    
    def onWindowIconize(self, evt):
        """Iconize app."""
        self.Iconize()
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
#             ["O", self.presenter.onOrigamiRawDirectory, wx.ACCEL_CTRL],
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
    
    def makeToolbar(self):
        
        # Bind events
        self.Bind(wx.EVT_TOOL, self.presenter.onOrigamiRawDirectory, id=ID_openORIGAMIRawFile)
        self.Bind(wx.EVT_TOOL, self.presenter.on2DTextFile, id=ID_openIMStxtFile)
        self.Bind(wx.EVT_TOOL, self.presenter.onOrigamiRawDirectory, id=ID_openMassLynxRawFile)
                
        
        self.mainToolbar = self.CreateToolBar(wx.TB_HORIZONTAL | wx.TB_DOCKABLE, wx.ID_ANY)
        self.mainToolbar.SetToolBitmapSize((24,24)) 
        self.mainToolbar.AddTool(ID_openDocument, self.icons.iconsLib['folderProject'], 
                                 shortHelpString="Open project file")
        self.mainToolbar.AddTool(ID_saveDocument, self.icons.iconsLib['saveDoc'], 
                                 shortHelpString="Save project file")
        
        self.mainToolbar.AddSeparator()
        self.mainToolbar.AddTool(ID_openORIGAMIRawFile, self.icons.iconsLib['folderOrigami'], 
                                 shortHelpString="Open ORIGAMI MassLynx file")
        self.mainToolbar.AddTool(ID_openORIGAMIRawFile, self.icons.iconsLib['folderMassLynx'],
                                 shortHelpString="Open MassLynx file")
        self.mainToolbar.AddTool(ID_openIMStxtFile, self.icons.iconsLib['folderText'], 
                                 shortHelpString="Open text file")
        self.mainToolbar.AddSeparator()
        
        self.mainToolbar.AddTool(ID_openTextFiles, self.icons.iconsLib['folderTextMany'], 
                                 shortHelpString="Open multiple text files")
        self.mainToolbar.AddTool(ID_openMassLynxFiles, self.icons.iconsLib['folderMassLynxMany'], 
                                 shortHelpString="Open multiple MassLynx files")
        self.mainToolbar.AddSeparator()
        
        self.Bind(wx.EVT_TOOL, self.ToggleView, id=ID_OnOff_docView)
        
        self.mainToolbar.AddCheckTool(ID_OnOff_docView, self.icons.iconsLib['panelDoc'], 
                                      shortHelp="Enable/Disable documents panel")
        self.mainToolbar.ToggleTool(id=ID_OnOff_docView, toggle=True)
        
        self.mainToolbar.AddCheckTool(ID_OnOff_settingsView, self.icons.iconsLib['panelParameters'], 
                                      shortHelp="Enable/Disable settings panel")
        self.mainToolbar.ToggleTool(id=ID_OnOff_settingsView, toggle=True)
        
        self.mainToolbar.AddCheckTool(ID_OnOff_ionView, self.icons.iconsLib['panelIon'], 
                                      shortHelp="Enable/Disable multi ion panel")
        
        self.mainToolbar.AddCheckTool(ID_OnOff_textView, self.icons.iconsLib['panelText'], 
                                      shortHelp="Enable/Disable multi text panel")
        
        self.mainToolbar.AddCheckTool(ID_OnOff_mlynxView, self.icons.iconsLib['panelML'], 
                                      shortHelp="Enable/Disable multi MassLynx panel")

        self.mainToolbar.AddCheckTool(ID_OnOff_dtView, self.icons.iconsLib['panelDT'], 
                                      shortHelp="Enable/Disable linear DT panel")
         
        self.mainToolbar.AddCheckTool(ID_OnOff_ccsView, self.icons.iconsLib['panelCCS'], 
                                      shortHelp="Enable/Disable CCS calibration panel")

        self.mainToolbar.AddSeparator()
        self.mainToolbar.AddTool(ID_saveAsInteractive, self.icons.iconsLib['bokehLogo'], 
                                 shortHelpString="Open interactive output panel")
        
        self.mainToolbar.Realize()
        
    def openSaveAsDlg(self, evt):
        dlg = dlgOutputInteractive(self, self.icons, self.presenter, self.config)
        dlg.Show()
   
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
        if not self.panelControls.IsShown(): self.settingsPage.Check(False)
        if not self.panelCCS.IsShown(): self.ccsTable.Check(False)
        
        if evt != None:
            evt.Skip()
        
    def ToggleView(self, evt):
        """
        Enable/Disable panels
        """

        if evt.GetId() == ID_OnOff_docView:
            if self.docView:
                self._mgr.GetPane(self.panelDocuments).Show()
                self.documentsPage.Check(True)
                self.docView = False
                self.mainToolbar.ToggleTool(id=ID_OnOff_docView, toggle=True)
            else:
                self._mgr.GetPane(self.panelDocuments).Hide()
                self.documentsPage.Check(False)
                self.docView = True
                self.mainToolbar.ToggleTool(id=ID_OnOff_docView, toggle=False)
                
        if evt.GetId() == ID_OnOff_settingsView:
            if self.settingsView:
                self._mgr.GetPane(self.panelControls).Show()
                self.settingsPage.Check(True)
                self.settingsView = False
                self.mainToolbar.ToggleTool(id=ID_OnOff_settingsView, toggle=True)
            else:
                self._mgr.GetPane(self.panelControls).Hide()
                self.settingsPage.Check(False)
                self.settingsView = True
                self.mainToolbar.ToggleTool(id=ID_OnOff_settingsView, toggle=False)
                
        if evt.GetId() == ID_OnOff_ionView:
            if self.peakView:
                self._mgr.GetPane(self.panelMultipleIons).Show()
                self.mzTable.Check(True)
                self.peakView = False
                self.mainToolbar.ToggleTool(id=ID_OnOff_ionView, toggle=True)
            else:
                self._mgr.GetPane(self.panelMultipleIons).Hide()
                self.mzTable.Check(False)
                self.peakView = True
                self.mainToolbar.ToggleTool(id=ID_OnOff_ionView, toggle=False)
                
        if evt.GetId() == ID_OnOff_mlynxView:
            if self.masslynxView:
                self._mgr.GetPane(self.panelMML).Show()
                self.multipleMLTable.Check(True)
                self.masslynxView = False
                self.mainToolbar.ToggleTool(id=ID_OnOff_mlynxView, toggle=True)
            else:
                self._mgr.GetPane(self.panelMML).Hide()
                self.multipleMLTable.Check(False)
                self.masslynxView = True
                self.mainToolbar.ToggleTool(id=ID_OnOff_mlynxView, toggle=False)
             
        if evt.GetId() == ID_OnOff_textView:
            if self.textView:
                self._mgr.GetPane(self.panelMultipleText).Show()
                self.textTable.Check(True)
                self.textView = False
                self.mainToolbar.ToggleTool(id=ID_OnOff_textView, toggle=True)
            else:
                self._mgr.GetPane(self.panelMultipleText).Hide()
                self.textTable.Check(False)
                self.textView = True
                self.mainToolbar.ToggleTool(id=ID_OnOff_textView, toggle=False)
                
        if evt.GetId() == ID_OnOff_ccsView:
            if self.ccsView:
                self._mgr.GetPane(self.panelCCS).Show()
                self.ccsTable.Check(True)
                self.ccsView = False
                self.mainToolbar.ToggleTool(id=ID_OnOff_ccsView, toggle=True)
            else:
                self._mgr.GetPane(self.panelCCS).Hide()
                self.ccsTable.Check(False)
                self.ccsView = True
                self.mainToolbar.ToggleTool(id=ID_OnOff_ccsView, toggle=False)
                
        if evt.GetId() == ID_OnOff_dtView:
            if self.dtView:
                self._mgr.GetPane(self.panelLinearDT).Show()
                self.multifieldTable.Check(True)
                self.dtView = False
                self.mainToolbar.ToggleTool(id=ID_OnOff_dtView, toggle=True)
            else:
                self._mgr.GetPane(self.panelLinearDT).Hide()
                self.multifieldTable.Check(False)
                self.dtView = True
                self.mainToolbar.ToggleTool(id=ID_OnOff_dtView, toggle=False)
             
        self._mgr.Update()
        
    def OnClose(self, event):
        # deinitialize the frame manager
        try:
            self.config.saveConfigXML(path='configOut.xml', evt=None)
        except: pass
        self._mgr.UnInit()
        self.Destroy()
        
    def OnDistance(self, startX):
        # Simple way of setting the start point
        self.startX = startX
        pass
        
    def OnMotion(self, xpos, ypos):
        """
        Triggered by pubsub from plot windows. Reports text in Status Bar.
        :param xpos: x position fed from event
        :param ypos: y position fed from event
        :return: None
        """
        self.currentPage = self.panelPlots.mainBook.GetPageText(self.panelPlots.mainBook.GetSelection())
        
        if xpos is not None and ypos is not None:
            # If measuring distance, additional fields are used to help user 
            # make observations
            if self.startX is not None:
                range = absolute(self.startX - xpos)
                charge = round(1.0/range,1)
                mass = (xpos+charge)*charge
                # If inside a plot area with MS, give out charge state
                if self.mode == 'Measure' and (self.currentPage == "MS" or 
                                              self.currentPage == "DT/MS"):
                    self.SetStatusText(u"X=%.2f Y=%.2f Δx=%.2f z=%.1f mw=%.1f" % (xpos, ypos, range, charge, mass), number=0)
                else:
                    self.SetStatusText(u"X=%.2f Y=%.2f Δx=%.2f" % (xpos, ypos, range), number=0)
            else:
                self.SetStatusText("X=%.2f Y=%.2f" % (xpos, ypos), number=0)
            
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
            
        if self.currentPage == "MS" or currentView == "MS":
            if currentDoc == "": currentDoc = self.presenter.currentDoc
            if xvalsMin == None or xvalsMax == None: 
                self.SetStatusText('Your extraction range was outside the window. Please try again',3)
                return
            mzStart = round(xvalsMin,2)
            mzEnd = round(xvalsMax,2)
            mzYMax = round(yvalsMax*100,1)
            # Check that values are in correct order
            if mzEnd < mzStart: mzEnd, mzStart = mzStart, mzEnd
            
            # Make sure the document has MS in first place (i.e. Text)
            if not self.presenter.documentsDict[currentDoc].gotMS: return
            # Get MS data for specified region and extract Y-axis maximum
            ms = self.presenter.documentsDict[currentDoc].massSpectrum
            ms = flipud(rot90(array([ms['xvals'], ms['yvals']])))
            mzYMax = self.getYvalue(msList=ms, mzStart=mzStart, mzEnd=mzEnd)
            if (self.config.ciuMode == 'ORIGAMI' or 
                self.config.ciuMode == 'MANUAL' or
                self.config.ciuMode == 'Infrared'):
                self._mgr.GetPane(self.panelMultipleIons).Show()
                self.mzTable.Check(True)
                self._mgr.Update()
                # Check if value already present
                outcome = self.panelMultipleIons.topP.onCheckForDuplicates(mzStart=str(mzStart), 
                                                                           mzEnd=str(mzEnd))
                if outcome:
                    self.SetStatusText('Selected range already in the table',3)
                    if currentView == "MS":
                        return outcome
                    return
                self.panelMultipleIons.topP.peaklist.Append([mzStart,
                                                            mzEnd, "","","", 
                                                            currentDoc,"",mzYMax])
                if self.config.showRectanges:
                    self.presenter.addRectMS(mzStart, 0, (mzEnd-mzStart), 1.0, 
                                   color=self.config.annotColor, 
                                   alpha=(self.config.annotTransparency/100),
                                   repaint=True)
                
            elif self.config.ciuMode == 'LinearDT':
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
            currentDocument = self.presenter.view.panelDocuments.topP.documents.enableCurrentDocument()
            document = self.presenter.documentsDict[currentDocument]
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
            
                
        elif self.currentPage == "RT" and self.config.ciuMode == 'LinearDT':
            # TODO Add function so it plots a patch on the plot.
            # TODO Change the way zoom works for this figure - it should not zoom the Y-axis!
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
            self.panelLinearDT.topP.peaklist.Append([xvalsMin,
                                                     xvalsMax,
                                                     xvalDiff, "",
                                                     self.presenter.currentDoc])
            
            self.presenter.addRectRT(xvalsMin, 0, (xvalsMax-xvalsMin), 1.0, 
                           color=self.config.annotColor, 
                           alpha=(self.config.annotTransparency/100),
                           repaint=True)
        elif self.currentPage == 'RT' and self.config.ciuMode != 'LinearDT':
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
           
    def selectOverlayMethod(self, event):
        self.config.overlayMethod = self.panelMultipleIons.topP.combo.GetValue()
         
    def selectTextOverlayMethod(self, event):
        self.config.overlayMethod = self.panelMultipleText.topP.combo.GetValue()
        
