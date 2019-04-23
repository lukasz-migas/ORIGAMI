# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
#    Copyright (C) 2017-2018 Lukasz G. Migas
#    <lukasz.migas@manchester.ac.uk> OR <lukas.migas@yahoo.com>
#
# 	 GitHub : https://github.com/lukasz-migas/ORIGAMI
# 	 University of Manchester IP : https://www.click2go.umip.com/i/s_w/ORIGAMI.html
# 	 Cite : 10.1016/j.ijms.2017.08.014
#
#    This program is free software. Feel free to redistribute it and/or
#    modify it under the condition you cite and credit the authors whenever
#    appropriate.
#    The program is distributed in the hope that it will be useful but is
#    provided WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE
# -------------------------------------------------------------------------
# __author__ lukasz.g.migas

import wx


def dlgBox(exceptionTitle="", exceptionMsg="", type="Error", exceptionPrint=True):
    """
    Generic message box
    """

    if type == "Error":
        dlgStyle = wx.OK | wx.ICON_ERROR
    elif type == "Info":
        dlgStyle = wx.OK | wx.ICON_INFORMATION
    elif type == "Stop":
        dlgStyle = wx.OK | wx.ICON_STOP
    elif type == "Warning":
        dlgStyle = wx.OK | wx.ICON_EXCLAMATION
    elif type == "Question":
        dlgStyle = wx.YES_NO | wx.ICON_QUESTION

    if exceptionPrint:
        print(exceptionMsg)
    dlg = wx.MessageDialog(None, exceptionMsg, exceptionTitle, dlgStyle)
    result = dlg.ShowModal()

    if type == "Question":
        return result


def dlgAsk(message='', defaultValue=''):
    dlg = wx.TextEntryDialog(None,  # parent
                             message,
                             defaultValue)

    if dlg.ShowModal() == wx.ID_CANCEL:
        return False

    result = dlg.GetValue()
    dlg.Destroy()
    return result

