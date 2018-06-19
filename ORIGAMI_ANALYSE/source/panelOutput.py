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

# load libs
from __future__ import division
import wx
import wx.lib.mixins.listctrl as listmix
import wx.lib.scrolledpanel
from ids import *
from wx import ID_ANY
from toolbox import str2int, str2num, convertRGB1to255, convertRGB1toHEX, find_nearest, find_limits_list
import numpy as np
from styles import *
from os import getcwd
from operator import itemgetter
import dialogs as dialogs
import re
from collections import defaultdict
from bokeh.plotting import figure, show, save, ColumnDataSource, Column, gridplot
from bokeh.models import (HoverTool, LinearColorMapper, Label, ColorBar, 
                          AdaptiveTicker, LogColorMapper, LogTicker,
                          BasicTickFormatter, NumeralTickFormatter,
                          FixedTicker, FuncTickFormatter)
from bokeh.layouts import (column, widgetbox, layout, gridplot, row)
from bokeh.models.widgets import Panel, Tabs, Div
import matplotlib.colors as colors
import matplotlib.cm as cm
import webbrowser
from bokeh.models.tickers import FixedTicker
import time
from massLynxFcns import linearize_data

class dlgOutputInteractive(wx.MiniFrame):
    """Save data in an interactive format"""
    
    def __init__(self, parent, icons, presenter, config):
        wx.MiniFrame.__init__(self, parent, -1, "Save Interactive Plots", 
                              style= (wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER | 
                                      wx.RESIZE_BOX | wx.MAXIMIZE_BOX ))
        
        self.displaysize = wx.GetDisplaySize()
        self.view = parent
        self.icons = icons
        self.presenter = presenter 
        self.config = config
        self.documentsDict = self.presenter.documentsDict
        self.docsText = self.presenter.docsText
        self.currentPath = self.presenter.currentPath
        
        self.currentItem = None
        self.loading = False
        self.listOfPlots = []
        
        # Set up tools
        self.tools = ""
        self.activeDrag = None
        self.activeWheel = None
        self.activeInspect = None
        
        self.allChecked = True
        
        self.reverse = False
        self.lastColumn = None
        self.filtered = False
        self.listOfSelected = []
        
        self.makeGUI()
        self.populateTable()
        self.onChangeSettings(evt=None)
        self.onEnableDisableItems(evt=None)
        
        # bind
        wx.EVT_CLOSE(self, self.onClose)
        self.Bind(wx.EVT_CHAR_HOOK, self.OnKey)
        
        
        # fit layout
        self.sizer.Fit(self)
        self.SetSizer(self.sizer)
        self.SetFocus()
        self.CentreOnParent()
        self.Maximize()
        
#         # add a couple of accelerators
#         accelerators = [
#             (wx.ACCEL_NORMAL, ord('S'), ID_interactivePanel_select_item),
#             ]
#         self.SetAcceleratorTable(wx.AcceleratorTable(accelerators))
#         
#         wx.EVT_MENU(self, ID_interactivePanel_select_item, self.onCheckItem)
        
    def onClose(self, evt):
        self.config.interactiveParamsWindow_on_off = False
        self.Destroy()
        
    def OnKey(self, evt):
        keyCode = evt.GetKeyCode()
        if keyCode == wx.WXK_ESCAPE: # key = esc
            self.onClose(evt=None)
        elif keyCode == 83: # key = S
            self.onItemCheck(evt=None)
            
        if evt != None: evt.Skip()
        
    def onItemCheck(self, evt):
        try:
            check = not self.itemsList.IsChecked(index=self.currentItem)
            self.itemsList.CheckItem(self.currentItem, check)
        except TypeError:
            pass
        
    def onItemActivated(self, evt):
        """Create annotation for activated peak."""
        self.currentItem, __ = self.itemsList.HitTest(evt.GetPosition())
        
    def onItemClicked(self, evt):
        keyCode = evt.GetKeyCode()
        if keyCode == wx.WXK_UP or keyCode == wx.WXK_DOWN:
            self.currentItem = evt.m_itemIndex
        else:
            self.currentItem = evt.m_itemIndex

        if evt != None:
            evt.Skip()
    # ----
        
    def makeGUI(self):
        """Make GUI elements."""
        
#         # splitter window
#         self.split_panel = wx.SplitterWindow(self, wx.ID_ANY, wx.DefaultPosition,
#                                         wx.DefaultSize, 
#                                         wx.TAB_TRAVERSAL|wx.SP_3DSASH|wx.SP_LIVE_UPDATE)
        
