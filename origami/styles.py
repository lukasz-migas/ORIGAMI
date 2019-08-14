"""This file creates various styles for the GUI"""
# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import itertools
from operator import itemgetter

import numpy as np
import wx
import wx.lib.mixins.listctrl as listmix
from gui_elements.misc_dialogs import DialogBox
from natsort.natsort import natsorted
from utils.color import convertRGB255to1
from utils.converters import byte2str
from utils.converters import str2int
from utils.converters import str2num
from wx.lib.agw import supertooltip as superTip

# Sizes
COMBO_SIZE = 120
COMBO_SIZE_COMPACT = 80
BTN_SIZE = 60
TXTBOX_SIZE = 45

GAUGE_HEIGHT = 15
GAUGE_SPACE = 10
PANEL_SPACE_MAIN = 10

LISTCTRL_STYLE_MULTI = wx.LC_REPORT | wx.LC_VRULES | wx.LC_HRULES | wx.SUNKEN_BORDER
LISTCTRL_SORT = 1

SLIDER_STYLE = wx.SL_HORIZONTAL | wx.SL_MIN_MAX_LABELS | wx.SL_VALUE_LABEL


def make_spin_ctrl(parent, value, min_value, max_value, increment_value, size=(-1, -1), evtid=-1):
    """Convenient way to initilize SpinCtrlDouble"""
    spin_ctrl = wx.SpinCtrlDouble(
        parent, evtid, value=str(value), min=min_value, max=max_value, initial=value, inc=increment_value, size=size
    )
    return spin_ctrl


def makeMenuItem(parent, text, id=-1, bitmap=None, help_text=None, kind=wx.ITEM_NORMAL):
    """ Helper function to make a menu item with or without bitmap image """
    menuItem = wx.MenuItem(parent, id, text, kind=kind)
    if bitmap is not None:
        menuItem.SetBitmap(bitmap)

    if help_text is not None:
        menuItem.SetHelp(help_text)

    return menuItem


def setItemFont(parent, size=10, color=wx.BLACK):
    font = wx.Font(size, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
    parent.SetForegroundColour(color)
    parent.SetFont(font)

    return parent


def makeStaticBox(parent, title, size, color, id=-1):
    staticBox = wx.StaticBox(parent, id, title, size=size, style=wx.SB_FLAT)
    font = wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
    staticBox.SetForegroundColour(color)
    staticBox.SetFont(font)

    return staticBox


def makeToggleBtn(parent, text, colorOff, name="other", size=(40, -1)):
    toggleBtn = wx.ToggleButton(
        parent, wx.ID_ANY, text, wx.DefaultPosition, size, style=wx.ALIGN_CENTER_VERTICAL, name=name
    )
    font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
    toggleBtn.SetFont(font)
    toggleBtn.SetForegroundColour(colorOff)

    return toggleBtn


def makeStaticText(parent, text):
    textBox = wx.StaticText(
        parent, wx.ID_ANY, text, wx.DefaultPosition, wx.DefaultSize, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.LEFT
    )
    return textBox


def makeTextCtrl(parent, size=(wx.DefaultSize)):
    textBox = wx.TextCtrl(
        parent, wx.ID_ANY, "", wx.DefaultPosition, size, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.LEFT
    )
    return textBox


def makeSlider(parent, value, minValue, maxValue):
    slider = wx.Slider(
        parent, -1, value=value, minValue=minValue, maxValue=maxValue, size=(140, -1), style=SLIDER_STYLE
    )
    return slider


def makeCheckbox(parent, text, style=wx.ALIGN_LEFT, ID=-1, name=""):
    checkbox = wx.CheckBox(parent, ID, text, (3, 3), style=style, name=name)
    return checkbox


def makeTooltip(text=None, delay=500, reshow=500, autopop=3000):
    """
    Make tooltips with specified delay time
    """
    tooltip = wx.ToolTip(text)
    tooltip.SetDelay(delay)
    tooltip.SetReshow(reshow)
    tooltip.SetAutoPop(autopop)
    return tooltip


def layout(parent, sizer, size=None):
    """Ensure correct panel layout - hack."""

    parent.SetMinSize((-1, -1))
    sizer.Fit(parent)
    parent.Layout()

    if size is None:
        size = parent.GetSize()
    parent.SetSize((size[0] + 1, size[1] + 1))
    parent.SetSize(size)
    parent.SetMinSize(size)


def makeSuperTip(
    parent, title="Title", text="Insert message", delay=5, headerLine=False, footerLine=False, headerImg=None, **kwargs
):

    if kwargs:
        title = kwargs["help_title"]
        text = kwargs["help_msg"]
        headerImg = kwargs["header_img"]
        headerLine = kwargs["header_line"]
        footerLine = kwargs["footer_line"]

    # You can define your BalloonTip as follows:
    tip = superTip.SuperToolTip(text)
    tip.SetStartDelay(1)
    tip.SetEndDelay(delay)
    tip.SetDrawHeaderLine(headerLine)
    tip.SetDrawFooterLine(footerLine)
    tip.SetHeader(title)
    tip.SetTarget(parent)
    tip.SetTopGradientColour((255, 255, 255, 255))
    tip.SetMiddleGradientColour((228, 236, 248, 255))
    tip.SetBottomGradientColour((198, 214, 235, 255))

    if headerImg is not None:
        tip.SetHeaderBitmap(headerImg)

    return tip


def mac_app_init():
    """Run after application initialize."""
    # set MAC
    if wx.Platform == "__WXMAC__":
        wx.SystemOptions.SetOptionInt("mac.listctrl.always_use_generic", True)
        wx.ToolTip.SetDelay(1500)
        global SCROLL_DIRECTION
        SCROLL_DIRECTION = -1


class Dialog(wx.Dialog):
    """Proxy of Dialog"""

    def __init__(self, parent, **kwargs):
        wx.Dialog.__init__(
            self, parent, -1, style=wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX), **kwargs
        )

        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_event)

    def on_key_event(self, evt):
        key_code = evt.GetKeyCode()
        # exit window
        if key_code == wx.WXK_ESCAPE:
            self.on_close(evt=None)

        if evt is not None:
            evt.Skip()

    def on_close(self, evt):
        """Destroy this frame."""
        self.Destroy()

    def make_gui(self):
        """Make and arrange main panel"""

        # make panel
        panel = self.make_panel()

        # pack element
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.Add(panel, 1, wx.EXPAND, 5)

        # fit layout
        self.main_sizer.Fit(self)
        self.SetSizer(self.main_sizer)
        self.Layout()


