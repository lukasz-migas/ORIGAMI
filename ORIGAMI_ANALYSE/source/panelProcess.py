# -*- coding: utf-8 -*-

# Load libraries
import wx        
from toolbox import str2num, str2int, convertRGB255to1, isempty
from styles import (makeToggleBtn, validator, layout, makeCheckbox, makeSuperTip,
                    makeStaticBox)
from ids import (ID_processSettings_replotMS, ID_processSettings_processMS, 
                 ID_processSettings_process2D, ID_processSettings_replot2D,
                 ID_processSettings_UniDec_info, ID_processSettings_runUniDec,
                 ID_processSettings_preprocessUniDec, ID_processSettings_pickPeaksUniDec,
                 ID_processSettings_autoUniDec, ID_processSettings_loadDataUniDec,
                 ID_processSettings_runAll, ID_processSettings_replotUniDec,
                 ID_processSettings_showZUniDec, ID_processSettings_isolateZUniDec,
                 ID_processSettings_replotAll)
import massLynxFcns as ml
import numpy as np
from help import OrigamiHelp as help
from dialogs import panelHTMLViewer, panelPeakWidthTool, dlgBox
import unidec
from os import chdir


class panelProcessData(wx.MiniFrame):
    """
    """
    
    def __init__(self, parent, presenter, config, icons, **kwargs):
        wx.MiniFrame.__init__(self, parent,-1, 'Processing...', size=(-1, -1), 
                              style= (wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BOX | 
                                      wx.MAXIMIZE_BOX | wx.CLOSE_BOX))
        
        self.parent = parent
        self.presenter = presenter
        self.config = config
        self.icons = icons
        self.help = help()
        
        self.importEvent = False
        
        self.currentPage = None
        self.windowSizes = {'Extract':(470,390), 'ORIGAMI':(412,366),
                            'Mass spectrum':(412,575), 
                            '2D':(412,268), 'Peak fitting':(412,517),
                            'UniDec':(400,775)}
        
        # check if document/item information in kwarg
        if kwargs.get('processKwargs', None) != {}:
            self.onUpdateKwargs(data_type=kwargs['processKwargs']['update_mode'],
                                **kwargs['processKwargs'])
        else:
            self.document = {}
            self.dataset = {}
            self.ionName = {}
            
        # get document
        self.currentDoc = self.presenter.view.panelDocuments.topP.documents.enableCurrentDocument()
        try:
            document = self.presenter.documentsDict[self.currentDoc]
        except: 
            document = None
        try:
            self.parameters = document.parameters
        except:
            self.parameters = {}
        
        # make gui items
        self.makeGUI()
        self.makeStatusBar()
        self.mainBook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.onPageChanged)
        self.mainBook.SetSelection(self.config.processParamsWindow[kwargs['window']])
                    
        
        # check if new title is present
        if document != None:
            self.SetTitle("Processing - %s" % document.title)
        elif kwargs.get('title', None) != None:
            self.SetTitle(kwargs['title'])
        
        # bind
        wx.EVT_CLOSE(self, self.onClose)
        self.Bind(wx.EVT_CHAR_HOOK, self.OnKey)
        
        layout(self, self.mainSizer, size=(412,-1))
        self.mainSizer.Fit(self)
        self.Centre()
        self.Layout()
        self.Show(True)
        self.SetFocus()
        
        # fire-up start events
        self.onPageChanged(evt=None)
        self.updateStatusbar()
        self.onUpdateUniDecPanel()
        
    def onUpdateKwargs(self, data_type='MS', **kwargs):
        if not hasattr(self, 'document'):
            self.document = {}
        if not hasattr(self, 'dataset'):
            self.dataset = {}
        if not hasattr(self, 'ionName'):
            self.ionName = {}
            
        if data_type == 'MS':
            self.document['MS'] = kwargs['document_MS']
            self.dataset['MS'] = kwargs['dataset_MS']
            self.ionName['MS'] = kwargs['ionName_MS']
        elif data_type == '2D':
            self.document['2D'] = kwargs['document_2D']
            self.dataset['2D'] = kwargs['dataset_2D']
            self.ionName['2D'] = kwargs['ionName_2D']
        
        try:
            self.onUpdateUniDecPanel()
        except:
            pass
        
    def onUpdateUniDecPanel(self):
        try:
            self.unidec_weightList_choice.Clear()
            kwargs = {'notify_of_error':False}
            data, __, __ = self.get_unidec_data(data_type="document_all", **kwargs)
            massList, massMax = data['unidec']['m/z with isolated species']['_massList_']
            self.unidec_weightList_choice.SetItems(massList)
            self.unidec_weightList_choice.SetStringSelection(massMax) 
        except:
            pass
        
    def OnKey(self, evt):
        keyCode = evt.GetKeyCode()
