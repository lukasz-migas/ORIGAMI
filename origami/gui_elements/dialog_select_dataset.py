"""Simple dialog that enables selection of document/dataset pair"""
# Standard library imports
from typing import Dict
from typing import List

# Third-party imports
import wx

# Local imports
from origami.styles import Dialog


class DialogSelectDataset(Dialog):
    """Simple dialog that enables selection of document/dataset pair"""

    # UI elements
    document_list_choice = None
    dataset_list_choice = None
    ok_btn = None
    cancel_btn = None

    # attributes
    document = None
    dataset = None

    def __init__(
        self,
        parent,
        document_list: List,
        dataset_list: Dict[str, List[str]],
        set_document: str = None,
        title="Select document/dataset pair",
    ):
        Dialog.__init__(self, parent, title=title, size=(500, 300))
        self._document_list = document_list
        self._dataset_list = dataset_list

        # make gui items
        self.make_gui()
        if set_document:
            self.document_list_choice.SetStringSelection(set_document)
        self.on_update_gui(None)

        self.CentreOnParent()
        self.SetFocus()

        self.Bind(wx.EVT_CLOSE, self.on_close)

    def on_close(self, evt):
        """Destroy this frame."""
        self.document = None
        self.dataset = None

        self.Destroy()

    def make_gui(self):
        """Make UI"""

        # make panel
        panel = self.make_panel()

        # pack element
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(panel, 0, wx.EXPAND, 0)

        # bind
        self.ok_btn.Bind(wx.EVT_BUTTON, self.on_make_selection, id=wx.ID_OK)
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_close)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizer(main_sizer)

    def make_panel(self):
        """Make panel"""

        panel = wx.Panel(self, -1)

        self.document_list_choice = wx.ComboBox(
            panel, -1, choices=self._document_list, size=(400, -1), style=wx.CB_READONLY
        )
        self.document_list_choice.Select(0)
        self.document_list_choice.Bind(wx.EVT_COMBOBOX, self.on_update_gui)

        self.dataset_list_choice = wx.ComboBox(panel, -1, choices=[], size=(400, -1), style=wx.CB_READONLY)

        self.ok_btn = wx.Button(panel, wx.ID_OK, "Select", size=(-1, 22))
        self.cancel_btn = wx.Button(panel, -1, "Cancel", size=(-1, 22))

        btn_grid = wx.GridBagSizer(5, 5)
        n = 0
        btn_grid.Add(self.ok_btn, (n, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        btn_grid.Add(self.cancel_btn, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)

        # pack elements
        grid = wx.GridBagSizer(5, 5)
        n = 0
        grid.Add(wx.StaticText(panel, -1, "Document:"), (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.document_list_choice, (n, 1), wx.GBSpan(1, 3))
        n += 1
        grid.Add(wx.StaticText(panel, -1, "Dataset:"), (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.dataset_list_choice, (n, 1), wx.GBSpan(1, 3))
        n += 1
        grid.Add(btn_grid, (n, 0), wx.GBSpan(1, 5), flag=wx.ALIGN_CENTER)

        # add to sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizer(main_sizer)

        return panel

    def on_update_gui(self, _evt):
        """Update GUI by making selection"""
        document = self.document_list_choice.GetStringSelection()
        spectrum = self._dataset_list[document]

        self.dataset_list_choice.SetItems(spectrum)
        self.dataset_list_choice.SetStringSelection(spectrum[0])

    def on_make_selection(self, _evt):
        """Make selection and close the window"""
        document = self.document_list_choice.GetStringSelection()
        dataset = self.dataset_list_choice.GetStringSelection()
        self.document = document
        self.dataset = dataset
        self.EndModal(wx.OK)


def _main():

    app = wx.App()
    ex = DialogSelectDataset(None, ["TEST", "TEST2"], dict(TEST=["Spectrum 1", "Spectrum 2"], TEST2=["Spec 3"]))

    ex.ShowModal()
    app.MainLoop()


if __name__ == "__main__":
    _main()
