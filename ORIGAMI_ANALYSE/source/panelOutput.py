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
import wx
import wx.lib.mixins.listctrl as listmix
import wx.lib.scrolledpanel
from ids import *
from wx import ID_ANY
from toolbox import str2int, isempty, str2num
import numpy as np
from origamiStyles import *
# from origamiConfig import IconContainer as icons
from os import getcwd
from operator import itemgetter
import dialogs as dialogs

from bokeh.plotting import figure, show, save, ColumnDataSource, Column, gridplot
from bokeh.models import HoverTool, LinearColorMapper, Label, ColorBar
from bokeh.layouts import column, widgetbox, layout, row, gridplot
from bokeh.models.widgets import Panel, Tabs, Div
from bokeh import events

import matplotlib.colors as colors
import matplotlib.cm as cm
import webbrowser


class dlgOutputInteractive(wx.MiniFrame):
    """Save data in an interactive format"""
    
    def __init__(self, parent, icons, presenter, config):
        wx.MiniFrame.__init__(self, parent, -1, "Save Interactive Plots", 
                              style= (wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER | 
                                      wx.RESIZE_BOX | wx.MAXIMIZE_BOX ))
        
                
        self.view = parent
        self.icons = icons
        self.presenter = presenter 
        self.config = config
        self.documentsDict = self.presenter.documentsDict
        self.docsText = self.presenter.docsText
        self.currentPath = self.presenter.currentPath
        
        self.currentItem = None
        self.listOfPlots = []
        self.SetBackgroundColour(wx.WHITE)
        
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
        
    def makeGUI(self):
        """Make GUI elements."""
        
        # make GUI elements
#         preToolbar = self.preToolbar()
        toolbar = self.makeToolbar()
        self.makeItemsList()
        editor = self.makeItemEditor()
        buttons = self.makeDlgButtons()
        
        # pack elements
        self.sizer = wx.BoxSizer(wx.VERTICAL)
#         self.sizer.Add(preToolbar, 0, wx.EXPAND, 0)
        self.sizer.Add(toolbar, 0, wx.EXPAND, 0)
        self.sizer.Add(self.itemsList, 1, wx.EXPAND, 0)
        self.sizer.Add(editor, 0, wx.EXPAND, 0)
        self.sizer.Add(buttons, 0, wx.EXPAND, 0)
        
        # fit layout
        self.sizer.Fit(self)
        self.SetSizer(self.sizer)
        self.SetMinSize(self.GetSize())
        self.Centre()
        self.Layout()
        
#     def preToolbar(self):
#    This is to be added in future to add a couple of labels to make things clearer
#
#         """ Make toolbar header with labels """
#         TOOLBAR_TOOLSIZE = (16,16)
#         TOOLBAR_HEIGHT = 38
#         BUTTON_SIZE_CORRECTION = 0
#         TOOLBAR_RSPACE = 15
#         TOOLBAR_LSPACE = 0
#         SPACER = 5
#         SPACER_L = 20
#         
#         # init toolbar
#         panel = bgrPanel(self, -1, self.icons.iconsLib['bgrToolbar'], 
#                              size=(40, 40))
#         
#         filter_label = wx.StaticText(panel, -1, "Filter:")
#         self.dataSelection_combo = wx.ComboBox(panel, ID_ANY, 
#                                                value= "Show All",
#                                                choices=["Show All", "Show Selected", 
#                                                         "Show MS", "Show MS (multiple files)",
#                                                         "Show RT", "Show 1D IM-MS", 
#                                                         "Show 1D plots (MS, DT, RT)",
#                                                         "Show 2D IM-MS", "Show Overlay", 
#                                                         "Show Statistical"],
#                                                style=wx.CB_READONLY)
#         
#         
#         
# #         self.preToolbar = wx.BoxSizer(wx.HORIZONTAL)
#         self.preToolbar = wx.GridBagSizer(2, 2)
# #         self.preToolbar.AddSpacer(24)
# #         self.preToolbar.AddSpacer(25)
#         self.preToolbar.Add(filter_label, (0,1), wx.GBSpan(1,1), wx.ALIGN_CENTER_VERTICAL)
#         self.preToolbar.Add(self.dataSelection_combo, (1,1), wx.GBSpan(1,1), wx.ALIGN_CENTER_VERTICAL)
#         
#         mainSizer = wx.BoxSizer(wx.VERTICAL)
#         mainSizer.Add(self.preToolbar, 1, wx.EXPAND)
#         panel.SetSizer(mainSizer)
#         mainSizer.Fit(panel)
#         
#         return panel
#         
    
    def makeToolbar(self):
                        
        # Create toolbar for the table
        toolbar = wx.ToolBar(self, style=wx.TB_HORIZONTAL | wx.TB_DOCKABLE, id = wx.ID_ANY) 
        toolbar.SetToolBitmapSize((16, 20)) 
        toolbar.AddTool(ID_checkAllItems_HTML, self.icons.iconsLib['check16'], 
                        shortHelpString='Select All')
        self.dataSelection_combo = wx.ComboBox(toolbar, ID_ANY, 
                                               value= "Show All",
                                               choices=["Show All", "Show Selected", 
                                                        "Show MS", "Show MS (multiple files)",
                                                        "Show RT", "Show 1D IM-MS", 
                                                        "Show 1D plots (MS, DT, RT)",
                                                        "Show 2D IM-MS", "Show Overlay", 
                                                        "Show Statistical"],
                                               style=wx.CB_READONLY)
        tip = self.makeTooltip(text=u"Filter the table based on the plot type", delay=500)
        self.dataSelection_combo.SetToolTip(tip)
        toolbar.AddControl(self.dataSelection_combo)
        toolbar.AddSeparator()
        toolbar.AddSeparator()
        toolbar.AddSeparator()
        docList = ['All'] + self.documentsDict.keys()
        self.docSelection_combo = wx.ComboBox(toolbar, ID_ANY, value='All',
                                               choices = docList,
                                               style=wx.CB_READONLY)
        tip = self.makeTooltip(text=u"Filter the table based on the document name", delay=500)
        self.docSelection_combo.SetToolTip(tip)
        toolbar.AddControl(self.docSelection_combo)
        toolbar.AddSeparator()
        toolbar.AddSeparator()
        toolbar.AddSeparator()
        self.pageLayoutSelect_toolbar = wx.ComboBox(toolbar, ID_ANY, 
                                                 value='None',
                                                 choices = self.config.pageDict.keys(),
                                                 style=wx.CB_READONLY, size=(120, -1))
        msg = ''.join([u"Select output format. None - each plot is displayed on individual page ",
                      u" Rows - each plot with this page will be added as separate item in a row format ",
                      u" Columns - each plot with this page will be added as separate item in a column format.",
                      u" Click on green tick to assign the page to selected plots."])
        tip = self.makeTooltip(text=msg, delay=500)
        self.pageLayoutSelect_toolbar.SetToolTip(tip)
        toolbar.AddControl(self.pageLayoutSelect_toolbar)
        toolbar.AddTool(ID_assignPageSelected_HTML, self.icons.iconsLib['tick16'], 
                        shortHelpString='Assign this page to selected items')
        toolbar.AddTool(ID_addPage_HTML, self.icons.iconsLib['add16'], shortHelpString='Add page')
        toolbar.AddSeparator()
        toolbar.AddSeparator()
        toolbar.AddSeparator()
        self.plotTypeToolsSelect_toolbar = wx.ComboBox(toolbar, ID_ANY, 
                                                 value='1D', choices=['1D', '2D','Overlay'],
                                                 style=wx.CB_READONLY, size=(-1, -1))
        msg = ''.join(["Select a list of tools to be added to each plot."])
        tip = self.makeTooltip(text=msg, delay=500)
        self.plotTypeToolsSelect_toolbar.SetToolTip(tip)
        toolbar.AddControl(self.plotTypeToolsSelect_toolbar)
        toolbar.AddTool(ID_assignToolsSelected_HTML, self.icons.iconsLib['tick16'], 
                        shortHelpString='Assign this toolset to selected items')
        toolbar.Realize()
        
        self.dataSelection_combo.Bind(wx.EVT_COMBOBOX, self.OnShowOneDataType)
        self.docSelection_combo.Bind(wx.EVT_COMBOBOX, self.OnShowOneDataType)
        self.Bind(wx.EVT_TOOL, self.OnCheckAllItems, id=ID_checkAllItems_HTML) 
        self.Bind(wx.EVT_TOOL, self.onAddPage, id=ID_addPage_HTML)
        self.Bind(wx.EVT_TOOL, self.onChangePageForSelectedItems, 
                  id=ID_assignPageSelected_HTML)
        self.Bind(wx.EVT_TOOL, self.onChangeToolsForSelectedItems, 
                  id=ID_assignToolsSelected_HTML)
        
        
        return toolbar

    def makeTooltip(self, text=None, delay=500):
        tip = wx.ToolTip(text)
        tip.SetDelay(delay)
        
        return tip

    def makeItemsList(self):
        """Make list for items."""
        
        LISTCTRL_STYLE_MULTI = wx.LC_REPORT|wx.LC_VRULES|wx.LC_HRULES
        
        # init table
        self.itemsList = ListCtrl(self, -1, size=(845, -1), style=LISTCTRL_STYLE_MULTI)
        self.itemsList.SetFont(wx.SMALL_FONT)
        
        # Bind events
        self.itemsList.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onItemSelected)
        self.itemsList.Bind(wx.EVT_LIST_COL_CLICK, self.OnGetColumnClick)
#         self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnRightClickMenu)
        
        # make columns
        self.itemsList.InsertColumn(0, u"Document Title", wx.LIST_FORMAT_CENTER, width=200)
        self.itemsList.InsertColumn(1, u"Type", wx.LIST_FORMAT_LEFT, width=90)
        self.itemsList.InsertColumn(2, u"File/Ion", wx.LIST_FORMAT_LEFT, width=100)
        self.itemsList.InsertColumn(3, u"Title", wx.LIST_FORMAT_LEFT, width=100)
        self.itemsList.InsertColumn(4, u"Header", wx.LIST_FORMAT_LEFT, width=50)
        self.itemsList.InsertColumn(5, u"Footnote", wx.LIST_FORMAT_LEFT, width=50)
        self.itemsList.InsertColumn(6, u"Color/Colormap", wx.LIST_FORMAT_LEFT, width=85)
        self.itemsList.InsertColumn(7, u"#", wx.LIST_FORMAT_LEFT, width=30)
        self.itemsList.InsertColumn(8, u"Page", wx.LIST_FORMAT_LEFT, width=70)
        self.itemsList.InsertColumn(9, u"Tools", wx.LIST_FORMAT_LEFT, width=50)
        
        self.itemsList.SetToolTip(wx.ToolTip("Select items save in the .HTML file"))
  
    def makeItemEditor(self):
        """Make items editor."""
            
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.editorBook = wx.Notebook(self, wx.ID_ANY, wx.DefaultPosition, size=(300,-1), style=0)
#===========================================================================
#  HTML
#===========================================================================
        self.htmlView = wx.lib.scrolledpanel.ScrolledPanel(self.editorBook, wx.ID_ANY, 
                                                           wx.DefaultPosition, (-1,300), wx.TAB_TRAVERSAL)
        self.htmlView.SetupScrolling()
        self.makeHTMLView()
        self.editorBook.AddPage(self.htmlView, u"HTML", False)
