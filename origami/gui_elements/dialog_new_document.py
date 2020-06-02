# Standard library imports
import os
import logging

# Third-party imports
import wx

# Local imports
from origami.styles import Dialog
from origami.utils.exceptions import MessageError
from origami.config.environment import ENV
from origami.config.environment import DOCUMENT_TYPES

LOGGER = logging.getLogger(__name__)


class DialogNewDocument(Dialog):
    """Create new document dialog"""

    # ui elements
    ok_btn = None
    cancel_btn = None
    document_type_choice = None
    title_value = None
    path_value = None
    full_path_value = None
    directory_btn = None

    # settable parameters
    current_document = None

    def __init__(self, parent, **kwargs):
        wx.Dialog.__init__(self, parent, title="Create new document...", size=(400, 300))

        self.parent = parent

        self._document_type = kwargs.get("document_type", None)

        # make gui items
        self.make_gui()
        self.CentreOnParent()
        self.SetFocus()

        self.Bind(wx.EVT_CLOSE, self.on_close, self)

        self.setup()

    @property
    def path(self):
        return self.path_value.GetValue()

    @property
    def title(self):
        return self.title_value.GetValue()

    @property
    def document_type(self):
        return self.document_type_choice.GetStringSelection()

    @property
    def full_path(self):
        return os.path.join(self.path, self.title + ".origami")

    def setup(self):
        """Runs all setup events"""
        if self._document_type and self._document_type in DOCUMENT_TYPES:
            self.document_type_choice.SetStringSelection(self._document_type)
            self.document_type_choice.Disable()
        self.validate_path(None)

    def make_gui(self):
        """Create GUI"""
        # make panel
        panel = self.make_panel()

        # pack element
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(panel, 0, wx.EXPAND, 0)

        # bind

        # fit layout
        main_sizer.Fit(self)
        self.SetSizer(main_sizer)

    def validate_path(self, evt):
        """Validates that the selected path exists"""
        color = wx.WHITE
        if not os.path.exists(self.path):
            color = (255, 230, 239)

        self.path_value.SetBackgroundColour(color)
        self.Refresh()
        if evt is not None:
            evt.Skip()

    def update_full_path(self, evt):
        """Updates full path in the UI"""
        self.full_path_value.SetLabel(self.full_path)

        if evt is not None:
            evt.Skip()

    def make_panel(self):
        """Make main panel"""
        panel = wx.Panel(self, -1)

        path_label = wx.StaticText(panel, -1, "Directory:")
        self.path_value = wx.TextCtrl(panel, -1, "")
        self.path_value.Bind(wx.EVT_TEXT, self.validate_path)
        self.path_value.Bind(wx.EVT_TEXT, self.update_full_path)

        self.directory_btn = wx.Button(panel, wx.ID_OK, "Directory...", size=(-1, 22))
        self.directory_btn.Bind(wx.EVT_BUTTON, self.on_select_directory)

        title_label = wx.StaticText(panel, -1, "Title:")
        self.title_value = wx.TextCtrl(panel, -1, "")
        self.title_value.Bind(wx.EVT_TEXT, self.update_full_path)

        full_path_label = wx.StaticText(panel, -1, "Document path:")
        self.full_path_value = wx.StaticText(panel, -1, "")

        document_type_label = wx.StaticText(panel, -1, "Document type:")
        self.document_type_choice = wx.Choice(panel, -1, choices=DOCUMENT_TYPES, size=(300, -1))
        self.document_type_choice.Select(0)

        self.ok_btn = wx.Button(panel, wx.ID_OK, "OK", size=(-1, 22))
        self.ok_btn.Bind(wx.EVT_BUTTON, self.on_ok, id=wx.ID_ANY)

        self.cancel_btn = wx.Button(panel, -1, "Cancel", size=(-1, 22))
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_close)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.Add(self.ok_btn)
        btn_sizer.Add(self.cancel_btn)

        grid = wx.GridBagSizer(5, 5)
        y = 0
        grid.Add(path_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.path_value, (y, 1), wx.GBSpan(1, 3), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.directory_btn, (y, 4), flag=wx.ALIGN_CENTER_VERTICAL)
        y += 1
        grid.Add(title_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.title_value, (y, 1), wx.GBSpan(1, 3), wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y += 1
        grid.Add(full_path_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.full_path_value, (y, 1), wx.GBSpan(1, 3), wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y += 1
        grid.Add(document_type_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.document_type_choice, (y, 1), wx.GBSpan(1, 3), wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)

        # fit layout
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        main_sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        main_sizer.Fit(panel)
        panel.SetSizer(main_sizer)

        return panel

    def on_select_directory(self, _):
        """Select directory where to start searching for files/directories"""
        dlg = wx.DirDialog(self, "Choose directory", style=wx.DD_DEFAULT_STYLE)

        path = self.path
        title = self.title
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            title = os.path.split(path)[1]
        dlg.Destroy()

        self.path_value.SetValue(path)
        self.title_value.SetValue(title)
        LOGGER.debug(f"Selected {path}")

    def on_ok(self, _):
        """Select document"""
        path = self.path
        title = self.title
        full_path = self.full_path
        document_type = self.document_type

        if path in ["", None] or title in ["", None]:
            raise MessageError(
                "Cannot create new document",
                "Please select directory and specify appropriate document title before clicking on `OK`."
                " If you would prefer not to create new document, please click on the `Cancel` button or close"
                " the window.",
            )

        document = ENV.add_new(document_type=document_type, path=full_path, title=title)

        self.current_document = document.title
        if self.IsModal():
            self.EndModal(wx.ID_OK)
        else:
            self.Destroy()

    def on_close(self, _):
        """Destroy this frame."""
        self.current_document = None
        if self.IsModal():
            self.EndModal(wx.ID_NO)
        else:
            self.Destroy()


def main():

    app = wx.App()
    ex = DialogNewDocument(None, document_type="Type: Imaging")

    ex.Show()
    app.MainLoop()


if __name__ == "__main__":
    main()
