# Standard library imports
import logging

# Third-party imports
import wx
from pubsub import pub

# Local imports
from origami.styles import MiniFrame
from origami.styles import Validator
from origami.icons.assets import Icons
from origami.config.config import CONFIG
from origami.utils.converters import str2num
from origami.utils.exceptions import MessageError
from origami.gui_elements.helpers import make_checkbox
from origami.gui_elements.helpers import make_spin_ctrl_double

logger = logging.getLogger(__name__)

# TODO: Should have a temporary data storage and check whether data was previously extracted


class PanelProcessExtractData(MiniFrame):
    """Extract data"""

    # ui elements
    extract_mzStart_value, extract_mzEnd_value, extract_rt_start_value = None, None, None
    extract_rt_end_value, extract_dt_start_value, extract_dt_end_value = None, None, None
    extract_extract_ms_ms_check, extract_extract_ms_rt_check, extract_extract_ms_dt_check = None, None, None
    extract_extract_rt_ms_check, extract_extract_rt_dt_check, extract_extract_dt_ms_check = None, None, None
    extract_extract_dt_rt_check, extract_extract_heatmap_ms_check, extract_extract_heatmap_rt_check = None, None, None
    extract_extract_ms_check, extract_extract_rt_check, extract_pusher_freq_value = None, None, None
    dt_label, extract_scan_time_value, document_info_text = None, None, None
    extraction_info_text, mz_label, extract_dt_ms_check = None, None, None
    extract_extract_heatmap_check, extract_btn, add_to_document_btn = None, None, None
    cancel_btn, rt_label, extract_rt_scans_check, extract_extract_dt_check = None, None, None, None

    def __init__(
        self, parent, presenter, document_title: str = None, disable_plot: bool = False, disable_process: bool = False
    ):
        MiniFrame.__init__(self, parent, title="Extract data...", style=wx.DEFAULT_FRAME_STYLE & ~wx.RESIZE_BORDER)
        self.view = parent
        self.presenter = presenter
        self._icons = Icons()

        # setup kwargs
        self.document_title = document_title
        self.parameters = dict()
        self.extraction_ranges = dict()
        self.extraction_data = dict()

        # if self.document is not None:
        #     self.parameters = self.document.parameters
        #     try:
        #         self.extraction_ranges = self.data_handling._get_waters_extraction_ranges(self.document)
        #     except (TypeError, ValueError, IndexError):
        #         logger.warning("Could not determine extraction ranges")

        self.disable_plot = disable_plot
        self.disable_process = disable_process

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

    def on_close(self, evt, force: bool = False):
        """Close window"""
        n_extracted_items = len(self.extraction_data)
        if n_extracted_items > 0:
            # Local imports
            from origami.gui_elements.misc_dialogs import DialogBox

            msg = (
                f"Found {n_extracted_items} extracted item(s) in the clipboard. Closing this window will lose"
                + " this data. Would you like to continue?"
            )
            dlg = DialogBox(title="Clipboard is not empty", msg=msg, kind="Question")
            if dlg == wx.ID_NO:
                logger.warning("Action was cancelled")
                return

        # unsubscribe from events
        pub.unsubscribe(self.on_add_data_to_storage, "extract.data.user")
        super(PanelProcessExtractData, self).on_close(evt, force)

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

        extraction_info_text = wx.StaticText(panel, -1, "Extraction ranges:")
        self.extraction_info_text = wx.StaticText(panel, -1, "\n\n\n\n")

        start_label = wx.StaticText(panel, wx.ID_ANY, "Min:")
        end_label = wx.StaticText(panel, wx.ID_ANY, "Max:")

        mass_range = self.extraction_ranges.get("mass_range", [0, 99999])
        self.mz_label = wx.StaticText(panel, wx.ID_ANY, "m/z (Da):")
        self.extract_mzStart_value = make_spin_ctrl_double(
            panel, CONFIG.extract_mz_start, mass_range[0], mass_range[1], 100
        )
        self.extract_mzStart_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        self.extract_mzEnd_value = make_spin_ctrl_double(
            panel, CONFIG.extract_mz_end, mass_range[0], mass_range[1], 100
        )
        self.extract_mzEnd_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        self.rt_label = wx.StaticText(panel, wx.ID_ANY, "RT (min): ")
        self.extract_rt_start_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("floatPos"))
        self.extract_rt_start_value.SetValue(str(CONFIG.extract_rt_start))
        self.extract_rt_start_value.Bind(wx.EVT_TEXT, self.on_apply)

        self.extract_rt_end_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("floatPos"))
        self.extract_rt_end_value.SetValue(str(CONFIG.extract_rt_end))
        self.extract_rt_end_value.Bind(wx.EVT_TEXT, self.on_apply)

        self.extract_rt_scans_check = make_checkbox(panel, "In scans")
        self.extract_rt_scans_check.SetValue(CONFIG.extract_rt_use_scans)
        self.extract_rt_scans_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.extract_rt_scans_check.Bind(wx.EVT_CHECKBOX, self.on_change_validator)
        self.extract_rt_scans_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        scan_time_label = wx.StaticText(panel, wx.ID_ANY, "Scan time (s):")
        self.extract_scan_time_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("floatPos"))
        self.extract_scan_time_value.SetValue(str(self.parameters.get("scanTime", 1)))
        self.extract_scan_time_value.Bind(wx.EVT_TEXT, self.on_apply)

        self.dt_label = wx.StaticText(panel, wx.ID_ANY, "DT (bins):")
        self.extract_dt_start_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("floatPos"))
        self.extract_dt_start_value.SetValue(str(CONFIG.extract_dt_start))
        self.extract_dt_start_value.Bind(wx.EVT_TEXT, self.on_apply)

        self.extract_dt_end_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("floatPos"))
        self.extract_dt_end_value.SetValue(str(CONFIG.extract_dt_end))
        self.extract_dt_end_value.Bind(wx.EVT_TEXT, self.on_apply)

        self.extract_dt_ms_check = make_checkbox(panel, "In ms")
        self.extract_dt_ms_check.SetValue(CONFIG.extract_dt_use_ms)
        self.extract_dt_ms_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.extract_dt_ms_check.Bind(wx.EVT_CHECKBOX, self.on_change_validator)
        self.extract_dt_ms_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        pusher_freq_label = wx.StaticText(panel, wx.ID_ANY, "Pusher frequency (ms):")
        self.extract_pusher_freq_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("floatPos"))
        self.extract_pusher_freq_value.SetValue(str(self.parameters.get("pusherFreq", 1)))
        self.extract_pusher_freq_value.Bind(wx.EVT_TEXT, self.on_apply)

        self.extract_extract_ms_check = make_checkbox(panel, "")
        self.extract_extract_ms_check.SetValue(CONFIG.extract_mz)
        self.extract_extract_ms_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.extract_extract_ms_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        self.extract_extract_ms_ms_check = make_checkbox(panel, "m/z")
        self.extract_extract_ms_ms_check.SetValue(False)
        self.extract_extract_ms_ms_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.extract_extract_ms_rt_check = make_checkbox(panel, "RT")
        self.extract_extract_ms_rt_check.SetValue(True)
        self.extract_extract_ms_rt_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.extract_extract_ms_dt_check = make_checkbox(panel, "DT")
        self.extract_extract_ms_dt_check.SetValue(True)
        self.extract_extract_ms_dt_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.extract_extract_rt_check = make_checkbox(panel, "")
        self.extract_extract_rt_check.SetValue(CONFIG.extract_rt)
        self.extract_extract_rt_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.extract_extract_rt_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        self.extract_extract_rt_ms_check = make_checkbox(panel, "m/z")
        self.extract_extract_rt_ms_check.SetValue(True)
        self.extract_extract_rt_ms_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.extract_extract_rt_dt_check = make_checkbox(panel, "DT")
        self.extract_extract_rt_dt_check.SetValue(True)
        self.extract_extract_rt_dt_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.extract_extract_dt_check = make_checkbox(panel, "")
        self.extract_extract_dt_check.SetValue(CONFIG.extract_dt)
        self.extract_extract_dt_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.extract_extract_dt_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        self.extract_extract_dt_ms_check = make_checkbox(panel, "m/z")
        self.extract_extract_dt_ms_check.SetValue(True)
        self.extract_extract_dt_ms_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.extract_extract_dt_rt_check = make_checkbox(panel, "RT")
        self.extract_extract_dt_rt_check.SetValue(True)
        self.extract_extract_dt_rt_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.extract_extract_heatmap_check = make_checkbox(panel, "")
        self.extract_extract_heatmap_check.SetValue(CONFIG.extract_heatmap)
        self.extract_extract_heatmap_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.extract_extract_heatmap_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        self.extract_extract_heatmap_ms_check = make_checkbox(panel, "m/z")
        self.extract_extract_heatmap_ms_check.SetValue(True)
        self.extract_extract_heatmap_ms_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.extract_extract_heatmap_rt_check = make_checkbox(panel, "RT")
        self.extract_extract_heatmap_rt_check.SetValue(True)
        self.extract_extract_heatmap_rt_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        if not self.disable_plot:
            self.extract_btn = wx.Button(panel, wx.ID_OK, "Extract", size=(120, 22))
            self.extract_btn.Bind(wx.EVT_BUTTON, self.on_extract)
            btn_sizer.Add(self.extract_btn)
        if not self.disable_process:
            self.add_to_document_btn = wx.Button(panel, wx.ID_OK, "Add to document", size=(120, 22))
            self.add_to_document_btn.Bind(wx.EVT_BUTTON, self.on_add_to_document)
            btn_sizer.Add(self.add_to_document_btn)

        self.cancel_btn = wx.Button(panel, wx.ID_OK, "Cancel", size=(120, 22))
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_close)
        btn_sizer.Add(self.cancel_btn)

        ms_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ms_sizer.Add(self.extract_extract_ms_ms_check)
        ms_sizer.Add(self.extract_extract_ms_rt_check)
        ms_sizer.Add(self.extract_extract_ms_dt_check)

        rt_sizer = wx.BoxSizer(wx.HORIZONTAL)
        rt_sizer.Add(self.extract_extract_rt_ms_check)
        rt_sizer.Add(self.extract_extract_rt_dt_check)

        dt_sizer = wx.BoxSizer(wx.HORIZONTAL)
        dt_sizer.Add(self.extract_extract_dt_ms_check)
        dt_sizer.Add(self.extract_extract_dt_rt_check)

        heatmap_sizer = wx.BoxSizer(wx.HORIZONTAL)
        heatmap_sizer.Add(self.extract_extract_heatmap_ms_check)
        heatmap_sizer.Add(self.extract_extract_heatmap_rt_check)

        statusbar_sizer = self.make_statusbar(panel, "right")

        n_span = 3
        n_col = 3
        grid = wx.GridBagSizer(2, 2)
        n = 0
        # document information
        grid.Add(document_info_text, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.document_info_text, (n, 1), wx.GBSpan(1, n_span), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(extraction_info_text, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.extraction_info_text, (n, 1), wx.GBSpan(1, n_span), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        # parameters
        grid.Add(start_label, (n, 1), flag=wx.ALIGN_CENTER)
        grid.Add(end_label, (n, 2), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(self.mz_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.EXPAND)
        grid.Add(self.extract_mzStart_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.extract_mzEnd_value, (n, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(self.rt_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.EXPAND)
        grid.Add(self.extract_rt_start_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.extract_rt_end_value, (n, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(scan_time_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.EXPAND)
        grid.Add(self.extract_scan_time_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.extract_rt_scans_check, (n, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(self.dt_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.EXPAND)
        grid.Add(self.extract_dt_start_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.extract_dt_end_value, (n, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(pusher_freq_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.EXPAND)
        grid.Add(self.extract_pusher_freq_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.extract_dt_ms_check, (n, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        # specify extraction
        grid.Add(wx.StaticText(panel, wx.ID_ANY, "Extract mass spectrum"), (n, 0), flag=wx.ALIGN_RIGHT)
        grid.Add(self.extract_extract_ms_check, (n, 1), flag=wx.ALIGN_LEFT | wx.EXPAND)
        n += 1
        grid.Add(ms_sizer, (n, 1), flag=wx.ALIGN_LEFT)
        n += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(wx.StaticText(panel, wx.ID_ANY, "Extract chromatogram"), (n, 0), flag=wx.ALIGN_RIGHT)
        grid.Add(self.extract_extract_rt_check, (n, 1), flag=wx.ALIGN_LEFT | wx.EXPAND)
        n += 1
        grid.Add(rt_sizer, (n, 1), flag=wx.ALIGN_LEFT)
        n += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(wx.StaticText(panel, wx.ID_ANY, "Extract mobilogram"), (n, 0), flag=wx.ALIGN_RIGHT)
        grid.Add(self.extract_extract_dt_check, (n, 1), flag=wx.ALIGN_LEFT | wx.EXPAND)
        n += 1
        grid.Add(dt_sizer, (n, 1), flag=wx.ALIGN_LEFT)
        n += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(wx.StaticText(panel, wx.ID_ANY, "Extract heatmap"), (n, 0), flag=wx.ALIGN_RIGHT)
        grid.Add(self.extract_extract_heatmap_check, (n, 1), flag=wx.ALIGN_LEFT | wx.EXPAND)
        n += 1
        grid.Add(heatmap_sizer, (n, 1), flag=wx.ALIGN_LEFT)
        n += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)

        # fit layout
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.EXPAND, 5)
        main_sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL, 5)
        main_sizer.Add(statusbar_sizer, 0, wx.EXPAND, 5)

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
        """Update extraction ranges"""
        if not kwargs:
            kwargs = self.extraction_ranges

        mass_range = kwargs.get("mass_range", ["N/A", "N/A"])
        xvals_rt_mins = kwargs.get("xvals_RT_mins", ["N/A", "N/A"])
        xvals_rt_scans = kwargs.get("xvals_RT_scans", ["N/A", "N/A"])
        xvals_dt_ms = kwargs.get("xvals_DT_ms", ["N/A", "N/A"])
        xvals_dt_bins = kwargs.get("xvals_DT_bins", ["N/A", "N/A"])

        try:
            info = (
                f"m/z (Da): {mass_range[0]:.2f}-{mass_range[1]:.2f}\n"
                + f"RT (scans): {xvals_rt_scans[0]:d}-{xvals_rt_scans[1]:d} \n"
                + f"RT (mins): {xvals_rt_mins[0]:.2f}-{xvals_rt_mins[1]:.2f}\n"
                + f"DT (bins): {xvals_dt_bins[0]:d}-{xvals_dt_bins[1]:d} \n"
                + f"DT (ms): {xvals_dt_ms[0]:.2f}-{xvals_dt_ms[1]:.2f}"
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

    def on_extract(self, _evt, **kwargs):
        """Extract data without adding it to the document"""
        self.on_check_user_input()
        self.data_handling.on_extract_data_from_user_input_fcn(
            self.document_title,
            scan_time=str2num(self.extract_scan_time_value.GetValue()),
            pusher_frequency=str2num(self.extract_pusher_freq_value.GetValue()),
            return_data=True,
            **kwargs,
        )

    def generate_extraction_list(self):
        """Generate extraction list"""
        item_list = []
        for key, dataset in self.extraction_data.items():
            item_list.append([dataset["type"], key])

        return item_list

    def on_add_to_document(self, _evt):
        """Add data to document. Ask users what data should be added"""
        # Local imports
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
        """Toggle controls"""
        CONFIG.extract_mz = self.extract_extract_ms_check.GetValue()
        self.extract_extract_ms_dt_check.Enable(CONFIG.extract_mz)
        self.extract_extract_ms_rt_check.Enable(CONFIG.extract_mz)
        self.extract_extract_ms_ms_check.Enable(CONFIG.extract_mz)

        CONFIG.extract_rt = self.extract_extract_rt_check.GetValue()
        self.extract_extract_rt_dt_check.Enable(CONFIG.extract_rt)
        self.extract_extract_rt_ms_check.Enable(CONFIG.extract_rt)

        CONFIG.extract_dt = self.extract_extract_dt_check.GetValue()
        self.extract_extract_dt_ms_check.Enable(enable=CONFIG.extract_dt)
        self.extract_extract_dt_rt_check.Enable(enable=CONFIG.extract_dt)

        CONFIG.extract_heatmap = self.extract_extract_heatmap_check.GetValue()
        self.extract_extract_heatmap_ms_check.Enable(enable=CONFIG.extract_heatmap)
        self.extract_extract_heatmap_rt_check.Enable(enable=CONFIG.extract_heatmap)

        CONFIG.extract_rt_use_scans = self.extract_rt_scans_check.GetValue()
        self.extract_scan_time_value.Enable(enable=CONFIG.extract_rt_use_scans)

        CONFIG.extract_dt_use_ms = self.extract_dt_ms_check.GetValue()
        self.extract_pusher_freq_value.Enable(enable=CONFIG.extract_dt_use_ms)

        if evt is not None:
            evt.Skip()

    def on_apply(self, evt):
        """Update configuration"""
        self.on_update_extraction_ranges()
        CONFIG.extract_mz_start = str2num(self.extract_mzStart_value.GetValue())
        CONFIG.extract_mz_end = str2num(self.extract_mzEnd_value.GetValue())
        CONFIG.extract_rt_start = str2num(self.extract_rt_start_value.GetValue())
        CONFIG.extract_rt_end = str2num(self.extract_rt_end_value.GetValue())
        CONFIG.extract_dt_start = str2num(self.extract_dt_start_value.GetValue())
        CONFIG.extract_dt_end = str2num(self.extract_dt_end_value.GetValue())

        CONFIG.extract_mz_use_mz = self.extract_extract_ms_ms_check.GetValue()
        CONFIG.extract_mz_use_rt = self.extract_extract_ms_rt_check.GetValue()
        CONFIG.extract_mz_use_dt = self.extract_extract_ms_dt_check.GetValue()

        CONFIG.extract_rt_use_mz = self.extract_extract_rt_ms_check.GetValue()
        CONFIG.extract_rt_use_dt = self.extract_extract_rt_dt_check.GetValue()

        CONFIG.extract_dt_use_mz = self.extract_extract_dt_ms_check.GetValue()
        CONFIG.extract_dt_use_rt = self.extract_extract_dt_rt_check.GetValue()

        CONFIG.extract_heatmap_use_mz = self.extract_extract_heatmap_ms_check.GetValue()
        CONFIG.extract_heatmap_use_rt = self.extract_extract_heatmap_rt_check.GetValue()

        if evt is not None:
            evt.Skip()

    def on_change_validator(self, evt):
        """Update validator"""
        CONFIG.extract_rt_use_scans = self.extract_rt_scans_check.GetValue()
        if CONFIG.extract_rt_use_scans:
            self.rt_label.SetLabel("RT (scans):")
            self.extract_rt_start_value.SetValidator(Validator("intPos"))
            self.extract_rt_start_value.SetValue(str(int(CONFIG.extract_rt_start)))
            self.extract_rt_end_value.SetValidator(Validator("intPos"))
            self.extract_rt_end_value.SetValue(str(int(CONFIG.extract_rt_end)))
        else:
            self.rt_label.SetLabel("RT (mins): ")
            self.extract_rt_start_value.SetValidator(Validator("floatPos"))
            self.extract_rt_end_value.SetValidator(Validator("floatPos"))

        CONFIG.extract_dt_use_ms = self.extract_dt_ms_check.GetValue()
        if CONFIG.extract_dt_use_ms:
            self.dt_label.SetLabel("DT (ms):")
            self.extract_dt_start_value.SetValidator(Validator("intPos"))
            self.extract_dt_start_value.SetValue(str(int(CONFIG.extract_dt_start)))
            self.extract_dt_end_value.SetValidator(Validator("intPos"))
            self.extract_dt_end_value.SetValue(str(int(CONFIG.extract_dt_end)))
        else:
            self.dt_label.SetLabel("DT (bins):")
            self.extract_dt_start_value.SetValidator(Validator("floatPos"))
            self.extract_dt_end_value.SetValidator(Validator("floatPos"))

        self.Layout()

        if evt is not None:
            evt.Skip()

    def on_check_user_input(self):
        """Validate user input"""
        if self.extraction_ranges:
            # check mass range
            mass_range = self.extraction_ranges.get("mass_range")
            if CONFIG.extract_mz_start < mass_range[0]:
                CONFIG.extract_mz_start = mass_range[0]
                self.extract_mzStart_value.SetValue(f"{CONFIG.extract_mz_start}")
            if CONFIG.extract_mz_end > mass_range[1]:
                CONFIG.extract_mz_end = mass_range[1]
                self.extract_mzEnd_value.SetValue(f"{CONFIG.extract_mz_end}")

            # check chromatographic range
            if CONFIG.extract_rt_use_scans:
                rt_range = self.extraction_ranges.get("xvals_RT_scans")
            else:
                rt_range = self.extraction_ranges.get("xvals_RT_mins")

            if CONFIG.extract_rt_start < rt_range[0]:
                CONFIG.extract_rt_start = rt_range[0]
                self.extract_rt_start_value.SetValue(f"{CONFIG.extract_rt_start}")
            if CONFIG.extract_rt_start > rt_range[1]:
                CONFIG.extract_rt_start = rt_range[1]
                self.extract_rt_start_value.SetValue(f"{CONFIG.extract_rt_start}")
            if CONFIG.extract_rt_end < rt_range[0]:
                CONFIG.extract_rt_end = rt_range[0]
                self.extract_rt_end_value.SetValue(f"{CONFIG.extract_rt_end}")
            if CONFIG.extract_rt_end > rt_range[1]:
                CONFIG.extract_rt_end = rt_range[1]
                self.extract_rt_end_value.SetValue(f"{CONFIG.extract_rt_end}")

            # check mobility range
            if CONFIG.extract_dt_use_ms:
                dt_range = self.extraction_ranges.get("xvals_DT_ms")
            else:
                dt_range = self.extraction_ranges.get("xvals_DT_bins")

            if CONFIG.extract_dt_start < dt_range[0]:
                CONFIG.extract_dt_start = dt_range[0]
                self.extract_dt_start_value.SetValue(f"{CONFIG.extract_dt_start}")
            if CONFIG.extract_dt_start > dt_range[1]:
                CONFIG.extract_dt_start = dt_range[1]
                self.extract_dt_start_value.SetValue(f"{CONFIG.extract_dt_start}")
            if CONFIG.extract_dt_end < dt_range[0]:
                CONFIG.extract_dt_end = dt_range[0]
                self.extract_dt_end_value.SetValue(f"{CONFIG.extract_dt_end}")
            if CONFIG.extract_dt_end > dt_range[1]:
                CONFIG.extract_dt_end = dt_range[1]
                self.extract_dt_end_value.SetValue(f"{CONFIG.extract_dt_end}")


def _main():
    # Local imports
    from origami.app import App

    app = App()
    ex = PanelProcessExtractData(None, None)
    ex.Show()
    app.MainLoop()


if __name__ == "__main__":
    _main()
