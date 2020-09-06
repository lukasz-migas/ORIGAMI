"""Overlay panel"""
# Standard library imports
import logging
from copy import deepcopy
from typing import Dict
from typing import List
from typing import Union

# Third-party imports
import wx
import wx.lib.scrolledpanel as wxScrolledPanel
from pubsub import pub

# Local imports
from origami.styles import MiniFrame
from origami.utils.color import get_random_color
from origami.utils.color import convert_rgb_1_to_255
from origami.utils.random import get_random_int
from origami.utils.secret import hash_obj
from origami.utils.system import running_under_pytest
from origami.config.config import CONFIG
from origami.config.environment import ENV
from origami.gui_elements.mixins import ColorGetterMixin
from origami.objects.groups.base import DataGroup
from origami.gui_elements.helpers import TableConfig
from origami.gui_elements.helpers import set_tooltip
from origami.gui_elements.helpers import make_color_btn
from origami.gui_elements.helpers import make_menu_item
from origami.gui_elements.helpers import make_bitmap_btn
from origami.gui_elements.helpers import make_spin_ctrl_int
from origami.gui_elements.helpers import make_spin_ctrl_double
from origami.gui_elements.panel_base import TableMixin
from origami.widgets.overlay.view_overlay import ViewOverlay
from origami.widgets.overlay.overlay_handler import OVERLAY_HANDLER
from origami.gui_elements.dialog_review_cards import DialogCardManager
from origami.widgets.overlay.panel_plot_parameters import PanelOverlayViewerSettings

LOGGER = logging.getLogger(__name__)


def _str_fmt(value, default: Union[str, float, int] = ""):
    if value is None:
        return str(default)
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


# TODO: add option to reduce number of colormaps
# TODO: add a way to export the plot config


class TableColumnIndex:
    """Table indexer"""

    check = 0
    order = 1
    name = 2
    dimensions = 3
    label = 4
    document_title = 5
    dataset_name = 6
    color = 7


