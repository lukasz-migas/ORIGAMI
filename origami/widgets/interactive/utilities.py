"""Various utilities"""
import wx
from origami.utils.system import RUNNING_UNDER_PYTEST

DIV_STYLE = wx.TE_MULTILINE | wx.TE_WORDWRAP | wx.TE_RICH2 if not RUNNING_UNDER_PYTEST else wx.TE_RICH
PUB_EVENT_LAYOUT_ADD = "interactive.layout.new"
PUB_EVENT_LAYOUT_REMOVE = "interactive.layout.remove"
PUB_EVENT_LAYOUT_UPDATE = "interactive.layout.update"
PUB_EVENT_TAB_REMOVE = "interactive.tab.remove"
PUB_EVENT_PLOT_ORDER = "interactive.plot.order"


DIV_STYLE = wx.TE_MULTILINE | wx.TE_WORDWRAP | wx.TE_RICH2 if not RUNNING_UNDER_PYTEST else wx.TE_RICH
