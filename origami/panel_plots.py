"""Plotting panel"""
# Standard library imports
import os
import math
import time
import logging

# Third-party imports
import wx
import numpy as np
import seaborn as sns
import matplotlib
import matplotlib.pyplot as plt
from pubsub import pub
from natsort import natsorted

# Local imports
import origami.processing.UniDec.utilities as unidec_utils
from origami.ids import ID_save1DImage
from origami.ids import ID_save2DImage
from origami.ids import ID_save3DImage
from origami.ids import ID_saveMSImage
from origami.ids import ID_saveRTImage
from origami.ids import ID_clearPlot_1D
from origami.ids import ID_clearPlot_2D
from origami.ids import ID_clearPlot_3D
from origami.ids import ID_clearPlot_MS
from origami.ids import ID_clearPlot_RT
from origami.ids import ID_saveMZDTImage
from origami.ids import ID_saveRMSDImage
from origami.ids import ID_saveRMSFImage
from origami.ids import ID_clearPlot_MZDT
from origami.ids import ID_clearPlot_RMSD
from origami.ids import ID_clearPlot_RMSF
from origami.ids import ID_plots_rotate90
from origami.ids import ID_save1DImageDoc
from origami.ids import ID_save2DImageDoc
from origami.ids import ID_save3DImageDoc
from origami.ids import ID_saveMSImageDoc
from origami.ids import ID_saveOtherImage
from origami.ids import ID_saveRTImageDoc
from origami.ids import ID_smooth1DdataRT
from origami.ids import ID_clearPlot_1D_MS
from origami.ids import ID_clearPlot_other
from origami.ids import ID_clearPlot_RT_MS
from origami.ids import ID_smooth1Ddata1DT
from origami.ids import ID_clearPlot_Matrix
from origami.ids import ID_plotPanel_resize
from origami.ids import ID_saveMZDTImageDoc
from origami.ids import ID_saveOverlayImage
from origami.ids import ID_saveRMSDImageDoc
from origami.ids import ID_saveRMSFImageDoc
from origami.ids import ID_clearPlot_Overlay
from origami.ids import ID_saveOtherImageDoc
from origami.ids import ID_clearPlot_Watefall
from origami.ids import ID_plotPanel_lockPlot
from origami.ids import ID_saveCompareMSImage
from origami.ids import ID_saveWaterfallImage
from origami.ids import ID_clearPlot_UniDec_MS
from origami.ids import ID_clearPlot_Waterfall
from origami.ids import ID_pickMSpeaksDocument
from origami.ids import ID_saveOverlayImageDoc
from origami.ids import ID_saveRMSDmatrixImage
from origami.ids import ID_extraSettings_legend
from origami.ids import ID_extraSettings_plot1D
from origami.ids import ID_extraSettings_plot2D
from origami.ids import ID_extraSettings_plot3D
from origami.ids import ID_extraSettings_violin
from origami.ids import ID_highlightRectAllIons
from origami.ids import ID_plots_customise_plot
from origami.ids import ID_clearPlot_Calibration
from origami.ids import ID_saveWaterfallImageDoc
from origami.ids import ID_extraSettings_colorbar
from origami.ids import ID_saveRMSDmatrixImageDoc
from origami.ids import ID_clearPlot_UniDec_mwGrid
from origami.ids import ID_clearPlot_UniDec_mzGrid
from origami.ids import ID_extraSettings_waterfall
from origami.ids import ID_clearPlot_UniDec_barchart
from origami.ids import ID_extraSettings_general_plot
from origami.ids import ID_plots_customise_smart_zoom
from origami.ids import ID_clearPlot_UniDec_pickedPeaks
from origami.ids import ID_clearPlot_UniDec_mwDistribution
from origami.ids import ID_docTree_action_open_peak_picker
from origami.ids import ID_clearPlot_UniDec_chargeDistribution
from origami.styles import make_menu_item
from origami.utils.misc import merge_two_dicts
from origami.utils.path import clean_filename
from origami.utils.time import ttime
from origami.icons.icons import IconContainer
from origami.utils.check import isempty
from origami.utils.color import get_random_color
from origami.utils.color import convert_rgb_1_to_255
from origami.utils.color import convert_rgb_1_to_hex
from origami.utils.exceptions import MessageError
from origami.visuals.mpl.normalize import MidpointNormalize
from origami.visuals.mpl.plot_misc import PlotMixed
from origami.gui_elements.misc_dialogs import DialogBox
from origami.visuals.mpl.plot_spectrum import PlotSpectrum
from origami.visuals.mpl.plot_heatmap_2d import PlotHeatmap2D
from origami.visuals.mpl.plot_heatmap_3d import PlotHeatmap3D
from origami.gui_elements.views.view_heatmap import ViewIonHeatmap
from origami.gui_elements.views.view_heatmap import ViewMassSpectrumHeatmap
from origami.gui_elements.views.view_spectrum import ViewMobilogram
from origami.gui_elements.views.view_spectrum import ViewChromatogram
from origami.gui_elements.views.view_spectrum import ViewMassSpectrum
from origami.gui_elements.dialog_customise_plot import DialogCustomisePlot

logger = logging.getLogger(__name__)

# 2D -> Heatmap; Other -> Annotated (or else)