#         print(keyCode)
        if keyCode == wx.WXK_ESCAPE: # key = esc
            self.onClose(evt=None)
        elif keyCode == 65: # key = a
            self.onApply(evt=None)
            
        if evt != None:
            evt.Skip()
       
    def onPageChanged(self, evt):
        self.currentPage = self.mainBook.GetPageText(self.mainBook.GetSelection())
        self.SetSize(self.windowSizes[self.currentPage])
        self.Layout()
        
        # check if current tab is one of the following
        if self.currentPage in ['Mass spectrum', '2D', 'Peak fitting']:
            if self.currentPage == 'Mass spectrum':
                try: self.SetTitle("%s - %s" % (self.document['MS'], self.dataset['MS']))
                except: 
                    self.SetTitle("Processing...")
            elif self.currentPage == '2D':
                try: self.SetTitle("%s - %s - %s" % (self.document['2D'], self.dataset['2D'], self.ionName['2D']))
                except: self.SetTitle("Processing...")
        else:
            self.SetTitle("Processing...")
        
    def onSetPage(self, **kwargs):
        self.mainBook.SetSelection(self.config.processParamsWindow[kwargs['window']])
        self.onPageChanged(evt=None)
        self.onUpdateKwargs(data_type=kwargs['processKwargs'].get('update_mode', None),
                            **kwargs['processKwargs'])
       
    def onClose(self, evt):
        """Destroy this frame."""
        self.config.processParamsWindow_on_off = False
        self.Destroy()
    # ----
        
    def onSelect(self, evt):
        self.Destroy()
        
    def makeGUI(self):
        
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        # Setup notebook
        self.mainBook = wx.Notebook(self, wx.ID_ANY, wx.DefaultPosition,
                                    wx.DefaultSize, style=wx.NB_MULTILINE)
        
        
        
        self.parameters_Extract = wx.Panel(self.mainBook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.mainBook.AddPage(self.makePanel_ExtractData(self.parameters_Extract), 
                              u"Extract", False)
        # ------
        self.parameters_ORIGAMI = wx.Panel(self.mainBook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.mainBook.AddPage(self.makePanel_ORIGAMI(self.parameters_ORIGAMI), 
                              u"ORIGAMI", False)
        # ------
        self.parameters_MS = wx.Panel(self.mainBook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.mainBook.AddPage(self.makePanel_MS(self.parameters_MS), 
                              u"Mass spectrum", False)
        # ------
        self.parameters_2D = wx.Panel(self.mainBook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.mainBook.AddPage(self.makePanel_2D(self.parameters_2D), 
                              u"2D", False)
        # ------
        self.parameters_peakFitting = wx.Panel(self.mainBook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.mainBook.AddPage(self.makePanel_PeakFitting(self.parameters_peakFitting), 
                              u"Peak fitting", False)
        # ------
        self.parameters_unidec = wx.Panel(self.mainBook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.mainBook.AddPage(self.makePanel_UniDec(self.parameters_unidec), 
                              u"UniDec", False)
        
        self.mainSizer.Add(self.mainBook, 1, wx.EXPAND |wx.ALL, 2)
        
        # fire-up a couple of events
        self.enableDisableBoxes(evt=None)
        
        # setup color
        self.mainBook.SetBackgroundColour((240, 240, 240))
        
    def makeStatusBar(self):
        self.mainStatusbar = self.CreateStatusBar(4, wx.ST_SIZEGRIP|wx.ST_ELLIPSIZE_MIDDLE, wx.ID_ANY)
        self.mainStatusbar.SetStatusWidths([-1, 90, 120, 60])
        self.mainStatusbar.SetFont(wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.NORMAL))
        
    def updateStatusbar(self):
        # update status bar
        self.SetStatusText('Processing:', 0)
        self.SetStatusText('Plot 1D: %s' % self.parent.panelPlots.window_plot1D, 1) 
        self.SetStatusText('Plot 2D: %s' % self.parent.panelPlots.window_plot2D, 2) 
        self.SetStatusText('Plot 3D: %s' % self.parent.panelPlots.window_plot3D, 3) 
         
    def makePanel_UniDec(self, panel):
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        
        TEXTCTRL_SIZE = (60, -1)
        BTN_SIZE = (100, 22)
        
        # Preprocess
        preprocess_staticBox = makeStaticBox(panel, "Pre-processing parameters", size=(-1, -1), color=wx.BLACK)
        preprocess_staticBox.SetSize((-1,-1))
        preprocess_box_sizer = wx.StaticBoxSizer(preprocess_staticBox, wx.HORIZONTAL)
        
        unidec_ms_min_label = wx.StaticText(panel, wx.ID_ANY, u"m/z start:")
        self.unidec_mzStart_value = wx.TextCtrl(panel, -1, "", size=TEXTCTRL_SIZE,
                                                validator=validator('floatPos'))
        self.unidec_mzStart_value.SetValue(str(self.config.unidec_mzStart))
        self.unidec_mzStart_value.Bind(wx.EVT_TEXT, self.onApply)
        _tip = makeSuperTip(self.unidec_mzStart_value, **self.help.unidec_min_mz)
        
        unidec_ms_max_label = wx.StaticText(panel, wx.ID_ANY, u"end:")
        self.unidec_mzEnd_value = wx.TextCtrl(panel, -1, "", size=TEXTCTRL_SIZE,
                                          validator=validator('floatPos'))
        self.unidec_mzEnd_value.SetValue(str(self.config.unidec_mzEnd))
        self.unidec_mzEnd_value.Bind(wx.EVT_TEXT, self.onApply)
        _tip = makeSuperTip(self.unidec_mzEnd_value, **self.help.unidec_max_mz)
        
        unidec_ms_binsize_label = wx.StaticText(panel, wx.ID_ANY, u"m/z bin size:")
        self.unidec_mzBinSize_value = wx.TextCtrl(panel, -1, "", size=TEXTCTRL_SIZE,
                                          validator=validator('floatPos'))
        self.unidec_mzBinSize_value.SetValue(str(self.config.unidec_mzBinSize))
        self.unidec_mzBinSize_value.Bind(wx.EVT_TEXT, self.onApply)
        _tip = makeSuperTip(self.unidec_mzBinSize_value, **self.help.unidec_linearization)
        
        unidec_ms_gaussianFilter_label = wx.StaticText(panel, wx.ID_ANY, u"Gaussian filter:")
        self.unidec_gaussianFilter_value = wx.TextCtrl(panel, -1, "", size=TEXTCTRL_SIZE,
                                          validator=validator('floatPos'))
        self.unidec_gaussianFilter_value.SetValue(str(self.config.unidec_gaussianFilter))
        self.unidec_gaussianFilter_value.Bind(wx.EVT_TEXT, self.onApply)

        unidec_ms_accelerationV_label = wx.StaticText(panel, wx.ID_ANY, u"Acceleration voltage (kV):")
        self.unidec_accelerationV_value = wx.TextCtrl(panel, -1, "", size=TEXTCTRL_SIZE,
                                          validator=validator('floatPos'))
        self.unidec_accelerationV_value.SetValue(str(self.config.unidec_accelerationV))
        self.unidec_accelerationV_value.Bind(wx.EVT_TEXT, self.onApply)
        
        unidec_linearization_label = wx.StaticText(panel, wx.ID_ANY, u"Linearization mode:")
        self.unidec_linearization_choice = wx.Choice(panel, -1, choices=self.config.unidec_linearization_choices.keys(),
                                          size=(-1, -1))
        self.unidec_linearization_choice.SetStringSelection(self.config.unidec_linearization)
        self.unidec_linearization_choice.Bind(wx.EVT_CHOICE, self.onApply)
        
        self.unidec_load = wx.Button(panel, ID_processSettings_loadDataUniDec, "Initilise UniDec", size=BTN_SIZE)
        self.unidec_preprocess = wx.Button(panel, ID_processSettings_preprocessUniDec, "Pre-process", size=BTN_SIZE)
         
        # pack elements
        preprocess_grid = wx.GridBagSizer(2, 2)
        n = 0
        preprocess_grid.Add(unidec_ms_min_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        preprocess_grid.Add(self.unidec_mzStart_value, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL)
#         n = n + 1
        preprocess_grid.Add(unidec_ms_max_label, (n,2), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        preprocess_grid.Add(self.unidec_mzEnd_value, (n,3), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        preprocess_grid.Add(unidec_ms_binsize_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        preprocess_grid.Add(self.unidec_mzBinSize_value, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        preprocess_grid.Add(unidec_ms_gaussianFilter_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        preprocess_grid.Add(self.unidec_gaussianFilter_value, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        preprocess_grid.Add(unidec_ms_accelerationV_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        preprocess_grid.Add(self.unidec_accelerationV_value, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        preprocess_grid.Add(unidec_linearization_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        preprocess_grid.Add(self.unidec_linearization_choice, (n,1), wx.GBSpan(1,4), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        preprocess_grid.Add(self.unidec_load, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL)
        preprocess_grid.Add(self.unidec_preprocess, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL)
        preprocess_box_sizer.Add(preprocess_grid, 0, wx.EXPAND, 10)
         
        # UniDec parameters
        unidec_staticBox = makeStaticBox(panel, "UniDec parameters", size=(-1, -1), color=wx.BLACK)
        unidec_staticBox.SetSize((-1,-1))
        unidec_box_sizer = wx.StaticBoxSizer(unidec_staticBox, wx.HORIZONTAL)
         
        unidec_charge_min_label = wx.StaticText(panel, wx.ID_ANY, u"Charge start:")
        self.unidec_zStart_value = wx.TextCtrl(panel, -1, "", size=TEXTCTRL_SIZE,
                                          validator=validator('floatPos'))
        self.unidec_zStart_value.SetValue(str(self.config.unidec_zStart))
        self.unidec_zStart_value.Bind(wx.EVT_TEXT, self.onApply)
        _tip = makeSuperTip(self.unidec_zStart_value, **self.help.unidec_min_z)
        
        unidec_charge_max_label = wx.StaticText(panel, wx.ID_ANY, u"end:")
        self.unidec_zEnd_value = wx.TextCtrl(panel, -1, "", size=TEXTCTRL_SIZE,
                                          validator=validator('floatPos'))
        self.unidec_zEnd_value.SetValue(str(self.config.unidec_zEnd))
        self.unidec_zEnd_value.Bind(wx.EVT_TEXT, self.onApply)
        _tip = makeSuperTip(self.unidec_zEnd_value, **self.help.unidec_max_z)
        
        unidec_mw_min_label = wx.StaticText(panel, wx.ID_ANY, u"MW start:")
        self.unidec_mwStart_value = wx.TextCtrl(panel, -1, "", size=TEXTCTRL_SIZE,
                                          validator=validator('floatPos'))
        self.unidec_mwStart_value.SetValue(str(self.config.unidec_mwStart))
        self.unidec_mwStart_value.Bind(wx.EVT_TEXT, self.onApply)
        _tip = makeSuperTip(self.unidec_mwStart_value, **self.help.unidec_min_mw)
        
        unidec_mw_max_label = wx.StaticText(panel, wx.ID_ANY, u"end:")
        self.unidec_mwEnd_value = wx.TextCtrl(panel, -1, "", size=TEXTCTRL_SIZE,
                                          validator=validator('floatPos'))
        self.unidec_mwEnd_value.SetValue(str(self.config.unidec_mwEnd))
        self.unidec_mwEnd_value.Bind(wx.EVT_TEXT, self.onApply)
        _tip = makeSuperTip(self.unidec_mwEnd_value, **self.help.unidec_max_mw)
        
        unidec_mw_sampleFrequency_label = wx.StaticText(panel, wx.ID_ANY, u"Sample frequency (Da):")
        self.unidec_mw_sampleFrequency_value = wx.TextCtrl(panel, -1, "", size=TEXTCTRL_SIZE,
                                          validator=validator('floatPos'))
        self.unidec_mw_sampleFrequency_value.SetValue(str(self.config.unidec_mwFrequency))
        self.unidec_mw_sampleFrequency_value.Bind(wx.EVT_TEXT, self.onApply)
        _tip = makeSuperTip(self.unidec_mw_sampleFrequency_value, **self.help.unidec_mw_resolution)
        
        unidec_peakWidth_label = wx.StaticText(panel, wx.ID_ANY, u"Peak FWHM (Da):")
        self.unidec_fit_peakWidth_value = wx.TextCtrl(panel, -1, "", size=TEXTCTRL_SIZE,
                                          validator=validator('floatPos'))
        self.unidec_fit_peakWidth_value.SetValue(str(self.config.unidec_peakWidth))
        self.unidec_fit_peakWidth_value.Bind(wx.EVT_TEXT, self.onApply)
        _tip = makeSuperTip(self.unidec_fit_peakWidth_value, **self.help.unidec_peak_FWHM)
        
        self.unidec_fit_peakWidth_check = makeCheckbox(panel, u"Auto")
        self.unidec_fit_peakWidth_check.SetValue(self.config.unidec_peakWidth_auto)
        self.unidec_fit_peakWidth_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        self.unidec_fit_peakWidth_check.Bind(wx.EVT_CHECKBOX, self.enableDisableBoxes)
        
        unidec_peakShape_label = wx.StaticText(panel, wx.ID_ANY, u"Peak Shape:")
        self.unidec_peakFcn_choice = wx.Choice(panel, -1, choices=self.config.unidec_peakFunction_choices.keys(),
                                          size=(-1, -1))
        self.unidec_peakFcn_choice.SetStringSelection(self.config.unidec_peakFunction)
        self.unidec_peakFcn_choice.Bind(wx.EVT_CHOICE, self.onApply)
        
        self.unidec_peakTool = wx.Button(panel, -1, "Peak width tool", size=BTN_SIZE)
        self.unidec_runUnidec = wx.Button(panel, ID_processSettings_runUniDec, "Run UniDec", size=BTN_SIZE)
         
        # pack elements
        ms_grid = wx.GridBagSizer(2, 2)
        n = 0
        ms_grid.Add(unidec_charge_min_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        ms_grid.Add(self.unidec_zStart_value, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL)
#         n = n + 1
        ms_grid.Add(unidec_charge_max_label, (n,2), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        ms_grid.Add(self.unidec_zEnd_value, (n,3), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        ms_grid.Add(unidec_mw_min_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        ms_grid.Add(self.unidec_mwStart_value, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL)
#         n = n + 1
        ms_grid.Add(unidec_mw_max_label, (n,2), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        ms_grid.Add(self.unidec_mwEnd_value, (n,3), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        ms_grid.Add(unidec_mw_sampleFrequency_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        ms_grid.Add(self.unidec_mw_sampleFrequency_value, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        ms_grid.Add(unidec_peakWidth_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        ms_grid.Add(self.unidec_fit_peakWidth_value, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL)
        ms_grid.Add(self.unidec_peakTool, (n,2), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL)
        ms_grid.Add(self.unidec_fit_peakWidth_check, (n,3), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        ms_grid.Add(unidec_peakShape_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        ms_grid.Add(self.unidec_peakFcn_choice, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL)
        ms_grid.Add(self.unidec_runUnidec, (n,2), wx.GBSpan(1,2), flag=wx.ALIGN_CENTER_VERTICAL)
        unidec_box_sizer.Add(ms_grid, 0, wx.EXPAND, 10)
         
        # Peak detection
        peakDetect_staticBox = makeStaticBox(panel, "Peak detection parameters", size=(-1, -1), color=wx.BLACK)
        peakDetect_staticBox.SetSize((-1,-1))
        peakDetect_box_sizer = wx.StaticBoxSizer(peakDetect_staticBox, wx.HORIZONTAL)
         
        unidec_peak_width_label = wx.StaticText(panel, wx.ID_ANY, u"Peak detection window (Da):")
        self.unidec_peakWidth_value = wx.TextCtrl(panel, -1, "", size=TEXTCTRL_SIZE,
                                          validator=validator('floatPos'))
        self.unidec_peakWidth_value.SetValue(str(self.config.unidec_peakDetectionWidth))
        self.unidec_peakWidth_value.Bind(wx.EVT_TEXT, self.onApply)
        
        unidec_peak_threshold_label = wx.StaticText(panel, wx.ID_ANY, u"Peak detection threshold:")
        self.unidec_peakThreshold_value = wx.TextCtrl(panel, -1, "", size=TEXTCTRL_SIZE,
                                          validator=validator('floatPos'))
        self.unidec_peakThreshold_value.SetValue(str(self.config.unidec_peakDetectionThreshold))
        self.unidec_peakThreshold_value.Bind(wx.EVT_TEXT, self.onApply)
        
        unidec_peak_normalization_label = wx.StaticText(panel, wx.ID_ANY, u"Peak normalization:")
        self.unidec_peakNormalization_choice = wx.Choice(panel, -1, choices=self.config.unidec_peakNormalization_choices.keys(),
                                          size=(-1, -1))
        self.unidec_peakNormalization_choice.SetStringSelection(self.config.unidec_peakNormalization)
        self.unidec_peakNormalization_choice.Bind(wx.EVT_CHOICE, self.onApply)
        
        individualComponents_label = wx.StaticText(panel, wx.ID_ANY, u"Show individual components:")
        self.unidec_individualComponents_check = makeCheckbox(panel, u"")
        self.unidec_individualComponents_check.SetValue(self.config.unidec_show_individualComponents)
        self.unidec_individualComponents_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        
        markers_label = wx.StaticText(panel, wx.ID_ANY, u"Show markers:")
        self.unidec_markers_check = makeCheckbox(panel, u"")
        self.unidec_markers_check.SetValue(self.config.unidec_show_markers)
        self.unidec_markers_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        
        unidec_peak_separation_label = wx.StaticText(panel, wx.ID_ANY, u"Line separation:")
        self.unidec_lineSeparation_value = wx.TextCtrl(panel, -1, "", size=TEXTCTRL_SIZE,
                                          validator=validator('floatPos'))
        self.unidec_lineSeparation_value.SetValue(str(self.config.unidec_lineSeparation))
        self.unidec_lineSeparation_value.Bind(wx.EVT_TEXT, self.onApply)
        
        self.unidec_detectPeaks = wx.Button(panel, ID_processSettings_pickPeaksUniDec, "Detect peaks", size=BTN_SIZE)
        
        # pack elements
        peak_grid = wx.GridBagSizer(2, 2)
        n = 0
        peak_grid.Add(unidec_peak_width_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        peak_grid.Add(self.unidec_peakWidth_value, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        peak_grid.Add(unidec_peak_threshold_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        peak_grid.Add(self.unidec_peakThreshold_value, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        peak_grid.Add(unidec_peak_normalization_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        peak_grid.Add(self.unidec_peakNormalization_choice, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        peak_grid.Add(unidec_peak_separation_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        peak_grid.Add(self.unidec_lineSeparation_value, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        peak_grid.Add(individualComponents_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        peak_grid.Add(self.unidec_individualComponents_check, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        peak_grid.Add(markers_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        peak_grid.Add(self.unidec_markers_check, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        peak_grid.Add(self.unidec_detectPeaks, (n,0), wx.GBSpan(1,2), flag=wx.ALIGN_CENTER_VERTICAL)
        peakDetect_box_sizer.Add(peak_grid, 0, wx.EXPAND, 10)
         
        # Buttons
        self.unidec_autorun = wx.Button(panel, ID_processSettings_autoUniDec, "Autorun UniDec", size=(-1, 22))
        self.unidec_runAll = wx.Button(panel, ID_processSettings_runAll, "Run all", size=(-1, 22))
        self.unidec_cancelBtn = wx.Button(panel, wx.ID_OK, "Cancel", size=(-1, 22))
        
        self.unidec_info = wx.BitmapButton(panel, ID_processSettings_UniDec_info,
                                             self.icons.iconsLib['process_unidec_16'],
                                             size=(-1, -1), 
                                             style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL)
        self.unidec_info.SetBackgroundColour((240,240,240))
        _tip = makeSuperTip(self.unidec_info, **self.help.unidec_about)
        
        plot_staticBox = makeStaticBox(panel, "Plotting", size=(-1, -1), color=wx.BLACK)
        plot_staticBox.SetSize((-1,-1))
        plot_box_sizer = wx.StaticBoxSizer(plot_staticBox, wx.HORIZONTAL)
        
        self.unidec_chargeStates_Btn = wx.Button(panel, ID_processSettings_showZUniDec, "Label charges", size=(-1, 22))
        self.unidec_chargeStates_Btn.Bind(wx.EVT_BUTTON, self.onPlotUnidec)

        self.unidec_isolateCharges_Btn = wx.Button(panel, ID_processSettings_isolateZUniDec, "Isolate", size=(-1, 22))
        self.unidec_isolateCharges_Btn.Bind(wx.EVT_BUTTON, self.onPlotUnidec)

        speedy_label = wx.StaticText(panel, wx.ID_ANY, u"Quick plot:")
        self.unidec_speedy_check = makeCheckbox(panel, u"", ID=ID_processSettings_replotUniDec)
        self.unidec_speedy_check.SetValue(self.config.unidec_speedy)
        self.unidec_speedy_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        self.unidec_speedy_check.Bind(wx.EVT_CHECKBOX, self.onPlotUnidec)
        
        unidec_plotting_weights_label = wx.StaticText(panel, wx.ID_ANY, u"Molecular weights:")
        self.unidec_weightList_choice = wx.ComboBox(panel, -1, choices=[],
                                                    size=(150, -1), style=wx.CB_READONLY,
                                                    name="ChargeStates")
#         self.unidec_weightList_choice.Bind(wx.EVT_CHOICE, self.onPlotUnidec)

        unidec_plotting_adduct_label = wx.StaticText(panel, wx.ID_ANY, u"Adduct:")
        self.unidec_adductMW_choice = wx.Choice(panel, -1, choices=["H+", "Na+", "K+", "NH4+", "H-", "Cl-"],
                                                size=(-1, -1), name="ChargeStates")
        self.unidec_adductMW_choice.SetStringSelection("H+")
        self.unidec_adductMW_choice.Bind(wx.EVT_CHOICE, self.onPlotUnidec)
        
        self.unidec_replot_Btn = wx.Button(panel, ID_processSettings_replotAll, "Replot", size=(-1, 22))
        self.unidec_replot_Btn.Bind(wx.EVT_BUTTON, self.onPlotUnidec)
        
        unidec_max_iters_label = wx.StaticText(panel, wx.ID_ANY, u"Max iterations:")
        self.unidec_maxIters_value = wx.TextCtrl(panel, -1, "", size=TEXTCTRL_SIZE,
                                          validator=validator('intPos'))
        self.unidec_maxIters_value.SetValue(str(self.config.unidec_maxIterations))
        self.unidec_maxIters_value.Bind(wx.EVT_TEXT, self.onApply)
        
        # pack elements
        plotting_grid = wx.GridBagSizer(2, 2)
        n = 0
        plotting_grid.Add(unidec_plotting_weights_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        plotting_grid.Add(self.unidec_weightList_choice, (n,1), wx.GBSpan(1,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        n = n + 1
        plotting_grid.Add(unidec_plotting_adduct_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        plotting_grid.Add(self.unidec_adductMW_choice, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        n = n + 1
        plotting_grid.Add(self.unidec_chargeStates_Btn, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        plotting_grid.Add(self.unidec_isolateCharges_Btn, (n,2), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        plot_box_sizer.Add(plotting_grid, 0, wx.EXPAND, 10)
        
        horizontal_line_1 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_2 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(preprocess_box_sizer, (n,0), wx.GBSpan(1,5), flag=wx.EXPAND|wx.ALIGN_LEFT)
        n = n + 1
        grid.Add(unidec_box_sizer, (n,0), wx.GBSpan(1,5), flag=wx.EXPAND|wx.ALIGN_LEFT)
        n = n + 1
        grid.Add(peakDetect_box_sizer, (n,0), wx.GBSpan(1,5), flag=wx.EXPAND|wx.ALIGN_LEFT)
        n = n + 1
        grid.Add(plot_box_sizer, (n,0), wx.GBSpan(1,5), flag=wx.EXPAND)
        n = n + 1
        grid.Add(horizontal_line_1, (n,0), wx.GBSpan(1,5), flag=wx.EXPAND)
        n = n + 1
        grid.Add(self.unidec_autorun, (n,0), wx.GBSpan(1,1))
        grid.Add(self.unidec_runAll, (n,1), wx.GBSpan(1,1))
        grid.Add(self.unidec_cancelBtn, (n,2), wx.GBSpan(1,1))
        grid.Add(self.unidec_info, (n,3), wx.GBSpan(1,1), flag=wx.EXPAND|wx.ALIGN_LEFT| wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(horizontal_line_2, (n,0), wx.GBSpan(1,5), flag=wx.EXPAND)
        n = n + 1
        grid.Add(speedy_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.unidec_speedy_check, (n,1), wx.GBSpan(1,1))
        grid.Add(self.unidec_replot_Btn, (n,2), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        n = n + 1
        grid.Add(unidec_max_iters_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.unidec_maxIters_value, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        
        
        mainSizer.Add(grid, 0, wx.ALIGN_CENTER_HORIZONTAL, 10)
         
         
        # bind events
        self.unidec_load.Bind(wx.EVT_BUTTON, self.onRunUnidec)
        self.unidec_preprocess.Bind(wx.EVT_BUTTON, self.onRunUnidec)
        self.unidec_runUnidec.Bind(wx.EVT_BUTTON, self.onRunUnidec)
        self.unidec_runAll.Bind(wx.EVT_BUTTON, self.onRunUnidec)
        self.unidec_detectPeaks.Bind(wx.EVT_BUTTON, self.onRunUnidec)
        self.unidec_autorun.Bind(wx.EVT_BUTTON, self.onRunUnidec)
        self.unidec_cancelBtn.Bind(wx.EVT_BUTTON, self.onClose)
        self.unidec_info.Bind(wx.EVT_BUTTON, self.openHTMLViewer)
        self.unidec_peakTool.Bind(wx.EVT_BUTTON, self.openWidthTool)
        
         
        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizerAndFit(mainSizer)

        return panel
         
    def makePanel_PeakFitting(self, panel):
        mainSizer = wx.BoxSizer(wx.VERTICAL)        
        
        fitPlot_label = wx.StaticText(panel, wx.ID_ANY, u"Fit plot:")
        self.fit_fitPlot_choice = wx.Choice(panel, -1, choices=self.config.fit_type_choices,
                                          size=(-1, -1))
        self.fit_fitPlot_choice.SetStringSelection(self.config.fit_type)
        self.fit_fitPlot_choice.Bind(wx.EVT_CHOICE, self.onApply)
        self.fit_fitPlot_choice.Bind(wx.EVT_CHOICE, self.enableDisableBoxes)
        
        threshold_label = wx.StaticText(panel, wx.ID_ANY, u"Threshold:")
        self.fit_threshold_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('floatPos'))
        self.fit_threshold_value.SetValue(str(self.config.fit_threshold))
        self.fit_threshold_value.Bind(wx.EVT_TEXT, self.onApply)
        
        window_label = wx.StaticText(panel, wx.ID_ANY, u"Window size:")
        self.fit_window_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                            validator=validator('intPos'))
        self.fit_window_value.SetValue(str(self.config.fit_window))
        self.fit_window_value.Bind(wx.EVT_TEXT, self.onApply)
        
        width_label = wx.StaticText(panel, wx.ID_ANY, u"Peak width:")
        self.fit_width_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                           validator=validator('floatPos'))
        self.fit_width_value.SetValue(str(self.config.fit_width))
        self.fit_width_value.Bind(wx.EVT_TEXT, self.onApply)
        
        asymmetricity_label = wx.StaticText(panel, wx.ID_ANY, u"Peak asymmetricity:")
        self.fit_asymmetricRatio_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                           validator=validator('float'))
        self.fit_asymmetricRatio_value.SetValue(str(self.config.fit_asymmetric_ratio))
        self.fit_asymmetricRatio_value.Bind(wx.EVT_TEXT, self.onApply)
        
        smooth_label = wx.StaticText(panel, wx.ID_ANY, u"Smooth peaks:")
        self.fit_smooth_check = makeCheckbox(panel, u"")
        self.fit_smooth_check.SetValue(self.config.fit_smoothPeaks)
        self.fit_smooth_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        self.fit_smooth_check.Bind(wx.EVT_CHECKBOX, self.enableDisableBoxes)

        sigma_label = wx.StaticText(panel, wx.ID_ANY, u"Gaussian sigma:")
        self.fit_sigma_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                           validator=validator('floatPos'))
        self.fit_sigma_value.SetValue(str(self.config.fit_smooth_sigma))
        self.fit_sigma_value.Bind(wx.EVT_TEXT, self.onApply)
        
        highRes_staticBox = makeStaticBox(panel, "Charge state prediction", size=(-1, -1), color=wx.BLACK)
        highRes_staticBox.SetSize((-1,-1))
        highRes_box_sizer = wx.StaticBoxSizer(highRes_staticBox, wx.HORIZONTAL)
        
        highRes_label = wx.StaticText(panel, wx.ID_ANY, u"Enable:")
        self.fit_highRes_check = makeCheckbox(panel, u"")
        self.fit_highRes_check.SetValue(self.config.fit_highRes)
        self.fit_highRes_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        self.fit_highRes_check.Bind(wx.EVT_CHECKBOX, self.enableDisableBoxes)
        self.fit_highRes_tip = makeSuperTip(self.fit_highRes_check, **self.help.fit_highRes)
        
        threshold_highRes_label = wx.StaticText(panel, wx.ID_ANY, u"Threshold:")
        self.fit_thresholdHighRes_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator('floatPos'))
        self.fit_thresholdHighRes_value.SetValue(str(self.config.fit_highRes_threshold))
        self.fit_thresholdHighRes_value.Bind(wx.EVT_TEXT, self.onApply)
         
        window_highRes_label = wx.StaticText(panel, wx.ID_ANY, u"Window size:")
        self.fit_windowHighRes_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator('floatPos'))
        self.fit_windowHighRes_value.SetValue(str(self.config.fit_highRes_window))
        self.fit_windowHighRes_value.Bind(wx.EVT_TEXT, self.onApply)
         
        width_highRes_label = wx.StaticText(panel, wx.ID_ANY, u"Peak width:")
        self.fit_widthHighRes_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator('floatPos'))
        self.fit_widthHighRes_value.SetValue(str(self.config.fit_highRes_width))
        self.fit_widthHighRes_value.Bind(wx.EVT_TEXT, self.onApply)
        
        fitChargeStates_label = wx.StaticText(panel, wx.ID_ANY, u"Isotopic fit:")
        self.fit_isotopes_check = makeCheckbox(panel, u"")
        self.fit_isotopes_check.SetValue(self.config.fit_highRes_isotopicFit)
        self.fit_isotopes_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        self.fit_isotopes_tip = makeSuperTip(self.fit_isotopes_check, **self.help.fit_showIsotopes)

        horizontal_line = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        highlight_label = wx.StaticText(panel, wx.ID_ANY, u"Highlight:")
        self.fit_highlight_check = makeCheckbox(panel, u"")
        self.fit_highlight_check.SetValue(self.config.fit_highlight)
        self.fit_highlight_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        
        addPeaks_label = wx.StaticText(panel, wx.ID_ANY, u"Add peaks to peak list:")
        self.fit_addPeaks_check = makeCheckbox(panel, u"")
        self.fit_addPeaks_check.SetValue(self.config.fit_addPeaks)
        self.fit_addPeaks_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        
        xaxisLimit_label = wx.StaticText(panel, wx.ID_ANY, u"Use current x-axis range:")
        self.fit_xaxisLimit_check = makeCheckbox(panel, u"")
        self.fit_xaxisLimit_check.SetValue(self.config.fit_xaxis_limit)
        self.fit_xaxisLimit_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        
        self.fit_findPeaksBtn = wx.Button(panel, wx.ID_OK, "Find peaks", size=(-1, 22))
        self.fit_findPeaksBtn.Bind(wx.EVT_BUTTON, self.presenter.onPickPeaks)

        self.fit_cancelBtn = wx.Button(panel, wx.ID_OK, "Cancel", size=(-1, 22))        
        self.fit_cancelBtn.Bind(wx.EVT_BUTTON, self.onClose)

        # pack elements
        grid = wx.GridBagSizer(5, 5)
        n = 0
        grid.Add(fitPlot_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.fit_fitPlot_choice, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(threshold_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.fit_threshold_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(window_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.fit_window_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(width_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.fit_width_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(asymmetricity_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.fit_asymmetricRatio_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(smooth_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.fit_smooth_check, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(sigma_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.fit_sigma_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
       
        highRes_grid = wx.GridBagSizer(2, 2)
        n = 0
        highRes_grid.Add(highRes_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        highRes_grid.Add(self.fit_highRes_check, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        highRes_grid.Add(threshold_highRes_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        highRes_grid.Add(self.fit_thresholdHighRes_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        highRes_grid.Add(window_highRes_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        highRes_grid.Add(self.fit_windowHighRes_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        highRes_grid.Add(width_highRes_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        highRes_grid.Add(self.fit_widthHighRes_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        highRes_grid.Add(fitChargeStates_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        highRes_grid.Add(self.fit_isotopes_check, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        highRes_box_sizer.Add(highRes_grid, 0, wx.EXPAND, 10)
        n = 7
        grid.Add(highRes_box_sizer, (n,0), wx.GBSpan(1,5), flag=wx.EXPAND|wx.ALIGN_LEFT)
        n = n + 1
        grid.Add(horizontal_line, (n,0), wx.GBSpan(1,5), flag=wx.EXPAND)
        n = n + 1
        grid.Add(highlight_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.fit_highlight_check, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(addPeaks_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.fit_addPeaks_check, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(xaxisLimit_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.fit_xaxisLimit_check, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(self.fit_findPeaksBtn, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        grid.Add(self.fit_cancelBtn, (n,2), wx.GBSpan(1,1), flag=wx.EXPAND)
        
        
        mainSizer.Add(grid, 0, wx.ALIGN_CENTER_HORIZONTAL, 10)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizerAndFit(mainSizer)
        
        return panel
    
    def makePanel_ORIGAMI(self, panel):
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        
        acquisition_label = wx.StaticText(panel, wx.ID_ANY, u"Acquisition method:")
        self.origami_method_choice = wx.Choice(panel, -1, choices=self.config.origami_acquisition_choices,
                                          size=(-1, -1))
        self.origami_method_choice.SetStringSelection(self.config.origami_acquisition)
        self.origami_method_choice.Bind(wx.EVT_CHOICE, self.onApply)
        self.origami_method_choice.Bind(wx.EVT_CHOICE, self.enableDisableBoxes)
        
#         self.origami_loadParams = wx.BitmapButton(panel, wx.ID_ANY,
#                                                   self.icons.iconsLib['load16'],
#                                                   size=(26, 26),
#                                                   style=wx.BORDER_DOUBLE | wx.ALIGN_CENTER_VERTICAL)
#         self.origami_loadParams.Bind(wx.EVT_BUTTON, self.onUpdateColorbar)
        
        spv_label = wx.StaticText(panel, wx.ID_ANY, u"Scans per voltage:")
        self.origami_scansPerVoltage_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('intPos'))
        self.origami_scansPerVoltage_value.SetValue(str(self.config.origami_spv))
        self.origami_scansPerVoltage_value.Bind(wx.EVT_TEXT, self.onApply)
        
        scan_label = wx.StaticText(panel, wx.ID_ANY, u"First scan:")
        self.origami_startScan_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('intPos'))
        self.origami_startScan_value.SetValue(str(self.config.origami_startScan))
        self.origami_startScan_value.Bind(wx.EVT_TEXT, self.onApply)
        
        startVoltage_label = wx.StaticText(panel, wx.ID_ANY, u"First voltage:")
        self.origami_startVoltage_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('floatPos'))
        self.origami_startVoltage_value.SetValue(str(self.config.origami_startVoltage))
        self.origami_startVoltage_value.Bind(wx.EVT_TEXT, self.onApply)
        
        endVoltage_label = wx.StaticText(panel, wx.ID_ANY, u"Final voltage:")
        self.origami_endVoltage_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('floatPos'))
        self.origami_endVoltage_value.SetValue(str(self.config.origami_endVoltage))
        self.origami_endVoltage_value.Bind(wx.EVT_TEXT, self.onApply)
        
        stepVoltage_label = wx.StaticText(panel, wx.ID_ANY, u"Voltage step:")
        self.origami_stepVoltage_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('floatPos'))
        self.origami_stepVoltage_value.SetValue(str(self.config.origami_stepVoltage))
        self.origami_stepVoltage_value.Bind(wx.EVT_TEXT, self.onApply)
        
        boltzmann_label = wx.StaticText(panel, wx.ID_ANY, u"Boltzmann offset:")
        self.origami_boltzmannOffset_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                                         validator=validator('floatPos'))
        self.origami_boltzmannOffset_value.SetValue(str(self.config.origami_boltzmannOffset))
        self.origami_boltzmannOffset_value.Bind(wx.EVT_TEXT, self.onApply)
        
        exponentialPercentage_label = wx.StaticText(panel, wx.ID_ANY, u"Exponential percentage:")
        self.origami_exponentialPercentage_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('floatPos'))
        self.origami_exponentialPercentage_value.SetValue(str(self.config.origami_exponentialPercentage))
        self.origami_exponentialPercentage_value.Bind(wx.EVT_TEXT, self.onApply)
        
        exponentialIncrement_label = wx.StaticText(panel, wx.ID_ANY, u"Exponential increment:")
        self.origami_exponentialIncrement_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('floatPos'))
        self.origami_exponentialIncrement_value.SetValue(str(self.config.origami_exponentialIncrement))
        self.origami_exponentialIncrement_value.Bind(wx.EVT_TEXT, self.onApply)
        
        import_label = wx.StaticText(panel, wx.ID_ANY, u"Import list:")
        self.origami_loadListBtn = wx.Button(panel, wx.ID_OK, "...", size=(-1, 22))
        self.origami_loadListBtn.Bind(wx.EVT_BUTTON, self.presenter.onUserDefinedListImport)
        
        horizontal_line = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        self.origami_applyBtn = wx.Button(panel, wx.ID_OK, "Apply", size=(-1, 22))
        self.origami_applyBtn.Bind(wx.EVT_BUTTON, self.onProcessMS)
        
        self.origami_cancelBtn = wx.Button(panel, wx.ID_OK, "Cancel", size=(-1, 22))        
        self.origami_cancelBtn.Bind(wx.EVT_BUTTON, self.onClose)
        
        # pack elements
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(acquisition_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.origami_method_choice, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
#         grid.Add(self.origami_loadParams, (n,2), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT)
        n = n + 1
        grid.Add(spv_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.origami_scansPerVoltage_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(scan_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.origami_startScan_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(startVoltage_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.origami_startVoltage_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(endVoltage_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.origami_endVoltage_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(stepVoltage_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.origami_stepVoltage_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(boltzmann_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.origami_boltzmannOffset_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(exponentialPercentage_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.origami_exponentialPercentage_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(exponentialIncrement_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.origami_exponentialIncrement_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(import_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.origami_loadListBtn, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(horizontal_line, (n,0), wx.GBSpan(1,3), flag=wx.EXPAND)
        n = n + 1
        grid.Add(self.origami_applyBtn, (n,1), wx.GBSpan(1,1))
        grid.Add(self.origami_cancelBtn, (n,2), wx.GBSpan(1,1))
        
        mainSizer.Add(grid, 0, wx.ALIGN_CENTER_HORIZONTAL, 10)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizerAndFit(mainSizer)
        
        return panel
    
    def makePanel_MS(self, panel):
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        
        massSpec_staticBox = makeStaticBox(panel, "Linearization parameters", size=(-1, -1), color=wx.BLACK)
        massSpec_staticBox.SetSize((-1,-1))
        massSpec_box_sizer = wx.StaticBoxSizer(massSpec_staticBox, wx.HORIZONTAL)
        
        self.bin_RT_window_check = makeCheckbox(panel, u"Enable MS linearization in chromatogram/mobiligram window")
        self.bin_RT_window_check.SetValue(self.config.ms_enable_in_RT)
        self.bin_RT_window_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        self.bin_RT_window_tip = makeSuperTip(self.bin_RT_window_check, **self.help.bin_MS_in_RT)
        
        self.bin_MML_window_check = makeCheckbox(panel, u"Enable MS linearization when loading Manual aIM-MS datasets")
        self.bin_MML_window_check.SetValue(self.config.ms_enable_in_MML_start)
        self.bin_MML_window_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        self.bin_MML_window_tip = makeSuperTip(self.bin_MML_window_check, **self.help.bin_MS_when_loading_MML)
        
        linearizationMode_label = wx.StaticText(panel, wx.ID_ANY, u"Linearization mode:")
        self.bin_linearizationMode_choice = wx.Choice(panel, -1, choices=self.config.ms_linearization_mode_choices,
                                          size=(-1, -1))
        self.bin_linearizationMode_choice.SetStringSelection(self.config.ms_linearization_mode)
        self.bin_linearizationMode_choice.Bind(wx.EVT_CHOICE, self.onApply)

        bin_ms_min_label = wx.StaticText(panel, wx.ID_ANY, u"m/z start:")
        self.bin_mzStart_value = wx.TextCtrl(panel, -1, "", size=(65, -1),
                                          validator=validator('floatPos'))
        self.bin_mzStart_value.SetValue(str(self.config.ms_mzStart))
        self.bin_mzStart_value.Bind(wx.EVT_TEXT, self.onApply)
        
        bin_ms_max_label = wx.StaticText(panel, wx.ID_ANY, u"end:")
        self.bin_mzEnd_value = wx.TextCtrl(panel, -1, "", size=(65, -1),
                                          validator=validator('floatPos'))
        self.bin_mzEnd_value.SetValue(str(self.config.ms_mzEnd))
        self.bin_mzEnd_value.Bind(wx.EVT_TEXT, self.onApply)
        
        self.bin_autoRange_check = makeCheckbox(panel, u"Automatic range")
        self.bin_autoRange_check.SetValue(self.config.ms_auto_range)
        self.bin_autoRange_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        self.bin_autoRange_check.Bind(wx.EVT_CHECKBOX, self.enableDisableBoxes)
#         self.bin_autoRange_check = makeSuperTip(self.bin_MML_window_check, **self.help.bin_MS_when_loading_MML)

        bin_ms_binsize_label = wx.StaticText(panel, wx.ID_ANY, u"m/z bin size:")
        self.bin_mzBinSize_value = wx.TextCtrl(panel, -1, "", size=(65, -1),
                                          validator=validator('floatPos'))
        self.bin_mzBinSize_value.SetValue(str(self.config.ms_mzBinSize))
        self.bin_mzBinSize_value.Bind(wx.EVT_TEXT, self.onApply)
        
        dtms_staticBox = makeStaticBox(panel, "DT/MS binning parameters", size=(-1, -1), color=wx.BLACK)
        dtms_staticBox.SetSize((-1,-1))
        dtms_box_sizer = wx.StaticBoxSizer(dtms_staticBox, wx.HORIZONTAL)    
        
        bin_msdt_label = wx.StaticText(panel, wx.ID_ANY, u"DT/MS bin size:")
        self.bin_msdt_binSize_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('floatPos'))
        self.bin_msdt_binSize_value.SetValue(str(self.config.ms_dtmsBinSize))
        self.bin_msdt_binSize_value.Bind(wx.EVT_TEXT, self.onApply)
        
        process_staticBox = makeStaticBox(panel, "Smoothing and normalization parameters", size=(-1, -1), color=wx.BLACK)
        process_staticBox.SetSize((-1,-1))
        process_box_sizer = wx.StaticBoxSizer(process_staticBox, wx.HORIZONTAL)    
        
        smoothFcn_label = wx.StaticText(panel, wx.ID_ANY, u"Smooth function:")
        self.ms_smoothFcn_choice = wx.Choice(panel, -1, choices=self.config.ms_smooth_choices,
                                          size=(-1, -1))
        self.ms_smoothFcn_choice.SetStringSelection(self.config.ms_smooth_mode)
        self.ms_smoothFcn_choice.Bind(wx.EVT_CHOICE, self.onApply)
        self.ms_smoothFcn_choice.Bind(wx.EVT_CHOICE, self.enableDisableBoxes)
        
        polynomial_label = wx.StaticText(panel, wx.ID_ANY, u"Polynomial:")
        self.ms_polynomial_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('intPos'))
        self.ms_polynomial_value.SetValue(str(self.config.ms_smooth_polynomial))
        self.ms_polynomial_value.Bind(wx.EVT_TEXT, self.onApply)
        
        window_label = wx.StaticText(panel, wx.ID_ANY, u"Window size:")
        self.ms_window_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('intPos'))
        self.ms_window_value.SetValue(str(self.config.ms_smooth_window))
        self.ms_window_value.Bind(wx.EVT_TEXT, self.onApply)
        
        sigma_label = wx.StaticText(panel, wx.ID_ANY, u"Sigma:")
        self.ms_sigma_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('floatPos'))
        self.ms_sigma_value.SetValue(str(self.config.ms_smooth_sigma))
        self.ms_sigma_value.Bind(wx.EVT_TEXT, self.onApply)
        
        threshold_label = wx.StaticText(panel, wx.ID_ANY, u"Baseline subtraction:")
        self.ms_threshold_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('floatPos'))
        self.ms_threshold_value.SetValue(str(self.config.ms_threshold))
        self.ms_threshold_value.Bind(wx.EVT_TEXT, self.onApply)
        
        normalize_label = wx.StaticText(panel, wx.ID_ANY, u"Normalize:")
        self.ms_normalizeTgl = makeToggleBtn(panel, 'Off', wx.RED)
        self.ms_normalizeTgl.SetValue(self.config.ms_normalize)
        self.ms_normalizeTgl.Bind(wx.EVT_TOGGLEBUTTON, self.onApply)
        self.ms_normalizeTgl.Bind(wx.EVT_TOGGLEBUTTON, self.enableDisableBoxes)
        
        self.ms_normalizeFcn_choice = wx.Choice(panel, -1, 
                                                choices=self.config.ms_normalize_choices,
                                                size=(-1, -1))
        self.ms_normalizeFcn_choice.SetStringSelection(self.config.ms_normalize_mode)
        self.ms_normalizeFcn_choice.Bind(wx.EVT_CHOICE, self.onApply)
        self.ms_normalizeFcn_choice.Bind(wx.EVT_CHOICE, self.enableDisableBoxes)
        
        horizontal_line_1 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        self.ms_applyBtn = wx.Button(panel, ID_processSettings_replotMS, "Replot", size=(-1, 22))
        __tip = makeSuperTip(self.ms_applyBtn, **self.help.process_mass_spectra_replotBtn)
        
        self.ms_processBtn = wx.Button(panel, ID_processSettings_processMS, "Process", size=(-1, 22))
        __tip = makeSuperTip(self.ms_processBtn, **self.help.process_mass_spectra_processesBtn)
        
        self.ms_cancelBtn = wx.Button(panel, wx.ID_OK, "Cancel", size=(-1, 22))
        
        self.ms_applyBtn.Bind(wx.EVT_BUTTON, self.onProcessMS)
        self.ms_processBtn.Bind(wx.EVT_BUTTON, self.onProcessMS)
        self.ms_cancelBtn.Bind(wx.EVT_BUTTON, self.onClose)
        
        steps_staticBox = makeStaticBox(panel, "Processing steps...", size=(-1, -1), color=wx.BLACK)
        steps_staticBox.SetSize((-1,-1))
        steps_box_sizer = wx.StaticBoxSizer(steps_staticBox, wx.HORIZONTAL)
    
        self.ms_process_linearize = makeCheckbox(panel, u"Linearize spectrum")
        self.ms_process_linearize.SetValue(self.config.ms_process_linearize)
        self.ms_process_linearize.Bind(wx.EVT_CHECKBOX, self.onApply)
        
        self.ms_process_smooth = makeCheckbox(panel, u"Smooth spectrum")
        self.ms_process_smooth.SetValue(self.config.ms_process_smooth)
        self.ms_process_smooth.Bind(wx.EVT_CHECKBOX, self.onApply)
        
        self.ms_process_threshold = makeCheckbox(panel, u"Baseline subtract")
        self.ms_process_threshold.SetValue(self.config.ms_process_threshold)
        self.ms_process_threshold.Bind(wx.EVT_CHECKBOX, self.onApply)
        
        self.ms_process_normalize = makeCheckbox(panel, u"Normalize")
        self.ms_process_normalize.SetValue(self.config.ms_process_normalize)
        self.ms_process_normalize.Bind(wx.EVT_CHECKBOX, self.onApply)
            
        # pack elements
        steps_grid = wx.GridBagSizer(2, 2)
        n = 0
        steps_grid.Add(self.ms_process_linearize, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        steps_grid.Add(self.ms_process_smooth, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        steps_grid.Add(self.ms_process_threshold, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        steps_grid.Add(self.ms_process_normalize, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL)
        steps_box_sizer.Add(steps_grid, 0, wx.EXPAND, 10)
        
        
        ms_grid = wx.GridBagSizer(2, 2)
        n = 0
        ms_grid.Add(linearizationMode_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        ms_grid.Add(self.bin_linearizationMode_choice, (n,1), wx.GBSpan(1,4), flag=wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        n = n + 1
        ms_grid.Add(bin_ms_min_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        ms_grid.Add(self.bin_mzStart_value, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL)
        ms_grid.Add(bin_ms_max_label, (n,2), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        ms_grid.Add(self.bin_mzEnd_value, (n,3), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL)
        ms_grid.Add(self.bin_autoRange_check, (n,4), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        ms_grid.Add(bin_ms_binsize_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        ms_grid.Add(self.bin_mzBinSize_value, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1  
        ms_grid.Add(self.bin_RT_window_check, (n,0), wx.GBSpan(1,5), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        ms_grid.Add(self.bin_MML_window_check, (n,0), wx.GBSpan(1,5), flag=wx.ALIGN_CENTER_VERTICAL)

        massSpec_box_sizer.Add(ms_grid, 0, wx.EXPAND, 10)

        dtms_grid = wx.GridBagSizer(2, 2)
        n = 0
        dtms_grid.Add(bin_msdt_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        dtms_grid.Add(self.bin_msdt_binSize_value, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL)
        dtms_box_sizer.Add(dtms_grid, 0, wx.EXPAND, 10)

        process_grid = wx.GridBagSizer(2, 2)
        n = 0
        process_grid.Add(smoothFcn_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        process_grid.Add(self.ms_smoothFcn_choice, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        process_grid.Add(polynomial_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        process_grid.Add(self.ms_polynomial_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        process_grid.Add(window_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        process_grid.Add(self.ms_window_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        process_grid.Add(sigma_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        process_grid.Add(self.ms_sigma_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        process_grid.Add(threshold_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        process_grid.Add(self.ms_threshold_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        process_grid.Add(normalize_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        process_grid.Add(self.ms_normalizeTgl, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        process_grid.Add(self.ms_normalizeFcn_choice, (n,2), wx.GBSpan(1,1), flag=wx.EXPAND)
        process_box_sizer.Add(process_grid, 0, wx.EXPAND, 10)
        
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(dtms_box_sizer, (n,0), wx.GBSpan(1,5), flag=wx.EXPAND|wx.ALIGN_LEFT)
        n = n + 1
        grid.Add(massSpec_box_sizer, (n,0), wx.GBSpan(1,5), flag=wx.EXPAND|wx.ALIGN_LEFT)
        n = n + 1
        grid.Add(process_box_sizer, (n,0), wx.GBSpan(1,5), flag=wx.EXPAND|wx.ALIGN_LEFT)
        n = n + 1
        grid.Add(steps_box_sizer, (n,0), wx.GBSpan(1,5), flag=wx.EXPAND|wx.ALIGN_LEFT)
        n = n + 1
        grid.Add(horizontal_line_1, (n,0), wx.GBSpan(1,5), flag=wx.EXPAND)
        n = n + 1
        grid.Add(self.ms_applyBtn, (n,0), wx.GBSpan(1,1))
        grid.Add(self.ms_processBtn, (n,1), wx.GBSpan(1,1))
        grid.Add(self.ms_cancelBtn, (n,2), wx.GBSpan(1,1))
        
        mainSizer.Add(grid, 0, wx.ALIGN_CENTER_HORIZONTAL, 10)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizerAndFit(mainSizer)
        
        return panel
    
    def makePanel_2D(self, panel):
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        smoothFcn_label = wx.StaticText(panel, wx.ID_ANY, u"Smooth function:")
        self.plot2D_smoothFcn_choice = wx.Choice(panel, -1, choices=self.config.plot2D_smooth_choices,
                                          size=(-1, -1))
        self.plot2D_smoothFcn_choice.SetStringSelection(self.config.plot2D_smooth_mode)
        self.plot2D_smoothFcn_choice.Bind(wx.EVT_CHOICE, self.onApply)
        self.plot2D_smoothFcn_choice.Bind(wx.EVT_CHOICE, self.enableDisableBoxes)
        
        polynomial_label = wx.StaticText(panel, wx.ID_ANY, u"Polynomial:")
        self.plot2D_polynomial_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('intPos'))
        self.plot2D_polynomial_value.SetValue(str(self.config.plot2D_smooth_polynomial))
        self.plot2D_polynomial_value.Bind(wx.EVT_TEXT, self.onApply)
        
        window_label = wx.StaticText(panel, wx.ID_ANY, u"Window size:")
        self.plot2D_window_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('intPos'))
        self.plot2D_window_value.SetValue(str(self.config.plot2D_smooth_window))
        self.plot2D_window_value.Bind(wx.EVT_TEXT, self.onApply)
        
        sigma_label = wx.StaticText(panel, wx.ID_ANY, u"Sigma:")
        self.plot2D_sigma_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                              validator=validator('floatPos'))
        self.plot2D_sigma_value.SetValue(str(self.config.plot2D_smooth_sigma))
        self.plot2D_sigma_value.Bind(wx.EVT_TEXT, self.onApply)
        
        threshold_label = wx.StaticText(panel, wx.ID_ANY, u"Threshold:")
        self.plot2D_threshold_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('floatPos'))
        self.plot2D_threshold_value.SetValue(str(self.config.plot2D_threshold))
        self.plot2D_threshold_value.Bind(wx.EVT_TEXT, self.onApply)
        
        normalize_label = wx.StaticText(panel, wx.ID_ANY, u"Normalize:")
        self.plot2D_normalizeTgl = makeToggleBtn(panel, 'Off', wx.RED)
        self.plot2D_normalizeTgl.SetValue(self.config.plot2D_normalize)
        self.plot2D_normalizeTgl.Bind(wx.EVT_TOGGLEBUTTON, self.onApply)
        self.plot2D_normalizeTgl.Bind(wx.EVT_TOGGLEBUTTON, self.enableDisableBoxes)
                
        self.plot2D_normalizeFcn_choice = wx.Choice(panel, -1, 
                                             choices=self.config.plot2D_normalize_choices,
                                             size=(-1, -1))
        self.plot2D_normalizeFcn_choice.SetStringSelection(self.config.plot2D_normalize_mode)
        self.plot2D_normalizeFcn_choice.Bind(wx.EVT_CHOICE, self.onApply)
        self.plot2D_normalizeFcn_choice.Bind(wx.EVT_CHOICE, self.enableDisableBoxes)
               
        self.plot2D_applyBtn = wx.Button(panel, ID_processSettings_replot2D, "Replot", size=(-1, 22))
        self.plot2D_processBtn = wx.Button(panel, ID_processSettings_process2D, "Process", size=(-1, 22))
        self.plot2D_cancelBtn = wx.Button(panel, wx.ID_OK, "Cancel", size=(-1, 22))
        
        horizontal_line = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        
        self.plot2D_applyBtn.Bind(wx.EVT_BUTTON, self.onProcess2D)
        self.plot2D_processBtn.Bind(wx.EVT_BUTTON, self.onProcess2D)
        self.plot2D_cancelBtn.Bind(wx.EVT_BUTTON, self.onClose)
        
        # pack elements
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(smoothFcn_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.plot2D_smoothFcn_choice, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(polynomial_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.plot2D_polynomial_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(window_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.plot2D_window_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(sigma_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.plot2D_sigma_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(threshold_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.plot2D_threshold_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(normalize_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.plot2D_normalizeTgl, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        grid.Add(self.plot2D_normalizeFcn_choice, (n,2), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(horizontal_line, (n,0), wx.GBSpan(1,3), flag=wx.EXPAND)
        n = n + 1
        grid.Add(self.plot2D_applyBtn, (n,0), wx.GBSpan(1,1))
        grid.Add(self.plot2D_processBtn, (n,1), wx.GBSpan(1,1))
        grid.Add(self.plot2D_cancelBtn, (n,2), wx.GBSpan(1,1))
        
        mainSizer.Add(grid, 0, wx.ALIGN_CENTER_HORIZONTAL, 10)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizerAndFit(mainSizer)

        return panel
    
    def makePanel_ExtractData(self, panel):
        BOLD_STYLE = wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        extractData_sep_label = wx.StaticText(panel, -1, "Extract data")
        extractData_sep_label.SetFont(BOLD_STYLE)
        
        self.mz_label = wx.StaticText(panel, wx.ID_ANY, u"m/z (Da):")
        self.rt_label = wx.StaticText(panel, wx.ID_ANY, u"RT (min): ")
        self.dt_label = wx.StaticText(panel, wx.ID_ANY, u"DT (bins):")
        start_label = wx.StaticText(panel, wx.ID_ANY, u"Min:")
        end_label = wx.StaticText(panel, wx.ID_ANY, u"Max:")
        pusherFreq_label = wx.StaticText(panel, wx.ID_ANY, u"Pusher frequency:")
        scanTime_label = wx.StaticText(panel, wx.ID_ANY, u"Scan time:")
        
        self.extract_mzStart_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                        validator=validator('floatPos')
                                          )
        self.extract_mzStart_value.SetValue(str(self.config.extract_mzStart))
        self.extract_mzStart_value.Bind(wx.EVT_TEXT, self.onApply)
        _extract_mzStart_value = makeSuperTip(self.extract_mzStart_value, **self.help.extract_mz)
        
        self.extract_mzEnd_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                        validator=validator('floatPos'))
        self.extract_mzEnd_value.SetValue(str(self.config.extract_mzEnd))
        self.extract_mzEnd_value.Bind(wx.EVT_TEXT, self.onApply)
        _extract_mzEnd_value = makeSuperTip(self.extract_mzEnd_value, **self.help.extract_mz)
        
        self.extract_rtStart_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                        validator=validator('floatPos'))
        self.extract_rtStart_value.SetValue(str(self.config.extract_rtStart))
        self.extract_rtStart_value.Bind(wx.EVT_TEXT, self.onApply)
        _extract_rtStart_value = makeSuperTip(self.extract_rtStart_value, **self.help.extract_rt)
        
        self.extract_rtEnd_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                        validator=validator('floatPos'))
        self.extract_rtEnd_value.SetValue(str(self.config.extract_rtEnd))
        self.extract_rtEnd_value.Bind(wx.EVT_TEXT, self.onApply)
        _extract_rtEnd_value = makeSuperTip(self.extract_rtEnd_value, **self.help.extract_rt)
        
        self.extract_rt_scans_check = makeCheckbox(panel, u"In scans")
        self.extract_rt_scans_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        self.extract_rt_scans_check.Bind(wx.EVT_CHECKBOX, self.onChangeValidator)
        self.extract_rt_scans_check.Bind(wx.EVT_CHECKBOX, self.enableDisableBoxes)
        _extract_rt_scans_check = makeSuperTip(self.extract_rt_scans_check, **self.help.extract_in_scans)
        
        self.extract_scanTime_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                        validator=validator('floatPos')
                                          )
        self.extract_scanTime_value.SetValue(str(self.parameters.get('scanTime', 1)))
        self.extract_scanTime_value.Bind(wx.EVT_TEXT, self.onApply)
        _extract_scanTime_value = makeSuperTip(self.extract_scanTime_value, **self.help.extract_scanTime)
        
        self.extract_dtStart_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                        validator=validator('floatPos')
                                          )
        self.extract_dtStart_value.SetValue(str(self.config.extract_dtStart))
        self.extract_dtStart_value.Bind(wx.EVT_TEXT, self.onApply)
        _extract_dtStart_value = makeSuperTip(self.extract_dtStart_value, **self.help.extract_dt)
        
        self.extract_dtEnd_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                        validator=validator('floatPos')
                                          )
        self.extract_dtEnd_value.SetValue(str(self.config.extract_dtEnd))
        self.extract_dtEnd_value.Bind(wx.EVT_TEXT, self.onApply)
        _extract_dtEnd_value = makeSuperTip(self.extract_dtEnd_value, **self.help.extract_dt)
        
        self.extract_dt_ms_check = makeCheckbox(panel, u"In ms")
        self.extract_dt_ms_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        self.extract_dt_ms_check.Bind(wx.EVT_CHECKBOX, self.onChangeValidator)
        self.extract_dt_ms_check.Bind(wx.EVT_CHECKBOX, self.enableDisableBoxes)
        _extract_dt_ms_check = makeSuperTip(self.extract_dt_ms_check, **self.help.extract_in_ms)
        
        self.extract_pusherFreq_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                        validator=validator('floatPos')
                                        )
        self.extract_pusherFreq_value.SetValue(str(self.parameters.get('pusherFreq', 1)))
        self.extract_pusherFreq_value.Bind(wx.EVT_TEXT, self.onApply)
        _extract_pusherFreq_value = makeSuperTip(self.extract_pusherFreq_value, **self.help.extract_pusherFreq)
                      
        ms_staticBox = makeStaticBox(panel, "Mass spectrum", size=(-1, -1), color=wx.BLACK)
        ms_staticBox.SetSize((-1,-1))
        ms_box_sizer = wx.StaticBoxSizer(ms_staticBox, wx.HORIZONTAL)       

        self.extract_extractMS_check = makeCheckbox(panel, u"Enable")
        self.extract_extractMS_check.SetValue(self.config.extract_massSpectra)
        self.extract_extractMS_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        self.extract_extractMS_check.Bind(wx.EVT_CHECKBOX, self.enableDisableBoxes)

        self.extract_extractMS_ms_check = makeCheckbox(panel, u"m/z")
        self.extract_extractMS_ms_check.SetValue(False)
        self.extract_extractMS_ms_check.Bind(wx.EVT_CHECKBOX, self.onApply)

        self.extract_extractMS_rt_check = makeCheckbox(panel, u"RT")
        self.extract_extractMS_rt_check.SetValue(True)
        self.extract_extractMS_rt_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        
        self.extract_extractMS_dt_check = makeCheckbox(panel, u"DT")
        self.extract_extractMS_dt_check.SetValue(True)
        self.extract_extractMS_dt_check.Bind(wx.EVT_CHECKBOX, self.onApply)

        rt_staticBox = makeStaticBox(panel, "Chromatogram", size=(-1, -1), color=wx.BLACK)
        rt_staticBox.SetSize((-1,-1))
        rt_box_sizer = wx.StaticBoxSizer(rt_staticBox, wx.HORIZONTAL)

        self.extract_extractRT_check = makeCheckbox(panel, u"Enable")
        self.extract_extractRT_check.SetValue(self.config.extract_chromatograms)
        self.extract_extractRT_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        self.extract_extractRT_check.Bind(wx.EVT_CHECKBOX, self.enableDisableBoxes)

        self.extract_extractRT_ms_check = makeCheckbox(panel, u"m/z")
        self.extract_extractRT_ms_check.SetValue(True)
        self.extract_extractRT_ms_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        
        self.extract_extractRT_dt_check = makeCheckbox(panel, u"DT")
        self.extract_extractRT_dt_check.SetValue(True)
        self.extract_extractRT_dt_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        
        dt_staticBox = makeStaticBox(panel, "Drift time (1D)", size=(-1, -1), color=wx.BLACK)
        dt_staticBox.SetSize((-1,-1))
        dt_box_sizer = wx.StaticBoxSizer(dt_staticBox, wx.HORIZONTAL)

        self.extract_extractDT_check = makeCheckbox(panel, u"Enable")
        self.extract_extractDT_check.SetValue(self.config.extract_driftTime1D)
        self.extract_extractDT_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        self.extract_extractDT_check.Bind(wx.EVT_CHECKBOX, self.enableDisableBoxes)

        self.extract_extractDT_ms_check = makeCheckbox(panel, u"m/z")
        self.extract_extractDT_ms_check.SetValue(True)
        self.extract_extractDT_ms_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        
        self.extract_extractDT_rt_check = makeCheckbox(panel, u"RT")
        self.extract_extractDT_rt_check.SetValue(True)
        self.extract_extractDT_rt_check.Bind(wx.EVT_CHECKBOX, self.onApply)
          
        dt2d_staticBox = makeStaticBox(panel, "Drift time (2D)", size=(-1, -1), color=wx.BLACK)
        dt2d_staticBox.SetSize((-1,-1))
        dt2d_box_sizer = wx.StaticBoxSizer(dt2d_staticBox, wx.HORIZONTAL)           
        
        self.extract_extract2D_check = makeCheckbox(panel, u"Enable")
        self.extract_extract2D_check.SetValue(self.config.extract_driftTime2D)
        self.extract_extract2D_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        self.extract_extract2D_check.Bind(wx.EVT_CHECKBOX, self.enableDisableBoxes)

        self.extract_extract2D_ms_check = makeCheckbox(panel, u"m/z")
        self.extract_extract2D_ms_check.SetValue(True)
        self.extract_extract2D_ms_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        
        self.extract_extract2D_rt_check = makeCheckbox(panel, u"RT")
        self.extract_extract2D_rt_check.SetValue(True)
        self.extract_extract2D_rt_check.Bind(wx.EVT_CHECKBOX, self.onApply)
                   
        horizontal_line = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        
        add_to_document_label = wx.StaticText(panel, wx.ID_ANY, u"Add data to document:")
        self.extract_add_to_document = makeCheckbox(panel, u"")
        self.extract_add_to_document.SetValue(False)
        self.extract_add_to_document.Bind(wx.EVT_CHECKBOX, self.onApply)

        self.extract_extractBtn = wx.Button(panel, wx.ID_OK, "Extract", size=(-1, 22))
        self.extract_cancelBtn = wx.Button(panel, wx.ID_OK, "Cancel", size=(-1, 22))

        self.extract_extractBtn.Bind(wx.EVT_BUTTON, self.onExtractData)
        self.extract_cancelBtn.Bind(wx.EVT_BUTTON, self.onClose)
        
        # pack elements
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(extractData_sep_label, (n,0), wx.GBSpan(1,3), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
        n = n + 1
        grid.Add(start_label, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        grid.Add(end_label, (n,2), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        n = n + 1
        grid.Add(self.mz_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.extract_mzStart_value, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.extract_mzEnd_value, (n,2), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(self.rt_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.extract_rtStart_value, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.extract_rtEnd_value, (n,2), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.extract_rt_scans_check, (n,3), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(scanTime_label, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.extract_scanTime_value, (n,2), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(self.dt_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.extract_dtStart_value, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.extract_dtEnd_value, (n,2), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.extract_dt_ms_check, (n,3), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(pusherFreq_label, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.extract_pusherFreq_value, (n,2), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(self.extract_extractMS_check, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(self.extract_extractRT_check, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(self.extract_extractDT_check, (n,2), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(self.extract_extract2D_check, (n,3), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_HORIZONTAL)

        # extract MS
        extract_ms_grid = wx.GridBagSizer(2, 2)
        extract_ms_grid.Add(self.extract_extractMS_ms_check, (0,0), wx.GBSpan(1,1), flag=wx.EXPAND)
        extract_ms_grid.Add(self.extract_extractMS_rt_check, (1,0), wx.GBSpan(1,1), flag=wx.EXPAND)
        extract_ms_grid.Add(self.extract_extractMS_dt_check, (2,0), wx.GBSpan(1,1), flag=wx.EXPAND)
        ms_box_sizer.Add(extract_ms_grid, 0, wx.EXPAND, 10)
        
        # extract RT
        extract_rt_grid = wx.GridBagSizer(2, 2)
        extract_rt_grid.Add(self.extract_extractRT_ms_check, (0,0), wx.GBSpan(1,1), flag=wx.EXPAND)
        extract_rt_grid.Add(self.extract_extractRT_dt_check, (1,0), wx.GBSpan(1,1), flag=wx.EXPAND)
        rt_box_sizer.Add(extract_rt_grid, 0, wx.EXPAND, 10)
        
        # extract DT
        extract_dt_grid = wx.GridBagSizer(2, 2)
        extract_dt_grid.Add(self.extract_extractDT_ms_check, (0,0), wx.GBSpan(1,1), flag=wx.EXPAND)
        extract_dt_grid.Add(self.extract_extractDT_rt_check, (1,0), wx.GBSpan(1,1), flag=wx.EXPAND)
        dt_box_sizer.Add(extract_dt_grid, 0, wx.EXPAND, 10)
        
        # extract 2D
        extract_2d_grid = wx.GridBagSizer(2, 2)
        extract_2d_grid.Add(self.extract_extract2D_ms_check, (0,0), wx.GBSpan(1,1), flag=wx.EXPAND)
        extract_2d_grid.Add(self.extract_extract2D_rt_check, (1,0), wx.GBSpan(1,1), flag=wx.EXPAND)
        dt2d_box_sizer.Add(extract_2d_grid, 0, wx.EXPAND, 10)
        
        n = n + 1
        grid.Add(ms_box_sizer, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(rt_box_sizer, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(dt_box_sizer, (n,2), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(dt2d_box_sizer, (n,3), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_HORIZONTAL)
        n = n + 1
        grid.Add(horizontal_line, (n,0), wx.GBSpan(1,4), flag=wx.EXPAND)
        n = n + 1
        grid.Add(add_to_document_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.extract_add_to_document, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(self.extract_extractBtn, (n,1), wx.GBSpan(1,1))
        grid.Add(self.extract_cancelBtn, (n,2), wx.GBSpan(1,1))
        
        mainSizer.Add(grid, 0, wx.ALIGN_CENTER_HORIZONTAL, 10)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizerAndFit(mainSizer)

        return panel
                
    def onRunUnidec(self, evt):
        
        # get event ID
        if isinstance(evt, int):
            evtID = evt
        else:
            evtID = evt.GetId()
        
        try:
            print("Processing document: {} and {} dataset".format(self.document['MS'], self.dataset['MS']))
        except: pass
        
        data, document, document_title = self.get_unidec_data(data_type="document_all")
        
        if "temporary_unidec" in data:
            self.config.unidec_engine = data['temporary_unidec']
        else:
            self.config.unidec_engine = unidec.UniDec()
            self.config.unidec_engine.config.UniDecPath = self.config.unidec_path
            
        self.config.unidec_maxIterations = str2int(self.unidec_maxIters_value.GetValue())
        
        # set maximum number of iterations
        self.config.unidec_engine.config.numit = self.config.unidec_maxIterations
         
        if evtID in [ID_processSettings_autoUniDec, ID_processSettings_loadDataUniDec]:
            self.presenter.view.panelPlots.on_clear_unidec()
            
            # reshape spectra
            msX = data['xvals']
            msY = data['yvals']
            
            file_name = "".join([document.title, ".txt"])
            folder = document.path
            self.config.unidec_engine.open_file(file_name=file_name, 
                                                file_directory=folder, 
                                                data_in=np.transpose([msX, msY]))
        
        if evtID in [ID_processSettings_preprocessUniDec, ID_processSettings_autoUniDec, ID_processSettings_runAll]:
            # preprocess
            self.config.unidec_engine.config.minmz = self.config.unidec_mzStart
            self.config.unidec_engine.config.maxmz = self.config.unidec_mzEnd
            self.config.unidec_engine.config.mzbins = self.config.unidec_mzBinSize
            self.config.unidec_engine.config.smooth = self.config.unidec_gaussianFilter
            self.config.unidec_engine.config.accvol = self.config.unidec_accelerationV
            self.config.unidec_engine.config.linflag = self.config.unidec_linearization_choices[self.config.unidec_linearization]
            self.config.unidec_engine.config.cmap = self.config.currentCmap
            
            self.presenter.view.panelPlots.on_clear_unidec(which="all")
            # preprocess
            try:
                self.config.unidec_engine.process_data()
            except IndexError:
                print("No data was loaded. Trying to load it automatically")
                self.onRunUnidec(evt=ID_processSettings_loadDataUniDec)
                return
            
        if evtID in [ID_processSettings_runUniDec, ID_processSettings_runAll]:
            # unidec engine 
            self.config.unidec_engine.config.masslb = self.config.unidec_mwStart
            self.config.unidec_engine.config.massub = self.config.unidec_mwEnd
            self.config.unidec_engine.config.massbins = self.config.unidec_mwFrequency
            
            self.config.unidec_engine.config.startz = self.config.unidec_zStart
            self.config.unidec_engine.config.endz = self.config.unidec_zEnd
            self.config.unidec_engine.config.numz = self.config.unidec_zEnd - self.config.unidec_zStart
            
            self.config.unidec_engine.config.psfun = self.config.unidec_peakFunction_choices[self.config.unidec_peakFunction]
            
            if self.config.unidec_peakWidth_auto:
                self.config.unidec_engine.get_auto_peak_width()
                self.unidec_fit_peakWidth_value.SetValue(str(self.config.unidec_engine.config.mzsig))
            else:
                self.config.unidec_engine.config.mzsig = self.config.unidec_peakWidth
            
            self.presenter.view.panelPlots.on_clear_unidec(which="run")
            try:
                self.config.unidec_engine.run_unidec()
            except IndexError:
                dlgBox(exceptionTitle="Error",
                       exceptionMsg="Load and pre-process data first", 
                       type="Error")
                return
            except ValueError:
                print("Could not perform task")
                return
            
        if evtID in [ID_processSettings_pickPeaksUniDec, ID_processSettings_runAll]:
            # peak finding
            self.config.unidec_engine.config.peaknorm = self.config.unidec_peakNormalization_choices[self.config.unidec_peakNormalization]
            self.config.unidec_engine.config.peakwindow = self.config.unidec_peakDetectionWidth
            self.config.unidec_engine.config.peakthresh = self.config.unidec_peakDetectionThreshold
            self.config.unidec_engine.config.separation = self.config.unidec_lineSeparation
            
            self.presenter.view.panelPlots.on_clear_unidec(which="detect")
            try:
                self.config.unidec_engine.pick_peaks()  
            except (ValueError, ZeroDivisionError):
                print("Failed to find peaks. Try increasing the value of Peak detection range (Da)")
                return
            except IndexError:
                dlgBox(exceptionTitle="Error",
                       exceptionMsg="Please run UniDec first", 
                       type="Error")
                return
            
            try:
                self.config.unidec_engine.convolve_peaks()
            except OverflowError:
                print("Too many peaks! Try reprocessing your data with larger peak width or larger bin size.")
                return
            
        if evtID == ID_processSettings_isolateZUniDec:
            try:
                self.config.unidec_engine.pick_peaks()
            except (ValueError, ZeroDivisionError):
                print("Failed to find peaks. Try increasing the value of Peak detection range (Da)")
                return
            except IndexError:
                dlgBox(exceptionTitle="Error",
                       exceptionMsg="Please run UniDec first", 
                       type="Error")
                return
            try:
                self.config.unidec_engine.convolve_peaks()
            except OverflowError:
                print("Too many peaks! Try reprocessing your data with larger peak width or larger bin size.")
                return

        if evtID == ID_processSettings_autoUniDec:
            self.config.unidec_engine.autorun()
            self.config.unidec_engine.convolve_peaks()
            
        # plot data
#         try:
        self.onPlotUnidec(evtID)
#         except:
#             print("Something went wrong")
#             return
        
        self.onAddUnidecData(evtID, document_title)
        
    def onPlotUnidec(self, evtID):
        
        self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['UniDec'])
        if not isinstance(evtID, int):
            source = evtID.GetEventObject().GetName()
            evtID = evtID.GetId()
            if source == 'ChargeStates': evtID = ID_processSettings_showZUniDec
            
        self.config.unidec_speedy = self.unidec_speedy_check.GetValue()
        
        kwargs = {'show_markers':self.config.unidec_show_markers,
                  'show_individual_lines':self.config.unidec_show_individualComponents,
                  'speedy':self.config.unidec_speedy}
        
        if evtID in [ID_processSettings_preprocessUniDec, ID_processSettings_autoUniDec, ID_processSettings_runAll]:
            self.presenter.view.panelPlots.on_plot_unidec_MS(self.config.unidec_engine.data, **kwargs)
            
        if evtID in [ID_processSettings_runUniDec, ID_processSettings_runAll]:
            self.presenter.view.panelPlots.on_plot_unidec_MS_v_Fit(self.config.unidec_engine.data, **kwargs)
            self.presenter.view.panelPlots.on_plot_unidec_mwDistribution(self.config.unidec_engine.data, **kwargs)
            self.presenter.view.panelPlots.on_plot_unidec_mzGrid(self.config.unidec_engine.data, **kwargs)
            self.presenter.view.panelPlots.on_plot_unidec_MW_v_Charge(self.config.unidec_engine.data, **kwargs)
            
        if evtID in [ID_processSettings_pickPeaksUniDec, ID_processSettings_runAll]:
            self.presenter.view.panelPlots.on_plot_unidec_individualPeaks(self.config.unidec_engine, **kwargs)
            self.presenter.view.panelPlots.on_plot_unidec_barChart(self.config.unidec_engine, **kwargs)
            
            massList, massMax = self.get_unidec_data(data_type="MassList")
            self.unidec_weightList_choice.SetItems(massList)
            self.unidec_weightList_choice.SetStringSelection(massMax) 
        
        if evtID == ID_processSettings_autoUniDec:
            self.presenter.view.panelPlots.on_plot_unidec_MS_v_Fit(self.config.unidec_engine.data, **kwargs)
            self.presenter.view.panelPlots.on_plot_unidec_mwDistribution(self.config.unidec_engine.data, **kwargs)
            self.presenter.view.panelPlots.on_plot_unidec_mzGrid(self.config.unidec_engine.data, **kwargs)
            self.presenter.view.panelPlots.on_plot_unidec_MW_v_Charge(self.config.unidec_engine.data, **kwargs)
            self.presenter.view.panelPlots.on_plot_unidec_individualPeaks(self.config.unidec_engine, **kwargs)
            self.presenter.view.panelPlots.on_plot_unidec_barChart(self.config.unidec_engine, **kwargs)
            
        if evtID == ID_processSettings_replotUniDec:
            self.presenter.view.panelPlots.on_plot_unidec_mzGrid(self.config.unidec_engine.data, **kwargs)
            self.presenter.view.panelPlots.on_plot_unidec_MW_v_Charge(self.config.unidec_engine.data, **kwargs)
            
        if evtID == ID_processSettings_showZUniDec:
            try:
                charges = self.config.unidec_engine.get_charge_peaks()
                self.presenter.view.panelPlots.on_plot_unidec_ChargeDistribution(charges[:,0], charges[:,1], **kwargs)
                selection = self.unidec_weightList_choice.GetStringSelection().split()[1]
                adductIon = self.unidec_adductMW_choice.GetStringSelection()
                peakpos, charges, intensity = self._calculate_charge_positions(charges, selection, adductIon)
                self.presenter.view.panelPlots.on_plot_charge_states(peakpos, charges, **kwargs)
                
#                 if self.unidec_isolateCharges_check.GetValue():
#                     try:
#                         mw_selection = "MW: {}".format(self.unidec_weightList_choice.GetStringSelection().split()[1])
#                     except: pass
#                     kwargs['show_isolated_mw'] = True
#                     kwargs['mw_selection'] = mw_selection
#                     self.presenter.view.panelPlots.on_plot_unidec_individualPeaks(self.config.unidec_engine, **kwargs)
            except: 
                dlgBox(exceptionTitle="Error",
                       exceptionMsg="Could not complete action. Pick peaks first?", 
                       type="Error")
                return
        if evtID == ID_processSettings_isolateZUniDec:
            try:
                mw_selection = "MW: {}".format(self.unidec_weightList_choice.GetStringSelection().split()[1])
            except: return
            kwargs['show_isolated_mw'] = True
            kwargs['mw_selection'] = mw_selection
            
            data, __, __ = self.get_unidec_data(data_type="document_all")
            
            self.presenter.view.panelPlots.on_plot_unidec_individualPeaks(unidec_eng_data=None,
                                                                          replot=data['unidec']['m/z with isolated species'], 
                                                                          **kwargs)
            
        if evtID == ID_processSettings_replotAll:
            data, __, __ = self.get_unidec_data(data_type="document_all")
            try: self.presenter.view.panelPlots.on_plot_unidec_MS_v_Fit(self.config.unidec_engine.data, **kwargs)
            except: print("Failed to plot MS vs Fit plot")
            try: self.presenter.view.panelPlots.on_plot_unidec_mwDistribution(self.config.unidec_engine.data, **kwargs)
            except: print("Failed to plot MW distribution plot")
            try: self.presenter.view.panelPlots.on_plot_unidec_mzGrid(self.config.unidec_engine.data, **kwargs)
            except: print("Failed to plot m/z vs charge plot")
            try: self.presenter.view.panelPlots.on_plot_unidec_MW_v_Charge(self.config.unidec_engine.data, **kwargs)
            except: print("Failed to plot MW vs charge plot")
            try: self.presenter.view.panelPlots.on_plot_unidec_individualPeaks(unidec_eng_data=None,
                                                                                replot=data['unidec']['m/z with isolated species'], 
                                                                                **kwargs)
            except: print("Failed to plot individual MS plot")
            try: self.presenter.view.panelPlots.on_plot_unidec_barChart(unidec_eng_data=None,
                                                                        replot=data['unidec']['Barchart'], 
                                                                        **kwargs)
            except: print("Failed to plot barplot")
        
    def _calculate_charge_positions(self, chargeList, selectedMW, adductIon="H+"):
        
        _adducts = {'H+':1.007276467, 'Na+':22.989218, 'K+':38.963158, 'NH4+':18.033823,
                    'H-': -1.007276, 'Cl-':34.969402}
        
        min_mz, max_mz = np.min(self.config.unidec_engine.data.data2[:, 0]), np.max(self.config.unidec_engine.data.data2[:, 0])
        charges = np.arange(self.config.unidec_zStart, self.config.unidec_zEnd + 1)
        peakpos = (float(selectedMW) + charges * _adducts[adductIon]) / charges
        ignore = (peakpos > min_mz) & (peakpos < max_mz)
        peakpos, charges, intensity = peakpos[ignore], charges[ignore], chargeList[:,1][ignore]
        return peakpos, charges, intensity
        
    def onAddUnidecData(self, evtID, document_title=None):
               
        # export current MS to file
        if 'MS' in self.document:
            document_title = self.document['MS']
        else:
            document_title = self.presenter.view.panelDocuments.topP.documents.enableCurrentDocument()
            
        try:
            document = self.presenter.documentsDict[document_title]
        except KeyError: 
            dlgBox(exceptionTitle="Error",
                   exceptionMsg="Please create or load a document first", 
                   type="Error")
            return
        
        # initilise data in the mass spectrum dictionary
        if 'MS' in self.dataset:
            if self.dataset['MS'] == 'Mass Spectrum':
                if 'unidec' not in document.massSpectrum:
                    document.massSpectrum['unidec'] = {}
                data = document.massSpectrum
            elif self.dataset['MS'] == "Mass Spectrum (processed)":
                data = document.smoothMS
                if 'unidec' not in document.smoothMS:
                    document.smoothMS['unidec'] = {}
            else:
                if 'unidec' not in document.multipleMassSpectrum[self.dataset['MS']]:
                    document.multipleMassSpectrum[self.dataset['MS']]['unidec'] = {}
                data = document.multipleMassSpectrum[self.dataset['MS']]
        else:
            if not document.gotMS:
                dlgBox(exceptionTitle="Error",
                       exceptionMsg="Document must have mass spectrum", 
                       type="Error")
                return
            if 'unidec' not in document.massSpectrum:
                document.massSpectrum['unidec'] = {}
            data = document.massSpectrum

        
        if evtID in [ID_processSettings_preprocessUniDec, ID_processSettings_autoUniDec, ID_processSettings_runAll]:
            raw_data = {'xvals':self.config.unidec_engine.data.data2[:, 0],
                        'yvals':self.config.unidec_engine.data.data2[:, 1],
                        'color':[0,0,0], 'label':"Data", 'xlabels':"m/z", 
                        'ylabels':"Intensity"}
            # add data
            data['unidec']['Processed'] = raw_data
            
        if evtID in [ID_processSettings_runUniDec, ID_processSettings_runAll]:
            fit_data = {'xvals':[self.config.unidec_engine.data.data2[:, 0], 
                                 self.config.unidec_engine.data.data2[:, 0]],
                        'yvals':[self.config.unidec_engine.data.data2[:, 1], 
                                 self.config.unidec_engine.data.fitdat],
                        'colors':[[0,0,0], [1,0,0]], 'labels':['Data', 'Fit Data'],
                        'xlabel':"m/z", 'ylabel':"Intensity", 
                        'xlimits':[np.min(self.config.unidec_engine.data.data2[:, 0]), 
                                   np.max(self.config.unidec_engine.data.data2[:, 0])]}
            
            mw_distribution_data = {'xvals':self.config.unidec_engine.data.massdat[:, 0],
                                    'yvals':self.config.unidec_engine.data.massdat[:, 1],
                                    'color':[0,0,0], 'label':"Data", 'xlabels':"Mass (Da)",
                                    'ylabels':"Intensity"}
            mz_grid_data = {'grid':self.config.unidec_engine.data.mzgrid,
                            'xlabels':" m/z (Da)", 'ylabels':"Charge",
                            'cmap':self.config.unidec_engine.config.cmap}
            mw_v_z_data = {'xvals':self.config.unidec_engine.data.massdat[:, 0],
                           'yvals':self.config.unidec_engine.data.ztab,
                           'zvals':self.config.unidec_engine.data.massgrid,
                           'xlabels':"Mass (Da)", 'ylabels':"Charge",
                           'cmap':self.config.unidec_engine.config.cmap}
            # add data
            data['unidec']['Fitted'] = fit_data
            data['unidec']['MW distribution'] = mw_distribution_data
            data['unidec']['m/z vs Charge'] = mz_grid_data
            data['unidec']['MW vs Charge'] = mw_v_z_data
        if evtID in [ID_processSettings_pickPeaksUniDec, ID_processSettings_runAll]:
            # individually plotted
            individual_dict = self.get_unidec_data(data_type="Individual MS")
            barchart_dict = self.get_unidec_data(data_type="Barchart")
            massList, massMax = self.get_unidec_data(data_type="MassList")
            individual_dict['_massList_'] = [massList, massMax] 
            
            # add data
            data['unidec']['m/z with isolated species'] = individual_dict
            data['unidec']['Barchart'] = barchart_dict
            data['unidec']['Charge information'] = self.config.unidec_engine.get_charge_peaks()
        
        data['temporary_unidec'] = self.config.unidec_engine
            
        # update data dictionary
        if 'MS' in self.dataset:
            if self.dataset['MS'] == 'Mass Spectrum':
                document.massSpectrum = data
            else:
                document.multipleMassSpectrum[self.dataset['MS']] = data
        else:
            document.massSpectrum = data
            
        # update document
        if 'MS' in self.dataset and self.dataset['MS'] != "Mass Spectrum":
            self.presenter.OnUpdateDocument(document, expand_item="mass_spectra",
                                            expant_item_title=self.dataset['MS'])
        else:
            self.presenter.OnUpdateDocument(document, expand_item="document")
        
    def get_unidec_data(self, data_type="Individual MS", **kwargs):
        if data_type == "Individual MS":   
            stickmax = 1.0
            num = 0
            individual_dict = dict()
            legend_text = [[[0,0,0], "Raw"]]
            colors = []
            labels = []
            for i in range(0, self.config.unidec_engine.pks.plen):
                p = self.config.unidec_engine.pks.peaks[i]
                if p.ignore == 0:
                    list1, list2 = [], []
                    if (not isempty(p.mztab)) and (not isempty(p.mztab2)):
                        mztab = np.array(p.mztab)
                        mztab2 = np.array(p.mztab2)
                        maxval = np.amax(mztab[:, 1])
                        for k in range(0, len(mztab)):
                            if mztab[k, 1] > self.config.unidec_engine.config.peakplotthresh * maxval:
                                list1.append(mztab2[k, 0])
                                list2.append(mztab2[k, 1])
                                
                        if self.config.unidec_engine.pks.plen <= 16:
                            color=convertRGB255to1(self.config.customColors[i])
                        else:
                            color=p.color
                        colors.append(color)
                        labels.append("MW: {:.2f}".format(p.mass))
                        legend_text.append([color, "MW: {:.2f}".format(p.mass)])
                        individual_dict["MW: {:.2f}".format(p.mass)] = {'scatter_xvals':np.array(list1),
                                                                        'scatter_yvals':np.array(list2),
                                                                        'marker':p.marker, 
                                                                        'color':color,
                                                                        'label':"MW: {:.2f}".format(p.mass),
                                                                        'line_xvals':self.config.unidec_engine.data.data2[:, 0],
                                                                        'line_yvals':np.array(p.stickdat)/stickmax-(num + 1) * self.config.unidec_engine.config.separation
                                                                        }
                        num += 1
            individual_dict['legend_text'] = legend_text
            individual_dict['xvals'] = self.config.unidec_engine.data.data2[:, 0]
            individual_dict['yvals'] = self.config.unidec_engine.data.data2[:, 1]
            individual_dict['xlabel'] = "m/z (Da)"
            individual_dict['ylabel'] = "Intensity"
            individual_dict['colors'] = colors
            individual_dict['labels'] = labels
            return individual_dict
        elif data_type == 'MassList':
            mwList, heightList = [], []
            for i in range(0, self.config.unidec_engine.pks.plen):
                p = self.config.unidec_engine.pks.peaks[i]
                if p.ignore == 0:
                    mwList.append("MW: {:.2f} ({:.2f} %)".format(p.mass, p.height))
                    heightList.append(p.height)
            return mwList, mwList[heightList.index(np.max(heightList))]
        elif data_type == 'Barchart':
            if self.config.unidec_engine.pks.plen > 0:
                num = 0
                yvals, colors, labels, legend_text, markers, legend = [], [], [], [], [], []
                for p in self.config.unidec_engine.pks.peaks:
                    if p.ignore == 0:
                        yvals.append(p.height)
                        if self.config.unidec_engine.pks.plen <= 15:
                            color = convertRGB255to1(self.config.customColors[num])
                        else:
                            color = p.color
                        markers.append(p.marker)
                        labels.append(p.label)
                        colors.append(color)
                        legend_text.append([color, "MW: {:.2f}".format(p.mass)])
                        legend.append("MW: {:.2f}".format(p.mass))
                        num += 1
                    xvals = range(0, num)
                    barchart_dict = {'xvals':xvals,
                                     'yvals':yvals,
                                     'labels':labels,
                                     'colors':colors,
                                     'legend':legend,
                                     'legend_text':legend_text,
                                     'markers':markers}
#                 for k, v in vars(p).items():
#                   print k, v
                return barchart_dict
        elif data_type == 'unidec_all':
            if 'MS' in self.document:
                document_title = self.document['MS']
            else:
                document_title = self.presenter.view.panelDocuments.topP.documents.enableCurrentDocument()
                
            try:
                document = self.presenter.documentsDict[document_title]
            except KeyError: 
                if kwargs.get("notify_of_error", True):
                    dlgBox(exceptionTitle="Error",
                           exceptionMsg="Please create or load a document first", 
                           type="Error")
                return
            
            if 'MS' in self.dataset:
                if self.dataset['MS'] == 'Mass Spectrum':
                    data = document.massSpectrum['unidec']
                else:
                    data = document.multipleMassSpectrum[self.dataset['MS']]['unidec']
            else:
                if not document.gotMS:
                    if kwargs.get("notify_of_error", True):
                        dlgBox(exceptionTitle="Error",
                               exceptionMsg="Document must have mass spectrum", 
                               type="Error")
                    return
                data = document.massSpectrum['unidec']

            return data, document, document_title

        elif data_type == 'document_all':
            
            if 'MS' in self.document:
                document_title = self.document['MS']
            else:
                document_title = self.presenter.view.panelDocuments.topP.documents.enableCurrentDocument()
                
            try:
                document = self.presenter.documentsDict[document_title]
            except KeyError: 
                if kwargs.get("notify_of_error", True):
                    dlgBox(exceptionTitle="Error",
                           exceptionMsg="Please create or load a document first", 
                           type="Error")
                return
        
            if 'MS' in self.dataset:
                if self.dataset['MS'] == 'Mass Spectrum':
                    data = document.massSpectrum
                elif self.dataset['MS'] == "Mass Spectrum (processed)":
                    data = document.smoothMS
                else:
                    data = document.multipleMassSpectrum[self.dataset['MS']]
            else:
                if not document.gotMS:
                    if kwargs.get("notify_of_error", True):
                        dlgBox(exceptionTitle="Error",
                               exceptionMsg="Document must have mass spectrum", 
                               type="Error")
                    return
                data = document.massSpectrum
                                
            return data, document, document_title
        
        elif data_type == 'document_info':
            
            if 'MS' in self.document:
                document_title = self.document['MS']
            else:
                document_title = self.presenter.view.panelDocuments.topP.documents.enableCurrentDocument()
                
            try:
                document = self.presenter.documentsDict[document_title]
            except KeyError: 
                if kwargs.get("notify_of_error", True):
                    dlgBox(exceptionTitle="Error",
                           exceptionMsg="Please create or load a document first", 
                           type="Error")
                return
            
            return document, document_title
            
    def onApply(self, evt):
        # prevent updating config
        
        if self.importEvent: return
        # UniDec
        self.config.unidec_mzStart = str2num(self.unidec_mzStart_value.GetValue())
        self.config.unidec_mzEnd = str2num(self.unidec_mzEnd_value.GetValue())
        self.config.unidec_mzBinSize = str2num(self.unidec_mzBinSize_value.GetValue())
        self.config.unidec_gaussianFilter = str2num(self.unidec_gaussianFilter_value.GetValue())
        self.config.unidec_accelerationV = str2num(self.unidec_accelerationV_value.GetValue())
        self.config.unidec_linearization = self.unidec_linearization_choice.GetStringSelection()
        
        self.config.unidec_zStart = str2int(self.unidec_zStart_value.GetValue())
        self.config.unidec_zEnd = str2int(self.unidec_zEnd_value.GetValue())
        self.config.unidec_mwStart = str2num(self.unidec_mwStart_value.GetValue())
        self.config.unidec_mwEnd = str2num(self.unidec_mwEnd_value.GetValue())
        self.config.unidec_mwFrequency = str2num(self.unidec_mw_sampleFrequency_value.GetValue())
        self.config.unidec_peakWidth = str2num(self.unidec_fit_peakWidth_value.GetValue())
        self.config.unidec_peakFunction = self.unidec_peakFcn_choice.GetStringSelection()
        self.config.unidec_peakWidth_auto = self.unidec_fit_peakWidth_check.GetValue()
        
        self.config.unidec_peakDetectionWidth = str2num(self.unidec_peakWidth_value.GetValue())
        self.config.unidec_peakDetectionThreshold = str2num(self.unidec_peakThreshold_value.GetValue())
        self.config.unidec_peakNormalization = self.unidec_peakNormalization_choice.GetStringSelection()
        self.config.unidec_lineSeparation = str2num(self.unidec_lineSeparation_value.GetValue())
        
        self.config.unidec_show_markers = self.unidec_markers_check.GetValue()
        self.config.unidec_speedy = self.unidec_speedy_check.GetValue()
        self.config.unidec_show_individualComponents = self.unidec_individualComponents_check.GetValue()
#         self.config.unidec_show_chargeStates = self.unidec_chargeStates_check.GetValue()
        
        # Extract        
        self.config.extract_mzStart = str2num(self.extract_mzStart_value.GetValue())
        self.config.extract_mzEnd = str2num(self.extract_mzEnd_value.GetValue())
        self.config.extract_rtStart = str2num(self.extract_rtStart_value.GetValue())
        self.config.extract_rtEnd = str2num(self.extract_rtEnd_value.GetValue())
        self.config.extract_dtStart = str2num(self.extract_dtStart_value.GetValue())
        self.config.extract_dtEnd = str2num(self.extract_dtEnd_value.GetValue())
        
        # Mass spectrum
        self.config.ms_process_linearize = self.ms_process_linearize.GetValue()
        self.config.ms_process_smooth = self.ms_process_smooth.GetValue()
        self.config.ms_process_threshold = self.ms_process_threshold.GetValue()
        self.config.ms_process_normalize = self.ms_process_normalize.GetValue()
        
        self.config.ms_mzStart = str2num(self.bin_mzStart_value.GetValue())
        self.config.ms_mzEnd = str2num(self.bin_mzEnd_value.GetValue())
        self.config.ms_mzBinSize = str2num(self.bin_mzBinSize_value.GetValue())
        self.config.ms_enable_in_RT = self.bin_RT_window_check.GetValue()
        self.config.ms_enable_in_MML_start = self.bin_MML_window_check.GetValue()
        self.config.ms_dtmsBinSize = str2num(self.bin_msdt_binSize_value.GetValue())
        
        self.config.ms_linearization_mode = self.bin_linearizationMode_choice.GetStringSelection()
        self.config.ms_auto_range = self.bin_autoRange_check.GetValue()
        
        self.config.ms_normalize = self.ms_normalizeTgl.GetValue()
        self.config.ms_normalize_mode = self.ms_normalizeFcn_choice.GetStringSelection()
        self.config.ms_smooth_mode = self.ms_smoothFcn_choice.GetStringSelection()
        self.config.ms_smooth_sigma = str2num(self.ms_sigma_value.GetValue())
        self.config.ms_smooth_window = str2int(self.ms_window_value.GetValue())
        self.config.ms_smooth_polynomial = str2int(self.ms_polynomial_value.GetValue())
        self.config.ms_threshold = str2num(self.ms_threshold_value.GetValue())
        
        # 2D
        self.config.plot2D_normalize = self.plot2D_normalizeTgl.GetValue()
        self.config.plot2D_normalize_mode = self.plot2D_normalizeFcn_choice.GetStringSelection()
        self.config.plot2D_smooth_mode = self.plot2D_smoothFcn_choice.GetStringSelection()
        self.config.plot2D_smooth_sigma = str2num(self.plot2D_sigma_value.GetValue())
        self.config.plot2D_smooth_window = str2int(self.plot2D_window_value.GetValue())
        self.config.plot2D_smooth_polynomial = str2int(self.plot2D_polynomial_value.GetValue())
        self.config.plot2D_threshold = str2num(self.plot2D_threshold_value.GetValue())
        
        # ORIGAMI
        self.config.origami_acquisition = self.origami_method_choice.GetStringSelection()
        self.config.origami_startScan = str2int(self.origami_startScan_value.GetValue())
        self.config.origami_spv = str2int(self.origami_scansPerVoltage_value.GetValue())
        self.config.origami_startVoltage = str2num(self.origami_startVoltage_value.GetValue())
        self.config.origami_endVoltage = str2num(self.origami_endVoltage_value.GetValue())
        self.config.origami_stepVoltage = str2num(self.origami_stepVoltage_value.GetValue())
        self.config.origami_boltzmannOffset = str2num(self.origami_boltzmannOffset_value.GetValue())
        self.config.origami_exponentialPercentage = str2num(self.origami_exponentialPercentage_value.GetValue())
        self.config.origami_exponentialIncrement = str2num(self.origami_exponentialIncrement_value.GetValue())
        
        # Peak fitting
        self.config.fit_highlight = self.fit_highlight_check.GetValue()
        self.config.fit_addPeaks = self.fit_addPeaks_check.GetValue()
        self.config.fit_xaxis_limit = self.fit_xaxisLimit_check.GetValue()
        self.config.fit_type = self.fit_fitPlot_choice.GetStringSelection()
        self.config.fit_threshold = str2num(self.fit_threshold_value.GetValue())
        self.config.fit_window = str2int(self.fit_window_value.GetValue())
        self.config.fit_width = str2num(self.fit_width_value.GetValue())
        self.config.fit_asymmetric_ratio = str2num(self.fit_asymmetricRatio_value.GetValue())
        self.config.fit_smoothPeaks = self.fit_smooth_check.GetValue()
        self.config.fit_smooth_sigma = str2num(self.fit_sigma_value.GetValue())
        self.config.fit_highRes = self.fit_highRes_check.GetValue()
        self.config.fit_highRes_threshold = str2num(self.fit_thresholdHighRes_value.GetValue())
        self.config.fit_highRes_window = str2int(self.fit_windowHighRes_value.GetValue())
        self.config.fit_highRes_width = str2num(self.fit_widthHighRes_value.GetValue())
        self.config.fit_highRes_isotopicFit = self.fit_isotopes_check.GetValue()

    def enableDisableBoxes(self, evt):
        
        if self.bin_autoRange_check.GetValue():
            self.bin_mzStart_value.Disable()
            self.bin_mzEnd_value.Disable()
        else:
            self.bin_mzStart_value.Enable()
            self.bin_mzEnd_value.Enable()
            
        # check if MS process data is present
        if self.document.get('MS', None) == None or self.dataset.get('MS', None) == None:
            self.ms_processBtn.Disable()
        else:
            self.ms_processBtn.Enable()
        
        # check if 2D process data is present
        if self.document.get('2D', None) == None or self.dataset.get('2D', None) == None:
            self.plot2D_processBtn.Disable()
        else:
            self.plot2D_processBtn.Enable()
            
        # extract panel
        enableDisable_MS = [self.extract_extractMS_dt_check, self.extract_extractMS_rt_check,
                            self.extract_extractMS_ms_check]
        if self.extract_extractMS_check.GetValue(): 
            for item in enableDisable_MS: item.Enable()
        else: 
            for item in enableDisable_MS: item.Disable()
            
        enableDisable_RT = [self.extract_extractRT_dt_check, self.extract_extractRT_ms_check]
        if self.extract_extractRT_check.GetValue(): 
            for item in enableDisable_RT: item.Enable()
        else: 
            for item in enableDisable_RT: item.Disable()
            
        enableDisable_DT = [self.extract_extractDT_ms_check, self.extract_extractDT_rt_check]
        if self.extract_extractDT_check.GetValue(): 
            for item in enableDisable_DT: item.Enable()
        else: 
            for item in enableDisable_DT: item.Disable()
            
        enableDisable_2D = [self.extract_extract2D_ms_check, self.extract_extract2D_rt_check]
        if self.extract_extract2D_check.GetValue(): 
            for item in enableDisable_2D: item.Enable()
        else: 
            for item in enableDisable_2D: item.Disable()
            
        if self.extract_rt_scans_check.GetValue(): self.extract_scanTime_value.Enable()
        else: self.extract_scanTime_value.Disable()
        
        if self.extract_dt_ms_check.GetValue(): self.extract_pusherFreq_value.Enable()
        else: self.extract_pusherFreq_value.Disable()  
        
        # origami panel
        self.config.origami_acquisition = self.origami_method_choice.GetStringSelection()
        if self.config.origami_acquisition == 'Linear':
            enableList = [self.origami_startScan_value, self.origami_startVoltage_value, 
                          self.origami_endVoltage_value, self.origami_stepVoltage_value, 
                          self.origami_scansPerVoltage_value]
            disableList = [self.origami_boltzmannOffset_value, self.origami_exponentialIncrement_value, 
                           self.origami_exponentialPercentage_value, self.origami_loadListBtn]
        elif self.config.origami_acquisition == 'Exponential':
            enableList = [self.origami_startScan_value, self.origami_startVoltage_value, 
                          self.origami_endVoltage_value, self.origami_stepVoltage_value, 
                          self.origami_scansPerVoltage_value, self.origami_exponentialIncrement_value, 
                           self.origami_exponentialPercentage_value]
            disableList = [self.origami_boltzmannOffset_value,  self.origami_loadListBtn]
        elif self.config.origami_acquisition == 'Boltzmann':
            enableList = [self.origami_startScan_value, self.origami_startVoltage_value, 
                          self.origami_endVoltage_value, self.origami_stepVoltage_value, 
                          self.origami_scansPerVoltage_value, self.origami_boltzmannOffset_value]
            disableList = [self.origami_exponentialIncrement_value, self.origami_exponentialPercentage_value,
                           self.origami_loadListBtn]
        elif self.config.origami_acquisition == 'User-defined':
            disableList = [self.origami_startVoltage_value, 
                          self.origami_endVoltage_value, self.origami_stepVoltage_value, 
                          self.origami_exponentialIncrement_value, self.origami_exponentialPercentage_value,
                          self.origami_scansPerVoltage_value, self.origami_boltzmannOffset_value]
            enableList = [self.origami_loadListBtn, self.origami_startScan_value]
        else:
            disableList = [self.origami_startScan_value, self.origami_startVoltage_value, 
                          self.origami_endVoltage_value, self.origami_stepVoltage_value, 
                          self.origami_exponentialIncrement_value, self.origami_exponentialPercentage_value,
                          self.origami_scansPerVoltage_value, self.origami_boltzmannOffset_value,
                          self.origami_loadListBtn]
            enableList = []
            
        # iterate
        for item in enableList: item.Enable()
        for item in disableList: item.Disable()
        
        # peak fitting
        self.config.fit_type = self.fit_fitPlot_choice.GetStringSelection()
        self.config.fit_highRes = self.fit_highRes_check.GetValue()
        
        enableDisableList = [self.fit_thresholdHighRes_value, self.fit_windowHighRes_value,
                            self.fit_widthHighRes_value, self.fit_isotopes_check]
        if self.config.fit_highRes and self.config.fit_type in ['MS', 'MS + RT']: 
            for item in enableDisableList: item.Enable()
        else:
            for item in enableDisableList: item.Disable()
            
        if self.config.fit_type == 'RT':
            self.fit_highRes_check.Disable()
        else:
            self.fit_highRes_check.Enable()
            
        self.config.fit_smoothPeaks = self.fit_smooth_check.GetValue()
        if self.config.fit_smoothPeaks:
            self.fit_sigma_value.Enable()
        else:
            self.fit_sigma_value.Disable()     
        
        # mass spectrum panel
        self.config.ms_smooth_mode = self.ms_smoothFcn_choice.GetStringSelection()
        if self.config.ms_smooth_mode == 'None':
            for item in [self.ms_polynomial_value, self.ms_sigma_value, self.ms_window_value]: 
                item.Disable()
        elif self.config.ms_smooth_mode == 'Gaussian':
            for item in [self.ms_polynomial_value, self.ms_window_value]: 
                item.Disable()
            self.ms_sigma_value.Enable()
        else:
            for item in [self.ms_polynomial_value, self.ms_window_value]: 
                item.Enable()
            self.ms_sigma_value.Disable()
        
        self.config.ms_normalize = self.ms_normalizeTgl.GetValue()
        if self.config.ms_normalize: 
            self.ms_normalizeFcn_choice.Enable()
            self.ms_normalizeTgl.SetLabel('On')
            self.ms_normalizeTgl.SetForegroundColour(wx.WHITE)
            self.ms_normalizeTgl.SetBackgroundColour(wx.BLUE)
        else:
            self.ms_normalizeFcn_choice.Disable()
            self.ms_normalizeTgl.SetLabel('Off')
            self.ms_normalizeTgl.SetForegroundColour(wx.WHITE)
            self.ms_normalizeTgl.SetBackgroundColour(wx.RED)
        
        # 2D panel
        self.config.plot2D_smooth_mode = self.plot2D_smoothFcn_choice.GetStringSelection()
        if self.config.plot2D_smooth_mode == 'None':
            for item in [self.plot2D_polynomial_value, self.plot2D_sigma_value, self.plot2D_window_value]: 
                item.Disable()
        elif self.config.plot2D_smooth_mode == 'Gaussian':
            for item in [self.plot2D_polynomial_value, self.plot2D_window_value]: 
                item.Disable()
            self.plot2D_sigma_value.Enable()
        else:
            for item in [self.plot2D_polynomial_value, self.plot2D_window_value]: 
                item.Enable()
            self.plot2D_sigma_value.Disable()
        
        self.config.plot2D_normalize = self.plot2D_normalizeTgl.GetValue()
        if self.config.plot2D_normalize: 
            self.plot2D_normalizeFcn_choice.Enable()
            self.plot2D_normalizeTgl.SetLabel('On')
            self.plot2D_normalizeTgl.SetForegroundColour(wx.WHITE)
            self.plot2D_normalizeTgl.SetBackgroundColour(wx.BLUE)
        else:
            self.plot2D_normalizeFcn_choice.Disable()
            self.plot2D_normalizeTgl.SetLabel('Off')
            self.plot2D_normalizeTgl.SetForegroundColour(wx.WHITE)
            self.plot2D_normalizeTgl.SetBackgroundColour(wx.RED)
        
        # unidec 
        self.config.unidec_peakWidth_auto = self.unidec_fit_peakWidth_check.GetValue()
        if self.config.unidec_peakWidth_auto: 
            self.unidec_fit_peakWidth_value.Disable()
            self.unidec_peakTool.Disable()
        else: 
            self.unidec_fit_peakWidth_value.Enable()
            self.unidec_peakTool.Enable()
        
        if evt != None:
            evt.Skip() 

    def onSetupValues(self, evt=None):
        
        self.importEvent = True
        # panel mass spectrum
        self.ms_sigma_value.SetValue(str(self.config.ms_smooth_sigma))
        self.ms_window_value.SetValue(str(self.config.ms_smooth_window))
        self.ms_polynomial_value.SetValue(str(self.config.ms_smooth_polynomial))
        
        # panel 2D
        self.plot2D_sigma_value.SetValue(str(self.config.plot2D_smooth_sigma))
        self.plot2D_window_value.SetValue(str(self.config.plot2D_smooth_window))
        self.plot2D_polynomial_value.SetValue(str(self.config.plot2D_smooth_polynomial))
        
        self.importEvent = False
        if evt != None: 
            evt.Skip()

    def onProcess2D(self, evt):
        """
        Automatically process and replot 2D array
        """
        evtID = evt.GetId()
        
        self.config.onCheckValues(data_type='process')
        self.onSetupValues()
        
        if evtID == ID_processSettings_replot2D:
            if self.parent.panelPlots.window_plot2D == '2D':
                self.presenter.process2Ddata(replot=True, replot_type='2D')
            elif self.parent.panelPlots.window_plot2D == 'DT/MS':
                self.presenter.process2Ddata(replot=True, replot_type='DT/MS')
                
        elif evtID == ID_processSettings_process2D:
            self.presenter.process_2D(self.document['2D'], self.dataset['2D'], self.ionName['2D'])
         
        if evt != None: 
            evt.Skip()
        
    def onProcessMS(self, evt):
        """
        Automatically process and replot MS array
        """
        evtID = evt.GetId()
#         
#         self.config.onCheckValues(data_type='process')
#         self.onSetupValues()
        
        # only replotting
        if evtID == ID_processSettings_replotMS:
            self.presenter.processMSdata(replot=True)
        # processing and adding to dictionary
        elif evtID == ID_processSettings_processMS:
            self.presenter.process_MS(self.document['MS'], self.dataset['MS'])
         
        if evt != None: 
            evt.Skip()  
      
    def onExtractData(self, evt):
        # get document
        self.currentDoc = self.presenter.view.panelDocuments.topP.documents.enableCurrentDocument()
        if self.currentDoc == 'Current documents': return
        document = self.presenter.documentsDict[self.currentDoc]
        parameters = document.parameters
        
        # get parameters
        scanTime = str2num(self.extract_scanTime_value.GetValue())
        pusherFreq = str2num(self.extract_pusherFreq_value.GetValue())
        add_to_document = self.extract_add_to_document.GetValue()

        # mass spectra
        if self.config.extract_mzStart == self.config.extract_mzEnd:
            self.config.extract_mzEnd =+ 1
            self.extract_mzEnd_value.SetValue(str(self.config.extract_mzEnd))
        elif self.config.extract_mzStart > self.config.extract_mzEnd:
            self.config.extract_mzStart, self.config.extract_mzEnd = self.config.extract_mzEnd, self.config.extract_mzStart
        
        mzStart = self.config.extract_mzStart
        mzEnd = self.config.extract_mzEnd
        xlimits = [mzStart, mzEnd]
            
        # chromatogram
        if self.config.extract_rtStart == self.config.extract_rtEnd:
            self.config.extract_rtEnd =+ 1
            self.extract_rtEnd_value.SetValue(str(self.config.extract_rtEnd))
        elif self.config.extract_rtStart > self.config.extract_rtEnd:
            self.config.extract_rtStart, self.config.extract_rtEnd = self.config.extract_rtEnd, self.config.extract_rtStart
        
            
        if self.extract_rt_scans_check.GetValue():
            if scanTime in ["", 0, None]: 
                print('Scan time is incorrect. Setting value to 1')
                scanTime = 1
                self.extract_scanTime_value.SetValue(str(scanTime))
            rtStart = ((self.config.extract_rtStart+1) * scanTime) / 60
            rtEnd = ((self.config.extract_rtEnd+1) * scanTime) / 60
        else:
            rtStart = self.config.extract_rtStart
            rtEnd = self.config.extract_rtEnd
        
        # drift time
        if self.config.extract_dtStart == self.config.extract_dtEnd:
            self.config.extract_dtEnd =+ 1
            self.extract_dtEnd_value.SetValue(str(self.config.extract_dtEnd))
        elif self.config.extract_dtStart > self.config.extract_dtEnd:
            self.config.extract_dtStart, self.config.extract_dtEnd = self.config.extract_dtEnd, self.config.extract_dtStart

        if self.extract_dt_ms_check.GetValue():
            if pusherFreq in ["", 0, None]: 
                print('Pusher frequency is incorrect. Setting value to 1')
                pusherFreq = 1
                self.extract_pusherFreq_value.SetValue(str(pusherFreq))
            dtStart = int(self.config.extract_dtStart / (pusherFreq*0.001))
            dtEnd = int(self.config.extract_dtEnd / (pusherFreq*0.001))
        else:
            dtStart = self.config.extract_dtStart
            dtEnd = self.config.extract_dtEnd

        # create titles
        mz_title = "ion=%s-%s" % (np.round(mzStart,2), np.round(mzEnd,2))
        rt_title = "rt=%s-%s" % (np.round(rtStart,2), np.round(rtEnd,2))
        dt_title = "dt=%s-%s" % (np.round(dtStart,2), np.round(dtEnd,2))
        
        # extract mass spectrum
        if self.extract_extractMS_check.GetValue():
            if not self.extract_extractMS_ms_check.GetValue(): 
                mzStart, mzEnd = 0, 999999
                mz_title = "ion=all"
                xlimits = [parameters['startMS'], parameters['endMS']]
            if not self.extract_extractMS_rt_check.GetValue():
                rtStart, rtEnd = 0.0, 999.0
                rt_title = "rt=all"
            if not self.extract_extractMS_dt_check.GetValue():
                dtStart, dtEnd = 1, 200
                dt_title = "dt=all"
            ml.rawExtractMSdata(fileNameLocation=document.path, 
                                driftscopeLocation=self.config.driftscopePath,
                                mzStart=mzStart, mzEnd=mzEnd,
                                rtStart=rtStart, rtEnd=rtEnd,
                                dtStart=dtStart, dtEnd=dtEnd)
            try:
                xvals_MS, yvals_MS = ml.rawOpenMSdata(path=document.path)
                self.presenter.onPlotMS2(xvals_MS, yvals_MS, xlimits=xlimits)
                if add_to_document:
                    item_name = "%s, %s, %s" % (mz_title, rt_title, dt_title)
                    document.gotMultipleMS = True
                    document.multipleMassSpectrum[item_name] = {'xvals':xvals_MS,
                                                                'yvals':yvals_MS,
                                                                'xlabels':'m/z (Da)',
                                                                'xlimits':xlimits}
            except: pass
        
        # extract chromatogram
        if self.extract_extractRT_check.GetValue():
            if not self.extract_extractRT_ms_check.GetValue():
                mzStart, mzEnd = 0, 999999
                mz_title = "ion=all"
            if not self.extract_extractRT_dt_check.GetValue():
                dtStart, dtEnd = 1, 200
                dt_title = "dt=all"
            ml.rawExtractRTdata(fileNameLocation=document.path, 
                                driftscopeLocation=self.config.driftscopePath,
                                mzStart=mzStart, mzEnd=mzEnd,
                                dtStart=dtStart, dtEnd=dtEnd)
            try:
                yvals_RT = ml.rawOpenRTdata(path=document.path, norm=False)
                xvals_RT = np.arange(1,len(yvals_RT)+1) 
                self.presenter.onPlotRT2(xvals_RT, yvals_RT, 'Scans')
                if add_to_document:
                    item_name = "%s, %s" % (mz_title, dt_title)
                    if not hasattr(document, "gotMultipleRT"):
                        setattr(document, "gotMultipleRT", False)
                    if not hasattr(document, "multipleRT"):
                        setattr(document, "multipleRT", {})
                    document.gotMultipleRT = True
                    document.multipleRT[item_name] = {'xvals':xvals_RT,
                                                      'yvals':yvals_RT,
                                                      'xlabels':'Scans',
                                                      'ylabels':'Intensity'}
            except: pass
        
        # extract drift time
        if self.extract_extractDT_check.GetValue():
            if not self.extract_extractDT_ms_check.GetValue():
                mzStart, mzEnd = 0, 999999
                mz_title = "ion=all"
            if not self.extract_extractDT_rt_check.GetValue():
                rtStart, rtEnd = 0.0, 999.0
                rt_title = "rt=all"
            ml.rawExtract1DIMSdata(fileNameLocation=document.path,
                                driftscopeLocation=self.config.driftscopePath,
                                mzStart=mzStart, mzEnd=mzEnd,
                                rtStart=rtStart, rtEnd=rtEnd)
            try:
                yvals_DT=  ml.rawOpen1DRTdata(path=document.path, norm=False)
                xvals_DT = np.arange(1,len(yvals_DT)+1)
                self.presenter.onPlot1DIMS2(xvals_DT, yvals_DT, 'Drift time (bins)', self.config.lineColour_1D)
                if add_to_document:
                    item_name = "%s, %s" % (mz_title, rt_title)
                    # check for attributes
                    if not hasattr(document, "gotMultipleDT"):
                        setattr(document, "gotMultipleDT", False)
                    if not hasattr(document, "multipleDT"):
                        setattr(document, "multipleDT", {})
                    # add data
                    document.gotMultipleDT = True
                    document.multipleDT[item_name] = {'xvals':xvals_DT,
                                                      'yvals':yvals_DT,
                                                      'xlabels':'Drift time (bins)',
                                                      'ylabels':'Intensity'}
            except: pass
        
        # extract drift time (2D)
        if self.extract_extract2D_check.GetValue():
            if not self.extract_extract2D_ms_check.GetValue():
                mzStart, mzEnd = 0, 999999
                mz_title = "ion=all"
            if not self.extract_extract2D_rt_check.GetValue():
                rtStart, rtEnd = 0.0, 999.0
                rt_title = "rt=all"
            print(rtStart, rtEnd)
            ml.rawExtract2DIMSdata(fileNameLocation=document.path,
                                   driftscopeLocation=self.config.driftscopePath,
                                   mzStart=mzStart, mzEnd=mzEnd,
                                   rtStart=rtStart, rtEnd=rtEnd)
            try:
                zvals_2D = ml.rawOpen2DIMSdata(path=document.path, norm=False)
                print('2d shape', zvals_2D.shape)
                xvals_2D = 1+np.arange(len(zvals_2D[1,:]))
                yvals_2D = 1+np.arange(len(zvals_2D[:,1]))
                yvals_1D = np.sum(zvals_2D, axis=1).T
                yvals_RT = np.sum(zvals_2D, axis=0)
                self.presenter.plot2Ddata2(data=[zvals_2D, xvals_2D,'Scans', yvals_2D, 'Drift time (bins)'])
                if add_to_document:
                    item_name = "%s, %s" % (mz_title, rt_title)
                    document.gotExtractedIons = True
                    document.IMS2Dions[item_name] = {'zvals':zvals_2D,
                                                     'xvals':xvals_2D,
                                                     'yvals':yvals_2D,
                                                     'yvals1D':yvals_1D,
                                                     'yvalsRT':yvals_RT,
                                                     'xlabels':'Scans',
                                                     'ylabels':'Drift time (bins)'}
            except: pass
            
        # Update document
        if add_to_document:
            self.presenter.OnUpdateDocument(document, 'document')    
    
    def onChangeValidator(self, evt):
        
        if self.extract_rt_scans_check.GetValue():
            self.rt_label.SetLabel("RT (scans):")
            self.extract_rtStart_value.SetValidator(validator('intPos'))
            self.extract_rtStart_value.SetValue(str(int(self.config.extract_rtStart)))
            self.extract_rtEnd_value.SetValidator(validator('intPos'))
            self.extract_rtEnd_value.SetValue(str(int(self.config.extract_rtEnd)))
        else:
            self.rt_label.SetLabel("RT (mins): ")
            self.extract_rtStart_value.SetValidator(validator('floatPos'))
            self.extract_rtEnd_value.SetValidator(validator('floatPos'))

        if self.extract_dt_ms_check.GetValue():
            self.dt_label.SetLabel("DT (ms):")
            self.extract_dtStart_value.SetValidator(validator('intPos'))
            self.extract_dtStart_value.SetValue(str(int(self.config.extract_dtStart)))
            self.extract_dtEnd_value.SetValidator(validator('intPos'))
            self.extract_dtEnd_value.SetValue(str(int(self.config.extract_dtEnd)))
        else:
            self.dt_label.SetLabel("DT (bins):")
            self.extract_dtStart_value.SetValidator(validator('floatPos'))
            self.extract_dtEnd_value.SetValidator(validator('floatPos'))
            
    def onCheckValues(self, evt):
        
        # get values
        self.config.extract_mzStart = str2num(self.extract_mzStart_value.GetValue())
        self.config.extract_mzEnd = str2num(self.extract_mzEnd_value.GetValue())
        self.config.extract_rtStart = str2num(self.extract_rtStart_value.GetValue())
        self.config.extract_rtEnd = str2num(self.extract_rtEnd_value.GetValue())
        self.config.extract_dtStart = str2num(self.extract_dtStart_value.GetValue())
        self.config.extract_dtEnd = str2num(self.extract_dtEnd_value.GetValue())
        
    def openHTMLViewer(self, evt):
        
        evtID = evt.GetId()
        
        if evtID == ID_processSettings_UniDec_info:
            msg = """
            <p>UniDec is a Bayesian deconvolution program for deconvolution of mass spectra and ion mobility-mass spectra developed by Dr. Michael Marty and is available under a modified BSD licence.</p>
            <p>If you have used UniDec while using ORIGAMI, please cite:</p>
            <p><a href="http://pubs.acs.org/doi/abs/10.1021/acs.analchem.5b00140" rel="nofollow">M. T. Marty, A. J. Baldwin, E. G. Marklund, G. K. A. Hochberg, J. L. P. Benesch, C. V. Robinson, Anal. Chem. 2015, 87, 4370-4376.</a></p>
            <p>This is a somewhat stripped version of UniDec so for full experience I would highly recommend downloading UniDec to give it a try yourself from <a href="https://github.com/michaelmarty/UniDec/releases">here</a>.</p>
            <p>UniDec engine version 2.6.7.</p>
            """.strip()
            title = "About UniDec..."
            
            kwargs = {'window_size': (550, 300)}

        htmlViewer = panelHTMLViewer(self, self.config, msg, title, **kwargs)
        htmlViewer.Show()
#         if htmlViewer.ShowModal() == wx.ID_OK: 
#             pass
    
    def openWidthTool(self, evt):
        try:
            kwargs = {'xvals':self.config.unidec_engine.data.data2[:, 0],
                      'yvals':self.config.unidec_engine.data.data2[:, 1]}
        except:
            dlgBox(exceptionTitle="Error",
                   exceptionMsg="Please initilise and process data first!", 
                   type="Error")
            return
        
        self.widthTool = panelPeakWidthTool(self, self.presenter, self.config, **kwargs)
        self.widthTool.Show()

    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    