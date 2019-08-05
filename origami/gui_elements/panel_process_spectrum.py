# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import copy
import logging

import wx
from styles import makeCheckbox
from styles import MiniFrame
from styles import validator
from utils.converters import str2int
from utils.converters import str2num

logger = logging.getLogger("origami")

# TODO: speed up plotting


class PanelProcessMassSpectrum(MiniFrame):
    """Mass spectrum processing panel"""

    def __init__(self, parent, presenter, config, icons, **kwargs):
        MiniFrame.__init__(
            self, parent, title="Process mass spectrum...", style=wx.DEFAULT_FRAME_STYLE & ~wx.RESIZE_BORDER
        )
        self.view = parent
        self.presenter = presenter
        self.documentTree = self.view.panelDocuments.documents
        self.data_handling = presenter.data_handling
        self.config = config
        self.icons = icons

        self.data_processing = presenter.data_processing
        self.data_handling = presenter.data_handling
        self.panel_plot = self.view.panelPlots

        # setup kwargs
        self.document = kwargs.pop("document", None)
        self.document_title = kwargs.pop("document_title", None)
        self.dataset_name = kwargs.pop("dataset_name", None)
        self.mz_data = kwargs.pop("mz_data", None)
        self.disable_plot = kwargs.get("disable_plot", False)
        self.disable_process = kwargs.get("disable_process", False)
        self.process_all = kwargs.get("process_all", False)

        self.make_gui()
        self.on_toggle_controls(None)
        self.on_update_info()

        # setup layout
        self.CentreOnScreen()
        self.Show(True)
        self.SetFocus()

        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_event)

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

    def make_panel(self):
        """Make settings panel"""
        panel = wx.Panel(self, -1, size=(-1, -1))

        document_info_text = wx.StaticText(panel, -1, "Document:")
        self.document_info_text = wx.StaticText(panel, -1, "")

        dataset_info_text = wx.StaticText(panel, -1, "Dataset:")
        self.dataset_info_text = wx.StaticText(panel, -1, "")

        ms_process_crop = wx.StaticText(panel, -1, "Crop spectrum:")
        self.ms_process_crop = makeCheckbox(panel, "")
        self.ms_process_crop.SetValue(self.config.ms_process_crop)
        self.ms_process_crop.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.ms_process_crop.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        crop_min_label = wx.StaticText(panel, wx.ID_ANY, "m/z start:")
        self.crop_min_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator("floatPos"))
        self.crop_min_value.SetValue(str(self.config.ms_crop_min))
        self.crop_min_value.Bind(wx.EVT_TEXT, self.on_apply)

        crop_max_label = wx.StaticText(panel, wx.ID_ANY, "end:")
        self.crop_max_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator("floatPos"))
        self.crop_max_value.SetValue(str(self.config.ms_crop_max))
        self.crop_max_value.Bind(wx.EVT_TEXT, self.on_apply)

        ms_process_linearize = wx.StaticText(panel, -1, "Linearize spectrum:")
        self.ms_process_linearize = makeCheckbox(panel, "")
        self.ms_process_linearize.SetValue(self.config.ms_process_linearize)
        self.ms_process_linearize.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.ms_process_linearize.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        linearizationMode_label = wx.StaticText(panel, wx.ID_ANY, "Linearization mode:")
        self.bin_linearizationMode_choice = wx.Choice(
            panel, -1, choices=self.config.ms_linearization_mode_choices, size=(-1, -1)
        )
        self.bin_linearizationMode_choice.SetStringSelection(self.config.ms_linearization_mode)
        self.bin_linearizationMode_choice.Bind(wx.EVT_CHOICE, self.on_apply)

        bin_ms_min_label = wx.StaticText(panel, wx.ID_ANY, "m/z start:")
        self.bin_mzStart_value = wx.TextCtrl(panel, -1, "", size=(65, -1), validator=validator("floatPos"))
        self.bin_mzStart_value.SetValue(str(self.config.ms_mzStart))
        self.bin_mzStart_value.Bind(wx.EVT_TEXT, self.on_apply)

        bin_ms_max_label = wx.StaticText(panel, wx.ID_ANY, "end:")
        self.bin_mzEnd_value = wx.TextCtrl(panel, -1, "", size=(65, -1), validator=validator("floatPos"))
        self.bin_mzEnd_value.SetValue(str(self.config.ms_mzEnd))
        self.bin_mzEnd_value.Bind(wx.EVT_TEXT, self.on_apply)

        self.bin_autoRange_check = makeCheckbox(panel, "Automatic range")
        self.bin_autoRange_check.SetValue(self.config.ms_auto_range)
        self.bin_autoRange_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.bin_autoRange_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        bin_ms_binsize_label = wx.StaticText(panel, wx.ID_ANY, "m/z bin size:")
        self.bin_mzBinSize_value = wx.TextCtrl(panel, -1, "", size=(65, -1), validator=validator("floatPos"))
        self.bin_mzBinSize_value.SetValue(str(self.config.ms_mzBinSize))
        self.bin_mzBinSize_value.Bind(wx.EVT_TEXT, self.on_apply)

        ms_process_smooth = wx.StaticText(panel, -1, "Smooth spectrum:")
        self.ms_process_smooth = makeCheckbox(panel, "")
        self.ms_process_smooth.SetValue(self.config.ms_process_smooth)
        self.ms_process_smooth.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.ms_process_smooth.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        smoothFcn_label = wx.StaticText(panel, wx.ID_ANY, "Smooth function:")
        self.ms_smoothFcn_choice = wx.Choice(panel, -1, choices=self.config.ms_smooth_choices, size=(-1, -1))
        self.ms_smoothFcn_choice.SetStringSelection(self.config.ms_smooth_mode)
        self.ms_smoothFcn_choice.Bind(wx.EVT_CHOICE, self.on_apply)
        self.ms_smoothFcn_choice.Bind(wx.EVT_CHOICE, self.on_toggle_controls)

        polynomial_label = wx.StaticText(panel, wx.ID_ANY, "Savitzky-Golay polynomial order:")
        self.ms_polynomial_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator("intPos"))
        self.ms_polynomial_value.SetValue(str(self.config.ms_smooth_polynomial))
        self.ms_polynomial_value.Bind(wx.EVT_TEXT, self.on_apply)

        window_label = wx.StaticText(panel, wx.ID_ANY, "Savitzky-Golay window size:")
        self.ms_window_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator("intPos"))
        self.ms_window_value.SetValue(str(self.config.ms_smooth_window))
        self.ms_window_value.Bind(wx.EVT_TEXT, self.on_apply)

        sigma_label = wx.StaticText(panel, wx.ID_ANY, "Gaussian sigma:")
        self.ms_sigma_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator("floatPos"))
        self.ms_sigma_value.SetValue(str(self.config.ms_smooth_sigma))
        self.ms_sigma_value.Bind(wx.EVT_TEXT, self.on_apply)

        ms_smooth_moving_window = wx.StaticText(panel, wx.ID_ANY, "Moving average window size:")
        self.ms_smooth_moving_window = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator("intPos"))
        self.ms_smooth_moving_window.SetValue(str(self.config.ms_smooth_moving_window))
        self.ms_smooth_moving_window.Bind(wx.EVT_TEXT, self.on_apply)

        ms_process_threshold = wx.StaticText(panel, -1, "Subtract baseline:")
        self.ms_process_threshold = makeCheckbox(panel, "")
        self.ms_process_threshold.SetValue(self.config.ms_process_threshold)
        self.ms_process_threshold.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.ms_process_threshold.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        baseline_label = wx.StaticText(panel, wx.ID_ANY, "Subtraction mode:")

        self.ms_baseline_choice = wx.Choice(panel, choices=self.config.ms_baseline_choices)
        self.ms_baseline_choice.SetStringSelection(self.config.ms_baseline)
        self.ms_baseline_choice.Bind(wx.EVT_CHOICE, self.on_apply)
        self.ms_baseline_choice.Bind(wx.EVT_CHOICE, self.on_toggle_controls)

        threshold_label = wx.StaticText(panel, wx.ID_ANY, "Threshold:")
        self.ms_threshold_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator("floatPos"))
        self.ms_threshold_value.SetValue(str(self.config.ms_threshold))
        self.ms_threshold_value.Bind(wx.EVT_TEXT, self.on_apply)

        ms_baseline_polynomial_order = wx.StaticText(panel, wx.ID_ANY, "Polynomial order:")
        self.ms_baseline_polynomial_order = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator("intPos"))
        self.ms_baseline_polynomial_order.SetValue(str(self.config.ms_baseline_polynomial_order))
        self.ms_baseline_polynomial_order.Bind(wx.EVT_TEXT, self.on_apply)

        ms_baseline_curved_window = wx.StaticText(panel, wx.ID_ANY, "Window:")
        self.ms_baseline_curved_window = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator("intPos"))
        self.ms_baseline_curved_window.SetValue(str(self.config.ms_baseline_curved_window))
        self.ms_baseline_curved_window.Bind(wx.EVT_TEXT, self.on_apply)

        ms_process_normalize = wx.StaticText(panel, -1, "Normalize spectrum:")
        self.ms_process_normalize = makeCheckbox(panel, "")
        self.ms_process_normalize.SetValue(self.config.ms_process_normalize)
        self.ms_process_normalize.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.ms_process_normalize.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        if not self.disable_plot:
            self.plot_btn = wx.Button(panel, wx.ID_OK, "Plot", size=(120, 22))
            self.plot_btn.Bind(wx.EVT_BUTTON, self.on_plot)

        if not self.disable_process:
            self.add_to_document_btn = wx.Button(panel, wx.ID_OK, "Add to document", size=(120, 22))
            self.add_to_document_btn.Bind(wx.EVT_BUTTON, self.on_add_to_document)

        self.cancel_btn = wx.Button(panel, wx.ID_OK, "Cancel", size=(120, 22))
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_close)

        btn_grid = wx.GridBagSizer(2, 2)
        n = 0
        if not self.disable_plot:
            btn_grid.Add(self.plot_btn, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        if not self.disable_process:
            btn_grid.Add(self.add_to_document_btn, (n, 2), wx.GBSpan(1, 1), flag=wx.EXPAND)
        btn_grid.Add(self.cancel_btn, (n, 3), wx.GBSpan(1, 1), flag=wx.EXPAND)

        horizontal_line_0 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_1 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_2 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_3 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_4 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_5 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(document_info_text, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.document_info_text, (n, 1), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(dataset_info_text, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.dataset_info_text, (n, 1), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(horizontal_line_0, (n, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
        n += 1
        grid.Add(ms_process_crop, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.ms_process_crop, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        n += 1
        grid.Add(crop_min_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.crop_min_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(crop_max_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.crop_max_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(horizontal_line_1, (n, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
        n += 1
        grid.Add(ms_process_linearize, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.ms_process_linearize, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        n += 1
        grid.Add(linearizationMode_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bin_linearizationMode_choice, (n, 1), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n = n + 1
        grid.Add(bin_ms_min_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bin_mzStart_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(bin_ms_max_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bin_mzEnd_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.bin_autoRange_check, (n, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(bin_ms_binsize_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.bin_mzBinSize_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(horizontal_line_2, (n, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
        n += 1
        grid.Add(ms_process_smooth, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.ms_process_smooth, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        n += 1
        grid.Add(smoothFcn_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.ms_smoothFcn_choice, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(polynomial_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.ms_polynomial_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(window_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.ms_window_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(sigma_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.ms_sigma_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(ms_smooth_moving_window, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.ms_smooth_moving_window, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(horizontal_line_3, (n, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
        n += 1
        grid.Add(ms_process_threshold, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.ms_process_threshold, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        n += 1
        grid.Add(baseline_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.ms_baseline_choice, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(threshold_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.ms_threshold_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(ms_baseline_polynomial_order, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.ms_baseline_polynomial_order, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(ms_baseline_curved_window, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.ms_baseline_curved_window, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(horizontal_line_4, (n, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
        n += 1
        grid.Add(ms_process_normalize, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.ms_process_normalize, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        n += 1
        grid.Add(horizontal_line_5, (n, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
        n = n + 1
        grid.Add(btn_grid, (n, 0), wx.GBSpan(1, 3), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)

        # fit layout
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.ALIGN_CENTER_HORIZONTAL | wx.EXPAND, 5)
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

    def on_plot(self, evt):
        """Plot data"""
        mz_x = copy.deepcopy(self.mz_data["xvals"])
        mz_y = copy.deepcopy(self.mz_data["yvals"])
        mz_x, mz_y = self.data_processing.on_process_MS(mz_x, mz_y, return_data=True)

        #         self.panel_plot.on_simple_plot_1D(mz_x, mz_y, xlabel="m/z", ylabel="Intensity", plot="MS")
        self.panel_plot.on_plot_MS(mz_x, mz_y)

    def on_add_to_document(self, evt):
        if self.process_all:
            for dataset_name in self.mz_data:
                self.data_processing.on_process_MS_and_add_data(self.document_title, dataset_name)
            return

        self.data_processing.on_process_MS_and_add_data(self.document_title, self.dataset_name)

    def on_toggle_controls(self, evt):
        # crop
        self.config.ms_process_crop = self.ms_process_crop.GetValue()
        obj_list = [self.crop_min_value, self.crop_max_value]
        for item in obj_list:
            item.Enable(enable=self.config.ms_process_crop)

        # linearize
        self.config.ms_process_linearize = self.ms_process_linearize.GetValue()
        obj_list = [
            self.bin_linearizationMode_choice,
            self.bin_mzBinSize_value,
            self.bin_mzStart_value,
            self.bin_mzEnd_value,
            self.bin_autoRange_check,
        ]
        for item in obj_list:
            item.Enable(enable=self.config.ms_process_linearize)

        self.config.ms_auto_range = self.bin_autoRange_check.GetValue()
        if self.config.ms_process_linearize:
            self.bin_mzStart_value.Enable(enable=not self.config.ms_auto_range)
            self.bin_mzEnd_value.Enable(enable=not self.config.ms_auto_range)

        # smooth
        self.config.ms_process_smooth = self.ms_process_smooth.GetValue()
        obj_list = [self.ms_sigma_value, self.ms_polynomial_value, self.ms_window_value, self.ms_smooth_moving_window]
        for item in obj_list:
            item.Enable(enable=False)
        self.ms_smoothFcn_choice.Enable(self.config.ms_process_smooth)

        self.config.ms_smooth_mode = self.ms_smoothFcn_choice.GetStringSelection()
        if self.config.ms_process_smooth:
            if self.config.ms_smooth_mode == "Gaussian":
                self.ms_sigma_value.Enable()
            elif self.config.ms_smooth_mode == "Savitzky-Golay":
                for item in [self.ms_polynomial_value, self.ms_window_value]:
                    item.Enable()
            elif self.config.ms_smooth_mode == "Moving average":
                self.ms_smooth_moving_window.Enable()

        # threshold
        self.config.ms_process_threshold = self.ms_process_threshold.GetValue()
        self.config.ms_baseline = self.ms_baseline_choice.GetStringSelection()
        obj_list = [
            self.ms_threshold_value,
            self.ms_baseline_choice,
            self.ms_baseline_polynomial_order,
            self.ms_baseline_curved_window,
        ]
        for item in obj_list:
            item.Enable(enable=False)
        self.ms_baseline_choice.Enable(enable=self.config.ms_process_threshold)

        if self.config.ms_process_threshold:
            if self.config.ms_baseline == "Linear":
                self.ms_threshold_value.Enable()
            elif self.config.ms_baseline == "Polynomial":
                self.ms_baseline_polynomial_order.Enable()
            elif self.config.ms_baseline == "Curved":
                self.ms_baseline_curved_window.Enable()

        if evt is not None:
            evt.Skip()

    def on_apply(self, evt):
        self.config.ms_process_crop = self.ms_process_crop.GetValue()
        self.config.ms_process_linearize = self.ms_process_linearize.GetValue()
        self.config.ms_process_smooth = self.ms_process_smooth.GetValue()
        self.config.ms_process_threshold = self.ms_process_threshold.GetValue()
        self.config.ms_process_normalize = self.ms_process_normalize.GetValue()

        self.config.ms_mzStart = str2num(self.bin_mzStart_value.GetValue())
        self.config.ms_mzEnd = str2num(self.bin_mzEnd_value.GetValue())
        self.config.ms_mzBinSize = str2num(self.bin_mzBinSize_value.GetValue())

        self.config.ms_linearization_mode = self.bin_linearizationMode_choice.GetStringSelection()
        self.config.ms_auto_range = self.bin_autoRange_check.GetValue()

        self.config.ms_smooth_mode = self.ms_smoothFcn_choice.GetStringSelection()
        self.config.ms_smooth_sigma = str2num(self.ms_sigma_value.GetValue())
        self.config.ms_smooth_window = str2int(self.ms_window_value.GetValue())
        self.config.ms_smooth_polynomial = str2int(self.ms_polynomial_value.GetValue())
        self.config.ms_smooth_moving_window = str2int(self.ms_smooth_moving_window.GetValue())

        self.config.ms_threshold = str2num(self.ms_threshold_value.GetValue())
        self.config.ms_baseline = self.ms_baseline_choice.GetStringSelection()
        self.config.ms_baseline_polynomial_order = str2int(self.ms_baseline_polynomial_order.GetValue())
        self.config.ms_baseline_curved_window = str2int(self.ms_baseline_curved_window.GetValue())

        self.config.ms_crop_min = str2num(self.crop_min_value.GetValue())
        self.config.ms_crop_max = str2num(self.crop_max_value.GetValue())

        if evt is not None:
            evt.Skip()

    def on_click_on_setting(self, setting):
        """Change setting value based on keyboard event"""
        if setting == "linearize":
            self.config.ms_process_linearize = not self.config.ms_process_linearize
            self.ms_process_linearize.SetValue(self.config.ms_process_linearize)
        elif setting == "smooth":
            self.config.ms_process_smooth = not self.config.ms_process_smooth
            self.ms_process_smooth.SetValue(self.config.ms_process_smooth)
        elif setting == "crop":
            self.config.ms_process_crop = not self.config.ms_process_crop
            self.ms_process_crop.SetValue(self.config.ms_process_crop)
        elif setting == "baseline":
            self.config.ms_process_threshold = not self.config.ms_process_threshold
            self.ms_process_threshold.SetValue(self.config.ms_process_threshold)
        elif setting == "normalize":
            self.config.ms_process_normalize = not self.config.ms_process_normalize
            self.ms_process_normalize.SetValue(self.config.ms_process_normalize)

        self.on_toggle_controls(None)
