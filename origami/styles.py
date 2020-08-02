"""This file creates various styles for the GUI"""

# Standard library imports
import logging
import itertools
from ast import literal_eval
from operator import itemgetter

# Third-party imports
import wx
import numpy as np
from wx.lib.agw import supertooltip as superTip
from natsort.natsort import natsorted

# Local imports
from origami.utils.color import convert_rgb_1_to_255
from origami.utils.color import convert_rgb_255_to_1
from origami.config.config import CONFIG
from origami.utils.converters import str2int
from origami.utils.converters import str2num
from origami.utils.converters import byte2str
from origami.gui_elements.misc_dialogs import DialogBox
from origami.gui_elements.dialog_color_picker import DialogColorPicker

LOGGER = logging.getLogger(__name__)
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


def make_spin_ctrl_int(parent, value, min_value, max_value, size=(-1, -1), evtid=-1, name="name"):
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


def make_staticbox(parent, title, size, color):
    """Make staticbox"""
    static_box = wx.StaticBox(parent, wx.ID_ANY, title, size=size, style=wx.SB_FLAT)
    font = wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
    static_box.SetForegroundColour(color)
    static_box.SetFont(font)

    return static_box


def make_toggle_btn(parent, text, color_off, name="other", size=(40, -1)):
    """Make toggle button"""
    toggle_btn = wx.ToggleButton(
        parent, wx.ID_ANY, text, wx.DefaultPosition, size, style=wx.ALIGN_CENTER_VERTICAL, name=name
    )
    font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
    toggle_btn.SetFont(font)
    toggle_btn.SetForegroundColour(color_off)

    return toggle_btn


def make_static_text(parent, text):
    """Make static text"""
    text_box = wx.StaticText(
        parent, wx.ID_ANY, text, wx.DefaultPosition, wx.DefaultSize, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.LEFT
    )
    return text_box


def make_text_ctrl(parent, size=wx.DefaultSize):
    """Make text control"""
    text_ctrl = wx.TextCtrl(
        parent, wx.ID_ANY, "", wx.DefaultPosition, size, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.LEFT
    )
    return text_ctrl


def make_slider(parent, value, min_value, max_value):
    """Make slider"""
    slider = wx.Slider(
        parent, -1, value=value, minValue=min_value, maxValue=max_value, size=(140, -1), style=SLIDER_STYLE
    )
    return slider


def make_checkbox(parent, text, style=wx.ALIGN_LEFT, evt_id=-1, name="", tooltip=None):
    """Make checkbox"""
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
    """Make tooltips with specified delay time"""
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
    """Make super tooltip"""

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
    if wx.Platform == "__WXMAC__":  # noqa
        wx.SystemOptions.SetOption("mac.listctrl.always_use_generic", True)
        wx.ToolTip.SetDelay(1500)
        global SCROLL_DIRECTION  # noqa
        SCROLL_DIRECTION = -1


class ActivityIndicatorMixin:
    """Activity indicator mixin"""

    # ui elements
    activity_indicator = None

    def on_progress(self, is_running: bool, message: str):  # noqa
        """Handle extraction progress"""
        if self.activity_indicator is None:
            LOGGER.warning("Cannot indicate activity - it has not been instantiated in the window")
            return

        # show indicator
        if is_running:
            self.activity_indicator.Show()
            self.activity_indicator.Start()
        else:
            self.activity_indicator.Hide()
            self.activity_indicator.Stop()
        self.Update()  # noqa


