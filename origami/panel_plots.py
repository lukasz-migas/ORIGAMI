"""Plotting panel"""
# Standard library imports
import logging
from typing import Union
from functools import partial

# Third-party imports
import wx
from pubsub import pub

# Local imports
from origami.ids import ID_clearPlot_1D
from origami.ids import ID_clearPlot_2D
from origami.ids import ID_clearPlot_3D
from origami.ids import ID_clearPlot_MS
from origami.ids import ID_clearPlot_RT
from origami.ids import ID_clearPlot_MZDT
from origami.ids import ID_clearPlot_RMSD
from origami.ids import ID_clearPlot_RMSF
from origami.ids import ID_clearPlot_1D_MS
from origami.ids import ID_clearPlot_other
from origami.ids import ID_clearPlot_RT_MS
from origami.ids import ID_clearPlot_Matrix
from origami.ids import ID_clearPlot_Overlay
from origami.ids import ID_clearPlot_Waterfall
from origami.ids import ID_plots_customise_plot
from origami.icons.assets import Icons
from origami.config.config import CONFIG
from origami.visuals.utilities import on_change_plot_style
from origami.objects.containers import DataObject
from origami.objects.containers import IonHeatmapObject
from origami.objects.containers import MobilogramObject
from origami.objects.containers import ChromatogramObject
from origami.objects.containers import MassSpectrumObject
from origami.objects.containers import MassSpectrumHeatmapObject
from origami.gui_elements.helpers import make_menu_item
from origami.gui_elements.popup_view import PopupHeatmapView
from origami.gui_elements.popup_view import PopupMobilogramView
from origami.gui_elements.popup_view import PopupChromatogramView
from origami.gui_elements.popup_view import PopupMassSpectrumView
from origami.gui_elements.views.view_base import ViewBase
from origami.gui_elements.views.view_heatmap import ViewIonHeatmap
from origami.gui_elements.views.view_heatmap import ViewMassSpectrumHeatmap
from origami.gui_elements.views.view_spectrum import ViewMobilogram
from origami.gui_elements.views.view_spectrum import ViewChromatogram
from origami.gui_elements.views.view_spectrum import ViewMassSpectrum
from origami.gui_elements.views.view_heatmap_3d import ViewHeatmap3d
from origami.gui_elements.views.popup_plot_settings import PopupPlotPanelSettings

logger = logging.getLogger(__name__)

# 2D -> Heatmap; Other -> Annotated (or else)


