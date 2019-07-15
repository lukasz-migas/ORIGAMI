# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import logging

import wx
from styles import makeCheckbox
from styles import MiniFrame
from styles import validator
from styles import make_spin_ctrl
from utils.converters import str2num
logger = logging.getLogger('origami')

# TODO: speed up plotting


class PanelProcessExtractData(MiniFrame):
    """Extract data"""

    def __init__(self, parent, presenter, config, icons, **kwargs):
        MiniFrame.__init__(self, parent, title='Extract data...')
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
        self.parameters = dict()
        self.extraction_ranges = dict()

        if self.document is not None:
            self.parameters = self.document.parameters
            try:
                self.extraction_ranges = self.data_handling._get_waters_extraction_ranges(self.document)
            except (TypeError, ValueError, IndexError):
                logger.warning("Could not determine extraction ranges")

        self.disable_plot = kwargs.get('disable_plot', False)
        self.disable_process = kwargs.get('disable_process', False)
        self.process_all = kwargs.get('process_all', False)

        # make gui
        self.make_gui()

        # trigger updates
        self.on_toggle_controls(None)
        self.on_update_info()
        self.on_update_extraction_ranges()

        # setup layout
        self.CentreOnScreen()
        self.Show(True)
        self.SetFocus()

        # bind
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_event)

    def on_key_event(self, evt):
        """Trigger event based on keyboard input"""
        key_code = evt.GetKeyCode()
        if key_code == wx.WXK_ESCAPE:  # key = esc
            self.on_close(None)
