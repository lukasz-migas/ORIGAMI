# Standard library imports
import logging
from abc import abstractmethod
from ast import literal_eval
from enum import IntEnum
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

# Third-party imports
import wx

# Local imports
from origami.styles import ListCtrl
from origami.styles import make_menu_item
from origami.utils.color import round_rgb
from origami.utils.color import get_font_color
from origami.utils.color import get_random_color
from origami.utils.color import get_all_color_types
from origami.utils.color import convert_rgb_1_to_255
from origami.utils.color import convert_rgb_255_to_1
from origami.config.config import CONFIG
from origami.gui_elements.misc_dialogs import DialogBox
from origami.gui_elements.dialog_color_picker import DialogColorPicker

LOGGER = logging.getLogger(__name__)


class TableColumnIndex(IntEnum):
    pass


class TableMixin:
    """Mixin class to add Table controls"""

    # must have name, tag, type, show, id, width
    TABLE_DICT = {}
    TABLE_COLUMN_INDEX = TableColumnIndex
    TABLE_RESERVED = {"hide_all": wx.NewIdRef(), "show_all": wx.NewIdRef()}
    TABLE_STYLE = wx.LC_REPORT | wx.LC_VRULES
    TABLE_KWARGS = dict()
    TABLE_TEXT_ALIGN = wx.LIST_FORMAT_CENTER
    DUPLICATE_ID_CHECK = []
    KEYWORD_ALIAS = {}
    USE_COLOR = True

    # ui attributes
    data_processing = None
    data_handling = None
    data_visualisation = None
    document_tree = None

    def __init__(self, **kwargs):

        self.peaklist = None

    @abstractmethod
    def on_update_document(self, item_id: Optional[int] = None, item_info: Optional[Dict] = None):
        raise NotImplementedError("Must implement method")

    @abstractmethod
    def on_double_click_on_item(self, evt):
        raise NotImplementedError("Must implement method")

    @abstractmethod
    def on_menu_item_right_click(self, evt):
        raise NotImplementedError("Must implement method")

    @staticmethod
    def _check_table(table_dict):
        """Check whether the class-set table is correctly formatted"""
        if not isinstance(table_dict, dict):
            raise ValueError("Table list should be a dictionary")

        tags = []
        for key, value in table_dict.items():
            if not isinstance(key, int):
                raise ValueError("The key value should be an integer")
            if not all([_k in value for _k in ["name", "order", "tag", "type", "id", "show", "width"]]):
                raise ValueError(
                    "The value should contain the following keys: `name, order, tag, type, id, show, width`"
                )
            tags.append(value["tag"])

        if len(set(tags)) != len(table_dict):
            raise ValueError("Expected tags to be unique")

    def make_table(self, table_dict, panel=None):
        if panel is None:
            panel = self
        peaklist = ListCtrl(panel, style=self.TABLE_STYLE, column_info=table_dict, **self.TABLE_KWARGS)

        for order, item in table_dict.items():
            name = item["name"]
            width = item["width"] if item["show"] else 0
            peaklist.InsertColumn(order, name, width=width, format=self.TABLE_TEXT_ALIGN)

        peaklist.Bind(wx.EVT_LEFT_DCLICK, self.on_double_click_on_item)
        peaklist.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.on_menu_item_right_click)
        peaklist.Bind(wx.EVT_LIST_COL_RIGHT_CLICK, self.on_menu_column_right_click)
        # peaklist.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_double_click_on_item)
        return peaklist

    def on_get_item_information(self, item_id: Optional[int] = None):
        """Return basic information about an item - method should be overwritten if want to have access to more
        attributes"""
        if item_id is None:
            item_id = self.peaklist.item_id
        information = self.peaklist.on_get_item_information(item_id)
        return information

    def on_check_selected(self, _evt):
        """Check current item when letter S is pressed on the keyboard"""
        if self.peaklist.item_id is None:
            return

        check = not self.peaklist.IsChecked(self.peaklist.item_id)
        self.peaklist.CheckItem(self.peaklist.item_id, check=check)

    def on_assign_color(self, _evt, item_id=None, give_value=False):
        """Assign new color

        Parameters
        ----------
        _evt : wxPython event
            unused
        item_id : int
            value for item in table
        give_value : bool
            should/not return color
        """

        if item_id is not None:
            self.peaklist.item_id = item_id

        if self.peaklist.item_id is None:
            return

        dlg = DialogColorPicker(self, CONFIG.customColors)
        if dlg.ShowModal() == wx.ID_OK:
            color_255, color_1, font_color = dlg.GetChosenColour()
            CONFIG.customColors = dlg.GetCustomColours()
            self.on_update_value_in_peaklist(self.peaklist.item_id, "color", [color_255, color_1, font_color])

            # update document
            self.on_update_document(self.peaklist.item_id)

            if give_value:
                return color_255
        else:
            try:
                color_255 = convert_rgb_1_to_255(literal_eval(self.on_get_value(value_type="color")), 3)
            except Exception:
                color_255 = next(CONFIG.custom_color_cycle)
            color_255, color_1, font_color = get_all_color_types(color_255, True)
            self.on_update_value_in_peaklist(self.peaklist.item_id, "color", [color_255, color_1, font_color])
            if give_value:
                return color_255

    def on_get_color(self, evt):
        """Convenient method to get new color"""
        dlg = DialogColorPicker(self, CONFIG.customColors)
        if dlg.ShowModal() == wx.ID_OK:
            color_255, color_1, font_color = dlg.GetChosenColour()
            CONFIG.customColors = dlg.GetCustomColours()

            return color_255, color_1, font_color
        return None, None, None

    def on_update_value_in_peaklist(self, item_id, value_type, value):
        if value_type == "color":
            color_255, color_1, font_color = value
            self.peaklist.SetItemBackgroundColour(item_id, color_255)
            self.peaklist.SetItem(item_id, self.TABLE_COLUMN_INDEX.color, str(color_1))
            self.peaklist.SetItemTextColour(item_id, font_color)
        elif value_type == "color_text":
            self.peaklist.SetItemBackgroundColour(item_id, value)
            self.peaklist.SetItem(item_id, self.TABLE_COLUMN_INDEX.color, str(convert_rgb_255_to_1(value)))
            self.peaklist.SetItemTextColour(item_id, get_font_color(value, return_rgb=True))
        else:
            for col_id, col_values in self.TABLE_DICT.items():
                if col_values["tag"] == value_type:
                    self.peaklist.SetItem(item_id, col_id, str(value))
                    break

    def on_get_value(self, value_type="color"):
        """Returns item information for particular key/column"""
        information = self.on_get_item_information(self.peaklist.item_id)
        return information[value_type]

    @property
    def color_list(self):
        """Returns the list of colors in the table"""
        return [self.peaklist.GetItemBackgroundColour(item_id) for item_id in range(self.peaklist.GetItemCount())]

    @property
    def n_rows(self):
        """Returns number of rows/items in the table"""
        return self.peaklist.GetItemCount()

    @property
    def n_columns(self):
        """Returns number of columns in the table"""
        return self.peaklist.GetColumnCount()

    def get_checked_items(self):
        """Return list of indices of items that are checked"""
        checked = []
        for item_id in range(self.n_rows):
            if self.peaklist.IsChecked(item_id):
                checked.append(item_id)
        return checked

    def on_get_unique_color(self, color):
        """Retrieves unique color by checking if current color already exists"""
        return self.on_check_duplicate_colors(color)

    def on_check_duplicate_colors(self, new_color):
        """Check whether newly assigned color is already in the table and if so, return a different one"""
        color_list = self.color_list
        if new_color in color_list:
            color_count = len(CONFIG.custom_color_cycle)
            while color_count > 0:
                new_color = next(CONFIG.custom_color_cycle)
                if new_color not in color_list:
                    break
                color_count -= 1
            if new_color in color_list:
                new_color = get_random_color(True)
        return new_color

    def on_add_to_table(self, add_dict, check_color: bool = True, return_color: bool = False):
        """Add new item(s) to the table

        Parameters
        ----------
        add_dict : Dict
            dictionary with appropriate names: values
        check_color : bool
            if `True`, user/app defined color will be checked against existing values
        return_color : bool
            if `True`, the final color will be returned

        Returns
        -------
        color :
            color of the item in the table
        """
        if self.USE_COLOR:
            color = add_dict.get("color", next(CONFIG.custom_color_cycle))
            if check_color:
                color = self.on_check_duplicate_colors(color)

        self.peaklist.Append(self._parse(add_dict))
        if self.USE_COLOR:
            self.peaklist.SetItemBackgroundColour(self.peaklist.GetItemCount() - 1, color)  # noqa
            font_color = get_font_color(color, return_rgb=True)
            self.peaklist.SetItemTextColour(self.peaklist.GetItemCount() - 1, font_color)
            if return_color:
                return color

    def remove_from_table(self, item_ids: List[int]):
        """
        Parameters
        ----------
        item_ids: Union[List[int], int]
            list of item ids of elements to be removed
        """
        # TODO: add trigger here

        iterator = item_ids if isinstance(item_ids, list) else [item_ids]
        if len(iterator) == 0 or len(iterator) > self.n_rows:
            raise ValueError("List of items to be delete does not appear to be correct")

        n_rows = self.n_rows
        if any([val >= n_rows for val in iterator]):
            raise ValueError("Tried to delete element that no longer exists")

        for item_id in sorted(iterator, reverse=True):
            self.peaklist.DeleteItem(item_id)

    def on_find_item(self, key: str, value: Any):
        """Find item and return its index"""
        for item_id in range(self.n_rows):
            info = self.on_get_item_information(item_id)
            if info[key] == value:
                return item_id
        return -1

    def _parse(self, add_dict):
        """Parse dictionary with key:value pairs so they can be added to the table

        Parameters
        ----------
        add_dict : Dict
            dictionary with appropriate names:values so they can be added to the table

        Returns
        -------
        item_list : List[str]
            list containing stringified values
        """

        def convert(value):
            if col_type == "color" and value:
                if self.peaklist.color_0_to_1:
                    return round_rgb(value)
                return round_rgb(convert_rgb_255_to_1(value))
            return str(value)

        item_list = []
        for column_value in self.TABLE_DICT.values():
            col_tag = column_value["tag"]
            col_type = column_value["type"]
            if col_tag in ["check"]:
                item_list.append("")
            else:
                item_list.append(convert(add_dict.get(col_tag, "")))
        return item_list

    def on_delete_item(self, evt):
        """Delete item from ORIGAMI"""
        item_info = self.on_get_item_information(self.peaklist.item_id)
        if not item_info:
            return
        msg = "Are you sure you would like to delete {}?\nThis action cannot be undone.".format(item_info["document"])
        dlg = DialogBox(kind="Question", msg=msg)
        if dlg == wx.ID_NO:
            LOGGER.info("Delete operation was cancelled")
            return
        self.remove_from_table(item_info["id"])

    def on_delete_selected(self, evt):
        """Delete checked item(s) from ORIGAMI"""
        item_id = self.n_rows - 1
        while item_id >= 0:
            if self.peaklist.IsChecked(item_id):
                item_info = self.on_get_item_information(item_id)
                msg = "Are you sure you would like to delete {}?\nThis action cannot be undone.".format(
                    item_info["document"]
                )
                dlg = DialogBox(msg=msg, kind="Question")
                if dlg == wx.ID_NO:
                    LOGGER.info("Delete operation was cancelled")
                    continue
                self.remove_from_table(item_info["id"])

            item_id -= 1

    def on_delete_all(self, evt):
        msg = "Are you sure you would like to delete all elements from the list?\nThis action cannot be undone."
        dlg = DialogBox(msg=msg, kind="Question")
        if dlg == wx.ID_NO:
            LOGGER.info("Delete operation was cancelled")
            return

        item_id = self.n_rows - 1
        while item_id >= 0:
            item_info = self.on_get_item_information(item_id)
            self.remove_from_table(item_info["id"])
            item_id -= 1

    def delete_row_from_table(self, delete_document_title=None):
        item_id = self.n_rows - 1
        while item_id >= 0:
            item_info = self.on_get_item_information(item_id)

            if item_info["document"] == delete_document_title:
                self.peaklist.DeleteItem(item_id)
            item_id -= 1

    def _on_delete_all_force(self):
        """Forecfully remove all elements without asking for permission"""
        item_id = self.n_rows - 1
        while item_id >= 0:
            item_info = self.on_get_item_information(item_id)
            self.remove_from_table(item_info["id"])
            item_id -= 1

    # noinspection PyUnresolvedReferences
    def on_menu_column_right_click(self, evt):
        """Right-click on column title to show/hide it"""
        menu = wx.Menu()

        for col_id, col_values in self.TABLE_DICT.items():
            # some columns are hidden
            if col_values.get("hidden", False):
                continue
            menu_item = menu.AppendCheckItem(col_values["id"], f"Column: {col_values['name']}")
            menu_item.Check(col_values["show"])
            self.Bind(wx.EVT_MENU, self.on_update_peaklist_table, id=col_values["id"])
        menu.AppendSeparator()
        _ = menu.Append(
            make_menu_item(
                parent=menu,
                evt_id=self.TABLE_RESERVED["hide_all"],
                text="Column: Hide all",
                # bitmap=self.icons.iconsLib["hide_table_16"],
            )
        )
        self.Bind(wx.EVT_MENU, self.on_update_peaklist_table, id=self.TABLE_RESERVED["hide_all"])
        _ = menu.Append(
            make_menu_item(
                parent=menu,
                evt_id=self.TABLE_RESERVED["show_all"],
                text="Column: Restore all",
                # bitmap=self.icons.iconsLib["show_table_16"],
            )
        )
        self.Bind(wx.EVT_MENU, self.on_update_peaklist_table, id=self.TABLE_RESERVED["show_all"])

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def on_update_peaklist_table(self, evt):
        evt_id = evt.GetId()

        # check whether any of the special events was triggered
        hide_all, restore_all = False, False
        if evt_id == self.TABLE_RESERVED["hide_all"]:
            hide_all = True
        elif evt_id == self.TABLE_RESERVED["show_all"]:
            restore_all = True

        for col_id, col_values in self.TABLE_DICT.items():
            if col_values["id"] == evt_id or hide_all or restore_all:
                if col_values.get("hidden", False):
                    continue
                if hide_all:
                    col_shown = False
                elif restore_all:
                    col_shown = True
                else:
                    col_shown = not col_values["show"]
                col_width = 0 if not col_shown else col_values["width"]
                self.peaklist.SetColumnWidth(col_id, col_width)
                self.TABLE_DICT[col_id]["show"] = col_shown

    def on_change_item_colormap(self, evt):
        """Update colormap of item(s)"""
        # get number of checked items
        check_count = 0
        for row in range(self.peaklist.GetItemCount()):
            if self.peaklist.IsChecked(row):
                check_count += 1

        if check_count > len(CONFIG.narrowCmapList):
            colormaps = CONFIG.narrowCmapList
        else:
            colormaps = CONFIG.narrowCmapList + CONFIG.cmaps2

        for row in range(self.peaklist.GetItemCount()):
            if self.peaklist.IsChecked(row):
                self.peaklist.item_id = row
                colormap = colormaps[row]
                self.peaklist.SetStringItem(row, self.TABLE_COLUMN_INDEX.colormap, str(colormap))

                # update document
                try:
                    self.on_update_document()
                except TypeError:
                    print("Please select item")

    def on_change_item_value(self, item_id: int, column_id: int, value: str):
        """Update value in the peaklist"""
        if item_id >= self.n_rows:
            raise ValueError("Cannot set value for the selected item")
        if not isinstance(value, str):
            raise ValueError("`Value` must be a string")
        self.peaklist.SetStringItem(item_id, column_id, value)


