# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
#    Copyright (C) 2017-2018 Lukasz G. Migas 
#    <lukasz.migas@manchester.ac.uk> OR <lukas.migas@yahoo.com>
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
# __author__ lukasz.g.migas

from __future__ import division
import wx, time, math, matplotlib, os
import numpy as np
import seaborn as sns
import plots as plots
import matplotlib.pyplot as plt
from natsort import natsorted
from wx.lib.pubsub import pub 

from ids import *
from styles import makeMenuItem
from icons import IconContainer as icons
from toolbox import (isempty, merge_two_dicts, convertRGB1to255, convertRGB255to1, 
                             convertRGB1toHEX, dir_extra, randomColorGenerator)
from dialogs import dlgBox
from panelCustomisePlot import panelCustomisePlot

class panelPlot(wx.Panel):
    def __init__(self, parent, config, presenter):
        wx.Panel.__init__ ( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition,
                             size = wx.Size( 800, 600 ), style = wx.TAB_TRAVERSAL )
        
        self.config = config
        self.parent = parent
        self.presenter = presenter
        self.icons = icons()
        self.data_processing = self.parent.data_processing
        
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
        self.current_plot = self.plot1
        
        # bind events
        self.mainBook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.onPageChanged)
        
        # initialise
        self.onPageChanged(evt=None)
        
        # initilise pub
        pub.subscribe(self._update_label_position, 'update_text_position') # update position of label
        

    # TODO: arrow positions should be updated automatically
    def _update_label_position(self, text_obj):
        document_title, dataset_name, annotation_name, text_type  = text_obj.obj_name.split('|-|')
        
        # get document
        __, annotations = self.parent.panelDocuments.topP.documents.on_get_annotation_dataset(document_title, dataset_name)
        if text_type == "annotation":
            new_pos_x, new_pos_y = text_obj.get_position()
            annotations[annotation_name]['position_label_x'] = np.round(new_pos_x, 4)
            annotations[annotation_name]['position_label_y'] = np.round(new_pos_y, 4)
            try:
                arrow_kwargs = self._buildPlotParameters(plotType="arrow")
                if annotations[annotation_name].get('add_arrow', False):
                    for i, arrow in enumerate(self.current_plot.arrows):
                        if arrow.obj_name == text_obj.obj_name:
                            arrow_x_end, arrow_y_end = arrow.obj_props
                            arrow_kwargs['text_name'] = arrow.obj_name
                            arrow_kwargs['props'] = [arrow_x_end, arrow_y_end]
                            
                            # remove all arrow
                            del self.current_plot.arrows[i]
                            arrow.remove()
                            
                            # add arrow to plot
                            arrow_list = [new_pos_x, new_pos_y, arrow_x_end-new_pos_x, arrow_y_end-new_pos_y]
                            self.current_plot.plot_add_arrow(
                                arrow_list, stick_to_intensity=True,
                                **arrow_kwargs)
            except: pass
                        
        # update annotation
        self.parent.panelDocuments.topP.documents.onUpdateAnotations(
            annotations, document_title, dataset_name, set_data_only=True)
        
    def onPageChanged(self, evt):
        # get current page
        self.currentPage = self.mainBook.GetPageText(self.mainBook.GetSelection())
        
        # keep track of previous pages
        if self.currentPage in ['MS', 'RT', '1D']:
            self.window_plot1D = self.currentPage
        elif self.currentPage in ['2D', 'DT/MS', 'Waterfall', 'RMSF', 'Comparison', 
                                  'Overlay', 'UniDec', 'Other']:
            self.window_plot2D = self.currentPage
        elif self.currentPage in ['3D']:
            self.window_plot3D = self.currentPage
            
        if self.currentPage == "Waterfall": self.current_plot = self.plotWaterfallIMS
        elif self.currentPage == "MS": self.current_plot = self.plot1
        elif self.currentPage == "1D": self.current_plot = self.plot1D
        elif self.currentPage == "RT": self.current_plot = self.plotRT
        elif self.currentPage == "2D": self.current_plot = self.plot2D
        elif self.currentPage == "DT/MS": self.current_plot = self.plotMZDT
        elif self.currentPage == "Overlay": self.current_plot = self.plotOverlay
        elif self.currentPage == "Other": self.current_plot = self.plotOther
        
            
        # update statusbars
        if self.config.processParamsWindow_on_off:
            self.parent.panelProcessData.updateStatusbar()
            
        if self.config.extraParamsWindow_on_off:
            self.parent.panelParametersEdit.updateStatusbar()    
            
    def makeNotebook(self):
		# Setup notebook
        self.mainBook = wx.Notebook( self, wx.ID_ANY, wx.DefaultPosition,
                                         wx.DefaultSize, 0 )
        # Setup PLOT MS
        self.panelMS = wx.Panel( self.mainBook, wx.ID_ANY, wx.DefaultPosition,
                                    wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.mainBook.AddPage( self.panelMS, u"MS", False )
        
        self.plot1 = plots.plots(self.panelMS, 
                                 figsize=self.config._plotSettings["MS"]['gui_size'], 
                                 config=self.config)
        
        boxsizer_MS = wx.BoxSizer(wx.VERTICAL)
        boxsizer_MS.Add(self.plot1, 1, wx.EXPAND)
        self.panelMS.SetSizer(boxsizer_MS)

        # Setup PLOT RT
        self.panelRT = wx.SplitterWindow(self.mainBook, wx.ID_ANY, wx.DefaultPosition,
                                         wx.DefaultSize, wx.TAB_TRAVERSAL | wx.SP_3DSASH)
        self.mainBook.AddPage( self.panelRT, u"RT", False )        

        # Create two panels for each dataset
        self.topPanelRT_RT = wx.Panel(self.panelRT)
        self.plotRT = plots.plots(self.topPanelRT_RT, 
                                  figsize=self.config._plotSettings["RT"]['gui_size'], 
                                  config=self.config)
        boxTopPanelRT = wx.BoxSizer(wx.VERTICAL)
        boxTopPanelRT.Add(self.plotRT, 1, wx.EXPAND)
        self.topPanelRT_RT.SetSizer(boxTopPanelRT)
         
        self.bottomPanelRT_MS = wx.Panel(self.panelRT)
        self.plotRT_MS = plots.plots(self.bottomPanelRT_MS, 
                                     figsize=self.config._plotSettings["MS (DT/RT)"]['gui_size'], 
                                     config=self.config)
        boxBottomPanelMS = wx.BoxSizer(wx.VERTICAL)
        boxBottomPanelMS.Add(self.plotRT_MS, 1, wx.EXPAND)
        self.bottomPanelRT_MS.SetSizer(boxBottomPanelMS)
         
        # Add panels to splitter window
        self.panelRT.SplitHorizontally(self.topPanelRT_RT, self.bottomPanelRT_MS)
        self.panelRT.SetMinimumPaneSize(300)
        self.panelRT.SetSashGravity(0.5)
        self.panelRT.SetSashSize(5)

        # Setup PLOT 1D
        self.panel1D = wx.SplitterWindow(self.mainBook, wx.ID_ANY, wx.DefaultPosition,
                                         wx.DefaultSize, wx.TAB_TRAVERSAL | wx.SP_3DSASH)
        self.mainBook.AddPage(self.panel1D, u"1D", False)        

        # Create two panels for each dataset
        self.topPanel1D_1D = wx.Panel(self.panel1D)
        self.plot1D = plots.plots(self.topPanel1D_1D, 
                                  figsize=self.config._plotSettings["DT"]['gui_size'], 
                                  config=self.config)
        boxTopPanelMS = wx.BoxSizer(wx.VERTICAL)
        boxTopPanelMS.Add(self.plot1D, 1, wx.EXPAND)
        self.topPanel1D_1D.SetSizer(boxTopPanelMS)
         
        self.bottomPanel1D_MS = wx.Panel(self.panel1D)
        self.plot1D_MS = plots.plots(self.bottomPanel1D_MS, 
                                     figsize=self.config._plotSettings["MS (DT/RT)"]['gui_size'], 
                                     config=self.config)
        boxBottomPanel1DT = wx.BoxSizer(wx.VERTICAL)
        boxBottomPanel1DT.Add(self.plot1D_MS, 1, wx.EXPAND)
        self.bottomPanel1D_MS.SetSizer(boxBottomPanel1DT)
         
        # Add panels to splitter window
        self.panel1D.SplitHorizontally(self.topPanel1D_1D, self.bottomPanel1D_MS)
        self.panel1D.SetMinimumPaneSize(300)
        self.panel1D.SetSashGravity(0.5)
        self.panel1D.SetSashSize(5)
        
        # Setup PLOT 2D
        self.panel2D = wx.Panel(self.mainBook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.mainBook.AddPage(self.panel2D, u"2D", False)

        self.plot2D = plots.plots(self.panel2D, 
                                  figsize=self.config._plotSettings["2D"]['gui_size'], 
                                  config=self.config) 
        
        boxsizer_2D = wx.BoxSizer(wx.HORIZONTAL)
        boxsizer_2D.Add(self.plot2D, 1, wx.EXPAND | wx.ALL)
        self.panel2D.SetSizerAndFit(boxsizer_2D)         
        
        # Setup PLOT DT/MS
        self.panelMZDT = wx.Panel( self.mainBook, wx.ID_ANY, wx.DefaultPosition, 
                                   wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.mainBook.AddPage( self.panelMZDT, u"DT/MS", False )

        self.plotMZDT = plots.plots(self.panelMZDT, 
                                    figsize=self.config._plotSettings["DT/MS"]['gui_size'], 
                                    config=self.config) 
          
        boxsizer_MZDT = wx.BoxSizer(wx.HORIZONTAL)
        boxsizer_MZDT.Add(self.plotMZDT, 1, wx.EXPAND | wx.ALL)
        self.panelMZDT.SetSizerAndFit(boxsizer_MZDT)

        # Setup PLOT WATERFALL
        self.waterfallIMS = wx.Panel( self.mainBook, wx.ID_ANY, wx.DefaultPosition, 
                                   wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.mainBook.AddPage( self.waterfallIMS, u"Waterfall", False )

        self.plotWaterfallIMS = plots.plots(self.waterfallIMS, 
                                            figsize=self.config._plotSettings["Waterfall"]['gui_size'], 
                                            config=self.config)
        
        boxsizer_waterfall = wx.BoxSizer(wx.HORIZONTAL)
        boxsizer_waterfall.Add(self.plotWaterfallIMS, 1, wx.EXPAND | wx.ALL)
        self.waterfallIMS.SetSizerAndFit(boxsizer_waterfall)     

        # Setup PLOT 3D
        self.panel3D = wx.Panel( self.mainBook, wx.ID_ANY, wx.DefaultPosition, 
                                   wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.mainBook.AddPage( self.panel3D, u"3D", False )
        
        self.plot3D = plots.plots(self.panel3D, 
                                  figsize=self.config._plotSettings["3D"]['gui_size'], 
                                  config=self.config)

        boxsizer_3D = wx.BoxSizer(wx.VERTICAL)     
        boxsizer_3D.Add(self.plot3D, 1, wx.EXPAND)
        self.panel3D.SetSizer(boxsizer_3D)  
        
        # Setup PLOT RMSF
        self.panelRMSF = wx.Panel( self.mainBook, wx.ID_ANY, wx.DefaultPosition, 
                                   wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.mainBook.AddPage( self.panelRMSF, u"RMSF", False )

        self.plotRMSF = plots.plots(self.panelRMSF, 
                                    figsize=self.config._plotSettings["RMSF"]['gui_size'], 
                                    config=self.config)
        boxsizer_RMSF = wx.BoxSizer(wx.VERTICAL)     
        boxsizer_RMSF.Add(self.plotRMSF, 1, wx.EXPAND)
        self.panelRMSF.SetSizer(boxsizer_RMSF)  
        
        
        # Setup PLOT Comparison
        self.panelCompare = wx.Panel( self.mainBook, wx.ID_ANY, wx.DefaultPosition, 
                                   wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.mainBook.AddPage( self.panelCompare, u"Comparison", False )

        self.plotCompare = plots.plots(self.panelCompare, 
                                       figsize=self.config._plotSettings["Comparison"]['gui_size'],
                                       config=self.config)
        boxsizer_compare = wx.BoxSizer(wx.VERTICAL)     
        boxsizer_compare.Add(self.plotCompare, 1, wx.EXPAND)
        self.panelCompare.SetSizer(boxsizer_compare)  
        
        # Setup PLOT Overlay
        self.panelOverlay = wx.Panel( self.mainBook, wx.ID_ANY, wx.DefaultPosition, 
                                   wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.mainBook.AddPage( self.panelOverlay, u"Overlay", False )

        self.plotOverlay = plots.plots(self.panelOverlay, 
                                       figsize=self.config._plotSettings["Overlay"]['gui_size'],
                                       config=self.config)

        
        boxsizer_overlay = wx.BoxSizer(wx.VERTICAL)     
        boxsizer_overlay.Add(self.plotOverlay, 1, wx.EXPAND)
        self.panelOverlay.SetSizer(boxsizer_overlay)  
        
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
        self.topPlotMS = plots.plots(self.topPanelMS, 
                                     figsize=self.config._plotSettings["Calibration (MS)"]['gui_size'],
                                     config=self.config)
        boxTopPanelMS = wx.BoxSizer(wx.VERTICAL)
        boxTopPanelMS.Add(self.topPlotMS, 1, wx.EXPAND)
        self.topPanelMS.SetSizer(boxTopPanelMS)
        
        # Plot 1DT
        self.bottomPlot1DT = plots.plots(self.bottomPanel1DT, 
                                         figsize=self.config._plotSettings["Calibration (DT)"]['gui_size'],
                                         config=self.config)
        boxBottomPanel1DT = wx.BoxSizer(wx.VERTICAL)
        boxBottomPanel1DT.Add(self.bottomPlot1DT, 1, wx.EXPAND)
        self.bottomPanel1DT.SetSizer(boxBottomPanel1DT)
        
        if self.config.unidec_plot_panel_view == "Single page view":
            self.panelUniDec = wx.lib.scrolledpanel.ScrolledPanel(self.mainBook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, # @UndefinedVariable
                                                                  wx.TAB_TRAVERSAL) 
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
        
            plotUnidecSizer = wx.GridBagSizer(10, 10)
            plotUnidecSizer.Add(self.plotUnidec_MS, (0, 0), span=(1, 1), flag=wx.EXPAND)
            plotUnidecSizer.Add(self.plotUnidec_mwDistribution, (0, 1), span=(1, 1), flag=wx.EXPAND)
            plotUnidecSizer.Add(self.plotUnidec_mzGrid, (1, 0), span=(1, 1), flag=wx.EXPAND)
            plotUnidecSizer.Add(self.plotUnidec_individualPeaks, (1, 1), span=(1, 1), flag=wx.EXPAND)
            plotUnidecSizer.Add(self.plotUnidec_mwVsZ, (2, 0), span=(1, 1), flag=wx.EXPAND)
            plotUnidecSizer.Add(self.plotUnidec_barChart, (2, 1), span=(1, 1), flag=wx.EXPAND)
            plotUnidecSizer.Add(self.plotUnidec_chargeDistribution, (3, 0), span=(1, 1), flag=wx.EXPAND)
            self.panelUniDec.SetSizer(plotUnidecSizer)
        else:
            self.panelUniDec = wx.Panel( self.mainBook, wx.ID_ANY, wx.DefaultPosition, 
                                       wx.DefaultSize, wx.TAB_TRAVERSAL )
            self.mainBook.AddPage( self.panelUniDec, u"UniDec", False )
            
            # Setup notebook
            self.unidec_notebook = wx.Notebook(self.panelUniDec, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
            # Setup PLOT MS
            self.unidec_MS = wx.Panel(self.unidec_notebook, wx.ID_ANY, wx.DefaultPosition,
                                    wx.DefaultSize, wx.TAB_TRAVERSAL )
            self.unidec_notebook.AddPage(self.unidec_MS, u"MS", False )
            figsize = self.config._plotSettings["UniDec (MS)"]['gui_size']
            self.plotUnidec_MS = plots.plots(self.unidec_MS, config=self.config, figsize=figsize)
            boxsizer_unidec_MS = wx.BoxSizer(wx.VERTICAL)     
            boxsizer_unidec_MS.Add(self.plotUnidec_MS, 1, wx.EXPAND)
            self.unidec_MS.SetSizer(boxsizer_unidec_MS)  
             
            self.unidec_mzGrid = wx.Panel(self.unidec_notebook, wx.ID_ANY, wx.DefaultPosition,
                                    wx.DefaultSize, wx.TAB_TRAVERSAL )
            self.unidec_notebook.AddPage(self.unidec_mzGrid, u"m/z vs Charge", False )
            figsize = self.config._plotSettings["UniDec (m/z vs Charge)"]['gui_size']
            self.plotUnidec_mzGrid = plots.plots(self.unidec_mzGrid, config=self.config, figsize=figsize)
            boxsizer_unidec_mzGrid = wx.BoxSizer(wx.VERTICAL)     
            boxsizer_unidec_mzGrid.Add(self.plotUnidec_mzGrid, 1, wx.EXPAND)
            self.unidec_mzGrid.SetSizer(boxsizer_unidec_mzGrid)  
             
            self.unidec_mwVsZ = wx.Panel(self.unidec_notebook, wx.ID_ANY, wx.DefaultPosition,
                                    wx.DefaultSize, wx.TAB_TRAVERSAL )
            self.unidec_notebook.AddPage(self.unidec_mwVsZ, u"MW vs Charge", False )
            figsize = self.config._plotSettings["UniDec (MW vs Charge)"]['gui_size']
            self.plotUnidec_mwVsZ = plots.plots(self.unidec_mwVsZ, config=self.config, figsize=figsize)
            boxsizer_unidec__mwVsZ = wx.BoxSizer(wx.VERTICAL)     
            boxsizer_unidec__mwVsZ.Add(self.plotUnidec_mwVsZ, 1, wx.EXPAND)
            self.unidec_mwVsZ.SetSizer(boxsizer_unidec__mwVsZ)  
             
            self.unidec_mwDistribution = wx.Panel(self.unidec_notebook, wx.ID_ANY, wx.DefaultPosition,
                                    wx.DefaultSize, wx.TAB_TRAVERSAL )
            self.unidec_notebook.AddPage(self.unidec_mwDistribution, u"MW", False )
            figsize = self.config._plotSettings["UniDec (MW)"]['gui_size']
            self.plotUnidec_mwDistribution = plots.plots(self.unidec_mwDistribution, config=self.config, figsize=figsize)
            boxsizer_unidec_mwDistribution = wx.BoxSizer(wx.VERTICAL)     
            boxsizer_unidec_mwDistribution.Add(self.plotUnidec_mwDistribution, 1, wx.EXPAND)
            self.unidec_mwDistribution.SetSizer(boxsizer_unidec_mwDistribution)  
             
            self.unidec_individualPeaks = wx.Panel(self.unidec_notebook, wx.ID_ANY, wx.DefaultPosition,
                                                   wx.DefaultSize, wx.TAB_TRAVERSAL )
            self.unidec_notebook.AddPage(self.unidec_individualPeaks, u"Isolated MS", False )
            figsize = self.config._plotSettings["UniDec (Isolated MS)"]['gui_size']
            self.plotUnidec_individualPeaks = plots.plots(self.unidec_individualPeaks, config=self.config, figsize=figsize)
            boxsizer_unidec_individualPeaks = wx.BoxSizer(wx.VERTICAL)     
            boxsizer_unidec_individualPeaks.Add(self.plotUnidec_individualPeaks, 1, wx.EXPAND)
            self.unidec_individualPeaks.SetSizer(boxsizer_unidec_individualPeaks)  
 
             
            self.unidec_barChart = wx.Panel(self.unidec_notebook, wx.ID_ANY, wx.DefaultPosition,
                                    wx.DefaultSize, wx.TAB_TRAVERSAL )
            self.unidec_notebook.AddPage(self.unidec_barChart, u"Barplot", False )
            figsize = self.config._plotSettings["UniDec (Barplot)"]['gui_size']
            self.plotUnidec_barChart = plots.plots(self.unidec_barChart, 
                                                   config=self.config, 
                                                   figsize=figsize)
            boxsizer_unidec_barChart = wx.BoxSizer(wx.VERTICAL)     
            boxsizer_unidec_barChart.Add(self.plotUnidec_barChart, 1, wx.EXPAND)
            self.unidec_barChart.SetSizer(boxsizer_unidec_barChart)  
             
            self.unidec_chargeDistribution = wx.Panel(self.unidec_notebook, wx.ID_ANY, wx.DefaultPosition,
                                    wx.DefaultSize, wx.TAB_TRAVERSAL )
            self.unidec_notebook.AddPage(self.unidec_chargeDistribution, u"Charge distribution", False )
            figsize = self.config._plotSettings["UniDec (Charge Distribution)"]['gui_size']
            self.plotUnidec_chargeDistribution = plots.plots(self.unidec_chargeDistribution, 
                                                             config=self.config, 
                                                             figsize=figsize)
            boxsizer_unidec_chargeDistribution = wx.BoxSizer(wx.VERTICAL)     
            boxsizer_unidec_chargeDistribution.Add(self.plotUnidec_chargeDistribution, 1, wx.EXPAND)
            self.unidec_chargeDistribution.SetSizer(boxsizer_unidec_chargeDistribution)  
            
            tabSizer = wx.BoxSizer( wx.VERTICAL )
            tabSizer.Add(self.unidec_notebook, 1, wx.EXPAND |wx.ALL, 1)
            self.panelUniDec.SetSizerAndFit(tabSizer)
        
        
        # Other
        self.panelOther = wx.Panel( self.mainBook, wx.ID_ANY, wx.DefaultPosition, 
                                   wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.mainBook.AddPage( self.panelOther, u"Other", False )        

        self.plotOther = plots.plots(self.panelOther, 
                                     figsize=self.config._plotSettings["2D"]['gui_size'], 
                                     config=self.config)

        boxsizer_other = wx.BoxSizer(wx.VERTICAL)
        boxsizer_other.Add(self.plotOther, 1, wx.EXPAND)
        self.panelOther.SetSizer(boxsizer_other)
        
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

        mainSizer = wx.BoxSizer( wx.VERTICAL )
        mainSizer.Add(self.mainBook, 1, wx.EXPAND |wx.ALL, 1)
        
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnRightClickMenu)
        self.SetSizer(mainSizer)
        self.Layout()
        self.Show(True)
        
        
        # now that we set sizer, we can get window size
        panel_size = self.mainBook.GetSize()[1]
        half_size = (panel_size - 50) / 2
        
        self.panel1D.SetMinimumPaneSize(half_size)
        self.panelRT.SetMinimumPaneSize(half_size)
        
    def OnRightClickMenu(self, evt):
        self.currentPage = self.mainBook.GetPageText(self.mainBook.GetSelection())
        
        # Make bindings    
        self.Bind(wx.EVT_MENU, self.data_processing.on_smooth_1D_and_add_data, id=ID_smooth1DdataMS)
        self.Bind(wx.EVT_MENU, self.data_processing.on_smooth_1D_and_add_data, id=ID_smooth1DdataRT) 
        self.Bind(wx.EVT_MENU, self.data_processing.on_smooth_1D_and_add_data, id=ID_smooth1Ddata1DT) 
        self.Bind(wx.EVT_MENU, self.presenter.onShowExtractedIons, id=ID_highlightRectAllIons) 
        self.Bind(wx.EVT_MENU, self.data_processing.on_pick_peaks, id=ID_pickMSpeaksDocument)
        self.Bind(wx.EVT_MENU, self.onClearPlot, id=ID_clearPlot_MS)
        self.Bind(wx.EVT_MENU, self.onClearPlot, id=ID_clearPlot_RT)
        self.Bind(wx.EVT_MENU, self.onClearPlot, id=ID_clearPlot_RT_MS)
        self.Bind(wx.EVT_MENU, self.onClearPlot, id=ID_clearPlot_1D)
        self.Bind(wx.EVT_MENU, self.onClearPlot, id=ID_clearPlot_1D_MS)
        self.Bind(wx.EVT_MENU, self.onClearPlot, id=ID_clearPlot_2D)
        self.Bind(wx.EVT_MENU, self.onClearPlot, id=ID_clearPlot_3D)
        self.Bind(wx.EVT_MENU, self.onClearPlot, id=ID_clearPlot_RMSF)
        self.Bind(wx.EVT_MENU, self.onClearPlot, id=ID_clearPlot_RMSD)
        self.Bind(wx.EVT_MENU, self.onClearPlot, id=ID_clearPlot_Matrix)
        self.Bind(wx.EVT_MENU, self.onClearPlot, id=ID_clearPlot_Overlay)
        self.Bind(wx.EVT_MENU, self.onClearPlot, id=ID_clearPlot_Watefall)
        self.Bind(wx.EVT_MENU, self.onClearPlot, id=ID_clearPlot_Calibration)
        self.Bind(wx.EVT_MENU, self.onClearPlot, id=ID_clearPlot_MZDT)
        self.Bind(wx.EVT_MENU, self.onClearPlot, id=ID_clearPlot_Waterfall)
        self.Bind(wx.EVT_MENU, self.onClearPlot, id=ID_clearPlot_other)
        self.Bind(wx.EVT_MENU, self.onClearPlot, id=ID_clearPlot_UniDec_MS)
        self.Bind(wx.EVT_MENU, self.onClearPlot, id=ID_clearPlot_UniDec_mwDistribution)
        self.Bind(wx.EVT_MENU, self.onClearPlot, id=ID_clearPlot_UniDec_mzGrid)
        self.Bind(wx.EVT_MENU, self.onClearPlot, id=ID_clearPlot_UniDec_mwGrid)
        self.Bind(wx.EVT_MENU, self.onClearPlot, id=ID_clearPlot_UniDec_pickedPeaks)
        self.Bind(wx.EVT_MENU, self.onClearPlot, id=ID_clearPlot_UniDec_barchart)
        self.Bind(wx.EVT_MENU, self.onClearPlot, id=ID_clearPlot_UniDec_chargeDistribution)
        
        self.Bind(wx.EVT_MENU, self.on_clear_unidec, id=ID_clearPlot_UniDec_all)
        self.Bind(wx.EVT_MENU, self.onSetupMenus, id=ID_plotPanel_binMS)
        self.Bind(wx.EVT_MENU, self.onLockPlot, id=ID_plotPanel_lockPlot)
        self.Bind(wx.EVT_MENU, self.on_rotate_plot, id=ID_plots_rotate90)
        self.Bind(wx.EVT_MENU, self.on_resize_check, id=ID_plotPanel_resize)
        
        
        self.Bind(wx.EVT_MENU, self.customisePlot, id=ID_plots_customisePlot)
        self.Bind(wx.EVT_MENU, self.customisePlot, id=ID_plots_customisePlot_unidec_ms)
        self.Bind(wx.EVT_MENU, self.customisePlot, id=ID_plots_customisePlot_unidec_mw)
        self.Bind(wx.EVT_MENU, self.customisePlot, id=ID_plots_customisePlot_unidec_mz_v_charge)
        self.Bind(wx.EVT_MENU, self.customisePlot, id=ID_plots_customisePlot_unidec_isolated_mz)
        self.Bind(wx.EVT_MENU, self.customisePlot, id=ID_plots_customisePlot_unidec_mw_v_charge)
        self.Bind(wx.EVT_MENU, self.customisePlot, id=ID_plots_customisePlot_unidec_ms_barchart)
        self.Bind(wx.EVT_MENU, self.customisePlot, id=ID_plots_customisePlot_unidec_chargeDist)
        
        self.Bind(wx.EVT_MENU, self.save_images, id=ID_saveOtherImage)
        self.Bind(wx.EVT_MENU, self.save_images, id=ID_saveCompareMSImage)
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
        customiseUniDecMenu.Append(ID_plots_customisePlot_unidec_mw_v_charge, 'Customise molecular weight vs charge...')
        customiseUniDecMenu.Append(ID_plots_customisePlot_unidec_isolated_mz, 'Customise mass spectrum with isolated species...')
        customiseUniDecMenu.Append(ID_plots_customisePlot_unidec_ms_barchart, 'Customise barchart...')
        customiseUniDecMenu.Append(ID_plots_customisePlot_unidec_chargeDist, 'Customise charge state distribution...')
        
        saveUniDecMenu = wx.Menu()
        saveUniDecMenu.Append(ID_plots_saveImage_unidec_ms, 'Save mass spectrum (.{})'.format(self.config.imageFormat))
        saveUniDecMenu.Append(ID_plots_saveImage_unidec_mw, 'Save Zero charge mass spectrum (.{})'.format(self.config.imageFormat))
        saveUniDecMenu.Append(ID_plots_saveImage_unidec_mz_v_charge, 'Save m/z vs charge (.{})'.format(self.config.imageFormat))
        saveUniDecMenu.Append(ID_plots_saveImage_unidec_mw_v_charge, 'Save molecular weight vs charge (.{})'.format(self.config.imageFormat))
        saveUniDecMenu.Append(ID_plots_saveImage_unidec_isolated_mz, 'Save mass spectrum with isolated species (.{})'.format(self.config.imageFormat))
        saveUniDecMenu.Append(ID_plots_saveImage_unidec_ms_barchart, 'Save barchart (.{})'.format(self.config.imageFormat))
        saveUniDecMenu.Append(ID_plots_saveImage_unidec_chargeDist, 'Save charge state distribution (.{})'.format(self.config.imageFormat))
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
                                         text='Show extracted ions', 
                                         bitmap=self.icons.iconsLib['annotate16']))
            menu.AppendSeparator()
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_extraSettings_general_plot,
                                         text='Edit general parameters...', 
                                         bitmap=self.icons.iconsLib['panel_plot_general_16']))
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_extraSettings_plot1D,
                                         text='Edit plot parameters...', 
                                         bitmap=self.icons.iconsLib['panel_plot1D_16']))
            self.lock_plot_check =  menu.AppendCheckItem(ID_plotPanel_lockPlot, "Lock plot", help="")
            self.lock_plot_check.Check(self.plot1.lock_plot_from_updating)
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_plots_customisePlot,
                                         text='Customise plot...', 
                                         bitmap=self.icons.iconsLib['change_xlabels_16']))
            menu.AppendSeparator()
            self.resize_plot_check =  menu.AppendCheckItem(ID_plotPanel_resize, "Resize on saving", help="")
            self.resize_plot_check.Check(self.config.resize)
            if self.parent.plot_name == "compare_MS":
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveCompareMSImage, text=saveImageLabel, 
                                             bitmap=self.icons.iconsLib['save16']))
            else:
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveMSImage, text=saveImageLabel, 
                                             bitmap=self.icons.iconsLib['save16']))
            menu.AppendSeparator()
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_clearPlot_MS, text="Clear plot", 
                                         bitmap=self.icons.iconsLib['clear_16']))
        elif self.currentPage == "RT":
            if self.parent.plot_name == "MS":
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_clearPlot_RT_MS, text="Clear plot", 
                                             bitmap=self.icons.iconsLib['clear_16']))
            else:
                menu.Append(ID_smooth1DdataRT, "Smooth chromatogram")
                self.binMS_check =  menu.AppendCheckItem(ID_plotPanel_binMS, 
                                                         "Bin mass spectra during extraction",
                                                         help="")
                self.binMS_check.Check(self.config.ms_enable_in_RT)
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_processSettings_MS,
                                             text='Edit extraction parameters...', 
                                             bitmap=self.icons.iconsLib['process_ms_16']))
                menu.AppendSeparator()
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_extraSettings_general_plot,
                                             text='Edit general parameters...', 
                                             bitmap=self.icons.iconsLib['panel_plot_general_16']))
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_extraSettings_plot1D,
                                             text='Edit plot parameters...', 
                                             bitmap=self.icons.iconsLib['panel_plot1D_16']))
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_extraSettings_legend,
                                             text='Edit legend parameters...', 
                                             bitmap=self.icons.iconsLib['panel_legend_16']))
                self.lock_plot_check =  menu.AppendCheckItem(ID_plotPanel_lockPlot, "Lock plot", help="")
                self.lock_plot_check.Check(self.plotRT.lock_plot_from_updating)
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_plots_customisePlot,
                                             text='Customise plot...', 
                                             bitmap=self.icons.iconsLib['change_xlabels_16']))
                menu.AppendSeparator()
                self.resize_plot_check =  menu.AppendCheckItem(ID_plotPanel_resize, "Resize on saving", help="")
                self.resize_plot_check.Check(self.config.resize)
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveRTImage, text=saveImageLabel, 
                                             bitmap=self.icons.iconsLib['save16']))
                menu.AppendSeparator()
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_clearPlot_RT, text="Clear plot", 
                                             bitmap=self.icons.iconsLib['clear_16']))
        elif self.currentPage == "1D":
            if self.parent.plot_name == "MS":
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_clearPlot_1D_MS, text="Clear plot", 
                                             bitmap=self.icons.iconsLib['clear_16']))
            else:
                menu.Append(ID_smooth1Ddata1DT, "Smooth mobiligram")
                self.binMS_check =  menu.AppendCheckItem(ID_plotPanel_binMS, 
                                                         "Bin mass spectra during extraction",
                                                         help="")
                self.binMS_check.Check(self.config.ms_enable_in_RT)
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_processSettings_MS,
                                             text='Edit extraction parameters...', 
                                             bitmap=self.icons.iconsLib['process_ms_16']))
                menu.AppendSeparator()
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_extraSettings_general_plot,
                                             text='Edit general parameters...', 
                                             bitmap=self.icons.iconsLib['panel_plot_general_16']))
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_extraSettings_plot1D,
                                             text='Edit plot parameters...', 
                                             bitmap=self.icons.iconsLib['panel_plot1D_16']))
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_extraSettings_legend,
                                             text='Edit legend parameters...', 
                                             bitmap=self.icons.iconsLib['panel_legend_16']))
                self.lock_plot_check =  menu.AppendCheckItem(ID_plotPanel_lockPlot, "Lock plot", help="")
                self.lock_plot_check.Check(self.plot1D.lock_plot_from_updating)
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_plots_customisePlot,
                                             text='Customise plot...', 
                                             bitmap=self.icons.iconsLib['change_xlabels_16']))
                menu.AppendSeparator()
                self.resize_plot_check =  menu.AppendCheckItem(ID_plotPanel_resize, "Resize on saving", help="")
                self.resize_plot_check.Check(self.config.resize)
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_save1DImage, text=saveImageLabel, 
                                             bitmap=self.icons.iconsLib['save16']))
                menu.AppendSeparator()
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_clearPlot_1D, text="Clear plot", 
                                             bitmap=self.icons.iconsLib['clear_16']))
        elif self.currentPage == "2D":
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_processSettings_2D,
                                         text='Process heatmap...', 
                                         bitmap=self.icons.iconsLib['process_2d_16']))
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_plots_rotate90,
                                         text=u'Rotate 90°', 
                                         bitmap=self.icons.iconsLib['blank_16']))
            menu.AppendSeparator()
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_extraSettings_general_plot,
                                         text='Edit general parameters...', 
                                         bitmap=self.icons.iconsLib['panel_plot_general_16']))
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_extraSettings_plot2D,
                                         text='Edit plot parameters...', 
                                         bitmap=self.icons.iconsLib['panel_plot2D_16']))
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_extraSettings_colorbar,
                                         text='Edit colorbar parameters...', 
                                         bitmap=self.icons.iconsLib['panel_colorbar_16']))
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_extraSettings_legend,
                                         text='Edit legend parameters...', 
                                         bitmap=self.icons.iconsLib['panel_legend_16']))
            self.lock_plot_check =  menu.AppendCheckItem(ID_plotPanel_lockPlot, "Lock plot", help="")
            self.lock_plot_check.Check(self.plot2D.lock_plot_from_updating)
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_plots_customisePlot,
                                         text='Customise plot...', 
                                         bitmap=self.icons.iconsLib['change_xlabels_16']))
            menu.AppendSeparator()
            self.resize_plot_check =  menu.AppendCheckItem(ID_plotPanel_resize, "Resize on saving", help="")
            self.resize_plot_check.Check(self.config.resize)
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_save2DImage, text=saveImageLabel, 
                                         bitmap=self.icons.iconsLib['save16']))
            menu.AppendSeparator()
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_clearPlot_2D, text="Clear plot", 
                                         bitmap=self.icons.iconsLib['clear_16']))
        elif self.currentPage == "DT/MS":
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_processSettings_2D,
                                         text='Process heatmap...', 
                                         bitmap=self.icons.iconsLib['process_2d_16']))
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_plots_rotate90,
                                         text=u'Rotate 90°', 
                                         bitmap=self.icons.iconsLib['blank_16']))
            menu.AppendSeparator()
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_extraSettings_general_plot,
                                         text='Edit general parameters...', 
                                         bitmap=self.icons.iconsLib['panel_plot_general_16']))
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_extraSettings_plot2D,
                                         text='Edit plot parameters...', 
                                         bitmap=self.icons.iconsLib['panel_plot2D_16']))
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_extraSettings_colorbar,
                                         text='Edit colorbar parameters...', 
                                         bitmap=self.icons.iconsLib['panel_colorbar_16']))
            self.lock_plot_check =  menu.AppendCheckItem(ID_plotPanel_lockPlot, "Lock plot", help="")
            self.lock_plot_check.Check(self.plotMZDT.lock_plot_from_updating)
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_plots_customisePlot,
                                         text='Customise plot...', 
                                         bitmap=self.icons.iconsLib['change_xlabels_16']))
            menu.AppendSeparator()
            self.resize_plot_check =  menu.AppendCheckItem(ID_plotPanel_resize, "Resize on saving", help="")
            self.resize_plot_check.Check(self.config.resize)
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
            self.resize_plot_check =  menu.AppendCheckItem(ID_plotPanel_resize, "Resize on saving", help="")
            self.resize_plot_check.Check(self.config.resize)
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_save3DImage, text=saveImageLabel, 
                                         bitmap=self.icons.iconsLib['save16']))
            menu.AppendSeparator()
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_clearPlot_3D, text="Clear plot", 
                                         bitmap=self.icons.iconsLib['clear_16']))
        elif self.currentPage == "Overlay":
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_extraSettings_general_plot,
                                         text='Edit general parameters...', 
                                         bitmap=self.icons.iconsLib['panel_plot_general_16']))
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_extraSettings_plot2D,
                                         text='Edit plot parameters...', 
                                         bitmap=self.icons.iconsLib['panel_plot2D_16']))
            menu.AppendSeparator()
            self.lock_plot_check =  menu.AppendCheckItem(ID_plotPanel_lockPlot, "Lock plot", help="")
            self.lock_plot_check.Check(self.plotOverlay.lock_plot_from_updating)
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_plots_customisePlot,
                                         text='Customise plot...', 
                                         bitmap=self.icons.iconsLib['change_xlabels_16']))
            menu.AppendSeparator()
            self.resize_plot_check =  menu.AppendCheckItem(ID_plotPanel_resize, "Resize on saving", help="")
            self.resize_plot_check.Check(self.config.resize)
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveOverlayImage, text=saveImageLabel, 
                                         bitmap=self.icons.iconsLib['save16']))
            menu.AppendSeparator()
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_clearPlot_Overlay, text="Clear plot", 
                                         bitmap=self.icons.iconsLib['clear_16']))
        elif self.currentPage == "Waterfall":
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_extraSettings_general_plot,
                                         text='Edit general parameters...', 
                                         bitmap=self.icons.iconsLib['panel_plot_general_16']))
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_extraSettings_plot2D,
                                         text='Edit plot parameters...', 
                                         bitmap=self.icons.iconsLib['panel_plot2D_16']))
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_extraSettings_legend,
                                         text='Edit legend parameters...', 
                                         bitmap=self.icons.iconsLib['panel_legend_16']))
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_extraSettings_waterfall,
                                         text='Edit waterfall parameters...', 
                                         bitmap=self.icons.iconsLib['panel_waterfall_16']))
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_extraSettings_violin,
                                         text='Edit violin parameters...', 
                                         bitmap=self.icons.iconsLib['panel_violin_16']))
            self.lock_plot_check =  menu.AppendCheckItem(ID_plotPanel_lockPlot, "Lock plot", help="")
            self.lock_plot_check.Check(self.plotWaterfallIMS.lock_plot_from_updating)
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_plots_customisePlot,
                                         text='Customise plot...', 
                                         bitmap=self.icons.iconsLib['change_xlabels_16']))
            menu.AppendSeparator()
            self.resize_plot_check =  menu.AppendCheckItem(ID_plotPanel_resize, "Resize on saving", help="")
            self.resize_plot_check.Check(self.config.resize)
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveWaterfallImage, text=saveImageLabel, 
                                         bitmap=self.icons.iconsLib['save16']))
            menu.AppendSeparator()
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_clearPlot_Waterfall, text="Clear plot", 
                                         bitmap=self.icons.iconsLib['clear_16']))
        elif self.currentPage == "RMSF":
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_extraSettings_general_plot,
                                         text='Edit general parameters...', 
                                         bitmap=self.icons.iconsLib['panel_plot_general_16']))
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_extraSettings_rmsd,
                                         text='Edit plot parameters...', 
                                         bitmap=self.icons.iconsLib['panel_rmsd_16']))
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_plots_customisePlot,
                                         text='Customise plot...', 
                                         bitmap=self.icons.iconsLib['change_xlabels_16']))
            menu.AppendSeparator()
            self.resize_plot_check =  menu.AppendCheckItem(ID_plotPanel_resize, "Resize on saving", help="")
            self.resize_plot_check.Check(self.config.resize)
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveRMSFImage, text=saveImageLabel, 
                                         bitmap=self.icons.iconsLib['save16']))
            menu.AppendSeparator()
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_clearPlot_RMSF, text="Clear plot", 
                                         bitmap=self.icons.iconsLib['clear_16']))
        elif self.currentPage == "Comparison":
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_extraSettings_general_plot,
                                         text='Edit general parameters...', 
                                         bitmap=self.icons.iconsLib['panel_plot_general_16']))
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_plots_customisePlot,
                                         text='Customise plot...', 
                                         bitmap=self.icons.iconsLib['change_xlabels_16']))
            menu.AppendSeparator()
            self.resize_plot_check =  menu.AppendCheckItem(ID_plotPanel_resize, "Resize on saving", help="")
            self.resize_plot_check.Check(self.config.resize)
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveRMSDmatrixImage, text=saveImageLabel, 
                                         bitmap=self.icons.iconsLib['save16']))
            menu.AppendSeparator()
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_clearPlot_Matrix, text="Clear plot", 
                                         bitmap=self.icons.iconsLib['clear_16']))
        elif self.currentPage == "Calibration":
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_clearPlot_Calibration, text="Clear plot", 
                                         bitmap=self.icons.iconsLib['clear_16']))
        elif self.currentPage == "UniDec":

            menu.AppendItem(makeMenuItem(parent=menu, id=ID_extraSettings_general_plot,
                                         text='Edit general parameters...', 
                                         bitmap=self.icons.iconsLib['panel_plot_general_16']))
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
            evtID = None
            if self.parent.plot_name == "MS": evtID = ID_plots_customisePlot_unidec_ms
            elif self.parent.plot_name == "mwDistribution": evtID = ID_plots_customisePlot_unidec_mw
            elif self.parent.plot_name == "mzGrid": evtID = ID_plots_customisePlot_unidec_mz_v_charge
            elif self.parent.plot_name == "mwGrid": evtID = ID_plots_customisePlot_unidec_mw_v_charge
            elif self.parent.plot_name == "pickedPeaks": evtID = ID_plots_customisePlot_unidec_isolated_mz
            elif self.parent.plot_name == "Barchart": evtID = ID_plots_customisePlot_unidec_ms_barchart
            elif self.parent.plot_name == "ChargeDistribution": evtID = ID_plots_customisePlot_unidec_chargeDist
            if evtID is not None:
                menu.AppendItem(makeMenuItem(parent=menu, id=evtID,
                                             text='Customise plot...', 
                                             bitmap=self.icons.iconsLib['change_xlabels_16']))
            menu.AppendMenu(wx.ID_ANY, 'Customise plot...', customiseUniDecMenu)
            menu.AppendSeparator()
            self.resize_plot_check =  menu.AppendCheckItem(ID_plotPanel_resize, "Resize on saving", help="")
            self.resize_plot_check.Check(self.config.resize)
            evtID = None
            if self.parent.plot_name == "MS": evtID = ID_clearPlot_UniDec_MS
            elif self.parent.plot_name == "mwDistribution": evtID = ID_plots_saveImage_unidec_mw
            elif self.parent.plot_name == "mzGrid": evtID = ID_plots_saveImage_unidec_mz_v_charge
            elif self.parent.plot_name == "mwGrid": evtID = ID_plots_saveImage_unidec_mw_v_charge
            elif self.parent.plot_name == "pickedPeaks": evtID = ID_plots_saveImage_unidec_isolated_mz
            elif self.parent.plot_name == "Barchart": evtID = ID_plots_saveImage_unidec_ms_barchart
            elif self.parent.plot_name == "ChargeDistribution": evtID = ID_plots_saveImage_unidec_chargeDist
            if evtID is not None:
                menu.AppendItem(makeMenuItem(parent=menu, id=evtID, text=saveImageLabel, 
                                             bitmap=self.icons.iconsLib['save16']))
            menu.AppendMenu(wx.ID_ANY, 'Save figure...', saveUniDecMenu)
            menu.AppendSeparator()
            evtID = None
            if self.parent.plot_name == "MS": evtID = ID_clearPlot_UniDec_MS
            elif self.parent.plot_name == "mwDistribution": evtID = ID_clearPlot_UniDec_mwDistribution
            elif self.parent.plot_name == "mzGrid": evtID = ID_clearPlot_UniDec_mzGrid
            elif self.parent.plot_name == "mwGrid": evtID = ID_clearPlot_UniDec_mwGrid
            elif self.parent.plot_name == "pickedPeaks": evtID = ID_clearPlot_UniDec_pickedPeaks
            elif self.parent.plot_name == "Barchart": evtID = ID_clearPlot_UniDec_barchart
            elif self.parent.plot_name == "ChargeDistribution": evtID = ID_clearPlot_UniDec_chargeDistribution
            if evtID is not None:
                menu.AppendItem(makeMenuItem(parent=menu, id=evtID, text="Clear plot", 
                                             bitmap=self.icons.iconsLib['clear_16']))
            
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_clearPlot_UniDec_all, text="Clear all", 
                                         bitmap=self.icons.iconsLib['clear_16']))
        elif self.currentPage == "Other":
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_extraSettings_general_plot,
                                         text='Edit general parameters...', 
                                         bitmap=self.icons.iconsLib['panel_plot_general_16']))
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
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_extraSettings_waterfall,
                                         text='Edit waterfall parameters...', 
                                         bitmap=self.icons.iconsLib['panel_waterfall_16']))
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_extraSettings_violin,
                                         text='Edit violin parameters...', 
                                         bitmap=self.icons.iconsLib['panel_violin_16']))
            menu.AppendSeparator()
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_plots_customisePlot,
                                         text='Customise plot...', 
                                         bitmap=self.icons.iconsLib['change_xlabels_16']))
            menu.AppendSeparator()
            self.resize_plot_check =  menu.AppendCheckItem(ID_plotPanel_resize, "Resize on saving", help="")
            self.resize_plot_check.Check(self.config.resize)
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveOtherImage, text=saveImageLabel, 
                                         bitmap=self.icons.iconsLib['save16']))
            menu.AppendSeparator()
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_clearPlot_other, text="Clear plot", 
                                         bitmap=self.icons.iconsLib['clear_16']))
        else: 
            pass
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()
        
    def save_images(self, evt, path=None, **save_kwargs):
        """ Save figure depending on the event ID """
        args = ("Saving image. Please wait...", 4, 10)
        self.presenter.onThreading(evt, args, action='updateStatusbar')
        
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
            
        # Select default name + link to the plot
        elif evtID in [ID_saveCompareMSImage]:
            defaultName = self.config._plotSettings['MS (compare)']['default_name']
            resizeName ="MS (compare)"
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
            plotWindow = self.plotWaterfallIMS
            if plotWindow.plot_name == "Violin":
                defaultName = self.config._plotSettings['Violin']['default_name']
                resizeName = "Violin"
            else:
                defaultName = self.config._plotSettings['Waterfall']['default_name']
                resizeName = "Waterfall"
            
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

        elif evtID in [ID_saveOtherImageDoc, ID_saveOtherImage]:
            defaultName = "custom_plot"
            resizeName = None
            plotWindow = self.plotOther
            
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
            args = ("Operation was cancelled", 4)
        self.presenter.onThreading(evt, args, action='updateStatusbar')
         
    def onLockPlot(self, evt):
        if self.currentPage == "Waterfall": plot = self.plotWaterfallIMS
        elif self.currentPage == "MS": plot = self.plot1
        elif self.currentPage == "1D": plot = self.plot1D
        elif self.currentPage == "RT": plot = self.plotRT
        elif self.currentPage == "2D": plot = self.plot2D
        elif self.currentPage == "DT/MS": plot = self.plotMZDT
        elif self.currentPage == "Overlay": plot = self.plotOverlay
        
        plot.lock_plot_from_updating = not plot.lock_plot_from_updating
         
    def on_resize_check(self, evt):
        self.config.resize = not self.config.resize
         
    def customisePlot(self, evt):
        open_window, title = True, ""
        
        if self.currentPage == "Waterfall": plot, title = self.plotWaterfallIMS, "Waterfall..."
        elif self.currentPage == "MS": plot, title = self.plot1, "Mass spectrum..."
        elif self.currentPage == "1D": plot, title = self.plot1D, "Mobiligram..."
        elif self.currentPage == "RT": plot, title = self.plotRT, "Chromatogram ..."
        elif self.currentPage == "2D": plot, title = self.plot2D, "Heatmap..."
        elif self.currentPage == "DT/MS": plot, title = self.plotMZDT, "DT/MS..."
        elif self.currentPage == "Overlay": 
            plot, title = self.plotOverlay, "Overlay"
            if plot.plot_name not in ["Mask", "Transparent"]: open_window = False
        elif self.currentPage == "RMSF": 
            plot, title = self.plotRMSF, "RMSF"
            if plot.plot_name not in ["RMSD"]: open_window = False 
        elif self.currentPage == "Comparison": plot, title = self.plotCompare, "Comparison..."
        elif self.currentPage == "UniDec":
            evtID = evt.GetId()
            if evtID == ID_plots_customisePlot_unidec_ms: plot, title = self.plotUnidec_MS, "UniDec - Mass spectrum..."
            elif evtID == ID_plots_customisePlot_unidec_mw: plot, title = self.plotUnidec_mwDistribution, "UniDec - Molecular weight distribution..."
            elif evtID == ID_plots_customisePlot_unidec_mz_v_charge: plot, title = self.plotUnidec_mzGrid, "UniDec - Mass spectrum vs charge..."
            elif evtID == ID_plots_customisePlot_unidec_isolated_mz: plot, title = self.plotUnidec_individualPeaks, "UniDec - Mass spectrum with individual species..."
            elif evtID == ID_plots_customisePlot_unidec_mw_v_charge: plot, title = self.plotUnidec_mwVsZ, "UniDec - molecular weight vs charge..."
            elif evtID == ID_plots_customisePlot_unidec_ms_barchart: plot, title = self.plotUnidec_barChart, "UniDec - Barchart..."
            elif evtID == ID_plots_customisePlot_unidec_chargeDist: plot, title = self.plotUnidec_chargeDistribution, "UniDec - Charge state distribution..."
        elif self.currentPage == "Other":
            plot, title = self.plotOther, "Custom data..."
            
        if not open_window:
            args = ("Cannot customise parameters for this plot. Try replotting instead", 4) 
            self.presenter.onThreading(None, args, action='updateStatusbar')
            return
        
        if not hasattr(plot, "plotMS"):
            args = ("Cannot customise plot parameters, either because it does nto exist or is not supported yet.", 4) 
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


        try:
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
                      'plot':plot,
                      'window_title':title} 
        except AttributeError: 
            args = ("Cannot customise plot parameters if the plot does not exist", 4) 
            self.presenter.onThreading(None, args, action='updateStatusbar')
            return
        
        dlg = panelCustomisePlot(self, self.presenter, self.config, **kwargs)
        dlg.ShowModal()
         
    def on_rotate_plot(self, evt):
        plot = self.get_current_plot()
         
        plot.on_rotate_90()
        plot.repaint()
         
    def get_current_plot(self):
        if self.currentPage == "Waterfall": plot = self.plotWaterfallIMS
        elif self.currentPage == "MS": plot = self.plot1
        elif self.currentPage == "1D": plot = self.plot1D
        elif self.currentPage == "RT": plot = self.plotRT
        elif self.currentPage == "2D": plot = self.plot2D
        elif self.currentPage == "DT/MS": plot = self.plotMZDT
        elif self.currentPage == "Overlay": plot = self.plotOverlay
        elif self.currentPage == "RMSF": plot = self.plotRMSF
        elif self.currentPage == "Comparison": plot = self.plotCompare
        elif self.currentPage == "Other": plot = self.plotOther
        
        return plot
         
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
        self.parent.panelMultipleIons.peaklist.Append([round(xmin, 2),
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
                  
    def onChangePalette(self, evt, cmap=None, n_colors=16, return_colors=False, return_hex=False):
        if cmap is not None:
            palette_name = cmap
        else:
            if self.config.currentPalette in ['Spectral', 'RdPu']:
                palette_name = self.config.currentPalette
            else:
                palette_name = self.config.currentPalette.lower()
                
        new_colors = sns.color_palette(palette_name, n_colors)
        
        if not return_colors:
            for i in xrange(n_colors):
                self.config.customColors[i] = convertRGB1to255(new_colors[i])
        else:
            if return_hex:
                new_colors_hex = []
                for new_color in new_colors:
                    new_colors_hex.append(convertRGB1toHEX(new_color))
                return new_colors_hex
            else:
                return new_colors
                 
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

    def onClearPlot(self, evt, plot=None):
        """
        Clear selected plot
        """
        
        eventID = evt.GetId()
            
        if plot == 'MS' or eventID == ID_clearPlot_MS:
            plot = self.plot1
        elif plot =='RT' or eventID == ID_clearPlot_RT:
            plot =  self.plotRT
        elif plot =='RT_MS' or eventID == ID_clearPlot_RT_MS:
            plot =  self.plotRT_MS
        elif plot == '1D' or eventID == ID_clearPlot_1D:
            plot = self.plot1D
        elif plot =='1D_MS' or eventID == ID_clearPlot_1D_MS:
            plot =  self.plot1D_MS
        elif plot == '2D' or eventID == ID_clearPlot_2D:
            plot = self.plot2D
        elif plot == 'DT/MS' or eventID == ID_clearPlot_MZDT:
            plot = self.plotMZDT
        elif plot == '3D' or eventID == ID_clearPlot_3D:
            plot = self.plot3D
        elif plot == 'RMSF' or eventID == ID_clearPlot_RMSF:
            plot = self.plotRMSF
        elif plot == 'Overlay' or eventID == ID_clearPlot_Overlay:
            plot = self.plotOverlay
        elif plot == 'Matrix' or eventID == ID_clearPlot_Matrix:
            plot = self.plotCompare
        elif plot == 'Waterall' or eventID == ID_clearPlot_Waterfall:
            plot = self.plotWaterfallIMS
        elif plot == 'Calibration' or eventID == ID_clearPlot_Calibration:
            plot = [self.topPlotMS, self.bottomPlot1DT]
        elif plot == 'Other' or eventID == ID_clearPlot_other:
            plot = self.plotOther
        elif plot == 'UniDec' or eventID == ID_clearPlot_UniDec_MS:
            plot = self.plotUnidec_MS
        elif plot == 'UniDec' or eventID == ID_clearPlot_UniDec_mwDistribution:
            plot = self.plotUnidec_mwDistribution
        elif plot == 'UniDec' or eventID == ID_clearPlot_UniDec_mzGrid:
            plot = self.plotUnidec_mzGrid
        elif plot == 'UniDec' or eventID == ID_clearPlot_UniDec_mwGrid:
            plot = self.plotUnidec_mwVsZ
        elif plot == 'UniDec' or eventID == ID_clearPlot_UniDec_pickedPeaks:
            plot = self.plotUnidec_individualPeaks
        elif plot == 'UniDec' or eventID == ID_clearPlot_UniDec_barchart:
            plot = self.plotUnidec_barChart
        elif plot == 'UniDec' or eventID == ID_clearPlot_UniDec_chargeDistribution:
            plot = self.plotUnidec_chargeDistribution
            

        try:
            plot.clearPlot()
        except: 
            for p in plot: 
                p.clearPlot()    
        
        self.presenter.onThreading(evt, ("Cleared plot area", 4), action='updateStatusbar')

    def on_clear_all_plots(self):
        
        # Delete all plots
        plotList = [self.plot1, self.plotRT, self.plotRMSF,self.plot1D,
                    self.plotCompare, self.plot2D, self.plot3D, self.plotOverlay,
                    self.plotWaterfallIMS, self.topPlotMS, self.bottomPlot1DT, self.plotMZDT,
                    self.plotUnidec_MS, self.plotUnidec_mzGrid,
                    self.plotUnidec_mwDistribution, self.plotUnidec_mwVsZ, 
                    self.plotUnidec_individualPeaks, self.plotUnidec_barChart,
                    self.plotUnidec_chargeDistribution, self.plotOther]
        
        for plot in plotList:
            plot.clearPlot()
            plot.repaint()
        # Message
        args = ("Cleared all plots", 4)
        self.presenter.onThreading(None, args, action='updateStatusbar')

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

    def on_clear_patches(self, plot="MS", repaint=False):
        
        if plot == 'MS': 
            self.plot1.plot_remove_patches()
            if not repaint: return 
            else: self.plot1.repaint()
            
        elif plot == 'CalibrationMS':
            self.topPlotMS.plot_remove_patches()
            if not repaint: return 
            else: self.topPlotMS.repaint()
            
        elif plot == 'RT':
            self.plotRT.plot_remove_patches()
            if not repaint: return 
            else: self.plotRT.repaint()

    def on_plot_patches(self, xmin, ymin, width, height, color='r', alpha=0.5, 
                        plot='MS', repaint=False):
        if plot == 'MS': 
            self.plot1.plot_add_patch(xmin, ymin, width,
                                      height, color=color,
                                      alpha=alpha)
            if not repaint: return 
            else: self.plot1.repaint()
                
        elif plot == 'CalibrationMS':
            self.topPlotMS.plot_add_patch(xmin, ymin, width,
                                          height, color=color,
                                          alpha=alpha)
            if not repaint: return 
            else: self.topPlotMS.repaint()
            
    def on_clear_labels(self, plot="MS"):
        if plot == 'MS': 
            self.plot1.plot_remove_text_and_lines()
        elif plot == 'CalibrationMS':
            self.topPlotMS.plot_remove_text_and_lines()
            
    def on_plot_labels(self, xpos, yval, label='', plot='MS', repaint=False, 
                       optimise_labels=False, **kwargs):
                
        plt_kwargs = {"horizontalalignment": kwargs.pop("horizontal_alignment", "center"),
                      "verticalalignment": kwargs.pop("vertical_alignment", "center") ,
                      "check_yscale":kwargs.pop("check_yscale", False),
                      "butterfly_plot":kwargs.pop("butterfly_plot", False),
                      "fontweight": kwargs.pop("font_weight", "normal"),
                      "fontsize": kwargs.pop("font_size", "medium"),}
        
        if plot == 'MS': 
            self.plot1.plot_add_text(xpos=xpos, yval=yval, label=label, 
                                     yoffset=kwargs.get("yoffset", 0.0),
                                     **plt_kwargs)
            if not repaint: 
                return 
            else: 
                if optimise_labels: self.plot1._fix_label_positions()
                self.plot1.repaint()
                
        elif plot == 'CalibrationMS':
            self.topPlotMS.plot_add_text(xpos=xpos, yval=yval, label=label, **plt_kwargs)
            if not repaint: return 
            else: 
                if optimise_labels: self.topPlotMS._fix_label_positions()
                self.topPlotMS.repaint()

    def on_plot_markers(self, xvals=None, yvals=None, color='b', marker='o', 
                        size=5, plot='MS', repaint=True, **kwargs):
        if plot == 'MS':
            self.plot1.plot_add_markers(xvals=xvals, 
                                        yvals=yvals, 
                                        color=color,
                                        marker=marker, 
                                        size=size,
                                        test_yvals=True)
            if not repaint: 
                return 
            else: self.plot1.repaint()
            
        elif plot == 'RT':
            self.plotRT.plot_add_markers(xvals=xvals, 
                                         yvals=yvals,
                                         color=color,
                                         marker=marker,
                                         size=size)
            self.plotRT.repaint()
        elif plot == 'CalibrationMS':
            self.topPlotMS.plot_add_markers(xval=xvals, 
                                            yval=yvals,
                                            color=color,
                                            marker=marker,
                                            size=size)
            self.topPlotMS.repaint()
        elif plot == 'CalibrationDT':
            self.bottomPlot1DT.plot_add_markers(xvals=xvals,
                                                yvals=yvals,
                                                color=color,
                                                marker=marker,
                                                size=size,
                                                testMax='yvals')
            self.bottomPlot1DT.repaint()
            
    def on_clear_markers(self, plot="MS", repaint=False):
        
        if plot == 'RT':
            plot_obj = self.plotRT
        elif plot == 'MS':
            plot_obj = self.plot1
            
        
        plot_obj.plot_remove_markers()
        if not repaint: return 
        else: plot_obj.repaint()
            
        

    def _get_color_list(self, colorList, count=None, **kwargs):
        """
        colorList : list
           list of colors to replace 
        kwargs : dict
            dictionary with appropriate keys (color_scheme, colormap)
        """
        if colorList is None:
            n_count = count
        else:
            n_count = len(colorList)
        
#         print(kwargs['color_scheme'], n_count, kwargs['colormap'], kwargs['palette'])
        if kwargs['color_scheme'] == "Colormap":
            colorlist = sns.color_palette(kwargs['colormap'], n_count)
        elif kwargs['color_scheme'] == "Color palette":
            if kwargs['palette'] not in ['Spectral', 'RdPu']:
                kwargs['palette'] = kwargs['palette'].lower()
            colorlist = sns.color_palette(kwargs['palette'], n_count)
        elif kwargs["color_scheme"] == "Same color":
            colorlist = [kwargs["line_color"]] * n_count
        elif kwargs['color_scheme'] == "Random":
            colorlist = []
            for __ in range(n_count): 
                colorlist.append(randomColorGenerator())
                
                
        return colorlist

    def on_plot_charge_states(self, position, charges, **kwargs):
        
        self.plotUnidec_individualPeaks.plot_remove_text_and_lines()
        for position, charge in zip(position, charges):
            self.plotUnidec_individualPeaks.plot_add_text_and_lines(xpos=position, 
                                                                    yval=0.9, label=charge,
                                                                    stick_to_intensity=True)
            
        self.plotUnidec_individualPeaks.repaint() 
        
        if kwargs.get('optimise_positions', True):
            self.plotUnidec_individualPeaks._fix_label_positions()
        
        self.plotUnidec_individualPeaks.repaint() 
    
    def on_plot_unidec_ChargeDistribution(self, xvals=None, yvals=None, replot=None, xlimits=None, **kwargs):
        """
        Plot simple Mass spectrum before it is pre-processed
        @param unidec_eng_data (object):  reference to unidec engine data structure
        @param xlimits: unused
        """
        
        if self.config.unidec_plot_panel_view == "Tabbed view" and kwargs.get("set_page", False):
            try: self.unidec_notebook.SetSelection(6)
            except: pass    
        
        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType='1D')
        
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
        
        if self.config.unidec_plot_panel_view == "Tabbed view" and kwargs.get("set_page", False):
            try: self.unidec_notebook.SetSelection(0)
            except: pass
            
        plt_kwargs = self._buildPlotParameters(plotType='1D')
        
        if unidec_eng_data is None and replot is not None:
            xvals = replot['xvals']
            yvals = replot['yvals']
            
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
        
        if self.config.unidec_plot_panel_view == "Tabbed view" and kwargs.get("set_page", False):
            try: self.unidec_notebook.SetSelection(0)
            except: pass
        
        # Build kwargs
        plt1d_kwargs = self._buildPlotParameters(plotType='1D')
        unidec_kwargs = self._buildPlotParameters(plotType='UniDec')
        plt_kwargs = merge_two_dicts(plt1d_kwargs, unidec_kwargs)
        
        if unidec_eng_data is None and replot is not None:
            xvals = replot['xvals']
            yvals = replot['yvals']
            colors = replot['colors']
            labels = replot['labels']
        
        colors[1] = plt_kwargs['fit_line_color']
        
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
        
        if self.config.unidec_plot_panel_view == "Tabbed view" and kwargs.get("set_page", False):
            try: self.unidec_notebook.SetSelection(1)
            except: pass
        
        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType='2D')
        plt_kwargs['contour_levels'] = self.config.unidec_plot_contour_levels
        plt_kwargs['colorbar'] = True
        
        if unidec_eng_data is None and replot is not None:
            grid = replot['grid']
        
        self.plotUnidec_mzGrid.clearPlot()
        self.plotUnidec_mzGrid.plot_2D_contour_unidec(data=grid, 
                                                      xlabel="m/z (Da)", 
                                                      ylabel="Charge",
                                                      axesSize=self.config._plotSettings['UniDec (m/z vs Charge)']['axes_size'],
                                                      plotType='2D', plotName="mzGrid",
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
        
        if self.config.unidec_plot_panel_view == "Tabbed view" and kwargs.get("set_page", False):
            try: self.unidec_notebook.SetSelection(3)
            except: pass
        
        # Build kwargs
        plt1d_kwargs = self._buildPlotParameters(plotType='1D')
        unidec_kwargs = self._buildPlotParameters(plotType='UniDec')
        plt_kwargs = merge_two_dicts(plt1d_kwargs, unidec_kwargs)
        
        if unidec_eng_data is None and replot is not None:
            xvals = replot['xvals']
            yvals = replot['yvals']

        
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

    def on_plot_unidec_MW_add_markers(self, data, mw_data, **kwargs):
        # remove all markers
        self.plotUnidec_mwDistribution.plot_remove_markers()
        
        plt1d_kwargs = self._buildPlotParameters(plotType='1D')
        unidec_kwargs = self._buildPlotParameters(plotType='UniDec')
        plt_kwargs = merge_two_dicts(plt1d_kwargs, unidec_kwargs)
        
        
        legend_text = data['legend_text']
        mw = np.transpose([mw_data['xvals'], mw_data['yvals']])
        
        num = 0
        for key in natsorted(data.keys()):
            if key.split(" ")[0] != "MW:": 
                continue
            if num >= plt_kwargs["maximum_shown_items"]: 
                continue
            num += 1
            
        colors = self._get_color_list(None, count=num, **unidec_kwargs)
        
        num = 0
        for key in natsorted(data.keys()):
            if key.split(" ")[0] != "MW:": continue
             
            if num >= plt_kwargs["maximum_shown_items"]: continue
             
            xval = float(key.split(" ")[1])
            yval = self.data_processing.get_peak_maximum(mw, xval=xval)
            marker = data[key]['marker']
            color = colors[num] 
            
            self.plotUnidec_mwDistribution.plot_add_markers(xval, yval, 
                                                            color=color, marker=marker, 
                                                            size=plt_kwargs['MW_marker_size'],
                                                            label=key, 
                                                            test_xvals=True)
            num += 1
            
        self.plotUnidec_mwDistribution.plot_1D_add_legend(legend_text, **plt_kwargs)
        self.plotUnidec_mwDistribution.repaint()
    
    def on_plot_unidec_individualPeaks(self, unidec_eng_data=None, replot=None, xlimits=None, **kwargs):
        """
        Plot simple Mass spectrum before it is pre-processed
        @param unidec_eng_data (object):  reference to unidec engine data structure
        @param xlimits: unused
        """
        
        if self.config.unidec_plot_panel_view == "Tabbed view" and kwargs.get("set_page", False):
            try: self.unidec_notebook.SetSelection(4)
            except: pass        

        # Build kwargs
        plt1d_kwargs = self._buildPlotParameters(plotType='1D')
        unidec_kwargs = self._buildPlotParameters(plotType='UniDec')
        plt_kwargs = merge_two_dicts(plt1d_kwargs, unidec_kwargs)
        
        if unidec_eng_data is None and replot is not None:
            xvals = replot['xvals']
            yvals = replot['yvals']
            legend_text = replot['legend_text']
            
        # Plot MS
        self.plotUnidec_individualPeaks.clearPlot()
        self.plotUnidec_individualPeaks.plot_1D(xvals=xvals, yvals=yvals, 
                                                xlimits=xlimits, xlabel="m/z", 
                                                ylabel="Intensity",
                                                axesSize=self.config._plotSettings['UniDec (Isolated MS)']['axes_size'],
                                                plotType='pickedPeaks', label="Raw",
                                                allowWheel=False,
                                                **plt_kwargs)
        
        if kwargs.get('show_isolated_mw', False):
            legend_text = [[[0,0,0], "Raw"]]
            
        num = 0
        for key in natsorted(replot.keys()):
            if key.split(" ")[0] != "MW:": continue
            if num >= plt_kwargs["maximum_shown_items"]: continue
            num += 1
            
        colors = self._get_color_list(None, count=num, **unidec_kwargs)
            
        num = 0
        for key in natsorted(replot.keys()):
            if key.split(" ")[0] != "MW:": continue
            if num >= plt_kwargs["maximum_shown_items"]:
                continue
            
            scatter_yvals = replot[key]['scatter_yvals']
            line_yvals = replot[key]['line_yvals']
            
            if kwargs.get('show_isolated_mw', False):
                if key != kwargs['mw_selection']: 
                    continue
                else:
                    legend_text.append([colors[num], #replot[key]['color'], 
                                        replot[key]['label']])
                    # adjust offset so its closer to the MS plot
                    offset = np.min(replot[key]['line_yvals']) + self.config.unidec_charges_offset
                    line_yvals = line_yvals - offset
            else:
                legend_text[num+1][0] = colors[num]
            
            if kwargs['show_markers']:
                self.plotUnidec_individualPeaks.plot_add_markers(replot[key]['scatter_xvals'], 
                                                                 scatter_yvals, 
                                                                 color=colors[num], # replot[key]['color'], 
                                                                 marker=replot[key]['marker'], 
                                                                 size=plt_kwargs['isolated_marker_size'],
                                                                 label=replot[key]['label'])
            if kwargs['show_individual_lines']:
                self.plotUnidec_individualPeaks.plot_1D_add(replot[key]['line_xvals'], 
                                                            line_yvals, 
                                                            color=colors[num], #replot[key]['color'], 
                                                            label=replot[key]['label'],
                                                            allowWheel=False,
                                                            plot_name="pickedPeaks",
                                                            **plt_kwargs)
                
            num += 1
            
        if len(legend_text)-1 > plt_kwargs["maximum_shown_items"]:
            msg = "Only showing {} out of {} items. If you would like to see more go to Processing -> UniDec -> Max shown".format(plt_kwargs["maximum_shown_items"], len(legend_text)-1)
            self.presenter.onThreading(None, (msg, 4, 7), action='updateStatusbar')
            
        # Add legend
        if len(legend_text) >= plt_kwargs["maximum_shown_items"]:
            legend_text = legend_text[:plt_kwargs["maximum_shown_items"]]
            
        self.plotUnidec_individualPeaks.plot_1D_add_legend(legend_text, **plt_kwargs)
        self.plotUnidec_individualPeaks.repaint()
        
    def on_plot_unidec_MW_v_Charge(self, unidec_eng_data=None, replot=None, **kwargs):
        """
        Plot simple Mass spectrum before it is pre-processed
        @param unidec_eng_data (object):  reference to unidec engine data structure
        """
        
        if self.config.unidec_plot_panel_view == "Tabbed view" and kwargs.get("set_page", False):
            try: self.unidec_notebook.SetSelection(2)
            except: pass    
        
        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType='2D')
        plt_kwargs['contour_levels'] = self.config.unidec_plot_contour_levels
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
                                                     plotType='MS', plotName="mwGrid", testX=True,
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
        
        if self.config.unidec_plot_panel_view == "Tabbed view" and kwargs.get("set_page", False):
            try: self.unidec_notebook.SetSelection(5)
            except: pass    
            
        # Build kwargs
        plt1d_kwargs = self._buildPlotParameters(plotType='1D')
        unidec_kwargs = self._buildPlotParameters(plotType='UniDec')
        plt_kwargs = merge_two_dicts(plt1d_kwargs, unidec_kwargs)
            
        if unidec_eng_data is None and replot is not None:
            xvals = replot['xvals']
            yvals = replot['yvals']
            labels = replot['labels']
            colors = replot['colors']
            legend_text = replot['legend_text']
            markers = replot['markers']
            
            if len(xvals) > plt_kwargs["maximum_shown_items"]:
                msg = "Only showing {} out of {} items. If you would like to see more go to Processing -> UniDec -> Max shown".format(plt_kwargs["maximum_shown_items"], 
                                                                                                                                      len(xvals))
                self.presenter.onThreading(None, (msg, 4, 7), action='updateStatusbar')
            
            if len(xvals) >= plt_kwargs["maximum_shown_items"]:
                xvals = xvals[:plt_kwargs["maximum_shown_items"]]
                yvals = yvals[:plt_kwargs["maximum_shown_items"]]
                labels = labels[:plt_kwargs["maximum_shown_items"]]
                colors = colors[:plt_kwargs["maximum_shown_items"]]
                legend_text = legend_text[:plt_kwargs["maximum_shown_items"]]
                markers = markers[:plt_kwargs["maximum_shown_items"]]
        
        colors = self._get_color_list(colors, **unidec_kwargs)
        for i in xrange(len(legend_text)):
            legend_text[i][0] = colors[i]
        
        self.plotUnidec_barChart.clearPlot()
        self.plotUnidec_barChart.plot_1D_barplot(xvals, yvals, labels, colors,
                                                 axesSize=self.config._plotSettings['UniDec (Barplot)']['axes_size'],
                                                 title="Peak Intensities",
                                                 ylabel="Intensity",
                                                 plotType="Barchart",
                                                 **plt_kwargs)
            
        if unidec_eng_data is None and replot is not None:
            if kwargs['show_markers']:
                for i in xrange(len(markers)):
                    if i >= plt_kwargs["maximum_shown_items"]:
                        continue
                    self.plotUnidec_barChart.plot_add_markers(xvals[i], yvals[i], 
                                                              color=colors[i], 
                                                              marker=markers[i], 
                                                              size=plt_kwargs['bar_marker_size'])

        
        # Add legend
        self.plotUnidec_barChart.plot_1D_add_legend(legend_text, **plt_kwargs)
        self.plotUnidec_barChart.repaint()
        
    def plot_1D_update(self, plotName='all', evt=None):
        
        plt_kwargs = self._buildPlotParameters(plotType='1D')
        
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
            plt_kwargs = self._buildPlotParameters(plotType='2D')
            rmsd_kwargs = self._buildPlotParameters(plotType='RMSF')
            plt_kwargs = merge_two_dicts(plt_kwargs, rmsd_kwargs)
            try:
                self.plotRMSF.plot_1D_update_rmsf(**plt_kwargs)
                self.plotRMSF.repaint()
            except AttributeError: pass
        
    def on_plot_other_1D(self, msX=None, msY=None, xlabel="", ylabel="", 
                         xlimits=None, set_page=False, **kwargs):
        
        if set_page: self.mainBook.SetSelection(self.config.panelNames['Other'])
        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType='1D')
        plt_kwargs = merge_two_dicts(plt_kwargs, kwargs)
        # check limits
        try:
            if math.isnan(xlimits.get(0, msX[0])): xlimits[0] = msX[0]
            if math.isnan(xlimits.get(1, msX[-1])): xlimits[1] = msX[-1]
        except:
            xlimits = [np.min(msX), np.max(msX)]
                
        try:
            if len(msX[0]) > 1:
                msX = msX[0]
                msY = msY[0]
        except TypeError: pass
            
                
        self.plotOther.clearPlot()
        self.plotOther.plot_1D(xvals=msX, 
                               yvals=msY, 
                               xlimits=xlimits,
                               xlabel=xlabel, ylabel=ylabel,
                               axesSize=self.config._plotSettings['Other (Line)']['axes_size'],
                               plotType='MS',
                               **plt_kwargs)
        self.plotOther.repaint()
        self.plotOther.plot_type = "line"
        
    def on_plot_other_overlay(self, xvals, yvals, xlabel, ylabel, colors, labels, 
                              xlimits=None, set_page=False, **kwargs):
        
        if set_page: self.mainBook.SetSelection(self.config.panelNames['Other'])
        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType='1D')
        plt_kwargs = merge_two_dicts(plt_kwargs, kwargs)

        self.plotOther.clearPlot()
        self.plotOther.plot_1D_overlay(xvals=xvals, 
                                       yvals=yvals, 
                                       title="", 
                                       xlabel=xlabel,
                                       ylabel=ylabel, 
                                       labels=labels,
                                       colors=colors, 
                                       xlimits=xlimits,
                                       zoom='box',
                                       axesSize=self.config._plotSettings['Other (Multi-line)']['axes_size'],
                                       plotName='1D',
                                       **plt_kwargs)
        self.plotOther.repaint()
        self.plotOther.plot_type = "multi-line"
        
    def on_plot_other_waterfall(self, xvals, yvals, zvals, xlabel,  ylabel, colors=[], 
                                set_page=False, **kwargs):

        if set_page: self.mainBook.SetSelection(self.config.panelNames['Other'])
        
        plt_kwargs = self._buildPlotParameters(plotType='1D')
        waterfall_kwargs = self._buildPlotParameters(plotType='waterfall')
        plt_kwargs = merge_two_dicts(plt_kwargs, waterfall_kwargs)
        if 'increment' in kwargs:
            plt_kwargs['increment'] = kwargs['increment']
        
        # reverse labels 
        xlabel, ylabel = ylabel, xlabel
        
        self.plotOther.clearPlot()
        self.plotOther.plot_1D_waterfall(xvals=xvals, yvals=yvals,
                                         zvals=zvals, label="", 
                                         xlabel=xlabel, 
                                         ylabel=ylabel,
                                         colorList=colors,
                                         labels=kwargs.get('labels',[]),
                                         axesSize=self.config._plotSettings['Other (Waterfall)']['axes_size'],
                                         plotName='1D',
                                         **plt_kwargs)
        
