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
from __future__ import division
import wx
import plots as plots
from ids import *
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
from styles import makeMenuItem
from icons import IconContainer as icons
import os
from toolbox import isempty, merge_two_dicts
from dialogs import dlgBox


class panelPlot ( wx.Panel ):
    def __init__( self, parent, config, presenter):
        wx.Panel.__init__ ( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition,
                             size = wx.Size( 800,600 ), style = wx.TAB_TRAVERSAL )
        
        self.config = config
        self.parent = parent
        self.presenter = presenter
        self.icons = icons()
        self.currentPage = None
        #Extract size of screen
        self.displaysize = wx.GetDisplaySize()
        self.SetDimensions(0,0,self.displaysize[0]-320,self.displaysize[1]-50)
        self.displaysizeMM = wx.GetDisplaySizeMM()

        self.displayRes = (wx.GetDisplayPPI())
        self.figsizeX = (self.displaysize[0]-320)/self.displayRes[0]
        self.figsizeY = (self.displaysize[1]-70)/self.displayRes[1]
        
        # used to keep track of what were the last selected pages
        self.window_plot1D = 'MS'
        self.window_plot2D = '2D'
        self.window_plot3D = '3D'
        self.makeNotebook()
        
        # bind events
        self.mainBook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.onPageChanged)
        
        # initialise
        self.onPageChanged(evt=None)
        
    def onPageChanged(self, evt):
        # get current page
        self.currentPage = self.mainBook.GetPageText(self.mainBook.GetSelection())
        
        # keep track of previous pages
        if self.currentPage in ['MS', 'RT', '1D']:
            self.window_plot1D = self.currentPage
        elif self.currentPage in ['2D', 'DT/MS', 'Waterfall', 'RMSF', 'Comparison', 'Overlay']:
            self.window_plot2D = self.currentPage
        elif self.currentPage in ['3D']:
            self.window_plot3D = self.currentPage
            
        # update statusbars
        if self.config.processParamsWindow_on_off:
            self.parent.panelProcessData.updateStatusbar()
            
        if self.config.extraParamsWindow_on_off:
            self.parent.panelParametersEdit.updateStatusbar()    
            
    def makeNotebook(self):
        bSizer1 = wx.BoxSizer( wx.VERTICAL )
		# Setup notebook
        self.mainBook = wx.Notebook( self, wx.ID_ANY, wx.DefaultPosition,
                                         wx.DefaultSize, 0 )
        # Setup PLOT MS
        self.panelMS = wx.Panel( self.mainBook, wx.ID_ANY, wx.DefaultPosition,
                                    wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.mainBook.AddPage( self.panelMS, u"MS", False )
        figsize = (self.figsizeX, 2)
        self.plot1 = plots.plots(self.panelMS, figsize = figsize, config = self.config)
        
        box1 = wx.BoxSizer(wx.VERTICAL)
        box1.Add(self.plot1, 1, wx.EXPAND)
        self.panelMS.SetSizer(box1)
        
        # Setup PLOT RT
        self.panelRT = wx.Panel( self.mainBook, wx.ID_ANY, wx.DefaultPosition, 
                                   wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.mainBook.AddPage( self.panelRT, u"RT", False )        
        figsize = (self.figsizeX, 2)
        self.plotRT = plots.plots(self.panelRT, figsize = figsize, config = self.config)

        box12 = wx.BoxSizer(wx.VERTICAL)
        box12.Add(self.plotRT, 1, wx.EXPAND)
        self.panelRT.SetSizer(box12)
        
        # Setup PLOT 1D 
        self.panel1D = wx.Panel( self.mainBook, wx.ID_ANY, wx.DefaultPosition, 
                                   wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.mainBook.AddPage( self.panel1D, u"1D", False )        
        figsize = (self.figsizeX, 2)
        self.plot1D = plots.plots(self.panel1D, figsize = figsize, config = self.config)

        box1 = wx.BoxSizer(wx.VERTICAL)
        box1.Add(self.plot1D, 1, wx.EXPAND)
        self.panel1D.SetSizer(box1)
          
        # Setup PLOT 2D
        self.panel2D = wx.Panel( self.mainBook, wx.ID_ANY, wx.DefaultPosition, 
                                   wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.mainBook.AddPage( self.panel2D, u"2D", False )
        figsize = (self.figsizeX, 4)  
        self.plot2D = plots.plots(self.panel2D, config = self.config) 
        
        box14 = wx.BoxSizer(wx.HORIZONTAL)
        box14.Add(self.plot2D, 1, wx.EXPAND | wx.ALL)
        self.panel2D.SetSizerAndFit(box14)         
        
        # Setup PLOT DT/MS
        self.panelMZDT = wx.Panel( self.mainBook, wx.ID_ANY, wx.DefaultPosition, 
                                   wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.mainBook.AddPage( self.panelMZDT, u"DT/MS", False )
        figsize = (self.figsizeX, 4)  
        self.plotMZDT = plots.plots(self.panelMZDT, config = self.config) 
          
        boxMZDT = wx.BoxSizer(wx.HORIZONTAL)
        boxMZDT.Add(self.plotMZDT, 1, wx.EXPAND | wx.ALL)
        self.panelMZDT.SetSizerAndFit(boxMZDT)
        
#         # Setup PLOT RT/MS
#         self.panelMZRT = wx.Panel( self.mainBook, wx.ID_ANY, wx.DefaultPosition, 
#                                    wx.DefaultSize, wx.TAB_TRAVERSAL )
#         self.mainBook.AddPage( self.panelMZRT, u"RT/MS", False )
#         figsize = (self.figsizeX, 4)  
#         self.plotMZRT = plot2d.plot2D(self.panelMZRT, config = self.config) 
#           
#         boxMZRT = wx.BoxSizer(wx.HORIZONTAL)
#         boxMZRT.Add(self.plotMZRT, 1, wx.EXPAND | wx.ALL)
#         self.panelMZDT.SetSizerAndFit(boxMZRT)        

        # Setup PLOT WATERFALL
        self.waterfallIMS = wx.Panel( self.mainBook, wx.ID_ANY, wx.DefaultPosition, 
                                   wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.mainBook.AddPage( self.waterfallIMS, u"Waterfall", False )
        figsize = (self.figsizeX, 4)  
        self.plotWaterfallIMS = plots.plots(self.waterfallIMS, figsize = figsize, 
                                              config = self.config)
        
        box15 = wx.BoxSizer(wx.HORIZONTAL)
        box15.Add(self.plotWaterfallIMS, 1, wx.EXPAND | wx.ALL)
        self.waterfallIMS.SetSizerAndFit(box15)     

        # Setup PLOT 3D
        self.panel3D = wx.Panel( self.mainBook, wx.ID_ANY, wx.DefaultPosition, 
                                   wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.mainBook.AddPage( self.panel3D, u"3D", False )
        self.plot3D = plots.plots(self.panel3D, config = self.config)

        plotSizer = wx.BoxSizer(wx.VERTICAL)     
        plotSizer.Add(self.plot3D, 1, wx.EXPAND)
        self.panel3D.SetSizer(plotSizer)  
        
        # Setup PLOT RMSF
        self.panelRMSF = wx.Panel( self.mainBook, wx.ID_ANY, wx.DefaultPosition, 
                                   wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.mainBook.AddPage( self.panelRMSF, u"RMSF", False )
        self.plotRMSF = plots.plots(self.panelRMSF, figsize = figsize, 
                                      config = self.config)

        plotSizer5 = wx.BoxSizer(wx.VERTICAL)     
        plotSizer5.Add(self.plotRMSF, 1, wx.EXPAND)
        self.panelRMSF.SetSizer(plotSizer5)  
        
        
        # Setup PLOT Comparison
        self.m_panel17 = wx.Panel( self.mainBook, wx.ID_ANY, wx.DefaultPosition, 
                                   wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.mainBook.AddPage( self.m_panel17, u"Comparison", False )
        self.plotCompare = plots.plots(self.m_panel17, config = self.config)

        
        plotSizer3 = wx.BoxSizer(wx.VERTICAL)     
        plotSizer3.Add(self.plotCompare, 1, wx.EXPAND)
        self.m_panel17.SetSizer(plotSizer3)  
        
        
        # Setup PLOT Overlay
        self.panelOverlay = wx.Panel( self.mainBook, wx.ID_ANY, wx.DefaultPosition, 
                                   wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.mainBook.AddPage( self.panelOverlay, u"Overlay", False )
        self.plotOverlay = plots.plots(self.panelOverlay, config = self.config)

        
        plotSizer4 = wx.BoxSizer(wx.VERTICAL)     
        plotSizer4.Add(self.plotOverlay, 1, wx.EXPAND)
        self.panelOverlay.SetSizer(plotSizer4)  
        
        self.panelCCSCalibration = wx.SplitterWindow(self.mainBook, wx.ID_ANY, wx.DefaultPosition,
                                                     wx.DefaultSize, wx.TAB_TRAVERSAL | wx.SP_3DSASH)
        # Create two panels for each dataset
        self.topPanelMS = wx.Panel(self.panelCCSCalibration)
        self.topPanelMS.SetBackgroundColour("white")
        self.bottomPanel1DT = wx.Panel(self.panelCCSCalibration)
        self.bottomPanel1DT.SetBackgroundColour("white")
        # Add panels to splitter window
        self.panelCCSCalibration.SplitHorizontally(self.topPanelMS, self.bottomPanel1DT)
        self.panelCCSCalibration.SetMinimumPaneSize(250)
        self.panelCCSCalibration.SetSashGravity(0.5)
        self.panelCCSCalibration.SetSashSize(10)
        # Add to notebook
        self.mainBook.AddPage(self.panelCCSCalibration, u"Calibration", False)
        
        # Plot MS 
        self.topPlotMS = plots.plots(self.topPanelMS, figsize = figsize, config = self.config)
        boxTopPanelMS = wx.BoxSizer(wx.VERTICAL)
        boxTopPanelMS.Add(self.topPlotMS, 1, wx.EXPAND)
        self.topPanelMS.SetSizer(boxTopPanelMS)
        
        # Plot 1DT
        self.bottomPlot1DT = plots.plots(self.bottomPanel1DT, figsize = figsize, config = self.config)
        boxBottomPanel1DT = wx.BoxSizer(wx.VERTICAL)
        boxBottomPanel1DT.Add(self.bottomPlot1DT, 1, wx.EXPAND)
        self.bottomPanel1DT.SetSizer(boxBottomPanel1DT)
        
#         # Plot MAYAVI
#         self.mayaviPanel = wx.Panel( self.mainBook, wx.ID_ANY, wx.DefaultPosition, 
#                                    wx.DefaultSize, wx.TAB_TRAVERSAL )
#         self.mainBook.AddPage( self.mayaviPanel, u"Mayavi", False )
#             
#         self.MV = plots.MayaviPanel()
#         self.plotMayavi = self.MV.edit_traits(parent=self.mayaviPanel, 
#                                               kind='subpanel').control
#   
#     
#         mayaviSizer = wx.BoxSizer(wx.VERTICAL)     
#         mayaviSizer.Add(self.plotMayavi, 1, wx.EXPAND)
#         self.mayaviPanel.SetSizer(mayaviSizer)  

        # Setup LOG 
        self.panelLog = wx.Panel( self.mainBook, wx.ID_ANY, wx.DefaultPosition, 
                                   wx.DefaultSize, wx.TAB_TRAVERSAL )

        self.mainBook.AddPage( self.panelLog, u"Log", False )
        
        style = wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL
        self.log = wx.TextCtrl(self.panelLog, wx.ID_ANY, size=(-1,-1),
                          style=style)
        self.log.SetBackgroundColour(wx.BLACK)
        self.log.SetForegroundColour(wx.GREEN)
        
        logSizer = wx.BoxSizer(wx.VERTICAL)     
        logSizer.Add(self.log, 1, wx.EXPAND)
        self.panelLog.SetSizer(logSizer) 
        
        self.log.Bind(wx.EVT_TEXT, self.saveLogData)
        
        bSizer1.Add( self.mainBook, 1, wx.EXPAND |wx.ALL, 5 )   
        
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnRightClickMenu)
        self.SetSizer( bSizer1 )
        self.Layout()
        self.Show(True)
        
    def saveLogData(self, evt):
            
        try:
            savefile = open(self.config.loggingFile_path,'w')
            savefile.write(self.log.GetValue())
            savefile.close()
        except:
            pass
        
    def clearLogData(self, evt):
        self.log.SetValue("")
        
    def onGoToDirectory(self, evt=None):
        '''
        Go to selected directory
        '''
        path = os.path.join(self.config.cwd, "logs")
        self.presenter.openDirectory(path=path)
        
    def saveLogDataAs(self, evt):
        dlg = wx.FileDialog(self, "Open Configuration File", wildcard = "*.log" ,
                           style=wx.FD_DEFAULT_STYLE | wx.FD_CHANGE_DIR)
        path = os.path.join(self.config.cwd, "logs", "ORIGAMI_logfile.log")
        dlg.SetPath(path)
        if dlg.ShowModal() == wx.ID_OK:
            fileName=dlg.GetPath()
            savefile = open(fileName,'w')
            savefile.write(self.log.GetValue())
            savefile.close()
        
    def OnRightClickMenu(self, evt):
        
        # Make bindings    
        self.Bind(wx.EVT_MENU, self.presenter.onSmooth1Ddata, id=ID_smooth1DdataMS)
        self.Bind(wx.EVT_MENU, self.presenter.onSmooth1Ddata, id=ID_smooth1DdataRT) 
        self.Bind(wx.EVT_MENU, self.presenter.onSmooth1Ddata, id=ID_smooth1Ddata1DT) 
        
        self.Bind(wx.EVT_MENU, self.presenter.onShowExtractedIons, id=ID_highlightRectAllIons) 
        self.Bind(wx.EVT_MENU, self.presenter.onPickPeaks, id=ID_pickMSpeaksDocument)
        
        self.Bind(wx.EVT_MENU, self.presenter.onClearPlot, id=ID_clearPlot_MS)
        self.Bind(wx.EVT_MENU, self.presenter.onClearPlot, id=ID_clearPlot_RT)
        self.Bind(wx.EVT_MENU, self.presenter.onClearPlot, id=ID_clearPlot_1D)
        self.Bind(wx.EVT_MENU, self.presenter.onClearPlot, id=ID_clearPlot_2D)
        self.Bind(wx.EVT_MENU, self.presenter.onClearPlot, id=ID_clearPlot_3D)
        self.Bind(wx.EVT_MENU, self.presenter.onClearPlot, id=ID_clearPlot_RMSF)
        self.Bind(wx.EVT_MENU, self.presenter.onClearPlot, id=ID_clearPlot_RMSD)
        self.Bind(wx.EVT_MENU, self.presenter.onClearPlot, id=ID_clearPlot_Matrix)
        self.Bind(wx.EVT_MENU, self.presenter.onClearPlot, id=ID_clearPlot_Overlay)
        self.Bind(wx.EVT_MENU, self.presenter.onClearPlot, id=ID_clearPlot_Watefall)
        self.Bind(wx.EVT_MENU, self.presenter.onClearPlot, id=ID_clearPlot_Calibration)
        self.Bind(wx.EVT_MENU, self.presenter.onClearPlot, id=ID_clearPlot_MZDT)
        
        self.Bind(wx.EVT_MENU, self.onSetupMenus, id=ID_plotPanel_binMS)
        
        self.Bind(wx.EVT_MENU, self.saveLogDataAs, id=ID_log_save_log)
        self.Bind(wx.EVT_MENU, self.onGoToDirectory, id=ID_log_go_to_directory)
        self.Bind(wx.EVT_MENU, self.clearLogData, id=ID_log_clear_window)

        
        saveImageLabel = ''.join(['Save figure (.', self.config.imageFormat,')'])
        saveAsImageLabel = ''.join(['Save as... (.', self.config.imageFormat,')'])
        
        self.currentPage = self.mainBook.GetPageText(self.mainBook.GetSelection())
        
        menu = wx.Menu()
        # MS
        if self.currentPage == "Log":
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_log_go_to_directory, 
                                         text="Go to folder with log files... ", 
                                         bitmap=self.icons.iconsLib['folder_path_16']))
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_log_save_log, 
                                         text="Save log to new file", 
                                         bitmap=self.icons.iconsLib['save16']))
            menu.AppendSeparator()
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_log_clear_window, 
                                         text="Clear current log file",
                                         bitmap=self.icons.iconsLib['clear_16']))
        elif self.currentPage == "MS":
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_processSettings_MS,
                                         text='Process mass spectrum...', 
                                         bitmap=self.icons.iconsLib['process_ms_16']))
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_processSettings_FindPeaks,
                                         text='Find peaks...', 
                                         bitmap=self.icons.iconsLib['process_fit_16']))
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_highlightRectAllIons,
                                         text='Show annotations', 
                                         bitmap=self.icons.iconsLib['annotate16']))
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_extraSettings_plot1D,
                                         text='Edit plot parameters...', 
                                         bitmap=self.icons.iconsLib['panel_plot1D_16']))
            menu.AppendSeparator()
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveMSImage, text=saveImageLabel, 
                                         bitmap=self.icons.iconsLib['save16']))
            menu.AppendSeparator()
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_clearPlot_MS, text="Clear plot", 
                                         bitmap=self.icons.iconsLib['clear_16']))
        elif self.currentPage == "RT":
            menu.Append(ID_smooth1DdataRT, "Smooth chromatogram")
            self.binMS_check =  menu.AppendCheckItem(ID_plotPanel_binMS, 
                                                     "Bin mass spectra during extraction",
                                                     help="")
            self.binMS_check.Check(self.config.ms_enable_in_RT)
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_processSettings_MS,
                                         text='Edit extraction parameters...', 
                                         bitmap=self.icons.iconsLib['process_ms_16']))
            menu.AppendSeparator()
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_extraSettings_plot1D,
                                         text='Edit plot parameters...', 
                                         bitmap=self.icons.iconsLib['panel_plot1D_16']))
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_extraSettings_legend,
                                         text='Edit legend parameters...', 
                                         bitmap=self.icons.iconsLib['panel_legend_16']))
            menu.AppendSeparator()
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveRTImage, text=saveImageLabel, 
                                         bitmap=self.icons.iconsLib['save16']))
            menu.AppendSeparator()
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_clearPlot_RT, text="Clear plot", 
                                         bitmap=self.icons.iconsLib['clear_16']))
        elif self.currentPage == "1D":
            menu.Append(ID_smooth1Ddata1DT, "Smooth mobiligram")
            self.binMS_check =  menu.AppendCheckItem(ID_plotPanel_binMS, 
                                                     "Bin mass spectra during extraction",
                                                     help="")
            self.binMS_check.Check(self.config.ms_enable_in_RT)
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_processSettings_MS,
                                         text='Edit extraction parameters...', 
                                         bitmap=self.icons.iconsLib['process_ms_16']))
            menu.AppendSeparator()
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_extraSettings_plot1D,
                                         text='Edit plot parameters...', 
                                         bitmap=self.icons.iconsLib['panel_plot1D_16']))
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_extraSettings_legend,
                                         text='Edit legend parameters...', 
                                         bitmap=self.icons.iconsLib['panel_legend_16']))
            menu.AppendSeparator()
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_save1DImage, text=saveImageLabel, 
                                         bitmap=self.icons.iconsLib['save16']))
            menu.AppendSeparator()
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_clearPlot_1D, text="Clear plot", 
                                         bitmap=self.icons.iconsLib['clear_16']))
        elif self.currentPage == "2D":
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_processSettings_2D,
                                         text='Process heatmap...', 
                                         bitmap=self.icons.iconsLib['process_2d_16']))
            menu.AppendSeparator()
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_extraSettings_plot2D,
                                         text='Edit plot parameters...', 
                                         bitmap=self.icons.iconsLib['panel_plot2D_16']))
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_extraSettings_colorbar,
                                         text='Edit colorbar parameters...', 
                                         bitmap=self.icons.iconsLib['panel_colorbar_16']))
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_extraSettings_legend,
                                         text='Edit legend parameters...', 
                                         bitmap=self.icons.iconsLib['panel_legend_16']))
            menu.AppendSeparator()
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_save2DImage, text=saveImageLabel, 
                                         bitmap=self.icons.iconsLib['save16']))
            menu.AppendSeparator()
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_clearPlot_2D, text="Clear plot", 
                                         bitmap=self.icons.iconsLib['clear_16']))
        elif self.currentPage == "DT/MS":
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_processSettings_2D,
                                         text='Process heatmap...', 
                                         bitmap=self.icons.iconsLib['process_2d_16']))
            menu.AppendSeparator()
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_extraSettings_plot2D,
                                         text='Edit plot parameters...', 
                                         bitmap=self.icons.iconsLib['panel_plot2D_16']))
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_extraSettings_colorbar,
                                         text='Edit colorbar parameters...', 
                                         bitmap=self.icons.iconsLib['panel_colorbar_16']))
            menu.AppendSeparator()
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveMZDTImage, text=saveImageLabel, 
                                         bitmap=self.icons.iconsLib['save16']))
            menu.AppendSeparator()
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_clearPlot_MZDT, text="Clear plot", 
                                         bitmap=self.icons.iconsLib['clear_16']))
        elif self.currentPage == "3D":
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_extraSettings_plot3D,
                                         text='Edit plot parameters...', 
                                         bitmap=self.icons.iconsLib['panel_plot3D_16']))
            menu.AppendSeparator()
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_save3DImage, text=saveImageLabel, 
                                         bitmap=self.icons.iconsLib['save16']))
            menu.AppendSeparator()
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_clearPlot_3D, text="Clear plot", 
                                         bitmap=self.icons.iconsLib['clear_16']))
        elif self.currentPage == "Overlay":
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_extraSettings_plot2D,
                                         text='Edit plot parameters...', 
                                         bitmap=self.icons.iconsLib['panel_plot2D_16']))
            menu.AppendSeparator()
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveOverlayImage, text=saveImageLabel, 
                                         bitmap=self.icons.iconsLib['save16']))
            menu.AppendSeparator()
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_clearPlot_Overlay, text="Clear plot", 
                                         bitmap=self.icons.iconsLib['clear_16']))
        elif self.currentPage == "Waterfall":
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveWaterfallImage, text=saveImageLabel, 
                                         bitmap=self.icons.iconsLib['save16']))
            menu.AppendSeparator()
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_clearPlot_Waterfall, text="Clear plot", 
                                         bitmap=self.icons.iconsLib['clear_16']))
        elif self.currentPage == "RMSF":
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_extraSettings_rmsd,
                                         text='Edit plot parameters...', 
                                         bitmap=self.icons.iconsLib['panel_rmsd_16']))
            menu.AppendSeparator()
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveRMSFImage, text=saveImageLabel, 
                                         bitmap=self.icons.iconsLib['save16']))
            menu.AppendSeparator()
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_clearPlot_RMSF, text="Clear plot", 
                                         bitmap=self.icons.iconsLib['clear_16']))
        elif self.currentPage == "Comparison":
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveRMSDmatrixImage, text=saveImageLabel, 
                                         bitmap=self.icons.iconsLib['save16']))
            menu.AppendSeparator()
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_clearPlot_Matrix, text="Clear plot", 
                                         bitmap=self.icons.iconsLib['clear_16']))
        elif self.currentPage == "Calibration":
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_clearPlot_Calibration, text="Clear plot", 
                                         bitmap=self.icons.iconsLib['clear_16']))
        else: 
            pass
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()
         
    def onSetupMenus(self, evt):
        
        evtID = evt.GetId()
        
        if evtID == ID_plotPanel_binMS:
            check_value = not self.config.ms_enable_in_RT
            self.config.ms_enable_in_RT = check_value
            if self.config.ms_enable_in_RT:
                args = ("Mass spectra will be binned when extracted from chromatogram and mobiligram windows", 4)
            else:
                args = ("Mass spectra will be not binned when extracted from chromatogram and mobiligram windows", 4)
            self.presenter.onThreading(evt, args, action='updateStatusbar')
         
    def OnAddDataToMZTable(self, evt):
        self.parent._mgr.GetPane(self.parent.panelMultipleIons).Show()
        self.parent._mgr.Update()
        xmin, xmax = self.getPlotExtent(evt=None)
        self.parent.panelMultipleIons.topP.peaklist.Append([round(xmin, 2),
                                                     round(xmax, 2),
                                                     ""])
    
    def OnExtractRTDT(self, evt):
        xmin, xmax, ymin, ymax = self.getPlotExtent(evt=None)
        
    def getPlotExtent(self, evt=None):
        self.currentPage = self.mainBook.GetPageText(self.mainBook.GetSelection())
        if self.currentPage == "MS":
            return self.plot1.plotMS.get_xlim()
        elif self.currentPage == "RT": pass
        elif self.currentPage == "1D": pass
        elif self.currentPage == "2D": 
            xmin, xmax = self.plot2D.plotMS.get_xlim()
            ymin, ymax = self.plot2D.plotMS.get_ylim()
            return round(xmin,0), round(xmax,0), round(ymin,0), round(ymax,0)
        elif self.currentPage == "": 
            xmin, xmax = self.plotMZDT.plotMS.get_xlim()
            ymin, ymax = self.plotMZDT.plotMS.get_ylim()
            return round(xmin,0), round(xmax,0), round(ymin,0), round(ymax,0)
        else: pass
        
    def onChangePlotStyle(self, evt, plot_style=None):
        
        # https://tonysyu.github.io/raw_content/matplotlib-style-gallery/gallery.html
        
        if self.config.currentStyle == "Default":
            matplotlib.rcParams.update(matplotlib.rcParamsDefault)
        elif self.config.currentStyle == "ggplot":
            plt.style.use('ggplot')
        elif self.config.currentStyle == "ticks":
            sns.set_style('ticks')
        else:
            plt.style.use(self.config.currentStyle)
        
