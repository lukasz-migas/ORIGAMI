# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import logging
import math
import os
import time

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import wx
from gui_elements.misc_dialogs import DialogBox
from icons.icons import IconContainer
from ids import ID_clearPlot_1D
from ids import ID_clearPlot_1D_MS
from ids import ID_clearPlot_2D
from ids import ID_clearPlot_3D
from ids import ID_clearPlot_Calibration
from ids import ID_clearPlot_Matrix
from ids import ID_clearPlot_MS
from ids import ID_clearPlot_MZDT
from ids import ID_clearPlot_other
from ids import ID_clearPlot_Overlay
from ids import ID_clearPlot_RMSD
from ids import ID_clearPlot_RMSF
from ids import ID_clearPlot_RT
from ids import ID_clearPlot_RT_MS
from ids import ID_clearPlot_UniDec_all
from ids import ID_clearPlot_UniDec_barchart
from ids import ID_clearPlot_UniDec_chargeDistribution
from ids import ID_clearPlot_UniDec_MS
from ids import ID_clearPlot_UniDec_mwDistribution
from ids import ID_clearPlot_UniDec_mwGrid
from ids import ID_clearPlot_UniDec_mzGrid
from ids import ID_clearPlot_UniDec_pickedPeaks
from ids import ID_clearPlot_Watefall
from ids import ID_clearPlot_Waterfall
from ids import ID_docTree_action_open_peak_picker
from ids import ID_extraSettings_colorbar
from ids import ID_extraSettings_general_plot
from ids import ID_extraSettings_legend
from ids import ID_extraSettings_plot1D
from ids import ID_extraSettings_plot2D
from ids import ID_extraSettings_plot3D
from ids import ID_extraSettings_rmsd
from ids import ID_extraSettings_violin
from ids import ID_extraSettings_waterfall
from ids import ID_highlightRectAllIons
from ids import ID_pickMSpeaksDocument
from ids import ID_plotPanel_binMS
from ids import ID_plotPanel_lockPlot
from ids import ID_plotPanel_resize
from ids import ID_plots_customise_plot
from ids import ID_plots_customise_plot_unidec_chargeDist
from ids import ID_plots_customise_plot_unidec_isolated_mz
from ids import ID_plots_customise_plot_unidec_ms
from ids import ID_plots_customise_plot_unidec_ms_barchart
from ids import ID_plots_customise_plot_unidec_mw
from ids import ID_plots_customise_plot_unidec_mw_v_charge
from ids import ID_plots_customise_plot_unidec_mz_v_charge
from ids import ID_plots_customise_smart_zoom
from ids import ID_plots_rotate90
from ids import ID_plots_saveImage_unidec_chargeDist
from ids import ID_plots_saveImage_unidec_isolated_mz
from ids import ID_plots_saveImage_unidec_ms
from ids import ID_plots_saveImage_unidec_ms_barchart
from ids import ID_plots_saveImage_unidec_mw
from ids import ID_plots_saveImage_unidec_mw_v_charge
from ids import ID_plots_saveImage_unidec_mz_v_charge
from ids import ID_processSettings_2D
from ids import ID_processSettings_MS
from ids import ID_save1DImage
from ids import ID_save1DImageDoc
from ids import ID_save2DImage
from ids import ID_save2DImageDoc
from ids import ID_save3DImage
from ids import ID_save3DImageDoc
from ids import ID_saveCompareMSImage
from ids import ID_saveMSImage
from ids import ID_saveMSImageDoc
from ids import ID_saveMZDTImage
from ids import ID_saveMZDTImageDoc
from ids import ID_saveOtherImage
from ids import ID_saveOtherImageDoc
from ids import ID_saveOverlayImage
from ids import ID_saveOverlayImageDoc
from ids import ID_saveRMSDImage
from ids import ID_saveRMSDImageDoc
from ids import ID_saveRMSDmatrixImage
from ids import ID_saveRMSDmatrixImageDoc
from ids import ID_saveRMSFImage
from ids import ID_saveRMSFImageDoc
from ids import ID_saveRTImage
from ids import ID_saveRTImageDoc
from ids import ID_saveUniDecAll
from ids import ID_saveWaterfallImage
from ids import ID_saveWaterfallImageDoc
from ids import ID_smooth1Ddata1DT
from ids import ID_smooth1DdataMS
from ids import ID_smooth1DdataRT
from natsort import natsorted
from panelCustomisePlot import panel_customise_plot
from pubsub import pub
from styles import makeMenuItem
from toolbox import merge_two_dicts
from utils.check import isempty
from utils.color import convertRGB1to255
from utils.color import convertRGB1toHEX
from utils.color import randomColorGenerator
from utils.exceptions import MessageError
from utils.path import clean_filename
from visuals import mpl_plots
from visuals.normalize import MidpointNormalize
logger = logging.getLogger('origami')

# TODO: Improve layout
# TODO: Improve how plot panels are generated
# TODO: Remove the following panels: Waterfall, UniDec, Overlay, RMSF, Calibration
# TODO: Rename the following panels: MS -> Mass spectrum; RT -> Chromatogram; 1D -> Mobilogram; 2D -> Heatmap; Other -> Annotated (or else)
# TODO: Make each function accept plot_obj and use the get_plot function
# TODO: Standardize how plots are exported
# TODO: Add option to copy plot clipboard


