"""Dialog allowing selection of multiple directories"""
# Standard library imports
import os
import logging

# Third-party imports
import wx
from natsort import natsorted

# Local imports
from origami.styles import Dialog
from origami.styles import ListCtrl
from origami.utils.path import get_subdirectories
from origami.gui_elements.helpers import TableConfig
from origami.gui_elements.helpers import set_tooltip

LOGGER = logging.getLogger(__name__)


class TableColumnIndex:
    """Table indexer"""

    check = 0
    filename = 1
    path = 2


class DialogMultiDirPicker(Dialog):
    """Select multiple directories dialog"""

    # lists
    FILELIST_ALL_CONFIG = TableConfig()
    FILELIST_ALL_CONFIG.add("", "check", "bool", 25)
    FILELIST_ALL_CONFIG.add("filename", "filename", "str", 300)
    FILELIST_ALL_CONFIG.add("path", "path", "str", 0, hidden=True)
    FILELIST_SELECT_CONFIG = FILELIST_ALL_CONFIG
    TABLE_COLUMN_INDEX = TableColumnIndex

    # ui elements
    path_value = None
    directory_btn = None
    add_btn = None
    remove_btn = None
    ok_btn = None
    cancel_btn = None
    filelist_all = None
    filelist_select = None

    def __init__(self, parent, title="Select files/directories", last_dir="", extension=None):
        """This panel serves as a replacement for the MultiDirDialog provided by wxPython - the reason being that MDD
        can sporadically crash the UI if user clicks in the wrong place. I have tried tracing it but annoyingly I cannot
        figure out what is causing it..."""
        Dialog.__init__(self, parent, title=title, bind_key_events=False)
        self.view = parent

        # private attributes
        self._extension = extension
        self._path = last_dir
        self._filelist_select = dict()
        self._filelist_all = dict()

        self.output_list = []

        self.make_gui()
        self.setup()

        # setup layout
        self.SetSize((800, 500))
        self.Layout()
        self.CentreOnScreen()
        self.Show(True)
        self.SetFocus()

    def setup(self):
        """Setup UI before displayed to the user"""
        self._populate_all_list()

    def ShowModal(self):
        """Simplified ShowModal(), returning strings 'ok' or 'cancel'. """
        result = super().ShowModal()

        output = "cancel"
        if result == wx.ID_OK:
            output = "ok"

        return output

    def get_paths(self):
        """Compatibility method"""
        return self.get_selected_items()

    @property
    def last_path(self):
        """Return the last path"""
        return self._path

    def on_ok(self, _evt):
        """Exit with OK statement"""
        self.output_list = self.get_selected_items()
        if self.IsModal():
            self.EndModal(wx.ID_OK)
        else:
            self.Destroy()

    def on_close(self, evt, force: bool = False):
        """Destroy this frame"""
        if self.IsModal():
            self.EndModal(wx.ID_NO)
        else:
            self.Destroy()

    def make_panel(self):
        """Make panel"""
        panel = wx.Panel(self, -1, size=(-1, -1))

        msg = (
            "Please specify path and select files/directories on the left-hand side before pressing the '>>>' "
            " button. You can easily remove items from the list by selecting them on the right-hand side and"
            " pressing the '<<<' button."
        )

        info_label = wx.StaticText(panel, -1, msg)
        info_label.Wrap(750)

        self.make_table(panel)

        horizontal_line_1 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        path_label = wx.StaticText(panel, -1, "Directory")
        self.path_value = wx.TextCtrl(panel, -1, self._path)
        self.path_value.Bind(wx.EVT_TEXT, self._populate_all_list)
        set_tooltip(self.path_value, "Base directory where to look for other directories.")

        self.directory_btn = wx.Button(panel, wx.ID_OK, "Directory...", size=(-1, -1))
        self.directory_btn.Bind(wx.EVT_BUTTON, self.on_select_directory)
        set_tooltip(self.directory_btn, "Click here to select base directory.")

        self.add_btn = wx.Button(panel, wx.ID_OK, ">>>", size=(-1, -1))
        self.add_btn.Bind(wx.EVT_BUTTON, self.on_add)
        set_tooltip(self.add_btn, "Add currently selected directories to the `hold` list.")

        self.remove_btn = wx.Button(panel, wx.ID_OK, "<<<", size=(-1, -1))
        self.remove_btn.Bind(wx.EVT_BUTTON, self.on_remove)
        set_tooltip(self.remove_btn, "Remove the currently selected directories from the `hold` list.")

        self.ok_btn = wx.Button(panel, wx.ID_OK, "Select", size=(-1, -1))
        self.ok_btn.Bind(wx.EVT_BUTTON, self.on_ok)
        set_tooltip(self.ok_btn, "Select directories (currently selected in the `hold` list and close the window")

        self.cancel_btn = wx.Button(panel, wx.ID_OK, "Cancel", size=(-1, -1))
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_close)
        set_tooltip(self.cancel_btn, "Close the window without making selection")

        table_control_grid = wx.BoxSizer(wx.VERTICAL)
        table_control_grid.Add(self.add_btn, 1, wx.ALIGN_CENTER)
        table_control_grid.Add(self.remove_btn, 1, wx.ALIGN_CENTER)

        btn_grid = wx.GridBagSizer(2, 2)
        n = 0
        btn_grid.Add(self.ok_btn, (n, 0), flag=wx.ALIGN_CENTER)
        btn_grid.Add(self.cancel_btn, (n, 1), flag=wx.ALIGN_CENTER)

        path_sizer = wx.BoxSizer()
        path_sizer.Add(path_label, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        path_sizer.Add(self.path_value, 1, wx.EXPAND, 0)
        path_sizer.Add(self.directory_btn, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        table_sizer = wx.BoxSizer()
        table_sizer.Add(self.filelist_all, 1, wx.EXPAND, 0)
        table_sizer.Add(table_control_grid, 0, wx.ALIGN_CENTER, 0)
        table_sizer.Add(self.filelist_select, 1, wx.EXPAND, 0)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(info_label, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        main_sizer.Add(path_sizer, 0, wx.EXPAND | wx.ALL, 10)
        main_sizer.Add(table_sizer, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(horizontal_line_1, 0, wx.ALIGN_CENTER_HORIZONTAL, 10)
        main_sizer.Add(btn_grid, 0, wx.ALIGN_CENTER_HORIZONTAL, 10)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def make_table(self, panel):
        """Initialize file lists"""

        def _make_table(iterator):
            filelist = ListCtrl(panel, style=wx.LC_REPORT | wx.LC_VRULES, column_info=iterator)
            for order, item in iterator.items():
                name = item["name"]
                width = 0 if not item["show"] else item["width"]
                filelist.InsertColumn(order, name, width=width, format=wx.LIST_FORMAT_LEFT)
                filelist.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))

            return filelist

        # initialize filelist with all files/directories in the folder
        self.filelist_all = _make_table(self.FILELIST_ALL_CONFIG)
        self.filelist_select = _make_table(self.FILELIST_SELECT_CONFIG)

        LOGGER.debug("Initialized file lists")

    def on_select_directory(self, _):
        """Select directory where to start searching for files/directories"""
        dlg = wx.DirDialog(self.view, "Choose directory")

        path = None
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
        dlg.Destroy()

        self._on_select_directory(path)

    def _on_select_directory(self, path):
        """Select directory where the files/directories can be found"""
        if path is None:
            return

        # clear previous list
        self.filelist_all.on_clear_table_all(None, False)
        if path in self._filelist_all:
            self._filelist_all[path] = []
        self.path_value.SetValue(path)
        LOGGER.info(f"Selected {path}")

    def on_add(self, _):
        """Add currently selected items (on the lhs) to the rhs"""
        item_list = self.filelist_all.get_all_checked()
        self.populate_select_list(item_list)

    def on_remove(self, _):
        """Remove currently selected items (on the rhs) from the list"""
        item_list = self.filelist_select.get_all_checked()
        i = 0
        for item_info in item_list:
            path = item_info["path"]
            filename = item_info["filename"]
            if filename in self._filelist_select[path]:
                self._filelist_select[path].remove(filename)
                self.filelist_select.remove_by_keys(["filename", "path"], [filename, path])
                i += 1
        logging.info(f"Removed {i} items")

    def _populate_all_list(self, _=None):
        """Populate filelist (lhs) with new items by first collecting subdirectories of the
        self._path path
        """
        self._path = self.path_value.GetValue()
        if self._path in ["", "None", None] or not os.path.exists(self._path):
            LOGGER.warning(f"Path `{self._path}` does not exist")
            return

        if self._path not in self._filelist_all:
            self._filelist_all[self._path] = []
        if self._path not in self._filelist_select:
            self._filelist_select[self._path] = []

        directories = get_subdirectories(self._path, self._extension)
        self.populate_all_list(directories)

    def populate_all_list(self, item_list):
        """Populate filelist (lhs) with new items"""
        if not item_list:
            LOGGER.warning("Filelist was empty")
            return

        for filename in item_list:
            if filename not in self._filelist_all[self._path]:
                self.filelist_all.Append(["", filename, self._path])
                # self._filelist_all[self._path].append(filename)

    def populate_select_list(self, item_list):
        """Populate filelist (rhs) with items that have been selected on the lhs"""
        if not item_list:
            LOGGER.warning("You must select at least one item in the left-hand side")
            return

        for item_info in item_list:
            filename = item_info["filename"]
            if filename not in self._filelist_select[self._path]:
                self.filelist_select.Append(["", filename, self._path])
                self._filelist_select[self._path].append(filename)
        self.filelist_select.on_check_all(True)

    def get_selected_items(self):
        """Get currently selected items in the filelist"""
        item_count = self.filelist_select.GetItemCount()

        # generate list of document_title and dataset_name
        item_list = []
        for item_id in range(item_count):
            information = self.on_get_item_information(item_id)
            if information["select"]:
                item_list.append(os.path.join(information["path"], information["filename"]))

        return natsorted(item_list)

    def on_get_item_information(self, item_id):
        """Get item information from the lhs table"""
        return self.filelist_select.on_get_item_information(item_id)


def _main():

    from origami.app import App

    app = App()
    ex = DialogMultiDirPicker(None)
    ex.ShowModal()
    # ex.Show()
    app.MainLoop()


if __name__ == "__main__":
    _main()