class MiniFrame(wx.MiniFrame):
    """Proxy of MiniFrame"""

    def __init__(
        self, parent, style=wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX | wx.STAY_ON_TOP, **kwargs
    ):
        bind_key_events = kwargs.pop("bind_key_events", True)
        wx.MiniFrame.__init__(self, parent, -1, size=(-1, -1), style=style, **kwargs)

        self.Bind(wx.EVT_CLOSE, self.on_close)

        if bind_key_events:
            self.Bind(wx.EVT_CHAR_HOOK, self.on_key_event)

    def on_key_event(self, evt):
        key_code = evt.GetKeyCode()
        # exit window
        if key_code == wx.WXK_ESCAPE:
            self.on_close(evt=None)

        if evt is not None:
            evt.Skip()

    def on_close(self, evt):
        """Destroy this frame."""
        self.Destroy()

    def make_gui(self):
        """Make and arrange main panel"""
        # make panel
        panel = self.make_panel()

        # pack element
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.Add(panel, 1, wx.EXPAND, 5)

        # fit layout
        self.main_sizer.Fit(self)
        self.SetSizer(self.main_sizer)
        self.Layout()


class ListCtrl(wx.ListCtrl, listmix.CheckListCtrlMixin):
    """ListCtrl"""

    def __init__(self, parent, id=-1, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.LC_REPORT, **kwargs):
        wx.ListCtrl.__init__(self, parent, id, pos, size, style)
        listmix.CheckListCtrlMixin.__init__(self)

        # specify that simpler sorter should be used to speed things up
        self.use_simple_sorter = kwargs.get("use_simple_sorter", False)

        self.parent = parent
        self.item_id = None
        self.old_column = None
        self.reverse = False
        self.check = False

        self.column_info = kwargs.get("column_info", None)

        self.Bind(wx.EVT_LIST_COL_CLICK, self.on_column_click, self)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_select_item, self)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_activate_item, self)
        self.Bind(wx.EVT_LIST_KEY_DOWN, self.on_key_select_item, self)

    def on_select_item(self, evt):
        self.item_id = evt.Index

    def on_activate_item(self, evt):
        self.item_id = evt.Index

    def on_key_select_item(self, evt):
        key_code = evt.GetKeyCode()
        if key_code == wx.WXK_UP or key_code == wx.WXK_DOWN:
            self.item_id = evt.GetIndex()

        if evt is not None:
            evt.Skip()

    def on_get_item_information(self, item_id):
        if self.column_info is None:
            return dict()

        if item_id is None:
            return dict()

        is_checked = self.IsChecked(item_id)
        information = {}
        information["id"] = item_id
        information["select"] = is_checked

        for column in self.column_info:
            item_tag = self.column_info[column]["tag"]
            item_type = self.column_info[column]["type"]
            if item_tag == "color":
                item_value, color_1 = self._convert_color(self.GetItemBackgroundColour(item_id))
                information["color_255to1"] = color_1
            else:
                item_value = self._convert_type(self.GetItem(item_id, column).GetText(), item_type)
            information[item_tag] = item_value
        information["check"] = is_checked

        return information

    @staticmethod
    def _convert_type(item_value, item_type):

        if item_type == "bool":
            return bool(item_value)
        elif item_type == "int":
            return str2int(item_value)
        elif item_type == "float":
            return str2num(item_value)
        else:
            return byte2str(item_value)

    @staticmethod
    def _convert_color(color_255):
        color_1 = convertRGB255to1(color_255, decimals=3)
        return color_255, color_1

    def on_column_click(self, evt):
        column = evt.GetColumn()

        if self.old_column is not None and self.old_column == column:
            self.reverse = not self.reverse
        else:
            self.reverse = False

        if column == 0:
            self.check = not self.check
            self.on_check_all(self.check)
        else:
            if self.use_simple_sorter:
                self.on_simple_sort(column, self.reverse)
            else:
                self.on_sort(column, self.reverse)

        self.old_column = column

    def on_check_all(self, check):
        rows = self.GetItemCount()

        for row in range(rows):
            self.CheckItem(row, check=check)

    def on_sort(self, column, direction):
        """
        Sort items based on column and direction
        """

        # get list data
        tempData = self._get_list_data()

        # Sort data
        tempData = natsorted(tempData, key=itemgetter(column), reverse=direction)
        # Clear table
        self.DeleteAllItems()

        # restructure data
        tempData, checkData, bg_rgb, fg_rgb = self._restructure_list_data(tempData)

        # Reinstate data
        self._set_list_data(tempData, checkData, bg_rgb, fg_rgb)

    def on_simple_sort(self, column, direction):
        """
        Sort items based on column and direction
        """
        columns = self.GetColumnCount()
        rows = self.GetItemCount()

        tempData = []
        # Iterate over row and columns to get data
        for row in range(rows):
            tempRow = []

            for col in range(columns):
                item = self.GetItem(itemIdx=row, col=col)
                tempRow.append(item.GetText())

            tempRow.append(self.IsChecked(index=row))
            tempData.append(tempRow)

        # Sort data
        tempData = natsorted(tempData, key=itemgetter(column), reverse=direction)
        # Clear table
        self.DeleteAllItems()

        checkData = []
        for check in tempData:
            checkData.append(check[-1])
            del check[-1]

        # Reinstate data
        rowList = np.arange(len(tempData))
        for row, check in zip(rowList, checkData):
            self.Append(tempData[row])
            self.CheckItem(row, check)

    def on_clear_table_selected(self, evt):
        """
        This function clears the table without deleting any items from the
        document tree
        """
        rows = self.GetItemCount() - 1
        while rows >= 0:
            if self.IsChecked(rows):
                self.DeleteItem(rows)
            rows -= 1

    def on_clear_table_all(self, evt):
        """
        This function clears the table without deleting any items from the
        document tree
        """
        # Ask if you want to delete all items
        dlg = DialogBox(exceptionMsg="Are you sure you would like to clear the table?", type="Question")
        if dlg == wx.ID_NO:
            print("The operation was cancelled")
            return
        self.DeleteAllItems()

    def on_remove_duplicates(self):

        # get list data
        tempData = sorted(self._get_list_data())

        # remove duplicates
        tempData = list(k for k, _ in itertools.groupby(tempData))

        # clear table
        self.DeleteAllItems()

        tempData, checkData, bg_rgb, fg_rgb = self._restructure_list_data(tempData)

        self._set_list_data(tempData, checkData, bg_rgb, fg_rgb)

    def _get_list_data(self, include_color=True):
        columns = self.GetColumnCount()
        rows = self.GetItemCount()

        tempData = []
        # Iterate over row and columns to get data
        for row in range(rows):
            tempRow = []
            for col in range(columns):
                item = self.GetItem(itemIdx=row, col=col)
                tempRow.append(item.GetText())
            tempRow.append(self.IsChecked(index=row))
            tempRow.append(self.GetItemBackgroundColour(row))
            tempRow.append(self.GetItemTextColour(row))
            tempData.append(tempRow)

        return tempData

    @staticmethod
    def _restructure_list_data(listData):

        check_list, bg_rgb, fg_rgb = [], [], []
        for check in listData:
            fg_rgb.append(check[-1])
            del check[-1]
            bg_rgb.append(check[-1])
            del check[-1]
            check_list.append(check[-1])
            del check[-1]

        return listData, check_list, bg_rgb, fg_rgb

    def _set_list_data(self, listData, checkData, bg_rgb, fg_rgb):
        # Reinstate data
        rowList = np.arange(len(listData))
        for row, check, bg_color, fg_color in zip(rowList, checkData, bg_rgb, fg_rgb):
            self.Append(listData[row])
            self.CheckItem(row, check)
            self.SetItemBackgroundColour(row, bg_color)
            self.SetItemTextColour(row, fg_color)

    @staticmethod
    def _convert_color_to_list(color):
        return list(color)


