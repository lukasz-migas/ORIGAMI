"""Dialog about dataset"""
# Standard library imports
import os
import logging

# Third-party imports
from typing import List

import wx
from pubsub import pub
from pubsub.core import TopicNameError

# Local imports
from origami.styles import MiniFrame, VListBox
from origami.config.config import PUB_EVENT_USER_ADD, PUB_EVENT_USER_REMOVE, USERS
from origami.config.environment import ENV
from origami.gui_elements.helpers import set_tooltip
from origami.gui_elements.helpers import make_bitmap_btn
from origami.gui_elements.helpers import make_static_text

LOGGER = logging.getLogger(__name__)


def is_dir(path: str) -> bool:
    """Determines whether we should look for file or directory"""
    if path.endswith(".raw") or path.endswith(".origami"):  # waters
        return True
    elif path.endswith(".RAW"):  # thermo
        return False
    return True


class PathsVListBox(VListBox):
    """VListBox responsible for informing the user of all paths in the Document"""

    GOOD_COLOR = "#98FB98"
    BAD_COLOR = "#FFCCCB"

    def setup(self):
        """Additional setup"""

    def set_items(self, item_list: List[str]):
        """Set items in the listbox"""
        super(PathsVListBox, self).set_items(item_list)
        self.validate_items(item_list)

    def validate_items(self, items: List[str]):
        """Validate items"""
        for item_id, value in enumerate(items):
            color = self.GOOD_COLOR if os.path.exists(value) else self.BAD_COLOR
            self.SetItemBackgroundColour(item_id, color)

    def update_item(self, item_id: int, value: str):
        """Update value in the ui"""
        super(PathsVListBox, self).update_item(item_id, value)
        color = self.GOOD_COLOR if os.path.exists(value) else self.BAD_COLOR
        self.SetItemBackgroundColour(item_id, color)


