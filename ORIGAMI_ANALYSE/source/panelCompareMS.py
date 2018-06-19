# -*- coding: utf-8 -*-

# Load libraries
import wx       
from ids import (ID_extraSettings_plot1D, ID_processSettings_MS,
                 ID_extraSettings_legend, ID_compareMS_MS_1, ID_compareMS_MS_2)
from styles import makeCheckbox, makeSuperTip, makeStaticBox
from toolbox import (str2num,  convertRGB1to255, convertRGB255to1, num2str, isnumber)
from help import OrigamiHelp as help

class panelCompareMS(wx.MiniFrame):
    """
    Simple GUI to select mass spectra to compare
    """
    def __init__(self, parent, presenter, config, icons, **kwargs):
        wx.MiniFrame.__init__(self, parent,-1, 'Compare mass spectra...', size=(-1, -1), 
                              style=wx.DEFAULT_FRAME_STYLE & ~wx.RESIZE_BORDER)
        
        self.parent = parent
        self.presenter = presenter
        self.config = config
        self.icons = icons
        
        self.help = help()
        
        self.currentItem = None
        self.kwargs = kwargs   
        self.current_document = self.kwargs['current_document']
        self.spectrum_list = self.kwargs['spectrum_list']
        self.document_list = self.kwargs['document_list']
                
        # make gui items
        self.makeGUI()
                      
        self.Centre()
        self.Layout()
        self.SetFocus()
        
        # bind
        wx.EVT_CLOSE(self, self.onClose)
        self.Bind(wx.EVT_CHAR_HOOK, self.OnKey)
    # ----
    
    def OnKey(self, evt):
        keyCode = evt.GetKeyCode()
        if keyCode == wx.WXK_ESCAPE: # key = esc
            self.onClose(evt=None)
        elif keyCode == 83: # key = s
            self.onSelect(evt=None)
        elif keyCode == 85: # key = u
            self.onPlot(evt=None)
        
        evt.Skip()
        
    def onClose(self, evt):
        """Destroy this frame."""
        
        self.updateMS(evt=None)
        self.Destroy()
    # ----
        
    def onSelect(self, evt):
        
        self.updateMS(evt=None)
        self.parent.documents.updateComparisonMS(evt=None)
        self.Destroy()
        
    def onPlot (self, evt):
        """
        Update plot with currently selected PCs
        """
        self.output = {'spectrum_1':[self.document1_value.GetStringSelection(),
                                     self.msSpectrum1_value.GetStringSelection()],
                       'spectrum_2':[self.document2_value.GetStringSelection(),
                                     self.msSpectrum2_value.GetStringSelection()]}
        
        self.updateMS(evt=None)
        self.parent.documents.updateComparisonMS(evt=None)
        
    def makeGUI(self):
        
        # make panel
        panel = self.makePanel()
        
        # pack element
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(panel, 1, wx.EXPAND, 5)
        
        # fit layout
        self.mainSizer.Fit(self)
        self.SetSizer(self.mainSizer)
        
    def makePanel(self):

        panel = wx.Panel(self, -1, size=(-1,-1))
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        
        ms1_staticBox = makeStaticBox(panel, "Mass spectrum - 1", size=(-1, -1), color=wx.BLACK)
        ms1_staticBox.SetSize((-1,-1))
        ms1_box_sizer = wx.StaticBoxSizer(ms1_staticBox, wx.HORIZONTAL)    
        
        ms2_staticBox = makeStaticBox(panel, "Mass spectrum - 2", size=(-1, -1), color=wx.BLACK)
        ms2_staticBox.SetSize((-1,-1))
        ms2_box_sizer = wx.StaticBoxSizer(ms2_staticBox, wx.HORIZONTAL)    
        
        document1_label = wx.StaticText(panel, -1, "Document:")
        msSpectrum1_spectrum_label = wx.StaticText(panel, -1, "Spectrum:")
        msSpectrum1_color_label = wx.StaticText(panel, -1, "Color:")
        msSpectrum1_transparency_label = wx.StaticText(panel, -1, "Transparency:")
        msSpectrum1_lineStyle_label = wx.StaticText(panel, -1, "Line style:")
        
        document2_label = wx.StaticText(panel, -1, "Document:")
        msSpectrum2_spectrum_label = wx.StaticText(panel, -1, "Spectrum:")
        msSpectrum2_color_label = wx.StaticText(panel, -1, "Color:")
        msSpectrum2_transparency_label = wx.StaticText(panel, -1, "Transparency:")
        msSpectrum2_lineStyle_label = wx.StaticText(panel, -1, "Line style:")
        
        self.document1_value = wx.ComboBox(panel, ID_compareMS_MS_1, 
                                            wx.EmptyString, wx.DefaultPosition, 
                                            wx.Size( -1,-1 ), 
                                            self.document_list, 
                                            wx.CB_READONLY, wx.DefaultValidator)
        self.document1_value.SetStringSelection(self.current_document)
