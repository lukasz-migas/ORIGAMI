"""This file creates various styles for the GUI"""

# Standard library imports
import time
import logging
import itertools
from ast import literal_eval
from typing import List
from operator import itemgetter

# Third-party imports
import wx
import numpy as np
import wx.html
from natsort.natsort import natsorted

# Local imports
from origami.utils.color import convert_rgb_1_to_255
from origami.utils.color import convert_rgb_255_to_1
from origami.utils.utilities import report_time
from origami.utils.converters import str2int
from origami.utils.converters import str2num
from origami.utils.converters import byte2str
from origami.gui_elements.mixins import ParentSizeMixin
from origami.gui_elements.mixins import DocumentationMixin
from origami.gui_elements.mixins import WindowPositionMixin
from origami.gui_elements.mixins import ActivityIndicatorMixin
from origami.gui_elements.misc_dialogs import DialogBox

LOGGER = logging.getLogger(__name__)


class UIBase:
    """Base class for Dialog and MiniFrame"""

    @staticmethod
    def _parse_evt(evt):
        """Parse event"""
        if evt is not None:
            evt.Skip()

    @staticmethod
    def _get_icons(icons):
        """Get Icons"""
        if icons is None:

            from origami.icons.assets import Icons

            icons = Icons()
        return icons

    def on_key_event(self, evt):
        """Catch key events"""
        key_code = evt.GetKeyCode()

        # exit window
        if key_code == wx.WXK_ESCAPE:
            self.on_close(None)
            return

        if evt is not None:
            evt.Skip()

    def make_panel(self, *args):
        """Make panel"""
        pass

    def make_gui(self):
        """Make and arrange main panel"""

        # make panel
        panel = self.make_panel()

        # pack element
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(panel, 1, wx.EXPAND, 5)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizerAndFit(main_sizer)  # noqa
        self.Layout()  # noqa

    def on_close(self, evt, force: bool = False):
        """Destroy this frame."""
        raise NotImplementedError("Must implement method")

    def ask(self, title: str, msg: str):
        """Ask question and return value"""
        dlg = DialogBox(title, msg, kind="Question", parent=self)
        return dlg

    def warn(self, title: str, msg: str):
        """Ask question and return value"""
        _ = DialogBox(title, msg, kind="Warning", parent=self)

    def error(self, title: str, msg: str):
        """Ask question and return value"""
        _ = DialogBox(title, msg, parent=self)


class Dialog(wx.Dialog, UIBase, ActivityIndicatorMixin, DocumentationMixin, ParentSizeMixin, WindowPositionMixin):
    """Proxy of Dialog"""

    def __init__(self, parent, style=wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX), **kwargs):
        self.parent = parent
        bind_key_events = kwargs.pop("bind_key_events", True)
        wx.Dialog.__init__(self, parent, -1, style=style, **kwargs)

        self.Bind(wx.EVT_CLOSE, self.on_close)

        if bind_key_events:
            self.Bind(wx.EVT_CHAR_HOOK, self.on_key_event)

    def on_ok(self, evt):
        """Close the frame gracefully"""
        if self.IsModal():
            self.EndModal(wx.ID_OK)
        else:
            self.Destroy()

    def on_close(self, evt, force: bool = False):
        """Destroy this frame."""
        if self.IsModal():
            self.EndModal(wx.ID_NO)
        else:
            self.Destroy()


class MiniFrame(wx.MiniFrame, UIBase, ActivityIndicatorMixin, DocumentationMixin, ParentSizeMixin, WindowPositionMixin):
    """Proxy of MiniFrame"""

    def __init__(
        self,
        parent,
        style=wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX | wx.STAY_ON_TOP,
        size=(-1, -1),
        **kwargs,
    ):
        bind_key_events = kwargs.pop("bind_key_events", True)
        wx.MiniFrame.__init__(self, parent, -1, size=size, style=style, **kwargs)
        self.parent = parent

        self.Bind(wx.EVT_CLOSE, self.on_close)

        if bind_key_events:
            self.Bind(wx.EVT_CHAR_HOOK, self.on_key_event)

    def filter_keys(self, evt):
        """Filter keys"""

    def on_close(self, evt, force: bool = False):
        """Destroy this frame."""
        self.Destroy()

    def on_ok(self, _evt):
        """Close the frame gracefully"""
        self.Destroy()


