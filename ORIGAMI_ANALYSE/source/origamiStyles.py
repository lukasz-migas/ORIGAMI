# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
#    Copyright (C) 2017 Lukasz G. Migas <lukasz.migas@manchester.ac.uk>
# 
#	 GitHub : https://github.com/lukasz-migas/ORIGAMI
#	 University of Manchester IP : https://www.click2go.umip.com/i/s_w/ORIGAMI.html
#	 Cite : 10.1016/j.ijms.2017.08.014
#
#    This program is free software. Feel free to redistribute it and/or 
#    modify it under the condition you cite and credit the authors whenever 
#    appropriate. 
#    The program is distributed in the hope that it will be useful but is 
#    provided WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE
# -------------------------------------------------------------------------


# This file creates various styles for the GUI
import wx
import time
import wx.lib.mixins.listctrl  as  listmix

# Styles
TEXT_STYLE_CV_R_L = wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.LEFT
# TEXT_STYLE_CV_R_L = wx.ALIGN_CENTER_VERTICAL|wx.LEFT

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

GAUGE_HEIGHT = 15
GAUGE_SPACE = 10
PANEL_SPACE_MAIN = 10


LISTCTRL_STYLE_MULTI = wx.LC_REPORT|wx.LC_VRULES|wx.LC_HRULES|wx.SUNKEN_BORDER
LISTCTRL_SORT = 1

# SLIDER_STYLE = wx.SL_HORIZONTAL|wx.SL_AUTOTICKS|wx.SL_LABELS
SLIDER_STYLE = wx.SL_HORIZONTAL| wx.SL_MIN_MAX_LABELS | wx.SL_VALUE_LABEL

# font = wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD)


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
    font = wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD)
    toggleBtn.SetFont(font)
    toggleBtn.SetForegroundColour(colorOff)
    
    return toggleBtn

def makeStaticText(parent, text):
    textBox = wx.StaticText(parent, wx.ID_ANY,
                            text, wx.DefaultPosition, 
                            wx.DefaultSize, 
                            TEXT_STYLE_CV_R_L)
    return textBox

def makeTextCtrl(parent, size=(wx.DefaultSize)):
    textBox = wx.TextCtrl(parent, wx.ID_ANY, ""  , wx.DefaultPosition, 
                            size, TEXT_STYLE_CV_R_L)
    return textBox
    
def makeSlider(parent, value, minValue, maxValue):
    slider = wx.Slider(parent, -1, value=value, minValue=minValue, 
                       maxValue=maxValue, size=(140, -1), style=SLIDER_STYLE)
    
    return slider

def makeCheckbox(parent, text):
    checkbox = wx.CheckBox(parent, -1, text, (3, 3))
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

def layout(parent, sizer):
    """Ensure correct panel layout - hack."""
    
    parent.SetMinSize((-1,-1))
    sizer.Fit(parent)
    parent.Layout()
    
    size = parent.GetSize()
    parent.SetSize((size[0]+1, size[1]+1))
    parent.SetSize(size)
    parent.SetMinSize(size)
# ----
    
