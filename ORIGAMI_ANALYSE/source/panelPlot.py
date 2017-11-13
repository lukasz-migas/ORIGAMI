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
import plot1d as plot1d
import plot2d as plot2d
import plot3d as plot3d
# from plot3d import plot3D 
# from plot3d import MayaviPanel
import plot_MSandCIU as plotMSCIU
import numpy as np
from ids import *
import matplotlib
from matplotlib import interactive
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import seaborn as sns

class panelPlot ( wx.Panel ):
    def __init__( self, parent, config, presenter):
        wx.Panel.__init__ ( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition,
                             size = wx.Size( 800,600 ), style = wx.TAB_TRAVERSAL )
        
        self.config = config
        self.parent = parent
        self.presenter = presenter
        self.currentPage = None
        #Extract size of screen
        self.displaysize = wx.GetDisplaySize()
        self.SetDimensions(0,0,self.displaysize[0]-320,self.displaysize[1]-50)
        self.displaysizeMM = wx.GetDisplaySizeMM()

        self.displayRes = (wx.GetDisplayPPI())
        self.figsizeX = (self.displaysize[0]-320)/self.displayRes[0]
        self.figsizeY = (self.displaysize[1]-70)/self.displayRes[1]

        self.makeNotebook()

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
        self.plot1 = plot1d.plot1D(self.panelMS, figsize = figsize, config = self.config)
        
        box1 = wx.BoxSizer(wx.VERTICAL)
        box1.Add(self.plot1, 1, wx.EXPAND)
        self.panelMS.SetSizer(box1)
        
        # Setup PLOT RT
        self.panelRT = wx.Panel( self.mainBook, wx.ID_ANY, wx.DefaultPosition, 
                                   wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.mainBook.AddPage( self.panelRT, u"RT", False )        
        figsize = (self.figsizeX, 2)
        self.plotRT = plot1d.plot1D(self.panelRT, figsize = figsize, config = self.config)

        box12 = wx.BoxSizer(wx.VERTICAL)
        box12.Add(self.plotRT, 1, wx.EXPAND)
        self.panelRT.SetSizer(box12)
        
        # Setup PLOT 1D 
        self.panel1D = wx.Panel( self.mainBook, wx.ID_ANY, wx.DefaultPosition, 
                                   wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.mainBook.AddPage( self.panel1D, u"1D", False )        
        figsize = (self.figsizeX, 2)
        self.plot1D = plot1d.plot1D(self.panel1D, figsize = figsize, config = self.config)

        box1 = wx.BoxSizer(wx.VERTICAL)
        box1.Add(self.plot1D, 1, wx.EXPAND)
        self.panel1D.SetSizer(box1)
          
        # Setup PLOT 2D
        self.panel2D = wx.Panel( self.mainBook, wx.ID_ANY, wx.DefaultPosition, 
                                   wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.mainBook.AddPage( self.panel2D, u"2D", False )
        figsize = (self.figsizeX, 4)  
        self.plot2D = plot2d.plot2D(self.panel2D, config = self.config) 
        
        box14 = wx.BoxSizer(wx.HORIZONTAL)
        box14.Add(self.plot2D, 1, wx.EXPAND | wx.ALL)
        self.panel2D.SetSizerAndFit(box14)         
        
        # Setup PLOT DT/MS
        self.panelMZDT = wx.Panel( self.mainBook, wx.ID_ANY, wx.DefaultPosition, 
                                   wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.mainBook.AddPage( self.panelMZDT, u"DT/MS", False )
        figsize = (self.figsizeX, 4)  
        self.plotMZDT = plot2d.plot2D(self.panelMZDT, config = self.config) 
          
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
        self.plotWaterfallIMS = plot1d.plot1D(self.waterfallIMS, figsize = figsize, 
                                              config = self.config)
        
        box15 = wx.BoxSizer(wx.HORIZONTAL)
        box15.Add(self.plotWaterfallIMS, 1, wx.EXPAND | wx.ALL)
        self.waterfallIMS.SetSizerAndFit(box15)     

        # Setup PLOT 3D
        self.m_panel13 = wx.Panel( self.mainBook, wx.ID_ANY, wx.DefaultPosition, 
                                   wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.mainBook.AddPage( self.m_panel13, u"3D", False )
        self.plot3D = plot3d.plot3D(self.m_panel13, config = self.config)

        plotSizer = wx.BoxSizer(wx.VERTICAL)     
        plotSizer.Add(self.plot3D, 1, wx.EXPAND)
        self.m_panel13.SetSizer(plotSizer)  
                
#         # Setup PLOT RMSD
#         self.m_panel16 = wx.Panel( self.mainBook, wx.ID_ANY, wx.DefaultPosition, 
#                                    wx.DefaultSize, wx.TAB_TRAVERSAL )
#         self.mainBook.AddPage( self.m_panel16, u"RMSD", False )
#         self.plotRMSD = plot2d.plot2D(self.m_panel16, config = self.config)
#   
#         plotSizer2 = wx.BoxSizer(wx.VERTICAL)     
#         plotSizer2.Add(self.plotRMSD, 1, wx.EXPAND)
#         self.m_panel16.SetSizer(plotSizer2)  
        
        # Setup PLOT RMSF
        self.panelRMSF = wx.Panel( self.mainBook, wx.ID_ANY, wx.DefaultPosition, 
                                   wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.mainBook.AddPage( self.panelRMSF, u"RMSF", False )
        self.plotRMSF = plot1d.plot1D(self.panelRMSF, figsize = figsize, 
                                      config = self.config)

        plotSizer5 = wx.BoxSizer(wx.VERTICAL)     
        plotSizer5.Add(self.plotRMSF, 1, wx.EXPAND)
        self.panelRMSF.SetSizer(plotSizer5)  
        
        
        # Setup PLOT Comparison
        self.m_panel17 = wx.Panel( self.mainBook, wx.ID_ANY, wx.DefaultPosition, 
                                   wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.mainBook.AddPage( self.m_panel17, u"Comparison", False )
        self.plotCompare = plot2d.plot2D(self.m_panel17, config = self.config)

        
        plotSizer3 = wx.BoxSizer(wx.VERTICAL)     
        plotSizer3.Add(self.plotCompare, 1, wx.EXPAND)
        self.m_panel17.SetSizer(plotSizer3)  
        
        
        # Setup PLOT Overlay
        self.panelOverlay = wx.Panel( self.mainBook, wx.ID_ANY, wx.DefaultPosition, 
                                   wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.mainBook.AddPage( self.panelOverlay, u"Overlay", False )
        self.plotOverlay = plot2d.plot2D(self.panelOverlay, config = self.config)

        
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
        self.topPlotMS = plot1d.plot1D(self.topPanelMS, figsize = figsize, config = self.config)
        boxTopPanelMS = wx.BoxSizer(wx.VERTICAL)
        boxTopPanelMS.Add(self.topPlotMS, 1, wx.EXPAND)
        self.topPanelMS.SetSizer(boxTopPanelMS)
        
        # Plot 1DT
        self.bottomPlot1DT = plot1d.plot1D(self.bottomPanel1DT, figsize = figsize, config = self.config)
        boxBottomPanel1DT = wx.BoxSizer(wx.VERTICAL)
        boxBottomPanel1DT.Add(self.bottomPlot1DT, 1, wx.EXPAND)
        self.bottomPanel1DT.SetSizer(boxBottomPanel1DT)
        
        # Plot MAYAVI
#         self.mayaviPanel = wx.Panel( self.mainBook, wx.ID_ANY, wx.DefaultPosition, 
#                                    wx.DefaultSize, wx.TAB_TRAVERSAL )
#         self.mainBook.AddPage( self.mayaviPanel, u"Mayavi", False )
#          
#         self.MV = plot3d.MayaviPanel()
#         self.plotMayavi = self.MV.edit_traits(parent=self.mayaviPanel, 
#                                               kind='subpanel').control
#  
#         mayaviSizer = wx.BoxSizer(wx.VERTICAL)     
#         mayaviSizer.Add(self.plotMayavi, 1, wx.EXPAND)
#         self.mayaviPanel.SetSizer(mayaviSizer)  

        # Setup LOG 
        self.panelLog = wx.Panel( self.mainBook, wx.ID_ANY, wx.DefaultPosition, 
                                   wx.DefaultSize, wx.TAB_TRAVERSAL )

        self.mainBook.AddPage( self.panelLog, u"ORIGAMI Log", False )
        
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
        fileName = ''.join(['ORIGAMI_log__',self.config.startTime,'.log'])
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
        
        saveImageLabel = ''.join(['Save figure (.', self.config.imageFormat,')'])
        saveAsImageLabel = ''.join(['Save as... (.', self.config.imageFormat,')'])
        
        self.currentPage = self.mainBook.GetPageText(self.mainBook.GetSelection())
        
        menu = wx.Menu()
        # MS
        if self.currentPage == "MS":
            menu.Append(ID_smooth1DdataMS, "Smooth MS")
            menu.Append(ID_pickMSpeaksDocument, 'Find peaks\tAlt+F')
            menu.Append(ID_highlightRectAllIons, "Show annotations")
            menu.AppendSeparator()
            menu.Append(ID_saveMSImage, saveImageLabel)
            menu.AppendSeparator()
            menu.Append(ID_clearPlot_MS, "Clear plot")
        elif self.currentPage == "RT":
            menu.Append(ID_smooth1DdataRT, "Smooth RT")
            menu.AppendSeparator()
            menu.Append(ID_saveRTImage, saveImageLabel)
            menu.AppendSeparator()
            menu.Append(ID_clearPlot_RT, "Clear plot")
        elif self.currentPage == "1D":
            menu.Append(ID_smooth1Ddata1DT, "Smooth DT")
            menu.AppendSeparator()
            menu.Append(ID_save1DImage, saveImageLabel)
            menu.AppendSeparator()
            menu.Append(ID_clearPlot_1D, "Clear plot")
        elif self.currentPage == "2D":
            menu.Append(ID_save2DImage, saveImageLabel)
            menu.AppendSeparator()
            menu.Append(ID_clearPlot_2D, "Clear plot")
        elif self.currentPage == "DT/MS":
            menu.Append(ID_saveMZDTImage, saveImageLabel)
            menu.AppendSeparator()
            menu.Append(ID_clearPlot_MZDT, "Clear plot")
        elif self.currentPage == "3D": 
            menu.Append(ID_save3DImage, saveImageLabel)
            menu.AppendSeparator()
            menu.Append(ID_clearPlot_3D, "Clear plot")
            # Should be able to set the view to certain position
            # Replot in case of change of colormap or out of view
        elif self.currentPage == "Overlay": 
            menu.Append(ID_saveOverlayImage, saveImageLabel)
            menu.AppendSeparator()
            menu.Append(ID_clearPlot_Overlay, "Clear plot")
        elif self.currentPage == "Waterfall": 
            menu.Append(ID_saveWaterfallImage, saveImageLabel)
            menu.AppendSeparator()
            menu.Append(ID_clearPlot_Waterfall, "Clear plot")
        elif self.currentPage == "RMSF": 
            menu.Append(ID_saveRMSFImage, saveImageLabel)
            menu.AppendSeparator()
            menu.Append(ID_clearPlot_RMSF, "Clear plot")
        elif self.currentPage == "Comparison": 
            menu.Append(ID_saveRMSDmatrixImage, saveImageLabel)
            menu.AppendSeparator()
            menu.Append(ID_clearPlot_Matrix, "Clear plot")
        elif self.currentPage == "Calibration":
            menu.Append(ID_clearPlot_Calibration, "Clear plot")
        else: 
            pass
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()
         
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
        else: pass
        
    def onChangePlotStyle(self, evt):
        
        # Good source of info on styles:
        # https://tonysyu.github.io/raw_content/matplotlib-style-gallery/gallery.html
        self.config.currentStyle = self.parent.panelControls.StyleSelect.GetStringSelection()
        
        if self.config.currentStyle == "Default":
            matplotlib.rcParams.update(matplotlib.rcParamsDefault)
        elif self.config.currentStyle == "ggplot":
            plt.style.use('ggplot')
        elif self.config.currentStyle == "ticks":
            sns.set_style('ticks')
        else:
            plt.style.use(self.config.currentStyle)
        
#     def __del__( self ):
#          pass
     

        