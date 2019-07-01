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
import logging
from copy import deepcopy

import processing.spectra as pr_spectra
import wx
from gui_elements.dialog_color_picker import DialogColorPicker
from ids import ID_compareMS_MS_1
from ids import ID_compareMS_MS_2
from ids import ID_extraSettings_legend
from ids import ID_extraSettings_plot1D
from ids import ID_plotPanel_resize
from ids import ID_plots_customisePlot
from ids import ID_processSettings_MS
from natsort import natsorted
from styles import makeCheckbox
from styles import makeMenuItem
from styles import makeStaticBox
from utils.color import convertRGB1to255
from utils.converters import str2num
from utils.screen import calculate_window_size
from visuals import mpl_plots

logger = logging.getLogger('origami')


class panel_signal_comparison_viewer(wx.MiniFrame):
    """
    Simple GUI to select mass spectra to compare
    """

    def __init__(self, parent, presenter, config, icons, **kwargs):
        wx.MiniFrame.__init__(
            self, parent, -1, 'Compare mass spectra...', size=(-1, -1),
            style=wx.DEFAULT_FRAME_STYLE & ~wx.RESIZE_BORDER,
        )

        self.parent = parent
        self.presenter = presenter
        self.config = config
        self.icons = icons

        self.kwargs = kwargs
        self.current_document = self.kwargs['current_document']
        self.document_list = self.kwargs['document_list']

        self.compare_massSpectrum = []

        self.data_handling = presenter.data_handling
        self.data_processing = presenter.data_processing
        self.panel_plot = self.presenter.view.panelPlots

        self.displaysize = wx.GetDisplaySize()
        self.displayRes = (wx.GetDisplayPPI())
        self.figsizeX = (self.displaysize[0] - 320) / self.displayRes[0]

        # make gui items
        self.make_gui()
        self.update_spectrum(None)
        try:
            self.on_plot(None)
        except IndexError as err:
            print(err)

        # bind
        wx.EVT_CLOSE(self, self.on_close)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_event)
        self.Bind(wx.EVT_CONTEXT_MENU, self.on_right_click)

    def on_right_click(self, evt):

        self.Bind(wx.EVT_MENU, self.on_resize_check, id=ID_plotPanel_resize)
        self.Bind(wx.EVT_MENU, self.on_customise_plot, id=ID_plots_customisePlot)

        menu = wx.Menu()
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_plots_customisePlot,
                text='Customise plot...',
                bitmap=self.icons.iconsLib['change_xlabels_16'],
            ),
        )
        menu.AppendSeparator()
        self.resize_plot_check = menu.AppendCheckItem(
            ID_plotPanel_resize,
            'Resize on saving',
            help='',
        )
        self.resize_plot_check.Check(self.config.resize)
