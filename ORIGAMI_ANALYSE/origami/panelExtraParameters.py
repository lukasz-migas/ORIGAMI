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

import os
import time
import wx
from wx.combo import BitmapComboBox

from help import OrigamiHelp as help
from ids import *
from styles import layout, makeCheckbox, makeToggleBtn, makeSuperTip, makeStaticBox
from toolbox import *


class panelParametersEdit(wx.Panel):
    """Extra settings panel."""
    
    def __init__(self, parent, presenter, config, icons, **kwargs):
        wx.Panel.__init__(self, parent, -1, size=(-1, -1), 
                          style=wx.TAB_TRAVERSAL)
        tstart = time.time()
        self.parent = parent
        self.presenter = presenter
        self.config = config
        self.icons = icons
        self.help = help()
        
        self.importEvent = False
        self.currentPage = None
        self.windowSizes = {'General':(540,400), 'Plot 1D':(540,510), 
                            'Plot 2D':(540,295), 'Plot 3D':(540,385), 
                            'Colorbar':(540,220), 'Legend':(540,350), 
                            'RMSD':(540,540), 'Waterfall':(540,515), 
                            'Violin':(540,415), 'Extra':(540, 640)}

        # make gui items
        self.makeGUI()
#         self.makeStatusBar()

        self.mainBook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.onPageChanged)
        if kwargs['window'] is not None:
            self.mainBook.SetSelection(self.config.extraParamsWindow[kwargs['window']])

        # fire-up some events
        self.onEnableDisableFeatures_1D(evt=None)
        self.onEnableDisableFeatures_2D(evt=None)
        self.onEnableDisableFeatures_3D(evt=None)
        self.onEnableDisableFeatures_colorbar(evt=None)
        self.onEnableDisableFeatures_legend(evt=None)
        self.onEnableDisableFeatures_waterfall(evt=None)
        self.onEnableDisableFeatures_violin(evt=None)
        self.onEnableDisableFeatures_rmsd(evt=None)
        self.onEnableDisableFeatures_general(evt=None)
        
        self.mainSizer.Fit(self)
        self.Centre()
        self.Layout()
        self.Show(True)
        self.SetFocus()
        self.SetSizer(self.mainSizer)
        
        self.onSetupRMSDPosition(evt=None)
        self.onSetupPlotSizes(evt=None)
        self.onPageChanged(evt=None)