# noinspection DuplicatedCode
class TablePanelBase(wx.Panel, TableMixin):
    def __init__(self, parent, icons, presenter):
        """Instantiate class"""
        wx.Panel.__init__(
            self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.Size(300, -1), style=wx.TAB_TRAVERSAL
        )
        TableMixin.__init__(self)

        self.view = parent
        self.presenter = presenter
        self.icons = icons

        self.toolbar = None

        self._check_table(self.TABLE_DICT)
        self.make_panel_gui()
        self.bind_events()

    @abstractmethod
    def make_toolbar(self):
        raise NotImplementedError("Must implement method")

    def bind_events(self):
        """Bind extra events"""

    @staticmethod
    def on_open_info_panel(evt):
        # TODO: add info handler
        LOGGER.error("This function is not implemented yet")

    def make_panel_gui(self):
        """ Make panel GUI """
        # make toolbar
        self.toolbar = self.make_toolbar()
        self.peaklist = self.make_table(self.TABLE_DICT)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        if self.toolbar:
            main_sizer.Add(self.toolbar, 0, wx.EXPAND, 0)
        if self.peaklist:
            main_sizer.Add(self.peaklist, 1, wx.EXPAND, 0)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizer(main_sizer)
        self.SetSize((300, -1))
        self.Layout()


