# Standard library imports
import logging
from copy import deepcopy

# Third-party imports
import wx
from natsort import natsorted

# Local imports
import origami.processing.spectra as pr_spectra
from origami.ids import ID_compareMS_MS_1
from origami.ids import ID_compareMS_MS_2
from origami.ids import ID_plotPanel_resize
from origami.ids import ID_processSettings_MS
from origami.ids import ID_extraSettings_legend
from origami.ids import ID_extraSettings_plot1D
from origami.ids import ID_plots_customise_plot
from origami.styles import MiniFrame
from origami.styles import make_checkbox
from origami.styles import make_color_btn
from origami.styles import make_menu_item
from origami.styles import make_staticbox
from origami.styles import make_bitmap_btn
from origami.styles import make_spin_ctrl_double
from origami.utils.time import ttime
from origami.utils.screen import calculate_window_size
from origami.utils.converters import str2num
from origami.visuals.mpl.plot_spectrum import PlotSpectrum
from origami.gui_elements.dialog_color_picker import DialogColorPicker

logger = logging.getLogger(__name__)

# TODO: FIXME: Changing label does not update the legend as you write
# TODO: Add key_events for N, P, I, S (except when editing  labels)
# TODO: FIXME: changing document title doesnt change the plot


class PanelSignalComparisonViewer(MiniFrame):
    """Signal comparison viewer"""

    def __init__(self, parent, presenter, config, icons, **kwargs):
        MiniFrame.__init__(
            self,
            parent,
            title="Compare mass spectra...",
            style=wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX),
        )

        self.parent = parent
        self.presenter = presenter
        self.config = config
        self.icons = icons

        self.kwargs = kwargs
        self.current_document = self.kwargs["current_document"]
        self.document_list = self.kwargs["document_list"]

        self.compare_massSpectrum = []

        self.data_handling = presenter.data_handling
        self.data_processing = presenter.data_processing
        self.panel_plot = self.presenter.view.panelPlots
        self.document_tree = self.presenter.view.panelDocuments.documents

        self.parent.GetSize()
        self._display_size = self.parent.GetSize()
        self._display_resolution = wx.ScreenDC().GetPPI()
        self._window_size = calculate_window_size(self._display_size, 0.8)

        # make gui items
        self.make_gui()
        self._set_item_lists()
        self.update_spectrum(None)
        try:
            self.on_plot(None)
        except (KeyError, IndexError) as err:
            logger.error(err)

        # bind
        self.Bind(wx.EVT_CONTEXT_MENU, self.on_right_click)

    @staticmethod
    def _get_dataset_index(source):
        if source.endswith("_1"):
            index = 0
        elif source.endswith("_2"):
            index = 1

        return index

    def on_right_click(self, evt):

        menu = wx.Menu()
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                evt_id=ID_plots_customise_plot,
                text="Customise plot...",
                bitmap=self.icons.iconsLib["change_xlabels_16"],
            )
        )
        menu.AppendSeparator()
        self.resize_plot_check = menu.AppendCheckItem(ID_plotPanel_resize, "Resize on saving")
        self.resize_plot_check.Check(self.config.resize)
        save_figure_menu_item = make_menu_item(
            menu, evt_id=wx.ID_ANY, text="Save figure as...", bitmap=self.icons.iconsLib["save16"]
        )
        menu.AppendItem(save_figure_menu_item)
        menu_action_copy_to_clipboard = make_menu_item(
            parent=menu, evt_id=wx.ID_ANY, text="Copy plot to clipboard", bitmap=self.icons.iconsLib["filelist_16"]
        )
        menu.AppendItem(menu_action_copy_to_clipboard)

        menu.AppendSeparator()
        clear_plot_menu_item = make_menu_item(
            menu, evt_id=wx.ID_ANY, text="Clear plot", bitmap=self.icons.iconsLib["clear_16"]
        )
        menu.AppendItem(clear_plot_menu_item)

        self.Bind(wx.EVT_MENU, self.on_resize_check, id=ID_plotPanel_resize)
        self.Bind(wx.EVT_MENU, self.on_customise_plot, id=ID_plots_customise_plot)
        self.Bind(wx.EVT_MENU, self.on_save_figure, save_figure_menu_item)
        self.Bind(wx.EVT_MENU, self.on_copy_to_clipboard, menu_action_copy_to_clipboard)
        self.Bind(wx.EVT_MENU, self.on_clear_plot, clear_plot_menu_item)

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def on_close(self, evt):
        """Destroy this frame."""
        self.update_spectrum(evt=None)
        self.document_tree._compare_panel = None
        self.Destroy()

    def on_resize_check(self, evt):
        self.panel_plot.on_resize_check(None)

    def on_copy_to_clipboard(self, evt):
        self.plot_window.copy_to_clipboard()

    def on_customise_plot(self, evt):
        self.panel_plot.on_customise_plot(None, plot="MS...", plot_obj=self.plot_window)

    def make_gui(self):

        # make panel
        panel = wx.Panel(self, -1, size=(-1, -1), name="main")

        settings_panel = self.make_settings_panel(panel)
        self._settings_panel_size = settings_panel.GetSize()
        plot_panel = self.make_plot_panel(panel)

        # pack element
        self.main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.main_sizer.Add(settings_panel, 0, wx.EXPAND, 0)
        self.main_sizer.Add(plot_panel, 0, wx.EXPAND, 0)

        # fit layout
        self.main_sizer.Fit(panel)
        self.SetSize(self._window_size)
        self.SetSizer(self.main_sizer)
        self.Layout()
        self.CentreOnScreen()
        self.SetFocus()

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

    def make_settings_panel(self, split_panel):
        panel = wx.Panel(split_panel, -1, size=(-1, -1), name="settings")

        ms_1_staticbox = make_staticbox(panel, "Spectrum - 1", size=(-1, -1), color=wx.BLACK)
        ms_1_staticbox.SetSize((-1, -1))
        ms_1_boxsizer = wx.StaticBoxSizer(ms_1_staticbox, wx.HORIZONTAL)

        ms_2_staticbox = make_staticbox(panel, "Spectrum - 2", size=(-1, -1), color=wx.BLACK)
        ms_2_staticbox.SetSize((-1, -1))
        ms_2_boxsizer = wx.StaticBoxSizer(ms_2_staticbox, wx.HORIZONTAL)

        # MS 1
        spectrum_1_document_label = wx.StaticText(panel, -1, "Document:")
        self.spectrum_1_document_value = wx.ComboBox(panel, ID_compareMS_MS_1, choices=[], style=wx.CB_READONLY)

        spectrum_1_spectrum_label = wx.StaticText(panel, -1, "Spectrum:")
        self.spectrum_1_spectrum_value = wx.ComboBox(
            panel, wx.ID_ANY, choices=[], style=wx.CB_READONLY, name="spectrum_1"
        )

        spectrum_1_label_label = wx.StaticText(panel, -1, "Label:")
        self.spectrum_1_label_value = wx.TextCtrl(panel, -1, "", style=wx.TE_PROCESS_ENTER, name="label_1")

        spectrum_1_color_label = wx.StaticText(panel, -1, "Color:")
        self.spectrum_1_color_btn = make_color_btn(panel, self.config.lineColour_MS1, name="color_1")

        spectrum_1_transparency_label = wx.StaticText(panel, -1, "Transparency:")
        self.spectrum_1_transparency = make_spin_ctrl_double(
            panel, self.config.lineTransparency_MS1 * 100, 0, 100, 10, (90, -1), name="transparency_1"
        )

        spectrum_1_line_style_label = wx.StaticText(panel, -1, "Line style:")
        self.spectrum_1_line_style_value = wx.ComboBox(
            panel, choices=self.config.lineStylesList, style=wx.CB_READONLY, name="style_1"
        )
        self.spectrum_1_line_style_value.SetStringSelection(self.config.lineStyle_MS1)

        # MS 2
        document_2_label = wx.StaticText(panel, -1, "Document:")
        self.spectrum_2_document_value = wx.ComboBox(
            panel, ID_compareMS_MS_2, choices=self.document_list, style=wx.CB_READONLY
        )

        spectrum_2_spectrum_label = wx.StaticText(panel, -1, "Spectrum:")
        self.spectrum_2_spectrum_value = wx.ComboBox(
            panel, wx.ID_ANY, choices=[], style=wx.CB_READONLY, name="spectrum_2"
        )

        spectrum_2_label_label = wx.StaticText(panel, -1, "Label:")
        self.spectrum_2_label_value = wx.TextCtrl(panel, -1, "", style=wx.TE_PROCESS_ENTER, name="label_2")

        spectrum_2_color_label = wx.StaticText(panel, -1, "Color:")
        self.spectrum_2_color_btn = make_color_btn(panel, self.config.lineColour_MS2, name="color_2")

        spectrum_2_transparency_label = wx.StaticText(panel, -1, "Transparency:")
        self.spectrum_2_transparency = make_spin_ctrl_double(
            panel, self.config.lineTransparency_MS2 * 100, 0, 100, 10, (90, -1), name="transparency_2"
        )

        spectrum_2_line_style_label = wx.StaticText(panel, -1, "Line style:")
        self.spectrum_2_line_style_value = wx.ComboBox(
            panel, choices=self.config.lineStylesList, style=wx.CB_READONLY, name="style_2"
        )
        self.spectrum_2_line_style_value.SetStringSelection(self.config.lineStyle_MS2)

        # Processing
        process_static_box = make_staticbox(panel, "Processing", size=(-1, -1), color=wx.BLACK)
        process_static_box.SetSize((-1, -1))
        processing_boxsizer = wx.StaticBoxSizer(process_static_box, wx.HORIZONTAL)

        self.preprocess_check = make_checkbox(panel, "Pre-process")
        self.preprocess_check.SetValue(self.config.compare_massSpectrumParams["preprocess"])

        self.normalize_check = make_checkbox(panel, "Normalize")
        self.normalize_check.SetValue(self.config.compare_massSpectrumParams["normalize"])

        self.inverse_check = make_checkbox(panel, "Inverse")
        self.inverse_check.SetValue(self.config.compare_massSpectrumParams["inverse"])

        self.subtract_check = make_checkbox(panel, "Subtract")
        self.subtract_check.SetValue(self.config.compare_massSpectrumParams["subtract"])

        settings_label = wx.StaticText(panel, wx.ID_ANY, "Settings:")
        self.settings_btn = make_bitmap_btn(panel, ID_extraSettings_plot1D, self.icons.iconsLib["panel_plot1D_16"])
        self.legend_btn = make_bitmap_btn(panel, ID_extraSettings_legend, self.icons.iconsLib["panel_legend_16"])
        self.process_btn = make_bitmap_btn(panel, ID_processSettings_MS, self.icons.iconsLib["process_ms_16"])

        horizontal_line_1 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_2 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        self.plot_btn = wx.Button(panel, wx.ID_OK, "Full replot", size=(-1, 22))
        self.cancel_btn = wx.Button(panel, wx.ID_OK, "Cancel", size=(-1, 22))

        self.spectrum_1_document_value.Bind(wx.EVT_COMBOBOX, self.update_gui)
        self.spectrum_2_document_value.Bind(wx.EVT_COMBOBOX, self.update_gui)

        self.spectrum_1_spectrum_value.Bind(wx.EVT_COMBOBOX, self.update_spectrum)
        self.spectrum_2_spectrum_value.Bind(wx.EVT_COMBOBOX, self.update_spectrum)
        self.spectrum_1_spectrum_value.Bind(wx.EVT_COMBOBOX, self.on_plot)
        self.spectrum_2_spectrum_value.Bind(wx.EVT_COMBOBOX, self.on_plot)

        self.preprocess_check.Bind(wx.EVT_CHECKBOX, self.update_spectrum)
        self.normalize_check.Bind(wx.EVT_CHECKBOX, self.update_spectrum)
        self.inverse_check.Bind(wx.EVT_CHECKBOX, self.update_spectrum)
        self.subtract_check.Bind(wx.EVT_CHECKBOX, self.update_spectrum)

        self.spectrum_1_label_value.Bind(wx.EVT_TEXT_ENTER, self.on_plot)
        self.spectrum_2_label_value.Bind(wx.EVT_TEXT_ENTER, self.on_plot)

        self.spectrum_1_color_btn.Bind(wx.EVT_BUTTON, self.on_update_color)
        self.spectrum_2_color_btn.Bind(wx.EVT_BUTTON, self.on_update_color)

        self.spectrum_1_transparency.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.spectrum_2_transparency.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.spectrum_1_line_style_value.Bind(wx.EVT_COMBOBOX, self.on_apply)
        self.spectrum_2_line_style_value.Bind(wx.EVT_COMBOBOX, self.on_apply)

        self.preprocess_check.Bind(wx.EVT_CHECKBOX, self.on_plot)
        self.normalize_check.Bind(wx.EVT_CHECKBOX, self.on_plot)
        self.inverse_check.Bind(wx.EVT_CHECKBOX, self.on_plot)
        self.subtract_check.Bind(wx.EVT_CHECKBOX, self.on_plot)
        self.subtract_check.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        self.plot_btn.Bind(wx.EVT_BUTTON, self.on_plot)
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_close)

        self.settings_btn.Bind(wx.EVT_BUTTON, self.presenter.view.on_open_plot_settings_panel)
        self.legend_btn.Bind(wx.EVT_BUTTON, self.presenter.view.on_open_plot_settings_panel)
        self.process_btn.Bind(wx.EVT_BUTTON, self.on_open_process_MS_settings)

        # button grid
        btn_grid = wx.GridBagSizer(7, 5)
        y = 0
        btn_grid.Add(self.settings_btn, (y, 0), flag=wx.ALIGN_CENTER)
        btn_grid.Add(self.legend_btn, (y, 1), flag=wx.ALIGN_CENTER)
        btn_grid.Add(self.process_btn, (y, 2), flag=wx.ALIGN_CENTER)

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

        ms_1_boxsizer.Add(ms1_grid, 0, wx.EXPAND, 10)

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
        ms_2_boxsizer.Add(ms2_grid, 0, wx.EXPAND, 10)

        processing_grid = wx.GridBagSizer(2, 2)
        y = 0
        processing_grid.Add(self.preprocess_check, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        processing_grid.Add(self.normalize_check, (y, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        processing_grid.Add(self.inverse_check, (y, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        processing_grid.Add(self.subtract_check, (y, 3), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        processing_boxsizer.Add(processing_grid, 0, wx.EXPAND, 10)

        grid = wx.GridBagSizer(7, 5)
        y = 0
        grid.Add(ms_1_boxsizer, (y, 0), wx.GBSpan(1, 6), flag=wx.EXPAND)
        y += 1
        grid.Add(ms_2_boxsizer, (y, 0), wx.GBSpan(1, 6), flag=wx.EXPAND)
        y += 1
        grid.Add(processing_boxsizer, (y, 0), wx.GBSpan(1, 6), flag=wx.EXPAND)
        y += 1
        grid.Add(horizontal_line_1, (y, 0), wx.GBSpan(1, 6), flag=wx.EXPAND)
        y += 1
        grid.Add(settings_label, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(btn_grid, (y, 1), flag=wx.ALIGN_CENTER)
        y += 1
        grid.Add(horizontal_line_2, (y, 0), wx.GBSpan(1, 6), flag=wx.EXPAND)
        y += 1
        grid.Add(self.plot_btn, (y, 3), flag=wx.ALIGN_CENTER)
        grid.Add(self.cancel_btn, (y, 4), flag=wx.ALIGN_CENTER)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 0, wx.EXPAND, 10)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def make_plot_panel(self, split_panel):

        panel = wx.Panel(split_panel, -1, size=(-1, -1), name="plot")
        self.plot_panel = wx.Panel(panel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)

        pixel_size = [(self._window_size[0] - self._settings_panel_size[0]), (self._window_size[1] - 50)]
        figsize = [pixel_size[0] / self._display_resolution[0], pixel_size[1] / self._display_resolution[1]]

        self.plot_window = PlotSpectrum(self.plot_panel, figsize=figsize, config=self.config)

        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(self.plot_window, 1, wx.EXPAND)

        box.Fit(self.plot_panel)
        self.plot_window.SetSize(pixel_size)
        self.plot_panel.SetSizer(box)
        self.plot_panel.Layout()
        #

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
            spectrum_list_1 = natsorted(self.kwargs["document_spectrum_list"][document_1])
            self.spectrum_1_spectrum_value.SetItems(spectrum_list_1)
            self.spectrum_1_spectrum_value.SetStringSelection(spectrum_list_1[0])

        elif evtID == ID_compareMS_MS_2:
            document_2 = self.spectrum_2_document_value.GetStringSelection()
            spectrum_list_2 = natsorted(self.kwargs["document_spectrum_list"][document_2])
            self.spectrum_2_spectrum_value.SetItems(spectrum_list_2)
            self.spectrum_2_spectrum_value.SetStringSelection(spectrum_list_2[0])

    def on_apply(self, evt):
        if evt is not None:
            source = evt.GetEventObject().GetName()

        self.config.lineTransparency_MS1 = str2num(self.spectrum_1_transparency.GetValue()) / 100
        self.config.lineStyle_MS1 = self.spectrum_1_line_style_value.GetStringSelection()

        self.config.lineTransparency_MS2 = str2num(self.spectrum_2_transparency.GetValue()) / 100
        self.config.lineStyle_MS2 = self.spectrum_2_line_style_value.GetStringSelection()

        if evt is not None:
            self.on_plot_update_style(source)

    def on_toggle_controls(self, evt):
        if self.subtract_check.GetValue():
            self.inverse_check.SetValue(False)
            self.inverse_check.Disable()
        else:
            self.inverse_check.Enable()

        if evt is not None:
            evt.Skip()

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

        self.config.compare_massSpectrumParams["preprocess"] = self.preprocess_check.GetValue()
        self.config.compare_massSpectrumParams["inverse"] = self.inverse_check.GetValue()
        self.config.compare_massSpectrumParams["normalize"] = self.normalize_check.GetValue()
        self.config.compare_massSpectrumParams["subtract"] = self.subtract_check.GetValue()

        label_1 = self.spectrum_1_label_value.GetValue()
        if label_1 == "":
            label_1 = self.spectrum_1_spectrum_value.GetStringSelection()
        label_2 = self.spectrum_2_label_value.GetValue()
        if label_2 == "":
            label_2 = self.spectrum_2_spectrum_value.GetStringSelection()
        self.config.compare_massSpectrumParams["legend"] = [label_1, label_2]

        self.on_apply(None)

        if evt is not None:
            evt.Skip()

    def on_update_color(self, evt):
        """Update spectrum color"""
        # get object name
        source = evt.GetEventObject().GetName()

        # get color
        dlg = DialogColorPicker(self, self.config.customColors)
        if dlg.ShowModal() == "ok":
            color_255, color_1, __ = dlg.GetChosenColour()
            self.config.customColors = dlg.GetCustomColours()
        else:
            return

        # assign color
        if source == "color_1":
            self.config.lineColour_MS1 = color_1
            self.spectrum_1_color_btn.SetBackgroundColour(color_255)
        elif source == "color_2":
            self.config.lineColour_MS2 = color_1
            self.spectrum_2_color_btn.SetBackgroundColour(color_255)

        self.on_plot_update_style(source)

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

    def on_plot_update_style(self, source):
        tstart = ttime()

        index = self._get_dataset_index(source)

        kwargs = dict()
        if source.endswith("_1"):
            kwargs["color"] = self.config.lineColour_MS1
            kwargs["line_style"] = self.config.lineStyle_MS1
            kwargs["transparency"] = self.config.lineTransparency_MS1
        elif source.endswith("_2"):
            kwargs["color"] = self.config.lineColour_MS2
            kwargs["line_style"] = self.config.lineStyle_MS2
            kwargs["transparency"] = self.config.lineTransparency_MS2

        self.panel_plot.plot_1D_update_style_by_label(index, plot=None, plot_obj=self.plot_window, **kwargs)
        logger.info(f"Plot update took {ttime()-tstart:.2f} seconds.")

    def on_plot(self, evt):
        tstart = ttime()
        self.update_spectrum(None)

        __, spectrum_1 = self.data_handling.get_spectrum_data(self.config.compare_massSpectrum[0][:2])
        __, spectrum_2 = self.data_handling.get_spectrum_data(self.config.compare_massSpectrum[1][:2])

        xvals_1 = spectrum_1["xvals"]
        yvals_1 = spectrum_1["yvals"]

        xvals_2 = spectrum_2["xvals"]
        yvals_2 = spectrum_2["yvals"]

        if self.config.compare_massSpectrumParams["preprocess"]:
            xvals_1, yvals_1 = self.data_processing.on_process_MS(xvals_1, yvals_1, return_data=True)
            xvals_2, yvals_2 = self.data_processing.on_process_MS(xvals_2, yvals_2, return_data=True)

        if self.config.compare_massSpectrumParams["normalize"]:
            yvals_1 = pr_spectra.normalize_1D(yvals_1)
            yvals_2 = pr_spectra.normalize_1D(yvals_2)

        if self.config.compare_massSpectrumParams["inverse"] and not self.config.compare_massSpectrumParams["subtract"]:
            yvals_2 = -yvals_2

        if self.config.compare_massSpectrumParams["subtract"]:
            xvals_1, yvals_1, xvals_2, yvals_2 = self.data_processing.subtract_spectra(
                xvals_1, yvals_1, xvals_2, yvals_2
            )

        self.panel_plot.plot_compare_spectra(xvals_1, xvals_2, yvals_1, yvals_2, plot=None, plot_obj=self.plot_window)

        self._update_local_plot_information()
        logger.info(f"Plot update took {ttime()-tstart:.2f} seconds.")

    def _update_local_plot_information(self):
        # update local information about the plots
        spectrum_1_choice = deepcopy(self.config.compare_massSpectrum[0])
        spectrum_1_choice.append(self.config.compare_massSpectrumParams["legend"][0])
        spectrum_2_choice = deepcopy(self.config.compare_massSpectrum[1])
        spectrum_2_choice.append(self.config.compare_massSpectrumParams["legend"][1])

        self.compare_massSpectrum = [spectrum_1_choice, spectrum_2_choice]

    def on_clear_plot(self, evt):
        self.plot_window.clear()

    def on_save_figure(self, evt):
        document_title_1, spectrum_1 = self.config.compare_massSpectrum[0][:2]
        document_title_2, spectrum_2 = self.config.compare_massSpectrum[1][:2]

        plot_title = f"{document_title_1}_{spectrum_1}__{document_title_2}_{spectrum_2}".replace(" ", "-").replace(
            ":", ""
        )
        self.panel_plot.save_images(None, None, plot_obj=self.plot_window, image_name=plot_title)

    def on_open_process_MS_settings(self, evt):
        self.document_tree.on_open_process_MS_settings(disable_plot=True, disable_process=True)
