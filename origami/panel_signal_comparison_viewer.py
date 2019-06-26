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
import wx
from natsort import natsorted

from help_documentation import OrigamiHelp
from ids import (
    ID_compareMS_MS_1, ID_compareMS_MS_2, ID_extraSettings_legend,
    ID_extraSettings_plot1D, ID_processSettings_MS)
from styles import makeCheckbox, makeStaticBox, makeSuperTip
from utils.color import convertRGB1to255, convertRGB255to1
from utils.converters import str2num
from gui_elements.dialog_color_picker import DialogColorPicker


class panel_signal_comparison_viewer(wx.MiniFrame):
    """
    Simple GUI to select mass spectra to compare
    """

    def __init__(self, parent, presenter, config, icons, **kwargs):
        wx.MiniFrame.__init__(self, parent, -1, 'Compare mass spectra...', size=(-1, -1),
                              style=wx.DEFAULT_FRAME_STYLE & ~wx.RESIZE_BORDER)

        self.parent = parent
        self.presenter = presenter
        self.config = config
        self.icons = icons

        self.help = OrigamiHelp()

        self.currentItem = None
        self.kwargs = kwargs
        self.current_document = self.kwargs['current_document']
        self.document_list = self.kwargs['document_list']

        # make gui items
        self.make_gui()

        self.Centre()
        self.Layout()
        self.SetFocus()

        # bind
        wx.EVT_CLOSE(self, self.on_close)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_event)
    # ----

    def on_key_event(self, evt):
        key_code = evt.GetKeyCode()
        if key_code == wx.WXK_ESCAPE:  # key = esc
            self.on_close(evt=None)

        evt.Skip()

    def on_close(self, evt):
        """Destroy this frame."""

        self.updateMS(evt=None)
        self.Destroy()

    def onSelect(self, evt):

        self.updateMS(evt=None)
        self.parent.documents.updateComparisonMS(evt=None)
        self.Destroy()

    def onPlot(self, evt):
        """
        Update plot with currently selected PCs
        """
        self.output = {'spectrum_1': [self.document1_value.GetStringSelection(),
                                      self.msSpectrum1_value.GetStringSelection()],
                       'spectrum_2': [self.document2_value.GetStringSelection(),
                                      self.msSpectrum2_value.GetStringSelection()]}

        self.updateMS(evt=None)
        self.parent.documents.updateComparisonMS(evt=None)

    def make_gui(self):

        # make panel
        panel = self.make_panel()

        # pack element
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(panel, 1, wx.EXPAND, 5)

        # fit layout
        self.mainSizer.Fit(self)
        self.SetSizer(self.mainSizer)

    def make_panel(self):

        panel = wx.Panel(self, -1, size=(-1, -1))
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        ms1_staticBox = makeStaticBox(panel, "Mass spectrum - 1", size=(-1, -1), color=wx.BLACK)
        ms1_staticBox.SetSize((-1, -1))
        ms1_box_sizer = wx.StaticBoxSizer(ms1_staticBox, wx.HORIZONTAL)

        ms2_staticBox = makeStaticBox(panel, "Mass spectrum - 2", size=(-1, -1), color=wx.BLACK)
        ms2_staticBox.SetSize((-1, -1))
        ms2_box_sizer = wx.StaticBoxSizer(ms2_staticBox, wx.HORIZONTAL)

        msSpectrum1_transparency_label = wx.StaticText(panel, -1, "Transparency:")
        msSpectrum1_lineStyle_label = wx.StaticText(panel, -1, "Line style:")

        document2_label = wx.StaticText(panel, -1, "Document:")
        msSpectrum2_spectrum_label = wx.StaticText(panel, -1, "Spectrum:")
        msSpectrum2_color_label = wx.StaticText(panel, -1, "Color:")
        msSpectrum2_transparency_label = wx.StaticText(panel, -1, "Transparency:")
        msSpectrum2_lineStyle_label = wx.StaticText(panel, -1, "Line style:")

        # check document list
        document_1, spectrum_1, spectrum_list_1, document_2, spectrum_2, spectrum_list_2 = self._check_spectrum_list()

        # MS 1
        document1_label = wx.StaticText(panel, -1, "Document:")
        self.document1_value = wx.ComboBox(panel, ID_compareMS_MS_1,
                                           choices=self.document_list,
                                           style=wx.CB_READONLY)
        self.document1_value.SetStringSelection(document_1)

        msSpectrum1_spectrum_label = wx.StaticText(panel, -1, "Spectrum:")
        self.msSpectrum1_value = wx.ComboBox(panel, wx.ID_ANY,
                                             choices=spectrum_list_1,
                                             style=wx.CB_READONLY)
        self.msSpectrum1_value.SetStringSelection(spectrum_1)

        label1_label = wx.StaticText(panel, -1, "Label:")
        self.label1_value = wx.TextCtrl(panel, -1, "")

        msSpectrum1_color_label = wx.StaticText(panel, -1, "Color:")
        self.msSpectrum1_colorBtn = wx.Button(panel, wx.ID_ANY, "", wx.DefaultPosition,
                                              wx.Size(26, 26), 0)
        self.msSpectrum1_colorBtn.SetBackgroundColour(convertRGB1to255(self.config.lineColour_MS1))

        self.msSpectrum1_transparency = wx.SpinCtrlDouble(panel, -1,
                                                          value=str(self.config.lineTransparency_MS1 * 100),
                                                          min=0, max=100, initial=self.config.lineTransparency_MS1 * 100,
                                                          inc=10, size=(90, -1))

        self.msSpectrum1_lineStyle_value = wx.ComboBox(panel, choices=self.config.lineStylesList,
                                                       style=wx.CB_READONLY)
        self.msSpectrum1_lineStyle_value.SetStringSelection(self.config.lineStyle_MS1)

        # MS 2
        self.document2_value = wx.ComboBox(panel, ID_compareMS_MS_2,
                                           choices=self.document_list,
                                           style=wx.CB_READONLY)
        self.document2_value.SetStringSelection(document_2)

        self.msSpectrum2_value = wx.ComboBox(panel, wx.ID_ANY,
                                             choices=spectrum_list_2,
                                             style=wx.CB_READONLY)
        self.msSpectrum2_value.SetStringSelection(spectrum_2)

        label2_label = wx.StaticText(panel, -1, "Label:")
        self.label2_value = wx.TextCtrl(panel, -1, "")

        self.msSpectrum2_colorBtn = wx.Button(panel, wx.ID_ANY,
                                              "", wx.DefaultPosition,
                                              wx.Size(26, 26), 0)
        self.msSpectrum2_colorBtn.SetBackgroundColour(convertRGB1to255(self.config.lineColour_MS2))

        self.msSpectrum2_transparency = wx.SpinCtrlDouble(panel, -1,
                                                          value=str(self.config.lineTransparency_MS1 * 100),
                                                          min=0, max=100, initial=self.config.lineTransparency_MS1 * 100,
                                                          inc=10, size=(90, -1))

        self.msSpectrum2_lineStyle_value = wx.ComboBox(panel, choices=self.config.lineStylesList,
                                                       style=wx.CB_READONLY)
        self.msSpectrum2_lineStyle_value.SetStringSelection(self.config.lineStyle_MS2)

        # Processing
        processing_staticBox = makeStaticBox(panel, "Processing",
                                             size=(-1, -1), color=wx.BLACK)
        processing_staticBox.SetSize((-1, -1))
        processing_box_sizer = wx.StaticBoxSizer(processing_staticBox, wx.HORIZONTAL)

        self.preprocess_check = makeCheckbox(panel, "Preprocess")
        self.preprocess_check.SetValue(self.config.compare_massSpectrumParams['preprocess'])
        self.preprocess_tip = makeSuperTip(self.preprocess_check, delay=7, **self.help.compareMS_preprocess)

        self.normalize_check = makeCheckbox(panel, "Normalize")
        self.normalize_check.SetValue(self.config.compare_massSpectrumParams['normalize'])

        self.inverse_check = makeCheckbox(panel, "Inverse")
        self.inverse_check.SetValue(self.config.compare_massSpectrumParams['inverse'])

        self.subtract_check = makeCheckbox(panel, "Subtract")
        self.subtract_check.SetValue(self.config.compare_massSpectrumParams['subtract'])

        settings_label = wx.StaticText(panel, wx.ID_ANY, "Settings:")
        self.settingsBtn = wx.BitmapButton(panel, ID_extraSettings_plot1D,
                                           self.icons.iconsLib['panel_plot1D_16'],
                                           size=(26, 26),
                                           style=wx.BORDER_DEFAULT | wx.ALIGN_CENTER_VERTICAL)
        self.settingsBtn.SetBackgroundColour((240, 240, 240))
        self.settingsBtn_tip = makeSuperTip(self.settingsBtn, delay=7, **self.help.compareMS_open_plot1D_settings)

        self.legendBtn = wx.BitmapButton(panel, ID_extraSettings_legend,
                                         self.icons.iconsLib['panel_legend_16'],
                                         size=(26, 26),
                                         style=wx.BORDER_DEFAULT | wx.ALIGN_CENTER_VERTICAL)
        self.legendBtn.SetBackgroundColour((240, 240, 240))
        self.legendBtn_tip = makeSuperTip(self.legendBtn, delay=7, **self.help.compareMS_open_legend_settings)

        self.processingBtn = wx.BitmapButton(panel, ID_processSettings_MS,
                                             self.icons.iconsLib['process_ms_16'],
                                             size=(26, 26),
                                             style=wx.BORDER_DEFAULT | wx.ALIGN_CENTER_VERTICAL)
        self.processingBtn.SetBackgroundColour((240, 240, 240))
        self.processingBtn_tip = makeSuperTip(self.processingBtn, delay=7, **
                                              self.help.compareMS_open_processMS_settings)

        horizontal_line_1 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_2 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        self.selectBtn = wx.Button(panel, wx.ID_OK, "Select", size=(-1, 22))
        self.plotBtn = wx.Button(panel, wx.ID_OK, "Update", size=(-1, 22))
        self.cancelBtn = wx.Button(panel, wx.ID_OK, "Cancel", size=(-1, 22))

        self.document1_value.Bind(wx.EVT_COMBOBOX, self.updateGUI)
        self.document2_value.Bind(wx.EVT_COMBOBOX, self.updateGUI)

        self.msSpectrum1_value.Bind(wx.EVT_COMBOBOX, self.updateMS)
        self.msSpectrum2_value.Bind(wx.EVT_COMBOBOX, self.updateMS)
        self.preprocess_check.Bind(wx.EVT_CHECKBOX, self.updateMS)
        self.normalize_check.Bind(wx.EVT_CHECKBOX, self.updateMS)
        self.inverse_check.Bind(wx.EVT_CHECKBOX, self.updateMS)
        self.subtract_check.Bind(wx.EVT_CHECKBOX, self.updateMS)
        self.label1_value.Bind(wx.EVT_TEXT, self.updateMS)
        self.label2_value.Bind(wx.EVT_TEXT, self.updateMS)

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
        self.cancelBtn.Bind(wx.EVT_BUTTON, self.on_close)

        self.settingsBtn.Bind(wx.EVT_BUTTON, self.presenter.view.onPlotParameters)
        self.legendBtn.Bind(wx.EVT_BUTTON, self.presenter.view.onPlotParameters)
        self.processingBtn.Bind(wx.EVT_BUTTON, self.presenter.view.onProcessParameters)

        GRIDBAG_VSPACE = 7
        GRIDBAG_HSPACE = 5

        # button grid
        btn_grid = wx.GridBagSizer(GRIDBAG_VSPACE, GRIDBAG_HSPACE)
        y = 0
        btn_grid.Add(self.settingsBtn, (y, 0), wx.GBSpan(1, 1),
                     flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        btn_grid.Add(self.legendBtn, (y, 1), wx.GBSpan(1, 1),
                     flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        btn_grid.Add(self.processingBtn, (y, 2), wx.GBSpan(1, 1),
                     flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)

        # pack elements
        ms1_grid = wx.GridBagSizer(2, 2)
        y = 0
        ms1_grid.Add(document1_label, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        ms1_grid.Add(self.document1_value, (y, 1), wx.GBSpan(1, 6), flag=wx.EXPAND)
        y = y + 1
        ms1_grid.Add(msSpectrum1_spectrum_label, (y, 0), wx.GBSpan(
            1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        ms1_grid.Add(self.msSpectrum1_value, (y, 1), wx.GBSpan(1, 6), flag=wx.EXPAND)
        y = y + 1
        ms1_grid.Add(label1_label, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        ms1_grid.Add(self.label1_value, (y, 1), wx.GBSpan(1, 6), flag=wx.EXPAND)
        y = y + 1
        ms1_grid.Add(msSpectrum1_color_label, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        ms1_grid.Add(self.msSpectrum1_colorBtn, (y, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        ms1_grid.Add(msSpectrum1_transparency_label, (y, 2), wx.GBSpan(
            1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        ms1_grid.Add(self.msSpectrum1_transparency, (y, 3), wx.GBSpan(
            1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        ms1_grid.Add(msSpectrum1_lineStyle_label, (y, 4), wx.GBSpan(
            1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        ms1_grid.Add(self.msSpectrum1_lineStyle_value, (y, 5), wx.GBSpan(
            1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)

        ms1_box_sizer.Add(ms1_grid, 0, wx.EXPAND, 10)

        ms2_grid = wx.GridBagSizer(2, 2)
        y = 0
        ms2_grid.Add(document2_label, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        ms2_grid.Add(self.document2_value, (y, 1), wx.GBSpan(1, 6), flag=wx.EXPAND)
        y = y + 1
        ms2_grid.Add(msSpectrum2_spectrum_label, (y, 0), wx.GBSpan(
            1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        ms2_grid.Add(self.msSpectrum2_value, (y, 1), wx.GBSpan(1, 6), flag=wx.EXPAND)
        y = y + 1
        ms2_grid.Add(label2_label, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        ms2_grid.Add(self.label2_value, (y, 1), wx.GBSpan(1, 6), flag=wx.EXPAND)
        y = y + 1
        ms2_grid.Add(msSpectrum2_color_label, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        ms2_grid.Add(self.msSpectrum2_colorBtn, (y, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        ms2_grid.Add(msSpectrum2_transparency_label, (y, 2), wx.GBSpan(
            1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        ms2_grid.Add(self.msSpectrum2_transparency, (y, 3), wx.GBSpan(
            1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        ms2_grid.Add(msSpectrum2_lineStyle_label, (y, 4), wx.GBSpan(
            1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        ms2_grid.Add(self.msSpectrum2_lineStyle_value, (y, 5), wx.GBSpan(
            1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        ms2_box_sizer.Add(ms2_grid, 0, wx.EXPAND, 10)

        processing_grid = wx.GridBagSizer(2, 2)
        y = 0
        processing_grid.Add(self.preprocess_check, (y, 0), wx.GBSpan(1, 1),
                            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        processing_grid.Add(self.normalize_check, (y, 1), wx.GBSpan(1, 1),
                            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        processing_grid.Add(self.inverse_check, (y, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        processing_grid.Add(self.subtract_check, (y, 3), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        processing_box_sizer.Add(processing_grid, 0, wx.EXPAND, 10)

        grid = wx.GridBagSizer(GRIDBAG_VSPACE, GRIDBAG_HSPACE)
        y = 0
        grid.Add(ms1_box_sizer, (y, 0), wx.GBSpan(1, 6), flag=wx.EXPAND)
        y = y + 1
        grid.Add(ms2_box_sizer, (y, 0), wx.GBSpan(1, 6), flag=wx.EXPAND)
        y = y + 1
        grid.Add(processing_box_sizer, (y, 0), wx.GBSpan(1, 6), flag=wx.EXPAND)
        y = y + 1
        grid.Add(horizontal_line_1, (y, 0), wx.GBSpan(1, 6), flag=wx.EXPAND)
        y = y + 1
        grid.Add(settings_label, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(btn_grid, (y, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        y = y + 1
        grid.Add(horizontal_line_2, (y, 0), wx.GBSpan(1, 6), flag=wx.EXPAND)
        y = y + 1
        grid.Add(self.selectBtn, (y, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(self.plotBtn, (y, 3), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(self.cancelBtn, (y, 4), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)

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
            spectrum_list_1 = natsorted(self.kwargs['document_spectrum_list'][document_1])
            self.msSpectrum1_value.SetItems(spectrum_list_1)
            self.msSpectrum1_value.SetStringSelection(spectrum_list_1[0])

        elif evtID == ID_compareMS_MS_2:
            document_2 = self.document2_value.GetStringSelection()
            spectrum_list_2 = natsorted(self.kwargs['document_spectrum_list'][document_2])
            self.msSpectrum2_value.SetItems(spectrum_list_2)
            self.msSpectrum2_value.SetStringSelection(spectrum_list_2[0])

    def updateMS(self, evt):
        self.config.compare_massSpectrum = [self.msSpectrum1_value.GetStringSelection(),
                                            self.msSpectrum2_value.GetStringSelection()]
        self.config.lineTransparency_MS1 = str2num(self.msSpectrum1_transparency.GetValue()) / 100
        self.config.lineStyle_MS1 = self.msSpectrum1_lineStyle_value.GetStringSelection()

        self.config.lineTransparency_MS2 = str2num(self.msSpectrum2_transparency.GetValue()) / 100
        self.config.lineStyle_MS2 = self.msSpectrum2_lineStyle_value.GetStringSelection()

        self.config.compare_massSpectrumParams['preprocess'] = self.preprocess_check.GetValue()
        self.config.compare_massSpectrumParams['inverse'] = self.inverse_check.GetValue()
        self.config.compare_massSpectrumParams['normalize'] = self.normalize_check.GetValue()
        self.config.compare_massSpectrumParams['subtract'] = self.subtract_check.GetValue()

        label_1 = self.label1_value.GetValue()
        if label_1 == "":
            label_1 = self.msSpectrum1_value.GetStringSelection()
        label_2 = self.label2_value.GetValue()
        if label_2 == "":
            label_2 = self.msSpectrum2_value.GetStringSelection()
        self.config.compare_massSpectrumParams['legend'] = [label_1, label_2]

        if evt is not None:
            evt.Skip()

    def onUpdateMS1color(self, evt):
        dlg = DialogColorPicker(self, self.config.customColors)
        if dlg.ShowModal() == "ok":
            color_255, color_1, __ = dlg.GetChosenColour()
            self.config.customColors = dlg.GetCustomColours()
        else:
            return
        self.config.lineColour_MS1 = color_1
        self.msSpectrum1_colorBtn.SetBackgroundColour(color_255)

    def onUpdateMS2color(self, evt):
        dlg = DialogColorPicker(self, self.config.customColors)
        if dlg.ShowModal() == "ok":
            color_255, color_1, __ = dlg.GetChosenColour()
            self.config.customColors = dlg.GetCustomColours()
        else:
            return
        self.config.lineColour_MS2 = color_1
        self.msSpectrum2_colorBtn.SetBackgroundColour(color_255)

    def error_handler(self, flag=None):
        """
        Enable/disable item if error msg occured
        """
        if flag is None:
            return

        if flag == "subtract":
            self.subtract_check.SetValue(False)

        if flag == "normalize":
            self.normalize_check.SetValue(False)

    def _check_spectrum_list(self):

        spectrum_list_1 = natsorted(self.kwargs['document_spectrum_list'][self.document_list[0]])
        if len(spectrum_list_1) >= 2:
            return (self.document_list[0], spectrum_list_1[0], spectrum_list_1,
                    self.document_list[0], spectrum_list_1[1], spectrum_list_1)
        else:
            spectrum_list_2 = natsorted(self.kwargs['document_spectrum_list'][self.document_list[1]])
            return (self.document_list[0], spectrum_list_1[0], spectrum_list_1,
                    self.document_list[1], spectrum_list_2[0], spectrum_list_2)
