# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import copy
import logging

import wx
from styles import make_checkbox
from styles import MiniFrame
from styles import validator
from utils.converters import str2int
from utils.converters import str2num

logger = logging.getLogger(__name__)

# TODO: remove self.data and self.document and rather always get new instance of the document which accounts for
# changes


class PanelProcessHeatmap(MiniFrame):
    """Heatmap processing panel"""

    def __init__(self, parent, presenter, config, icons, **kwargs):
        MiniFrame.__init__(self, parent, title="Process heatmap...", style=wx.DEFAULT_FRAME_STYLE & ~wx.RESIZE_BORDER)
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
        self.dataset_type = kwargs.pop("dataset_type", None)
        self.dataset_name = kwargs.pop("dataset_name", None)
        self.data = kwargs.pop("data", None)
        self.disable_plot = kwargs.get("disable_plot", False)
        self.disable_process = kwargs.get("disable_process", False)
        self.process_all = kwargs.get("process_all", False)
        self.process_list = kwargs.get("process_list", False)

        self.make_gui()
        self.on_toggle_controls(None)
        self.on_update_info()

        # setup layout
        self.CentreOnScreen()
        self.Show(True)
        self.SetFocus()

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

        document_info_text = wx.StaticText(panel, -1, "Document:")
        self.document_info_text = wx.StaticText(panel, -1, "")

        dataset_type_info_text = wx.StaticText(panel, -1, "Dataset type:")
        self.dataset_type_info_text = wx.StaticText(panel, -1, "")

        dataset_info_text = wx.StaticText(panel, -1, "Dataset name:")
        self.dataset_info_text = wx.StaticText(panel, -1, "")

        plot2D_process_crop = wx.StaticText(panel, -1, "Crop heatmap:")
        self.plot2D_process_crop = make_checkbox(panel, "")
        self.plot2D_process_crop.SetValue(self.config.plot2D_process_crop)
        self.plot2D_process_crop.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.plot2D_process_crop.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        plot2D_crop_xmin = wx.StaticText(panel, wx.ID_ANY, "start (x-axis):")
        self.plot2D_crop_xmin = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator("floatPos"))
        self.plot2D_crop_xmin.SetValue(str(self.config.plot2D_crop_xmin))
        self.plot2D_crop_xmin.Bind(wx.EVT_TEXT, self.on_apply)

        plot2D_crop_xmax = wx.StaticText(panel, wx.ID_ANY, "end (x-axis):")
        self.plot2D_crop_xmax = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator("floatPos"))
        self.plot2D_crop_xmax.SetValue(str(self.config.plot2D_crop_xmax))
        self.plot2D_crop_xmax.Bind(wx.EVT_TEXT, self.on_apply)

        plot2D_crop_ymin = wx.StaticText(panel, wx.ID_ANY, "start (y-axis):")
        self.plot2D_crop_ymin = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator("floatPos"))
        self.plot2D_crop_ymin.SetValue(str(self.config.plot2D_crop_ymin))
        self.plot2D_crop_ymin.Bind(wx.EVT_TEXT, self.on_apply)

        plot2D_crop_ymax = wx.StaticText(panel, wx.ID_ANY, "end (y-axis):")
        self.plot2D_crop_ymax = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator("floatPos"))
        self.plot2D_crop_ymax.SetValue(str(self.config.plot2D_crop_ymax))
        self.plot2D_crop_ymax.Bind(wx.EVT_TEXT, self.on_apply)

        plot2D_process_interpolate = wx.StaticText(panel, -1, "Interpolate heatmap:")
        self.plot2D_process_interpolate = make_checkbox(panel, "")
        self.plot2D_process_interpolate.SetValue(self.config.plot2D_process_interpolate)
        self.plot2D_process_interpolate.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.plot2D_process_interpolate.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        plot2D_interpolate_mode = wx.StaticText(panel, wx.ID_ANY, "Interpolation method:")
        self.plot2D_interpolate_mode = wx.Choice(
            panel, -1, choices=self.config.plot2D_interpolate_choices, size=(-1, -1)
        )
        self.plot2D_interpolate_mode.SetStringSelection(self.config.plot2D_interpolate_mode)
        self.plot2D_interpolate_mode.Bind(wx.EVT_CHOICE, self.on_apply)

        plot2D_interpolate_fold = wx.StaticText(panel, wx.ID_ANY, "Fold:")
        self.plot2D_interpolate_fold = wx.TextCtrl(panel, -1, "", size=(65, -1), validator=validator("floatPos"))
        self.plot2D_interpolate_fold.SetValue(str(self.config.plot2D_interpolate_fold))
        self.plot2D_interpolate_fold.Bind(wx.EVT_TEXT, self.on_apply)

        plot2D_interpolate_xaxis = wx.StaticText(panel, -1, "x-axis:")
        self.plot2D_interpolate_xaxis = make_checkbox(panel, "")
        self.plot2D_interpolate_xaxis.SetValue(self.config.plot2D_interpolate_xaxis)
        self.plot2D_interpolate_xaxis.Bind(wx.EVT_CHECKBOX, self.on_apply)

        plot2D_interpolate_yaxis = wx.StaticText(panel, -1, "y-axis:")
        self.plot2D_interpolate_yaxis = make_checkbox(panel, "")
        self.plot2D_interpolate_yaxis.SetValue(self.config.plot2D_interpolate_yaxis)
        self.plot2D_interpolate_yaxis.Bind(wx.EVT_CHECKBOX, self.on_apply)

        plot2D_process_smooth = wx.StaticText(panel, -1, "Smooth heatmap:")
        self.plot2D_process_smooth = make_checkbox(panel, "")
        self.plot2D_process_smooth.SetValue(self.config.plot2D_process_smooth)
        self.plot2D_process_smooth.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.plot2D_process_smooth.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        smoothFcn_label = wx.StaticText(panel, wx.ID_ANY, "Smooth function:")
        self.plot2D_smoothFcn_choice = wx.Choice(panel, -1, choices=self.config.plot2D_smooth_choices, size=(-1, -1))
        self.plot2D_smoothFcn_choice.SetStringSelection(self.config.ms_smooth_mode)
        self.plot2D_smoothFcn_choice.Bind(wx.EVT_CHOICE, self.on_apply)
        self.plot2D_smoothFcn_choice.Bind(wx.EVT_CHOICE, self.on_toggle_controls)

        polynomial_label = wx.StaticText(panel, wx.ID_ANY, "Savitzky-Golay polynomial order:")
        self.plot2D_polynomial_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator("intPos"))
        self.plot2D_polynomial_value.SetValue(str(self.config.plot2D_smooth_polynomial))
        self.plot2D_polynomial_value.Bind(wx.EVT_TEXT, self.on_apply)

        window_label = wx.StaticText(panel, wx.ID_ANY, "Savitzky-Golay window size:")
        self.plot2D_window_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator("intPos"))
        self.plot2D_window_value.SetValue(str(self.config.plot2D_smooth_window))
        self.plot2D_window_value.Bind(wx.EVT_TEXT, self.on_apply)

        sigma_label = wx.StaticText(panel, wx.ID_ANY, "Gaussian sigma:")
        self.plot2D_sigma_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator("floatPos"))
        self.plot2D_sigma_value.SetValue(str(self.config.plot2D_smooth_sigma))
        self.plot2D_sigma_value.Bind(wx.EVT_TEXT, self.on_apply)

        plot2D_process_threshold = wx.StaticText(panel, -1, "Subtract baseline:")
        self.plot2D_process_threshold = make_checkbox(panel, "")
        self.plot2D_process_threshold.SetValue(self.config.plot2D_process_threshold)
        self.plot2D_process_threshold.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.plot2D_process_threshold.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        threshold_label = wx.StaticText(panel, wx.ID_ANY, "Threshold:")
        self.plot2D_threshold_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator("floatPos"))
        self.plot2D_threshold_value.SetValue(str(self.config.ms_threshold))
        self.plot2D_threshold_value.Bind(wx.EVT_TEXT, self.on_apply)

        plot2D_process_normalize = wx.StaticText(panel, -1, "Normalize heatmap:")
        self.plot2D_process_normalize = make_checkbox(panel, "")
        self.plot2D_process_normalize.SetValue(self.config.plot2D_normalize)
        self.plot2D_process_normalize.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.plot2D_process_normalize.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        normalize_mode = wx.StaticText(panel, wx.ID_ANY, "Normalization mode:")
        self.plot2D_normalizeFcn_choice = wx.Choice(
            panel, -1, choices=self.config.plot2D_normalize_choices, size=(-1, -1)
        )
        self.plot2D_normalizeFcn_choice.SetStringSelection(self.config.plot2D_normalize_mode)
        self.plot2D_normalizeFcn_choice.Bind(wx.EVT_CHOICE, self.on_apply)

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
            btn_grid.Add(self.plot_btn, (n, 1), flag=wx.EXPAND)
        if not self.disable_process:
            btn_grid.Add(self.add_to_document_btn, (n, 2), flag=wx.EXPAND)
        btn_grid.Add(self.cancel_btn, (n, 3), flag=wx.EXPAND)

        horizontal_line_0 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_1 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_2 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_3 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_4 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_5 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(document_info_text, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.document_info_text, (n, 1), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(dataset_type_info_text, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.dataset_type_info_text, (n, 1), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(dataset_info_text, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.dataset_info_text, (n, 1), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(horizontal_line_0, (n, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
        n += 1
        grid.Add(plot2D_process_crop, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot2D_process_crop, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        n += 1
        grid.Add(plot2D_crop_xmin, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot2D_crop_xmin, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(plot2D_crop_xmax, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot2D_crop_xmax, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(plot2D_crop_ymin, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot2D_crop_ymin, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(plot2D_crop_ymax, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot2D_crop_ymax, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(horizontal_line_1, (n, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
        n += 1
        grid.Add(plot2D_process_interpolate, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot2D_process_interpolate, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        n += 1
        grid.Add(plot2D_interpolate_mode, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot2D_interpolate_mode, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(plot2D_interpolate_fold, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot2D_interpolate_fold, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(plot2D_interpolate_xaxis, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot2D_interpolate_xaxis, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(plot2D_interpolate_yaxis, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot2D_interpolate_yaxis, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(horizontal_line_2, (n, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
        n += 1
        grid.Add(plot2D_process_smooth, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot2D_process_smooth, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        n += 1
        grid.Add(smoothFcn_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot2D_smoothFcn_choice, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(polynomial_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot2D_polynomial_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(window_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot2D_window_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(sigma_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot2D_sigma_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(horizontal_line_3, (n, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
        n += 1
        grid.Add(plot2D_process_threshold, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot2D_process_threshold, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        n += 1
        grid.Add(threshold_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot2D_threshold_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(horizontal_line_4, (n, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
        n += 1
        grid.Add(plot2D_process_normalize, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot2D_process_normalize, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        n += 1
        grid.Add(normalize_mode, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot2D_normalizeFcn_choice, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        n += 1
        grid.Add(horizontal_line_5, (n, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
        n += 1
        grid.Add(btn_grid, (n, 0), wx.GBSpan(1, 3), flag=wx.ALIGN_CENTER)

        # fit layout
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.ALIGN_CENTER_HORIZONTAL | wx.EXPAND, 5)
        main_sizer.Fit(panel)

        panel.SetSizerAndFit(main_sizer)

        return panel

    def on_update_info(self, **kwargs):
        """Update information labels"""
        document_title = kwargs.get("document_title", self.document_title)
        dataset_type = kwargs.get("dataset_type", self.dataset_type)
        dataset_name = kwargs.get("dataset_name", self.dataset_name)

        if document_title is None:
            document_title = "N/A"
        if dataset_type is None:
            dataset_type = "N/A"
        if dataset_name is None:
            dataset_name = "N/A"

        if self.process_list:
            document_title = dataset_type = dataset_name = "Various"

        self.document_info_text.SetLabel(document_title)
        self.dataset_type_info_text.SetLabel(dataset_type)
        self.dataset_info_text.SetLabel(dataset_name)

    def on_plot(self, evt):
        """Plot data"""
        if self.disable_plot:
            return

        xvals = copy.deepcopy(self.data["xvals"])
        yvals = copy.deepcopy(self.data["yvals"])
        zvals = copy.deepcopy(self.data["zvals"])
        xvals, yvals, zvals = self.data_processing.on_process_2D(xvals, yvals, zvals, return_data=True)
        if "DT/MS" in self.dataset_type:
            self.panel_plot.on_plot_MSDT(zvals, xvals, yvals, self.data["xlabels"], self.data["ylabels"], override=True)
        else:
            self.panel_plot.on_plot_2D(zvals, xvals, yvals, self.data["xlabels"], self.data["ylabels"], override=False)

    def on_add_to_document(self, evt):
        # process anything that is in dataset
        if self.process_all and not self.process_list:
            for dataset_name in self.data:
                self.data_processing.on_process_2D_and_add_data(self.document_title, self.dataset_type, dataset_name)
            return

        # process anything that is in a list
        if self.process_list:
            for document_title, dataset_type, dataset_name in self.data:
                self.data_processing.on_process_2D_and_add_data(document_title, dataset_type, dataset_name)
            return

        self.data_processing.on_process_2D_and_add_data(self.document_title, self.dataset_type, self.dataset_name)

    def on_toggle_controls(self, evt):
        # crop
        self.config.plot2D_process_crop = self.plot2D_process_crop.GetValue()
        obj_list = [self.plot2D_crop_xmin, self.plot2D_crop_xmax, self.plot2D_crop_ymin, self.plot2D_crop_ymax]
        for item in obj_list:
            item.Enable(enable=self.config.plot2D_process_crop)

        # linearize
        self.config.plot2D_process_interpolate = self.plot2D_process_interpolate.GetValue()
        obj_list = [
            self.plot2D_interpolate_mode,
            self.plot2D_interpolate_fold,
            self.plot2D_interpolate_xaxis,
            self.plot2D_interpolate_yaxis,
        ]
        for item in obj_list:
            item.Enable(enable=self.config.plot2D_process_interpolate)

        # smooth
        self.config.plot2D_process_smooth = self.plot2D_process_smooth.GetValue()
        obj_list = [self.plot2D_sigma_value, self.plot2D_polynomial_value, self.plot2D_window_value]
        for item in obj_list:
            item.Enable(enable=False)
        self.plot2D_smoothFcn_choice.Enable(self.config.plot2D_process_smooth)

        self.config.ms_smooth_mode = self.plot2D_smoothFcn_choice.GetStringSelection()
        if self.config.plot2D_process_smooth:
            if self.config.ms_smooth_mode == "Gaussian":
                self.plot2D_sigma_value.Enable()
            elif self.config.ms_smooth_mode == "Savitzky-Golay":
                for item in [self.plot2D_polynomial_value, self.plot2D_window_value]:
                    item.Enable()

        # threshold
        self.config.plot2D_process_threshold = self.plot2D_process_threshold.GetValue()
        obj_list = [self.plot2D_threshold_value]
        for item in obj_list:
            item.Enable(enable=self.config.plot2D_process_threshold)

        # normalize
        self.config.plot2D_normalize = self.plot2D_process_normalize.GetValue()
        obj_list = [self.plot2D_normalizeFcn_choice]
        for item in obj_list:
            item.Enable(enable=self.config.plot2D_normalize)

        self.on_plot(None)

        if evt is not None:
            evt.Skip()

    def on_apply(self, evt):
        self.config.plot2D_process_crop = self.plot2D_process_crop.GetValue()
        self.config.plot2D_process_interpolate = self.plot2D_process_interpolate.GetValue()
        self.config.plot2D_process_smooth = self.plot2D_process_smooth.GetValue()
        self.config.plot2D_process_threshold = self.plot2D_process_threshold.GetValue()
        self.config.plot2D_normalize = self.plot2D_process_normalize.GetValue()

        self.config.plot2D_interpolate_fold = str2num(self.plot2D_interpolate_fold.GetValue())
        self.config.plot2D_interpolate_mode = self.plot2D_interpolate_mode.GetStringSelection()
        self.config.plot2D_interpolate_xaxis = self.plot2D_interpolate_xaxis.GetValue()
        self.config.plot2D_interpolate_yaxis = self.plot2D_interpolate_yaxis.GetValue()

        self.config.plot2D_crop_xmin = str2num(self.plot2D_crop_xmin.GetValue())
        self.config.plot2D_crop_xmax = str2num(self.plot2D_crop_xmax.GetValue())
        self.config.plot2D_crop_ymin = str2num(self.plot2D_crop_ymin.GetValue())
        self.config.plot2D_crop_ymax = str2num(self.plot2D_crop_ymax.GetValue())

        self.config.plot2D_smooth_mode = self.plot2D_smoothFcn_choice.GetStringSelection()
        self.config.plot2D_smooth_sigma = str2num(self.plot2D_sigma_value.GetValue())
        self.config.plot2D_smooth_window = str2int(self.plot2D_window_value.GetValue())
        self.config.plot2D_smooth_polynomial = str2int(self.plot2D_polynomial_value.GetValue())

        self.config.plot2D_threshold = str2num(self.plot2D_threshold_value.GetValue())

        self.config.plot2D_normalize_mode = self.plot2D_normalizeFcn_choice.GetStringSelection()

        if evt is not None:
            evt.Skip()

    def on_click_on_setting(self, setting):
        """Change setting value based on keyboard event"""
        if setting == "interpolate":
            self.config.plot2D_process_interpolate = not self.config.plot2D_process_interpolate
            self.plot2D_process_interpolate.SetValue(self.config.plot2D_process_interpolate)
        elif setting == "smooth":
            self.config.plot2D_process_smooth = not self.config.plot2D_process_smooth
            self.plot2D_process_smooth.SetValue(self.config.plot2D_process_smooth)
        elif setting == "crop":
            self.config.plot2D_process_crop = not self.config.plot2D_process_crop
            self.plot2D_process_crop.SetValue(self.config.plot2D_process_crop)
        elif setting == "baseline":
            self.config.plot2D_process_threshold = not self.config.plot2D_process_threshold
            self.plot2D_process_threshold.SetValue(self.config.plot2D_process_threshold)
        elif setting == "normalize":
            self.config.plot2D_normalize = not self.config.plot2D_normalize
            self.plot2D_process_normalize.SetValue(self.config.plot2D_normalize)

        self.on_toggle_controls(None)