class panelPlot(wx.Panel):

    def __init__(self, parent, config, presenter):
        wx.Panel.__init__(
            self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
            size=wx.Size(800, 600), style=wx.TAB_TRAVERSAL,
        )

        self.config = config
        self.view = parent
        self.presenter = presenter
        self.icons = IconContainer()

        self.currentPage = None
        # Extract size of screen
        self.displaysize = wx.GetDisplaySize()
        self.SetDimensions(0, 0, self.displaysize[0] - 320, self.displaysize[1] - 50)
        self.displaysizeMM = wx.GetDisplaySizeMM()

        self.displayRes = (wx.GetDisplayPPI())
        self.figsizeX = (self.displaysize[0] - 320) / self.displayRes[0]
        self.figsizeY = (self.displaysize[1] - 70) / self.displayRes[1]

        # used to keep track of what were the last selected pages
        self.window_plot1D = 'MS'
        self.window_plot2D = '2D'
        self.window_plot3D = '3D'
        self.make_notebook()
        self.current_plot = self.plot1

        # bind events
        self.mainBook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.on_page_changed)

        # initialise
        self.on_page_changed(evt=None)

        # initilise pub
        pub.subscribe(self._update_label_position, 'update_text_position')

    def _setup_handling_and_processing(self):
        self.data_processing = self.view.data_processing
        self.data_handling = self.view.data_handling

    def on_get_current_page(self):
        self.currentPage = self.mainBook.GetPageText(self.mainBook.GetSelection())

    def _get_page_text(self):
        self.on_get_current_page()
        return self.currentPage

    def _set_page(self, page_name):
        self.mainBook.SetSelection(page_name)

    def _update_label_position(self, text_obj):
        document_title, dataset_name, annotation_name, text_type = text_obj.obj_name.split('|-|')

        # get document
        __, annotations = self.view.panelDocuments.documents.on_get_annotation_dataset(document_title, dataset_name)
        if text_type == 'annotation':
            new_pos_x, new_pos_y = text_obj.get_position()
            annotations[annotation_name]['position_label_x'] = np.round(new_pos_x, 4)
            annotations[annotation_name]['position_label_y'] = np.round(new_pos_y, 4)
            try:
                arrow_kwargs = self._buildPlotParameters(plotType='arrow')
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
                            arrow_list = [new_pos_x, new_pos_y, arrow_x_end - new_pos_x, arrow_y_end - new_pos_y]
                            self.current_plot.plot_add_arrow(
                                arrow_list, stick_to_intensity=True,
                                **arrow_kwargs
                            )
            except Exception:
                pass

        # update annotation
        self.view.panelDocuments.documents.on_update_annotation(
            annotations, document_title, dataset_name, set_data_only=True,
        )

    def on_page_changed(self, evt):
        # get current page
        self.currentPage = self.mainBook.GetPageText(self.mainBook.GetSelection())

        # keep track of previous pages
        if self.currentPage in ['MS', 'RT', '1D']:
            self.window_plot1D = self.currentPage
        elif self.currentPage in [
            '2D', 'DT/MS', 'Waterfall', 'RMSF', 'Comparison',
            'Overlay', 'UniDec', 'Other',
        ]:
            self.window_plot2D = self.currentPage
        elif self.currentPage in ['3D']:
            self.window_plot3D = self.currentPage

        if self.currentPage == 'Waterfall':
            self.current_plot = self.plot_waterfall
        elif self.currentPage == 'MS':
            self.current_plot = self.plot1
        elif self.currentPage == '1D':
            self.current_plot = self.plot1D
        elif self.currentPage == 'RT':
            self.current_plot = self.plotRT
        elif self.currentPage == '2D':
            self.current_plot = self.plot2D
        elif self.currentPage == 'DT/MS':
            self.current_plot = self.plot_DT_vs_MS
        elif self.currentPage == 'Overlay':
            self.current_plot = self.plot_overlay
        elif self.currentPage == 'Other':
            self.current_plot = self.plotOther

    def make_notebook(self):
        # Setup notebook
        self.mainBook = wx.Notebook(
            self, wx.ID_ANY, wx.DefaultPosition,
            wx.DefaultSize, 0,
        )
        # Setup PLOT MS
        self.panelMS = wx.Panel(
            self.mainBook, wx.ID_ANY, wx.DefaultPosition,
            wx.DefaultSize, wx.TAB_TRAVERSAL,
        )
        self.mainBook.AddPage(self.panelMS, 'MS', False)

        self.plot1 = mpl_plots.plots(
            self.panelMS,
            figsize=self.config._plotSettings['MS']['gui_size'],
            config=self.config,
        )

        boxsizer_MS = wx.BoxSizer(wx.VERTICAL)
        boxsizer_MS.Add(self.plot1, 1, wx.EXPAND)
        self.panelMS.SetSizer(boxsizer_MS)

        # Setup PLOT RT
        self.panelRT = wx.SplitterWindow(
            self.mainBook, wx.ID_ANY, wx.DefaultPosition,
            wx.DefaultSize, wx.TAB_TRAVERSAL | wx.SP_3DSASH,
        )
        self.mainBook.AddPage(self.panelRT, 'RT', False)

        # Create two panels for each dataset
        self.topPanelRT_RT = wx.Panel(self.panelRT)
        self.plotRT = mpl_plots.plots(
            self.topPanelRT_RT,
            figsize=self.config._plotSettings['RT']['gui_size'],
            config=self.config,
        )
        boxTopPanelRT = wx.BoxSizer(wx.VERTICAL)
        boxTopPanelRT.Add(self.plotRT, 1, wx.EXPAND)
        self.topPanelRT_RT.SetSizer(boxTopPanelRT)

        self.bottomPanelRT_MS = wx.Panel(self.panelRT)
        self.plot_RT_MS = mpl_plots.plots(
            self.bottomPanelRT_MS,
            figsize=self.config._plotSettings['MS (DT/RT)']['gui_size'],
            config=self.config,
        )
        boxBottomPanelMS = wx.BoxSizer(wx.VERTICAL)
        boxBottomPanelMS.Add(self.plot_RT_MS, 1, wx.EXPAND)
        self.bottomPanelRT_MS.SetSizer(boxBottomPanelMS)

        # Add panels to splitter window
        self.panelRT.SplitHorizontally(self.topPanelRT_RT, self.bottomPanelRT_MS)
        self.panelRT.SetMinimumPaneSize(300)
        self.panelRT.SetSashGravity(0.5)
        self.panelRT.SetSashSize(5)

        # Setup PLOT 1D
        self.panel1D = wx.SplitterWindow(
            self.mainBook, wx.ID_ANY, wx.DefaultPosition,
            wx.DefaultSize, wx.TAB_TRAVERSAL | wx.SP_3DSASH,
        )
        self.mainBook.AddPage(self.panel1D, '1D', False)

        # Create two panels for each dataset
        self.topPanel1D_1D = wx.Panel(self.panel1D)
        self.plot1D = mpl_plots.plots(
            self.topPanel1D_1D,
            figsize=self.config._plotSettings['DT']['gui_size'],
            config=self.config,
        )
        boxTopPanelMS = wx.BoxSizer(wx.VERTICAL)
        boxTopPanelMS.Add(self.plot1D, 1, wx.EXPAND)
        self.topPanel1D_1D.SetSizer(boxTopPanelMS)

        self.bottomPanel1D_MS = wx.Panel(self.panel1D)
        self.plot_DT_MS = mpl_plots.plots(
            self.bottomPanel1D_MS,
            figsize=self.config._plotSettings['MS (DT/RT)']['gui_size'],
            config=self.config,
        )
        boxBottomPanel1DT = wx.BoxSizer(wx.VERTICAL)
        boxBottomPanel1DT.Add(self.plot_DT_MS, 1, wx.EXPAND)
        self.bottomPanel1D_MS.SetSizer(boxBottomPanel1DT)

        # Add panels to splitter window
        self.panel1D.SplitHorizontally(self.topPanel1D_1D, self.bottomPanel1D_MS)
        self.panel1D.SetMinimumPaneSize(300)
        self.panel1D.SetSashGravity(0.5)
        self.panel1D.SetSashSize(5)

        # Setup PLOT 2D
        self.panel2D = wx.Panel(self.mainBook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.mainBook.AddPage(self.panel2D, '2D', False)

        self.plot2D = mpl_plots.plots(
            self.panel2D,
            figsize=self.config._plotSettings['2D']['gui_size'],
            config=self.config,
        )

        boxsizer_2D = wx.BoxSizer(wx.HORIZONTAL)
        boxsizer_2D.Add(self.plot2D, 1, wx.EXPAND | wx.ALL)
        self.panel2D.SetSizerAndFit(boxsizer_2D)

        # Setup PLOT DT/MS
        self.panelMZDT = wx.Panel(
            self.mainBook, wx.ID_ANY, wx.DefaultPosition,
            wx.DefaultSize, wx.TAB_TRAVERSAL,
        )
        self.mainBook.AddPage(self.panelMZDT, 'DT/MS', False)

        self.plot_DT_vs_MS = mpl_plots.plots(
            self.panelMZDT,
            figsize=self.config._plotSettings['DT/MS']['gui_size'],
            config=self.config,
        )

        boxsizer_MZDT = wx.BoxSizer(wx.HORIZONTAL)
        boxsizer_MZDT.Add(self.plot_DT_vs_MS, 1, wx.EXPAND | wx.ALL)
        self.panelMZDT.SetSizerAndFit(boxsizer_MZDT)

        # Setup PLOT WATERFALL
        self.waterfallIMS = wx.Panel(
            self.mainBook, wx.ID_ANY, wx.DefaultPosition,
            wx.DefaultSize, wx.TAB_TRAVERSAL,
        )
        self.mainBook.AddPage(self.waterfallIMS, 'Waterfall', False)

        self.plot_waterfall = mpl_plots.plots(
            self.waterfallIMS,
            figsize=self.config._plotSettings['Waterfall']['gui_size'],
            config=self.config,
        )

        boxsizer_waterfall = wx.BoxSizer(wx.HORIZONTAL)
        boxsizer_waterfall.Add(self.plot_waterfall, 1, wx.EXPAND | wx.ALL)
        self.waterfallIMS.SetSizerAndFit(boxsizer_waterfall)

        # Setup PLOT 3D
        self.panel3D = wx.Panel(
            self.mainBook, wx.ID_ANY, wx.DefaultPosition,
            wx.DefaultSize, wx.TAB_TRAVERSAL,
        )
        self.mainBook.AddPage(self.panel3D, '3D', False)

        self.plot3D = mpl_plots.plots(
            self.panel3D,
            figsize=self.config._plotSettings['3D']['gui_size'],
            config=self.config,
        )

        boxsizer_3D = wx.BoxSizer(wx.VERTICAL)
        boxsizer_3D.Add(self.plot3D, 1, wx.EXPAND)
        self.panel3D.SetSizer(boxsizer_3D)

        # Setup PLOT RMSF
        self.panelRMSF = wx.Panel(
            self.mainBook, wx.ID_ANY, wx.DefaultPosition,
            wx.DefaultSize, wx.TAB_TRAVERSAL,
        )
        self.mainBook.AddPage(self.panelRMSF, 'RMSF', False)

        self.plot_RMSF = mpl_plots.plots(
            self.panelRMSF,
            figsize=self.config._plotSettings['RMSF']['gui_size'],
            config=self.config,
        )
        boxsizer_RMSF = wx.BoxSizer(wx.VERTICAL)
        boxsizer_RMSF.Add(self.plot_RMSF, 1, wx.EXPAND)
        self.panelRMSF.SetSizer(boxsizer_RMSF)

        # Setup PLOT Comparison
        self.panelCompare = wx.Panel(
            self.mainBook, wx.ID_ANY, wx.DefaultPosition,
            wx.DefaultSize, wx.TAB_TRAVERSAL,
        )
        self.mainBook.AddPage(self.panelCompare, 'Comparison', False)

        self.plotCompare = mpl_plots.plots(
            self.panelCompare,
            figsize=self.config._plotSettings['Comparison']['gui_size'],
            config=self.config,
        )
        boxsizer_compare = wx.BoxSizer(wx.VERTICAL)
        boxsizer_compare.Add(self.plotCompare, 1, wx.EXPAND)
        self.panelCompare.SetSizer(boxsizer_compare)

        # Setup PLOT Overlay
        self.panelOverlay = wx.Panel(
            self.mainBook, wx.ID_ANY, wx.DefaultPosition,
            wx.DefaultSize, wx.TAB_TRAVERSAL,
        )
        self.mainBook.AddPage(self.panelOverlay, 'Overlay', False)

        self.plot_overlay = mpl_plots.plots(
            self.panelOverlay,
            figsize=self.config._plotSettings['Overlay']['gui_size'],
            config=self.config,
        )

        boxsizer_overlay = wx.BoxSizer(wx.VERTICAL)
        boxsizer_overlay.Add(self.plot_overlay, 1, wx.EXPAND)
        self.panelOverlay.SetSizer(boxsizer_overlay)

        self.panelCCSCalibration = wx.SplitterWindow(
            self.mainBook, wx.ID_ANY, wx.DefaultPosition,
            wx.DefaultSize, wx.TAB_TRAVERSAL | wx.SP_3DSASH,
        )
        # Create two panels for each dataset
        self.topPanelMS = wx.Panel(self.panelCCSCalibration)
        self.topPanelMS.SetBackgroundColour('white')

        self.bottomPanel1DT = wx.Panel(self.panelCCSCalibration)
        self.bottomPanel1DT.SetBackgroundColour('white')
        # Add panels to splitter window
        self.panelCCSCalibration.SplitHorizontally(self.topPanelMS, self.bottomPanel1DT)
        self.panelCCSCalibration.SetMinimumPaneSize(250)
        self.panelCCSCalibration.SetSashGravity(0.5)
        self.panelCCSCalibration.SetSashSize(10)
        # Add to notebook
        self.mainBook.AddPage(self.panelCCSCalibration, 'Calibration', False)

        # Plot MS
        self.topPlotMS = mpl_plots.plots(
            self.topPanelMS,
            figsize=self.config._plotSettings['Calibration (MS)']['gui_size'],
            config=self.config,
        )
        boxTopPanelMS = wx.BoxSizer(wx.VERTICAL)
        boxTopPanelMS.Add(self.topPlotMS, 1, wx.EXPAND)
        self.topPanelMS.SetSizer(boxTopPanelMS)

        # Plot 1DT
        self.bottomPlot1DT = mpl_plots.plots(
            self.bottomPanel1DT,
            figsize=self.config._plotSettings['Calibration (DT)']['gui_size'],
            config=self.config,
        )
        boxBottomPanel1DT = wx.BoxSizer(wx.VERTICAL)
        boxBottomPanel1DT.Add(self.bottomPlot1DT, 1, wx.EXPAND)
        self.bottomPanel1DT.SetSizer(boxBottomPanel1DT)

        if self.config.unidec_plot_panel_view == 'Single page view':
            self.panelUniDec = wx.lib.scrolledpanel.ScrolledPanel(
                self.mainBook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize,
                wx.TAB_TRAVERSAL,
            )
            self.panelUniDec.SetupScrolling()
            self.mainBook.AddPage(self.panelUniDec, 'UniDec', False)
            figsize = self.config._plotSettings['UniDec (MS)']['gui_size']
            self.plotUnidec_MS = mpl_plots.plots(self.panelUniDec, config=self.config, figsize=figsize)

            figsize = self.config._plotSettings['UniDec (m/z vs Charge)']['gui_size']
            self.plotUnidec_mzGrid = mpl_plots.plots(self.panelUniDec, config=self.config, figsize=figsize)

            figsize = self.config._plotSettings['UniDec (MW)']['gui_size']
            self.plotUnidec_mwDistribution = mpl_plots.plots(self.panelUniDec, config=self.config, figsize=figsize)

            figsize = self.config._plotSettings['UniDec (Isolated MS)']['gui_size']
            self.plotUnidec_individualPeaks = mpl_plots.plots(self.panelUniDec, config=self.config, figsize=figsize)

            figsize = self.config._plotSettings['UniDec (MW vs Charge)']['gui_size']
            self.plotUnidec_mwVsZ = mpl_plots.plots(self.panelUniDec, config=self.config, figsize=figsize)

            figsize = self.config._plotSettings['UniDec (Barplot)']['gui_size']
            self.plotUnidec_barChart = mpl_plots.plots(self.panelUniDec, config=self.config, figsize=figsize)

            figsize = self.config._plotSettings['UniDec (Charge Distribution)']['gui_size']
            self.plotUnidec_chargeDistribution = mpl_plots.plots(self.panelUniDec, config=self.config, figsize=figsize)

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
            self.panelUniDec = wx.Panel(
                self.mainBook, wx.ID_ANY, wx.DefaultPosition,
                wx.DefaultSize, wx.TAB_TRAVERSAL,
            )
            self.mainBook.AddPage(self.panelUniDec, 'UniDec', False)

            # Setup notebook
            self.unidec_notebook = wx.Notebook(self.panelUniDec, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0)
            # Setup PLOT MS
            self.unidec_MS = wx.Panel(
                self.unidec_notebook, wx.ID_ANY, wx.DefaultPosition,
                wx.DefaultSize, wx.TAB_TRAVERSAL,
            )
            self.unidec_notebook.AddPage(self.unidec_MS, 'MS', False)
            figsize = self.config._plotSettings['UniDec (MS)']['gui_size']
            self.plotUnidec_MS = mpl_plots.plots(self.unidec_MS, config=self.config, figsize=figsize)
            boxsizer_unidec_MS = wx.BoxSizer(wx.VERTICAL)
            boxsizer_unidec_MS.Add(self.plotUnidec_MS, 1, wx.EXPAND)
            self.unidec_MS.SetSizer(boxsizer_unidec_MS)

            self.unidec_mzGrid = wx.Panel(
                self.unidec_notebook, wx.ID_ANY, wx.DefaultPosition,
                wx.DefaultSize, wx.TAB_TRAVERSAL,
            )
            self.unidec_notebook.AddPage(self.unidec_mzGrid, 'm/z vs Charge', False)
            figsize = self.config._plotSettings['UniDec (m/z vs Charge)']['gui_size']
            self.plotUnidec_mzGrid = mpl_plots.plots(self.unidec_mzGrid, config=self.config, figsize=figsize)
            boxsizer_unidec_mzGrid = wx.BoxSizer(wx.VERTICAL)
            boxsizer_unidec_mzGrid.Add(self.plotUnidec_mzGrid, 1, wx.EXPAND)
            self.unidec_mzGrid.SetSizer(boxsizer_unidec_mzGrid)

            self.unidec_mwVsZ = wx.Panel(
                self.unidec_notebook, wx.ID_ANY, wx.DefaultPosition,
                wx.DefaultSize, wx.TAB_TRAVERSAL,
            )
            self.unidec_notebook.AddPage(self.unidec_mwVsZ, 'MW vs Charge', False)
            figsize = self.config._plotSettings['UniDec (MW vs Charge)']['gui_size']
            self.plotUnidec_mwVsZ = mpl_plots.plots(self.unidec_mwVsZ, config=self.config, figsize=figsize)
            boxsizer_unidec__mwVsZ = wx.BoxSizer(wx.VERTICAL)
            boxsizer_unidec__mwVsZ.Add(self.plotUnidec_mwVsZ, 1, wx.EXPAND)
            self.unidec_mwVsZ.SetSizer(boxsizer_unidec__mwVsZ)

            self.unidec_mwDistribution = wx.Panel(
                self.unidec_notebook, wx.ID_ANY, wx.DefaultPosition,
                wx.DefaultSize, wx.TAB_TRAVERSAL,
            )
            self.unidec_notebook.AddPage(self.unidec_mwDistribution, 'MW', False)
            figsize = self.config._plotSettings['UniDec (MW)']['gui_size']
            self.plotUnidec_mwDistribution = mpl_plots.plots(
                self.unidec_mwDistribution, config=self.config, figsize=figsize,
            )
            boxsizer_unidec_mwDistribution = wx.BoxSizer(wx.VERTICAL)
            boxsizer_unidec_mwDistribution.Add(self.plotUnidec_mwDistribution, 1, wx.EXPAND)
            self.unidec_mwDistribution.SetSizer(boxsizer_unidec_mwDistribution)

            self.unidec_individualPeaks = wx.Panel(
                self.unidec_notebook, wx.ID_ANY, wx.DefaultPosition,
                wx.DefaultSize, wx.TAB_TRAVERSAL,
            )
            self.unidec_notebook.AddPage(self.unidec_individualPeaks, 'Isolated MS', False)
            figsize = self.config._plotSettings['UniDec (Isolated MS)']['gui_size']
            self.plotUnidec_individualPeaks = mpl_plots.plots(
                self.unidec_individualPeaks, config=self.config, figsize=figsize,
            )
            boxsizer_unidec_individualPeaks = wx.BoxSizer(wx.VERTICAL)
            boxsizer_unidec_individualPeaks.Add(self.plotUnidec_individualPeaks, 1, wx.EXPAND)
            self.unidec_individualPeaks.SetSizer(boxsizer_unidec_individualPeaks)

            self.unidec_barChart = wx.Panel(
                self.unidec_notebook, wx.ID_ANY, wx.DefaultPosition,
                wx.DefaultSize, wx.TAB_TRAVERSAL,
            )
            self.unidec_notebook.AddPage(self.unidec_barChart, 'Barplot', False)
            figsize = self.config._plotSettings['UniDec (Barplot)']['gui_size']
            self.plotUnidec_barChart = mpl_plots.plots(
                self.unidec_barChart,
                config=self.config,
                figsize=figsize,
            )
            boxsizer_unidec_barChart = wx.BoxSizer(wx.VERTICAL)
            boxsizer_unidec_barChart.Add(self.plotUnidec_barChart, 1, wx.EXPAND)
            self.unidec_barChart.SetSizer(boxsizer_unidec_barChart)

            self.unidec_chargeDistribution = wx.Panel(
                self.unidec_notebook, wx.ID_ANY, wx.DefaultPosition,
                wx.DefaultSize, wx.TAB_TRAVERSAL,
            )
            self.unidec_notebook.AddPage(self.unidec_chargeDistribution, 'Charge distribution', False)
            figsize = self.config._plotSettings['UniDec (Charge Distribution)']['gui_size']
            self.plotUnidec_chargeDistribution = mpl_plots.plots(
                self.unidec_chargeDistribution,
                config=self.config,
                figsize=figsize,
            )
            boxsizer_unidec_chargeDistribution = wx.BoxSizer(wx.VERTICAL)
            boxsizer_unidec_chargeDistribution.Add(self.plotUnidec_chargeDistribution, 1, wx.EXPAND)
            self.unidec_chargeDistribution.SetSizer(boxsizer_unidec_chargeDistribution)

            tabSizer = wx.BoxSizer(wx.VERTICAL)
            tabSizer.Add(self.unidec_notebook, 1, wx.EXPAND | wx.ALL, 1)
            self.panelUniDec.SetSizerAndFit(tabSizer)

        # Other
        self.panelOther = wx.Panel(
            self.mainBook, wx.ID_ANY, wx.DefaultPosition,
            wx.DefaultSize, wx.TAB_TRAVERSAL,
        )
        self.mainBook.AddPage(self.panelOther, 'Other', False)

        self.plotOther = mpl_plots.plots(
            self.panelOther,
            figsize=self.config._plotSettings['2D']['gui_size'],
            config=self.config,
        )

        boxsizer_other = wx.BoxSizer(wx.VERTICAL)
        boxsizer_other.Add(self.plotOther, 1, wx.EXPAND)
        self.panelOther.SetSizer(boxsizer_other)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.mainBook, 1, wx.EXPAND | wx.ALL, 1)

        self.Bind(wx.EVT_CONTEXT_MENU, self.on_right_click)
        self.SetSizer(main_sizer)
        self.Layout()
        self.Show(True)

        # now that we set sizer, we can get window size
        panel_size = self.mainBook.GetSize()[1]
        half_size = (panel_size - 50) / 2

        self.panel1D.SetMinimumPaneSize(half_size)
        self.panelRT.SetMinimumPaneSize(half_size)

    def make_plot(self, parent, figsize):
        plot_panel = wx.Panel(parent)
        plot_window = mpl_plots.plots(plot_panel, config=self.config, figsize=figsize)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(plot_window, 1, wx.EXPAND)
        plot_panel.SetSizer(sizer)
        sizer.Fit(plot_panel)

        return plot_panel, plot_window, sizer

    def on_right_click(self, evt):
        self.currentPage = self.mainBook.GetPageText(self.mainBook.GetSelection())

        # Make bindings
        self.Bind(wx.EVT_MENU, self.data_processing.on_smooth_1D_and_add_data, id=ID_smooth1DdataMS)
        self.Bind(wx.EVT_MENU, self.data_processing.on_smooth_1D_and_add_data, id=ID_smooth1DdataRT)
        self.Bind(wx.EVT_MENU, self.data_processing.on_smooth_1D_and_add_data, id=ID_smooth1Ddata1DT)
        self.Bind(wx.EVT_MENU, self.data_handling.on_highlight_selected_ions, id=ID_highlightRectAllIons)
        self.Bind(wx.EVT_MENU, self.data_processing.on_pick_peaks, id=ID_pickMSpeaksDocument)
        self.Bind(wx.EVT_MENU, self.on_clear_plot, id=ID_clearPlot_MS)
        self.Bind(wx.EVT_MENU, self.on_clear_plot, id=ID_clearPlot_RT)
        self.Bind(wx.EVT_MENU, self.on_clear_plot, id=ID_clearPlot_RT_MS)
        self.Bind(wx.EVT_MENU, self.on_clear_plot, id=ID_clearPlot_1D)
        self.Bind(wx.EVT_MENU, self.on_clear_plot, id=ID_clearPlot_1D_MS)
        self.Bind(wx.EVT_MENU, self.on_clear_plot, id=ID_clearPlot_2D)
        self.Bind(wx.EVT_MENU, self.on_clear_plot, id=ID_clearPlot_3D)
        self.Bind(wx.EVT_MENU, self.on_clear_plot, id=ID_clearPlot_RMSF)
        self.Bind(wx.EVT_MENU, self.on_clear_plot, id=ID_clearPlot_RMSD)
        self.Bind(wx.EVT_MENU, self.on_clear_plot, id=ID_clearPlot_Matrix)
        self.Bind(wx.EVT_MENU, self.on_clear_plot, id=ID_clearPlot_Overlay)
        self.Bind(wx.EVT_MENU, self.on_clear_plot, id=ID_clearPlot_Watefall)
        self.Bind(wx.EVT_MENU, self.on_clear_plot, id=ID_clearPlot_Calibration)
        self.Bind(wx.EVT_MENU, self.on_clear_plot, id=ID_clearPlot_MZDT)
        self.Bind(wx.EVT_MENU, self.on_clear_plot, id=ID_clearPlot_Waterfall)
        self.Bind(wx.EVT_MENU, self.on_clear_plot, id=ID_clearPlot_other)
        self.Bind(wx.EVT_MENU, self.on_clear_plot, id=ID_clearPlot_UniDec_MS)
        self.Bind(wx.EVT_MENU, self.on_clear_plot, id=ID_clearPlot_UniDec_mwDistribution)
        self.Bind(wx.EVT_MENU, self.on_clear_plot, id=ID_clearPlot_UniDec_mzGrid)
        self.Bind(wx.EVT_MENU, self.on_clear_plot, id=ID_clearPlot_UniDec_mwGrid)
        self.Bind(wx.EVT_MENU, self.on_clear_plot, id=ID_clearPlot_UniDec_pickedPeaks)
        self.Bind(wx.EVT_MENU, self.on_clear_plot, id=ID_clearPlot_UniDec_barchart)
        self.Bind(wx.EVT_MENU, self.on_clear_plot, id=ID_clearPlot_UniDec_chargeDistribution)

        self.Bind(wx.EVT_MENU, self.on_clear_unidec, id=ID_clearPlot_UniDec_all)
        self.Bind(wx.EVT_MENU, self.onSetupMenus, id=ID_plotPanel_binMS)
        self.Bind(wx.EVT_MENU, self.on_lock_plot, id=ID_plotPanel_lockPlot)
        self.Bind(wx.EVT_MENU, self.on_rotate_plot, id=ID_plots_rotate90)
        self.Bind(wx.EVT_MENU, self.on_resize_check, id=ID_plotPanel_resize)

        self.Bind(wx.EVT_MENU, self.on_customise_plot, id=ID_plots_customise_plot)
        self.Bind(wx.EVT_MENU, self.on_customise_plot, id=ID_plots_customise_plot_unidec_ms)
        self.Bind(wx.EVT_MENU, self.on_customise_plot, id=ID_plots_customise_plot_unidec_mw)
        self.Bind(wx.EVT_MENU, self.on_customise_plot, id=ID_plots_customise_plot_unidec_mz_v_charge)
        self.Bind(wx.EVT_MENU, self.on_customise_plot, id=ID_plots_customise_plot_unidec_isolated_mz)
        self.Bind(wx.EVT_MENU, self.on_customise_plot, id=ID_plots_customise_plot_unidec_mw_v_charge)
        self.Bind(wx.EVT_MENU, self.on_customise_plot, id=ID_plots_customise_plot_unidec_ms_barchart)
        self.Bind(wx.EVT_MENU, self.on_customise_plot, id=ID_plots_customise_plot_unidec_chargeDist)

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

        self.Bind(wx.EVT_MENU, self.on_customise_smart_zoom, id=ID_plots_customise_smart_zoom)
        self.Bind(wx.EVT_MENU, self.on_open_peak_picker, id=ID_docTree_action_open_peak_picker)

        customiseUniDecMenu = wx.Menu()
        customiseUniDecMenu.Append(ID_plots_customise_plot_unidec_ms, 'Customise mass spectrum...')
        customiseUniDecMenu.Append(ID_plots_customise_plot_unidec_mw, 'Customise Zero charge mass spectrum...')
        customiseUniDecMenu.Append(ID_plots_customise_plot_unidec_mz_v_charge, 'Customise m/z vs charge...')
        customiseUniDecMenu.Append(
            ID_plots_customise_plot_unidec_mw_v_charge,
            'Customise molecular weight vs charge...',
        )
        customiseUniDecMenu.Append(
            ID_plots_customise_plot_unidec_isolated_mz,
            'Customise mass spectrum with isolated species...',
        )
        customiseUniDecMenu.Append(ID_plots_customise_plot_unidec_ms_barchart, 'Customise barchart...')
        customiseUniDecMenu.Append(
            ID_plots_customise_plot_unidec_chargeDist,
            'Customise charge state distribution...',
        )

        saveUniDecMenu = wx.Menu()
        saveUniDecMenu.Append(ID_plots_saveImage_unidec_ms, 'Save mass spectrum as...')
        saveUniDecMenu.Append(ID_plots_saveImage_unidec_mw, 'Save Zero charge mass spectrum as...')
        saveUniDecMenu.Append(ID_plots_saveImage_unidec_mz_v_charge, 'Save m/z vs charge as...')
        saveUniDecMenu.Append(ID_plots_saveImage_unidec_mw_v_charge, 'Save molecular weight vs charge as...')
        saveUniDecMenu.Append(ID_plots_saveImage_unidec_isolated_mz, 'Save mass spectrum with isolated species as...')
        saveUniDecMenu.Append(ID_plots_saveImage_unidec_ms_barchart, 'Save barchart as...')
        saveUniDecMenu.Append(ID_plots_saveImage_unidec_chargeDist, 'Save charge state distribution as...')
        saveUniDecMenu.AppendSeparator()
        saveUniDecMenu.AppendItem(
            makeMenuItem(
                parent=saveUniDecMenu, id=ID_saveUniDecAll, text='Save all figures as...',
                bitmap=self.icons.iconsLib['save16'],
            ),
        )

        # make main menu
        menu = wx.Menu()

        # pre-generate common menu items
        menu_edit_general = makeMenuItem(
            parent=menu, id=ID_extraSettings_general_plot,
            text='Edit general parameters...',
            bitmap=self.icons.iconsLib['panel_plot_general_16'],
        )
        menu_edit_plot_1D = makeMenuItem(
            parent=menu, id=ID_extraSettings_plot1D,
            text='Edit plot parameters...',
            bitmap=self.icons.iconsLib['panel_plot1D_16'],
        )
        menu_edit_plot_2D = makeMenuItem(
            parent=menu, id=ID_extraSettings_plot2D,
            text='Edit plot parameters...',
            bitmap=self.icons.iconsLib['panel_plot2D_16'],
        )
        menu_edit_plot_3D = makeMenuItem(
            parent=menu, id=ID_extraSettings_plot3D,
            text='Edit plot parameters...',
            bitmap=self.icons.iconsLib['panel_plot3D_16'],
        ),
        menu_edit_colorbar = makeMenuItem(
            parent=menu, id=ID_extraSettings_colorbar,
            text='Edit colorbar parameters...',
            bitmap=self.icons.iconsLib['panel_colorbar_16'],
        )
        menu_edit_legend = makeMenuItem(
            parent=menu, id=ID_extraSettings_legend,
            text='Edit legend parameters...',
            bitmap=self.icons.iconsLib['panel_legend_16'],
        )
        menu_edit_rmsd = makeMenuItem(
            parent=menu, id=ID_extraSettings_rmsd,
            text='Edit plot parameters...',
            bitmap=self.icons.iconsLib['panel_rmsd_16'],
        )
        menu_edit_waterfall = makeMenuItem(
            parent=menu, id=ID_extraSettings_waterfall,
            text='Edit waterfall parameters...',
            bitmap=self.icons.iconsLib['panel_waterfall_16'],
        )
        menu_edit_violin = makeMenuItem(
            parent=menu, id=ID_extraSettings_violin,
            text='Edit violin parameters...',
            bitmap=self.icons.iconsLib['panel_violin_16'],
        )
        menu_customise_plot = makeMenuItem(
            parent=menu, id=ID_plots_customise_plot,
            text='Customise plot...',
            bitmap=self.icons.iconsLib['change_xlabels_16'],
        )
        menu_action_rotate90 = makeMenuItem(
            parent=menu, id=ID_plots_rotate90,
            text='Rotate 90°',
            bitmap=self.icons.iconsLib['blank_16'],
        )
        menu_action_process_2D = makeMenuItem(
            parent=menu, id=ID_processSettings_2D,
            text='Process heatmap...',
            bitmap=self.icons.iconsLib['process_2d_16'],
        )

        menu_action_process_MS = makeMenuItem(
            parent=menu, id=ID_processSettings_MS,
            text='Process mass spectrum...',
            bitmap=self.icons.iconsLib['process_ms_16'],
        )

        if self.currentPage == 'MS':
            menu.AppendItem(menu_action_process_MS)
            menu.AppendItem(
                makeMenuItem(
                    parent=menu, id=ID_docTree_action_open_peak_picker,
                    text='Open peak picker...',
                    bitmap=self.icons.iconsLib['process_fit_16'],
                ),
            )
            menu.AppendItem(
                makeMenuItem(
                    parent=menu, id=ID_highlightRectAllIons,
                    text='Show extracted ions',
                    bitmap=self.icons.iconsLib['annotate16'],
                ),
            )
            menu.AppendSeparator()
            menu.AppendItem(menu_edit_general)
            menu.AppendItem(menu_edit_plot_1D)
            self.lock_plot_check = menu.AppendCheckItem(ID_plotPanel_lockPlot, 'Lock plot', help='')
            self.lock_plot_check.Check(self.plot1.lock_plot_from_updating)
            menu.AppendItem(menu_customise_plot)
            menu.AppendSeparator()
            self.resize_plot_check = menu.AppendCheckItem(ID_plotPanel_resize, 'Resize on saving', help='')
            self.resize_plot_check.Check(self.config.resize)
            if self.view.plot_name == 'compare_MS':
                menu.AppendItem(
                    makeMenuItem(
                        parent=menu, id=ID_saveCompareMSImage, text='Save figure as...',
                        bitmap=self.icons.iconsLib['save16'],
                    ),
                )
            else:
                menu.AppendItem(
                    makeMenuItem(
                        parent=menu, id=ID_saveMSImage, text='Save figure as...',
                        bitmap=self.icons.iconsLib['save16'],
                    ),
                )
            menu.AppendSeparator()
            menu.AppendItem(
                makeMenuItem(
                    parent=menu, id=ID_clearPlot_MS, text='Clear plot',
                    bitmap=self.icons.iconsLib['clear_16'],
                ),
            )
        elif self.currentPage == 'RT':
            if self.view.plot_name == 'MS':
                menu.AppendItem(
                    makeMenuItem(
                        parent=menu, id=ID_clearPlot_RT_MS, text='Clear plot',
                        bitmap=self.icons.iconsLib['clear_16'],
                    ),
                )
            else:
                menu.Append(ID_smooth1DdataRT, 'Smooth chromatogram')
                self.binMS_check = menu.AppendCheckItem(
                    ID_plotPanel_binMS,
                    'Bin mass spectra during extraction',
                    help='',
                )
                self.binMS_check.Check(self.config.ms_enable_in_RT)
                menu.AppendItem(menu_action_process_MS)
                menu.AppendSeparator()
                menu.AppendItem(menu_edit_general)
                menu.AppendItem(menu_edit_plot_1D)
                menu.AppendItem(menu_edit_legend)
                self.lock_plot_check = menu.AppendCheckItem(ID_plotPanel_lockPlot, 'Lock plot', help='')
                self.lock_plot_check.Check(self.plotRT.lock_plot_from_updating)
                menu.AppendItem(menu_customise_plot)
                menu.AppendSeparator()
                self.resize_plot_check = menu.AppendCheckItem(ID_plotPanel_resize, 'Resize on saving', help='')
                self.resize_plot_check.Check(self.config.resize)
                menu.AppendItem(
                    makeMenuItem(
                        parent=menu, id=ID_saveRTImage, text='Save figure as...',
                        bitmap=self.icons.iconsLib['save16'],
                    ),
                )
                menu.AppendSeparator()
                menu.AppendItem(
                    makeMenuItem(
                        parent=menu, id=ID_clearPlot_RT, text='Clear plot',
                        bitmap=self.icons.iconsLib['clear_16'],
                    ),
                )
        elif self.currentPage == '1D':
            if self.view.plot_name == 'MS':
                menu.AppendItem(
                    makeMenuItem(
                        parent=menu, id=ID_clearPlot_1D_MS, text='Clear plot',
                        bitmap=self.icons.iconsLib['clear_16'],
                    ),
                )
            else:
                menu.Append(ID_smooth1Ddata1DT, 'Smooth mobiligram')
                self.binMS_check = menu.AppendCheckItem(
                    ID_plotPanel_binMS,
                    'Bin mass spectra during extraction',
                    help='',
                )
                self.binMS_check.Check(self.config.ms_enable_in_RT)
                menu.AppendItem(menu_action_process_MS)
                menu.AppendSeparator()
                menu.AppendItem(menu_edit_general)
                menu.AppendItem(menu_edit_plot_1D)
                menu.AppendItem(menu_edit_legend)
                self.lock_plot_check = menu.AppendCheckItem(ID_plotPanel_lockPlot, 'Lock plot', help='')
                self.lock_plot_check.Check(self.plot1D.lock_plot_from_updating)
                menu.AppendItem(menu_customise_plot)
                menu.AppendSeparator()
                self.resize_plot_check = menu.AppendCheckItem(ID_plotPanel_resize, 'Resize on saving', help='')
                self.resize_plot_check.Check(self.config.resize)
                menu.AppendItem(
                    makeMenuItem(
                        parent=menu, id=ID_save1DImage, text='Save figure as...',
                        bitmap=self.icons.iconsLib['save16'],
                    ),
                )
                menu.AppendSeparator()
                menu.AppendItem(
                    makeMenuItem(
                        parent=menu, id=ID_clearPlot_1D, text='Clear plot',
                        bitmap=self.icons.iconsLib['clear_16'],
                    ),
                )
        elif self.currentPage == '2D':
            menu.AppendItem(menu_action_process_2D)
            menu.AppendItem(menu_action_rotate90)
            menu.AppendSeparator()
            menu.AppendItem(menu_edit_general)
            menu.AppendItem(menu_edit_plot_2D)
            menu.AppendItem(menu_edit_colorbar)
            menu.AppendItem(menu_edit_legend)
            self.lock_plot_check = menu.AppendCheckItem(ID_plotPanel_lockPlot, 'Lock plot', help='')
            self.lock_plot_check.Check(self.plot2D.lock_plot_from_updating)
            menu.AppendItem(menu_customise_plot)
            menu.AppendSeparator()
            self.resize_plot_check = menu.AppendCheckItem(ID_plotPanel_resize, 'Resize on saving', help='')
            self.resize_plot_check.Check(self.config.resize)
            menu.AppendItem(
                makeMenuItem(
                    parent=menu, id=ID_save2DImage, text='Save figure as...',
                    bitmap=self.icons.iconsLib['save16'],
                ),
            )
            menu.AppendSeparator()
            menu.AppendItem(
                makeMenuItem(
                    parent=menu, id=ID_clearPlot_2D, text='Clear plot',
                    bitmap=self.icons.iconsLib['clear_16'],
                ),
            )
        elif self.currentPage == 'DT/MS':
            menu.AppendItem(menu_action_process_2D)
            menu.AppendItem(menu_action_rotate90)
            menu.AppendSeparator()
            menu.AppendItem(
                makeMenuItem(
                    parent=menu,
                    id=ID_plots_customise_smart_zoom,
                    text='Customise smart zoom....',
                    bitmap=self.icons.iconsLib['zoom_16'],
                ),
            )
            menu.AppendSeparator()
            menu.AppendItem(menu_edit_general)
            menu.AppendItem(menu_edit_plot_2D)
            menu.AppendItem(menu_edit_colorbar)
            self.lock_plot_check = menu.AppendCheckItem(ID_plotPanel_lockPlot, 'Lock plot', help='')
            self.lock_plot_check.Check(self.plot_DT_vs_MS.lock_plot_from_updating)
            menu.AppendItem(menu_customise_plot)
            menu.AppendSeparator()
            self.resize_plot_check = menu.AppendCheckItem(ID_plotPanel_resize, 'Resize on saving', help='')
            self.resize_plot_check.Check(self.config.resize)
            menu.AppendItem(
                makeMenuItem(
                    parent=menu, id=ID_saveMZDTImage, text='Save figure as...',
                    bitmap=self.icons.iconsLib['save16'],
                ),
            )
            menu.AppendSeparator()
            menu.AppendItem(
                makeMenuItem(
                    parent=menu, id=ID_clearPlot_MZDT, text='Clear plot',
                    bitmap=self.icons.iconsLib['clear_16'],
                ),
            )
        elif self.currentPage == '3D':
            menu.AppendItem(menu_edit_plot_3D)
            menu.AppendSeparator()
            self.resize_plot_check = menu.AppendCheckItem(ID_plotPanel_resize, 'Resize on saving', help='')
            self.resize_plot_check.Check(self.config.resize)
            menu.AppendItem(
                makeMenuItem(
                    parent=menu, id=ID_save3DImage, text='Save figure as...',
                    bitmap=self.icons.iconsLib['save16'],
                ),
            )
            menu.AppendSeparator()
            menu.AppendItem(
                makeMenuItem(
                    parent=menu, id=ID_clearPlot_3D, text='Clear plot',
                    bitmap=self.icons.iconsLib['clear_16'],
                ),
            )
        elif self.currentPage == 'Overlay':
            menu.AppendItem(menu_edit_general)
            menu.AppendItem(menu_edit_plot_2D)
            menu.AppendSeparator()
            self.lock_plot_check = menu.AppendCheckItem(ID_plotPanel_lockPlot, 'Lock plot', help='')
            self.lock_plot_check.Check(self.plot_overlay.lock_plot_from_updating)
            menu.AppendItem(menu_customise_plot)
            menu.AppendSeparator()
            self.resize_plot_check = menu.AppendCheckItem(ID_plotPanel_resize, 'Resize on saving', help='')
            self.resize_plot_check.Check(self.config.resize)
            menu.AppendItem(
                makeMenuItem(
                    parent=menu, id=ID_saveOverlayImage, text='Save figure as...',
                    bitmap=self.icons.iconsLib['save16'],
                ),
            )
            menu.AppendSeparator()
            menu.AppendItem(
                makeMenuItem(
                    parent=menu, id=ID_clearPlot_Overlay, text='Clear plot',
                    bitmap=self.icons.iconsLib['clear_16'],
                ),
            )
        elif self.currentPage == 'Waterfall':
            menu.AppendItem(menu_edit_general)
            menu.AppendItem(menu_edit_plot_2D)
            menu.AppendItem(menu_edit_legend)
            menu.AppendItem(menu_edit_waterfall)
            menu.AppendItem(menu_edit_violin)
            self.lock_plot_check = menu.AppendCheckItem(ID_plotPanel_lockPlot, 'Lock plot', help='')
            self.lock_plot_check.Check(self.plot_waterfall.lock_plot_from_updating)
            menu.AppendItem(menu_customise_plot)
            menu.AppendSeparator()
            self.resize_plot_check = menu.AppendCheckItem(ID_plotPanel_resize, 'Resize on saving', help='')
            self.resize_plot_check.Check(self.config.resize)
            menu.AppendItem(
                makeMenuItem(
                    parent=menu, id=ID_saveWaterfallImage, text='Save figure as...',
                    bitmap=self.icons.iconsLib['save16'],
                ),
            )
            menu.AppendSeparator()
            menu.AppendItem(
                makeMenuItem(
                    parent=menu, id=ID_clearPlot_Waterfall, text='Clear plot',
                    bitmap=self.icons.iconsLib['clear_16'],
                ),
            )
        elif self.currentPage == 'RMSF':
            menu.AppendItem(menu_edit_general)
            menu.AppendItem(menu_edit_rmsd)
            menu.AppendItem(menu_customise_plot)
            menu.AppendSeparator()
            self.resize_plot_check = menu.AppendCheckItem(ID_plotPanel_resize, 'Resize on saving', help='')
            self.resize_plot_check.Check(self.config.resize)
            menu.AppendItem(
                makeMenuItem(
                    parent=menu, id=ID_saveRMSFImage, text='Save figure as...',
                    bitmap=self.icons.iconsLib['save16'],
                ),
            )
            menu.AppendSeparator()
            menu.AppendItem(
                makeMenuItem(
                    parent=menu, id=ID_clearPlot_RMSF, text='Clear plot',
                    bitmap=self.icons.iconsLib['clear_16'],
                ),
            )
        elif self.currentPage == 'Comparison':
            menu.AppendItem(menu_edit_general)
            menu.AppendItem(menu_customise_plot)
            menu.AppendSeparator()
            self.resize_plot_check = menu.AppendCheckItem(ID_plotPanel_resize, 'Resize on saving', help='')
            self.resize_plot_check.Check(self.config.resize)
            menu.AppendItem(
                makeMenuItem(
                    parent=menu, id=ID_saveRMSDmatrixImage, text='Save figure as...',
                    bitmap=self.icons.iconsLib['save16'],
                ),
            )
            menu.AppendSeparator()
            menu.AppendItem(
                makeMenuItem(
                    parent=menu, id=ID_clearPlot_Matrix, text='Clear plot',
                    bitmap=self.icons.iconsLib['clear_16'],
                ),
            )
        elif self.currentPage == 'Calibration':
            menu.AppendItem(
                makeMenuItem(
                    parent=menu, id=ID_clearPlot_Calibration, text='Clear plot',
                    bitmap=self.icons.iconsLib['clear_16'],
                ),
            )
        elif self.currentPage == 'UniDec':

            menu.AppendItem(menu_edit_general)
            menu.AppendItem(menu_edit_plot_1D)
            menu.AppendItem(menu_edit_plot_2D)
            menu.AppendItem(menu_edit_colorbar)
            menu.AppendItem(menu_edit_legend)
            menu.AppendSeparator()
            evtID = {
                'MS': ID_plots_customise_plot_unidec_ms,
                'mwDistribution': ID_plots_customise_plot_unidec_mw,
                'mzGrid': ID_plots_customise_plot_unidec_mz_v_charge,
                'mwGrid': ID_plots_customise_plot_unidec_mw_v_charge,
                'pickedPeaks': ID_plots_customise_plot_unidec_isolated_mz,
                'Barchart': ID_plots_customise_plot_unidec_ms_barchart,
                'ChargeDistribution': ID_plots_customise_plot_unidec_chargeDist
            }.get(self.view.plot_name, None)

            if evtID is not None:
                menu.AppendItem(
                    makeMenuItem(
                        parent=menu, id=evtID,
                        text='Customise plot...',
                        bitmap=self.icons.iconsLib['change_xlabels_16'],
                    ),
                )
            menu.AppendMenu(wx.ID_ANY, 'Customise plot...', customiseUniDecMenu)
            menu.AppendSeparator()
            self.resize_plot_check = menu.AppendCheckItem(ID_plotPanel_resize, 'Resize on saving', help='')
            self.resize_plot_check.Check(self.config.resize)

            evtID = {
                'MS': ID_plots_saveImage_unidec_ms,
                'mwDistribution': ID_plots_saveImage_unidec_mw,
                'mzGrid': ID_plots_saveImage_unidec_mz_v_charge,
                'mwGrid': ID_plots_saveImage_unidec_mw_v_charge,
                'pickedPeaks': ID_plots_saveImage_unidec_isolated_mz,
                'Barchart': ID_plots_saveImage_unidec_ms_barchart,
                'ChargeDistribution': ID_plots_saveImage_unidec_chargeDist
            }.get(self.view.plot_name, None)

            if evtID is not None:
                menu.AppendItem(
                    makeMenuItem(
                        parent=menu, id=evtID, text='Save figure as...',
                        bitmap=self.icons.iconsLib['save16'],
                    ),
                )
            menu.AppendMenu(wx.ID_ANY, 'Save figure...', saveUniDecMenu)
            menu.AppendSeparator()

            evtID = {
                'MS': ID_clearPlot_UniDec_MS,
                'mwDistribution': ID_clearPlot_UniDec_mwDistribution,
                'mzGrid': ID_clearPlot_UniDec_mzGrid,
                'mwGrid': ID_clearPlot_UniDec_mwGrid,
                'pickedPeaks': ID_clearPlot_UniDec_pickedPeaks,
                'Barchart': ID_clearPlot_UniDec_barchart,
                'ChargeDistribution': ID_clearPlot_UniDec_chargeDistribution
            }.get(self.view.plot_name, None)

            if evtID is not None:
                menu.AppendItem(
                    makeMenuItem(
                        parent=menu, id=evtID, text='Clear plot',
                        bitmap=self.icons.iconsLib['clear_16'],
                    ),
                )

            menu.AppendItem(
                makeMenuItem(
                    parent=menu, id=ID_clearPlot_UniDec_all, text='Clear all',
                    bitmap=self.icons.iconsLib['clear_16'],
                ),
            )
        elif self.currentPage == 'Other':
            menu.AppendItem(menu_edit_general)
            menu.AppendItem(menu_edit_plot_1D)
            menu.AppendItem(menu_edit_plot_2D)
            menu.AppendItem(menu_edit_colorbar)
            menu.AppendItem(menu_edit_legend)
            menu.AppendItem(menu_edit_waterfall)
            menu.AppendItem(menu_edit_violin)
            menu.AppendSeparator()
            menu.AppendItem(
                makeMenuItem(
                    parent=menu, id=ID_plots_customise_plot,
                    text='Customise plot...',
                    bitmap=self.icons.iconsLib['change_xlabels_16'],
                ),
            )
            menu.AppendSeparator()
            self.resize_plot_check = menu.AppendCheckItem(ID_plotPanel_resize, 'Resize on saving', help='')
            self.resize_plot_check.Check(self.config.resize)
            menu.AppendItem(
                makeMenuItem(
                    parent=menu, id=ID_saveOtherImage, text='Save figure as...',
                    bitmap=self.icons.iconsLib['save16'],
                ),
            )
            menu.AppendSeparator()
            menu.AppendItem(
                makeMenuItem(
                    parent=menu, id=ID_clearPlot_other, text='Clear plot',
                    bitmap=self.icons.iconsLib['clear_16'],
                ),
            )

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def onSetupMenus(self, evt):

        evtID = evt.GetId()

        if evtID == ID_plotPanel_binMS:
            check_value = not self.config.ms_enable_in_RT
            self.config.ms_enable_in_RT = check_value
            if self.config.ms_enable_in_RT:
                args = ('Mass spectra will be binned when extracted from chromatogram and mobiligram windows', 4)
            else:
                args = ('Mass spectra will be not binned when extracted from chromatogram and mobiligram windows', 4)
            self.presenter.onThreading(evt, args, action='updateStatusbar')

    def save_images(self, evt, path=None, **save_kwargs):
        """ Save figure depending on the event ID """
        args = ('Saving image. Please wait...', 4, 10)

        self.data_handling.update_statusbar('Saving image...', 4)

        # retrieve event ID
        if isinstance(evt, int):
            evtID = evt
        elif evt is None:
            evtID = None
        else:
            evtID = evt.GetId()

        path, title = self.data_handling._on_get_document_path_and_title()
        if path is None:
            args = ('Could not find path', 4)
            self.presenter.onThreading(None, args, action='updateStatusbar')
            return

        # Select default name + link to the plot
        if evtID in [ID_saveMSImage, ID_saveMSImageDoc]:
            image_name = self.config._plotSettings['MS']['default_name']
            resizeName = 'MS'
            plotWindow = self.plot1

        # Select default name + link to the plot
        elif evtID in [ID_saveCompareMSImage]:
            image_name = self.config._plotSettings['MS (compare)']['default_name']
            resizeName = 'MS (compare)'
            plotWindow = self.plot1

        elif evtID in [ID_saveRTImage, ID_saveRTImageDoc]:
            image_name = self.config._plotSettings['RT']['default_name']
            resizeName = 'RT'
            plotWindow = self.plotRT

        elif evtID in [ID_save1DImage, ID_save1DImageDoc]:
            image_name = self.config._plotSettings['DT']['default_name']
            resizeName = 'DT'
            plotWindow = self.plot1D

        elif evtID in [ID_save2DImage, ID_save2DImageDoc]:
            plotWindow = self.plot2D
            image_name = self.config._plotSettings['2D']['default_name']
            resizeName = '2D'

        elif evtID in [ID_save3DImage, ID_save3DImageDoc]:
            image_name = self.config._plotSettings['3D']['default_name']
            resizeName = '3D'
            plotWindow = self.plot3D

        elif evtID in [ID_saveWaterfallImage, ID_saveWaterfallImageDoc]:
            plotWindow = self.plot_waterfall
            if plotWindow.plot_name == 'Violin':
                image_name = self.config._plotSettings['Violin']['default_name']
                resizeName = 'Violin'
            else:
                image_name = self.config._plotSettings['Waterfall']['default_name']
                resizeName = 'Waterfall'

        elif evtID in [
            ID_saveRMSDImage, ID_saveRMSDImageDoc,
            ID_saveRMSFImage, ID_saveRMSFImageDoc,
        ]:
            plotWindow = self.plot_RMSF
            image_name = self.config._plotSettings['RMSD']['default_name']
            resizeName = plotWindow.get_plot_name()

        elif evtID in [ID_saveOverlayImage, ID_saveOverlayImageDoc]:
            plotWindow = self.plot_overlay
            image_name = plotWindow.get_plot_name()
            resizeName = 'Overlay'

        elif evtID in [ID_saveRMSDmatrixImage, ID_saveRMSDmatrixImageDoc]:
            image_name = self.config._plotSettings['Matrix']['default_name']
            resizeName = 'Matrix'
            plotWindow = self.plotCompare

        elif evtID in [ID_saveMZDTImage, ID_saveMZDTImageDoc]:
            image_name = self.config._plotSettings['DT/MS']['default_name']
            resizeName = 'DT/MS'
            plotWindow = self.plot_DT_vs_MS

        elif evtID in [ID_plots_saveImage_unidec_ms]:
            image_name = self.config._plotSettings['UniDec (MS)']['default_name']
            resizeName = 'UniDec (MS)'
            plotWindow = self.plotUnidec_MS

        elif evtID in [ID_plots_saveImage_unidec_mw]:
            image_name = self.config._plotSettings['UniDec (MW)']['default_name']
            resizeName = 'UniDec (MW)'
            plotWindow = self.plotUnidec_mwDistribution

        elif evtID in [ID_plots_saveImage_unidec_mz_v_charge]:
            image_name = self.config._plotSettings['UniDec (m/z vs Charge)']['default_name']
            resizeName = 'UniDec (m/z vs Charge)'
            plotWindow = self.plotUnidec_mzGrid

        elif evtID in [ID_plots_saveImage_unidec_isolated_mz]:
            image_name = self.config._plotSettings['UniDec (Isolated MS)']['default_name']
            resizeName = 'UniDec (Isolated MS)'
            plotWindow = self.plotUnidec_individualPeaks

        elif evtID in [ID_plots_saveImage_unidec_mw_v_charge]:
            image_name = self.config._plotSettings['UniDec (MW vs Charge)']['default_name']
            resizeName = 'UniDec (MW vs Charge)'
            plotWindow = self.plotUnidec_mwVsZ

        elif evtID in [ID_plots_saveImage_unidec_ms_barchart]:
            image_name = self.config._plotSettings['UniDec (Barplot)']['default_name']
            resizeName = 'UniDec (Barplot)'
            plotWindow = self.plotUnidec_barChart

        elif evtID in [ID_plots_saveImage_unidec_chargeDist]:
            image_name = self.config._plotSettings['UniDec (Charge Distribution)']['default_name']
            resizeName = 'UniDec (Charge Distribution)'
            plotWindow = self.plotUnidec_chargeDistribution

        elif evtID in [ID_saveOtherImageDoc, ID_saveOtherImage]:
            image_name = 'custom_plot'
            resizeName = None
            plotWindow = self.plotOther
        elif evtID is None and 'plot_obj' in save_kwargs:
            image_name = save_kwargs.get('image_name')
            resizeName = None
            plotWindow = save_kwargs.pop('plot_obj')

        # generate a better default name and remove any silly characters
        if 'image_name' in save_kwargs:
            image_name = save_kwargs.pop('image_name')
            if image_name is None:
                image_name = '{}_{}'.format(title, image_name)
        else:
            image_name = '{}_{}'.format(title, image_name)
        image_name = clean_filename(image_name)

        # Setup filename
        wildcard = 'SVG Scalable Vector Graphic (*.svg)|*.svg|' + \
                   'SVGZ Compressed Scalable Vector Graphic (*.svgz)|*.svgz|' + \
                   'PNG Portable Network Graphic (*.png)|*.png|' + \
                   'Enhanced Windows Metafile (*.eps)|*.eps|' + \
                   'JPEG File Interchange Format (*.jpeg)|*.jpeg|' + \
                   'TIFF Tag Image File Format (*.tiff)|*.tiff|' + \
                   'RAW Image File Format (*.raw)|*.raw|' + \
                   'PS PostScript Image File Format (*.ps)|*.ps|' + \
                   'PDF Portable Document Format (*.pdf)|*.pdf'

        wildcard_dict = {
            'svg': 0, 'svgz': 1, 'png': 2, 'eps': 3, 'jpeg': 4,
            'tiff': 5, 'raw': 6, 'ps': 7, 'pdf': 8,
        }

        dlg = wx.FileDialog(
            self,
            'Save as...', '', '',
            wildcard=wildcard,
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        )
        dlg.CentreOnParent()
        dlg.SetFilename(image_name)
        try:
            dlg.SetFilterIndex(wildcard_dict[self.config.imageFormat])
        except Exception:
            logger.error('Could not set image format')

        if dlg.ShowModal() == wx.ID_OK:
            tstart = time.clock()
            filename = dlg.GetPath()
            __, extension = os.path.splitext(filename)
            self.config.imageFormat = extension[1::]

            # build kwargs
            kwargs = {
                'transparent': self.config.transparent,
                'dpi': self.config.dpi,
                'format': extension[1::],
                'compression': 'zlib',
                'resize': None,
            }

            if self.config.resize:
                kwargs['resize'] = resizeName

            plotWindow.save_figure(path=filename, **kwargs)

            tend = time.clock()
            msg = 'Saved figure to {}. It took {} s.'.format(path, str(np.round((tend - tstart), 4)))
            args = (msg, 4)
        else:
            msg = 'Operation was cancelled'

        self.data_handling.update_statusbar(msg, 4)

    def on_open_peak_picker(self, evt):
        plot_obj = self.get_plot_from_name('MS')

        document_name = plot_obj.document_name
        dataset_name = plot_obj.dataset_name
        if document_name is None or dataset_name is None:
            raise MessageError(
                'No spectrum information',
                'Document title and/or spectrum title were not recorded for this plot.' +
                '\n\nYou can try peak picking by right-clicking in the document tree on the desired mass spectrum' +
                ' and clicking on `Open peak picker`',
            )

        self.view.panelDocuments.documents.on_open_peak_picker(
            None, document_name=document_name, dataset_name=dataset_name,
        )

    def get_plot_from_name(self, plot_name):
        plot_dict = {
            'MS': self.plot1,
            'RT': self.plotRT,
            '1D': self.plot1D,
            '2D': self.plot2D,
            'DT/MS': self.plot_DT_vs_MS,
            'CalibrationMS': self.topPlotMS,
            'CalibrationDT': self.bottomPlot1DT,
            'Overlay': self.plot_overlay,
            'RMSF': self.plot_RMSF,
            'Compare': self.plotCompare,
            'Waterfall': self.plot_waterfall,
            'Other': self.plotOther,
            '3D': self.plot3D,
            'Matrix': self.plotCompare,
            'UniDec_MS': self.plotUnidec_MS,
            'UniDec_MW': self.plotUnidec_mwDistribution,
            'UniDec_mz_v_charge': self.plotUnidec_mzGrid,
            'UniDec_peaks': self.plotUnidec_individualPeaks,
            'UniDec_mw_v_charge': self.plotUnidec_mwVsZ,
            'UniDec_bar': self.plotUnidec_barChart,
            'UniDec_charge': self.plotUnidec_chargeDistribution,

        }

        return plot_dict.get(plot_name, None)

    def on_lock_plot(self, evt):
        if self.currentPage == 'Waterfall':
            plot = self.plot_waterfall
        elif self.currentPage == 'MS':
            plot = self.plot1
        elif self.currentPage == '1D':
            plot = self.plot1D
        elif self.currentPage == 'RT':
            plot = self.plotRT
        elif self.currentPage == '2D':
            plot = self.plot2D
        elif self.currentPage == 'DT/MS':
            plot = self.plot_DT_vs_MS
        elif self.currentPage == 'Overlay':
            plot = self.plot_overlay

        plot.lock_plot_from_updating = not plot.lock_plot_from_updating

    def on_resize_check(self, evt):
        self.config.resize = not self.config.resize

    def on_customise_smart_zoom(self, evt):
        from gui_elements.dialog_customise_smart_zoom import dialog_customise_smart_zoom
        dlg = dialog_customise_smart_zoom(self, self.presenter, self.config)
        dlg.ShowModal()

    def on_customise_plot(self, evt, **kwargs):
        open_window, title = True, ''

        if 'plot' in kwargs and 'plot_obj' in kwargs:
            plot = kwargs.pop('plot_obj')
            title = kwargs.pop('plot')
        elif self.currentPage == 'Waterfall':
            plot, title = self.plot_waterfall, 'Waterfall...'
        elif self.currentPage == 'MS':
            plot, title = self.plot1, 'Mass spectrum...'
        elif self.currentPage == '1D':
            plot, title = self.plot1D, 'Mobiligram...'
        elif self.currentPage == 'RT':
            plot, title = self.plotRT, 'Chromatogram ...'
        elif self.currentPage == '2D':
            plot, title = self.plot2D, 'Heatmap...'
        elif self.currentPage == 'DT/MS':
            plot, title = self.plot_DT_vs_MS, 'DT/MS...'
        elif self.currentPage == 'Overlay':
            plot, title = self.plot_overlay, 'Overlay'
            if plot.plot_name not in ['Mask', 'Transparent']:
                open_window = False
        elif self.currentPage == 'RMSF':
            plot, title = self.plot_RMSF, 'RMSF'
            if plot.plot_name not in ['RMSD']:
                open_window = False
        elif self.currentPage == 'Comparison':
            plot, title = self.plotCompare, 'Comparison...'
        elif self.currentPage == 'UniDec':
            evtID = evt.GetId()
            if evtID == ID_plots_customise_plot_unidec_ms:
                plot, title = self.plotUnidec_MS, 'UniDec - Mass spectrum...'
            elif evtID == ID_plots_customise_plot_unidec_mw:
                plot, title = self.plotUnidec_mwDistribution, 'UniDec - Molecular weight distribution...'
            elif evtID == ID_plots_customise_plot_unidec_mz_v_charge:
                plot, title = self.plotUnidec_mzGrid, 'UniDec - Mass spectrum vs charge...'
            elif evtID == ID_plots_customise_plot_unidec_isolated_mz:
                plot, title = self.plotUnidec_individualPeaks, 'UniDec - Mass spectrum with individual species...'
            elif evtID == ID_plots_customise_plot_unidec_mw_v_charge:
                plot, title = self.plotUnidec_mwVsZ, 'UniDec - molecular weight vs charge...'
            elif evtID == ID_plots_customise_plot_unidec_ms_barchart:
                plot, title = self.plotUnidec_barChart, 'UniDec - Barchart...'
            elif evtID == ID_plots_customise_plot_unidec_chargeDist:
                plot, title = self.plotUnidec_chargeDistribution, 'UniDec - Charge state distribution...'
        elif self.currentPage == 'Other':
            plot, title = self.plotOther, 'Custom data...'

        if not open_window:
            args = ('Cannot customise parameters for this plot. Try replotting instead', 4)
            self.presenter.onThreading(None, args, action='updateStatusbar')
            return

        if not hasattr(plot, 'plotMS'):
            args = ('Cannot customise plot parameters, either because it does nto exist or is not supported yet.', 4)
            self.presenter.onThreading(None, args, action='updateStatusbar')
            return

        if hasattr(plot, 'plot_limits') and len(plot.plot_limits) == 4:
            xmin, xmax = plot.plot_limits[0], plot.plot_limits[1]
            ymin, ymax = plot.plot_limits[2], plot.plot_limits[3]
        else:
            try:
                xmin, xmax = plot.plotMS.get_xlim()
                ymin, ymax = plot.plotMS.get_ylim()
            except AttributeError:
                args = ('Cannot customise plot parameters if the plot does not exist', 4)
                self.presenter.onThreading(None, args, action='updateStatusbar')
                return

        dpi = wx.ScreenDC().GetPPI()
        if hasattr(plot, 'plot_parameters'):
            if 'panel_size' in plot.plot_parameters:
                plot_sizeInch = (
                    np.round(plot.plot_parameters['panel_size'][0] / dpi[0], 2),
                    np.round(plot.plot_parameters['panel_size'][1] / dpi[1], 2),
                )
            else:
                plot_size = plot.GetSize()
                plot_sizeInch = (
                    np.round(plot_size[0] / dpi[0], 2),
                    np.round(plot_size[1] / dpi[1], 2),
                )
        else:
            plot_size = plot.GetSize()
            plot_sizeInch = (
                np.round(plot_size[0] / dpi[0], 2),
                np.round(plot_size[1] / dpi[1], 2),
            )

        try:
            kwargs = {
                'xmin': xmin, 'xmax': xmax,
                'ymin': ymin, 'ymax': ymax,
                'major_xticker': plot.plotMS.xaxis.get_major_locator(),
                'major_yticker': plot.plotMS.yaxis.get_major_locator(),
                'minor_xticker': plot.plotMS.xaxis.get_minor_locator(),
                'minor_yticker': plot.plotMS.yaxis.get_minor_locator(),
                'tick_size': self.config.tickFontSize_1D,
                'tick_weight': self.config.tickFontWeight_1D,
                'label_size': self.config.labelFontSize_1D,
                'label_weight': self.config.labelFontWeight_1D,
                'title_size': self.config.titleFontSize_1D,
                'title_weight': self.config.titleFontWeight_1D,
                'xlabel': plot.plotMS.get_xlabel(),
                'ylabel': plot.plotMS.get_ylabel(),
                'title': plot.plotMS.get_title(),
                'plot_size': plot_sizeInch,
                'plot_axes': plot._axes,
                'plot': plot,
                'window_title': title,
            }
        except AttributeError:
            args = ('Cannot customise plot parameters if the plot does not exist', 4)
            self.presenter.onThreading(None, args, action='updateStatusbar')
            return

        dlg = panel_customise_plot(self, self.presenter, self.config, **kwargs)
        dlg.ShowModal()

    def on_rotate_plot(self, evt):
        plot = self.get_current_plot()

        plot.on_rotate_90()
        plot.repaint()

    def get_current_plot(self):
        if self.currentPage == 'Waterfall':
            plot = self.plot_waterfall
        elif self.currentPage == 'MS':
            plot = self.plot1
        elif self.currentPage == '1D':
            plot = self.plot1D
        elif self.currentPage == 'RT':
            plot = self.plotRT
        elif self.currentPage == '2D':
            plot = self.plot2D
        elif self.currentPage == 'DT/MS':
            plot = self.plot_DT_vs_MS
        elif self.currentPage == 'Overlay':
            plot = self.plot_overlay
        elif self.currentPage == 'RMSF':
            plot = self.plot_RMSF
        elif self.currentPage == 'Comparison':
            plot = self.plotCompare
        elif self.currentPage == 'Other':
            plot = self.plotOther

        return plot

    def save_unidec_images(self, evt, path=None):
        """ Save figure depending on the event ID """

        path, document_name = self.presenter.getCurrentDocumentPath()
        document_name = document_name.replace('.raw', '').replace(' ', '')
        if path is None:
            args = ('Could not find path', 4)
            self.presenter.onThreading(None, args, action='updateStatusbar')
            return

        plots = {
            'UniDec (MS)': self.plotUnidec_MS,
            'UniDec (MW)': self.plotUnidec_mwDistribution,
            'UniDec (m/z vs Charge)': self.plotUnidec_mzGrid,
            'UniDec (Isolated MS)': self.plotUnidec_individualPeaks,
            'UniDec (MW vs Charge)': self.plotUnidec_mwVsZ,
            'UniDec (Barplot)': self.plotUnidec_barChart,
            'UniDec (Charge Distribution)': self.plotUnidec_chargeDistribution,
        }

        for plot in plots:
            image_name = self.config._plotSettings[plot]['default_name']

            # generate a better default name and remove any silly characters
            image_name = '{}_{}'.format(document_name, image_name)
            image_name = clean_filename(image_name)

            self.save_images(None, plot_obj=plots[plot], image_name=image_name)

    def plot_update_axes(self, plotName):

        # get current sizes
        axes_sizes = self.config._plotSettings[plotName]['axes_size']

        # get link to the plot
        if plotName == 'MS':
            resize_plot = [self.plot1, self.plot_RT_MS, self.plot_DT_MS]
        elif plotName == 'MS (compare)':
            resize_plot = self.plot1
        elif plotName == 'RT':
            resize_plot = self.plotRT
        elif plotName == 'DT':
            resize_plot = self.plot1D
        elif plotName == '2D':
            resize_plot = self.plot2D
        elif plotName == 'Waterfall':
            resize_plot = self.plot_waterfall
        elif plotName == 'RMSD':
            resize_plot = self.plot_RMSF
        elif plotName in ['Comparison', 'Matrix']:
            resize_plot = self.plotCompare
        elif plotName == 'DT/MS':
            resize_plot = self.plot_DT_vs_MS
        elif plotName in ['Overlay', 'Overlay (Grid)']:
            resize_plot = self.plot_overlay
        elif plotName == 'Calibration (MS)':
            resize_plot = self.topPlotMS
        elif plotName == 'Calibration (DT)':
            resize_plot = self.bottomPlot1DT
        elif plotName == '3D':
            resize_plot = self.plot3D
        elif plotName == 'UniDec (MS)':
            resize_plot = self.plotUnidec_MS
        elif plotName == 'UniDec (MW)':
            resize_plot = self.plotUnidec_mwDistribution
        elif plotName == 'UniDec (m/z vs Charge)':
            resize_plot = self.plotUnidec_mzGrid
        elif plotName == 'UniDec (Isolated MS)':
            resize_plot = self.plotUnidec_individualPeaks
        elif plotName == 'UniDec (MW vs Charge)':
            resize_plot = self.plotUnidec_mwVsZ
        elif plotName == 'UniDec (Barplot)':
            resize_plot = self.plotUnidec_barChart
        elif plotName == 'UniDec (Charge Distribution)':
            resize_plot = self.plotUnidec_chargeDistribution

        # apply new size
        try:
            if not isinstance(resize_plot, list):
                resize_plot = [resize_plot]
            for plot in resize_plot:
                if plot.lock_plot_from_updating:
                    msg = 'This plot is locked and you cannot use global setting updated. \n' + \
                          'Please right-click in the plot area and select Customise plot...' + \
                          ' to adjust plot settings.'
                    print(msg)
                    continue
                plot.plot_update_axes(axes_sizes)
                plot.repaint()
                plot._axes = axes_sizes
        except (AttributeError, UnboundLocalError):
            pass

    def plot_update_size(self, plotName=None):
        dpi = wx.ScreenDC().GetPPI()
        resizeSize = self.config._plotSettings[plotName]['gui_size']
        figsizeNarrowPix = (int(resizeSize[0] * dpi[0]), int(resizeSize[1] * dpi[1]))

        if plotName == 'MS':
            resize_plot = self.plot1
        elif plotName == 'MS (compare)':
            resize_plot = self.plot1
        elif plotName == 'RT':
            resize_plot = self.plotRT
        elif plotName == 'DT':
            resize_plot = self.plot1D
        elif plotName == '2D':
            resize_plot = self.plot2D
        elif plotName == 'Waterfall':
            resize_plot = self.plot_waterfall
        elif plotName == 'RMSD':
            resize_plot = self.plot_RMSF
        elif plotName in ['Comparison', 'Matrix']:
            resize_plot = self.plotCompare
        elif plotName == 'DT/MS':
            resize_plot = self.plot_DT_vs_MS
        elif plotName in ['Overlay', 'Overlay (Grid)']:
            resize_plot = self.plot_overlay
        elif plotName == 'Calibration (MS)':
            resize_plot = self.topPlotMS
        elif plotName == 'Calibration (DT)':
            resize_plot = self.bottomPlot1DT
        elif plotName == '3D':
            resize_plot = self.plot3D
        elif plotName == 'UniDec (MS)':
            resize_plot = self.plotUnidec_MS
        elif plotName == 'UniDec (MW)':
            resize_plot = self.plotUnidec_mwDistribution
        elif plotName == 'UniDec (m/z vs Charge)':
            resize_plot = self.plotUnidec_mzGrid
        elif plotName == 'UniDec (Isolated MS)':
            resize_plot = self.plotUnidec_individualPeaks
        elif plotName == 'UniDec (MW vs Charge)':
            resize_plot = self.plotUnidec_mwVsZ
        elif plotName == 'UniDec (Barplot)':
            resize_plot = self.plotUnidec_barChart
        elif plotName == 'UniDec (Charge Distribution)':
            resize_plot = self.plotUnidec_chargeDistribution

        try:
            if resize_plot.lock_plot_from_updating:
                msg = 'This plot is locked and you cannot use global setting updated. \n' + \
                      'Please right-click in the plot area and select Customise plot...' + \
                      ' to adjust plot settings.'
                print(msg)
                return
            resize_plot.SetSize(figsizeNarrowPix)
        except (AttributeError, UnboundLocalError):
            pass

    def on_change_plot_style(self, evt, plot_style=None):

        # https://tonysyu.github.io/raw_content/matplotlib-style-gallery/gallery.html

        if self.config.currentStyle == 'Default':
            matplotlib.rcParams.update(matplotlib.rcParamsDefault)
        elif self.config.currentStyle == 'ggplot':
            plt.style.use('ggplot')
        elif self.config.currentStyle == 'ticks':
            sns.set_style('ticks')
        else:
            plt.style.use(self.config.currentStyle)

    def on_change_color_palette(self, evt, cmap=None, n_colors=16, return_colors=False, return_hex=False):
        if cmap is not None:
            palette_name = cmap
        else:
            if self.config.currentPalette in ['Spectral', 'RdPu']:
                palette_name = self.config.currentPalette
            else:
                palette_name = self.config.currentPalette.lower()

        new_colors = sns.color_palette(palette_name, n_colors)

        if not return_colors:
            for i in range(n_colors):
                self.config.customColors[i] = convertRGB1to255(new_colors[i])
        else:
            if return_hex:
                new_colors_hex = []
                for new_color in new_colors:
                    new_colors_hex.append(convertRGB1toHEX(new_color))
                return new_colors_hex
            else:
                return new_colors

    def on_get_colors_from_colormap(self, n_colors):
        colorlist = sns.color_palette(self.config.currentCmap, n_colors)
        return colorlist

    def get_colorList(self, count):
        colorList = sns.color_palette('cubehelix', count)
        colorList_return = []
        for color in colorList:
            colorList_return.append(convertRGB1to255(color))

        return colorList_return

    def on_clear_plot(self, evt, plot=None, **kwargs):
        """
        Clear selected plot
        """

        eventID = None
        if evt is not None:
            eventID = evt.GetId()

        if plot == 'MS' or eventID == ID_clearPlot_MS:
            plot = self.plot1
        elif plot == 'RT' or eventID == ID_clearPlot_RT:
            plot = self.plotRT
        elif plot == 'RT_MS' or eventID == ID_clearPlot_RT_MS:
            plot = self.plot_RT_MS
        elif plot == '1D' or eventID == ID_clearPlot_1D:
            plot = self.plot1D
        elif plot == '1D_MS' or eventID == ID_clearPlot_1D_MS:
            plot = self.plot_DT_MS
        elif plot == '2D' or eventID == ID_clearPlot_2D:
            plot = self.plot2D
        elif plot == 'DT/MS' or eventID == ID_clearPlot_MZDT:
            plot = self.plot_DT_vs_MS
        elif plot == '3D' or eventID == ID_clearPlot_3D:
            plot = self.plot3D
        elif plot == 'RMSF' or eventID == ID_clearPlot_RMSF:
            plot = self.plot_RMSF
        elif plot == 'Overlay' or eventID == ID_clearPlot_Overlay:
            plot = self.plot_overlay
        elif plot == 'Matrix' or eventID == ID_clearPlot_Matrix:
            plot = self.plotCompare
        elif plot == 'Waterall' or eventID == ID_clearPlot_Waterfall:
            plot = self.plot_waterfall
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
        elif plot is None and 'plot_obj' in kwargs:
            plot = kwargs.pop('plot_obj')

        try:
            plot.clearPlot()
        except Exception:
            for p in plot:
                p.clearPlot()

        self.presenter.onThreading(evt, ('Cleared plot area', 4), action='updateStatusbar')

    def on_clear_all_plots(self, evt=None):

        # Delete all plots
        plotList = [
            self.plot1, self.plotRT, self.plot_RMSF, self.plot1D,
            self.plotCompare, self.plot2D, self.plot3D, self.plot_overlay,
            self.plot_waterfall, self.topPlotMS, self.bottomPlot1DT, self.plot_DT_vs_MS,
            self.plotUnidec_MS, self.plotUnidec_mzGrid,
            self.plotUnidec_mwDistribution, self.plotUnidec_mwVsZ,
            self.plotUnidec_individualPeaks, self.plotUnidec_barChart,
            self.plotUnidec_chargeDistribution, self.plotOther,
            self.plot_RT_MS, self.plot_DT_MS,
        ]

        for plot in plotList:
            plot.clearPlot()
            plot.repaint()
        # Message
        args = ('Cleared all plots', 4)
        self.presenter.onThreading(None, args, action='updateStatusbar')

    def on_clear_unidec(self, evt=None, which='all'):

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

    def on_clear_patches(self, plot='MS', repaint=False, **kwargs):

        if plot == 'MS':
            self.plot1.plot_remove_patches()
            if repaint:
                self.plot1.repaint()

        elif plot == 'CalibrationMS':
            self.topPlotMS.plot_remove_patches()
            if repaint:
                self.topPlotMS.repaint()

        elif plot == 'RT':
            self.plotRT.plot_remove_patches()
            if repaint:
                self.plotRT.repaint()

        elif plot is None and 'plot_obj' in kwargs:
            plot_obj = kwargs.get('plot_obj')
            plot_obj.plot_remove_patches()
            if repaint:
                plot_obj.repaint()

    def plot_repaint(self, plot_window='MS'):
        if plot_window == 'MS':
            self.plot1.repaint()

    def plot_remove_patches_with_labels(
        self, label, plot_window='2D',
        refresh=False,
    ):
        if plot_window == 'MS':
            self.plot1.plot_remove_patch_with_label(label)

            if refresh:
                self.plot1.repaint()

    def on_plot_patches(
        self, xmin, ymin, width, height, color='r', alpha=0.5, label='',
        plot='MS', repaint=False, **kwargs
    ):

        if plot is None and 'plot_obj' in kwargs:
            plot_obj = kwargs.get('plot_obj')
        else:
            plot_obj = self.get_plot_from_name(plot)

        plot_obj.plot_add_patch(
            xmin, ymin, width, height, color=color,
            alpha=alpha, label=label,
        )
        if repaint:
            plot_obj.repaint()

    def on_clear_labels(self, plot='MS', **kwargs):
        if plot is None and 'plot_obj' in kwargs:
            plot_obj = kwargs.get('plot_obj')
        else:
            plot_obj = self.get_plot_from_name(plot)

        plot_obj.plot_remove_text_and_lines()

    def on_plot_labels(
        self, xpos, yval, label='', plot='MS', repaint=False,
        optimise_labels=False, **kwargs
    ):

        plt_kwargs = {
            'horizontalalignment': kwargs.pop('horizontal_alignment', 'center'),
            'verticalalignment': kwargs.pop('vertical_alignment', 'center'),
            'check_yscale': kwargs.pop('check_yscale', False),
            'butterfly_plot': kwargs.pop('butterfly_plot', False),
            'fontweight': kwargs.pop('font_weight', 'normal'),
            'fontsize': kwargs.pop('font_size', 'medium'), }

        if plot is None and 'plot_obj' in kwargs:
            plot_obj = kwargs.get('plot_obj')
        else:
            plot_obj = self.get_plot_from_name(plot)

        if plot == 'MS':
            plot_obj.plot_add_text(
                xpos, yval, label,
                yoffset=kwargs.get('yoffset', 0.0),
                **plt_kwargs
            )
        elif plot == 'CalibrationMS':
            plot_obj.plot_add_text(xpos, yval, label, **plt_kwargs)

        elif plot is None and 'plot_obj' in kwargs:
            plot_obj.plot_add_text(xpos, yval, label, **plt_kwargs)

        if optimise_labels:
            plot_obj._fix_label_positions()

        if not repaint:
            return

        self.plot1.repaint()

    def on_plot_markers(
        self, xvals, yvals, color='b', marker='o',
        size=5, plot='MS', repaint=True, **kwargs
    ):
        if plot == 'MS':
            self.plot1.plot_add_markers(
                xvals=xvals,
                yvals=yvals,
                color=color,
                marker=marker,
                size=size,
                test_yvals=True,
            )
            if not repaint:
                return
            else:
                self.plot1.repaint()

        elif plot == 'RT':
            self.plotRT.plot_add_markers(
                xvals=xvals,
                yvals=yvals,
                color=color,
                marker=marker,
                size=size,
            )
            self.plotRT.repaint()
        elif plot == 'CalibrationMS':
            self.topPlotMS.plot_add_markers(
                xval=xvals,
                yval=yvals,
                color=color,
                marker=marker,
                size=size,
            )
            self.topPlotMS.repaint()
        elif plot == 'CalibrationDT':
            self.bottomPlot1DT.plot_add_markers(
                xvals=xvals,
                yvals=yvals,
                color=color,
                marker=marker,
                size=size,
                testMax='yvals',
            )
            self.bottomPlot1DT.repaint()

    def on_clear_markers(self, plot='MS', repaint=False, **kwargs):

        if plot is None and 'plot_obj' in kwargs:
            plot_obj = kwargs.get('plot_obj')
        else:
            plot_obj = self.get_plot_from_name(plot)

        plot_obj.plot_remove_markers()

        if repaint:
            plot_obj.repaint()

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
        if kwargs['color_scheme'] == 'Colormap':
            colorlist = sns.color_palette(kwargs['colormap'], n_count)
        elif kwargs['color_scheme'] == 'Color palette':
            if kwargs['palette'] not in ['Spectral', 'RdPu']:
                kwargs['palette'] = kwargs['palette'].lower()
            colorlist = sns.color_palette(kwargs['palette'], n_count)
        elif kwargs['color_scheme'] == 'Same color':
            colorlist = [kwargs['line_color']] * n_count
        elif kwargs['color_scheme'] == 'Random':
            colorlist = []
            for __ in range(n_count):
                colorlist.append(randomColorGenerator())

        return colorlist

    def _on_change_unidec_page(self, page_id, **kwargs):
        if self.config.unidec_plot_panel_view == 'Tabbed view' and kwargs.get('set_page', False):
            try:
                self.unidec_notebook.SetSelection(page_id)
            except Exception:
                pass

    def on_plot_charge_states(self, position, charges, plot='UniDec_peaks', **kwargs):

        if plot is None and 'plot_obj' in kwargs:
            plot_obj = kwargs.get('plot_obj')
        else:
            plot_obj = self.get_plot_from_name(plot)
            self._on_change_unidec_page(4, **kwargs)

        plot_obj.plot_remove_text_and_lines()
        for position, charge in zip(position, charges):
            plot_obj.plot_add_text_and_lines(
                xpos=position,
                yval=0.9, label=charge,
                stick_to_intensity=True,
            )
        plot_obj.repaint()