class SimpleListCtrl(wx.ListCtrl):
    """ListCtrl"""

    def __init__(self, parent, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.LC_REPORT):
        wx.ListCtrl.__init__(self, parent, id, pos, size, style)

        self.old_column = None
        self.reverse = False
        self.check = False

        self.Bind(wx.EVT_LIST_COL_CLICK, self.on_column_click, self)

    def on_column_click(self, evt):
        column = evt.GetColumn()

        if self.old_column is not None and self.old_column == column:
            self.reverse = not self.reverse
        else:
            self.reverse = False

        self.on_sort(column, self.reverse)
        self.old_column = column

    def on_sort(self, column, direction):
        """
        Sort items based on column and direction
        """
        columns = self.GetColumnCount()
        rows = self.GetItemCount()

        tempData = []
        # Iterate over row and columns to get data
        for row in range(rows):
            tempRow = []

            for col in range(columns):
                item = self.GetItem(itemIdx=row, col=col)
                tempRow.append(item.GetText())
            tempData.append(tempRow)

        # Sort data
        tempData = natsorted(tempData, key=itemgetter(column), reverse=direction)
        # Clear table
        self.DeleteAllItems()

        # Reinstate data
        for row in tempData:
            self.Append(row)

    def on_clear_table_selected(self, evt):
        """
        This function clears the table without deleting any items from the
        document tree
        """
        rows = self.GetItemCount() - 1
        while rows >= 0:
            if self.IsChecked(rows):
                self.DeleteItem(rows)
            rows -= 1

    def on_clear_table_all(self, evt):
        """
        This function clears the table without deleting any items from the
        document tree
        """
        # Ask if you want to delete all items
        dlg = DialogBox(exceptionMsg="Are you sure you would like to clear the table?", type="Question")
        if dlg == wx.ID_NO:
            print("The operation was cancelled")
            return
        self.DeleteAllItems()


