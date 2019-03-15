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

# Load libraries
import wx, time, threading, re
import numpy as np
from natsort import natsorted
from operator import itemgetter

from toolbox import (str2num, str2int)
from styles import (makeToggleBtn, validator, makeCheckbox, makeSuperTip,
                    makeStaticBox, makeTooltip)
from ids import (ID_processSettings_replotMS, ID_processSettings_processMS,
                 ID_processSettings_process2D, ID_processSettings_replot2D,
                 ID_processSettings_UniDec_info, ID_processSettings_runUniDec,
                 ID_processSettings_preprocessUniDec, ID_processSettings_pickPeaksUniDec,
                 ID_processSettings_autoUniDec, ID_processSettings_loadDataUniDec,
                 ID_processSettings_runAll, ID_processSettings_showZUniDec, ID_processSettings_isolateZUniDec,
                 ID_processSettings_replotAll, ID_processSettings_restoreIsolatedAll,
                 ID_saveConfig)
from help_documentation import OrigamiHelp
from dialogs import panelHTMLViewer, panelPeakWidthTool, dlgBox
from gui_elements.dialog_customiseUniDecPlots import panelCustomiseParameters
from readers.io_waters_raw import (rawMassLynx_MS_extract, rawMassLynx_RT_extract, rawMassLynx_DT_extract,
                                   rawMassLynx_2DT_extract)

# TODO: UniDec - when picking peak and selecting G/L it gives the wrong value
# TODO: UniDec - restrict how many points can be shown in a MW plot when finding peaks
# TODO: UniDec - adding points to MW plot should check the current min/max range when
#       finding maximum value


class panelProcessData(wx.MiniFrame):
    """
    """

    def __init__(self, parent, presenter, config, icons, **kwargs):
        wx.MiniFrame.__init__(self, parent, -1, 'Processing...', size=(-1, -1),
                              style=(wx.DEFAULT_FRAME_STYLE |
                                      wx.MAXIMIZE_BOX | wx.CLOSE_BOX))
        tstart = time.time()
        self.parent = parent
        self.presenter = presenter
        self.config = config
        self.icons = icons
        self.help = OrigamiHelp()
        self.data_processing = self.parent.data_processing

        self.importEvent = False
        self.currentPage = None
        self.windowSizes = {'Extract':(470, 390), 'ORIGAMI':(412, 337),
                            'Mass spectrum':(412, 640), '2D':(412, 268),
                            'Peak fitting':(412, 555), 'UniDec':(400, 785)}
        self.show_smoothed = True
        self._unidec_sort_column = 0  # 0 == MW / 1 == %

        # check if document/item information in kwarg
        if kwargs.get('processKwargs', None) != {}:
            self.onUpdateKwargs(data_type=kwargs['processKwargs']['update_mode'],
                                **kwargs['processKwargs'])
        else:
            self.document = {}
            self.dataset = {}
            self.ionName = {}

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

        self.mainSizer.Fit(self)
        self.Centre()
        self.Layout()
        self.Show(True)
        self.SetFocus()

        # fire-up start events
        self.onPageChanged(evt=None)
        self.updateStatusbar()
        self.onUpdateUniDecPanel()
        print(("Startup took {:.3f} seconds".format(time.time() - tstart)))

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
            # set new dataset
            try: self.data_processing.unidec_dataset = self.dataset['MS']
            except KeyError: pass

            self.unidec_weightList_choice.Clear()
            kwargs = {'notify_of_error':False}
            massList, massMax = self.data_processing.get_unidec_data(data_type="mass_list", **kwargs)
            self.unidec_weightList_choice.SetItems(massList)
            self.unidec_weightList_choice.SetStringSelection(massMax)

        except:
            pass

    def OnKey(self, evt):
        keyCode = evt.GetKeyCode()
