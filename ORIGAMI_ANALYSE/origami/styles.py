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

# This file creates various styles for the GUI

import wx
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

# SLIDER_STYLE = wx.SL_HORIZONTAL|wx.SL_AUTOTICKS|wx.SL_LABELS
SLIDER_STYLE = wx.SL_HORIZONTAL | wx.SL_MIN_MAX_LABELS | wx.SL_VALUE_LABEL

# font = wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD)


def makeMenuItem(parent, text, id=-1, bitmap=None, help_text=None,
                 kind=wx.ITEM_NORMAL):
    """ Helper function to make a menu item with or without bitmap image """
    menuItem = wx.MenuItem(parent, id, text, kind=kind)
    if bitmap != None:
        menuItem.SetBitmap(bitmap)

    if help_text != None:
        menuItem.SetHelp(help_text)

    return menuItem


def makeStaticBox(parent, title, size, color, id=-1):
    staticBox = wx.StaticBox(parent, id, title, size=size, style=wx.SB_FLAT)
    font = wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.BOLD)
    staticBox.SetForegroundColour(color)
    staticBox.SetFont(font)

    return staticBox


def makeToggleBtn(parent, text, colorOff, name="other", size=(40, -1)):
    toggleBtn = wx.ToggleButton(parent, wx.ID_ANY,
                                text, wx.DefaultPosition,
                                size,
                                style=wx.ALIGN_CENTER_VERTICAL,
                                name=name)
    font = wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD)
    toggleBtn.SetFont(font)
    toggleBtn.SetForegroundColour(colorOff)

    return toggleBtn


def makeStaticText(parent, text):
    textBox = wx.StaticText(parent, wx.ID_ANY,
                            text, wx.DefaultPosition,
                            wx.DefaultSize,
                             wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.LEFT)
    return textBox


def makeTextCtrl(parent, size=(wx.DefaultSize)):
    textBox = wx.TextCtrl(parent, wx.ID_ANY, ""  , wx.DefaultPosition,
                            size, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.LEFT)
    return textBox


def makeSlider(parent, value, minValue, maxValue):
    slider = wx.Slider(parent, -1, value=value, minValue=minValue,
                       maxValue=maxValue, size=(140, -1), style=SLIDER_STYLE)
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
# ----


def makeSuperTip(parent, title='Title', text='Insert message', delay=5,
                 headerLine=False, footerLine=False, headerImg=None, **kwargs):

    if kwargs:
        title = kwargs['help_title']
        text = kwargs['help_msg']
        headerImg = kwargs['header_img']
        headerLine = kwargs['header_line']
        footerLine = kwargs['footer_line']

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

    if headerImg != None:
        tip.SetHeaderBitmap(headerImg)

    return tip


class bgrPanel(wx.Panel):
    """Simple panel with image background."""

    def __init__(self, parent, id, image, size=(-1, -1)):
        wx.Panel.__init__(self, parent, id, size=size)
        self.SetMinSize(size)

        self.image = image

        # set paint event to tile image
        wx.EVT_PAINT(self, self._onPaint)
    # ----

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
    # ----

    def Clone(self):
        return validator(self.flag)
    # ----

    def TransferToWindow(self):
        return True
    # ----

    def TransferFromWindow(self):
        return True
    # ----

    def OnChar(self, evt):
        ctrl = self.GetWindow()
        value = ctrl.GetValue()
        key = evt.GetKeyCode()

        # define navigation keys
        navKeys = (wx.WXK_HOME, wx.WXK_LEFT, wx.WXK_UP,
                    wx.WXK_END, wx.WXK_RIGHT, wx.WXK_DOWN,
                    wx.WXK_NUMPAD_HOME, wx.WXK_NUMPAD_LEFT, wx.WXK_NUMPAD_UP,
                    wx.WXK_NUMPAD_END, wx.WXK_NUMPAD_RIGHT, wx.WXK_NUMPAD_DOWN)

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
        elif self.flag == 'int' and chr(key) in '-0123456789eE':
            evt.Skip()
            return

        # positive int only
        elif self.flag == 'intPos' and chr(key) in '0123456789eE':
            evt.Skip()
            return

        # floats only
        elif self.flag == 'float' and (chr(key) in '-0123456789.eE'):
            evt.Skip()
            return

        # positive floats only
        elif self.flag == 'floatPos' and (chr(key) in '0123456789.eE'):
            evt.Skip()
            return

        # error
        else:
            wx.Bell()
            return

