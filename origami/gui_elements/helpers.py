"""Various helper functions"""
# Third-party imports
import wx
from wx.lib.agw import supertooltip as superTip

# Local imports
from origami.utils.color import convert_rgb_1_to_255


def get_name_from_evt(evt) -> str:
    """Get widget name"""
    source = ""
    if hasattr(evt, "GetEventObject"):
        source = evt.GetEventObject()
        if hasattr(source, "GetName"):
            source = source.GetName()
    return source


def get_widget_from_evt(evt) -> str:
    """Get widget name"""
    widget = None
    if hasattr(evt, "GetEventObject"):
        widget = evt.GetEventObject()
    return widget


def make_spin_ctrl_double(parent, value, min_value, max_value, increment_value, size=(-1, -1), evt_id=-1, name="name"):
    """Convenient way to initialize SpinCtrlDouble"""
    spin_ctrl = wx.SpinCtrlDouble(
        parent,
        evt_id,
        value=str(value),
        min=min_value,
        max=max_value,
        initial=value,
        inc=increment_value,
        size=size,
        name=name,
    )
    return spin_ctrl


def make_spin_ctrl_int(parent, value, min_value, max_value, size=(-1, -1), evt_id=-1, name="name"):
    """Convenient way to initialize SpinCtrl"""
    spin_ctrl = wx.SpinCtrl(
        parent,
        evt_id,
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
    name="",
):
    """Convenient way to initialize bitmap btn"""
    bitmap_btn = wx.BitmapButton(parent, evt_id, icon, size=size, style=style, name=name)
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


def get_item_font(size=10, family=wx.FONTFAMILY_DEFAULT, style=wx.FONTSTYLE_NORMAL, weight=wx.FONTWEIGHT_BOLD):
    """Get item font"""
    font = wx.Font(size, family, style, weight)
    return font


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
        parent,
        -1,
        value=value,
        minValue=min_value,
        maxValue=max_value,
        size=(140, -1),
        style=wx.SL_HORIZONTAL | wx.SL_MIN_MAX_LABELS | wx.SL_VALUE_LABEL,
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
    tip.SetStartDelay()
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


class TableConfig(dict):
    """Table configuration object"""

    def __init__(self):  # noqa
        self.last_idx = -1

    def add(self, name: str, tag: str, dtype: str, width: int, show: bool = True, hidden: bool = False):
        """Add an item to the configuration"""
        self.last_idx += 1
        self[self.last_idx] = {
            "name": name,
            "tag": tag,
            "type": dtype,
            "show": show,
            "width": width,
            "order": self.last_idx,
            "id": wx.NewIdRef(),
            "hidden": hidden,
        }

    def find_col_id(self, tag: str):
        """Find column id by the tag"""
        for col_id, col_info in self.items():
            if col_info["tag"] == tag:
                return col_id
        return -1