#         print(self.currentPage)
        if keyCode == wx.WXK_ESCAPE:  # key = esc
            self.onClose(evt=None)
        elif keyCode == 65:  # key = a
            self.onApply(evt=None)
        elif keyCode == 70 and self.currentPage == "Peak fitting":  # key = a
            self.onPickPeaksThreaded(evt=None)

        if evt != None:
            evt.Skip()

    def onPageChanged(self, evt):

        self.windowSizes = {'Extract':(470, 385), 'ORIGAMI':(412, 335),
                            'Mass spectrum':(412, 632), '2D':(412, 264),
                            'Peak fitting':(465, 568), 'UniDec':(740, 498)}

        self.currentPage = self.mainBook.GetPageText(self.mainBook.GetSelection())
        self.SetSize(self.windowSizes[self.currentPage])
        self.SetMaxSize(self.windowSizes[self.currentPage])
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
                              "Extract", False)
        # ------
        self.parameters_ORIGAMI = wx.Panel(self.mainBook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.mainBook.AddPage(self.makePanel_ORIGAMI(self.parameters_ORIGAMI),
                              "ORIGAMI", False)
        # ------
        self.parameters_MS = wx.Panel(self.mainBook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.mainBook.AddPage(self.makePanel_MS(self.parameters_MS),
                              "Mass spectrum", False)
        # ------
        self.parameters_2D = wx.Panel(self.mainBook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.mainBook.AddPage(self.makePanel_2D(self.parameters_2D),
                              "2D", False)
        # ------
        self.parameters_peakFitting = wx.Panel(self.mainBook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.mainBook.AddPage(self.makePanel_PeakFitting(self.parameters_peakFitting),
                              "Peak fitting", False)
        # ------
        self.parameters_unidec = wx.Panel(self.mainBook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.mainBook.AddPage(self.makePanel_UniDec(self.parameters_unidec),
                              "UniDec", False)

        self.mainSizer.Add(self.mainBook, 1, wx.EXPAND | wx.ALL, 2)

        # fire-up a couple of events
        self.enableDisableBoxes(evt=None)

        # setup color
        self.mainBook.SetBackgroundColour((240, 240, 240))

    def makeStatusBar(self):
        self.mainStatusbar = self.CreateStatusBar(4, wx.ST_SIZEGRIP | wx.ST_ELLIPSIZE_MIDDLE, wx.ID_ANY)
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
        preprocess_staticBox = makeStaticBox(panel, "1. Pre-processing parameters", size=(-1, -1), color=wx.BLACK)
        preprocess_staticBox.SetSize((-1, -1))
        preprocess_box_sizer = wx.StaticBoxSizer(preprocess_staticBox, wx.HORIZONTAL)

        unidec_ms_min_label = wx.StaticText(panel, wx.ID_ANY, "m/z start:")
        self.unidec_mzStart_value = wx.TextCtrl(panel, -1, "", size=TEXTCTRL_SIZE,
                                                validator=validator('floatPos'))
        self.unidec_mzStart_value.SetValue(str(self.config.unidec_mzStart))
        self.unidec_mzStart_value.Bind(wx.EVT_TEXT, self.onApply)
        self.unidec_mzStart_value.SetToolTip(makeTooltip(text=self.help.unidec_min_mz['help_msg']))

        unidec_ms_max_label = wx.StaticText(panel, wx.ID_ANY, "end:")
        self.unidec_mzEnd_value = wx.TextCtrl(panel, -1, "", size=TEXTCTRL_SIZE,
                                          validator=validator('floatPos'))
        self.unidec_mzEnd_value.SetValue(str(self.config.unidec_mzEnd))
        self.unidec_mzEnd_value.Bind(wx.EVT_TEXT, self.onApply)
        self.unidec_mzEnd_value.SetToolTip(makeTooltip(text=self.help.unidec_max_mz['help_msg']))

        unidec_ms_binsize_label = wx.StaticText(panel, wx.ID_ANY, "m/z bin size:")
        self.unidec_mzBinSize_value = wx.TextCtrl(panel, -1, "", size=TEXTCTRL_SIZE,
                                          validator=validator('floatPos'))
        self.unidec_mzBinSize_value.SetValue(str(self.config.unidec_mzBinSize))
        self.unidec_mzBinSize_value.Bind(wx.EVT_TEXT, self.onApply)
        self.unidec_mzBinSize_value.SetToolTip(makeTooltip(text=self.help.unidec_linearization['help_msg']))

        unidec_ms_gaussianFilter_label = wx.StaticText(panel, wx.ID_ANY, "Gaussian filter:")
        self.unidec_gaussianFilter_value = wx.TextCtrl(panel, -1, "", size=TEXTCTRL_SIZE,
                                          validator=validator('floatPos'))
        self.unidec_gaussianFilter_value.SetValue(str(self.config.unidec_gaussianFilter))
        self.unidec_gaussianFilter_value.Bind(wx.EVT_TEXT, self.onApply)

        unidec_ms_accelerationV_label = wx.StaticText(panel, wx.ID_ANY, "Acceleration voltage (kV):")
        self.unidec_accelerationV_value = wx.TextCtrl(panel, -1, "", size=TEXTCTRL_SIZE,
                                          validator=validator('floatPos'))
        self.unidec_accelerationV_value.SetValue(str(self.config.unidec_accelerationV))
        self.unidec_accelerationV_value.Bind(wx.EVT_TEXT, self.onApply)

        unidec_linearization_label = wx.StaticText(panel, wx.ID_ANY, "Linearization mode:")
        self.unidec_linearization_choice = wx.Choice(panel, -1, choices=list(self.config.unidec_linearization_choices.keys()),
                                          size=(-1, -1))
        self.unidec_linearization_choice.SetStringSelection(self.config.unidec_linearization)
        self.unidec_linearization_choice.Bind(wx.EVT_CHOICE, self.onApply)

        self.unidec_load = wx.Button(panel, ID_processSettings_loadDataUniDec, "Initilise UniDec",
                                     size=BTN_SIZE, name="load_data_unidec")
        self.unidec_preprocess = wx.Button(panel, ID_processSettings_preprocessUniDec, "Pre-process",
                                           size=BTN_SIZE, name="preprocess_unidec")

        # pack elements
        preprocess_grid = wx.GridBagSizer(2, 2)
        n = 0
        preprocess_grid.Add(unidec_ms_min_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        preprocess_grid.Add(self.unidec_mzStart_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
#         n = n + 1
        preprocess_grid.Add(unidec_ms_max_label, (n, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        preprocess_grid.Add(self.unidec_mzEnd_value, (n, 3), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        preprocess_grid.Add(unidec_ms_binsize_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        preprocess_grid.Add(self.unidec_mzBinSize_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        preprocess_grid.Add(unidec_ms_gaussianFilter_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        preprocess_grid.Add(self.unidec_gaussianFilter_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        preprocess_grid.Add(unidec_ms_accelerationV_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        preprocess_grid.Add(self.unidec_accelerationV_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        preprocess_grid.Add(unidec_linearization_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        preprocess_grid.Add(self.unidec_linearization_choice, (n, 1), wx.GBSpan(1, 4), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        preprocess_grid.Add(self.unidec_load, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        preprocess_grid.Add(self.unidec_preprocess, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        preprocess_box_sizer.Add(preprocess_grid, 0, wx.EXPAND, 10)

        # UniDec parameters
        unidec_staticBox = makeStaticBox(panel, "2. UniDec parameters", size=(-1, -1), color=wx.BLACK)
        unidec_staticBox.SetSize((-1, -1))
        unidec_box_sizer = wx.StaticBoxSizer(unidec_staticBox, wx.HORIZONTAL)

        unidec_charge_min_label = wx.StaticText(panel, wx.ID_ANY, "Charge start:")
        self.unidec_zStart_value = wx.TextCtrl(panel, -1, "", size=TEXTCTRL_SIZE,
                                          validator=validator('floatPos'))
        self.unidec_zStart_value.SetValue(str(self.config.unidec_zStart))
        self.unidec_zStart_value.Bind(wx.EVT_TEXT, self.onApply)
        self.unidec_zStart_value.SetToolTip(makeTooltip(text=self.help.unidec_min_z['help_msg']))

        unidec_charge_max_label = wx.StaticText(panel, wx.ID_ANY, "end:")
        self.unidec_zEnd_value = wx.TextCtrl(panel, -1, "", size=TEXTCTRL_SIZE,
                                          validator=validator('floatPos'))
        self.unidec_zEnd_value.SetValue(str(self.config.unidec_zEnd))
        self.unidec_zEnd_value.Bind(wx.EVT_TEXT, self.onApply)
        self.unidec_zEnd_value.SetToolTip(makeTooltip(text=self.help.unidec_max_z['help_msg']))

        unidec_mw_min_label = wx.StaticText(panel, wx.ID_ANY, "MW start:")
        self.unidec_mwStart_value = wx.TextCtrl(panel, -1, "", size=TEXTCTRL_SIZE,
                                          validator=validator('floatPos'))
        self.unidec_mwStart_value.SetValue(str(self.config.unidec_mwStart))
        self.unidec_mwStart_value.Bind(wx.EVT_TEXT, self.onApply)
        self.unidec_mwStart_value.SetToolTip(makeTooltip(text=self.help.unidec_min_mw['help_msg']))

        unidec_mw_max_label = wx.StaticText(panel, wx.ID_ANY, "end:")
        self.unidec_mwEnd_value = wx.TextCtrl(panel, -1, "", size=TEXTCTRL_SIZE,
                                          validator=validator('floatPos'))
        self.unidec_mwEnd_value.SetValue(str(self.config.unidec_mwEnd))
        self.unidec_mwEnd_value.Bind(wx.EVT_TEXT, self.onApply)
        self.unidec_mwEnd_value.SetToolTip(makeTooltip(text=self.help.unidec_max_mw['help_msg']))

        unidec_mw_sampleFrequency_label = wx.StaticText(panel, wx.ID_ANY, "Sample frequency (Da):")
        self.unidec_mw_sampleFrequency_value = wx.TextCtrl(panel, -1, "", size=TEXTCTRL_SIZE,
                                          validator=validator('floatPos'))
        self.unidec_mw_sampleFrequency_value.SetValue(str(self.config.unidec_mwFrequency))
        self.unidec_mw_sampleFrequency_value.Bind(wx.EVT_TEXT, self.onApply)
        self.unidec_mw_sampleFrequency_value.SetToolTip(makeTooltip(text=self.help.unidec_mw_resolution['help_msg']))

        unidec_peakWidth_label = wx.StaticText(panel, wx.ID_ANY, "Peak FWHM (Da):")
        self.unidec_fit_peakWidth_value = wx.TextCtrl(panel, -1, "", size=TEXTCTRL_SIZE,
                                          validator=validator('floatPos'))
        self.unidec_fit_peakWidth_value.SetValue(str(self.config.unidec_peakWidth))
        self.unidec_fit_peakWidth_value.Bind(wx.EVT_TEXT, self.onApply)
        self.unidec_fit_peakWidth_value.SetToolTip(makeTooltip(text=self.help.unidec_peak_FWHM['help_msg']))

        self.unidec_fit_peakWidth_check = makeCheckbox(panel, "Auto")
        self.unidec_fit_peakWidth_check.SetValue(self.config.unidec_peakWidth_auto)
        self.unidec_fit_peakWidth_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        self.unidec_fit_peakWidth_check.Bind(wx.EVT_CHECKBOX, self.enableDisableBoxes)

        unidec_peakShape_label = wx.StaticText(panel, wx.ID_ANY, "Peak Shape:")
        self.unidec_peakFcn_choice = wx.Choice(panel, -1, choices=list(self.config.unidec_peakFunction_choices.keys()),
                                          size=(-1, -1))
        self.unidec_peakFcn_choice.SetStringSelection(self.config.unidec_peakFunction)
        self.unidec_peakFcn_choice.Bind(wx.EVT_CHOICE, self.onApply)

        self.unidec_peakTool = wx.Button(panel, -1, "Peak width tool", size=BTN_SIZE)
        self.unidec_runUnidec = wx.Button(panel, ID_processSettings_runUniDec, "Run UniDec",
                                          size=BTN_SIZE, name="run_unidec")

        # pack elements
        ms_grid = wx.GridBagSizer(2, 2)
        n = 0
        ms_grid.Add(unidec_charge_min_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        ms_grid.Add(self.unidec_zStart_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        ms_grid.Add(unidec_charge_max_label, (n, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        ms_grid.Add(self.unidec_zEnd_value, (n, 3), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n = n + 1
        ms_grid.Add(unidec_mw_min_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        ms_grid.Add(self.unidec_mwStart_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        ms_grid.Add(unidec_mw_max_label, (n, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        ms_grid.Add(self.unidec_mwEnd_value, (n, 3), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n = n + 1
        ms_grid.Add(unidec_mw_sampleFrequency_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        ms_grid.Add(self.unidec_mw_sampleFrequency_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n = n + 1
        ms_grid.Add(unidec_peakWidth_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        ms_grid.Add(self.unidec_fit_peakWidth_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        ms_grid.Add(self.unidec_peakTool, (n, 2), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER_VERTICAL)
        ms_grid.Add(self.unidec_fit_peakWidth_check, (n, 4), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        ms_grid.Add(unidec_peakShape_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        ms_grid.Add(self.unidec_peakFcn_choice, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        ms_grid.Add(self.unidec_runUnidec, (n, 2), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER_VERTICAL)
        unidec_box_sizer.Add(ms_grid, 0, wx.EXPAND, 10)

        # Peak detection
        peakDetect_staticBox = makeStaticBox(panel, "3. Peak detection parameters", size=(-1, -1), color=wx.BLACK)
        peakDetect_staticBox.SetSize((-1, -1))
        peakDetect_box_sizer = wx.StaticBoxSizer(peakDetect_staticBox, wx.HORIZONTAL)

        unidec_peak_width_label = wx.StaticText(panel, wx.ID_ANY, "Peak detection window (Da):")
        self.unidec_peakWidth_value = wx.TextCtrl(panel, -1, "", size=TEXTCTRL_SIZE,
                                          validator=validator('floatPos'))
        self.unidec_peakWidth_value.SetValue(str(self.config.unidec_peakDetectionWidth))
        self.unidec_peakWidth_value.Bind(wx.EVT_TEXT, self.onApply)

        unidec_peak_threshold_label = wx.StaticText(panel, wx.ID_ANY, "Peak detection threshold:")
        self.unidec_peakThreshold_value = wx.TextCtrl(panel, -1, "", size=TEXTCTRL_SIZE,
                                          validator=validator('floatPos'))
        self.unidec_peakThreshold_value.SetValue(str(self.config.unidec_peakDetectionThreshold))
        self.unidec_peakThreshold_value.Bind(wx.EVT_TEXT, self.onApply)

        unidec_peak_normalization_label = wx.StaticText(panel, wx.ID_ANY, "Peak normalization:")
        self.unidec_peakNormalization_choice = wx.Choice(panel, -1, choices=list(self.config.unidec_peakNormalization_choices.keys()),
                                          size=(-1, -1))
        self.unidec_peakNormalization_choice.SetStringSelection(self.config.unidec_peakNormalization)
        self.unidec_peakNormalization_choice.Bind(wx.EVT_CHOICE, self.onApply)

        individualComponents_label = wx.StaticText(panel, wx.ID_ANY, "Show individual components:")
        self.unidec_individualComponents_check = makeCheckbox(panel, "")
        self.unidec_individualComponents_check.SetValue(self.config.unidec_show_individualComponents)
        self.unidec_individualComponents_check.Bind(wx.EVT_CHECKBOX, self.onApply)

        markers_label = wx.StaticText(panel, wx.ID_ANY, "Show markers:")
        self.unidec_markers_check = makeCheckbox(panel, "")
        self.unidec_markers_check.SetValue(self.config.unidec_show_markers)
        self.unidec_markers_check.Bind(wx.EVT_CHECKBOX, self.onApply)

        unidec_peak_separation_label = wx.StaticText(panel, wx.ID_ANY, "Line separation:")
        self.unidec_lineSeparation_value = wx.TextCtrl(panel, -1, "", size=TEXTCTRL_SIZE,
                                          validator=validator('floatPos'))
        self.unidec_lineSeparation_value.SetValue(str(self.config.unidec_lineSeparation))
        self.unidec_lineSeparation_value.Bind(wx.EVT_TEXT, self.onApply)

        self.unidec_detectPeaks = wx.Button(panel, ID_processSettings_pickPeaksUniDec, "Detect peaks",
                                            size=BTN_SIZE, name="pick_peaks_unidec")

        # pack elements
        peak_grid = wx.GridBagSizer(2, 2)
        n = 0
        peak_grid.Add(unidec_peak_width_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        peak_grid.Add(self.unidec_peakWidth_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        peak_grid.Add(unidec_peak_threshold_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        peak_grid.Add(self.unidec_peakThreshold_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        peak_grid.Add(unidec_peak_normalization_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        peak_grid.Add(self.unidec_peakNormalization_choice, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        peak_grid.Add(unidec_peak_separation_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        peak_grid.Add(self.unidec_lineSeparation_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        peak_grid.Add(individualComponents_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        peak_grid.Add(self.unidec_individualComponents_check, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        peak_grid.Add(markers_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        peak_grid.Add(self.unidec_markers_check, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
#         n = n + 1
        peak_grid.Add(self.unidec_detectPeaks, (n, 2), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER_VERTICAL)
        peakDetect_box_sizer.Add(peak_grid, 0, wx.EXPAND, 10)

        # Buttons
        self.unidec_autorun = wx.Button(panel, ID_processSettings_autoUniDec, "Autorun UniDec",
                                        size=(-1, 22), name="auto_unidec")
        self.unidec_runAll = wx.Button(panel, ID_processSettings_runAll, "Run all", size=(-1, 22))
        self.unidec_cancelBtn = wx.Button(panel, wx.ID_OK, "Cancel", size=(-1, 22))

        self.unidec_info = wx.BitmapButton(panel, ID_processSettings_UniDec_info,
                                             self.icons.iconsLib['process_unidec_16'],
                                             size=(-1, -1),
                                             style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL)
        self.unidec_info.SetBackgroundColour((240, 240, 240))
        self.unidec_info.SetToolTip(makeTooltip(text=self.help.unidec_about['help_msg']))

        plot_staticBox = makeStaticBox(panel, "4. Plotting", size=(-1, -1), color=wx.BLACK)
        plot_staticBox.SetSize((-1, -1))
        plot_box_sizer = wx.StaticBoxSizer(plot_staticBox, wx.HORIZONTAL)

        unidec_plotting_weights_label = wx.StaticText(panel, wx.ID_ANY, "Molecular weights:")
        self.unidec_weightList_choice = wx.ComboBox(panel, ID_processSettings_showZUniDec,
                                                    choices=[],
                                                    size=(150, -1), style=wx.CB_READONLY,
                                                    name="ChargeStates")
        self.unidec_weightList_choice.Bind(wx.EVT_COMBOBOX, self.onRunUnidecThreaded)

        self.unidec_weightList_sort = wx.BitmapButton(panel, wx.ID_ANY,
                                                      self.icons.iconsLib['reload16'],
                                                      size=(-1, -1), name="unidec_sort",
                                                      style=wx.ALIGN_CENTER_VERTICAL)
        self.unidec_weightList_sort.SetBackgroundColour((240, 240, 240))
        self.unidec_weightList_sort.Bind(wx.EVT_BUTTON, self.on_sort_unidec_MW)
        self.unidec_weightList_sort.SetToolTip(makeTooltip(text=self.help.unidec_sort_mw_list['help_msg']))

        unidec_plotting_adduct_label = wx.StaticText(panel, wx.ID_ANY, "Adduct:")
        self.unidec_adductMW_choice = wx.Choice(panel, ID_processSettings_showZUniDec,
                                                choices=["H+", "Na+", "K+", "NH4+", "H-", "Cl-"],
                                                size=(-1, -1), name="ChargeStates")
        self.unidec_adductMW_choice.SetStringSelection("H+")
        self.unidec_adductMW_choice.Bind(wx.EVT_CHOICE, self.onRunUnidecThreaded)

        unidec_charges_threshold_label = wx.StaticText(panel, wx.ID_ANY, "Intensity threshold:")
        self.unidec_charges_threshold_value = wx.SpinCtrlDouble(panel, -1,
                                                             value=str(self.config.unidec_charges_label_charges),
                                                             min=0, max=1,
                                                             initial=self.config.unidec_charges_label_charges,
                                                             inc=0.01, size=(90, -1))
        self.unidec_charges_threshold_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)

        unidec_charges_offset_label = wx.StaticText(panel, wx.ID_ANY, "Vertical charge offset:")
        self.unidec_charges_offset_value = wx.SpinCtrlDouble(panel, -1,
                                                             value=str(self.config.unidec_charges_offset),
                                                             min=0, max=1,
                                                             initial=self.config.unidec_charges_offset,
                                                             inc=0.05, size=(90, -1))
        self.unidec_charges_offset_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)

        self.unidec_restoreAll_Btn = wx.Button(panel, ID_processSettings_restoreIsolatedAll, "Restore all", size=(-1, 22))
        self.unidec_restoreAll_Btn.Bind(wx.EVT_BUTTON, self.onRunUnidecThreaded)

        self.unidec_chargeStates_Btn = wx.Button(panel, ID_processSettings_showZUniDec, "Label", size=(-1, 22))
        self.unidec_chargeStates_Btn.Bind(wx.EVT_BUTTON, self.onRunUnidecThreaded)

        self.unidec_isolateCharges_Btn = wx.Button(panel, ID_processSettings_isolateZUniDec, "Isolate", size=(-1, 22))
        self.unidec_isolateCharges_Btn.Bind(wx.EVT_BUTTON, self.onRunUnidecThreaded)
#
#         self.unidec_addToAnnotations_Btn = wx.Button(panel, wx.ID_ANY, "Add to annotations", size=(-1, 22))
#         self.unidec_addToAnnotations_Btn.Bind(wx.EVT_BUTTON, self.onAddToAnnotations)

        # pack elements
        plotting_grid = wx.GridBagSizer(2, 2)
        n = 0
        plotting_grid.Add(unidec_plotting_weights_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        plotting_grid.Add(self.unidec_weightList_choice, (n, 1), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        plotting_grid.Add(self.unidec_weightList_sort, (n, 3), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n = n + 1
        plotting_grid.Add(unidec_plotting_adduct_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        plotting_grid.Add(self.unidec_adductMW_choice, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        plotting_grid.Add(self.unidec_restoreAll_Btn, (n, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n = n + 1
        plotting_grid.Add(unidec_charges_threshold_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        plotting_grid.Add(self.unidec_charges_threshold_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        plotting_grid.Add(self.unidec_chargeStates_Btn, (n, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n = n + 1
        plotting_grid.Add(unidec_charges_offset_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        plotting_grid.Add(self.unidec_charges_offset_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        plotting_grid.Add(self.unidec_isolateCharges_Btn, (n, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
#         n = n + 1
#         plotting_grid.Add(self.unidec_addToAnnotations_Btn, (n,1), wx.GBSpan(1,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        plot_box_sizer.Add(plotting_grid, 0, wx.EXPAND, 10)

        other_staticBox = makeStaticBox(panel, "Other settings", size=(-1, -1), color=wx.BLACK)
        other_staticBox.SetSize((-1, -1))
        other_box_sizer = wx.StaticBoxSizer(other_staticBox, wx.HORIZONTAL)

        unidec_max_iters_label = wx.StaticText(panel, wx.ID_ANY, "Max iterations:")
        self.unidec_maxIters_value = wx.TextCtrl(panel, -1, "", size=TEXTCTRL_SIZE,
                                          validator=validator('intPos'))
        self.unidec_maxIters_value.SetValue(str(self.config.unidec_maxIterations))
        self.unidec_maxIters_value.Bind(wx.EVT_TEXT, self.onApply)

        unidec_max_shown_label = wx.StaticText(panel, wx.ID_ANY, "Max shown:")
        self.unidec_maxShownLines_value = wx.TextCtrl(panel, -1, "", size=TEXTCTRL_SIZE,
                                          validator=validator('intPos'))
        self.unidec_maxShownLines_value.SetValue(str(self.config.unidec_maxShown_individualLines))
        self.unidec_maxShownLines_value.Bind(wx.EVT_TEXT, self.onApply)

        self.unidec_customise_Btn = wx.Button(panel, wx.ID_ANY, "Customise plots...", size=(-1, 22))
        self.unidec_customise_Btn.Bind(wx.EVT_BUTTON, self.onRunUnidecThreaded)

        other_grid = wx.GridBagSizer(2, 2)
        n = 0
        other_grid.Add(unidec_max_iters_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        other_grid.Add(self.unidec_maxIters_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        other_grid.Add(unidec_max_shown_label, (n, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        other_grid.Add(self.unidec_maxShownLines_value, (n, 3), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n = n + 1
        other_grid.Add(self.unidec_customise_Btn, (n, 0), wx.GBSpan(1, 4), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        other_box_sizer.Add(other_grid, 0, wx.EXPAND, 10)

        self.unidec_replot_Btn = wx.Button(panel, ID_processSettings_replotAll, "Replot", size=(-1, 22))
        self.unidec_replot_Btn.Bind(wx.EVT_BUTTON, self.onRunUnidecThreaded)

        horizontal_line_1 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        button_grid = wx.GridBagSizer(2, 2)
        n = 0
        button_grid.Add(self.unidec_autorun, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        button_grid.Add(self.unidec_runAll, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        button_grid.Add(self.unidec_cancelBtn, (n, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        button_grid.Add(self.unidec_replot_Btn, (n, 3), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        button_grid.Add(self.unidec_info, (n, 4), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)

        sizer_left = wx.BoxSizer(wx.VERTICAL)
        sizer_left.Add(preprocess_box_sizer, 0, wx.EXPAND, 0)
        sizer_left.Add(unidec_box_sizer, 0, wx.EXPAND, 0)

        sizer_right = wx.BoxSizer(wx.VERTICAL)
        sizer_right.Add(peakDetect_box_sizer, 0, wx.EXPAND, 0)
        sizer_right.Add(plot_box_sizer, 0, wx.EXPAND, 0)
        sizer_right.Add(other_box_sizer, 0, wx.EXPAND, 0)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(sizer_left, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND | wx.ALIGN_LEFT)
        grid.Add(sizer_right, (n, 5), wx.GBSpan(1, 5), flag=wx.EXPAND | wx.ALIGN_LEFT)
        n = n + 1
        grid.Add(horizontal_line_1, (n, 0), wx.GBSpan(1, 10), flag=wx.EXPAND)
        n = n + 1
        grid.Add(button_grid, (n, 0), wx.GBSpan(1, 10), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        mainSizer.Add(grid, 0, wx.ALIGN_CENTER_HORIZONTAL, 10)

        # bind events
        self.unidec_load.Bind(wx.EVT_BUTTON, self.onRunUnidecThreaded)
        self.unidec_preprocess.Bind(wx.EVT_BUTTON, self.onRunUnidecThreaded)
        self.unidec_runUnidec.Bind(wx.EVT_BUTTON, self.onRunUnidecThreaded)
        self.unidec_runAll.Bind(wx.EVT_BUTTON, self.onRunUnidecThreaded)
        self.unidec_detectPeaks.Bind(wx.EVT_BUTTON, self.onRunUnidecThreaded)
        self.unidec_autorun.Bind(wx.EVT_BUTTON, self.onRunUnidecThreaded)
        self.unidec_cancelBtn.Bind(wx.EVT_BUTTON, self.onClose)
        self.unidec_info.Bind(wx.EVT_BUTTON, self.openHTMLViewer)
        self.unidec_peakTool.Bind(wx.EVT_BUTTON, self.openWidthTool)
        self.unidec_customise_Btn.Bind(wx.EVT_BUTTON, self.onCustomiseUniDecParameters)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizerAndFit(mainSizer)

        return panel

    def makePanel_PeakFitting(self, panel):
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        fitPlot_label = wx.StaticText(panel, wx.ID_ANY, "Search plot:")
        self.fit_fitPlot_choice = wx.Choice(panel, -1, choices=["MS", "RT", "MS + RT"],  # self.config.fit_type_choices,
                                          size=(-1, -1))
        self.fit_fitPlot_choice.SetStringSelection(self.config.fit_type)
        self.fit_fitPlot_choice.Bind(wx.EVT_CHOICE, self.onApply)
        self.fit_fitPlot_choice.Bind(wx.EVT_CHOICE, self.enableDisableBoxes)

        threshold_label = wx.StaticText(panel, wx.ID_ANY, "Threshold:")
        self.fit_threshold_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('floatPos'))
        self.fit_threshold_value.SetValue(str(self.config.fit_threshold))
        self.fit_threshold_value.Bind(wx.EVT_TEXT, self.onApply)

        window_label = wx.StaticText(panel, wx.ID_ANY, "Window size (points):")
        self.fit_window_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                            validator=validator('intPos'))
        self.fit_window_value.SetValue(str(self.config.fit_window))
        self.fit_window_value.Bind(wx.EVT_TEXT, self.onApply)

        width_label = wx.StaticText(panel, wx.ID_ANY, "Peak width:")
        self.fit_width_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                           validator=validator('floatPos'))
        self.fit_width_value.SetValue(str(self.config.fit_width))
        self.fit_width_value.Bind(wx.EVT_TEXT, self.onApply)

        asymmetricity_label = wx.StaticText(panel, wx.ID_ANY, "Peak asymmetricity:")
        self.fit_asymmetricRatio_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                           validator=validator('float'))
        self.fit_asymmetricRatio_value.SetValue(str(self.config.fit_asymmetric_ratio))
        self.fit_asymmetricRatio_value.Bind(wx.EVT_TEXT, self.onApply)

        smooth_label = wx.StaticText(panel, wx.ID_ANY, "Smooth peaks:")
        self.fit_smooth_check = makeCheckbox(panel, "")
        self.fit_smooth_check.SetValue(self.config.fit_smoothPeaks)
        self.fit_smooth_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        self.fit_smooth_check.Bind(wx.EVT_CHECKBOX, self.enableDisableBoxes)

        sigma_label = wx.StaticText(panel, wx.ID_ANY, "Gaussian sigma:")
        self.fit_sigma_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                           validator=validator('floatPos'))
        self.fit_sigma_value.SetValue(str(self.config.fit_smooth_sigma))
        self.fit_sigma_value.Bind(wx.EVT_TEXT, self.onApply)

        self.fit_show_smoothed = makeCheckbox(panel, "Show")
        self.fit_show_smoothed.SetValue(self.show_smoothed)
        self.fit_show_smoothed.Bind(wx.EVT_CHECKBOX, self.onApply)

        highRes_staticBox = makeStaticBox(panel, "Charge state prediction", size=(-1, -1), color=wx.BLACK)
        highRes_staticBox.SetSize((-1, -1))
        highRes_box_sizer = wx.StaticBoxSizer(highRes_staticBox, wx.HORIZONTAL)

        highRes_label = wx.StaticText(panel, wx.ID_ANY, "Enable:")
        self.fit_highRes_check = makeCheckbox(panel, "")
        self.fit_highRes_check.SetValue(self.config.fit_highRes)
        self.fit_highRes_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        self.fit_highRes_check.Bind(wx.EVT_CHECKBOX, self.enableDisableBoxes)
        __fit_highRes_tip = makeSuperTip(self.fit_highRes_check, **self.help.fit_highRes)

        threshold_highRes_label = wx.StaticText(panel, wx.ID_ANY, "Threshold:")
        self.fit_thresholdHighRes_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator('floatPos'))
        self.fit_thresholdHighRes_value.SetValue(str(self.config.fit_highRes_threshold))
        self.fit_thresholdHighRes_value.Bind(wx.EVT_TEXT, self.onApply)

        window_highRes_label = wx.StaticText(panel, wx.ID_ANY, "Window size (points):")
        self.fit_windowHighRes_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator('floatPos'))
        self.fit_windowHighRes_value.SetValue(str(self.config.fit_highRes_window))
        self.fit_windowHighRes_value.Bind(wx.EVT_TEXT, self.onApply)

        width_highRes_label = wx.StaticText(panel, wx.ID_ANY, "Peak width:")
        self.fit_widthHighRes_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=validator('floatPos'))
        self.fit_widthHighRes_value.SetValue(str(self.config.fit_highRes_width))
        self.fit_widthHighRes_value.Bind(wx.EVT_TEXT, self.onApply)

        fitChargeStates_label = wx.StaticText(panel, wx.ID_ANY, "Isotopic fit:")
        self.fit_isotopes_check = makeCheckbox(panel, "")
        self.fit_isotopes_check.SetValue(self.config.fit_highRes_isotopicFit)
        self.fit_isotopes_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        __fit_isotopes_tip = makeSuperTip(self.fit_isotopes_check, **self.help.fit_showIsotopes)

        horizontal_line_1 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_2 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_3 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        highlight_label = wx.StaticText(panel, wx.ID_ANY, "Highlight:")
        self.fit_highlight_check = makeCheckbox(panel, "")
        self.fit_highlight_check.SetValue(self.config.fit_highlight)
        self.fit_highlight_check.Bind(wx.EVT_CHECKBOX, self.onApply)

        labels_label = wx.StaticText(panel, wx.ID_ANY, "Labels:")
        self.fit_show_labels_check = makeCheckbox(panel, "")
        self.fit_show_labels_check.SetValue(self.config.fit_show_labels)
        self.fit_show_labels_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        self.fit_show_labels_check.Bind(wx.EVT_CHECKBOX, self.enableDisableBoxes)

        max_labels_label = wx.StaticText(panel, wx.ID_ANY, "Max no. labels:")
        self.fit_max_labels = wx.SpinCtrlDouble(panel, -1,
                                                value=str(self.config.fit_show_labels_max_count),
                                                min=0, max=250,
                                                initial=self.config.fit_show_labels_max_count,
                                                inc=50, size=(90, -1))
        self.fit_max_labels.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)

        self.fit_show_labels_mz_check = makeCheckbox(panel, "m/z")
        self.fit_show_labels_mz_check.SetValue(self.config.fit_show_labels_mz)
        self.fit_show_labels_mz_check.Bind(wx.EVT_CHECKBOX, self.onApply)

        self.fit_show_labels_int_check = makeCheckbox(panel, "intensity")
        self.fit_show_labels_int_check.SetValue(self.config.fit_show_labels_int)
        self.fit_show_labels_int_check.Bind(wx.EVT_CHECKBOX, self.onApply)

        remove_label_overlap_label = wx.StaticText(panel, wx.ID_ANY, "Optimise label position:")
        self.fit_labels_optimise_position_check = makeCheckbox(panel, "")
        self.fit_labels_optimise_position_check.SetValue(self.config.fit_labels_optimise_position)
        self.fit_labels_optimise_position_check.Bind(wx.EVT_CHECKBOX, self.onApply)

        annot_grid = wx.GridBagSizer(5, 5)
        n = 0
        annot_grid.Add(highlight_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        annot_grid.Add(self.fit_highlight_check, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        annot_grid.Add(labels_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        annot_grid.Add(self.fit_show_labels_check, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        annot_grid.Add(max_labels_label, (n, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        annot_grid.Add(self.fit_max_labels, (n, 3), wx.GBSpan(1, 1), flag=wx.EXPAND)
        annot_grid.Add(self.fit_show_labels_mz_check, (n, 4), wx.GBSpan(1, 1), flag=wx.EXPAND)
        annot_grid.Add(self.fit_show_labels_int_check, (n, 5), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        annot_grid.Add(remove_label_overlap_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        annot_grid.Add(self.fit_labels_optimise_position_check, (n, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)

        xaxisLimit_label = wx.StaticText(panel, wx.ID_ANY, "Use current x-axis range:")
        self.fit_xaxisLimit_check = makeCheckbox(panel, "")
        self.fit_xaxisLimit_check.SetValue(self.config.fit_xaxis_limit)
        self.fit_xaxisLimit_check.Bind(wx.EVT_CHECKBOX, self.onApply)

        addPeaks_label = wx.StaticText(panel, wx.ID_ANY, "Add peaks to peak list:")
        self.fit_addPeaks_check = makeCheckbox(panel, "")
        self.fit_addPeaks_check.SetValue(self.config.fit_addPeaks)
        self.fit_addPeaks_check.Bind(wx.EVT_CHECKBOX, self.onApply)

        addPeaksToAnnotations_label = wx.StaticText(panel, wx.ID_ANY, "Add peaks to annotations:")
        self.fit_addPeaksToAnnotations_check = makeCheckbox(panel, "")
        self.fit_addPeaksToAnnotations_check.SetValue(self.config.fit_addPeaksToAnnotations)
        self.fit_addPeaksToAnnotations_check.Bind(wx.EVT_CHECKBOX, self.onApply)

        check_grid = wx.GridBagSizer(5, 5)
        n = 0
        check_grid.Add(xaxisLimit_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        check_grid.Add(self.fit_xaxisLimit_check, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        check_grid.Add(addPeaks_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, border=20)
        check_grid.Add(self.fit_addPeaks_check, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        check_grid.Add(addPeaksToAnnotations_label, (n, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT, border=20)
        check_grid.Add(self.fit_addPeaksToAnnotations_check, (n, 3), wx.GBSpan(1, 1), flag=wx.EXPAND)

        self.fit_findPeaksBtn = wx.Button(panel, wx.ID_OK, "Find peaks", size=(-1, 22))
        self.fit_findPeaksBtn.Bind(wx.EVT_BUTTON, self.onPickPeaksThreaded)

        self.fit_cancelBtn = wx.Button(panel, wx.ID_OK, "Cancel", size=(-1, 22))
        self.fit_cancelBtn.Bind(wx.EVT_BUTTON, self.onClose)

        # pack elements
        grid = wx.GridBagSizer(5, 5)
        n = 0
        grid.Add(fitPlot_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.fit_fitPlot_choice, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(threshold_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.fit_threshold_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(window_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.fit_window_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(width_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.fit_width_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(asymmetricity_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.fit_asymmetricRatio_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(smooth_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.fit_smooth_check, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(sigma_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.fit_sigma_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        grid.Add(self.fit_show_smoothed, (n, 2), wx.GBSpan(1, 1), flag=wx.EXPAND)

        highRes_grid = wx.GridBagSizer(2, 2)
        n = 0
        highRes_grid.Add(highRes_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        highRes_grid.Add(self.fit_highRes_check, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        highRes_grid.Add(threshold_highRes_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        highRes_grid.Add(self.fit_thresholdHighRes_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        highRes_grid.Add(window_highRes_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        highRes_grid.Add(self.fit_windowHighRes_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        highRes_grid.Add(width_highRes_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        highRes_grid.Add(self.fit_widthHighRes_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        highRes_grid.Add(fitChargeStates_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        highRes_grid.Add(self.fit_isotopes_check, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        highRes_box_sizer.Add(highRes_grid, 0, wx.EXPAND, 10)
        n = 7
        grid.Add(highRes_box_sizer, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND | wx.ALIGN_LEFT)
        n = n + 1
        grid.Add(horizontal_line_1, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n = n + 1
        grid.Add(annot_grid, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n = n + 1
        grid.Add(horizontal_line_2, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n = n + 1
        grid.Add(check_grid, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n = n + 1
        grid.Add(horizontal_line_3, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n = n + 1
        grid.Add(self.fit_findPeaksBtn, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        grid.Add(self.fit_cancelBtn, (n, 2), wx.GBSpan(1, 1), flag=wx.EXPAND)

        mainSizer.Add(grid, 0, wx.ALIGN_CENTER_HORIZONTAL, 10)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizerAndFit(mainSizer)

        return panel

    def makePanel_ORIGAMI(self, panel):
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        acquisition_label = wx.StaticText(panel, wx.ID_ANY, "Acquisition method:")
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

        spv_label = wx.StaticText(panel, wx.ID_ANY, "Scans per voltage:")
        self.origami_scansPerVoltage_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('intPos'))
        self.origami_scansPerVoltage_value.SetValue(str(self.config.origami_spv))
        self.origami_scansPerVoltage_value.Bind(wx.EVT_TEXT, self.onApply)

        scan_label = wx.StaticText(panel, wx.ID_ANY, "First scan:")
        self.origami_startScan_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('intPos'))
        self.origami_startScan_value.SetValue(str(self.config.origami_startScan))
        self.origami_startScan_value.Bind(wx.EVT_TEXT, self.onApply)

        startVoltage_label = wx.StaticText(panel, wx.ID_ANY, "First voltage:")
        self.origami_startVoltage_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('floatPos'))
        self.origami_startVoltage_value.SetValue(str(self.config.origami_startVoltage))
        self.origami_startVoltage_value.Bind(wx.EVT_TEXT, self.onApply)

        endVoltage_label = wx.StaticText(panel, wx.ID_ANY, "Final voltage:")
        self.origami_endVoltage_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('floatPos'))
        self.origami_endVoltage_value.SetValue(str(self.config.origami_endVoltage))
        self.origami_endVoltage_value.Bind(wx.EVT_TEXT, self.onApply)

        stepVoltage_label = wx.StaticText(panel, wx.ID_ANY, "Voltage step:")
        self.origami_stepVoltage_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('floatPos'))
        self.origami_stepVoltage_value.SetValue(str(self.config.origami_stepVoltage))
        self.origami_stepVoltage_value.Bind(wx.EVT_TEXT, self.onApply)

        boltzmann_label = wx.StaticText(panel, wx.ID_ANY, "Boltzmann offset:")
        self.origami_boltzmannOffset_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                                         validator=validator('floatPos'))
        self.origami_boltzmannOffset_value.SetValue(str(self.config.origami_boltzmannOffset))
        self.origami_boltzmannOffset_value.Bind(wx.EVT_TEXT, self.onApply)

        exponentialPercentage_label = wx.StaticText(panel, wx.ID_ANY, "Exponential percentage:")
        self.origami_exponentialPercentage_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('floatPos'))
        self.origami_exponentialPercentage_value.SetValue(str(self.config.origami_exponentialPercentage))
        self.origami_exponentialPercentage_value.Bind(wx.EVT_TEXT, self.onApply)

        exponentialIncrement_label = wx.StaticText(panel, wx.ID_ANY, "Exponential increment:")
        self.origami_exponentialIncrement_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('floatPos'))
        self.origami_exponentialIncrement_value.SetValue(str(self.config.origami_exponentialIncrement))
        self.origami_exponentialIncrement_value.Bind(wx.EVT_TEXT, self.onApply)

        import_label = wx.StaticText(panel, wx.ID_ANY, "Import list:")
        self.origami_loadListBtn = wx.Button(panel, wx.ID_OK, "...", size=(-1, 22))
        self.origami_loadListBtn.Bind(wx.EVT_BUTTON, self.presenter.onUserDefinedListImport)

#         horizontal_line = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
#
#         self.origami_applyBtn = wx.Button(panel, wx.ID_OK, "Apply", size=(-1, 22))
#         self.origami_applyBtn.Bind(wx.EVT_BUTTON, self.onProcessMS)
#
#         self.origami_cancelBtn = wx.Button(panel, wx.ID_OK, "Cancel", size=(-1, 22))
#         self.origami_cancelBtn.Bind(wx.EVT_BUTTON, self.onClose)

        # pack elements
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(acquisition_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.origami_method_choice, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
#         grid.Add(self.origami_loadParams, (n,2), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT)
        n = n + 1
        grid.Add(spv_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.origami_scansPerVoltage_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(scan_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.origami_startScan_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(startVoltage_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.origami_startVoltage_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(endVoltage_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.origami_endVoltage_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(stepVoltage_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.origami_stepVoltage_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(boltzmann_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.origami_boltzmannOffset_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(exponentialPercentage_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.origami_exponentialPercentage_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(exponentialIncrement_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.origami_exponentialIncrement_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(import_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.origami_loadListBtn, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
#         n = n + 1
#         grid.Add(horizontal_line, (n,0), wx.GBSpan(1,3), flag=wx.EXPAND)
#         n = n + 1
#         grid.Add(self.origami_applyBtn, (n,1), wx.GBSpan(1,1))
#         grid.Add(self.origami_cancelBtn, (n,2), wx.GBSpan(1,1))

        mainSizer.Add(grid, 0, wx.ALIGN_CENTER_HORIZONTAL, 10)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizerAndFit(mainSizer)

        return panel

    def makePanel_MS(self, panel):
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        dtms_staticBox = makeStaticBox(panel, "DT/MS binning parameters", size=(-1, -1), color=wx.BLACK)
        dtms_staticBox.SetSize((-1, -1))
        dtms_box_sizer = wx.StaticBoxSizer(dtms_staticBox, wx.HORIZONTAL)

        bin_msdt_label = wx.StaticText(panel, wx.ID_ANY, "DT/MS bin size:")
        self.bin_msdt_binSize_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('floatPos'))
        self.bin_msdt_binSize_value.SetValue(str(self.config.ms_dtmsBinSize))
        self.bin_msdt_binSize_value.Bind(wx.EVT_TEXT, self.onApply)

        crop_staticBox = makeStaticBox(panel, "Crop parameters", size=(-1, -1), color=wx.BLACK)
        crop_staticBox.SetSize((-1, -1))
        crop_box_sizer = wx.StaticBoxSizer(crop_staticBox, wx.HORIZONTAL)

        crop_min_label = wx.StaticText(panel, wx.ID_ANY, "m/z start:")
        self.crop_min_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('floatPos'))
        self.crop_min_value.SetValue(str(self.config.ms_crop_min))
        self.crop_min_value.Bind(wx.EVT_TEXT, self.onApply)

        crop_max_label = wx.StaticText(panel, wx.ID_ANY, "end:")
        self.crop_max_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('floatPos'))
        self.crop_max_value.SetValue(str(self.config.ms_crop_max))
        self.crop_max_value.Bind(wx.EVT_TEXT, self.onApply)

        massSpec_staticBox = makeStaticBox(panel, "Linearization parameters", size=(-1, -1), color=wx.BLACK)
        massSpec_staticBox.SetSize((-1, -1))
        massSpec_box_sizer = wx.StaticBoxSizer(massSpec_staticBox, wx.HORIZONTAL)

        self.bin_RT_window_check = makeCheckbox(panel, "Enable MS linearization in chromatogram/mobiligram window")
        self.bin_RT_window_check.SetValue(self.config.ms_enable_in_RT)
        self.bin_RT_window_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        __bin_RT_window_tip = makeSuperTip(self.bin_RT_window_check, **self.help.bin_MS_in_RT)

        self.bin_MML_window_check = makeCheckbox(panel, "Enable MS linearization when loading Manual aIM-MS datasets")
        self.bin_MML_window_check.SetValue(self.config.ms_enable_in_MML_start)
        self.bin_MML_window_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        __bin_MML_window_tip = makeSuperTip(self.bin_MML_window_check, **self.help.bin_MS_when_loading_MML)

        linearizationMode_label = wx.StaticText(panel, wx.ID_ANY, "Linearization mode:")
        self.bin_linearizationMode_choice = wx.Choice(panel, -1, choices=self.config.ms_linearization_mode_choices,
                                          size=(-1, -1))
        self.bin_linearizationMode_choice.SetStringSelection(self.config.ms_linearization_mode)
        self.bin_linearizationMode_choice.Bind(wx.EVT_CHOICE, self.onApply)

        bin_ms_min_label = wx.StaticText(panel, wx.ID_ANY, "m/z start:")
        self.bin_mzStart_value = wx.TextCtrl(panel, -1, "", size=(65, -1),
                                          validator=validator('floatPos'))
        self.bin_mzStart_value.SetValue(str(self.config.ms_mzStart))
        self.bin_mzStart_value.Bind(wx.EVT_TEXT, self.onApply)

        bin_ms_max_label = wx.StaticText(panel, wx.ID_ANY, "end:")
        self.bin_mzEnd_value = wx.TextCtrl(panel, -1, "", size=(65, -1),
                                          validator=validator('floatPos'))
        self.bin_mzEnd_value.SetValue(str(self.config.ms_mzEnd))
        self.bin_mzEnd_value.Bind(wx.EVT_TEXT, self.onApply)

        self.bin_autoRange_check = makeCheckbox(panel, "Automatic range")
        self.bin_autoRange_check.SetValue(self.config.ms_auto_range)
        self.bin_autoRange_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        self.bin_autoRange_check.Bind(wx.EVT_CHECKBOX, self.enableDisableBoxes)
#         self.bin_autoRange_check = makeSuperTip(self.bin_MML_window_check, **self.help.bin_MS_when_loading_MML)

        bin_ms_binsize_label = wx.StaticText(panel, wx.ID_ANY, "m/z bin size:")
        self.bin_mzBinSize_value = wx.TextCtrl(panel, -1, "", size=(65, -1),
                                          validator=validator('floatPos'))
        self.bin_mzBinSize_value.SetValue(str(self.config.ms_mzBinSize))
        self.bin_mzBinSize_value.Bind(wx.EVT_TEXT, self.onApply)

        process_staticBox = makeStaticBox(panel, "Smoothing and normalization parameters", size=(-1, -1), color=wx.BLACK)
        process_staticBox.SetSize((-1, -1))
        process_box_sizer = wx.StaticBoxSizer(process_staticBox, wx.HORIZONTAL)

        smoothFcn_label = wx.StaticText(panel, wx.ID_ANY, "Smooth function:")
        self.ms_smoothFcn_choice = wx.Choice(panel, -1, choices=self.config.ms_smooth_choices,
                                          size=(-1, -1))
        self.ms_smoothFcn_choice.SetStringSelection(self.config.ms_smooth_mode)
        self.ms_smoothFcn_choice.Bind(wx.EVT_CHOICE, self.onApply)
        self.ms_smoothFcn_choice.Bind(wx.EVT_CHOICE, self.enableDisableBoxes)

        polynomial_label = wx.StaticText(panel, wx.ID_ANY, "Polynomial:")
        self.ms_polynomial_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('intPos'))
        self.ms_polynomial_value.SetValue(str(self.config.ms_smooth_polynomial))
        self.ms_polynomial_value.Bind(wx.EVT_TEXT, self.onApply)

        window_label = wx.StaticText(panel, wx.ID_ANY, "Window size:")
        self.ms_window_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('intPos'))
        self.ms_window_value.SetValue(str(self.config.ms_smooth_window))
        self.ms_window_value.Bind(wx.EVT_TEXT, self.onApply)

        sigma_label = wx.StaticText(panel, wx.ID_ANY, "Sigma:")
        self.ms_sigma_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('floatPos'))
        self.ms_sigma_value.SetValue(str(self.config.ms_smooth_sigma))
        self.ms_sigma_value.Bind(wx.EVT_TEXT, self.onApply)

        threshold_label = wx.StaticText(panel, wx.ID_ANY, "Baseline subtraction:")
        self.ms_threshold_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('floatPos'))
        self.ms_threshold_value.SetValue(str(self.config.ms_threshold))
        self.ms_threshold_value.Bind(wx.EVT_TEXT, self.onApply)

        normalize_label = wx.StaticText(panel, wx.ID_ANY, "Normalize:")
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
        __ms_applyBtn_tip = makeSuperTip(self.ms_applyBtn, **self.help.process_mass_spectra_replotBtn)

        self.ms_processBtn = wx.Button(panel, ID_processSettings_processMS, "Process", size=(-1, 22))
        __ms_processBtn_tip = makeSuperTip(self.ms_processBtn, **self.help.process_mass_spectra_processesBtn)

        self.ms_cancelBtn = wx.Button(panel, wx.ID_OK, "Cancel", size=(-1, 22))

        self.ms_applyBtn.Bind(wx.EVT_BUTTON, self.onProcessMS)
        self.ms_processBtn.Bind(wx.EVT_BUTTON, self.onProcessMS)
        self.ms_cancelBtn.Bind(wx.EVT_BUTTON, self.onClose)

        steps_staticBox = makeStaticBox(panel, "Processing steps...", size=(-1, -1), color=wx.BLACK)
        steps_staticBox.SetSize((-1, -1))
        steps_box_sizer = wx.StaticBoxSizer(steps_staticBox, wx.HORIZONTAL)

        self.ms_process_crop = makeCheckbox(panel, "Crop spectrum")
        self.ms_process_crop.SetValue(self.config.ms_process_crop)
        self.ms_process_crop.Bind(wx.EVT_CHECKBOX, self.onApply)

        self.ms_process_linearize = makeCheckbox(panel, "Linearize spectrum")
        self.ms_process_linearize.SetValue(self.config.ms_process_linearize)
        self.ms_process_linearize.Bind(wx.EVT_CHECKBOX, self.onApply)

        self.ms_process_smooth = makeCheckbox(panel, "Smooth spectrum")
        self.ms_process_smooth.SetValue(self.config.ms_process_smooth)
        self.ms_process_smooth.Bind(wx.EVT_CHECKBOX, self.onApply)

        self.ms_process_threshold = makeCheckbox(panel, "Baseline subtract")
        self.ms_process_threshold.SetValue(self.config.ms_process_threshold)
        self.ms_process_threshold.Bind(wx.EVT_CHECKBOX, self.onApply)

        self.ms_process_normalize = makeCheckbox(panel, "Normalize")
        self.ms_process_normalize.SetValue(self.config.ms_process_normalize)
        self.ms_process_normalize.Bind(wx.EVT_CHECKBOX, self.onApply)

        # pack elements
        steps_grid = wx.GridBagSizer(2, 2)
        n = 0
        steps_grid.Add(self.ms_process_crop, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        steps_grid.Add(self.ms_process_linearize, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        steps_grid.Add(self.ms_process_smooth, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        steps_grid.Add(self.ms_process_threshold, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        steps_grid.Add(self.ms_process_normalize, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        steps_box_sizer.Add(steps_grid, 0, wx.EXPAND, 10)

        crop_grid = wx.GridBagSizer(2, 2)
        n = 0
        crop_grid.Add(crop_min_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        crop_grid.Add(self.crop_min_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        crop_grid.Add(crop_max_label, (n, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        crop_grid.Add(self.crop_max_value, (n, 3), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        crop_box_sizer.Add(crop_grid, 0, wx.EXPAND, 10)

        ms_grid = wx.GridBagSizer(2, 2)
        n = 0
        ms_grid.Add(linearizationMode_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        ms_grid.Add(self.bin_linearizationMode_choice, (n, 1), wx.GBSpan(1, 4), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n = n + 1
        ms_grid.Add(bin_ms_min_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        ms_grid.Add(self.bin_mzStart_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        ms_grid.Add(bin_ms_max_label, (n, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        ms_grid.Add(self.bin_mzEnd_value, (n, 3), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        ms_grid.Add(self.bin_autoRange_check, (n, 4), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        ms_grid.Add(bin_ms_binsize_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        ms_grid.Add(self.bin_mzBinSize_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        ms_grid.Add(self.bin_RT_window_check, (n, 0), wx.GBSpan(1, 5), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        ms_grid.Add(self.bin_MML_window_check, (n, 0), wx.GBSpan(1, 5), flag=wx.ALIGN_CENTER_VERTICAL)
        massSpec_box_sizer.Add(ms_grid, 0, wx.EXPAND, 10)

        dtms_grid = wx.GridBagSizer(2, 2)
        n = 0
        dtms_grid.Add(bin_msdt_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        dtms_grid.Add(self.bin_msdt_binSize_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        dtms_box_sizer.Add(dtms_grid, 0, wx.EXPAND, 10)

        process_grid = wx.GridBagSizer(2, 2)
        n = 0
        process_grid.Add(smoothFcn_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        process_grid.Add(self.ms_smoothFcn_choice, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        process_grid.Add(polynomial_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        process_grid.Add(self.ms_polynomial_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        process_grid.Add(window_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        process_grid.Add(self.ms_window_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        process_grid.Add(sigma_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        process_grid.Add(self.ms_sigma_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        process_grid.Add(threshold_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        process_grid.Add(self.ms_threshold_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        process_grid.Add(normalize_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        process_grid.Add(self.ms_normalizeTgl, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        process_grid.Add(self.ms_normalizeFcn_choice, (n, 2), wx.GBSpan(1, 1), flag=wx.EXPAND)
        process_box_sizer.Add(process_grid, 0, wx.EXPAND, 10)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(dtms_box_sizer, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND | wx.ALIGN_LEFT)
        n = n + 1
        grid.Add(crop_box_sizer, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND | wx.ALIGN_LEFT)
        n = n + 1
        grid.Add(massSpec_box_sizer, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND | wx.ALIGN_LEFT)
        n = n + 1
        grid.Add(process_box_sizer, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND | wx.ALIGN_LEFT)
        n = n + 1
        grid.Add(steps_box_sizer, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND | wx.ALIGN_LEFT)
        n = n + 1
        grid.Add(horizontal_line_1, (n, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        n = n + 1
        grid.Add(self.ms_applyBtn, (n, 0), wx.GBSpan(1, 1))
        grid.Add(self.ms_processBtn, (n, 1), wx.GBSpan(1, 1))
        grid.Add(self.ms_cancelBtn, (n, 2), wx.GBSpan(1, 1))

        mainSizer.Add(grid, 0, wx.ALIGN_CENTER_HORIZONTAL, 10)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizerAndFit(mainSizer)

        return panel

    def makePanel_2D(self, panel):
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        smoothFcn_label = wx.StaticText(panel, wx.ID_ANY, "Smooth function:")
        self.plot2D_smoothFcn_choice = wx.Choice(panel, -1, choices=self.config.plot2D_smooth_choices,
                                          size=(-1, -1))
        self.plot2D_smoothFcn_choice.SetStringSelection(self.config.plot2D_smooth_mode)
        self.plot2D_smoothFcn_choice.Bind(wx.EVT_CHOICE, self.onApply)
        self.plot2D_smoothFcn_choice.Bind(wx.EVT_CHOICE, self.enableDisableBoxes)

        polynomial_label = wx.StaticText(panel, wx.ID_ANY, "Polynomial:")
        self.plot2D_polynomial_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('intPos'))
        self.plot2D_polynomial_value.SetValue(str(self.config.plot2D_smooth_polynomial))
        self.plot2D_polynomial_value.Bind(wx.EVT_TEXT, self.onApply)

        window_label = wx.StaticText(panel, wx.ID_ANY, "Window size:")
        self.plot2D_window_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('intPos'))
        self.plot2D_window_value.SetValue(str(self.config.plot2D_smooth_window))
        self.plot2D_window_value.Bind(wx.EVT_TEXT, self.onApply)

        sigma_label = wx.StaticText(panel, wx.ID_ANY, "Sigma:")
        self.plot2D_sigma_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                              validator=validator('floatPos'))
        self.plot2D_sigma_value.SetValue(str(self.config.plot2D_smooth_sigma))
        self.plot2D_sigma_value.Bind(wx.EVT_TEXT, self.onApply)

        threshold_label = wx.StaticText(panel, wx.ID_ANY, "Threshold:")
        self.plot2D_threshold_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('floatPos'))
        self.plot2D_threshold_value.SetValue(str(self.config.plot2D_threshold))
        self.plot2D_threshold_value.Bind(wx.EVT_TEXT, self.onApply)

        normalize_label = wx.StaticText(panel, wx.ID_ANY, "Normalize:")
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
        grid.Add(smoothFcn_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot2D_smoothFcn_choice, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(polynomial_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot2D_polynomial_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(window_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot2D_window_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(sigma_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot2D_sigma_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(threshold_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot2D_threshold_value, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(normalize_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.plot2D_normalizeTgl, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        grid.Add(self.plot2D_normalizeFcn_choice, (n, 2), wx.GBSpan(1, 1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(horizontal_line, (n, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
        n = n + 1
        grid.Add(self.plot2D_applyBtn, (n, 0), wx.GBSpan(1, 1))
        grid.Add(self.plot2D_processBtn, (n, 1), wx.GBSpan(1, 1))
        grid.Add(self.plot2D_cancelBtn, (n, 2), wx.GBSpan(1, 1))

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

        self.mz_label = wx.StaticText(panel, wx.ID_ANY, "m/z (Da):")
        self.rt_label = wx.StaticText(panel, wx.ID_ANY, "RT (min): ")
        self.dt_label = wx.StaticText(panel, wx.ID_ANY, "DT (bins):")
        start_label = wx.StaticText(panel, wx.ID_ANY, "Min:")
        end_label = wx.StaticText(panel, wx.ID_ANY, "Max:")
        pusherFreq_label = wx.StaticText(panel, wx.ID_ANY, "Pusher frequency:")
        scanTime_label = wx.StaticText(panel, wx.ID_ANY, "Scan time:")

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

        self.extract_rt_scans_check = makeCheckbox(panel, "In scans")
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

        self.extract_dt_ms_check = makeCheckbox(panel, "In ms")
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
        ms_staticBox.SetSize((-1, -1))
        ms_box_sizer = wx.StaticBoxSizer(ms_staticBox, wx.HORIZONTAL)

        self.extract_extractMS_check = makeCheckbox(panel, "Enable")
        self.extract_extractMS_check.SetValue(self.config.extract_massSpectra)
        self.extract_extractMS_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        self.extract_extractMS_check.Bind(wx.EVT_CHECKBOX, self.enableDisableBoxes)

        self.extract_extractMS_ms_check = makeCheckbox(panel, "m/z")
        self.extract_extractMS_ms_check.SetValue(False)
        self.extract_extractMS_ms_check.Bind(wx.EVT_CHECKBOX, self.onApply)

        self.extract_extractMS_rt_check = makeCheckbox(panel, "RT")
        self.extract_extractMS_rt_check.SetValue(True)
        self.extract_extractMS_rt_check.Bind(wx.EVT_CHECKBOX, self.onApply)

        self.extract_extractMS_dt_check = makeCheckbox(panel, "DT")
        self.extract_extractMS_dt_check.SetValue(True)
        self.extract_extractMS_dt_check.Bind(wx.EVT_CHECKBOX, self.onApply)

        rt_staticBox = makeStaticBox(panel, "Chromatogram", size=(-1, -1), color=wx.BLACK)
        rt_staticBox.SetSize((-1, -1))
        rt_box_sizer = wx.StaticBoxSizer(rt_staticBox, wx.HORIZONTAL)

        self.extract_extractRT_check = makeCheckbox(panel, "Enable")
        self.extract_extractRT_check.SetValue(self.config.extract_chromatograms)
        self.extract_extractRT_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        self.extract_extractRT_check.Bind(wx.EVT_CHECKBOX, self.enableDisableBoxes)

        self.extract_extractRT_ms_check = makeCheckbox(panel, "m/z")
        self.extract_extractRT_ms_check.SetValue(True)
        self.extract_extractRT_ms_check.Bind(wx.EVT_CHECKBOX, self.onApply)

        self.extract_extractRT_dt_check = makeCheckbox(panel, "DT")
        self.extract_extractRT_dt_check.SetValue(True)
        self.extract_extractRT_dt_check.Bind(wx.EVT_CHECKBOX, self.onApply)

        dt_staticBox = makeStaticBox(panel, "Drift time (1D)", size=(-1, -1), color=wx.BLACK)
        dt_staticBox.SetSize((-1, -1))
        dt_box_sizer = wx.StaticBoxSizer(dt_staticBox, wx.HORIZONTAL)

        self.extract_extractDT_check = makeCheckbox(panel, "Enable")
        self.extract_extractDT_check.SetValue(self.config.extract_driftTime1D)
        self.extract_extractDT_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        self.extract_extractDT_check.Bind(wx.EVT_CHECKBOX, self.enableDisableBoxes)

        self.extract_extractDT_ms_check = makeCheckbox(panel, "m/z")
        self.extract_extractDT_ms_check.SetValue(True)
        self.extract_extractDT_ms_check.Bind(wx.EVT_CHECKBOX, self.onApply)

        self.extract_extractDT_rt_check = makeCheckbox(panel, "RT")
        self.extract_extractDT_rt_check.SetValue(True)
        self.extract_extractDT_rt_check.Bind(wx.EVT_CHECKBOX, self.onApply)

        dt2d_staticBox = makeStaticBox(panel, "Drift time (2D)", size=(-1, -1), color=wx.BLACK)
        dt2d_staticBox.SetSize((-1, -1))
        dt2d_box_sizer = wx.StaticBoxSizer(dt2d_staticBox, wx.HORIZONTAL)

        self.extract_extract2D_check = makeCheckbox(panel, "Enable")
        self.extract_extract2D_check.SetValue(self.config.extract_driftTime2D)
        self.extract_extract2D_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        self.extract_extract2D_check.Bind(wx.EVT_CHECKBOX, self.enableDisableBoxes)

        self.extract_extract2D_ms_check = makeCheckbox(panel, "m/z")
        self.extract_extract2D_ms_check.SetValue(True)
        self.extract_extract2D_ms_check.Bind(wx.EVT_CHECKBOX, self.onApply)

        self.extract_extract2D_rt_check = makeCheckbox(panel, "RT")
        self.extract_extract2D_rt_check.SetValue(True)
        self.extract_extract2D_rt_check.Bind(wx.EVT_CHECKBOX, self.onApply)

        horizontal_line = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        add_to_document_label = wx.StaticText(panel, wx.ID_ANY, "Add data to document:")
        self.extract_add_to_document = makeCheckbox(panel, "")
        self.extract_add_to_document.SetValue(False)
        self.extract_add_to_document.Bind(wx.EVT_CHECKBOX, self.onApply)

        self.extract_extractBtn = wx.Button(panel, wx.ID_OK, "Extract", size=(-1, 22))
        self.extract_cancelBtn = wx.Button(panel, wx.ID_OK, "Cancel", size=(-1, 22))

        self.extract_extractBtn.Bind(wx.EVT_BUTTON, self.onExtractData)
        self.extract_cancelBtn.Bind(wx.EVT_BUTTON, self.onClose)

        # pack elements
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(extractData_sep_label, (n, 0), wx.GBSpan(1, 3), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        n = n + 1
        grid.Add(start_label, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER)
        grid.Add(end_label, (n, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER)
        n = n + 1
        grid.Add(self.mz_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.extract_mzStart_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.extract_mzEnd_value, (n, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(self.rt_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.extract_rtStart_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.extract_rtEnd_value, (n, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.extract_rt_scans_check, (n, 3), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(scanTime_label, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.extract_scanTime_value, (n, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(self.dt_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.extract_dtStart_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.extract_dtEnd_value, (n, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.extract_dt_ms_check, (n, 3), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(pusherFreq_label, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.extract_pusherFreq_value, (n, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(self.extract_extractMS_check, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(self.extract_extractRT_check, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(self.extract_extractDT_check, (n, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(self.extract_extract2D_check, (n, 3), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_HORIZONTAL)

        # extract MS
        extract_ms_grid = wx.GridBagSizer(2, 2)
        extract_ms_grid.Add(self.extract_extractMS_ms_check, (0, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        extract_ms_grid.Add(self.extract_extractMS_rt_check, (1, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        extract_ms_grid.Add(self.extract_extractMS_dt_check, (2, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        ms_box_sizer.Add(extract_ms_grid, 0, wx.EXPAND, 10)

        # extract RT
        extract_rt_grid = wx.GridBagSizer(2, 2)
        extract_rt_grid.Add(self.extract_extractRT_ms_check, (0, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        extract_rt_grid.Add(self.extract_extractRT_dt_check, (1, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        rt_box_sizer.Add(extract_rt_grid, 0, wx.EXPAND, 10)

        # extract DT
        extract_dt_grid = wx.GridBagSizer(2, 2)
        extract_dt_grid.Add(self.extract_extractDT_ms_check, (0, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        extract_dt_grid.Add(self.extract_extractDT_rt_check, (1, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        dt_box_sizer.Add(extract_dt_grid, 0, wx.EXPAND, 10)

        # extract 2D
        extract_2d_grid = wx.GridBagSizer(2, 2)
        extract_2d_grid.Add(self.extract_extract2D_ms_check, (0, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        extract_2d_grid.Add(self.extract_extract2D_rt_check, (1, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        dt2d_box_sizer.Add(extract_2d_grid, 0, wx.EXPAND, 10)

        n = n + 1
        grid.Add(ms_box_sizer, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(rt_box_sizer, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(dt_box_sizer, (n, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(dt2d_box_sizer, (n, 3), wx.GBSpan(1, 1), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_HORIZONTAL)
        n = n + 1
        grid.Add(horizontal_line, (n, 0), wx.GBSpan(1, 4), flag=wx.EXPAND)
        n = n + 1
        grid.Add(add_to_document_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.extract_add_to_document, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(self.extract_extractBtn, (n, 1), wx.GBSpan(1, 1))
        grid.Add(self.extract_cancelBtn, (n, 2), wx.GBSpan(1, 1))

        mainSizer.Add(grid, 0, wx.ALIGN_CENTER_HORIZONTAL, 10)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizerAndFit(mainSizer)

        return panel

    def onRunUnidecThreaded(self, evt):
        if not self.config.threading:
            self.onRunUnidec(evt)
        else:
            self.onThreading(evt, {}, action='unidec')

    def onRunUnidec(self, evt):

        # get event ID
        if isinstance(evt, int):
            evtID = evt
        else:
            evtID = evt.GetId()

        if "MS" in self.dataset:
            dataset = self.dataset['MS']
        else:
            dataset = "Mass Spectrum"

        task, plots = "auto_unidec", "all"
        if evtID == ID_processSettings_loadDataUniDec:
            task = "load_data_unidec"
            plots = []
        elif evtID == ID_processSettings_preprocessUniDec:
            task = "preprocess_unidec"
            plots = ["Processed"]
        elif evtID == ID_processSettings_autoUniDec:
            task = "auto_unidec"
            plots = ["all"]
        elif evtID == ID_processSettings_runUniDec:
            task = "run_unidec"
            plots = ["Fitted", "m/z vs Charge", "MW vs Charge", "MW distribution"]
        elif evtID == ID_processSettings_runAll:
            task = "run_all_unidec"
            plots = ["Fitted", "m/z vs Charge", "MW vs Charge", "MW distribution",
                     "m/z with isolated species", "Barchart"]
        elif evtID == ID_processSettings_pickPeaksUniDec:
            task = "pick_peaks_unidec"
            plots = ["m/z with isolated species", "Barchart"]
        elif evtID == ID_processSettings_isolateZUniDec:
            task = None
            plots = ["Isolate MW"]
        elif evtID == ID_processSettings_restoreIsolatedAll:
            task = None
            plots = ["m/z with isolated species"]
        elif evtID == ID_processSettings_replotAll:
            task = None
            plots = ["Fitted", "m/z vs Charge", "MW vs Charge", "MW distribution",
                     "m/z with isolated species", "Barchart"]
        elif evtID == ID_processSettings_showZUniDec:
            task = None
            plots = ["Charge information"]
        else:
            return

        if task in ["all", "load_data_unidec", "run_all_unidec", "preprocess_unidec"]:
            self.presenter.view.panelPlots.on_clear_unidec()

        if task is not None:
            self.data_processing.on_run_unidec(dataset, task)

        # modify GUI when necessary
        if task in ["auto_unidec", "run_unidec", "run_all_unidec"]:
            self.unidec_fit_peakWidth_value.SetValue(str(self.config.unidec_peakWidth))

        if task in ["pick_peaks_unidec", "run_all_unidec", "auto_unidec"]:
            massList, massMax = self.data_processing.get_unidec_data(data_type="mass_list")
            self.unidec_weightList_choice.SetItems(massList)
            self.unidec_weightList_choice.SetStringSelection(massMax)

        # plot
        self.onPlotUnidec(evtID, plots)

    def onPlotUnidec(self, evtID, plots):

        self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['UniDec'])
        if not isinstance(evtID, int):
            source = evtID.GetEventObject().GetName()
            evtID = evtID.GetId()
            if source == 'ChargeStates': evtID = ID_processSettings_showZUniDec

        kwargs = {'show_markers':self.config.unidec_show_markers,
                  'show_individual_lines':self.config.unidec_show_individualComponents,
                  'speedy':self.config.unidec_speedy,
                  'optimise_positions':self.config.unidec_optimiseLabelPositions}

        data = self.data_processing.get_unidec_data(data_type="unidec_data")

        for plot in plots:
            if plot in ["all", "Fitted", "Processed"]:

                try: self.presenter.view.panelPlots.on_plot_unidec_MS_v_Fit(unidec_eng_data=None,
                                                                            replot=data['Fitted'],
                                                                            **kwargs)
                except:
                    try: self.presenter.view.panelPlots.on_plot_unidec_MS(unidec_eng_data=None,
                                                                          replot=data['Processed'],
                                                                          **kwargs)
                    except: pass

            if plot in ["all", "MW distribution"]:
                try:
                    self.presenter.view.panelPlots.on_plot_unidec_mwDistribution(unidec_eng_data=None,
                                                                                 replot=data['MW distribution'],
                                                                                 **kwargs)
                except: pass

            if plot in ["all", "m/z vs Charge"]:
                try:
                    self.presenter.view.panelPlots.on_plot_unidec_mzGrid(unidec_eng_data=None,
                                                                         replot=data['m/z vs Charge'],
                                                                         **kwargs)
                except: pass

            if plot in ["all", "m/z with isolated species"]:
                try:
                    self.presenter.view.panelPlots.on_plot_unidec_individualPeaks(unidec_eng_data=None,
                                                                                  replot=data['m/z with isolated species'],
                                                                                  **kwargs)
                    try:
                        self.presenter.view.panelPlots.on_plot_unidec_MW_add_markers(data['m/z with isolated species'],
                                                                                     data['MW distribution'],
                                                                                     **kwargs)
                    except: pass
                except: pass

            if plot in ["all", "MW vs Charge"]:
                try:
                    self.presenter.view.panelPlots.on_plot_unidec_MW_v_Charge(unidec_eng_data=None,
                                                                              replot=data['MW vs Charge'],
                                                                              **kwargs)
                except: pass

            if plot in ["all", "Barchart"]:
                try: self.presenter.view.panelPlots.on_plot_unidec_barChart(unidec_eng_data=None,
                                                                            replot=data['Barchart'],
                                                                            **kwargs)
                except: pass

            if plot in ['Isolate MW']:
                try: mw_selection = "MW: {}".format(self.unidec_weightList_choice.GetStringSelection().split()[1])
                except: return
                kwargs['show_isolated_mw'] = True
                kwargs['mw_selection'] = mw_selection

                self.presenter.view.panelPlots.on_plot_unidec_individualPeaks(unidec_eng_data=None,
                                                                              replot=data['m/z with isolated species'],
                                                                              **kwargs)
            if plot in ["all", "Charge information"]:
                charges = data['Charge information']
                self.presenter.view.panelPlots.on_plot_unidec_ChargeDistribution(charges[:, 0], charges[:, 1],
                                                                                 **kwargs)

                selection = self.unidec_weightList_choice.GetStringSelection().split()[1]
                adductIon = self.unidec_adductMW_choice.GetStringSelection()

                peakpos, charges, __ = self._calculate_charge_positions(charges, selection, data['Processed']['xvals'],
                                                                        adductIon,
                                                                        remove_below=self.config.unidec_charges_label_charges)
                self.presenter.view.panelPlots.on_plot_charge_states(peakpos, charges, **kwargs)

    def onAddToAnnotations(self, evt):
        pass

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
#         self.config.unidec_speedy = self.unidec_speedy_check.GetValue()
        self.config.unidec_show_individualComponents = self.unidec_individualComponents_check.GetValue()

        self.config.unidec_charges_label_charges = str2num(self.unidec_charges_threshold_value.GetValue())
        self.config.unidec_charges_offset = str2num(self.unidec_charges_offset_value.GetValue())
        self.config.unidec_maxShown_individualLines = str2int(self.unidec_maxShownLines_value.GetValue())
#         self.config.unidec_show_chargeStates = self.unidec_chargeStates_check.GetValue()

        # Extract
        self.config.extract_mzStart = str2num(self.extract_mzStart_value.GetValue())
        self.config.extract_mzEnd = str2num(self.extract_mzEnd_value.GetValue())
        self.config.extract_rtStart = str2num(self.extract_rtStart_value.GetValue())
        self.config.extract_rtEnd = str2num(self.extract_rtEnd_value.GetValue())
        self.config.extract_dtStart = str2num(self.extract_dtStart_value.GetValue())
        self.config.extract_dtEnd = str2num(self.extract_dtEnd_value.GetValue())

        # Mass spectrum
        self.config.ms_process_crop = self.ms_process_crop.GetValue()
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

        self.config.ms_crop_min = str2num(self.crop_min_value.GetValue())
        self.config.ms_crop_max = str2num(self.crop_max_value.GetValue())

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
        self.config.fit_addPeaksToAnnotations = self.fit_addPeaksToAnnotations_check.GetValue()
        self.config.fit_highlight = self.fit_highlight_check.GetValue()
        self.config.fit_show_labels = self.fit_show_labels_check.GetValue()
        self.config.fit_show_labels_mz = self.fit_show_labels_mz_check.GetValue()
        self.config.fit_show_labels_int = self.fit_show_labels_int_check.GetValue()
        self.config.fit_show_labels_max_count = str2int(self.fit_max_labels.GetValue())
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
        self.config.fit_labels_optimise_position = self.fit_labels_optimise_position_check.GetValue()

        if self.config.autoSaveSettings:
            self.presenter.onExportConfig(evt=ID_saveConfig, verbose=False)

    def enableDisableBoxes(self, evt):
        enableDisableList = [self.fit_show_labels_int_check, self.fit_show_labels_mz_check,
                             self.fit_max_labels]

        if self.fit_show_labels_check.GetValue():
            for item in enableDisableList: item.Enable()
        else:
            for item in enableDisableList: item.Disable()

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
            disableList = [self.origami_boltzmannOffset_value, self.origami_loadListBtn]
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
            self.fit_show_smoothed.Enable()
        else:
            self.fit_sigma_value.Disable()
            self.fit_show_smoothed.Disable()

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
                self.data_processing.on_process_2D(replot=True, replot_type='2D')
            elif self.parent.panelPlots.window_plot2D == 'DT/MS':
                self.data_processing.on_process_2D(replot=True, replot_type='DT/MS')

        elif evtID == ID_processSettings_process2D:
            self.data_processing.on_process_2D_and_add_data(self.document['2D'], self.dataset['2D'], self.ionName['2D'])

        if evt != None:
            evt.Skip()

    def onProcessMS(self, evt):
        """
        Automatically process and replot MS array
        """
        evtID = evt.GetId()

        try:
            args = ("Processing document: {} | dataset: {}".format(self.document['MS'], self.dataset['MS']), 4)
            self.presenter.onThreading(evt, args, action='updateStatusbar')
        except KeyError: pass

        # only replotting
        if evtID == ID_processSettings_replotMS:
            self.data_processing.on_process_MS(replot=True)
        # processing and adding to dictionary
        elif evtID == ID_processSettings_processMS:
            self.data_processing.on_process_MS_and_add_data(self.document['MS'], self.dataset['MS'])

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
            self.config.extract_mzEnd = +1
            self.extract_mzEnd_value.SetValue(str(self.config.extract_mzEnd))
        elif self.config.extract_mzStart > self.config.extract_mzEnd:
            self.config.extract_mzStart, self.config.extract_mzEnd = self.config.extract_mzEnd, self.config.extract_mzStart

        mzStart = self.config.extract_mzStart
        mzEnd = self.config.extract_mzEnd
        xlimits = [mzStart, mzEnd]

        # chromatogram
        if self.config.extract_rtStart == self.config.extract_rtEnd:
            self.config.extract_rtEnd = +1
            self.extract_rtEnd_value.SetValue(str(self.config.extract_rtEnd))
        elif self.config.extract_rtStart > self.config.extract_rtEnd:
            self.config.extract_rtStart, self.config.extract_rtEnd = self.config.extract_rtEnd, self.config.extract_rtStart

        if self.extract_rt_scans_check.GetValue():
            if scanTime in ["", 0, None]:
                print('Scan time is incorrect. Setting value to 1')
                scanTime = 1
                self.extract_scanTime_value.SetValue(str(scanTime))
            rtStart = ((self.config.extract_rtStart + 1) * scanTime) / 60
            rtEnd = ((self.config.extract_rtEnd + 1) * scanTime) / 60
        else:
            rtStart = self.config.extract_rtStart
            rtEnd = self.config.extract_rtEnd

        # drift time
        if self.config.extract_dtStart == self.config.extract_dtEnd:
            self.config.extract_dtEnd = +1
            self.extract_dtEnd_value.SetValue(str(self.config.extract_dtEnd))
        elif self.config.extract_dtStart > self.config.extract_dtEnd:
            self.config.extract_dtStart, self.config.extract_dtEnd = self.config.extract_dtEnd, self.config.extract_dtStart

        if self.extract_dt_ms_check.GetValue():
            if pusherFreq in ["", 0, None]:
                print('Pusher frequency is incorrect. Setting value to 1')
                pusherFreq = 1
                self.extract_pusherFreq_value.SetValue(str(pusherFreq))
            dtStart = int(self.config.extract_dtStart / (pusherFreq * 0.001))
            dtEnd = int(self.config.extract_dtEnd / (pusherFreq * 0.001))
        else:
            dtStart = self.config.extract_dtStart
            dtEnd = self.config.extract_dtEnd

        # create titles
        mz_title = "ion=%s-%s" % (np.round(mzStart, 2), np.round(mzEnd, 2))
        rt_title = "rt=%s-%s" % (np.round(rtStart, 2), np.round(rtEnd, 2))
        dt_title = "dt=%s-%s" % (np.round(dtStart, 2), np.round(dtEnd, 2))

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
            try:
                extract_kwargs = {'return_data':True}
                xvals_MS, yvals_MS = rawMassLynx_MS_extract(path=document.path,
                                                            mz_start=mzStart, mz_end=mzEnd,
                                                            rt_start=rtStart, rt_end=rtEnd,
                                                            dt_start=dtStart, dt_end=dtEnd,
                                                            driftscope_path=self.config.driftscopePath,
                                                            **extract_kwargs)
                self.presenter.view.panelPlots.on_plot_MS(xvals_MS, yvals_MS)
                if add_to_document:
                    item_name = "%s, %s, %s" % (mz_title, rt_title, dt_title)
                    document.gotMultipleMS = True
                    document.multipleMassSpectrum[item_name] = {'xvals':xvals_MS,
                                                                'yvals':yvals_MS,
                                                                'xlabels':'m/z (Da)',
                                                                'xlimits':xlimits}
            except:
                msg = "Failed to extract mass spectrum for selected range"
                self.presenter.onThreading(None, (msg, 4) , action='updateStatusbar')

        # extract chromatogram
        if self.extract_extractRT_check.GetValue():
            if not self.extract_extractRT_ms_check.GetValue():
                mzStart, mzEnd = 0, 999999
                mz_title = "ion=all"
            if not self.extract_extractRT_dt_check.GetValue():
                dtStart, dtEnd = 1, 200
                dt_title = "dt=all"
            try:
                extract_kwargs = {'return_data':True}
                xvals_RT, yvals_RT = rawMassLynx_RT_extract(path=document.path,
                                                            mz_start=mzStart, mz_end=mzEnd,
                                                            dt_start=dtStart, dt_end=dtEnd,
                                                            driftscope_path=self.config.driftscopePath,
                                                            **extract_kwargs)
                self.presenter.view.panelPlots.on_plot_RT(xvals_RT, yvals_RT, 'Scans')
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
            except:
                msg = "Failed to extract chromatogram for selected range"
                self.presenter.onThreading(None, (msg, 4) , action='updateStatusbar')

        # extract drift time
        if self.extract_extractDT_check.GetValue():
            if not self.extract_extractDT_ms_check.GetValue():
                mzStart, mzEnd = 0, 999999
                mz_title = "ion=all"
            if not self.extract_extractDT_rt_check.GetValue():
                rtStart, rtEnd = 0.0, 999.0
                rt_title = "rt=all"
            try:
                extract_kwargs = {'return_data':True}
                xvals_DT, yvals_DT = rawMassLynx_DT_extract(path=document.path,
                                                            mz_start=mzStart, mz_end=mzEnd,
                                                            rt_start=rtStart, rt_end=rtEnd,
                                                            driftscope_path=self.config.driftscopePath,
                                                            **extract_kwargs)
                self.presenter.view.panelPlots.on_plot_1D(xvals_DT, yvals_DT, 'Drift time (bins)')
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
            except:
                msg = "Failed to extract mobiligram for selected range"
                self.presenter.onThreading(None, (msg, 4) , action='updateStatusbar')

        # extract drift time (2D)
        if self.extract_extract2D_check.GetValue():
            if not self.extract_extract2D_ms_check.GetValue():
                mzStart, mzEnd = 0, 999999
                mz_title = "ion=all"
            if not self.extract_extract2D_rt_check.GetValue():
                rtStart, rtEnd = 0.0, 999.0
                rt_title = "rt=all"
            try:
                extract_kwargs = {'return_data':True}
                zvals_2D = rawMassLynx_2DT_extract(path=document.path,
                                                   mz_start=mzStart, mz_end=mzEnd,
                                                   rt_start=rtStart, rt_end=rtEnd,
                                                   driftscope_path=self.config.driftscopePath,
                                                   **extract_kwargs)
                xvals_2D = 1 + np.arange(len(zvals_2D[1, :]))
                yvals_2D = 1 + np.arange(len(zvals_2D[:, 1]))
                yvals_1D = np.sum(zvals_2D, axis=1).T
                yvals_RT = np.sum(zvals_2D, axis=0)
                self.presenter.view.panelPlots.on_plot_2D_data(data=[zvals_2D, xvals_2D, 'Scans', yvals_2D, 'Drift time (bins)'])
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

        if not self.config.fit_show_labels_mz and not self.config.fit_show_labels_int:
            self.fit_show_labels_check.SetValue(False)
            self.config.fit_show_labels = False
            self.enableDisableBoxes(None)

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

    def onPickPeaksThreaded(self, evt):
        if not self.config.threading:
            self.data_processing.on_pick_peaks(None)
        else:
            self.onThreading(evt, {}, action='pick_peaks')

    def get_document_annotations(self):
        if (self.presenter.view.panelPlots.plot1.document_name is not None and
            self.presenter.view.panelPlots.plot1.dataset_name is not None):
            document_title = self.presenter.view.panelPlots.plot1.document_name
            dataset_title = self.presenter.view.panelPlots.plot1.dataset_name

            try: document = self.presenter.documentsDict[document_title]
            except: return None

            if dataset_title == "Mass Spectrum":
                annotations = document.massSpectrum.get('annotations', {})
            elif dataset_title == "Mass Spectrum (processed)":
                annotations = document.smoothMS.get('annotations', {})
            else:
                annotations = document.multipleMassSpectrum[dataset_title].get('annotations', {})

            return annotations
        else:
            return None

    def set_document_annotations(self, annotations, document_title=None, dataset_title=None):

        if document_title is None:
            document_title = self.presenter.view.panelPlots.plot1.document_name

        if dataset_title is None:
            dataset_title = self.presenter.view.panelPlots.plot1.dataset_name

        if (document_title is not None and dataset_title is not None):

            document = self.presenter.documentsDict[document_title]
            if dataset_title == "Mass Spectrum":
                document.massSpectrum['annotations'] = annotations
            elif dataset_title == "Mass Spectrum (processed)":
                document.smoothMS['annotations'] = annotations
            else:
                document.multipleMassSpectrum[dataset_title]['annotations'] = annotations

            self.presenter.OnUpdateDocument(document, 'document')

    def onThreading(self, evt, args, action="pick_peaks"):
        # Setup thread
        if action == 'pick_peaks':
            th = threading.Thread(target=self.data_processing.on_pick_peaks, args=(evt,))
        elif action == 'unidec':
            th = threading.Thread(target=self.onRunUnidec, args=(evt,))

        # Start thread
        try:
            th.start()
        except:
            print('Failed to execute the operation in threaded mode. Consider switching it off?')

    def _calculate_charge_positions(self, chargeList, selectedMW, msX,
                                    adductIon="H+", remove_below=0.01):

        _adducts = {'H+':1.007276467, 'Na+':22.989218, 'K+':38.963158, 'NH4+':18.033823,
                    'H-':-1.007276, 'Cl-':34.969402}

        min_mz, max_mz = np.min(msX), np.max(msX)  # np.min(self.config.unidec_engine.data.data2[:, 0]), np.max(self.config.unidec_engine.data.data2[:, 0])
        charges = np.array(list(map(int, np.arange(chargeList[0, 0], chargeList[-1, 0] + 1))))
        peakpos = (float(selectedMW) + (charges * _adducts[adductIon])) / charges

        ignore = (peakpos > min_mz) & (peakpos < max_mz)
        peakpos, charges, intensity = peakpos[ignore], charges[ignore], chargeList[:, 1][ignore]

        # remove peaks that are of poor intensity
        max_intensity = np.amax(intensity) * remove_below
        ignore = intensity > max_intensity
        peakpos, charges, intensity = peakpos[ignore], charges[ignore], intensity[ignore]

        return peakpos, charges, intensity

    def _calculate_peak_widths(self, chargeList, selectedMW, peakWidth, adductIon="H+"):
        _adducts = {'H+':1.007276467, 'Na+':22.989218, 'K+':38.963158, 'NH4+':18.033823,
                    'H-':-1.007276, 'Cl-':34.969402}
        min_mz, max_mz = np.min(self.config.unidec_engine.data.data2[:, 0]), np.max(self.config.unidec_engine.data.data2[:, 0])
        charges = np.array(list(map(int, np.arange(chargeList[0, 0], chargeList[-1, 0] + 1))))
        peakpos = (float(selectedMW) + charges * _adducts[adductIon]) / charges

        ignore = (peakpos > min_mz) & (peakpos < max_mz)
        peakpos, charges, intensities = peakpos[ignore], charges[ignore], chargeList[:, 1][ignore]

        # calculate min and max value based on the peak width
        mw_annotations = {}
        for peak, charge, intensity in zip(peakpos, charges, intensities):
            min_value = peak - peakWidth / 2.
            max_value = peak + peakWidth / 2.
            label_value = "MW: {}".format(selectedMW)
            annotation_dict = {"min":min_value,
                               "max":max_value,
                               "charge":charge,
                               "intensity":intensity,
                                "label":label_value,
                               'color':self.config.interactive_ms_annotations_color}

            name = "{} - {}".format(np.round(min_value, 2), np.round(max_value, 2))
            mw_annotations[name] = annotation_dict
        return mw_annotations

    def on_update_GUI(self, update_what="all"):
        # TODO: add all available fields
        """
        Update panel with new values if they were changed elsewhere in the program.
        You can selectively update ALL fields (i.e. if reloading configuration file) or
        single set of fields. 
        ---
        @param update_what (str): select what you would like to update
        """
        print(("??", self.config.ms_mzStart, self.config.ms_mzEnd, self.config))
        if update_what in ["all", "mass_spectra"]:
            self.bin_mzStart_value.SetValue(str(self.config.ms_mzStart))
            self.bin_mzEnd_value.SetValue(str(self.config.ms_mzEnd))

    def on_sort_unidec_MW(self, evt):
        if self._unidec_sort_column == 0:
            self._unidec_sort_column = 1
        else:
            self._unidec_sort_column = 0

        mass_list = self.unidec_weightList_choice.GetItems()

        _mass_list_sort = []
        for item in mass_list:
            item_split = re.split('MW: | \(| %\)', item)
            _mass_list_sort.append([item_split[1], item_split[2]])

        _mass_list_sort = natsorted(_mass_list_sort,
                                    key=itemgetter(self._unidec_sort_column),
                                    reverse=True)

        mass_list = []
        for item in _mass_list_sort:
            mass_list.append("MW: {} ({} %)".format(item[0], item[1]))

        self.unidec_weightList_choice.SetItems(mass_list)
        self.unidec_weightList_choice.SetStringSelection(mass_list[0])

    def onCustomiseUniDecParameters(self, evt):

        dlg = panelCustomiseParameters(self, self.config, self.icons)
        dlg.ShowModal()