#         self.updateStatusbar()
        print("Startup took {:.3f} seconds".format(time.time()-tstart))
        
        wx.EVT_CLOSE(self, self.onClose)
        self.Bind(wx.EVT_CHAR_HOOK, self.OnKey)
        
    def OnKey(self, evt):
        keyCode = evt.GetKeyCode()
        if keyCode == wx.WXK_ESCAPE: # key = esc
            self.onClose(evt=None)
        elif keyCode == 49:
            self.onReplot1D(evt=None)
        elif keyCode == 50:
            self.onReplot2D(evt=None)
        elif keyCode == 51:
            self.onReplot3D(evt=None)
        
        if evt != None:
            evt.Skip()
         
    def onPageChanged(self, evt):
        self.windowSizes = {'General':(540,340), 'Plot 1D':(540,530), 
                            'Plot 2D':(540,295), 'Plot 3D':(540,385), 
                            'Colorbar':(540,220), 'Legend':(540,350), 
                            'RMSD':(540,540), 'Waterfall':(540,550), 
                            'Violin':(540,422), 'Extra':(540, 640)}
        
        self.currentPage = self.mainBook.GetPageText(self.mainBook.GetSelection())
        
        if self.parent._mgr.GetPane(self).IsFloating():
            self.SetSize(self.windowSizes[self.currentPage])
            self.Layout()
            
            self.parent._mgr.GetPane(self).FloatingSize(self.windowSizes[self.currentPage])
            self.parent._mgr.Update()

    def onSetPage(self, **kwargs):
        self.mainBook.SetSelection(self.config.extraParamsWindow[kwargs['window']])
        self.onPageChanged(evt=None)

    def onClose(self, evt):
        """Destroy this frame."""
        self.config._windowSettings['Plot parameters']['show'] = False
        self.config.extraParamsWindow_on_off = False
        self.parent._mgr.GetPane(self).Hide()
        self.parent._mgr.Update()
    # ----
    
    def makeGUI(self):
        
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        # Setup notebook
        self.mainBook = wx.Notebook(self, wx.ID_ANY, wx.DefaultPosition,
                                    wx.DefaultSize, 0)
        # general
        self.settings_general = wx.Panel(self.mainBook, wx.ID_ANY, wx.DefaultPosition,
                                          wx.DefaultSize, wx.TAB_TRAVERSAL|wx.NB_MULTILINE)
        self.mainBook.AddPage(self.makePanelGeneral(self.settings_general), 
                              u"General", False)
        
        # plot 1D
        self.settings_plot1D = wx.Panel(self.mainBook, wx.ID_ANY, wx.DefaultPosition,
                                          wx.DefaultSize, wx.TAB_TRAVERSAL|wx.NB_MULTILINE)
        self.mainBook.AddPage(self.make1DparametersPanel(self.settings_plot1D), 
                              u"Plot 1D", False)
        
        # plot 2D
        self.settings_plot2D = wx.Panel(self.mainBook, wx.ID_ANY, wx.DefaultPosition,
                                          wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.mainBook.AddPage(self.make2DparametersPanel(self.settings_plot2D), u"Plot 2D", False)
        
        # plot 3D
        self.settings_plot3D = wx.Panel(self.mainBook, wx.ID_ANY, wx.DefaultPosition,
                                          wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.mainBook.AddPage(self.make3DparametersPanel(self.settings_plot3D), u"Plot 3D", False)
        
        # colorbar
        self.settings_colorbar =  wx.Panel(self.mainBook, wx.ID_ANY, wx.DefaultPosition,
                                           wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.mainBook.AddPage(self.makeColorbarPanel(self.settings_colorbar), 
                              u"Colorbar", False)
        
        # legend
        self.settings_legend = wx.Panel(self.mainBook, wx.ID_ANY, wx.DefaultPosition,
                                          wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.mainBook.AddPage(self.makeLegendPanel(self.settings_legend), u"Legend", False)
        
        # rmsd
        self.settings_rmsd =  wx.Panel(self.mainBook, wx.ID_ANY, wx.DefaultPosition,
                                           wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.mainBook.AddPage(self.makePanelRMSD(self.settings_rmsd), 
                              u"RMSD", False)
        
        # waterfall
        self.settings_waterfall =  wx.Panel(self.mainBook, wx.ID_ANY, wx.DefaultPosition,
                                           wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.mainBook.AddPage(self.makePanelWaterfall(self.settings_waterfall), 
                              u"Waterfall", False)

        # violin
        self.settings_violin =  wx.Panel(self.mainBook, wx.ID_ANY, wx.DefaultPosition,
                                         wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.mainBook.AddPage(self.makePanelViolin(self.settings_violin), 
                              u"Violin", False)
        
        # plot sizes
        self.settings_extra =  wx.Panel(self.mainBook, wx.ID_ANY, wx.DefaultPosition,
                                           wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.mainBook.AddPage(self.makePanelExtra(self.settings_extra), 
                              u"Extra", False)
        
        # fit sizer
        self.mainSizer.Add(self.mainBook, 1, wx.EXPAND |wx.ALL, 2)
        
        # setup color
        self.mainBook.SetBackgroundColour((240, 240, 240))
        
#     def makeStatusBar(self):
#         self.mainStatusbar = self.CreateStatusBar(4, wx.ST_SIZEGRIP|wx.ST_ELLIPSIZE_MIDDLE, wx.ID_ANY)
#         self.mainStatusbar.SetStatusWidths([-1, 90, 120, 60])
#         self.mainStatusbar.SetFont(wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.NORMAL))
#         
#     def updateStatusbar(self):
#         # update status bar
#         self.SetStatusText('Updating plots:', 0)
#         self.SetStatusText('Plot 1D: %s' % self.parent.panelPlots.window_plot1D, 1) 
#         self.SetStatusText('Plot 2D: %s' % self.parent.panelPlots.window_plot2D, 2) 
#         self.SetStatusText('Plot 3D: %s' % self.parent.panelPlots.window_plot3D, 3) 
              
    def onUpdateValues(self):
        # general
        
        self.plot1D_titleFontWeight_check.GetValue(self.config.titleFontWeight_1D)
        self.plot1D_labelFontWeight_check.GetValue(self.config.labelFontWeight_1D)
        self.plot1D_annotationFontWeight_check.GetValue(self.config.annotationFontWeight_1D)
        self.plot1D_tickFontWeight_check.GetValue(self.config.tickFontWeight_1D)
        self.plot1D_axisOnOff_check.GetValue(self.config.axisOnOff_1D)
        self.plot1D_leftSpines_check.GetValue(self.config.spines_left_1D)
        self.plot1D_rightSpines_check.GetValue(self.config.spines_right_1D)
        self.plot1D_topSpines_check.GetValue(self.config.spines_top_1D)
        self.plot1D_bottomSpines_check.GetValue(self.config.spines_bottom_1D)
        self.plot1D_leftTicks_check.GetValue(self.config.ticks_left_1D)
        self.plot1D_rightTicks_check.GetValue(self.config.ticks_right_1D)
        self.plot1D_topTicks_check.GetValue(self.config.ticks_top_1D)
        self.plot1D_bottomTicks_check.GetValue(self.config.ticks_bottom_1D)
        self.plot1D_leftTickLabels_check.GetValue(self.config.tickLabels_left_1D)
        self.plot1D_rightTickLabels_check.GetValue(self.config.tickLabels_right_1D)
        self.plot1D_topTickLabels_check.GetValue(self.config.tickLabels_top_1D)
        self.plot1D_bottomTickLabels_check.GetValue(self.config.tickLabels_bottom_1D)
        
    def makePanelGeneral(self, panel):
        PANEL_SPACE_MAIN = 2
        axisParameters_staticBox = makeStaticBox(panel, "Axis parameters", 
                                                 size=(-1, -1), color=wx.BLACK)
        axisParameters_staticBox.SetSize((-1,-1))
        axis_box_sizer = wx.StaticBoxSizer(axisParameters_staticBox, wx.HORIZONTAL)
         
        plot1D_axisOnOff_label = wx.StaticText(panel, -1, "Show frame:")
        self.plot1D_axisOnOff_check = makeCheckbox(panel, u"", name="frame")
        self.plot1D_axisOnOff_check.SetValue(self.config.axisOnOff_1D)
        self.plot1D_axisOnOff_check.Bind(wx.EVT_CHECKBOX, self.onApply_1D)
        self.plot1D_axisOnOff_check.Bind(wx.EVT_CHECKBOX, self.onEnableDisableFeatures_1D)
        self.plot1D_axisOnOff_check.Bind(wx.EVT_CHECKBOX, self.onUpdate)
         
        plot1D_spines_label = wx.StaticText(panel, -1, "Line:")
        self.plot1D_leftSpines_check = makeCheckbox(panel, u"Left", name="frame")
        self.plot1D_leftSpines_check.SetValue(self.config.spines_left_1D)
        self.plot1D_leftSpines_check.Bind(wx.EVT_CHECKBOX, self.onApply_1D)
        self.plot1D_leftSpines_check.Bind(wx.EVT_CHECKBOX, self.onUpdate)
         
        self.plot1D_rightSpines_check = makeCheckbox(panel, u"Right", name="frame")
        self.plot1D_rightSpines_check.SetValue(self.config.spines_right_1D)
        self.plot1D_rightSpines_check.Bind(wx.EVT_CHECKBOX, self.onApply_1D)
        self.plot1D_rightSpines_check.Bind(wx.EVT_CHECKBOX, self.onUpdate)
         
        self.plot1D_topSpines_check = makeCheckbox(panel, u"Top", name="frame")
        self.plot1D_topSpines_check.SetValue(self.config.spines_top_1D)
        self.plot1D_topSpines_check.Bind(wx.EVT_CHECKBOX, self.onApply_1D)
        self.plot1D_topSpines_check.Bind(wx.EVT_CHECKBOX, self.onUpdate1D)
         
        self.plot1D_bottomSpines_check = makeCheckbox(panel, u"Bottom", name="frame")
        self.plot1D_bottomSpines_check.SetValue(self.config.spines_bottom_1D)
        self.plot1D_bottomSpines_check.Bind(wx.EVT_CHECKBOX, self.onApply_1D)
        self.plot1D_bottomSpines_check.Bind(wx.EVT_CHECKBOX, self.onUpdate)
         
        plot1D_ticks_label = wx.StaticText(panel, -1, "Ticks:")
        self.plot1D_leftTicks_check = makeCheckbox(panel, u"Left", name="frame")
        self.plot1D_leftTicks_check.SetValue(self.config.ticks_left_1D)
        self.plot1D_leftTicks_check.Bind(wx.EVT_CHECKBOX, self.onApply_1D)
        self.plot1D_leftTicks_check.Bind(wx.EVT_CHECKBOX, self.onUpdate)
         
        self.plot1D_rightTicks_check = makeCheckbox(panel, u"Right", name="frame")
        self.plot1D_rightTicks_check.SetValue(self.config.ticks_right_1D)
        self.plot1D_rightTicks_check.Bind(wx.EVT_CHECKBOX, self.onApply_1D)
        self.plot1D_rightTicks_check.Bind(wx.EVT_CHECKBOX, self.onUpdate)
         
        self.plot1D_topTicks_check = makeCheckbox(panel, u"Top", name="frame")
        self.plot1D_topTicks_check.SetValue(self.config.ticks_top_1D)
        self.plot1D_topTicks_check.Bind(wx.EVT_CHECKBOX, self.onApply_1D)
        self.plot1D_topTicks_check.Bind(wx.EVT_CHECKBOX, self.onUpdate)
         
        self.plot1D_bottomTicks_check = makeCheckbox(panel, u"Bottom", name="frame")
        self.plot1D_bottomTicks_check.SetValue(self.config.ticks_bottom_1D)
        self.plot1D_bottomTicks_check.Bind(wx.EVT_CHECKBOX, self.onApply_1D)
        self.plot1D_bottomTicks_check.Bind(wx.EVT_CHECKBOX, self.onUpdate)
         
        plot1D_tickLabels_label = wx.StaticText(panel, -1, "Tick labels:")
        self.plot1D_leftTickLabels_check = makeCheckbox(panel, u"Left", name="frame")
        self.plot1D_leftTickLabels_check.SetValue(self.config.tickLabels_left_1D)
        self.plot1D_leftTickLabels_check.Bind(wx.EVT_CHECKBOX, self.onApply_1D)
        self.plot1D_leftTickLabels_check.Bind(wx.EVT_CHECKBOX, self.onUpdate)
         
        self.plot1D_rightTickLabels_check = makeCheckbox(panel, u"Right", name="frame")
        self.plot1D_rightTickLabels_check.SetValue(self.config.tickLabels_right_1D)
        self.plot1D_rightTickLabels_check.Bind(wx.EVT_CHECKBOX, self.onApply_1D)
        self.plot1D_rightTickLabels_check.Bind(wx.EVT_CHECKBOX, self.onUpdate)
         
        self.plot1D_topTickLabels_check = makeCheckbox(panel, u"Top", name="frame")
        self.plot1D_topTickLabels_check.SetValue(self.config.tickLabels_top_1D)
        self.plot1D_topTickLabels_check.Bind(wx.EVT_CHECKBOX, self.onApply_1D)
        self.plot1D_topTickLabels_check.Bind(wx.EVT_CHECKBOX, self.onUpdate)
         
        self.plot1D_bottomTickLabels_check = makeCheckbox(panel, u"Bottom", name="frame")
        self.plot1D_bottomTickLabels_check.SetValue(self.config.tickLabels_bottom_1D)
        self.plot1D_bottomTickLabels_check.Bind(wx.EVT_CHECKBOX, self.onApply_1D)
        self.plot1D_bottomTickLabels_check.Bind(wx.EVT_CHECKBOX, self.onUpdate)
        
        
        plot1D_frameWidth_label = wx.StaticText(panel, -1, "Frame width:")
        self.plot1D_frameWidth_value = wx.SpinCtrlDouble(panel, -1, 
                                               value=str(self.config.frameWidth_1D), 
                                               min=0, max=10, initial=self.config.frameWidth_1D, 
                                               inc=1, size=(90, -1), name="frame")
        self.plot1D_frameWidth_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_1D)
        self.plot1D_frameWidth_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onUpdate)
        
        fontParameters_staticBox = makeStaticBox(panel, "Font parameters", 
                                                 size=(-1, -1), color=wx.BLACK)
        fontParameters_staticBox.SetSize((-1,-1))
        font_box_sizer = wx.StaticBoxSizer(fontParameters_staticBox, wx.HORIZONTAL)
         
        plot1D_padding_label = wx.StaticText(panel, -1, "Label pad:")
        self.plot1D_padding_value = wx.SpinCtrlDouble(panel, -1, 
                                               value=str(self.config.labelPad_1D), 
                                               min=0, max=100, initial=self.config.labelPad_1D, 
                                               inc=5, size=(90, -1), name="fonts")
        self.plot1D_padding_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_1D)
        self.plot1D_padding_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onUpdate)
         
        plot1D_titleFontSize_label = wx.StaticText(panel, -1, "Title font size:")
        self.plot1D_titleFontSize_value = wx.SpinCtrlDouble(panel, -1, 
                                               value=str(self.config.titleFontSize_1D), 
                                               min=0, max=48, initial=self.config.titleFontSize_1D, 
                                               inc=2, size=(90, -1), name="fonts")
        self.plot1D_titleFontSize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_1D)
        self.plot1D_titleFontSize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onUpdate)
 
        self.plot1D_titleFontWeight_check = makeCheckbox(panel, u"Bold", name="fonts")
        self.plot1D_titleFontWeight_check.SetValue(self.config.titleFontWeight_1D)
        self.plot1D_titleFontWeight_check.Bind(wx.EVT_CHECKBOX, self.onApply_1D)
        self.plot1D_titleFontWeight_check.Bind(wx.EVT_CHECKBOX, self.onUpdate)
         
        plot1D_labelFontSize_label = wx.StaticText(panel, -1, "Label font size:")
        self.plot1D_labelFontSize_value = wx.SpinCtrlDouble(panel, -1, 
                                               value=str(self.config.labelFontSize_1D), 
                                               min=0, max=48, initial=self.config.labelFontSize_1D, 
                                               inc=2, size=(90, -1), name="fonts")
        self.plot1D_labelFontSize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_1D)
        self.plot1D_labelFontSize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onUpdate)
 
        self.plot1D_labelFontWeight_check = makeCheckbox(panel, u"Bold", name="fonts")
        self.plot1D_labelFontWeight_check.SetValue(self.config.labelFontWeight_1D)
        self.plot1D_labelFontWeight_check.Bind(wx.EVT_CHECKBOX, self.onApply_1D)
        self.plot1D_labelFontWeight_check.Bind(wx.EVT_CHECKBOX, self.onUpdate)
         
        plot1D_tickFontSize_label = wx.StaticText(panel, -1, "Tick font size:")
        self.plot1D_tickFontSize_value = wx.SpinCtrlDouble(panel, -1, 
                                               value=str(self.config.tickFontSize_1D), 
                                               min=0, max=48, initial=self.config.tickFontSize_1D, 
                                               inc=2, size=(90, -1), name="fonts")
        self.plot1D_tickFontSize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_1D)
        self.plot1D_tickFontSize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onUpdate)
         
        self.plot1D_tickFontWeight_check = makeCheckbox(panel, u"Bold", name="fonts")
        self.plot1D_tickFontWeight_check.SetValue(self.config.tickFontWeight_1D)
        self.plot1D_tickFontWeight_check.Bind(wx.EVT_CHECKBOX, self.onApply_1D)
        self.plot1D_tickFontWeight_check.Bind(wx.EVT_CHECKBOX, self.onUpdate)
        self.plot1D_tickFontWeight_check.Disable()
         
        plot1D_annotationFontSize_label = wx.StaticText(panel, -1, "Annotation font size:")
        self.plot1D_annotationFontSize_value = wx.SpinCtrlDouble(panel, -1, 
                                               value=str(self.config.annotationFontSize_1D), 
                                               min=0, max=48, initial=self.config.annotationFontSize_1D, 
                                               inc=2, size=(90, -1), name="fonts")
        self.plot1D_annotationFontSize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_1D)
        self.plot1D_annotationFontSize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onUpdate)
         
        self.plot1D_annotationFontWeight_check = makeCheckbox(panel, u"Bold", name="fonts")
        self.plot1D_annotationFontWeight_check.SetValue(self.config.annotationFontWeight_1D)
        self.plot1D_annotationFontWeight_check.Bind(wx.EVT_CHECKBOX, self.onApply_1D)
        self.plot1D_annotationFontWeight_check.Bind(wx.EVT_CHECKBOX, self.onUpdate)
         
        
        # axes parameters
        axis_grid = wx.GridBagSizer(2, 2)
        y = 0
        axis_grid.Add(plot1D_axisOnOff_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        axis_grid.Add(self.plot1D_axisOnOff_check, (y,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        y = y+1
        axis_grid.Add(plot1D_spines_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        axis_grid.Add(self.plot1D_leftSpines_check, (y,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        axis_grid.Add(self.plot1D_rightSpines_check, (y,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        axis_grid.Add(self.plot1D_topSpines_check, (y,3), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        axis_grid.Add(self.plot1D_bottomSpines_check, (y,4), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        y = y+1
        axis_grid.Add(plot1D_ticks_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        axis_grid.Add(self.plot1D_leftTicks_check, (y,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        axis_grid.Add(self.plot1D_rightTicks_check, (y,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        axis_grid.Add(self.plot1D_topTicks_check, (y,3), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        axis_grid.Add(self.plot1D_bottomTicks_check, (y,4), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        y = y+1
        axis_grid.Add(plot1D_tickLabels_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        axis_grid.Add(self.plot1D_leftTickLabels_check, (y,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        axis_grid.Add(self.plot1D_rightTickLabels_check, (y,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        axis_grid.Add(self.plot1D_topTickLabels_check, (y,3), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        axis_grid.Add(self.plot1D_bottomTickLabels_check, (y,4), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        y = y+1
        axis_grid.Add(plot1D_frameWidth_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        axis_grid.Add(self.plot1D_frameWidth_value, (y,1), (1,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        axis_box_sizer.Add(axis_grid, 0, wx.EXPAND, 10)
     
        # font parameters
        font_grid = wx.GridBagSizer(2, 2)
        y = 0
        font_grid.Add(plot1D_padding_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        font_grid.Add(self.plot1D_padding_value, (y,1), wx.GBSpan(1,2), flag=wx.EXPAND)
        y = y+1
        font_grid.Add(plot1D_titleFontSize_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        font_grid.Add(self.plot1D_titleFontSize_value, (y,1), wx.GBSpan(1,2), flag=wx.EXPAND)
        font_grid.Add(self.plot1D_titleFontWeight_check, (y,3), wx.GBSpan(1,1), flag=wx.EXPAND)
        y = y+1
        font_grid.Add(plot1D_labelFontSize_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        font_grid.Add(self.plot1D_labelFontSize_value, (y,1), wx.GBSpan(1,2), flag=wx.EXPAND)
        font_grid.Add(self.plot1D_labelFontWeight_check, (y,3), wx.GBSpan(1,1), flag=wx.EXPAND)
        y = y+1
        font_grid.Add(plot1D_tickFontSize_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        font_grid.Add(self.plot1D_tickFontSize_value, (y,1), wx.GBSpan(1,2), flag=wx.EXPAND)
        font_grid.Add(self.plot1D_tickFontWeight_check, (y,3), wx.GBSpan(1,1), flag=wx.EXPAND)
        y = y+1
        font_grid.Add(plot1D_annotationFontSize_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        font_grid.Add(self.plot1D_annotationFontSize_value, (y,1), wx.GBSpan(1,2), flag=wx.EXPAND)
        font_grid.Add(self.plot1D_annotationFontWeight_check, (y,3), wx.GBSpan(1,1), flag=wx.EXPAND)
        font_box_sizer.Add(font_grid, 0, wx.EXPAND, 10)
        
        grid = wx.GridBagSizer(2, 2)
        y = 0
        grid.Add(axis_box_sizer, (y,0), wx.GBSpan(1,5), flag=wx.EXPAND)
        y = y+1
        grid.Add(font_box_sizer, (y,0), wx.GBSpan(1,5), flag=wx.EXPAND)
        
        # pack elements
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(grid, 0, wx.ALIGN_CENTER|wx.ALL, PANEL_SPACE_MAIN)
        
        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)
        
        return panel
              
    def makePanelExtra(self, panel):
        PANEL_SPACE_MAIN = 2
        
        # make elements
        axes_staticBox = makeStaticBox(panel, "Axes parameters", size=(-1, -1), color=wx.BLACK)
        axes_staticBox.SetSize((-1,-1))
        axes_box_sizer = wx.StaticBoxSizer(axes_staticBox, wx.HORIZONTAL)
        
        plotName_label = wx.StaticText(panel, -1, "Plot name:")
        self.general_plotName_value = wx.Choice(panel, -1, 
                                                choices=sorted(self.config._plotSettings.keys()),
                                                size=(-1, -1))
        self.general_plotName_value.SetSelection(0)
        self.general_plotName_value.Bind(wx.EVT_CHOICE, self.onSetupPlotSizes)
        __general_plotName_tip = makeSuperTip(self.general_plotName_value, **self.help.general_plotName)
        
        plotSize_label = wx.StaticText(panel, -1, "Plot size (proportion)")
        
        left_label = wx.StaticText(panel, -1, "Left")
        self.general_left_value = wx.SpinCtrlDouble(panel, -1, value=str(0), 
                                                    min=0.0, max=1, initial=0, inc=0.05,
                                                    size=(60, -1))
        self.general_left_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_general)
        __general_left_tip = makeSuperTip(left_label, **self.help.general_leftAxes)
        
        bottom_label = wx.StaticText(panel, -1, "Bottom")
        self.general_bottom_value = wx.SpinCtrlDouble(panel, -1, value=str(0), 
                                                    min=0.0, max=1, initial=0, inc=0.05,
                                                    size=(60, -1))
        self.general_bottom_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_general)
        __general_bottom_tip = makeSuperTip(bottom_label, **self.help.general_bottomAxes)
        
        width_label = wx.StaticText(panel, -1, "Width")
        self.general_width_value = wx.SpinCtrlDouble(panel, -1, value=str(0), 
                                                    min=0.0, max=1, initial=0, inc=0.05,
                                                    size=(60, -1))
        self.general_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_general)
        __general_width_tip = makeSuperTip(width_label, **self.help.general_widthAxes)
        
        height_label = wx.StaticText(panel, -1, "Height")
        self.general_height_value = wx.SpinCtrlDouble(panel, -1, value=str(0), 
                                                    min=0.0, max=1, initial=0, inc=0.05,
                                                    size=(60, -1))
        self.general_height_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_general)
        __general_height_tip = makeSuperTip(height_label, **self.help.general_heightAxes)

        plotSize_window_inch_label= wx.StaticText(panel, -1, "Plot size (inch)")
        width_window_inch_label = wx.StaticText(panel, -1, "Width")
        self.general_width_window_inch_value = wx.SpinCtrlDouble(panel, -1, value=str(0), 
                                                    min=0.0, max=20, initial=0, inc=.5,
                                                    size=(60, -1))
        self.general_width_window_inch_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_general)
#         __general_width_tip = makeSuperTip(width_label, **self.help.general_widthPlot_inch)
        
        height_window_inch_label = wx.StaticText(panel, -1, "Height")
        self.general_height_window_inch_value = wx.SpinCtrlDouble(panel, -1, value=str(0), 
                                                    min=0.0, max=20, initial=0, inc=.5,
                                                    size=(60, -1))
        self.general_height_window_inch_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_general)
#         __general_height_tip = makeSuperTip(height_label, **self.help.general_heightPlot_inch)

########
        export_staticBox = makeStaticBox(panel, "Export parameters", size=(-1, -1), color=wx.BLACK)
        export_staticBox.SetSize((-1,-1))
        export_box_sizer = wx.StaticBoxSizer(export_staticBox, wx.HORIZONTAL)
        
        plotSize_export_label = wx.StaticText(panel, -1, "Export plot size (proportion)")
        
        left_export_label = wx.StaticText(panel, -1, "Left")
        self.general_left_export_value = wx.SpinCtrlDouble(panel, -1, value=str(0), 
                                                    min=0.0, max=1, initial=0, inc=0.05,
                                                    size=(60, -1))
        self.general_left_export_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        __general_left_tip = makeSuperTip(left_export_label, **self.help.general_leftAxes_export)
        
        bottom_export_label = wx.StaticText(panel, -1, "Bottom")
        self.general_bottom_export_value = wx.SpinCtrlDouble(panel, -1, value=str(0), 
                                                    min=0.0, max=1, initial=0, inc=0.05,
                                                    size=(60, -1))
        self.general_bottom_export_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        __general_bottom_tip = makeSuperTip(bottom_export_label, **self.help.general_bottomAxes_export)
        
        width_export_label = wx.StaticText(panel, -1, "Width")
        self.general_width_export_value = wx.SpinCtrlDouble(panel, -1, value=str(0), 
                                                    min=0.0, max=1, initial=0, inc=0.05,
                                                    size=(60, -1))
        self.general_width_export_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        __general_width_tip = makeSuperTip(width_export_label, **self.help.general_widthAxes_export)
        
        height_export_label = wx.StaticText(panel, -1, "Height")
        self.general_height_export_value = wx.SpinCtrlDouble(panel, -1, value=str(0), 
                                                    min=0.0, max=1, initial=0, inc=0.05,
                                                    size=(60, -1))
        self.general_height_export_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        __general_height_tip = makeSuperTip(height_export_label, **self.help.general_heightAxes_export)
             
        plotSize_inch_label= wx.StaticText(panel, -1, "Plot size (inch)")
        width_inch_label = wx.StaticText(panel, -1, "Width")
        self.general_width_inch_value = wx.SpinCtrlDouble(panel, -1, value=str(0), 
                                                    min=0.0, max=20, initial=0, inc=2,
                                                    size=(60, -1))
        self.general_width_inch_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_general)
        __general_width_tip = makeSuperTip(width_label, **self.help.general_widthPlot_inch)
        
        height_inch_label = wx.StaticText(panel, -1, "Height")
        self.general_height_inch_value = wx.SpinCtrlDouble(panel, -1, value=str(0), 
                                                    min=0.0, max=20, initial=0, inc=2,
                                                    size=(60, -1))
        self.general_height_inch_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_general)
        __general_height_tip = makeSuperTip(height_label, **self.help.general_heightPlot_inch)

########
        style_staticBox = makeStaticBox(panel, "Style parameters", size=(-1, -1), color=wx.BLACK)
        style_staticBox.SetSize((-1,-1))
        style_box_sizer = wx.StaticBoxSizer(style_staticBox, wx.HORIZONTAL)
        
        style_label = wx.StaticText(panel, -1, "Style:")
        self.general_style_value = wx.Choice(panel, -1, 
                                             choices=self.config.styles,
                                             size=(-1, -1))
        self.general_style_value.SetStringSelection(self.config.currentStyle)
        self.general_style_value.Bind(wx.EVT_CHOICE, self.onChangePlotStyle)
        
        palette_label = wx.StaticText(panel, -1, "Color palette:")
        self.general_palette_value = BitmapComboBox(panel, -1, choices=[],
                                                    size=(160, -1), style=wx.CB_READONLY)
        
        # add choices
        self.general_palette_value.Append("HLS", bitmap=self.icons.iconsLib['cmap_hls'])
        self.general_palette_value.Append("HUSL", bitmap=self.icons.iconsLib['cmap_husl'])
        self.general_palette_value.Append("Cubehelix", bitmap=self.icons.iconsLib['cmap_cubehelix'])
        self.general_palette_value.Append("Spectral", bitmap=self.icons.iconsLib['cmap_spectral'])
        self.general_palette_value.Append("Viridis", bitmap=self.icons.iconsLib['cmap_viridis'])
        self.general_palette_value.Append("Rainbow", bitmap=self.icons.iconsLib['cmap_rainbow'])
        self.general_palette_value.Append("Inferno", bitmap=self.icons.iconsLib['cmap_inferno'])
        self.general_palette_value.Append("Cividis", bitmap=self.icons.iconsLib['cmap_cividis'])
        self.general_palette_value.Append("Winter", bitmap=self.icons.iconsLib['cmap_winter'])
        self.general_palette_value.Append("Cool", bitmap=self.icons.iconsLib['cmap_cool'])
        self.general_palette_value.Append("Gray", bitmap=self.icons.iconsLib['cmap_gray'])
        self.general_palette_value.Append("RdPu", bitmap=self.icons.iconsLib['cmap_rdpu'])
        self.general_palette_value.Append("Tab20b", bitmap=self.icons.iconsLib['cmap_tab20b'])
        self.general_palette_value.Append("Tab20c", bitmap=self.icons.iconsLib['cmap_tab20c'])
#         self.general_palette_value.Append("Modern UI 1", bitmap=self.icons.iconsLib['cmap_modern1'])
#         self.general_palette_value.Append("Modern UI 2", bitmap=self.icons.iconsLib['cmap_modern2'])
        
        self.general_palette_value.SetStringSelection(self.config.currentPalette)
        self.general_palette_value.Bind(wx.EVT_COMBOBOX, self.onChangePalette)
        
########
        CTRL_SIZE = 60
        
        plot_staticBox = makeStaticBox(panel, "Interactive plot parameters", size=(-1, -1), color=wx.BLACK)
        plot_staticBox.SetSize((-1,-1))
        plot_box_sizer = wx.StaticBoxSizer(plot_staticBox, wx.HORIZONTAL)
         
        zoom_grid_label = wx.StaticText(panel, -1, "Show cursor grid:")
        self.zoom_grid_check = makeCheckbox(panel, u"")
        self.zoom_grid_check.SetValue(self.config._plots_grid_show)
        self.zoom_grid_check.Bind(wx.EVT_CHECKBOX, self.onApply_zoom)
        self.zoom_grid_check.Bind(wx.EVT_CHECKBOX, self.onEnableDisableFeatures_general)

        zoom_cursor_width_label = wx.StaticText(panel, -1, "Cursor line width:")
        self.zoom_cursor_lineWidth_value = wx.SpinCtrlDouble(panel, -1, 
                                                       value=str(self.config._plots_grid_line_width), 
                                                       min=0.5, max=10, initial=0, inc=0.5,
                                                       size=(CTRL_SIZE, -1))
        self.zoom_cursor_lineWidth_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_zoom)
        
        zoom_cursor_color_label = wx.StaticText(panel, -1, "Color:")
        self.zoom_cursor_colorBtn = wx.Button(panel, ID_extraSettings_zoomCursorColor,
                                              u"", wx.DefaultPosition, 
                                              wx.Size( 26, 26 ), 0 )
        self.zoom_cursor_colorBtn.SetBackgroundColour(convertRGB1to255(self.config._plots_grid_color))
        self.zoom_cursor_colorBtn.Bind(wx.EVT_BUTTON, self.onChangeColour)
        
        zoom_extract_width_label = wx.StaticText(panel, -1, "Extract line width:")
        self.zoom_extract_lineWidth_value = wx.SpinCtrlDouble(panel, -1, 
                                                       value=str(self.config._plots_extract_line_width), 
                                                       min=0.5, max=10, initial=0, inc=0.5,
                                                       size=(CTRL_SIZE, -1))
        self.zoom_extract_lineWidth_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_zoom)
        
        zoom_extract_crossover_1D_label = wx.StaticText(panel, -1, "Crossover (1D):")
        self.zoom_extract_crossover1D_value = wx.SpinCtrlDouble(panel, -1, 
                                                                value=str(self.config._plots_extract_crossover_1D), 
                                                                min=0.01, max=1, initial=0, inc=0.01,
                                                                size=(CTRL_SIZE, -1))
        self.zoom_extract_crossover1D_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_zoom)
        
        zoom_extract_crossover_2D_label = wx.StaticText(panel, -1, "Crossover (2D):")
        self.zoom_extract_crossover2D_value = wx.SpinCtrlDouble(panel, -1, 
                                                                value=str(self.config._plots_extract_crossover_2D), 
                                                                min=0.001, max=1, initial=0, inc=0.01,
                                                                size=(CTRL_SIZE, -1))
        self.zoom_extract_crossover2D_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_zoom)
        
        zoom_extract_color_label = wx.StaticText(panel, -1, "Color:")
        self.zoom_extract_colorBtn = wx.Button(panel, ID_extraSettings_extractColor,
                                              u"", wx.DefaultPosition, 
                                              wx.Size( 26, 26 ), 0 )
        self.zoom_extract_colorBtn.SetBackgroundColour(convertRGB1to255(self.config._plots_extract_color))
        self.zoom_extract_colorBtn.Bind(wx.EVT_BUTTON, self.onChangeColour)        
        
        zoom_zoom_width_label = wx.StaticText(panel, -1, "Zoom line width:")
        self.zoom_zoom_lineWidth_value = wx.SpinCtrlDouble(panel, -1, 
                                                       value=str(self.config._plots_zoom_line_width), 
                                                       min=0.5, max=10, initial=0, inc=0.5,
                                                       size=(CTRL_SIZE, -1))
        self.zoom_zoom_lineWidth_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_zoom)
        
        zoom_zoom_vertical_color_label = wx.StaticText(panel, -1, "Vertical:")
        self.zoom_zoom_vertical_colorBtn = wx.Button(panel, ID_extraSettings_verticalColor,
                                              u"", wx.DefaultPosition, 
                                              wx.Size( 26, 26 ), 0 )
        self.zoom_zoom_vertical_colorBtn.SetBackgroundColour(convertRGB1to255(self.config._plots_zoom_vertical_color))
        self.zoom_zoom_vertical_colorBtn.Bind(wx.EVT_BUTTON, self.onChangeColour)

        zoom_zoom_horizontal_color_label = wx.StaticText(panel, -1, "Horizontal:")
        self.zoom_zoom_horizontal_colorBtn = wx.Button(panel, ID_extraSettings_horizontalColor,
                                              u"", wx.DefaultPosition, 
                                              wx.Size( 26, 26 ), 0 )
        self.zoom_zoom_horizontal_colorBtn.SetBackgroundColour(convertRGB1to255(self.config._plots_zoom_horizontal_color))
        self.zoom_zoom_horizontal_colorBtn.Bind(wx.EVT_BUTTON, self.onChangeColour)
        
        
        zoom_zoom_box_color_label = wx.StaticText(panel, -1, "Rectangle:")
        self.zoom_zoom_box_colorBtn = wx.Button(panel, ID_extraSettings_boxColor,
                                              u"", wx.DefaultPosition, 
                                              wx.Size( 26, 26 ), 0 )
        self.zoom_zoom_box_colorBtn.SetBackgroundColour(convertRGB1to255(self.config._plots_zoom_box_color))
        self.zoom_zoom_box_colorBtn.Bind(wx.EVT_BUTTON, self.onChangeColour)
        
        zoom_sensitivity_label = wx.StaticText(panel, -1, "Zoom crossover:")
        self.zoom_sensitivity_value = wx.SpinCtrlDouble(panel, -1, 
                                                       value=str(self.config._plots_zoom_crossover), 
                                                       min=0.01, max=1, initial=0, inc=0.01,
                                                       size=(CTRL_SIZE, -1))
        self.zoom_sensitivity_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_zoom)
        _zoom_sensitivity_value = makeSuperTip(zoom_sensitivity_label, **self.help.general_zoom_crossover)
        
########
        gui_staticBox = makeStaticBox(panel, "Graphical User Interface parameters", size=(-1, -1), color=wx.BLACK)
        gui_staticBox.SetSize((-1,-1))
        gui_box_sizer = wx.StaticBoxSizer(gui_staticBox, wx.HORIZONTAL)
        
        self.general_instantPlot_check = makeCheckbox(panel, u"Instant plot when selected in Document Tree", ID=ID_extraSettings_instantPlot)
        self.general_instantPlot_check.SetValue(self.config.quickDisplay)
        self.general_instantPlot_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        self.general_instantPlot_check.Bind(wx.EVT_CHECKBOX, self.onUpdateGUI)
        _general_instantPlot_check = makeSuperTip(self.general_instantPlot_check, **self.help.general_instantPlot)

        self.general_multiThreading_check = makeCheckbox(panel, u"Multi-threading", ID=ID_extraSettings_multiThreading)
        self.general_multiThreading_check.SetValue(self.config.threading)
        self.general_multiThreading_check.Bind(wx.EVT_CHECKBOX, self.onUpdateGUI)
        _general_multiThreading_check = makeSuperTip(self.general_multiThreading_check, **self.help.general_multiThreading)
        
        self.general_logToFile_check = makeCheckbox(panel, u"Log events to file", ID=ID_extraSettings_logging)
        self.general_logToFile_check.SetValue(self.config.logging)
        self.general_logToFile_check.Bind(wx.EVT_CHECKBOX, self.onUpdateGUI)
        _general_logToFile_check = makeSuperTip(self.general_logToFile_check, **self.help.general_logToFile)
        
        self.general_autoSaveSettings_check = makeCheckbox(panel, u"Auto-save settings", ID=ID_extraSettings_autoSaveSettings)
        self.general_autoSaveSettings_check.SetValue(self.config.autoSaveSettings)
        self.general_autoSaveSettings_check.Bind(wx.EVT_CHECKBOX, self.onUpdateGUI)
        _general_autoSaveSettings_check = makeSuperTip(self.general_autoSaveSettings_check, **self.help.general_autoSaveSettings)

        # add elements to grids
        axes_grid = wx.GridBagSizer(2, 2)
        y = 0
        axes_grid.Add(plotName_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        axes_grid.Add(self.general_plotName_value, (y,1), wx.GBSpan(1,2), flag=wx.EXPAND)
        y = y+1
        axes_grid.Add(left_label, (y,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        axes_grid.Add(bottom_label, (y,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        axes_grid.Add(width_label, (y,3), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        axes_grid.Add(height_label, (y,4), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        y = y+1
        axes_grid.Add(plotSize_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        axes_grid.Add(self.general_left_value, (y,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        axes_grid.Add(self.general_bottom_value, (y,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        axes_grid.Add(self.general_width_value, (y,3), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        axes_grid.Add(self.general_height_value, (y,4), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        y = y+1
        axes_grid.Add(width_window_inch_label, (y,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        axes_grid.Add(height_window_inch_label, (y,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        y = y+1
        axes_grid.Add(plotSize_window_inch_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        axes_grid.Add(self.general_width_window_inch_value, (y,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        axes_grid.Add(self.general_height_window_inch_value, (y,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        axes_box_sizer.Add(axes_grid, 0, wx.EXPAND, 10)
        
        export_grid = wx.GridBagSizer(2, 2)
        y = 0
        export_grid.Add(left_export_label, (y,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        export_grid.Add(bottom_export_label, (y,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        export_grid.Add(width_export_label, (y,3), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        export_grid.Add(height_export_label, (y,4), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        y = y+1
        export_grid.Add(plotSize_export_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        export_grid.Add(self.general_left_export_value, (y,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        export_grid.Add(self.general_bottom_export_value, (y,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        export_grid.Add(self.general_width_export_value, (y,3), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        export_grid.Add(self.general_height_export_value, (y,4), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        y = y+1
        export_grid.Add(width_inch_label, (y,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        export_grid.Add(height_inch_label, (y,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        y = y+1
        export_grid.Add(plotSize_inch_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        export_grid.Add(self.general_width_inch_value, (y,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        export_grid.Add(self.general_height_inch_value, (y,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        export_box_sizer.Add(export_grid, 0, wx.EXPAND, 10)
        
        style_grid = wx.GridBagSizer(2, 2)
        y = 0
        style_grid.Add(style_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        style_grid.Add(self.general_style_value, (y,1), wx.GBSpan(1,2), flag=wx.EXPAND)
        style_grid.Add(palette_label, (y,3), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        style_grid.Add(self.general_palette_value, (y,4), wx.GBSpan(1,2), flag=wx.EXPAND)
        style_box_sizer.Add(style_grid, 0, wx.EXPAND, 10)
        
        plot_grid = wx.GridBagSizer(2, 2)
        y = 0
        plot_grid.Add(zoom_grid_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        plot_grid.Add(self.zoom_grid_check, (y,1), wx.GBSpan(1,2), flag=wx.EXPAND)
        y = y+1
        plot_grid.Add(zoom_cursor_width_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        plot_grid.Add(self.zoom_cursor_lineWidth_value, (y,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        plot_grid.Add(zoom_cursor_color_label, (y,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        plot_grid.Add(self.zoom_cursor_colorBtn, (y,3), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT)
        y = y+1
        plot_grid.Add(zoom_extract_width_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        plot_grid.Add(self.zoom_extract_lineWidth_value, (y,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        plot_grid.Add(zoom_extract_color_label, (y,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        plot_grid.Add(self.zoom_extract_colorBtn, (y,3), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT)
        y = y+1
        plot_grid.Add(zoom_extract_crossover_1D_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        plot_grid.Add(self.zoom_extract_crossover1D_value, (y,1), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT)
        plot_grid.Add(zoom_extract_crossover_2D_label, (y,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        plot_grid.Add(self.zoom_extract_crossover2D_value, (y,3), wx.GBSpan(1,2), flag=wx.ALIGN_LEFT)
        y = y+1
        plot_grid.Add(zoom_zoom_width_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        plot_grid.Add(self.zoom_zoom_lineWidth_value, (y,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        plot_grid.Add(zoom_zoom_vertical_color_label, (y,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        plot_grid.Add(self.zoom_zoom_vertical_colorBtn, (y,3), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT)
        plot_grid.Add(zoom_zoom_horizontal_color_label, (y,4), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        plot_grid.Add(self.zoom_zoom_horizontal_colorBtn, (y,5), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT)
        plot_grid.Add(zoom_zoom_box_color_label, (y,6), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        plot_grid.Add(self.zoom_zoom_box_colorBtn, (y,7), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT)
        y = y+1
        plot_grid.Add(zoom_sensitivity_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        plot_grid.Add(self.zoom_sensitivity_value, (y,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        plot_box_sizer.Add(plot_grid, 0, wx.EXPAND, 10)
        
        gui_grid = wx.GridBagSizer(2, 2)
        y = 0
        gui_grid.Add(self.general_instantPlot_check, (y,0), wx.GBSpan(1,2), flag=wx.EXPAND)
        y = y+1
        gui_grid.Add(self.general_multiThreading_check, (y,0), wx.GBSpan(1,2), flag=wx.EXPAND)
        y = y+1
        gui_grid.Add(self.general_logToFile_check, (y,0), wx.GBSpan(1,2), flag=wx.EXPAND)
        y = y+1
        gui_grid.Add(self.general_autoSaveSettings_check, (y,0), wx.GBSpan(1,2), flag=wx.EXPAND)
        gui_box_sizer.Add(gui_grid, 0, wx.EXPAND, 10)
        
        # add elements to the main grid
        grid = wx.GridBagSizer(2, 2)
        y = 0
        grid.Add(axes_box_sizer, (y,0), wx.GBSpan(1,5), flag=wx.EXPAND|wx.ALIGN_LEFT)
        y = y+1
        grid.Add(export_box_sizer, (y,0), wx.GBSpan(1,5), flag=wx.EXPAND|wx.ALIGN_LEFT)
        y = y+1
        grid.Add(style_box_sizer, (y,0), wx.GBSpan(1,5), flag=wx.EXPAND|wx.ALIGN_LEFT)
        y = y+1
        grid.Add(plot_box_sizer, (y,0), wx.GBSpan(1,5), flag=wx.EXPAND|wx.ALIGN_LEFT)
        y = y+1
        grid.Add(gui_box_sizer, (y,0), wx.GBSpan(1,5), flag=wx.EXPAND|wx.ALIGN_LEFT)
        
        # pack elements
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(grid, 0, wx.ALIGN_CENTER|wx.ALL, PANEL_SPACE_MAIN)
        
        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)
        
        return panel
        
    def makePanelRMSD(self, panel):
        PANEL_SPACE_MAIN = 2
        
        rmsd_staticBox = makeStaticBox(panel, "RMSD", size=(-1, -1), color=wx.BLACK)
        rmsd_staticBox.SetSize((-1,-1))
        rmsd_box_sizer = wx.StaticBoxSizer(rmsd_staticBox, wx.HORIZONTAL)

        rmsd_position_label = wx.StaticText(panel, -1, "Position:")
        self.rmsd_position_value= wx.Choice(panel, -1, 
                                              choices=self.config.rmsd_position_choices,
                                              size=(-1, -1))
        self.rmsd_position_value.SetStringSelection(self.config.rmsd_position)
        self.rmsd_position_value.Bind(wx.EVT_CHOICE, self.onSetupRMSDPosition)
        self.rmsd_position_value.Bind(wx.EVT_CHOICE, self.onEnableDisableFeatures_rmsd)
        self.rmsd_position_value.Bind(wx.EVT_CHOICE, self.onApply)
        self.rmsd_position_value.Bind(wx.EVT_CHOICE, self.onUpdateLabel)
        
        rmsd_x_position_label = wx.StaticText(panel, -1, "Position X:")
        self.rmsd_positionX_value = wx.SpinCtrlDouble(panel, -1, 
                                                      value=str(), min=0, max=100, initial=0, 
                                                      inc=5, size=(90, -1))
        self.rmsd_positionX_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onSetupRMSDPosition)
        self.rmsd_positionX_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onUpdateLabel)
        
        rmsd_y_position_label = wx.StaticText(panel, -1, "Position Y:")
        self.rmsd_positionY_value = wx.SpinCtrlDouble(panel, -1, 
                                                      value=str(), min=0, max=100, initial=0, 
                                                      inc=5, size=(90, -1))
        self.rmsd_positionY_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onSetupRMSDPosition)
        self.rmsd_positionY_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onUpdateLabel)
        
        rmsd_fontSize_label = wx.StaticText(panel, -1, "Label size:")
        self.rmsd_fontSize_value = wx.SpinCtrlDouble(panel, -1, 
                                                     value=str(self.config.rmsd_fontSize), 
                                                     min=1, max=50, initial=0, inc=1,
                                                     size=(90, -1))
        self.rmsd_fontSize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        self.rmsd_fontSize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onUpdateLabel)
        
        self.rmsd_fontWeight_check = makeCheckbox(panel, u"Bold")
        self.rmsd_fontWeight_check.SetValue(self.config.rmsd_fontWeight)
        self.rmsd_fontWeight_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        self.rmsd_fontWeight_check.Bind(wx.EVT_CHECKBOX, self.onUpdateLabel)
        
        rmsd_color_label = wx.StaticText(panel, -1, "Label color:")
        self.rmsd_colorBtn = wx.Button(panel, ID_extraSettings_labelColor_rmsd, u"", wx.DefaultPosition, 
                                       wx.Size( 26, 26 ), 0 )
        self.rmsd_colorBtn.SetBackgroundColour(convertRGB1to255(self.config.rmsd_color))
        self.rmsd_colorBtn.Bind(wx.EVT_BUTTON, self.onChangeColour)

        rmsf_staticBox = makeStaticBox(panel, "RMSF", size=(-1, -1), color=wx.BLACK)
        rmsf_staticBox.SetSize((-1,-1))
        rmsf_box_sizer = wx.StaticBoxSizer(rmsf_staticBox, wx.HORIZONTAL)


        rmsd_lineWidth_label = wx.StaticText(panel, -1, "Line width:")
        self.rmsd_lineWidth_value = wx.SpinCtrlDouble(panel, -1, 
                                                      value=str(self.config.lineWidth_1D*10), 
                                                      min=1, max=100, initial=self.config.rmsd_lineWidth*10, 
                                                      inc=5, size=(90, -1), name="rmsf")
        self.rmsd_lineWidth_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        self.rmsd_lineWidth_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onUpdate2D)
        
        rmsd_lineColor_label = wx.StaticText(panel, -1, "Line color:")
        self.rmsd_colorLineBtn = wx.Button(panel, ID_extraSettings_lineColor_rmsd,
                                           u"", wx.DefaultPosition, 
                                           wx.Size( 26, 26 ), 0 )
        self.rmsd_colorLineBtn.SetBackgroundColour(convertRGB1to255(self.config.rmsd_lineColour))
        self.rmsd_colorLineBtn.Bind(wx.EVT_BUTTON, self.onChangeColour)
#         self.rmsd_colorLineBtn.Bind(wx.EVT_BUTTON, self.onUpdate2D)
        
        rmsd_lineStyle_label = wx.StaticText(panel, -1, "Line style:")
        self.rmsd_lineStyle_value= wx.Choice(panel, -1, 
                                             choices=self.config.lineStylesList,
                                             size=(-1, -1), name="rmsf")
        self.rmsd_lineStyle_value.SetStringSelection(self.config.rmsd_lineStyle)
        self.rmsd_lineStyle_value.Bind(wx.EVT_CHOICE, self.onApply)
        self.rmsd_lineStyle_value.Bind(wx.EVT_CHOICE, self.onUpdate2D)  
        
        rmsd_lineHatch_label = wx.StaticText(panel, -1, "Underline hatch:")
        self.rmsd_lineHatch_value= wx.Choice(panel, -1, 
                                               choices=self.config.lineHatchDict.keys(),
                                               size=(-1, -1), name="rmsf")
        self.rmsd_lineHatch_value.SetStringSelection(self.config.lineHatchDict.keys()[self.config.lineHatchDict.values().index(self.config.rmsd_lineHatch)])
        self.rmsd_lineHatch_value.Bind(wx.EVT_CHOICE, self.onApply)
        self.rmsd_lineHatch_value.Bind(wx.EVT_CHOICE, self.onUpdate2D)  
        
        rmsd_underlineColor_label = wx.StaticText(panel, -1, "Underline color:")
        self.rmsd_undercolorLineBtn = wx.Button(panel, ID_extraSettings_underlineColor_rmsd,
                                                u"", wx.DefaultPosition, 
                                                wx.Size( 26, 26 ), 0 )
        self.rmsd_undercolorLineBtn.SetBackgroundColour(convertRGB1to255(self.config.rmsd_underlineColor))
        self.rmsd_undercolorLineBtn.Bind(wx.EVT_BUTTON, self.onChangeColour)
        
        rmsd_alpha_label = wx.StaticText(panel, -1, "Underline transparency:")
        self.rmsd_alpha_value = wx.SpinCtrlDouble(panel, -1, 
                                                  value=str(self.config.rmsd_underlineTransparency*100), 
                                                  min=0, max=100, initial=self.config.rmsd_underlineTransparency*100, 
                                                  inc=5, size=(90, -1), name="rmsf")
        self.rmsd_alpha_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        self.rmsd_alpha_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onUpdate2D)  
        
        rmsd_hspace_label = wx.StaticText(panel, -1, "Vertical spacing:")
        self.rmsd_hspace_value = wx.SpinCtrlDouble(panel, -1, 
                                                  value=str(self.config.rmsd_hspace), 
                                                  min=0, max=1, initial=self.config.rmsd_hspace, 
                                                  inc=0.05, size=(90, -1), name="rmsf")
        self.rmsd_hspace_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        self.rmsd_hspace_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onUpdate2D)  
        
        rmsd_matrix_staticBox = makeStaticBox(panel, "RMSD Matrix", size=(-1, -1), color=wx.BLACK)
        rmsd_matrix_staticBox.SetSize((-1,-1))
        rmsd_matrix_box_sizer = wx.StaticBoxSizer(rmsd_matrix_staticBox, wx.HORIZONTAL)
        
        rmsd_rotationX_label = wx.StaticText(panel, -1, "Rotation (X-axis):")
        self.rmsd_rotationX_value = wx.SpinCtrlDouble(panel, -1, 
                                                     value=str(self.config.rmsd_rotation_X), 
                                                     min=0, max=360, initial=0, inc=45,
                                                     size=(90, -1))
        self.rmsd_rotationX_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        self.rmsd_rotationX_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onUpdateLabel_Matrix)
        
        rmsd_rotationY_label = wx.StaticText(panel, -1, "Rotation (Y-axis):")
        self.rmsd_rotationY_value = wx.SpinCtrlDouble(panel, -1, 
                                                     value=str(self.config.rmsd_rotation_Y), 
                                                     min=0, max=360, initial=0, inc=45,
                                                     size=(90, -1))
        self.rmsd_rotationY_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        self.rmsd_rotationY_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onUpdateLabel_Matrix)

        rmsd_add_labels_label = wx.StaticText(panel, -1, "Add labels:")
        self.rmsd_add_labels_check = makeCheckbox(panel, u"")
        self.rmsd_add_labels_check.SetValue(self.config.rmsd_matrix_add_labels)
        self.rmsd_add_labels_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        self.rmsd_add_labels_check.Bind(wx.EVT_CHECKBOX, self.onUpdateLabel_Matrix)
        
        rmsd_grid = wx.GridBagSizer(2, 2)
        y = 0
        rmsd_grid.Add(rmsd_position_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        rmsd_grid.Add(self.rmsd_position_value, (y,1), flag=wx.EXPAND)
        y = y+1
        rmsd_grid.Add(rmsd_x_position_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        rmsd_grid.Add(self.rmsd_positionX_value, (y,1), flag=wx.EXPAND)
        y = y+1
        rmsd_grid.Add(rmsd_y_position_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        rmsd_grid.Add(self.rmsd_positionY_value, (y,1), flag=wx.EXPAND)
        y = y+1
        rmsd_grid.Add(rmsd_fontSize_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        rmsd_grid.Add(self.rmsd_fontSize_value, (y,1), flag=wx.EXPAND)
        rmsd_grid.Add(self.rmsd_fontWeight_check, (y,2), wx.GBSpan(1,1), flag=wx.EXPAND)
        y = y+1
        rmsd_grid.Add(rmsd_color_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        rmsd_grid.Add(self.rmsd_colorBtn, (y,1), flag=wx.EXPAND)
        rmsd_box_sizer.Add(rmsd_grid, 0, wx.EXPAND, 10)
        
        rmsf_grid = wx.GridBagSizer(2, 2)
        y = 0
        rmsf_grid.Add(rmsd_lineWidth_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        rmsf_grid.Add(self.rmsd_lineWidth_value, (y,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        y = y+1
        rmsf_grid.Add(rmsd_lineColor_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        rmsf_grid.Add(self.rmsd_colorLineBtn, (y,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        y = y+1
        rmsf_grid.Add(rmsd_lineStyle_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        rmsf_grid.Add(self.rmsd_lineStyle_value, (y,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        y = y+1
        rmsf_grid.Add(rmsd_lineHatch_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        rmsf_grid.Add(self.rmsd_lineHatch_value, (y,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        y = y+1
        rmsf_grid.Add(rmsd_underlineColor_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        rmsf_grid.Add(self.rmsd_undercolorLineBtn, (y,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        y = y+1
        rmsf_grid.Add(rmsd_alpha_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        rmsf_grid.Add(self.rmsd_alpha_value, (y,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        y = y+1
        rmsf_grid.Add(rmsd_hspace_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        rmsf_grid.Add(self.rmsd_hspace_value, (y,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        rmsf_box_sizer.Add(rmsf_grid, 0, wx.EXPAND, 10)
        
        rmsd_matrix_grid = wx.GridBagSizer(2, 2)
        y = 0
        rmsd_matrix_grid.Add(rmsd_rotationX_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        rmsd_matrix_grid.Add(self.rmsd_rotationX_value, (y,1), flag=wx.EXPAND)
        y = y+1
        rmsd_matrix_grid.Add(rmsd_rotationY_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        rmsd_matrix_grid.Add(self.rmsd_rotationY_value, (y,1), flag=wx.EXPAND)
        y = y+1
        rmsd_matrix_grid.Add(rmsd_add_labels_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        rmsd_matrix_grid.Add(self.rmsd_add_labels_check, (y,1), flag=wx.EXPAND)
        
        rmsd_matrix_box_sizer.Add(rmsd_matrix_grid, 0, wx.EXPAND, 10)
        
        grid = wx.GridBagSizer(2, 2)
        y = 0
        grid.Add(rmsd_box_sizer, (y,0), wx.GBSpan(1,5), flag=wx.EXPAND)
        y = y+1
        grid.Add(rmsf_box_sizer, (y,0), wx.GBSpan(1,5), flag=wx.EXPAND)
        y = y+1
        grid.Add(rmsd_matrix_box_sizer, (y,0), wx.GBSpan(1,5), flag=wx.EXPAND)
        
        # pack elements
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(grid, 0, wx.ALIGN_CENTER|wx.ALL, PANEL_SPACE_MAIN)
        
        
        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)
        
        return panel
        
    def makePanelViolin(self, panel):
        PANEL_SPACE_MAIN = 2
        
        # make elements
        violin_orientation_label = wx.StaticText(panel, -1, "Line style:")
        self.violin_orientation_value= wx.Choice(panel, -1, choices=self.config.violin_orientation_choices,
                                                  size=(-1, -1), name="style")
        self.violin_orientation_value.SetStringSelection(self.config.violin_orientation)
        self.violin_orientation_value.Bind(wx.EVT_CHOICE, self.onApply)
        
        violin_spacing_label = wx.StaticText(panel, -1, "Spacing:")
        self.violin_spacing_value = wx.SpinCtrlDouble(panel, -1, 
                                                        value=str(self.config.violin_spacing), 
                                                        min=0.0, max=5, initial=0, inc=0.25,
                                                        size=(90, -1))
        self.violin_spacing_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        
        violin_min_percentage_label = wx.StaticText(panel, -1, "Noise threshold:")
        self.violin_min_percentage_value = wx.SpinCtrlDouble(panel, -1, 
                                                        value=str(self.config.violin_min_percentage), 
                                                        min=0.0, max=1.0, initial=0, inc=0.01,
                                                        size=(90, -1), name="data")
        self.violin_min_percentage_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        self.violin_min_percentage_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onUpdate2D)
        
        violin_normalize_label = wx.StaticText(panel, -1, "Normalize:")
        self.violin_normalize_check = makeCheckbox(panel, u"")
        self.violin_normalize_check.SetValue(self.config.violin_normalize)
        self.violin_normalize_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        

        violin_lineWidth_label = wx.StaticText(panel, -1, "Line width:")
        self.violin_lineWidth_value = wx.SpinCtrlDouble(panel, -1, 
                                                           value=str(self.config.violin_lineWidth), 
                                                           min=1, max=10, initial=self.config.violin_lineWidth, 
                                                           inc=1, size=(90, -1), name="style")
        self.violin_lineWidth_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        self.violin_lineWidth_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onUpdate2D)
        
        violin_lineStyle_label = wx.StaticText(panel, -1, "Line style:")
        self.violin_lineStyle_value= wx.Choice(panel, -1, choices=self.config.lineStylesList,
                                                  size=(-1, -1), name="style")
        self.violin_lineStyle_value.SetStringSelection(self.config.violin_lineStyle)
        self.violin_lineStyle_value.Bind(wx.EVT_CHOICE, self.onApply)
        self.violin_lineStyle_value.Bind(wx.EVT_CHOICE, self.onUpdate2D)

        violin_lineColor_label = wx.StaticText(panel, -1, "Line color:")
        self.violin_colorLineBtn = wx.Button(panel, ID_extraSettings_lineColour_violin,
                                                u"", wx.DefaultPosition, 
                                                wx.Size( 26, 26 ), 0, name="color")
        self.violin_colorLineBtn.SetBackgroundColour(convertRGB1to255(self.config.violin_color))
        self.violin_colorLineBtn.Bind(wx.EVT_BUTTON, self.onChangeColour)
        
        self.violin_line_sameAsShade_check = makeCheckbox(panel, u"Same as shade", name="color")
        self.violin_line_sameAsShade_check.SetValue(self.config.violin_line_sameAsShade)
        self.violin_line_sameAsShade_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        self.violin_line_sameAsShade_check.Bind(wx.EVT_CHECKBOX, self.onEnableDisableFeatures_violin)
        self.violin_line_sameAsShade_check.Bind(wx.EVT_CHECKBOX, self.onUpdate2D)
        
        violin_color_scheme_label = wx.StaticText(panel, -1, "Color scheme:")
        self.violin_colorScheme_value= wx.Choice(panel, -1, choices=self.config.waterfall_color_choices,
                                                    size=(-1, -1), name="color")
        self.violin_colorScheme_value.SetStringSelection(self.config.violin_color_value)
        self.violin_colorScheme_value.Bind(wx.EVT_CHOICE, self.onApply)
        self.violin_colorScheme_value.Bind(wx.EVT_CHOICE, self.onUpdate2D)
        self.violin_colorScheme_value.Bind(wx.EVT_CHOICE, self.onEnableDisableFeatures_violin)
        
        self.violin_colorScheme_msg = wx.StaticText(panel, -1, "")

        cmap_list = self.config.cmaps2[:]
        cmap_list.remove("jet")
        violin_colormap_label = wx.StaticText(panel, -1, "Colormap:")
        self.violin_colormap_value = wx.Choice(panel, -1, choices=cmap_list,
                                               size=(-1, -1), name="color")
        self.violin_colormap_value.SetStringSelection(self.config.violin_colormap)
        self.violin_colormap_value.Bind(wx.EVT_CHOICE, self.onApply)
        self.violin_colormap_value.Bind(wx.EVT_CHOICE, self.onUpdate2D)
        
        violin_shadeColor_label = wx.StaticText(panel, -1, "Shade color:")
        self.violin_colorShadeBtn = wx.Button(panel, ID_extraSettings_shadeColour_violin,
                                                u"", wx.DefaultPosition, 
                                                wx.Size( 26, 26 ), 0, name="color")
        self.violin_colorShadeBtn.SetBackgroundColour(convertRGB1to255(self.config.violin_shade_under_color))
        self.violin_colorShadeBtn.Bind(wx.EVT_BUTTON, self.onChangeColour)
        
        violin_shadeTransparency_label = wx.StaticText(panel, -1, "Shade transparency:")
        self.violin_shadeTransparency_value = wx.SpinCtrlDouble(panel, -1,
                                                                value=str(self.config.violin_shade_under_transparency), 
                                                                min=0, max=1, 
                                                                initial=self.config.violin_shade_under_transparency, 
                                                                inc=0.25, size=(90, -1), name="shade")
        self.violin_shadeTransparency_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        self.violin_shadeTransparency_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onUpdate2D)
        
        violin_label_format_label = wx.StaticText(panel, -1, "Label format:")
        self.violin_label_format_value= wx.Choice(panel, -1, choices=self.config.violin_label_format_choices,
                                                    size=(-1, -1), name="label")
        self.violin_label_format_value.SetStringSelection(self.config.waterfall_label_format)
        self.violin_label_format_value.Bind(wx.EVT_CHOICE, self.onApply)
        self.violin_label_format_value.Bind(wx.EVT_CHOICE, self.onUpdate2D)
        self.violin_label_format_value.Bind(wx.EVT_CHOICE, self.onEnableDisableFeatures_violin)
        
        violin_label_frequency_label = wx.StaticText(panel, -1, "Label frequency:")
        self.violin_label_frequency_value = wx.SpinCtrlDouble(panel, -1, 
                                                              value=str(self.config.violin_labels_frequency), 
                                                              min=0, max=100, 
                                                              initial=self.config.violin_labels_frequency, 
                                                              inc=1, size=(45, -1), name="label")
        self.violin_label_frequency_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
#         self.violin_label_frequency_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onUpdate2D)
       
        violin_nLimit_label = wx.StaticText(panel, -1, "Violin limit:")
        self.violin_nLimit_value = wx.SpinCtrlDouble(panel, -1, 
                                                         value=str(self.config.violin_nlimit), 
                                                         min=1, max=200, 
                                                         initial=self.config.violin_nlimit, 
                                                         inc=5, size=(90, -1), name="shade")
        self.violin_nLimit_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
       
        grid = wx.GridBagSizer(2, 2)
        y = 0
        grid.Add(violin_orientation_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.violin_orientation_value, (y,1), flag=wx.EXPAND)
        y = y + 1
        grid.Add(violin_spacing_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.violin_spacing_value, (y,1), flag=wx.EXPAND)
        y = y + 1
        grid.Add(violin_min_percentage_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.violin_min_percentage_value, (y,1), flag=wx.EXPAND)
        y = y + 1
        grid.Add(violin_normalize_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.violin_normalize_check, (y,1), flag=wx.EXPAND)
        y = y + 1
        grid.Add(violin_lineWidth_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.violin_lineWidth_value, (y,1), flag=wx.EXPAND)
        y = y + 1
        grid.Add(violin_lineStyle_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.violin_lineStyle_value, (y,1), flag=wx.EXPAND)
        y = y + 1
        grid.Add(violin_lineColor_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.violin_colorLineBtn, (y,1), flag=wx.EXPAND)
        grid.Add(self.violin_line_sameAsShade_check, (y,2), flag=wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        grid.Add(violin_color_scheme_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.violin_colorScheme_value, (y,1), flag=wx.EXPAND)
        grid.Add(self.violin_colorScheme_msg, (y,2), (2,1),flag=wx.EXPAND)
        y = y + 1
        grid.Add(violin_colormap_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.violin_colormap_value, (y,1), flag=wx.EXPAND)
        y = y + 1
        grid.Add(violin_shadeColor_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.violin_colorShadeBtn, (y,1), flag=wx.EXPAND)
        y = y + 1
        grid.Add(violin_shadeTransparency_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.violin_shadeTransparency_value, (y,1), flag=wx.EXPAND)
        y = y + 1
        grid.Add(violin_label_frequency_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.violin_label_frequency_value, (y,1), flag=wx.EXPAND)
        y = y + 1
        grid.Add(violin_label_format_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.violin_label_format_value, (y,1), flag=wx.EXPAND)
        y = y + 1
        grid.Add(violin_nLimit_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.violin_nLimit_value, (y,1), flag=wx.EXPAND)


        # pack elements
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(grid, 0, wx.ALIGN_CENTER|wx.ALL, PANEL_SPACE_MAIN)
        
        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)
        
        return panel
        
    def makePanelWaterfall(self, panel):
        PANEL_SPACE_MAIN = 2
        
        # make elements
        waterfall_waterfallTgl_label = wx.StaticText(panel, -1, "Waterfall:")
        self.waterfallTgl = makeToggleBtn(panel, 'Off', wx.RED)
        self.waterfallTgl.SetValue(self.config.waterfall)
        self.waterfallTgl.Bind(wx.EVT_TOGGLEBUTTON, self.onEnableDisableFeatures_waterfall)
        
        waterfall_offset_label = wx.StaticText(panel, -1, "Offset:")
        self.waterfall_offset_value = wx.SpinCtrlDouble(panel, -1, 
                                                        value=str(self.config.waterfall_offset), 
                                                        min=0.0, max=1, initial=0, inc=0.05,
                                                        size=(90, -1))
        self.waterfall_offset_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        
        waterfall_increment_label = wx.StaticText(panel, -1, "Increment:")
        self.waterfall_increment_value = wx.SpinCtrlDouble(panel, -1, 
                                                        value=str(self.config.waterfall_increment), 
                                                        min=0.0, max=99999.0, initial=0, inc=0.1,
                                                        size=(90, -1), name="data")
        self.waterfall_increment_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        self.waterfall_increment_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onUpdate2D)
        
        waterfall_normalize_label = wx.StaticText(panel, -1, "Normalize:")
        self.waterfall_normalize_check = makeCheckbox(panel, u"")
        self.waterfall_normalize_check.SetValue(self.config.waterfall_normalize)
        self.waterfall_normalize_check.Bind(wx.EVT_CHECKBOX, self.onApply)

        waterfall_reverse_label = wx.StaticText(panel, -1, "Reverse order:")
        self.waterfall_reverse_check = makeCheckbox(panel, u"")
        self.waterfall_reverse_check.SetValue(self.config.waterfall_reverse)
        self.waterfall_reverse_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        
        waterfall_lineWidth_label = wx.StaticText(panel, -1, "Line width:")
        self.waterfall_lineWidth_value = wx.SpinCtrlDouble(panel, -1, 
                                                           value=str(self.config.waterfall_lineWidth), 
                                                           min=1, max=10, initial=self.config.waterfall_lineWidth, 
                                                           inc=1, size=(90, -1), name="style")
        self.waterfall_lineWidth_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        self.waterfall_lineWidth_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onUpdate2D)
        
        waterfall_lineStyle_label = wx.StaticText(panel, -1, "Line style:")
        self.waterfall_lineStyle_value= wx.Choice(panel, -1, choices=self.config.lineStylesList,
                                                  size=(-1, -1), name="style")
        self.waterfall_lineStyle_value.SetStringSelection(self.config.waterfall_lineStyle)
        self.waterfall_lineStyle_value.Bind(wx.EVT_CHOICE, self.onApply)
        self.waterfall_lineStyle_value.Bind(wx.EVT_CHOICE, self.onUpdate2D)

        waterfall_lineColor_label = wx.StaticText(panel, -1, "Line color:")
        self.waterfall_colorLineBtn = wx.Button(panel, ID_extraSettings_lineColour_waterfall,
                                                u"", wx.DefaultPosition, 
                                                wx.Size( 26, 26 ), 0, name="color")
        self.waterfall_colorLineBtn.SetBackgroundColour(convertRGB1to255(self.config.waterfall_color))
        self.waterfall_colorLineBtn.Bind(wx.EVT_BUTTON, self.onChangeColour)

        self.waterfall_line_sameAsShade_check = makeCheckbox(panel, u"Same as shade    ", name="color")
        self.waterfall_line_sameAsShade_check.SetValue(self.config.waterfall_line_sameAsShade)
        self.waterfall_line_sameAsShade_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        self.waterfall_line_sameAsShade_check.Bind(wx.EVT_CHECKBOX, self.onEnableDisableFeatures_waterfall)
        self.waterfall_line_sameAsShade_check.Bind(wx.EVT_CHECKBOX, self.onUpdate2D)
        
        waterfall_color_scheme_label = wx.StaticText(panel, -1, "Color scheme:")
        self.waterfall_colorScheme_value= wx.Choice(panel, -1, choices=self.config.waterfall_color_choices,
                                                    size=(-1, -1), name="color")
        self.waterfall_colorScheme_value.SetStringSelection(self.config.waterfall_color_value)
        self.waterfall_colorScheme_value.Bind(wx.EVT_CHOICE, self.onApply)
        self.waterfall_colorScheme_value.Bind(wx.EVT_CHOICE, self.onUpdate2D)
        self.waterfall_colorScheme_value.Bind(wx.EVT_CHOICE, self.onEnableDisableFeatures_waterfall)
        self.waterfall_colorScheme_msg = wx.StaticText(panel, -1, "")

        cmap_list = self.config.cmaps2[:]
        cmap_list.remove("jet")
        waterfall_colormap_label = wx.StaticText(panel, -1, "Colormap:")
        self.waterfall_colormap_value = wx.Choice(panel, -1, choices=cmap_list,
                                                 size=(-1, -1), name="color")
        self.waterfall_colormap_value.SetStringSelection(self.config.waterfall_colormap)
        self.waterfall_colormap_value.Bind(wx.EVT_CHOICE, self.onApply)
        self.waterfall_colormap_value.Bind(wx.EVT_CHOICE, self.onUpdate2D)
        
        waterfall_shade_under_label = wx.StaticText(panel, -1, "Shade under:")
        self.waterfall_shadeUnder_check = makeCheckbox(panel, u"", name="shade")
        self.waterfall_shadeUnder_check.SetValue(self.config.waterfall_shade_under)
        self.waterfall_shadeUnder_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        self.waterfall_shadeUnder_check.Bind(wx.EVT_CHECKBOX, self.onEnableDisableFeatures_waterfall)
        self.waterfall_shadeUnder_check.Bind(wx.EVT_CHECKBOX, self.onUpdate2D)
        
        waterfall_shadeColor_label = wx.StaticText(panel, -1, "Shade color:")
        self.waterfall_colorShadeBtn = wx.Button(panel, ID_extraSettings_shadeColour_waterfall,
                                                u"", wx.DefaultPosition, 
                                                wx.Size( 26, 26 ), 0, name="color")
        self.waterfall_colorShadeBtn.SetBackgroundColour(convertRGB1to255(self.config.waterfall_shade_under_color))
        self.waterfall_colorShadeBtn.Bind(wx.EVT_BUTTON, self.onChangeColour)
        
        waterfall_shadeTransparency_label = wx.StaticText(panel, -1, "Shade transparency:")
        self.waterfall_shadeTransparency_value = wx.SpinCtrlDouble(panel, -1, 
                                                                   value=str(self.config.waterfall_shade_under_transparency), 
                                                                   min=0, max=1, 
                                                                   initial=self.config.waterfall_shade_under_transparency, 
                                                                   inc=0.25, size=(90, -1), name="shade")
        self.waterfall_shadeTransparency_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        self.waterfall_shadeTransparency_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onUpdate2D)
        
        waterfall_shadeLimit_label = wx.StaticText(panel, -1, "Shade limit:")
        self.waterfall_shadeLimit_value = wx.SpinCtrlDouble(panel, -1, 
                                                                   value=str(self.config.waterfall_shade_under_nlimit), 
                                                                   min=0, max=100, 
                                                                   initial=self.config.waterfall_shade_under_nlimit, 
                                                                   inc=5, size=(90, -1), name="shade")
        self.waterfall_shadeLimit_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        
        waterfall_show_labels_label = wx.StaticText(panel, -1, "Show labels:")
        self.waterfall_showLabels_check = makeCheckbox(panel, u"", name="label")
        self.waterfall_showLabels_check.SetValue(self.config.waterfall_add_labels)
        self.waterfall_showLabels_check.Bind(wx.EVT_CHECKBOX, self.onEnableDisableFeatures_waterfall)
        
        waterfall_label_frequency_label = wx.StaticText(panel, -1, "Label frequency:")
        self.waterfall_label_frequency_value = wx.SpinCtrlDouble(panel, -1, 
                                                                 value=str(self.config.waterfall_labels_frequency), 
                                                                 min=0, max=100, 
                                                                 initial=self.config.waterfall_labels_frequency, 
                                                                 inc=1, size=(45, -1), name="label")
        self.waterfall_label_frequency_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        self.waterfall_label_frequency_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onUpdate2D)

        waterfall_label_format_label = wx.StaticText(panel, -1, "Label format:")
        self.waterfall_label_format_value= wx.Choice(panel, -1, choices=self.config.waterfall_label_format_choices,
                                                    size=(-1, -1), name="label")
        self.waterfall_label_format_value.SetStringSelection(self.config.waterfall_label_format)
        self.waterfall_label_format_value.Bind(wx.EVT_CHOICE, self.onApply)
        self.waterfall_label_format_value.Bind(wx.EVT_CHOICE, self.onUpdate2D)
        self.waterfall_label_format_value.Bind(wx.EVT_CHOICE, self.onEnableDisableFeatures_waterfall)

        waterfall_label_fontSize_label = wx.StaticText(panel, -1, "Font size:")
        self.waterfall_label_fontSize_value = wx.SpinCtrlDouble(panel, -1, 
                                                                   value=str(self.config.waterfall_label_fontSize), 
                                                                   min=0, max=32, 
                                                                   initial=self.config.waterfall_label_fontSize, 
                                                                   inc=4, size=(45, -1), name="label")
        self.waterfall_label_fontSize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        self.waterfall_label_fontSize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onUpdate2D)

        self.waterfall_label_fontWeight_check = makeCheckbox(panel, u"Bold", name="label")
        self.waterfall_label_fontWeight_check.SetValue(self.config.waterfall_label_fontWeight)
        self.waterfall_label_fontWeight_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        self.waterfall_label_fontWeight_check.Bind(wx.EVT_CHECKBOX, self.onUpdate2D)

        waterfall_label_x_offset_label = wx.StaticText(panel, -1, "Horizontal offset:")
        self.waterfall_label_x_offset_value = wx.SpinCtrlDouble(panel, -1, 
                                                                value=str(self.config.waterfall_labels_x_offset), 
                                                                min=0, max=1, 
                                                                initial=self.config.waterfall_labels_x_offset, 
                                                                inc=0.01, size=(45, -1), name="label")
        self.waterfall_label_x_offset_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        self.waterfall_label_x_offset_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onUpdate2D)
        
        waterfall_label_y_offset_label = wx.StaticText(panel, -1, "Vertical offset:")
        self.waterfall_label_y_offset_value = wx.SpinCtrlDouble(panel, -1, 
                                                                value=str(self.config.waterfall_labels_y_offset), 
                                                                min=0, max=1, 
                                                                initial=self.config.waterfall_labels_y_offset, 
                                                                inc=0.05, size=(45, -1), name="label")
        self.waterfall_label_y_offset_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        self.waterfall_label_y_offset_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onUpdate2D)
        

        grid = wx.GridBagSizer(2, 2)
        y = 0
        grid.Add(waterfall_waterfallTgl_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.waterfallTgl, (y,1), flag=wx.EXPAND)
        y = y + 1
        grid.Add(waterfall_offset_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.waterfall_offset_value, (y,1), flag=wx.EXPAND)
        y = y + 1
        grid.Add(waterfall_increment_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.waterfall_increment_value, (y,1), flag=wx.EXPAND)
        y = y + 1
        grid.Add(waterfall_normalize_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.waterfall_normalize_check, (y,1), flag=wx.EXPAND)
        y = y + 1
        grid.Add(waterfall_reverse_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.waterfall_reverse_check, (y,1), flag=wx.EXPAND)
        y = y + 1
        grid.Add(waterfall_lineWidth_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.waterfall_lineWidth_value, (y,1), flag=wx.EXPAND)
        y = y + 1
        grid.Add(waterfall_lineStyle_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.waterfall_lineStyle_value, (y,1), flag=wx.EXPAND)
        y = y + 1
        grid.Add(waterfall_lineColor_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.waterfall_colorLineBtn, (y,1), flag=wx.EXPAND)
        grid.Add(self.waterfall_line_sameAsShade_check, (y,2), flag=wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        grid.Add(waterfall_color_scheme_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.waterfall_colorScheme_value, (y,1), flag=wx.EXPAND)
        grid.Add(self.waterfall_colorScheme_msg, (y,2), (2,1), flag=wx.EXPAND)
        y = y + 1
        grid.Add(waterfall_colormap_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.waterfall_colormap_value, (y,1), flag=wx.EXPAND)
        y = y + 1
        grid.Add(waterfall_shade_under_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.waterfall_shadeUnder_check, (y,1), flag=wx.EXPAND)
        y = y + 1
        grid.Add(waterfall_shadeColor_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.waterfall_colorShadeBtn, (y,1), flag=wx.EXPAND)
        y = y + 1
        grid.Add(waterfall_shadeTransparency_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.waterfall_shadeTransparency_value, (y,1), flag=wx.EXPAND)
        y = y + 1
        grid.Add(waterfall_shadeLimit_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.waterfall_shadeLimit_value, (y,1), flag=wx.EXPAND)
        y = y + 1
        grid.Add(waterfall_show_labels_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.waterfall_showLabels_check, (y,1), flag=wx.EXPAND)
        y = y + 1
        grid.Add(waterfall_label_frequency_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.waterfall_label_frequency_value, (y,1), flag=wx.EXPAND)
        y = y + 1
        grid.Add(waterfall_label_format_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.waterfall_label_format_value, (y,1), flag=wx.EXPAND)
        y = y + 1
        grid.Add(waterfall_label_fontSize_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.waterfall_label_fontSize_value, (y,1), flag=wx.EXPAND)
        grid.Add(self.waterfall_label_fontWeight_check, (y,2), flag=wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        grid.Add(waterfall_label_x_offset_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.waterfall_label_x_offset_value, (y,1), flag=wx.EXPAND)   
        y = y + 1
        grid.Add(waterfall_label_y_offset_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.waterfall_label_y_offset_value, (y,1), flag=wx.EXPAND)        

#         y = y + 1
#         grid.Add(waterfall_useColormap_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
#         grid.Add(self.waterfall_useColormap_check, (y,1), flag=wx.EXPAND)

        # pack elements
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(grid, 0, wx.ALIGN_CENTER|wx.ALL, PANEL_SPACE_MAIN)
        
        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)
        
        return panel
        
    def makeColorbarPanel(self, panel):
        PANEL_SPACE_MAIN = 2
        
        """
        TODO:
        - add support for rotating colorbar
        - allow labels on the left hand side
        - add check function if vertical = left/right, if horizontal = top/bottom
        """
    
        # make elements
        cbar_colorbarTgl_label = wx.StaticText(panel, -1, "Colorbar:")
        self.colorbarTgl = makeToggleBtn(panel, 'Off', wx.RED, name="colorbar")
        self.colorbarTgl.SetValue(self.config.colorbar)
        self.colorbarTgl.Bind(wx.EVT_TOGGLEBUTTON, self.onEnableDisableFeatures_colorbar)
        self.colorbarTgl.Bind(wx.EVT_TOGGLEBUTTON, self.onUpdate2D)
        
        cbar_position_label = wx.StaticText(panel, -1, "Position:")
        self.colorbarPosition_value= wx.Choice(panel, -1, 
                                   choices=self.config.colorbarChoices,
                                   size=(-1, -1), name="colorbar")
        self.colorbarPosition_value.SetStringSelection(self.config.colorbarPosition)
        self.colorbarPosition_value.Bind(wx.EVT_CHOICE, self.onApply)
        self.colorbarPosition_value.Bind(wx.EVT_CHOICE, self.onUpdate2D)
        
        cbar_pad_label = wx.StaticText(panel, -1, "Distance:")
        self.colorbarPad_value = wx.SpinCtrlDouble(panel, -1, 
                                               value=str(self.config.colorbarPad), 
                                               min=0.0, max=2, initial=0, inc=0.05,
                                               size=(90, -1), name="colorbar")
        self.colorbarPad_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        self.colorbarPad_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onUpdate2D)
                
        cbar_width_label = wx.StaticText(panel, -1, "Width:")
        self.colorbarWidth_value = wx.SpinCtrlDouble(panel, -1, 
                                           value=str(self.config.colorbarWidth), 
                                           min=0.0, max=10, initial=0, inc=0.5, 
                                           size=(90, -1), name="colorbar")
        self.colorbarWidth_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        self.colorbarWidth_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onUpdate2D)
        
        cbar_fontsize = wx.StaticText(panel, -1, "Label font size:")
        self.colorbarFontsize_value = wx.SpinCtrlDouble(panel, -1, 
                                                        value=str(self.config.colorbarLabelSize), 
                                                        min=0, max=32, initial=0, inc=2, 
                                                        size=(90, -1), name="colorbar")
        self.colorbarFontsize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_2D)
        self.colorbarFontsize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onUpdate2D)

#         horizontal_line = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        
#         # Replot button
#         self.plotColorbarBtn = wx.Button(panel, wx.ID_ANY,
#                                          u"Plot", wx.DefaultPosition, 
#                                          wx.Size( -1, -1 ), 0)
#         self.plotColorbarBtn.Bind(wx.EVT_BUTTON, self.onReplot2D)

        grid = wx.GridBagSizer(2, 2)
        y = 0
        grid.Add(cbar_colorbarTgl_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.colorbarTgl, (y,1), flag=wx.EXPAND)
        y = y+1
        grid.Add(cbar_position_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.colorbarPosition_value, (y,1), flag=wx.EXPAND)
        y = y+1
        grid.Add(cbar_pad_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.colorbarPad_value, (y,1), flag=wx.EXPAND)
        y = y+1
        grid.Add(cbar_width_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.colorbarWidth_value, (y,1), flag=wx.EXPAND)
        y = y+1
        grid.Add(cbar_fontsize, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.colorbarFontsize_value, (y,1), flag=wx.EXPAND)
#         y = y+1
#         grid.Add(horizontal_line, (y,0), wx.GBSpan(1,3), flag=wx.EXPAND)
#         y = y+1
#         grid.Add(self.plotColorbarBtn, (y,1), flag=wx.ALIGN_CENTER_VERTICAL)
        
        # pack elements
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(grid, 0, wx.ALIGN_CENTER|wx.ALL, PANEL_SPACE_MAIN)
        
        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)
        
        return panel
        
    def makeLegendPanel(self, panel):
        PANEL_SPACE_MAIN = 2
        
        # make elements
        legend_legendTgl_label = wx.StaticText(panel, -1, "Legend:")
        self.legendTgl = makeToggleBtn(panel, 'Off', wx.RED)
        self.legendTgl.SetValue(self.config.legend)
        self.legendTgl.Bind(wx.EVT_TOGGLEBUTTON, self.onEnableDisableFeatures_legend)
        
        legend_position_label = wx.StaticText(panel, -1, "Position:")
        self.legend_position_value= wx.Choice(panel, -1, 
                                              choices=self.config.legendPositionChoice,
                                              size=(-1, -1))
        self.legend_position_value.SetStringSelection(self.config.legendPosition)
        self.legend_position_value.Bind(wx.EVT_CHOICE, self.onApply)
        
        legend_columns_label = wx.StaticText(panel, -1, "Columns:")
        self.legend_columns_value = wx.SpinCtrlDouble(panel, -1, 
                                                      value=str(self.config.legendColumns), 
                                                      min=1, max=5, initial=0, inc=1,
                                                      size=(90, -1))
        self.legend_columns_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        
        legend_fontSize_label = wx.StaticText(panel, -1, "Font size:")
        self.legend_fontSize_value= wx.Choice(panel, -1, 
                                   choices=self.config.legendFontChoice,
                                   size=(-1, -1))
        self.legend_fontSize_value.SetStringSelection(self.config.legendFontSize)
        self.legend_fontSize_value.Bind(wx.EVT_CHOICE, self.onApply)
        
        legend_markerSize_label = wx.StaticText(panel, -1, "Marker size:")
        self.legend_markerSize_value = wx.SpinCtrlDouble(panel, -1, 
                                               value=str(self.config.legendMarkerSize), 
                                               min=0.5, max=5, initial=0, inc=0.5,
                                               size=(90, -1))
        self.legend_markerSize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        
        legend_markerNumber_label = wx.StaticText(panel, -1, "Number of points:")
        self.legend_numberMarkers_value = wx.SpinCtrlDouble(panel, -1, 
                                               value=str(self.config.legendNumberMarkers), 
                                               min=1, max=10, initial=1, inc=1,
                                               size=(90, -1))
        self.legend_numberMarkers_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        
        legend_markerFirst_label = wx.StaticText(panel, -1, "Marker before label:")
        self.legend_markerFirst_check = makeCheckbox(panel, u"")
        self.legend_markerFirst_check.SetValue(self.config.legendMarkerFirst)
        self.legend_markerFirst_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        
        legend_alpha_label = wx.StaticText(panel, -1, "Frame transparency:")
        self.legend_alpha_value = wx.SpinCtrlDouble(panel, -1, 
                                               value=str(self.config.legendAlpha), 
                                               min=0.0, max=1, initial=0, inc=0.05,
                                               size=(90, -1))
        self.legend_alpha_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        
        legend_patch_alpha_label = wx.StaticText(panel, -1, "Patch transparency:")
        self.legend_patch_alpha_value = wx.SpinCtrlDouble(panel, -1, 
                                               value=str(self.config.legendPatchAlpha), 
                                               min=0.0, max=1, initial=0, inc=0.25,
                                               size=(90, -1))
        self.legend_patch_alpha_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        
        legend_frame_label = wx.StaticText(panel, -1, "Frame:")
        self.legend_frame_check = makeCheckbox(panel, u"")
        self.legend_frame_check.SetValue(self.config.legendFrame)
        self.legend_frame_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        
        legend_fancy_label = wx.StaticText(panel, -1, "Rounded corners:")
        self.legend_fancyBox_check = makeCheckbox(panel, u"")
        self.legend_fancyBox_check.SetValue(self.config.legendFancyBox)
        self.legend_fancyBox_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        
        
        grid = wx.GridBagSizer(2, 2)
        y = 0
        grid.Add(legend_legendTgl_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.legendTgl, (y,1), flag=wx.EXPAND)
        y = y+1
        grid.Add(legend_position_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.legend_position_value, (y,1), flag=wx.EXPAND)
        y = y+1
        grid.Add(legend_columns_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.legend_columns_value, (y,1), flag=wx.EXPAND)
        y = y+1
        grid.Add(legend_fontSize_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.legend_fontSize_value, (y,1), flag=wx.EXPAND)
        y = y+1
        grid.Add(legend_markerSize_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.legend_markerSize_value, (y,1), flag=wx.EXPAND)
        y = y+1
        grid.Add(legend_markerNumber_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.legend_numberMarkers_value, (y,1), flag=wx.EXPAND)
        y = y+1
        grid.Add(legend_markerFirst_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.legend_markerFirst_check, (y,1), flag=wx.EXPAND)
        y = y+1
        grid.Add(legend_alpha_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.legend_alpha_value, (y,1), flag=wx.EXPAND)
        y = y+1
        grid.Add(legend_patch_alpha_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.legend_patch_alpha_value, (y,1), flag=wx.EXPAND)
        y = y+1
        grid.Add(legend_frame_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.legend_frame_check, (y,1), flag=wx.EXPAND)
        y = y+1
        grid.Add(legend_fancy_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.legend_fancyBox_check, (y,1), flag=wx.EXPAND)
        
        # pack elements
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(grid, 0, wx.ALIGN_CENTER|wx.ALL, PANEL_SPACE_MAIN)
        
        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)
        
        return panel

    def make1DparametersPanel(self, panel):
        PANEL_SPACE_MAIN = 2
        
        # make elements
        lineParameters_staticBox = makeStaticBox(panel, "Line parameters", 
                                                 size=(-1, -1), color=wx.BLACK)
        lineParameters_staticBox.SetSize((-1,-1))
        line_box_sizer = wx.StaticBoxSizer(lineParameters_staticBox, wx.HORIZONTAL)
        
        plot1D_lineWidth_label = wx.StaticText(panel, -1, "Line width:")
        self.plot1D_lineWidth_value = wx.SpinCtrlDouble(panel, -1, 
                                               value=str(self.config.lineWidth_1D*10), 
                                               min=1, max=100, initial=self.config.lineWidth_1D*10, 
                                               inc=5, size=(90, -1))
        self.plot1D_lineWidth_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_1D)
        self.plot1D_lineWidth_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onUpdate1D)
        
        plot1D_lineColor_label = wx.StaticText(panel, -1, "Line color:")
        self.plot1D_colorLineBtn = wx.Button(panel, ID_extraSettings_lineColor_1D,
                                             u"", wx.DefaultPosition, 
                                             wx.Size( 26, 26 ), 0 )
        self.plot1D_colorLineBtn.SetBackgroundColour(convertRGB1to255(self.config.lineColour_1D))
        self.plot1D_colorLineBtn.Bind(wx.EVT_BUTTON, self.onChangeColour)
        
        plot1D_lineStyle_label = wx.StaticText(panel, -1, "Line style:")
        self.plot1D_lineStyle_value= wx.Choice(panel, -1, 
                                               choices=self.config.lineStylesList,
                                               size=(-1, -1))
        self.plot1D_lineStyle_value.SetStringSelection(self.config.lineStyle_1D)
        self.plot1D_lineStyle_value.Bind(wx.EVT_CHOICE, self.onApply_1D)
        self.plot1D_lineStyle_value.Bind(wx.EVT_CHOICE, self.onUpdate1D)
        
        plot1D_shade_label = wx.StaticText(panel, -1, "Shade under:")
        self.plot1D_shade_check = makeCheckbox(panel, u"")
        self.plot1D_shade_check.SetValue(self.config.lineShadeUnder_1D)
        self.plot1D_shade_check.Bind(wx.EVT_CHECKBOX, self.onApply_1D)
        self.plot1D_shade_check.Bind(wx.EVT_CHECKBOX, self.onEnableDisableFeatures_1D)
        self.plot1D_shade_check.Bind(wx.EVT_CHECKBOX, self.onUpdate1D)
        
        plot1D_shadeColor_label = wx.StaticText(panel, -1, "Shade under color:")
        self.plot1D_shadeUnderColorBtn = wx.Button(panel, ID_extraSettings_shadeUnderColor_1D,
                                             u"", wx.DefaultPosition, 
                                             wx.Size( 26, 26 ), 0 )
        self.plot1D_shadeUnderColorBtn.SetBackgroundColour(convertRGB1to255(self.config.lineShadeUnderColour_1D))
        self.plot1D_shadeUnderColorBtn.Bind(wx.EVT_BUTTON, self.onChangeColour)
        
        markerParameters_staticBox = makeStaticBox(panel, "Marker parameters", 
                                                 size=(-1, -1), color=wx.BLACK)
        markerParameters_staticBox.SetSize((-1,-1))
        marker_box_sizer = wx.StaticBoxSizer(markerParameters_staticBox, wx.HORIZONTAL)
        
        plot1D_markerShape_label = wx.StaticText(panel, -1, "Marker shape:")
        self.plot1D_markerShape_value= wx.Choice(panel, -1, 
                                   choices=self.config.markerShapeDict.keys(),
                                   size=(-1, -1))
        self.plot1D_markerShape_value.SetStringSelection(self.config.markerShapeTXT_1D)
        self.plot1D_markerShape_value.Bind(wx.EVT_CHOICE, self.onApply_1D)
        
        plot1D_markerSize_label = wx.StaticText(panel, -1, "Marker size:")
        self.plot1D_markerSize_value = wx.SpinCtrlDouble(panel, -1, 
                                               value=str(self.config.markerSize_1D), 
                                               min=1, max=100, initial=1, inc=5,
                                               size=(90, -1))
        self.plot1D_markerSize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_1D)
        
        plot1D_alpha_label = wx.StaticText(panel, -1, "Marker transparency:")
        self.plot1D_alpha_value = wx.SpinCtrlDouble(panel, -1, 
                                                    value=str(self.config.markerTransparency_1D*100), 
                                                    min=0, max=100, initial=self.config.markerTransparency_1D*100, 
                                                    inc=5, size=(90, -1))
        self.plot1D_alpha_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_1D)
        
        plot1D_markerColor_label = wx.StaticText(panel, -1, "Marker face color:")
        self.plot1D_colorAnnotBtn = wx.Button(panel, ID_extraSettings_markerColor_1D,
                                              u"", wx.DefaultPosition, 
                                              wx.Size( 26, 26 ), 0 )
        self.plot1D_colorAnnotBtn.SetBackgroundColour(convertRGB1to255(self.config.markerColor_1D))
        self.plot1D_colorAnnotBtn.Bind(wx.EVT_BUTTON, self.onChangeColour)

        plot1D_markerEdgeColor_label = wx.StaticText(panel, -1, "Marker edge color:")
        self.plot1D_colorEdgeAnnotBtn= wx.Button(panel, ID_extraSettings_edgeMarkerColor_1D,
                                                 u"", wx.DefaultPosition, 
                                                 wx.Size( 26, 26 ), 0 )
        self.plot1D_colorEdgeAnnotBtn.SetBackgroundColour(convertRGB1to255(self.config.markerEdgeColor_3D))
        self.plot1D_colorEdgeAnnotBtn.Bind(wx.EVT_BUTTON, self.onChangeColour)

        self.plot1D_colorEdgeMarker_check = makeCheckbox(panel, u"Same as fill")
        self.plot1D_colorEdgeMarker_check.SetValue(self.config.markerEdgeUseSame_1D)
        self.plot1D_colorEdgeMarker_check.Bind(wx.EVT_CHECKBOX, self.onApply_1D)
        self.plot1D_colorEdgeMarker_check.Bind(wx.EVT_CHECKBOX, self.onEnableDisableFeatures_1D)
        
        barParameters_staticBox = makeStaticBox(panel, "Bar parameters", 
                                                 size=(-1, -1), color=wx.BLACK)
        barParameters_staticBox.SetSize((-1,-1))
        bar_box_sizer = wx.StaticBoxSizer(barParameters_staticBox, wx.HORIZONTAL)
        
        bar_width_label = wx.StaticText(panel, -1, "Bar width:")
        self.bar_width_value = wx.SpinCtrlDouble(panel, -1, 
                                               value=str(self.config.bar_width), 
                                               min=0.01, max=10, inc=0.1,
                                               initial=self.config.bar_width, 
                                               size=(90, -1))
        self.bar_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_1D)

        bar_alpha_label = wx.StaticText(panel, -1, "Bar transparency:")
        self.bar_alpha_value = wx.SpinCtrlDouble(panel, -1, 
                                                    value=str(self.config.bar_alpha), 
                                                    min=0, max=1, initial=self.config.bar_alpha, 
                                                    inc=0.25, size=(90, -1))
        self.bar_alpha_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_1D)        

        bar_lineWidth_label = wx.StaticText(panel, -1, "Edge line width:")
        self.bar_lineWidth_value = wx.SpinCtrlDouble(panel, -1, 
                                                    value=str(self.config.bar_lineWidth), 
                                                    min=0, max=5, initial=self.config.bar_lineWidth, 
                                                    inc=1, size=(90, -1))
        self.bar_lineWidth_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_1D)        

        bar_edgeColor_label = wx.StaticText(panel, -1, "Edge color:")
        self.bar_edgeColorBtn = wx.Button(panel, ID_extraSettings_bar_edgeColor,
                                              u"", wx.DefaultPosition, 
                                              wx.Size( 26, 26 ), 0 )
        self.bar_edgeColorBtn.SetBackgroundColour(convertRGB1to255(self.config.bar_edge_color))
        self.bar_edgeColorBtn.Bind(wx.EVT_BUTTON, self.onChangeColour)

        self.bar_colorEdge_check = makeCheckbox(panel, u"Same as fill")
        self.bar_colorEdge_check.SetValue(self.config.bar_sameAsFill)
        self.bar_colorEdge_check.Bind(wx.EVT_CHECKBOX, self.onApply_1D)
        self.bar_colorEdge_check.Bind(wx.EVT_CHECKBOX, self.onEnableDisableFeatures_1D)
        
        horizontal_line = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        
        # Replot button
        self.update1DBtn = wx.Button( panel, wx.ID_ANY,
                                            u"Update", wx.DefaultPosition, 
                                            wx.Size( -1, -1 ), 0 )
        self.update1DBtn.Bind(wx.EVT_BUTTON, self.onUpdate1D)

        self.plot1DBtn = wx.Button( panel, wx.ID_ANY,
                                            u"Replot", wx.DefaultPosition, 
                                            wx.Size( -1, -1 ), 0 )
        self.plot1DBtn.Bind(wx.EVT_BUTTON, self.onReplot1D)

        line_grid = wx.GridBagSizer(2, 2)
        y = 0
        line_grid.Add(plot1D_lineWidth_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        line_grid.Add(self.plot1D_lineWidth_value, (y,1), wx.GBSpan(1,2), flag=wx.EXPAND)
        y = y+1
        line_grid.Add(plot1D_lineColor_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        line_grid.Add(self.plot1D_colorLineBtn, (y,1), wx.GBSpan(1,2), flag=wx.EXPAND)
        y = y+1
        line_grid.Add(plot1D_lineStyle_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        line_grid.Add(self.plot1D_lineStyle_value, (y,1), wx.GBSpan(1,2), flag=wx.EXPAND)
        y = y+1
        line_grid.Add(plot1D_shade_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        line_grid.Add(self.plot1D_shade_check, (y,1), wx.GBSpan(1,2), flag=wx.EXPAND)
        y = y+1
        line_grid.Add(plot1D_shadeColor_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        line_grid.Add(self.plot1D_shadeUnderColorBtn, (y,1), wx.GBSpan(1,2), flag=wx.EXPAND)
        line_box_sizer.Add(line_grid, 0, wx.EXPAND, 10)
        
        marker_grid = wx.GridBagSizer(2, 2)
        y = 0
        marker_grid.Add(plot1D_markerShape_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        marker_grid.Add(self.plot1D_markerShape_value, (y,1), wx.GBSpan(1,2), flag=wx.EXPAND)
        y = y+1
        marker_grid.Add(plot1D_markerSize_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        marker_grid.Add(self.plot1D_markerSize_value, (y,1), wx.GBSpan(1,2), flag=wx.EXPAND)
        y = y+1
        marker_grid.Add(plot1D_alpha_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        marker_grid.Add(self.plot1D_alpha_value, (y,1), wx.GBSpan(1,2), flag=wx.EXPAND)      
        y = y+1
        marker_grid.Add(plot1D_markerColor_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        marker_grid.Add(self.plot1D_colorAnnotBtn, (y,1), wx.GBSpan(1,2), flag=wx.EXPAND)
        y = y+1
        marker_grid.Add(plot1D_markerEdgeColor_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        marker_grid.Add(self.plot1D_colorEdgeAnnotBtn, (y,1), wx.GBSpan(1,2), flag=wx.EXPAND)
        marker_grid.Add(self.plot1D_colorEdgeMarker_check, (y,3), wx.GBSpan(1,2), flag=wx.EXPAND)
        marker_box_sizer.Add(marker_grid, 0, wx.EXPAND, 10)
        
        bar_grid = wx.GridBagSizer(2, 2)
        y = 0
        bar_grid.Add(bar_width_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        bar_grid.Add(self.bar_width_value, (y,1), wx.GBSpan(1,2), flag=wx.EXPAND)
        y = y+1
        bar_grid.Add(bar_alpha_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        bar_grid.Add(self.bar_alpha_value, (y,1), wx.GBSpan(1,2), flag=wx.EXPAND)
        y = y+1
        bar_grid.Add(bar_lineWidth_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        bar_grid.Add(self.bar_lineWidth_value, (y,1), wx.GBSpan(1,2), flag=wx.EXPAND)
        y = y+1
        bar_grid.Add(bar_edgeColor_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        bar_grid.Add(self.bar_edgeColorBtn, (y,1), wx.GBSpan(1,2), flag=wx.EXPAND)
        bar_grid.Add(self.bar_colorEdge_check, (y,3), wx.GBSpan(1,2), flag=wx.EXPAND)
        bar_box_sizer.Add(bar_grid, 0, wx.EXPAND, 10)
        
        grid = wx.GridBagSizer(2, 2)
        y = 0
        grid.Add(line_box_sizer, (y,0), wx.GBSpan(1,5), flag=wx.EXPAND)
        y = y+1
        grid.Add(marker_box_sizer, (y,0), wx.GBSpan(1,5), flag=wx.EXPAND)
        y = y+1
        grid.Add(bar_box_sizer, (y,0), wx.GBSpan(1,5), flag=wx.EXPAND)
        y = y+1
        grid.Add(horizontal_line, (y,0), wx.GBSpan(1,5), flag=wx.EXPAND)
        y = y+1
        grid.Add(self.update1DBtn, (y,0), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.plot1DBtn, (y,1), wx.GBSpan(1,2), flag=wx.ALIGN_CENTER_VERTICAL)
        
        # pack elements
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(grid, 0, wx.ALIGN_CENTER|wx.ALL, PANEL_SPACE_MAIN)
        
        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)
        
        return panel
    
    def make2DparametersPanel(self, panel):
        PANEL_SPACE_MAIN = 2
        
        # make elements 
        plot2D_staticBox = makeStaticBox(panel, "Plot 2D parameters", 
                                         size=(-1, -1), color=wx.BLACK)
        plot2D_staticBox.SetSize((-1,-1))
        plot2D_box_sizer = wx.StaticBoxSizer(plot2D_staticBox, wx.HORIZONTAL)    
        
        plot2D_colormap_label = wx.StaticText(panel, -1, "Colormap:")
        self.plot2D_colormap_value= wx.Choice(panel, -1, 
                                   choices=self.config.cmaps2,
                                   size=(-1, -1), name="color")
        self.plot2D_colormap_value.SetStringSelection(self.config.currentCmap)
        self.plot2D_colormap_value.Bind(wx.EVT_CHOICE, self.onApply_2D)
        self.plot2D_colormap_value.Bind(wx.EVT_CHOICE, self.onUpdate2D)

        self.plot2D_overrideColormap_check = makeCheckbox(panel, u"Override colormap")
        self.plot2D_overrideColormap_check.SetValue(self.config.useCurrentCmap)
        self.plot2D_overrideColormap_check.Bind(wx.EVT_CHECKBOX, self.onApply_2D)
        self.plot2D_overrideColormap_check.Bind(wx.EVT_CHOICE, self.onUpdate2D)
        
        plot2D_plotType_label = wx.StaticText(panel, -1, "Plot type:")
        self.plot2D_plotType_value= wx.Choice(panel, -1, 
                                              choices=self.config.imageType2D,
                                              size=(-1, -1))
        self.plot2D_plotType_value.SetStringSelection(self.config.plotType)
        self.plot2D_plotType_value.Bind(wx.EVT_CHOICE, self.onApply_2D)
        self.plot2D_plotType_value.Bind(wx.EVT_CHOICE, self.onReplot2D)
        
        plot2D_interpolation_label = wx.StaticText(panel, -1, "Interpolation:")
        self.plot2D_interpolation_value= wx.Choice(panel, -1, 
                                   choices=self.config.comboInterpSelectChoices,
                                   size=(-1, -1))
        self.plot2D_interpolation_value.SetStringSelection(self.config.interpolation)
        self.plot2D_interpolation_value.Bind(wx.EVT_CHOICE, self.onApply_2D)
        self.plot2D_interpolation_value.Bind(wx.EVT_CHOICE, self.onUpdate2D)
        
        plot2D_min_label = wx.StaticText(panel, -1, "Min %:")
        self.plot2D_min_value = wx.SpinCtrlDouble(panel, -1, 
                                               value=str(self.config.minCmap),min=0, max=100,
                                               initial=0, inc=5, size=(50, -1), name="normalization")
        self.plot2D_min_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_2D)
        self.plot2D_min_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onUpdate2D)
        
        plot2D_mid_label = wx.StaticText(panel, -1, "Mid %:")
        self.plot2D_mid_value = wx.SpinCtrlDouble(panel, -1, 
                                               value=str(self.config.midCmap),min=0, max=100,
                                               initial=0, inc=5, size=(50, -1), name="normalization")
        self.plot2D_mid_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_2D)
        self.plot2D_mid_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onUpdate2D)
        
        plot2D_max_label = wx.StaticText(panel, -1, "Max %:")
        self.plot2D_max_value = wx.SpinCtrlDouble(panel, -1, 
                                               value=str(self.config.maxCmap),min=0, max=100,
                                               initial=0, inc=5, size=(90, -1), name="normalization")
        self.plot2D_max_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_2D)
        self.plot2D_max_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onUpdate2D)
         
        horizontal_line = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
         
        # Replot button
        self.update2DBtn = wx.Button(panel, wx.ID_ANY, u"Update")
        self.update2DBtn.Bind(wx.EVT_BUTTON, self.onUpdate2D)
        
        self.plot2DBtn = wx.Button(panel, wx.ID_ANY, u"Replot")
        self.plot2DBtn.Bind(wx.EVT_BUTTON, self.onReplot2D)
 
        plot2D_grid = wx.GridBagSizer(2, 2)
        y = 0
        plot2D_grid.Add(plot2D_colormap_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        plot2D_grid.Add(self.plot2D_colormap_value, (y,1), wx.GBSpan(1,2), flag=wx.EXPAND)
        plot2D_grid.Add(self.plot2D_overrideColormap_check, (y,3), wx.GBSpan(1,4), flag=wx.EXPAND)
        y = y+1
        plot2D_grid.Add(plot2D_plotType_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        plot2D_grid.Add(self.plot2D_plotType_value, (y,1), wx.GBSpan(1,2), flag=wx.EXPAND)
        y = y+1
        plot2D_grid.Add(plot2D_interpolation_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        plot2D_grid.Add(self.plot2D_interpolation_value, (y,1), wx.GBSpan(1,2), flag=wx.EXPAND)
        y = y+1
        plot2D_grid.Add(plot2D_min_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        plot2D_grid.Add(self.plot2D_min_value, (y,1), wx.GBSpan(1,2), flag=wx.EXPAND)
        y = y+1
        plot2D_grid.Add(plot2D_mid_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        plot2D_grid.Add(self.plot2D_mid_value, (y,1), wx.GBSpan(1,2), flag=wx.EXPAND)
        y = y+1
        plot2D_grid.Add(plot2D_max_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        plot2D_grid.Add(self.plot2D_max_value, (y,1), wx.GBSpan(1,2), flag=wx.EXPAND)
        plot2D_box_sizer.Add(plot2D_grid, 0, wx.EXPAND, 10)
            
        grid = wx.GridBagSizer(2, 2)
        y = 0
        grid.Add(plot2D_box_sizer, (y,0), wx.GBSpan(1,8), flag=wx.EXPAND)
        y = y+1
        grid.Add(horizontal_line, (y,0), wx.GBSpan(1,8), flag=wx.EXPAND)
        y = y+1
        grid.Add(self.update2DBtn, (y,0), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.plot2DBtn, (y,1), wx.GBSpan(1,2), flag=wx.ALIGN_CENTER_VERTICAL)
        
        # pack elements
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(grid, 0, wx.ALIGN_CENTER|wx.ALL, PANEL_SPACE_MAIN)
        
        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)
        
        return panel

    def make3DparametersPanel(self, panel):
        PANEL_SPACE_MAIN = 2
        
        # make elements
        plot3D_staticBox = makeStaticBox(panel, "Plot 3D parameters", 
                                         size=(-1, -1), color=wx.BLACK)
        plot3D_staticBox.SetSize((-1,-1))
        plot3D_box_sizer = wx.StaticBoxSizer(plot3D_staticBox, wx.HORIZONTAL)  
        
        plot3D_plotType_label = wx.StaticText(panel, -1, "Plot type:")
        self.plot3D_plotType_value= wx.Choice(panel, -1, 
                                              choices=self.config.imageType3D,
                                              size=(-1, -1))
        self.plot3D_plotType_value.SetStringSelection(self.config.plotType_3D)
        self.plot3D_plotType_value.Bind(wx.EVT_CHOICE, self.onApply_3D)
        self.plot3D_plotType_value.Bind(wx.EVT_CHOICE, self.onReplot3D)
        
        scatter3D_staticBox = makeStaticBox(panel, "Scatter 3D parameters", 
                                         size=(-1, -1), color=wx.BLACK)
        scatter3D_staticBox.SetSize((-1,-1))
        scatter3D_box_sizer = wx.StaticBoxSizer(scatter3D_staticBox, wx.HORIZONTAL)  
        
        plot3D_markerShape_label = wx.StaticText(panel, -1, "Marker shape:")
        self.plot3D_markerShape_value= wx.Choice(panel, -1, 
                                   choices=self.config.markerShapeDict.keys(),
                                   size=(-1, -1))
        self.plot3D_markerShape_value.SetStringSelection(self.config.markerShapeTXT_3D)
        self.plot3D_markerShape_value.Bind(wx.EVT_CHOICE, self.onApply_3D)
         
        plot3D_markerSize_label = wx.StaticText(panel, -1, "Marker size:")
        self.plot3D_markerSize_value = wx.SpinCtrlDouble(panel, -1, 
                                               value=str(self.config.markerSize_3D), 
                                               min=1, max=200, initial=1, inc=5,
                                               size=(90, -1))
        self.plot3D_markerSize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_3D)
         
        plot3D_alpha_label = wx.StaticText(panel, -1, "Marker transparency:")
        self.plot3D_alpha_value = wx.SpinCtrlDouble(panel, -1, 
                                               value=str(self.config.markerTransparency_3D*100), 
                                               min=0, max=100, initial=self.config.markerTransparency_3D*100, 
                                               inc=5, size=(90, -1))
        self.plot3D_alpha_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_3D)
         
        plot3D_markerColor_label = wx.StaticText(panel, -1, "Marker fill color:")
        self.plot3D_colorAnnotBtn = wx.Button(panel, ID_extraSettings_markerColor_3D,
                                              u"", wx.DefaultPosition, 
                                              wx.Size( 26, 26 ), 0 )
        self.plot3D_colorAnnotBtn.SetBackgroundColour(convertRGB1to255(self.config.markerColor_3D))
        self.plot3D_colorAnnotBtn.Bind(wx.EVT_BUTTON, self.onChangeColour)

        plot3D_markerEdgeColor_label = wx.StaticText(panel, -1, "Marker edge color:")
        self.plot3D_colorEdgeAnnotBtn= wx.Button(panel, ID_extraSettings_edgeMarkerColor_3D,
                                                 u"", wx.DefaultPosition, 
                                                 wx.Size( 26, 26 ), 0 )
        self.plot3D_colorEdgeAnnotBtn.SetBackgroundColour(convertRGB1to255(self.config.markerEdgeColor_3D))
        self.plot3D_colorEdgeAnnotBtn.Bind(wx.EVT_BUTTON, self.onChangeColour)

        self.plot3D_colorEdgeMarker_check = makeCheckbox(panel, u"Same as fill")
        self.plot3D_colorEdgeMarker_check.SetValue(self.config.markerEdgeUseSame_3D)
        self.plot3D_colorEdgeMarker_check.Bind(wx.EVT_CHECKBOX, self.onApply_3D)
        self.plot3D_colorEdgeMarker_check.Bind(wx.EVT_CHECKBOX, self.onEnableDisableFeatures_3D)
        
        axisParameters_staticBox = makeStaticBox(panel, "Axis parameters", 
                                                 size=(-1, -1), color=wx.BLACK)
        axisParameters_staticBox.SetSize((-1,-1))
        axis_box_sizer = wx.StaticBoxSizer(axisParameters_staticBox, wx.HORIZONTAL)    

        plot3D_shadeOnOff_label = wx.StaticText(panel, -1, "Show shade:")
        self.plot3D_shadeOnOff_check = makeCheckbox(panel, u"")
        self.plot3D_shadeOnOff_check.SetValue(self.config.shade_3D)
        self.plot3D_shadeOnOff_check.Bind(wx.EVT_CHECKBOX, self.onApply_3D)
        self.plot3D_shadeOnOff_check.Bind(wx.EVT_CHECKBOX, self.onUpdate3D)
         
        plot3D_gridsOnOff_label = wx.StaticText(panel, -1, "Show grids:")
        self.plot3D_gridsOnOff_check = makeCheckbox(panel, u"")
        self.plot3D_gridsOnOff_check.SetValue(self.config.showGrids_3D)
        self.plot3D_gridsOnOff_check.Bind(wx.EVT_CHECKBOX, self.onApply_3D)
        self.plot3D_gridsOnOff_check.Bind(wx.EVT_CHECKBOX, self.onUpdate3D)
        
        plot3D_ticksOnOff_label = wx.StaticText(panel, -1, "Show ticks:")
        self.plot3D_ticksOnOff_check = makeCheckbox(panel, u"")
        self.plot3D_ticksOnOff_check.SetValue(self.config.ticks_3D)
        self.plot3D_ticksOnOff_check.Bind(wx.EVT_CHECKBOX, self.onApply_3D)
        self.plot3D_ticksOnOff_check.Bind(wx.EVT_CHECKBOX, self.onReplot3D)
         
        plot3D_spinesOnOff_label = wx.StaticText(panel, -1, "Show line:")
        self.plot3D_spinesOnOff_check = makeCheckbox(panel, u"")
        self.plot3D_spinesOnOff_check.SetValue(self.config.spines_3D)
        self.plot3D_spinesOnOff_check.Bind(wx.EVT_CHECKBOX, self.onApply_3D)
        self.plot3D_spinesOnOff_check.Bind(wx.EVT_CHECKBOX, self.onReplot3D)
        
        plot3D_labelsOnOff_label = wx.StaticText(panel, -1, "Show labels:")
        self.plot3D_labelsOnOff_check = makeCheckbox(panel, u"")
        self.plot3D_labelsOnOff_check.SetValue(self.config.labels_3D)
        self.plot3D_labelsOnOff_check.Bind(wx.EVT_CHECKBOX, self.onApply_3D)
        self.plot3D_labelsOnOff_check.Bind(wx.EVT_CHECKBOX, self.onUpdate3D)
        
        horizontal_line = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
         
        # Replot button
        self.update3DBtn = wx.Button( panel, wx.ID_ANY,
                                            u"Update", wx.DefaultPosition, 
                                            wx.Size( -1, -1 ), 0 )
        self.update3DBtn.Bind(wx.EVT_BUTTON, self.onUpdate3D)
         
        # Replot button
        self.plot3DBtn = wx.Button( panel, wx.ID_ANY,
                                            u"Replot", wx.DefaultPosition, 
                                            wx.Size( -1, -1 ), 0 )
        self.plot3DBtn.Bind(wx.EVT_BUTTON, self.onReplot3D)
 
        plot3D_grid = wx.GridBagSizer(2, 2)
        y = 0
        plot3D_grid.Add(plot3D_plotType_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        plot3D_grid.Add(self.plot3D_plotType_value, (y,1), wx.GBSpan(1,2), flag=wx.EXPAND)
        plot3D_box_sizer.Add(plot3D_grid, 0, wx.EXPAND, 10)
 
        scatter3D_grid = wx.GridBagSizer(2, 2)
        y = 0
        scatter3D_grid.Add(plot3D_markerShape_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        scatter3D_grid.Add(self.plot3D_markerShape_value, (y,1), wx.GBSpan(1,2), flag=wx.EXPAND)
        y = y+1
        scatter3D_grid.Add(plot3D_markerSize_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        scatter3D_grid.Add(self.plot3D_markerSize_value, (y,1), wx.GBSpan(1,2), flag=wx.EXPAND)
        y = y+1
        scatter3D_grid.Add(plot3D_alpha_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        scatter3D_grid.Add(self.plot3D_alpha_value, (y,1), wx.GBSpan(1,2), flag=wx.EXPAND)
        y = y+1
        scatter3D_grid.Add(plot3D_markerColor_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        scatter3D_grid.Add(self.plot3D_colorAnnotBtn, (y,1), wx.GBSpan(1,2), flag=wx.EXPAND)
        y = y+1
        scatter3D_grid.Add(plot3D_markerEdgeColor_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        scatter3D_grid.Add(self.plot3D_colorEdgeAnnotBtn, (y,1), wx.GBSpan(1,2), flag=wx.EXPAND)
        scatter3D_grid.Add(self.plot3D_colorEdgeMarker_check, (y,3), wx.GBSpan(1,3), flag=wx.EXPAND)
        scatter3D_box_sizer.Add(scatter3D_grid, 0, wx.EXPAND, 10)
        
        # axis grids
        axis_grid = wx.GridBagSizer(2, 2)
        y = 0
        axis_grid.Add(plot3D_shadeOnOff_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        axis_grid.Add(self.plot3D_shadeOnOff_check, (y,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        axis_grid.Add(plot3D_gridsOnOff_label, (y,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        axis_grid.Add(self.plot3D_gridsOnOff_check, (y,3), wx.GBSpan(1,1), flag=wx.EXPAND)
        axis_grid.Add(plot3D_ticksOnOff_label, (y,4), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        axis_grid.Add(self.plot3D_ticksOnOff_check, (y,5), wx.GBSpan(1,1), flag=wx.EXPAND)
        y = y+1
        axis_grid.Add(plot3D_spinesOnOff_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        axis_grid.Add(self.plot3D_spinesOnOff_check, (y,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        axis_grid.Add(plot3D_labelsOnOff_label, (y,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        axis_grid.Add(self.plot3D_labelsOnOff_check, (y,3), wx.GBSpan(1,1), flag=wx.EXPAND)
        axis_box_sizer.Add(axis_grid, 0, wx.EXPAND, 10)
        
        grid = wx.GridBagSizer(2, 2)
        y = 0
        grid.Add(plot3D_box_sizer, (y,0), wx.GBSpan(1,8), flag=wx.EXPAND)
        y = y+1
        grid.Add(scatter3D_box_sizer, (y,0), wx.GBSpan(1,8), flag=wx.EXPAND)
        y = y+1
        grid.Add(axis_box_sizer, (y,0), wx.GBSpan(1,8), flag=wx.EXPAND)
        y = y+1
        grid.Add(horizontal_line, (y,0), wx.GBSpan(1,8), flag=wx.EXPAND)
        y = y+1
        grid.Add(self.update3DBtn, (y,0), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.plot3DBtn, (y,1), wx.GBSpan(1,2), flag=wx.ALIGN_CENTER_VERTICAL)
        
        # pack elements
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(grid, 0, wx.ALIGN_CENTER|wx.ALL, PANEL_SPACE_MAIN)
        
        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)
        
        return panel

    def plot_update_size(self, plotName=None):
        dpi = wx.ScreenDC().GetPPI()
        resizeSize = self.config._plotSettings[plotName]['gui_size']
        figsizeNarrowPix = (int(resizeSize[0]*dpi[0]), int(resizeSize[1]*dpi[1]))
        
        if plotName == 'MS':
            resize_plot = self.presenter.view.panelPlots.plot1
        elif plotName == 'MS (compare)':
            resize_plot = self.presenter.view.panelPlots.plot1
        elif plotName == 'RT':
            resize_plot = self.presenter.view.panelPlots.plotRT
        elif plotName == 'DT':
            resize_plot = self.presenter.view.panelPlots.plot1D
        elif plotName == '2D':
            resize_plot = self.presenter.view.panelPlots.plot2D
        elif plotName == 'Waterfall':
            resize_plot = self.presenter.view.panelPlots.plotWaterfallIMS
        elif plotName == 'RMSD':
            resize_plot = self.presenter.view.panelPlots.plotRMSF
        elif plotName in ['Comparison', 'Matrix']:
            resize_plot = self.presenter.view.panelPlots.plotCompare
        elif plotName == 'DT/MS':
            resize_plot = self.presenter.view.panelPlots.plotMZDT
        elif plotName in ['Overlay', 'Overlay (Grid)']:
            resize_plot = self.presenter.view.panelPlots.plotOverlay
        elif plotName == 'Calibration (MS)':
            resize_plot = self.presenter.view.panelPlots.topPlotMS
        elif plotName == 'Calibration (DT)':
            resize_plot = self.presenter.view.panelPlots.bottomPlot1DT
        elif plotName == '3D':
            resize_plot = self.presenter.view.panelPlots.plot3D
        elif plotName == 'UniDec (MS)':
            resize_plot = self.presenter.view.panelPlots.plotUnidec_MS
        elif plotName == 'UniDec (MW)':
            resize_plot = self.presenter.view.panelPlots.plotUnidec_mwDistribution
        elif plotName == 'UniDec (m/z vs Charge)':
            resize_plot = self.presenter.view.panelPlots.plotUnidec_mzGrid
        elif plotName == 'UniDec (Isolated MS)':
            resize_plot = self.presenter.view.panelPlots.plotUnidec_individualPeaks
        elif plotName == 'UniDec (MW vs Charge)':
            resize_plot = self.presenter.view.panelPlots.plotUnidec_mwVsZ
        elif plotName == 'UniDec (Barplot)':
            resize_plot = self.presenter.view.panelPlots.plotUnidec_barChart
        elif plotName == 'UniDec (Charge Distribution)':
            resize_plot = self.presenter.view.panelPlots.plotUnidec_chargeDistribution            

        try:
            if resize_plot.lock_plot_from_updating: 
                msg = "This plot is locked and you cannot use global setting updated. \n" + \
                      "Please right-click in the plot area and select Customise plot..." + \
                      " to adjust plot settings."
                print(msg)
                return
            resize_plot.SetSize(figsizeNarrowPix)
        except (AttributeError, UnboundLocalError): 
            pass
    
    def onApply_1D(self, evt):
        # plot 1D
        self.config.lineWidth_1D = str2num(self.plot1D_lineWidth_value.GetValue())/10
        self.config.lineStyle_1D = self.plot1D_lineStyle_value.GetStringSelection()
        self.config.markerSize_1D = str2num(self.plot1D_markerSize_value.GetValue())
        self.config.lineShadeUnder_1D = self.plot1D_shade_check.GetValue()
        self.config.markerShapeTXT_1D = self.plot1D_markerShape_value.GetStringSelection()
        self.config.markerShape_1D = self.config.markerShapeDict[self.plot1D_markerShape_value.GetStringSelection()]
        self.config.markerTransparency_1D = str2num(self.plot1D_alpha_value.GetValue())/100
        
        self.config.tickFontSize_1D = str2num(self.plot1D_tickFontSize_value.GetValue())
        self.config.tickFontWeight_1D = self.plot1D_tickFontWeight_check.GetValue()
        self.config.labelFontSize_1D = str2num(self.plot1D_labelFontSize_value.GetValue())
        self.config.labelFontWeight_1D = self.plot1D_labelFontWeight_check.GetValue()
        self.config.titleFontSize_1D =  str2num(self.plot1D_titleFontSize_value.GetValue())
        self.config.titleFontWeight_1D =  self.plot1D_titleFontWeight_check.GetValue()
        self.config.annotationFontSize_1D =  str2num(self.plot1D_annotationFontSize_value.GetValue())
        self.config.annotationFontWeight_1D =  self.plot1D_annotationFontWeight_check.GetValue()
        self.config.axisOnOff_1D = self.plot1D_axisOnOff_check.GetValue()
        self.config.spines_left_1D = self.plot1D_leftSpines_check.GetValue()
        self.config.spines_right_1D = self.plot1D_rightSpines_check.GetValue()
        self.config.spines_top_1D = self.plot1D_topSpines_check.GetValue()
        self.config.spines_bottom_1D = self.plot1D_bottomSpines_check.GetValue()
        self.config.ticks_left_1D = self.plot1D_leftTicks_check.GetValue()
        self.config.ticks_right_1D = self.plot1D_rightTicks_check.GetValue()
        self.config.ticks_top_1D = self.plot1D_topTicks_check.GetValue()
        self.config.ticks_bottom_1D = self.plot1D_bottomTicks_check.GetValue()
        self.config.tickLabels_left_1D = self.plot1D_leftTickLabels_check.GetValue()
        self.config.tickLabels_right_1D = self.plot1D_rightTickLabels_check.GetValue()
        self.config.tickLabels_top_1D = self.plot1D_topTickLabels_check.GetValue()
        self.config.tickLabels_bottom_1D = self.plot1D_bottomTickLabels_check.GetValue()
        self.config.labelPad_1D = self.plot1D_padding_value.GetValue()
        self.config.frameWidth_1D = self.plot1D_frameWidth_value.GetValue()
        
        # bar
        self.config.bar_width = self.bar_width_value.GetValue()
        self.config.bar_alpha = self.bar_alpha_value.GetValue()
        self.config.bar_sameAsFill = self.bar_colorEdge_check.GetValue()
        self.config.bar_lineWidth = self.bar_lineWidth_value.GetValue()
        
        if self.config.autoSaveSettings:
            self.presenter.onExportConfig(evt=ID_saveConfig, verbose=False)
        
        if evt != None:
            evt.Skip()

    def onApply_2D(self, evt):
        self.config.currentCmap = self.plot2D_colormap_value.GetStringSelection()
        self.config.useCurrentCmap = self.plot2D_overrideColormap_check.GetValue()
        self.config.plotType = self.plot2D_plotType_value.GetStringSelection()
        self.config.interpolation = self.plot2D_interpolation_value.GetStringSelection()
        self.config.minCmap = str2num(self.plot2D_min_value.GetValue())
        self.config.midCmap = str2num(self.plot2D_mid_value.GetValue())
        self.config.maxCmap = str2num(self.plot2D_max_value.GetValue())

        # fire events
        self.onApply(evt=None)

        if self.config.autoSaveSettings:
            self.presenter.onExportConfig(evt=ID_saveConfig, verbose=False)

        if evt != None:
            evt.Skip()

    def onApply_3D(self, evt):
        self.config.plotType_3D = self.plot3D_plotType_value.GetStringSelection()
        self.config.showGrids_3D = self.plot3D_gridsOnOff_check.GetValue()
        self.config.shade_3D = self.plot3D_shadeOnOff_check.GetValue()
        self.config.ticks_3D = self.plot3D_ticksOnOff_check.GetValue()
        self.config.spines_3D = self.plot3D_spinesOnOff_check.GetValue()
        self.config.labels_3D = self.plot3D_labelsOnOff_check.GetValue()                
        self.config.markerTransparency_3D = str2num(self.plot3D_alpha_value.GetValue())/100
        self.config.markerShapeTXT_3D = self.plot3D_markerShape_value.GetStringSelection()
        self.config.markerShape_3D = self.config.markerShapeDict[self.plot3D_markerShape_value.GetStringSelection()]
        self.config.markerSize_3D = str2num(self.plot3D_markerSize_value.GetValue())
        self.config.markerEdgeUseSame_3D = self.plot3D_colorEdgeMarker_check.GetValue()
        if self.plot3D_colorEdgeMarker_check.GetValue():
            self.config.markerEdgeColor_3D = self.config.markerColor_3D

        if self.config.autoSaveSettings:
            self.presenter.onExportConfig(evt=ID_saveConfig, verbose=False)

        if evt != None:
            evt.Skip()

    def onApply_general(self, evt):
        # general
        plotName = self.general_plotName_value.GetStringSelection()
        plotValues = [self.general_left_value.GetValue(), self.general_bottom_value.GetValue(),
                      self.general_width_value.GetValue(), self.general_height_value.GetValue()] 
        self.config._plotSettings[plotName]['axes_size'] = plotValues
        
        plotSizes = [self.general_width_inch_value.GetValue(),
                     self.general_height_inch_value.GetValue()]
        self.config._plotSettings[plotName]['resize_size'] = plotSizes
        
        plotSizes = [self.general_width_window_inch_value.GetValue(),
                     self.general_height_window_inch_value.GetValue()]
        self.config._plotSettings[plotName]['gui_size'] = plotSizes
        
        # fire events
        self.presenter.plot_update_axes(plotName=plotName)
        
        self.plot_update_size(plotName=plotName)
        
        if self.config.autoSaveSettings:
            self.presenter.onExportConfig(evt=ID_saveConfig, verbose=False)
        
        if evt != None:
            evt.Skip()


    def onApply_zoom(self, evt):
        # plots
        self.config._plots_grid_show = self.zoom_grid_check.GetValue()
        self.config._plots_grid_line_width = self.zoom_cursor_lineWidth_value.GetValue()
        self.config._plots_extract_line_width = self.zoom_extract_lineWidth_value.GetValue()
        self.config._plots_zoom_line_width = self.zoom_zoom_lineWidth_value.GetValue()
        self.config._plots_zoom_crossover = self.zoom_sensitivity_value.GetValue()
        self.config._plots_extract_crossover_1D = self.zoom_extract_crossover1D_value.GetValue()
        self.config._plots_extract_crossover_2D = self.zoom_extract_crossover2D_value.GetValue()
        
        # fire events
        self.presenter.view.updatePlots(None)

        if self.config.autoSaveSettings:
            self.presenter.onExportConfig(evt=ID_saveConfig, verbose=False)
            
        if evt != None:
            evt.Skip()

    def onApply(self, evt):
        
        if self.importEvent: return
                
        # rmsd
        self.config.rmsd_position = self.rmsd_position_value.GetStringSelection()
        self.config.rmsd_fontSize = str2num(self.rmsd_fontSize_value.GetValue())
        self.config.rmsd_fontWeight = self.rmsd_fontWeight_check.GetValue()
        self.config.rmsd_rotation_X = str2num(self.rmsd_rotationX_value.GetValue())
        self.config.rmsd_rotation_Y = str2num(self.rmsd_rotationY_value.GetValue())
        self.config.rmsd_lineStyle = self.rmsd_lineStyle_value.GetStringSelection()
        self.config.rmsd_lineHatch = self.config.lineHatchDict[self.rmsd_lineHatch_value.GetStringSelection()]
        self.config.rmsd_underlineTransparency = str2num(self.rmsd_alpha_value.GetValue())/100
        self.config.rmsd_hspace = str2num(self.rmsd_hspace_value.GetValue())
        self.config.rmsd_matrix_add_labels = self.rmsd_add_labels_check.GetValue()

        # violin
        self.config.violin_orientation = self.violin_orientation_value.GetStringSelection()
        self.config.violin_min_percentage = str2num(self.violin_min_percentage_value.GetValue())
        self.config.violin_spacing = str2num(self.violin_spacing_value.GetValue())
        self.config.violin_lineWidth = self.violin_lineWidth_value.GetValue()
        self.config.violin_lineStyle = self.violin_lineStyle_value.GetStringSelection()
        self.config.violin_color_scheme = self.violin_colorScheme_value.GetStringSelection()
        if self.config.violin_color_scheme == "Color palette": self.violin_colorScheme_msg.SetLabel("You can change the color \npalette in the 'Extra' tab.")
        else: self.violin_colorScheme_msg.SetLabel("")
        self.config.violin_colormap = self.violin_colormap_value.GetStringSelection()
        self.config.violin_normalize = self.violin_normalize_check.GetValue()
        self.config.violin_line_sameAsShade = self.violin_line_sameAsShade_check.GetValue()
        self.config.violin_shade_under_transparency = self.violin_shadeTransparency_value.GetValue()
        self.config.violin_nlimit = self.violin_nLimit_value.GetValue()
        self.config.violin_label_format = self.violin_label_format_value.GetStringSelection()
        self.config.violin_labels_frequency = self.violin_label_frequency_value.GetValue()
        
        # waterfall
        self.config.waterfall = self.waterfallTgl.GetValue()
        self.config.waterfall_offset = str2num(self.waterfall_offset_value.GetValue())
        self.config.waterfall_increment = self.waterfall_increment_value.GetValue()
        self.config.waterfall_lineWidth = self.waterfall_lineWidth_value.GetValue()
        self.config.waterfall_lineStyle = self.waterfall_lineStyle_value.GetStringSelection()
        self.config.waterfall_reverse = self.waterfall_reverse_check.GetValue()
        self.config.waterfall_color_value = self.waterfall_colorScheme_value.GetStringSelection()
        if self.config.waterfall_color_value == "Color palette": self.waterfall_colorScheme_msg.SetLabel("You can change the color \npalette in the 'Extra' tab.")
        else: self.waterfall_colorScheme_msg.SetLabel("")
        self.config.waterfall_colormap = self.waterfall_colormap_value.GetStringSelection()
        self.config.waterfall_normalize = self.waterfall_normalize_check.GetValue()
        self.config.waterfall_line_sameAsShade = self.waterfall_line_sameAsShade_check.GetValue()
        self.config.waterfall_add_labels = self.waterfall_showLabels_check.GetValue()
        self.config.waterfall_labels_frequency = self.waterfall_label_frequency_value.GetValue()
        self.config.waterfall_labels_x_offset = self.waterfall_label_x_offset_value.GetValue()
        self.config.waterfall_labels_y_offset = self.waterfall_label_y_offset_value.GetValue()
        self.config.waterfall_label_fontSize = self.waterfall_label_fontSize_value.GetValue()
        self.config.waterfall_label_fontWeight = self.waterfall_label_fontWeight_check.GetValue()
        self.config.waterfall_shade_under = self.waterfall_shadeUnder_check.GetValue()
        self.config.waterfall_shade_under_transparency = self.waterfall_shadeTransparency_value.GetValue()
        self.config.waterfall_shade_under_nlimit = self.waterfall_shadeLimit_value.GetValue()
        self.config.waterfall_label_format = self.waterfall_label_format_value.GetStringSelection()
        
        # legend
        self.config.legend = self.legendTgl.GetValue()
        self.config.legendPosition = self.legend_position_value.GetStringSelection()
        self.config.legendColumns = str2int(self.legend_columns_value.GetValue())
        self.config.legendFontSize = self.legend_fontSize_value.GetStringSelection()
        self.config.legendFrame = self.legend_frame_check.GetValue()
        self.config.legendAlpha = str2num(self.legend_alpha_value.GetValue())
        self.config.legendMarkerSize = str2num(self.legend_markerSize_value.GetValue())
        self.config.legendNumberMarkers = str2int(self.legend_numberMarkers_value.GetValue())
        self.config.legendMarkerFirst = self.legend_markerFirst_check.GetValue()
        self.config.legendPatchAlpha = self.legend_patch_alpha_value.GetValue()
        self.config.legendFancyBox = self.legend_fancyBox_check.GetValue()
        
        # colorbar
        self.config.colorbar = self.colorbarTgl.GetValue()
        self.config.colorbarPosition = self.colorbarPosition_value.GetStringSelection()
        self.config.colorbarWidth = str2num(self.colorbarWidth_value.GetValue())
        self.config.colorbarPad = str2num(self.colorbarPad_value.GetValue())
        self.config.colorbarLabelSize = str2num(self.colorbarFontsize_value.GetValue())

        if self.config.autoSaveSettings:
            self.presenter.onExportConfig(evt=ID_saveConfig, verbose=False)

        if evt != None:
            evt.Skip()
        
    def onChangeColour(self, evt):
        
        evtID = evt.GetId()
        
        # Restore custom colors
        custom = wx.ColourData()
        for key in range(len(self.config.customColors)): #key in self.config.customColors:
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
        else:
            return
        
        if evtID == ID_extraSettings_labelColor_rmsd:
            self.config.rmsd_color = convertRGB255to1(newColour)
            self.rmsd_colorBtn.SetBackgroundColour(newColour)
            self.onUpdateLabel(None)
            
        elif evtID == ID_extraSettings_lineColor_rmsd:
            self.config.rmsd_lineColour = convertRGB255to1(newColour)
            self.rmsd_colorLineBtn.SetBackgroundColour(newColour)
            
        elif evtID == ID_extraSettings_underlineColor_rmsd:
            self.config.rmsd_underlineColor = convertRGB255to1(newColour)
            self.rmsd_undercolorLineBtn.SetBackgroundColour(newColour)
            
        elif evtID == ID_extraSettings_markerColor_1D:
            self.config.markerColor_1D = convertRGB255to1(newColour)
            self.plot1D_colorAnnotBtn.SetBackgroundColour(newColour)
            
        elif evtID == ID_extraSettings_edgeMarkerColor_1D:
            self.config.markerEdgeColor_1D = convertRGB255to1(newColour)
            self.plot1D_colorEdgeAnnotBtn.SetBackgroundColour(newColour)
            
        elif evtID == ID_extraSettings_markerColor_3D:
            self.config.markerColor_3D = convertRGB255to1(newColour)
            self.plot3D_colorAnnotBtn.SetBackgroundColour(newColour)
            
        elif evtID == ID_extraSettings_edgeMarkerColor_3D:
            self.config.markerEdgeColor_3D = convertRGB255to1(newColour)
            self.plot3D_colorEdgeAnnotBtn.SetBackgroundColour(newColour)
            
        elif evtID == ID_extraSettings_lineColor_1D:
            self.config.lineColour_1D = convertRGB255to1(newColour)
            self.plot1D_colorLineBtn.SetBackgroundColour(newColour)
            
        elif evtID == ID_extraSettings_zoomCursorColor:
            self.config._plots_grid_color = convertRGB255to1(newColour)
            self.zoom_cursor_colorBtn.SetBackgroundColour(newColour)

        elif evtID == ID_extraSettings_extractColor:
            self.config._plots_extract_color = convertRGB255to1(newColour)
            self.zoom_extract_colorBtn.SetBackgroundColour(newColour)
            
        elif evtID == ID_extraSettings_boxColor:
            self.config._plots_zoom_box_color = convertRGB255to1(newColour)
            self.zoom_zoom_box_colorBtn.SetBackgroundColour(newColour)
            
        elif evtID == ID_extraSettings_verticalColor:
            self.config._plots_zoom_vertical_color = convertRGB255to1(newColour)
            self.zoom_zoom_vertical_colorBtn.SetBackgroundColour(newColour)
            
        elif evtID == ID_extraSettings_horizontalColor:
            self.config._plots_zoom_horizontal_color = convertRGB255to1(newColour)
            self.zoom_zoom_horizontal_colorBtn.SetBackgroundColour(newColour)

        elif evtID == ID_extraSettings_lineColour_waterfall:
            self.config.waterfall_color = convertRGB255to1(newColour)
            self.waterfall_colorLineBtn.SetBackgroundColour(newColour)
            self.onUpdate2D(evt)
            
        elif evtID == ID_extraSettings_shadeColour_waterfall:
            self.config.waterfall_shade_under_color = convertRGB255to1(newColour)
            self.waterfall_colorShadeBtn.SetBackgroundColour(newColour)
            self.onUpdate2D(evt)
            
        elif evtID == ID_extraSettings_lineColour_violin:
            self.config.violin_color = convertRGB255to1(newColour)
            self.violin_colorLineBtn.SetBackgroundColour(newColour)
            self.onUpdate2D(evt)
            
        elif evtID == ID_extraSettings_shadeColour_violin:
            self.config.violin_shade_under_color = convertRGB255to1(newColour)
            self.violin_colorShadeBtn.SetBackgroundColour(newColour)
            self.onUpdate2D(evt)
            
        elif evtID == ID_extraSettings_shadeUnderColor_1D:
            self.config.lineShadeUnderColour_1D = convertRGB255to1(newColour)
            self.plot1D_shadeUnderColorBtn.SetBackgroundColour(newColour)
            
        elif evtID == ID_extraSettings_bar_edgeColor:
            self.config.bar_edge_color = convertRGB255to1(newColour)
            self.bar_edgeColorBtn.SetBackgroundColour(newColour)
            
        if self.config.autoSaveSettings:
            self.presenter.onExportConfig(evt=ID_saveConfig, verbose=False)
            
        try: 
            self.presenter.view.updatePlots(None)
        except: 
            pass
               
    def onSetupRMSDPosition(self, evt):
        self.config.rmsd_position = self.rmsd_position_value.GetStringSelection()
        if self.config.rmsd_position == 'bottom left':
            self.config.rmsd_location = (5, 5)
        elif self.config.rmsd_position == 'bottom right':
            self.config.rmsd_location = (75, 5)
        elif self.config.rmsd_position == 'top left':
            self.config.rmsd_location = (5, 95)
        elif self.config.rmsd_position == 'top right':
            self.config.rmsd_location = (75, 95)
        elif self.config.rmsd_position == 'other':
            self.config.rmsd_location = (str2int(self.rmsd_positionX_value.GetValue()),
                                         str2int(self.rmsd_positionY_value.GetValue()))

        self.rmsd_positionX_value.SetValue(self.config.rmsd_location[0])
        self.rmsd_positionY_value.SetValue(self.config.rmsd_location[1])

        if self.config.autoSaveSettings:
            self.presenter.onExportConfig(evt=ID_saveConfig, verbose=False)

        if evt != None:
            evt.Skip()
                 
    def onUpdateLabel(self, evt):      
        self.onApply(None)
        self.onSetupRMSDPosition(None)
        
        self.parent.panelPlots.plot_2D_update_label()
        
        if evt != None:
            evt.Skip()
            
    def onUpdateLabel_Matrix(self, evt):
        self.onApply(None)
        
        self.parent.panelPlots.plot_2D_matrix_update_label()
        
        if evt != None:
            evt.Skip()
              
    def onUpdate(self, evt):
        
        self.onApply_1D(None)
        if self.parent.panelPlots.currentPage in ["MS", "RT", "1D"]:
            if self.parent.panelPlots.window_plot1D == 'MS':
                self.parent.panelPlots.plot_1D_update(plotName="MS")
                
            elif self.parent.panelPlots.window_plot1D == 'RT':
                self.parent.panelPlots.plot_1D_update(plotName="RT")
                
            elif self.parent.panelPlots.window_plot1D == '1D':
                self.parent.panelPlots.plot_1D_update(plotName="1D")
        
        if self.parent.panelPlots.currentPage in ["2D", "DT/MS", "Waterfall"]:
            if self.parent.panelPlots.window_plot2D == '2D':
                self.parent.panelPlots.plot_2D_update(plotName="2D")
                
            elif self.parent.panelPlots.window_plot2D == 'DT/MS':
                self.parent.panelPlots.plot_2D_update(plotName="DT/MS")
                
            elif self.parent.panelPlots.window_plot2D == 'Waterfall':
                try: source = evt.GetEventObject().GetName()
                except: source = "axes"
                self.parent.panelPlots.plot_1D_waterfall_update(which=source)
            
        if self.parent.panelPlots.currentPage == 'Other':
            try: source = evt.GetEventObject().GetName()
            except: source = "axes"
            try: 
                if self.parent.panelPlots.plotOther.plot_type == "waterfall":
                    self.parent.panelPlots.plot_1D_waterfall_update(which=source)
            except: 
                pass  
                
        if self.parent.panelPlots.window_plot3D == '3D':
            self.presenter.plot_3D_update(plotName="3D")
            
        if evt != None:
            evt.Skip()
                     
    def onUpdate1D(self, evt):
        
        self.onApply_1D(None)
        if self.parent.panelPlots.window_plot1D == 'MS':
            self.parent.panelPlots.plot_1D_update(plotName="MS")
            
        elif self.parent.panelPlots.window_plot1D == 'RT':
            self.parent.panelPlots.plot_1D_update(plotName="RT")
            
        elif self.parent.panelPlots.window_plot1D == '1D':
            self.parent.panelPlots.plot_1D_update(plotName="1D")
            
        if evt != None:
            evt.Skip()
          
    def onUpdate2D(self, evt):
        
        self.onApply_1D(None)
        self.onApply_2D(None)
        try: source = evt.GetEventObject().GetName()
        except: source = "all"

        if self.parent.panelPlots.window_plot2D == '2D':
            if source == "colorbar":
                self.parent.panelPlots.plot_colorbar_update()
            elif source == 'normalization':
                self.parent.panelPlots.plot_normalization_update()
            else:
                self.parent.panelPlots.plot_2D_update(plotName="2D")
                
        elif self.parent.panelPlots.window_plot2D == 'RMSF':
            if source == "colorbar":
                self.parent.panelPlots.plot_colorbar_update()
            elif source == "rmsf":
                self.parent.panelPlots.plot_1D_update(plotName="RMSF")
                
        elif self.parent.panelPlots.window_plot2D == 'Comparison':
            self.parent.panelPlots.plot_colorbar_update()
            
        elif self.parent.panelPlots.window_plot2D == 'DT/MS':
            self.parent.panelPlots.plot_2D_update(plotName="DT/MS")
            
        elif self.parent.panelPlots.window_plot2D == 'UniDec':
            if source == "colorbar":
                self.parent.panelPlots.plot_colorbar_update()
            elif source == 'normalization':
                self.parent.panelPlots.plot_normalization_update()
            else:
                self.parent.panelPlots.plot_2D_update(plotName="UniDec")
                
        elif (self.parent.panelPlots.window_plot2D == 'Waterfall' or 
              self.parent.panelPlots.currentPage == "Other"):
            try: source = evt.GetEventObject().GetName()
            except: source = "color"
            self.onApply(None)
            self.parent.panelPlots.plot_1D_waterfall_update(which=source)
        
        if evt != None:
            evt.Skip()
            
    def onUpdate3D(self, evt):
        
        self.onApply_3D(None)
        if self.parent.panelPlots.window_plot3D == '3D':
            self.presenter.plot_3D_update(plotName="3D")
            
        if evt != None:
            evt.Skip()
                      
    def onReplot1D(self, evt):
        
        self.onApply_1D(None)
        if self.parent.panelPlots.window_plot1D == 'MS':
            self.parent.panelPlots.on_plot_MS(replot=True)
            
        elif self.parent.panelPlots.window_plot1D == 'RT':
            self.parent.panelPlots.on_plot_RT(replot=True)
            
        elif self.parent.panelPlots.window_plot1D == '1D':
            self.parent.panelPlots.on_plot_1D(replot=True)
            
        if evt != None:
            evt.Skip()
    
    def onReplot2D(self, evt):
        self.onApply_2D(None)
        if self.parent.panelPlots.window_plot2D == '2D':
            self.parent.panelPlots.on_plot_2D(replot=True)
            
        elif self.parent.panelPlots.window_plot2D == 'DT/MS':
            self.parent.panelPlots.on_plot_MSDT(replot=True)
            
        elif self.parent.panelPlots.window_plot2D == 'Comparison':
            self.parent.panelPlots.on_plot_matrix(replot=True)
            
        if evt != None:
            evt.Skip()
        
    def onReplot3D(self, evt):
        
        self.onApply_3D(None)
        if self.parent.panelPlots.window_plot3D == '3D':
            self.parent.panelPlots.on_plot_3D(replot=True)
            
        if evt != None:
            evt.Skip()
                
    def onEnableDisableFeatures_1D(self, evt):
            
        if not self.plot1D_colorEdgeMarker_check.GetValue():
            self.plot1D_colorEdgeAnnotBtn.Enable()
        else:
            self.plot1D_colorEdgeAnnotBtn.Disable()
            self.plot1D_colorEdgeAnnotBtn.SetBackgroundColour(self.plot1D_colorAnnotBtn.GetBackgroundColour())
            
        if not self.plot1D_shade_check.GetValue():
            self.plot1D_shadeUnderColorBtn.Disable()
        else:
            self.plot1D_shadeUnderColorBtn.Enable()
            
        if evt != None:
            evt.Skip()
        
    def onEnableDisableFeatures_2D(self, evt):
            
        if evt != None:
            evt.Skip()
        
    def onEnableDisableFeatures_3D(self, evt):

        if not self.plot3D_colorEdgeMarker_check.GetValue():
            self.plot3D_colorEdgeAnnotBtn.Enable()
        else:
            self.plot3D_colorEdgeAnnotBtn.Disable()
            self.plot3D_colorEdgeAnnotBtn.SetBackgroundColour(self.plot3D_colorAnnotBtn.GetBackgroundColour())
        
        if evt != None:
            evt.Skip()
        
    def onEnableDisableFeatures_colorbar(self, evt):        
        enableDisableList = [self.colorbarPosition_value,
                             self.colorbarWidth_value,
                             self.colorbarPad_value,
                             self.colorbarFontsize_value
                             ]

        self.config.colorbar = self.colorbarTgl.GetValue()
        if self.config.colorbar:
            self.colorbarTgl.SetLabel('On')
            self.colorbarTgl.SetForegroundColour(wx.WHITE)
            self.colorbarTgl.SetBackgroundColour(wx.BLUE)
            for item in enableDisableList: item.Enable()
        else:
            self.colorbarTgl.SetLabel('Off')
            self.colorbarTgl.SetForegroundColour(wx.WHITE)
            self.colorbarTgl.SetBackgroundColour(wx.RED)
            for item in enableDisableList: item.Disable()
        
        if evt != None:
            evt.Skip()

    def onEnableDisableFeatures_legend(self, evt):
        enableDisableList = [self.legend_position_value,
                             self.legend_columns_value,
                             self.legend_fontSize_value,
                             self.legend_markerSize_value,
                             self.legend_numberMarkers_value,
                             self.legend_markerFirst_check,
                             self.legend_alpha_value,
                             self.legend_patch_alpha_value,
                             self.legend_frame_check,
                             self.legend_fancyBox_check]
        
        self.config.legend = self.legendTgl.GetValue()
        if self.config.legend:
            self.legendTgl.SetLabel('On')
            self.legendTgl.SetForegroundColour(wx.WHITE)
            self.legendTgl.SetBackgroundColour(wx.BLUE)
            for item in enableDisableList: item.Enable()
        else:
            self.legendTgl.SetLabel('Off')
            self.legendTgl.SetForegroundColour(wx.WHITE)
            self.legendTgl.SetBackgroundColour(wx.RED)
            for item in enableDisableList: item.Disable()
            
        if evt != None:
            evt.Skip()
        
    def onEnableDisableFeatures_violin(self, evt):
        self.config.violin_line_sameAsShade = self.violin_line_sameAsShade_check.GetValue()
        if not self.config.violin_line_sameAsShade:
            self.violin_colorLineBtn.Enable()
        else: 
            self.violin_colorLineBtn.Disable()

        self.config.violin_color_value = self.violin_colorScheme_value.GetStringSelection()
        if self.config.violin_color_value == "Same color":
            self.violin_colormap_value.Disable()
        elif self.config.violin_color_value == "Colormap":
            self.violin_colormap_value.Enable()
        else:
            self.violin_colormap_value.Disable()

        
        if evt != None:
            evt.Skip()
        
    def onEnableDisableFeatures_waterfall(self, evt):
        
        enableDisableList = [self.waterfall_offset_value, self.waterfall_colorLineBtn,
                             self.waterfall_lineStyle_value, self.waterfall_lineWidth_value,
                             self.waterfall_offset_value, self.waterfall_increment_value,
                             self.waterfall_reverse_check, self.waterfall_colormap_value,
                             self.waterfall_label_fontSize_value, self.waterfall_label_fontWeight_check,
                             self.waterfall_label_frequency_value, self.waterfall_label_x_offset_value,
                             self.waterfall_showLabels_check, self.waterfall_shadeTransparency_value,
                             self.waterfall_shadeLimit_value, self.waterfall_shadeUnder_check,
                             self.waterfall_normalize_check, self.waterfall_colorScheme_value,
                             self.waterfall_line_sameAsShade_check,
                             
                             ]
        self.config.waterfall = self.waterfallTgl.GetValue()
        if self.config.waterfall:
            self.waterfallTgl.SetLabel('On')
            self.waterfallTgl.SetForegroundColour(wx.WHITE)
            self.waterfallTgl.SetBackgroundColour(wx.BLUE)
            for item in enableDisableList: item.Enable()
        else:
            self.waterfallTgl.SetLabel('Off')
            self.waterfallTgl.SetForegroundColour(wx.WHITE)
            self.waterfallTgl.SetBackgroundColour(wx.RED)
            for item in enableDisableList: item.Disable()
            
        self.config.waterfall_line_sameAsShade = self.waterfall_line_sameAsShade_check.GetValue()
        if not self.config.waterfall_line_sameAsShade and self.config.waterfall: 
            self.waterfall_colorLineBtn.Enable()
        else: 
            self.waterfall_colorLineBtn.Disable()
        
        self.config.waterfall_shade_under = self.waterfall_shadeUnder_check.GetValue()
        if self.config.waterfall_shade_under and self.config.waterfall: 
            self.waterfall_shadeTransparency_value.Enable()
            self.waterfall_shadeLimit_value.Enable()
        else: 
            self.waterfall_shadeTransparency_value.Disable()
            self.waterfall_shadeLimit_value.Disable()
        
        self.config.waterfall_add_labels = self.waterfall_showLabels_check.GetValue()
        labels_list = [self.waterfall_label_fontSize_value, self.waterfall_label_fontWeight_check,
                       self.waterfall_label_frequency_value, self.waterfall_label_x_offset_value]
        if self.config.waterfall_add_labels and self.config.waterfall: 
            for item in labels_list: item.Enable()
        else: 
            for item in labels_list: item.Disable()
        
        self.config.waterfall_color_value = self.waterfall_colorScheme_value.GetStringSelection()
        if self.config.waterfall_color_value == "Same color" and self.config.waterfall:
            self.waterfall_colormap_value.Disable()
        elif self.config.waterfall_color_value == "Colormap" and self.config.waterfall:
            self.waterfall_colormap_value.Enable()
        else:
            self.waterfall_colormap_value.Disable()

        
        if evt != None:
            evt.Skip()
        
    def onEnableDisableFeatures_rmsd(self, evt):
        
        enableDisableList = [self.rmsd_positionX_value, self.rmsd_positionY_value]
        self.config.rmsd_position = self.rmsd_position_value.GetStringSelection()
        if self.config.rmsd_position == 'other':
            for item in enableDisableList: item.Enable()
        else:
            for item in enableDisableList: item.Disable()
        
        if evt != None:
            evt.Skip()
        
    def onEnableDisableFeatures_general(self, evt):
        enableDisableList = [self.zoom_cursor_colorBtn, self.zoom_cursor_lineWidth_value]
        self.config._plots_grid_show = self.zoom_grid_check.GetValue()
        if self.config._plots_grid_show:
            for item in enableDisableList: item.Enable()
        else:
            for item in enableDisableList: item.Disable()
        
        if evt != None:
            evt.Skip()
        
    def onSetupPlotSizes(self, evt):
        
        # get current plot name
        plotName = self.general_plotName_value.GetStringSelection()
        
        # get axes sizes
        plotValues = self.config._plotSettings[plotName]
        
        # update axes sizes
        axSizes = plotValues['axes_size']
        for i, item in enumerate([self.general_left_value, self.general_bottom_value,
                                  self.general_width_value, self.general_height_value]):
            item.SetValue(axSizes[i])

        # update export axes sizes
        axSizes = plotValues['save_size']
        for i, item in enumerate([self.general_left_export_value, self.general_bottom_export_value,
                                  self.general_width_export_value, self.general_height_export_value]):
            item.SetValue(axSizes[i])
            
        # update plot sizes
        plotSizes = plotValues['resize_size']
        for i, item in enumerate([self.general_width_inch_value, 
                                  self.general_height_inch_value]):
            item.SetValue(plotSizes[i])

        plotSizes = plotValues['gui_size']
        for i, item in enumerate([self.general_width_window_inch_value, 
                                  self.general_height_window_inch_value]):
            item.SetValue(plotSizes[i])

            
        
        if evt != None:
            evt.Skip()
        
    def onChangePlotStyle(self, evt):
        self.config.currentStyle = self.general_style_value.GetStringSelection()
        self.presenter.view.panelPlots.onChangePlotStyle(evt=None)
        
        if self.config.autoSaveSettings:
            self.presenter.onExportConfig(evt=ID_saveConfig, verbose=False)
        
        if evt != None:
            evt.Skip()

    def onChangePalette(self, evt):
        self.config.currentPalette = self.general_palette_value.GetStringSelection()
        self.presenter.view.panelPlots.onChangePalette(evt=None)  

        if self.config.autoSaveSettings:
            self.presenter.onExportConfig(evt=ID_saveConfig, verbose=False)

        if evt != None:
            evt.Skip()
        
    def onUpdateGUI(self, evt):
        evtID = evt.GetId()
        
        self.config.quickDisplay = self.general_instantPlot_check.GetValue()
        self.config.threading = self.general_multiThreading_check.GetValue()
        self.config.logging = self.general_logToFile_check.GetValue()
        self.config.autoSaveSettings = self.general_autoSaveSettings_check.GetValue()
        
        if evtID == ID_extraSettings_instantPlot:
            if self.config.quickDisplay: msg = "Instant plotting was enabled"
            else: msg = "Instant plotting was disabled"
            # fire events
            self.presenter.view.panelDocuments.topP.documents.onNotUseQuickDisplay(evt=None)
            
        elif evtID == ID_extraSettings_multiThreading:
            if self.config.threading: msg = "Multi-threading was enabled"
            else: msg = "Multi-threading was disabled"
            # fire events
            self.presenter.view.onEnableDisableThreading(evt=None)
            
        elif evtID == ID_extraSettings_logging:
            if self.config.logging: 
                msg = "Logging events/warnings/errors to file in: %s" % self.config.loggingFile_path
            else: 
                msg = "Logging to file was disabled"
            # fire events
            self.presenter.view.onEnableDisableLogging(evt=None)
            
        elif evtID == ID_extraSettings_autoSaveSettings:
            if self.config.autoSaveSettings: msg = "Auto-saving of settings was enabled"
            else: msg = "Auto-saving of settings was disabled"
            
        self.presenter.onThreading(None, (msg, 4) , action='updateStatusbar')
        
        if self.config.autoSaveSettings:
            self.presenter.onExportConfig(evt=ID_saveConfig, verbose=False)
        
        if evt != None:
            evt.Skip()
        
        
        
        
        
        
        
        
        
        
        
        