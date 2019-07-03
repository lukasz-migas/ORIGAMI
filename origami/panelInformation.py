# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import re

import numpy as np
import wx
from ids import ID_documentInfoCalibration
from ids import ID_documentInfoNotes
from ids import ID_documentInfoPlotIMS
from ids import ID_documentInfoSpectrum
from ids import ID_documentInfoSummary
from ids import ID_saveAsConfig
from ids import ID_selectProtein
from styles import bgrPanel
from styles import layout
from styles import makeCheckbox
from utils.converters import num2str
from utils.converters import str2int
from utils.converters import str2num


class panelDocumentInfo(wx.MiniFrame):
    """Document info tools."""

    def __init__(self, parent, presenter, config, icons, document, **kwargs):
        wx.MiniFrame.__init__(
            self, parent, -1, 'Document Information',
            size=(400, 200), style=wx.DEFAULT_FRAME_STYLE,
        )

        self.parent = parent
        self.presenter = presenter
        self.config = config
        self.icons = icons
        self.document = document

        # Check if there are any kwargs
        self.currentTool = kwargs.get('currentTool', 'summary')
        self.itemType = kwargs.get('itemType', None)
        self.extractData = kwargs.get('extractData', None)

        # Make some variables
        self.plot2Dtitle = 'None'

        # make gui items
        self.make_gui()
        wx.EVT_CLOSE(self, self.on_close)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_event)

        # select default tool
        self.onToolSelected(tool=self.currentTool, evt=None)

        self.CentreOnScreen()
        self.SetFocus()

    def on_key_event(self, evt):
        key_code = evt.GetKeyCode()

        if key_code == wx.WXK_ESCAPE:  # key = esc
            self.on_close(evt=None)

        evt.Skip()

    def on_close(self, evt):
        """Destroy this frame."""
        self.Destroy()
    # ----

    def make_gui(self):
        """Make panel gui."""

        # make toolbar
        toolbar = self.make_toolbar()

        # make panels
        buttons = self.makeBtnPanel()
        summary = self.makeSummaryPanel()
        spectrum = self.makeSpectrumPanel()
        if self.document.got2DIMS:
            plot2D = self.makeIMS2DPanel()
        elif self.document.gotExtractedIons:
            plot2D = self.makeIMS2DPanel()
        elif self.document.gotCombinedExtractedIons:
            plot2D = self.makeIMS2DPanel()
        elif self.document.gotComparisonData:
            plot2D = self.makeIMS2DPanel()
        else:
            plot2D = self.makeEmptyPanel()
        calibration = self.makeCCSCalibrationPanel()
        notes = self.makeNotesPanel()

        # pack elements
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(toolbar, 0, wx.EXPAND, 0)
        self.mainSizer.Add(summary, 1, wx.EXPAND, 0)
        self.mainSizer.Add(spectrum, 1, wx.EXPAND, 0)
        self.mainSizer.Add(plot2D, 1, wx.EXPAND, 0)
        self.mainSizer.Add(calibration, 1, wx.EXPAND, 0)
        self.mainSizer.Add(notes, 1, wx.EXPAND, 0)
        self.mainSizer.Add(buttons, 0, wx.EXPAND, 0)

        # enable/disable
        self.onEnableDisable(evt=None)

        # fit layout
        self.mainSizer.Fit(self)
        self.SetSizer(self.mainSizer)

    def make_toolbar(self):
        """Make toolbar."""

        toolbar_toolsize = (16, 16)
#         toolbar_height = 38
        button_size_correction = 0
        toolbar_rspace = 15
