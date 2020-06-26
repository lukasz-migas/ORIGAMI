"""This file creates various styles for the GUI"""


# Standard library imports
import itertools
from ast import literal_eval
from operator import itemgetter

# Third-party imports
import wx
import numpy as np
import wx.lib.mixins.listctrl as listmix
from wx.lib.agw import supertooltip as superTip
from natsort.natsort import natsorted

# Local imports
from origami.utils.color import convert_rgb_1_to_255
from origami.utils.color import convert_rgb_255_to_1
from origami.utils.converters import str2int
from origami.utils.converters import str2num
from origami.utils.converters import byte2str
from origami.gui_elements.misc_dialogs import DialogBox

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


def make_spin_ctrl_double(parent, value, min_value, max_value, increment_value, size=(-1, -1), evtid=-1, name="name"):
    """Convenient way to initialize SpinCtrlDouble"""
    spin_ctrl = wx.SpinCtrlDouble(
        parent,
        evtid,
        value=str(value),
        min=min_value,
        max=max_value,
        initial=value,
        inc=increment_value,
        size=size,
        name=name,
    )
    return spin_ctrl


def make_spin_ctrl_int(parent, value, min_value, max_value, increment_value, size=(-1, -1), evtid=-1, name="name"):
    """Convenient way to initialize SpinCtrl"""
    spin_ctrl = wx.SpinCtrl(
        parent,
        evtid,
        value=str(value),
        min=min_value,
        max=max_value,
        initial=value,
        #         inc=increment_value,
        size=size,
        name=name,
    )
    return spin_ctrl


def make_bitmap_btn(
    parent,
    evt_id,
    icon,
    size=(26, 26),
    style=wx.BORDER_DEFAULT | wx.ALIGN_CENTER_VERTICAL,
    bg_color=(240, 240, 240),
    tooltip: str = None,
):
    """Convenient way to initialize bitmap btn"""
    bitmap_btn = wx.BitmapButton(parent, evt_id, icon, size=size, style=style)
    bitmap_btn.SetBackgroundColour(bg_color)
    if tooltip is not None:
        bitmap_btn.SetToolTip(make_tooltip(tooltip))

    return bitmap_btn


def make_color_btn(parent, color, size=(26, 26), name="color", evt_id=-1):
    """Convenient way to initialize a color btn"""

    color_btn = wx.Button(parent, evt_id, size=size, name=name)
    color_btn.SetBackgroundColour(convert_rgb_1_to_255(color))

    return color_btn


def make_menu_item(parent, text, evt_id=-1, bitmap=None, help_text=None, kind=wx.ITEM_NORMAL):
    """ Helper function to make a menu item with or without bitmap image """
    menu_item = wx.MenuItem(parent, evt_id, text, kind=kind)
    if bitmap is not None:
        menu_item.SetBitmap(bitmap)

    if help_text is not None:
        menu_item.SetHelp(help_text)

    return menu_item


def set_item_font(
    parent, size=10, color=wx.BLACK, family=wx.FONTFAMILY_DEFAULT, style=wx.FONTSTYLE_NORMAL, weight=wx.FONTWEIGHT_BOLD
):
    """Set item font"""
    font = wx.Font(size, family, style, weight)
    parent.SetForegroundColour(color)
    parent.SetFont(font)

    return parent


def make_staticbox(parent, title, size, color, id=-1):
    static_box = wx.StaticBox(parent, id, title, size=size, style=wx.SB_FLAT)
    font = wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
    static_box.SetForegroundColour(color)
    static_box.SetFont(font)

    return static_box


def make_toggle_btn(parent, text, colorOff, name="other", size=(40, -1)):
    toggle_btn = wx.ToggleButton(
        parent, wx.ID_ANY, text, wx.DefaultPosition, size, style=wx.ALIGN_CENTER_VERTICAL, name=name
    )
    font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
    toggle_btn.SetFont(font)
    toggle_btn.SetForegroundColour(colorOff)

    return toggle_btn


def make_static_text(parent, text):
    text_box = wx.StaticText(
        parent, wx.ID_ANY, text, wx.DefaultPosition, wx.DefaultSize, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.LEFT
    )
    return text_box


def make_text_ctrl(parent, size=(wx.DefaultSize)):
    text_ctrl = wx.TextCtrl(
        parent, wx.ID_ANY, "", wx.DefaultPosition, size, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.LEFT
    )
    return text_ctrl


def make_slider(parent, value, min_value, max_value):
    slider = wx.Slider(
        parent, -1, value=value, minValue=min_value, maxValue=max_value, size=(140, -1), style=SLIDER_STYLE
    )
    return slider


def make_checkbox(parent, text, style=wx.ALIGN_LEFT, evt_id=-1, name="", tooltip=None):
    checkbox = wx.CheckBox(parent, evt_id, text, (3, 3), style=style, name=name)

    if tooltip:
        checkbox.SetToolTip(make_tooltip(tooltip))
    return checkbox


def set_tooltip(parent, tooltip):
    """Set tooltip information on an object"""
    assert hasattr(parent, "SetToolTip"), "Parent object does not have `SetToolTip` attribute"
    parent.SetToolTip(make_tooltip(tooltip))
    return parent


