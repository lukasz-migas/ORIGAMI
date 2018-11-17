# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
#    Copyright (C) 2017-2018 Lukasz G. Migas 
#    <lukasz.migas@manchester.ac.uk> OR <lukas.migas@yahoo.com>
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
# __author__ lukasz.g.migas

import wx, os
from copy import deepcopy

from styles import (layout, makeCheckbox, makeToggleBtn, makeSuperTip,
                    makeStaticBox, makeStaticText, validator)
from help import OrigamiHelp as help
from toolbox import str2num, convertRGB1to255, convertRGB255to1


class panelCustomiseInteractive(wx.MiniFrame):
    """
    Panel where you can customise interactive plots
    """
    
    def __init__(self, presenter, parent, config, icons, **kwargs):
        wx.MiniFrame.__init__(self, parent, -1, 
                        'Customise interactive plot...', size=(-1, -1),
                        style=wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER
                          )
        
        self._loading_ = True
        self.presenter = presenter
        self.parent = parent
        self.config = config
        self.icons = icons
        self.help = help()
        
        # retrieve data from kwargs
        self.data = kwargs.pop("data")
        self.document_title = kwargs.pop("document_title")
        self.item_type = kwargs.pop("item_type")
        self.item_title = kwargs.pop("item_title")
        self.kwargs = deepcopy(self.data.get("interactive_params", {}))
        
        self._checkInteractiveParameters()
        
        # make gui items
        self.makeGUI()
        self.Layout()
        self.SetSize((500, 500))
        self.SetMinSize((521, 500))
        self.SetFocus()
        
        # bind
        wx.EVT_CLOSE(self, self.onClose)
        self.Bind(wx.EVT_CHAR_HOOK, self.OnKey)
        
        self.onEnableDisable_widgets(None)
        
        msg = "Customising parameters of: {} - {} - {}".format(
            self.document_title, self.item_type, self.item_title)
        print(msg)
        self._loading_ = False
        
        self.parent.onUpdateItemParameters(self.document_title, 
                                           self.item_type,
                                           self.item_title, 
                                           self.kwargs)
        
    def OnKey(self, evt):
        """Respond to key press"""
        keyCode = evt.GetKeyCode()
        if keyCode == wx.WXK_ESCAPE: # key = esc
            self.onClose(evt=None)
        
        if evt != None:
            evt.Skip()
        
    def onClose(self, evt):
        """Destroy this frame."""
        self.Destroy()
        
    def _checkInteractiveParameters(self):
        
        if "widgets" not in self.kwargs:
            self.kwargs['widgets'] = {}
            
        if "legend_properties" not in self.kwargs:
            self.kwargs['legend_properties'] = {}
            
        if "frame_properties" not in self.kwargs:
            self.kwargs['frame_properties'] = {}
            
        if "plot_width" not in self.kwargs:
            self.kwargs['plot_width'] = self.config.figWidth
        if "plot_height" not in self.kwargs:
            self.kwargs['plot_height'] = self.config.figHeight

        if "xlimits" not in self.kwargs:
            self.kwargs['xlimits'] = None
        if "ylimits" not in self.kwargs:
            self.kwargs['ylimits'] = None
            
    def makeGUI(self):
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        # Setup notebook
        self.mainBook = wx.Notebook(self, wx.ID_ANY, wx.DefaultPosition,
                                    wx.DefaultSize, 0)
#         # About
#         self.settings_about = wx.Panel(self.mainBook, wx.ID_ANY, wx.DefaultPosition,
#                                           wx.DefaultSize, wx.TAB_TRAVERSAL|wx.NB_MULTILINE)
#         self.mainBook.AddPage(self.makeAboutPanel(self.settings_about), u"About", False)
        # Frame
        self.settings_general = wx.Panel(self.mainBook, wx.ID_ANY, wx.DefaultPosition,
                                          wx.DefaultSize, wx.TAB_TRAVERSAL|wx.NB_MULTILINE)
        self.mainBook.AddPage(self.makeGeneralPanel(self.settings_general), u"General", False)
#         
#         # 1D plots
#         self.settings_1D = wx.Panel(self.mainBook, wx.ID_ANY, wx.DefaultPosition,
#                                           wx.DefaultSize, wx.TAB_TRAVERSAL|wx.NB_MULTILINE)
#         self.mainBook.AddPage(self.make1DPanel(self.settings_1D), u"Plots (1D)", False)
#         
#         # 2D plots
#         self.settings_2D = wx.Panel(self.mainBook, wx.ID_ANY, wx.DefaultPosition,
#                                           wx.DefaultSize, wx.TAB_TRAVERSAL|wx.NB_MULTILINE)
#         self.mainBook.AddPage(self.make2DPanel(self.settings_2D), u"Plots (2D)", False)
#         
#         # overlay 
#         self.settings_overlay = wx.Panel(self.mainBook, wx.ID_ANY, wx.DefaultPosition,
#                                           wx.DefaultSize, wx.TAB_TRAVERSAL|wx.NB_MULTILINE)
#         self.mainBook.AddPage(self.makeOverlayPanel(self.settings_overlay), u"Overlay", False)
#         
#         # waterfall
#         self.settings_waterfall = wx.Panel(self.mainBook, wx.ID_ANY, wx.DefaultPosition,
#                                           wx.DefaultSize, wx.TAB_TRAVERSAL|wx.NB_MULTILINE)
#         self.mainBook.AddPage(self.makeWaterfallPanel(self.settings_waterfall), u"Waterfall", False)
         
        # legend
        self.settings_legend = wx.Panel(self.mainBook, wx.ID_ANY, wx.DefaultPosition,
                                          wx.DefaultSize, wx.TAB_TRAVERSAL|wx.NB_MULTILINE)
        self.mainBook.AddPage(self.makeLegendPanel(self.settings_legend), u"Legend", False)
         