#         menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveMZDTImage, text=saveImageLabel,
#                                      bitmap=self.icons.iconsLib['save16']))
#         menu.AppendSeparator()
#         menu.AppendItem(makeMenuItem(parent=menu, id=ID_clearPlot_MZDT, text="Clear plot",
#                                      bitmap=self.icons.iconsLib['clear_16']))

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def on_key_event(self, evt):
        key_code = evt.GetKeyCode()
        if key_code == wx.WXK_ESCAPE:  # key = esc
            self.on_close(evt=None)

        evt.Skip()

    def on_close(self, evt):
        """Destroy this frame."""

        self.update_spectrum(evt=None)
        self.Destroy()

    def on_resize_check(self, evt):
        self.panel_plot.on_resize_check(None)

    def on_customise_plot(self, evt):
        kwargs = dict(plot='MS...', plot_obj=self.plot_window)
        self.panel_plot.customisePlot(None, **kwargs)

    def on_ok(self, evt):

        self.update_spectrum(evt=None)
        self.Destroy()

    def make_gui(self):

        # make panel
        panel = wx.Panel(self, -1, size=(-1, -1), name='main')

        settings_panel = self.make_settings_panel(panel)
        plot_panel = self.make_plot_panel(panel)

        # pack element
        self.main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.main_sizer.Add(settings_panel, 0, wx.EXPAND, 0)
        self.main_sizer.Add(plot_panel, 0, wx.EXPAND, 0)

        # fit layout
        self.main_sizer.Fit(panel)
        self.SetSize(calculate_window_size(self.displaysize, 0.8))
        self.SetSizer(self.main_sizer)
        self.Layout()
        self.CentreOnScreen()
        self.SetFocus()

    def make_settings_panel(self, split_panel):
        panel = wx.Panel(split_panel, -1, size=(-1, -1), name='settings')

        ms1_staticBox = makeStaticBox(panel, 'Spectrum - 1', size=(-1, -1), color=wx.BLACK)
        ms1_staticBox.SetSize((-1, -1))
        ms1_box_sizer = wx.StaticBoxSizer(ms1_staticBox, wx.HORIZONTAL)

        ms2_staticBox = makeStaticBox(panel, 'Spectrum - 2', size=(-1, -1), color=wx.BLACK)
        ms2_staticBox.SetSize((-1, -1))
        ms2_box_sizer = wx.StaticBoxSizer(ms2_staticBox, wx.HORIZONTAL)

        # check document list
        document_1, spectrum_1, spectrum_list_1, document_2, spectrum_2, spectrum_list_2 = self._check_spectrum_list()

        # MS 1
        spectrum_1_document_label = wx.StaticText(panel, -1, 'Document:')
        self.spectrum_1_document_value = wx.ComboBox(
            panel, ID_compareMS_MS_1,
            choices=self.document_list,
            style=wx.CB_READONLY,
        )
        self.spectrum_1_document_value.SetStringSelection(document_1)

        spectrum_1_spectrum_label = wx.StaticText(panel, -1, 'Spectrum:')
        self.spectrum_1_spectrum_value = wx.ComboBox(
            panel, wx.ID_ANY,
            choices=spectrum_list_1,
            style=wx.CB_READONLY,
            name='spectrum_1',
        )
        self.spectrum_1_spectrum_value.SetStringSelection(spectrum_1)

        spectrum_1_label_label = wx.StaticText(panel, -1, 'Label:')
        self.spectrum_1_label_value = wx.TextCtrl(panel, -1, '', name='label_1')

        spectrum_1_color_label = wx.StaticText(panel, -1, 'Color:')
        self.spectrum_1_colorBtn = wx.Button(panel, size=wx.Size(26, 26), name='color_1')
        self.spectrum_1_colorBtn.SetBackgroundColour(convertRGB1to255(self.config.lineColour_MS1))

        spectrum_1_transparency_label = wx.StaticText(panel, -1, 'Transparency:')
        self.spectrum_1_transparency = wx.SpinCtrlDouble(
            panel, -1,
            value=str(self.config.lineTransparency_MS1 * 100),
            min=0, max=100,
            initial=self.config.lineTransparency_MS1 * 100,
            inc=10, size=(90, -1),
            name='transparency_1',
        )

        spectrum_1_lineStyle_label = wx.StaticText(panel, -1, 'Line style:')
        self.spectrum_1_lineStyle_value = wx.ComboBox(
            panel, choices=self.config.lineStylesList,
            style=wx.CB_READONLY,
            name='style_1',
        )
        self.spectrum_1_lineStyle_value.SetStringSelection(self.config.lineStyle_MS1)

        # MS 2
        document2_label = wx.StaticText(panel, -1, 'Document:')
        self.spectrum_2_document_value = wx.ComboBox(
            panel, ID_compareMS_MS_2,
            choices=self.document_list,
            style=wx.CB_READONLY,
        )
        self.spectrum_2_document_value.SetStringSelection(document_2)

        spectrum_2_spectrum_label = wx.StaticText(panel, -1, 'Spectrum:')
        self.spectrum_2_spectrum_value = wx.ComboBox(
            panel, wx.ID_ANY,
            choices=spectrum_list_2,
            style=wx.CB_READONLY,
            name='spectrum_2',
        )
        self.spectrum_2_spectrum_value.SetStringSelection(spectrum_2)

        spectrum_2_label_label = wx.StaticText(panel, -1, 'Label:')
        self.spectrum_2_label_value = wx.TextCtrl(panel, -1, '', name='label_2')

        spectrum_2_color_label = wx.StaticText(panel, -1, 'Color:')
        self.spectrum_2_colorBtn = wx.Button(panel, size=wx.Size(26, 26), name='color_2')
        self.spectrum_2_colorBtn.SetBackgroundColour(convertRGB1to255(self.config.lineColour_MS2))

        spectrum_2_transparency_label = wx.StaticText(panel, -1, 'Transparency:')
        self.spectrum_2_transparency = wx.SpinCtrlDouble(
            panel, -1,
            value=str(self.config.lineTransparency_MS1 * 100),
            min=0, max=100,
            initial=self.config.lineTransparency_MS1 * 100,
            inc=10, size=(90, -1),
            name='transparency_2',
        )

        spectrum_2_lineStyle_label = wx.StaticText(panel, -1, 'Line style:')
        self.spectrum_2_lineStyle_value = wx.ComboBox(
            panel, choices=self.config.lineStylesList,
            style=wx.CB_READONLY,
            name='style_2',
        )
        self.spectrum_2_lineStyle_value.SetStringSelection(self.config.lineStyle_MS2)

        # Processing
        processing_staticBox = makeStaticBox(
            panel, 'Processing',
            size=(-1, -1), color=wx.BLACK,
        )
        processing_staticBox.SetSize((-1, -1))
        processing_box_sizer = wx.StaticBoxSizer(processing_staticBox, wx.HORIZONTAL)

        self.preprocess_check = makeCheckbox(panel, 'Preprocess')
        self.preprocess_check.SetValue(self.config.compare_massSpectrumParams['preprocess'])

        self.normalize_check = makeCheckbox(panel, 'Normalize')
        self.normalize_check.SetValue(self.config.compare_massSpectrumParams['normalize'])

        self.inverse_check = makeCheckbox(panel, 'Inverse')
        self.inverse_check.SetValue(self.config.compare_massSpectrumParams['inverse'])

        self.subtract_check = makeCheckbox(panel, 'Subtract')
        self.subtract_check.SetValue(self.config.compare_massSpectrumParams['subtract'])

        settings_label = wx.StaticText(panel, wx.ID_ANY, 'Settings:')
        self.settings_btn = wx.BitmapButton(
            panel, ID_extraSettings_plot1D,
            self.icons.iconsLib['panel_plot1D_16'],
            size=(26, 26),
            style=wx.BORDER_DEFAULT | wx.ALIGN_CENTER_VERTICAL,
        )
        self.settings_btn.SetBackgroundColour((240, 240, 240))

        self.legend_btn = wx.BitmapButton(
            panel, ID_extraSettings_legend,
            self.icons.iconsLib['panel_legend_16'],
            size=(26, 26),
            style=wx.BORDER_DEFAULT | wx.ALIGN_CENTER_VERTICAL,
        )
        self.legend_btn.SetBackgroundColour((240, 240, 240))

        self.process_btn = wx.BitmapButton(
            panel, ID_processSettings_MS,
            self.icons.iconsLib['process_ms_16'],
            size=(26, 26),
            style=wx.BORDER_DEFAULT | wx.ALIGN_CENTER_VERTICAL,
        )
        self.process_btn.SetBackgroundColour((240, 240, 240))

        horizontal_line_1 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_2 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        self.plot_btn = wx.Button(panel, wx.ID_OK, 'Full replot', size=(-1, 22))
        self.cancel_btn = wx.Button(panel, wx.ID_OK, 'Cancel', size=(-1, 22))

        self.spectrum_1_document_value.Bind(wx.EVT_COMBOBOX, self.update_gui)
        self.spectrum_2_document_value.Bind(wx.EVT_COMBOBOX, self.update_gui)

        self.spectrum_1_spectrum_value.Bind(wx.EVT_COMBOBOX, self.update_spectrum)
        self.spectrum_2_spectrum_value.Bind(wx.EVT_COMBOBOX, self.update_spectrum)
        self.spectrum_1_spectrum_value.Bind(wx.EVT_COMBOBOX, self.on_plot_update_data)
        self.spectrum_2_spectrum_value.Bind(wx.EVT_COMBOBOX, self.on_plot_update_data)

        self.preprocess_check.Bind(wx.EVT_CHECKBOX, self.update_spectrum)
        self.normalize_check.Bind(wx.EVT_CHECKBOX, self.update_spectrum)
        self.inverse_check.Bind(wx.EVT_CHECKBOX, self.update_spectrum)
        self.subtract_check.Bind(wx.EVT_CHECKBOX, self.update_spectrum)
