"""Dialog window to give the user an option to save data"""
# Standard library imports
import logging
from typing import List

# Third-party imports
import wx

# Local imports
from origami.styles import Dialog
from origami.config.environment import ENV
from origami.gui_elements.helpers import set_tooltip

FORBIDDEN_NAMES = [""]
BOX_SIZE = 400
LOGGER = logging.getLogger(__name__)


class DialogSaveUnsaved(Dialog):
    """Simple dialog to save unsaved changes"""

    # ui elements
    document_title_value = None
    group_name_value = None
    dataset_name_value = None
    current_name_value = None
    new_name_value = None
    note_value = None
    ok_btn = None
    cancel_btn = None

    def __init__(self, parent, document_title: str, dataset_name: str, forbidden: List[str] = None):
        Dialog.__init__(self, parent, title="Save unsaved changes...", size=(400, 300))

        self.parent = parent
        self.new_name = None
        self.document_title = document_title
        self.group_name, self.dataset_name = self._parse_dataset_name(dataset_name)

        if forbidden is None:
            forbidden = FORBIDDEN_NAMES
        forbidden.append(self.dataset_name)
        self.forbidden = forbidden

        # make gui items
        self.make_gui()

        self.CentreOnParent()
        self.Layout()

        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_event)
        self.on_new_name(None)
        self.set_forbidden_names()

    @staticmethod
    def _parse_dataset_name(dataset_name: str):
        """Parse dataset name and get group name"""
        if "/" not in dataset_name:
            raise ValueError("Incorrect dataset name - expected GROUP_NAME/DATASET_NAME format")
        group_name, dataset_name = dataset_name.split("/")
        return group_name, dataset_name

    def set_forbidden_names(self):
        """Update list of forbidden items with currently present object names"""
        document = ENV.on_get_document(self.document_title)
        if not document:
            LOGGER.warning(f"Could not get document with the title `{self.document_title}`")
            return

        names = document.view_group(self.group_name)
        for name in names:
            self.forbidden.append(name.split("/")[-1])

    def on_key_event(self, evt):
        """Keyboard event handler"""
        key_code = evt.GetKeyCode()
        if key_code == wx.WXK_ESCAPE:  # key = esc
            self.on_close(evt=None)

        if evt is not None:
            evt.Skip()

    def on_close(self, evt, force: bool = False):
        """Destroy this frame."""
        self.new_name = None
        super(DialogSaveUnsaved, self).on_close(evt, force)

    def make_gui(self):
        """Make UI"""

        # make panel
        panel = self.make_panel()

        # pack element
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(panel, 1, wx.EXPAND, 10)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizer(main_sizer)
        self.SetMinSize((500, 100))

    def make_panel(self):
        """Make panel"""

        panel = wx.Panel(self, -1)

        self.document_title_value = wx.StaticText(panel, -1, "", size=(BOX_SIZE, -1))
        self.document_title_value.SetLabel(self.document_title)
        set_tooltip(self.document_title_value, "Title of the document the object belongs to")

        self.group_name_value = wx.StaticText(panel, -1, "", size=(BOX_SIZE, -1))
        self.group_name_value.SetLabel(self.group_name)
        set_tooltip(self.group_name_value, "Name of the group data belongs to")

        self.current_name_value = wx.StaticText(panel, -1, "", size=(BOX_SIZE, -1))
        self.current_name_value.SetLabel(self.dataset_name)
        set_tooltip(self.current_name_value, "Current name of the object")

        self.new_name_value = wx.TextCtrl(panel, -1, "", size=(BOX_SIZE, -1), style=wx.TE_PROCESS_ENTER)
        self.new_name_value.SetValue(self.dataset_name)
        self.new_name_value.Bind(wx.EVT_TEXT, self.on_new_name)
        self.new_name_value.SetFocus()
        set_tooltip(
            self.new_name_value,
            "Type-in new name of the object. If the box is glowing red, it indicates that the selected name is"
            " not allowed.",
        )

        self.note_value = wx.StaticText(panel, -1, "", size=(BOX_SIZE, 40))
        self.note_value.Wrap(BOX_SIZE)
        set_tooltip(self.note_value, "Final name of the object after you click on `Rename` button")

        self.ok_btn = wx.Button(panel, wx.ID_OK, "Save changes", size=(-1, -1))
        self.ok_btn.Bind(wx.EVT_BUTTON, self.on_ok)
        set_tooltip(self.ok_btn, "Save object with the `New name` value.")

        self.cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel", size=(-1, -1))
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_close)
        set_tooltip(self.cancel_btn, "Close window and do not save changes.")

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.Add(self.ok_btn)
        btn_sizer.AddSpacer(10)
        btn_sizer.Add(self.cancel_btn)

        # pack elements
        grid = wx.GridBagSizer(5, 5)
        n = 0
        grid.Add(wx.StaticText(panel, -1, "Document title:"), (n, 0), flag=wx.ALIGN_TOP)
        grid.Add(self.document_title_value, (n, 1), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(wx.StaticText(panel, -1, "Group name:"), (n, 0), flag=wx.ALIGN_TOP)
        grid.Add(self.group_name_value, (n, 1), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(wx.StaticText(panel, -1, "Current name:"), (n, 0), flag=wx.ALIGN_TOP)
        grid.Add(self.current_name_value, (n, 1), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(wx.StaticText(panel, -1, "New name:"), (n, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.new_name_value, (n, 1), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(wx.StaticLine(panel, wx.SL_HORIZONTAL), (n, 0), (1, 6), flag=wx.EXPAND)
        n += 1
        grid.Add(wx.StaticText(panel, -1, "Final name:"), (n, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.note_value, (n, 1), wx.GBSpan(2, 5), flag=wx.EXPAND)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def on_new_name(self, _evt):
        """Finish editing label"""
        new_name = self.set_new_name

        if new_name in self.forbidden:
            self.new_name_value.SetBackgroundColour((255, 230, 239))
            self.note_value.SetLabel("This name is not allowed")
        else:
            self.new_name_value.SetBackgroundColour(wx.WHITE)
            self.note_value.SetLabel(self.full_name)
        self.new_name_value.Refresh()

    @property
    def set_new_name(self):
        """Return `new_name`"""
        self.new_name = "{}".format(self.new_name_value.GetValue())

        return self.new_name

    @property
    def full_name(self):
        """Return full name including group name"""
        return f"{self.group_name}/{self.new_name}"

    def on_ok(self, _evt):
        """ change label of the selected item """
        if self.new_name in self.forbidden:

            from origami.gui_elements.misc_dialogs import DialogBox

            DialogBox(
                title="Forbidden name",
                msg=f"The name you've selected {self.new_name} is not allowed!\nPlease type-in another name.",
                kind="Error",
                parent=self,
            )
            return

        self.new_name = self.full_name
        super(DialogSaveUnsaved, self).on_ok(_evt)


def _main():

    from origami.app import App

    app = App()
    ex = DialogSaveUnsaved(None, "Document 1", "MassSpectra/Summed Spectrum")

    ex.Show()
    app.MainLoop()


if __name__ == "__main__":
    _main()