class sortListCtrl(wx.ListCtrl, listmix.TextEditMixin, listmix.CheckListCtrlMixin):
    """ListCtrl with automatic sorter."""
    LISTCTRL_STYLE_MULTI = wx.LC_REPORT|wx.LC_VRULES|wx.LC_HRULES
    def __init__(self, parent, id=-1, pos=wx.DefaultPosition, size=wx.DefaultSize, style=LISTCTRL_STYLE_MULTI):#wx.LC_REPORT):
        wx.ListCtrl.__init__(self, parent, id, pos, size, style)
        listmix.TextEditMixin.__init__(self)
        listmix.CheckListCtrlMixin.__init__(self)
        
        
        self._data = None
        self._currentColumn = 0
        self._currentDirection = 1
        self._secondarySortColumn = None
        
        self._defaultColour = self.GetBackgroundColour()
        self._altColour = self.GetBackgroundColour()
        self._currentAttr = wx.ListItemAttr()
        
        self._getItemTextFn = None
        self._getItemAttrFn = None
        
        # set events
        self.Bind(wx.EVT_LIST_COL_CLICK, self._onColClick, self)
    # ----
    
    
    def OnGetItemText(self, row, col):
        """Get text for selected cell."""
        
        if self._getItemTextFn != None:
            return self._getItemTextFn(row, col)
        else:
            return unicode(self._data[row][col])
    # ----
    
    
    def OnGetItemAttr(self, row):
        """Get attributes for selected cell."""
        
        # get user defined attr
        attr = None
        if self._getItemAttrFn != None:
            attr = self._getItemAttrFn(row)
        
        # set background colour
        if attr and attr.HasBackgroundColour():
            self._currentAttr.SetBackgroundColour(attr.GetBackgroundColour())
        elif row % 2:
            self._currentAttr.SetBackgroundColour(self._defaultColour)
        else:
            self._currentAttr.SetBackgroundColour(self._altColour)
        
        # set text colour
        if attr:
            self._currentAttr.SetTextColour(attr.GetTextColour())
        
        # set font
        if attr:
            self._currentAttr.SetFont(attr.GetFont())
        
        return self._currentAttr
    # ----
    
    
    def OnGetItemImage(self, row):
        return -1
    # ----
    
    
    def _onColClick(self, evt):
        """Sort data by this column."""
        
        # check data
        if not self._data:
            print('Data empty')
            return
        
        # get selected column
        oldCol = self._currentColumn
        newCol = evt.GetColumn()
        
        # update direction flag
        if oldCol == newCol:
            direction = -1 * self._currentDirection
        else:
            direction = 1
        
        # sort
        self._sort(newCol, direction)
        evt.Skip()
    # ----
    
    
    def _sort(self, col, direction):
        """Sort list."""
        
        # unselect all items
        self.unselectAll()
        
        # set new flags
        self._currentColumn = min(col, self.GetColumnCount()-1)
        self._currentDirection = direction
        
        # sort data
        if self.IsVirtual():
            self._data.sort(self._sortItems)
            self.Refresh()
        else:
            self.SortItems(self._sortData)
            self.updateItemsBackground()
    # ----
    
    
    def _sortData(self, item1, item2):
        """Sort data."""
        return self._sortItems(self._data[item1], self._data[item2])
    # ----
    
    
    def _sortItems(self, item1, item2):
        """Sort items."""
        
        comp = cmp(item1[self._currentColumn], item2[self._currentColumn])
        if comp == 0 and self._secondarySortColumn != None:
            comp = cmp(item1[self._secondarySortColumn], item2[self._secondarySortColumn])
        
        return comp * self._currentDirection
    # ----
    
    
    def _columnSorter(self, key1, key2):
        """Sort data."""
        
        # check data
        if not self._data:
            return self._currentDirection
        
        # get values
        item1 = self._data[key1][self._currentColumn]
        item2 = self._data[key2][self._currentColumn]
        
        # compare values
        comp = cmp(item1, item2)
        if comp == 0 and self._secondarySortColumn != None:
            item1 = self._data[key1][self._secondarySortColumn]
            item2 = self._data[key2][self._secondarySortColumn]
            comp = cmp(item1, item2)
        
        # set direction
        comp *= self._currentDirection
        
        return comp
    # ----
    
    
    def setItemTextFn(self, fn):
        """Set OnGetItemText callback."""
        self._getItemTextFn = fn
    # ----
    
    
    def setItemAttrFn(self, fn):
        """Set OnGetItemAttr callback."""
        self._getItemAttrFn = fn
    # ----
    
    
    def setSecondarySortColumn(self, col):
        """Set secondary column to sort by."""
        self._secondarySortColumn = col
    # ----
    
    
    def setDataMap(self, data):
        """Set data."""
        self._data = data
    # ----
    
    
    def setAltColour(self, colour):
        """Set alternate background colour."""
        
        if colour:
            self._altColour = colour
        else:
            self._altColour = self._defaultColour
    # ----
    
    
    def getSelected(self):
        """Return indexes of selected items."""
        
        selected = []
        
        i = -1
        while True:
            i = self.GetNextItem(i, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
            if i == -1:
                break
            else:
                selected.append(i)
        
        selected.sort()
        return selected
    # ----
    
    
    def sort(self, col=None):
        """Sort by last or selected column."""
        
        # get column and direction
        direction = self._currentDirection
        if col == None:
            col = self._currentColumn
        else:
            if self._currentColumn != col:
                direction = 1
        
        # sort
        self._sort(col, direction)
    # ----
    
    
    def deleteColumns(self):
        """Delete all columns."""
        
        self._currentColumn = 0
        while self.GetColumnCount():
            self.DeleteColumn(0)
    # ----
    
    
    def unselectAll(self):
        """Unselect all items."""
        
        i = -1
        while True:
            i = self.GetNextItem(i, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
            self.SetItemState(i, 0, wx.LIST_STATE_SELECTED)
            if i == -1:
                break
    # ----
    
    
    def updateItemsBackground(self):
        """Update item background colours."""
        
        # check colours
        if self._defaultColour == self._altColour:
            return
        
        # update each row
        for row in xrange(self.GetItemCount()):
            if row % 2:
                self.SetItemBackgroundColour(row, self._altColour)
            else:
                self.SetItemBackgroundColour(row, self._defaultColour)
    # ----
    
    
    def copyToClipboard(self, selected=False):
        """Copy current data to clipboard."""
        
        buff = ''
        
        # get selected only
        if selected:
            for row in self.getSelected():
                line = ''
                for col in range(self.GetColumnCount()):
                    item = self.GetItem(row, col)
                    line += item.GetText() + '\t'
                buff += '%s\n' % (line.rstrip())
        
        # get all
        else:
            for row in range(self.GetItemCount()):
                line = ''
                for col in range(self.GetColumnCount()):
                    item = self.GetItem(row, col)
                    line += item.GetText() + '\t'
                buff += '%s\n' % (line.rstrip())
        
        # make text object for data
        obj = wx.TextDataObject()
        obj.SetText(buff.rstrip())
        
        # paste to clipboard
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(obj)
            wx.TheClipboard.Close()
    # ----
class gauge(wx.Gauge):
    """Gauge."""
     
    def __init__(self, parent, id=-1, size=(-1, GAUGE_HEIGHT), style=wx.GA_HORIZONTAL):
        wx.Gauge.__init__(self, parent, id, size=size, style=style)
    # ----
     
     
    def pulse(self):
        """Pulse gauge."""
         
        self.Pulse()
        try: wx.Yield()
        except: pass
        time.sleep(0.05)
    # ----
class gaugePanel(wx.Dialog):
    """Processing panel."""
     
    def __init__(self, parent, label, title='Progress...'):
        wx.Dialog.__init__(self, parent, -1, title, style=(wx.CAPTION | wx.STAY_ON_TOP))
         
        self.parent = parent
        self.label = label
         
        # make GUI
        panel = wx.Panel(self, -1)
        self.label = wx.StaticText(panel, -1, label)
        self.label.SetFont(wx.SMALL_FONT)
        self.gauge = wx.Gauge(panel, -1, size=(250, GAUGE_HEIGHT))
         
        # pack elements
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.label, 0, wx.BOTTOM, 5)
        sizer.Add(self.gauge, 0, wx.EXPAND, 0)
         
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(sizer, 0, wx.ALL, PANEL_SPACE_MAIN)
         
        self.Layout()
        mainSizer.Fit(self)
        self.SetSizer(mainSizer)
        try: wx.Yield()
        except: pass
    # ----
     
     
    def setLabel(self, label):
        """Set new label."""
         
        self.label.SetLabel(label)
        try: wx.Yield()
        except: pass
    # ----
     
     
    def pulse(self):
        """Pulse gauge."""
         
        self.gauge.Pulse()
         
        try: wx.Yield()
        except: pass
        time.sleep(0.01)
    # ----
     
     
    def show(self):
        """Show panel."""
         
        self.Center()
        self.MakeModal(True)
        self.Show()
         
        try: wx.Yield()
        except: pass
    # ----
     
     
    def close(self):
        """Hide panel"""
         
        self.MakeModal(False)
        self.Destroy()
    # ----
class EditableListCtrl(wx.ListCtrl, listmix.TextEditMixin, listmix.CheckListCtrlMixin):
    """
    Editable list
    """
    # TODO Add checkbox to the first column - useful for selecting ions to plot?
    def __init__(self, parent, ID=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0): 
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.TextEditMixin.__init__(self)
        listmix.CheckListCtrlMixin.__init__(self)
        
class bgrPanel(wx.Panel):
    """Simple panel with image background."""
    
    def __init__(self, parent, id, image, size=(-1,-1)):
        wx.Panel.__init__(self, parent, id, size=size)
        self.SetMinSize(size)
        
        self.image = image
        
        # set paint event to tile image
        wx.EVT_PAINT(self, self._onPaint)
    # ----
    
    
    def _onPaint(self, event=None):
        
        # create paint surface
        dc = wx.PaintDC(self)
        #dc.Clear()
        
        # tile/wallpaper the image across the canvas
        for x in range(0, self.GetSize()[0], self.image.GetWidth()):
            dc.DrawBitmap(self.image, x, 0, True)
    # ----
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

     
    
