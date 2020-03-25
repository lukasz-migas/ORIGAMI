# Standard library imports
import logging

# Third-party imports
import wx

logger = logging.getLogger(__name__)


def DialogBox(exceptionTitle="", exceptionMsg="", type="Error", exceptionPrint=True):
    """
    Generic message box
    """

    logger_printer = logger.info
    if type == "Error":
        dlgStyle = wx.OK | wx.ICON_ERROR
        logger_printer = logger.error
    elif type == "Info":
        dlgStyle = wx.OK | wx.ICON_INFORMATION
    elif type == "Stop":
        dlgStyle = wx.OK | wx.ICON_STOP
    elif type == "Warning":
        dlgStyle = wx.OK | wx.ICON_EXCLAMATION
        logger_printer = logger.warning
    elif type == "Question":
        dlgStyle = wx.YES_NO | wx.ICON_QUESTION

    if exceptionPrint:
        logger_printer(exceptionMsg)

    dlg = wx.MessageDialog(None, exceptionMsg, exceptionTitle, dlgStyle)
    result = dlg.ShowModal()

    if type == "Question":
        return result


def DialogSimpleAsk(message="", title="", defaultValue="", value_type=None):

    if value_type is not None and value_type in ["float", "floatPos", "int", "intPos"]:
        dlg = wx.NumberEntryDialog(None, message, "", title, 0, -100000, 1000000)
    else:
        dlg = wx.TextEntryDialog(None, message, title, defaultValue)

    dlg.CentreOnScreen()

    if dlg.ShowModal() == wx.ID_CANCEL:
        return None

    result = dlg.GetValue()
    dlg.Destroy()
    return result