def make_tooltip(text=None, delay=500, reshow=500, auto_pop=3000):
    """
    Make tooltips with specified delay time
    """
    tooltip = wx.ToolTip(text)
    tooltip.SetDelay(delay)
    tooltip.SetReshow(reshow)
    tooltip.SetAutoPop(auto_pop)
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


def make_super_tooltip(
    parent,
    title="Title",
    text="Insert message",
    delay=5,
    header_line=False,
    footer_line=False,
    header_img=None,
    **kwargs,
):

    if kwargs:
        title = kwargs["help_title"]
        text = kwargs["help_msg"]
        header_img = kwargs["header_img"]
        header_line = kwargs["header_line"]
        footer_line = kwargs["footer_line"]

    # You can define your BalloonTip as follows:
    tip = superTip.SuperToolTip(text)
    tip.SetStartDelay(1)
    tip.SetEndDelay(delay)
    tip.SetDrawHeaderLine(header_line)
    tip.SetDrawFooterLine(footer_line)
    tip.SetHeader(title)
    tip.SetTarget(parent)
    tip.SetTopGradientColour((255, 255, 255, 255))
    tip.SetMiddleGradientColour((228, 236, 248, 255))
    tip.SetBottomGradientColour((198, 214, 235, 255))

    if header_img is not None:
        tip.SetHeaderBitmap(header_img)

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

    def __init__(self, parent, style=wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX), **kwargs):
        self.parent = parent
        bind_key_events = kwargs.pop("bind_key_events", True)
        wx.Dialog.__init__(self, parent, -1, style=style, **kwargs)

        self.Bind(wx.EVT_CLOSE, self.on_close)

        if bind_key_events:
            self.Bind(wx.EVT_CHAR_HOOK, self.on_key_event)

    def on_key_event(self, evt):
        """Catch key events"""
        key_code = evt.GetKeyCode()

        # exit window
        if key_code == wx.WXK_ESCAPE:
            self.on_close(evt=None)

        if evt is not None:
            evt.Skip()

    def on_close(self, evt):
        """Destroy this frame."""
        if self.IsModal():
            self.EndModal(wx.ID_NO)
        else:
            self.Destroy()

    def make_panel(self):
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
        self.SetSizerAndFit(main_sizer)
        self.Layout()


class MiniFrame(wx.MiniFrame):
    """Proxy of MiniFrame"""

    HELP_MD = None
    HELP_LINK = None

    _icons = None

    info_btn = None
    display_label = None

    def __init__(
        self, parent, style=wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX | wx.STAY_ON_TOP, **kwargs
    ):
        bind_key_events = kwargs.pop("bind_key_events", True)
        wx.MiniFrame.__init__(self, parent, -1, size=(-1, -1), style=style, **kwargs)
        self.parent = parent

        self.Bind(wx.EVT_CLOSE, self.on_close)

        if bind_key_events:
            self.Bind(wx.EVT_CHAR_HOOK, self.on_key_event)

    def on_key_event(self, evt):
        key_code = evt.GetKeyCode()
        # exit window
        if key_code == wx.WXK_ESCAPE:
            self.on_close(None)

        if evt is not None:
            evt.Skip()

    def filter_keys(self, evt):
        """Filter keys"""
        # print(evt)

    def on_close(self, evt):
        """Destroy this frame."""
        self.Destroy()

    def on_open_info(self, evt):
        """Open help window to inform user on how to use this window / panel"""
        from origami.gui_elements.panel_html_viewer import PanelHTMLViewer

        if self.HELP_LINK:
            PanelHTMLViewer(self, link=self.HELP_LINK)
        elif self.HELP_MD:
            PanelHTMLViewer(self, md_msg=self.HELP_MD)

    def make_info_button(self, panel):
        """Make clickable information button"""
        info_btn = make_bitmap_btn(panel, wx.ID_ANY, self._icons.info, style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL)
        info_btn.Bind(wx.EVT_BUTTON, self.on_open_info)
        return info_btn

    def make_statusbar(self, panel):
        """Make make-shift statusbar"""
        # add info button
        self.info_btn = self.make_info_button(panel)

        self.display_label = wx.StaticText(panel, wx.ID_ANY, "")
        self.display_label.SetForegroundColour(wx.BLUE)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.info_btn, 0, wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        sizer.AddSpacer(5)
        sizer.Add(self.display_label, 1, wx.ALIGN_CENTER_VERTICAL)

        return sizer

    def make_panel(self, *args):
        """Make panel"""
        pass

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