class ListCtrl(wx.ListCtrl):
    """ListCtrl"""

    def __init__(self, parent, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.LC_REPORT, **kwargs):
        wx.ListCtrl.__init__(self, parent, wx.ID_ANY, pos, size, style)

        if hasattr(self, "EnableCheckBoxes"):
            self.EnableCheckBoxes()

        # specify that simpler sorter should be used to speed things up
        self.disable_sort = kwargs.get("disable_sort", False)
        self.use_simple_sorter = kwargs.get("use_simple_sorter", False)

        self.parent = parent
        self.item_id = None
        self.old_column = None
        self.reverse = False
        self.check = False
        self.locked = False

        self.column_info = kwargs.get("column_info", None)
        self.color_0_to_1 = kwargs.get("color_0_to_1", False)
        self.add_item_color = kwargs.get("add_item_color", False)
        self.color_in_column = kwargs.get("color_in_column", False)
        self.color_column_id = kwargs.get("color_column_id", -1)
        self.color_in_column_255 = kwargs.get("color_in_column_255", False)

        self.Bind(wx.EVT_LIST_COL_CLICK, self.on_column_click, self)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_select_item, self)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_activate_item, self)
        self.Bind(wx.EVT_LIST_KEY_DOWN, self.on_key_select_item, self)

    def get_text(self, row_id: int, col_id: int) -> str:
        """Get value of a row/column in the table"""
        return self.GetItem(row_id, col_id).GetText()

    def set_text(self, row_id: int, col_id: int, value: str):
        """Get value of a row/column in the table"""
        return self.SetItem(row_id, col_id, str(value))

    def set_background_color(self, row_id: int, color):
        """Set background color"""
        self.SetItemBackgroundColour(row_id, color)

    def get_all_in_column(self, col_id: int):
        """Return a list of all items in a particular column"""
        return [self.GetItem(row_id, col_id).GetText() for row_id in range(self.GetItemCount())]

    def IsChecked(self, item):  # noqa
        """Check whether an item has been checked"""
        return self.IsItemChecked(item)

    def on_select_item(self, evt):
        """Select item"""
        self.item_id = evt.Index

        if evt is not None:
            evt.Skip()

    def on_activate_item(self, evt):
        """Activate item"""
        self.item_id = evt.Index

        if evt is not None:
            evt.Skip()

    def on_key_select_item(self, evt):
        """Select item using keyboard"""
        key_code = evt.GetKeyCode()
        if key_code == wx.WXK_UP or key_code == wx.WXK_DOWN:
            self.item_id = evt.GetIndex()

        if evt is not None:
            evt.Skip()

    def remove_by_key(self, key, value):
        """Remove item by key"""
        item_id = self.GetItemCount() - 1
        while item_id >= 0:
            item_info = self.on_get_item_information(item_id)
            if item_info[key] == value:
                self.DeleteItem(item_id)
            item_id -= 1

    def remove_by_keys(self, keys, values):
        """Remove items by keys"""
        assert len(keys) == len(values)
        item_id = self.GetItemCount() - 1
        while item_id >= 0:
            item_info = self.on_get_item_information(item_id)
            if all(
                [
                    check_value == list_value
                    for check_value, list_value in zip(values, [item_info.get(key) for key in keys])
                ]
            ):
                self.DeleteItem(item_id)
            item_id -= 1

    def on_get_item_information(self, item_id):
        """Get information about particular row"""
        if self.column_info is None:
            return dict()

        if item_id is None:
            return dict()

        is_checked = self.IsChecked(item_id)
        information = {"id": item_id, "select": is_checked}

        for column in self.column_info:
            item_tag = self.column_info[column]["tag"]
            item_type = self.column_info[column]["type"]
            if item_tag == "color":
                if self.color_in_column:
                    _color = literal_eval(self.GetItem(item_id, column).GetText())
                else:
                    _color = self.GetItemBackgroundColour(item_id)
                item_value, color_1 = self._convert_color(_color)
                information["color_255to1"] = color_1
            else:
                item_value = self._convert_type(self.GetItem(item_id, column).GetText(), item_type)
            information[item_tag] = item_value

        # add color regardless whether the color column is present
        if "color" not in information and self.add_item_color:
            if self.color_in_column:
                _color = literal_eval(self.GetItem(item_id, self.color_column_id).GetText())
            else:
                _color = self.GetItemBackgroundColour(item_id)
            color_255, color_1 = self._convert_color(_color)
            information["color_255to1"] = color_1
            information["color"] = color_255

        information["check"] = is_checked

        return information

    def get_all_checked(self):
        """Return list of items that have been checked"""
        rows = self.GetItemCount()

        items = list()
        for item_id in range(rows):
            if self.IsChecked(item_id):
                items.append(self.on_get_item_information(item_id))
        return items

    @staticmethod
    def _convert_type(item_value, item_type):

        if item_type == "bool":
            return bool(item_value)
        elif item_type == "int":
            return str2int(item_value)
        elif item_type == "float":
            return str2num(item_value)
        elif item_type == "list":
            return literal_eval(item_value)
        else:
            return byte2str(item_value)

    def _convert_color(self, color_255):
        """Convert color to appropriate format"""
        # sometimes its convenient to keep colors in the 0-1 range
        if self.color_0_to_1:
            color_1 = color_255
            color_255 = convert_rgb_1_to_255(color_1)
        else:
            color_1 = convert_rgb_255_to_1(color_255)
        return color_255, color_1

    def _indicate_order(self, column: int):
        """Indicate whether values are sorted in ascending or descending order"""

        def _parse_column(_col):
            _col_text = _col.GetText()
            if "▲" in _col_text:
                _col_text = _col_text.split("▲ ")[-1]
            elif "▼" in _col_text:
                _col_text = _col_text.split("▼ ")[-1]
            return _col_text

        # clear old column
        if self.old_column not in [0, None] and self.old_column != column:
            col = self.GetColumn(self.old_column)
            col_text = _parse_column(col)
            col.SetText(col_text)
            self.SetColumn(self.old_column, col)

        if column == 0:
            return

        # set new column
        col = self.GetColumn(column)
        col_text = _parse_column(col)
        col_text = "▼ " + col_text if not self.reverse else "▲ " + col_text
        col.SetText(col_text)
        self.SetColumn(column, col)

    def on_column_click(self, evt):
        """Interact on column click"""
        if self.disable_sort:
            return
        t_start = time.time()
        self.locked = True
        column = evt.GetColumn()

        if self.old_column is not None and self.old_column == column:
            self.reverse = not self.reverse
        else:
            self.reverse = False

        self._indicate_order(column)
        if column == 0:
            self.check = not self.check
            self.on_check_all(self.check)
        else:
            if self.use_simple_sorter:
                self.on_simple_sort(column, self.reverse)
            else:
                self.on_sort(column, self.reverse)

        self.old_column = column
        self.locked = False
        LOGGER.debug(f"Sorted table in {report_time(t_start)}")

    def on_check_all(self, check):
        """Check all rows in the table"""
        self.locked = True
        t_start = time.time()
        rows = self.GetItemCount()
        [self.CheckItem(row, check=check) for row in range(rows)]
        self.check = check
        self.locked = False
        LOGGER.debug(f"(Un)checked all items in {report_time(t_start)}")

    def on_sort(self, column, direction):
        """Sort items based on column and direction"""

        # get list data
        temp_data = self._get_list_data()

        # Sort data
        temp_data = natsorted(temp_data, key=itemgetter(column), reverse=direction)
        # Clear table
        self.DeleteAllItems()

        # restructure data
        temp_data, check_data, bg_rgb, fg_rgb = self._restructure_list_data(temp_data)

        # Reinstate data
        self._set_list_data(temp_data, check_data, bg_rgb, fg_rgb)

    def on_simple_sort(self, column, direction):
        """Sort items based on column and direction"""
        columns = self.GetColumnCount()
        rows = self.GetItemCount()

        temp_data = []
        # Iterate over row and columns to get data
        for row in range(rows):
            temp_row = []

            for col in range(columns):
                item = self.GetItem(row, col)
                temp_row.append(item.GetText())

            temp_row.append(self.IsChecked(row))
            temp_data.append(temp_row)

        # Sort data
        temp_data = natsorted(temp_data, key=itemgetter(column), reverse=direction)
        # Clear table
        self.DeleteAllItems()

        check_data = []
        for check in temp_data:
            check_data.append(check[-1])
            del check[-1]

        # Reinstate data
        row_list = np.arange(len(temp_data))
        for row, check in zip(row_list, check_data):
            self.Append(temp_data[row])
            self.CheckItem(row, check)

    def on_clear_table_selected(self, _evt):
        """
        This function clears the table without deleting any items from the
        document tree
        """
        rows = self.GetItemCount() - 1
        while rows >= 0:
            if self.IsChecked(rows):
                self.DeleteItem(rows)
            rows -= 1

    def on_clear_table_all(self, _evt, ask=True):
        """
        This function clears the table without deleting any items from the
        document tree
        """
        # Ask if you want to delete all items
        if ask:
            dlg = DialogBox(msg="Are you sure you would like to clear the table?", kind="Question")
            if dlg == wx.ID_NO:
                print("The operation was cancelled")
                return
        self.DeleteAllItems()

    def on_remove_duplicates(self):
        """Remove duplicates from the table"""
        # get list data
        temp_data = sorted(self._get_list_data())
        # remove duplicates
        temp_data = list(k for k, _ in itertools.groupby(temp_data))

        # clear table
        self.DeleteAllItems()

        temp_data, check_data, bg_rgb, fg_rgb = self._restructure_list_data(temp_data)

        self._set_list_data(temp_data, check_data, bg_rgb, fg_rgb)

    def _get_list_data(self, include_color=True):  # noqa
        columns = self.GetColumnCount()
        rows = self.GetItemCount()

        temp_data = []
        # Iterate over row and columns to get data
        for row in range(rows):
            temp_row = []
            for col in range(columns):
                item = self.GetItem(itemIdx=row, col=col)
                temp_row.append(item.GetText())
            temp_row.append(self.IsChecked(row))
            temp_row.append(self.GetItemBackgroundColour(row))
            temp_row.append(self.GetItemTextColour(row))
            temp_data.append(temp_row)

        return temp_data

    @staticmethod
    def _restructure_list_data(list_data):

        check_list, bg_rgb, fg_rgb = [], [], []
        for check in list_data:
            fg_rgb.append(check[-1])
            del check[-1]
            bg_rgb.append(check[-1])
            del check[-1]
            check_list.append(check[-1])
            del check[-1]

        return list_data, check_list, bg_rgb, fg_rgb

    def _set_list_data(self, list_data, check_data, bg_rgb, fg_rgb):
        # Reinstate data
        row_list = np.arange(len(list_data))
        for row, check, bg_color, fg_color in zip(row_list, check_data, bg_rgb, fg_rgb):
            self.Append(list_data[row])
            self.CheckItem(row, check)
            self.SetItemBackgroundColour(row, bg_color)
            self.SetItemTextColour(row, fg_color)

    @staticmethod
    def _convert_color_to_list(color):
        return list(color)


