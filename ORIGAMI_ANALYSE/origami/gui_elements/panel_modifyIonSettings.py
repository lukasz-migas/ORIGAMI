import wx

from icons import IconContainer as icons
from styles import makeCheckbox, validator, makeStaticBox
from toolbox import num2str, str2int, str2num


class panelModifyIonSettings(wx.MiniFrame):
    """
    Small panel to modify settings in the Ion peaklist panel
    """
    
    def __init__(self, parent, presenter, config, **kwargs):
        wx.MiniFrame.__init__(self, parent,-1, 'Modify settings...', size=(-1, -1), 
                              style=wx.DEFAULT_FRAME_STYLE & ~wx.RESIZE_BORDER)
        
        self.parent = parent
        self.presenter = presenter
        self.config = config
        self.icons = icons()
        self.importEvent = False
                
        self.SetTitle("Ion: {}".format(kwargs['ionName']))
        self.itemInfo = kwargs
        
        # check values
        if self.itemInfo['mask'] in ['', None, 'None']:
            self.itemInfo['mask'] = self.config.overlay_defaultMask
            
        if self.itemInfo['alpha'] in ['', None, 'None']:
            self.itemInfo['alpha'] = self.config.overlay_defaultAlpha
            
        if self.itemInfo['colormap'] in ['', None, 'None']:
            self.itemInfo['colormap'] = self.config.currentCmap
            
        if self.itemInfo['color'][0] == -1:
              self.itemInfo['color'] = (1, 1, 1, 255)
                
        if self.itemInfo['charge'] in ['', None, 'None']:
            self.itemInfo['charge'] = 1
                
        # make gui items
        self.makeGUI()
        
        self.Centre()
        self.Layout()
        self.SetFocus()

        # bind
        wx.EVT_CLOSE(self, self.onClose)
        self.Bind(wx.EVT_CHAR_HOOK, self.OnKey)
        
        # fire-up events
        self.onSetupParameters(evt=None)
    # ----
    
    def OnKey(self, evt):
        keyCode = evt.GetKeyCode()
        if keyCode == wx.WXK_ESCAPE:
            self.onClose(evt=None)
        
        evt.Skip()
                
    def onClose(self, evt):
        """Destroy this frame."""
        self.Destroy()
    # ----
        
    def onSelect(self, evt):
        self.OnAssignColor(evt=None)
        self.parent.onUpdateDocument(itemInfo=self.itemInfo, evt=None)
        self.Destroy()
        
    def makeGUI(self):
        
        # make panel
        panel = self.makePanel()
        
        # pack element
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(panel, 1, wx.EXPAND, 0)
        
        # fit layout
        self.mainSizer.Fit(self)
        self.SetSizer(self.mainSizer)
        
    def makePanel(self):

        panel = wx.Panel(self, -1, size=(-1,-1))
        mainSizer = wx.BoxSizer(wx.VERTICAL)
                
        select_label = wx.StaticText(panel, wx.ID_ANY, u"Select:")
        self.origami_select_value = makeCheckbox(panel, u"")
        self.origami_select_value.Bind(wx.EVT_CHECKBOX, self.onApply)
        
        filename_label = wx.StaticText(panel, wx.ID_ANY, u"Filename:")
        self.origami_filename_value = wx.TextCtrl(panel, wx.ID_ANY, u"", style=wx.TE_READONLY)
        
        ion_label = wx.StaticText(panel, wx.ID_ANY, u"Ion:")
        self.origami_ion_value = wx.TextCtrl(panel, wx.ID_ANY, u"", style=wx.TE_READONLY)

        label_label = wx.StaticText(panel, wx.ID_ANY,
                                    u"Label:", wx.DefaultPosition, 
                                    wx.DefaultSize, wx.ALIGN_LEFT)
        self.origami_label_value = wx.TextCtrl(panel, -1, "", size=(90, -1))
        self.origami_label_value.SetValue(self.itemInfo['label'])
        self.origami_label_value.Bind(wx.EVT_TEXT, self.onApply)

        charge_label = wx.StaticText(panel, wx.ID_ANY, u"Charge:")
        self.origami_charge_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('intPos'))
        self.origami_charge_value.Bind(wx.EVT_TEXT, self.onApply)
        
        min_threshold_label = wx.StaticText(panel, wx.ID_ANY, u"Min threshold:")
        self.origami_min_threshold_value = wx.SpinCtrlDouble(panel, wx.ID_ANY,
                                            value="1",min=0.0, max=1.0,
                                            initial=1.0, inc=0.05, size=(60,-1))
        self.origami_min_threshold_value.SetValue(self.itemInfo['min_threshold'])
        self.origami_min_threshold_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)

        max_threshold_label = wx.StaticText(panel, wx.ID_ANY, u"Max threshold:")
        self.origami_max_threshold_value = wx.SpinCtrlDouble(panel, wx.ID_ANY,
                                            value="1",min=0.0, max=1.0,
                                            initial=1.0, inc=0.05, size=(60,-1))
        self.origami_max_threshold_value.SetValue(self.itemInfo['max_threshold'])
        self.origami_max_threshold_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        
        mask_label = wx.StaticText(panel, wx.ID_ANY, u"Mask:")
        self.origami_mask_value = wx.SpinCtrlDouble(panel, wx.ID_ANY,
                                            value="1",min=0.0, max=1.0,
                                            initial=1.0, inc=0.05, size=(60,-1))
        self.origami_mask_value.SetValue(self.itemInfo['mask'])
        self.origami_mask_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        
        transparency_label = wx.StaticText(panel, wx.ID_ANY, u"Transparency:")
        self.origami_transparency_value = wx.SpinCtrlDouble(panel, wx.ID_ANY,
                                                    value="1",min=0.0, max=1.0,
                                                    initial=1.0, inc=0.05, size=(60,-1))
        self.origami_transparency_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        
        colormap_label = wx.StaticText(panel, -1, "Colormap:")
        self.origami_colormap_value= wx.Choice(panel, -1, 
                                               choices=self.config.cmaps2,
                                               size=(-1, -1))
        self.origami_colormap_value.Bind(wx.EVT_CHOICE, self.onApply)
        
        self.origami_restrictColormap_value = makeCheckbox(panel, u"")
        self.origami_restrictColormap_value.Bind(wx.EVT_CHECKBOX, self.onRestrictCmaps)
        
        color_label = wx.StaticText(panel, -1, "Color:")
        self.origami_color_value = wx.Button(panel, wx.ID_ANY, u"", wx.DefaultPosition, 
                                     wx.Size( 26, 26 ), 0)
        self.origami_color_value.SetBackgroundColour(self.itemInfo['color'])
        self.origami_color_value.Bind(wx.EVT_BUTTON, self.OnAssignColor)

        origami_staticBox = makeStaticBox(panel, "Collision voltage parameters", size=(-1, -1), color=wx.BLACK)
        origami_staticBox.SetSize((-1,-1))
        origami_box_sizer = wx.StaticBoxSizer(origami_staticBox, wx.HORIZONTAL)   

        method_label = wx.StaticText(panel, -1, "Acquisition method:")
        self.origami_method_value= wx.Choice(panel, -1, 
                                             choices=self.config.origami_acquisition_choices,
                                             size=(-1, -1))
        self.origami_method_value.SetStringSelection(self.itemInfo['method'])
        self.origami_method_value.Bind(wx.EVT_CHOICE, self.enableDisableBoxes)
        self.origami_method_value.Bind(wx.EVT_CHOICE, self.onApply)
        
