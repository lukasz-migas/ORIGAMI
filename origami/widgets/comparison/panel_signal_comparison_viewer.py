"""Signal comparison panel"""
# Standard library imports
import logging

# Third-party imports
import wx
from pubsub import pub
from natsort import natsorted
from pubsub.core.topicexc import TopicNameError

# Local imports
from origami.ids import ID_compareMS_MS_1
from origami.ids import ID_compareMS_MS_2
from origami.ids import ID_plotPanel_resize
from origami.ids import ID_processSettings_MS
from origami.ids import ID_extraSettings_legend
from origami.ids import ID_extraSettings_plot1D
from origami.styles import MiniFrame
from origami.styles import make_checkbox
from origami.styles import make_color_btn
from origami.styles import make_menu_item
from origami.styles import make_staticbox
from origami.styles import make_bitmap_btn
from origami.styles import make_spin_ctrl_double
from origami.utils.time import ttime
from origami.objects.misc import CompareItem
from origami.utils.screen import calculate_window_size
from origami.config.config import CONFIG
from origami.utils.utilities import report_time
from origami.utils.converters import str2num
from origami.visuals.mpl.gids import PlotIds
from origami.gui_elements.misc_dialogs import DialogBox
from origami.gui_elements.dialog_color_picker import DialogColorPicker
from origami.gui_elements.views.view_spectrum import ViewCompareMassSpectra

logger = logging.getLogger(__name__)

# TODO: Add key_events for N, P, I, S (except when editing  labels)