#         # colorbar
#         self.settings_colorbar = wx.Panel(self.mainBook, wx.ID_ANY, wx.DefaultPosition,
#                                           wx.DefaultSize, wx.TAB_TRAVERSAL|wx.NB_MULTILINE)
#         self.mainBook.AddPage(self.makeColorbarPanel(self.settings_colorbar), u"Colorbar", False)
        
        
        # widgets
        self.settings_widgets = wx.Panel(self.mainBook, wx.ID_ANY, wx.DefaultPosition,
                                          wx.DefaultSize, wx.TAB_TRAVERSAL|wx.NB_MULTILINE)
        self.mainBook.AddPage(self.makeWidgetsPanel(self.settings_widgets), u"Widgets", False)
        
    def makeAboutPanel(self, panel):
        
        # pack elements
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        
        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)
        
        return panel
    
    def makeGeneralPanel(self, panel):
        
        figure_height_label = makeStaticText(panel, u"Height:")
        self.figure_height_value = wx.SpinCtrlDouble(
            panel, wx.ID_ANY, min=0, max=2000, inc=100, size=(70,-1),
            value=str(self.kwargs.get("plot_height",  self.config.figHeight1D)),
            initial=self.kwargs.get("plot_height", self.config.figHeight1D))
        self.figure_height_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_general)
        
        figure_width_label = makeStaticText(panel, u"Width:")
        self.figure_width_value = wx.SpinCtrlDouble(
            panel, wx.ID_ANY, min=0, max=2000, inc=100, size=(70,-1),
            value=str(self.kwargs.get("plot_width", self.config.figWidth1D)),
            initial=self.kwargs.get("plot_width", self.config.figWidth1D))
        self.figure_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_general)
        
        figureSize_staticBox = makeStaticBox(
            panel, "Figure parameters", size=(-1, -1), color=wx.BLACK)
        figureSize_staticBox.SetSize((-1,-1))
        figureSize_box_sizer = wx.StaticBoxSizer(figureSize_staticBox, wx.HORIZONTAL)    
        grid = wx.GridBagSizer(2, 2)
        y = 0
        grid.Add(figure_height_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.figure_height_value, (y,1), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(figure_width_label, (y,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.figure_width_value, (y,3), flag=wx.ALIGN_CENTER_VERTICAL)
        figureSize_box_sizer.Add(grid, 0, wx.EXPAND, 10)
        
        
        plot_xmin_label = makeStaticText(panel, u"X min:")
        self.plot_xmin_value = wx.TextCtrl(
            panel, -1, "", size=(80, -1), validator=validator('float'))
        self.plot_xmin_value.Bind(wx.EVT_TEXT, self.onApply_general)
        
        plot_xmax_label = makeStaticText(panel, u"X max:")
        self.plot_xmax_value = wx.TextCtrl(
            panel, -1, "", size=(80, -1), validator=validator('float'))
        self.plot_xmax_value.Bind(wx.EVT_TEXT, self.onApply_general)
    
        if self.kwargs['xlimits'] is not None:
            try: self.plot_xmin_value.SetValue(str(float(self.kwargs['xlimits'][0])))
            except: pass
            try: self.plot_xmax_value.SetValue(str(float(self.kwargs['xlimits'][1])))
            except: pass
        
        plot_ymin_label = makeStaticText(panel, u"Y min:")
        self.plot_ymin_value = wx.TextCtrl(
            panel, -1, "", size=(80, -1), validator=validator('float'))
        self.plot_ymin_value.Bind(wx.EVT_TEXT, self.onApply_general)
        
        plot_ymax_label = makeStaticText(panel, u"Y max:")
        self.plot_ymax_value = wx.TextCtrl(
            panel, -1, "", size=(80, -1), validator=validator('float'))
        self.plot_ymax_value.Bind(wx.EVT_TEXT, self.onApply_general)
        
        # set y-mins
        if self.kwargs['ylimits'] is not None:
            try: self.plot_ymin_value.SetValue(str(float(self.kwargs['ylimits'][0])))
            except: pass
            try: self.plot_ymax_value.SetValue(str(float(self.kwargs['ylimits'][1])))
            except: pass
        
        # axes parameters
        plotSize_staticBox = makeStaticBox(
            panel, "Plot parameters", size=(-1, -1), color=wx.BLACK)
        plotSize_staticBox.SetSize((-1,-1))
        plotSize_box_sizer = wx.StaticBoxSizer(plotSize_staticBox, wx.HORIZONTAL)    
        grid = wx.GridBagSizer(2, 2)
        y = 0
        grid.Add(plot_xmin_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.plot_xmin_value, (y,1), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(plot_xmax_label, (y,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.plot_xmax_value, (y,3), flag=wx.ALIGN_CENTER_VERTICAL)
        y = y+1
        grid.Add(plot_ymin_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.plot_ymin_value, (y,1), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(plot_ymax_label, (y,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.plot_ymax_value, (y,3), flag=wx.ALIGN_CENTER_VERTICAL)
        plotSize_box_sizer.Add(grid, 0, wx.EXPAND, 10)
        
        
        label_fontsize_label = makeStaticText(panel, u"Label font size")
        self.frame_label_fontsize = wx.SpinCtrlDouble(
            panel, wx.ID_ANY, min=0, max=32, inc=2, size=(50,-1),
            value=str(self.kwargs.get("frame_properties", {}).get("label_fontsize", self.config.interactive_label_fontSize)),
            initial=self.kwargs.get("frame_properties", {}).get("label_fontsize", self.config.interactive_label_fontSize))
        self.frame_label_fontsize.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_general)
        self.frame_label_fontsize.SetToolTip(wx.ToolTip("Label font size. Value in points."))
        
        self.frame_label_weight = makeCheckbox(panel, u"bold", name="frame")
        self.frame_label_weight.SetValue(
            self.kwargs.get("frame_properties", {}).get("label_fontweight", self.config.interactive_label_weight))
        self.frame_label_weight.Bind(wx.EVT_CHECKBOX, self.onApply_general)
        self.frame_label_weight.SetToolTip(wx.ToolTip("Label font weight."))
        
        ticks_fontsize_label = makeStaticText(panel, u"Tick font size")
        self.frame_ticks_fontsize = wx.SpinCtrlDouble(
            panel, wx.ID_ANY, min=0, max=32, inc=2, size=(50,-1),
            value=str(self.kwargs.get("frame_properties", {}).get("tick_fontsize", self.config.interactive_tick_fontSize)),
            initial=self.kwargs.get("frame_properties", {}).get("tick_fontsize", self.config.interactive_tick_fontSize))
        self.frame_ticks_fontsize.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_general)
        self.frame_ticks_fontsize.SetToolTip(wx.ToolTip("Tick font size. Value in points."))
        
        # axes parameters
        fontSize_staticBox = makeStaticBox(
            panel, "Font parameters", size=(-1, -1), color=wx.BLACK)
        fontSize_staticBox.SetSize((-1,-1))
        fontSize_box_sizer = wx.StaticBoxSizer(fontSize_staticBox, wx.HORIZONTAL)    
        grid = wx.GridBagSizer(2, 2)
        y = 0
        grid.Add(label_fontsize_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.frame_label_fontsize, (y,1), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.frame_label_weight, (y,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        y = y+1
        grid.Add(ticks_fontsize_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.frame_ticks_fontsize, (y,1), flag=wx.ALIGN_CENTER_VERTICAL)
        fontSize_box_sizer.Add(grid, 0, wx.EXPAND, 10)
        
        label_label = wx.StaticText(panel, -1, "Label:")
        self.frame_label_xaxis_check = makeCheckbox(panel, u"x-axis", name="frame")
        self.frame_label_xaxis_check.SetValue(
            self.kwargs.get("frame_properties", {}).get("label_xaxis", True))
        self.frame_label_xaxis_check.Bind(wx.EVT_CHECKBOX, self.onApply_general)
        self.frame_label_xaxis_check.SetToolTip(wx.ToolTip("Show labels on the x-axis."))
        
        self.frame_label_yaxis_check = makeCheckbox(panel, u"y-axis", name="frame")
        self.frame_label_yaxis_check.SetValue(
            self.kwargs.get("frame_properties", {}).get("label_yaxis", True))
        self.frame_label_yaxis_check.Bind(wx.EVT_CHECKBOX, self.onApply_general)
        self.frame_label_yaxis_check.SetToolTip(wx.ToolTip("Show labels on the y-axis."))
        
        tickLabels_label = wx.StaticText(panel, -1, "Tick labels:")
        self.frame_tick_labels_xaxis_check = makeCheckbox(panel, u"x-axis", name="frame")
        self.frame_tick_labels_xaxis_check.SetValue(
            self.kwargs.get("frame_properties", {}).get("tick_labels_xaxis", True))
        self.frame_tick_labels_xaxis_check.Bind(wx.EVT_CHECKBOX, self.onApply_general)
        self.frame_tick_labels_xaxis_check.SetToolTip(wx.ToolTip("Show tick labels on the x-axis"))
        
        self.frame_tick_labels_yaxis_check = makeCheckbox(panel, u"y-axis", name="frame")
        self.frame_tick_labels_yaxis_check.SetValue(
            self.kwargs.get("frame_properties", {}).get("tick_labels_yaxis", True))
        self.frame_tick_labels_yaxis_check.Bind(wx.EVT_CHECKBOX, self.onApply_general)
        self.frame_tick_labels_yaxis_check.SetToolTip(wx.ToolTip("Show tick labels on the y-axis"))
        
        ticks_label = wx.StaticText(panel, -1, "Ticks:")
        self.frame_ticks_xaxis_check = makeCheckbox(panel, u"x-axis", name="frame")
        self.frame_ticks_xaxis_check.SetValue(
            self.kwargs.get("frame_properties", {}).get("ticks_xaxis", True))
        self.frame_ticks_xaxis_check.Bind(wx.EVT_CHECKBOX, self.onApply_general)
        self.frame_ticks_xaxis_check.SetToolTip(wx.ToolTip("Show ticks on the x-axis"))
        
        self.frame_ticks_yaxis_check = makeCheckbox(panel, u"y-axis", name="frame")
        self.frame_ticks_yaxis_check.SetValue(
            self.kwargs.get("frame_properties", {}).get("ticks_yaxis", True))
        self.frame_ticks_yaxis_check.Bind(wx.EVT_CHECKBOX, self.onApply_general)
        self.frame_ticks_yaxis_check.SetToolTip(wx.ToolTip("Show ticks on the y-axis"))
        
        borderLeft_label = makeStaticText(panel, u"Border\nleft")
        self.frame_border_min_left = wx.SpinCtrlDouble(
            panel, wx.ID_ANY, min=0, max=100, inc=5, size=(50,-1),
            value=str(self.kwargs.get("frame_properties", {}).get("border_left", self.config.interactive_border_min_left)),
            initial=int(self.kwargs.get("frame_properties", {}).get("border_left", self.config.interactive_border_min_left)))
        self.frame_border_min_left.SetToolTip(wx.ToolTip("Set minimum border size (pixels)"))
        self.frame_border_min_left.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_general)
        
        borderRight_label = makeStaticText(panel, u"Border\nright")
        self.frame_border_min_right = wx.SpinCtrlDouble(
            panel, wx.ID_ANY, min=0, max=100, inc=5, size=(50,-1),
            value=str(self.kwargs.get("frame_properties", {}).get("border_right", self.config.interactive_border_min_right)),
            initial=int(self.kwargs.get("frame_properties", {}).get("border_right", self.config.interactive_border_min_right)))
        self.frame_border_min_right.SetToolTip(wx.ToolTip("Set minimum border size (pixels)"))
        self.frame_border_min_right.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_general)

        borderTop_label = makeStaticText(panel, u"Border\ntop")
        self.frame_border_min_top = wx.SpinCtrlDouble(
            panel, wx.ID_ANY, min=0, max=100, inc=5, size=(50,-1),
            value=str(self.kwargs.get("frame_properties", {}).get("border_top", self.config.interactive_border_min_top)),
            initial=int(self.kwargs.get("frame_properties", {}).get("border_top", self.config.interactive_border_min_top)))
        self.frame_border_min_top.SetToolTip(wx.ToolTip("Set minimum border size (pixels)"))
        self.frame_border_min_top.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_general)

        borderBottom_label = makeStaticText(panel, u"Border\nbottom")
        self.frame_border_min_bottom = wx.SpinCtrlDouble(
            panel, wx.ID_ANY, min=0, max=100, inc=5, size=(50,-1),
            value=str(self.kwargs.get("frame_properties", {}).get("border_bottom", self.config.interactive_border_min_bottom)),
            initial=int(self.kwargs.get("frame_properties", {}).get("border_bottom", self.config.interactive_border_min_bottom)))
        self.frame_border_min_bottom.SetToolTip(wx.ToolTip("Set minimum border size (pixels)"))
        self.frame_border_min_bottom.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_general)

        outlineWidth_label = makeStaticText(panel, u"Outline\nwidth")
        self.frame_outline_width = wx.SpinCtrlDouble(
            panel, wx.ID_ANY, min=0, max=5, inc=0.5, size=(50,-1),
            value=str(self.kwargs.get("frame_properties", {}).get("outline_width", self.config.interactive_outline_width)),
            initial=self.kwargs.get("frame_properties", {}).get("outline_width", self.config.interactive_outline_width))
        self.frame_outline_width.SetToolTip(wx.ToolTip("Plot outline line thickness"))
        self.frame_outline_width.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_general)

        outlineTransparency_label = makeStaticText(panel, u"Outline\nalpha")
        self.frame_outline_alpha = wx.SpinCtrlDouble(
            panel, wx.ID_ANY, min=0, max=1, inc=0.05, size=(50,-1),
            value=str(self.kwargs.get("frame_properties", {}).get("outline_alpha", self.config.interactive_outline_alpha)),
            initial=self.kwargs.get("frame_properties", {}).get("outline_alpha", self.config.interactive_outline_alpha))
        self.frame_outline_alpha.SetToolTip(wx.ToolTip("Plot outline line transparency value"))
        self.frame_outline_alpha.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_general)
        
        frame_background_color= makeStaticText(panel, u"Background\ncolor")
        self.frame_background_colorBtn = wx.Button(panel, wx.ID_ANY, size=wx.Size(26, 26),
                                                   name="background_color")
        self.frame_background_colorBtn.SetBackgroundColour(
            convertRGB1to255(self.kwargs.get("frame_properties", {}).get(
                "background_color", self.config.interactive_background_color)))
        self.frame_background_colorBtn.Bind(wx.EVT_BUTTON, self.onApply_color)
        
        frame_gridline_label = makeStaticText(panel, u"Grid lines:")
        self.frame_gridline_check = makeCheckbox(panel, u"show")
        self.frame_gridline_check.SetValue(
            self.kwargs.get("frame_properties", {}).get("gridline", self.config.interactive_grid_line))
        self.frame_gridline_check.Bind(wx.EVT_CHECKBOX, self.onApply_general)
        self.frame_gridline_check.SetToolTip(wx.ToolTip("Show gridlines in the plot area."))

        self.frame_gridline_color = wx.Button(panel, wx.ID_ANY, u"",  size=wx.Size(26, 26), name="gridline_color")
        self.frame_gridline_color.SetBackgroundColour(
            convertRGB1to255(self.kwargs.get("frame_properties", {}).get(
                "gridline_color", self.config.interactive_grid_line_color)))
        self.frame_gridline_color.Bind(wx.EVT_BUTTON, self.onApply_color)
        self.frame_gridline_check.SetToolTip(wx.ToolTip("Gridlines color. Only takes effect if gridlines are shown."))
         
        # axes parameters
        frameParameters_staticBox = makeStaticBox(
            panel, "Frame parameters", size=(-1, -1), color=wx.BLACK)
        frameParameters_staticBox.SetSize((-1,-1))
        frame_box_sizer = wx.StaticBoxSizer(frameParameters_staticBox, wx.HORIZONTAL)    
        axis_grid = wx.GridBagSizer(2, 2)
        y = 0
        axis_grid.Add(label_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        axis_grid.Add(self.frame_label_xaxis_check, (y,1), flag=wx.ALIGN_CENTER_VERTICAL)
        axis_grid.Add(self.frame_label_yaxis_check, (y,2), flag=wx.ALIGN_CENTER_VERTICAL)
        y = y+1
        axis_grid.Add(tickLabels_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        axis_grid.Add(self.frame_tick_labels_xaxis_check, (y,1), flag=wx.ALIGN_CENTER_VERTICAL)
        axis_grid.Add(self.frame_tick_labels_yaxis_check, (y,2), flag=wx.ALIGN_CENTER_VERTICAL)
        y = y+1
        axis_grid.Add(ticks_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        axis_grid.Add(self.frame_ticks_xaxis_check, (y,1), flag=wx.ALIGN_CENTER_VERTICAL)
        axis_grid.Add(self.frame_ticks_yaxis_check, (y,2), flag=wx.ALIGN_CENTER_VERTICAL)
        y = y+1
        axis_grid.Add(borderLeft_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        axis_grid.Add(self.frame_border_min_left, (y,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        axis_grid.Add(borderRight_label, (y,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        axis_grid.Add(self.frame_border_min_right, (y,3), flag=wx.ALIGN_CENTER_VERTICAL)
        axis_grid.Add(borderTop_label, (y,4), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        axis_grid.Add(self.frame_border_min_top, (y,5), flag=wx.ALIGN_CENTER_VERTICAL)
        axis_grid.Add(borderBottom_label, (y,6), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        axis_grid.Add(self.frame_border_min_bottom, (y,7), flag=wx.ALIGN_CENTER_VERTICAL)
        y = y+1
        axis_grid.Add(outlineWidth_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        axis_grid.Add(self.frame_outline_width, (y,1), flag=wx.ALIGN_CENTER_VERTICAL)
        axis_grid.Add(outlineTransparency_label, (y,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        axis_grid.Add(self.frame_outline_alpha, (y,3), flag=wx.ALIGN_CENTER_VERTICAL)
        axis_grid.Add(frame_background_color, (y,4), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        axis_grid.Add(self.frame_background_colorBtn, (y,5), flag=wx.ALIGN_CENTER_VERTICAL)
        y = y+1
        axis_grid.Add(frame_gridline_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        axis_grid.Add(self.frame_gridline_check, (y,1), flag=wx.ALIGN_CENTER_VERTICAL)
        axis_grid.Add(self.frame_gridline_color, (y,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        frame_box_sizer.Add(axis_grid, 0, wx.EXPAND, 10)
        
        # pack elements
        grid = wx.GridBagSizer(2, 2)
        y = 0
        grid.Add(figureSize_box_sizer, (y,0), flag=wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL)
        y = y + 1
        grid.Add(fontSize_box_sizer, (y,0), flag=wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL)
        y = y + 1
        grid.Add(plotSize_box_sizer, (y,0), flag=wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL)
        y = y + 1
        grid.Add(frame_box_sizer, (y,0), flag=wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL)
         
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(grid, wx.ALIGN_CENTER_HORIZONTAL, 2)
        
        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)
        
        return panel
    
    def make1DPanel(self, panel):
        
        # pack elements
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        
        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)
        
        return panel
    
    def make2DPanel(self, panel):
        
        # pack elements
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        
        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)
        
        return panel
    
    def makeOverlayPanel(self, panel):
        
        # pack elements
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        
        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)
        
        return panel
    
    def makeWaterfallPanel(self, panel):
        
        # pack elements
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        
        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)
        
        return panel
    
    def makeLegendPanel(self, panel):
        
        legend_label = makeStaticText(panel, u"Legend:")
        self.legend_legend = wx.CheckBox(panel, -1 ,u'', (15, 30))
        self.legend_legend.SetValue(self.kwargs.get("legend_properties", {}).get("legend", self.config.interactive_legend))
        self.legend_legend.Bind(wx.EVT_CHECKBOX, self.onApply_legend)

        position_label = makeStaticText(panel, u"Position")
        self.legend_position = wx.ComboBox(panel, -1,
                                           choices=self.config.interactive_legend_location_choices,
                                           value=self.kwargs.get("legend_properties", {}).get("legend_location", self.config.interactive_legend_location), 
                                           style=wx.CB_READONLY)
        self.legend_position.Bind(wx.EVT_COMBOBOX, self.onApply_legend)

        orientation_label = makeStaticText(panel, u"Orientation")
        self.legend_orientation = wx.ComboBox(panel, -1,
                                              choices=self.config.interactive_legend_orientation_choices,
                                              value=self.kwargs.get("legend_properties", {}).get("legend_orientation", self.config.interactive_legend_orientation), 
                                              style=wx.CB_READONLY)
        self.legend_orientation.Bind(wx.EVT_COMBOBOX, self.onApply_legend)

        legendAlpha_label = makeStaticText(panel, u"Legend transparency")
        self.legend_transparency = wx.SpinCtrlDouble(panel, wx.ID_ANY,
                                                     value=str(self.kwargs.get("legend_properties", {}).get("legend_background_alpha", self.config.interactive_legend_background_alpha)),
                                                     min=0, max=1,
                                                     initial=self.kwargs.get("legend_properties", {}).get("legend_background_alpha", self.config.interactive_legend_background_alpha), 
                                                     inc=0.25, size=(50,-1))
        self.legend_transparency.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_legend)

        fontSize_label = makeStaticText(panel, u"Font size")
        self.legend_fontSize = wx.SpinCtrlDouble(panel, wx.ID_ANY,
                                                 value=str(self.kwargs.get("legend_properties", {}).get("legend_font_size", self.config.interactive_legend_font_size)), 
                                                 min=0, max=32,
                                                 initial=self.kwargs.get("legend_properties", {}).get("legend_font_size", self.config.interactive_legend_font_size), inc=2, size=(50,-1))
        self.legend_fontSize.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_legend)

        action_label = makeStaticText(panel, u"Action")
        self.legend_click_policy = wx.ComboBox(panel, -1,
                                               choices=self.config.interactive_legend_click_policy_choices,
                                               value=self.kwargs.get("legend_properties", {}).get("legend_click_policy", self.config.interactive_legend_click_policy), style=wx.CB_READONLY)
        self.legend_click_policy.Bind(wx.EVT_COMBOBOX, self.onApply_legend)
        self.legend_click_policy.Bind(wx.EVT_COMBOBOX, self.onEnableDisable_legend)

        muteAlpha_label = makeStaticText(panel, u"Line transparency")
        self.legend_mute_transparency = wx.SpinCtrlDouble(panel, wx.ID_ANY,
                                                   value=str(self.kwargs.get("legend_properties", {}).get("legend_mute_alpha", self.config.interactive_legend_mute_alpha)), 
                                                   min=0, max=1,
                                                   initial=self.kwargs.get("legend_properties", {}).get("legend_mute_alpha", self.config.interactive_legend_mute_alpha), inc=0.25, size=(50,-1))
        self.legend_mute_transparency.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_legend)


        grid = wx.GridBagSizer(2,2)
        n = 0
        grid.Add(legend_label, (n,0), flag=wx.ALIGN_LEFT)
        grid.Add(self.legend_legend, (n,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(position_label, (n,0), flag=wx.ALIGN_LEFT)
        grid.Add(self.legend_position, (n,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(orientation_label, (n,0), flag=wx.ALIGN_LEFT)
        grid.Add(self.legend_orientation, (n,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(fontSize_label, (n,0), flag=wx.ALIGN_LEFT)
        grid.Add(self.legend_fontSize, (n,1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(legendAlpha_label, (n,0), flag=wx.ALIGN_LEFT)
        grid.Add(self.legend_transparency, (n,1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(action_label, (n,0), flag=wx.ALIGN_LEFT)
        grid.Add(self.legend_click_policy, (n,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(muteAlpha_label, (n,0), flag=wx.ALIGN_LEFT)
        grid.Add(self.legend_mute_transparency, (n,1), flag=wx.ALIGN_CENTER_VERTICAL)

        # pack elements
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(grid, 0, wx.ALIGN_LEFT|wx.ALL, 2)
        
        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)
        
        return panel
    
    def makeColorbarPanel(self, panel):
        
        # pack elements
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        
        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)
        
        return panel
    
    def makeWidgetsPanel(self, panel):
        
        self.widgets_add_widgets = makeCheckbox(panel, u"Add custom JS widgets")
        self.widgets_add_widgets.Bind(wx.EVT_CHECKBOX, self.onEnableDisable_widgets)
        self.widgets_add_widgets.SetValue(self.kwargs.get("widgets", {}).get("add_custom_widgets", self.config.interactive_custom_scripts))
        
        # general
        general_staticBox = makeStaticBox(panel, "General widgets", size=(-1, -1), color=wx.BLACK)
        general_staticBox.SetSize((-1,-1))
        general_box_sizer = wx.StaticBoxSizer(general_staticBox, wx.HORIZONTAL)
    
        self.widgets_general_zoom_1D = makeCheckbox(panel, u"Y-axis scale slider")
        self.widgets_general_zoom_1D.Bind(wx.EVT_CHECKBOX, self.onApply_widgets)
        self.widgets_general_zoom_1D.SetValue(self.kwargs.get("widgets", {}).get("slider_zoom", True))
        
        self.widgets_general_hover_mode = makeCheckbox(panel, u"Hover mode toggle")
        self.widgets_general_hover_mode.Bind(wx.EVT_CHECKBOX, self.onApply_widgets)
        self.widgets_general_hover_mode.SetValue(self.kwargs.get("widgets", {}).get("hover_mode", True))
        
        general_grid = wx.GridBagSizer(2, 2)
        y = 0
        general_grid.Add(self.widgets_general_zoom_1D, (y,0), wx.GBSpan(1,2), flag=wx.EXPAND)
        y = y+1
        general_grid.Add(self.widgets_general_hover_mode, (y,0), wx.GBSpan(1,2), flag=wx.EXPAND)
        general_box_sizer.Add(general_grid, 0, wx.EXPAND, 10)
        
        # color
        color_staticBox = makeStaticBox(panel, "General widgets", size=(-1, -1), color=wx.BLACK)
        color_staticBox.SetSize((-1,-1))
        color_box_sizer = wx.StaticBoxSizer(color_staticBox, wx.HORIZONTAL)
        
        self.widgets_color_colorblind = makeCheckbox(panel, u"Colorblind toggle")
        self.widgets_color_colorblind.Bind(wx.EVT_CHECKBOX, self.onApply_widgets)
        self.widgets_color_colorblind.SetValue(self.kwargs.get("widgets", {}).get("colorblind_safe_1D", True))
        
        self.widgets_color_colormap = makeCheckbox(panel, u"Colormap dropdown")
        self.widgets_color_colormap.Bind(wx.EVT_CHECKBOX, self.onApply_widgets)
        self.widgets_color_colormap.SetValue(self.kwargs.get("widgets", {}).get("colormap_change", True))
        
        color_grid = wx.GridBagSizer(2, 2)
        y = 0
        color_grid.Add(self.widgets_color_colorblind, (y,0), wx.GBSpan(1,2), flag=wx.EXPAND)
        y = y+1
        color_grid.Add(self.widgets_color_colormap, (y,0), wx.GBSpan(1,2), flag=wx.EXPAND)
        color_box_sizer.Add(color_grid, 0, wx.EXPAND, 10)
        
        # scatter
        scatter_staticBox = makeStaticBox(panel, "Scatter widgets", size=(-1, -1), color=wx.BLACK)
        scatter_staticBox.SetSize((-1,-1))
        scatter_box_sizer = wx.StaticBoxSizer(scatter_staticBox, wx.HORIZONTAL)
        
        self.widgets_scatter_size = makeCheckbox(panel, u"Size slider")
        self.widgets_scatter_size.Bind(wx.EVT_CHECKBOX, self.onApply_widgets)
        self.widgets_scatter_size.SetValue(self.kwargs.get("widgets", {}).get("scatter_size", True))

        self.widgets_scatter_transparency = makeCheckbox(panel, u"Transparency slider")
        self.widgets_scatter_transparency.Bind(wx.EVT_CHECKBOX, self.onApply_widgets)
        self.widgets_scatter_transparency.SetValue(self.kwargs.get("widgets", {}).get("scatter_transparency", True))
        
        scatter_grid = wx.GridBagSizer(2, 2)
        y = 0
        scatter_grid.Add(self.widgets_scatter_size, (y,0), wx.GBSpan(1,2), flag=wx.EXPAND)
        y = y+1
        scatter_grid.Add(self.widgets_scatter_transparency, (y,0), wx.GBSpan(1,2), flag=wx.EXPAND)
        scatter_box_sizer.Add(scatter_grid, 0, wx.EXPAND, 10)
        
        # legend
        legend_staticBox = makeStaticBox(panel, "Legend widgets", size=(-1, -1), color=wx.BLACK)
        legend_staticBox.SetSize((-1,-1))
        legend_box_sizer = wx.StaticBoxSizer(legend_staticBox, wx.HORIZONTAL)
        
        self.widgets_legend_show = makeCheckbox(panel, u"Show/hide toggle")
        self.widgets_legend_show.Bind(wx.EVT_CHECKBOX, self.onApply_widgets)
        self.widgets_legend_show.SetValue(self.kwargs.get("widgets", {}).get("legend_toggle", True))

        self.widgets_legend_transparency = makeCheckbox(panel, u"Font size slider")
        self.widgets_legend_transparency.Bind(wx.EVT_CHECKBOX, self.onApply_widgets)
        self.widgets_legend_transparency.SetValue(self.kwargs.get("widgets", {}).get("legend_transparency", True))
        
        self.widgets_legend_orientation = makeCheckbox(panel, u"Orientation radiobox")
        self.widgets_legend_orientation.Bind(wx.EVT_CHECKBOX, self.onApply_widgets)
        self.widgets_legend_orientation.SetValue(self.kwargs.get("widgets", {}).get("legend_orientation", True))
        
        self.widgets_legend_position = makeCheckbox(panel, u"Position dropdown")
        self.widgets_legend_position.Bind(wx.EVT_CHECKBOX, self.onApply_widgets)
        self.widgets_legend_position.SetValue(self.kwargs.get("widgets", {}).get("legend_position", True))

        legend_grid = wx.GridBagSizer(2, 2)
        y = 0
        legend_grid.Add(self.widgets_legend_show, (y,0), wx.GBSpan(1,2), flag=wx.EXPAND)
        y = y+1
        legend_grid.Add(self.widgets_legend_transparency, (y,0), wx.GBSpan(1,2), flag=wx.EXPAND)
        y = y+1
        legend_grid.Add(self.widgets_legend_orientation, (y,0), wx.GBSpan(1,2), flag=wx.EXPAND)
        y = y+1
        legend_grid.Add(self.widgets_legend_position, (y,0), wx.GBSpan(1,2), flag=wx.EXPAND)
        legend_box_sizer.Add(legend_grid, 0, wx.EXPAND, 10)
        
        # labels
        labels_staticBox = makeStaticBox(panel, "Label and annotation widgets", size=(-1, -1), color=wx.BLACK)
        labels_staticBox.SetSize((-1,-1))
        labels_box_sizer = wx.StaticBoxSizer(labels_staticBox, wx.HORIZONTAL)
        
        self.widgets_labels_show = makeCheckbox(panel, u"Show/hide toggle")
        self.widgets_labels_show.Bind(wx.EVT_CHECKBOX, self.onApply_widgets)
        self.widgets_labels_show.SetValue(self.kwargs.get("widgets", {}).get("label_toggle", True))

        self.widgets_labels_font_size = makeCheckbox(panel, u"Font size slider")
        self.widgets_labels_font_size.Bind(wx.EVT_CHECKBOX, self.onApply_widgets)
        self.widgets_labels_font_size.SetValue(self.kwargs.get("widgets", {}).get("label_size_slider", True))
        
        self.widgets_labels_rotate = makeCheckbox(panel, u"Rotation slider")
        self.widgets_labels_rotate.Bind(wx.EVT_CHECKBOX, self.onApply_widgets)
        self.widgets_labels_rotate.SetValue(self.kwargs.get("widgets", {}).get("label_rotation", True))
        
        self.widgets_labels_offset_x = makeCheckbox(panel, u"Offset x slider")
        self.widgets_labels_offset_x.Bind(wx.EVT_CHECKBOX, self.onApply_widgets)
        self.widgets_labels_offset_x.SetValue(self.kwargs.get("widgets", {}).get("label_offset_x", True))
        
        self.widgets_labels_offset_y = makeCheckbox(panel, u"Offset y slider")
        self.widgets_labels_offset_y.Bind(wx.EVT_CHECKBOX, self.onApply_widgets)
        self.widgets_labels_offset_y.SetValue(self.kwargs.get("widgets", {}).get("label_offset_y", True))

        labels_grid = wx.GridBagSizer(2, 2)
        y = 0
        labels_grid.Add(self.widgets_labels_show, (y,0), wx.GBSpan(1,2), flag=wx.EXPAND)
        y = y+1
        labels_grid.Add(self.widgets_labels_font_size, (y,0), wx.GBSpan(1,2), flag=wx.EXPAND)
        y = y+1
        labels_grid.Add(self.widgets_labels_rotate, (y,0), wx.GBSpan(1,2), flag=wx.EXPAND)
        y = y+1
        labels_grid.Add(self.widgets_labels_offset_x, (y,0), wx.GBSpan(1,2), flag=wx.EXPAND)
        y = y+1
        labels_grid.Add(self.widgets_labels_offset_y, (y,0), wx.GBSpan(1,2), flag=wx.EXPAND)
        labels_box_sizer.Add(labels_grid, 0, wx.EXPAND, 10)
        
        # processing
        processing_staticBox = makeStaticBox(panel, "Data processing widgets", size=(-1, -1), color=wx.BLACK)
        processing_staticBox.SetSize((-1,-1))
        processing_box_sizer = wx.StaticBoxSizer(processing_staticBox, wx.HORIZONTAL)
        
        self.widgets_processing_normalization = makeCheckbox(panel, u"Normalization modes dropdown")
        self.widgets_processing_normalization.Bind(wx.EVT_CHECKBOX, self.onApply_widgets)
        self.widgets_processing_normalization.SetValue(self.kwargs.get("widgets", {}).get("processing_normalization", True))

#         self.widgets_labels_font_size = makeCheckbox(panel, u"Font size slider")
#         self.widgets_labels_font_size.Bind(wx.EVT_CHECKBOX, self.onApply_widgets)
#         self.widgets_labels_font_size.SetValue(self.kwargs.get("widgets", {}).get("label_size_slider", False))
#         
#         self.widgets_labels_rotate = makeCheckbox(panel, u"Rotation slider")
#         self.widgets_labels_rotate.Bind(wx.EVT_CHECKBOX, self.onApply_widgets)
#         self.widgets_labels_rotate.SetValue(self.kwargs.get("widgets", {}).get("label_rotation", False))
#         
#         self.widgets_labels_offset_x = makeCheckbox(panel, u"Offset x slider")
#         self.widgets_labels_offset_x.Bind(wx.EVT_CHECKBOX, self.onApply_widgets)
#         self.widgets_labels_offset_x.SetValue(self.kwargs.get("widgets", {}).get("label_offset_x", False))
#         
#         self.widgets_labels_offset_y = makeCheckbox(panel, u"Offset y slider")
#         self.widgets_labels_offset_y.Bind(wx.EVT_CHECKBOX, self.onApply_widgets)
#         self.widgets_labels_offset_y.SetValue(self.kwargs.get("widgets", {}).get("label_offset_y", False))

        processing_grid = wx.GridBagSizer(2, 2)
        y = 0
        processing_grid.Add(self.widgets_processing_normalization, (y,0), wx.GBSpan(1,2), flag=wx.EXPAND)
#         y = y+1
#         processing_grid.Add(self.widgets_labels_font_size, (y,0), wx.GBSpan(1,2), flag=wx.EXPAND)
#         y = y+1
#         processing_grid.Add(self.widgets_labels_rotate, (y,0), wx.GBSpan(1,2), flag=wx.EXPAND)
#         y = y+1
#         processing_grid.Add(self.widgets_labels_offset_x, (y,0), wx.GBSpan(1,2), flag=wx.EXPAND)
#         y = y+1
#         processing_grid.Add(self.widgets_labels_offset_y, (y,0), wx.GBSpan(1,2), flag=wx.EXPAND)
        processing_box_sizer.Add(processing_grid, 0, wx.EXPAND, 10)
        
        grid_1 = wx.GridBagSizer(2, 2) 
        y = 0
        grid_1.Add(self.widgets_add_widgets, (y,0), wx.GBSpan(1,1), flag=wx.EXPAND|wx.ALIGN_LEFT)
        y = y+1
        grid_1.Add(general_box_sizer, (y,0), wx.GBSpan(1,1), flag=wx.EXPAND|wx.ALIGN_LEFT)
        y = y+1
        grid_1.Add(color_box_sizer, (y,0), wx.GBSpan(1,1), flag=wx.EXPAND|wx.ALIGN_LEFT)
        y = y+1
        grid_1.Add(scatter_box_sizer, (y,0), wx.GBSpan(1,1), flag=wx.EXPAND|wx.ALIGN_LEFT)
        y = y+1
        grid_1.Add(legend_box_sizer, (y,0), wx.GBSpan(1,1), flag=wx.EXPAND|wx.ALIGN_LEFT)
        y = y+1
        grid_1.Add(labels_box_sizer, (y,0), wx.GBSpan(1,1), flag=wx.EXPAND|wx.ALIGN_LEFT)
        y = y+1
        grid_1.Add(processing_box_sizer, (y,0), wx.GBSpan(1,1), flag=wx.EXPAND|wx.ALIGN_LEFT)
        
        # pack elements
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(grid_1, 0, wx.ALIGN_LEFT|wx.ALL, 2)
        
        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)
        
        return panel
    
    def onApply_widgets(self, evt):
        if self._loading_: return
        
        self.kwargs['widgets']['add_custom_widgets'] = self.widgets_add_widgets.GetValue()    
        
        self.kwargs['widgets']['label_toggle'] = self.widgets_labels_show.GetValue()
        self.kwargs['widgets']['label_size_slider'] = self.widgets_labels_font_size.GetValue()
        self.kwargs['widgets']['label_rotation'] = self.widgets_labels_rotate.GetValue()
        self.kwargs['widgets']['label_offset_x'] = self.widgets_labels_offset_x.GetValue()
        self.kwargs['widgets']['label_offset_y'] = self.widgets_labels_offset_y.GetValue()
        
        self.kwargs['widgets']['slider_zoom'] = self.widgets_general_zoom_1D.GetValue()
        self.kwargs['widgets']['hover_mode'] = self.widgets_general_hover_mode.GetValue()
        self.kwargs['widgets']['colorblind_safe_1D'] = self.widgets_color_colorblind.GetValue()
        self.kwargs['widgets']['colorblind_safe_2D'] = self.widgets_color_colorblind.GetValue()
        self.kwargs['widgets']['colorblind_safe_scatter'] = self.widgets_color_colorblind.GetValue()
        
        self.kwargs['widgets']['legend_toggle'] = self.widgets_legend_show.GetValue()
        self.kwargs['widgets']['legend_position'] = self.widgets_legend_position.GetValue()
        self.kwargs['widgets']['legend_orientation'] = self.widgets_legend_orientation.GetValue()
        self.kwargs['widgets']['legend_transparency'] = self.widgets_legend_transparency.GetValue()
        
        self.kwargs['widgets']['scatter_size'] = self.widgets_scatter_size.GetValue()
        self.kwargs['widgets']['scatter_transparency'] = self.widgets_scatter_transparency.GetValue()
        self.kwargs['widgets']['processing_normalization'] = self.widgets_processing_normalization.GetValue()
        
        self.onUpdateDocument()
        
    def onApply_legend(self, evt):
        if self._loading_: return
        
        self.kwargs['legend_properties']['legend'] = self.legend_legend.GetValue()
        self.kwargs['legend_properties']['legend_location'] = self.legend_position.GetStringSelection()
        self.kwargs['legend_properties']['legend_click_policy'] = self.legend_click_policy.GetStringSelection()
        self.kwargs['legend_properties']['legend_orientation'] = self.legend_orientation.GetStringSelection()
        self.kwargs['legend_properties']['legend_font_size'] = self.legend_fontSize.GetValue()
        self.kwargs['legend_properties']['legend_background_alpha'] = self.legend_transparency.GetValue()
        self.kwargs['legend_properties']['legend_mute_alpha'] = self.legend_mute_transparency.GetValue()
        
        self.onUpdateDocument()
    
    def onApply_general(self, evt):
        if self._loading_: return
        
        # figure parameters
        self.kwargs['plot_height'] = int(self.figure_height_value.GetValue())
        self.kwargs['plot_width'] = int(self.figure_width_value.GetValue())
        
        
        # plot parameters
        xlimits = [str2num(self.plot_xmin_value.GetValue()), str2num(self.plot_xmax_value.GetValue())]
        self.kwargs['xlimits'] = xlimits
        ylimits = [str2num(self.plot_ymin_value.GetValue()), str2num(self.plot_ymax_value.GetValue())]
        self.kwargs['ylimits'] = ylimits
               
               
        # frame parameters
        self.kwargs['frame_properties']['label_fontsize'] = self.frame_label_fontsize.GetValue() 
        self.kwargs['frame_properties']['label_fontweight'] = self.frame_label_weight.GetValue()
        self.kwargs['frame_properties']['tick_fontsize'] = self.frame_ticks_fontsize.GetValue()
        
        self.kwargs['frame_properties']['label_xaxis'] = self.frame_label_xaxis_check.GetValue()
        if self.kwargs['frame_properties']['label_xaxis']: 
            self.kwargs['frame_properties']['label_xaxis_fontsize'] = self.kwargs['frame_properties']['label_fontsize']
        else: 
            self.kwargs['frame_properties']['label_xaxis_fontsize'] = 0
            
        self.kwargs['frame_properties']['label_yaxis'] = self.frame_label_yaxis_check.GetValue()
        if self.kwargs['frame_properties']['label_yaxis']: 
            self.kwargs['frame_properties']['label_yaxis_fontsize'] = self.kwargs['frame_properties']['label_fontsize']
        else: 
            self.kwargs['frame_properties']['label_yaxis_fontsize'] = 0
        
        self.kwargs['frame_properties']['ticks_xaxis'] = self.kwargs['frame_properties']['tick_fontsize']
        if self.kwargs['frame_properties']['ticks_xaxis']:
            self.kwargs['frame_properties']['ticks_xaxis_color'] = "#000000"
        else: 
            self.kwargs['frame_properties']['ticks_xaxis_color'] = None
            
        self.kwargs['frame_properties']['ticks_yaxis'] = self.frame_ticks_yaxis_check.GetValue()
        if self.kwargs['frame_properties']['ticks_yaxis']: 
        self.kwargs['frame_properties']['tick_labels_xaxis'] = self.frame_tick_labels_xaxis_check.GetValue()
        
        self.kwargs['frame_properties']['tick_labels_yaxis'] = self.frame_tick_labels_yaxis_check.GetValue()
        if self.kwargs['frame_properties']['tick_labels_yaxis']: 
            self.kwargs['frame_properties']['tick_labels_yaxis_fontsize'] = self.kwargs['frame_properties']['tick_fontsize']
        else: 
            self.kwargs['frame_properties']['tick_labels_yaxis_fontsize'] = 0
            
        # border parameters
        self.kwargs['frame_properties']['border_left'] = int(self.frame_border_min_left.GetValue())
        self.kwargs['frame_properties']['border_right'] = int(self.frame_border_min_right.GetValue())
        self.kwargs['frame_properties']['border_top'] = int(self.frame_border_min_top.GetValue())
        self.kwargs['frame_properties']['border_bottom'] = int(self.frame_border_min_bottom.GetValue())
        
        self.kwargs['frame_properties']['outline_width'] = self.frame_outline_width.GetValue()
        self.kwargs['frame_properties']['outline_transparency'] = self.frame_outline_alpha.GetValue()
        
        self.kwargs['frame_properties']['gridline'] = self.frame_gridline_check.GetValue()
            
        self.onUpdateDocument()
        
    def onApply_color(self, evt):
        source = evt.GetEventObject().GetName()
         
        # Restore custom colors
        custom = wx.ColourData()
        for key in range(len(self.config.customColors)):
            custom.SetCustomColour(key, self.config.customColors[key])
        dlg = wx.ColourDialog(self, custom)
        dlg.GetColourData().SetChooseFull(True)
         
        # Show dialog and get new colour
        if dlg.ShowModal() == wx.ID_OK:
            data = dlg.GetColourData()
            newColour = list(data.GetColour().Get())
            dlg.Destroy()
            # Retrieve custom colors
            for i in xrange(15): 
                self.config.customColors[i] = data.GetCustomColour(i)
                
                
            if source == "gridline_color":
                self.frame_gridline_color.SetBackgroundColour(newColour)
                self.kwargs['frame_properties']['gridline_color'] = convertRGB255to1(newColour)
            elif source == "background_color":
                self.frame_background_colorBtn.SetBackgroundColour(newColour)
                self.kwargs['frame_properties']['background_color'] = convertRGB255to1(newColour)
                
            self.onUpdateDocument()
        else: 
            return
            
    def _check_allowed_settings(self):
        """
        Check which settings can be displayed for selected item
        """
        # widgets
        pass
    
    def onUpdateDocument(self):
        self.parent.onUpdateItemParameters(self.document_title, 
                                           self.item_type,
                                           self.item_title, 
                                           self.kwargs)
        
    def onEnableDisable_widgets(self, evt):
        itemList = [self.widgets_labels_show, self.widgets_labels_font_size, 
                    self.widgets_labels_rotate, self.widgets_labels_offset_x,
                    self.widgets_labels_offset_y, self.widgets_general_zoom_1D, 
                    self.widgets_general_hover_mode, self.widgets_color_colorblind,
                    self.widgets_color_colormap, self.widgets_legend_show,
                    self.widgets_legend_orientation, self.widgets_legend_position, 
                    self.widgets_legend_transparency, self.widgets_labels_show,
                    self.widgets_scatter_size, self.widgets_scatter_transparency, 
                    self.widgets_processing_normalization]
        
        if self.widgets_add_widgets.GetValue():
            for item in itemList: item.Enable()
        else:
            for item in itemList: item.Disable()
            
        self.onApply_widgets(None)
        
    def onEnableDisable_legend(self, evt):
        pass
                  
        
        
        
        
        
        
        
        
        
        
                
            
        