#         # optimise label positions
#         if kwargs.get('optimise_positions', True):
#             plot_obj._fix_label_positions()

        plot_obj.repaint()

    def on_plot_unidec_ChargeDistribution(
        self, xvals=None, yvals=None, replot=None, xlimits=None,
        plot='UniDec_charge', **kwargs
    ):
        """
        Plot simple Mass spectrum before it is pre-processed
        @param unidec_eng_data (object):  reference to unidec engine data structure
        @param xlimits: unused
        """

        if plot is None and 'plot_obj' in kwargs:
            plot_obj = kwargs.get('plot_obj')
        else:
            plot_obj = self.get_plot_from_name(plot)
            self._on_change_unidec_page(6, **kwargs)

        if replot is not None:
            xvals = replot[:, 0]
            yvals = replot[:, 1]

        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType='1D')

        plot_obj.clearPlot()
        plot_obj.plot_1D(
            xvals=xvals,
            yvals=yvals,
            xlimits=xlimits,
            xlabel='Charge',
            ylabel='Intensity',
            testMax=None,
            axesSize=self.config._plotSettings['UniDec (Charge Distribution)']['axes_size'],
            plotType='ChargeDistribution',
            title='Charge State Distribution',
            allowWheel=False,
            **plt_kwargs
        )
        # Show the mass spectrum
        plot_obj.repaint()

    def on_plot_unidec_MS(self, unidec_eng_data=None, replot=None, xlimits=None, plot='UniDec_MS', **kwargs):
        """
        Plot simple Mass spectrum before it is pre-processed
        @param unidec_eng_data (object):  reference to unidec engine data structure
        @param xlimits: unused
        """

        if plot is None and 'plot_obj' in kwargs:
            plot_obj = kwargs.get('plot_obj')
        else:
            plot_obj = self.get_plot_from_name(plot)
            self._on_change_unidec_page(0, **kwargs)

        plt_kwargs = self._buildPlotParameters(plotType='1D')

        if unidec_eng_data is None and replot is not None:
            xvals = replot['xvals']
            yvals = replot['yvals']

        plot_obj.clearPlot()
        plot_obj.plot_1D(
            xvals=xvals, yvals=yvals,
            xlimits=xlimits, xlabel='m/z',
            ylabel='Intensity',
            axesSize=self.config._plotSettings['UniDec (MS)']['axes_size'],
            plotType='MS', title='MS',
            allowWheel=False,
            **plt_kwargs
        )
        # Show the mass spectrum
        plot_obj.repaint()

    def on_plot_unidec_MS_v_Fit(self, unidec_eng_data=None, replot=None, xlimits=None, plot='UniDec_MS', **kwargs):

        if plot is None and 'plot_obj' in kwargs:
            plot_obj = kwargs.get('plot_obj')
        else:
            plot_obj = self.get_plot_from_name(plot)
            self._on_change_unidec_page(0, **kwargs)

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

        plot_obj.clearPlot()
        plot_obj.plot_1D_overlay(
            xvals=xvals,
            yvals=yvals,
            labels=labels,
            colors=colors,
            xlimits=xlimits,
            xlabel='m/z',
            ylabel='Intensity',
            axesSize=self.config._plotSettings['UniDec (MS)']['axes_size'],
            plotType='MS', title='MS and UniDec Fit',
            allowWheel=False,
            **plt_kwargs
        )
        # Show the mass spectrum
        plot_obj.repaint()

    def on_plot_unidec_mzGrid(self, unidec_eng_data=None, replot=None, plot='UniDec_mz_v_charge', **kwargs):
        """
        Plot simple Mass spectrum before it is pre-processed
        """

        if plot is None and 'plot_obj' in kwargs:
            plot_obj = kwargs.get('plot_obj')
        else:
            plot_obj = self.get_plot_from_name(plot)
            self._on_change_unidec_page(1, **kwargs)

        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType='2D')
        plt_kwargs['contour_levels'] = self.config.unidec_plot_contour_levels
        plt_kwargs['colorbar'] = True

        if unidec_eng_data is None and replot is not None:
            grid = replot['grid']

        plot_obj.clearPlot()
        plot_obj.plot_2D_contour_unidec(
            data=grid,
            xlabel='m/z (Da)',
            ylabel='Charge',
            axesSize=self.config._plotSettings['UniDec (m/z vs Charge)']['axes_size'],
            plotType='2D',
            plotName='mzGrid',
            speedy=kwargs.get(
                'speedy',
                True,
            ),
            title='m/z vs Charge',
            allowWheel=False,
            **plt_kwargs
        )
        # Show the mass spectrum
        plot_obj.repaint()

    def on_plot_unidec_mwDistribution(self, unidec_eng_data=None, replot=None, xlimits=None, plot='UniDec_MW', **kwargs):
        """
        Plot simple Mass spectrum before it is pre-processed
        @param unidec_eng_data (object):  reference to unidec engine data structure
        @param xlimits: unused
        """

        if plot is None and 'plot_obj' in kwargs:
            plot_obj = kwargs.get('plot_obj')
        else:
            plot_obj = self.get_plot_from_name(plot)
            self._on_change_unidec_page(3, **kwargs)

        # Build kwargs
        plt1d_kwargs = self._buildPlotParameters(plotType='1D')
        unidec_kwargs = self._buildPlotParameters(plotType='UniDec')
        plt_kwargs = merge_two_dicts(plt1d_kwargs, unidec_kwargs)

        if unidec_eng_data is None and replot is not None:
            xvals = replot['xvals']
            yvals = replot['yvals']

        plot_obj.clearPlot()
        plot_obj.plot_1D(
            xvals=xvals,
            yvals=yvals,
            xlimits=xlimits,
            xlabel='Mass Distribution',
            ylabel='Intensity',
            axesSize=self.config._plotSettings['UniDec (MW)']['axes_size'],
            plotType='mwDistribution', testMax=None, testX=True,
            title='Zero-charge Mass Spectrum',
            allowWheel=False,
            **plt_kwargs
        )
        # Show the mass spectrum
        plot_obj.repaint()

    def on_plot_unidec_MW_add_markers(self, data, mw_data, plot='UniDec_MW', **kwargs):
        """Add markers to the MW plot to indicate found peaks"""

        if plot is None and 'plot_obj' in kwargs:
            plot_obj = kwargs.get('plot_obj')
        else:
            plot_obj = self.get_plot_from_name(plot)
            self._on_change_unidec_page(1, **kwargs)

        # remove all markers
        plot_obj.plot_remove_markers()

        # build plot parameters
        plt1d_kwargs = self._buildPlotParameters(plotType='1D')
        unidec_kwargs = self._buildPlotParameters(plotType='UniDec')
        plt_kwargs = merge_two_dicts(plt1d_kwargs, unidec_kwargs)

        # get legend text
        legend_text = data['legend_text']
        mw = np.transpose([
            mw_data['xvals'],
            mw_data['yvals'],
        ])

        num = 0
        for key in natsorted(list(data.keys())):
            if key.split(' ')[0] != 'MW:':
                continue
            if num >= plt_kwargs['maximum_shown_items']:
                continue
            num += 1

        # get color list
        colors = self._get_color_list(None, count=num, **unidec_kwargs)

        num = 0
        for key in natsorted(list(data.keys())):
            if key.split(' ')[0] != 'MW:':
                continue
            if num >= plt_kwargs['maximum_shown_items']:
                continue

            xval = float(key.split(' ')[1])
            yval = self.data_processing.get_peak_maximum(mw, xval=xval)
