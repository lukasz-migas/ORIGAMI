"""Peak picking panel"""
# Standard library imports
import time
import logging

# Third-party imports
import wx
import numpy as np
import wx.lib.scrolledpanel as wxScrolledPanel
from pubsub import pub
from pubsub.core.topicexc import TopicNameError

# Local imports
from origami.styles import MiniFrame
from origami.styles import Validator
from origami.utils.screen import calculate_window_size
from origami.utils.system import running_under_pytest
from origami.config.config import CONFIG
from origami.utils.utilities import report_time
from origami.handlers.process import PROCESS_HANDLER
from origami.utils.converters import str2int
from origami.utils.converters import str2num
from origami.utils.exceptions import MessageError
from origami.config.environment import ENV
from origami.objects.containers import MassSpectrumObject
from origami.gui_elements.mixins import DatasetMixin
from origami.gui_elements.helpers import set_tooltip
from origami.gui_elements.helpers import make_checkbox
from origami.gui_elements.helpers import set_item_font
from origami.gui_elements.helpers import make_menu_item
from origami.gui_elements.helpers import make_bitmap_btn
from origami.gui_elements.misc_dialogs import DialogBox
from origami.processing.feature.mz_picker import MassSpectrumBasePicker
from origami.gui_elements.views.view_spectrum import ViewMassSpectrum

logger = logging.getLogger(__name__)


