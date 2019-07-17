# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import logging

import wx
from styles import makeCheckbox
from styles import makeMenuItem
from styles import makeTooltip
from styles import validator
from utils.converters import str2int
from utils.converters import str2num
from utils.exceptions import MessageError
from utils.screen import calculate_window_size
from visuals import mpl_plots
logger = logging.getLogger('origami')

TEXTCTRL_SIZE = (60, -1)
BTN_SIZE = (100, 22)

# TODO: Migrate all UniDec code to widgets.unidec module
# TODO: Update to latest version of UniDec
# TODO: Remove UniDec plot panels from the main window and move them to here
# TODO: Improve layout and add new functionality


class PanelProcessUniDec(wx.MiniFrame):
    """Peak picking panel"""

    def __init__(self, parent, presenter, config, icons, **kwargs):
        """Initlize panel"""
        wx.MiniFrame.__init__(
            self, parent, -1, 'UniDec...', size=(-1, -1),
            style=wx.DEFAULT_FRAME_STYLE & ~
            (wx.RESIZE_BORDER | wx.MAXIMIZE_BOX),
        )
        self.view = parent
        self.presenter = presenter
        self.document_tree = self.view.panelDocuments.documents
        self.panel_plot = self.view.panelPlots

        self.ionPanel = self.view.panelMultipleIons
        self.ionList = self.ionPanel.peaklist

        self.config = config
        self.icons = icons

        self.data_processing = presenter.data_processing
        self.data_handling = presenter.data_handling

        self._display_size = wx.GetDisplaySize()
        self._display_resolution = wx.ScreenDC().GetPPI()
        self._window_size = calculate_window_size(self._display_size, [0.9, 0.9])

        # initilize gui
        self.make_gui()
        self.on_toggle_controls(None)
        self.CentreOnScreen()
        self.SetFocus()

        # setup kwargs
        self.document = kwargs.pop('document', None)
        self.document_title = kwargs.pop('document_title', None)
        self.dataset_name = kwargs.pop('dataset_name', None)
        self.mz_data = kwargs.pop('mz_data', None)

        # bind events
        wx.EVT_CLOSE(self, self.on_close)
        self.Bind(wx.EVT_CONTEXT_MENU, self.on_right_click)

    def on_right_click(self, evt):

        menu = wx.Menu()
        save_figure_menu_item = makeMenuItem(
            menu, id=wx.ID_ANY,
            text='Save figure as...',
            bitmap=self.icons.iconsLib['save16'],
        )
        menu.AppendItem(save_figure_menu_item)
        self.Bind(wx.EVT_MENU, self.on_save_figure, save_figure_menu_item)

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def on_close(self, evt):
        """Destroy this frame."""
        self.Destroy()

    def make_gui(self):
        """Make miniframe"""
        panel = wx.Panel(self, -1, size=(-1, -1), name='main')

        self.settings_buttons = self.make_buttons_settings_panel(panel)
        self.settings_preprocess = self.make_preprocess_settings_panel(panel)
        self.settings_unidec = self.make_unidec_settings_panel(panel)
        self.settings_peaks = self.make_peaks_settings_panel(panel)
        self.settings_visual = self.make_visualise_settings_panel(panel)

        # pack settings panel
        self.settings_sizer = wx.BoxSizer(wx.VERTICAL)
        self.settings_sizer.Add(self.settings_buttons, 0, wx.EXPAND)
        self.settings_sizer.Add(self.settings_preprocess, 0, wx.EXPAND)
        self.settings_sizer.Add(self.settings_unidec, 0, wx.EXPAND)
        self.settings_sizer.Add(self.settings_peaks, 0, wx.EXPAND)
        self.settings_sizer.Add(self.settings_visual, 0, wx.EXPAND)
        self.settings_sizer.Fit(panel)

        self._settings_panel_size = self.settings_sizer.GetSize()

        self.plot_panel = self.make_plot_panel(panel)

        # pack element
        self.main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.main_sizer.Add(self.settings_sizer, 0, wx.EXPAND)
        self.main_sizer.Add(self.plot_panel, 1, wx.EXPAND)
        self.main_sizer.Fit(panel)

        self.SetSize(self._window_size)
        self.SetSizer(self.main_sizer)
        self.Layout()

    def make_plot_panel(self, split_panel):
        """Make plot panel"""

        pixel_size = [(self._window_size[0] - self._settings_panel_size[0]), (self._window_size[1] - 50)]
        figsize = [
            pixel_size[0] / self._display_resolution[0],
            pixel_size[1] / self._display_resolution[1],
        ]
        figsize_1D = [figsize[0] / 2.75, figsize[1] / 3]
        figsize_2D = [figsize[0] / 2.75, figsize[1] / 1.5]

        if self.config.unidec_plot_panel_view == 'Single page view':
            self.plot_panel = wx.lib.scrolledpanel.ScrolledPanel(split_panel)
            self.plot_panel.SetupScrolling()

            self.plotUnidec_MS = mpl_plots.plots(self.plot_panel, config=self.config, figsize=figsize_1D)
            self.plotUnidec_mwDistribution = mpl_plots.plots(self.plot_panel, config=self.config, figsize=figsize_1D)

            self.plotUnidec_mzGrid = mpl_plots.plots(self.plot_panel, config=self.config, figsize=figsize_2D)
            self.plotUnidec_mwVsZ = mpl_plots.plots(self.plot_panel, config=self.config, figsize=figsize_2D)

            self.plotUnidec_individualPeaks = mpl_plots.plots(self.plot_panel, config=self.config, figsize=figsize_2D)
            self.plotUnidec_barChart = mpl_plots.plots(self.plot_panel, config=self.config, figsize=figsize_2D)
            self.plotUnidec_chargeDistribution = mpl_plots.plots(
                self.plot_panel, config=self.config, figsize=figsize_1D,
            )

            grid = wx.GridBagSizer(10, 10)
            n = 0
            grid.Add(self.plotUnidec_MS, (n, 0), span=(1, 1), flag=wx.EXPAND)
            grid.Add(self.plotUnidec_mwDistribution, (n, 1), span=(1, 1), flag=wx.EXPAND)
            n += 1
            grid.Add(self.plotUnidec_mzGrid, (n, 0), span=(1, 1), flag=wx.EXPAND)
            grid.Add(self.plotUnidec_mwVsZ, (n, 1), span=(1, 1), flag=wx.EXPAND)
            n += 1
            grid.Add(self.plotUnidec_individualPeaks, (n, 0), span=(1, 1), flag=wx.EXPAND)
            grid.Add(self.plotUnidec_barChart, (n, 1), span=(1, 1), flag=wx.EXPAND)
            n += 1
            grid.Add(self.plotUnidec_chargeDistribution, (n, 0), span=(1, 1), flag=wx.EXPAND)

            main_sizer = wx.BoxSizer(wx.VERTICAL)
            main_sizer.Add(grid, 1, wx.EXPAND, 2)
            # fit layout
            self.plot_panel.SetSizer(main_sizer)
            main_sizer.Fit(self.plot_panel)
        else:
            self.plot_panel = wx.Panel(split_panel)
            self.unidec_notebook = wx.Notebook(self.plot_panel)

            self.unidec_MS, self.plotUnidec_MS, __ = \
                self.panel_plot.make_plot(self.unidec_notebook, figsize_1D)
            self.unidec_mwDistribution, self.plotUnidec_mwDistribution, __ = \
                self.panel_plot.make_plot(self.unidec_notebook, figsize_1D)

            self.unidec_mzGrid, self.plotUnidec_mzGrid, __ = \
                self.panel_plot.make_plot(self.unidec_notebook, figsize_2D)
            self.unidec_mwVsZ, self.plotUnidec_mwVsZ, __ = \
                self.panel_plot.make_plot(self.unidec_notebook, figsize_2D)

            self.unidec_individualPeaks, self.plotUnidec_individualPeaks, __ = \
                self.panel_plot.make_plot(self.unidec_notebook, figsize_2D)
            self.unidec_barChart, self.plotUnidec_barChart, __ = \
                self.panel_plot.make_plot(self.unidec_notebook, figsize_2D)

            self.unidec_chargeDistribution, self.plotUnidec_chargeDistribution, __ = \
                self.panel_plot.make_plot(self.unidec_notebook, figsize_1D)

            self.unidec_notebook.AddPage(self.unidec_MS, 'MS', False)
            self.unidec_notebook.AddPage(self.unidec_mwDistribution, 'MW', False)

            self.unidec_notebook.AddPage(self.unidec_mzGrid, 'm/z vs Charge', False)
            self.unidec_notebook.AddPage(self.unidec_mwVsZ, 'MW vs Charge', False)

            self.unidec_notebook.AddPage(self.unidec_individualPeaks, 'Isolated MS', False)
            self.unidec_notebook.AddPage(self.unidec_barChart, 'Barplot', False)

            self.unidec_notebook.AddPage(self.unidec_chargeDistribution, 'Charge distribution', False)

            main_sizer = wx.BoxSizer(wx.VERTICAL)
            main_sizer.Add(self.unidec_notebook, 1, wx.EXPAND, 2)
            # fit layout
            self.plot_panel.SetSizer(main_sizer)
            main_sizer.Fit(self.plot_panel)

        return self.plot_panel

    def make_preprocess_settings_panel(self, split_panel):
        panel = wx.Panel(split_panel, -1, size=(-1, -1), name='preprocess')

        unidec_ms_min_label = wx.StaticText(panel, wx.ID_ANY, 'm/z start:')
        self.unidec_mzStart_value = wx.TextCtrl(
            panel, -1, '', size=TEXTCTRL_SIZE,
            validator=validator('floatPos'),
        )
        self.unidec_mzStart_value.SetValue(str(self.config.unidec_mzStart))
        self.unidec_mzStart_value.Bind(wx.EVT_TEXT, self.on_apply)

        unidec_ms_max_label = wx.StaticText(panel, wx.ID_ANY, 'end:')
        self.unidec_mzEnd_value = wx.TextCtrl(
            panel, -1, '', size=TEXTCTRL_SIZE,
            validator=validator('floatPos'),
        )
        self.unidec_mzEnd_value.SetValue(str(self.config.unidec_mzEnd))
        self.unidec_mzEnd_value.Bind(wx.EVT_TEXT, self.on_apply)

        unidec_ms_binsize_label = wx.StaticText(panel, wx.ID_ANY, 'm/z bin size:')
        self.unidec_mzBinSize_value = wx.TextCtrl(
            panel, -1, '', size=TEXTCTRL_SIZE,
            validator=validator('floatPos'),
        )
        self.unidec_mzBinSize_value.SetValue(str(self.config.unidec_mzBinSize))
        self.unidec_mzBinSize_value.Bind(wx.EVT_TEXT, self.on_apply)

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

        self.unidec_preprocess = wx.Button(
            panel, -1, 'Pre-process',
            size=BTN_SIZE, name='preprocess_unidec',
        )
        self.unidec_preprocess.Bind(wx.EVT_BUTTON, self.on_initilize_unidec)

        horizontal_line_0 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        btn_grid = wx.GridBagSizer(2, 2)
        n = 0
        btn_grid.Add(self.unidec_preprocess, (n, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)

        # pack elements
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(unidec_ms_min_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.unidec_mzStart_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(unidec_ms_max_label, (n, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.unidec_mzEnd_value, (n, 3), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n += 1
        grid.Add(unidec_ms_binsize_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.unidec_mzBinSize_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n += 1
        grid.Add(
            unidec_ms_gaussianFilter_label, (n, 0), wx.GBSpan(1, 1),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT,
        )
        grid.Add(self.unidec_gaussianFilter_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n += 1
        grid.Add(
            unidec_ms_accelerationV_label, (n, 0), wx.GBSpan(1, 1),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT,
        )
        grid.Add(self.unidec_accelerationV_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n += 1
        grid.Add(unidec_linearization_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.unidec_linearization_choice, (n, 1), wx.GBSpan(1, 4), flag=wx.ALIGN_CENTER_VERTICAL)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.ALIGN_CENTER_HORIZONTAL, 2)
        main_sizer.Add(btn_grid, 0, wx.ALIGN_RIGHT, 2)
        main_sizer.Add(horizontal_line_0, 0, wx.EXPAND, 2)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def make_unidec_settings_panel(self, split_panel):
        panel = wx.Panel(split_panel, -1, size=(-1, -1), name='unidec')

        unidec_charge_min_label = wx.StaticText(panel, wx.ID_ANY, 'Charge start:')
        self.unidec_zStart_value = wx.TextCtrl(
            panel, -1, '', size=TEXTCTRL_SIZE,
            validator=validator('floatPos'),
        )
        self.unidec_zStart_value.SetValue(str(self.config.unidec_zStart))
        self.unidec_zStart_value.Bind(wx.EVT_TEXT, self.on_apply)

        unidec_charge_max_label = wx.StaticText(panel, wx.ID_ANY, 'end:')
        self.unidec_zEnd_value = wx.TextCtrl(
            panel, -1, '', size=TEXTCTRL_SIZE,
            validator=validator('floatPos'),
        )
        self.unidec_zEnd_value.SetValue(str(self.config.unidec_zEnd))
        self.unidec_zEnd_value.Bind(wx.EVT_TEXT, self.on_apply)

        unidec_mw_min_label = wx.StaticText(panel, wx.ID_ANY, 'MW start:')
        self.unidec_mwStart_value = wx.TextCtrl(
            panel, -1, '', size=TEXTCTRL_SIZE,
            validator=validator('floatPos'),
        )
        self.unidec_mwStart_value.SetValue(str(self.config.unidec_mwStart))
        self.unidec_mwStart_value.Bind(wx.EVT_TEXT, self.on_apply)

        unidec_mw_max_label = wx.StaticText(panel, wx.ID_ANY, 'end:')
        self.unidec_mwEnd_value = wx.TextCtrl(
            panel, -1, '', size=TEXTCTRL_SIZE,
            validator=validator('floatPos'),
        )
        self.unidec_mwEnd_value.SetValue(str(self.config.unidec_mwEnd))
        self.unidec_mwEnd_value.Bind(wx.EVT_TEXT, self.on_apply)

        unidec_mw_sampleFrequency_label = wx.StaticText(panel, wx.ID_ANY, 'Sample frequency (Da):')
        self.unidec_mw_sampleFrequency_value = wx.TextCtrl(
            panel, -1, '', size=TEXTCTRL_SIZE,
            validator=validator('floatPos'),
        )
        self.unidec_mw_sampleFrequency_value.SetValue(str(self.config.unidec_mwFrequency))
        self.unidec_mw_sampleFrequency_value.Bind(wx.EVT_TEXT, self.on_apply)

        unidec_peakWidth_label = wx.StaticText(panel, wx.ID_ANY, 'Peak FWHM (Da):')
        self.unidec_fit_peakWidth_value = wx.TextCtrl(
            panel, -1, '', size=TEXTCTRL_SIZE,
            validator=validator('floatPos'),
        )
        self.unidec_fit_peakWidth_value.SetValue(str(self.config.unidec_peakWidth))
        self.unidec_fit_peakWidth_value.Bind(wx.EVT_TEXT, self.on_apply)

        self.unidec_fit_peakWidth_check = makeCheckbox(panel, 'Auto')
        self.unidec_fit_peakWidth_check.SetValue(self.config.unidec_peakWidth_auto)
        self.unidec_fit_peakWidth_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.unidec_fit_peakWidth_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        self.unidec_peak_width_btn = wx.BitmapButton(
            panel, -1, self.icons.iconsLib['measure_16'], size=(-1, 22),
            style=wx.ALIGN_CENTER_VERTICAL,
        )
        self.unidec_peak_width_btn.SetToolTip(makeTooltip('Open peak width tool...'))
        self.unidec_peak_width_btn.Bind(wx.EVT_BUTTON, self.on_open_width_tool)

        unidec_peakShape_label = wx.StaticText(panel, wx.ID_ANY, 'Peak Shape:')
        self.unidec_peakFcn_choice = wx.Choice(
            panel, -1, choices=list(self.config.unidec_peakFunction_choices.keys()),
            size=(-1, -1),
        )

        self.unidec_peakFcn_choice.SetStringSelection(self.config.unidec_peakFunction)
        self.unidec_peakFcn_choice.Bind(wx.EVT_CHOICE, self.on_apply)

        self.unidec_runUnidec = wx.Button(
            panel, -1, 'Run UniDec', size=BTN_SIZE, name='run_unidec',
        )
        self.unidec_runUnidec.Bind(wx.EVT_BUTTON, self.on_run_unidec)
        horizontal_line_0 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        btn_grid = wx.GridBagSizer(2, 2)
        n = 0
        btn_grid.Add(self.unidec_runUnidec, (n, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)

        # pack elements
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(unidec_charge_min_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.unidec_zStart_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(unidec_charge_max_label, (n, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.unidec_zEnd_value, (n, 3), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(unidec_mw_min_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.unidec_mwStart_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(unidec_mw_max_label, (n, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.unidec_mwEnd_value, (n, 3), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(
            unidec_mw_sampleFrequency_label, (n, 0), wx.GBSpan(1, 1),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT,
        )
        grid.Add(
            self.unidec_mw_sampleFrequency_value, (n, 1), wx.GBSpan(1, 1),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND,
        )
        n += 1
        grid.Add(unidec_peakWidth_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.unidec_fit_peakWidth_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.unidec_peak_width_btn, (n, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.unidec_fit_peakWidth_check, (n, 3), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n += 1
        grid.Add(unidec_peakShape_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.unidec_peakFcn_choice, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.ALIGN_CENTER_HORIZONTAL, 2)
        main_sizer.Add(btn_grid, 0, wx.ALIGN_RIGHT, 2)
        main_sizer.Add(horizontal_line_0, 0, wx.EXPAND, 2)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def make_peaks_settings_panel(self, split_panel):
        panel = wx.Panel(split_panel, -1, size=(-1, -1), name='peaks')

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

        unidec_peak_separation_label = wx.StaticText(panel, wx.ID_ANY, 'Line separation:')
        self.unidec_lineSeparation_value = wx.TextCtrl(
            panel, -1, '', size=TEXTCTRL_SIZE,
            validator=validator('floatPos'),
        )
        self.unidec_lineSeparation_value.SetValue(str(self.config.unidec_lineSeparation))
        self.unidec_lineSeparation_value.Bind(wx.EVT_TEXT, self.on_apply)

        individualComponents_label = wx.StaticText(panel, wx.ID_ANY, 'Show individual components:')
        self.unidec_individualComponents_check = makeCheckbox(panel, '')
        self.unidec_individualComponents_check.SetValue(self.config.unidec_show_individualComponents)
        self.unidec_individualComponents_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        markers_label = wx.StaticText(panel, wx.ID_ANY, 'Show markers:')
        self.unidec_markers_check = makeCheckbox(panel, '')
        self.unidec_markers_check.SetValue(self.config.unidec_show_markers)
        self.unidec_markers_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.unidec_detectPeaks = wx.Button(
            panel, -1,
            #              ID_processSettings_pickPeaksUniDec,
            'Detect peaks',
            size=BTN_SIZE, name='pick_peaks_unidec',
        )

        btn_grid = wx.GridBagSizer(2, 2)
        n = 0
        btn_grid.Add(self.unidec_detectPeaks, (n, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)

        horizontal_line_0 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        # pack elements
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(unidec_peak_width_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.unidec_peakWidth_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n += 1
        grid.Add(unidec_peak_threshold_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.unidec_peakThreshold_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n += 1
        grid.Add(
            unidec_peak_normalization_label, (n, 0), wx.GBSpan(1, 1),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT,
        )
        grid.Add(self.unidec_peakNormalization_choice, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n += 1
        grid.Add(unidec_peak_separation_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.unidec_lineSeparation_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n += 1
        grid.Add(individualComponents_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.unidec_individualComponents_check, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n += 1
        grid.Add(markers_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.unidec_markers_check, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.ALIGN_CENTER_HORIZONTAL, 2)
        main_sizer.Add(btn_grid, 0, wx.ALIGN_RIGHT, 2)
        main_sizer.Add(horizontal_line_0, 0, wx.EXPAND, 2)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def make_visualise_settings_panel(self, split_panel):
        panel = wx.Panel(split_panel, -1, size=(-1, -1), name='peaks')

        unidec_plotting_weights_label = wx.StaticText(panel, wx.ID_ANY, 'Molecular weights:')
        self.unidec_weightList_choice = wx.ComboBox(
            panel, -1,
            #             ID_processSettings_showZUniDec,
            choices=[],
            size=(150, -1), style=wx.CB_READONLY,
            name='ChargeStates',
        )
#         self.unidec_weightList_choice.Bind(wx.EVT_COMBOBOX, self.on_run_unidec_fcn)

        self.unidec_weightList_sort = wx.BitmapButton(
            panel, wx.ID_ANY,
            self.icons.iconsLib['sort_1to9_16'],
            size=(-1, -1), name='unidec_sort',
            style=wx.ALIGN_CENTER_VERTICAL,
        )
        self.unidec_weightList_sort.SetBackgroundColour((240, 240, 240))
#         self.unidec_weightList_sort.Bind(wx.EVT_BUTTON, self.on_sort_unidec_MW)

        unidec_plotting_adduct_label = wx.StaticText(panel, wx.ID_ANY, 'Adduct:')
        self.unidec_adductMW_choice = wx.Choice(
            panel, -1,
            #             ID_processSettings_showZUniDec,
            choices=['H+', 'Na+', 'K+', 'NH4+', 'H-', 'Cl-'],
            size=(-1, -1), name='ChargeStates',
        )
        self.unidec_adductMW_choice.SetStringSelection('H+')
#         self.unidec_adductMW_choice.Bind(wx.EVT_CHOICE, self.on_run_unidec_fcn)

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
            panel, -1,
            #             ID_processSettings_restoreIsolatedAll,
            'Restore all', size=(-1, 22),
        )
#         self.unidec_restoreAll_Btn.Bind(wx.EVT_BUTTON, self.on_run_unidec_fcn)

        self.unidec_chargeStates_Btn = wx.Button(
            panel, -1,
            #                                                  ID_processSettings_showZUniDec,
            'Label', size=(-1, 22),
        )
#         self.unidec_chargeStates_Btn.Bind(wx.EVT_BUTTON, self.on_run_unidec_fcn)

        self.unidec_isolateCharges_Btn = wx.Button(
            panel, -1,
            #                                                    ID_processSettings_isolateZUniDec,
            'Isolate', size=(-1, 22),
        )
#         self.unidec_isolateCharges_Btn.Bind(wx.EVT_BUTTON, self.on_run_unidec_fcn)

        horizontal_line_0 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        btn_grid = wx.GridBagSizer(2, 2)
        n = 0
        btn_grid.Add(self.unidec_restoreAll_Btn, (n, 0), wx.GBSpan(1, 1), flag=wx.EXPAND)
        btn_grid.Add(self.unidec_chargeStates_Btn, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        btn_grid.Add(self.unidec_isolateCharges_Btn, (n, 2), wx.GBSpan(1, 1), flag=wx.EXPAND)

        # pack elements
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(
            unidec_plotting_weights_label, (n, 0), wx.GBSpan(1, 1),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT,
        )
        grid.Add(
            self.unidec_weightList_choice, (n, 1), wx.GBSpan(1, 2),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND,
        )
        grid.Add(
            self.unidec_weightList_sort, (n, 3), wx.GBSpan(1, 1),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND,
        )
        n += 1
        grid.Add(
            unidec_plotting_adduct_label, (n, 0), wx.GBSpan(1, 1),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT,
        )
        grid.Add(
            self.unidec_adductMW_choice, (n, 1), wx.GBSpan(1, 1),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND,
        )
        n += 1
        grid.Add(
            unidec_charges_threshold_label, (n, 0), wx.GBSpan(1, 1),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT,
        )
        grid.Add(
            self.unidec_charges_threshold_value, (n, 1), wx.GBSpan(1, 1),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT,
        )
        n += 1
        grid.Add(
            unidec_charges_offset_label, (n, 0), wx.GBSpan(1, 1),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT,
        )
        grid.Add(
            self.unidec_charges_offset_value, (n, 1), wx.GBSpan(1, 1),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT,
        )

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.ALIGN_CENTER_HORIZONTAL, 2)
        main_sizer.Add(btn_grid, 0, wx.ALIGN_RIGHT, 2)
        main_sizer.Add(horizontal_line_0, 0, wx.EXPAND, 2)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def make_buttons_settings_panel(self, split_panel):
        panel = wx.Panel(split_panel, -1, size=(-1, -1), name='peaks')

        self.unidec_auto_btn = wx.BitmapButton(
            panel, -1, self.icons.iconsLib['rocket_16'], size=(40, 22),
            style=wx.ALIGN_CENTER_VERTICAL,
        )
        self.unidec_auto_btn.Bind(wx.EVT_BUTTON, self.on_auto_unidec)

        self.unidec_init_btn = wx.BitmapButton(
            panel, -1, self.icons.iconsLib['run_run_16'], size=(40, 22),
            style=wx.ALIGN_CENTER_VERTICAL,
        )
        self.unidec_init_btn.Bind(wx.EVT_BUTTON, self.on_initilize_unidec)

        self.unidec_unidec_btn = wx.BitmapButton(
            panel, -1, self.icons.iconsLib['process_unidec_16'], size=(40, 22),
            style=wx.ALIGN_CENTER_VERTICAL,
        )
        self.unidec_unidec_btn.Bind(wx.EVT_BUTTON, self.on_run_unidec)

        self.unidec_peak_btn = wx.BitmapButton(
            panel, -1, self.icons.iconsLib['mark_peak_16'], size=(40, 22),
            style=wx.ALIGN_CENTER_VERTICAL,
        )
        self.unidec_peak_btn.Bind(wx.EVT_BUTTON, self.on_detect_peaks_unidec)

        self.unidec_all_btn = wx.Button(panel, wx.ID_OK, 'All', size=(40, 22))
        self.unidec_all_btn.Bind(wx.EVT_BUTTON, self.on_all_unidec)

        self.unidec_cancel_btn = wx.Button(panel, wx.ID_OK, 'Cancel', size=(-1, 22))
        self.unidec_cancel_btn.Bind(wx.EVT_BUTTON, self.on_close)

        self.unidec_customise_btn = wx.BitmapButton(
            panel, -1, self.icons.iconsLib['settings16_2'], size=(40, 22),
            style=wx.ALIGN_CENTER_VERTICAL,
        )
        self.unidec_customise_btn.SetToolTip(makeTooltip('Open customisation window...'))
        self.unidec_customise_btn.Bind(wx.EVT_BUTTON, self.on_open_customisation_settings)

        horizontal_line_0 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(self.unidec_auto_btn, (n, 0), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTRE_HORIZONTAL)
        grid.Add(self.unidec_init_btn, (n, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTRE_HORIZONTAL)
        grid.Add(self.unidec_unidec_btn, (n, 2), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTRE_HORIZONTAL)
        grid.Add(self.unidec_peak_btn, (n, 3), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTRE_HORIZONTAL)
        grid.Add(self.unidec_all_btn, (n, 4), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTRE_HORIZONTAL)
        grid.Add(self.unidec_cancel_btn, (n, 5), wx.GBSpan(1, 1), flag=wx.EXPAND)
        grid.Add(self.unidec_customise_btn, (n, 6), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTRE_HORIZONTAL)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.ALIGN_CENTER_HORIZONTAL, 2)
        main_sizer.Add(horizontal_line_0, 0, wx.EXPAND, 2)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def on_toggle_controls(self, evt):
        """Event driven GUI updates"""

        self.config.unidec_peakWidth_auto = self.unidec_fit_peakWidth_check.GetValue()
        obj_list = [self.unidec_fit_peakWidth_value, self.unidec_peak_width_btn]
        for item in obj_list:
            item.Enable(enable=not self.config.unidec_peakWidth_auto)

        if evt is not None:
            evt.Skip()

    def on_apply(self, evt):
        """Event driven GUI updates"""
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
        self.config.unidec_show_individualComponents = self.unidec_individualComponents_check.GetValue()

        self.config.unidec_charges_label_charges = str2num(self.unidec_charges_threshold_value.GetValue())
        self.config.unidec_charges_offset = str2num(self.unidec_charges_offset_value.GetValue())

        if evt is not None:
            evt.Skip()

    def on_clear_plot(self, evt):
        #         pass
        self.panel_plot.on_clear_plot(None, None, plot_obj=self.plot_window)

    def on_save_figure(self, evt):
        pass
#         plot_title = f'{self.document_title}_{self.dataset_name}'.replace(
#             ' ', '-',
#         ).replace(':', '')
#         self.panel_plot.save_images(None, None, plot_obj=self.plot_window, image_name=plot_title)

    def on_open_customisation_settings(self, evt):
        """Call another function to open the customisation window"""
        self.view.on_customise_unidec_plot_parameters(None)

    def on_open_width_tool(self, evt):
        from gui_elements.panel_process_unidec_peak_width_tool import PanelPeakWidthTool
        try:
            kwargs = {
                'xvals': self.config.unidec_engine.data.data2[:, 0],
                'yvals': self.config.unidec_engine.data.data2[:, 1],
            }
        except IndexError:
            raise MessageError('Missing data', 'Please pre-process data first')

        self.widthTool = PanelPeakWidthTool(self, self.presenter, self.config, **kwargs)
        self.widthTool.Show()

    def on_get_unidec_data(self):
        """Convenience function to retrieve UniDec data from the document"""
        # get data and document
        __, data = self.data_handling.get_spectrum_data([self.document_title, self.dataset_name])
        data = data.get('unidec', None)

        return data

    def on_plot(self, task):

        # get data and plot in the panel
        data = self.on_get_unidec_data()
        if data:
            if task in ['all', 'preprocess_unidec']:
                replot_data = data.get('Processed', None)
                if replot_data:
                    self.panel_plot.on_plot_unidec_MS(replot=replot_data, plot=None, plot_obj=self.plotUnidec_MS)

            if task in ['all', 'run_unidec']:
                replot_data = data.get('Fitted', None)
                if replot_data:
                    self.panel_plot.on_plot_unidec_MS_v_Fit(replot=replot_data, plot=None, plot_obj=self.plotUnidec_MS)
                replot_data = data.get('MW distribution', None)
                if replot_data:
                    self.panel_plot.on_plot_unidec_mwDistribution(
                        replot=replot_data, plot=None, plot_obj=self.plotUnidec_mwDistribution)
                replot_data = data.get('m/z vs Charge', None)
                if replot_data:
                    self.panel_plot.on_plot_unidec_mzGrid(
                        replot=replot_data, plot=None, plot_obj=self.plotUnidec_mzGrid)
                replot_data = data.get('MW vs Charge', None)
                if replot_data:
                    self.panel_plot.on_plot_unidec_MW_v_Charge(
                        replot=replot_data, plot=None, plot_obj=self.plotUnidec_mwVsZ)

            if task in ['all', 'pick_peaks_unidec']:
                print('not yet')

    def on_initilize_unidec(self, evt):
        tasks = ['load_data_unidec', 'preprocess_unidec']
        for task in tasks:
            self.data_processing.on_run_unidec_fcn(self.dataset_name, task)

        # plot
        self.on_plot('preprocess_unidec')

    def on_process_unidec(self, evt):
        self.data_processing.on_run_unidec_fcn(self.dataset_name, 'preprocess_unidec')

        # plot
        self.on_plot('preprocess_unidec')

    def on_run_unidec(self, evt):
        self.data_processing.on_run_unidec_fcn(self.dataset_name, 'run_unidec')

        # plot
        self.on_plot('run_unidec')

    def on_detect_peaks_unidec(self, evt):
        self.data_processing.on_run_unidec(self.dataset_name, 'pick_peaks_unidec')

        # plot
        self.on_plot('pick_peaks_unidec')

    def on_all_unidec(self, evt):
        self.data_processing.on_run_unidec_fcn(self.dataset_name, 'run_all_unidec')

        # plot
        self.on_plot('all')

    def on_auto_unidec(self, evt):
        self.data_processing.on_run_unidec_fcn(self.dataset_name, 'auto_unidec')

        # plot
        self.on_plot('all')