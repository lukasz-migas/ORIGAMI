# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
#    Copyright (C) 2017 Lukasz G. Migas <lukasz.migas@manchester.ac.uk>

#    This program is free software. Feel free to redistribute it and/or 
#    modify it under the condition you cite and credit the authors whenever 
#    appropriate. 
#    The program is distributed in the hope that it will be useful but is 
#    provided WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE
# -------------------------------------------------------------------------

import wx


# Styles
TEXT_STYLE_CV_R_L = wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.LEFT
TEXT_STYLE_CENT = wx.ALIGN_CENTRE
TEXT_STYLE_CENT_VERT = wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.LEFT
TEXT_STYLE_SEP = wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL

ALL_CENTER_VERT = wx.ALL|wx.ALIGN_CENTER_VERTICAL
ALL_CENTER_HORZ = wx.ALL|wx.ALIGN_CENTER_HORIZONTAL
BTN_STYLE = wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL|wx.RIGHT|wx.LEFT

COMBO_STYLE = wx.CB_READONLY

# Sizes
COMBO_SIZE = 120
COMBO_SIZE_COMPACT = 80
BTN_SIZE = 60
TGL_SIZE = 40
TXTBOX_SIZE = 45


LISTCTRL_STYLE_MULTI = wx.LC_REPORT|wx.LC_VRULES|wx.LC_HRULES|wx.SUNKEN_BORDER
LISTCTRL_SORT = 1

def makeStaticBox(parent, title, size, color, id=-1):
    staticBox = wx.StaticBox(parent, id, title, size=size)
    font = wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.BOLD)
    staticBox.SetForegroundColour(color)
    staticBox.SetFont(font)
    
    return staticBox


def makeToggleBtn(parent, text, colorOff):
    toggleBtn = wx.ToggleButton(parent, wx.ID_ANY,
                                text, wx.DefaultPosition, 
                                wx.Size( TGL_SIZE,-1 ), 0 )
#     font = wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD)
#     toggleBtn.SetFont(font)
#     toggleBtn.SetForegroundColour(colorOff)
    
    return toggleBtn

def makeStaticText(parent, text):
    textBox = wx.StaticText(parent, wx.ID_ANY,
                            text, wx.DefaultPosition, 
                            wx.DefaultSize, 
                            TEXT_STYLE_CV_R_L)
    
    return textBox

def makeTextCtrl(parent):
    textBox = wx.TextCtrl(parent, wx.ID_ANY,
                            ""  , wx.DefaultPosition, 
                            wx.DefaultSize, 
                            TEXT_STYLE_CV_R_L)
    
    return textBox
    
    
    
    
    