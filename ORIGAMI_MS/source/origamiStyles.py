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

def makeMenuItem(parent, text, id=-1, bitmap=None):
    """ Helper function to make a menu item with or without bitmap image """
    menuItem = wx.MenuItem(parent, id, text)
    if bitmap!=None:
        menuItem.SetBitmap(bitmap)
    
    return menuItem

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
    # ----
    
    