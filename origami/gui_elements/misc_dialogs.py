# Standard library imports
import logging

# Third-party imports
import wx

# Local imports
from origami.utils.converters import str2num

logger = logging.getLogger(__name__)


# noinspection PyPep8Naming
def DialogBox(title="", msg="", kind="Error", show_exception=True, parent=None):
    """Generic dialog box that displays any kind of message

    Parameters
    ----------
    title : str
        title of  the dialog box
    msg : str
        message to be shown to the user
    kind : str
        message to be shown to the user
    show_exception : bool
        if `True`, exception will be printed in the logger
    parent
        parent of the window object

    Returns
    -------
    result : bool
        value if  question was the type specified by the user
    """

    logger_printer = logger.info
    if kind == "Error":
        style = wx.OK | wx.ICON_ERROR
        logger_printer = logger.error
    elif kind == "Info":
        style = wx.OK | wx.ICON_INFORMATION
    elif kind == "Stop":
        style = wx.OK | wx.ICON_STOP
    elif kind == "Warning":
        style = wx.OK | wx.ICON_EXCLAMATION
        logger_printer = logger.warning
    elif kind == "Question":
        style = wx.YES_NO | wx.ICON_QUESTION
    else:
        style = wx.OK | wx.ICON_INFORMATION

    if show_exception:
        logger_printer(msg)

    dlg = wx.MessageDialog(parent, msg, title, style)
    dlg.Raise()
    dlg.CenterOnParent()
    result = dlg.ShowModal()

    if kind == "Question":
        return result


# noinspection PyPep8Naming
def DialogSimpleAsk(message="", title="", value="", value_type=None, parent=None):

    if value_type is not None and value_type in ["int", "intPos"]:
        if value is None:
            value = 0
        dlg = wx.NumberEntryDialog(parent, message, title, "", value, -100000, 1000000)
    else:
        dlg = wx.TextEntryDialog(parent, message, title, value)

    dlg.CenterOnParent()

    if dlg.ShowModal() == wx.ID_CANCEL:
        return None

    result = dlg.GetValue()

    if value_type in ["float", "floatPos"]:
        result = str2num(result)

    dlg.Destroy()
    return result


# noinspection PyPep8Naming
def DialogNumberAsk(message="", title="", value="", min_value=-100000, max_value=100000, parent=None):
    """Dialog class to ask for integer numbers"""

    if value is None:
        value = 0
    dlg = wx.NumberEntryDialog(parent, message, title, "", value, min_value, max_value)
    dlg.CenterOnParent()

    if dlg.ShowModal() == wx.ID_CANCEL:
        return None

    result = dlg.GetValue()
    dlg.Destroy()
    return result