#         elif key_code in [66, 67, 73, 78, 83]:
#             click_dict = {73: 'interpolate', 83: 'smooth', 67: 'crop', 66: 'baseline', 78: 'normalize'}
#             self.on_click_on_setting(click_dict.get(key_code))
#         elif key_code == 80 and not self.disable_plot and not self.disable_process:
#             self.on_plot(None)
#         elif key_code == 65 and not self.disable_plot and not self.disable_process:
#             self.on_add_to_document(None)

        if evt is not None:
            evt.Skip()

    def make_gui(self):
        """Make and arrange main panel"""

        # make panel
        panel = self.make_panel()

        # pack element
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.Add(panel, 1, wx.EXPAND, 5)

        # fit layout
        self.main_sizer.Fit(self)
        self.SetSizer(self.main_sizer)
        self.Layout()

    def make_panel(self):
        """Make settings panel"""
        panel = wx.Panel(self, -1, size=(-1, -1))

        document_info_text = wx.StaticText(panel, -1, 'Document:')
        self.document_info_text = wx.StaticText(panel, -1, '')

        extraction_info_text = wx.StaticText(panel, -1, 'Extraction \nranges:')
        self.extraction_info_text = wx.StaticText(panel, -1, '\n\n')

        start_label = wx.StaticText(panel, wx.ID_ANY, 'Min:')
        end_label = wx.StaticText(panel, wx.ID_ANY, 'Max:')

        self.mz_label = wx.StaticText(panel, wx.ID_ANY, 'm/z (Da):')
        self.extract_mzStart_value = make_spin_ctrl(panel,
                                                    self.config.extract_mzStart,
                                                    self.extraction_ranges.get("mass_range", [0, 99999])[0],
                                                    self.extraction_ranges.get("mass_range", [0, 99999])[1],
                                                    100)
        self.extract_mzStart_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        self.extract_mzEnd_value = make_spin_ctrl(panel,
                                                    self.config.extract_mzEnd,
                                                    self.extraction_ranges.get("mass_range", [0, 99999])[0],
                                                    self.extraction_ranges.get("mass_range", [0, 99999])[1],
                                                    100)
        self.extract_mzEnd_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        self.rt_label = wx.StaticText(panel, wx.ID_ANY, 'RT (min): ')
        self.extract_rtStart_value = wx.TextCtrl(
            panel, -1, '', size=(-1, -1),
            validator=validator('floatPos'),
        )
        self.extract_rtStart_value.SetValue(str(self.config.extract_rtStart))
        self.extract_rtStart_value.Bind(wx.EVT_TEXT, self.on_apply)

        self.extract_rtEnd_value = wx.TextCtrl(
            panel, -1, '', size=(-1, -1),
            validator=validator('floatPos'),
        )
        self.extract_rtEnd_value.SetValue(str(self.config.extract_rtEnd))
        self.extract_rtEnd_value.Bind(wx.EVT_TEXT, self.on_apply)

        self.extract_rt_scans_check = makeCheckbox(panel, 'In scans')
        self.extract_rt_scans_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.extract_rt_scans_check.Bind(wx.EVT_CHECKBOX, self.on_change_validator)
        self.extract_rt_scans_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        scanTime_label = wx.StaticText(panel, wx.ID_ANY, 'Scan time (s):')
        self.extract_scanTime_value = wx.TextCtrl(
            panel, -1, '', size=(-1, -1),
            validator=validator('floatPos'),
        )
        self.extract_scanTime_value.SetValue(str(self.parameters.get('scanTime', 1)))
        self.extract_scanTime_value.Bind(wx.EVT_TEXT, self.on_apply)

        self.dt_label = wx.StaticText(panel, wx.ID_ANY, 'DT (bins):')
        self.extract_dtStart_value = wx.TextCtrl(
            panel, -1, '', size=(-1, -1),
            validator=validator('floatPos'),
        )
        self.extract_dtStart_value.SetValue(str(self.config.extract_dtStart))
        self.extract_dtStart_value.Bind(wx.EVT_TEXT, self.on_apply)

        self.extract_dtEnd_value = wx.TextCtrl(
            panel, -1, '', size=(-1, -1),
            validator=validator('floatPos'),
        )
        self.extract_dtEnd_value.SetValue(str(self.config.extract_dtEnd))
        self.extract_dtEnd_value.Bind(wx.EVT_TEXT, self.on_apply)

        self.extract_dt_ms_check = makeCheckbox(panel, 'In ms')
        self.extract_dt_ms_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.extract_dt_ms_check.Bind(wx.EVT_CHECKBOX, self.on_change_validator)
        self.extract_dt_ms_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        pusherFreq_label = wx.StaticText(panel, wx.ID_ANY, 'Pusher frequency (ms):')
        self.extract_pusherFreq_value = wx.TextCtrl(
            panel, -1, '', size=(-1, -1),
            validator=validator('floatPos'),
        )
        self.extract_pusherFreq_value.SetValue(str(self.parameters.get('pusherFreq', 1)))
        self.extract_pusherFreq_value.Bind(wx.EVT_TEXT, self.on_apply)

        self.extract_extractMS_check = makeCheckbox(panel, 'Extract mass spectrum')
        self.extract_extractMS_check.SetValue(self.config.extract_massSpectra)
        self.extract_extractMS_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.extract_extractMS_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        self.extract_extractMS_ms_check = makeCheckbox(panel, 'm/z')
        self.extract_extractMS_ms_check.SetValue(False)
        self.extract_extractMS_ms_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.extract_extractMS_rt_check = makeCheckbox(panel, 'RT')
        self.extract_extractMS_rt_check.SetValue(True)
        self.extract_extractMS_rt_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.extract_extractMS_dt_check = makeCheckbox(panel, 'DT')
        self.extract_extractMS_dt_check.SetValue(True)
        self.extract_extractMS_dt_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.extract_extractRT_check = makeCheckbox(panel, 'Extract chromatogram')
        self.extract_extractRT_check.SetValue(self.config.extract_chromatograms)
        self.extract_extractRT_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.extract_extractRT_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        self.extract_extractRT_ms_check = makeCheckbox(panel, 'm/z')
        self.extract_extractRT_ms_check.SetValue(True)
        self.extract_extractRT_ms_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.extract_extractRT_dt_check = makeCheckbox(panel, 'DT')
        self.extract_extractRT_dt_check.SetValue(True)
        self.extract_extractRT_dt_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.extract_extractDT_check = makeCheckbox(panel, 'Extract mobilogram')
        self.extract_extractDT_check.SetValue(self.config.extract_driftTime1D)
        self.extract_extractDT_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.extract_extractDT_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        self.extract_extractDT_ms_check = makeCheckbox(panel, 'm/z')
        self.extract_extractDT_ms_check.SetValue(True)
        self.extract_extractDT_ms_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.extract_extractDT_rt_check = makeCheckbox(panel, 'RT')
        self.extract_extractDT_rt_check.SetValue(True)
        self.extract_extractDT_rt_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.extract_extract2D_check = makeCheckbox(panel, 'Extract heatmap')
        self.extract_extract2D_check.SetValue(self.config.extract_driftTime2D)
        self.extract_extract2D_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.extract_extract2D_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        self.extract_extract2D_ms_check = makeCheckbox(panel, 'm/z')
        self.extract_extract2D_ms_check.SetValue(True)
        self.extract_extract2D_ms_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.extract_extract2D_rt_check = makeCheckbox(panel, 'RT')
        self.extract_extract2D_rt_check.SetValue(True)
        self.extract_extract2D_rt_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        if not self.disable_plot:
            self.extract_btn = wx.Button(panel, wx.ID_OK, 'Extract', size=(120, 22))
            self.extract_btn.Bind(wx.EVT_BUTTON, self.on_extract)

        if not self.disable_process:
            self.add_to_document_btn = wx.Button(panel, wx.ID_OK, 'Add to document', size=(120, 22))
            self.add_to_document_btn.Bind(wx.EVT_BUTTON, self.on_add_to_document)

        self.cancel_btn = wx.Button(panel, wx.ID_OK, 'Cancel', size=(120, 22))
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_close)

        btn_grid = wx.GridBagSizer(2, 2)
        n = 0
        if not self.disable_plot:
            btn_grid.Add(self.extract_btn, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
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
        grid.Add(extraction_info_text, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.extraction_info_text, (n, 1), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(horizontal_line_0, (n, 0), wx.GBSpan(1, 4), flag=wx.EXPAND)
        n += 1
        grid.Add(start_label, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER)
        grid.Add(end_label, (n, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER)
        n = n + 1
        grid.Add(self.mz_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.EXPAND)
        grid.Add(self.extract_mzStart_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.extract_mzEnd_value, (n, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n = n + 1
        grid.Add(self.rt_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.EXPAND)
        grid.Add(self.extract_rtStart_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.extract_rtEnd_value, (n, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.extract_rt_scans_check, (n, 3), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n = n + 1
        grid.Add(scanTime_label, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.EXPAND)
        grid.Add(self.extract_scanTime_value, (n, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n = n + 1
        grid.Add(self.dt_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.EXPAND)
        grid.Add(self.extract_dtStart_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.extract_dtEnd_value, (n, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.extract_dt_ms_check, (n, 3), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n = n + 1
        grid.Add(pusherFreq_label, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.EXPAND)
        grid.Add(self.extract_pusherFreq_value, (n, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n = n + 1
        grid.Add(horizontal_line_1, (n, 0), wx.GBSpan(1, 4), flag=wx.EXPAND)
        n = n + 1
        grid.Add(self.extract_extractMS_check, (n, 1), wx.GBSpan(1, 3), flag=wx.ALIGN_LEFT | wx.EXPAND)
        n = n + 1
        grid.Add(self.extract_extractMS_ms_check, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.extract_extractMS_rt_check, (n, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.extract_extractMS_dt_check, (n, 3), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n = n + 1
        grid.Add(horizontal_line_2, (n, 0), wx.GBSpan(1, 4), flag=wx.EXPAND)
        n = n + 1
        grid.Add(self.extract_extractRT_check, (n, 1), wx.GBSpan(1, 3), flag=wx.ALIGN_LEFT | wx.EXPAND)
        n = n + 1
        grid.Add(self.extract_extractRT_ms_check, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.extract_extractRT_dt_check, (n, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n = n + 1
        grid.Add(horizontal_line_3, (n, 0), wx.GBSpan(1, 4), flag=wx.EXPAND)
        n = n + 1
        grid.Add(self.extract_extractDT_check, (n, 1), wx.GBSpan(1, 3), flag=wx.ALIGN_LEFT | wx.EXPAND)
        n = n + 1
        grid.Add(self.extract_extractDT_ms_check, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.extract_extractDT_rt_check, (n, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n = n + 1
        grid.Add(horizontal_line_4, (n, 0), wx.GBSpan(1, 4), flag=wx.EXPAND)
        n = n + 1
        grid.Add(self.extract_extract2D_check, (n, 1), wx.GBSpan(1, 3), flag=wx.ALIGN_LEFT | wx.EXPAND)
        n = n + 1
        grid.Add(self.extract_extract2D_ms_check, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.extract_extract2D_rt_check, (n, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n = n + 1
        grid.Add(horizontal_line_5, (n, 0), wx.GBSpan(1, 4), flag=wx.EXPAND)
        n = n + 1
        grid.Add(btn_grid, (n, 0), wx.GBSpan(1, 4), flag=wx.ALIGN_LEFT | wx.EXPAND)

        # fit layout
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.ALIGN_CENTER_HORIZONTAL | wx.EXPAND, 5)
        main_sizer.Fit(panel)

        panel.SetSizerAndFit(main_sizer)

        return panel

    def on_update_info(self, **kwargs):
        """Update information labels"""
        document_title = kwargs.get('document_title', self.document_title)

        if document_title is None:
            document_title = 'N/A'

        self.document_info_text.SetLabel(document_title)
        self.Layout()

    def on_update_extraction_ranges(self, **kwargs):
        if not kwargs:
            kwargs = self.extraction_ranges

        mass_range = kwargs.get("mass_range", ["N/A", "N/A"])
        xvals_RT_mins = kwargs.get("xvals_RT_mins", ["N/A", "N/A"])
        xvals_RT_scans = kwargs.get("xvals_RT_scans", ["N/A", "N/A"])
        xvals_DT_ms = kwargs.get("xvals_DT_ms", ["N/A", "N/A"])
        xvals_DT_bins = kwargs.get("xvals_DT_bins", ["N/A", "N/A"])

        try:
            info = \
                f"m/z (Da): {mass_range[0]:.2f}-{mass_range[1]:.2f}\n" + \
                f"RT (scans): {xvals_RT_scans[0]:d}-{xvals_RT_scans[1]:d} | " + \
                f"RT (mins): {xvals_RT_mins[0]:.2f}-{xvals_RT_mins[1]:.2f}\n" + \
                f"DT (bins): {xvals_DT_bins[0]:d}-{xvals_DT_bins[1]:d} | " + \
                f"DT (ms): {xvals_DT_ms[0]:.2f}-{xvals_DT_ms[1]:.2f}"
        except ValueError:
            info = "N/A"
        self.extraction_info_text.SetLabel(info)
        self.Layout()

    def on_extract(self, evt):
        """Extract data without adding it to the document"""

        self.data_handling.on_extract_data_from_user_input(
            self.document_title,
            scan_time=str2num(self.extract_scanTime_value.GetValue()),
            pusher_frequency=str2num(self.extract_pusherFreq_value.GetValue()))

    def on_add_to_document(self, evt):
        self.data_handling.on_extract_data_from_user_input(
            self.document_title,
            scan_time=str2num(self.extract_scanTime_value.GetValue()),
            pusher_frequency=str2num(self.extract_pusherFreq_value.GetValue()),
            add_to_document=True)

    def on_toggle_controls(self, evt):
        self.config.extract_massSpectra = self.extract_extractMS_check.GetValue()
        obj_list = [self.extract_extractMS_dt_check, self.extract_extractMS_rt_check, self.extract_extractMS_ms_check]
        for item in obj_list:
            item.Enable(enable=self.config.extract_massSpectra)

        self.config.extract_chromatograms = self.extract_extractRT_check.GetValue()
        obj_list = [self.extract_extractRT_dt_check, self.extract_extractRT_ms_check]
        for item in obj_list:
            item.Enable(enable=self.config.extract_chromatograms)

        self.config.extract_driftTime1D = self.extract_extractDT_check.GetValue()
        obj_list = [self.extract_extractDT_ms_check, self.extract_extractDT_rt_check]
        for item in obj_list:
            item.Enable(enable=self.config.extract_driftTime1D)

        self.config.extract_driftTime2D = self.extract_extract2D_check.GetValue()
        obj_list = [self.extract_extract2D_ms_check, self.extract_extract2D_rt_check]
        for item in obj_list:
            item.Enable(enable=self.config.extract_driftTime2D)

        self.config.extract_rt_use_scans = self.extract_rt_scans_check.GetValue()
        self.extract_scanTime_value.Enable(enable=self.config.extract_rt_use_scans)

        self.config.extract_dt_use_ms = self.extract_dt_ms_check.GetValue()
        self.extract_pusherFreq_value.Enable(enable=self.config.extract_dt_use_ms)

        if evt is not None:
            evt.Skip()

    def on_apply(self, evt):
        self.on_update_extraction_ranges()
        self.config.extract_mzStart = str2num(self.extract_mzStart_value.GetValue())
        self.config.extract_mzEnd = str2num(self.extract_mzEnd_value.GetValue())
        self.config.extract_rtStart = str2num(self.extract_rtStart_value.GetValue())
        self.config.extract_rtEnd = str2num(self.extract_rtEnd_value.GetValue())
        self.config.extract_dtStart = str2num(self.extract_dtStart_value.GetValue())
        self.config.extract_dtEnd = str2num(self.extract_dtEnd_value.GetValue())

        self.config.extract_massSpectra_use_mz = self.extract_extractMS_ms_check.GetValue()
        self.config.extract_massSpectra_use_rt = self.extract_extractMS_rt_check.GetValue()
        self.config.extract_massSpectra_use_dt = self.extract_extractMS_dt_check.GetValue()

        self.config.extract_chromatograms_use_mz = self.extract_extractRT_ms_check.GetValue()
        self.config.extract_chromatograms_use_dt = self.extract_extractRT_dt_check.GetValue()

        self.config.extract_driftTime1D_use_mz = self.extract_extractDT_ms_check.GetValue()
        self.config.extract_driftTime1D_use_rt = self.extract_extractDT_rt_check.GetValue()

        self.config.extract_driftTime2D_use_mz = self.extract_extract2D_ms_check.GetValue()
        self.config.extract_driftTime2D_use_rt = self.extract_extract2D_rt_check.GetValue()

        if evt is not None:
            evt.Skip()

    def on_click_on_setting(self, setting):
        """Change setting value based on keyboard event"""
#         if setting == 'interpolate':
#             self.config.plot2D_process_interpolate = not self.config.plot2D_process_interpolate
#             self.plot2D_process_interpolate.SetValue(self.config.plot2D_process_interpolate)
#         elif setting == 'smooth':
#             self.config.plot2D_process_smooth = not self.config.plot2D_process_smooth
#             self.plot2D_process_smooth.SetValue(self.config.plot2D_process_smooth)
#         elif setting == 'crop':
#             self.config.plot2D_process_crop = not self.config.plot2D_process_crop
#             self.plot2D_process_crop.SetValue(self.config.plot2D_process_crop)
#         elif setting == 'baseline':
#             self.config.plot2D_process_threshold = not self.config.plot2D_process_threshold
#             self.plot2D_process_threshold.SetValue(self.config.plot2D_process_threshold)
#         elif setting == 'normalize':
#             self.config.plot2D_normalize = not self.config.plot2D_normalize
#             self.plot2D_process_normalize.SetValue(self.config.plot2D_normalize)

        self.on_toggle_controls(None)

    def on_change_validator(self, evt):

        self.config.extract_rt_use_scans = self.extract_rt_scans_check.GetValue()
        if self.config.extract_rt_use_scans:
            self.rt_label.SetLabel('RT (scans):')
            self.extract_rtStart_value.SetValidator(validator('intPos'))
            self.extract_rtStart_value.SetValue(str(int(self.config.extract_rtStart)))
            self.extract_rtEnd_value.SetValidator(validator('intPos'))
            self.extract_rtEnd_value.SetValue(str(int(self.config.extract_rtEnd)))
        else:
            self.rt_label.SetLabel('RT (mins): ')
            self.extract_rtStart_value.SetValidator(validator('floatPos'))
            self.extract_rtEnd_value.SetValidator(validator('floatPos'))

        self.config.extract_dt_use_ms = self.extract_dt_ms_check.GetValue()
        if self.config.extract_dt_use_ms:
            self.dt_label.SetLabel('DT (ms):')
            self.extract_dtStart_value.SetValidator(validator('intPos'))
            self.extract_dtStart_value.SetValue(str(int(self.config.extract_dtStart)))
            self.extract_dtEnd_value.SetValidator(validator('intPos'))
            self.extract_dtEnd_value.SetValue(str(int(self.config.extract_dtEnd)))
        else:
            self.dt_label.SetLabel('DT (bins):')
            self.extract_dtStart_value.SetValidator(validator('floatPos'))
            self.extract_dtEnd_value.SetValidator(validator('floatPos'))

        self.Layout()

        if evt is not None:
            evt.Skip()