class PanelSignalComparisonViewer(MiniFrame):
    """Signal comparison viewer"""

    # panel settings
    TIMER_DELAY = 1000  # ms

    # module specific parameters
    PUB_SUBSCRIBE_EVENT = "widget.compare.update.spectrum"
    HELP_LINK = "https://origami.lukasz-migas.com/"

    # parameters
    _settings_panel_size = None

    # ui elements
    plot_view = None
    plot_panel = None
    plot_window = None

    resize_plot_check = None
    spectrum_1_document_value = None
    spectrum_1_spectrum_value = None
    spectrum_1_label_value = None
    spectrum_1_color_btn = None
    spectrum_1_transparency = None
    spectrum_1_line_style_value = None
    spectrum_2_document_value = None
    spectrum_2_spectrum_value = None
    spectrum_2_label_value = None
    spectrum_2_color_btn = None
    spectrum_2_transparency = None
    spectrum_2_line_style_value = None

    preprocess_check = None
    normalize_check = None
    inverse_check = None
    subtract_check = None
    settings_btn = None
    legend_btn = None
    process_btn = None
    plot_btn = None
    cancel_btn = None
    info_btn = None

    def __init__(self, parent, presenter, icons, **kwargs):
        MiniFrame.__init__(
            self, parent, title="Compare mass spectra...", style=wx.DEFAULT_FRAME_STYLE & ~wx.MAXIMIZE_BOX
        )

        self.parent = parent
        self.presenter = presenter
        self._icons = icons

        self.kwargs = kwargs
        self.current_document = self.kwargs.get("current_document", "")
        self.document_list = self.kwargs.get("document_list", [])
        self.compare_massSpectrum = []

        screen_size = wx.GetDisplaySize()
        if parent is not None:
            screen_size = self.parent.GetSize()
        self._display_size = screen_size
        self._display_resolution = wx.ScreenDC().GetPPI()
        self._window_size = calculate_window_size(self._display_size, [0.8, 0.6])

        # make gui items
        self.make_gui()
        if kwargs.get("debug", False):
            return

        self.setup()
        self._set_item_lists()
        self.update_spectrum(None)
        try:
            self.on_plot(None)
        except (KeyError, IndexError) as err:
            logger.error(err)

        self._timer = wx.Timer(self, True)
        self.Bind(wx.EVT_TIMER, self.on_update_widget, self._timer)

        # bind
        self.Bind(wx.EVT_CONTEXT_MENU, self.on_right_click)

    def setup(self):
        """Setup various UI elements"""
        self.settings_btn.Bind(wx.EVT_BUTTON, self.presenter.view.on_open_plot_settings_panel)
        self.legend_btn.Bind(wx.EVT_BUTTON, self.presenter.view.on_open_plot_settings_panel)
        self.process_btn.Bind(wx.EVT_BUTTON, self.on_open_process_ms_settings)
        if self.PUB_SUBSCRIBE_EVENT:
            pub.subscribe(self.on_process, self.PUB_SUBSCRIBE_EVENT)

    def on_update_widget(self, _evt):
        """Timer-based update"""
        if not self._timer.IsRunning():
            self.on_plot(None)

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
        return self.presenter.view.panelPlots

    @property
    def document_tree(self):
        """Return handle to `document_tree`"""
        return self.presenter.view.panelDocuments.documents

    @staticmethod
    def _get_dataset_index(source):
        """Return source index, depending on which spectrum parameter was selected"""
        if source.endswith("_1"):
            return PlotIds.PLOT_COMPARE_TOP_GID
        elif source.endswith("_2"):
            return PlotIds.PLOT_COMPARE_BOTTOM_GID

    # noinspection DuplicatedCode
    def on_right_click(self, _evt):
        """Right-click menu"""

        menu = wx.Menu()

        menu_customize = make_menu_item(parent=menu, text="Customise plot...", bitmap=self._icons.x_label)
        menu.AppendItem(menu_customize)
        menu.AppendSeparator()
        self.resize_plot_check = menu.AppendCheckItem(ID_plotPanel_resize, "Resize on saving")
        self.resize_plot_check.Check(CONFIG.resize)
        save_figure_menu_item = make_menu_item(
            menu, evt_id=wx.ID_ANY, text="Save figure as...", bitmap=self._icons.save
        )
        menu.AppendItem(save_figure_menu_item)
        menu_action_copy_to_clipboard = make_menu_item(
            parent=menu, evt_id=wx.ID_ANY, text="Copy plot to clipboard", bitmap=self._icons.filelist
        )
        menu.AppendItem(menu_action_copy_to_clipboard)

        menu.AppendSeparator()
        clear_plot_menu_item = make_menu_item(menu, evt_id=wx.ID_ANY, text="Clear plot", bitmap=self._icons.erase)
        menu.AppendItem(clear_plot_menu_item)

        self.Bind(wx.EVT_MENU, self.on_resize_check, id=ID_plotPanel_resize)
        self.Bind(wx.EVT_MENU, self.on_customise_plot, menu_customize)
        self.Bind(wx.EVT_MENU, self.on_save_figure, save_figure_menu_item)
        self.Bind(wx.EVT_MENU, self.on_copy_to_clipboard, menu_action_copy_to_clipboard)
        self.Bind(wx.EVT_MENU, self.on_clear_plot, clear_plot_menu_item)

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def on_close(self, evt):
        """Destroy this frame."""
        try:
            if self.PUB_SUBSCRIBE_EVENT:
                pub.unsubscribe(self.on_process, self.PUB_SUBSCRIBE_EVENT)
        except TopicNameError:
            pass

        try:
            self.update_spectrum(evt=None)
            self.document_tree._compare_panel = None
        except AttributeError:
            pass
        self.Destroy()

    # noinspection DuplicatedCode
    def make_gui(self):
        """Make UI"""
        # make panel
        settings_panel = self.make_settings_panel(self)
        self._settings_panel_size = settings_panel.GetSize()
        self.plot_panel = self.make_plot_panel(self)

        # pack element
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        main_sizer.Add(settings_panel, 0, wx.EXPAND, 0)
        main_sizer.Add(self.plot_panel, 1, wx.EXPAND, 0)

        # fit layout
        main_sizer.Fit(self)
        self.SetMinSize((1400, 700))
        self.SetSizer(main_sizer)
        self.SetSize(self._window_size)
        self.Layout()
        self.CenterOnParent()
        self.SetFocus()

    # noinspection DuplicatedCode
    def make_settings_panel(self, split_panel):
        """Make settings panel"""
        panel = wx.Panel(split_panel, -1, size=(-1, -1), name="settings")

        # MS 1
        spectrum_1_document_label = wx.StaticText(panel, -1, "Document:")
        self.spectrum_1_document_value = wx.ComboBox(panel, ID_compareMS_MS_1, choices=[], style=wx.CB_READONLY)
        self.spectrum_1_document_value.Bind(wx.EVT_COMBOBOX, self.update_gui)

        spectrum_1_spectrum_label = wx.StaticText(panel, -1, "Spectrum:")
        self.spectrum_1_spectrum_value = wx.ComboBox(
            panel, wx.ID_ANY, choices=[], style=wx.CB_READONLY, name="spectrum_1"
        )
        self.spectrum_1_spectrum_value.Bind(wx.EVT_COMBOBOX, self.update_spectrum)
        self.spectrum_1_spectrum_value.Bind(wx.EVT_COMBOBOX, self.on_plot)

        spectrum_1_label_label = wx.StaticText(panel, -1, "Label:")
        self.spectrum_1_label_value = wx.TextCtrl(panel, -1, "", style=wx.TE_PROCESS_ENTER, name="label_1")
        self.spectrum_1_label_value.Bind(wx.EVT_TEXT_ENTER, self.on_plot)
        self.spectrum_1_label_value.Bind(wx.EVT_TEXT, self.on_update_label)

        spectrum_1_color_label = wx.StaticText(panel, -1, "Color:")
        self.spectrum_1_color_btn = make_color_btn(panel, CONFIG.compare_panel_color_top, name="color_1")
        self.spectrum_1_color_btn.Bind(wx.EVT_BUTTON, self.on_update_color)

        spectrum_1_transparency_label = wx.StaticText(panel, -1, "Transparency:")
        self.spectrum_1_transparency = make_spin_ctrl_double(
            panel, CONFIG.compare_panel_alpha_top * 100, 0, 100, 10, (90, -1), name="transparency_1"
        )
        self.spectrum_1_transparency.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        spectrum_1_line_style_label = wx.StaticText(panel, -1, "Line style:")
        self.spectrum_1_line_style_value = wx.ComboBox(
            panel, choices=CONFIG.lineStylesList, style=wx.CB_READONLY, name="style_1"
        )
        self.spectrum_1_line_style_value.SetStringSelection(CONFIG.compare_panel_style_top)
        self.spectrum_1_line_style_value.Bind(wx.EVT_COMBOBOX, self.on_apply)

        # MS 2
        document_2_label = wx.StaticText(panel, -1, "Document:")
        self.spectrum_2_document_value = wx.ComboBox(
            panel, ID_compareMS_MS_2, choices=self.document_list, style=wx.CB_READONLY
        )
        self.spectrum_2_document_value.Bind(wx.EVT_COMBOBOX, self.update_gui)

        spectrum_2_spectrum_label = wx.StaticText(panel, -1, "Spectrum:")
        self.spectrum_2_spectrum_value = wx.ComboBox(
            panel, wx.ID_ANY, choices=[], style=wx.CB_READONLY, name="spectrum_2"
        )
        self.spectrum_2_spectrum_value.Bind(wx.EVT_COMBOBOX, self.update_spectrum)
        self.spectrum_2_spectrum_value.Bind(wx.EVT_COMBOBOX, self.on_plot)

        spectrum_2_label_label = wx.StaticText(panel, -1, "Label:")
        self.spectrum_2_label_value = wx.TextCtrl(panel, -1, "", style=wx.TE_PROCESS_ENTER, name="label_2")
        self.spectrum_2_label_value.Bind(wx.EVT_TEXT_ENTER, self.on_plot)
        self.spectrum_2_label_value.Bind(wx.EVT_TEXT, self.on_update_label)

        spectrum_2_color_label = wx.StaticText(panel, -1, "Color:")
        self.spectrum_2_color_btn = make_color_btn(panel, CONFIG.compare_panel_color_bottom, name="color_2")
        self.spectrum_2_color_btn.Bind(wx.EVT_BUTTON, self.on_update_color)

        spectrum_2_transparency_label = wx.StaticText(panel, -1, "Transparency:")
        self.spectrum_2_transparency = make_spin_ctrl_double(
            panel, CONFIG.compare_panel_alpha_bottom * 100, 0, 100, 10, (90, -1), name="transparency_2"
        )
        self.spectrum_2_transparency.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        spectrum_2_line_style_label = wx.StaticText(panel, -1, "Line style:")
        self.spectrum_2_line_style_value = wx.ComboBox(
            panel, choices=CONFIG.lineStylesList, style=wx.CB_READONLY, name="style_2"
        )
        self.spectrum_2_line_style_value.SetStringSelection(CONFIG.compare_panel_style_bottom)
        self.spectrum_2_line_style_value.Bind(wx.EVT_COMBOBOX, self.on_apply)

        # Processing
        process_static_box = make_staticbox(panel, "Visualization", size=(-1, -1), color=wx.BLACK)
        process_static_box.SetSize((-1, -1))

        self.preprocess_check = make_checkbox(panel, "Pre-process", tooltip="Enable pre-processing before plotting")
        self.preprocess_check.SetValue(CONFIG.compare_panel_preprocess)
        self.preprocess_check.Bind(wx.EVT_CHECKBOX, self.update_spectrum)
        self.preprocess_check.Bind(wx.EVT_CHECKBOX, self.on_plot)

        self.normalize_check = make_checkbox(
            panel, "Normalize", tooltip="Normalize spectra to range 0-1 before plotting"
        )
        self.normalize_check.SetValue(CONFIG.compare_panel_normalize)
        self.normalize_check.Bind(wx.EVT_CHECKBOX, self.update_spectrum)
        self.normalize_check.Bind(wx.EVT_CHECKBOX, self.on_plot)

        self.inverse_check = make_checkbox(panel, "Inverse", tooltip="Inverse spectra to give a butterfly-like effect")
        self.inverse_check.SetValue(CONFIG.compare_panel_inverse)
        self.inverse_check.Bind(wx.EVT_CHECKBOX, self.update_spectrum)
        self.inverse_check.Bind(wx.EVT_CHECKBOX, self.on_plot)

        self.subtract_check = make_checkbox(
            panel,
            "Subtract",
            tooltip="Subtract the bottom spectrum from the top. You can combine effect by pre-processing or "
            "normalizing spectra before subtraction/",
        )
        self.subtract_check.SetValue(CONFIG.compare_panel_subtract)
        self.subtract_check.Bind(wx.EVT_CHECKBOX, self.update_spectrum)
        self.subtract_check.Bind(wx.EVT_CHECKBOX, self.on_plot)
        self.subtract_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        self.settings_btn = make_bitmap_btn(
            panel, ID_extraSettings_plot1D, self._icons.plot_1d, tooltip="Change plot parameters"
        )
        self.legend_btn = make_bitmap_btn(
            panel, ID_extraSettings_legend, self._icons.plot_legend, tooltip="Change legend parameters"
        )
        self.process_btn = make_bitmap_btn(
            panel, ID_processSettings_MS, self._icons.process_ms, tooltip="Change MS pre-processing parameters"
        )

        self.plot_btn = wx.Button(panel, wx.ID_OK, "Plot", size=(-1, 22))
        self.plot_btn.Bind(wx.EVT_BUTTON, self.on_plot)

        self.cancel_btn = wx.Button(panel, wx.ID_OK, "Cancel", size=(-1, 22))
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_close)

        # pack elements
        ms1_grid = wx.GridBagSizer(2, 2)
        y = 0
        ms1_grid.Add(spectrum_1_document_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        ms1_grid.Add(self.spectrum_1_document_value, (y, 1), wx.GBSpan(1, 6), flag=wx.EXPAND)
        y += 1
        ms1_grid.Add(spectrum_1_spectrum_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        ms1_grid.Add(self.spectrum_1_spectrum_value, (y, 1), wx.GBSpan(1, 6), flag=wx.EXPAND)
        y += 1
        ms1_grid.Add(spectrum_1_label_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        ms1_grid.Add(self.spectrum_1_label_value, (y, 1), wx.GBSpan(1, 6), flag=wx.EXPAND)
        y += 1
        ms1_grid.Add(spectrum_1_color_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        ms1_grid.Add(self.spectrum_1_color_btn, (y, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        ms1_grid.Add(spectrum_1_transparency_label, (y, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        ms1_grid.Add(self.spectrum_1_transparency, (y, 3), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        ms1_grid.Add(spectrum_1_line_style_label, (y, 4), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        ms1_grid.Add(self.spectrum_1_line_style_value, (y, 5), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)

        ms_1_static_box = make_staticbox(panel, "Spectrum (top)", size=(-1, -1), color=wx.BLACK)
        ms_1_static_box.SetSize((-1, -1))
        ms_1_box_sizer = wx.StaticBoxSizer(ms_1_static_box, wx.HORIZONTAL)
        ms_1_box_sizer.Add(ms1_grid, 0, wx.EXPAND, 10)

        ms2_grid = wx.GridBagSizer(2, 2)
        y = 0
        ms2_grid.Add(document_2_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        ms2_grid.Add(self.spectrum_2_document_value, (y, 1), wx.GBSpan(1, 6), flag=wx.EXPAND)
        y += 1
        ms2_grid.Add(spectrum_2_spectrum_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        ms2_grid.Add(self.spectrum_2_spectrum_value, (y, 1), wx.GBSpan(1, 6), flag=wx.EXPAND)
        y += 1
        ms2_grid.Add(spectrum_2_label_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        ms2_grid.Add(self.spectrum_2_label_value, (y, 1), wx.GBSpan(1, 6), flag=wx.EXPAND)
        y += 1
        ms2_grid.Add(spectrum_2_color_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        ms2_grid.Add(self.spectrum_2_color_btn, (y, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        ms2_grid.Add(spectrum_2_transparency_label, (y, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        ms2_grid.Add(self.spectrum_2_transparency, (y, 3), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        ms2_grid.Add(spectrum_2_line_style_label, (y, 4), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        ms2_grid.Add(self.spectrum_2_line_style_value, (y, 5), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)

        ms_2_static_box = make_staticbox(panel, "Spectrum (bottom)", size=(-1, -1), color=wx.BLACK)
        ms_2_static_box.SetSize((-1, -1))
        ms_2_box_sizer = wx.StaticBoxSizer(ms_2_static_box, wx.HORIZONTAL)
        ms_2_box_sizer.Add(ms2_grid, 0, wx.EXPAND, 10)

        processing_grid = wx.StaticBoxSizer(process_static_box, wx.VERTICAL)
        processing_grid.Add(self.preprocess_check, 0, wx.EXPAND)
        processing_grid.Add(self.normalize_check, 0, wx.EXPAND)
        processing_grid.Add(self.inverse_check, 0, wx.EXPAND)
        processing_grid.Add(self.subtract_check, 0, wx.EXPAND)

        view_grid = wx.BoxSizer(wx.HORIZONTAL)
        view_grid.Add(self.settings_btn)
        view_grid.Add(self.legend_btn)
        view_grid.Add(self.process_btn)

        btn_grid = wx.BoxSizer(wx.HORIZONTAL)
        btn_grid.Add(self.plot_btn)
        btn_grid.AddSpacer(20)
        btn_grid.Add(self.cancel_btn)

        self.info_btn = self.make_info_button(panel)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(ms_1_box_sizer, 0, wx.EXPAND, 10)
        sizer.Add(ms_2_box_sizer, 0, wx.EXPAND, 10)
        sizer.AddSpacer(5)
        sizer.Add(processing_grid, 0, wx.EXPAND, 10)
        sizer.AddSpacer(5)
        sizer.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND, 10)
        sizer.AddSpacer(5)
        sizer.Add(view_grid, 0, wx.ALIGN_CENTER_HORIZONTAL, 10)
        sizer.AddSpacer(5)
        sizer.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND, 10)
        sizer.AddSpacer(5)
        sizer.Add(btn_grid, 0, wx.ALIGN_CENTER_HORIZONTAL, 10)
        sizer.AddStretchSpacer(1)
        sizer.Add(self.info_btn, 0, wx.ALIGN_LEFT, 10)

        # fit layout
        sizer.Fit(panel)
        panel.SetSizerAndFit(sizer)

        return panel

    # noinspection DuplicatedCode
    def make_plot_panel(self, split_panel):
        """Make plot panel"""
        pixel_size = [(self._window_size[0] - self._settings_panel_size[0] - 50), (self._window_size[1] - 50)]
        figsize = [pixel_size[0] / self._display_resolution[0], pixel_size[1] / self._display_resolution[1]]

        self.plot_view = ViewCompareMassSpectra(split_panel, figsize, x_label="m/z (Da)", y_label="Intensity")
        self.plot_window = self.plot_view.figure

        return self.plot_view.panel

    def _set_item_lists(self, **kwargs):
        """Set items in the GUI after the start of the widget or something has changed in the document(s)"""
        refresh = kwargs.pop("refresh", False)

        # update items in the widget
        if "current_document" in kwargs:
            self.current_document = kwargs["current_document"]
            self.kwargs["current_document"] = kwargs.pop("current_document")

        if "document_list" in kwargs:
            self.document_list = kwargs["document_list"]
            self.kwargs["document_list"] = kwargs.pop("document_list")

        if "document_spectrum_list" in kwargs:
            self.kwargs["document_spectrum_list"] = kwargs.pop("document_spectrum_list")

        # check document list
        document_1, spectrum_1, spectrum_list_1, document_2, spectrum_2, spectrum_list_2 = self._check_spectrum_list()

        if refresh:
            _document_1 = self.spectrum_1_document_value.GetStringSelection()
            if _document_1 in self.document_list:
                document_1 = _document_1
            _document_2 = self.spectrum_2_document_value.GetStringSelection()
            if _document_2 in self.document_list:
                document_2 = _document_2
            _spectrum_1 = self.spectrum_1_spectrum_value.GetStringSelection()
            if _spectrum_1 in spectrum_list_1:
                spectrum_1 = _spectrum_1
            _spectrum_2 = self.spectrum_2_spectrum_value.GetStringSelection()
            if _spectrum_2 in spectrum_list_2:
                spectrum_2 = _spectrum_2

        # update lists
        self.spectrum_1_document_value.SetItems(self.document_list)
        self.spectrum_2_document_value.SetItems(self.document_list)
        self.spectrum_1_spectrum_value.SetItems(spectrum_list_1)
        self.spectrum_2_spectrum_value.SetItems(spectrum_list_2)

        # update current selection
        self.spectrum_1_document_value.SetStringSelection(document_1)
        self.spectrum_2_document_value.SetStringSelection(document_2)
        self.spectrum_1_spectrum_value.SetStringSelection(spectrum_1)
        self.spectrum_2_spectrum_value.SetStringSelection(spectrum_2)

    def _check_spectrum_list(self):

        spectrum_list_1 = natsorted(self.kwargs["document_spectrum_list"][self.document_list[0]])
        if len(spectrum_list_1) >= 2:
            return (
                self.document_list[0],
                spectrum_list_1[0],
                spectrum_list_1,
                self.document_list[0],
                spectrum_list_1[1],
                spectrum_list_1,
            )
        else:
            spectrum_list_2 = natsorted(self.kwargs["document_spectrum_list"][self.document_list[1]])
            return (
                self.document_list[0],
                spectrum_list_1[0],
                spectrum_list_1,
                self.document_list[1],
                spectrum_list_2[0],
                spectrum_list_2,
            )

    def update_gui(self, evt):
        """Update GUI"""
        evt_id = evt.GetId()
        # update document list
        if evt_id == ID_compareMS_MS_1:
            document_1 = self.spectrum_1_document_value.GetStringSelection()
            spectrum_list_1 = natsorted(self.kwargs["document_spectrum_list"][document_1])
            self.spectrum_1_spectrum_value.SetItems(spectrum_list_1)
            self.spectrum_1_spectrum_value.SetStringSelection(spectrum_list_1[0])

        elif evt_id == ID_compareMS_MS_2:
            document_2 = self.spectrum_2_document_value.GetStringSelection()
            spectrum_list_2 = natsorted(self.kwargs["document_spectrum_list"][document_2])
            self.spectrum_2_spectrum_value.SetItems(spectrum_list_2)
            self.spectrum_2_spectrum_value.SetStringSelection(spectrum_list_2[0])

    def on_apply(self, evt):
        """Update settings"""
        source = None
        if evt is not None:
            source = evt.GetEventObject().GetName()

        CONFIG.compare_panel_alpha_top = str2num(self.spectrum_1_transparency.GetValue()) / 100
        CONFIG.compare_panel_style_top = self.spectrum_1_line_style_value.GetStringSelection()

        CONFIG.compare_panel_alpha_bottom = str2num(self.spectrum_2_transparency.GetValue()) / 100
        CONFIG.compare_panel_style_bottom = self.spectrum_2_line_style_value.GetStringSelection()

        if evt is not None:
            self.on_plot_update_style(source)

    def on_toggle_controls(self, evt):
        """Update UI elements based on some other settings"""
        if self.subtract_check.GetValue():
            self.inverse_check.SetValue(False)
            self.inverse_check.Disable()
        else:
            self.inverse_check.Enable()

        if evt is not None:
            evt.Skip()

    def update_spectrum(self, evt):
        """Update spectrum selection"""
        CONFIG.compare_panel_top_ = CompareItem(
            document=self.spectrum_1_document_value.GetStringSelection(),
            title=self.spectrum_1_spectrum_value.GetStringSelection(),
        )
        CONFIG.compare_panel_bottom_ = CompareItem(
            document=self.spectrum_2_document_value.GetStringSelection(),
            title=self.spectrum_2_spectrum_value.GetStringSelection(),
        )
        CONFIG.compare_panel_preprocess = self.preprocess_check.GetValue()
        CONFIG.compare_panel_inverse = self.inverse_check.GetValue()
        CONFIG.compare_panel_normalize = self.normalize_check.GetValue()
        CONFIG.compare_panel_subtract = self.subtract_check.GetValue()

        # setup labels - if the user has not specified the label, infer it from the object name. Names that are too long
        # will be automatically truncated to approx 35 characters long. The inferred name is purposefully not set in the
        # text control, since if the spectrum is changed, the label will not be automatically updated - its up to the
        # user to keep track of what is being displayed
        label_1 = self.spectrum_1_label_value.GetValue()
        if label_1 == "":
            label_1 = self.spectrum_1_spectrum_value.GetStringSelection()
            if len(label_1) > 35:
                label_1 = label_1[:35] + "..."
        label_2 = self.spectrum_2_label_value.GetValue()
        if label_2 == "":
            label_2 = self.spectrum_2_spectrum_value.GetStringSelection()
            if len(label_2) > 35:
                label_2 = label_2[:35] + "..."
        CONFIG.compare_panel_top_.legend = label_1
        CONFIG.compare_panel_bottom_.legend = label_2

        self.on_apply(None)

        if evt is not None:
            evt.Skip()

    def on_update_label(self, _evt):
        """Reset timer based on how frequently the label is being updated"""
        self._timer.Stop()
        self._timer.StartOnce(self.TIMER_DELAY)

    def on_update_color(self, evt):
        """Update spectrum color"""
        # get object name
        source = evt.GetEventObject().GetName()

        # get color
        dlg = DialogColorPicker(self, CONFIG.customColors)
        if dlg.ShowModal() == wx.ID_OK:
            color_255, color_1, __ = dlg.GetChosenColour()
            CONFIG.customColors = dlg.GetCustomColours()
        else:
            return

        # assign color
        if source == "color_1":
            CONFIG.compare_panel_color_top = color_1
            self.spectrum_1_color_btn.SetBackgroundColour(color_255)
        elif source == "color_2":
            CONFIG.compare_panel_color_bottom = color_1
            self.spectrum_2_color_btn.SetBackgroundColour(color_255)

        self.on_plot_update_style(source)

    def error_handler(self, flag=None):
        """Enable/disable item if error msg occurred"""
        if flag is None:
            return

        if flag == "subtract":
            self.subtract_check.SetValue(False)

        if flag == "normalize":
            self.normalize_check.SetValue(False)

    def on_plot_update_style(self, source: str):
        """Update plot style"""
        t_start = ttime()

        index = self._get_dataset_index(source)

        kwargs = dict()
        if source.endswith("_1"):
            kwargs["color"] = CONFIG.compare_panel_color_top
            kwargs["line_style"] = CONFIG.compare_panel_style_top
            kwargs["transparency"] = CONFIG.compare_panel_alpha_top
            kwargs["label"] = self.spectrum_1_label_value.GetValue()
        elif source.endswith("_2"):
            kwargs["color"] = CONFIG.compare_panel_color_bottom
            kwargs["line_style"] = CONFIG.compare_panel_style_bottom
            kwargs["transparency"] = CONFIG.compare_panel_alpha_bottom
            kwargs["label"] = self.spectrum_2_label_value.GetValue()

        self.plot_view.update_style(index, **kwargs)
        self.panel_plot.plot_1D_update_style_by_label(index, plot=None, plot_obj=self.plot_window, **kwargs)
        logger.info(f"Plot update took {report_time(t_start)}")

    def on_plot(self, _evt):
        """Plot overlay spectra"""
        t_start = ttime()
        self.update_spectrum(None)

        __, spectrum_1 = self.data_handling.get_spectrum_data(
            [CONFIG.compare_panel_top_.document, CONFIG.compare_panel_top_.title]
        )
        __, spectrum_2 = self.data_handling.get_spectrum_data(
            [CONFIG.compare_panel_bottom_.document, CONFIG.compare_panel_bottom_.title]
        )

        # normalize mass spectra
        if CONFIG.compare_panel_normalize:
            spectrum_1.normalize()
            spectrum_2.normalize()

        if CONFIG.compare_panel_preprocess:
            self.data_handling.on_process_ms(spectrum_1)
            self.data_handling.on_process_ms(spectrum_2)

        x_top, y_top = spectrum_1.x, spectrum_1.y
        x_bottom, y_bottom = spectrum_2.x, spectrum_2.y

        if CONFIG.compare_panel_inverse and not CONFIG.compare_panel_subtract:
            y_bottom = -y_bottom

        if CONFIG.compare_panel_subtract:
            x_top, y_top, x_bottom, y_bottom = self.data_handling.subtract_spectra(x_top, y_top, x_bottom, y_bottom)

        self.plot_view.plot(
            x_top,
            x_bottom,
            y_top,
            y_bottom,
            labels=[CONFIG.compare_panel_top_.legend, CONFIG.compare_panel_bottom_.legend],
        )
        logger.info(f"Plot update took {report_time(t_start)}")

    def on_process(self):
        """Process spectrum"""
        if CONFIG.compare_panel_preprocess:
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
                CONFIG.compare_panel_preprocess = True

    def on_clear_plot(self, _evt):
        """Clear plot area"""
        self.plot_window.clear()

    def on_save_figure(self, _evt):
        """Save figure"""
        filename = "compare-mass-spectra"
        self.plot_view.save_figure(filename)

    def on_resize_check(self, _evt):
        """Resize checkbox"""
        self.panel_plot.on_resize_check(None)

    def on_copy_to_clipboard(self, _evt):
        """Copy plot to clipboard"""
        self.plot_window.copy_to_clipboard()

    def on_customise_plot(self, _evt):
        """Customise plot"""
        self.panel_plot.on_customise_plot(None, plot="MS...", plot_obj=self.plot_window)

    def on_open_process_ms_settings(self, _evt):
        """Open MS pre-processing panel"""
        self.document_tree.on_open_process_ms_settings(
            disable_plot=True, disable_process=True, update_widget=self.PUB_SUBSCRIBE_EVENT
        )


def _main():
    from origami.icons.assets import Icons

    app = wx.App()
    icons = Icons()
    ex = PanelSignalComparisonViewer(None, None, icons, debug=True)

    ex.Show()
    app.MainLoop()


if __name__ == "__main__":
    _main()
