"""Heatmap pre-processing settings panel"""
# Standard library imports
import logging
from typing import List
from typing import Union

# Third-party imports
import wx
from pubsub import pub

# Local imports
from origami.styles import MiniFrame
from origami.styles import Validator
from origami.styles import make_checkbox
from origami.config.config import CONFIG
from origami.utils.converters import str2int
from origami.utils.converters import str2num
from origami.objects.containers import IonHeatmapObject
from origami.objects.containers import MassSpectrumHeatmapObject
from origami.handlers.queue_handler import QUEUE
from origami.gui_elements.panel_base import DatasetMixin

logger = logging.getLogger(__name__)


class PanelProcessHeatmap(MiniFrame, DatasetMixin):
    """Heatmap processing panel"""

    # panel settings
    TIMER_DELAY = 1000  # ms
    PUB_IN_PROGRESS_EVENT = "widget.process.heatmap"
    PANEL_BASE_TITLE = "Process Heatmap"

    # ui elements
    document_info_text = None
    dataset_info_text = None
    crop_check = None
    crop_xmin_value = None
    crop_xmax_value = None
    crop_ymin_value = None
    crop_ymax_value = None
    interpolate_check = None
    smooth_check = None
    baseline_check = None
    normalize_check = None
    interpolate_fold = None
    interpolate_choice = None
    interpolate_xaxis = None
    interpolate_yaxis = None
    smooth_choice = None
    smooth_sigma_value = None
    smooth_window_value = None
    smooth_poly_order_value = None
    baseline_threshold_value = None
    normalize_choice = None
    plot_btn = None
    add_to_document_btn = None
    cancel_btn = None

    def __init__(
        self,
        parent,
        presenter,
        document=None,
        document_title: str = None,
        dataset_name: str = None,
        heatmap_obj: Union[IonHeatmapObject, MassSpectrumHeatmapObject] = None,
        disable_plot: bool = False,
        disable_process: bool = False,
        process_all: bool = False,
        process_list: List = None,
        update_widget: str = None,
    ):
        MiniFrame.__init__(
            self,
            parent,
            title="Process heatmap...",
            style=wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX),
        )
        """Instantiate pre-processing module

        Parameters
        ----------
        parent :
            parent of the object
        presenter : ORIGAMI instance
            instance of the presenter/main class
        document : DocumentStore
            instance of document
        document_title : str
            name of the document
        heatmap_obj : IonHeatmapObject
            instance of the spectrum that should be pre-processed
        disable_plot : bool
            disable plotting
        disable_process : bool
            disable pre-processing; only allow change of parameters
        process_all : bool
            process all elements in a group of mass spectra
        update_widget : str
            name of the pubsub event to be triggered when timer runs out
        """
        self.view = parent
        self.presenter = presenter

        # setup kwargs
        self.document = document
        self.document_title = document_title
        self.dataset_name = dataset_name
        self.heatmap_obj = heatmap_obj
        self.disable_plot = disable_plot
        self.disable_process = disable_process
        self.process_all = process_all
        self.update_widget = update_widget
        self.process_list = process_list

        self.make_gui()
        self.setup()

        # setup layout
        self.CentreOnScreen()
        self.Show(True)
        self.SetFocus()

    @property
    def data_handling(self):
        """Return handle to `data_processing`"""
        return self.presenter.data_handling

    @property
    def panel_plot(self):
        """Return handle to `panel_plot`"""
        return self.view.panelPlots

    @property
    def document_tree(self):
        """Return handle to `document_tree`"""
        return self.presenter.view.panelDocuments.documents

    def on_progress(self, is_running: bool, message: str):
        """Handle extraction progress"""
        super(PanelProcessHeatmap, self).on_progress(is_running, message)

        # disable import button
        if self.plot_btn is not None:
            self.plot_btn.Enable(not is_running)
        if self.add_to_document_btn is not None:
            self.add_to_document_btn.Enable(not is_running)

    def setup(self):
        """Setup UI"""
        self.on_toggle_controls(None)
        self.on_update_info()
        self._dataset_mixin_setup()
        if self.PUB_IN_PROGRESS_EVENT:
            pub.subscribe(self.on_progress, self.PUB_IN_PROGRESS_EVENT)

    def on_close(self, evt, force: bool = False):
        """Overwrite close"""
        self._dataset_mixin_teardown()
        if self.PUB_IN_PROGRESS_EVENT:
            pub.unsubscribe(self.on_progress, self.PUB_IN_PROGRESS_EVENT)
        super(PanelProcessHeatmap, self).on_close(evt, force)

    def on_key_event(self, evt):
        """Trigger event based on keyboard input"""
        key_code = evt.GetKeyCode()
        if key_code == wx.WXK_ESCAPE:  # key = esc
            self.on_close(None)
        elif key_code in [66, 67, 73, 78, 83]:
            click_dict = {73: "interpolate", 83: "smooth", 67: "crop", 66: "baseline", 78: "normalize"}
            self.on_click_on_setting(click_dict.get(key_code))
        elif key_code == 80 and not self.disable_plot and not self.disable_process:
            self.on_plot(None)
        elif key_code == 65 and not self.disable_plot and not self.disable_process:
            self.on_add_to_document(None)

        if evt is not None:
            evt.Skip()

    def make_panel(self):
        """Make settings panel"""
        panel = wx.Panel(self, -1, size=(-1, -1))

        self.document_info_text = wx.StaticText(panel, -1, "", style=wx.ST_ELLIPSIZE_START)
        self.dataset_info_text = wx.StaticText(panel, -1, "", style=wx.ST_ELLIPSIZE_START)

        self.crop_check = make_checkbox(panel, "")
        self.crop_check.SetValue(CONFIG.heatmap_process_crop)
        self.crop_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.crop_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        self.crop_xmin_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("floatPos"))
        self.crop_xmin_value.SetValue(str(CONFIG.heatmap_crop_xmin))
        self.crop_xmin_value.Bind(wx.EVT_TEXT, self.on_apply)

        self.crop_xmax_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("floatPos"))
        self.crop_xmax_value.SetValue(str(CONFIG.heatmap_crop_xmax))
        self.crop_xmax_value.Bind(wx.EVT_TEXT, self.on_apply)

        self.crop_ymin_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("floatPos"))
        self.crop_ymin_value.SetValue(str(CONFIG.heatmap_crop_ymin))
        self.crop_ymin_value.Bind(wx.EVT_TEXT, self.on_apply)

        self.crop_ymax_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("floatPos"))
        self.crop_ymax_value.SetValue(str(CONFIG.heatmap_crop_ymax))
        self.crop_ymax_value.Bind(wx.EVT_TEXT, self.on_apply)

        self.interpolate_check = make_checkbox(panel, "")
        self.interpolate_check.SetValue(CONFIG.heatmap_process_interpolate)
        self.interpolate_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.interpolate_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        self.interpolate_choice = wx.Choice(panel, -1, choices=CONFIG.heatmap_interpolate_choices, size=(-1, -1))
        self.interpolate_choice.SetStringSelection(CONFIG.heatmap_interpolate_mode)
        self.interpolate_choice.Bind(wx.EVT_CHOICE, self.on_apply)

        self.interpolate_fold = wx.TextCtrl(panel, -1, "", size=(65, -1), validator=Validator("floatPos"))
        self.interpolate_fold.SetValue(str(CONFIG.heatmap_interpolate_fold))
        self.interpolate_fold.Bind(wx.EVT_TEXT, self.on_apply)

        self.interpolate_xaxis = make_checkbox(panel, "")
        self.interpolate_xaxis.SetValue(CONFIG.heatmap_interpolate_xaxis)
        self.interpolate_xaxis.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.interpolate_yaxis = make_checkbox(panel, "")
        self.interpolate_yaxis.SetValue(CONFIG.heatmap_interpolate_yaxis)
        self.interpolate_yaxis.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.smooth_check = make_checkbox(panel, "")
        self.smooth_check.SetValue(CONFIG.heatmap_process_smooth)
        self.smooth_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.smooth_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        self.smooth_choice = wx.Choice(panel, -1, choices=CONFIG.heatmap_smooth_choices, size=(-1, -1))
        self.smooth_choice.SetStringSelection(CONFIG.ms_smooth_mode)
        self.smooth_choice.Bind(wx.EVT_CHOICE, self.on_apply)
        self.smooth_choice.Bind(wx.EVT_CHOICE, self.on_toggle_controls)

        self.smooth_poly_order_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("intPos"))
        self.smooth_poly_order_value.SetValue(str(CONFIG.heatmap_smooth_polynomial))
        self.smooth_poly_order_value.Bind(wx.EVT_TEXT, self.on_apply)

        self.smooth_window_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("intPos"))
        self.smooth_window_value.SetValue(str(CONFIG.heatmap_smooth_window))
        self.smooth_window_value.Bind(wx.EVT_TEXT, self.on_apply)

        self.smooth_sigma_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("floatPos"))
        self.smooth_sigma_value.SetValue(str(CONFIG.heatmap_smooth_sigma))
        self.smooth_sigma_value.Bind(wx.EVT_TEXT, self.on_apply)

        self.baseline_check = make_checkbox(panel, "")
        self.baseline_check.SetValue(CONFIG.heatmap_process_threshold)
        self.baseline_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.baseline_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        self.baseline_threshold_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("floatPos"))
        self.baseline_threshold_value.SetValue(str(CONFIG.ms_baseline_linear_threshold))
        self.baseline_threshold_value.Bind(wx.EVT_TEXT, self.on_apply)

        self.normalize_check = make_checkbox(panel, "")
        self.normalize_check.SetValue(CONFIG.heatmap_normalize)
        self.normalize_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.normalize_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        self.normalize_choice = wx.Choice(panel, -1, choices=CONFIG.heatmap_normalize_choices, size=(-1, -1))
        self.normalize_choice.SetStringSelection(CONFIG.heatmap_normalize_mode)
        self.normalize_choice.Bind(wx.EVT_CHOICE, self.on_apply)

        if not self.disable_plot:
            self.plot_btn = wx.Button(panel, wx.ID_OK, "Plot", size=(120, 22))
            self.plot_btn.Bind(wx.EVT_BUTTON, self.on_plot)

        if not self.disable_process:
            self.add_to_document_btn = wx.Button(panel, wx.ID_OK, "Add to document", size=(120, 22))
            self.add_to_document_btn.Bind(wx.EVT_BUTTON, self.on_add_to_document)

        self.cancel_btn = wx.Button(panel, wx.ID_OK, "Cancel", size=(120, 22))
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_close)

        self.activity_indicator = wx.ActivityIndicator(panel)
        self.activity_indicator.Hide()

        btn_grid = wx.BoxSizer(wx.HORIZONTAL)
        if not self.disable_plot:
            btn_grid.Add(self.plot_btn)
        if not self.disable_process:
            btn_grid.Add(self.add_to_document_btn)
        btn_grid.Add(self.cancel_btn)
        btn_grid.Add(self.activity_indicator, 0, wx.ALIGN_CENTER_VERTICAL)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(wx.StaticText(panel, -1, "Document:"), (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.document_info_text, (n, 1), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(wx.StaticText(panel, -1, "Dataset name:"), (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.dataset_info_text, (n, 1), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
        n += 1
        grid.Add(wx.StaticText(panel, -1, "Crop heatmap:"), (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.crop_check, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        n += 1
        grid.Add(
            wx.StaticText(panel, wx.ID_ANY, "start (x-axis):"), (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT
        )
        grid.Add(self.crop_xmin_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(
            wx.StaticText(panel, wx.ID_ANY, "end (x-axis):"), (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT
        )
        grid.Add(self.crop_xmax_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(
            wx.StaticText(panel, wx.ID_ANY, "start (y-axis):"), (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT
        )
        grid.Add(self.crop_ymin_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(
            wx.StaticText(panel, wx.ID_ANY, "end (y-axis):"), (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT
        )
        grid.Add(self.crop_ymax_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
        n += 1
        grid.Add(
            wx.StaticText(panel, -1, "Interpolate heatmap:"), (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT
        )
        grid.Add(self.interpolate_check, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        n += 1
        grid.Add(
            wx.StaticText(panel, wx.ID_ANY, "Interpolation method:"),
            (n, 0),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT,
        )
        grid.Add(self.interpolate_choice, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(wx.StaticText(panel, wx.ID_ANY, "Fold:"), (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.interpolate_fold, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(wx.StaticText(panel, -1, "x-axis:"), (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.interpolate_xaxis, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(wx.StaticText(panel, -1, "y-axis:"), (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.interpolate_yaxis, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
        n += 1
        grid.Add(wx.StaticText(panel, -1, "Smooth heatmap:"), (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.smooth_check, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        n += 1
        grid.Add(
            wx.StaticText(panel, wx.ID_ANY, "Smooth function:"), (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT
        )
        grid.Add(self.smooth_choice, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(
            wx.StaticText(panel, wx.ID_ANY, "Savitzky-Golay polynomial order:"),
            (n, 0),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT,
        )
        grid.Add(self.smooth_poly_order_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(
            wx.StaticText(panel, wx.ID_ANY, "Savitzky-Golay window size:"),
            (n, 0),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT,
        )
        grid.Add(self.smooth_window_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(
            wx.StaticText(panel, wx.ID_ANY, "Gaussian sigma:"), (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT
        )
        grid.Add(self.smooth_sigma_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
        n += 1
        grid.Add(wx.StaticText(panel, -1, "Subtract baseline:"), (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.baseline_check, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        n += 1
        grid.Add(wx.StaticText(panel, wx.ID_ANY, "Threshold:"), (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.baseline_threshold_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
        n += 1
        grid.Add(wx.StaticText(panel, -1, "Normalize heatmap:"), (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.normalize_check, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        n += 1
        grid.Add(
            wx.StaticText(panel, wx.ID_ANY, "Normalization mode:"),
            (n, 0),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT,
        )
        grid.Add(self.normalize_choice, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.AddGrowableCol(1, 1)

        # fit layout
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND, 5)
        main_sizer.Add(btn_grid, 0, wx.ALIGN_CENTER_HORIZONTAL, 5)

        panel.SetSizerAndFit(main_sizer)

        return panel

    def on_update_info(self):
        """Update information labels"""
        document_title = self.document_title
        dataset_name = self.dataset_name

        if document_title is None:
            document_title = "N/A"
        if dataset_name is None:
            dataset_name = "N/A"

        if self.process_list:
            document_title = dataset_name = "Various"

        self.document_info_text.SetLabel(document_title)
        self.dataset_info_text.SetLabel(dataset_name)

    def on_plot(self, _evt):
        """Plot data"""
        pub.sendMessage(self.PUB_IN_PROGRESS_EVENT, is_running=True, message="")
        from copy import deepcopy

        heatmap_obj = deepcopy(self.heatmap_obj)
        QUEUE.add_call(self.data_handling.on_process_heatmap, (heatmap_obj,), func_result=self._on_plot)

    def on_add_to_document(self, _evt):
        """Add data to document"""
        pub.sendMessage(self.PUB_IN_PROGRESS_EVENT, is_running=True, message="")
        new_name = self.document.get_new_name(self.dataset_name, "processed")

        # create copy of the object
        _, heatmap_obj = self.heatmap_obj.copy(new_name)

        # process and flush to disk
        # heatmap_obj = self.data_handling.on_process_heatmap(heatmap_obj)
        QUEUE.add_call(
            self.data_handling.on_process_heatmap,
            (heatmap_obj,),
            func_result=self._on_add_to_document,
            func_result_args=(new_name,),
        )

    def _on_plot(self, heatmap_obj: Union[MassSpectrumHeatmapObject, IonHeatmapObject]):
        """Safely plot data"""
        if isinstance(heatmap_obj, MassSpectrumHeatmapObject):
            self.panel_plot.view_msdt.plot(obj=heatmap_obj)
        else:
            self.panel_plot.view_heatmap.plot(obj=heatmap_obj)
        pub.sendMessage(self.PUB_IN_PROGRESS_EVENT, is_running=False, message="")

    def _on_add_to_document(self, heatmap_obj: Union[MassSpectrumHeatmapObject, IonHeatmapObject], new_name: str):
        """Safely add data to document"""
        if isinstance(heatmap_obj, MassSpectrumHeatmapObject):
            self.panel_plot.view_msdt.plot(obj=heatmap_obj)
        else:
            self.panel_plot.view_heatmap.plot(obj=heatmap_obj)
        heatmap_obj.flush()

        # notify document tree of changes
        self.document_tree.on_update_document(heatmap_obj.DOCUMENT_KEY, new_name.split("/")[-1], self.document_title)
        pub.sendMessage(self.PUB_IN_PROGRESS_EVENT, is_running=False, message="")

    def on_toggle_controls(self, evt):
        """Toggle controls based on some other settings"""
        # crop
        CONFIG.heatmap_process_crop = self.crop_check.GetValue()
        self.crop_xmin_value.Enable(CONFIG.heatmap_process_crop)
        self.crop_xmax_value.Enable(CONFIG.heatmap_process_crop)
        self.crop_ymin_value.Enable(CONFIG.heatmap_process_crop)
        self.crop_ymax_value.Enable(CONFIG.heatmap_process_crop)

        # linearize
        CONFIG.heatmap_process_interpolate = self.interpolate_check.GetValue()
        self.interpolate_choice.Enable(CONFIG.heatmap_process_interpolate)
        self.interpolate_fold.Enable(CONFIG.heatmap_process_interpolate)
        self.interpolate_xaxis.Enable(CONFIG.heatmap_process_interpolate)
        self.interpolate_yaxis.Enable(CONFIG.heatmap_process_interpolate)

        # smooth
        CONFIG.heatmap_process_smooth = self.smooth_check.GetValue()
        obj_list = [self.smooth_sigma_value, self.smooth_poly_order_value, self.smooth_window_value]
        for item in obj_list:
            item.Enable(enable=False)
        self.smooth_choice.Enable(CONFIG.heatmap_process_smooth)

        CONFIG.ms_smooth_mode = self.smooth_choice.GetStringSelection()
        if CONFIG.heatmap_process_smooth:
            if CONFIG.ms_smooth_mode == "Gaussian":
                self.smooth_sigma_value.Enable()
            elif CONFIG.ms_smooth_mode == "Savitzky-Golay":
                for item in [self.smooth_poly_order_value, self.smooth_window_value]:
                    item.Enable()

        # threshold
        CONFIG.heatmap_process_threshold = self.baseline_check.GetValue()
        self.baseline_threshold_value.Enable(CONFIG.heatmap_process_threshold)

        # normalize
        CONFIG.heatmap_normalize = self.normalize_check.GetValue()
        self.normalize_choice.Enable(CONFIG.heatmap_normalize)

        if evt is not None:
            evt.Skip()

    def on_apply(self, evt):
        """Update config values"""
        CONFIG.heatmap_process_crop = self.crop_check.GetValue()
        CONFIG.heatmap_process_interpolate = self.interpolate_check.GetValue()
        CONFIG.heatmap_process_smooth = self.smooth_check.GetValue()
        CONFIG.heatmap_process_threshold = self.baseline_check.GetValue()
        CONFIG.heatmap_normalize = self.normalize_check.GetValue()

        CONFIG.heatmap_interpolate_fold = str2int(self.interpolate_fold.GetValue())
        CONFIG.heatmap_interpolate_mode = self.interpolate_choice.GetStringSelection()
        CONFIG.heatmap_interpolate_xaxis = self.interpolate_xaxis.GetValue()
        CONFIG.heatmap_interpolate_yaxis = self.interpolate_yaxis.GetValue()

        CONFIG.heatmap_crop_xmin = str2num(self.crop_xmin_value.GetValue())
        CONFIG.heatmap_crop_xmax = str2num(self.crop_xmax_value.GetValue())
        CONFIG.heatmap_crop_ymin = str2num(self.crop_ymin_value.GetValue())
        CONFIG.heatmap_crop_ymax = str2num(self.crop_ymax_value.GetValue())

        CONFIG.heatmap_smooth_mode = self.smooth_choice.GetStringSelection()
        CONFIG.heatmap_smooth_sigma = str2num(self.smooth_sigma_value.GetValue())
        CONFIG.heatmap_smooth_window = str2int(self.smooth_window_value.GetValue())
        CONFIG.heatmap_smooth_polynomial = str2int(self.smooth_poly_order_value.GetValue())

        CONFIG.heatmap_threshold = str2num(self.baseline_threshold_value.GetValue())

        CONFIG.heatmap_normalize_mode = self.normalize_choice.GetStringSelection()

        if evt is not None:
            evt.Skip()

    def on_click_on_setting(self, setting):
        """Change setting value based on keyboard event"""
        if setting == "interpolate":
            CONFIG.heatmap_process_interpolate = not CONFIG.heatmap_process_interpolate
            self.interpolate_check.SetValue(CONFIG.heatmap_process_interpolate)
        elif setting == "smooth":
            CONFIG.heatmap_process_smooth = not CONFIG.heatmap_process_smooth
            self.smooth_check.SetValue(CONFIG.heatmap_process_smooth)
        elif setting == "crop":
            CONFIG.heatmap_process_crop = not CONFIG.heatmap_process_crop
            self.crop_check.SetValue(CONFIG.heatmap_process_crop)
        elif setting == "baseline":
            CONFIG.heatmap_process_threshold = not CONFIG.heatmap_process_threshold
            self.baseline_check.SetValue(CONFIG.heatmap_process_threshold)
        elif setting == "normalize":
            CONFIG.heatmap_normalize = not CONFIG.heatmap_normalize
            self.normalize_check.SetValue(CONFIG.heatmap_normalize)

        self.on_toggle_controls(None)


def _main():
    app = wx.App()
    ex = PanelProcessHeatmap(None, None)
    ex.Show()
    app.MainLoop()


if __name__ == "__main__":
    _main()