#         self.origami_loadParams = wx.BitmapButton(panel, wx.ID_ANY,
#                                                   self.icons.iconsLib['load16'],
#                                                   size=(26, 26),
#                                                   style=wx.BORDER_DOUBLE | wx.ALIGN_CENTER_VERTICAL)
                
        spv_label = wx.StaticText(panel, wx.ID_ANY, u"Scans per voltage:")
        self.origami_scansPerVoltage_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('intPos'))
        self.origami_scansPerVoltage_value.SetValue(str(self.config.origami_spv))
        self.origami_scansPerVoltage_value.Bind(wx.EVT_TEXT, self.onApply)
        
        scan_label = wx.StaticText(panel, wx.ID_ANY, u"First scan:")
        self.origami_startScan_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('intPos'))
        self.origami_startScan_value.Bind(wx.EVT_TEXT, self.onApply)
        
        startVoltage_label = wx.StaticText(panel, wx.ID_ANY, u"First voltage:")
        self.origami_startVoltage_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('floatPos'))
        self.origami_startVoltage_value.Bind(wx.EVT_TEXT, self.onApply)
        
        endVoltage_label = wx.StaticText(panel, wx.ID_ANY, u"Final voltage:")
        self.origami_endVoltage_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('floatPos'))
        self.origami_endVoltage_value.Bind(wx.EVT_TEXT, self.onApply)
        
        stepVoltage_label = wx.StaticText(panel, wx.ID_ANY, u"Voltage step:")
        self.origami_stepVoltage_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('floatPos'))
        self.origami_stepVoltage_value.Bind(wx.EVT_TEXT, self.onApply)
        
        boltzmann_label = wx.StaticText(panel, wx.ID_ANY, u"Boltzmann offset:")
        self.origami_boltzmannOffset_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                                         validator=validator('floatPos'))
        self.origami_boltzmannOffset_value.Bind(wx.EVT_TEXT, self.onApply)
        
        exponentialPercentage_label = wx.StaticText(panel, wx.ID_ANY, u"Exponential percentage:")
        self.origami_exponentialPercentage_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('floatPos'))
        self.origami_exponentialPercentage_value.Bind(wx.EVT_TEXT, self.onApply)
        
        exponentialIncrement_label = wx.StaticText(panel, wx.ID_ANY, u"Exponential increment:")
        self.origami_exponentialIncrement_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('floatPos'))
        self.origami_exponentialIncrement_value.Bind(wx.EVT_TEXT, self.onApply)
       
        origami_grid = wx.GridBagSizer(2, 2)
        n = 0
        origami_grid.Add(method_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        origami_grid.Add(self.origami_method_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
#         origami_grid.Add(self.origami_loadParams, (n,2), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT)
        n = n + 1
        origami_grid.Add(spv_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        origami_grid.Add(self.origami_scansPerVoltage_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        origami_grid.Add(scan_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        origami_grid.Add(self.origami_startScan_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        origami_grid.Add(startVoltage_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        origami_grid.Add(self.origami_startVoltage_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        origami_grid.Add(endVoltage_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        origami_grid.Add(self.origami_endVoltage_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        origami_grid.Add(stepVoltage_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        origami_grid.Add(self.origami_stepVoltage_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        origami_grid.Add(boltzmann_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        origami_grid.Add(self.origami_boltzmannOffset_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        origami_grid.Add(exponentialPercentage_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        origami_grid.Add(self.origami_exponentialPercentage_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        origami_grid.Add(exponentialIncrement_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        origami_grid.Add(self.origami_exponentialIncrement_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        origami_box_sizer.Add(origami_grid, 0, wx.EXPAND, 10)
        
        
        horizontal_line = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        self.applyBtn = wx.Button(panel, wx.ID_OK, "Apply", size=(-1, 22))
        self.previousBtn = wx.Button(panel, wx.ID_OK, "Previous", size=(-1, 22))
        self.nextBtn = wx.Button(panel, wx.ID_OK, "Next", size=(-1, 22))
        self.cancelBtn = wx.Button(panel, wx.ID_OK, "Close", size=(-1, 22))
        
        self.applyBtn.Bind(wx.EVT_BUTTON, self.onSelect)
        self.cancelBtn.Bind(wx.EVT_BUTTON, self.onClose)
        self.nextBtn.Bind(wx.EVT_BUTTON, self.onGetNext)
        self.previousBtn.Bind(wx.EVT_BUTTON, self.onGetPrevious)
        
        btn_grid = wx.GridBagSizer(2, 2)
        n = 0
        btn_grid.Add(self.applyBtn, (n,0), wx.GBSpan(1,1))
        btn_grid.Add(self.previousBtn, (n,1), wx.GBSpan(1,1))
        btn_grid.Add(self.nextBtn, (n,2), wx.GBSpan(1,1))
        btn_grid.Add(self.cancelBtn, (n,3), wx.GBSpan(1,1))
        
        # pack elements
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(select_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.origami_select_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(filename_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.origami_filename_value, (n,1), wx.GBSpan(1,2), flag=wx.EXPAND)
        n = n + 1
        grid.Add(ion_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.origami_ion_value, (n,1), wx.GBSpan(1,2), flag=wx.EXPAND)
        n = n + 1
        grid.Add(label_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.origami_label_value, (n,1), wx.GBSpan(1,2), flag=wx.EXPAND)
        n = n + 1
        grid.Add(charge_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.origami_charge_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(min_threshold_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.origami_min_threshold_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(max_threshold_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.origami_max_threshold_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(colormap_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.origami_colormap_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        grid.Add(self.origami_restrictColormap_value, (n,2), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(color_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.origami_color_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(mask_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.origami_mask_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(transparency_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.origami_transparency_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(origami_box_sizer, (n,0), wx.GBSpan(1,3), flag=wx.EXPAND)
        n = n + 1
        grid.Add(horizontal_line, (n,0), wx.GBSpan(1,3), flag=wx.EXPAND)
        n = n + 1
        grid.Add(btn_grid, (n,0), wx.GBSpan(1,3), flag=wx.EXPAND)
        mainSizer.Add(grid, 0, wx.EXPAND, 10)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizerAndFit(mainSizer)
        
        self.enableDisableBoxes(evt=None)

        return panel
           
    def onApply(self, evt):
        self.onCheckID()
        if self.importEvent: return
        self.parent.peaklist.CheckItem(self.itemInfo['id'], self.origami_select_value.GetValue())
        self.parent.peaklist.SetStringItem(self.itemInfo['id'], self.config.peaklistColNames['charge'], 
                                           self.origami_charge_value.GetValue())
        self.parent.peaklist.SetStringItem(self.itemInfo['id'], self.config.peaklistColNames['colormap'], 
                                           self.origami_colormap_value.GetStringSelection())
        self.parent.peaklist.SetStringItem(self.itemInfo['id'], self.config.peaklistColNames['mask'], 
                                           num2str(self.origami_mask_value.GetValue()))
        self.parent.peaklist.SetStringItem(self.itemInfo['id'], self.config.peaklistColNames['alpha'], 
                                           num2str(self.origami_transparency_value.GetValue()))
        self.parent.peaklist.SetStringItem(self.itemInfo['id'], self.config.peaklistColNames['method'], 
                                           self.origami_method_value.GetStringSelection())
        self.parent.peaklist.SetStringItem(self.itemInfo['id'], self.config.peaklistColNames['label'], 
                                           self.origami_label_value.GetValue())
        
        if self.itemInfo['parameters'] == None:
            self.itemInfo['parameters'] = {}
        self.itemInfo['parameters']['firstVoltage'] = str2int(self.origami_startScan_value.GetValue())
        self.itemInfo['parameters']['startV'] = str2num(self.origami_startVoltage_value.GetValue())
        self.itemInfo['parameters']['endV'] = str2num(self.origami_endVoltage_value.GetValue())
        self.itemInfo['parameters']['stepV'] = str2num(self.origami_stepVoltage_value.GetValue())
        self.itemInfo['parameters']['spv'] = str2int(self.origami_scansPerVoltage_value.GetValue())
        self.itemInfo['parameters']['expIncrement'] = str2num(self.origami_exponentialIncrement_value.GetValue())
        self.itemInfo['parameters']['expPercent'] = str2num(self.origami_exponentialPercentage_value.GetValue())
        self.itemInfo['parameters']['dx'] = str2num(self.origami_boltzmannOffset_value.GetValue())
        
        # update ion information
        self.itemInfo['charge'] = self.origami_charge_value.GetValue()
        self.itemInfo['colormap'] = self.origami_colormap_value.GetStringSelection()
        self.itemInfo['mask'] = self.origami_mask_value.GetValue()
        self.itemInfo['alpha'] = self.origami_transparency_value.GetValue()
        self.itemInfo['label'] = self.origami_label_value.GetValue()
        self.itemInfo['min_threshold'] = self.origami_min_threshold_value.GetValue()
        self.itemInfo['max_threshold'] = self.origami_max_threshold_value.GetValue()
        
        # update ion value
        try:
            charge = str2int(self.itemInfo['charge'])
            ion_centre = (str2num(self.itemInfo['mzStart']) + str2num(self.itemInfo['mzEnd']))/2
            mw = (ion_centre - self.config.elementalMass['Hydrogen'] * charge) * charge
            ion_value = (u"%s  ~%.2f Da") % (self.itemInfo['ionName'], mw)
            self.origami_ion_value.SetValue(ion_value)
        except:
            self.origami_ion_value.SetValue(self.itemInfo['ionName'])
        
        self.OnAssignColor(evt=None)
        self.parent.onUpdateDocument(itemInfo=self.itemInfo, evt=None)
        
        if evt != None:
            evt.Skip() 
         
    def onSetupParameters(self, evt):
        self.importEvent = True
        self.origami_select_value.SetValue(self.itemInfo['select'])
        self.origami_filename_value.SetValue(self.itemInfo['document'])
        
        try:
            charge = str2int(self.itemInfo['charge'])
            ion_centre = (str2num(self.itemInfo['mzStart']) + str2num(self.itemInfo['mzEnd']))/2
            mw = (ion_centre - self.config.elementalMass['Hydrogen'] * charge) * charge
            ion_value = (u"%s  ~%.2f Da") % (self.itemInfo['ionName'], mw)
            self.origami_ion_value.SetValue(ion_value)
        except:
            self.origami_ion_value.SetValue(self.itemInfo['ionName'])
            
        self.origami_charge_value.SetValue(str(self.itemInfo['charge']))
        self.origami_label_value.SetValue(self.itemInfo['label'])
        self.origami_colormap_value.SetStringSelection(self.itemInfo['colormap'])
        self.origami_mask_value.SetValue(self.itemInfo['mask'])
        self.origami_transparency_value.SetValue(self.itemInfo['alpha'])
        self.origami_color_value.SetBackgroundColour(self.itemInfo['color'])
        self.origami_min_threshold_value.SetValue(self.itemInfo['min_threshold'])
        self.origami_max_threshold_value.SetValue(self.itemInfo['max_threshold'])
        
        if self.itemInfo['parameters'] != None:
            self.origami_method_value.SetStringSelection(self.itemInfo['parameters']['method'])
            self.origami_startScan_value.SetValue(str(self.itemInfo['parameters'].get('firstVoltage', '')))
            self.origami_scansPerVoltage_value.SetValue(str(self.itemInfo['parameters'].get('spv', '')))
            self.origami_startVoltage_value.SetValue(str(self.itemInfo['parameters'].get('startV', '')))
            self.origami_endVoltage_value.SetValue(str(self.itemInfo['parameters'].get('endV', '')))
            self.origami_stepVoltage_value.SetValue(str(self.itemInfo['parameters'].get('stepV', '')))
            self.origami_exponentialIncrement_value.SetValue(str(self.itemInfo['parameters'].get('expIncrement', '')))
            self.origami_exponentialPercentage_value.SetValue(str(self.itemInfo['parameters'].get('expPercent', '')))
            self.origami_boltzmannOffset_value.SetValue(str(self.itemInfo['parameters'].get('dx', '')))
        else:
            self.origami_startScan_value.SetValue(str(self.config.origami_startScan))
            self.origami_scansPerVoltage_value.SetValue(str(self.config.origami_spv))
            self.origami_startVoltage_value.SetValue(str(self.config.origami_startVoltage))
            self.origami_endVoltage_value.SetValue(str(self.config.origami_endVoltage))
            self.origami_stepVoltage_value.SetValue(str(self.config.origami_stepVoltage))
            self.origami_exponentialIncrement_value.SetValue(str(self.config.origami_exponentialIncrement))
            self.origami_exponentialPercentage_value.SetValue(str(self.config.origami_exponentialPercentage))
            self.origami_boltzmannOffset_value.SetValue(str(self.config.origami_boltzmannOffset))
            self.origami_method_value.SetStringSelection(self.config.origami_acquisition)
            try: self.origami_method_value.SetStringSelection(self.itemInfo['method'])
            except: pass
            
        self.enableDisableBoxes(evt=None)
        self.importEvent = False
        
    def onUpdateGUI(self, itemInfo):
        """
        @param itemInfo (dict): updating GUI with new item information
        """
        self.itemInfo = itemInfo
        self.SetTitle(self.itemInfo['ionName'])
        
        # check values
        if self.itemInfo['mask'] in ['', None, 'None']:
            self.itemInfo['mask'] = 1

        if self.itemInfo['alpha'] in ['', None, 'None']:
            self.itemInfo['alpha'] = 1
            
        if self.itemInfo['colormap'] in ['', None, 'None']:
            self.itemInfo['colormap'] = self.config.currentCmap
            
        if self.itemInfo['color'][0] == -1:
              self.itemInfo['color'] = (1, 1, 1, 255)
              
        if self.itemInfo['charge'] in ['', None, 'None']:
            self.itemInfo['charge'] = ""
              
        # setup values
        self.onSetupParameters(evt=None)
        
        self.SetFocus()
            
    def enableDisableBoxes(self, evt):
        
        method = self.origami_method_value.GetStringSelection()
        enableList, disableList = [], []
        if method == 'Linear':
            disableList = [self.origami_boltzmannOffset_value,self.origami_exponentialIncrement_value,
                           self.origami_exponentialPercentage_value]
            enableList = [self.origami_scansPerVoltage_value, 
#                           self.origami_loadParams, 
                          self.origami_startScan_value, self.origami_startVoltage_value,
                          self.origami_endVoltage_value, self.origami_stepVoltage_value]
        elif method == 'Exponential':
            disableList = [self.origami_boltzmannOffset_value]
            enableList = [self.origami_scansPerVoltage_value, 
#                           self.origami_loadParams, 
                          self.origami_startScan_value, self.origami_startVoltage_value,
                          self.origami_endVoltage_value, self.origami_stepVoltage_value,
                          self.origami_exponentialIncrement_value,
                          self.origami_exponentialPercentage_value]
        elif method == 'Boltzmann':
            disableList = []
            enableList = [self.origami_scansPerVoltage_value, 
#                           self.origami_loadParams, 
                          self.origami_startScan_value, self.origami_startVoltage_value,
                          self.origami_endVoltage_value, self.origami_stepVoltage_value,
                          self.origami_exponentialIncrement_value,
                          self.origami_exponentialPercentage_value,
                          self.origami_boltzmannOffset_value]
        elif method == 'User-defined':
            disableList = [self.origami_scansPerVoltage_value, 
                          self.origami_startVoltage_value,
                          self.origami_endVoltage_value, self.origami_stepVoltage_value,
                          self.origami_exponentialIncrement_value,
                          self.origami_exponentialPercentage_value,
                          self.origami_boltzmannOffset_value]
            enableList = [self.origami_startScan_value
#                         self.origami_loadParams, 
                          ]
        elif method == 'Manual':
            disableList = [self.origami_scansPerVoltage_value, 
#                            self.origami_loadParams
                              self.origami_startScan_value, self.origami_startVoltage_value,
                          self.origami_endVoltage_value, self.origami_stepVoltage_value,
                          self.origami_exponentialIncrement_value,
                          self.origami_exponentialPercentage_value,
                          self.origami_boltzmannOffset_value, ]
            enableList = []
            
        for item in enableList:
            item.Enable()
        for item in disableList:
            item.Disable()
        
        if evt != None:
            evt.Skip() 

    def OnAssignColor(self, evt):
        self.onCheckID()
        if evt:
            color = self.parent.OnAssignColor(evt=None, 
                                                   itemID=self.itemInfo['id'], 
                                                   give_value=True)
            self.origami_color_value.SetBackgroundColour(color)
        else:
            color = self.origami_color_value.GetBackgroundColour()
            self.parent.peaklist.SetItemBackgroundColour(self.itemInfo['id'], color)
              
    def onRestrictCmaps(self, evt):
        """
        The cmap list will be restricted to more limited selection
        """
        currentCmap = self.origami_colormap_value.GetStringSelection()
        narrowList = self.config.narrowCmapList
        narrowList.append(currentCmap)
        
        # remove duplicates
        narrowList = sorted(list(set(narrowList)))
         
        if self.origami_restrictColormap_value.GetValue():
            self.origami_colormap_value.Clear()
            for item in narrowList:
                self.origami_colormap_value.Append(item)
            self.origami_colormap_value.SetStringSelection(currentCmap)
        else:
            self.origami_colormap_value.Clear()
            for item in self.config.cmaps2:
                self.origami_colormap_value.Append(item)
            self.origami_colormap_value.SetStringSelection(currentCmap)
      
    def onGetNext(self, evt):
        self.onCheckID()
        count = self.parent.peaklist.GetItemCount()-1
        if self.itemInfo['id'] == count:
            new_id = 0
        else:
            new_id = self.itemInfo['id'] + 1

        
        # get new information
        self.itemInfo = self.parent.OnGetItemInformation(new_id)
        # update table
        self.onSetupParameters(None)
        # update title
        self.SetTitle(self.itemInfo['document'])
        
    def onGetPrevious(self, evt):
        self.onCheckID()
        count = self.parent.peaklist.GetItemCount()-1
        if self.itemInfo['id'] == 0:
            new_id = count
        else:
            new_id = self.itemInfo['id'] - 1
            
        # get new information
        self.itemInfo = self.parent.OnGetItemInformation(new_id)
        # update table
        self.onSetupParameters(None)
        # update title
        self.SetTitle(self.itemInfo['document'])
      
    def onCheckID(self):
        # check whether ID is still correct
        information = self.parent.OnGetItemInformation(self.itemInfo['id'])
        
        if information['document'] == self.itemInfo['document']:
            return
        else:
            count = self.parent.peaklist.GetItemCount()
            for row in range(count):
                information = self.parent.OnGetItemInformation(row)
                if information['document'] == self.itemInfo['document']:
                    if information['id'] == self.itemInfo['id']:
                        return
                    else:
                        self.itemInfo['id'] = information['id']
                        return