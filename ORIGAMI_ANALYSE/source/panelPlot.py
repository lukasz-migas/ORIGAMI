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
from toolbox import isempty, merge_two_dicts, convertRGB1to255, convertRGB255to1, dir_extra
from dialogs import dlgBox, panelCustomisePlot
import numpy as np
import time 
import math


class panelPlot ( wx.Panel ):
    def __init__( self, parent, config, presenter):
        wx.Panel.__init__ ( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition,
                             size = wx.Size( 800, 600 ), style = wx.TAB_TRAVERSAL )
        
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
        elif self.currentPage in ['2D', 'DT/MS', 'Waterfall', 'RMSF', 'Comparison', 'Overlay', 'UniDec']:
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

        dpi = wx.ScreenDC().GetPPI()
        
		# Setup notebook
        self.mainBook = wx.Notebook( self, wx.ID_ANY, wx.DefaultPosition,
                                         wx.DefaultSize, 0 )
        # Setup PLOT MS
        self.panelMS = wx.Panel( self.mainBook, wx.ID_ANY, wx.DefaultPosition,
                                    wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.mainBook.AddPage( self.panelMS, u"MS", False )
        
        figsize = self.config._plotSettings["MS"]['gui_size']
        self.plot1 = plots.plots(self.panelMS, figsize=figsize, config=self.config)
        
        box1 = wx.BoxSizer(wx.VERTICAL)
        box1.Add(self.plot1, 1, wx.EXPAND)
        self.panelMS.SetSizer(box1)
        
        # Setup PLOT RT
        self.panelRT = wx.Panel( self.mainBook, wx.ID_ANY, wx.DefaultPosition, 
                                   wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.mainBook.AddPage( self.panelRT, u"RT", False )        

        figsize = self.config._plotSettings["RT"]['gui_size']
        self.plotRT = plots.plots(self.panelRT, figsize=figsize, config=self.config)

        box12 = wx.BoxSizer(wx.VERTICAL)
        box12.Add(self.plotRT, 1, wx.EXPAND)
        self.panelRT.SetSizer(box12)
        
        # Setup PLOT 1D 
        self.panel1D = wx.Panel( self.mainBook, wx.ID_ANY, wx.DefaultPosition, 
                                   wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.mainBook.AddPage( self.panel1D, u"1D", False )        

        figsize = self.config._plotSettings["DT"]['gui_size']
        self.plot1D = plots.plots(self.panel1D, figsize=figsize, config=self.config)

        box1 = wx.BoxSizer(wx.VERTICAL)
        box1.Add(self.plot1D, 1, wx.EXPAND)
        self.panel1D.SetSizer(box1)
          
        # Setup PLOT 2D
        self.panel2D = wx.Panel( self.mainBook, wx.ID_ANY, wx.DefaultPosition, 
                                   wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.mainBook.AddPage( self.panel2D, u"2D", False )

        figsize = self.config._plotSettings["2D"]['gui_size']
        self.plot2D = plots.plots(self.panel2D, figsize=figsize, config=self.config) 
        
        box14 = wx.BoxSizer(wx.HORIZONTAL)
        box14.Add(self.plot2D, 1, wx.EXPAND | wx.ALL)
        self.panel2D.SetSizerAndFit(box14)         
        
        # Setup PLOT DT/MS
        self.panelMZDT = wx.Panel( self.mainBook, wx.ID_ANY, wx.DefaultPosition, 
                                   wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.mainBook.AddPage( self.panelMZDT, u"DT/MS", False )

        figsize = self.config._plotSettings["DT/MS"]['gui_size']
        self.plotMZDT = plots.plots(self.panelMZDT, figsize=figsize, config=self.config) 
          
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

        figsize = self.config._plotSettings["Waterfall"]['gui_size']
        self.plotWaterfallIMS = plots.plots(self.waterfallIMS, figsize=figsize, config=self.config)
        
        box15 = wx.BoxSizer(wx.HORIZONTAL)
        box15.Add(self.plotWaterfallIMS, 1, wx.EXPAND | wx.ALL)
        self.waterfallIMS.SetSizerAndFit(box15)     

        # Setup PLOT 3D
        self.panel3D = wx.Panel( self.mainBook, wx.ID_ANY, wx.DefaultPosition, 
                                   wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.mainBook.AddPage( self.panel3D, u"3D", False )
        
        figsize = self.config._plotSettings["3D"]['gui_size']
        self.plot3D = plots.plots(self.panel3D, figsize=figsize, config=self.config)

        plotSizer = wx.BoxSizer(wx.VERTICAL)     
        plotSizer.Add(self.plot3D, 1, wx.EXPAND)
        self.panel3D.SetSizer(plotSizer)  
        
        # Setup PLOT RMSF
        self.panelRMSF = wx.Panel( self.mainBook, wx.ID_ANY, wx.DefaultPosition, 
                                   wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.mainBook.AddPage( self.panelRMSF, u"RMSF", False )

        figsize = self.config._plotSettings["RMSF"]['gui_size']
        self.plotRMSF = plots.plots(self.panelRMSF, figsize=figsize, config=self.config)

        plotSizer5 = wx.BoxSizer(wx.VERTICAL)     
        plotSizer5.Add(self.plotRMSF, 1, wx.EXPAND)
        self.panelRMSF.SetSizer(plotSizer5)  
        
        
        # Setup PLOT Comparison
        self.m_panel17 = wx.Panel( self.mainBook, wx.ID_ANY, wx.DefaultPosition, 
                                   wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.mainBook.AddPage( self.m_panel17, u"Comparison", False )

        figsize = self.config._plotSettings["Comparison"]['gui_size']
        self.plotCompare = plots.plots(self.m_panel17, config = self.config)

        
        plotSizer3 = wx.BoxSizer(wx.VERTICAL)     
        plotSizer3.Add(self.plotCompare, 1, wx.EXPAND)
        self.m_panel17.SetSizer(plotSizer3)  
        
        # Setup PLOT Overlay
        self.panelOverlay = wx.Panel( self.mainBook, wx.ID_ANY, wx.DefaultPosition, 
                                   wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.mainBook.AddPage( self.panelOverlay, u"Overlay", False )

        figsize = self.config._plotSettings["Overlay"]['gui_size']
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
        
        
        # Setup PLOT Comparison
        self.panelUniDec = wx.lib.scrolledpanel.ScrolledPanel(self.mainBook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.panelUniDec.SetupScrolling()
        self.mainBook.AddPage(self.panelUniDec, u"UniDec", False)
        
        figsize = self.config._plotSettings["UniDec (MS)"]['gui_size']
        self.plotUnidec_MS = plots.plots(self.panelUniDec, config=self.config, figsize=figsize)
        
        figsize = self.config._plotSettings["UniDec (m/z vs Charge)"]['gui_size']
        self.plotUnidec_mzGrid = plots.plots(self.panelUniDec, config=self.config, figsize=figsize)
        
        figsize = self.config._plotSettings["UniDec (MW)"]['gui_size']
        self.plotUnidec_mwDistribution = plots.plots(self.panelUniDec, config=self.config, figsize=figsize)
        
        figsize = self.config._plotSettings["UniDec (Isolated MS)"]['gui_size']
        self.plotUnidec_individualPeaks = plots.plots(self.panelUniDec, config=self.config, figsize=figsize)
        
        figsize = self.config._plotSettings["UniDec (MW vs Charge)"]['gui_size']
        self.plotUnidec_mwVsZ = plots.plots(self.panelUniDec, config=self.config, figsize=figsize)

        figsize = self.config._plotSettings["UniDec (Barplot)"]['gui_size']
        self.plotUnidec_barChart = plots.plots(self.panelUniDec, config=self.config, figsize=figsize)
        
        figsize = self.config._plotSettings["UniDec (Charge Distribution)"]['gui_size']
        self.plotUnidec_chargeDistribution = plots.plots(self.panelUniDec, config=self.config, figsize=figsize)

        plotUnidecSizer = wx.GridBagSizer()
        plotUnidecSizer.Add(self.plotUnidec_MS, (0, 0), span=(1, 1), flag=wx.EXPAND)
        plotUnidecSizer.Add(self.plotUnidec_mwDistribution, (0, 1), span=(1, 1), flag=wx.EXPAND)
        plotUnidecSizer.Add(self.plotUnidec_mzGrid, (1, 0), span=(1, 1), flag=wx.EXPAND)
        plotUnidecSizer.Add(self.plotUnidec_individualPeaks, (1, 1), span=(1, 1), flag=wx.EXPAND)
        plotUnidecSizer.Add(self.plotUnidec_mwVsZ, (2, 0), span=(1, 1), flag=wx.EXPAND)
        plotUnidecSizer.Add(self.plotUnidec_barChart, (2, 1), span=(1, 1), flag=wx.EXPAND)
        plotUnidecSizer.Add(self.plotUnidec_chargeDistribution, (3, 0), span=(1, 1), flag=wx.EXPAND)
        
        self.panelUniDec.SetSizer(plotUnidecSizer)  
        
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

        
        bSizer1.Add( self.mainBook, 1, wx.EXPAND |wx.ALL, 5 )
        
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnRightClickMenu)
        self.SetSizer( bSizer1 )
        self.Layout()
        self.Show(True)
        
    def OnRightClickMenu(self, evt):
        self.currentPage = self.mainBook.GetPageText(self.mainBook.GetSelection())
        
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
        self.Bind(wx.EVT_MENU, self.presenter.onClearPlot, id=ID_clearPlot_Waterfall)
        self.Bind(wx.EVT_MENU, self.on_clear_unidec, id=ID_clearPlot_UniDec_all)
        self.Bind(wx.EVT_MENU, self.onSetupMenus, id=ID_plotPanel_binMS)
        
        self.Bind(wx.EVT_MENU, self.customisePlot, id=ID_plots_customisePlot)
        self.Bind(wx.EVT_MENU, self.customisePlot, id=ID_plots_customisePlot_unidec_ms)
        self.Bind(wx.EVT_MENU, self.customisePlot, id=ID_plots_customisePlot_unidec_mw)
        self.Bind(wx.EVT_MENU, self.customisePlot, id=ID_plots_customisePlot_unidec_mz_v_charge)
        self.Bind(wx.EVT_MENU, self.customisePlot, id=ID_plots_customisePlot_unidec_isolated_mz)
        self.Bind(wx.EVT_MENU, self.customisePlot, id=ID_plots_customisePlot_unidec_mw_v_charge)
        self.Bind(wx.EVT_MENU, self.customisePlot, id=ID_plots_customisePlot_unidec_ms_barchart)
        self.Bind(wx.EVT_MENU, self.customisePlot, id=ID_plots_customisePlot_unidec_chargeDist)
        
        self.Bind(wx.EVT_MENU, self.save_images, id=ID_plots_saveImage_unidec_ms)
        self.Bind(wx.EVT_MENU, self.save_images, id=ID_plots_saveImage_unidec_mw)
        self.Bind(wx.EVT_MENU, self.save_images, id=ID_plots_saveImage_unidec_mz_v_charge)
        self.Bind(wx.EVT_MENU, self.save_images, id=ID_plots_saveImage_unidec_isolated_mz)
        self.Bind(wx.EVT_MENU, self.save_images, id=ID_plots_saveImage_unidec_mw_v_charge)
        self.Bind(wx.EVT_MENU, self.save_images, id=ID_plots_saveImage_unidec_ms_barchart)
        self.Bind(wx.EVT_MENU, self.save_images, id=ID_plots_saveImage_unidec_chargeDist)
        self.Bind(wx.EVT_MENU, self.save_unidec_images, id=ID_saveUniDecAll)
        
        saveImageLabel = ''.join(['Save figure (.', self.config.imageFormat,')'])
        
        customiseUniDecMenu = wx.Menu()
        customiseUniDecMenu.Append(ID_plots_customisePlot_unidec_ms, 'Customise mass spectrum...')
        customiseUniDecMenu.Append(ID_plots_customisePlot_unidec_mw, 'Customise Zero charge mass spectrum...')
        customiseUniDecMenu.Append(ID_plots_customisePlot_unidec_mz_v_charge, 'Customise m/z vs charge...')
        customiseUniDecMenu.Append(ID_plots_customisePlot_unidec_isolated_mz, 'Customise mass spectrum with isolated species...')
        customiseUniDecMenu.Append(ID_plots_customisePlot_unidec_mw_v_charge, 'Customise molecular weight vs charge...')
        customiseUniDecMenu.Append(ID_plots_customisePlot_unidec_ms_barchart, 'Customise barchart...')
        customiseUniDecMenu.Append(ID_plots_customisePlot_unidec_chargeDist, 'Customise charge state distribution...')
        
        saveUniDecMenu = wx.Menu()
        saveUniDecMenu.Append(ID_plots_saveImage_unidec_ms, 'Save mass spectrum (.{})'.format(self.config.imageFormat))
        saveUniDecMenu.Append(ID_plots_saveImage_unidec_mw, 'Save Zero charge mass spectrum (.{})'.format(self.config.imageFormat))
        saveUniDecMenu.Append(ID_plots_saveImage_unidec_mz_v_charge, 'Save m/z vs charge (.{})'.format(self.config.imageFormat))
        saveUniDecMenu.Append(ID_plots_saveImage_unidec_isolated_mz, 'Save mass spectrum with isolated species (.{})'.format(self.config.imageFormat))
        saveUniDecMenu.Append(ID_plots_saveImage_unidec_mw_v_charge, 'Save molecular weight vs charge (.{})'.format(self.config.imageFormat))
        saveUniDecMenu.Append(ID_plots_saveImage_unidec_ms_barchart, 'Save barchart (.{})'.format(self.config.imageFormat))
        saveUniDecMenu.Append(ID_saveData_excel, 'Save charge state distribution (.{})'.format(self.config.imageFormat))
        saveUniDecMenu.AppendSeparator()
        saveUniDecMenu.AppendItem(makeMenuItem(parent=saveUniDecMenu, id=ID_saveUniDecAll, text="Save all figures (.{})".format(self.config.imageFormat), 
                                               bitmap=self.icons.iconsLib['save16']))
        menu = wx.Menu()
        if self.currentPage == "MS":
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
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_plots_customisePlot,
                                         text='Customise plot...', 
                                         bitmap=self.icons.iconsLib['change_xlabels_16']))
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
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_plots_customisePlot,
                                         text='Customise plot...', 
                                         bitmap=self.icons.iconsLib['change_xlabels_16']))
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
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_plots_customisePlot,
                                         text='Customise plot...', 
                                         bitmap=self.icons.iconsLib['change_xlabels_16']))
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
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_plots_customisePlot,
                                         text='Customise plot...', 
                                         bitmap=self.icons.iconsLib['change_xlabels_16']))
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
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_plots_customisePlot,
                                         text='Customise plot...', 
                                         bitmap=self.icons.iconsLib['change_xlabels_16']))
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
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_plots_customisePlot,
                                         text='Customise plot...', 
                                         bitmap=self.icons.iconsLib['change_xlabels_16']))
            menu.AppendSeparator()
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveOverlayImage, text=saveImageLabel, 
                                         bitmap=self.icons.iconsLib['save16']))
            menu.AppendSeparator()
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_clearPlot_Overlay, text="Clear plot", 
                                         bitmap=self.icons.iconsLib['clear_16']))
        elif self.currentPage == "Waterfall":
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_extraSettings_plot2D,
                                         text='Edit plot parameters...', 
                                         bitmap=self.icons.iconsLib['panel_plot2D_16']))
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_extraSettings_legend,
                                         text='Edit legend parameters...', 
                                         bitmap=self.icons.iconsLib['panel_legend_16']))
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_extraSettings_waterfall,
                                         text='Edit waterfall parameters...', 
                                         bitmap=self.icons.iconsLib['panel_waterfall_16']))
            menu.AppendSeparator()
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_plots_customisePlot,
                                         text='Customise plot...', 
                                         bitmap=self.icons.iconsLib['change_xlabels_16']))
            menu.AppendSeparator()
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
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_plots_customisePlot,
                                         text='Customise plot...', 
                                         bitmap=self.icons.iconsLib['change_xlabels_16']))
            menu.AppendSeparator()
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveRMSFImage, text=saveImageLabel, 
                                         bitmap=self.icons.iconsLib['save16']))
            menu.AppendSeparator()
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_clearPlot_RMSF, text="Clear plot", 
                                         bitmap=self.icons.iconsLib['clear_16']))
        elif self.currentPage == "Comparison":
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_plots_customisePlot,
                                         text='Customise plot...', 
                                         bitmap=self.icons.iconsLib['change_xlabels_16']))
            menu.AppendSeparator()
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveRMSDmatrixImage, text=saveImageLabel, 
                                         bitmap=self.icons.iconsLib['save16']))
            menu.AppendSeparator()
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_clearPlot_Matrix, text="Clear plot", 
                                         bitmap=self.icons.iconsLib['clear_16']))
        elif self.currentPage == "Calibration":
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_clearPlot_Calibration, text="Clear plot", 
                                         bitmap=self.icons.iconsLib['clear_16']))
        elif self.currentPage == "UniDec":
            
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_extraSettings_plot1D,
                                         text='Edit plot parameters...', 
                                         bitmap=self.icons.iconsLib['panel_plot1D_16']))
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
            menu.AppendMenu(wx.ID_ANY, 'Customise plot...', customiseUniDecMenu)
            menu.AppendSeparator()
            menu.AppendMenu(wx.ID_ANY, 'Save to file...', saveUniDecMenu)
            menu.AppendSeparator()
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_clearPlot_UniDec_all, text="Clear all", 
                                         bitmap=self.icons.iconsLib['clear_16']))
        else: 
            pass
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()
        
    def save_images(self, evt, path=None, **save_kwargs):
        """ Save figure depending on the event ID """
        print("Saving image. Please wait...")
        
        if isinstance(evt, int):
            evtID = evt
        else:
            evtID = evt.GetId()
        
        path, title = self.presenter.getCurrentDocumentPath()
        if path == None: 
            args = ("Could not find path", 4) 
            self.presenter.onThreading(None, args, action='updateStatusbar')
            return
        
        # Select default name + link to the plot
        if evtID in [ID_saveMSImage, ID_saveMSImageDoc]:
            defaultName = self.config._plotSettings['MS']['default_name']
            resizeName ="MS"
            plotWindow = self.plot1
            
        elif evtID in [ID_saveRTImage, ID_saveRTImageDoc]:
            defaultName = self.config._plotSettings['RT']['default_name']
            resizeName = "RT"
            plotWindow = self.plotRT
            
        elif evtID in [ID_save1DImage, ID_save1DImageDoc]:
            defaultName = self.config._plotSettings['DT']['default_name']
            resizeName = "DT"
            plotWindow = self.plot1D
            
        elif evtID in [ID_save2DImage, ID_save2DImageDoc]:
            plotWindow = self.plot2D
            defaultName = self.config._plotSettings['2D']['default_name']
            resizeName = "2D"
            
        elif evtID in [ID_save3DImage, ID_save3DImageDoc]:
            defaultName = self.config._plotSettings['3D']['default_name']
            resizeName = "3D"
            plotWindow = self.plot3D
            
        elif evtID in [ID_saveWaterfallImage, ID_saveWaterfallImageDoc]:
            defaultName = self.config._plotSettings['Waterfall']['default_name']
            resizeName = "Waterfall"
            plotWindow = self.plotWaterfallIMS
            
        elif evtID in [ID_saveRMSDImage, ID_saveRMSDImageDoc, 
                             ID_saveRMSFImage, ID_saveRMSFImageDoc]:
            plotWindow = self.plotRMSF
            defaultName = self.config._plotSettings['RMSD']['default_name']
            resizeName = plotWindow.getPlotName()
            
        elif evtID in [ID_saveOverlayImage, ID_saveOverlayImageDoc]:
            plotWindow = self.plotOverlay
            defaultName = plotWindow.getPlotName()
            resizeName = "Overlay"
            
        elif evtID in [ID_saveRMSDmatrixImage, ID_saveRMSDmatrixImageDoc]:
            defaultName = self.config._plotSettings['Matrix']['default_name']
            resizeName = "Matrix"
            plotWindow = self.plotCompare
            
        elif evtID in [ID_saveMZDTImage, ID_saveMZDTImageDoc]:
            defaultName = self.config._plotSettings['DT/MS']['default_name']
            resizeName = "DT/MS"
            plotWindow = self.plotMZDT

        elif evtID in [ID_plots_saveImage_unidec_ms]:
            defaultName = self.config._plotSettings['UniDec (MS)']['default_name']
            resizeName = 'UniDec (MS)'
            plotWindow = self.plotUnidec_MS
            
        elif evtID in [ID_plots_saveImage_unidec_mw]:
            defaultName = self.config._plotSettings['UniDec (MW)']['default_name']
            resizeName = 'UniDec (MW)'
            plotWindow = self.plotUnidec_mwDistribution
            
        elif evtID in [ID_plots_saveImage_unidec_mz_v_charge]:
            defaultName = self.config._plotSettings['UniDec (m/z vs Charge)']['default_name']
            resizeName = 'UniDec (m/z vs Charge)'
            plotWindow = self.plotUnidec_mzGrid
            
        elif evtID in [ID_plots_saveImage_unidec_isolated_mz]:
            defaultName = self.config._plotSettings['UniDec (Isolated MS)']['default_name']
            resizeName = 'UniDec (Isolated MS)'
            plotWindow = self.plotUnidec_individualPeaks
            
        elif evtID in [ID_plots_saveImage_unidec_mw_v_charge]:
            defaultName = self.config._plotSettings['UniDec (MW vs Charge)']['default_name']
            resizeName = 'UniDec (MW vs Charge)'
            plotWindow = self.plotUnidec_mwVsZ
            
        elif evtID in [ID_plots_saveImage_unidec_ms_barchart]:
            defaultName = self.config._plotSettings['UniDec (Barplot)']['default_name']
            resizeName = 'UniDec (Barplot)'
            plotWindow = self.plotUnidec_barChart
            
        elif evtID in [ID_plots_saveImage_unidec_chargeDist]:
            defaultName = self.config._plotSettings['UniDec (Charge Distribution)']['default_name']
            resizeName = 'UniDec (Charge Distribution)'
            plotWindow = self.plotUnidec_chargeDistribution

            
        # generate a better default name and remove any silly characters
        if "image_name" in save_kwargs:
            defaultName = save_kwargs.pop("image_name")
            if defaultName == None:
                defaultName = "{}_{}".format(title, defaultName)
        else:
            defaultName = "{}_{}".format(title, defaultName)
        defaultName = defaultName.replace(' ','').replace(':','').replace(" ","").replace(".csv","").replace(".txt","").replace(".raw","").replace(".d","").replace(".","")
        
        # Setup filename
        wildcard = "SVG Scalable Vector Graphic (*.svg)|*.svg|" + \
                   "SVGZ Compressed Scalable Vector Graphic (*.svgz)|*.svgz|" + \
                   "PNG Portable Network Graphic (*.png)|*.png|" + \
                   "Enhanced Windows Metafile (*.eps)|*.eps|" + \
                   "JPEG File Interchange Format (*.jpeg)|*.jpeg|" + \
                   "TIFF Tag Image File Format (*.tiff)|*.tiff|" + \
                   "RAW Image File Format (*.raw)|*.raw|" + \
                   "PS PostScript Image File Format (*.ps)|*.ps|" + \
                   "PDF Portable Document Format (*.pdf)|*.pdf"
                   
        wildcard_dict = {'svg':0, 'svgz':1, 'png':2, 'eps':3, 'jpeg':4,
                         'tiff':5, 'raw':6, 'ps':7, 'pdf':8}
                   
        dlg =  wx.FileDialog(self, "Please select a name for the file", 
                             "", "", wildcard=wildcard, style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        dlg.CentreOnParent()
        dlg.SetFilename(defaultName)
        try: dlg.SetFilterIndex(wildcard_dict[self.config.imageFormat])
        except: pass
        
        if dlg.ShowModal() == wx.ID_OK:
            tstart = time.clock()
            filename = dlg.GetPath()
            __, extension = os.path.splitext(filename)
            self.config.imageFormat = extension[1::]
                        
            # Build kwargs
            kwargs = {"transparent":self.config.transparent,
                      "dpi":self.config.dpi, 
                      'format':extension[1::],
                      'compression':"zlib",
                      'resize': None}
        
            if self.config.resize:
                kwargs['resize'] = resizeName
            
            plotWindow.saveFigure2(path=filename, **kwargs)
    
            tend = time.clock()
            msg = "Saved figure to %s. It took %s s." % (path, str(np.round((tend-tstart),4)))
            args = (msg, 4) 
        else:
            msg = "Operation was cancelled"
            args = (msg, 4)
        print(msg)
        self.presenter.onThreading(evt, args, action='updateStatusbar')
         
    def customisePlot(self, evt):
        open_window = True
        if self.currentPage == "Waterfall": plot = self.plotWaterfallIMS
        elif self.currentPage == "MS": plot = self.plot1
        elif self.currentPage == "1D": plot = self.plot1D
        elif self.currentPage == "RT": plot = self.plotRT
        elif self.currentPage == "2D": plot = self.plot2D
        elif self.currentPage == "DT/MS": plot = self.plotMZDT
        elif self.currentPage == "Overlay": 
            plot = self.plotOverlay
            if plot.plot_name not in ["Mask", "Transparent"]: open_window = False
        elif self.currentPage == "RMSF": 
            plot = self.plotRMSF
            if plot.plot_name not in ["RMSD"]: open_window = False 
        elif self.currentPage == "Comparison": plot = self.plotCompare
        elif self.currentPage == "UniDec":
            evtID = evt.GetId()
            if evtID == ID_plots_customisePlot_unidec_ms: plot = self.plotUnidec_MS
            elif evtID == ID_plots_customisePlot_unidec_mw: plot = self.plotUnidec_mwDistribution
            elif evtID == ID_plots_customisePlot_unidec_mz_v_charge: plot = self.plotUnidec_mzGrid
            elif evtID == ID_plots_customisePlot_unidec_isolated_mz: plot = self.plotUnidec_individualPeaks
            elif evtID == ID_plots_customisePlot_unidec_mw_v_charge: plot = self.plotUnidec_mwVsZ
            elif evtID == ID_plots_customisePlot_unidec_ms_barchart: plot = self.plotUnidec_barChart
            elif evtID == ID_plots_customisePlot_unidec_chargeDist: plot = self.plotUnidec_chargeDistribution
            
        if not open_window:
            args = ("Cannot customise parameters for this plot. Try replotting instead", 4) 
            self.presenter.onThreading(None, args, action='updateStatusbar')
            return
        
        if not hasattr(plot, "plotMS"):
            args = ("Cannot customise plot parameters if the plot does not exist", 4) 
            self.presenter.onThreading(None, args, action='updateStatusbar')
            return
            
        if hasattr(plot, "plot_limits") and len(plot.plot_limits) == 4:
            xmin, xmax = plot.plot_limits[0], plot.plot_limits[1]
            ymin, ymax = plot.plot_limits[2], plot.plot_limits[3]
        else:
            try:
                xmin, xmax = plot.plotMS.get_xlim()
                ymin, ymax = plot.plotMS.get_ylim()
            except AttributeError:
                args = ("Cannot customise plot parameters if the plot does not exist", 4) 
                self.presenter.onThreading(None, args, action='updateStatusbar')
                return
        
        dpi = wx.ScreenDC().GetPPI()
        if hasattr(plot, "plot_parameters"):
            if "panel_size" in plot.plot_parameters:
                plot_sizeInch = (np.round(plot.plot_parameters['panel_size'][0]/dpi[0],2),
                                 np.round(plot.plot_parameters['panel_size'][1]/dpi[1],2))
            else:
                plot_size = plot.GetSize()
                plot_sizeInch = (np.round(plot_size[0]/dpi[0],2),
                                 np.round(plot_size[1]/dpi[1],2))
        else:
            plot_size = plot.GetSize()
            plot_sizeInch = (np.round(plot_size[0]/dpi[0],2),
                             np.round(plot_size[1]/dpi[1],2))


        kwargs = {'xmin':xmin, 'xmax':xmax,
                  'ymin':ymin, 'ymax':ymax,
                  'major_xticker':plot.plotMS.xaxis.get_major_locator(),
                  'major_yticker':plot.plotMS.yaxis.get_major_locator(),
                  'minor_xticker':plot.plotMS.xaxis.get_minor_locator(),
                  'minor_yticker':plot.plotMS.yaxis.get_minor_locator(),
                  'tick_size':self.config.tickFontSize_1D,
                  'tick_weight':self.config.tickFontWeight_1D,
                  'label_size':self.config.labelFontSize_1D,
                  'label_weight':self.config.labelFontWeight_1D,
                  'title_size':self.config.titleFontSize_1D,
                  'title_weight':self.config.titleFontWeight_1D,
                  'xlabel':plot.plotMS.get_xlabel(),
                  'ylabel':plot.plotMS.get_ylabel(),
                  'title':plot.plotMS.get_title(),
                  'plot_size':plot_sizeInch,
                  'plot_axes':plot._axes,
                  'plot':plot}       
        
        dlg = panelCustomisePlot(self, self.presenter, self.config, **kwargs)
        dlg.ShowModal()
         
    def save_unidec_images(self, evt, path=None):
        """ Save figure depending on the event ID """
        print("Saving image. Please wait...")
        # Setup filename
        wildcard = "SVG Scalable Vector Graphic (*.svg)|*.svg|" + \
                   "SVGZ Compressed Scalable Vector Graphic (*.svgz)|*.svgz|" + \
                   "PNG Portable Network Graphic (*.png)|*.png|" + \
                   "Enhanced Windows Metafile (*.eps)|*.eps|" + \
                   "JPEG File Interchange Format (*.jpeg)|*.jpeg|" + \
                   "TIFF Tag Image File Format (*.tiff)|*.tiff|" + \
                   "RAW Image File Format (*.raw)|*.raw|" + \
                   "PS PostScript Image File Format (*.ps)|*.ps|" + \
                   "PDF Portable Document Format (*.pdf)|*.pdf"
                   
        wildcard_dict = {'svg':0, 'svgz':1, 'png':2, 'eps':3, 'jpeg':4,
                         'tiff':5, 'raw':6, 'ps':7, 'pdf':8}
        
#         tstart = time.clock()
        # Build kwargs
        kwargs = {"transparent":self.config.transparent,
                  "dpi":self.config.dpi, 
                  'format':self.config.imageFormat,
                  'compression':"zlib",
                  'resize': None}
        
        path, document_name = self.presenter.getCurrentDocumentPath()
        document_name = document_name.replace('.raw','').replace(' ','')
        if path == None: 
            args = ("Could not find path", 4) 
            self.presenter.onThreading(None, args, action='updateStatusbar')
            return
        
        plots = {'UniDec (MS)':self.plotUnidec_MS, 
                 'UniDec (MW)':self.plotUnidec_mwDistribution, 
                 'UniDec (m/z vs Charge)':self.plotUnidec_mzGrid, 
                 'UniDec (Isolated MS)':self.plotUnidec_individualPeaks, 
                 'UniDec (MW vs Charge)':self.plotUnidec_mwVsZ, 
                 'UniDec (Barplot)':self.plotUnidec_barChart,
                 'UniDec (Charge Distribution)':self.plotUnidec_chargeDistribution}
        
        for plot in plots:
            defaultName = self.config._plotSettings[plot]['default_name']
            
            # generate a better default name and remove any silly characters
            defaultName = "{}_{}".format(document_name, defaultName)
            defaultName = defaultName.replace(' ','').replace(':','').replace(" ","").replace(".csv","").replace(".txt","").replace(".raw","").replace(".d","")
            
            dlg =  wx.FileDialog(self, "Please select a name for the file", 
                                 "", "", wildcard=wildcard, style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
            dlg.CentreOnParent()
            dlg.SetFilename(defaultName)
            try: dlg.SetFilterIndex(wildcard_dict[self.config.imageFormat])
            except: pass
            plotWindow = plots[plot]
            if dlg.ShowModal() == wx.ID_OK:
                filename = dlg.GetPath()
                __, extension = os.path.splitext(filename)
                self.config.imageFormat = extension[1::]
             
                if self.config.resize:
                    kwargs['resize'] = plot
                    
                try:
                    plotWindow.saveFigure2(path=filename, **kwargs)
                    print("Saved {}".format(filename))
                except: 
                    print("Could not save {}. Moving on...".format(filename))
                    continue

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
                  
    def onChangePalette(self, evt, n_colors=16, return_colors=False):
        if self.config.currentPalette in ['Spectral', 'RdPu']:
            palette_name = self.config.currentPalette
        else:
            palette_name = self.config.currentPalette.lower()
        new_color = sns.color_palette(palette_name, n_colors)
        
        if not return_colors:
            for i in xrange(n_colors):
                self.config.customColors[i] = convertRGB1to255(new_color[i])
        else:
            return new_color
                 
    def onGetColormapList(self, n_colors):
        colorlist = sns.color_palette(self.config.currentCmap, n_colors) #plt.cm.get_cmap(name=self.config.currentCmap, lut=n_colors)
        return colorlist
        
    def get_colorList(self, count):
        colorList = sns.color_palette("cubehelix", count)
        colorList_return = []
        for color in colorList:
            colorList_return.append(convertRGB1to255(color))
        
        return colorList_return
        
# plots

    def on_clear_unidec(self, evt=None, which="all"):
        
        if which in ['all', 'initilise']:
            self.plotUnidec_MS.clearPlot()
        
        if which in ['all', 'run']:
            self.plotUnidec_mzGrid.clearPlot()
            self.plotUnidec_mwDistribution.clearPlot()
            self.plotUnidec_mwVsZ.clearPlot()
            
        if which in ['all', 'detect', 'run']:
            self.plotUnidec_individualPeaks.clearPlot()
            self.plotUnidec_barChart.clearPlot()
            self.plotUnidec_chargeDistribution.clearPlot()

    def on_plot_charge_states(self, position, charges, **kwargs):
        
        
        self.plotUnidec_individualPeaks.plot_remove_text_and_lines()
        for position, charge in zip(position, charges):
            self.plotUnidec_individualPeaks.plot_add_text_and_lines(xpos=position, yval=1, label=charge)
            
        self.plotUnidec_individualPeaks.repaint()      
    
    def on_plot_unidec_ChargeDistribution(self, xvals=None, yvals=None, replot=None, xlimits=None, **kwargs):
        """
        Plot simple Mass spectrum before it is pre-processed
        @param unidec_eng_data (object):  reference to unidec engine data structure
        @param xlimits: unused
        """
        
        # Build kwargs
        plt_kwargs = self.presenter._buildPlotParameters(plotType='1D')
        
        self.plotUnidec_chargeDistribution.clearPlot()
#         self.plotUnidec_barChart.plot_1D_barplot(xvals, yvals, xvals, colors,
#                                                  axesSize=self.config._plotSettings['UniDec (Barplot)']['axes_size'],
#                                                  title="Peak Intensities",
#                                                  ylabel="Intensity",
#                                                  plotType="Test",
#                                                  **plt_kwargs)
        self.plotUnidec_chargeDistribution.plot_1D(xvals=xvals, yvals=yvals, 
                                   xlimits=xlimits, xlabel="Charge", 
                                   ylabel="Intensity", testMax=None, 
                                   axesSize=self.config._plotSettings['UniDec (Charge Distribution)']['axes_size'],
                                   plotType='ChargeDistribution', title="Charge State Distribution",
                                   allowWheel=False,
                                   **plt_kwargs)
        # Show the mass spectrum
        self.plotUnidec_chargeDistribution.repaint()
    
    def on_plot_unidec_MS(self, unidec_eng_data=None, replot=None, xlimits=None, **kwargs):
        """
        Plot simple Mass spectrum before it is pre-processed
        @param unidec_eng_data (object):  reference to unidec engine data structure
        @param xlimits: unused
        """
        
        # Build kwargs
        plt_kwargs = self.presenter._buildPlotParameters(plotType='1D')
        
        if unidec_eng_data is None and replot is not None:
            xvals = replot['xvals']
            yvals = replot['yvals']
        else:
            xvals = unidec_eng_data.data2[:, 0]
            yvals = unidec_eng_data.data2[:, 1]
            
        self.plotUnidec_MS.clearPlot()
        self.plotUnidec_MS.plot_1D(xvals=xvals, yvals=yvals, 
                                   xlimits=xlimits, xlabel="m/z", 
                                   ylabel="Intensity",
                                   axesSize=self.config._plotSettings['UniDec (MS)']['axes_size'],
                                   plotType='MS', title="MS",
                                   allowWheel=False,
                                   **plt_kwargs)
        # Show the mass spectrum
        self.plotUnidec_MS.repaint()
    
    def on_plot_unidec_MS_v_Fit(self, unidec_eng_data=None, replot=None, xlimits=None, **kwargs):
        
        # Build kwargs
        plt_kwargs = self.presenter._buildPlotParameters(plotType='1D')
        
        if unidec_eng_data is None and replot is not None:
            xvals = replot['xvals']
            yvals = replot['yvals']
            colors = replot['colors']
            labels = replot['labels']
        else:
            xvals = [unidec_eng_data.data2[:, 0], unidec_eng_data.data2[:, 0]]
            yvals = [unidec_eng_data.data2[:, 1], unidec_eng_data.fitdat]
            colors = ['black', 'red']
            labels = ['Data', 'Fit Data']
        
        self.plotUnidec_MS.clearPlot()
        self.plotUnidec_MS.plot_1D_overlay(xvals=xvals, 
                                           yvals=yvals, 
                                           labels=labels,
                                           colors=colors, 
                                           xlimits=xlimits,
                                           xlabel="m/z", 
                                           ylabel="Intensity",
                                           axesSize=self.config._plotSettings['UniDec (MS)']['axes_size'],
                                           plotType='MS', title="MS and UniDec Fit",
                                           allowWheel=False,
                                           **plt_kwargs)
        # Show the mass spectrum
        self.plotUnidec_MS.repaint()
    
    def on_plot_unidec_mzGrid(self, unidec_eng_data=None, replot=None, **kwargs):
        """
        Plot simple Mass spectrum before it is pre-processed
        @param unidec_eng_data (object):  reference to unidec engine data structure
        """
        
        # Build kwargs
        plt_kwargs = self.presenter._buildPlotParameters(plotType='2D')
        plt_kwargs['colorbar'] = True
        
        if unidec_eng_data is None and replot is not None:
            grid = replot['grid']
        else:
            grid = unidec_eng_data.mzgrid
        
        self.plotUnidec_mzGrid.clearPlot()
        self.plotUnidec_mzGrid.plot_2D_contour_unidec(data=grid, 
                                                      xlabel="m/z (Da)", 
                                                      ylabel="Charge",
                                                      axesSize=self.config._plotSettings['UniDec (m/z vs Charge)']['axes_size'],
                                                      plotType='2D', plotName="zGrid",
                                                      speedy=kwargs.get('speedy', True),
                                                      title="m/z vs Charge",
                                                      allowWheel=False,
                                                      **plt_kwargs)
        # Show the mass spectrum
        self.plotUnidec_mzGrid.repaint()

    def on_plot_unidec_mwDistribution(self, unidec_eng_data=None, replot=None, xlimits=None, **kwargs):
        """
        Plot simple Mass spectrum before it is pre-processed
        @param unidec_eng_data (object):  reference to unidec engine data structure
        @param xlimits: unused
        """
        
        # Build kwargs
        plt_kwargs = self.presenter._buildPlotParameters(plotType='1D')
        
        if unidec_eng_data is None and replot is not None:
            xvals = replot['xvals']
            yvals = replot['yvals']
        else:
            xvals = unidec_eng_data.massdat[:, 0]
            yvals = unidec_eng_data.massdat[:, 1]
        
        self.plotUnidec_mwDistribution.clearPlot()
        self.plotUnidec_mwDistribution.plot_1D(xvals=xvals, 
                                               yvals=yvals, 
                                               xlimits=xlimits,
                                               xlabel="Mass Distribution", 
                                               ylabel="Intensity",
                                               axesSize=self.config._plotSettings['UniDec (MW)']['axes_size'],
                                               plotType='mwDistribution', testMax=None, testX=True, 
                                               title="Zero-charge Mass Spectrum",
                                               allowWheel=False,
                                               **plt_kwargs)
        # Show the mass spectrum
        self.plotUnidec_mwDistribution.repaint()

    def on_plot_unidec_individualPeaks(self, unidec_eng_data=None, replot=None, xlimits=None, **kwargs):
        """
        Plot simple Mass spectrum before it is pre-processed
        @param unidec_eng_data (object):  reference to unidec engine data structure
        @param xlimits: unused
        """
        
        # Build kwargs
        plt_kwargs = self.presenter._buildPlotParameters(plotType='1D')
        
        if unidec_eng_data is None and replot is not None:
            xvals = replot['xvals']
            yvals = replot['yvals']
            legend_text = replot['legend_text']
        else:
            xvals=unidec_eng_data.data.data2[:, 0]
            yvals=unidec_eng_data.data.data2[:, 1]
            
        # Plot MS
        self.plotUnidec_individualPeaks.clearPlot()
        self.plotUnidec_individualPeaks.plot_1D(xvals=xvals, yvals=yvals, 
                                                xlimits=xlimits, xlabel="m/z", 
                                                ylabel="Intensity",
                                                axesSize=self.config._plotSettings['UniDec (Isolated MS)']['axes_size'],
                                                plotType='MS', label="Raw",
                                                allowWheel=False,
                                                **plt_kwargs)
        
        if unidec_eng_data is None and replot is not None:
            if kwargs.get('show_isolated_mw', False):
                legend_text = [[[0,0,0], "Raw"]]
            for key in replot:
                if key.split(" ")[0] != "MW:": continue
                scatter_yvals = replot[key]['scatter_yvals']
                line_yvals = replot[key]['line_yvals']
                if kwargs.get('show_isolated_mw', False):
                    if key != kwargs['mw_selection']: continue
                    else:
                        legend_text.append([replot[key]['color'], replot[key]['label']])
                        # adjust offset so its closer to the MS plot
                        offset = np.min(replot[key]['line_yvals']) + 0.05
                        line_yvals = line_yvals - offset
                
                if kwargs['show_markers']:
                    self.plotUnidec_individualPeaks.onAddMarker(replot[key]['scatter_xvals'], 
                                                                scatter_yvals, 
                                                                color=replot[key]['color'], 
                                                                marker=replot[key]['marker'], size=50,
                                                                label=replot[key]['label'], as_line=False)
                if kwargs['show_individual_lines']:
                    self.plotUnidec_individualPeaks.plot_1D_add(replot[key]['line_xvals'], 
                                                                line_yvals, 
                                                                color=replot[key]['color'], 
                                                                label=replot[key]['label'],
                                                                allowWheel=False)
        
        else:
            # Plot individual spectra
            stickmax = 1.0
            num = 0
            legend_text = [[[0,0,0], "Raw"]]
            for i in range(0, unidec_eng_data.pks.plen):
                p = unidec_eng_data.pks.peaks[i]
                label = "MW: {:.2f}".format(p.mass)
                if kwargs.get('show_isolated_mw', False):
                    if label != kwargs['mw_selection']: continue
                    
                if p.ignore == 0:
                    list1 = []
                    list2 = []
                    if unidec_eng_data.pks.plen <= 15:
                            color=convertRGB255to1(self.config.customColors[i])
                    else:
                        color=p.color
                    if (not isempty(p.mztab)) and (not isempty(p.mztab2)):
                        mztab = np.array(p.mztab)
                        mztab2 = np.array(p.mztab2)
                        maxval = np.amax(mztab[:, 1])
                        for k in range(0, len(mztab)):
                            if mztab[k, 1] > unidec_eng_data.config.peakplotthresh * maxval:
                                list1.append(mztab2[k, 0])
                                list2.append(mztab2[k, 1])
                                
                        legend_text.append([color, "MW: {:.2f}".format(p.mass)])
                        if kwargs['show_markers']:
                            self.plotUnidec_individualPeaks.onAddMarker(np.array(list1), np.array(list2), 
                                                                        color=color, marker=p.marker, size=50,
                                                                        label="MW: {:.2f}".format(p.mass),
                                                                        as_line=False)
                    if kwargs['show_individual_lines']:
                        self.plotUnidec_individualPeaks.plot_1D_add(unidec_eng_data.data.data2[:, 0], 
                                                                    np.array(p.stickdat)/stickmax-(num + 1) * unidec_eng_data.config.separation, 
                                                                    color, 
                                                                    label="MW: {:.2f}".format(p.mass))
                    num += 1
        # Add legend
        self.plotUnidec_individualPeaks.plot_1D_add_legend(legend_text, **plt_kwargs)
        self.plotUnidec_individualPeaks.repaint()
    
    def on_plot_unidec_MW_v_Charge(self, unidec_eng_data=None, replot=None, **kwargs):
        """
        Plot simple Mass spectrum before it is pre-processed
        @param unidec_eng_data (object):  reference to unidec engine data structure
        """
        
        # Build kwargs
        plt_kwargs = self.presenter._buildPlotParameters(plotType='2D')
        plt_kwargs['colorbar'] = True
        
        if unidec_eng_data is None and replot is not None:
            xvals = replot['xvals']
            yvals = replot['yvals']
            zvals = replot['zvals']
        else:
            xvals=unidec_eng_data.massdat[:, 0]
            yvals=unidec_eng_data.ztab
            zvals=unidec_eng_data.massgrid
            
        # Check that cmap modifier is included
        cmapNorm = self.presenter.onCmapNormalization(zvals, 
                                                      min=self.config.minCmap, 
                                                      mid=self.config.midCmap, 
                                                      max=self.config.maxCmap,
                                                      )
        plt_kwargs['colormap_norm'] = cmapNorm
        
        self.plotUnidec_mwVsZ.clearPlot()
        self.plotUnidec_mwVsZ.plot_2D_contour_unidec(xvals=xvals, yvals=yvals,
                                                     zvals=zvals, xlabel="Mass (Da)", 
                                                     ylabel="Charge",
                                                     axesSize=self.config._plotSettings['UniDec (MW vs Charge)']['axes_size'],
                                                     plotType='MS', plotName="zGrid", testX=True,
                                                     speedy=kwargs.get('speedy',True),
                                                     title="Mass vs Charge",
                                                     **plt_kwargs)
        # Show the mass spectrum
        self.plotUnidec_mwVsZ.repaint()
    
    def on_plot_unidec_barChart(self, unidec_eng_data=None, replot=None, show="height", **kwargs):
        """
        Plot simple Mass spectrum before it is pre-processed
        @param unidec_eng_data (object):  reference to unidec engine data structure
        """
        # Build kwargs
        plt_kwargs = self.presenter._buildPlotParameters(plotType='1D')
            
        if unidec_eng_data is None and replot is not None:
            xvals = replot['xvals']
            yvals = replot['yvals']
            labels = replot['labels']
            colors = replot['colors']
            legend_text = replot['legend_text']
            markers = replot['markers']
        else:
            if unidec_eng_data.pks.plen > 0:
                yvals, colors, labels, legend_text = [], [], [], []
                num = 0
                for p in unidec_eng_data.pks.peaks:
                    if p.ignore == 0:
                        
                        if show == "height":
                            yvals.append(p.height)
                        elif show == "integral":
                            yvals.append(p.integral)
                        if unidec_eng_data.pks.plen <= 15:
                            color = convertRGB255to1(self.config.customColors[num])
                        else:
                            color = p.color
                        labels.append(p.label)
                        colors.append(color)
                        legend_text.append([color, "MW: {:.2f} ({})".format(p.mass, p.label)])
#                         print("MW: {:.2f}".format(p.mass), p.label)
#                         labels.append("MW: {:.2f}".format(p.mass))#p.label)
                        num += 1
                xvals = range(0, num)
            
        self.plotUnidec_barChart.clearPlot()
        self.plotUnidec_barChart.plot_1D_barplot(xvals, yvals, labels, colors,
                                                 axesSize=self.config._plotSettings['UniDec (Barplot)']['axes_size'],
                                                 title="Peak Intensities",
                                                 ylabel="Intensity",
                                                 plotType="Barchart",
                                                 **plt_kwargs)
            
        if unidec_eng_data is None and replot is not None:
            if kwargs['show_markers']:
                for i in range(len(markers)):
                    self.plotUnidec_barChart.onAddMarker(xvals[i], yvals[i], color=colors[i], marker=markers[i], size=10)
                
        else:
            if kwargs['show_markers']:
                # add marker
                num = 0
                for p in unidec_eng_data.pks.peaks:
                    if p.ignore == 0:
                        if unidec_eng_data.pks.plen <= 15:
                            color=convertRGB255to1(self.config.customColors[num])
                        else:
                            color=p.color
                        
                        if show == "height":
                            y = p.height
                        elif show == "integral":
                            y = p.integral
                        else:
                            y = 0
                        self.plotUnidec_barChart.onAddMarker(num, y, color=color, marker=p.marker, size=10)
                        num += 1
        
        # Add legend
        self.plotUnidec_barChart.plot_1D_add_legend(legend_text, **plt_kwargs)
        self.plotUnidec_barChart.repaint()
        
    def plot_1D_update(self, plotName='all', evt=None):
        
        plt_kwargs = self.presenter._buildPlotParameters(plotType='1D')
       
        if plotName in ['all', 'MS']:
            try:
                self.plot1.plot_1D_update(**plt_kwargs)
                self.plot1.repaint()
            except AttributeError: pass
        
        if plotName in ['all', 'RT']:
            try:
                self.plotRT.plot_1D_update(**plt_kwargs)
                self.plotRT.repaint()
            except AttributeError: pass
            
        if plotName in ['all', '1D']:
            try:
                self.plot1D.plot_1D_update(**plt_kwargs)
                self.plot1D.repaint()
            except AttributeError: pass
            
        if plotName in ['all', 'RMSF']:
            plt_kwargs = self.presenter._buildPlotParameters(plotType='2D')
            rmsd_kwargs = self.presenter._buildPlotParameters(plotType='RMSF')
            plt_kwargs = merge_two_dicts(plt_kwargs, rmsd_kwargs)
            try:
                self.plotRMSF.plot_1D_update_rmsf(**plt_kwargs)
                self.plotRMSF.repaint()
            except AttributeError: pass
        
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
         
        # check limits
        try:
            if math.isnan(xlimits.get(0, msX[0])): xlimits[0] = msX[0]
            if math.isnan(xlimits.get(1, msX[-1])): xlimits[1] = msX[-1]
        except:
            xlimits = [np.min(msX), np.max(msX)]
            
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
        
        if plotName in ['all', 'UniDec']:
            
            try:
                self.plotUnidec_mzGrid.plot_2D_update(**plt_kwargs)
                self.plotUnidec_mzGrid.repaint()
            except AttributeError: pass
            
            try:
                self.plotUnidec_mwVsZ.plot_2D_update(**plt_kwargs)
                self.plotUnidec_mwVsZ.repaint()
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
        
    def on_plot_waterfall(self, xvals, yvals, zvals, xlabel,  ylabel, colors=[], e=None, **kwargs):

        # Check if cmap should be overwritten
        cmap = self.config.currentCmap
                
        plt_kwargs = self.presenter._buildPlotParameters(plotType='1D')
        waterfall_kwargs = self.presenter._buildPlotParameters(plotType='waterfall')
        plt_kwargs = merge_two_dicts(plt_kwargs, waterfall_kwargs)
        plt_kwargs['colormap'] = cmap
        if 'increment' in kwargs:
            plt_kwargs['increment'] = kwargs['increment']
        
        self.plotWaterfallIMS.clearPlot()
        self.plotWaterfallIMS.plot_1D_waterfall(xvals=xvals, yvals=yvals,
                                                zvals=zvals, label="", 
                                                xlabel=xlabel, 
                                                ylabel=ylabel,
                                                colorList=colors,
                                                axesSize=self.config._plotSettings['Waterfall']['axes_size'],
                                                plotName='1D',
                                                **plt_kwargs)
        
        if ('add_legend' in kwargs and 'labels' in kwargs and
            len(colors) == len(kwargs['labels'])):
            if kwargs['add_legend']:
                legend_text = zip(colors, kwargs['labels'])
                self.plotWaterfallIMS.plot_1D_add_legend(legend_text, **plt_kwargs)
        
        # Show the mass spectrum
        self.plotWaterfallIMS.repaint() 
       
    def plot_1D_waterfall_update(self, which='other'):
        plt_kwargs = self.presenter._buildPlotParameters(plotType='1D')
        waterfall_kwargs = self.presenter._buildPlotParameters(plotType='waterfall')
        plt_kwargs = merge_two_dicts(plt_kwargs, waterfall_kwargs)
        plt_kwargs['colormap'] = self.config.currentCmap
        
        self.plotWaterfallIMS.plot_1D_waterfall_update(which=which, **plt_kwargs)
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
        
    def plot_colorbar_update(self, plot_window=""):
        plt_kwargs = self.presenter._buildPlotParameters(plotType='2D')
        if plot_window == "2D" or self.currentPage == "2D":
            self.plot2D.plot_2D_colorbar_update(**plt_kwargs)
            self.plot2D.repaint()
        elif plot_window == "RMSD" or self.currentPage == "RMSF":
            self.plotRMSF.plot_2D_colorbar_update(**plt_kwargs)
            self.plotRMSF.repaint()
        elif plot_window == "Comparison" or self.currentPage == "Comparison":
            self.plotCompare.plot_2D_colorbar_update(**plt_kwargs)
            self.plotCompare.repaint()
        elif plot_window == "UniDec" or self.currentPage == "UniDec":
            self.plotUnidec_mzGrid.plot_2D_colorbar_update(**plt_kwargs)
            self.plotUnidec_mzGrid.repaint()
            
            self.plotUnidec_mwVsZ.plot_2D_colorbar_update(**plt_kwargs)
            self.plotUnidec_mwVsZ.repaint()
        
    def plot_normalization_update(self, plot_window=""):
        plt_kwargs = self.presenter._buildPlotParameters(plotType='2D')
        
        if plot_window == "2D" or self.currentPage == "2D":
            self.plot2D.plot_2D_update_normalization(**plt_kwargs)
            self.plot2D.repaint()
        elif plot_window == "Comparison" or self.currentPage == "Comparison":
            self.plotCompare.plot_2D_colorbar_update(**plt_kwargs)
            self.plotCompare.repaint()
        elif plot_window == "UniDec" or self.currentPage == "UniDec":
            self.plotUnidec_mzGrid.plot_2D_update_normalization(**plt_kwargs)
            self.plotUnidec_mzGrid.repaint()
            
            self.plotUnidec_mwVsZ.plot_2D_update_normalization(**plt_kwargs)
            self.plotUnidec_mwVsZ.repaint()
        
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
        
    def on_plot_grid(self, zvals_1, zvals_2, zvals_cum, xvals, yvals, xlabel, ylabel, 
                     cmap_1, cmap_2, **kwargs):

        plt_kwargs = self.presenter._buildPlotParameters(plotType='2D')
        rmsd_kwargs = self.presenter._buildPlotParameters(plotType='RMSD')
        plt_kwargs = merge_two_dicts(plt_kwargs, rmsd_kwargs)
        plt_kwargs['colormap_1'] = cmap_1
        plt_kwargs['colormap_2'] = cmap_2
        
        plt_kwargs['cmap_norm_1'] = self.presenter.onCmapNormalization(zvals_1, 
                                                         min=self.config.minCmap, 
                                                         mid=self.config.midCmap, 
                                                         max=self.config.maxCmap)
        plt_kwargs['cmap_norm_2'] = self.presenter.onCmapNormalization(zvals_2, 
                                                         min=self.config.minCmap, 
                                                         mid=self.config.midCmap, 
                                                         max=self.config.maxCmap)
        plt_kwargs['cmap_norm_cum'] = self.presenter.onCmapNormalization(zvals_cum, 
                                                         min=-100, mid=0, max=100)
        self.plotOverlay.clearPlot()
        self.plotOverlay.plot_grid_2D_overlay(zvals_1, zvals_2, zvals_cum, xvals, yvals, 
                                              xlabel, ylabel, 
                                              axesSize=self.config._plotSettings['Overlay (Grid)']['axes_size'], 
                                              **plt_kwargs)
        self.plotOverlay.repaint()
        
    def on_plot_n_grid(self, n_zvals, cmap_list, title_list, xvals, yvals, xlabel, ylabel):
        plt_kwargs = self.presenter._buildPlotParameters(plotType='2D')
        self.plotOverlay.clearPlot()
        self.plotOverlay.plot_n_grid_2D_overlay(n_zvals, cmap_list, title_list, 
                                                xvals, yvals, xlabel, ylabel, 
                                                axesSize=self.config._plotSettings['Overlay (Grid)']['axes_size'], 
                                                **plt_kwargs)
        self.plotOverlay.repaint()        

    def plot_compare(self, msX=None, msX_1=None, msX_2=None, msY_1=None, msY_2=None, 
                     msY=None, xlimits=None, replot=False, override=True, evt=None):

        if replot:
            data = self.presenter._get_replot_data('compare_MS')
            if data['subtract']:
                msX = data['xvals']
                msY = data['yvals']
                xlimits = data['xlimits']
            else:
                msX = data['xvals']
                msX_1 = data['xvals1']
                msX_2 = data['xvals2']
                msY_1 = data['yvals1']
                msY_2 = data['yvals2']
                xlimits = data['xlimits']
                legend = data['legend']
#                 return
        else:
            legend = self.config.compare_massSpectrum 
            subtract = self.config.compare_massSpectrumParams['subtract']
 
        # Build kwargs
        plt_kwargs = self.presenter._buildPlotParameters(plotType='1D')

        self.plot1.clearPlot()
        if subtract:
            try:
                self.plot1.plot_1D(xvals=msX, yvals=msY, 
                                   xlimits=xlimits,
                                   zoom='box', title="", xlabel="m/z",
                                   ylabel="Intensity", label="",  
                                   lineWidth=self.config.lineWidth_1D,
                                   axesSize=self.config._plotSettings['MS']['axes_size'],
                                   plotType='MS',
                                   **plt_kwargs)
            except:
                self.plot1.repaint()
            if override:
                self.config.replotData['compare_MS'] = {'xvals':msX, 
                                                        'yvals':msY,
                                                        'xlimits':xlimits,
                                                        'subtract':subtract}
        else:
            try:
                self.plot1.plot_1D_compare(xvals1=msX_1, xvals2=msX_2,
                                           yvals1=msY_1, yvals2=msY_2, 
                                           xlimits=xlimits,
                                           zoom='box', title="", 
                                           xlabel="m/z", ylabel="Intensity",
                                           label=legend,  
                                           lineWidth=self.config.lineWidth_1D,
                                           axesSize=self.config._plotSettings['MS (compare)']['axes_size'],
                                           plotType='compare',
                                           **plt_kwargs)
            except:
                self.plot1.repaint()
            if override:
                self.config.replotData['compare_MS'] = {'xvals':msX, 
                                                        'xvals1':msX_1,
                                                        'xvals2':msX_2,
                                                        'yvals1':msY_1,
                                                        'yvals2':msY_2,
                                                        'xlimits':xlimits,
                                                        'legend':legend,
                                                        'subtract':subtract}
        # Show the mass spectrum
        self.plot1.repaint()
        
        
        
        
        