# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import logging
import re
import threading
from operator import itemgetter
from sys import platform

import numpy as np
import wx
from gui_elements.dialog_customise_unidec_visuals import DialogCustomiseUniDecVisuals
from gui_elements.misc_dialogs import DialogBox
from gui_elements.panel_htmlViewer import panelHTMLViewer
from gui_elements.panel_process_unidec_peak_width_tool import PanelPeakWidthTool
from help_documentation import OrigamiHelp
from ids import ID_processSettings_autoUniDec
from ids import ID_processSettings_isolateZUniDec
from ids import ID_processSettings_loadDataUniDec
from ids import ID_processSettings_pickPeaksUniDec
from ids import ID_processSettings_preprocessUniDec
from ids import ID_processSettings_replotAll
from ids import ID_processSettings_restoreIsolatedAll
from ids import ID_processSettings_runAll
from ids import ID_processSettings_runUniDec
from ids import ID_processSettings_showZUniDec
from ids import ID_processSettings_UniDec_info
from ids import ID_saveConfig
from natsort import natsorted
from styles import makeCheckbox
from styles import makeStaticBox
from styles import makeTooltip
from styles import validator
from utils.check import check_value_order
from utils.converters import str2int
from utils.converters import str2num
from utils.time import ttime
if platform == 'win32':
    from readers.io_waters_raw import (
        driftscope_extract_MS, driftscope_extract_RT, driftscope_extract_DT,
        driftscope_extract_2D,
    )
logger = logging.getLogger('origami')


