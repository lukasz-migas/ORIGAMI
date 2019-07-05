# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import logging

import wx
from styles import validator, MiniFrame, makeCheckbox, makeToggleBtn
from utils.converters import str2num, str2int
logger = logging.getLogger('origami')


class PanelProcessMassSpectrum(MiniFrame):
    """
    """

    def __init__(self, parent, presenter, config, icons, **kwargs):
        MiniFrame.__init__(self, parent, title='Process mass spectrum...')
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
        self.document = kwargs.pop('document', None)
        self.document_title = kwargs.pop('document_title', None)
        self.dataset_name = kwargs.pop('dataset_name', None)
        self.mz_data = kwargs.pop('mz_data', None)

        self.make_gui()
        self.on_toggle_controls(None)

        self.CentreOnScreen()
        self.SetFocus()

    def make_gui(self):

        # make panel
        panel = self.make_panel()

        # pack element
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.Add(panel, 1, wx.EXPAND, 0)

        # fit layout
        self.main_sizer.Fit(self)
        self.SetSizer(self.main_sizer)

    def make_panel(self):
        panel = wx.Panel(self, -1, size=(-1, -1))
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.ms_process_crop = makeCheckbox(panel, 'Crop spectrum')
        self.ms_process_crop.SetValue(self.config.ms_process_crop)
        self.ms_process_crop.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.ms_process_crop.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        crop_min_label = wx.StaticText(panel, wx.ID_ANY, 'm/z start:')
        self.crop_min_value = wx.TextCtrl(
            panel, -1, '', size=(-1, -1),
            validator=validator('floatPos'),
        )
        self.crop_min_value.SetValue(str(self.config.ms_crop_min))
        self.crop_min_value.Bind(wx.EVT_TEXT, self.on_apply)

        crop_max_label = wx.StaticText(panel, wx.ID_ANY, 'end:')
        self.crop_max_value = wx.TextCtrl(
            panel, -1, '', size=(-1, -1),
            validator=validator('floatPos'),
        )
        self.crop_max_value.SetValue(str(self.config.ms_crop_max))
        self.crop_max_value.Bind(wx.EVT_TEXT, self.on_apply)

        self.ms_process_linearize = makeCheckbox(panel, 'Linearize spectrum')
        self.ms_process_linearize.SetValue(self.config.ms_process_linearize)
        self.ms_process_linearize.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.ms_process_linearize.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        linearizationMode_label = wx.StaticText(panel, wx.ID_ANY, 'Linearization mode:')
        self.bin_linearizationMode_choice = wx.Choice(
            panel, -1, choices=self.config.ms_linearization_mode_choices,
            size=(-1, -1),
        )
        self.bin_linearizationMode_choice.SetStringSelection(self.config.ms_linearization_mode)
        self.bin_linearizationMode_choice.Bind(wx.EVT_CHOICE, self.on_apply)

        bin_ms_min_label = wx.StaticText(panel, wx.ID_ANY, 'm/z start:')
        self.bin_mzStart_value = wx.TextCtrl(
            panel, -1, '', size=(65, -1),
            validator=validator('floatPos'),
        )
        self.bin_mzStart_value.SetValue(str(self.config.ms_mzStart))
        self.bin_mzStart_value.Bind(wx.EVT_TEXT, self.on_apply)

        bin_ms_max_label = wx.StaticText(panel, wx.ID_ANY, 'end:')
        self.bin_mzEnd_value = wx.TextCtrl(
            panel, -1, '', size=(65, -1),
            validator=validator('floatPos'),
        )
        self.bin_mzEnd_value.SetValue(str(self.config.ms_mzEnd))
        self.bin_mzEnd_value.Bind(wx.EVT_TEXT, self.on_apply)

        self.bin_autoRange_check = makeCheckbox(panel, 'Automatic range')
        self.bin_autoRange_check.SetValue(self.config.ms_auto_range)
        self.bin_autoRange_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.bin_autoRange_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        bin_ms_binsize_label = wx.StaticText(panel, wx.ID_ANY, 'm/z bin size:')
        self.bin_mzBinSize_value = wx.TextCtrl(
            panel, -1, '', size=(65, -1),
            validator=validator('floatPos'),
        )
        self.bin_mzBinSize_value.SetValue(str(self.config.ms_mzBinSize))
        self.bin_mzBinSize_value.Bind(wx.EVT_TEXT, self.on_apply)

        self.ms_process_smooth = makeCheckbox(panel, 'Smooth spectrum')
        self.ms_process_smooth.SetValue(self.config.ms_process_smooth)
        self.ms_process_smooth.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.ms_process_smooth.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        smoothFcn_label = wx.StaticText(panel, wx.ID_ANY, 'Smooth function:')
        self.ms_smoothFcn_choice = wx.Choice(
            panel, -1, choices=self.config.ms_smooth_choices,
            size=(-1, -1),
        )
        self.ms_smoothFcn_choice.SetStringSelection(self.config.ms_smooth_mode)
        self.ms_smoothFcn_choice.Bind(wx.EVT_CHOICE, self.on_apply)
        self.ms_smoothFcn_choice.Bind(wx.EVT_CHOICE, self.on_toggle_controls)

        polynomial_label = wx.StaticText(panel, wx.ID_ANY, 'Polynomial:')
        self.ms_polynomial_value = wx.TextCtrl(
            panel, -1, '', size=(-1, -1),
            validator=validator('intPos'),
        )
        self.ms_polynomial_value.SetValue(str(self.config.ms_smooth_polynomial))
        self.ms_polynomial_value.Bind(wx.EVT_TEXT, self.on_apply)

        window_label = wx.StaticText(panel, wx.ID_ANY, 'Window size:')
        self.ms_window_value = wx.TextCtrl(
            panel, -1, '', size=(-1, -1),
            validator=validator('intPos'),
        )
        self.ms_window_value.SetValue(str(self.config.ms_smooth_window))
        self.ms_window_value.Bind(wx.EVT_TEXT, self.on_apply)

        sigma_label = wx.StaticText(panel, wx.ID_ANY, 'Sigma:')
        self.ms_sigma_value = wx.TextCtrl(
            panel, -1, '', size=(-1, -1),
            validator=validator('floatPos'),
        )
        self.ms_sigma_value.SetValue(str(self.config.ms_smooth_sigma))
        self.ms_sigma_value.Bind(wx.EVT_TEXT, self.on_apply)

        self.ms_process_threshold = makeCheckbox(panel, 'Baseline subtract')
        self.ms_process_threshold.SetValue(self.config.ms_process_threshold)
        self.ms_process_threshold.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.ms_process_threshold.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        threshold_label = wx.StaticText(panel, wx.ID_ANY, 'Baseline subtraction:')
        self.ms_threshold_value = wx.TextCtrl(
            panel, -1, '', size=(-1, -1),
            validator=validator('floatPos'),
        )
        self.ms_threshold_value.SetValue(str(self.config.ms_threshold))
        self.ms_threshold_value.Bind(wx.EVT_TEXT, self.on_apply)

        self.ms_process_normalize = makeCheckbox(panel, 'Normalize')
        self.ms_process_normalize.SetValue(self.config.ms_process_normalize)
        self.ms_process_normalize.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.ms_process_normalize.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        normalize_label = wx.StaticText(panel, wx.ID_ANY, 'Normalization mode:')

        self.ms_normalizeFcn_choice = wx.Choice(panel, choices=self.config.ms_normalize_choices)
        self.ms_normalizeFcn_choice.SetStringSelection(self.config.ms_normalize_mode)
        self.ms_normalizeFcn_choice.Bind(wx.EVT_CHOICE, self.on_apply)
        self.ms_normalizeFcn_choice.Bind(wx.EVT_CHOICE, self.on_toggle_controls)

        self.plot_btn = wx.Button(panel, wx.ID_OK, 'Plot', size=(-1, 22))
        self.plot_btn.Bind(wx.EVT_BUTTON, self.on_plot)

        self.add_to_document_btn = wx.Button(panel, wx.ID_OK, 'Add to document', size=(-1, 22))
        self.add_to_document_btn.Bind(wx.EVT_BUTTON, self.on_add_to_document)

        self.cancel_btn = wx.Button(panel, wx.ID_OK, 'Cancel', size=(-1, 22))
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_close)

        horizontal_line_1 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_2 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_3 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_4 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_5 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(self.ms_process_crop, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n += 1
        grid.Add(crop_min_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.crop_min_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(crop_max_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.crop_max_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(horizontal_line_1, (n, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
        n += 1
        grid.Add(self.ms_process_linearize, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
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
        grid.Add(self.ms_process_smooth, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
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
        grid.Add(horizontal_line_3, (n, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
        n += 1
        grid.Add(self.ms_process_threshold, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n += 1
        grid.Add(threshold_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.ms_threshold_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(horizontal_line_4, (n, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
        n += 1
        grid.Add(self.ms_process_normalize, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n += 1
        grid.Add(normalize_label, (n, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        grid.Add(self.ms_normalizeFcn_choice, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(horizontal_line_5, (n, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
        n += 1
        grid.Add(self.plot_btn, (n, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        grid.Add(self.add_to_document_btn, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        grid.Add(self.cancel_btn, (n, 2), wx.GBSpan(1, 1), flag=wx.EXPAND)

        main_sizer.Add(grid, 0, wx.ALIGN_CENTER_HORIZONTAL, 10)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def on_plot(self, evt):
        mz_x = self.mz_data["xvals"]
        mz_y = self.mz_data["yvals"]
        mz_x, mz_y = self.data_processing.on_process_MS(mz_x, mz_y, return_data=True)

        self.panel_plot.on_plot_MS(mz_x, mz_y)

    def on_add_to_document(self, evt):
        pass

    def on_toggle_controls(self, evt):
        # crop
        self.config.ms_process_crop = self.ms_process_crop.GetValue()
        obj_list = [self.crop_min_value, self.crop_max_value]
        for item in obj_list:
            item.Enable(enable=self.config.ms_process_crop)

        # linearize
        self.config.ms_process_linearize = self.ms_process_linearize.GetValue()
        obj_list = [self.bin_linearizationMode_choice, self.bin_mzBinSize_value,
                    self.bin_mzStart_value, self.bin_mzEnd_value, self.bin_autoRange_check]
        for item in obj_list:
            item.Enable(enable=self.config.ms_process_linearize)

        self.config.ms_auto_range = self.bin_autoRange_check.GetValue()
        if self.config.ms_process_linearize:
            self.bin_mzStart_value.Enable(enable=not self.config.ms_auto_range)
            self.bin_mzEnd_value.Enable(enable=not self.config.ms_auto_range)

        # smooth
        self.config.ms_process_smooth = self.ms_process_smooth.GetValue()
        obj_list = [self.ms_smoothFcn_choice, self.ms_sigma_value, self.ms_polynomial_value,
                    self.ms_window_value]
        for item in obj_list:
            item.Enable(enable=self.config.ms_process_smooth)

        self.config.ms_smooth_mode = self.ms_smoothFcn_choice.GetStringSelection()
        if self.config.ms_process_smooth:
            if self.config.ms_smooth_mode == 'None':
                for item in [self.ms_polynomial_value, self.ms_sigma_value, self.ms_window_value]:
                    item.Disable()
            elif self.config.ms_smooth_mode == 'Gaussian':
                for item in [self.ms_polynomial_value, self.ms_window_value]:
                    item.Disable()
                self.ms_sigma_value.Enable()
            else:
                for item in [self.ms_polynomial_value, self.ms_window_value]:
                    item.Enable()
                self.ms_sigma_value.Disable()

        # threshold
        self.config.ms_process_threshold = self.ms_process_threshold.GetValue()
        obj_list = [self.ms_threshold_value]
        for item in obj_list:
            item.Enable(enable=self.config.ms_process_threshold)

        # normalize
        self.config.ms_process_normalize = self.ms_process_normalize.GetValue()
        obj_list = [self.ms_normalizeFcn_choice]

        for item in obj_list:
            item.Enable(enable=self.config.ms_process_normalize)

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

        self.config.ms_normalize_mode = self.ms_normalizeFcn_choice.GetStringSelection()
        self.config.ms_smooth_mode = self.ms_smoothFcn_choice.GetStringSelection()
        self.config.ms_smooth_sigma = str2num(self.ms_sigma_value.GetValue())
        self.config.ms_smooth_window = str2int(self.ms_window_value.GetValue())
        self.config.ms_smooth_polynomial = str2int(self.ms_polynomial_value.GetValue())
        self.config.ms_threshold = str2num(self.ms_threshold_value.GetValue())

        self.config.ms_crop_min = str2num(self.crop_min_value.GetValue())
        self.config.ms_crop_max = str2num(self.crop_max_value.GetValue())

        if evt is not None:
            evt.Skip()