class PanelPlots(wx.Panel):
    """Plotting panel instance"""

    HELP_LINK = None

    # ui elements
    lock_plot_check = None
    resize_plot_check = None

    # view-based plots
    view_ms = None
    plot_ms = None
    view_rt_rt = None
    plot_rt_rt = None
    view_dt_dt = None
    plot_dt_dt = None
    plot_heatmap = None
    view_heatmap = None
    plot_msdt = None
    view_msdt = None

    # old-style plot windows
    panel_overlay = None
    plot_overlay = None
    view_overlay = None
    panel_heatmap_3d = None
    plot_heatmap_3d = None
    view_heatmap_3d = None
    panel_annotated = None
    plot_annotated = None
    view_annotated = None

    # popup windows
    _popup_ms = None
    _popup_rt = None
    _popup_dt = None
    _popup_2d = None

    def __init__(self, parent, presenter):
        wx.Panel.__init__(
            self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.Size(800, 600), style=wx.TAB_TRAVERSAL
        )

        self.view = parent
        self.presenter = presenter
        self._icons = Icons()

        self.current_page = None
        # Extract size of screen
        self._display_size_px = wx.GetDisplaySize()
        self.SetSize(0, 0, self._display_size_px[0] - 320, self._display_size_px[1] - 50)
        self._display_size_mm = wx.GetDisplaySizeMM()

        self.displayRes = wx.GetDisplayPPI()
        self.figsizeX = (self._display_size_px[0] - 320) / self.displayRes[0]
        self.figsizeY = (self._display_size_px[1] - 70) / self.displayRes[1]

        # used to keep track of what were the last selected pages
        self.plot_notebook = self.make_notebook()

        self._resizing = False
        self._timer = wx.Timer(self, True)
        self.Bind(wx.EVT_TIMER, self._on_late_resize, self._timer)

        self.plot_notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.on_page_changed)
        self.Bind(wx.EVT_SIZE, self.on_resize)

        # initialise
        self.on_page_changed(None)
        on_change_plot_style()

    @property
    def popup_ms(self) -> PopupMassSpectrumView:
        """Return instance of the popup viewer"""

        if not self._popup_ms:
            self._popup_ms = PopupMassSpectrumView(self.view)
            self._popup_ms.position_on_window(self.view)
        self._popup_ms.Show()
        return self._popup_ms

    @property
    def popup_rt(self) -> PopupChromatogramView:
        """Return instance of the popup viewer"""
        if not self._popup_rt:
            self._popup_rt = PopupChromatogramView(self.view)
            self._popup_rt.position_on_window(self.view)
        self._popup_rt.Show()
        return self._popup_rt

    @property
    def popup_dt(self) -> PopupMobilogramView:
        """Return instance of the popup viewer"""
        if not self._popup_dt:
            self._popup_dt = PopupMobilogramView(self.view)
            self._popup_dt.position_on_window(self.view)
        self._popup_dt.Show()
        return self._popup_dt

    @property
    def popup_2d(self) -> PopupHeatmapView:
        """Return instance of the popup viewer"""
        if not self._popup_2d:
            self._popup_2d = PopupHeatmapView(self.view)
            self._popup_2d.position_on_window(self.view)
        self._popup_2d.Show()
        return self._popup_2d

    @property
    def data_handling(self):
        """Return handle to `data_processing`"""
        return self.presenter.data_handling

    @property
    def data_processing(self):
        """Return handle to `data_processing`"""
        return self.presenter.data_processing

    @property
    def document_tree(self):
        """Return handle to `document_tree`"""
        return self.presenter.view.panelDocuments.documents

    def on_resize(self, evt):
        """Slightly modified resized event which reduces the number of `EVT_SIZE` triggers that can significantly
        affect performance since each plot object in ORIGAMI is automatically resized too"""
        if self._resizing:
            evt.Skip()
            self._resizing = False
        else:
            self._timer.Stop()
            self._timer.StartOnce(200)

    def _on_late_resize(self, _evt):
        """Triggers additional resize after timer event has run out"""
        # trigger resize event
        self._resizing = True
        self.PostSizeEvent()

    def on_get_current_page(self):
        """Return current page"""
        self.current_page = self.plot_notebook.GetPageText(self.plot_notebook.GetSelection())

    def _get_page_text(self):
        self.on_get_current_page()
        return self.current_page

    @staticmethod
    def _map_name_to_tab_id(tab_name: str) -> int:
        """Return index to the tab"""
        return {
            "Mass spectrum": 0,
            "MS": 0,
            "Chromatogram": 1,
            "RT": 1,
            "Mobilogram": 2,
            "DT": 2,
            "Heatmap": 3,
            "DT/MS": 4,
            "Heatmap (3D)": 5,
        }.get(tab_name, 0)

    def set_page(self, page_id: Union[int, str]):
        """Set current page in the window"""
        # provided string so have to find appropriate window
        if isinstance(page_id, str):
            page_id = self._map_name_to_tab_id(page_id)

        try:
            self.plot_notebook.SetSelection(page_id)
        except RuntimeError:
            logger.warning("Failed to set to requested page", exc_info=True)

    def on_page_changed(self, _evt):
        """Triggered by change of panel in the plot section

        Parameters
        ----------
        _evt : wxPython event
            unused
        """
        # get current page
        self.current_page = self.plot_notebook.GetPageText(self.plot_notebook.GetSelection())
        view = self.get_view_from_name(self.current_page)
        pub.sendMessage("view.activate", view_id=view.PLOT_ID)

    def make_notebook(self):
        """Make notebook panel"""

        # Setup notebook
        plot_notebook = wx.Notebook(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0)

        # Setup PLOT MS
        self.view_ms = ViewMassSpectrum(
            plot_notebook,
            CONFIG._plotSettings["MS"]["gui_size"],  # noqa
            CONFIG,
            allow_extraction=True,
            callbacks=dict(
                CTRL=[
                    "extract.heatmap.from.spectrum",
                    "extract.chromatogram.from.spectrum",
                    "extract.mobilogram.from.spectrum",
                ]
            ),
            filename="mass-spectrum",
        )
        plot_notebook.AddPage(self.view_ms.panel, "Mass spectrum")
        self.plot_ms = self.view_ms.figure

        # Setup PLOT RT
        self.view_rt_rt = ViewChromatogram(
            plot_notebook,
            CONFIG._plotSettings["RT"]["gui_size"],  # noqa
            CONFIG,
            allow_extraction=True,
            callbacks=dict(CTRL=["extract.spectrum.from.chromatogram"]),
            filename="chromatogram",
        )
        plot_notebook.AddPage(self.view_rt_rt.panel, "Chromatogram")
        self.plot_rt_rt = self.view_ms.figure

        # Setup PLOT 1D
        self.view_dt_dt = ViewMobilogram(
            plot_notebook,
            CONFIG._plotSettings["DT"]["gui_size"],  # noqa
            CONFIG,
            allow_extraction=True,
            callbacks=dict(CTRL=["extract.spectrum.from.mobilogram"]),
            filename="mobilogram",
        )
        plot_notebook.AddPage(self.view_dt_dt.panel, "Mobilogram")
        self.plot_dt_dt = self.view_ms.figure

        # Setup PLOT 2D
        self.view_heatmap = ViewIonHeatmap(
            plot_notebook,
            CONFIG._plotSettings["2D"]["gui_size"],  # noqa
            CONFIG,
            allow_extraction=True,
            callbacks=dict(CTRL=["extract.spectrum.from.heatmap"]),
            filename="heatmap",
        )
        plot_notebook.AddPage(self.view_heatmap.panel, "Heatmap")
        self.plot_heatmap = self.view_heatmap.figure

        # Setup PLOT DT/MS
        self.view_msdt = ViewMassSpectrumHeatmap(
            plot_notebook,
            CONFIG._plotSettings["DT/MS"]["gui_size"],  # noqa
            CONFIG,
            allow_extraction=True,
            callbacks=dict(CTRL=["extract.rt.from.heatmap"]),
            filename="ms-heatmap",
        )
        plot_notebook.AddPage(self.view_msdt.panel, "DT/MS")
        self.plot_msdt = self.view_msdt.figure

        # Setup PLOT 3D
        self.view_heatmap_3d = ViewHeatmap3d(
            plot_notebook,
            CONFIG._plotSettings["DT/MS"]["gui_size"],  # noqa
            CONFIG,
            allow_extraction=False,
            callbacks=dict(),
            filename="heatmap-3d",
        )
        plot_notebook.AddPage(self.view_heatmap_3d.panel, "Heatmap (3D)")
        self.plot_heatmap_3d = self.view_heatmap_3d.figure

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(plot_notebook, 1, wx.EXPAND | wx.ALL, 1)
        self.SetSizer(main_sizer)
        self.Layout()
        self.Show()

        self.Bind(wx.EVT_CONTEXT_MENU, self.on_right_click)

        return plot_notebook

    def on_copy_to_clipboard(self, _evt):
        """Copy plot to clipboard"""
        plot_obj = self.get_plot_from_name(self.current_page)
        plot_obj.copy_to_clipboard()
        pub.sendMessage("notify.message.success", message="Copied figure to clipboard!")

    def on_smooth_object(self, _evt):
        """Smooth plot signal"""
        from origami.gui_elements.misc_dialogs import DialogSimpleAsk

        view_obj = self.get_view_from_name(self.current_page)
        obj = view_obj.get_object(get_cache=False)

        if obj is None:
            pub.sendMessage("notify.message.error", message="Cannot smooth object as the plot cache is empty")
            return

        sigma = DialogSimpleAsk(
            "Smoothing spectrum using Gaussian Filter. Sigma value:", value=1, value_type="floatPos"
        )
        if sigma is None:
            pub.sendMessage("notify.message.warning", message="Smoothing action was cancelled")
            return
        sigma = float(sigma)
        obj = obj.smooth(smooth_method="Gaussian", sigma=sigma)
        view_obj.plot(obj=obj)

    def on_process_mass_spectrum(self, _evt):
        """Process mass spectrum"""
        view_obj = self.get_view_from_name(self.current_page)
        data_obj = view_obj.get_object()

        if data_obj is None:
            pub.sendMessage("notify.message.error", message="Cannot process mass spectrum - data object is empty")
            return

        self.document_tree.on_open_process_ms_settings(mz_obj=data_obj, disable_process=True)

    def on_process_heatmap(self, _evt):
        """Process heatmap"""
        view_obj = self.get_view_from_name(self.current_page)
        data_obj = view_obj.get_object()

        if data_obj is None:
            pub.sendMessage("notify.message.error", message="Cannot process heatmap - data object is empty")
            return

        self.document_tree.on_open_process_heatmap_settings(heatmap_obj=data_obj, disable_process=True)

    def on_rotate_plot(self, _evt):
        """Rotate heatmap plot"""
        view_obj = self.get_view_from_name(self.current_page)
        data_obj = view_obj.get_object()

        if data_obj is None:
            pub.sendMessage("notify.message.error", message="Cannot rotate heatmap - data object is empty")
            return

        view_obj.plot(obj=data_obj.transpose(), repaint=False)
        view_obj.reset_zoom()

    def on_open_peak_picker(self, _evt):
        """Open peak picker window"""
        view_obj = self.get_view_from_name(self.current_page)
        mz_obj = view_obj.get_object()

        try:
            document_title, dataset_name = mz_obj.owner
        except AttributeError:
            document_title, dataset_name = None, None

        if document_title is None or dataset_name is None:
            pub.sendMessage(
                "notify.message.error",
                message="Could not find the document/dataset information in the plot metadata."
                "\nTry right-clicking on a mass spectrum in the document tree and select `Open peak picker`",
            )
            return

        self.document_tree.on_open_peak_picker(None, document_title=document_title, dataset_name=dataset_name)

    def on_open_unidec(self, _evt):
        """Open UniDec deconvolution panel"""
        view_obj = self.get_view_from_name(self.current_page)
        mz_obj = view_obj.get_object()

        try:
            document_title, dataset_name = mz_obj.owner
        except AttributeError:
            document_title, dataset_name = None, None

        if document_title is None or dataset_name is None:
            pub.sendMessage(
                "notify.message.error",
                message="Could not find the document/dataset information in the plot metadata."
                "\nTry right-clicking on a mass spectrum in the document tree and select `Open peak picker`",
            )
            return

        self.document_tree.on_open_unidec(None, document_title=document_title, dataset_name=dataset_name, mz_obj=mz_obj)

    def on_open_annotations_panel(self, _evt):
        """Open the annotations panel for particular object"""
        view_obj = self.get_view_from_name(self.current_page)

        data_obj = view_obj.get_object()
        try:
            document_title, dataset_name = data_obj.owner
        except AttributeError:
            document_title, dataset_name = None, None

        # check whether data object has document/dataset associated with it
        if document_title is None or dataset_name is None:
            pub.sendMessage(
                "notify.message.error",
                message="Could not find the document/dataset information in the plot metadata."
                "\nTry right-clicking on the object in the document tree and select"
                "`Annotations...->Show annotations panel...`",
            )
            return

        # check whether dataset has been modified and not saved
        if data_obj.unsaved:
            is_saved, data_obj = self.data_handling.on_save_unsaved_changes(data_obj, document_title, dataset_name)

            if not is_saved:
                pub.sendMessage("notify.message.error", message="Cannot annotate object that has unsaved changes.")
                return
            # update dataset information
            document_title, dataset_name = data_obj.owner
            view_obj.set_object(data_obj)

        self.document_tree.on_open_annotation_editor(
            None, document_title=document_title, dataset_name=dataset_name, data_obj=data_obj
        )

    def on_show_as_joint(self, _evt):
        """Show heatmap plot as joint-plot"""
        view_obj = self.get_view_from_name(self.current_page)
        if not hasattr(view_obj, "plot_joint"):
            pub.sendMessage("notify.message.error", message="Cannot show this view as a joint-plot")
            return

        data_obj = view_obj.get_object()
        if not data_obj:
            pub.sendMessage("notify.message.error", message="Cannot show this view as the plot cache is empty.")
            return

        view_obj.plot_joint(obj=data_obj)

    def on_show_as_contour(self, _evt):
        """Show heatmap plot as contour-plot"""
        view_obj = self.get_view_from_name(self.current_page)
        if not hasattr(view_obj, "plot_contour"):
            pub.sendMessage("notify.message.error", message="Cannot show this view as a contour-plot")
            return

        data_obj = view_obj.get_object()
        if not data_obj:
            pub.sendMessage("notify.message.error", message="Cannot show this view as the plot cache is empty.")
            return

        view_obj.plot_contour(obj=data_obj)

    def on_show_as_waterfall(self, _evt):
        """Show heatmap plot as waterfall-plot"""
        view_obj = self.get_view_from_name(self.current_page)
        if not hasattr(view_obj, "plot_waterfall"):
            pub.sendMessage("notify.message.error", message="Cannot show this view as a waterfall-plot")
            return

        data_obj = view_obj.get_object()
        if not data_obj:
            pub.sendMessage("notify.message.error", message="Cannot show this view as the plot cache is empty.")
            return

        view_obj.plot_waterfall(obj=data_obj)

    def on_show_as_violin(self, _evt):
        """Show heatmap object as violin plot"""
        view_obj = self.get_view_from_name(self.current_page)
        if not hasattr(view_obj, "plot_violin"):
            pub.sendMessage("notify.message.error", message="Cannot show this view as a violin-plot")
            return

        data_obj = view_obj.get_object()
        if not data_obj:
            pub.sendMessage("notify.message.error", message="Cannot show this view as the plot cache is empty.")
            return

        view_obj.plot_violin(obj=data_obj)

    def on_show_as_heatmap(self, _evt):
        """Show heatmap plot as heatmap-plot"""
        view_obj = self.get_view_from_name(self.current_page)
        data_obj = view_obj.get_object()
        if not data_obj:
            pub.sendMessage("notify.message.error", message="Cannot show this view as the plot cache is empty.")
            return

        view_obj.plot(obj=data_obj)

    def on_show_as_heatmap_3d(self, _evt):
        """Show heatmap plot as heatmap-plot"""
        view_obj = self.get_view_from_name(self.current_page)
        data_obj = view_obj.get_object()
        if not data_obj:
            pub.sendMessage("notify.message.error", message="Cannot show this view as the plot cache is empty.")
            return

        self.view_heatmap_3d.plot(obj=data_obj)
        self.set_page("Heatmap (3D)")

    def on_open_settings(self, _evt):
        """Open settings of the Document Tree"""
        popup = PopupPlotPanelSettings(self.view)
        popup.position_on_mouse()
        popup.Show()

    def on_open_info(self, _evt):
        """Open help window to inform user on how to use this window / panel"""
        from origami.gui_elements.panel_html_viewer import PanelHTMLViewer

        if self.HELP_LINK:
            PanelHTMLViewer(self.view, link=self.HELP_LINK)

    def on_right_click_ctrl(self, _evt):
        """Right-click menu"""
        # make main menu
        menu = wx.Menu()

        menu_info = make_menu_item(
            parent=menu, evt_id=wx.ID_ANY, text="Learn more about Plot Panel...", bitmap=self._icons.info
        )
        self.Bind(wx.EVT_MENU, self.on_open_info, menu_info)

        menu.AppendItem(menu_info)
        menu_settings = make_menu_item(
            parent=menu, evt_id=wx.ID_ANY, text="Data extraction settings", bitmap=self._icons.gear
        )
        self.Bind(wx.EVT_MENU, self.on_open_settings, menu_settings)

        menu.AppendItem(menu_settings)
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def on_right_click(self, evt):
        """Right-click event handler"""
        self.current_page = self.plot_notebook.GetPageText(self.plot_notebook.GetSelection())

        if wx.GetKeyState(wx.WXK_CONTROL):
            self.on_right_click_ctrl(evt)
            return

        # Make bindings
        self.Bind(wx.EVT_MENU, self.on_customise_plot, id=ID_plots_customise_plot)

        view = self.get_view_from_name()
        menu = view.get_right_click_menu(self)

        # pre-generate common menu items
        menu_plot_general = make_menu_item(parent=menu, text="Edit general parameters...", bitmap=self._icons.gear)
        menu_plot_1d = make_menu_item(parent=menu, text="Edit plot parameters...", bitmap=self._icons.plot_1d)
        menu_plot_2d = make_menu_item(parent=menu, text="Edit plot parameters...", bitmap=self._icons.heatmap)
        menu_plot_3d = make_menu_item(parent=menu, text="Edit plot parameters...", bitmap=self._icons.overlay)
        menu_plot_colorbar = make_menu_item(
            parent=menu, text="Edit colorbar parameters...", bitmap=self._icons.plot_colorbar
        )
        menu_plot_legend = make_menu_item(parent=menu, text="Edit legend parameters...", bitmap=self._icons.plot_legend)
        #         menu_plot_rmsd = make_menu_item(
        #             parent=menu,
        #             text="Edit plot parameters...",
        #             bitmap=self.icons.iconsLib["panel_rmsd_16"],
        #         )
        menu_plot_waterfall = make_menu_item(
            parent=menu, text="Edit waterfall parameters...", bitmap=self._icons.waterfall
        )
        menu_plot_violin = make_menu_item(parent=menu, text="Edit violin parameters...", bitmap=self._icons.violin)
        menu_action_rotate90 = make_menu_item(parent=menu, text="Rotate 90°", bitmap=self._icons.rotate)
        menu_action_process_2d = make_menu_item(
            parent=menu, text="Process heatmap...", bitmap=self._icons.process_heatmap
        )

        menu_action_process_ms = make_menu_item(
            parent=menu, text="Process mass spectrum...", bitmap=self._icons.process_ms
        )

        menu_action_process_pick = make_menu_item(parent=menu, text="Open peak picker...", bitmap=self._icons.highlight)
        menu_action_unidec = make_menu_item(parent=menu, text="Open UniDec deconvolution...", bitmap=self._icons.unidec)

        menu_action_smooth_signal = make_menu_item(
            parent=menu, text="Smooth signal (Gaussian)", bitmap=self._icons.clean
        )
        menu_action_smooth_heatmap = make_menu_item(
            parent=menu, text="Smooth heatmap (Gaussian)", bitmap=self._icons.clean
        )
        menu_action_open_annotations = make_menu_item(
            parent=menu, text="Show annotations panel...", bitmap=self._icons.label
        )
        menu_action_show_joint = make_menu_item(parent=menu, text="Show as a joint plot", bitmap=self._icons.joint)
        menu_action_show_contour = make_menu_item(
            parent=menu, text="Show as a contour plot", bitmap=self._icons.contour
        )
        menu_action_show_waterfall = make_menu_item(
            parent=menu, text="Show as a waterfall plot", bitmap=self._icons.waterfall
        )
        menu_action_show_heatmap = make_menu_item(
            parent=menu, text="Show as a heatmap plot", bitmap=self._icons.heatmap
        )
        menu_action_show_violin = make_menu_item(parent=menu, text="Show as a violin plot", bitmap=self._icons.violin)
        menu_action_show_3d = make_menu_item(parent=menu, text="Show in 3d", bitmap=self._icons.cube)

        # bind events by item
        self.Bind(wx.EVT_MENU, partial(self.view.on_open_plot_settings_panel, "General"), menu_plot_general)
        self.Bind(wx.EVT_MENU, partial(self.view.on_open_plot_settings_panel, "Colorbar"), menu_plot_colorbar)
        self.Bind(wx.EVT_MENU, partial(self.view.on_open_plot_settings_panel, "Legend"), menu_plot_legend)
        self.Bind(wx.EVT_MENU, partial(self.view.on_open_plot_settings_panel, "Plot 1D"), menu_plot_1d)
        self.Bind(wx.EVT_MENU, partial(self.view.on_open_plot_settings_panel, "Plot 2D"), menu_plot_2d)
        self.Bind(wx.EVT_MENU, partial(self.view.on_open_plot_settings_panel, "Plot 3D"), menu_plot_3d)
        self.Bind(wx.EVT_MENU, partial(self.view.on_open_plot_settings_panel, "Waterfall"), menu_plot_waterfall)
        self.Bind(wx.EVT_MENU, partial(self.view.on_open_plot_settings_panel, "Violin"), menu_plot_violin)
        # self.Bind(wx.EVT_MENU, partial(self.view.on_open_plot_settings_panel, "RMSD"), menu_plot_rmsd)

        self.Bind(wx.EVT_MENU, self.on_process_mass_spectrum, menu_action_process_ms)
        self.Bind(wx.EVT_MENU, self.on_process_heatmap, menu_action_process_2d)
        self.Bind(wx.EVT_MENU, self.on_rotate_plot, menu_action_rotate90)
        self.Bind(wx.EVT_MENU, self.on_open_peak_picker, menu_action_process_pick)
        self.Bind(wx.EVT_MENU, self.on_open_unidec, menu_action_unidec)
        self.Bind(wx.EVT_MENU, self.on_smooth_object, menu_action_smooth_signal)
        self.Bind(wx.EVT_MENU, self.on_smooth_object, menu_action_smooth_heatmap)
        self.Bind(wx.EVT_MENU, self.on_open_annotations_panel, menu_action_open_annotations)
        self.Bind(wx.EVT_MENU, self.on_show_as_joint, menu_action_show_joint)
        self.Bind(wx.EVT_MENU, self.on_show_as_contour, menu_action_show_contour)
        self.Bind(wx.EVT_MENU, self.on_show_as_waterfall, menu_action_show_waterfall)
        self.Bind(wx.EVT_MENU, self.on_show_as_heatmap, menu_action_show_heatmap)
        self.Bind(wx.EVT_MENU, self.on_show_as_violin, menu_action_show_violin)
        self.Bind(wx.EVT_MENU, self.on_show_as_heatmap_3d, menu_action_show_3d)

        if self.current_page == "Mass spectrum":
            menu.Insert(0, menu_action_smooth_signal)
            menu.Insert(1, menu_action_process_ms)
            menu.Insert(2, menu_action_process_pick)
            menu.Insert(3, menu_action_unidec)
            menu.Insert(4, menu_action_open_annotations)
            menu.InsertSeparator(5)
            menu.Insert(6, menu_plot_general)
            menu.Insert(7, menu_plot_1d)
        elif self.current_page == "Chromatogram":
            menu.Insert(0, menu_action_smooth_signal)
            menu.Insert(1, menu_action_open_annotations)
            menu.InsertSeparator(2)
            menu.Insert(3, menu_plot_general)
            menu.Insert(4, menu_plot_1d)
            menu.Insert(5, menu_plot_legend)
        elif self.current_page == "Mobilogram":
            menu.Insert(0, menu_action_smooth_signal)
            menu.Insert(1, menu_action_open_annotations)
            menu.InsertSeparator(2)
            menu.Insert(3, menu_plot_general)
            menu.Insert(4, menu_plot_1d)
            menu.Insert(5, menu_plot_legend)
        elif self.current_page == "Heatmap":
            menu.Insert(0, menu_action_show_heatmap)
            menu.Insert(1, menu_action_show_contour)
            menu.Insert(2, menu_action_show_waterfall)
            menu.Insert(3, menu_action_show_violin)
            menu.Insert(4, menu_action_show_joint)
            menu.Insert(5, menu_action_show_3d)
            menu.InsertSeparator(6)
            menu.Insert(7, menu_action_smooth_heatmap)
            menu.Insert(8, menu_action_process_2d)
            menu.Insert(9, menu_action_rotate90)
            menu.Insert(10, menu_action_open_annotations)
            menu.InsertSeparator(11)
            menu.Insert(12, menu_plot_general)
            menu.Insert(13, menu_plot_2d)
            menu.Insert(14, menu_plot_colorbar)
            menu.Insert(15, menu_plot_waterfall)
            menu.Insert(16, menu_plot_violin)
        elif self.current_page == "DT/MS":
            menu.Insert(0, menu_action_show_heatmap)
            menu.Insert(1, menu_action_show_contour)
            menu.Insert(2, menu_action_show_joint)
            menu.InsertSeparator(3)
            menu.Insert(4, menu_action_smooth_heatmap)
            menu.Insert(5, menu_action_process_2d)
            menu.Insert(6, menu_action_rotate90)
            menu.Insert(7, menu_action_open_annotations)
            menu.InsertSeparator(8)
            menu.Insert(9, menu_plot_general)
            menu.Insert(10, menu_plot_2d)
            menu.Insert(11, menu_plot_colorbar)
        elif self.current_page == "Heatmap (3D)":
            menu.Insert(0, menu_action_smooth_heatmap)
            menu.InsertSeparator(1)
            menu.Insert(2, menu_plot_3d)

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def get_plot_from_name(self, plot_name):
        """Retrieve plot object from name

        Parameters
        ----------
        plot_name : str
            name of the plot

        Returns
        -------
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
            "3d": self.plot_heatmap_3d,
            "heatmap (3d)": self.plot_heatmap_3d,
        }
        plot_name = plot_name.lower()
        plot_obj = plot_dict.get(plot_name, None)
        if plot_obj is None:
            logger.error(f"Could not find plot object with name `{plot_name}")
        return plot_obj

    def get_view_from_name(self, plot_name: str = None):
        """Retrieve view from name"""
        plot_dict = {
            "mass spectrum": self.view_ms,
            "chromatogram": self.view_rt_rt,
            "mobilogram": self.view_dt_dt,
            "heatmap": self.view_heatmap,
            "msdt": self.view_msdt,
            "dt/ms": self.view_msdt,
            "3d": self.view_heatmap_3d,
            "heatmap (3d)": self.view_heatmap_3d,
        }
        if plot_name is None:
            plot_name = self.current_page
        plot_name = plot_name.lower()
        plot_obj = plot_dict.get(plot_name, None)
        if plot_obj is None:
            logger.error(f"Could not find view object with name `{plot_name}")
        return plot_obj

    def get_plot_from_id(self, id_value):
        """Retrieve plot object from id"""

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

    def on_customise_plot(self, evt, **kwargs):
        """Open customization panel..."""
        raise NotImplementedError("Must implement method")
        # open_window, title = True, ""
        #
        # if "plot" in kwargs and "plot_obj" in kwargs:
        #     plot = kwargs.pop("plot_obj")
        #     title = kwargs.pop("plot")
        # else:
        #     plot = self.get_plot_from_name(self.currentPage)
        #     title = f"{self.currentPage}..."
        # #         elif self.currentPage == "Overlay":
        # #             plot, title = self.plot2D, "Overlay"
        # #             if plot.plot_name not in ["Mask", "Transparent"]:
        # #                 open_window = False
        # #         elif self.currentPage == "RMSF":
        # #             plot, title = self.plot2D, "RMSF"
        # #             if plot.plot_name not in ["RMSD"]:
        # #                 open_window = False
        # #         elif self.currentPage == "Comparison":
        # #             plot, title = self.plot2D, "Comparison..."
        # #         elif self.currentPage == "Other":
        # #             plot, title = self.plotOther, "Custom data..."
        #
        # if not open_window:
        #     raise MessageError("Error", "Cannot customise parameters for this plot. Try replotting instead.")
        #
        # if not hasattr(plot, "plotMS"):
        #     raise MessageError(
        #         "Error", "Cannot customise plot parameters, either because it does not exist or is not supported yet."
        #     )
        #
        # if hasattr(plot, "plot_limits") and len(plot.plot_limits) == 4:
        #     xmin, xmax = plot.plot_limits[0], plot.plot_limits[1]
        #     ymin, ymax = plot.plot_limits[2], plot.plot_limits[3]
        # else:
        #     try:
        #         xmin, xmax = plot.plot_base.get_xlim()
        #         ymin, ymax = plot.plot_base.get_ylim()
        #     except AttributeError as err:
        #         raise MessageError("Error", "Cannot customise plot parameters if the plot does not exist." +
        #         f"\n{err}")
        #
        # dpi = wx.ScreenDC().GetPPI()
        # if hasattr(plot, "plot_parameters"):
        #     if "panel_size" in plot.plot_parameters:
        #         plot_sizeInch = (
        #             np.round(plot.plot_parameters["panel_size"][0] / dpi[0], 2),
        #             np.round(plot.plot_parameters["panel_size"][1] / dpi[1], 2),
        #         )
        #     else:
        #         plot_size = plot.GetSize()
        #         plot_sizeInch = (np.round(plot_size[0] / dpi[0], 2), np.round(plot_size[1] / dpi[1], 2))
        # else:
        #     plot_size = plot.GetSize()
        #     plot_sizeInch = (np.round(plot_size[0] / dpi[0], 2), np.round(plot_size[1] / dpi[1], 2))
        #
        # try:
        #     kwargs = {
        #         "xmin": xmin,
        #         "xmax": xmax,
        #         "ymin": ymin,
        #         "ymax": ymax,
        #         "major_xticker": plot.plot_base.xaxis.get_major_locator(),
        #         "major_yticker": plot.plot_base.yaxis.get_major_locator(),
        #         "minor_xticker": plot.plot_base.xaxis.get_minor_locator(),
        #         "minor_yticker": plot.plot_base.yaxis.get_minor_locator(),
        #         "axes_tick_font_size": CONFIG.tickFontSize_1D,
        #         "axes_tick_font_weight": CONFIG.tickFontWeight_1D,
        #         "axes_tick_font_size": CONFIG.labelFontSize_1D,
        #         "axes_label_font_weight": CONFIG.labelFontWeight_1D,
        #         "axes_title_font_size": CONFIG.titleFontSize_1D,
        #         "axes_title_font_weight": CONFIG.titleFontWeight_1D,
        #         "xlabel": plot.plot_base.get_xlabel(),
        #         "ylabel": plot.plot_base.get_ylabel(),
        #         "title": plot.plot_base.get_title(),
        #         "plot_size": plot_sizeInch,
        #         "plot_axes": plot._axes,
        #         "plot": plot,
        #         "window_title": title,
        #     }
        # except AttributeError as err:
        #     raise MessageError("Error", "Cannot customise plot parameters if the plot does not exist." + f"\n{err}")
        #
        # dlg = DialogCustomisePlot(self, self.presenter, CONFIG, **kwargs)
        # dlg.ShowModal()

    def on_clear_plot_(self, _evt):
        """Clear current plot"""
        view_obj = self.get_view_from_name(self.current_page)
        view_obj.clear()
        pub.sendMessage("notify.message.success", message="Cleared figure")

    def on_save_figure(self, _evt):
        """Save current plot"""
        view_obj = self.get_view_from_name(self.current_page)
        view_obj.save_figure()

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

        event_id = None
        if evt is not None:
            event_id = evt.GetId()

        plot_obj = None
        if event_id is None:
            if plot is None:
                plot_obj = self.get_view_from_name(self.current_page)
            else:
                plot_obj = self.get_plot_from_name(plot)
        elif event_id is not None:
            plot_obj = self.get_plot_from_id(event_id)
        elif "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.pop("plot_obj")

        if not isinstance(plot_obj, list):
            plot_obj = [plot_obj]

        for p in plot_obj:
            if p is None:
                continue
            p.clear()  # noqa

        logger.info("Cleared plot area...")

    def on_clear_all_plots(self, _evt=None):
        """Clear all plots in the main window"""

        # Delete all plots
        view_list = [
            self.view_ms,
            self.view_rt_rt,
            self.view_dt_dt,
            self.view_heatmap,
            self.view_msdt,
            self.view_heatmap_3d,
        ]

        for view in view_list:
            view.clear()
            view.repaint()
        logger.info("Cleared all plots")

    def on_plot_ms(self, obj, allow_extraction: bool = True, set_page: bool = False) -> ViewMassSpectrum:
        """Plot mass spectrum"""
        self.view_ms.plot(obj=obj, allow_extraction=allow_extraction)

        if set_page:
            self.set_page("Mass spectrum")
        return self.view_ms

    def on_plot_1d(self, obj, allow_extraction: bool = True, set_page: bool = False) -> ViewMobilogram:
        """Plot mobilogram"""
        self.view_dt_dt.plot(obj=obj, allow_extraction=allow_extraction)

        if set_page:
            self.set_page("Mobilogram")
        return self.view_dt_dt

    def on_plot_rt(self, obj, allow_extraction: bool = True, set_page: bool = False) -> ViewChromatogram:
        """Plot chromatogram"""
        self.view_rt_rt.plot(obj=obj, allow_extraction=allow_extraction)

        if set_page:
            self.set_page("Chromatogram")
        return self.view_rt_rt

    def on_plot_2d(self, obj, allow_extraction: bool = True, set_page: bool = False) -> ViewIonHeatmap:
        """Plot heatmap"""
        self.view_heatmap.plot(obj=obj, allow_extraction=allow_extraction)

        if set_page:
            self.set_page("Heatmap")
        return self.view_heatmap

    def on_plot_dtms(self, obj, allow_extraction: bool = True, set_page: bool = False) -> ViewMassSpectrumHeatmap:
        """Plot heatmap"""
        self.view_msdt.plot(obj=obj, allow_extraction=allow_extraction)

        if set_page:
            self.set_page("DT/MS")
        return self.view_msdt

    def on_plot_3d(self, obj, allow_extraction: bool = True, set_page: bool = False) -> ViewHeatmap3d:
        """Plot heatmap"""
        self.view_heatmap_3d.plot(obj=obj, allow_extraction=allow_extraction)

        if set_page:
            self.set_page("Heatmap (3D)")
        return self.view_heatmap_3d

    def on_plot_data_object(self, data_obj: DataObject) -> ViewBase:
        """Plot data based on which data object it is

        Parameters
        ----------
        data_obj : DataObject
            container object that needs to be plotted

        Returns
        -------
        view : ViewBase
            viewer object
        """
        if isinstance(data_obj, MassSpectrumObject):
            self.view_ms.plot(obj=data_obj)
            return self.view_ms

        elif isinstance(data_obj, ChromatogramObject):
            self.view_rt_rt.plot(obj=data_obj)
            return self.view_rt_rt

        elif isinstance(data_obj, MobilogramObject):
            self.view_dt_dt.plot(obj=data_obj)
            return self.view_dt_dt

        elif isinstance(data_obj, MassSpectrumHeatmapObject):
            self.view_msdt.plot(obj=data_obj)
            return self.view_msdt

        elif isinstance(data_obj, IonHeatmapObject):
            self.view_heatmap.plot(obj=data_obj)
            return self.view_heatmap

    # def plot_update_axes(self, plotName):
    #
    #     # get current sizes
    #     axes_sizes = CONFIG._plotSettings[plotName]["axes_size"]
    #
    #     plot_obj = self.get_plot_from_name(plotName)
    #     if plot_obj is None:
    #         return
    #
    #     #         # get link to the plot
    #     #         if plotName == "MS":
    #     #             resize_plot = [self.plot1, self.plot_RT_MS, self.plot_DT_MS]
    #     #         elif plotName == "RMSD":
    #     #             resize_plot = self.plot2D
    #     #         elif plotName in ["Comparison", "Matrix"]:
    #     #             resize_plot = self.plot2D
    #     #         elif plotName in ["Overlay", "Overlay (Grid)"]:
    #     #             resize_plot = self.plot2D
    #     #         elif plotName == "Calibration (MS)":
    #     #             resize_plot = self.topPlotMS
    #     #         elif plotName == "Calibration (DT)":
    #     #             resize_plot = self.bottomPlot1DT
    #
    #     # apply new size
    #     try:
    #         if not isinstance(plot_obj, list):
    #             resize_plot = [plot_obj]
    #         for plot in resize_plot:
    #             if plot.lock_plot_from_updating:
    #                 msg = (
    #                     "This plot is locked and you cannot use global setting updated. \n"
    #                     + "Please right-click in the plot area and select Customise plot..."
    #                     + " to adjust plot settings."
    #                 )
    #                 print(msg)
    #                 continue
    #             plot.plot_update_axes(axes_sizes)
    #             plot.repaint()
    #             plot._axes = axes_sizes
    #     except (AttributeError, UnboundLocalError):
    #         logger.warning("Failed to resize plot")
    #
    # def plot_update_size(self, plotName):
    #     dpi = wx.ScreenDC().GetPPI()
    #     resizeSize = CONFIG._plotSettings[plotName]["gui_size"]
    #     figsizeNarrowPix = (int(resizeSize[0] * dpi[0]), int(resizeSize[1] * dpi[1]))
    #
    #     plot_obj = self.get_plot_from_name(plotName)
    #     if plot_obj is None:
    #         return
    #
    #     try:
    #         if plot_obj.lock_plot_from_updating:
    #             msg = (
    #                 "This plot is locked and you cannot use global setting updated. \n"
    #                 + "Please right-click in the plot area and select Customise plot..."
    #                 + " to adjust plot settings."
    #             )
    #             print(msg)
    #             return
    #         plot_obj.SetSize(figsizeNarrowPix)
    #     except (AttributeError, UnboundLocalError):
    #         logger.warning("Failed to update plot size")

    # def on_plot_other_1D(
    #     self, msX=None, msY=None, xlabel="", ylabel="", xlimits=None, set_page=False, plot="Other", **kwargs
    # ):
    #
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #         if set_page:
    #             self.set_page(CONFIG.panelNames["Other"])
    #
    #     plt_kwargs = self._buildPlotParameters(plotType="1D")
    #     plt_kwargs = merge_two_dicts(plt_kwargs, kwargs)
    #     # check limits
    #     try:
    #         if math.isnan(xlimits.get(0, msX[0])):
    #             xlimits[0] = msX[0]
    #         if math.isnan(xlimits.get(1, msX[-1])):
    #             xlimits[1] = msX[-1]
    #     except Exception:
    #         xlimits = [np.min(msX), np.max(msX)]
    #
    #     try:
    #         if len(msX[0]) > 1:
    #             msX = msX[0]
    #             msY = msY[0]
    #     except TypeError:
    #         pass
    #
    #     plot_obj.clear()
    #     plot_obj.plot_1D(
    #         xvals=msX,
    #         yvals=msY,
    #         xlimits=xlimits,
    #         xlabel=xlabel,
    #         ylabel=ylabel,
    #         axesSize=CONFIG._plotSettings["Other (Line)"]["axes_size"],
    #         plotType="MS",
    #         **plt_kwargs,
    #     )
    #     plot_obj.repaint()
    #     plot_obj.plot_type = "line"
    #
    # def on_plot_other_overlay(
    #     self, xvals, yvals, xlabel, ylabel, colors, labels, xlimits=None, set_page=False, plot="Other", **kwargs
    # ):
    #
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #         if set_page:
    #             self.set_page(CONFIG.panelNames["Other"])
    #     # Build kwargs
    #     plt_kwargs = self._buildPlotParameters(plotType="1D")
    #     plt_kwargs = merge_two_dicts(plt_kwargs, kwargs)
    #
    #     plot_obj.clear()
    #     plot_obj.plot_1D_overlay(
    #         xvals=xvals,
    #         yvals=yvals,
    #         title="",
    #         xlabel=xlabel,
    #         ylabel=ylabel,
    #         labels=labels,
    #         colors=colors,
    #         xlimits=xlimits,
    #         zoom="box",
    #         axesSize=CONFIG._plotSettings["Other (Multi-line)"]["axes_size"],
    #         plotName="1D",
    #         **plt_kwargs,
    #     )
    #     plot_obj.repaint()
    #     plot_obj.plot_type = "multi-line"
    #
    # def on_plot_other_waterfall(
    #     self, xvals, yvals, zvals, xlabel, ylabel, colors=[], set_page=False, plot="Other", **kwargs
    # ):
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #         if set_page:
    #             self.set_page(CONFIG.panelNames["Other"])
    #
    #     plt_kwargs = self._buildPlotParameters(["1D", "waterfall"])
    #     if "waterfall_increment" in kwargs:
    #         plt_kwargs["waterfall_increment"] = kwargs["waterfall_increment"]
    #
    #     # reverse labels
    #     xlabel, ylabel = ylabel, xlabel
    #
    #     plot_obj.clear()
    #     plot_obj.plot_1D_waterfall(
    #         xvals=xvals,
    #         yvals=yvals,
    #         zvals=zvals,
    #         label="",
    #         xlabel=xlabel,
    #         ylabel=ylabel,
    #         colorList=colors,
    #         labels=kwargs.get("labels", []),
    #         axesSize=CONFIG._plotSettings["Other (Waterfall)"]["axes_size"],
    #         plotName="1D",
    #         **plt_kwargs,
    #     )
    #
    #     #         if ('add_legend' in kwargs and 'labels' in kwargs and
    #     #             len(colors) == len(kwargs['labels'])):
    #     #             if kwargs['add_legend']:
    #     #                 legend_text = zip(colors, kwargs['labels'])
    #     #                 plot_obj.plot_1D_add_legend(legend_text, **plt_kwargs)
    #
    #     plot_obj.repaint()
    #     plot_obj.plot_type = "waterfall"
    #
    # def on_plot_other_scatter(
    #     self, xvals, yvals, zvals, xlabel, ylabel, colors, labels, xlimits=None, set_page=False, plot="Other",
    #     **kwargs
    # ):
    #
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #         if set_page:
    #             self.set_page(CONFIG.panelNames["Other"])
    #
    #     # Build kwargs
    #     plt_kwargs = self._buildPlotParameters(plotType="1D")
    #     plt_kwargs = merge_two_dicts(plt_kwargs, kwargs)
    #
    #     plot_obj.clear()
    #     plot_obj.plot_1D_scatter(
    #         xvals=xvals,
    #         yvals=yvals,
    #         zvals=zvals,
    #         title="",
    #         xlabel=xlabel,
    #         ylabel=ylabel,
    #         labels=labels,
    #         colors=colors,
    #         xlimits=xlimits,
    #         zoom="box",
    #         axesSize=CONFIG._plotSettings["Other (Scatter)"]["axes_size"],
    #         plotName="1D",
    #         **plt_kwargs,
    #     )
    #     plot_obj.repaint()
    #     plot_obj.plot_type = "scatter"
    #
    # def on_plot_other_grid_1D(
    #     self, xvals, yvals, xlabel, ylabel, colors, labels, set_page=False, plot="Other", **kwargs
    # ):
    #
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #         if set_page:
    #             self.set_page(CONFIG.panelNames["Other"])
    #
    #     # Build kwargs
    #     plt_kwargs = self._buildPlotParameters(plotType="1D")
    #     plt_kwargs = merge_two_dicts(plt_kwargs, kwargs)
    #
    #     plot_obj.clear()
    #     plot_obj.plot_n_grid_1D_overlay(
    #         xvals=xvals,
    #         yvals=yvals,
    #         title="",
    #         xlabel=xlabel,
    #         ylabel=ylabel,
    #         labels=labels,
    #         colors=colors,
    #         zoom="box",
    #         axesSize=CONFIG._plotSettings["Other (Grid-1D)"]["axes_size"],
    #         plotName="1D",
    #         **plt_kwargs,
    #     )
    #     plot_obj.repaint()
    #     plot_obj.plot_type = "grid-line"
    #
    # def on_plot_other_grid_scatter(
    #     self, xvals, yvals, xlabel, ylabel, colors, labels, set_page=False, plot="Other", **kwargs
    # ):
    #
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #         if set_page:
    #             self.set_page(CONFIG.panelNames["Other"])
    #
    #     # Build kwargs
    #     plt_kwargs = self._buildPlotParameters(plotType="1D")
    #     plt_kwargs = merge_two_dicts(plt_kwargs, kwargs)
    #
    #     plot_obj.clear()
    #     plot_obj.plot_n_grid_scatter(
    #         xvals=xvals,
    #         yvals=yvals,
    #         title="",
    #         xlabel=xlabel,
    #         ylabel=ylabel,
    #         labels=labels,
    #         colors=colors,
    #         zoom="box",
    #         axesSize=CONFIG._plotSettings["Other (Grid-1D)"]["axes_size"],
    #         plotName="1D",
    #         **plt_kwargs,
    #     )
    #     plot_obj.repaint()
    #     plot_obj.plot_type = "grid-scatter"
    #
    # def on_plot_other_bars(
    #     self, xvals, yvals_min, yvals_max, xlabel, ylabel, colors, set_page=False, plot="Other", **kwargs
    # ):
    #
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #         if set_page:
    #             self.set_page(CONFIG.panelNames["Other"])
    #
    #     # Build kwargs
    #     plt_kwargs = self._buildPlotParameters(plotType="1D")
    #     plt_kwargs = merge_two_dicts(plt_kwargs, kwargs)
    #
    #     plot_obj.clear()
    #     plot_obj.plot_floating_barplot(
    #         xvals=xvals,
    #         yvals_min=yvals_min,
    #         yvals_max=yvals_max,
    #         itle="",
    #         xlabel=xlabel,
    #         ylabel=ylabel,
    #         colors=colors,
    #         zoom="box",
    #         axesSize=CONFIG._plotSettings["Other (Barplot)"]["axes_size"],
    #         **plt_kwargs,
    #     )
    #     plot_obj.repaint()
    #     plot_obj.plot_type = "bars"
    #
    #
    # def on_add_centroid_MS_and_labels(
    #     self,
    #     msX,
    #     msY,
    #     labels,
    #     full_labels,
    #     xlimits=None,
    #     title="",
    #     butterfly_plot=False,
    #     set_page=False,
    #     plot="MS",
    #     **kwargs,
    # ):
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #         if set_page:
    #             self.set_page(CONFIG.panelNames["MS"])
    #
    #     # Build kwargs
    #     plt_kwargs = self._buildPlotParameters(plotType="1D")
    #     plt_kwargs["spectrum_line_color"] = CONFIG.msms_line_color_labelled
    #     plt_kwargs["butterfly_plot"] = butterfly_plot
    #
    #     plot_name = "MS"
    #     plot_size = CONFIG._plotSettings["MS"]["axes_size"]
    #     if butterfly_plot:
    #         plot_name = "compareMS"
    #         plot_size = CONFIG._plotSettings["MS (compare)"]["axes_size"]
    #
    #     xylimits = self.plot_ms.get_xy_limits()
    #     plot_obj.plot_1D_centroid(
    #         xvals=msX,
    #         yvals=msY,
    #         xlimits=xlimits,
    #         update_y_axis=False,
    #         xlabel="m/z",
    #         ylabel="Intensity",
    #         title=title,
    #         axesSize=plot_size,
    #         plot_name=plot_name,
    #         adding_on_top=True,
    #         **plt_kwargs,
    #     )
    #
    #     # add labels
    #     plt_label_kwargs = {
    #         "horizontalalignment": CONFIG.annotation_label_horz,
    #         "verticalalignment": CONFIG.annotation_label_vert,
    #         "check_yscale": True,
    #         "add_arrow_to_low_intensity": CONFIG.msms_add_arrows,
    #         "butterfly_plot": butterfly_plot,
    #         "fontweight": CONFIG.annotation_label_font_weight,
    #         "fontsize": CONFIG.annotation_label_font_size,
    #         "rotation": CONFIG.annotation_label_font_orientation,
    #     }
    #
    #     for i in range(len(labels)):
    #         xval, yval, label, full_label = msX[i], msY[i], labels[i], full_labels[i]
    #
    #         if not CONFIG.msms_show_neutral_loss:
    #             if "H2O" in full_label or "NH3" in full_label:
    #                 continue
    #
    #         if CONFIG.msms_show_full_label:
    #             label = full_label
    #
    #         plot_obj.plot_add_label(
    #             xpos=xval, yval=yval, label=label, yoffset=CONFIG.msms_label_y_offset, **plt_label_kwargs
    #         )
    #
    #     if i == len(labels) - 1 and not butterfly_plot:
    #         plot_obj.set_xy_limits(xylimits)
    #
    #     plot_obj.repaint()
    #
    # def on_plot_centroid_MS(
    #     self, msX, msY, msXY=None, xlimits=None, title="", repaint=True, set_page=False, plot="MS", **kwargs
    # ):
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #         if set_page:
    #             self.set_page(CONFIG.panelNames["MS"])
    #
    #     # Build kwargs
    #     plt_kwargs = self._buildPlotParameters(plotType="1D")
    #     plt_kwargs["spectrum_line_color"] = CONFIG.msms_line_color_unlabelled
    #
    #     plot_obj.clear()
    #     plot_obj.plot_1D_centroid(
    #         xvals=msX,
    #         yvals=msY,
    #         xyvals=msXY,
    #         xlimits=xlimits,
    #         xlabel="m/z",
    #         ylabel="Intensity",
    #         title=title,
    #         axesSize=CONFIG._plotSettings["MS"]["axes_size"],
    #         plotType="MS",
    #         **plt_kwargs,
    #     )
    #     if repaint:
    #         plot_obj.repaint()


def _main_popup():
    from origami.gui_elements._panel import TestPanel  # noqa

    class TestPopup(TestPanel):
        """Test the popup window"""

        def __init__(self, parent):
            super().__init__(parent)

            self.btn_1.Bind(wx.EVT_BUTTON, self.on_popup)

        def on_popup(self, evt):
            """Activate popup"""
            p = PopupPlotPanelSettings(self)
            p.position_on_event(evt)
            p.Show()

    app = wx.App()

    dlg = TestPopup(None)
    dlg.Show()

    app.MainLoop()


if __name__ == "__main__":
    _main_popup()