# plots

    def on_plot_MS(self, msX=None, msY=None, xlimits=None, override=True, replot=False,
                   full_repaint=False, e=None):
        
        if replot:
            msX, msY, xlimits = self.presenter._get_replot_data('MS')
            if msX is None or msY is None:
                return
        
        # Build kwargs
        plt_kwargs = self.presenter._buildPlotParameters(plotType='1D')
        
        if not full_repaint:
            try:
                self.plot1.plot_1D_update_data(msX, msY, "m/z", "Intensity", **plt_kwargs)
                self.plot1.repaint()
                if override:
                    self.config.replotData['MS'] = {'xvals':msX, 'yvals':msY, 'xlimits':xlimits}
                    
                return
            except:
                pass
         
        
        self.plot1.clearPlot()
        self.plot1.plot_1D(xvals=msX, 
                           yvals=msY, 
                           xlimits=xlimits,
                           xlabel="m/z", ylabel="Intensity",
                           axesSize=self.config._plotSettings['MS']['axes_size'],
                           plotType='MS',
                           **plt_kwargs)
        # Show the mass spectrum
        self.plot1.repaint()
        
        if override:
            self.config.replotData['MS'] = {'xvals':msX, 'yvals':msY, 'xlimits':xlimits}
        
    def on_plot_1D(self, dtX=None, dtY=None, xlabel=None, color=None, override=True, 
                   full_repaint=False, replot=False, e=None):
               
        if replot:
            dtX, dtY, xlabel = self.presenter._get_replot_data('1D')
            if dtX is None or dtY is None or xlabel is None:
                return
               
        # get kwargs
        plt_kwargs = self.presenter._buildPlotParameters(plotType='1D')
        
        if not full_repaint:
            try:
                self.plot1D.plot_1D_update_data(dtX, dtY, xlabel, "Intensity", **plt_kwargs)
                self.plot1D.repaint()
                if override:
                    self.config.replotData['1D'] = {'xvals':dtX, 'yvals':dtY, 'xlabel':xlabel}
                    return
            except:
                pass
        
        self.plot1D.clearPlot()     
        self.plot1D.plot_1D(xvals=dtX,
                            yvals=dtY, 
                            xlabel=xlabel, 
                            ylabel="Intensity",
                            axesSize=self.config._plotSettings['DT']['axes_size'],
                            plotType='1D',
                            **plt_kwargs)
        # show the plot
        self.plot1D.repaint()
        
        if override:
            self.config.replotData['1D'] = {'xvals':dtX, 'yvals':dtY, 'xlabel':xlabel}

    def on_plot_RT(self, rtX=None, rtY=None, xlabel=None, ylabel="Intensity", color=None, override=True, 
                  replot=False, full_repaint=False, e=None):
        
        if replot:
            rtX, rtY, xlabel = self.presenter._get_replot_data('RT')
            if rtX is None or rtY is None or xlabel is None:
                return
        
        # Build kwargs
        plt_kwargs = self.presenter._buildPlotParameters(plotType='1D')
        
        if not full_repaint:
            try:
                self.plotRT.plot_1D_update_data(rtX, rtY, xlabel, ylabel, **plt_kwargs)
                self.plotRT.repaint()
                if override:
                    self.config.replotData['RT'] = {'xvals':rtX, 'yvals':rtY, 'xlabel':xlabel}
                    return
            except:
                pass
        
        self.plotRT.clearPlot()
        self.plotRT.plot_1D(xvals=rtX,yvals=rtY, xlabel=xlabel, ylabel=ylabel,
                            axesSize=self.config._plotSettings['RT']['axes_size'],
                            plotType='1D',
                            **plt_kwargs)
        # Show the mass spectrum
        self.plotRT.repaint()
        
        if override:
            self.config.replotData['RT'] = {'xvals':rtX, 
                                            'yvals':rtY, 
                                            'xlabel':xlabel}
        
    def plot_2D_update(self, plotName='all', evt=None):
        plt_kwargs = self.presenter._buildPlotParameters(plotType='2D')

        if plotName in ['all', '2D']:
            try:
                self.plot2D.plot_2D_update(**plt_kwargs)
                self.plot2D.repaint()
            except AttributeError: pass
        
        if plotName in ['all', 'DT/MS']:
            try:
                self.plotMZDT.plot_2D_update(**plt_kwargs)
                self.plotMZDT.repaint()
            except AttributeError: pass
        
    def on_plot_2D_data(self, data=None, **kwargs):
        """
        This function plots IMMS data in relevant windows.
        Input format: zvals, xvals, xlabel, yvals, ylabel
        """
        if isempty(data[0]):
                dlgBox(exceptionTitle='Missing data',
                       exceptionMsg= "Missing data. Cannot plot 2D plots.",
                       type="Error")
                return
        else: pass       
        
        # Unpack data
        if len(data) == 5:
            zvals, xvals, xlabel, yvals, ylabel = data
        elif len(data) == 6:
            zvals, xvals, xlabel, yvals, ylabel, cmap = data
                
        # Check and change colormap if necessary
        cmapNorm = self.presenter.onCmapNormalization(zvals,
                                                      min=self.config.minCmap, 
                                                      mid=self.config.midCmap,
                                                      max=self.config.maxCmap)

        # Plot data 
        self.on_plot_2D(zvals, xvals, yvals, xlabel, ylabel, cmapNorm=cmapNorm)
        if self.config.waterfall:
            self.on_plot_waterfall(yvals=xvals, xvals=yvals, zvals=zvals, 
                                   xlabel=xlabel, ylabel=ylabel)  
        self.on_plot_3D(zvals=zvals, labelsX=xvals, labelsY=yvals, 
                         xlabel=xlabel, ylabel=ylabel, zlabel='Intensity')
        
    def on_plot_2D(self, zvals=None, xvals=None, yvals=None, xlabel=None, 
                     ylabel=None, cmap=None, cmapNorm=None, plotType=None, 
                     override=True, replot=False, e=None):
        
                    
        # If the user would like to replot data, you can directly unpack it
        if replot:
            zvals, xvals, yvals, xlabel, ylabel = self.presenter._get_replot_data('2D')
            if zvals is None or xvals is None or yvals is None:
                return

        # Update values
        self.presenter.getXYlimits2D(xvals, yvals, zvals)

        # Check if cmap should be overwritten
        if self.config.useCurrentCmap: 
            cmap = self.config.currentCmap
            
        # Check that cmap modifier is included
        if cmapNorm==None and plotType != "RMSD":
            cmapNorm = self.presenter.onCmapNormalization(zvals, 
                                                          min=self.config.minCmap, 
                                                          mid=self.config.midCmap, 
                                                          max=self.config.maxCmap,
                                                          )
            
        elif cmapNorm==None and plotType == "RMSD":
            cmapNorm = self.presenter.onCmapNormalization(zvals, 
                                                          min=-100, mid=0, max=100,
                                                          )
        
        # Build kwargs
        plt_kwargs = self.presenter._buildPlotParameters(plotType='2D')
        plt_kwargs['colormap'] = cmap
        plt_kwargs['colormap_norm'] = cmapNorm
        
        try:
            self.plot2D.plot_2D_update_data(xvals, yvals, xlabel, ylabel, zvals,
                                            **plt_kwargs)
            self.plot2D.repaint()
            if override:
                self.config.replotData['2D'] = {'zvals':zvals, 'xvals':xvals,
                                                'yvals':yvals, 'xlabels':xlabel,
                                                'ylabels':ylabel, 'cmap':cmap,
                                                'cmapNorm':cmapNorm}
            return
        except:
            pass
        
        # Plot 2D dataset
        self.plot2D.clearPlot() 
        if self.config.plotType == 'Image':
            self.plot2D.plot_2D_surface(zvals, xvals, yvals, xlabel, ylabel,
                                        axesSize=self.config._plotSettings['2D']['axes_size'],
                                        plotName='2D',
                                        **plt_kwargs)
             
        elif self.config.plotType == 'Contour':
            self.plot2D.plot_2D_contour(zvals, xvals, yvals, xlabel, ylabel,
                                        axesSize=self.config._plotSettings['2D']['axes_size'],
                                        plotName='2D',
                                        **plt_kwargs)
 
        self.plot2D.repaint()
        if override:
            self.config.replotData['2D'] = {'zvals':zvals, 'xvals':xvals,
                                            'yvals':yvals, 'xlabels':xlabel,
                                            'ylabels':ylabel, 'cmap':cmap,
                                            'cmapNorm':cmapNorm}
            
        # update plot data
        self.presenter.view._onUpdatePlotData(plot_type='2D')
        
    def on_plot_MSDT(self, zvals=None, xvals=None, yvals=None, xlabel=None, ylabel=None, 
                     cmap=None, cmapNorm=None, plotType=None,  override=True, replot=False, e=None):
        
        
        # If the user would like to replot data, you can directly unpack it
        if replot:
            zvals, xvals, yvals, xlabel, ylabel = self.presenter._get_replot_data('DT/MS')
            if zvals is None or xvals is None or yvals is None:
                return
        
        # Check if cmap should be overwritten
        if self.config.useCurrentCmap:
            cmap = self.config.currentCmap
        elif cmap == None:
            cmap = self.config.currentCmap
            
        # Check that cmap modifier is included
        if cmapNorm==None:
            cmapNorm = self.presenter.onCmapNormalization(zvals, 
                                                min=self.config.minCmap, 
                                                mid=self.config.midCmap, 
                                                max=self.config.maxCmap,
                                                )

        # Build kwargs
        plt_kwargs = self.presenter._buildPlotParameters(plotType='2D')
        plt_kwargs['colormap'] = cmap
        plt_kwargs['colormap_norm'] = cmapNorm

        # Plot 2D dataset
        self.plotMZDT.clearPlot() 
        if self.config.plotType == 'Image':
            self.plotMZDT.plot_2D_surface(zvals, xvals, yvals, xlabel, ylabel,
                                                          axesSize=self.config._plotSettings['DT/MS']['axes_size'],
                                                          plotName='MSDT',
                                                          **plt_kwargs)
            
        elif self.config.plotType == 'Contour':
            self.plotMZDT.plot_2D_contour(zvals, xvals, yvals, xlabel, ylabel,
                                                          axesSize=self.config._plotSettings['DT/MS']['axes_size'],
                                                          plotName='MSDT',
                                                          **plt_kwargs)

        # Show the mass spectrum
        self.plotMZDT.repaint()
                
        if override:
            self.config.replotData['DT/MS'] = {'zvals':zvals, 'xvals':xvals,
                                              'yvals':yvals, 'xlabels':xlabel,
                                              'ylabels':ylabel, 'cmap':cmap,
                                              'cmapNorm':cmapNorm}
        # update plot data
        self.presenter.view._onUpdatePlotData(plot_type='DT/MS')
        
    def on_plot_3D(self, zvals=None, labelsX=None, labelsY=None, 
                    xlabel="", ylabel="", zlabel="Intensity",cmap='inferno', 
                    cmapNorm=None, replot=False, e=None):
        
        plt1d_kwargs = self.presenter._buildPlotParameters(plotType='1D')
        plt3d_kwargs = self.presenter._buildPlotParameters(plotType='3D')
        plt_kwargs = merge_two_dicts(plt1d_kwargs, plt3d_kwargs)
        
        # If the user would like to replot data, you can directly unpack it
        if replot:
            zvals, labelsX, labelsY, xlabel, ylabel = self.presenter._get_replot_data('2D')
            if zvals is None or labelsX is None or labelsY is None:
                return
        # Check if cmap should be overwritten
        if self.config.useCurrentCmap:
            cmap = self.config.currentCmap
            
        # Check that cmap modifier is included
        if cmapNorm==None:
            cmapNorm = self.presenter.onCmapNormalization(zvals, 
                                                          min=self.config.minCmap, 
                                                          mid=self.config.midCmap, 
                                                          max=self.config.maxCmap,
                                                          )
        # add to kwargs    
        plt_kwargs['colormap'] = cmap
        plt_kwargs['colormap_norm'] = cmapNorm
        
        self.plot3D.clearPlot()
        if self.config.plotType_3D == 'Surface':
            self.plot3D.plot_3D_surface(xvals=labelsX,
                                        yvals=labelsY,
                                        zvals=zvals, 
                                        title="",  
                                        xlabel=xlabel, 
                                        ylabel=ylabel,
                                        zlabel=zlabel,
                                        axesSize=self.config._plotSettings['3D']['axes_size'],
                                        **plt_kwargs)
        elif self.config.plotType_3D == 'Wireframe':
            self.plot3D.plot_3D_wireframe(xvals=labelsX,
                                        yvals=labelsY,
                                        zvals=zvals, 
                                        title="",  
                                        xlabel=xlabel, 
                                        ylabel=ylabel,
                                        zlabel=zlabel,
                                        axesSize=self.config._plotSettings['3D']['axes_size'],
                                        **plt_kwargs)
        # Show the mass spectrum
        self.plot3D.repaint() 
        
    def on_plot_waterfall(self, xvals, yvals, zvals, xlabel, ylabel,e=None):

        # Check if cmap should be overwritten
        if self.config.useCurrentCmap:
            cmap = self.config.currentCmap
        
        plt_kwargs = self.presenter._buildPlotParameters(plotType='1D')
        waterfall_kwargs = self.presenter._buildPlotParameters(plotType='waterfall')
        plt_kwargs = merge_two_dicts(plt_kwargs, waterfall_kwargs)
        plt_kwargs['colormap'] = cmap

        self.plotWaterfallIMS.clearPlot()
        self.plotWaterfallIMS.plot_1D_waterfall(xvals=xvals, yvals=yvals,
                                                zvals=zvals, label="", 
                                                xlabel=xlabel, 
                                                ylabel=ylabel,
                                                axesSize=self.config._plotSettings['Waterfall']['axes_size'],
                                                plotName='1D',
                                                **plt_kwargs)
    
        # Show the mass spectrum
        self.plotWaterfallIMS.repaint() 
       
    def plot_1D_waterfall_update(self):
        plt_kwargs = self.presenter._buildPlotParameters(plotType='1D')
        waterfall_kwargs = self.presenter._buildPlotParameters(plotType='waterfall')
        plt_kwargs = merge_two_dicts(plt_kwargs, waterfall_kwargs)
        plt_kwargs['colormap'] = self.config.currentCmap
        
        self.plotWaterfallIMS.plot_1D_waterfall_update(**plt_kwargs)
        self.plotWaterfallIMS.repaint()
        
    def on_plot_RMSDF(self, yvalsRMSF, zvals, xvals=None, yvals=None, xlabelRMSD=None,
                      ylabelRMSD=None, ylabelRMSF=None, color='blue', cmapNorm=None,
                      cmap='inferno', plotType=None, override=True, replot=False,
                      e=None):
        """
        Plot RMSD and RMSF plots together in panel RMSD
        """
        
        plt_kwargs = self.presenter._buildPlotParameters(plotType='2D')
        rmsd_kwargs = self.presenter._buildPlotParameters(plotType='RMSF')
        plt_kwargs = merge_two_dicts(plt_kwargs, rmsd_kwargs)
        
        # If the user would like to replot data, you can directly unpack it
        if replot:
            zvals, xvals, yvals, xlabelRMSD, ylabelRMSD, ylabelRMSF = self.presenter._get_replot_data('RMSF')
            if zvals is None or xvals is None or yvals is None:
                return
        
        # Update values
        self.presenter.getXYlimits2D(xvals, yvals, zvals)
    
        if self.config.useCurrentCmap:
            cmap = self.config.currentCmap
            
        if cmapNorm==None and plotType == "RMSD":
            cmapNorm = self.presenter.onCmapNormalization(zvals, min=-100, mid=0, max=100)
        
        # update kwargs    
        plt_kwargs['colormap'] = cmap
        plt_kwargs['colormap_norm'] = cmapNorm
        
        self.plotRMSF.clearPlot()
        self.plotRMSF.plot_1D_2D(yvalsRMSF=yvalsRMSF, 
                                                 zvals=zvals, 
                                                 labelsX=xvals, 
                                                 labelsY=yvals,
                                                 xlabelRMSD=xlabelRMSD,
                                                 ylabelRMSD=ylabelRMSD,
                                                 ylabelRMSF=ylabelRMSF,
                                                 label="", zoom="box",
                                                 plotName='RMSF',
                                                 **plt_kwargs)
        self.plotRMSF.repaint()
        self.rmsdfFlag = False
                    
        if override:
            self.config.replotData['RMSF'] = {'zvals':zvals, 'xvals':xvals, 'yvals':yvals, 
                                              'xlabelRMSD':xlabelRMSD, 'ylabelRMSD':ylabelRMSD,
                                              'ylabelRMSF':ylabelRMSF,
                                              'cmapNorm':cmapNorm}
            
        self.presenter.view._onUpdatePlotData(plot_type='RMSF')

    def on_plot_RMSD(self, zvals=None, xvals=None, yvals=None, xlabel=None, 
                   ylabel=None, cmap=None, cmapNorm=None, plotType=None, 
                   override=True, replot=False, e=None):
        self.plotRMSF.clearPlot()
                    
        # If the user would like to replot data, you can directly unpack it
        if replot:
            zvals, xvals, yvals, xlabel, ylabel = self.presenter._get_replot_data('2D')
            if zvals is None or xvals is None or yvals is None:
                return

        # Update values
        self.presenter.getXYlimits2D(xvals, yvals, zvals)

        # Check if cmap should be overwritten
        if self.config.useCurrentCmap: 
            cmap = self.config.currentCmap
            
        # Check that cmap modifier is included
        if cmapNorm==None and plotType == "RMSD":
            cmapNorm = self.presenter.onCmapNormalization(zvals, min=-100, mid=0, max=100)
        
        # Build kwargs
        plt_kwargs = self.presenter._buildPlotParameters(plotType='2D')
        plt_kwargs['colormap'] = cmap
        plt_kwargs['colormap_norm'] = cmapNorm
        
        # Plot 2D dataset 
        if self.config.plotType == 'Image':
            self.plotRMSF.plot_2D_surface(zvals, xvals, yvals, xlabel, ylabel,
                                                        axesSize=self.config._plotSettings['2D']['axes_size'],
                                                        plotName='RMSD',
                                                        **plt_kwargs)
        elif self.config.plotType == 'Contour':
            self.plotRMSF.plot_2D_contour(zvals, xvals, yvals, xlabel, ylabel,
                                                        axesSize=self.config._plotSettings['2D']['axes_size'],
                                                        plotName='RMSD',
                                                        **plt_kwargs)

        # Show the mass spectrum
        self.plotRMSF.repaint()
        
        if override:
            self.config.replotData['2D'] = {'zvals':zvals, 'xvals':xvals,
                                            'yvals':yvals, 'xlabels':xlabel,
                                            'ylabels':ylabel, 'cmap':cmap,
                                            'cmapNorm':cmapNorm}
            
        # update plot data
        self.presenter.view._onUpdatePlotData(plot_type='2D')
        
    def plot_2D_update_label(self):
        
        try:
            if self.plotRMSF.plot_name == 'RMSD':
                zvals, xvals, yvals, xlabel, ylabel = self.presenter._get_replot_data('2D')
            elif self.plotRMSF.plot_name == 'RMSF':
                zvals, xvals, yvals, xlabelRMSD, ylabelRMSD, ylabelRMSF = self.presenter._get_replot_data('RMSF')
            else:
                return
            
            plt_kwargs = self.presenter._buildPlotParameters(plotType='RMSF')
            rmsdXpos, rmsdYpos = self.presenter.onCalculateRMSDposition(xlist=xvals, ylist=yvals)
            
            plt_kwargs['rmsd_label_coordinates'] = [rmsdXpos, rmsdYpos]
            plt_kwargs['rmsd_label_color'] = self.config.rmsd_color
            
            
            self.plotRMSF.plot_2D_update_label(**plt_kwargs)
            self.plotRMSF.repaint()
        except:
            pass

    def plot_2D_matrix_update_label(self):
        plt_kwargs = self.presenter._buildPlotParameters(plotType='RMSF')
        
        try:
            self.plotCompare.plot_2D_matrix_update_label(**plt_kwargs)
            self.plotCompare.repaint()
        except:
            pass
        
    def on_plot_matrix(self, zvals=None, xylabels=None, cmap=None, override=True, replot=False, e=None):

       # If the user would like to replot data, you can directly unpack it
        if replot:
            zvals, xylabels, cmap = self.presenter._get_replot_data('Matrix')
            if zvals is None or xylabels is None or cmap is None:
                return

        # Check if cmap should be overwritten
        if self.config.useCurrentCmap:
            cmap = self.config.currentCmap
        
        plt_kwargs = self.presenter._buildPlotParameters(plotType='2D')
        rmsd_kwargs = self.presenter._buildPlotParameters(plotType='RMSF')
        plt_kwargs = merge_two_dicts(plt_kwargs, rmsd_kwargs)
        plt_kwargs['colormap'] = cmap
        
        self.plotCompare.clearPlot()
        self.plotCompare.plot_2D_matrix(zvals=zvals, xylabels=xylabels, 
                                        xNames=None, 
                                        axesSize=self.config._plotSettings['Comparison']['axes_size'],
                                        plotName='2D',
                                        **plt_kwargs)
        self.plotCompare.repaint()

        plt_kwargs = self.presenter._buildPlotParameters(plotType='3D')
        rmsd_kwargs = self.presenter._buildPlotParameters(plotType='RMSF')
        plt_kwargs = merge_two_dicts(plt_kwargs, rmsd_kwargs)
        plt_kwargs['colormap'] = cmap
        
        self.plot3D.clearPlot()
        self.plot3D.plot_3D_bar(xvals=None, yvals=None, xylabels=xylabels, 
                                zvals=zvals, title="", xlabel="", ylabel="",
                                axesSize=self.config._plotSettings['3D']['axes_size'],
                                **plt_kwargs)
        self.plot3D.repaint()
        
        if override:
            self.config.replotData['Matrix'] = {'zvals':zvals, 
                                                'xylabels':xylabels,
                                                'cmap':cmap}
        

        
        
        
        
        
        
        