class VListBox(wx.ListBox):
    """VListBox widget"""

    items = None
    FONT = None

    def __init__(self, *args, style=wx.LB_DEFAULT | wx.LB_OWNERDRAW, **kwargs):
        super(VListBox, self).__init__(*args, style=style, **kwargs)
        self.setup()

    def setup(self):
        """Additional setup"""

    def set_items(self, item_list: List[str]):
        """Set items in the VListBox"""
        self.AppendItems(item_list)
        if self.FONT:
            self.SetFont(self.FONT)

    def get_items(self):
        """Get items"""
        item_list = []
        for item_id in range(self.GetCount()):
            item_list.append(self.GetString(item_id))
        return item_list

    def update_item(self, item_id: int, value: str):
        """Update value in the table"""
        self.SetString(item_id, value)

    # def set_items(self, path_list: List[str]):
    #     """Set items in the VListBox"""
    #     self.items = path_list
    #     self.SetItemCount(len(path_list))
    #
    # def OnGetItem(self, n: int):
    #     """Return the item"""
    #     return self._get_item_text(n)

    # def OnDrawItem(self, dc, rect, n):  # noqa
    #     """Draw item in the ui"""
    #     if self.GetSelection() == n:
    #         c = wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT)
    #     else:
    #         c = self.GetForegroundColour()
    #     dc.SetFont(self.GetFont())
    #     dc.SetTextForeground(c)
    #     dc.DrawLabel(self._get_item_text(n), rect, wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
    #
    # # This method must be overridden.  It should return the height
    # # required to draw the n'th item.
    # def OnMeasureItem(self, n):
    #     """Measure the size of the item"""
    #     height = 0
    #     for line in self._get_item_text(n).split("\n"):
    #         w, h = self.GetTextExtent(line)
    #         height += h
    #     return height + 5

    # These are also overridable:
    #
    # OnDrawSeparator(dc, rect, n)
    #   Draw a separator between items.  Note that rect may be reduced
    #   in size if desired so OnDrawItem gets a smaller rect.
    #
    # OnDrawBackground(dc, rect, n)
    #   Draw the background and maybe a border if desired.

    def _get_item_text(self, item):
        if self.items:
            return self.items[item]
        return ""