#
#         self.spectrum_1_label_value.Bind(wx.EVT_TEXT, self.update_spectrum)
#         self.spectrum_2_label_value.Bind(wx.EVT_TEXT, self.update_spectrum)

        self.spectrum_1_label_value.Bind(wx.EVT_TEXT, self.on_plot_update_label)
        self.spectrum_2_label_value.Bind(wx.EVT_TEXT, self.on_plot_update_label)

        self.spectrum_1_colorBtn.Bind(wx.EVT_BUTTON, self.on_update_color)
        self.spectrum_2_colorBtn.Bind(wx.EVT_BUTTON, self.on_update_color)

        self.spectrum_1_transparency.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.spectrum_2_transparency.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.spectrum_1_lineStyle_value.Bind(wx.EVT_COMBOBOX, self.on_apply)
        self.spectrum_2_lineStyle_value.Bind(wx.EVT_COMBOBOX, self.on_apply)

        self.preprocess_check.Bind(wx.EVT_CHECKBOX, self.on_plot)
        self.normalize_check.Bind(wx.EVT_CHECKBOX, self.on_plot)
        self.inverse_check.Bind(wx.EVT_CHECKBOX, self.on_plot)
#         self.subtract_check.Bind(wx.EVT_CHECKBOX, self.onPlot)

        self.plot_btn.Bind(wx.EVT_BUTTON, self.on_plot)
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_close)

        self.settings_btn.Bind(wx.EVT_BUTTON, self.presenter.view.onPlotParameters)
        self.legend_btn.Bind(wx.EVT_BUTTON, self.presenter.view.onPlotParameters)
        self.process_btn.Bind(wx.EVT_BUTTON, self.presenter.view.onProcessParameters)

        GRIDBAG_VSPACE = 7
        GRIDBAG_HSPACE = 5

        # button grid
        btn_grid = wx.GridBagSizer(GRIDBAG_VSPACE, GRIDBAG_HSPACE)
        y = 0
        btn_grid.Add(
            self.settings_btn, (y, 0), wx.GBSpan(1, 1),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL,
        )
        btn_grid.Add(
            self.legend_btn, (y, 1), wx.GBSpan(1, 1),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL,
        )
        btn_grid.Add(
            self.process_btn, (y, 2), wx.GBSpan(1, 1),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL,
        )

        # pack elements
        ms1_grid = wx.GridBagSizer(2, 2)
        y = 0
        ms1_grid.Add(spectrum_1_document_label, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        ms1_grid.Add(self.spectrum_1_document_value, (y, 1), wx.GBSpan(1, 6), flag=wx.EXPAND)
        y = y + 1
        ms1_grid.Add(
            spectrum_1_spectrum_label, (y, 0), wx.GBSpan(
                1, 1,
            ), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT,
        )
        ms1_grid.Add(self.spectrum_1_spectrum_value, (y, 1), wx.GBSpan(1, 6), flag=wx.EXPAND)
        y = y + 1
        ms1_grid.Add(spectrum_1_label_label, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        ms1_grid.Add(self.spectrum_1_label_value, (y, 1), wx.GBSpan(1, 6), flag=wx.EXPAND)
        y = y + 1
        ms1_grid.Add(spectrum_1_color_label, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        ms1_grid.Add(self.spectrum_1_colorBtn, (y, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        ms1_grid.Add(
            spectrum_1_transparency_label, (y, 2), wx.GBSpan(
                1, 1,
            ), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT,
        )
        ms1_grid.Add(
            self.spectrum_1_transparency, (y, 3), wx.GBSpan(
                1, 1,
            ), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT,
        )
        ms1_grid.Add(
            spectrum_1_lineStyle_label, (y, 4), wx.GBSpan(
                1, 1,
            ), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT,
        )
        ms1_grid.Add(
            self.spectrum_1_lineStyle_value, (y, 5), wx.GBSpan(
                1, 1,
            ), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT,
        )

        ms1_box_sizer.Add(ms1_grid, 0, wx.EXPAND, 10)

        ms2_grid = wx.GridBagSizer(2, 2)
        y = 0
        ms2_grid.Add(document2_label, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        ms2_grid.Add(self.spectrum_2_document_value, (y, 1), wx.GBSpan(1, 6), flag=wx.EXPAND)
        y = y + 1
        ms2_grid.Add(
            spectrum_2_spectrum_label, (y, 0), wx.GBSpan(
                1, 1,
            ), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT,
        )
        ms2_grid.Add(self.spectrum_2_spectrum_value, (y, 1), wx.GBSpan(1, 6), flag=wx.EXPAND)
        y = y + 1
        ms2_grid.Add(spectrum_2_label_label, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        ms2_grid.Add(self.spectrum_2_label_value, (y, 1), wx.GBSpan(1, 6), flag=wx.EXPAND)
        y = y + 1
        ms2_grid.Add(spectrum_2_color_label, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        ms2_grid.Add(self.spectrum_2_colorBtn, (y, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        ms2_grid.Add(
            spectrum_2_transparency_label, (y, 2), wx.GBSpan(
                1, 1,
            ), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT,
        )
        ms2_grid.Add(
            self.spectrum_2_transparency, (y, 3), wx.GBSpan(
                1, 1,
            ), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT,
        )
        ms2_grid.Add(
            spectrum_2_lineStyle_label, (y, 4), wx.GBSpan(
                1, 1,
            ), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT,
        )
        ms2_grid.Add(
            self.spectrum_2_lineStyle_value, (y, 5), wx.GBSpan(
                1, 1,
            ), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT,
        )
        ms2_box_sizer.Add(ms2_grid, 0, wx.EXPAND, 10)

        processing_grid = wx.GridBagSizer(2, 2)
        y = 0
        processing_grid.Add(
            self.preprocess_check, (y, 0), wx.GBSpan(1, 1),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT,
        )
        processing_grid.Add(
            self.normalize_check, (y, 1), wx.GBSpan(1, 1),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT,
        )
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
        grid.Add(self.plot_btn, (y, 3), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(self.cancel_btn, (y, 4), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 0, wx.EXPAND, 10)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def make_plot_panel(self, split_panel):

        panel = wx.Panel(split_panel, -1, size=(-1, -1), name='plot')
        self.plot_panel = wx.Panel(
            panel, wx.ID_ANY, wx.DefaultPosition,
            wx.DefaultSize, wx.TAB_TRAVERSAL,
        )

        self.plot_window = mpl_plots.plots(
            self.plot_panel,
            figsize=(self.figsizeX, 2),
            config=self.config,
        )

        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(self.plot_window, 1, wx.EXPAND)
        self.plot_panel.SetSizer(box)
        self.plot_panel.Fit()

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.plot_panel, 1, wx.EXPAND, 2)
        # fit layout
        panel.SetSizer(main_sizer)
        main_sizer.Fit(panel)

        return panel

    def update_gui(self, evt):
        evtID = evt.GetId()
        # update document list
        if evtID == ID_compareMS_MS_1:
            document_1 = self.spectrum_1_document_value.GetStringSelection()
            spectrum_list_1 = natsorted(self.kwargs['document_spectrum_list'][document_1])
            self.spectrum_1_spectrum_value.SetItems(spectrum_list_1)
            self.spectrum_1_spectrum_value.SetStringSelection(spectrum_list_1[0])

        elif evtID == ID_compareMS_MS_2:
            document_2 = self.spectrum_2_document_value.GetStringSelection()
            spectrum_list_2 = natsorted(self.kwargs['document_spectrum_list'][document_2])
            self.spectrum_2_spectrum_value.SetItems(spectrum_list_2)
            self.spectrum_2_spectrum_value.SetStringSelection(spectrum_list_2[0])

    def on_apply(self, evt):
        if evt is not None:
            source = evt.GetEventObject().GetName()

        self.config.lineTransparency_MS1 = str2num(self.spectrum_1_transparency.GetValue()) / 100
        self.config.lineStyle_MS1 = self.spectrum_1_lineStyle_value.GetStringSelection()

        self.config.lineTransparency_MS2 = str2num(self.spectrum_2_transparency.GetValue()) / 100
        self.config.lineStyle_MS2 = self.spectrum_2_lineStyle_value.GetStringSelection()

        if evt is not None:
            self.on_plot_update_style(source)

    def update_spectrum(self, evt):
        spectrum_1_choice = [
            self.spectrum_1_document_value.GetStringSelection(),
            self.spectrum_1_spectrum_value.GetStringSelection(),
        ]
        spectrum_2_choice = [
            self.spectrum_2_document_value.GetStringSelection(),
            self.spectrum_2_spectrum_value.GetStringSelection(),
        ]
        self.config.compare_massSpectrum = [spectrum_1_choice, spectrum_2_choice]

        self.config.compare_massSpectrumParams['preprocess'] = self.preprocess_check.GetValue()
        self.config.compare_massSpectrumParams['inverse'] = self.inverse_check.GetValue()
        self.config.compare_massSpectrumParams['normalize'] = self.normalize_check.GetValue()
        self.config.compare_massSpectrumParams['subtract'] = self.subtract_check.GetValue()

        label_1 = self.spectrum_1_label_value.GetValue()
        if label_1 == '':
            label_1 = self.spectrum_1_spectrum_value.GetStringSelection()
        label_2 = self.spectrum_2_label_value.GetValue()
        if label_2 == '':
            label_2 = self.spectrum_2_spectrum_value.GetStringSelection()
        self.config.compare_massSpectrumParams['legend'] = [label_1, label_2]

        self.on_apply(None)

        if evt is not None:
            evt.Skip()

    def on_update_color(self, evt):
        """Update spectrum color"""
        # get object name
        source = evt.GetEventObject().GetName()

        # get color
        dlg = DialogColorPicker(self, self.config.customColors)
        if dlg.ShowModal() == 'ok':
            color_255, color_1, __ = dlg.GetChosenColour()
            self.config.customColors = dlg.GetCustomColours()
        else:
            return

        # assign color
        if source == 'color_1':
            self.config.lineColour_MS1 = color_1
            self.spectrum_1_colorBtn.SetBackgroundColour(color_255)
        elif source == 'color_2':
            self.config.lineColour_MS2 = color_1
            self.spectrum_2_colorBtn.SetBackgroundColour(color_255)

        self.on_plot_update_style(source)

    def error_handler(self, flag=None):
        """
        Enable/disable item if error msg occured
        """
        if flag is None:
            return

        if flag == 'subtract':
            self.subtract_check.SetValue(False)

        if flag == 'normalize':
            self.normalize_check.SetValue(False)

    def _check_spectrum_list(self):

        spectrum_list_1 = natsorted(self.kwargs['document_spectrum_list'][self.document_list[0]])
        if len(spectrum_list_1) >= 2:
            return (
                self.document_list[0], spectrum_list_1[0], spectrum_list_1,
                self.document_list[0], spectrum_list_1[1], spectrum_list_1,
            )
        else:
            spectrum_list_2 = natsorted(self.kwargs['document_spectrum_list'][self.document_list[1]])
            return (
                self.document_list[0], spectrum_list_1[0], spectrum_list_1,
                self.document_list[1], spectrum_list_2[0], spectrum_list_2,
            )

    def on_plot_update_label(self, evt):
        source = evt.GetEventObject().GetName()

#         old_label = self.compare_massSpectrum[index][-1]
#         new_label = self.config.compare_massSpectrumParams['legend'][index]
#
#         print(old_label, new_label)
#         print(source, label_1, label_2)

    def on_process_and_plot_data(self, evt):
        pass
#         for index in range(2):
#             spectrum = self.data_handling.get_spectrum(self.config.compare_massSpectrum[index])
#             xvals = spectrum['xvals']
#             yvals = spectrum['yvals']
#             label = self.config.compare_massSpectrumParams['legend'][index]
#
#             if self.config.compare_massSpectrumParams['normalize']:
#                 yvals = pr_spectra.normalize_1D(yvals)
#
#             if self.config.compare_massSpectrumParams['inverse'] and index == 1:
#                 yvals = -yvals
#
#             self.panel_plot.plot_1D_update_data_by_label(
#                 xvals, yvals, index, label,
#                 plot=None, plot_obj=self.plot_window,
#             )
#
#         spectrum = self.data_handling.get_spectrum(self.config.compare_massSpectrum[0])
#         xvals = spectrum['xvals']
#         yvals = spectrum['yvals']
#         label = self.config.compare_massSpectrumParams['legend'][1]
#
#         self.panel_plot.plot_1D_update_data_by_label(
#             xvals, yvals, 1, label,
#             plot=None, plot_obj=self.plot_window,
#         )

    def on_plot_update_data(self, evt):
        if evt is not None:
            source = evt.GetEventObject().GetName()

        self.update_spectrum(evt=None)

        index = self._get_dataset_index(source)

        spectrum = self.data_handling.get_spectrum(self.config.compare_massSpectrum[index])
        xvals = spectrum['xvals']
        yvals = spectrum['yvals']
        label = self.config.compare_massSpectrumParams['legend'][index]

        if self.config.compare_massSpectrumParams['normalize']:
            yvals = pr_spectra.normalize_1D(yvals)

        if self.config.compare_massSpectrumParams['inverse'] and index == 1:
            yvals = -yvals

        self.panel_plot.plot_1D_update_data_by_label(
            xvals, yvals, index, label,
            plot=None, plot_obj=self.plot_window,
        )

        self._update_local_plot_information()
        if evt is not None:
            evt.Skip()

    def on_plot_update_style(self, source):

        kwargs = dict()
        index = self._get_dataset_index(source)

        if source.endswith('_1'):
            kwargs['color'] = self.config.lineColour_MS1
            kwargs['line_style'] = self.config.lineStyle_MS1
            kwargs['transparency'] = self.config.lineTransparency_MS1
        elif source.endswith('_2'):
            kwargs['color'] = self.config.lineColour_MS2
            kwargs['line_style'] = self.config.lineStyle_MS2
            kwargs['transparency'] = self.config.lineTransparency_MS2

        self.panel_plot.plot_1D_update_style_by_label(index, plot=None, plot_obj=self.plot_window, **kwargs)

    def on_plot(self, evt):
        self.update_spectrum(None)

        spectrum_1 = self.data_handling.get_spectrum(self.config.compare_massSpectrum[0][:2])
        spectrum_2 = self.data_handling.get_spectrum(self.config.compare_massSpectrum[1][:2])

        xvals_1 = spectrum_1['xvals']
        yvals_1 = spectrum_1['yvals']

        xvals_2 = spectrum_2['xvals']
        yvals_2 = spectrum_2['yvals']

        if self.config.compare_massSpectrumParams['normalize']:
            yvals_1 = pr_spectra.normalize_1D(yvals_1)
            yvals_2 = pr_spectra.normalize_1D(yvals_2)

        if self.config.compare_massSpectrumParams['inverse']:
            yvals_2 = -yvals_2

        self.panel_plot.plot_compare_spectra(xvals_1, xvals_2, yvals_1, yvals_2, plot=None, plot_obj=self.plot_window)

        self._update_local_plot_information()

    @staticmethod
    def _get_dataset_index(source):
        if source.endswith('_1'):
            index = 0
        elif source.endswith('_2'):
            index = 1

        return index

    def _update_local_plot_information(self):
        # update local information about the plots
        spectrum_1_choice = deepcopy(self.config.compare_massSpectrum[0])
        spectrum_1_choice.append(self.config.compare_massSpectrumParams['legend'][0])
        spectrum_2_choice = deepcopy(self.config.compare_massSpectrum[1])
        spectrum_2_choice.append(self.config.compare_massSpectrumParams['legend'][1])

        self.compare_massSpectrum = [spectrum_1_choice, spectrum_2_choice]
