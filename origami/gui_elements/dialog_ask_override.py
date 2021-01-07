"""Simple dialog to ask whether to overwrite, merge or duplicate object"""
# Third-party imports
import wx

# Local imports
from origami.styles import Dialog
from origami.config.config import CONFIG
from origami.gui_elements.helpers import set_tooltip
from origami.gui_elements.helpers import make_checkbox


class DialogAskOverride(Dialog):
    """Simple dialog to ask whether to overwrite, merge or duplicate object"""

    # ui elements
    msg = None
    override_btn = None
    merge_btn = None
    copy_btn = None
    close_btn = None
    not_ask_again_check = None

    def __init__(self, parent, msg: str = None):
        Dialog.__init__(self, parent, title="Conflicting name...")

        self.parent = parent
        if msg is None:
            msg = "Item already exists in the document. \nWhat would you like to do?"

        self._msg = msg
        self.action = None

        self.make_gui()
        self.CentreOnParent()

    def make_gui(self):
        """Make UI"""

        # make panel
        panel = self.make_panel()

        # pack element
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(panel, 0, wx.EXPAND, 10)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizer(main_sizer)
        self.SetSize((-1, -1))

    def make_panel(self):
        """Make panel"""
        panel = wx.Panel(self, -1)

        self.msg = wx.StaticText(panel, -1, self._msg, size=(-1, -1))

        self.override_btn = wx.Button(panel, wx.ID_ANY, "Override", size=(-1, -1))
        self.override_btn.Bind(wx.EVT_BUTTON, self.overwrite)
        set_tooltip(self.override_btn, "Overwrite current data with new values.")

        self.merge_btn = wx.Button(panel, wx.ID_ANY, "Merge", size=(-1, -1))
        self.merge_btn.Bind(wx.EVT_BUTTON, self.merge)
        set_tooltip(self.merge_btn, "Merge current data with new values (if possible).")

        self.copy_btn = wx.Button(panel, wx.ID_OK, "Create copy", size=(-1, -1))
        self.copy_btn.Bind(wx.EVT_BUTTON, self.create_copy)
        set_tooltip(self.copy_btn, "Create duplicate entry of current data (if possible).")

        self.close_btn = wx.Button(panel, wx.ID_OK, "Close", size=(-1, -1))
        self.close_btn.Bind(wx.EVT_BUTTON, self.on_close)
        set_tooltip(self.close_btn, "Close this window and perform no action.")

        self.not_ask_again_check = make_checkbox(panel, "Don't ask again")
        self.not_ask_again_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        set_tooltip(self.not_ask_again_check, "Select an action and do not ask again.")

        btn_grid = wx.BoxSizer(wx.HORIZONTAL)
        btn_grid.Add(self.override_btn)
        btn_grid.AddSpacer(5)
        btn_grid.Add(self.merge_btn)
        btn_grid.AddSpacer(5)
        btn_grid.Add(self.copy_btn)
        btn_grid.AddSpacer(5)
        btn_grid.Add(self.close_btn)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.msg, 1, wx.EXPAND | wx.ALL, 10)
        main_sizer.Add(btn_grid, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)
        main_sizer.Add(self.not_ask_again_check, 0, wx.ALIGN_LEFT | wx.ALL, 5)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def overwrite(self, _evt):
        """Overwrite existing"""
        CONFIG.import_duplicate_panel_action = "override"
        self.on_ok(None)

    def merge(self, _evt):
        """Merge existing"""
        CONFIG.import_duplicate_panel_action = "merge"
        self.on_ok(None)

    def create_copy(self, _evt):
        """Create new copy"""
        CONFIG.import_duplicate_panel_action = "duplicate"
        self.on_ok(None)

    def on_apply(self, _evt):
        """Update changes"""
        CONFIG.import_duplicate_panel_ask = self.not_ask_again_check.GetValue()

    def on_ok(self, _evt):
        """Close window in tidy manner"""
        self.action = CONFIG.import_duplicate_panel_action
        if self.IsModal():
            self.EndModal(wx.ID_OK)
        else:
            self.Destroy()

    def on_close(self, _evt):
        """Close window with ID_NO event"""
        CONFIG.import_duplicate_panel_action = None
        self.action = None

        if self.IsModal():
            self.EndModal(wx.ID_NO)
        else:
            self.Destroy()


def _main():
    # Local imports
    from origami.app import App

    app = App()
    frame = wx.Frame(None, -1)
    ex = DialogAskOverride(frame)
    ex.ShowModal()
    app.MainLoop()


if __name__ == "__main__":
    _main()
