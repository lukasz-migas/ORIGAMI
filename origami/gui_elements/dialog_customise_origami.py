# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import numpy as np
import processing.origami_ms as pr_origami
import wx
from gui_elements.misc_dialogs import DialogBox
from styles import Dialog
from styles import validator
from utils.converters import str2int
from utils.converters import str2num
from utils.exceptions import MessageError
from utils.screen import calculate_window_size
from visuals import mpl_plots


class DialogCustomiseORIGAMI(Dialog):
    """Dialog to setup ORIGAMI-MS settings"""

    def __init__(self, parent, presenter, config, **kwargs):
        Dialog.__init__(self, parent, title="ORIGAMI-MS settings...")

        self.document_tree = parent
        self.presenter = presenter
        self.config = config

        self.panel_plot = self.presenter.view.panelPlots
        self.data_handling = self.document_tree.data_handling
        self.data_processing = self.document_tree.data_processing

        self.document_title = kwargs.get("document_title", None)
        if self.document_title is None:
            document = self.data_handling._on_get_document()
            if document is None:
                self.Destroy()
                raise MessageError(
                    "Please load a document",
                    "Could not find a document. Please load a document before trying this action again",
                )

            self.document_title = document.title

        self.SetTitle(f"ORIGAMI-MS settings: {self.document_title}")

        self.user_settings = self.on_setup_gui()
        self.user_settings_changed = False

        self._display_size = wx.GetDisplaySize()
        self._display_resolution = wx.ScreenDC().GetPPI()
        self._window_size = calculate_window_size(self._display_size, [0.5, 0.4])

        self.make_gui()
        self.on_toggle_controls(None)
        self.Layout()
        self.CentreOnScreen()
        self.SetFocus()

        # bind events
        wx.EVT_CLOSE(self, self.on_close)

    def on_setup_gui(self):
        document = self.data_handling._on_get_document(self.document_title)
        origami_settings = document.metadata.get("origami_ms", None)

        # there are no user specified settings yet, so we preset them with the global settings
        if origami_settings is None:
            origami_settings = {
                "origami_acquisition": self.config.origami_acquisition,
                "origami_startScan": self.config.origami_startScan,
                "origami_spv": self.config.origami_spv,
                "origami_startVoltage": self.config.origami_startVoltage,
                "origami_endVoltage": self.config.origami_endVoltage,
                "origami_stepVoltage": self.config.origami_stepVoltage,
                "origami_boltzmannOffset": self.config.origami_boltzmannOffset,
                "origami_exponentialPercentage": self.config.origami_exponentialPercentage,
                "origami_exponentialIncrement": self.config.origami_exponentialIncrement,
                "origami_cv_spv_list": [],
            }
            # update document with these global settings
            document.metadata["origami_ms"] = origami_settings
            self.data_handling.on_update_document(document, "no_refresh")

        return origami_settings

    def on_close(self, evt):
        """Destroy this frame."""

        if self.user_settings_changed:
            msg = (
                "You've made some changes to the ORIGAMI-MS settings but have not saved them.\n"
                + "Would you like to continue?"
            )
            dlg = DialogBox(exceptionTitle="Would you like to continue?", exceptionMsg=msg, type="Question")
            if dlg == wx.ID_NO:
                msg = "Action was cancelled"
                return

        self.Destroy()

    def on_ok(self, evt):
        self.on_apply_to_document(None)

    def make_gui(self):

        panel = wx.Panel(self, -1, size=(-1, -1), name="main")

        # make panel
        settings_panel = self.make_panel_settings(panel)
        self._settings_panel_size = settings_panel.GetSize()
        buttons_panel = self.make_buttons_panel(panel)

        plot_panel = self.make_plot_panel(panel)

        extraction_panel = self.make_spectrum_panel(panel)

        # pack element
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(settings_panel, 1, wx.EXPAND, 10)
        sizer.Add(extraction_panel, 1, wx.EXPAND, 10)
        sizer.Add(buttons_panel, 0, wx.EXPAND, 10)

        self.main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.main_sizer.Add(sizer, 0, wx.EXPAND, 10)
        self.main_sizer.Add(plot_panel, 1, wx.EXPAND, 10)

        # fit layout
        self.main_sizer.Fit(self)
        self.SetSizer(self.main_sizer)

    def make_panel_settings(self, split_panel):
        panel = wx.Panel(split_panel, -1, name="settings")

        acquisition_label = wx.StaticText(panel, wx.ID_ANY, "Acquisition method:")
        self.origami_method_choice = wx.Choice(
            panel, -1, choices=self.config.origami_acquisition_choices, size=(-1, -1)
        )
        self.origami_method_choice.SetStringSelection(self.user_settings["origami_acquisition"])
        self.origami_method_choice.Bind(wx.EVT_CHOICE, self.on_apply)
        self.origami_method_choice.Bind(wx.EVT_CHOICE, self.on_toggle_controls)

        spv_label = wx.StaticText(panel, wx.ID_ANY, "Scans per voltage:")
        self.origami_scansPerVoltage_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator("intPos"))
        self.origami_scansPerVoltage_value.SetValue(str(self.user_settings["origami_spv"]))
        self.origami_scansPerVoltage_value.Bind(wx.EVT_TEXT, self.on_apply)

        scan_label = wx.StaticText(panel, wx.ID_ANY, "First scan:")
        self.origami_startScan_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator("intPos"))
        self.origami_startScan_value.SetValue(str(self.user_settings["origami_startScan"]))
        self.origami_startScan_value.Bind(wx.EVT_TEXT, self.on_apply)

        startVoltage_label = wx.StaticText(panel, wx.ID_ANY, "First voltage:")
        self.origami_startVoltage_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator("floatPos"))
        self.origami_startVoltage_value.SetValue(str(self.user_settings["origami_startVoltage"]))
        self.origami_startVoltage_value.Bind(wx.EVT_TEXT, self.on_apply)

        endVoltage_label = wx.StaticText(panel, wx.ID_ANY, "Final voltage:")
        self.origami_endVoltage_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator("floatPos"))
        self.origami_endVoltage_value.SetValue(str(self.user_settings["origami_endVoltage"]))
        self.origami_endVoltage_value.Bind(wx.EVT_TEXT, self.on_apply)

        stepVoltage_label = wx.StaticText(panel, wx.ID_ANY, "Voltage step:")
        self.origami_stepVoltage_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator("floatPos"))
        self.origami_stepVoltage_value.SetValue(str(self.user_settings["origami_stepVoltage"]))
        self.origami_stepVoltage_value.Bind(wx.EVT_TEXT, self.on_apply)

        boltzmann_label = wx.StaticText(panel, wx.ID_ANY, "Boltzmann offset:")
        self.origami_boltzmannOffset_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator("floatPos"))
        self.origami_boltzmannOffset_value.SetValue(str(self.user_settings["origami_boltzmannOffset"]))
        self.origami_boltzmannOffset_value.Bind(wx.EVT_TEXT, self.on_apply)

        exponentialPercentage_label = wx.StaticText(panel, wx.ID_ANY, "Exponential percentage:")
        self.origami_exponentialPercentage_value = wx.TextCtrl(
            panel, -1, "", size=(-1, -1), validator=validator("floatPos")
        )
        self.origami_exponentialPercentage_value.SetValue(str(self.user_settings["origami_exponentialPercentage"]))
        self.origami_exponentialPercentage_value.Bind(wx.EVT_TEXT, self.on_apply)

        exponentialIncrement_label = wx.StaticText(panel, wx.ID_ANY, "Exponential increment:")
        self.origami_exponentialIncrement_value = wx.TextCtrl(
            panel, -1, "", size=(-1, -1), validator=validator("floatPos")
        )
        self.origami_exponentialIncrement_value.SetValue(str(self.user_settings["origami_exponentialIncrement"]))
        self.origami_exponentialIncrement_value.Bind(wx.EVT_TEXT, self.on_apply)

        import_label = wx.StaticText(panel, wx.ID_ANY, "Import list:")
        self.origami_loadListBtn = wx.Button(panel, wx.ID_ANY, "...", size=(-1, 22))
        self.origami_loadListBtn.Bind(wx.EVT_BUTTON, self.on_load_origami_list)

        horizontal_line = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        # pack elements
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(acquisition_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.origami_method_choice, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(spv_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.origami_scansPerVoltage_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(scan_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.origami_startScan_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(startVoltage_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.origami_startVoltage_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(endVoltage_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.origami_endVoltage_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(stepVoltage_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.origami_stepVoltage_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(boltzmann_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.origami_boltzmannOffset_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(exponentialPercentage_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.origami_exponentialPercentage_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(exponentialIncrement_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.origami_exponentialIncrement_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(import_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.origami_loadListBtn, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(horizontal_line, (n, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 0, wx.ALIGN_CENTER_HORIZONTAL, 10)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def make_buttons_panel(self, split_panel):
        panel = wx.Panel(split_panel, -1, name="settings")

        # pack elements
        grid = wx.GridBagSizer(2, 2)
        n = 0
        self.origami_applyBtn = wx.Button(panel, wx.ID_OK, "Apply", size=(-1, 22))
        self.origami_applyBtn.Bind(wx.EVT_BUTTON, self.on_apply_to_document)

        self.origami_cancelBtn = wx.Button(panel, wx.ID_OK, "Close", size=(-1, 22))
        self.origami_cancelBtn.Bind(wx.EVT_BUTTON, self.on_close)

        n += 1
        grid.Add(self.origami_applyBtn, (n, 0), flag=wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.origami_cancelBtn, (n, 1), flag=wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 0, wx.ALIGN_CENTER_HORIZONTAL, 10)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def make_spectrum_panel(self, split_panel):
        panel = wx.Panel(split_panel, -1, name="information")

        info_label = wx.StaticText(panel, wx.ID_ANY, "Information")
        self.info_value = wx.StaticText(panel, -1, "")
        self.info_value.SetLabel("")

        self.preprocess_check = wx.CheckBox(panel, -1, "Pre-process", (3, 3))
        self.preprocess_check.SetValue(self.config.origami_preprocess)
        self.preprocess_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        self.process_btn = wx.Button(panel, wx.ID_ANY, "Edit MS processing settings...", size=(-1, 22))
        self.process_btn.Bind(wx.EVT_BUTTON, self.on_open_process_MS_settings)

        horizontal_line = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        self.origami_extractBtn = wx.Button(
            panel, wx.ID_ANY, "Extract mass spectrum for each collision voltage", size=(-1, 22)
        )
        self.origami_extractBtn.Bind(
            wx.EVT_BUTTON, self.data_handling.on_extract_mass_spectrum_for_each_collision_voltage_fcn
        )

        # pack elements
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(info_label, (n, 0), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(self.info_value, (n, 0), wx.GBSpan(6, 2), flag=wx.EXPAND)
        n += 6
        grid.Add(self.preprocess_check, (n, 0), flag=wx.EXPAND)
        grid.Add(self.process_btn, (n, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        n += 1
        grid.Add(self.origami_extractBtn, (n, 0), wx.GBSpan(1, 2), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        n += 1
        grid.Add(horizontal_line, (n, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n += 1

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 0, wx.ALIGN_CENTER_HORIZONTAL, 10)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def make_plot_panel(self, split_panel):

        panel = wx.Panel(split_panel, -1, size=(-1, -1), name="plot")
        self.plot_panel = wx.Panel(panel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)

        pixel_size = [(self._window_size[0] - self._settings_panel_size[0]), (self._window_size[1] - 50)]
        figsize = [pixel_size[0] / self._display_resolution[0], pixel_size[1] / self._display_resolution[1]]

        self.plot_window = mpl_plots.plots(self.plot_panel, figsize=figsize, config=self.config)

        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(self.plot_window, 1, wx.EXPAND)

        box.Fit(self.plot_panel)
        self.plot_window.SetSize(pixel_size)
        self.plot_panel.SetSizer(box)
        self.plot_panel.Layout()

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.plot_panel, 1, wx.EXPAND, 2)
        # fit layout
        panel.SetSizer(main_sizer)
        main_sizer.Fit(panel)

        return panel

    def on_apply(self, evt):

        self.user_settings["origami_acquisition"] = self.origami_method_choice.GetStringSelection()
        self.user_settings["origami_startScan"] = str2int(self.origami_startScan_value.GetValue())
        self.user_settings["origami_spv"] = str2int(self.origami_scansPerVoltage_value.GetValue())
        self.user_settings["origami_startVoltage"] = str2num(self.origami_startVoltage_value.GetValue())
        self.user_settings["origami_endVoltage"] = str2num(self.origami_endVoltage_value.GetValue())
        self.user_settings["origami_stepVoltage"] = str2num(self.origami_stepVoltage_value.GetValue())
        self.user_settings["origami_boltzmannOffset"] = str2num(self.origami_boltzmannOffset_value.GetValue())
        self.user_settings["origami_exponentialPercentage"] = str2num(
            self.origami_exponentialPercentage_value.GetValue()
        )
        self.user_settings["origami_exponentialIncrement"] = str2num(self.origami_exponentialIncrement_value.GetValue())

        self.user_settings_changed = True

        self.on_update_info()

    def on_apply_to_document(self, evt):
        # update settings
        self.on_update_info()

        start_end_cv_list = self.calculate_origami_parameters()

        document = self.data_handling._on_get_document(self.document_title)

        try:
            reader = self.data_handling._get_waters_api_reader(document)
            n_scans = reader.stats_in_functions[0]["n_scans"]
        except (KeyError, IndexError):
            n_scans = 999999

        calculated_n_scans = start_end_cv_list[-1][1]
        if calculated_n_scans > n_scans:
            raise MessageError(
                "Incorrect input settings",
                f"Your current settings indicate there is {calculated_n_scans} scans in the dataset, whereas"
                + f" there is only {n_scans}.",
            )

        document.metadata["origami_ms"] = self.user_settings
        document.combineIonsList = start_end_cv_list
        self.data_handling.on_update_document(document, "no_refresh")
        self.user_settings_changed = False

        self.on_plot()

    def on_update_info(self):

        try:
            start_end_cv_list = self.calculate_origami_parameters()
        except (TypeError, IndexError, ValueError):
            self.info_value.SetLabel("")
            return

        if len(start_end_cv_list) == 0:
            self.info_value.SetLabel("")
            return

        document = self.data_handling._on_get_document(self.document_title)
        reader = self.data_handling._get_waters_api_reader(document)

        mz_x, mz_spacing = self.data_handling._get_waters_api_spacing(reader)
        n_spectra = len(start_end_cv_list)
        n_bins = len(mz_x)

        first_scan = start_end_cv_list[0][0]
        last_scan = start_end_cv_list[-1][1]
        approx_ram = (n_spectra * n_bins * 8) / (1024 ** 2)
        info = (
            f"\n" + f"Number of iterations: {n_spectra}\n" + f"First scan {first_scan} | Last scan: {last_scan}\n"
            f"Number of points in each spectrum: {n_bins}\n"
            + f"m/z spacing: {mz_spacing}\n"
            + f"Approx. amount of RAM: {approx_ram:.0f} MB"
        )
        self.info_value.SetLabel(info)

    def on_toggle_controls(self, evt):
        self.config.origami_acquisition = self.origami_method_choice.GetStringSelection()
        if self.config.origami_acquisition == "Linear":
            enableList = [
                self.origami_startScan_value,
                self.origami_startVoltage_value,
                self.origami_endVoltage_value,
                self.origami_stepVoltage_value,
                self.origami_scansPerVoltage_value,
            ]
            disableList = [
                self.origami_boltzmannOffset_value,
                self.origami_exponentialIncrement_value,
                self.origami_exponentialPercentage_value,
                self.origami_loadListBtn,
            ]
        elif self.config.origami_acquisition == "Exponential":
            enableList = [
                self.origami_startScan_value,
                self.origami_startVoltage_value,
                self.origami_endVoltage_value,
                self.origami_stepVoltage_value,
                self.origami_scansPerVoltage_value,
                self.origami_exponentialIncrement_value,
                self.origami_exponentialPercentage_value,
            ]
            disableList = [self.origami_boltzmannOffset_value, self.origami_loadListBtn]
        elif self.config.origami_acquisition == "Boltzmann":
            enableList = [
                self.origami_startScan_value,
                self.origami_startVoltage_value,
                self.origami_endVoltage_value,
                self.origami_stepVoltage_value,
                self.origami_scansPerVoltage_value,
                self.origami_boltzmannOffset_value,
            ]
            disableList = [
                self.origami_exponentialIncrement_value,
                self.origami_exponentialPercentage_value,
                self.origami_loadListBtn,
            ]
        elif self.config.origami_acquisition == "User-defined":
            disableList = [
                self.origami_startVoltage_value,
                self.origami_endVoltage_value,
                self.origami_stepVoltage_value,
                self.origami_exponentialIncrement_value,
                self.origami_exponentialPercentage_value,
                self.origami_scansPerVoltage_value,
                self.origami_boltzmannOffset_value,
            ]
            enableList = [self.origami_loadListBtn, self.origami_startScan_value]
        else:
            disableList = [
                self.origami_startScan_value,
                self.origami_startVoltage_value,
                self.origami_endVoltage_value,
                self.origami_stepVoltage_value,
                self.origami_exponentialIncrement_value,
                self.origami_exponentialPercentage_value,
                self.origami_scansPerVoltage_value,
                self.origami_boltzmannOffset_value,
                self.origami_loadListBtn,
            ]
            enableList = []

        # iterate
        for item in enableList:
            item.Enable()
        for item in disableList:
            item.Disable()

        self.config.origami_preprocess = self.preprocess_check.GetValue()
        self.process_btn.Enable(enable=self.config.origami_preprocess)

        if evt is not None:
            evt.Skip()

    def on_open_process_MS_settings(self, evt):
        self.document_tree.on_open_process_MS_settings(disable_plot=True, disable_process=True)

    @staticmethod
    def _load_origami_list(path):
        """Load ORIGAMI-MS CV/SPV list"""
        origami_list = np.genfromtxt(path, delimiter=",", skip_header=True)
        return origami_list

    def on_load_origami_list(self, evt):
        """Load a csv file with CV/SPV values for the List/User-defined method"""
        dlg = wx.FileDialog(self, "Choose a text file:", wildcard="*.csv", style=wx.FD_DEFAULT_STYLE | wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            origami_list = self._load_origami_list(path)

            self.user_settings["origami_cv_spv_list"] = origami_list

        dlg.Destroy()

    def on_plot(self):
        start_end_cv_list = self.calculate_origami_parameters()
        scans, voltages = pr_origami.generate_extraction_windows(start_end_cv_list)

        self.panel_plot.on_plot_scan_vs_voltage(
            scans,
            voltages,
            xlabel="Scans",
            ylabel="Collision Voltage (V)",
            testMax=False,
            plot=None,
            plot_obj=self.plot_window,
        )

    def calculate_origami_parameters(self):
        method = self.user_settings["origami_acquisition"]

        if method == "Linear":
            start_end_cv_list = pr_origami.calculate_scan_list_linear(
                self.user_settings["origami_startScan"],
                self.user_settings["origami_startVoltage"],
                self.user_settings["origami_endVoltage"],
                self.user_settings["origami_stepVoltage"],
                self.user_settings["origami_spv"],
            )
        elif method == "Exponential":
            start_end_cv_list = pr_origami.calculate_scan_list_exponential(
                self.user_settings["origami_startScan"],
                self.user_settings["origami_startVoltage"],
                self.user_settings["origami_endVoltage"],
                self.user_settings["origami_stepVoltage"],
                self.user_settings["origami_spv"],
                self.user_settings["origami_exponentialIncrement"],
                self.user_settings["origami_exponentialPercentage"],
            )
        elif method == "Boltzmann":
            start_end_cv_list = pr_origami.calculate_scan_list_boltzmann(
                self.user_settings["origami_startScan"],
                self.user_settings["origami_startVoltage"],
                self.user_settings["origami_endVoltage"],
                self.user_settings["origami_stepVoltage"],
                self.user_settings["origami_spv"],
                self.user_settings["origami_boltzmannOffset"],
            )
        elif method == "User-defined":
            start_end_cv_list = []
        elif method == "Manual":
            start_end_cv_list = []

        return start_end_cv_list