#         toolbar_lspace = 0
        spacer = 5
        spacer_l = 20

        # init toolbar
        panel = bgrPanel(
            self, -1, self.icons.iconsLib['bgrToolbar'],
            size=(16, 20),
        )

        # make buttons
        self.summary_butt = wx.BitmapButton(
            panel, ID_documentInfoSummary, self.icons.iconsLib['documentTwo16'],
            size=(toolbar_toolsize), style=wx.BORDER_NONE,
        )
        self.summary_butt.SetToolTip(wx.ToolTip('Document summary'))
        self.summary_butt.Bind(wx.EVT_BUTTON, self.onToolSelected)

        self.spectrum_butt = wx.BitmapButton(
            panel, ID_documentInfoSpectrum, self.icons.iconsLib['ms16'],
            size=(toolbar_toolsize), style=wx.BORDER_NONE,
        )
        self.spectrum_butt.SetToolTip(wx.ToolTip('Spectrum information'))
        self.spectrum_butt.Bind(wx.EVT_BUTTON, self.onToolSelected)

        self.plotIMS_butt = wx.BitmapButton(
            panel, ID_documentInfoPlotIMS, self.icons.iconsLib['plotIMS16'],
            size=(toolbar_toolsize), style=wx.BORDER_NONE,
        )
        self.plotIMS_butt.SetToolTip(wx.ToolTip('Plot (2D) information'))
        self.plotIMS_butt.Bind(wx.EVT_BUTTON, self.onToolSelected)

        self.plotCali_butt = wx.BitmapButton(
            panel,
            ID_documentInfoCalibration,
            self.icons.iconsLib['plotCalibration16'],
            size=(toolbar_toolsize),
            style=wx.BORDER_NONE,
        )
        self.plotCali_butt.SetToolTip(wx.ToolTip('CCS calibration information'))
        self.plotCali_butt.Bind(wx.EVT_BUTTON, self.onToolSelected)

        self.notes_butt = wx.BitmapButton(
            panel, ID_documentInfoNotes, self.icons.iconsLib['document16'],
            size=(toolbar_toolsize), style=wx.BORDER_NONE,
        )
        self.notes_butt.SetToolTip(wx.ToolTip('Analysis notes'))
        self.notes_butt.Bind(wx.EVT_BUTTON, self.onToolSelected)

        self.presets_butt = wx.BitmapButton(
            panel, ID_saveAsConfig, self.icons.iconsLib['save16'],
            size=(toolbar_toolsize),
            style=wx.BORDER_NONE,
        )
        self.presets_butt.SetToolTip(wx.ToolTip('Operator presets'))
        self.presets_butt.Bind(wx.EVT_BUTTON, self.presenter.onExportConfig, id=ID_saveAsConfig)

        # pack elements
        self.toolbar = wx.BoxSizer(wx.HORIZONTAL)
        self.toolbar.AddSpacer(spacer)
        self.toolbar.Add(self.summary_butt, 0, wx.ALIGN_CENTER_VERTICAL)
        self.toolbar.AddSpacer(spacer)
        self.toolbar.Add(self.spectrum_butt, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, button_size_correction)
        self.toolbar.AddSpacer(spacer)
        self.toolbar.Add(self.plotIMS_butt, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, button_size_correction)
        self.toolbar.AddSpacer(spacer)
        self.toolbar.Add(self.plotCali_butt, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, button_size_correction)
        self.toolbar.AddSpacer(spacer)
        self.toolbar.Add(self.notes_butt, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, button_size_correction)
        self.toolbar.AddSpacer(spacer_l)
        self.toolbar.Add(self.presets_butt, 0, wx.ALIGN_CENTER_VERTICAL)
        self.toolbar.AddSpacer(toolbar_rspace)

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(self.toolbar, 1, wx.EXPAND)
        panel.SetSizer(mainSizer)
        mainSizer.Fit(panel)

        return panel
    # ----

    def makeBtnPanel(self):
        """ Document button panel"""
        panel = wx.Panel(self, -1)

        applyBtn = wx.Button(panel, -1, 'Apply', size=(80, -1))
        self.plotBtn = wx.Button(panel, -1, 'Replot', size=(80, -1))
        self.plotBtn.Hide()
        cancelBtn = wx.Button(panel, -1, 'Close', size=(80, -1))

