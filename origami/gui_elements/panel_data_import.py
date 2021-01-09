"""Panel used to import new data into ORIGAMI"""
# Standard library imports
import os
import logging
from functools import partial

# Third-party imports
import wx
from pubsub import pub
from pubsub.core import TopicNameError

# Local imports
from origami.styles import MiniFrame
from origami.config.config import USERS
from origami.config.config import PUB_EVENT_USER_ADD
from origami.config.config import PUB_EVENT_USER_REMOVE
from origami.config.enabler import APP_ENABLER
from origami.config.environment import ENV
from origami.config.environment import PUB_EVENT_ENV_ADD
from origami.gui_elements.helpers import set_tooltip
from origami.gui_elements.helpers import make_menu_item
from origami.gui_elements.helpers import make_bitmap_btn
from origami.gui_elements.helpers import make_static_text

LOGGER = logging.getLogger(__name__)


class PanelDatasetImport(MiniFrame):
    """Import dataset."""

    path_value, output_value, notes_value, users_value, ok_btn, cancel_btn = None, None, None, None, None, None
    import_btn, add_btn, output_path_btn, base_dir_value, file_dir_value = None, None, None, None, None

    def __init__(self, parent, icons, presenter, debug: bool = False):
        MiniFrame.__init__(self, parent, title="Import Dataset...", style=wx.DEFAULT_FRAME_STYLE & ~wx.MAXIMIZE_BOX)
        self.parent = parent
        self.presenter = presenter
        self._icons = self._get_icons(icons)
        self._debug = debug

        # make ui
        self.make_gui()
        self.SetSize((800, 400))
        self.CenterOnParent()

        # bind events
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.setup()

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
        pub.subscribe(self.on_import_dataset, "file.dataset.import")
        pub.subscribe(self.on_load_dataset, PUB_EVENT_ENV_ADD)
        self.output_path_btn.Enable(False)

    def on_close(self, evt, force: bool = False):
        """Close window"""
        try:
            pub.unsubscribe(self.on_update_user_list, PUB_EVENT_USER_ADD)
            pub.unsubscribe(self.on_update_user_list, PUB_EVENT_USER_REMOVE)
            pub.unsubscribe(self.on_import_dataset, "file.dataset.import")
            pub.unsubscribe(self.on_load_dataset, PUB_EVENT_ENV_ADD)
        except TopicNameError:
            pass
        LOGGER.debug("Toredown dialog")
        super(PanelDatasetImport, self).on_close(evt, force)

    def make_panel(self):
        """Make panel gui."""
        # make elements
        panel = wx.Panel(self, wx.ID_ANY)

        path_value = make_static_text(panel, "File path:")
        self.path_value = wx.TextCtrl(panel, wx.ID_ANY, "", style=wx.TE_READONLY)
        set_tooltip(self.path_value, "Path to the dataset")

        self.import_btn = make_bitmap_btn(panel, wx.ID_ANY, self._icons.wand)
        self.import_btn.Bind(wx.EVT_BUTTON, self.on_show_menu)
        set_tooltip(self.import_btn, "Select directory/file to import")

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

        notes_value = make_static_text(panel, "Notes:")
        self.notes_value = wx.TextCtrl(panel, wx.ID_ANY, "", size=(-1, 100))
        set_tooltip(self.notes_value, "Notes about the dataset")

        users_value = make_static_text(panel, "Users:")
        self.users_value = wx.ComboBox(panel, -1, choices=USERS.user_list, style=wx.CB_READONLY)
        set_tooltip(self.users_value, "Select user you would like to associate with the dataset")

        self.add_btn = make_bitmap_btn(panel, wx.ID_ANY, self._icons.add)
        self.add_btn.Bind(wx.EVT_BUTTON, self.on_add_user_account)
        set_tooltip(self.add_btn, "Add new user")

        self.ok_btn = wx.Button(panel, wx.ID_OK, "OK", size=(-1, -1))
        self.ok_btn.Bind(wx.EVT_BUTTON, self.on_ok)
        set_tooltip(self.ok_btn, "Import dataset")

        self.cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Close", size=(-1, -1))
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_close)
        set_tooltip(self.cancel_btn, "Close window")

        btn_sizer = wx.BoxSizer()
        btn_sizer.Add(self.ok_btn)
        btn_sizer.AddSpacer(5)
        btn_sizer.Add(self.cancel_btn)

        path_sizer = wx.BoxSizer()
        path_sizer.Add(self.path_value, 1, wx.EXPAND)
        path_sizer.AddSpacer(5)
        path_sizer.Add(self.import_btn)

        output_sizer = wx.BoxSizer()
        output_sizer.Add(self.base_dir_value, 1, wx.EXPAND)
        output_sizer.AddSpacer(5)
        output_sizer.Add(self.output_path_btn)

        add_sizer = wx.BoxSizer()
        add_sizer.Add(self.users_value, 1, wx.EXPAND)
        add_sizer.AddSpacer(5)
        add_sizer.Add(self.add_btn)

        # pack elements
        grid = wx.GridBagSizer(5, 5)
        n = 0
        grid.Add(path_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(path_sizer, (n, 1), flag=wx.EXPAND)
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
        grid.AddGrowableCol(1, 1)
        grid.AddGrowableRow(n, 1)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def on_show_menu(self, _evt):
        """Show import menu"""
        menu = wx.Menu()
        menu_file_waters_ms = make_menu_item(
            parent=menu, text="Open Waters file (.raw) [MS only]", bitmap=self._icons.micromass
        )
        menu_file_waters_ms.Enable(APP_ENABLER.ALLOW_WATERS_EXTRACTION)

        menu_file_waters_imms = make_menu_item(
            parent=menu, text="Open Waters file (.raw) [IM-MS]", bitmap=self._icons.micromass
        )
        menu_file_waters_imms.Enable(APP_ENABLER.ALLOW_WATERS_EXTRACTION)

        menu_file_waters_origami = make_menu_item(
            parent=menu, text="Open Waters file (.raw) [ORIGAMI-MS; CIU]", bitmap=self._icons.micromass
        )
        menu_file_waters_origami.Enable(APP_ENABLER.ALLOW_WATERS_EXTRACTION)

        menu_file_thermo = make_menu_item(parent=menu, text="Open Thermo file (.RAW)", bitmap=self._icons.thermo)
        menu_file_thermo.Enable(APP_ENABLER.ALLOW_THERMO_EXTRACTION)

        menu_file_text_ms = make_menu_item(
            parent=menu, text="Open mass spectrum file(s) (.csv; .txt; .tab)", bitmap=self._icons.csv
        )
        menu_file_text_heatmap = make_menu_item(
            parent=menu, text="Open heatmap file(s) (.csv; .txt; .tab)", bitmap=self._icons.csv
        )

        # bind events
        if not self._debug:
            self.Bind(wx.EVT_MENU, partial(self.data_handling.on_open_multiple_text_ms_fcn, True), menu_file_text_ms)
            self.Bind(
                wx.EVT_MENU, partial(self.data_handling.on_open_multiple_text_2d_fcn, True), menu_file_text_heatmap
            )
            self.Bind(wx.EVT_MENU, self.data_handling.on_open_thermo_file_fcn, menu_file_thermo)
            self.Bind(wx.EVT_MENU, self.data_handling.on_open_waters_raw_ms_fcn, menu_file_waters_ms)
            self.Bind(wx.EVT_MENU, self.data_handling.on_open_waters_raw_imms_fcn, menu_file_waters_imms)
            self.Bind(wx.EVT_MENU, self.data_handling.on_open_waters_raw_imms_fcn, menu_file_waters_origami)

        # make menu
        menu.Append(menu_file_waters_ms)
        menu.Append(menu_file_waters_imms)
        menu.Append(menu_file_waters_origami)
        menu.AppendSeparator()
        menu.Append(menu_file_thermo)
        menu.AppendSeparator()
        menu.Append(menu_file_text_ms)
        menu.Append(menu_file_text_heatmap)

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def on_import_dataset(self, path: str):
        """Import dataset"""
        self.path_value.SetValue(path)

    def on_load_dataset(self, document_title: str):
        """Dataset was imported"""
        document = ENV.on_get_document(document_title)
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

        super(PanelDatasetImport, self).on_ok(evt)

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


if __name__ == "__main__":  # pragma: no cover

    def _main():

        from origami.app import App

        app = App()
        ex = PanelDatasetImport(None, None, None, debug=True)

        ex.Show()
        app.MainLoop()

    _main()