#             print(xval, yval)
            marker = data[key]['marker']
            color = colors[num]

            plot_obj.plot_add_markers(
                xval, yval,
                color=color, marker=marker,
                size=plt_kwargs['MW_marker_size'],
                label=key,
                test_xvals=True,
            )
            num += 1

        plot_obj.plot_1D_add_legend(legend_text, **plt_kwargs)
        plot_obj.repaint()

    def on_plot_unidec_individualPeaks(
        self, unidec_eng_data=None, replot=None, xlimits=None, plot='UniDec_peaks',
        **kwargs
    ):
        """
        Plot simple Mass spectrum before it is pre-processed
        @param unidec_eng_data (object):  reference to unidec engine data structure
        @param xlimits: unused
        """

        if plot is None and 'plot_obj' in kwargs:
            plot_obj = kwargs.get('plot_obj')
        else:
            plot_obj = self.get_plot_from_name(plot)
            self._on_change_unidec_page(4, **kwargs)

        # Build kwargs
        plt1d_kwargs = self._buildPlotParameters(plotType='1D')
        unidec_kwargs = self._buildPlotParameters(plotType='UniDec')
        plt_kwargs = merge_two_dicts(plt1d_kwargs, unidec_kwargs)

        if unidec_eng_data is None and replot is not None:
            xvals = replot['xvals']
            yvals = replot['yvals']

        # Plot MS
        plot_obj.clearPlot()
        plot_obj.plot_1D(
            xvals=xvals, yvals=yvals,
            xlimits=xlimits, xlabel='m/z',
            ylabel='Intensity',
            axesSize=self.config._plotSettings['UniDec (Isolated MS)']['axes_size'],
            plotType='pickedPeaks', label='Raw',
            allowWheel=False,
            **plt_kwargs
        )
        plot_obj.repaint()

        # add lines and markers
        self.on_plot_unidec_add_individual_lines_and_markers(replot=replot, plot=None, **kwargs)

    def on_plot_unidec_add_individual_lines_and_markers(
        self, unidec_eng_data=None, replot=None,
        plot='UniDec_peaks', **kwargs
    ):

        if plot is None and 'plot_obj' in kwargs:
            plot_obj = kwargs.get('plot_obj')
        else:
            plot_obj = self.get_plot_from_name(plot)
            self._on_change_unidec_page(4, **kwargs)

        # remove all markers/lines and reset y-axis zoom
        plot_obj.plot_remove_markers()
        plot_obj.plot_remove_lines('MW:')
        plot_obj.on_zoom_y_axis(0)

        # Build kwargs
        plt1d_kwargs = self._buildPlotParameters(plotType='1D')
        unidec_kwargs = self._buildPlotParameters(plotType='UniDec')
        plt_kwargs = merge_two_dicts(plt1d_kwargs, unidec_kwargs)

        if unidec_eng_data is None and replot is not None:
            legend_text = replot['legend_text']

        if kwargs.get('show_isolated_mw', False):
            legend_text = [[[0, 0, 0], 'Raw']]

        # get number of lines in the dataset
        num = 0
        for key in natsorted(list(replot.keys())):
            if key.split(' ')[0] != 'MW:':
                continue
            if num >= plt_kwargs['maximum_shown_items']:
                continue
            num += 1

        # get colorlist
        colors = self._get_color_list(None, count=num, **unidec_kwargs)

        # iteratively add lines
        num, mw_num = 0, 0
        for key in natsorted(list(replot.keys())):
            if not kwargs['show_markers'] and not kwargs['show_individual_lines']:
                break

            if key.split(' ')[0] != 'MW:':
                continue
            if num >= plt_kwargs['maximum_shown_items']:
                continue

            scatter_yvals = replot[key]['scatter_yvals']
            line_yvals = replot[key]['line_yvals']

            if kwargs.get('show_isolated_mw', False):
                if key != kwargs['mw_selection']:
                    mw_num += 1
                    continue
                else:
                    color = colors[mw_num]
                    legend_text.append([
                        color,
                        replot[key]['label'],
                    ])
                    # adjust offset so its closer to the MS plot
                    offset = np.min(replot[key]['line_yvals']) + self.config.unidec_charges_offset
                    line_yvals = line_yvals - offset
            else:
                color = colors[num]
                legend_text[num + 1][0] = color
            # plot markers
            if kwargs['show_markers']:
                plot_obj.plot_add_markers(
                    replot[key]['scatter_xvals'],
                    scatter_yvals,
                    color=color,  # colors[num],
                    marker=replot[key]['marker'],
                    size=plt_kwargs['isolated_marker_size'],
                    label=replot[key]['label'],
                )
            # plot lines
            if kwargs['show_individual_lines']:
                plot_obj.plot_1D_add(
                    replot[key]['line_xvals'],
                    line_yvals,
                    color=color,  # colors[num],
                    label=replot[key]['label'],
                    allowWheel=False,
                    plot_name='pickedPeaks',
                    update_extents=True,
                    setup_zoom=False,
                    **plt_kwargs
                )
            num += 1

        # modify legend
        if len(legend_text) - 1 > plt_kwargs['maximum_shown_items']:
            msg = 'Only showing {} out of {} items.'.format(plt_kwargs['maximum_shown_items'], len(legend_text) - 1) + \
                ' If you would like to see more go to Processing -> UniDec -> Max shown'
            logger.info(msg)

        legend_text = legend_text[:num + 1]
        # Add legend
        if len(legend_text) >= plt_kwargs['maximum_shown_items']:
            legend_text = legend_text[:plt_kwargs['maximum_shown_items']]

        plot_obj.plot_1D_add_legend(legend_text, **plt_kwargs)
        plot_obj.repaint()

    def on_plot_unidec_MW_v_Charge(self, unidec_eng_data=None, replot=None, plot='UniDec_mw_v_charge', **kwargs):
        """
        Plot simple Mass spectrum before it is pre-processed
        @param unidec_eng_data (object):  reference to unidec engine data structure
        """

        if plot is None and 'plot_obj' in kwargs:
            plot_obj = kwargs.get('plot_obj')
        else:
            plot_obj = self.get_plot_from_name(plot)
            self._on_change_unidec_page(2, **kwargs)

        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType='2D')
        plt_kwargs['contour_levels'] = self.config.unidec_plot_contour_levels
        plt_kwargs['colorbar'] = True

        if unidec_eng_data is None and replot is not None:
            xvals = replot['xvals']
            yvals = replot['yvals']
            zvals = replot['zvals']
        else:
            xvals = unidec_eng_data.massdat[:, 0]
            yvals = unidec_eng_data.ztab
            zvals = unidec_eng_data.massgrid

        # Check that cmap modifier is included
        cmapNorm = self.normalize_colormap(
            zvals,
            min=self.config.minCmap,
            mid=self.config.midCmap,
            max=self.config.maxCmap,
        )
        plt_kwargs['colormap_norm'] = cmapNorm

        plot_obj.clearPlot()
        plot_obj.plot_2D_contour_unidec(
            xvals=xvals, yvals=yvals, zvals=zvals, xlabel='Mass (Da)',
            ylabel='Charge', axesSize=self.config._plotSettings['UniDec (MW vs Charge)']['axes_size'],
            plotType='MS', plotName='mwGrid', testX=True, speedy=kwargs.get('speedy', True),
            title='Mass vs Charge', **plt_kwargs
        )
        # Show the mass spectrum
        plot_obj.repaint()

    def on_plot_unidec_barChart(self, unidec_eng_data=None, replot=None, show='height', plot='UniDec_bar', **kwargs):
        """
        Plot simple Mass spectrum before it is pre-processed
        @param unidec_eng_data (object):  reference to unidec engine data structure
        """

        if plot is None and 'plot_obj' in kwargs:
            plot_obj = kwargs.get('plot_obj')
        else:
            plot_obj = self.get_plot_from_name(plot)
            self._on_change_unidec_page(5, **kwargs)

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

            if len(xvals) > plt_kwargs['maximum_shown_items']:
                msg = 'Only showing {} out of {} items.'.format(plt_kwargs['maximum_shown_items'], len(xvals)) + \
                    ' If you would like to see more go to Processing -> UniDec -> Max shown'
                self.presenter.onThreading(None, (msg, 4, 7), action='updateStatusbar')

            if len(xvals) >= plt_kwargs['maximum_shown_items']:
                xvals = xvals[:plt_kwargs['maximum_shown_items']]
                yvals = yvals[:plt_kwargs['maximum_shown_items']]
                labels = labels[:plt_kwargs['maximum_shown_items']]
                colors = colors[:plt_kwargs['maximum_shown_items']]
                legend_text = legend_text[:plt_kwargs['maximum_shown_items']]
                markers = markers[:plt_kwargs['maximum_shown_items']]

        colors = self._get_color_list(colors, **unidec_kwargs)
        for i in range(len(legend_text)):
            legend_text[i][0] = colors[i]

        plot_obj.clearPlot()
        plot_obj.plot_1D_barplot(
            xvals, yvals, labels, colors,
            axesSize=self.config._plotSettings['UniDec (Barplot)']['axes_size'],
            title='Peak Intensities',
            ylabel='Intensity',
            plotType='Barchart',
            **plt_kwargs
        )

        if unidec_eng_data is None and replot is not None:
            if kwargs['show_markers']:
                for i in range(len(markers)):
                    if i >= plt_kwargs['maximum_shown_items']:
                        continue
                    plot_obj.plot_add_markers(
                        xvals[i], yvals[i],
                        color=colors[i],
                        marker=markers[i],
                        size=plt_kwargs['bar_marker_size'],
                    )

        # Add legend
        plot_obj.plot_1D_add_legend(legend_text, **plt_kwargs)
        plot_obj.repaint()

    def plot_1D_update(self, plotName='all', evt=None):

        plt_kwargs = self._buildPlotParameters(plotType='1D')

        if plotName in ['all', 'MS']:
            try:
                self.plot1.plot_1D_update(**plt_kwargs)
                self.plot1.repaint()
            except AttributeError:
                pass

        if plotName in ['all', 'RT']:
            try:
                self.plotRT.plot_1D_update(**plt_kwargs)
                self.plotRT.repaint()
            except AttributeError:
                pass

        if plotName in ['all', '1D']:
            try:
                self.plot1D.plot_1D_update(**plt_kwargs)
                self.plot1D.repaint()
            except AttributeError:
                pass

        if plotName in ['all', 'RMSF']:
            plt_kwargs = self._buildPlotParameters(plotType='2D')
            rmsd_kwargs = self._buildPlotParameters(plotType='RMSF')
            plt_kwargs = merge_two_dicts(plt_kwargs, rmsd_kwargs)
            try:
                self.plot_RMSF.plot_1D_update_rmsf(**plt_kwargs)
                self.plot_RMSF.repaint()
            except AttributeError:
                pass

    def on_plot_other_1D(
        self, msX=None, msY=None, xlabel='', ylabel='',
        xlimits=None, set_page=False, **kwargs
    ):

        if set_page:
            self._set_page(self.config.panelNames['Other'])
        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType='1D')
        plt_kwargs = merge_two_dicts(plt_kwargs, kwargs)
        # check limits
        try:
            if math.isnan(xlimits.get(0, msX[0])):
                xlimits[0] = msX[0]
            if math.isnan(xlimits.get(1, msX[-1])):
                xlimits[1] = msX[-1]
        except Exception:
            xlimits = [np.min(msX), np.max(msX)]

        try:
            if len(msX[0]) > 1:
                msX = msX[0]
                msY = msY[0]
        except TypeError:
            pass

        self.plotOther.clearPlot()
        self.plotOther.plot_1D(
            xvals=msX,
            yvals=msY,
            xlimits=xlimits,
            xlabel=xlabel, ylabel=ylabel,
            axesSize=self.config._plotSettings['Other (Line)']['axes_size'],
            plotType='MS',
            **plt_kwargs
        )
        self.plotOther.repaint()
        self.plotOther.plot_type = 'line'

    def on_plot_other_overlay(
        self, xvals, yvals, xlabel, ylabel, colors, labels,
        xlimits=None, set_page=False, **kwargs
    ):

        if set_page:
            self._set_page(self.config.panelNames['Other'])
        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType='1D')
        plt_kwargs = merge_two_dicts(plt_kwargs, kwargs)

        self.plotOther.clearPlot()
        self.plotOther.plot_1D_overlay(
            xvals=xvals,
            yvals=yvals,
            title='',
            xlabel=xlabel,
            ylabel=ylabel,
            labels=labels,
            colors=colors,
            xlimits=xlimits,
            zoom='box',
            axesSize=self.config._plotSettings['Other (Multi-line)']['axes_size'],
            plotName='1D',
            **plt_kwargs
        )
        self.plotOther.repaint()
        self.plotOther.plot_type = 'multi-line'

    def on_plot_other_waterfall(
        self, xvals, yvals, zvals, xlabel, ylabel, colors=[],
        set_page=False, **kwargs
    ):

        if set_page:
            self._set_page(self.config.panelNames['Other'])

        plt_kwargs = self._buildPlotParameters(plotType='1D')
        waterfall_kwargs = self._buildPlotParameters(plotType='waterfall')
        plt_kwargs = merge_two_dicts(plt_kwargs, waterfall_kwargs)
        if 'increment' in kwargs:
            plt_kwargs['increment'] = kwargs['increment']

        # reverse labels
        xlabel, ylabel = ylabel, xlabel

        self.plotOther.clearPlot()
        self.plotOther.plot_1D_waterfall(
            xvals=xvals, yvals=yvals,
            zvals=zvals, label='',
            xlabel=xlabel,
            ylabel=ylabel,
            colorList=colors,
            labels=kwargs.get('labels', []),
            axesSize=self.config._plotSettings['Other (Waterfall)']['axes_size'],
            plotName='1D',
            **plt_kwargs
        )