#         self.document1_value.Disable()
        
        self.document2_value = wx.ComboBox(panel, ID_compareMS_MS_2, 
                                            wx.EmptyString, wx.DefaultPosition, 
                                            wx.Size( -1,-1 ), 
                                            self.document_list, 
                                            wx.CB_READONLY, wx.DefaultValidator)
        self.document2_value.SetStringSelection(self.current_document)
#         self.document2_value.Disable()
        
        self.msSpectrum1_value = wx.ComboBox(panel, wx.ID_ANY, 
                                            wx.EmptyString, wx.DefaultPosition, 
                                            wx.Size( -1,-1 ), 
                                            self.spectrum_list, 
                                            wx.CB_READONLY, wx.DefaultValidator)
        self.msSpectrum1_value.SetStringSelection(self.spectrum_list[0])
        self.msSpectrum2_value = wx.ComboBox(panel, wx.ID_ANY, 
                                            wx.EmptyString, wx.DefaultPosition, 
                                            wx.Size( -1,-1 ), 
                                            self.spectrum_list, 
                                            wx.CB_READONLY, wx.DefaultValidator)
        self.msSpectrum2_value.SetStringSelection(self.spectrum_list[1])
        
        self.msSpectrum1_colorBtn = wx.Button(panel, wx.ID_ANY, u"", wx.DefaultPosition, 
                                              wx.Size( 26, 26 ), 0 )
        self.msSpectrum1_colorBtn.SetBackgroundColour(convertRGB1to255(self.config.lineColour_MS1))
        
        self.msSpectrum2_colorBtn = wx.Button(panel, wx.ID_ANY,
                                              u"", wx.DefaultPosition, 
                                              wx.Size( 26, 26 ), 0 )
        self.msSpectrum2_colorBtn.SetBackgroundColour(convertRGB1to255(self.config.lineColour_MS2))
        
        self.msSpectrum1_transparency = wx.SpinCtrlDouble(panel, -1, 
                                               value=str(self.config.lineTransparency_MS1*100), 
                                               min=0, max=100, initial=self.config.lineTransparency_MS1*100, 
                                               inc=10, size=(90, -1))
        self.msSpectrum2_transparency = wx.SpinCtrlDouble(panel, -1, 
                                               value=str(self.config.lineTransparency_MS1*100), 
                                               min=0, max=100, initial=self.config.lineTransparency_MS1*100, 
                                               inc=10, size=(90, -1))
        
        self.msSpectrum1_lineStyle_value = wx.ComboBox(panel, wx.ID_ANY, 
                                            wx.EmptyString, wx.DefaultPosition, 
                                            wx.Size( -1,-1 ), 
                                            self.config.lineStylesList, 
                                            wx.CB_READONLY, wx.DefaultValidator)
        self.msSpectrum1_lineStyle_value.SetStringSelection(self.config.lineStyle_MS1)
        
        self.msSpectrum2_lineStyle_value = wx.ComboBox(panel, wx.ID_ANY, 
                                            wx.EmptyString, wx.DefaultPosition, 
                                            wx.Size( -1,-1 ), 
                                            self.config.lineStylesList, 
                                            wx.CB_READONLY, wx.DefaultValidator)
        self.msSpectrum2_lineStyle_value.SetStringSelection(self.config.lineStyle_MS2)
         
        processing_staticBox = makeStaticBox(panel, "Processing", 
                                                 size=(-1, -1), color=wx.BLACK)
        processing_staticBox.SetSize((-1,-1))
        processing_box_sizer = wx.StaticBoxSizer(processing_staticBox, wx.HORIZONTAL)    
         
        self.preprocess_check = makeCheckbox(panel, u"Preprocess")
        self.preprocess_check.SetValue(self.config.compare_massSpectrumParams['preprocess'])
        self.preprocess_tip = makeSuperTip(self.preprocess_check, delay=7, **self.help.compareMS_preprocess)
         
        self.normalize_check = makeCheckbox(panel, u"Normalize")
        self.normalize_check.SetValue(self.config.compare_massSpectrumParams['normalize'])
        
        self.inverse_check = makeCheckbox(panel, u"Inverse")
        self.inverse_check.SetValue(self.config.compare_massSpectrumParams['inverse'])
        
        self.subtract_check = makeCheckbox(panel, u"Subtract")
        self.subtract_check.SetValue(self.config.compare_massSpectrumParams['subtract'])
        
        settings_label = wx.StaticText(panel, wx.ID_ANY, u"Settings:")
        self.settingsBtn = wx.BitmapButton(panel, ID_extraSettings_plot1D,
                                           self.icons.iconsLib['panel_plot1D_16'],
                                           size=(26, 26), 
                                           style=wx.BORDER_DEFAULT | wx.ALIGN_CENTER_VERTICAL)
        self.settingsBtn.SetBackgroundColour((240,240,240))
        self.settingsBtn_tip = makeSuperTip(self.settingsBtn, delay=7, **self.help.compareMS_open_plot1D_settings)
        
        self.legendBtn = wx.BitmapButton(panel, ID_extraSettings_legend,
                                           self.icons.iconsLib['panel_legend_16'],
                                           size=(26, 26), 
                                           style=wx.BORDER_DEFAULT | wx.ALIGN_CENTER_VERTICAL)
        self.legendBtn.SetBackgroundColour((240,240,240))
        self.legendBtn_tip = makeSuperTip(self.legendBtn, delay=7, **self.help.compareMS_open_legend_settings)
        
        self.processingBtn = wx.BitmapButton(panel, ID_processSettings_MS,
                                           self.icons.iconsLib['process_ms_16'],
                                           size=(26, 26), 
                                           style=wx.BORDER_DEFAULT | wx.ALIGN_CENTER_VERTICAL)
        self.processingBtn.SetBackgroundColour((240,240,240))
        self.processingBtn_tip = makeSuperTip(self.processingBtn, delay=7, **self.help.compareMS_open_processMS_settings)
        
        horizontal_line_1 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_2 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        
        self.selectBtn = wx.Button(panel, wx.ID_OK, "Select", size=(-1, 22))
        self.plotBtn = wx.Button(panel, wx.ID_OK, "Update", size=(-1, 22))
        self.cancelBtn = wx.Button(panel, wx.ID_OK, "Cancel", size=(-1, 22))
 
