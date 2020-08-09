"""Plotting panel"""
# Standard library imports
import time
import logging
from typing import Union

# Third-party imports
import wx
import seaborn as sns
import matplotlib
import matplotlib.pyplot as plt
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
from origami.ids import ID_extraSettings_legend
from origami.ids import ID_extraSettings_plot1D
from origami.ids import ID_extraSettings_plot2D
from origami.ids import ID_extraSettings_plot3D
from origami.ids import ID_extraSettings_violin
from origami.ids import ID_plots_customise_plot
from origami.ids import ID_extraSettings_colorbar
from origami.ids import ID_extraSettings_waterfall
from origami.ids import ID_extraSettings_general_plot
from origami.styles import make_menu_item
from origami.utils.color import convert_rgb_1_to_255
from origami.utils.color import convert_rgb_1_to_hex
from origami.icons.assets import Icons
from origami.config.config import CONFIG
from origami.objects.containers import DataObject
from origami.objects.containers import IonHeatmapObject
from origami.objects.containers import MobilogramObject
from origami.objects.containers import ChromatogramObject
from origami.objects.containers import MassSpectrumObject
from origami.objects.containers import MassSpectrumHeatmapObject
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

logger = logging.getLogger(__name__)

# 2D -> Heatmap; Other -> Annotated (or else)