#         if ('add_legend' in kwargs and 'labels' in kwargs and
#             len(colors) == len(kwargs['labels'])):
#             if kwargs['add_legend']:
#                 legend_text = zip(colors, kwargs['labels'])
#                 self.plotOther.plot_1D_add_legend(legend_text, **plt_kwargs)

        self.plotOther.repaint()
        self.plotOther.plot_type = 'waterfall'

    def on_plot_other_scatter(
        self, xvals, yvals, zvals, xlabel, ylabel, colors, labels,
        xlimits=None, set_page=False, **kwargs
    ):

        if set_page:
            self._set_page(self.config.panelNames['Other'])

        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType='1D')
        plt_kwargs = merge_two_dicts(plt_kwargs, kwargs)

        self.plotOther.clearPlot()
        self.plotOther.plot_1D_scatter(
            xvals=xvals,
            yvals=yvals,
            zvals=zvals,
            title='',
            xlabel=xlabel,
            ylabel=ylabel,
            labels=labels,
            colors=colors,
            xlimits=xlimits,
            zoom='box',
            axesSize=self.config._plotSettings['Other (Scatter)']['axes_size'],
            plotName='1D',
            **plt_kwargs
        )
        self.plotOther.repaint()
        self.plotOther.plot_type = 'scatter'

    def on_plot_other_grid_1D(
        self, xvals, yvals, xlabel, ylabel, colors, labels,
        set_page=False, **kwargs
    ):

        if set_page:
            self._set_page(self.config.panelNames['Other'])

        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType='1D')
        plt_kwargs = merge_two_dicts(plt_kwargs, kwargs)

        self.plotOther.clearPlot()
        self.plotOther.plot_n_grid_1D_overlay(
            xvals=xvals,
            yvals=yvals,
            title='',
            xlabel=xlabel,
            ylabel=ylabel,
            labels=labels,
            colors=colors,
            zoom='box',
            axesSize=self.config._plotSettings['Other (Grid-1D)']['axes_size'],
            plotName='1D',
            **plt_kwargs
        )
        self.plotOther.repaint()
        self.plotOther.plot_type = 'grid-line'

    def on_plot_other_grid_scatter(
        self, xvals, yvals, xlabel, ylabel, colors, labels,
        set_page=False, **kwargs
    ):

        if set_page:
            self._set_page(self.config.panelNames['Other'])

        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType='1D')
        plt_kwargs = merge_two_dicts(plt_kwargs, kwargs)

        self.plotOther.clearPlot()
        self.plotOther.plot_n_grid_scatter(
            xvals=xvals,
            yvals=yvals,
            title='',
            xlabel=xlabel,
            ylabel=ylabel,
            labels=labels,
            colors=colors,
            zoom='box',
            axesSize=self.config._plotSettings['Other (Grid-1D)']['axes_size'],
            plotName='1D',
            **plt_kwargs
        )
        self.plotOther.repaint()
        self.plotOther.plot_type = 'grid-scatter'

    def on_plot_other_bars(
        self, xvals, yvals_min, yvals_max, xlabel, ylabel, colors,
        set_page=False, **kwargs
    ):

        if set_page:
            self._set_page(self.config.panelNames['Other'])

        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType='1D')
        plt_kwargs = merge_two_dicts(plt_kwargs, kwargs)

        self.plotOther.clearPlot()
        self.plotOther.plot_floating_barplot(
            xvals=xvals,
            yvals_min=yvals_min,
            yvals_max=yvals_max,
            itle='',
            xlabel=xlabel,
            ylabel=ylabel,
            colors=colors,
            zoom='box',
            axesSize=self.config._plotSettings['Other (Barplot)']['axes_size'],
            **plt_kwargs
        )
        self.plotOther.repaint()
        self.plotOther.plot_type = 'bars'

    def _on_check_plot_names(self, document_name, dataset_name, plot_window):
        """
        Check if document name and dataset name match that of the plotted window
        """
        plot = None
        if plot_window == 'MS':
            plot = self.plot1

        if plot is None:
            return False

        if plot.document_name is None or plot.dataset_name is None:
            return

        if plot.document_name != document_name:
            return False

        if plot.dataset_name != dataset_name:
            return False

        return True

    def on_add_centroid_MS_and_labels(
        self, msX, msY, labels, full_labels, xlimits=None,
        title='', butterfly_plot=False, set_page=False, **kwargs
    ):
        if set_page:
            self._set_page(self.config.panelNames['MS'])

        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType='1D')
        plt_kwargs['line_color'] = self.config.msms_line_color_labelled
        plt_kwargs['butterfly_plot'] = butterfly_plot

        plot_name = 'MS'
        plot_size = self.config._plotSettings['MS']['axes_size']
        if butterfly_plot:
            plot_name = 'compareMS'
            plot_size = self.config._plotSettings['MS (compare)']['axes_size']

        xylimits = self.plot1.get_xylimits()
        self.plot1.plot_1D_centroid(
            xvals=msX,
            yvals=msY,
            xlimits=xlimits,
            update_y_axis=False,
            xlabel='m/z', ylabel='Intensity', title=title,
            axesSize=plot_size,
            plot_name=plot_name,
            adding_on_top=True,
            **plt_kwargs
        )

        # add labels
        plt_label_kwargs = {
            'horizontalalignment': self.config.annotation_label_horz,
            'verticalalignment': self.config.annotation_label_vert,
            'check_yscale': True,
            'add_arrow_to_low_intensity': self.config.msms_add_arrows,
            'butterfly_plot': butterfly_plot,
            'fontweight': self.config.annotation_label_font_weight,
            'fontsize': self.config.annotation_label_font_size,
            'rotation': self.config.annotation_label_font_orientation,
        }

        for i in range(len(labels)):
            xval, yval, label, full_label = msX[i], msY[i], labels[i], full_labels[i]

            if not self.config.msms_show_neutral_loss:
                if 'H2O' in full_label or 'NH3' in full_label:
                    continue

            if self.config.msms_show_full_label:
                label = full_label

            self.plot1.plot_add_text(
                xpos=xval, yval=yval, label=label,
                yoffset=self.config.msms_label_y_offset,
                **plt_label_kwargs
            )

        if i == len(labels) - 1 and not butterfly_plot:
            self.plot1.set_xylimits(xylimits)

        self.plot1.repaint()

    def on_plot_centroid_MS(
        self, msX, msY, msXY=None, xlimits=None, title='', repaint=True,
        set_page=False, **kwargs
    ):
        if set_page:
            self._set_page(self.config.panelNames['MS'])

        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType='1D')
        plt_kwargs['line_color'] = self.config.msms_line_color_unlabelled

        self.plot1.clearPlot()
        self.plot1.plot_1D_centroid(
            xvals=msX,
            yvals=msY,
            xyvals=msXY,
            xlimits=xlimits,
            xlabel='m/z', ylabel='Intensity', title=title,
            axesSize=self.config._plotSettings['MS']['axes_size'],
            plotType='MS',
            **plt_kwargs
        )
        # Show the mass spectrum
        if repaint:
            self.plot1.repaint()

    def on_clear_MS_annotations(self):

        try:
            self.on_clear_labels(plot='MS')
        except Exception:
            pass
        try:
            self.on_clear_patches(plot='MS')
        except Exception:
            pass

    def on_update_plot_1D(self, xvals, yvals, plot, **kwargs):

        if plot is None and 'plot_obj' in kwargs:
            plot_obj = kwargs.get('plot_obj')
        else:
            plot_obj = self.get_plot_from_name(plot)

        plot_obj.plot_1D_update_data_only(xvals, yvals)
        plot_obj.repaint()

    def on_simple_plot_1D(self, xvals, yvals, **kwargs):
        plot = kwargs.pop('plot', None)

        if plot is None and 'plot_obj' in kwargs:
            plot_obj = kwargs.get('plot_obj')
        else:
            plot_obj = self.get_plot_from_name(plot)

        # get kwargs
        plt_kwargs = self._buildPlotParameters(plotType='1D')

        try:
            plot_obj.plot_1D_update_data_only(xvals, yvals)
        except Exception as err:
            print(err)

            plot_obj.clearPlot()
            plot_obj.plot_1D(
                xvals=xvals,
                yvals=yvals,
                xlabel=kwargs.pop('xlabel', ''),
                ylabel=kwargs.pop('ylabel', ''),
                #                 axesSize=self.config._plotSettings['DT']['axes_size'],
                plotType='1D',
                **plt_kwargs
            )
        # show the plot
        plot_obj.repaint()

    def on_plot_MS(
        self, msX=None, msY=None, xlimits=None, override=True, replot=False,
        full_repaint=False, set_page=False, show_in_window='MS', view_range=[], **kwargs
    ):

        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType='1D')

        panel = self.plot1
        window = self.config.panelNames['MS']
        if show_in_window == 'MS':
            panel = self.plot1
            window = self.config.panelNames['MS']
            plot_size_key = 'MS'
        elif show_in_window == 'RT':
            panel = self.plot_RT_MS
            window = self.config.panelNames['RT']
            plt_kwargs['prevent_extraction'] = True
            plot_size_key = 'MS (DT/RT)'
        elif show_in_window == '1D':
            panel = self.plot_DT_MS
            window = self.config.panelNames['1D']
            plt_kwargs['prevent_extraction'] = True
            plot_size_key = 'MS (DT/RT)'
        else:
            panel = kwargs.pop('plot_obj')
            window = None
            plt_kwargs['prevent_extraction'] = True
            plot_size_key = 'MS'

        # change page
        if set_page and window is not None:
            self._set_page(window)

        if replot:
            msX, msY, xlimits = self.presenter._get_replot_data('MS')
            if msX is None or msY is None:
                return

        # setup names
        if 'document' in kwargs:
            panel.document_name = kwargs['document']
            panel.dataset_name = kwargs['dataset']
        else:
            panel.document_name = None
            panel.dataset_name = None

        if not full_repaint:
            try:
                panel.plot_1D_update_data(msX, msY, 'm/z', 'Intensity', **plt_kwargs)
                if len(view_range):
                    self.on_zoom_1D_x_axis(
                        startX=view_range[0], endX=view_range[1],
                        repaint=False, plot='MS',
                    )
                panel.repaint()
                if override:
                    self.config.replotData['MS'] = {'xvals': msX, 'yvals': msY, 'xlimits': xlimits}
                return
            except Exception as err:
                logger.warning(err)

        # check limits
        try:
            if math.isnan(xlimits.get(0, msX[0])):
                xlimits[0] = msX[0]
            if math.isnan(xlimits.get(1, msX[-1])):
                xlimits[1] = msX[-1]
        except Exception:
            xlimits = [np.min(msX), np.max(msX)]

        panel.clearPlot()
        panel.plot_1D(
            xvals=msX,
            yvals=msY,
            xlimits=xlimits,
            xlabel='m/z', ylabel='Intensity',
            axesSize=self.config._plotSettings[plot_size_key]['axes_size'],
            plotType='MS',
            **plt_kwargs
        )
        # Show the mass spectrum
        panel.repaint()

        if override:
            self.config.replotData['MS'] = {'xvals': msX, 'yvals': msY, 'xlimits': xlimits}

    def on_plot_1D(
        self, dtX=None, dtY=None, xlabel=None, color=None, override=True,
        full_repaint=False, replot=False, e=None, set_page=False,
    ):

        # change page
        if set_page:
            self._set_page(self.config.panelNames['1D'])

        if replot:
            dtX, dtY, xlabel = self.presenter._get_replot_data('1D')
            if dtX is None or dtY is None or xlabel is None:
                return

        # get kwargs
        plt_kwargs = self._buildPlotParameters(plotType='1D')

        if not full_repaint:
            try:
                self.plot1D.plot_1D_update_data(dtX, dtY, xlabel, 'Intensity', **plt_kwargs)
                self.plot1D.repaint()
                if override:
                    self.config.replotData['1D'] = {'xvals': dtX, 'yvals': dtY, 'xlabel': xlabel}
                    return
            except Exception:
                pass

        self.plot1D.clearPlot()
        self.plot1D.plot_1D(
            xvals=dtX,
            yvals=dtY,
            xlabel=xlabel,
            ylabel='Intensity',
            axesSize=self.config._plotSettings['DT']['axes_size'],
            plotType='1D',
            **plt_kwargs
        )
        # show the plot
        self.plot1D.repaint()

        if override:
            self.config.replotData['1D'] = {'xvals': dtX, 'yvals': dtY, 'xlabel': xlabel}

    def on_plot_RT(
        self, rtX=None, rtY=None, xlabel=None, ylabel='Intensity',
        color=None, override=True, replot=False, full_repaint=False,
        e=None, set_page=False,
    ):

        # change page
        if set_page:
            self._set_page(self.config.panelNames['RT'])

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
                    self.config.replotData['RT'] = {'xvals': rtX, 'yvals': rtY, 'xlabel': xlabel}
                    return
            except Exception:
                pass

        self.plotRT.clearPlot()
        self.plotRT.plot_1D(
            xvals=rtX, yvals=rtY, xlabel=xlabel, ylabel=ylabel,
            axesSize=self.config._plotSettings['RT']['axes_size'],
            plotType='1D',
            **plt_kwargs
        )
        # Show the mass spectrum
        self.plotRT.repaint()

        if override:
            self.config.replotData['RT'] = {
                'xvals': rtX,
                'yvals': rtY,
                'xlabel': xlabel,
            }

    def plot_2D_update(self, plotName='all', evt=None):
        plt_kwargs = self._buildPlotParameters(plotType='2D')

        if plotName in ['all', '2D']:
            try:
                self.plot2D.plot_2D_update(**plt_kwargs)
                self.plot2D.repaint()
            except AttributeError:
                pass

        if plotName in ['all', 'UniDec']:

            try:
                self.plotUnidec_mzGrid.plot_2D_update(**plt_kwargs)
                self.plotUnidec_mzGrid.repaint()
            except AttributeError:
                pass

            try:
                self.plotUnidec_mwVsZ.plot_2D_update(**plt_kwargs)
                self.plotUnidec_mwVsZ.repaint()
            except AttributeError:
                pass

        if plotName in ['all', 'DT/MS']:
            try:
                self.plot_DT_vs_MS.plot_2D_update(**plt_kwargs)
                self.plot_DT_vs_MS.repaint()
            except AttributeError:
                pass

    def on_plot_2D_data(self, data=None, **kwargs):
        """
        This function plots IMMS data in relevant windows.
        Input format: zvals, xvals, xlabel, yvals, ylabel
        """
        if isempty(data[0]):
            raise MessageError(
                'Missing data',
                'Missing data - cannot plot 2D plot',
            )

        # Unpack data
        if len(data) == 5:
            zvals, xvals, xlabel, yvals, ylabel = data
        elif len(data) == 6:
            zvals, xvals, xlabel, yvals, ylabel, __ = data

        # Check and change colormap if necessary
        cmapNorm = self.normalize_colormap(
            zvals,
            min=self.config.minCmap,
            mid=self.config.midCmap,
            max=self.config.maxCmap,
        )

        # Plot data
        self.on_plot_2D(zvals, xvals, yvals, xlabel, ylabel, cmapNorm=cmapNorm)
        if self.config.waterfall:
            if len(xvals) > 500:
                msg = 'There are {} scans in this dataset'.format(len(xvals)) + \
                    ' (it could be slow to plot Waterfall plot...). Would you like to continue?'
                dlg = DialogBox(
                    exceptionTitle='Would you like to continue?',
                    exceptionMsg=msg,
                    type='Question',
                )
                if dlg == wx.ID_YES:
                    self.on_plot_waterfall(
                        yvals=xvals, xvals=yvals, zvals=zvals,
                        xlabel=xlabel, ylabel=ylabel,
                    )
        try:
            self.on_plot_3D(
                zvals=zvals, labelsX=xvals, labelsY=yvals,
                xlabel=xlabel, ylabel=ylabel, zlabel='Intensity',
            )
        except Exception:
            pass

    def on_plot_violin(self, data=None, set_page=False, **kwargs):

        # change page
        if set_page:
            self._set_page(self.config.panelNames['Waterfall'])

        # Unpack data
        if len(data) == 5:
            zvals, xvals, xlabel, yvals, ylabel = data
        elif len(data) == 6:
            zvals, xvals, xlabel, yvals, ylabel, __ = data

        plt_kwargs = self._buildPlotParameters(plotType='1D')
        violin_kwargs = self._buildPlotParameters(plotType='violin')
        plt_kwargs = merge_two_dicts(plt_kwargs, violin_kwargs)
        if 'increment' in kwargs:
            plt_kwargs['increment'] = kwargs['increment']

        self.plot_waterfall.clearPlot()
        try:
            if zvals.shape[1] < plt_kwargs['violin_nlimit']:
                self.plot_waterfall.plot_1D_violin(
                    xvals=yvals, yvals=xvals,
                    zvals=zvals, label='',
                    xlabel=xlabel,
                    ylabel=ylabel,
                    labels=kwargs.get('labels', []),
                    axesSize=self.config._plotSettings['Violin']['axes_size'],
                    orientation=self.config.violin_orientation,
                    plotName='1D',
                    **plt_kwargs
                )
            else:
                self.presenter.onThreading(
                    None, ('Selected item is too large to plot as violin. Plotting as waterfall instead.', 4, 10),
                    action='updateStatusbar',
                )
                # check if there are more than 500 elements
                if zvals.shape[1] > 500:
                    msg = 'There are {} scans in this dataset'.format(len(xvals)) + \
                        ' (this could be slow...). Would you like to continue?'
                    dlg = DialogBox(
                        exceptionTitle='Would you like to continue?',
                        exceptionMsg=msg,
                        type='Question',
                    )
                    if dlg == wx.ID_NO:
                        return
                # plot
                self.on_plot_waterfall(
                    yvals=xvals, xvals=yvals, zvals=zvals,
                    xlabel=xlabel, ylabel=ylabel,
                )
        except Exception:
            self.plot_waterfall.clearPlot()
            print('Failed to plot the violin plot...')

        # Show the mass spectrum
        self.plot_waterfall.repaint()

    def on_plot_2D(
        self, zvals=None, xvals=None, yvals=None, xlabel=None,
        ylabel=None, cmap=None, cmapNorm=None, plotType=None,
        override=True, replot=False, set_page=False,
    ):

        # change page
        if set_page:
            self._set_page(self.config.panelNames['2D'])

        # If the user would like to replot data, you can directly unpack it
        if replot:
            zvals, xvals, yvals, xlabel, ylabel = self.presenter._get_replot_data('2D')
            if zvals is None or xvals is None or yvals is None:
                return

        # Check if cmap should be overwritten
        if self.config.useCurrentCmap:
            cmap = self.config.currentCmap

        # Check that cmap modifier is included
        if cmapNorm is None and plotType != 'RMSD':
            cmapNorm = self.normalize_colormap(
                zvals,
                min=self.config.minCmap,
                mid=self.config.midCmap,
                max=self.config.maxCmap,
            )

        elif cmapNorm is None and plotType == 'RMSD':
            cmapNorm = self.normalize_colormap(
                zvals,
                min=-100, mid=0, max=100,
            )

        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType='2D')
        plt_kwargs['colormap'] = cmap
        plt_kwargs['colormap_norm'] = cmapNorm

        try:
            self.plot2D.plot_2D_update_data(
                xvals, yvals, xlabel, ylabel, zvals,
                **plt_kwargs
            )
            self.plot2D.repaint()
            if override:
                self.config.replotData['2D'] = {
                    'zvals': zvals, 'xvals': xvals,
                    'yvals': yvals, 'xlabels': xlabel,
                    'ylabels': ylabel, 'cmap': cmap,
                    'cmapNorm': cmapNorm,
                }
            return
        except Exception:
            pass

        # Plot 2D dataset
        self.plot2D.clearPlot()
        if self.config.plotType == 'Image':
            self.plot2D.plot_2D_surface(
                zvals, xvals, yvals, xlabel, ylabel,
                axesSize=self.config._plotSettings['2D']['axes_size'],
                plotName='2D',
                **plt_kwargs
            )

        elif self.config.plotType == 'Contour':
            self.plot2D.plot_2D_contour(
                zvals, xvals, yvals, xlabel, ylabel,
                axesSize=self.config._plotSettings['2D']['axes_size'],
                plotName='2D',
                **plt_kwargs
            )

        self.plot2D.repaint()
        if override:
            self.config.replotData['2D'] = {
                'zvals': zvals, 'xvals': xvals,
                'yvals': yvals, 'xlabels': xlabel,
                'ylabels': ylabel, 'cmap': cmap,
                'cmapNorm': cmapNorm,
            }

        # update plot data
        self.presenter.view._onUpdatePlotData(plot_type='2D')

    def on_plot_MSDT(
        self, zvals=None, xvals=None, yvals=None, xlabel=None, ylabel=None,
        cmap=None, cmapNorm=None, plotType=None, override=True, replot=False,
        set_page=False, **kwargs
    ):

        # change page
        if set_page:
            self._set_page(self.config.panelNames['MZDT'])

        # If the user would like to replot data, you can directly unpack it
        if replot:
            zvals, xvals, yvals, xlabel, ylabel = self.presenter._get_replot_data('DT/MS')
            if zvals is None or xvals is None or yvals is None:
                return

        # Check if cmap should be overwritten
        if self.config.useCurrentCmap or cmap is None:
            cmap = self.config.currentCmap

        # Check that cmap modifier is included
        if cmapNorm is None:
            cmapNorm = self.normalize_colormap(
                zvals,
                min=self.config.minCmap,
                mid=self.config.midCmap,
                max=self.config.maxCmap,
            )

        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType='2D')
        plt_kwargs['colormap'] = cmap
        plt_kwargs['colormap_norm'] = cmapNorm
        plt_kwargs = merge_two_dicts(plt_kwargs, kwargs)

        try:
            self.plot_DT_vs_MS.plot_2D_update_data(
                xvals, yvals, xlabel, ylabel, zvals,
                **plt_kwargs
            )
            self.plot_DT_vs_MS.repaint()
            if override:
                self.config.replotData['DT/MS'] = {
                    'zvals': zvals, 'xvals': xvals,
                    'yvals': yvals, 'xlabels': xlabel,
                    'ylabels': ylabel, 'cmap': cmap,
                    'cmapNorm': cmapNorm,
                }
            return
        except Exception:
            pass

        # Plot 2D dataset
        self.plot_DT_vs_MS.clearPlot()
        if self.config.plotType == 'Image':
            self.plot_DT_vs_MS.plot_2D_surface(
                zvals, xvals, yvals, xlabel, ylabel,
                axesSize=self.config._plotSettings['DT/MS']['axes_size'],
                plotName='MSDT',
                **plt_kwargs
            )

        elif self.config.plotType == 'Contour':
            self.plot_DT_vs_MS.plot_2D_contour(
                zvals, xvals, yvals, xlabel, ylabel,
                axesSize=self.config._plotSettings['DT/MS']['axes_size'],
                plotName='MSDT',
                **plt_kwargs
            )

        # Show the mass spectrum
        self.plot_DT_vs_MS.repaint()

        # since we always sub-sample this dataset, it is makes sense to keep track of the full dataset before it was
        # subsampled - this way, when we replot data it will always use the full information
        if kwargs.get('full_data', False):
            xvals = kwargs['full_data'].pop('xvals', xvals)
            zvals = kwargs['full_data'].pop('zvals', zvals)

        if override:
            self.config.replotData['DT/MS'] = {
                'zvals': zvals, 'xvals': xvals,
                'yvals': yvals, 'xlabels': xlabel,
                'ylabels': ylabel, 'cmap': cmap,
                'cmapNorm': cmapNorm,
            }
        # update plot data
        self.presenter.view._onUpdatePlotData(plot_type='DT/MS')

    def on_plot_3D(
        self, zvals=None, labelsX=None, labelsY=None,
        xlabel='', ylabel='', zlabel='Intensity', cmap='inferno',
        cmapNorm=None, replot=False, set_page=False,
    ):

        # change page
        if set_page:
            self._set_page(self.config.panelNames['3D'])

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
        if cmapNorm is None:
            cmapNorm = self.normalize_colormap(
                zvals,
                min=self.config.minCmap,
                mid=self.config.midCmap,
                max=self.config.maxCmap,
            )
        # add to kwargs
        plt_kwargs['colormap'] = cmap
        plt_kwargs['colormap_norm'] = cmapNorm

        self.plot3D.clearPlot()
        if self.config.plotType_3D == 'Surface':
            self.plot3D.plot_3D_surface(
                xvals=labelsX,
                yvals=labelsY,
                zvals=zvals,
                title='',
                xlabel=xlabel,
                ylabel=ylabel,
                zlabel=zlabel,
                axesSize=self.config._plotSettings['3D']['axes_size'],
                **plt_kwargs
            )
        elif self.config.plotType_3D == 'Wireframe':
            self.plot3D.plot_3D_wireframe(
                xvals=labelsX,
                yvals=labelsY,
                zvals=zvals,
                title='',
                xlabel=xlabel,
                ylabel=ylabel,
                zlabel=zlabel,
                axesSize=self.config._plotSettings['3D']['axes_size'],
                **plt_kwargs
            )
        # Show the mass spectrum
        self.plot3D.repaint()

    def on_plot_waterfall(
        self, xvals, yvals, zvals, xlabel, ylabel, colors=[],
        set_page=False, **kwargs
    ):

        # change page
        if set_page:
            self._set_page(self.config.panelNames['Waterfall'])

        plt_kwargs = self._buildPlotParameters(plotType='1D')
        waterfall_kwargs = self._buildPlotParameters(plotType='waterfall')
        plt_kwargs = merge_two_dicts(plt_kwargs, waterfall_kwargs)
        if 'increment' in kwargs:
            plt_kwargs['increment'] = kwargs['increment']

        self.plot_waterfall.clearPlot()
        self.plot_waterfall.plot_1D_waterfall(
            xvals=xvals, yvals=yvals,
            zvals=zvals, label='',
            xlabel=xlabel,
            ylabel=ylabel,
            colorList=colors,
            labels=kwargs.get('labels', []),
            axesSize=self.config._plotSettings['Waterfall']['axes_size'],
            plotName='1D',
            **plt_kwargs
        )

        if (
            'add_legend' in kwargs and 'labels' in kwargs and
            len(colors) == len(kwargs['labels'])
        ):
            if kwargs['add_legend']:
                legend_text = list(zip(colors, kwargs['labels']))
                self.plot_waterfall.plot_1D_add_legend(legend_text, **plt_kwargs)

        # Show the mass spectrum
        self.plot_waterfall.repaint()

    def plot_1D_waterfall_update(self, which='other'):
        plt_kwargs = self._buildPlotParameters(plotType='1D')

        if self.currentPage == 'Other':
            plot_name = self.plotOther
        else:
            plot_name = self.plot_waterfall

        if self.plot_waterfall.plot_name != 'Violin':
            extra_kwargs = self._buildPlotParameters(plotType='waterfall')
        else:
            extra_kwargs = self._buildPlotParameters(plotType='violin')
            if which in ['data', 'label']:
                return
        plt_kwargs = merge_two_dicts(plt_kwargs, extra_kwargs)

        plot_name.plot_1D_waterfall_update(which=which, **plt_kwargs)
        plot_name.repaint()

    def on_plot_waterfall_overlay(
        self, xvals, yvals, zvals, colors, xlabel, ylabel,
        labels=None, set_page=False, **kwargs
    ):

        # change page
        if set_page:
            self._set_page(self.config.panelNames['Waterfall'])

        plt_kwargs = self._buildPlotParameters(plotType='1D')
        waterfall_kwargs = self._buildPlotParameters(plotType='waterfall')
        plt_kwargs = merge_two_dicts(plt_kwargs, waterfall_kwargs)
        if 'increment' in kwargs:
            plt_kwargs['increment'] = kwargs['increment']

        self.plot_waterfall.clearPlot()
        self.plot_waterfall.plot_1D_waterfall_overlay(
            xvals=xvals, yvals=yvals,
            zvals=zvals, label='',
            xlabel=xlabel,
            ylabel=ylabel,
            colorList=colors,
            labels=labels,
            axesSize=self.config._plotSettings['Waterfall']['axes_size'],
            plotName='1D',
            **plt_kwargs
        )

        if (
            'add_legend' in kwargs and 'labels' in kwargs and
            len(colors) == len(kwargs['labels'])
        ):
            if kwargs['add_legend']:
                legend_text = list(zip(colors, kwargs['labels']))
                self.plot_waterfall.plot_1D_add_legend(legend_text, **plt_kwargs)

        self.plot_waterfall.repaint()

    def on_plot_overlay_RT(
        self, xvals, yvals, xlabel, colors, labels, xlimits, style=None,
        set_page=False,
    ):

        # change page
        if set_page:
            self._set_page(self.config.panelNames['RT'])

        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType='1D')
        print(colors)
        self.plotRT.clearPlot()
        self.plotRT.plot_1D_overlay(
            xvals=xvals, yvals=yvals,
            title='', xlabel=xlabel,
            ylabel='Intensity',
            labels=labels,
            colors=colors,
            xlimits=xlimits,
            zoom='box',
            axesSize=self.config._plotSettings['RT']['axes_size'],
            plotName='1D',
            **plt_kwargs
        )
        self.plotRT.repaint()

    def on_plot_overlay_DT(
        self, xvals, yvals, xlabel, colors, labels, xlimits, style=None,
        set_page=False,
    ):

        # change page
        if set_page:
            self._set_page(self.config.panelNames['1D'])

        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType='1D')

        self.plot1D.clearPlot()
        self.plot1D.plot_1D_overlay(
            xvals=xvals, yvals=yvals,
            title='', xlabel=xlabel,
            ylabel='Intensity', labels=labels,
            colors=colors, xlimits=xlimits,
            zoom='box',
            axesSize=self.config._plotSettings['DT']['axes_size'],
            plotName='1D',
            **plt_kwargs
        )
        self.plot1D.repaint()

    def on_plot_overlay_2D(
        self, zvalsIon1, zvalsIon2, cmapIon1, cmapIon2,
        alphaIon1, alphaIon2, xvals, yvals, xlabel, ylabel,
        flag=None, plotName='2D', set_page=False,
    ):
        """
        Plot an overlay of *2* ions
        """

        # change page
        if set_page:
            self._set_page(self.config.panelNames['Overlay'])

        plt_kwargs = self._buildPlotParameters(plotType='2D')
        self.plot_overlay.clearPlot()
        self.plot_overlay.plot_2D_overlay(
            zvalsIon1=zvalsIon1,
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
            **plt_kwargs
        )

        self.plot_overlay.repaint()

    def on_plot_rgb(
        self, zvals=None, xvals=None, yvals=None, xlabel=None,
        ylabel=None, legend_text=None, set_page=False,
    ):

        # change page
        if set_page:
            self._set_page(self.config.panelNames['2D'])

        plt_kwargs = self._buildPlotParameters(plotType='2D')

        self.plot2D.clearPlot()
        self.plot2D.plot_2D_rgb(
            zvals, xvals, yvals, xlabel, ylabel,
            axesSize=self.config._plotSettings['2D']['axes_size'],
            legend_text=legend_text,
            **plt_kwargs
        )
        self.plot2D.repaint()

    def on_plot_RMSDF(
        self, yvalsRMSF, zvals, xvals=None, yvals=None, xlabelRMSD=None,
        ylabelRMSD=None, ylabelRMSF=None, color='blue', cmapNorm=None,
        cmap='inferno', plotType=None, override=True, replot=False,
        set_page=False,
    ):
        """
        Plot RMSD and RMSF plots together in panel RMSD
        """

        # change page
        if set_page:
            self._set_page(self.config.panelNames['RMSF'])

        plt_kwargs = self._buildPlotParameters(plotType='2D')
        rmsd_kwargs = self._buildPlotParameters(plotType='RMSF')
        plt_kwargs = merge_two_dicts(plt_kwargs, rmsd_kwargs)

        # If the user would like to replot data, you can directly unpack it
        if replot:
            zvals, xvals, yvals, xlabelRMSD, ylabelRMSD, ylabelRMSF = self.presenter._get_replot_data('RMSF')
            if zvals is None or xvals is None or yvals is None:
                return

        # Update values
        # self.presenter.getXYlimits2D(xvals, yvals, zvals)

        if self.config.useCurrentCmap:
            cmap = self.config.currentCmap

        if cmapNorm is None and plotType == 'RMSD':
            cmapNorm = self.normalize_colormap(zvals, min=-100, mid=0, max=100)

        # update kwargs
        plt_kwargs['colormap'] = cmap
        plt_kwargs['colormap_norm'] = cmapNorm

        self.plot_RMSF.clearPlot()
        self.plot_RMSF.plot_1D_2D(
            yvalsRMSF=yvalsRMSF,
            zvals=zvals,
            labelsX=xvals,
            labelsY=yvals,
            xlabelRMSD=xlabelRMSD,
            ylabelRMSD=ylabelRMSD,
            ylabelRMSF=ylabelRMSF,
            label='', zoom='box',
            plotName='RMSF',
            **plt_kwargs
        )
        self.plot_RMSF.repaint()
        self.rmsdfFlag = False

        if override:
            self.config.replotData['RMSF'] = {
                'zvals': zvals, 'xvals': xvals, 'yvals': yvals,
                'xlabelRMSD': xlabelRMSD, 'ylabelRMSD': ylabelRMSD,
                'ylabelRMSF': ylabelRMSF,
                'cmapNorm': cmapNorm,
            }

        self.presenter.view._onUpdatePlotData(plot_type='RMSF')

    def on_plot_RMSD(
        self, zvals=None, xvals=None, yvals=None, xlabel=None,
        ylabel=None, cmap=None, cmapNorm=None, plotType=None,
        override=True, replot=False, set_page=False,
    ):

        # change page
        if set_page:
            self._set_page(self.config.panelNames['RMSF'])

        self.plot_RMSF.clearPlot()

        # If the user would like to replot data, you can directly unpack it
        if replot:
            zvals, xvals, yvals, xlabel, ylabel = self.presenter._get_replot_data('2D')
            if zvals is None or xvals is None or yvals is None:
                return

        # Update values
        # self.presenter.getXYlimits2D(xvals, yvals, zvals)

        # Check if cmap should be overwritten
        if self.config.useCurrentCmap:
            cmap = self.config.currentCmap

        # Check that cmap modifier is included
        if cmapNorm is None and plotType == 'RMSD':
            cmapNorm = self.normalize_colormap(zvals, min=-100, mid=0, max=100)

        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType='2D')
        plt_kwargs['colormap'] = cmap
        plt_kwargs['colormap_norm'] = cmapNorm

        # Plot 2D dataset
        if self.config.plotType == 'Image':
            self.plot_RMSF.plot_2D_surface(
                zvals, xvals, yvals, xlabel, ylabel,
                axesSize=self.config._plotSettings['2D']['axes_size'],
                plotName='RMSD',
                **plt_kwargs
            )
        elif self.config.plotType == 'Contour':
            self.plot_RMSF.plot_2D_contour(
                zvals, xvals, yvals, xlabel, ylabel,
                axesSize=self.config._plotSettings['2D']['axes_size'],
                plotName='RMSD',
                **plt_kwargs
            )

        # Show the mass spectrum
        self.plot_RMSF.repaint()

        if override:
            self.config.replotData['2D'] = {
                'zvals': zvals, 'xvals': xvals,
                'yvals': yvals, 'xlabels': xlabel,
                'ylabels': ylabel, 'cmap': cmap,
                'cmapNorm': cmapNorm,
            }

        # update plot data
        self.presenter.view._onUpdatePlotData(plot_type='2D')

    def on_plot_MS_DT_calibration(
        self, msX=None, msY=None, xlimits=None, dtX=None,
        dtY=None, color=None, xlabelDT='Drift time (bins)',
        plotType='both', set_page=False,
        view_range=[],
    ):  # onPlotMSDTCalibration

        # change page
        if set_page:
            self._set_page(self.config.panelNames['Calibration'])

        # MS plot
        if plotType == 'both' or plotType == 'MS':
            self.topPlotMS.clearPlot()
            # get kwargs
            plt_kwargs = self._buildPlotParameters(plotType='1D')
            self.topPlotMS.plot_1D(
                xvals=msX, yvals=msY, xlabel='m/z',
                ylabel='Intensity', xlimits=xlimits,
                axesSize=self.config._plotSettings['Calibration (MS)']['axes_size'],
                plotType='1D',
                **plt_kwargs
            )
            if len(view_range):
                self.on_zoom_1D_x_axis(
                    startX=view_range[0], endX=view_range[1],
                    repaint=False, plot='calibration_MS',
                )
            # Show the mass spectrum
            self.topPlotMS.repaint()

        if plotType == 'both' or plotType == '1DT':
            ylabel = 'Intensity'
            # 1DT plot
            self.bottomPlot1DT.clearPlot()
            # get kwargs
            plt_kwargs = self._buildPlotParameters(plotType='1D')
            self.bottomPlot1DT.plot_1D(
                xvals=dtX, yvals=dtY,
                xlabel=xlabelDT, ylabel=ylabel,
                axesSize=self.config._plotSettings['Calibration (DT)']['axes_size'],
                plotType='CalibrationDT',
                **plt_kwargs
            )
            self.bottomPlot1DT.repaint()

    def on_plot_DT_calibration(
        self, dtX=None, dtY=None, color=None,
        xlabel='Drift time (bins)', set_page=False,
    ):  # onPlot1DTCalibration

        # change page
        if set_page:
            self._set_page(self.config.panelNames['Calibration'])

        # Check yaxis labels
        ylabel = 'Intensity'
        # 1DT plot
        self.bottomPlot1DT.clearPlot()
        # get kwargs
        plt_kwargs = self._buildPlotParameters(plotType='1D')
        self.bottomPlot1DT.plot_1D(
            xvals=dtX, yvals=dtY, xlabel=xlabel, ylabel=ylabel,
            axesSize=self.config._plotSettings['Calibration (DT)']['axes_size'],
            plotType='1D',
            **plt_kwargs
        )
        self.bottomPlot1DT.repaint()

    def plot_2D_update_label(self):

        try:
            if self.plot_RMSF.plot_name == 'RMSD':
                zvals, xvals, yvals, xlabel, ylabel = self.presenter._get_replot_data('2D')
            elif self.plot_RMSF.plot_name == 'RMSF':
                zvals, xvals, yvals, xlabelRMSD, ylabelRMSD, ylabelRMSF = self.presenter._get_replot_data('RMSF')
            else:
                return

            plt_kwargs = self._buildPlotParameters(plotType='RMSF')
            rmsdXpos, rmsdYpos = self.presenter.onCalculateRMSDposition(xlist=xvals, ylist=yvals)

            plt_kwargs['rmsd_label_coordinates'] = [rmsdXpos, rmsdYpos]
            plt_kwargs['rmsd_label_color'] = self.config.rmsd_color

            self.plot_RMSF.plot_2D_update_label(**plt_kwargs)
            self.plot_RMSF.repaint()
        except Exception:
            pass

    def plot_2D_matrix_update_label(self):
        plt_kwargs = self._buildPlotParameters(plotType='RMSF')

        try:
            self.plot2D.plot_2D_matrix_update_label(**plt_kwargs)
            self.plot2D.repaint()
        except Exception:
            pass

    def on_plot_matrix(
        self, zvals=None, xylabels=None, cmap=None, override=True,
        replot=False, set_page=False,
    ):

        # change page
        if set_page:
            self._set_page(self.config.panelNames['Comparison'])

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
        self.plotCompare.plot_2D_matrix(
            zvals=zvals, xylabels=xylabels,
            xNames=None,
            axesSize=self.config._plotSettings['Comparison']['axes_size'],
            plotName='2D',
            **plt_kwargs
        )
        self.plotCompare.repaint()

        plt_kwargs = self._buildPlotParameters(plotType='3D')
        rmsd_kwargs = self._buildPlotParameters(plotType='RMSF')
        plt_kwargs = merge_two_dicts(plt_kwargs, rmsd_kwargs)
        plt_kwargs['colormap'] = cmap

        self.plot3D.clearPlot()
        self.plot3D.plot_3D_bar(
            xvals=None, yvals=None, xylabels=xylabels,
            zvals=zvals, title='', xlabel='', ylabel='',
            axesSize=self.config._plotSettings['3D']['axes_size'],
            **plt_kwargs
        )
        self.plot3D.repaint()

        if override:
            self.config.replotData['Matrix'] = {
                'zvals': zvals,
                'xylabels': xylabels,
                'cmap': cmap,
            }

    def on_plot_grid(
        self, zvals_1, zvals_2, zvals_cum, xvals, yvals, xlabel, ylabel,
        cmap_1, cmap_2, set_page=False, **kwargs
    ):

        if set_page:
            self._set_page(self.config.panelNames['Overlay'])

        plt_kwargs = self._buildPlotParameters(plotType='2D')
        rmsd_kwargs = self._buildPlotParameters(plotType='RMSD')
        plt_kwargs = merge_two_dicts(plt_kwargs, rmsd_kwargs)
        plt_kwargs['colormap_1'] = cmap_1
        plt_kwargs['colormap_2'] = cmap_2

        plt_kwargs['cmap_norm_1'] = self.normalize_colormap(
            zvals_1,
            min=self.config.minCmap,
            mid=self.config.midCmap,
            max=self.config.maxCmap,
        )
        plt_kwargs['cmap_norm_2'] = self.normalize_colormap(
            zvals_2,
            min=self.config.minCmap,
            mid=self.config.midCmap,
            max=self.config.maxCmap,
        )
        plt_kwargs['cmap_norm_cum'] = self.normalize_colormap(
            zvals_cum,
            min=-100, mid=0, max=100,
        )
        self.plot_overlay.clearPlot()
        self.plot_overlay.plot_grid_2D_overlay(
            zvals_1, zvals_2, zvals_cum, xvals, yvals,
            xlabel, ylabel,
            axesSize=self.config._plotSettings['Overlay (Grid)']['axes_size'],
            **plt_kwargs
        )
        self.plot_overlay.repaint()

    def on_plot_n_grid(
        self, n_zvals, cmap_list, title_list, xvals, yvals, xlabel,
        ylabel, set_page=False,
    ):

        if set_page:
            self._set_page(self.config.panelNames['Overlay'])

        plt_kwargs = self._buildPlotParameters(plotType='2D')
        self.plot_overlay.clearPlot()
        self.plot_overlay.plot_n_grid_2D_overlay(
            n_zvals, cmap_list, title_list,
            xvals, yvals, xlabel, ylabel,
            axesSize=self.config._plotSettings['Overlay (Grid)']['axes_size'],
            **plt_kwargs
        )
        self.plot_overlay.repaint()

    def plot_compare(
        self, msX=None, msX_1=None, msX_2=None, msY_1=None, msY_2=None,
        msY=None, xlimits=None, replot=False, override=True, set_page=True,
        plot='MS', **kwargs
    ):

        if plot is None and 'plot_obj' in kwargs:
            plot_obj = kwargs.get('plot_obj')
        else:
            plot_obj = self.get_plot_from_name(plot)

        if set_page:
            self._set_page(self.config.panelNames['MS'])

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
            legend = self.config.compare_massSpectrumParams['legend']
            subtract = self.config.compare_massSpectrumParams['subtract']

        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType='1D')

        plot_obj.clearPlot()
        if subtract:
            try:
                plot_obj.plot_1D(
                    xvals=msX, yvals=msY,
                    xlimits=xlimits,
                    zoom='box', title='', xlabel='m/z',
                    ylabel='Intensity', label='',
                    lineWidth=self.config.lineWidth_1D,
                    axesSize=self.config._plotSettings['MS']['axes_size'],
                    plotType='MS',
                    **plt_kwargs
                )
            except Exception:
                plot_obj.repaint()
            if override:
                self.config.replotData['compare_MS'] = {
                    'xvals': msX,
                    'yvals': msY,
                    'xlimits': xlimits,
                    'subtract': subtract,
                }
        else:
            try:
                plot_obj.plot_1D_compare(
                    xvals1=msX_1, xvals2=msX_2,
                    yvals1=msY_1, yvals2=msY_2,
                    xlimits=xlimits,
                    zoom='box', title='',
                    xlabel='m/z', ylabel='Intensity',
                    label=legend,
                    lineWidth=self.config.lineWidth_1D,
                    axesSize=self.config._plotSettings['MS (compare)']['axes_size'],
                    plotType='compare_MS',
                    **plt_kwargs
                )
            except Exception:
                plot_obj.repaint()
            if override:
                self.config.replotData['compare_MS'] = {
                    'xvals': msX,
                    'xvals1': msX_1,
                    'xvals2': msX_2,
                    'yvals1': msY_1,
                    'yvals2': msY_2,
                    'xlimits': xlimits,
                    'legend': legend,
                    'subtract': subtract,
                }
        # Show the mass spectrum
        plot_obj.repaint()

    def plot_compare_spectra(self, xvals_1, xvals_2, yvals_1, yvals_2, xlimits=None, plot='MS', **kwargs):

        if plot is None and 'plot_obj' in kwargs:
            plot_obj = kwargs.get('plot_obj')
        else:
            plot_obj = self.get_plot_from_name(plot)

        legend = self.config.compare_massSpectrumParams['legend']

        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType='1D')

        plt_kwargs['label_1'] = self.config.compare_massSpectrumParams['legend'][0]
        plt_kwargs['label_2'] = self.config.compare_massSpectrumParams['legend'][1]

        try:
            plot_obj.plot_1D_compare_update_data(
                xvals_1, xvals_2, yvals_1, yvals_2,
                **plt_kwargs
            )
        except AttributeError:
            plot_obj.clearPlot()
            plot_obj.plot_1D_compare(
                xvals1=xvals_1, xvals2=xvals_2,
                yvals1=yvals_1, yvals2=yvals_2,
                xlimits=xlimits,
                zoom='box', title='',
                xlabel='m/z', ylabel='Intensity',
                label=legend,
                lineWidth=self.config.lineWidth_1D,
                plotType='compare_MS',
                **plt_kwargs
            )
            # Show the mass spectrum
        plot_obj.repaint()

    def plot_1D_update_data_by_label(self, xvals, yvals, gid, label, plot, **kwargs):
        if plot is None and 'plot_obj' in kwargs:
            plot_obj = kwargs.get('plot_obj')
        else:
            plot_obj = self.get_plot_from_name(plot)

        plot_obj.plot_1D_update_data_by_label(xvals, yvals, gid, label)
        plot_obj.repaint()

    def plot_1D_update_style_by_label(self, gid, plot, **kwargs):
        if plot is None and 'plot_obj' in kwargs:
            plot_obj = kwargs.get('plot_obj')
        else:
            plot_obj = self.get_plot_from_name(plot)

        plot_obj.plot_1D_update_style_by_label(gid, **kwargs)
        plot_obj.repaint()

    def plot_colorbar_update(self, plot_window=''):
        plt_kwargs = self._buildPlotParameters(plotType='2D')
        if plot_window == '2D' or self.currentPage == '2D':
            self.plot2D.plot_2D_colorbar_update(**plt_kwargs)
            self.plot2D.repaint()
        elif plot_window == 'RMSD' or self.currentPage == 'RMSF':
            self.plot_RMSF.plot_2D_colorbar_update(**plt_kwargs)
            self.plot_RMSF.repaint()
        elif plot_window == 'Comparison' or self.currentPage == 'Comparison':
            self.plotCompare.plot_2D_colorbar_update(**plt_kwargs)
            self.plotCompare.repaint()
        elif plot_window == 'UniDec' or self.currentPage == 'UniDec':
            self.plotUnidec_mzGrid.plot_2D_colorbar_update(**plt_kwargs)
            self.plotUnidec_mzGrid.repaint()

            self.plotUnidec_mwVsZ.plot_2D_colorbar_update(**plt_kwargs)
            self.plotUnidec_mwVsZ.repaint()

    def plot_normalization_update(self, plot_window=''):
        plt_kwargs = self._buildPlotParameters(plotType='2D')

        if plot_window == '2D' or self.currentPage == '2D':
            self.plot2D.plot_2D_update_normalization(**plt_kwargs)
            self.plot2D.repaint()
        elif plot_window == 'Comparison' or self.currentPage == 'Comparison':
            self.plotCompare.plot_2D_colorbar_update(**plt_kwargs)
            self.plotCompare.repaint()
        elif plot_window == 'UniDec' or self.currentPage == 'UniDec':
            self.plotUnidec_mzGrid.plot_2D_update_normalization(**plt_kwargs)
            self.plotUnidec_mzGrid.repaint()

            self.plotUnidec_mwVsZ.plot_2D_update_normalization(**plt_kwargs)
            self.plotUnidec_mwVsZ.repaint()

    def on_add_legend(self, labels, colors, plot='RT'):
        plt_kwargs = self._buildPlotParameters(plotType='legend')

        if len(colors) == len(labels):
            legend_text = list(zip(colors, labels))

        if plot == 'RT':
            self.plotRT.plot_1D_add_legend(legend_text, **plt_kwargs)

    def on_clear_legend(self, plot, repaint=False):
        if plot == 'RT':
            self.plotRT.plot_remove_legend()

    def on_add_marker(
        self, xvals=None, yvals=None, color='b', marker='o',
        size=5, plot='MS', repaint=True,
        clear_first=False, **kwargs
    ):

        if plot is None and 'plot_obj' in kwargs:
            plot_obj = kwargs.get('plot_obj')
        else:
            plot_obj = self.get_plot_from_name(plot)

        if clear_first:
            plot_obj.plot_remove_markers()

        plot_obj.plot_add_markers(
            xvals=xvals,
            yvals=yvals,
            color=color,
            marker=marker,
            size=size,
            test_yvals=kwargs.pop('test_yvals', False),
            **kwargs
        )

        if repaint:
            plot_obj.repaint()

    def on_add_patch(
        self, x, y, width, height, color='r', alpha=0.5,
        repaint=False, plot='MS', **kwargs
    ):

        if plot is None and 'plot_obj' in kwargs:
            plot_obj = kwargs.get('plot_obj')
        else:
            plot_obj = self.get_plot_from_name(plot)

        plot_obj.plot_add_patch(
            x, y, width, height, color=color,
            alpha=alpha,
        )
        if repaint:
            plot_obj.repaint()

    def on_zoom_1D_x_axis(self, startX, endX, endY=None, set_page=False, plot='MS', repaint=True, **kwargs):

        if plot is None and 'plot_obj' in kwargs:
            plot_obj = kwargs.get('plot_obj')
        else:
            plot_obj = self.get_plot_from_name(plot)

        if set_page:
            self._set_page(self.config.panelNames['MS'])

        if endY is None:
            plot_obj.on_zoom_x_axis(startX, endX)
        else:
            plot_obj.on_zoom(startX, endX, endY)

        if repaint:
            plot_obj.repaint()

    def on_zoom_1D_xy_axis(self, startX, endX, startY, endY, set_page=False, plot='MS', repaint=True):

        if set_page:
            self._set_page(self.config.panelNames['MS'])

        if plot == 'MS':
            self.plot1.on_zoom_xy(startX, endX, startY, endY)

            if repaint:
                self.plot1.repaint()

    def addTextRMSD(self, x, y, text, rotation, color='k', plot='RMSD'):  # addTextRMSD

        if plot == 'RMSD':
            self.plot_RMSF.addText(
                x, y, text, rotation,
                color=self.config.rmsd_color,
                fontsize=self.config.rmsd_fontSize,
                weight=self.config.rmsd_fontWeight,
            )
            self.plot_RMSF.repaint()
        elif plot == 'RMSF':
            self.plot_RMSF.addText(
                x, y, text, rotation,
                color=self.config.rmsd_color,
                fontsize=self.config.rmsd_fontSize,
                weight=self.config.rmsd_fontWeight,
            )
            self.plot_RMSF.repaint()
        elif plot == 'Grid':
            self.plot_overlay.addText(
                x, y, text, rotation,
                color=self.config.rmsd_color,
                fontsize=self.config.rmsd_fontSize,
                weight=self.config.rmsd_fontWeight,
                plot=plot,
            )
            self.plot_overlay.repaint()

    def _buildPlotParameters(self, plotType=None, evt=None):
        add_frame_width = True
        if plotType == '1D':
            plt_kwargs = {
                'line_width': self.config.lineWidth_1D,
                'line_color': self.config.lineColour_1D,
                'line_style': self.config.lineStyle_1D,
                'shade_under': self.config.lineShadeUnder_1D,
                'shade_under_color': self.config.lineShadeUnderColour_1D,
                'shade_under_transparency': self.config.lineShadeUnderTransparency_1D,
                'line_color_1': self.config.lineColour_MS1,
                'line_color_2': self.config.lineColour_MS2,
                'line_transparency_1': self.config.lineTransparency_MS1,
                'line_transparency_2': self.config.lineTransparency_MS2,
                'line_style_1': self.config.lineStyle_MS1,
                'line_style_2': self.config.lineStyle_MS2,
                'inverse': self.config.compare_massSpectrumParams['inverse'],
                'tick_size': self.config.tickFontSize_1D,
                'tick_weight': self.config.tickFontWeight_1D,
                'label_size': self.config.labelFontSize_1D,
                'label_weight': self.config.labelFontWeight_1D,
                'title_size': self.config.titleFontSize_1D,
                'title_weight': self.config.titleFontWeight_1D,
                'frame_width': self.config.frameWidth_1D,
                'label_pad': self.config.labelPad_1D,
                'axis_onoff': self.config.axisOnOff_1D,
                'ticks_left': self.config.ticks_left_1D,
                'ticks_right': self.config.ticks_right_1D,
                'ticks_top': self.config.ticks_top_1D,
                'ticks_bottom': self.config.ticks_bottom_1D,
                'tickLabels_left': self.config.tickLabels_left_1D,
                'tickLabels_right': self.config.tickLabels_right_1D,
                'tickLabels_top': self.config.tickLabels_top_1D,
                'tickLabels_bottom': self.config.tickLabels_bottom_1D,
                'spines_left': self.config.spines_left_1D,
                'spines_right': self.config.spines_right_1D,
                'spines_top': self.config.spines_top_1D,
                'spines_bottom': self.config.spines_bottom_1D,
                'scatter_edge_color': self.config.markerEdgeColor_1D,
                'scatter_color': self.config.markerColor_1D,
                'scatter_size': self.config.markerSize_1D,
                'scatter_shape': self.config.markerShape_1D,
                'scatter_alpha': self.config.markerTransparency_1D,
                'legend': self.config.legend,
                'legend_transparency': self.config.legendAlpha,
                'legend_position': self.config.legendPosition,
                'legend_num_columns': self.config.legendColumns,
                'legend_font_size': self.config.legendFontSize,
                'legend_frame_on': self.config.legendFrame,
                'legend_fancy_box': self.config.legendFancyBox,
                'legend_marker_first': self.config.legendMarkerFirst,
                'legend_marker_size': self.config.legendMarkerSize,
                'legend_num_markers': self.config.legendNumberMarkers,
                'legend_line_width': self.config.legendLineWidth,
                'legend_patch_transparency': self.config.legendPatchAlpha,
                'bar_width': self.config.bar_width,
                'bar_alpha': self.config.bar_alpha,
                'bar_edgecolor': self.config.bar_edge_color,
                'bar_edgecolor_sameAsFill': self.config.bar_sameAsFill,
                'bar_linewidth': self.config.bar_lineWidth,
            }
        elif plotType == 'annotation':
            plt_kwargs = {
                'horizontal_alignment': self.config.annotation_label_horz,
                'vertical_alignment': self.config.annotation_label_vert,
                'font_size': self.config.annotation_label_font_size,
                'font_weight': self.config.annotation_label_font_weight,
            }
        elif plotType == 'legend':
            plt_kwargs = {
                'legend': self.config.legend,
                'legend_transparency': self.config.legendAlpha,
                'legend_position': self.config.legendPosition,
                'legend_num_columns': self.config.legendColumns,
                'legend_font_size': self.config.legendFontSize,
                'legend_frame_on': self.config.legendFrame,
                'legend_fancy_box': self.config.legendFancyBox,
                'legend_marker_first': self.config.legendMarkerFirst,
                'legend_marker_size': self.config.legendMarkerSize,
                'legend_num_markers': self.config.legendNumberMarkers,
                'legend_line_width': self.config.legendLineWidth,
                'legend_patch_transparency': self.config.legendPatchAlpha,
            }
        elif plotType == 'UniDec':
            plt_kwargs = {
                'bar_width': self.config.unidec_plot_bar_width,
                'bar_alpha': self.config.unidec_plot_bar_alpha,
                'bar_edgecolor': self.config.unidec_plot_bar_edge_color,
                'bar_edgecolor_sameAsFill': self.config.unidec_plot_bar_sameAsFill,
                'bar_linewidth': self.config.unidec_plot_bar_lineWidth,
                'bar_marker_size': self.config.unidec_plot_bar_markerSize,
                'fit_line_color': self.config.unidec_plot_fit_lineColor,
                'isolated_marker_size': self.config.unidec_plot_isolatedMS_markerSize,
                'MW_marker_size': self.config.unidec_plot_MW_markerSize,
                'MW_show_markers': self.config.unidec_plot_MW_showMarkers,
                'color_scheme': self.config.unidec_plot_color_scheme,
                'colormap': self.config.unidec_plot_colormap,
                'palette': self.config.unidec_plot_palette,
                'maximum_shown_items': self.config.unidec_maxShown_individualLines,
                'contour_levels': self.config.unidec_plot_contour_levels,
            }

        elif plotType == '2D':
            plt_kwargs = {
                'colorbar': self.config.colorbar,
                'colorbar_width': self.config.colorbarWidth,
                'colorbar_pad': self.config.colorbarPad,
                'colorbar_range': self.config.colorbarRange,
                'colorbar_min_points': self.config.colorbarMinPoints,
                'colorbar_position': self.config.colorbarPosition,
                'colorbar_label_size': self.config.colorbarLabelSize,
                'legend': self.config.legend,
                'legend_transparency': self.config.legendAlpha,
                'legend_position': self.config.legendPosition,
                'legend_num_columns': self.config.legendColumns,
                'legend_font_size': self.config.legendFontSize,
                'legend_frame_on': self.config.legendFrame,
                'legend_fancy_box': self.config.legendFancyBox,
                'legend_marker_first': self.config.legendMarkerFirst,
                'legend_marker_size': self.config.legendMarkerSize,
                'legend_num_markers': self.config.legendNumberMarkers,
                'legend_line_width': self.config.legendLineWidth,
                'legend_patch_transparency': self.config.legendPatchAlpha,
                'interpolation': self.config.interpolation,
                'frame_width': self.config.frameWidth_1D,
                'axis_onoff': self.config.axisOnOff_1D,
                'label_pad': self.config.labelPad_1D,
                'tick_size': self.config.tickFontSize_1D,
                'tick_weight': self.config.tickFontWeight_1D,
                'label_size': self.config.labelFontSize_1D,
                'label_weight': self.config.labelFontWeight_1D,
                'title_size': self.config.titleFontSize_1D,
                'title_weight': self.config.titleFontWeight_1D,
                'ticks_left': self.config.ticks_left_1D,
                'ticks_right': self.config.ticks_right_1D,
                'ticks_top': self.config.ticks_top_1D,
                'ticks_bottom': self.config.ticks_bottom_1D,
                'tickLabels_left': self.config.tickLabels_left_1D,
                'tickLabels_right': self.config.tickLabels_right_1D,
                'tickLabels_top': self.config.tickLabels_top_1D,
                'tickLabels_bottom': self.config.tickLabels_bottom_1D,
                'spines_left': self.config.spines_left_1D,
                'spines_right': self.config.spines_right_1D,
                'spines_top': self.config.spines_top_1D,
                'spines_bottom': self.config.spines_bottom_1D,
                'override_colormap': self.config.useCurrentCmap,
                'colormap': self.config.currentCmap,
                'colormap_min': self.config.minCmap,
                'colormap_mid': self.config.midCmap,
                'colormap_max': self.config.maxCmap,
            }
        elif plotType == '3D':
            plt_kwargs = {
                'label_pad': self.config.labelPad_1D,
                'tick_size': self.config.tickFontSize_1D,
                'tick_weight': self.config.tickFontWeight_1D,
                'label_size': self.config.labelFontSize_1D,
                'label_weight': self.config.labelFontWeight_1D,
                'title_size': self.config.titleFontSize_1D,
                'title_weight': self.config.titleFontWeight_1D,
                'scatter_edge_color': self.config.markerEdgeColor_3D,
                'scatter_color': self.config.markerColor_3D,
                'scatter_size': self.config.markerSize_3D,
                'scatter_shape': self.config.markerShape_3D,
                'scatter_alpha': self.config.markerTransparency_3D,
                'grid': self.config.showGrids_3D,
                'shade': self.config.shade_3D,
                'show_ticks': self.config.ticks_3D,
                'show_spines': self.config.spines_3D,
                'show_labels': self.config.labels_3D,
            }

        elif plotType in ['RMSD', 'RMSF']:
            plt_kwargs = {
                'axis_onoff_1D': self.config.axisOnOff_1D,
                'ticks_left_1D': self.config.ticks_left_1D,
                'ticks_right_1D': self.config.ticks_right_1D,
                'ticks_top_1D': self.config.ticks_top_1D,
                'ticks_bottom_1D': self.config.ticks_bottom_1D,
                'tickLabels_left_1D': self.config.tickLabels_left_1D,
                'tickLabels_right_1D': self.config.tickLabels_right_1D,
                'tickLabels_top_1D': self.config.tickLabels_top_1D,
                'tickLabels_bottom_1D': self.config.tickLabels_bottom_1D,
                'spines_left_1D': self.config.spines_left_1D,
                'spines_right_1D': self.config.spines_right_1D,
                'spines_top_1D': self.config.spines_top_1D,
                'spines_bottom_1D': self.config.spines_bottom_1D,
                'rmsd_label_position': self.config.rmsd_position,
                'rmsd_label_font_size': self.config.rmsd_fontSize,
                'rmsd_label_font_weight': self.config.rmsd_fontWeight,
                'rmsd_hspace': self.config.rmsd_hspace,
                'rmsd_line_color': self.config.rmsd_lineColour,
                'rmsd_line_transparency': self.config.rmsd_lineTransparency,
                'rmsd_line_style': self.config.rmsd_lineStyle,
                'rmsd_line_width': self.config.rmsd_lineWidth,
                'rmsd_underline_hatch': self.config.rmsd_lineHatch,
                'rmsd_underline_color': self.config.rmsd_underlineColor,
                'rmsd_underline_transparency': self.config.rmsd_underlineTransparency,
                'rmsd_matrix_rotX': self.config.rmsd_rotation_X,
                'rmsd_matrix_rotY': self.config.rmsd_rotation_Y,
                'rmsd_matrix_labels': self.config.rmsd_matrix_add_labels,
            }
        elif plotType in 'waterfall':
            plt_kwargs = {
                'increment': self.config.waterfall_increment,
                'offset': self.config.waterfall_offset,
                'line_width': self.config.waterfall_lineWidth,
                'line_style': self.config.waterfall_lineStyle,
                'reverse': self.config.waterfall_reverse,
                'use_colormap': self.config.waterfall_useColormap,
                'line_color': self.config.waterfall_color,
                'shade_color': self.config.waterfall_shade_under_color,
                'normalize': self.config.waterfall_normalize,
                'colormap': self.config.waterfall_colormap,
                'palette': self.config.currentPalette,
                'color_scheme': self.config.waterfall_color_value,
                'line_color_as_shade': self.config.waterfall_line_sameAsShade,
                'add_labels': self.config.waterfall_add_labels,
                'labels_frequency': self.config.waterfall_labels_frequency,
                'labels_x_offset': self.config.waterfall_labels_x_offset,
                'labels_y_offset': self.config.waterfall_labels_y_offset,
                'labels_font_size': self.config.waterfall_label_fontSize,
                'labels_font_weight': self.config.waterfall_label_fontWeight,
                'labels_format': self.config.waterfall_label_format,
                'shade_under': self.config.waterfall_shade_under,
                'shade_under_n_limit': self.config.waterfall_shade_under_nlimit,
                'shade_under_transparency': self.config.waterfall_shade_under_transparency,
                'legend': self.config.legend,
                'legend_transparency': self.config.legendAlpha,
                'legend_position': self.config.legendPosition,
                'legend_num_columns': self.config.legendColumns,
                'legend_font_size': self.config.legendFontSize,
                'legend_frame_on': self.config.legendFrame,
                'legend_fancy_box': self.config.legendFancyBox,
                'legend_marker_first': self.config.legendMarkerFirst,
                'legend_marker_size': self.config.legendMarkerSize,
                'legend_num_markers': self.config.legendNumberMarkers,
                'legend_line_width': self.config.legendLineWidth,
                'legend_patch_transparency': self.config.legendPatchAlpha,
            }
        elif plotType in ['violin']:
            plt_kwargs = {
                'min_percentage': self.config.violin_min_percentage,
                'spacing': self.config.violin_spacing,
                'line_width': self.config.violin_lineWidth,
                'line_style': self.config.violin_lineStyle,
                'line_color': self.config.violin_color,
                'shade_color': self.config.violin_shade_under_color,
                'normalize': self.config.violin_normalize,
                'colormap': self.config.violin_colormap,
                'palette': self.config.currentPalette,
                'color_scheme': self.config.violin_color_value,
                'line_color_as_shade': self.config.violin_line_sameAsShade,
                'labels_format': self.config.violin_label_format,
                'shade_under': self.config.violin_shade_under,
                'violin_nlimit': self.config.violin_nlimit,
                'shade_under_transparency': self.config.violin_shade_under_transparency,
                'labels_frequency': self.config.violin_labels_frequency,
            }
        elif plotType in ['arrow']:
            plt_kwargs = {
                'arrow_line_width': self.config.annotation_arrow_line_width,
                'arrow_line_style': self.config.annotation_arrow_line_style,
                'arrow_head_length': self.config.annotation_arrow_cap_length,
                'arrow_head_width': self.config.annotation_arrow_cap_width,
            }
            add_frame_width = False
        elif plotType == 'label':
            plt_kwargs = {
                'horizontalalignment': self.config.annotation_label_horz,
                'verticalalignment': self.config.annotation_label_vert,
                'fontweight': self.config.annotation_label_font_weight,
                'fontsize': self.config.annotation_label_font_size,
                'rotation': self.config.annotation_label_font_orientation,
            }
            add_frame_width = False

        if 'frame_width' not in plt_kwargs and add_frame_width:
            plt_kwargs['frame_width'] = self.config.frameWidth_1D

        # return kwargs
        return plt_kwargs

    def normalize_colormap(self, data, min=0, mid=50, max=100, cbarLimits=None):
        """
        This function alters the colormap intensities
        """
        # Check if cbarLimits have been adjusted
        if cbarLimits is not None and self.config.colorbar:
            maxValue = self.config.colorbarRange[1]
        else:
            maxValue = np.max(data)

        # Determine what are normalization values
        # Convert from % to number
        cmapMin = (maxValue * min) / 100
        cmapMid = (maxValue * mid) / 100
        cmapMax = (maxValue * max) / 100

        cmapNormalization = MidpointNormalize(
            midpoint=cmapMid,
            vmin=cmapMin,
            vmax=cmapMax,
            clip=False,
        )
        return cmapNormalization