class EditableListCtrl(ListCtrl, listmix.TextEditMixin, listmix.CheckListCtrlMixin, listmix.ColumnSorterMixin):
    """
    Editable list
    """

    def __init__(self, parent, ID=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0, **kwargs):
        ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.TextEditMixin.__init__(self)
        listmix.CheckListCtrlMixin.__init__(self)

        self.block_columns = kwargs.get("block_columns", [0, 2])

        self.Bind(wx.EVT_LIST_BEGIN_LABEL_EDIT, self.OnBeginLabelEdit)

    def OnBeginLabelEdit(self, event):
        if event.m_col in self.block_columns:
            event.Veto()
        else:
            event.Skip()


class bgrPanel(wx.Panel):
    """Simple panel with image background."""

    def __init__(self, parent, id, image, size=(-1, -1)):
        wx.Panel.__init__(self, parent, id, size=size)
        self.SetMinSize(size)

        self.image = image

        # set paint event to tile image
        wx.EVT_PAINT(self, self._onPaint)

    def _onPaint(self, event=None):

        # create paint surface
        dc = wx.PaintDC(self)
        # dc.Clear()

        # tile/wallpaper the image across the canvas
        for x in range(0, self.GetSize()[0], self.image.GetWidth()):
            dc.DrawBitmap(self.image, x, 0, True)


class validator(wx.PyValidator):
    """Text validator."""

    def __init__(self, flag):
        wx.PyValidator.__init__(self)
        self.flag = flag
        self.Bind(wx.EVT_CHAR, self.OnChar)

    def Clone(self):
        return validator(self.flag)

    def TransferToWindow(self):
        return True

    def TransferFromWindow(self):
        return True

    def OnChar(self, evt):
        #         ctrl = self.GetWindow()
        #         value = ctrl.GetValue()
        key = evt.GetKeyCode()

        # define navigation keys
        navKeys = (
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

        # navigation keys
        if key in navKeys or key < wx.WXK_SPACE or key == wx.WXK_DELETE:
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

        # error
        else:
            wx.Bell()
            return