class panelProcessData(wx.MiniFrame):
    """
    """

    def __init__(self, parent, presenter, config, icons, **kwargs):
        wx.MiniFrame.__init__(
            self, parent, -1, 'Processing...', size=(-1, -1),
            style=(
                wx.DEFAULT_FRAME_STYLE |
                wx.MAXIMIZE_BOX | wx.CLOSE_BOX
            ),
        )
        tstart = ttime()
        self.parent = parent
        self.presenter = presenter
        self.config = config
        self.icons = icons
        self.help = OrigamiHelp()
        self.data_processing = self.parent.data_processing
        self.data_handling = self.parent.data_handling

        self.importEvent = False
        self.currentPage = None
        self.windowSizes = {
            'Extract': (470, 390), 'ORIGAMI': (412, 337),
            'Mass spectrum': (412, 640), '2D': (412, 268),
            'Peak fitting': (412, 555), 'UniDec': (400, 785),
        }
        self.show_smoothed = True
        self._unidec_sort_column = 0  # 0 == MW / 1 == %

        # check if document/item information in kwarg
        if kwargs.get('processKwargs', None) != {}:
            self.onUpdateKwargs(
                data_type=kwargs['processKwargs']['update_mode'],
                **kwargs['processKwargs']
            )
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
        except Exception:
            self.currentDisplaySize = None

        # make gui items
        self.make_gui()

        self.main_sizer.Fit(self)
        self.Centre()
        self.Layout()
        self.Show(True)
        self.SetFocus()

        # fire-up start events
        self.onUpdateUniDecPanel()

    def onUpdateUniDecPanel(self):
        try:
            # set new dataset
            try:
                self.data_processing.unidec_dataset = self.dataset['MS']
            except KeyError:
                pass

            self.unidec_weightList_choice.Clear()
            kwargs = {'notify_of_error': False}
            massList, massMax = self.data_processing.get_unidec_data(data_type='mass_list', **kwargs)
            self.unidec_weightList_choice.SetItems(massList)
            self.unidec_weightList_choice.SetStringSelection(massMax)

        except Exception:
            pass

    def on_close(self, evt):
        """Destroy this frame."""
        self.Destroy()

    def make_gui(self):

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        # Setup notebook
        self.mainBook = wx.Notebook(
            self, wx.ID_ANY, wx.DefaultPosition,
            wx.DefaultSize, style=wx.NB_MULTILINE,
        )
        self.parameters_unidec = wx.Panel(
            self.mainBook, wx.ID_ANY, wx.DefaultPosition,
            wx.DefaultSize, wx.TAB_TRAVERSAL,
        )
        self.mainBook.AddPage(
            self.make_panel_UniDec(self.parameters_unidec),
            'UniDec', False,
        )

        self.main_sizer.Add(self.mainBook, 1, wx.EXPAND | wx.ALL, 2)

        # fire-up a couple of events
        self.on_toggle_controls(evt=None)

    def make_panel_UniDec(self, panel):
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        TEXTCTRL_SIZE = (60, -1)
        BTN_SIZE = (100, 22)

        # pre-process
        preprocess_staticBox = makeStaticBox(panel, '1. Pre-processing parameters', size=(-1, -1), color=wx.BLACK)
        preprocess_staticBox.SetSize((-1, -1))
        preprocess_box_sizer = wx.StaticBoxSizer(preprocess_staticBox, wx.HORIZONTAL)

        unidec_ms_min_label = wx.StaticText(panel, wx.ID_ANY, 'm/z start:')
        self.unidec_mzStart_value = wx.TextCtrl(
            panel, -1, '', size=TEXTCTRL_SIZE,
            validator=validator('floatPos'),
        )
        self.unidec_mzStart_value.SetValue(str(self.config.unidec_mzStart))
        self.unidec_mzStart_value.Bind(wx.EVT_TEXT, self.on_apply)
        self.unidec_mzStart_value.SetToolTip(makeTooltip(text=self.help.unidec_min_mz['help_msg']))

        unidec_ms_max_label = wx.StaticText(panel, wx.ID_ANY, 'end:')
        self.unidec_mzEnd_value = wx.TextCtrl(
            panel, -1, '', size=TEXTCTRL_SIZE,
            validator=validator('floatPos'),
        )
        self.unidec_mzEnd_value.SetValue(str(self.config.unidec_mzEnd))
        self.unidec_mzEnd_value.Bind(wx.EVT_TEXT, self.on_apply)
        self.unidec_mzEnd_value.SetToolTip(makeTooltip(text=self.help.unidec_max_mz['help_msg']))

        unidec_ms_binsize_label = wx.StaticText(panel, wx.ID_ANY, 'm/z bin size:')
        self.unidec_mzBinSize_value = wx.TextCtrl(
            panel, -1, '', size=TEXTCTRL_SIZE,
            validator=validator('floatPos'),
        )
        self.unidec_mzBinSize_value.SetValue(str(self.config.unidec_mzBinSize))
        self.unidec_mzBinSize_value.Bind(wx.EVT_TEXT, self.on_apply)
        self.unidec_mzBinSize_value.SetToolTip(makeTooltip(text=self.help.unidec_linearization['help_msg']))

        unidec_ms_gaussianFilter_label = wx.StaticText(panel, wx.ID_ANY, 'Gaussian filter:')
        self.unidec_gaussianFilter_value = wx.TextCtrl(
            panel, -1, '', size=TEXTCTRL_SIZE,
            validator=validator('floatPos'),
        )
        self.unidec_gaussianFilter_value.SetValue(str(self.config.unidec_gaussianFilter))
        self.unidec_gaussianFilter_value.Bind(wx.EVT_TEXT, self.on_apply)

        unidec_ms_accelerationV_label = wx.StaticText(panel, wx.ID_ANY, 'Acceleration voltage (kV):')
        self.unidec_accelerationV_value = wx.TextCtrl(
            panel, -1, '', size=TEXTCTRL_SIZE,
            validator=validator('floatPos'),
        )
        self.unidec_accelerationV_value.SetValue(str(self.config.unidec_accelerationV))
        self.unidec_accelerationV_value.Bind(wx.EVT_TEXT, self.on_apply)

        unidec_linearization_label = wx.StaticText(panel, wx.ID_ANY, 'Linearization mode:')
        self.unidec_linearization_choice = wx.Choice(
            panel, -1, choices=list(self.config.unidec_linearization_choices.keys()), size=(-1, -1),
        )
        self.unidec_linearization_choice.SetStringSelection(self.config.unidec_linearization)
        self.unidec_linearization_choice.Bind(wx.EVT_CHOICE, self.on_apply)

        self.unidec_load = wx.Button(
            panel, ID_processSettings_loadDataUniDec, 'Initilise UniDec',
            size=BTN_SIZE, name='load_data_unidec',
        )
        self.unidec_preprocess = wx.Button(
            panel, ID_processSettings_preprocessUniDec, 'Pre-process',
            size=BTN_SIZE, name='preprocess_unidec',
        )

        # pack elements
        preprocess_grid = wx.GridBagSizer(2, 2)
        n = 0
        preprocess_grid.Add(
            unidec_ms_min_label, (n, 0), wx.GBSpan(
                1, 1,
            ), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT,
        )
        preprocess_grid.Add(self.unidec_mzStart_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        preprocess_grid.Add(
            unidec_ms_max_label, (n, 2), wx.GBSpan(
                1, 1,
            ), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT,
        )
        preprocess_grid.Add(self.unidec_mzEnd_value, (n, 3), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        preprocess_grid.Add(
            unidec_ms_binsize_label, (n, 0), wx.GBSpan(1, 1),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT,
        )
        preprocess_grid.Add(self.unidec_mzBinSize_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        preprocess_grid.Add(
            unidec_ms_gaussianFilter_label, (n, 0), wx.GBSpan(1, 1),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT,
        )
        preprocess_grid.Add(self.unidec_gaussianFilter_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        preprocess_grid.Add(
            unidec_ms_accelerationV_label, (n, 0), wx.GBSpan(1, 1),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT,
        )
        preprocess_grid.Add(self.unidec_accelerationV_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        preprocess_grid.Add(
            unidec_linearization_label, (n, 0), wx.GBSpan(1, 1),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT,
        )
        preprocess_grid.Add(self.unidec_linearization_choice, (n, 1), wx.GBSpan(1, 4), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        preprocess_grid.Add(self.unidec_load, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        preprocess_grid.Add(self.unidec_preprocess, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        preprocess_box_sizer.Add(preprocess_grid, 0, wx.EXPAND, 10)

        # UniDec parameters
        unidec_staticBox = makeStaticBox(panel, '2. UniDec parameters', size=(-1, -1), color=wx.BLACK)
        unidec_staticBox.SetSize((-1, -1))
        unidec_box_sizer = wx.StaticBoxSizer(unidec_staticBox, wx.HORIZONTAL)

        unidec_charge_min_label = wx.StaticText(panel, wx.ID_ANY, 'Charge start:')
        self.unidec_zStart_value = wx.TextCtrl(
            panel, -1, '', size=TEXTCTRL_SIZE,
            validator=validator('floatPos'),
        )
        self.unidec_zStart_value.SetValue(str(self.config.unidec_zStart))
        self.unidec_zStart_value.Bind(wx.EVT_TEXT, self.on_apply)
        self.unidec_zStart_value.SetToolTip(makeTooltip(text=self.help.unidec_min_z['help_msg']))

        unidec_charge_max_label = wx.StaticText(panel, wx.ID_ANY, 'end:')
        self.unidec_zEnd_value = wx.TextCtrl(
            panel, -1, '', size=TEXTCTRL_SIZE,
            validator=validator('floatPos'),
        )
        self.unidec_zEnd_value.SetValue(str(self.config.unidec_zEnd))
        self.unidec_zEnd_value.Bind(wx.EVT_TEXT, self.on_apply)
        self.unidec_zEnd_value.SetToolTip(makeTooltip(text=self.help.unidec_max_z['help_msg']))

        unidec_mw_min_label = wx.StaticText(panel, wx.ID_ANY, 'MW start:')
        self.unidec_mwStart_value = wx.TextCtrl(
            panel, -1, '', size=TEXTCTRL_SIZE,
            validator=validator('floatPos'),
        )
        self.unidec_mwStart_value.SetValue(str(self.config.unidec_mwStart))
        self.unidec_mwStart_value.Bind(wx.EVT_TEXT, self.on_apply)
        self.unidec_mwStart_value.SetToolTip(makeTooltip(text=self.help.unidec_min_mw['help_msg']))

        unidec_mw_max_label = wx.StaticText(panel, wx.ID_ANY, 'end:')
        self.unidec_mwEnd_value = wx.TextCtrl(
            panel, -1, '', size=TEXTCTRL_SIZE,
            validator=validator('floatPos'),
        )
        self.unidec_mwEnd_value.SetValue(str(self.config.unidec_mwEnd))
        self.unidec_mwEnd_value.Bind(wx.EVT_TEXT, self.on_apply)
        self.unidec_mwEnd_value.SetToolTip(makeTooltip(text=self.help.unidec_max_mw['help_msg']))

        unidec_mw_sampleFrequency_label = wx.StaticText(panel, wx.ID_ANY, 'Sample frequency (Da):')
        self.unidec_mw_sampleFrequency_value = wx.TextCtrl(
            panel, -1, '', size=TEXTCTRL_SIZE,
            validator=validator('floatPos'),
        )
        self.unidec_mw_sampleFrequency_value.SetValue(str(self.config.unidec_mwFrequency))
        self.unidec_mw_sampleFrequency_value.Bind(wx.EVT_TEXT, self.on_apply)
        self.unidec_mw_sampleFrequency_value.SetToolTip(makeTooltip(text=self.help.unidec_mw_resolution['help_msg']))

        unidec_peakWidth_label = wx.StaticText(panel, wx.ID_ANY, 'Peak FWHM (Da):')
        self.unidec_fit_peakWidth_value = wx.TextCtrl(
            panel, -1, '', size=TEXTCTRL_SIZE,
            validator=validator('floatPos'),
        )
        self.unidec_fit_peakWidth_value.SetValue(str(self.config.unidec_peakWidth))
        self.unidec_fit_peakWidth_value.Bind(wx.EVT_TEXT, self.on_apply)
        self.unidec_fit_peakWidth_value.SetToolTip(makeTooltip(text=self.help.unidec_peak_FWHM['help_msg']))

        self.unidec_fit_peakWidth_check = makeCheckbox(panel, 'Auto')
        self.unidec_fit_peakWidth_check.SetValue(self.config.unidec_peakWidth_auto)
        self.unidec_fit_peakWidth_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.unidec_fit_peakWidth_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        unidec_peakShape_label = wx.StaticText(panel, wx.ID_ANY, 'Peak Shape:')
        self.unidec_peakFcn_choice = wx.Choice(
            panel, -1, choices=list(self.config.unidec_peakFunction_choices.keys()),
            size=(-1, -1),
        )
        self.unidec_peakFcn_choice.SetStringSelection(self.config.unidec_peakFunction)
        self.unidec_peakFcn_choice.Bind(wx.EVT_CHOICE, self.on_apply)

        self.unidec_peakTool = wx.Button(panel, -1, 'Peak width tool', size=BTN_SIZE)
        self.unidec_runUnidec = wx.Button(
            panel, ID_processSettings_runUniDec, 'Run UniDec',
            size=BTN_SIZE, name='run_unidec',
        )

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
        ms_grid.Add(
            unidec_mw_sampleFrequency_label, (n, 0), wx.GBSpan(
                1, 1,
            ), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT,
        )
        ms_grid.Add(
            self.unidec_mw_sampleFrequency_value, (n, 1),
            wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND,
        )
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
        peakDetect_staticBox = makeStaticBox(panel, '3. Peak detection parameters', size=(-1, -1), color=wx.BLACK)
        peakDetect_staticBox.SetSize((-1, -1))
        peakDetect_box_sizer = wx.StaticBoxSizer(peakDetect_staticBox, wx.HORIZONTAL)

        unidec_peak_width_label = wx.StaticText(panel, wx.ID_ANY, 'Peak detection window (Da):')
        self.unidec_peakWidth_value = wx.TextCtrl(
            panel, -1, '', size=TEXTCTRL_SIZE,
            validator=validator('floatPos'),
        )
        self.unidec_peakWidth_value.SetValue(str(self.config.unidec_peakDetectionWidth))
        self.unidec_peakWidth_value.Bind(wx.EVT_TEXT, self.on_apply)

        unidec_peak_threshold_label = wx.StaticText(panel, wx.ID_ANY, 'Peak detection threshold:')
        self.unidec_peakThreshold_value = wx.TextCtrl(
            panel, -1, '', size=TEXTCTRL_SIZE,
            validator=validator('floatPos'),
        )
        self.unidec_peakThreshold_value.SetValue(str(self.config.unidec_peakDetectionThreshold))
        self.unidec_peakThreshold_value.Bind(wx.EVT_TEXT, self.on_apply)

        unidec_peak_normalization_label = wx.StaticText(panel, wx.ID_ANY, 'Peak normalization:')
        self.unidec_peakNormalization_choice = wx.Choice(
            panel, -1, choices=list(self.config.unidec_peakNormalization_choices.keys()), size=(-1, -1),
        )
        self.unidec_peakNormalization_choice.SetStringSelection(self.config.unidec_peakNormalization)
        self.unidec_peakNormalization_choice.Bind(wx.EVT_CHOICE, self.on_apply)

        individualComponents_label = wx.StaticText(panel, wx.ID_ANY, 'Show individual components:')
        self.unidec_individualComponents_check = makeCheckbox(panel, '')
        self.unidec_individualComponents_check.SetValue(self.config.unidec_show_individualComponents)
        self.unidec_individualComponents_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        markers_label = wx.StaticText(panel, wx.ID_ANY, 'Show markers:')
        self.unidec_markers_check = makeCheckbox(panel, '')
        self.unidec_markers_check.SetValue(self.config.unidec_show_markers)
        self.unidec_markers_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        unidec_peak_separation_label = wx.StaticText(panel, wx.ID_ANY, 'Line separation:')
        self.unidec_lineSeparation_value = wx.TextCtrl(
            panel, -1, '', size=TEXTCTRL_SIZE,
            validator=validator('floatPos'),
        )
        self.unidec_lineSeparation_value.SetValue(str(self.config.unidec_lineSeparation))
        self.unidec_lineSeparation_value.Bind(wx.EVT_TEXT, self.on_apply)

        self.unidec_detectPeaks = wx.Button(
            panel, ID_processSettings_pickPeaksUniDec, 'Detect peaks',
            size=BTN_SIZE, name='pick_peaks_unidec',
        )

        # pack elements
        peak_grid = wx.GridBagSizer(2, 2)
        n = 0
        peak_grid.Add(unidec_peak_width_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        peak_grid.Add(self.unidec_peakWidth_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        peak_grid.Add(
            unidec_peak_threshold_label, (n, 0), wx.GBSpan(
                1, 1,
            ), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT,
        )
        peak_grid.Add(self.unidec_peakThreshold_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        peak_grid.Add(
            unidec_peak_normalization_label, (n, 0), wx.GBSpan(
                1, 1,
            ), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT,
        )
        peak_grid.Add(self.unidec_peakNormalization_choice, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        peak_grid.Add(
            unidec_peak_separation_label, (n, 0), wx.GBSpan(
                1, 1,
            ), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT,
        )
        peak_grid.Add(self.unidec_lineSeparation_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        peak_grid.Add(
            individualComponents_label, (n, 0), wx.GBSpan(
                1, 1,
            ), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT,
        )
        peak_grid.Add(self.unidec_individualComponents_check, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        peak_grid.Add(markers_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        peak_grid.Add(self.unidec_markers_check, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        peak_grid.Add(self.unidec_detectPeaks, (n, 2), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER_VERTICAL)
        peakDetect_box_sizer.Add(peak_grid, 0, wx.EXPAND, 10)

        # Buttons
        self.unidec_autorun = wx.Button(
            panel, ID_processSettings_autoUniDec, 'Autorun UniDec',
            size=(-1, 22), name='auto_unidec',
        )
        self.unidec_runAll = wx.Button(panel, ID_processSettings_runAll, 'Run all', size=(-1, 22))
        self.unidec_cancelBtn = wx.Button(panel, wx.ID_OK, 'Cancel', size=(-1, 22))

        self.unidec_info = wx.BitmapButton(
            panel, ID_processSettings_UniDec_info,
            self.icons.iconsLib['process_unidec_16'],
            size=(-1, -1),
            style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL,
        )
        self.unidec_info.SetBackgroundColour((240, 240, 240))
        self.unidec_info.SetToolTip(makeTooltip(text=self.help.unidec_about['help_msg']))

        plot_staticBox = makeStaticBox(panel, '4. Plotting', size=(-1, -1), color=wx.BLACK)
        plot_staticBox.SetSize((-1, -1))
        plot_box_sizer = wx.StaticBoxSizer(plot_staticBox, wx.HORIZONTAL)

        unidec_plotting_weights_label = wx.StaticText(panel, wx.ID_ANY, 'Molecular weights:')
        self.unidec_weightList_choice = wx.ComboBox(
            panel, ID_processSettings_showZUniDec,
            choices=[],
            size=(150, -1), style=wx.CB_READONLY,
            name='ChargeStates',
        )
        self.unidec_weightList_choice.Bind(wx.EVT_COMBOBOX, self.on_run_unidec_fcn)

        self.unidec_weightList_sort = wx.BitmapButton(
            panel, wx.ID_ANY,
            self.icons.iconsLib['reload16'],
            size=(-1, -1), name='unidec_sort',
            style=wx.ALIGN_CENTER_VERTICAL,
        )
        self.unidec_weightList_sort.SetBackgroundColour((240, 240, 240))
        self.unidec_weightList_sort.Bind(wx.EVT_BUTTON, self.on_sort_unidec_MW)
        self.unidec_weightList_sort.SetToolTip(makeTooltip(text=self.help.unidec_sort_mw_list['help_msg']))

        unidec_plotting_adduct_label = wx.StaticText(panel, wx.ID_ANY, 'Adduct:')
        self.unidec_adductMW_choice = wx.Choice(
            panel, ID_processSettings_showZUniDec,
            choices=['H+', 'Na+', 'K+', 'NH4+', 'H-', 'Cl-'],
            size=(-1, -1), name='ChargeStates',
        )
        self.unidec_adductMW_choice.SetStringSelection('H+')
        self.unidec_adductMW_choice.Bind(wx.EVT_CHOICE, self.on_run_unidec_fcn)

        unidec_charges_threshold_label = wx.StaticText(panel, wx.ID_ANY, 'Intensity threshold:')
        self.unidec_charges_threshold_value = wx.SpinCtrlDouble(
            panel, -1,
            value=str(self.config.unidec_charges_label_charges),
            min=0, max=1,
            initial=self.config.unidec_charges_label_charges,
            inc=0.01, size=(90, -1),
        )
        self.unidec_charges_threshold_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        unidec_charges_offset_label = wx.StaticText(panel, wx.ID_ANY, 'Vertical charge offset:')
        self.unidec_charges_offset_value = wx.SpinCtrlDouble(
            panel, -1,
            value=str(self.config.unidec_charges_offset),
            min=0, max=1,
            initial=self.config.unidec_charges_offset,
            inc=0.05, size=(90, -1),
        )
        self.unidec_charges_offset_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        self.unidec_restoreAll_Btn = wx.Button(
            panel, ID_processSettings_restoreIsolatedAll, 'Restore all', size=(-1, 22),
        )
        self.unidec_restoreAll_Btn.Bind(wx.EVT_BUTTON, self.on_run_unidec_fcn)

        self.unidec_chargeStates_Btn = wx.Button(panel, ID_processSettings_showZUniDec, 'Label', size=(-1, 22))
        self.unidec_chargeStates_Btn.Bind(wx.EVT_BUTTON, self.on_run_unidec_fcn)

        self.unidec_isolateCharges_Btn = wx.Button(panel, ID_processSettings_isolateZUniDec, 'Isolate', size=(-1, 22))
        self.unidec_isolateCharges_Btn.Bind(wx.EVT_BUTTON, self.on_run_unidec_fcn)

        # pack elements
        plotting_grid = wx.GridBagSizer(2, 2)
        n = 0
        plotting_grid.Add(
            unidec_plotting_weights_label, (n, 0), wx.GBSpan(1, 1),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT,
        )
        plotting_grid.Add(
            self.unidec_weightList_choice, (n, 1), wx.GBSpan(1, 2),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND,
        )
        plotting_grid.Add(
            self.unidec_weightList_sort, (n, 3), wx.GBSpan(1, 1),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND,
        )
        n = n + 1
        plotting_grid.Add(
            unidec_plotting_adduct_label, (n, 0), wx.GBSpan(1, 1),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT,
        )
        plotting_grid.Add(
            self.unidec_adductMW_choice, (n, 1), wx.GBSpan(1, 1),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND,
        )
        plotting_grid.Add(
            self.unidec_restoreAll_Btn, (n, 2), wx.GBSpan(1, 1),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND,
        )
        n = n + 1
        plotting_grid.Add(
            unidec_charges_threshold_label, (n, 0), wx.GBSpan(1, 1),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT,
        )
        plotting_grid.Add(
            self.unidec_charges_threshold_value, (n, 1), wx.GBSpan(1, 1),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT,
        )
        plotting_grid.Add(
            self.unidec_chargeStates_Btn, (n, 2), wx.GBSpan(1, 1),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND,
        )
        n = n + 1
        plotting_grid.Add(
            unidec_charges_offset_label, (n, 0), wx.GBSpan(1, 1),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT,
        )
        plotting_grid.Add(
            self.unidec_charges_offset_value, (n, 1), wx.GBSpan(1, 1),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT,
        )
        plotting_grid.Add(
            self.unidec_isolateCharges_Btn, (n, 2), wx.GBSpan(1, 1),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT,
        )
        plot_box_sizer.Add(plotting_grid, 0, wx.EXPAND, 10)

        other_staticBox = makeStaticBox(panel, 'Other settings', size=(-1, -1), color=wx.BLACK)
        other_staticBox.SetSize((-1, -1))
        other_box_sizer = wx.StaticBoxSizer(other_staticBox, wx.HORIZONTAL)

        unidec_max_iters_label = wx.StaticText(panel, wx.ID_ANY, 'Max iterations:')
        self.unidec_maxIters_value = wx.TextCtrl(
            panel, -1, '', size=TEXTCTRL_SIZE,
            validator=validator('intPos'),
        )
        self.unidec_maxIters_value.SetValue(str(self.config.unidec_maxIterations))
        self.unidec_maxIters_value.Bind(wx.EVT_TEXT, self.on_apply)

        unidec_max_shown_label = wx.StaticText(panel, wx.ID_ANY, 'Max shown:')
        self.unidec_maxShownLines_value = wx.TextCtrl(
            panel, -1, '', size=TEXTCTRL_SIZE,
            validator=validator('intPos'),
        )
        self.unidec_maxShownLines_value.SetValue(str(self.config.unidec_maxShown_individualLines))
        self.unidec_maxShownLines_value.Bind(wx.EVT_TEXT, self.on_apply)

        self.unidec_customise_Btn = wx.Button(panel, wx.ID_ANY, 'Customise plots...', size=(-1, 22))
        self.unidec_customise_Btn.Bind(wx.EVT_BUTTON, self.on_run_unidec_fcn)

        other_grid = wx.GridBagSizer(2, 2)
        n = 0
        other_grid.Add(unidec_max_iters_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        other_grid.Add(self.unidec_maxIters_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        other_grid.Add(unidec_max_shown_label, (n, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        other_grid.Add(
            self.unidec_maxShownLines_value, (n, 3), wx.GBSpan(
                1, 1,
            ), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND,
        )
        n = n + 1
        other_grid.Add(
            self.unidec_customise_Btn, (n, 0), wx.GBSpan(1, 4),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL,
        )
        other_box_sizer.Add(other_grid, 0, wx.EXPAND, 10)

        self.unidec_replot_Btn = wx.Button(panel, ID_processSettings_replotAll, 'Replot', size=(-1, 22))
        self.unidec_replot_Btn.Bind(wx.EVT_BUTTON, self.on_run_unidec_fcn)

        horizontal_line_1 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        button_grid = wx.GridBagSizer(2, 2)
        n = 0
        button_grid.Add(
            self.unidec_autorun, (n, 0), wx.GBSpan(1, 1),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL,
        )
        button_grid.Add(
            self.unidec_runAll, (n, 1), wx.GBSpan(1, 1),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL,
        )
        button_grid.Add(
            self.unidec_cancelBtn, (n, 2), wx.GBSpan(1, 1),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL,
        )
        button_grid.Add(
            self.unidec_replot_Btn, (n, 3), wx.GBSpan(1, 1),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL,
        )
        button_grid.Add(
            self.unidec_info, (n, 4), wx.GBSpan(1, 1),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL,
        )

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
        main_sizer.Add(grid, 0, wx.ALIGN_CENTER_HORIZONTAL, 10)

        # bind events
        self.unidec_load.Bind(wx.EVT_BUTTON, self.on_run_unidec_fcn)
        self.unidec_preprocess.Bind(wx.EVT_BUTTON, self.on_run_unidec_fcn)
        self.unidec_runUnidec.Bind(wx.EVT_BUTTON, self.on_run_unidec_fcn)
        self.unidec_runAll.Bind(wx.EVT_BUTTON, self.on_run_unidec_fcn)
        self.unidec_detectPeaks.Bind(wx.EVT_BUTTON, self.on_run_unidec_fcn)
        self.unidec_autorun.Bind(wx.EVT_BUTTON, self.on_run_unidec_fcn)
        self.unidec_cancelBtn.Bind(wx.EVT_BUTTON, self.on_close)
        self.unidec_info.Bind(wx.EVT_BUTTON, self.openHTMLViewer)
        self.unidec_peakTool.Bind(wx.EVT_BUTTON, self.openWidthTool)
        self.unidec_customise_Btn.Bind(wx.EVT_BUTTON, self.on_open_unidec_customisation_settings)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def on_run_unidec_fcn(self, evt):
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

        if 'MS' in self.dataset:
            dataset = self.dataset['MS']
        else:
            dataset = 'Mass Spectrum'

        task, plots = 'auto_unidec', 'all'
        if evtID == ID_processSettings_loadDataUniDec:
            task = 'load_data_unidec'
            plots = []
        elif evtID == ID_processSettings_preprocessUniDec:
            task = 'preprocess_unidec'
            plots = ['Processed']
        elif evtID == ID_processSettings_autoUniDec:
            task = 'auto_unidec'
            plots = ['all']
        elif evtID == ID_processSettings_runUniDec:
            task = 'run_unidec'
            plots = ['Fitted', 'm/z vs Charge', 'MW vs Charge', 'MW distribution']
        elif evtID == ID_processSettings_runAll:
            task = 'run_all_unidec'
            plots = [
                'Fitted', 'm/z vs Charge', 'MW vs Charge', 'MW distribution',
                'm/z with isolated species', 'Barchart',
            ]
        elif evtID == ID_processSettings_pickPeaksUniDec:
            task = 'pick_peaks_unidec'
            plots = ['m/z with isolated species', 'Barchart']
        elif evtID == ID_processSettings_isolateZUniDec:
            task = None
            plots = ['Isolate MW']
        elif evtID == ID_processSettings_restoreIsolatedAll:
            task = None
            plots = ['m/z with isolated species']
        elif evtID == ID_processSettings_replotAll:
            task = None
            plots = [
                'Fitted', 'm/z vs Charge', 'MW vs Charge', 'MW distribution',
                'm/z with isolated species', 'Barchart',
            ]
        elif evtID == ID_processSettings_showZUniDec:
            task = None
            plots = ['Charge information']
        else:
            return

        if task in ['all', 'load_data_unidec', 'run_all_unidec', 'preprocess_unidec']:
            self.presenter.view.panelPlots.on_clear_unidec()

        if task is not None:
            self.data_processing.on_run_unidec(dataset, task)

        # modify GUI when necessary
        if task in ['auto_unidec', 'run_unidec', 'run_all_unidec']:
            self.unidec_fit_peakWidth_value.SetValue(str(self.config.unidec_peakWidth))

        if task in ['pick_peaks_unidec', 'run_all_unidec', 'auto_unidec']:
            massList, massMax = self.data_processing.get_unidec_data(data_type='mass_list')
            self.unidec_weightList_choice.SetItems(massList)
            self.unidec_weightList_choice.SetStringSelection(massMax)

        # plot
        self.onPlotUnidec(evtID, plots)

    def onPlotUnidec(self, evtID, plots):

        self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['UniDec'])
        if not isinstance(evtID, int):
            source = evtID.GetEventObject().GetName()
            evtID = evtID.GetId()
            if source == 'ChargeStates':
                evtID = ID_processSettings_showZUniDec

        kwargs = {
            'show_markers': self.config.unidec_show_markers,
            'show_individual_lines': self.config.unidec_show_individualComponents,
            'speedy': self.config.unidec_speedy,
            'optimise_positions': self.config.unidec_optimiseLabelPositions,
        }

        data = self.data_processing.get_unidec_data(data_type='unidec_data')

        for plot in plots:
            if plot in ['all', 'Fitted', 'Processed']:

                try:
                    self.presenter.view.panelPlots.on_plot_unidec_MS_v_Fit(
                        unidec_eng_data=None,
                        replot=data['Fitted'],
                        **kwargs
                    )
                except Exception:
                    try:
                        self.presenter.view.panelPlots.on_plot_unidec_MS(
                            unidec_eng_data=None,
                            replot=data['Processed'],
                            **kwargs
                        )
                    except Exception:
                        pass

            if plot in ['all', 'MW distribution']:
                try:
                    self.presenter.view.panelPlots.on_plot_unidec_mwDistribution(
                        unidec_eng_data=None,
                        replot=data['MW distribution'],
                        **kwargs
                    )
                except Exception:
                    pass

            if plot in ['all', 'm/z vs Charge']:
                try:
                    self.presenter.view.panelPlots.on_plot_unidec_mzGrid(
                        unidec_eng_data=None,
                        replot=data['m/z vs Charge'],
                        **kwargs
                    )
                except Exception:
                    pass

            if plot in ['all', 'm/z with isolated species']:
                try:
                    self.presenter.view.panelPlots.on_plot_unidec_individualPeaks(
                        unidec_eng_data=None, replot=data['m/z with isolated species'], **kwargs
                    )
                    try:
                        self.presenter.view.panelPlots.on_plot_unidec_MW_add_markers(
                            data['m/z with isolated species'],
                            data['MW distribution'],
                            **kwargs
                        )
                    except Exception:
                        pass
                except Exception:
                    pass

            if plot in ['all', 'MW vs Charge']:
                try:
                    self.presenter.view.panelPlots.on_plot_unidec_MW_v_Charge(
                        unidec_eng_data=None,
                        replot=data['MW vs Charge'],
                        **kwargs
                    )
                except Exception:
                    pass

            if plot in ['all', 'Barchart']:
                try:
                    self.presenter.view.panelPlots.on_plot_unidec_barChart(
                        unidec_eng_data=None,
                        replot=data['Barchart'],
                        **kwargs
                    )
                except Exception:
                    pass

            if plot in ['Isolate MW']:
                try:
                    mw_selection = 'MW: {}'.format(self.unidec_weightList_choice.GetStringSelection().split()[1])
                except Exception:
                    return
                kwargs['show_isolated_mw'] = True
                kwargs['mw_selection'] = mw_selection

                self.presenter.view.panelPlots.on_plot_unidec_individualPeaks(
                    unidec_eng_data=None,
                    replot=data['m/z with isolated species'],
                    **kwargs
                )
            if plot in ['all', 'Charge information']:
                charges = data['Charge information']
                self.presenter.view.panelPlots.on_plot_unidec_ChargeDistribution(
                    charges[:, 0], charges[:, 1],
                    **kwargs
                )

                selection = self.unidec_weightList_choice.GetStringSelection().split()[1]
                adductIon = self.unidec_adductMW_choice.GetStringSelection()

                peakpos, charges, __ = self._calculate_charge_positions(
                    charges, selection, data['Processed']['xvals'], adductIon,
                    remove_below=self.config.unidec_charges_label_charges,
                )
                self.presenter.view.panelPlots.on_plot_charge_states(peakpos, charges, **kwargs)

    def on_apply(self, evt):
        # prevent updating config

        if self.importEvent:
            return
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

        if self.config.autoSaveSettings:
            try:
                self.presenter.onExportConfig(evt=ID_saveConfig, verbose=False)
            except TypeError:
                pass

    def on_toggle_controls(self, evt):

        # unidec
        self.config.unidec_peakWidth_auto = self.unidec_fit_peakWidth_check.GetValue()
        if self.config.unidec_peakWidth_auto:
            self.unidec_fit_peakWidth_value.Disable()
            self.unidec_peakTool.Disable()
        else:
            self.unidec_fit_peakWidth_value.Enable()
            self.unidec_peakTool.Enable()

        if evt is not None:
            evt.Skip()

    def onSetupValues(self, evt=None):

        self.importEvent = True

        # panel 2D
        self.plot2D_sigma_value.SetValue(str(self.config.plot2D_smooth_sigma))
        self.plot2D_window_value.SetValue(str(self.config.plot2D_smooth_window))
        self.plot2D_polynomial_value.SetValue(str(self.config.plot2D_smooth_polynomial))
        self.plot2D_threshold_value.SetValue(str(self.config.plot2D_threshold))

        self.importEvent = False
        if evt is not None:
            evt.Skip()

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
            title = 'About UniDec...'

            kwargs = {'window_size': (550, 300)}

        htmlViewer = panelHTMLViewer(self, self.config, msg, title, **kwargs)
        htmlViewer.Show()

    def openWidthTool(self, evt):
        try:
            kwargs = {
                'xvals': self.config.unidec_engine.data.data2[:, 0],
                'yvals': self.config.unidec_engine.data.data2[:, 1],
            }
        except Exception:
            DialogBox(
                exceptionTitle='Error',
                exceptionMsg='Please initilise and process data first!',
                type='Error',
            )
            return

        self.widthTool = PanelPeakWidthTool(self, self.presenter, self.config, **kwargs)
        self.widthTool.Show()

    def get_document_annotations(self):
        if (
            self.presenter.view.panelPlots.plot1.document_name is not None and
            self.presenter.view.panelPlots.plot1.dataset_name is not None
        ):
            document_title = self.presenter.view.panelPlots.plot1.document_name
            dataset_title = self.presenter.view.panelPlots.plot1.dataset_name

            try:
                document = self.presenter.documentsDict[document_title]
            except Exception:
                return None

            if dataset_title == 'Mass Spectrum':
                annotations = document.massSpectrum.get('annotations', {})
            elif dataset_title == 'Mass Spectrum (processed)':
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
            if dataset_title == 'Mass Spectrum':
                document.massSpectrum['annotations'] = annotations
            elif dataset_title == 'Mass Spectrum (processed)':
                document.smoothMS['annotations'] = annotations
            else:
                document.multipleMassSpectrum[dataset_title]['annotations'] = annotations

            self.data_handling.on_update_document(document, 'document')

    def _calculate_charge_positions(
        self, chargeList, selectedMW, msX,
        adductIon='H+', remove_below=0.01,
    ):

        _adducts = {
            'H+': 1.007276467, 'Na+': 22.989218, 'K+': 38.963158, 'NH4+': 18.033823,
            'H-': -1.007276, 'Cl-': 34.969402,
        }

        # np.min(self.config.unidec_engine.data.data2[:, 0]), np.max(self.config.unidec_engine.data.data2[:, 0])
        min_mz, max_mz = np.min(msX), np.max(msX)
        charges = np.array(list(map(int, np.arange(chargeList[0, 0], chargeList[-1, 0] + 1))))
        peakpos = (float(selectedMW) + (charges * _adducts[adductIon])) / charges

        ignore = (peakpos > min_mz) & (peakpos < max_mz)
        peakpos, charges, intensity = peakpos[ignore], charges[ignore], chargeList[:, 1][ignore]

        # remove peaks that are of poor intensity
        max_intensity = np.amax(intensity) * remove_below
        ignore = intensity > max_intensity
        peakpos, charges, intensity = peakpos[ignore], charges[ignore], intensity[ignore]

        return peakpos, charges, intensity

    def _calculate_peak_widths(self, chargeList, selectedMW, peakWidth, adductIon='H+'):
        _adducts = {
            'H+': 1.007276467, 'Na+': 22.989218, 'K+': 38.963158, 'NH4+': 18.033823,
            'H-': -1.007276, 'Cl-': 34.969402,
        }
        min_mz, max_mz = np.min(self.config.unidec_engine.data.data2[:, 0]), np.max(
            self.config.unidec_engine.data.data2[:, 0],
        )
        charges = np.array(list(map(int, np.arange(chargeList[0, 0], chargeList[-1, 0] + 1))))
        peakpos = (float(selectedMW) + charges * _adducts[adductIon]) / charges

        ignore = (peakpos > min_mz) & (peakpos < max_mz)
        peakpos, charges, intensities = peakpos[ignore], charges[ignore], chargeList[:, 1][ignore]

        # calculate min and max value based on the peak width
        mw_annotations = {}
        for peak, charge, intensity in zip(peakpos, charges, intensities):
            min_value = peak - peakWidth / 2.
            max_value = peak + peakWidth / 2.
            label_value = 'MW: {}'.format(selectedMW)
            annotation_dict = {
                'min': min_value,
                'max': max_value,
                'charge': charge,
                'intensity': intensity,
                'label': label_value,
                'color': self.config.interactive_ms_annotations_color,
            }

            name = '{} - {}'.format(np.round(min_value, 2), np.round(max_value, 2))
            mw_annotations[name] = annotation_dict
        return mw_annotations

    def on_sort_unidec_MW(self, evt):
        if self._unidec_sort_column == 0:
            self._unidec_sort_column = 1
        else:
            self._unidec_sort_column = 0

        mass_list = self.unidec_weightList_choice.GetItems()

        _mass_list_sort = []
        for item in mass_list:
            item_split = re.split(r'MW: | \(| %\)', item)
            _mass_list_sort.append([item_split[1], item_split[2]])

        _mass_list_sort = natsorted(
            _mass_list_sort,
            key=itemgetter(self._unidec_sort_column),
            reverse=True,
        )

        mass_list = []
        for item in _mass_list_sort:
            mass_list.append('MW: {} ({} %)'.format(item[0], item[1]))

        self.unidec_weightList_choice.SetItems(mass_list)
        self.unidec_weightList_choice.SetStringSelection(mass_list[0])

    def on_open_unidec_customisation_settings(self, evt):

        dlg = DialogCustomiseUniDecVisuals(self, self.config, self.icons)
        dlg.ShowModal()