#===========================================================================
#  TOOLS
#===========================================================================
#         self.propertiesView = wx.Panel(self.editorBook, wx.ID_ANY, 
#                                  wx.DefaultPosition, (-1,300), wx.TAB_TRAVERSAL)
#         self.editorBook.AddPage(self.propertiesView, u"Tools/Annotations", False)
#         self.makeToolsView()
#===========================================================================
#  PROPERTIES
#===========================================================================
        self.propertiesView = wx.Panel(self.editorBook, wx.ID_ANY, 
                                 wx.DefaultPosition, (-1,250), wx.TAB_TRAVERSAL)
        self.editorBook.AddPage(self.propertiesView, u"Properties", False)
        self.makePropertiesView()
        
        
        mainSizer.Add(self.editorBook, 1, wx.EXPAND |wx.ALL, 3)
        
        return mainSizer
                
    def makeHTMLView(self):
        
        RICH_TEXT = wx.TE_MULTILINE|wx.TE_WORDWRAP|wx.TE_RICH2

        self.mainBoxHTML = makeStaticBox(self.htmlView, "Item properties", (-1,-1), wx.BLUE)
        mainSizer = wx.StaticBoxSizer(self.mainBoxHTML, wx.HORIZONTAL)
        
        # make elements
        itemName_label = wx.StaticText(self.htmlView, -1, "Title")
        self.itemName_value = wx.TextCtrl(self.htmlView, -1, "", size=(-1, -1))
        self.itemName_value.SetToolTip(wx.ToolTip("Filename to be used to save the file"))
        
        
        itemHeader_label = wx.StaticText(self.htmlView, -1, "Header")
        self.itemHeader_value = wx.TextCtrl(self.htmlView, -1, "", size=(-1, 80), style=RICH_TEXT)
        self.itemHeader_value.SetToolTip(wx.ToolTip("HTML-rich text to be used for the header of the interactive file"))
        
      
        itemFootnote_label = wx.StaticText(self.htmlView, -1, "Footnote")
        self.itemFootnote_value = wx.TextCtrl(self.htmlView, -1, "", size=(-1, 80), style=RICH_TEXT)
        self.itemFootnote_value.SetToolTip(wx.ToolTip("HTML-rich text to be used for the footnote of the interactive file"))
        
        itemColormap_label = wx.StaticText(self.htmlView, wx.ID_ANY,
                                             u"Colormap", wx.DefaultPosition, 
                                             wx.DefaultSize, TEXT_STYLE_CV_R_L)
        
        self.comboCmapSelect = wx.ComboBox( self.htmlView, ID_changeColormapInteractive, 
                                            wx.EmptyString, wx.DefaultPosition, wx.Size( COMBO_SIZE,-1 ), 
                                            self.config.cmaps2, COMBO_STYLE, wx.DefaultValidator) 

        itemColorLine_label = wx.StaticText(self.htmlView, wx.ID_ANY,
                                             u"Line Color", wx.DefaultPosition, 
                                             wx.DefaultSize, TEXT_STYLE_CV_R_L)
        
        self.colorBtn = wx.Button( self.htmlView, ID_changeColorInteractive,
                                 u"", wx.DefaultPosition, wx.Size( 26, 26 ), 0 )
        
        order_label = makeStaticText(self.htmlView, u"Order")
        self.order_value = wx.TextCtrl(self.htmlView, -1, "", size=(50, -1))
        

        
        page_label = makeStaticText(self.htmlView, u"Assign page")
        self.pageLayoutSelect_htmlView = wx.ComboBox(self.htmlView, -1, choices=[], value="None", style=wx.CB_READONLY)
        
        tools_label = makeStaticText(self.htmlView, u"Assign toolset")
        self.plotTypeToolsSelect_htmlView = wx.ComboBox(self.htmlView, -1, choices=[], value="", style=wx.CB_READONLY)
        self.plotTypeToolsSelect_htmlView.Disable()
        
        xmin_label = makeStaticText(self.htmlView, u"Xmin")
        self.xmin_value = wx.TextCtrl(self.htmlView, -1, "", size=(40, -1))
        self.xmin_value.SetFont(wx.SMALL_FONT)
        xmax_label = makeStaticText(self.htmlView, u"Xmax")
        self.xmax_value = wx.TextCtrl(self.htmlView, -1, "", size=(40, -1))
        self.xmax_value.SetFont(wx.SMALL_FONT)
        ymin_label = makeStaticText(self.htmlView, u"Ymin")
        self.ymin_value = wx.TextCtrl(self.htmlView, -1, "", size=(40, -1))
        self.ymin_value.SetFont(wx.SMALL_FONT)
        ymax_label = makeStaticText(self.htmlView, u"Ymax")
        self.ymax_value = wx.TextCtrl(self.htmlView, -1, "", size=(40, -1))
        self.ymax_value.SetFont(wx.SMALL_FONT)
        
        hideLabels = [xmin_label, xmax_label, ymin_label, ymax_label,
                      self.xmin_value, self.xmax_value,
                       self.ymin_value, self.ymax_value]
        for label in hideLabels:
            label.Hide()
        
        
        # Bind
        self.itemName_value.Bind(wx.EVT_TEXT, self.onAnnotateItems)
        self.itemHeader_value.Bind(wx.EVT_TEXT, self.onAnnotateItems)
        self.itemFootnote_value.Bind(wx.EVT_TEXT, self.onAnnotateItems)
        self.order_value.Bind(wx.EVT_TEXT, self.onAnnotateItems)
        self.colorBtn.Bind(wx.EVT_BUTTON, self.onChangeColour, id=ID_changeColorInteractive)
        self.comboCmapSelect.Bind(wx.EVT_COMBOBOX, self.onChangeColour, id=ID_changeColormapInteractive)        
        self.pageLayoutSelect_htmlView.Bind(wx.EVT_COMBOBOX, self.onChangePageForItem)
        self.plotTypeToolsSelect_htmlView.Bind(wx.EVT_COMBOBOX, self.onChangeToolsForItem)
        
        
        # Disable all elements when nothing is selected
        itemList = [self.itemName_value, self.itemHeader_value, self.itemFootnote_value,
                    self.order_value, self.colorBtn, self.comboCmapSelect, self.pageLayoutSelect_htmlView,
                    self.plotTypeToolsSelect_htmlView, self.xmin_value, self.xmax_value,
                    self.ymin_value, self.ymax_value]
    
        for item in itemList:
            item.Disable()
         
        grid = wx.GridBagSizer(5,5)
        n = 0
        grid.Add(itemName_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.itemName_value, (n,1), wx.GBSpan(1,36), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        n = n+1
        grid.Add(itemHeader_label, (1,0), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.itemHeader_value, (1,1), wx.GBSpan(1,36), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        n = n+1
        grid.Add(itemFootnote_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.itemFootnote_value, (n,1), wx.GBSpan(1,36), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        n = n+1
        grid.Add(itemColormap_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.comboCmapSelect, (n,1), wx.GBSpan(1,2), flag=wx.ALIGN_CENTER_VERTICAL)
        
        grid.Add(itemColorLine_label, (n,3), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.colorBtn, (n,4), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        grid.Add(order_label, (n,5), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.order_value, (n,6), wx.GBSpan(1,1), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(xmin_label, (n,8), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.xmin_value, (n,9), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        grid.Add(xmax_label, (n,10), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.xmax_value, (n,11), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        grid.Add(ymin_label, (n,12), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.ymin_value, (n,13), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        grid.Add(ymax_label, (n,14), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.ymax_value, (n,15), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        n = n+1
        grid.Add(tools_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.plotTypeToolsSelect_htmlView, (n,1), wx.GBSpan(1,2), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        n = n+1
        grid.Add(page_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.pageLayoutSelect_htmlView, (n,1), wx.GBSpan(1,2), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)

        mainSizer.Add(grid, 0, wx.EXPAND, 5)        

        mainGrid = wx.GridBagSizer(2,2)
        mainGrid.Add(mainSizer, (0,0), flag=wx.EXPAND)

        mainSizer.Fit(self.htmlView)
        self.htmlView.SetSizer(mainSizer)
        
        return mainSizer

    def makePropertiesView(self):
        viewSizer = wx.BoxSizer(wx.VERTICAL)

        fontSizer = self.makeFontSubPanel()
        imageSizer = self.makeImageSubPanel()
        pageLayoutSizer = self.makePageLayoutSubPanel()
        rmsdSizer = self.makeRMSDSubPanel()
        toolsSizer = self.makeInteractiveToolsSubPanel()
        plot1Dsizer = self.make1DplotSubPanel()
        overlaySizer = self.makeOverLaySubPanel()

        mainGrid = wx.GridBagSizer(2,2)
        # x = 1
        mainGrid.Add(toolsSizer, (0,0), wx.GBSpan(6,1), flag=wx.EXPAND)
        mainGrid.Add(plot1Dsizer, (6,0), wx.GBSpan(1,1), flag=wx.EXPAND)
        # x = 2 
        mainGrid.Add(fontSizer, (0,1), wx.GBSpan(2,1), flag=wx.EXPAND)
        mainGrid.Add(imageSizer, (2,1), wx.GBSpan(2,1), flag=wx.EXPAND)
        mainGrid.Add(overlaySizer, (4,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        # x = 3
        mainGrid.Add(pageLayoutSizer, (0,2), wx.GBSpan(2,1), flag=wx.EXPAND)
        mainGrid.Add(rmsdSizer, (2,2), wx.GBSpan(2,1), flag=wx.EXPAND)
        
        
        
        viewSizer.Add(mainGrid, 0, wx.EXPAND, 5)
        viewSizer.Fit(self.propertiesView)
        self.propertiesView.SetSizer(viewSizer)
        
        self.onSetupTools(evt=None)
        self.onSelectPageProperties(evt=None)
        self.onChangePage(evt=None)
        
        return viewSizer
   
    def makeFontSubPanel(self):
        mainBox = makeStaticBox(self.propertiesView, "Font properties", (270,-1), wx.BLUE)
        mainBox.SetSize((270,-1))
        mainSizer = wx.StaticBoxSizer(mainBox, wx.HORIZONTAL)
        titleFontSize = makeStaticText(self.propertiesView, u"Title font size")
        
        self.titleSlider = wx.SpinCtrlDouble(self.propertiesView, wx.ID_ANY, 
                                             value=str(self.config.titleFontSizeVal),min=8, max=32,
                                             initial=self.config.titleFontSizeVal, inc=1, size=(50,-1))
        self.titleBoldCheck = makeCheckbox(self.propertiesView, u"Bold")
        self.titleBoldCheck.SetValue(self.config.titleFontWeightInteractive)
        
        labelFontSize = makeStaticText(self.propertiesView, u"Label font size")
        self.labelSlider = wx.SpinCtrlDouble(self.propertiesView, wx.ID_ANY, 
                                             value=str(self.config.labelFontSizeVal),min=8, max=32,
                                             initial=self.config.labelFontSizeVal, inc=1, size=(50,-1))
        
        self.labelBoldCheck = makeCheckbox(self.propertiesView, u"Bold")
        self.labelBoldCheck.SetValue(self.config.labelFontWeightInteractive)
        
        tickFontSize = makeStaticText(self.propertiesView, u"Tick font size")
        self.tickSlider = wx.SpinCtrlDouble(self.propertiesView, wx.ID_ANY, 
                                             value=str(self.config.tickFontSizeVal),min=8, max=32,
                                             initial=self.config.tickFontSizeVal, inc=1, size=(50,-1))   
             
        # Add to grid sizer
        grid = wx.GridBagSizer(2,2)
        grid.Add(titleFontSize, wx.GBPosition(0,0), wx.GBSpan(1,2), TEXT_STYLE_CV_R_L, 2)
        grid.Add(self.titleSlider, wx.GBPosition(1,0), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
        grid.Add(self.titleBoldCheck, wx.GBPosition(1,1), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
        
        grid.Add(labelFontSize, wx.GBPosition(0,2), wx.GBSpan(1,4), TEXT_STYLE_CV_R_L, 2)
        grid.Add(self.labelSlider, wx.GBPosition(1,2), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
        grid.Add(self.labelBoldCheck, wx.GBPosition(1,3), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
        
        grid.Add(tickFontSize, wx.GBPosition(2,0), wx.GBSpan(1,2), TEXT_STYLE_CV_R_L, 2)
        grid.Add(self.tickSlider, wx.GBPosition(3,0), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
#         grid.Add(self.tickBoldCheck, wx.GBPosition(2,2), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
        
        mainSizer.Add(grid, 0, wx.EXPAND|wx.ALL, 2)
        return mainSizer
   
    def makeImageSubPanel(self):
        imageBox = makeStaticBox(self.propertiesView, "Image properties", (270,-1), wx.BLUE)
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

        gridFigure = wx.GridBagSizer(2,10)
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
    
    def makePageLayoutSubPanel(self):
        layoutBox = makeStaticBox(self.propertiesView, "Page properties", (200,-1), wx.BLUE)
        layoutSizer = wx.StaticBoxSizer(layoutBox, wx.HORIZONTAL)
        layoutBox.SetToolTip(wx.ToolTip("Each HTML document is tabbed (when more than one item is selected). Each tab can be subsequently one of the following: individual, row, column or grid."))
        
        
        selPage_label = makeStaticText(self.propertiesView, u"Select page")
        self.pageLayoutSelect_propView = wx.ComboBox(self.propertiesView, -1, choices=[],
                                        value="None", style=wx.CB_READONLY)
        
        layoutDoc_label = makeStaticText(self.propertiesView, u"Page layout")
        self.layoutDoc_combo = wx.ComboBox(self.propertiesView, -1, choices=['Individual', 
                                                                             'Columns','Rows',
                                                                             'Grid'],
                                        value=self.config.layoutModeDoc, style=wx.CB_READONLY)
        self.layoutDoc_combo.SetToolTip(wx.ToolTip("Select type of layout for the page. Default: Individual"))
        
        self.addPage = wx.Button(self.propertiesView, ID_ANY,size=(26,26))
        self.addPage.SetBitmap(self.icons.iconsLib['add16'])
  
        columns_label = makeStaticText(self.propertiesView, u"Columns")
        self.columns_value = wx.TextCtrl(self.propertiesView, -1, "", size=(50, -1))
        self.columns_value.SetToolTip(wx.ToolTip("Grid only. Number of columns in the grid"))
        

        # bind
        self.pageLayoutSelect_propView.Bind(wx.EVT_COMBOBOX, self.onChangePage)
        
        self.layoutDoc_combo.Bind(wx.EVT_COMBOBOX, self.onChangeSettings)
        self.layoutDoc_combo.Bind(wx.EVT_COMBOBOX, self.onSelectPageProperties)
        
        self.columns_value.Bind(wx.EVT_TEXT, self.onSelectPageProperties)
        self.columns_value.Bind(wx.EVT_TEXT, self.onChangeSettings)

        self.addPage.Bind(wx.EVT_BUTTON, self.onAddPage)

        gridLayout = wx.GridBagSizer(2,2)
        gridLayout.Add(selPage_label, (0,0), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        gridLayout.Add(self.pageLayoutSelect_propView, (0,1), wx.GBSpan(1,2), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        gridLayout.Add(self.addPage, (0,3))
 
        gridLayout.Add(layoutDoc_label, (1,0), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        gridLayout.Add(self.layoutDoc_combo, (1,1), wx.GBSpan(1,2), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
#         gridLayout.Add(rows_label, (2,0), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
#         gridLayout.Add(self.rows_value, (2,1), flag=wx.ALIGN_CENTER_VERTICAL)
        gridLayout.Add(columns_label, (2,0), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        gridLayout.Add(self.columns_value, (2,1), flag=wx.ALIGN_CENTER_VERTICAL)
 
        layoutSizer.Add(gridLayout, 0, wx.EXPAND|wx.ALL, 2)
        return layoutSizer
    
    def makeRMSDSubPanel(self):
        rmsdBox = makeStaticBox(self.propertiesView, "RMSD plot properties", (200,-1), wx.BLUE)
        rmsdSizer = wx.StaticBoxSizer(rmsdBox, wx.HORIZONTAL)
        rmsdBox.SetToolTip(wx.ToolTip(""))

        notationFontSize = makeStaticText(self.propertiesView, u"Label font size")
        self.notationSlider = wx.SpinCtrlDouble(self.propertiesView, wx.ID_ANY, 
                                             value=str(self.config.notationFontSizeVal),min=8, max=32,
                                             initial=self.config.notationFontSizeVal, inc=1, size=(50,-1))     
        self.notationBoldCheck = makeCheckbox(self.propertiesView, u"Bold")
        self.notationBoldCheck.SetValue(self.config.notationFontWeightInteractive)

        notationColor_label= makeStaticText(self.propertiesView, u"Font")
        self.notationColorBtn = wx.Button( self.propertiesView, ID_changeColorNotationInteractive,
                                           u"", wx.DefaultPosition, wx.Size( 26, 26 ), 0 )
        self.notationColorBtn.SetBackgroundColour(tuple([np.int(self.config.notationColor[0]*255),
                                                         np.int(self.config.notationColor[1]*255),
                                                         np.int(self.config.notationColor[2]*255)]))
        
        notationBackgroundColor_label= makeStaticText(self.propertiesView, u"Background")
        self.notationColorBackgroundBtn = wx.Button( self.propertiesView, ID_changeColorBackgroundNotationInteractive,
                                                     u"", wx.DefaultPosition, wx.Size( 26, 26 ), 0 )
        self.notationColorBackgroundBtn.SetBackgroundColour(tuple([np.int(self.config.notationBackgroundColor[0]*255),
                                                                   np.int(self.config.notationBackgroundColor[1]*255),
                                                                   np.int(self.config.notationBackgroundColor[2]*255)]))
        
        
        
        self.titleSlider.Bind(wx.EVT_SPINCTRLDOUBLE, self.onChangeSettings)
        self.titleBoldCheck.Bind(wx.EVT_CHECKBOX, self.onChangeSettings)
        self.labelSlider.Bind(wx.EVT_SPINCTRLDOUBLE, self.onChangeSettings)
        self.labelBoldCheck.Bind(wx.EVT_CHECKBOX, self.onChangeSettings)
        self.tickSlider.Bind(wx.EVT_SPINCTRLDOUBLE, self.onChangeSettings)
        self.notationSlider.Bind(wx.EVT_SPINCTRLDOUBLE, self.onChangeSettings)
        self.notationBoldCheck.Bind(wx.EVT_CHECKBOX, self.onChangeSettings)
        self.notationColorBtn.Bind(wx.EVT_BUTTON, self.onChangeColour, id=ID_changeColorNotationInteractive)
        self.notationColorBackgroundBtn.Bind(wx.EVT_BUTTON, self.onChangeColour, id=ID_changeColorBackgroundNotationInteractive)


        grid = wx.GridBagSizer(2,2)
        n=0
        grid.Add(notationFontSize, wx.GBPosition(n,0), wx.GBSpan(1,2), TEXT_STYLE_CV_R_L, 2)
        grid.Add(notationColor_label, wx.GBPosition(n,2), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
        grid.Add(notationBackgroundColor_label, wx.GBPosition(n,3), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
        n=n+1
        grid.Add(self.notationSlider, wx.GBPosition(n,0), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
        grid.Add(self.notationBoldCheck, wx.GBPosition(n,1), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
        grid.Add(self.notationColorBtn, wx.GBPosition(n,2), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
        grid.Add(self.notationColorBackgroundBtn, wx.GBPosition(n,3), wx.GBSpan(1,1), TEXT_STYLE_CV_R_L, 2)
 
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
        self.wheelZoom_combo = wx.ComboBox(self.propertiesView, -1, choices=['Wheel Zoom XY', 'Wheel Zoom X', 
                                                                        'Wheel Zoom Y'], 
                                          value='Wheel Zoom XY', style=wx.CB_READONLY)


        location_label = wx.StaticText(self.propertiesView, -1, "Toolbar position", style=TEXT_STYLE_CV_R_L)
        self.location_combo = wx.ComboBox(self.propertiesView, -1, choices=['left','above','right','below'], 
                                          value=self.config.toolsLocation, style=wx.CB_READONLY)
        self.location_combo.Disable()
        
        activeDragTools = ['Box Zoom', 'Pan', 'Pan X', 'Pan Y', 'auto', 'None']
        activeWheelTools = ['Wheel Zoom XY', 'Wheel Zoom X', 'Wheel Zoom Y', 'auto', 'None']
        activeHoverTools = ['Hover', 'Crosshair', 'auto', 'None']
        
        
        availableActiveTools_label = wx.StaticText(self.propertiesView, -1, "Active tools", 
                                                   style=TEXT_STYLE_CV_R_L)
        availableActiveTools_label.SetFont(font)
        availableActiveTools_label.SetForegroundColour((34,139,34))
        
        drag_label = makeStaticText(self.propertiesView, u"Active Drag")
        self.activeDrag_combo = wx.ComboBox(self.propertiesView, -1, choices=activeDragTools, 
                                            value=self.config.activeDrag, 
                                            style=wx.CB_READONLY)
        wheel_labe = makeStaticText(self.propertiesView, u"Active Wheel")
        self.activeWheel_combo = wx.ComboBox(self.propertiesView, -1, choices=activeWheelTools,
                                             value=self.config.activeWheel, 
                                             style=wx.CB_READONLY)
        inspect_label = makeStaticText(self.propertiesView, u"Active Hover")
        self.activeInspect_combo= wx.ComboBox(self.propertiesView, -1, choices=activeHoverTools,
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
        gridTools.Add(self.addPlotType, (n,2), flag=wx.ALIGN_CENTER_VERTICAL)
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
        mainBox = makeStaticBox(self.propertiesView, "1D plot properties", (270,-1), wx.BLUE)
        figSizer = wx.StaticBoxSizer(mainBox, wx.HORIZONTAL)
         
        self.hoverVlineCheck = wx.CheckBox(self.propertiesView, -1 ,u'Hover tool linked to X axis (1D)', (15, 30))
        self.hoverVlineCheck.SetToolTip(wx.ToolTip("Hover tool information is linked to the X-axis"))
        self.hoverVlineCheck.SetValue(self.config.hoverVline)
 
        # bind
        self.hoverVlineCheck.Bind(wx.EVT_CHECKBOX, self.onChangeSettings)   

        gridFigure = wx.GridBagSizer(2,10)
        n = 0
        gridFigure.Add(self.hoverVlineCheck, (n,0))
        
        figSizer.Add(gridFigure, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        
        return figSizer
    
    def makeOverLaySubPanel(self):
        mainBox = makeStaticBox(self.propertiesView, "Overlay plot properties", (270,-1), wx.BLUE)
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
        
        gridFigure = wx.GridBagSizer(2,10)
        n = 0
        gridFigure.Add(layout_label, (n,0))
        gridFigure.Add(self.layout_combo, (n,1))
        gridFigure.Add(self.XYaxisLinkCheck, (n,2))
        n = n+1
        
        
        figSizer.Add(gridFigure, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        
        return figSizer
    
    def makeDlgButtons(self):
        mainSizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, ""), wx.VERTICAL)
        
        pathBtn = wx.Button(self, -1, "Set Path", size=(80,-1))
        saveBtn = wx.Button(self, -1, "Save", size=(80,-1))
        cancelBtn = wx.Button(self, -1, "Cancel", size=(80,-1))
        openHTMLWebBtn = wx.Button(self, ID_helpHTMLEditor, "HTML Editor", size=(80,-1))
        openHTMLWebBtn.SetToolTip(wx.ToolTip("Opens a web-based HTML editor"))
        
        itemPath_label = wx.StaticText(self, -1, "Path:")
        self.itemPath_value = wx.TextCtrl(self, -1, "", size=(720, -1), style=wx.TE_READONLY)
        self.itemPath_value.SetValue(str(self.currentPath))
        self.openInBrowserCheck = makeCheckbox(self, u"Open in browser \nafter saving")
        self.openInBrowserCheck.SetValue(self.config.openInteractiveOnSave)

        
        
        grid = wx.GridBagSizer(5, 5)
        grid.Add(itemPath_label, (0,0), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.itemPath_value, (0,1), wx.GBSpan(1,6), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(openHTMLWebBtn, (1,0), flag=wx.ALIGN_CENTER|wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(pathBtn, (1,1), flag=wx.ALIGN_CENTER|wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(saveBtn, (1,2), flag=wx.ALIGN_CENTER|wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(cancelBtn, (1,3), flag=wx.ALIGN_CENTER|wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(self.openInBrowserCheck, (1,6), flag=wx.ALIGN_CENTER|wx.ALIGN_CENTER_HORIZONTAL)
        
        # make bindings
        saveBtn.Bind(wx.EVT_BUTTON, self.onGenerateHTML)
        openHTMLWebBtn.Bind(wx.EVT_BUTTON, self.presenter.onLibraryLink)
        cancelBtn.Bind(wx.EVT_BUTTON, self.onClose)
        pathBtn.Bind(wx.EVT_BUTTON, self.onGetSavePath)

        mainSizer.Add(grid, 0, wx.ALIGN_CENTER|wx.ALL, 2)
        
        return mainSizer

    def onAddPage(self, evt):
        pageName = dialogs.dlgAsk('Please select page name.', defaultValue='')
        if pageName == '': return
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
#             self.rows_value.Disable()
            self.columns_value.Disable()
            self.layoutDoc_combo.Disable()
        else:
            self.layoutDoc_combo.Enable()
            if self.layoutDoc_combo.GetValue() != 'Grid':
#                 self.rows_value.Disable()
                self.columns_value.Disable()
            else:
#                 self.rows_value.Enable()
                self.columns_value.Enable()
            
        # Change values in dictionary
        if selectedItem != 'None':
            self.config.pageDict[selectedItem] = {'layout':self.layoutDoc_combo.GetStringSelection(), 
#                                                   'rows':str2int(self.rows_value.GetValue()),
                                                  'columns':str2int(self.columns_value.GetValue()),
                                                  'name':selectedItem}

        if evt != None:
            evt.Skip()

    def onChangeSettings(self, evt):
        """
        Update figure settings
        """
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
        self.config.titleFontSizeVal = self.titleSlider.GetValue()
        self.titleFontSize = ''.join([str(self.config.titleFontSizeVal),'pt'])
        
        self.config.titleFontWeightInteractive = self.titleBoldCheck.GetValue()
        if self.titleBoldCheck.GetValue(): self.titleFontWeightInteractive = 'bold'
        else: self.titleFontWeightInteractive  = 'normal'
        
        self.config.labelFontSizeVal = self.labelSlider.GetValue()
        self.labelFontSize = ''.join([str(self.config.labelFontSizeVal),'pt'])
        
        self.config.labelFontWeightInteractive = self.labelBoldCheck.GetValue()
        if self.labelBoldCheck.GetValue(): self.labelFontWeightInteractive = 'bold'
        else: self.labelFontWeightInteractive  = 'normal'
        
        self.config.tickFontSizeVal = self.tickSlider.GetValue()
        self.tickFontSize = ''.join([str(self.config.tickFontSizeVal),'pt'])
        
        self.config.notationFontSizeVal = self.notationSlider.GetValue()      
        self.notationFontSize = ''.join([str(self.config.notationFontSizeVal),'pt'])
        
        self.config.notationFontWeightInteractive = self.notationBoldCheck.GetValue()
        if self.notationBoldCheck.GetValue(): self.notationFontWeightInteractive = 'bold'
        else: self.notationFontWeightInteractive  = 'normal'
        
        
        # Tools
        self.config.toolsLocation = self.location_combo.GetValue()
         
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
            method = subType.split('__')
            if any(method[0] in item for item in ['Mask', 'Transparent']):
                preset='Overlay'
            elif any(method[0] in item for item in ['RMSD', 'RMSF','Mean',
                                                    'Standard Deviation',
                                                    'Variance',
                                                    'RMSD Matrix']):
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
         
    def onClose(self, evt):
        self.Destroy()
 
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

        if 'page' in dictionary: 
            # If it has page information in dictionary, add it to the config object
            self.config.pageDict[dictionary['page']['name']] = dictionary['page']
            pass
        else: dictionary['page'] = self.config.pageDict['None']

        if 'tools' in dictionary: 
            # If it has page information in dictionary, add it to the config object
            pass
        else: dictionary['tools'] = {}
        
        
        if 'interactive' in dictionary: pass
        else: 
            interactiveDict = {'order':'',
                               'page':self.config.pageDict['None'],
                               'tools':''}
            dictionary['interactive'] = interactiveDict 
        
        return dictionary
                    
    def populateTable(self):
        """
        Populate table with appropriate dataset values
        """
        if len(self.documentsDict) > 0:
            for key in self.documentsDict:
                docData = self.documentsDict[key]                
                if docData.gotMS == True:
                    docData.massSpectrum = self.checkIfHasHTMLkeys(docData.massSpectrum)
                    if docData.massSpectrum['cmap'] == '': docData.massSpectrum['cmap'] = docData.lineColour
                    if len(docData.massSpectrum['tools']) == 0:
                        docData.massSpectrum['tools']['name'] = '1D'
                        docData.massSpectrum['tools']['tools'] = self.getToolSet(plotType='MS')
                    self.itemsList.Append([key, 'MS', '',
                                           docData.massSpectrum['title'],
                                           docData.massSpectrum['header'],
                                           docData.massSpectrum['footnote'],
                                           docData.massSpectrum['cmap'],
                                           docData.massSpectrum['order'],
                                           docData.massSpectrum['page']['name'],
                                           docData.massSpectrum['tools']['name'],
                                           ])
                if docData.got1RT == True:
                    docData.RT = self.checkIfHasHTMLkeys(docData.RT)
                    if docData.RT['cmap'] == '': docData.RT['cmap'] = docData.lineColour
                    if len(docData.RT['tools']) == 0:
                        docData.RT['tools']['name'] = '1D'
                        docData.RT['tools']['tools'] = self.getToolSet(plotType='RT')
                    self.itemsList.Append([key, 'RT', '',
                                           docData.RT['title'],
                                           docData.RT['header'],
                                           docData.RT['footnote'],
                                           docData.RT['cmap'],
                                           docData.RT['order'],
                                           docData.RT['page']['name'],
                                           docData.RT['tools']['name'],
                                           ])
                if docData.got1DT == True:
                    docData.DT = self.checkIfHasHTMLkeys(docData.DT)
                    if docData.DT['cmap'] == '': docData.DT['cmap'] = docData.lineColour
                    if len(docData.DT['tools']) == 0:
                        docData.DT['tools']['name'] = '1D'
                        docData.DT['tools']['tools'] = self.getToolSet(plotType='1D')
                    self.itemsList.Append([key, '1D', '',
                                           docData.DT['title'],
                                           docData.DT['header'],
                                           docData.DT['footnote'],
                                           docData.DT['cmap'],
                                           docData.DT['order'],
                                           docData.DT['page']['name'],
                                           docData.DT['tools']['name'],
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
                                           docData.IMS2D['order'],
                                           docData.IMS2D['page']['name'],
                                           docData.IMS2D['tools']['name'],
                                           ])
                    
                if docData.got2Dprocess == True:
                    docData.IMS2Dprocess = self.checkIfHasHTMLkeys(docData.IMS2Dprocess)
                    if len(docData.IMS2Dprocess['tools']) == 0:
                        docData.IMS2Dprocess['tools']['name'] = '2D'
                        docData.IMS2Dprocess['tools']['tools'] = self.getToolSet(plotType='2D')
                    self.itemsList.Append([key, '2D, Processed', '',
                                           docData.IMS2Dprocess['title'],
                                           docData.IMS2Dprocess['header'],
                                           docData.IMS2Dprocess['footnote'],
                                           docData.IMS2Dprocess['cmap'],
                                           docData.IMS2Dprocess['order'],
                                           docData.IMS2Dprocess['page']['name'],
                                           docData.IMS2Dprocess['tools']['name'],
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
                                               docData.IMS2Dions[innerKey]['order'],
                                               docData.IMS2Dions[innerKey]['page']['name'],
                                               docData.IMS2Dions[innerKey]['tools']['name'],
                                               ])        
                        
                if docData.gotMultipleMS == True:
                    for innerKey in docData.multipleMassSpectrum:
                        docData.multipleMassSpectrum[innerKey] = self.checkIfHasHTMLkeys(docData.multipleMassSpectrum[innerKey])
                        if docData.multipleMassSpectrum[innerKey]['cmap'] == '': docData.multipleMassSpectrum[innerKey]['cmap'] = docData.lineColour
                        if len(docData.multipleMassSpectrum[innerKey]['tools']) == 0:
                            docData.multipleMassSpectrum[innerKey]['tools']['name'] = 'MS'
                            docData.multipleMassSpectrum[innerKey]['tools']['tools'] = self.getToolSet(plotType='MS')
                        self.itemsList.Append([key, 'MS, Multiple', innerKey,
                                               docData.multipleMassSpectrum[innerKey]['title'],
                                               docData.multipleMassSpectrum[innerKey]['header'],
                                               docData.multipleMassSpectrum[innerKey]['footnote'],
                                               docData.multipleMassSpectrum[innerKey]['cmap'],
                                               docData.multipleMassSpectrum[innerKey]['order'],
                                               docData.multipleMassSpectrum[innerKey]['page']['name'],
                                               docData.multipleMassSpectrum[innerKey]['tools']['name'],
                                               ])       
                        
                if docData.gotExtractedDriftTimes == True:
                    for innerKey in docData.IMS1DdriftTimes:
                        docData.IMS1DdriftTimes[innerKey] = self.checkIfHasHTMLkeys(docData.IMS1DdriftTimes[innerKey])
                        if docData.IMS1DdriftTimes[innerKey]['cmap'] == '': docData.IMS1DdriftTimes[innerKey]['cmap'] = docData.lineColour
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
                                               docData.IMS1DdriftTimes[innerKey]['order'],
                                               docData.IMS1DdriftTimes[innerKey]['page']['name'],
                                               docData.IMS1DdriftTimes[innerKey]['tools']['name'],
                                               ])   
                        
                if docData.gotCombinedExtractedIonsRT == True:
                    for innerKey in docData.IMSRTCombIons:
                        docData.IMSRTCombIons[innerKey] = self.checkIfHasHTMLkeys(docData.IMSRTCombIons[innerKey])
                        if docData.IMSRTCombIons[innerKey]['cmap'] == '': docData.IMSRTCombIons[innerKey]['cmap'] = docData.lineColour
                        if len(docData.IMSRTCombIons[innerKey]['tools']) == 0:
                            docData.IMSRTCombIons[innerKey]['tools']['name'] = 'RT'
                            docData.IMSRTCombIons[innerKey]['tools']['tools'] = self.getToolSet(plotType='RT')
                        self.itemsList.Append([key, 'RT, Combined', innerKey,
                                               docData.IMSRTCombIons[innerKey]['title'],
                                               docData.IMSRTCombIons[innerKey]['header'],
                                               docData.IMSRTCombIons[innerKey]['footnote'],
                                               docData.IMSRTCombIons[innerKey]['cmap'],
                                               docData.IMSRTCombIons[innerKey]['order'],
                                               docData.IMSRTCombIons[innerKey]['page']['name'],
                                               docData.IMSRTCombIons[innerKey]['tools']['name'],
                                               ])   
                        
                if docData.gotCombinedExtractedIons == True:
                    for innerKey in docData.IMS2DCombIons:
                        docData.IMS2DCombIons[innerKey] = self.checkIfHasHTMLkeys(docData.IMS2DCombIons[innerKey])
                        if len(docData.IMS2DCombIons[innerKey]['tools']) == 0:
                            docData.IMS2DCombIons[innerKey]['tools']['name'] = '2D'
                            docData.IMS2DCombIons[innerKey]['tools']['tools'] = self.getToolSet(plotType='2D')
                        self.itemsList.Append([key, '2D, Combined', innerKey,
                                               docData.IMS2DCombIons[innerKey]['title'],
                                               docData.IMS2DCombIons[innerKey]['header'],
                                               docData.IMS2DCombIons[innerKey]['footnote'],
                                               docData.IMS2DCombIons[innerKey]['cmap'],
                                               docData.IMS2DCombIons[innerKey]['order'],
                                               docData.IMS2DCombIons[innerKey]['page']['name'],
                                               docData.IMS2DCombIons[innerKey]['tools']['name'],
                                               ])   
                        
                if docData.got2DprocessIons == True:
                    for innerKey in docData.IMS2DionsProcess:
                        docData.IMS2DionsProcess[innerKey] = self.checkIfHasHTMLkeys(docData.IMS2DionsProcess[innerKey])
                        if len(docData.IMS2DionsProcess[innerKey]['tools']) == 0:
                            docData.IMS2DionsProcess[innerKey]['tools']['name'] = '2D'
                            docData.IMS2DionsProcess[innerKey]['tools']['tools'] = self.getToolSet(plotType='2D')
                        self.itemsList.Append([key, '2D, Processed', innerKey,
                                               docData.IMS2DionsProcess[innerKey]['title'],
                                               docData.IMS2DionsProcess[innerKey]['header'],
                                               docData.IMS2DionsProcess[innerKey]['footnote'],
                                               docData.IMS2DionsProcess[innerKey]['cmap'],
                                               docData.IMS2DionsProcess[innerKey]['order'],
                                               docData.IMS2DionsProcess[innerKey]['page']['name'],
                                               docData.IMS2DionsProcess[innerKey]['tools']['name'],
                                               ])   
                        
                # Overlay data
                if docData.gotOverlay == True:
                    for innerKey in docData.IMS2DoverlayData:
                        docData.IMS2DoverlayData[innerKey] = self.checkIfHasHTMLkeys(docData.IMS2DoverlayData[innerKey])
                        if len(docData.IMS2DoverlayData[innerKey]['tools']) == 0:
                            preset, toolSet = self.getToolSet(plotType=None, subType=innerKey)
                            docData.IMS2DoverlayData[innerKey]['tools']['name'] = preset
                            docData.IMS2DoverlayData[innerKey]['tools']['tools'] = toolSet
                        self.itemsList.Append([key, 'Overlay', innerKey,
                                               docData.IMS2DoverlayData[innerKey]['title'],
                                               docData.IMS2DoverlayData[innerKey]['header'],
                                               docData.IMS2DoverlayData[innerKey]['footnote'],
                                               docData.IMS2DoverlayData[innerKey].get('cmap',""),
                                               docData.IMS2DoverlayData[innerKey].get('order',""),
                                               docData.IMS2DoverlayData[innerKey].get('page',"")['name'],
                                               docData.IMS2DoverlayData[innerKey]['tools']['name'],
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
                                               docData.IMS2DstatsData[innerKey]['order'],
                                               docData.IMS2DstatsData[innerKey]['page']['name'],
                                               docData.IMS2DstatsData[innerKey]['tools']['name'],
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
                    self.plotTypeToolsSelect_htmlView
                    ]
        
        for item in itemList:
            item.Enable()
        
        self.currentItem = evt.m_itemIndex
        name = self.itemsList.GetItem(self.currentItem,0).GetText()
        key = self.itemsList.GetItem(self.currentItem,1).GetText()
        innerKey = self.itemsList.GetItem(self.currentItem,2).GetText()
        color = self.itemsList.GetItem(self.currentItem,6).GetText()
        
        boxLabel = ''.join(["Document: ",name,", Type: ", key, ", Details: ", innerKey])
        self.mainBoxHTML.SetLabel(boxLabel)
                
        # Determine which document was selected
        document = self.documentsDict[name]
        if key == 'MS' and innerKey == '': docData = document.massSpectrum
        if key == 'RT' and innerKey == '': docData = document.RT
        if key == '1D' and innerKey == '': docData = document.DT
        if key == '2D' and innerKey == '': docData = document.IMS2D
        if key == '2D, Processed' and innerKey == '': docData = document.IMS2Dprocess
        if key == 'MS, Multiple' and innerKey != '': docData = document.multipleMassSpectrum[innerKey]
        if key == '2D' and innerKey != '': docData = document.IMS2Dions[innerKey]
        if key == 'DT-IMS' and innerKey != '': docData = document.IMS1DdriftTimes[innerKey]
        if key == '1D' and innerKey != '': docData = document.IMS1DdriftTimes[innerKey]
        if key == 'RT, Combined' and innerKey != '': docData = document.IMSRTCombIons[innerKey]
        if key == '2D, Combined' and innerKey != '': docData = document.IMS2DCombIons[innerKey]
        if key == '2D, Processed' and innerKey != '': docData = document.IMS2DionsProcess[innerKey]
        if key == 'Overlay' and innerKey != '': 
            docData = document.IMS2DoverlayData[innerKey]
            overlayMethod = innerKey.split('__')
        if key == 'Statistical' and innerKey != '': docData = document.IMS2DstatsData[innerKey]
        
        # Retrieve information
        title = docData['title']
        header = docData['header']
        footnote = docData['footnote']
        order = docData['order']
        page = docData['page']['name']
        tool = docData['tools']['name']
                     
        # Update item editor
        self.itemName_value.SetValue(title)
        self.itemHeader_value.SetValue(header)
        self.itemFootnote_value.SetValue(footnote)
        self.order_value.SetValue(order)
        self.pageLayoutSelect_htmlView.SetStringSelection(page)
        self.plotTypeToolsSelect_htmlView.SetStringSelection(tool)
        
        if any(key in method for method in ["MS", "RT", "1D", "RT, Combined", 'MS, Multiple', 'DT-IMS']):
            color = (eval(color))
            self.colorBtn.SetBackgroundColour(tuple([np.int(color[0]*255),
                                                     np.int(color[1]*255),
                                                     np.int(color[2]*255)]))
            self.colorBtn.Enable()
            self.comboCmapSelect.Disable()
            self.layout_combo.Disable()
            self.pageLayoutSelect_htmlView.Enable()
        elif any(key in method for method in ["2D", "Statistical","2D, Combined","2D, Processed"]):
            self.comboCmapSelect.SetValue(color)
            self.comboCmapSelect.Enable()
            self.colorBtn.Disable()
            self.layout_combo.Disable()
            self.pageLayoutSelect_htmlView.Enable()
        elif key == 'Overlay' and (overlayMethod[0] == 'Mask' or overlayMethod[0] == 'Transparent'):
            self.layout_combo.Enable()
            self.comboCmapSelect.Disable()
            self.colorBtn.Disable()
#             self.pageLayoutSelect_htmlView.SetStringSelection('None')
            self.pageLayoutSelect_htmlView.Disable()
        else:
            self.comboCmapSelect.Enable()
            self.colorBtn.Enable()
            self.layout_combo.Disable()
            self.pageLayoutSelect_htmlView.Enable()
         
    def getItemData(self, name, key, innerKey):
        # Determine which document was selected
        document = self.documentsDict[name]
        if key == 'MS' and innerKey == '': docData = document.massSpectrum
        if key == 'RT' and innerKey == '': docData = document.RT
        if key == '1D' and innerKey == '': docData = document.DT
        if key == '2D' and innerKey == '': docData = document.IMS2D
        if key == '2D, Processed' and innerKey == '': docData = document.IMS2Dprocess
        if key == 'MS, Multiple' and innerKey != '': docData = document.multipleMassSpectrum[innerKey]
        if key == '2D' and innerKey != '': docData = document.IMS2Dions[innerKey]
        if key == 'DT-IMS' and innerKey != '': docData = document.IMS1DdriftTimes[innerKey]
        if key == '1D' and innerKey != '': docData = document.IMS1DdriftTimes[innerKey]
        if key == 'RT, Combined' and innerKey != '': docData = document.IMSRTCombIons[innerKey]
        if key == '2D, Combined' and innerKey != '': docData = document.IMS2DCombIons[innerKey]
        if key == '2D, Processed' and innerKey != '': docData = document.IMS2DionsProcess[innerKey]
        if key == 'Overlay' and innerKey != '': docData = document.IMS2DoverlayData[innerKey]
        if key == 'Statistical' and innerKey != '': docData = document.IMS2DstatsData[innerKey]
        
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
                                     col=8, label=str(page))
        self.onAnnotateItems(evt=None)
        
    def onChangePageForSelectedItems(self, evt):
        """ This function changes the output page for selected items (batch)"""
        rows = self.itemsList.GetItemCount()
        page = self.pageLayoutSelect_toolbar.GetStringSelection()
        for row in range(rows):
            if self.itemsList.IsChecked(index=row):
                self.currentItem = row
                self.itemsList.SetStringItem(index=row, col=8, label=page)
                self.onAnnotateItems(evt=None)
                       
    def onChangeToolsForItem(self, evt):
        """ This function changes the toolset for selected item """
        if self.currentItem == None: 
            msg = 'Please select item first'
            self.view.SetStatusText(msg, 3)
            return     
        
        # Get current page selection
        tool = self.plotTypeToolsSelect_htmlView.GetStringSelection()
        self.itemsList.SetStringItem(index=self.currentItem, 
                                     col=9, label=str(tool))
        self.onAnnotateItems(evt=None)
        
    def onChangeToolsForSelectedItems(self, evt):
        """ This function changes the toolset for selected items (batch)"""
        rows = self.itemsList.GetItemCount()
        tool = self.plotTypeToolsSelect_toolbar.GetStringSelection()
        
        for row in range(rows):
            if self.itemsList.IsChecked(index=row):
                self.currentItem = row
                self.itemsList.SetStringItem(index=row, col=9, label=str(tool))
                self.onAnnotateItems(evt=None)
#                 
    def onChangeColour(self, evt):
        
        if self.currentItem == None and evt.GetId() == ID_changeColorInteractive:
            msg = 'Please select item first'
            self.view.SetStatusText(msg, 3)
            return        
        if (evt.GetId() == ID_changeColorInteractive 
            or evt.GetId() == ID_changeColorNotationInteractive 
            or evt.GetId() == ID_changeColorBackgroundNotationInteractive):
            # Show dialog and get new colour
            dlg = wx.ColourDialog(self)
            dlg.GetColourData().SetChooseFull(True)
            if dlg.ShowModal() == wx.ID_OK:
                data = dlg.GetColourData()
                newColour = list(data.GetColour().Get())
                newColour255 = list([np.float(newColour[0])/255,
                                     np.float(newColour[1])/255,
                                     np.float(newColour[2])/255])
                if evt.GetId() == ID_changeColorInteractive:
                    self.colorBtn.SetBackgroundColour(newColour)
                    self.itemsList.SetStringItem(index=self.currentItem, 
                                                 col=6, label=str(newColour255))
                elif evt.GetId() == ID_changeColorNotationInteractive:
                    self.notationColorBtn.SetBackgroundColour(newColour)
                    self.config.notationColor = newColour255
                elif evt.GetId() == ID_changeColorBackgroundNotationInteractive:
                    self.notationColorBackgroundBtn.SetBackgroundColour(newColour)
                    self.config.notationBackgroundColor = newColour255
                    
                self.onAnnotateItems(evt=None)
                dlg.Destroy()
            else:
                return
        elif evt.GetId() == ID_changeColormapInteractive:
            colormap = self.comboCmapSelect.GetValue()
            self.itemsList.SetStringItem(index=self.currentItem, 
                                         col=6, label=str(colormap))
            self.onAnnotateItems(evt=None)
        
    def onAnnotateItems(self, evt=None, itemID=None):
        
        # If we only updating dictionary
        if itemID != None:
            self.currentItem = itemID
        else: pass
        
        # Check if is empty
        if self.currentItem == None: return
        name = self.itemsList.GetItem(self.currentItem,0).GetText()
        key = self.itemsList.GetItem(self.currentItem,1).GetText()
        innerKey = self.itemsList.GetItem(self.currentItem,2).GetText()
        color = self.itemsList.GetItem(self.currentItem,6).GetText()
        page = self.itemsList.GetItem(self.currentItem,8).GetText() 
        tool = self.itemsList.GetItem(self.currentItem,9).GetText() # string
        # Get data
        pageData = self.config.pageDict[page]
        tools = self.getToolSet(preset=tool)
        toolSet = {'name':tool, 'tools':tools} # dictionary object
        

        if any(key in method for method in ["MS", "RT", "1D", "RT, Combined", 'MS, Multiple']):
            color = (eval(color))
                
        title = self.itemName_value.GetValue()
        header = self.itemHeader_value.GetValue()
        footnote = self.itemFootnote_value.GetValue()
        orderNum = self.order_value.GetValue()
        
        if key == 'Overlay':
            overlayMethod = innerKey.split('__')
            if overlayMethod[0] == 'Mask' or overlayMethod[0] == 'Transparent':
                pageData = self.config.pageDict['None']
        
        
        # Retrieve and add data to dictionary
        document = self.documentsDict[name]
        
        
        if key == 'MS, Multiple' and innerKey != '': docData = document.multipleMassSpectrum[innerKey]
        if key == 'MS' and innerKey == '': document.massSpectrum = self.addHTMLtagsToDictionary(document.massSpectrum, 
                                                                             title, header, footnote, orderNum, color, pageData, toolSet)
        
        if key == 'RT' and innerKey == '': document.RT = self.addHTMLtagsToDictionary(document.RT, 
                                                                             title, header, footnote, orderNum, color, pageData, toolSet)
        
        if key == '1D' and innerKey == '': document.DT = self.addHTMLtagsToDictionary(document.DT, 
                                                                             title, header, footnote, orderNum, color, pageData, toolSet)
        
        if key == '2D' and innerKey == '': document.IMS2D = self.addHTMLtagsToDictionary(document.IMS2D, 
                                                                             title, header, footnote, orderNum, color, pageData, toolSet)
        
        if key == '2D, Processed' and innerKey == '': document.IMS2Dprocess = self.addHTMLtagsToDictionary(document.IMS2Dprocess, 
                                                                             title, header, footnote, orderNum, color, pageData, toolSet)
        
        if key == '2D, Processed' and innerKey == '': document.IMS2Dprocess = self.addHTMLtagsToDictionary(document.multipleMassSpectrum, 
                                                                             title, header, footnote, orderNum, color, pageData, toolSet)
        
        if key == '2D' and innerKey != '': document.IMS2Dions[innerKey] = self.addHTMLtagsToDictionary(document.IMS2Dions[innerKey], 
                                                                             title, header, footnote, orderNum, color, pageData, toolSet)
        
        if key == 'MS, Multiple' and innerKey != '': document.multipleMassSpectrum[innerKey] = self.addHTMLtagsToDictionary(document.multipleMassSpectrum[innerKey], 
                                                                                                title, header, footnote, orderNum, color, pageData, toolSet)
        
        if key == 'DT-IMS' and innerKey != '': document.IMS1DdriftTimes[innerKey] = self.addHTMLtagsToDictionary(document.IMS1DdriftTimes[innerKey], 
                                                                             title, header, footnote, orderNum, color, pageData, toolSet)
        
        if key == 'RT, Combined' and innerKey != '': document.IMSRTCombIons[innerKey] = self.addHTMLtagsToDictionary(document.IMSRTCombIons[innerKey], 
                                                                             title, header, footnote, orderNum, color, pageData, toolSet)
        
        if key == '2D, Combined' and innerKey != '': document.IMS2DCombIons[innerKey] = self.addHTMLtagsToDictionary(document.IMS2DCombIons[innerKey], 
                                                                             title, header, footnote, orderNum, color, pageData, toolSet)
        
        if key == '2D, Processed' and innerKey != '': document.IMS2DionsProcess[innerKey] = self.addHTMLtagsToDictionary(document.IMS2DionsProcess[innerKey], 
                                                                             title, header, footnote, orderNum, color, pageData, toolSet)
        
        if key == 'Overlay' and innerKey != '': document.IMS2DoverlayData[innerKey] = self.addHTMLtagsToDictionary(document.IMS2DoverlayData[innerKey], 
                                                                             title, header, footnote, orderNum, color, pageData, toolSet)
        
        if key == 'Statistical' and innerKey != '': document.IMS2DstatsData[innerKey] = self.addHTMLtagsToDictionary(document.IMS2DstatsData[innerKey], 
                                                                             title, header, footnote, orderNum, color, pageData, toolSet)


        # Set new text for labels
        self.itemsList.SetStringItem(index=self.currentItem,
                                     col=3, label=title)
        self.itemsList.SetStringItem(index=self.currentItem,
                                     col=4, label=header)
        self.itemsList.SetStringItem(index=self.currentItem,
                                     col=5, label=footnote)
        self.itemsList.SetStringItem(index=self.currentItem,
                                     col=6, label=str(color))
        self.itemsList.SetStringItem(index=self.currentItem,
                                     col=7, label=orderNum)
        self.itemsList.SetStringItem(index=self.currentItem,
                                     col=8, label=page)
        self.itemsList.SetStringItem(index=self.currentItem,
                                     col=9, label=tool)
        # Update dictionary
        self.presenter.documentsDict[document.title] = document
        
    def addHTMLtagsToDictionary(self, dictionary, title, header, footnote, 
                                orderNumber, color, page, toolSet):
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
        
        return dictionary 
                                   
    def prepareDataForInteractivePlots(self, data=None, type=None, subtype=None, title=None,
                                       xlabelIn=None, ylabelIn=None, linkXYAxes=False,
                                       layout='Rows'):
        """
        Prepare data to be in an appropriate format
        """
        
        # Call the helper function to make sure we generated tool list
        self.onSelectTools(evt=None)
        
        if type == 'MS' or type == 'RT' or type == '1D' or type == 'MS, Multiple':
            xvals, yvals, xlabelIn, cmap =  self.presenter.get2DdataFromDictionary(dictionary=data,
                                                                                   plotType='1D',
                                                                                   dataType='plot',
                                                                                   compact=False)
            # Check if we should lock the hoverline
            if self.config.hoverVline:
                hoverMode='vline'
            else:
                hoverMode='mouse'
            # Prepare hover tool
            if type == 'MS' or type == 'MS, Multiple':
                hoverTool = HoverTool(tooltips = [(xlabelIn, '$x{0.00}'),
                                                  (ylabelIn, '$y{0.00}')],
                                      mode=hoverMode) 
            elif type == 'RT':
                hoverTool = HoverTool(tooltips = [(xlabelIn, '$x{0.00}'),
                                                  (ylabelIn, '$y{0.00}'),],
                                      mode=hoverMode) 
            elif type == '1D':
                hoverTool = HoverTool(tooltips = [(xlabelIn, '$x{0.00}'),
                                                  (ylabelIn, '$y{0.00}'),],
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
                print('generic tools')
                TOOLS = [hoverTool,self.tools]
            else: TOOLS = self.tools
            bokehPlot = figure(x_range=(min(xvals), max(xvals)), 
                               y_range=(min(yvals), max(yvals)),
                               tools=TOOLS,
                               active_drag=self.activeDrag,
                               active_scroll=self.activeWheel,
                               plot_width=self.config.figWidth1D, 
                               plot_height=(self.config.figHeight1D), 
                               toolbar_location=self.config.toolsLocation)
            cmap = tuple([np.int(cmap[0]*255), 
                          np.int(cmap[1]*255),
                          np.int(cmap[2]*255)])
            bokehPlot.line(xvals, yvals, line_color=cmap)
            # Add border 
            bokehPlot.outline_line_width = 2
            bokehPlot.outline_line_alpha = 1
            bokehPlot.outline_line_color = "black"
            # X-axis
            bokehPlot.xaxis.axis_label = xlabelIn
            bokehPlot.xaxis.axis_label_text_font_size = self.labelFontSize
            bokehPlot.xaxis.axis_label_text_font_style = self.labelFontWeightInteractive
            bokehPlot.xaxis.major_label_text_font_size = self.tickFontSize
            # Y-axis
            bokehPlot.yaxis.axis_label = ylabelIn
            bokehPlot.yaxis.axis_label_text_font_size = self.labelFontSize
            bokehPlot.yaxis.major_label_text_font_size = self.tickFontSize
            bokehPlot.yaxis.axis_label_text_font_style = self.labelFontWeightInteractive
             
        elif type == '2D':
            # Unpacks data using a helper function
            zvals, xvals, xlabel, yvals, ylabel, cmap = self.presenter.get2DdataFromDictionary(dictionary=data,
                                                                                               dataType='plot',
                                                                                               plotType='2D',
                                                                                               compact=False)
            colormap = cm.get_cmap(cmap) # choose any matplotlib colormap here
            bokehpalette = [colors.rgb2hex(m) for m in colormap(np.arange(colormap.N))]
            hoverTool = HoverTool(tooltips = [(xlabel, '$x{0}'),
                                              (ylabel, '$y{0}')],
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
            bokehPlot = figure(x_range=(min(xvals), max(xvals)), 
                               y_range=(min(yvals), max(yvals)),
                               tools=TOOLS, 
                               active_drag=self.activeDrag,
                               active_scroll=self.activeWheel,
                               plot_width=self.config.figWidth, 
                               plot_height=(self.config.figHeight), 
                               toolbar_location=self.config.toolsLocation)
            bokehPlot.image(image=[zvals], 
                            x=min(xvals), 
                            y=min(yvals), 
                            dw=max(xvals), 
                            dh=max(yvals), 
                            palette=bokehpalette)
            bokehPlot.quad(top=max(yvals), bottom=min(yvals), 
                           left=min(xvals), right=max(xvals), 
                           alpha=0)
            # Add border 
            bokehPlot.outline_line_width = 2
            bokehPlot.outline_line_alpha = 1
            bokehPlot.outline_line_color = "black"
            bokehPlot.min_border_right = 60
            bokehPlot.min_border_left = 60
            bokehPlot.min_border_top = 20
            bokehPlot.min_border_bottom = 60
            # X-axis
            bokehPlot.xaxis.axis_label = xlabel
            bokehPlot.xaxis.axis_label_text_font_size = self.labelFontSize
            bokehPlot.xaxis.axis_label_text_font_style = self.labelFontWeightInteractive
            bokehPlot.xaxis.major_label_text_font_size = self.tickFontSize
            # Y-axis
            bokehPlot.yaxis.axis_label = ylabel
            bokehPlot.yaxis.axis_label_text_font_size = self.labelFontSize
            bokehPlot.yaxis.major_label_text_font_size = self.tickFontSize
            bokehPlot.yaxis.axis_label_text_font_style = self.labelFontWeightInteractive
                
        
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
                for i, namex in enumerate(yxlabels):
                    for j, namey in enumerate(yxlabels):
                        xname.append(namex)
                        yname.append(namey)
                        new_value = ((zvals[i,j] - old_min)/(old_max - old_min))*(new_max - new_min)+new_min
                        color.append(bokehpalette[int(new_value)])
                        alpha.append(min(zvals[i,j]/3.0, 0.9) + 0.1)
                        
                # Create data source
                source = ColumnDataSource(data=dict(xname=xname,
                                                    yname=yname,
                                                    count=zvals.flatten(),
                                                    alphas=alpha,
                                                    colors=color))
                
                bokehPlot = figure(x_range=list(reversed(yxlabels)), 
                                   y_range=yxlabels,
                                   tools=TOOLS, 
                                   active_drag=self.activeDrag,
                                   active_scroll=self.activeWheel,
                                   plot_width=self.config.figWidth, 
                                   plot_height=(self.config.figHeight), 
                                   toolbar_location=self.config.toolsLocation)
                bokehPlot.rect('xname', 
                               'yname', 
                               1, 1, 
                               source=source,
                               line_color=None, 
                               hover_line_color='black',
                               alpha='alphas', 
                               hover_color='colors',
                               color='colors')
                
                # Add border 
                bokehPlot.outline_line_width = 2
                bokehPlot.outline_line_alpha = 1
                bokehPlot.outline_line_color = "black"
                bokehPlot.min_border_right = 60
                bokehPlot.min_border_left = 60
                bokehPlot.min_border_top = 20
                bokehPlot.min_border_bottom = 60
                # X-axis
                bokehPlot.xaxis.axis_label_text_font_size = self.labelFontSize
                bokehPlot.xaxis.axis_label_text_font_style = self.labelFontWeightInteractive
                bokehPlot.xaxis.major_label_text_font_size = self.tickFontSize
                bokehPlot.xaxis.major_label_orientation = np.pi/3
                # Y-axis
                bokehPlot.yaxis.axis_label_text_font_size = self.labelFontSize
                bokehPlot.yaxis.major_label_text_font_size = self.tickFontSize
                bokehPlot.yaxis.axis_label_text_font_style = self.labelFontWeightInteractive
                
                bokehPlot.grid.grid_line_color = None
                bokehPlot.axis.axis_line_color = None
                bokehPlot.axis.major_tick_line_color = None
           
        elif type == 'RMSD':
                zvals, xvals, xlabel, yvals, ylabel, rmsdLabel, cmap = self.presenter.get2DdataFromDictionary(dictionary=data,
                                                                                                                plotType='RMSD',
                                                                                                                compact=True)
                # Calculate position of RMSD label
                rmsdXpos, rmsdYpos = self.presenter.onCalculateRMSDposition(xlist=xvals,
                                                                            ylist=yvals)
                
                colormap =cm.get_cmap(cmap) # choose any matplotlib colormap here
                bokehpalette = [colors.rgb2hex(m) for m in colormap(np.arange(colormap.N))]
                hoverTool = HoverTool(tooltips = [(xlabel, '$x{0}'),
                                                  (ylabel, '$y{0}')],
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
                bokehPlot = figure(x_range=(min(xvals), max(xvals)), 
                                   y_range=(min(yvals), max(yvals)),
                                   tools=TOOLS, 
                                   active_drag=self.activeDrag,
                                   active_scroll=self.activeWheel,
                                   plot_width=self.config.figWidth, 
                                   plot_height=(self.config.figHeight), 
                                   toolbar_location=self.config.toolsLocation)
                bokehPlot.image(image=[zvals], 
                                x=min(xvals), 
                                y=min(yvals), 
                                dw=max(xvals), 
                                dh=max(yvals), 
                                palette=bokehpalette)
                bokehPlot.quad(top=max(yvals), bottom=min(yvals), 
                               left=min(xvals), right=max(xvals), 
                               alpha=0)
                # Add RMSD label to the plot
                textColor = tuple([np.int(self.config.notationColor[0]*255), 
                                  np.int(self.config.notationColor[1]*255), 
                                  np.int(self.config.notationColor[2]*255)])
                
                backgroundColor = tuple([np.int(self.config.notationBackgroundColor[0]*255), 
                                         np.int(self.config.notationBackgroundColor[1]*255), 
                                         np.int(self.config.notationBackgroundColor[2]*255)])
                rmsdAnnot = Label(x=rmsdXpos, y=rmsdYpos, x_units='data', y_units='data',
                                 text=rmsdLabel, 
                                 render_mode='canvas', 
                                 text_color = textColor,
                                 text_font_size=self.notationFontSize,
                                 text_font_style=self.notationFontWeightInteractive,
                                 background_fill_color=backgroundColor, 
                                 background_fill_alpha=1.0)
                bokehPlot.add_layout(rmsdAnnot)
                
                # Add border 
                bokehPlot.outline_line_width = 2
                bokehPlot.outline_line_alpha = 1
                bokehPlot.outline_line_color = "black"
                bokehPlot.min_border_right = 60
                bokehPlot.min_border_left = 60
                bokehPlot.min_border_top = 20
                bokehPlot.min_border_bottom = 60
                # X-axis
                bokehPlot.xaxis.axis_label = xlabel
                bokehPlot.xaxis.axis_label_text_font_size = self.labelFontSize
                bokehPlot.xaxis.axis_label_text_font_style = self.labelFontWeightInteractive
                bokehPlot.xaxis.major_label_text_font_size = self.tickFontSize
                # Y-axis
                bokehPlot.yaxis.axis_label = ylabel
                bokehPlot.yaxis.axis_label_text_font_size = self.labelFontSize
                bokehPlot.yaxis.major_label_text_font_size = self.tickFontSize
                bokehPlot.yaxis.axis_label_text_font_style = self.labelFontWeightInteractive
                
                self.titleFontWeightInteractive
                
        elif type == 'RMSF':
                zvals, yvalsRMSF, xvals, yvals, xlabelRMSD, ylabelRMSD, ylabelRMSF, color, cmap, rmsdLabel = self.presenter.get2DdataFromDictionary(dictionary=data,
                                                                                                                              plotType='RMSF',
                                                                                                                              compact=True)
                if self.config.hoverVline:
                    hoverMode='vline'
                else:
                    hoverMode='mouse'
                
                ylabelRMSF = ''.join([ylabelRMSF]) #, u' (%)'])
                hoverToolRMSF = HoverTool(tooltips = [(xlabelRMSD, '$x{0.00}'),
                                                      (ylabelRMSF, '$y{0.00}'),],
                                          mode=hoverMode) 
                 
                # Prepare MS file
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
                color = tuple([np.int(color[0]*255), 
                              np.int(color[1]*255),
                              np.int(color[2]*255)])
                bokehPlotRMSF.line(xvals, yvalsRMSF, line_color=color)
                # Add border 
                bokehPlotRMSF.outline_line_width = 2
                bokehPlotRMSF.outline_line_alpha = 1
                bokehPlotRMSF.outline_line_color = "black"
                # Y-axis
                bokehPlotRMSF.yaxis.axis_label = ylabelRMSF
                bokehPlotRMSF.yaxis.axis_label_text_font_size = self.labelFontSize
                bokehPlotRMSF.yaxis.major_label_text_font_size = self.tickFontSize
                bokehPlotRMSF.yaxis.axis_label_text_font_style = self.labelFontWeightInteractive
                
                # Calculate position of RMSD label
                rmsdXpos, rmsdYpos = self.presenter.onCalculateRMSDposition(xlist=xvals,
                                                                            ylist=yvals)
                colormap =cm.get_cmap(cmap) # choose any matplotlib colormap here
                bokehpalette = [colors.rgb2hex(m) for m in colormap(np.arange(colormap.N))]
                hoverTool = HoverTool(tooltips = [(xlabelRMSD, '$x{0}'),
                                                  (ylabelRMSD, '$y{0}')],
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

                bokehPlotRMSD.image(image=[zvals], 
                                x=min(xvals), 
                                y=min(yvals), 
                                dw=max(xvals), 
                                dh=max(yvals), 
                                palette=bokehpalette)
                bokehPlotRMSD.quad(top=max(yvals), bottom=min(yvals), 
                               left=min(xvals), right=max(xvals), 
                               alpha=0)
                # Add RMSD label to the plot
                textColor = tuple([np.int(self.config.notationColor[0]*255), 
                                  np.int(self.config.notationColor[1]*255), 
                                  np.int(self.config.notationColor[2]*255)])
                
                backgroundColor = tuple([np.int(self.config.notationBackgroundColor[0]*255), 
                                         np.int(self.config.notationBackgroundColor[1]*255), 
                                         np.int(self.config.notationBackgroundColor[2]*255)])
                rmsdAnnot = Label(x=rmsdXpos, y=rmsdYpos, x_units='data', y_units='data',
                                 text=rmsdLabel, 
                                 render_mode='canvas', 
                                 text_color = textColor,
                                 text_font_size=self.notationFontSize,
                                 text_font_style=self.notationFontWeightInteractive,
                                 background_fill_color=backgroundColor, 
                                 background_fill_alpha=1.0)
                bokehPlotRMSD.add_layout(rmsdAnnot)
                
                # Add border 
                bokehPlotRMSD.outline_line_width = 2
                bokehPlotRMSD.outline_line_alpha = 1
                bokehPlotRMSD.outline_line_color = "black"
                bokehPlotRMSD.min_border_right = 60
                bokehPlotRMSD.min_border_left = 60
                bokehPlotRMSD.min_border_top = 20
                bokehPlotRMSD.min_border_bottom = 60
                # X-axis
                bokehPlotRMSD.xaxis.axis_label = xlabelRMSD
                bokehPlotRMSD.xaxis.axis_label_text_font_size = self.labelFontSize
                bokehPlotRMSD.xaxis.axis_label_text_font_style = self.labelFontWeightInteractive
                bokehPlotRMSD.xaxis.major_label_text_font_size = self.tickFontSize
                # Y-axis
                bokehPlotRMSD.yaxis.axis_label = ylabelRMSD
                bokehPlotRMSD.yaxis.axis_label_text_font_size = self.labelFontSize
                bokehPlotRMSD.yaxis.major_label_text_font_size = self.tickFontSize
                bokehPlotRMSD.yaxis.axis_label_text_font_style = self.labelFontWeightInteractive
                
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
                    # TOOLS1 tools + hover
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
                    # TOOLS1 tools + hover
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
                plot.outline_line_width = 2
                plot.outline_line_alpha = 1
                plot.outline_line_color = "black"
                plot.min_border_right = 60
                plot.min_border_left = 60
                plot.min_border_top = 20
                plot.min_border_bottom = 60
            
            if layout=='Rows':
                for plot in [leftPlot, rightPlot]:
                    plot.xaxis.axis_label = xlabel
                    plot.xaxis.axis_label_text_font_size = self.labelFontSize
                    plot.xaxis.axis_label_text_font_style = self.labelFontWeightInteractive
                    plot.xaxis.major_label_text_font_size = self.tickFontSize
                leftPlot.yaxis.axis_label = ylabel
                leftPlot.yaxis.axis_label_text_font_size = self.labelFontSize
                leftPlot.yaxis.major_label_text_font_size = self.tickFontSize
                leftPlot.yaxis.axis_label_text_font_style =  self.labelFontWeightInteractive
                # Remove tick values from right plot
                rightPlot.yaxis.major_label_text_color = None  # turn off y-axis tick labels leaving space 
                bokehPlot =  gridplot([[leftPlot, rightPlot]])
            elif layout=='Columns':
                for plot in [leftPlot, rightPlot]:
                    plot.yaxis.axis_label = ylabel
                    plot.yaxis.axis_label_text_font_size = self.labelFontSize
                    plot.yaxis.major_label_text_font_size = self.tickFontSize
                    plot.yaxis.axis_label_text_font_style =  self.labelFontWeightInteractive
                leftPlot.xaxis.major_label_text_color = None  # turn off y-axis tick labels leaving space 
                rightPlot.xaxis.axis_label = xlabel
                rightPlot.xaxis.axis_label_text_font_size = self.labelFontSize
                rightPlot.xaxis.axis_label_text_font_style =  self.labelFontWeightInteractive
                rightPlot.xaxis.major_label_text_font_size = self.tickFontSize
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
                listOfPages.append(self.itemsList.GetItem(item,8).GetText())
                
        listOfPages = list(set(listOfPages))
        
        # This dictionary acts as a temporary holding space for each
        # individual plot
        plotDict = {}
        # Pre-populate the dictionary with keys
        for key in listOfPages:
            plotDict[key] = []
            
        # Sort the list based on which page each item belongs to
        if len(listOfPages) > 1:
            self.OnSortByColumn(column=8)

        if len(listOfPages) == 0:
            msg = 'Please select items to plot'
            dialogs.dlgBox(exceptionTitle='No plots were selected', 
                           exceptionMsg= msg,
                           type="Warning")
        
        for item in xrange(self.itemsList.GetItemCount()):
            if self.itemsList.IsChecked(index=item):
                self.onAnnotateItems(evt=None, itemID=item)
                name = self.itemsList.GetItem(item,0).GetText()
                key = self.itemsList.GetItem(item,1).GetText()
                innerKey = self.itemsList.GetItem(item,2).GetText()
                pageTable = self.itemsList.GetItem(item,8).GetText()
                data = self.getItemData(name, key, innerKey)
                title = data['title']
                header = data['header']
                footnote = data['footnote']
                page = data['page']
                # Check that the page names agree. If they don't, the table page
                # name takes priority as it has been pre-emptively added to the
                # plotDict dictionary
                if pageTable != page['name']:
                    msg = 'Overriding page name'
                    self.view.SetStatusText(msg, 3)
                    page = self.config.pageDict[pageTable] 
                    
                if title == '':
                    msg = 'Overriding title'
                    self.view.SetStatusText(msg, 3)
                    title = key
                 
                if any(key in itemType for itemType in ['MS', 'MS, Multiple', 
                                                        'RT', '1D']):
                    width = self.config.figWidth1D
                else:
                    width = self.config.figWidth 
                
                # Generate header and footnote information
                divHeader = Div(text=str(header), width=width)
                markupHeader = widgetbox(divHeader, width=width)
                divFootnote = Div(text=str(footnote), width=width)
                markupFootnote = widgetbox(divFootnote, width=width)
                
                bokehPlot = None
                # Now generate plot                
                if key == 'MS' or key == 'MS, Multiple':
                    bokehPlot = self.prepareDataForInteractivePlots(data=data, 
                                                                    type='MS', 
                                                                    title=title,
                                                                    xlabelIn='m/z',
                                                                    ylabelIn='Intensity')
                     
                elif key =='2D' or key == '2D, Combined' or key == '2D, Processed':
                    bokehPlot = self.prepareDataForInteractivePlots(data=data, 
                                                                    type='2D', 
                                                                    title=title)
                     
                elif key == 'RT':
                    bokehPlot = self.prepareDataForInteractivePlots(data=data, 
                                                                    type='RT', 
                                                                    title=title,
                                                                    ylabelIn='Intensity')
                     
                elif key == '1D':
                    bokehPlot = self.prepareDataForInteractivePlots(data=data, 
                                                                    type='1D', 
                                                                    title=title,
                                                                    ylabelIn='Intensity')
                elif key =='Overlay':
                    overlayMethod = innerKey.split('__')
                    if overlayMethod[0] == 'Mask' or overlayMethod[0] == 'Transparent':
                        bokehPlot = self.prepareDataForInteractivePlots(data=data, 
                                                                        type='Overlay', 
                                                                        subtype=overlayMethod[0],
                                                                        title=title,
                                                                        linkXYAxes=self.config.linkXYaxes,
                                                                        layout=self.config.plotLayoutOverlay)
                    elif overlayMethod[0] == 'RMSF': 
                        bokehPlot = self.prepareDataForInteractivePlots(data=data, 
                                                                        type='RMSF', 
                                                                        linkXYAxes=self.config.linkXYaxes,
                                                                        title=title)
                    elif overlayMethod[0] == 'RMSD': 
                        bokehPlot = self.prepareDataForInteractivePlots(data=data, 
                                                                        type='RMSD', 
                                                                        title=title)
                    elif overlayMethod[0] == '1D' or overlayMethod[0] == 'RT':
                        msg = "Cannot export '%s - %s (%s)' in an interactive format yet - it will be available in the future updates. For now, please deselect it in the table. LM" % (overlayMethod[0], key, innerKey)
                        dialogs.dlgBox(exceptionTitle='Not supported yet', 
                                       exceptionMsg= msg,
                                       type="Error")
                        continue
                        
                        
                elif key =='Statistical':
                    overlayMethod = innerKey.split('__')
                    if (overlayMethod[0] == 'Variance' or 
                        overlayMethod[0] == 'Mean' or 
                        overlayMethod[0] == 'Standard Deviation'):
                        bokehPlot = self.prepareDataForInteractivePlots(data=data, 
                                                                        type='2D', 
                                                                        title=title)
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
                    print('Plot is empty')
                    return
                
                # Generate layout
                bokehLayout = layout([markupHeader],
                                     [bokehPlot], 
                                     [markupFootnote], 
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
        
        
        outputList = []
        
        outList = []
        for pageKey in plotDict:
            if self.config.pageDict[pageKey]['layout'] == 'Individual':
                if len(plotDict[pageKey]) > 1:
                    for plot in range(len(plotDict[pageKey])):
                        outList.append(plotDict[pageKey][plot])
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
#             bokehOutput = outList
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
                tempRow.append(item.GetText())
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
        filter = self.dataSelection_combo.GetValue()
        docFilter = self.docSelection_combo.GetValue()
        
        if filter == 'Show Selected': 
            for row in range(rows):
                tempRow = []
                if self.itemsList.IsChecked(index=row) and docFilter == 'All':
                    for col in range(columns):
                        item = self.itemsList.GetItem(itemId=row, col=col)
                        tempRow.append(item.GetText())
                    tempData.append(tempRow)
                elif self.itemsList.IsChecked(index=row) and docFilter != 'All':
                    if self.itemsList.GetItem(itemId=row, col=0).GetText() == docFilter:
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
            criteria = ['MS', 'RT', '1D', '2D', '2D, Processed', 'DT-IMS',
                        'RT, Combined', '2D, Combined', 'Overlay', 'Statistical', 
                        'MS, Multiple']
        elif filter == 'Show MS':
            criteria = ['MS']
        elif filter == 'Show MS (multiple files)':
            criteria = ['MS, Multiple']
        elif filter == 'Show RT':
            criteria = ['RT']
        elif filter == 'Show 1D IM-MS':
            criteria = ['1D']
        elif filter == 'Show 1D plots (MS, DT, RT)':
            criteria = ['1D', 'MS', 'RT']
        elif filter == 'Show 2D IM-MS':
            criteria = ['2D', '2D, Processed', '2D, Combined']
        elif filter == 'Show Overlay':
            criteria = ['Overlay']
        elif filter == 'Show Statistical':
            criteria = ['Statistical']

        # Iterate over row and columns to get data
        for row in range(rows):
            tempRow = []
            itemType = self.itemsList.GetItem(itemId=row, col=1).GetText()
            if any(itemType in dataType for dataType in criteria) and docFilter == 'All': 
                for col in range(columns):
                    item = self.itemsList.GetItem(itemId=row, col=col)
                    tempRow.append(item.GetText())
                tempData.append(tempRow)
            elif any(itemType in dataType for dataType in criteria) and docFilter != 'All':
                if self.itemsList.GetItem(itemId=row, col=0).GetText() == docFilter:
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

class ListCtrl(wx.ListCtrl, listmix.CheckListCtrlMixin):
    """ListCtrl"""
     
    def __init__(self, parent, id=-1, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.LC_REPORT):
        wx.ListCtrl.__init__(self, parent, id, pos, size, style)
        listmix.CheckListCtrlMixin.__init__(self)
         
       
            