#         info1_label = wx.StaticText(panel, -1, "Information:")
#         self.info1_value = wx.StaticText(panel, -1, "")
#         info2_label = wx.StaticText(panel, -1, "Information:")
#         self.info2_value = wx.StaticText(panel, -1, "")
        
        self.document1_value.Bind(wx.EVT_COMBOBOX, self.updateGUI)
        self.document2_value.Bind(wx.EVT_COMBOBOX, self.updateGUI)
        self.msSpectrum1_value.Bind(wx.EVT_COMBOBOX, self.updateMS)
        self.msSpectrum2_value.Bind(wx.EVT_COMBOBOX, self.updateMS)
        self.preprocess_check.Bind(wx.EVT_CHECKBOX, self.updateMS)
        self.normalize_check.Bind(wx.EVT_CHECKBOX, self.updateMS)
        self.inverse_check.Bind(wx.EVT_CHECKBOX, self.updateMS)
        self.subtract_check.Bind(wx.EVT_CHECKBOX, self.updateMS)

        self.msSpectrum1_colorBtn.Bind(wx.EVT_BUTTON, self.onUpdateMS1color)
        self.msSpectrum2_colorBtn.Bind(wx.EVT_BUTTON, self.onUpdateMS2color)

        self.msSpectrum1_value.Bind(wx.EVT_COMBOBOX, self.onPlot)
        self.msSpectrum2_value.Bind(wx.EVT_COMBOBOX, self.onPlot)
        self.preprocess_check.Bind(wx.EVT_CHECKBOX, self.onPlot)
        self.normalize_check.Bind(wx.EVT_CHECKBOX, self.onPlot)
        self.inverse_check.Bind(wx.EVT_CHECKBOX, self.onPlot)
        self.subtract_check.Bind(wx.EVT_CHECKBOX, self.onPlot)

        self.selectBtn.Bind(wx.EVT_BUTTON, self.onSelect)
        self.plotBtn.Bind(wx.EVT_BUTTON, self.onPlot)
        self.cancelBtn.Bind(wx.EVT_BUTTON, self.onClose)
        
        self.settingsBtn.Bind(wx.EVT_BUTTON, self.presenter.view.onPlotParameters)
        self.legendBtn.Bind(wx.EVT_BUTTON, self.presenter.view.onPlotParameters)
        self.processingBtn.Bind(wx.EVT_BUTTON, self.presenter.view.onProcessParameters)
            
        GRIDBAG_VSPACE = 7
        GRIDBAG_HSPACE = 5
        
        # button grid
        btn_grid = wx.GridBagSizer(GRIDBAG_VSPACE, GRIDBAG_HSPACE)
        y = 0
        btn_grid.Add(self.settingsBtn, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
        btn_grid.Add(self.legendBtn, (y,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL) 
        btn_grid.Add(self.processingBtn, (y,2), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)  
        
        # pack elements
        
        ms1_grid = wx.GridBagSizer(2, 2)
        y = 0
        ms1_grid.Add(document1_label, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        ms1_grid.Add(self.document1_value, (y,1), wx.GBSpan(1,6), flag=wx.EXPAND)
        y = y+1
        ms1_grid.Add(msSpectrum1_spectrum_label, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        ms1_grid.Add(self.msSpectrum1_value, (y,1), wx.GBSpan(1,6), flag=wx.EXPAND)
        y = y+1
        ms1_grid.Add(msSpectrum1_color_label, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        ms1_grid.Add(self.msSpectrum1_colorBtn, (y,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        ms1_grid.Add(msSpectrum1_transparency_label, (y,2), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        ms1_grid.Add(self.msSpectrum1_transparency, (y,3), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        ms1_grid.Add(msSpectrum1_lineStyle_label, (y,4), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        ms1_grid.Add(self.msSpectrum1_lineStyle_value, (y,5), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
#         y = y+1
#         ms1_grid.Add(info1_label, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
#         ms1_grid.Add(self.info1_value, (y,1), wx.GBSpan(1,6), flag=wx.EXPAND)
        ms1_box_sizer.Add(ms1_grid, 0, wx.EXPAND, 10)
        
        ms2_grid = wx.GridBagSizer(2, 2)
        y = 0
        ms2_grid.Add(document2_label, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        ms2_grid.Add(self.document2_value, (y,1), wx.GBSpan(1,6), flag=wx.EXPAND)
        y = y+1
        ms2_grid.Add(msSpectrum2_spectrum_label, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        ms2_grid.Add(self.msSpectrum2_value, (y,1), wx.GBSpan(1,6), flag=wx.EXPAND)
        y = y+1
        ms2_grid.Add(msSpectrum2_color_label, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        ms2_grid.Add(self.msSpectrum2_colorBtn, (y,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        ms2_grid.Add(msSpectrum2_transparency_label, (y,2), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        ms2_grid.Add(self.msSpectrum2_transparency, (y,3), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        ms2_grid.Add(msSpectrum2_lineStyle_label, (y,4), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        ms2_grid.Add(self.msSpectrum2_lineStyle_value, (y,5), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
#         y = y+1
#         ms2_grid.Add(info2_label, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
#         ms2_grid.Add(self.info2_value, (y,1), wx.GBSpan(1,6), flag=wx.EXPAND)
        ms2_box_sizer.Add(ms2_grid, 0, wx.EXPAND, 10)
        
        processing_grid = wx.GridBagSizer(2, 2)
        y = 0
        processing_grid.Add(self.preprocess_check, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        processing_grid.Add(self.normalize_check, (y,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        processing_grid.Add(self.inverse_check, (y,2), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        processing_grid.Add(self.subtract_check, (y,3), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        processing_box_sizer.Add(processing_grid, 0, wx.EXPAND, 10)
        
        grid = wx.GridBagSizer(GRIDBAG_VSPACE, GRIDBAG_HSPACE)
        y = 0
        grid.Add(ms1_box_sizer, (y,0), wx.GBSpan(1,6), flag=wx.EXPAND)
        y = y+1
        grid.Add(ms2_box_sizer, (y,0), wx.GBSpan(1,6), flag=wx.EXPAND)
        y = y+1
        grid.Add(processing_box_sizer, (y,0), wx.GBSpan(1,6), flag=wx.EXPAND)
        y = y+1
        grid.Add(horizontal_line_1, (y,0), wx.GBSpan(1,6), flag=wx.EXPAND)
        y = y + 1
        grid.Add(settings_label, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(btn_grid, (y,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
        y = y+1
        grid.Add(horizontal_line_2, (y,0), wx.GBSpan(1,6), flag=wx.EXPAND)
        y = y+1
        grid.Add(self.selectBtn, (y,2), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(self.plotBtn, (y,3), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(self.cancelBtn, (y,4), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
        
        mainSizer.Add(grid, 0, wx.EXPAND, 10)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizerAndFit(mainSizer)

        return panel
   
    def updateGUI(self, evt):
        evtID = evt.GetId()
        # update document list
        if evtID == ID_compareMS_MS_1:
            document_1 = self.document1_value.GetStringSelection()
            spectrum_list_1 = self.kwargs['document_spectrum_list'][document_1]
            self.msSpectrum1_value.SetItems(spectrum_list_1)
            self.msSpectrum1_value.SetStringSelection(spectrum_list_1[0])
            
        elif evtID == ID_compareMS_MS_2:
            document_2 = self.document2_value.GetStringSelection()
            spectrum_list_2 = self.kwargs['document_spectrum_list'][document_2]
            self.msSpectrum2_value.SetItems(spectrum_list_2)
            self.msSpectrum2_value.SetStringSelection(spectrum_list_2[0])
        
    def updateMS(self, evt):
        self.config.compare_massSpectrum = [self.msSpectrum1_value.GetStringSelection(),
                                            self.msSpectrum2_value.GetStringSelection()]
        self.config.lineTransparency_MS1 = str2num(self.msSpectrum1_transparency.GetValue())/100
        self.config.lineStyle_MS1 = self.msSpectrum1_lineStyle_value.GetStringSelection()
        
        self.config.lineTransparency_MS2 = str2num(self.msSpectrum2_transparency.GetValue())/100
        self.config.lineStyle_MS2 = self.msSpectrum2_lineStyle_value.GetStringSelection()
        
        self.config.compare_massSpectrumParams['preprocess'] = self.preprocess_check.GetValue()
        self.config.compare_massSpectrumParams['inverse'] = self.inverse_check.GetValue()
        self.config.compare_massSpectrumParams['normalize'] = self.normalize_check.GetValue()
        self.config.compare_massSpectrumParams['subtract'] = self.subtract_check.GetValue()
        
        if evt != None:
            evt.Skip() 
           
    def onUpdateMS1color(self, evt):
        # Restore custom colors
        custom = wx.ColourData()
        for key in self.config.customColors:
            custom.SetCustomColour(key, self.config.customColors[key])
        dlg = wx.ColourDialog(self, custom)
        dlg.GetColourData().SetChooseFull(True)
        
        # Show dialog and get new colour
        if dlg.ShowModal() == wx.ID_OK:
            data = dlg.GetColourData()
            newColour = list(data.GetColour().Get())
            self.config.lineColour_MS1 = convertRGB255to1(newColour)
            dlg.Destroy()
            # Retrieve custom colors
            for i in xrange(15):
                self.config.customColors[i] = data.GetCustomColour(i)
        else:
            return
        self.msSpectrum1_colorBtn.SetBackgroundColour(newColour)
         
    def onUpdateMS2color(self, evt):
        # Restore custom colors
        custom = wx.ColourData()
        for key in self.config.customColors:
            custom.SetCustomColour(key, self.config.customColors[key])
        dlg = wx.ColourDialog(self, custom)
        dlg.GetColourData().SetChooseFull(True)
        
        # Show dialog and get new colour
        if dlg.ShowModal() == wx.ID_OK:
            data = dlg.GetColourData()
            newColour = list(data.GetColour().Get())
            self.config.lineColour_MS2 = convertRGB255to1(newColour)
            dlg.Destroy()
            # Retrieve custom colors
            for i in xrange(15):
                self.config.customColors[i] = data.GetCustomColour(i)
        else:
            return
        self.msSpectrum2_colorBtn.SetBackgroundColour(newColour)