class PanelPeakPicker(MiniFrame, DatasetMixin):
    """Peak picking panel"""

    # module specific parameters
    PUB_SUBSCRIBE_EVENT = "widget.picker.update.spectrum"
    HELP_LINK = "https://origami.lukasz-migas.com/"
    PANEL_BASE_TITLE = "Peak Picker"

    # parameters
    _settings_panel_size = None

    # ui elements
    plot_view = None
    plot_panel = None
    plot_window = None
    resize_plot_check = None
    panel_book = None
    settings_native_local = None
    settings_native_differential = None
    settings_small = None
    settings_panel = None
    mz_limit_check = None
    mz_min_value = None
    mz_max_value = None
    visualize_scatter_check = None
    visualize_highlight_check = None
    visualize_show_labels_check = None
    visualize_max_labels = None
    visualize_show_labels_mz_check = None
    visualize_show_labels_int_check = None
    visualize_show_labels_width_check = None
    display_label = None
    find_peaks_btn = None
    plot_peaks_btn = None
    action_btn = None
    close_btn = None
    verbose_check = None
    threshold_value = None
    width_value = None
    relative_height_value = None
    min_intensity_value = None
    min_distance_value = None
    peak_width_modifier_value = None
    method_choice = None
    fit_local_threshold_value = None
    fit_local_window_value = None
    fit_local_relative_height = None
    fit_local_window_mz_spacing = None
    fit_differential_window_mz_spacing = None
    fit_differential_relative_height = None
    fit_differential_threshold_value = None
    fit_differential_window_value = None
    info_btn = None
    preprocess_check = None
    process_btn = None
    post_filter_choice = None
    post_score_choice = None
    post_filter_lower_value = None
    post_filter_upper_value = None
    post_filter_btn = None
    post_apply_btn = None
    post_refresh_btn = None

    def __init__(
        self, parent, presenter, icons, document_title: str = None, dataset_name: str = None, debug: bool = False
    ):
        """Initialize panel"""
        MiniFrame.__init__(self, parent, title="Peak picker...", style=wx.DEFAULT_FRAME_STYLE & ~wx.MAXIMIZE_BOX)
        t_start = time.time()

        self.parent = parent
        self.presenter = presenter
        self._icons = icons

        screen_size = wx.GetDisplaySize()
        if parent is not None:
            screen_size = self.parent.GetSize()
        self._display_size = screen_size
        self._display_resolution = wx.ScreenDC().GetPPI()

        self._window_size = calculate_window_size(self._display_size, [0.7, 0.8])

        # pre-allocate parameters#
        self._recompute_peaks = True
        self._peaks_dict = None
        self._labels = None
        self._show_smoothed_spectrum = True
        self._n_peaks_max = 1000
        self._mz_obj = None
        self._mz_picker = None
        self._mz_picker_filter = None
        self._debug = debug

        # setup kwargs
        self.document_title = document_title
        self.dataset_name = dataset_name

        # initialize gui
        self.make_gui()
        self.on_toggle_controls(None)

        # set title
        self.update_window_title()

        # bind events
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_CONTEXT_MENU, self.on_right_click)

        # trigger UI events
        self.on_plot(None)
        self.on_set_method(CONFIG.peak_panel_method_choice)
        # self.on_update_method(None)
        self.setup()

        # setup panel scrolling - this should only be done when running full application rather than when running
        # under pytest
        if not running_under_pytest():
            self.settings_panel.SetupScrolling(scroll_x=False)

        logger.info(f"Startup of peak picker took {report_time(t_start)}")

    def setup(self):
        """Setup various UI elements"""
        # restrict the widths of the elements
        self.post_filter_choice.SetMaxSize(self.post_filter_choice.GetSize())
        self.post_score_choice.SetMaxSize(self.post_score_choice.GetSize())
        self.post_filter_lower_value.SetMaxSize(self.post_filter_lower_value.GetSize())
        self.post_filter_upper_value.SetMaxSize(self.post_filter_upper_value.GetSize())

        # bind events
        self.process_btn.Bind(wx.EVT_BUTTON, self.on_open_process_ms_settings)
        if self.PUB_SUBSCRIBE_EVENT:
            pub.subscribe(self.on_process, self.PUB_SUBSCRIBE_EVENT)
        self._dataset_mixin_setup()

    @property
    def data_handling(self):
        """Return handle to `data_handling`"""
        return self.presenter.data_handling

    @property
    def document_tree(self):
        """Return handle to `document_tree`"""
        return self.presenter.view.panelDocuments.documents

    @property
    def panel_plot(self):
        """Return handle to `panel_plot`"""
        return self.presenter.view.panelPlots

    @property
    def ion_panel(self):
        """Return handle to `ion_panel"""
        return self.parent.panelMultipleIons

    @property
    def ion_list(self):
        """Return handle to `ion_list"""
        return self.ion_panel.peaklist

    @property
    def mz_obj(self) -> MassSpectrumObject:
        """Return `MassSpectrumObject`"""
        if self.document_title is not None:
            document = ENV[self.document_title]
            mz_obj = document[self.dataset_name, True]
            return mz_obj

    @property
    def mz_obj_cache(self) -> MassSpectrumObject:
        """Return `MassSpectrumObject` after it was pre-processed"""
        if self._mz_obj is None:
            self.mz_obj_cache = self.mz_obj
        return self._mz_obj

    @mz_obj_cache.setter
    def mz_obj_cache(self, value: MassSpectrumObject):
        """Set `mz_obj_cache`"""
        if value is None:
            return
        if not isinstance(value, MassSpectrumObject):
            raise ValueError("Incorrect data-type was being set to the `mz_obj_cache` attribute")
        self._mz_obj = value

    @property
    def mz_picker(self) -> MassSpectrumBasePicker:
        """Return `MassSpectrumObject` after it was pre-processed"""
        return self._mz_picker

    @mz_picker.setter
    def mz_picker(self, value: MassSpectrumBasePicker):
        """Set `mz_obj_cache`"""
        if value is None:
            return
        if not isinstance(value, MassSpectrumBasePicker):
            raise ValueError("Incorrect data type was being set to the `mz_picker` attribute")
        self._mz_picker = value

    @property
    def mz_picker_tmp(self) -> MassSpectrumBasePicker:
        """Return `MassSpectrumObject` after it was pre-processed"""
        return self._mz_picker_filter

    @mz_picker_tmp.setter
    def mz_picker_tmp(self, value: MassSpectrumBasePicker):
        """Set `mz_obj_cache`"""
        if value is None:
            self._mz_picker_filter = None
        if not isinstance(value, MassSpectrumBasePicker):
            raise ValueError("Incorrect data type was being set to the `mz_picker_tmp` attribute")
        self._mz_picker_filter = value

    def on_close(self, evt, force: bool = False):
        """Close window"""
        if self.mz_picker is not None and not force and not self._debug:
            dlg = DialogBox(
                title="Would you like to continue?",
                msg="There is a cached peak-picker in this window. Closing the window will remove it."
                "\nWould you like to continue?",
                kind="Question",
            )
            if dlg == wx.ID_NO:
                return

        try:
            if self.PUB_SUBSCRIBE_EVENT:
                pub.unsubscribe(self.on_process, self.PUB_SUBSCRIBE_EVENT)
        except TopicNameError:
            pass

        # unregister view
        pub.sendMessage("view.unregister", view_id=self.plot_view.PLOT_ID)

        # teardown dataset mixin
        self._dataset_mixin_teardown()

        try:
            self.document_tree._picker_panel = None
        except AttributeError:
            pass
        super(PanelPeakPicker, self).on_close(evt)

    def _check_active(self, query):
        """Check whether the currently open editor should be closed"""
        return all([self.document_title == query[0], self.dataset_name == query[1]])

    # noinspection DuplicatedCode
    def on_right_click(self, evt):
        """Right-click menu"""
        # ensure that user clicked inside the plot area
        if hasattr(evt.EventObject, "figure"):
            menu = self.plot_view.get_right_click_menu(self)
            menu.AppendSeparator()
            menu_plot_clear_labels = menu.Append(wx.ID_ANY, "Clear annotations")

            self.Bind(wx.EVT_MENU, self.on_clear_from_plot, menu_plot_clear_labels)

            self.PopupMenu(menu)
            menu.Destroy()
            self.SetFocus()

    # noinspection DuplicatedCode
    def on_action_tools(self, _evt):
        """Action menu"""

        menu = wx.Menu()

        menu_action_restore_original_plot = make_menu_item(
            parent=menu, text="Restore original plot", bitmap=self._icons.repaint
        )
        menu_action_add_peaks_to_peaklist = make_menu_item(
            parent=menu, text="Add peaks to peaklist panel", bitmap=self._icons.add
        )
        menu_action_add_peaks_to_annotations = make_menu_item(
            parent=menu, text="Add peaks to spectrum annotations", bitmap=self._icons.label
        )

        menu.Append(menu_action_restore_original_plot)
        menu.AppendSeparator()
        menu.Append(menu_action_add_peaks_to_peaklist)
        menu.Append(menu_action_add_peaks_to_annotations)

        # bind events
        self.Bind(wx.EVT_MENU, self.on_plot, menu_action_restore_original_plot)
        self.Bind(wx.EVT_MENU, self.on_add_to_peaklist, menu_action_add_peaks_to_peaklist)
        self.Bind(wx.EVT_MENU, self.on_add_to_annotations, menu_action_add_peaks_to_annotations)

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def on_set_method(self, method: str):
        """Set method"""
        page_id = {"native_local": 0, "native_differential": 1, "small_molecule": 2}.get(method, 0)
        self.panel_book.SetSelection(page_id)

    def on_update_method(self, _evt):
        """Update pick-picking method"""
        page = self.panel_book.GetPageText(self.panel_book.GetSelection())
        CONFIG.peak_panel_method_choice = {
            "Small molecule": "small_molecule",
            "Native MS (Local)": "native_local",
            "Native MS (Differential)": "native_differential",
        }[page]
        logger.debug(f"Changed peak picking method to `{CONFIG.peak_panel_method_choice}`")
        try:
            self.on_show_threshold_line(None)
        except IndexError:
            pass

    # noinspection DuplicatedCode
    def make_gui(self):
        """Make UI"""
        self.settings_panel = self.make_notebook(self)
        self._settings_panel_size = self.settings_panel.GetSize()

        self.plot_panel = self.make_plot_panel(self)

        # pack element
        main_sizer = wx.BoxSizer()
        main_sizer.Add(self.settings_panel, 1, wx.EXPAND, 0)
        main_sizer.Add(self.plot_panel, 2, wx.EXPAND, 0)

        # fit layout
        main_sizer.Fit(self)
        self.SetSize(self._window_size)
        self.SetSizer(main_sizer)

        self.Layout()
        self.CenterOnParent()
        self.SetFocus()

    def make_notebook(self, split_panel):
        """Make settings notebook"""
        panel = wxScrolledPanel.ScrolledPanel(split_panel, size=(-1, -1), name="main")

        # make pre-processing panel
        preprocess_panel = self.make_settings_panel_preprocess(panel)

        self.panel_book = wx.Choicebook(panel, wx.ID_ANY, style=wx.CHB_DEFAULT)
        self.panel_book.SetBackgroundColour((240, 240, 240))
        self.panel_book.Bind(wx.EVT_CHOICEBOOK_PAGE_CHANGED, self.on_update_method)

        # add peak-picking methods
        self.settings_native_local = self.make_settings_panel_native_local(self.panel_book)
        self.panel_book.AddPage(self.settings_native_local, "Native MS (Local)")

        self.settings_native_differential = self.make_settings_panel_native_differential(self.panel_book)
        self.panel_book.AddPage(self.settings_native_differential, "Native MS (Differential)")

        self.settings_small = self.make_settings_panel_small_molecule(self.panel_book)
        self.panel_book.AddPage(self.settings_small, "Small molecule")

        btn_sizer = self.make_settings_button(panel)

        postprocess_panel = self.make_settings_panel_postprocess(panel)

        # make common settings panel
        visualise_panel = self.make_settings_panel_visualise(panel)

        info_sizer = self.make_statusbar(panel)

        # pack settings panel
        settings_sizer = wx.BoxSizer(wx.VERTICAL)

        # pre-processing
        settings_sizer.Add(
            set_item_font(wx.StaticText(panel, wx.ID_ANY, "Pre-process")), 0, wx.EXPAND | wx.LEFT | wx.TOP, 10
        )
        settings_sizer.Add(preprocess_panel, 0, wx.EXPAND | wx.ALL, 10)
        settings_sizer.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND | wx.ALL, 0)

        # peak-picking
        settings_sizer.Add(
            set_item_font(wx.StaticText(panel, wx.ID_ANY, "Peak-picking settings")),
            0,
            wx.EXPAND | wx.LEFT | wx.BOTTOM,
            10,
        )
        settings_sizer.Add(self.panel_book, 0, wx.EXPAND | wx.ALL, 0)
        settings_sizer.AddSpacer(5)
        settings_sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)
        settings_sizer.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND | wx.ALL, 0)

        # filtering
        settings_sizer.Add(set_item_font(wx.StaticText(panel, wx.ID_ANY, "Filter peaks")), 0, wx.EXPAND | wx.LEFT, 10)
        settings_sizer.Add(postprocess_panel, 0, wx.EXPAND | wx.ALL, 10)
        settings_sizer.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND | wx.ALL, 0)

        # visualisation
        settings_sizer.Add(
            set_item_font(wx.StaticText(panel, wx.ID_ANY, "Visualize")), 0, wx.EXPAND | wx.LEFT | wx.TOP, 10
        )
        settings_sizer.Add(visualise_panel, 0, wx.EXPAND | wx.ALL, 10)

        # info
        settings_sizer.AddStretchSpacer()
        settings_sizer.Add(info_sizer, 0, wx.EXPAND, 10)
        settings_sizer.Fit(panel)
        settings_sizer.SetMinSize((380, -1))
        panel.SetSizerAndFit(settings_sizer)

        return panel

    def make_settings_button(self, panel):
        """Make sub-section that contains the peak-picking button"""

        # make peak-picking button
        self.find_peaks_btn = wx.Button(panel, wx.ID_OK, "Find peaks", size=(-1, -1))
        self.find_peaks_btn.Bind(wx.EVT_BUTTON, self.on_find_peaks)
        self.verbose_check = make_checkbox(
            panel, "Verbose", tooltip="When checked, more logging information will be printed to the console."
        )
        self.verbose_check.SetValue(CONFIG.peak_panel_verbose)
        self.verbose_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        sizer = wx.BoxSizer()
        sizer.Add(self.find_peaks_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer.AddSpacer(5)
        sizer.Add(self.verbose_check, 0, wx.ALIGN_CENTER_VERTICAL)

        return sizer

    # noinspection DuplicatedCode
    def make_settings_panel_preprocess(self, split_panel):
        """Make panel that handles pre-processing steps before peak picking"""
        panel = wx.Panel(split_panel, -1, size=(-1, -1), name="settings")

        self.mz_limit_check = make_checkbox(
            panel,
            "Specify peak picking mass range",
            tooltip="Specify the mass range where you would like the peak-picker to focus on.",
        )
        self.mz_limit_check.SetValue(CONFIG.peak_panel_specify_mz)
        self.mz_limit_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.mz_limit_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        mz_min_value = wx.StaticText(panel, wx.ID_ANY, "m/z start:")
        self.mz_min_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("floatPos"))
        # self.mz_min_value.SetValue(str(self._mz_xrange[0]))
        self.mz_min_value.Bind(wx.EVT_TEXT, self.on_apply)

        mz_max_value = wx.StaticText(panel, wx.ID_ANY, "-")
        self.mz_max_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("floatPos"))
        # self.mz_max_value.SetValue(str(self._mz_xrange[1]))
        self.mz_max_value.Bind(wx.EVT_TEXT, self.on_apply)

        self.preprocess_check = make_checkbox(panel, "Pre-process", tooltip="Enable pre-processing before plotting")
        self.preprocess_check.SetValue(CONFIG.peak_panel_preprocess)
        self.preprocess_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.preprocess_check.Bind(wx.EVT_CHECKBOX, self.on_plot)

        self.process_btn = make_bitmap_btn(
            panel, -1, self._icons.process_ms, tooltip="Change MS pre-processing parameters"
        )

        sizer = wx.BoxSizer()
        sizer.Add(self.mz_min_value, 1, wx.EXPAND)
        sizer.AddSpacer(5)
        sizer.Add(mz_max_value, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer.AddSpacer(5)
        sizer.Add(self.mz_max_value, 1, wx.EXPAND)

        # visualize grid
        grid = wx.GridBagSizer(5, 5)
        n = 0
        grid.Add(self.mz_limit_check, (n, 0), (1, 2), flag=wx.EXPAND)
        n += 1
        grid.Add(mz_min_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(sizer, (n, 1), (1, 3), flag=wx.EXPAND)
        n += 1
        grid.Add(self.preprocess_check, (n, 0), (1, 1), flag=wx.EXPAND)
        grid.Add(self.process_btn, (n, 1), (1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.AddGrowableCol(n, 1)

        # fit layout
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.EXPAND, 0)
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    # noinspection DuplicatedCode
    def make_settings_panel_postprocess(self, split_panel):
        """Make settings panel that controls post-processing (e.g. peak filtering)"""
        panel = wx.Panel(split_panel, -1, size=(-1, -1), name="settings")

        filter_value = wx.StaticText(panel, wx.ID_ANY, "Filter-by:")
        self.post_filter_choice = wx.ComboBox(panel, choices=CONFIG.peak_panel_filter_choices, style=wx.CB_READONLY)
        self.post_filter_choice.SetStringSelection(CONFIG.peak_panel_filter)
        self.post_filter_choice.Bind(wx.EVT_COMBOBOX, self.on_toggle_controls)
        self.post_filter_choice.Bind(wx.EVT_COMBOBOX, self.on_refresh_lower_upper_bounds)
        set_tooltip(
            self.post_filter_choice,
            "Select filtering method. "
            "\nScores - filter peaks using one of the scoring methods selected below"
            "\nWidth (Da) - filter peaks using peak widths defined in Da"
            "\nWidth (no. bins) - filter peaks using peak widths defined in number of points",
        )

        self.post_refresh_btn = make_bitmap_btn(
            panel,
            -1,
            self._icons.reload,
            tooltip="Refresh the lower and upper bounds for the currently selected filter method.",
        )
        self.post_refresh_btn.Bind(wx.EVT_BUTTON, self.on_refresh_lower_upper_bounds)

        score_value = wx.StaticText(panel, wx.ID_ANY, "Score:")
        self.post_score_choice = wx.ComboBox(panel, choices=CONFIG.peak_panel_score_choices, style=wx.CB_READONLY)
        self.post_score_choice.SetStringSelection(CONFIG.peak_panel_score)
        set_tooltip(
            self.post_score_choice,
            "Select scoring method."
            "\nAsymmetry - measures the peak asymmetricity"
            "\nTailing - measures the peak tailing"
            "\nSlopes - measures the left/right side slopes of the peak",
        )

        criteria_value = wx.StaticText(panel, wx.ID_ANY, "Criteria:")
        self.post_filter_lower_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("floatPos"))
        self.post_filter_lower_value.Bind(wx.EVT_TEXT, self.on_apply)
        set_tooltip(self.post_filter_lower_value, "Set lower bound of the selection criteria. Values are inclusive.")

        upper_value = wx.StaticText(panel, wx.ID_ANY, "-")
        self.post_filter_upper_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("floatPos"))
        self.post_filter_upper_value.Bind(wx.EVT_TEXT, self.on_apply)
        set_tooltip(self.post_filter_upper_value, "Set upper bound of the selection criteria. Values are inclusive.")

        self.post_filter_btn = wx.Button(panel, wx.ID_OK, "View", size=(-1, -1))
        self.post_filter_btn.Bind(wx.EVT_BUTTON, self.on_view_filter)
        set_tooltip(
            self.post_filter_btn,
            "Click on this button to view the changes. Filter criteria will NOT be applied to the peak picker.",
        )

        self.post_apply_btn = wx.Button(panel, wx.ID_OK, "Apply", size=(-1, -1))
        self.post_apply_btn.Bind(wx.EVT_BUTTON, self.on_apply_filter)
        set_tooltip(
            self.post_apply_btn,
            "Click on this button to view the changes. Filter criteria WILL be applied to the peak picker.",
        )

        # data grid
        btn_sizer = wx.BoxSizer()
        btn_sizer.Add(self.post_filter_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        btn_sizer.AddSpacer(5)
        btn_sizer.Add(self.post_apply_btn, 0, wx.ALIGN_CENTER_VERTICAL)

        sizer = wx.BoxSizer()
        sizer.Add(self.post_filter_lower_value, 1, wx.EXPAND)
        sizer.AddSpacer(5)
        sizer.Add(upper_value, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer.AddSpacer(5)
        sizer.Add(self.post_filter_upper_value, 1, wx.EXPAND)

        # visualize grid
        grid = wx.GridBagSizer(5, 5)
        n = 0
        grid.Add(filter_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.post_filter_choice, (n, 1), (1, 3), flag=wx.EXPAND)
        grid.Add(self.post_refresh_btn, (n, 4), (1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n += 1
        grid.Add(score_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.post_score_choice, (n, 1), (1, 3), flag=wx.EXPAND)
        n += 1
        grid.Add(criteria_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(sizer, (n, 1), (1, 3), flag=wx.EXPAND | wx.ALL)
        grid.AddGrowableCol(1, 1)

        # fit layout
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 1, wx.EXPAND)
        main_sizer.AddSpacer(10)
        main_sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL)
        main_sizer.Fit(panel)

        panel.SetSizerAndFit(main_sizer)

        return panel

    # noinspection DuplicatedCode
    def make_settings_panel_visualise(self, split_panel):
        """Make settings panel"""
        panel = wx.Panel(split_panel, -1, size=(-1, -1), name="settings")

        self.visualize_scatter_check = make_checkbox(
            panel,
            "Show scatter points",
            tooltip="When checked, scatter points are shown in the plot area to indicate the peak position",
        )
        self.visualize_scatter_check.SetValue(CONFIG.peak_panel_scatter)
        self.visualize_scatter_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.visualize_scatter_check.Bind(wx.EVT_CHECKBOX, self.on_annotate_spectrum_with_scatter)

        self.visualize_highlight_check = make_checkbox(
            panel,
            "Highlight with patch",
            tooltip="When checked, rectangular patch will be shown to indicate the peak position as well as its width",
        )
        self.visualize_highlight_check.SetValue(CONFIG.peak_panel_highlight)
        self.visualize_highlight_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.visualize_highlight_check.Bind(wx.EVT_CHECKBOX, self.on_annotate_spectrum_with_patches)

        self.visualize_show_labels_check = make_checkbox(
            panel,
            "Show labels on plot",
            tooltip="When checked, label associated with the peak will be shown in the plot area.",
        )
        self.visualize_show_labels_check.SetValue(CONFIG.peak_panel_labels)
        self.visualize_show_labels_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.visualize_show_labels_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)
        self.visualize_show_labels_check.Bind(wx.EVT_CHECKBOX, self.on_annotate_spectrum_with_labels)

        visualize_max_labels = wx.StaticText(panel, wx.ID_ANY, "Max no. labels / patches:")
        self.visualize_max_labels = wx.SpinCtrlDouble(
            panel,
            -1,
            value=str(CONFIG.peak_panel_labels_max_count),
            min=0,
            max=1000,
            initial=CONFIG.peak_panel_labels_max_count,
            inc=50,
            size=(90, -1),
        )
        set_tooltip(
            self.visualize_max_labels,
            "Set the maximum number of labels and patches/highlights that will be displayed in the plot. "
            "Setting this value too high (>500) can seriously harm the performance.",
        )
        self.visualize_max_labels.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        self.visualize_show_labels_mz_check = make_checkbox(
            panel, "m/z", tooltip="When checked, the m/z value of the found peak will be shown in the label."
        )
        self.visualize_show_labels_mz_check.SetValue(CONFIG.peak_panel_labels_mz)
        self.visualize_show_labels_mz_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.visualize_show_labels_mz_check.Bind(wx.EVT_CHECKBOX, self.on_annotate_spectrum_with_labels)

        self.visualize_show_labels_int_check = make_checkbox(
            panel,
            "intensity",
            tooltip="When checked, the intensity value of the found peak will be shown in the label.",
        )
        self.visualize_show_labels_int_check.SetValue(CONFIG.peak_panel_labels_int)
        self.visualize_show_labels_int_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.visualize_show_labels_int_check.Bind(wx.EVT_CHECKBOX, self.on_annotate_spectrum_with_labels)

        self.visualize_show_labels_width_check = make_checkbox(
            panel, "width", tooltip="When checked, the width value of the found peak will be shown in the label."
        )
        self.visualize_show_labels_width_check.SetValue(CONFIG.peak_panel_labels_width)
        self.visualize_show_labels_width_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.visualize_show_labels_width_check.Bind(wx.EVT_CHECKBOX, self.on_annotate_spectrum_with_labels)

        self.plot_peaks_btn = wx.Button(panel, wx.ID_OK, "Plot peaks", size=(-1, -1))
        self.plot_peaks_btn.Bind(wx.EVT_BUTTON, self.on_annotate_spectrum)

        self.action_btn = wx.Button(panel, wx.ID_OK, "Action ▼", size=(-1, -1))
        self.action_btn.Bind(wx.EVT_BUTTON, self.on_action_tools)

        # visualize grid
        settings_grid = wx.GridBagSizer(5, 5)
        n = 0
        settings_grid.Add(self.visualize_scatter_check, (n, 0), (1, 1), flag=wx.EXPAND)
        n += 1
        settings_grid.Add(self.visualize_highlight_check, (n, 0), (1, 1), flag=wx.EXPAND)
        n += 1
        settings_grid.Add(self.visualize_show_labels_check, (n, 0), (1, 1), flag=wx.EXPAND)
        settings_grid.Add(self.visualize_show_labels_mz_check, (n, 1), flag=wx.EXPAND)
        settings_grid.Add(self.visualize_show_labels_int_check, (n, 2), flag=wx.EXPAND)
        settings_grid.Add(self.visualize_show_labels_width_check, (n, 3), flag=wx.EXPAND)
        n += 1
        settings_grid.Add(visualize_max_labels, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        settings_grid.Add(self.visualize_max_labels, (n, 1), flag=wx.EXPAND)

        # data grid
        btn_sizer = wx.BoxSizer()
        btn_sizer.Add(self.plot_peaks_btn)
        btn_sizer.Add(self.action_btn)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(settings_grid, 0, wx.EXPAND)
        main_sizer.AddSpacer(10)
        main_sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL)

        main_sizer.Fit(panel)

        panel.SetSizerAndFit(main_sizer)

        return panel

    # noinspection DuplicatedCode
    def make_settings_panel_small_molecule(self, split_panel):
        """Make settings panel for small molecule peak picking"""

        panel = wx.Panel(split_panel, -1, size=(-1, -1), name="small_molecules")

        threshold_value = wx.StaticText(panel, wx.ID_ANY, "Threshold:")
        self.threshold_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("floatPos"))
        self.threshold_value.SetValue(str(CONFIG.peak_property_threshold))
        self.threshold_value.Bind(wx.EVT_TEXT, self.on_apply)

        width_value = wx.StaticText(panel, wx.ID_ANY, "Minimal width:")
        self.width_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("intPos"))
        self.width_value.SetValue(str(CONFIG.peak_property_width))
        self.width_value.Bind(wx.EVT_TEXT, self.on_apply)

        relative_height_value = wx.StaticText(panel, wx.ID_ANY, "Peak width at rel. height:")
        self.relative_height_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("floatPos"))
        self.relative_height_value.SetValue(str(CONFIG.peak_property_relative_height))
        self.relative_height_value.Bind(wx.EVT_TEXT, self.on_apply)
        set_tooltip(
            self.relative_height_value,
            "Specify the relative height at which to measure the peak width. The larger the value, the wider the peak "
            " becomes as width is measured closer to the base.\nValues should be between 0.-1.",
        )

        min_intensity_value = wx.StaticText(panel, wx.ID_ANY, "Minimal intensity:")
        self.min_intensity_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("floatPos"))
        self.min_intensity_value.SetValue(str(CONFIG.peak_property_min_intensity))
        self.min_intensity_value.Bind(wx.EVT_TEXT, self.on_apply)
        self.min_intensity_value.Bind(wx.EVT_TEXT, self.on_show_threshold_line)

        min_distance_value = wx.StaticText(panel, wx.ID_ANY, "Min. distance between peaks:")
        self.min_distance_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("intPos"))
        self.min_distance_value.SetValue(str(CONFIG.peak_property_distance))
        self.min_distance_value.Bind(wx.EVT_TEXT, self.on_apply)

        peak_width_modifier_value = wx.StaticText(panel, wx.ID_ANY, "Peak width modifier:")
        self.peak_width_modifier_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("floatPos"))
        self.peak_width_modifier_value.SetValue(str(CONFIG.peak_property_peak_width_modifier))
        self.peak_width_modifier_value.Bind(wx.EVT_TEXT, self.on_apply)

        # pack elements
        grid = wx.GridBagSizer(5, 5)
        n = 0
        grid.Add(threshold_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.threshold_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(width_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.width_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(relative_height_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.relative_height_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(min_intensity_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.min_intensity_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(min_distance_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.min_distance_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(peak_width_modifier_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.peak_width_modifier_value, (n, 1), flag=wx.EXPAND)
        n += 1

        # fit layout
        main_sizer = wx.BoxSizer()
        main_sizer.Add(grid, 0, wx.FIXED_MINSIZE, 0)
        main_sizer.Fit(panel)

        panel.SetSizerAndFit(main_sizer)

        return panel

    # noinspection DuplicatedCode
    def make_settings_panel_native_local(self, split_panel):
        """Make settings panel for native MS peak picking"""
        panel = wx.Panel(split_panel, -1, size=(-1, -1), name="native-local")

        threshold_label = wx.StaticText(panel, wx.ID_ANY, "Threshold:")
        self.fit_local_threshold_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("floatPos"))
        self.fit_local_threshold_value.SetValue(str(CONFIG.peak_local_threshold))
        self.fit_local_threshold_value.Bind(wx.EVT_TEXT, self.on_apply)
        self.fit_local_threshold_value.Bind(wx.EVT_TEXT, self.on_show_threshold_line)

        window_label = wx.StaticText(panel, wx.ID_ANY, "Window size (points):")
        self.fit_local_window_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("intPos"))
        self.fit_local_window_value.SetValue(str(CONFIG.peak_local_window))
        self.fit_local_window_value.Bind(wx.EVT_TEXT, self.on_apply)
        self.fit_local_window_value.Bind(wx.EVT_TEXT, self.on_show_window_size_in_mz)

        self.fit_local_window_mz_spacing = wx.StaticText(panel, wx.ID_ANY, "")

        fit_relative_height = wx.StaticText(panel, wx.ID_ANY, "Peak width at rel. height:")
        self.fit_local_relative_height = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("floatPos"))
        self.fit_local_relative_height.SetValue(str(CONFIG.peak_local_relative_height))
        self.fit_local_relative_height.Bind(wx.EVT_TEXT, self.on_apply)
        set_tooltip(
            self.fit_local_relative_height,
            "Specify the relative height at which to measure the peak width. The larger the value, the wider the peak "
            " becomes as width is measured closer to the base.\nValues should be between 0.-1.",
        )

        # pack elements
        grid = wx.GridBagSizer(5, 5)
        n = 0
        grid.Add(threshold_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.fit_local_threshold_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(window_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.fit_local_window_value, (n, 1), flag=wx.EXPAND)
        grid.Add(self.fit_local_window_mz_spacing, (n, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        n += 1
        grid.Add(fit_relative_height, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.fit_local_relative_height, (n, 1), flag=wx.EXPAND)

        # fit layout
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 0, wx.EXPAND, 0)
        main_sizer.Fit(panel)

        panel.SetSizerAndFit(main_sizer)

        return panel

    # noinspection DuplicatedCode
    def make_settings_panel_native_differential(self, split_panel):
        """Make settings panel for native MS peak picking"""
        panel = wx.Panel(split_panel, -1, size=(-1, -1), name="native-differential")

        threshold_label = wx.StaticText(panel, wx.ID_ANY, "Threshold:")
        self.fit_differential_threshold_value = wx.TextCtrl(
            panel, -1, "", size=(-1, -1), validator=Validator("floatPos")
        )
        self.fit_differential_threshold_value.SetValue(str(CONFIG.peak_differential_threshold))
        self.fit_differential_threshold_value.Bind(wx.EVT_TEXT, self.on_apply)
        self.fit_differential_threshold_value.Bind(wx.EVT_TEXT, self.on_show_threshold_line)

        window_label = wx.StaticText(panel, wx.ID_ANY, "Window size (points):")
        self.fit_differential_window_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), validator=Validator("intPos"))
        self.fit_differential_window_value.SetValue(str(CONFIG.peak_differential_window))
        self.fit_differential_window_value.Bind(wx.EVT_TEXT, self.on_apply)
        self.fit_differential_window_value.Bind(wx.EVT_TEXT, self.on_show_window_size_in_mz)

        self.fit_differential_window_mz_spacing = wx.StaticText(panel, wx.ID_ANY, "")

        fit_relative_height = wx.StaticText(panel, wx.ID_ANY, "Peak width at rel. height:")
        self.fit_differential_relative_height = wx.TextCtrl(
            panel, -1, "", size=(-1, -1), validator=Validator("floatPos")
        )
        self.fit_differential_relative_height.SetValue(str(CONFIG.peak_differential_relative_height))
        self.fit_differential_relative_height.Bind(wx.EVT_TEXT, self.on_apply)
        set_tooltip(
            self.fit_differential_relative_height,
            "Specify the relative height at which to measure the peak width. The larger the value, the wider the peak "
            " becomes as width is measured closer to the base.\nValues should be between 0.-1.",
        )

        # pack elements
        grid = wx.GridBagSizer(5, 5)
        n = 0
        grid.Add(threshold_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.fit_differential_threshold_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(window_label, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.fit_differential_window_value, (n, 1), flag=wx.EXPAND)
        grid.Add(self.fit_differential_window_mz_spacing, (n, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        n += 1
        grid.Add(fit_relative_height, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.fit_differential_relative_height, (n, 1), flag=wx.EXPAND)

        # fit layout
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 0, wx.EXPAND, 0)
        main_sizer.Fit(panel)

        panel.SetSizerAndFit(main_sizer)

        return panel

    # noinspection DuplicatedCode
    def make_plot_panel(self, split_panel):
        """Make plot panel"""
        pixel_size = [(self._window_size[0] - self._settings_panel_size[0] - 50), (self._window_size[1] - 50)]
        figsize = [pixel_size[0] / self._display_resolution[0], pixel_size[1] / self._display_resolution[1]]

        self.plot_view = ViewMassSpectrum(
            split_panel, figsize, x_label="m/z (Da)", y_label="Intensity", filename="picked-mass-spectrum"
        )
        self.plot_window = self.plot_view.figure

        return self.plot_view.panel

    # noinspection DuplicatedCode
    def on_apply(self, evt):
        """Event driven configuration updates"""
        # Small-molecule peak finder
        CONFIG.peak_property_threshold = str2num(self.threshold_value.GetValue())
        CONFIG.peak_property_width = str2int(self.width_value.GetValue())
        CONFIG.peak_property_relative_height = str2num(self.relative_height_value.GetValue())
        CONFIG.peak_property_min_intensity = str2num(self.min_intensity_value.GetValue())
        CONFIG.peak_property_distance = str2int(self.min_distance_value.GetValue())
        CONFIG.peak_property_peak_width_modifier = str2num(self.peak_width_modifier_value.GetValue())

        # Native local-max
        CONFIG.peak_local_threshold = str2num(self.fit_local_threshold_value.GetValue())
        CONFIG.peak_local_window = str2int(self.fit_local_window_value.GetValue())
        CONFIG.peak_local_relative_height = str2num(self.fit_local_relative_height.GetValue())

        # Native differential
        CONFIG.peak_differential_threshold = str2num(self.fit_differential_threshold_value.GetValue())
        CONFIG.peak_differential_window = str2int(self.fit_differential_window_value.GetValue())
        CONFIG.peak_differential_relative_height = str2num(self.fit_differential_relative_height.GetValue())

        # Panel-specific
        CONFIG.peak_panel_specify_mz = self.mz_limit_check.GetValue()
        CONFIG.peak_panel_preprocess = self.preprocess_check.GetValue()
        CONFIG.peak_panel_mz_start = str2num(self.mz_min_value.GetValue())
        CONFIG.peak_panel_mz_end = str2num(self.mz_max_value.GetValue())
        CONFIG.peak_panel_verbose = self.verbose_check.GetValue()
        CONFIG.peak_panel_scatter = self.visualize_scatter_check.GetValue()
        CONFIG.peak_panel_highlight = self.visualize_highlight_check.GetValue()
        CONFIG.peak_panel_labels = self.visualize_show_labels_check.GetValue()
        CONFIG.peak_panel_labels_max_count = str2int(self.visualize_max_labels.GetValue())
        CONFIG.peak_panel_labels_mz = self.visualize_show_labels_mz_check.GetValue()
        CONFIG.peak_panel_labels_int = self.visualize_show_labels_int_check.GetValue()
        CONFIG.peak_panel_labels_width = self.visualize_show_labels_width_check.GetValue()

        if evt is not None:
            evt.Skip()

    def on_show_window_size_in_mz(self, evt):
        """Display m/z spacing in the UI"""
        if CONFIG.peak_panel_method_choice == "native_local":
            mz_bins = str2int(self.fit_local_window_value.GetValue(), 0) * self.mz_obj_cache.x_spacing
            self.fit_local_window_mz_spacing.SetLabel(f"{mz_bins:.4f} Da")
        elif CONFIG.peak_panel_method_choice == "native_differential":
            mz_bins = str2int(self.fit_differential_window_value.GetValue(), 0) * self.mz_obj_cache.x_spacing
            self.fit_differential_window_mz_spacing.SetLabel(f"{mz_bins:.4f} Da")

        if evt is not None:
            evt.Skip()

    def on_show_threshold_line(self, evt):
        """Display a horizontal line indicating the minimal intensity that will be picked"""
        if CONFIG.peak_panel_method_choice == "small_molecule":
            threshold = str2num(self.min_intensity_value.GetValue())
        elif CONFIG.peak_panel_method_choice == "native_local":
            threshold = str2num(self.fit_local_threshold_value.GetValue())
        else:
            threshold = str2num(self.fit_differential_threshold_value.GetValue())

        if self.mz_obj_cache:
            _, y_max = self.mz_obj_cache.y_limit

            # if threshold is below 1, we assume that its meant to be a proportion
            if threshold is None:
                return

            if threshold <= 1:
                threshold = y_max * threshold

            self.plot_view.add_h_line(threshold)

        if evt is not None:
            evt.Skip()

    def on_toggle_controls(self, evt):
        """Event driven GUI updates"""
        # mass range controls
        CONFIG.peak_panel_specify_mz = self.mz_limit_check.GetValue()
        self.mz_min_value.Enable(CONFIG.peak_panel_specify_mz)
        self.mz_max_value.Enable(CONFIG.peak_panel_specify_mz)

        # labels controls
        CONFIG.peak_panel_labels = self.visualize_show_labels_check.GetValue()
        self.visualize_show_labels_int_check.Enable(CONFIG.peak_panel_labels)
        self.visualize_show_labels_mz_check.Enable(CONFIG.peak_panel_labels)
        self.visualize_show_labels_width_check.Enable(CONFIG.peak_panel_labels)

        # filtering
        CONFIG.peak_panel_filter = self.post_filter_choice.GetStringSelection()
        self.post_score_choice.Enable(CONFIG.peak_panel_filter == "Score")

        if evt is not None:
            evt.Skip()

    def on_find_peaks(self, _evt):
        """Detect peaks in the spectrum"""
        t_start = time.time()
        logger.info("Started peak picking...")
        self.display_label.SetLabel("Started peak picking...")

        mz_obj = self.mz_obj_cache
        mz_min, mz_max = None, None
        if CONFIG.peak_panel_specify_mz:
            mz_min = CONFIG.peak_panel_mz_start
            mz_max = CONFIG.peak_panel_mz_end

        mz_picker = None
        if CONFIG.peak_panel_method_choice not in CONFIG.peak_panel_method_choices:
            raise ValueError(f"Incorrect method - `{CONFIG.peak_panel_method_choice}`")

        if CONFIG.peak_panel_method_choice == "small_molecule":
            mz_picker = PROCESS_HANDLER.find_peaks_in_mass_spectrum_peak_properties(
                mz_obj,
                pick_mz_min=mz_min,
                pick_mz_max=mz_max,
                threshold=CONFIG.peak_property_threshold,
                distance=CONFIG.peak_property_distance,
                width=CONFIG.peak_property_width,
                rel_height=CONFIG.peak_property_relative_height,
                min_intensity=CONFIG.peak_property_min_intensity,
                peak_width_modifier=CONFIG.peak_property_peak_width_modifier,
            )
        elif CONFIG.peak_panel_method_choice == "native_differential":
            mz_picker = PROCESS_HANDLER.find_peaks_in_mass_spectrum_peakutils(
                mz_obj,
                pick_mz_min=mz_min,
                pick_mz_max=mz_max,
                window=CONFIG.peak_differential_window,
                threshold=CONFIG.peak_differential_threshold,
                rel_height=CONFIG.peak_differential_relative_height,
            )
        elif CONFIG.peak_panel_method_choice == "native_local":
            mz_picker = PROCESS_HANDLER.find_peaks_in_mass_spectrum_local_max(
                mz_obj,
                pick_mz_min=mz_min,
                pick_mz_max=mz_max,
                window=CONFIG.peak_local_window,
                threshold=CONFIG.peak_local_threshold,
                rel_height=CONFIG.peak_local_relative_height,
            )

        # post-process the peaks
        mz_picker.sort_by_y()
        self.mz_picker = mz_picker
        logger.info(f"Picked peaks in {report_time(t_start)}")
        self.display_label.SetLabel(f"Found {mz_picker.n_peaks} peaks")

        # update plot area
        self.on_annotate_spectrum(None)
        self.on_refresh_lower_upper_bounds(None)

    def on_plot(self, _evt):
        """Plot mass spectrum"""
        CONFIG.peak_panel_preprocess = self.preprocess_check.GetValue()

        mz_obj = self.mz_obj
        if mz_obj is None:
            return
        if CONFIG.peak_panel_preprocess:
            PROCESS_HANDLER.on_process_ms(mz_obj)
        self.mz_obj_cache = mz_obj

        self.plot_view.plot(obj=mz_obj)
        self.on_show_threshold_line(None)

    def on_process(self):
        """Process spectrum"""
        if CONFIG.peak_panel_preprocess:
            self.on_plot(None)
        else:
            dlg = DialogBox(
                "Warning",
                (
                    "Changing pre-processing parameters has no effect - the setting is disabled. "
                    "Would you like to turn it on?"
                ),
                "Question",
            )
            if dlg == wx.ID_YES:
                self.preprocess_check.SetValue(True)
                CONFIG.peak_panel_preprocess = True

    def _on_get_filtered_picker(self):
        """Retrieve filtered picker"""
        criteria = self.post_filter_choice.GetStringSelection()
        criteria = {"Score": "score", "Width (no. bins)": "idx_fwhm", "Width (Da)": "x_fwhm"}[criteria]
        metric = self.post_score_choice.GetStringSelection()

        mz_picker = self.mz_picker
        if mz_picker is None:
            raise MessageError("Error", "Please pick peaks first! Click on the `Find peaks` button.")

        # score peak values
        if criteria == "score":
            mz_picker.score(metric)

        return mz_picker, criteria

    def on_view_filter(self, evt):
        """View found peaks after they've been filtered"""
        lower = str2num(self.post_filter_lower_value.GetValue())
        upper = str2num(self.post_filter_upper_value.GetValue())

        mz_picker, criteria = self._on_get_filtered_picker()

        mz_picker_tmp = mz_picker.filter_by(criteria, [lower, upper])
        self.mz_picker_tmp = mz_picker_tmp
        self.on_annotate_spectrum(None, mz_picker_tmp)

        if evt is not None:
            evt.Skip()

    def on_apply_filter(self, _evt):
        """Apply filtering and set the filtered peak-picker as the default"""
        mz_picker_tmp = self.mz_picker_tmp
        if mz_picker_tmp is None:
            raise MessageError("Error", "Please filter peaks first. Select criteria and click on `Filter` first.")

        self.mz_picker = mz_picker_tmp

    #         self.mz_picker_tmp = None

    def on_refresh_lower_upper_bounds(self, evt):
        """Update the lower/upper bounds of the filtering step"""
        try:
            mz_picker, criteria = self._on_get_filtered_picker()

            # score peak values
            if criteria == "score":
                values = mz_picker.scores
            elif criteria == "idx_fwhm":
                values = mz_picker.idx_width
            else:
                values = mz_picker.x_width
        except ValueError:
            values = []
            logger.warning("Could not compute filtering ranges.")

        if len(values) == 0:
            values = np.asarray([0, 0])

        min_val = f"{values.min()-0.0001:.4f}"  # noqa
        self.post_filter_lower_value.SetValue(min_val)

        max_val = f"{values.max()+0.0001:.4f}"  # noqa
        self.post_filter_upper_value.SetValue(max_val)

        if evt is not None:
            evt.Skip()

    def on_annotate_spectrum(self, _evt, mz_picker: MassSpectrumBasePicker = None):
        """Highlight peaks in the spectrum"""
        if mz_picker is None:
            mz_picker = self.mz_picker
        if mz_picker is None:
            raise MessageError("Error", "Please pick peaks first! Click on the `Find peaks` button.")

        if mz_picker.n_peaks == 0:
            self.on_clear_from_plot(None)
            return

        self.on_annotate_spectrum_with_scatter(None, False, mz_picker)
        self.on_annotate_spectrum_with_patches(None, False, mz_picker)
        self.on_annotate_spectrum_with_labels(None, False, mz_picker)

        self.plot_view.repaint()

    def on_annotate_spectrum_with_scatter(self, evt, repaint: bool = True, mz_picker: MassSpectrumBasePicker = None):
        """Annotate peaks on spectrum with patches"""
        CONFIG.peak_panel_scatter = self.visualize_scatter_check.GetValue()
        t_start = time.time()

        if mz_picker is None:
            mz_picker = self.mz_picker
        if mz_picker is None:
            raise MessageError("Error", "Please pick peaks first! Click on the `Find peaks` button.")

        if CONFIG.peak_panel_scatter:
            x = mz_picker.x
            y = mz_picker.y
            self.plot_view.remove_scatter(repaint=False)
            self.plot_view.add_scatter(
                x,
                y,
                color=CONFIG.marker_fill_color,
                marker=CONFIG.marker_shape_mpl_,
                size=CONFIG.marker_size,
                repaint=False,
            )
        else:
            self.plot_view.remove_scatter(repaint=False)

        if repaint:
            self.plot_view.repaint()

        logger.info(f"Annotated spectrum with scatter points in {report_time(t_start)}")

        if evt is not None:
            evt.Skip()

    def on_annotate_spectrum_with_patches(self, evt, repaint: bool = True, mz_picker: MassSpectrumBasePicker = None):
        """Annotate peaks on spectrum with patches"""
        CONFIG.peak_panel_highlight = self.visualize_highlight_check.GetValue()
        t_start = time.time()

        if mz_picker is None:
            mz_picker = self.mz_picker
        if mz_picker is None:
            raise MessageError("Error", "Please pick peaks first! Click on the `Find peaks` button.")

        if CONFIG.peak_panel_highlight:
            y = mz_picker.y[: CONFIG.peak_panel_labels_max_count]
            x_left = mz_picker.x_min_edge[: CONFIG.peak_panel_labels_max_count]
            width = mz_picker.x_width[: CONFIG.peak_panel_labels_max_count]
            y_start = np.zeros_like(x_left)
            self.plot_view.remove_patches(repaint=False)
            self.plot_view.add_patches(x_left, y_start, width, y, repaint=False, pickable=False)
        else:
            self.plot_view.remove_patches(repaint=False)

        if repaint:
            self.plot_view.repaint()

        logger.info(f"Annotated spectrum with patches in {report_time(t_start)}")

        if evt is not None:
            evt.Skip()

    # noinspection DuplicatedCode
    def on_annotate_spectrum_with_labels(self, evt, repaint: bool = True, mz_picker: MassSpectrumBasePicker = None):
        """Annotate peaks on spectrum with labels"""
        CONFIG.peak_panel_labels = self.visualize_show_labels_check.GetValue()
        CONFIG.peak_panel_labels = self.visualize_show_labels_check.GetValue()
        CONFIG.peak_panel_labels_max_count = str2int(self.visualize_max_labels.GetValue())
        CONFIG.peak_panel_labels_mz = self.visualize_show_labels_mz_check.GetValue()
        CONFIG.peak_panel_labels_int = self.visualize_show_labels_int_check.GetValue()
        CONFIG.peak_panel_labels_width = self.visualize_show_labels_width_check.GetValue()

        t_start = time.time()

        if mz_picker is None:
            mz_picker = self.mz_picker
        if mz_picker is None:
            raise MessageError("Error", "Please pick peaks first! Click on the `Find peaks` button.")

        if CONFIG.peak_panel_labels:
            x, y, labels = self.on_generate_labels(mz_picker)
            self.plot_view.remove_labels(repaint=False)
            self.plot_view.add_labels(x, y, labels, repaint=False)
        else:
            self.plot_view.remove_labels(repaint=False)

        if repaint:
            self.plot_view.repaint()

        if evt is not None:
            evt.Skip()

        logger.info(f"Annotated spectrum with labels in {report_time(t_start)}")

    def on_generate_labels(self, mz_picker: MassSpectrumBasePicker = None):
        """Generate labels that will be added to the plot"""
        if mz_picker is None:
            mz_picker = self.mz_picker

        if mz_picker is None:
            raise MessageError("Error", "Please pick peaks first! Click on the `Find peaks` button.")

        x, y, labels = [], [], []
        for i, (_x, _y, _label) in enumerate(
            mz_picker.get_label(
                CONFIG.peak_panel_labels_mz, CONFIG.peak_panel_labels_int, CONFIG.peak_panel_labels_width
            )
        ):
            x.append(_x)
            y.append(_y)
            labels.append(_label)
            if i >= CONFIG.peak_panel_labels_max_count:
                break

        return x, y, labels

    def on_clear_from_plot(self, _evt):
        """Clear peaks and various annotations"""
        self.plot_view.remove_scatter(repaint=False)
        self.plot_view.remove_patches(repaint=False)
        self.plot_view.remove_labels(repaint=False)
        self.on_show_threshold_line(None)
        self.plot_view.repaint()

    def on_add_to_annotations(self, _evt):
        """Add peaks as annotations"""
        raise NotImplementedError("Must implement method")
        # from origami.utils.labels import sanitize_string
        # from origami.objects.annotations import check_annotation_input
        #
        # t_start = time.time()
        # logger.info("Adding peaks to annotations...")
        #
        # peaks_dict = self._peaks_dict
        # if not peaks_dict:
        #     raise MessageError(
        #         "Pick peaks first", "You must pick peaks before you can plot them. Click on the `Find peaks` button"
        #     )
        #
        # # get annotations object
        # annotations_obj = self.data_handling.get_annotations_data(
        #     [self.document_title, self.dataset_type, self.dataset_name]
        # )
        #
        # ymin = 0
        # charge = 1
        # for i, __ in enumerate(peaks_dict["peaks_y_values"]):
        #     # generate all required fields
        #     position = peaks_dict["peaks_x_values"][i]
        #     intensity = peaks_dict["peaks_y_values"][i]
        #     xmin = peaks_dict["peaks_x_minus_width"][i]
        #     xmax = peaks_dict["peaks_x_plus_width"][i]
        #     height = intensity - ymin
        #     width = xmax - xmin
        #
        #     name = f"x={position:.4f}; y={intensity:.2f}"
        #     label = f"x={position:.4f}\ny={intensity:.2f}\n charge={charge:d}"
        #
        #     annotation_dict = {
        #         "name": name,
        #         "position_x": position,
        #         "position_y": intensity,
        #         "label": label,
        #         "label_position_x": position,
        #         "label_position_y": intensity,
        #         "label_position": [position, intensity],
        #         "arrow": True,
        #         "width": width,
        #         "height": height,
        #         "charge": charge,
        #         "patch_color": CONFIG.interactive_ms_annotations_color,
        #         "label_color": (0.0, 0.0, 0.0),
        #         "patch_position": [xmin, ymin, width, height],
        #         "patch": False,
        #     }
        #     name = sanitize_string(name)
        #     try:
        #         annotation_dict = check_annotation_input(annotation_dict)
        #     except ValueError as err:
        #         logger.error(err, exc_info=True)
        #         raise MessageError("Incorrect input", str(err))
        #
        #     if name in annotations_obj:
        #         annotations_obj.update_annotation(name, annotation_dict)
        #     else:
        #         annotations_obj.add_annotation(name, annotation_dict)
        #
        # self.document_tree.on_update_annotation(
        #     annotations_obj, self.document_title, self.dataset_type, self.dataset_name
        # )
        #
        # if CONFIG.peak_find_verbose:
        #     logger.info(f"Adding peaks to annotations object took {time.time()-t_start:.4f} seconds.")

    def on_add_to_peaklist(self, _evt):
        """Add peaks to peaklist"""
        raise NotImplementedError("Must implement method")
        # t_start = time.time()
        # logger.info("Adding peaks to peaklist...")
        #
        # peaks_dict = self._peaks_dict
        # if not peaks_dict:
        #     raise MessageError(
        #         "Pick peaks first", "You must pick peaks before you can plot them. Click on the `Find peaks` button"
        #     )
        #
        # document = self.data_handling.on_get_document(self.document_title)
        #
        # document_type = document.dataType
        # allowed_document_types = ["Type: ORIGAMI", "Type: MANUAL", "Type: Infrared", "Type: MassLynx"]
        #
        # if document_type not in allowed_document_types:
        #     raise MessageError(
        #         "Incorrect document type",
        #         f"Document type `{document_type}` does not permit addition of found peaks to the"
        #         + f" peaklist. Allowed document types include {allowed_document_types}.",
        #     )
        #
        # peaks_y_values = peaks_dict["peaks_y_values"]
        # peaks_x_minus_width = peaks_dict["peaks_x_minus_width"]
        # peaks_x_plus_width = peaks_dict["peaks_x_plus_width"]
        #
        # for __, (mz_x_minus, mz_x_plus, mz_height) in enumerate(
        #     zip(peaks_x_minus_width, peaks_x_plus_width, peaks_y_values)
        # ):
        #     ion_name = f"{mz_x_minus:.4f}-{mz_x_plus:.4f}"
        #     if not self.ion_panel.on_check_duplicate(ion_name, self.document_title):
        #         add_dict = {
        #             "ion_name": ion_name,
        #             "charge": 1,
        #             "mz_ymax": mz_height,
        #             "alpha": CONFIG.overlay_defaultAlpha,
        #             "mask": CONFIG.overlay_defaultMask,
        #             "document": self.document_title,
        #         }
        #         self.ion_panel.on_add_to_table(add_dict)
        #
        # if CONFIG.peak_find_verbose:
        #     logger.info(f"Adding peaks to peaklist took {time.time()-t_start:.4f} seconds.")

    def on_open_process_ms_settings(self, _evt):
        """Open MS pre-processing panel"""
        self.document_tree.on_open_process_ms_settings(
            disable_plot=True, disable_process=True, update_widget=self.PUB_SUBSCRIBE_EVENT
        )


def _main():
    from origami.icons.assets import Icons

    app = wx.App()
    icons = Icons()
    ex = PanelPeakPicker(None, None, icons, debug=True)

    ex.Show()
    app.MainLoop()


if __name__ == "__main__":
    _main()
