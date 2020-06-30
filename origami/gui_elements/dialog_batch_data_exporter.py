"""Dialog to select parameters for data export"""
# Standard library imports
import logging

# Third-party imports
import wx

# Local imports
from origami.styles import Dialog
from origami.styles import set_tooltip
from origami.styles import make_bitmap_btn
from origami.utils.path import check_path_exists
from origami.icons.assets import Icons
from origami.config.config import CONFIG

logger = logging.getLogger(__name__)


class DialogExportData(Dialog):
    """Batch export images"""

    folder_path = None
    folder_path_btn = None
    file_delimiter_choice = None
    file_extension_label = None
    save_btn = None
    cancel_btn = None

    def __init__(self, parent, default_path=None):
        Dialog.__init__(self, parent, title="Export data....")
        self._icons = Icons()

        self.default_path = default_path

        self.make_gui()
        self.setup()

        # setup layout
        self.CentreOnParent()
        self.Show(True)
        self.SetFocus()

    def setup(self):
        """Setup GUI"""
        if isinstance(self.default_path, str) and check_path_exists(self.default_path):
            self.folder_path.SetLabel(self.default_path)

    def on_close(self, evt, force: bool = False):
        """Destroy this frame"""
        CONFIG.data_folder_path = None
        if self.IsModal():
            self.EndModal(wx.ID_NO)
        else:
            self.Destroy()

    def make_panel(self):
        """Make panel"""
        panel = wx.Panel(self, -1, size=(-1, -1))

        self.folder_path = wx.TextCtrl(panel, -1, "", style=wx.TE_CHARWRAP, size=(350, -1))
        self.folder_path.SetLabel(str(CONFIG.data_folder_path))
        self.folder_path.Bind(wx.EVT_TEXT, self.on_apply)
        set_tooltip(self.folder_path, "Specify output path.")

        self.folder_path_btn = make_bitmap_btn(panel, wx.ID_ANY, self._icons.folder)
        self.folder_path_btn.Bind(wx.EVT_BUTTON, self.on_get_path)
        set_tooltip(self.folder_path_btn, "Select output path.")

        self.file_delimiter_choice = wx.Choice(panel, -1, choices=list(CONFIG.textOutputDict.keys()), size=(-1, -1))
        self.file_delimiter_choice.SetStringSelection(CONFIG.saveDelimiterTXT)
        self.file_delimiter_choice.Bind(wx.EVT_CHOICE, self.on_apply)

        self.file_extension_label = wx.StaticText(panel, -1, CONFIG.saveExtension)

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
        grid.Add(wx.StaticText(panel, -1, "Folder path:"), (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.folder_path, (n, 1), wx.GBSpan(1, 4), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.folder_path_btn, (n, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(wx.StaticText(panel, wx.ID_ANY, "Delimiter:"), (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.file_delimiter_choice, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(wx.StaticText(panel, wx.ID_ANY, "Extension:"), (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.file_extension_label, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(btn_grid, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def on_save(self, _evt):
        """Save event"""
        if not check_path_exists(CONFIG.data_folder_path):
            from origami.gui_elements.misc_dialogs import DialogBox

            dlg = DialogBox(
                "Incorrect input path",
                f"The folder path is set to `{CONFIG.data_folder_path}` or does not exist."
                + " Are you sure you would like to continue?",
                kind="Question",
            )
            if dlg == wx.ID_NO:
                return

        if self.IsModal():
            self.EndModal(wx.ID_OK)
        else:
            self.Destroy()

    def on_get_path(self, _evt):
        """Get directory where to save the data"""
        dlg = wx.DirDialog(
            self, "Choose a folder where to save images", style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST
        )
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.folder_path.SetLabel(path)
            CONFIG.data_folder_path = path

    def on_apply(self, _evt):
        """Update config"""
        CONFIG.saveDelimiterTXT = self.file_delimiter_choice.GetStringSelection()
        CONFIG.saveDelimiter = CONFIG.textOutputDict[CONFIG.saveDelimiterTXT]
        CONFIG.saveExtension = CONFIG.textExtensionDict[CONFIG.saveDelimiterTXT]
        CONFIG.data_folder_path = self.folder_path.GetValue()

        self.file_extension_label.SetLabel(CONFIG.saveExtension)


def _main():
    app = wx.App()
    ex = DialogExportData(None)

    ex.Show()
    app.MainLoop()


if __name__ == "__main__":
    _main()