class ListCtrl(wx.ListCtrl, listmix.TextEditMixin):
    """ListCtrl"""

    def __init__(self, parent, id=-1, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.LC_REPORT, **kwargs):
        wx.ListCtrl.__init__(self, parent, id, pos, size, style)

        self.EnableCheckBoxes(True)

        # specify that simpler sorter should be used to speed things up
        self.use_simple_sorter = kwargs.get("use_simple_sorter", False)

        self.parent = parent
        self.item_id = None
        self.old_column = None
        self.reverse = False
        self.check = False

        self.column_info = kwargs.get("column_info", None)
        self.color_0_to_1 = kwargs.get("color_0_to_1", False)

        self.Bind(wx.EVT_LIST_COL_CLICK, self.on_column_click, self)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_select_item, self)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_activate_item, self)
        self.Bind(wx.EVT_LIST_KEY_DOWN, self.on_key_select_item, self)

    #     self.Bind(wx.EVT_LIST_BEGIN_LABEL_EDIT, self.OnBeginLabelEdit, self)
    #
    # def OnBeginLabelEdit(self, evt):
    #     print(self.allowed_edit)
    #     # if evt.Column not in self.allowed_edit:
    #     #     evt.Veto()
    #     # else:
    #     #     evt.Skip()

    def IsChecked(self, item):
        return self.IsItemChecked(item)

    def on_select_item(self, evt):
        self.item_id = evt.Index

    def on_activate_item(self, evt):
        self.item_id = evt.Index

        if evt is not None:
            evt.Skip()

    def on_key_select_item(self, evt):
        key_code = evt.GetKeyCode()
        if key_code == wx.WXK_UP or key_code == wx.WXK_DOWN:
            self.item_id = evt.GetIndex()

        if evt is not None:
            evt.Skip()

    def remove_by_key(self, key, value):
        item_id = self.GetItemCount() - 1
        while item_id >= 0:
            item_info = self.on_get_item_information(item_id)
            if item_info[key] == value:
                self.DeleteItem(item_id)
            item_id -= 1

    def remove_by_keys(self, keys, values):
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
                item_value, color_1 = self._convert_color(self.GetItemBackgroundColour(item_id))
                information["color_255to1"] = color_1
            else:
                item_value = self._convert_type(self.GetItem(item_id, column).GetText(), item_type)
            information[item_tag] = item_value
        information["check"] = is_checked

        return information

    def get_all_checked(self):
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
            color_255 = convert_rgb_1_to_255(color_1, decimals=3)
        else:
            color_1 = convert_rgb_255_to_1(color_255, decimals=3)
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
        """
        Sort items based on column and direction
        """
        columns = self.GetColumnCount()
        rows = self.GetItemCount()

        temp_data = []
        # Iterate over row and columns to get data
        for row in range(rows):
            temp_row = []

            for col in range(columns):
                item = self.GetItem(itemIdx=row, col=col)
                temp_row.append(item.GetText())

            temp_row.append(self.IsChecked(index=row))
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

    def on_clear_table_all(self, evt, ask=True):
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

        # get list data
        temp_data = sorted(self._get_list_data())
        # remove duplicates
        temp_data = list(k for k, _ in itertools.groupby(temp_data))

        # clear table
        self.DeleteAllItems()

        temp_data, checkData, bg_rgb, fg_rgb = self._restructure_list_data(temp_data)

        self._set_list_data(temp_data, checkData, bg_rgb, fg_rgb)

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
            tempRow.append(self.IsChecked(row))
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
        dlg = DialogBox(msg="Are you sure you would like to clear the table?", kind="Question")
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


class validator(wx.Validator):
    """Text validator."""

    def __init__(self, flag):
        wx.Validator.__init__(self)
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


class PopupBase(wx.PopupTransientWindow):
    """Create popup window to modify few uncommon settings"""

    ld_pos = None
    w_pos = None

    def __init__(self, parent, style=wx.BORDER_SIMPLE):
        wx.PopupTransientWindow.__init__(self, parent, style)

        self.make_panel()

        self.Bind(wx.EVT_LEFT_DOWN, self.on_mouse_left_down)
        self.Bind(wx.EVT_LEFT_UP, self.on_mouse_left_up)
        self.Bind(wx.EVT_MOTION, self.on_move)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_event)

    def make_panel(self):
        """Make popup window"""
        raise NotImplementedError("Must implement method")

    def on_key_event(self, evt):
        """Capture keyboard events"""
        key_code = evt.GetKeyCode()

        if key_code == wx.WXK_ESCAPE:  # key = esc
            self.Destroy()

        evt.Skip()

    def position_on_event(self, evt):
        """Position the window on an event location"""
        pos = evt.GetEventObject().ClientToScreen((0, 0))
        self.SetPosition(pos)

    def on_mouse_left_down(self, evt):
        """On left-click event"""
        self.Refresh()
        self.ld_pos = evt.GetEventObject().ClientToScreen(evt.GetPosition())
        self.w_pos = self.ClientToScreen((0, 0))
        self.CaptureMouse()

    def on_mouse_left_up(self, evt):
        """On left-release event"""
        if self.HasCapture():
            self.ReleaseMouse()

    def on_move(self, evt):
        """On move event"""
        if evt.Dragging() and evt.LeftIsDown() and self.w_pos is not None and self.ld_pos is not None:
            d_pos = evt.GetEventObject().ClientToScreen(evt.GetPosition())
            new_pos = (self.w_pos.x + (d_pos.x - self.ld_pos.x), self.w_pos.y + (d_pos.y - self.ld_pos.y))
            self.Move(new_pos)
