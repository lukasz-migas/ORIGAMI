"""MS pre-processing settings panel"""
# Standard library imports
import logging
from copy import deepcopy

# Third-party imports
import wx
from pubsub import pub

# Local imports
from origami.styles import MiniFrame
from origami.styles import Validator
from origami.config.config import CONFIG
from origami.utils.converters import str2int
from origami.utils.converters import str2num
from origami.objects.containers import MassSpectrumObject
from origami.gui_elements.mixins import DatasetMixin
from origami.gui_elements.mixins import ConfigUpdateMixin
from origami.gui_elements.helpers import make_checkbox
from origami.handlers.queue_handler import QUEUE

logger = logging.getLogger(__name__)


class PanelProcessMassSpectrum(MiniFrame, DatasetMixin, ConfigUpdateMixin):
    """Mass spectrum processing panel"""

    # panel settings
    TIMER_DELAY = 1000  # ms
    TIMER_PLOT_DELAY = 500  # ms
    PUB_IN_PROGRESS_EVENT = "widget.process.spectrum"
    PANEL_BASE_TITLE = "Process Mass Spectrum"

    # ui elements
    document_info_text = None
    dataset_info_text = None
    ms_process_crop = None
    crop_min_value = None
    crop_max_value = None
    ms_process_linearize = None
    baseline_warning_msg = None
    ms_process_threshold = None
    ms_sigma_value = None
    ms_window_value = None
    ms_threshold_value = None
    ms_baseline_choice = None
    ms_baseline_polynomial_order = None
    ms_baseline_curved_window = None
    ms_baseline_median_window = None
    ms_baseline_tophat_window = None
    bin_linearization_method_choice = None
    bin_ppm_value = None
    bin_mzStart_value = None
    bin_mzEnd_value = None
    bin_autoRange_check = None
    bin_mzBinSize_value = None
    ms_process_smooth = None
    ms_smoothFcn_choice = None
    ms_polynomial_value = None
    ms_smooth_moving_window = None
    ms_process_normalize = None
    plot_btn = None
    add_to_document_btn = None
    cancel_btn = None
    activity_indicator = None

    def __init__(
        self,
        parent,
        presenter,
        document=None,
        document_title: str = None,
        dataset_name: str = None,
        mz_obj: MassSpectrumObject = None,
        disable_plot: bool = False,
        disable_process: bool = False,
        process_all: bool = False,
        update_widget: str = None,
        delay: int = 1000,
    ):
        MiniFrame.__init__(
            self,
            parent,
            title="Process mass spectrum...",
            style=wx.DEFAULT_FRAME_STYLE | wx.STAY_ON_TOP & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX),
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
        mz_obj : MassSpectrumObject
            instance of the spectrum that should be pre-processed
        disable_plot : bool
            disable plotting
        disable_process : bool
            disable pre-processing; only allow change of parameters
        process_all : bool
            process all elements in a group of mass spectra
        update_widget : str
            name of the pubsub event to be triggered when timer runs out
        delay : int
            amount of time between timed update
        """
        self.view = parent
        self.presenter = presenter

        # setup kwargs
        self.document = document
        self.document_title = document_title
        self.dataset_name = dataset_name
        self.mz_obj = mz_obj
        self.disable_plot = disable_plot
        self.disable_process = disable_process
        self.process_all = process_all
        self.update_widget = update_widget
        self.TIMER_DELAY = delay

        # enable on-demand updates using wxTimer
        self._timer = None
        if self.update_widget:
            self._timer = wx.Timer(self, True)
            self.Bind(wx.EVT_TIMER, self.on_update_widget, self._timer)

        self._plot_timer = None
        if not self.disable_plot:
            self._plot_timer = wx.Timer(self, True)
            self.Bind(wx.EVT_TIMER, self.on_update_plot)

        self.import_evt = True
        self.make_gui()
        self.setup()

        # setup layout
        self.CentreOnScreen()
        self.Show()
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

    def on_progress(self, is_running: bool, message: str):  # noqa
        """Handle extraction progress"""
        super(PanelProcessMassSpectrum, self).on_progress(is_running, message)

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
        self._config_mixin_setup()
        self._on_set_config()
        if self.PUB_IN_PROGRESS_EVENT:
            pub.subscribe(self.on_progress, self.PUB_IN_PROGRESS_EVENT)

    def on_close(self, evt, force: bool = False):
        """Overwrite close"""
        self._dataset_mixin_teardown()
        self._config_mixin_teardown()
        if self.PUB_IN_PROGRESS_EVENT:
            pub.unsubscribe(self.on_progress, self.PUB_IN_PROGRESS_EVENT)
        if self.update_widget:
            self._timer.Stop()
            # pub.sendMessage(self.update_widget)
        super(PanelProcessMassSpectrum, self).on_close(evt, force)

    def on_key_event(self, evt):
        """Trigger event based on keyboard input"""
        key_code = evt.GetKeyCode()
        if key_code == wx.WXK_ESCAPE:  # key = esc
            self.on_close(None)
        elif key_code in [66, 67, 76, 78, 83]:
            click_dict = {76: "linearize", 83: "smooth", 67: "crop", 66: "baseline", 78: "normalize"}
            self.on_click_on_setting(click_dict.get(key_code))
        elif key_code == 80 and not self.disable_plot and not self.disable_process:
            logger.info("Processing data")
            self.on_plot(None)
        elif key_code == 65 and not self.disable_plot and not self.disable_process:
            logger.info("Processing and adding data to document")
            self.on_add_to_document(None)

        if evt is not None:
            evt.Skip()

    # noinspection DuplicatedCode
    def make_panel(self):
        """Make settings panel"""
        panel = wx.Panel(self, -1, size=(-1, -1))

        document_info_text = wx.StaticText(panel, -1, "Document:")
        self.document_info_text = wx.StaticText(panel, -1, "")

        dataset_info_text = wx.StaticText(panel, -1, "Dataset:")
        self.dataset_info_text = wx.StaticText(panel, -1, "")

        ms_process_crop = wx.StaticText(panel, -1, "Crop spectrum:")
        self.ms_process_crop = make_checkbox(panel, "")
        self.ms_process_crop.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.ms_process_crop.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        crop_min_label = wx.StaticText(panel, wx.ID_ANY, "m/z start:")
        self.crop_min_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("floatPos"))
        self.crop_min_value.Bind(wx.EVT_TEXT, self.on_apply)

        crop_max_label = wx.StaticText(panel, wx.ID_ANY, "end:")
        self.crop_max_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("floatPos"))
        self.crop_max_value.Bind(wx.EVT_TEXT, self.on_apply)

        ms_process_linearize = wx.StaticText(panel, -1, "Linearize spectrum:")
        self.ms_process_linearize = make_checkbox(panel, "")
        self.ms_process_linearize.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.ms_process_linearize.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        linearization_method_label = wx.StaticText(panel, wx.ID_ANY, "Linearization mode:")
        self.bin_linearization_method_choice = wx.Choice(
            panel, -1, choices=CONFIG.ms_linearize_method_choices, size=(-1, -1)
        )
        self.bin_linearization_method_choice.Bind(wx.EVT_CHOICE, self.on_apply)
        self.bin_linearization_method_choice.Bind(wx.EVT_CHOICE, self.on_toggle_controls)

        bin_ms_min_label = wx.StaticText(panel, wx.ID_ANY, "m/z start:")
        self.bin_mzStart_value = wx.TextCtrl(panel, -1, "", size=(65, -1), validator=Validator("floatPos"))
        self.bin_mzStart_value.Bind(wx.EVT_TEXT, self.on_apply)

        bin_ms_max_label = wx.StaticText(panel, wx.ID_ANY, "end:")
        self.bin_mzEnd_value = wx.TextCtrl(panel, -1, "", size=(65, -1), validator=Validator("floatPos"))
        self.bin_mzEnd_value.Bind(wx.EVT_TEXT, self.on_apply)

        self.bin_autoRange_check = make_checkbox(panel, "Automatic range")
        self.bin_autoRange_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.bin_autoRange_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        bin_ms_bin_size_label = wx.StaticText(panel, wx.ID_ANY, "m/z bin size:")
        self.bin_mzBinSize_value = wx.TextCtrl(panel, -1, "", size=(65, -1), validator=Validator("floatPos"))
        self.bin_mzBinSize_value.Bind(wx.EVT_TEXT, self.on_apply)

        # bin_ms_ppm_label = wx.StaticText(panel, wx.ID_ANY, "Parts-per-million:")
        # self.bin_ppm_value = wx.TextCtrl(panel, -1, "", size=(65, -1), validator=Validator("floatPos"))
        # self.bin_ppm_value.Bind(wx.EVT_TEXT, self.on_apply)

        ms_process_smooth = wx.StaticText(panel, -1, "Smooth spectrum:")
        self.ms_process_smooth = make_checkbox(panel, "")
        self.ms_process_smooth.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.ms_process_smooth.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        smooth_method_label = wx.StaticText(panel, wx.ID_ANY, "Smooth function:")
        self.ms_smoothFcn_choice = wx.Choice(panel, -1, choices=CONFIG.ms_smooth_mode_choices, size=(-1, -1))
        self.ms_smoothFcn_choice.Bind(wx.EVT_CHOICE, self.on_apply)
        self.ms_smoothFcn_choice.Bind(wx.EVT_CHOICE, self.on_toggle_controls)

        polynomial_label = wx.StaticText(panel, wx.ID_ANY, "Savitzky-Golay polynomial order:")
        self.ms_polynomial_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("intPos"))
        self.ms_polynomial_value.Bind(wx.EVT_TEXT, self.on_apply)

        window_label = wx.StaticText(panel, wx.ID_ANY, "Savitzky-Golay window size:")
        self.ms_window_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("intPos"))
        self.ms_window_value.Bind(wx.EVT_TEXT, self.on_apply)

        sigma_label = wx.StaticText(panel, wx.ID_ANY, "Gaussian sigma:")
        self.ms_sigma_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("floatPos"))
        self.ms_sigma_value.Bind(wx.EVT_TEXT, self.on_apply)

        ms_smooth_moving_window = wx.StaticText(panel, wx.ID_ANY, "Moving average window size:")
        self.ms_smooth_moving_window = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("intPos"))
        self.ms_smooth_moving_window.Bind(wx.EVT_TEXT, self.on_apply)

        ms_process_threshold = wx.StaticText(panel, -1, "Subtract baseline:")
        self.ms_process_threshold = make_checkbox(panel, "")
        self.ms_process_threshold.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.ms_process_threshold.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        baseline_label = wx.StaticText(panel, wx.ID_ANY, "Subtraction mode:")
        self.ms_baseline_choice = wx.Choice(panel, choices=CONFIG.ms_baseline_method_choices)
        self.ms_baseline_choice.Bind(wx.EVT_CHOICE, self.on_apply)
        self.ms_baseline_choice.Bind(wx.EVT_CHOICE, self.on_toggle_controls)

        self.baseline_warning_msg = wx.StaticText(panel, wx.ID_ANY, "")

        threshold_label = wx.StaticText(panel, wx.ID_ANY, "Threshold:")
        self.ms_threshold_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("floatPos"))
        self.ms_threshold_value.Bind(wx.EVT_TEXT, self.on_apply)

        ms_baseline_polynomial_order = wx.StaticText(panel, wx.ID_ANY, "Polynomial order:")
        self.ms_baseline_polynomial_order = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("intPos"))
        self.ms_baseline_polynomial_order.Bind(wx.EVT_TEXT, self.on_apply)

        ms_baseline_curved_window = wx.StaticText(panel, wx.ID_ANY, "Curved window:")
        self.ms_baseline_curved_window = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("intPos"))
        self.ms_baseline_curved_window.Bind(wx.EVT_TEXT, self.on_apply)

        ms_baseline_median_window = wx.StaticText(panel, wx.ID_ANY, "Median window:")
        self.ms_baseline_median_window = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("intPos"))
        self.ms_baseline_median_window.Bind(wx.EVT_TEXT, self.on_apply)

        ms_baseline_tophat_window = wx.StaticText(panel, wx.ID_ANY, "Top Hat window:")
        self.ms_baseline_tophat_window = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("intPos"))
        self.ms_baseline_tophat_window.Bind(wx.EVT_TEXT, self.on_apply)

        ms_process_normalize = wx.StaticText(panel, -1, "Normalize spectrum:")
        self.ms_process_normalize = make_checkbox(panel, "")
        self.ms_process_normalize.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.ms_process_normalize.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        if not self.disable_plot:
            self.plot_btn = wx.Button(panel, wx.ID_OK, "Plot", size=(120, -1))
            self.plot_btn.Bind(wx.EVT_BUTTON, self.on_plot)

        if not self.disable_process:
            self.add_to_document_btn = wx.Button(panel, wx.ID_OK, "Add to document", size=(120, -1))
            self.add_to_document_btn.Bind(wx.EVT_BUTTON, self.on_add_to_document)

        self.cancel_btn = wx.Button(panel, wx.ID_OK, "Close", size=(120, -1))
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_close)

        self.activity_indicator = wx.ActivityIndicator(panel)
        self.activity_indicator.Hide()

        btn_grid = wx.BoxSizer()
        if not self.disable_plot:
            btn_grid.Add(self.plot_btn)
        if not self.disable_process:
            btn_grid.Add(self.add_to_document_btn)
        btn_grid.Add(self.cancel_btn)
        btn_grid.AddStretchSpacer()
        btn_grid.Add(self.activity_indicator, 0, wx.ALIGN_CENTER_VERTICAL)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(document_info_text, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.document_info_text, (n, 1), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(dataset_info_text, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.dataset_info_text, (n, 1), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
        n += 1
        grid.Add(ms_process_crop, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.ms_process_crop, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        n += 1
        grid.Add(crop_min_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.crop_min_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(crop_max_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.crop_max_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
        n += 1
        grid.Add(ms_process_linearize, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.ms_process_linearize, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        n += 1
        grid.Add(linearization_method_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(
            self.bin_linearization_method_choice, (n, 1), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND
        )
        n += 1
        grid.Add(bin_ms_min_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bin_mzStart_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(bin_ms_max_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bin_mzEnd_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.bin_autoRange_check, (n, 2), flag=wx.ALIGN_CENTER_VERTICAL)
        n += 1
        grid.Add(bin_ms_bin_size_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bin_mzBinSize_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        # n += 1
        # grid.Add(bin_ms_ppm_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        # grid.Add(self.bin_ppm_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
        n += 1
        grid.Add(ms_process_smooth, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.ms_process_smooth, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        n += 1
        grid.Add(smooth_method_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.ms_smoothFcn_choice, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(polynomial_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.ms_polynomial_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(window_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.ms_window_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(sigma_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.ms_sigma_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(ms_smooth_moving_window, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.ms_smooth_moving_window, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
        n += 1
        grid.Add(ms_process_threshold, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.ms_process_threshold, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        n += 1
        grid.Add(baseline_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.ms_baseline_choice, (n, 1), flag=wx.EXPAND)
        grid.Add(self.baseline_warning_msg, (n, 2), flag=wx.ALIGN_CENTER_VERTICAL)
        n += 1
        grid.Add(threshold_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.ms_threshold_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(ms_baseline_polynomial_order, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.ms_baseline_polynomial_order, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(ms_baseline_curved_window, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.ms_baseline_curved_window, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(ms_baseline_median_window, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.ms_baseline_median_window, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(ms_baseline_tophat_window, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.ms_baseline_tophat_window, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
        n += 1
        grid.Add(ms_process_normalize, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.ms_process_normalize, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.AddGrowableCol(1, 1)

        # fit layout
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND, 5)
        main_sizer.Add(btn_grid, 0, wx.ALIGN_CENTER_HORIZONTAL, 5)

        main_sizer.Fit(panel)

        panel.SetSizerAndFit(main_sizer)

        return panel

    def on_update_info(self, **kwargs):
        """Update information labels"""
        document_title = kwargs.get("document_title", self.document_title)
        dataset_name = kwargs.get("dataset_name", self.dataset_name)

        if document_title is None:
            document_title = "N/A"
        if dataset_name is None:
            dataset_name = "N/A"

        self.document_info_text.SetLabel(document_title)
        self.dataset_info_text.SetLabel(dataset_name)

    def on_update_widget(self, _evt):
        """Timer-based widget update"""
        if self.update_widget and isinstance(self.update_widget, str) and not self._timer.IsRunning():
            pub.sendMessage(self.update_widget)

    def on_update_plot(self, _evt):
        """Timer-based plot update"""
        if not self.disable_plot and not self._plot_timer.IsRunning():
            try:
                self.on_plot(None)
            except AttributeError:
                pass

    def on_plot(self, _evt):
        """Plot data"""
        pub.sendMessage(self.PUB_IN_PROGRESS_EVENT, is_running=True, message="")

        mz_obj = deepcopy(self.mz_obj)
        QUEUE.add_call(self.data_handling.on_process_ms, (mz_obj,), func_result=self._on_plot)

    def _on_plot(self, mz_obj: MassSpectrumObject):
        """Safely plot data"""
        self.panel_plot.view_ms.plot(obj=mz_obj)
        pub.sendMessage(self.PUB_IN_PROGRESS_EVENT, is_running=False, message="")

    def on_add_to_document(self, _evt):
        """Add data to document"""
        pub.sendMessage(self.PUB_IN_PROGRESS_EVENT, is_running=True, message="")
        # get new, unique name for the object
        new_name = self.document.get_new_name(self.dataset_name, "processed")

        # create copy of the object
        _, mz_obj = self.mz_obj.copy(new_name)
        QUEUE.add_call(
            self.data_handling.on_process_ms,
            (mz_obj,),
            func_result=self._on_add_to_document,
            func_result_args=(new_name,),
        )

    def _on_add_to_document(self, mz_obj: MassSpectrumObject, new_name: str):
        """Safely add data to document"""
        self.panel_plot.view_ms.plot(obj=mz_obj)
        mz_obj.flush()

        # notify document tree of changes
        self.document_tree.on_update_document(mz_obj.DOCUMENT_KEY, new_name.split("/")[-1], self.document_title)
        pub.sendMessage(self.PUB_IN_PROGRESS_EVENT, is_running=False, message="")

    def on_toggle_controls(self, evt):
        """Toggle controls based on some other settings"""
        if self.import_evt:
            return
        # crop
        CONFIG.ms_crop = self.ms_process_crop.GetValue()
        self.crop_min_value.Enable(enable=CONFIG.ms_crop)
        self.crop_max_value.Enable(enable=CONFIG.ms_crop)

        # linearize
        CONFIG.ms_linearize = self.ms_process_linearize.GetValue()
        self.bin_linearization_method_choice.Enable(enable=CONFIG.ms_linearize)
        self.bin_mzBinSize_value.Enable(enable=CONFIG.ms_linearize)
        self.bin_mzStart_value.Enable(enable=CONFIG.ms_linearize)
        self.bin_mzEnd_value.Enable(enable=CONFIG.ms_linearize)
        self.bin_autoRange_check.Enable(enable=CONFIG.ms_linearize)
        # self.bin_ppm_value.Enable(enable=CONFIG.ms_linearize)
        #
        # CONFIG.ms_linearize_method = self.bin_linearization_method_choice.GetStringSelection()
        # self.bin_ppm_value.Enable(enable=CONFIG.ms_linearize_method == "Parts-per-million")

        CONFIG.ms_linearize_mz_auto_range = self.bin_autoRange_check.GetValue()
        if CONFIG.ms_linearize:
            self.bin_mzStart_value.Enable(enable=not CONFIG.ms_linearize_mz_auto_range)
            self.bin_mzEnd_value.Enable(enable=not CONFIG.ms_linearize_mz_auto_range)

        # smooth
        CONFIG.ms_smooth = self.ms_process_smooth.GetValue()
        obj_list = [self.ms_sigma_value, self.ms_polynomial_value, self.ms_window_value, self.ms_smooth_moving_window]
        for item in obj_list:
            item.Enable(enable=False)
        self.ms_smoothFcn_choice.Enable(CONFIG.ms_smooth)

        CONFIG.ms_smooth_mode = self.ms_smoothFcn_choice.GetStringSelection()
        if CONFIG.ms_smooth:
            if CONFIG.ms_smooth_mode == "Gaussian":
                self.ms_sigma_value.Enable()
            elif CONFIG.ms_smooth_mode == "Savitzky-Golay":
                for item in [self.ms_polynomial_value, self.ms_window_value]:
                    item.Enable()
            elif CONFIG.ms_smooth_mode == "Moving average":
                self.ms_smooth_moving_window.Enable()

        # threshold
        CONFIG.ms_threshold = self.ms_process_threshold.GetValue()
        CONFIG.ms_baseline_method = self.ms_baseline_choice.GetStringSelection()
        obj_list = [
            self.ms_threshold_value,
            self.ms_baseline_choice,
            self.ms_baseline_polynomial_order,
            self.ms_baseline_curved_window,
            self.ms_baseline_median_window,
            self.ms_baseline_tophat_window,
        ]
        for item in obj_list:
            item.Enable(enable=False)
        self.ms_baseline_choice.Enable(enable=CONFIG.ms_threshold)
        self.baseline_warning_msg.SetLabel("")
        if CONFIG.ms_threshold:
            if CONFIG.ms_baseline_method == "Linear":
                self.ms_threshold_value.Enable()
            elif CONFIG.ms_baseline_method == "Polynomial":
                self.ms_baseline_polynomial_order.Enable()
            elif CONFIG.ms_baseline_method == "Curved":
                self.ms_baseline_curved_window.Enable()
                self.baseline_warning_msg.SetLabel("Note: Can be slow!")
            elif CONFIG.ms_baseline_method == "Median":
                self.ms_baseline_median_window.Enable()
            elif CONFIG.ms_baseline_method == "Top Hat":
                self.ms_baseline_tophat_window.Enable()

        if evt is not None:
            evt.Skip()

    def _on_set_config(self):
        """Update values from configuration file"""
        self.import_evt = True
        self.ms_process_crop.SetValue(CONFIG.ms_crop)
        self.crop_min_value.SetValue(str(CONFIG.ms_crop_min))
        self.crop_max_value.SetValue(str(CONFIG.ms_crop_max))

        self.ms_process_linearize.SetValue(CONFIG.ms_linearize)
        self.bin_linearization_method_choice.SetStringSelection(CONFIG.ms_linearize_method)
        self.bin_mzStart_value.SetValue(str(CONFIG.ms_linearize_mz_start))
        self.bin_mzEnd_value.SetValue(str(CONFIG.ms_linearize_mz_end))
        self.bin_autoRange_check.SetValue(CONFIG.ms_linearize_mz_auto_range)
        self.bin_mzBinSize_value.SetValue(str(CONFIG.ms_linearize_mz_bin_size))
        # self.bin_ppm_value.SetValue(str(CONFIG.ms_linearize_mz_ppm))

        self.ms_process_smooth.SetValue(CONFIG.ms_smooth)
        self.ms_smoothFcn_choice.SetStringSelection(CONFIG.ms_smooth_mode)
        self.ms_polynomial_value.SetValue(str(CONFIG.ms_smooth_polynomial))
        self.ms_window_value.SetValue(str(CONFIG.ms_smooth_window))
        self.ms_sigma_value.SetValue(str(CONFIG.ms_smooth_sigma))
        self.ms_smooth_moving_window.SetValue(str(CONFIG.ms_smooth_moving_window))

        self.ms_process_threshold.SetValue(CONFIG.ms_threshold)
        self.ms_baseline_choice.SetStringSelection(CONFIG.ms_baseline_method)
        self.ms_threshold_value.SetValue(str(CONFIG.ms_baseline_linear_threshold))
        self.ms_baseline_polynomial_order.SetValue(str(CONFIG.ms_baseline_polynomial_order))
        self.ms_baseline_curved_window.SetValue(str(CONFIG.ms_baseline_curved_window))
        self.ms_baseline_median_window.SetValue(str(CONFIG.ms_baseline_median_window))
        self.ms_baseline_tophat_window.SetValue(str(CONFIG.ms_baseline_tophat_window))

        self.ms_process_normalize.SetValue(CONFIG.ms_normalize)

        self.import_evt = False
        self.on_toggle_controls(None)
        self.on_apply(None)

    def on_apply(self, evt):
        """Update configuration based on changed values"""
        if self.import_evt:
            return
        CONFIG.ms_crop = self.ms_process_crop.GetValue()
        CONFIG.ms_linearize = self.ms_process_linearize.GetValue()
        CONFIG.ms_smooth = self.ms_process_smooth.GetValue()
        CONFIG.ms_threshold = self.ms_process_threshold.GetValue()
        CONFIG.ms_normalize = self.ms_process_normalize.GetValue()

        CONFIG.ms_linearize_mz_start = str2num(self.bin_mzStart_value.GetValue())
        CONFIG.ms_linearize_mz_end = str2num(self.bin_mzEnd_value.GetValue())
        CONFIG.ms_linearize_mz_bin_size = str2num(self.bin_mzBinSize_value.GetValue())
        # CONFIG.ms_linearize_mz_ppm = str2num(self.bin_ppm_value.GetValue())

        CONFIG.ms_linearize_method = self.bin_linearization_method_choice.GetStringSelection()
        CONFIG.ms_linearize_mz_auto_range = self.bin_autoRange_check.GetValue()

        CONFIG.ms_smooth_mode = self.ms_smoothFcn_choice.GetStringSelection()
        CONFIG.ms_smooth_sigma = str2num(self.ms_sigma_value.GetValue())
        CONFIG.ms_smooth_window = str2int(self.ms_window_value.GetValue())
        CONFIG.ms_smooth_polynomial = str2int(self.ms_polynomial_value.GetValue())
        CONFIG.ms_smooth_moving_window = str2int(self.ms_smooth_moving_window.GetValue())

        CONFIG.ms_baseline_linear_threshold = str2num(self.ms_threshold_value.GetValue())
        CONFIG.ms_baseline_method = self.ms_baseline_choice.GetStringSelection()
        CONFIG.ms_baseline_polynomial_order = str2int(self.ms_baseline_polynomial_order.GetValue())
        CONFIG.ms_baseline_curved_window = str2int(self.ms_baseline_curved_window.GetValue())
        CONFIG.ms_baseline_median_window = str2int(self.ms_baseline_median_window.GetValue())
        CONFIG.ms_baseline_tophat_window = str2int(self.ms_baseline_tophat_window.GetValue())

        CONFIG.ms_crop_min = str2num(self.crop_min_value.GetValue())
        CONFIG.ms_crop_max = str2num(self.crop_max_value.GetValue())

        # trigger widget update
        if self.update_widget and isinstance(self.update_widget, str):
            self._timer.Stop()
            self._timer.StartOnce(self.TIMER_DELAY)

        # trigger auto-plot update
        if not self.disable_plot:
            self._plot_timer.Stop()
            self._plot_timer.StartOnce(self.TIMER_PLOT_DELAY)

        if evt is not None:
            evt.Skip()

    def on_click_on_setting(self, setting):
        """Change setting value based on keyboard event"""
        if setting == "linearize":
            CONFIG.ms_linearize = not CONFIG.ms_linearize
            self.ms_process_linearize.SetValue(CONFIG.ms_linearize)
        elif setting == "smooth":
            CONFIG.ms_smooth = not CONFIG.ms_smooth
            self.ms_process_smooth.SetValue(CONFIG.ms_smooth)
        elif setting == "crop":
            CONFIG.ms_crop = not CONFIG.ms_crop
            self.ms_process_crop.SetValue(CONFIG.ms_crop)
        elif setting == "baseline":
            CONFIG.ms_threshold = not CONFIG.ms_threshold
            self.ms_process_threshold.SetValue(CONFIG.ms_threshold)
        elif setting == "normalize":
            CONFIG.ms_normalize = not CONFIG.ms_normalize
            self.ms_process_normalize.SetValue(CONFIG.ms_normalize)

        self.on_toggle_controls(None)


def _main():

    from origami.app import App

    app = App()
    ex = PanelProcessMassSpectrum(None, None)

    ex.Show()
    app.MainLoop()


if __name__ == "__main__":
    _main()
