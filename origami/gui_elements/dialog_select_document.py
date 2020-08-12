"""Select document dialog"""
# Standard library imports
import logging
from typing import List

# Third-party imports
import wx

# Local imports
from origami.styles import Dialog
from origami.styles import set_tooltip
from origami.config.environment import ENV

LOGGER = logging.getLogger(__name__)


class DialogSelectDocument(Dialog):
    """Select document from dropdown list"""

    # ui elements
    ok_btn = None
    add_btn = None
    open_btn = None
    cancel_btn = None
    document_list_choice = None

    # settable parameters
    current_document = None

    def __init__(
        self, parent, document_type: str = "all", document_list: List[str] = None, allow_new_document: bool = True
    ):
        wx.Dialog.__init__(self, parent, title="Please select document...", size=(400, 300))

        if document_list is None:
            document_list = []

        self.parent = parent
        self._document_type = document_type
        self._document_list = document_list
        self._allow_new_document = allow_new_document

        # make gui items
        self.make_gui()
        self.CentreOnParent()
        self.SetFocus()

        self.setup()

        self.Bind(wx.EVT_CLOSE, self.on_close, self)

    def setup(self):
        """Runs all setup events"""
        # In some cases, we don't want to be able to create new document!
        self.add_btn.Enable(enable=self._allow_new_document)
        if len(self._document_list) == 0:
            self.refresh(None)

    def make_gui(self):
        """Create GUI"""
        # make panel
        panel = self.make_panel()

        # pack element
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(panel, 0, wx.EXPAND, 0)
        main_sizer.Fit(self)
        self.SetSizer(main_sizer)

    def make_panel(self):
        """Make main panel"""
        panel = wx.Panel(self, -1)

        self.document_list_choice = wx.Choice(panel, -1, choices=self._document_list, size=(300, -1))
        self.document_list_choice.Select(0)
        set_tooltip(self.document_list_choice, "Select one of the available documents.")

        self.ok_btn = wx.Button(panel, wx.ID_OK, "OK", size=(-1, -1))
        self.ok_btn.Bind(wx.EVT_BUTTON, self.on_ok, id=wx.ID_ANY)
        set_tooltip(self.ok_btn, "Select currently selected document and close the window.")

        self.open_btn = wx.Button(panel, wx.ID_ANY, "Open existing...", size=(-1, -1))
        self.open_btn.Bind(wx.EVT_BUTTON, self.on_open, id=wx.ID_ANY)
        set_tooltip(
            self.open_btn,
            "Open another `ORIGAMI` document already present on the PC (must end with .origami extension).",
        )

        self.add_btn = wx.Button(panel, wx.ID_ANY, "Add new document", size=(-1, -1))
        self.add_btn.Bind(wx.EVT_BUTTON, self.on_new_document)
        set_tooltip(self.add_btn, "Create new document.")

        self.cancel_btn = wx.Button(panel, -1, "Cancel", size=(-1, -1))
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_close)
        set_tooltip(self.cancel_btn, "Close the window without making a selection.")

        # pack elements
        choice_sizer = wx.BoxSizer(wx.HORIZONTAL)
        choice_sizer.Add(wx.StaticText(panel, -1, "Choose document:"), flag=wx.ALIGN_CENTER_VERTICAL)
        choice_sizer.AddSpacer(10)
        choice_sizer.Add(self.document_list_choice, flag=wx.EXPAND)

        btn_grid = wx.GridBagSizer(5, 5)
        btn_grid.Add(self.ok_btn, (0, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        btn_grid.Add(self.open_btn, (0, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        btn_grid.Add(self.add_btn, (0, 3), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        btn_grid.Add(self.cancel_btn, (0, 4), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(choice_sizer, 1, wx.ALIGN_CENTER | wx.ALL, 10)
        main_sizer.Add(btn_grid, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizer(main_sizer)

        return panel

    def on_ok(self, _):
        """Select document"""
        self.current_document = self.document_list_choice.GetStringSelection()
        if self.IsModal():
            self.EndModal(wx.ID_OK)
        else:
            self.Destroy()

    def on_open(self, _):
        """Selects document from already existing data on the disk"""
        path = None

        dlg = wx.DirDialog(self, "Choose ORIGAMI document (.origami)", style=wx.DD_DEFAULT_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
        dlg.Destroy()

        if path is not None:
            document = ENV.open(path)
            self.current_document = document.title
            self.refresh(None)
            self.set_document()

        return path

    def on_new_document(self, _evt):
        """Create new document"""
        from origami.gui_elements.dialog_new_document import DialogNewDocument

        dlg = DialogNewDocument(self, document_type=self._document_type)
        if dlg.ShowModal() == wx.ID_OK:
            self.current_document = dlg.current_document
            self.refresh(None)
            self.set_document()
        dlg.Destroy()

    def on_close(self, _):
        """Destroy this frame."""
        self.current_document = None
        if self.IsModal():
            self.EndModal(wx.ID_NO)
        else:
            self.Destroy()

    def refresh(self, _):
        """Refresh list of documents"""
        self._document_list = ENV.get_document_list(self._document_type, check_path=True)
        self.document_list_choice.Clear()
        self.document_list_choice.AppendItems(self._document_list)
        self.document_list_choice.SetSelection(0)
        LOGGER.debug("Updated document list")

    def set_document(self):
        """Set currently cached document (if its in the document list)"""
        if self.current_document in self._document_list:
            self.document_list_choice.SetStringSelection(self.current_document)
        else:
            LOGGER.warning(f"Document `{self.current_document}` is not found in the document list")


def _main():
    app = wx.App()
    ex = DialogSelectDocument(None, document_list=["Document 1", "Document 2"], document_type="Type: Imaging")

    ex.Show()
    app.MainLoop()


if __name__ == "__main__":
    _main()