class BackgroundPanel(wx.Panel):
    """Simple panel with image background."""

    def __init__(self, parent, image, size=(-1, -1)):
        wx.Panel.__init__(self, parent, wx.ID_ANY, size=size)
        self.SetMinSize(size)

        self.image = image

        # set paint event to tile image
        wx.EVT_PAINT(self, self.on_paint)

    def on_paint(self, _evt):
        """On paint event handler"""

        # create paint surface
        dc = wx.PaintDC(self)
        # dc.Clear()

        # tile/wallpaper the image across the canvas
        for x in range(0, self.GetSize()[0], self.image.GetWidth()):
            dc.DrawBitmap(self.image, x, 0, True)


class Validator(wx.Validator):
    """Text validator."""

    # define navigation keys
    NAV_KEYS = (
        wx.WXK_HOME,
        wx.WXK_LEFT,
        wx.WXK_UP,
        wx.WXK_END,
        wx.WXK_RIGHT,
        wx.WXK_DOWN,
        wx.WXK_NUMPAD_HOME,
        wx.WXK_NUMPAD_LEFT,
        wx.WXK_NUMPAD_UP,
        wx.WXK_NUMPAD_END,
        wx.WXK_NUMPAD_RIGHT,
        wx.WXK_NUMPAD_DOWN,
    )

    def __init__(self, flag):
        wx.Validator.__init__(self)
        self.flag = flag
        self.Bind(wx.EVT_CHAR, self.on_key_press)

    def Clone(self):  # noqa
        """Clone validator"""
        return Validator(self.flag)

    def TransferToWindow(self):  # noqa
        return True

    def TransferFromWindow(self):  # noqa
        return True

    def on_key_press(self, evt):
        """Interact on key press"""
        key = evt.GetKeyCode()

        # navigation keys
        if key in self.NAV_KEYS or key < wx.WXK_SPACE or key == wx.WXK_DELETE:
            evt.Skip()
            return

        # copy
        elif key == 99 and evt.CmdDown():
            evt.Skip()
            return

        # paste
        elif key == 118 and evt.CmdDown():
            evt.Skip()
            return

        # illegal characters
        elif key > 255:
            return

        # int only
        elif self.flag == "int" and chr(key) in "-0123456789eE":
            evt.Skip()
            return

        # positive int only
        elif self.flag == "intPos" and chr(key) in "0123456789eE":
            evt.Skip()
            return

        # floats only
        elif self.flag == "float" and (chr(key) in "-0123456789.eE"):
            evt.Skip()
            return

        # positive floats only
        elif self.flag == "floatPos" and (chr(key) in "0123456789.eE"):
            evt.Skip()
            return

        elif self.flag == "path" and (chr(key) not in r'\/:*?!<>|"'):
            evt.Skip()
            return

        # error
        else:
            wx.Bell()
            return


class TestListCtrl(wx.Frame):
    """Test the popup window"""

    def __init__(self, parent):
        wx.Frame.__init__(self, parent, -1)

        self.list = ListCtrl(self)
        self.list.InsertColumn(0, "")
        self.list.InsertColumn(1, "Column 1")
        self.list.InsertColumn(2, "Column 2")

        for i in range(100):
            self.list.Append(["", str(i), "COLUMN 2"])

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.list, 1, wx.EXPAND)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)

        self.SetSize((800, 800))


def _main():

    from origami.app import App

    app = App()

    dlg = TestListCtrl(None)
    dlg.Show()

    app.MainLoop()


if __name__ == "__main__":
    _main()
