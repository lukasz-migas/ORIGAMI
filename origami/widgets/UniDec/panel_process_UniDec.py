"""UniDec processing panel"""
# Standard library imports
import time
import logging

# Third-party imports
import wx
import wx.lib.scrolledpanel as wxScrolledPanel
from pubsub import pub
from pubsub.core import TopicNameError

# Local imports
import origami.processing.UniDec.utilities as unidec_utils
from origami.styles import MiniFrame
from origami.styles import Validator
from origami.utils.screen import calculate_window_size
from origami.config.config import CONFIG
from origami.utils.utilities import report_time
from origami.utils.converters import str2int
from origami.utils.converters import str2num
from origami.gui_elements.mixins import DatasetMixin
from origami.gui_elements.mixins import ConfigUpdateMixin
from origami.gui_elements.helpers import make_tooltip
from origami.gui_elements.helpers import make_checkbox
from origami.gui_elements.helpers import set_item_font
from origami.gui_elements.helpers import make_menu_item
from origami.gui_elements.helpers import make_bitmap_btn
from origami.widgets.unidec.view_unidec import ViewBarchart
from origami.widgets.unidec.view_unidec import ViewIndividualPeaks
from origami.widgets.unidec.view_unidec import ViewMolecularWeight
from origami.widgets.unidec.view_unidec import ViewMassSpectrumGrid
from origami.widgets.unidec.view_unidec import ViewChargeDistribution
from origami.widgets.unidec.view_unidec import ViewMolecularWeightGrid
from origami.gui_elements.views.view_register import VIEW_REG
from origami.gui_elements.views.view_spectrum import ViewMassSpectrum

logger = logging.getLogger(__name__)

TEXTCTRL_SIZE = (60, -1)
BTN_SIZE = (100, -1)

# TODO: Improve layout and add new functionality
# TODO: Add table
# TODO: Add display difference and FWHM
# TODO: FIXME: There is an issue with adding markers to MW plot