#         # make panels
#         self.settings_panel = self.makeSettingsPanel(self.split_panel)
#         self.settings_panel.SetSize((245,-1))
#         self.settings_panel.SetMinSize((245, -1))
#         self.settings_panel.SetMaxSize((245, -1))
#         
#         self.plot_panel = self.makePlotPanel(self.split_panel)
#         self.plot_panel.SetSize((600,-1))
#         self.plot_panel.SetMinSize((600,-1))
#         self.plot_panel.SetMaxSize((600,-1))
#         
#         self.split_panel.SplitVertically(self.settings_panel, self.plot_panel)
#         self.split_panel.SetSashGravity(0.0)
#         self.split_panel.SetSashSize(5)
#         self.split_panel.SetSashPosition((320))
        
        # make GUI elements
        preToolbar = self.makePreToolbar()
        self.makeItemsList()
        editor = self.makeItemEditor()
        buttons = self.makeDlgButtons()
        
        
        # Add to grid sizer
        sizer_left = wx.BoxSizer(wx.VERTICAL)
        sizer_left.Add(preToolbar, 0, wx.EXPAND, 0)
        sizer_left.Add(self.itemsList, 1, wx.EXPAND| wx.ALL, 0)
         
        sizer_right = wx.BoxSizer(wx.VERTICAL)
        sizer_right.Add(editor, 1, wx.EXPAND| wx.ALL, 0)
        sizer_right.Add(buttons, 0, wx.EXPAND, 0)
        
        # pack elements
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(sizer_left, 0, wx.EXPAND, 0)
        self.sizer.Add(sizer_right, 1, wx.EXPAND, 0)

        self.SetBackgroundColour((240, 240, 240))
        
    def makePreToolbar(self):
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        checkAll = wx.BitmapButton(self, ID_checkAllItems_HTML, self.icons.iconsLib['check16'],
                                   size=(26, 26),  style=wx.BORDER_DEFAULT | wx.ALIGN_CENTER_VERTICAL)
        
        document_label = wx.StaticText(self, -1, "Document filter:")
        docList = ['All'] + self.documentsDict.keys()
        self.docSelection_combo = wx.Choice(self, -1, choices=docList, size=(150, -1))
        self.docSelection_combo.SetStringSelection("All")
        
        type_label = wx.StaticText(self, -1, "Item type filter:")
        self.dataSelection_combo = wx.Choice(self, -1, choices=["Show All", "Show Selected", 
                                                                "Show MS (all)", "Show MS (multiple)",
                                                                "Show MS", "Show RT (all)", "Show RT", 
                                                                "Show 1D (all)", "Show 1D IM-MS", 
                                                                "Show 2D IM-MS", "Show 1D plots (MS, DT, RT)", 
                                                                "Show Overlay", "Show Statistical",
                                                                "Show UniDec (all)",
                                                                "Show UniDec (processed)",
                                                                "Show UniDec (multiple)"
                                                                ], 
                                             size=(-1, -1))
        self.dataSelection_combo.SetStringSelection("Show All")
        
        output_label = wx.StaticText(self, -1, "Assign output format:")
        self.pageLayoutSelect_toolbar = wx.Choice(self, -1, choices=self.config.pageDict.keys(), size=(-1, -1))
        self.pageLayoutSelect_toolbar.SetStringSelection("None")
        page_addBtn = wx.BitmapButton(self, ID_addPage_HTML, self.icons.iconsLib['add16'],
                                      size=(26, 26),  style=wx.BORDER_DEFAULT | wx.ALIGN_CENTER_VERTICAL)
        page_applyBtn = wx.BitmapButton(self, ID_assignPageSelected_HTML, self.icons.iconsLib['tick16'],
                                      size=(26, 26),  style=wx.BORDER_DEFAULT | wx.ALIGN_CENTER_VERTICAL)
        
        tools_label = wx.StaticText(self, -1, "Assign toolset:")
        self.plotTypeToolsSelect_toolbar = wx.Choice(self, -1, choices= self.config.interactiveToolsOnOff.keys(),
                                                     size=(-1, -1))
        tools_applyBtn = wx.BitmapButton(self, ID_assignToolsSelected_HTML, self.icons.iconsLib['tick16'],
                                      size=(26, 26),  style=wx.BORDER_DEFAULT | wx.ALIGN_CENTER_VERTICAL)
         
         
        colormap_label = wx.StaticText(self, -1, "Assign colormap:")
        self.colormapSelect_toolbar = wx.Choice(self, -1, choices= self.config.cmaps2,
                                                     size=(-1, -1))
        self.colormapSelect_toolbar.SetStringSelection(self.config.currentCmap)
        colormap_applyBtn = wx.BitmapButton(self, ID_assignColormapSelected_HTML, self.icons.iconsLib['tick16'],
                                      size=(26, 26),  style=wx.BORDER_DEFAULT | wx.ALIGN_CENTER_VERTICAL)

        table_applyBtn = wx.BitmapButton(self, ID_interactivePanel_guiMenuTool, self.icons.iconsLib['setting16'],
                                      size=(26, 26),  style=wx.BORDER_DEFAULT | wx.ALIGN_CENTER_VERTICAL)

        # bind
        self.dataSelection_combo.Bind(wx.EVT_CHOICE, self.OnShowOneDataType)
        self.docSelection_combo.Bind(wx.EVT_CHOICE, self.OnShowOneDataType)
        self.Bind(wx.EVT_BUTTON, self.OnCheckAllItems, id=ID_checkAllItems_HTML) 
        self.Bind(wx.EVT_BUTTON, self.onAddPage, id=ID_addPage_HTML)
        self.Bind(wx.EVT_BUTTON, self.onChangePageForSelectedItems, id=ID_assignPageSelected_HTML)
        self.Bind(wx.EVT_BUTTON, self.onChangeToolsForSelectedItems, id=ID_assignToolsSelected_HTML)
        self.Bind(wx.EVT_BUTTON, self.onChangeColormapForSelectedItems, id=ID_assignColormapSelected_HTML)
        self.Bind(wx.EVT_BUTTON, self.onTableTool, id=ID_interactivePanel_guiMenuTool)
        
        grid = wx.GridBagSizer(1, 1)
        grid.Add(document_label, (0,1), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(type_label, (0,2), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(output_label, (0,3), wx.GBSpan(1,3), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(tools_label, (0,6), wx.GBSpan(1,2), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(colormap_label, (0,8), wx.GBSpan(1,2), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        
        grid.Add(checkAll, (1,0), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.docSelection_combo, (1,1), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.dataSelection_combo, (1,2), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(page_addBtn, (1,3), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.pageLayoutSelect_toolbar, (1,4), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(page_applyBtn, (1,5), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.plotTypeToolsSelect_toolbar, (1,6), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(tools_applyBtn, (1,7), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.colormapSelect_toolbar, (1,8), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(colormap_applyBtn, (1,9), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(table_applyBtn, (1,10), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)     
        
        mainSizer.Add(grid, 0, wx.ALL, 2)
        return mainSizer

    def makeItemsList(self):
        """Make list for items."""
        
        # init table
        self.itemsList = EditableListCtrl(self, size=(750, -1), style=wx.LC_REPORT | wx.LC_VRULES)# |wx.LC_HRULES)
        self.itemsList.SetFont(wx.SMALL_FONT)
        self.itemsList.SetToolTip(wx.ToolTip("Select items save in the .HTML file"))
        
        for item in self.config._interactiveSettings:
            order = item['order']
            name = item['name']
            if item['show']: 
                width = item['width']
            else: 
                width = 0
            self.itemsList.InsertColumn(order, name, width=width, format=wx.LIST_FORMAT_LEFT)

        # Bind events
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onItemSelected)
        self.Bind(wx.EVT_LIST_COL_CLICK, self.OnGetColumnClick)
        self.Bind(wx.EVT_LEFT_DCLICK, self.onItemActivated)
        self.Bind(wx.EVT_LIST_KEY_DOWN, self.onItemClicked)
        self.Bind(wx.EVT_LIST_BEGIN_LABEL_EDIT, self.onStartEditingItem)
        self.Bind(wx.EVT_LIST_END_LABEL_EDIT, self.onFinishEditingItem)
        
    def makeItemEditor(self):
        """Make items editor."""
            
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.editorBook = wx.Notebook(self, wx.ID_ANY, wx.DefaultPosition, size=(-1,-1), style=0)

        self.htmlView = wx.lib.scrolledpanel.ScrolledPanel(self.editorBook, wx.ID_ANY, wx.DefaultPosition, (-1,-1), wx.TAB_TRAVERSAL)
        self.htmlView.SetupScrolling()
        self.makeHTMLView()
        
        self.editorBook.AddPage(self.htmlView, u"HTML", False)
        
        self.propertiesView = wx.lib.scrolledpanel.ScrolledPanel(self.editorBook, wx.ID_ANY, wx.DefaultPosition, (-1,-1), wx.TAB_TRAVERSAL)
        self.propertiesView.SetupScrolling()
        self.editorBook.AddPage(self.propertiesView, u"Properties", False)
        self.makePropertiesView()
        
        mainSizer.Add(self.editorBook, 1, wx.EXPAND |wx.ALL, 3)
        mainSizer.Fit(self.editorBook)
        
        return mainSizer
                
    def makeHTMLView(self):
        
        RICH_TEXT = wx.TE_MULTILINE|wx.TE_WORDWRAP|wx.TE_RICH2

        self.mainBoxHTML = makeStaticBox(self.htmlView, "HTML properties", (-1,-1), wx.BLACK)
        self.mainBoxHTML.SetSize((-1,-1))
        html_box_sizer = wx.StaticBoxSizer(self.mainBoxHTML, wx.HORIZONTAL)
        
        min_size_text = self.displaysize[0] / 3
        # make elements
        editing_label = wx.StaticText(self.htmlView, -1, "Document:")
        self.document_value = wx.StaticText(self.htmlView, -1, "",size=(min_size_text, -1))
        
        type_label = wx.StaticText(self.htmlView, -1, "Type:")
        self.type_value = wx.StaticText(self.htmlView, -1, "",size=(min_size_text, -1))
        
        details_label = wx.StaticText(self.htmlView, -1, "Details:")
        self.details_value = wx.StaticText(self.htmlView, -1, "",size=(min_size_text, -1))
        
        itemName_label = wx.StaticText(self.htmlView, -1, "Title:")
        self.itemName_value = wx.TextCtrl(self.htmlView, -1, "", size=(-1, -1))
        self.itemName_value.SetToolTip(wx.ToolTip("Filename to be used to save the file"))
        self.itemName_value.Bind(wx.EVT_TEXT, self.onAnnotateItems)
                
        itemHeader_label = wx.StaticText(self.htmlView, -1, "Header:")
        self.itemHeader_value = wx.TextCtrl(self.htmlView, -1, "", size=(-1, 100), style=RICH_TEXT)
        self.itemHeader_value.SetToolTip(wx.ToolTip("HTML-rich text to be used for the header of the interactive file"))
        self.itemHeader_value.Bind(wx.EVT_TEXT, self.onAnnotateItems)
      
        itemFootnote_label = wx.StaticText(self.htmlView, -1, "Footnote:")
        self.itemFootnote_value = wx.TextCtrl(self.htmlView, -1, "", size=(-1, 100), style=RICH_TEXT)
        self.itemFootnote_value.SetToolTip(wx.ToolTip("HTML-rich text to be used for the footnote of the interactive file"))
        self.itemFootnote_value.Bind(wx.EVT_TEXT, self.onAnnotateItems)
        
        html_grid = wx.GridBagSizer(1,1)
        n = 0
        html_grid.Add(editing_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        html_grid.Add(self.document_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL)
        n = n+1
        html_grid.Add(type_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        html_grid.Add(self.type_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL)
        n = n+1
        html_grid.Add(details_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        html_grid.Add(self.details_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL)
        n = n+1
        html_grid.Add(itemName_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        html_grid.Add(self.itemName_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL)
        n = n+1
        html_grid.Add(itemHeader_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        html_grid.Add(self.itemHeader_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL)
        n = n+1
        html_grid.Add(itemFootnote_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        html_grid.Add(self.itemFootnote_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL)
        html_box_sizer.Add(html_grid, 0, wx.EXPAND, 0)
        
        self.html_override = makeCheckbox(self.htmlView, u"Override defaults")
        self.html_override.SetValue(self.config.interactive_override_defaults)
        self.html_override.Bind(wx.EVT_CHECKBOX, self.onChangeSettings)
        
        # general subpanel
        general_staticBox = makeStaticBox(self.htmlView, "General settings", size=(-1, -1), color=wx.BLACK)
        general_staticBox.SetSize((-1,-1))
        general_box_sizer = wx.StaticBoxSizer(general_staticBox, wx.HORIZONTAL)

        page_label = makeStaticText(self.htmlView, u"Assign page:")
        self.pageLayoutSelect_htmlView = wx.ComboBox(self.htmlView, -1, choices=[], value="None", style=wx.CB_READONLY, size=(80, -1))
        self.pageLayoutSelect_htmlView.Bind(wx.EVT_COMBOBOX, self.onChangePageForItem)
        
        tools_label = makeStaticText(self.htmlView, u"Assign toolset:")
        self.plotTypeToolsSelect_htmlView = wx.ComboBox(self.htmlView, -1, choices=[], value="", style=wx.CB_READONLY, size=(80, -1))
        self.plotTypeToolsSelect_htmlView.Disable()
        self.plotTypeToolsSelect_htmlView.Bind(wx.EVT_COMBOBOX, self.onChangeToolsForItem)
        
        order_label = makeStaticText(self.htmlView, u"Order:")
        self.order_value = wx.TextCtrl(self.htmlView, -1, "", size=(50, -1))
        self.order_value.Bind(wx.EVT_TEXT, self.onAnnotateItems)
        
        
        general_grid = wx.GridBagSizer(2, 2)
        y = 0
        general_grid.Add(page_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        general_grid.Add(self.pageLayoutSelect_htmlView, (y,1), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT)
        y = y + 1
        general_grid.Add(tools_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        general_grid.Add(self.plotTypeToolsSelect_htmlView, (y,1), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT)
        y = y + 1
        general_grid.Add(order_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        general_grid.Add(self.order_value, (y,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        
        general_box_sizer.Add(general_grid, 0, wx.EXPAND, 10)

        # plot 1D subpanel
        plot1D_staticBox = makeStaticBox(self.htmlView, "Plot (1D) settings", size=(-1, -1), color=wx.BLACK)
        plot1D_staticBox.SetSize((-1,-1))
        plot1D_box_sizer = wx.StaticBoxSizer(plot1D_staticBox, wx.HORIZONTAL)

        plot1D_line_color_label = wx.StaticText(self.htmlView, -1, "Line color:")
        self.colorBtn = wx.Button( self.htmlView, ID_changeColorInteractive,
                                 u"", wx.DefaultPosition, wx.Size( 26, 26 ), 0 )
        self.colorBtn.Bind(wx.EVT_BUTTON, self.onChangeColour, id=ID_changeColorInteractive)
        
        plot1D_line_width_label = wx.StaticText(self.htmlView, -1, "Line width:")
        self.html_plot1D_line_width = wx.SpinCtrlDouble(self.htmlView, -1,
                                                        value=str(self.config.interactive_line_width), 
                                                        min=0.5, max=10, initial=0, inc=0.5,
                                                        size=(90, -1))
        self.html_plot1D_line_width.Bind(wx.EVT_SPINCTRLDOUBLE, self.onAnnotateItems)

        plot1D_line_alpha_label = wx.StaticText(self.htmlView, -1, "Line transparency:")
        self.html_plot1D_line_alpha = wx.SpinCtrlDouble(self.htmlView, -1,
                                                        value=str(self.config.interactive_line_alpha), 
                                                        min=0.0, max=1, initial=0, inc=0.1,
                                                        size=(90, -1))
        self.html_plot1D_line_alpha.Bind(wx.EVT_SPINCTRLDOUBLE, self.onAnnotateItems)
        
        plot1D_line_style_label = wx.StaticText(self.htmlView, -1, "Line style:")
        self.html_plot1D_line_style = wx.ComboBox(self.htmlView, -1, choices=self.config.interactive_line_style_choices, 
                                                  value="", style=wx.CB_READONLY)
        self.html_plot1D_line_style.SetStringSelection(self.config.interactive_line_style)
        self.html_plot1D_line_style.Bind(wx.EVT_COMBOBOX, self.onAnnotateItems)        
        
        hover_label = wx.StaticText(self.htmlView, wx.ID_ANY, u"Hover tool linked \nto X axis:")   
        self.html_plot1D_hoverLinkX = makeCheckbox(self.htmlView, u"")
        self.html_plot1D_hoverLinkX.Bind(wx.EVT_CHECKBOX, self.onAnnotateItems)
        
        plot1D_grid = wx.GridBagSizer(2, 2)
        y = 0
        plot1D_grid.Add(plot1D_line_color_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        plot1D_grid.Add(self.colorBtn, (y,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        y = y + 1
        plot1D_grid.Add(plot1D_line_width_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        plot1D_grid.Add(self.html_plot1D_line_width, (y,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        y = y + 1
        plot1D_grid.Add(plot1D_line_alpha_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        plot1D_grid.Add(self.html_plot1D_line_alpha, (y,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        y = y + 1
        plot1D_grid.Add(plot1D_line_style_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        plot1D_grid.Add(self.html_plot1D_line_style, (y,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        y = y + 1
        plot1D_grid.Add(hover_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        plot1D_grid.Add(self.html_plot1D_hoverLinkX, (y,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        plot1D_box_sizer.Add(plot1D_grid, 0, wx.EXPAND, 10)
        
        
        # plot 2D subpanel
        plot2D_staticBox = makeStaticBox(self.htmlView, "Plot (2D) settings", size=(-1, -1), color=wx.BLACK)
        plot2D_staticBox.SetSize((-1,-1))
        plot2D_box_sizer = wx.StaticBoxSizer(plot2D_staticBox, wx.HORIZONTAL)
        
        itemColormap_label = wx.StaticText(self.htmlView, wx.ID_ANY, u"Colormap:")        
        self.comboCmapSelect = wx.ComboBox( self.htmlView, ID_changeColormapInteractive, 
                                            wx.EmptyString, wx.DefaultPosition, wx.Size( -1, -1 ), 
                                            self.config.cmaps2, COMBO_STYLE, wx.DefaultValidator)
        self.comboCmapSelect.Bind(wx.EVT_COMBOBOX, self.onChangeColour, id=ID_changeColormapInteractive)    
        
        colorbar_label = wx.StaticText(self.htmlView, wx.ID_ANY, u"Colorbar:")  
        self.colorbarCheck = wx.CheckBox(self.htmlView, -1 ,u'', (15, 30))
        self.colorbarCheck.SetValue(self.config.interactive_colorbar)
        self.colorbarCheck.Bind(wx.EVT_CHECKBOX, self.onAnnotateItems)

        plot2D_grid = wx.GridBagSizer(2, 2)
        y = 0
        plot2D_grid.Add(itemColormap_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        plot2D_grid.Add(self.comboCmapSelect, (y,1), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT)
        y = y + 1
        plot2D_grid.Add(colorbar_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        plot2D_grid.Add(self.colorbarCheck, (y,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        plot2D_box_sizer.Add(plot2D_grid, 0, wx.EXPAND, 10)
        
        
       # plot waterfall subpanel
        ms_staticBox = makeStaticBox(self.htmlView, "Mass spectra settings", size=(-1, -1), color=wx.BLACK)
        ms_staticBox.SetSize((-1,-1))
        ms_box_sizer = wx.StaticBoxSizer(ms_staticBox, wx.HORIZONTAL)
        
        show_annotations_label = wx.StaticText(self.htmlView, wx.ID_ANY, u"Show annotations:")  
        self.showAnnotationsCheck = wx.CheckBox(self.htmlView, -1 ,u'', (15, 30))
        self.showAnnotationsCheck.SetValue(self.config.interactive_ms_annotations)
        self.showAnnotationsCheck.Bind(wx.EVT_CHECKBOX, self.onAnnotateItems)
        self.showAnnotationsCheck.SetToolTip(wx.ToolTip("Annotations will be shown if they are present in the dataset"))
        
        linearize_label = wx.StaticText(self.htmlView, wx.ID_ANY, u"Linearize:")  
        self.linearizeCheck = wx.CheckBox(self.htmlView, -1 ,u'', (15, 30))
        self.linearizeCheck.SetValue(self.config.interactive_ms_linearize)
        self.linearizeCheck.Bind(wx.EVT_CHECKBOX, self.onAnnotateItems)
        self.linearizeCheck.Bind(wx.EVT_CHECKBOX, self.onEnableDisableItems)
        
        
        binSize_label = wx.StaticText(self.htmlView, wx.ID_ANY, u"Bin size:")  
        self.binSize_value = wx.TextCtrl(self.htmlView, -1, "", size=(50, -1))
        self.binSize_value.SetValue(str(self.config.interactive_ms_binSize))
        self.binSize_value.Bind(wx.EVT_TEXT, self.onAnnotateItems)
        
        ms_grid = wx.GridBagSizer(2, 2)
        y = 0
        ms_grid.Add(show_annotations_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        ms_grid.Add(self.showAnnotationsCheck, (y,1), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT)
        y = y + 1
        ms_grid.Add(linearize_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        ms_grid.Add(self.linearizeCheck, (y,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        ms_grid.Add(binSize_label, (y,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        ms_grid.Add(self.binSize_value, (y,3), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        ms_box_sizer.Add(ms_grid, 0, wx.EXPAND, 10)
        
       # plot waterfall subpanel
        waterfall_staticBox = makeStaticBox(self.htmlView, "Plot (Waterfall) settings", size=(-1, -1), color=wx.BLACK)
        waterfall_staticBox.SetSize((-1,-1))
        waterfall_box_sizer = wx.StaticBoxSizer(waterfall_staticBox, wx.HORIZONTAL)
        
        waterfall_offset_label = makeStaticText(self.htmlView, u"Y-axis increment:")
        self.waterfall_increment_value = wx.SpinCtrlDouble(self.htmlView, wx.ID_ANY, 
                                                       value=str(self.config.interactive_waterfall_increment),min=0, max=1,
                                                       initial=self.config.interactive_waterfall_increment, inc=0.1, size=(50,-1))     
        self.waterfall_increment_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onAnnotateItems)
        
        waterfall_grid = wx.GridBagSizer(2, 2)
        y = 0
        waterfall_grid.Add(waterfall_offset_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        waterfall_grid.Add(self.waterfall_increment_value, (y,1), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT)
        waterfall_box_sizer.Add(waterfall_grid, 0, wx.EXPAND, 10)
        
        
        # plot overlay grid subpanel
        grids_staticBox = makeStaticBox(self.htmlView, "Overlay grid settings", size=(-1, -1), color=wx.BLACK)
        grids_staticBox.SetSize((-1,-1))
        grids_box_sizer = wx.StaticBoxSizer(grids_staticBox, wx.HORIZONTAL)
        
        grid_label_label = wx.StaticText(self.htmlView, wx.ID_ANY, u"Enable labels:")  
        self.grid_label_check = wx.CheckBox(self.htmlView, -1 ,u'', (15, 30))
        self.grid_label_check.Bind(wx.EVT_CHECKBOX, self.onAnnotateItems)
        
        grid_label_size_label = makeStaticText(self.htmlView, u"Label font size")
        self.grid_label_size_value = wx.SpinCtrlDouble(self.htmlView, wx.ID_ANY, 
                                                       value=str(self.config.interactive_grid_label_size),min=8, max=32,
                                                       initial=self.config.interactive_grid_label_size, inc=1, size=(50,-1))     
        self.grid_label_size_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onAnnotateItems)    
        
        self.grid_label_weight = makeCheckbox(self.htmlView, u"Bold")
        self.grid_label_weight.SetValue(self.config.interactive_grid_label_weight)
        self.grid_label_weight.Bind(wx.EVT_CHECKBOX, self.onAnnotateItems)    
        
        interactive_annotation_color_label= makeStaticText(self.htmlView, u"Font")
        self.interactive_grid_colorBtn = wx.Button( self.htmlView, ID_changeColorGridLabelInteractive,
                                           u"", wx.DefaultPosition, wx.Size( 26, 26 ), 0 )
        self.interactive_grid_colorBtn.SetBackgroundColour(convertRGB1to255(self.config.interactive_annotation_color))
        self.interactive_grid_colorBtn.Bind(wx.EVT_BUTTON, self.onChangeColour, id=ID_changeColorGridLabelInteractive)
        
        grid_label_xpos_label = makeStaticText(self.htmlView, u"Offset X:")
        self.grid_xpos_value = wx.SpinCtrlDouble(self.htmlView, wx.ID_ANY, 
                                                       value=str(self.config.interactive_grid_xpos),min=0, max=10000,
                                                       initial=self.config.interactive_grid_xpos, inc=50, size=(50,-1))     
        self.grid_xpos_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onAnnotateItems)    

        grid_label_ypos_label = makeStaticText(self.htmlView, u"Offset Y:")
        self.grid_ypos_value = wx.SpinCtrlDouble(self.htmlView, wx.ID_ANY, 
                                                       value=str(self.config.interactive_grid_ypos),min=0, max=10000,
                                                       initial=self.config.interactive_grid_ypos, inc=50, size=(50,-1))     
        self.grid_ypos_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onAnnotateItems)    
        
        grids_grid = wx.GridBagSizer(2, 2)
        y = 0
        grids_grid.Add(grid_label_label, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        grids_grid.Add(self.grid_label_check, (y,1), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT)
        y = y + 1
        grids_grid.Add(grid_label_size_label, (y,0), wx.GBSpan(1,2),flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        grids_grid.Add(interactive_annotation_color_label, (y,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        y = y + 1
        grids_grid.Add(self.grid_label_size_value, (y,0), wx.GBSpan(1,1), flag=wx.EXPAND)
        grids_grid.Add(self.grid_label_weight, wx.GBPosition(y,1), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
        grids_grid.Add(self.interactive_grid_colorBtn, (y,2), wx.GBSpan(1,1), flag=wx.EXPAND)
        y = y + 1
        grids_grid.Add(grid_label_xpos_label, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        grids_grid.Add(self.grid_xpos_value, (y,1), wx.GBSpan(1,2), flag=wx.EXPAND)
        y = y + 1
        grids_grid.Add(grid_label_ypos_label, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        grids_grid.Add(self.grid_ypos_value, (y,1), wx.GBSpan(1,2), flag=wx.EXPAND)
        grids_box_sizer.Add(grids_grid, 0, wx.EXPAND, 10)
        
        # overlay subpanel
        overlay_staticBox = makeStaticBox(self.htmlView, "Overlay plot settings", size=(-1, -1), color=wx.BLACK)
        overlay_staticBox.SetSize((-1,-1))
        overlay_box_sizer = wx.StaticBoxSizer(overlay_staticBox, wx.HORIZONTAL)
        
        colormap_1_label = wx.StaticText(self.htmlView, wx.ID_ANY, u"Colormap (1):")        
        self.html_overlay_colormap_1 = wx.ComboBox( self.htmlView, -1, 
                                                    wx.EmptyString, wx.DefaultPosition, wx.Size( -1,-1 ), 
                                                    self.config.cmaps2, COMBO_STYLE, wx.DefaultValidator)
        self.html_overlay_colormap_1.Bind(wx.EVT_COMBOBOX, self.onAnnotateItems)
        
        colormap_2_label = wx.StaticText(self.htmlView, wx.ID_ANY, u"Colormap (2):")        
        self.html_overlay_colormap_2 = wx.ComboBox( self.htmlView, -1, 
                                                    wx.EmptyString, wx.DefaultPosition, wx.Size( -1,-1 ), 
                                                    self.config.cmaps2, COMBO_STYLE, wx.DefaultValidator)
        self.html_overlay_colormap_2.Bind(wx.EVT_COMBOBOX, self.onAnnotateItems)

        layout_label = wx.StaticText(self.htmlView, wx.ID_ANY, u"Layout:")        
        self.html_overlay_layout = wx.ComboBox(self.htmlView, -1, 
                                               wx.EmptyString, wx.DefaultPosition, wx.Size( -1,-1 ), 
                                               ['Rows', 'Columns'], COMBO_STYLE, wx.DefaultValidator)
        self.html_overlay_layout.Bind(wx.EVT_COMBOBOX, self.onAnnotateItems)
        
        linkXY_label = wx.StaticText(self.htmlView, wx.ID_ANY, u"Link XY axes:")   
        self.html_overlay_linkXY = makeCheckbox(self.htmlView, u"")
        self.html_overlay_linkXY.Bind(wx.EVT_CHECKBOX, self.onAnnotateItems)
        
        legend_label = wx.StaticText(self.htmlView, wx.ID_ANY, u"Legend:")   
        self.html_overlay_legend = makeCheckbox(self.htmlView, u"")
        self.html_overlay_legend.Bind(wx.EVT_CHECKBOX, self.onAnnotateItems)
        

        overlay_grid = wx.GridBagSizer(2, 2)
        y = 0
        overlay_grid.Add(colormap_1_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        overlay_grid.Add(self.html_overlay_colormap_1, (y,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        y = y + 1
        overlay_grid.Add(colormap_2_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        overlay_grid.Add(self.html_overlay_colormap_2, (y,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        y = y + 1
        overlay_grid.Add(layout_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        overlay_grid.Add(self.html_overlay_layout, (y,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        y = y + 1
        overlay_grid.Add(linkXY_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        overlay_grid.Add(self.html_overlay_linkXY, (y,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        y = y + 1
        overlay_grid.Add(legend_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        overlay_grid.Add(self.html_overlay_legend, (y,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        overlay_box_sizer.Add(overlay_grid, 0, wx.EXPAND, 10)
        
        
        # Disable all elements when nothing is selected
        itemList = [self.itemName_value, self.itemHeader_value, self.itemFootnote_value,
                    self.order_value, self.colorBtn, self.comboCmapSelect, self.pageLayoutSelect_htmlView,
                    self.plotTypeToolsSelect_htmlView, self.html_overlay_colormap_1, self.html_overlay_colormap_2,
                    self.html_overlay_layout, self.html_overlay_linkXY, self.colorbarCheck,
                    self.html_plot1D_line_alpha, self.html_plot1D_line_width, self.html_plot1D_hoverLinkX,
                    self.html_overlay_legend, self.grid_label_check, self.grid_label_size_value,
                    self.grid_label_weight, self.interactive_grid_colorBtn, self.html_plot1D_line_style,
                    self.grid_ypos_value, self.grid_xpos_value, self.waterfall_increment_value,
                    self.binSize_value, self.showAnnotationsCheck, self.linearizeCheck]
    
        for item in itemList:
            item.Disable()

        sizer_col_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_col_1.Add(general_box_sizer, 0, wx.EXPAND, 0)
        sizer_col_1.Add(plot2D_box_sizer, 0, wx.EXPAND, 0)
        sizer_col_1.Add(overlay_box_sizer, 0, wx.EXPAND, 0)
        sizer_col_1.Add(waterfall_box_sizer, 0, wx.EXPAND, 0)
        
        
        sizer_col_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_col_2.Add(plot1D_box_sizer, 0, wx.EXPAND, 0)
        sizer_col_2.Add(grids_box_sizer, 0, wx.EXPAND, 0)
        sizer_col_2.Add(ms_box_sizer, 0, wx.EXPAND, 0)
        
        sizer_row_2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_row_2.Add(sizer_col_1, 0, wx.EXPAND, 0)
        sizer_row_2.Add(sizer_col_2, 0, wx.EXPAND, 0)
        
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(html_box_sizer, 0, wx.EXPAND, 0)
        mainSizer.Add(self.html_override, 0, wx.EXPAND, 0)
        mainSizer.Add(sizer_row_2, 0, wx.EXPAND, 0)
        mainSizer.Fit(self.htmlView)
        self.htmlView.SetSizer(mainSizer)
        
        self.htmlView.SetBackgroundColour((240, 240, 240))
        
        return mainSizer

    def makePropertiesView(self):
        viewSizer = wx.BoxSizer(wx.HORIZONTAL)

        fontSizer = self.makeFontSubPanel()
        imageSizer = self.makeImageSubPanel()
        pageLayoutSizer = self.makePageLayoutSubPanel()
        rmsdSizer = self.makeRMSDSubPanel()
        toolsSizer = self.makeInteractiveToolsSubPanel()
        plot1Dsizer = self.make1DplotSubPanel()
        overlaySizer = self.makeOverLaySubPanel()
        colorbarSizer = self.makeColorbarSubPanel()
        plotSettingsSizer = self.makePlotSettingsSubPanel()
        legendSettingsSizer = self.makeLegendSubPanel()



        # Add to grid sizer
        sizer_left = wx.BoxSizer(wx.VERTICAL)
        sizer_left.Add(toolsSizer, 0, wx.EXPAND, 0)
        sizer_left.Add(imageSizer, 0, wx.EXPAND, 0)
        sizer_left.Add(plot1Dsizer, 0, wx.EXPAND, 0)
        sizer_left.Add(legendSettingsSizer, 0, wx.EXPAND, 0)
        
        sizer_right = wx.BoxSizer(wx.VERTICAL)
        sizer_right.Add(fontSizer, 0, wx.EXPAND, 0)
        sizer_right.Add(plotSettingsSizer, 0, wx.EXPAND, 0)
        sizer_right.Add(pageLayoutSizer, 0, wx.EXPAND, 0)
        sizer_right.Add(colorbarSizer, 0, wx.EXPAND, 0)
        sizer_right.Add(rmsdSizer, 0, wx.EXPAND, 0)
        sizer_right.Add(overlaySizer, 0, wx.EXPAND, 0)
        
        
#         # pack elements
#         sizer = wx.BoxSizer(wx.HORIZONTAL)
        viewSizer.Add(sizer_left, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)
        viewSizer.Add(sizer_right, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)

        viewSizer.Fit(self.propertiesView)
        self.propertiesView.SetSizerAndFit(viewSizer)
        
        self.onSetupTools(evt=None)
        self.onSelectPageProperties(evt=None)
        self.onChangePage(evt=None)
        
        self.propertiesView.SetBackgroundColour((240, 240, 240))
        
        return viewSizer
   
    def makeFontSubPanel(self):
        mainBox = makeStaticBox(self.propertiesView, "Font properties", (210,-1), wx.BLUE)
        mainBox.SetSize((230,-1))
        mainSizer = wx.StaticBoxSizer(mainBox, wx.HORIZONTAL)
        titleFontSize = makeStaticText(self.propertiesView, u"Title font size")
        
        self.titleSlider = wx.SpinCtrlDouble(self.propertiesView, wx.ID_ANY, 
                                             value=str(self.config.interactive_title_fontSize),min=8, max=32,
                                             initial=self.config.interactive_title_fontSize, inc=1, size=(50,-1))
        self.titleBoldCheck = makeCheckbox(self.propertiesView, u"Bold")
        self.titleBoldCheck.SetValue(self.config.interactive_title_weight)
        
        labelFontSize = makeStaticText(self.propertiesView, u"Label font size")
        self.labelSlider = wx.SpinCtrlDouble(self.propertiesView, wx.ID_ANY, 
                                             value=str(self.config.interactive_label_fontSize),min=8, max=32,
                                             initial=self.config.interactive_label_fontSize, inc=1, size=(50,-1))
        
        self.labelBoldCheck = makeCheckbox(self.propertiesView, u"Bold")
        self.labelBoldCheck.SetValue(self.config.interactive_label_weight)
        
        tickFontSize = makeStaticText(self.propertiesView, u"Tick font size")
        self.tickSlider = wx.SpinCtrlDouble(self.propertiesView, wx.ID_ANY, 
                                             value=str(self.config.interactive_tick_fontSize),min=8, max=32,
                                             initial=self.config.interactive_tick_fontSize, inc=1, size=(50,-1))   


        precision_label = makeStaticText(self.propertiesView, u"Tick precision")
        self.tickPrecision = wx.SpinCtrlDouble(self.propertiesView, wx.ID_ANY, 
                                                   value=str(self.config.interactive_tick_precision),min=0, max=5,
                                                   initial=self.config.interactive_tick_precision, inc=1, size=(50,-1))

        
        self.tickUseScientific = wx.CheckBox(self.propertiesView, -1 ,u'Scientific\nnotation', (15, 30))
        self.tickUseScientific.SetValue(self.config.interactive_tick_useScientific)
        self.tickUseScientific.Bind(wx.EVT_CHECKBOX, self.onEnableDisableItems)
             
        # Add to grid sizer
        grid = wx.GridBagSizer(2,2)
        grid.Add(titleFontSize, wx.GBPosition(0,0), wx.GBSpan(1,2), TEXT_STYLE_CV_R_L, 2)
        grid.Add(self.titleSlider, wx.GBPosition(1,0), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
        grid.Add(self.titleBoldCheck, wx.GBPosition(1,1), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
        
        grid.Add(labelFontSize, wx.GBPosition(0,2), wx.GBSpan(1,2), TEXT_STYLE_CV_R_L, 2)
        grid.Add(self.labelSlider, wx.GBPosition(1,2), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
        grid.Add(self.labelBoldCheck, wx.GBPosition(1,3), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
        
        grid.Add(tickFontSize, wx.GBPosition(2,0), wx.GBSpan(1,2), TEXT_STYLE_CV_R_L, 2)
        grid.Add(self.tickSlider, wx.GBPosition(3,0), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
        grid.Add(precision_label, wx.GBPosition(2,2), wx.GBSpan(1,2), TEXT_STYLE_CV_R_L, 2)
        grid.Add(self.tickPrecision, wx.GBPosition(3,2), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
        grid.Add(self.tickUseScientific, wx.GBPosition(3,3), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
        
        mainSizer.Add(grid, 0, wx.EXPAND|wx.ALL, 2)
        return mainSizer
   
    def makeImageSubPanel(self):
        imageBox = makeStaticBox(self.propertiesView, "Image properties", (230,-1), wx.BLUE)
        figSizer = wx.StaticBoxSizer(imageBox, wx.HORIZONTAL)
         
        figHeight1D_label = makeStaticText(self.propertiesView, u"Height (1D)")
        self.figHeight1D_value = wx.TextCtrl(self.propertiesView, -1, "", size=(50, -1))
        self.figHeight1D_value.SetValue(str(self.config.figHeight1D))
        self.figHeight1D_value.SetToolTip(wx.ToolTip("Set figure height (pixels)"))
         
        figWidth1D_label = makeStaticText(self.propertiesView, u"Width (1D)")
        self.figWidth1D_value = wx.TextCtrl(self.propertiesView, -1, "", size=(50, -1))
        self.figWidth1D_value.SetValue(str(self.config.figWidth1D))
        self.figWidth1D_value.SetToolTip(wx.ToolTip("Set figure width (pixels)"))  
         
        figHeight_label = makeStaticText(self.propertiesView, u"Height (2D)")
        self.figHeight_value = wx.TextCtrl(self.propertiesView, -1, "", size=(50, -1))
        self.figHeight_value.SetValue(str(self.config.figHeight))
        self.figHeight_value.SetToolTip(wx.ToolTip("Set figure height (pixels)"))
         
        figWidth_label = makeStaticText(self.propertiesView, u"Width (2D)")
        self.figWidth_value = wx.TextCtrl(self.propertiesView, -1, "", size=(50, -1))
        self.figWidth_value.SetValue(str(self.config.figWidth))
        self.figWidth_value.SetToolTip(wx.ToolTip("Set figure width (pixels)"))  
     
        # bind
        self.figHeight_value.Bind(wx.EVT_TEXT, self.onChangeSettings)
        self.figWidth_value.Bind(wx.EVT_TEXT, self.onChangeSettings)
        self.figHeight1D_value.Bind(wx.EVT_TEXT, self.onChangeSettings)
        self.figWidth1D_value.Bind(wx.EVT_TEXT, self.onChangeSettings)

        gridFigure = wx.GridBagSizer(2,2)
        n = 0
        gridFigure.Add(figHeight1D_label, (n,0))
        gridFigure.Add(self.figHeight1D_value, (n,1))
        gridFigure.Add(figWidth1D_label, (n,2))
        gridFigure.Add(self.figWidth1D_value, (n,3))
        n = n+1
        gridFigure.Add(figHeight_label, (n,0))
        gridFigure.Add(self.figHeight_value, (n,1))
        gridFigure.Add(figWidth_label, (n,2))
        gridFigure.Add(self.figWidth_value, (n,3))
        figSizer.Add(gridFigure, 0, wx.EXPAND|wx.ALL, 2)
        return figSizer
    
    def makePlotSettingsSubPanel(self):
        imageBox = makeStaticBox(self.propertiesView, "Frame properties", (210,-1), wx.BLUE)
        figSizer = wx.StaticBoxSizer(imageBox, wx.HORIZONTAL)

        borderRight_label = makeStaticText(self.propertiesView, u"Border \nright")
        self.interactive_border_min_right = wx.SpinCtrlDouble(self.propertiesView, wx.ID_ANY, 
                                                   value=str(self.config.interactive_border_min_right),min=0, max=100,
                                                   initial=float(self.config.interactive_border_min_right), 
                                                   inc=5, size=(50,-1))
        self.interactive_border_min_right.SetToolTip(wx.ToolTip("Set minimum border size (pixels)"))
        
        borderLeft_label = makeStaticText(self.propertiesView, u"Border \nleft")
        self.interactive_border_min_left = wx.SpinCtrlDouble(self.propertiesView, wx.ID_ANY, 
                                                   value=str(self.config.interactive_border_min_left),min=0, max=100,
                                                   initial=float(self.config.interactive_border_min_left), inc=5, size=(50,-1))
        self.interactive_border_min_left.SetToolTip(wx.ToolTip("Set minimum border size (pixels)"))

        borderTop_label = makeStaticText(self.propertiesView, u"Border \ntop")
        self.interactive_border_min_top = wx.SpinCtrlDouble(self.propertiesView, wx.ID_ANY, 
                                                   value=str(self.config.interactive_border_min_top),min=0, max=100,
                                                   initial=float(self.config.interactive_border_min_top), inc=5, size=(50,-1))
        self.interactive_border_min_top.SetToolTip(wx.ToolTip("Set minimum border size (pixels)"))        
        
        borderBottom_label = makeStaticText(self.propertiesView, u"Border \nbottom")
        self.interactive_border_min_bottom = wx.SpinCtrlDouble(self.propertiesView, wx.ID_ANY, 
                                                   value=str(self.config.interactive_border_min_bottom),min=0, max=100,
                                                   initial=float(self.config.interactive_border_min_bottom), inc=5, size=(50,-1))
        self.interactive_border_min_bottom.SetToolTip(wx.ToolTip("Set minimum border size (pixels)"))
        
        outlineWidth_label = makeStaticText(self.propertiesView, u"Outline \nwidth")
        self.interactive_outline_width = wx.SpinCtrlDouble(self.propertiesView, wx.ID_ANY, 
                                                   value=str(self.config.interactive_outline_width),min=0, max=5,
                                                   initial=self.config.interactive_outline_width, inc=0.5, size=(50,-1))
        self.interactive_outline_width.SetToolTip(wx.ToolTip("Plot outline line thickness"))
        
        outlineTransparency_label = makeStaticText(self.propertiesView, u"Outline \nalpha")
        self.interactive_outline_alpha = wx.SpinCtrlDouble(self.propertiesView, wx.ID_ANY, 
                                                   value=str(self.config.interactive_outline_alpha),min=0, max=1,
                                                   initial=self.config.interactive_outline_alpha, inc=0.05, size=(50,-1))
        self.interactive_outline_alpha.SetToolTip(wx.ToolTip("Plot outline line transparency value"))
        
        # bind
        self.interactive_border_min_right.Bind(wx.EVT_SPINCTRLDOUBLE, self.onChangeSettings)
        self.interactive_border_min_left.Bind(wx.EVT_SPINCTRLDOUBLE, self.onChangeSettings)
        self.interactive_border_min_top.Bind(wx.EVT_SPINCTRLDOUBLE, self.onChangeSettings)
        self.interactive_border_min_bottom.Bind(wx.EVT_SPINCTRLDOUBLE, self.onChangeSettings)
        self.interactive_outline_width.Bind(wx.EVT_SPINCTRLDOUBLE, self.onChangeSettings)
        self.interactive_outline_alpha.Bind(wx.EVT_SPINCTRLDOUBLE, self.onChangeSettings)


        gridFigure = wx.GridBagSizer(5,2)
        n = 0
        gridFigure.Add(borderRight_label, (n,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        gridFigure.Add(borderLeft_label, (n,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        gridFigure.Add(borderTop_label, (n,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        gridFigure.Add(borderBottom_label, (n,3), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        n = n+1
        gridFigure.Add(self.interactive_border_min_right, (n,0))
        gridFigure.Add(self.interactive_border_min_left, (n,1))
        gridFigure.Add(self.interactive_border_min_top, (n,2))
        gridFigure.Add(self.interactive_border_min_bottom, (n,3))
        n = n+1
        gridFigure.Add(outlineWidth_label, (n,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        gridFigure.Add(outlineTransparency_label, (n,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        n = n+1
        gridFigure.Add(self.interactive_outline_width, (n,0))
        gridFigure.Add(self.interactive_outline_alpha, (n,1))
        
        figSizer.Add(gridFigure, 0, wx.EXPAND|wx.ALL, 2)
        return figSizer
    
    def makePageLayoutSubPanel(self):
        layoutBox = makeStaticBox(self.propertiesView, "Page properties", (200,-1), wx.BLUE)
        layoutSizer = wx.StaticBoxSizer(layoutBox, wx.HORIZONTAL)
        layoutBox.SetToolTip(wx.ToolTip("Each HTML document is tabbed (when more than one item is selected). Each tab can be subsequently one of the following: individual, row, column or grid."))
        
        
        selPage_label = makeStaticText(self.propertiesView, u"Select page:")
        self.pageLayoutSelect_propView = wx.ComboBox(self.propertiesView, -1, choices=[],
                                        value="None", style=wx.CB_READONLY)
        
        layoutDoc_label = makeStaticText(self.propertiesView, u"Page layout:")
        self.layoutDoc_combo = wx.ComboBox(self.propertiesView, -1, choices=self.config.interactive_pageLayout_choices,
                                        value=self.config.layoutModeDoc, style=wx.CB_READONLY)
        self.layoutDoc_combo.SetToolTip(wx.ToolTip("Select type of layout for the page. Default: Individual"))
        
        self.addPage = wx.Button(self.propertiesView, ID_ANY,size=(26,26))
        self.addPage.SetBitmap(self.icons.iconsLib['add16'])
  
        columns_label = makeStaticText(self.propertiesView, u"Columns")
        self.columns_value = wx.TextCtrl(self.propertiesView, -1, "", size=(50, -1))
        self.columns_value.SetToolTip(wx.ToolTip("Grid only. Number of columns in the grid"))
        
        pageTitle_label = makeStaticText(self.propertiesView, u"Page title:")
        self.pageTitle_value = wx.TextCtrl(self.propertiesView, -1, "", size=(50, -1))
        self.pageTitle_value.SetToolTip(wx.ToolTip("Title of the page."))
        

        # bind
        self.pageLayoutSelect_propView.Bind(wx.EVT_COMBOBOX, self.onChangePage)
        
        self.layoutDoc_combo.Bind(wx.EVT_COMBOBOX, self.onChangeSettings)
        self.layoutDoc_combo.Bind(wx.EVT_COMBOBOX, self.onSelectPageProperties)
        
        self.columns_value.Bind(wx.EVT_TEXT, self.onSelectPageProperties)
        self.columns_value.Bind(wx.EVT_TEXT, self.onChangeSettings)

        self.addPage.Bind(wx.EVT_BUTTON, self.onAddPage)

        gridLayout = wx.GridBagSizer(2,5)
        gridLayout.Add(selPage_label, (0,0), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        gridLayout.Add(self.pageLayoutSelect_propView, (0,1), wx.GBSpan(1,2), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        gridLayout.Add(self.addPage, (0,3))
 
        gridLayout.Add(layoutDoc_label, (1,0), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        gridLayout.Add(self.layoutDoc_combo, (1,1), wx.GBSpan(1,2), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        gridLayout.Add(columns_label, (1,3), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        gridLayout.Add(self.columns_value, (1,4), flag=wx.ALIGN_CENTER_VERTICAL)
 
        gridLayout.Add(pageTitle_label, (2,0), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        gridLayout.Add(self.pageTitle_value, (2,1), wx.GBSpan(1,2), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        
        layoutSizer.Add(gridLayout, 0, wx.EXPAND|wx.ALL, 2)
        return layoutSizer
    
    def makeRMSDSubPanel(self):
        rmsdBox = makeStaticBox(self.propertiesView, "RMSD label properties", (200,-1), wx.BLUE)
        rmsdSizer = wx.StaticBoxSizer(rmsdBox, wx.HORIZONTAL)
        rmsdBox.SetToolTip(wx.ToolTip(""))

        notationFontSize = makeStaticText(self.propertiesView, u"Label font size")
        self.notationSlider = wx.SpinCtrlDouble(self.propertiesView, wx.ID_ANY, 
                                             value=str(self.config.interactive_annotation_fontSize),min=8, max=32,
                                             initial=self.config.interactive_annotation_fontSize, inc=1, size=(50,-1))     
        self.notationBoldCheck = makeCheckbox(self.propertiesView, u"Bold")
        self.notationBoldCheck.SetValue(self.config.interactive_annotation_weight)

        interactive_annotation_color_label= makeStaticText(self.propertiesView, u"Font")
        self.interactive_annotation_colorBtn = wx.Button( self.propertiesView, ID_changeColorNotationInteractive,
                                           u"", wx.DefaultPosition, wx.Size( 26, 26 ), 0 )
        self.interactive_annotation_colorBtn.SetBackgroundColour(convertRGB1to255(self.config.interactive_annotation_color))
        
        interactive_annotation_background_color_label= makeStaticText(self.propertiesView, u"Background")
        self.interactive_annotation_colorBackgroundBtn = wx.Button( self.propertiesView, ID_changeColorBackgroundNotationInteractive,
                                                     u"", wx.DefaultPosition, wx.Size( 26, 26 ), 0 )
        self.interactive_annotation_colorBackgroundBtn.SetBackgroundColour(convertRGB1to255(self.config.interactive_annotation_background_color))

        interactive_transparency_label= makeStaticText(self.propertiesView, u"Transparency")
        self.rmsd_label_transparency = wx.SpinCtrlDouble(self.propertiesView, wx.ID_ANY, 
                                                         value=str(self.config.interactive_annotation_alpha),min=0, max=1,
                                                         initial=self.config.interactive_annotation_alpha, inc=0.1, size=(50,-1))     
        
        
        
        self.titleSlider.Bind(wx.EVT_SPINCTRLDOUBLE, self.onChangeSettings)
        self.titleBoldCheck.Bind(wx.EVT_CHECKBOX, self.onChangeSettings)
        self.labelSlider.Bind(wx.EVT_SPINCTRLDOUBLE, self.onChangeSettings)
        self.labelBoldCheck.Bind(wx.EVT_CHECKBOX, self.onChangeSettings)
        self.tickSlider.Bind(wx.EVT_SPINCTRLDOUBLE, self.onChangeSettings)
        self.notationSlider.Bind(wx.EVT_SPINCTRLDOUBLE, self.onChangeSettings)
        self.rmsd_label_transparency.Bind(wx.EVT_SPINCTRLDOUBLE, self.onChangeSettings)
        self.notationBoldCheck.Bind(wx.EVT_CHECKBOX, self.onChangeSettings)
        self.interactive_annotation_colorBtn.Bind(wx.EVT_BUTTON, self.onChangeColour, id=ID_changeColorNotationInteractive)
        self.interactive_annotation_colorBackgroundBtn.Bind(wx.EVT_BUTTON, self.onChangeColour, id=ID_changeColorBackgroundNotationInteractive)

        grid = wx.GridBagSizer(2,2)
        n=0
        grid.Add(notationFontSize, wx.GBPosition(n,0), wx.GBSpan(1,2), TEXT_STYLE_CV_R_L, 2)
        grid.Add(interactive_annotation_color_label, wx.GBPosition(n,2), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
        grid.Add(interactive_annotation_background_color_label, wx.GBPosition(n,3), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
        grid.Add(interactive_transparency_label, wx.GBPosition(n,4), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
        n=n+1
        grid.Add(self.notationSlider, wx.GBPosition(n,0), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
        grid.Add(self.notationBoldCheck, wx.GBPosition(n,1), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
        grid.Add(self.interactive_annotation_colorBtn, wx.GBPosition(n,2), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
        grid.Add(self.interactive_annotation_colorBackgroundBtn, wx.GBPosition(n,3), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
        grid.Add(self.rmsd_label_transparency, wx.GBPosition(n,4), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
 
        rmsdSizer.Add(grid, 0, wx.EXPAND|wx.ALL, 2)
        return rmsdSizer
    
    def makeInteractiveToolsSubPanel(self):
        mainBox = makeStaticBox(self.propertiesView, "Interactive tools", (240,-1), wx.BLUE)
        toolsSizer = wx.StaticBoxSizer(mainBox, wx.HORIZONTAL)
        
        font = wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        
        availableTools_label = wx.StaticText(self.propertiesView, -1, "Available tools", style=TEXT_STYLE_CV_R_L)
        availableTools_label.SetFont(font)
        availableTools_label.SetForegroundColour((34,139,34))
        
        plotType_label = wx.StaticText(self.propertiesView, -1, "Plot type", style=TEXT_STYLE_CV_R_L)
        self.plotTypeToolsSelect_propView = wx.ComboBox(self.propertiesView, -1, choices=['1D', '2D','Overlay'], 
                                          value='1D', style=wx.CB_READONLY)
        msg = 'Name of the toolset. Select tools that you would like to add to toolset.'
        tip = self.makeTooltip(text=msg, delay=500)
        self.plotTypeToolsSelect_propView.SetToolTip(tip)
        self.addPlotType = wx.Button(self.propertiesView, ID_ANY,size=(26,26))
        self.addPlotType.SetBitmap(self.icons.iconsLib['add16'])
        
        self.hover_check = wx.CheckBox(self.propertiesView, -1 ,'Hover', (15, 30))
        self.save_check = wx.CheckBox(self.propertiesView, -1 ,'Save', (15, 30))
        self.pan_check = wx.CheckBox(self.propertiesView, -1 ,'Pan', (15, 30))
        self.boxZoom_check = wx.CheckBox(self.propertiesView, -1 ,'Box Zoom', (15, 30))
        self.crosshair_check = wx.CheckBox(self.propertiesView, -1 ,'Crosshair', (15, 30))
        self.reset_check = wx.CheckBox(self.propertiesView, -1 ,'Reset', (15, 30))
        self.wheel_check = wx.CheckBox(self.propertiesView, -1 ,'Wheel', (15, 30))
        
#         wheelZoom_label = wx.StaticText(self.propertiesView, -1, "Wheel Zoom", style=TEXT_STYLE_CV_R_L)
        self.wheelZoom_combo = wx.ComboBox(self.propertiesView, -1, choices=self.config.interactive_wheelZoom_choices, 
                                          value='Wheel Zoom XY', style=wx.CB_READONLY)


        location_label = wx.StaticText(self.propertiesView, -1, "Toolbar position", style=TEXT_STYLE_CV_R_L)
        self.location_combo = wx.ComboBox(self.propertiesView, -1, choices=self.config.interactive_toolbarPosition_choices, 
                                          value=self.config.toolsLocation, style=wx.CB_READONLY)
        self.location_combo.Disable()

        
        
        availableActiveTools_label = wx.StaticText(self.propertiesView, -1, "Active tools", 
                                                   style=TEXT_STYLE_CV_R_L)
        availableActiveTools_label.SetFont(font)
        availableActiveTools_label.SetForegroundColour((34,139,34))
        
        drag_label = makeStaticText(self.propertiesView, u"Active Drag")
        self.activeDrag_combo = wx.ComboBox(self.propertiesView, -1, 
                                            choices=self.config.interactive_activeDragTools_choices, 
                                            value=self.config.activeDrag, 
                                            style=wx.CB_READONLY)
        wheel_labe = makeStaticText(self.propertiesView, u"Active Wheel")
        self.activeWheel_combo = wx.ComboBox(self.propertiesView, -1, 
                                             choices=self.config.interactive_activeWheelTools_choices,
                                             value=self.config.activeWheel, 
                                             style=wx.CB_READONLY)
        inspect_label = makeStaticText(self.propertiesView, u"Active Hover")
        self.activeInspect_combo= wx.ComboBox(self.propertiesView, -1, 
                                              choices=self.config.interactive_activeHoverTools_choices,
                                              value=self.config.activeInspect,
                                              style=wx.CB_READONLY)
      
        # bind
        self.hover_check.Bind(wx.EVT_CHECKBOX, self.onSelectTools)
        self.save_check.Bind(wx.EVT_CHECKBOX, self.onSelectTools)
        self.pan_check.Bind(wx.EVT_CHECKBOX, self.onSelectTools)
        self.boxZoom_check.Bind(wx.EVT_CHECKBOX, self.onSelectTools)
        self.crosshair_check.Bind(wx.EVT_CHECKBOX, self.onSelectTools)
        self.reset_check.Bind(wx.EVT_CHECKBOX, self.onSelectTools)
        self.wheel_check.Bind(wx.EVT_CHECKBOX, self.onSelectTools)
        self.location_combo.Bind(wx.EVT_COMBOBOX, self.onChangeSettings)
        self.wheelZoom_combo.Bind(wx.EVT_COMBOBOX, self.onSelectTools)
        self.plotTypeToolsSelect_propView.Bind(wx.EVT_COMBOBOX, self.onSetupTools)
        
        self.activeDrag_combo.Bind(wx.EVT_COMBOBOX, self.onSelectTools)
        self.activeWheel_combo.Bind(wx.EVT_COMBOBOX, self.onSelectTools)
        self.activeInspect_combo.Bind(wx.EVT_COMBOBOX, self.onSelectTools)
        
        self.addPlotType.Bind(wx.EVT_BUTTON, self.onAddToolSet)
        
        
        if self.wheel_check.GetValue():
            self.wheelZoom_combo.Enable()
        else: 
            self.wheelZoom_combo.Disable()

        gridTools = wx.GridBagSizer(2,5)
        n = 0
        gridTools.Add(availableTools_label, (n,0), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n+1
        gridTools.Add(plotType_label, (n,0), flag=wx.ALIGN_CENTER_VERTICAL)
        gridTools.Add(self.plotTypeToolsSelect_propView, (n,1), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        gridTools.Add(self.addPlotType, (n,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
        n = n+1
        gridTools.Add(self.hover_check, (n,0), flag=wx.ALIGN_CENTER_VERTICAL)
        gridTools.Add(self.save_check, (n,1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n+1
        gridTools.Add(self.pan_check, (n,0), flag=wx.ALIGN_CENTER_VERTICAL)
        gridTools.Add(self.boxZoom_check, (n,1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n+1
        gridTools.Add(self.crosshair_check, (n,0), flag=wx.ALIGN_CENTER_VERTICAL)
        gridTools.Add(self.reset_check, (n,1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n+1
        gridTools.Add(self.wheel_check, (n,0), flag=wx.ALIGN_CENTER_VERTICAL)
        gridTools.Add(self.wheelZoom_combo, (n,1), wx.GBSpan(1,2), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n+1
        gridTools.Add(location_label, (n,0), flag=wx.ALIGN_CENTER_VERTICAL)
        gridTools.Add(self.location_combo, (n,1), wx.GBSpan(1,2))
        n = n+1
        gridTools.Add(availableActiveTools_label, (n,0), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n+1
        gridTools.Add(drag_label, (n,0), flag=wx.ALIGN_CENTER_VERTICAL)
        gridTools.Add(self.activeDrag_combo, (n,1), wx.GBSpan(1,2), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        n = n+1
        gridTools.Add(wheel_labe, (n,0), flag=wx.ALIGN_CENTER_VERTICAL)
        gridTools.Add(self.activeWheel_combo, (n,1), wx.GBSpan(1,2), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        n = n+1
        gridTools.Add(inspect_label, (n,0), flag=wx.ALIGN_CENTER_VERTICAL)
        gridTools.Add(self.activeInspect_combo, (n,1), wx.GBSpan(1,2), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
         
        toolsSizer.Add(gridTools, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        
        return toolsSizer

    def make1DplotSubPanel(self):
        mainBox = makeStaticBox(self.propertiesView, "1D plot properties", (230,-1), wx.BLUE)
        figSizer = wx.StaticBoxSizer(mainBox, wx.HORIZONTAL)
         
        lineWidth_label= makeStaticText(self.propertiesView, u"Line width:")
        self.line_width = wx.SpinCtrlDouble(self.propertiesView, wx.ID_ANY, 
                                                         value=str(self.config.interactive_line_width),min=0.5, max=10,
                                                         initial=self.config.interactive_line_width, inc=0.5, size=(50,-1))     
        self.line_width.Bind(wx.EVT_SPINCTRLDOUBLE, self.onChangeSettings)   

        lineAlpha_label= makeStaticText(self.propertiesView, u"Line transparency:")
        self.line_transparency = wx.SpinCtrlDouble(self.propertiesView, wx.ID_ANY, 
                                                   value=str(self.config.interactive_line_alpha),min=0, max=1,
                                                   initial=self.config.interactive_line_alpha, inc=0.1, size=(50,-1))
        self.line_transparency.Bind(wx.EVT_SPINCTRLDOUBLE, self.onChangeSettings)   
        
        lineStyle_label = wx.StaticText(self.propertiesView, -1, "Line style:")
        self.line_style = wx.ComboBox(self.propertiesView, -1, choices=self.config.interactive_line_style_choices, 
                                                  value="", style=wx.CB_READONLY)
        self.line_style.SetStringSelection(self.config.interactive_line_style)
        self.line_style.Bind(wx.EVT_COMBOBOX, self.onChangeSettings)         
         
        self.hoverVlineCheck = wx.CheckBox(self.propertiesView, -1 ,u'Hover tool linked to X axis (1D)', (15, 30))
        self.hoverVlineCheck.SetToolTip(wx.ToolTip("Hover tool information is linked to the X-axis"))
        self.hoverVlineCheck.SetValue(self.config.hoverVline)
        self.hoverVlineCheck.Bind(wx.EVT_CHECKBOX, self.onChangeSettings)   

        gridFigure = wx.GridBagSizer(2,2)
        n = 0
        gridFigure.Add(lineWidth_label, (n,0), wx.GBSpan(1,1))
        gridFigure.Add(self.line_width, (n,1), wx.GBSpan(1,1))
        n = n + 1
        gridFigure.Add(lineAlpha_label, (n,0), wx.GBSpan(1,1))
        gridFigure.Add(self.line_transparency, (n,1), wx.GBSpan(1,1))
        n = n + 1
        gridFigure.Add(lineStyle_label, (n,0), wx.GBSpan(1,1))
        gridFigure.Add(self.line_style, (n,1), wx.GBSpan(1,1))
        n = n + 1
        gridFigure.Add(self.hoverVlineCheck, (n,0), wx.GBSpan(1,2))
        
        
        figSizer.Add(gridFigure, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        
        return figSizer
    
    def makeOverLaySubPanel(self):
        mainBox = makeStaticBox(self.propertiesView, "Overlay plot properties", (230,-1), wx.BLUE)
        figSizer = wx.StaticBoxSizer(mainBox, wx.HORIZONTAL)
        
        layout_label = makeStaticText(self.propertiesView, u"Layout")
        self.layout_combo = wx.ComboBox(self.propertiesView, -1, choices=['Rows', 'Columns'],
                                        value=self.config.plotLayoutOverlay, style=wx.CB_READONLY)
        self.layout_combo.SetToolTip(wx.ToolTip("Select type of layout for the 2D overlay plots. The HTML viewer does not allow a good enough overlay function, so column/row option is provided. Default: Rows"))
        
        self.XYaxisLinkCheck = wx.CheckBox(self.propertiesView, -1 ,u'Link XY axes', (15, 30))
        self.XYaxisLinkCheck.SetValue(self.config.linkXYaxes)
 
        # bind 
        self.layout_combo.Bind(wx.EVT_COMBOBOX, self.onChangeSettings)
        self.XYaxisLinkCheck.Bind(wx.EVT_CHECKBOX, self.onChangeSettings) 
        
        gridFigure = wx.GridBagSizer(2,2)
        n = 0
        gridFigure.Add(layout_label, (n,0), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        gridFigure.Add(self.layout_combo, (n,1), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        gridFigure.Add(self.XYaxisLinkCheck, (n,2), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        
        figSizer.Add(gridFigure, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        return figSizer
    
    def makeColorbarSubPanel(self):
        mainBox = makeStaticBox(self.propertiesView, "Colorbar properties", (230,-1), wx.BLUE)
        figSizer = wx.StaticBoxSizer(mainBox, wx.HORIZONTAL)
         
        colorbar_label = makeStaticText(self.propertiesView, u"Colorbar:")
        self.interactive_colorbar = wx.CheckBox(self.propertiesView, -1 ,u'', (15, 30))
        self.interactive_colorbar.SetValue(self.config.interactive_colorbar)
        self.interactive_colorbar.Bind(wx.EVT_CHECKBOX, self.onChangeSettings)
         
        precision_label = makeStaticText(self.propertiesView, u"Precision")
        self.interactive_colorbar_precision = wx.SpinCtrlDouble(self.propertiesView, wx.ID_ANY, 
                                                   value=str(self.config.interactive_colorbar_precision),min=0, max=5,
                                                   initial=self.config.interactive_colorbar_precision, inc=1, size=(50,-1))
        self.interactive_colorbar_precision.SetToolTip(wx.ToolTip("Number of decimal places in the colorbar tickers"))
        
        self.interactive_colorbar_useScientific = wx.CheckBox(self.propertiesView, -1 ,u'Scientific\nnotation', (15, 30))
        self.interactive_colorbar_useScientific.SetValue(self.config.interactive_colorbar_useScientific)
        self.interactive_colorbar_useScientific.SetToolTip(wx.ToolTip("Enable/disable scientific notation of colorbar tickers"))
        self.interactive_colorbar_useScientific.Bind(wx.EVT_CHECKBOX, self.onEnableDisableItems)

        labelOffset_label = makeStaticText(self.propertiesView, u"Label offset:")
        self.interactive_colorbar_label_offset = wx.SpinCtrlDouble(self.propertiesView, wx.ID_ANY, 
                                                   value=str(self.config.interactive_colorbar_label_offset),min=0, max=100,
                                                   initial=self.config.interactive_colorbar_label_offset, inc=5, size=(50,-1))
        self.interactive_colorbar_label_offset.SetToolTip(wx.ToolTip("Distance between the colorbar and labels"))
        
        location_label = makeStaticText(self.propertiesView, u"Position:")
        self.interactive_colorbar_location = wx.ComboBox(self.propertiesView, -1, 
                                            choices=self.config.interactive_colorbarPosition_choices,
                                            value=self.config.interactive_colorbar_location, style=wx.CB_READONLY)
        self.interactive_colorbar_location.SetToolTip(wx.ToolTip("Colorbar position next to the plot. The colorbar orientation changes automatically"))
        
        offsetX_label = makeStaticText(self.propertiesView, u"Offset X")
        self.interactive_colorbar_offset_x = wx.SpinCtrlDouble(self.propertiesView, wx.ID_ANY, 
                                                   value=str(self.config.interactive_colorbar_offset_x),min=0, max=100,
                                                   initial=self.config.interactive_colorbar_offset_x, inc=5, size=(50,-1))
        self.interactive_colorbar_offset_x.SetToolTip(wx.ToolTip("Colorbar position offset in the X axis. Adjust if colorbar is too close or too far away from the plot"))
        
        offsetY_label = makeStaticText(self.propertiesView, u"Offset Y")
        self.interactive_colorbar_offset_y = wx.SpinCtrlDouble(self.propertiesView, wx.ID_ANY, 
                                                   value=str(self.config.interactive_colorbar_offset_y),min=0, max=100,
                                                   initial=self.config.interactive_colorbar_offset_y, inc=5, size=(50,-1))
        self.interactive_colorbar_offset_y.SetToolTip(wx.ToolTip("Colorbar position offset in the Y axis. Adjust if colorbar is too close or too far away from the plot"))

        padding_label = makeStaticText(self.propertiesView, u"Pad")
        self.colorbarPadding = wx.SpinCtrlDouble(self.propertiesView, wx.ID_ANY, 
                                                   value=str(self.config.interactive_colorbar_width),min=0, max=100,
                                                   initial=self.config.interactive_colorbar_width, inc=5, size=(50,-1))
        self.colorbarPadding.SetToolTip(wx.ToolTip(""))

        margin_label = makeStaticText(self.propertiesView, u"Width")
        self.colorbarWidth = wx.SpinCtrlDouble(self.propertiesView, wx.ID_ANY, 
                                                   value=str(self.config.interactive_colorbar_width), min=0, max=100,
                                                   initial=self.config.interactive_colorbar_width, inc=5, size=(50,-1))
        self.colorbarWidth.SetToolTip(wx.ToolTip(""))
        
        
        # bind 
        self.interactive_colorbar_precision.Bind(wx.EVT_SPINCTRLDOUBLE, self.onChangeSettings)
        self.interactive_colorbar_useScientific.Bind(wx.EVT_CHECKBOX, self.onChangeSettings)
        self.interactive_colorbar_location.Bind(wx.EVT_COMBOBOX, self.onChangeSettings) 
        self.interactive_colorbar_offset_x.Bind(wx.EVT_SPINCTRLDOUBLE, self.onChangeSettings)
        self.interactive_colorbar_offset_y.Bind(wx.EVT_SPINCTRLDOUBLE, self.onChangeSettings)
        self.colorbarPadding.Bind(wx.EVT_SPINCTRLDOUBLE, self.onChangeSettings)
        self.colorbarWidth.Bind(wx.EVT_SPINCTRLDOUBLE, self.onChangeSettings)
        self.interactive_colorbar_label_offset.Bind(wx.EVT_SPINCTRLDOUBLE, self.onChangeSettings)
        
        gridFigure = wx.GridBagSizer(2,2)
        n = 0
        gridFigure.Add(colorbar_label, (n,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        gridFigure.Add(self.interactive_colorbar, (n,1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n+1
        gridFigure.Add(precision_label, (n,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        gridFigure.Add(self.interactive_colorbar_precision, (n,1), flag=wx.ALIGN_CENTER_VERTICAL)
        gridFigure.Add(self.interactive_colorbar_useScientific, (n,2), wx.GBSpan(1,2), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n+1
        gridFigure.Add(labelOffset_label, (n,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        gridFigure.Add(self.interactive_colorbar_label_offset, (n,1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n+1
        gridFigure.Add(location_label, (n,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        gridFigure.Add(offsetX_label, (n,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        gridFigure.Add(offsetY_label, (n,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        gridFigure.Add(padding_label, (n,3), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        gridFigure.Add(margin_label, (n,4), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        n = n+1
        gridFigure.Add(self.interactive_colorbar_location, (n,0), flag=wx.ALIGN_CENTER_VERTICAL)
        gridFigure.Add(self.interactive_colorbar_offset_x, (n,1), flag=wx.ALIGN_CENTER_VERTICAL)
        gridFigure.Add(self.interactive_colorbar_offset_y, (n,2), flag=wx.ALIGN_CENTER_VERTICAL)
        gridFigure.Add(self.colorbarPadding, (n,3), flag=wx.ALIGN_CENTER_VERTICAL)
        gridFigure.Add(self.colorbarWidth, (n,4), flag=wx.ALIGN_CENTER_VERTICAL)
        
        figSizer.Add(gridFigure, 0, wx.ALIGN_CENTER|wx.ALL, 5)
          
        return figSizer
    
    def makeLegendSubPanel(self):
        mainBox = makeStaticBox(self.propertiesView, "Interactive legend properties", (210,-1), wx.BLUE)
        figSizer = wx.StaticBoxSizer(mainBox, wx.HORIZONTAL)
        
        legend_label = makeStaticText(self.propertiesView, u"Legend:")
        self.legend_legend = wx.CheckBox(self.propertiesView, -1 ,u'', (15, 30))
        self.legend_legend.SetValue(self.config.interactive_legend)
        self.legend_legend.Bind(wx.EVT_CHECKBOX, self.onChangeSettings)
        
        position_label = makeStaticText(self.propertiesView, u"Position")
        self.legend_position = wx.ComboBox(self.propertiesView, -1, 
                                           choices=self.config.interactive_legend_location_choices,
                                           value=self.config.interactive_legend_location, style=wx.CB_READONLY)
        self.legend_position.Bind(wx.EVT_COMBOBOX, self.onChangeSettings)
        
        orientation_label = makeStaticText(self.propertiesView, u"Orientation")
        self.legend_orientation = wx.ComboBox(self.propertiesView, -1, 
                                               choices=self.config.interactive_legend_orientation_choices,
                                               value=self.config.interactive_legend_orientation, style=wx.CB_READONLY)
        self.legend_orientation.Bind(wx.EVT_COMBOBOX, self.onChangeSettings)

        legendAlpha_label = makeStaticText(self.propertiesView, u"Legend transparency")
        self.legend_transparency = wx.SpinCtrlDouble(self.propertiesView, wx.ID_ANY, 
                                                     value=str(self.config.interactive_legend_background_alpha),min=0, max=1,
                                                     initial=self.config.interactive_legend_background_alpha, inc=0.1, size=(50,-1))
        self.legend_transparency.Bind(wx.EVT_SPINCTRLDOUBLE, self.onChangeSettings)
        
        fontSize_label = makeStaticText(self.propertiesView, u"Font size")
        self.legend_fontSize = wx.SpinCtrlDouble(self.propertiesView, wx.ID_ANY, 
                                                 value=str(self.config.interactive_legend_font_size),min=0, max=32,
                                                 initial=self.config.interactive_legend_font_size, inc=2, size=(50,-1))
        self.legend_fontSize.Bind(wx.EVT_SPINCTRLDOUBLE, self.onChangeSettings)

        action_label = makeStaticText(self.propertiesView, u"Action")
        self.legend_click_policy = wx.ComboBox(self.propertiesView, -1, 
                                               choices=self.config.interactive_legend_click_policy_choices,
                                               value=self.config.interactive_legend_click_policy, style=wx.CB_READONLY)
        self.legend_click_policy.Bind(wx.EVT_COMBOBOX, self.onChangeSettings)
        self.legend_click_policy.Bind(wx.EVT_COMBOBOX, self.onEnableDisableItems)
        
        muteAlpha_label = makeStaticText(self.propertiesView, u"Line transparency")
        self.legend_mute_transparency = wx.SpinCtrlDouble(self.propertiesView, wx.ID_ANY, 
                                                   value=str(self.config.interactive_legend_mute_alpha),min=0, max=1,
                                                   initial=self.config.interactive_legend_mute_alpha, inc=0.1, size=(50,-1))
        self.legend_mute_transparency.Bind(wx.EVT_SPINCTRLDOUBLE, self.onChangeSettings)
        

        gridFigure = wx.GridBagSizer(2,2)
        n = 0
        gridFigure.Add(legend_label, (n,0), flag=wx.ALIGN_LEFT)
        gridFigure.Add(self.legend_legend, (n,1), flag=wx.EXPAND)
        n = n + 1
        gridFigure.Add(position_label, (n,0), flag=wx.ALIGN_LEFT)
        gridFigure.Add(self.legend_position, (n,1), flag=wx.EXPAND)
        n = n + 1
        gridFigure.Add(orientation_label, (n,0), flag=wx.ALIGN_LEFT)
        gridFigure.Add(self.legend_orientation, (n,1), flag=wx.EXPAND)
        n = n + 1
        gridFigure.Add(fontSize_label, (n,0), flag=wx.ALIGN_LEFT)
        gridFigure.Add(self.legend_fontSize, (n,1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        gridFigure.Add(legendAlpha_label, (n,0), flag=wx.ALIGN_LEFT)
        gridFigure.Add(self.legend_transparency, (n,1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        gridFigure.Add(action_label, (n,0), flag=wx.ALIGN_LEFT)
        gridFigure.Add(self.legend_click_policy, (n,1), flag=wx.EXPAND)
        n = n + 1
        gridFigure.Add(muteAlpha_label, (n,0), flag=wx.ALIGN_LEFT)
        gridFigure.Add(self.legend_mute_transparency, (n,1), flag=wx.ALIGN_CENTER_VERTICAL)
        
        figSizer.Add(gridFigure, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        return figSizer
    
    def makeDlgButtons(self):
        mainSizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, ""), wx.VERTICAL)
        
        pathBtn = wx.Button(self, -1, "Set Path", size=(-1,22))
        saveBtn = wx.Button(self, -1, "Export HTML", size=(-1,22))
        cancelBtn = wx.Button(self, -1, "Cancel", size=(-1,22))
        
        openHTMLWebBtn = wx.Button(self, ID_helpHTMLEditor, "HTML Editor", size=(-1,22))
        openHTMLWebBtn.SetToolTip(wx.ToolTip("Opens a web-based HTML editor"))
        
        itemPath_label = wx.StaticText(self, -1, "File path:")
        self.itemPath_value = wx.TextCtrl(self, -1, "", size=(-1, -1), style=wx.TE_READONLY)
        self.itemPath_value.SetValue(str(self.currentPath))
        self.openInBrowserCheck = makeCheckbox(self, u"Open in browser after saving")
        self.openInBrowserCheck.SetValue(self.config.openInteractiveOnSave)
        
        btnGrid = wx.GridBagSizer(1, 1)
        btnGrid.Add(openHTMLWebBtn, (0,0), flag=wx.ALIGN_CENTER|wx.ALIGN_CENTER_HORIZONTAL)
        btnGrid.Add(saveBtn, (0,1), flag=wx.ALIGN_CENTER|wx.ALIGN_CENTER_HORIZONTAL)
        btnGrid.Add(cancelBtn, (0,2), flag=wx.ALIGN_CENTER|wx.ALIGN_CENTER_HORIZONTAL)
        btnGrid.Add(self.openInBrowserCheck, (0,3), flag=wx.ALIGN_CENTER|wx.ALIGN_CENTER_HORIZONTAL)
        
        sizer_row_1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_row_1.Add(itemPath_label, 0, wx.EXPAND, 0)
        sizer_row_1.Add(self.itemPath_value, 1, wx.EXPAND, 0)
        sizer_row_1.Add(pathBtn, 0, wx.EXPAND, 0)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(sizer_row_1, 0, wx.EXPAND, 0)
        sizer.Add(btnGrid, 0, wx.EXPAND, 0)
        
        # make bindings
        saveBtn.Bind(wx.EVT_BUTTON, self.onGenerateHTML)
        openHTMLWebBtn.Bind(wx.EVT_BUTTON, self.presenter.onLibraryLink)
        cancelBtn.Bind(wx.EVT_BUTTON, self.onClose)
        pathBtn.Bind(wx.EVT_BUTTON, self.onGetSavePath)

        mainSizer.Add(sizer, 0, wx.EXPAND|wx.ALL, 2)
        return mainSizer
        
    def onTableTool(self, evt):
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_interactivePanel_table_document)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_interactivePanel_table_type)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_interactivePanel_table_file)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_interactivePanel_table_title)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_interactivePanel_table_header)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_interactivePanel_table_footnote)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_interactivePanel_table_colormap)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_interactivePanel_table_page)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_interactivePanel_table_tools)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_interactivePanel_table_order)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_ionPanel_table_label)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_ionPanel_table_method)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_interactivePanel_table_hideAll)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_interactivePanel_table_restoreAll)
        

        menu = wx.Menu()
        n = 0
        self.table_start = menu.AppendCheckItem(ID_interactivePanel_table_document, 'Table: Document')
        self.table_start.Check(self.config._interactiveSettings[n]['show'])
        n = n + 1
        self.table_end = menu.AppendCheckItem(ID_interactivePanel_table_type, 'Table: Type')
        self.table_end.Check(self.config._interactiveSettings[n]['show'])
        n = n + 1
        self.table_charge = menu.AppendCheckItem(ID_interactivePanel_table_file, 'Table: File/ion/item')
        self.table_charge.Check(self.config._interactiveSettings[n]['show'])
        n = n + 1
        self.table_intensity = menu.AppendCheckItem(ID_interactivePanel_table_title, 'Table: Title')
        self.table_intensity.Check(self.config._interactiveSettings[n]['show'])
        n = n + 1
        self.table_color = menu.AppendCheckItem(ID_interactivePanel_table_header, 'Table: Header')
        self.table_color.Check(self.config._interactiveSettings[n]['show'])
        n = n + 1
        self.table_colormap = menu.AppendCheckItem(ID_interactivePanel_table_footnote, 'Table: Footnote')
        self.table_colormap.Check(self.config._interactiveSettings[n]['show'])
        n = n + 1
        self.table_alpha = menu.AppendCheckItem(ID_interactivePanel_table_colormap, 'Table: Color/colormap')
        self.table_alpha.Check(self.config._interactiveSettings[n]['show'])
        n = n + 1
        self.table_mask = menu.AppendCheckItem(ID_interactivePanel_table_page, 'Table: Page')
        self.table_mask.Check(self.config._interactiveSettings[n]['show'])
        n = n + 1
        self.table_label = menu.AppendCheckItem(ID_interactivePanel_table_tools, 'Table: Tools')
        self.table_label.Check(self.config._interactiveSettings[n]['show'])
        n = n + 1
        self.table_method = menu.AppendCheckItem(ID_interactivePanel_table_order, 'Table: Order')
        self.table_method.Check(self.config._interactiveSettings[n]['show'])
        menu.AppendSeparator()
        self.table_index = menu.AppendItem(makeMenuItem(parent=menu, id=ID_interactivePanel_table_hideAll,
                                     text='Table: Hide all', 
                                     bitmap=self.icons.iconsLib['hide_table_16']))
        self.table_index = menu.AppendItem(makeMenuItem(parent=menu, id=ID_interactivePanel_table_restoreAll,
                                     text='Table: Restore all', 
                                     bitmap=self.icons.iconsLib['show_table_16']))
        
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def onUpdateTable(self, evt):
        evtID = evt.GetId()
        
        # check which event was triggered
        if evtID == ID_interactivePanel_table_document:
            col_index = self.config.interactiveColNames['document']
        elif evtID == ID_interactivePanel_table_type:
            col_index = self.config.interactiveColNames['type']
        elif evtID == ID_interactivePanel_table_file:
            col_index = self.config.interactiveColNames['file']
        elif evtID == ID_interactivePanel_table_title:
            col_index = self.config.interactiveColNames['title']
        elif evtID == ID_interactivePanel_table_header:
            col_index = self.config.interactiveColNames['header']
        elif evtID == ID_interactivePanel_table_footnote:
            col_index = self.config.interactiveColNames['footnote']
        elif evtID == ID_interactivePanel_table_colormap:
            col_index = self.config.interactiveColNames['color']
        elif evtID == ID_interactivePanel_table_page:
            col_index = self.config.interactiveColNames['page']
        elif evtID == ID_interactivePanel_table_tools:
            col_index = self.config.interactiveColNames['tools']
        elif evtID == ID_interactivePanel_table_order:
            col_index = self.config.interactiveColNames['order']
        elif evtID == ID_interactivePanel_table_restoreAll:
            for i in range(len(self.config._interactiveSettings)):
                self.config._interactiveSettings[i]['show'] = True
                col_width = self.config._interactiveSettings[i]['width']
                self.itemsList.SetColumnWidth(i, col_width)
            return
        elif evtID == ID_interactivePanel_table_hideAll:
            for i in range(len(self.config._interactiveSettings)):
                self.config._interactiveSettings[i]['show'] = False
                col_width = 0
                self.itemsList.SetColumnWidth(i, col_width)
            return 
        
        # check values
        col_check = not self.config._interactiveSettings[col_index]['show']
        self.config._interactiveSettings[col_index]['show'] = col_check
        if col_check: col_width = self.config._interactiveSettings[col_index]['width']
        else: col_width = 0
        # set new column width
        self.itemsList.SetColumnWidth(col_index, col_width)

    def makeTooltip(self, text=None, delay=500):
        tip = wx.ToolTip(text)
        tip.SetDelay(delay)
        
        return tip
     
    def onStartEditingItem(self, evt):
        self.Unbind(wx.EVT_CHAR_HOOK, id=wx.ID_ANY)
        
        self.currentItem = evt.m_itemIndex
        self.onItemSelected(evt)
        
    def _updateTable(self):
        title = self.itemsList.GetItem(self.currentItem,self.config.interactiveColNames['title']).GetText()
        header = self.itemsList.GetItem(self.currentItem,self.config.interactiveColNames['header']).GetText()
        footnote = self.itemsList.GetItem(self.currentItem,self.config.interactiveColNames['footnote']).GetText()
        order = self.itemsList.GetItem(self.currentItem,self.config.interactiveColNames['order']).GetText()
        
        self.itemName_value.SetValue(title)
        self.itemHeader_value.SetValue(header)
        self.itemFootnote_value.SetValue(footnote)
        self.order_value.SetValue(order)
        
        self.onAnnotateItems(None, itemID=self.currentItem)
        
    def onFinishEditingItem(self, evt):
        """
        Modify information after finished editing in the table
        """
         
        title = self.itemsList.GetItem(self.currentItem,self.config.interactiveColNames['title']).GetText()
        header = self.itemsList.GetItem(self.currentItem,self.config.interactiveColNames['header']).GetText()
        footnote = self.itemsList.GetItem(self.currentItem,self.config.interactiveColNames['footnote']).GetText()
        order = self.itemsList.GetItem(self.currentItem,self.config.interactiveColNames['order']).GetText()
 
        self.itemName_value.SetValue(title)
        self.itemHeader_value.SetValue(header)
        self.itemFootnote_value.SetValue(footnote)
        self.order_value.SetValue(order)

        wx.CallAfter(self._updateTable)
        self._preAnnotateItems()
        
        self.Bind(wx.EVT_CHAR_HOOK, self.OnKey)

    def onEnableDisableItems(self, evt):
        self.config.interactive_tick_useScientific = self.tickUseScientific.GetValue()
        if self.config.interactive_tick_useScientific: self.tickPrecision.Disable()
        else: self.tickPrecision.Enable()
        
        self.config.interactive_colorbar_useScientific = self.interactive_colorbar_useScientific.GetValue() 
        if self.config.interactive_colorbar_useScientific: self.interactive_colorbar_precision.Disable()
        else: self.interactive_colorbar_precision.Enable()
        
        self.config.interactive_legend_click_policy = self.legend_click_policy.GetStringSelection()
        if self.config.interactive_legend_click_policy == 'mute': self.legend_mute_transparency.Enable()
        else: self.legend_mute_transparency.Disable()
        
        if self.linearizeCheck.GetValue() and self.linearizeCheck.IsEnabled(): self.binSize_value.Enable()
        else: self.binSize_value.Disable()
        
        if evt != None:
            evt.Skip()
    
    def onAddPage(self, evt):
        pageName = dialogs.dlgAsk('Please select page name.', defaultValue='')
        if pageName == '' or pageName == False: 
            print("Incorrect name. Operation was cancelled")
            return
        elif pageName == 'None': 
                msg = 'This name is reserved. Please try again.'
                dialogs.dlgBox(exceptionTitle='Incorrect name', 
                               exceptionMsg= msg,
                               type="Error")
                return
        
        # If page name is correct, we can add it to the combo boxes
        self.config.pageDict[pageName] = {'layout':'Individual', 
                                          'rows':None, 
                                          'columns':None,
                                          'name':pageName}

        self.pageLayoutSelect_propView.Append(pageName)
        self.pageLayoutSelect_htmlView.Append(pageName)
        self.pageLayoutSelect_toolbar.Append(pageName)
        
        self.editorBook.SetSelection(1)
        self.onChangePage(preset=pageName, evt=None)
        
        if evt != None:
            evt.Skip()
        
    def onAddToolSet(self, evt):
        toolName = dialogs.dlgAsk('Please select ToolSet name.', defaultValue='')
        if toolName == '': return
        elif toolName == '1D' or toolName == '2D' or toolName == 'Overlay': 
                msg = "'%s' name is reserved. Please try again." % (toolName)
                dialogs.dlgBox(exceptionTitle='Incorrect name', 
                               exceptionMsg= msg,
                               type="Error")
                return
            
        # Add new toolset to dictionary
        self.config.interactiveToolsOnOff[toolName] = {'hover':False,'save':True,'pan':False,
                                                      'boxzoom':False,'crosshair':False,
                                                      'reset':True, 'resize':False,
                                                      'wheel':False, 'wheelType':'Wheel Zoom X',
                                                      'activeDrag':'None',
                                                      'activeWheel':'None',
                                                      'activeInspect':'None'}
        # Add to combo boxes
        self.plotTypeToolsSelect_htmlView.Append(toolName)
        self.plotTypeToolsSelect_propView.Append(toolName)
        self.plotTypeToolsSelect_toolbar.Append(toolName)
        
        self.onSetupTools(preset=toolName, evt=None)
        
        
        if evt != None:
            evt.Skip()
    
    def onChangePage(self, evt, preset=None):
        """
        This function changes the values shown in the GUI for the selected page
        -----------
        @param preset: name of the new page
        """
        
        if preset!=None:
            self.pageLayoutSelect_propView.SetStringSelection(preset)
            
        selectedItem = self.pageLayoutSelect_propView.GetStringSelection()
                
        rowValue = str(self.config.pageDict[selectedItem].get('rows', None))
        colValue = str(self.config.pageDict[selectedItem].get('columns', None))
        
        self.layoutDoc_combo.SetStringSelection(self.config.pageDict[selectedItem].get('layout', 'Individual'))
        
        self.columns_value.SetValue(colValue)
        
        
        self.onSelectPageProperties(evt=None)
        if evt != None:
            evt.Skip()
            
    def onSelectPageProperties(self, evt):
                
        selectedItem = self.pageLayoutSelect_propView.GetStringSelection()
        # Enable/Disable row/column boxes
        if selectedItem == 'None':
            self.columns_value.Disable()
            self.layoutDoc_combo.Disable()
        else:
            self.layoutDoc_combo.Enable()
            if self.layoutDoc_combo.GetStringSelection() != 'Grid':
                self.columns_value.Disable()
            else:
                self.columns_value.Enable()
            
        # Change values in dictionary
        if selectedItem != 'None':
            self.config.pageDict[selectedItem] = {'layout':self.layoutDoc_combo.GetStringSelection(), 
                                                  'columns':str2int(self.columns_value.GetValue()),
                                                  'name':selectedItem}

        if evt != None:
            evt.Skip()

    def onChangeSettings(self, evt):
        """
        Update figure settings
        """
        
        self.config.interactive_override_defaults = self.html_override.GetValue()
        
        # Figure size
        self.config.figHeight = str2int(self.figHeight_value.GetValue())
        self.config.figWidth = str2int(self.figWidth_value.GetValue())
        self.config.figHeight1D = str2int(self.figHeight1D_value.GetValue())
        self.config.figWidth1D = str2int(self.figWidth1D_value.GetValue())
        
        # Figure format 
        self.config.layoutModeDoc = self.layoutDoc_combo.GetValue()
        self.config.plotLayoutOverlay = self.layout_combo.GetValue()
        self.defNumColumns = self.columns_value.GetValue()
        self.config.linkXYaxes = self.XYaxisLinkCheck.GetValue()
        self.config.hoverVline = self.hoverVlineCheck.GetValue()

        # Font 
        self.config.interactive_title_fontSize = self.titleSlider.GetValue()
        self.config.interactive_title_weight = self.titleBoldCheck.GetValue()
        self.config.interactive_label_fontSize = self.labelSlider.GetValue()
        self.config.interactive_label_weight = self.labelBoldCheck.GetValue()
        self.config.interactive_tick_fontSize = self.tickSlider.GetValue()
        self.config.interactive_annotation_fontSize = self.notationSlider.GetValue()
        self.config.interactive_annotation_weight = self.notationBoldCheck.GetValue()
        self.config.interactive_annotation_alpha = self.rmsd_label_transparency.GetValue()
    
        # ticks parameters
        self.config.interactive_tick_useScientific = self.tickUseScientific.GetValue()
        self.config.interactive_tick_precision = int(self.tickPrecision.GetValue())
        
        # tools
        self.config.toolsLocation = self.location_combo.GetValue()
        
        # Grid overlay settings
        self.config.interactive_grid_label_size = self.grid_label_size_value.GetValue()
        self.config.interactive_grid_label_weight = self.grid_label_weight.GetValue()
                
        # colorbar
        self.config.interactive_colorbar = self.interactive_colorbar.GetValue() 
        self.config.interactive_colorbar_precision = str2int(self.interactive_colorbar_precision.GetValue())
        self.config.interactive_colorbar_useScientific = self.interactive_colorbar_useScientific.GetValue()        
        self.config.interactive_colorbar_offset_x = str2int(self.interactive_colorbar_offset_x.GetValue())
        self.config.interactive_colorbar_offset_y = str2int(self.interactive_colorbar_offset_y.GetValue())
        self.config.interactive_colorbar_location = self.interactive_colorbar_location.GetStringSelection()
        if self.config.interactive_colorbar_location in ('right', 'left'): 
            self.config.interactive_colorbar_orientation = 'vertical'
        else: 
            self.config.interactive_colorbar_orientation = 'horizontal'
        
        self.config.interactive_colorbar_width = str2int(self.colorbarPadding.GetValue())
        self.config.interactive_colorbar_width = str2int(self.colorbarWidth.GetValue())
        self.config.interactive_colorbar_label_offset = str2int(self.interactive_colorbar_label_offset.GetValue())

        # Plot parameters
        self.config.interactive_outline_width = str2num(self.interactive_outline_width.GetValue())
        self.config.interactive_outline_alpha = str2num(self.interactive_outline_alpha.GetValue())
        self.config.interactive_border_min_right = str2int(self.interactive_border_min_right.GetValue())
        self.config.interactive_border_min_left = str2int(self.interactive_border_min_left.GetValue())
        self.config.interactive_border_min_top = str2int(self.interactive_border_min_top.GetValue())
        self.config.interactive_border_min_bottom = str2int(self.interactive_border_min_bottom.GetValue())
        
        # legend
        self.config.interactive_legend = self.legend_legend.GetValue()
        self.config.interactive_legend_location = self.legend_position.GetStringSelection()
        self.config.interactive_legend_click_policy = self.legend_click_policy.GetStringSelection()
        self.config.interactive_legend_orientation = self.legend_orientation.GetStringSelection()
        self.config.interactive_legend_font_size = self.legend_fontSize.GetValue()
        self.config.interactive_legend_background_alpha = self.legend_transparency.GetValue()
        self.config.interactive_legend_mute_alpha = self.legend_mute_transparency.GetValue()
        
        # line parameters
        self.config.interactive_line_width = self.line_width.GetValue()
        self.config.interactive_line_alpha =  self.line_transparency.GetValue()
        self.config.interactive_line_style = self.line_style.GetStringSelection()
        
        if evt != None:
            evt.Skip() 
          
    def onSetupTools(self, evt=None, preset=None):
        """
        This function is used to pre-set which tools are selected in the GUI
        parameters:
        -----------
        @param preset: name of the toolset
        """
        if preset!=None:
            self.plotTypeToolsSelect_propView.SetStringSelection(preset)

        # Get current plot type
        currentPlot = self.plotTypeToolsSelect_propView.GetStringSelection()
        
        # Get tools dictionary
        toolSettings = self.config.interactiveToolsOnOff[currentPlot]
        
        self.hover_check.SetValue(toolSettings['hover'])
        self.save_check.SetValue(toolSettings['save'])
        self.pan_check.SetValue(toolSettings['pan'])
        self.boxZoom_check.SetValue(toolSettings['boxzoom'])
        self.crosshair_check.SetValue(toolSettings['crosshair'])
        self.reset_check.SetValue(toolSettings['reset'])
        self.wheel_check.SetValue(toolSettings['wheel'])
        self.wheelZoom_combo.SetStringSelection(toolSettings['wheelType'])
        
        if toolSettings['wheel']: self.wheelZoom_combo.Enable()
        else: self.wheelZoom_combo.Disable()
            
        
        
        self.activeDrag_combo.SetStringSelection(toolSettings['activeDrag'])
        self.activeWheel_combo.SetStringSelection(toolSettings['activeWheel'])
        self.activeInspect_combo.SetStringSelection(toolSettings['activeInspect'])
         
    def onSelectTools(self, getTools=False, evt=None):
        """
        @param getTools: returns a dictionary of tools to be appended to the plot
        """
        
        # Find one which (if any) wheel too is selected
        toolList = []
        wheelDict = {'Wheel Zoom XY':'wheel_zoom', 
                     'Wheel Zoom X':'xwheel_zoom',
                     'Wheel Zoom Y':'ywheel_zoom'}
        if self.wheel_check.GetValue():
            self.wheelZoom_combo.Enable()
            wheelTool = wheelDict[self.wheelZoom_combo.GetStringSelection()]
            toolList.append(wheelTool)
        else: 
            self.wheelZoom_combo.Disable()
        
        listToGetState = {'save':self.save_check, 'pan': self.pan_check,
                          'box_zoom':self.boxZoom_check, 'crosshair':self.crosshair_check, 
                          'reset':self.reset_check}
        # Iterate over the list to get their state
        for item in listToGetState:
            itemState = listToGetState[item].GetValue()
            if itemState:
                toolList.append(item)
        
        activeDragTools = {'Box Zoom':'box_zoom', 'Pan':'pan', 'Pan X':'xpan', 'Pan Y':'ypan',
                           'auto':'auto', 'None':None}
        
        activeWheelTools = {'Wheel Zoom XY':'wheel_zoom', 'Wheel Zoom X':'xwheel_zoom',
                            'Wheel Zoom Y':'ywheel_zoom', 'auto':'auto', 'None':None}
        
        activeHoverTools = {'Hover':'hover', 'Crosshair':'crosshair', 'auto':'auto', 'None':None}
        
        # Get current states of the active tools
        self.config.activeDrag = self.activeDrag_combo.GetStringSelection()
        self.config.activeWheel = self.activeWheel_combo.GetStringSelection()
        self.config.activeInspect = self.activeInspect_combo.GetStringSelection()
        
        # Match those values to dictionary
        self.activeDrag = activeDragTools[self.activeDrag_combo.GetStringSelection()]
        self.activeWheel = activeWheelTools[self.activeWheel_combo.GetStringSelection()]
        self.activeInspect = activeHoverTools[self.activeInspect_combo.GetStringSelection()]
        
        # Check that those tools were selected. If they are not in the list, it 
        # will throw an error
        for active in [self.activeDrag, self.activeWheel, self.activeInspect]:
            if active == None or active == 'auto' or active=='hover': continue
            else:
                if not active in toolList:
                    toolList.append(active)
                    
        # Set the tools
        self.tools = ','.join(toolList)
        
        # Update tools dictionary
        currentTool = self.plotTypeToolsSelect_propView.GetValue()
        self.config.interactiveToolsOnOff[currentTool]['hover'] = self.hover_check.GetValue()
        self.config.interactiveToolsOnOff[currentTool]['pan'] = self.pan_check.GetValue()
        self.config.interactiveToolsOnOff[currentTool]['save'] = self.save_check.GetValue()
        self.config.interactiveToolsOnOff[currentTool]['reset'] = self.reset_check.GetValue()
        self.config.interactiveToolsOnOff[currentTool]['boxzoom'] = self.boxZoom_check.GetValue()
        self.config.interactiveToolsOnOff[currentTool]['crosshair'] = self.crosshair_check.GetValue()
        self.config.interactiveToolsOnOff[currentTool]['wheel'] = self.wheel_check.GetValue()
        self.config.interactiveToolsOnOff[currentTool]['wheelType'] = self.wheelZoom_combo.GetStringSelection()
        self.config.interactiveToolsOnOff[currentTool]['activeDrag'] = self.activeDrag_combo.GetStringSelection()
        self.config.interactiveToolsOnOff[currentTool]['activeWheel'] = self.activeWheel_combo.GetStringSelection()
        self.config.interactiveToolsOnOff[currentTool]['activeInspect'] = self.activeInspect_combo.GetStringSelection()
        

        if getTools:
            toolSet = {'tools':self.tools,
                       'hover':self.hover_check.GetValue(),
                       'activeDrag':self.activeDrag,
                       'activeWheel':self.activeWheel,
                       'activeInspect':self.activeInspect}
            return toolSet

        if evt != None:
            evt.Skip() 
        
    def getToolSet(self, plotType=None, subType=None, preset=None, 
                   evt=None):
        
        # If empty, populate with defaults
        if plotType == '':
            preset='2D'
        elif plotType == 'MS' or plotType == 'RT' or plotType == '1D':
            preset='1D'
        elif plotType == '2D' or plotType == 'Overlay':
            preset='2D'
        # In case it is a complex dataset
        elif plotType == None and subType != None:
            method = re.split('-|,|:|__', subType)
            if any(method[0] in item for item in ['Mask', 'Transparent']):
                preset='Overlay'
            elif any(method[0] in item for item in ['RMSD', 'RMSF','Mean',
                                                    'Standard Deviation',
                                                    'Variance', 'RMSD Matrix']):
                preset='2D'
            elif any(method[0] in item for item in ['1D','RT']):
                preset='1D'
            
        # User defined values
        elif plotType==None and subType==None and preset!=None:
            preset=preset
        else:
            preset='2D'
        
        self.onSetupTools(preset=preset)
        toolSet = self.onSelectTools(getTools=True)
        
        # If item type is statistical or overlay return tools + name
        if plotType == None and subType != None:
            return preset, toolSet
        else:
            return toolSet
          
    def onChangeComboBox(self, evt=None):
        self.itemOrder_combo.Clear()
         
        for i in self.listOfPlots:
            self.itemOrder_combo.Append(str(i))
 
    def checkIfHasHTMLkeys(self, dictionary):
        """
        Helper function to see if dataset has html dictionary keys
        """
        if 'title' in dictionary: pass
        else: dictionary['title'] = ''

        if 'header' in dictionary: pass
        else: dictionary['header'] = ''
     
        if 'footnote' in dictionary: pass
        else: dictionary['footnote'] = ''
            
        if 'order' in dictionary: pass
        else: dictionary['order'] = ''

        if 'cmap' in dictionary: pass
        else: dictionary['cmap'] = ''
        
        if 'colorbar' in dictionary: pass
        else: dictionary['colorbar'] = False

        if 'page' in dictionary: 
            # If it has page information in dictionary, add it to the config object
            self.config.pageDict[dictionary['page']['name']] = dictionary['page']
        else: dictionary['page'] = self.config.pageDict['None']
        
        # If it has page information in dictionary, add it to the config object
        if 'tools' in dictionary: pass
        else: dictionary['tools'] = {}
        
        if 'interactive_params' in dictionary: pass
        else: 
            dictionary['interactive_params'] = {'line_width':self.config.interactive_line_width,
                                                'line_alpha':self.config.interactive_line_alpha,
                                                'line_style':self.config.interactive_line_style,
                                                'line_linkXaxis':self.config.hoverVline,
                                                'overlay_layout':self.config.plotLayoutOverlay,
                                                'overlay_linkXY':self.config.linkXYaxes,
                                                'colorbar':self.config.interactive_colorbar,
                                                'legend':self.config.interactive_legend}
        
        if 'interactive' in dictionary: pass
        else: 
            interactiveDict = {'order':'', 
                               'page':self.config.pageDict['None'],
                               'tools':''}
            dictionary['interactive'] = interactiveDict 
        
        return dictionary
                  
    def checkToolsUnidec(self, key):
        if key in ['Processed', 'Fitted', 'MW distribution', 'm/z with isolated species']:
            toolname = "1D"
            toolset = self.getToolSet(plotType='1D')
        elif key in ['m/z vs Charge', 'MW vs Charge']:
            toolname = "2D"
            toolset = self.getToolSet(plotType='2D')
        elif key == "Barchart":
            toolname = "1D"
            toolset = self.getToolSet(plotType='1D')
            
        return toolname, toolset
                    
    def populateTable(self):
        """
        Populate table with appropriate dataset values
        """
        if len(self.documentsDict) > 0:
            for key in self.documentsDict:
                docData = self.documentsDict[key]                
                if docData.gotMS == True:
                    docData.massSpectrum = self.checkIfHasHTMLkeys(docData.massSpectrum)
                    if docData.massSpectrum['cmap'] == '': docData.massSpectrum['cmap'] = self.config.lineColour_1D
                    if len(docData.massSpectrum['tools']) == 0:
                        docData.massSpectrum['tools']['name'] = '1D'
                        docData.massSpectrum['tools']['tools'] = self.getToolSet(plotType='MS')
                    self.itemsList.Append([key, 'MS', '',
                                           docData.massSpectrum['title'],
                                           docData.massSpectrum['header'],
                                           docData.massSpectrum['footnote'],
                                           docData.massSpectrum['cmap'],
                                           docData.massSpectrum['page']['name'],
                                           docData.massSpectrum['tools']['name'],
                                           docData.massSpectrum['order'],
                                           ])
                    if 'unidec' in docData.massSpectrum:
                        for innerKey in docData.massSpectrum['unidec']:
                            if innerKey in ['Charge information']: continue
                            docData.massSpectrum['unidec'][innerKey] = self.checkIfHasHTMLkeys(docData.massSpectrum['unidec'][innerKey])
                            if len(docData.massSpectrum['unidec'][innerKey]['tools']) == 0:
                                toolname, toolset = self.checkToolsUnidec(key=innerKey)
                                docData.massSpectrum['unidec'][innerKey]['tools']['name'] = toolname
                                docData.massSpectrum['unidec'][innerKey]['tools']['tools'] = toolset
                            self.itemsList.Append([key, 'UniDec', innerKey,
                                                   docData.massSpectrum['unidec'][innerKey]['title'],
                                                   docData.massSpectrum['unidec'][innerKey]['header'],
                                                   docData.massSpectrum['unidec'][innerKey]['footnote'],
                                                   docData.massSpectrum['unidec'][innerKey]['cmap'],
                                                   docData.massSpectrum['unidec'][innerKey]['page']['name'],
                                                   docData.massSpectrum['unidec'][innerKey]['tools']['name'],
                                                   docData.massSpectrum['unidec'][innerKey]['order'],
                                                   ])
                if hasattr(docData, "gotSmoothMS"):
                    if docData.gotSmoothMS == True:
                        docData.smoothMS = self.checkIfHasHTMLkeys(docData.smoothMS)
                        if docData.smoothMS['cmap'] == '': docData.smoothMS['cmap'] = self.config.lineColour_1D
                        if len(docData.smoothMS['tools']) == 0:
                            docData.smoothMS['tools']['name'] = '1D'
                            docData.smoothMS['tools']['tools'] = self.getToolSet(plotType='MS')
                        self.itemsList.Append([key, 'Processed MS', '',
                                               docData.smoothMS['title'],
                                               docData.smoothMS['header'],
                                               docData.smoothMS['footnote'],
                                               docData.smoothMS['cmap'],
                                               docData.smoothMS['page']['name'],
                                               docData.smoothMS['tools']['name'],
                                               docData.smoothMS['order'],
                                               ])
                    if 'unidec' in docData.smoothMS:
                        for innerKey in docData.smoothMS['unidec']:
                            if innerKey in ['Charge information']: continue
                            docData.smoothMS['unidec'][innerKey] = self.checkIfHasHTMLkeys(docData.smoothMS['unidec'][innerKey])
                            if len(docData.smoothMS['unidec'][innerKey]['tools']) == 0:
                                toolname, toolset = self.checkToolsUnidec(key=innerKey)
                                docData.smoothMS['unidec'][innerKey]['tools']['name'] = toolname
                                docData.smoothMS['unidec'][innerKey]['tools']['tools'] = toolset
                            self.itemsList.Append([key, 'UniDec, processed', innerKey,
                                                   docData.smoothMS['unidec'][innerKey]['title'],
                                                   docData.smoothMS['unidec'][innerKey]['header'],
                                                   docData.smoothMS['unidec'][innerKey]['footnote'],
                                                   docData.smoothMS['unidec'][innerKey]['cmap'],
                                                   docData.smoothMS['unidec'][innerKey]['page']['name'],
                                                   docData.smoothMS['unidec'][innerKey]['tools']['name'],
                                                   docData.smoothMS['unidec'][innerKey]['order'],
                                                   ])
                        
                if docData.got1RT == True:
                    docData.RT = self.checkIfHasHTMLkeys(docData.RT)
                    if docData.RT['cmap'] == '': docData.RT['cmap'] = self.config.lineColour_1D
                    if len(docData.RT['tools']) == 0:
                        docData.RT['tools']['name'] = '1D'
                        docData.RT['tools']['tools'] = self.getToolSet(plotType='RT')
                    self.itemsList.Append([key, 'RT', '',
                                           docData.RT['title'],
                                           docData.RT['header'],
                                           docData.RT['footnote'],
                                           docData.RT['cmap'],
                                           docData.RT['page']['name'],
                                           docData.RT['tools']['name'],
                                           docData.RT['order'],
                                           ])
                if docData.got1DT == True:
                    docData.DT = self.checkIfHasHTMLkeys(docData.DT)
                    if docData.DT['cmap'] == '': docData.DT['cmap'] = self.config.lineColour_1D
                    if len(docData.DT['tools']) == 0:
                        docData.DT['tools']['name'] = '1D'
                        docData.DT['tools']['tools'] = self.getToolSet(plotType='1D')
                    self.itemsList.Append([key, '1D', '',
                                           docData.DT['title'],
                                           docData.DT['header'],
                                           docData.DT['footnote'],
                                           docData.DT['cmap'],
                                           docData.DT['page']['name'],
                                           docData.DT['tools']['name'],
                                           docData.DT['order'],
                                           ])
                    
                if docData.got2DIMS == True:
                    docData.IMS2D = self.checkIfHasHTMLkeys(docData.IMS2D)
                    if len(docData.IMS2D['tools']) == 0:
                        docData.IMS2D['tools']['name'] = '2D'
                        docData.IMS2D['tools']['tools'] = self.getToolSet(plotType='2D')
                    self.itemsList.Append([key, '2D', '',
                                           docData.IMS2D['title'],
                                           docData.IMS2D['header'],
                                           docData.IMS2D['footnote'],
                                           docData.IMS2D['cmap'],
                                           docData.IMS2D['page']['name'],
                                           docData.IMS2D['tools']['name'],
                                           docData.IMS2D['order'],
                                           ])
                    
                if docData.got2Dprocess == True:
                    docData.IMS2Dprocess = self.checkIfHasHTMLkeys(docData.IMS2Dprocess)
                    if len(docData.IMS2Dprocess['tools']) == 0:
                        docData.IMS2Dprocess['tools']['name'] = '2D'
                        docData.IMS2Dprocess['tools']['tools'] = self.getToolSet(plotType='2D')
                    self.itemsList.Append([key, '2D, processed', '',
                                           docData.IMS2Dprocess['title'],
                                           docData.IMS2Dprocess['header'],
                                           docData.IMS2Dprocess['footnote'],
                                           docData.IMS2Dprocess['cmap'],
                                           docData.IMS2Dprocess['page']['name'],
                                           docData.IMS2Dprocess['tools']['name'],
                                           docData.IMS2Dprocess['order'],
                                           ])        
                    
                if docData.gotExtractedIons == True:
                    for innerKey in docData.IMS2Dions:
                        docData.IMS2Dions[innerKey] = self.checkIfHasHTMLkeys(docData.IMS2Dions[innerKey])
                        if len(docData.IMS2Dions[innerKey]['tools']) == 0:
                            docData.IMS2Dions[innerKey]['tools']['name'] = '2D'
                            docData.IMS2Dions[innerKey]['tools']['tools'] = self.getToolSet(plotType='2D')
                        self.itemsList.Append([key, '2D', innerKey,
                                               docData.IMS2Dions[innerKey]['title'],
                                               docData.IMS2Dions[innerKey]['header'],
                                               docData.IMS2Dions[innerKey]['footnote'],
                                               docData.IMS2Dions[innerKey]['cmap'],
                                               docData.IMS2Dions[innerKey]['page']['name'],
                                               docData.IMS2Dions[innerKey]['tools']['name'],
                                               docData.IMS2Dions[innerKey]['order'],
                                               ])        
                        
                if docData.gotMultipleMS == True:
                    for innerKey in docData.multipleMassSpectrum:
                        docData.multipleMassSpectrum[innerKey] = self.checkIfHasHTMLkeys(docData.multipleMassSpectrum[innerKey])
                        if docData.multipleMassSpectrum[innerKey]['cmap'] == '': docData.multipleMassSpectrum[innerKey]['cmap'] = self.config.lineColour_1D
                        if len(docData.multipleMassSpectrum[innerKey]['tools']) == 0:
                            docData.multipleMassSpectrum[innerKey]['tools']['name'] = 'MS'
                            docData.multipleMassSpectrum[innerKey]['tools']['tools'] = self.getToolSet(plotType='MS')
                        self.itemsList.Append([key, 'MS, multiple', innerKey,
                                               docData.multipleMassSpectrum[innerKey]['title'],
                                               docData.multipleMassSpectrum[innerKey]['header'],
                                               docData.multipleMassSpectrum[innerKey]['footnote'],
                                               docData.multipleMassSpectrum[innerKey]['cmap'],
                                               docData.multipleMassSpectrum[innerKey]['page']['name'],
                                               docData.multipleMassSpectrum[innerKey]['tools']['name'],
                                               docData.multipleMassSpectrum[innerKey]['order'],
                                               ])
                        if 'unidec' in docData.multipleMassSpectrum[innerKey]:
                            for innerInnerKey in docData.multipleMassSpectrum[innerKey]['unidec']:
                                if innerInnerKey in ['Charge information']: continue
                                docData.multipleMassSpectrum[innerKey]['unidec'][innerInnerKey] = self.checkIfHasHTMLkeys(docData.multipleMassSpectrum[innerKey]['unidec'][innerInnerKey])
                                innerInnerKeyLabel = "{} | {}".format(innerInnerKey, innerKey)
                                if len(docData.multipleMassSpectrum[innerKey]['unidec'][innerInnerKey]['tools']) == 0:
                                    toolname, toolset = self.checkToolsUnidec(key=innerInnerKey)
                                    docData.multipleMassSpectrum[innerKey]['unidec'][innerInnerKey]['tools']['name'] = toolname
                                    docData.multipleMassSpectrum[innerKey]['unidec'][innerInnerKey]['tools']['tools'] = toolset
                                self.itemsList.Append([key, 'UniDec, multiple', innerInnerKeyLabel,
                                                       docData.multipleMassSpectrum[innerKey]['unidec'][innerInnerKey]['title'],
                                                       docData.multipleMassSpectrum[innerKey]['unidec'][innerInnerKey]['header'],
                                                       docData.multipleMassSpectrum[innerKey]['unidec'][innerInnerKey]['footnote'],
                                                       docData.multipleMassSpectrum[innerKey]['unidec'][innerInnerKey]['cmap'],
                                                       docData.multipleMassSpectrum[innerKey]['unidec'][innerInnerKey]['page']['name'],
                                                       docData.multipleMassSpectrum[innerKey]['unidec'][innerInnerKey]['tools']['name'],
                                                       docData.multipleMassSpectrum[innerKey]['unidec'][innerInnerKey]['order'],
                                                       ])
                        
                if hasattr(docData, 'gotMultipleRT'):
                    for innerKey in docData.multipleRT:
                        docData.multipleRT[innerKey] = self.checkIfHasHTMLkeys(docData.multipleRT[innerKey])
                        if docData.multipleRT[innerKey]['cmap'] == '': docData.multipleRT[innerKey]['cmap'] = self.config.lineColour_1D
                        if len(docData.multipleRT[innerKey]['tools']) == 0:
                            docData.multipleRT[innerKey]['tools']['name'] = '1D'
                            docData.multipleRT[innerKey]['tools']['tools'] = self.getToolSet(plotType='1D')
                        self.itemsList.Append([key, 'RT, multiple', innerKey,
                                               docData.multipleRT[innerKey]['title'],
                                               docData.multipleRT[innerKey]['header'],
                                               docData.multipleRT[innerKey]['footnote'],
                                               docData.multipleRT[innerKey]['cmap'],
                                               docData.multipleRT[innerKey]['page']['name'],
                                               docData.multipleRT[innerKey]['tools']['name'],
                                               docData.multipleRT[innerKey]['order'],
                                               ])      
                        
                if hasattr(docData, 'gotMultipleDT'):
                    for innerKey in docData.multipleDT:
                        docData.multipleDT[innerKey] = self.checkIfHasHTMLkeys(docData.multipleDT[innerKey])
                        if docData.multipleDT[innerKey]['cmap'] == '': docData.multipleDT[innerKey]['cmap'] = self.config.lineColour_1D
                        if len(docData.multipleDT[innerKey]['tools']) == 0:
                            docData.multipleDT[innerKey]['tools']['name'] = '1D'
                            docData.multipleDT[innerKey]['tools']['tools'] = self.getToolSet(plotType='1D')
                        self.itemsList.Append([key, '1D, multiple', innerKey,
                                               docData.multipleDT[innerKey]['title'],
                                               docData.multipleDT[innerKey]['header'],
                                               docData.multipleDT[innerKey]['footnote'],
                                               docData.multipleDT[innerKey]['cmap'],
                                               docData.multipleDT[innerKey]['page']['name'],
                                               docData.multipleDT[innerKey]['tools']['name'],
                                               docData.multipleDT[innerKey]['order'],
                                               ])      
                        
                if docData.gotExtractedDriftTimes == True:
                    for innerKey in docData.IMS1DdriftTimes:
                        docData.IMS1DdriftTimes[innerKey] = self.checkIfHasHTMLkeys(docData.IMS1DdriftTimes[innerKey])
                        if docData.IMS1DdriftTimes[innerKey]['cmap'] == '': docData.IMS1DdriftTimes[innerKey]['cmap'] = self.config.lineColour_1D
                        if len(docData.IMS1DdriftTimes[innerKey]['tools']) == 0:
                            docData.IMS1DdriftTimes[innerKey]['tools']['name'] = '1D'
                            docData.IMS1DdriftTimes[innerKey]['tools']['tools'] = self.getToolSet(plotType='1D')
                        if docData.dataType == 'Type: MANUAL':
                            tableKey = '1D'
                        else:
                            tableKey = 'DT-IMS'
                        self.itemsList.Append([key, tableKey, innerKey,
                                               docData.IMS1DdriftTimes[innerKey]['title'],
                                               docData.IMS1DdriftTimes[innerKey]['header'],
                                               docData.IMS1DdriftTimes[innerKey]['footnote'],
                                               docData.IMS1DdriftTimes[innerKey]['cmap'],
                                               docData.IMS1DdriftTimes[innerKey]['page']['name'],
                                               docData.IMS1DdriftTimes[innerKey]['tools']['name'],
                                               docData.IMS1DdriftTimes[innerKey]['order'],
                                               ])
                        
                if docData.gotCombinedExtractedIonsRT == True:
                    for innerKey in docData.IMSRTCombIons:
                        docData.IMSRTCombIons[innerKey] = self.checkIfHasHTMLkeys(docData.IMSRTCombIons[innerKey])
                        if docData.IMSRTCombIons[innerKey]['cmap'] == '': docData.IMSRTCombIons[innerKey]['cmap'] = self.config.lineColour_1D
                        if len(docData.IMSRTCombIons[innerKey]['tools']) == 0:
                            docData.IMSRTCombIons[innerKey]['tools']['name'] = 'RT'
                            docData.IMSRTCombIons[innerKey]['tools']['tools'] = self.getToolSet(plotType='RT')
                        self.itemsList.Append([key, 'RT, combined', innerKey,
                                               docData.IMSRTCombIons[innerKey]['title'],
                                               docData.IMSRTCombIons[innerKey]['header'],
                                               docData.IMSRTCombIons[innerKey]['footnote'],
                                               docData.IMSRTCombIons[innerKey]['cmap'],
                                               docData.IMSRTCombIons[innerKey]['page']['name'],
                                               docData.IMSRTCombIons[innerKey]['tools']['name'],
                                               docData.IMSRTCombIons[innerKey]['order'],
                                               ])
                        
                if docData.gotCombinedExtractedIons == True:
                    for innerKey in docData.IMS2DCombIons:
                        docData.IMS2DCombIons[innerKey] = self.checkIfHasHTMLkeys(docData.IMS2DCombIons[innerKey])
                        if len(docData.IMS2DCombIons[innerKey]['tools']) == 0:
                            docData.IMS2DCombIons[innerKey]['tools']['name'] = '2D'
                            docData.IMS2DCombIons[innerKey]['tools']['tools'] = self.getToolSet(plotType='2D')
                        self.itemsList.Append([key, '2D, combined', innerKey,
                                               docData.IMS2DCombIons[innerKey]['title'],
                                               docData.IMS2DCombIons[innerKey]['header'],
                                               docData.IMS2DCombIons[innerKey]['footnote'],
                                               docData.IMS2DCombIons[innerKey]['cmap'],
                                               docData.IMS2DCombIons[innerKey]['page']['name'],
                                               docData.IMS2DCombIons[innerKey]['tools']['name'],
                                               docData.IMS2DCombIons[innerKey]['order'],
                                               ])   
                        
                if docData.got2DprocessIons == True:
                    for innerKey in docData.IMS2DionsProcess:
                        docData.IMS2DionsProcess[innerKey] = self.checkIfHasHTMLkeys(docData.IMS2DionsProcess[innerKey])
                        if len(docData.IMS2DionsProcess[innerKey]['tools']) == 0:
                            docData.IMS2DionsProcess[innerKey]['tools']['name'] = '2D'
                            docData.IMS2DionsProcess[innerKey]['tools']['tools'] = self.getToolSet(plotType='2D')
                        self.itemsList.Append([key, '2D, processed', innerKey,
                                               docData.IMS2DionsProcess[innerKey]['title'],
                                               docData.IMS2DionsProcess[innerKey]['header'],
                                               docData.IMS2DionsProcess[innerKey]['footnote'],
                                               docData.IMS2DionsProcess[innerKey]['cmap'],
                                               docData.IMS2DionsProcess[innerKey]['page']['name'],
                                               docData.IMS2DionsProcess[innerKey]['tools']['name'],
                                               docData.IMS2DionsProcess[innerKey]['order'],
                                               ])   
                        
                # Overlay data
                if docData.gotOverlay == True:
                    for innerKey in docData.IMS2DoverlayData:
                        docData.IMS2DoverlayData[innerKey] = self.checkIfHasHTMLkeys(docData.IMS2DoverlayData[innerKey])
                        if len(docData.IMS2DoverlayData[innerKey]['tools']) == 0:
                            preset, toolSet = self.getToolSet(plotType=None, subType=innerKey)
                            docData.IMS2DoverlayData[innerKey]['tools']['name'] = preset
                            docData.IMS2DoverlayData[innerKey]['tools']['tools'] = toolSet
                        # generate cmap label
                        overlayMethod = re.split('-|,|:|__', innerKey)
                        if overlayMethod[0] in ['Mask', 'Transparent']:
                            cmap_label = "%s/%s" % (docData.IMS2DoverlayData[innerKey]['cmap1'],
                                                    docData.IMS2DoverlayData[innerKey]['cmap2'])
                        else:
                            cmap_label = docData.IMS2DoverlayData[innerKey].get('cmap',"")
                        self.itemsList.Append([key, 'Overlay', innerKey,
                                               docData.IMS2DoverlayData[innerKey]['title'],
                                               docData.IMS2DoverlayData[innerKey]['header'],
                                               docData.IMS2DoverlayData[innerKey]['footnote'],
                                               cmap_label,
                                               docData.IMS2DoverlayData[innerKey].get('page',"")['name'],
                                               docData.IMS2DoverlayData[innerKey]['tools']['name'],
                                               docData.IMS2DoverlayData[innerKey].get('order',""),
                                               ])

                if docData.gotStatsData == True:
                    for innerKey in docData.IMS2DstatsData:
                        docData.IMS2DstatsData[innerKey] = self.checkIfHasHTMLkeys(docData.IMS2DstatsData[innerKey])
                        if len(docData.IMS2DstatsData[innerKey]['tools']) == 0:
                            preset, toolSet = self.getToolSet(plotType=None, subType=innerKey)
                            docData.IMS2DstatsData[innerKey]['tools']['name'] = preset
                            docData.IMS2DstatsData[innerKey]['tools']['tools'] = toolSet
                        self.itemsList.Append([key, 'Statistical', innerKey,
                                               docData.IMS2DstatsData[innerKey]['title'],
                                               docData.IMS2DstatsData[innerKey]['header'],
                                               docData.IMS2DstatsData[innerKey]['footnote'],
                                               docData.IMS2DstatsData[innerKey]['cmap'],
                                               docData.IMS2DstatsData[innerKey]['page']['name'],
                                               docData.IMS2DstatsData[innerKey]['tools']['name'],
                                               docData.IMS2DstatsData[innerKey]['order'],
                                               ])   
                        
            self.colorTable(evt=None)
            self.onAddPageChoices(evt=None)
            self.onAddToolsChoices(evt=None)
        else:
            msg = 'Document list is empty'
            self.view.SetStatusText(msg, 3)
            self.onAddPageChoices(evt=None)
    
    def onAddPageChoices(self, evt=None):
        """
        Repopulate combo boxes
        """
        self.pageLayoutSelect_htmlView.Clear()
        self.pageLayoutSelect_propView.Clear()
        self.pageLayoutSelect_toolbar.Clear()
        
        # Remove any key without a proper name
        try:
            del self.config.pageDict[u'']
        except KeyError: pass 
        
        for key in self.config.pageDict:
            self.pageLayoutSelect_htmlView.Append(key)
            self.pageLayoutSelect_propView.Append(key)
            self.pageLayoutSelect_toolbar.Append(key)
        
        # Setup the Layout window
        self.pageLayoutSelect_propView.SetStringSelection('None')
        self.pageLayoutSelect_toolbar.SetStringSelection('None')
        self.onSelectPageProperties(evt=None)
    
    def onAddToolsChoices(self, evt=None):
        self.plotTypeToolsSelect_htmlView.Clear()
        self.plotTypeToolsSelect_propView.Clear()
        self.plotTypeToolsSelect_toolbar.Clear()
        
        for key in self.config.interactiveToolsOnOff:
            self.plotTypeToolsSelect_htmlView.Append(key)
            self.plotTypeToolsSelect_propView.Append(key)
            self.plotTypeToolsSelect_toolbar.Append(key)
            
        self.plotTypeToolsSelect_propView.SetStringSelection('1D')
    
    def colorTable(self, evt):
        
        rows = self.itemsList.GetItemCount()
        if rows > 0:
            for row in range(rows):
                if row % 2: self.itemsList.SetItemBackgroundColour(row, wx.WHITE)
                else:  self.itemsList.SetItemBackgroundColour(row, (236, 236, 236))
                    
    def onItemSelected(self, evt):
        
        # Disable all elements when nothing is selected
        itemList = [self.itemName_value, self.itemHeader_value, self.itemFootnote_value,
                    self.order_value, self.pageLayoutSelect_htmlView, 
                    self.plotTypeToolsSelect_htmlView, self.colorbarCheck
                    ]
        
        for item in itemList:
            item.Enable()
        
        # When selecting new item, it automatically updates each field in the GUI,
        # however, as it does that, it also updates the data dictionary. By enabling
        # loading mode, only the GUI is updated and nothing else.
        self.loading = True
        self.currentItem = evt.m_itemIndex
        name = self.itemsList.GetItem(self.currentItem,self.config.interactiveColNames['document']).GetText()
        key = self.itemsList.GetItem(self.currentItem,self.config.interactiveColNames['type']).GetText()
        innerKey = self.itemsList.GetItem(self.currentItem,self.config.interactiveColNames['file']).GetText()
        color = self.itemsList.GetItem(self.currentItem,self.config.interactiveColNames['color']).GetText()
        order = self.itemsList.GetItem(self.currentItem,self.config.interactiveColNames['order']).GetText()
        if color == "": color = "(0, 0, 0)"

        # combine labels
        self.document_value.SetLabel(name.replace("__"," ").replace(".raw", ""))
        self.type_value.SetLabel(key.replace("__"," ").replace(".raw", ""))
        self.details_value.SetLabel(innerKey.replace("__"," ").replace(".raw", ""))
  
        # Determine which document was selected
        document = self.documentsDict[name]
        if key == 'MS' and innerKey == '': docData = document.massSpectrum
        if key == 'Processed MS' and innerKey == '': docData = document.smoothMS
        if key == 'RT' and innerKey == '': docData = document.RT
        if key == 'RT, multiple' and innerKey != '': docData = document.multipleRT[innerKey]
        if key == '1D' and innerKey == '': docData = document.DT
        if key == '1D, multiple' and innerKey != '': docData = document.multipleDT[innerKey]
        if key == '2D' and innerKey == '': docData = document.IMS2D
        if key == '2D, processed' and innerKey == '': docData = document.IMS2Dprocess
        if key == 'MS, multiple' and innerKey != '': docData = document.multipleMassSpectrum[innerKey]
        if key == '2D' and innerKey != '': docData = document.IMS2Dions[innerKey]
        if key == 'DT-IMS' and innerKey != '': docData = document.IMS1DdriftTimes[innerKey]
        if key == '1D' and innerKey != '': docData = document.IMS1DdriftTimes[innerKey]
        if key == 'RT, combined' and innerKey != '': docData = document.IMSRTCombIons[innerKey]
        if key == '2D, combined' and innerKey != '': docData = document.IMS2DCombIons[innerKey]
        if key == '2D, processed' and innerKey != '': docData = document.IMS2DionsProcess[innerKey]
        if key == 'Overlay' and innerKey != '': 
            docData = document.IMS2DoverlayData[innerKey]
            overlayMethod = re.split('-|,|:|__', innerKey)
        if key == 'Statistical' and innerKey != '': docData = document.IMS2DstatsData[innerKey]
        if key == 'UniDec' and innerKey != '': docData = document.massSpectrum['unidec'][innerKey]
        if key == 'UniDec, multiple' and innerKey != '':
            unidecMethod = re.split(' \| ', innerKey)[0]
            innerKey = re.split(' \| ', innerKey)[1]
            docData = document.multipleMassSpectrum[innerKey]['unidec'][unidecMethod]
            
        # Retrieve information
        title = docData['title']
        header = docData['header']
        footnote = docData['footnote']
#         order = docData['order']
        page = docData['page']['name']
        tool = docData['tools']['name']
        colorbar = docData['colorbar']
        
        interactive_params = docData.get('interactive_params', {})
        colormap_1 = docData.get('cmap1', color)
        colormap_2 = docData.get('cmap2', color)

        # Update item editor
        try:
            self.itemName_value.SetValue(title)
            self.itemHeader_value.SetValue(header)
            self.itemFootnote_value.SetValue(footnote)
            self.order_value.SetValue(order)
            self.pageLayoutSelect_htmlView.SetStringSelection(page)
            self.plotTypeToolsSelect_htmlView.SetStringSelection(tool)
            self.colorbarCheck.SetValue(colorbar)
            self.grid_label_check.SetValue(interactive_params.get("title_label", False))
            self.grid_xpos_value.SetValue(interactive_params.get("grid_xpos", self.config.interactive_grid_xpos))
            self.grid_ypos_value.SetValue(interactive_params.get("grid_ypos", self.config.interactive_grid_xpos))
            self.waterfall_increment_value.SetValue(interactive_params.get("waterfall_increment", self.config.interactive_waterfall_increment))
            self.showAnnotationsCheck.SetValue(interactive_params.get("show_annotations", self.config.interactive_ms_annotations))
            self.linearizeCheck.SetValue(interactive_params.get("linearize_spectra", self.config.interactive_ms_linearize))
            self.binSize_value.SetValue(interactive_params.get("bin_size", self.config.interactive_ms_binSize))
        except:
            self.loading = False
        
        if (key in ["RT", 'RT, multiple', "1D", '1D, multiple', "RT, combined"]):
            self.colorBtn.SetBackgroundColour(convertRGB1to255((eval(color))))
            self.html_plot1D_hoverLinkX.SetValue(interactive_params['line_linkXaxis'])
            self.html_plot1D_line_alpha.SetValue(interactive_params['line_alpha'])
            self.html_plot1D_line_width.SetValue(interactive_params['line_width'])
            self.html_plot1D_line_style.SetStringSelection(interactive_params['line_style'])
            enableList = [self.colorBtn, self.pageLayoutSelect_htmlView, 
                          self.plotTypeToolsSelect_htmlView,
                          self.html_plot1D_hoverLinkX, self.html_plot1D_line_alpha,
                          self.html_plot1D_line_width, self.html_plot1D_line_style]
            disableList = [self.comboCmapSelect, self.layout_combo, self.colorbarCheck, 
                           self.html_overlay_colormap_1, self.html_overlay_colormap_2,
                           self.html_overlay_layout, self.html_overlay_linkXY,
                           self.html_overlay_legend, self.grid_label_check, 
                           self.grid_label_size_value, self.grid_label_weight,
                           self.interactive_grid_colorBtn, self.grid_ypos_value, 
                           self.grid_xpos_value,
                          self.waterfall_increment_value, self.binSize_value,
                          self.showAnnotationsCheck, self.linearizeCheck]

        elif (key in ["MS", 'MS, multiple', 'DT-IMS', "Processed MS"] or
              key in ["UniDec","UniDec, multiple", "UniDec, processed"] and innerKey in ["Processed", "MW distribution"]):
            self.colorBtn.SetBackgroundColour(convertRGB1to255((eval(color))))
            self.html_plot1D_hoverLinkX.SetValue(interactive_params['line_linkXaxis'])
            self.html_plot1D_line_alpha.SetValue(interactive_params['line_alpha'])
            self.html_plot1D_line_width.SetValue(interactive_params['line_width'])
            self.html_plot1D_line_style.SetStringSelection(interactive_params['line_style'])
            enableList = [self.colorBtn, self.pageLayoutSelect_htmlView, 
                          self.plotTypeToolsSelect_htmlView,
                          self.html_plot1D_hoverLinkX, self.html_plot1D_line_alpha,
                          self.html_plot1D_line_width, self.html_plot1D_line_style,
                          self.binSize_value,
                          self.showAnnotationsCheck, self.linearizeCheck]
            disableList = [self.comboCmapSelect, self.layout_combo, self.colorbarCheck, 
                           self.html_overlay_colormap_1, self.html_overlay_colormap_2,
                           self.html_overlay_layout, self.html_overlay_linkXY,
                           self.html_overlay_legend, self.grid_label_check, 
                           self.grid_label_size_value, self.grid_label_weight,
                           self.interactive_grid_colorBtn, self.grid_ypos_value, 
                           self.grid_xpos_value,  self.waterfall_increment_value]
        elif key == "Overlay" and overlayMethod[0] in ["Waterfall (Raw)", "Waterfall (Processed)", "Waterfall (Fitted)",
                                                       "Waterfall (Deconvoluted MW)", "Waterfall (Charge states)"]:
            enableList = [self.pageLayoutSelect_htmlView, self.plotTypeToolsSelect_htmlView,
                          self.html_plot1D_hoverLinkX, self.html_plot1D_line_alpha,
                          self.html_plot1D_line_width, self.html_plot1D_line_style,
                          self.waterfall_increment_value, self.binSize_value,
                          self.showAnnotationsCheck, self.linearizeCheck]
            disableList = [self.comboCmapSelect, self.layout_combo, self.colorbarCheck, 
                           self.html_overlay_colormap_1, self.html_overlay_colormap_2,
                           self.html_overlay_layout, self.html_overlay_linkXY,
                           self.html_overlay_legend, self.grid_label_check, 
                           self.grid_label_size_value, self.grid_label_weight,
                           self.interactive_grid_colorBtn, self.grid_ypos_value, 
                           self.grid_xpos_value, self.colorBtn]
        elif (key in ["2D", "Statistical", "2D, combined", "2D, processed"] or 
              key == 'Overlay' and overlayMethod[0] in ['RMSD','RMSF'] or 
              key in ["UniDec", "UniDec, multiple", "UniDec, processed"] and innerKey in ['MW vs Charge', 'm/z vs Charge'] or
              key == "UniDec, multiple" and unidecMethod in ['MW vs Charge', 'm/z vs Charge']):
            self.comboCmapSelect.SetValue(color)
            enableList = [self.comboCmapSelect, self.pageLayoutSelect_htmlView, 
                          self.colorbarCheck, self.plotTypeToolsSelect_htmlView]
            disableList = [self.colorBtn, self.layout_combo, 
                           self.html_overlay_colormap_1, self.html_overlay_colormap_2,
                           self.html_overlay_layout, self.html_overlay_linkXY,
                           self.html_overlay_legend, self.html_plot1D_line_alpha,
                           self.html_plot1D_line_width, self.html_plot1D_line_style, 
                           self.grid_label_check, self.grid_label_size_value, 
                           self.grid_label_weight, self.interactive_grid_colorBtn, self.grid_ypos_value, 
                           self.grid_xpos_value,
                          self.waterfall_increment_value, self.binSize_value,
                          self.showAnnotationsCheck, self.linearizeCheck]
            
        elif key == 'Overlay' and (overlayMethod[0] in ['Mask','Transparent']):
            self.html_overlay_colormap_1.SetStringSelection(colormap_1)
            self.html_overlay_colormap_2.SetStringSelection(colormap_2)
            self.html_overlay_layout.SetStringSelection(interactive_params['overlay_layout'])
            self.html_overlay_linkXY.SetValue(interactive_params['overlay_linkXY'])
            enableList = [self.layout_combo, self.colorbarCheck, 
                          self.plotTypeToolsSelect_htmlView,
                          self.html_overlay_colormap_1, self.html_overlay_colormap_2,
                          self.html_overlay_layout, self.html_overlay_linkXY]
            disableList = [self.comboCmapSelect, self.colorBtn, 
                           self.pageLayoutSelect_htmlView, self.html_plot1D_hoverLinkX,
                           self.html_plot1D_line_alpha, self.html_plot1D_line_width,
                           self.html_overlay_legend, self.html_plot1D_line_style, self.grid_label_check, 
                           self.grid_label_size_value, self.grid_label_weight,
                           self.interactive_grid_colorBtn, self.grid_ypos_value, 
                           self.grid_xpos_value,
                          self.waterfall_increment_value, self.binSize_value,
                          self.showAnnotationsCheck, self.linearizeCheck]
        elif key == 'Overlay' and overlayMethod[0] in ['Grid (2', 'Grid (n x n)']:
            enableList = [self.grid_label_check, self.grid_label_size_value, 
                          self.grid_label_weight,self.interactive_grid_colorBtn,
                          self.pageLayoutSelect_htmlView, self.grid_ypos_value, 
                           self.grid_xpos_value]
            disableList = [self.comboCmapSelect, self.colorBtn, 
                           self.html_overlay_layout, self.html_plot1D_hoverLinkX,
                           self.html_plot1D_line_alpha, self.html_plot1D_line_width,
                           self.html_overlay_legend, self.html_plot1D_line_style,
                           self.colorbarCheck,
                          self.waterfall_increment_value, self.binSize_value,
                          self.showAnnotationsCheck, self.linearizeCheck]
            
        elif (key == 'Overlay' and (overlayMethod[0] in ['1D','RT']) or 
              key in ["UniDec", "UniDec, multiple", "UniDec, processed"] and innerKey in ['m/z with isolated species', 'Fitted']):
            self.html_plot1D_hoverLinkX.SetValue(interactive_params['line_linkXaxis'])
            self.html_plot1D_line_alpha.SetValue(interactive_params['line_alpha'])
            self.html_plot1D_line_width.SetValue(interactive_params['line_width'])
            self.html_plot1D_line_style.SetStringSelection(interactive_params['line_style'])
            self.html_overlay_legend.SetValue(interactive_params['legend'])
            enableList = [self.layout_combo, self.plotTypeToolsSelect_htmlView,
                          self.html_plot1D_hoverLinkX, self.html_plot1D_line_alpha,
                          self.html_plot1D_line_width, self.html_overlay_legend,
                          self.html_plot1D_line_style
                          ]
            disableList = [self.comboCmapSelect, self.colorBtn, 
                           self.pageLayoutSelect_htmlView, self.colorbarCheck, 
                           self.html_overlay_colormap_1, self.html_overlay_colormap_2,
                           self.html_overlay_layout, self.html_overlay_linkXY,
                           self.colorbarCheck, self.grid_label_check, 
                           self.grid_label_size_value, self.grid_label_weight,
                           self.interactive_grid_colorBtn, self.grid_ypos_value, 
                           self.grid_xpos_value,
                          self.waterfall_increment_value, self.binSize_value,
                          self.showAnnotationsCheck, self.linearizeCheck
                           ]
        else:
            enableList = [self.comboCmapSelect, self.colorBtn,
                          self.pageLayoutSelect_htmlView, 
                          self.plotTypeToolsSelect_htmlView]
            disableList = [self.layout_combo, self.colorbarCheck, 
                           self.html_overlay_colormap_1, self.html_overlay_colormap_2,
                           self.html_overlay_layout, self.html_overlay_linkXY, self.grid_ypos_value, 
                           self.grid_xpos_value,
                          self.waterfall_increment_value, self.binSize_value,
                          self.showAnnotationsCheck, self.linearizeCheck]
            
        for item in enableList: item.Enable()
        for item in disableList: item.Disable()    
    
        self.loading = False
                
    def getItemData(self, name, key, innerKey):
        # Determine which document was selected
        document = self.documentsDict[name]
        if key == 'MS' and innerKey == '': docData = document.massSpectrum
        if key == 'Processed MS' and innerKey == '': docData = document.smoothMS
        if key == 'RT' and innerKey == '': docData = document.RT
        if key == '1D' and innerKey == '': docData = document.DT
        if key == '2D' and innerKey == '': docData = document.IMS2D
        if key == '2D, processed' and innerKey == '': docData = document.IMS2Dprocess
        if key == 'MS, multiple' and innerKey != '': docData = document.multipleMassSpectrum[innerKey]
        if key == '2D' and innerKey != '': docData = document.IMS2Dions[innerKey]
        if key == 'DT-IMS' and innerKey != '': docData = document.IMS1DdriftTimes[innerKey]
        if key == '1D' and innerKey != '': docData = document.IMS1DdriftTimes[innerKey]
        if key == '1D, multiple' and innerKey != '': docData = document.multipleDT[innerKey]
        if key == 'RT, combined' and innerKey != '': docData = document.IMSRTCombIons[innerKey]
        if key == 'RT, multiple' and innerKey != '': docData = document.multipleRT[innerKey]
        if key == '2D, combined' and innerKey != '': docData = document.IMS2DCombIons[innerKey]
        if key == '2D, processed' and innerKey != '': docData = document.IMS2DionsProcess[innerKey]
        if key == 'Overlay' and innerKey != '': docData = document.IMS2DoverlayData[innerKey]
        if key == 'Statistical' and innerKey != '': docData = document.IMS2DstatsData[innerKey]
        if key == 'UniDec' and innerKey != '': docData = document.massSpectrum['unidec'][innerKey]
        if key == 'UniDec, processed' and innerKey != '': docData = document.smoothMS['unidec'][innerKey]
        if key == 'UniDec, multiple' and innerKey != '':
            unidecMethod = re.split(' \| ', innerKey)[0]
            innerKey = re.split(' \| ', innerKey)[1]
            docData = document.multipleMassSpectrum[innerKey]['unidec'][unidecMethod]
        
        return docData
          
    def onChangePageForItem(self, evt):
        """ This function changes the output page for selected item """
        if self.currentItem == None: 
            msg = 'Please select item first'
            self.view.SetStatusText(msg, 3)
            return     
        
        # Get current page selection
        page = self.pageLayoutSelect_htmlView.GetStringSelection()
        self.itemsList.SetStringItem(index=self.currentItem, 
                                     col=self.config.interactiveColNames['page'], 
                                     label=str(page))
        self._preAnnotateItems()
        self.onAnnotateItems(evt=None)
        
    def onChangePageForSelectedItems(self, evt):
        """ This function changes the output page for selected items (batch)"""
        rows = self.itemsList.GetItemCount()
        page = self.pageLayoutSelect_toolbar.GetStringSelection()
        for row in range(rows):
            if self.itemsList.IsChecked(index=row):
                self.currentItem = row
                self.itemsList.SetStringItem(index=row, 
                                             col=self.config.interactiveColNames['page'], 
                                             label=page)
                self._preAnnotateItems()
                self.onAnnotateItems(evt=None, itemID=row)
                       
    def onChangeToolsForItem(self, evt):
        """ This function changes the toolset for selected item """
        if self.currentItem == None: 
            msg = 'Please select item first'
            self.view.SetStatusText(msg, 3)
            return     
        
        # Get current page selection
        tool = self.plotTypeToolsSelect_htmlView.GetStringSelection()
        self.itemsList.SetStringItem(index=self.currentItem, 
                                     col=self.config.interactiveColNames['tools'], 
                                     label=str(tool))
        self._preAnnotateItems()
        self.onAnnotateItems(evt=None)
        
    def onChangeToolsForSelectedItems(self, evt):
        """ This function changes the toolset for selected items (batch)"""
        rows = self.itemsList.GetItemCount()
        tool = self.plotTypeToolsSelect_toolbar.GetStringSelection()
        
        if tool in ['', ' ', '   '] or tool not in self.config.interactiveToolsOnOff.keys():
            msg = 'Could not find toolset with that name.'
            print(msg)
            self.presenter.onThreading(None, (msg, 4), action='updateStatusbar')
            return
        
        for row in range(rows):
            if self.itemsList.IsChecked(index=row):
                self.currentItem = row
                self.itemsList.SetStringItem(index=row, 
                                             col=self.config.interactiveColNames['tools'], 
                                             label=str(tool))
                self._preAnnotateItems()
                self.onAnnotateItems(evt=None)

    def onChangeColormapForSelectedItems(self, evt):
        """ This function changes colormap for selected items (batch)"""
        rows = self.itemsList.GetItemCount()
        colormap = self.colormapSelect_toolbar.GetStringSelection()
        
        for row in range(rows):
            if self.itemsList.IsChecked(index=row):
                item_type = self.itemsList.GetItem(row, self.config.interactiveColNames['type']).GetText()
                if item_type in ['2D', '2D, processed', '2D, combined', 'Overlay', 'Statistical']:
                    self.currentItem = row
                    self.itemsList.SetStringItem(index=row, 
                                                 col=self.config.interactiveColNames['colormap'], 
                                                 label=str(colormap))
                    self._preAnnotateItems()
                    self.onAnnotateItems(evt=None, itemID=row)
                 
    def onChangeColour(self, evt):
        
        if self.currentItem == None and evt.GetId() == ID_changeColorInteractive:
            msg = 'Please select item first'
            self.view.SetStatusText(msg, 3)
            return        
        if (evt.GetId() == ID_changeColorInteractive 
            or evt.GetId() == ID_changeColorNotationInteractive 
            or evt.GetId() == ID_changeColorBackgroundNotationInteractive
            or evt.GetId() == ID_changeColorGridLabelInteractive):
            # Show dialog and get new colour
            dlg = wx.ColourDialog(self)
            dlg.GetColourData().SetChooseFull(True)
            if dlg.ShowModal() == wx.ID_OK:
                data = dlg.GetColourData()
                newColour = list(data.GetColour().Get())
                newColour255 = tuple([round((np.float(newColour[0])/255),2),
                                      round((np.float(newColour[1])/255),2),
                                      round((np.float(newColour[2])/255),2)])
                if evt.GetId() == ID_changeColorInteractive:
                    self.colorBtn.SetBackgroundColour(newColour)
                    self.itemsList.SetStringItem(index=self.currentItem, 
                                                 col=self.config.interactiveColNames['color'], 
                                                 label=str(newColour255))
                elif evt.GetId() == ID_changeColorNotationInteractive:
                    self.interactive_annotation_colorBtn.SetBackgroundColour(newColour)
                    self.config.interactive_annotation_color = newColour255
                elif evt.GetId() == ID_changeColorBackgroundNotationInteractive:
                    self.interactive_annotation_colorBackgroundBtn.SetBackgroundColour(newColour)
                    self.config.interactive_annotation_background_color = newColour255
                elif evt.GetId() == ID_changeColorGridLabelInteractive:
                    self.interactive_grid_colorBtn.SetBackgroundColour(newColour)
                    self.config.interactive_grid_label_color = newColour255
                    
                self.onAnnotateItems(evt=None)
                dlg.Destroy()
            else:
                return
        elif evt.GetId() == ID_changeColormapInteractive:
            colormap = self.comboCmapSelect.GetValue()
            self.itemsList.SetStringItem(index=self.currentItem, 
                                         col=6, label=str(colormap))
            self.onAnnotateItems(evt=None)
        
    def _preAnnotateItems(self, itemID=None):
        if itemID != None:
            self.currentItem = itemID
            
        color = self.itemsList.GetItem(self.currentItem,self.config.interactiveColNames['color']).GetText()
        if color != "" and "(" not in color and "[" not in color and color in self.config.cmaps2:
            self.comboCmapSelect.SetStringSelection(color)
        
        title = self.itemsList.GetItem(self.currentItem,self.config.interactiveColNames['title']).GetText()
        self.itemName_value.SetValue(title)
        
        header = self.itemsList.GetItem(self.currentItem,self.config.interactiveColNames['header']).GetText() 
        self.itemHeader_value.SetValue(header)
        
        footnote = self.itemsList.GetItem(self.currentItem,self.config.interactiveColNames['footnote']).GetText()
        self.itemFootnote_value.SetValue(footnote)
        
        orderNum = self.itemsList.GetItem(self.currentItem,self.config.interactiveColNames['order']).GetText()
        self.order_value.SetValue(orderNum)
        
    def onAnnotateItems(self, evt=None, itemID=None):
        
        # If we only updating dictionary
        if itemID != None:
            self.currentItem = itemID
        
        # Check if is empty
        if self.currentItem == None: return
        name = self.itemsList.GetItem(self.currentItem,self.config.interactiveColNames['document']).GetText()
        key = self.itemsList.GetItem(self.currentItem,self.config.interactiveColNames['type']).GetText()
        innerKey = self.itemsList.GetItem(self.currentItem,self.config.interactiveColNames['file']).GetText()
        color = self.itemsList.GetItem(self.currentItem,self.config.interactiveColNames['color']).GetText()
        page = self.itemsList.GetItem(self.currentItem,self.config.interactiveColNames['page']).GetText() 
        tool = self.itemsList.GetItem(self.currentItem,self.config.interactiveColNames['tools']).GetText()
#         title = self.itemsList.GetItem(self.currentItem,self.config.interactiveColNames['title']).GetText()
#         header = self.itemsList.GetItem(self.currentItem,self.config.interactiveColNames['header']).GetText() 
#         footnote = self.itemsList.GetItem(self.currentItem,self.config.interactiveColNames['footnote']).GetText()
#         orderNum = self.itemsList.GetItem(self.currentItem,self.config.interactiveColNames['order']).GetText() 
        
        # Get data
        pageData = self.config.pageDict[page]
        tools = self.getToolSet(preset=tool)
        toolSet = {'name':tool, 'tools':tools} # dictionary object
        
        if any(key in method for method in ["MS", "RT", "1D", "RT, combined", 
                                            'MS, multiple', '1D, multiple', 
                                            'RT, multiple']):
            color = (eval(color))
                
        title = self.itemName_value.GetValue()
        header = self.itemHeader_value.GetValue()
        footnote = self.itemFootnote_value.GetValue()
        orderNum = self.order_value.GetValue()
        colorbar = self.colorbarCheck.GetValue()
        
        interactive_params = {'line_width':self.html_plot1D_line_width.GetValue(),
                              'line_alpha':self.html_plot1D_line_alpha.GetValue(),
                              'line_style':self.html_plot1D_line_style.GetStringSelection(),
                              'line_linkXaxis':self.html_plot1D_hoverLinkX.GetValue(),
                              'overlay_layout':self.html_overlay_layout.GetValue(),
                              'overlay_linkXY':self.html_overlay_linkXY.GetValue(),
                              'overlay_color_1':self.html_overlay_colormap_1.GetStringSelection(),
                              'overlay_color_2':self.html_overlay_colormap_2.GetStringSelection(),
                              'colorbar':self.colorbarCheck.GetValue(),
                              'legend':self.html_overlay_legend.GetValue(),
                              'title_label':self.grid_label_check.GetValue(),
                              'grid_xpos':self.grid_xpos_value.GetValue(),
                              'grid_ypos':self.grid_ypos_value.GetValue(),
                              'waterfall_increment':self.waterfall_increment_value.GetValue(),
                              'linearize_spectra':self.linearizeCheck.GetValue(),
                              'show_annotations':self.showAnnotationsCheck.GetValue(),
                              'bin_size':self.binSize_value.GetValue()
                              }
        color_label = color
        if key == 'Overlay':
            overlayMethod = re.split('-|,|:|__', innerKey)
            if overlayMethod[0] == 'Mask' or overlayMethod[0] == 'Transparent':
                color_label = "%s/%s" % (self.html_overlay_colormap_1.GetStringSelection(), 
                                         self.html_overlay_colormap_2.GetStringSelection())
                pageData = self.config.pageDict['None']

        if self.loading: return
        
        # Retrieve and add data to dictionary
        document = self.documentsDict[name]
        if key == 'MS' and innerKey == '': document.massSpectrum = self.addHTMLtagsToDictionary(document.massSpectrum, 
                                                                             title, header, footnote, orderNum, color, pageData, toolSet, False,
                                                                             interactive_params)
        
        if key == 'RT' and innerKey == '': document.RT = self.addHTMLtagsToDictionary(document.RT, 
                                                                             title, header, footnote, orderNum, color, pageData, toolSet, False,
                                                                             interactive_params)
        
        if key == 'RT, multiple' and innerKey != '': document.multipleRT[innerKey] = self.addHTMLtagsToDictionary(document.multipleRT[innerKey], 
                                                                                                title, header, footnote, orderNum, color, pageData, toolSet,
                                                                                                interactive_params)
        
        if key == '1D' and innerKey == '': document.DT = self.addHTMLtagsToDictionary(document.DT, 
                                                                             title, header, footnote, orderNum, color, pageData, toolSet, False,
                                                                             interactive_params)
        
        if key == '1D, multiple' and innerKey != '': document.multipleDT[innerKey] = self.addHTMLtagsToDictionary(document.multipleDT[innerKey], 
                                                                                                title, header, footnote, orderNum, color, pageData, toolSet, False,
                                                                                                interactive_params)
        
        if key == 'MS, multiple' and innerKey != '': document.multipleMassSpectrum[innerKey] = self.addHTMLtagsToDictionary(document.multipleMassSpectrum[innerKey], 
                                                                                                title, header, footnote, orderNum, color, pageData, toolSet, False,
                                                                                                interactive_params)
        
        if key == 'DT-IMS' and innerKey != '': document.IMS1DdriftTimes[innerKey] = self.addHTMLtagsToDictionary(document.IMS1DdriftTimes[innerKey], 
                                                                             title, header, footnote, orderNum, color, pageData, toolSet, False,
                                                                             interactive_params)
        
        if key == 'RT, combined' and innerKey != '': document.IMSRTCombIons[innerKey] = self.addHTMLtagsToDictionary(document.IMSRTCombIons[innerKey], 
                                                                             title, header, footnote, orderNum, color, pageData, toolSet, False,
                                                                             interactive_params)
        
        if key == '2D' and innerKey == '': document.IMS2D = self.addHTMLtagsToDictionary(document.IMS2D, 
                                                                             title, header, footnote, orderNum, color, pageData, toolSet, colorbar,
                                                                             interactive_params)
        
        if key == '2D, processed' and innerKey == '': document.IMS2Dprocess = self.addHTMLtagsToDictionary(document.IMS2Dprocess, 
                                                                             title, header, footnote, orderNum, color, pageData, toolSet, colorbar,
                                                                             interactive_params)
        
        if key == '2D, processed' and innerKey == '': document.IMS2Dprocess = self.addHTMLtagsToDictionary(document.multipleMassSpectrum, 
                                                                             title, header, footnote, orderNum, color, pageData, toolSet, colorbar,
                                                                             interactive_params)
        
        if key == '2D' and innerKey != '': document.IMS2Dions[innerKey] = self.addHTMLtagsToDictionary(document.IMS2Dions[innerKey], 
                                                                             title, header, footnote, orderNum, color, pageData, toolSet, colorbar,
                                                                             interactive_params)
        
        if key == '2D, combined' and innerKey != '': document.IMS2DCombIons[innerKey] = self.addHTMLtagsToDictionary(document.IMS2DCombIons[innerKey], 
                                                                             title, header, footnote, orderNum, color, pageData, toolSet, colorbar,
                                                                             interactive_params)
        
        if key == '2D, processed' and innerKey != '': document.IMS2DionsProcess[innerKey] = self.addHTMLtagsToDictionary(document.IMS2DionsProcess[innerKey], 
                                                                             title, header, footnote, orderNum, color, pageData, toolSet, colorbar,
                                                                             interactive_params)
        
        if key == 'Overlay' and innerKey != '': document.IMS2DoverlayData[innerKey] = self.addHTMLtagsToDictionary(document.IMS2DoverlayData[innerKey], 
                                                                             title, header, footnote, orderNum, color, pageData, toolSet, colorbar,
                                                                             interactive_params)
        
        if key == 'Statistical' and innerKey != '': document.IMS2DstatsData[innerKey] = self.addHTMLtagsToDictionary(document.IMS2DstatsData[innerKey], 
                                                                             title, header, footnote, orderNum, color, pageData, toolSet, colorbar,
                                                                             interactive_params)
        
        if key == 'UniDec' and innerKey != '': document.massSpectrum['unidec'][innerKey] = self.addHTMLtagsToDictionary(document.massSpectrum['unidec'][innerKey], 
                                                                                                                        title, header, footnote, orderNum, color, pageData, toolSet, colorbar,
                                                                                                                        interactive_params)
        if key == 'UniDec, multiple' and innerKey != '': 
            unidecMethod = re.split(' \| ', innerKey)[0]
            innerKey = re.split(' \| ', innerKey)[1]
            document.multipleMassSpectrum[innerKey]['unidec'][unidecMethod] = self.addHTMLtagsToDictionary(document.multipleMassSpectrum[innerKey]['unidec'][unidecMethod], 
                                                                                                           title, header, footnote, orderNum, color, pageData, toolSet, colorbar,
                                                                                                           interactive_params)
        
        # Set new text for labels
        self.itemsList.SetStringItem(index=self.currentItem,
                                     col=self.config.interactiveColNames['title'], label=title)
        self.itemsList.SetStringItem(index=self.currentItem,
                                     col=self.config.interactiveColNames['header'], label=header)
        self.itemsList.SetStringItem(index=self.currentItem,
                                     col=self.config.interactiveColNames['footnote'], label=footnote)
        self.itemsList.SetStringItem(index=self.currentItem,
                                     col=self.config.interactiveColNames['color'], label=str(color_label))
        self.itemsList.SetStringItem(index=self.currentItem,
                                     col=self.config.interactiveColNames['order'], label=orderNum)
        self.itemsList.SetStringItem(index=self.currentItem,
                                     col=self.config.interactiveColNames['page'], label=page)
        self.itemsList.SetStringItem(index=self.currentItem,
                                     col=self.config.interactiveColNames['tools'], label=tool)
        
        # Update dictionary
        self.presenter.documentsDict[document.title] = document
        
    def addHTMLtagsToDictionary(self, dictionary, title, header, footnote, 
                                orderNumber, color, page, toolSet, colorbar=False,
                                interactive_params={}):
        """
        Helper function to add title,header,footnote data
        to dictionary
        """
        dictionary['title'] = title
        dictionary['header'] = header
        dictionary['footnote'] = footnote
        dictionary['order'] = orderNumber
        dictionary['cmap'] = color
        dictionary['page'] = page
        dictionary['tools'] = toolSet
        dictionary['colorbar'] = colorbar
        dictionary['interactive_params'] = interactive_params
        try: dictionary['cmap1'] = interactive_params['overlay_color_1']
        except: pass
        try: dictionary['cmap2'] = interactive_params['overlay_color_2']
        except: pass
        
        return dictionary 
                            
    def _setupPlotParameters(self, bokehPlot, plot_type="1D", **kwargs):
        
        if plot_type == "1D":
            # Add border 
            bokehPlot.outline_line_width = self.config.interactive_outline_width
            bokehPlot.outline_line_alpha = self.config.interactive_outline_alpha
            bokehPlot.outline_line_color = "black"
            # X-axis
            bokehPlot.xaxis.axis_label_text_font_size = self._fontSizeConverter(self.config.interactive_label_fontSize)
            bokehPlot.xaxis.axis_label_text_font_style = self._fontWeightConverter(self.config.interactive_label_weight)
            bokehPlot.xaxis.major_label_text_font_size = self._fontSizeConverter(self.config.interactive_tick_fontSize)
            # Y-axis
            bokehPlot.yaxis.axis_label_text_font_size = self._fontSizeConverter(self.config.interactive_label_fontSize)
            bokehPlot.yaxis.major_label_text_font_size = self._fontSizeConverter(self.config.interactive_tick_fontSize)
            bokehPlot.yaxis.axis_label_text_font_style = self._fontWeightConverter(self.config.interactive_label_weight)
            # Y-axis ticks
            bokehPlot.yaxis[0].formatter = BasicTickFormatter(precision=self.config.interactive_tick_precision, 
                                                              use_scientific=self.config.interactive_tick_useScientific)
            return bokehPlot
        
        elif plot_type == "Waterfall":
            # Interactive legend
            bokehPlot.legend.location = self.config.interactive_legend_location
            bokehPlot.legend.click_policy = self.config.interactive_legend_click_policy
            bokehPlot.legend.background_fill_alpha = self.config.interactive_legend_background_alpha
            bokehPlot.legend.label_text_font_size = self._fontSizeConverter(self.config.interactive_legend_font_size)
            bokehPlot.legend.orientation = self.config.interactive_legend_orientation
            # Add border 
            bokehPlot.outline_line_width = self.config.interactive_outline_width
            bokehPlot.outline_line_alpha = self.config.interactive_outline_alpha
            bokehPlot.outline_line_color = "black"
            # X-axis
            bokehPlot.xaxis.axis_label_text_font_size = self._fontSizeConverter(self.config.interactive_label_fontSize)
            bokehPlot.xaxis.axis_label_text_font_style = self._fontWeightConverter(self.config.interactive_label_weight)
            bokehPlot.xaxis.major_label_text_font_size = self._fontSizeConverter(self.config.interactive_tick_fontSize)
            # Y-axis
            bokehPlot.yaxis.axis_label_text_font_size = self._fontSizeConverter(self.config.interactive_label_fontSize)
            bokehPlot.yaxis.major_label_text_font_size = self._fontSizeConverter(self.config.interactive_tick_fontSize)
            bokehPlot.yaxis.axis_label_text_font_style = self._fontWeightConverter(self.config.interactive_label_weight)
            # Y-axis ticks
            bokehPlot.yaxis[0].formatter = BasicTickFormatter(precision=self.config.interactive_tick_precision, 
                                                              use_scientific=self.config.interactive_tick_useScientific)
            
            return bokehPlot
            
        elif plot_type == "Overlay_1D":
            # Interactive legend
            bokehPlot.legend.location = self.config.interactive_legend_location
            bokehPlot.legend.click_policy = self.config.interactive_legend_click_policy
            bokehPlot.legend.background_fill_alpha = self.config.interactive_legend_background_alpha
            bokehPlot.legend.label_text_font_size = self._fontSizeConverter(self.config.interactive_legend_font_size)
            bokehPlot.legend.orientation = self.config.interactive_legend_orientation
            # Add border 
            bokehPlot.outline_line_width = self.config.interactive_outline_width
            bokehPlot.outline_line_alpha = self.config.interactive_outline_alpha
            bokehPlot.outline_line_color = "black"
            # X-axis
            bokehPlot.xaxis.axis_label_text_font_size = self._fontSizeConverter(self.config.interactive_label_fontSize)
            bokehPlot.xaxis.axis_label_text_font_style = self._fontWeightConverter(self.config.interactive_label_weight)
            bokehPlot.xaxis.major_label_text_font_size = self._fontSizeConverter(self.config.interactive_tick_fontSize)
            # Y-axis
            bokehPlot.yaxis.axis_label_text_font_size = self._fontSizeConverter(self.config.interactive_label_fontSize)
            bokehPlot.yaxis.major_label_text_font_size = self._fontSizeConverter(self.config.interactive_tick_fontSize)
            bokehPlot.yaxis.axis_label_text_font_style = self._fontWeightConverter(self.config.interactive_label_weight)
            # Y-axis ticks
            bokehPlot.yaxis[0].formatter = BasicTickFormatter(precision=self.config.interactive_tick_precision, 
                                                              use_scientific=self.config.interactive_tick_useScientific)
            return bokehPlot
        
        elif plot_type == "2D":
            # Add border 
            bokehPlot.outline_line_width = self.config.interactive_outline_width
            bokehPlot.outline_line_alpha = self.config.interactive_outline_alpha  
            bokehPlot.outline_line_color = "black"
            bokehPlot.min_border_right = self.config.interactive_border_min_right
            bokehPlot.min_border_left = self.config.interactive_border_min_left
            bokehPlot.min_border_top = self.config.interactive_border_min_top
            bokehPlot.min_border_bottom = self.config.interactive_border_min_bottom
            # X-axis
            bokehPlot.xaxis.axis_label_text_font_size = self._fontSizeConverter(self.config.interactive_label_fontSize)
            bokehPlot.xaxis.axis_label_text_font_style = self._fontWeightConverter(self.config.interactive_label_weight)
            bokehPlot.xaxis.major_label_text_font_size = self._fontSizeConverter(self.config.interactive_tick_fontSize)
            # Y-axis
            bokehPlot.yaxis.axis_label_text_font_size = self._fontSizeConverter(self.config.interactive_label_fontSize)
            bokehPlot.yaxis.major_label_text_font_size = self._fontSizeConverter(self.config.interactive_tick_fontSize)
            bokehPlot.yaxis.axis_label_text_font_style = self._fontWeightConverter(self.config.interactive_label_weight)
            
            if kwargs.get("tight_layout", False):
                bokehPlot.min_border_right = 10
                bokehPlot.min_border_left = 10
                bokehPlot.min_border_top = 10
                bokehPlot.min_border_bottom = 10
            
            return bokehPlot
        
        elif plot_type == "Matrix":
            # Add border 
            bokehPlot.outline_line_width = self.config.interactive_outline_width
            bokehPlot.outline_line_alpha = self.config.interactive_outline_alpha  
            bokehPlot.outline_line_color = "black"
            bokehPlot.min_border_right = self.config.interactive_border_min_right
            bokehPlot.min_border_left = self.config.interactive_border_min_left
            bokehPlot.min_border_top = self.config.interactive_border_min_top
            bokehPlot.min_border_bottom = self.config.interactive_border_min_bottom
            # X-axis
            bokehPlot.xaxis.axis_label_text_font_size = self._fontSizeConverter(self.config.interactive_label_fontSize)
            bokehPlot.xaxis.axis_label_text_font_style = self._fontWeightConverter(self.config.interactive_label_weight)
            bokehPlot.xaxis.major_label_text_font_size = self._fontSizeConverter(self.config.interactive_tick_fontSize)
            bokehPlot.xaxis.major_label_orientation = np.pi/3
            # Y-axis
            bokehPlot.yaxis.axis_label_text_font_size = self._fontSizeConverter(self.config.interactive_label_fontSize)
            bokehPlot.yaxis.major_label_text_font_size = self._fontSizeConverter(self.config.interactive_tick_fontSize)
            bokehPlot.yaxis.axis_label_text_font_style = self._fontWeightConverter(self.config.interactive_label_weight)
            bokehPlot.grid.grid_line_color = None
            bokehPlot.axis.axis_line_color = None
            bokehPlot.axis.major_tick_line_color = None
            return bokehPlot
        
        elif plot_type == "RMSF":
            # Add border 
            bokehPlot.outline_line_width = self.config.interactive_outline_width
            bokehPlot.outline_line_alpha = self.config.interactive_outline_alpha
            bokehPlot.outline_line_color = "black"
            # Y-axis
            bokehPlot.yaxis.axis_label_text_font_size = self._fontSizeConverter(self.config.interactive_label_fontSize)
            bokehPlot.yaxis.major_label_text_font_size = self._fontSizeConverter(self.config.interactive_tick_fontSize)
            bokehPlot.yaxis.axis_label_text_font_style = self._fontWeightConverter(self.config.interactive_label_weight)
            return bokehPlot
            
    def kda_test(self, xvals):
        """
        Adapted from Unidec/PlottingWindow.py
        
        Test whether the axis should be normalized to convert mass units from Da to kDa.
        Will use kDa if: xvals[int(len(xvals) / 2)] > 100000 or xvals[len(xvals) - 1] > 1000000

        If kDa is used, self.kda=True and self.kdnorm=1000. Otherwise, self.kda=False and self.kdnorm=1.
        :param xvals: mass axis
        :return: None
        """
        try:
            if xvals[int(len(xvals) / 2)] > 100000 or xvals[len(xvals) - 1] > 1000000:
                kdnorm = 1000.
                xlabel = "Mass (kDa)"
                kda = True
            elif np.amax(xvals) > 10000:
                kdnorm = 1000.
                xlabel = "Mass (kDa)"
                kda = True
            else:
                xlabel = "Mass (Da)"
                kda = False
                kdnorm = 1.
        except (TypeError, ValueError):
            xlabel = "Mass (Da)"
            kdnorm = 1.
            kda = False
            
        # convert x-axis
        xvals = xvals / kdnorm
        
        return xvals, xlabel, kda
            
    def linearize_spectrum(self, xvals, yvals, binsize):
        kwargs = {'auto_range':self.config.ms_auto_range,
                  'mz_min':np.round(np.min(xvals),0), 
                  'mz_max':np.round(np.min(yvals),0), 
                  'mz_bin':float(binsize),
                  'linearization_mode':"Linear interpolation"}

        msX, msY = linearize_data(xvals, yvals, **kwargs)
        print("Linearized spectrum. Reduced spectrum from {} to {}".format(len(xvals), len(msX)))
        return msX, msY
            
    def prepareDataForInteractivePlots(self, data=None, type=None, subtype=None, title=None,
                                       xlabelIn=None, ylabelIn=None, linkXYAxes=False,
                                       testX=False, reshape=False, layout='Rows', 
                                       addColorbar=None, **kwargs):
        """
        Prepare data to be in an appropriate format
        """
        # Call the helper function to make sure we generated tool list
        self.onSelectTools(evt=None)
        
        # get parameters
        if self.config.interactive_override_defaults:
            interactive_params = data.get('interactive_params', {})
        else:
            interactive_params = {}
            
        if len(interactive_params) == 0:
            hover_vline = self.config.hoverVline
            line_width = self.config.interactive_line_width
            line_alpha = self.config.interactive_line_alpha
            line_style = self.config.interactive_line_style
            overlay_layout = self.config.plotLayoutOverlay
            overlay_linkXY = self.config.linkXYaxes
            legend = self.config.interactive_legend
            addColorbar = self.config.interactive_colorbar
            title_label = False
            xpos = self.config.interactive_grid_xpos
            ypos = self.config.interactive_grid_ypos
            waterfall_increment = self.config.interactive_waterfall_increment
            linearize_spectra = self.config.interactive_ms_linearize
            show_annotations = self.config.interactive_ms_annotations
            bin_size = self.config.interactive_ms_binSize
        else:
            hover_vline = interactive_params['line_linkXaxis']
            line_width = interactive_params['line_width']
            line_alpha = interactive_params['line_alpha']
            line_style = interactive_params['line_style']
            overlay_layout = interactive_params['overlay_layout']
            overlay_linkXY = interactive_params['overlay_linkXY']
            legend = interactive_params['legend']
            addColorbar = interactive_params['colorbar']
            title_label = interactive_params.get('title_label', self.config.interactive_grid_xpos)
            xpos = interactive_params.get('grid_xpos', self.config.interactive_grid_xpos)
            ypos = interactive_params.get('grid_ypos', self.config.interactive_grid_ypos)
            waterfall_increment = interactive_params.get('waterfall_increment', self.config.interactive_waterfall_increment)
            linearize_spectra = interactive_params.get('linearize_spectra', self.config.interactive_ms_linearize)
            show_annotations = interactive_params.get('show_annotations', self.config.interactive_ms_annotations)
            bin_size = interactive_params.get('bin_size', self.config.interactive_ms_binSize)
            
        if type == 'MS' or type == 'RT' or type == '1D' or type == 'MS, multiple':
            xvals, yvals, xlabelIn, cmap =  self.presenter.get2DdataFromDictionary(dictionary=data,
                                                                                   plotType='1D',
                                                                                   dataType='plot',
                                                                                   compact=False)
            if testX:
                xvals, xlabelIn, __ = self.kda_test(xvals)
            
            if cmap == "": cmap = [0, 0, 0]
            
            # Check if we should lock the hoverline
            if hover_vline:
                hoverMode='vline'
            else:
                hoverMode='mouse'
                
            # Prepare hover tool
            if type in ['MS', 'MS, multiple']:
                hoverTool = HoverTool(tooltips = [(xlabelIn, '$x{0.00}'),
                                                  (ylabelIn, '$y{0.00}')],
                                      mode=hoverMode) 
            elif type in ['RT', 'RT, multiple']:
                hoverTool = HoverTool(tooltips = [(xlabelIn, '$x{0.00}'),
                                                  (ylabelIn, '$y{0.00}'),],
                                      mode=hoverMode) 
            elif type in ['1D', '1D, multiple']:
                hoverTool = HoverTool(tooltips = [(xlabelIn, '$x{0.00}'),
                                                  (ylabelIn, '$y{0.00}'),],
                                      mode=hoverMode) 

            if linearize_spectra and len(xvals) > 25000:
                xvals, yvals = self.linearize_spectrum(xvals, yvals, bin_size)
            if "annotations" in data and len(data["annotations"]) > 0 and show_annotations:
                hoverTool = HoverTool(tooltips = [(xlabelIn, '$x{0.00}'),
                                                  (ylabelIn, '$y{0.00}'),
                                                  ("Charge", '@charge'),
                                                  ("Label", '@label')],
                                      mode=hoverMode) 
                annot_xmin_list, annot_xmax_list, annot_ymin_list, annot_ymax_list, charge_list = [], [], [], [], []
                annot_list_x_charge = [""] * len(xvals)
                annot_list_x_label = list(annot_list_x_charge) # make a copy of list
                annot_list_y = [0] * len(xvals)
                for i, annotKey in enumerate(data['annotations']):
#                     print(data['annotations'][annotKey]["charge"])
#                     annot_xmin_list.append(data['annotations'][annotKey]["min"])
#                     annot_xmax_list.append(data['annotations'][annotKey]["max"])
#                     annot_ymax_list.append(data['annotations'][annotKey]["intensity"])
#                     annot_ymin_list.append(0)
                    __, x_min_idx = find_nearest(xvals, data['annotations'][annotKey]["min"])
                    __, x_max_idx = find_nearest(xvals, data['annotations'][annotKey]["max"])
                    annot_list_x_charge[x_min_idx:x_max_idx] = (x_max_idx-x_min_idx) * [data['annotations'][annotKey]["charge"]]
                    annot_list_x_label[x_min_idx:x_max_idx] = (x_max_idx-x_min_idx) * [data['annotations'][annotKey]["label"]]
                    annot_list_y[x_min_idx:x_max_idx] = yvals[x_min_idx:x_max_idx]
                
                # generate patch and ms data source
                patch_source = ColumnDataSource(data=dict(xvals=xvals, 
                                                          yvals=annot_list_y))
                ms_source = ColumnDataSource(data=dict(xvals=xvals, 
                                                       yvals=yvals,
                                                       charge=annot_list_x_charge,
                                                       label=annot_list_x_label))
            else:
                ms_source = ColumnDataSource(data=dict(xvals=xvals, 
                                                       yvals=yvals))

            # Prepare MS file
            if len(data['tools']) > 0:
                # Enable current active tools
                self.activeDrag = data['tools']['tools']['activeDrag']
                self.activeWheel = data['tools']['tools']['activeWheel']
                # Check if toolset should include hover tool
                if data['tools']['tools']['hover']:
                    # Add tools + hover
                    TOOLS = [hoverTool, data['tools']['tools']['tools']]
                else:
                    # Add only tools
                    TOOLS = data['tools']['tools']['tools']
            elif self.hover_check.GetValue():  
                TOOLS = [hoverTool,self.tools]
            else: TOOLS = self.tools
            
            bokehPlot = figure(x_range=(min(xvals), max(xvals)), 
                               y_range=(min(yvals), max(yvals)),
                               tools=TOOLS,
                               title=title,
                               active_drag=self.activeDrag,
                               active_scroll=self.activeWheel,
                               plot_width=self.config.figWidth1D, 
                               plot_height=(self.config.figHeight1D), 
                               toolbar_location=self.config.toolsLocation)
            
#             if "annotations" in data:
#                 hoverTool = HoverTool(tooltips = [(xlabelIn, '$x{0.00}'),
#                                                   (ylabelIn, '$y{0.00}'),
#                                                   ("Charge", '@charge')],
#                                       mode=hoverMode) 
#                 annot_xmin_list, annot_xmax_list, annot_ymin_list, annot_ymax_list, charge_list = [], [], [], [], []
#                 annot_list = [0] * len(xvals)
#                 for i, annotKey in enumerate(data['annotations']):
#                     annot_xmin_list.append(data['annotations'][annotKey]["min"])
#                     annot_xmax_list.append(data['annotations'][annotKey]["max"])
#                     annot_ymax_list.append(data['annotations'][annotKey]["intensity"])
#                     annot_ymin_list.append(0)
#                     __, x_min_idx = find_nearest(xvals, data['annotations'][annotKey]["min"])
#                     __, x_max_idx = find_nearest(xvals, data['annotations'][annotKey]["max"])
#                     annot_list[x_min_idx:x_max_idx] = (x_max_idx-x_min_idx) * [i+2]
#                     

            cmap = convertRGB1to255(cmap, as_integer=True, as_tuple=True)
            bokehPlot.line("xvals", "yvals", source=ms_source,
                           line_color=cmap,
                           line_width=line_width,
                           line_dash=line_style,
                           line_alpha=line_alpha)
#             if "annotations" in data and len(data["annotations"]) > 0:
#                 bokehPlot.patch("xvals", "yvals", color='#FF0000', 
#                                 fill_alpha=0.8, 
#                                 source=patch_source)
#             if "annotations" in data:
#                 bokehPlot.quad(top="top", bottom="bottom", left="left", right="right", 
#                                 color="#B3DE69", fill_alpha=0.5, source=quad_source)
#                 bokehPlot.add_tools(None)
#                 
#                 quad_source = ColumnDataSource(data=dict(top=annot_ymin_list,
#                                                     bottom=annot_ymax_list,
#                                                     left=annot_xmin_list,
#                                                     right=annot_xmax_list,
#                                                     ))
#                 bokehPlot.quad(top="top", bottom="bottom", left="left", right="right", 
#                                color="#B3DE69", fill_alpha=0.5, source=quad_source)
#             else:
#             cmap = convertRGB1to255(cmap, as_integer=True, as_tuple=True)
#             bokehPlot.line(xvals, yvals, 
#                            line_color=cmap,
#                            line_width=line_width,
#                            line_dash=line_style,
#                            line_alpha=line_alpha)
            
            
                
#                     print(x_min_idx, x_max_idx)
#                     annot_xmin_list.append(data['annotations'][annotKey]["min"])
#                     annot_xmax_list.append(data['annotations'][annotKey]["max"])
#                     annot_ymax_list.append(data['annotations'][annotKey]["intensity"])
#                     annot_ymin_list.append(0)
#                     charge_list.append(1) #data['annotations'][annotKey]["charge"])
#                 source = ColumnDataSource(data=dict(top=annot_ymin_list,
#                                                     bottom=annot_ymax_list,
#                                                     left=annot_xmin_list,
#                                                     right=annot_xmax_list,
#                                                     charge=charge_list 
#                                                     ))
#                 bokehPlot.quad(top="top", bottom="bottom", left="left", right="right", 
#                                color="#B3DE69", fill_alpha=0.5, source=source)
#                 bokehPlot.add_tools(annotTool)
            
#             cmap = convertRGB1to255(cmap, as_integer=True, as_tuple=True)  
#             bokehPlot.line(xvals, yvals, 
#                            line_color=cmap,
#                            line_width=line_width,
#                            line_dash=line_style,
#                            line_alpha=line_alpha)

#                     annotTool = HoverTool(tooltips = [("Charge state", data['annotations'][annotKey]["charge"])])
#                     bokehPlot.add_tools(annotTool)
#                 # add annotations
#                 bokehPlot.quad(top=annot_ymax_list, bottom=annot_ymin_list, 
#                                left=annot_xmin_list, right=annot_xmax_list, 
#                                color="#B3DE69", fill_alpha=0.1)
#                 bokehPlot.add_tools(annotTool)
            # setup labels
            bokehPlot.xaxis.axis_label = xlabelIn
            bokehPlot.yaxis.axis_label = ylabelIn
            
            # setup common plot parameters
            bokehPlot = self._setupPlotParameters(bokehPlot, plot_type="1D")
        
        elif type == 'Waterfall':
            xvals = data['xvals']
            yvals = data['yvals']
            colorList = data['colors']
            xlabel = data['xlabel']
            ylabel = data['ylabel']
            labels = data['waterfall_kwargs']['labels']
            kwargs = data['waterfall_kwargs']
            
            # Check if we should lock the hoverline
            if hover_vline: hoverMode='vline'
            else: hoverMode='mouse'
        
            # Prepare hover tool
            hoverTool = HoverTool(tooltips = [(xlabel, '@xvals{0.00}'),
                                              (ylabel, '@yvals{0.00}'),
                                              ("Label", "@label")],
                                  mode=hoverMode)
            # Prepare MS file
            if len(data['tools']) > 0:
                # Enable current active tools
                self.activeDrag = data['tools']['tools']['activeDrag']
                self.activeWheel = data['tools']['tools']['activeWheel']
                # Check if toolset should include hover tool
                if data['tools']['tools']['hover']:
                    # Add tools + hover
                    TOOLS = [hoverTool, data['tools']['tools']['tools']]
                else:
                    # Add only tools
                    TOOLS = data['tools']['tools']['tools']
            elif self.hover_check.GetValue():  
                TOOLS = [hoverTool,self.tools]
            else: TOOLS = self.tools

            xvals_list, yvals_list = find_limits_list(xvals, yvals)
                
            xlimits = [np.min(xvals_list), np.max(xvals_list)]
            ylimits = [np.min(yvals_list), np.max(yvals_list)]
            
            ylimits[1] = ylimits[1] + len(xvals) * waterfall_increment
            
            bokehPlot = figure(x_range=xlimits, 
                               y_range=ylimits, 
                               tools=TOOLS,
                               active_drag=self.activeDrag,
                               active_scroll=self.activeWheel,
                               plot_width=self.config.figWidth, 
                               plot_height=(self.config.figHeight), 
                               toolbar_location=self.config.toolsLocation)
            # create dataframe
            i = len(xvals)
            for xval, yval, color, label in zip(xvals, yvals, colorList, labels):
                color = convertRGB1to255(color, as_integer=True, as_tuple=True)
                if linearize_spectra and len(xval) > 25000:
                    xval, yval = self.linearize_spectrum(xval, yval, bin_size)
                source = ColumnDataSource(data=dict(xvals=xval,
                                                    yvals=yval + waterfall_increment * i,
                                                    label=([label]*len(xval))))
                if not legend: label = None
                bokehPlot.line(x="xvals", y="yvals", 
                               line_color=color, 
                               line_width=line_width,
                               line_alpha=line_alpha,
                               line_dash=line_style,
                               legend=label,
                               muted_alpha=self.config.interactive_legend_mute_alpha,
                               muted_color=color,
                               source=source)
                i = i - 1
            # setup labels
            bokehPlot.xaxis.axis_label = xlabel
            bokehPlot.yaxis.axis_label = ylabel
            # setup common parameters
            bokehPlot = self._setupPlotParameters(bokehPlot, plot_type="Waterfall")
        
        elif type == 'Overlay_1D':
            xvals, yvals, xlabelIn, line_colors, labels, __ = self.presenter.get2DdataFromDictionary(dictionary=data,
                                                                                                     plotType='Overlay1D',
                                                                                                     compact=True)
            # Check if we should lock the hoverline
            if hover_vline:
                hoverMode='vline'
            else:
                hoverMode='mouse'
            # Prepare hover tool
            hoverTool = HoverTool(tooltips = [(xlabelIn, '@xvals{0.00}'),
                                              (ylabelIn, '@yvals{0.00}'),
                                              ("Label", "@label")],
                                  mode=hoverMode)
            # Prepare MS file
            if len(data['tools']) > 0:
                # Enable current active tools
                self.activeDrag = data['tools']['tools']['activeDrag']
                self.activeWheel = data['tools']['tools']['activeWheel']
                # Check if toolset should include hover tool
                if data['tools']['tools']['hover']:
                    # Add tools + hover
                    TOOLS = [hoverTool, data['tools']['tools']['tools']]
                else:
                    # Add only tools
                    TOOLS = data['tools']['tools']['tools']
            elif self.hover_check.GetValue():  
                TOOLS = [hoverTool,self.tools]
            else: TOOLS = self.tools
            
            bokehPlot = figure(x_range=(np.amin(np.ravel(xvals)), 
                                        np.amax(np.ravel(xvals))), 
                               y_range=(np.amin(np.ravel(yvals)), 
                                        np.amax(np.ravel(yvals))), 
                               tools=TOOLS,
                               active_drag=self.activeDrag,
                               active_scroll=self.activeWheel,
                               plot_width=self.config.figWidth1D, 
                               plot_height=(self.config.figHeight1D), 
                               toolbar_location=self.config.toolsLocation)
#             colorList = []
#             for color in line_colors:
#                 colorList.append(convertRGB1toHEX(color))
#                 
#             source = ColumnDataSource(data=dict(xvals=xvals,
#                                                 yvals=yvals,
#                                                 colors=colorList,
#                                                 labels=labels,
#                                                 ))
#             bokehPlot.multi_line(xs="xvals", ys="yvals", 
#                                  line_color="colors", 
#                                  line_width=line_width,
#                                  line_alpha=line_alpha,
#                                  line_dash=line_style,
#                                  legend="labels",
#                                  muted_alpha=self.config.interactive_legend_mute_alpha,
#                                  muted_color="colors",
#                                  source=source)
            
            # create dataframe
            for xval, yval, color, label in zip(xvals, yvals, line_colors, labels):
                color = convertRGB1to255(color, as_integer=True, as_tuple=True)
                source = ColumnDataSource(data=dict(xvals=xval,
                                                    yvals=yval,
                                                    label=([label]*len(xval))))
                if not legend:
                    label = None
                bokehPlot.line(x="xvals", y="yvals", 
                               line_color=color, 
                               line_width=line_width,
                               line_alpha=line_alpha,
                               line_dash=line_style,
                               legend=label,
                               muted_alpha=self.config.interactive_legend_mute_alpha,
                               muted_color=color,
                               source=source)
            # setup labels
            bokehPlot.xaxis.axis_label = xlabelIn
            bokehPlot.yaxis.axis_label = ylabelIn
            # setup common parameters
            bokehPlot = self._setupPlotParameters(bokehPlot, plot_type="Overlay_1D")
           
        elif type == "Grid_NxN":
            zvals_list = data['zvals_list']
            cmap_list = data['cmap_list']
            title_list = data['title_list']
            xvals = data['xvals']
            yvals = data['yvals']
            xlabel = data['xlabels']
            ylabel = data['ylabels']
            plot_parameters = data['plot_parameters']
            
            hoverTool = HoverTool(tooltips=[(xlabel, '$x{0.00}'), 
                                            (ylabel, '$y{0.00}'), 
                                            ('Intensity', '@image')],
                                point_policy = 'follow_mouse')    
        
            if len(data['tools']) > 0:
                # Enable current active tools
                self.activeDrag = data['tools']['tools']['activeDrag']
                self.activeWheel = data['tools']['tools']['activeWheel']
                # Check if toolset should include hover tool
                if data['tools']['tools']['hover']:
                    # Add tools + hover
                    TOOLS = [hoverTool, data['tools']['tools']['tools']]
                else:
                    # Add only tools
                    TOOLS = data['tools']['tools']['tools']
            elif self.hover_check.GetValue():  TOOLS = [hoverTool,self.tools]
            else: TOOLS = self.tools
            
            plot_list = []
            for i, zvals in enumerate(zvals_list):
                row = int(i // plot_parameters["n_cols"])
                col = i % plot_parameters["n_cols"]
                data = dict(image=[zvals], x=[min(xvals)], y=[min(yvals)],
                            dw=[max(xvals)], dh=[max(yvals)])
                cds = ColumnDataSource(data=data)
                colormap = cm.get_cmap(cmap_list[i])
                colormap = [colors.rgb2hex(m) for m in colormap(np.arange(colormap.N))]
                if i == 0:
                    plot = figure(x_range=(min(xvals), max(xvals)),
                                  y_range=(min(yvals), max(yvals)),
                                  tools=TOOLS, title=title_list[i],
                                  active_drag=self.activeDrag,
                                  active_scroll=self.activeWheel,
                                  plot_width=300, plot_height=300, 
                                  toolbar_location=self.config.toolsLocation)
                else:
                    plot = figure(x_range=plot_list[0].x_range, 
                                  y_range=plot_list[0].y_range,
                                  tools=TOOLS, 
                                  active_drag=self.activeDrag,
                                  active_scroll=self.activeWheel,
                                  plot_width=300, plot_height=300, 
                                  toolbar_location=self.config.toolsLocation)
                plot.image(source=cds, image='image', x='x', y='y', dw='dw', dh='dh', palette=colormap)
                if col == 0:
                    plot.yaxis.axis_label = ylabel
                if row == plot_parameters['n_rows'] - 1:
                    plot.xaxis.axis_label = xlabel

                # Add RMSD label to the plot
                if title_label:
                    textColor = convertRGB1to255(self.config.interactive_grid_label_color, as_integer=True, as_tuple=True)  
                    titleAnnot = Label(x=xpos, y=ypos, x_units='data', y_units='data',
                                      text=title_list[i], render_mode='canvas', 
                                      text_color = textColor,
                                      text_font_size=self._fontSizeConverter(self.config.interactive_grid_label_size),
                                      text_font_style=self._fontWeightConverter(self.config.interactive_grid_label_weight),
                                      background_fill_alpha=0)
                    plot.add_layout(titleAnnot)
                
                kwargs = {'tight_layout':True}
                plot = self._setupPlotParameters(plot, plot_type="2D", **kwargs)
                
                plot_list.append(plot)
                
            bokehPlot =  gridplot(plot_list, ncols=plot_parameters['n_cols'])
            
        elif type == 'Grid':           
            zvals_1, zvals_2, zvals_cum = data['zvals_1'], data['zvals_2'], data['zvals_cum'] 
            xvals, yvals = data['xvals'], data['yvals']
            xlabel, ylabel, rmsdLabel = data['xlabels'], data['ylabels'], data['rmsdLabel']
            cmap_1, cmap_2 = data['cmap_1'], data['cmap_2']
            
            z_top_left_data = dict(image=[zvals_1], x=[min(xvals)], y=[min(yvals)],
                            dw=[max(xvals)], dh=[max(yvals)])
            cds_top_left = ColumnDataSource(data=z_top_left_data)
            z_bottom_left_data = dict(image=[zvals_2], x=[min(xvals)], y=[min(yvals)],
                            dw=[max(xvals)], dh=[max(yvals)])
            cds_bottom_left = ColumnDataSource(data=z_bottom_left_data)
            z_right_data = dict(image=[zvals_cum], x=[min(xvals)], y=[min(yvals)],
                            dw=[max(xvals)], dh=[max(yvals)])
            cds_right_left = ColumnDataSource(data=z_right_data)
            
            hoverTool = HoverTool(tooltips=[(xlabel, '$x{0}'), 
                                            (ylabel, '$y{0}'), 
                                            ('Intensity', '@image')
                                            ],
                                point_policy = 'follow_mouse',
                                 )
            
            if len(data['tools']) > 0:
                # Enable current active tools
                self.activeDrag = data['tools']['tools']['activeDrag']
                self.activeWheel = data['tools']['tools']['activeWheel']
                # Check if toolset should include hover tool
                if data['tools']['tools']['hover']:
                    # Add tools + hover
                    TOOLS = [hoverTool, data['tools']['tools']['tools']]
                else:
                    # Add only tools
                    TOOLS = data['tools']['tools']['tools']
            elif self.hover_check.GetValue():  TOOLS = [hoverTool,self.tools]
            else: TOOLS = self.tools
            
            colormap_top_left = cm.get_cmap(cmap_1)
            colormap_top_left = [colors.rgb2hex(m) for m in colormap_top_left(np.arange(colormap_top_left.N))]
            colormap_bottom_left = cm.get_cmap(cmap_2)
            colormap_bottom_left = [colors.rgb2hex(m) for m in colormap_bottom_left(np.arange(colormap_bottom_left.N))]
            colormap_right = cm.get_cmap("coolwarm")
            colormap_right = [colors.rgb2hex(m) for m in colormap_right(np.arange(colormap_right.N))]
            
            top_left = figure(x_range=(min(xvals), max(xvals)), 
                               y_range=(min(yvals), max(yvals)),
                                tools=TOOLS, 
                                active_drag=self.activeDrag,
                                active_scroll=self.activeWheel,
                               plot_width=int(self.config.figWidth*0.5), plot_height=int(self.config.figHeight*0.5), 
                               toolbar_location=self.config.toolsLocation)
            
            top_left.image(source=cds_top_left, image='image', x='x', y='y', dw='dw', dh='dh', palette=colormap_top_left)
            top_left.yaxis.axis_label = ylabel
            
            bottom_left = figure(x_range=top_left.x_range, 
                                 y_range=top_left.y_range, 
                                tools=TOOLS, 
                                active_drag=self.activeDrag,
                                active_scroll=self.activeWheel,
                               plot_width=int(self.config.figWidth*0.5), plot_height=int(self.config.figHeight*0.5), 
                               toolbar_location=self.config.toolsLocation)
            
            bottom_left.image(source=cds_bottom_left, image='image', x='x', y='y', dw='dw', dh='dh', palette=colormap_top_left)
            bottom_left.xaxis.axis_label = xlabel
            bottom_left.yaxis.axis_label = ylabel

            right = figure(x_range=top_left.x_range, 
                           y_range=top_left.y_range, 
                                tools=TOOLS, 
                                active_drag=self.activeDrag,
                                active_scroll=self.activeWheel,
                               plot_width=self.config.figWidth, plot_height=(self.config.figHeight), 
                               toolbar_location=self.config.toolsLocation)
            
            right.image(source=cds_right_left, image='image', x='x', y='y', dw='dw', dh='dh', palette=colormap_right)
            right.xaxis.axis_label = xlabel
            right.yaxis.axis_label = ylabel
            
            kwargs = {'tight_layout':True}
            top_left = self._setupPlotParameters(top_left, plot_type="2D", **kwargs)
            bottom_left = self._setupPlotParameters(bottom_left, plot_type="2D", **kwargs)
            right = self._setupPlotParameters(right, plot_type="2D", **kwargs)
            
            left_column = column(top_left, bottom_left)
            bokehPlot =  gridplot([[left_column, right]], sizing_mode="fixed")
            
        elif type == 'RGB':
            # Unpacks data using a helper function
            zvals, xvals, xlabel, yvals, ylabel, cmap = self.presenter.get2DdataFromDictionary(dictionary=data,
                                                                                               dataType='plot',
                                                                                               plotType='2D',
                                                                                               compact=False)
            # add transparency and reshape the array
            zvals = zvals * 255
            zvals = zvals.astype('int32')

            rgb = np.empty([zvals.shape[0], zvals.shape[1], 4], dtype=np.uint8)
            rgb[:, :, 0] = zvals[:, :, 0]
            rgb[:, :, 1] = zvals[:, :, 1] 
            rgb[:, :, 2] = zvals[:, :, 2] 
            rgb[:, :, 3].fill(255)
                    
            z_data = dict(image=[rgb], x=[min(xvals)], y=[min(yvals)],
                          dw=[max(xvals)], dh=[max(yvals)])
            cds = ColumnDataSource(data=z_data)
            hoverTool = HoverTool(tooltips=[(xlabel, '$x{0}'), 
                                            (ylabel, '$y{0}')],
                                point_policy = 'follow_mouse',
                                 )
             
            if len(data['tools']) > 0:
                # Enable current active tools
                self.activeDrag = data['tools']['tools']['activeDrag']
                self.activeWheel = data['tools']['tools']['activeWheel']
                # Check if toolset should include hover tool
                if data['tools']['tools']['hover']:
                    # Add tools + hover
                    TOOLS = [hoverTool, data['tools']['tools']['tools']]
                else:
                    # Add only tools
                    TOOLS = data['tools']['tools']['tools']
            elif self.hover_check.GetValue():  TOOLS = [hoverTool,self.tools]
            else: TOOLS = self.tools
            
            bokehPlot = figure(x_range=(min(xvals), max(xvals)), 
                               y_range=(min(yvals), max(yvals)),
                               tools=TOOLS, 
                               active_drag=self.activeDrag,
                               active_scroll=self.activeWheel,
                               plot_width=self.config.figWidth, 
                               plot_height=(self.config.figHeight), 
                               toolbar_location=self.config.toolsLocation
                               )
            bokehPlot.image_rgba(source=cds, image='image', x='x', y='y', dw='dw', dh='dh')
            bokehPlot.quad(top=max(yvals), bottom=min(yvals), 
                           left=min(xvals), right=max(xvals), 
                           alpha=0)
            bokehPlot.xaxis.axis_label = xlabel
            bokehPlot.yaxis.axis_label = ylabel
            
            self._setupPlotParameters(bokehPlot, plot_type="2D")
            
        elif type == '2D':
            # Unpacks data using a helper function
            zvals, xvals, xlabel, yvals, ylabel, cmap = self.presenter.get2DdataFromDictionary(dictionary=data,
                                                                                               dataType='plot',
                                                                                               plotType='2D',
                                                                                               compact=False)
            if testX:
                xvals, xlabel, __ = self.kda_test(xvals)
                
            if reshape:
                xlen = len(xvals)
                ylen = len(yvals)
                zvals = np.transpose(np.reshape(zvals, (xlen, ylen)))
                if zvals.shape[1] > 20000:
                    print("Have to subsample the grid")
                    zvals = zvals[:,::20].copy()
                    
            z_data = dict(image=[zvals], x=[min(xvals)], y=[min(yvals)],
                          dw=[max(xvals)-min(xvals)], 
                          dh=[max(yvals)-min(yvals)])
            
            cds = ColumnDataSource(data=z_data)
            colormap = cm.get_cmap(cmap) # choose any matplotlib colormap here
            bokehpalette = [colors.rgb2hex(m) for m in colormap(np.arange(colormap.N))]
            hoverTool = HoverTool(tooltips=[(xlabel, '$x{0}'), 
                                            (ylabel, '$y{0}'), 
                                            ('Intensity', '@image')],
                                point_policy = 'follow_mouse',
                                 )
            
            if len(data['tools']) > 0:
                # Enable current active tools
                self.activeDrag = data['tools']['tools']['activeDrag']
                self.activeWheel = data['tools']['tools']['activeWheel']
                # Check if toolset should include hover tool
                if data['tools']['tools']['hover']:
                    # Add tools + hover
                    TOOLS = [hoverTool, data['tools']['tools']['tools']]
                else:
                    # Add only tools
                    TOOLS = data['tools']['tools']['tools']
            elif self.hover_check.GetValue():  TOOLS = [hoverTool,self.tools]
            else: TOOLS = self.tools
            
            colorbar, colorMapper = None, None
            if addColorbar:
                zmin, zmax = np.round(np.min(zvals),2), np.round(np.max(zvals),2)
                zmid = np.round(np.max(zvals) /2.,2)
                if kwargs.get("modify_colorbar", False):
                    ticker = FixedTicker(ticks=[zmin, zmid, zmax])
                    formatter = FuncTickFormatter(code="""
                    data = {zmin: '0', zmid: '%', zmax: '100'}
                    return data[tick]
                    """.replace("zmin", str(zmin)).replace("zmid", str(zmid)).replace("zmax", str(zmax)))
                else:
                    ticker = AdaptiveTicker()
                    formatter = BasicTickFormatter(precision=self.config.interactive_colorbar_precision, 
                                                   use_scientific=self.config.interactive_colorbar_useScientific)
                colorMapper = LinearColorMapper(palette=bokehpalette, 
                                                 low=zmin, high=zmax)
                colorbar = ColorBar(color_mapper=colorMapper, 
                                    ticker=ticker,
                                    label_standoff = self.config.interactive_colorbar_label_offset,
                                    border_line_color = None, 
                                    location = (self.config.interactive_colorbar_offset_x,
                                                self.config.interactive_colorbar_offset_y),
                                    formatter=formatter,
                                    orientation=self.config.interactive_colorbar_orientation,
                                    width=self.config.interactive_colorbar_width,
                                    padding=self.config.interactive_colorbar_width)
            
            bokehPlot = figure(x_range=(min(xvals), max(xvals)), 
                               y_range=(min(yvals), max(yvals)),
                               tools=TOOLS, 
                               title=title,
                               active_drag=self.activeDrag,
                               active_scroll=self.activeWheel,
                               plot_width=self.config.figWidth, 
                               plot_height=(self.config.figHeight), 
                               toolbar_location=self.config.toolsLocation)
            bokehPlot.image(source=cds, image='image', x='x', y='y', dw='dw', dh='dh', palette=bokehpalette)
            if addColorbar:
                bokehPlot.add_layout(colorbar, self.config.interactive_colorbar_location)
            # setup labels
            bokehPlot.xaxis.axis_label = xlabel
            bokehPlot.yaxis.axis_label = ylabel
            
            # setup common parameters
            self._setupPlotParameters(bokehPlot, plot_type="2D")
                
        elif type == 'Unidec_barchart':
            xvals = data['xvals']
            yvals = data['yvals']
            labels = data['labels']
            colorList, molweight = [], []
            for color in data['colors']:
                colorList.append(convertRGB1toHEX(color))
            for mw in data['legend']:
                molweight.append(mw.split(" ")[1])
            legend = data['legend']
            source = ColumnDataSource(data=dict(xvals=labels, yvals=yvals,
                                                labels=labels, colors=colorList,
                                                legend=legend, mw=molweight))
            
            # Check if we should lock the hoverline
                
            hoverTool = HoverTool(tooltips = [("Component", '@labels'),
                                              ("Deconvoluted MW (Da)", '@mw'),
                                              ("Intensity", '@yvals')],
                                  mode='mouse') 

            # Prepare MS file
            if len(data['tools']) > 0:
                # Enable current active tools
                self.activeDrag = data['tools']['tools']['activeDrag']
                self.activeWheel = data['tools']['tools']['activeWheel']
                # Check if toolset should include hover tool
                if data['tools']['tools']['hover']:
                    # Add tools + hover
                    TOOLS = [hoverTool, data['tools']['tools']['tools']]
                else:
                    # Add only tools
                    TOOLS = data['tools']['tools']['tools']
            elif self.hover_check.GetValue():  
                TOOLS = [hoverTool,self.tools]
            else: TOOLS = self.tools

            bokehPlot = figure(x_range=labels, 
                               y_range=(0, max(yvals)*1.05),
                               tools=TOOLS,
                               active_drag=self.activeDrag,
                               active_scroll=self.activeWheel,
                               plot_width=self.config.figWidth1D, 
                               plot_height=(self.config.figHeight1D), 
                               toolbar_location=self.config.toolsLocation)
            bokehPlot.vbar(x='xvals', top='yvals', width=0.9, source=source, legend="legend",
                           fill_color="colors", line_color='white')

            # setup labels
            bokehPlot.yaxis.axis_label = ylabelIn
            # setup common parameters
            bokehPlot = self._setupPlotParameters(bokehPlot, plot_type="1D")

        elif type == 'UniDec_1D':
            
            _markers_map = {'o':"circle", 'v':"inverted_triangle", '^':"triangle", 
                            '>':"cross", 's':"square", 'd':"diamond", '*':"asterisk"}
            
            xvals = data['xvals']
            yvals = data['yvals']
            xlabelIn = data['xlabel']
            # Check if we should lock the hoverline
            if hover_vline:
                hoverMode='vline'
            else:
                hoverMode='mouse'
            # Prepare hover tool
            hoverTool = HoverTool(tooltips = [(xlabelIn, '@xvals{0.00}'),
                                              ("Offset Intensity", '@yvals{0.00}'),
                                              ("Label", "@label")],
                                  mode=hoverMode)
            # Prepare MS file
            if len(data['tools']) > 0:
                # Enable current active tools
                self.activeDrag = data['tools']['tools']['activeDrag']
                self.activeWheel = data['tools']['tools']['activeWheel']
                # Check if toolset should include hover tool
                if data['tools']['tools']['hover']:
                    # Add tools + hover
                    TOOLS = [hoverTool, data['tools']['tools']['tools']]
                else:
                    # Add only tools
                    TOOLS = data['tools']['tools']['tools']
            elif self.hover_check.GetValue():  
                TOOLS = [hoverTool,self.tools]
            else: TOOLS = self.tools
             
            bokehPlot = figure(x_range=(np.amin(np.ravel(xvals)), 
                                        np.amax(np.ravel(xvals))), 
                               tools=TOOLS,
                               active_drag=self.activeDrag,
                               active_scroll=self.activeWheel,
                               plot_width=self.config.figWidth, 
                               plot_height=(self.config.figHeight), 
                               toolbar_location=self.config.toolsLocation)
            # create dataframe
            source = ColumnDataSource(data=dict(xvals=xvals,
                                                yvals=yvals,
                                                label=(["Raw"]*len(xvals))))
            if not legend: label = None
            else: label = "Raw"

            bokehPlot.line(x="xvals", y="yvals", 
                           line_color="black", 
                           line_width=line_width,
                           line_alpha=line_alpha,
                           line_dash=line_style,
                           legend=label,
                           muted_alpha=self.config.interactive_legend_mute_alpha,
                           muted_color="black",
                           source=source)
                
            for key in data:
                if key.split(" ")[0] != "MW:": continue
                
                color = convertRGB1to255(data[key]['color'], as_integer=True, as_tuple=True)
                source = ColumnDataSource(data=dict(xvals=data[key]['line_xvals'],
                                                    yvals=data[key]['line_yvals'],
                                                    label=([data[key]['label']]*len(data[key]['line_xvals']))))
                if not legend: label = None
                else: label = data[key]['label']
                    
                bokehPlot.line(x="xvals", y="yvals", 
                               line_color=color, 
                               line_width=line_width,
                               line_alpha=line_alpha,
                               line_dash=line_style,
                               legend=label,
                               muted_alpha=self.config.interactive_legend_mute_alpha,
                               muted_color=color,
                               source=source)
                source = ColumnDataSource(data=dict(xvals=data[key]['scatter_xvals'],
                                                    yvals=data[key]['scatter_yvals'],
                                                    label=([data[key]['label']]*len(data[key]['scatter_xvals']))))
                bokehPlot.scatter("xvals", "yvals", 
                                  marker=_markers_map[data[key]['marker']], 
                                  size=10,
                                  source=source,
                                  line_color="black", 
                                  fill_color=color, 
                                  muted_color=color,
                                  muted_alpha=self.config.interactive_legend_mute_alpha,
                                  )
            # setup labels
            bokehPlot.xaxis.axis_label = xlabelIn
            bokehPlot.yaxis.axis_label = ylabelIn
            # setup common parameters
            bokehPlot = self._setupPlotParameters(bokehPlot, plot_type="Overlay_1D")

        elif type == 'UniDec_2D':
            # Unpacks data using a helper function
            zvals = data['grid'][:, 2]
            xvals = np.unique(data['grid'][:, 0])
            yvals = np.unique(data['grid'][:, 1])
            xlen = len(xvals)
            ylen = len(yvals)
            zvals = np.transpose(np.reshape(zvals, (xlen, ylen)))
            xlabel = data['xlabels']
            ylabel = data['ylabels']
            cmap = data['cmap']
            
            if zvals.shape[1] > 20000:
                print("Have to subsample the grid")
                zvals = zvals[:,::10].copy()            
            
            if testX:
                xvals, xlabel, __ = self.kda_test(xvals)
                
            z_data = dict(image=[zvals], x=[min(xvals)], y=[min(yvals)],
                          dw=[max(xvals)-min(xvals)], 
                          dh=[max(yvals)-min(yvals)])
            
            cds = ColumnDataSource(data=z_data)
            colormap = cm.get_cmap(cmap) # choose any matplotlib colormap here
            bokehpalette = [colors.rgb2hex(m) for m in colormap(np.arange(colormap.N))]
            zmin, zmax = np.round(np.min(zvals),2), np.round(np.max(zvals),2)
            colorMapper = LinearColorMapper(palette=bokehpalette, low=zmin, high=zmax)
            hoverTool = HoverTool(tooltips=[(xlabel, '$x{0}'), 
                                            (ylabel, '$y{0}'), 
                                            ('Intensity', '@image')],
                                point_policy = 'follow_mouse',
                                 )
            
            if len(data['tools']) > 0:
                # Enable current active tools
                self.activeDrag = data['tools']['tools']['activeDrag']
                self.activeWheel = data['tools']['tools']['activeWheel']
                # Check if toolset should include hover tool
                if data['tools']['tools']['hover']:
                    # Add tools + hover
                    TOOLS = [hoverTool, data['tools']['tools']['tools']]
                else:
                    # Add only tools
                    TOOLS = data['tools']['tools']['tools']
            elif self.hover_check.GetValue():  TOOLS = [hoverTool,self.tools]
            else: TOOLS = self.tools
            
            colorbar = None 
            if addColorbar:
                zmid = np.round(np.max(zvals) /2.,2)
                ticker = FixedTicker(ticks=[zmin, zmid, zmax])
                formatter = FuncTickFormatter(code="""
                data = {zmin: '0', zmid: '%', zmax: '100'}
                return data[tick]
                """.replace("zmin", str(zmin)).replace("zmid", str(zmid)).replace("zmax", str(zmax)))
                colorbar = ColorBar(color_mapper=colorMapper, 
                                    ticker=ticker,
                                    label_standoff=self.config.interactive_colorbar_label_offset,
#                                     border_line_color = None, 
                                    location = (self.config.interactive_colorbar_offset_x,
                                                self.config.interactive_colorbar_offset_y),
                                    formatter=formatter,
                                    orientation=self.config.interactive_colorbar_orientation,
#                                     border_line_color="firebrick",
                                    border_line_width=50,
                                    width=self.config.interactive_colorbar_width,
                                    padding=self.config.interactive_colorbar_width)
            
            bokehPlot = figure(x_range=(min(xvals), max(xvals)), 
                               y_range=(min(yvals), max(yvals)),
                               tools=TOOLS, 
                               active_drag=self.activeDrag,
                               active_scroll=self.activeWheel,
                               plot_width=self.config.figWidth, 
                               plot_height=(self.config.figHeight), 
                               toolbar_location=self.config.toolsLocation)

            bokehPlot.image(source=cds, image='image', x='x', y='y', dw='dw', dh='dh', color_mapper=colorMapper)
            
            if addColorbar:
                bokehPlot.add_layout(colorbar, self.config.interactive_colorbar_location)
                
            # setup labels
            bokehPlot.xaxis.axis_label = xlabel
            bokehPlot.yaxis.axis_label = ylabel
            
            # setup common parameters
            self._setupPlotParameters(bokehPlot, plot_type="2D")
                
        elif type == 'Matrix':
            zvals, yxlabels, cmap = self.presenter.get2DdataFromDictionary(dictionary=data,
                                                                           plotType='Matrix',
                                                                           compact=False)
            zvals = np.rot90(np.fliplr(zvals))
            colormap =cm.get_cmap(cmap) # choose any matplotlib colormap here
            bokehpalette = [colors.rgb2hex(m) for m in colormap(np.arange(colormap.N))]
            xlabel = 'Labels:'
            ylabel = u'RMSD (%):'
            hoverTool = HoverTool(tooltips = [(xlabel, '@xname, @yname'),
                                              (ylabel, '@count{0.00}')],
                                 point_policy = 'follow_mouse')
            # Add tools
            if len(data['tools']) > 0:
                # Enable current active tools
                self.activeDrag = data['tools']['tools']['activeDrag']
                self.activeWheel = data['tools']['tools']['activeWheel']
                # Check if toolset should include hover tool
                if data['tools']['tools']['hover']:
                    # Add tools + hover
                    TOOLS = [hoverTool, data['tools']['tools']['tools']]
                else:
                    # Add only tools
                    TOOLS = data['tools']['tools']['tools']
            elif self.hover_check.GetValue():  TOOLS = [hoverTool,self.tools]
            else: TOOLS = self.tools
            # Assemble data into appropriate format
            xname, yname, color, alpha = [], [], [], []
            # Rescalling parameters
            old_min = np.min(zvals)
            old_max = np.max(zvals)
            new_min = 0
            new_max = len(bokehpalette) -1
            if len(set(yxlabels)) == 1:
                msg = 'Exporting RMSD Matrix to a HTML file is only possible with full list of x/y-axis labels.\n' + \
                      'Please add those to the file and try repeating.'
                dialogs.dlgBox(exceptionTitle='No file name', 
                               exceptionMsg= msg,
                               type="Error")
                return None
            else:
                for i, namex in enumerate(yxlabels):
                    for j, namey in enumerate(yxlabels):
                        xname.append(namex)
                        yname.append(namey)
                        new_value = ((zvals[i,j] - old_min)/(old_max - old_min))*(new_max - new_min)+new_min
                        color.append(bokehpalette[int(new_value)])
                        alpha.append(min(zvals[i,j]/3.0, 0.9) + 0.1)
                    
            # Create data source
            source = ColumnDataSource(data=dict(xname=xname, yname=yname,
                                                count=zvals.flatten(),
                                                alphas=alpha, colors=color))
            
            bokehPlot = figure(x_range=list(reversed(yxlabels)), 
                               y_range=yxlabels,
                               tools=TOOLS, 
                               active_drag=self.activeDrag,
                               active_scroll=self.activeWheel,
                               plot_width=self.config.figWidth, 
                               plot_height=(self.config.figHeight), 
                               toolbar_location=self.config.toolsLocation)
            bokehPlot.rect('xname', 'yname', 1, 1, 
                           source=source, line_color=None, 
                           hover_line_color='black',
                           alpha='alphas', hover_color='colors',
                           color='colors')
            bokehPlot = self._setupPlotParameters(bokehPlot, plot_type="Matrix")
           
        elif type == 'RMSD':
            zvals, xvals, xlabel, yvals, ylabel, rmsdLabel, cmap = self.presenter.get2DdataFromDictionary(dictionary=data,
                                                                                                            plotType='RMSD',
                                                                                                            compact=True)
            z_data = dict(image=[zvals], x=[min(xvals)], y=[min(yvals)],
                          dw=[max(xvals)-min(xvals)], 
                          dh=[max(yvals)-min(yvals)])
            cds = ColumnDataSource(data=z_data)
            
            # Calculate position of RMSD label
            rmsdXpos, rmsdYpos = self.presenter.onCalculateRMSDposition(xlist=xvals,
                                                                        ylist=yvals)
            
            colormap =cm.get_cmap(cmap) # choose any matplotlib colormap here
            bokehpalette = [colors.rgb2hex(m) for m in colormap(np.arange(colormap.N))]
            hoverTool = HoverTool(tooltips = [(xlabel, '$x{0}'),
                                              (ylabel, '$y{0}'),
                                              ('Intensity', '@image')],
                                  point_policy = 'follow_mouse')
            colorbar, colorMapper = None, None
            if addColorbar:
                zmin, zmax = np.round(np.min(zvals),2), np.round(np.max(zvals),2)
                if kwargs.get("modify_colorbar", True):
                    ticker = FixedTicker(ticks=[-1., 0., 1.])
                    formatter = BasicTickFormatter(precision=self.config.interactive_colorbar_precision, 
                                                   use_scientific=self.config.interactive_colorbar_useScientific)
                else:
                    ticker = AdaptiveTicker()
                    formatter = BasicTickFormatter(precision=self.config.interactive_colorbar_precision, 
                                                   use_scientific=self.config.interactive_colorbar_useScientific)
                colorMapper = LinearColorMapper(palette=bokehpalette, 
                                                 low=zmin, high=zmax)
                colorbar = ColorBar(color_mapper=colorMapper, 
                                    ticker=ticker,
                                    label_standoff = self.config.interactive_colorbar_label_offset,
                                    border_line_color = None, 
                                    location = (self.config.interactive_colorbar_offset_x,
                                                self.config.interactive_colorbar_offset_y),
                                    formatter=formatter,
                                    orientation=self.config.interactive_colorbar_orientation,
                                    width=self.config.interactive_colorbar_width,
                                    padding=self.config.interactive_colorbar_width)
            
            # Add tools
            if len(data['tools']) > 0:
                # Enable current active tools
                self.activeDrag = data['tools']['tools']['activeDrag']
                self.activeWheel = data['tools']['tools']['activeWheel']
                # Check if toolset should include hover tool
                if data['tools']['tools']['hover']:
                    # Add tools + hover
                    TOOLS = [hoverTool, data['tools']['tools']['tools']]
                else:
                    # Add only tools
                    TOOLS = data['tools']['tools']['tools']
            elif self.hover_check.GetValue():  TOOLS = [hoverTool,self.tools]
            else: TOOLS = self.tools
            bokehPlot = figure(x_range=(min(xvals), max(xvals)), 
                               y_range=(min(yvals), max(yvals)),
                               tools=TOOLS, 
                               active_drag=self.activeDrag,
                               active_scroll=self.activeWheel,
                               plot_width=self.config.figWidth, 
                               plot_height=(self.config.figHeight), 
                               toolbar_location=self.config.toolsLocation)
            bokehPlot.image(source=cds, image='image', x='x', y='y', dw='dw', dh='dh', palette=bokehpalette)
            # Add RMSD label to the plot
            textColor = convertRGB1to255(self.config.interactive_annotation_color, as_integer=True, as_tuple=True)  
            backgroundColor = convertRGB1to255(self.config.interactive_annotation_background_color, as_integer=True, as_tuple=True)  
            rmsdAnnot = Label(x=rmsdXpos, y=rmsdYpos, x_units='data', y_units='data',
                             text=rmsdLabel, render_mode='canvas', 
                             text_color = textColor,
                             text_font_size=self._fontSizeConverter(self.config.interactive_annotation_fontSize),
                             text_font_style=self._fontWeightConverter(self.config.interactive_annotation_weight),
                             background_fill_color=backgroundColor, 
                             background_fill_alpha=self.config.interactive_annotation_alpha)
            bokehPlot.add_layout(rmsdAnnot)
            if addColorbar:
                bokehPlot.add_layout(colorbar, self.config.interactive_colorbar_location)
            
            bokehPlot.xaxis.axis_label = xlabel
            bokehPlot.yaxis.axis_label = ylabel
            bokehPlot = self._setupPlotParameters(bokehPlot, plot_type="2D")
            
        elif type == 'RMSF':
            zvals, yvalsRMSF, xvals, yvals, xlabelRMSD, ylabelRMSD, ylabelRMSF, color, cmap, rmsdLabel = self.presenter.get2DdataFromDictionary(dictionary=data,
                                                                                                                          plotType='RMSF',
                                                                                                                          compact=True)
            if hover_vline:
                hoverMode='vline'
            else:
                hoverMode='mouse'
            
            ylabelRMSF = ''.join([ylabelRMSF]) 
            
            hoverToolRMSF = HoverTool(tooltips = [(xlabelRMSD, '$x{0.00}'),
                                                  (ylabelRMSF, '$y{0.00}')],
                                      mode=hoverMode) 
             
            # Add tools
            if len(data['tools']) > 0:
                # Enable current active tools
                self.activeDrag = data['tools']['tools']['activeDrag']
                self.activeWheel = data['tools']['tools']['activeWheel']
                # Check if toolset should include hover tool
                if data['tools']['tools']['hover']:
                    # Add tools + hover
                    TOOLS_RMSF = [hoverToolRMSF, data['tools']['tools']['tools']]
                else:
                    # Add only tools
                    TOOLS_RMSF = data['tools']['tools']['tools']
            elif self.hover_check.GetValue():  TOOLS_RMSF = [hoverToolRMSF,self.tools]
            else: TOOLS_RMSF = self.tools
            bokehPlotRMSF = figure(x_range=(min(xvals), max(xvals)), 
                               y_range=(min(yvalsRMSF), max(yvalsRMSF)),
                               tools=TOOLS_RMSF,
                               active_drag=self.activeDrag,
                               active_scroll=self.activeWheel,
                               plot_width=self.config.figWidth1D, 
                               plot_height=(self.config.figHeight1D), 
                               toolbar_location=self.config.toolsLocation)
            color = convertRGB1to255(color, as_integer=True, as_tuple=True)
            bokehPlotRMSF.line(xvals, yvalsRMSF, 
                               line_color=color,
                               line_width=line_width,
                               line_alpha=line_alpha)
            bokehPlotRMSF.yaxis.axis_label = ylabelRMSF
            bokehPlotRMSF = self._setupPlotParameters(bokehPlotRMSF, plot_type="RMSF")
            
            z_data = dict(image=[zvals], x=[min(xvals)], y=[min(yvals)],
                          dw=[max(xvals)-min(xvals)], 
                          dh=[max(yvals)-min(yvals)])
            cds = ColumnDataSource(data=z_data)

            # Calculate position of RMSD label
            rmsdXpos, rmsdYpos = self.presenter.onCalculateRMSDposition(xlist=xvals,
                                                                        ylist=yvals)
            colormap =cm.get_cmap(cmap) # choose any matplotlib colormap here
            bokehpalette = [colors.rgb2hex(m) for m in colormap(np.arange(colormap.N))]
            hoverTool = HoverTool(tooltips = [(xlabelRMSD, '$x{0.00}'),
                                              (ylabelRMSD, '$y{0.00}'),
                                              ('Intensity', '@image')],
                                 point_policy = 'follow_mouse')
            colorbar, colorMapper = None, None
            if addColorbar:
                zmin, zmax = np.round(np.min(zvals),2), np.round(np.max(zvals),2)
                zmid = np.round(np.max(zvals) /2.,2)
                if kwargs.get("modify_colorbar", False):
                    ticker = FixedTicker(ticks=[zmin, zmid, zmax])
                    formatter = FuncTickFormatter(code="""
                    data = {zmin: '0', zmid: '%', zmax: '100'}
                    return data[tick]
                    """.replace("zmin", str(zmin)).replace("zmid", str(zmid)).replace("zmax", str(zmax)))
                else:
                    ticker = AdaptiveTicker()
                    formatter = BasicTickFormatter(precision=self.config.interactive_colorbar_precision, 
                                                   use_scientific=self.config.interactive_colorbar_useScientific)
                colorMapper = LinearColorMapper(palette=bokehpalette, 
                                                 low=zmin, high=zmax)
                colorbar = ColorBar(color_mapper=colorMapper, 
                                    ticker=ticker,
                                    label_standoff = self.config.interactive_colorbar_label_offset,
                                    border_line_color = None, 
                                    location = (self.config.interactive_colorbar_offset_x,
                                                self.config.interactive_colorbar_offset_y),
                                    formatter=formatter,
                                    orientation=self.config.interactive_colorbar_orientation,
                                    width=self.config.interactive_colorbar_width,
                                    padding=self.config.interactive_colorbar_width)
        
            # Add tools
            if len(data['tools']) > 0:
                # Enable current active tools
                self.activeDrag = data['tools']['tools']['activeDrag']
                self.activeWheel = data['tools']['tools']['activeWheel']
                # Check if toolset should include hover tool
                if data['tools']['tools']['hover']:
                    # Add tools + hover
                    TOOLS = [hoverTool, data['tools']['tools']['tools']]
                else:
                    # Add only tools
                    TOOLS = data['tools']['tools']['tools']
            elif self.hover_check.GetValue():  TOOLS = [hoverTool,self.tools]
            else: TOOLS = self.tools
            if linkXYAxes: 
                bokehPlotRMSD = figure(x_range=bokehPlotRMSF.x_range, 
                                   y_range=(min(yvals), max(yvals)),
                                   tools=TOOLS, 
                                   active_drag=self.activeDrag,
                                   active_scroll=self.activeWheel,
                                   plot_width=self.config.figWidth1D, 
                                   plot_height=(self.config.figHeight), 
                                   toolbar_location=self.config.toolsLocation)
            else:
                bokehPlotRMSD = figure(x_range=(min(xvals), max(xvals)), 
                                   y_range=(min(yvals), max(yvals)),
                                   tools=TOOLS, 
                                   active_drag=self.activeDrag,
                                   active_scroll=self.activeWheel,
                                   plot_width=self.config.figWidth1D, 
                                   plot_height=(self.config.figHeight), 
                                   toolbar_location=self.config.toolsLocation)

            bokehPlotRMSD.image(source=cds, image='image', x='x', y='y', dw='dw', dh='dh', palette=bokehpalette)
            # Add RMSD label to the plot
            textColor = convertRGB1to255(self.config.interactive_annotation_color, as_integer=True, as_tuple=True)
            backgroundColor = convertRGB1to255(self.config.interactive_annotation_background_color, as_integer=True, as_tuple=True)  
            rmsdAnnot = Label(x=rmsdXpos, y=rmsdYpos, x_units='data', y_units='data',
                             text=rmsdLabel, 
                             render_mode='canvas', 
                             text_color = textColor,
                             text_font_size=self._fontSizeConverter(self.config.interactive_annotation_fontSize),
                             text_font_style=self._fontWeightConverter(self.config.interactive_annotation_weight),
                             background_fill_color=backgroundColor, 
                             background_fill_alpha=self.config.interactive_annotation_alpha)
            bokehPlotRMSD.add_layout(rmsdAnnot)
            if addColorbar:
                bokehPlotRMSD.add_layout(colorbar, self.config.interactive_colorbar_location)
            
            bokehPlotRMSD.xaxis.axis_label = xlabelRMSD
            bokehPlotRMSD.yaxis.axis_label = ylabelRMSD
            bokehPlotRMSD = self._setupPlotParameters(bokehPlotRMSD, plot_type="2D")
            
            bokehPlot =  gridplot([[bokehPlotRMSF], [bokehPlotRMSD]])
         
        elif type == 'Overlay':
            """
            This method is only for the overlay type plot
            """
            (zvals1, zvals2, cmapIon1, cmapIon2, alphaIon1, alphaIon2, xvals,
             xlabel, yvals, ylabel, charge1, charge2)  = self.presenter.get2DdataFromDictionary(dictionary=data,
                                                                                               dataType='plot',
                                                                                               plotType='Overlay',
                                                                                               compact=False)
            if subtype == 'Mask':
                zvals1 = zvals1.filled(0)
                zvals2 = zvals2.filled(0)
            
            if self.config.interactive_override_defaults:
                cmapIon1 = interactive_params.get('overlay_color_1', cmapIon1) 
                cmapIon2 = interactive_params.get('overlay_color_2', cmapIon2)
                linkXYAxes = overlay_linkXY
                layout = overlay_layout
                 
            colormap =cm.get_cmap(cmapIon1) 
            bokehpalette1 = [colors.rgb2hex(m) for m in colormap(np.arange(colormap.N))]
            hoverTool1 = HoverTool(tooltips = [(xlabel, '$x{0}'),
                                               (ylabel, '$y{0}')],
                                 point_policy = 'follow_mouse')
            # Add tools
            if len(data['tools']) > 0:
                # Enable current active tools
                self.activeDrag = data['tools']['tools']['activeDrag']
                self.activeWheel = data['tools']['tools']['activeWheel']
                # Check if toolset should include hover tool
                if data['tools']['tools']['hover']:
                    TOOLS1 = [hoverTool1, data['tools']['tools']['tools']]
                else:
                    # Add only tools
                    TOOLS1 = data['tools']['tools']['tools']
            elif self.hover_check.GetValue():  TOOLS1 = [hoverTool1,self.tools] 
            else: TOOLS1 = self.tools

            leftPlot = figure(x_range=(min(xvals), max(xvals)), 
                               y_range=(min(yvals), max(yvals)),
                               tools=TOOLS1, 
                               active_drag=self.activeDrag,
                               active_scroll=self.activeWheel,
                               plot_width=self.config.figWidth, plot_height=(self.config.figHeight), 
                               toolbar_location=self.config.toolsLocation)
            leftPlot.image(image=[zvals1], x=min(xvals), 
                            y=min(yvals), dw=max(xvals), 
                            dh=max(yvals), palette=bokehpalette1)
            leftPlot.quad(top=max(yvals), bottom=min(yvals), 
                           left=min(xvals), right=max(xvals), 
                           alpha=0)            
            
            colormap =cm.get_cmap(cmapIon2) 
            bokehpalette2 = [colors.rgb2hex(m) for m in colormap(np.arange(colormap.N))]
            hoverTool2 = HoverTool(tooltips = [(xlabel, '$x{0}'),
                                              (ylabel, '$y{0}')],
                                 point_policy = 'follow_mouse')            
            # Add tools
            if len(data['tools']) > 0:
                # Enable current active tools
                self.activeDrag = data['tools']['tools']['activeDrag']
                self.activeWheel = data['tools']['tools']['activeWheel']
                # Check if toolset should include hover tool
                if data['tools']['tools']['hover']:
                    TOOLS2 = [hoverTool2, data['tools']['tools']['tools']]
                else:
                    # Add only tools
                    TOOLS2 = data['tools']['tools']['tools']
            elif self.hover_check.GetValue():  TOOLS2 = [hoverTool2,self.tools] 
            else: TOOLS2 = self.tools
            
            if linkXYAxes: 
                rightPlot = figure(x_range=leftPlot.x_range,
                                   y_range=leftPlot.y_range,
                                   tools=TOOLS2, 
                                   active_drag="box_zoom", 
                                   plot_width=self.config.figWidth, plot_height=(self.config.figHeight), 
                                   toolbar_location=self.config.toolsLocation)
            else:
                rightPlot = figure(x_range=(min(xvals), max(xvals)), 
                                   y_range=(min(yvals), max(yvals)),
                                   tools=TOOLS2, 
                                   active_drag="box_zoom", 
                                   plot_width=self.config.figWidth, 
                                   plot_height=(self.config.figHeight), 
                                   toolbar_location=self.config.toolsLocation)
                
            rightPlot.image(image=[zvals2], x=min(xvals), 
                            y=min(yvals), dw=max(xvals), 
                            dh=max(yvals), palette=bokehpalette2)
            rightPlot.quad(top=max(yvals), bottom=min(yvals), 
                           left=min(xvals), right=max(xvals), 
                           alpha=0)
            
            for plot in [leftPlot, rightPlot]:
                plot.outline_line_width = self.config.interactive_outline_width
                plot.outline_line_alpha = self.config.interactive_outline_alpha  
                plot.outline_line_color = "black"
                plot.min_border_right = self.config.interactive_border_min_right
                plot.min_border_left = self.config.interactive_border_min_left
                plot.min_border_top = self.config.interactive_border_min_top
                plot.min_border_bottom = self.config.interactive_border_min_bottom
            
            if layout=='Rows':
                for plot in [leftPlot, rightPlot]:
                    plot.xaxis.axis_label = xlabel
                    plot.xaxis.axis_label_text_font_size = self._fontSizeConverter(self.config.interactive_label_fontSize)
                    plot.xaxis.axis_label_text_font_style = self._fontWeightConverter(self.config.interactive_label_weight)
                    plot.xaxis.major_label_text_font_size = self._fontSizeConverter(self.config.interactive_tick_fontSize)
                leftPlot.yaxis.axis_label = ylabel
                leftPlot.yaxis.axis_label_text_font_size = self._fontSizeConverter(self.config.interactive_label_fontSize)
                leftPlot.yaxis.major_label_text_font_size = self._fontSizeConverter(self.config.interactive_tick_fontSize)
                leftPlot.yaxis.axis_label_text_font_style =  self._fontWeightConverter(self.config.interactive_label_weight)
                # Remove tick values from right plot
                rightPlot.yaxis.major_label_text_color = None  # turn off y-axis tick labels leaving space 
                bokehPlot =  gridplot([[leftPlot, rightPlot]])
            elif layout=='Columns':
                for plot in [leftPlot, rightPlot]:
                    plot.yaxis.axis_label = ylabel
                    plot.yaxis.axis_label_text_font_size = self._fontSizeConverter(self.config.interactive_label_fontSize)
                    plot.yaxis.major_label_text_font_size = self._fontSizeConverter(self.config.interactive_tick_fontSize)
                    plot.yaxis.axis_label_text_font_style =  self._fontWeightConverter(self.config.interactive_label_weight)
                leftPlot.xaxis.major_label_text_color = None  # turn off y-axis tick labels leaving space 
                rightPlot.xaxis.axis_label = xlabel
                rightPlot.xaxis.axis_label_text_font_size = self._fontSizeConverter(self.config.interactive_label_fontSize)
                rightPlot.xaxis.axis_label_text_font_style =  self._fontWeightConverter(self.config.interactive_label_weight)
                rightPlot.xaxis.major_label_text_font_size = self._fontSizeConverter(self.config.interactive_tick_fontSize)
                bokehPlot =  gridplot([[leftPlot], [rightPlot]])
        
        return bokehPlot
        
    def onGenerateHTML(self, evt):
        """
        Generate plots for HTML output
        """
         
        plotList = []
         
        if self.currentPath == None:
            try:
                msg = 'Please select file name'
                dialogs.dlgBox(exceptionTitle='No file name', 
                               exceptionMsg= msg,
                               type="Error")
                self.onGetSavePath(evt=None)
            except: 
                msg = 'Please select a path to save the file before continuing'
                self.view.SetStatusText(msg, 3)
                return
            
        # First, lets check how many pages are present in the selected item list
        listOfPages = []
        for item in xrange(self.itemsList.GetItemCount()):
            if self.itemsList.IsChecked(index=item):
                listOfPages.append(self.itemsList.GetItem(item,self.config.interactiveColNames['page']).GetText())
                
        listOfPages = list(set(listOfPages))
        
        # This dictionary acts as a temporary holding space for each
        # individual plot
        plotDict = {}
        # Pre-populate the dictionary with keys
        for key in listOfPages:
            plotDict[key] = []
            
        # Sort the list based on which page each item belongs to
        if len(listOfPages) > 1:
            self.OnSortByColumn(column=self.config.interactiveColNames['order'])

        if len(listOfPages) == 0:
            msg = 'Please select items to plot'
            dialogs.dlgBox(exceptionTitle='No plots were selected', 
                           exceptionMsg= msg,
                           type="Warning")
        
        for item in xrange(self.itemsList.GetItemCount()):
            if self.itemsList.IsChecked(index=item):
                # Disabled in v1.0.5 as it was always overriding title, header and other information = should have known better...
#                 self.onAnnotateItems(evt=None, itemID=item)
                name = self.itemsList.GetItem(item,self.config.interactiveColNames['document']).GetText()
                key = self.itemsList.GetItem(item,self.config.interactiveColNames['type']).GetText()
                innerKey = self.itemsList.GetItem(item,self.config.interactiveColNames['file']).GetText()
                pageTable = self.itemsList.GetItem(item,self.config.interactiveColNames['page']).GetText()
                data = self.getItemData(name, key, innerKey)
                title = data['title']
                header = data['header']
                footnote = data['footnote']
                page = data['page']
                colorbar = data['colorbar']
                                
                # Check that the page names agree. If they don't, the table page
                # name takes priority as it has been pre-emptively added to the
                # plotDict dictionary
                if pageTable != page['name']:
                    msg = 'Overriding page name'
                    self.view.SetStatusText(msg, 3)
                    page = self.config.pageDict[pageTable] 
                    
                if title == '':
                    if innerKey != '':
                        title = innerKey
                    else:
                        title = key
                 
                if any(key in itemType for itemType in ['MS', 'MS, multiple', 
                                                        'RT', 'RT, multiple', 'RT, combined', 
                                                        '1D', '1D, multiple']):
                    width = self.config.figWidth1D
                else:
                    width = self.config.figWidth 
                
                # Generate header and footnote information
                divHeader = Div(text=(header), width=width)
                markupHeader = widgetbox(divHeader, width=width)
                divFootnote = Div(text=str(footnote), width=width)
                markupFootnote = widgetbox(divFootnote, width=width)
                
                bokehPlot = None
                # Now generate plot         
                if key in ['MS', 'MS, multiple', 'Processed MS']:
                    bokehPlot = self.prepareDataForInteractivePlots(data=data, 
                                                                    type='MS', 
                                                                    title=title,
                                                                    xlabelIn='m/z',
                                                                    ylabelIn='Intensity')
                elif key in ['UniDec', 'UniDec, multiple', "UniDec, processed"]:
                    if key == "UniDec, multiple":
                        innerKey = re.split(' \| ', innerKey)[0]
                    
                    if innerKey == 'Processed':
                        bokehPlot = self.prepareDataForInteractivePlots(data=data, 
                                                                        type='MS', 
                                                                        title=title,
                                                                        xlabelIn='m/z (Da)',
                                                                        ylabelIn='Intensity')
                    elif innerKey == 'MW distribution':
                        bokehPlot = self.prepareDataForInteractivePlots(data=data, 
                                                                        type='MS', 
                                                                        testX=True,
                                                                        title=title,
                                                                        xlabelIn='m/z (Da)',
                                                                        ylabelIn='Intensity')
                    elif innerKey == 'Fitted':
                        bokehPlot = self.prepareDataForInteractivePlots(data=data, 
                                                                        type='Overlay_1D', 
                                                                        title=title,
                                                                        ylabelIn='Intensity')
                    elif innerKey == 'MW vs Charge':
                        kwargs = {'modify_colorbar':True}
                        bokehPlot = self.prepareDataForInteractivePlots(data=data, 
                                                                        type='2D', 
                                                                        testX=True,
                                                                        reshape=True,
                                                                        title=title,
                                                                        addColorbar=True,
                                                                        **kwargs)
                    elif innerKey == 'm/z vs Charge':
                        bokehPlot = self.prepareDataForInteractivePlots(data=data, 
                                                                        type='UniDec_2D', 
                                                                        title=title,
                                                                        addColorbar=True)
                    elif innerKey == 'Barchart':
                        bokehPlot = self.prepareDataForInteractivePlots(data=data, 
                                                                        type='Unidec_barchart', 
                                                                        ylabelIn='Intensity',
                                                                        title=title)
                    elif innerKey == 'm/z with isolated species':
                        bokehPlot = self.prepareDataForInteractivePlots(data=data, 
                                                                        type='UniDec_1D', 
                                                                        title=title,
                                                                        ylabelIn='Intensity')
                        
                elif key in ['1D', '1D, multiple']:
                    bokehPlot = self.prepareDataForInteractivePlots(data=data, 
                                                                    type='1D', 
                                                                    title=title,
                                                                    ylabelIn='Intensity')
                    
                     
                elif key in ['RT', 'RT, multiple', 'RT, combined']:
                    bokehPlot = self.prepareDataForInteractivePlots(data=data, 
                                                                    type='RT', 
                                                                    title=title,
                                                                    ylabelIn='Intensity')
                     
                elif key =='2D' or key == '2D, combined' or key == '2D, processed':
                    bokehPlot = self.prepareDataForInteractivePlots(data=data, 
                                                                    type='2D', 
                                                                    title=title,
                                                                    addColorbar=colorbar)

                elif key =='Overlay':
                    overlayMethod = re.split('-|,|:|__', innerKey)
                    if overlayMethod[0] == 'Mask' or overlayMethod[0] == 'Transparent':
                        bokehPlot = self.prepareDataForInteractivePlots(data=data, 
                                                                        type='Overlay', 
                                                                        subtype=overlayMethod[0],
                                                                        title=title,
                                                                        linkXYAxes=self.config.linkXYaxes,
                                                                        layout=self.config.plotLayoutOverlay)
                    elif overlayMethod[0] == 'RMSF': 
                        kwargs = {'modify_colorbar':True}
                        bokehPlot = self.prepareDataForInteractivePlots(data=data, 
                                                                        type='RMSF', 
                                                                        linkXYAxes=self.config.linkXYaxes,
                                                                        title=title,
                                                                        addColorbar=colorbar,
                                                                        **kwargs)
                    elif overlayMethod[0] == 'RMSD': 
                        kwargs = {'modify_colorbar':True}
                        bokehPlot = self.prepareDataForInteractivePlots(data=data, 
                                                                        type='RMSD', 
                                                                        title=title,
                                                                        addColorbar=colorbar,
                                                                        **kwargs)
                    elif overlayMethod[0] in ['1D', 'RT']:
                        bokehPlot = self.prepareDataForInteractivePlots(data=data, 
                                                                        type='Overlay_1D', 
                                                                        title=title,
                                                                        ylabelIn='Intensity')
                    elif overlayMethod[0] == 'RGB':
                        bokehPlot = self.prepareDataForInteractivePlots(data=data, 
                                                                        type='RGB', 
                                                                        title=title)
                    elif overlayMethod[0] == 'Grid (2':
                        bokehPlot = self.prepareDataForInteractivePlots(data=data, 
                                                                        type='Grid', 
                                                                        title=title)
                    elif overlayMethod[0] == "Grid (n x n)":
                        bokehPlot = self.prepareDataForInteractivePlots(data=data, 
                                                                        type='Grid_NxN', 
                                                                        title=title)
                    elif overlayMethod[0] in ["Waterfall (Raw)", "Waterfall (Processed)", "Waterfall (Fitted)",
                                              "Waterfall (Deconvoluted MW)", "Waterfall (Charge states)"]:
                        bokehPlot = self.prepareDataForInteractivePlots(data=data, 
                                                                        type='Waterfall', 
                                                                        testX=True,
                                                                        title=title)
                    else:
                        msg = "Cannot export '%s - %s (%s)' in an interactive format yet - it will be available in the future updates. For now, please deselect it in the table. LM" % (overlayMethod[0], key, innerKey)
                        dialogs.dlgBox(exceptionTitle='Not supported yet', 
                                       exceptionMsg= msg,
                                       type="Error")
                        continue
                elif key == 'Statistical':
                    overlayMethod = re.split('-|,|:|__', innerKey)
                    if (overlayMethod[0] == 'Variance' or 
                        overlayMethod[0] == 'Mean' or 
                        overlayMethod[0] == 'Standard Deviation'):
                        bokehPlot = self.prepareDataForInteractivePlots(data=data, 
                                                                        type='2D', 
                                                                        title=title,
                                                                        addColorbar=colorbar)
                    elif overlayMethod[0] == 'RMSD Matrix': 
                        bokehPlot = self.prepareDataForInteractivePlots(data=data, 
                                                                        type='Matrix', 
                                                                        title=title)
                    else: pass
                     
                else:
                    msg = "Cannot export '%s (%s)' in an interactive format yet - it will be available in the future updates. For now, please deselect it in the table. LM" % (key, innerKey)
                    dialogs.dlgBox(exceptionTitle='Not supported yet', 
                                   exceptionMsg= msg,
                                   type="Error")
                    continue
                     
                if bokehPlot == None: 
                    print("%s - %s plot was returned empty. Skipping") % (key, innerKey)
                    continue
                
                # Generate layout
                divWatermark = Div(text=str(self.config.watermark), width=width+50)
                markupWatermark = widgetbox(divWatermark, width=width+50)
                
                if page['layout'] == 'Individual':
                    bokehLayout = layout([markupHeader],
                                         [bokehPlot], 
                                         [markupFootnote], 
                                        [markupWatermark],
                                         sizing_mode='fixed', 
                                         width=width+50)
                else:
                    bokehLayout = layout([markupHeader],
                                         [bokehPlot], 
                                         [markupFootnote], 
    #                                      [markupWatermark],
                                         sizing_mode='fixed', 
                                         width=width+50)
                # Add to plot dictionary
                if page['layout'] == 'Individual':
                    bokehTab = Panel(child=bokehLayout, title=title)           
                    plotDict[page['name']].append(bokehTab)
                    plotList.append(bokehTab)
                elif page['layout'] == 'Rows':  
                    plotDict[page['name']].append(bokehLayout)
                    plotList.append(bokehLayout)
                elif page['layout'] == 'Columns':    
                    plotDict[page['name']].append(bokehLayout)
                    plotList.append(bokehLayout)
                elif page['layout'] == 'Grid': 
                    plotDict[page['name']].append(bokehLayout)
                    plotList.append(bokehLayout)
                    
                print("Added {} - {} ({}) to the HTML file".format(key, innerKey, name))
        
        outList = []
        for pageKey in plotDict:
            if self.config.pageDict[pageKey]['layout'] == 'Individual':
                if len(plotDict[pageKey]) > 1:
                    for plot in range(len(plotDict[pageKey])):
                        outList.append(plotDict[pageKey][plot])
                elif len(plotDict[pageKey]) == 0:
                    msg = "The list of plots is empty. Please select supported plots and try again."
                    dialogs.dlgBox(exceptionTitle='Error', 
                                   exceptionMsg= msg,
                                   type="Error")
                    return
                else:
                    outList.append(plotDict[pageKey][0])
                
            if self.config.pageDict[pageKey]['layout'] == 'Rows': 
                rowOutput = row(plotDict[pageKey])
                bokehTab = Panel(child=rowOutput, title=self.config.pageDict[pageKey]['name'])    
                outList.append(bokehTab)
                
            if self.config.pageDict[pageKey]['layout'] == 'Columns': 
                rowOutput = column(plotDict[pageKey])
                bokehTab = Panel(child=rowOutput, title=self.config.pageDict[pageKey]['name'])    
                outList.append(bokehTab)
                
            if self.config.pageDict[pageKey]['layout'] == 'Grid': 
                columnVal = self.config.pageDict[pageKey]['columns']
                if columnVal == None or columnVal == '':
                    columnVal = int(len(plotDict[pageKey]))
                rowOutput = gridplot(plotDict[pageKey], 
                                     ncols=columnVal,
                                     merge_tools=True)
                bokehTab = Panel(child=rowOutput, title=self.config.pageDict[pageKey]['name'])    
                outList.append(bokehTab)
        # Check how many items in the list
        if len(plotList) > 1:
            bokehOutput = Tabs(tabs=outList)
        elif len(plotList) == 1:
            bokehOutput = Tabs(tabs=outList)
        else: 
            return

        # Save output
        filename = self.currentPath
        try:
            save(obj=bokehOutput, filename=filename, title='ORIGAMI')
        except IOError:
            msg = 'This file already exists and is currently in usage. Try selecting a different file name or closing the file first.'
            dialogs.dlgBox(exceptionTitle='Wrong file name', 
                           exceptionMsg= msg,
                           type="Error")
            return            
        if self.openInBrowserCheck.GetValue():
            webbrowser.open(filename)
          
    def onGetSavePath(self, evt):
        """
        Select path to save interactive plot in in
        """
         
        fileType = "HTML file|*.html"
        if self.config.saveInteractiveOverride:
            dlg =  wx.FileDialog(self, "Save interactive document to file...", "", "", fileType,
                                wx.FD_SAVE)
        else:
            dlg =  wx.FileDialog(self, "Save interactive document to file...", "", "", fileType,
                                wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        dlg.SetFilename('Interactive Output')
        if dlg.ShowModal() == wx.ID_OK:
            self.currentPath = dlg.GetPath()
            print "You chose %s" % dlg.GetPath()
            self.itemPath_value.SetValue(dlg.GetPath())
         
        self.presenter.currentPath = self.currentPath

    def OnGetColumnClick(self, evt):
        self.OnSortByColumn(column=evt.GetColumn())
     
    def OnSortByColumn(self, column):
        """
        Sort data in peaklist based on pressed column
        """
        # Check if it should be reversed
        if self.lastColumn == None:
            self.lastColumn = column
        elif self.lastColumn == column:
            if self.reverse == True:
                self.reverse = False
            else:
                self.reverse = True
        else:
            self.reverse = False
            self.lastColumn = column
        
        columns = self.itemsList.GetColumnCount()
        rows = self.itemsList.GetItemCount()
        
        tempData = []
        # Iterate over row and columns to get data
        for row in range(rows):
            tempRow = []
            for col in range(columns):
                item = self.itemsList.GetItem(itemId=row, col=col)
                if col == self.config.interactiveColNames['order']:
                    try: itemText = str2num(item.GetText())
                    except:itemText = item.GetText()
                    if itemText in [None, "None"]: 
                        itemText = ""
                else: itemText = item.GetText()

                tempRow.append(itemText)
            tempRow.append(self.itemsList.IsChecked(index=row))
            tempData.append(tempRow)
                
        # Sort data  
        tempData.sort(key = itemgetter(column), reverse=self.reverse)
        # Clear table and reinsert data
        self.itemsList.DeleteAllItems()
        
        checkData = []
        for check in tempData:
            checkData.append(check[-1])
            del check[-1]
        
        rowList = np.arange(len(tempData))
        for row, check in zip(rowList,checkData):
            self.itemsList.Append(tempData[row])
            self.itemsList.CheckItem(row, check)
            
        self.colorTable(evt=None)

    def OnShowOneDataType(self, filter='Show all'):
        """
        Function to only show select type of figure to be plotted
        """
    
        checkedItems = []
        # Create a backup list of checked items
        for row in range(self.itemsList.GetItemCount()):
            checkedItems.append(row)
                
        # Extract information
        columns = self.itemsList.GetColumnCount()
        rows = self.itemsList.GetItemCount()
        
        tempData = []
        filter = self.dataSelection_combo.GetStringSelection()
        docFilter = self.docSelection_combo.GetStringSelection()
        
        if filter == 'Show Selected': 
            for row in range(rows):
                tempRow = []
                if self.itemsList.IsChecked(index=row) and docFilter == 'All':
                    for col in range(columns):
                        item = self.itemsList.GetItem(itemId=row, col=col)
                        tempRow.append(item.GetText())
                    tempData.append(tempRow)
                elif self.itemsList.IsChecked(index=row) and docFilter != 'All':
                    if self.itemsList.GetItem(itemId=row, col=self.config.interactiveColNames['document']).GetText() == docFilter:
                        for col in range(columns):
                            item = self.itemsList.GetItem(itemId=row, col=col)
                            tempRow.append(item.GetText())
                        tempData.append(tempRow)
                    else:
                        pass
                else: 
                    pass
             
            # Clear table and reinsert data
            self.itemsList.DeleteAllItems()
            rows = len(tempData)
            for row in range(rows):
                self.itemsList.Append(tempData[row])
                self.itemsList.CheckItem(index=row, check=True)
            return 
        else:
            pass
        
        
        # Check if its not just selected items
        self.itemsList.DeleteAllItems()
        self.populateTable()
        
        # Extract information
        columns = self.itemsList.GetColumnCount()
        rows = self.itemsList.GetItemCount()
        tempData = []

        if filter == 'Show All':
            criteria = ['MS', 'RT', 'RT, multiple', '1D', '1D, multiple', '2D', '2D, processed', 'DT-IMS',
                        'RT, combined', '2D, combined', 'Overlay', 'Statistical', 'MS, multiple', 'UniDec',
                        'UniDec, multiple']
        elif filter == 'Show MS (all)':
            criteria = ['MS', 'MS, multiple']
        elif filter == 'Show MS (multiple)':
            criteria = ['MS, multiple']
        elif filter == 'Show MS':
            criteria = ['MS']
        elif filter == 'Show RT':
            criteria = ['RT']
        elif filter == 'Show RT (all)':
            criteria = ['RT', 'RT, multiple']
        elif filter == 'Show 1D IM-MS':
            criteria = ['1D']
        elif filter == 'Show 1D (all)':
            criteria = ['1D', '1D, multiple']
        elif filter == 'Show 1D plots (MS, DT, RT)':
            criteria = ['1D', 'MS', 'RT']
        elif filter == 'Show 2D IM-MS':
            criteria = ['2D', '2D, processed', '2D, combined']
        elif filter == 'Show Overlay':
            criteria = ['Overlay']
        elif filter == 'Show Statistical':
            criteria = ['Statistical']
        elif filter == 'Show UniDec (all)':
            criteria = ['UniDec', 'UniDec, multiple', 'UniDec, processed']
        elif filter == 'Show UniDec (processed)':
            criteria = ['UniDec, processed'] 
        elif filter == 'Show UniDec (multiple)':
            criteria = ['UniDec, multiple'] 

        # Iterate over row and columns to get data
        for row in range(rows):
            tempRow = []
            itemType = self.itemsList.GetItem(itemId=row, col=self.config.interactiveColNames['type']).GetText()
            if itemType in criteria and docFilter == 'All':  
                for col in range(columns):
                    item = self.itemsList.GetItem(itemId=row, col=col)
                    tempRow.append(item.GetText())
                tempData.append(tempRow)
            elif itemType in criteria and docFilter != 'All':
                if self.itemsList.GetItem(itemId=row, 
                                          col=self.config.interactiveColNames['document']).GetText() == docFilter:
                    for col in range(columns):
                        item = self.itemsList.GetItem(itemId=row, col=col)
                        tempRow.append(item.GetText())
                    tempData.append(tempRow)
                else:
                    pass
            else: pass

        # Clear table and reinsert data
        self.itemsList.DeleteAllItems()
        rows = len(tempData)
        for row in range(rows):
            self.itemsList.Append(tempData[row])
            
        self.colorTable(evt=None)
        self.allChecked = False

    def OnCheckAllItems(self, evt, check=True, override=False):
        """
        Check/uncheck all items in the list
        ===
        Parameters:
        check : boolean, sets items to specified state
        override : boolean, skips settings self.allChecked value
        """
        rows = self.itemsList.GetItemCount()
        if not override: 
            if self.allChecked:
                self.allChecked = False
                check = True
            else:
                self.allChecked = True
                check = False 
            
        if rows > 0:
            for row in range(rows):
                self.itemsList.CheckItem(row, check=check)
                
        if evt != None:
            evt.Skip()

    def onCheckItem(self, evt):
        item_state = not self.itemsList.IsChecked(self.currentItem)
        self.itemsList.CheckItem(self.currentItem, check=item_state)

    def _fontSizeConverter(self, value):
        return "%spt" % value
    
    def _fontWeightConverter(self, value):
        if value:
            return "bold"
        else:
            return "normal"
       
class EditableListCtrl(wx.ListCtrl, 
                        listmix.TextEditMixin, 
                       listmix.CheckListCtrlMixin):
    """ListCtrl"""
     
    def __init__(self, parent, id=-1, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.LC_REPORT):
        wx.ListCtrl.__init__(self, parent, id, pos, size, style)
        listmix.TextEditMixin.__init__(self)
        listmix.CheckListCtrlMixin.__init__(self)
         
        self.Bind(wx.EVT_LIST_BEGIN_LABEL_EDIT, self.OnBeginLabelEdit)
 
    def OnBeginLabelEdit(self, event):
        if event.m_col in [3, 4, 5, 9]:
            event.Skip()
        else:
            event.Veto()
#             