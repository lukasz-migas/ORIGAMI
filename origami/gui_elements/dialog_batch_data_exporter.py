# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
from __future__ import division

import logging

import wx
from styles import Dialog
from utils.path import check_path_exists

logger = logging.getLogger(__name__)


class DialogExportData(Dialog):
    """Batch export images"""

    def __init__(self, parent, presenter, config, icons, **kwargs):
        Dialog.__init__(self, parent, title="Export data....")
        self.view = parent
        self.presenter = presenter
        self.documentTree = self.view.panelDocuments.documents
        self.data_handling = presenter.data_handling
        self.config = config
        self.icons = icons

        self.data_processing = presenter.data_processing
        self.data_handling = presenter.data_handling

        self.make_gui()

        # setup layout
        self.CentreOnScreen()
        self.Show(True)
        self.SetFocus()

    def on_close(self, evt):
        """Destroy this frame"""
        self.EndModal(wx.ID_NO)

    def make_panel(self):
        panel = wx.Panel(self, -1, size=(-1, -1))

        folder_path = wx.StaticText(panel, -1, "Folder path:")
        self.folder_path = wx.TextCtrl(
            panel, -1, "", style=wx.TE_READONLY | wx.TE_MULTILINE | wx.TE_CHARWRAP, size=(350, -1)
        )
        self.folder_path.SetLabel(str(self.config.data_folder_path))
        self.folder_path.Disable()

        self.folder_path_btn = wx.Button(panel, wx.ID_ANY, "...", size=(25, 22))
        self.folder_path_btn.Bind(wx.EVT_BUTTON, self.on_get_path)

        file_delimiter_choice = wx.StaticText(panel, wx.ID_ANY, "Delimiter:")
        self.file_delimiter_choice = wx.Choice(
            panel, -1, choices=list(self.config.textOutputDict.keys()), size=(-1, -1)
        )
        self.file_delimiter_choice.SetStringSelection(self.config.saveDelimiterTXT)
        self.file_delimiter_choice.Bind(wx.EVT_CHOICE, self.on_apply)

        file_extension_label = wx.StaticText(panel, wx.ID_ANY, "Extension:")
        self.file_extension_label = wx.StaticText(panel, -1, self.config.saveExtension)

        horizontal_line_0 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        self.save_btn = wx.Button(panel, wx.ID_OK, "Save data", size=(-1, 22))
        self.save_btn.Bind(wx.EVT_BUTTON, self.on_save)

        self.cancel_btn = wx.Button(panel, wx.ID_OK, "Cancel", size=(-1, 22))
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_close)

        btn_grid = wx.GridBagSizer(2, 2)
        n = 0
        btn_grid.Add(self.save_btn, (n, 0), flag=wx.EXPAND)
        btn_grid.Add(self.cancel_btn, (n, 1), flag=wx.EXPAND)

        # pack elements
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(folder_path, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.folder_path, (n, 1), wx.GBSpan(1, 4), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.folder_path_btn, (n, 5), flag=wx.ALIGN_CENTER_VERTICAL)
        n += 1
        grid.Add(file_delimiter_choice, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.file_delimiter_choice, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(file_extension_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.file_extension_label, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(horizontal_line_0, (n, 0), wx.GBSpan(1, 6), flag=wx.EXPAND)
        n += 1
        grid.Add(btn_grid, (n, 0), wx.GBSpan(1, 6), flag=wx.ALIGN_CENTER)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 0, wx.ALIGN_CENTER_HORIZONTAL, 10)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def on_save(self, evt):
        if not check_path_exists(self.config.data_folder_path):
            from gui_elements.misc_dialogs import DialogBox

            dlg = DialogBox(
                "Incorrect input path",
                f"The folder path is set to `{self.config.data_folder_path}` or does not exist."
                + " Are you sure you would like to continue?",
                type="Question",
            )
            if dlg == wx.ID_NO:
                return

        self.EndModal(wx.OK)

    def on_get_path(self, evt):
        dlg = wx.DirDialog(
            self.view, "Choose a folder where to save images", style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST
        )
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.folder_path.SetLabel(path)
            self.config.data_folder_path = path

    def on_apply(self, evt):
        self.config.saveDelimiterTXT = self.file_delimiter_choice.GetStringSelection()
        self.config.saveDelimiter = self.config.textOutputDict[self.config.saveDelimiterTXT]
        self.config.saveExtension = self.config.textExtensionDict[self.config.saveDelimiterTXT]

        self.file_extension_label.SetLabel(self.config.saveExtension)
