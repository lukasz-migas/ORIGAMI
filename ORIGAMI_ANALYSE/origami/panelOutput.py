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

# TODO: add support for holoviews
# EXAMPLE
# import holoviews as hv
# hv.extension('bokeh')
# renderer = hv.renderer('bokeh')
# np.random.seed(37)
# violin = hv.Violin(np.random.randn(100), vdims='Value')
# plot = renderer.get_plot(violin).state # need to grab the figure instance

# load libs
from __future__ import division, unicode_literals
import wx, re, webbrowser, time, threading
import wx.lib.mixins.listctrl as listmix
import wx.lib.scrolledpanel
import numpy as np
from operator import itemgetter
from seaborn import color_palette
from natsort import natsorted
from copy import deepcopy
from math import sqrt
import matplotlib.colors as colors
import matplotlib.cm as cm

# bokeh imports
from bokeh.plotting import figure, save, ColumnDataSource
from bokeh.models import (HoverTool, LinearColorMapper, Label, ColorBar,
                          AdaptiveTicker, BasicTickFormatter,
                          FixedTicker, FuncTickFormatter, LabelSet,
                          CustomJS, Toggle, Slider, Legend, Dropdown, Select,
                          Select, Arrow, NormalHead, TapTool, OpenURL)
from bokeh.layouts import (column, widgetbox, gridplot, row)
from bokeh.layouts import layout as bokeh_layout
from bokeh.models.widgets import Panel, Tabs, Div, RadioButtonGroup
from bokeh import events
from bokeh.resources import INLINE
from bokeh.models.tickers import FixedTicker
from bokeh.embed import components

from ids import *
from panelCustomiseInteractive import panelCustomiseInteractive
from toolbox import (str2int, str2num, convertRGB1to255, convertRGB1toHEX, find_nearest,
                             find_limits_list, _replace_labels, remove_nan_from_list,
                             num2str, find_limits_all, merge_two_dicts, determineFontColor,
    convertHEXtoRGB255)
from styles import makeStaticBox, makeStaticText, makeCheckbox, TEXT_STYLE_CV_R_L, makeMenuItem, validator
import dialogs as dialogs
from processing.spectra import linearize_data, crop_1D_data, normalize_1D

# TODO: replace Dropdown with Select tool

# import cmaputil as cmu
# import cmaputil.cvdutil as cvu
# import holoviews as hv
# hv.extension('bokeh')

import warnings
# needed to avoid annoying warnings to be printed on console
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UnicodeWarning)

class dlgOutputInteractive(wx.MiniFrame):
    """Save data in an interactive format"""

    def __init__(self, parent, icons, presenter, config):
        wx.MiniFrame.__init__(self, parent, -1, "Export plots in interactive format...",
                              style=(wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER |
                                      wx.RESIZE_BOX | wx.MAXIMIZE_BOX))

        tstart = time.time()
        self.displaysize = wx.GetDisplaySize()
        self.view = parent
        self.icons = icons
        self.presenter = presenter
        self.config = config
        self.documentsDict = self.presenter.documentsDict
        self.docsText = self.presenter.docsText
        self.currentPath = self.presenter.currentPath
        self.currentDocumentName = 'ORIGAMI'

        try:
            _main_position = self.view.GetPosition()
            position_diff = []
            for idx in range(wx.Display.GetCount()):
                d = wx.Display(idx)
                position_diff.append(_main_position[0] - d.GetGeometry()[0])

            self.currentDisplaySize = wx.Display(position_diff.index(np.min(position_diff))).GetGeometry()
            self.currentDisplayMain = wx.Display(position_diff.index(np.min(position_diff))).IsPrimary()
        except:
            self.currentDisplaySize = None

        self.currentItem = None
        self.loading = False
        self.listOfPlots = []

        # Set up tools
        self.tools = ""
        self.activeDrag = None
        self.activeWheel = None
        self.activeInspect = None

        self.tools_all = "save, pan, box_zoom, xbox_zoom, ybox_zoom, reset"

        self.allChecked = True
        self.reverse = False
        self.lastColumn = None
        self.filtered = False
        self.listOfSelected = []
        self._item_style_ = {}

        self.makeGUI()
        self.populateTable()
        self.onApply(evt=None)
        self.onEnableDisableItems(evt=None)

        # fit layout
        self.mainSizer.Fit(self.split_panel)
        self.SetSizer(self.mainSizer)
        self.CenterOnParent()
        self.Layout()
        self.SetFocus()

        print("Startup of interactive panel took {:.3f} seconds".format(time.time() - tstart))
        # bind
        wx.EVT_CLOSE(self, self.onClose)
        wx.EVT_SPLITTER_DCLICK(self, wx.ID_ANY, self._onSash)
        self.Bind(wx.EVT_CHAR_HOOK, self.OnKey)
        self.itemsList.Bind(wx.EVT_LEFT_DCLICK, self.onCustomiseItem)
        self.itemsList.Bind(wx.EVT_LIST_COL_RIGHT_CLICK, self.onColumnRightClickMenu)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnRightClickMenu)

    def OnRightClickMenu(self, evt):

        self.Bind(wx.EVT_MENU, self.onCustomiseItem, id=ID_interactivePanel_customise_item)

        self.Bind(wx.EVT_MENU, self.on_copy_style, id=ID_interactivePanel_copy_all)
        self.Bind(wx.EVT_MENU, self.on_copy_style, id=ID_interactivePanel_copy_frame)
        self.Bind(wx.EVT_MENU, self.on_copy_style, id=ID_interactivePanel_copy_legend)
        self.Bind(wx.EVT_MENU, self.on_copy_style, id=ID_interactivePanel_copy_widgets)
        self.Bind(wx.EVT_MENU, self.on_copy_style, id=ID_interactivePanel_copy_plot)
        self.Bind(wx.EVT_MENU, self.on_copy_style, id=ID_interactivePanel_copy_figure)
        self.Bind(wx.EVT_MENU, self.on_copy_style, id=ID_interactivePanel_copy_annotations)
        self.Bind(wx.EVT_MENU, self.on_copy_style, id=ID_interactivePanel_copy_colorbar)
        self.Bind(wx.EVT_MENU, self.on_copy_style, id=ID_interactivePanel_copy_tools)
        self.Bind(wx.EVT_MENU, self.on_copy_style, id=ID_interactivePanel_copy_overlay)
        self.Bind(wx.EVT_MENU, self.on_copy_style, id=ID_interactivePanel_copy_plots)
        self.Bind(wx.EVT_MENU, self.on_copy_style, id=ID_interactivePanel_copy_preprocess)

        self.Bind(wx.EVT_MENU, self.on_apply_style, id=ID_interactivePanel_apply_all)
        self.Bind(wx.EVT_MENU, self.on_apply_style, id=ID_interactivePanel_apply_frame)
        self.Bind(wx.EVT_MENU, self.on_apply_style, id=ID_interactivePanel_apply_legend)
        self.Bind(wx.EVT_MENU, self.on_apply_style, id=ID_interactivePanel_apply_widgets)
        self.Bind(wx.EVT_MENU, self.on_apply_style, id=ID_interactivePanel_apply_plot)
        self.Bind(wx.EVT_MENU, self.on_apply_style, id=ID_interactivePanel_apply_figure)
        self.Bind(wx.EVT_MENU, self.on_apply_style, id=ID_interactivePanel_apply_annotations)
        self.Bind(wx.EVT_MENU, self.on_apply_style, id=ID_interactivePanel_apply_colorbar)
        self.Bind(wx.EVT_MENU, self.on_apply_style, id=ID_interactivePanel_apply_tools)
        self.Bind(wx.EVT_MENU, self.on_apply_style, id=ID_interactivePanel_apply_overlay)
        self.Bind(wx.EVT_MENU, self.on_apply_style, id=ID_interactivePanel_apply_plots)
        self.Bind(wx.EVT_MENU, self.on_apply_style, id=ID_interactivePanel_apply_preprocess)


        copy_style_menu = wx.Menu()
        copy_style_menu.Append(ID_interactivePanel_copy_plot, 'Copy: X/Y limits')
        copy_style_menu.Append(ID_interactivePanel_copy_figure, 'Copy: Figure parameters (figure size)')
        copy_style_menu.Append(ID_interactivePanel_copy_frame, 'Copy: Axes parameters (ticks, labels, fontsize...)')
        copy_style_menu.Append(ID_interactivePanel_copy_preprocess, 'Copy: Pre-processing parameters')
        copy_style_menu.Append(ID_interactivePanel_copy_annotations, 'Copy: Annotation parameters')
        copy_style_menu.Append(ID_interactivePanel_copy_plots, 'Copy: Plot parameters')
        copy_style_menu.Append(ID_interactivePanel_copy_colorbar, 'Copy: Colorbar parameters')
        copy_style_menu.Append(ID_interactivePanel_copy_legend, 'Copy: Legend parameters')
        copy_style_menu.Append(ID_interactivePanel_copy_overlay, 'Copy: Overlay parameters')
        copy_style_menu.Append(ID_interactivePanel_copy_tools, 'Copy: Tools parameters')
        copy_style_menu.Append(ID_interactivePanel_copy_widgets, 'Copy: Widget parameters')

        apply_style_menu = wx.Menu()
        apply_style_menu.Append(ID_interactivePanel_apply_plot, 'Paste: X/Y limits')
        apply_style_menu.Append(ID_interactivePanel_apply_figure, 'Paste: Figure parameters (figure size)')
        apply_style_menu.Append(ID_interactivePanel_apply_frame, 'Paste: Axes parameters (ticks, labels, fontsize...)')
        apply_style_menu.Append(ID_interactivePanel_apply_preprocess, 'Paste: Pre-processing parameters')
        apply_style_menu.Append(ID_interactivePanel_apply_annotations, 'Paste: Annotation parameters')
        apply_style_menu.Append(ID_interactivePanel_apply_plots, 'Paste: Plot parameters')
        apply_style_menu.Append(ID_interactivePanel_apply_colorbar, 'Paste: Colorbar parameters')
        apply_style_menu.Append(ID_interactivePanel_apply_legend, 'Paste: Legend parameters')
        apply_style_menu.Append(ID_interactivePanel_apply_overlay, 'Paste: Overlay parameters')
        apply_style_menu.Append(ID_interactivePanel_apply_tools, 'Paste: Tools parameters')
        apply_style_menu.Append(ID_interactivePanel_apply_widgets, 'Paste: Widget parameters')



        menu = wx.Menu()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_interactivePanel_customise_item,
                                     text='Customise plot...',
                                     bitmap=self.icons.iconsLib['change_xlabels_16']))
        menu.AppendSeparator()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_interactivePanel_copy_all,
                                     text='Copy style (all)',
                                     bitmap=None))
        menu.AppendMenu(wx.ID_ANY, 'Copy style...', copy_style_menu)
        menu.AppendSeparator()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_interactivePanel_apply_all,
                                     text='Paste style (all)',
                                     bitmap=None))
        menu.AppendMenu(wx.ID_ANY, u'Paste style...', apply_style_menu)
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def on_copy_style(self, evt):
        # clear previous style
        self._item_style_ = dict()

        # retrieve item information
        name, key, innerKey = self._getItemDetails()
        data = self.getItemData(name, key, innerKey)
        style_data = deepcopy(data.get("interactive_params", {}))

        self._item_style_.update(document_title=name, item_type=key, item_title=innerKey)

        evtID = evt.GetId()
        # get styles
        if evtID == ID_interactivePanel_copy_all:
            frame_properties = style_data.get("frame_properties", {})
            legend_properties = style_data.get("legend_properties", {})
            tools = style_data.get("tools", {})
            colorbar_properties = style_data.get("colorbar_properties", {})
            overlay_properties = style_data.get("overlay_properties", {})
            annotation_properties = style_data.get("annotation_properties", {})
            preprocessing_properties = style_data.get("preprocessing_properties", {})
            plot_properties = style_data.get("plot_properties", {})
            widgets = style_data.get("widgets", {})
            plot_height = style_data.get("plot_height", self.config.figHeight)
            plot_width = style_data.get("plot_width", self.config.figWidth)
            xlimits = style_data.get("xlimits", [])
            ylimits = style_data.get("ylimits", [])
            self._item_style_.update(frame_properties=frame_properties,
                                     legend_properties=legend_properties,
                                     tools=tools,
                                     colorbar_properties=colorbar_properties,
                                     overlay_properties=overlay_properties,
                                     annotation_properties=annotation_properties,
                                     preprocessing_properties=preprocessing_properties,
                                     plot_properties=plot_properties,
                                     widgets=widgets,
                                     plot_height=plot_height,
                                     plot_width=plot_width,
                                     xlimits=xlimits,
                                     ylimits=ylimits)
            _copied_msg = "all"
        elif evtID == ID_interactivePanel_copy_frame:
            frame_properties = style_data.get("frame_properties", {})
            self._item_style_.update(frame_properties=frame_properties)
            _copied_msg = "frame"
        elif evtID == ID_interactivePanel_copy_legend:
            legend_properties = style_data.get("legend_properties", {})
            self._item_style_.update(legend_properties=legend_properties)
            _copied_msg = "legend"
        elif evtID == ID_interactivePanel_copy_tools:
            tools = style_data.get("tools", {})
            self._item_style_.update(tools=tools)
            _copied_msg = "tools"
        elif evtID == ID_interactivePanel_copy_annotations:
            annotation_properties = style_data.get("annotation_properties", {})
            self._item_style_.update(annotation_properties=annotation_properties)
            _copied_msg = "annotations"
        elif evtID == ID_interactivePanel_copy_colorbar:
            colorbar_properties = style_data.get("colorbar_properties", {})
            self._item_style_.update(colorbar_properties=colorbar_properties)
            _copied_msg = "colorbar"
        elif evtID == ID_interactivePanel_copy_overlay:
            overlay_properties = style_data.get("overlay_properties", {})
            self._item_style_.update(overlay_properties=overlay_properties)
            _copied_msg = "overlay"
        elif evtID == ID_interactivePanel_copy_widgets:
            widgets = style_data.get("widgets", {})
            self._item_style_.update(widgets=widgets)
            _copied_msg = "widgets"
        elif evtID == ID_interactivePanel_copy_plots:
            plot_properties = style_data.get("plot_properties", {})
            self._item_style_.update(plot_properties=plot_properties)
            _copied_msg = "plot"
        elif evtID == ID_interactivePanel_copy_preprocess:
            preprocessing_properties = style_data.get("preprocessing_properties", {})
            self._item_style_.update(preprocessing_properties=preprocessing_properties)
            _copied_msg = "pre-processing"
        elif evtID == ID_interactivePanel_copy_figure:
            plot_height = style_data.get("plot_height", self.config.figHeight)
            plot_width = style_data.get("plot_width", self.config.figWidth)
            self._item_style_.update(plot_height=plot_height, plot_width=plot_width)
            _copied_msg = "figure size"
        elif evtID == ID_interactivePanel_copy_plot:
            xlimits = style_data.get("xlimits", [])
            ylimits = style_data.get("ylimits", [])
            self._item_style_.update(xlimits=xlimits, ylimits=ylimits)
            _copied_msg = "plot limits"

        print("Copied [{}] parameters from: {} - {} - {}".format(_copied_msg, name, key, innerKey))

    def on_apply_style(self, evt, itemID=None):
        """
        Apply/paste copied parameters from one object to another
        ===
        evt : wxPython event, int
            event used to figure out which action should be taken. If event is an
            integer, no evt.GetId() will be used
        itemID : int
            checked item ID in the table
        """

        if itemID is None:
            name, key, innerKey = self._getItemDetails()
        else:
            name, key, innerKey = self._getItemDetails(itemID)

        if isinstance(evt, int):
            evtID = evt
        else:
            evtID = evt.GetId()

        data = self.getItemData(name, key, innerKey)
        style_data = deepcopy(data.get("interactive_params", {}))
        _copied_msg = ""

        if len(self._item_style_) == 0:
            return

        if evtID == ID_interactivePanel_apply_all:
            if "frame_properties" in self._item_style_:
                style_data['frame_properties'] = self._item_style_['frame_properties']
            if "legend_properties" in self._item_style_:
                style_data['legend_properties'] = self._item_style_['legend_properties']
            if "tools" in self._item_style_:
                style_data['tools'] = self._item_style_['tools']
            if "colorbar_properties" in self._item_style_:
                style_data['colorbar_properties'] = self._item_style_['colorbar_properties']
            if "overlay_properties" in self._item_style_:
                style_data['overlay_properties'] = self._item_style_['overlay_properties']
            if "plot_properties" in self._item_style_:
                style_data['plot_properties'] = self._item_style_['plot_properties']
            if "preprocessing_properties" in self._item_style_:
                style_data['preprocessing_properties'] = self._item_style_['preprocessing_properties']
            if "annotation_properties" in self._item_style_:
                style_data['annotation_properties'] = self._item_style_['annotation_properties']
            if "widgets" in self._item_style_:
                style_data['widgets'] = self._item_style_['widgets']
            if "plot_height" in self._item_style_:
                style_data['plot_height'] = self._item_style_['plot_height']
            if "plot_width" in self._item_style_:
                style_data['plot_width'] = self._item_style_['plot_width']
            if "xlimits" in self._item_style_:
                style_data['xlimits'] = self._item_style_['xlimits']
            if "ylimits" in self._item_style_:
                style_data['ylimits'] = self._item_style_['ylimits']
            _copied_msg = "all"
        elif evtID == ID_interactivePanel_apply_frame:
            if "frame_properties" in self._item_style_:
                style_data['frame_properties'] = self._item_style_['frame_properties']
                _copied_msg = "frame"
        elif evtID == ID_interactivePanel_apply_plots:
            if "plot_properties" in self._item_style_:
                style_data['plot_properties'] = self._item_style_['plot_properties']
                _copied_msg = "plot"
        elif evtID == ID_interactivePanel_apply_preprocess:
            if "preprocessing_properties" in self._item_style_:
                style_data['preprocessing_properties'] = self._item_style_['preprocessing_properties']
                _copied_msg = "pre-processing"
        elif evtID == ID_interactivePanel_apply_legend:
            if "legend_properties" in self._item_style_:
                style_data['legend_properties'] = self._item_style_['legend_properties']
                _copied_msg = "legend"
        elif evtID == ID_interactivePanel_apply_annotations:
            if "annotation_properties" in self._item_style_:
                style_data['annotation_properties'] = self._item_style_['annotation_properties']
                _copied_msg = "annotation"
        elif evtID == ID_interactivePanel_apply_colorbar:
            if "colorbar_properties" in self._item_style_:
                style_data['colorbar_properties'] = self._item_style_['colorbar_properties']
                _copied_msg = "colorbar"
        elif evtID == ID_interactivePanel_apply_tools:
            if "tools" in self._item_style_:
                style_data['tools'] = self._item_style_['tools']
                _copied_msg = "tools"
        elif evtID == ID_interactivePanel_apply_overlay:
            if "overlay_properties" in self._item_style_:
                style_data['overlay_properties'] = self._item_style_['overlay_properties']
                _copied_msg = "overlay"
        elif evtID == ID_interactivePanel_apply_widgets:
            if "widgets" in self._item_style_:
                style_data['widgets'] = self._item_style_['widgets']
                _copied_msg = "widgets"
        elif evtID == ID_interactivePanel_apply_figure:
            if "plot_height" in self._item_style_:
                style_data['plot_height'] = self._item_style_['plot_height']
            if "plot_width" in self._item_style_:
                style_data['plot_width'] = self._item_style_['plot_width']
                _copied_msg = "figure size"
        elif evtID == ID_interactivePanel_apply_plot:
            if "xlimits" in self._item_style_:
                style_data['xlimits'] = self._item_style_['xlimits']
            if "ylimits" in self._item_style_:
                style_data['ylimits'] = self._item_style_['ylimits']
            _copied_msg = "plot limits"

        self.onUpdateItemParameters(name, key, innerKey, style_data)

        print("Applied [{}] parameters from {} - {} - {} to {} - {} - {}".format(
            _copied_msg, self._item_style_['document_title'],
            self._item_style_['item_type'], self._item_style_['item_title'],
            name, key, innerKey))

    def on_apply_style_batch(self, evt):
        """
        Apply/paste copied parameters from one object to another - batch mode
        ===
        evt : wxPython event
            event used to figure out which action should be taken
        """
        if len(self._item_style_) == 0:
            self.presenter.onThreading(None, ("Style clipboard is empty. Please try again", 4),
                                       action='updateStatusbar')
            return


        # get event and decide event trigger
        evtID = evt.GetId()
        if evtID == ID_interactivePanel_apply_batch_all: evt_trg = ID_interactivePanel_apply_all
        elif evtID == ID_interactivePanel_apply_batch_plot: evt_trg = ID_interactivePanel_apply_plot
        elif evtID == ID_interactivePanel_apply_batch_figure: evt_trg = ID_interactivePanel_apply_figure
        elif evtID == ID_interactivePanel_apply_batch_frame: evt_trg = ID_interactivePanel_apply_frame
        elif evtID == ID_interactivePanel_apply_batch_legend: evt_trg = ID_interactivePanel_apply_legend
        elif evtID == ID_interactivePanel_apply_batch_widgets: evt_trg = ID_interactivePanel_apply_widgets
        elif evtID == ID_interactivePanel_apply_batch_colorbar: evt_trg = ID_interactivePanel_apply_colorbar
        elif evtID == ID_interactivePanel_apply_batch_annotations: evt_trg = ID_interactivePanel_apply_annotations
        elif evtID == ID_interactivePanel_apply_batch_tools: evt_trg = ID_interactivePanel_apply_tools
        elif evtID == ID_interactivePanel_apply_batch_plots: evt_trg = ID_interactivePanel_apply_plots
        elif evtID == ID_interactivePanel_apply_batch_preprocess: evt_trg = ID_interactivePanel_apply_preprocess
        elif evtID == ID_interactivePanel_apply_batch_overlay: evt_trg = ID_interactivePanel_apply_overlay

        # iterate over list and apply style to selected items
        rows = self.itemsList.GetItemCount()
        for row in range(rows):
            if self.itemsList.IsChecked(index=row):
                self.on_apply_style(evt=evt_trg, itemID=row)

    def on_apply_style_menu(self, evt):
        """
        Menu produced when apply_style button is used
        ===
        evt : wxPython event
            unused
        """
        if len(self._item_style_) == 0:
            self.presenter.onThreading(None, ("Style clipboard is empty. Please try again", 4),
                                       action='updateStatusbar')
            return

        self.Bind(wx.EVT_MENU, self.on_apply_style_batch, id=ID_interactivePanel_apply_batch_all)
        self.Bind(wx.EVT_MENU, self.on_apply_style_batch, id=ID_interactivePanel_apply_batch_plot)
        self.Bind(wx.EVT_MENU, self.on_apply_style_batch, id=ID_interactivePanel_apply_batch_figure)
        self.Bind(wx.EVT_MENU, self.on_apply_style_batch, id=ID_interactivePanel_apply_batch_frame)
        self.Bind(wx.EVT_MENU, self.on_apply_style_batch, id=ID_interactivePanel_apply_batch_legend)
        self.Bind(wx.EVT_MENU, self.on_apply_style_batch, id=ID_interactivePanel_apply_batch_widgets)
        self.Bind(wx.EVT_MENU, self.on_apply_style_batch, id=ID_interactivePanel_apply_batch_colorbar)
        self.Bind(wx.EVT_MENU, self.on_apply_style_batch, id=ID_interactivePanel_apply_batch_annotations)
        self.Bind(wx.EVT_MENU, self.on_apply_style_batch, id=ID_interactivePanel_apply_batch_tools)
        self.Bind(wx.EVT_MENU, self.on_apply_style_batch, id=ID_interactivePanel_apply_batch_overlay)
        self.Bind(wx.EVT_MENU, self.on_apply_style_batch, id=ID_interactivePanel_apply_batch_plots)
        self.Bind(wx.EVT_MENU, self.on_apply_style_batch, id=ID_interactivePanel_apply_batch_preprocess)

        menu = wx.Menu()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_interactivePanel_apply_batch_all,
                                     text='Paste: All (selected items)',
                                     bitmap=None))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_interactivePanel_apply_batch_plot,
                                     text='Paste: X/Y limits (selected items)',
                                     bitmap=None))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_interactivePanel_apply_batch_figure,
                                     text='Paste: Figure parameters (selected items)',
                                     bitmap=None))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_interactivePanel_apply_batch_frame,
                                     text='Paste: Axes parameters (selected items)',
                                     bitmap=None))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_interactivePanel_apply_batch_preprocess,
                                     text='Paste: Pre-processing parameters (selected items)',
                                     bitmap=None))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_interactivePanel_apply_batch_annotations,
                                     text='Paste: Annotation parameters (selected items)',
                                     bitmap=self.icons.iconsLib['annotate16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_interactivePanel_apply_batch_plots,
                                     text='Paste: Plot parameters (selected items)',
                                     bitmap=None))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_interactivePanel_apply_batch_colorbar,
                                     text='Paste: Colorbar parameters (selected items)',
                                     bitmap=self.icons.iconsLib['panel_colorbar_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_interactivePanel_apply_batch_legend,
                                     text='Paste: Legend parameters (selected items)',
                                     bitmap=self.icons.iconsLib['panel_legend_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_interactivePanel_apply_batch_overlay,
                                     text='Paste: Overlay parameters (selected items)',
                                     bitmap=self.icons.iconsLib['overlay_2D_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_interactivePanel_apply_batch_tools,
                                     text='Paste: Tools parameters (selected items)',
                                     bitmap=self.icons.iconsLib['parameters_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_interactivePanel_apply_batch_widgets,
                                     text='Paste: Widget parameters (selected items)',
                                     bitmap=None))

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def _onSash(self, evt):
        evt.Veto()

    def onClose(self, evt):
        self.config.interactiveParamsWindow_on_off = False
        self.Destroy()

    def onGenerateHTMLThreaded(self, evt):

        if not self.config.threading:
            print("Exporting interactive document using a non-threaded process")
            self.onGenerateHTML(None)
        else:
            print("Exporting interactive document using a threaded process")
            th = threading.Thread(target=self.onGenerateHTML, args=(evt,))
            # Start thread
            try: th.start()
            except: print('Failed to execute the operation in threaded mode. Consider switching it off?')

    def OnKey(self, evt=None):
        keyCode = evt.GetKeyCode()
        if keyCode == 344:  # F5
            self.onUpdateList()

        if evt != None:
            evt.Skip()

    def onItemCheck(self, evt=None):
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

    def onCustomiseItem(self, evt):
        try: name, key, innerKey = self._getItemDetails()
        except TypeError: 
            print("Please select an item in the table")
            return
        data = self.getItemData(name, key, innerKey)

        kwargs = dict(data=data, document_title=name, item_type=key, item_title=innerKey)
        self.itemEditor = panelCustomiseInteractive(self.presenter, self, self.config, self.icons, **kwargs)
        self.itemEditor.Show()

    def onUpdateItemParameters(self, name, key, innerKey, parameters):
        """
        Updates interactive parameters for selected item.
        @param name: name of the document    (str)
        @param key: type of dataset    (str)
        @param innerKey: name of dataset    (str)
        @param parameters: updated parameters    (dict)
        """

        document = self.documentsDict[name]

        if key == 'MS' and innerKey == '':
            document.massSpectrum['interactive_params'] = parameters

        if key == 'Processed MS' and innerKey == '':
            document.smoothMS['interactive_params'] = parameters

        if key == 'RT' and innerKey == '':
            document.RT['interactive_params'] = parameters

        if key == 'RT, multiple' and innerKey != '':
            document.multipleRT[innerKey]['interactive_params'] = parameters

        if key == '1D' and innerKey == '':
            document.DT['interactive_params'] = parameters

        if key == '1D, multiple' and innerKey != '':
            document.multipleDT[innerKey]['interactive_params'] = parameters

        if key == 'MS, multiple' and innerKey != '':
            document.multipleMassSpectrum[innerKey]['interactive_params'] = parameters

        if key == 'DT-IMS' and innerKey != '':
            document.IMS1DdriftTimes[innerKey]['interactive_params'] = parameters

        if key == 'RT, combined' and innerKey != '':
            document.IMSRTCombIons[innerKey]['interactive_params'] = parameters

        if key == '2D' and innerKey == '':
            document.IMS2D['interactive_params'] = parameters

        if key == '2D, processed' and innerKey == '':
            document.IMS2Dprocess['interactive_params'] = parameters

        if key == '2D, processed' and innerKey == '':
            document.IMS2Dprocess['interactive_params'] = parameters

        if key == '2D' and innerKey != '':
            document.IMS2Dions[innerKey]['interactive_params'] = parameters

        if key == '2D, combined' and innerKey != '':
            document.IMS2DCombIons[innerKey]['interactive_params'] = parameters

        if key == '2D, processed' and innerKey != '':
            document.IMS2DionsProcess[innerKey]

        if key == 'Overlay' and innerKey != '':
            document.IMS2DoverlayData[innerKey]['interactive_params'] = parameters

        if key == 'Statistical' and innerKey != '':
            document.IMS2DstatsData[innerKey]['interactive_params'] = parameters

        if key == 'Other data' and innerKey != '':
            document.other_data[innerKey].update(interactive_params=parameters)

        if key == 'UniDec' and innerKey != '':
            document.massSpectrum['unidec'][innerKey]['interactive_params'] = parameters

        if key == 'UniDec, processed' and innerKey != '':
            document.massSpectrum['unidec'][innerKey]['interactive_params'] = parameters

        if key == 'UniDec, multiple' and innerKey != '':
            unidecMethod = re.split(' \| ', innerKey)[0]
            innerKey = re.split(' \| ', innerKey)[1]
            document.multipleMassSpectrum[innerKey]['unidec'][unidecMethod]['interactive_params'] = parameters
            
        if key == "MS/MS" and innerKey == '': 
            document.tandem_spectra.update(interactive_params=parameters)

        # Update dictionary
        self.presenter.OnUpdateDocument(document, 'no_refresh')

    def onUpdateList(self):

        # clear table
        self.itemsList.DeleteAllItems()

        # populate table
        self.populateTable()

    def makeGUI(self):
        """Make GUI elements."""

        size_left = 735
        size_right = 655
        size_height = 650

        if self.currentDisplaySize is not None:
            screen_width, screen_height = self.currentDisplaySize[2], self.currentDisplaySize[3]
            if (size_height + size_right) > screen_width:
                size_right = screen_width - size_left

            if size_height > screen_height:
               size_height = screen_height - 75

        # splitter window
        self.split_panel = wx.SplitterWindow(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize,
                                             wx.TAB_TRAVERSAL | wx.SP_3DSASH | wx.SP_LIVE_UPDATE)

        # make panels
        self.list_panel = self.makeListPanel(self.split_panel)

        self.list_panel.SetSize((size_left, -1))
        self.list_panel.SetMinSize((size_left, -1))
        self.list_panel.SetMaxSize((size_left, -1))

        self.settings_panel = self.makeSettingsPanel(self.split_panel)

        self.settings_panel.SetSize((size_right, -1))
        self.settings_panel.SetMinSize((size_right, -1))
        self.settings_panel.SetMaxSize((size_right, -1))

        self.split_panel.SplitVertically(self.list_panel, self.settings_panel)
        self.split_panel.SetSashGravity(0.0)
        self.split_panel.SetSashSize(2)
        self.split_panel.SetSashPosition((size_left + 10))

        # pack element
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(self.split_panel, 1, wx.EXPAND)

        # fit layout
        split_size = (size_left + size_right, size_height)
        self.SetSize(split_size)
        self.SetMinSize(split_size)

    def makeListPanel(self, split_panel):
        panel = wx.Panel(split_panel, -1, size=(-1, -1))

        preToolbar = self.makePreToolbar(panel)
        self.itemsList = self.makeItemsList(panel)

        # Add to grid sizer
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(preToolbar, 0, wx.EXPAND, 0)
        mainSizer.Add(self.itemsList, 1, wx.EXPAND | wx.ALL, 0)
        mainSizer.Fit(panel)

        panel.SetSizer(mainSizer)
        panel.Layout()

        return panel

    def makeSettingsPanel(self, split_panel):
        panel = wx.Panel(split_panel, -1, size=(-1, -1))

        editor = self.makeItemEditor(panel)
        buttons = self.makeDlgButtons(panel)

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(editor, 1, wx.EXPAND | wx.ALL, 0)
        mainSizer.Add(buttons, 0, wx.EXPAND, 0)

        # pack elements
#         mainSizer = wx.BoxSizer( wx.VERTICAL)
#         mainSizer.Add(sizer_right, 1, wx.EXPAND |wx.ALL, 0)
        panel.SetSizer(mainSizer)
        panel.Layout()

        return panel

    def makePreToolbar(self, panel):

        checkAll = wx.BitmapButton(panel, ID_interactivePanel_check_menu, self.icons.iconsLib['check16'],
                                   size=(26, 26), style=wx.BORDER_DEFAULT | wx.ALIGN_CENTER_VERTICAL)
        self.Bind(wx.EVT_BUTTON, self.onCheckTool, id=ID_interactivePanel_check_menu)

        document_label = wx.StaticText(panel, -1, "Document filter:")
        docList = ['All'] + self.documentsDict.keys()
        self.docSelection_combo = wx.Choice(panel, -1, choices=docList, size=(160, -1))
        self.docSelection_combo.SetStringSelection("All")
        self.docSelection_combo.Bind(wx.EVT_CHOICE, self.OnShowOneDataType)

        type_label = wx.StaticText(panel, -1, "Item type filter:")
        self.dataSelection_combo = wx.Choice(panel, -1, choices=["Show all", "Show selected",
                                                                 "Show MS (all)", "Show MS (multiple)",
                                                                 "Show MS", "Show RT (all)", "Show RT",
                                                                 "Show 1D (all)", "Show 1D IM-MS",
                                                                 "Show 2D IM-MS", "Show 1D plots (MS, DT, RT)",
                                                                 "Show Overlay", "Show Statistical",
                                                                 "Show UniDec (all)",
                                                                 "Show UniDec (processed)",
                                                                 "Show UniDec (multiple)",
                                                                 "Show Other data"],
                                             size=(150, -1))
        self.dataSelection_combo.SetStringSelection("Show All")
        self.dataSelection_combo.Bind(wx.EVT_CHOICE, self.OnShowOneDataType)

        output_label = wx.StaticText(panel, -1, "Assign output page:")
        self.pageLayoutSelect_toolbar = wx.Choice(panel, -1, choices=self.config.pageDict.keys(), size=(140, -1))
        self.pageLayoutSelect_toolbar.SetStringSelection("None")
        page_applyBtn = wx.BitmapButton(panel, ID_assignPageSelected_HTML, self.icons.iconsLib['tick16'],
                                      size=(26, 26), style=wx.BORDER_DEFAULT | wx.ALIGN_CENTER_VERTICAL)
        self.Bind(wx.EVT_BUTTON, self.on_change_page_for_items, id=ID_assignPageSelected_HTML)

        colormap_label = wx.StaticText(panel, -1, "Assign colormap:")
        self.colormapSelect_toolbar = wx.Choice(panel, -1, choices=self.config.cmaps2,
                                                size=(-1, -1))
        self.colormapSelect_toolbar.SetStringSelection(self.config.currentCmap)
        self.Bind(wx.EVT_BUTTON, self.on_change_colormap_for_items, id=ID_assignColormapSelected_HTML)

        colormap_applyBtn = wx.BitmapButton(panel, ID_assignColormapSelected_HTML, self.icons.iconsLib['tick16'],
                                      size=(26, 26), style=wx.BORDER_DEFAULT | wx.ALIGN_CENTER_VERTICAL)

        self.apply_style_btn = wx.BitmapButton(panel, -1, self.icons.iconsLib['idea16'],
                                          size=(26, 26), style=wx.BORDER_DEFAULT | wx.ALIGN_CENTER_VERTICAL)
        self.apply_style_btn.Bind(wx.EVT_BUTTON, self.on_apply_style_menu)
        
        sort_label = wx.StaticText(panel, -1, "Sort:")
        self.sort_before_saving = wx.CheckBox(panel, -1 , u'', (15, 30))
        self.sort_before_saving.SetToolTip(wx.ToolTip("When checked, table will be sorted by the # column before plots are exported."))
        self.sort_before_saving.SetValue(self.config.interactive_sort_before_saving)
        self.sort_before_saving.Bind(wx.EVT_CHECKBOX, self.onApply)

        # pack elements
        vertical_line_1 = wx.StaticLine(panel, -1, style=wx.LI_VERTICAL)
        vertical_line_2 = wx.StaticLine(panel, -1, style=wx.LI_VERTICAL)
        vertical_line_3 = wx.StaticLine(panel, -1, style=wx.LI_VERTICAL)
        vertical_line_4 = wx.StaticLine(panel, -1, style=wx.LI_VERTICAL)
        vertical_line_5 = wx.StaticLine(panel, -1, style=wx.LI_VERTICAL)

        grid = wx.GridBagSizer(1, 1)
        grid.Add(document_label, (0, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(vertical_line_1, (0, 2), wx.GBSpan(2, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(type_label, (0, 3), wx.GBSpan(1, 1), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(vertical_line_2, (0, 4), wx.GBSpan(2, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(output_label, (0, 5), wx.GBSpan(1, 3), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(vertical_line_3, (0, 8), wx.GBSpan(2, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(colormap_label, (0, 9), wx.GBSpan(1, 2), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(vertical_line_4, (0, 11), wx.GBSpan(2, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(vertical_line_5, (0, 13), wx.GBSpan(2, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(sort_label, (0, 14), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)

        grid.Add(checkAll, (1, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.docSelection_combo, (1, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.dataSelection_combo, (1, 3), wx.GBSpan(1, 1), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.pageLayoutSelect_toolbar, (1, 5), wx.GBSpan(1, 1), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(page_applyBtn, (1, 6), wx.GBSpan(1, 1), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.colormapSelect_toolbar, (1, 9), wx.GBSpan(1, 1), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(colormap_applyBtn, (1, 10), wx.GBSpan(1, 1), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.apply_style_btn, (1, 12), wx.GBSpan(1, 1), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.sort_before_saving, (1, 14), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL)


        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(grid, 0, wx.ALL, 2)
        return mainSizer

    def makeItemsList(self, panel):
        """Make list for items."""

        # init table
        itemsList = ListCtrl(panel, size=(750, -1),
                             style=wx.LC_REPORT | wx.LC_VRULES)
        itemsList.SetFont(wx.SMALL_FONT)

        for item in self.config._interactiveSettings:
            order = item['order']
            name = item['name']
            if item['show']:
                width = item['width']
            else:
                width = 0
            itemsList.InsertColumn(order, name, width=width, format=wx.LIST_FORMAT_LEFT)

        # Bind events
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onItemSelected)
        self.Bind(wx.EVT_LIST_COL_CLICK, self.OnGetColumnClick)
        self.Bind(wx.EVT_LEFT_DCLICK, self.onCustomiseItem)
        self.Bind(wx.EVT_LIST_KEY_DOWN, self.onItemClicked)
        self.Bind(wx.EVT_LIST_BEGIN_LABEL_EDIT, self.onStartEditingItem)
        self.Bind(wx.EVT_LIST_END_LABEL_EDIT, self.onFinishEditingItem)

        return itemsList

    def makeDlgButtons(self, panel):

        pathBtn = wx.Button(panel, -1, "Set Path", size=(-1, 22))
        saveBtn = wx.Button(panel, -1, "Export HTML", size=(-1, 22))
        cancelBtn = wx.Button(panel, -1, "Cancel", size=(-1, 22))

        openHTMLWebBtn = wx.Button(panel, ID_helpHTMLEditor, "HTML Editor", size=(-1, 22))
        openHTMLWebBtn.SetToolTip(wx.ToolTip("Opens a web-based HTML editor"))

        itemPath_label = wx.StaticText(panel, -1, "File path:")
        self.itemPath_value = wx.TextCtrl(panel, -1, "", size=(350, -1))
        self.itemPath_value.SetValue(str(self.currentPath))

        documentName_label = wx.StaticText(panel, -1, "Document title:")
        self.documentName_value = wx.TextCtrl(panel, -1, "", size=(350, -1))
        self.documentName_value.SetValue(str(self.currentDocumentName))

        self.openInBrowserCheck = makeCheckbox(panel, u"Open in browser after saving")
        self.openInBrowserCheck.SetValue(self.config.openInteractiveOnSave)

        self.addOfflineSupportCheck = makeCheckbox(panel, u"Add offline support")
        self.addOfflineSupportCheck.SetValue(self.config.interactive_add_offline_support)
        self.addOfflineSupportCheck.SetToolTip(wx.ToolTip("Will enable viewing HTML files offline. Beware: file size and time to generate the document will increase."))

        self.addWatermarkCheck = makeCheckbox(panel, u"Add watermark")
        self.addWatermarkCheck.SetValue(True)
        self.addWatermarkCheck.SetToolTip(wx.ToolTip("When checked, a watermark message will be displayed on each tab in the document. Only a little bit of advertising..."))


        btnGrid = wx.GridBagSizer(1, 1)
        btnGrid.Add(openHTMLWebBtn, (0, 0), flag=wx.ALIGN_CENTER | wx.ALIGN_CENTER_HORIZONTAL)
        btnGrid.Add(cancelBtn, (0, 1), flag=wx.ALIGN_CENTER | wx.ALIGN_CENTER_HORIZONTAL)
        btnGrid.Add(self.openInBrowserCheck, (0, 2), flag=wx.ALIGN_CENTER | wx.ALIGN_CENTER_HORIZONTAL)
        btnGrid.Add(self.addOfflineSupportCheck, (0, 3), flag=wx.ALIGN_CENTER | wx.ALIGN_CENTER_HORIZONTAL)
        btnGrid.Add(self.addWatermarkCheck, (0, 4), flag=wx.ALIGN_CENTER | wx.ALIGN_CENTER_HORIZONTAL)

        docGrid = wx.GridBagSizer(1, 1)
        docGrid.Add(documentName_label, (0, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        docGrid.Add(self.documentName_value, (0, 1), flag=wx.ALIGN_CENTER | wx.EXPAND)
        docGrid.Add(itemPath_label, (1, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        docGrid.Add(self.itemPath_value, (1, 1), flag=wx.ALIGN_CENTER | wx.EXPAND)
        docGrid.Add(pathBtn, (1, 2), flag=wx.ALIGN_CENTER | wx.ALIGN_CENTER_HORIZONTAL)
        docGrid.Add(saveBtn, (1, 3), flag=wx.ALIGN_CENTER | wx.ALIGN_CENTER_HORIZONTAL)

        # make bindings
        saveBtn.Bind(wx.EVT_BUTTON, self.onGenerateHTMLThreaded)
        openHTMLWebBtn.Bind(wx.EVT_BUTTON, self.presenter.onLibraryLink)
        cancelBtn.Bind(wx.EVT_BUTTON, self.onClose)
        pathBtn.Bind(wx.EVT_BUTTON, self.onGetSavePath)

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(docGrid, 0, wx.EXPAND, 0)
        mainSizer.Add(btnGrid, 0, wx.EXPAND, 0)
        mainSizer.Fit(panel)
        return mainSizer

    def makeItemEditor(self, panel):
        """Make items editor."""

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.editorBook = wx.Notebook(panel, wx.ID_ANY, wx.DefaultPosition, size=(-1, -1), style=0)

        self.htmlView = wx.lib.scrolledpanel.ScrolledPanel(self.editorBook, wx.ID_ANY, wx.DefaultPosition, (-1, -1), wx.TAB_TRAVERSAL)
        self.htmlView.SetupScrolling()
        self.htmlView = self.makeHTMLView(self.htmlView)
        self.editorBook.AddPage(self.htmlView, u"HTML", False)

        self.pageView = wx.lib.scrolledpanel.ScrolledPanel(self.editorBook, wx.ID_ANY, wx.DefaultPosition, (-1, -1), wx.TAB_TRAVERSAL)
        self.pageView.SetupScrolling()
        self.pageView = self.makePageView(self.pageView)
        self.editorBook.AddPage(self.pageView, u"Output page", False)

        self.propertiesView = wx.lib.scrolledpanel.ScrolledPanel(self.editorBook, wx.ID_ANY, wx.DefaultPosition, (-1, -1), wx.TAB_TRAVERSAL)
        self.propertiesView.SetupScrolling()
        self.propertiesView = self.makePropertiesView(self.propertiesView)
        self.editorBook.AddPage(self.propertiesView, u"Default settings", False)

        mainSizer.Add(self.editorBook, 1, wx.EXPAND | wx.ALL, 3)
        mainSizer.Fit(self.editorBook)

        # run events
#         self.onSetupTools(evt=None)
        self.onSelectPageProperties(evt=None)
        self.onChangePage(evt=None)

        return mainSizer

    def makePageView(self, panel):
        RICH_TEXT = wx.TE_MULTILINE | wx.TE_WORDWRAP | wx.TE_RICH2

        self.mainBoxPage = makeStaticBox(panel, "Page properties", (-1, -1), wx.BLACK)
        self.mainBoxPage.SetSize((-1, -1))
        html_box_sizer = wx.StaticBoxSizer(self.mainBoxPage, wx.HORIZONTAL)

        pageSelect_label = makeStaticText(panel, u"Select page:")
        self.pageLayoutSelect_propView = wx.ComboBox(panel, -1, choices=[],
                                        value="None", style=wx.CB_READONLY)
        self.pageLayoutSelect_propView.Bind(wx.EVT_COMBOBOX, self.onChangePage)

        self.addPage = wx.Button(panel, wx.ID_ANY, size=(26, 26))
        self.addPage.SetBitmap(self.icons.iconsLib['add16'])
        self.addPage.Bind(wx.EVT_BUTTON, self.onAddPage)
        self.addPage.SetToolTip(wx.ToolTip("Add new page. You can change settings below"))

        self.removePage = wx.Button(panel, wx.ID_ANY, size=(26, 26))
        self.removePage.SetBitmap(self.icons.iconsLib['remove16'])
        self.removePage.Bind(wx.EVT_BUTTON, self.onRemovePage)
        self.removePage.SetToolTip(wx.ToolTip("Remove current page"))

        self.clearAllPages = wx.Button(panel, wx.ID_ANY, size=(26, 26))
        self.clearAllPages.SetBitmap(self.icons.iconsLib['bin16'])
        self.clearAllPages.Bind(wx.EVT_BUTTON, self.onClearPages)
        self.clearAllPages.SetToolTip(wx.ToolTip("Remove ALL non-default pages"))

        layoutDoc_label = makeStaticText(panel, u"Page layout:")
        self.layoutDoc_combo = wx.ComboBox(panel, -1, choices=self.config.interactive_pageLayout_choices,
                                        value=self.config.layoutModeDoc, style=wx.CB_READONLY)
        self.layoutDoc_combo.SetToolTip(wx.ToolTip("Select type of layout for the page. Default: Individual"))
        self.layoutDoc_combo.Bind(wx.EVT_COMBOBOX, self.onApply)
        self.layoutDoc_combo.Bind(wx.EVT_COMBOBOX, self.onSelectPageProperties)

        columns_label = makeStaticText(panel, u"Columns:")
        self.columns_value = wx.TextCtrl(panel, -1, "", size=(50, -1))
        self.columns_value.SetToolTip(wx.ToolTip("Grid only. Number of columns in the grid"))
        self.columns_value.Bind(wx.EVT_TEXT, self.onSelectPageProperties)

        self.grid_shared_tools = makeCheckbox(panel, u"Shared tools")
        self.grid_shared_tools.SetValue(True)
        self.grid_shared_tools.Bind(wx.EVT_CHECKBOX, self.onSelectPageProperties)

        self.grid_add_custom_js_widgets = makeCheckbox(panel, u"Add widgets when available")
        self.grid_add_custom_js_widgets.SetToolTip(wx.ToolTip("Grid/rows only. Add custom widgets that work for all plots in a grid."))
        self.grid_add_custom_js_widgets.SetValue(True)
        self.grid_add_custom_js_widgets.Bind(wx.EVT_CHECKBOX, self.onSelectPageProperties)

        height_label = makeStaticText(panel, u"Plot height:")
        self.grid_height_value = wx.TextCtrl(panel, -1, "", size=(50, -1))
        self.grid_height_value.SetToolTip(wx.ToolTip("Grid only. Height of individual plots"))
        self.grid_height_value.Bind(wx.EVT_TEXT, self.onSelectPageProperties)

        width_label = makeStaticText(panel, u"Plot width:")
        self.grid_width_value = wx.TextCtrl(panel, -1, "", size=(50, -1))
        self.grid_width_value.SetToolTip(wx.ToolTip("Grid only. Width of individual plots"))
        self.grid_width_value.Bind(wx.EVT_TEXT, self.onSelectPageProperties)


        min_size_text = 525
        itemName_label = wx.StaticText(panel, -1, "Title:", style=RICH_TEXT)
        self.pageTitle_value = wx.TextCtrl(panel, -1, "", size=(-1, -1))
        self.pageTitle_value.SetToolTip(wx.ToolTip("Title of the HTML page."))
        self.pageTitle_value.Bind(wx.EVT_TEXT, self.onSelectPageProperties)

        itemHeader_label = wx.StaticText(panel, -1, "Header:")
        self.pageHeader_value = wx.TextCtrl(panel, -1, "", size=(min_size_text, 100), style=RICH_TEXT)
        self.pageHeader_value.SetToolTip(wx.ToolTip("HTML-rich text to be used in the header of the interactive figure."))
        self.pageHeader_value.Bind(wx.EVT_TEXT, self.onSelectPageProperties)

        itemFootnote_label = wx.StaticText(panel, -1, "Footnote:")
        self.pageFootnote_value = wx.TextCtrl(panel, -1, "", size=(min_size_text, 100), style=RICH_TEXT)
        self.pageFootnote_value.SetToolTip(wx.ToolTip("HTML-rich text to be used in the footnote of the interactive figure."))
        self.pageFootnote_value.Bind(wx.EVT_TEXT, self.onSelectPageProperties)

        html_grid = wx.GridBagSizer(2, 5)
        n = 0
        html_grid.Add(pageSelect_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        html_grid.Add(self.pageLayoutSelect_propView, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL | wx.ALL)
        html_grid.Add(self.addPage, (n, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        html_grid.Add(self.removePage, (n, 3), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        html_grid.Add(self.clearAllPages, (n, 4), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        html_grid.Add(layoutDoc_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_RIGHT | wx.ALIGN_TOP)
        html_grid.Add(self.layoutDoc_combo, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL | wx.ALL)
        html_grid.Add(self.grid_add_custom_js_widgets, (n, 2), wx.GBSpan(1, 3), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        html_grid.Add(columns_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        html_grid.Add(self.columns_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        html_grid.Add(self.grid_shared_tools, (n, 2), wx.GBSpan(1, 3), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        html_grid.Add(height_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        html_grid.Add(self.grid_height_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n = n + 1
        html_grid.Add(width_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        html_grid.Add(self.grid_width_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n = n + 1
        html_grid.Add(itemName_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_RIGHT | wx.ALIGN_TOP)
        html_grid.Add(self.pageTitle_value, (n, 1), wx.GBSpan(1, 5), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL | wx.ALL)
        n = n + 1
        html_grid.Add(itemHeader_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_RIGHT | wx.ALIGN_TOP)
        html_grid.Add(self.pageHeader_value, (n, 1), wx.GBSpan(1, 5), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL | wx.ALL)
        n = n + 1
        html_grid.Add(itemFootnote_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_RIGHT | wx.ALIGN_TOP)
        html_grid.Add(self.pageFootnote_value, (n, 1), wx.GBSpan(1, 5), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL | wx.ALL)
        html_box_sizer.Add(html_grid, 0, wx.EXPAND, 0)

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(html_box_sizer, 0, wx.EXPAND, 0)


        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)
        panel.SetBackgroundColour((240, 240, 240))

        return panel

    def makeHTMLView(self, panel):

        RICH_TEXT = wx.TE_MULTILINE | wx.TE_WORDWRAP | wx.TE_RICH2

        self.mainBoxHTML = makeStaticBox(panel, "HTML properties", (-1, -1), wx.BLACK)
        self.mainBoxHTML.SetSize((-1, -1))
        html_box_sizer = wx.StaticBoxSizer(self.mainBoxHTML, wx.HORIZONTAL)

        min_size_text = 550
        # make elements
        editing_label = wx.StaticText(panel, -1, "Document:")
        self.document_value = wx.StaticText(panel, -1, "", size=(min_size_text, -1))

        type_label = wx.StaticText(panel, -1, "Type:")
        self.type_value = wx.StaticText(panel, -1, "", size=(min_size_text, -1))

        details_label = wx.StaticText(panel, -1, "Details:")
        self.details_value = wx.StaticText(panel, -1, "", size=(min_size_text, -1))

        itemInformation_label = wx.StaticText(panel, -1, "Information:")
        self.itemInformation_value = wx.StaticText(panel, -1, "", size=(-1, 70))

        itemName_label = wx.StaticText(panel, -1, "Title:", style=RICH_TEXT)
        self.itemName_value = wx.TextCtrl(panel, -1, "", size=(-1, -1))
        self.itemName_value.SetToolTip(wx.ToolTip("Title of the HTML page. Might not be used."))
        self.itemName_value.Bind(wx.EVT_TEXT, self.onAnnotateItems)

        itemHeader_label = wx.StaticText(panel, -1, "Header:")
        self.itemHeader_value = wx.TextCtrl(panel, -1, "", size=(-1, 120), style=RICH_TEXT)
        self.itemHeader_value.SetToolTip(wx.ToolTip("HTML-rich text to be used in the header of the interactive figure."))
        self.itemHeader_value.Bind(wx.EVT_TEXT, self.onAnnotateItems)

        itemFootnote_label = wx.StaticText(panel, -1, "Footnote:")
        self.itemFootnote_value = wx.TextCtrl(panel, -1, "", size=(-1, 120), style=RICH_TEXT)
        self.itemFootnote_value.SetToolTip(wx.ToolTip("HTML-rich text to be used in the footnote of the interactive figure."))
        self.itemFootnote_value.Bind(wx.EVT_TEXT, self.onAnnotateItems)

        html_grid = wx.GridBagSizer(2, 5)
        n = 0
        html_grid.Add(editing_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        html_grid.Add(self.document_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL | wx.ALL)
        n = n + 1
        html_grid.Add(type_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        html_grid.Add(self.type_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL | wx.ALL)
        n = n + 1
        html_grid.Add(details_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        html_grid.Add(self.details_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL | wx.ALL)
        n = n + 1
        html_grid.Add(itemInformation_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_RIGHT | wx.ALIGN_TOP)
        html_grid.Add(self.itemInformation_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL | wx.ALL)
        n = n + 1
        html_grid.Add(itemName_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        html_grid.Add(self.itemName_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL | wx.ALL)
        n = n + 1
        html_grid.Add(itemHeader_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_RIGHT | wx.ALIGN_TOP)
        html_grid.Add(self.itemHeader_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL | wx.ALL)
        n = n + 1
        html_grid.Add(itemFootnote_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_RIGHT | wx.ALIGN_TOP)
        html_grid.Add(self.itemFootnote_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL | wx.ALL)
        html_box_sizer.Add(html_grid, 0, wx.EXPAND, 0)

        # general subpanel
        general_staticBox = makeStaticBox(panel, "General settings", size=(-1, -1), color=wx.BLACK)
        general_staticBox.SetSize((-1, -1))
        general_box_sizer = wx.StaticBoxSizer(general_staticBox, wx.HORIZONTAL)

        page_label = makeStaticText(panel, u"Output page:")
        self.pageLayoutSelect_htmlView = wx.ComboBox(panel, -1, choices=[], value="None", style=wx.CB_READONLY, size=(200, -1))
        self.pageLayoutSelect_htmlView.Bind(wx.EVT_COMBOBOX, self.on_change_page_for_item)

        order_label = makeStaticText(panel, u"Plot order:")
        self.order_value = wx.TextCtrl(panel, -1, "", size=(50, -1))
        self.order_value.Bind(wx.EVT_TEXT, self.onAnnotateItems)


        general_grid = wx.GridBagSizer(2, 2)
        y = 0
        general_grid.Add(page_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        general_grid.Add(self.pageLayoutSelect_htmlView, (y, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_LEFT)
        y = y + 1
        general_grid.Add(order_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        general_grid.Add(self.order_value, (y, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_LEFT)
        general_box_sizer.Add(general_grid, 0, wx.EXPAND, 10)

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(html_box_sizer, 0, wx.EXPAND, 0)
        mainSizer.Add(general_box_sizer, 0, wx.EXPAND, 0)
        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)
        panel.SetBackgroundColour((240, 240, 240))
        
        return panel

    def onCheckTool(self, evt):

        self.Bind(wx.EVT_MENU, self.OnCheckAllItems, id=ID_interactivePanel_check_all)
        self.Bind(wx.EVT_MENU, self.OnCheckSelectedItems, id=ID_interactivePanel_check_ms)
        self.Bind(wx.EVT_MENU, self.OnCheckSelectedItems, id=ID_interactivePanel_check_rt)
        self.Bind(wx.EVT_MENU, self.OnCheckSelectedItems, id=ID_interactivePanel_check_dt1D)
        self.Bind(wx.EVT_MENU, self.OnCheckSelectedItems, id=ID_interactivePanel_check_dt2D)
        self.Bind(wx.EVT_MENU, self.OnCheckSelectedItems, id=ID_interactivePanel_check_overlay)
        self.Bind(wx.EVT_MENU, self.OnCheckSelectedItems, id=ID_interactivePanel_check_unidec)
        self.Bind(wx.EVT_MENU, self.OnCheckSelectedItems, id=ID_interactivePanel_check_other)

        menu = wx.Menu()
        if self.allChecked:
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_interactivePanel_check_all,
                                         text='Check all...',
                                         bitmap=None))
        else:
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_interactivePanel_check_all,
                                         text='Uncheck all...',
                                         bitmap=None))
        menu.AppendSeparator()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_interactivePanel_check_ms,
                                     text='Check MS only',
                                     bitmap=None))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_interactivePanel_check_rt,
                                     text='Check RT only',
                                     bitmap=None))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_interactivePanel_check_dt1D,
                                     text='Check DT (1D) only',
                                     bitmap=None))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_interactivePanel_check_dt2D,
                                     text='Check DT (2D) only',
                                     bitmap=None))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_interactivePanel_check_overlay,
                                     text='Check Overlay only',
                                     bitmap=None))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_interactivePanel_check_unidec,
                                     text='Check UniDec only',
                                     bitmap=None))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_interactivePanel_check_other,
                                     text='Check Other only',
                                     bitmap=None))

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def makePropertiesView(self, panel):
        
        fontSizer = self.makeFontSubPanel(panel)
        plot1Dsizer = self.make1DplotSubPanel(panel)
        overlaySizer = self.makeOverLaySubPanel(panel)
        markerSizer = self.makeScatterSubPanel(panel)
        barSizer = self.makeBarSubPanel(panel)
        rmsdSizer = self.makeRMSDSubPanel(panel)
        colorbarSizer = self.makeColorbarSubPanel(panel)
        legendSettingsSizer = self.makeLegendSubPanel(panel)
        annotSettingsSizer = self.makeAnnotationSubPanel(panel)
        customJSSizer = self.makeCustomJSSubPanel(panel)

        # Add to grid sizer
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(fontSizer, 0, wx.EXPAND, 0)
        sizer_1.Add(plot1Dsizer, 0, wx.EXPAND, 0)
        sizer_1.Add(overlaySizer, 0, wx.EXPAND, 0)
        sizer_1.Add(markerSizer, 0, wx.EXPAND, 0)
        sizer_1.Add(barSizer, 0, wx.EXPAND, 0)
        sizer_1.Add(annotSettingsSizer, 0, wx.EXPAND, 0)

        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(rmsdSizer, 0, wx.EXPAND, 0)
        sizer_2.Add(colorbarSizer, 0, wx.EXPAND, 0)
        sizer_2.Add(legendSettingsSizer, 0, wx.EXPAND, 0)
        
        sizer_2.Add(customJSSizer, 0, wx.EXPAND, 0)


        # pack elements
        viewSizer = wx.BoxSizer(wx.HORIZONTAL)
        viewSizer.Add(sizer_1, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)
        viewSizer.Add(sizer_2, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)

        viewSizer.Fit(panel)
        panel.SetSizerAndFit(viewSizer)

        panel.SetBackgroundColour((240, 240, 240))

        return panel

    def makeFontSubPanel(self, panel):
        mainBox = makeStaticBox(panel, "Font properties", (210, -1), wx.BLACK)
        mainBox.SetSize((230, -1))
        mainSizer = wx.StaticBoxSizer(mainBox, wx.HORIZONTAL)
        titleFontSize = makeStaticText(panel, u"Title font size")

        self.titleSlider = wx.SpinCtrlDouble(panel, wx.ID_ANY,
                                             value=str(self.config.interactive_title_fontSize), min=8, max=32,
                                             initial=self.config.interactive_title_fontSize, inc=1, size=(50, -1))
        self.titleBoldCheck = makeCheckbox(panel, u"Bold")
        self.titleBoldCheck.SetValue(self.config.interactive_title_weight)

        labelFontSize = makeStaticText(panel, u"Label font size")
        self.labelSlider = wx.SpinCtrlDouble(panel, wx.ID_ANY,
                                             value=str(self.config.interactive_label_fontSize), min=8, max=32,
                                             initial=self.config.interactive_label_fontSize, inc=1, size=(50, -1))

        self.labelBoldCheck = makeCheckbox(panel, u"Bold")
        self.labelBoldCheck.SetValue(self.config.interactive_label_weight)

        tickFontSize = makeStaticText(panel, u"Tick font size")
        self.tickSlider = wx.SpinCtrlDouble(panel, wx.ID_ANY,
                                             value=str(self.config.interactive_tick_fontSize), min=8, max=32,
                                             initial=self.config.interactive_tick_fontSize, inc=1, size=(50, -1))


        precision_label = makeStaticText(panel, u"Tick precision")
        self.tickPrecision = wx.SpinCtrlDouble(panel, wx.ID_ANY,
                                                   value=str(self.config.interactive_tick_precision), min=0, max=5,
                                                   initial=self.config.interactive_tick_precision, inc=1, size=(50, -1))


        self.tickUseScientific = wx.CheckBox(panel, -1 , u'Scientific\nnotation', (15, 30))
        self.tickUseScientific.SetValue(self.config.interactive_tick_useScientific)
        self.tickUseScientific.Bind(wx.EVT_CHECKBOX, self.onEnableDisableItems)

        # Add to grid sizer
        grid = wx.GridBagSizer(2, 2)
        grid.Add(titleFontSize, wx.GBPosition(0, 0), wx.GBSpan(1, 2), TEXT_STYLE_CV_R_L, 2)
        grid.Add(self.titleSlider, wx.GBPosition(1, 0), wx.GBSpan(1, 1), TEXT_STYLE_CV_R_L, 2)
        grid.Add(self.titleBoldCheck, wx.GBPosition(1, 1), wx.GBSpan(1, 1), TEXT_STYLE_CV_R_L, 2)

        grid.Add(labelFontSize, wx.GBPosition(0, 2), wx.GBSpan(1, 2), TEXT_STYLE_CV_R_L, 2)
        grid.Add(self.labelSlider, wx.GBPosition(1, 2), wx.GBSpan(1, 1), TEXT_STYLE_CV_R_L, 2)
        grid.Add(self.labelBoldCheck, wx.GBPosition(1, 3), wx.GBSpan(1, 1), TEXT_STYLE_CV_R_L, 2)

        grid.Add(tickFontSize, wx.GBPosition(2, 0), wx.GBSpan(1, 2), TEXT_STYLE_CV_R_L, 2)
        grid.Add(self.tickSlider, wx.GBPosition(3, 0), wx.GBSpan(1, 1), TEXT_STYLE_CV_R_L, 2)
        grid.Add(precision_label, wx.GBPosition(2, 2), wx.GBSpan(1, 2), TEXT_STYLE_CV_R_L, 2)
        grid.Add(self.tickPrecision, wx.GBPosition(3, 2), wx.GBSpan(1, 1), TEXT_STYLE_CV_R_L, 2)
        grid.Add(self.tickUseScientific, wx.GBPosition(3, 3), wx.GBSpan(1, 1), TEXT_STYLE_CV_R_L, 2)

        mainSizer.Add(grid, 0, wx.EXPAND | wx.ALL, 2)
        return mainSizer

#     def makeImageSubPanel(self):
#         imageBox = makeStaticBox(panel, "Image properties", (230,-1), wx.BLACK)
#         figSizer = wx.StaticBoxSizer(imageBox, wx.HORIZONTAL)
#
#         figHeight1D_label = makeStaticText(panel, u"Height (1D)")
#         self.figHeight1D_value = wx.TextCtrl(panel, -1, "", size=(50, -1))
#         self.figHeight1D_value.SetValue(str(self.config.figHeight1D))
#         self.figHeight1D_value.SetToolTip(wx.ToolTip("Set figure height (pixels)"))
#
#         figWidth1D_label = makeStaticText(panel, u"Width (1D)")
#         self.figWidth1D_value = wx.TextCtrl(panel, -1, "", size=(50, -1))
#         self.figWidth1D_value.SetValue(str(self.config.figWidth1D))
#         self.figWidth1D_value.SetToolTip(wx.ToolTip("Set figure width (pixels)"))
#
#         figHeight_label = makeStaticText(panel, u"Height (2D)")
#         self.figHeight_value = wx.TextCtrl(panel, -1, "", size=(50, -1))
#         self.figHeight_value.SetValue(str(self.config.figHeight))
#         self.figHeight_value.SetToolTip(wx.ToolTip("Set figure height (pixels)"))
#
#         figWidth_label = makeStaticText(panel, u"Width (2D)")
#         self.figWidth_value = wx.TextCtrl(panel, -1, "", size=(50, -1))
#         self.figWidth_value.SetValue(str(self.config.figWidth))
#         self.figWidth_value.SetToolTip(wx.ToolTip("Set figure width (pixels)"))
#
#         # bind
#         self.figHeight_value.Bind(wx.EVT_TEXT, self.onApply)
#         self.figWidth_value.Bind(wx.EVT_TEXT, self.onApply)
#         self.figHeight1D_value.Bind(wx.EVT_TEXT, self.onApply)
#         self.figWidth1D_value.Bind(wx.EVT_TEXT, self.onApply)
#
#         gridFigure = wx.GridBagSizer(2,2)
#         n = 0
#         gridFigure.Add(figHeight1D_label, (n,0))
#         gridFigure.Add(self.figHeight1D_value, (n,1))
#         gridFigure.Add(figWidth1D_label, (n,2))
#         gridFigure.Add(self.figWidth1D_value, (n,3))
#         n = n+1
#         gridFigure.Add(figHeight_label, (n,0))
#         gridFigure.Add(self.figHeight_value, (n,1))
#         gridFigure.Add(figWidth_label, (n,2))
#         gridFigure.Add(self.figWidth_value, (n,3))
#         figSizer.Add(gridFigure, 0, wx.EXPAND|wx.ALL, 2)
#         return figSizer

#     def makePlotSettingsSubPanel(self):
#         imageBox = makeStaticBox(panel, "Frame properties", (210,-1), wx.BLACK)
#         figSizer = wx.StaticBoxSizer(imageBox, wx.HORIZONTAL)
#
#         borderRight_label = makeStaticText(panel, u"Border\nright")
#         self.interactive_border_min_right = wx.SpinCtrlDouble(panel, wx.ID_ANY,
#                                                    value=str(self.config.interactive_border_min_right),min=0, max=100,
#                                                    initial=int(self.config.interactive_border_min_right),
#                                                    inc=5, size=(50,-1))
#         self.interactive_border_min_right.SetToolTip(wx.ToolTip("Set minimum border size (pixels)"))
#
#         borderLeft_label = makeStaticText(panel, u"Border\nleft")
#         self.interactive_border_min_left = wx.SpinCtrlDouble(panel, wx.ID_ANY,
#                                                    value=str(self.config.interactive_border_min_left),min=0, max=100,
#                                                    initial=int(self.config.interactive_border_min_left), inc=5, size=(50,-1))
#         self.interactive_border_min_left.SetToolTip(wx.ToolTip("Set minimum border size (pixels)"))
#
#         borderTop_label = makeStaticText(panel, u"Border\ntop")
#         self.interactive_border_min_top = wx.SpinCtrlDouble(panel, wx.ID_ANY,
#                                                    value=str(self.config.interactive_border_min_top),min=0, max=100,
#                                                    initial=int(self.config.interactive_border_min_top), inc=5, size=(50,-1))
#         self.interactive_border_min_top.SetToolTip(wx.ToolTip("Set minimum border size (pixels)"))
#
#         borderBottom_label = makeStaticText(panel, u"Border\nbottom")
#         self.interactive_border_min_bottom = wx.SpinCtrlDouble(panel, wx.ID_ANY,
#                                                    value=str(self.config.interactive_border_min_bottom),min=0, max=100,
#                                                    initial=int(self.config.interactive_border_min_bottom), inc=5, size=(50,-1))
#         self.interactive_border_min_bottom.SetToolTip(wx.ToolTip("Set minimum border size (pixels)"))
#
#         outlineWidth_label = makeStaticText(panel, u"Outline\nwidth")
#         self.interactive_outline_width = wx.SpinCtrlDouble(panel, wx.ID_ANY,
#                                                    value=str(self.config.interactive_outline_width),min=0, max=5,
#                                                    initial=self.config.interactive_outline_width, inc=0.5, size=(50,-1))
#         self.interactive_outline_width.SetToolTip(wx.ToolTip("Plot outline line thickness"))
#
#         outlineTransparency_label = makeStaticText(panel, u"Outline\nalpha")
#         self.interactive_outline_alpha = wx.SpinCtrlDouble(panel, wx.ID_ANY,
#                                                    value=str(self.config.interactive_outline_alpha),min=0, max=1,
#                                                    initial=self.config.interactive_outline_alpha, inc=0.05, size=(50,-1))
#         self.interactive_outline_alpha.SetToolTip(wx.ToolTip("Plot outline line transparency value"))
#
#         background_color_label= makeStaticText(panel, u"Background\ncolor")
#         self.interactive_background_colorBtn = wx.Button( self.propertiesView, ID_changeColorBackgroundInteractive,
#                                            u"", wx.DefaultPosition, wx.Size( 26, 26 ), 0 )
#         self.interactive_background_colorBtn.SetBackgroundColour(convertRGB1to255(self.config.interactive_background_color))
#
#         self.interactive_grid_line = wx.CheckBox(panel, -1 ,'Add', (15, 30))
#         self.interactive_grid_line.SetValue(self.config.interactive_grid_line)
#
#         grid_line_color_label= makeStaticText(panel, u"Grid lines")
#         self.interactive_grid_line_colorBtn = wx.Button( self.propertiesView, ID_changeColorGridLineInteractive,
#                                            u"", wx.DefaultPosition, wx.Size( 26, 26 ), 0 )
#         self.interactive_grid_line_colorBtn.SetBackgroundColour(convertRGB1to255(self.config.interactive_grid_line_color))
#
#         # bind
#         self.interactive_border_min_right.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
#         self.interactive_border_min_left.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
#         self.interactive_border_min_top.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
#         self.interactive_border_min_bottom.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
#         self.interactive_outline_width.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
#         self.interactive_outline_alpha.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
#         self.interactive_grid_line.Bind(wx.EVT_CHECKBOX, self.onApply)
#         self.interactive_background_colorBtn.Bind(wx.EVT_BUTTON, self.on_change_color, id=ID_changeColorBackgroundInteractive)
#         self.interactive_grid_line_colorBtn.Bind(wx.EVT_BUTTON, self.on_change_color, id=ID_changeColorGridLineInteractive)
#
#         gridFigure = wx.GridBagSizer(5,2)
#         n = 0
#         gridFigure.Add(borderRight_label, (n,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
#         gridFigure.Add(borderLeft_label, (n,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
#         gridFigure.Add(borderTop_label, (n,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
#         gridFigure.Add(borderBottom_label, (n,3), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
#         n = n+1
#         gridFigure.Add(self.interactive_border_min_right, (n,0))
#         gridFigure.Add(self.interactive_border_min_left, (n,1))
#         gridFigure.Add(self.interactive_border_min_top, (n,2))
#         gridFigure.Add(self.interactive_border_min_bottom, (n,3))
#         n = n+1
#         gridFigure.Add(outlineWidth_label, (n,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
#         gridFigure.Add(outlineTransparency_label, (n,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
#         gridFigure.Add(background_color_label, (n,2), (1, 2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
#         n = n+1
#         gridFigure.Add(self.interactive_outline_width, (n,0))
#         gridFigure.Add(self.interactive_outline_alpha, (n,1))
#         gridFigure.Add(self.interactive_background_colorBtn, (n,2), (1, 2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
#         n = n+1
#         gridFigure.Add(grid_line_color_label, (n,0), (1, 2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
#         n = n+1
#         gridFigure.Add(self.interactive_grid_line, (n,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
#         gridFigure.Add(self.interactive_grid_line_colorBtn, (n,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
#
#         figSizer.Add(gridFigure, 0, wx.EXPAND|wx.ALL, 2)
#         return figSizer

    def makeRMSDSubPanel(self, panel):
        rmsdBox = makeStaticBox(panel, "RMSD label properties", (200, -1), wx.BLACK)
        rmsdSizer = wx.StaticBoxSizer(rmsdBox, wx.HORIZONTAL)
        rmsdBox.SetToolTip(wx.ToolTip(""))

        notationFontSize = makeStaticText(panel, u"Label font size")
        self.notationSlider = wx.SpinCtrlDouble(panel, wx.ID_ANY,
                                             value=str(self.config.interactive_annotation_fontSize), min=8, max=32,
                                             initial=self.config.interactive_annotation_fontSize, inc=1, size=(50, -1))
        self.notationBoldCheck = makeCheckbox(panel, u"Bold")
        self.notationBoldCheck.SetValue(self.config.interactive_annotation_weight)

        interactive_annotation_color_label = makeStaticText(panel, u"Font")
        self.interactive_annotation_colorBtn = wx.Button(panel, ID_changeColorNotationInteractive,
                                           u"", wx.DefaultPosition, wx.Size(26, 26), 0)
        self.interactive_annotation_colorBtn.SetBackgroundColour(convertRGB1to255(self.config.interactive_annotation_color))

        interactive_annotation_background_color_label = makeStaticText(panel, u"Background")
        self.interactive_annotation_colorBackgroundBtn = wx.Button(panel, ID_changeColorBackgroundNotationInteractive,
                                                     u"", wx.DefaultPosition, wx.Size(26, 26), 0)
        self.interactive_annotation_colorBackgroundBtn.SetBackgroundColour(convertRGB1to255(self.config.interactive_annotation_background_color))

        interactive_transparency_label = makeStaticText(panel, u"Transparency")
        self.rmsd_label_transparency = wx.SpinCtrlDouble(panel, wx.ID_ANY,
                                                         value=str(self.config.interactive_annotation_alpha), min=0, max=1,
                                                         initial=self.config.interactive_annotation_alpha, inc=0.1, size=(50, -1))



        self.titleSlider.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        self.titleBoldCheck.Bind(wx.EVT_CHECKBOX, self.onApply)
        self.labelSlider.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        self.labelBoldCheck.Bind(wx.EVT_CHECKBOX, self.onApply)
        self.tickSlider.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        self.notationSlider.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        self.rmsd_label_transparency.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        self.notationBoldCheck.Bind(wx.EVT_CHECKBOX, self.onApply)
        self.interactive_annotation_colorBtn.Bind(wx.EVT_BUTTON, self.on_change_color, id=ID_changeColorNotationInteractive)
        self.interactive_annotation_colorBackgroundBtn.Bind(wx.EVT_BUTTON, self.on_change_color, id=ID_changeColorBackgroundNotationInteractive)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(notationFontSize, wx.GBPosition(n, 0), wx.GBSpan(1, 2), TEXT_STYLE_CV_R_L, 2)
        grid.Add(interactive_annotation_color_label, wx.GBPosition(n, 2), wx.GBSpan(1, 1), TEXT_STYLE_CV_R_L, 2)
        grid.Add(interactive_annotation_background_color_label, wx.GBPosition(n, 3), wx.GBSpan(1, 1), TEXT_STYLE_CV_R_L, 2)
        grid.Add(interactive_transparency_label, wx.GBPosition(n, 4), wx.GBSpan(1, 1), TEXT_STYLE_CV_R_L, 2)
        n = n + 1
        grid.Add(self.notationSlider, wx.GBPosition(n, 0), wx.GBSpan(1, 1), TEXT_STYLE_CV_R_L, 2)
        grid.Add(self.notationBoldCheck, wx.GBPosition(n, 1), wx.GBSpan(1, 1), TEXT_STYLE_CV_R_L, 2)
        grid.Add(self.interactive_annotation_colorBtn, wx.GBPosition(n, 2), wx.GBSpan(1, 1), TEXT_STYLE_CV_R_L, 2)
        grid.Add(self.interactive_annotation_colorBackgroundBtn, wx.GBPosition(n, 3), wx.GBSpan(1, 1), TEXT_STYLE_CV_R_L, 2)
        grid.Add(self.rmsd_label_transparency, wx.GBPosition(n, 4), wx.GBSpan(1, 1), TEXT_STYLE_CV_R_L, 2)

        rmsdSizer.Add(grid, 0, wx.EXPAND | wx.ALL, 2)
        return rmsdSizer

#     def makeInteractiveToolsSubPanel(self):
#         mainBox = makeStaticBox(panel, "Interactive tools", (240, -1), wx.BLACK)
#         toolsSizer = wx.StaticBoxSizer(mainBox, wx.HORIZONTAL)
#
#         font = wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD)
#
#         availableTools_label = wx.StaticText(panel, -1, "Available tools", style=TEXT_STYLE_CV_R_L)
#         availableTools_label.SetFont(font)
#         availableTools_label.SetForegroundColour((34, 139, 34))
#
#         plotType_label = wx.StaticText(panel, -1, "Toolset:", style=TEXT_STYLE_CV_R_L)
#         self.plotTypeToolsSelect_propView = wx.ComboBox(panel, -1, choices=[],
#                                                         style=wx.CB_READONLY)
#         msg = 'Name of the toolset. Select tools that you would like to add to toolset.'
#         tip = self.makeTooltip(text=msg, delay=500)
#         self.plotTypeToolsSelect_propView.SetToolTip(tip)
#         self.addPlotType = wx.Button(panel, wx.ID_ANY, size=(26, 26))
#         self.addPlotType.SetBitmap(self.icons.iconsLib['add16'])
#
#         self.hover_check = wx.CheckBox(panel, -1 , 'Hover', (15, 30))
#         self.save_check = wx.CheckBox(panel, -1 , 'Save', (15, 30))
#         self.pan_check = wx.CheckBox(panel, -1 , 'Pan', (15, 30))
#         self.boxZoom_check = wx.CheckBox(panel, -1 , 'Box Zoom', (15, 30))
#         self.boxZoom_horizontal_check = wx.CheckBox(panel, -1 , 'Box Zoom\n(horizontal)', (15, 30))
#         self.boxZoom_vertical_check = wx.CheckBox(panel, -1 , 'Box Zoom\n(vertical)', (15, 30))
#         self.crosshair_check = wx.CheckBox(panel, -1 , 'Crosshair', (15, 30))
#         self.reset_check = wx.CheckBox(panel, -1 , 'Reset', (15, 30))
#         self.wheel_check = wx.CheckBox(panel, -1 , 'Wheel', (15, 30))
#
# #         wheelZoom_label = wx.StaticText(panel, -1, "Wheel Zoom", style=TEXT_STYLE_CV_R_L)
#         self.wheelZoom_combo = wx.ComboBox(panel, -1, choices=self.config.interactive_wheelZoom_choices,
#                                           value='Wheel Zoom XY', style=wx.CB_READONLY)
#
#
#         location_label = wx.StaticText(panel, -1, "Toolbar position", style=TEXT_STYLE_CV_R_L)
#         self.location_combo = wx.ComboBox(panel, -1, choices=self.config.interactive_toolbarPosition_choices,
#                                           value=self.config.toolsLocation, style=wx.CB_READONLY)
#         self.location_combo.Disable()
#
#
#
#         availableActiveTools_label = wx.StaticText(panel, -1, "Active tools",
#                                                    style=TEXT_STYLE_CV_R_L)
#         availableActiveTools_label.SetFont(font)
#         availableActiveTools_label.SetForegroundColour((34, 139, 34))
#
#         drag_label = makeStaticText(panel, u"Active drag")
#         self.activeDrag_combo = wx.ComboBox(panel, -1,
#                                             choices=self.config.interactive_activeDragTools_choices,
#                                             value=self.config.activeDrag,
#                                             style=wx.CB_READONLY)
#         wheel_labe = makeStaticText(panel, u"Active wheel")
#         self.activeWheel_combo = wx.ComboBox(panel, -1,
#                                              choices=self.config.interactive_activeWheelTools_choices,
#                                              value=self.config.activeWheel,
#                                              style=wx.CB_READONLY)
#         inspect_label = makeStaticText(panel, u"Active inspect")
#         self.activeInspect_combo = wx.ComboBox(panel, -1,
#                                               choices=self.config.interactive_activeHoverTools_choices,
#                                               value=self.config.activeInspect,
#                                               style=wx.CB_READONLY)
#
#         # bind
#         self.hover_check.Bind(wx.EVT_CHECKBOX, self.onSelectTools)
#         self.save_check.Bind(wx.EVT_CHECKBOX, self.onSelectTools)
#         self.pan_check.Bind(wx.EVT_CHECKBOX, self.onSelectTools)
#         self.boxZoom_check.Bind(wx.EVT_CHECKBOX, self.onSelectTools)
#         self.boxZoom_horizontal_check.Bind(wx.EVT_CHECKBOX, self.onSelectTools)
#         self.boxZoom_vertical_check.Bind(wx.EVT_CHECKBOX, self.onSelectTools)
#         self.crosshair_check.Bind(wx.EVT_CHECKBOX, self.onSelectTools)
#         self.reset_check.Bind(wx.EVT_CHECKBOX, self.onSelectTools)
#         self.wheel_check.Bind(wx.EVT_CHECKBOX, self.onSelectTools)
#         self.location_combo.Bind(wx.EVT_COMBOBOX, self.onApply)
#         self.wheelZoom_combo.Bind(wx.EVT_COMBOBOX, self.onSelectTools)
#         self.plotTypeToolsSelect_propView.Bind(wx.EVT_COMBOBOX, self.onSetupTools)
#
#         self.activeDrag_combo.Bind(wx.EVT_COMBOBOX, self.onSelectTools)
#         self.activeWheel_combo.Bind(wx.EVT_COMBOBOX, self.onSelectTools)
#         self.activeInspect_combo.Bind(wx.EVT_COMBOBOX, self.onSelectTools)
#
# #         self.addPlotType.Bind(wx.EVT_BUTTON, self.onAddToolSet)
#
#
#         if self.wheel_check.GetValue(): self.wheelZoom_combo.Enable()
#         else: self.wheelZoom_combo.Disable()
#
#         gridTools = wx.GridBagSizer(2, 5)
#         n = 0
#         gridTools.Add(availableTools_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL)
#         n = n + 1
#         gridTools.Add(plotType_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL)
#         gridTools.Add(self.plotTypeToolsSelect_propView, (n, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
#         gridTools.Add(self.addPlotType, (n, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
#         n = n + 1
#         gridTools.Add(self.hover_check, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL)
#         gridTools.Add(self.save_check, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
#         n = n + 1
#         gridTools.Add(self.pan_check, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL)
#         gridTools.Add(self.boxZoom_check, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
#         n = n + 1
#         gridTools.Add(self.boxZoom_horizontal_check, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL)
#         gridTools.Add(self.boxZoom_vertical_check, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
#         n = n + 1
#         gridTools.Add(self.crosshair_check, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL)
#         gridTools.Add(self.reset_check, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
#         n = n + 1
#         gridTools.Add(self.wheel_check, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL)
#         gridTools.Add(self.wheelZoom_combo, (n, 1), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER_VERTICAL)
#         n = n + 1
#         gridTools.Add(location_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL)
#         gridTools.Add(self.location_combo, (n, 1), wx.GBSpan(1, 2))
#         n = n + 1
#         gridTools.Add(availableActiveTools_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL)
#         n = n + 1
#         gridTools.Add(drag_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL)
#         gridTools.Add(self.activeDrag_combo, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
#         n = n + 1
#         gridTools.Add(wheel_labe, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL)
#         gridTools.Add(self.activeWheel_combo, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
#         n = n + 1
#         gridTools.Add(inspect_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL)
#         gridTools.Add(self.activeInspect_combo, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
#
#         toolsSizer.Add(gridTools, 0, wx.ALIGN_CENTER | wx.ALL, 5)
#
#         return toolsSizer

    def make1DplotSubPanel(self, panel):
        mainBox = makeStaticBox(panel, "Plot (1D) properties", (230, -1), wx.BLACK)
        figSizer = wx.StaticBoxSizer(mainBox, wx.HORIZONTAL)

        lineWidth_label = makeStaticText(panel, u"Line width:")
        self.line_width = wx.SpinCtrlDouble(panel, wx.ID_ANY,
                                                         value=str(self.config.interactive_line_width), min=0.5, max=10,
                                                         initial=self.config.interactive_line_width, inc=0.5, size=(50, -1))
        self.line_width.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)

        lineAlpha_label = makeStaticText(panel, u"Transparency:")
        self.line_transparency = wx.SpinCtrlDouble(panel, wx.ID_ANY,
                                                   value=str(self.config.interactive_line_alpha), min=0, max=1,
                                                   initial=self.config.interactive_line_alpha, inc=0.1, size=(50, -1))
        self.line_transparency.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)

        lineStyle_label = wx.StaticText(panel, -1, "Line style:")
        self.line_style = wx.ComboBox(panel, -1, choices=self.config.interactive_line_style_choices,
                                                  value="", style=wx.CB_READONLY)
        self.line_style.SetStringSelection(self.config.interactive_line_style)
        self.line_style.Bind(wx.EVT_COMBOBOX, self.onApply)

        self.hoverVlineCheck = wx.CheckBox(panel, -1 , u'Link hover to X axis', (15, 30))
        self.hoverVlineCheck.SetToolTip(wx.ToolTip("Hover tool information is linked to the X-axis"))
        self.hoverVlineCheck.SetValue(self.config.hoverVline)
        self.hoverVlineCheck.Bind(wx.EVT_CHECKBOX, self.onApply)

        gridFigure = wx.GridBagSizer(2, 2)
        n = 0
        gridFigure.Add(lineWidth_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        gridFigure.Add(self.line_width, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        gridFigure.Add(lineAlpha_label, (n, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        gridFigure.Add(self.line_transparency, (n, 3), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n = n + 1
        gridFigure.Add(lineStyle_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        gridFigure.Add(self.line_style, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        gridFigure.Add(self.hoverVlineCheck, (n, 2), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER_VERTICAL)


        figSizer.Add(gridFigure, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        return figSizer

    def makeOverLaySubPanel(self, panel):
        mainBox = makeStaticBox(panel, "Overlay plot properties", (230, -1), wx.BLACK)
        figSizer = wx.StaticBoxSizer(mainBox, wx.HORIZONTAL)

        layout_label = makeStaticText(panel, u"Layout")
        self.layout_combo = wx.ComboBox(panel, -1, choices=['Rows', 'Columns'],
                                        value=self.config.plotLayoutOverlay, style=wx.CB_READONLY)
        self.layout_combo.SetToolTip(wx.ToolTip("Select type of layout for the 2D overlay plots. The HTML viewer does not allow a good enough overlay function, so column/row option is provided. Default: Rows"))

        self.XYaxisLinkCheck = wx.CheckBox(panel, -1 , u'Link XY axes', (15, 30))
        self.XYaxisLinkCheck.SetValue(self.config.linkXYaxes)

        # bind
        self.layout_combo.Bind(wx.EVT_COMBOBOX, self.onApply)
        self.XYaxisLinkCheck.Bind(wx.EVT_CHECKBOX, self.onApply)

        gridFigure = wx.GridBagSizer(2, 2)
        n = 0
        gridFigure.Add(layout_label, (n, 0), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        gridFigure.Add(self.layout_combo, (n, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        gridFigure.Add(self.XYaxisLinkCheck, (n, 2), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)

        figSizer.Add(gridFigure, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        return figSizer

    def makeBarSubPanel(self, panel):
        mainBox = makeStaticBox(panel, "Plot (bar) properties", (230, -1), wx.BLACK)
        figSizer = wx.StaticBoxSizer(mainBox, wx.HORIZONTAL)

        bar_width_label = wx.StaticText(panel, -1, "Bar width:")
        self.bar_width_value = wx.SpinCtrlDouble(panel, -1,
                                               value=str(self.config.bar_width),
                                               min=0.01, max=10, inc=0.05,
                                               initial=self.config.bar_width,
                                               size=(50, -1))
        self.bar_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)

        bar_alpha_label = wx.StaticText(panel, -1, "transparency:")
        self.bar_alpha_value = wx.SpinCtrlDouble(panel, -1,
                                                    value=str(self.config.bar_alpha),
                                                    min=0, max=1, initial=self.config.bar_alpha,
                                                    inc=0.25, size=(50, -1))
        self.bar_alpha_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)

        bar_lineWidth_label = wx.StaticText(panel, -1, "Line width:")
        self.bar_lineWidth_value = wx.SpinCtrlDouble(panel, -1,
                                                    value=str(self.config.bar_lineWidth),
                                                    min=0, max=5, initial=self.config.bar_lineWidth,
                                                    inc=1, size=(50, -1))
        self.bar_lineWidth_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)

        bar_edgeColor_label = wx.StaticText(panel, -1, "Edge color:")
        self.bar_edgeColorBtn = wx.Button(panel, ID_interactivePanel_color_barEdge,
                                              u"", wx.DefaultPosition,
                                              wx.Size(26, 26), 0)
        self.bar_edgeColorBtn.SetBackgroundColour(convertRGB1to255(self.config.bar_edge_color))
        self.bar_edgeColorBtn.Bind(wx.EVT_BUTTON, self.on_change_color)

        self.bar_colorEdge_check = makeCheckbox(panel, u"Same as fill")
        self.bar_colorEdge_check.SetValue(self.config.bar_sameAsFill)
        self.bar_colorEdge_check.Bind(wx.EVT_CHECKBOX, self.onApply)

        bar_grid = wx.GridBagSizer(2, 2)
        n = 0
        bar_grid.Add(bar_width_label, (n, 0), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        bar_grid.Add(bar_alpha_label, (n, 1), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        bar_grid.Add(bar_lineWidth_label, (n, 2), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        bar_grid.Add(self.bar_width_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        bar_grid.Add(self.bar_alpha_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        bar_grid.Add(self.bar_lineWidth_value, (n, 2), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        bar_grid.Add(bar_edgeColor_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        bar_grid.Add(self.bar_edgeColorBtn, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        bar_grid.Add(self.bar_colorEdge_check, (n, 2), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)

        figSizer.Add(bar_grid, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        return figSizer

    def makeScatterSubPanel(self, panel):
        mainBox = makeStaticBox(panel, "Plot (scatter) properties", (230, -1), wx.BLACK)
        figSizer = wx.StaticBoxSizer(mainBox, wx.HORIZONTAL)

        marker_label = makeStaticText(panel, u"Marker shape")
        self.scatter_marker = wx.ComboBox(panel, -1,
                                        choices=self.config.interactive_scatter_marker_choices,
                                          value=self.config.interactive_scatter_marker, style=wx.CB_READONLY)
        self.scatter_marker.Bind(wx.EVT_COMBOBOX, self.onApply)

        marker_size_label = makeStaticText(panel, u"Marker size:")
        self.scatter_marker_size = wx.SpinCtrlDouble(panel, wx.ID_ANY,
                                                     value=str(self.config.interactive_scatter_size), min=1, max=100,
                                                     initial=self.config.interactive_scatter_size, inc=5, size=(50, -1))
        self.scatter_marker_size.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)

        marker_alpha_label = makeStaticText(panel, u"transparency:")
        self.scatter_marker_alpha = wx.SpinCtrlDouble(panel, wx.ID_ANY,
                                                     value=str(self.config.interactive_scatter_alpha), min=0, max=1,
                                                     initial=self.config.interactive_scatter_alpha, inc=0.1, size=(50, -1))
        self.scatter_marker_alpha.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)

        marker_color_label = makeStaticText(panel, u"Edge color:")
        self.scatter_marker_edge_colorBtn = wx.Button(panel, ID_interactivePanel_color_markerEdge,
                                                  u"", wx.DefaultPosition, wx.Size(26, 26), 0)
        self.scatter_marker_edge_colorBtn.SetBackgroundColour(convertRGB1to255(self.config.interactive_scatter_edge_color))
        self.scatter_marker_edge_colorBtn.Bind(wx.EVT_BUTTON, self.on_change_color, id=ID_interactivePanel_color_markerEdge)

        self.scatter_color_sameAsFill = wx.CheckBox(panel, -1 , u'Same as fill', (15, 30))
        self.scatter_color_sameAsFill.SetValue(self.config.interactive_scatter_sameAsFill)
        self.scatter_color_sameAsFill.Bind(wx.EVT_CHECKBOX, self.onApply)

        gridFigure = wx.GridBagSizer(2, 2)
        n = 0
        gridFigure.Add(marker_label, (n, 0), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        gridFigure.Add(self.scatter_marker, (n, 1), (1, 2), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        gridFigure.Add(marker_size_label, (n, 0), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        gridFigure.Add(marker_alpha_label, (n, 1), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        gridFigure.Add(self.scatter_marker_size, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        gridFigure.Add(self.scatter_marker_alpha, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        gridFigure.Add(marker_color_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        gridFigure.Add(self.scatter_marker_edge_colorBtn, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        gridFigure.Add(self.scatter_color_sameAsFill, (n, 2), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)

        figSizer.Add(gridFigure, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        return figSizer

    def makeCustomJSSubPanel(self, panel):
        mainBox = makeStaticBox(panel, "Custom JavaScript", (230, -1), wx.BLACK)
        figSizer = wx.StaticBoxSizer(mainBox, wx.HORIZONTAL)

        self.custom_js_events = wx.CheckBox(panel, -1 , u'Add custom JS events when available', (15, 30))
        self.custom_js_events.SetToolTip(wx.ToolTip("When checked, custom JavaScripts will be added to the plot to enable better operation (i.e. double-tap in plot area will restore original state of the plot)"))
        self.custom_js_events.SetValue(self.config.interactive_custom_events)
        self.custom_js_events.Bind(wx.EVT_CHECKBOX, self.onApply)

        self.custom_js_scripts = wx.CheckBox(panel, -1 , u'Add custom JS scripts when available', (15, 30))
        self.custom_js_scripts.SetToolTip(wx.ToolTip("When checked, custom JavaScript code snippets will be execute when triggered (i.e. toggle button to show/hide legend)"))
        self.custom_js_scripts.SetValue(self.config.interactive_custom_scripts)
        self.custom_js_scripts.Bind(wx.EVT_CHECKBOX, self.onApply)

        position_label = makeStaticText(panel, u"Widget position")
        self.custom_js_position = wx.ComboBox(panel, -1,
                                               choices=["left", "right", "bottom_row", "bottom_column", "top_row", "top_column"],
                                               value="right", style=wx.CB_READONLY)
        self.custom_js_position.SetStringSelection(self.config.interactive_custom_position)

        gridAnnot = wx.GridBagSizer(2, 2)
        y = 0
        gridAnnot.Add(self.custom_js_events, (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        gridAnnot.Add(self.custom_js_scripts, (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        gridAnnot.Add(position_label, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        gridAnnot.Add(self.custom_js_position, (y, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)

        figSizer.Add(gridAnnot, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        return figSizer

    def makeAnnotationSubPanel(self, panel):
        mainBox = makeStaticBox(panel, "Annotation properties", (230, -1), wx.BLACK)
        figSizer = wx.StaticBoxSizer(mainBox, wx.HORIZONTAL)

        self.annot_peakLabel = wx.CheckBox(panel, -1 , u'Label peak', (15, 30))
        self.annot_peakLabel.SetValue(self.config.interactive_ms_annotations_labels)
        self.annot_peakLabel.Bind(wx.EVT_CHECKBOX, self.onApply)

        self.annot_peakHighlight = wx.CheckBox(panel, -1 , u'Highlight peak', (15, 30))
        self.annot_peakHighlight.SetValue(self.config.interactive_ms_annotations_highlight)
        self.annot_peakHighlight.Bind(wx.EVT_CHECKBOX, self.onApply)

        annot_xpos_label = makeStaticText(panel, u"Offset X:")
        self.annot_xpos_value = wx.SpinCtrlDouble(panel, wx.ID_ANY,
                                                  value=str(self.config.interactive_ms_annotations_offsetX), min=-100, max=100,
                                                  initial=self.config.interactive_ms_annotations_offsetX, inc=5, size=(50, -1))
        self.annot_xpos_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)

        annot_ypos_label = makeStaticText(panel, u"Offset Y:")
        self.annot_ypos_value = wx.SpinCtrlDouble(panel, wx.ID_ANY,
                                                  value=str(self.config.interactive_ms_annotations_offsetY), min=-100, max=100,
                                                  initial=self.config.interactive_ms_annotations_offsetY, inc=5, size=(50, -1))
        self.annot_ypos_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)

        annot_rotation_label = makeStaticText(panel, u"Rotation:")
        self.annot_rotation_value = wx.SpinCtrlDouble(panel, wx.ID_ANY,
                                                  value=str(self.config.interactive_ms_annotations_rotation), min=0, max=180,
                                                  initial=self.config.interactive_ms_annotations_rotation, inc=45, size=(50, -1))
        self.annot_rotation_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)

        annot_fontSize_label = makeStaticText(panel, u"Font size:")
        self.annot_fontSize_value = wx.SpinCtrlDouble(panel, wx.ID_ANY,
                                                      value=str(self.config.interactive_ms_annotations_fontSize), min=0, max=32,
                                                      initial=self.config.interactive_ms_annotations_fontSize, inc=2, size=(50, -1))
        self.annot_fontSize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)

        self.annot_fontWeight_value = makeCheckbox(panel, u"Bold")
        self.annot_fontWeight_value.SetValue(self.config.interactive_ms_annotations_fontWeight)
        self.annot_fontWeight_value.Bind(wx.EVT_CHECKBOX, self.onApply)

        annot_fontColor_label = makeStaticText(panel, u"Color:")
        self.annot_fontColor_colorBtn = wx.Button(panel, ID_changeColorAnnotLabelInteractive,
                                                  u"", wx.DefaultPosition, wx.Size(26, 26), 0)
        self.annot_fontColor_colorBtn.SetBackgroundColour(convertRGB1to255(self.config.interactive_ms_annotations_label_color))
        self.annot_fontColor_colorBtn.Bind(wx.EVT_BUTTON, self.on_change_color, id=ID_changeColorAnnotLabelInteractive)


        gridAnnot = wx.GridBagSizer(2, 2)
        y = 0
        gridAnnot.Add(self.annot_peakLabel, (y, 0), wx.GBSpan(1, 2), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        gridAnnot.Add(self.annot_peakHighlight, (y, 2), wx.GBSpan(1, 2), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        gridAnnot.Add(annot_xpos_label, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        gridAnnot.Add(annot_ypos_label, (y, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        gridAnnot.Add(annot_rotation_label, (y, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        gridAnnot.Add(annot_fontSize_label, (y, 3), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        gridAnnot.Add(annot_fontColor_label, (y, 4), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        y = y + 1
        gridAnnot.Add(self.annot_xpos_value, (y, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        gridAnnot.Add(self.annot_ypos_value, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        gridAnnot.Add(self.annot_rotation_value, (y, 2), wx.GBSpan(1, 1), flag=wx.EXPAND)
        gridAnnot.Add(self.annot_fontSize_value, (y, 3), wx.GBSpan(1, 1), flag=wx.EXPAND)
        gridAnnot.Add(self.annot_fontWeight_value, (y, 4), wx.GBSpan(1, 1), flag=wx.EXPAND)
        gridAnnot.Add(self.annot_fontColor_colorBtn, (y, 5), wx.GBSpan(1, 1), flag=wx.EXPAND)

        figSizer.Add(gridAnnot, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        return figSizer

    def makeColorbarSubPanel(self, panel):
        mainBox = makeStaticBox(panel, "Colorbar properties", (230, -1), wx.BLACK)
        figSizer = wx.StaticBoxSizer(mainBox, wx.HORIZONTAL)

        colorbar_label = makeStaticText(panel, u"Colorbar:")
        self.interactive_colorbar = wx.CheckBox(panel, -1 , u'', (15, 30))
        self.interactive_colorbar.SetValue(self.config.interactive_colorbar)
        self.interactive_colorbar.Bind(wx.EVT_CHECKBOX, self.onApply)

        precision_label = makeStaticText(panel, u"Precision")
        self.interactive_colorbar_precision = wx.SpinCtrlDouble(panel, wx.ID_ANY,
                                                   value=str(self.config.interactive_colorbar_precision), min=0, max=5,
                                                   initial=self.config.interactive_colorbar_precision, inc=1, size=(50, -1))
        self.interactive_colorbar_precision.SetToolTip(wx.ToolTip("Number of decimal places in the colorbar tickers"))

        self.interactive_colorbar_useScientific = wx.CheckBox(panel, -1 , u'Scientific\nnotation', (15, 30))
        self.interactive_colorbar_useScientific.SetValue(self.config.interactive_colorbar_useScientific)
        self.interactive_colorbar_useScientific.SetToolTip(wx.ToolTip("Enable/disable scientific notation of colorbar tickers"))
        self.interactive_colorbar_useScientific.Bind(wx.EVT_CHECKBOX, self.onEnableDisableItems)

        labelOffset_label = makeStaticText(panel, u"Label offset:")
        self.interactive_colorbar_label_offset = wx.SpinCtrlDouble(panel, wx.ID_ANY,
                                                   value=str(self.config.interactive_colorbar_label_offset), min=0, max=100,
                                                   initial=self.config.interactive_colorbar_label_offset, inc=5, size=(50, -1))
        self.interactive_colorbar_label_offset.SetToolTip(wx.ToolTip("Distance between the colorbar and labels"))

        location_label = makeStaticText(panel, u"Position:")
        self.interactive_colorbar_location = wx.ComboBox(panel, -1,
                                            choices=self.config.interactive_colorbarPosition_choices,
                                            value=self.config.interactive_colorbar_location, style=wx.CB_READONLY)
        self.interactive_colorbar_location.SetToolTip(wx.ToolTip("Colorbar position next to the plot. The colorbar orientation changes automatically"))

        offsetX_label = makeStaticText(panel, u"Offset X")
        self.interactive_colorbar_offset_x = wx.SpinCtrlDouble(panel, wx.ID_ANY,
                                                   value=str(self.config.interactive_colorbar_offset_x), min=0, max=100,
                                                   initial=self.config.interactive_colorbar_offset_x, inc=5, size=(50, -1))
        self.interactive_colorbar_offset_x.SetToolTip(wx.ToolTip("Colorbar position offset in the X axis. Adjust if colorbar is too close or too far away from the plot"))

        offsetY_label = makeStaticText(panel, u"Offset Y")
        self.interactive_colorbar_offset_y = wx.SpinCtrlDouble(panel, wx.ID_ANY,
                                                   value=str(self.config.interactive_colorbar_offset_y), min=0, max=100,
                                                   initial=self.config.interactive_colorbar_offset_y, inc=5, size=(50, -1))
        self.interactive_colorbar_offset_y.SetToolTip(wx.ToolTip("Colorbar position offset in the Y axis. Adjust if colorbar is too close or too far away from the plot"))

        padding_label = makeStaticText(panel, u"Pad")
        self.colorbarPadding = wx.SpinCtrlDouble(panel, wx.ID_ANY,
                                                   value=str(self.config.interactive_colorbar_padding), min=0, max=100,
                                                   initial=self.config.interactive_colorbar_padding, inc=5, size=(50, -1))
        self.colorbarPadding.SetToolTip(wx.ToolTip(""))

        margin_label = makeStaticText(panel, u"Width")
        self.colorbarWidth = wx.SpinCtrlDouble(panel, wx.ID_ANY,
                                                   value=str(self.config.interactive_colorbar_width), min=0, max=100,
                                                   initial=self.config.interactive_colorbar_width, inc=5, size=(50, -1))
        self.colorbarWidth.SetToolTip(wx.ToolTip(""))


        # bind
        self.interactive_colorbar_precision.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        self.interactive_colorbar_useScientific.Bind(wx.EVT_CHECKBOX, self.onApply)
        self.interactive_colorbar_location.Bind(wx.EVT_COMBOBOX, self.onApply)
        self.interactive_colorbar_offset_x.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        self.interactive_colorbar_offset_y.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        self.colorbarPadding.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        self.colorbarWidth.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        self.interactive_colorbar_label_offset.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)

        gridFigure = wx.GridBagSizer(2, 2)
        n = 0
        gridFigure.Add(colorbar_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        gridFigure.Add(self.interactive_colorbar, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        gridFigure.Add(precision_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        gridFigure.Add(self.interactive_colorbar_precision, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        gridFigure.Add(self.interactive_colorbar_useScientific, (n, 2), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        gridFigure.Add(labelOffset_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        gridFigure.Add(self.interactive_colorbar_label_offset, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        gridFigure.Add(location_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        gridFigure.Add(offsetX_label, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        gridFigure.Add(offsetY_label, (n, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        gridFigure.Add(padding_label, (n, 3), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        gridFigure.Add(margin_label, (n, 4), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        n = n + 1
        gridFigure.Add(self.interactive_colorbar_location, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        gridFigure.Add(self.interactive_colorbar_offset_x, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        gridFigure.Add(self.interactive_colorbar_offset_y, (n, 2), flag=wx.ALIGN_CENTER_VERTICAL)
        gridFigure.Add(self.colorbarPadding, (n, 3), flag=wx.ALIGN_CENTER_VERTICAL)
        gridFigure.Add(self.colorbarWidth, (n, 4), flag=wx.ALIGN_CENTER_VERTICAL)

        figSizer.Add(gridFigure, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        return figSizer

    def makeLegendSubPanel(self, panel):
        mainBox = makeStaticBox(panel, "Legend properties", (210,-1), wx.BLACK)
        figSizer = wx.StaticBoxSizer(mainBox, wx.HORIZONTAL)

        legend_label = makeStaticText(panel, u"Legend:")
        self.legend_legend = wx.CheckBox(panel, -1 ,u'', (15, 30))
        self.legend_legend.SetValue(self.config.interactive_legend)
        self.legend_legend.Bind(wx.EVT_CHECKBOX, self.onApply)

        position_label = makeStaticText(panel, u"Position")
        self.legend_position = wx.ComboBox(panel, -1,
                                           choices=self.config.interactive_legend_location_choices,
                                           value=self.config.interactive_legend_location, style=wx.CB_READONLY)
        self.legend_position.Bind(wx.EVT_COMBOBOX, self.onApply)

        orientation_label = makeStaticText(panel, u"Orientation")
        self.legend_orientation = wx.ComboBox(panel, -1,
                                               choices=self.config.interactive_legend_orientation_choices,
                                               value=self.config.interactive_legend_orientation, style=wx.CB_READONLY)
        self.legend_orientation.Bind(wx.EVT_COMBOBOX, self.onApply)

        legendAlpha_label = makeStaticText(panel, u"Legend transparency")
        self.legend_transparency = wx.SpinCtrlDouble(panel, wx.ID_ANY,
                                                     value=str(self.config.interactive_legend_background_alpha),min=0, max=1,
                                                     initial=self.config.interactive_legend_background_alpha, inc=0.1, size=(50,-1))
        self.legend_transparency.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)

        fontSize_label = makeStaticText(panel, u"Font size")
        self.legend_fontSize = wx.SpinCtrlDouble(panel, wx.ID_ANY,
                                                 value=str(self.config.interactive_legend_font_size),min=0, max=32,
                                                 initial=self.config.interactive_legend_font_size, inc=2, size=(50,-1))
        self.legend_fontSize.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)

        action_label = makeStaticText(panel, u"Action")
        self.legend_click_policy = wx.ComboBox(panel, -1,
                                               choices=self.config.interactive_legend_click_policy_choices,
                                               value=self.config.interactive_legend_click_policy, style=wx.CB_READONLY)
        self.legend_click_policy.Bind(wx.EVT_COMBOBOX, self.onApply)
        self.legend_click_policy.Bind(wx.EVT_COMBOBOX, self.onEnableDisableItems)

        muteAlpha_label = makeStaticText(panel, u"Line transparency")
        self.legend_mute_transparency = wx.SpinCtrlDouble(panel, wx.ID_ANY,
                                                   value=str(self.config.interactive_legend_mute_alpha),min=0, max=1,
                                                   initial=self.config.interactive_legend_mute_alpha, inc=0.1, size=(50,-1))
        self.legend_mute_transparency.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)


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

    def onColumnRightClickMenu(self, evt):
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_interactivePanel_table_document)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_interactivePanel_table_type)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_interactivePanel_table_file)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_interactivePanel_table_title)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_interactivePanel_table_header)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_interactivePanel_table_footnote)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_interactivePanel_table_colormap)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_interactivePanel_table_page)
#         self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_interactivePanel_table_tools)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_interactivePanel_table_order)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_ionPanel_table_label)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_ionPanel_table_method)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_interactivePanel_table_hideAll)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_interactivePanel_table_restoreAll)


        menu = wx.Menu()
        n = 1
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

    def onEvents(self, evt=None, evt_on=True):
        if evt_on:
            self.Bind(wx.EVT_CHAR_HOOK, self.OnKey)
        else:
            self.Unbind(wx.EVT_CHAR_HOOK, id=wx.ID_ANY)

    def onStartEditingItem(self, evt):
        self.Unbind(wx.EVT_CHAR_HOOK, id=wx.ID_ANY)

        self.currentItem = evt.m_itemIndex
        self.onItemSelected(evt)

    def onFinishEditingItem(self, evt):
        """
        Modify information after finished editing in the table
        """

        title = self.itemsList.GetItem(self.currentItem, self.config.interactiveColNames['title']).GetText()
        order = self.itemsList.GetItem(self.currentItem, self.config.interactiveColNames['order']).GetText()

        self.itemName_value.SetValue(title)
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

        if evt != None:
            evt.Skip()

    def onClearPages(self, evt):

        dlg = dialogs.dlgBox(exceptionTitle='Are you sure?',
                             exceptionMsg= "Are you sure you want to remove all pages?\nThis action is irreversible!",
                             type="Question")
        if dlg == wx.ID_NO:
            self.presenter.onThreading(evt, ("Cancelled operation", 4, 3), action='updateStatusbar')
            return

        pages = self.pageLayoutSelect_propView.GetItems()
        for page in pages:
            if page not in ["None", "Rows", "Columns"]:
                del self.config.pageDict[page]

        # Clear list
        self.pageLayoutSelect_htmlView.Clear()
        self.pageLayoutSelect_propView.Clear()
        self.pageLayoutSelect_toolbar.Clear()

        # Append new list
        sorted_page_list = natsorted(self.config.pageDict.keys())
        self.pageLayoutSelect_htmlView.AppendItems(sorted_page_list)
        self.pageLayoutSelect_propView.AppendItems(sorted_page_list)
        self.pageLayoutSelect_toolbar.AppendItems(sorted_page_list)

        # Preset
        self.pageLayoutSelect_propView.SetStringSelection("None")
        self.pageLayoutSelect_toolbar.SetStringSelection("None")

    def onRemovePage(self, evt):
        page_name = self.pageLayoutSelect_propView.GetStringSelection()
        if page_name in ["None", "Rows", "Columns", ""]:
            self.presenter.onThreading(None, ("Cannot remove '{}' page. Operation was cancelled".format(page_name), 4), action='updateStatusbar')
            return

        del self.config.pageDict[page_name]

        # Clear list
        self.pageLayoutSelect_htmlView.Clear()
        self.pageLayoutSelect_propView.Clear()
        self.pageLayoutSelect_toolbar.Clear()

        # Append new list
        sorted_page_list = natsorted(self.config.pageDict.keys())
        self.pageLayoutSelect_htmlView.AppendItems(sorted_page_list)
        self.pageLayoutSelect_propView.AppendItems(sorted_page_list)
        self.pageLayoutSelect_toolbar.AppendItems(sorted_page_list)

        # Preset
        self.pageLayoutSelect_toolbar.SetStringSelection("None")

    def onAddPage(self, evt):
        pageName = dialogs.dlgAsk('Please select page name.', defaultValue='')
        if pageName in ['', False]:
            self.presenter.onThreading(None, ("Incorrect name. Operation was cancelled", 4), action='updateStatusbar')
            return
        elif pageName == 'None':
                msg = 'This name is reserved. Please try again.'
                dialogs.dlgBox(exceptionTitle='Incorrect name',
                               exceptionMsg=msg,
                               type="Error")
                return

        # If page name is correct, we can add it to the combo boxes
        self.config.pageDict[pageName] = {'layout':'Individual',
                                          'rows':None, 'columns':None,
                                          'name':pageName, 'grid_share_tools':True,
                                          'header':"", "footnote":""}

        self.pageLayoutSelect_propView.Append(pageName)
        self.pageLayoutSelect_htmlView.Append(pageName)
        self.pageLayoutSelect_toolbar.Append(pageName)

        self.onChangePage(preset=pageName, evt=None)

#     def onAddToolSet(self, evt):
#         toolName = dialogs.dlgAsk('Please select ToolSet name.', defaultValue='')
#         if toolName in ['', False]:
#             self.presenter.onThreading(None, ("Operation was cancelled", 4), action='updateStatusbar')
#             return
#         elif toolName == '1D' or toolName == '2D' or toolName == 'Overlay':
#                 msg = "'%s' name is reserved. Please try again." % (toolName)
#                 dialogs.dlgBox(exceptionTitle='Incorrect name',
#                                exceptionMsg=msg,
#                                type="Error")
#                 return
#
#         # Add new toolset to dictionary
#         self.config.interactiveToolsOnOff[toolName] = {'hover':False, 'save':True, 'pan':False,
#                                                        'boxzoom':False, 'crosshair':False,
#                                                        'boxzoom_horizontal':True,
#                                                        'boxzoom_vertical':False,
#                                                         'reset':True, 'resize':False,
#                                                         'wheel':False, 'wheelType':'Wheel Zoom X',
#                                                         'activeDrag':'None',
#                                                         'activeWheel':'None',
#                                                         'activeInspect':'None'}
        # Add to combo boxes
#         self.plotTypeToolsSelect_htmlView.Append(toolName)
#         self.plotTypeToolsSelect_propView.Append(toolName)
#         self.plotTypeToolsSelect_toolbar.Append(toolName)

#         self.onSetupTools(preset=toolName, evt=None)


#         if evt != None:
#             evt.Skip()

    def onChangePage(self, evt, preset=None):
        """
        This function changes the values shown in the GUI for the selected page
        -----------
        @param preset: name of the new page
        """

        if preset != None:
            self.pageLayoutSelect_propView.SetStringSelection(preset)

        selectedItem = self.pageLayoutSelect_propView.GetStringSelection()

        colValue = str(self.config.pageDict[selectedItem].get('columns', ""))
        shareTools = self.config.pageDict[selectedItem].get('grid_share_tools', True)
        title = self.config.pageDict[selectedItem].get('title', selectedItem)
        header = self.config.pageDict[selectedItem].get('header', "")
        footnote = self.config.pageDict[selectedItem].get('footnote', "")
        plot_width = str(self.config.pageDict[selectedItem].get('grid_plot_width', 400))
        plot_height = str(self.config.pageDict[selectedItem].get('grid_plot_height', 500))
        addCustomJSWidgets = self.config.pageDict[selectedItem].get('add_js_widgets', False)


        self.layoutDoc_combo.SetStringSelection(self.config.pageDict[selectedItem].get('layout', 'Individual'))
        self.columns_value.SetValue(colValue)
        self.grid_shared_tools.SetValue(shareTools)
        self.pageTitle_value.SetValue(title)
        self.pageHeader_value.SetValue(header)
        self.pageFootnote_value.SetValue(footnote)
        self.grid_width_value.SetValue(plot_width)
        self.grid_height_value.SetValue(plot_height)
        self.grid_add_custom_js_widgets.SetValue(addCustomJSWidgets)
        self.onSelectPageProperties(evt=None)

    def onSelectPageProperties(self, evt):

        selectedItem = self.pageLayoutSelect_propView.GetStringSelection()
        # Enable/Disable row/column boxes
        if selectedItem == 'None':
            self.columns_value.Disable()
            self.layoutDoc_combo.Disable()
            self.pageTitle_value.Disable()
            self.pageHeader_value.Disable()
            self.pageFootnote_value.Disable()
        else:
            self.layoutDoc_combo.Enable()
            enableDisableList = [self.columns_value, self.grid_shared_tools, self.grid_height_value,
                                 self.grid_width_value]
            if self.layoutDoc_combo.GetStringSelection() != 'Grid':
                for item in enableDisableList: item.Disable()
            else:
                for item in enableDisableList: item.Enable()

            if self.layoutDoc_combo.GetStringSelection() in ["Columns", "Grid", "Rows"]:
                self.pageTitle_value.Enable()
                self.pageHeader_value.Enable()
                self.pageFootnote_value.Enable()
                self.grid_add_custom_js_widgets.Enable()
            else:
                self.pageTitle_value.Disable()
                self.pageHeader_value.Disable()
                self.pageFootnote_value.Disable()
                self.grid_add_custom_js_widgets.Disable()

        # Change values in dictionary
        if selectedItem != 'None':
            self.config.pageDict[selectedItem] = {'layout':self.layoutDoc_combo.GetStringSelection(),
                                                  'columns':str2int(self.columns_value.GetValue()),
                                                  'rows':None, 'name':selectedItem,
                                                  'grid_share_tools':self.grid_shared_tools.GetValue(),
                                                  'title':self.pageTitle_value.GetValue(),
                                                  'header':self.pageHeader_value.GetValue(),
                                                  'footnote':self.pageFootnote_value.GetValue(),
                                                  'grid_plot_height':str2int(self.grid_height_value.GetValue()),
                                                  'grid_plot_width':str2int(self.grid_width_value.GetValue()),
                                                  'add_js_widgets':self.grid_add_custom_js_widgets.GetValue()}

    def onApply(self, evt):
        """
        Update figure settings
        """

        self.config.interactive_custom_events = self.custom_js_events.GetValue()
        self.config.interactive_custom_scripts = self.custom_js_scripts.GetValue()
        self.config.interactive_sort_before_saving = self.sort_before_saving.GetValue()

        # Bar
        self.config.interactive_bar_width = self.bar_width_value.GetValue()
        self.config.interactive_bar_alpha = self.bar_alpha_value.GetValue()
        self.config.interactive_bar_sameAsFill = self.bar_colorEdge_check.GetValue()
        self.config.interactive_bar_lineWidth = self.bar_lineWidth_value.GetValue()

        # Scatter
        self.config.interactive_scatter_size = self.scatter_marker_size.GetValue()
        self.config.interactive_scatter_alpha = self.scatter_marker_alpha.GetValue()
        self.config.interactive_scatter_marker = self.scatter_marker.GetStringSelection()
        self.config.interactive_scatter_sameAsFill = self.scatter_color_sameAsFill.GetValue()

        # Annotations
        self.config.interactive_ms_annotations_offsetX = self.annot_xpos_value.GetValue()
        self.config.interactive_ms_annotations_offsetY = self.annot_ypos_value.GetValue()
        self.config.interactive_ms_annotations_highlight = self.annot_peakHighlight.GetValue()
        self.config.interactive_ms_annotations_labels = self.annot_peakLabel.GetValue()
        self.config.interactive_ms_annotations_fontSize = self.annot_fontSize_value.GetValue()
        self.config.interactive_ms_annotations_rotation = self.annot_rotation_value.GetValue()
        self.config.interactive_ms_annotations_fontWeight = self.annot_fontWeight_value.GetValue()

        # Figure size
#         self.config.figHeight = str2int(self.figHeight_value.GetValue())
#         self.config.figWidth = str2int(self.figWidth_value.GetValue())
#         self.config.figHeight1D = str2int(self.figHeight1D_value.GetValue())
#         self.config.figWidth1D = str2int(self.figWidth1D_value.GetValue())

        # Figure format
        self.config.layoutModeDoc = self.layoutDoc_combo.GetValue()
        self.config.plotLayoutOverlay = self.layout_combo.GetValue()
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

#         # tools
#         self.config.toolsLocation = self.location_combo.GetValue()

        # Grid overlay settings
#         self.config.interactive_grid_label_size = str2num(self.grid_label_size_value.GetValue())
#         self.config.interactive_grid_label_weight = self.grid_label_weight.GetValue()

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

        self.config.interactive_colorbar_padding = str2int(self.colorbarPadding.GetValue())
        self.config.interactive_colorbar_width = str2int(self.colorbarWidth.GetValue())
        self.config.interactive_colorbar_label_offset = str2int(self.interactive_colorbar_label_offset.GetValue())

#         # Plot parameters
#         self.config.interactive_outline_width = str2num(self.interactive_outline_width.GetValue())
#         self.config.interactive_outline_alpha = str2num(self.interactive_outline_alpha.GetValue())
#         self.config.interactive_border_min_right = str2int(self.interactive_border_min_right.GetValue())
#         self.config.interactive_border_min_left = str2int(self.interactive_border_min_left.GetValue())
#         self.config.interactive_border_min_top = str2int(self.interactive_border_min_top.GetValue())
#         self.config.interactive_border_min_bottom = str2int(self.interactive_border_min_bottom.GetValue())
#         self.config.interactive_grid_line = self.interactive_grid_line.GetValue()

        # legend
#         self.config.interactive_legend = self.legend_legend.GetValue()
#         self.config.interactive_legend_location = self.legend_position.GetStringSelection()
#         self.config.interactive_legend_click_policy = self.legend_click_policy.GetStringSelection()
#         self.config.interactive_legend_orientation = self.legend_orientation.GetStringSelection()
#         self.config.interactive_legend_font_size = self.legend_fontSize.GetValue()
#         self.config.interactive_legend_background_alpha = self.legend_transparency.GetValue()
#         self.config.interactive_legend_mute_alpha = self.legend_mute_transparency.GetValue()

        # line parameters
        self.config.interactive_line_width = self.line_width.GetValue()
        self.config.interactive_line_alpha = self.line_transparency.GetValue()
        self.config.interactive_line_style = self.line_style.GetStringSelection()

        if self.config.autoSaveSettings:
            self.presenter.onExportConfig(evt=ID_saveConfig, verbose=False)

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
#             print("dict", dictionary['tools']['tools'])
#             self.config.interactiveToolsOnOff[dictionary['tools']['name']] = dictionary['tools']['tools']
        else: dictionary['tools'] = {}

        if 'interactive_params' in dictionary:
            pass
        else:
            dictionary['interactive_params'] = {'line_width':self.config.interactive_line_width,
                                                'line_alpha':self.config.interactive_line_alpha,
                                                'line_style':self.config.interactive_line_style,
                                                'line_linkXaxis':self.config.hoverVline,
                                                'overlay_layout':self.config.plotLayoutOverlay,
                                                'overlay_linkXY':self.config.linkXYaxes,
                                                'colorbar':self.config.interactive_colorbar,
                                                'legend':self.config.interactive_legend}

        dictionary = self._preset_interactive_parameters(dictionary)

        if 'interactive' in dictionary: pass
        else:
            interactiveDict = {'order':'',
                               'page':self.config.pageDict['None'],
                               'tools':''}
            dictionary['interactive'] = interactiveDict

        return dictionary

    def checkFigureSizes(self, dictionary, data_type="1D"):

        try:
            plot_width = dictionary['interactive_params']['plot_width']
            plot_height = dictionary['interactive_params']['plot_height']
        except:
            if data_type in ["1D", "MS", "RT"]:
                plot_width, plot_height = 800, 400
            elif data_type == "2D":
                plot_width, plot_height = 600, 600
            elif data_type == "Grid":
                plot_width, plot_height = 500, 300
            else:
                plot_width, plot_height = 600, 600

        dictionary['interactive_params']['plot_width'] = plot_width
        dictionary['interactive_params']['plot_height'] = plot_height

        return dictionary

#     def checkToolsUnidec(self, key):
#         if key in ['Processed', 'Fitted', 'MW distribution', 'm/z with isolated species']:
#             toolname = "1D"
# #             toolset = self.getToolSet(plotType='1D')
#         elif key in ['m/z vs Charge', 'MW vs Charge']:
#             toolname = "2D"
# #             toolset = self.getToolSet(plotType='2D')
#         elif key == "Barchart":
#             toolname = "1D"
#             toolset = self.getToolSet(plotType='1D')
#
#         return toolname, toolset

    def populateTable(self):
        """
        Populate table with appropriate dataset values
        """

        if len(self.documentsDict) > 0:
            for key in self.documentsDict:
                data = []
                docData = self.documentsDict[key]
                if docData.gotMS == True:
                    data = docData.massSpectrum
                    if data.get('cmap', "") == "": data['cmap'] = self.config.interactive_line_color
                    kwargs = {"toolset":"MS", "color":(200, 236, 236)}
                    self.append_to_table(data, key, "", "MS", **kwargs)

                    if 'unidec' in docData.massSpectrum:
                        for innerKey in docData.massSpectrum['unidec']:
                            if innerKey in ['Charge information']: continue
                            data = docData.massSpectrum['unidec'][innerKey]
                            kwargs = {"color":(176, 202, 220), "toolset":innerKey}
                            self.append_to_table(data, key, innerKey, "UniDec", **kwargs)

                if hasattr(docData, "gotSmoothMS"):
                    if docData.gotSmoothMS == True:
                        data = docData.smoothMS
                        if data.get('cmap', "") == "": data['cmap'] = self.config.interactive_line_color
                        kwargs = {"toolset":"MS", "color":(116, 185, 255)}
                        self.append_to_table(data, key, "", "Processed MS", **kwargs)


                    if 'unidec' in docData.smoothMS:
                        for innerKey in docData.smoothMS['unidec']:
                            if innerKey in ['Charge information']: continue
                            data = docData.smoothMS['unidec'][innerKey]
                            kwargs = {"color":(176, 202, 220), "toolset":innerKey}
                            self.append_to_table(data, key, innerKey, "UniDec, processed", **kwargs)

                if docData.got1RT == True:
                    data = docData.RT
                    if data.get('cmap', "") == "": data['cmap'] = self.config.interactive_line_color
                    kwargs = {"toolset":"1D", "color":(219, 209, 255)}
                    self.append_to_table(data, key, "", "RT", **kwargs)

                if docData.got1DT == True:
                    data = docData.DT
                    if data.get('cmap', "") == "": data['cmap'] = self.config.interactive_line_color
                    kwargs = {"toolset":"1D", "color":(255, 118, 117)}
                    self.append_to_table(data, key, "", "1D", **kwargs)

                if docData.got2DIMS == True:
                    data = docData.IMS2D
                    kwargs = {"toolset":"2D", "color":(255, 206, 252)}
                    self.append_to_table(data, key, "", "2D", **kwargs)

                if docData.got2Dprocess == True:
                    data = docData.IMS2Dprocess
                    kwargs = {"toolset":"2D", "color":(99, 110, 114)}
                    self.append_to_table(data, key, "", "2D, processed", **kwargs)

                if docData.gotExtractedIons == True:
                    for innerKey in docData.IMS2Dions:
                        data = docData.IMS2Dions[innerKey]
                        kwargs = {"toolset":"2D", "color":(179, 180, 180)}
                        self.append_to_table(data, key, innerKey, "2D", **kwargs)

                if docData.gotMultipleMS == True:
                    for innerKey in docData.multipleMassSpectrum:
                        data = docData.multipleMassSpectrum[innerKey]
                        if data.get('cmap', "") == "": data['cmap'] = self.config.interactive_line_color
                        kwargs = {"toolset":"MS", "color":(200, 236, 236)}
                        self.append_to_table(data, key, innerKey, "MS, multiple", **kwargs)

                        if 'unidec' in docData.multipleMassSpectrum[innerKey]:
                            for innerInnerKey in docData.multipleMassSpectrum[innerKey]['unidec']:
                                if innerInnerKey in ['Charge information']: continue
                                data = docData.multipleMassSpectrum[innerKey]['unidec'][innerInnerKey]
                                kwargs = {"color":(176, 202, 220), "toolset":innerInnerKey}
                                innerInnerKeyLabel = "{} | {}".format(innerInnerKey, innerKey)
                                self.append_to_table(data, key, innerInnerKeyLabel, "UniDec, multiple", **kwargs)

                if hasattr(docData, 'gotMultipleRT'):
                    for innerKey in docData.multipleRT:
                        data = docData.multipleRT[innerKey]
                        if data.get('cmap', "") == "": data['cmap'] = self.config.interactive_line_color
                        kwargs = {"toolset":"1D", "color":(219, 209, 255)}
                        self.append_to_table(data, key, innerKey, "RT, multiple", **kwargs)

                if hasattr(docData, 'gotMultipleDT'):
                    for innerKey in docData.multipleDT:
                        data = docData.multipleDT[innerKey]
                        if data.get('cmap', "") == "": data['cmap'] = self.config.interactive_line_color
                        kwargs = {"toolset":"1D", "color":(255, 118, 117)}
                        self.append_to_table(data, key, innerKey, "1D, multiple", **kwargs)


                if docData.gotExtractedDriftTimes == True:
                    for innerKey in docData.IMS1DdriftTimes:
                        if docData.dataType == 'Type: MANUAL': tableKey = '1D'
                        else: tableKey = 'DT-IMS'
                        data = docData.IMS1DdriftTimes[innerKey]
                        if data.get('cmap', "") == "": data['cmap'] = self.config.interactive_line_color
                        kwargs = {"toolset":"1D", "color":(154, 236, 219)}
                        self.append_to_table(data, key, innerKey, tableKey, **kwargs)

                if docData.gotCombinedExtractedIonsRT == True:
                    for innerKey in docData.IMSRTCombIons:
                        data = docData.IMSRTCombIons[innerKey]
                        if data.get('cmap', "") == "": data['cmap'] = self.config.interactive_line_color
                        kwargs = {"toolset":"RT", "color":(219, 209, 255)}
                        self.append_to_table(data, key, innerKey, "RT, combined", **kwargs)

                if docData.gotCombinedExtractedIons == True:
                    for innerKey in docData.IMS2DCombIons:
                        data = docData.IMS2DCombIons[innerKey]
                        kwargs = {"toolset":"2D", "color":(255, 206, 252)}
                        self.append_to_table(data, key, innerKey, "2D, combined", **kwargs)

                if docData.got2DprocessIons == True:
                    for innerKey in docData.IMS2DionsProcess:
                        data = docData.IMS2DionsProcess[innerKey]
                        kwargs = {"toolset":"2D", "color":(255, 206, 252)}
                        self.append_to_table(data, key, innerKey, "2D, processed", **kwargs)

                # Overlay data
                if docData.gotOverlay == True:
                    for innerKey in docData.IMS2DoverlayData:
                        data = docData.IMS2DoverlayData[innerKey]
                        overlayMethod = re.split('-|,|:|__', innerKey)
                        if overlayMethod[0] in ['Mask', 'Transparent']: color_label = "{}/{}".format(data['cmap1'], data['cmap2'])
                        else: color_label = data.get('cmap', "")
                        kwargs = {"toolset":"2D", "color_label":color_label, "color":(214, 220, 198)}
                        self.append_to_table(data, key, innerKey, "Overlay", **kwargs)

                if docData.gotStatsData == True:
                    for innerKey in docData.IMS2DstatsData:
                        data = docData.IMS2DstatsData[innerKey]
                        overlayMethod = re.split('-|,|:|__', innerKey)
                        kwargs = {"color":(222, 215, 255), "toolset":"2D"}
                        self.append_to_table(data, key, innerKey, "Statistical", **kwargs)

                if len(docData.other_data) > 0:
                    for innerKey in docData.other_data:
                        data = docData.other_data[innerKey]
                        kwargs = {"color":(215, 224, 184)}
                        self.append_to_table(data, key, innerKey, "Other data", **kwargs)
                        
                # Tandem dat a
                if len(docData.tandem_spectra) > 0:
                    data = docData.tandem_spectra
                    if data.get('cmap', "") == "": data['cmap'] = self.config.interactive_line_color
                    kwargs = {"toolset":"1D", "color":(219, 209, 255)}
                    self.append_to_table(data, key, "", "MS/MS", **kwargs)

            self.onAddPageChoices(evt=None)
        else:
            msg = 'Document list is empty'
            self.presenter.onThreading(None, (msg, 4), action='updateStatusbar')
            self.onAddPageChoices(evt=None)

    def append_to_table(self, data, key, innerKey, subKey, **kwargs):
        # check if has all keys
        data = self.checkIfHasHTMLkeys(data)
        data = self.checkFigureSizes(data, kwargs.get("toolset", "1D"))

        # extract data
        title = data['title']
        header = data['header']
        footnote = data['footnote']
        color = data['cmap']
        page = data['page']['name']
        order = data['order']

        if kwargs.get("color_label", False):
            color = kwargs['color_label']

        # append item
        self.itemsList.Append(["", key, subKey, innerKey, title, header,
                               footnote, color, page, order])
        if "color" in kwargs:
            self.itemsList.SetItemBackgroundColour(
                self.itemsList.GetItemCount() - 1, kwargs['color'])
            self.itemsList.SetItemTextColour(
                self.itemsList.GetItemCount() - 1, determineFontColor(kwargs['color'], return_rgb=True))

    def onAddPageChoices(self, evt=None):
        """
        Repopulate combo boxes
        """
        self.pageLayoutSelect_htmlView.Clear()
        self.pageLayoutSelect_propView.Clear()
        self.pageLayoutSelect_toolbar.Clear()

        # Remove any key without a proper name
        try: del self.config.pageDict[u'']
        except KeyError: pass

        sorted_page_list = natsorted(self.config.pageDict.keys())
        self.pageLayoutSelect_htmlView.AppendItems(sorted_page_list)
        self.pageLayoutSelect_propView.AppendItems(sorted_page_list)
        self.pageLayoutSelect_toolbar.AppendItems(sorted_page_list)
#
        # Setup the Layout window
        self.pageLayoutSelect_propView.SetStringSelection('None')
        self.pageLayoutSelect_toolbar.SetStringSelection('None')
        self.onSelectPageProperties(evt=None)

#     def onAddToolsChoices(self, evt=None):
# #         self.plotTypeToolsSelect_htmlView.Clear()
# #         self.plotTypeToolsSelect_propView.Clear()
# #         self.plotTypeToolsSelect_toolbar.Clear()
#
#         sorted_tools_list = natsorted(self.config.interactiveToolsOnOff.keys())
# #         self.plotTypeToolsSelect_htmlView.AppendItems(sorted_tools_list)
#         self.plotTypeToolsSelect_propView.AppendItems(sorted_tools_list)
#         self.plotTypeToolsSelect_toolbar.AppendItems(sorted_tools_list)
#
#         self.plotTypeToolsSelect_toolbar.SetStringSelection('1D')
#         self.plotTypeToolsSelect_propView.SetStringSelection('1D')

    def onItemSelected(self, evt):

#         # Disable all elements when nothing is selected
#         itemList = [self.itemName_value, self.itemHeader_value, self.itemFootnote_value,
#                     self.order_value, self.pageLayoutSelect_htmlView,
# #                     self.plotTypeToolsSelect_htmlView,
# #                     self.colorbarCheck
#                     ]
#
#         for item in itemList:
#             item.Enable()

        # When selecting new item, it automatically updates each field in the GUI,
        # however, as it does that, it also updates the data dictionary. By enabling
        # loading mode, only the GUI is updated and nothing else.
        self.loading = True
        self.currentItem = evt.m_itemIndex
        name = self.itemsList.GetItem(self.currentItem, self.config.interactiveColNames['document']).GetText()
        key = self.itemsList.GetItem(self.currentItem, self.config.interactiveColNames['type']).GetText()
        innerKey = self.itemsList.GetItem(self.currentItem, self.config.interactiveColNames['file']).GetText()
        color = self.itemsList.GetItem(self.currentItem, self.config.interactiveColNames['color']).GetText()
        order = self.itemsList.GetItem(self.currentItem, self.config.interactiveColNames['order']).GetText()
        if color == "": color = "(0, 0, 0)"

        # combine labels
        self.document_value.SetLabel(name.replace("__", " ").replace(".raw", ""))
        self.type_value.SetLabel(key.replace("__", " ").replace(".raw", ""))
        self.details_value.SetLabel(innerKey.replace("__", " ").replace(".raw", ""))

        information, unidecMethod = "", ""
        # Determine which document was selected
        document = self.documentsDict[name]
        docData = self.getItemData(name, key, innerKey)


        # build information
        if key in ['MS', 'Processed MS', 'RT', 'RT, multiple', '1D', '1D, multiple',
                   'MS, multiple', 'RT, combined']:
            information = "Length: {} \nRange: x-axis = {}-{} | y-axis = {}-{}".format(len(docData['xvals']),
                                                                                       np.round(docData['xvals'][0], 4),
                                                                                       np.round(docData['xvals'][-1], 4),
                                                                                       np.round(np.min(docData['yvals']), 4),
                                                                                       np.round(np.max(docData['yvals']), 4))
        elif key in ['2D', '2D, processed', '2D, combined']:
            information = "Shape: {} x {} \nRange: x-axis = {}-{} | y-axis = {}-{}".format(docData['zvals'].shape[0], docData['zvals'].shape[1],
                                                                                           np.round(docData['xvals'][0], 4),
                                                                                           np.round(docData['xvals'][-1], 4),
                                                                                           np.round(np.min(docData['yvals']), 4),
                                                                                           np.round(np.max(docData['yvals']), 4))
        if "annotations" in docData:
            if len(information) > 0:
                try: information = "{}\nAnnotations: {}".format(information, len(docData["annotations"]))
                except: pass
            else:
                try: information = "Annotations: {}".format(len(docData["annotations"]))
                except: information = ""
                
        if "annotated_item_list" in docData:
            if len(information) > 0:
                try: information = "{}\nAnnotated mass spectra: {}".format(information, len(docData["annotated_item_list"]))
                except: pass
            else:
                try: information = "Annotated mass spectra: {}".format(len(docData["annotated_item_list"]))
                except: information = ""
            
        #

        # Retrieve information
        title = docData.get('title', " ")
        header = docData['header']
        footnote = docData['footnote']
        page = docData['page']['name']

        # Update item editor
        try:
            self.itemName_value.SetValue(title)
            self.itemHeader_value.SetValue(header)
            self.itemFootnote_value.SetValue(footnote)
            self.itemInformation_value.SetLabel(information)
            self.order_value.SetValue(order)
            self.pageLayoutSelect_htmlView.SetStringSelection(page)
        except:
            self.loading = False

        self.loading = False

    def getItemData(self, name, key, innerKey):
        # Determine which document was selected
        document = self.documentsDict[name]

        if key == 'MS' and innerKey == '': docData = deepcopy(document.massSpectrum)
        if key == 'Processed MS' and innerKey == '': docData = deepcopy(document.smoothMS)
        if key == 'RT' and innerKey == '': docData = deepcopy(document.RT)
        if key == '1D' and innerKey == '': docData = deepcopy(document.DT)
        if key == '2D' and innerKey == '': docData = deepcopy(document.IMS2D)
        if key == '2D, processed' and innerKey == '': docData = deepcopy(document.IMS2Dprocess)
        if key == 'MS, multiple' and innerKey != '': docData = deepcopy(document.multipleMassSpectrum[innerKey])
        if key == '2D' and innerKey != '': docData = deepcopy(document.IMS2Dions[innerKey])
        if key == 'DT-IMS' and innerKey != '': docData = deepcopy(document.IMS1DdriftTimes[innerKey])
        if key == '1D' and innerKey != '': docData = deepcopy(document.IMS1DdriftTimes[innerKey])
        if key == '1D, multiple' and innerKey != '': docData = deepcopy(document.multipleDT[innerKey])
        if key == 'RT, combined' and innerKey != '': docData = deepcopy(document.IMSRTCombIons[innerKey])
        if key == 'RT, multiple' and innerKey != '': docData = deepcopy(document.multipleRT[innerKey])
        if key == '2D, combined' and innerKey != '': docData = deepcopy(document.IMS2DCombIons[innerKey])
        if key == '2D, processed' and innerKey != '': docData = deepcopy(document.IMS2DionsProcess[innerKey])
        if key == 'Overlay' and innerKey != '': docData = deepcopy(document.IMS2DoverlayData[innerKey])
        if key == 'Statistical' and innerKey != '': docData = deepcopy(document.IMS2DstatsData[innerKey])
        if key == 'UniDec' and innerKey != '': docData = deepcopy(document.massSpectrum['unidec'][innerKey])
        if key == 'UniDec, processed' and innerKey != '': docData = deepcopy(document.smoothMS['unidec'][innerKey])
        if key == 'UniDec, multiple' and innerKey != '':
            unidecMethod = re.split(' \| ', innerKey)[0]
            innerKey = re.split(' \| ', innerKey)[1]
            docData = deepcopy(document.multipleMassSpectrum[innerKey]['unidec'][unidecMethod])
        if key == "Other data" and innerKey != "": docData = document.other_data[innerKey]
        if key == "MS/MS" and innerKey == '': docData = document.tandem_spectra
        
        return docData

    def on_change_page_for_item(self, evt):
        """ This function changes the output page for selected item """
        if self.currentItem == None:
            msg = 'Please select item first'
            self.presenter.onThreading(None, (msg, 4), action='updateStatusbar')
            return

        # Get current page selection
        page = self.pageLayoutSelect_htmlView.GetStringSelection()
        self.itemsList.SetStringItem(index=self.currentItem,
                                     col=self.config.interactiveColNames['page'],
                                     label=str(page))

        name, key, innerKey = self._getItemDetails()

        pageData = self.config.pageDict[page]
        self.onUpdateDocumentKeyword(name, key, innerKey, keyword="page", value=pageData)

    def on_change_page_for_items(self, evt):
        """ This function changes the output page for selected items (batch)"""
        rows = self.itemsList.GetItemCount()
        page = self.pageLayoutSelect_toolbar.GetStringSelection()
        for row in range(rows):
            if self.itemsList.IsChecked(index=row):
                self.currentItem = row
                self.itemsList.SetStringItem(index=row,
                                             col=self.config.interactiveColNames['page'],
                                             label=page)

                name, key, innerKey = self._getItemDetails()
                pageData = self.config.pageDict[page]
                self.onUpdateDocumentKeyword(name, key, innerKey, keyword="page", value=pageData)

    def on_change_colormap_for_items(self, evt):
        """ This function changes colormap for selected items (batch)"""
        rows = self.itemsList.GetItemCount()
        colormap = self.colormapSelect_toolbar.GetStringSelection()

        for row in range(rows):
            if self.itemsList.IsChecked(index=row):
                name, key, innerKey = self._getItemDetails()
                if key in ['2D', '2D, processed', '2D, combined', 'Overlay', 'Statistical']:
                    self.currentItem = row
                    self.itemsList.SetStringItem(index=row,
                                                 col=self.config.interactiveColNames['colormap'],
                                                 label=str(colormap))
                    self.onUpdateDocumentKeyword(name, key, innerKey, keyword="cmap", value=str(colormap))

    def on_change_color(self, evt):

        if self.currentItem == None and evt.GetId() == ID_changeColorInteractive:
            msg = 'Please select item first'
            self.presenter.onThreading(None, (msg, 4), action='updateStatusbar')
            return
        if evt.GetId() in [ID_changeColorInteractive,
                            ID_changeColorNotationInteractive,
                            ID_changeColorBackgroundNotationInteractive,
                            ID_changeColorGridLabelInteractive,
                            ID_changeColorAnnotLabelInteractive,
                            ID_interactivePanel_color_markerEdge,
                            ID_interactivePanel_color_barEdge,
                            ID_changeColorBackgroundInteractive,
                            ID_changeColorGridLineInteractive
                            ]:
            # Show dialog and get new colour
            custom = wx.ColourData()
            for key in range(len(self.config.customColors)):
                custom.SetCustomColour(key, self.config.customColors[key])
            dlg = wx.ColourDialog(self, custom)
            dlg.GetColourData().SetChooseFull(True)


            if dlg.ShowModal() == wx.ID_OK:
                data = dlg.GetColourData()
                newColour = list(data.GetColour().Get())
                newColour255 = tuple([round((np.float(newColour[0]) / 255), 2),
                                      round((np.float(newColour[1]) / 255), 2),
                                      round((np.float(newColour[2]) / 255), 2)])
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
                elif evt.GetId() == ID_changeColorAnnotLabelInteractive:
                    self.annot_fontColor_colorBtn.SetBackgroundColour(newColour)
                    self.config.interactive_ms_annotations_label_color = newColour255
                elif evt.GetId() == ID_interactivePanel_color_markerEdge:
                    self.scatter_marker_edge_colorBtn.SetBackgroundColour(newColour)
                    self.config.interactive_scatter_edge_color = newColour255
                elif evt.GetId() == ID_interactivePanel_color_barEdge:
                    self.bar_edgeColorBtn.SetBackgroundColour(newColour)
                    self.config.interactive_bar_edge_color = newColour255

                self.onAnnotateItems(evt=None)
                dlg.Destroy()
            else:
                return
        elif evt.GetId() == ID_changeColormapInteractive:
            colormap = self.comboCmapSelect.GetValue()
            self.itemsList.SetStringItem(index=self.currentItem,
                                         col=self.config.interactiveColNames['colormap'],
                                         label=str(colormap))
            self.onAnnotateItems(evt=None)

    def onUpdateDocumentKeyword(self, name, key, innerKey, keyword, value):
        document = self.documentsDict[name]

        if key == 'MS' and innerKey == '':
            document.massSpectrum[keyword] = value

        if key == 'Processed MS' and innerKey == '':
            document.smoothMS[keyword] = value

        if key == 'RT' and innerKey == '':
            document.RT[keyword] = value

        if key == 'RT, multiple' and innerKey != '':
            document.multipleRT[innerKey][keyword] = value

        if key == '1D' and innerKey == '':
            document.DT[keyword] = value

        if key == '1D, multiple' and innerKey != '':
            document.multipleDT[innerKey][keyword] = value

        if key == 'MS, multiple' and innerKey != '':
            document.multipleMassSpectrum[innerKey][keyword] = value

        if key == 'DT-IMS' and innerKey != '':
            document.IMS1DdriftTimes[innerKey][keyword] = value

        if key == 'RT, combined' and innerKey != '':
            document.IMSRTCombIons[innerKey][keyword] = value

        if key == '2D' and innerKey == '':
            document.IMS2D[keyword] = value

        if key == '2D, processed' and innerKey == '':
            document.IMS2Dprocess[keyword] = value

        if key == '2D, processed' and innerKey == '':
            document.IMS2Dprocess[keyword] = value

        if key == '2D' and innerKey != '':
            document.IMS2Dions[innerKey][keyword] = value

        if key == '2D, combined' and innerKey != '':
            document.IMS2DCombIons[innerKey][keyword] = value

        if key == '2D, processed' and innerKey != '':
            document.IMS2DionsProcess[innerKey][keyword] = value

        if key == 'Overlay' and innerKey != '':
            document.IMS2DoverlayData[innerKey][keyword] = value

        if key == 'Statistical' and innerKey != '':
            document.IMS2DstatsData[innerKey][keyword] = value

        if key == 'Other data' and innerKey != '':
            document.other_data[innerKey][keyword] = value

        if key == 'UniDec' and innerKey != '':
            document.massSpectrum['unidec'][innerKey][keyword] = value

        if key == 'UniDec, processed' and innerKey != '':
            document.massSpectrum['unidec'][innerKey][keyword] = value

        if key == 'UniDec, multiple' and innerKey != '':
            unidecMethod = re.split(' \| ', innerKey)[0]
            innerKey = re.split(' \| ', innerKey)[1]
            document.multipleMassSpectrum[innerKey]['unidec'][unidecMethod][keyword] = value

        # Update dictionary
        self.presenter.documentsDict[document.title] = document

    def onUpdateDocument(self, name, key, innerKey, **kwargs):
        document = self.documentsDict[name]
        colorbar = kwargs.pop("colorbar", False)

        if key == 'MS' and innerKey == '': document.massSpectrum = self.add_tags_to_data(document.massSpectrum, colorbar=False, **kwargs)

        if key == 'Processed MS' and innerKey == '': document.smoothMS = self.add_tags_to_data(document.smoothMS, colorbar=False, **kwargs)

        if key == 'RT' and innerKey == '': document.RT = self.add_tags_to_data(document.RT, colorbar=False, **kwargs)

        if key == 'RT, multiple' and innerKey != '': document.multipleRT[innerKey] = self.add_tags_to_data(document.multipleRT[innerKey], **kwargs)

        if key == '1D' and innerKey == '': document.DT = self.add_tags_to_data(document.DT, colorbar=False, **kwargs)

        if key == '1D, multiple' and innerKey != '': document.multipleDT[innerKey] = self.add_tags_to_data(document.multipleDT[innerKey], colorbar=False, **kwargs)

        if key == 'MS, multiple' and innerKey != '': document.multipleMassSpectrum[innerKey] = self.add_tags_to_data(document.multipleMassSpectrum[innerKey], colorbar=False, **kwargs)

        if key == 'DT-IMS' and innerKey != '': document.IMS1DdriftTimes[innerKey] = self.add_tags_to_data(document.IMS1DdriftTimes[innerKey], colorbar=False, **kwargs)

        if key == 'RT, combined' and innerKey != '': document.IMSRTCombIons[innerKey] = self.add_tags_to_data(document.IMSRTCombIons[innerKey], colorbar=False, **kwargs)

        if key == '2D' and innerKey == '': document.IMS2D = self.add_tags_to_data(document.IMS2D, colorbar=colorbar, **kwargs)

        if key == '2D, processed' and innerKey == '': document.IMS2Dprocess = self.add_tags_to_data(document.IMS2Dprocess, colorbar=colorbar, **kwargs)

        if key == '2D, processed' and innerKey == '': document.IMS2Dprocess = self.add_tags_to_data(document.multipleMassSpectrum, colorbar=colorbar, **kwargs)

        if key == '2D' and innerKey != '': document.IMS2Dions[innerKey] = self.add_tags_to_data(document.IMS2Dions[innerKey], colorbar=colorbar, **kwargs)

        if key == '2D, combined' and innerKey != '': document.IMS2DCombIons[innerKey] = self.add_tags_to_data(document.IMS2DCombIons[innerKey], colorbar=colorbar, **kwargs)

        if key == '2D, processed' and innerKey != '': document.IMS2DionsProcess[innerKey] = self.add_tags_to_data(document.IMS2DionsProcess[innerKey], colorbar=colorbar, **kwargs)

        if key == 'Overlay' and innerKey != '': document.IMS2DoverlayData[innerKey] = self.add_tags_to_data(document.IMS2DoverlayData[innerKey], colorbar=colorbar, **kwargs)

        if key == 'Statistical' and innerKey != '': document.IMS2DstatsData[innerKey] = self.add_tags_to_data(document.IMS2DstatsData[innerKey], colorbar=colorbar, **kwargs)

        if key == 'Other data' and innerKey != '': document.other_data[innerKey] = self.add_tags_to_data(document.other_data[innerKey], colorbar=colorbar, **kwargs)

        if key == 'UniDec' and innerKey != '': document.massSpectrum['unidec'][innerKey] = self.add_tags_to_data(document.massSpectrum['unidec'][innerKey], colorbar=colorbar, **kwargs)

        if key == 'UniDec, processed' and innerKey != '': document.massSpectrum['unidec'][innerKey] = self.add_tags_to_data(document.smoothMS['unidec'][innerKey], colorbar=colorbar, **kwargs)

        if key == 'UniDec, multiple' and innerKey != '':
            unidecMethod = re.split(' \| ', innerKey)[0]
            innerKey = re.split(' \| ', innerKey)[1]
            document.multipleMassSpectrum[innerKey]['unidec'][unidecMethod] = self.add_tags_to_data(document.multipleMassSpectrum[innerKey]['unidec'][unidecMethod], colorbar=colorbar, **kwargs)

        # Update dictionary
        self.presenter.documentsDict[document.title] = document

    def onAnnotateItems(self, evt=None, itemID=None):

        # If we only updating dictionary
        if itemID != None:
            self.currentItem = itemID

        # Check if is empty
        if self.currentItem == None:
            return

        if self.loading:
            return

        name = self.itemsList.GetItem(self.currentItem, self.config.interactiveColNames['document']).GetText()
        key = self.itemsList.GetItem(self.currentItem, self.config.interactiveColNames['type']).GetText()
        innerKey = self.itemsList.GetItem(self.currentItem, self.config.interactiveColNames['file']).GetText()
        color = self.itemsList.GetItem(self.currentItem, self.config.interactiveColNames['color']).GetText()
        page = self.itemsList.GetItem(self.currentItem, self.config.interactiveColNames['page']).GetText()
#         tool = self.itemsList.GetItem(self.currentItem, self.config.interactiveColNames['tools']).GetText()
#         title = self.itemsList.GetItem(self.currentItem,self.config.interactiveColNames['title']).GetText()
#         header = self.itemsList.GetItem(self.currentItem,self.config.interactiveColNames['header']).GetText()
#         footnote = self.itemsList.GetItem(self.currentItem,self.config.interactiveColNames['footnote']).GetText()
#         orderNum = self.itemsList.GetItem(self.currentItem,self.config.interactiveColNames['order']).GetText()

        # Get data
        pageData = self.config.pageDict[page]
#         tools = self.getToolSet(preset=tool)
#         toolSet = {'name':tool, 'tools':tools}  # dictionary object

        if any(key in method for method in ["MS", "RT", "1D", "RT, combined",
                                            'MS, multiple', '1D, multiple',
                                            'RT, multiple']):
            color = (eval(color))

        title = self.itemName_value.GetValue()
        header = self.itemHeader_value.GetValue()
        footnote = self.itemFootnote_value.GetValue()
        orderNum = self.order_value.GetValue()
#         colorbar = self.colorbarCheck.GetValue()

        interactive_params = {}
#         interactive_params = {'line_width':self.html_plot1D_line_width.GetValue(),
#                               'line_alpha':self.html_plot1D_line_alpha.GetValue(),
#                               'line_style':self.html_plot1D_line_style.GetStringSelection(),
#                               'line_linkXaxis':self.html_plot1D_hoverLinkX.GetValue(),
#                               'overlay_layout':self.html_overlay_layout.GetValue(),
#                               'overlay_linkXY':self.html_overlay_linkXY.GetValue(),
#                               'overlay_color_1':self.html_overlay_colormap_1.GetStringSelection(),
#                               'overlay_color_2':self.html_overlay_colormap_2.GetStringSelection(),
#                               'colorbar':self.colorbarCheck.GetValue(),
#                               'legend':self.html_overlay_legend.GetValue(),
#                               'title_label':self.grid_label_check.GetValue(),
#                               'grid_xpos':str2num(self.grid_xpos_value.GetValue()),
#                               'grid_ypos':str2num(self.grid_ypos_value.GetValue()),
#                               'linearize_spectra':self.linearizeCheck.GetValue(),
#                               'show_annotations':self.showAnnotationsCheck.GetValue(),
#                               'bin_size':str2num(self.binSize_value.GetValue()),
#                               'plot_height':str2int(self.figsize_height_value.GetValue()),
#                               'plot_width':str2int(self.figsize_width_value.GetValue()),
#                               'xlimits':[str2num(self.axes_xmin_value.GetValue()), str2num(self.axes_xmax_value.GetValue())],
#                               'ylimits':[str2num(self.axes_ymin_value.GetValue()), str2num(self.axes_ymax_value.GetValue())],
#                               'waterfall_increment':str2num(self.waterfall_increment_value.GetValue()),
#                               'waterfall_shade_under':self.waterfall_shade_check.GetValue(),
#                               'waterfall_shade_transparency':str2num(self.waterfall_shade_transparency_value.GetValue()),
#                               'overlay_1D_shade_under':self.overlay_shade_check.GetValue(),
#                               'overlay_1D_shade_transparency':str2num(self.overlay_shade_transparency_value.GetValue()),
#                               }

        color_label = color
#         if key == 'Overlay':
#             overlayMethod = re.split('-|,|:|__', innerKey)
#             if overlayMethod[0] == 'Mask' or overlayMethod[0] == 'Transparent':
#                 color_label = "%s/%s" % (self.html_overlay_colormap_1.GetStringSelection(),
#                                          self.html_overlay_colormap_2.GetStringSelection())
#                 pageData = self.config.pageDict['None']
#
#         if ((key in ['MS', 'Processed MS', 'RT', '1D']  and innerKey == '') or
#             (key in ['MS, multiple', 'RT, multiple', '1D, multiple', 'DT-IMS',
#                      'RT, combined', ] and innerKey != '')):
# #             colorbar = False


        # Retrieve and add data to dictionary
        kwargs = {"title":_replace_labels(title), "header":header, "footnote":footnote,
                  "order":orderNum, "color":color, "page":pageData,
#                   "toolset":toolSet,
                  "interactive_parameters":interactive_params,
#                   "colorbar":colorbar
                  }

        self.onUpdateDocument(name, key, innerKey, **kwargs)

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
#         self.itemsList.SetStringItem(index=self.currentItem,
#                                      col=self.config.interactiveColNames['tools'], label=tool)

    def add_tags_to_data(self, dictionary, colorbar=False, **kwargs):
        """
        Helper function to add title,header,footnote data
        to dictionary
        """
        dictionary['title'] = kwargs.pop("title")
        dictionary['header'] = kwargs.pop("header")
        dictionary['footnote'] = kwargs.pop("footnote")
        dictionary['order'] = kwargs.pop("order")
        dictionary['cmap'] = kwargs.pop("color")
        dictionary['page'] = kwargs.pop("page")
        dictionary['colorbar'] = colorbar

        dictionary['interactive_params'] = merge_two_dicts(dictionary.get('interactive_params', {}),
                                                           kwargs["interactive_parameters"])

        try: dictionary['cmap1'] = kwargs["interactive_parameters"]['overlay_color_1']
        except: pass
        try: dictionary['cmap2'] = kwargs["interactive_parameters"]['overlay_color_2']
        except: pass

        return dictionary

    def linearize_spectrum(self, xvals, yvals, binsize):
        kwargs = {'auto_range':self.config.ms_auto_range,
                  'mz_min':np.round(np.min(xvals), 0),
                  'mz_max':np.round(np.min(yvals), 0),
                  'mz_bin':float(binsize),
                  'linearization_mode':"Linear interpolation"}

        msX, msY = linearize_data(xvals, yvals, **kwargs)
        if len(msX) > len(xvals):
            print("Chose not to linearize spectrum as it would increase it from {} to {}".format(len(xvals), len(msX)))
            return xvals, yvals
        else:
            print("Linearized spectrum. Reduced spectrum from {} to {}".format(len(xvals), len(msX)))
            return msX, msY

    def add_custom_js_widgets(self, bokehPlot, js_type="label_toggle",
                              position="right", data={}, **kwargs):
        """
        Add custoom JS scripts to plots
        @param bokehPlot (figure): bokeh figure
        @param js_type (figure): list of types of java script tools to be added
        @param position (str): widget position
        @param data (dict): data object
        @param kwargs (dict): kwargs with necessary objects
        """

        widget_width = 302
        user_kwargs = deepcopy(data['interactive_params'])

        tstart = time.time()
        if not isinstance(js_type, list):
            js_type = [js_type]

        # get position
        position = self.custom_js_position.GetStringSelection()
        js_widgets = []
        msg = "Added JS scripts: "
        try:
            if "label_toggle" in js_type and "labels" in kwargs:
                labels = kwargs["labels"]
                js_code = '''\
                if (toggle.active) {
                    labels.text_alpha = 1;
                    toggle.label = "Hide labels";
                    console.log('Showing labels');
                    }
                else {
                    labels.text_alpha = 0;
                    toggle.label = "Show labels";
                    console.log('Hiding labels');
                    }
                '''
                callback = CustomJS(code=js_code, args={})
                toggle = Toggle(label="Hide labels", button_type="success", callback=callback, active=True,
                                width=widget_width)
                callback.args = {'toggle': toggle, 'labels': labels, 'figure':bokehPlot}
                js_widgets.append(toggle)
                msg = "{} Annotation on/off toggle |".format(msg)
    
            if "label_size_slider" in js_type and "labels" in kwargs:
                labels = kwargs["labels"]
                js_code = '''\
                label_size = slider.value;
                labels.text_font_size = label_size + 'pt';
                console.log('Font size: ' + label_size);
                '''
                callback = CustomJS(code=js_code, args={})
                slider = Slider(start=6, end=16, step=0.5, value=self.config.interactive_ms_annotations_fontSize,
                                callback=callback, title="Label fontsize",
                                width=widget_width)
                callback.args = {'slider': slider, 'labels':labels}
                js_widgets.append(slider)
                msg = "{} Annotation font size slider |".format(msg)
    
            if "label_offset_x" in js_type and "labels" in kwargs:
                labels = kwargs["labels"]
                js_code = '''\
                x_offset = slider.value;
                labels.x_offset = x_offset;
                console.log('X offset: ' + x_offset);
                '''
                callback = CustomJS(code=js_code, args={})
                slider = Slider(start=-100, end=100, step=5, value=self.config.interactive_ms_annotations_offsetX,
                                callback=callback, title="Label x-axis offset",
                                width=widget_width)
                callback.args = {'slider': slider, 'labels':labels}
                js_widgets.append(slider)
                msg = "{} Annotation x-axis offset slider |".format(msg)
    
            if "label_offset_y" in js_type and "labels" in kwargs:
                labels = kwargs["labels"]
                js_code = '''\
                y_offset = slider.value;
                labels.y_offset = y_offset;
                console.log('Y offset: ' + y_offset);
                '''
                callback = CustomJS(code=js_code, args={})
                slider = Slider(start=-100, end=100, step=5, value=self.config.interactive_ms_annotations_offsetY,
                                callback=callback, title="Label y-axis offset",
                                width=widget_width)
                callback.args = {'slider': slider, 'labels':labels}
                js_widgets.append(slider)
                msg = "{} Annotation y-axis offset slider |".format(msg)
    
            if "label_rotation" in js_type and "labels" in kwargs:
                labels = kwargs["labels"]
                js_code = '''\
                angle = slider.value * 0.0174533;
                labels.angle_units = 'deg';
                labels.angle = angle;
                console.log('Angle: ' + angle);
                '''
                callback = CustomJS(code=js_code, args={})
                slider = Slider(start=0, end=180, step=10, value=kwargs.get("label_rotation_angle", self.config.interactive_ms_annotations_rotation),
                                callback=callback, title="Label rotation angle",
                                width=widget_width)
                callback.args = {'slider': slider, 'labels':labels}
                js_widgets.append(slider)
                msg = "{} Annotation rotation slider |".format(msg)
    
            if "slider_zoom" in js_type and "y_range_x1" in kwargs:
                js_code = '''\
                zoom_value  = slider.value;
                figure.y_range.end = {} * zoom_value;
                console.log 'Y-axis zoom x ' + zoom_value;
                '''.format(kwargs["y_range_x1"])
                callback = CustomJS.from_coffeescript(code=js_code, args={})
                slider = Slider(start=1, end=5, step=0.5, value=2,
                                callback=callback, title="Y-axis zoom",
                                width=widget_width)
                callback.args = {'slider': slider, 'figure':bokehPlot}
                js_widgets.append(slider)
                msg = "{} Y-axis range slider |".format(msg)
    
            if "hover_mode" in js_type and "hover" in kwargs:
                hover = kwargs["hover"]
                js_code = '''\
                if (radio.active == 0) {
                    hover.mode = 'mouse';
                    console.log('Hover mode: follow mouse');
                    }
                else if (radio.active == 1) {
                    hover.mode = 'vline';
                    console.log('Hover mode: follow vertical line');
                    }
                '''
                callback = CustomJS(code=js_code, args={})
                if hover.mode == "mouse": active_mode = 0
                elif hover.mode == "vline": active_mode = 1
                elif hover.mode == "hline": active_mode = 2
                group = RadioButtonGroup(labels=["        Follow mouse        ",
                                                 "    Follow vertical line    "],
                                         active=active_mode, callback=callback,
                                         width=widget_width)
                callback.args = {'radio': group, 'hover':hover}
                js_widgets.append(group)
                msg = "{} Hovertool mode toggle |".format(msg)
    
            if "legend_toggle" in js_type and "legend" in kwargs:
                legend = kwargs["legend"]
                js_code = '''\
                if (toggle.active) {
                    legend.border_line_alpha = 0;
                    legend.visible = true;
                    toggle.label = "Hide legend";
                    console.log('Showing legend');
                    }
                else {
                    legend.border_line_alpha = 0;
                    legend.visible = false;
                    toggle.label = "Show legend";
                    console.log('Hiding legend');
                    }
                figure.change.emit();
                '''
                callback = CustomJS(code=js_code, args={})
                toggle = Toggle(label="Hide legend", button_type="success", callback=callback,
                                active=True, width=widget_width)
                callback.args = {'toggle': toggle, 'legend': legend, 'figure':bokehPlot}
                js_widgets.append(toggle)
                msg = "{} Legend on/off toggle |".format(msg)
    
            if "legend_toggle_multi" in js_type and "legends" in kwargs:
                legends = kwargs["legends"]
                figures = kwargs["figures"]
                js_code = '''\
                if (toggle.active {
                    for j, i in legends
                        [legend, figure] = [legends[i], figures[i]];
                        legend.border_line_alpha = 0;
                        legend.visible = true;
                        figure.change.emit();
                    toggle.label = "Hide legends";
                    console.log('Showing legends');
                    }
                else {
                    for j, i in legends
                        [legend, figure] = [legends[i], figures[i]];
                        legend.border_line_alpha = 0;
                        legend.visible = false;
                        figure.change.emit();
                    toggle.label = "Show legends";
                    console.log('Hiding legends');
                    }
                '''
                callback = CustomJS.from_coffeescript(code=js_code, args={})
                toggle = Toggle(label="Hide legend", button_type="success", callback=callback,
                                active=True, width=widget_width)
                callback.args = {'toggle': toggle, 'legends': legends, 'figures':figures}
                js_widgets.append(toggle)
                msg = "{} Legend on/off toggle |".format(msg)
    
    
            if "legend_position" in js_type and "legend" in kwargs:
                legend = kwargs["legend"]
                js_code = '''\
                position = dropdown.value;
                legend.location = position;
                legend.visible = true;
                figure.change.emit();
                console.log('Legend position: ' + position);
                '''
                callback = CustomJS(code=js_code, args={})
                menu = [("Top left", "top_left"), ("Top right", "top_right"),
                        ("Bottom left", "bottom_left"), ("Bottom right", "bottom_right")]
                dropdown = Dropdown(menu=menu, callback=callback, label="Legend position",
                                    width=widget_width)
    
                callback.args = {'dropdown': dropdown, 'legend':legend, 'figure':bokehPlot}
                js_widgets.append(dropdown)
                msg = "{} Legend position dropdown |".format(msg)
    
            if "legend_orientation" in js_type and "legend" in kwargs:
                legend = kwargs["legend"]
                js_code = '''\
                if (radio.active == 0) {
                    legend.orientation = 'vertical';
                    console.log('Legend orientation: vertical');
                    }
                else if (radio.active == 1) {
                    legend.orientation = 'horizontal';
                    console.log('Legend orientation: horizontal');
                    }
                figure.change.emit();
                '''
                callback = CustomJS(code=js_code, args={})
                if user_kwargs["legend_properties"].get(
                    "legend_orientation", self.config.interactive_legend_orientation) == "vertical":
                    active_mode = 0
                else:
                    active_mode = 1
    
                group = RadioButtonGroup(labels=["      Legend: vertical      ",
                                                 "     Legend: horizontal    "],
                                         active=active_mode, callback=callback,
                                         width=widget_width)
                callback.args = {'radio': group, 'legend':legend, 'figure':bokehPlot}
                js_widgets.append(group)
                msg = "{} Legend orientation toggle |".format(msg)
    
            if "legend_transparency" in js_type and "legend" in kwargs:
                legend = kwargs["legend"]
                js_code = '''\
                transparency = slider.value;
                legend.background_fill_alpha = transparency;
                figure.change.emit();
                console.log('Legend transparency: ' + transparency);
                '''
                callback = CustomJS(code=js_code, args={})
                slider = Slider(start=0, end=1, step=0.1,
                                value=user_kwargs["legend_properties"].get(
                                    "legend_background_alpha", self.config.interactive_legend_background_alpha),
                                callback=callback, title="Legend transparency",
                                width=widget_width)
                callback.args = {'slider': slider, 'legend':legend, 'figure':bokehPlot}
                js_widgets.append(slider)
                msg = "{} Legend transparency slider |".format(msg)
    
            if "legend_transparency_multi" in js_type and "legends" in kwargs:
                legends = kwargs["legends"]
                figures = kwargs["figures"]
                js_code = '''\
                transparency = slider.value;
                for j, i in legends
                    [legend, figure] = [legends[i], figures[i]];
                    legend.background_fill_alpha = transparency;
                    figure.change.emit();
                    
                console.log('Legend transparency: ' + transparency);
                '''
                callback = CustomJS(code=js_code, args={})
                slider = Slider(start=0, end=1, step=0.1,
                                value=user_kwargs["legend_properties"].get(
                                    "legend_background_alpha", self.config.interactive_legend_background_alpha),
                                callback=callback, title="Legend transparency",
                                width=widget_width)
                callback.args = {'slider': slider, 'legends':legends, 'figures':figures}
                js_widgets.append(slider)
                msg = "{} Legend transparency slider |".format(msg)
    
            if "colorblind_safe_1D" in js_type and "lines" in kwargs:
                lines = kwargs["lines"]
                patches = kwargs.get("patches", [])
                cvd_colors = kwargs['cvd_colors']
                original_colors = kwargs['original_colors']
                if len(patches) != len(lines):
                    js_code = '''\
                    if toggle.active
                        for line, i in lines
                            line.glyph.line_color = original_colors[i];
                        toggle.label = "Show in colorblind mode";
                        console.log('Colors set to: normal mode');
                    else 
                        for line, i in lines
                            line.glyph.line_color = cvd_colors[i];
                        toggle.label = "Show in normal mode"
                        console.log 'Colors set to: colorblind friendly mode'
                    figure.change.emit()
                    '''
                else:
                    js_code = '''\
                    if toggle.active
                        for line, i in lines
                            line.glyph.line_color = original_colors[i];
                        for patch, i in patches
                            patch.glyph.fill_color = original_colors[i];
                        toggle.label = "Show in colorblind mode"
                        console.log 'Colors set to: normal mode'
                    else
                        for line, i in lines
                            line.glyph.line_color = cvd_colors[i];
                        for patch, i in patches
                            patch.glyph.fill_color = cvd_colors[i];
                        toggle.label = "Show in normal mode"
                        console.log 'Colors set to: colorblind friendly mode'
                    figure.change.emit()
                    '''
                callback = CustomJS.from_coffeescript(code=js_code, args={})
                toggle = Toggle(label="Show in colorblind mode", button_type="success",
                                callback=callback, active=True, width=widget_width)
                callback.args = {'toggle': toggle, 'figure':bokehPlot, 'lines': lines, 'patches':patches,
                                 'cvd_colors':cvd_colors, 'original_colors':original_colors}
                js_widgets.append(toggle)
                msg = "{} Colorblind toggle |".format(msg)
    
            if "colorblind_safe_1D_multi" in js_type and "lines" in kwargs:
                lines = kwargs["lines"]
                patches = kwargs.get("patches", [])
                cvd_colors = kwargs['cvd_colors']
                original_colors = kwargs['original_colors']
                figures = kwargs['figures']
                js_code = '''\
                if toggle.active
                    for _, i in lines
                        [line_list, patch_list, color_list] = [lines[i], patches[i], original_colors[i]]
                        for _, j in line_list
                            [line, patch, color] = [line_list[j], patch_list[j], color_list[j]]
                            line.glyph.line_color = color;
                            patch.glyph.fill_color = color;
    
                    toggle.label = "Show in colorblind mode"
                    console.log 'Colors set to: normal mode'
                else
                    for _, i in lines
                        [line_list, patch_list, color_list] = [lines[i], patches[i], cvd_colors[i]]
                        for _, j in line_list
                            [line, patch, color] = [line_list[j], patch_list[j], color_list[j]]
                            line.glyph.line_color = color;
                            patch.glyph.fill_color = color;
    
                    toggle.label = "Show in normal mode"
                    console.log 'Colors set to: colorblind friendly mode'
    
                for figure in figures
                    figure.change.emit()
                '''
                callback = CustomJS.from_coffeescript(code=js_code, args={})
                toggle = Toggle(label="Show in colorblind mode", button_type="success",
                                callback=callback, active=True, width=widget_width)
                callback.args = {'toggle': toggle, 'figures':figures, 'lines': lines, 'patches':patches,
                                 'cvd_colors':cvd_colors, 'original_colors':original_colors}
                js_widgets.append(toggle)
                msg = "{} Colorblind toggle |".format(msg)
    
            if "colorblind_safe_scatter" in js_type and "scatters" in kwargs:
                scatters = kwargs["scatters"]
                cvd_colors = kwargs['cvd_colors']
                fill_colors = kwargs['fill_colors']
                edge_colors = kwargs['edge_colors']
                js_code = '''\
                if toggle.active
                    for scatter, i in scatters
                        scatter.glyph.fill_color = fill_colors[i];
                        scatter.glyph.line_color = edge_colors[i];
                    toggle.label = "Show in colorblind mode"
                    console.log 'Colors set to: normal mode'
                else
                    for scatter, i in scatters
                        scatter.glyph.fill_color = cvd_colors[i];
                        scatter.glyph.line_color = "#000000";
                    toggle.label = "Show in normal mode"
                    console.log 'Colors set to: colorblind friendly mode'
                figure.change.emit()
                '''
                callback = CustomJS.from_coffeescript(code=js_code, args={})
                toggle = Toggle(label="Show in colorblind mode", button_type="success",
                                callback=callback, active=True, width=widget_width)
                callback.args = {'toggle': toggle, 'figure':bokehPlot, 'scatters': scatters,
                                 'cvd_colors':cvd_colors, 'fill_colors':fill_colors, 'edge_colors':edge_colors}
                js_widgets.append(toggle)
                msg = "{} Colorblind toggle |".format(msg)
    
            if "colorblind_safe_2D" in js_type and "images" in kwargs:
                images = kwargs["images"]
                colorbars = kwargs.get("colorbars", None)
                cvd_colors = kwargs['cvd_colors']
                original_colors = kwargs['original_colors']
                if colorbars is None or colorbars[0] is None:
                    js_code = '''\
                    if toggle.active
                        for image, i in images
                            console.log original_colors[i]
                            image.glyph.color_mapper = original_colors[i];
                        toggle.label = "Show in colorblind mode"
                        console.log 'Colormap set to: normal mode'
                    else
                        for image, i in images
                            image.glyph.color_mapper = cvd_colors[i];
                        toggle.label = "Show in normal mode"
                        console.log 'Colormap set to: colorblind friendly mode'
                    figure.change.emit()
                    '''
                else:
                    js_code = '''\
                    if toggle.active
                        for image, i in images
                            image.glyph.color_mapper = original_colors[i];
                        for colorbar, i in colorbars
                            colorbar.color_mapper = original_colors[i];
                        toggle.label = "Show in colorblind mode"
                        console.log 'Colormap set to: normal mode'
                    else
                        for image, i in images
                            image.glyph.color_mapper = cvd_colors[i];
                        for colorbar, i in colorbars
                            colorbar.color_mapper = cvd_colors[i];
                        toggle.label = "Show in normal mode"
                        console.log 'Colormap set to: colorblind friendly mode'
                    figure.change.emit()
                    '''
                callback = CustomJS.from_coffeescript(code=js_code, args={})
                toggle = Toggle(label="Show in colorblind mode", button_type="success",
                                callback=callback, active=True, width=widget_width)
                callback.args = {'toggle': toggle, 'figure':bokehPlot, 'images': images,
                                 'colorbars':colorbars, 'cvd_colors':cvd_colors, 'original_colors':original_colors}
                js_widgets.append(toggle)
                msg = "{} Colorblind toggle |".format(msg)
    
            if "colormap_change" in js_type and "images" in kwargs:
                images = kwargs["images"]
                colorbars = kwargs.get("colorbars", [])
                colormaps = kwargs['colormaps']
                colormap_names = kwargs['colormap_names']
                js_code = '''\
                i = parseInt(dropdown.value, 10);
                console.log colormaps[i];
                for image in images
                    image.glyph.color_mapper = colormaps[i];
                for cbar in colorbars
                    cbar.color_mapper = colormaps[i];
    
                figure.change.emit();
                console.log 'Changed colormap', cbar
                '''
                callback = CustomJS.from_coffeescript(code=js_code, args={})
                menu = [("{}".format(colormap_names[0]), "0"), ("{}".format(colormap_names[1]), "1"),
                        ("{}".format(colormap_names[2]), "2"), ("{}".format(colormap_names[3]), "3")]
                dropdown = Dropdown(menu=menu, callback=callback, label="Colormap selection",
                                    width=widget_width)
    
                callback.args = {'dropdown': dropdown, 'colormaps':colormaps,
                                 'figure':bokehPlot, 'images': images, 'colorbars':colorbars}
                js_widgets.append(dropdown)
                msg = "{} Colormap dropdown |".format(msg)
    
            if "scatter_size" in js_type and "scatters" in kwargs:
                scatters = kwargs['scatters']
                js_code = '''\
                scatter_size = slider.value;
                for scatter, i in scatters
                    scatter.glyph.size = scatter_size;
                figure.change.emit();
                console.log 'Scatter size: ' + scatter_size;
                '''
                callback = CustomJS.from_coffeescript(code=js_code, args={})
                slider = Slider(start=1, end=100, step=1, value=self.config.interactive_scatter_size,
                                callback=callback, title="Scatter size",
                                width=widget_width)
                callback.args = {'slider': slider, 'scatters':scatters, 'figure':bokehPlot}
                js_widgets.append(slider)
                msg = "{} Scatter size slider |".format(msg)
    
            if "scatter_transparency" in js_type and "scatters" in kwargs:
                scatters = kwargs['scatters']
                js_code = '''\
                scatter_alpha = slider.value;
                for scatter, i in scatters
                    scatter.glyph.line_alpha = scatter_alpha;
                    scatter.glyph.fill_alpha = scatter_alpha;
                figure.change.emit();
                console.log 'Scatter transparency: ' + scatter_alpha;
                '''
                callback = CustomJS.from_coffeescript(code=js_code, args={})
                slider = Slider(start=0, end=1, step=0.1, value=self.config.interactive_scatter_alpha,
                                callback=callback, title="Scatter transparency",
                                width=widget_width)
                callback.args = {'slider': slider, 'scatters':scatters, 'figure':bokehPlot}
                js_widgets.append(slider)
                msg = "{} Scatter size slider |".format(msg)
    
            if "plot_size" in js_type:
                js_code = '''\
                width = slider_width.value;
                height = slider_height.value;
                figure.plot_width = width;
                figure.plot_height = height;
                figure.change.emit();
                console.log 'Plot width: ' + width + ' height: ' + height;
                '''
                callback = CustomJS.from_coffeescript(code=js_code, args={})
                slider_width = Slider(start=100, end=1000, step=50, value=kwargs['plot_width'],
                                      callback=callback, title="Plot width")
                slider_height = Slider(start=100, end=1000, step=50, value=kwargs['plot_height'],
                                      callback=callback, title="Plot height")
                callback.args = {'slider_width': slider_width,
                                 'slider_height': slider_height,
                                 'figure':bokehPlot}
                js_widgets.append(slider_width)
                js_widgets.append(slider_height)
                msg = "{} Plot size sliders |".format(msg)
    
            
            # add controls to the plot at specified position
            if position == "right":
                bokehPlot = row(bokehPlot, widgetbox(js_widgets))
            elif position == "left":
                bokehPlot = row(widgetbox(js_widgets), bokehPlot)
            elif position == "top_row":
                bokehPlot = bokeh_layout([js_widgets, bokehPlot])
            elif position == "top_column":
                bokehPlot = bokeh_layout([widgetbox(js_widgets), bokehPlot])
            elif position == "bottom_row":
                bokehPlot = bokeh_layout([bokehPlot, js_widgets])
            elif position == "bottom_column":
                bokehPlot = bokeh_layout([bokehPlot, widgetbox(js_widgets)])
                
            
                
            msg = "{}. It took {:.3f} seconds".format(msg[:-2], (time.time() - tstart))
            self.presenter.onThreading(None, (msg, 4), action='updateStatusbar')
        except Exception, e:
            print(e)
#         except RuntimeError:
            msg = "ORIGAMI encountered an error when compiling custom JavaScript widgets. There are a few things you can do to fix this.\n" + \
                  "1) Disable JavaScript widgets/events in the Annotations tab. OR\n" + \
                  "2) Go to ORIGAMI's working directory and use attached JavaScript installer \n" + \
                  "   (node-v10.14.1-x64.msi)\n" + \
                  "   Execute the script and either restart ORIGAMI or close the Interactive panel and try again OR\n" + \
                  "3) Go to https://nodejs.org/en/download/ and download the latest version of JavaScript installer \n" + \
                  "   and execute same steps as in the above option.\n\n" + \
                  "ORIGAMI directory: {}".format(self.config.cwd)

            dialogs.dlgBox(exceptionTitle='No JavaScript available',
                           exceptionMsg= msg,
                           type="Error")
            self.config.interactive_custom_scripts = False
            self.custom_js_scripts.SetValue(False)

        # return plot with widgets
        return bokehPlot

    def add_custom_js_events(self, bokehPlot, js_type="double_tap_unzoom", **kwargs):
        """
        Add custoom JS scripts to plots
        bokehPlot    figure    bokeh figure
        js_type     list    list of types of java script tools to be added
        """

        try:
            tstart = time.time()
            msg = "Added JS events: "
            if not isinstance(js_type, list):
                js_type = [js_type]

#             hover = kwargs['hover']
#             js_code = """\
#             console.log 'PanStart';
#             hover.active = false;
#             """
#             bokehPlot.js_on_event(events.PanStart, CustomJS.from_coffeescript(code=js_code, args={"figure":bokehPlot,
#                                                                                                   "hover":hover}))


            if "double_tap_unzoom" in js_type:
                # TODO: add support to programatically disable hover tool
                # figure.toolbar.active_inspect.active = false;
                # figure.change.emit()
                # figure.toolbar.active_inspect.active = true;
                # look here: https://groups.google.com/a/continuum.io/forum/#!topic/bokeh/_xtHNgab45o

                js_code = '''\
                console.log('Resetting zoom');
                figure.reset.emit();
                '''

                bokehPlot.js_on_event(events.DoubleTap, CustomJS.from_coffeescript(code=js_code, args={"figure":bokehPlot}))
                msg = "{} Double tap = unzoom |".format(msg)

            msg = "{}. It took {:.3f} seconds".format(msg[:-2], (time.time() - tstart))
            self.presenter.onThreading(None, (msg, 4), action='updateStatusbar')
        except RuntimeError:
            msg = "ORIGAMI encountered an error when compiling custom JavaScript widgets. There are a few things you can do to fix this.\n" + \
                  "1) Disable JavaScript widgets/events in the Annotations tab. OR\n" + \
                  "2) Go to ORIGAMI's working directory and use attached JavaScript installer \n" + \
                  "   (node-v10.14.1-x64.msi).\n" + \
                  "   Execute the script and either restart ORIGAMI or close the Interactive panel and try again OR\n" + \
                  "3) Go to https://nodejs.org/en/download/ and download the latest version of JavaScript installer \n" + \
                  "   and execute same steps as in the above option.\n\n" + \
                  "ORIGAMI directory: {}".format(self.config.cwd)

            dialogs.dlgBox(exceptionTitle='No JavaScript available',
                           exceptionMsg=msg,
                           type="Error")
            self.config.interactive_custom_events = False
            self.custom_js_events.SetValue(False)
        # return plot
        return bokehPlot

#     def _add_legend(self, plot, location=(0, 0), orientation="horizontal", side="above"):
#         legend = Legend(
#             items=[("line", [line]), ("circle", [circle])],
#             location=location, orientation=orientation,
#             border_line_color="black",
#             )
#         plot.add_layout(legend, side)

    def _prepare_annotations(self, data, yvals=None, y_offset=0, ylimits=None):
        user_kwargs = deepcopy(data['interactive_params'])
        
        if yvals is not None:
            __, ylimits = find_limits_all(yvals, yvals)
        
        annot_xmin_list, annot_xmax_list, annot_ymin_list, annot_ymax_list, color_list = [], [], [], [], []
        text_annot_xpos, text_annot_ypos, text_annot_label, text_annot_color = [], [], [], []
        arrow_xpos_start, arrow_xpos_end, arrow_ypos_start, arrow_ypos_end = [], [], [], []
        text_annot_xpos_start, text_annot_ypos_start = [], []
        quad_source, label_source, arrow_source = None, None, None

        # get color
        label_use_preset_color = user_kwargs["annotation_properties"].get("label_use_preset_color", True)
        label_color = convertRGB1toHEX(user_kwargs["annotation_properties"].get("label_color", self.config.interactive_ms_annotations_line_color))
                                          
        # add annotations iteratively
        for i, annotKey in enumerate(data['annotations']):
            # add patches
            if user_kwargs["annotation_properties"].get(
                "show_patches", self.config.interactive_ms_annotations_highlight):
                annot_xmin_list.append(data['annotations'][annotKey]["min"])
                annot_xmax_list.append(data['annotations'][annotKey]["max"])
                annot_ymin_list.append(0)
                annot_ymax_list.append(ylimits[1] + y_offset)
                color_list.append(convertRGB1toHEX(data['annotations'][annotKey].get("color", data.get("interactive_params", {}).get(
                    "annotation_properties", {}).get("label_color", self.config.interactive_ms_annotations_line_color))))

            # add labels
            if user_kwargs["annotation_properties"].get(
                "show_labels", self.config.interactive_ms_annotations_labels):
                # determine position of the ion/peak
                if 'isotopic_x' in data['annotations'][annotKey]:
                    mz_value = data['annotations'][annotKey]['isotopic_x']
                else:
                    mz_value = data['annotations'][annotKey]["max"] - (data['annotations'][annotKey]["max"] - data['annotations'][annotKey]["min"]) / 2.
                    
                if 'isotopic_y' in data['annotations'][annotKey]:
                    intensity = data['annotations'][annotKey]['isotopic_y']
                else:
                    intensity = data['annotations'][annotKey]["intensity"]
                
                xpos = data['annotations'][annotKey].get('position_label_x', mz_value)
                ypos = data['annotations'][annotKey].get('position_label_y', intensity)
                
                text_annot_xpos.append(xpos)
                text_annot_ypos.append(ypos + y_offset)
                
                if label_use_preset_color:
                    label_color = convertRGB1toHEX(data['annotations'][annotKey].get("color", user_kwargs[
                        "annotation_properties"].get("label_color", self.config.interactive_ms_annotations_line_color)))
                text_annot_color.append(label_color)
                
                

                # determine position of arrow (if any)
                if data['annotations'][annotKey].get('add_arrow', False):
                    xpos_start = data['annotations'][annotKey].get('position_label_x', xpos)
                    ypos_start = data['annotations'][annotKey].get('position_label_y', ypos)
                else: xpos_start, ypos_start = xpos, ypos

                # if either xpos or ypos not equal position of the peak then we are not
                # adding arrow
                if xpos_start != xpos or ypos_start != ypos:
                     arrow_xpos_start.append(xpos_start)
                     arrow_xpos_end.append(xpos)
                     arrow_ypos_start.append(ypos_start)
                     arrow_ypos_end.append(ypos)
                     # replace x/ypos of the label
                     text_annot_xpos[-1] = xpos_start
                     text_annot_ypos[-1] = ypos_start

                # label
                if data['annotations'][annotKey]["label"] not in ["", None]:
                    label = u"{}".format(_replace_labels(data['annotations'][annotKey]["label"]))
                else:
                    label = u"{}".format(data['annotations'][annotKey]["charge"])
                text_annot_label.append(label)

                # check if need to add arrow
                if data['annotations'][annotKey].get('add_arrow', False):
                    xpos_start = data['annotations'][annotKey].get('position_label_x', xpos)
                    ypos_start = data['annotations'][annotKey].get('position_label_y', ypos)
                    if xpos_start == xpos and ypos_start == ypos: continue
                    text_annot_xpos_start.append(xpos_start)
                    text_annot_ypos_start.append(ypos_start)


        if user_kwargs["annotation_properties"].get(
            "show_patches", self.config.interactive_ms_annotations_highlight):
            quad_source = ColumnDataSource(data=dict(top=annot_ymax_list,
                                                     bottom=annot_ymin_list,
                                                     left=annot_xmin_list,
                                                     right=annot_xmax_list,
                                                     color=color_list
                                                     ))
        if user_kwargs["annotation_properties"].get(
            "show_labels", self.config.interactive_ms_annotations_labels):
            ylimits[1] = max(text_annot_ypos) * 2
            label_source = ColumnDataSource(data=dict(xpos=text_annot_xpos,
                                                      ypos=text_annot_ypos,
                                                      label=text_annot_label,
                                                      color=text_annot_color))

        if len(text_annot_xpos_start) > 0 and len(text_annot_ypos_start) > 0:
            arrow_source = ColumnDataSource(data=dict(xpos_start=arrow_xpos_start,
                                                      ypos_start=arrow_ypos_start,
                                                      xpos_end=arrow_xpos_end,
                                                      ypos_end=arrow_ypos_end))

        return quad_source, label_source, arrow_source

    def _buildPlotParameters(self, data):
        # get parameters
        interactive_params = deepcopy(data.get('interactive_params', {}))

        hover_vline = interactive_params['line_linkXaxis']
        line_width = interactive_params['line_width']
        line_alpha = interactive_params['line_alpha']
        line_style = interactive_params['line_style']
        overlay_layout = interactive_params['overlay_layout']
        overlay_linkXY = interactive_params['overlay_linkXY']
        legend = interactive_params['legend']
        title_label = interactive_params.get('title_label', "")
        xpos = interactive_params.get('grid_xpos', self.config.interactive_grid_xpos)
        ypos = interactive_params.get('grid_ypos', self.config.interactive_grid_ypos)
        waterfall_increment = interactive_params.get('waterfall_increment', self.config.interactive_waterfall_increment)
        waterfall_shade = interactive_params.get('waterfall_shade_under', False)
        waterfall_shade_transparency = interactive_params.get('waterfall_shade_transparency', 0.25)
        overlay_shade = interactive_params.get('overlay_1D_shade_under', False)
        overlay_shade_transparency = interactive_params.get('overlay_1D_shade_transparency', 0.25)
        linearize_spectra = interactive_params.get('linearize_spectra', self.config.interactive_ms_linearize)
        show_annotations = interactive_params.get('show_annotations', self.config.interactive_ms_annotations)
        bin_size = interactive_params.get('bin_size', self.config.interactive_ms_binSize)
        plot_width = interactive_params.get("plot_width", self.config.figWidth)
        plot_height = interactive_params.get("plot_height", self.config.figHeight)
        _xlimits_ = interactive_params.get("xlimits", None)
        _ylimits_ = interactive_params.get("ylimits", None)

        # Check if we should lock the hoverline
        if hover_vline: hoverMode = 'vline'
        else: hoverMode = 'mouse'

        plt_kwargs = {'hover_mode':hoverMode, 
                      'line_width':line_width,
                      'line_alpha':line_alpha,
                      'line_style':line_style,
                      'overlay_layout':overlay_layout,
                      'overlay_linkXY':overlay_linkXY,
                      'add_legend':legend,
                      'title_label':title_label,
                      'xpos':xpos, 'ypos':ypos,
                      'waterfall_increment':waterfall_increment,
                      'linearize_spectra':linearize_spectra,
                      'show_annotations':show_annotations,
                      'bin_size':bin_size,
                      'waterfall_shade':waterfall_shade,
                      'waterfall_shade_transparency':waterfall_shade_transparency,
                      'overlay_shade':overlay_shade,
                      'overlay_shade_transparency':overlay_shade_transparency,
                      'plot_width':plot_width,
                      'plot_height':plot_height,
                      '_xlimits_':_xlimits_,
                      '_ylimits_':_ylimits_,
                      }

        return plt_kwargs

    def _setupPlotParameters(self, bokehPlot, data={}, plot_type="1D", **kwargs):

        if "xlimits" in kwargs:
            bokehPlot.x_range.start = kwargs['xlimits'][0]
            bokehPlot.x_range.end = kwargs['xlimits'][1]

        if "ylimits" in kwargs:
            bokehPlot.y_range.start = kwargs['ylimits'][0]
            bokehPlot.y_range.end = kwargs['ylimits'][1]

        # common
        bokehPlot.title.text_font_size = self._fontSizeConverter(data.get("interactive_params", {}).get(
            "frame_properties", {}).get("title_fontsize", self.config.interactive_title_fontSize))
        bokehPlot.title.text_font_style = self._fontWeightConverter(data.get("interactive_params", {}).get(
            "frame_properties", {}).get("title_fontweight", self.config.interactive_title_weight))

        if data.get("interactive_params", {}).get("frame_properties", {}).get(
            "gridline", self.config.interactive_grid_line):
            bokehPlot.grid.grid_line_color = convertRGB1toHEX(
                data.get("interactive_params", {}).get("frame_properties", {}).get(
                    "gridline_color", self.config.interactive_grid_line_color))

        bokehPlot.background_fill_color = convertRGB1toHEX(
            data.get("interactive_params", {}).get("frame_properties", {}).get(
                    "background_color", self.config.interactive_background_color))

        set_common_parameters = []
        if plot_type == "1D":
            set_common_parameters = ['label', 'frame', 'border']

        elif plot_type == "Scatter":
            set_common_parameters = ['legend', 'label', 'frame', 'border']

        elif plot_type == "Waterfall":
            set_common_parameters = ['legend', 'label', 'frame', 'border']

        elif plot_type == "Waterfall_overlay":
            set_common_parameters = ['legend', 'label', 'frame', 'border']

        elif plot_type == "Overlay_1D":
            set_common_parameters = ['legend', 'label', 'frame', 'border']

        elif plot_type == "2D":
            set_common_parameters = ['label', 'frame', 'border']

        elif plot_type == "Matrix":
            # X-axis
            bokehPlot.xaxis.major_label_orientation = data.get(
                "interactive_params", {}).get("overlay_properties", {}).get(
                    "rmsd_matrix_xaxis_rotation", 120) * 0.0174533
            bokehPlot.xaxis.major_label_standoff = 10
            # Y-axis
            bokehPlot.grid.grid_line_color = None
            bokehPlot.axis.axis_line_color = None
            bokehPlot.axis.major_tick_line_color = None

            set_common_parameters = ['label', 'frame', 'border']

        elif plot_type == "RMSF":
            # Add border
            bokehPlot.outline_line_width = data.get(
                    "interactive_params", {}).get("frame_properties", {}).get(
                        "outline_width", self.config.interactive_outline_width)
            bokehPlot.outline_line_alpha = data.get(
                "interactive_params", {}).get("frame_properties", {}).get(
                    "outline_alpha", self.config.interactive_outline_alpha)

            bokehPlot.outline_line_color = data.get(
                "interactive_params", {}).get("frame_properties", {}).get(
                    "outline_color", "#000000")
            # Y-axis
            bokehPlot.yaxis.axis_label_text_font_size = self._fontSizeConverter(self.config.interactive_label_fontSize)
            bokehPlot.yaxis.major_label_text_font_size = self._fontSizeConverter(self.config.interactive_tick_fontSize)
            bokehPlot.yaxis.axis_label_text_font_style = self._fontWeightConverter(self.config.interactive_label_weight)
            # X-axis
            bokehPlot.xaxis.axis_label_text_font_size = "0pt"
            bokehPlot.xaxis.major_label_text_font_size = "0pt"

        for param in set_common_parameters:
            if param == "label":
                # set label parameters
                bokehPlot.xaxis.axis_label_text_font_size = self._fontSizeConverter(
                    data.get("interactive_params", {}).get("frame_properties", {}).get(
                        "label_xaxis_fontsize", self.config.interactive_label_fontSize))
                bokehPlot.xaxis.axis_label_text_font_style = self._fontWeightConverter(
                    data.get("interactive_params", {}).get("frame_properties", {}).get(
                        "label_fontweight", self.config.interactive_label_weight))

                bokehPlot.yaxis.axis_label_text_font_size = self._fontSizeConverter(
                    data.get("interactive_params", {}).get("frame_properties", {}).get(
                        "label_yaxis_fontsize", self.config.interactive_label_fontSize))
                bokehPlot.yaxis.axis_label_text_font_style = self._fontWeightConverter(
                    data.get("interactive_params", {}).get("frame_properties", {}).get(
                        "label_fontweight", self.config.interactive_label_weight))

            if param in ["frame", "ticks"]:
                # set tick parameters
                bokehPlot.xaxis.major_tick_line_color = data.get(
                    "interactive_params", {}).get("frame_properties", {}).get(
                        "ticks_xaxis_color", "#000000")
                bokehPlot.xaxis.minor_tick_line_color = data.get(
                    "interactive_params", {}).get("frame_properties", {}).get(
                        "ticks_xaxis_color", "#000000")
                bokehPlot.yaxis.major_tick_line_color = data.get(
                    "interactive_params", {}).get("frame_properties", {}).get(
                        "ticks_yaxis_color", "#000000")
                bokehPlot.yaxis.minor_tick_line_color = data.get(
                    "interactive_params", {}).get("frame_properties", {}).get(
                        "ticks_yaxis_color", "#000000")
                bokehPlot.xaxis.major_label_text_font_size = self._fontSizeConverter(
                    data.get("interactive_params", {}).get("frame_properties", {}).get(
                        "tick_labels_xaxis_fontsize", self.config.interactive_tick_fontSize))
                bokehPlot.yaxis.major_label_text_font_size = self._fontSizeConverter(
                    data.get("interactive_params", {}).get("frame_properties", {}).get(
                        "tick_labels_yaxis_fontsize", self.config.interactive_tick_fontSize))

                

            if param in ["legend"]:
                bokehPlot.legend.location = data.get(
                    "interactive_params", {}).get("legend_properties", {}).get(
                        "legend_location", self.config.interactive_legend_location)
                bokehPlot.legend.click_policy = data.get(
                    "interactive_params", {}).get("legend_properties", {}).get(
                        "legend_click_policy", self.config.interactive_legend_click_policy)
                bokehPlot.legend.background_fill_alpha = data.get(
                    "interactive_params", {}).get("legend_properties", {}).get(
                        "legend_background_alpha", self.config.interactive_legend_background_alpha)
                bokehPlot.legend.border_line_alpha = data.get(
                    "interactive_params", {}).get("legend_properties", {}).get(
                        "legend_background_alpha", self.config.interactive_legend_background_alpha)
                bokehPlot.legend.label_text_font_size = self._fontSizeConverter(data.get(
                    "interactive_params", {}).get("legend_font_size", {}).get(
                        "legend_location", self.config.interactive_legend_font_size))
                bokehPlot.legend.orientation = data.get(
                    "interactive_params", {}).get("legend_properties", {}).get(
                        "legend_orientation", self.config.interactive_legend_orientation)
                bokehPlot.legend.border_line_width = 0

            if param in ["border"]:
                # add outline
                bokehPlot.outline_line_width = data.get(
                    "interactive_params", {}).get("frame_properties", {}).get(
                        "outline_width", self.config.interactive_outline_width)

                bokehPlot.outline_line_alpha = data.get(
                    "interactive_params", {}).get("frame_properties", {}).get(
                        "outline_alpha", self.config.interactive_outline_alpha)

                bokehPlot.outline_line_color = data.get(
                    "interactive_params", {}).get("frame_properties", {}).get(
                        "outline_color", "#000000")
                    
                # add borders
                bokehPlot.min_border_right = data.get(
                    "interactive_params", {}).get("frame_properties", {}).get(
                        "border_left", self.config.interactive_border_min_right)
                bokehPlot.min_border_left = data.get(
                    "interactive_params", {}).get("frame_properties", {}).get(
                        "border_right", self.config.interactive_border_min_left)
                bokehPlot.min_border_top = data.get(
                    "interactive_params", {}).get("frame_properties", {}).get(
                        "border_top", self.config.interactive_border_min_top)
                bokehPlot.min_border_bottom = data.get(
                    "interactive_params", {}).get("frame_properties", {}).get(
                        "border_bottom", self.config.interactive_border_min_bottom)

                if kwargs.get("tight_layout", False):
                    bokehPlot.min_border_right = 10
                    bokehPlot.min_border_left = 10
                    bokehPlot.min_border_top = 10
                    bokehPlot.min_border_bottom = 10

        # add custom javascript
        if self.config.interactive_custom_events:
#             try:
#
            bokehPlot = self.add_custom_js_events(bokehPlot, js_type=["double_tap_unzoom"], **kwargs)
#             except: pass
        return bokehPlot

#     def _prepare_centroid_annotations(self, data, yvals, y_offset=0):
#         
#         __, ylimits = find_limits_all(yvals, yvals)
#         text_annot_xpos, text_annot_ypos, text_annot_label = [], [], []
#         arrow_xpos_start, arrow_xpos_end, arrow_ypos_start, arrow_ypos_end = [], [], [], []
#         text_annot_xpos_start, text_annot_ypos_start = [], []
# 
# #         # add annotations iteratively
# #         for i, annotKey in enumerate(data['annotations']):
# #             
# #             # add labels
# #             if user_kwargs["annotation_properties"].get(
# #                 "show_labels", self.config.interactive_ms_annotations_labels):
# #                 # determine position of the ion/peak
# #                 if 'isotopic_x' in data['annotations'][annotKey]:
# #                     xpos = data['annotations'][annotKey]['isotopic_x']
# #                 else:
# #                     xpos = data['annotations'][annotKey]["max"] - (data['annotations'][annotKey]["max"] - data['annotations'][annotKey]["min"]) / 2.
# #                 text_annot_xpos.append(xpos)
# # 
# #                 if 'isotopic_y' in data['annotations'][annotKey]:
# #                     ypos = data['annotations'][annotKey]['isotopic_y']
# #                 else:
# #                     ypos = data['annotations'][annotKey]["intensity"]
# #                 text_annot_ypos.append(ypos + y_offset)
# # 
# #                 # determine position of arrow (if any)
# #                 if data['annotations'][annotKey].get('add_arrow', False):
# #                     xpos_start = data['annotations'][annotKey].get('position_label_x', xpos)
# #                     ypos_start = data['annotations'][annotKey].get('position_label_y', ypos)
# #                 else: xpos_start, ypos_start = xpos, ypos
# # 
# #                 # if either xpos or ypos not equal position of the peak then we are not
# #                 # adding arrow
# #                 if xpos_start != xpos or ypos_start != ypos:
# #                      arrow_xpos_start.append(xpos_start)
# #                      arrow_xpos_end.append(xpos)
# #                      arrow_ypos_start.append(ypos_start)
# #                      arrow_ypos_end.append(ypos)
# #                      # replace x/ypos of the label
# #                      text_annot_xpos[-1] = xpos_start
# #                      text_annot_ypos[-1] = ypos_start
# # 
# #                 # label
# #                 if data['annotations'][annotKey]["label"] not in ["", None]:
# #                     label = u"{}".format(_replace_labels(data['annotations'][annotKey]["label"]))
# #                 else:
# #                     label = u"{}".format(data['annotations'][annotKey]["charge"])
# #                 text_annot_label.append(label)
# # 
# #                 # check if need to add arrow
# #                 if data['annotations'][annotKey].get('add_arrow', False):
# #                     xpos_start = data['annotations'][annotKey].get('position_label_x', xpos)
# #                     ypos_start = data['annotations'][annotKey].get('position_label_y', ypos)
# #                     if xpos_start == xpos and ypos_start == ypos: continue
# #                     text_annot_xpos_start.append(xpos_start)
# #                     text_annot_ypos_start.append(ypos_start)
# 
#         if user_kwargs["annotation_properties"].get(
#             "show_labels", self.config.interactive_ms_annotations_labels):
#             ylimits[1] = max(text_annot_ypos) * 2
#             label_source = ColumnDataSource(data=dict(xpos=text_annot_xpos,
#                                                       ypos=text_annot_ypos,
#                                                       label=text_annot_label))
# 
#         return label_source

    def _prepare_centroid_data(self, xvals_raw, xvals_lab, data, color_labelled, color_unlabelled):
        """
        Generate colors, labels and details about annotations in a MSMS file
        ===
        xvals_raw:    list / numpy.array
            list of x-axis values (m/z)
        xvals_lab:    list / numpy.array
            list of x-axis values (m/z) of the annotations
        data:    dict
            dataset with annotation inforation: peptide, charge, label, measured_mz, calculated_mz, ...
        """
        
        # unpack
        xvals_raw = list(xvals_raw)
        
        # get index of labelled items
        match_index = []
        for mz_lab in xvals_lab:
            match_index.append(xvals_raw.index(mz_lab))
        
        # xvals, yvals, labels, colors, details
        mz_list_size = len(xvals_raw)
        
        labels = [""] * mz_list_size
        details = deepcopy(labels)
        item_colors = [color_unlabelled] *  mz_list_size
        for i in match_index:
            item_colors[i] = color_labelled
            mz_value = xvals_raw[i]
            detail_label = "{}; z={}; error={} Da".format(
                data[mz_value][0]['peptide'],
                data[mz_value][0]['charge'],
                data[mz_value][0]['delta_mz'])
            details[i] = detail_label
            labels[i] = data[mz_value][0]['label']
            
        return item_colors, labels, details
    
    def _prepare_centroid_title(self, scanID, title):
        """
        Generate html text for div
        """
        
        html_title = "<p><strong>ID: </strong>{}</p> <p><strong>Title: </strong>{}</p>".format(
            scanID, title)
        
        return html_title
        
    def _add_plot_centroid_without_annotations(self, data, **bkh_kwargs):
        plt_kwargs = self._buildPlotParameters(data)
        user_kwargs = deepcopy(data['interactive_params'])
        
        # temporary limit
        hard_limit = 500
        
        # collect data
        xvals_list, yvals_list, options_list = [], [], []
        annotated_ms_list, title_list = [], []
        i = 0
        for key in data:
            # skip keys that are forbidden 
            if "Scan " not in key: 
                continue
            if i >= hard_limit: 
                break
            # plot data
            xvals_list.append(data[key]['xvals'])
            yvals_list.append(data[key]['yvals'])
            options_list.append(str(i))
            html_title = self._prepare_centroid_title(key, data[key]['scan_info']['title'])
            title_list.append(html_title)
            annotated_ms_list.append(i)
            i += 1
            
        # create source data
        source_list = ColumnDataSource(dict(
            xvals_list=xvals_list,
            yvals_list=yvals_list,
            title_list=title_list,
            ))
        
        
        source = ColumnDataSource(dict(
            xvals=xvals_list[0],
            yvals=yvals_list[0],
            ))
        
        # Prepare hover tool
        hoverTool = HoverTool(tooltips=[("m/z", '@xvals{0.00}'),
                                        ("Intensity", '@yvals{0.00}'),
                                        ], mode="mouse")
        TOOLS = self._check_tools(hoverTool, data)
        if user_kwargs['tools'].get("active_inspect", "auto") == "hover": inspect_tool = hoverTool
        else: inspect_tool = user_kwargs['tools'].get("active_inspect", "auto")
        
        # create figure
        bokehPlot = figure(
            tools=TOOLS,
            title=bkh_kwargs["title"],
            active_drag=user_kwargs['tools'].get("active_drag", "auto"),
            active_scroll=user_kwargs['tools'].get("active_wheel", "auto"),
            active_inspect=inspect_tool,
            plot_width=plt_kwargs['plot_width'],
            plot_height=plt_kwargs['plot_height'],
            toolbar_location=user_kwargs['tools'].get("position", self.config.toolsLocation),
            toolbar_sticky=False)
        
        # add plot
        bokehPlot.segment(
            x0="xvals", y0=0, x1="xvals", y1="yvals", line_color="#000000",
            line_width=user_kwargs['plot_properties']['tandem_line_width'], 
            source=source)
    
    
        # setup labels
        bokehPlot.xaxis.axis_label = "m/z"
        bokehPlot.yaxis.axis_label = "Intensity"

        # generate js kwargs
        setup_kwargs = dict(hover=hoverTool)
        
        # setup common plot parameters
        bokehPlot = self._setupPlotParameters(bokehPlot, plot_type="1D", data=data, **setup_kwargs)
    
        # create div for scan information
        divHeader = Div(text=title_list[0])

        # generate javascript widget
        js_widgets = []
        js_code = '''
        // get data
        var list_data = source_list.data;
        var plot_data = source.data;
        
        // convert value to integer
        i = parseInt(cb_obj.value, 10);
        
        // retrieve data from list 
        var xvals = list_data['xvals_list'][i];
        var yvals = list_data['yvals_list'][i];
        var title = list_data['title_list'][i];
        
        // report title
        console.log("Spectrum title: " + title_list[i]);
        div.text = title;
        
        // replace data and trigger replot
        plot_data['xvals'] = xvals;
        plot_data['yvals'] = yvals;
        
        source.change.emit();
        '''
        
        callback = CustomJS(code=js_code, 
                            args={'figure':bokehPlot, 'source':source, 
                                  'source_list':source_list, 
                                  'title_list':annotated_ms_list,
                                  'div':divHeader})
        
        toggle = Select(title="Dataset (id):", value="0", options=options_list, callback=callback)
        js_widgets.append(toggle)
        
        # arrange
        bokehPlot = row(bokehPlot, column(widgetbox(js_widgets), divHeader))
                
        return [bokehPlot, plt_kwargs['plot_width'], plt_kwargs['plot_height']]
        
    def _add_plot_centroid_with_annotations(self, data, **bkh_kwargs):
        plt_kwargs = self._buildPlotParameters(data)
        user_kwargs = deepcopy(data['interactive_params'])
        
        annotated_ms_list = data.get("annotated_item_list", [])
        if len(annotated_ms_list) == 0:
            return 
        
        # convert colors
        color_labelled = convertRGB1toHEX(user_kwargs["plot_properties"]["tandem_line_color_labelled"])
        color_unlabelled = convertRGB1toHEX(user_kwargs["plot_properties"]["tandem_line_color_unlabelled"])
        
        
        # sort list
        annotated_ms_list = natsorted(annotated_ms_list)
        
#         print(tandem_data.keys(), tandem_data['charges'], tandem_data['identification'])
        
        # collect data
        xvals_list, yvals_list, options_list = [], [], []
        item_colors_list, item_labels_list, item_details_list, title_list = [], [], [], []
        for i, key in enumerate(annotated_ms_list):
            # plot data
            xvals_list.append(data[key]['xvals'])
            yvals_list.append(data[key]['yvals'])
            options_list.append(str(i))
            
            item_colors, labels, details = self._prepare_centroid_data(
                data[key]['xvals'],
                data[key]['fragment_annotations']['fragment_mass_list'],
                data[key]['fragment_annotations']['fragment_table'], 
                color_labelled, color_unlabelled)
            item_colors_list.append(item_colors)
            item_labels_list.append(labels)
            item_details_list.append(details)
            html_title = self._prepare_centroid_title(key, data[key]['scan_info']['title'])
            title_list.append(html_title)
            
        # create source data
        source_list = ColumnDataSource(dict(
            xvals_list=xvals_list,
            yvals_list=yvals_list,
            colors_frag_list=item_colors_list,
            labels_frag_list=item_labels_list,
            details_frag_list=item_details_list,
            title_list=title_list,
            ))
        
        
        source = ColumnDataSource(dict(
            xvals=xvals_list[0],
            yvals=yvals_list[0],
            colors=item_colors_list[0], 
            label=item_labels_list[0], 
            details=item_details_list[0], 
            ))
        
        # Prepare hover tool
        hoverTool = HoverTool(tooltips=[("m/z", '@xvals{0.00}'),
                                        ("Intensity", '@yvals{0.00}'),
                                        ("Label", "@label"),
                                        ("Details", "@details")
                                        ], mode="mouse")
        TOOLS = self._check_tools(hoverTool, data)
        if user_kwargs['tools'].get("active_inspect", "auto") == "hover": inspect_tool = hoverTool
        else: inspect_tool = user_kwargs['tools'].get("active_inspect", "auto")
        
        # create figure
        bokehPlot = figure(
            tools=TOOLS,
            title=bkh_kwargs["title"],
            active_drag=user_kwargs['tools'].get("active_drag", "auto"),
            active_scroll=user_kwargs['tools'].get("active_wheel", "auto"),
            active_inspect=inspect_tool,
            plot_width=plt_kwargs['plot_width'],
            plot_height=plt_kwargs['plot_height'],
            toolbar_location=user_kwargs['tools'].get("position", self.config.toolsLocation),
            toolbar_sticky=False)
        
        # add plot
        bokehPlot.segment(
            x0="xvals", y0=0, x1="xvals", y1="yvals", line_color="colors",
            line_width=user_kwargs['plot_properties']['tandem_line_width'], 
            source=source)
    
    
        # setup labels
        bokehPlot.xaxis.axis_label = "m/z"
        bokehPlot.yaxis.axis_label = "Intensity"

        # generate js kwargs
        setup_kwargs = dict(hover=hoverTool)
        
        # setup common plot parameters
        bokehPlot = self._setupPlotParameters(bokehPlot, plot_type="1D", data=data, **setup_kwargs)
    
        # create div for scan information
#         text = self._prepare_centroid_title(annotated_ms_list[0], data[annotated_ms_list[0]]['scan_info']['title'])
        divHeader = Div(text=title_list[0]) #("<p><strong>Current ID: {}<br /></strong></p>".format(annotated_ms_list[0])))

        # generate javascript widget
        js_widgets = []
        js_code = '''
        // get data
        var list_data = source_list.data;
        var plot_data = source.data
        
        // convert value to integer
        i = parseInt(cb_obj.value, 10);
        
        // retrieve data from list 
        var xvals = list_data['xvals_list'][i];
        var yvals = list_data['yvals_list'][i];
        var colors = list_data['colors_frag_list'][i];
        var labels = list_data['labels_frag_list'][i];
        var details = list_data['details_frag_list'][i];
        var title = list_data['title_list'][i];
        
        // report title
        console.log("Spectrum title: " + title_list[i]);
        div.text = title;
        //div.text = "<p><strong>Current ID: " + title_list[i] + "<br /></strong></p>";
        
        // replace data and trigger replot
        plot_data['xvals'] = xvals;
        plot_data['yvals'] = yvals;
        plot_data['colors'] = colors;
        plot_data['labels'] = labels;
        plot_data['details'] = details;
        
        source.change.emit();
        '''
        
        callback = CustomJS(code=js_code, 
                            args={'figure':bokehPlot, 'source':source, 
                                  'source_list':source_list, 
                                  'title_list':annotated_ms_list,
                                  'div':divHeader})
        
        toggle = Select(title="Dataset (id):", value="0", options=options_list, callback=callback)
        js_widgets.append(toggle)
        
        
        # arrange
        bokehPlot = row(bokehPlot, column(widgetbox(js_widgets), divHeader))
                
        return [bokehPlot, plt_kwargs['plot_width'], plt_kwargs['plot_height']]

    def _add_plot_1D(self, data, **bkh_kwargs):
        """
        """
        plt_kwargs = self._buildPlotParameters(data)
        user_kwargs = deepcopy(data['interactive_params'])
        
        xvals, yvals, xlabel, cmap = self.presenter.get2DdataFromDictionary(dictionary=data,
                                                                            plotType='1D',
                                                                            dataType='plot',
                                                                            compact=False)
        ylabel = data['ylabel']
        # check xlabel
        if xlabel == []:
            try: xlabel = data['xlabel']
            except: xlabel = ""

        # unpack if embedded in a list
        if len(xvals) == 1: xvals = xvals[0]
        if len(yvals) == 1: yvals = yvals[0]

        if bkh_kwargs.get("test_x_axis", False):
            xvals, xlabel, __ = self._kda_test(xvals)

        if cmap == "":
            cmap = [0, 0, 0]

        # Prepare hover tool
        if bkh_kwargs['plot_type'] in ['MS', 'MS, multiple', 'RT', 'RT, multiple', '1D', '1D, multiple']:
            _tooltips = [(xlabel, '@xvals{0.00}'),
                         (ylabel, '@yvals{0.00}')]
            itemLabels = []
        elif bkh_kwargs['plot_type'] == "Other 1D":
            _tooltips = [(xlabel, '@xvals{0.00}'),
                         (ylabel, '@yvals{0.00}')]
            itemLabels = data['itemLabels']
            hoverLabels = data['hover_labels']
            for i in xrange(len(itemLabels)):
                try: hover_label = hoverLabels[i]
                except: hover_label = "Label ({})".format(i)
                _tooltips.append((hover_label, '@labels_{}'.format(i)))

        # create tooltip
        hoverTool = HoverTool(
            tooltips=_tooltips,
            mode=user_kwargs["plot_properties"].get("hover_mode", "mouse"),
            names=["plot"])

        # downsample
        if (user_kwargs["preprocessing_properties"]["linearize"] and
            len(xvals) > user_kwargs["preprocessing_properties"].get("linearize_limit", 25000)):
            xvals, yvals = self.linearize_spectrum(
                xvals, yvals, user_kwargs["preprocessing_properties"]["linearize_binsize"])

        # check x/y limits
        xlimits = [min(xvals), max(xvals)]
        xlimits = self._check_limits(xlimits, plt_kwargs['_xlimits_'])
        ylimits = [min(yvals), max(yvals) * 1.05]
        ylimits = self._check_limits(ylimits, plt_kwargs['_ylimits_'])

        # crop data with xlimits in mind
        if plt_kwargs['_xlimits_'] is not None and bkh_kwargs['plot_type'] != "Other 1D":
            try:
                kwargs = {'min':xlimits[0], 'max':xlimits[1]}
                xvals, yvals = crop_1D_data(xvals, yvals, **kwargs)
            except: pass

        # check if annotations should prepared
        if ("annotations" in data and len(data["annotations"]) > 0 and
            user_kwargs["preprocessing_properties"].get("show_annotations", True)):
            quad_source, label_source, arrow_source = self._prepare_annotations(data, yvals)

        # generate source data
        _sourceDict = dict(xvals=xvals, yvals=yvals)
        if len(itemLabels) > 0:
            for ilabel in xrange(len(itemLabels)):
                dict_label = "labels_{}".format(ilabel)
                if len(itemLabels[ilabel]) == len(xvals):
                    _labels = itemLabels[ilabel]
                else:
                    _labels = len(xvals) * [""]
                _sourceDict[dict_label] = _labels

        ms_source = ColumnDataSource(data=_sourceDict)

        # prepare tools
        TOOLS = self._check_tools(hoverTool, data)
        if user_kwargs['tools'].get("active_inspect", "auto") == "hover":
            inspect_tool = hoverTool
        else:
            inspect_tool = user_kwargs['tools'].get("active_inspect", "auto")

        # create figure
        bokehPlot = figure(
            x_range=xlimits, y_range=ylimits,
            tools=TOOLS,
            title=bkh_kwargs["title"],
            active_drag=user_kwargs['tools'].get("active_drag", "auto"),
            active_scroll=user_kwargs['tools'].get("active_wheel", "auto"),
            active_inspect=inspect_tool,
            plot_width=plt_kwargs['plot_width'],
            plot_height=plt_kwargs['plot_height'],
            toolbar_location=user_kwargs['tools'].get("position", self.config.toolsLocation),
            toolbar_sticky=False)

        # add line plot
        cmap = convertRGB1toHEX(user_kwargs["plot_properties"].get("line_color", cmap))
        line = bokehPlot.line(
            "xvals", "yvals", source=ms_source,
            line_color=cmap,
            line_width=user_kwargs["plot_properties"]["line_transparency"],
            line_dash=user_kwargs["plot_properties"]["line_style"],
            line_alpha=user_kwargs["plot_properties"]["line_transparency"],
            name="plot")
        _lines, _patches = [line], []

        # add patch
        if user_kwargs["plot_properties"].get("line_shade_under", False):
                patch = bokehPlot.patch(
                    "xvals", "yvals", color=cmap,
                    fill_alpha=user_kwargs["plot_properties"].get("shade_transparency", self.config.interactive_line_alpha),
                    line_alpha=0.,
                    source=ms_source)
                _patches = [patch]

        # setup labels
        bokehPlot.xaxis.axis_label = xlabel
        bokehPlot.yaxis.axis_label = ylabel

        # generate js kwargs
        js_kwargs = dict(xlimits=xlimits, ylimits=ylimits, hover=hoverTool)
        # setup common plot parameters
        bokehPlot = self._setupPlotParameters(bokehPlot, plot_type="1D", data=data, **js_kwargs)

        # add labels, patches and arrows
        labels = None
        if "annotations" in data and len(data["annotations"]) > 0 and user_kwargs["annotation_properties"].get(
                "show_annotations", plt_kwargs['show_annotations']):
            if user_kwargs["annotation_properties"].get(
                "show_patches", self.config.interactive_ms_annotations_highlight):
                bokehPlot.quad(
                    top="top", bottom="bottom", left="left", right="right", color="color",
                    fill_alpha=user_kwargs["annotation_properties"].get(
                        "patch_transparency", self.config.interactive_ms_annotations_transparency),
                    source=quad_source,
                    name="ignore_hover")

            if user_kwargs["annotation_properties"].get("show_labels", self.config.interactive_ms_annotations_labels):
                bokehPlot, labels = self._add_plot_labels(bokehPlot, data, label_source)

                if arrow_source is not None:
                    bokehPlot, __ = self._add_plot_arrows(bokehPlot, data, arrow_source)

        # setup widgets
        if user_kwargs["widgets"].get("add_custom_widgets", self.config.interactive_custom_scripts):
            js_type, js_code = [], {}

            if user_kwargs["widgets"].get("hover_mode", True):
                js_code.update(hover=hoverTool)
                js_type.extend(["hover_mode"])

            if user_kwargs["widgets"].get("colorblind_safe_1D", True):
                _original_colors = [cmap]
                _cvd_colors = self.presenter.view.panelPlots.onChangePalette(
                    None, cmap=self.config.interactive_cvd_cmap, n_colors=len(_lines),
                    return_colors=True, return_hex=True)
                js_code.update(lines=_lines, original_colors=_original_colors,
                               cvd_colors=_cvd_colors, patches=_patches)
                js_type.extend(["colorblind_safe_1D"])

            if labels is not None:
                js_code.update(labels=labels, y_range_shown=ylimits[1], y_range_hidden=ylimits[1] / 2, y_range_x1=ylimits[1] / 2)
                if user_kwargs["widgets"].get("label_toggle", True): js_type.extend(["label_toggle"])
                if user_kwargs["widgets"].get("label_size_slider", True): js_type.extend(["label_size_slider"])
                if user_kwargs["widgets"].get("label_rotation", True): js_type.extend(["label_rotation"])
                if user_kwargs["widgets"].get("label_offset_x", True): js_type.extend(["label_offset_x"])
                if user_kwargs["widgets"].get("label_offset_y", True): js_type.extend(["label_offset_y"])

            try: bokehPlot = self.add_custom_js_widgets(bokehPlot, js_type=js_type, data=data, **js_code)
            except: pass

        return [bokehPlot, plt_kwargs['plot_width'], plt_kwargs['plot_height']]

#     def _add_plot_compare_1D(self, data, **bkh_kwargs):
#         """
#         Comparison plot when one of the plots is inversed
#         """
#         plt_kwargs = self._buildPlotParameters(data)
#         user_kwargs = deepcopy(data['interactive_params'])
# 
#         # unpack data
#         xvals = data['xvals']
#         yvals = data['yvals']
#         xlabel = data['xlabel']
#         ylabel = data['ylabel']
#         line_colors = data['colors']
#         labels = data['labels']
# 
#         # Prepare hover tool
#         hoverTool = HoverTool(tooltips=[(xlabel, '@xvals{0.00}'),
#                                           (ylabel, '@yvals{0.00}'),
#                                           ("Label", "@label")],
#                               mode=plt_kwargs['hover_mode'])
#         # Prepare MS file
#         TOOLS = self._check_tools(hoverTool, data)
# 
#         xlimits, ylimits = find_limits_all(xvals, yvals)
#         xlimits = self._check_limits(xlimits, plt_kwargs['_xlimits_'])
# 
#         bokehPlot = figure(x_range=xlimits, y_range=ylimits,
#                            tools=TOOLS, title=bkh_kwargs['title'],
#                            active_drag=user_kwargs['tools'].get("active_drag", "auto"),
#                            active_scroll=user_kwargs['tools'].get("active_wheel", "auto"),
#                            plot_width=plt_kwargs["plot_width"],
#                            plot_height=plt_kwargs["plot_height"],
#                            toolbar_location=user_kwargs['tools'].get("position", self.config.toolsLocation),
#                            toolbar_sticky=False)
# 
#         ms_source = ColumnDataSource(data=dict(xvals=xvals[0], yvals=yvals[0]))
#         color_1 = convertRGB1toHEX(line_colors[0])
#         line_1 = bokehPlot.line("xvals", "yvals", source=ms_source,
#                                 line_color=color_1,
#                                 line_width=user_kwargs["plot_properties"]["line_width"],
#                                 line_dash=user_kwargs["plot_properties"]["line_style"],
#                                 line_alpha=user_kwargs["plot_properties"]["line_transparency"],
#                                 name="plot")
# 
#         ms_source = ColumnDataSource(data=dict(xvals=xvals[0], yvals=-yvals[0]))
#         color_2 = convertRGB1toHEX(line_colors[0])
#         line_2 = bokehPlot.line("xvals", "yvals", source=ms_source,
#                                 line_color=color_2,
#                                 line_width=user_kwargs["plot_properties"]["line_width"],
#                                 line_dash=user_kwargs["plot_properties"]["line_style"],
#                                 line_alpha=user_kwargs["plot_properties"]["line_transparency"],
#                                 name="plot")
# 
#         bokehPlot = self._setupPlotParameters(bokehPlot, plot_type="1D", data=data)
#         return [bokehPlot, plt_kwargs['plot_width'], plt_kwargs['plot_height']]

    def _add_plot_overlay_1D(self, data, **bkh_kwargs):
        plt_kwargs = self._buildPlotParameters(data)
        user_kwargs = deepcopy(data['interactive_params'])

        # unpack data
        xvals = data['xvals']
        yvals = data['yvals']
        xlabel = data['xlabel']
        ylabel = data['ylabel']
        line_colors = data['colors']
        labels = data['labels']

        xlabel = _replace_labels(xlabel)
        ylabel = _replace_labels(ylabel)

        # Prepare hover tool
        hoverTool = HoverTool(tooltips=[(xlabel, '@xvals{0.00}'),
                                          (ylabel, '@yvals{0.00}'),
                                          ("Label", "@label")],
                              mode=plt_kwargs['hover_mode'])

        TOOLS = self._check_tools(hoverTool, data)


        xlimits, ylimits = find_limits_all(xvals, yvals)
        xlimits = self._check_limits(xlimits, plt_kwargs['_xlimits_'])
        ylimits = self._check_limits(ylimits, plt_kwargs['_ylimits_'])

        bokehPlot = figure(x_range=xlimits, y_range=ylimits,
                           tools=TOOLS, title=bkh_kwargs['title'],
                           active_drag=user_kwargs['tools'].get("active_drag", "auto"),
                           active_scroll=user_kwargs['tools'].get("active_wheel", "auto"),
                           plot_width=plt_kwargs["plot_width"],
                           plot_height=plt_kwargs["plot_height"],
                           toolbar_location=user_kwargs['tools'].get("position", self.config.toolsLocation),
                           toolbar_sticky=False
                           )

        # check in case only one item was passed
        # assumes xvals is a list in a list
        if len(xvals) != len(yvals) and len(xvals) == 1:
            xvals = xvals * len(yvals)

        # create dataframe
        _lines, _patches, _original_colors = [], [], []
        for xval, yval, color, label in zip(xvals, yvals, line_colors, labels):
            if plt_kwargs['_xlimits_'] is not None:
                try:
                    kwargs = {'min':xlimits[0], 'max':xlimits[1]}
                    xval, yval = crop_1D_data(xval, yval, **kwargs)
                except: pass

            if (user_kwargs["preprocessing_properties"]["linearize"] and
                len(xval) > user_kwargs["preprocessing_properties"].get("linearize_limit", 25000)):
                # TODO: implement better downsampling
                # downsampling: https://github.com/devoxi/lttb-py/blob/master/lttb/lttb.py
                xval, yval = self.linearize_spectrum(
                    xval, yval, user_kwargs["preprocessing_properties"]["linearize_binsize"])

            try: color = convertRGB1toHEX(color)
            except (SyntaxError, ValueError): pass
            source = ColumnDataSource(data=dict(xvals=xval,
                                                yvals=yval,
                                                label=([_replace_labels(label)] * len(xval))))
            if not user_kwargs["legend_properties"].get("legend", plt_kwargs['add_legend']):
                label = None
            else:
                label = _replace_labels(label)
            line = bokehPlot.line(
                x="xvals", y="yvals",
                line_color=color,
                line_width=user_kwargs["plot_properties"]["line_width"],
                line_alpha=user_kwargs["plot_properties"]["line_transparency"],
                line_dash=user_kwargs["plot_properties"]["line_style"],
                legend=label,
                muted_alpha=user_kwargs["legend_properties"].get("legend_mute_alpha", self.config.interactive_legend_mute_alpha),
                muted_color=color,
                source=source)
            _lines.append(line)
            _original_colors.append(color)
            
            if plt_kwargs['overlay_shade']:
                patch = bokehPlot.patch(
                    "xvals", "yvals", color=color,
                    fill_alpha=plt_kwargs['overlay_shade_transparency'],
                    line_alpha=0., source=source,
                    legend=label)
                _patches.append(patch)
                
        if ("annotations" in data and len(data["annotations"]) > 0 and 
            user_kwargs["annotation_properties"].get("show_annotations", plt_kwargs['show_annotations'])):
            __, label_source, __ = self._prepare_annotations(data, yvals)
            bokehPlot, labels = self._add_plot_labels(bokehPlot, data, label_source, plot_type="waterfall")

        # setup labelss
        bokehPlot.xaxis.axis_label = xlabel
        bokehPlot.yaxis.axis_label = ylabel
        # setup common parameters
        bokehPlot = self._setupPlotParameters(bokehPlot, plot_type="Overlay_1D", data=data)

        plot_mods = {}
        if user_kwargs["widgets"].get("add_custom_widgets", self.config.interactive_custom_scripts) and bkh_kwargs['page_layout'] in ["Individual", "Columns"]:
            js_type, js_code = [], {}
            if user_kwargs["widgets"].get("hover_mode", True):
                js_code.update(hover=hoverTool)
                js_type.extend(["hover_mode"])

            if user_kwargs["widgets"].get("colorblind_safe_1D", True):
                _cvd_colors = self.presenter.view.panelPlots.onChangePalette(None, cmap=self.config.interactive_cvd_cmap,
                                                                            n_colors=len(_lines),
                                                                            return_colors=True, return_hex=True)
                js_code.update(lines=_lines, original_colors=_original_colors, cvd_colors=_cvd_colors,
                               patches=_patches)
                js_type.extend(["colorblind_safe_1D"])

            if user_kwargs["legend_properties"].get("legend", plt_kwargs['add_legend']) and len(bokehPlot.legend) > 0:
                js_code.update(legend=bokehPlot.legend[0])

                if user_kwargs["widgets"].get("legend_toggle", True):
                    js_type.extend(["legend_toggle"])
                if user_kwargs["widgets"].get("legend_position", True):
                    js_type.extend(["legend_position"])
                if user_kwargs["widgets"].get("legend_orientation", True):
                    js_type.extend(["legend_orientation"])
                if user_kwargs["widgets"].get("legend_transparency", True):
                    js_type.extend(["legend_transparency"])

            try: bokehPlot = self.add_custom_js_widgets(bokehPlot, js_type=js_type, data=data, **js_code)
            except: pass
        elif self.config.interactive_custom_scripts and bkh_kwargs['page_layout'] not in ["Individual", "Columns"]:
            _cvd_colors = self.presenter.view.panelPlots.onChangePalette(None, cmap=self.config.interactive_cvd_cmap, n_colors=len(_lines),
                                                                         return_colors=True, return_hex=True)
            plot_mods.update(lines=_lines, original_colors=_original_colors, cvd_colors=_cvd_colors,
                             patches=_patches)
            self.presenter.onThreading(None, ("Adding widgets to 'Grid'/'Rows' is not supported at the moment." , 4),
                                       action='updateStatusbar')

        return [bokehPlot, plt_kwargs['plot_width'], plt_kwargs['plot_height'], plot_mods]

    def _add_plot_scatter(self, data, **bkh_kwargs):
        plt_kwargs = self._buildPlotParameters(data)
        user_kwargs = deepcopy(data['interactive_params'])

        # get data
        xvals = data['xvals']
        yvals = data['yvals']
        xlabel = _replace_labels(data['xlabel'])
        ylabel = _replace_labels(data['ylabel'])
        labels = data['labels']
        colors_list = data['colors']
        plot_modifiers = data["plot_modifiers"]
        legend_labels = plot_modifiers["legend_labels"]
        itemColors = data["itemColors"]
        itemLabels = data["itemLabels"]
        xvalsErr = data['xvalsErr']
        yvalsErr = data['yvalsErr']
        hoverLabels = data.get('hover_labels', [])
        urls = data.get('urls', [])

        # Prepare hover tool
        _tooltips = [(xlabel, '@xvals{0.00}'),
                     (ylabel, '@yvals{0.00}')]
        if len(xvalsErr) == len(yvals):
            _tooltips.append(("Error (x)", '@xvalsErr{0.00}'))
            plot_modifiers["bokeh_add_xerror"] = True
        if len(yvalsErr) == len(yvals):
            _tooltips.append(("Error (y)", '@yvalsErr{0.00}'))
            plot_modifiers["bokeh_add_yerror"] = True
#             if len(labels) == len(yvals):
#                 _tooltips.append(("Dataset", '@labels'))
#                 plot_modifiers["bokeh_add_dataset_label"] = True
        if plot_modifiers.get("label_items", False):
            if len(itemLabels) > len(yvals):
                for i in xrange(len(itemLabels)):
                    try: hover_label = hoverLabels[i]
                    except: hover_label = "Label ({})".format(i)
                    _tooltips.append((_replace_labels(hover_label), '@labels_{}'.format(i)))
            elif len(itemLabels) == len(yvals):
                i = 0
                try: hover_label = hoverLabels[i]
                except: hover_label = "Label"
                _tooltips.append((_replace_labels(hover_label), '@labels_{}'.format(i)))
            plot_modifiers["bokeh_add_item_label"] = True

        # prepare tools
        hoverTool = HoverTool(tooltips=_tooltips, mode='mouse')
        # create tools
        TOOLS = self._check_tools(hoverTool, data)
        # add tap tool for url action
        TOOLS.extend(["tap"])

        # create figure
        bokehPlot = figure(tools=TOOLS,
                           title=bkh_kwargs["title"],
                           active_drag=user_kwargs['tools'].get("active_drag", "auto"),
                           active_scroll=user_kwargs['tools'].get("active_wheel", "auto"),
                           plot_width=plt_kwargs["plot_width"],
                           plot_height=plt_kwargs["plot_height"],
                           toolbar_location=user_kwargs['tools'].get("position", self.config.toolsLocation),
                           toolbar_sticky=False)

        # add plots
        add_tap_url = False
        _scatter, _colors, _edge_colors = [], [], []
        for i in range(len(yvals)):
            yval = yvals[i]
            yval_size = len(yval)
            # if multiple xvals are provided - extract one for each yvals
            if len(xvals) == len(yvals): xval = xvals[i]
            else: xval = xvals[0]
            
            # get urls
            if len(urls) == len(yvals): url = urls[i]
            else: url = urls[0]
            
            if len(url) == yval_size:
                add_tap_url = True

            # check if individual colors are provided
            if len(itemColors) > 0:
                if len(itemColors) == len(yvals):
                    color = self._convert_color_list(itemColors[i])
                else:
                    color = self._convert_color_list(itemColors[0])
            else:
                try: color = convertRGB1toHEX(colors_list[i])
                except: color = colors_list[i]

            # create edge colors
            if user_kwargs['plot_properties'].get(
                "scatter_edge_color_sameAsFill", self.config.interactive_scatter_sameAsFill):
                edge_color = color
            else:
                edge_color = convertRGB1toHEX(user_kwargs['plot_properties'].get(
                    "scatter_edge_color", self.config.interactive_scatter_edge_color))

            # generate color list
            if len(color) != yval_size:
                color = [color] * yval_size
            if len(edge_color) != yval_size:
                edge_color = [edge_color] * yval_size

            # create source
            _sourceDict = dict(xvals=xval, yvals=yval, color=color, edge_color=edge_color)
            if plot_modifiers.get("bokeh_add_xerror", False) and len(xvalsErr[i]) == yval_size:
                _sourceDict["xvalsErr"] = xvalsErr[i]

            if plot_modifiers.get("bokeh_add_yerror", False) and len(yvalsErr[i]) == yval_size:
                _sourceDict["yvalsErr"] = yvalsErr[i]

            if plot_modifiers.get("bokeh_add_dataset_label", False):
                _sourceDict["labels"] = [labels[i]] * yval_size

            if plot_modifiers.get("bokeh_add_item_label", False):
                if len(itemLabels) > len(yvals):
                    for ilabel in xrange(len(itemLabels)):
                        dict_label = "labels_{}".format(ilabel)
                        _sourceDict[dict_label] = itemLabels[ilabel]
                elif len(itemLabels) == len(yvals):
                    _sourceDict["labels_0"] = itemLabels[i]
                else:
                    _sourceDict["labels_0"] = itemLabels[0]
                    
            if add_tap_url:
                _sourceDict["urls"] = url
                
            if len(legend_labels) == len(yvals):
                label = legend_labels[i]
            else:
                try: label = labels[i]
                except: label = " "
            source = ColumnDataSource(data=_sourceDict)
            scatter = bokehPlot.scatter(
                x="xvals", y="yvals",
                color="color", line_color="edge_color",
                marker=user_kwargs['plot_properties'].get("scatter_shape", self.config.interactive_scatter_marker),
                fill_alpha=user_kwargs['plot_properties'].get("scatter_transparency", self.config.interactive_scatter_alpha),
                size=user_kwargs['plot_properties'].get("scatter_size", self.config.interactive_scatter_size),
                line_width=user_kwargs['plot_properties'].get("scatter_line_width", self.config.interactive_scatter_lineWidth),
                muted_alpha=user_kwargs['legend_properties'].get("legend_mute_alpha", self.config.interactive_legend_mute_alpha),
                source=source,
                legend=label)
            
            # add tap tool
            if add_tap_url:
                print("Added tap -> URL tool")
                taptool = bokehPlot.select(type=TapTool)
                jscode = """
                var select_id = cb_data.source.selected['1d'].indices[0];
                var url_data = source.data['urls'];
                var url = url_data[select_id];
                if (url !== "nan") { window.open(url); }
                else { console.log("URL address was missing"); }
                """
                url_callback = CustomJS(args=dict(source=source), code=jscode)
                taptool.callback = url_callback
            
            _scatter.append(scatter)
            _colors.append(color[0])
            _edge_colors.append(edge_color[0])
            
        # add annotations
        if ("annotations" in data and len(data["annotations"]) > 0 and 
            user_kwargs["annotation_properties"].get("show_annotations", plt_kwargs['show_annotations'])):
            __, label_source, __ = self._prepare_annotations(data, yvals)
            bokehPlot, labels = self._add_plot_labels(bokehPlot, data, label_source, plot_type="waterfall")

        # setup labels
        bokehPlot.xaxis.axis_label = xlabel
        bokehPlot.yaxis.axis_label = ylabel
        # modify plot
        bokehPlot = self._setupPlotParameters(bokehPlot, data=data, plot_type="Scatter")
        
        # add widgets
        if (user_kwargs["widgets"].get("add_custom_widgets", self.config.interactive_custom_scripts) and
            bkh_kwargs['page_layout'] in ["Individual", "Columns"]):
            _cvd_colors = self.presenter.view.panelPlots.onChangePalette(None, cmap=self.config.interactive_cvd_cmap,
                                                                        n_colors=len(_scatter),
                                                                        return_colors=True, return_hex=True)
            js_type, js_code = [], {}
            if user_kwargs["widgets"].get("hover_mode", True):
                js_code.update(hover=hoverTool)
                js_type.extend(["hover_mode"])
                
            if user_kwargs["widgets"].get("colorblind_safe_scatter", True):
                js_code.update(fill_colors=_colors, edge_colors=_edge_colors, cvd_colors=_cvd_colors, scatters=_scatter)
                js_type.extend(["colorblind_safe_scatter"])

            if user_kwargs["widgets"].get("scatter_size", True):
                js_code.update(scatters=_scatter)
                js_type.extend(["scatter_size"])
            if user_kwargs["widgets"].get("scatter_transparency", True):
                js_code.update(scatters=_scatter)
                js_code.update(hover=hoverTool)
                js_type.extend(["scatter_transparency"])

            if user_kwargs["legend_properties"].get("legend", plt_kwargs['add_legend']) and len(bokehPlot.legend) > 0:
                js_code.update(legend=bokehPlot.legend[0])
                if user_kwargs["widgets"].get("legend_toggle", True):
                    js_type.extend(["legend_toggle"])
                if user_kwargs["widgets"].get("legend_position", True):
                    js_type.extend(["legend_position"])
                if user_kwargs["widgets"].get("legend_orientation", True):
                    js_type.extend(["legend_orientation"])
                if user_kwargs["widgets"].get("legend_transparency", True):
                    js_type.extend(["legend_transparency"])

            if len(js_type) > 0:
                try: bokehPlot = self.add_custom_js_widgets(bokehPlot, js_type=js_type, data=data, **js_code)
                except: pass
                
        elif (user_kwargs["widgets"].get("add_custom_widgets", self.config.interactive_custom_scripts) and
              bkh_kwargs['page_layout'] not in ["Individual", "Columns"]):
            self.presenter.onThreading(None, ("Adding widgets to 'Grid'/'Rows' is not supported at the moment." , 4),
                                       action='updateStatusbar')

        return [bokehPlot, plt_kwargs['plot_width'], plt_kwargs['plot_height']]

    def _add_plot_2D(self, data, **bkh_kwargs):
        plt_kwargs = self._buildPlotParameters(data)
        user_kwargs = deepcopy(data['interactive_params'])

        # Unpacks data using a helper function
        zvals, xvals, xlabel, yvals, ylabel, cmap = self.presenter.get2DdataFromDictionary(
            dictionary=data, dataType='plot', plotType='2D', compact=False)

        # test x-axis
        if bkh_kwargs.get("test_x_axis", False):
            xvals, xlabel, __ = self._kda_test(xvals)

        try:
            shape = zvals.shape[1]
            if shape > user_kwargs['preprocessing_properties'].get("subsample_limit", 20000):
                shape = True
            else: shape = False
        except:
            shape = True
            
        # reshape array to ro reduce size
        if (user_kwargs['preprocessing_properties'].get("subsample", bkh_kwargs.get("reshape_array", False))
            and shape):
            xlen = len(xvals)
            ylen = len(yvals)
            zvals = np.transpose(np.reshape(zvals, (xlen, ylen)))
            if zvals.shape[1] > user_kwargs['preprocessing_properties'].get("subsample_limit", 20000):
                print("Have to subsample the grid as it is too big...")
                zvals = zvals[:,::user_kwargs['preprocessing_properties'].get("subsample_frequency", 20)].copy()

        # generate image data
        z_data = dict(image=[zvals], x=[min(xvals)], y=[min(yvals)],
                      dw=[max(xvals) - min(xvals)],
                      dh=[max(yvals) - min(yvals)])
        cds = ColumnDataSource(data=z_data)

        # get colormapper and palette
        cmap = user_kwargs['plot_properties'].get("colormap", cmap)
        colorMapper, bokehpalette = self._convert_cmap_to_colormapper(cmap, zvals=zvals, return_palette=True)
        # create tooltip
        hoverTool = HoverTool(tooltips=[
            (xlabel, '$x{0.00}'), (ylabel, '$y{0.00}'),
            ('Intensity', '@image')],
                              point_policy='follow_mouse')

        # check tools
        TOOLS = self._check_tools(hoverTool, data)

        # create figure
        bokehPlot = figure(x_range=(min(xvals), max(xvals)),
                           y_range=(min(yvals), max(yvals)),
                           tools=TOOLS,
                           # title=bkh_kwargs["title"],
                           active_drag=user_kwargs['tools'].get("active_drag", "auto"),
                           active_scroll=user_kwargs['tools'].get("active_wheel", "auto"),
                           plot_width=plt_kwargs["plot_width"],
                           plot_height=plt_kwargs["plot_height"],
                           toolbar_location=user_kwargs['tools'].get("position", self.config.toolsLocation),
                           toolbar_sticky=False)
        # add image
        image = bokehPlot.image(source=cds, image='image', x='x', y='y', dw='dw', dh='dh', palette=bokehpalette)

        # add colorbar to the plot
        colorbar = None
        if user_kwargs["colorbar_properties"].get(
                "colorbar", self.config.interactive_colorbar):
            # check if colorbar should be modified
            modify_colorbar = data.get("interactive_params", {}).get(
                "colorbar_properties", {}).get("modify_ticks", bkh_kwargs.get("modify_colorbar", False))
            if modify_colorbar: colorbar_as_percentage = True
            else: colorbar_as_percentage = False
            bokehPlot, colorbar = self._add_colorbar(bokehPlot, zvals, colorMapper,
                                                     modify_colorbar,
                                                     as_percentage=colorbar_as_percentage,
                                                     return_colorbar=True,
                                                     data=data)
        # setup labels
        bokehPlot.xaxis.axis_label = xlabel
        bokehPlot.yaxis.axis_label = ylabel

        # setup common parameters
        bokehPlot = self._setupPlotParameters(bokehPlot, plot_type="2D", data=data)

        # add widgets
        if (user_kwargs["widgets"].get("add_custom_widgets", self.config.interactive_custom_scripts) and
            bkh_kwargs['page_layout'] in ["Individual", "Columns"]):
            js_type, js_code = [], {}

            if user_kwargs["widgets"].get("colormap_change", True):
                cmaps = []
                zmin, zmax = np.round(np.min(zvals), 10), np.round(np.max(zvals), 10)
                for alt_cmap in ["cividis", "viridis", "magma", "cubehelix"]:
                    cmaps.append(self._convert_cmap_to_colormapper(alt_cmap, zmin=zmin, zmax=zmax))

                js_code.update(colormaps=cmaps, colormap_names=["cividis", "viridis", "magma", "cubehelix"], images=[image], colorbars=[colorbar])
                js_type.extend(["colormap_change"])

            if user_kwargs["widgets"].get("colorblind_safe_2D", True):
                zmin, zmax = np.round(np.min(zvals), 10), np.round(np.max(zvals), 10)
                _cvd_colors = [self._convert_cmap_to_colormapper(self.config.interactive_cvd_cmap, zmin, zmax)]
                _original_colors = [self._convert_cmap_to_colormapper(palette=bokehpalette, zmin=zmin, zmax=zmax)]
                js_code.update(original_colors=_original_colors,
                               cvd_colors=_cvd_colors, images=[image],
                               colorbars=[colorbar])
                js_type.extend(["colorblind_safe_2D"])

            if len(js_type) > 0:
                try: bokehPlot = self.add_custom_js_widgets(bokehPlot, js_type=js_type, data=data, **js_code)
                except: pass
        elif (user_kwargs["widgets"].get("add_custom_widgets", self.config.interactive_custom_scripts) and
              bkh_kwargs['page_layout'] not in ["Individual", "Columns"]):
            self.presenter.onThreading(None, ("Adding widgets to 'Grid'/'Rows' is not supported at the moment." , 4),
                                       action='updateStatusbar')

        return [bokehPlot, plt_kwargs['plot_width'], plt_kwargs['plot_height']]

    def _add_plot_rgb(self, data, **bkh_kwargs):
        plt_kwargs = self._buildPlotParameters(data)
        user_kwargs = deepcopy(data['interactive_params'])
        
        # Unpacks data using a helper function
        zvals, xvals, xlabel, yvals, ylabel, __ = self.presenter.get2DdataFromDictionary(dictionary=data,
                                                                                           dataType='plot',
                                                                                           plotType='2D',
                                                                                           compact=False)
        if xlabel == "": hover_xlabel = "x"
        else: hover_xlabel = xlabel
        if ylabel == "": hover_ylabel = "y"
        else: hover_ylabel = ylabel

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
        hoverTool = HoverTool(tooltips=[(hover_xlabel, '$x{0}'),
                                        (hover_ylabel, '$y{0}')],
                              point_policy='follow_mouse')

        TOOLS = self._check_tools(hoverTool, data)
        bokehPlot = figure(x_range=(min(xvals), max(xvals)),
                           y_range=(min(yvals), max(yvals)),
                           tools=TOOLS,
                           active_drag=user_kwargs['tools'].get("active_drag", "auto"),
                           active_scroll=user_kwargs['tools'].get("active_wheel", "auto"),
                           plot_width=plt_kwargs["plot_width"],
                           plot_height=plt_kwargs["plot_height"],
                           toolbar_location=user_kwargs['tools'].get("position", self.config.toolsLocation),
                           toolbar_sticky=False)
        bokehPlot.image_rgba(source=cds, image='image', x='x', y='y', dw='dw', dh='dh')
        bokehPlot.quad(top=max(yvals), bottom=min(yvals),
                       left=min(xvals), right=max(xvals),
                       alpha=0)
        bokehPlot.xaxis.axis_label = xlabel
        bokehPlot.yaxis.axis_label = ylabel

        self._setupPlotParameters(bokehPlot, plot_type="2D", data=data)

        return [bokehPlot, plt_kwargs['plot_width'], plt_kwargs['plot_height']]

    def _add_plot_matrix(self, data, **bkh_kwargs):
        plt_kwargs = self._buildPlotParameters(data)
        user_kwargs = deepcopy(data['interactive_params'])

        # get data
        zvals, yxlabels, cmap = self.presenter.get2DdataFromDictionary(
            dictionary=data, plotType='Matrix', compact=False)
        
        # rotate data
        zvals = np.rot90(np.fliplr(zvals))
        
        # get colormapper and palette
        colorMapper, bokehpalette = self._convert_cmap_to_colormapper(
            user_kwargs["overlay_properties"].get("rmsd_matrix_colormap", cmap), 
            zvals=zvals, return_palette=True)
        xlabel = 'Labels (x, y):'
        ylabel = bkh_kwargs.get("hover_label", 'RMSD (%)')
        hoverTool = HoverTool(tooltips=[(xlabel, '@xname, @yname'),
                                          (ylabel, '@count')],
                             point_policy='follow_mouse')
        # Add tools
        TOOLS = self._check_tools(hoverTool, data)
        
        # Assemble data into appropriate format
        xname, yname, color, alpha, text_color = [], [], [], [], []
        # rescaling parameters
        old_min, old_max, new_min, new_max = np.min(zvals), np.max(zvals), 0, len(bokehpalette) - 1

        # check label length
        if len(set(yxlabels)) == 1:
            msg = 'Exporting RMSD Matrix to a HTML file is only possible with full list of x/y-axis labels.\n' + \
                  'Please add those to the file and try repeating.'
            dialogs.dlgBox(exceptionTitle='No file name',
                           exceptionMsg=msg,
                           type="Error")
            return None
        else:
            text_annot_xpos, text_annot_ypos, text_annot_label = [], [], []
            for i, namey in enumerate(yxlabels):
                for j, namex in enumerate(yxlabels):
                    xname.append(namex)
                    yname.append(namey)
                    new_value = ((zvals[i, j] - old_min) / (old_max - old_min)) * (new_max - new_min) + new_min
                    text_annot_xpos.append(j + .5)
                    text_annot_ypos.append(i + .3)
                    text_annot_label.append(zvals[i, j])
                    color.append(bokehpalette[int(new_value)])
                    if zvals[i, j] == 0: alpha_val = 0.
                    else: alpha_val = 1.
                    alpha.append(alpha_val) #min(zvals[i, j] / 3.0, 0.9) + 0.0)
                    if user_kwargs["overlay_properties"].get("rmsd_matrix_auto_label_color", True):
                        label_color = determineFontColor(convertHEXtoRGB255(color[-1]), return_hex=True)
                    else:
                        label_color = convertRGB1toHEX(user_kwargs["overlay_properties"].get("rmsd_matrix_label_color", self.config.interactive_ms_annotations_label_color))
                    text_color.append(label_color)
                    
                    
        # create plot source
        source = ColumnDataSource(data=dict(xname=xname, yname=yname,
                                            count=zvals.flatten(),
                                            alphas=alpha, colors=color))

        # create figure
        bokehPlot = figure(x_range=yxlabels,
                           y_range=yxlabels,
                           tools=TOOLS,
                           active_drag=user_kwargs['tools'].get("active_drag", "auto"),
                           active_scroll=user_kwargs['tools'].get("active_wheel", "auto"),
                           plot_width=plt_kwargs["plot_width"],
                           plot_height=plt_kwargs["plot_height"],
                           toolbar_location=user_kwargs['tools'].get("position", self.config.toolsLocation),
                           toolbar_sticky=False)
        # add plot
        bokehPlot.rect('xname', 'yname', 1, 1,
                       source=source, line_color=None,
                       hover_line_color='black',
                       alpha='alphas', hover_color='colors',
                       color='colors')
        # create label source
        label_source = ColumnDataSource(data=dict(xpos=text_annot_xpos,
                                                  ypos=text_annot_ypos,
                                                  label=text_annot_label,
                                                  text_color=text_color))
        # add labels
        bokehPlot, __ = self._add_plot_labels(bokehPlot, data, label_source, plot_type="waterfall")

        # add colorbar
        if user_kwargs["colorbar_properties"].get(
                "colorbar", self.config.interactive_colorbar):
            modify_colorbar = user_kwargs["colorbar_properties"].get(
                    "modify_ticks", bkh_kwargs.get("modify_colorbar", False))
            if modify_colorbar: colorbar_as_percentage = True
            else: colorbar_as_percentage = False
            bokehPlot = self._add_colorbar(bokehPlot, zvals, colorMapper,
                                           modify_colorbar, colorbar_as_percentage,
                                           data=data)

        # setup plot parameters
        bokehPlot = self._setupPlotParameters(bokehPlot, plot_type="Matrix", data=data)

        return [bokehPlot, plt_kwargs['plot_width'], plt_kwargs['plot_height']]

    def _add_plot_rmsd(self, data, **bkh_kwargs):
        plt_kwargs = self._buildPlotParameters(data)
        user_kwargs = deepcopy(data['interactive_params'])

        # get plot data
        zvals, xvals, xlabel, yvals, ylabel, rmsdLabel, cmap = self.presenter.get2DdataFromDictionary(
            dictionary=data, plotType='RMSD', compact=True)

        # create plot source
        z_data = dict(image=[zvals], x=[min(xvals)], y=[min(yvals)],
                      dw=[max(xvals) - min(xvals)],
                      dh=[max(yvals) - min(yvals)])
        cds = ColumnDataSource(data=z_data)

        # calculate position of RMSD label
        rmsdXpos, rmsdYpos = self.presenter.onCalculateRMSDposition(
            xlist=xvals, ylist=yvals)

        # get colormapper and palette
        colorMapper, bokehpalette = self._convert_cmap_to_colormapper(cmap, zvals=zvals, return_palette=True)
        # create tooltip
        hoverTool = HoverTool(tooltips=[(xlabel, '$x{0}'), (ylabel, '$y{0}'),
                                          ('Intensity', '@image')],
                              point_policy='follow_mouse')

        # Add tools
        TOOLS = self._check_tools(hoverTool, data)
        # create figure
        bokehPlot = figure(x_range=(min(xvals), max(xvals)),
                           y_range=(min(yvals), max(yvals)),
                           tools=TOOLS,
                           active_drag=user_kwargs['tools'].get("active_drag", "auto"),
                           active_scroll=user_kwargs['tools'].get("active_wheel", "auto"),
                           plot_width=plt_kwargs["plot_width"],
                           plot_height=plt_kwargs["plot_height"],
                           toolbar_location=user_kwargs['tools'].get("position", self.config.toolsLocation),
                           toolbar_sticky=False)
        # create plot
        bokehPlot.image(source=cds, image='image', x='x', y='y', dw='dw', dh='dh', palette=bokehpalette)

        # add colorbar
        if user_kwargs["colorbar_properties"].get(
                "colorbar", self.config.interactive_colorbar):
            bokehPlot = self._add_colorbar(bokehPlot, zvals, colorMapper,
                                           modify_colorbar = data.get(
                                                "interactive_params", {}).get("colorbar_properties", {}).get(
                                                    "modify_ticks", bkh_kwargs.get("modify_colorbar", False)),
                                           data=data)

        # Add RMSD label to the plot
        self._add_rmsd_label(bokehPlot, rmsdLabel, rmsdXpos, rmsdYpos, data=data)

        bokehPlot.xaxis.axis_label = xlabel
        bokehPlot.yaxis.axis_label = ylabel
        bokehPlot = self._setupPlotParameters(bokehPlot, plot_type="2D", data=data)

        return [bokehPlot, plt_kwargs['plot_width'], plt_kwargs['plot_height']]

    def _add_plot_rmsf(self, data, **bkh_kwargs):
        plt_kwargs = self._buildPlotParameters(data)
        user_kwargs = deepcopy(data['interactive_params'])

        # get plot data
        zvals, yvalsRMSF, xvals, yvals, xlabelRMSD, ylabelRMSD, ylabelRMSF, color, cmap, rmsdLabel = self.presenter.get2DdataFromDictionary(
            dictionary=data, plotType='RMSF', compact=True)

        ylabelRMSF = ''.join([ylabelRMSF])

        hoverToolRMSF = HoverTool(tooltips=[(xlabelRMSD, '$x{0.00}'),
                                            (ylabelRMSF, '$y{0.00}')],
                                  mode=plt_kwargs['hover_mode'])

        # Add tools
        TOOLS_RMSF = self._check_tools(hoverToolRMSF, data)

        # create rmsf figure
        bokehPlotRMSF = figure(x_range=(min(xvals), max(xvals)),
                               y_range=(min(yvalsRMSF), max(yvalsRMSF)),
                               tools=TOOLS_RMSF,
                               active_drag=user_kwargs['tools'].get("active_drag", "auto"),
                               active_scroll=user_kwargs['tools'].get("active_wheel", "auto"),
                                plot_width=plt_kwargs["plot_width"],
                                plot_height=int(plt_kwargs["plot_height"] / 2),
                                toolbar_location=user_kwargs['tools'].get("position", self.config.toolsLocation),
                               toolbar_sticky=False)
        # create rmsf plot
        color = convertRGB1to255(color, as_integer=True, as_tuple=True)
        rmsf_source = ColumnDataSource(data=dict(xvals=xvals, yvals=yvalsRMSF))
        line = bokehPlotRMSF.line(x="xvals", y="yvals",
                                  source=rmsf_source,
                                  line_color=color,
                                  line_width=user_kwargs["overlay_properties"]["rmsf_line_width"],
                                  line_alpha=user_kwargs["overlay_properties"]["rmsf_line_transparency"],
                                  line_dash=user_kwargs["overlay_properties"]["rmsf_line_style"])
        bokehPlotRMSF.yaxis.axis_label = ylabelRMSF
        
        # add patch
        if user_kwargs["overlay_properties"].get("rmsf_line_shade_under", False):
            patch = bokehPlotRMSF.patch(
                "xvals", "yvals", color=color,
                fill_alpha=user_kwargs["overlay_properties"].get("rmsf_shade_transparency", self.config.interactive_line_alpha),
                line_alpha=0., source=rmsf_source)
        # setup parameters
        bokehPlotRMSF = self._setupPlotParameters(bokehPlotRMSF, plot_type="RMSF", data=data)

        # create data sourcee
        z_data = dict(image=[zvals], x=[min(xvals)], y=[min(yvals)],
                      dw=[max(xvals) - min(xvals)],
                      dh=[max(yvals) - min(yvals)])
        cds = ColumnDataSource(data=z_data)

        # Calculate position of RMSD label
        rmsdXpos, rmsdYpos = self.presenter.onCalculateRMSDposition(xlist=xvals, ylist=yvals)
        colorMapper, bokehpalette = self._convert_cmap_to_colormapper(cmap, zvals=zvals, return_palette=True)
        hoverTool = HoverTool(tooltips=[(xlabelRMSD, '$x{0.00}'),
                                          (ylabelRMSD, '$y{0.00}'),
                                          ('Intensity', '@image')],
                             point_policy='follow_mouse')
        # Add tools
        TOOLS = self._check_tools(hoverTool, data)
        if plt_kwargs['overlay_linkXY']: x_range = bokehPlotRMSF.x_range
        else: x_range = (min(xvals), max(xvals))

        bokehPlotRMSD = figure(x_range=x_range,
                               y_range=(min(yvals), max(yvals)),
                               tools=TOOLS,
                               active_drag=user_kwargs['tools'].get("active_drag", "auto"),
                               active_scroll=user_kwargs['tools'].get("active_wheel", "auto"),
                               plot_width=plt_kwargs["plot_width"],
                               plot_height=plt_kwargs["plot_height"],
                       toolbar_location=user_kwargs['tools'].get("position", self.config.toolsLocation),
                       toolbar_sticky=False)
        bokehPlotRMSD.image(source=cds, image='image', x='x', y='y', dw='dw', dh='dh', palette=bokehpalette)

        # add colorbar
        if user_kwargs["colorbar_properties"].get(
                "colorbar", self.config.interactive_colorbar):
             bokehPlotRMSD = self._add_colorbar(bokehPlotRMSD, zvals, colorMapper,
                                                modify_colorbar = data.get(
                                                    "interactive_params", {}).get("colorbar_properties", {}).get(
                                                        "modify_ticks", bkh_kwargs.get("modify_colorbar", False)),
                                                data=data)

        # Add RMSD label to the plot
        self._add_rmsd_label(bokehPlotRMSD, rmsdLabel, rmsdXpos, rmsdYpos, data=data)

        bokehPlotRMSD.xaxis.axis_label = xlabelRMSD
        bokehPlotRMSD.yaxis.axis_label = ylabelRMSD
        bokehPlotRMSD = self._setupPlotParameters(bokehPlotRMSD, plot_type="2D", data=data)

        bokehPlot = gridplot([[bokehPlotRMSF], [bokehPlotRMSD]], merge_tools=False)

        return [bokehPlot, plt_kwargs['plot_width'], int(plt_kwargs['plot_height'] * 1.5)]

    def _add_plot_overlay_2D(self, data, **bkh_kwargs):
        plt_kwargs = self._buildPlotParameters(data)
        user_kwargs = deepcopy(data['interactive_params'])
        
        # get plot data
        (zvals1, zvals2, cmapIon1, cmapIon2, alphaIon1, alphaIon2, xvals,
         xlabel, yvals, ylabel, charge1, charge2) = self.presenter.get2DdataFromDictionary(
             dictionary=data, dataType='plot', plotType='Overlay', compact=False)
        
        if bkh_kwargs['plot_type'] == 'Mask':
            zvals1 = zvals1.filled(0)
            zvals2 = zvals2.filled(0)

        cmapIon1 = user_kwargs['overlay_properties'].get(
            "overlay_colormap_1", plt_kwargs.get('overlay_color_1', cmapIon1))
        cmapIon2 = user_kwargs['overlay_properties'].get(
            "overlay_colormap_2", plt_kwargs.get('overlay_color_2', cmapIon2))

        colorMapper1, bokehpalette1 = self._convert_cmap_to_colormapper(cmapIon1, zvals=zvals1, return_palette=True)
        hoverTool1 = HoverTool(tooltips=[(xlabel, '$x{0.00}'),
                                         (ylabel, '$y{0.00}'),
                                         ('Intensity', '@image')],
                             point_policy='follow_mouse')
        # Add tools
        TOOLS1 = self._check_tools(hoverTool1, data)
        
        # create figure
        leftPlot = figure(x_range=(min(xvals), max(xvals)),
                           y_range=(min(yvals), max(yvals)),
                           tools=TOOLS1,
                           active_drag=user_kwargs['tools'].get("active_drag", "auto"),
                           active_scroll=user_kwargs['tools'].get("active_wheel", "auto"),
                           toolbar_location=user_kwargs['tools'].get("position", self.config.toolsLocation),
                           toolbar_sticky=False)

        z_data = dict(image=[zvals1], x=[min(xvals)], y=[min(yvals)],
                      dw=[max(xvals) - min(xvals)],
                      dh=[max(yvals) - min(yvals)])
        cds = ColumnDataSource(data=z_data)
        image_1 = leftPlot.image(source=cds, image='image', x='x', y='y', dw='dw', dh='dh', palette=bokehpalette1)

        colorMapper2, bokehpalette2 = self._convert_cmap_to_colormapper(cmapIon2, zvals=zvals2, return_palette=True)
        hoverTool2 = HoverTool(tooltips=[(xlabel, '$x{0.00}'),
                                           (ylabel, '$y{0.00}'),
                                           ('Intensity', '@image')],
                             point_policy='follow_mouse')
        # Add tools
        TOOLS2 = self._check_tools(hoverTool2, data)

        if user_kwargs['overlay_properties']['overlay_link_xy']:
            x_range=leftPlot.x_range
            y_range=leftPlot.y_range
        else:
            x_range=(min(xvals), max(xvals))
            y_range=(min(yvals), max(yvals))
        
        rightPlot = figure(x_range=x_range, y_range=y_range,
                           tools=TOOLS2,
                           active_drag=user_kwargs['tools'].get("active_drag", "auto"),
                           active_scroll=user_kwargs['tools'].get("active_wheel", "auto"),
                           plot_width=plt_kwargs["plot_width"],
                           plot_height=plt_kwargs["plot_height"],
                           toolbar_location=user_kwargs['tools'].get("position", self.config.toolsLocation),
                           toolbar_sticky=False)

        z_data = dict(image=[zvals2], x=[min(xvals)], y=[min(yvals)],
                      dw=[max(xvals) - min(xvals)],
                      dh=[max(yvals) - min(yvals)])
        cds = ColumnDataSource(data=z_data)
        image_2 = rightPlot.image(source=cds, image='image', x='x', y='y', dw='dw', dh='dh', palette=bokehpalette2)

        if user_kwargs["colorbar_properties"].get(
                "colorbar", self.config.interactive_colorbar):
            leftPlot = self._add_colorbar(leftPlot, zvals1, colorMapper1, True, True, data=data)
            rightPlot = self._add_colorbar(rightPlot, zvals2, colorMapper2, True, True, data=data)

        for plot in [leftPlot, rightPlot]:
            plot = self._setupPlotParameters(plot, plot_type="2D", data=data)

        if user_kwargs['overlay_properties']['overlay_layout'] == 'Rows':
            for plot in [leftPlot, rightPlot]:
                plot.xaxis.axis_label = xlabel
            leftPlot.yaxis.axis_label = ylabel
            # Remove tick values from right plot
            rightPlot.yaxis.major_label_text_color = None  # turn off y-axis tick labels leaving space
            bokehPlot = gridplot([[leftPlot, rightPlot]],
                merge_tools=user_kwargs['overlay_properties'].get("overlay_merge_tools", False))
            plt_kwargs['plot_width'] = plt_kwargs['plot_width'] * 2
        elif user_kwargs['overlay_properties']['overlay_layout'] == 'Columns':
            for plot in [leftPlot, rightPlot]:
                plot.yaxis.axis_label = ylabel
            leftPlot.xaxis.major_label_text_color = None  # turn off y-axis tick labels leaving space
            rightPlot.xaxis.axis_label = xlabel
            bokehPlot = gridplot([[leftPlot], [rightPlot]], 
                merge_tools=user_kwargs['overlay_properties'].get("overlay_merge_tools", False))

        return [bokehPlot, plt_kwargs['plot_width'], plt_kwargs['plot_height']]

    def _add_plot_unidec_1D(self, data, **bkh_kwargs):
        plt_kwargs = self._buildPlotParameters(data)
        user_kwargs = deepcopy(data['interactive_params'])

        _markers_map = {'o':"circle", 'v':"inverted_triangle", '^':"triangle",
                        '>':"cross", 's':"square", 'd':"diamond", '*':"asterisk"}
        _ydata, legend_handle = [], []
        xvals = data['xvals']
        yvals = data['yvals']
        xlabel = data['xlabel']
        ylabel = data['ylabel']

        # Prepare hover tool
        hoverTool = HoverTool(tooltips=[(xlabel, '@xvals{0.00}'),
                                          ("Offset Intensity", '@yvals{0.00}'),
                                          ("Label", "@label")],
                              mode=plt_kwargs['hover_mode'])
        TOOLS = self._check_tools(hoverTool, data)

        if (user_kwargs["preprocessing_properties"]["linearize"] and
            len(xvals) > user_kwargs["preprocessing_properties"].get("linearize_limit", 25000)):
            # TODO: implement better downsampling
            # downsampling: https://github.com/devoxi/lttb-py/blob/master/lttb/lttb.py
            xvals, yvals = self.linearize_spectrum(
                xvals, yvals, user_kwargs["preprocessing_properties"]["linearize_binsize"])

        xlimits = [np.amin(np.ravel(xvals)), np.amax(np.ravel(xvals))]
        bokehPlot = figure(x_range=xlimits,
                           tools=TOOLS,
                           active_drag=user_kwargs['tools'].get("active_drag", "auto"),
                           active_scroll=user_kwargs['tools'].get("active_wheel", "auto"),
                           plot_width=plt_kwargs["plot_width"],
                           plot_height=plt_kwargs["plot_height"],
                           toolbar_location=user_kwargs['tools'].get("position", self.config.toolsLocation),
                           toolbar_sticky=False)
        # create dataframe

        source = ColumnDataSource(data=dict(xvals=xvals,
                                            yvals=yvals,
                                            label=(["Raw"] * len(xvals))))
        _ydata.extend(yvals)
        if not user_kwargs["legend_properties"].get("legend", plt_kwargs['add_legend']): label = None
        else: label = "Raw"

        bokehPlot.line(x="xvals", y="yvals",
                       line_color="black",
                       line_width=user_kwargs["plot_properties"]["line_width"],
                       line_alpha=user_kwargs["plot_properties"]["line_transparency"],
                       line_dash=user_kwargs["plot_properties"]["line_style"],
                       legend=label,
                       muted_alpha=user_kwargs['legend_properties'].get("legend_mute_alpha", self.config.interactive_legend_mute_alpha),
                       muted_color="black",
                       source=source)

        for key in data:
            if key.split(" ")[0] != "MW:": continue

            line_xvals = data[key]['line_xvals']
            line_yvals = data[key]['line_yvals']

            if (user_kwargs["preprocessing_properties"]["linearize"] and
                len(line_xvals) > user_kwargs["preprocessing_properties"].get("linearize_limit", 25000)):
                # TODO: implement better downsampling
                # downsampling: https://github.com/devoxi/lttb-py/blob/master/lttb/lttb.py
                line_xvals, line_yvals = self.linearize_spectrum(
                    line_xvals, line_yvals, user_kwargs["preprocessing_properties"]["linearize_binsize"])


            _ydata.extend(line_yvals)
            color = convertRGB1to255(data[key]['color'], as_integer=True, as_tuple=True)
            source = ColumnDataSource(data=dict(xvals=line_xvals,
                                                yvals=line_yvals,
                                                label=([data[key]['label']] * len(line_xvals))))
            if not user_kwargs["legend_properties"].get("legend", plt_kwargs['add_legend']): label = None
            else: label = data[key]['label']

            bokehPlot.line(x="xvals", y="yvals",
                           line_color=color,
                           line_width=user_kwargs["plot_properties"]["line_width"],
                           line_alpha=user_kwargs["plot_properties"]["line_transparency"],
                           line_dash=user_kwargs["plot_properties"]["line_style"],
                           legend=label,
                           muted_alpha=user_kwargs['legend_properties'].get("legend_mute_alpha", self.config.interactive_legend_mute_alpha),
                           muted_color=color,
                           source=source)
            legend_handle.append((label, [bokehPlot]))


            source = ColumnDataSource(data=dict(xvals=data[key]['scatter_xvals'],
                                                yvals=data[key]['scatter_yvals'],
                                                label=([data[key]['label']] * len(data[key]['scatter_xvals']))))

            if self.config.interactive_scatter_sameAsFill: edge_color = color
            else: edge_color = convertRGB1toHEX(self.config.interactive_scatter_edge_color)
            bokehPlot.scatter("xvals", "yvals",
                              marker=_markers_map[data[key]['marker']],
                              fill_alpha=user_kwargs['plot_properties'].get("scatter_transparency", self.config.interactive_scatter_alpha),
                              size=user_kwargs['plot_properties'].get("scatter_line_width", self.config.interactive_scatter_size),
                              line_width=user_kwargs['plot_properties'].get("scatter_line_width", self.config.interactive_scatter_lineWidth),
                              source=source,
                              legend=label,
                              line_color=edge_color, fill_color=color, muted_color=color,
                              muted_alpha=user_kwargs['legend_properties'].get("legend_mute_alpha", self.config.interactive_legend_mute_alpha))

#             leg = Legend(items=legend_handle, location=(0, -60))
#             print(leg)
        # setup labels
        bokehPlot.xaxis.axis_label = xlabel
        bokehPlot.yaxis.axis_label = ylabel
        # setup common parameters
        ylimits = [np.min(_ydata), np.max(_ydata)]
        js_kwargs = dict(xlimits=xlimits, ylimits=ylimits)
        bokehPlot = self._setupPlotParameters(bokehPlot, data=data, plot_type="Overlay_1D", **js_kwargs)

        if user_kwargs["widgets"].get("add_custom_widgets", self.config.interactive_custom_scripts):
            js_type = []
            js_code = {"hover":hoverTool}
            if user_kwargs["widgets"].get("hover_mode", True):
                js_type.extend(["hover_mode"])

            if user_kwargs["legend_properties"].get("legend", plt_kwargs['add_legend']) and len(bokehPlot.legend) > 0:
                js_code.update(legend=bokehPlot.legend[0])

                if user_kwargs["widgets"].get("legend_toggle", True):
                    js_type.extend(["legend_toggle"])
                if user_kwargs["widgets"].get("legend_position", True):
                    js_type.extend(["legend_position"])
                if user_kwargs["widgets"].get("legend_orientation", True):
                    js_type.extend(["legend_orientation"])
                if user_kwargs["widgets"].get("legend_transparency", True):
                    js_type.extend(["legend_transparency"])

            if len(js_type) > 0:
                try: bokehPlot = self.add_custom_js_widgets(bokehPlot, js_type=js_type, data=data, **js_code)
                except: pass

        return [bokehPlot, plt_kwargs['plot_width'], plt_kwargs['plot_height']]

    def _add_plot_unidec_2D(self, data, **bkh_kwargs):
        plt_kwargs = self._buildPlotParameters(data)
        user_kwargs = deepcopy(data['interactive_params'])
        
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
        if zvals.shape[1] > user_kwargs['preprocessing_properties'].get("subsample_limit", 20000):
            print("Have to subsample the grid as it is too big...")
            zvals = zvals[:, ::user_kwargs['preprocessing_properties'].get("subsample_frequency", 10)].copy()

        if bkh_kwargs.get("test_x_axis", False):
            xvals, xlabel, __ = self._kda_test(xvals)

        z_data = dict(image=[zvals], x=[min(xvals)], y=[min(yvals)],
                      dw=[max(xvals) - min(xvals)],
                      dh=[max(yvals) - min(yvals)])

        cds = ColumnDataSource(data=z_data)
        hoverTool = HoverTool(tooltips=[(xlabel, '$x{0}'),
                                        (ylabel, '$y{0}'),
                                        ('Intensity', '@image')],
                            point_policy='follow_mouse',
                             )

        TOOLS = self._check_tools(hoverTool, data)

        bokehPlot = figure(x_range=(min(xvals), max(xvals)),
                           y_range=(min(yvals), max(yvals)),
                           tools=TOOLS,
                           active_drag=user_kwargs['tools'].get("active_drag", "auto"),
                           active_scroll=user_kwargs['tools'].get("active_wheel", "auto"),
                           plot_width=plt_kwargs["plot_width"],
                           plot_height=plt_kwargs["plot_height"],
                           toolbar_location=user_kwargs['tools'].get("position", self.config.toolsLocation),
                           toolbar_sticky=False)

        colorMapper = self._convert_cmap_to_colormapper(cmap, zvals=zvals)
        bokehPlot.image(source=cds, image='image', x='x', y='y', dw='dw', dh='dh', color_mapper=colorMapper)

        if user_kwargs["colorbar_properties"].get(
                "colorbar", self.config.interactive_colorbar):
             bokehPlot = self._add_colorbar(bokehPlot, zvals, colorMapper,
                                            modify_colorbar = data.get(
                                                "interactive_params", {}).get("colorbar_properties", {}).get(
                                                    "modify_ticks", bkh_kwargs.get("modify_colorbar", False)),
                                            as_percentage=True, data=data)

        # setup labels
        bokehPlot.xaxis.axis_label = xlabel
        bokehPlot.yaxis.axis_label = ylabel

        # setup common parameters
        self._setupPlotParameters(bokehPlot, plot_type="2D", data=data)

        return [bokehPlot, plt_kwargs['plot_width'], plt_kwargs['plot_height']]

    # TODO: check if thats right...

    def _add_plot_unidec_barchart(self, data, **bkh_kwargs):
        plt_kwargs = self._buildPlotParameters(data)
        user_kwargs = deepcopy(data['interactive_params'])

        xvals = data['xvals']
        yvals = data['yvals']
        labels = data['labels']
        ylabel = data['ylabel']
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

        hoverTool = HoverTool(tooltips=[("Component", '@labels'),
                                          ("Deconvoluted MW (Da)", '@mw'),
                                          ("Intensity", '@yvals')],
                              mode='mouse')

        TOOLS = self._check_tools(hoverTool, data)

        bokehPlot = figure(x_range=labels,
                           y_range=(0, max(yvals) * 1.05),
                           tools=TOOLS,
                           active_drag=user_kwargs['tools'].get("active_drag", "auto"),
                           active_scroll=user_kwargs['tools'].get("active_wheel", "auto"),
                           plot_width=plt_kwargs["plot_width"],
                           plot_height=plt_kwargs["plot_height"],
                           toolbar_location=user_kwargs['tools'].get("position", self.config.toolsLocation),
                           toolbar_sticky=False)
        bokehPlot.vbar(x='xvals', top='yvals', width=0.9, source=source, legend="legend",
                       fill_color="colors", line_color='white')

        # setup labels
        bokehPlot.yaxis.axis_label = ylabel
        # setup common parameters
        bokehPlot = self._setupPlotParameters(bokehPlot, plot_type="1D", data=data)
        if user_kwargs["widgets"].get("add_custom_widgets", self.config.interactive_custom_scripts):
            js_type, js_code = [], {}

            if user_kwargs["widgets"].get("hover_mode", True):
                js_code.update(hover=hoverTool)
                js_type.extend(["hover_mode"])

            if user_kwargs["legend_properties"].get("legend", plt_kwargs['add_legend']) and len(bokehPlot.legend) > 0:
                js_code.update(legend=bokehPlot.legend[0])
                if user_kwargs["widgets"].get("legend_toggle", True):
                    js_type.extend(["legend_toggle"])
                if user_kwargs["widgets"].get("legend_position", True):
                    js_type.extend(["legend_position"])
                if user_kwargs["widgets"].get("legend_orientation", True):
                    js_type.extend(["legend_orientation"])
                if user_kwargs["widgets"].get("legend_transparency", True):
                    js_type.extend(["legend_transparency"])

            if len(js_type) > 0:
                try: bokehPlot = self.add_custom_js_widgets(bokehPlot, js_type=js_type, data=data, **js_code)
                except: pass

        return [bokehPlot, plt_kwargs['plot_width'], plt_kwargs['plot_height']]

    def _add_plot_waterfall(self, data, **bkh_kwargs):
        plt_kwargs = self._buildPlotParameters(data)
        user_kwargs = deepcopy(data['interactive_params'])

        # get data
        xvals = data['xvals']
        yvals = data['yvals']
        colorList = data['colors']
        xlabel = data['xlabel']
        ylabel = data['ylabel']
        hoverLabels = data.get('hover_labels', [])

        xlabel = _replace_labels(xlabel)
        ylabel = _replace_labels(ylabel)

        if ylabel in ["Intensity", "Normalized intensity", "Normalised intensity"]:
            ylabel = "Offset intensity"

        # check parameters
        if "waterfall_kwargs" in data: labels = data['waterfall_kwargs']['labels']
        else: labels = data['labels']

        # check in case only one item was passed. Assumes xvals is a list in a list
        if len(xvals) != len(yvals) and len(xvals) == 1:
            xvals = xvals * len(yvals)

        # generate tooltip and hover
        _tooltips = [(xlabel, '@xvals{0.00}'), (ylabel, '@yvals{0.00}')]
        if len(hoverLabels) > 0:
            try: hover_label = hoverLabels[0]
            except: hover_label = "Label ({})".format(0)
            _tooltips.append((hover_label, '@label'))
        else:
            hover_label = "Label"
            _tooltips.append((hover_label, '@label'))
        hoverTool = HoverTool(tooltips=_tooltips, mode=plt_kwargs['hover_mode'])

        # generate tools
        TOOLS = self._check_tools(hoverTool, data)

        xvals_list, __ = find_limits_list(xvals, yvals)

        # create figure
        bokehPlot = figure(
            tools=TOOLS, title=bkh_kwargs['title'],
            active_drag=user_kwargs['tools'].get("active_drag", "auto"),
            active_scroll=user_kwargs['tools'].get("active_wheel", "auto"),
            plot_width=plt_kwargs["plot_width"], plot_height=plt_kwargs["plot_height"],
            toolbar_location=user_kwargs['tools'].get("position", self.config.toolsLocation),
            toolbar_sticky=False)

        i = len(xvals)
        _ydata = []
        
        # create empty label holders
        if user_kwargs["annotation_properties"].get(
            "show_labels", self.config.interactive_ms_annotations_labels):
            text_annot_ypos, text_annot_label = [], []

        # add plots
        _lines, _patches, _original_colors, = [], [], []
        for xval, yval, color, label in zip(xvals, yvals, colorList, labels):
            try: color = convertRGB1toHEX(color)
            except (SyntaxError, ValueError): pass

            # linearize
            if (user_kwargs["preprocessing_properties"]["linearize"] and
                len(xval) > user_kwargs["preprocessing_properties"].get("linearize_limit", 25000)):
                xval, yval = self.linearize_spectrum(
                xval, yval, user_kwargs["preprocessing_properties"]["linearize_binsize"])

            yval = np.asarray(yval)

            # normalize data
            normalize = True # TODO: add to parameters
            if normalize: yval = normalize_1D(inputData=yval)

            # create plot source
            source = ColumnDataSource(
                data=dict(xvals=xval,
                          yvals=yval + user_kwargs['plot_properties'].get(
                              "waterfall_increment", self.config.interactive_waterfall_increment) * i,
                          label=([_replace_labels(label)] * len(xval))))
            
            # create legend label
            if not user_kwargs["legend_properties"].get("legend", plt_kwargs['add_legend']): 
                legend_label = None
            else: 
                legend_label = _replace_labels(label)
                
            line = bokehPlot.line(
                x="xvals", y="yvals", line_color=color,
                line_width=user_kwargs["plot_properties"]["line_width"],
                line_alpha=user_kwargs['plot_properties'].get(
                    "line_transparency", self.config.interactive_line_alpha),
                line_dash=user_kwargs['plot_properties'].get(
                    "line_style", self.config.interactive_line_style),
                legend=legend_label,
                muted_alpha=user_kwargs['legend_properties'].get("legend_mute_alpha", self.config.interactive_legend_mute_alpha),
                muted_color=color,
                source=source)
            
            # add underline patch
            if user_kwargs['plot_properties'].get(
                "waterfall_shade_under", self.config.interactive_waterfall_shade_under):
                patch = bokehPlot.patch(
                    "xvals", "yvals", color=color, 
                    fill_alpha=user_kwargs['plot_properties'].get(
                        "waterfall_shade_transparency", self.config.interactive_waterfall_shade_alpha),
                    line_alpha=0., source=source, legend=legend_label)
                _patches.append(patch)

            # add labels
            if user_kwargs["annotation_properties"].get(
                "show_labels", self.config.interactive_ms_annotations_labels):
                text_annot_ypos.append(user_kwargs['plot_properties'].get(
                    "waterfall_increment", self.config.interactive_waterfall_increment) * i)
                text_annot_label.append(_replace_labels(label))

            # collect plot data for limit determination
            _ydata.extend(yval + user_kwargs['plot_properties'].get(
                "waterfall_increment", self.config.interactive_waterfall_increment) * i)
            _lines.append(line)
            _original_colors.append(color)
            i = i - 1

        xlimits = [np.min(xvals_list), np.max(xvals_list)]
        xlimits = self._check_limits(xlimits, plt_kwargs['_xlimits_'])

        _ydata = remove_nan_from_list(_ydata)
        ylimits = [np.min(_ydata), np.max(_ydata) * 1.05]
        ylimits = self._check_limits(ylimits, plt_kwargs['_ylimits_'])

        # add labels
        labels = None
        
        # add annotations
        if ("annotations" in data and len(data["annotations"]) > 0 and 
            user_kwargs["annotation_properties"].get("show_annotations", plt_kwargs['show_annotations'])):
            quad_source, label_source, __ = self._prepare_annotations(data, yvals, y_offset=user_kwargs['plot_properties'].get(
                "waterfall_increment", self.config.interactive_waterfall_increment) * len(xvals))


            if user_kwargs["annotation_properties"].get(
                        "show_patches", self.config.interactive_ms_annotations_highlight):
                bokehPlot.quad(top="top", bottom="bottom", left="left", right="right",
                                color="color", 
                                fill_alpha=user_kwargs["annotation_properties"].get(
                                    "patch_transparency", self.config.interactive_ms_annotations_transparency),
                                source=quad_source,
                                name="ignore_hover")

            if user_kwargs["annotation_properties"].get(
                        "show_labels", self.config.interactive_ms_annotations_labels):
                bokehPlot, labels = self._add_plot_labels(bokehPlot, data, label_source, plot_type="waterfall")


        # setup labels
        bokehPlot.xaxis.axis_label = xlabel
        bokehPlot.yaxis.axis_label = ylabel

        # setup common parameters
        js_kwargs = dict(xlimits=xlimits, ylimits=ylimits)
        bokehPlot = self._setupPlotParameters(bokehPlot, plot_type="Waterfall", data=data, **js_kwargs)
        plot_mods = {}
        # add widgets
        if (user_kwargs["widgets"].get("add_custom_widgets", self.config.interactive_custom_scripts) and 
            bkh_kwargs['page_layout'] in ["Individual", "Columns"]):
            _cvd_colors = self.presenter.view.panelPlots.onChangePalette(None, cmap=self.config.interactive_cvd_cmap,
                                                                        n_colors=len(_lines),
                                                                        return_colors=True, return_hex=True)
            js_type, js_code = [], {}
            if user_kwargs["widgets"].get("colorblind_safe_1D", True):
                js_code.update(lines=_lines, original_colors=_original_colors,
                               cvd_colors=_cvd_colors, patches=_patches)
                js_type.extend(["colorblind_safe_1D"])

            if user_kwargs["widgets"].get("hover_mode", True):
                js_code.update(hover=hoverTool)
                js_type.extend(["hover_mode"])

            if user_kwargs["legend_properties"].get("legend", plt_kwargs['add_legend']) and len(bokehPlot.legend) > 0:
                js_code.update(legend=bokehPlot.legend[0])
                if user_kwargs["widgets"].get("legend_toggle", True): js_type.extend(["legend_toggle"])
                if user_kwargs["widgets"].get("legend_position", True): js_type.extend(["legend_position"])
                if user_kwargs["widgets"].get("legend_orientation", True): js_type.extend(["legend_orientation"])
                if user_kwargs["widgets"].get("legend_transparency", True): js_type.extend(["legend_transparency"])

            if labels is not None:
                js_code.update(labels=labels, y_range_shown=ylimits[1], y_range_hidden=ylimits[1])
                if user_kwargs["widgets"].get("label_toggle", True): js_type.extend(["label_toggle"])
                if user_kwargs["widgets"].get("label_size_slider", True): js_type.extend(["label_size_slider"])
                if user_kwargs["widgets"].get("label_rotation", True): js_type.extend(["label_rotation"])
                if user_kwargs["widgets"].get("label_offset_x", True): js_type.extend(["label_offset_x"])
                if user_kwargs["widgets"].get("label_offset_y", True): js_type.extend(["label_offset_y"])

            if len(js_type) > 0:
                bokehPlot = self.add_custom_js_widgets(bokehPlot, js_type=js_type, data=data, **js_code)
        elif (user_kwargs["widgets"].get("add_custom_widgets", self.config.interactive_custom_scripts) and 
              bkh_kwargs['page_layout'] not in ["Individual", "Columns"]):
            _cvd_colors = self.presenter.view.panelPlots.onChangePalette(None, cmap=self.config.interactive_cvd_cmap, n_colors=len(_lines),
                                                                         return_colors=True, return_hex=True)
            plot_mods.update(lines=_lines, original_colors=_original_colors, cvd_colors=_cvd_colors,
                             patches=_patches)
            self.presenter.onThreading(None, ("Adding widgets to 'Grid'/'Rows' is not supported at the moment." , 4),
                                       action='updateStatusbar')

        return [bokehPlot, plt_kwargs['plot_width'], plt_kwargs['plot_height'], plot_mods]

    def _add_plot_waterfall_overlay(self, data, **bkh_kwargs):
        plt_kwargs = self._buildPlotParameters(data)
        user_kwargs = deepcopy(data['interactive_params'])

        # get plot data
        xvals = data['xvals']
        yvals = data['yvals']
        zvals = data['zvals']
        xlabel = data['xlabel']
        ylabel = data['ylabel']
        colorList = data['colors']
        labels = data['labels']
        count = len(xvals)

        # swap labels in some cases
        if xlabel not in ["m/z", "Mass (Da)", "Charge"]:
            xlabel, ylabel = ylabel, xlabel

        ylabel = "Offset intensity"
        
        # create hover tool
        hoverTool = HoverTool(tooltips=[(xlabel, '@xvals{0.00}'),
                                          (ylabel, '@yvals{0.00}'),
                                          ("Dataset", '@dataset'),
                                          ("Label", "@label")],
                              mode=plt_kwargs['hover_mode'])
        # Prepare MS file
        TOOLS = self._check_tools(hoverTool, data)

        xvals_list, __ = find_limits_list(xvals, yvals)
        
        # create figure
        bokehPlot = figure(tools=TOOLS,
                           title=bkh_kwargs['title'],
                           active_drag=user_kwargs['tools'].get("active_drag", "auto"),
                           active_scroll=user_kwargs['tools'].get("active_wheel", "auto"),
                           plot_width=plt_kwargs["plot_width"],
                           plot_height=plt_kwargs["plot_height"],
                           toolbar_location=user_kwargs['tools'].get("position", self.config.toolsLocation),
                           toolbar_sticky=False)
        
        # generate labels
        if len(labels) == 0:
            labels = [" "] * count

        # get colorblind colors
        cvd_colors = self.presenter.view.panelPlots.onChangePalette(
            None, cmap=self.config.interactive_cvd_cmap, n_colors=len(xvals), return_colors=True, return_hex=True)
        
        # add plots
        _ydata = []
        _lines, _patches, _original_colors, _cvd_colors = [], [], [], []
        for item in xrange(len(xvals)):
            xval = xvals[item]
            yval = yvals[item]
            zval = zvals[item]
            dataset = labels[item]
            line_color = convertRGB1toHEX(colorList[item])
            shade_color = convertRGB1toHEX(colorList[item])
            for irow in xrange(len(yval)):
                if irow > 0: 
                    label = ""
                
                yOffset = user_kwargs['plot_properties'].get(
                    "waterfall_increment", self.config.interactive_waterfall_increment) * irow
                label = str(yval[irow])
                y = zval[:, irow] + yOffset
                # create source
                source = ColumnDataSource(
                    data=dict(xvals=xval, yvals=y, 
                              dataset=([dataset] * len(xval)),
                              label=([label] * len(xval))))

                # generate legend label
                if not user_kwargs['legend_properties'].get(
                    "legend", self.config.interactive_legend): 
                    legend_label = None
                elif irow == 0: 
                    legend_label = dataset
                else: 
                    legend_label = None
                    
                line = bokehPlot.line(
                    x="xvals", y="yvals",
                    line_color=line_color,
                    line_width=user_kwargs["plot_properties"]["line_width"],
                    line_alpha=user_kwargs["plot_properties"]["line_transparency"],
                    line_dash=user_kwargs["plot_properties"]["line_style"],
                    legend=legend_label,
                    muted_alpha=user_kwargs['legend_properties'].get("legend_mute_alpha", self.config.interactive_legend_mute_alpha),
                    muted_color=line_color,
                    source=source)
                
                # add underline patch
                if user_kwargs['plot_properties'].get(
                    "waterfall_shade_under", self.config.interactive_waterfall_shade_under):
                    patch = bokehPlot.patch(
                        "xvals", "yvals", 
                        color=shade_color, 
                        fill_alpha=user_kwargs['plot_properties'].get(
                            "waterfall_shade_transparency", self.config.interactive_waterfall_shade_alpha),
                        line_alpha=0., source=source, legend=legend_label)
                    _patches.append(patch)
                    
                _ydata.extend(y)
                _lines.append(line)
                _original_colors.append(line_color)
                _cvd_colors.append(cvd_colors[item])


        xvals_list, __ = find_limits_list(xvals, yvals)
        xlimits = [np.min(xvals_list), np.max(xvals_list)]
        xlimits = self._check_limits(xlimits, plt_kwargs['_xlimits_'])

        ylimits = [np.min(_ydata), np.max(_ydata)]
        # setup labels
        bokehPlot.xaxis.axis_label = xlabel
        bokehPlot.yaxis.axis_label = ylabel

        # setup common parameters
        js_kwargs = dict(xlimits=xlimits, ylimits=ylimits)
        bokehPlot = self._setupPlotParameters(bokehPlot, plot_type="Waterfall_overlay", data=data, **js_kwargs)
        
        # add widgets        
        if user_kwargs["widgets"].get("add_custom_widgets", self.config.interactive_custom_scripts):
            # get cvd colors
            js_type, js_code = [], {}

            if user_kwargs["widgets"].get("colorblind_safe_1D", True):
                js_code.update(lines=_lines, original_colors=_original_colors,
                               cvd_colors=_cvd_colors, patches=_patches)
                js_type.extend(["colorblind_safe_1D"])

            if user_kwargs["widgets"].get("hover_mode", True):
                js_code.update(hover=hoverTool)
                js_type.extend(["hover_mode"])

            if (user_kwargs['legend_properties'].get(
                "legend", self.config.interactive_legend) and 
                len(bokehPlot.legend) > 0):
                js_code.update(legend=bokehPlot.legend[0])
                if user_kwargs["widgets"].get("legend_toggle", True):
                    js_type.extend(["legend_toggle"])
                if user_kwargs["widgets"].get("legend_position", True):
                    js_type.extend(["legend_position"])
                if user_kwargs["widgets"].get("legend_orientation", True):
                    js_type.extend(["legend_orientation"])
                if user_kwargs["widgets"].get("legend_transparency", True):
                    js_type.extend(["legend_transparency"])

            bokehPlot = self.add_custom_js_widgets(bokehPlot, js_type=js_type, data=data, **js_code)

        return [bokehPlot, plt_kwargs['plot_width'], plt_kwargs['plot_height']]

    def _add_plot_grid_2to1(self, data, **bkh_kwargs):
        plt_kwargs = self._buildPlotParameters(data)
        user_kwargs = deepcopy(data['interactive_params'])

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

        hoverTool = HoverTool(tooltips=[(xlabel, '$x{0}'), (ylabel, '$y{0}'),
                                        ('Intensity', '@image')],
                            point_policy='follow_mouse')

        TOOLS = self._check_tools(hoverTool, data)

        colorMapper_top_left, colormap_top_left = self._convert_cmap_to_colormapper(cmap_1, zvals=zvals_1, return_palette=True)
        colorMapper_bottom_left, colormap_bottom_left = self._convert_cmap_to_colormapper(cmap_2, zvals=zvals_2, return_palette=True)
        colorMapper_right, colormap_right = self._convert_cmap_to_colormapper("coolwarm", zvals=zvals_cum, return_palette=True)

        top_left = figure(x_range=(min(xvals), max(xvals)),
                          y_range=(min(yvals), max(yvals)),
                          tools=TOOLS,
                          active_drag=user_kwargs['tools'].get("active_drag", "auto"),
                          active_scroll=user_kwargs['tools'].get("active_wheel", "auto"),
                          plot_width=int(self.config.figWidth * 0.5),
                          plot_height=int(self.config.figHeight * 0.5),
                          toolbar_location=user_kwargs['tools'].get("position", self.config.toolsLocation),
                          toolbar_sticky=False)

        top_left.image(source=cds_top_left, image='image', x='x', y='y', dw='dw', dh='dh', palette=colormap_top_left)
        top_left.yaxis.axis_label = ylabel

        bottom_left = figure(x_range=top_left.x_range,
                             y_range=top_left.y_range,
                             tools=TOOLS,
                             active_drag=user_kwargs['tools'].get("active_drag", "auto"),
                             active_scroll=user_kwargs['tools'].get("active_wheel", "auto"),
                             plot_width=int(self.config.figWidth * 0.5), plot_height=int(self.config.figHeight * 0.5),
                             toolbar_location=user_kwargs['tools'].get("position", self.config.toolsLocation),
                             toolbar_sticky=False)

        bottom_left.image(source=cds_bottom_left, image='image', x='x', y='y', dw='dw', dh='dh', palette=colormap_bottom_left)
        bottom_left.xaxis.axis_label = xlabel
        bottom_left.yaxis.axis_label = ylabel

        right = figure(x_range=top_left.x_range,
                       y_range=top_left.y_range,
                       tools=TOOLS,
                       active_drag=user_kwargs['tools'].get("active_drag", "auto"),
                       active_scroll=user_kwargs['tools'].get("active_wheel", "auto"),
                       plot_width=self.config.figWidth, plot_height=(self.config.figHeight),
                       toolbar_location=user_kwargs['tools'].get("position", self.config.toolsLocation),
                       toolbar_sticky=False)

        right.image(source=cds_right_left, image='image', x='x', y='y', dw='dw', dh='dh', palette=colormap_right)
        right.xaxis.axis_label = xlabel

        kwargs = {'tight_layout':True}
        top_left = self._setupPlotParameters(top_left, plot_type="2D", data=data, **kwargs)
        bottom_left = self._setupPlotParameters(bottom_left, plot_type="2D", data=data, **kwargs)
        right = self._setupPlotParameters(right, plot_type="2D", data=data, **kwargs)

        left_column = column(top_left, bottom_left)
        bokehPlot = gridplot([[left_column, right]], sizing_mode="fixed")

        return [bokehPlot, plt_kwargs['plot_width'], plt_kwargs['plot_height']]

    def _add_plot_grid_NxN_2D(self, data, **bkh_kwargs):
        plt_kwargs = self._buildPlotParameters(data)
        user_kwargs = deepcopy(data['interactive_params'])
        
        zvals_list = data['zvals_list']
        cmap_list = data['cmap_list']
        title_list = data['title_list']
        xvals = data['xvals']
        yvals = data['yvals']
        xlabel = data['xlabels']
        ylabel = data['ylabels']
        plot_parameters = data['plot_parameters']

        if xlabel == "": hover_xlabel = "x"
        else: hover_xlabel = xlabel
        if ylabel == "": hover_ylabel = "y"
        else: hover_ylabel = ylabel

        hoverTool = HoverTool(tooltips=[(hover_xlabel, '$x{0.00}'),
                                        (hover_ylabel, '$y{0.00}'),
                                        ('Intensity', '@image')],
                            point_policy='follow_mouse')

        TOOLS = self._check_tools(hoverTool, data)

        plot_list = []
        n_grid = len(zvals_list)
        for i, zvals in enumerate(zvals_list):
            row = int(i // plot_parameters["n_cols"])
            col = i % plot_parameters["n_cols"]

            if len(xvals) == n_grid:
                xmin, xmax = np.min(xvals[i]), np.max(xvals[i])
                ymin, ymax = np.min(yvals[i]), np.max(yvals[i])
            else:
                xmin, xmax = np.min(xvals), np.max(xvals)
                ymin, ymax = np.min(yvals), np.max(yvals)

            data = dict(image=[zvals], x=[xmin], y=[ymin], dw=[xmax - xmin], dh=[ymax - ymin])
            cds = ColumnDataSource(data=data)
            colorMapper, colormap = self._convert_cmap_to_colormapper(cmap_list[i], zvals=zvals, return_palette=True)
            plot_size_x = data.get("interactive_params", {}).get("grid_NxN", {}).get("plot_width", 400)
            plot_size_y = data.get("interactive_params", {}).get("grid_NxN", {}).get("plot_height", 400)
            if data.get("interactive_params", {}).get("grid_NxN", {}).get("link_xy", True):
                if i == 0:
                    plot = figure(x_range=(xmin, xmax),
                                  y_range=(ymin, ymax),
                                  tools=TOOLS, title=title_list[i],
                                  active_drag=user_kwargs['tools'].get("active_drag", "auto"),
                                  active_scroll=user_kwargs['tools'].get("active_wheel", "auto"),
                                  plot_width=plot_size_x, plot_height=plot_size_y,
                                  toolbar_location=user_kwargs['tools'].get("position", self.config.toolsLocation),
                                  toolbar_sticky=False)
                else:
                    plot = figure(x_range=plot_list[0].x_range,
                                  y_range=plot_list[0].y_range,
                                  tools=TOOLS, title=title_list[i],
                                  active_drag=user_kwargs['tools'].get("active_drag", "auto"),
                                  active_scroll=user_kwargs['tools'].get("active_wheel", "auto"),
                                  plot_width=plot_size_x, plot_height=plot_size_y,
                                  toolbar_location=user_kwargs['tools'].get("position", self.config.toolsLocation),
                                  toolbar_sticky=False)
            else:
                plot = figure(x_range=(xmin, xmax), y_range=(ymin, ymax),
                              tools=TOOLS, title=title_list[i],
                              active_drag=user_kwargs['tools'].get("active_drag", "auto"),
                              active_scroll=user_kwargs['tools'].get("active_wheel", "auto"),
                              plot_width=plot_size_x, plot_height=plot_size_y,
                              toolbar_location=user_kwargs['tools'].get("position", self.config.toolsLocation),
                              toolbar_sticky=False)

            plot.image(source=cds, image='image', x='x', y='y', dw='dw', dh='dh', palette=colormap)

            if col == 0:
                plot.yaxis.axis_label = ylabel
            if row == plot_parameters['n_rows'] - 1:
                plot.xaxis.axis_label = xlabel

            # Add RMSD label to the plot
            if plt_kwargs['title_label']:
                plot = self._add_grid_label(plot, title_list[i],
                                            plt_kwargs['xpos'], plt_kwargs['ypos'])


            kwargs = {'tight_layout':True}
            plot = self._setupPlotParameters(plot, plot_type="2D", data=data, **kwargs)
            plot_list.append(plot)

            bokehPlot = gridplot(plot_list, ncols=plot_parameters['n_cols'], merge_tools=False)

        plt_kwargs['plot_width'] = plot_size_x * plot_parameters["n_cols"]
        plt_kwargs['plot_height'] = plot_size_y * plot_parameters["n_rows"]
        return [bokehPlot, plt_kwargs['plot_width'], plt_kwargs['plot_height']]

    def _add_plot_grid_NxN_scatter(self, data, **bkh_kwargs):
        plt_kwargs = self._buildPlotParameters(data)
        user_kwargs = deepcopy(data['interactive_params'])
        
        xvals = data['xvals']
        yvals = data['yvals']
        xlabel = data['xlabel']
        xlabels = data['xlabels']
        ylabel = data['ylabel']
        ylabels = data['ylabels']
        labels = data['labels']
        colors_list = data['colors']
        plot_modifiers = data["plot_modifiers"]
        itemColors = data["itemColors"]
        itemLabels = data["itemLabels"]
        xvalsErr = data['xvalsErr']
        yvalsErr = data['yvalsErr']
        n_cols, n_rows, n_grid = plot_modifiers['n_cols'], plot_modifiers['n_rows'], plot_modifiers['n_grid']

        # check in case only one item was passed
        # assumes xvals is a list in a list
        if len(xvals) != len(yvals) and len(xvals) == 1:
            xvals = xvals * len(yvals)

        # check length of labels
        if len(labels) != len(yvals):
            labels = [""] * len(yvals)

        n_xvals = len(xvals)
        n_yvals = len(yvals)

        # check if labels were added
        if len(xlabels) != n_xvals:
            xlabels = [xlabel] * n_xvals

        if len(ylabels) != n_yvals:
            ylabels = [ylabel] * n_yvals

        # find limits
        xlimits, ylimits = find_limits_all(xvals, yvals)

        plot_list = []
        for i in range(n_grid):
            row = int(i // n_cols)
            col = i % n_cols

            xval = xvals[i]
            yval = yvals[i]
            yval_size = len(yval)
            color = colors_list[i]
            label = labels[i]
            xmin, xmax = np.min(xval), np.max(xval)
            ymin, ymax = np.min(yval), np.max(yval)
            _tooltips = [(xlabel, '@xvals{0.00}'),
                         (ylabel, '@yvals{0.00}')]


            if len(itemColors) > 0 and len(itemColors[0]) == yval_size:
                color = self._convert_color_list(itemColors[0])
            else:
                color = colors_list[i]

            if self.config.interactive_scatter_sameAsFill:
                edge_color = color
            else:
                edge_color = convertRGB1toHEX(self.config.interactive_scatter_edge_color)

            # generate color list
            if len(color) != yval_size:
                color = [color] * yval_size
            if len(edge_color) != yval_size:
                edge_color = [edge_color] * yval_size

            _sourceDict = dict(xvals=xval, yvals=yval, color=color, edge_color=edge_color)
            if len(xvalsErr) == len(yvals) and len(xvalsErr[i]) == yval_size:
                _sourceDict["xvalsErr"] = xvalsErr[i]
                _tooltips.append(("Error (x)", '@xvalsErr{0.00}'))

            if len(yvalsErr) == len(yvals) and len(yvalsErr[i]) == yval_size:
                _sourceDict["yvalsErr"] = yvalsErr[i]
                _tooltips.append(("Error (y)", '@yvalsErr{0.00}'))

            if plot_modifiers.get("bokeh_add_dataset_label", False):
                _sourceDict["labels"] = [labels[i]] * yval_size

            if plot_modifiers.get("label_items", False):
                _sourceDict["itemLabels"] = itemLabels[0]
                _tooltips.append(("Label", '@itemLabels'))

            xlabel = _replace_labels(xlabels[i])
            ylabel = _replace_labels(ylabels[i])


            hoverTool = HoverTool(tooltips=_tooltips,
                                  point_policy='follow_mouse')
            TOOLS = self._check_tools(hoverTool, data)

            plot_size_x, plot_size_y = 300, 300
            if i == 0:
                x_range, y_range = xlimits, ylimits
            else:
                x_range, y_range = plot_list[0].x_range, plot_list[0].y_range
                
            plot = figure(x_range=x_range, y_range=y_range,
                          tools=TOOLS,
                          title=label,
                          active_drag=user_kwargs['tools'].get("active_drag", "auto"),
                          active_scroll=user_kwargs['tools'].get("active_wheel", "auto"),
                          plot_width=plot_size_x, plot_height=plot_size_y,
                          toolbar_location=user_kwargs['tools'].get("position", self.config.toolsLocation),
                          toolbar_sticky=False)

            try: label = labels[i]
            except: label = " "
            source = ColumnDataSource(data=_sourceDict)

            plot.scatter(x="xvals", y="yvals",
                              color="color", line_color="edge_color",
                              marker=user_kwargs['plot_properties'].get("scatter_shape", self.config.interactive_scatter_marker),
                              fill_alpha=user_kwargs['plot_properties'].get("scatter_transparency", self.config.interactive_scatter_alpha),
                              size=user_kwargs['plot_properties'].get("scatter_line_width", self.config.interactive_scatter_size),
                              line_width=user_kwargs['plot_properties'].get("scatter_line_width", self.config.interactive_scatter_lineWidth),
                              muted_alpha=user_kwargs['legend_properties'].get("legend_mute_alpha", self.config.interactive_legend_mute_alpha),
                              source=source,
                              legend=label)

            plot.xaxis.axis_label = xlabel
            plot.yaxis.axis_label = ylabel

            kwargs = {'tight_layout':True}
            plot = self._setupPlotParameters(plot, plot_type="2D", data=data, **kwargs)
            plot_list.append(plot)

        plt_kwargs['plot_width'] = plot_size_x * n_cols
        plt_kwargs['plot_height'] = plot_size_y * n_rows
        bokehPlot = gridplot(plot_list, ncols=n_cols)

        return [bokehPlot, plt_kwargs['plot_width'], plt_kwargs['plot_height']]

    def _add_plot_grid_NxN_1D(self, data, **bkh_kwargs):
        plt_kwargs = self._buildPlotParameters(data)
        user_kwargs = deepcopy(data['interactive_params'])
        
        xvals = data['xvals']
        yvals = data['yvals']
        xlabel = data['xlabel']
        xlabels = data['xlabels']
        ylabel = data['ylabel']
        ylabels = data['ylabels']
        labels = data['labels']
        colors_list = data['colors']
        plot_modifiers = data["plot_modifiers"]
        n_cols, n_rows, n_grid = plot_modifiers['n_cols'], plot_modifiers['n_rows'], plot_modifiers['n_grid']

        # check in case only one item was passed
        # assumes xvals is a list in a list
        if len(xvals) != len(yvals) and len(xvals) == 1:
            xvals = xvals * len(yvals)

        # check length of labels
        if len(labels) != len(yvals):
            labels = [""] * len(yvals)

        n_xvals = len(xvals)
        n_yvals = len(yvals)

        # check if labels were added
        if len(xlabels) != n_xvals:
            xlabels = [xlabel] * n_xvals

        if len(ylabels) != n_yvals:
            ylabels = [ylabel] * n_yvals

        plot_list = []
        for i in range(n_grid):
            row = int(i // n_cols)
            col = i % n_cols

            xval = xvals[i]
            yval = yvals[i]
            color = colors_list[i]
            label = labels[i]
            xmin, xmax = np.min(xval), np.max(xval)
            ymin, ymax = np.min(yval), np.max(yval)

            xlabel = _replace_labels(xlabels[i])
            ylabel = _replace_labels(ylabels[i])

            hoverTool = HoverTool(tooltips=[(xlabel, '$x{0.00}'),
                                            (ylabel, '$y{0.00}')],
                                point_policy='follow_mouse')
            TOOLS = self._check_tools(hoverTool, data)

            plot_size_x, plot_size_y = 500, 300
            plot = figure(x_range=(xmin, xmax),
                          y_range=(ymin, ymax),
                          tools=TOOLS,
                          title=label,
                          active_drag=user_kwargs['tools'].get("active_drag", "auto"),
                          active_scroll=user_kwargs['tools'].get("active_wheel", "auto"),
                          plot_width=plot_size_x, plot_height=plot_size_y,
                          toolbar_location=user_kwargs['tools'].get("position", self.config.toolsLocation),
                          toolbar_sticky=False)

            if (user_kwargs["preprocessing_properties"]["linearize"] and
                len(xval) > user_kwargs["preprocessing_properties"].get("linearize_limit", 25000)):
                # TODO: implement better downsampling
                # downsampling: https://github.com/devoxi/lttb-py/blob/master/lttb/lttb.py
                xval, yval = self.linearize_spectrum(
                xval, yval, user_kwargs["preprocessing_properties"]["linearize_binsize"])

            try: color = convertRGB1toHEX(color)
            except (SyntaxError, ValueError): pass
            source = ColumnDataSource(data=dict(xvals=xval, yvals=yval))
            plot.line(x="xvals", y="yvals",
                      line_color=color,
                      line_width=user_kwargs["plot_properties"]["line_width"],
                      line_alpha=user_kwargs["plot_properties"]["line_transparency"],
                      line_dash=user_kwargs["plot_properties"]["line_style"],
                      muted_alpha=user_kwargs['legend_properties'].get("legend_mute_alpha", self.config.interactive_legend_mute_alpha),
                      muted_color=color,
                      source=source)
            if plt_kwargs['overlay_shade']:
                plot.patch(
                    "xvals", "yvals", color=color, 
                    fill_alpha=plt_kwargs['overlay_shade_transparency'],
                    line_alpha=0., source=source)

            plot.xaxis.axis_label = xlabel
            plot.yaxis.axis_label = ylabel

            kwargs = {'tight_layout':True}
            plot = self._setupPlotParameters(plot, plot_type="2D", data=data, **kwargs)
            plot_list.append(plot)

        plt_kwargs['plot_width'] = plot_size_x * n_cols
        plt_kwargs['plot_height'] = plot_size_y * n_rows

        bokehPlot = gridplot(plot_list, ncols=n_cols, merge_tools=False)

        return [bokehPlot, plt_kwargs['plot_width'], plt_kwargs['plot_height']]

    def _add_plot_barchart(self, data, **bkh_kwargs):
        plt_kwargs = self._buildPlotParameters(data)
        user_kwargs = deepcopy(data['interactive_params'])
        
        xvals = data['xvals']
        yvals_min = data['yvals_min']
        yvals_max = data['yvals_max']
        xlabel = _replace_labels(data['xlabel'])
        ylabel = _replace_labels(data['ylabel'])
        itemColors = data['itemColors']
        itemLabels = data['itemLabels']
        _colors = data['colors']
        plot_modifiers = data["plot_modifiers"]
        legend_labels = plot_modifiers["legend_labels"]
        hoverLabels = data.get('hover_labels', [])

        xvals_count = len(xvals)
        yvals_min_count = len(yvals_min)
        yvals_max_count = len(yvals_max)
        
        if yvals_min_count > 1 or yvals_max_count > 1:
            if xvals_count < yvals_min_count or xvals_count < yvals_max_count:
                xvals = xvals * yvals_min_count

        if len(_colors) != len(xvals):
            _colors = self._get_colors(len(xvals))

        if bkh_kwargs['plot_type'] == "H-bar":
            _tooltips = [(ylabel, '@xvals{0.00}'),
                         ("Min / max", '@yvals_min{0.00} / @yvals_max{0.00}'),
                         ("Width", '@yvals_height{0.00}')]
        else:
            _tooltips = [(xlabel, '@xvals{0.00}'),
                         ("Min / max", '@yvals_min{0.00} / @yvals_max{0.00}'),
                         ("Height", '@yvals_height{0.00}')]

        if len(legend_labels) == len(xvals):
            _tooltips.append(("Dataset", '@dataset'))

        if len(itemLabels) > 0:
            for i in xrange(len(itemLabels)):
                try: hover_label = hoverLabels[i]
                except:
                    if len(itemLabels) == 1:
                        hover_label = "Label"
                    else:
                        hover_label = "Label ({})".format(i)
                _tooltips.append((_replace_labels(hover_label), '@labels_{}'.format(i)))

        hoverTool = HoverTool(tooltips=_tooltips, mode="mouse")
        TOOLS = self._check_tools(hoverTool, data)

        bokehPlot = figure(tools=TOOLS, title=bkh_kwargs['title'],
                           active_drag=user_kwargs['tools'].get("active_drag", "auto"),
                           active_scroll=user_kwargs['tools'].get("active_wheel", "auto"),
                           plot_width=plt_kwargs["plot_width"],
                           plot_height=plt_kwargs["plot_height"],
                           toolbar_location=user_kwargs['tools'].get("position", self.config.toolsLocation),
                           toolbar_sticky=False)

        # iterate over list of bar containers
        for i in xrange(len(xvals)):
            xval = xvals[i]
            yval_min = yvals_min[i]
            yval_max = yvals_max[i]
            _sourceDict = dict(xvals=xval, yvals_min=yval_min, yvals_max=yval_max,
                               yvals_height=yval_max - yval_min)

            # get labels
            if len(itemLabels) > 0:
                for ilabel in xrange(len(itemLabels)):
                    dict_label = "labels_{}".format(ilabel)
                    if len(itemLabels[ilabel]) == len(xval):
                        _labels = itemLabels[ilabel]
                    else:
                        _labels = len(xval) * ""
                    _sourceDict[dict_label] = _labels

            # convert colors back to hex
            if len(itemColors) > 0 and len(itemColors) == yvals_max_count:
                if len(itemColors[i]) == len(xval):
                    colorList = []
                    for color in itemColors[i]:
                        colorList.append(convertRGB1toHEX(color))
                else:
                    colorList = len(xval) * [_colors[i]]
            else:
                colorList = len(xval) * [_colors[i]]

            if user_kwargs['plot_properties'].get("bar_edge_color_sameAsFill", self.config.interactive_bar_sameAsFill):
                linecolorList = colorList
            else:
                edgecolor = [convertRGB1toHEX(user_kwargs['plot_properties'].get("bar_edge_color", self.config.interactive_bar_edge_color))]
                linecolorList = len(xval) * edgecolor
            _sourceDict.update(colors=colorList, linecolors=linecolorList)

            if len(legend_labels) == len(xvals):
                _sourceDict["dataset"] = [_replace_labels(legend_labels[i])] * len(xval)

            source = ColumnDataSource(data=_sourceDict)
            if bkh_kwargs['plot_type'] == "H-bar":
                bokehPlot.hbar(y="xvals", left='yvals_min', right='yvals_max', source=source,
                               color="colors", line_color="linecolors",
                               height=user_kwargs['plot_properties'].get(
                                   "bar_width", self.config.interactive_bar_width),
                               fill_alpha=user_kwargs['plot_properties'].get(
                                   "bar_transparency", self.config.interactive_bar_alpha),
                               line_width=user_kwargs['plot_properties'].get(
                                   "bar_line_width", self.config.interactive_bar_lineWidth),
                               )
            else:
                bokehPlot.vbar(x="xvals", top='yvals_min', bottom='yvals_max', source=source,
                               color="colors", line_color="linecolors",
                               width=user_kwargs['plot_properties'].get(
                                   "bar_width", self.config.interactive_bar_width),
                               fill_alpha=user_kwargs['plot_properties'].get(
                                   "bar_transparency", self.config.interactive_bar_alpha),
                               line_width=user_kwargs['plot_properties'].get(
                                   "bar_line_width", self.config.interactive_bar_lineWidth)
                               
                               )
                
        ylimits = [bokehPlot.y_range.start, bokehPlot.y_range.end]
        ylimits = self._check_limits(ylimits, plt_kwargs['_ylimits_'])
        
        # setup labels
        bokehPlot.xaxis.axis_label = xlabel
        bokehPlot.yaxis.axis_label = ylabel

        kwargs = {"bar_type":type, "ylimits":ylimits}
        # setup common plot parameters
        bokehPlot = self._setupPlotParameters(bokehPlot, plot_type="1D", data=data, **kwargs)        
        
        if ("annotations" in data and len(data["annotations"]) > 0 and 
            user_kwargs["annotation_properties"].get("show_annotations", plt_kwargs['show_annotations'])):
            __, label_source, __ = self._prepare_annotations(data, yvals=None, ylimits=ylimits)
            bokehPlot, labels = self._add_plot_labels(bokehPlot, data, label_source, plot_type="waterfall")
            
        # setup widgets
        if user_kwargs["widgets"].get("add_custom_widgets", self.config.interactive_custom_scripts):
            js_type, js_code = [], {}            

            if labels is not None:
                js_code.update(labels=labels, y_range_shown=ylimits[1], y_range_hidden=ylimits[1])
                if user_kwargs["widgets"].get("label_toggle", True): js_type.extend(["label_toggle"])
                if user_kwargs["widgets"].get("label_size_slider", True): js_type.extend(["label_size_slider"])
                if user_kwargs["widgets"].get("label_rotation", True): js_type.extend(["label_rotation"])
                if user_kwargs["widgets"].get("label_offset_x", True): js_type.extend(["label_offset_x"])
                if user_kwargs["widgets"].get("label_offset_y", True): js_type.extend(["label_offset_y"])
                
            if len(js_type) > 0: 
                bokehPlot = self.add_custom_js_widgets(bokehPlot, js_type=js_type, data=data, **js_code)

        return [bokehPlot, plt_kwargs['plot_width'], plt_kwargs['plot_height']]

    def _add_colorbar(self, bokehPlot, zvals, color_mapper, modify_ticks=True, as_percentage=False,
                      return_colorbar=False, data={}, **kwargs):
        """
        Add colorbar to bokeh plot
        ===
        bokehPlot : bokeh object
            bokeh plot object
        zvals : numpy array
            data array
        color_mapper : bokeh colorMapper object
        modify_ticks : bool
            decide whether ticks should be modified
        as_percentage : bool
            decide whether ticks should be 'values' or 'percentages'
        data : dict
            data dictionary with 'interactive_params' settings
        return_colorbar : bool
            decide whether colorbar should also be returned
        """
        user_kwargs = deepcopy(data['interactive_params'])

        if modify_ticks:
            if as_percentage:
                zmin, zmax = np.round(np.min(zvals), 10), np.round(np.max(zvals), 10)
                zmid = np.round(np.max(zvals) / 2., 10)
                ticker = FixedTicker(ticks=[zmin, zmid, zmax])
                formatter = FuncTickFormatter(code="""
                data = {zmin: '0', zmid: '%', zmax: '100'}
                return data[tick]
                """.replace("zmin", str(zmin)).replace("zmid", str(zmid)).replace("zmax", str(zmax)))
            else:
                ticker = FixedTicker(ticks=[-1., 0., 1.])
                formatter = BasicTickFormatter(
                    precision=user_kwargs["colorbar_properties"].get(
                        "precision", self.config.interactive_colorbar_precision),
                    use_scientific=user_kwargs["colorbar_properties"].get(
                        "use_scientific", self.config.interactive_colorbar_useScientific))
        else:
            ticker = AdaptiveTicker()
            formatter = BasicTickFormatter(
                precision=user_kwargs["colorbar_properties"].get(
                    "precision", self.config.interactive_colorbar_precision),
                use_scientific=user_kwargs["colorbar_properties"].get(
                    "use_scientific", self.config.interactive_colorbar_useScientific))



        colorbar = ColorBar(
            color_mapper=color_mapper, ticker=ticker, formatter=formatter,
            label_standoff=user_kwargs["colorbar_properties"].get(
                "label_offset", self.config.interactive_colorbar_label_offset),
            location=(user_kwargs["colorbar_properties"].get(
                "position_offset_x", self.config.interactive_colorbar_offset_x),
                      user_kwargs["colorbar_properties"].get(
                "position_offset_y", self.config.interactive_colorbar_offset_y)),
            orientation=user_kwargs["colorbar_properties"].get(
                "orientation", self.config.interactive_colorbar_orientation),
            width=data.get("interactive_params", {}).get(
                "colorbar_properties", {}).get("width", "auto"),
            height=data.get("interactive_params", {}).get(
                "colorbar_properties", {}).get("height", "auto"),
            padding=data.get("interactive_params", {}).get(
                "colorbar_properties", {}).get("pad", self.config.interactive_colorbar_padding),
            bar_line_width=data.get("interactive_params", {}).get(
                "colorbar_properties", {}).get("edge_width", self.config.interactive_colorbar_edge_width),
            bar_line_color=convertRGB1to255(data.get("interactive_params", {}).get(
                "colorbar_properties", {}).get("edge_color", self.config.interactive_colorbar_edge_color),
                                                as_integer=True, as_tuple=True),
            bar_line_cap="square",
            major_tick_line_color=convertRGB1to255(data.get("interactive_params", {}).get(
                "colorbar_properties", {}).get("edge_color", self.config.interactive_colorbar_edge_color),
                                                as_integer=True, as_tuple=True),
            major_tick_line_width=data.get("interactive_params", {}).get(
                "colorbar_properties", {}).get("edge_width", self.config.interactive_colorbar_edge_width),
            minor_tick_line_color=convertRGB1to255(data.get("interactive_params", {}).get(
                "colorbar_properties", {}).get("edge_color", self.config.interactive_colorbar_edge_color),
                                                as_integer=True, as_tuple=True),
            minor_tick_line_width=data.get("interactive_params", {}).get(
                "colorbar_properties", {}).get("edge_width", self.config.interactive_colorbar_edge_width),
            major_label_text_align=data.get("interactive_params", {}).get(
                "colorbar_properties", {}).get("label_align", "left"),
            major_label_text_font_size=self._fontSizeConverter(data.get("interactive_params", {}).get(
                "colorbar_properties", {}).get("label_fontsize", self.config.interactive_colorbar_label_fontSize)),
            major_label_text_font_style=self._fontWeightConverter(data.get("interactive_params", {}).get(
                "colorbar_properties", {}).get("label_fontweight", self.config.interactive_colorbar_label_weight)),
                            )

        bokehPlot.add_layout(colorbar, user_kwargs["colorbar_properties"].get(
                "position", self.config.interactive_colorbar_location))

        if return_colorbar:
            return bokehPlot, colorbar
        else:
            return bokehPlot

    def _add_rmsd_label(self, bokehPlot, label, xpos, ypos, data={}, **kwargs):
        """
        Add RMSD label to the plot
        ===
        bokehPlot : bokeh object
            bokeh plot object
        label : str
            label to be added to the plot
        xpos : int/float
             x-axis position of the label in 'data' units
        ypos : int/float
            y-axis position of the label in 'data' units
        data : dict
            data dictionary with 'interactive_params' settings
        """
        rmsdAnnot = Label(
            x=xpos, y=ypos, x_units='data', y_units='data', render_mode='canvas',
            text=label,
            text_color=convertRGB1toHEX(data.get("interactive_params", {}).get(
                "overlay_properties", {}).get("rmsd_label_color", self.config.interactive_annotation_color)),
            background_fill_color=convertRGB1toHEX(data.get("interactive_params", {}).get(
                "overlay_properties", {}).get("rmsd_background_color", self.config.interactive_annotation_background_color)),
            text_font_size=self._fontSizeConverter(data.get("interactive_params", {}).get(
                "overlay_properties", {}).get("rmsd_label_fontsize", self.config.interactive_annotation_fontSize)),
            text_font_style=self._fontWeightConverter(data.get("interactive_params", {}).get(
                "overlay_properties", {}).get("rmsd_label_fontweight", self.config.interactive_annotation_weight)),
            background_fill_alpha=data.get("interactive_params", {}).get(
                "overlay_properties", {}).get("rmsd_background_transparency", self.config.interactive_annotation_alpha))
        bokehPlot.add_layout(rmsdAnnot)

        return bokehPlot

    def _add_grid_label(self, bokehPlot, label, xpos, ypos, **kwargs):
        titleAnnot = Label(x=xpos, y=ypos, x_units='data', y_units='data',
                          text=label, render_mode='canvas',
                          text_color=convertRGB1toHEX(self.config.interactive_grid_label_color),
                          text_font_size=self._fontSizeConverter(self.config.interactive_grid_label_size),
                          text_font_style=self._fontWeightConverter(self.config.interactive_grid_label_weight),
                          background_fill_alpha=0)
        bokehPlot.add_layout(titleAnnot)
        return bokehPlot

    def _add_plot_labels(self, bokehPlot, data, label_source, plot_type="1D"):
        user_kwargs = deepcopy(data['interactive_params'])
        
        if plot_type in ["1D"]:
            labels = LabelSet(
                x='xpos', y='ypos', text='label', level='glyph',
                x_offset=user_kwargs["annotation_properties"].get(
                    "position_offset_x", self.config.interactive_ms_annotations_offsetX),
                y_offset=user_kwargs["annotation_properties"].get(
                    "position_offset_y", self.config.interactive_ms_annotations_offsetY),
                text_align="center",
                text_font_size=self._fontSizeConverter(user_kwargs["annotation_properties"].get(
                    "label_fontsize", self.config.interactive_ms_annotations_fontSize)),
                text_font_style=self._fontWeightConverter(user_kwargs["annotation_properties"].get(
                    "label_fontweight", self.config.interactive_ms_annotations_fontWeight)),
                text_color=convertRGB1to255(user_kwargs["annotation_properties"].get(
                    "label_color", self.config.interactive_ms_annotations_label_color),
                                            as_integer=True, as_tuple=True),
                angle=user_kwargs["annotation_properties"].get(
                    "label_rotation", self.config.interactive_ms_annotations_rotation),
                angle_units="deg",
                source=label_source, render_mode='canvas')
        elif plot_type in ["waterfall", "multi-line"]:
            labels = LabelSet(
                x='xpos', y='ypos', text='label', level='glyph',
                x_offset=user_kwargs["annotation_properties"].get(
                    "position_offset_x", self.config.interactive_ms_annotations_offsetX),
                y_offset=user_kwargs["annotation_properties"].get(
                    "position_offset_y", self.config.interactive_ms_annotations_offsetY),
                text_align="center",
                text_font_size=self._fontSizeConverter(user_kwargs["annotation_properties"].get(
                    "label_fontsize", self.config.interactive_ms_annotations_fontSize)),
                text_font_style=self._fontWeightConverter(data.get("interactive_params", {}).get(
                    "annotation_properties", {}).get("label_fontweight", self.config.interactive_ms_annotations_fontWeight)),
                text_color="color", #=convertRGB1to255(data.get("annotation_properties", {}).get("label_color", self.config.interactive_ms_annotations_label_color),as_integer=True, as_tuple=True),
                angle=user_kwargs["annotation_properties"].get(
                    "label_rotation", self.config.interactive_ms_annotations_rotation),
                angle_units="deg",
                source=label_source, render_mode='canvas')
        elif plot_type in ["matrix"]:
            labels = LabelSet(
                x='xpos', y='ypos', text='label', level='glyph', text_align="center",
                x_offset=user_kwargs["overlay_properties"].get("rmsd_matrix_position_offset_x", 0),
                y_offset=user_kwargs["overlay_properties"].get("rmsd_matrix_position_offset_y", 0),
                text_font_size=self._fontSizeConverter(user_kwargs["overlay_properties"].get("rmsd_matrix_label_fontsize", self.config.interactive_ms_annotations_fontSize)),
                text_font_style=self._fontWeightConverter(user_kwargs["overlay_properties"].get("rmsd_matrix_label_fontweight", self.config.interactive_ms_annotations_fontWeight)),
                text_color="text_color",
                angle=0, angle_units="deg",
                source=label_source, render_mode='canvas')

        # add
        bokehPlot.add_layout(labels)

        return bokehPlot, labels

    def _add_plot_arrows(self, bokehPlot, data, arrow_source):
        arrows = Arrow(
            end=NormalHead(size=0), line_dash="dashed",
            x_start="xpos_start", y_start="ypos_start", x_end="xpos_end", y_end="ypos_end",
            source=arrow_source)
        bokehPlot.add_layout(arrows)

        return bokehPlot, arrows

    def onGenerateHTML(self, evt):
        """
        Generate plots for HTML output
        """
        self.currentDocumentName = self.documentName_value.GetValue()
        if self.currentDocumentName in ["None", "", None]:
            self.currentDocumentName = "ORIGAMI"

        add_width = 0
        add_watermark = self.addWatermarkCheck.GetValue()
        if self.currentPath == None:
            try:
                msg = 'Please select file name'
                dialogs.dlgBox(exceptionTitle='No file name',
                               exceptionMsg=msg,
                               type="Error")
                self.onGetSavePath(evt=None)
            except:
                msg = 'Please select a path to save the file before continuing'
                self.presenter.onThreading(None, (msg, 4), action='updateStatusbar')
                return

        tstart = time.time()
        # First, lets check how many pages are present in the selected item list
        listOfPages = []
        pageItems = self.config.pageDict.keys()
        for item in xrange(self.itemsList.GetItemCount()):
            if self.itemsList.IsChecked(index=item):
                page = self.itemsList.GetItem(item, self.config.interactiveColNames['page']).GetText()
                if page not in pageItems:
                    page = "None"
                listOfPages.append(page)

        listOfPages = list(set(listOfPages))

        # This dictionary acts as a temporary holding space for each
        # individual plot
        plotDict, widgetDict = {}, {}
        # Pre-populate the dictionary with keys
        for key in listOfPages:
            plotDict[key] = []
            widgetDict[key] = {"colorbars":[], "legends":[], "figures":[], "labels":[],
                               "lines":[], "patches":[], "original_colors":[], "cvd_colors":[],
                               "plot_width":[]}


        # Sort the list based on which page each item belongs to
        if self.config.interactive_sort_before_saving:
            self.OnSortByColumn(column=self.config.interactiveColNames['order'], sort_direction=False)

        if len(listOfPages) == 0:
            msg = 'Please select items to plot'
            dialogs.dlgBox(exceptionTitle='No plots were selected',
                           exceptionMsg=msg,
                           type="Warning")

        itemCount = self.itemsList.GetItemCount()
        data_export_list = []
        for item in xrange(itemCount):
            if self.itemsList.IsChecked(index=item):
                name = self.itemsList.GetItem(item, self.config.interactiveColNames['document']).GetText()
                key = self.itemsList.GetItem(item, self.config.interactiveColNames['type']).GetText()
                innerKey = self.itemsList.GetItem(item, self.config.interactiveColNames['file']).GetText()
                pageTable = self.itemsList.GetItem(item, self.config.interactiveColNames['page']).GetText()
                data_export_list.append([name, key, innerKey, pageTable])

        for data_export_item in data_export_list:
            name, key, innerKey, pageTable = data_export_item
            data = self.getItemData(name, key, innerKey)
            title = _replace_labels(data['title'])
            header = data['header']
            footnote = data['footnote']
            page = data['page']

            # Check that the page names agree. If they don't, the table page
            # name takes priority as it has been pre-emptively added to the
            # plotDict dictionary
            if pageTable != page['name']:
                self.presenter.onThreading(None, ('Overriding page name', 4), action='updateStatusbar')
                page = self.config.pageDict[pageTable]

            if page.get("name", False) not in pageItems:
                page = deepcopy(self.config.pageDict["None"])

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

            bokehPlot = None
            bkh_kwargs = {"title":title, "page_layout":page['layout']}
            # Now generate plot
            if key in ['MS', 'MS, multiple', 'Processed MS']:
                bkh_kwargs.update(plot_type="MS")
                data['ylabel'] = "Intensity"
                bokehPlot = self._add_plot_1D(data, **bkh_kwargs)

            elif key == "Other data":
                plot_type = data['plot_type']
                if plot_type == "scatter":
                    bokehPlot = self._add_plot_scatter(data, **bkh_kwargs)

                elif plot_type == "waterfall":
                    bkh_kwargs.update(test_x_axis=True)
                    bokehPlot = self._add_plot_waterfall(data, **bkh_kwargs)

                elif plot_type == "multi-line":
                    bokehPlot = self._add_plot_overlay_1D(data, **bkh_kwargs)

                elif plot_type == "line":
                    bkh_kwargs.update(plot_type="Other 1D")
                    bokehPlot = self._add_plot_1D(data, **bkh_kwargs)

                elif plot_type == "grid-line":
                    bokehPlot = self._add_plot_grid_NxN_1D(data, **bkh_kwargs)

                elif plot_type == "grid-scatter":
                    bokehPlot = self._add_plot_grid_NxN_scatter(data, **bkh_kwargs)

                elif plot_type == "vertical-bar":
                    bkh_kwargs.update(plot_type='V-bar')
                    bokehPlot = self._add_plot_barchart(data, **bkh_kwargs)

                elif plot_type == "horizontal-bar":
                    bkh_kwargs.update(plot_type='H-bar')
                    bokehPlot = self._add_plot_barchart(data, **bkh_kwargs)

                elif plot_type == "matrix":
                    bkh_kwargs.update(hover_label='Value')
                    bokehPlot = self._add_plot_matrix(data, **bkh_kwargs)

            elif key in ['UniDec', 'UniDec, multiple', "UniDec, processed"]:
                if key == "UniDec, multiple":
                    innerKey = re.split(' \| ', innerKey)[0]

                if innerKey == 'Processed':
                    bkh_kwargs.update(plot_type="MS")
                    data['ylabel'] = "Intensity"
                    bokehPlot = self._add_plot_1D(data, **bkh_kwargs)

                elif innerKey == 'MW distribution':
                    bkh_kwargs.update(plot_type="MS", test_x_axis=True)
                    data['ylabel'] = "Intensity"
                    bokehPlot = self._add_plot_1D(data, **bkh_kwargs)

                elif innerKey == 'Fitted':
                    bokehPlot = self._add_plot_overlay_1D(data, **bkh_kwargs)

                elif innerKey == 'MW vs Charge':
                    bkh_kwargs.update(test_x_axis=True, reshape_array=True, modify_colorbar=True)
                    bokehPlot = self._add_plot_2D(data, **bkh_kwargs)

                elif innerKey == 'm/z vs Charge':
                    bkh_kwargs.update(modify_colorbar=True)
                    bokehPlot = self._add_plot_unidec_2D(data, **bkh_kwargs)

                elif innerKey == 'Barchart':
                    data['ylabel'] = "Intensity"
                    bokehPlot = self._add_plot_unidec_barchart(data, **bkh_kwargs)

                elif innerKey == 'm/z with isolated species':
                    data['ylabel'] = 'Intensity'
                    bokehPlot = self._add_plot_unidec_1D(data, **bkh_kwargs)

            elif key in ['1D', '1D, multiple']:
                bkh_kwargs.update(plot_type="1D")
                data['ylabel'] = "Intensity"
                bokehPlot = self._add_plot_1D(data, **bkh_kwargs)


            elif key in ['RT', 'RT, multiple', 'RT, combined']:
                bkh_kwargs.update(plot_type="RT")
                data['ylabel'] = "Intensity"
                bokehPlot = self._add_plot_1D(data, **bkh_kwargs)

            elif key in ['2D', '2D, combined', '2D, processed']:
                bokehPlot = self._add_plot_2D(data, **bkh_kwargs)

            elif key == 'Overlay':
                overlayMethod = re.split('-|,|:|__', innerKey)
                if overlayMethod[0] == 'Mask' or overlayMethod[0] == 'Transparent':
                    bkh_kwargs.update(plot_type=overlayMethod[0])
                    bokehPlot = self._add_plot_overlay_2D(data, **bkh_kwargs)

                elif overlayMethod[0] == 'RMSF':
                    bkh_kwargs.update(modify_colorbar=True)
                    bokehPlot = self._add_plot_rmsf(data, **bkh_kwargs)

                elif overlayMethod[0] == 'RMSD':
                    bkh_kwargs.update(modify_colorbar=True)
                    bokehPlot = self._add_plot_rmsd(data, **bkh_kwargs)

                elif overlayMethod[0] in ['1D', 'RT']:
                    data["ylabel"] = 'Intensity'
                    bokehPlot = self._add_plot_overlay_1D(data, **bkh_kwargs)

                elif overlayMethod[0] == 'RGB':
                    bokehPlot = self._add_plot_rgb(data, **bkh_kwargs)

                elif overlayMethod[0] == 'Grid (2':
                    bokehPlot = self._add_plot_grid_2to1(data, **bkh_kwargs)

                elif overlayMethod[0] == "Grid (n x n)":
                    bokehPlot = self._add_plot_grid_NxN_2D(data, **bkh_kwargs)

                elif overlayMethod[0] in ["Waterfall (Raw)", "Waterfall (Processed)", "Waterfall (Fitted)",
                                          "Waterfall (Deconvoluted MW)", "Waterfall (Charge states)"]:
                    bkh_kwargs.update(test_x_axis=True)
                    bokehPlot = self._add_plot_waterfall(data, **bkh_kwargs)

                elif overlayMethod[0] == "Waterfall overlay":
                    bokehPlot = self._add_plot_waterfall_overlay(data, **bkh_kwargs)
                    
                else:
                    msg = "Cannot export '%s - %s (%s)' in an interactive format yet - it will be available in the future updates. For now, please deselect it in the table. LM" % (overlayMethod[0], key, innerKey)
                    dialogs.dlgBox(exceptionTitle='Not supported yet',
                                   exceptionMsg=msg,
                                   type="Error")
                    continue
            elif key == 'Statistical':
                overlayMethod = re.split('-|,|:|__', innerKey)
                if overlayMethod[0] in ['Variance', 'Mean', 'Standard Deviation']:
                    bokehPlot = self._add_plot_2D(data, **bkh_kwargs)

                elif overlayMethod[0] == 'RMSD Matrix':
                    bokehPlot = self._add_plot_matrix(data, **bkh_kwargs)
                    
            elif key == "MS/MS":
                annotated_ms_list = data.get("annotated_item_list", []) 
                if len(annotated_ms_list) == 0:
                    bokehPlot = self._add_plot_centroid_without_annotations(data, **bkh_kwargs)
                else:
                    bokehPlot = self._add_plot_centroid_with_annotations(data, **bkh_kwargs)

            else:
                msg = "Cannot export '%s (%s)' in an interactive format yet - it will be available in the future updates. For now, please deselect it in the table. LM" % (key, innerKey)
                dialogs.dlgBox(exceptionTitle='Not supported yet',
                               exceptionMsg=msg,
                               type="Error")
                continue

            if bokehPlot == None:
                print("%s - %s plot was returned empty. Skipping") % (key, innerKey)
                continue

            # check if returned width and height
            if len(bokehPlot) == 3:
                bokehPlot, width, __ = bokehPlot
                widget_kwargs = {}
            # check if returned width, height and widget information
            elif len(bokehPlot) == 4:
                bokehPlot, width, __, widget_kwargs = bokehPlot

#             Add possibility to export div/script
#             script, div = components(bokehPlot)
#             print(div)

            # plot width
            widgetDict[page['name']]['plot_width'].append(width)
            # add widget kwargs to dictionary
            if page['layout'] != 'Individual':
                # figures
                widgetDict[page['name']]["figures"].append(bokehPlot)
                # cvd specific
                widgetDict[page['name']]["lines"].append(widget_kwargs.get("lines", []))
                widgetDict[page['name']]["patches"].append(widget_kwargs.get("patches", []))
                widgetDict[page['name']]["original_colors"].append(widget_kwargs.get("original_colors", []))
                widgetDict[page['name']]["cvd_colors"].append(widget_kwargs.get("cvd_colors", []))
                # legend specific
                try: widgetDict[page['name']]["legends"].append(bokehPlot.legend[0])
                except: pass

            plot_output = [bokehPlot]
            # Generate header and footnote information
            if header != "":
                divHeader = Div(text=(header), width=width)
                markupHeader = widgetbox(divHeader, width=width)
                plot_output.insert(0, markupHeader)
            if footnote != "":
                divFootnote = Div(text=(footnote), width=width)
                markupFootnote = widgetbox(divFootnote, width=width)
                plot_output.append(markupFootnote)

            
            # Generate layout
            if page['layout'] == 'Individual':
                if add_watermark:
                    divWatermark = Div(text=str(self.config.watermark), width=width + add_width)
                    markupWatermark = widgetbox(divWatermark, width=width + add_width)
                    plot_output.append(markupWatermark)
                bokehLayout = bokeh_layout(plot_output,
                                           sizing_mode='fixed',
                                           width=width + add_width)
            else:
                bokehLayout = bokeh_layout(plot_output,
                                           sizing_mode='fixed',
                                           width=width + add_width)
            # Add to plot dictionary
            if page['layout'] == 'Individual':
                bokehTab = Panel(child=bokehLayout, title=title)
                plotDict[page['name']].append(bokehTab)
            elif page['layout'] == 'Rows':
                plotDict[page['name']].append(bokehLayout)
            elif page['layout'] == 'Columns':
                plotDict[page['name']].append(bokehLayout)
            elif page['layout'] == 'Grid':
                plotDict[page['name']].append(bokehLayout)

            print("Added {} - {} ({}) to the HTML file".format(key, innerKey, name))

        outList = []
        # Generate layout
        if self.config.interactive_sort_before_saving:
            plotDict_list = natsorted(plotDict.keys())
        else:
            plotDict_list = plotDict.keys()
        
        for pageKey in plotDict_list:
            try:
                width = np.max(widgetDict[pageKey]["plot_width"])
            except ValueError:
                return

            if add_watermark:
                divWatermark = Div(text=str(self.config.watermark), width=width + add_width)
                markupWatermark = widgetbox(divWatermark, width=width + add_width)

            # get page format
            page_format = self.config.pageDict.get(pageKey, None)
            if page_format is None:
                page_format = self.config.pageDict["None"]

            if page_format['layout'] == 'Individual':
                if len(plotDict[pageKey]) > 1:
                    for plot in range(len(plotDict[pageKey])):
                        outList.append(plotDict[pageKey][plot])
                elif len(plotDict[pageKey]) == 0:
                    msg = "The list of plots is empty. Please select supported plots and try again."
                    dialogs.dlgBox(exceptionTitle='Error',
                                   exceptionMsg=msg,
                                   type="Error")
                    return
                else:
                    outList.append(plotDict[pageKey][0])

            if page_format['layout'] == 'Rows':
                bokeh_output = [[row(plotDict[pageKey])]]
                if page_format.get("header", "") != "":
                    pageHeaderDiv = Div(text=page_format.get("header", ""), width=(width) + add_width)
                    pageHeader = widgetbox(pageHeaderDiv, width=(width) + add_width)
                    bokeh_output.insert(0, pageHeader)
                if page_format.get("footnote", "") != "":
                    pageFootnoteDiv = Div(text=page_format.get("footnote", ""), width=(width) + add_width)
                    pageFootnote = widgetbox(pageFootnoteDiv, width=(width) + add_width)
                    bokeh_output.append(pageFootnote)
                if add_watermark:
                    bokeh_output.append(markupWatermark)
                rowOutput = bokeh_layout(bokeh_output,
                                         sizing_mode='fixed',
                                         width=width + add_width)

                # add widgets
                if page_format.get("add_js_widgets", False):
                    js_type, js_code = [], {}
                    if len(widgetDict[pageKey]["legends"]) > 0:
                        js_type.extend(["legend_toggle_multi", "legend_transparency_multi"])
                        js_code.update(legends=widgetDict[pageKey]["legends"],
                                       figures=widgetDict[pageKey]["figures"])
                    if len(widgetDict[page['name']]["lines"]) > 0:
                        js_type.extend(["colorblind_safe_1D_multi"])
                        js_code.update(figures=widgetDict[pageKey]["figures"],
                                       original_colors=widgetDict[pageKey]["original_colors"],
                                       cvd_colors=widgetDict[pageKey]["cvd_colors"],
                                       lines=widgetDict[pageKey]["lines"],
                                       patches=widgetDict[pageKey]["patches"])

                    try: rowOutput = self.add_custom_js_widgets(rowOutput, js_type=js_type, data=data, **js_code)
                    except: pass

                bokehTab = Panel(child=rowOutput, title=page_format.get("title", page_format['name']))
                outList.append(bokehTab)

            if page_format['layout'] == 'Columns':
                bokeh_output = [[column(plotDict[pageKey])]]
                if page_format.get("header", "") != "":
                    pageHeaderDiv = Div(text=page_format.get("header", ""), width=(width))
                    pageHeader = widgetbox(pageHeaderDiv, width=(width))
                    bokeh_output.insert(0, pageHeader)
                if page_format.get("footnote", "") != "":
                    pageFootnoteDiv = Div(text=page_format.get("footnote", ""), width=(width))
                    pageFootnote = widgetbox(pageFootnoteDiv, width=(width))
                    bokeh_output.append(pageFootnote)
                if add_watermark:
                    bokeh_output.append(markupWatermark)
                rowOutput = bokeh_layout(bokeh_output,
                                         sizing_mode='fixed',
                                         width=width + add_width)
                bokehTab = Panel(child=rowOutput, title=page_format.get("title", page_format['name']))
                outList.append(bokehTab)

            if page_format['layout'] == 'Grid':
                columnVal = page_format.get('columns', None)
                if columnVal in [None, '']:
                    columnVal = int(sqrt(len(plotDict[pageKey])))

                rowOutput = gridplot(plotDict[pageKey],
                                     ncols=columnVal,
                                     merge_tools=page_format.get("grid_share_tools", True))
                bokeh_output = [[rowOutput]]
                if page_format.get("header", "") != "":
                    pageHeaderDiv = Div(text=page_format.get("header", ""), width=(width * columnVal))
                    pageHeader = widgetbox(pageHeaderDiv, width=(width * columnVal))
                    bokeh_output.insert(0, pageHeader)
                if page_format.get("footnote", "") != "":
                    pageFootnoteDiv = Div(text=page_format.get("footnote", ""), width=(width * columnVal))
                    pageFootnote = widgetbox(pageFootnoteDiv, width=(width * columnVal))
                    bokeh_output.append(pageFootnote)

                if add_watermark:
                    divWatermark = Div(text=str(self.config.watermark), width=(width * columnVal) + add_width)
                    markupWatermark = widgetbox(divWatermark, width=(width * columnVal) + add_width)
                    bokeh_output.append(markupWatermark)

                rowOutput = bokeh_layout(bokeh_output,
                                         sizing_mode='fixed',
                                         width=(width * columnVal) + add_width)

                # add widgets
                if page_format.get("add_js_widgets", False):
                    js_type, js_code = [], {}
                    if len(widgetDict[pageKey]["legends"]) > 0:
                        js_type.extend(["legend_toggle_multi", "legend_transparency_multi"])
                        js_code.update(legends=widgetDict[pageKey]["legends"],
                                       figures=widgetDict[pageKey]["figures"])
                    if len(widgetDict[page['name']]["lines"]) > 0:
                        js_type.extend(["colorblind_safe_1D_multi"])
                        js_code.update(figures=widgetDict[pageKey]["figures"],
                                       original_colors=widgetDict[pageKey]["original_colors"],
                                       cvd_colors=widgetDict[pageKey]["cvd_colors"],
                                       lines=widgetDict[pageKey]["lines"],
                                       patches=widgetDict[pageKey]["patches"])

                    try: rowOutput = self.add_custom_js_widgets(rowOutput, js_type=js_type, data=data, **js_code)
                    except: pass


                bokehTab = Panel(child=rowOutput, title=page_format.get("title", page_format['name']))
                outList.append(bokehTab)

        # Check how many items in the list
        if len(plotDict) >= 1:
            bokehOutput = Tabs(tabs=outList)
        else:
            return

        # Save output
        filename = self.itemPath_value.GetValue()
        self.config.interactive_add_offline_support = self.addOfflineSupportCheck.GetValue()
        try:
            if self.config.interactive_add_offline_support: _resource = INLINE
            else: _resource = None
            # save
            save(obj=bokehOutput, filename=filename, title=self.currentDocumentName, resources=_resource)
        except IOError:
            msg = 'This file already exists and is currently in usage. Try selecting a different file name or closing the file first.'
            dialogs.dlgBox(exceptionTitle='Wrong file name',
                           exceptionMsg=msg,
                           type="Error")
            return
        if self.openInBrowserCheck.GetValue():
            webbrowser.open(filename)

        print("It took {:.3f} seconds to generate interactive document. It was saved as {}".format(time.time() - tstart, filename))

    def onGetSavePath(self, evt):
        """
        Select path to save interactive plot in in
        """

        fileType = "HTML file|*.html"
        if self.config.saveInteractiveOverride:
            dlg = wx.FileDialog(self, "Save interactive document to file...", "", "", fileType,
                                wx.FD_SAVE)
        else:
            dlg = wx.FileDialog(self, "Save interactive document to file...", "", "", fileType,
                                wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if self.currentDocumentName not in ["", None, False]:
            dlg.SetFilename(self.currentDocumentName)
        else:
            dlg.SetFilename('Interactive Output')

        try: dlg.SetPath(self.currentPath)
        except: pass

        if dlg.ShowModal() == wx.ID_OK:
            self.currentPath = dlg.GetPath()
            print "You chose %s" % dlg.GetPath()
            self.itemPath_value.SetValue(dlg.GetPath())

        self.presenter.currentPath = self.currentPath

    def OnGetColumnClick(self, evt):
        column = evt.GetColumn()
        if column == self.config.interactiveColNames['check']:
            self.OnCheckAllItems(None)
            return

        self.OnSortByColumn(column=column)

    def OnSortByColumn(self, column, sort_direction=None):
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

        if sort_direction is None:
            sort_direction = self.reverse


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
            tempRow.append(self.itemsList.GetItemBackgroundColour(row))
            tempRow.append(self.itemsList.GetItemTextColour(row))
            tempData.append(tempRow)

        # Sort data
        tempData = natsorted(tempData, key=itemgetter(column), reverse=sort_direction)
        # Clear table and reinsert data
        self.itemsList.DeleteAllItems()

        checkData, bg_rgb, fg_rgb = [], [], []
        for check in tempData:
            fg_rgb.append(check[-1])
            del check[-1]
            bg_rgb.append(check[-1])
            del check[-1]
            checkData.append(check[-1])
            del check[-1]

        # Reinstate data
        rowList = np.arange(len(tempData))
        for row, check, bg_rgb, fg_color in zip(rowList, checkData, bg_rgb, fg_rgb):
            self.itemsList.Append(tempData[row])
            self.itemsList.CheckItem(row, check)
            self.itemsList.SetItemBackgroundColour(row, bg_rgb)
            self.itemsList.SetItemTextColour(row, fg_color)

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

        if filter == 'Show selected':
            for row in range(rows):
                tempRow = []
                if self.itemsList.IsChecked(index=row) and docFilter == 'All':
                    for col in range(columns):
                        item = self.itemsList.GetItem(itemId=row, col=col)
                        tempRow.append(item.GetText())
                    tempRow.append(self.itemsList.IsChecked(index=row))
                    tempRow.append(self.itemsList.GetItemBackgroundColour(row))
                    tempRow.append(self.itemsList.GetItemTextColour(row))
                    tempData.append(tempRow)
                elif self.itemsList.IsChecked(index=row) and docFilter != 'All':
                    if self.itemsList.GetItem(itemId=row, col=self.config.interactiveColNames['document']).GetText() == docFilter:
                        for col in range(columns):
                            item = self.itemsList.GetItem(itemId=row, col=col)
                            tempRow.append(item.GetText())
                        tempRow.append(self.itemsList.IsChecked(index=row))
                        tempRow.append(self.itemsList.GetItemBackgroundColour(row))
                        tempRow.append(self.itemsList.GetItemTextColour(row))
                        tempData.append(tempRow)
                else:
                    pass

            checkData, bg_rgb, fg_rgb = [], [], []
            for check in tempData:
                fg_rgb.append(check[-1])
                del check[-1]
                bg_rgb.append(check[-1])
                del check[-1]
                checkData.append(check[-1])
                del check[-1]

            # Reinstate data
            rowList = np.arange(len(tempData))
            self.itemsList.DeleteAllItems()
            for row, check, bg_rgb, fg_color in zip(rowList, checkData, bg_rgb, fg_rgb):
                self.itemsList.Append(tempData[row])
                self.itemsList.CheckItem(row, check=check)
                self.itemsList.SetItemBackgroundColour(row, bg_rgb)
                self.itemsList.SetItemTextColour(row, fg_color)

            return

        # Check if its not just selected items
        self.itemsList.DeleteAllItems()
        self.populateTable()

        # Extract information
        columns = self.itemsList.GetColumnCount()
        rows = self.itemsList.GetItemCount()
        tempData = []

        if filter == 'Show all':
            criteria = ['MS', 'Processed MS', 'RT', 'RT, multiple', '1D',
                        '1D, multiple', '2D', '2D, processed', 'DT-IMS',
                        'RT, combined', '2D, combined', 'Overlay', 'Statistical',
                        'MS, multiple', 'UniDec', 'UniDec, multiple', 'Other data']
        elif filter == 'Show MS (all)':
            criteria = ['MS', 'MS, multiple', 'Processed MS']
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
        elif filter == 'Show Other data':
            criteria = ['Other data']

        # Iterate over row and columns to get data
        for row in range(rows):
            tempRow = []
            itemType = self.itemsList.GetItem(itemId=row, col=self.config.interactiveColNames['type']).GetText()
            if itemType in criteria and docFilter == 'All':
                for col in range(columns):
                    item = self.itemsList.GetItem(itemId=row, col=col)
                    tempRow.append(item.GetText())
                tempRow.append(self.itemsList.IsChecked(index=row))
                tempRow.append(self.itemsList.GetItemBackgroundColour(row))
                tempRow.append(self.itemsList.GetItemTextColour(row))
                tempData.append(tempRow)
            elif itemType in criteria and docFilter != 'All':
                if self.itemsList.GetItem(itemId=row,
                                          col=self.config.interactiveColNames['document']).GetText() == docFilter:
                    for col in range(columns):
                        item = self.itemsList.GetItem(itemId=row, col=col)
                        tempRow.append(item.GetText())
                    tempRow.append(self.itemsList.IsChecked(index=row))
                    tempRow.append(self.itemsList.GetItemBackgroundColour(row))
                    tempRow.append(self.itemsList.GetItemTextColour(row))
                    tempData.append(tempRow)

        checkData, bg_rgb, fg_rgb = [], [], []
        for check in tempData:
            fg_rgb.append(check[-1])
            del check[-1]
            bg_rgb.append(check[-1])
            del check[-1]
            checkData.append(check[-1])
            del check[-1]

        # Clear table and reinsert data
        self.itemsList.DeleteAllItems()
        # Reinstate data
        rowList = np.arange(len(tempData))
        for row, check, bg_rgb, fg_color in zip(rowList, checkData, bg_rgb, fg_rgb):
            self.itemsList.Append(tempData[row])
            self.itemsList.CheckItem(row, check)
            self.itemsList.SetItemBackgroundColour(row, bg_rgb)
            self.itemsList.SetItemTextColour(row, fg_color)

        self.allChecked = False

    def OnCheckSelectedItems(self, evt):
        evtID = evt.GetId()

        if evtID == ID_interactivePanel_check_ms:
            criteria = ['MS', 'MS, multiple', 'Processed MS']
        elif evtID == ID_interactivePanel_check_rt:
            criteria = ['RT', 'RT, multiple']
        elif evtID == ID_interactivePanel_check_dt1D:
            criteria = ['1D', '1D, multiple']
        elif evtID == ID_interactivePanel_check_dt2D:
            criteria = ['2D', '2D, processed', '2D, combined']
        elif evtID == ID_interactivePanel_check_overlay:
            criteria = ['Overlay']
        elif evtID == ID_interactivePanel_check_unidec:
             criteria = ['UniDec', 'UniDec, multiple', 'UniDec, processed']
        elif evtID == ID_interactivePanel_check_other:
            criteria = ['Other data']


        rows = self.itemsList.GetItemCount()

        # first uncheck all
        for row in range(rows):
            self.itemsList.CheckItem(row, check=False)

        if rows > 0:
            for row in range(rows):
                row_type = self.itemsList.GetItem(row, self.config.interactiveColNames['type']).GetText()
                if row_type in criteria:
                    self.itemsList.CheckItem(row, check=True)

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
            self.allChecked = not self.allChecked
            check = self.allChecked

        for row in xrange(rows):
            self.itemsList.CheckItem(row, check=check)

    def onCheckItem(self, evt):
        item_state = not self.itemsList.IsChecked(self.currentItem)
        self.itemsList.CheckItem(self.currentItem, check=item_state)

    def _getItemDetails(self, itemID=None):
        """ Return document name, item type and its subtype"""
        if itemID is None:
            itemID = self.currentItem

        name = self.itemsList.GetItem(itemID, self.config.interactiveColNames['document']).GetText()
        key = self.itemsList.GetItem(itemID, self.config.interactiveColNames['type']).GetText()
        innerKey = self.itemsList.GetItem(itemID, self.config.interactiveColNames['file']).GetText()

        return name, key, innerKey

    def _check_limits(self, old_limits, new_limits):
        """
        Check extent lists to ensure values are not bonkers
        """
        if new_limits is not None:
            if new_limits[0] in [None, "None", ""] or new_limits[0] >= old_limits[1]:
                new_limits[0] = old_limits[0]
            if new_limits[1] in [None, "None", ""] or new_limits[1] <= old_limits[0]:
                new_limits[1] = old_limits[1]
            old_limits = new_limits

        return old_limits

    def _check_tools(self, hoverTool, data):

        if len(data['interactive_params']['tools'].get("on_tools", "")) > 0:
            TOOLS = data['interactive_params']['tools'].get("on_tools", "")
            if "hover" in TOOLS: TOOLS = [hoverTool, TOOLS.replace("hover", "")]
        else:
            if hoverTool is not None:
                TOOLS = [hoverTool, self.tools_all]
            else:
                TOOLS = self.tools_all

        return TOOLS

    def _fontSizeConverter(self, value):
        return "%spt" % value

    def _fontWeightConverter(self, value):
        if value: return "bold"
        else: return "normal"

    def _preAnnotateItems(self, itemID=None):
        if itemID != None:
            self.currentItem = itemID

        color = self.itemsList.GetItem(self.currentItem, self.config.interactiveColNames['color']).GetText()
        if color != "" and "(" not in color and "[" not in color and color in self.config.cmaps2:
            self.comboCmapSelect.SetStringSelection(color)

        title = self.itemsList.GetItem(self.currentItem, self.config.interactiveColNames['title']).GetText()
        self.itemName_value.SetValue(title)

        orderNum = self.itemsList.GetItem(self.currentItem, self.config.interactiveColNames['order']).GetText()
        self.order_value.SetValue(orderNum)

    def _kda_test(self, xvals):
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

    def _prepareToolsForPlot(self, tools):
        # Find one which (if any) wheel too is selected

        toolList = []
        wheelDict = {'Wheel Zoom XY':'wheel_zoom',
                     'Wheel Zoom X':'xwheel_zoom',
                     'Wheel Zoom Y':'ywheel_zoom'}
        if tools['activeWheel'] not in ["None", "auto"]:
            wheelTool = wheelDict[tools['activeWheel']]
            toolList.append(wheelTool)

        listToGetState = {'save':tools['save'],
                          'pan': tools['pan'],
                          'box_zoom':tools['boxzoom'],
                          'xbox_zoom':tools['boxzoom_horizontal'],
                          'ybox_zoom':tools['boxzoom_vertical'],
                          'crosshair':tools['crosshair'],
                          'reset':tools['reset']}
        # Iterate over the list to get their state
        for item in listToGetState:
            itemState = listToGetState[item]
            if itemState:
                toolList.append(item)

        activeDragTools = {'Box Zoom':'box_zoom', 'Pan':'pan', 'Pan X':'xpan', 'Pan Y':'ypan',
                           'Box Zoom X':'xbox_zoom', 'Box Zoom Y':'ybox_zoom',
                           'auto':'auto', 'None':None}

        activeWheelTools = {'Wheel Zoom XY':'wheel_zoom',
                            'Wheel Zoom X':'xwheel_zoom',
                            'Wheel Zoom Y':'ywheel_zoom',
                            'auto':'auto', 'None':None}

        activeHoverTools = {'Hover':'hover',
                            'Crosshair':'crosshair',
                            'auto':'auto', 'None':None}


        # Match those values to dictionary
        self.activeDrag = activeDragTools[tools['activeDrag']]
        self.activeWheel = activeWheelTools[tools['activeWheel']]
        self.activeInspect = activeHoverTools[tools['activeInspect']]

        # Check that those tools were selected. If they are not in the list, it
        # will throw an error
        for active in [self.activeDrag, self.activeWheel, self.activeInspect]:
            if active == None or active == 'auto' or active == 'hover': continue
            else:
                if not active in toolList:
                    toolList.append(active)

        # Set the tools
        tools_out = ','.join(toolList)
        return tools_out

    def _updateTable(self):
        title = self.itemsList.GetItem(self.currentItem, self.config.interactiveColNames['title']).GetText()
#         header = self.itemsList.GetItem(self.currentItem,self.config.interactiveColNames['header']).GetText()
#         footnote = self.itemsList.GetItem(self.currentItem,self.config.interactiveColNames['footnote']).GetText()
        order = self.itemsList.GetItem(self.currentItem, self.config.interactiveColNames['order']).GetText()

        self.itemName_value.SetValue(title)
#         self.itemHeader_value.SetValue(header)
#         self.itemFootnote_value.SetValue(footnote)
        self.order_value.SetValue(order)

        self.onAnnotateItems(None, itemID=self.currentItem)

    def _convert_color_list(self, colorList):
        hexcolorlist = []
        for _color in colorList:
            hexcolorlist.append(convertRGB1toHEX(_color))
        colorList = hexcolorlist

        return colorList

    def _get_colors(self, n_colors, return_as_hex=True):
        if self.config.currentPalette not in ['Spectral', 'RdPu']:
            palette = self.config.currentPalette.lower()
        else:
            palette = self.config.currentPalette
        colorlist = color_palette(palette, n_colors)

        if return_as_hex:
            hexcolorlist = []
            for _color in colorlist:
                hexcolorlist.append(convertRGB1toHEX(_color))
            colorlist = hexcolorlist

        return colorlist

    def _convert_cmap_to_colormapper(self, cmap=None, zmin=None, zmax=None, zvals=None, palette=None,
                                     return_palette=False):
        if zmin is None or zmax is None and zvals is not None:
            zmin, zmax = np.round(np.min(zvals), 2), np.round(np.max(zvals), 2)

        if palette is None:
            _colormap = cm.get_cmap(cmap)
            _palette = [colors.rgb2hex(m) for m in _colormap(np.arange(_colormap.N))]
        else:
            _palette = palette

        _color_mapper = LinearColorMapper(palette=_palette, low=zmin, high=zmax)
        if return_palette:
            return _color_mapper, _palette
        else:
            return _color_mapper

    def _preset_interactive_parameters(self, data):
        """
        Add all necessary interactive parameters to the item
        ===
        data : dict
            dictionary object will all data
        """
        data = self._preset_interactive_parameters_widgets(data)
        data = self._preset_interactive_parameters_tools(data)
        data = self._preset_interactive_parameters_colorbar(data)
        data = self._preset_interactive_parameters_legend(data)
        data = self._preset_interactive_parameters_preprocess(data)
        data = self._preset_interactive_parameters_plots(data)
        data = self._preset_interactive_parameters_overlay(data)
        data = self._preset_interactive_parameters_general(data)
        data = self._preset_interactive_parameters_annotation(data)

        return data

    def _preset_interactive_parameters_widgets(self, data):
        """
        Add widget parameters to the item
        ===
        data : dict
            dictionary object will all data
        """
        if "widgets" not in data['interactive_params']:
            data['interactive_params']["widgets"] = {}
            
        if "add_custom_widgets" not in data['interactive_params']['widgets']:
            data['interactive_params']['widgets']['add_custom_widgets'] = False
        if "label_toggle" not in data['interactive_params']['widgets']:
            data['interactive_params']['widgets']['label_toggle'] = False
        if "label_size_slider" not in data['interactive_params']['widgets']:
            data['interactive_params']['widgets']['label_size_slider'] = False
        if "label_rotation" not in data['interactive_params']['widgets']:
            data['interactive_params']['widgets']['label_rotation'] = False
        if "label_offset_x" not in data['interactive_params']['widgets']:
            data['interactive_params']['widgets']['label_offset_x'] = False
        if "label_offset_y" not in data['interactive_params']['widgets']:
            data['interactive_params']['widgets']['label_offset_y'] = False
        if "slider_zoom" not in data['interactive_params']['widgets']:
            data['interactive_params']['widgets']['slider_zoom'] = False
        if "hover_mode" not in data['interactive_params']['widgets']:
            data['interactive_params']['widgets']['hover_mode'] = False
        if "colorblind_safe_1D" not in data['interactive_params']['widgets']:
            data['interactive_params']['widgets']['colorblind_safe_1D'] = False
        if "colorblind_safe_2D" not in data['interactive_params']['widgets']:
            data['interactive_params']['widgets']['colorblind_safe_2D'] = False
        if "colorblind_safe_scatter" not in data['interactive_params']['widgets']:
            data['interactive_params']['widgets']['colorblind_safe_scatter'] = False
        if "colormap_change" not in data['interactive_params']['widgets']:
            data['interactive_params']['widgets']['colormap_change'] = False
        if "legend_toggle" not in data['interactive_params']['widgets']:
            data['interactive_params']['widgets']['legend_toggle'] = False
        if "legend_position" not in data['interactive_params']['widgets']:
            data['interactive_params']['widgets']['legend_position'] = False
        if "legend_orientation" not in data['interactive_params']['widgets']:
            data['interactive_params']['widgets']['legend_orientation'] = False
        if "legend_transparency" not in data['interactive_params']['widgets']:
            data['interactive_params']['widgets']['legend_transparency'] = False
        if "scatter_size" not in data['interactive_params']['widgets']:
            data['interactive_params']['widgets']['scatter_size'] = False
        if "scatter_transparency" not in data['interactive_params']['widgets']:
            data['interactive_params']['widgets']['scatter_transparency'] = False
        if "processing_normalization" not in data['interactive_params']['widgets']:
            data['interactive_params']['widgets']['processing_normalization'] = False

        return data

    def _preset_interactive_parameters_tools(self, data):
        """
        Add tools parameters to the item
        ===
        data : dict
            dictionary object will all data
        """
        
        _active_replace_ = {
            'Box zoom (both)':"box_zoom", 'Box zoom (horizontal)':"xbox_zoom",
            'Box zoom (vertical)':"ybox_zoom", 'Pan (both)':"pan", 'Pan (horizontal)':"xpan",
            'Wheel zoom (both)':"wheel_zoom", 'Wheel zoom (horizontal)':"xwheel_zoom",
            'Wheel zoom (vertical)':"ywheel_zoom", 'Pan (vertical)':"ypan", 'auto':"auto", 'None':None,
            'Hover':'hover', 'Crosshair':'crosshair'}
        
        if "tools" not in data['interactive_params']:
            data['interactive_params']["tools"] = {}
        
        if "position" not in data['interactive_params']['tools']:
            data['interactive_params']['tools']['position'] = "right"
        if "hover" not in data['interactive_params']['tools']:
            data['interactive_params']['tools']['hover'] = True
        if "pan" not in data['interactive_params']['tools']:
            data['interactive_params']['tools']['pan'] = True
        if "xpan" not in data['interactive_params']['tools']:
            data['interactive_params']['tools']['xpan'] = False
        if "ypan" not in data['interactive_params']['tools']:
            data['interactive_params']['tools']['ypan'] = False
        if "box_zoom" not in data['interactive_params']['tools']:
            data['interactive_params']['tools']['box_zoom'] = True
        if "xbox_zoom" not in data['interactive_params']['tools']:
            data['interactive_params']['tools']['xbox_zoom'] = False
        if "ybox_zoom" not in data['interactive_params']['tools']:
            data['interactive_params']['tools']['ybox_zoom'] = False
        if "save" not in data['interactive_params']['tools']:
            data['interactive_params']['tools']['save'] = True
        if "crosshair" not in data['interactive_params']['tools']:
            data['interactive_params']['tools']['crosshair'] = True
        if "reset" not in data['interactive_params']['tools']:
            data['interactive_params']['tools']['reset'] = True
        if "wheel" not in data['interactive_params']['tools']:
            data['interactive_params']['tools']['wheel'] = True
        if "wheel_type" not in data['interactive_params']['tools']:
            data['interactive_params']['tools']['wheel_type'] = "wheel zoom (both)"
        if "wheel_zoom" not in data['interactive_params']['tools']:
            data['interactive_params']['tools']['wheel_zoom'] = True
        if "xwheel_zoom" not in data['interactive_params']['tools']:
            data['interactive_params']['tools']['xwheel_zoom'] = False
        if "ywheel_zoom" not in data['interactive_params']['tools']:
            data['interactive_params']['tools']['ywheel_zoom'] = False

        if "active_drag_type" not in data['interactive_params']['tools']:
            data['interactive_params']['tools']['active_drag_type'] = "Box zoom (both)"
            data['interactive_params']['tools']['active_drag'] = _active_replace_[data['interactive_params']['tools']['active_drag_type']]
        if "active_inspect_type" not in data['interactive_params']['tools']:
            data['interactive_params']['tools']['active_inspect_type'] = "Hover"
            data['interactive_params']['tools']['active_inspect'] = _active_replace_[data['interactive_params']['tools']['active_inspect_type']]
        if "active_wheel_type" not in data['interactive_params']['tools']:
            data['interactive_params']['tools']['active_wheel_type'] = "None"
            data['interactive_params']['tools']['active_wheel'] = _active_replace_[data['interactive_params']['tools']['active_wheel_type']]

        # create string representation of tools
        on_tools = []
        for key in data['interactive_params']['tools']:
            if key in ["on_tools", "wheel", "wheel_type", "position", "active_drag_type",
                       "active_inspect_type", "active_wheel_type"]:
                continue
            elif key in ["active_drag","active_inspect", "active_wheel"]:
                active_value = data['interactive_params']['tools'][key]
                if active_value not in ["auto", "None", None]:
                    on_tools.append(active_value)
            elif data['interactive_params']['tools'][key]:
                on_tools.append(key)

        return data

    def _preset_interactive_parameters_colorbar(self, data):
        """
        Add widget parameters to the item
        ===
        data : dict
            dictionary object will all data
        """
        if "colorbar_properties" not in data['interactive_params']:
            data['interactive_params']["colorbar_properties"] = {}

        if "colorbar" not in data['interactive_params']['colorbar_properties']:
            data['interactive_params']['colorbar_properties']['colorbar'] = self.config.interactive_colorbar
        if "precision" not in data['interactive_params']['colorbar_properties']:
            data['interactive_params']['colorbar_properties']['precision'] = self.config.interactive_colorbar_precision
        if "use_scientific" not in data['interactive_params']['colorbar_properties']:
            data['interactive_params']['colorbar_properties']['use_scientific'] = self.config.interactive_colorbar_useScientific
        if "label_offset" not in data['interactive_params']['colorbar_properties']:
            data['interactive_params']['colorbar_properties']['label_offset'] = self.config.interactive_colorbar_label_offset
        if "position" not in data['interactive_params']['colorbar_properties']:
            data['interactive_params']['colorbar_properties']['position'] = self.config.interactive_colorbar_location
        if "position_offset_x" not in data['interactive_params']['colorbar_properties']:
            data['interactive_params']['colorbar_properties']['position_offset_x'] = self.config.interactive_colorbar_offset_x
        if "position_offset_y" not in data['interactive_params']['colorbar_properties']:
            data['interactive_params']['colorbar_properties']['position_offset_y'] = self.config.interactive_colorbar_offset_y
        if "pad" not in data['interactive_params']['colorbar_properties']:
            data['interactive_params']['colorbar_properties']['pad'] = self.config.interactive_colorbar_padding
        if "width" not in data['interactive_params']['colorbar_properties']:
            data['interactive_params']['colorbar_properties']['width'] = self.config.interactive_colorbar_width
        if "edge_width" not in data['interactive_params']['colorbar_properties']:
            data['interactive_params']['colorbar_properties']['edge_width'] = self.config.interactive_colorbar_edge_width
        if "modify_ticks" not in data['interactive_params']['colorbar_properties']:
            data['interactive_params']['colorbar_properties']['modify_ticks'] = self.config.interactive_colorbar_modify_ticks
        if "label_fontsize" not in data['interactive_params']['colorbar_properties']:
            data['interactive_params']['colorbar_properties']['label_fontsize'] = self.config.interactive_colorbar_label_fontSize
        if "label_fontweight" not in data['interactive_params']['colorbar_properties']:
            data['interactive_params']['colorbar_properties']['label_fontweight'] = self.config.interactive_colorbar_label_weight
        if "edge_color" not in data['interactive_params']['colorbar_properties']:
            data['interactive_params']['colorbar_properties']['edge_color'] = self.config.interactive_colorbar_edge_color

        if data['interactive_params']['colorbar_properties']['position'] in ('right', 'left'):
            data['interactive_params']['colorbar_properties']['orientation'] = 'vertical'
            data['interactive_params']['colorbar_properties']['height'] = "auto"
            data['interactive_params']['colorbar_properties']['label_align'] = "left"
        else:
            data['interactive_params']['colorbar_properties']['orientation'] = 'horizontal'
            data['interactive_params']['colorbar_properties']['height'] = self.config.interactive_colorbar_width
            data['interactive_params']['colorbar_properties']['width'] = "auto"
            data['interactive_params']['colorbar_properties']['label_align'] = "center"

        return data

    def _preset_interactive_parameters_legend(self, data):
        """
        Add widget parameters to the item
        ===
        data : dict
            dictionary object will all data
        """
        if "legend_properties" not in data['interactive_params']:
            data['interactive_params']["legend_properties"] = {}

        if "legend" not in data['interactive_params']['legend_properties']:
            data['interactive_params']['legend_properties']['legend'] = self.config.interactive_legend
        if "legend_location" not in data['interactive_params']['legend_properties']:
            data['interactive_params']['legend_properties']['legend_location'] = self.config.interactive_legend_location
        if "legend_click_policy" not in data['interactive_params']['legend_properties']:
            data['interactive_params']['legend_properties']['legend_click_policy'] = self.config.interactive_legend_click_policy
        if "legend_orientation" not in data['interactive_params']['legend_properties']:
            data['interactive_params']['legend_properties']['legend_orientation'] = self.config.interactive_legend_orientation
        if "legend_font_size" not in data['interactive_params']['legend_properties']:
            data['interactive_params']['legend_properties']['legend_font_size'] = self.config.interactive_legend_font_size
        if "legend_background_alpha" not in data['interactive_params']['legend_properties']:
            data['interactive_params']['legend_properties']['legend_background_alpha'] = self.config.interactive_legend_background_alpha
        if "legend_mute_alpha" not in data['interactive_params']['legend_properties']:
            data['interactive_params']['legend_properties']['legend_mute_alpha'] = self.config.interactive_legend_mute_alpha

        return data

    def _preset_interactive_parameters_preprocess(self, data):
        """
        Add widget parameters to the item
        ===
        data : dict
            dictionary object will all data
        """
        if "preprocessing_properties" not in data['interactive_params']:
            data['interactive_params']["preprocessing_properties"] = {}

        if "linearize" not in data['interactive_params']['preprocessing_properties']:
            data['interactive_params']['preprocessing_properties']['linearize'] = self.config.interactive_ms_linearize
        if "linearize_binsize" not in data['interactive_params']['preprocessing_properties']:
            data['interactive_params']['preprocessing_properties']['linearize_binsize'] = self.config.interactive_ms_binSize
        if "linearize_limit" not in data['interactive_params']['preprocessing_properties']:
            data['interactive_params']['preprocessing_properties']['linearize_limit'] = 25000

        if "subsample" not in data['interactive_params']['preprocessing_properties']:
            data['interactive_params']['preprocessing_properties']['subsample'] = True
        if "subsample_frequency" not in data['interactive_params']['preprocessing_properties']:
            data['interactive_params']['preprocessing_properties']['subsample_frequency'] = 20
        if "subsample_limit" not in data['interactive_params']['preprocessing_properties']:
            data['interactive_params']['preprocessing_properties']['subsample_limit'] = 20000

        return data

    def _preset_interactive_parameters_plots(self, data):
        """
        Add widget parameters to the item
        ===
        data : dict
            dictionary object will all data
        """
        if "plot_properties" not in data['interactive_params']:
            data['interactive_params']["plot_properties"] = {}

        # line plots
        if "line_width" not in data['interactive_params']['plot_properties']:
            data['interactive_params']['plot_properties']['line_width'] = self.config.interactive_line_width
        if "line_transparency" not in data['interactive_params']['plot_properties']:
            data['interactive_params']['plot_properties']['line_transparency'] = self.config.interactive_line_alpha
        if "line_style" not in data['interactive_params']['plot_properties']:
            data['interactive_params']['plot_properties']['line_style'] = self.config.interactive_line_style
        if "line_shade_under" not in data['interactive_params']['plot_properties']:
            data['interactive_params']['plot_properties']['line_shade_under'] = self.config.interactive_line_shade_under
        if "shade_transparency" not in data['interactive_params']['plot_properties']:
            data['interactive_params']['plot_properties']['shade_transparency'] = self.config.interactive_line_shade_alpha
        if "line_color" not in data['interactive_params']['plot_properties']:
            color = data.get('cmap', self.config.interactive_line_color)
            if isinstance(color, (str, unicode)): color = self.config.interactive_line_color
            data['interactive_params']['plot_properties']['line_color'] = color
        if "hover_link_x" not in data['interactive_params']['plot_properties']:
            data['interactive_params']['plot_properties']['hover_link_x'] = self.config.linkXYaxes

            if data['interactive_params']['plot_properties']['hover_link_x']:
                data['interactive_params']['plot_properties']['hover_mode'] = 'vline'
            else:
                data['interactive_params']['plot_properties']['hover_mode'] = 'mouse'

        # waterfall plots
        if "waterfall_increment" not in data['interactive_params']['plot_properties']:
            data['interactive_params']['plot_properties']['waterfall_increment'] = self.config.interactive_waterfall_increment
        if "waterfall_shade_under" not in data['interactive_params']['plot_properties']:
            data['interactive_params']['plot_properties']['waterfall_shade_under'] = self.config.interactive_waterfall_shade_under
        if "waterfall_shade_transparency" not in data['interactive_params']['plot_properties']:
            data['interactive_params']['plot_properties']['waterfall_shade_transparency'] = self.config.interactive_waterfall_shade_alpha

        # heatmaps
        if "colormap" not in data['interactive_params']['plot_properties']:
            color = data.get('cmap', self.config.currentCmap)
            if not isinstance(color, (str, unicode)): color = self.config.currentCmap
            data['interactive_params']['plot_properties']['colormap'] = color
            
        # bar
        if "bar_width" not in data['interactive_params']['plot_properties']:
            data['interactive_params']['plot_properties']['bar_width'] = self.config.interactive_bar_width
        if "bar_transparency" not in data['interactive_params']['plot_properties']:
            data['interactive_params']['plot_properties']['bar_transparency'] = self.config.interactive_bar_alpha
        if "bar_line_width" not in data['interactive_params']['plot_properties']:
            data['interactive_params']['plot_properties']['bar_line_width'] = self.config.interactive_bar_lineWidth
        if "bar_edge_color_sameAsFill" not in data['interactive_params']['plot_properties']:
            data['interactive_params']['plot_properties']['bar_edge_color_sameAsFill'] = self.config.interactive_bar_sameAsFill
        if "bar_edge_color" not in data['interactive_params']['plot_properties']:
            data['interactive_params']['plot_properties']['bar_edge_color'] = self.config.interactive_bar_edge_color
            
        # scatter
        if "scatter_shape" not in data['interactive_params']['plot_properties']:
            data['interactive_params']['plot_properties']['scatter_shape'] = self.config.interactive_scatter_marker
        if "scatter_size" not in data['interactive_params']['plot_properties']:
            data['interactive_params']['plot_properties']['scatter_size'] = self.config.interactive_scatter_size
        if "scatter_transparency" not in data['interactive_params']['plot_properties']:
            data['interactive_params']['plot_properties']['scatter_transparency'] = self.config.interactive_scatter_alpha
        if "scatter_line_width" not in data['interactive_params']['plot_properties']:
            data['interactive_params']['plot_properties']['scatter_line_width'] = self.config.interactive_scatter_lineWidth
        if "scatter_edge_color_sameAsFill" not in data['interactive_params']['plot_properties']:
            data['interactive_params']['plot_properties']['scatter_edge_color_sameAsFill'] = self.config.interactive_scatter_sameAsFill
        if "scatter_edge_color" not in data['interactive_params']['plot_properties']:
            data['interactive_params']['plot_properties']['scatter_edge_color'] = self.config.interactive_scatter_edge_color

        # tandem
        if "tandem_line_width" not in data['interactive_params']['plot_properties']:
            data['interactive_params']['plot_properties']['tandem_line_width'] = 1.
        if "tandem_line_color_unlabelled" not in data['interactive_params']['plot_properties']:
            data['interactive_params']['plot_properties']['tandem_line_color_unlabelled'] = (1., 1., 1.)
        if "tandem_line_color_labelled" not in data['interactive_params']['plot_properties']:
            data['interactive_params']['plot_properties']['tandem_line_color_labelled'] = (1., 0., 0.)

        return data

    def _preset_interactive_parameters_overlay(self, data):
        """
        Add widget parameters to the item
        ===
        data : dict
            dictionary object will all data
        """
        if "overlay_properties" not in data['interactive_params']:
            data['interactive_params']["overlay_properties"] = {}

        # rmds
        if "rmsd_label_fontsize" not in data['interactive_params']['overlay_properties']:
            data['interactive_params']['overlay_properties']['rmsd_label_fontsize'] = self.config.interactive_annotation_fontSize
        if "rmsd_label_fontweight" not in data['interactive_params']['overlay_properties']:
            data['interactive_params']['overlay_properties']['rmsd_label_fontweight'] = self.config.interactive_annotation_weight
        if "rmsd_background_transparency" not in data['interactive_params']['overlay_properties']:
            data['interactive_params']['overlay_properties']['rmsd_background_transparency'] = self.config.interactive_annotation_alpha
        if "rmsd_label_color" not in data['interactive_params']['overlay_properties']:
            data['interactive_params']['overlay_properties']['rmsd_label_color'] = self.config.interactive_annotation_color
        if "rmsd_background_color" not in data['interactive_params']['overlay_properties']:
            data['interactive_params']['overlay_properties']['rmsd_background_color'] = self.config.interactive_annotation_background_color

        # rmsd matrix
        if "rmsd_matrix_position_offset_x" not in data['interactive_params']['overlay_properties']:
            data['interactive_params']['overlay_properties']['rmsd_matrix_position_offset_x'] = self.config.interactive_ms_annotations_offsetX
        if "rmsd_matrix_position_offset_y" not in data['interactive_params']['overlay_properties']:
            data['interactive_params']['overlay_properties']['rmsd_matrix_position_offset_y'] = self.config.interactive_ms_annotations_offsetY
        if "rmsd_matrix_label_fontsize" not in data['interactive_params']['overlay_properties']:
            data['interactive_params']['overlay_properties']['rmsd_matrix_label_fontsize'] = self.config.interactive_ms_annotations_fontSize
        if "rmsd_matrix_label_fontweight" not in data['interactive_params']['overlay_properties']:
            data['interactive_params']['overlay_properties']['rmsd_matrix_label_fontweight'] = self.config.interactive_ms_annotations_fontWeight
        if "rmsd_matrix_xaxis_rotation" not in data['interactive_params']['overlay_properties']:
            data['interactive_params']['overlay_properties']['rmsd_matrix_xaxis_rotation'] = 120
        if "rmsd_matrix_label_color" not in data['interactive_params']['overlay_properties']:
            data['interactive_params']['overlay_properties']['rmsd_matrix_label_color'] = self.config.interactive_ms_annotations_label_color
        if "rmsd_matrix_colormap" not in data['interactive_params']['overlay_properties']:
            color = data.get('cmap', "coolwarm")
            if not isinstance(color, (str, unicode)): color = "coolwarm"
            data['interactive_params']['overlay_properties']['rmsd_matrix_colormap'] = color
        if "rmsd_matrix_auto_label_color" not in data['interactive_params']['overlay_properties']:
            data['interactive_params']['overlay_properties']['rmsd_matrix_auto_label_color'] = True
            
        # multi-line
        if "multiline_shade_under" not in data['interactive_params']['overlay_properties']:
            data['interactive_params']['overlay_properties']['multiline_shade_under'] = False
        if "multiline_shade_transparency" not in data['interactive_params']['overlay_properties']:
            data['interactive_params']['overlay_properties']['multiline_shade_transparency'] = 0.25

        # mask/transparency
        if "overlay_link_xy" not in data['interactive_params']['overlay_properties']:
            data['interactive_params']['overlay_properties']['overlay_link_xy'] = self.config.linkXYaxes
        if "overlay_layout" not in data['interactive_params']['overlay_properties']:
            data['interactive_params']['overlay_properties']['overlay_layout'] = self.config.plotLayoutOverlay
        if "overlay_colormap_1" not in data['interactive_params']['overlay_properties']:
            data['interactive_params']['overlay_properties']['overlay_colormap_1'] = data.get('cmap1', "Reds")
        if "overlay_colormap_2" not in data['interactive_params']['overlay_properties']:
            data['interactive_params']['overlay_properties']['overlay_colormap_2'] = data.get('cmap2', "Blues")
        if "overlay_merge_tools" not in data['interactive_params']['overlay_properties']:
            data['interactive_params']['overlay_properties']['overlay_merge_tools'] = False

        # grid (nxn)
        if "overlay_grid_add_labels" not in data['interactive_params']['overlay_properties']:
            data['interactive_params']['overlay_properties']['overlay_grid_add_labels'] = False
        if "grid_label_fontsize" not in data['interactive_params']['overlay_properties']:
            data['interactive_params']['overlay_properties']['grid_label_fontsize'] = self.config.interactive_grid_label_size
        if "grid_label_fontweight" not in data['interactive_params']['overlay_properties']:
            data['interactive_params']['overlay_properties']['grid_label_fontweight'] = self.config.interactive_grid_label_weight
        if "grid_position_offset_x" not in data['interactive_params']['overlay_properties']:
            data['interactive_params']['overlay_properties']['grid_position_offset_x'] = self.config.interactive_ms_annotations_offsetX
        if "grid_position_offset_y" not in data['interactive_params']['overlay_properties']:
            data['interactive_params']['overlay_properties']['grid_position_offset_y'] = self.config.interactive_ms_annotations_offsetY
        if "grid_label_color" not in data['interactive_params']['overlay_properties']:
            data['interactive_params']['overlay_properties']['grid_label_color'] = self.config.interactive_annotation_color
            
        # rmsf
        if "rmsf_line_width" not in data['interactive_params']['overlay_properties']:
            data['interactive_params']['overlay_properties']['rmsf_line_width'] = self.config.interactive_line_width
        if "rmsf_line_transparency" not in data['interactive_params']['overlay_properties']:
            data['interactive_params']['overlay_properties']['rmsf_line_transparency'] = self.config.interactive_line_alpha
        if "rmsf_line_style" not in data['interactive_params']['overlay_properties']:
            data['interactive_params']['overlay_properties']['rmsf_line_style'] = self.config.interactive_line_style
        if "rmsf_line_shade_under" not in data['interactive_params']['overlay_properties']:
            data['interactive_params']['overlay_properties']['rmsf_line_shade_under'] = False
        if "rmsf_shade_transparency" not in data['interactive_params']['overlay_properties']:
            data['interactive_params']['overlay_properties']['rmsf_shade_transparency'] = self.config.interactive_line_alpha
        if "rmsf_line_color" not in data['interactive_params']['overlay_properties']:
            data['interactive_params']['overlay_properties']['rmsf_line_color'] = data.get("colorRMSF", (0.,0.,0.))

        return data

    def _preset_interactive_parameters_general(self, data):
        """
        Add widget parameters to the item
        ===
        data : dict
            dictionary object will all data
        """

        # plot parameters
        if "xlimits" not in data['interactive_params']:
            data['interactive_params']['xlimits'] = None
        if "ylimits" not in data['interactive_params']:
            data['interactive_params']['ylimits'] = None

        if "frame_properties" not in data['interactive_params']:
            data['interactive_params']["frame_properties"] = {}

            # frame parameters
        if "title_fontsize" not in data['interactive_params']['frame_properties']:
            data['interactive_params']['frame_properties']['title_fontsize'] = self.config.interactive_title_fontSize
        if "title_fontweight" not in data['interactive_params']['frame_properties']:
            data['interactive_params']['frame_properties']['title_fontweight'] = self.config.interactive_title_weight
        if "label_fontsize" not in data['interactive_params']['frame_properties']:
            data['interactive_params']['frame_properties']['label_fontsize'] = self.config.interactive_label_fontSize
        if "label_fontweight" not in data['interactive_params']['frame_properties']:
            data['interactive_params']['frame_properties']['label_fontweight'] = self.config.interactive_label_weight
        if "tick_fontsize" not in data['interactive_params']['frame_properties']:
            data['interactive_params']['frame_properties']['tick_fontsize'] = self.config.interactive_tick_fontSize

        if "label_xaxis" not in data['interactive_params']['frame_properties']:
            data['interactive_params']['frame_properties']['label_xaxis'] = True
        if "label_xaxis_fontsize" not in data['interactive_params']['frame_properties']:
            data['interactive_params']['frame_properties']['label_xaxis_fontsize'] = data['interactive_params']['frame_properties']['label_fontsize']
        if "label_yaxis" not in data['interactive_params']['frame_properties']:
            data['interactive_params']['frame_properties']['label_yaxis'] = True
        if "label_yaxis_fontsize" not in data['interactive_params']['frame_properties']:
            data['interactive_params']['frame_properties']['label_yaxis_fontsize'] = data['interactive_params']['frame_properties']['label_fontsize']

        if "ticks_xaxis" not in data['interactive_params']['frame_properties']:
            data['interactive_params']['frame_properties']['ticks_xaxis'] = data['interactive_params']['frame_properties']['tick_fontsize']
            if data['interactive_params']['frame_properties']['ticks_xaxis']:
                data['interactive_params']['frame_properties']['ticks_xaxis_color'] = "#000000"
            else:
                data['interactive_params']['frame_properties']['ticks_xaxis_color'] = None
        
        if "ticks_yaxis" not in data['interactive_params']['frame_properties']:
            data['interactive_params']['frame_properties']['ticks_yaxis'] = True
        if "ticks_yaxis_color" not in data['interactive_params']['frame_properties']:
            data['interactive_params']['frame_properties']['ticks_yaxis_color'] = "#000000"
        
        if "tick_labels_xaxis" not in data['interactive_params']['frame_properties']:
            data['interactive_params']['frame_properties']['tick_labels_xaxis'] = True
        if "tick_labels_xaxis_fontsize" not in data['interactive_params']['frame_properties']:
            data['interactive_params']['frame_properties']['tick_labels_xaxis_fontsize'] = data['interactive_params']['frame_properties']['tick_fontsize']
        if "tick_labels_yaxis" not in data['interactive_params']['frame_properties']:
            data['interactive_params']['frame_properties']['tick_labels_yaxis'] = True
        if "tick_labels_yaxis_fontsize" not in data['interactive_params']['frame_properties']:
            data['interactive_params']['frame_properties']['tick_labels_yaxis_fontsize'] = data['interactive_params']['frame_properties']['tick_fontsize']

            # border parameters
        if "border_left" not in data['interactive_params']['frame_properties']:
            data['interactive_params']['frame_properties']['border_left'] = self.config.interactive_border_min_left
        if "border_right" not in data['interactive_params']['frame_properties']:
            data['interactive_params']['frame_properties']['border_right'] = self.config.interactive_border_min_right
        if "border_top" not in data['interactive_params']['frame_properties']:
            data['interactive_params']['frame_properties']['border_top'] = self.config.interactive_border_min_top
        if "border_bottom" not in data['interactive_params']['frame_properties']:
            data['interactive_params']['frame_properties']['border_bottom'] = self.config.interactive_border_min_bottom
        if "outline_width" not in data['interactive_params']['frame_properties']:
            data['interactive_params']['frame_properties']['outline_width'] = self.config.interactive_outline_width
        if "outline_transparency" not in data['interactive_params']['frame_properties']:
            data['interactive_params']['frame_properties']['outline_transparency'] = self.config.interactive_outline_alpha
        if "gridline" not in data['interactive_params']['frame_properties']:
            data['interactive_params']['frame_properties']['gridline'] = self.config.interactive_grid_line
        if "gridline_color" not in data['interactive_params']['frame_properties']:
            data['interactive_params']['frame_properties']['gridline_color'] = self.config.interactive_grid_line_color
        if "background_color" not in data['interactive_params']['frame_properties']:
            data['interactive_params']['frame_properties']['background_color'] = self.config.interactive_background_color


        return data

    def _preset_interactive_parameters_annotation(self, data):
        """
        Add widget parameters to the item
        ===
        data : dict
            dictionary object will all data
        """
        if "annotation_properties" not in data['interactive_params']:
            data['interactive_params']["annotation_properties"] = {}

        if "show_annotations" not in data['interactive_params']['annotation_properties']:
            data['interactive_params']['annotation_properties']['show_annotations'] = True
        if "show_labels" not in data['interactive_params']['annotation_properties']:
            data['interactive_params']['annotation_properties']['show_labels'] = self.config.interactive_ms_annotations_labels
        if "position_offset_x" not in data['interactive_params']['annotation_properties']:
            data['interactive_params']['annotation_properties']['position_offset_x'] = self.config.interactive_ms_annotations_offsetX
        if "position_offset_y" not in data['interactive_params']['annotation_properties']:
            data['interactive_params']['annotation_properties']['position_offset_y'] = self.config.interactive_ms_annotations_offsetY
        if "label_rotation" not in data['interactive_params']['annotation_properties']:
            data['interactive_params']['annotation_properties']['label_rotation'] = self.config.interactive_ms_annotations_rotation
        if "label_fontsize" not in data['interactive_params']['annotation_properties']:
            data['interactive_params']['annotation_properties']['label_fontsize'] = self.config.interactive_ms_annotations_fontSize
        if "label_fontweight" not in data['interactive_params']['annotation_properties']:
            data['interactive_params']['annotation_properties']['label_fontweight'] = self.config.interactive_ms_annotations_fontWeight
        if "label_color" not in data['interactive_params']['annotation_properties']:
            data['interactive_params']['annotation_properties']['label_color'] = self.config.interactive_ms_annotations_label_color
        if "show_patches" not in data['interactive_params']['annotation_properties']:
            data['interactive_params']['annotation_properties']['show_patches'] = self.config.interactive_ms_annotations_highlight
        if "patch_transparency" not in data['interactive_params']['annotation_properties']:
            data['interactive_params']['annotation_properties']['patch_transparency'] = self.config.interactive_ms_annotations_transparency
        if "label_use_preset_color" not in data['interactive_params']['annotation_properties']:
            data['interactive_params']['annotation_properties']['label_use_preset_color'] = True

            

        return data


class ListCtrl(wx.ListCtrl, listmix.CheckListCtrlMixin):
    """ListCtrl"""

    def __init__(self, parent, id=-1, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.LC_REPORT):
        wx.ListCtrl.__init__(self, parent, id, pos, size, style)
        listmix.CheckListCtrlMixin.__init__(self)

