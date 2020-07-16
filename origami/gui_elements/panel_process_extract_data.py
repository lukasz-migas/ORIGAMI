# Standard library imports
import logging

# Third-party imports
import wx
from pubsub import pub

# Local imports
from origami.styles import MiniFrame
from origami.styles import Validator
from origami.styles import make_checkbox
from origami.styles import make_spin_ctrl_double
from origami.config.config import CONFIG
from origami.utils.converters import str2num
from origami.utils.exceptions import MessageError

logger = logging.getLogger(__name__)

# TODO: Should have a temporary data storage and check whether data was previously extracted


class PanelProcessExtractData(MiniFrame):
    """Extract data"""

    def __init__(self, parent, presenter, **kwargs):
        MiniFrame.__init__(self, parent, title="Extract data...", style=wx.DEFAULT_FRAME_STYLE & ~wx.RESIZE_BORDER)
        self.view = parent
        self.presenter = presenter

        # setup kwargs
        self.document = kwargs.pop("document", None)
        self.document_title = kwargs.pop("document_title", None)
        self.parameters = dict()
        self.extraction_ranges = dict()
        self.extraction_data = dict()

        if self.document is not None:
            self.parameters = self.document.parameters
            try:
                self.extraction_ranges = self.data_handling._get_waters_extraction_ranges(self.document)
            except (TypeError, ValueError, IndexError):
                logger.warning("Could not determine extraction ranges")

        self.disable_plot = kwargs.get("disable_plot", False)
        self.disable_process = kwargs.get("disable_process", False)
        #         self.process_all = kwargs.get("process_all", False)

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

        # subscribe to event
        pub.subscribe(self.on_add_data_to_storage, "extract.data.user")

    @property
    def data_handling(self):
        """Return handle to `data_handling`"""
        return self.presenter.data_handling

    @property
    def data_processing(self):
        """Return handle to `data_processing`"""
        return self.presenter.data_processing

    @property
    def document_tree(self):
        """Return handle to `document_tree`"""
        return self.presenter.view.panelDocuments.documents

    @property
    def panel_plot(self):
        """Return handle to `panel_plot`"""
        return self.presenter.view.panelPlots

    def on_close(self, evt):

        n_extracted_items = len(self.extraction_data)
        if n_extracted_items > 0:
            from origami.gui_elements.misc_dialogs import DialogBox

            msg = (
                f"Found {n_extracted_items} extracted item(s) in the clipboard. Closing this window will lose"
                + " this data. Would you like to continue?"
            )
            dlg = DialogBox(title="Clipboard is not empty", msg=msg, kind="Question")
            if dlg == wx.ID_NO:
                msg = "Action was cancelled"
                return

        # unsubscribe from events
        pub.unsubscribe(self.on_add_data_to_storage, "extract.data.user")

        self.Destroy()

    def on_key_event(self, evt):
        """Trigger event based on keyboard input"""
        key_code = evt.GetKeyCode()
        if key_code == wx.WXK_ESCAPE:  # key = esc
            self.on_close(None)
        elif key_code == 69:
            logger.info("Extracting data")
            self.on_extract(None)
        elif key_code == 65:
            logger.info("Extracting and adding data to document")
            self.on_add_to_document(None)

        if evt is not None:
            evt.Skip()

    def make_panel(self):
        """Make settings panel"""
        panel = wx.Panel(self, -1, size=(-1, -1))

        document_info_text = wx.StaticText(panel, -1, "Document:")
        self.document_info_text = wx.StaticText(panel, -1, "")

        extraction_info_text = wx.StaticText(panel, -1, "Extraction \nranges:")
        self.extraction_info_text = wx.StaticText(panel, -1, "\n\n\n\n")

        start_label = wx.StaticText(panel, wx.ID_ANY, "Min:")
        end_label = wx.StaticText(panel, wx.ID_ANY, "Max:")

        mass_range = self.extraction_ranges.get("mass_range", [0, 99999])
        self.mz_label = wx.StaticText(panel, wx.ID_ANY, "m/z (Da):")
        self.extract_mzStart_value = make_spin_ctrl_double(
            panel, CONFIG.extract_mzStart, mass_range[0], mass_range[1], 100
        )
        self.extract_mzStart_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        self.extract_mzEnd_value = make_spin_ctrl_double(panel, CONFIG.extract_mzEnd, mass_range[0], mass_range[1], 100)
        self.extract_mzEnd_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        self.rt_label = wx.StaticText(panel, wx.ID_ANY, "RT (min): ")
        self.extract_rtStart_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("floatPos"))
        self.extract_rtStart_value.SetValue(str(CONFIG.extract_rtStart))
        self.extract_rtStart_value.Bind(wx.EVT_TEXT, self.on_apply)

        self.extract_rtEnd_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("floatPos"))
        self.extract_rtEnd_value.SetValue(str(CONFIG.extract_rtEnd))
        self.extract_rtEnd_value.Bind(wx.EVT_TEXT, self.on_apply)

        self.extract_rt_scans_check = make_checkbox(panel, "In scans")
        self.extract_rt_scans_check.SetValue(CONFIG.extract_rt_use_scans)
        self.extract_rt_scans_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.extract_rt_scans_check.Bind(wx.EVT_CHECKBOX, self.on_change_validator)
        self.extract_rt_scans_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        scanTime_label = wx.StaticText(panel, wx.ID_ANY, "Scan time (s):")
        self.extract_scanTime_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("floatPos"))
        self.extract_scanTime_value.SetValue(str(self.parameters.get("scanTime", 1)))
        self.extract_scanTime_value.Bind(wx.EVT_TEXT, self.on_apply)

        self.dt_label = wx.StaticText(panel, wx.ID_ANY, "DT (bins):")
        self.extract_dtStart_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("floatPos"))
        self.extract_dtStart_value.SetValue(str(CONFIG.extract_dtStart))
        self.extract_dtStart_value.Bind(wx.EVT_TEXT, self.on_apply)

        self.extract_dtEnd_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("floatPos"))
        self.extract_dtEnd_value.SetValue(str(CONFIG.extract_dtEnd))
        self.extract_dtEnd_value.Bind(wx.EVT_TEXT, self.on_apply)

        self.extract_dt_ms_check = make_checkbox(panel, "In ms")
        self.extract_dt_ms_check.SetValue(CONFIG.extract_dt_use_ms)
        self.extract_dt_ms_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.extract_dt_ms_check.Bind(wx.EVT_CHECKBOX, self.on_change_validator)
        self.extract_dt_ms_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        pusherFreq_label = wx.StaticText(panel, wx.ID_ANY, "Pusher frequency (ms):")
        self.extract_pusherFreq_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("floatPos"))
        self.extract_pusherFreq_value.SetValue(str(self.parameters.get("pusherFreq", 1)))
        self.extract_pusherFreq_value.Bind(wx.EVT_TEXT, self.on_apply)

        self.extract_extractMS_check = make_checkbox(panel, "Extract mass spectrum")
        self.extract_extractMS_check.SetValue(CONFIG.extract_massSpectra)
        self.extract_extractMS_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.extract_extractMS_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        self.extract_extractMS_ms_check = make_checkbox(panel, "m/z")
        self.extract_extractMS_ms_check.SetValue(False)
        self.extract_extractMS_ms_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.extract_extractMS_rt_check = make_checkbox(panel, "RT")
        self.extract_extractMS_rt_check.SetValue(True)
        self.extract_extractMS_rt_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.extract_extractMS_dt_check = make_checkbox(panel, "DT")
        self.extract_extractMS_dt_check.SetValue(True)
        self.extract_extractMS_dt_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.extract_extractRT_check = make_checkbox(panel, "Extract chromatogram")
        self.extract_extractRT_check.SetValue(CONFIG.extract_chromatograms)
        self.extract_extractRT_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.extract_extractRT_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        self.extract_extractRT_ms_check = make_checkbox(panel, "m/z")
        self.extract_extractRT_ms_check.SetValue(True)
        self.extract_extractRT_ms_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.extract_extractRT_dt_check = make_checkbox(panel, "DT")
        self.extract_extractRT_dt_check.SetValue(True)
        self.extract_extractRT_dt_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.extract_extractDT_check = make_checkbox(panel, "Extract mobilogram")
        self.extract_extractDT_check.SetValue(CONFIG.extract_driftTime1D)
        self.extract_extractDT_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.extract_extractDT_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        self.extract_extractDT_ms_check = make_checkbox(panel, "m/z")
        self.extract_extractDT_ms_check.SetValue(True)
        self.extract_extractDT_ms_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.extract_extractDT_rt_check = make_checkbox(panel, "RT")
        self.extract_extractDT_rt_check.SetValue(True)
        self.extract_extractDT_rt_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.extract_extract2D_check = make_checkbox(panel, "Extract heatmap")
        self.extract_extract2D_check.SetValue(CONFIG.extract_driftTime2D)
        self.extract_extract2D_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.extract_extract2D_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        self.extract_extract2D_ms_check = make_checkbox(panel, "m/z")
        self.extract_extract2D_ms_check.SetValue(True)
        self.extract_extract2D_ms_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.extract_extract2D_rt_check = make_checkbox(panel, "RT")
        self.extract_extract2D_rt_check.SetValue(True)
        self.extract_extract2D_rt_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        if not self.disable_plot:
            self.extract_btn = wx.Button(panel, wx.ID_OK, "Extract", size=(120, 22))
            self.extract_btn.Bind(wx.EVT_BUTTON, self.on_extract)

        if not self.disable_process:
            self.add_to_document_btn = wx.Button(panel, wx.ID_OK, "Add to document", size=(120, 22))
            self.add_to_document_btn.Bind(wx.EVT_BUTTON, self.on_add_to_document)

        self.cancel_btn = wx.Button(panel, wx.ID_OK, "Cancel", size=(120, 22))
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_close)

        btn_grid = wx.GridBagSizer(2, 2)
        n = 0
        if not self.disable_plot:
            btn_grid.Add(self.extract_btn, (n, 1), flag=wx.EXPAND)
        if not self.disable_process:
            btn_grid.Add(self.add_to_document_btn, (n, 2), flag=wx.EXPAND)
        btn_grid.Add(self.cancel_btn, (n, 3), flag=wx.EXPAND)

        ms_grid = wx.GridBagSizer(2, 2)
        ms_grid.Add(self.extract_extractMS_ms_check, (n, 0), flag=wx.ALIGN_LEFT)
        ms_grid.Add(self.extract_extractMS_rt_check, (n, 1), flag=wx.ALIGN_LEFT)
        ms_grid.Add(self.extract_extractMS_dt_check, (n, 2), flag=wx.ALIGN_LEFT)

        rt_grid = wx.GridBagSizer(2, 2)
        rt_grid.Add(self.extract_extractRT_ms_check, (n, 1), flag=wx.ALIGN_LEFT)
        rt_grid.Add(self.extract_extractRT_dt_check, (n, 2), flag=wx.ALIGN_LEFT)

        dt_grid = wx.GridBagSizer(2, 2)
        dt_grid.Add(self.extract_extractDT_ms_check, (n, 1), flag=wx.ALIGN_LEFT)
        dt_grid.Add(self.extract_extractDT_rt_check, (n, 2), flag=wx.ALIGN_LEFT)

        heatmap_grid = wx.GridBagSizer(2, 2)
        heatmap_grid.Add(self.extract_extract2D_ms_check, (n, 1), flag=wx.ALIGN_LEFT)
        heatmap_grid.Add(self.extract_extract2D_rt_check, (n, 2), flag=wx.ALIGN_LEFT)

        horizontal_line_0 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_1 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_2 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_3 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_4 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_5 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(document_info_text, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.EXPAND)
        grid.Add(self.document_info_text, (n, 1), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(extraction_info_text, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.extraction_info_text, (n, 1), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(horizontal_line_0, (n, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
        n += 1
        grid.Add(start_label, (n, 1), flag=wx.ALIGN_CENTER)
        grid.Add(end_label, (n, 2), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(self.mz_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.EXPAND)
        grid.Add(self.extract_mzStart_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.extract_mzEnd_value, (n, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(self.rt_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.EXPAND)
        grid.Add(self.extract_rtStart_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.extract_rtEnd_value, (n, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(scanTime_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.EXPAND)
        grid.Add(self.extract_scanTime_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.extract_rt_scans_check, (n, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(self.dt_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.EXPAND)
        grid.Add(self.extract_dtStart_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.extract_dtEnd_value, (n, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(pusherFreq_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.EXPAND)
        grid.Add(self.extract_pusherFreq_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.extract_dt_ms_check, (n, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(horizontal_line_1, (n, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
        n += 1
        grid.Add(self.extract_extractMS_check, (n, 0), flag=wx.ALIGN_LEFT | wx.EXPAND)
        grid.Add(ms_grid, (n, 1), flag=wx.ALIGN_LEFT)
        n += 1
        grid.Add(horizontal_line_2, (n, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
        n += 1
        grid.Add(self.extract_extractRT_check, (n, 0), flag=wx.ALIGN_LEFT | wx.EXPAND)
        grid.Add(rt_grid, (n, 1), flag=wx.ALIGN_LEFT)
        n += 1
        grid.Add(horizontal_line_3, (n, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
        n += 1
        grid.Add(self.extract_extractDT_check, (n, 0), flag=wx.ALIGN_LEFT | wx.EXPAND)
        grid.Add(dt_grid, (n, 1), flag=wx.ALIGN_LEFT | wx.EXPAND)
        n += 1
        grid.Add(horizontal_line_4, (n, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
        n += 1
        grid.Add(self.extract_extract2D_check, (n, 0), flag=wx.ALIGN_LEFT | wx.EXPAND)
        grid.Add(heatmap_grid, (n, 1), flag=wx.ALIGN_LEFT | wx.EXPAND)
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

        if document_title is None:
            document_title = "N/A"

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
            info = (
                f"m/z (Da): {mass_range[0]:.2f}-{mass_range[1]:.2f}\n"
                + f"RT (scans): {xvals_RT_scans[0]:d}-{xvals_RT_scans[1]:d} \n"
                + f"RT (mins): {xvals_RT_mins[0]:.2f}-{xvals_RT_mins[1]:.2f}\n"
                + f"DT (bins): {xvals_DT_bins[0]:d}-{xvals_DT_bins[1]:d} \n"
                + f"DT (ms): {xvals_DT_ms[0]:.2f}-{xvals_DT_ms[1]:.2f}"
            )
        except ValueError:
            info = "N/A"
        self.extraction_info_text.SetLabel(info)
        self.Layout()

    def on_add_data_to_storage(self, data):
        """Add data to document"""
        for title, dataset in data.items():
            self.extraction_data[title] = dataset
        logger.info("Updated clipboard")

    def on_extract(self, evt, **kwargs):
        """Extract data without adding it to the document"""
        self.on_check_user_input()
        self.data_handling.on_extract_data_from_user_input_fcn(
            self.document_title,
            scan_time=str2num(self.extract_scanTime_value.GetValue()),
            pusher_frequency=str2num(self.extract_pusherFreq_value.GetValue()),
            return_data=True,
            **kwargs,
        )

    def generate_extraction_list(self):

        item_list = []
        for key, dataset in self.extraction_data.items():
            item_list.append([dataset["type"], key])

        return item_list

    def on_add_to_document(self, evt):
        """Add data to document. Ask users what data should be added"""
        from origami.gui_elements.dialog_review_editor import DialogReviewEditorExtract

        # if the list is empty, notify the user
        if not self.extraction_data:
            raise MessageError(
                "Clipboard is empty",
                "There are no items in the clipboard." + " Please extract data before adding it to the document",
            )

        # get document
        document = self.data_handling.on_get_document(self.document_title)
        if document is None:
            raise MessageError("Missing document", f"Could not find {self.document_title}. Was it deleted?")

        # collect list of items in the clipboard
        item_list = self.generate_extraction_list()
        dlg = DialogReviewEditorExtract(self, item_list)
        dlg.ShowModal()
        add_to_document_list = dlg.output_list

        # add data to document while also removing it from the clipboard object
        for key in add_to_document_list:
            dataset = self.extraction_data.pop(key)
            self.document_tree.on_update_data(
                dataset["data"], dataset["name"], document, data_type=dataset["data_type"]
            )
            logger.info(f"Added {dataset['name']} to {self.document_title}")

    def on_toggle_controls(self, evt):
        CONFIG.extract_massSpectra = self.extract_extractMS_check.GetValue()
        obj_list = [self.extract_extractMS_dt_check, self.extract_extractMS_rt_check, self.extract_extractMS_ms_check]
        for item in obj_list:
            item.Enable(enable=CONFIG.extract_massSpectra)

        CONFIG.extract_chromatograms = self.extract_extractRT_check.GetValue()
        obj_list = [self.extract_extractRT_dt_check, self.extract_extractRT_ms_check]
        for item in obj_list:
            item.Enable(enable=CONFIG.extract_chromatograms)

        CONFIG.extract_driftTime1D = self.extract_extractDT_check.GetValue()
        obj_list = [self.extract_extractDT_ms_check, self.extract_extractDT_rt_check]
        for item in obj_list:
            item.Enable(enable=CONFIG.extract_driftTime1D)

        CONFIG.extract_driftTime2D = self.extract_extract2D_check.GetValue()
        obj_list = [self.extract_extract2D_ms_check, self.extract_extract2D_rt_check]
        for item in obj_list:
            item.Enable(enable=CONFIG.extract_driftTime2D)

        CONFIG.extract_rt_use_scans = self.extract_rt_scans_check.GetValue()
        self.extract_scanTime_value.Enable(enable=CONFIG.extract_rt_use_scans)

        CONFIG.extract_dt_use_ms = self.extract_dt_ms_check.GetValue()
        self.extract_pusherFreq_value.Enable(enable=CONFIG.extract_dt_use_ms)

        if evt is not None:
            evt.Skip()

    def on_apply(self, evt):
        self.on_update_extraction_ranges()
        CONFIG.extract_mzStart = str2num(self.extract_mzStart_value.GetValue())
        CONFIG.extract_mzEnd = str2num(self.extract_mzEnd_value.GetValue())
        CONFIG.extract_rtStart = str2num(self.extract_rtStart_value.GetValue())
        CONFIG.extract_rtEnd = str2num(self.extract_rtEnd_value.GetValue())
        CONFIG.extract_dtStart = str2num(self.extract_dtStart_value.GetValue())
        CONFIG.extract_dtEnd = str2num(self.extract_dtEnd_value.GetValue())

        CONFIG.extract_massSpectra_use_mz = self.extract_extractMS_ms_check.GetValue()
        CONFIG.extract_massSpectra_use_rt = self.extract_extractMS_rt_check.GetValue()
        CONFIG.extract_massSpectra_use_dt = self.extract_extractMS_dt_check.GetValue()

        CONFIG.extract_chromatograms_use_mz = self.extract_extractRT_ms_check.GetValue()
        CONFIG.extract_chromatograms_use_dt = self.extract_extractRT_dt_check.GetValue()

        CONFIG.extract_driftTime1D_use_mz = self.extract_extractDT_ms_check.GetValue()
        CONFIG.extract_driftTime1D_use_rt = self.extract_extractDT_rt_check.GetValue()

        CONFIG.extract_driftTime2D_use_mz = self.extract_extract2D_ms_check.GetValue()
        CONFIG.extract_driftTime2D_use_rt = self.extract_extract2D_rt_check.GetValue()

        if evt is not None:
            evt.Skip()

    def on_change_validator(self, evt):

        CONFIG.extract_rt_use_scans = self.extract_rt_scans_check.GetValue()
        if CONFIG.extract_rt_use_scans:
            self.rt_label.SetLabel("RT (scans):")
            self.extract_rtStart_value.SetValidator(Validator("intPos"))
            self.extract_rtStart_value.SetValue(str(int(CONFIG.extract_rtStart)))
            self.extract_rtEnd_value.SetValidator(Validator("intPos"))
            self.extract_rtEnd_value.SetValue(str(int(CONFIG.extract_rtEnd)))
        else:
            self.rt_label.SetLabel("RT (mins): ")
            self.extract_rtStart_value.SetValidator(Validator("floatPos"))
            self.extract_rtEnd_value.SetValidator(Validator("floatPos"))

        CONFIG.extract_dt_use_ms = self.extract_dt_ms_check.GetValue()
        if CONFIG.extract_dt_use_ms:
            self.dt_label.SetLabel("DT (ms):")
            self.extract_dtStart_value.SetValidator(Validator("intPos"))
            self.extract_dtStart_value.SetValue(str(int(CONFIG.extract_dtStart)))
            self.extract_dtEnd_value.SetValidator(Validator("intPos"))
            self.extract_dtEnd_value.SetValue(str(int(CONFIG.extract_dtEnd)))
        else:
            self.dt_label.SetLabel("DT (bins):")
            self.extract_dtStart_value.SetValidator(Validator("floatPos"))
            self.extract_dtEnd_value.SetValidator(Validator("floatPos"))

        self.Layout()

        if evt is not None:
            evt.Skip()

    def on_check_user_input(self):
        if self.extraction_ranges:
            # check mass range
            mass_range = self.extraction_ranges.get("mass_range")
            if CONFIG.extract_mzStart < mass_range[0]:
                CONFIG.extract_mzStart = mass_range[0]
                self.extract_mzStart_value.SetValue(f"{CONFIG.extract_mzStart}")
            if CONFIG.extract_mzEnd > mass_range[1]:
                CONFIG.extract_mzEnd = mass_range[1]
                self.extract_mzEnd_value.SetValue(f"{CONFIG.extract_mzEnd}")

            # check chromatographic range
            if CONFIG.extract_rt_use_scans:
                rt_range = self.extraction_ranges.get("xvals_RT_scans")
            else:
                rt_range = self.extraction_ranges.get("xvals_RT_mins")

            if CONFIG.extract_rtStart < rt_range[0]:
                CONFIG.extract_rtStart = rt_range[0]
                self.extract_rtStart_value.SetValue(f"{CONFIG.extract_rtStart}")
            if CONFIG.extract_rtStart > rt_range[1]:
                CONFIG.extract_rtStart = rt_range[1]
                self.extract_rtStart_value.SetValue(f"{CONFIG.extract_rtStart}")
            if CONFIG.extract_rtEnd < rt_range[0]:
                CONFIG.extract_rtEnd = rt_range[0]
                self.extract_rtEnd_value.SetValue(f"{CONFIG.extract_rtEnd}")
            if CONFIG.extract_rtEnd > rt_range[1]:
                CONFIG.extract_rtEnd = rt_range[1]
                self.extract_rtEnd_value.SetValue(f"{CONFIG.extract_rtEnd}")

            # check mobility range
            if CONFIG.extract_dt_use_ms:
                dt_range = self.extraction_ranges.get("xvals_DT_ms")
            else:
                dt_range = self.extraction_ranges.get("xvals_DT_bins")

            if CONFIG.extract_dtStart < dt_range[0]:
                CONFIG.extract_dtStart = dt_range[0]
                self.extract_dtStart_value.SetValue(f"{CONFIG.extract_dtStart}")
            if CONFIG.extract_dtStart > dt_range[1]:
                CONFIG.extract_dtStart = dt_range[1]
                self.extract_dtStart_value.SetValue(f"{CONFIG.extract_dtStart}")
            if CONFIG.extract_dtEnd < dt_range[0]:
                CONFIG.extract_dtEnd = dt_range[0]
                self.extract_dtEnd_value.SetValue(f"{CONFIG.extract_dtEnd}")
            if CONFIG.extract_dtEnd > dt_range[1]:
                CONFIG.extract_dtEnd = dt_range[1]
                self.extract_dtEnd_value.SetValue(f"{CONFIG.extract_dtEnd}")