class PanelPlots(wx.Panel):
    """Plotting panel instance"""

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

        self.currentPage = None
        # Extract size of screen
        self._display_size_px = wx.GetDisplaySize()
        self.SetDimensions(0, 0, self._display_size_px[0] - 320, self._display_size_px[1] - 50)
        self._display_size_mm = wx.GetDisplaySizeMM()

        self.displayRes = wx.GetDisplayPPI()
        self.figsizeX = (self._display_size_px[0] - 320) / self.displayRes[0]
        self.figsizeY = (self._display_size_px[1] - 70) / self.displayRes[1]

        # used to keep track of what were the last selected pages
        self.plot_notebook = self.make_notebook()
        self.current_plot = self.plot_ms

        self._resizing = False
        self._timer = wx.Timer(self, True)
        self.Bind(wx.EVT_TIMER, self._on_late_resize, self._timer)

        # initialise pub
        pub.subscribe(self._update_label_position, "update_text_position")

        self.plot_notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.on_page_changed)
        self.Bind(wx.EVT_SIZE, self.on_resize)

        # initialise
        self.on_page_changed(None)

    @property
    def popup_ms(self) -> PopupMassSpectrumView:
        """Return instance of the popup viewer"""

        if not self._popup_ms:
            self._popup_ms = PopupMassSpectrumView(self.view)
            self._popup_ms.position_on_mouse(-100, -100)
        self._popup_ms.Show()
        return self._popup_ms

    @property
    def popup_rt(self) -> PopupChromatogramView:
        """Return instance of the popup viewer"""
        if not self._popup_rt:
            self._popup_rt = PopupChromatogramView(self.view)
            self._popup_rt.position_on_mouse(200, 200)
        self._popup_rt.Show()
        return self._popup_rt

    @property
    def popup_dt(self) -> PopupMobilogramView:
        """Return instance of the popup viewer"""
        if not self._popup_rt:
            self._popup_rt = PopupMobilogramView(self.view)
            self._popup_rt.position_on_mouse(200, 200)
        self._popup_rt.Show()
        return self._popup_rt

    @property
    def popup_2d(self) -> PopupHeatmapView:
        """Return instance of the popup viewer"""
        if not self._popup_2d:
            self._popup_2d = PopupHeatmapView(self.view)
            self._popup_2d.position_on_mouse(200, 200)
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
        self.currentPage = self.plot_notebook.GetPageText(self.plot_notebook.GetSelection())

    def _get_page_text(self):
        self.on_get_current_page()
        return self.currentPage

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

    def on_page_changed(self, _evt):
        """Triggered by change of panel in the plot section

        Parameters
        ----------
        _evt : wxPython event
            unused
        """
        # get current page
        self.currentPage = self.plot_notebook.GetPageText(self.plot_notebook.GetSelection())

        # keep track of previous pages
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
            CONFIG._plotSettings["MS"]["gui_size"],  # noqa
            CONFIG,
            allow_extraction=True,
            callbacks=dict(CTRL="extract.heatmap.from.spectrum"),
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
            callbacks=dict(CTRL="extract.spectrum.from.chromatogram"),
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
            callbacks=dict(CTRL="extract.spectrum.from.mobilogram"),
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
            callbacks=dict(CTRL="extract.spectrum.from.heatmap"),
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
            callbacks=dict(CTRL="extract.rt.from.heatmap"),
            filename="ms-heatmap",
        )
        plot_notebook.AddPage(self.view_msdt.panel, "DT/MS")
        self.plot_msdt = self.view_msdt.figure

        # # Setup PLOT WATERFALL
        # self.panel_overlay, self.plot_overlay, __ = self.make_base_plot(
        #     plot_notebook, CONFIG._plotSettings["Waterfall"]["gui_size"]  # noqa
        # )
        # plot_notebook.AddPage(self.panel_overlay, "Waterfall", False)

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

        # # Other
        # self.panel_annotated, self.plot_annotated, __ = self.make_base_plot(
        #     plot_notebook, CONFIG._plotSettings["2D"]["gui_size"]  # noqa
        # )
        # plot_notebook.AddPage(self.panel_annotated, "Annotated", False)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(plot_notebook, 1, wx.EXPAND | wx.ALL, 1)
        self.SetSizer(main_sizer)
        self.Layout()
        self.Show()

        self.Bind(wx.EVT_CONTEXT_MENU, self.on_right_click)

        return plot_notebook

    def on_copy_to_clipboard(self, _evt):
        """Copy plot to clipboard"""
        plot_obj = self.get_plot_from_name(self.currentPage)
        plot_obj.copy_to_clipboard()
        pub.sendMessage("notify.message.success", message="Copied figure to clipboard!")

    def on_smooth_object(self, _evt):
        """Smooth plot signal"""
        from origami.gui_elements.misc_dialogs import DialogSimpleAsk

        view_obj = self.get_view_from_name(self.currentPage)
        obj = view_obj.get_object(get_cache=False)

        if obj is None:
            pub.sendMessage("notify.message.warning", message="Cannot smooth object as the plot cache is empty")
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
        view_obj = self.get_view_from_name(self.currentPage)
        mz_obj = view_obj.get_object()
        self.document_tree.on_open_process_ms_settings(mz_obj=mz_obj, disable_process=True)

    def on_process_heatmap(self, _evt):
        """Process heatmap"""
        view_obj = self.get_view_from_name(self.currentPage)
        heatmap_obj = view_obj.get_object()
        self.document_tree.on_open_process_heatmap_settings(heatmap_obj=heatmap_obj, disable_process=True)

    def on_rotate_plot(self, _evt):
        """Rotate heatmap plot"""
        view_obj = self.get_view_from_name(self.currentPage)
        heatmap_obj = view_obj.get_object()

        view_obj.plot(obj=heatmap_obj.transpose(), repaint=False)
        view_obj.reset_zoom()

    def on_open_peak_picker(self, _evt):
        """Open peak picker window"""
        view_obj = self.get_view_from_name(self.currentPage)
        mz_obj = view_obj.get_object()
        document_title, dataset_name = mz_obj.owner

        if document_title is None or dataset_name is None:
            pub.sendMessage(
                "notify.message.warning",
                message="Could not find the document/dataset information in the plot metadata."
                "\nTry right-clicking on a mass spectrum in the document tree and select `Open peak picker`",
            )
            return

        self.document_tree.on_open_peak_picker(None, document_title=document_title, dataset_name=dataset_name)

    def on_open_annotations_panel(self, _evt):
        """Open the annotations panel for particular object"""
        view_obj = self.get_view_from_name(self.currentPage)

        data_obj = view_obj.get_object()
        document_title, dataset_name = data_obj.owner

        # check whether data object has document/dataset associated with it
        if document_title is None or dataset_name is None:
            pub.sendMessage(
                "notify.message.warning",
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
        view_obj = self.get_view_from_name(self.currentPage)
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
        view_obj = self.get_view_from_name(self.currentPage)
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
        view_obj = self.get_view_from_name(self.currentPage)
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
        view_obj = self.get_view_from_name(self.currentPage)
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
        view_obj = self.get_view_from_name(self.currentPage)
        data_obj = view_obj.get_object()
        if not data_obj:
            pub.sendMessage("notify.message.error", message="Cannot show this view as the plot cache is empty.")
            return

        view_obj.plot(obj=data_obj)

    def on_show_as_heatmap_3d(self, _evt):
        """Show heatmap plot as heatmap-plot"""
        view_obj = self.get_view_from_name(self.currentPage)
        data_obj = view_obj.get_object()
        if not data_obj:
            pub.sendMessage("notify.message.error", message="Cannot show this view as the plot cache is empty.")
            return

        self.view_heatmap_3d.plot(obj=data_obj)
        self.set_page("Heatmap (3D)")

    def on_right_click(self, _evt):
        """Right-click event handler"""
        self.currentPage = self.plot_notebook.GetPageText(self.plot_notebook.GetSelection())

        # Make bindings
        self.Bind(wx.EVT_MENU, self.on_customise_plot, id=ID_plots_customise_plot)
        #         self.Bind(wx.EVT_MENU, self.on_customise_smart_zoom, id=ID_plots_customise_smart_zoom)

        view = self.get_view_from_name()
        menu = view.get_right_click_menu(self)

        # pre-generate common menu items
        menu_edit_general = make_menu_item(
            parent=menu,
            evt_id=ID_extraSettings_general_plot,
            text="Edit general parameters...",
            bitmap=self._icons.gear,
        )
        menu_edit_plot_1d = make_menu_item(
            parent=menu, evt_id=ID_extraSettings_plot1D, text="Edit plot parameters...", bitmap=self._icons.plot_1d
        )
        menu_edit_plot_2d = make_menu_item(
            parent=menu, evt_id=ID_extraSettings_plot2D, text="Edit plot parameters...", bitmap=self._icons.heatmap
        )
        menu_edit_plot_3d = make_menu_item(
            parent=menu, evt_id=ID_extraSettings_plot3D, text="Edit plot parameters...", bitmap=self._icons.overlay
        )
        menu_edit_colorbar = make_menu_item(
            parent=menu,
            evt_id=ID_extraSettings_colorbar,
            text="Edit colorbar parameters...",
            bitmap=self._icons.plot_colorbar,
        )
        menu_edit_legend = make_menu_item(
            parent=menu,
            evt_id=ID_extraSettings_legend,
            text="Edit legend parameters...",
            bitmap=self._icons.plot_legend,
        )
        #         menu_edit_rmsd = make_menu_item(
        #             parent=menu,
        #             id=ID_extraSettings_rmsd,
        #             text="Edit plot parameters...",
        #             bitmap=self.icons.iconsLib["panel_rmsd_16"],
        #         )
        menu_edit_waterfall = make_menu_item(
            parent=menu,
            evt_id=ID_extraSettings_waterfall,
            text="Edit waterfall parameters...",
            bitmap=self._icons.waterfall,
        )
        menu_edit_violin = make_menu_item(
            parent=menu, evt_id=ID_extraSettings_violin, text="Edit violin parameters...", bitmap=self._icons.violin
        )
        menu_action_rotate90 = make_menu_item(parent=menu, text="Rotate 90°", bitmap=self._icons.rotate)
        menu_action_process_2d = make_menu_item(
            parent=menu, text="Process heatmap...", bitmap=self._icons.process_heatmap
        )

        menu_action_process_ms = make_menu_item(
            parent=menu, text="Process mass spectrum...", bitmap=self._icons.process_ms
        )

        menu_action_process_pick = make_menu_item(parent=menu, text="Open peak picker...", bitmap=self._icons.highlight)

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
        self.Bind(wx.EVT_MENU, self.on_process_mass_spectrum, menu_action_process_ms)
        self.Bind(wx.EVT_MENU, self.on_process_heatmap, menu_action_process_2d)
        self.Bind(wx.EVT_MENU, self.on_rotate_plot, menu_action_rotate90)
        self.Bind(wx.EVT_MENU, self.on_open_peak_picker, menu_action_process_pick)
        self.Bind(wx.EVT_MENU, self.on_smooth_object, menu_action_smooth_signal)
        self.Bind(wx.EVT_MENU, self.on_smooth_object, menu_action_smooth_heatmap)
        self.Bind(wx.EVT_MENU, self.on_open_annotations_panel, menu_action_open_annotations)
        self.Bind(wx.EVT_MENU, self.on_show_as_joint, menu_action_show_joint)
        self.Bind(wx.EVT_MENU, self.on_show_as_contour, menu_action_show_contour)
        self.Bind(wx.EVT_MENU, self.on_show_as_waterfall, menu_action_show_waterfall)
        self.Bind(wx.EVT_MENU, self.on_show_as_heatmap, menu_action_show_heatmap)
        self.Bind(wx.EVT_MENU, self.on_show_as_violin, menu_action_show_violin)
        self.Bind(wx.EVT_MENU, self.on_show_as_heatmap_3d, menu_action_show_3d)

        if self.currentPage == "Mass spectrum":
            menu.Insert(0, menu_action_smooth_signal)
            menu.Insert(1, menu_action_process_ms)
            menu.Insert(2, menu_action_process_pick)
            menu.Insert(3, menu_action_open_annotations)
            menu.InsertSeparator(4)
            menu.Insert(5, menu_edit_general)
            menu.Insert(6, menu_edit_plot_1d)
        elif self.currentPage == "Chromatogram":
            menu.Insert(0, menu_action_smooth_signal)
            menu.Insert(1, menu_action_open_annotations)
            menu.InsertSeparator(2)
            menu.Insert(3, menu_edit_general)
            menu.Insert(4, menu_edit_plot_1d)
            menu.Insert(5, menu_edit_legend)
        elif self.currentPage == "Mobilogram":
            menu.Insert(0, menu_action_smooth_signal)
            menu.Insert(1, menu_action_open_annotations)
            menu.InsertSeparator(2)
            menu.Insert(3, menu_edit_general)
            menu.Insert(4, menu_edit_plot_1d)
            menu.Insert(5, menu_edit_legend)
        elif self.currentPage == "Heatmap":
            menu.Insert(0, menu_action_show_heatmap)
            menu.Insert(1, menu_action_show_contour)
            menu.Insert(2, menu_action_show_waterfall)
            menu.Insert(3, menu_action_show_violin)
            menu.Insert(4, menu_action_show_joint)
            menu.Insert(4, menu_action_show_3d)
            menu.InsertSeparator(5)
            menu.Insert(6, menu_action_smooth_heatmap)
            menu.Insert(7, menu_action_process_2d)
            menu.Insert(8, menu_action_rotate90)
            menu.Insert(9, menu_action_open_annotations)
            menu.InsertSeparator(10)
            menu.Insert(11, menu_edit_general)
            menu.Insert(12, menu_edit_plot_2d)
            menu.Insert(13, menu_edit_colorbar)
            menu.Insert(14, menu_edit_waterfall)
            menu.Insert(15, menu_edit_violin)
        elif self.currentPage == "DT/MS":
            menu.Insert(0, menu_action_show_heatmap)
            menu.Insert(1, menu_action_show_contour)
            menu.Insert(2, menu_action_show_joint)
            menu.InsertSeparator(3)
            menu.Insert(4, menu_action_smooth_heatmap)
            menu.Insert(5, menu_action_process_2d)
            menu.Insert(6, menu_action_rotate90)
            menu.Insert(7, menu_action_open_annotations)
            menu.InsertSeparator(8)
            menu.Insert(9, menu_edit_general)
            menu.Insert(10, menu_edit_plot_2d)
            menu.Insert(11, menu_edit_colorbar)
        elif self.currentPage == "Heatmap (3D)":
            menu.Insert(0, menu_action_smooth_heatmap)
            menu.InsertSeparator(1)
            menu.Insert(2, menu_edit_plot_3d)

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def on_save_image(self, plot, filename, **kwargs):
        """Save image"""
        t_start = time.time()

        if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
            plot_obj = kwargs.get("plot_obj")
        else:
            plot_obj = self.get_plot_from_name(plot)

        extension = CONFIG.imageFormat
        resize_name = kwargs.pop("resize_name", None)

        if not filename.endswith(f".{extension}"):
            filename += f".{extension}"

        # build kwargs
        kwargs = {
            "transparent": CONFIG.transparent,
            "dpi": CONFIG.dpi,
            "format": extension,
            "compression": "zlib",
            "resize": None,
            "tight": CONFIG.image_tight,
            "image_size_inch": None,
            "image_size_px": None,
            "image_axes_size": None,
        }

        if CONFIG.resize and resize_name is not None:
            kwargs["resize"] = resize_name
            kwargs["image_size_inch"] = CONFIG.image_size_inch
            kwargs["image_size_px"] = CONFIG.image_size_px
            kwargs["image_axes_size"] = CONFIG.image_axes_size

        plot_obj.save_figure(filename, **kwargs)

        logger.info(f"Saved figure {filename} in {time.time()-t_start:.2f} seconds")

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
            plot_name = self.currentPage
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

    def on_lock_plot(self, _evt):
        """Lock/unlock plot"""
        plot_obj = self.get_plot_from_name(self.currentPage)
        plot_obj.lock_plot_from_updating = not plot_obj.lock_plot_from_updating

    @staticmethod
    def on_resize_check(_evt):
        """Enable/disable plot resizing"""
        CONFIG.resize = not CONFIG.resize

    #     def on_customise_smart_zoom(self, _evt):
    #         """Customise smart zoom in the MS/DT plot"""
    #         from origami.gui_elements.dialog_customise_smart_zoom import DialogCustomiseSmartZoom
    #
    #         dlg = DialogCustomiseSmartZoom(self)
    #         dlg.ShowModal()

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

    @staticmethod
    def on_change_plot_style():
        """Change plot style"""
        # https://tonysyu.github.io/raw_content/matplotlib-style-gallery/gallery.html

        if CONFIG.current_style == "Default":
            matplotlib.rcParams.update(matplotlib.rcParamsDefault)
        elif CONFIG.current_style == "ggplot":
            plt.style.use("ggplot")
        elif CONFIG.current_style == "ticks":
            sns.set_style("ticks")
        else:
            plt.style.use(CONFIG.current_style)

    @staticmethod
    def on_change_color_palette(evt, cmap=None, n_colors=16, return_colors=False, return_hex=False):  # noqa
        """Change color palette"""
        if cmap is not None:
            palette_name = cmap
        else:
            if CONFIG.current_palette in ["Spectral", "RdPu"]:
                palette_name = CONFIG.current_palette
            else:
                palette_name = CONFIG.current_palette.lower()

        new_colors = sns.color_palette(palette_name, n_colors)

        if not return_colors:
            for i in range(n_colors):
                CONFIG.custom_colors[i] = convert_rgb_1_to_255(new_colors[i])
        else:
            if return_hex:
                new_colors_hex = []
                for new_color in new_colors:
                    new_colors_hex.append(convert_rgb_1_to_hex(new_color))
                return new_colors_hex
            else:
                return new_colors

    @staticmethod
    def on_get_colors_from_colormap(n_colors: int):
        """Return list of colors from colormap"""
        color_list = sns.color_palette(CONFIG.heatmap_colormap, n_colors)
        return color_list

    def on_clear_plot_(self, _evt):
        """Clear current plot"""
        view_obj = self.get_view_from_name(self.currentPage)
        view_obj.clear()
        pub.sendMessage("notify.message.success", message="Cleared figure")

    def on_save_figure(self, _evt):
        """Save current plot"""
        view_obj = self.get_view_from_name(self.currentPage)
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
                plot_obj = self.get_view_from_name(self.currentPage)
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

    # def on_change_rmsf_zoom(self, xmin, xmax):
    #     """Receives a message about change in RMSF plot"""
    #     try:
    #         self.plot_objs["RMSF"].onZoomRMSF(xmin, xmax)
    #     except (AttributeError, KeyError) as err:
    #         logger.error(f"Could not zoom-in on RMSF. {err}")
    #
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

    # def on_clear_patches(self, plot="MS", repaint=False, **kwargs):
    #
    #     if plot == "MS":
    #         self.plot_ms.plot_remove_patches()
    #         if repaint:
    #             self.plot_ms.repaint()
    #
    #     elif plot == "CalibrationMS":
    #         self.topPlotMS.plot_remove_patches()
    #         if repaint:
    #             self.topPlotMS.repaint()
    #
    #     elif plot == "RT":
    #         self.plot_rt_rt.plot_remove_patches()
    #         if repaint:
    #             self.plot_rt_rt.repaint()
    #
    #     elif "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #         plot_obj.plot_remove_patches()
    #         if repaint:
    #             plot_obj.repaint()
    #
    # def plot_repaint(self, plot_window="MS"):
    #     if plot_window == "MS":
    #         self.plot_ms.repaint()
    #
    # def plot_remove_patches_with_labels(self, label, plot_window="2D", refresh=False):
    #     if plot_window == "MS":
    #         self.plot_ms.plot_remove_patch_with_label(label)
    #
    #         if refresh:
    #             self.plot_ms.repaint()
    #
    # def on_plot_patches(
    #     self, xmin, ymin, width, height, color="r", alpha=0.5, label="", plot="MS", repaint=False, **kwargs
    # ):
    #
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.pop("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #
    #     plot_obj.plot_add_patch(xmin, ymin, width, height, color=color, alpha=alpha, label=label, **kwargs)
    #     if repaint:
    #         plot_obj.repaint()
    #
    # def on_clear_labels(self, plot="MS", **kwargs):
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #
    #     plot_obj.plot_remove_text_and_lines()
    #
    # def on_plot_labels(self, xpos, yval, label="", plot="MS", repaint=False, optimise_labels=False, **kwargs):
    #
    #     plt_kwargs = {
    #         "horizontalalignment": kwargs.pop("annotation_label_horz", "center"),
    #         "verticalalignment": kwargs.pop("annotation_label_vert", "center"),
    #         "check_yscale": kwargs.pop("check_yscale", False),
    #         "butterfly_plot": kwargs.pop("butterfly_plot", False),
    #         "fontweight": kwargs.pop("annotation_label_font_weight", "normal"),
    #         "fontsize": kwargs.pop("annotation_label_font_size", "medium"),
    #     }
    #
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #
    #     if plot == "MS":
    #         plot_obj.plot_add_label(xpos, yval, label, yoffset=kwargs.get("yoffset", 0.0), **plt_kwargs)
    #     elif plot == "CalibrationMS":
    #         plot_obj.plot_add_label(xpos, yval, label, **plt_kwargs)
    #
    #     elif "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj.plot_add_label(xpos, yval, label, **plt_kwargs)
    #
    #     if optimise_labels:
    #         plot_obj._fix_label_positions()
    #
    #     if not repaint:
    #         return
    #
    #     self.plot_ms.repaint()
    #
    # def on_plot_markers(self, xvals, yvals, color="b", marker="o", size=5, plot="MS", repaint=True, **kwargs):
    #     if plot == "MS":
    #         self.plot_ms.plot_add_markers(
    #             xvals=xvals, yvals=yvals, color=color, marker=marker, size=size, test_yvals=True
    #         )
    #         if not repaint:
    #             return
    #         else:
    #             self.plot_ms.repaint()
    #
    #     elif plot == "RT":
    #         self.plot_rt_rt.plot_add_markers(xvals=xvals, yvals=yvals, color=color, marker=marker, size=size)
    #         self.plot_rt_rt.repaint()
    #     # elif plot == "CalibrationMS":
    #     #     self.topPlotMS.plot_add_markers(xval=xvals, yval=yvals, color=color, marker=marker, size=size)
    #     #     self.topPlotMS.repaint()
    #     # elif plot == "CalibrationDT":
    #     #     self.bottomPlot1DT.plot_add_markers(
    #     #         xvals=xvals, yvals=yvals, color=color, marker=marker, size=size, testMax="yvals"
    #     #     )
    #     #     self.bottomPlot1DT.repaint()
    #
    # def on_clear_markers(self, plot="MS", repaint=False, **kwargs):
    #
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #
    #     plot_obj.plot_remove_markers()
    #
    #     if repaint:
    #         plot_obj.repaint()
    #
    # def _get_color_list(self, colorList, count=None, **kwargs):
    #     """
    #     colorList : list
    #        list of colors to replace
    #     kwargs : dict
    #         dictionary with appropriate keys (color_scheme, colormap)
    #     """
    #     if colorList is None:
    #         n_count = count
    #     else:
    #         n_count = len(colorList)
    #
    #     #         print(kwargs['color_scheme'], n_count, kwargs['colormap'], kwargs['palette'])
    #     if kwargs["color_scheme"] == "Colormap":
    #         colorlist = sns.color_palette(kwargs["heatmap_colormap"], n_count)
    #     elif kwargs["color_scheme"] == "Color palette":
    #         if kwargs["palette"] not in ["Spectral", "RdPu"]:
    #             kwargs["palette"] = kwargs["palette"].lower()
    #         colorlist = sns.color_palette(kwargs["palette"], n_count)
    #     elif kwargs["color_scheme"] == "Same color":
    #         colorlist = [kwargs["spectrum_line_color"]] * n_count
    #     elif kwargs["color_scheme"] == "Random":
    #         colorlist = []
    #         for __ in range(n_count):
    #             colorlist.append(get_random_color())
    #
    #     return colorlist
    #
    # def _on_change_unidec_page(self, page_id, **kwargs):
    #     if CONFIG.unidec_plot_panel_view == "Tabbed view" and kwargs.get("set_page", False):
    #         try:
    #             self.unidec_notebook.SetSelection(page_id)
    #         except Exception:
    #             pass
    #
    # def on_plot_charge_states(self, position, charges, plot="UniDec_peaks", **kwargs):
    #
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #         self._on_change_unidec_page(4, **kwargs)
    #
    #     plot_obj.plot_remove_text_and_lines()
    #
    #     if CONFIG.unidec_show_chargeStates:
    #         for position, charge in zip(position, charges):
    #             plot_obj.plot_add_text_and_lines(
    #                 xpos=position, yval=CONFIG.unidec_charges_offset, label=charge, stick_to_intensity=True
    #             )
    #     plot_obj.repaint()
    #
    # def on_add_horizontal_line(self, xmin, xmax, yval, plot_obj):
    #     plot_obj.plot_add_line(xmin, xmax, yval, yval, "horizontal")
    #     plot_obj.repaint()
    #
    # def on_plot_unidec_ChargeDistribution(
    #     self, xvals=None, yvals=None, replot=None, xlimits=None, plot="UniDec_charge", **kwargs
    # ):
    #     """
    #     Plot simple Mass spectrum before it is pre-processed
    #     @param unidec_eng_data (object):  reference to unidec engine data structure
    #     @param xlimits: unused
    #     """
    #
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #         self._on_change_unidec_page(6, **kwargs)
    #
    #     if replot is not None:
    #         xvals = replot[:, 0]
    #         yvals = replot[:, 1]
    #
    #     # Build kwargs
    #     plt_kwargs = self._buildPlotParameters(plotType="1D")
    #
    #     plot_obj.clear()
    #     plot_obj.plot_1D(
    #         xvals=xvals,
    #         yvals=yvals,
    #         xlimits=xlimits,
    #         xlabel="Charge",
    #         ylabel="Intensity",
    #         testMax=None,
    #         axesSize=CONFIG._plotSettings["UniDec (Charge Distribution)"]["axes_size"],
    #         plotType="ChargeDistribution",
    #         title="Charge State Distribution",
    #         allowWheel=False,
    #         **plt_kwargs,
    #     )
    #     # Show the mass spectrum
    #     plot_obj.repaint()
    #
    # def on_plot_unidec_MS(self, unidec_eng_data=None, replot=None, xlimits=None, plot="UniDec_MS", **kwargs):
    #     """
    #     Plot simple Mass spectrum before it is pre-processed
    #     @param unidec_eng_data (object):  reference to unidec engine data structure
    #     @param xlimits: unused
    #     """
    #
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #         self._on_change_unidec_page(0, **kwargs)
    #
    #     plt_kwargs = self._buildPlotParameters(plotType="1D")
    #
    #     if unidec_eng_data is None and replot is not None:
    #         xvals = replot["xvals"]
    #         yvals = replot["yvals"]
    #
    #     plot_obj.clear()
    #     plot_obj.plot_1D(
    #         xvals=xvals,
    #         yvals=yvals,
    #         xlimits=xlimits,
    #         xlabel="m/z",
    #         ylabel="Intensity",
    #         axesSize=CONFIG._plotSettings["UniDec (MS)"]["axes_size"],
    #         plotType="MS",
    #         title="MS",
    #         allowWheel=False,
    #         **plt_kwargs,
    #     )
    #     # Show the mass spectrum
    #     plot_obj.repaint()
    #
    # def on_plot_unidec_MS_v_Fit(self, unidec_eng_data=None, replot=None, xlimits=None, plot="UniDec_MS", **kwargs):
    #
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #         self._on_change_unidec_page(0, **kwargs)
    #
    #     # Build kwargs
    #     plt_kwargs = self._buildPlotParameters(["1D", "UniDec"])
    #
    #     if unidec_eng_data is None and replot is not None:
    #         xvals = replot["xvals"]
    #         yvals = replot["yvals"]
    #         colors = replot["colors"]
    #         labels = replot["labels"]
    #
    #     colors[1] = plt_kwargs["fit_line_color"]
    #
    #     plot_obj.clear()
    #     plot_obj.plot_1D_overlay(
    #         xvals=xvals,
    #         yvals=yvals,
    #         labels=labels,
    #         colors=colors,
    #         xlimits=xlimits,
    #         xlabel="m/z",
    #         ylabel="Intensity",
    #         axesSize=CONFIG._plotSettings["UniDec (MS)"]["axes_size"],
    #         plotType="MS",
    #         title="MS and UniDec Fit",
    #         allowWheel=False,
    #         **plt_kwargs,
    #     )
    #     # Show the mass spectrum
    #     plot_obj.repaint()
    #
    # def on_plot_unidec_mzGrid(self, unidec_eng_data=None, replot=None, plot="UniDec_mz_v_charge", **kwargs):
    #     """
    #     Plot simple Mass spectrum before it is pre-processed
    #     """
    #
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #         self._on_change_unidec_page(1, **kwargs)
    #
    #     # Build kwargs
    #     plt_kwargs = self._buildPlotParameters(plotType="2D")
    #     plt_kwargs["contour_levels"] = CONFIG.unidec_plot_contour_levels
    #     plt_kwargs["colorbar"] = True
    #
    #     if unidec_eng_data is None and replot is not None:
    #         grid = replot["grid"]
    #
    #     plot_obj.clear()
    #     plot_obj.plot_2D_contour_unidec(
    #         data=grid,
    #         xlabel="m/z (Da)",
    #         ylabel="Charge",
    #         axesSize=CONFIG._plotSettings["UniDec (m/z vs Charge)"]["axes_size"],
    #         plotType="2D",
    #         plotName="mzGrid",
    #         speedy=kwargs.get("speedy", True),
    #         title="m/z vs Charge",
    #         allowWheel=False,
    #         **plt_kwargs,
    #     )
    #     # Show the mass spectrum
    #     plot_obj.repaint()
    #
    # def on_plot_unidec_mwDistribution(
    #     self, unidec_eng_data=None, replot=None, xlimits=None, plot="UniDec_MW", **kwargs
    # ):
    #
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #         self._on_change_unidec_page(3, **kwargs)
    #
    #     # Build kwargs
    #     plt_kwargs = self._buildPlotParameters(["1D", "UniDec"])
    #
    #     if unidec_eng_data is None and replot is not None:
    #         xvals = replot["xvals"]
    #         yvals = replot["yvals"]
    #
    #     try:
    #         plot_obj.plot_1D_update_data(xvals, yvals, "Mass Distribution", "Intensity", testX=True, **plt_kwargs)
    #     except AttributeError:
    #         plot_obj.clear()
    #         plot_obj.plot_1D(
    #             xvals=xvals,
    #             yvals=yvals,
    #             xlimits=xlimits,
    #             xlabel="Mass Distribution",
    #             ylabel="Intensity",
    #             axesSize=CONFIG._plotSettings["UniDec (MW)"]["axes_size"],
    #             plotType="mwDistribution",
    #             testMax=None,
    #             testX=True,
    #             title="Zero-charge Mass Spectrum",
    #             allowWheel=False,
    #             **plt_kwargs,
    #         )
    #     plot_obj.repaint()
    #
    # def on_plot_unidec_MW_add_markers(self, data, mw_data, plot="UniDec_MW", **kwargs):
    #     """Add markers to the MW plot to indicate found peaks"""
    #
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #         self._on_change_unidec_page(1, **kwargs)
    #
    #     # remove all markers
    #     plot_obj.plot_remove_markers()
    #
    #     # build plot parameters
    #     plt_kwargs = self._buildPlotParameters(["1D", "UniDec"])
    #
    #     # get legend text
    #     legend_text = data["legend_text"]
    #     mw = np.transpose([mw_data["xvals"], mw_data["yvals"]])
    #
    #     num = 0
    #     for key in natsorted(list(data.keys())):
    #         if key.split(" ")[0] != "MW:":
    #             continue
    #         if num >= plt_kwargs["maximum_shown_items"]:
    #             continue
    #         num += 1
    #
    #     # get color list
    #     colors = self._get_color_list(None, count=num, **plt_kwargs)
    #
    #     num = 0
    #     for key in natsorted(list(data.keys())):
    #         if key.split(" ")[0] != "MW:":
    #             continue
    #         if num >= plt_kwargs["maximum_shown_items"]:
    #             continue
    #
    #         xval = float(key.split(" ")[1])
    #         yval = unidec_utils.get_peak_maximum(mw, xval=xval)
    #         marker = data[key]["marker"]
    #         color = colors[num]
    #
    #         plot_obj.plot_add_markers(
    #             xval, yval, color=color, marker=marker, size=plt_kwargs["MW_marker_size"], label=key, test_xvals=True
    #         )
    #         num += 1
    #
    #     plot_obj.plot_1D_add_legend(legend_text, **plt_kwargs)
    #     plot_obj.repaint()
    #
    # def on_plot_unidec_individualPeaks(
    #     self, unidec_eng_data=None, replot=None, xlimits=None, plot="UniDec_peaks", **kwargs
    # ):
    #     """
    #     Plot simple Mass spectrum before it is pre-processed
    #     @param unidec_eng_data (object):  reference to unidec engine data structure
    #     @param xlimits: unused
    #     """
    #
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #         self._on_change_unidec_page(4, **kwargs)
    #
    #     # Build kwargs
    #     plt_kwargs = self._buildPlotParameters(["1D", "UniDec"])
    #
    #     if unidec_eng_data is None and replot is not None:
    #         xvals = replot["xvals"]
    #         yvals = replot["yvals"]
    #
    #     # Plot MS
    #     plot_obj.clear()
    #     plot_obj.plot_1D(
    #         xvals=xvals,
    #         yvals=yvals,
    #         xlimits=xlimits,
    #         xlabel="m/z",
    #         ylabel="Intensity",
    #         axesSize=CONFIG._plotSettings["UniDec (Isolated MS)"]["axes_size"],
    #         plotType="pickedPeaks",
    #         label="Raw",
    #         allowWheel=False,
    #         **plt_kwargs,
    #     )
    #     plot_obj.repaint()
    #
    #     # add lines and markers
    #     self.on_plot_unidec_add_individual_lines_and_markers(replot=replot, plot=plot, **kwargs)
    #
    # def on_plot_unidec_add_individual_lines_and_markers(
    #     self, unidec_eng_data=None, replot=None, plot="UniDec_peaks", **kwargs
    # ):
    #
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #         self._on_change_unidec_page(4, **kwargs)
    #
    #     # remove all markers/lines and reset y-axis zoom
    #     plot_obj.plot_remove_markers()
    #     plot_obj.plot_remove_lines("MW:")
    #     plot_obj.plot_remove_text_and_lines()
    #     plot_obj.on_zoom_y_axis(0)
    #
    #     # Build kwargs
    #     plt_kwargs = self._buildPlotParameters(["1D", "UniDec"])
    #
    #     if unidec_eng_data is None and replot is not None:
    #         legend_text = replot["legend_text"]
    #
    #     if kwargs.get("show_isolated_mw", False):
    #         legend_text = [[[0, 0, 0], "Raw"]]
    #
    #     # get number of lines in the dataset
    #     num = 0
    #     color_num = 0
    #     for key in natsorted(list(replot.keys())):
    #         if key.split(" ")[0] != "MW:":
    #             continue
    #         color_num += 1
    #         if num >= plt_kwargs["maximum_shown_items"]:
    #             continue
    #         num += 1
    #
    #     # get colorlist
    #     colors = self._get_color_list(None, count=color_num, **plt_kwargs)
    #
    #     # iteratively add lines
    #     num, mw_num = 0, 0
    #     for key in natsorted(list(replot.keys())):
    #         if not kwargs["show_markers"] and not kwargs["show_individual_lines"]:
    #             break
    #
    #         if key.split(" ")[0] != "MW:":
    #             continue
    #         if num >= plt_kwargs["maximum_shown_items"]:
    #             continue
    #
    #         scatter_yvals = replot[key]["scatter_yvals"]
    #         line_yvals = replot[key]["line_yvals"]
    #         if kwargs.get("show_isolated_mw", False):
    #             if key != kwargs["mw_selection"]:
    #                 mw_num += 1
    #                 continue
    #             else:
    #                 print(len(colors), mw_num)
    #                 color = colors[mw_num]
    #                 legend_text.append([color, replot[key]["label"]])
    #                 # adjust offset so its closer to the MS plot
    #                 offset = np.min(replot[key]["line_yvals"]) + CONFIG.unidec_lineSeparation
    #                 line_yvals = line_yvals - offset
    #         else:
    #             color = colors[num]
    #             legend_text[num + 1][0] = color
    #
    #         # plot markers
    #         if kwargs["show_markers"]:
    #             plot_obj.plot_add_markers(
    #                 replot[key]["scatter_xvals"],
    #                 scatter_yvals,
    #                 color=color,  # colors[num],
    #                 marker=replot[key]["marker"],
    #                 size=plt_kwargs["isolated_marker_size"],
    #                 label=replot[key]["label"],
    #             )
    #         # plot lines
    #         if kwargs["show_individual_lines"]:
    #             plot_obj.plot_1D_add(
    #                 replot[key]["line_xvals"],
    #                 line_yvals,
    #                 color=color,
    #                 label=replot[key]["label"],
    #                 allowWheel=False,
    #                 plot_name="pickedPeaks",
    #                 update_extents=True,
    #                 setup_zoom=False,
    #                 **plt_kwargs,
    #             )
    #         num += 1
    #
    #     # modify legend
    #     if len(legend_text) - 1 > plt_kwargs["maximum_shown_items"]:
    #         msg = (
    #             "Only showing {} out of {} items.".format(plt_kwargs["maximum_shown_items"], len(legend_text) - 1)
    #             + " If you would like to see more go to Processing -> UniDec -> Max shown"
    #         )
    #         logger.info(msg)
    #
    #     legend_text = legend_text[: num + 1]
    #     # Add legend
    #     if len(legend_text) >= plt_kwargs["maximum_shown_items"]:
    #         legend_text = legend_text[: plt_kwargs["maximum_shown_items"]]
    #
    #     plot_obj.plot_1D_add_legend(legend_text, **plt_kwargs)
    #     plot_obj.repaint()
    #
    # def on_plot_unidec_MW_v_Charge(self, unidec_eng_data=None, replot=None, plot="UniDec_mw_v_charge", **kwargs):
    #     """
    #     Plot simple Mass spectrum before it is pre-processed
    #     @param unidec_eng_data (object):  reference to unidec engine data structure
    #     """
    #
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #         self._on_change_unidec_page(2, **kwargs)
    #
    #     # Build kwargs
    #     plt_kwargs = self._buildPlotParameters(plotType="2D")
    #     plt_kwargs["contour_levels"] = CONFIG.unidec_plot_contour_levels
    #     plt_kwargs["colorbar"] = True
    #
    #     if unidec_eng_data is None and replot is not None:
    #         xvals = replot["xvals"]
    #         yvals = replot["yvals"]
    #         zvals = replot["zvals"]
    #     else:
    #         xvals = unidec_eng_data.massdat[:, 0]
    #         yvals = unidec_eng_data.ztab
    #         zvals = unidec_eng_data.massgrid
    #
    #     # Check that cmap modifier is included
    #     cmapNorm = self.normalize_colormap(
    #         zvals, min=CONFIG.minCmap, mid=CONFIG.midCmap, max=CONFIG.maxCmap
    #     )
    #     plt_kwargs["colormap_norm"] = cmapNorm
    #
    #     plot_obj.clear()
    #     plot_obj.plot_2D_contour_unidec(
    #         xvals=xvals,
    #         yvals=yvals,
    #         zvals=zvals,
    #         xlabel="Mass (Da)",
    #         ylabel="Charge",
    #         axesSize=CONFIG._plotSettings["UniDec (MW vs Charge)"]["axes_size"],
    #         plotType="MS",
    #         plotName="mwGrid",
    #         testX=True,
    #         speedy=kwargs.get("speedy", True),
    #         title="Mass vs Charge",
    #         **plt_kwargs,
    #     )
    #     # Show the mass spectrum
    #     plot_obj.repaint()
    #
    # def on_plot_unidec_barChart(self, unidec_eng_data=None, replot=None, show="height", plot="UniDec_bar", **kwargs):
    #     """
    #     Plot simple Mass spectrum before it is pre-processed
    #     @param unidec_eng_data (object):  reference to unidec engine data structure
    #     """
    #
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #         self._on_change_unidec_page(5, **kwargs)
    #
    #     # Build kwargs
    #     plt_kwargs = self._buildPlotParameters(["1D", "UniDec"])
    #
    #     if unidec_eng_data is None and replot is not None:
    #         xvals = replot["xvals"]
    #         yvals = replot["yvals"]
    #         labels = replot["labels"]
    #         colors = replot["colors"]
    #         legend_text = replot["legend_text"]
    #         markers = replot["markers"]
    #
    #         if len(xvals) > plt_kwargs["maximum_shown_items"]:
    #             msg = (
    #                 "Only showing {} out of {} items.".format(plt_kwargs["maximum_shown_items"], len(xvals))
    #                 + " If you would like to see more go to Processing -> UniDec -> Max shown"
    #             )
    #             self.presenter.onThreading(None, (msg, 4, 7), action="updateStatusbar")
    #
    #         if len(xvals) >= plt_kwargs["maximum_shown_items"]:
    #             xvals = xvals[: plt_kwargs["maximum_shown_items"]]
    #             yvals = yvals[: plt_kwargs["maximum_shown_items"]]
    #             labels = labels[: plt_kwargs["maximum_shown_items"]]
    #             colors = colors[: plt_kwargs["maximum_shown_items"]]
    #             legend_text = legend_text[: plt_kwargs["maximum_shown_items"]]
    #             markers = markers[: plt_kwargs["maximum_shown_items"]]
    #
    #     colors = self._get_color_list(colors, **plt_kwargs)
    #     for i in range(len(legend_text)):
    #         legend_text[i][0] = colors[i]
    #
    #     plot_obj.clear()
    #     plot_obj.plot_1D_barplot(
    #         xvals,
    #         yvals,
    #         labels,
    #         colors,
    #         axesSize=CONFIG._plotSettings["UniDec (Barplot)"]["axes_size"],
    #         title="Peak Intensities",
    #         ylabel="Intensity",
    #         plotType="Barchart",
    #         **plt_kwargs,
    #     )
    #
    #     if unidec_eng_data is None and replot is not None:
    #         if kwargs["show_markers"]:
    #             for i in range(len(markers)):
    #                 if i >= plt_kwargs["maximum_shown_items"]:
    #                     continue
    #                 plot_obj.plot_add_markers(
    #                     xvals[i], yvals[i], color=colors[i], marker=markers[i], size=plt_kwargs["bar_marker_size"]
    #                 )
    #
    #     # Add legend
    #     plot_obj.plot_1D_add_legend(legend_text, **plt_kwargs)
    #     plot_obj.repaint()
    #
    # def plot_1D_update(self, plotName="all"):
    #
    #     plt_kwargs = self._buildPlotParameters(plotType="1D")
    #
    #     if plotName in ["all", "MS"]:
    #         try:
    #             self.plot_ms.plot_1D_update(**plt_kwargs)
    #             self.plot_ms.repaint()
    #         except AttributeError:
    #             logger.warning("Failed to update `Mass spectrum` plot", exc_info=True)
    #
    #     if plotName in ["all", "RT"]:
    #         try:
    #             self.plot_rt_rt.plot_1D_update(**plt_kwargs)
    #             self.plot_rt_rt.repaint()
    #         except AttributeError:
    #             logger.warning("Failed to update `Chromatogram` plot", exc_info=True)
    #
    #     if plotName in ["all", "1D"]:
    #         try:
    #             self.plot_dt_dt.plot_1D_update(**plt_kwargs)
    #             self.plot_dt_dt.repaint()
    #         except AttributeError:
    #             logger.warning("Failed to update `Mobilogram` plot", exc_info=True)
    #
    #     if plotName in ["all", "RMSF"]:
    #         plt_kwargs = self._buildPlotParameters(["1D", "2D", "RMSF"])
    #
    #         plot_obj = self.get_plot_from_name("RMSF")
    #         try:
    #             plot_obj.plot_1D_update_rmsf(**plt_kwargs)
    #             plot_obj.repaint()
    #         except AttributeError:
    #             logger.warning("Failed to update `RMSF` plot", exc_info=True)
    #
    # #         if plotName in ["all", "1D", "MS", "RT", "RMSF"]:
    # #             plot_obj = self.get_plot_from_name(plotName)
    # #             plot_obj.plot_1D_update(**plt_kwargs)
    # #             plot_obj.repaint()
    #
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
    # def _on_check_plot_names(self, document_name, dataset_name, plot_window):
    #     """
    #     Check if document name and dataset name match that of the plotted window
    #     """
    #     plot = None
    #     if plot_window == "MS":
    #         plot = self.plot_ms
    #
    #     if plot is None:
    #         return False
    #
    #     if plot.document_name is None or plot.dataset_name is None:
    #         return
    #
    #     if plot.document_name != document_name:
    #         return False
    #
    #     if plot.dataset_name != dataset_name:
    #         return False
    #
    #     return True
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
    #
    # def on_clear_MS_annotations(self):
    #
    #     try:
    #         self.on_clear_labels(plot="MS")
    #     except Exception:
    #         pass
    #
    #     try:
    #         self.on_clear_patches(plot="MS")
    #     except Exception:
    #         pass
    #
    # def on_simple_plot_1D(self, xvals, yvals, **kwargs):
    #     plot = kwargs.pop("plot", None)
    #
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #
    #     # get kwargs
    #     plt_kwargs = self._buildPlotParameters(plotType="1D")
    #
    #     try:
    #         plot_obj.plot_1D_update_data_only(xvals, yvals)
    #     except Exception as err:
    #         print(err)
    #
    #         plot_obj.clear()
    #         plot_obj.plot_1D(
    #             xvals=xvals,
    #             yvals=yvals,
    #             xlabel=kwargs.pop("xlabel", ""),
    #             ylabel=kwargs.pop("ylabel", ""),
    #             plotType="1D",
    #             **plt_kwargs,
    #         )
    #     # show the plot
    #     plot_obj.repaint()
    #
    # def on_plot_1D_annotations(self, annotations_obj, plot="MS", **kwargs):
    #     from origami.utils.labels import _replace_labels
    #
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #
    #     label_kwargs = self._buildPlotParameters(plotType="label")
    #     arrow_kwargs = self._buildPlotParameters(plotType="arrow")
    #     vline = False
    #     _ymax = []
    #
    #     if len(annotations_obj) > 1:
    #         plot_obj.plot_remove_text_and_lines()
    #         plot_obj.plot_remove_patches()
    #         plot_obj.plot_remove_arrows()
    #
    #     label_fmt = kwargs.pop("label_fmt", "all")
    #     pin_to_intensity = kwargs.pop("pin_to_intensity", True)
    #     document_title = kwargs.pop("document_title")
    #     dataset_type = kwargs.pop("dataset_type")
    #     dataset_name = kwargs.pop("dataset_name")
    #     show_names = kwargs.pop("show_names", None)
    #
    #     for name, annotation_obj in annotations_obj.items():
    #         if show_names is not None and name not in show_names:
    #             continue
    #
    #         if label_fmt == "charge":
    #             show_label = f"z={annotation_obj.charge:d}"
    #         elif label_fmt == "label":
    #             show_label = _replace_labels(annotation_obj.label)
    #         elif label_fmt == "patch":
    #             show_label = ""
    #         else:
    #             show_label = "{:.2f}, {}\nz={}".format(
    #                 annotation_obj.position_x, annotation_obj.position_y, annotation_obj.charge
    #             )
    #
    #         # add  custom name tag
    #         obj_name_tag = f"{document_title}|-|{dataset_type}|-|{dataset_name}|-|{name}|-|annotation"
    #         label_kwargs["text_name"] = obj_name_tag
    #
    #         # add patch
    #         if annotation_obj.patch_show:
    #             plot_obj.plot_add_patch(
    #                 annotation_obj.patch_position[0],
    #                 annotation_obj.patch_position[1],
    #                 annotation_obj.width,
    #                 annotation_obj.height,
    #                 color=annotation_obj.patch_color,
    #                 alpha=CONFIG.annotation_patch_transparency,
    #                 label=obj_name_tag,
    #             )
    #         else:
    #             plot_obj._remove_existing_patch(obj_name_tag)
    #
    #         _ymax.append(annotation_obj.label_position_y)
    #         if show_label != "" and annotation_obj.arrow_show and pin_to_intensity:
    #             # arrows have 4 positional parameters:
    #             #    xpos, ypos = correspond to the label position
    #             #    dx, dy = difference between label position and peak position
    #             arrow_list, arrow_x_end, arrow_y_end = annotation_obj.get_arrow_position()
    #
    #             arrow_kwargs["text_name"] = obj_name_tag
    #             arrow_kwargs["props"] = [arrow_x_end, arrow_y_end]
    #             plot_obj.plot_add_arrow(arrow_list, stick_to_intensity=pin_to_intensity, **arrow_kwargs)
    #         else:
    #             plot_obj._remove_existing_arrow(obj_name_tag)
    #
    #         # add label to the plot
    #         if show_label != "":
    #             plot_obj.plot_add_text_and_lines(
    #                 xpos=annotation_obj.label_position_x,
    #                 yval=annotation_obj.label_position_y,
    #                 label=show_label,
    #                 vline=vline,
    #                 vline_position=annotation_obj.position_x,
    #                 stick_to_intensity=pin_to_intensity,
    #                 yoffset=CONFIG.annotation_label_y_offset,
    #                 color=annotation_obj.label_color,
    #                 **label_kwargs,
    #             )
    #
    #     if CONFIG.annotation_zoom_y:
    #         try:
    #             plot_obj.on_zoom_y_axis(endY=np.amax(_ymax) * CONFIG.annotation_zoom_y_multiplier)
    #         except TypeError:
    #             logger.warning("Failed to zoom in on plot/annotation", exc_info=True)
    #
    #     plot_obj.repaint()

    #
    # def plot_2D_update(self, plotName="all", evt=None):
    #     plt_kwargs = self._buildPlotParameters(plotType="2D")
    #
    #     if plotName in ["all", "2D"]:
    #         try:
    #             self.plot_heatmap.plot_2D_update(**plt_kwargs)
    #             self.plot_heatmap.repaint()
    #         except AttributeError:
    #             logging.warning("Failed to update plot", exc_info=True)
    #
    #     if plotName in ["all", "UniDec"]:
    #
    #         try:
    #             self.plotUnidec_mzGrid.plot_2D_update(**plt_kwargs)
    #             self.plotUnidec_mzGrid.repaint()
    #         except AttributeError:
    #             logging.warning("Failed to update plot", exc_info=True)
    #
    #         try:
    #             self.plotUnidec_mwVsZ.plot_2D_update(**plt_kwargs)
    #             self.plotUnidec_mwVsZ.repaint()
    #         except AttributeError:
    #             pass
    #
    #     if plotName in ["all", "DT/MS"]:
    #         try:
    #             self.plot_msdt.plot_2D_update(**plt_kwargs)
    #             self.plot_msdt.repaint()
    #         except AttributeError:
    #             logging.warning("Failed to update plot", exc_info=True)
    #
    #     if plotName in ["other"]:
    #         plot_obj = self.get_plot_from_name(plotName)
    #         try:
    #             plot_obj.plot_2D_update(**plt_kwargs)
    #             plot_obj.repaint()
    #         except AttributeError:
    #             logging.warning("Failed to update plot", exc_info=True)
    #
    # def on_plot_2D_data(self, data=None, **kwargs):
    #     """
    #     This function plots IMMS data in relevant windows.
    #     Input format: zvals, xvals, xlabel, yvals, ylabel
    #     """
    #     if isempty(data[0]):
    #         raise MessageError("Missing data", "Missing data - cannot plot 2D plot")
    #
    #     # Unpack data
    #     if len(data) == 5:
    #         zvals, xvals, xlabel, yvals, ylabel = data
    #     elif len(data) == 6:
    #         zvals, xvals, xlabel, yvals, ylabel, __ = data
    #
    #     # Check and change colormap if necessary
    #     cmapNorm = self.normalize_colormap(
    #         zvals, min=CONFIG.minCmap, mid=CONFIG.midCmap, max=CONFIG.maxCmap
    #     )
    #
    #     # Plot data
    #     self.on_plot_2d(zvals, xvals, yvals, xlabel, ylabel, cmapNorm=cmapNorm, **kwargs)
    #
    # def on_plot_violin(self, data=None, set_page=False, plot="Waterfall", **kwargs):
    #
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #         if set_page:
    #             self.set_page(CONFIG.panelNames["Waterfall"])
    #
    #     # Unpack data
    #     if len(data) == 5:
    #         zvals, xvals, xlabel, yvals, ylabel = data
    #     elif len(data) == 6:
    #         zvals, xvals, xlabel, yvals, ylabel, __ = data
    #
    #     plt_kwargs = self._buildPlotParameters(["1D", "violin"])
    #     if "waterfall_increment" in kwargs:
    #         plt_kwargs["waterfall_increment"] = kwargs["waterfall_increment"]
    #
    #     n_scans = zvals.shape[1]
    #
    #     plot_obj.clear()
    #     try:
    #         if n_scans < plt_kwargs["violin_n_limit"]:
    #             plot_obj.plot_1D_violin(
    #                 xvals=yvals,
    #                 yvals=xvals,
    #                 zvals=zvals,
    #                 label="",
    #                 xlabel=xlabel,
    #                 ylabel=ylabel,
    #                 labels=kwargs.get("labels", []),
    #                 axesSize=CONFIG._plotSettings["Violin"]["axes_size"],
    #                 orientation=CONFIG.violin_orientation,
    #                 plotName="1D",
    #                 **plt_kwargs,
    #             )
    #         else:
    #             logger.warning("Seleted item is too large to plot as violin. Will try to plot as waterfall instead")
    #             if n_scans > 500:
    #                 msg = (
    #                     f"There are {n_scans} scans in this dataset"
    #                     + "(this could be slow...). Would you like to continue?"
    #                 )
    #                 dlg = DialogBox(title="Would you like to continue?", msg=msg, kind="Question")
    #                 if dlg == wx.ID_NO:
    #                     return
    #             # plot
    #             self.on_plot_waterfall(yvals=xvals, xvals=yvals, zvals=zvals, xlabel=xlabel, ylabel=ylabel)
    #     except Exception:
    #         plot_obj.clear()
    #         logger.warning("Failed to plot violin plot...")
    #
    #     # Show the mass spectrum
    #     plot_obj.repaint()
    #
    # def on_plot_image(self, zvals, xvals, yvals, plot="2D", set_page=False, **kwargs):
    #     def set_data():
    #         CONFIG.replotData["image"] = {
    #             "zvals": zvals,
    #             "xvals": xvals,
    #             "yvals": yvals,
    #             "cmap": plt_kwargs["heatmap_colormap"],
    #             "cmapNorm": cmapNorm,
    #         }
    #
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #         if set_page:
    #             self.set_page(CONFIG.panelNames[plot])
    #
    #     # Check that cmap modifier is included
    #     cmapNorm = self.normalize_colormap(
    #         zvals, min=CONFIG.minCmap, mid=CONFIG.midCmap, max=CONFIG.maxCmap
    #     )
    #
    #     # Build kwargs
    #     plt_kwargs = self._buildPlotParameters(plotType="2D")
    #
    #     # Check if cmap should be overwritten
    #     if CONFIG.useCurrentCmap or kwargs.get("cmap", None) is None:
    #         plt_kwargs["heatmap_colormap"] = CONFIG.currentCmap
    #     plt_kwargs["colormap_norm"] = kwargs.get("cmapNorm", None)
    #     plt_kwargs["allow_extraction"] = kwargs.pop("allow_extraction", True)
    #
    #     if not kwargs.get("full_repaint", False):
    #         try:
    #             plot_obj.plot_2D_image_update_data(xvals, yvals, zvals, "", "", **plt_kwargs)
    #             plot_obj.repaint()
    #             return
    #         except Exception:
    #             logger.info("Failed to quickly plot heatmap", exc_info=False)
    #
    #     # Plot 2D dataset
    #     plot_obj.clear()
    #     plot_obj.plot_2D_image(
    #         zvals,
    #         xvals,
    #         yvals,
    #         axesSize=CONFIG._plotSettings["2D"]["axes_size"],
    #         plotName="2D",
    #         callbacks=kwargs.get("callbacks", dict()),
    #         **plt_kwargs,
    #     )
    #     plot_obj.repaint()
    #
    # def on_plot_2d(
    #     self,
    #     zvals=None,
    #     xvals=None,
    #     yvals=None,
    #     xlabel=None,
    #     ylabel=None,
    #     plotType=None,
    #     override=True,
    #     replot=False,
    #     cmapNorm=None,
    #     set_page=False,
    #     plot="2D",
    #     obj=None,
    #     **kwargs,
    # ):
    #     def set_data():
    #         CONFIG.replotData["2D"] = {
    #             "zvals": zvals,
    #             "xvals": xvals,
    #             "yvals": yvals,
    #             "xlabels": xlabel,
    #             "ylabels": ylabel,
    #             "cmap": plt_kwargs["heatmap_colormap"],
    #             "cmapNorm": cmapNorm,
    #         }
    #
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #         if set_page:
    #             self.set_page(CONFIG.panelNames["2D"])
    #
    #     plt_kwargs = self._buildPlotParameters(plotType="2D")
    #
    #     if plot_obj == self.plot_heatmap:
    #         self.view_heatmap.plot(xvals, yvals, zvals, obj=obj, **plt_kwargs)
    #         return
    #
    #     # If the user would like to replot data, you can directly unpack it
    #     if replot:
    #         zvals, xvals, yvals, xlabel, ylabel = self.get_replot_data("2D")
    #         if zvals is None or xvals is None or yvals is None:
    #             logger.warning("Could not replot data as data was missing...")
    #             return
    #
    #     # Check that cmap modifier is included
    #     if cmapNorm is None and plotType != "RMSD":
    #         cmapNorm = self.normalize_colormap(
    #             zvals, min=CONFIG.minCmap, mid=CONFIG.midCmap, max=CONFIG.maxCmap
    #         )
    #     elif cmapNorm is None and plotType == "RMSD":
    #         cmapNorm = self.normalize_colormap(zvals, min=-100, mid=0, max=100)
    #
    #     # Check if cmap should be overwritten
    #     if CONFIG.useCurrentCmap or kwargs.get("cmap", None) is None:
    #         plt_kwargs["heatmap_colormap"] = CONFIG.currentCmap
    #     plt_kwargs["colormap_norm"] = kwargs.get("cmapNorm", None)
    #     plt_kwargs["allow_extraction"] = kwargs.pop("allow_extraction", True)
    #
    #     if not kwargs.get("full_repaint", False):
    #         try:
    #             plot_obj.plot_2D_update_data(xvals, yvals, xlabel, ylabel, zvals, **plt_kwargs)
    #             plot_obj.repaint()
    #             if override:
    #                 set_data()
    #             return
    #         except Exception:
    #             logger.info("Failed to quickly plot heatmap", exc_info=False)
    #
    #     # Plot 2D dataset
    #     plot_obj.clear()
    #     if CONFIG.plotType == "Image":
    #         plot_obj.plot_2D_surface(
    #             zvals,
    #             xvals,
    #             yvals,
    #             xlabel,
    #             ylabel,
    #             axesSize=CONFIG._plotSettings["2D"]["axes_size"],
    #             plotName="2D",
    #             **plt_kwargs,
    #         )
    #
    #     elif CONFIG.plotType == "Contour":
    #         plot_obj.plot_2D_contour(
    #             zvals,
    #             xvals,
    #             yvals,
    #             xlabel,
    #             ylabel,
    #             axesSize=CONFIG._plotSettings["2D"]["axes_size"],
    #             plotName="2D",
    #             **plt_kwargs,
    #         )
    #
    #     plot_obj.repaint()
    #     if override:
    #         set_data()
    #
    #     # update plot data
    #     # self.presenter.view._onUpdatePlotData(plot_type="2D")
    #
    # def on_plot_dtms(
    #     self,
    #     zvals=None,
    #     xvals=None,
    #     yvals=None,
    #     xlabel=None,
    #     ylabel=None,
    #     cmap=None,
    #     cmapNorm=None,
    #     override=True,
    #     replot=False,
    #     set_page=False,
    #     obj=None,
    #     **kwargs,
    # ):
    #
    #     # change page
    #     if set_page:
    #         self.set_page(CONFIG.panelNames["MZDT"])
    #
    #     #         # If the user would like to replot data, you can directly unpack it
    #     #         if replot:
    #     #             zvals, xvals, yvals, xlabel, ylabel = self.get_replot_data("DT/MS")
    #     #             if zvals is None or xvals is None or yvals is None:
    #     #                 return
    #     #
    #     #         # Check if cmap should be overwritten
    #     #         if CONFIG.useCurrentCmap or cmap is None:
    #     #             cmap = CONFIG.currentCmap
    #     #
    #     #         # Check that cmap modifier is included
    #     #         if cmapNorm is None:
    #     #             cmapNorm = self.normalize_colormap(
    #     #                 zvals, min=CONFIG.minCmap, mid=CONFIG.midCmap, max=CONFIG.maxCmap
    #     #             )
    #
    #     # Build kwargs
    #     plt_kwargs = self._buildPlotParameters(plotType="2D")
    #     #         plt_kwargs["heatmap_colormap"] = cmap
    #     #         plt_kwargs["colormap_norm"] = cmapNorm
    #     #         plt_kwargs["allow_extraction"] = kwargs.pop("allow_extraction", True)
    #     #         plt_kwargs = merge_two_dicts(plt_kwargs, kwargs)
    #
    #     self.view_msdt.plot(xvals, yvals, zvals, obj=obj, **plt_kwargs)
    #     return

    #         try:
    #             self.plot_msdt.plot_2D_update_data(xvals, yvals, xlabel, ylabel, zvals, **plt_kwargs)
    #             self.plot_msdt.repaint()
    #             if override:
    #                 CONFIG.replotData["DT/MS"] = {
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
    #         if CONFIG.plotType == "Image":
    #             self.plot_msdt.plot_2D_surface(
    #                 zvals,
    #                 xvals,
    #                 yvals,
    #                 xlabel,
    #                 ylabel,
    #                 axesSize=CONFIG._plotSettings["DT/MS"]["axes_size"],
    #                 plotName="MSDT",
    #                 **plt_kwargs,
    #             )
    #
    #         elif CONFIG.plotType == "Contour":
    #             self.plot_msdt.plot_2D_contour(
    #                 zvals,
    #                 xvals,
    #                 yvals,
    #                 xlabel,
    #                 ylabel,
    #                 axesSize=CONFIG._plotSettings["DT/MS"]["axes_size"],
    #                 plotName="MSDT",
    #                 **plt_kwargs,
    #             )
    #
    #         # Show the mass spectrum
    #         self.plot_msdt.repaint()
    #
    #         # since we always sub-sample this dataset, it is makes sense to keep track of the full dataset before
    #         it was
    #         # subsampled - this way, when we replot data it will always use the full information
    #         if kwargs.get("full_data", False):
    #             xvals = kwargs["full_data"].pop("xvals", xvals)
    #             zvals = kwargs["full_data"].pop("zvals", zvals)
    #
    #         if override:
    #             CONFIG.replotData["DT/MS"] = {
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
    #
    # def on_plot_3D(
    #     self,
    #     zvals=None,
    #     labelsX=None,
    #     labelsY=None,
    #     xlabel="",
    #     ylabel="",
    #     zlabel="Intensity",
    #     cmap="inferno",
    #     cmapNorm=None,
    #     replot=False,
    #     set_page=False,
    # ):
    #
    #     # change page
    #     if set_page:
    #         self.set_page(CONFIG.panelNames["3D"])
    #
    #     plt_kwargs = self._buildPlotParameters(["1D", "3D"])
    #
    #     # If the user would like to replot data, you can directly unpack it
    #     if replot:
    #         zvals, labelsX, labelsY, xlabel, ylabel = self.get_replot_data("2D")
    #         if zvals is None or labelsX is None or labelsY is None:
    #             return
    #     # Check if cmap should be overwritten
    #     if CONFIG.useCurrentCmap:
    #         cmap = CONFIG.currentCmap
    #
    #     # Check that cmap modifier is included
    #     if cmapNorm is None:
    #         cmapNorm = self.normalize_colormap(
    #             zvals, min=CONFIG.minCmap, mid=CONFIG.midCmap, max=CONFIG.maxCmap
    #         )
    #     # add to kwargs
    #     plt_kwargs["heatmap_colormap"] = cmap
    #     plt_kwargs["colormap_norm"] = cmapNorm
    #
    #     self.plot_heatmap_3d.clear()
    #     if CONFIG.plotType_3D == "Surface":
    #         self.plot_heatmap_3d.plot_3D_surface(
    #             xvals=labelsX,
    #             yvals=labelsY,
    #             zvals=zvals,
    #             title="",
    #             xlabel=xlabel,
    #             ylabel=ylabel,
    #             zlabel=zlabel,
    #             axesSize=CONFIG._plotSettings["3D"]["axes_size"],
    #             **plt_kwargs,
    #         )
    #     elif CONFIG.plotType_3D == "Wireframe":
    #         self.plot_heatmap_3d.plot_3D_wireframe(
    #             xvals=labelsX,
    #             yvals=labelsY,
    #             zvals=zvals,
    #             title="",
    #             xlabel=xlabel,
    #             ylabel=ylabel,
    #             zlabel=zlabel,
    #             axesSize=CONFIG._plotSettings["3D"]["axes_size"],
    #             **plt_kwargs,
    #         )
    #     # Show the mass spectrum
    #     self.plot_heatmap_3d.repaint()
    #
    # def on_plot_waterfall(
    #     self, xvals, yvals, zvals, xlabel, ylabel, colors=[], set_page=False, plot="Waterfall", **kwargs
    # ):
    #
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #         if set_page:
    #             self.set_page(CONFIG.panelNames["Waterfall"])
    #
    #     plt_kwargs = self._buildPlotParameters(["1D", "waterfall"])
    #     if "waterfall_increment" in kwargs:
    #         plt_kwargs["waterfall_increment"] = kwargs["waterfall_increment"]
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
    #         axesSize=CONFIG._plotSettings["Waterfall"]["axes_size"],
    #         plotName="1D",
    #         **plt_kwargs,
    #     )
    #
    #     if "add_legend" in kwargs and "labels" in kwargs and len(colors) == len(kwargs["labels"]):
    #         if kwargs["add_legend"]:
    #             legend_text = list(zip(colors, kwargs["labels"]))
    #             plot_obj.plot_1D_add_legend(legend_text, **plt_kwargs)
    #     plot_obj.repaint()
    #
    # def plot_1D_waterfall_update(self, which="other", **kwargs):
    #
    #     plt_kwargs = self._buildPlotParameters(plotType="1D")
    #
    #     if self.currentPage == "Other":
    #         plot_name = self.plot_annotated
    #     else:
    #         plot_name = self.plot_overlay
    #
    #     if self.plot_overlay.plot_name != "Violin":
    #         extra_kwargs = self._buildPlotParameters(plotType="waterfall")
    #     else:
    #         extra_kwargs = self._buildPlotParameters(plotType="violin")
    #         if which in ["data", "label"]:
    #             return
    #     plt_kwargs = merge_two_dicts(plt_kwargs, extra_kwargs)
    #
    #     plot_name.plot_1D_waterfall_update(which=which, **plt_kwargs)
    #     plot_name.repaint()
    #
    # def on_plot_waterfall_overlay(
    #     self, xvals, yvals, zvals, colors, xlabel, ylabel, labels=None, set_page=False, plot="Waterfall", **kwargs
    # ):
    #
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #         if set_page:
    #             self.set_page(CONFIG.panelNames["Waterfall"])
    #
    #     plt_kwargs = self._buildPlotParameters(plotType="1D")
    #     waterfall_kwargs = self._buildPlotParameters(plotType="waterfall")
    #     plt_kwargs = merge_two_dicts(plt_kwargs, waterfall_kwargs)
    #     if "waterfall_increment" in kwargs:
    #         plt_kwargs["waterfall_increment"] = kwargs["waterfall_increment"]
    #
    #     plot_obj.clear()
    #     plot_obj.plot_1D_waterfall_overlay(
    #         xvals=xvals,
    #         yvals=yvals,
    #         zvals=zvals,
    #         label="",
    #         xlabel=xlabel,
    #         ylabel=ylabel,
    #         colorList=colors,
    #         labels=labels,
    #         axesSize=CONFIG._plotSettings["Waterfall"]["axes_size"],
    #         plotName="1D",
    #         **plt_kwargs,
    #     )
    #
    #     if "add_legend" in kwargs and "labels" in kwargs and len(colors) == len(kwargs["labels"]):
    #         if kwargs["add_legend"]:
    #             legend_text = list(zip(colors, kwargs["labels"]))
    #             plot_obj.plot_1D_add_legend(legend_text, **plt_kwargs)
    #
    #     plot_obj.repaint()
    #
    # def on_plot_overlay_RT(self, xvals, yvals, xlabel, colors, labels, xlimits, set_page=False, plot="RT", **kwargs):
    #
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #         if set_page:
    #             self.set_page(CONFIG.panelNames.get(plot, "RT"))
    #
    #     # Build kwargs
    #     plt_kwargs = self._buildPlotParameters(plotType="1D")
    #     plot_obj.clear()
    #     plot_obj.plot_1D_overlay(
    #         xvals=xvals,
    #         yvals=yvals,
    #         title="",
    #         xlabel=xlabel,
    #         ylabel="Intensity",
    #         labels=labels,
    #         colors=colors,
    #         xlimits=xlimits,
    #         zoom="box",
    #         axesSize=CONFIG._plotSettings["RT"]["axes_size"],
    #         plotName="1D",
    #         **plt_kwargs,
    #     )
    #     plot_obj.repaint()
    #
    # def on_plot_overlay_DT(self, xvals, yvals, xlabel, colors, labels, xlimits, set_page=False, plot="1D", **kwargs):
    #
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #         if set_page:
    #             self.set_page(CONFIG.panelNames.get(plot, "1D"))
    #
    #     # Build kwargs
    #     plt_kwargs = self._buildPlotParameters(plotType="1D")
    #
    #     plot_obj.clear()
    #     plot_obj.plot_1D_overlay(
    #         xvals=xvals,
    #         yvals=yvals,
    #         title="",
    #         xlabel=xlabel,
    #         ylabel="Intensity",
    #         labels=labels,
    #         colors=colors,
    #         xlimits=xlimits,
    #         zoom="box",
    #         axesSize=CONFIG._plotSettings["DT"]["axes_size"],
    #         plotName="1D",
    #         **plt_kwargs,
    #     )
    #     plot_obj.repaint()
    #
    # def on_plot_overlay_2D(
    #     self,
    #     zvalsIon1,
    #     zvalsIon2,
    #     cmapIon1,
    #     cmapIon2,
    #     alphaIon1,
    #     alphaIon2,
    #     xvals,
    #     yvals,
    #     xlabel,
    #     ylabel,
    #     plotName="2D",
    #     set_page=False,
    #     plot="Overlay",
    #     **kwargs,
    # ):
    #     """
    #     Plot an overlay of *2* ions
    #     """
    #
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #         if set_page:
    #             self.set_page(CONFIG.panelNames["Overlay"])
    #
    #     plt_kwargs = self._buildPlotParameters(plotType="2D")
    #     plot_obj.clear()
    #     plot_obj.plot_2D_overlay(
    #         zvalsIon1=zvalsIon1,
    #         zvalsIon2=zvalsIon2,
    #         cmapIon1=cmapIon1,
    #         cmapIon2=cmapIon2,
    #         alphaIon1=alphaIon1,
    #         alphaIon2=alphaIon2,
    #         labelsX=xvals,
    #         labelsY=yvals,
    #         xlabel=xlabel,
    #         ylabel=ylabel,
    #         axesSize=CONFIG._plotSettings["Overlay"]["axes_size"],
    #         plotName=plotName,
    #         **plt_kwargs,
    #     )
    #     plot_obj.repaint()
    #
    # def on_plot_rgb(
    #     self,
    #     zvals=None,
    #     xvals=None,
    #     yvals=None,
    #     xlabel=None,
    #     ylabel=None,
    #     legend_text=None,
    #     set_page=False,
    #     plot="2D",
    #     **kwargs,
    # ):
    #
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #         if set_page:
    #             self.set_page(CONFIG.panelNames.get(plot, "2D"))
    #
    #     plt_kwargs = self._buildPlotParameters(plotType="2D")
    #
    #     plot_obj.clear()
    #     plot_obj.plot_2D_rgb(
    #         zvals,
    #         xvals,
    #         yvals,
    #         xlabel,
    #         ylabel,
    #         axesSize=CONFIG._plotSettings["2D"]["axes_size"],
    #         legend_text=legend_text,
    #         **plt_kwargs,
    #     )
    #     plot_obj.repaint()
    #
    # def on_plot_RMSDF(
    #     self,
    #     yvalsRMSF,
    #     zvals,
    #     xvals=None,
    #     yvals=None,
    #     xlabelRMSD=None,
    #     ylabelRMSD=None,
    #     ylabelRMSF=None,
    #     color="blue",
    #     cmapNorm=None,
    #     cmap="inferno",
    #     plotType=None,
    #     override=True,
    #     replot=False,
    #     set_page=False,
    #     plot="RMSF",
    #     **kwargs,
    # ):
    #     """
    #     Plot RMSD and RMSF plots together in panel RMSD
    #     """
    #
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #         if set_page:
    #             self.set_page(CONFIG.panelNames["RMSF"])
    #
    #     plt_kwargs = self._buildPlotParameters(["2D", "RMSF"])
    #
    #     # If the user would like to replot data, you can directly unpack it
    #     if replot:
    #         zvals, xvals, yvals, xlabelRMSD, ylabelRMSD, ylabelRMSF = self.get_replot_data("RMSF")
    #         if zvals is None or xvals is None or yvals is None:
    #             return
    #
    #     # Update values
    #     # self.presenter.getXYlimits2D(xvals, yvals, zvals)
    #
    #     if CONFIG.useCurrentCmap:
    #         cmap = CONFIG.currentCmap
    #
    #     if cmapNorm is None and plotType == "RMSD":
    #         cmapNorm = self.normalize_colormap(zvals, min=-100, mid=0, max=100)
    #
    #     # update kwargs
    #     plt_kwargs["heatmap_colormap"] = cmap
    #     plt_kwargs["colormap_norm"] = cmapNorm
    #
    #     plot_obj.clear()
    #     plot_obj.plot_1D_2D(
    #         yvalsRMSF=yvalsRMSF,
    #         zvals=zvals,
    #         labelsX=xvals,
    #         labelsY=yvals,
    #         xlabelRMSD=xlabelRMSD,
    #         ylabelRMSD=ylabelRMSD,
    #         ylabelRMSF=ylabelRMSF,
    #         label="",
    #         zoom="box",
    #         plotName="RMSF",
    #         **plt_kwargs,
    #     )
    #     plot_obj.repaint()
    #     self.rmsdfFlag = False
    #
    #     # if override:
    #     #     CONFIG.replotData["RMSF"] = {
    #     #         "zvals": zvals,
    #     #         "xvals": xvals,
    #     #         "yvals": yvals,
    #     #         "xlabelRMSD": xlabelRMSD,
    #     #         "ylabelRMSD": ylabelRMSD,
    #     #         "ylabelRMSF": ylabelRMSF,
    #     #         "cmapNorm": cmapNorm,
    #     #     }
    #
    #     # self.presenter.view._onUpdatePlotData(plot_type="RMSF")
    #
    #     # setup plot object
    #     self.plot_objs["RMSF"] = plot_obj
    #
    # def on_plot_RMSD(
    #     self,
    #     zvals=None,
    #     xvals=None,
    #     yvals=None,
    #     xlabel=None,
    #     ylabel=None,
    #     cmap=None,
    #     cmapNorm=None,
    #     plotType=None,
    #     override=True,
    #     replot=False,
    #     set_page=False,
    #     plot="RMSF",
    #     **kwargs,
    # ):
    #
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #         if set_page:
    #             self.set_page(CONFIG.panelNames["RMSF"])
    #
    #     plot_obj.clear()
    #
    #     # If the user would like to replot data, you can directly unpack it
    #     if replot:
    #         zvals, xvals, yvals, xlabel, ylabel = self.get_replot_data("2D")
    #         if zvals is None or xvals is None or yvals is None:
    #             return
    #
    #     # Update values
    #     # self.presenter.getXYlimits2D(xvals, yvals, zvals)
    #
    #     # Check if cmap should be overwritten
    #     if CONFIG.useCurrentCmap:
    #         cmap = CONFIG.currentCmap
    #
    #     # Check that cmap modifier is included
    #     if cmapNorm is None and plotType == "RMSD":
    #         cmapNorm = self.normalize_colormap(zvals, min=-100, mid=0, max=100)
    #
    #     # Build kwargs
    #     plt_kwargs = self._buildPlotParameters(plotType="2D")
    #     plt_kwargs["heatmap_colormap"] = cmap
    #     plt_kwargs["colormap_norm"] = cmapNorm
    #
    #     # Plot 2D dataset
    #     if CONFIG.plotType == "Image":
    #         plot_obj.plot_2D_surface(
    #             zvals,
    #             xvals,
    #             yvals,
    #             xlabel,
    #             ylabel,
    #             axesSize=CONFIG._plotSettings["2D"]["axes_size"],
    #             plotName="RMSD",
    #             **plt_kwargs,
    #         )
    #     elif CONFIG.plotType == "Contour":
    #         plot_obj.plot_2D_contour(
    #             zvals,
    #             xvals,
    #             yvals,
    #             xlabel,
    #             ylabel,
    #             axesSize=CONFIG._plotSettings["2D"]["axes_size"],
    #             plotName="RMSD",
    #             **plt_kwargs,
    #         )
    #
    #     # Show the mass spectrum
    #     plot_obj.repaint()
    #
    #     # if override:
    #     #     CONFIG.replotData["2D"] = {
    #     #         "zvals": zvals,
    #     #         "xvals": xvals,
    #     #         "yvals": yvals,
    #     #         "xlabels": xlabel,
    #     #         "ylabels": ylabel,
    #     #         "cmap": cmap,
    #     #         "cmapNorm": cmapNorm,
    #     #     }
    #
    #     # update plot data
    #     # self.presenter.view._onUpdatePlotData(plot_type="2D")
    #
    # def on_plot_MS_DT_calibration(
    #     self,
    #     msX=None,
    #     msY=None,
    #     xlimits=None,
    #     dtX=None,
    #     dtY=None,
    #     xlabelDT="Drift time (bins)",
    #     plotType="both",
    #     set_page=False,
    #     view_range=[],
    #     **kwargs,
    # ):
    #
    #     # change page
    #     if set_page:
    #         self.set_page(CONFIG.panelNames["Calibration"])
    #
    #     # MS plot
    #     if plotType == "both" or plotType == "MS":
    #         self.topPlotMS.clear()
    #         # get kwargs
    #         plt_kwargs = self._buildPlotParameters(plotType="1D")
    #         self.topPlotMS.plot_1D(
    #             xvals=msX,
    #             yvals=msY,
    #             xlabel="m/z",
    #             ylabel="Intensity",
    #             xlimits=xlimits,
    #             axesSize=CONFIG._plotSettings["Calibration (MS)"]["axes_size"],
    #             plotType="1D",
    #             **plt_kwargs,
    #         )
    #         if len(view_range):
    #             self.on_zoom_1D_x_axis(startX=view_range[0], endX=view_range[1], repaint=False, plot="calibration_MS")
    #         # Show the mass spectrum
    #         self.topPlotMS.repaint()
    #
    #     if plotType == "both" or plotType == "1DT":
    #         ylabel = "Intensity"
    #         # 1DT plot
    #         self.bottomPlot1DT.clear()
    #         # get kwargs
    #         plt_kwargs = self._buildPlotParameters(plotType="1D")
    #         self.bottomPlot1DT.plot_1D(
    #             xvals=dtX,
    #             yvals=dtY,
    #             xlabel=xlabelDT,
    #             ylabel=ylabel,
    #             axesSize=CONFIG._plotSettings["Calibration (DT)"]["axes_size"],
    #             plotType="CalibrationDT",
    #             **plt_kwargs,
    #         )
    #         self.bottomPlot1DT.repaint()
    #
    # def on_plot_DT_calibration(
    #     self, dtX=None, dtY=None, color=None, xlabel="Drift time (bins)", set_page=False
    # ):  # onPlot1DTCalibration
    #
    #     # change page
    #     if set_page:
    #         self.set_page(CONFIG.panelNames["Calibration"])
    #
    #     # Check yaxis labels
    #     ylabel = "Intensity"
    #     # 1DT plot
    #     self.bottomPlot1DT.clear()
    #     # get kwargs
    #     plt_kwargs = self._buildPlotParameters(plotType="1D")
    #     self.bottomPlot1DT.plot_1D(
    #         xvals=dtX,
    #         yvals=dtY,
    #         xlabel=xlabel,
    #         ylabel=ylabel,
    #         axesSize=CONFIG._plotSettings["Calibration (DT)"]["axes_size"],
    #         plotType="1D",
    #         **plt_kwargs,
    #     )
    #     self.bottomPlot1DT.repaint()
    #
    # def plot_2d_update_label(self, plot_name="RMSD", **kwargs):
    #     from origami.utils.visuals import calculate_label_position
    #
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot_name)
    #
    #     try:
    #         if plot_obj.plot_name == "RMSD":
    #             __, xvals, yvals, __, __ = self.get_replot_data("2D")
    #         elif plot_obj.plot_name == "RMSF":
    #             __, xvals, yvals, __, __, __ = self.get_replot_data("RMSF")
    #         else:
    #             logger.error("Operation is not supported")
    #             return
    #
    #         plt_kwargs = self._buildPlotParameters(plotType="RMSF")
    #         label_x_pos, label_y_pos = calculate_label_position(xvals, yvals, CONFIG.rmsd_location)
    #         plt_kwargs["rmsd_label_coordinates"] = [label_x_pos, label_y_pos]
    #         plt_kwargs["rmsd_label_color"] = CONFIG.rmsd_color
    #
    #         plot_obj.plot_2d_update_label(**plt_kwargs)
    #         plot_obj.repaint()
    #     except (AttributeError, KeyError, ValueError):
    #         logger.error("Failed to update RMSD label", exc_info=True)
    #
    # def plot_2D_matrix_update_label(self):
    #     plt_kwargs = self._buildPlotParameters("RMSF")
    #
    #     plot_obj = self.get_plot_from_name("matrix")
    #     try:
    #         plot_obj.plot_2D_matrix_update_label(**plt_kwargs)
    #         plot_obj.repaint()
    #     except Exception:
    #         logger.error("Failed to update RMSD matrix", exc_info=True)

    # def on_plot_matrix(
    #     self,
    #     zvals=None,
    #     xylabels=None,
    #     cmap=None,
    #     override=True,
    #     replot=False,
    #     set_page=False,
    #     plot="Comparison",
    #     **kwargs,
    # ):
    #
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #         if set_page:
    #             self.set_page(CONFIG.panelNames["Comparison"])
    #
    #     # If the user would like to replot data, you can directly unpack it
    #     if replot:
    #         zvals, xylabels, cmap = self.get_replot_data("Matrix")
    #         if zvals is None or xylabels is None or cmap is None:
    #             return
    #
    #     # Check if cmap should be overwritten
    #     if CONFIG.useCurrentCmap:
    #         cmap = CONFIG.currentCmap
    #
    #     plt_kwargs = self._buildPlotParameters(["2D", "RMSF"])
    #     plt_kwargs["heatmap_colormap"] = cmap
    #
    #     plot_obj.clear()
    #     plot_obj.plot_2D_matrix(
    #         zvals=zvals,
    #         xylabels=xylabels,
    #         xNames=None,
    #         axesSize=CONFIG._plotSettings["Comparison"]["axes_size"],
    #         plotName="2D",
    #         **plt_kwargs,
    #     )
    #     plot_obj.repaint()
    #
    #     if override:
    #         CONFIG.replotData["Matrix"] = {"zvals": zvals, "xylabels": xylabels, "cmap": cmap}
    #
    # def on_plot_grid(
    #     self,
    #     zvals_1,
    #     zvals_2,
    #     zvals_cum,
    #     xvals,
    #     yvals,
    #     xlabel,
    #     ylabel,
    #     cmap_1,
    #     cmap_2,
    #     set_page=False,
    #     plot="Overlay",
    #     **kwargs,
    # ):
    #
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #         if set_page:
    #             self.set_page(CONFIG.panelNames["Overlay"])
    #
    #     plt_kwargs = self._buildPlotParameters(["2D", "RMSD"])
    #     plt_kwargs["colormap_1"] = cmap_1
    #     plt_kwargs["colormap_2"] = cmap_2
    #
    #     plt_kwargs["cmap_norm_1"] = self.normalize_colormap(
    #         zvals_1, min=CONFIG.minCmap, mid=CONFIG.midCmap, max=CONFIG.maxCmap
    #     )
    #     plt_kwargs["cmap_norm_2"] = self.normalize_colormap(
    #         zvals_2, min=CONFIG.minCmap, mid=CONFIG.midCmap, max=CONFIG.maxCmap
    #     )
    #     plt_kwargs["cmap_norm_cum"] = self.normalize_colormap(zvals_cum, min=-100, mid=0, max=100)
    #     plot_obj.clear()
    #     plot_obj.plot_grid_2D_overlay(
    #         zvals_1,
    #         zvals_2,
    #         zvals_cum,
    #         xvals,
    #         yvals,
    #         xlabel,
    #         ylabel,
    #         axesSize=CONFIG._plotSettings["Overlay (Grid)"]["axes_size"],
    #         **plt_kwargs,
    #     )
    #     plot_obj.repaint()
    #
    # def on_plot_n_grid(
    #     self, n_zvals, cmap_list, title_list, xvals, yvals, xlabel, ylabel, set_page=False, plot="Overlay", **kwargs
    # ):
    #
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #         if set_page:
    #             self.set_page(CONFIG.panelNames["Overlay"])
    #
    #     plt_kwargs = self._buildPlotParameters(plotType="2D")
    #     plot_obj.clear()
    #     plot_obj.plot_n_grid_2D_overlay(
    #         n_zvals,
    #         cmap_list,
    #         title_list,
    #         xvals,
    #         yvals,
    #         xlabel,
    #         ylabel,
    #         axesSize=CONFIG._plotSettings["Overlay (Grid)"]["axes_size"],
    #         **plt_kwargs,
    #     )
    #     plot_obj.repaint()
    #
    # def plot_compare_spectra(
    #     self,
    #     xvals_1,
    #     xvals_2,
    #     yvals_1,
    #     yvals_2,
    #     xlimits=None,
    #     xlabel="m/z",
    #     ylabel="Intensity",
    #     legend=None,
    #     plot="MS",
    #     **kwargs,
    # ):
    #
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.pop("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #
    #     # Build kwargs
    #     plt_kwargs = self._buildPlotParameters(plotType="1D")
    #     plt_kwargs = merge_two_dicts(plt_kwargs, kwargs)
    #
    #     if legend is None:
    #         legend = CONFIG.compare_massSpectrumParams["legend"]
    #
    #     # setup labels
    #     plt_kwargs["label_1"] = legend[0]
    #     plt_kwargs["label_2"] = legend[1]
    #
    #     try:
    #         plot_obj.plot_1D_compare_update_data(xvals_1, xvals_2, yvals_1, yvals_2, **plt_kwargs)
    #     except (AttributeError, ValueError):
    #         plot_obj.clear()
    #         plot_obj.plot_1D_compare(
    #             xvals1=xvals_1,
    #             xvals2=xvals_2,
    #             yvals1=yvals_1,
    #             yvals2=yvals_2,
    #             xlimits=xlimits,
    #             title="",
    #             xlabel=xlabel,
    #             ylabel=ylabel,
    #             label=legend,
    #             lineWidth=CONFIG.lineWidth_1D,
    #             plotType="compare_MS",
    #             **plt_kwargs,
    #         )
    #         # Show the mass spectrum
    #     plot_obj.repaint()
    #
    # def plot_1D_update_data_by_label(self, xvals, yvals, gid, label, plot, **kwargs):
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #
    #     plot_obj.plot_1D_update_data_by_label(xvals, yvals, gid, label)
    #     plot_obj.repaint()
    #
    # def plot_1d_update_style_by_label(self, gid, plot, **kwargs):
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #
    #     plot_obj.plot_1d_update_style_by_label(gid, **kwargs)
    #     plot_obj.repaint()
    #
    # def plot_colorbar_update(self, plot_window="", **kwargs):
    #
    #     if plot_window is None and "plot_obj" in kwargs:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot_window)
    #
    #     # get parameters
    #     plt_kwargs = self._buildPlotParameters(plotType="2D")
    #
    #     # update plot
    #     plot_obj.plot_2d_colorbar_update(**plt_kwargs)
    #     plot_obj.repaint()
    #
    # def plot_normalization_update(self, plot_window="", **kwargs):
    #     if plot_window is None and "plot_obj" in kwargs:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot_window)
    #
    #     plt_kwargs = self._buildPlotParameters(plotType="2D")
    #
    #     plot_obj.plot_2D_update_normalization(**plt_kwargs)
    #     plot_obj.repaint()
    #
    # def on_add_legend(self, labels, colors, plot="RT", **kwargs):
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #
    #     plt_kwargs = self._buildPlotParameters(plotType="legend")
    #
    #     if len(colors) == len(labels):
    #         legend_text = list(zip(colors, labels))
    #
    #     plot_obj.plot_1D_add_legend(legend_text, **plt_kwargs)
    #
    # def on_clear_legend(self, plot, **kwargs):
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #
    #     plot_obj.plot_remove_legend()
    #
    # def on_add_marker(
    #     self,
    #     xvals=None,
    #     yvals=None,
    #     color="b",
    #     marker="o",
    #     size=5,
    #     plot="MS",
    #     repaint=True,
    #     clear_first=False,
    #     **kwargs,
    # ):
    #
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #
    #     if clear_first:
    #         plot_obj.plot_remove_markers()
    #
    #     plot_obj.plot_add_markers(
    #         xvals=xvals,
    #         yvals=yvals,
    #         color=color,
    #         marker=marker,
    #         size=size,
    #         test_yvals=kwargs.pop("test_yvals", False),
    #         **kwargs,
    #     )
    #
    #     if repaint:
    #         plot_obj.repaint()
    #
    # def on_add_patch(self, x, y, width, height, color="r", alpha=0.5, repaint=False, plot="MS", **kwargs):
    #
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #
    #     plot_obj.plot_add_patch(x, y, width, height, color=color, alpha=alpha)
    #     if repaint:
    #         plot_obj.repaint()
    #
    # def on_zoom_1D_x_axis(self, startX, endX, endY=None, set_page=False, plot="MS", repaint=True, **kwargs):
    #
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #
    #     if set_page:
    #         self.set_page(CONFIG.panelNames["MS"])
    #
    #     if endY is None:
    #         plot_obj.on_zoom_x_axis(startX, endX)
    #     else:
    #         plot_obj.on_zoom(startX, endX, endY)
    #
    #     if repaint:
    #         plot_obj.repaint()
    #
    # def on_zoom_1D_xy_axis(self, startX, endX, startY, endY, set_page=False, plot="MS", repaint=True):
    #
    #     if set_page:
    #         self.set_page(CONFIG.panelNames["MS"])
    #
    #     if plot == "MS":
    #         self.plot_ms.on_zoom_xy_axis(startX, endX, startY, endY)
    #
    #         if repaint:
    #             self.plot_ms.repaint()
    #
    # def on_add_label(self, x, y, text, rotation, color="k", plot="RMSD", **kwargs):
    #
    #     if "plot_obj" in kwargs and kwargs["plot_obj"] is not None:
    #         plot_obj = kwargs.get("plot_obj")
    #     else:
    #         plot_obj = self.get_plot_from_name(plot)
    #
    #     plot_obj.addText(
    #         x,
    #         y,
    #         text,
    #         rotation,
    #         color=CONFIG.rmsd_color,
    #         fontsize=CONFIG.rmsd_fontSize,
    #         weight=CONFIG.rmsd_fontWeight,
    #         plot=plot,
    #     )
    #     plot_obj.repaint()
    #
    # def _buildPlotParameters(self, plotType):
    #     return CONFIG.get_mpl_parameters(plotType)
    #
    # def normalize_colormap(self, data, min=0, mid=50, max=100, cbarLimits=None):
    #     """
    #     This function alters the colormap intensities
    #     """
    #     # Check if cbarLimits have been adjusted
    #     if cbarLimits is not None and CONFIG.colorbar:
    #         maxValue = CONFIG.colorbarRange[1]
    #     else:
    #         maxValue = np.max(data)
    #
    #     # Determine what are normalization values
    #     # Convert from % to number
    #     cmapMin = (maxValue * min) / 100
    #     cmapMid = (maxValue * mid) / 100
    #     cmapMax = (maxValue * max) / 100
    #
    #     norm_method = CONFIG.normalization_2D
    #
    #     if norm_method == "Midpoint":
    #         cmapNormalization = MidpointNormalize(midpoint=cmapMid, v_min=cmapMin, v_max=cmapMax, clip=False)
    #     elif norm_method == "Logarithmic":
    #         from matplotlib.colors import LogNorm
    #
    #         cmapNormalization = LogNorm(vmin=cmapMin, vmax=cmapMax)
    #     elif norm_method == "Power":
    #         from matplotlib.colors import PowerNorm
    #
    #         cmapNormalization = PowerNorm(gamma=CONFIG.normalization_2D_power_gamma, vmin=cmapMin, vmax=cmapMax)
    #
    #     return cmapNormalization
    #
    # def plot_3D_update(self, plotName="all", evt=None):
    #     plt_kwargs = self._buildPlotParameters(plotType="3D")
    #
    #     if plotName in ["all", "3D"]:
    #         try:
    #             self.plot_heatmap_3d.plot_3D_update(**plt_kwargs)
    #             self.plot_heatmap_3d.repaint()
    #         except AttributeError:
    #             pass