# noinspection DuplicatedCode
class TableMiniFrameBase(wx.MiniFrame, TableMixin):
    def __init__(self, parent, icons, presenter):
        """Instantiate class"""
        wx.MiniFrame.__init__(
            self,
            parent,
            id=wx.ID_ANY,
            pos=wx.DefaultPosition,
            size=wx.Size(300, -1),
            style=wx.RESIZE_BORDER | wx.CLOSE_BOX | wx.CAPTION,
        )
        TableMixin.__init__(self)

        self.view = parent
        self.presenter = presenter
        self.icons = icons

        self.toolbar = None

        self._check_table(self.TABLE_DICT)
        self.make_panel_gui()
        self.bind_events()

    @abstractmethod
    def make_toolbar(self):
        raise NotImplementedError("Must implement method")

    def bind_events(self):
        """Bind extra events"""

    @staticmethod
    def on_open_info_panel(evt):
        # TODO: add info handler
        LOGGER.error("This function is not implemented yet")

    def make_panel_gui(self):
        """ Make panel GUI """
        # make toolbar
        self.toolbar = self.make_toolbar()
        self.peaklist = self.make_table(self.TABLE_DICT)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        if self.toolbar:
            main_sizer.Add(self.toolbar, 0, wx.EXPAND, 0)
        if self.peaklist:
            main_sizer.Add(self.peaklist, 1, wx.EXPAND, 0)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizer(main_sizer)
        self.SetSize((300, -1))
        self.Layout()


