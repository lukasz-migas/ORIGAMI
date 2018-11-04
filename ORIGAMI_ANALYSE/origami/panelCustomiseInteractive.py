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
                    makeStaticBox, makeStaticText)
from help import OrigamiHelp as help


class panelCustomiseInteractive(wx.MiniFrame):
    """
    Panel where you can customise interactive plots
    """
    
    def __init__(self, presenter, parent, config, icons, **kwargs):
        wx.MiniFrame.__init__(self, parent, -1, 
                        'Customise interactive plot...', size=(-1, -1),
                        style=wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER
                          )
        
#         tstart = time.time()
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
        
        print("Customising: {} - {} - {}".format(self.document_title,
                                                 self.item_type,
                                                 self.item_title))
        
#         print("Startup took {:.3f} seconds".format(time.time()-tstart))
        
    def OnKey(self, evt):
        """Respond to key press"""
#         keyCode = evt.GetKeyCode()
        evt.Skip()
        
    def onClose(self, evt):
        """Destroy this frame."""
        self.Destroy()
        
    def _checkInteractiveParameters(self):
        
        if "widgets" not in self.kwargs:
            self.kwargs['widgets'] = {}
            
        if "legend_properties" not in self.kwargs:
            self.kwargs['legend_properties'] = {}
            
        self.parent.onUpdateItemParameters(self.document_title, self.item_type,
                                           self.item_title, self.kwargs)
            
    def makeGUI(self):
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        # Setup notebook
        self.mainBook = wx.Notebook(self, wx.ID_ANY, wx.DefaultPosition,
                                    wx.DefaultSize, 0)
#         # About
#         self.settings_about = wx.Panel(self.mainBook, wx.ID_ANY, wx.DefaultPosition,
#                                           wx.DefaultSize, wx.TAB_TRAVERSAL|wx.NB_MULTILINE)
#         self.mainBook.AddPage(self.makeAboutPanel(self.settings_about), u"About", False)
#         # Frame
#         self.settings_general = wx.Panel(self.mainBook, wx.ID_ANY, wx.DefaultPosition,
#                                           wx.DefaultSize, wx.TAB_TRAVERSAL|wx.NB_MULTILINE)
#         self.mainBook.AddPage(self.makeGeneralPanel(self.settings_general), u"General", False)
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
        
        # pack elements
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        
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
        
        self.onUpdateDocument()
        
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
        
    def onApply_legend(self, evt):
        
        self.kwargs['legend_properties']['legend'] = self.legend_legend.GetValue()
        self.kwargs['legend_properties']['legend_location'] = self.legend_position.GetStringSelection()
        self.kwargs['legend_properties']['legend_click_policy'] = self.legend_click_policy.GetStringSelection()
        self.kwargs['legend_properties']['legend_orientation'] = self.legend_orientation.GetStringSelection()
        self.kwargs['legend_properties']['legend_font_size'] = self.legend_fontSize.GetValue()
        self.kwargs['legend_properties']['legend_background_alpha'] = self.legend_transparency.GetValue()
        self.kwargs['legend_properties']['legend_mute_alpha'] = self.legend_mute_transparency.GetValue()
        
        self.onUpdateDocument()
    
    def onEnableDisable_legend(self, evt):
        pass
            
    def _check_allowed_settings(self):
        """
        Check which settings can be displayed for selected item
        """
        # widgets
        pass
    
    def onUpdateDocument(self):
        self.parent.onUpdateItemParameters(self.document_title, self.item_type,
                                           self.item_title, self.kwargs)
        
        
        
        
        
        
        
        
        
        
        
        
                
            
        