class PanelProcessUniDec(MiniFrame, DatasetMixin, ConfigUpdateMixin):
    """UniDec panel"""

    # module specific parameters
    PUB_SUBSCRIBE_EVENT = "widget.picker.update.spectrum"
    HELP_LINK = "https://origami.lukasz-migas.com/"
    PANEL_BASE_TITLE = "UniDec"

    current_page = None

    # ui elements
    plot_notebook, view_ms, view_mw, view_ms_grid, main_sizer = None, None, None, None, None
    view_mw_grid, view_peaks, view_barchart, view_charge = None, None, None, None
    plot_panel, peak_width_value, peak_threshold_value, peak_normalization_choice = None, None, None, None
    line_separation_value, markers_check, individual_line_check, weight_list_choice = None, None, None, None
    charges_check, adduct_choice, charges_threshold_value, charges_offset_value = None, None, None, None
    restore_all_btn, isolate_charges_btn, label_charges_btn, weight_list_sort = None, None, None, None
    detect_peaks_btn, show_peaks_btn, z_start_value, z_end_value = None, None, None, None
    unidec_auto_btn, unidec_init_btn, unidec_unidec_btn, unidec_peak_btn = None, None, None, None
    unidec_all_btn, unidec_cancel_btn, unidec_customise_btn, mw_start_value = None, None, None, None
    mw_end_value, mw_sample_frequency_value, fit_peak_width_value, peak_width_btn = None, None, None, None
    peak_shape_func_choice, run_unidec_btn, peak_width_auto_check, process_settings_btn = None, None, None, None
    process_btn = None

    def __init__(self, parent, presenter, icons, document_title: str = None, dataset_name: str = None, mz_obj=None):
        """Initialize panel"""
        MiniFrame.__init__(self, parent, title="UniDec...", style=wx.DEFAULT_FRAME_STYLE & ~wx.MAXIMIZE_BOX)
        t_start = time.time()
        self.view = parent
        self.presenter = presenter
        self._icons = icons

        self._display_size = wx.GetDisplaySize()
        self._display_resolution = wx.ScreenDC().GetPPI()
        self._window_size = calculate_window_size(self._display_size, [0.9, 0.9])
        self._unidec_sort_column = 0

        # initialize gui
        self.make_gui()
        self.on_toggle_controls(None)
        self.CentreOnScreen()
        self.SetFocus()

        # setup kwargs
        self.document_title = document_title
        self.dataset_name = dataset_name
        self.mz_obj = mz_obj

        self.setup()

        # bind events
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_CONTEXT_MENU, self.on_right_click)
        logger.debug(f"Started-up UniDec panel in {report_time(t_start)}")

    def setup(self):
        """Setup window"""
        self._config_mixin_setup()
        self._dataset_mixin_setup()
        if self.PUB_SUBSCRIBE_EVENT:
            pub.subscribe(self.on_process, self.PUB_SUBSCRIBE_EVENT)
        # self.data_processing.on_threading("custom.action", ("all",), fcn=self.on_plot)

        if self.mz_obj:
            self.on_plot_ms(None)

    def on_close(self, evt, force: bool = False):
        """Close window"""
        self._config_mixin_teardown()
        self._dataset_mixin_teardown()
        try:
            if self.PUB_SUBSCRIBE_EVENT:
                pub.unsubscribe(self.on_process, self.PUB_SUBSCRIBE_EVENT)
        except TopicNameError:
            pass
        super(PanelProcessUniDec, self).on_close(evt, force)

    @property
    def data_handling(self):
        """Return handle to `data_handling`"""
        return self.presenter.data_handling

    @property
    def data_processing(self):
        """Return handle to `data_processing`"""
        return self.presenter.data_processing

    @property
    def panel_plot(self):
        """Return handle to `panel_plot`"""
        return self.view.panelPlots

    @property
    def document_tree(self):
        """Return handle to `document_tree`"""
        return self.presenter.view.panelDocuments.documents

    def on_right_click(self, _evt):
        """Right-click menu"""
        view = VIEW_REG.view

        menu = view.get_right_click_menu(self)
        save_all_figures_menu_item = make_menu_item(
            menu, evt_id=wx.ID_ANY, text="Save all figures as...", bitmap=self._icons.save_all
        )
        menu.Insert(4, save_all_figures_menu_item)

        self.Bind(wx.EVT_MENU, self.on_save_all_figures, save_all_figures_menu_item)

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def make_gui(self):
        """Make gui"""
        settings_panel = self.make_settings_panel(self)

        self.plot_panel = self.make_plot_panel(self)

        # pack element
        main_sizer = wx.BoxSizer()
        main_sizer.Add(self.plot_panel, 1, wx.EXPAND, 0)

        # add settings panel
        if "Left" in CONFIG.unidec_plot_settings_view:
            main_sizer.Insert(0, settings_panel, 0, wx.EXPAND, 0)
        else:
            main_sizer.Add(settings_panel, 0, wx.EXPAND, 0)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizerAndFit(main_sizer)
        self.Layout()

    def make_plot_panel(self, split_panel):
        """Make plot panel"""

        # pixel_size = [(self._window_size[0] - self._settings_panel_size[0]), (self._window_size[1] - 50)]
        # figsize = [pixel_size[0] / self._display_resolution[0], pixel_size[1] / self._display_resolution[1]]
        # figsize_1D = [figsize[0] / 2.75, figsize[1] / 3]
        # figsize_2D = [figsize[0] / 2.75, figsize[1] / 1.5]

        # setup plot base
        if CONFIG.unidec_plot_panel_view == "Single page view":
            plot_panel = wxScrolledPanel.ScrolledPanel(split_panel)
            plot_parent = plot_panel
        else:
            plot_panel = wx.Panel(split_panel)
            plot_parent = wx.Notebook(plot_panel)

        # mass spectrum
        self.view_ms = ViewMassSpectrum(
            plot_parent,
            CONFIG._plotSettings["MS"]["gui_size"],  # noqa
            CONFIG,
            allow_extraction=False,
            filename="mass-spectrum",
        )

        # molecular weight
        self.view_mw = ViewMolecularWeight(
            plot_parent,
            CONFIG._plotSettings["MS"]["gui_size"],  # noqa
            CONFIG,
            allow_extraction=False,
            filename="molecular-weight",
        )

        # molecular weight
        self.view_ms_grid = ViewMassSpectrumGrid(
            plot_parent,
            CONFIG._plotSettings["MS"]["gui_size"],  # noqa
            CONFIG,
            allow_extraction=False,
            filename="ms-grid",
        )

        # molecular weight
        self.view_mw_grid = ViewMolecularWeightGrid(
            plot_parent,
            CONFIG._plotSettings["MS"]["gui_size"],  # noqa
            CONFIG,
            allow_extraction=False,
            filename="mw-grid",
        )

        # molecular weight
        self.view_peaks = ViewIndividualPeaks(
            plot_parent,
            CONFIG._plotSettings["MS"]["gui_size"],  # noqa
            CONFIG,
            allow_extraction=False,
            filename="isolated-peaks",
        )

        # molecular weight
        self.view_barchart = ViewBarchart(
            plot_parent,
            CONFIG._plotSettings["MS"]["gui_size"],  # noqa
            CONFIG,
            allow_extraction=False,
            filename="barchart",
        )
        # molecular weight
        self.view_charge = ViewChargeDistribution(
            plot_parent,
            CONFIG._plotSettings["MS"]["gui_size"],  # noqa
            CONFIG,
            allow_extraction=False,
            filename="charge-distribution",
        )

        if CONFIG.unidec_plot_panel_view == "Single page view":
            grid = wx.GridBagSizer(10, 10)
            n = 0
            grid.Add(self.view_ms.panel, (n, 0), span=(1, 1), flag=wx.EXPAND)
            grid.Add(self.view_mw.panel, (n, 1), span=(1, 1), flag=wx.EXPAND)
            n += 1
            grid.Add(self.view_ms_grid.panel, (n, 0), span=(1, 1), flag=wx.EXPAND)
            grid.Add(self.view_mw_grid.panel, (n, 1), span=(1, 1), flag=wx.EXPAND)
            n += 1
            grid.Add(self.view_peaks.panel, (n, 0), span=(1, 1), flag=wx.EXPAND)
            grid.Add(self.view_barchart.panel, (n, 1), span=(1, 1), flag=wx.EXPAND)
            n += 1
            grid.Add(self.view_charge.panel, (n, 0), span=(1, 1), flag=wx.EXPAND)

            main_sizer = wx.BoxSizer(wx.VERTICAL)
            main_sizer.Add(grid, 1, wx.EXPAND, 2)
            # fit layout
            self.plot_panel.SetSizer(main_sizer)
            main_sizer.Fit(self.plot_panel)

            # setup scrolling
            plot_panel.SetupScrolling()
        else:
            plot_parent.AddPage(self.view_ms.panel, "MS")
            plot_parent.AddPage(self.view_mw.panel, "MW")
            plot_parent.AddPage(self.view_ms_grid.panel, "m/z vs Charge")
            plot_parent.AddPage(self.view_mw_grid.panel, "MW vs Charge")
            plot_parent.AddPage(self.view_peaks.panel, "Isolated MS")
            plot_parent.AddPage(self.view_barchart.panel, "Barchart")
            plot_parent.AddPage(self.view_charge.panel, "Charge distribution")

            plot_parent.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.on_page_changed)
            self.plot_notebook = plot_parent

            main_sizer = wx.BoxSizer(wx.VERTICAL)
            main_sizer.Add(plot_parent, 1, wx.EXPAND, 2)
            self.plot_panel = plot_panel

            # fit layout
            main_sizer.Fit(self.plot_panel)
            self.plot_panel.SetSizerAndFit(main_sizer)

            self.on_page_changed(None)

        return self.plot_panel

    def make_settings_panel(self, split_panel):
        """Make settings panel"""
        panel = wxScrolledPanel.ScrolledPanel(split_panel, size=(-1, -1), name="main")

        n_span = 3
        n_col = 4
        grid = wx.GridBagSizer(2, 2)

        # make buttons
        grid, n = self.make_buttons_settings_panel(panel, grid, 0, n_span, n_col)
        n += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)

        # pre-processing
        preprocessing_label = wx.StaticText(panel, -1, "Pre-processing")
        set_item_font(preprocessing_label)
        n += 1
        grid.Add(preprocessing_label, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        grid, n = self.make_preprocess_settings_panel(panel, grid, n, n_span, n_col)

        # unidec
        unidec_label = wx.StaticText(panel, -1, "UniDec")
        set_item_font(unidec_label)
        n += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(unidec_label, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        grid, n = self.make_unidec_settings_panel(panel, grid, n, n_span, n_col)

        # peak detection
        peak_label = wx.StaticText(panel, -1, "Peak detection")
        set_item_font(peak_label)
        n += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(peak_label, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        grid, n = self.make_peaks_settings_panel(panel, grid, n, n_span, n_col)

        # visualisation
        view_label = wx.StaticText(panel, -1, "Visualisation")
        set_item_font(view_label)
        n += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        n += 1
        grid.Add(view_label, (n, 0), wx.GBSpan(1, n_col), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (n, 0), wx.GBSpan(1, n_col), flag=wx.EXPAND)
        grid, n = self.make_visualise_settings_panel(panel, grid, n, n_span, n_col)
        grid.AddGrowableCol(0, 1)

        info_sizer = self.make_statusbar(panel)

        settings_sizer = wx.BoxSizer(wx.VERTICAL)
        settings_sizer.Add(grid, 1, wx.EXPAND, 5)
        settings_sizer.AddStretchSpacer()
        settings_sizer.Add(info_sizer, 0, wx.EXPAND, 10)

        # fit layout
        settings_sizer.Fit(panel)
        settings_sizer.SetMinSize((380, -1))
        panel.SetSizerAndFit(settings_sizer)
        panel.SetupScrolling()

        return panel

    def make_buttons_settings_panel(self, panel, grid, n: int, n_span: int, n_col: int):  # noqa
        """Make buttons sub-section"""
        self.unidec_auto_btn = make_bitmap_btn(panel, -1, self._icons.rocket)
        self.unidec_auto_btn.Bind(wx.EVT_BUTTON, self.on_auto_unidec)
        self.unidec_auto_btn.SetToolTip(make_tooltip("Autorun..."))

        self.unidec_init_btn = make_bitmap_btn(panel, -1, self._icons.run)
        self.unidec_init_btn.Bind(wx.EVT_BUTTON, self.on_initialize_unidec)
        self.unidec_init_btn.SetToolTip(make_tooltip("Initialize and pre-process..."))

        self.unidec_unidec_btn = make_bitmap_btn(panel, -1, self._icons.unidec)
        self.unidec_unidec_btn.Bind(wx.EVT_BUTTON, self.on_run_unidec)
        self.unidec_unidec_btn.SetToolTip(make_tooltip("Run UniDec..."))

        self.unidec_peak_btn = make_bitmap_btn(panel, -1, self._icons.peak)
        self.unidec_peak_btn.Bind(wx.EVT_BUTTON, self.on_detect_peaks_unidec)
        self.unidec_peak_btn.SetToolTip(make_tooltip("Detect peaks..."))

        self.unidec_all_btn = wx.Button(panel, wx.ID_OK, "All", size=(40, -1))
        self.unidec_all_btn.Bind(wx.EVT_BUTTON, self.on_all_unidec)
        self.unidec_all_btn.SetToolTip(make_tooltip("Run all..."))

        self.unidec_cancel_btn = wx.Button(panel, wx.ID_OK, "Cancel", size=(-1, -1))
        self.unidec_cancel_btn.Bind(wx.EVT_BUTTON, self.on_close)
        self.unidec_cancel_btn.SetToolTip(make_tooltip("Close window..."))

        self.unidec_customise_btn = make_bitmap_btn(panel, -1, self._icons.gear)
        self.unidec_customise_btn.SetToolTip(make_tooltip("Open customisation window..."))
        self.unidec_customise_btn.Bind(wx.EVT_BUTTON, self.on_open_customisation_settings)

        btn_sizer = wx.BoxSizer()
        btn_sizer.Add(self.unidec_auto_btn, 0, wx.EXPAND)
        btn_sizer.AddSpacer(5)
        btn_sizer.Add(self.unidec_init_btn, 0, wx.EXPAND)
        btn_sizer.AddSpacer(5)
        btn_sizer.Add(self.unidec_unidec_btn, 0, wx.EXPAND)
        btn_sizer.AddSpacer(5)
        btn_sizer.Add(self.unidec_peak_btn, 0, wx.EXPAND)
        btn_sizer.AddSpacer(5)
        btn_sizer.Add(self.unidec_all_btn, 0, wx.EXPAND)
        btn_sizer.AddSpacer(5)
        btn_sizer.Add(self.unidec_cancel_btn, 0, wx.EXPAND)
        btn_sizer.AddSpacer(5)
        btn_sizer.Add(self.unidec_customise_btn, 0, wx.EXPAND)

        grid.Add(btn_sizer, (n, 0), (1, n_col), flag=wx.ALIGN_CENTER_HORIZONTAL)

        return grid, n

    def make_preprocess_settings_panel(self, panel, grid, n: int, n_span: int, n_col: int):  # noqa
        """Make pre-processing sub-section"""

        process_label = wx.StaticText(
            panel,
            wx.ID_ANY,
            "Process MS data before running UniDec. You can change the "
            "\nsettings by clicking on the `Settings` button. Data will be "
            "\nautomatically plotted as you adjust the parameters",
            size=(-1, -1),
        )
        set_item_font(process_label, weight=wx.FONTWEIGHT_NORMAL)

        self.process_settings_btn = make_bitmap_btn(
            panel, -1, self._icons.process_ms, tooltip="Change MS pre-processing parameters"
        )
        self.process_settings_btn.Bind(wx.EVT_BUTTON, self.on_open_process_ms_settings)

        self.process_btn = wx.Button(panel, -1, "Process mass spectrum", size=(-1, -1), name="show_peaks_unidec")
        self.process_btn.Bind(wx.EVT_BUTTON, self.on_show_peaks_unidec)

        btn_sizer = wx.BoxSizer()
        btn_sizer.Add(self.process_settings_btn, 0, wx.EXPAND)
        btn_sizer.AddSpacer(5)
        btn_sizer.Add(self.process_btn, 0, wx.EXPAND)

        n += 1
        grid.Add(process_label, (n, 0), (1, n_col), flag=wx.ALIGN_CENTER_HORIZONTAL)
        n += 1
        grid.Add(btn_sizer, (n, 0), (1, n_col), flag=wx.ALIGN_CENTER_HORIZONTAL)

        return grid, n

    def make_unidec_settings_panel(self, panel, grid, n: int, n_span: int, n_col: int):  # noqa
        """Make unidec settings sub-section"""
        z_start_value = wx.StaticText(panel, wx.ID_ANY, "Charge start:")
        self.z_start_value = wx.TextCtrl(panel, -1, "", size=TEXTCTRL_SIZE, validator=Validator("floatPos"))
        self.z_start_value.SetValue(str(CONFIG.unidec_zStart))
        self.z_start_value.Bind(wx.EVT_TEXT, self.on_apply)

        z_end_value = wx.StaticText(panel, wx.ID_ANY, "end:")
        self.z_end_value = wx.TextCtrl(panel, -1, "", size=TEXTCTRL_SIZE, validator=Validator("floatPos"))
        self.z_end_value.SetValue(str(CONFIG.unidec_zEnd))
        self.z_end_value.Bind(wx.EVT_TEXT, self.on_apply)

        unidec_mw_min_label = wx.StaticText(panel, wx.ID_ANY, "MW start:")
        self.mw_start_value = wx.TextCtrl(panel, -1, "", size=TEXTCTRL_SIZE, validator=Validator("floatPos"))
        self.mw_start_value.SetValue(str(CONFIG.unidec_mwStart))
        self.mw_start_value.Bind(wx.EVT_TEXT, self.on_apply)

        unidec_mw_max_label = wx.StaticText(panel, wx.ID_ANY, "end:")
        self.mw_end_value = wx.TextCtrl(panel, -1, "", size=TEXTCTRL_SIZE, validator=Validator("floatPos"))
        self.mw_end_value.SetValue(str(CONFIG.unidec_mwEnd))
        self.mw_end_value.Bind(wx.EVT_TEXT, self.on_apply)

        mw_sample_frequency_label = wx.StaticText(panel, wx.ID_ANY, "Sample frequency (Da):")
        self.mw_sample_frequency_value = wx.TextCtrl(panel, -1, "", size=TEXTCTRL_SIZE, validator=Validator("floatPos"))
        self.mw_sample_frequency_value.SetValue(str(CONFIG.unidec_mwFrequency))
        self.mw_sample_frequency_value.Bind(wx.EVT_TEXT, self.on_apply)

        peak_width_label = wx.StaticText(panel, wx.ID_ANY, "Peak FWHM (Da):")
        self.fit_peak_width_value = wx.TextCtrl(panel, -1, "", size=TEXTCTRL_SIZE, validator=Validator("floatPos"))
        self.fit_peak_width_value.SetValue(str(CONFIG.unidec_peakWidth))
        self.fit_peak_width_value.Bind(wx.EVT_TEXT, self.on_apply)

        self.peak_width_btn = make_bitmap_btn(panel, -1, self._icons.measure)
        self.peak_width_btn.SetToolTip(make_tooltip("Open peak width tool..."))
        self.peak_width_btn.Bind(wx.EVT_BUTTON, self.on_open_width_tool)

        self.peak_width_auto_check = make_checkbox(panel, "Auto")
        self.peak_width_auto_check.SetValue(CONFIG.unidec_peakWidth_auto)
        self.peak_width_auto_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.peak_width_auto_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        peak_shape_label = wx.StaticText(panel, wx.ID_ANY, "Peak Shape:")
        self.peak_shape_func_choice = wx.Choice(panel, -1, choices=CONFIG.unidec_peakFunction_choices, size=(-1, -1))

        self.peak_shape_func_choice.SetStringSelection(CONFIG.unidec_peakFunction)
        self.peak_shape_func_choice.Bind(wx.EVT_CHOICE, self.on_apply)

        self.run_unidec_btn = wx.Button(panel, -1, "Run UniDec", size=BTN_SIZE, name="run_unidec")
        self.run_unidec_btn.Bind(wx.EVT_BUTTON, self.on_run_unidec)

        btn_sizer = wx.BoxSizer()
        btn_sizer.Add(self.run_unidec_btn, 0, wx.EXPAND)

        # pack elements
        n += 1
        grid.Add(z_start_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.z_start_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(z_end_value, (n, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(self.z_end_value, (n, 3), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(unidec_mw_min_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.mw_start_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(unidec_mw_max_label, (n, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(self.mw_end_value, (n, 3), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(mw_sample_frequency_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.mw_sample_frequency_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(peak_width_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.fit_peak_width_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.peak_width_auto_check, (n, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(self.peak_width_btn, (n, 3), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        n += 1
        grid.Add(peak_shape_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.peak_shape_func_choice, (n, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        n += 1
        grid.Add(btn_sizer, (n, 0), (1, n_col), flag=wx.ALIGN_CENTER_HORIZONTAL)

        return grid, n

    def make_peaks_settings_panel(self, panel, grid, n: int, n_span: int, n_col: int):  # noqa
        """Make peaks sub-section"""
        peak_width_value = wx.StaticText(panel, wx.ID_ANY, "Peak detection window (Da):")
        self.peak_width_value = wx.TextCtrl(panel, -1, "", size=TEXTCTRL_SIZE, validator=Validator("floatPos"))
        self.peak_width_value.SetValue(str(CONFIG.unidec_peakDetectionWidth))
        self.peak_width_value.Bind(wx.EVT_TEXT, self.on_apply)

        unidec_peak_threshold_label = wx.StaticText(panel, wx.ID_ANY, "Peak detection threshold:")
        self.peak_threshold_value = wx.TextCtrl(panel, -1, "", size=TEXTCTRL_SIZE, validator=Validator("floatPos"))
        self.peak_threshold_value.SetValue(str(CONFIG.unidec_peakDetectionThreshold))
        self.peak_threshold_value.Bind(wx.EVT_TEXT, self.on_apply)

        peak_normalization_choice = wx.StaticText(panel, wx.ID_ANY, "Peak normalization:")
        self.peak_normalization_choice = wx.Choice(
            panel, -1, choices=CONFIG.unidec_peakNormalization_choices, size=(-1, -1)
        )
        self.peak_normalization_choice.SetStringSelection(CONFIG.unidec_peakNormalization)
        self.peak_normalization_choice.Bind(wx.EVT_CHOICE, self.on_apply)

        line_separation_value = wx.StaticText(panel, wx.ID_ANY, "Line separation:")
        self.line_separation_value = wx.TextCtrl(panel, -1, "", size=TEXTCTRL_SIZE, validator=Validator("floatPos"))
        self.line_separation_value.SetValue(str(CONFIG.unidec_lineSeparation))
        self.line_separation_value.Bind(wx.EVT_TEXT, self.on_apply)

        markers_label = wx.StaticText(panel, wx.ID_ANY, "Show markers:")
        self.markers_check = make_checkbox(panel, "")
        self.markers_check.SetValue(CONFIG.unidec_show_markers)
        self.markers_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.markers_check.Bind(wx.EVT_CHECKBOX, self.on_show_peaks_unidec)

        individual_line_check = wx.StaticText(panel, wx.ID_ANY, "Show individual components:")
        self.individual_line_check = make_checkbox(panel, "")
        self.individual_line_check.SetValue(CONFIG.unidec_show_individualComponents)
        self.individual_line_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.individual_line_check.Bind(wx.EVT_CHECKBOX, self.on_show_peaks_unidec)

        self.detect_peaks_btn = wx.Button(panel, -1, "Detect peaks", size=BTN_SIZE, name="pick_peaks_unidec")
        self.detect_peaks_btn.Bind(wx.EVT_BUTTON, self.on_detect_peaks_unidec)

        self.show_peaks_btn = wx.Button(panel, -1, "Show peaks", size=BTN_SIZE, name="show_peaks_unidec")
        self.show_peaks_btn.Bind(wx.EVT_BUTTON, self.on_show_peaks_unidec)

        btn_sizer = wx.BoxSizer()
        btn_sizer.Add(self.detect_peaks_btn, 0, wx.EXPAND)
        btn_sizer.AddSpacer(5)
        btn_sizer.Add(self.show_peaks_btn, 0, wx.EXPAND)

        n += 1
        grid.Add(peak_width_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.peak_width_value, (n, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        n += 1
        grid.Add(unidec_peak_threshold_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.peak_threshold_value, (n, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        n += 1
        grid.Add(peak_normalization_choice, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.peak_normalization_choice, (n, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        n += 1
        grid.Add(line_separation_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.line_separation_value, (n, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        n += 1
        grid.Add(markers_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.markers_check, (n, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        n += 1
        grid.Add(individual_line_check, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.individual_line_check, (n, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        n += 1
        grid.Add(btn_sizer, (n, 0), (1, n_col), flag=wx.ALIGN_CENTER_HORIZONTAL)

        return grid, n

    def make_visualise_settings_panel(self, panel, grid, n: int, n_span: int, n_col: int):  # noqa
        """Make visualisation sub-section"""
        unidec_plotting_weights_label = wx.StaticText(panel, wx.ID_ANY, "Molecular weights:")
        self.weight_list_choice = wx.ComboBox(
            panel, -1, choices=[], size=(150, -1), style=wx.CB_READONLY, name="ChargeStates"
        )
        self.weight_list_choice.Bind(wx.EVT_COMBOBOX, self.on_isolate_peak_unidec)

        self.weight_list_sort = make_bitmap_btn(panel, -1, self._icons.sort)
        self.weight_list_sort.SetBackgroundColour((240, 240, 240))
        self.weight_list_sort.Bind(wx.EVT_BUTTON, self.on_sort_unidec_mw)

        charges_label = wx.StaticText(panel, wx.ID_ANY, "Show charges:")
        self.charges_check = make_checkbox(panel, "")
        self.charges_check.SetValue(CONFIG.unidec_show_chargeStates)
        self.charges_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.charges_check.Bind(wx.EVT_CHECKBOX, self.on_show_charge_states_unidec)
        self.charges_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        adduct_choice = wx.StaticText(panel, wx.ID_ANY, "Adduct:")
        self.adduct_choice = wx.Choice(
            panel,
            -1,
            choices=["H+", "H+ Na+", "Na+", "Na+ x2", "Na+ x3", "K+", "K+ x2", "K+ x3", "NH4+", "H-", "Cl-"],
            size=(-1, -1),
            name="ChargeStates",
        )
        self.adduct_choice.SetStringSelection("H+")
        self.adduct_choice.Bind(wx.EVT_CHOICE, self.on_show_charge_states_unidec)

        unidec_charges_threshold_label = wx.StaticText(panel, wx.ID_ANY, "Intensity threshold:")
        self.charges_threshold_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.unidec_charges_label_charges),
            min=0,
            max=1,
            initial=CONFIG.unidec_charges_label_charges,
            inc=0.01,
            size=(90, -1),
        )
        self.charges_threshold_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.charges_threshold_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_show_charge_states_unidec)

        unidec_charges_offset_label = wx.StaticText(panel, wx.ID_ANY, "Vertical charge offset:")
        self.charges_offset_value = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.unidec_charges_offset),
            min=0,
            max=1,
            initial=CONFIG.unidec_charges_offset,
            inc=0.05,
            size=(90, -1),
        )
        self.charges_offset_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.charges_offset_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_show_charge_states_unidec)

        self.restore_all_btn = wx.Button(panel, -1, "Restore all", size=(-1, -1))
        self.restore_all_btn.Bind(wx.EVT_BUTTON, self.on_show_peaks_unidec)

        self.isolate_charges_btn = wx.Button(panel, -1, "Isolate", size=(-1, -1))
        self.isolate_charges_btn.Bind(wx.EVT_BUTTON, self.on_isolate_peak_unidec)

        self.label_charges_btn = wx.Button(panel, -1, "Label", size=(-1, -1))
        self.label_charges_btn.Bind(wx.EVT_BUTTON, self.on_show_charge_states_unidec)

        btn_sizer = wx.BoxSizer()
        btn_sizer.Add(self.restore_all_btn, 0, wx.EXPAND)
        btn_sizer.AddSpacer(5)
        btn_sizer.Add(self.isolate_charges_btn, 0, wx.EXPAND)
        btn_sizer.AddSpacer(5)
        btn_sizer.Add(self.label_charges_btn, 0, wx.EXPAND)

        # pack elements
        n += 1
        grid.Add(unidec_plotting_weights_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.weight_list_choice, (n, 1), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.weight_list_sort, (n, 3), flag=wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL)
        n += 1
        grid.Add(charges_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.charges_check, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(adduct_choice, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.adduct_choice, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(unidec_charges_threshold_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.charges_threshold_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        n += 1
        grid.Add(unidec_charges_offset_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.charges_offset_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        n += 1
        grid.Add(btn_sizer, (n, 0), (1, n_col), flag=wx.ALIGN_CENTER_HORIZONTAL)

        return grid, n

    def on_toggle_controls(self, evt):
        """Event driven GUI updates"""

        CONFIG.unidec_peakWidth_auto = self.peak_width_auto_check.GetValue()
        obj_list = [self.fit_peak_width_value, self.peak_width_btn]
        for item in obj_list:
            item.Enable(enable=not CONFIG.unidec_peakWidth_auto)

        CONFIG.unidec_show_chargeStates = self.charges_check.GetValue()
        obj_list = [self.adduct_choice, self.charges_threshold_value, self.charges_offset_value, self.label_charges_btn]
        for item in obj_list:
            item.Enable(enable=CONFIG.unidec_show_chargeStates)

        if evt is not None:
            evt.Skip()

    def on_apply(self, evt):
        """Event driven GUI updates"""
        CONFIG.unidec_zStart = str2int(self.z_start_value.GetValue())
        CONFIG.unidec_zEnd = str2int(self.z_end_value.GetValue())
        CONFIG.unidec_mwStart = str2num(self.mw_start_value.GetValue())
        CONFIG.unidec_mwEnd = str2num(self.mw_end_value.GetValue())
        CONFIG.unidec_mwFrequency = str2num(self.mw_sample_frequency_value.GetValue())
        CONFIG.unidec_peakWidth = str2num(self.fit_peak_width_value.GetValue())
        CONFIG.unidec_peakFunction = self.peak_shape_func_choice.GetStringSelection()
        CONFIG.unidec_peakWidth_auto = self.peak_width_auto_check.GetValue()

        CONFIG.unidec_peakDetectionWidth = str2num(self.peak_width_value.GetValue())
        CONFIG.unidec_peakDetectionThreshold = str2num(self.peak_threshold_value.GetValue())
        CONFIG.unidec_peakNormalization = self.peak_normalization_choice.GetStringSelection()
        CONFIG.unidec_lineSeparation = str2num(self.line_separation_value.GetValue())

        CONFIG.unidec_show_markers = self.markers_check.GetValue()
        CONFIG.unidec_show_individualComponents = self.individual_line_check.GetValue()

        CONFIG.unidec_charges_label_charges = str2num(self.charges_threshold_value.GetValue())
        CONFIG.unidec_charges_offset = str2num(self.charges_offset_value.GetValue())
        CONFIG.unidec_show_chargeStates = self.charges_check.GetValue()

        if evt is not None:
            evt.Skip()

    def on_clear_plot_as_task(self, task):
        """Clear plots"""
        pass

        # if task in ["all", "load_data_and_preprocess_unidec", "preprocess_unidec"]:
        #     self.plotUnidec_MS.clear()
        #
        # if task in ["all", "load_data_and_preprocess_unidec", "preprocess_unidec", "run_unidec"]:
        #     self.plotUnidec_mzGrid.clear()
        #     self.plotUnidec_mwDistribution.clear()
        #     self.plotUnidec_mwVsZ.clear()
        #
        # if task in ["all", "load_data_and_preprocess_unidec", "preprocess_unidec", "detect", "run_unidec"]:
        #     self.plotUnidec_individualPeaks.clear()
        #     self.plotUnidec_barChart.clear()
        #     self.plotUnidec_chargeDistribution.clear()

    def on_page_changed(self, _evt):
        """Triggered by change of panel in the plot section"""
        # get current page
        self.current_page = self.plot_notebook.GetPageText(self.plot_notebook.GetSelection())
        view = self.get_view_from_name(self.current_page)
        pub.sendMessage("view.activate", view_id=view.PLOT_ID)

    def get_view_from_name(self, plot_name: str = None):
        """Retrieve view from name"""
        plot_dict = {
            "ms": self.view_ms,
            "mw": self.view_mw,
            "m/z vs charge": self.view_ms_grid,
            "mw vs charge": self.view_mw_grid,
            "isolated ms": self.view_peaks,
            "barchart": self.view_barchart,
            "charge distribution": self.view_charge,
        }
        if plot_name is None:
            plot_name = self.current_page
        plot_name = plot_name.lower()
        plot_obj = plot_dict.get(plot_name, None)
        if plot_obj is None:
            logger.error(f"Could not find view object with name `{plot_name}")
        return plot_obj

    def on_save_all_figures(self, evt):
        """Save all figures"""
        for view in [
            self.view_ms,
            self.view_mw,
            self.view_ms_grid,
            self.view_mw_grid,
            self.view_peaks,
            self.view_barchart,
            self.view_charge,
        ]:
            view.on_save_figure(evt)

    def on_open_customisation_settings(self, _evt):
        """Open UniDec customisation window"""
        from origami.widgets.unidec.dialog_customise_unidec_visuals import DialogCustomiseUniDecVisuals

        dlg = DialogCustomiseUniDecVisuals(self)
        dlg.ShowModal()

    def on_open_width_tool(self, _evt):
        """Open UniDec width tool"""
        from origami.widgets.unidec.panel_process_unidec_peak_width_tool import PanelPeakWidthTool

        # try:
        #     kwargs = {"xvals": CONFIG.unidec_engine.data.data2[:, 0], "yvals": CONFIG.unidec_engine.data.data2[:, 1]}
        # except IndexError:
        #     raise MessageError("Missing data", "Please pre-process data first")

        dlg = PanelPeakWidthTool(self, self.presenter, self.view, self.mz_obj)
        dlg.Show()

    def on_open_process_ms_settings(self, _evt):
        """Open MS pre-processing panel"""
        from origami.gui_elements.panel_process_spectrum import PanelProcessMassSpectrum

        panel = PanelProcessMassSpectrum(
            self.view, self.presenter, disable_plot=True, disable_process=True, update_widget=self.PUB_SUBSCRIBE_EVENT
        )
        panel.Show()

    def on_get_unidec_data(self):
        """Convenience function to retrieve UniDec data from the document"""
        # get data and document
        __, data = self.data_handling.get_spectrum_data([self.document_title, self.dataset_name])

        return data.get("unidec", None)

    def on_sort_unidec_mw(self, _evt):
        """Sort molecular weights"""
        if self._unidec_sort_column == 0:
            self._unidec_sort_column = 1
        else:
            self._unidec_sort_column = 0

        mass_list = self.weight_list_choice.GetItems()
        mass_list = unidec_utils.unidec_sort_MW_list(mass_list, self._unidec_sort_column)

        self.weight_list_choice.SetItems(mass_list)
        self.weight_list_choice.SetStringSelection(mass_list[0])

    def on_show_peaks_unidec(self, _evt):
        """Show peaks"""
        self.data_processing.on_threading("custom.action", ("show_peak_lines_and_markers",), fcn=self.on_plot)

    def on_process(self):
        """Process mass spectrum"""
        print("on_process", self)

    def on_plot_ms(self, _evt):
        """Plot mass spectrum"""
        self.view_ms.plot(obj=self.mz_obj)

    def on_plot(self, task):
        """Plot data"""
        # update settings first
        print("on_plot", task)
        self.on_apply(None)

    #
    #     # generate kwargs
    #     kwargs = {
    #         "show_markers": CONFIG.unidec_show_markers,
    #         "show_individual_lines": CONFIG.unidec_show_individualComponents,
    #         "speedy": CONFIG.unidec_speedy,
    #     }
    #
    #     try:
    #         # get data and plot in the panel
    #         data = self.on_get_unidec_data()
    #         if data:
    #             # called after `pre-processed` is executed
    #             if task in ["all", "preprocess_unidec", "load_data_and_preprocess_unidec"]:
    #                 replot_data = data.get("Processed", None)
    #                 if replot_data:
    #                     self.panel_plot.on_plot_unidec_MS(
    #                         replot=replot_data, plot=None, plot_obj=self.plotUnidec_MS, **kwargs
    #                     )
    #
    #             # called after `run unidec` is executed
    #             if task in ["all", "run_unidec"]:
    #                 replot_data = data.get("Fitted", None)
    #                 if replot_data:
    #                     self.panel_plot.on_plot_unidec_MS_v_Fit(
    #                         replot=replot_data, plot=None, plot_obj=self.plotUnidec_MS, **kwargs
    #                     )
    #                 replot_data = data.get("MW distribution", None)
    #                 if replot_data:
    #                     self.panel_plot.on_plot_unidec_mwDistribution(
    #                         replot=replot_data, plot=None, plot_obj=self.plotUnidec_mwDistribution, **kwargs
    #                     )
    #                 replot_data = data.get("m/z vs Charge", None)
    #                 if replot_data:
    #                     self.panel_plot.on_plot_unidec_mzGrid(
    #                         replot=replot_data, plot=None, plot_obj=self.plotUnidec_mzGrid, **kwargs
    #                     )
    #                 replot_data = data.get("MW vs Charge", None)
    #                 if replot_data:
    #                     self.panel_plot.on_plot_unidec_MW_v_Charge(
    #                         replot=replot_data, plot=None, plot_obj=self.plotUnidec_mwVsZ, **kwargs
    #                     )
    #
    #             # called after `detect peaks` is executed
    #             if task in ["all", "pick_peaks_unidec"]:
    #                 # update mass list
    #                 self.on_update_mass_list()
    #
    #                 replot_data = data.get("m/z with isolated species", None)
    #                 if replot_data:
    #                     self.panel_plot.on_plot_unidec_individualPeaks(
    #                         replot=replot_data, plot=None, plot_obj=self.plotUnidec_individualPeaks, **kwargs
    #                     )
    #                     self.on_plot_mw_normalization()
    #                     self.panel_plot.on_plot_unidec_MW_add_markers(
    #                         data["m/z with isolated species"],
    #                         data["MW distribution"],
    #                         plot=None,
    #                         plot_obj=self.plotUnidec_mwDistribution,
    #                         **kwargs,
    #                     )
    #                 replot_data = data.get("Barchart", None)
    #                 if replot_data:
    #                     self.panel_plot.on_plot_unidec_barChart(
    #                         replot=replot_data, plot=None, plot_obj=self.plotUnidec_barChart, **kwargs
    #                     )
    #                 replot_data = data.get("Charge information", None)
    #                 if replot_data is not None:
    #                     self.panel_plot.on_plot_unidec_ChargeDistribution(
    #                         replot=replot_data, plot=None, plot_obj=self.plotUnidec_chargeDistribution, **kwargs
    #                     )
    #
    #             # called after `show peaks` is exectured
    #             if task in ["show_peak_lines_and_markers"]:
    #                 replot_data = data.get("m/z with isolated species", None)
    #                 if replot_data:
    #                     self.panel_plot.on_plot_unidec_add_individual_lines_and_markers(
    #                         replot=replot_data, plot=None, plot_obj=self.plotUnidec_individualPeaks, **kwargs
    #                     )
    #                 else:
    #                     raise MessageError("Missing data", "Please detect peaks first")
    #
    #             # called after `isolate` is executed
    #             if task in ["isolate_mw_unidec"]:
    #                 mw_selection = "MW: {}".format(self.unidec_weightList_choice.GetStringSelection().split()[1])
    #                 kwargs["show_isolated_mw"] = True
    #                 kwargs["mw_selection"] = mw_selection
    #                 replot_data = data.get("m/z with isolated species", None)
    #                 if replot_data:
    #                     self.panel_plot.on_plot_unidec_add_individual_lines_and_markers(
    #                         replot=replot_data, plot=None, plot_obj=self.plotUnidec_individualPeaks, **kwargs
    #                     )
    #
    #             # show individual charge states
    #             if task in ["charge_states"]:
    #                 charges = data["Charge information"]
    #                 xvals = data["Processed"]["xvals"]
    #
    #                 mw_selection = self.unidec_weightList_choice.GetStringSelection().split()[1]
    #                 adduct_ion = self.unidec_adductMW_choice.GetStringSelection()
    #
    #                 peakpos, charges, __ = unidec_utils.calculate_charge_positions(
    #                     charges, mw_selection, xvals, adduct_ion, remove_below=CONFIG.unidec_charges_label_charges
    #                 )
    #                 self.panel_plot.on_plot_charge_states(
    #                     peakpos, charges, plot=None, plot_obj=self.plotUnidec_individualPeaks, **kwargs
    #                 )
    #
    #         # update peak width
    #         self.on_update_peak_width()
    #     except RuntimeError:
    #         logger.warning("The panel was closed before the action could be completed")

    def on_update_peak_width(self):
        """Update peak width"""
        self.fit_peak_width_value.SetValue(f"{CONFIG.unidec_engine.config.mzsig:.4f}")

    def on_plot_mw_normalization(self):
        """Trigger replot of the MW plot since the scaling might change"""
        # try:
        #     replot_data = dict(
        #         xvals=CONFIG.unidec_engine.data.massdat[:, 0], yvals=CONFIG.unidec_engine.data.massdat[:, 1]
        #     )
        # except IndexError:
        #     return
        #
        # if replot_data:
        #     self.panel_plot.on_plot_unidec_mwDistribution(
        #         replot=replot_data, plot=None, plot_obj=self.plotUnidec_mwDistribution
        #     )

    def on_initialize_unidec(self, _evt):
        """Initialize UniDec"""
        task = "load_data_and_preprocess_unidec"
        self.on_clear_plot_as_task(task)

        self.data_processing.on_run_unidec_fcn(self.dataset_name, task, call_after=True, fcn=self.on_plot, args=task)

    def on_process_unidec(self, _evt):
        """Process mass spectrum"""
        task = "preprocess_unidec"
        self.on_clear_plot_as_task(task)
        self.data_processing.on_run_unidec_fcn(self.dataset_name, task, call_after=True, fcn=self.on_plot, args=task)

    def on_run_unidec(self, _evt):
        """Run UniDec"""
        task = "run_unidec"
        self.on_clear_plot_as_task(task)
        self.data_processing.on_run_unidec_fcn(self.dataset_name, task, call_after=True, fcn=self.on_plot, args=task)

    def on_detect_peaks_unidec(self, _evt):
        """Detect features"""
        task = "pick_peaks_unidec"
        self.data_processing.on_run_unidec_fcn(self.dataset_name, task, call_after=True, fcn=self.on_plot, args=task)

    def on_all_unidec(self, _evt):
        """Run all"""
        self.data_processing.on_run_unidec_fcn(
            self.dataset_name, "run_all_unidec", call_after=True, fcn=self.on_plot, args="all"
        )

    def on_auto_unidec(self, _evt):
        """Auto UniDec"""
        self.data_processing.on_run_unidec_fcn(
            self.dataset_name, "auto_unidec", call_after=True, fcn=self.on_plot, args="all"
        )

    def on_isolate_peak_unidec(self, _evt):
        """Isolate peaks"""
        pass
        # self.on_plot("isolate_mw_unidec")
        # self.on_plot("charge_states")

    def on_show_charge_states_unidec(self, evt):
        """Show charge states"""
        print("on_show_charge_states_unidec", self)
        # self.on_plot("charge_states")

        if evt is not None:
            evt.Skip()

    def on_update_mass_list(self):
        """Update mass list"""
        data = self.on_get_unidec_data()
        data = data.get("m/z with isolated species", None)
        if data:
            mass_list, mass_max = data["_massList_"]
            self.weight_list_choice.SetItems(mass_list)
            self.weight_list_choice.SetStringSelection(mass_max)


def _main():
    from origami.icons.assets import Icons
    from origami.objects.containers.spectrum import MassSpectrumObject
    import numpy as np

    mz_obj = MassSpectrumObject(np.arange(1000), np.arange(1000))

    app = wx.App()
    icons = Icons()
    ex = PanelProcessUniDec(None, None, icons, mz_obj=mz_obj)
    ex.Show()
    app.MainLoop()


if __name__ == "__main__":
    _main()