class TestPanel(TablePanelBase):
    TABLE_DICT = {
        0: {
            "name": "",
            "order": 0,
            "tag": "check",
            "type": "bool",
            "id": wx.NewIdRef(),
            "show": True,
            "width": 25,
            "hidden": True,
        },
        1: {"name": "column 1", "order": 0, "tag": "c1", "type": "str", "id": wx.NewIdRef(), "show": True, "width": 50},
        2: {"name": "column 2", "order": 0, "tag": "c2", "type": "str", "id": wx.NewIdRef(), "show": True, "width": 50},
        3: {
            "name": "document",
            "order": 0,
            "tag": "document",
            "type": "str",
            "id": wx.NewIdRef(),
            "show": True,
            "width": 50,
        },
    }

    def on_double_click_on_item(self, evt):
        pass

    def on_menu_item_right_click(self, evt):
        pass

    def menu_column_right_click(self, evt):
        pass

    def make_toolbar(self):
        pass

    def on_update_document(self, item_id: Optional[int] = None, item_info: Optional[Dict] = None):
        pass


class ExampleFrame(wx.MiniFrame):
    def __init__(self, parent):
        wx.MiniFrame.__init__(self, parent, style=wx.RESIZE_BORDER | wx.CLOSE_BOX | wx.CAPTION)
        self.panel = TestPanel(self, None, None)
        add_btn = wx.Button(self, wx.ID_ANY, "Add")
        self.Bind(wx.EVT_BUTTON, self.add_item, add_btn)

        remove_btn = wx.Button(self, wx.ID_ANY, "Remove")
        self.Bind(wx.EVT_BUTTON, self.panel.on_delete_item, remove_btn)

        remove_selected_btn = wx.Button(self, wx.ID_ANY, "Remove selected")
        self.Bind(wx.EVT_BUTTON, self.panel.on_delete_selected, remove_selected_btn)

        remove_all_btn = wx.Button(self, wx.ID_ANY, "Remove all")
        self.Bind(wx.EVT_BUTTON, self.panel.on_delete_all, remove_all_btn)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(add_btn)
        sizer.Add(remove_btn)
        sizer.Add(remove_selected_btn)
        sizer.Add(remove_all_btn)

        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        main_sizer.Add(self.panel, 1, wx.EXPAND)
        main_sizer.Add(sizer, 1, wx.EXPAND)
        self.SetSizer(main_sizer)

        self.panel.on_add_to_table({"c1": 0, "c2": 4})
        self.panel.on_add_to_table({"c1": 1, "c2": 4})
        self.panel.on_add_to_table({"c1": 3, "c2": 4})
        self.panel.on_add_to_table({"c1": 6, "c2": 4})
        self.panel.on_add_to_table({"c1": 37, "c2": 4})
        self.Show()

    def add_item(self, evt):
        from random import randint

        self.panel.on_add_to_table({"c1": randint(0, 1000), "c2": randint(0, 1000)})

    # def remove_item(self, evt):
    #     self.panel.on_delete_item(None)
    #
    # def remove_item(self, evt):
    #     self.panel.on_delete_item(None)


def main():

    app = wx.App()
    # frame = wx.Frame()
    ex = ExampleFrame(None)

    # ex.ShowModal()
    app.MainLoop()


if __name__ == "__main__":
    main()