#         panel_space_main = 10

        # pack elements
        mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        grid = wx.GridBagSizer(2, 2)
        grid.Add(applyBtn, (0, 0), flag=wx.ALIGN_CENTER | wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(self.plotBtn, (0, 1), flag=wx.ALIGN_CENTER | wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(cancelBtn, (0, 2), flag=wx.ALIGN_CENTER | wx.ALIGN_CENTER_HORIZONTAL)

        mainSizer.Add(grid, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)

        # Bind
        applyBtn.Bind(wx.EVT_BUTTON, self.on_apply)
        self.plotBtn.Bind(wx.EVT_BUTTON, self.onReplot)
        cancelBtn.Bind(wx.EVT_BUTTON, self.on_close)

        return panel

    def makeNotesPanel(self):
        """Document notes panel."""

        panel = wx.Panel(self, -1)

        PANEL_SPACE_MAIN = 10

        # make elements
        self.notes_value = wx.TextCtrl(panel, -1, '', size=(400, 200), style=wx.TE_MULTILINE)
        self.notes_value.SetValue(self.document.notes)
        self.notes_value.Bind(wx.EVT_TEXT, self.on_apply)

        # pack elements
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(
            self.notes_value, 1, wx.EXPAND | wx.ALIGN_CENTER | wx.ALL,
            PANEL_SPACE_MAIN,
        )

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)

        return panel
    # ----

    def makeSummaryPanel(self):
        """Document summary panel."""

        panel = wx.Panel(self, -1)
        PANEL_SPACE_MAIN = 20

        if hasattr(self.document, 'userParameters'):
            pass
        else:
            print('Added attributes from config')
            self.document.userParameters = self.config.userParameters

        # make elements
        title_label = wx.StaticText(panel, -1, 'Title:')
        self.title_value = wx.TextCtrl(panel, -1, '', size=(300, -1))
        self.title_value.SetValue(self.document.title)
        self.title_value.Disable()

        operator_label = wx.StaticText(panel, -1, 'Operator:')
        self.operator_value = wx.TextCtrl(panel, -1, '', size=(300, -1))
        self.operator_value.SetValue(self.document.userParameters.get('operator', None))
        self.operator_value.Bind(wx.EVT_TEXT, self.on_apply)

        contact_label = wx.StaticText(panel, -1, 'Contact:')
        self.contact_value = wx.TextCtrl(panel, -1, '', size=(300, -1))
        self.contact_value.SetValue(self.document.userParameters.get('contact', None))
        self.contact_value.Bind(wx.EVT_TEXT, self.on_apply)

        institution_label = wx.StaticText(panel, -1, 'Institution:')
        self.institution_value = wx.TextCtrl(panel, -1, '', size=(300, -1))
        self.institution_value.SetValue(self.document.userParameters.get('institution', None))
        self.institution_value.Bind(wx.EVT_TEXT, self.on_apply)

        instrument_label = wx.StaticText(panel, -1, 'Instrument:')
        self.instrument_value = wx.TextCtrl(panel, -1, '', size=(300, -1))
        self.instrument_value.SetValue(self.document.userParameters.get('instrument', None))
        self.instrument_value.Bind(wx.EVT_TEXT, self.on_apply)

        date_label = wx.StaticText(panel, -1, 'Created on:')
        self.date_value = wx.TextCtrl(panel, -1, '', size=(300, -1))
        self.date_value.SetValue(self.document.userParameters.get('date', None))
        self.date_value.Disable()

        path_label = wx.StaticText(panel, -1, 'Path:')
        self.path_value = wx.TextCtrl(panel, -1, '', size=(300, -1))
        self.path_value.SetValue(self.document.path)
        self.path_value.Bind(wx.EVT_TEXT, self.on_apply)

        self.path_check = makeCheckbox(panel, '')
        self.path_check.SetToolTip(wx.ToolTip('Enable/disable'))
        self.path_check.SetValue(False)
        self.path_check.Bind(wx.EVT_CHECKBOX, self.onEnableDisable)

        self.chgDirBtn = wx.Button(panel, -1, '...', size=(20, -1))
        self.chgDirBtn.Bind(wx.EVT_BUTTON, self.onChangeDocPath)

        # pack elements
        grid = wx.GridBagSizer(2, 2)
        grid.Add(title_label, (0, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.title_value, (0, 1), flag=wx.EXPAND)
        grid.Add(operator_label, (1, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.operator_value, (1, 1))
        grid.Add(contact_label, (2, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.contact_value, (2, 1))
        grid.Add(institution_label, (3, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.institution_value, (3, 1))
        grid.Add(instrument_label, (4, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.instrument_value, (4, 1))
        grid.Add(date_label, (5, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.date_value, (5, 1))
        grid.Add(path_label, (6, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.path_value, (6, 1))
        grid.Add(self.path_check, (6, 3), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)

        grid.Add(self.chgDirBtn, (6, 2))

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(grid, 0, wx.ALIGN_CENTER | wx.ALL, PANEL_SPACE_MAIN)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)

        return panel
    # ----

    def makeSpectrumPanel(self):
        """Document summary panel."""

        panel = wx.Panel(self, -1)
        PANEL_SPACE_MAIN = 20

        if hasattr(self.document, 'moleculeDetails'):
            pass
        else:
            self.document.moleculeDetails = {}
        if hasattr(self.document, 'fileInformation'):
            pass
        else:
            self.document.fileInformation = {}

        # make elements
        docType_label = wx.StaticText(panel, -1, 'Document type:')
        self.docType_choice = wx.Choice(
            panel, -1, choices=[
                'Type: ORIGAMI',
                'Type: MANUAL',
                'Type: Multifield Linear DT',
                'Type: CALIBRANT',
                'Type: Comparison',
                'Type: Interactive',
                'Other',
            ],
            size=(180, -1),
        )

        if self.document.dataType == 'Type: ORIGAMI':
            self.docType_choice.SetStringSelection('Type: ORIGAMI')
        elif self.document.dataType == 'Type: MANUAL':
            self.docType_choice.SetStringSelection('Type: MANUAL')
        elif self.document.dataType == 'Type: Multifield Linear DT':
            self.docType_choice.SetStringSelection('Type: Multifield Linear DT')
        elif self.document.dataType == 'Type: CALIBRANT':
            self.docType_choice.SetStringSelection('Type: CALIBRANT')
        elif self.document.dataType == 'Type: Comparison':
            self.docType_choice.SetStringSelection('Type: Comparison')
        elif self.document.dataType == 'Type: Interactive':
            self.docType_choice.SetStringSelection('Type: Interactive')
        else:
            self.docType_choice.SetStringSelection('Other')

        self.docType_choice.Bind(wx.EVT_COMBOBOX, self.on_apply)

        self.docType_check = makeCheckbox(panel, '')
        self.docType_check.SetToolTip(wx.ToolTip('Enable/disable'))
        self.docType_check.SetValue(False)
        self.docType_check.Bind(wx.EVT_CHECKBOX, self.onEnableDisable)

        scanTime_label = wx.StaticText(panel, -1, 'Scan time (s):')
        self.scanTime_value = wx.TextCtrl(panel, -1, '', size=(180, -1))
        self.scanTime_value.SetValue(num2str(self.document.parameters.get('scanTime', None)))
        self.scanTime_value.Bind(wx.EVT_TEXT, self.on_apply)
        self.scanTime_check = makeCheckbox(panel, '')
        self.scanTime_check.SetValue(False)
        self.scanTime_check.Bind(wx.EVT_CHECKBOX, self.onEnableDisable)

        protein_label = wx.StaticText(panel, -1, 'Protein:')
        self.protein_value = wx.TextCtrl(panel, -1, '', size=(180, -1))
        self.protein_value.SetValue(num2str(self.document.moleculeDetails.get('protein', None)))
        self.protein_value.Bind(wx.EVT_TEXT, self.on_apply)

        self.selectBtn = wx.Button(
            panel, ID_selectProtein, '...',
            wx.DefaultPosition, wx.Size(25, -1), 0,
        )

        # self.selectBtn.Bind(wx.EVT_BUTTON, self.presenter.onSelectProtein, id=ID_selectProtein)

        molWeight_label = wx.StaticText(panel, -1, 'Molecular weight (Da):')
        self.molWeight_value = wx.TextCtrl(panel, -1, '', size=(180, -1))
        self.molWeight_value.SetValue(num2str(self.document.moleculeDetails.get('molWeight', None)))
        self.molWeight_value.Bind(wx.EVT_TEXT, self.on_apply)

        precursorMZ_label = wx.StaticText(panel, -1, 'Precursor m/z:')
        self.precursorMZ_value = wx.TextCtrl(panel, -1, '', size=(180, -1))
        self.precursorMZ_value.SetValue(num2str(self.document.parameters.get('setMS', None)))
        self.precursorMZ_value.Bind(wx.EVT_TEXT, self.on_apply)

        precursorCharge_label = wx.StaticText(panel, -1, 'Precursor charge:')
        self.precursorCharge_value = wx.TextCtrl(panel, -1, '', size=(180, -1))
        self.precursorCharge_value.SetValue(num2str(self.document.moleculeDetails.get('charge', None)))
        self.precursorCharge_value.Bind(wx.EVT_TEXT, self.on_apply)

        pusherFreq_label = wx.StaticText(panel, -1, 'Pusher frequency (μs):')
        self.pusherFreq_value = wx.TextCtrl(panel, -1, '', size=(180, -1))
        self.pusherFreq_value.SetValue(num2str(self.document.parameters.get('pusherFreq', None)))
        self.pusherFreq_value.Bind(wx.EVT_TEXT, self.on_apply)

        self.pusherFreq_check = makeCheckbox(panel, '')
        self.pusherFreq_check.SetValue(False)
        self.pusherFreq_check.Bind(wx.EVT_CHECKBOX, self.onEnableDisable)

        tofCorrFactor_label = wx.StaticText(panel, -1, 'TOF corr. factor (EDC):')
        self.tofCorrFactor_value = wx.TextCtrl(panel, -1, '', size=(180, -1))
        self.tofCorrFactor_value.SetValue(num2str(self.document.parameters.get('corrC', None)))
        self.tofCorrFactor_value.Bind(wx.EVT_TEXT, self.on_apply)

        self.tofCorrFactor_check = makeCheckbox(panel, '')
        self.tofCorrFactor_check.SetValue(False)
        self.tofCorrFactor_check.Bind(wx.EVT_CHECKBOX, self.onEnableDisable)

        headerInfo_label = wx.StaticText(panel, -1, 'Header information:')
        self.headerInfo_value = wx.TextCtrl(panel, -1, '', size=(180, 100), style=wx.TE_WORDWRAP | wx.TE_MULTILINE)
        self.headerInfo_value.SetValue(self.document.fileInformation.get('SampleDescription', 'None'))
        self.headerInfo_value.Disable()

        polarity_label = wx.StaticText(panel, -1, 'Polarity:')
        self.polarity_choice = wx.Choice(
            panel, -1, choices=['Positive', 'Negative', 'Undefined'],
            size=(180, -1),
        )
        if self.document.parameters.get('ionPolarity', None) == 'ES+':
            self.polarity_choice.SetStringSelection('Positive')
        elif self.document.parameters.get('ionPolarity', None) == 'ES-':
            self.polarity_choice.SetStringSelection('Negative')
        else:
            self.polarity_choice.SetStringSelection('Undefined')

        self.polarity_choice.Bind(wx.EVT_COMBOBOX, self.on_apply)

        # pack elements
        grid = wx.GridBagSizer(2, 2)
        grid.Add(docType_label, (0, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.docType_choice, (0, 1))
        grid.Add(self.docType_check, (0, 2), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(protein_label, (1, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.protein_value, (1, 1))
        grid.Add(self.selectBtn, (1, 2))
        grid.Add(molWeight_label, (2, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.molWeight_value, (2, 1))
        grid.Add(precursorMZ_label, (3, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.precursorMZ_value, (3, 1))
        grid.Add(precursorCharge_label, (4, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.precursorCharge_value, (4, 1))

        grid.Add(scanTime_label, (5, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.scanTime_value, (5, 1))
        grid.Add(self.scanTime_check, (5, 2), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(pusherFreq_label, (6, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.pusherFreq_value, (6, 1))
        grid.Add(self.pusherFreq_check, (6, 2), flag=wx.ALIGN_CENTER_VERTICAL)

        grid.Add(tofCorrFactor_label, (7, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.tofCorrFactor_value, (7, 1))
        grid.Add(self.tofCorrFactor_check, (7, 2), flag=wx.ALIGN_CENTER_VERTICAL)

        grid.Add(polarity_label, (8, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.polarity_choice, (8, 1))

        grid.Add(headerInfo_label, (9, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.headerInfo_value, (9, 1), wx.GBSpan(2, 2))

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(grid, 0, wx.ALIGN_CENTER | wx.ALL, PANEL_SPACE_MAIN)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)

        return panel

    def makeIMS2DPanel(self):
        """Document summary panel."""

        panel = wx.Panel(self, -1)
        PANEL_SPACE_MAIN = 20

        # Determine which dataset is used
        if self.itemType is None:
            self.plot2Dtitle = ''.join(['Plot (2D) Summary: ', 'Global'])
            plotType = 'Raw'
            data = self.document.IMS2D
        elif self.itemType == 'Drift time (2D)':
            plotType = 'Raw'
            self.plot2Dtitle = ''.join(['Plot (2D) Summary: ', 'Global'])
            data = self.document.IMS2D
        elif self.itemType == 'Drift time (2D, processed)':
            plotType = 'Processed'
            self.plot2Dtitle = ''.join(['Plot (2D) Summary: ', 'Global'])
            data = self.document.IMS2Dprocess
        elif self.itemType == 'Drift time(2D, EIC)' and self.extractData is not None:
            plotType = 'Raw'
            self.plot2Dtitle = ''.join(['Plot (2D) Summary: ', self.extractData])
            data = self.document.IMS2Dions[self.extractData]
        elif self.itemType == 'Drift time(2D, combined voltages, EIC)' and self.extractData is not None:
            plotType = 'Processed'
            self.plot2Dtitle = ''.join(['Plot (2D) Summary: ', self.extractData])
            data = self.document.IMS2DCombIons[self.extractData]
        elif self.itemType == 'Drift time(2D, processed, EIC)' and self.extractData is not None:
            plotType = 'Combined'
            self.plot2Dtitle = ''.join(['Plot (2D) Summary: ', self.extractData])
            data = self.document.IMS2DionsProcess[self.extractData]
        elif self.itemType == 'Input data' and self.extractData is not None:
            plotType = 'Processed'
            self.plot2Dtitle = ''.join(['Plot (2D) Summary: ', self.extractData])
            data = self.document.IMS2DcompData[self.extractData]
        else:
            self.plot2Dtitle = ''.join(['Plot (2D) Summary: ', 'Global'])
            plotType = 'Raw'
            data = self.document.IMS2D

        # make elements
        type_label = wx.StaticText(panel, -1, 'Plot type:')
        self.type_value = wx.TextCtrl(panel, -1, '', size=(180, -1))
        self.type_value.SetValue(plotType)
        self.type_value.Disable()

        charge_label = wx.StaticText(panel, -1, 'Charge:')
        self.charge_value = wx.TextCtrl(panel, -1, '', size=(180, -1))
        charge = data.get('charge', 'None')

        if charge == 'None' or charge == '' or charge is None:
            charge = 1
        else:
            charge = str2int(charge)
        self.charge_value.SetValue(str(charge))
        self.charge_value.Bind(wx.EVT_TEXT, self.on_apply)

        labelsX_label = wx.StaticText(panel, -1, 'X-labels:')
        self.labelsX_value = wx.Choice(
            panel, -1, choices=self.config.labelsXChoices,
            size=(180, -1),
        )
        self.labelsX_value.SetStringSelection(data.get('xlabels', 'Scans'))
        self.labelsX_value.Bind(wx.EVT_COMBOBOX, self.on_apply)

        self.labelsX_check = makeCheckbox(panel, 'Just label')
        self.labelsX_check.SetValue(False)
        self.labelsX_check.Bind(wx.EVT_CHECKBOX, self.onEnableDisable)
        self.restoreDefaultX_check = makeCheckbox(panel, 'Restore default')
        self.restoreDefaultX_check.SetValue(False)
        self.restoreDefaultX_check.Bind(wx.EVT_CHECKBOX, self.onEnableDisable)

        labelsY_label = wx.StaticText(panel, -1, 'Y-labels:')
        self.labelsY_value = wx.Choice(
            panel, -1, choices=self.config.labelsYChoices,
            size=(180, -1),
        )
        self.labelsY_value.SetStringSelection(data.get('ylabels', 'Drift time (bins)'))
        self.labelsY_value.Bind(wx.EVT_COMBOBOX, self.on_apply)

        self.labelsY_check = makeCheckbox(panel, 'Just label')
        self.labelsY_check.SetValue(False)
        self.labelsY_check.Bind(wx.EVT_CHECKBOX, self.onEnableDisable)
        self.restoreDefaultY_check = makeCheckbox(panel, 'Restore default')
        self.restoreDefaultY_check.SetValue(False)
        self.restoreDefaultY_check.Bind(wx.EVT_CHECKBOX, self.onEnableDisable)

        shape_label = wx.StaticText(panel, -1, 'Shape:')
        self.shape_value = wx.TextCtrl(panel, -1, '', size=(180, -1))
        try:
            dataShape = data['zvals'].shape
        except KeyError:
            dataShape = None
        self.shape_value.SetValue(str(dataShape))
        self.shape_value.Bind(wx.EVT_TEXT, self.on_apply)
        self.shape_value.Disable()

        colormap_label = wx.StaticText(panel, -1, 'Colormap:')
        self.colormap_value = wx.Choice(
            panel, -1, choices=self.config.cmaps2,
            size=(180, -1),
        )
        self.colormap_value.SetStringSelection(data.get('cmap', 'None'))
        self.colormap_value.Bind(wx.EVT_TEXT, self.on_apply)

        # pack elements
        grid = wx.GridBagSizer(2, 2)
        grid.Add(type_label, (0, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.type_value, (0, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        grid.Add(charge_label, (1, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.charge_value, (1, 1), wx.GBSpan(1, 2))

        grid.Add(labelsX_label, (2, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.labelsX_value, (2, 1), wx.GBSpan(1, 2))
        grid.Add(self.labelsX_check, (3, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.restoreDefaultX_check, (3, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)

        grid.Add(labelsY_label, (4, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.labelsY_value, (4, 1), wx.GBSpan(1, 2))
        grid.Add(self.labelsY_check, (5, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.restoreDefaultY_check, (5, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)

        grid.Add(shape_label, (6, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.shape_value, (6, 1), wx.GBSpan(1, 2))
        grid.Add(colormap_label, (7, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.colormap_value, (7, 1), wx.GBSpan(1, 2))

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(grid, 0, wx.ALIGN_CENTER | wx.ALL, PANEL_SPACE_MAIN)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)

        return panel
    # ----

    def makeCCSCalibrationPanel(self):

        panel = wx.Panel(self, -1)
        PANEL_SPACE_MAIN = 20

        calibrationType_label = wx.StaticText(panel, -1, 'Calibration type:')
        self.calibrationType_value = wx.Choice(
            panel, -1, choices=['Linear', 'Power'],
            size=(180, -1),
        )
        self.calibrationType_value.Disable()

        self.calibrationType_check = makeCheckbox(panel, '')
        self.calibrationType_check.SetValue(False)

        numOfPoints_label = wx.StaticText(panel, -1, 'Number of points:')
        self.numOfPoints_value = wx.TextCtrl(panel, -1, '', size=(180, -1))
        self.numOfPoints_value.Disable()

        numOfCalibrants_label = wx.StaticText(panel, -1, 'Number of calibrants:')
        self.numOfCalibrants_value = wx.TextCtrl(panel, -1, '', size=(180, -1))
        self.numOfCalibrants_value.Disable()

        calibrants_label = wx.StaticText(panel, -1, 'Calibrants:')
        self.calibrants_value = wx.TextCtrl(
            panel, -1, '', size=(180, 100),
            style=wx.TE_WORDWRAP | wx.TE_MULTILINE,
        )
        self.calibrants_value.Disable()

        linear_label = wx.StaticText(panel, -1, 'Linear')
        power_label = wx.StaticText(panel, -1, 'Power')

        slope_label = wx.StaticText(panel, -1, 'Slope:')
        self.slopeLinear_value = wx.TextCtrl(
            panel, -1, '', size=(90, -1),
            style=wx.TE_READONLY,
        )

        self.slopePower_value = wx.TextCtrl(
            panel, -1, '', size=(90, -1),
            style=wx.TE_READONLY,
        )

        intercept_label = wx.StaticText(panel, -1, 'Intercept:')
        self.interceptLinear_value = wx.TextCtrl(
            panel, -1, '', size=(90, -1),
            style=wx.TE_READONLY,
        )
        self.interceptPower_value = wx.TextCtrl(
            panel, -1, '', size=(90, -1),
            style=wx.TE_READONLY,
        )

        r2_label = wx.StaticText(panel, -1, 'R²:')
        self.r2Linear_value = wx.TextCtrl(
            panel, -1, '', size=(90, -1),
            style=wx.TE_READONLY,
        )
        self.r2Power_value = wx.TextCtrl(
            panel, -1, '', size=(90, -1),
            style=wx.TE_READONLY,
        )

        # bind events
        self.calibrationType_value.Bind(wx.EVT_COMBOBOX, self.on_apply)
        self.calibrationType_check.Bind(wx.EVT_CHECKBOX, self.onEnableDisable)

        # check if document has calibration parameters
        if self.document.gotCalibrationParameters:
            parameters = self.document.calibrationParameters.get('parameters', None)
            if parameters is not None:
                slopeLinear, interceptLinear, r2Linear = parameters['linear']
                slopePower, interceptPower, r2Power = parameters['power']
#                 gas = parameters['gas']
                mode = parameters.get('mode', 'Power')
                # set values
                self.calibrationType_value.SetStringSelection(mode)

                self.slopeLinear_value.SetValue(str(np.round(slopeLinear, 4)))
                self.slopePower_value.SetValue(str(np.round(slopePower, 4)))

                self.interceptLinear_value.SetValue(str(np.round(interceptLinear, 4)))
                self.interceptPower_value.SetValue(str(np.round(interceptPower, 4)))

                self.r2Linear_value.SetValue(str(np.round(r2Linear, 4)))
                self.r2Power_value.SetValue(str(np.round(r2Power, 4)))

        # pack elements
        grid = wx.GridBagSizer(2, 2)
        grid.Add(calibrationType_label, (0, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.calibrationType_value, (0, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)
        grid.Add(self.calibrationType_check, (0, 3), wx.GBSpan(1, 1), flag=wx.EXPAND)

        grid.Add(calibrants_label, (1, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.calibrants_value, (1, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)

        grid.Add(numOfPoints_label, (2, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.numOfPoints_value, (2, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)

        grid.Add(numOfCalibrants_label, (3, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.numOfCalibrants_value, (3, 1), wx.GBSpan(1, 2), flag=wx.EXPAND)

        grid.Add(linear_label, (4, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER)
        grid.Add(power_label, (4, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER)

        grid.Add(slope_label, (5, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.slopeLinear_value, (5, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        grid.Add(self.slopePower_value, (5, 2), wx.GBSpan(1, 1), flag=wx.EXPAND)

        grid.Add(intercept_label, (6, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.interceptLinear_value, (6, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        grid.Add(self.interceptPower_value, (6, 2), wx.GBSpan(1, 1), flag=wx.EXPAND)

        grid.Add(r2_label, (7, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.r2Linear_value, (7, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        grid.Add(self.r2Power_value, (7, 2), wx.GBSpan(1, 1), flag=wx.EXPAND)

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(grid, 0, wx.ALIGN_CENTER | wx.ALL | wx.EXPAND, PANEL_SPACE_MAIN)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)

        return panel

    def makeEmptyPanel(self):
        panel = wx.Panel(self, -1)

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        grid = wx.GridBagSizer(2, 2)
        mainSizer.Add(grid, 0, wx.ALIGN_CENTER | wx.ALL, 20)
        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)

        return panel

    def onToolSelected(self, evt=None, tool=None):
        """
        Selected tool.
        """

        # get the tool
        if evt is not None:
            tool = 'summary'
            if evt.GetId() == ID_documentInfoSummary:
                tool = 'summary'
            elif evt.GetId() == ID_documentInfoSpectrum:
                tool = 'spectrum'
            elif evt.GetId() == ID_documentInfoPlotIMS:
                tool = 'plot2D'
            elif evt.GetId() == ID_documentInfoCalibration:
                tool = 'plotCalibration'
            elif evt.GetId() == ID_documentInfoNotes:
                tool = 'notes'

        # hide panels
        self.mainSizer.Hide(1)
        self.mainSizer.Hide(2)
        self.mainSizer.Hide(3)
        self.mainSizer.Hide(4)
        self.mainSizer.Hide(5)

        if tool == 'summary':
            self.SetTitle('Document Information')
            self.mainSizer.Show(1)
            self.plotBtn.Hide()
        elif tool == 'spectrum':
            self.SetTitle('Document Summary')
            self.mainSizer.Show(2)
            self.plotBtn.Hide()
        elif tool == 'plot2D':
            if not self.plot2Dtitle:
                self.SetTitle('Plot (2D) Summary')
            else:
                self.SetTitle(self.plot2Dtitle)
            self.mainSizer.Show(3)
            self.plotBtn.Show()
        elif tool == 'plotCalibration':
            self.SetTitle('CCS Calibration Summary')
            self.plotBtn.Hide()
            self.mainSizer.Show(4)
        elif tool == 'notes':
            self.SetTitle('Notes')
            self.mainSizer.Show(5)
            self.plotBtn.Hide()

        layout(self, self.mainSizer)

    def on_apply(self, evt):
        """
        This function applies any changes made to the document
        """

        # Update document summary
        self.document.userParameters['operator'] = self.operator_value.GetValue()
        self.document.userParameters['contact'] = self.contact_value.GetValue()
        self.document.userParameters['institution'] = self.institution_value.GetValue()
        self.document.userParameters['instrument'] = self.instrument_value.GetValue()

        # Update document information
        self.document.dataType = self.docType_choice.GetStringSelection()
        self.document.path = self.path_value.GetValue()
        self.document.parameters['scanTime'] = str2num(self.scanTime_value.GetValue())
        self.document.parameters['setMS'] = self.precursorMZ_value.GetValue()
        self.document.parameters['ionPolarity'] = self.polarity_choice.GetStringSelection()
        self.document.parameters['pusherFreq'] = str2num(self.pusherFreq_value.GetValue())
        self.document.parameters['corrC'] = str2num(self.tofCorrFactor_value.GetValue())
        self.document.corrC = str2num(self.tofCorrFactor_value.GetValue())
        self.document.moleculeDetails['charge'] = str2int(self.precursorCharge_value.GetValue())
        self.document.moleculeDetails['protein'] = self.protein_value.GetValue()
        self.document.moleculeDetails['molWeight'] = str2num(self.molWeight_value.GetValue())

        # Update notes
        self.document.notes = self.notes_value.GetValue()

# ---
        if (
            hasattr(self, 'restoreDefaultX_check') and hasattr(self, 'restoreDefaultY_check') and
            hasattr(self, 'labelsX_check') and hasattr(self, 'labelsY_check')
        ):

            # Determine which dataset is used
            if self.itemType is None:
                data = self.document.IMS2D
            elif self.itemType == 'Drift time (2D)':
                data = self.document.IMS2D
            elif self.itemType == 'Drift time (2D, processed)':
                data = self.document.IMS2Dprocess
            elif self.itemType == 'Drift time (2D, EIC)' and self.extractData is not None:
                data = self.document.IMS2Dions[self.extractData]
            elif self.itemType == 'Drift time (2D, combined voltages, EIC)' and self.extractData is not None:
                data = self.document.IMS2DCombIons[self.extractData]
            elif self.itemType == 'Drift time (2D, processed, EIC)' and self.extractData is not None:
                data = self.document.IMS2DionsProcess[self.extractData]
            elif self.itemType == 'Input data' and self.extractData is not None:
                data = self.document.IMS2DcompData[self.extractData]
            else:
                data = {}

            # Add default values
            if 'defaultX' not in data:
                data['defaultX'] = {
                    'xlabels': data['xlabels'],
                    'xvals': data['xvals'],
                }
            if 'defaultY' not in data:
                data['defaultY'] = {
                    'ylabels': data['ylabels'],
                    'yvals': data['yvals'],
                }

            # Check if restore tickes have been checked
            if self.restoreDefaultX_check.GetValue():
                self.labelsX_value.SetStringSelection(data['defaultX']['xlabels'])

            if self.restoreDefaultY_check.GetValue():
                self.labelsY_value.SetStringSelection(data['defaultY']['ylabels'])

            # Change charge state
            data['charge'] = str2int(self.charge_value.GetValue())
            data['cmap'] = self.colormap_value.GetStringSelection()

            # If restoring defaults, we need to reset labels + values
            if self.restoreDefaultX_check.GetValue():
                data['xvals'] = data['defaultX']['xvals']
                data['xlabels'] = self.labelsX_value.GetStringSelection()

            if self.restoreDefaultY_check.GetValue():
                data['yvals'] = data['defaultY']['yvals']
                data['ylabels'] = self.labelsY_value.GetStringSelection()

            # Changing labels and values
            oldXLabel = data['xlabels']
            data['xlabels'] = self.labelsX_value.GetStringSelection()
            if not self.labelsX_check.GetValue():
                newXvals = self.parent.on_change_xy_axis(
                    data['xvals'], oldXLabel,
                    self.labelsX_value.GetStringSelection(),
                    charge=self.charge_value.GetValue(),
                    defaults=data['defaultX'],
                )
                data['xvals'] = newXvals

            oldYLabel = data['ylabels']
            data['ylabels'] = self.labelsY_value.GetStringSelection()
            if not self.labelsY_check.GetValue():
                newYvals = self.parent.on_change_xy_axis(
                    data['yvals'], oldYLabel,
                    self.labelsY_value.GetStringSelection(),
                    pusherFreq=self.pusherFreq_value.GetValue(),
                    defaults=data['defaultY'],
                )
                data['yvals'] = newYvals

            # Update other parameters
            data['mw'] = str2num(self.molWeight_value.GetValue())

            # Replace data in the dictionary
            if self.itemType is None:
                self.document.IMS2D = data
            elif self.itemType == 'Drift time (2D)':
                self.document.IMS2D = data
            elif self.itemType == 'Drift time (2D, processed)':
                self.document.IMS2Dprocess = data
            elif self.itemType == 'Drift time (2D, EIC)' and self.extractData is not None:
                self.document.IMS2Dions[self.extractData] = data
            elif self.itemType == 'Drift time (2D, combined voltages, EIC)' and self.extractData is not None:
                self.document.IMS2DCombIons[self.extractData] = data
            elif self.itemType == 'Drift time (2D, processed, EIC)' and self.extractData is not None:
                self.document.IMS2DionsProcess[self.extractData] = data
            else:
                self.document.IMS2D = data

            # Since charge state is inherent to the m/z range, it needs to be changed iteratively for each dataset
            if self.itemType is None:
                pass
            elif any(
                self.itemType in itemType for itemType in [
                    'Drift time (2D, EIC)',
                    'Combined CV 2D IM-MS (multiple ions)',
                    'Drift time (2D, processed, EIC)',
                    'Drift time (1D, EIC)',
                    'Drift time (2D, combined voltages, EIC)',
                ]
            ):
                if self.extractData in self.document.IMS2Dions:
                    self.document.IMS2Dions[self.extractData]['charge'] = str2int(self.charge_value.GetValue())
                if self.extractData in self.document.IMS2DCombIons:
                    self.document.IMS2DCombIons[self.extractData]['charge'] = str2int(self.charge_value.GetValue())
                if self.extractData in self.document.IMS2DionsProcess:
                    self.document.IMS2DionsProcess[self.extractData]['charge'] = str2int(self.charge_value.GetValue())
                if self.extractData in self.document.IMSRTCombIons:
                    self.document.IMSRTCombIons[self.extractData]['charge'] = str2int(self.charge_value.GetValue())
                if self.extractData in self.document.IMS1DdriftTimes:
                    self.document.IMS1DdriftTimes[self.extractData]['charge'] = str2int(self.charge_value.GetValue())

                # Only to MANUAL data type
                for key in self.document.IMS1DdriftTimes:
                    splitText = re.split('-| |,|', key)
                    if '-'.join([splitText[0], splitText[1]]) == self.extractData:
                        self.document.IMS1DdriftTimes[key]['charge'] = str2int(self.charge_value.GetValue())

            # We also have to check if there is data in the table
            if (
                self.document.dataType == 'Type: ORIGAMI' or
                self.document.dataType == 'Type: MANUAL'
            ) and self.extractData is not None:

                splitText = self.extractData.split('-')
                row = self.presenter.view.panelMultipleIons.findItem(
                    splitText[0],
                    splitText[1],
                    self.document.title,
                )
                if row is not None:
                    self.presenter.view.panelMultipleIons.peaklist.SetStringItem(
                        index=row, col=self.config.peaklistColNames['charge'], label=self.charge_value.GetValue(),
                    )

# ---

        # Update list
        self.presenter.documentsDict[self.document.title] = self.document

    def onEnableDisable(self, evt):
        # ---
        if not self.scanTime_check.GetValue():
            self.scanTime_value.Disable()
        else:
            self.scanTime_value.Enable()

        if not self.pusherFreq_check.GetValue():
            self.pusherFreq_value.Disable()
        else:
            self.pusherFreq_value.Enable()

        if not self.tofCorrFactor_check.GetValue():
            self.tofCorrFactor_value.Disable()
        else:
            self.tofCorrFactor_value.Enable()

        if not self.docType_check.GetValue():
            self.docType_choice.Disable()
        else:
            self.docType_choice.Enable()

        if not self.calibrationType_check.GetValue():
            self.calibrationType_value.Disable()
        else:
            self.calibrationType_value.Enable()
# ---
        if not self.path_check.GetValue():
            self.path_value.Disable()
            self.chgDirBtn.Disable()
        else:
            self.path_value.Enable()
            self.chgDirBtn.Enable()

# ---
        if hasattr(self, 'restoreDefaultX_check') and hasattr(self, 'restoreDefaultY_check'):
            if self.restoreDefaultX_check.GetValue():
                self.labelsX_check.Disable()
                self.labelsX_value.Disable()
            else:
                self.labelsX_check.Enable()
                self.labelsX_value.Enable()
# ---
            if self.restoreDefaultY_check.GetValue():
                self.labelsY_check.Disable()
                self.labelsY_value.Disable()
            else:
                self.labelsY_check.Enable()
                self.labelsY_value.Enable()
# ---
        if hasattr(self, 'labelsX_check') and hasattr(self, 'labelsY_check'):
            if self.labelsX_check.GetValue():
                self.restoreDefaultX_check.Disable()
            else:
                self.restoreDefaultX_check.Enable()
# ---
            if self.labelsY_check.GetValue():
                self.restoreDefaultY_check.Disable()
            else:
                self.restoreDefaultY_check.Enable()

    def onAnnotateProteinInfo(self, data):
        """
        receive data from the 'Select protein...' panel and add it to the GUI
        """
        protein = data[0]
        mw = str(str2num(data[1]) * 1000)
        self.protein_value.SetValue(protein)
        self.molWeight_value.SetValue(mw)

    def onChangeDocPath(self, evt):
        dlg = wx.DirDialog(
            self.parent, 'Choose new path to the document file',
            style=wx.DD_DEFAULT_STYLE,
        )

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.path_value.SetValue(path)

    def onReplot(self, evt):

        self.on_apply(evt=None)
        self.parent.onShowPlot(evt=None)
