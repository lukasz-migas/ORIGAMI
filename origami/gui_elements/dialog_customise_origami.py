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


class DialogCustomiseORIGAMI(Dialog):
    """Dialog to setup ORIGAMI-MS settings"""

    def __init__(self, parent, presenter, config, **kwargs):
        Dialog.__init__(self, parent, title="ORIGAMI-MS settings...")

        self.parent = parent
        self.presenter = presenter
        self.config = config

        self.data_handling = self.parent.data_handling
        self.data_processing = self.parent.data_processing

        self.user_settings = self.on_setup_gui()
        self.user_settings_changed = False

        self.make_gui()
        self.on_toggle_controls(None)
        self.SetSize((300, 314))
        self.Layout()
        self.CentreOnScreen()
        self.SetFocus()

        # bind events
        wx.EVT_CLOSE(self, self.on_close)

    def on_setup_gui(self):
        document = self.data_handling._on_get_document()
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
        self.on_apply_to_document()

    def make_gui(self):

        # make panel
        panel = self.make_panel()

        # pack element
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.Add(panel, 1, wx.EXPAND, 10)

        # fit layout
        self.main_sizer.Fit(self)
        self.SetSizer(self.main_sizer)

    def make_panel(self):
        panel = wx.Panel(self, -1)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

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

        self.origami_applyBtn = wx.Button(panel, wx.ID_OK, "Apply", size=(-1, 22))
        self.origami_applyBtn.Bind(wx.EVT_BUTTON, self.on_apply_to_document)

        self.origami_cancelBtn = wx.Button(panel, wx.ID_OK, "Close", size=(-1, 22))
        self.origami_cancelBtn.Bind(wx.EVT_BUTTON, self.on_close)

        # pack elements
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(acquisition_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.origami_method_choice, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        #         grid.Add(self.origami_loadParams, (n,2), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT)
        n = n + 1
        grid.Add(spv_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.origami_scansPerVoltage_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(scan_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.origami_startScan_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(startVoltage_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.origami_startVoltage_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(endVoltage_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.origami_endVoltage_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(stepVoltage_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.origami_stepVoltage_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(boltzmann_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.origami_boltzmannOffset_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(exponentialPercentage_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.origami_exponentialPercentage_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(exponentialIncrement_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.origami_exponentialIncrement_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(import_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.origami_loadListBtn, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(horizontal_line, (n, 0), wx.GBSpan(1, 2), flag=wx.EXPAND)
        n = n + 1
        grid.Add(
            self.origami_applyBtn, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL
        )
        grid.Add(
            self.origami_cancelBtn, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL
        )

        main_sizer.Add(grid, 0, wx.ALIGN_CENTER_HORIZONTAL, 10)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

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

    def on_apply_to_document(self, evt):
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

        document = self.data_handling._on_get_document()
        document.metadata["origami_ms"] = self.user_settings
        document.combineIonsList = start_end_cv_list
        self.data_handling.on_update_document(document, "no_refresh")
        self.user_settings_changed = False

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

        if evt is not None:
            evt.Skip()
