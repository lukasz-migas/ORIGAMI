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
import wx

from toolbox import (str2num, str2int, convertRGB1to255, convertRGB255to1, num2str)
from styles import (makeCheckbox)

class panelCustomiseParameters(wx.Dialog):
    def __init__(self, parent, config, **kwargs):
        wx.Dialog.__init__(self, parent, -1, 'Other parameters...', size=(-1, -1),
                              style=wx.DEFAULT_FRAME_STYLE & ~
                              (wx.RESIZE_BORDER | wx.RESIZE_BOX | wx.MAXIMIZE_BOX))

        self.parent = parent
        self.config = config
        
        self.makeGUI()
        self.CentreOnParent()
        
        
    def onClose(self, evt):
        """Destroy this frame."""
        self.Destroy()
    # ----
    
    def onOK(self, evt):
        self.EndModal(wx.OK)
        
    def makeGUI(self):
        
        # make panel
        panel = self.makePanel()
        
        # pack element
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(panel, 0, wx.EXPAND, 50)
        
        # fit layout
        self.mainSizer.Fit(self)
        self.SetSizer(self.mainSizer)
        
    def makePanel(self):
        panel = wx.Panel(self, -1)
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        
        add_arrows_check = wx.StaticText(panel, -1, "Add arrows to labels:")
        self.add_arrows_check = makeCheckbox(panel, u"")
        self.add_arrows_check.SetValue(self.parent.add_arrows)
        self.add_arrows_check.Bind(wx.EVT_CHECKBOX, self.onApply)
         
        arrow_line_width = wx.StaticText(panel, -1, "Line width:")
        self.arrow_line_width_value = wx.SpinCtrlDouble(panel, -1,
                                                        value=str(self.config.annotation_arrow_line_width), 
                                                        min=0.005, max=2, 
                                                        initial=self.config.annotation_arrow_line_width, inc=0.25, 
                                                        size=(-1, -1))
        self.arrow_line_width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        
        
        arrow_line_style = wx.StaticText(panel, -1, "Line style:")
        self.arrow_line_style_value = wx.Choice(panel, -1, 
                                                choices=self.config.lineStylesList,
                                                size=(-1, -1))
        self.arrow_line_style_value.SetStringSelection(self.config.annotation_arrow_line_style)
        self.arrow_line_style_value.Bind(wx.EVT_CHOICE, self.onApply)
        
        # temporarily disable
        self.add_arrows_check.Disable()
        self.arrow_line_width_value.Disable()
        self.arrow_line_style_value.Disable()
        
         
        hz_line_1 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        
        label_fontSize_label = wx.StaticText(panel, -1, "Font size:")
        self.label_fontSize_value= wx.Choice(panel, -1, 
                                   choices=self.config.label_fontsize_list,
                                   size=(-1, -1))
        self.label_fontSize_value.SetStringSelection(self.config.annotation_label_font_size)
        self.label_fontSize_value.Bind(wx.EVT_CHOICE, self.onApply)
        
        label_fontWeight_label = wx.StaticText(panel, -1, "Font weight:")
        self.label_fontWeight_value= wx.Choice(panel, -1, 
                                   choices=self.config.label_fontweight_list,
                                   size=(-1, -1))
        self.label_fontWeight_value.SetStringSelection(self.config.annotation_label_font_weight)
        self.label_fontWeight_value.Bind(wx.EVT_CHOICE, self.onApply)
        
        label_horz_alignment = wx.StaticText(panel, -1, "Label horizontal alignment:")
        self.label_horz_alignment_value = wx.Choice(panel, -1, 
                                                    choices=self.config.horizontal_alignment_list,
                                                    size=(-1, -1))
        self.label_horz_alignment_value.SetStringSelection(self.config.annotation_label_horz)
        self.label_horz_alignment_value.Bind(wx.EVT_CHOICE, self.onApply)
        
        label_vert_alignment = wx.StaticText(panel, -1, "Label vertical alignment:")
        self.label_vert_alignment_value = wx.Choice(panel, -1, 
                                                    choices=self.config.vertical_alignment_list,
                                                    size=(-1, -1))
        self.label_vert_alignment_value.SetStringSelection(self.config.annotation_label_vert)
        self.label_vert_alignment_value.Bind(wx.EVT_CHOICE, self.onApply)
        
        hz_line_2 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        
        label_show_name = wx.StaticText(panel, -1, "Label structure:")
        
        label_show_fragment = wx.StaticText(panel, -1, "fragment:")
        self.label_show_fragment_check = makeCheckbox(panel, u"")
        self.label_show_fragment_check.SetValue(self.parent.label_format['fragment_name'])
        self.label_show_fragment_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        
        label_show_peptide = wx.StaticText(panel, -1, "sequence:")
        self.label_show_peptide_check = makeCheckbox(panel, u"")
        self.label_show_peptide_check.SetValue(self.parent.label_format['peptide_seq'])
        self.label_show_peptide_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        
        label_show_charge = wx.StaticText(panel, -1, "charge:")
        self.label_show_charge_check = makeCheckbox(panel, u"")
        self.label_show_charge_check.SetValue(self.parent.label_format['charge'])
        self.label_show_charge_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        
        label_show_error = wx.StaticText(panel, -1, u"Δ error:")
        self.label_show_error_check = makeCheckbox(panel, u"")
        self.label_show_error_check.SetValue(self.parent.label_format['delta_mz'])
        self.label_show_error_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        
        # temporarily disable
        self.label_show_fragment_check.Disable()
        self.label_show_peptide_check.Disable()
        self.label_show_charge_check.Disable()
        self.label_show_error_check.Disable()
        
        label_grid = wx.GridBagSizer(5, 5)
        y = 0
        label_grid.Add(label_show_fragment, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        label_grid.Add(self.label_show_fragment_check, (y,1), wx.GBSpan(1,1), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        label_grid.Add(label_show_peptide, (y,2), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        label_grid.Add(self.label_show_peptide_check, (y,3), wx.GBSpan(1,1), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        label_grid.Add(label_show_charge, (y,4), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        label_grid.Add(self.label_show_charge_check, (y,5), wx.GBSpan(1,1), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        label_grid.Add(label_show_error, (y,6), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        label_grid.Add(self.label_show_error_check, (y,7), wx.GBSpan(1,1), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        
        # pack elements
        grid = wx.GridBagSizer(5, 5)
        y = 0
        grid.Add(add_arrows_check, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.add_arrows_check, (y,1), wx.GBSpan(1,1), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        y = y+1
        grid.Add(arrow_line_width, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.arrow_line_width_value, (y,1), wx.GBSpan(1,1), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        y = y+1
        grid.Add(arrow_line_style, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.arrow_line_style_value, (y,1), wx.GBSpan(1,1), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        y = y+1        
        grid.Add(hz_line_1, (y,0), wx.GBSpan(1,3), flag=wx.EXPAND)
        y = y+1
        grid.Add(label_fontSize_label, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.label_fontSize_value, (y,1), wx.GBSpan(1,1), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        y = y+1
        grid.Add(label_fontWeight_label, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.label_fontWeight_value, (y,1), wx.GBSpan(1,1), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        y = y+1
        grid.Add(label_horz_alignment, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.label_horz_alignment_value, (y,1), wx.GBSpan(1,1), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        y = y+1
        grid.Add(label_vert_alignment, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.label_vert_alignment_value, (y,1), wx.GBSpan(1,1), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        y = y+1
        grid.Add(hz_line_2, (y,0), wx.GBSpan(1,3), flag=wx.EXPAND)
        y = y+1
        grid.Add(label_show_name, (y,0), wx.GBSpan(1,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
        y = y+1
        grid.Add(label_grid, (y,0), wx.GBSpan(1,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        mainSizer.Add(grid, 0, wx.EXPAND, 10)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizerAndFit(mainSizer)

        return panel
    
    def onApply(self, evt):
        self.config.annotation_label_font_size = self.label_fontSize_value.GetStringSelection()
        self.config.annotation_label_font_weight = self.label_fontWeight_value.GetStringSelection()
        self.config.annotation_label_vert = self.label_vert_alignment_value.GetStringSelection()
        self.config.annotation_label_horz = self.label_horz_alignment_value.GetStringSelection()
        self.config.annotation_arrow_line_width = self.arrow_line_width_value.GetValue()
        self.config.annotation_arrow_line_style = self.arrow_line_style_value.GetStringSelection()
        
        self.parent.add_arrows = self.add_arrows_check.GetValue() 
        
        _label_format = {'fragment_name':self.label_show_fragment_check.GetValue(), 
                         'peptide_seq':self.label_show_peptide_check.GetValue(), 
                         'charge':self.label_show_charge_check.GetValue(), 
                         'delta_mz':self.label_show_error_check.GetValue(), }

        self.parent.label_format = _label_format
        
        
        
        
        
        
        