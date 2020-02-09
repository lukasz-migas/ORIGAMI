# __author__ lukasz.g.migas
import os
import wx
import wx.lib.agw.multidirdialog as MDD

from utils.path import clean_up_MDD_path

from styles import Dialog
from styles import ListCtrl

from utils.path import get_subdirectories


class DialogMultiDirectoryPicker(MDD.MultiDirDialog):
    def __init__(
        self, parent, title="Choose directories...", default_path=None, style=MDD.DD_MULTIPLE | MDD.DD_DIR_MUST_EXIST
    ):

        MDD.MultiDirDialog.__init__(self, parent=parent, title=title, defaultPath=default_path, agwStyle=style)

    def ShowModal(self):
        """Simplified ShowModal(), returning strings 'ok' or 'cancel'. """
        result = MDD.MultiDirDialog.ShowModal(self)

        output = "cancel"
        if result == wx.ID_OK:
            output = "ok"

        return output

    def GetPaths(self, *args, **kwargs):
        """Clean-up the list of paths that is returned from the GetPaths function"""
        path_list = MDD.MultiDirDialog.GetPaths(self, *args, **kwargs)
        return [clean_up_MDD_path(path) for path in path_list]


class DialogMultiDirPicker(Dialog):

    # lists
    FILELIST_ALL = {
        0: {"name": "", "tag": "check", "type": "bool", "width": 20, "show": True},
        1: {"name": "filename", "tag": "filename", "type": "str", "width": 300, "show": True},
        2: {"name": "path", "tag": "path", "type": "str", "width": 0, "show": False},
    }

    FILELIST_SELECT = {
        0: {"name": "", "tag": "check", "type": "bool", "width": 20, "show": True},
        1: {"name": "filename", "tag": "filename", "type": "str", "width": 300, "show": True},
        2: {"name": "path", "tag": "path", "type": "str", "width": 0, "show": False},
    }

    def __init__(self, parent, last_dir="", extension=None):
        Dialog.__init__(self, parent, title="Select files/directories....", bind_key_events=False)
        self.view = parent

        # private attributes
        self._extension = extension
        self._path = last_dir
        self._filelist_select = dict()
        self._filelist_all = dict()

        self.output_list = []

        self.make_gui()

        # setup layout
        self.SetSize((800, 500))
        self.Layout()

        self.CentreOnScreen()
        self.Show(True)
        self.SetFocus()

    def ShowModal(self):
        """Simplified ShowModal(), returning strings 'ok' or 'cancel'. """
        result = MDD.MultiDirDialog.ShowModal(self)

        output = "cancel"
        if result == wx.ID_OK:
            output = "ok"

        return output

    def GetPaths(self):
        """Compatibility method"""
        return self.get_selected_items()

    def on_close(self, evt):
        """Destroy this frame"""
        self.EndModal(wx.ID_NO)

    def on_ok(self, evt):
        self.output_list = self.get_selected_items()
        self.EndModal(wx.ID_OK)

    def make_panel(self):
        panel = wx.Panel(self, -1, size=(-1, -1))

        msg = ("Please specify path and select files/directories on the left-hand side before pressing the '>>>' "
               " button. You can easily remove items from the list by selecting them on the right-hand side and"
               " pressing the '<<<' button.")

        info_label = wx.StaticText(panel, -1, msg)
        info_label.Wrap(750)

        self.make_listctrl_panel(panel)

        horizontal_line_1 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        path_label = wx.StaticText(panel, -1, "Directory")
        self.path_value = wx.TextCtrl(panel, -1, self._path)
        self.path_value.Bind(wx.EVT_TEXT, self._populate_all_list)

        self.directory_btn = wx.Button(panel, wx.ID_OK, "Directory...", size=(-1, 22))
        self.directory_btn.Bind(wx.EVT_BUTTON, self.on_select_directory)

        self.add_btn = wx.Button(panel, wx.ID_OK, ">>>", size=(-1, 22))
        self.add_btn.Bind(wx.EVT_BUTTON, self.on_add)

        self.remove_btn = wx.Button(panel, wx.ID_OK, "<<<", size=(-1, 22))
        self.remove_btn.Bind(wx.EVT_BUTTON, self.on_remove)

        self.ok_btn = wx.Button(panel, wx.ID_OK, "Select", size=(-1, 22))
        self.ok_btn.Bind(wx.EVT_BUTTON, self.on_ok)

        self.cancel_btn = wx.Button(panel, wx.ID_OK, "Cancel", size=(-1, 22))
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_close)

        table_control_grid = wx.BoxSizer(wx.VERTICAL)
        table_control_grid.Add(self.add_btn, 1, wx.ALIGN_CENTER)
        table_control_grid.Add(self.remove_btn, 1, wx.ALIGN_CENTER)

        btn_grid = wx.GridBagSizer(2, 2)
        n = 0
        btn_grid.Add(self.ok_btn, (n, 0), flag=wx.ALIGN_CENTER)
        btn_grid.Add(self.cancel_btn, (n, 1), flag=wx.ALIGN_CENTER)

        path_sizer = wx.BoxSizer(wx.HORIZONTAL)
        path_sizer.Add(path_label, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        path_sizer.Add(self.path_value, 1, wx.EXPAND, 0)
        path_sizer.Add(self.directory_btn, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        table_sizer = wx.BoxSizer(wx.HORIZONTAL)
        table_sizer.Add(self.filelist_all, 1, wx.EXPAND, 0)
        table_sizer.Add(table_control_grid, 0, wx.ALIGN_CENTER, 0)
        table_sizer.Add(self.filelist_select, 1, wx.EXPAND, 0)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(info_label, 0, wx.ALIGN_CENTER, 10)
        main_sizer.Add(path_sizer, 0, wx.EXPAND, 1)
        main_sizer.Add(table_sizer, 1, wx.EXPAND, 1)
        main_sizer.Add(horizontal_line_1, 0, wx.ALIGN_CENTER_HORIZONTAL, 10)
        main_sizer.Add(btn_grid, 0, wx.ALIGN_CENTER_HORIZONTAL, 10)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def make_listctrl_panel(self, panel):
        """Initilize filelists"""

        # intilize filelist with all files/directories in the folder
        self.filelist_all = ListCtrl(panel, style=wx.LC_REPORT | wx.LC_VRULES, column_info=self.FILELIST_ALL)
        for col in range(len(self.FILELIST_ALL)):
            item = self.FILELIST_ALL[col]
            order = col
            name = item["name"]
            width = 0
            if item["show"]:
                width = item["width"]
            self.filelist_all.InsertColumn(order, name, width=width, format=wx.LIST_FORMAT_CENTER)
            self.filelist_all.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))

        # intilize filelist with select files/directories in the folder
        self.filelist_select = ListCtrl(panel, style=wx.LC_REPORT | wx.LC_VRULES, column_info=self.FILELIST_SELECT)
        for col in range(len(self.FILELIST_SELECT)):
            item = self.FILELIST_SELECT[col]
            order = col
            name = item["name"]
            width = 0
            if item["show"]:
                width = item["width"]
            self.filelist_select.InsertColumn(order, name, width=width, format=wx.LIST_FORMAT_CENTER)
            self.filelist_select.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))

    def on_select_directory(self, evt):
        dlg = wx.DirDialog(self.view, "Choose directory", style=wx.DD_DEFAULT_STYLE)

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            # clear previous list
            self.filelist_all.on_clear_table_all(None, False)
            if path in self._filelist_all:
                self._filelist_all[path] = []

            self.path_value.SetValue(path)

        dlg.Destroy()

    def on_add(self, evt):
        item_list = self.filelist_all.get_all_checked()
        self.populate_select_list(item_list)

    def on_remove(self, evt):
        item_list = self.filelist_select.get_all_checked()
        i = 0
        for item_info in item_list:
            path = item_info["path"]
            filename = item_info["filename"]
            if filename in self._filelist_select[path]:
                self._filelist_select[path].remove(filename)
                self.filelist_select.remove_by_keys(["filename", "path"],
                                                    [filename, path])
                i += 1
        print(f"Removed {i} items")

    def _populate_all_list(self, _=None):
        self._path = self.path_value.GetValue()

        if self._path not in self._filelist_all:
            self._filelist_all[self._path] = []
        if self._path not in self._filelist_select:
            self._filelist_select[self._path] = []

        directories = get_subdirectories(self._path, self._extension, as_short=True)
        self.populate_all_list(directories)
        
    def populate_all_list(self, item_list):
        if not item_list:
            print("Filelist was empty")
            return

        for filename in item_list:
            if filename not in self._filelist_all[self._path]:
                self.filelist_all.Append(["", filename, self._path])
                self._filelist_all[self._path].append(filename)

    def populate_select_list(self, item_list):
        if not item_list:
            print("You must select at least one item in the left-hand side")
            return

        for item_info in item_list:
            filename = item_info["filename"]
            if filename not in self._filelist_select[self._path]:
                self.filelist_select.Append(["", filename, self._path])
                self._filelist_select[self._path].append(filename)
        self.filelist_select.on_check_all(True)

    def get_selected_items(self):
        item_count = self.filelist_select.GetItemCount()

        # generate list of document_title and dataset_name
        item_list = []
        for item_id in range(item_count):
            information = self.on_get_item_information(item_id)
            if information["select"]:
                item_list.append(os.path.join(information["path"], information["filename"]))

        return item_list

    def on_get_item_information(self, item_id):
        return self.filelist_select.on_get_item_information(item_id)