class PanelDatasetInformation(MiniFrame):
    """Dataset information"""

    # ui elements
    output_value, notes_value, users_value, ok_btn, cancel_btn = None, None, None, None, None
    add_btn, output_path_btn, base_dir_value, file_dir_value, document_value = None, None, None, None, None
    paths_value, fix_btn, locate_btn = None, None, None

    def __init__(self, parent, icons, presenter, document_title: str, debug: bool = False):
        MiniFrame.__init__(self, parent, title="Import Dataset...", style=wx.DEFAULT_FRAME_STYLE & ~wx.MAXIMIZE_BOX)
        self.parent = parent
        self.presenter = presenter
        self._icons = self._get_icons(icons)
        self._debug = debug
        self.document_title = document_title

        # make ui
        self.make_gui()
        self.SetSize((800, -1))
        self.CenterOnParent()

        # bind events
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.setup()

        if document_title:
            self.setup_document(document_title)

    @property
    def data_handling(self):
        """Return handle to `data_handling`"""
        return self.presenter.data_handling

    @property
    def full_name(self) -> str:
        """Return the full name"""
        current_user = self.users_value.GetStringSelection().split(" :: ")
        if current_user:
            return current_user[0]
        return ""

    @property
    def output_dir(self) -> str:
        """Return output path"""
        base_dir = self.base_dir_value.GetValue()
        file_dir = self.file_dir_value.GetValue()
        return os.path.abspath(os.path.join(base_dir, file_dir))

    def setup(self):
        """Setup"""
        pub.subscribe(self.on_update_user_list, PUB_EVENT_USER_ADD)
        pub.subscribe(self.on_update_user_list, PUB_EVENT_USER_REMOVE)
        self.output_path_btn.Enable(False)

    def on_close(self, evt, force: bool = False):
        """Close window"""
        try:
            pub.unsubscribe(self.on_update_user_list, PUB_EVENT_USER_ADD)
            pub.unsubscribe(self.on_update_user_list, PUB_EVENT_USER_REMOVE)
        except TopicNameError:
            pass
        LOGGER.debug("Toredown dialog")
        super(PanelDatasetInformation, self).on_close(evt, force)

    def make_panel(self):
        """Make panel gui."""
        # make elements
        panel = wx.Panel(self, wx.ID_ANY)

        document_value = make_static_text(panel, "Document title:")
        self.document_value = make_static_text(panel, "")
        set_tooltip(self.document_value, "Title of the document")

        base_dir_value = make_static_text(panel, "Base output directory:")
        self.base_dir_value = wx.TextCtrl(panel, wx.ID_ANY, "", style=wx.TE_READONLY)
        set_tooltip(self.base_dir_value, "Base output directory - this path should not include the `FILENAME.origami`.")

        self.output_path_btn = make_bitmap_btn(panel, wx.ID_ANY, self._icons.folder)
        self.output_path_btn.Bind(wx.EVT_BUTTON, self.on_select_output)
        set_tooltip(self.output_path_btn, "Select base output directory")

        file_dir_value = make_static_text(panel, "Dataset directory:")
        self.file_dir_value = wx.TextCtrl(panel, wx.ID_ANY, "")
        self.file_dir_value.Bind(wx.EVT_TEXT, self.on_update_output)
        set_tooltip(
            self.file_dir_value,
            "Dataset name - this path should include `.origami` extension and will be joined together with "
            "`base output directory`",
        )

        output_value = make_static_text(panel, "Output path:")
        self.output_value = wx.TextCtrl(panel, wx.ID_ANY, "", style=wx.TE_READONLY)
        set_tooltip(
            self.output_value, "Full output directory - combination of `base output directory` and `dataset directory`"
        )

        users_value = make_static_text(panel, "Users:")
        self.users_value = wx.ComboBox(panel, -1, choices=USERS.user_list, style=wx.CB_READONLY)
        set_tooltip(self.users_value, "Select user you would like to associate with the dataset")

        notes_value = make_static_text(panel, "Notes:")
        self.notes_value = wx.TextCtrl(panel, wx.ID_ANY, "", size=(-1, 75))
        set_tooltip(self.notes_value, "Notes about the dataset")

        paths_value = make_static_text(panel, "Paths:")
        self.paths_value = PathsVListBox(panel, wx.ID_ANY, size=(-1, 100))
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.on_path_click, self.paths_value)
        set_tooltip(
            paths_value, "List of paths associated with this document. Paths that are missing are highlighted in red."
        )

        self.locate_btn = make_bitmap_btn(panel, wx.ID_ANY, self._icons.locate)
        self.locate_btn.Bind(wx.EVT_BUTTON, self.on_locate_path)
        set_tooltip(self.locate_btn, "Locate currently selected item somewhere on your hard drive")

        self.fix_btn = make_bitmap_btn(panel, wx.ID_ANY, self._icons.fix)
        self.fix_btn.Bind(wx.EVT_BUTTON, self.on_fix_path)
        set_tooltip(
            self.fix_btn,
            "Fix any/all paths in the list by selecting base path. Paths will be searched within the directory and if "
            "found, updated in the document.",
        )

        self.add_btn = make_bitmap_btn(panel, wx.ID_ANY, self._icons.add)
        self.add_btn.Bind(wx.EVT_BUTTON, self.on_add_user_account)
        set_tooltip(self.add_btn, "Add new user")

        self.ok_btn = wx.Button(panel, wx.ID_OK, "OK", size=(-1, -1))
        self.ok_btn.Bind(wx.EVT_BUTTON, self.on_ok)
        set_tooltip(self.ok_btn, "Import dataset")

        self.cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Close", size=(-1, -1))
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_close)
        set_tooltip(self.cancel_btn, "Close window")

        info_btn = self.make_info_button(panel)

        btn_sizer = wx.BoxSizer()
        btn_sizer.Add(self.ok_btn)
        btn_sizer.AddSpacer(5)
        btn_sizer.Add(self.cancel_btn)

        output_sizer = wx.BoxSizer()
        output_sizer.Add(self.base_dir_value, 1, wx.EXPAND)
        output_sizer.AddSpacer(5)
        output_sizer.Add(self.output_path_btn)

        add_sizer = wx.BoxSizer()
        add_sizer.Add(self.users_value, 1, wx.EXPAND)
        add_sizer.AddSpacer(5)
        add_sizer.Add(self.add_btn)

        _paths_btn_sizer = wx.BoxSizer(wx.VERTICAL)
        _paths_btn_sizer.Add(self.locate_btn)
        _paths_btn_sizer.AddSpacer(5)
        _paths_btn_sizer.Add(self.fix_btn)

        paths_sizer = wx.BoxSizer()
        paths_sizer.Add(self.paths_value, 1, wx.EXPAND)
        paths_sizer.AddSpacer(5)
        paths_sizer.Add(_paths_btn_sizer, 0, wx.ALIGN_TOP)

        # pack elements
        grid = wx.GridBagSizer(5, 5)
        n = 0
        grid.Add(document_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.document_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(base_dir_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(output_sizer, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(file_dir_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.file_dir_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(output_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.output_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(users_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(add_sizer, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(notes_value, (n, 0), flag=wx.ALIGN_TOP | wx.ALIGN_RIGHT)
        grid.Add(self.notes_value, (n, 1), flag=wx.EXPAND)
        grid.AddGrowableRow(n, 1)
        n += 1
        grid.Add(paths_value, (n, 0), flag=wx.ALIGN_TOP | wx.ALIGN_RIGHT)
        grid.Add(paths_sizer, (n, 1), flag=wx.EXPAND)
        grid.AddGrowableRow(n, 1)
        grid.AddGrowableCol(1, 1)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)
        main_sizer.Add(info_btn, 0, wx.ALIGN_RIGHT | wx.ALL, 3)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def _on_get_dlg_handle(self, path: str):
        """Get file or directory handle"""
        exists = os.path.exists(path)
        if is_dir(path):
            dlg = wx.DirDialog(
                wx.GetTopLevelParent(self),
                "Please select new location of the directory",
                style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST,
            )
            if exists:
                dlg.SetPath(path)
        else:
            dlg = wx.FileDialog(
                wx.GetTopLevelParent(self),
                "Please select new location of the file",
                style=wx.FD_DEFAULT_STYLE | wx.FD_FILE_MUST_EXIST,
            )
            if exists:
                dlg.SetPath(path)
        return dlg

    def on_path_click(self, evt):
        """Select path on the listbox"""
        path = evt.GetString()

        new_path = None

        # get dialog and new path
        dlg = self._on_get_dlg_handle(path)
        if dlg.ShowModal() == wx.ID_OK:
            new_path = dlg.GetPath()
        dlg.Destroy()

        # update path in the UI
        if new_path is not None:
            self.paths_value.update_item(evt.GetInt(), new_path)

    def on_locate_path(self, _evt):
        """Locate currently selected item on the hard drive"""
        print("on_locate_path")

    def on_auto_fix_path(self, _evt):
        """Locate currently selected item on the hard drive"""
        print("on_auto_fix_path")

    def on_fix_path(self, _evt):
        """Fix path"""
        print("on_fix_path")

    def setup_document(self, document_title: str):
        """Setup document"""
        document = ENV.on_get_document(document_title)
        if document:
            base_dir, out_dir = os.path.split(document.path)
            self.file_dir_value.SetValue(out_dir)
            self.base_dir_value.SetValue(base_dir)
            self.output_value.SetValue(document.path)
            self.output_path_btn.Enable()

    def on_select_output(self, _evt):
        """Select directory where the dataset should be moved to"""
        path = self.base_dir_value.GetValue()
        dlg = wx.DirDialog(
            wx.GetTopLevelParent(self),
            "Please select output directory",
            style=wx.DD_DEFAULT_STYLE | ~wx.DD_DIR_MUST_EXIST,
        )
        if os.path.exists(path):
            dlg.SetPath(path)

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
        dlg.Destroy()
        self.base_dir_value.SetValue(path)

    def on_update_output(self, _evt):
        """Update output directory"""
        self.output_value.SetValue(self.output_dir)

    def on_ok(self, evt):
        """Close window gracefully"""
        document = ENV.on_get_document()
        if document is None:
            return

        # get data
        path = self.output_dir
        user = USERS.get_user(self.full_name)
        notes = self.notes_value.GetValue()

        # add metadata
        document.add_config("about", dict(user=user, notes=notes))

        # move directory
        if document.path != path:
            document.move(path)

        super(PanelDatasetInformation, self).on_ok(evt)

    def on_update_user_list(self):
        """Update list of users"""
        user_list = USERS.user_list
        current_user = self.users_value.GetStringSelection()
        self.users_value.Clear()
        self.users_value.SetItems(user_list)
        idx = self.users_value.FindString(current_user)
        if idx != -1:
            self.users_value.SetSelection(idx)

    def on_add_user_account(self, _evt):
        """Add user account"""
        from origami.gui_elements.dialog_users import DialogAddUser

        dlg = DialogAddUser(self)
        dlg.Show()


if __name__ == "__main__":

    def _main():

        app = wx.App()
        ex = PanelDatasetInformation(None, None, None, None, debug=True)
        ex.paths_value.set_items(
            ["D:\surfdrive\Shared\Lab-PCs", "D:\surfdrive\Shared\Lab-PCs.raw", "D:\surfdrive\Shared\Lab-PCs"]
        )

        ex.Show()
        app.MainLoop()

    _main()