#         if ('add_legend' in kwargs and 'labels' in kwargs and
#             len(colors) == len(kwargs['labels'])):
#             if kwargs['add_legend']:
#                 legend_text = zip(colors, kwargs['labels'])
#                 self.plotOther.plot_1D_add_legend(legend_text, **plt_kwargs)
        
        self.plotOther.repaint() 
        self.plotOther.plot_type = "waterfall"
        
    def on_plot_other_scatter(self, xvals, yvals, zvals, xlabel, ylabel, colors, labels,
                              xlimits=None, set_page=False, **kwargs):
        
        if set_page: self.mainBook.SetSelection(self.config.panelNames['Other'])
        
        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType='1D')
        plt_kwargs = merge_two_dicts(plt_kwargs, kwargs)

        self.plotOther.clearPlot()
        self.plotOther.plot_1D_scatter(xvals=xvals, 
                                       yvals=yvals, 
                                       zvals=zvals,
                                       title="", 
                                       xlabel=xlabel,
                                       ylabel=ylabel, 
                                       labels=labels,
                                       colors=colors, 
                                       xlimits=xlimits,
                                       zoom='box',
                                       axesSize=self.config._plotSettings['Other (Scatter)']['axes_size'],
                                       plotName='1D',
                                       **plt_kwargs)
        self.plotOther.repaint()
        self.plotOther.plot_type = "scatter"
        
    def on_plot_other_grid_1D(self, xvals, yvals, xlabel, ylabel, colors, labels, 
                             set_page=False, **kwargs):
        
        if set_page: self.mainBook.SetSelection(self.config.panelNames['Other'])
        
        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType='1D')
        plt_kwargs = merge_two_dicts(plt_kwargs, kwargs)

        self.plotOther.clearPlot()
        self.plotOther.plot_n_grid_1D_overlay(xvals=xvals, 
                                              yvals=yvals, 
                                              title="", 
                                              xlabel=xlabel,
                                              ylabel=ylabel, 
                                              labels=labels,
                                              colors=colors, 
                                              zoom='box',
                                              axesSize=self.config._plotSettings['Other (Grid-1D)']['axes_size'],
                                              plotName='1D',
                                              **plt_kwargs)
        self.plotOther.repaint()
        self.plotOther.plot_type = "grid-line"

    def on_plot_other_grid_scatter(self, xvals, yvals, xlabel, ylabel, colors, labels,
                                   set_page=False, **kwargs):
        
        if set_page: self.mainBook.SetSelection(self.config.panelNames['Other'])
        
        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType='1D')
        plt_kwargs = merge_two_dicts(plt_kwargs, kwargs)

        self.plotOther.clearPlot()
        self.plotOther.plot_n_grid_scatter(xvals=xvals, 
                                           yvals=yvals, 
                                           title="", 
                                           xlabel=xlabel,
                                           ylabel=ylabel, 
                                           labels=labels,
                                           colors=colors, 
                                           zoom='box',
                                           axesSize=self.config._plotSettings['Other (Grid-1D)']['axes_size'],
                                           plotName='1D',
                                           **plt_kwargs)
        self.plotOther.repaint()
        self.plotOther.plot_type = "grid-scatter"
        
    def on_plot_other_bars(self, xvals, yvals_min, yvals_max, xlabel, ylabel, colors,
                           set_page=False, **kwargs):
        
        if set_page: self.mainBook.SetSelection(self.config.panelNames['Other'])
        
        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType='1D')
        plt_kwargs = merge_two_dicts(plt_kwargs, kwargs)

        self.plotOther.clearPlot()
        self.plotOther.plot_floating_barplot(xvals=xvals, 
                                             yvals_min=yvals_min, 
                                             yvals_max=yvals_max, 
                                             itle="", 
                                             xlabel=xlabel,
                                             ylabel=ylabel, 
                                             colors=colors, 
                                             zoom='box',
                                             axesSize=self.config._plotSettings['Other (Barplot)']['axes_size'],
                                             **plt_kwargs)
        self.plotOther.repaint()
        self.plotOther.plot_type = "bars"
        
    def _on_check_plot_names(self, document_name, dataset_name, plot_window):
        """
        Check if document name and dataset name match that of the plotted window
        """
        plot = None
        if plot_window == "MS":
            plot = self.plot1
            
        if plot is None: return False
        
        
        if plot.document_name is None or plot.dataset_name is None: return
        
        if plot.document_name != document_name: 
            return False
        
        if plot.dataset_name != dataset_name: 
            return False
        
        return True
         
    def on_add_centroid_MS_and_labels(self, msX, msY, labels, full_labels, xlimits=None, 
                                      title="", butterfly_plot=False, set_page=False, **kwargs):
        if set_page: self.mainBook.SetSelection(self.config.panelNames['MS'])
        
        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType='1D')
        plt_kwargs['line_color'] = self.config.msms_line_color_labelled
        plt_kwargs['butterfly_plot'] = butterfly_plot
        
        plot_name="MS"
        plot_size = self.config._plotSettings['MS']['axes_size']
        if butterfly_plot:
            plot_name="compareMS"
            plot_size = self.config._plotSettings['MS (compare)']['axes_size']
        
        xylimits = self.plot1.get_xylimits()
        self.plot1.plot_1D_centroid(xvals=msX, 
                                    yvals=msY, 
                                    xlimits=xlimits,
                                    update_y_axis=False,
                                    xlabel="m/z", ylabel="Intensity", title=title,
                                    axesSize=plot_size,
                                    plot_name=plot_name,
                                    adding_on_top=True,
                                    **plt_kwargs)
        
        # add labels
        plt_label_kwargs = {"horizontalalignment": self.config.annotation_label_horz,
                            "verticalalignment": self.config.annotation_label_vert,
                            "check_yscale":True,
                            "add_arrow_to_low_intensity":self.config.msms_add_arrows,
                            "butterfly_plot":butterfly_plot,
                            "fontweight": self.config.annotation_label_font_weight,
                            "fontsize": self.config.annotation_label_font_size,
                            'rotation':self.config.annotation_label_font_orientation}
     
        for i in xrange(len(labels)):
            xval, yval, label, full_label = msX[i], msY[i], labels[i], full_labels[i]
            
            if not self.config.msms_show_neutral_loss:
                if "H2O" in full_label or "NH3" in full_label:
                    continue
                
            if self.config.msms_show_full_label:
                label = full_label
                
            self.plot1.plot_add_text(xpos=xval, yval=yval, label=label, 
                                     yoffset=self.config.msms_label_y_offset,
                                     **plt_label_kwargs) 
            
        if i == len(labels)-1 and not butterfly_plot:
            self.plot1.set_xylimits(xylimits)
            
        self.plot1.repaint()
        
    def on_plot_centroid_MS(self, msX, msY, msXY=None, xlimits=None, title="", repaint=True, 
                            set_page=False, **kwargs):
        if set_page: self.mainBook.SetSelection(self.config.panelNames['MS'])
        
        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType='1D')
        plt_kwargs['line_color'] = self.config.msms_line_color_unlabelled 
        
        self.plot1.clearPlot() 
        self.plot1.plot_1D_centroid(xvals=msX, 
                                    yvals=msY, 
                                    xyvals=msXY,
                                    xlimits=xlimits,
                                    xlabel="m/z", ylabel="Intensity", title=title,
                                    axesSize=self.config._plotSettings['MS']['axes_size'],
                                    plotType='MS',
                                    **plt_kwargs)
        # Show the mass spectrum
        if repaint:
            self.plot1.repaint()
        
    def on_clear_MS_annotations(self):
        
        try: self.on_clear_labels(plot="MS")
        except: pass
        try: self.on_clear_patches(plot="MS")
        except: pass
        
    def on_plot_MS(self, msX=None, msY=None, xlimits=None, override=True, replot=False,
                   full_repaint=False, set_page=False, show_in_window="MS", view_range=[], **kwargs):
        
        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType='1D')
        
        panel = self.plot1
        window = self.config.panelNames['MS']
        if show_in_window == "MS":
            panel = self.plot1
            window = self.config.panelNames['MS']
            plot_size_key = 'MS'
        elif show_in_window == "RT":
            panel = self.plotRT_MS
            window = self.config.panelNames['RT']
            plt_kwargs["prevent_extraction"] = True
            plot_size_key = 'MS (DT/RT)'
        elif show_in_window == '1D':
            panel = self.plot1D_MS
            window = self.config.panelNames['1D']
            plt_kwargs["prevent_extraction"] = True
            plot_size_key = 'MS (DT/RT)'
            
        # change page
        if set_page: self.mainBook.SetSelection(window)
        
        if replot:
            msX, msY, xlimits = self.presenter._get_replot_data('MS')
            if msX is None or msY is None:
                return
        
        # setup names
        if "document" in kwargs:
            panel.document_name = kwargs['document']
            panel.dataset_name = kwargs['dataset']
        else:
            panel.document_name = None
            panel.dataset_name = None
            

        
        if not full_repaint:
            try:
                panel.plot_1D_update_data(msX, msY, "m/z", "Intensity", **plt_kwargs)
                if len(view_range): 
                    self.on_zoom_1D_x_axis(startX=view_range[0], endX=view_range[1], 
                                           repaint=False, plot="MS")
                panel.repaint()
                if override:
                    self.config.replotData['MS'] = {'xvals':msX, 'yvals':msY, 'xlimits':xlimits}
                return
            except: pass
         
        # check limits
        try:
            if math.isnan(xlimits.get(0, msX[0])): xlimits[0] = msX[0]
            if math.isnan(xlimits.get(1, msX[-1])): xlimits[1] = msX[-1]
        except:
            xlimits = [np.min(msX), np.max(msX)]
            
        panel.clearPlot() 
        panel.plot_1D(xvals=msX, 
                           yvals=msY, 
                           xlimits=xlimits,
                           xlabel="m/z", ylabel="Intensity",
                           axesSize=self.config._plotSettings[plot_size_key]['axes_size'],
                           plotType='MS',
                           **plt_kwargs)
        # Show the mass spectrum
        panel.repaint()
        
        if override:
            self.config.replotData['MS'] = {'xvals':msX, 'yvals':msY, 'xlimits':xlimits}
        
    def on_plot_1D(self, dtX=None, dtY=None, xlabel=None, color=None, override=True, 
                   full_repaint=False, replot=False, e=None, set_page=False):
               
        # change page
        if set_page: self.mainBook.SetSelection(self.config.panelNames['1D'])
               
        if replot:
            dtX, dtY, xlabel = self.presenter._get_replot_data('1D')
            if dtX is None or dtY is None or xlabel is None:
                return
               
        # get kwargs
        plt_kwargs = self._buildPlotParameters(plotType='1D')
        
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

    def on_plot_RT(self, rtX=None, rtY=None, xlabel=None, ylabel="Intensity", 
                   color=None, override=True, replot=False, full_repaint=False, 
                   e=None, set_page=False):
        
        # change page
        if set_page: self.mainBook.SetSelection(self.config.panelNames['RT'])
        
        if replot:
            rtX, rtY, xlabel = self.presenter._get_replot_data('RT')
            if rtX is None or rtY is None or xlabel is None:
                return
        
        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType='1D')
        
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
        plt_kwargs = self._buildPlotParameters(plotType='2D')

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
            if len(xvals) > 500:
                dlg = dlgBox(
                    exceptionTitle='Would you like to continue?',
                    exceptionMsg= "There are {} scans in this dataset (it could be slow to plot Waterfall plot...). Would you like to continue?".format(len(xvals)),
                    type="Question")
                if dlg == wx.ID_YES:
                    self.on_plot_waterfall(yvals=xvals, xvals=yvals, zvals=zvals, 
                                           xlabel=xlabel, ylabel=ylabel)
        try:
            self.on_plot_3D(zvals=zvals, labelsX=xvals, labelsY=yvals, 
                            xlabel=xlabel, ylabel=ylabel, zlabel='Intensity')
        except: pass
        
    def on_plot_violin(self, data=None, set_page=False, **kwargs):
        
                # change page
        if set_page: self.mainBook.SetSelection(self.config.panelNames['Waterfall'])
        
        # Unpack data
        if len(data) == 5:
            zvals, xvals, xlabel, yvals, ylabel = data
        elif len(data) == 6:
            zvals, xvals, xlabel, yvals, ylabel, cmap = data
        
        plt_kwargs = self._buildPlotParameters(plotType='1D')
        violin_kwargs = self._buildPlotParameters(plotType='violin')
        plt_kwargs = merge_two_dicts(plt_kwargs, violin_kwargs)
        if 'increment' in kwargs:
            plt_kwargs['increment'] = kwargs['increment']
        
        self.plotWaterfallIMS.clearPlot()
        try:
            if zvals.shape[1] < plt_kwargs['violin_nlimit']:
                self.plotWaterfallIMS.plot_1D_violin(xvals=yvals, yvals=xvals,
                                                     zvals=zvals, label="", 
                                                     xlabel=xlabel, 
                                                     ylabel=ylabel,
                                                     labels=kwargs.get('labels',[]),
                                                     axesSize=self.config._plotSettings['Violin']['axes_size'],
                                                     orientation=self.config.violin_orientation,
                                                     plotName='1D',
                                                     **plt_kwargs)
            else:
                self.presenter.onThreading(None, ("Selected item is too large to plot as violin. Plotting as waterfall instead.", 4, 10), 
                                           action='updateStatusbar')
                # check if there are more than 500 elements
                if zvals.shape[1] > 500:
                    dlg = dlgBox(exceptionTitle='Would you like to continue?',
                                 exceptionMsg= "There are {} scans in this dataset (this could be slow...). Would you like to continue?".format(len(xvals)),
                                 type="Question")
                    if dlg == wx.ID_NO:
                        return
                # plot
                self.on_plot_waterfall(yvals=xvals, xvals=yvals, zvals=zvals, 
                                       xlabel=xlabel, ylabel=ylabel)
        except:
            self.plotWaterfallIMS.clearPlot()
            print("Failed to plot the violin plot...")
            
        # Show the mass spectrum
        self.plotWaterfallIMS.repaint() 
        
    def on_plot_2D(self, zvals=None, xvals=None, yvals=None, xlabel=None, 
                     ylabel=None, cmap=None, cmapNorm=None, plotType=None, 
                     override=True, replot=False, e=None, set_page=False):
        
        # change page
        if set_page: self.mainBook.SetSelection(self.config.panelNames['2D'])
                    
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
        plt_kwargs = self._buildPlotParameters(plotType='2D')
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
                     cmap=None, cmapNorm=None, plotType=None,  override=True, replot=False, 
                     set_page=False):
        
        # change page
        if set_page: self.mainBook.SetSelection(self.config.panelNames['MZDT'])
        
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
        plt_kwargs = self._buildPlotParameters(plotType='2D')
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
                   cmapNorm=None, replot=False, set_page=False):
        
        # change page
        if set_page: self.mainBook.SetSelection(self.config.panelNames['3D'])
        
        plt1d_kwargs = self._buildPlotParameters(plotType='1D')
        plt3d_kwargs = self._buildPlotParameters(plotType='3D')
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
        
    def on_plot_waterfall(self, xvals, yvals, zvals, xlabel,  ylabel, colors=[], 
                          set_page=False, **kwargs):

        # change page
        if set_page: self.mainBook.SetSelection(self.config.panelNames['Waterfall'])
                
        plt_kwargs = self._buildPlotParameters(plotType='1D')
        waterfall_kwargs = self._buildPlotParameters(plotType='waterfall')
        plt_kwargs = merge_two_dicts(plt_kwargs, waterfall_kwargs)
        if 'increment' in kwargs:
            plt_kwargs['increment'] = kwargs['increment']
        
        self.plotWaterfallIMS.clearPlot()
        self.plotWaterfallIMS.plot_1D_waterfall(xvals=xvals, yvals=yvals,
                                                zvals=zvals, label="", 
                                                xlabel=xlabel, 
                                                ylabel=ylabel,
                                                colorList=colors,
                                                labels=kwargs.get('labels',[]),
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
        plt_kwargs = self._buildPlotParameters(plotType='1D')
        
        if self.currentPage == "Other":
            plot_name = self.plotOther
        else:
            plot_name = self.plotWaterfallIMS
        
        if self.plotWaterfallIMS.plot_name != "Violin":
            extra_kwargs = self._buildPlotParameters(plotType='waterfall')
        else:
            extra_kwargs = self._buildPlotParameters(plotType='violin')
            if which in ["data", "label"]:
                return
        plt_kwargs = merge_two_dicts(plt_kwargs, extra_kwargs)
        
        plot_name.plot_1D_waterfall_update(which=which, **plt_kwargs)
        plot_name.repaint()
        
    def on_plot_waterfall_overlay(self, xvals, yvals, zvals, colors, xlabel,  ylabel,
                                  labels=None, set_page=False, **kwargs):
        
        # change page
        if set_page: self.mainBook.SetSelection(self.config.panelNames['Waterfall'])
        
        plt_kwargs = self._buildPlotParameters(plotType='1D')
        waterfall_kwargs = self._buildPlotParameters(plotType='waterfall')
        plt_kwargs = merge_two_dicts(plt_kwargs, waterfall_kwargs)
        if 'increment' in kwargs:
            plt_kwargs['increment'] = kwargs['increment']
         
        self.plotWaterfallIMS.clearPlot()
        self.plotWaterfallIMS.plot_1D_waterfall_overlay(xvals=xvals, yvals=yvals,
                                                        zvals=zvals, label="", 
                                                        xlabel=xlabel, 
                                                        ylabel=ylabel,
                                                        colorList=colors,
                                                        labels=labels,
                                                        axesSize=self.config._plotSettings['Waterfall']['axes_size'],
                                                        plotName='1D',
                                                        **plt_kwargs)
        
        if ('add_legend' in kwargs and 'labels' in kwargs and
            len(colors) == len(kwargs['labels'])):
            if kwargs['add_legend']:
                legend_text = zip(colors, kwargs['labels'])
                self.plotWaterfallIMS.plot_1D_add_legend(legend_text, **plt_kwargs)
                
        self.plotWaterfallIMS.repaint()
        
    def on_plot_overlay_RT(self, xvals, yvals, xlabel, colors, labels, xlimits, style=None, 
                           set_page=False):

        # change page
        if set_page: self.mainBook.SetSelection(self.config.panelNames['RT'])

        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType='1D')

        
        self.plotRT.clearPlot()
        self.plotRT.plot_1D_overlay(xvals=xvals, yvals=yvals,
                                    title="", xlabel=xlabel,
                                     ylabel="Intensity", 
                                     labels=labels,
                                     colors=colors, 
                                     xlimits=xlimits,
                                     zoom='box',
                                     axesSize=self.config._plotSettings['RT']['axes_size'],
                                     plotName='1D',
                                     **plt_kwargs)
        self.plotRT.repaint()

    def on_plot_overlay_DT(self, xvals, yvals, xlabel, colors, labels, xlimits, style=None, 
                           set_page=False):

        # change page
        if set_page: self.mainBook.SetSelection(self.config.panelNames['1D'])

        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType='1D')

        self.plot1D.clearPlot()
        self.plot1D.plot_1D_overlay(xvals=xvals, yvals=yvals,
                                    title="", xlabel=xlabel,
                                    ylabel="Intensity", labels=labels,
                                    colors=colors, xlimits=xlimits,
                                    zoom='box', 
                                    axesSize=self.config._plotSettings['DT']['axes_size'],
                                    plotName='1D',
                                    **plt_kwargs)
        self.plot1D.repaint()

    def on_plot_overlay_2D(self, zvalsIon1, zvalsIon2, cmapIon1, cmapIon2,
                                  alphaIon1, alphaIon2, xvals, yvals, xlabel, ylabel,
                                  flag=None, plotName="2D", set_page=False):
        """
        Plot an overlay of *2* ions
        """

        # change page
        if set_page: self.mainBook.SetSelection(self.config.panelNames['Overlay'])

        plt_kwargs = self._buildPlotParameters(plotType='2D')
        self.plotOverlay.clearPlot()
        self.plotOverlay.plot_2D_overlay(zvalsIon1=zvalsIon1, 
                                         zvalsIon2=zvalsIon2, 
                                         cmapIon1=cmapIon1,
                                         cmapIon2=cmapIon2,
                                         alphaIon1=alphaIon1, 
                                         alphaIon2=alphaIon2,
                                         labelsX=xvals, 
                                         labelsY=yvals,
                                         xlabel=xlabel,
                                         ylabel=ylabel,
                                         axesSize=self.config._plotSettings['Overlay']['axes_size'],
                                         plotName=plotName,
                                         **plt_kwargs)
                                                          
        self.plotOverlay.repaint()

    def on_plot_rgb(self, zvals=None, xvals=None, yvals=None, xlabel=None, 
                    ylabel=None, legend_text=None, set_page=False):
        
        # change page
        if set_page: self.mainBook.SetSelection(self.config.panelNames['2D'])
        
        plt_kwargs = self._buildPlotParameters(plotType='2D')
        
        self.plot2D.clearPlot()
        self.plot2D.plot_2D_rgb(zvals, xvals, yvals, xlabel, ylabel,
                                axesSize=self.config._plotSettings['2D']['axes_size'],
                                legend_text=legend_text,
                                **plt_kwargs)
        self.plot2D.repaint()

    def on_plot_RMSDF(self, yvalsRMSF, zvals, xvals=None, yvals=None, xlabelRMSD=None,
                      ylabelRMSD=None, ylabelRMSF=None, color='blue', cmapNorm=None,
                      cmap='inferno', plotType=None, override=True, replot=False, 
                      set_page=False):
        """
        Plot RMSD and RMSF plots together in panel RMSD
        """
        
        # change page
        if set_page: self.mainBook.SetSelection(self.config.panelNames['RMSF'])
        
        plt_kwargs = self._buildPlotParameters(plotType='2D')
        rmsd_kwargs = self._buildPlotParameters(plotType='RMSF')
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
                   override=True, replot=False, set_page=False):
        
        # change page
        if set_page: self.mainBook.SetSelection(self.config.panelNames['RMSF'])
        
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
        plt_kwargs = self._buildPlotParameters(plotType='2D')
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
        
    def on_plot_MS_DT_calibration(self, msX=None, msY=None, xlimits=None, dtX=None, 
                                  dtY=None, color=None, xlabelDT='Drift time (bins)',
                                  plotType='both', set_page=False,
                                  view_range=[]): # onPlotMSDTCalibration

        # change page
        if set_page: self.mainBook.SetSelection(self.config.panelNames['Calibration'])
        
        # MS plot
        if plotType == 'both' or plotType == 'MS':
            self.view.panelPlots.topPlotMS.clearPlot()
            # get kwargs
            plt_kwargs = self._buildPlotParameters(plotType='1D')       
            self.topPlotMS.plot_1D(xvals=msX, yvals=msY, xlabel="m/z",
                                   ylabel="Intensity", xlimits=xlimits, 
                                   axesSize=self.config._plotSettings['Calibration (MS)']['axes_size'],
                                   plotType='1D',
                                   **plt_kwargs)
            if len(view_range): 
                self.on_zoom_1D_x_axis(startX=view_range[0], endX=view_range[1], 
                                       repaint=False, plot="calibration_MS")
            # Show the mass spectrum
            self.topPlotMS.repaint()
        
        if plotType == 'both' or plotType == '1DT':
            ylabel="Intensity"
            # 1DT plot
            self.bottomPlot1DT.clearPlot()
            # get kwargs
            plt_kwargs = self.view.panelPlots._buildPlotParameters(plotType='1D')       
            self.bottomPlot1DT.plot_1D(xvals=dtX, yvals=dtY, 
                                       xlabel=xlabelDT, ylabel=ylabel,
                                       axesSize=self.config._plotSettings['Calibration (DT)']['axes_size'],
                                       plotType='CalibrationDT',
                                       **plt_kwargs)      
            self.bottomPlot1DT.repaint()  
        
    def on_plot_DT_calibration(self, dtX=None, dtY=None, color=None,
                               xlabel='Drift time (bins)', set_page=False): # onPlot1DTCalibration
        
        # change page
        if set_page: self.mainBook.SetSelection(self.config.panelNames['Calibration'])
        
        # Check yaxis labels
        ylabel="Intensity"
        # 1DT plot
        self.bottomPlot1DT.clearPlot()
        # get kwargs
        plt_kwargs = self.view.panelPlots._buildPlotParameters(plotType='1D')       
        self.bottomPlot1DT.plot_1D(xvals=dtX, yvals=dtY, xlabel=xlabel, ylabel=ylabel,
                                   axesSize=self.config._plotSettings['Calibration (DT)']['axes_size'],
                                   plotType='1D',
                                   **plt_kwargs)      
        self.bottomPlot1DT.repaint() 
        
    def plot_2D_update_label(self):
        
        try:
            if self.plotRMSF.plot_name == 'RMSD':
                zvals, xvals, yvals, xlabel, ylabel = self.presenter._get_replot_data('2D')
            elif self.plotRMSF.plot_name == 'RMSF':
                zvals, xvals, yvals, xlabelRMSD, ylabelRMSD, ylabelRMSF = self.presenter._get_replot_data('RMSF')
            else:
                return
            
            plt_kwargs = self._buildPlotParameters(plotType='RMSF')
            rmsdXpos, rmsdYpos = self.presenter.onCalculateRMSDposition(xlist=xvals, ylist=yvals)
            
            plt_kwargs['rmsd_label_coordinates'] = [rmsdXpos, rmsdYpos]
            plt_kwargs['rmsd_label_color'] = self.config.rmsd_color
            
            self.plotRMSF.plot_2D_update_label(**plt_kwargs)
            self.plotRMSF.repaint()
        except:
            pass

    def plot_2D_matrix_update_label(self):
        plt_kwargs = self._buildPlotParameters(plotType='RMSF')
        
        try:
            self.plot2D.plot_2D_matrix_update_label(**plt_kwargs)
            self.plot2D.repaint()
        except:
            pass
        
    def on_plot_matrix(self, zvals=None, xylabels=None, cmap=None, override=True, 
                       replot=False, set_page=False):

        # change page
        if set_page: self.mainBook.SetSelection(self.config.panelNames['Comparison'])

        # If the user would like to replot data, you can directly unpack it
        if replot:
            zvals, xylabels, cmap = self.presenter._get_replot_data('Matrix')
            if zvals is None or xylabels is None or cmap is None:
                return

        # Check if cmap should be overwritten
        if self.config.useCurrentCmap:
            cmap = self.config.currentCmap
        
        plt_kwargs = self._buildPlotParameters(plotType='2D')
        rmsd_kwargs = self._buildPlotParameters(plotType='RMSF')
        plt_kwargs = merge_two_dicts(plt_kwargs, rmsd_kwargs)
        plt_kwargs['colormap'] = cmap
        
        self.plotCompare.clearPlot()
        self.plotCompare.plot_2D_matrix(zvals=zvals, xylabels=xylabels, 
                                        xNames=None, 
                                        axesSize=self.config._plotSettings['Comparison']['axes_size'],
                                        plotName='2D',
                                        **plt_kwargs)
        self.plotCompare.repaint()

        plt_kwargs = self._buildPlotParameters(plotType='3D')
        rmsd_kwargs = self._buildPlotParameters(plotType='RMSF')
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
                     cmap_1, cmap_2, set_page=False, **kwargs):
        
        if set_page: self.mainBook.SetSelection(self.config.panelNames['Overlay'])
        
        plt_kwargs = self._buildPlotParameters(plotType='2D')
        rmsd_kwargs = self._buildPlotParameters(plotType='RMSD')
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
        
    def on_plot_n_grid(self, n_zvals, cmap_list, title_list, xvals, yvals, xlabel, 
                       ylabel, set_page=False):
        
        if set_page: self.mainBook.SetSelection(self.config.panelNames['Overlay'])
        
        plt_kwargs = self._buildPlotParameters(plotType='2D')
        self.plotOverlay.clearPlot()
        self.plotOverlay.plot_n_grid_2D_overlay(n_zvals, cmap_list, title_list, 
                                                xvals, yvals, xlabel, ylabel, 
                                                axesSize=self.config._plotSettings['Overlay (Grid)']['axes_size'], 
                                                **plt_kwargs)
        self.plotOverlay.repaint()        

    def plot_compare(self, msX=None, msX_1=None, msX_2=None, msY_1=None, msY_2=None, 
                     msY=None, xlimits=None, replot=False, override=True, set_page=True):

        if set_page: self.mainBook.SetSelection(self.config.panelNames['MS'])

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
        else:
            legend = self.config.compare_massSpectrumParams['legend'] #self.config.compare_massSpectrum 
            subtract = self.config.compare_massSpectrumParams['subtract']
 
        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType='1D')

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
                                           plotType='compare_MS',
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
        
    def plot_colorbar_update(self, plot_window=""):
        plt_kwargs = self._buildPlotParameters(plotType='2D')
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
        plt_kwargs = self._buildPlotParameters(plotType='2D')
        
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
        
    def on_add_legend(self, labels, colors, plot="RT"):
        plt_kwargs = self._buildPlotParameters(plotType='legend')
        
        if len(colors) ==  len(labels):
            legend_text = zip(colors, labels)
            
        if plot == "RT":
            self.plotRT.plot_1D_add_legend(legend_text, **plt_kwargs)
            
    def on_clear_legend(self, plot, repaint=False):
        if plot == 'RT':
            self.plotRT.plot_remove_legend()
        
    def on_add_marker(self, xvals=None, yvals=None, color='b', marker='o', 
                    size=5, plot='MS', repaint=True, 
                    clear_first=False): #addMarkerMS
        if plot == 'MS':
            self.plot1.onAddMarker(xval=xvals, yval=yvals,
                                   color=color, marker=marker,
                                   size=size)
            self.plot1.repaint()
            
        elif plot == 'RT':
            if clear_first:
                self.plotRT.plot_remove_markers()
                
            self.plotRT.plot_add_markers(
                xvals, yvals, color=color, marker=marker,
                size=size)
            if repaint: self.plotRT.repaint()
            
        elif plot == 'CalibrationMS':
            self.topPlotMS.onAddMarker(xval=xvals, yval=yvals,
                                       color=color, marker=marker,
                                       size=size)
            self.topPlotMS.repaint()
            
        elif plot == 'CalibrationDT':
            self.bottomPlot1DT.onAddMarker(xval=xvals, yval=yvals, 
                                           color=color, marker=marker,
                                           size=size, testMax='yvals')
            self.bottomPlot1DT.repaint()
             
    def on_add_patch(self, x, y, width, height, color='r', alpha=0.5, 
                     repaint=False, plot='MS'): # addRectMS
        
        if plot == 'MS': 
            self.plot1.plot_add_patch(x,y, width, height, color=color,
                                    alpha=alpha)
            if not repaint: return 
            else:
                self.plot1.repaint()
                
        elif plot == 'CalibrationMS':
            self.topPlotMS.plot_add_patch(x,y, width, height, color=color, 
                                          alpha=alpha)
            if not repaint: return 
            else:
                self.topPlotMS.repaint()
                
        elif plot == 'RT':
            self.plotRT.plot_add_patch(x,y, width, height, color=color,
                                     alpha=alpha)
            if not repaint: return 
            else:
                self.plotRT.repaint()
            
    def on_zoom_1D(self, startX, endX, endY, plot='MS', set_page=False): # onZoomMS
        
        if plot == 'MS':
            self.plot1.onZoomIn(startX,endX, endY)
            self.plot1.repaint()
            if set_page: self.mainBook.SetSelection(self.config.panelNames['MS'])
        elif plot == 'CalibrationMS':
            self.topPlotMS.onZoomIn(startX,endX,endY)
            self.plot1.repaint()
            if set_page: self.mainBook.SetSelection(self.config.panelNames['1D'])
            
    def on_zoom_1D_x_axis(self, startX, endX, endY=None, set_page=False, plot="MS", repaint=True):
        
        if set_page: self.mainBook.SetSelection(self.config.panelNames['MS'])
        
        if plot == "MS":
            if endY is None:
                self.plot1.on_zoom_x_axis(startX,endX)
            else:
                self.plot1.on_zoom(startX,endX, endY)
                
            if repaint:
                self.plot1.repaint()
        elif plot == 'calibration_MS':
            self.topPlotMS.on_zoom_x_axis(startX,endX)
            if repaint:
                self.topPlotMS.repaint()
                
    def on_zoom_1D_xy_axis(self, startX, endX, startY, endY, set_page=False, plot="MS", repaint=True):
        
        if set_page: self.mainBook.SetSelection(self.config.panelNames['MS'])
        
        if plot == "MS":
            self.plot1.on_zoom_xy(startX,endX, startY, endY)
                
            if repaint:
                self.plot1.repaint()
        
    def addRectRT(self, x, y, width, height, color='r', alpha=0.5, 
                  repaint=False): # addRectRT
        self.view.panelPlots.plotRT.addRectangle(x,y,
                                                width,
                                                height,
                                                color=color,
                                                alpha=alpha)
        if not repaint: return 
        else:
            self.view.panelPlots.plotRT.repaint()

    def addTextMS(self, x,y, text, rotation, color="k"): # addTextMS
        self.view.panelPlots.plot1.addText(x,y, text, rotation, color)
        self.view.panelPlots.plot1.repaint()
        
    def addTextRMSD(self, x,y, text, rotation, color="k", plot='RMSD'): # addTextRMSD
        
        if plot == 'RMSD':
            self.view.panelPlots.plotRMSF.addText(x,y, text, rotation, 
                                                color=self.config.rmsd_color,
                                                fontsize=self.config.rmsd_fontSize,
                                                weight=self.config.rmsd_fontWeight)
            self.view.panelPlots.plotRMSF.repaint()
        elif plot == 'RMSF':
            self.view.panelPlots.plotRMSF.addText(x,y, text, rotation,
                                                  color=self.config.rmsd_color,
                                                  fontsize=self.config.rmsd_fontSize,
                                                  weight=self.config.rmsd_fontWeight)
            self.view.panelPlots.plotRMSF.repaint()
        elif plot == 'Grid':
            self.view.panelPlots.plotOverlay.addText(x,y, text, rotation,
                                                     color=self.config.rmsd_color,
                                                     fontsize=self.config.rmsd_fontSize,
                                                     weight=self.config.rmsd_fontWeight,
                                                     plot=plot)
            self.view.panelPlots.plotOverlay.repaint()
        
    def onAddMarker1D(self, xval=None, yval=None, color='r', marker='o'): # onAddMarker1D
        """ 
        This function adds marker to 1D plot
        """
        # Check yaxis labels
        ydivider = self.testXYmaxVals(values=yval)
        yval = yval / ydivider
        # Add single point
        self.view.panelPlots.bottomPlot1DT.onAddMarker(xval=xval, 
                                                       yval=yval,
                                                       color=color,
                                                       marker=marker)
        self.view.panelPlots.bottomPlot1DT.repaint() 
        
    def _buildPlotParameters(self, plotType = None, evt=None):
        add_frame_width = True
        if plotType == '1D':  
            plt_kwargs = {'line_width':self.config.lineWidth_1D,
                          'line_color':self.config.lineColour_1D,
                          'line_style':self.config.lineStyle_1D,
                          'shade_under':self.config.lineShadeUnder_1D,
                          'shade_under_color':self.config.lineShadeUnderColour_1D,
                          'shade_under_transparency':self.config.lineShadeUnderTransparency_1D,
                          'line_color_1':self.config.lineColour_MS1,
                          'line_color_2':self.config.lineColour_MS2,
                          'line_transparency_1':self.config.lineTransparency_MS1,
                          'line_transparency_2':self.config.lineTransparency_MS2,
                          'line_style_1':self.config.lineStyle_MS1,
                          'line_style_2':self.config.lineStyle_MS2,
                          'inverse':self.config.compare_massSpectrumParams['inverse'],
                          'tick_size':self.config.tickFontSize_1D,
                          'tick_weight':self.config.tickFontWeight_1D,
                          'label_size':self.config.labelFontSize_1D,
                          'label_weight':self.config.labelFontWeight_1D,
                          'title_size':self.config.titleFontSize_1D,
                          'title_weight':self.config.titleFontWeight_1D,
                          'frame_width':self.config.frameWidth_1D,
                          'label_pad':self.config.labelPad_1D,
                          'axis_onoff':self.config.axisOnOff_1D,
                          'ticks_left':self.config.ticks_left_1D,
                          'ticks_right':self.config.ticks_right_1D,
                          'ticks_top':self.config.ticks_top_1D,
                          'ticks_bottom':self.config.ticks_bottom_1D,
                          'tickLabels_left':self.config.tickLabels_left_1D,
                          'tickLabels_right':self.config.tickLabels_right_1D,
                          'tickLabels_top':self.config.tickLabels_top_1D,
                          'tickLabels_bottom':self.config.tickLabels_bottom_1D,
                          'spines_left':self.config.spines_left_1D,
                          'spines_right':self.config.spines_right_1D,
                          'spines_top':self.config.spines_top_1D,
                          'spines_bottom':self.config.spines_bottom_1D,
                          'scatter_edge_color':self.config.markerEdgeColor_1D,
                          'scatter_color':self.config.markerColor_1D,
                          'scatter_size':self.config.markerSize_1D,
                          'scatter_shape':self.config.markerShape_1D,
                          'scatter_alpha':self.config.markerTransparency_1D,
                          'legend':self.config.legend,
                          'legend_transparency':self.config.legendAlpha,
                          'legend_position':self.config.legendPosition,
                          'legend_num_columns':self.config.legendColumns,
                          'legend_font_size':self.config.legendFontSize,
                          'legend_frame_on':self.config.legendFrame,
                          'legend_fancy_box':self.config.legendFancyBox,
                          'legend_marker_first':self.config.legendMarkerFirst,
                          'legend_marker_size':self.config.legendMarkerSize,
                          'legend_num_markers':self.config.legendNumberMarkers,
                          'legend_line_width':self.config.legendLineWidth,
                          'legend_patch_transparency':self.config.legendPatchAlpha,
                          'bar_width':self.config.bar_width,
                          'bar_alpha':self.config.bar_alpha,
                          'bar_edgecolor':self.config.bar_edge_color,
                          'bar_edgecolor_sameAsFill':self.config.bar_sameAsFill,
                          'bar_linewidth':self.config.bar_lineWidth,
                          }
        elif plotType == "annotation":
            plt_kwargs = {'horizontal_alignment':self.config.annotation_label_horz,
                          'vertical_alignment':self.config.annotation_label_vert,
                          'font_size':self.config.annotation_label_font_size,
                          'font_weight':self.config.annotation_label_font_weight}
        elif plotType == 'legend':
            plt_kwargs = {'legend':self.config.legend,
                          'legend_transparency':self.config.legendAlpha,
                          'legend_position':self.config.legendPosition,
                          'legend_num_columns':self.config.legendColumns,
                          'legend_font_size':self.config.legendFontSize,
                          'legend_frame_on':self.config.legendFrame,
                          'legend_fancy_box':self.config.legendFancyBox,
                          'legend_marker_first':self.config.legendMarkerFirst,
                          'legend_marker_size':self.config.legendMarkerSize,
                          'legend_num_markers':self.config.legendNumberMarkers,
                          'legend_line_width':self.config.legendLineWidth,
                          'legend_patch_transparency':self.config.legendPatchAlpha
                          }
        elif plotType == "UniDec":
            plt_kwargs = {'bar_width':self.config.unidec_plot_bar_width,
                          'bar_alpha':self.config.unidec_plot_bar_alpha,
                          'bar_edgecolor':self.config.unidec_plot_bar_edge_color,
                          'bar_edgecolor_sameAsFill':self.config.unidec_plot_bar_sameAsFill,
                          'bar_linewidth':self.config.unidec_plot_bar_lineWidth,
                          'bar_marker_size':self.config.unidec_plot_bar_markerSize,
                          'fit_line_color':self.config.unidec_plot_fit_lineColor,
                          'isolated_marker_size':self.config.unidec_plot_isolatedMS_markerSize,
                          'MW_marker_size':self.config.unidec_plot_MW_markerSize,
                          'MW_show_markers':self.config.unidec_plot_MW_showMarkers,
                          'color_scheme':self.config.unidec_plot_color_scheme,
                          'colormap':self.config.unidec_plot_colormap,
                          'palette':self.config.unidec_plot_palette,
                          'maximum_shown_items':self.config.unidec_maxShown_individualLines,
                          'contour_levels':self.config.unidec_plot_contour_levels,
                          }
            
        elif plotType == '2D':  
            plt_kwargs = {'colorbar':self.config.colorbar,
                          'colorbar_width':self.config.colorbarWidth,
                          'colorbar_pad':self.config.colorbarPad,
                          'colorbar_range':self.config.colorbarRange,
                          'colorbar_min_points':self.config.colorbarMinPoints,
                          'colorbar_position':self.config.colorbarPosition,
                          'colorbar_label_size':self.config.colorbarLabelSize,
                          'legend':self.config.legend,
                          'legend_transparency':self.config.legendAlpha,
                          'legend_position':self.config.legendPosition,
                          'legend_num_columns':self.config.legendColumns,
                          'legend_font_size':self.config.legendFontSize,
                          'legend_frame_on':self.config.legendFrame,
                          'legend_fancy_box':self.config.legendFancyBox,
                          'legend_marker_first':self.config.legendMarkerFirst,
                          'legend_marker_size':self.config.legendMarkerSize,
                          'legend_num_markers':self.config.legendNumberMarkers,
                          'legend_line_width':self.config.legendLineWidth,
                          'legend_patch_transparency':self.config.legendPatchAlpha,
                          'interpolation':self.config.interpolation,
                          'frame_width':self.config.frameWidth_1D,
                          'axis_onoff':self.config.axisOnOff_1D,
                          'label_pad':self.config.labelPad_1D,
                          'tick_size':self.config.tickFontSize_1D,
                          'tick_weight':self.config.tickFontWeight_1D,
                          'label_size':self.config.labelFontSize_1D,
                          'label_weight':self.config.labelFontWeight_1D,
                          'title_size':self.config.titleFontSize_1D,
                          'title_weight':self.config.titleFontWeight_1D,
                          'ticks_left':self.config.ticks_left_1D,
                          'ticks_right':self.config.ticks_right_1D,
                          'ticks_top':self.config.ticks_top_1D,
                          'ticks_bottom':self.config.ticks_bottom_1D,
                          'tickLabels_left':self.config.tickLabels_left_1D,
                          'tickLabels_right':self.config.tickLabels_right_1D,
                          'tickLabels_top':self.config.tickLabels_top_1D,
                          'tickLabels_bottom':self.config.tickLabels_bottom_1D,
                          'spines_left':self.config.spines_left_1D,
                          'spines_right':self.config.spines_right_1D,
                          'spines_top':self.config.spines_top_1D,
                          'spines_bottom':self.config.spines_bottom_1D,
                          'override_colormap':self.config.useCurrentCmap,
                          'colormap':self.config.currentCmap,
                          'colormap_min':self.config.minCmap,
                          'colormap_mid':self.config.midCmap,
                          'colormap_max':self.config.maxCmap,
                          }
        elif plotType == '3D':  
            plt_kwargs = {'label_pad':self.config.labelPad_1D,
                          'tick_size':self.config.tickFontSize_1D,
                          'tick_weight':self.config.tickFontWeight_1D,
                          'label_size':self.config.labelFontSize_1D,
                          'label_weight':self.config.labelFontWeight_1D,
                          'title_size':self.config.titleFontSize_1D,
                          'title_weight':self.config.titleFontWeight_1D,
                          'scatter_edge_color':self.config.markerEdgeColor_3D,
                          'scatter_color':self.config.markerColor_3D,
                          'scatter_size':self.config.markerSize_3D,
                          'scatter_shape':self.config.markerShape_3D,
                          'scatter_alpha':self.config.markerTransparency_3D,
                          'grid':self.config.showGrids_3D,
                          'shade':self.config.shade_3D,
                          'show_ticks':self.config.ticks_3D,
                          'show_spines':self.config.spines_3D,
                          'show_labels':self.config.labels_3D}
            
        elif plotType in ['RMSD', 'RMSF']:
            plt_kwargs = {'axis_onoff_1D':self.config.axisOnOff_1D,
                          'ticks_left_1D':self.config.ticks_left_1D,
                          'ticks_right_1D':self.config.ticks_right_1D,
                          'ticks_top_1D':self.config.ticks_top_1D,
                          'ticks_bottom_1D':self.config.ticks_bottom_1D,
                          'tickLabels_left_1D':self.config.tickLabels_left_1D,
                          'tickLabels_right_1D':self.config.tickLabels_right_1D,
                          'tickLabels_top_1D':self.config.tickLabels_top_1D,
                          'tickLabels_bottom_1D':self.config.tickLabels_bottom_1D,
                          'spines_left_1D':self.config.spines_left_1D,
                          'spines_right_1D':self.config.spines_right_1D,
                          'spines_top_1D':self.config.spines_top_1D,
                          'spines_bottom_1D':self.config.spines_bottom_1D,
                          'rmsd_label_position':self.config.rmsd_position,
                          'rmsd_label_font_size':self.config.rmsd_fontSize,
                          'rmsd_label_font_weight':self.config.rmsd_fontWeight,
                          'rmsd_hspace':self.config.rmsd_hspace,
                          'rmsd_line_color':self.config.rmsd_lineColour,
                          'rmsd_line_transparency':self.config.rmsd_lineTransparency,
                          'rmsd_line_style':self.config.rmsd_lineStyle,
                          'rmsd_line_width':self.config.rmsd_lineWidth,
                          'rmsd_underline_hatch':self.config.rmsd_lineHatch,
                          'rmsd_underline_color':self.config.rmsd_underlineColor,
                          'rmsd_underline_transparency':self.config.rmsd_underlineTransparency,
                          'rmsd_matrix_rotX':self.config.rmsd_rotation_X,
                          'rmsd_matrix_rotY':self.config.rmsd_rotation_Y,
                          'rmsd_matrix_labels':self.config.rmsd_matrix_add_labels,
                          }
        elif plotType in 'waterfall':
            plt_kwargs = {'increment':self.config.waterfall_increment,
                          'offset':self.config.waterfall_offset,
                          'increment':self.config.waterfall_increment,
                          'line_width':self.config.waterfall_lineWidth,
                          'line_style':self.config.waterfall_lineStyle,
                          'reverse':self.config.waterfall_reverse,
                          'use_colormap': self.config.waterfall_useColormap,
                          'line_color':self.config.waterfall_color,
                          'shade_color':self.config.waterfall_shade_under_color,
                          'normalize':self.config.waterfall_normalize,
                          'colormap': self.config.waterfall_colormap,
                          'palette': self.config.currentPalette,
                          'color_scheme':self.config.waterfall_color_value,
                          'line_color_as_shade':self.config.waterfall_line_sameAsShade,
                          'add_labels': self.config.waterfall_add_labels,
                          'labels_frequency':self.config.waterfall_labels_frequency,
                          'labels_x_offset':self.config.waterfall_labels_x_offset,
                          'labels_y_offset':self.config.waterfall_labels_y_offset,
                          'labels_font_size':self.config.waterfall_label_fontSize,
                          'labels_font_weight': self.config.waterfall_label_fontWeight,
                          'labels_format': self.config.waterfall_label_format,
                          'shade_under':self.config.waterfall_shade_under,
                          'shade_under_n_limit': self.config.waterfall_shade_under_nlimit,
                          'shade_under_transparency':self.config.waterfall_shade_under_transparency,
                          'legend':self.config.legend,
                          'legend_transparency':self.config.legendAlpha,
                          'legend_position':self.config.legendPosition,
                          'legend_num_columns':self.config.legendColumns,
                          'legend_font_size':self.config.legendFontSize,
                          'legend_frame_on':self.config.legendFrame,
                          'legend_fancy_box':self.config.legendFancyBox,
                          'legend_marker_first':self.config.legendMarkerFirst,
                          'legend_marker_size':self.config.legendMarkerSize,
                          'legend_num_markers':self.config.legendNumberMarkers,
                          'legend_line_width':self.config.legendLineWidth,
                          'legend_patch_transparency':self.config.legendPatchAlpha,
                }
        elif plotType in ['violin']:
            plt_kwargs = {'min_percentage':self.config.violin_min_percentage,
                          'spacing':self.config.violin_spacing,
                          'line_width':self.config.violin_lineWidth,
                          'line_style':self.config.violin_lineStyle,
                          'line_color':self.config.violin_color,
                          'shade_color':self.config.violin_shade_under_color,
                          'normalize':self.config.violin_normalize,
                          'colormap': self.config.violin_colormap,
                          'palette': self.config.currentPalette,
                          'color_scheme':self.config.violin_color_value,
                          'line_color_as_shade':self.config.violin_line_sameAsShade,
                          'labels_format': self.config.violin_label_format,
                          'shade_under':self.config.violin_shade_under,
                          'violin_nlimit': self.config.violin_nlimit,
                          'shade_under_transparency':self.config.violin_shade_under_transparency,
                          'labels_frequency':self.config.violin_labels_frequency,
                          }
        elif plotType in ['arrow']:
            plt_kwargs = {'arrow_line_width':self.config.annotation_arrow_line_width,
                          'arrow_line_style':self.config.annotation_arrow_line_style,
                          'arrow_head_length':self.config.annotation_arrow_cap_length,
                          'arrow_head_width':self.config.annotation_arrow_cap_width}
            add_frame_width = False
        elif plotType == "label":
            plt_kwargs = {'horizontalalignment':self.config.annotation_label_horz,
                          'verticalalignment':self.config.annotation_label_vert,
                          'fontweight':self.config.annotation_label_font_weight,
                          'fontsize':self.config.annotation_label_font_size,
                          'rotation':self.config.annotation_label_font_orientation}
            add_frame_width = False
        
        if "frame_width" not in plt_kwargs and add_frame_width:
            plt_kwargs['frame_width'] = self.config.frameWidth_1D
            
        # return kwargs
        return plt_kwargs  
        
        
        