class PanelOverlayViewer(MiniFrame, TableMixin, ColorGetterMixin):
    """Overlay viewer and editor"""

    # peaklist list
    TABLE_DICT = TableConfig()
    TABLE_DICT.add("", "check", "bool", 25, hidden=True)
    TABLE_DICT.add("#", "order", "int", 50)
    TABLE_DICT.add("name", "name", "str", 150)
    TABLE_DICT.add("dimensions", "dimensions", "str", 100)
    TABLE_DICT.add("label", "label", "str", 100)
    TABLE_DICT.add("document", "document_title", "str", 100)
    TABLE_DICT.add("full name", "dataset_name", "str", 0, hidden=True)
    TABLE_DICT.add("color", "color", "color", 0, hidden=True)
    TABLE_DICT.add("tag", "tag", "str", 0, hidden=True)
    TABLE_KWARGS = dict(
        add_item_color=True,
        color_in_column=True,
        color_column_id=TABLE_DICT.find_col_id("color"),
        color_in_column_255=True,
    )
    USE_COLOR = False
    TABLE_WIDGET_DICT = dict()

    # ui elements
    view_overlay, panel_book, action_btn, plot_btn = None, None, None, None
    add_to_document_btn, cancel_btn, overlay_1d_method = None, None, None
    overlay_1d_label, overlay_1d_line_style, overlay_1d_transparency, overlay_1d_color_btn = None, None, None, None
    overlay_1d_order, overlay_2d_method, overlay_2d_colormap, overlay_2d_label = None, None, None, None
    overlay_2d_color_btn, overlay_2d_min_threshold, overlay_2d_max_threshold, overlay_2d_mask = None, None, None, None
    overlay_2d_transparency, overlay_2d_order, settings_spectra, settings_heatmaps = None, None, None, None
    overlay_1d_name, overlay_2d_name, overlay_1d_document, overlay_2d_document = None, None, None, None
    overlay_1d_spectrum_type, overlay_1d_method_settings_btn, overlay_2d_method_settings_btn = None, None, None
    plot_settings = None

    def __init__(self, parent, presenter, icons=None, item_list=None, debug: bool = False):
        MiniFrame.__init__(
            self,
            parent,
            title="Overlay viewer & editor...",
            style=wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX,
            bind_key_events=False,
        )
        self.view = parent
        self.presenter = presenter
        self._icons = self._get_icons(icons)

        self._window_size = self._get_window_size(self.view, [0.9, 0.8])

        # preset
        self._debug = debug
        self.clipboard = dict()
        self.item_list = item_list
        self._disable_table_update = False
        self._current_item = None
        self._document = None

        # make gui items
        self.make_gui()
        self.on_populate_item_list(None)

        # bind
        self.Bind(wx.EVT_CONTEXT_MENU, self.on_right_click)

        self.setup()

    def setup(self):
        """Setup widget"""
        self.TABLE_WIDGET_DICT = {
            # 1d overlays
            self.overlay_1d_label: TableColumnIndex.label,
            self.overlay_1d_order: TableColumnIndex.order,
            self.overlay_1d_line_style: "line_style",
            self.overlay_1d_transparency: "transparency",
            # 2d overlays
            self.overlay_2d_label: TableColumnIndex.label,
            self.overlay_2d_order: TableColumnIndex.order,
            self.overlay_2d_min_threshold: "min_threshold",
            self.overlay_2d_max_threshold: "max_threshold",
            self.overlay_2d_transparency: "transparency",
            self.overlay_2d_mask: "mask",
            self.overlay_2d_colormap: "colormap",
        }
        self.peaklist.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_select_item)

    @property
    def current_item_id(self):
        """Returns the index of currently selected item in the table"""
        idx = self.on_find_item("tag", self._current_item)
        return idx

    @property
    def data_handling(self):
        """Return handle to `data_handling`"""
        return self.presenter.data_handling

    @property
    def document_tree(self):
        """Return handle to `document_tree`"""
        return self.presenter.view.panelDocuments.documents

    @property
    def current_page(self):
        """Returns index of the current page"""
        return self.panel_book.GetSelection()

    @property
    def current_method(self) -> str:
        """Returns current method depending on which window is shown"""
        if self.current_page == 0:
            method = self.overlay_1d_method.GetStringSelection()
        else:
            method = self.overlay_2d_method.GetStringSelection()
        return method

    @property
    def document(self):
        """Return instance of the document"""
        if self._document is None:
            self.on_open_document(None)
        return self._document

    def on_right_click(self, evt):
        """Right-click event handler"""
        # ensure that user clicked inside the plot area
        if not hasattr(evt.EventObject, "figure"):
            return

        menu = self.view_overlay.get_right_click_menu(self)
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def on_close(self, evt, force: bool = False):
        """Destroy this frame"""

        n_clipboard_items = len(self.clipboard)
        if n_clipboard_items > 0 and not force and not self._debug:
            from origami.gui_elements.misc_dialogs import DialogBox

            msg = (
                f"Found {n_clipboard_items} overlay item(s) in the clipboard. Closing this window will lose"
                + " your overlay plots. Would you like to continue?"
            )
            dlg = DialogBox(title="Clipboard is not empty", msg=msg, kind="Question")
            if dlg == wx.ID_NO:
                LOGGER.info("Action was cancelled")
                return

        super(PanelOverlayViewer, self).on_close(evt, force)

    def make_gui(self):
        """Make UI"""
        # make panel
        settings_panel = self.make_side_panel(self)

        # make plot
        plot_panel = self.make_plot_panel(self)

        # make extra
        self.plot_settings = PanelOverlayViewerSettings(self, self.view)

        # pack elements
        main_sizer = wx.BoxSizer()
        main_sizer.Add(settings_panel, 0, wx.EXPAND, 0)
        main_sizer.Add(plot_panel, 1, wx.EXPAND, 0)
        main_sizer.Add(self.plot_settings, 0, wx.EXPAND, 0)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizer(main_sizer)
        self.SetSize(self._window_size)
        self.Layout()

        self.CenterOnParent()
        self.SetFocus()
        self.Show()

    def make_side_panel(self, split_panel):
        """Make side panel"""
        panel = wxScrolledPanel.ScrolledPanel(split_panel, size=(-1, -1), name="main")

        # make settings
        notebook = self.make_settings_panel(panel)

        buttons_sizer = self.make_plot_buttons(panel)

        # make listctrl
        self.peaklist = self.make_table(self.TABLE_DICT, panel)

        # add statusbar
        info_sizer = self.make_statusbar(panel, "right")

        # set in sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(notebook, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND | wx.ALL, 1)
        main_sizer.Add(buttons_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)
        main_sizer.Add(self.peaklist, 1, wx.EXPAND, 10)
        main_sizer.Add(info_sizer, 0, wx.EXPAND | wx.ALL, 2)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)
        if not running_under_pytest():
            panel.SetupScrolling()

        return panel

    def make_plot_buttons(self, panel):
        """Make buttons sizer"""
        self.action_btn = wx.Button(panel, wx.ID_OK, "Action ▼", size=(-1, -1))
        self.action_btn.Bind(wx.EVT_BUTTON, self.on_action_tools)

        self.plot_btn = wx.Button(panel, wx.ID_OK, "Plot", size=(-1, -1))
        self.plot_btn.Bind(wx.EVT_BUTTON, self.on_plot_overlay)

        self.add_to_document_btn = wx.Button(panel, wx.ID_OK, "Add to document", size=(-1, -1))
        self.add_to_document_btn.Bind(wx.EVT_BUTTON, self.on_add_to_document)

        self.cancel_btn = wx.Button(panel, wx.ID_OK, "Cancel", size=(-1, -1))
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_close)

        sizer = wx.BoxSizer()
        sizer.Add(self.action_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer.AddSpacer(5)
        sizer.Add(self.plot_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer.AddSpacer(5)
        sizer.Add(self.add_to_document_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer.AddSpacer(5)
        sizer.Add(self.cancel_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        return sizer

    def make_settings_panel(self, split_panel):
        """Make settings notebook"""
        panel = wx.Panel(split_panel, -1, size=(-1, -1), name="settings")

        self.panel_book = wx.Choicebook(panel, wx.ID_ANY, style=wx.CHB_DEFAULT)
        self.panel_book.SetBackgroundColour((240, 240, 240))
        self.panel_book.Bind(wx.EVT_CHOICEBOOK_PAGE_CHANGED, self.on_populate_item_list)

        # add settings
        self.settings_spectra = self.make_settings_panel_mass_spectra(self.panel_book)
        self.panel_book.AddPage(self.settings_spectra, "Overlay: Spectra")

        self.settings_heatmaps = self.make_settings_panel_heatmaps(self.panel_book)
        self.panel_book.AddPage(self.settings_heatmaps, "Overlay: Heatmaps")

        settings_sizer = wx.BoxSizer(wx.VERTICAL)
        settings_sizer.Add(self.panel_book, 1, wx.EXPAND | wx.ALL, 0)
        settings_sizer.Fit(panel)
        settings_sizer.SetMinSize((380, -1))
        panel.SetSizerAndFit(settings_sizer)

        return panel

    # noinspection DuplicatedCode
    def make_settings_panel_mass_spectra(self, split_panel):
        """Make settings panel for spectral overlays"""
        panel = wx.Panel(split_panel, -1, size=(-1, -1), name="mass-spectra")

        overlay_1d_document = wx.StaticText(panel, -1, "Document title:")
        self.overlay_1d_document = wx.StaticText(panel, -1, "")

        overlay_1d_name = wx.StaticText(panel, -1, "Dataset name:")
        self.overlay_1d_name = wx.StaticText(panel, -1, "")

        overlay_1d_label = wx.StaticText(panel, -1, "Label:")
        self.overlay_1d_label = wx.TextCtrl(panel, -1, "", style=wx.TE_PROCESS_ENTER, name="overlay.1d.label")
        self.overlay_1d_label.Bind(wx.EVT_TEXT, self.on_edit_item)

        overlay_1d_line_style = wx.StaticText(panel, -1, "Line style:")
        self.overlay_1d_line_style = wx.ComboBox(
            panel, choices=CONFIG.lineStylesList, style=wx.CB_READONLY, name="overlay.1d.line"
        )
        self.overlay_1d_line_style.SetStringSelection(CONFIG.overlay_panel_1d_line_style)
        self.overlay_1d_line_style.Bind(wx.EVT_COMBOBOX, self.on_apply)
        self.overlay_1d_line_style.Bind(wx.EVT_COMBOBOX, self.on_edit_item)

        overlay_1d_transparency = wx.StaticText(panel, -1, "Transparency:")
        self.overlay_1d_transparency = make_spin_ctrl_double(panel, 0.5, 0, 1, 0.25, (90, -1), name="overlay.1d.line")
        self.overlay_1d_transparency.SetValue(CONFIG.overlay_panel_1d_line_transparency)
        self.overlay_1d_transparency.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.overlay_1d_transparency.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_edit_item)

        overlay_1d_color_btn = wx.StaticText(panel, -1, "Color:")
        self.overlay_1d_color_btn = make_color_btn(panel, CONFIG.overlay_panel_1d_line_color, name="overlay.1d.color")
        self.overlay_1d_color_btn.Bind(wx.EVT_BUTTON, self.on_update_color)

        overlay_1d_order = wx.StaticText(panel, -1, "Order:")
        self.overlay_1d_order = make_spin_ctrl_int(panel, 0, 0, 100, (90, -1), name="overlay.1d.order")
        self.overlay_1d_order.Bind(wx.EVT_SPINCTRL, self.on_apply)
        self.overlay_1d_order.Bind(wx.EVT_SPINCTRL, self.on_edit_item)

        overlay_1d_spectrum_type = wx.StaticText(panel, -1, "Spectrum type:")
        self.overlay_1d_spectrum_type = wx.ComboBox(
            panel, choices=CONFIG.overlay_panel_1d_type_choices, style=wx.CB_READONLY
        )
        self.overlay_1d_spectrum_type.SetStringSelection(CONFIG.overlay_panel_1d_type)
        self.overlay_1d_spectrum_type.Bind(wx.EVT_COMBOBOX, self.on_populate_item_list)

        overlay_1d_method = wx.StaticText(panel, -1, "Overlay method:")
        self.overlay_1d_method = wx.ComboBox(
            panel, choices=CONFIG.overlay_panel_1d_method_choices, style=wx.CB_READONLY
        )
        self.overlay_1d_method.SetStringSelection(CONFIG.overlay_panel_1d_method)

        self.overlay_1d_method_settings_btn = make_bitmap_btn(panel, -1, self._icons.gear)
        self.overlay_1d_method_settings_btn.Bind(wx.EVT_BUTTON, self.on_open_method_settings)
        set_tooltip(self.overlay_1d_method_settings_btn, "Customise overlay plot...")

        # pack heatmap items
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(overlay_1d_document, (n, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.overlay_1d_document, (n, 1), (1, 3), flag=wx.EXPAND)
        n += 1
        grid.Add(overlay_1d_name, (n, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.overlay_1d_name, (n, 1), (1, 3), flag=wx.EXPAND)
        n += 1
        grid.Add(overlay_1d_label, (n, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.overlay_1d_label, (n, 1), (1, 3), flag=wx.EXPAND)
        n += 1
        grid.Add(overlay_1d_line_style, (n, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.overlay_1d_line_style, (n, 1), flag=wx.EXPAND)
        grid.Add(overlay_1d_transparency, (n, 2), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.overlay_1d_transparency, (n, 3), flag=wx.EXPAND)
        n += 1
        grid.Add(overlay_1d_color_btn, (n, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.overlay_1d_color_btn, (n, 1), flag=wx.EXPAND)
        grid.Add(overlay_1d_order, (n, 2), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.overlay_1d_order, (n, 3), flag=wx.EXPAND)
        n += 1
        n += 1
        grid.Add(overlay_1d_spectrum_type, (n, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.overlay_1d_spectrum_type, (n, 1), (1, 3), flag=wx.EXPAND)
        n += 1
        grid.Add(overlay_1d_method, (n, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.overlay_1d_method, (n, 1), (1, 3), flag=wx.EXPAND)
        grid.Add(self.overlay_1d_method_settings_btn, (n, 4), flag=wx.ALIGN_CENTER_VERTICAL)

        settings_sizer = wx.BoxSizer(wx.VERTICAL)
        settings_sizer.Add(grid, 1, wx.EXPAND | wx.ALL, 0)
        settings_sizer.Fit(panel)
        panel.SetSizerAndFit(settings_sizer)

        return panel

    # noinspection DuplicatedCode
    def make_settings_panel_heatmaps(self, split_panel):
        """Make settings panel for heatmap overlays"""
        panel = wx.Panel(split_panel, -1, size=(-1, -1), name="heatmaps")

        overlay_2d_document = wx.StaticText(panel, -1, "Document title:")
        self.overlay_2d_document = wx.StaticText(panel, -1, "")

        overlay_2d_name = wx.StaticText(panel, -1, "Dataset name:")
        self.overlay_2d_name = wx.StaticText(panel, -1, "")

        overlay_2d_label = wx.StaticText(panel, -1, "Label:")
        self.overlay_2d_label = wx.TextCtrl(panel, -1, "", style=wx.TE_PROCESS_ENTER, name="overlay.2d.label")
        self.overlay_2d_label.Bind(wx.EVT_TEXT, self.on_edit_item)

        overlay_2d_colormap = wx.StaticText(panel, -1, "Colormap:")
        self.overlay_2d_colormap = wx.ComboBox(
            panel, choices=CONFIG.colormap_choices, style=wx.CB_READONLY, name="overlay.2d.colormap"
        )
        self.overlay_2d_colormap.SetStringSelection(CONFIG.overlay_panel_2d_heatmap_colormap)
        self.overlay_2d_colormap.Bind(wx.EVT_COMBOBOX, self.on_apply)
        self.overlay_2d_colormap.Bind(wx.EVT_COMBOBOX, self.on_edit_item)

        overlay_2d_color_btn = wx.StaticText(panel, -1, "Color:")
        self.overlay_2d_color_btn = make_color_btn(
            panel, CONFIG.overlay_panel_2d_heatmap_color, name="overlay.2d.color"
        )
        self.overlay_2d_color_btn.Bind(wx.EVT_BUTTON, self.on_update_color)

        overlay_2d_min_threshold = wx.StaticText(panel, -1, "Min threshold:")
        self.overlay_2d_min_threshold = make_spin_ctrl_double(
            panel, 0.5, 0, 1, 0.25, (90, -1), name="overlay.2d.threshold"
        )
        self.overlay_2d_min_threshold.SetValue(CONFIG.overlay_panel_2d_heatmap_min_threshold)
        self.overlay_2d_min_threshold.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.overlay_2d_min_threshold.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_edit_item)

        overlay_2d_max_threshold = wx.StaticText(panel, -1, "Max threshold:")
        self.overlay_2d_max_threshold = make_spin_ctrl_double(
            panel, 0.5, 0, 1, 0.25, (90, -1), name="overlay.2d.threshold"
        )
        self.overlay_2d_max_threshold.SetValue(CONFIG.overlay_panel_2d_heatmap_max_threshold)
        self.overlay_2d_max_threshold.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.overlay_2d_max_threshold.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_edit_item)

        overlay_2d_transparency = wx.StaticText(panel, -1, "Transparency:")
        self.overlay_2d_transparency = make_spin_ctrl_double(
            panel, 0.5, 0, 1, 0.25, (90, -1), name="overlay.2d.transparency"
        )
        self.overlay_2d_transparency.SetValue(CONFIG.overlay_panel_2d_heatmap_transparency)
        self.overlay_2d_transparency.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.overlay_2d_transparency.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_edit_item)

        overlay_2d_mask = wx.StaticText(panel, -1, "Mask:")
        self.overlay_2d_mask = make_spin_ctrl_double(panel, 0.5, 0, 1, 0.25, (90, -1), name="overlay.2d.mask")
        self.overlay_2d_mask.SetValue(CONFIG.overlay_panel_2d_heatmap_mask)
        self.overlay_2d_mask.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)
        self.overlay_2d_mask.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_edit_item)

        overlay_2d_order = wx.StaticText(panel, -1, "Order:")
        self.overlay_2d_order = make_spin_ctrl_int(panel, 0, 0, 100, (90, -1), name="overlay.2d.order")
        self.overlay_2d_order.Bind(wx.EVT_SPINCTRL, self.on_apply)
        self.overlay_2d_order.Bind(wx.EVT_SPINCTRL, self.on_edit_item)

        overlay_2d_method = wx.StaticText(panel, -1, "Overlay method:")
        self.overlay_2d_method = wx.ComboBox(
            panel, choices=CONFIG.overlay_panel_2d_method_choices, style=wx.CB_READONLY
        )
        self.overlay_2d_method.SetStringSelection(CONFIG.overlay_panel_2d_method)

        self.overlay_2d_method_settings_btn = make_bitmap_btn(panel, -1, self._icons.gear)
        self.overlay_2d_method_settings_btn.Bind(wx.EVT_BUTTON, self.on_open_method_settings)
        set_tooltip(self.overlay_2d_method_settings_btn, "Customise overlay plot...")

        # pack heatmap items
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(overlay_2d_document, (n, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.overlay_2d_document, (n, 1), (1, 3), flag=wx.EXPAND)
        n += 1
        grid.Add(overlay_2d_name, (n, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.overlay_2d_name, (n, 1), (1, 3), flag=wx.EXPAND)
        n += 1
        grid.Add(overlay_2d_label, (n, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.overlay_2d_label, (n, 1), (1, 3), flag=wx.EXPAND)
        n += 1
        grid.Add(overlay_2d_colormap, (n, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.overlay_2d_colormap, (n, 1), flag=wx.EXPAND)
        grid.Add(overlay_2d_color_btn, (n, 2), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.overlay_2d_color_btn, (n, 3), flag=wx.EXPAND)
        n += 1
        grid.Add(overlay_2d_min_threshold, (n, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.overlay_2d_min_threshold, (n, 1), flag=wx.EXPAND)
        grid.Add(overlay_2d_max_threshold, (n, 2), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.overlay_2d_max_threshold, (n, 3), flag=wx.EXPAND)
        n += 1
        grid.Add(overlay_2d_transparency, (n, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.overlay_2d_transparency, (n, 1), flag=wx.EXPAND)
        grid.Add(overlay_2d_mask, (n, 2), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.overlay_2d_mask, (n, 3), flag=wx.EXPAND)
        n += 1
        grid.Add(overlay_2d_order, (n, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.overlay_2d_order, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(overlay_2d_method, (n, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.overlay_2d_method, (n, 1), (1, 3), flag=wx.EXPAND)
        grid.Add(self.overlay_2d_method_settings_btn, (n, 4), flag=wx.ALIGN_CENTER_VERTICAL)

        settings_sizer = wx.BoxSizer(wx.VERTICAL)
        settings_sizer.Add(grid, 1, wx.EXPAND | wx.ALL, 0)
        settings_sizer.Fit(panel)
        panel.SetSizerAndFit(settings_sizer)

        return panel

    # noinspection DuplicatedCode
    def make_plot_panel(self, split_panel):
        """Make plot panel"""
        self.view_overlay = ViewOverlay(
            split_panel, (0.01, 0.01), x_label="x-axis", y_label="y-axis", filename="overlay"
        )

        return self.view_overlay.panel

    def on_apply(self, evt):
        """Apply settings in config"""
        # 1d overlays
        CONFIG.overlay_panel_1d_method = self.overlay_1d_method.GetStringSelection()
        CONFIG.overlay_panel_1d_line_style = self.overlay_1d_line_style.GetStringSelection()
        CONFIG.overlay_panel_1d_line_transparency = self.overlay_1d_transparency.GetValue()

        # 2d overlays
        CONFIG.overlay_panel_2d_method = self.overlay_2d_method.GetStringSelection()
        CONFIG.overlay_panel_2d_heatmap_colormap = self.overlay_2d_colormap.GetStringSelection()
        CONFIG.overlay_panel_2d_heatmap_transparency = self.overlay_2d_transparency.GetValue()
        CONFIG.overlay_panel_2d_heatmap_mask = self.overlay_2d_mask.GetValue()
        CONFIG.overlay_panel_2d_heatmap_min_threshold = self.overlay_2d_min_threshold.GetValue()
        CONFIG.overlay_panel_2d_heatmap_max_threshold = self.overlay_2d_max_threshold.GetValue()

        self._parse_evt(evt)

    def on_select_item(self, evt):
        """Select calibrant from the table and populate fields"""
        self._disable_table_update = True
        if hasattr(evt, "GetIndex"):
            self.peaklist.item_id = evt.GetIndex()

        # get metadata contained within the table
        item_info = self.on_get_item_information()

        # get metadata contained within the config file
        metadata = self.get_item_metadata(item_info)

        # update UI based on which page is selected
        if self.current_page == 0:
            self.overlay_1d_name.SetLabel(item_info["dataset_name"])
            self.overlay_1d_document.SetLabel(item_info["document_title"])
            self.overlay_1d_order.SetValue(item_info["order"])
            self.overlay_1d_label.SetValue(_str_fmt(item_info["label"]))
            self.overlay_1d_color_btn.SetBackgroundColour(item_info["color"])
            self.overlay_1d_line_style.SetStringSelection(
                metadata.get("line_style", CONFIG.overlay_panel_1d_line_style)
            )
            self.overlay_1d_transparency.SetValue(
                metadata.get("transparency", CONFIG.overlay_panel_1d_line_transparency)
            )
        else:
            self.overlay_2d_name.SetLabel(item_info["dataset_name"])
            self.overlay_2d_document.SetLabel(item_info["document_title"])
            self.overlay_2d_order.SetValue(item_info["order"])
            self.overlay_2d_label.SetValue(_str_fmt(item_info["label"]))
            self.overlay_2d_color_btn.SetBackgroundColour(item_info["color"])
            self.overlay_2d_colormap.SetStringSelection(
                metadata.get("colormap", CONFIG.overlay_panel_2d_heatmap_colormap)
            )
            self.overlay_2d_transparency.SetValue(
                metadata.get("transparency", CONFIG.overlay_panel_2d_heatmap_transparency)
            )
            self.overlay_2d_mask.SetValue(metadata.get("mask", CONFIG.overlay_panel_2d_heatmap_mask))
            self.overlay_2d_min_threshold.SetValue(
                metadata.get("min_threshold", CONFIG.overlay_panel_2d_heatmap_min_threshold)
            )
            self.overlay_2d_max_threshold.SetValue(
                metadata.get("max_threshold", CONFIG.overlay_panel_2d_heatmap_max_threshold)
            )
        self._current_item = item_info["tag"]
        self._disable_table_update = False
        LOGGER.debug(f"Selected `{self._current_item}`")

    def on_edit_item(self, evt):
        """Edit calibrant that is already in the table"""
        # in certain circumstances, it is better not to update the table
        if self._disable_table_update:
            return
        # get ui object that created this event
        obj = evt.GetEventObject()

        # get current item in the table that is being edited
        item_id = self.on_find_item("tag", self._current_item)
        if item_id == -1:
            return

        # get current column
        col_id = self.TABLE_WIDGET_DICT.get(obj, -1)
        if col_id == -1:
            return

        if isinstance(col_id, str):
            self.update_item_metadata(item_id)
            return

        # update item in the table
        self.peaklist.SetItem(item_id, col_id, str(obj.GetValue()))
        self.update_item_metadata(item_id)

    def on_update_color(self, evt):
        """Update color in the ui and table"""
        # get id and source
        source = evt.GetEventObject().GetName()

        # get color
        color_255, color_1, font_color = self.on_get_color(None)
        if color_1 is None:
            return

        if source == "overlay.1d.color":
            self.overlay_1d_color_btn.SetBackgroundColour(color_255)
        elif source == "overlay.2d.color":
            self.overlay_2d_color_btn.SetBackgroundColour(color_255)

        # update table
        item_id = self.current_item_id
        if item_id >= 0:
            self.peaklist.SetItem(item_id, TableColumnIndex.color, str(color_255))
            # self.peaklist.SetItemBackgroundColour(item_id, color_255)
            # self.peaklist.SetItemTextColour(item_id, font_color)
            self.update_item_metadata(item_id)

    def update_item_metadata(self, item_id: int):
        """Update metadata in the DocumentStore based on what is contained within the ui controls"""
        item_info = self.on_get_item_information(item_id)

        # get document
        document = ENV.on_get_document(item_info["document_title"])
        if document is None or item_info["tag"] != self._current_item:
            return

        # set data in the document
        obj = document[item_info["dataset_name"], True, True]
        obj.add_metadata("overlay", self.get_current_overlay_metadata(item_info))
        LOGGER.debug(f"Flushed metadata to disk for `{item_info['tag']}` item")

    @staticmethod
    def get_item_metadata(item_info: Dict) -> Dict:
        """Get metadata from the DocumentStore"""
        document = ENV.on_get_document(item_info["document_title"])
        if document is None:
            return dict()

        # set data in the document
        obj = document[item_info["dataset_name"], True, True]
        return obj.get_metadata("overlay", dict())

    def get_current_overlay_metadata(self, item_info: Dict) -> Dict:
        """Returns dictionary containing metadata that is currently set in the UI"""
        metadata = dict()
        if self.current_page == 0:
            metadata.update(
                {
                    "line_style": self.overlay_1d_line_style.GetStringSelection(),
                    "transparency": float(self.overlay_1d_transparency.GetValue()),
                }
            )
        else:
            metadata.update(
                {
                    "colormap": self.overlay_2d_colormap.GetStringSelection(),
                    "min_threshold": float(self.overlay_2d_min_threshold.GetValue()),
                    "max_threshold": float(self.overlay_2d_max_threshold.GetValue()),
                    "transparency": float(self.overlay_2d_transparency.GetValue()),
                    "mask": float(self.overlay_2d_mask.GetValue()),
                }
            )
        metadata.update({"color": item_info["color_255to1"], "order": item_info["order"], "label": item_info["label"]})
        return metadata

    @staticmethod
    def get_default_overlay_metadata(idx: int):
        """Return default overlay type"""
        metadata = dict()
        if idx == 0:
            metadata.update(
                {
                    "line_style": CONFIG.overlay_panel_1d_line_style,
                    "transparency": CONFIG.overlay_panel_1d_line_transparency,
                    "color": CONFIG.overlay_panel_1d_line_color,
                }
            )
        else:
            metadata.update(
                {
                    "colormap": CONFIG.overlay_panel_2d_heatmap_colormap,
                    "min_threshold": CONFIG.overlay_panel_2d_heatmap_min_threshold,
                    "max_threshold": CONFIG.overlay_panel_2d_heatmap_max_threshold,
                    "transparency": CONFIG.overlay_panel_2d_heatmap_transparency,
                    "mask": CONFIG.overlay_panel_2d_heatmap_mask,
                    "color": CONFIG.overlay_panel_2d_heatmap_color,
                }
            )
        metadata.update({"order": 0, "label": ""})

    def get_selected_items(self):
        """Get list of selected items"""
        indices = self.get_checked_items()
        item_list = []
        for item_id in indices:
            item_info = self.on_get_item_information(item_id)
            item_list.append([item_info["document_title"], item_info["dataset_name"]])

            # update selection
            self.peaklist.item_id = item_id
            self.on_select_item(None)
            self.update_item_metadata(item_id)  # flush to hard drive
        return item_list

    def on_plot_overlay(self, _evt):
        """Plot overlap"""
        item_list = self.get_selected_items()

        current_page = self.current_page
        if current_page == 0:  # spectra
            self.on_overlay_spectra(item_list)
        else:  # heatmaps
            self.on_overlay_heatmap(item_list)

    def on_overlay_spectra(self, item_list):
        """Overlay spectra objects"""
        method = self.overlay_1d_method.GetStringSelection()
        spectral_type = self.overlay_1d_spectrum_type.GetStringSelection()

        group_obj, valid_x, valid_y = OVERLAY_HANDLER.collect_overlay_1d_spectra(item_list, spectral_type, True)

        plt_funcs = {
            "Butterfly (n=2)": self.on_plot_1d_butterfly,
            "Subtract (n=2)": self.on_plot_1d_subtract,
            "Overlay": self.on_plot_1d_overlay,
            "Waterfall": self.on_plot_1d_waterfall,
        }

        plt_func = plt_funcs.get(method, None)
        if plt_func is None:
            LOGGER.error("Method not implemented yet")
            return

        # plot function
        kwargs = plt_func(group_obj)  # noqa

        # set metadata
        group_obj.set_metadata({"overlay": kwargs})

        title = OVERLAY_HANDLER.get_group_title(method, item_list)
        self.add_to_clipboard(method, title, group_obj, item_list)

    def on_plot_1d_butterfly(self, group_obj):
        """Heatmap plot"""
        x_top, x_bottom, y_top, y_bottom, kwargs = OVERLAY_HANDLER.prepare_overlay_1d_butterfly(group_obj)
        kwargs = self.view_overlay.plot_1d_compare(x_top, x_bottom, y_top, y_bottom, forced_kwargs=kwargs)
        return kwargs

    def on_plot_1d_subtract(self, group_obj):
        """Heatmap plot"""
        x_top, x_bottom, y_top, y_bottom, kwargs = OVERLAY_HANDLER.prepare_overlay_1d_subtract(group_obj)
        kwargs = self.view_overlay.plot_1d_compare(x_top, x_bottom, y_top, y_bottom, forced_kwargs=kwargs)
        return kwargs

    def on_plot_1d_overlay(self, group_obj):
        """Heatmap plot"""
        x, y, array = OVERLAY_HANDLER.prepare_overlay_1d_multiline(group_obj)
        kwargs = self.view_overlay.plot_1d_overlay(x, y, array, forced_kwargs=dict(waterfall_increment=0))
        return kwargs

    def on_plot_1d_waterfall(self, group_obj):
        """Heatmap plot"""
        x, y, array = OVERLAY_HANDLER.prepare_overlay_1d_multiline(group_obj)
        kwargs = self.view_overlay.plot_1d_overlay(x, y, array)
        return kwargs

    def on_overlay_heatmap(self, item_list):
        """Overlay heatmap objects"""
        method = self.overlay_2d_method.GetStringSelection()
        group_obj, valid_x, valid_y = OVERLAY_HANDLER.collect_overlay_2d_heatmap(item_list, False)

        plt_funcs = {
            "Mean": self.on_plot_2d_mean,
            "Standard Deviation": self.on_plot_2d_stddev,
            "Variance": self.on_plot_2d_variance,
            "RMSD": self.on_plot_2d_rmsd,
            "RMSF": self.on_plot_2d_rmsf,
            "RMSD Matrix": self.on_plot_2d_rmsd_matrix,
            "RMSD Dot": self.on_plot_2d_rmsd_dot,
            "Mask": self.on_plot_2d_mask,
            "Transparent": self.on_plot_2d_transparent,
            "Grid (2->1)": self.on_plot_2d_tto,
            "Grid (NxN)": self.on_plot_2d_nxn,
            "Side-by-side": self.on_plot_2d_side_by_side,
            "RGB": self.on_plot_2d_rgb,
        }

        plt_func = plt_funcs.get(method, None)
        if plt_func is None:
            LOGGER.error("Method not implemented yet")
            return

        # plot function
        kwargs = plt_func(group_obj)  # noqa

        # set metadata
        group_obj.set_metadata({"overlay": kwargs})

        title = OVERLAY_HANDLER.get_group_title(method, item_list)
        self.add_to_clipboard(method, title, group_obj, item_list)

    def on_plot_2d_mean(self, group_obj):
        """Heatmap plot"""
        array, x, y, x_label, y_label = OVERLAY_HANDLER.prepare_overlay_2d_mean(group_obj)
        kwargs = self.view_overlay.plot_2d_heatmap(x, y, array, x_label=x_label, y_label=y_label)
        return kwargs

    def on_plot_2d_stddev(self, group_obj):
        """Heatmap plot"""
        array, x, y, x_label, y_label = OVERLAY_HANDLER.prepare_overlay_2d_stddev(group_obj)
        kwargs = self.view_overlay.plot_2d_heatmap(x, y, array, x_label=x_label, y_label=y_label)
        return kwargs

    def on_plot_2d_variance(self, group_obj):
        """Heatmap plot"""
        array, x, y, x_label, y_label = OVERLAY_HANDLER.prepare_overlay_2d_variance(group_obj)
        kwargs = self.view_overlay.plot_2d_heatmap(x, y, array, x_label=x_label, y_label=y_label)
        return kwargs

    def on_plot_2d_rmsd(self, group_obj):
        """Heatmap plot"""
        array, x, y, x_label, y_label, rmsd_label = OVERLAY_HANDLER.prepare_overlay_2d_rmsd(group_obj)
        kwargs = self.view_overlay.plot_2d_rmsd(x, y, array, rmsd_label, x_label=x_label, y_label=y_label)
        return kwargs

    def on_plot_2d_rmsf(self, group_obj):
        """Heatmap plot"""
        array, x, y, rmsf_y, x_label, y_label, rmsd_label = OVERLAY_HANDLER.prepare_overlay_2d_rmsf(group_obj)
        kwargs = self.view_overlay.plot_2d_rmsf(x, y, array, rmsf_y, rmsd_label, x_label=x_label, y_label=y_label)
        return kwargs

    def on_plot_2d_rmsd_matrix(self, group_obj):
        """Heatmap plot"""
        array, x, y, tick_labels = OVERLAY_HANDLER.prepare_overlay_2d_rmsd_matrix(group_obj)
        kwargs = self.view_overlay.plot_2d_rmsd_matrix(x, y, array, tick_labels)
        return kwargs

    def on_plot_2d_rmsd_dot(self, group_obj):
        """Heatmap plot"""
        array, x, y, tick_labels = OVERLAY_HANDLER.prepare_overlay_2d_rmsd_matrix(group_obj)
        kwargs = self.view_overlay.plot_2d_rmsd_dot(x, y, array, tick_labels)
        return kwargs

    def on_plot_2d_mask(self, group_obj):
        """Heatmap plot"""
        array_1, array_2, x, y, x_label, y_label, kwargs = OVERLAY_HANDLER.prepare_overlay_2d_mask(group_obj)
        kwargs = self.view_overlay.plot_2d_overlay(
            x, y, array_1, array_2, x_label=x_label, y_label=y_label, forced_kwargs=kwargs
        )
        return kwargs

    def on_plot_2d_transparent(self, group_obj):
        """Heatmap plot"""
        array_1, array_2, x, y, x_label, y_label, kwargs = OVERLAY_HANDLER.prepare_overlay_2d_transparent(group_obj)
        kwargs = self.view_overlay.plot_2d_overlay(
            x, y, array_1, array_2, x_label=x_label, y_label=y_label, forced_kwargs=kwargs
        )
        return kwargs

    def on_plot_2d_tto(self, group_obj):
        """Heatmap plot"""
        a_1, a_2, array, x, y, x_label, y_label, rmsd_label = OVERLAY_HANDLER.prepare_overlay_2d_grid_compare_rmsd(
            group_obj
        )
        kwargs = self.view_overlay.plot_2d_grid_compare_rmsd(
            x, y, a_1, a_2, array, rmsd_label, x_label=x_label, y_label=y_label
        )
        return kwargs

    def on_plot_2d_nxn(self, group_obj):
        """Heatmap plot"""
        arrays, x, y, x_label, y_label, n_rows, n_cols = OVERLAY_HANDLER.prepare_overlay_2d_grid_n_x_n(group_obj)
        kwargs = self.view_overlay.plot_2d_grid_n_x_n(x, y, arrays, n_rows, n_cols, x_label=x_label, y_label=y_label)
        return kwargs

    def on_plot_2d_side_by_side(self, group_obj):
        """Heatmap plot"""
        arrays, x, y, x_label, y_label, n_rows, n_cols = OVERLAY_HANDLER.prepare_overlay_2d_grid_n_x_n(
            group_obj, n_max=2
        )
        kwargs = self.view_overlay.plot_2d_grid_n_x_n(x, y, arrays, n_rows, n_cols, x_label=x_label, y_label=y_label)
        return kwargs

    def on_plot_2d_rgb(self, group_obj):
        """Heatmap plot"""
        array, x, y, x_label, y_label, forced_kwargs = OVERLAY_HANDLER.prepare_overlay_2d_rgb(group_obj)
        kwargs = self.view_overlay.plot_2d_rgb(
            x, y, array, x_label=x_label, y_label=y_label, forced_kwargs=forced_kwargs
        )
        return kwargs

    def add_to_clipboard(self, method: str, title: str, group: DataGroup, item_list: List):
        """Add group object to the clipboard"""
        # keep track of what method is associated with the selected items - this is necessary in case the same objects
        # are compared but different method is used
        item_list_ = deepcopy(item_list)
        item_list_.append(method)
        item_id = hash_obj(item_list_)

        # check whether there are any objects with the same name and if so, append a number
        for _item_id, _item in self.clipboard.items():
            if item_id == _item_id:
                continue
            if title == _item["title"]:
                title += f" #{get_random_int()}"

        # add to clipboard
        self.clipboard[item_id] = dict(method=method, title=title, group=group, item_id=item_id)

    def on_add_to_document(self, _evt):
        """Add data to document"""
        item_list = []
        for item in self.clipboard.values():
            method = item["method"]
            item_list.append(
                {"item_id": item["item_id"], "title": item["title"], "about": item["group"].pprint(method)}
            )

        dlg = DialogCardManager(self, item_list)
        res = dlg.ShowModal()
        if res == wx.ID_NO:
            return
        output_list = dlg.output_list
        if not output_list:
            pub.sendMessage("notify.message.warning", "The output list was empty. Action was cancelled")
            return

        # get document where data can be saved to
        document = self.document
        if not document:
            pub.sendMessage("notify.message.warning", "The Comparison document was not set. Action was cancelled")
            return

        for item_id, title in output_list:
            item = self.clipboard.pop(item_id)
            document.add_overlay(title, item["group"])
            LOGGER.debug(f"Added {title} to the {document.title} document")

    def on_action_tools(self, _evt):
        """Display action menu"""
        menu = wx.Menu()

        menu_action_create_blank_document = make_menu_item(
            parent=menu, text="Create/open `Comparison` document", bitmap=self._icons.new
        )
        self.Bind(wx.EVT_MENU, self.on_open_document, menu_action_create_blank_document)
        menu.AppendItem(menu_action_create_blank_document)

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def on_open_document(self, _evt):
        """Open new document where comparison data can be saved"""
        document = self._on_get_document()
        self._document = document

    def _on_get_document(self):
        """Get instance of selected document - the dialog also allows the user to load already existing document that
        is not found in the environment or create a new one if one does not exist."""
        from origami.gui_elements.dialog_select_document import DialogSelectDocument

        document_title = None

        dlg = DialogSelectDocument(self, document_type="Type: Comparison")
        if dlg.ShowModal() == wx.ID_OK:
            document_title = dlg.current_document
        dlg.Destroy()

        if document_title is not None:
            return ENV[document_title]

    def on_open_method_settings(self, _evt):
        """Show all relevant parameters for the currently used method"""
        self.plot_settings.setup_method_settings(self.current_method)

    def on_populate_item_list(self, _evt):
        """Populate item list"""
        item_list = self.item_list
        if not isinstance(item_list, (list, tuple)):
            return
        self.peaklist.DeleteAllItems()
        self._on_populate_item_list(item_list)

    def _on_populate_item_list(self, item_list: List[str]):
        """Populate table with items"""
        idx = self.current_page
        spectrum_type = self.overlay_1d_spectrum_type.GetSelection()

        filter_by = {0: [["MassSpectra/"], ["Chromatograms/"], ["Mobilograms/"]], 1: ["IonHeatmaps/"]}[idx]
        if idx == 0:
            filter_by = filter_by[spectrum_type]

        for item in item_list:
            if any([item[0].startswith(_filter_key) for _filter_key in filter_by]):
                # get document and dataset information
                dataset_name, document_title = item[0], item[1]
                _, name = dataset_name.split("/")

                # retrieve any saved metadata
                metadata = self.get_item_metadata({"document_title": document_title, "dataset_name": dataset_name})
                color = metadata.get("color", get_random_color())

                # add to table
                self.on_add_to_table(
                    {
                        "name": name,
                        "dataset_name": dataset_name,
                        "document_title": document_title,
                        "dimensions": str(item[2]),
                        "label": _str_fmt(item[3]),
                        "order": _str_fmt(item[4], "0"),
                        "tag": str(item[5]),
                        "color": convert_rgb_1_to_255(color),
                    },
                    check_color=False,
                )


def _main():
    from origami.utils.screen import move_to_different_screen
    from origami.utils.secret import get_short_hash

    item_list = [
        ["MassSpectra/Summed Spectrum", "Title", "(1000,)", "TEST\n\n\nTEST", None, get_short_hash()],
        ["MassSpectra/rt=0-15", "Title", "(1000,)", "", 0, get_short_hash()],
        ["MassSpectra/rt=41-42", "Title", "(1000,)", "label ", 0, get_short_hash()],
        ["Chromatograms/Summed Chromatogram", "Title", "(513,)", "", 0, get_short_hash()],
        ["Mobilogram/Summed Mobilogram", "Title", "(200,)", "", 0, get_short_hash()],
        ["IonHeatmaps/Summed Heatmap", "Title", "(200, 500)", "label 3", 0, get_short_hash()],
    ]

    app = wx.App()
    ex = PanelOverlayViewer(None, None, item_list=item_list, debug=True)

    ex.Show()
    move_to_different_screen(ex)
    app.MainLoop()


if __name__ == "__main__":
    _main()