class DocumentationMixin:
    """HTML documentation mixin"""

    # documentation attributes
    HELP_MD = None
    HELP_LINK = None
    PANEL_STATUSBAR_COLOR = wx.BLUE

    # attributes
    _icons = None

    # ui elements
    info_btn = None
    settings_btn = None
    display_label = None

    def on_open_info(self, _evt):
        """Open help window to inform user on how to use this window / panel"""
        from origami.gui_elements.panel_html_viewer import PanelHTMLViewer

        if self.HELP_LINK:
            PanelHTMLViewer(self, link=self.HELP_LINK)
        elif self.HELP_MD:
            PanelHTMLViewer(self, md_msg=self.HELP_MD)

    def on_open_popup_settings(self, evt):
        """Open settings popup window"""

    def make_info_button(self, panel):
        """Make clickable information button"""
        info_btn = make_bitmap_btn(panel, wx.ID_ANY, self._icons.info, style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL)
        set_tooltip(info_btn, "Open documentation page about this panel (online)")
        info_btn.Bind(wx.EVT_BUTTON, self.on_open_info)
        return info_btn

    def make_settings_button(self, panel):
        """Make clickable information button"""
        settings_btn = make_bitmap_btn(
            panel, wx.ID_ANY, self._icons.gear, style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL
        )
        set_tooltip(settings_btn, "Open popup window with settings specific to this panel")
        settings_btn.Bind(wx.EVT_BUTTON, self.on_open_popup_settings)
        return settings_btn

    def make_statusbar(self, panel, position: str = "left"):
        """Make make-shift statusbar"""
        # add info button
        self.info_btn = self.make_info_button(panel)

        self.display_label = wx.StaticText(panel, wx.ID_ANY, "")
        self.display_label.SetForegroundColour(self.PANEL_STATUSBAR_COLOR)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        if position == "left":
            sizer.Add(self.info_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 5)
            sizer.Add(self.display_label, 1, wx.ALIGN_CENTER_VERTICAL)
        else:
            sizer.Add(self.display_label, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 5)
            sizer.Add(self.info_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        return sizer

    def set_message(self, msg: str, duration: int = 5000):
        """Set message for a period of time

        Parameters
        ----------
        msg : str
            message to be displayed in the statusbar
        duration : int
            how long the message should be displayed for
        """
        self.display_label.SetLabel(msg)
        if duration > 0:
            wx.CallLater(duration, self.display_label.SetLabel, "")


class ColorGetterMixin:
    """Mixin class to provide easy retrieval of color(s)"""

    def on_get_color(self, _evt):
        """Convenient method to get new color"""
        dlg = DialogColorPicker(self, CONFIG.custom_colors)
        if dlg.ShowModal() == wx.ID_OK:
            color_255, color_1, font_color = dlg.GetChosenColour()
            CONFIG.custom_colors = dlg.GetCustomColours()

            return color_255, color_1, font_color
        return None, None, None


class Dialog(wx.Dialog, ActivityIndicatorMixin, DocumentationMixin):
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
            self.on_close(None)
            return

        if evt is not None:
            evt.Skip()

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


class MiniFrame(wx.MiniFrame, ActivityIndicatorMixin, DocumentationMixin):
    """Proxy of MiniFrame"""

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
        """Keyboard events"""
        key_code = evt.GetKeyCode()
        # exit window
        if key_code == wx.WXK_ESCAPE:
            self.on_close(None)

        if evt is not None:
            evt.Skip()

    def filter_keys(self, evt):
        """Filter keys"""

    def on_close(self, evt, force: bool = False):
        """Destroy this frame."""
        self.Destroy()

    def on_ok(self, _evt):
        """Close the frame gracefully"""
        self.Destroy()

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
        self.SetSizer(main_sizer)
        self.Layout()


class ListCtrl(wx.ListCtrl):
    """ListCtrl"""

    def __init__(self, parent, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.LC_REPORT, **kwargs):
        wx.ListCtrl.__init__(self, parent, wx.ID_ANY, pos, size, style)

        if hasattr(self, "EnableCheckBoxes"):
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
                item_value, color_1 = self._convert_color(self.GetItemBackgroundColour(item_id))
                information["color_255to1"] = color_1
            else:
                item_value = self._convert_type(self.GetItem(item_id, column).GetText(), item_type)
            information[item_tag] = item_value
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
            color_255 = convert_rgb_1_to_255(color_1, decimals=3)
        else:
            color_1 = convert_rgb_255_to_1(color_255, decimals=3)
        return color_255, color_1

    def on_column_click(self, evt):
        """Interact on column click"""
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
        """Check all rows in the table"""
        rows = self.GetItemCount()

        for row in range(rows):
            self.CheckItem(row, check=check)

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

        # define navigation keys
        nav_keys = (
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
        if key in nav_keys or key < wx.WXK_SPACE or key == wx.WXK_DELETE:
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