class PanelPlots(wx.Panel):
    """Plotting panel instance"""

    view_ms = None
    plot_ms = None
    panel_rt = None
    panel_rt_top_rt = None
    panel_rt_bottom_ms = None
    view_rt_rt = None
    view_rt_ms = None
    plot_rt_rt = None
    plot_rt_ms = None
    panel_dt = None
    panel_dt_top_dt = None
    panel_dt_bottom_ms = None
    view_dt_dt = None
    view_dt_ms = None
    plot_dt_dt = None
    plot_dt_ms = None
    panel_heatmap = None
    plot_heatmap = None
    view_heatmap = None
    panel_msdt = None
    plot_msdt = None
    view_msdt = None
    panel_overlay = None
    plot_overlay = None
    view_overlay = None
    panel_heatmap_3d = None
    plot_heatmap_3d = None
    view_heatmap_3d = None
    panel_annotated = None
    plot_annotated = None
    view_annotated = None

    def __init__(self, parent, config, presenter):
        wx.Panel.__init__(
            self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.Size(800, 600), style=wx.TAB_TRAVERSAL
        )

        self.config = config
        self.view = parent
        self.presenter = presenter
        self.icons = IconContainer()

        self.currentPage = None
        # Extract size of screen
        self._display_size_px = wx.GetDisplaySize()
        self.SetDimensions(0, 0, self._display_size_px[0] - 320, self._display_size_px[1] - 50)
        self._display_size_mm = wx.GetDisplaySizeMM()

        self.displayRes = wx.GetDisplayPPI()
        self.figsizeX = (self._display_size_px[0] - 320) / self.displayRes[0]
        self.figsizeY = (self._display_size_px[1] - 70) / self.displayRes[1]

        # used to keep track of what were the last selected pages
        self.window_plot1D = "MS"
        self.window_plot2D = "2D"
        self.window_plot3D = "3D"
        self.plot_notebook = self.make_notebook()
        self.current_plot = self.plot_ms
        self.plot_objs = dict()

        self._resizing = False
        self._timer = wx.Timer(self, True)
        self.Bind(wx.EVT_TIMER, self._on_late_resize, self._timer)
        #         self._timer.Bind(wx.EVT_TIMER, self._on_late_resize)

        # initialise pub
        pub.subscribe(self._update_label_position, "update_text_position")

        self.plot_notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.on_page_changed)
        self.Bind(wx.EVT_SIZE, self.on_resize)

        # initialise
        self.setup_splitter_windows()
        self.on_page_changed(evt=None)

    def on_resize(self, evt):
        """Slightly modified resized event which reduces the number of `EVT_SIZE` triggers that can significantly
        affect performance since each plot object in ORIGAMI is automatically resized too"""
        if self._resizing:
            evt.Skip()
            self._resizing = False
        else:
            if not self._timer.IsRunning():
                self._timer.StartOnce(350)

    def _on_late_resize(self, evt):
        """Triggers additional resize after timer event has run out"""
        # trigger resize event
        self._resizing = True
        self.PostSizeEvent()
        self.setup_splitter_windows()

    def setup_splitter_windows(self):
        """Update the size(s) of splitter windows after the window size has changed or at the startup of the program"""
        _, h = self.panel_rt.GetSize()
        h = h // 2
        self.panel_rt.SetMinimumPaneSize(h)

        _, h = self.panel_dt.GetSize()
        h = h // 2
        self.panel_dt.SetMinimumPaneSize(h)

    def setup_handling_and_processing(self):
        self.data_processing = self.view.data_processing
        self.data_handling = self.view.data_handling
        self.document_tree = self.view.panelDocuments.documents

    def on_get_current_page(self):
        self.currentPage = self.plot_notebook.GetPageText(self.plot_notebook.GetSelection())

    def _get_page_text(self):
        self.on_get_current_page()
        return self.currentPage

    def _set_page(self, page_name):
        try:
            self.plot_notebook.SetSelection(page_name)
        except wx.PyAssertionError:
            logger.warning("Failed to set to requested page", exc_info=True)

    def _update_label_position(self, text_obj):
        """Update annotation position

        Change to the label position triggers another event in Annotation Editor

        Parameters
        ----------
        text_obj : mpl.Text object
            Matplotlib object that is being changed
        """
        document_title, dataset_type, dataset_name, annotation_name, text_type = text_obj.obj_name.split("|-|")

        if text_type == "annotation":
            annotations_obj = self.data_handling.get_annotations_data([document_title, dataset_type, dataset_name])
            annotation_obj = annotations_obj.get(annotation_name, None)
            if annotation_obj is None:
                logger.warning(f"Annotation: {annotation_name} was empty")
                return

            new_pos_x, new_pos_y = text_obj.get_position()
            annotations_obj.update_annotation(
                annotation_name, {"label_position": [new_pos_x, new_pos_y * text_obj.y_divider]}
            )
            pub.sendMessage("editor.edit.annotation", annotation_obj=annotations_obj[annotation_name])

            self.view.panelDocuments.documents.on_update_annotation(
                annotations_obj, document_title, dataset_type, dataset_name, set_data_only=True
            )
            logger.info(f"MOUSE: Updated annotation {annotation_name}")

    def on_page_changed(self, evt):
        """Triggered by change of panel in the plot section

        Parameters
        ----------
        evt : wxPython event
            unused
        """
        # get current page
        self.currentPage = self.plot_notebook.GetPageText(self.plot_notebook.GetSelection())

        # keep track of previous pages
        if self.currentPage in ["Mass spectrum", "Chromatogram", "Mobilogram"]:
            self.window_plot1D = self.currentPage
        elif self.currentPage in ["Heatmap", "DT/MS", "Waterfall", "Annotated"]:
            self.window_plot2D = self.currentPage
        elif self.currentPage in ["Heatmap (3D)"]:
            self.window_plot3D = self.currentPage

        if self.currentPage == "Waterfall":
            self.current_plot = self.plot_overlay
        elif self.currentPage == "Mass spectrum":
            self.current_plot = self.plot_ms
        elif self.currentPage == "Mobilogram":
            self.current_plot = self.plot_dt_dt
        elif self.currentPage == "Chromatogram":
            self.current_plot = self.plot_rt_rt
        elif self.currentPage == "Heatmap":
            self.current_plot = self.plot_heatmap
        elif self.currentPage == "DT/MS":
            self.current_plot = self.plot_msdt
        elif self.currentPage == "Annotated":
            self.current_plot = self.plot_annotated
        elif self.currentPage == "Heatmap (3D)":
            self.current_plot = self.plot_heatmap_3d

    def make_notebook(self):
        """Make notebook panel"""

        # Setup notebook
        plot_notebook = wx.Notebook(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0)

        # Setup PLOT MS
        self.view_ms = ViewMassSpectrum(
            plot_notebook,
            self.config._plotSettings["MS"]["gui_size"],
            self.config,
            allow_extraction=True,
            callbacks=dict(CTRL="extract.heatmap.from.spectrum"),
        )
        plot_notebook.AddPage(self.view_ms.panel, "Mass spectrum", False)
        self.plot_ms = self.view_ms.figure

        # Setup PLOT RT
        self.panel_rt = wx.SplitterWindow(plot_notebook, wx.ID_ANY, style=wx.TAB_TRAVERSAL | wx.SP_3DSASH)
        plot_notebook.AddPage(self.panel_rt, "Chromatogram", False)  # RT
        self.view_rt_rt = ViewChromatogram(
            self.panel_rt,
            self.config._plotSettings["RT"]["gui_size"],
            self.config,
            allow_extraction=True,
            callbacks=dict(CTRL="extract.spectrum.from.chromatogram"),
        )
        self.panel_rt_top_rt = self.view_rt_rt.panel
        self.plot_rt_rt = self.view_rt_rt.figure

        self.view_rt_ms = ViewMassSpectrum(
            self.panel_rt, self.config._plotSettings["MS (DT/RT)"]["gui_size"], self.config, allow_extraction=False
        )
        self.panel_rt_bottom_ms = self.view_rt_ms.panel
        self.plot_rt_ms = self.view_rt_ms.figure

        self.panel_rt.SplitHorizontally(self.panel_rt_top_rt, self.panel_rt_bottom_ms)
        self.panel_rt.SetSashGravity(0.5)

        # Setup PLOT 1D
        self.panel_dt = wx.SplitterWindow(plot_notebook, wx.ID_ANY, style=wx.TAB_TRAVERSAL | wx.SP_3DSASH)
        plot_notebook.AddPage(self.panel_dt, "Mobilogram", False)  # 1D

        self.view_dt_dt = ViewMobilogram(
            self.panel_dt,
            self.config._plotSettings["DT"]["gui_size"],
            self.config,
            allow_extraction=True,
            callbacks=dict(CTRL="extract.spectrum.from.mobilogram"),
        )
        self.panel_dt_top_dt = self.view_dt_dt.panel
        self.plot_dt_dt = self.view_dt_dt.figure

        self.view_dt_ms = ViewMassSpectrum(
            self.panel_dt, self.config._plotSettings["MS (DT/RT)"]["gui_size"], self.config, allow_extraction=False
        )
        self.plot_dt_ms = self.view_dt_ms.figure
        self.panel_dt_bottom_ms = self.view_dt_ms.panel

        self.panel_dt.SplitHorizontally(self.panel_dt_top_dt, self.panel_dt_bottom_ms)
        self.panel_dt.SetSashGravity(0.5)

        # Setup PLOT 2D
        self.view_heatmap = ViewIonHeatmap(
            plot_notebook,
            self.config._plotSettings["2D"]["gui_size"],
            self.config,
            allow_extraction=True,
            callbacks=dict(CTRL="extract.heatmap.from.spectrum"),
        )
        plot_notebook.AddPage(self.view_heatmap.panel, "Heatmap", False)
        self.plot_heatmap = self.view_heatmap.figure

        #         self.panel_heatmap, self.plot_heatmap, __ = self.make_heatmap_2d_plot(
        #             plot_notebook, self.config._plotSettings["2D"]["gui_size"]
        #         )
        #         plot_notebook.AddPage(self.panel_heatmap, "Heatmap", False)

        # Setup PLOT DT/MS

        self.view_msdt = ViewMassSpectrumHeatmap(
            plot_notebook,
            self.config._plotSettings["DT/MS"]["gui_size"],
            self.config,
            allow_extraction=True,
            callbacks=dict(CTRL="extract.heatmap.from.spectrum"),
        )
        plot_notebook.AddPage(self.view_msdt.panel, "DT/MS", False)
        self.plot_msdt = self.view_msdt.figure

        #         self.panel_msdt, self.plot_msdt, __ = self.make_heatmap_2d_plot(
        #             plot_notebook, self.config._plotSettings["DT/MS"]["gui_size"]
        #         )
        #         plot_notebook.AddPage(self.panel_msdt, "DT/MS", False)

        # Setup PLOT WATERFALL
        self.panel_overlay, self.plot_overlay, __ = self.make_base_plot(
            plot_notebook, self.config._plotSettings["Waterfall"]["gui_size"]
        )
        plot_notebook.AddPage(self.panel_overlay, "Waterfall", False)

        # Setup PLOT 3D
        self.panel_heatmap_3d, self.plot_heatmap_3d, __ = self.make_heatmap_3d_plot(
            plot_notebook, self.config._plotSettings["3D"]["gui_size"]
        )
        plot_notebook.AddPage(self.panel_heatmap_3d, "Heatmap (3D)", False)

        # Other
        self.panel_annotated, self.plot_annotated, __ = self.make_base_plot(
            plot_notebook, self.config._plotSettings["2D"]["gui_size"]
        )
        plot_notebook.AddPage(self.panel_annotated, "Annotated", False)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(plot_notebook, 1, wx.EXPAND | wx.ALL, 1)
        self.SetSizer(main_sizer)
        self.Layout()
        self.Show(True)

        # now that we set sizer, we can get window size
        panel_size = plot_notebook.GetSize()[1]
        half_size = (panel_size - 50) / 2

        self.panel_dt.SetMinimumPaneSize(half_size)
        self.panel_rt.SetMinimumPaneSize(half_size)

        self.Bind(wx.EVT_CONTEXT_MENU, self.on_right_click)

        return plot_notebook

    def make_base_plot(self, parent, figsize):
        """Make basic plot"""
        plot_panel = wx.Panel(parent)
        plot_window = PlotMixed(plot_panel, config=self.config, figsize=figsize)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(plot_window, 1, wx.EXPAND)
        plot_panel.SetSizer(sizer)
        sizer.Fit(plot_panel)

        return plot_panel, plot_window, sizer

    def make_1d_plot(self, parent, figsize):
        """Make 2d heatmap plot"""
        plot_panel = wx.Panel(parent)
        plot_window = PlotSpectrum(plot_panel, config=self.config, figsize=figsize)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(plot_window, 1, wx.EXPAND)
        plot_panel.SetSizer(sizer)
        sizer.Fit(plot_panel)

        return plot_panel, plot_window, sizer

    def make_heatmap_2d_plot(self, parent, figsize):
        """Make 2d heatmap plot"""
        plot_panel = wx.Panel(parent)
        plot_window = PlotHeatmap2D(plot_panel, config=self.config, figsize=figsize)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(plot_window, 1, wx.EXPAND)
        plot_panel.SetSizer(sizer)
        sizer.Fit(plot_panel)

        return plot_panel, plot_window, sizer

    def make_heatmap_3d_plot(self, parent, figsize):
        """Make 3d heatmap plot"""
        plot_panel = wx.Panel(parent)
        plot_window = PlotHeatmap3D(plot_panel, config=self.config, figsize=figsize)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(plot_window, 1, wx.EXPAND)
        plot_panel.SetSizer(sizer)
        sizer.Fit(plot_panel)

        return plot_panel, plot_window, sizer

    def on_copy_to_clipboard(self, evt):
        plot_obj = self.get_plot_from_name(self.currentPage)
        plot_obj.copy_to_clipboard()

    def on_get_plot_data(self):
        plot_obj = self.get_plot_from_name(self.currentPage)
        xvals, yvals, labels, xlabel, ylabel = plot_obj.plot_1D_get_data()

        return plot_obj, xvals, yvals, labels, xlabel, ylabel

    def on_smooth_spectrum(self, evt):
        #         """Smooth plot signal"""
        try:
            plot_obj, xvals, yvals, labels, xlabel, ylabel = self.on_get_plot_data()
        except AttributeError:
            raise MessageError("Plot is empty", "There are no signals in the plot to smooth")
        #         plot_obj = self.get_plot_from_name(self.currentPage)
        #         try:
        #             xs, ys, labels, xlabel, ylabel = plot_obj.plot_1D_get_data()
        #         except AttributeError:
        #             raise MessageError("Plot is empty", "There are no signals in the plot to smooth")
        #         n_signals = len(xs)
        #         if n_signals > 1:
        #             raise MessageError("Not supported yet",
        #                                "At the moment signal smoothing is only supported for plot with one
        #                                signal." +
        #                                f" This one appears to have {n_signals}")
        yvals = self.data_processing.on_smooth_1D_signal(yvals)

        plt_kwargs = self._buildPlotParameters(plotType="1D")
        plot_obj.plot_1D_update_data(xvals[0], yvals[0], xlabel, ylabel, label=labels[0], **plt_kwargs)
        plot_obj.repaint()

    def on_process_spectrum(self, evt):
        plot_obj = self.get_plot_from_name(self.currentPage)
        try:
            xvals, yvals, __, xlabel, ylabel = plot_obj.plot_1D_get_data()
        except AttributeError:
            raise MessageError("Plot is empty", "There are no signals in the plot to smooth")

        data = {"xvals": xvals[0], "yvals": yvals[0], "xlabels": xlabel, "ylabels": ylabel}
        self.document_tree.on_process_MS_plot_only(data)

    def on_process_heatmap(self, evt):
        plot_obj = self.get_plot_from_name(self.currentPage)
        data = plot_obj.plot_2D_get_data()

        # ensure correct keys are present
        if "xlabels" not in data:
            data["xlabels"] = data["xlabel"]
        if "ylabels" not in data:
            data["ylabels"] = data["ylabel"]
        try:
            self.document_tree.on_process_2D_plot_only(self.currentPage, data)
        except ValueError:
            raise MessageError(
                "Failed processing",
                "This error can occur when visually processing DT/MS dataset. It is best to simply"
                + " right-click on DT/MS item in the Document Tree and select 'Process...'"
                + " where it should not occur.",
            )

    def on_right_click(self, evt):
        self.currentPage = self.plot_notebook.GetPageText(self.plot_notebook.GetSelection())

        # Make bindings
        self.Bind(wx.EVT_MENU, self.on_smooth_spectrum, id=ID_smooth1DdataRT)
        self.Bind(wx.EVT_MENU, self.on_smooth_spectrum, id=ID_smooth1Ddata1DT)
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
        self.Bind(wx.EVT_MENU, self.on_lock_plot, id=ID_plotPanel_lockPlot)
        self.Bind(wx.EVT_MENU, self.on_rotate_plot, id=ID_plots_rotate90)
        self.Bind(wx.EVT_MENU, self.on_resize_check, id=ID_plotPanel_resize)
        self.Bind(wx.EVT_MENU, self.on_customise_plot, id=ID_plots_customise_plot)
        self.Bind(wx.EVT_MENU, self.save_images, id=ID_saveOtherImage)
        self.Bind(wx.EVT_MENU, self.save_images, id=ID_saveCompareMSImage)
        self.Bind(wx.EVT_MENU, self.on_customise_smart_zoom, id=ID_plots_customise_smart_zoom)
        self.Bind(wx.EVT_MENU, self.on_open_peak_picker, id=ID_docTree_action_open_peak_picker)

        # make main menu
        menu = wx.Menu()

        # pre-generate common menu items
        menu_edit_general = make_menu_item(
            parent=menu,
            id=ID_extraSettings_general_plot,
            text="Edit general parameters...",
            bitmap=self.icons.iconsLib["panel_plot_general_16"],
        )
        menu_edit_plot_1D = make_menu_item(
            parent=menu,
            id=ID_extraSettings_plot1D,
            text="Edit plot parameters...",
            bitmap=self.icons.iconsLib["panel_plot1D_16"],
        )
        menu_edit_plot_2D = make_menu_item(
            parent=menu,
            id=ID_extraSettings_plot2D,
            text="Edit plot parameters...",
            bitmap=self.icons.iconsLib["panel_plot2D_16"],
        )
        menu_edit_plot_3D = make_menu_item(
            parent=menu,
            id=ID_extraSettings_plot3D,
            text="Edit plot parameters...",
            bitmap=self.icons.iconsLib["panel_plot3D_16"],
        )
        menu_edit_colorbar = make_menu_item(
            parent=menu,
            id=ID_extraSettings_colorbar,
            text="Edit colorbar parameters...",
            bitmap=self.icons.iconsLib["panel_colorbar_16"],
        )
        menu_edit_legend = make_menu_item(
            parent=menu,
            id=ID_extraSettings_legend,
            text="Edit legend parameters...",
            bitmap=self.icons.iconsLib["panel_legend_16"],
        )
        #         menu_edit_rmsd = make_menu_item(
        #             parent=menu,
        #             id=ID_extraSettings_rmsd,
        #             text="Edit plot parameters...",
        #             bitmap=self.icons.iconsLib["panel_rmsd_16"],
        #         )
        menu_edit_waterfall = make_menu_item(
            parent=menu,
            id=ID_extraSettings_waterfall,
            text="Edit waterfall parameters...",
            bitmap=self.icons.iconsLib["panel_waterfall_16"],
        )
        menu_edit_violin = make_menu_item(
            parent=menu,
            id=ID_extraSettings_violin,
            text="Edit violin parameters...",
            bitmap=self.icons.iconsLib["panel_violin_16"],
        )
        menu_customise_plot = make_menu_item(
            parent=menu,
            id=ID_plots_customise_plot,
            text="Customise plot...",
            bitmap=self.icons.iconsLib["change_xlabels_16"],
        )
        #         menu_action_rotate90 = make_menu_item(
        #             parent=menu, id=ID_plots_rotate90, text="Rotate 90°", bitmap=self.icons.iconsLib["blank_16"]
        #         )
        menu_action_process_2D = make_menu_item(
            parent=menu, text="Process heatmap...", bitmap=self.icons.iconsLib["process_2d_16"]
        )

        menu_action_process_MS = make_menu_item(
            parent=menu, text="Process mass spectrum...", bitmap=self.icons.iconsLib["process_ms_16"]
        )

        menu_action_copy_to_clipboard = make_menu_item(
            parent=menu, id=wx.ID_ANY, text="Copy plot to clipboard", bitmap=self.icons.iconsLib["filelist_16"]
        )

        # bind events by item
        self.Bind(wx.EVT_MENU, self.on_process_spectrum, menu_action_process_MS)
        self.Bind(wx.EVT_MENU, self.on_process_heatmap, menu_action_process_2D)

        if self.currentPage == "Mass spectrum":
            menu.AppendItem(menu_action_process_MS)
            menu.AppendItem(
                make_menu_item(
                    parent=menu,
                    id=ID_docTree_action_open_peak_picker,
                    text="Open peak picker...",
                    bitmap=self.icons.iconsLib["process_fit_16"],
                )
            )
            menu.AppendItem(
                make_menu_item(
                    parent=menu,
                    id=ID_highlightRectAllIons,
                    text="Show extracted ions",
                    bitmap=self.icons.iconsLib["annotate16"],
                )
            )
            menu.AppendSeparator()
            menu.AppendItem(menu_edit_general)
            menu.AppendItem(menu_edit_plot_1D)
            self.lock_plot_check = menu.AppendCheckItem(ID_plotPanel_lockPlot, "Lock plot", help="")
            self.lock_plot_check.Check(self.plot_ms.lock_plot_from_updating)
            menu.AppendItem(menu_customise_plot)
            menu.AppendSeparator()
            self.resize_plot_check = menu.AppendCheckItem(ID_plotPanel_resize, "Resize on saving", help="")
            self.resize_plot_check.Check(self.config.resize)
            if self.view.plot_name == "compare_MS":
                menu.AppendItem(
                    make_menu_item(
                        parent=menu,
                        id=ID_saveCompareMSImage,
                        text="Save figure as...",
                        bitmap=self.icons.iconsLib["save16"],
                    )
                )
            else:
                menu.AppendItem(
                    make_menu_item(
                        parent=menu, id=ID_saveMSImage, text="Save figure as...", bitmap=self.icons.iconsLib["save16"]
                    )
                )

            menu.AppendItem(menu_action_copy_to_clipboard)
            menu.AppendSeparator()
            menu.AppendItem(
                make_menu_item(
                    parent=menu, id=ID_clearPlot_MS, text="Clear plot", bitmap=self.icons.iconsLib["clear_16"]
                )
            )
        elif self.currentPage == "Chromatogram":
            if self.view.plot_name == "MS":
                menu.AppendItem(
                    make_menu_item(
                        parent=menu, id=ID_clearPlot_RT_MS, text="Clear plot", bitmap=self.icons.iconsLib["clear_16"]
                    )
                )
            else:
                menu.Append(ID_smooth1DdataRT, "Smooth chromatogram")
                menu.AppendSeparator()
                menu.AppendItem(menu_edit_general)
                menu.AppendItem(menu_edit_plot_1D)
                menu.AppendItem(menu_edit_legend)
                self.lock_plot_check = menu.AppendCheckItem(ID_plotPanel_lockPlot, "Lock plot", help="")
                self.lock_plot_check.Check(self.plot_rt_rt.lock_plot_from_updating)
                menu.AppendItem(menu_customise_plot)
                menu.AppendSeparator()
                self.resize_plot_check = menu.AppendCheckItem(ID_plotPanel_resize, "Resize on saving", help="")
                self.resize_plot_check.Check(self.config.resize)
                menu.AppendItem(
                    make_menu_item(
                        parent=menu, id=ID_saveRTImage, text="Save figure as...", bitmap=self.icons.iconsLib["save16"]
                    )
                )
                menu.AppendItem(menu_action_copy_to_clipboard)
                menu.AppendSeparator()
                menu.AppendItem(
                    make_menu_item(
                        parent=menu, id=ID_clearPlot_RT, text="Clear plot", bitmap=self.icons.iconsLib["clear_16"]
                    )
                )
        elif self.currentPage == "Mobilogram":
            if self.view.plot_name == "MS":
                menu.AppendItem(
                    make_menu_item(
                        parent=menu, id=ID_clearPlot_1D_MS, text="Clear plot", bitmap=self.icons.iconsLib["clear_16"]
                    )
                )
            else:
                menu.Append(ID_smooth1Ddata1DT, "Smooth mobilogram")
                menu.AppendSeparator()
                menu.AppendItem(menu_edit_general)
                menu.AppendItem(menu_edit_plot_1D)
                menu.AppendItem(menu_edit_legend)
                self.lock_plot_check = menu.AppendCheckItem(ID_plotPanel_lockPlot, "Lock plot", help="")
                self.lock_plot_check.Check(self.plot_dt_dt.lock_plot_from_updating)
                menu.AppendItem(menu_customise_plot)
                menu.AppendSeparator()
                self.resize_plot_check = menu.AppendCheckItem(ID_plotPanel_resize, "Resize on saving", help="")
                self.resize_plot_check.Check(self.config.resize)
                menu.AppendItem(
                    make_menu_item(
                        parent=menu, id=ID_save1DImage, text="Save figure as...", bitmap=self.icons.iconsLib["save16"]
                    )
                )
                menu.AppendItem(menu_action_copy_to_clipboard)
                menu.AppendSeparator()
                menu.AppendItem(
                    make_menu_item(
                        parent=menu, id=ID_clearPlot_1D, text="Clear plot", bitmap=self.icons.iconsLib["clear_16"]
                    )
                )
        elif self.currentPage == "Heatmap":
            menu.AppendItem(menu_action_process_2D)
            #             menu.AppendItem(menu_action_rotate90)
            menu.AppendSeparator()
            menu.AppendItem(menu_edit_general)
            menu.AppendItem(menu_edit_plot_2D)
            menu.AppendItem(menu_edit_colorbar)
            menu.AppendItem(menu_edit_legend)
            self.lock_plot_check = menu.AppendCheckItem(ID_plotPanel_lockPlot, "Lock plot", help="")
            self.lock_plot_check.Check(self.plot_heatmap.lock_plot_from_updating)
            menu.AppendItem(menu_customise_plot)
            menu.AppendSeparator()
            self.resize_plot_check = menu.AppendCheckItem(ID_plotPanel_resize, "Resize on saving", help="")
            self.resize_plot_check.Check(self.config.resize)
            menu.AppendItem(
                make_menu_item(
                    parent=menu, id=ID_save2DImage, text="Save figure as...", bitmap=self.icons.iconsLib["save16"]
                )
            )
            menu.AppendItem(menu_action_copy_to_clipboard)
            menu.AppendSeparator()
            menu.AppendItem(
                make_menu_item(
                    parent=menu, id=ID_clearPlot_2D, text="Clear plot", bitmap=self.icons.iconsLib["clear_16"]
                )
            )
        elif self.currentPage == "DT/MS":
            menu.AppendItem(menu_action_process_2D)
            #             menu.AppendItem(menu_action_rotate90)
            menu.AppendSeparator()
            menu.AppendItem(
                make_menu_item(
                    parent=menu,
                    id=ID_plots_customise_smart_zoom,
                    text="Customise smart zoom....",
                    bitmap=self.icons.iconsLib["zoom_16"],
                )
            )
            menu.AppendSeparator()
            menu.AppendItem(menu_edit_general)
            menu.AppendItem(menu_edit_plot_2D)
            menu.AppendItem(menu_edit_colorbar)
            self.lock_plot_check = menu.AppendCheckItem(ID_plotPanel_lockPlot, "Lock plot", help="")
            self.lock_plot_check.Check(self.plot_msdt.lock_plot_from_updating)
            menu.AppendItem(menu_customise_plot)
            menu.AppendSeparator()
            self.resize_plot_check = menu.AppendCheckItem(ID_plotPanel_resize, "Resize on saving", help="")
            self.resize_plot_check.Check(self.config.resize)
            menu.AppendItem(
                make_menu_item(
                    parent=menu, id=ID_saveMZDTImage, text="Save figure as...", bitmap=self.icons.iconsLib["save16"]
                )
            )
            menu.AppendItem(menu_action_copy_to_clipboard)
            menu.AppendSeparator()
            menu.AppendItem(
                make_menu_item(
                    parent=menu, id=ID_clearPlot_MZDT, text="Clear plot", bitmap=self.icons.iconsLib["clear_16"]
                )
            )
        elif self.currentPage == "Heatmap (3D)":
            menu.AppendItem(menu_edit_plot_3D)
            menu.AppendSeparator()
            self.resize_plot_check = menu.AppendCheckItem(ID_plotPanel_resize, "Resize on saving", help="")
            self.resize_plot_check.Check(self.config.resize)
            menu.AppendItem(
                make_menu_item(
                    parent=menu, id=ID_save3DImage, text="Save figure as...", bitmap=self.icons.iconsLib["save16"]
                )
            )
            menu.AppendSeparator()
            menu.AppendItem(
                make_menu_item(
                    parent=menu, id=ID_clearPlot_3D, text="Clear plot", bitmap=self.icons.iconsLib["clear_16"]
                )
            )
        elif self.currentPage == "Waterfall":
            menu.AppendItem(menu_edit_general)
            menu.AppendItem(menu_edit_plot_2D)
            menu.AppendItem(menu_edit_legend)
            menu.AppendItem(menu_edit_waterfall)
            menu.AppendItem(menu_edit_violin)
            self.lock_plot_check = menu.AppendCheckItem(ID_plotPanel_lockPlot, "Lock plot", help="")
            self.lock_plot_check.Check(self.plot_overlay.lock_plot_from_updating)
            menu.AppendItem(menu_customise_plot)
            menu.AppendSeparator()
            self.resize_plot_check = menu.AppendCheckItem(ID_plotPanel_resize, "Resize on saving", help="")
            self.resize_plot_check.Check(self.config.resize)
            menu.AppendItem(
                make_menu_item(
                    parent=menu,
                    id=ID_saveWaterfallImage,
                    text="Save figure as...",
                    bitmap=self.icons.iconsLib["save16"],
                )
            )
            menu.AppendItem(menu_action_copy_to_clipboard)
            menu.AppendSeparator()
            menu.AppendItem(
                make_menu_item(
                    parent=menu, id=ID_clearPlot_Waterfall, text="Clear plot", bitmap=self.icons.iconsLib["clear_16"]
                )
            )
        elif self.currentPage == "Annotated":
            menu.AppendItem(menu_edit_general)
            menu.AppendItem(menu_edit_plot_1D)
            menu.AppendItem(menu_edit_plot_2D)
            menu.AppendItem(menu_edit_colorbar)
            menu.AppendItem(menu_edit_legend)
            menu.AppendItem(menu_edit_waterfall)
            menu.AppendItem(menu_edit_violin)
            menu.AppendSeparator()
            menu.AppendItem(
                make_menu_item(
                    parent=menu,
                    id=ID_plots_customise_plot,
                    text="Customise plot...",
                    bitmap=self.icons.iconsLib["change_xlabels_16"],
                )
            )
            menu.AppendSeparator()
            self.resize_plot_check = menu.AppendCheckItem(ID_plotPanel_resize, "Resize on saving", help="")
            self.resize_plot_check.Check(self.config.resize)
            menu.AppendItem(
                make_menu_item(
                    parent=menu, id=ID_saveOtherImage, text="Save figure as...", bitmap=self.icons.iconsLib["save16"]
                )
            )
            menu.AppendItem(menu_action_copy_to_clipboard)
            menu.AppendSeparator()
            menu.AppendItem(
                make_menu_item(
                    parent=menu, id=ID_clearPlot_other, text="Clear plot", bitmap=self.icons.iconsLib["clear_16"]
                )
            )

        self.Bind(wx.EVT_MENU, self.on_copy_to_clipboard, menu_action_copy_to_clipboard)

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def on_save_image(self, plot, filename, **kwargs):
        tstart = ttime()

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)

        extension = self.config.imageFormat
        resize_name = kwargs.pop("resize_name", None)

        if not filename.endswith(f".{extension}"):
            filename += f".{extension}"

        # build kwargs
        kwargs = {
            "transparent": self.config.transparent,
            "dpi": self.config.dpi,
            "format": extension,
            "compression": "zlib",
            "resize": None,
            "tight": self.config.image_tight,
            "image_size_inch": None,
            "image_size_px": None,
            "image_axes_size": None,
        }

        if self.config.resize and resize_name is not None:
            kwargs["resize"] = resize_name
            kwargs["image_size_inch"] = self.config.image_size_inch
            kwargs["image_size_px"] = self.config.image_size_px
            kwargs["image_axes_size"] = self.config.image_axes_size

        plot_obj.save_figure(filename, **kwargs)

        logger.info(f"Saved figure {filename} in {ttime()-tstart:.2f} seconds")

    def save_images(self, evt, path=None, **save_kwargs):
        """ Save figure depending on the event ID """
        self.data_handling.update_statusbar("Saving image...", 4)

        # retrieve event ID
        if isinstance(evt, int):
            evtID = evt
        elif isinstance(evt, str):
            evtID = evt.lower()
        elif evt is None:
            evtID = None
        else:
            evtID = evt.GetId()

        path, title = self.data_handling._on_get_document_path_and_title()
        if path is None:
            logger.error(f"Could not find path {path}")
            return

        # Select default name + link to the plot
        if evtID in [ID_saveMSImage, ID_saveMSImageDoc, "ms"]:
            image_name = self.config._plotSettings["MS"]["default_name"]
            resizeName = "MS"
            plotWindow = self.plot_ms

        # Select default name + link to the plot
        elif evtID in [ID_saveCompareMSImage]:
            image_name = self.config._plotSettings["MS (compare)"]["default_name"]
            resizeName = "MS (compare)"
            plotWindow = self.plot_ms

        elif evtID in [ID_saveRTImage, ID_saveRTImageDoc, "rt", "chromatogram"]:
            image_name = self.config._plotSettings["RT"]["default_name"]
            resizeName = "RT"
            plotWindow = self.plot_rt_rt

        elif evtID in [ID_save1DImage, ID_save1DImageDoc, "1d", "mobilogram"]:
            image_name = self.config._plotSettings["DT"]["default_name"]
            resizeName = "DT"
            plotWindow = self.plot_dt_dt

        elif evtID in [ID_save2DImage, ID_save2DImageDoc, "2d", "heatmap"]:
            plotWindow = self.plot_heatmap
            image_name = self.config._plotSettings["2D"]["default_name"]
            resizeName = "2D"

        elif evtID in [ID_save3DImage, ID_save3DImageDoc, "3d", "heatmap (3d)"]:
            image_name = self.config._plotSettings["3D"]["default_name"]
            resizeName = "3D"
            plotWindow = self.plot_heatmap_3d

        elif evtID in [ID_saveWaterfallImage, ID_saveWaterfallImageDoc, "waterfall"]:
            plotWindow = self.plot_overlay
            if plotWindow.plot_name == "Violin":
                image_name = self.config._plotSettings["Violin"]["default_name"]
                resizeName = "Violin"
            else:
                image_name = self.config._plotSettings["Waterfall"]["default_name"]
                resizeName = "Waterfall"

        elif evtID in [ID_saveMZDTImage, ID_saveMZDTImageDoc, "ms/dt"]:
            image_name = self.config._plotSettings["DT/MS"]["default_name"]
            resizeName = "DT/MS"
            plotWindow = self.plot_msdt

        elif evtID in [ID_saveOverlayImage, ID_saveOverlayImageDoc, "mask", "transparent"]:
            plotWindow = self.plot_annotated
            image_name = plotWindow.get_plot_name()
            resizeName = "Overlay"

        elif evtID in [ID_saveRMSDmatrixImage, ID_saveRMSDmatrixImageDoc, "matrix"]:
            image_name = self.config._plotSettings["Matrix"]["default_name"]
            resizeName = "Matrix"
            plotWindow = self.plot_annotated

        elif evtID in [ID_saveRMSDImage, ID_saveRMSDImageDoc, ID_saveRMSFImage, ID_saveRMSFImageDoc, "rmsd", "rmsf"]:
            plotWindow = self.plot_annotated
            image_name = self.config._plotSettings["RMSD"]["default_name"]
            resizeName = plotWindow.get_plot_name()

        elif evtID in [ID_saveOtherImageDoc, ID_saveOtherImage, "overlay", "other"]:
            image_name = "custom_plot"
            resizeName = None
            plotWindow = self.plot_annotated

        elif evtID is None and "plot_obj" in save_kwargs:
            image_name = save_kwargs.get("image_name")
            resizeName = None
            plotWindow = save_kwargs.pop("plot_obj")

        # generate a better default name and remove any silly characters
        if "image_name" in save_kwargs:
            image_name = save_kwargs.pop("image_name")
            if image_name is None:
                image_name = "{}_{}".format(title, image_name)
        else:
            image_name = "{}_{}".format(title, image_name)
        image_name = clean_filename(image_name)

        # Setup filename
        wildcard = (
            "SVG Scalable Vector Graphic (*.svg)|*.svg|"
            + "SVGZ Compressed Scalable Vector Graphic (*.svgz)|*.svgz|"
            + "PNG Portable Network Graphic (*.png)|*.png|"
            + "Enhanced Windows Metafile (*.eps)|*.eps|"
            + "JPEG File Interchange Format (*.jpeg)|*.jpeg|"
            + "TIFF Tag Image File Format (*.tiff)|*.tiff|"
            + "RAW Image File Format (*.raw)|*.raw|"
            + "PS PostScript Image File Format (*.ps)|*.ps|"
            + "PDF Portable Document Format (*.pdf)|*.pdf"
        )

        wildcard_dict = {"svg": 0, "svgz": 1, "png": 2, "eps": 3, "jpeg": 4, "tiff": 5, "raw": 6, "ps": 7, "pdf": 8}

        dlg = wx.FileDialog(self, "Save as...", "", "", wildcard=wildcard, style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        dlg.CentreOnParent()
        dlg.SetFilename(image_name)
        try:
            dlg.SetFilterIndex(wildcard_dict[self.config.imageFormat])
        except Exception:
            logger.error("Could not set image format")

        if dlg.ShowModal() == wx.ID_OK:
            tstart = time.clock()
            filename = dlg.GetPath()
            __, extension = os.path.splitext(filename)
            self.config.imageFormat = extension[1::]

            # build kwargs
            kwargs = {
                "transparent": self.config.transparent,
                "dpi": self.config.dpi,
                "format": extension[1::],
                "compression": "zlib",
                "resize": None,
                "tight": self.config.image_tight,
            }

            if self.config.resize:
                kwargs["resize"] = resizeName

            plotWindow.save_figure(path=filename, **kwargs)

            logger.info(f"Saved figure `{path}` in {ttime()-tstart:.2f}s")
            return

        logger.warning("Image saving operation was cancelled")

    def on_open_peak_picker(self, evt):
        plot_obj = self.get_plot_from_name("MS")

        document_name = plot_obj.document_name
        dataset_name = plot_obj.dataset_name
        if document_name is None or dataset_name is None:
            raise MessageError(
                "No spectrum information",
                "Document title and/or spectrum title were not recorded for this plot."
                + "\n\nYou can try peak picking by right-clicking in the document tree on the desired mass spectrum"
                + " and clicking on `Open peak picker`",
            )

        self.view.panelDocuments.documents.on_open_peak_picker(
            None, document_name=document_name, dataset_name=dataset_name
        )

    def get_plot_from_name(self, plot_name):
        """Retrieve plot object from name

        Parameters
        ----------
        plot_name : str
            name of the plot

        Returns
        plot_obj : plot.plots object
            plot object
        """
        plot_dict = {
            "ms": self.plot_ms,
            "mass_spectrum": self.plot_ms,
            "mass spectrum": self.plot_ms,
            "rt": self.plot_rt_rt,
            "chromatogram": self.plot_rt_rt,
            "1d": self.plot_dt_dt,
            "mobilogram": self.plot_dt_dt,
            "2d": self.plot_heatmap,
            "heatmap": self.plot_heatmap,
            "dt/ms": self.plot_msdt,
            "overlay": self.plot_annotated,
            "rmsf": self.plot_annotated,
            "rmsd": self.plot_annotated,
            "grid": self.plot_annotated,
            "compare": self.plot_annotated,
            "comparison": self.plot_annotated,
            "waterfall": self.plot_overlay,
            "other": self.plot_annotated,
            "3d": self.plot_heatmap_3d,
            "heatmap (3d)": self.plot_heatmap_3d,
            "matrix": self.plot_annotated,
            "annotated": self.plot_annotated,
            "ms_rt": self.plot_rt_ms,
            "ms_dt": self.plot_dt_ms,
        }
        plot_name = plot_name.lower()
        plot_obj = plot_dict.get(plot_name, None)
        if plot_obj is None:
            logger.error(f"Could not find plot object with name `{plot_name}")
        return plot_obj

    def get_plot_from_id(self, id_value):
        """Retireve plot object from id"""

        id_plot_dict = {
            ID_clearPlot_MS: "Mass spectrum",
            ID_clearPlot_RT: "Chromatogram",
            ID_clearPlot_1D: "Mobilogram",
            ID_clearPlot_2D: "Heatmap",
            ID_clearPlot_MZDT: "DT/MS",
            ID_clearPlot_RMSF: "RMSF",
            ID_clearPlot_RMSD: "RMSD",
            ID_clearPlot_Overlay: "Overlay",
            ID_clearPlot_Waterfall: "Waterfall",
            ID_clearPlot_3D: "Heatmap (3D)",
            ID_clearPlot_Matrix: "Matrix",
            ID_clearPlot_other: "Annotated",
            ID_clearPlot_RT_MS: "MS_RT",
            ID_clearPlot_1D_MS: "MS_DT",
        }
        plot_name = id_plot_dict[id_value]
        return self.get_plot_from_name(plot_name)

    def on_lock_plot(self, evt):
        """Lock/unlock plot"""
        plot_obj = self.get_plot_from_name(self.currentPage)
        plot_obj.lock_plot_from_updating = not plot_obj.lock_plot_from_updating

    def on_resize_check(self, evt):
        self.config.resize = not self.config.resize

    def on_customise_smart_zoom(self, evt):
        from origami.gui_elements.dialog_customise_smart_zoom import dialog_customise_smart_zoom

        dlg = dialog_customise_smart_zoom(self, self.presenter, self.config)
        dlg.ShowModal()

    def on_customise_plot(self, evt, **kwargs):
        """Open customization panel..."""
        open_window, title = True, ""

        if "plot" in kwargs and "plot_obj" in kwargs:
            plot = kwargs.pop("plot_obj")
            title = kwargs.pop("plot")
        else:
            plot = self.get_plot_from_name(self.currentPage)
            title = f"{self.currentPage}..."
        #         elif self.currentPage == "Overlay":
        #             plot, title = self.plot2D, "Overlay"
        #             if plot.plot_name not in ["Mask", "Transparent"]:
        #                 open_window = False
        #         elif self.currentPage == "RMSF":
        #             plot, title = self.plot2D, "RMSF"
        #             if plot.plot_name not in ["RMSD"]:
        #                 open_window = False
        #         elif self.currentPage == "Comparison":
        #             plot, title = self.plot2D, "Comparison..."
        #         elif self.currentPage == "Other":
        #             plot, title = self.plotOther, "Custom data..."

        if not open_window:
            raise MessageError("Error", "Cannot customise parameters for this plot. Try replotting instead.")

        if not hasattr(plot, "plotMS"):
            raise MessageError(
                "Error", "Cannot customise plot parameters, either because it does not exist or is not supported yet."
            )

        if hasattr(plot, "plot_limits") and len(plot.plot_limits) == 4:
            xmin, xmax = plot.plot_limits[0], plot.plot_limits[1]
            ymin, ymax = plot.plot_limits[2], plot.plot_limits[3]
        else:
            try:
                xmin, xmax = plot.plot_base.get_xlim()
                ymin, ymax = plot.plot_base.get_ylim()
            except AttributeError as err:
                raise MessageError("Error", "Cannot customise plot parameters if the plot does not exist." + f"\n{err}")

        dpi = wx.ScreenDC().GetPPI()
        if hasattr(plot, "plot_parameters"):
            if "panel_size" in plot.plot_parameters:
                plot_sizeInch = (
                    np.round(plot.plot_parameters["panel_size"][0] / dpi[0], 2),
                    np.round(plot.plot_parameters["panel_size"][1] / dpi[1], 2),
                )
            else:
                plot_size = plot.GetSize()
                plot_sizeInch = (np.round(plot_size[0] / dpi[0], 2), np.round(plot_size[1] / dpi[1], 2))
        else:
            plot_size = plot.GetSize()
            plot_sizeInch = (np.round(plot_size[0] / dpi[0], 2), np.round(plot_size[1] / dpi[1], 2))

        try:
            kwargs = {
                "xmin": xmin,
                "xmax": xmax,
                "ymin": ymin,
                "ymax": ymax,
                "major_xticker": plot.plot_base.xaxis.get_major_locator(),
                "major_yticker": plot.plot_base.yaxis.get_major_locator(),
                "minor_xticker": plot.plot_base.xaxis.get_minor_locator(),
                "minor_yticker": plot.plot_base.yaxis.get_minor_locator(),
                "tick_size": self.config.tickFontSize_1D,
                "tick_weight": self.config.tickFontWeight_1D,
                "label_size": self.config.labelFontSize_1D,
                "label_weight": self.config.labelFontWeight_1D,
                "title_size": self.config.titleFontSize_1D,
                "title_weight": self.config.titleFontWeight_1D,
                "xlabel": plot.plot_base.get_xlabel(),
                "ylabel": plot.plot_base.get_ylabel(),
                "title": plot.plot_base.get_title(),
                "plot_size": plot_sizeInch,
                "plot_axes": plot._axes,
                "plot": plot,
                "window_title": title,
            }
        except AttributeError as err:
            raise MessageError("Error", "Cannot customise plot parameters if the plot does not exist." + f"\n{err}")

        dlg = DialogCustomisePlot(self, self.presenter, self.config, **kwargs)
        dlg.ShowModal()

    def on_rotate_plot(self, evt):
        plot = self.get_plot_from_name(self.currentPage)

        plot.on_rotate_90()
        plot.repaint()

    def on_change_rmsf_zoom(self, xmin, xmax):
        """Receives a message about change in RMSF plot"""
        try:
            self.plot_objs["RMSF"].onZoomRMSF(xmin, xmax)
        except (AttributeError, KeyError) as err:
            logger.error(f"Could not zoom-in on RMSF. {err}")

    def plot_update_axes(self, plotName):

        # get current sizes
        axes_sizes = self.config._plotSettings[plotName]["axes_size"]

        plot_obj = self.get_plot_from_name(plotName)
        if plot_obj is None:
            return

        #         # get link to the plot
        #         if plotName == "MS":
        #             resize_plot = [self.plot1, self.plot_RT_MS, self.plot_DT_MS]
        #         elif plotName == "RMSD":
        #             resize_plot = self.plot2D
        #         elif plotName in ["Comparison", "Matrix"]:
        #             resize_plot = self.plot2D
        #         elif plotName in ["Overlay", "Overlay (Grid)"]:
        #             resize_plot = self.plot2D
        #         elif plotName == "Calibration (MS)":
        #             resize_plot = self.topPlotMS
        #         elif plotName == "Calibration (DT)":
        #             resize_plot = self.bottomPlot1DT

        # apply new size
        try:
            if not isinstance(plot_obj, list):
                resize_plot = [plot_obj]
            for plot in resize_plot:
                if plot.lock_plot_from_updating:
                    msg = (
                        "This plot is locked and you cannot use global setting updated. \n"
                        + "Please right-click in the plot area and select Customise plot..."
                        + " to adjust plot settings."
                    )
                    print(msg)
                    continue
                plot.plot_update_axes(axes_sizes)
                plot.repaint()
                plot._axes = axes_sizes
        except (AttributeError, UnboundLocalError):
            logger.warning("Failed to resize plot")

    def plot_update_size(self, plotName):
        dpi = wx.ScreenDC().GetPPI()
        resizeSize = self.config._plotSettings[plotName]["gui_size"]
        figsizeNarrowPix = (int(resizeSize[0] * dpi[0]), int(resizeSize[1] * dpi[1]))

        plot_obj = self.get_plot_from_name(plotName)
        if plot_obj is None:
            return

        try:
            if plot_obj.lock_plot_from_updating:
                msg = (
                    "This plot is locked and you cannot use global setting updated. \n"
                    + "Please right-click in the plot area and select Customise plot..."
                    + " to adjust plot settings."
                )
                print(msg)
                return
            plot_obj.SetSize(figsizeNarrowPix)
        except (AttributeError, UnboundLocalError):
            logger.warning("Failed to update plot size")

    def on_change_plot_style(self, evt, plot_style=None):
        # https://tonysyu.github.io/raw_content/matplotlib-style-gallery/gallery.html

        if self.config.currentStyle == "Default":
            matplotlib.rcParams.update(matplotlib.rcParamsDefault)
        elif self.config.currentStyle == "ggplot":
            plt.style.use("ggplot")
        elif self.config.currentStyle == "ticks":
            sns.set_style("ticks")
        else:
            plt.style.use(self.config.currentStyle)

    def on_change_color_palette(self, evt, cmap=None, n_colors=16, return_colors=False, return_hex=False):
        if cmap is not None:
            palette_name = cmap
        else:
            if self.config.currentPalette in ["Spectral", "RdPu"]:
                palette_name = self.config.currentPalette
            else:
                palette_name = self.config.currentPalette.lower()

        new_colors = sns.color_palette(palette_name, n_colors)

        if not return_colors:
            for i in range(n_colors):
                self.config.customColors[i] = convert_rgb_1_to_255(new_colors[i])
        else:
            if return_hex:
                new_colors_hex = []
                for new_color in new_colors:
                    new_colors_hex.append(convert_rgb_1_to_hex(new_color))
                return new_colors_hex
            else:
                return new_colors

    def on_get_colors_from_colormap(self, n_colors):
        colorlist = sns.color_palette(self.config.currentCmap, n_colors)
        return colorlist

    def get_colorList(self, count):
        colorList = sns.color_palette("cubehelix", count)
        colorList_return = []
        for color in colorList:
            colorList_return.append(convert_rgb_1_to_255(color))

        return colorList_return

    def on_clear_plot(self, evt, plot=None, **kwargs):
        """Clear selected plot

        Action can be invoked directly by wxEvent or by simply calling this fcn with appropriate keyword

        Parameters
        ----------
        evt : wxEvent
            event ID
        plot : str
            name of plot to be cleared
        kwargs : optional, dict
            dictionary with plot to be cleared
        """

        eventID = None
        if evt is not None:
            eventID = evt.GetId()

        if eventID is None:
            plot_obj = self.get_plot_from_name(plot)
        elif eventID is not None:
            plot_obj = self.get_plot_from_id(eventID)
        elif "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.pop("plot_obj")

        if not isinstance(plot_obj, list):
            plot_obj = [plot_obj]

        for p in plot_obj:
            p.clear()

        logger.info("Cleared plot area...")

    def on_clear_all_plots(self, evt=None):

        # Delete all plots
        plotList = [
            self.plot_ms,
            self.plot_rt_rt,
            self.plot_dt_dt,
            self.plot_heatmap,
            self.plot_heatmap_3d,
            self.plot_overlay,
            self.plot_msdt,
            self.plot_annotated,
            self.plot_rt_ms,
            self.plot_dt_ms,
        ]

        for plot in plotList:
            plot.clear()
            plot.repaint()
        # Message
        logger.info("Cleared all plots")

    def on_clear_patches(self, plot="MS", repaint=False, **kwargs):

        if plot == "MS":
            self.plot_ms.plot_remove_patches()
            if repaint:
                self.plot_ms.repaint()

        elif plot == "CalibrationMS":
            self.topPlotMS.plot_remove_patches()
            if repaint:
                self.topPlotMS.repaint()

        elif plot == "RT":
            self.plot_rt_rt.plot_remove_patches()
            if repaint:
                self.plot_rt_rt.repaint()

        elif "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
            plot_obj.plot_remove_patches()
            if repaint:
                plot_obj.repaint()

    def plot_repaint(self, plot_window="MS"):
        if plot_window == "MS":
            self.plot_ms.repaint()

    def plot_remove_patches_with_labels(self, label, plot_window="2D", refresh=False):
        if plot_window == "MS":
            self.plot_ms.plot_remove_patch_with_label(label)

            if refresh:
                self.plot_ms.repaint()

    def on_plot_patches(
        self, xmin, ymin, width, height, color="r", alpha=0.5, label="", plot="MS", repaint=False, **kwargs
    ):

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.pop("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)

        plot_obj.plot_add_patch(xmin, ymin, width, height, color=color, alpha=alpha, label=label, **kwargs)
        if repaint:
            plot_obj.repaint()

    def on_clear_labels(self, plot="MS", **kwargs):
        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)

        plot_obj.plot_remove_text_and_lines()

    def on_plot_labels(self, xpos, yval, label="", plot="MS", repaint=False, optimise_labels=False, **kwargs):

        plt_kwargs = {
            "horizontalalignment": kwargs.pop("horizontal_alignment", "center"),
            "verticalalignment": kwargs.pop("vertical_alignment", "center"),
            "check_yscale": kwargs.pop("check_yscale", False),
            "butterfly_plot": kwargs.pop("butterfly_plot", False),
            "fontweight": kwargs.pop("font_weight", "normal"),
            "fontsize": kwargs.pop("font_size", "medium"),
        }

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)

        if plot == "MS":
            plot_obj.plot_add_text(xpos, yval, label, yoffset=kwargs.get("yoffset", 0.0), **plt_kwargs)
        elif plot == "CalibrationMS":
            plot_obj.plot_add_text(xpos, yval, label, **plt_kwargs)

        elif "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj.plot_add_text(xpos, yval, label, **plt_kwargs)

        if optimise_labels:
            plot_obj._fix_label_positions()

        if not repaint:
            return

        self.plot_ms.repaint()

    def on_plot_markers(self, xvals, yvals, color="b", marker="o", size=5, plot="MS", repaint=True, **kwargs):
        if plot == "MS":
            self.plot_ms.plot_add_markers(
                xvals=xvals, yvals=yvals, color=color, marker=marker, size=size, test_yvals=True
            )
            if not repaint:
                return
            else:
                self.plot_ms.repaint()

        elif plot == "RT":
            self.plot_rt_rt.plot_add_markers(xvals=xvals, yvals=yvals, color=color, marker=marker, size=size)
            self.plot_rt_rt.repaint()
        # elif plot == "CalibrationMS":
        #     self.topPlotMS.plot_add_markers(xval=xvals, yval=yvals, color=color, marker=marker, size=size)
        #     self.topPlotMS.repaint()
        # elif plot == "CalibrationDT":
        #     self.bottomPlot1DT.plot_add_markers(
        #         xvals=xvals, yvals=yvals, color=color, marker=marker, size=size, testMax="yvals"
        #     )
        #     self.bottomPlot1DT.repaint()

    def on_clear_markers(self, plot="MS", repaint=False, **kwargs):

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
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
        if kwargs["color_scheme"] == "Colormap":
            colorlist = sns.color_palette(kwargs["colormap"], n_count)
        elif kwargs["color_scheme"] == "Color palette":
            if kwargs["palette"] not in ["Spectral", "RdPu"]:
                kwargs["palette"] = kwargs["palette"].lower()
            colorlist = sns.color_palette(kwargs["palette"], n_count)
        elif kwargs["color_scheme"] == "Same color":
            colorlist = [kwargs["line_color"]] * n_count
        elif kwargs["color_scheme"] == "Random":
            colorlist = []
            for __ in range(n_count):
                colorlist.append(get_random_color())

        return colorlist

    def _on_change_unidec_page(self, page_id, **kwargs):
        if self.config.unidec_plot_panel_view == "Tabbed view" and kwargs.get("set_page", False):
            try:
                self.unidec_notebook.SetSelection(page_id)
            except Exception:
                pass

    def on_plot_charge_states(self, position, charges, plot="UniDec_peaks", **kwargs):

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)
            self._on_change_unidec_page(4, **kwargs)

        plot_obj.plot_remove_text_and_lines()

        if self.config.unidec_show_chargeStates:
            for position, charge in zip(position, charges):
                plot_obj.plot_add_text_and_lines(
                    xpos=position, yval=self.config.unidec_charges_offset, label=charge, stick_to_intensity=True
                )
        plot_obj.repaint()

    def on_add_horizontal_line(self, xmin, xmax, yval, plot_obj):
        plot_obj.plot_add_line(xmin, xmax, yval, yval, "horizontal")
        plot_obj.repaint()

    def on_plot_unidec_ChargeDistribution(
        self, xvals=None, yvals=None, replot=None, xlimits=None, plot="UniDec_charge", **kwargs
    ):
        """
        Plot simple Mass spectrum before it is pre-processed
        @param unidec_eng_data (object):  reference to unidec engine data structure
        @param xlimits: unused
        """

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)
            self._on_change_unidec_page(6, **kwargs)

        if replot is not None:
            xvals = replot[:, 0]
            yvals = replot[:, 1]

        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType="1D")

        plot_obj.clear()
        plot_obj.plot_1D(
            xvals=xvals,
            yvals=yvals,
            xlimits=xlimits,
            xlabel="Charge",
            ylabel="Intensity",
            testMax=None,
            axesSize=self.config._plotSettings["UniDec (Charge Distribution)"]["axes_size"],
            plotType="ChargeDistribution",
            title="Charge State Distribution",
            allowWheel=False,
            **plt_kwargs,
        )
        # Show the mass spectrum
        plot_obj.repaint()

    def on_plot_unidec_MS(self, unidec_eng_data=None, replot=None, xlimits=None, plot="UniDec_MS", **kwargs):
        """
        Plot simple Mass spectrum before it is pre-processed
        @param unidec_eng_data (object):  reference to unidec engine data structure
        @param xlimits: unused
        """

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)
            self._on_change_unidec_page(0, **kwargs)

        plt_kwargs = self._buildPlotParameters(plotType="1D")

        if unidec_eng_data is None and replot is not None:
            xvals = replot["xvals"]
            yvals = replot["yvals"]

        plot_obj.clear()
        plot_obj.plot_1D(
            xvals=xvals,
            yvals=yvals,
            xlimits=xlimits,
            xlabel="m/z",
            ylabel="Intensity",
            axesSize=self.config._plotSettings["UniDec (MS)"]["axes_size"],
            plotType="MS",
            title="MS",
            allowWheel=False,
            **plt_kwargs,
        )
        # Show the mass spectrum
        plot_obj.repaint()

    def on_plot_unidec_MS_v_Fit(self, unidec_eng_data=None, replot=None, xlimits=None, plot="UniDec_MS", **kwargs):

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)
            self._on_change_unidec_page(0, **kwargs)

        # Build kwargs
        plt_kwargs = self._buildPlotParameters(["1D", "UniDec"])

        if unidec_eng_data is None and replot is not None:
            xvals = replot["xvals"]
            yvals = replot["yvals"]
            colors = replot["colors"]
            labels = replot["labels"]

        colors[1] = plt_kwargs["fit_line_color"]

        plot_obj.clear()
        plot_obj.plot_1D_overlay(
            xvals=xvals,
            yvals=yvals,
            labels=labels,
            colors=colors,
            xlimits=xlimits,
            xlabel="m/z",
            ylabel="Intensity",
            axesSize=self.config._plotSettings["UniDec (MS)"]["axes_size"],
            plotType="MS",
            title="MS and UniDec Fit",
            allowWheel=False,
            **plt_kwargs,
        )
        # Show the mass spectrum
        plot_obj.repaint()

    def on_plot_unidec_mzGrid(self, unidec_eng_data=None, replot=None, plot="UniDec_mz_v_charge", **kwargs):
        """
        Plot simple Mass spectrum before it is pre-processed
        """

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)
            self._on_change_unidec_page(1, **kwargs)

        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType="2D")
        plt_kwargs["contour_levels"] = self.config.unidec_plot_contour_levels
        plt_kwargs["colorbar"] = True

        if unidec_eng_data is None and replot is not None:
            grid = replot["grid"]

        plot_obj.clear()
        plot_obj.plot_2D_contour_unidec(
            data=grid,
            xlabel="m/z (Da)",
            ylabel="Charge",
            axesSize=self.config._plotSettings["UniDec (m/z vs Charge)"]["axes_size"],
            plotType="2D",
            plotName="mzGrid",
            speedy=kwargs.get("speedy", True),
            title="m/z vs Charge",
            allowWheel=False,
            **plt_kwargs,
        )
        # Show the mass spectrum
        plot_obj.repaint()

    def on_plot_unidec_mwDistribution(
        self, unidec_eng_data=None, replot=None, xlimits=None, plot="UniDec_MW", **kwargs
    ):

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)
            self._on_change_unidec_page(3, **kwargs)

        # Build kwargs
        plt_kwargs = self._buildPlotParameters(["1D", "UniDec"])

        if unidec_eng_data is None and replot is not None:
            xvals = replot["xvals"]
            yvals = replot["yvals"]

        try:
            plot_obj.plot_1D_update_data(xvals, yvals, "Mass Distribution", "Intensity", testX=True, **plt_kwargs)
        except AttributeError:
            plot_obj.clear()
            plot_obj.plot_1D(
                xvals=xvals,
                yvals=yvals,
                xlimits=xlimits,
                xlabel="Mass Distribution",
                ylabel="Intensity",
                axesSize=self.config._plotSettings["UniDec (MW)"]["axes_size"],
                plotType="mwDistribution",
                testMax=None,
                testX=True,
                title="Zero-charge Mass Spectrum",
                allowWheel=False,
                **plt_kwargs,
            )
        plot_obj.repaint()

    def on_plot_unidec_MW_add_markers(self, data, mw_data, plot="UniDec_MW", **kwargs):
        """Add markers to the MW plot to indicate found peaks"""

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)
            self._on_change_unidec_page(1, **kwargs)

        # remove all markers
        plot_obj.plot_remove_markers()

        # build plot parameters
        plt_kwargs = self._buildPlotParameters(["1D", "UniDec"])

        # get legend text
        legend_text = data["legend_text"]
        mw = np.transpose([mw_data["xvals"], mw_data["yvals"]])

        num = 0
        for key in natsorted(list(data.keys())):
            if key.split(" ")[0] != "MW:":
                continue
            if num >= plt_kwargs["maximum_shown_items"]:
                continue
            num += 1

        # get color list
        colors = self._get_color_list(None, count=num, **plt_kwargs)

        num = 0
        for key in natsorted(list(data.keys())):
            if key.split(" ")[0] != "MW:":
                continue
            if num >= plt_kwargs["maximum_shown_items"]:
                continue

            xval = float(key.split(" ")[1])
            yval = unidec_utils.get_peak_maximum(mw, xval=xval)
            marker = data[key]["marker"]
            color = colors[num]

            plot_obj.plot_add_markers(
                xval, yval, color=color, marker=marker, size=plt_kwargs["MW_marker_size"], label=key, test_xvals=True
            )
            num += 1

        plot_obj.plot_1D_add_legend(legend_text, **plt_kwargs)
        plot_obj.repaint()

    def on_plot_unidec_individualPeaks(
        self, unidec_eng_data=None, replot=None, xlimits=None, plot="UniDec_peaks", **kwargs
    ):
        """
        Plot simple Mass spectrum before it is pre-processed
        @param unidec_eng_data (object):  reference to unidec engine data structure
        @param xlimits: unused
        """

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)
            self._on_change_unidec_page(4, **kwargs)

        # Build kwargs
        plt_kwargs = self._buildPlotParameters(["1D", "UniDec"])

        if unidec_eng_data is None and replot is not None:
            xvals = replot["xvals"]
            yvals = replot["yvals"]

        # Plot MS
        plot_obj.clear()
        plot_obj.plot_1D(
            xvals=xvals,
            yvals=yvals,
            xlimits=xlimits,
            xlabel="m/z",
            ylabel="Intensity",
            axesSize=self.config._plotSettings["UniDec (Isolated MS)"]["axes_size"],
            plotType="pickedPeaks",
            label="Raw",
            allowWheel=False,
            **plt_kwargs,
        )
        plot_obj.repaint()

        # add lines and markers
        self.on_plot_unidec_add_individual_lines_and_markers(replot=replot, plot=plot, **kwargs)

    def on_plot_unidec_add_individual_lines_and_markers(
        self, unidec_eng_data=None, replot=None, plot="UniDec_peaks", **kwargs
    ):

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)
            self._on_change_unidec_page(4, **kwargs)

        # remove all markers/lines and reset y-axis zoom
        plot_obj.plot_remove_markers()
        plot_obj.plot_remove_lines("MW:")
        plot_obj.plot_remove_text_and_lines()
        plot_obj.on_zoom_y_axis(0)

        # Build kwargs
        plt_kwargs = self._buildPlotParameters(["1D", "UniDec"])

        if unidec_eng_data is None and replot is not None:
            legend_text = replot["legend_text"]

        if kwargs.get("show_isolated_mw", False):
            legend_text = [[[0, 0, 0], "Raw"]]

        # get number of lines in the dataset
        num = 0
        color_num = 0
        for key in natsorted(list(replot.keys())):
            if key.split(" ")[0] != "MW:":
                continue
            color_num += 1
            if num >= plt_kwargs["maximum_shown_items"]:
                continue
            num += 1

        # get colorlist
        colors = self._get_color_list(None, count=color_num, **plt_kwargs)

        # iteratively add lines
        num, mw_num = 0, 0
        for key in natsorted(list(replot.keys())):
            if not kwargs["show_markers"] and not kwargs["show_individual_lines"]:
                break

            if key.split(" ")[0] != "MW:":
                continue
            if num >= plt_kwargs["maximum_shown_items"]:
                continue

            scatter_yvals = replot[key]["scatter_yvals"]
            line_yvals = replot[key]["line_yvals"]
            if kwargs.get("show_isolated_mw", False):
                if key != kwargs["mw_selection"]:
                    mw_num += 1
                    continue
                else:
                    print(len(colors), mw_num)
                    color = colors[mw_num]
                    legend_text.append([color, replot[key]["label"]])
                    # adjust offset so its closer to the MS plot
                    offset = np.min(replot[key]["line_yvals"]) + self.config.unidec_lineSeparation
                    line_yvals = line_yvals - offset
            else:
                color = colors[num]
                legend_text[num + 1][0] = color

            # plot markers
            if kwargs["show_markers"]:
                plot_obj.plot_add_markers(
                    replot[key]["scatter_xvals"],
                    scatter_yvals,
                    color=color,  # colors[num],
                    marker=replot[key]["marker"],
                    size=plt_kwargs["isolated_marker_size"],
                    label=replot[key]["label"],
                )
            # plot lines
            if kwargs["show_individual_lines"]:
                plot_obj.plot_1D_add(
                    replot[key]["line_xvals"],
                    line_yvals,
                    color=color,
                    label=replot[key]["label"],
                    allowWheel=False,
                    plot_name="pickedPeaks",
                    update_extents=True,
                    setup_zoom=False,
                    **plt_kwargs,
                )
            num += 1

        # modify legend
        if len(legend_text) - 1 > plt_kwargs["maximum_shown_items"]:
            msg = (
                "Only showing {} out of {} items.".format(plt_kwargs["maximum_shown_items"], len(legend_text) - 1)
                + " If you would like to see more go to Processing -> UniDec -> Max shown"
            )
            logger.info(msg)

        legend_text = legend_text[: num + 1]
        # Add legend
        if len(legend_text) >= plt_kwargs["maximum_shown_items"]:
            legend_text = legend_text[: plt_kwargs["maximum_shown_items"]]

        plot_obj.plot_1D_add_legend(legend_text, **plt_kwargs)
        plot_obj.repaint()

    def on_plot_unidec_MW_v_Charge(self, unidec_eng_data=None, replot=None, plot="UniDec_mw_v_charge", **kwargs):
        """
        Plot simple Mass spectrum before it is pre-processed
        @param unidec_eng_data (object):  reference to unidec engine data structure
        """

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)
            self._on_change_unidec_page(2, **kwargs)

        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType="2D")
        plt_kwargs["contour_levels"] = self.config.unidec_plot_contour_levels
        plt_kwargs["colorbar"] = True

        if unidec_eng_data is None and replot is not None:
            xvals = replot["xvals"]
            yvals = replot["yvals"]
            zvals = replot["zvals"]
        else:
            xvals = unidec_eng_data.massdat[:, 0]
            yvals = unidec_eng_data.ztab
            zvals = unidec_eng_data.massgrid

        # Check that cmap modifier is included
        cmapNorm = self.normalize_colormap(
            zvals, min=self.config.minCmap, mid=self.config.midCmap, max=self.config.maxCmap
        )
        plt_kwargs["colormap_norm"] = cmapNorm

        plot_obj.clear()
        plot_obj.plot_2D_contour_unidec(
            xvals=xvals,
            yvals=yvals,
            zvals=zvals,
            xlabel="Mass (Da)",
            ylabel="Charge",
            axesSize=self.config._plotSettings["UniDec (MW vs Charge)"]["axes_size"],
            plotType="MS",
            plotName="mwGrid",
            testX=True,
            speedy=kwargs.get("speedy", True),
            title="Mass vs Charge",
            **plt_kwargs,
        )
        # Show the mass spectrum
        plot_obj.repaint()

    def on_plot_unidec_barChart(self, unidec_eng_data=None, replot=None, show="height", plot="UniDec_bar", **kwargs):
        """
        Plot simple Mass spectrum before it is pre-processed
        @param unidec_eng_data (object):  reference to unidec engine data structure
        """

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)
            self._on_change_unidec_page(5, **kwargs)

        # Build kwargs
        plt_kwargs = self._buildPlotParameters(["1D", "UniDec"])

        if unidec_eng_data is None and replot is not None:
            xvals = replot["xvals"]
            yvals = replot["yvals"]
            labels = replot["labels"]
            colors = replot["colors"]
            legend_text = replot["legend_text"]
            markers = replot["markers"]

            if len(xvals) > plt_kwargs["maximum_shown_items"]:
                msg = (
                    "Only showing {} out of {} items.".format(plt_kwargs["maximum_shown_items"], len(xvals))
                    + " If you would like to see more go to Processing -> UniDec -> Max shown"
                )
                self.presenter.onThreading(None, (msg, 4, 7), action="updateStatusbar")

            if len(xvals) >= plt_kwargs["maximum_shown_items"]:
                xvals = xvals[: plt_kwargs["maximum_shown_items"]]
                yvals = yvals[: plt_kwargs["maximum_shown_items"]]
                labels = labels[: plt_kwargs["maximum_shown_items"]]
                colors = colors[: plt_kwargs["maximum_shown_items"]]
                legend_text = legend_text[: plt_kwargs["maximum_shown_items"]]
                markers = markers[: plt_kwargs["maximum_shown_items"]]

        colors = self._get_color_list(colors, **plt_kwargs)
        for i in range(len(legend_text)):
            legend_text[i][0] = colors[i]

        plot_obj.clear()
        plot_obj.plot_1D_barplot(
            xvals,
            yvals,
            labels,
            colors,
            axesSize=self.config._plotSettings["UniDec (Barplot)"]["axes_size"],
            title="Peak Intensities",
            ylabel="Intensity",
            plotType="Barchart",
            **plt_kwargs,
        )

        if unidec_eng_data is None and replot is not None:
            if kwargs["show_markers"]:
                for i in range(len(markers)):
                    if i >= plt_kwargs["maximum_shown_items"]:
                        continue
                    plot_obj.plot_add_markers(
                        xvals[i], yvals[i], color=colors[i], marker=markers[i], size=plt_kwargs["bar_marker_size"]
                    )

        # Add legend
        plot_obj.plot_1D_add_legend(legend_text, **plt_kwargs)
        plot_obj.repaint()

    def plot_1D_update(self, plotName="all"):

        plt_kwargs = self._buildPlotParameters(plotType="1D")

        if plotName in ["all", "MS"]:
            try:
                self.plot_ms.plot_1D_update(**plt_kwargs)
                self.plot_ms.repaint()
            except AttributeError:
                logger.warning("Failed to update `Mass spectrum` plot", exc_info=True)

        if plotName in ["all", "RT"]:
            try:
                self.plot_rt_rt.plot_1D_update(**plt_kwargs)
                self.plot_rt_rt.repaint()
            except AttributeError:
                logger.warning("Failed to update `Chromatogram` plot", exc_info=True)

        if plotName in ["all", "1D"]:
            try:
                self.plot_dt_dt.plot_1D_update(**plt_kwargs)
                self.plot_dt_dt.repaint()
            except AttributeError:
                logger.warning("Failed to update `Mobilogram` plot", exc_info=True)

        if plotName in ["all", "RMSF"]:
            plt_kwargs = self._buildPlotParameters(["1D", "2D", "RMSF"])

            plot_obj = self.get_plot_from_name("RMSF")
            try:
                plot_obj.plot_1D_update_rmsf(**plt_kwargs)
                plot_obj.repaint()
            except AttributeError:
                logger.warning("Failed to update `RMSF` plot", exc_info=True)

    #         if plotName in ["all", "1D", "MS", "RT", "RMSF"]:
    #             plot_obj = self.get_plot_from_name(plotName)
    #             plot_obj.plot_1D_update(**plt_kwargs)
    #             plot_obj.repaint()

    def on_plot_other_1D(
        self, msX=None, msY=None, xlabel="", ylabel="", xlimits=None, set_page=False, plot="Other", **kwargs
    ):

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)
            if set_page:
                self._set_page(self.config.panelNames["Other"])

        plt_kwargs = self._buildPlotParameters(plotType="1D")
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

        plot_obj.clear()
        plot_obj.plot_1D(
            xvals=msX,
            yvals=msY,
            xlimits=xlimits,
            xlabel=xlabel,
            ylabel=ylabel,
            axesSize=self.config._plotSettings["Other (Line)"]["axes_size"],
            plotType="MS",
            **plt_kwargs,
        )
        plot_obj.repaint()
        plot_obj.plot_type = "line"

    def on_plot_other_overlay(
        self, xvals, yvals, xlabel, ylabel, colors, labels, xlimits=None, set_page=False, plot="Other", **kwargs
    ):

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)
            if set_page:
                self._set_page(self.config.panelNames["Other"])
        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType="1D")
        plt_kwargs = merge_two_dicts(plt_kwargs, kwargs)

        plot_obj.clear()
        plot_obj.plot_1D_overlay(
            xvals=xvals,
            yvals=yvals,
            title="",
            xlabel=xlabel,
            ylabel=ylabel,
            labels=labels,
            colors=colors,
            xlimits=xlimits,
            zoom="box",
            axesSize=self.config._plotSettings["Other (Multi-line)"]["axes_size"],
            plotName="1D",
            **plt_kwargs,
        )
        plot_obj.repaint()
        plot_obj.plot_type = "multi-line"

    def on_plot_other_waterfall(
        self, xvals, yvals, zvals, xlabel, ylabel, colors=[], set_page=False, plot="Other", **kwargs
    ):
        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)
            if set_page:
                self._set_page(self.config.panelNames["Other"])

        plt_kwargs = self._buildPlotParameters(["1D", "waterfall"])
        if "increment" in kwargs:
            plt_kwargs["increment"] = kwargs["increment"]

        # reverse labels
        xlabel, ylabel = ylabel, xlabel

        plot_obj.clear()
        plot_obj.plot_1D_waterfall(
            xvals=xvals,
            yvals=yvals,
            zvals=zvals,
            label="",
            xlabel=xlabel,
            ylabel=ylabel,
            colorList=colors,
            labels=kwargs.get("labels", []),
            axesSize=self.config._plotSettings["Other (Waterfall)"]["axes_size"],
            plotName="1D",
            **plt_kwargs,
        )

        #         if ('add_legend' in kwargs and 'labels' in kwargs and
        #             len(colors) == len(kwargs['labels'])):
        #             if kwargs['add_legend']:
        #                 legend_text = zip(colors, kwargs['labels'])
        #                 plot_obj.plot_1D_add_legend(legend_text, **plt_kwargs)

        plot_obj.repaint()
        plot_obj.plot_type = "waterfall"

    def on_plot_other_scatter(
        self, xvals, yvals, zvals, xlabel, ylabel, colors, labels, xlimits=None, set_page=False, plot="Other", **kwargs
    ):

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)
            if set_page:
                self._set_page(self.config.panelNames["Other"])

        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType="1D")
        plt_kwargs = merge_two_dicts(plt_kwargs, kwargs)

        plot_obj.clear()
        plot_obj.plot_1D_scatter(
            xvals=xvals,
            yvals=yvals,
            zvals=zvals,
            title="",
            xlabel=xlabel,
            ylabel=ylabel,
            labels=labels,
            colors=colors,
            xlimits=xlimits,
            zoom="box",
            axesSize=self.config._plotSettings["Other (Scatter)"]["axes_size"],
            plotName="1D",
            **plt_kwargs,
        )
        plot_obj.repaint()
        plot_obj.plot_type = "scatter"

    def on_plot_other_grid_1D(
        self, xvals, yvals, xlabel, ylabel, colors, labels, set_page=False, plot="Other", **kwargs
    ):

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)
            if set_page:
                self._set_page(self.config.panelNames["Other"])

        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType="1D")
        plt_kwargs = merge_two_dicts(plt_kwargs, kwargs)

        plot_obj.clear()
        plot_obj.plot_n_grid_1D_overlay(
            xvals=xvals,
            yvals=yvals,
            title="",
            xlabel=xlabel,
            ylabel=ylabel,
            labels=labels,
            colors=colors,
            zoom="box",
            axesSize=self.config._plotSettings["Other (Grid-1D)"]["axes_size"],
            plotName="1D",
            **plt_kwargs,
        )
        plot_obj.repaint()
        plot_obj.plot_type = "grid-line"

    def on_plot_other_grid_scatter(
        self, xvals, yvals, xlabel, ylabel, colors, labels, set_page=False, plot="Other", **kwargs
    ):

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)
            if set_page:
                self._set_page(self.config.panelNames["Other"])

        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType="1D")
        plt_kwargs = merge_two_dicts(plt_kwargs, kwargs)

        plot_obj.clear()
        plot_obj.plot_n_grid_scatter(
            xvals=xvals,
            yvals=yvals,
            title="",
            xlabel=xlabel,
            ylabel=ylabel,
            labels=labels,
            colors=colors,
            zoom="box",
            axesSize=self.config._plotSettings["Other (Grid-1D)"]["axes_size"],
            plotName="1D",
            **plt_kwargs,
        )
        plot_obj.repaint()
        plot_obj.plot_type = "grid-scatter"

    def on_plot_other_bars(
        self, xvals, yvals_min, yvals_max, xlabel, ylabel, colors, set_page=False, plot="Other", **kwargs
    ):

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)
            if set_page:
                self._set_page(self.config.panelNames["Other"])

        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType="1D")
        plt_kwargs = merge_two_dicts(plt_kwargs, kwargs)

        plot_obj.clear()
        plot_obj.plot_floating_barplot(
            xvals=xvals,
            yvals_min=yvals_min,
            yvals_max=yvals_max,
            itle="",
            xlabel=xlabel,
            ylabel=ylabel,
            colors=colors,
            zoom="box",
            axesSize=self.config._plotSettings["Other (Barplot)"]["axes_size"],
            **plt_kwargs,
        )
        plot_obj.repaint()
        plot_obj.plot_type = "bars"

    def _on_check_plot_names(self, document_name, dataset_name, plot_window):
        """
        Check if document name and dataset name match that of the plotted window
        """
        plot = None
        if plot_window == "MS":
            plot = self.plot_ms

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
        self,
        msX,
        msY,
        labels,
        full_labels,
        xlimits=None,
        title="",
        butterfly_plot=False,
        set_page=False,
        plot="MS",
        **kwargs,
    ):
        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)
            if set_page:
                self._set_page(self.config.panelNames["MS"])

        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType="1D")
        plt_kwargs["line_color"] = self.config.msms_line_color_labelled
        plt_kwargs["butterfly_plot"] = butterfly_plot

        plot_name = "MS"
        plot_size = self.config._plotSettings["MS"]["axes_size"]
        if butterfly_plot:
            plot_name = "compareMS"
            plot_size = self.config._plotSettings["MS (compare)"]["axes_size"]

        xylimits = self.plot_ms.get_xylimits()
        plot_obj.plot_1D_centroid(
            xvals=msX,
            yvals=msY,
            xlimits=xlimits,
            update_y_axis=False,
            xlabel="m/z",
            ylabel="Intensity",
            title=title,
            axesSize=plot_size,
            plot_name=plot_name,
            adding_on_top=True,
            **plt_kwargs,
        )

        # add labels
        plt_label_kwargs = {
            "horizontalalignment": self.config.annotation_label_horz,
            "verticalalignment": self.config.annotation_label_vert,
            "check_yscale": True,
            "add_arrow_to_low_intensity": self.config.msms_add_arrows,
            "butterfly_plot": butterfly_plot,
            "fontweight": self.config.annotation_label_font_weight,
            "fontsize": self.config.annotation_label_font_size,
            "rotation": self.config.annotation_label_font_orientation,
        }

        for i in range(len(labels)):
            xval, yval, label, full_label = msX[i], msY[i], labels[i], full_labels[i]

            if not self.config.msms_show_neutral_loss:
                if "H2O" in full_label or "NH3" in full_label:
                    continue

            if self.config.msms_show_full_label:
                label = full_label

            plot_obj.plot_add_text(
                xpos=xval, yval=yval, label=label, yoffset=self.config.msms_label_y_offset, **plt_label_kwargs
            )

        if i == len(labels) - 1 and not butterfly_plot:
            plot_obj.set_xy_limits(xylimits)

        plot_obj.repaint()

    def on_plot_centroid_MS(
        self, msX, msY, msXY=None, xlimits=None, title="", repaint=True, set_page=False, plot="MS", **kwargs
    ):
        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)
            if set_page:
                self._set_page(self.config.panelNames["MS"])

        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType="1D")
        plt_kwargs["line_color"] = self.config.msms_line_color_unlabelled

        plot_obj.clear()
        plot_obj.plot_1D_centroid(
            xvals=msX,
            yvals=msY,
            xyvals=msXY,
            xlimits=xlimits,
            xlabel="m/z",
            ylabel="Intensity",
            title=title,
            axesSize=self.config._plotSettings["MS"]["axes_size"],
            plotType="MS",
            **plt_kwargs,
        )
        if repaint:
            plot_obj.repaint()

    def on_clear_MS_annotations(self):

        try:
            self.on_clear_labels(plot="MS")
        except Exception:
            pass

        try:
            self.on_clear_patches(plot="MS")
        except Exception:
            pass

    def on_update_plot_1D(self, xvals, yvals, plot, **kwargs):

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)

        plot_obj.plot_1D_update_data_only(xvals, yvals)
        plot_obj.repaint()

    def on_simple_plot_1D(self, xvals, yvals, **kwargs):
        plot = kwargs.pop("plot", None)

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)

        # get kwargs
        plt_kwargs = self._buildPlotParameters(plotType="1D")

        try:
            plot_obj.plot_1D_update_data_only(xvals, yvals)
        except Exception as err:
            print(err)

            plot_obj.clear()
            plot_obj.plot_1D(
                xvals=xvals,
                yvals=yvals,
                xlabel=kwargs.pop("xlabel", ""),
                ylabel=kwargs.pop("ylabel", ""),
                plotType="1D",
                **plt_kwargs,
            )
        # show the plot
        plot_obj.repaint()

    def on_plot_scan_vs_voltage(self, xvals, yvals, plot=None, **kwargs):
        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)

        # get kwargs
        plt_kwargs = self._buildPlotParameters(plotType="1D")

        plot_obj.clear()
        plot_obj.plot_1D(
            xvals=xvals,
            yvals=yvals,
            xlabel=kwargs.pop("xlabel", ""),
            ylabel=kwargs.pop("ylabel", ""),
            plotType="1D",
            testMax=None,
            axesSize=[0.17, 0.17, 0.75, 0.75],
            **plt_kwargs,
        )
        # show the plot
        plot_obj.repaint()

    def on_plot_1D_annotations(self, annotations_obj, plot="MS", **kwargs):
        from origami.utils.labels import _replace_labels

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)

        label_kwargs = self._buildPlotParameters(plotType="label")
        arrow_kwargs = self._buildPlotParameters(plotType="arrow")
        vline = False
        _ymax = []

        if len(annotations_obj) > 1:
            plot_obj.plot_remove_text_and_lines()
            plot_obj.plot_remove_patches()
            plot_obj.plot_remove_arrows()

        label_fmt = kwargs.pop("label_fmt", "all")
        pin_to_intensity = kwargs.pop("pin_to_intensity", True)
        document_title = kwargs.pop("document_title")
        dataset_type = kwargs.pop("dataset_type")
        dataset_name = kwargs.pop("dataset_name")
        show_names = kwargs.pop("show_names", None)

        for name, annotation_obj in annotations_obj.items():
            if show_names is not None and name not in show_names:
                continue

            if label_fmt == "charge":
                show_label = f"z={annotation_obj.charge:d}"
            elif label_fmt == "label":
                show_label = _replace_labels(annotation_obj.label)
            elif label_fmt == "patch":
                show_label = ""
            else:
                show_label = "{:.2f}, {}\nz={}".format(
                    annotation_obj.position_x, annotation_obj.position_y, annotation_obj.charge
                )

            # add  custom name tag
            obj_name_tag = f"{document_title}|-|{dataset_type}|-|{dataset_name}|-|{name}|-|annotation"
            label_kwargs["text_name"] = obj_name_tag

            # add patch
            if annotation_obj.patch_show:
                plot_obj.plot_add_patch(
                    annotation_obj.patch_position[0],
                    annotation_obj.patch_position[1],
                    annotation_obj.width,
                    annotation_obj.height,
                    color=annotation_obj.patch_color,
                    alpha=self.config.annotation_patch_transparency,
                    label=obj_name_tag,
                )
            else:
                plot_obj._remove_existing_patch(obj_name_tag)

            _ymax.append(annotation_obj.label_position_y)
            if show_label != "" and annotation_obj.arrow_show and pin_to_intensity:
                # arrows have 4 positional parameters:
                #    xpos, ypos = correspond to the label position
                #    dx, dy = difference between label position and peak position
                arrow_list, arrow_x_end, arrow_y_end = annotation_obj.get_arrow_position()

                arrow_kwargs["text_name"] = obj_name_tag
                arrow_kwargs["props"] = [arrow_x_end, arrow_y_end]
                plot_obj.plot_add_arrow(arrow_list, stick_to_intensity=pin_to_intensity, **arrow_kwargs)
            else:
                plot_obj._remove_existing_arrow(obj_name_tag)

            # add label to the plot
            if show_label != "":
                plot_obj.plot_add_text_and_lines(
                    xpos=annotation_obj.label_position_x,
                    yval=annotation_obj.label_position_y,
                    label=show_label,
                    vline=vline,
                    vline_position=annotation_obj.position_x,
                    stick_to_intensity=pin_to_intensity,
                    yoffset=self.config.annotation_label_y_offset,
                    color=annotation_obj.label_color,
                    **label_kwargs,
                )

        if self.config.annotation_zoom_y:
            try:
                plot_obj.on_zoom_y_axis(endY=np.amax(_ymax) * self.config.annotation_zoom_y_multiplier)
            except TypeError:
                logger.warning("Failed to zoom in on plot/annotation", exc_info=True)

        plot_obj.repaint()

    def on_plot_MS(
        self,
        msX=None,
        msY=None,
        xlimits=None,
        override=True,
        replot=False,
        full_repaint=False,
        set_page=False,
        show_in_window="MS",
        view_range=None,
        obj=None,
        **kwargs,
    ):

        # Build kwargs
        if view_range is None:
            view_range = []
        plt_kwargs = self._buildPlotParameters(plotType="1D")

        window = self.config.panelNames["MS"]

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(show_in_window)

        if plot_obj == self.plot_ms:
            self.view_ms.plot(msX, msY, obj=obj, **kwargs, **plt_kwargs)
            return
        elif plot_obj == self.plot_rt_ms:
            if obj:
                self.view_rt_ms.plot(obj=obj)
            else:
                self.view_rt_ms.plot(msX, msY, **kwargs, **plt_kwargs)
        elif plot_obj == self.plot_dt_ms:
            if obj:
                self.view_dt_ms.plot(obj=obj)
            else:
                self.view_dt_ms.plot(msX, msY, **kwargs, **plt_kwargs)
        else:
            window = None
            if show_in_window == "LESA":
                plot_size_key = "MS (DT/RT)"
            else:
                plot_size_key = "MS"

        # change page
        if set_page and window is not None:
            self._set_page(window)

        if replot:
            msX, msY, xlimits = self.get_replot_data("MS")
            if msX is None or msY is None:
                return

        # setup names
        if "document" in kwargs:
            plot_obj.document_name = kwargs["document"]
            plot_obj.dataset_name = kwargs["dataset"]

        if not full_repaint:
            try:
                plot_obj.plot_1D_update_data(msX, msY, "m/z", "Intensity", **plt_kwargs)
                if len(view_range):
                    self.on_zoom_1D_x_axis(startX=view_range[0], endX=view_range[1], repaint=False, plot="MS")
                plot_obj.repaint()
                if override:
                    self.config.replotData["MS"] = {"xvals": msX, "yvals": msY, "xlimits": xlimits}
                return
            except AttributeError:
                logger.warning("Failed to quickly plot MS data")

        # check limits
        try:
            if math.isnan(xlimits.get(0, msX[0])):
                xlimits[0] = msX[0]
            if math.isnan(xlimits.get(1, msX[-1])):
                xlimits[1] = msX[-1]
        except Exception:
            xlimits = [np.min(msX), np.max(msX)]

        plot_obj.clear()
        plot_obj.plot_1D(
            xvals=msX,
            yvals=msY,
            xlimits=xlimits,
            xlabel="m/z",
            ylabel="Intensity",
            axesSize=self.config._plotSettings[plot_size_key]["axes_size"],
            plotType="MS",
            callbacks=kwargs.get("callbacks", dict()),
            **plt_kwargs,
        )
        # Show the mass spectrum
        plot_obj.repaint()

        if override:
            self.config.replotData["MS"] = {"xvals": msX, "yvals": msY, "xlimits": xlimits}

    def on_plot_1D(
        self,
        dtX=None,
        dtY=None,
        xlabel=None,
        override=True,
        full_repaint=False,
        replot=False,
        set_page=False,
        plot="1D",
        obj=None,
        **kwargs,
    ):
        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)
            if set_page:
                self._set_page(self.config.panelNames["1D"])

        if replot:
            dtX, dtY, xlabel = self.get_replot_data("1D")
            if dtX is None or dtY is None or xlabel is None:
                return

        # get kwargs
        plt_kwargs = self._buildPlotParameters(plotType="1D")

        if plot_obj == self.plot_dt_dt:
            self.view_dt_dt.plot(dtX, dtY, obj=obj, **plt_kwargs)
            return

        plt_kwargs["allow_extraction"] = kwargs.pop("allow_extraction", True)
        if not full_repaint:
            try:
                plot_obj.plot_1D_update_data(dtX, dtY, xlabel, "Intensity", **plt_kwargs)
                plot_obj.repaint()
                if override:
                    self.config.replotData["1D"] = {"xvals": dtX, "yvals": dtY, "xlabel": xlabel}
                    return
            except Exception:
                pass

        plot_obj.clear()
        plot_obj.plot_1D(
            xvals=dtX,
            yvals=dtY,
            xlabel=xlabel,
            ylabel="Intensity",
            axesSize=self.config._plotSettings["DT"]["axes_size"],
            plotType="1D",
            callbacks=kwargs.get("callbacks", dict()),
            **plt_kwargs,
        )
        plot_obj.repaint()

        if override:
            self.config.replotData["1D"] = {"xvals": dtX, "yvals": dtY, "xlabel": xlabel}

    def on_plot_RT(
        self,
        rtX=None,
        rtY=None,
        xlabel=None,
        ylabel="Intensity",
        override=True,
        replot=False,
        full_repaint=False,
        set_page=False,
        plot="RT",
        obj=None,
        **kwargs,
    ):

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)
            if set_page:
                self._set_page(self.config.panelNames["RT"])

        if replot:
            rtX, rtY, xlabel = self.get_replot_data("RT")
            if rtX is None or rtY is None or xlabel is None:
                return

        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType="1D")

        if plot_obj == self.plot_rt_rt:
            self.view_rt_rt.plot(rtX, rtY, obj=obj, **plt_kwargs)
            return

        plt_kwargs["allow_extraction"] = kwargs.pop("allow_extraction", True)
        if not full_repaint:
            try:
                plot_obj.plot_1D_update_data(rtX, rtY, xlabel, ylabel, **plt_kwargs)
                plot_obj.repaint()
                if override:
                    self.config.replotData["RT"] = {"xvals": rtX, "yvals": rtY, "xlabel": xlabel}
                    return
            except Exception:
                pass

        plot_obj.clear()
        plot_obj.plot_1D(
            xvals=rtX,
            yvals=rtY,
            xlabel=xlabel,
            ylabel=ylabel,
            axesSize=self.config._plotSettings["RT"]["axes_size"],
            plotType="1D",
            **plt_kwargs,
        )
        # Show the mass spectrum
        plot_obj.repaint()

        if override:
            self.config.replotData["RT"] = {"xvals": rtX, "yvals": rtY, "xlabel": xlabel}

    def plot_2D_update(self, plotName="all", evt=None):
        plt_kwargs = self._buildPlotParameters(plotType="2D")

        if plotName in ["all", "2D"]:
            try:
                self.plot_heatmap.plot_2D_update(**plt_kwargs)
                self.plot_heatmap.repaint()
            except AttributeError:
                logging.warning("Failed to update plot", exc_info=True)

        if plotName in ["all", "UniDec"]:

            try:
                self.plotUnidec_mzGrid.plot_2D_update(**plt_kwargs)
                self.plotUnidec_mzGrid.repaint()
            except AttributeError:
                logging.warning("Failed to update plot", exc_info=True)

            try:
                self.plotUnidec_mwVsZ.plot_2D_update(**plt_kwargs)
                self.plotUnidec_mwVsZ.repaint()
            except AttributeError:
                pass

        if plotName in ["all", "DT/MS"]:
            try:
                self.plot_msdt.plot_2D_update(**plt_kwargs)
                self.plot_msdt.repaint()
            except AttributeError:
                logging.warning("Failed to update plot", exc_info=True)

        if plotName in ["other"]:
            plot_obj = self.get_plot_from_name(plotName)
            try:
                plot_obj.plot_2D_update(**plt_kwargs)
                plot_obj.repaint()
            except AttributeError:
                logging.warning("Failed to update plot", exc_info=True)

    def on_plot_2D_data(self, data=None, **kwargs):
        """
        This function plots IMMS data in relevant windows.
        Input format: zvals, xvals, xlabel, yvals, ylabel
        """
        if isempty(data[0]):
            raise MessageError("Missing data", "Missing data - cannot plot 2D plot")

        # Unpack data
        if len(data) == 5:
            zvals, xvals, xlabel, yvals, ylabel = data
        elif len(data) == 6:
            zvals, xvals, xlabel, yvals, ylabel, __ = data

        # Check and change colormap if necessary
        cmapNorm = self.normalize_colormap(
            zvals, min=self.config.minCmap, mid=self.config.midCmap, max=self.config.maxCmap
        )

        # Plot data
        self.on_plot_2D(zvals, xvals, yvals, xlabel, ylabel, cmapNorm=cmapNorm, **kwargs)

    def on_plot_violin(self, data=None, set_page=False, plot="Waterfall", **kwargs):

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)
            if set_page:
                self._set_page(self.config.panelNames["Waterfall"])

        # Unpack data
        if len(data) == 5:
            zvals, xvals, xlabel, yvals, ylabel = data
        elif len(data) == 6:
            zvals, xvals, xlabel, yvals, ylabel, __ = data

        plt_kwargs = self._buildPlotParameters(["1D", "violin"])
        if "increment" in kwargs:
            plt_kwargs["increment"] = kwargs["increment"]

        n_scans = zvals.shape[1]

        plot_obj.clear()
        try:
            if n_scans < plt_kwargs["violin_nlimit"]:
                plot_obj.plot_1D_violin(
                    xvals=yvals,
                    yvals=xvals,
                    zvals=zvals,
                    label="",
                    xlabel=xlabel,
                    ylabel=ylabel,
                    labels=kwargs.get("labels", []),
                    axesSize=self.config._plotSettings["Violin"]["axes_size"],
                    orientation=self.config.violin_orientation,
                    plotName="1D",
                    **plt_kwargs,
                )
            else:
                logger.warning("Seleted item is too large to plot as violin. Will try to plot as waterfall instead")
                if n_scans > 500:
                    msg = (
                        f"There are {n_scans} scans in this dataset"
                        + "(this could be slow...). Would you like to continue?"
                    )
                    dlg = DialogBox(exceptionTitle="Would you like to continue?", exceptionMsg=msg, type="Question")
                    if dlg == wx.ID_NO:
                        return
                # plot
                self.on_plot_waterfall(yvals=xvals, xvals=yvals, zvals=zvals, xlabel=xlabel, ylabel=ylabel)
        except Exception:
            plot_obj.clear()
            logger.warning("Failed to plot violin plot...")

        # Show the mass spectrum
        plot_obj.repaint()

    def get_replot_data(self, data_format):

        if data_format == "2D":
            get_data = self.config.replotData.get("2D", None)
            zvals, xvals, yvals, xlabel, ylabel = None, None, None, None, None
            if get_data is not None:
                zvals = get_data["zvals"].copy()
                xvals = get_data["xvals"]
                yvals = get_data["yvals"]
                xlabel = get_data["xlabels"]
                ylabel = get_data["ylabels"]
            return zvals, xvals, yvals, xlabel, ylabel
        if data_format == "RMSF":
            get_data = self.config.replotData.get("RMSF", None)
            zvals, xvals, yvals, xlabelRMSD, ylabelRMSD, ylabelRMSF = None, None, None, None, None, None
            if get_data is not None:
                zvals = get_data["zvals"].copy()
                xvals = get_data["xvals"]
                yvals = get_data["yvals"]
                xlabelRMSD = get_data["xlabelRMSD"]
                ylabelRMSD = get_data["ylabelRMSD"]
                ylabelRMSF = get_data["ylabelRMSF"]
            return zvals, xvals, yvals, xlabelRMSD, ylabelRMSD, ylabelRMSF
        if data_format == "DT/MS":
            get_data = self.config.replotData.get("DT/MS", None)
            zvals, xvals, yvals, xlabel, ylabel = None, None, None, None, None
            if get_data is not None:
                zvals = get_data["zvals"].copy()
                xvals = get_data["xvals"]
                yvals = get_data["yvals"]
                xlabel = get_data["xlabels"]
                ylabel = get_data["ylabels"]
            return zvals, xvals, yvals, xlabel, ylabel
        if data_format == "MS":
            get_data = self.config.replotData.get("MS", None)
            xvals, yvals, xlimits = None, None, None
            if get_data is not None:
                xvals = get_data.get("xvals", None)
                yvals = get_data.get("yvals", None)
                xlimits = get_data.get("xlimits", None)
            return xvals, yvals, xlimits
        if data_format == "RT":
            get_data = self.config.replotData.get("RT", None)
            xvals, yvals, xlabel = None, None, None
            if get_data is not None:
                xvals = get_data.get("xvals", None)
                yvals = get_data.get("yvals", None)
                xlabel = get_data.get("xlabel", None)
            return xvals, yvals, xlabel
        if data_format == "1D":
            get_data = self.config.replotData.get("1D", None)
            xvals, yvals, xlabel = None, None, None
            if get_data is not None:
                xvals = get_data.get("xvals", None)
                yvals = get_data.get("yvals", None)
                xlabel = get_data.get("xlabel", None)
            return xvals, yvals, xlabel
        if data_format == "Matrix":
            get_data = self.config.replotData.get("Matrix", None)
            zvals, xylabels, cmap = None, None, None
            if get_data is not None:
                zvals = get_data.get("zvals", None)
                xylabels = get_data.get("xylabels", None)
                cmap = get_data.get("cmap", None)
            return zvals, xylabels, cmap

    def on_plot_image(self, zvals, xvals, yvals, plot="2D", set_page=False, **kwargs):
        def set_data():
            self.config.replotData["image"] = {
                "zvals": zvals,
                "xvals": xvals,
                "yvals": yvals,
                "cmap": plt_kwargs["colormap"],
                "cmapNorm": cmapNorm,
            }

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)
            if set_page:
                self._set_page(self.config.panelNames[plot])

        # Check that cmap modifier is included
        cmapNorm = self.normalize_colormap(
            zvals, min=self.config.minCmap, mid=self.config.midCmap, max=self.config.maxCmap
        )

        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType="2D")

        # Check if cmap should be overwritten
        if self.config.useCurrentCmap or kwargs.get("cmap", None) is None:
            plt_kwargs["colormap"] = self.config.currentCmap
        plt_kwargs["colormap_norm"] = kwargs.get("cmapNorm", None)
        plt_kwargs["allow_extraction"] = kwargs.pop("allow_extraction", True)

        if not kwargs.get("full_repaint", False):
            try:
                plot_obj.plot_2D_image_update_data(xvals, yvals, zvals, "", "", **plt_kwargs)
                plot_obj.repaint()
                return
            except Exception:
                logger.info("Failed to quickly plot heatmap", exc_info=False)

        # Plot 2D dataset
        plot_obj.clear()
        plot_obj.plot_2D_image(
            zvals,
            xvals,
            yvals,
            axesSize=self.config._plotSettings["2D"]["axes_size"],
            plotName="2D",
            callbacks=kwargs.get("callbacks", dict()),
            **plt_kwargs,
        )
        plot_obj.repaint()

    def on_plot_2D(
        self,
        zvals=None,
        xvals=None,
        yvals=None,
        xlabel=None,
        ylabel=None,
        plotType=None,
        override=True,
        replot=False,
        cmapNorm=None,
        set_page=False,
        plot="2D",
        obj=None,
        **kwargs,
    ):
        def set_data():
            self.config.replotData["2D"] = {
                "zvals": zvals,
                "xvals": xvals,
                "yvals": yvals,
                "xlabels": xlabel,
                "ylabels": ylabel,
                "cmap": plt_kwargs["colormap"],
                "cmapNorm": cmapNorm,
            }

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)
            if set_page:
                self._set_page(self.config.panelNames["2D"])

        plt_kwargs = self._buildPlotParameters(plotType="2D")

        if plot_obj == self.plot_heatmap:
            self.view_heatmap.plot(xvals, yvals, zvals, obj=obj, **plt_kwargs)
            return

        # If the user would like to replot data, you can directly unpack it
        if replot:
            zvals, xvals, yvals, xlabel, ylabel = self.get_replot_data("2D")
            if zvals is None or xvals is None or yvals is None:
                logger.warning("Could not replot data as data was missing...")
                return

        # Check that cmap modifier is included
        if cmapNorm is None and plotType != "RMSD":
            cmapNorm = self.normalize_colormap(
                zvals, min=self.config.minCmap, mid=self.config.midCmap, max=self.config.maxCmap
            )
        elif cmapNorm is None and plotType == "RMSD":
            cmapNorm = self.normalize_colormap(zvals, min=-100, mid=0, max=100)

        # Check if cmap should be overwritten
        if self.config.useCurrentCmap or kwargs.get("cmap", None) is None:
            plt_kwargs["colormap"] = self.config.currentCmap
        plt_kwargs["colormap_norm"] = kwargs.get("cmapNorm", None)
        plt_kwargs["allow_extraction"] = kwargs.pop("allow_extraction", True)

        if not kwargs.get("full_repaint", False):
            try:
                plot_obj.plot_2D_update_data(xvals, yvals, xlabel, ylabel, zvals, **plt_kwargs)
                plot_obj.repaint()
                if override:
                    set_data()
                return
            except Exception:
                logger.info("Failed to quickly plot heatmap", exc_info=False)

        # Plot 2D dataset
        plot_obj.clear()
        if self.config.plotType == "Image":
            plot_obj.plot_2D_surface(
                zvals,
                xvals,
                yvals,
                xlabel,
                ylabel,
                axesSize=self.config._plotSettings["2D"]["axes_size"],
                plotName="2D",
                **plt_kwargs,
            )

        elif self.config.plotType == "Contour":
            plot_obj.plot_2D_contour(
                zvals,
                xvals,
                yvals,
                xlabel,
                ylabel,
                axesSize=self.config._plotSettings["2D"]["axes_size"],
                plotName="2D",
                **plt_kwargs,
            )

        plot_obj.repaint()
        if override:
            set_data()

        # update plot data
        self.presenter.view._onUpdatePlotData(plot_type="2D")

    def on_plot_MSDT(
        self,
        zvals=None,
        xvals=None,
        yvals=None,
        xlabel=None,
        ylabel=None,
        cmap=None,
        cmapNorm=None,
        override=True,
        replot=False,
        set_page=False,
        obj=None,
        **kwargs,
    ):

        # change page
        if set_page:
            self._set_page(self.config.panelNames["MZDT"])

        #         # If the user would like to replot data, you can directly unpack it
        #         if replot:
        #             zvals, xvals, yvals, xlabel, ylabel = self.get_replot_data("DT/MS")
        #             if zvals is None or xvals is None or yvals is None:
        #                 return
        #
        #         # Check if cmap should be overwritten
        #         if self.config.useCurrentCmap or cmap is None:
        #             cmap = self.config.currentCmap
        #
        #         # Check that cmap modifier is included
        #         if cmapNorm is None:
        #             cmapNorm = self.normalize_colormap(
        #                 zvals, min=self.config.minCmap, mid=self.config.midCmap, max=self.config.maxCmap
        #             )

        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType="2D")
        #         plt_kwargs["colormap"] = cmap
        #         plt_kwargs["colormap_norm"] = cmapNorm
        #         plt_kwargs["allow_extraction"] = kwargs.pop("allow_extraction", True)
        #         plt_kwargs = merge_two_dicts(plt_kwargs, kwargs)

        self.view_msdt.plot(xvals, yvals, zvals, obj=obj, **plt_kwargs)
        return

    #         try:
    #             self.plot_msdt.plot_2D_update_data(xvals, yvals, xlabel, ylabel, zvals, **plt_kwargs)
    #             self.plot_msdt.repaint()
    #             if override:
    #                 self.config.replotData["DT/MS"] = {
    #                     "zvals": zvals,
    #                     "xvals": xvals,
    #                     "yvals": yvals,
    #                     "xlabels": xlabel,
    #                     "ylabels": ylabel,
    #                     "cmap": cmap,
    #                     "cmapNorm": cmapNorm,
    #                 }
    #             return
    #         except Exception:
    #             pass
    #
    #         # Plot 2D dataset
    #         self.plot_msdt.clear()
    #         if self.config.plotType == "Image":
    #             self.plot_msdt.plot_2D_surface(
    #                 zvals,
    #                 xvals,
    #                 yvals,
    #                 xlabel,
    #                 ylabel,
    #                 axesSize=self.config._plotSettings["DT/MS"]["axes_size"],
    #                 plotName="MSDT",
    #                 **plt_kwargs,
    #             )
    #
    #         elif self.config.plotType == "Contour":
    #             self.plot_msdt.plot_2D_contour(
    #                 zvals,
    #                 xvals,
    #                 yvals,
    #                 xlabel,
    #                 ylabel,
    #                 axesSize=self.config._plotSettings["DT/MS"]["axes_size"],
    #                 plotName="MSDT",
    #                 **plt_kwargs,
    #             )
    #
    #         # Show the mass spectrum
    #         self.plot_msdt.repaint()
    #
    #         # since we always sub-sample this dataset, it is makes sense to keep track of the full dataset before it was
    #         # subsampled - this way, when we replot data it will always use the full information
    #         if kwargs.get("full_data", False):
    #             xvals = kwargs["full_data"].pop("xvals", xvals)
    #             zvals = kwargs["full_data"].pop("zvals", zvals)
    #
    #         if override:
    #             self.config.replotData["DT/MS"] = {
    #                 "zvals": zvals,
    #                 "xvals": xvals,
    #                 "yvals": yvals,
    #                 "xlabels": xlabel,
    #                 "ylabels": ylabel,
    #                 "cmap": cmap,
    #                 "cmapNorm": cmapNorm,
    #             }
    #         # update plot data
    #         self.presenter.view._onUpdatePlotData(plot_type="DT/MS")

    def on_plot_3D(
        self,
        zvals=None,
        labelsX=None,
        labelsY=None,
        xlabel="",
        ylabel="",
        zlabel="Intensity",
        cmap="inferno",
        cmapNorm=None,
        replot=False,
        set_page=False,
    ):

        # change page
        if set_page:
            self._set_page(self.config.panelNames["3D"])

        plt_kwargs = self._buildPlotParameters(["1D", "3D"])

        # If the user would like to replot data, you can directly unpack it
        if replot:
            zvals, labelsX, labelsY, xlabel, ylabel = self.get_replot_data("2D")
            if zvals is None or labelsX is None or labelsY is None:
                return
        # Check if cmap should be overwritten
        if self.config.useCurrentCmap:
            cmap = self.config.currentCmap

        # Check that cmap modifier is included
        if cmapNorm is None:
            cmapNorm = self.normalize_colormap(
                zvals, min=self.config.minCmap, mid=self.config.midCmap, max=self.config.maxCmap
            )
        # add to kwargs
        plt_kwargs["colormap"] = cmap
        plt_kwargs["colormap_norm"] = cmapNorm

        self.plot_heatmap_3d.clear()
        if self.config.plotType_3D == "Surface":
            self.plot_heatmap_3d.plot_3D_surface(
                xvals=labelsX,
                yvals=labelsY,
                zvals=zvals,
                title="",
                xlabel=xlabel,
                ylabel=ylabel,
                zlabel=zlabel,
                axesSize=self.config._plotSettings["3D"]["axes_size"],
                **plt_kwargs,
            )
        elif self.config.plotType_3D == "Wireframe":
            self.plot_heatmap_3d.plot_3D_wireframe(
                xvals=labelsX,
                yvals=labelsY,
                zvals=zvals,
                title="",
                xlabel=xlabel,
                ylabel=ylabel,
                zlabel=zlabel,
                axesSize=self.config._plotSettings["3D"]["axes_size"],
                **plt_kwargs,
            )
        # Show the mass spectrum
        self.plot_heatmap_3d.repaint()

    def on_plot_waterfall(
        self, xvals, yvals, zvals, xlabel, ylabel, colors=[], set_page=False, plot="Waterfall", **kwargs
    ):

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)
            if set_page:
                self._set_page(self.config.panelNames["Waterfall"])

        plt_kwargs = self._buildPlotParameters(["1D", "waterfall"])
        if "increment" in kwargs:
            plt_kwargs["increment"] = kwargs["increment"]

        plot_obj.clear()
        plot_obj.plot_1D_waterfall(
            xvals=xvals,
            yvals=yvals,
            zvals=zvals,
            label="",
            xlabel=xlabel,
            ylabel=ylabel,
            colorList=colors,
            labels=kwargs.get("labels", []),
            axesSize=self.config._plotSettings["Waterfall"]["axes_size"],
            plotName="1D",
            **plt_kwargs,
        )

        if "add_legend" in kwargs and "labels" in kwargs and len(colors) == len(kwargs["labels"]):
            if kwargs["add_legend"]:
                legend_text = list(zip(colors, kwargs["labels"]))
                plot_obj.plot_1D_add_legend(legend_text, **plt_kwargs)
        plot_obj.repaint()

    def plot_1D_waterfall_update(self, which="other", **kwargs):

        plt_kwargs = self._buildPlotParameters(plotType="1D")

        if self.currentPage == "Other":
            plot_name = self.plot_annotated
        else:
            plot_name = self.plot_overlay

        if self.plot_overlay.plot_name != "Violin":
            extra_kwargs = self._buildPlotParameters(plotType="waterfall")
        else:
            extra_kwargs = self._buildPlotParameters(plotType="violin")
            if which in ["data", "label"]:
                return
        plt_kwargs = merge_two_dicts(plt_kwargs, extra_kwargs)

        plot_name.plot_1D_waterfall_update(which=which, **plt_kwargs)
        plot_name.repaint()

    def on_plot_waterfall_overlay(
        self, xvals, yvals, zvals, colors, xlabel, ylabel, labels=None, set_page=False, plot="Waterfall", **kwargs
    ):

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)
            if set_page:
                self._set_page(self.config.panelNames["Waterfall"])

        plt_kwargs = self._buildPlotParameters(plotType="1D")
        waterfall_kwargs = self._buildPlotParameters(plotType="waterfall")
        plt_kwargs = merge_two_dicts(plt_kwargs, waterfall_kwargs)
        if "increment" in kwargs:
            plt_kwargs["increment"] = kwargs["increment"]

        plot_obj.clear()
        plot_obj.plot_1D_waterfall_overlay(
            xvals=xvals,
            yvals=yvals,
            zvals=zvals,
            label="",
            xlabel=xlabel,
            ylabel=ylabel,
            colorList=colors,
            labels=labels,
            axesSize=self.config._plotSettings["Waterfall"]["axes_size"],
            plotName="1D",
            **plt_kwargs,
        )

        if "add_legend" in kwargs and "labels" in kwargs and len(colors) == len(kwargs["labels"]):
            if kwargs["add_legend"]:
                legend_text = list(zip(colors, kwargs["labels"]))
                plot_obj.plot_1D_add_legend(legend_text, **plt_kwargs)

        plot_obj.repaint()

    def on_plot_overlay_RT(self, xvals, yvals, xlabel, colors, labels, xlimits, set_page=False, plot="RT", **kwargs):

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)
            if set_page:
                self._set_page(self.config.panelNames.get(plot, "RT"))

        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType="1D")
        plot_obj.clear()
        plot_obj.plot_1D_overlay(
            xvals=xvals,
            yvals=yvals,
            title="",
            xlabel=xlabel,
            ylabel="Intensity",
            labels=labels,
            colors=colors,
            xlimits=xlimits,
            zoom="box",
            axesSize=self.config._plotSettings["RT"]["axes_size"],
            plotName="1D",
            **plt_kwargs,
        )
        plot_obj.repaint()

    def on_plot_overlay_DT(self, xvals, yvals, xlabel, colors, labels, xlimits, set_page=False, plot="1D", **kwargs):

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)
            if set_page:
                self._set_page(self.config.panelNames.get(plot, "1D"))

        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType="1D")

        plot_obj.clear()
        plot_obj.plot_1D_overlay(
            xvals=xvals,
            yvals=yvals,
            title="",
            xlabel=xlabel,
            ylabel="Intensity",
            labels=labels,
            colors=colors,
            xlimits=xlimits,
            zoom="box",
            axesSize=self.config._plotSettings["DT"]["axes_size"],
            plotName="1D",
            **plt_kwargs,
        )
        plot_obj.repaint()

    def on_plot_overlay_2D(
        self,
        zvalsIon1,
        zvalsIon2,
        cmapIon1,
        cmapIon2,
        alphaIon1,
        alphaIon2,
        xvals,
        yvals,
        xlabel,
        ylabel,
        plotName="2D",
        set_page=False,
        plot="Overlay",
        **kwargs,
    ):
        """
        Plot an overlay of *2* ions
        """

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)
            if set_page:
                self._set_page(self.config.panelNames["Overlay"])

        plt_kwargs = self._buildPlotParameters(plotType="2D")
        plot_obj.clear()
        plot_obj.plot_2D_overlay(
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
            axesSize=self.config._plotSettings["Overlay"]["axes_size"],
            plotName=plotName,
            **plt_kwargs,
        )
        plot_obj.repaint()

    def on_plot_rgb(
        self,
        zvals=None,
        xvals=None,
        yvals=None,
        xlabel=None,
        ylabel=None,
        legend_text=None,
        set_page=False,
        plot="2D",
        **kwargs,
    ):

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)
            if set_page:
                self._set_page(self.config.panelNames.get(plot, "2D"))

        plt_kwargs = self._buildPlotParameters(plotType="2D")

        plot_obj.clear()
        plot_obj.plot_2D_rgb(
            zvals,
            xvals,
            yvals,
            xlabel,
            ylabel,
            axesSize=self.config._plotSettings["2D"]["axes_size"],
            legend_text=legend_text,
            **plt_kwargs,
        )
        plot_obj.repaint()

    def on_plot_RMSDF(
        self,
        yvalsRMSF,
        zvals,
        xvals=None,
        yvals=None,
        xlabelRMSD=None,
        ylabelRMSD=None,
        ylabelRMSF=None,
        color="blue",
        cmapNorm=None,
        cmap="inferno",
        plotType=None,
        override=True,
        replot=False,
        set_page=False,
        plot="RMSF",
        **kwargs,
    ):
        """
        Plot RMSD and RMSF plots together in panel RMSD
        """

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)
            if set_page:
                self._set_page(self.config.panelNames["RMSF"])

        plt_kwargs = self._buildPlotParameters(["2D", "RMSF"])

        # If the user would like to replot data, you can directly unpack it
        if replot:
            zvals, xvals, yvals, xlabelRMSD, ylabelRMSD, ylabelRMSF = self.get_replot_data("RMSF")
            if zvals is None or xvals is None or yvals is None:
                return

        # Update values
        # self.presenter.getXYlimits2D(xvals, yvals, zvals)

        if self.config.useCurrentCmap:
            cmap = self.config.currentCmap

        if cmapNorm is None and plotType == "RMSD":
            cmapNorm = self.normalize_colormap(zvals, min=-100, mid=0, max=100)

        # update kwargs
        plt_kwargs["colormap"] = cmap
        plt_kwargs["colormap_norm"] = cmapNorm

        plot_obj.clear()
        plot_obj.plot_1D_2D(
            yvalsRMSF=yvalsRMSF,
            zvals=zvals,
            labelsX=xvals,
            labelsY=yvals,
            xlabelRMSD=xlabelRMSD,
            ylabelRMSD=ylabelRMSD,
            ylabelRMSF=ylabelRMSF,
            label="",
            zoom="box",
            plotName="RMSF",
            **plt_kwargs,
        )
        plot_obj.repaint()
        self.rmsdfFlag = False

        if override:
            self.config.replotData["RMSF"] = {
                "zvals": zvals,
                "xvals": xvals,
                "yvals": yvals,
                "xlabelRMSD": xlabelRMSD,
                "ylabelRMSD": ylabelRMSD,
                "ylabelRMSF": ylabelRMSF,
                "cmapNorm": cmapNorm,
            }

        self.presenter.view._onUpdatePlotData(plot_type="RMSF")

        # setup plot object
        self.plot_objs["RMSF"] = plot_obj

    def on_plot_RMSD(
        self,
        zvals=None,
        xvals=None,
        yvals=None,
        xlabel=None,
        ylabel=None,
        cmap=None,
        cmapNorm=None,
        plotType=None,
        override=True,
        replot=False,
        set_page=False,
        plot="RMSF",
        **kwargs,
    ):

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)
            if set_page:
                self._set_page(self.config.panelNames["RMSF"])

        plot_obj.clear()

        # If the user would like to replot data, you can directly unpack it
        if replot:
            zvals, xvals, yvals, xlabel, ylabel = self.get_replot_data("2D")
            if zvals is None or xvals is None or yvals is None:
                return

        # Update values
        # self.presenter.getXYlimits2D(xvals, yvals, zvals)

        # Check if cmap should be overwritten
        if self.config.useCurrentCmap:
            cmap = self.config.currentCmap

        # Check that cmap modifier is included
        if cmapNorm is None and plotType == "RMSD":
            cmapNorm = self.normalize_colormap(zvals, min=-100, mid=0, max=100)

        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType="2D")
        plt_kwargs["colormap"] = cmap
        plt_kwargs["colormap_norm"] = cmapNorm

        # Plot 2D dataset
        if self.config.plotType == "Image":
            plot_obj.plot_2D_surface(
                zvals,
                xvals,
                yvals,
                xlabel,
                ylabel,
                axesSize=self.config._plotSettings["2D"]["axes_size"],
                plotName="RMSD",
                **plt_kwargs,
            )
        elif self.config.plotType == "Contour":
            plot_obj.plot_2D_contour(
                zvals,
                xvals,
                yvals,
                xlabel,
                ylabel,
                axesSize=self.config._plotSettings["2D"]["axes_size"],
                plotName="RMSD",
                **plt_kwargs,
            )

        # Show the mass spectrum
        plot_obj.repaint()

        if override:
            self.config.replotData["2D"] = {
                "zvals": zvals,
                "xvals": xvals,
                "yvals": yvals,
                "xlabels": xlabel,
                "ylabels": ylabel,
                "cmap": cmap,
                "cmapNorm": cmapNorm,
            }

        # update plot data
        self.presenter.view._onUpdatePlotData(plot_type="2D")

    def on_plot_MS_DT_calibration(
        self,
        msX=None,
        msY=None,
        xlimits=None,
        dtX=None,
        dtY=None,
        xlabelDT="Drift time (bins)",
        plotType="both",
        set_page=False,
        view_range=[],
        **kwargs,
    ):

        # change page
        if set_page:
            self._set_page(self.config.panelNames["Calibration"])

        # MS plot
        if plotType == "both" or plotType == "MS":
            self.topPlotMS.clear()
            # get kwargs
            plt_kwargs = self._buildPlotParameters(plotType="1D")
            self.topPlotMS.plot_1D(
                xvals=msX,
                yvals=msY,
                xlabel="m/z",
                ylabel="Intensity",
                xlimits=xlimits,
                axesSize=self.config._plotSettings["Calibration (MS)"]["axes_size"],
                plotType="1D",
                **plt_kwargs,
            )
            if len(view_range):
                self.on_zoom_1D_x_axis(startX=view_range[0], endX=view_range[1], repaint=False, plot="calibration_MS")
            # Show the mass spectrum
            self.topPlotMS.repaint()

        if plotType == "both" or plotType == "1DT":
            ylabel = "Intensity"
            # 1DT plot
            self.bottomPlot1DT.clear()
            # get kwargs
            plt_kwargs = self._buildPlotParameters(plotType="1D")
            self.bottomPlot1DT.plot_1D(
                xvals=dtX,
                yvals=dtY,
                xlabel=xlabelDT,
                ylabel=ylabel,
                axesSize=self.config._plotSettings["Calibration (DT)"]["axes_size"],
                plotType="CalibrationDT",
                **plt_kwargs,
            )
            self.bottomPlot1DT.repaint()

    def on_plot_DT_calibration(
        self, dtX=None, dtY=None, color=None, xlabel="Drift time (bins)", set_page=False
    ):  # onPlot1DTCalibration

        # change page
        if set_page:
            self._set_page(self.config.panelNames["Calibration"])

        # Check yaxis labels
        ylabel = "Intensity"
        # 1DT plot
        self.bottomPlot1DT.clear()
        # get kwargs
        plt_kwargs = self._buildPlotParameters(plotType="1D")
        self.bottomPlot1DT.plot_1D(
            xvals=dtX,
            yvals=dtY,
            xlabel=xlabel,
            ylabel=ylabel,
            axesSize=self.config._plotSettings["Calibration (DT)"]["axes_size"],
            plotType="1D",
            **plt_kwargs,
        )
        self.bottomPlot1DT.repaint()

    def plot_2D_update_label(self, plot_name="RMSD", **kwargs):
        from origami.utils.visuals import calculate_label_position

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot_name)

        try:
            if plot_obj.plot_name == "RMSD":
                __, xvals, yvals, __, __ = self.get_replot_data("2D")
            elif plot_obj.plot_name == "RMSF":
                __, xvals, yvals, __, __, __ = self.get_replot_data("RMSF")
            else:
                logger.error("Operation is not supported")
                return

            plt_kwargs = self._buildPlotParameters(plotType="RMSF")
            label_x_pos, label_y_pos = calculate_label_position(xvals, yvals, self.config.rmsd_location)
            plt_kwargs["rmsd_label_coordinates"] = [label_x_pos, label_y_pos]
            plt_kwargs["rmsd_label_color"] = self.config.rmsd_color

            plot_obj.plot_2D_update_label(**plt_kwargs)
            plot_obj.repaint()
        except (AttributeError, KeyError, ValueError):
            logger.error("Failed to update RMSD label", exc_info=True)

    def plot_2D_matrix_update_label(self):
        plt_kwargs = self._buildPlotParameters("RMSF")

        plot_obj = self.get_plot_from_name("matrix")
        try:
            plot_obj.plot_2D_matrix_update_label(**plt_kwargs)
            plot_obj.repaint()
        except Exception:
            logger.error("Failed to update RMSD matrix", exc_info=True)

    def on_plot_matrix(
        self,
        zvals=None,
        xylabels=None,
        cmap=None,
        override=True,
        replot=False,
        set_page=False,
        plot="Comparison",
        **kwargs,
    ):

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)
            if set_page:
                self._set_page(self.config.panelNames["Comparison"])

        # If the user would like to replot data, you can directly unpack it
        if replot:
            zvals, xylabels, cmap = self.get_replot_data("Matrix")
            if zvals is None or xylabels is None or cmap is None:
                return

        # Check if cmap should be overwritten
        if self.config.useCurrentCmap:
            cmap = self.config.currentCmap

        plt_kwargs = self._buildPlotParameters(["2D", "RMSF"])
        plt_kwargs["colormap"] = cmap

        plot_obj.clear()
        plot_obj.plot_2D_matrix(
            zvals=zvals,
            xylabels=xylabels,
            xNames=None,
            axesSize=self.config._plotSettings["Comparison"]["axes_size"],
            plotName="2D",
            **plt_kwargs,
        )
        plot_obj.repaint()

        if override:
            self.config.replotData["Matrix"] = {"zvals": zvals, "xylabels": xylabels, "cmap": cmap}

    def on_plot_grid(
        self,
        zvals_1,
        zvals_2,
        zvals_cum,
        xvals,
        yvals,
        xlabel,
        ylabel,
        cmap_1,
        cmap_2,
        set_page=False,
        plot="Overlay",
        **kwargs,
    ):

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)
            if set_page:
                self._set_page(self.config.panelNames["Overlay"])

        plt_kwargs = self._buildPlotParameters(["2D", "RMSD"])
        plt_kwargs["colormap_1"] = cmap_1
        plt_kwargs["colormap_2"] = cmap_2

        plt_kwargs["cmap_norm_1"] = self.normalize_colormap(
            zvals_1, min=self.config.minCmap, mid=self.config.midCmap, max=self.config.maxCmap
        )
        plt_kwargs["cmap_norm_2"] = self.normalize_colormap(
            zvals_2, min=self.config.minCmap, mid=self.config.midCmap, max=self.config.maxCmap
        )
        plt_kwargs["cmap_norm_cum"] = self.normalize_colormap(zvals_cum, min=-100, mid=0, max=100)
        plot_obj.clear()
        plot_obj.plot_grid_2D_overlay(
            zvals_1,
            zvals_2,
            zvals_cum,
            xvals,
            yvals,
            xlabel,
            ylabel,
            axesSize=self.config._plotSettings["Overlay (Grid)"]["axes_size"],
            **plt_kwargs,
        )
        plot_obj.repaint()

    def on_plot_n_grid(
        self, n_zvals, cmap_list, title_list, xvals, yvals, xlabel, ylabel, set_page=False, plot="Overlay", **kwargs
    ):

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)
            if set_page:
                self._set_page(self.config.panelNames["Overlay"])

        plt_kwargs = self._buildPlotParameters(plotType="2D")
        plot_obj.clear()
        plot_obj.plot_n_grid_2D_overlay(
            n_zvals,
            cmap_list,
            title_list,
            xvals,
            yvals,
            xlabel,
            ylabel,
            axesSize=self.config._plotSettings["Overlay (Grid)"]["axes_size"],
            **plt_kwargs,
        )
        plot_obj.repaint()

    def plot_compare(
        self,
        msX=None,
        msX_1=None,
        msX_2=None,
        msY_1=None,
        msY_2=None,
        msY=None,
        xlimits=None,
        replot=False,
        override=True,
        set_page=True,
        plot="MS",
        **kwargs,
    ):

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)

        if set_page:
            self._set_page(self.config.panelNames["MS"])

        if replot:
            data = self.get_replot_data("compare_MS")
            if data["subtract"]:
                msX = data["xvals"]
                msY = data["yvals"]
                xlimits = data["xlimits"]
            else:
                msX = data["xvals"]
                msX_1 = data["xvals1"]
                msX_2 = data["xvals2"]
                msY_1 = data["yvals1"]
                msY_2 = data["yvals2"]
                xlimits = data["xlimits"]
                legend = data["legend"]
        else:
            legend = self.config.compare_massSpectrumParams["legend"]
            subtract = self.config.compare_massSpectrumParams["subtract"]

        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType="1D")

        plot_obj.clear()
        if subtract:
            try:
                plot_obj.plot_1D(
                    xvals=msX,
                    yvals=msY,
                    xlimits=xlimits,
                    zoom="box",
                    title="",
                    xlabel="m/z",
                    ylabel="Intensity",
                    label="",
                    lineWidth=self.config.lineWidth_1D,
                    axesSize=self.config._plotSettings["MS"]["axes_size"],
                    plotType="MS",
                    **plt_kwargs,
                )
            except Exception:
                plot_obj.repaint()
            if override:
                self.config.replotData["compare_MS"] = {
                    "xvals": msX,
                    "yvals": msY,
                    "xlimits": xlimits,
                    "subtract": subtract,
                }
        else:
            try:
                plot_obj.plot_1D_compare(
                    xvals1=msX_1,
                    xvals2=msX_2,
                    yvals1=msY_1,
                    yvals2=msY_2,
                    xlimits=xlimits,
                    zoom="box",
                    title="",
                    xlabel="m/z",
                    ylabel="Intensity",
                    label=legend,
                    lineWidth=self.config.lineWidth_1D,
                    axesSize=self.config._plotSettings["MS (compare)"]["axes_size"],
                    plotType="compare_MS",
                    **plt_kwargs,
                )
            except Exception:
                plot_obj.repaint()
            if override:
                self.config.replotData["compare_MS"] = {
                    "xvals": msX,
                    "xvals1": msX_1,
                    "xvals2": msX_2,
                    "yvals1": msY_1,
                    "yvals2": msY_2,
                    "xlimits": xlimits,
                    "legend": legend,
                    "subtract": subtract,
                }
        # Show the mass spectrum
        plot_obj.repaint()

    def plot_compare_spectra(
        self,
        xvals_1,
        xvals_2,
        yvals_1,
        yvals_2,
        xlimits=None,
        xlabel="m/z",
        ylabel="Intensity",
        legend=None,
        plot="MS",
        **kwargs,
    ):

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.pop("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)

        # Build kwargs
        plt_kwargs = self._buildPlotParameters(plotType="1D")
        plt_kwargs = merge_two_dicts(plt_kwargs, kwargs)

        if legend is None:
            legend = self.config.compare_massSpectrumParams["legend"]

        # setup labels
        plt_kwargs["label_1"] = legend[0]
        plt_kwargs["label_2"] = legend[1]

        try:
            plot_obj.plot_1D_compare_update_data(xvals_1, xvals_2, yvals_1, yvals_2, **plt_kwargs)
        except (AttributeError, ValueError):
            plot_obj.clear()
            plot_obj.plot_1D_compare(
                xvals1=xvals_1,
                xvals2=xvals_2,
                yvals1=yvals_1,
                yvals2=yvals_2,
                xlimits=xlimits,
                title="",
                xlabel=xlabel,
                ylabel=ylabel,
                label=legend,
                lineWidth=self.config.lineWidth_1D,
                plotType="compare_MS",
                **plt_kwargs,
            )
            # Show the mass spectrum
        plot_obj.repaint()

    def plot_1D_update_data_by_label(self, xvals, yvals, gid, label, plot, **kwargs):
        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)

        plot_obj.plot_1D_update_data_by_label(xvals, yvals, gid, label)
        plot_obj.repaint()

    def plot_1D_update_style_by_label(self, gid, plot, **kwargs):
        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)

        plot_obj.plot_1D_update_style_by_label(gid, **kwargs)
        plot_obj.repaint()

    def plot_colorbar_update(self, plot_window="", **kwargs):

        if plot_window is None and "plot_obj" in kwargs:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot_window)

        # get parameters
        plt_kwargs = self._buildPlotParameters(plotType="2D")

        # update plot
        plot_obj.plot_2D_colorbar_update(**plt_kwargs)
        plot_obj.repaint()

    def plot_normalization_update(self, plot_window="", **kwargs):
        if plot_window is None and "plot_obj" in kwargs:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot_window)

        plt_kwargs = self._buildPlotParameters(plotType="2D")

        plot_obj.plot_2D_update_normalization(**plt_kwargs)
        plot_obj.repaint()

    def on_add_legend(self, labels, colors, plot="RT", **kwargs):
        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)

        plt_kwargs = self._buildPlotParameters(plotType="legend")

        if len(colors) == len(labels):
            legend_text = list(zip(colors, labels))

        plot_obj.plot_1D_add_legend(legend_text, **plt_kwargs)

    def on_clear_legend(self, plot, **kwargs):
        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)

        plot_obj.plot_remove_legend()

    def on_add_marker(
        self,
        xvals=None,
        yvals=None,
        color="b",
        marker="o",
        size=5,
        plot="MS",
        repaint=True,
        clear_first=False,
        **kwargs,
    ):

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
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
            test_yvals=kwargs.pop("test_yvals", False),
            **kwargs,
        )

        if repaint:
            plot_obj.repaint()

    def on_add_patch(self, x, y, width, height, color="r", alpha=0.5, repaint=False, plot="MS", **kwargs):

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)

        plot_obj.plot_add_patch(x, y, width, height, color=color, alpha=alpha)
        if repaint:
            plot_obj.repaint()

    def on_zoom_1D_x_axis(self, startX, endX, endY=None, set_page=False, plot="MS", repaint=True, **kwargs):

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)

        if set_page:
            self._set_page(self.config.panelNames["MS"])

        if endY is None:
            plot_obj.on_zoom_x_axis(startX, endX)
        else:
            plot_obj.on_zoom(startX, endX, endY)

        if repaint:
            plot_obj.repaint()

    def on_zoom_1D_xy_axis(self, startX, endX, startY, endY, set_page=False, plot="MS", repaint=True):

        if set_page:
            self._set_page(self.config.panelNames["MS"])

        if plot == "MS":
            self.plot_ms.on_zoom_xy(startX, endX, startY, endY)

            if repaint:
                self.plot_ms.repaint()

    def on_add_label(self, x, y, text, rotation, color="k", plot="RMSD", **kwargs):

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)

        plot_obj.addText(
            x,
            y,
            text,
            rotation,
            color=self.config.rmsd_color,
            fontsize=self.config.rmsd_fontSize,
            weight=self.config.rmsd_fontWeight,
            plot=plot,
        )
        plot_obj.repaint()

    def _buildPlotParameters(self, plotType):
        return self.config.get_mpl_parameters(plotType)

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

        norm_method = self.config.normalization_2D

        if norm_method == "Midpoint":
            cmapNormalization = MidpointNormalize(midpoint=cmapMid, v_min=cmapMin, v_max=cmapMax, clip=False)
        elif norm_method == "Logarithmic":
            from matplotlib.colors import LogNorm

            cmapNormalization = LogNorm(vmin=cmapMin, vmax=cmapMax)
        elif norm_method == "Power":
            from matplotlib.colors import PowerNorm

            cmapNormalization = PowerNorm(gamma=self.config.normalization_2D_power_gamma, vmin=cmapMin, vmax=cmapMax)

        return cmapNormalization

    def plot_3D_update(self, plotName="all", evt=None):
        plt_kwargs = self._buildPlotParameters(plotType="3D")

        if plotName in ["all", "3D"]:
            try:
                self.plot_heatmap_3d.plot_3D_update(**plt_kwargs)
                self.plot_heatmap_3d.repaint()
            except AttributeError:
                pass
