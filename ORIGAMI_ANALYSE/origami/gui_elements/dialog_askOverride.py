# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
#    Copyright (C) 2017-2018 Lukasz G. Migas 
#    <lukasz.migas@manchester.ac.uk> OR <lukas.migas@yahoo.com>
# 
#     GitHub : https://github.com/lukasz-migas/ORIGAMI
#     University of Manchester IP : https://www.click2go.umip.com/i/s_w/ORIGAMI.html
#     Cite : 10.1016/j.ijms.2017.08.014
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
from styles import makeCheckbox

class dialogAskOverride(wx.Dialog):
    def __init__(self, parent, config, msg=None, **kwargs):
        wx.Dialog.__init__(self, parent, -1, 'Conflicting name', size=(-1, -1),
                           style=wx.DEFAULT_FRAME_STYLE & ~
                           (wx.RESIZE_BORDER | wx.RESIZE_BOX | wx.MAXIMIZE_BOX))
        
        self.parent = parent
        self.config = config
        self.makeGUI()
        self.CentreOnParent()
        
        if msg is None:
            msg = "Item already exists in the document. What would you like to do?"
        self.msg.SetValue(msg)
        
    def onClose(self, evt):
        """Destroy this frame."""
        self.Destroy()
    # ----
        
    def makeGUI(self):
        
        # make panel
        panel = self.makePanel()
        
        # pack element
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(panel, 0, wx.EXPAND, 10)
        
        # fit layout
        self.mainSizer.Fit(self)
        self.SetSizer(self.mainSizer)
        
    def makePanel(self):
        panel = wx.Panel(self, -1)
        
        self.msg = wx.TextCtrl(panel, -1, "", size=(400, 40),
                               style=wx.TE_READONLY|wx.TE_WORDWRAP)

        self.overrideBtn = wx.Button(panel, wx.ID_ANY, "Override", size=(-1, 22))
        self.overrideBtn.Bind(wx.EVT_BUTTON, self.override)
        
        self.mergeBtn = wx.Button(panel, wx.ID_ANY, "Merge", size=(-1, 22))
        self.mergeBtn.Bind(wx.EVT_BUTTON, self.merge)
        
        self.copyBtn = wx.Button(panel, wx.ID_OK, "Create copy", size=(-1, 22))
        self.copyBtn.Bind(wx.EVT_BUTTON, self.create_copy)
        
        self.askAgain_check = makeCheckbox(panel, "Don't ask again")
        self.askAgain_check.Bind(wx.EVT_CHECKBOX, self.onApply)  
    
        # pack elements
        grid = wx.GridBagSizer(5, 5)
        y = 0
        grid.Add(self.msg, (y,0), wx.GBSpan(1,4))
        y = y+1
        grid.Add(self.overrideBtn, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(self.mergeBtn, (y,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(self.copyBtn, (y,2), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(self.askAgain_check, (y,3), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
        
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(grid, 0, wx.EXPAND, 10)
        
        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizerAndFit(mainSizer)

        return panel
    
    def override(self, evt):
        self.config.import_duplicate_action = "override"
        self.EndModal(wx.OK)
        
    def merge(self, evt):
        self.config.import_duplicate_action = "merge"
        self.EndModal(wx.OK)
        
    def create_copy(self, evt):
        self.config.import_duplicate_action = "duplicate"
        self.EndModal(wx.OK)
    
    def onApply(self, evt):
        self.config.import_duplicate_ask = self.askAgain_check.GetValue()
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        