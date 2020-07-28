"""Annotations editor"""
# Standard library imports
import time
import logging
from enum import IntEnum
from typing import Dict
from typing import Union
from typing import Optional
from builtins import isinstance

# Third-party imports
import wx
import numpy as np

import wx.lib.scrolledpanel as wxScrolledPanel
from pubsub import pub

# Local imports
from origami.styles import MiniFrame
from origami.styles import Validator
from origami.styles import make_checkbox
from origami.styles import make_menu_item
from origami.styles import make_bitmap_btn
from origami.utils.check import check_value_order
from origami.utils.color import round_rgb
from origami.utils.color import convert_rgb_1_to_255
from origami.utils.color import convert_rgb_255_to_1
from origami.utils.screen import calculate_window_size
from origami.utils.secret import get_short_hash
from origami.config.config import CONFIG
from origami.utils.utilities import report_time
from origami.utils.converters import rounder
from origami.utils.converters import str2num
from origami.utils.exceptions import MessageError
from origami.gui_elements.popup import PopupBase
from origami.objects.containers import DataObject
from origami.gui_elements._panel import TestPanel  # noqa
from origami.objects.annotations import Annotation
from origami.objects.annotations import Annotations
from origami.gui_elements.panel_base import TableMixin
from origami.gui_elements.panel_base import DatasetMixin
from origami.gui_elements.misc_dialogs import DialogBox
from origami.gui_elements.views.view_heatmap import ViewIonHeatmap
from origami.gui_elements.views.view_heatmap import ViewMassSpectrumHeatmap
from origami.gui_elements.views.view_spectrum import ViewMobilogram
from origami.gui_elements.views.view_spectrum import ViewChromatogram
from origami.gui_elements.views.view_spectrum import ViewMassSpectrum

# Module globals
logger = logging.getLogger(__name__)


class TableColumnIndex(IntEnum):
    """Table indexer"""

    check = 0
    label = 1
    label_color = 2
    arrow = 3
    patch = 4
    patch_color = 5
    name = 6


class PopupAnnotationSettings(PopupBase):
    """Create popup window to modify few uncommon settings"""

    highlight_on_selection = None
    zoom_on_selection = None
    zoom_window_size = None

    def __init__(self, parent, style=wx.BORDER_SIMPLE):
        PopupBase.__init__(self, parent, style)

    def make_panel(self):
        """Make popup window"""
        self.highlight_on_selection = make_checkbox(self, "")
        self.highlight_on_selection.SetValue(CONFIG.annotate_panel_highlight)
        self.highlight_on_selection.Bind(wx.EVT_CHECKBOX, self.on_apply)

        self.zoom_on_selection = make_checkbox(self, "")
        self.zoom_on_selection.SetValue(CONFIG.annotate_panel_zoom_in)
        self.zoom_on_selection.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.zoom_on_selection.Bind(wx.EVT_CHECKBOX, self.on_toggle)

        self.zoom_window_size = wx.SpinCtrlDouble(
            self,
            -1,
            value=str(CONFIG.annotate_panel_zoom_in_window),
            min=0.0001,
            max=250,
            initial=CONFIG.annotate_panel_zoom_in_window,
            inc=25,
            size=(90, -1),
        )
        self.zoom_window_size.Bind(wx.EVT_SPINCTRLDOUBLE, self.on_apply)

        grid = wx.GridBagSizer(2, 2)
        y = 0
        grid.Add(wx.StaticText(self, -1, "highlight:"), (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.highlight_on_selection, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        y += 1
        grid.Add(wx.StaticText(self, -1, "zoom-in:"), (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.zoom_on_selection, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)
        y += 1
        grid.Add(wx.StaticText(self, -1, "window size:"), (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.zoom_window_size, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(grid, 1, wx.EXPAND | wx.ALL, 5)
        self.set_info(sizer)

        self.SetSizerAndFit(sizer)
        self.Layout()

    def on_apply(self, evt):
        """Update settings"""
        CONFIG.annotate_panel_highlight = self.highlight_on_selection.GetValue()
        CONFIG.annotate_panel_zoom_in = self.zoom_on_selection.GetValue()
        CONFIG.annotate_panel_zoom_in_window = float(self.zoom_window_size.GetValue())

        if evt is not None:
            evt.Skip()

    def on_toggle(self, evt):
        """Update UI elements"""
        self.zoom_window_size.Enable(not CONFIG.annotate_panel_zoom_in)

        if evt is not None:
            evt.Skip()


class PanelAnnotationEditorUI(MiniFrame, TableMixin, DatasetMixin):
    """UI component of the Annotation Editor"""

    TABLE_DICT = {
        0: {
            "name": "",
            "tag": "check",
            "type": "bool",
            "width": 25,
            "show": True,
            "order": 0,
            "id": wx.NewIdRef(),
            "hidden": True,
        },
        1: {
            "name": "label",
            "tag": "label",
            "type": "str",
            "width": 200,
            "show": True,
            "order": 1,
            "id": wx.NewIdRef(),
        },
        2: {
            "name": "label color",
            "tag": "label_color",
            "type": "color",
            "width": 100,
            "show": True,
            "order": 2,
            "id": wx.NewIdRef(),
        },
        3: {
            "name": "arrow",
            "tag": "arrow_show",
            "type": "str",
            "width": 45,
            "show": True,
            "order": 3,
            "id": wx.NewIdRef(),
        },
        4: {
            "name": "patch",
            "tag": "patch_show",
            "type": "str",
            "width": 45,
            "show": True,
            "order": 4,
            "id": wx.NewIdRef(),
        },
        5: {
            "name": "patch color",
            "tag": "patch_color",
            "type": "color",
            "width": 100,
            "show": True,
            "order": 5,
            "id": wx.NewIdRef(),
        },
        6: {
            "name": "name",
            "tag": "name",
            "type": "str",
            "width": 0,
            "show": False,
            "order": 6,
            "id": wx.NewIdRef(),
            "hidden": True,
        },
    }
    TABLE_COLUMN_INDEX = TableColumnIndex
    TABLE_KWARGS = dict(color_0_to_1=True)
    PUB_SUBSCRIBE_MAKE_EVENT = "editor.mark.annotation"
    PUB_SUBSCRIBE_MOVE_LABEL_EVENT = "editor.edit.label"
    PUB_SUBSCRIBE_MOVE_PATCH_EVENT = "editor.edit.patch"
    USE_COLOR = False
    PANEL_BASE_TITLE = "Annotations"

    # pre-allocate ui controls
    peaklist = None
    name_value = None
    label_value = None
    marker_position_x = None
    marker_position_y = None
    label_position_x = None
    label_position_y = None
    label_color_btn = None
    add_arrow_to_peak = None
    patch_min_x = None
    patch_min_y = None
    patch_width = None
    patch_height = None
    patch_color_btn = None
    add_patch_to_peak = None
    auto_add_to_table = None

    # buttons
    info_btn = None
    add_btn = None
    remove_btn = None
    show_btn = None
    action_btn = None
    settings_btn = None

    # plot
    plot_view = None
    plot_panel = None
    plot_window = None

    # menu
    _menu_show_all_check = None
    _menu_pin_label_to_intensity_check = None
    _menu_autofix_label_position_check = None

    # misc
    _settings_panel_size = None
    main_sizer = None
    _plot_types_1d = ["mass_spectrum", "chromatogram", "mobilogram"]
    _plot_types_2d = ["heatmap", "ms_heatmap"]
    _plot_types_misc = ["annotated"]
    PLOT_TYPES = _plot_types_1d + _plot_types_2d + _plot_types_misc

    def __init__(self, parent, icons, plot_type):
        MiniFrame.__init__(self, parent, title="Annotations...", style=wx.DEFAULT_FRAME_STYLE & ~wx.MAXIMIZE_BOX)
        TableMixin.__init__(self)
        self.parent = parent
        self._icons = icons
        self.plot_type = plot_type

        # presets
        self._menu_show_all = True
        self._menu_pin_label_to_intensity = True
        self._menu_autofix_label_position = False
        self._auto_add_to_table = True
        self._allow_data_check = True if self.plot_type in self._plot_types_1d else False
        self.item_loading_lock = False

        # view
        screen_size = wx.GetDisplaySize()
        if parent is not None:
            screen_size = self.parent.GetSize()
        self._display_size = screen_size
        self._display_resolution = wx.ScreenDC().GetPPI()
        self._window_size = calculate_window_size(self._display_size, 0.9)

        # perform sanity check
        self.sanity_check()
        self.make_gui()

    def on_update_document(self, item_id: Optional[int] = None, item_info: Optional[Dict] = None):
        """Update document"""
        pass

    def on_menu_item_right_click(self, evt):
        """On right-click menu"""
        pass

    def sanity_check(self):
        """Perform self-check"""
        if self.plot_type not in self.PLOT_TYPES:
            raise ValueError(f"`{self.plot_type}` is not yet supported")

    def make_gui(self):
        """Make user-interface"""

        # make panel
        settings_panel = self.make_settings_panel(self)
        self._settings_panel_size = settings_panel.GetSize()

        plot_panel = self.make_plot_panel(self)

        # pack elements
        self.main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.main_sizer.Add(settings_panel, 0, wx.EXPAND, 0)
        self.main_sizer.Add(plot_panel, 1, wx.EXPAND, 0)

        # fit layout
        self.main_sizer.Fit(self)
        self.SetSizer(self.main_sizer)
        self.SetSize(self._window_size)
        self.Layout()
        self.Show(True)
        self.CentreOnScreen()
        self.SetFocus()

    def make_plot_panel(self, split_panel):
        """Make plot panel"""

        pixel_size = [(self._window_size[0] - self._settings_panel_size[0]), (self._window_size[1] - 50)]
        figsize = [pixel_size[0] / self._display_resolution[0], pixel_size[1] / self._display_resolution[1]]

        callbacks = dict(
            CTRL=self.PUB_SUBSCRIBE_MAKE_EVENT,
            MOVE_LABEL=self.PUB_SUBSCRIBE_MOVE_LABEL_EVENT,
            MOVE_PATCH=self.PUB_SUBSCRIBE_MOVE_PATCH_EVENT,
        )

        if self.plot_type in self._plot_types_1d:
            if self.plot_type == "mass_spectrum":
                self.plot_view = ViewMassSpectrum(split_panel, figsize, callbacks=callbacks, allow_extraction=True)
            elif self.plot_type == "chromatogram":
                self.plot_view = ViewChromatogram(split_panel, figsize, callbacks=callbacks, allow_extraction=True)
            elif self.plot_type == "mobilogram":
                self.plot_view = ViewMobilogram(split_panel, figsize, callbacks=callbacks, allow_extraction=True)

            self.plot_panel = self.plot_view.panel
            self.plot_window = self.plot_view.figure
        elif self.plot_type in self._plot_types_2d:
            if self.plot_type == "heatmap":
                self.plot_view = ViewIonHeatmap(split_panel, figsize, callbacks=callbacks, allow_extraction=True)
            elif self.plot_type == "ms_heatmap":
                self.plot_view = ViewMassSpectrumHeatmap(
                    split_panel, figsize, callbacks=callbacks, allow_extraction=True
                )

            self.plot_panel = self.plot_view.panel
            self.plot_window = self.plot_view.figure

        return self.plot_view.panel

    # noinspection DuplicatedCode
    def make_settings_panel(self, split_panel):
        """Make settings panel"""
        panel = wxScrolledPanel.ScrolledPanel(split_panel, -1, size=(-1, -1), name="main")

        # statusbar
        statusbar = self.make_statusbar(panel)

        # make peaklist
        self.peaklist = self.make_table(self.TABLE_DICT, panel)

        self.name_value = wx.TextCtrl(panel, -1, "", style=wx.TE_RICH2)

        self.label_value = wx.TextCtrl(panel, -1, "", style=wx.TE_RICH2 | wx.TE_MULTILINE)
        self.label_value.SetToolTip(wx.ToolTip("Label associated with the marked region in the plot area"))

        self.marker_position_x = wx.TextCtrl(panel, -1, "", validator=Validator("float"))
        self.marker_position_x.SetBackgroundColour((255, 230, 239))

        self.marker_position_y = wx.TextCtrl(panel, -1, "", validator=Validator("float"))
        self.marker_position_y.SetBackgroundColour((255, 230, 239))

        self.label_position_x = wx.TextCtrl(panel, -1, "", validator=Validator("float"))
        self.label_position_x.SetBackgroundColour((255, 230, 239))

        self.label_position_y = wx.TextCtrl(panel, -1, "", validator=Validator("float"))
        self.label_position_y.SetBackgroundColour((255, 230, 239))

        self.label_color_btn = wx.Button(panel, wx.ID_ANY, "", size=wx.Size(26, 26), name="label_color")
        self.label_color_btn.SetBackgroundColour([0, 0, 0])

        self.add_arrow_to_peak = make_checkbox(panel, "", name="arrow_show")
        self.add_arrow_to_peak.SetValue(False)

        self.patch_min_x = wx.TextCtrl(panel, -1, "", validator=Validator("float"))
        self.patch_min_x.SetBackgroundColour((255, 230, 239))
        self.patch_min_y = wx.TextCtrl(panel, -1, "", validator=Validator("float"))
        self.patch_min_y.SetBackgroundColour((255, 230, 239))
        self.patch_width = wx.TextCtrl(panel, -1, "", validator=Validator("float"))
        self.patch_height = wx.TextCtrl(panel, -1, "", validator=Validator("float"))

        self.patch_color_btn = wx.Button(panel, wx.ID_ANY, "", size=wx.Size(26, 26), name="patch_color")
        self.patch_color_btn.SetBackgroundColour(convert_rgb_1_to_255(CONFIG.interactive_ms_annotations_color))

        self.add_patch_to_peak = make_checkbox(panel, "", name="patch_show")
        self.add_patch_to_peak.SetValue(False)

        # make buttons
        self.add_btn = wx.Button(panel, wx.ID_OK, "Add", size=(-1, -1))
        self.remove_btn = wx.Button(panel, wx.ID_OK, "Remove", size=(-1, -1))
        self.show_btn = wx.Button(panel, wx.ID_OK, "Show ▼", size=(-1, -1))
        self.action_btn = wx.Button(panel, wx.ID_OK, "Action ▼", size=(-1, -1))
        self.settings_btn = make_bitmap_btn(
            panel,
            wx.ID_ANY,
            self._icons.settings_gear,
            tooltip="Show few additional setting options",
            style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL,
        )
        self.settings_btn.Bind(wx.EVT_BUTTON, self.on_popup)

        self.auto_add_to_table = make_checkbox(
            panel,
            "auto-add",
            tooltip="When checked, regions-of-interest highlighted in the plot area will be automatically added to the"
            " table.",
        )
        self.auto_add_to_table.SetValue(self._auto_add_to_table)

        # button grid
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.Add(self.add_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        btn_sizer.Add(self.remove_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        btn_sizer.Add(self.show_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        btn_sizer.Add(self.action_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        btn_sizer.Add(self.settings_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        btn_sizer.Add(self.auto_add_to_table, 0, wx.ALIGN_CENTER_VERTICAL)

        # pack elements
        grid = wx.GridBagSizer(5, 5)
        y = 0
        grid.Add(wx.StaticText(panel, -1, "name:"), (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.name_value, (y, 1), wx.GBSpan(1, 5), flag=wx.EXPAND)
        y += 1
        grid.Add(wx.StaticText(panel, -1, "label:"), (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.label_value, (y, 1), wx.GBSpan(4, 5), flag=wx.EXPAND)
        y += 4
        grid.Add(wx.StaticText(panel, -1, "x"), (y, 1), flag=wx.ALIGN_CENTER)
        grid.Add(wx.StaticText(panel, -1, "y"), (y, 2), flag=wx.ALIGN_CENTER)
        y += 1
        grid.Add(wx.StaticText(panel, -1, "marker position:"), (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.marker_position_x, (y, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.marker_position_y, (y, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        y += 1
        grid.Add(wx.StaticText(panel, -1, "label position:"), (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.label_position_x, (y, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.label_position_y, (y, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        y += 1
        grid.Add(wx.StaticText(panel, -1, "label color:"), (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.label_color_btn, (y, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        y += 1
        grid.Add(wx.StaticText(panel, -1, "show arrow:"), (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.add_arrow_to_peak, (y, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        y += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (y, 0), wx.GBSpan(1, 6), flag=wx.EXPAND)
        y += 1
        grid.Add(wx.StaticText(panel, -1, "position (x)"), (y, 1), flag=wx.ALIGN_CENTER)
        grid.Add(wx.StaticText(panel, -1, "position (y)"), (y, 2), flag=wx.ALIGN_CENTER)
        grid.Add(wx.StaticText(panel, -1, "width"), (y, 3), flag=wx.ALIGN_CENTER)
        grid.Add(wx.StaticText(panel, -1, "height"), (y, 4), flag=wx.ALIGN_CENTER)
        y += 1
        grid.Add(wx.StaticText(panel, -1, "patch:"), (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.patch_min_x, (y, 1), flag=wx.ALIGN_CENTER)
        grid.Add(self.patch_min_y, (y, 2), flag=wx.ALIGN_CENTER)
        grid.Add(self.patch_width, (y, 3), flag=wx.ALIGN_CENTER)
        grid.Add(self.patch_height, (y, 4), flag=wx.ALIGN_CENTER)
        y += 1
        grid.Add(wx.StaticText(panel, -1, "patch color:"), (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.patch_color_btn, (y, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        y += 1
        grid.Add(wx.StaticText(panel, -1, "show patch:"), (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.add_patch_to_peak, (y, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        y += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (y, 0), wx.GBSpan(1, 6), flag=wx.EXPAND)
        y += 1
        grid.Add(btn_sizer, (y, 0), wx.GBSpan(1, 6), flag=wx.ALIGN_CENTER)
        grid.AddGrowableCol(5, 1)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(self.peaklist, 1, wx.EXPAND, 2)
        main_sizer.Add(statusbar, 0, wx.EXPAND, 5)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)
        panel.SetupScrolling(scroll_x=False, scroll_y=True)

        return panel

    def on_double_click_on_item(self, _):
        """Double-click on item event"""
        if self.peaklist.item_id not in [-1, None]:
            check = not self.peaklist.IsChecked(self.peaklist.item_id)
            self.peaklist.CheckItem(self.peaklist.item_id, check)

    def on_popup(self, evt):
        """Show popup window"""

        popup = PopupAnnotationSettings(self)
        popup.position_on_event(evt)
        popup.Show()


class PanelAnnotationEditor(PanelAnnotationEditorUI):
    """Simple GUI to view and annotate plots"""

    _data_obj = None
    _annotations = None

    def __init__(self, parent, presenter, icons, **kwargs):
        PanelAnnotationEditorUI.__init__(self, parent, icons, kwargs["plot_type"])
        self.presenter = presenter

        # data
        self.document_title = kwargs["document_title"]
        self.dataset_name = kwargs["dataset_name"]
        self.data_obj = kwargs.pop("data_obj")
        self.annotations = self.data_obj.get_annotations()
        self.kwargs = kwargs

        # hard code few parameters
        CONFIG.annotation_patch_transparency = 0.2
        CONFIG.annotation_patch_width = 3

        # initialize correct view
        self.setup()

        # setup
        wx.CallAfter(self.on_setup_plot_on_startup)

    @property
    def data_obj(self) -> DataObject:
        """Return `DataObject`"""
        return self._data_obj

    @data_obj.setter
    def data_obj(self, value: DataObject):
        """Set `mz_obj_cache`"""
        assert isinstance(value, DataObject), "Incorrect data-type was being set to the `data_obj` attribute"
        self._data_obj = value

    @property
    def annotations(self):
        """Return annotations object"""
        return self._annotations

    @annotations.setter
    def annotations(self, value: Annotations):
        """Set `mz_obj_cache`"""
        assert isinstance(value, Annotations), "Incorrect data-type was being set to the `annotations` attribute"
        self._annotations = value

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

    def setup(self):
        """Setup UI"""
        self.update_title()
        self.on_populate_table()
        self.on_toggle_controls(None)
        self.bind_events()
        self._dataset_mixin_setup()

    # noinspection DuplicatedCode
    def bind_events(self):
        """Bind events"""

        # add listeners
        pub.subscribe(self.add_annotation_from_mouse_evt, self.PUB_SUBSCRIBE_MAKE_EVENT)
        pub.subscribe(self.edit_label_from_mouse_evt, self.PUB_SUBSCRIBE_MOVE_LABEL_EVENT)
        pub.subscribe(self.edit_patch_from_mouse_evt, self.PUB_SUBSCRIBE_MOVE_PATCH_EVENT)

        # bind buttons
        self.patch_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color_button)
        self.label_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color_button)
        self.add_btn.Bind(wx.EVT_BUTTON, self.on_add_annotation)
        self.remove_btn.Bind(wx.EVT_BUTTON, self.on_delete_annotation)
        self.show_btn.Bind(wx.EVT_BUTTON, self.on_menu_plot_tools)
        self.action_btn.Bind(wx.EVT_BUTTON, self.on_menu_action_tools)

        # bind checkboxes
        self.auto_add_to_table.Bind(wx.EVT_CHECKBOX, self.on_apply)
        self.add_patch_to_peak.Bind(wx.EVT_CHECKBOX, self.on_update_annotation)
        self.add_arrow_to_peak.Bind(wx.EVT_CHECKBOX, self.on_update_annotation)

        # bind table
        self.peaklist.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_select_item)
        self.peaklist.Bind(wx.EVT_LEFT_DCLICK, self.on_double_click_on_item)

        # window events
        self.Bind(wx.EVT_CONTEXT_MENU, self.on_right_click)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_event)
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def _check_active(self, query):
        """Check whether the currently open editor should be closed"""
        return all([self.document_title == query[0], self.dataset_name == query[2]])

    # noinspection DuplicatedCode
    def on_right_click(self, evt):
        """On right-click menu event"""
        menu = wx.Menu()
        # ensure that user clicked inside the plot area
        if hasattr(evt.EventObject, "figure"):
            save_figure_menu_item = make_menu_item(
                menu, evt_id=wx.ID_ANY, text="Save figure as...", bitmap=self._icons.save
            )
            menu.AppendItem(save_figure_menu_item)

            menu_action_copy_to_clipboard = make_menu_item(
                parent=menu, evt_id=wx.ID_ANY, text="Copy plot to clipboard", bitmap=self._icons.filelist
            )
            menu.AppendItem(menu_action_copy_to_clipboard)
            menu.AppendSeparator()
            menu_plot_clear_labels = make_menu_item(parent=menu, text="Clear annotations", bitmap=self._icons.clear)
            menu.Append(menu_plot_clear_labels)

            # bind events
            self.Bind(wx.EVT_MENU, self.on_save_figure, save_figure_menu_item)
            self.Bind(wx.EVT_MENU, self.on_copy_to_clipboard, menu_action_copy_to_clipboard)
            self.Bind(wx.EVT_MENU, self.on_clear_from_plot, menu_plot_clear_labels)
        else:
            menu_delete_annotation = make_menu_item(parent=menu, text="Delete annotation", bitmap=self._icons.bin)
            menu.Append(menu_delete_annotation)
            self.Bind(wx.EVT_MENU, self.on_delete_item, menu_delete_annotation)

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def update_title(self):
        """Update widget title"""
        self.SetTitle(f"Annotating: {self.document_title} :: {self.dataset_name}")

    def on_key_event(self, evt):
        """Handle keyboard events"""
        key_code = evt.GetKeyCode()

        if key_code == wx.WXK_ESCAPE:
            self.on_close(None)
        elif key_code == 127 and self.FindFocus() == self.peaklist:
            self.on_delete_annotation(evt)
        else:
            evt.Skip()

    def on_close(self, _, force: bool = False):
        """Destroy this frame."""
        # unsubscribe
        try:
            pub.unsubscribe(self.add_annotation_from_mouse_evt, self.PUB_SUBSCRIBE_MAKE_EVENT)
            pub.unsubscribe(self.edit_label_from_mouse_evt, self.PUB_SUBSCRIBE_MOVE_LABEL_EVENT)
            pub.unsubscribe(self.edit_patch_from_mouse_evt, self.PUB_SUBSCRIBE_MOVE_PATCH_EVENT)
        except Exception as err:
            logger.error("Failed to unsubscribe events: %s" % err)

        self._dataset_mixin_teardown()

        self.document_tree._annotate_panel = None
        self.Destroy()

    def on_apply(self, _):
        """Update config"""
        CONFIG.annotate_panel_add_to_table = self.auto_add_to_table.GetValue()

    def on_toggle_controls(self, evt):
        """Toggle various items in the UI based on event triggers"""
        self.name_value.Disable()

        if not CONFIG.annotate_panel_highlight:
            self.plot_window.plot_remove_temporary(True)

        if evt is not None:
            evt.Skip()

    # noinspection DuplicatedCode
    def on_menu_action_tools(self, _):
        """Create action menu"""
        menu = wx.Menu()

        menu_action_customise = make_menu_item(
            parent=menu, text="Customise other settings...", bitmap=self._icons.settings_gear, help_text=""
        )
        menu.Append(menu_action_customise)
        menu.AppendSeparator()

        menu_action_multiply = make_menu_item(
            parent=menu, text="Create copies of selected annotations", bitmap=self._icons.duplicate
        )
        menu.Append(menu_action_multiply)
        menu.AppendSeparator()

        if self._allow_data_check:
            menu_action_fix_label_intensity = make_menu_item(
                parent=menu, text="Fix intensity / label position (selected)"
            )
            menu.Append(menu_action_fix_label_intensity)

            menu_action_fix_patch_height = make_menu_item(
                parent=menu,
                text="Fix patch height (selected)",
                help_text="Pins the height of a patch to the maximum intensity at a particular position (x)",
            )
            menu.Append(menu_action_fix_patch_height)
            menu.AppendSeparator()

            self.Bind(wx.EVT_MENU, self.on_fix_intensity, menu_action_fix_label_intensity)
            self.Bind(wx.EVT_MENU, self.on_fix_patch_height, menu_action_fix_patch_height)

        menu_action_edit_text_color = make_menu_item(parent=menu, text="Set label color (selected)")
        menu.Append(menu_action_edit_text_color)

        menu_action_edit_patch_color = make_menu_item(parent=menu, text="Set patch color (selected)")
        menu.Append(menu_action_edit_patch_color)

        arrow_submenu = wx.Menu()
        menu_action_edit_arrow_true = arrow_submenu.Append(wx.ID_ANY, "True")
        menu_action_edit_arrow_false = arrow_submenu.Append(wx.ID_ANY, "False")
        menu.AppendMenu(wx.ID_ANY, "Set `show arrow` to... (selected)", arrow_submenu)

        patch_submenu = wx.Menu()
        menu_action_edit_patch_true = patch_submenu.Append(wx.ID_ANY, "True")
        menu_action_edit_patch_false = patch_submenu.Append(wx.ID_ANY, "False")
        menu.AppendMenu(wx.ID_ANY, "Set `show patch` to... (selected)", patch_submenu)

        menu_action_delete = make_menu_item(parent=menu, text="Delete (selected)", bitmap=self._icons.delete)
        menu.AppendSeparator()
        menu.Append(menu_action_delete)

        # bind events
        self.Bind(wx.EVT_MENU, self.on_customise_parameters, menu_action_customise)
        self.Bind(wx.EVT_MENU, self.on_copy_annotations, menu_action_multiply)
        self.Bind(wx.EVT_MENU, self.on_assign_color, menu_action_edit_text_color)
        self.Bind(wx.EVT_MENU, self.on_assign_color, menu_action_edit_patch_color)
        self.Bind(wx.EVT_MENU, self.on_assign_arrow, menu_action_edit_arrow_true)
        self.Bind(wx.EVT_MENU, self.on_assign_arrow, menu_action_edit_arrow_false)
        self.Bind(wx.EVT_MENU, self.on_assign_patch, menu_action_edit_patch_true)
        self.Bind(wx.EVT_MENU, self.on_assign_patch, menu_action_edit_patch_false)
        self.Bind(wx.EVT_MENU, self.on_delete_items, menu_action_delete)

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def on_menu_plot_tools(self, _):
        """Make plot tools menu"""
        menu = wx.Menu()
        self._menu_show_all_check = menu.AppendCheckItem(
            wx.ID_ANY,
            "Always show all annotation(s)",
            help="If checked, all annotations will be shown regardless of their checked status in the table",
        )
        self._menu_show_all_check.Check(self._menu_show_all)

        self._menu_pin_label_to_intensity_check = menu.AppendCheckItem(
            wx.ID_ANY, "Show labels at intensity value", help="If checked, labels will 'stick' to the intensity values"
        )
        self._menu_pin_label_to_intensity_check.Check(self._menu_pin_label_to_intensity)

        self._menu_autofix_label_position_check = menu.AppendCheckItem(
            wx.ID_ANY,
            "Auto-adjust positions to prevent overlap",
            help="If checked, labels will be repositioned to prevent overlap.",
        )
        self._menu_autofix_label_position_check.Check(self._menu_autofix_label_position)
        menu.AppendSeparator()
        menu_plot_show_labels = make_menu_item(parent=menu, text="Show annotations", bitmap=self._icons.label)
        menu.Append(menu_plot_show_labels)
        menu_plot_clear_labels = make_menu_item(parent=menu, text="Clear annotations", bitmap=self._icons.clear)
        menu.Append(menu_plot_clear_labels)

        # bind events
        self.Bind(wx.EVT_MENU, self.on_clear_from_plot, menu_plot_clear_labels)
        self.Bind(wx.EVT_MENU, self.on_plot_annotations, menu_plot_show_labels)
        self.Bind(wx.EVT_TOOL, self.on_check_tools, self._menu_show_all_check)
        self.Bind(wx.EVT_TOOL, self.on_check_tools, self._menu_pin_label_to_intensity_check)
        self.Bind(wx.EVT_TOOL, self.on_check_tools, self._menu_autofix_label_position_check)

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def on_check_tools(self, evt):
        """ Check/uncheck menu item """
        name = evt.GetEventObject().FindItemById(evt.GetId()).GetItemLabel()

        # check which event was triggered
        if "at intensity value" in name:
            check_value = not self._menu_pin_label_to_intensity
            self._menu_pin_label_to_intensity = check_value
        elif "Auto-adjust" in name:
            check_value = not self._menu_autofix_label_position
            self._menu_autofix_label_position = check_value
        elif "Always " in name:
            check_value = not self._menu_show_all
            self._menu_show_all = check_value

    def on_assign_color(self, evt):  # noqa
        """Change value of `color` for each selected annotation"""
        value = evt.GetEventObject().FindItemById(evt.GetId()).GetItemLabel()
        value = "label_color" if "label color" in value else "patch_color"

        checked = self.get_checked_items()
        if not checked:
            raise MessageError("Error", "Please check at least one annotation in the table")

        _, color_1, _ = self.on_get_color(None)

        changed = False
        for item_id in checked:
            name = self.on_get_item_information(item_id)["name"]
            annotation_obj = self.annotations.get(name)
            if annotation_obj is None:
                continue
            #             if annotation_obj.arrow_show == value:
            #                 continue

            if value == "label_color":
                annotation_obj.label_color = color_1
                self.annotations.add(annotation_obj.name, annotation_obj)
                self.on_change_item_value(item_id, self.TABLE_COLUMN_INDEX.label_color, str(round_rgb(color_1)))
            elif value == "patch_color":
                annotation_obj.patch_color = color_1
                self.annotations.add(annotation_obj.name, annotation_obj)
                self.on_change_item_value(item_id, self.TABLE_COLUMN_INDEX.patch_color, str(round_rgb(color_1)))
            changed = True

        if changed:
            self.data_obj.set_annotations(self.annotations)
            self.on_plot_annotations()

    # noinspection DuplicatedCode
    def on_assign_arrow(self, evt):
        """Change value of `arrow_show` for each selected annotation"""
        value = evt.GetEventObject().FindItemById(evt.GetId()).GetItemLabel()
        value = True if value == "True" else False

        checked = self.get_checked_items()
        if not checked:
            raise MessageError("Error", "Please check at least one annotation in the table")

        changed = False
        for item_id in checked:
            name = self.on_get_item_information(item_id)["name"]
            annotation_obj = self.annotations.get(name)
            if annotation_obj is None:
                continue
            if annotation_obj.arrow_show == value:
                continue

            annotation_obj.arrow_show = value
            self.annotations.add(annotation_obj.name, annotation_obj)
            self.on_change_item_value(item_id, self.TABLE_COLUMN_INDEX.arrow, str(value))
            changed = True

        if changed:
            self.data_obj.set_annotations(self.annotations)
            self.on_plot_annotations()

    # noinspection DuplicatedCode
    def on_assign_patch(self, evt):
        """Change value of `patch_show` for each selected annotation"""
        value = evt.GetEventObject().FindItemById(evt.GetId()).GetItemLabel()
        value = True if value == "True" else False

        checked = self.get_checked_items()
        if not checked:
            raise MessageError("Error", "Please check at least one annotation in the table")

        changed = False
        for item_id in checked:
            name = self.on_get_item_information(item_id)["name"]
            annotation_obj = self.annotations.get(name)
            if annotation_obj is None:
                continue
            if annotation_obj.patch_show == value:
                continue

            annotation_obj.patch_show = value
            self.annotations.add(annotation_obj.name, annotation_obj)
            self.on_change_item_value(item_id, self.TABLE_COLUMN_INDEX.patch, str(value))
            changed = True

        if changed:
            self.data_obj.set_annotations(self.annotations)
            self.on_plot_annotations()

    def on_fix_intensity(self, _, fix_type: str = "label"):
        """Fix intensity for 1d label"""
        if not self._allow_data_check:
            return

        checked = self.get_checked_items()
        if not checked:
            raise MessageError("Error", "Please check at least one annotation in the table")

        changed = False
        for item_id in checked:
            name = self.on_get_item_information(item_id)["name"]
            annotation_obj = self.annotations.get(name)
            if annotation_obj is None:
                continue

            x_min = annotation_obj.span_x_min
            x_max = annotation_obj.span_x_max

            try:
                y_max = self.data_obj.get_intensity_at_loc(x_min, x_max)  # noqa
            except ValueError:
                logger.warning("Could not get intensity at the position")
                continue

            if fix_type == "label":
                annotation_obj.label_position_y = y_max
            elif fix_type == "patch":
                annotation_obj.height = y_max
            self.annotations.add(annotation_obj.name, annotation_obj)
            changed = True

        if changed:
            self.data_obj.set_annotations(self.annotations)
            self.on_plot_annotations()

    def on_fix_patch_height(self, _):
        """Fx intensity for 1d patch"""
        self.on_fix_intensity(None, "patch")

    def on_delete_items(self, _):
        """Delete selected items from the table and the DocumentStore"""
        checked = self.get_checked_items()
        if not checked:
            raise MessageError("Error", "Please check at least one annotation in the table")

        dlg = DialogBox(
            title="Are you sure?",
            msg=f"Are you sure you want to delete `{len(checked)} annotations?\nThis action is not reversible",
            kind="Question",
        )
        if dlg == wx.ID_NO:
            return

        for item_id in reversed(checked):
            name = self.on_get_item_information(item_id)["name"]
            self.on_delete_annotation(None, name, flush=False)

        # update annotations in the object
        self.on_plot_annotations()
        self.data_obj.set_annotations(self.annotations)

    def on_delete_item(self, _evt):
        """Delete item from the table and document"""
        item_information = self.on_get_item_information(self.peaklist.item_id)
        self.on_delete_annotation(None, item_information["name"], flush=True)

    def on_assign_color_button(self, evt):
        """Assign new color to the element"""
        name = evt.GetEventObject().GetName()

        color_255, color_1, _ = self.on_get_color(None)
        if name == "patch_color":
            self.patch_color_btn.SetBackgroundColour(color_255)
        elif name == "label_color":
            self.label_color_btn.SetBackgroundColour(color_255)

        self.on_update_annotation(None, name, color_1)

    def on_select_item(self, evt, name: str = None):
        """Select-item and set its values in the GUI"""

        if name is None:
            self.peaklist.item_id = evt.GetIndex()
            info = self.on_get_item_information()
            name = info["name"]

        annotation_obj = self.annotations.get(name)
        self.set_annotation_in_gui(annotation_obj)

        if CONFIG.annotate_panel_highlight:
            x_min = annotation_obj.span_x_min - CONFIG.annotate_panel_zoom_in_window
            x_max = annotation_obj.span_x_max + CONFIG.annotate_panel_zoom_in_window
            y_min = annotation_obj.span_y_min
            y_max = annotation_obj.span_y_max * 1.2

            self.plot_view.set_xylim(x_min, x_max, y_min, y_max)

    def on_populate_table(self):
        """Populate table with current annotations"""
        annotations_obj = self.annotations

        for annotation_obj in annotations_obj.values():
            self.on_add_to_table(annotation_obj.to_dict())

    def clear_gui(self):
        """Clear all fields in the user interface"""
        self.name_value.SetValue("")
        self.label_value.SetValue("")
        self.label_position_x.SetValue("")
        self.label_position_y.SetValue("")
        self.patch_min_x.SetValue("")
        self.patch_min_y.SetValue("")
        self.patch_width.SetValue("")
        self.patch_height.SetValue("")
        self.marker_position_x.SetValue("")
        self.marker_position_y.SetValue("")

    def set_annotation_in_gui(self, annotation_obj: Annotation):
        """Set annotation in GUI before it is set in the document"""
        if not isinstance(annotation_obj, Annotation):
            raise ValueError("Incorrect data object")

        # set values in GUI
        self.name_value.SetValue(annotation_obj.name)
        self.label_value.SetValue(annotation_obj.label)
        self.label_position_x.SetValue(rounder(annotation_obj.label_position_x, 4))
        self.label_position_y.SetValue(rounder(annotation_obj.label_position_y, 4))
        self.add_arrow_to_peak.SetValue(annotation_obj.arrow_show)
        self.add_patch_to_peak.SetValue(annotation_obj.patch_show)
        self.patch_color_btn.SetBackgroundColour(convert_rgb_1_to_255(annotation_obj.patch_color))
        self.label_color_btn.SetBackgroundColour(convert_rgb_1_to_255(annotation_obj.label_color))
        self.patch_min_x.SetValue(rounder(annotation_obj.patch_position[0], 4))
        self.patch_min_y.SetValue(rounder(annotation_obj.patch_position[1], 4))
        self.patch_width.SetValue(rounder(annotation_obj.patch_position[2], 4))
        self.patch_height.SetValue(rounder(annotation_obj.patch_position[3], 4))
        self.marker_position_x.SetValue(rounder(annotation_obj.marker_position_x, 4))
        self.marker_position_y.SetValue(rounder(annotation_obj.marker_position_y, 4))

    def get_annotation_obj_from_data(self, x_min, x_max, y_min, y_max):
        """Pre-calculate parameters based on the data"""
        # make sure values are in the correct order
        x_min, x_max = check_value_order(x_min, x_max)
        y_min, y_max = check_value_order(y_min, y_max)

        name = get_short_hash()
        y_position = y_max
        x_position = x_max - ((x_max - x_min) / 2)

        # check if the annotation is a point annotation
        if np.abs(np.diff([x_min, x_max])) < 0.05:
            x_min = x_min - 0.1
            x_max = x_max + 0.1

        if self._allow_data_check:
            try:
                y_max = self.data_obj.get_intensity_at_loc(x_min, x_max)  # noqa
            except ValueError:
                logger.warning("Could not get intensity at the position")
            y_position = y_max * 1.05

        label = f"x={x_position:.4f}\ny={y_position:.2f}"
        width = x_max - x_min
        height = y_max - y_min

        # height in 1d plots can be pinned to the maximum value in a specified region
        if self.plot_type in self._plot_types_1d:
            height = y_max
            y_min = 0

        return dict(
            name=name,
            label=label,
            label_show=True,
            label_position=(x_position, y_position),
            marker_position=(x_position, y_position),
            label_color=CONFIG.annotate_panel_label_color,
            patch_position=(x_min, y_min, width, height),
            patch_color=CONFIG.annotate_panel_patch_color,
            patch_show=True if self.plot_type == "heatmap" else False,
            patch_alpha=CONFIG.annotate_panel_patch_alpha,
            arrow_show=True,
        )

    def add_annotation_from_mouse_evt(self, rect, x_labels, y_labels):  # noqa
        """Add annotations from mouse event"""
        xmin, xmax, ymin, ymax = rect
        del x_labels, y_labels

        # calculate some presets
        info_dict = self.get_annotation_obj_from_data(xmin, xmax, ymin, ymax)
        annotation_obj = Annotation(**info_dict)

        self.set_annotation_in_gui(annotation_obj)
        if self._auto_add_to_table:
            self.on_add_annotation(None, annotation_obj)
        self.add_btn.SetFocus()

    def edit_label_from_mouse_evt(self, label_obj):
        """Edit position of the arrow object"""
        name = label_obj.obj_name
        x, y = label_obj.get_position()
        annotation_obj = self.annotations.get(name)
        annotation_obj.label_position = (x, y)
        self.annotations.add(annotation_obj.name, annotation_obj)
        self.data_obj.set_annotations(self.annotations)
        self.set_annotation_in_gui(annotation_obj)

        if annotation_obj.arrow_show:
            self.on_annotate_spectrum_with_arrows(None)

    def edit_patch_from_mouse_evt(self, patch_obj):
        """Edit position of the patch object"""
        name = patch_obj.obj_name
        x_min, y_min = patch_obj.get_xy()
        annotation_obj = self.annotations.get(name)
        _, _, width, height = annotation_obj.patch_position
        annotation_obj.patch_position = (x_min, y_min, width, height)
        self.annotations.add(annotation_obj.name, annotation_obj)
        self.data_obj.set_annotations(self.annotations)
        self.set_annotation_in_gui(annotation_obj)

    def get_annotation_obj_from_gui(self):
        """Return annotation object from the data currently set in the user interface"""
        name = self.name_value.GetValue()
        annotation_obj = self.annotations.get(name)

        data = dict(
            name=name,
            label=self.label_value.GetValue(),
            label_show=True,
            label_position=(str2num(self.label_position_x.GetValue()), str2num(self.label_position_y.GetValue())),
            marker_position=(str2num(self.marker_position_x.GetValue()), str2num(self.marker_position_y.GetValue())),
            label_color=convert_rgb_255_to_1(self.label_color_btn.GetBackgroundColour()),
            patch_position=(
                str2num(self.patch_min_x.GetValue()),
                str2num(self.patch_min_y.GetValue()),
                str2num(self.patch_width.GetValue()),
                str2num(self.patch_height.GetValue()),
            ),
            patch_color=convert_rgb_255_to_1(self.patch_color_btn.GetBackgroundColour()),
            patch_show=self.add_patch_to_peak.GetValue(),
            patch_alpha=CONFIG.annotate_panel_patch_alpha,
            arrow_show=self.add_arrow_to_peak.GetValue(),
        )

        if annotation_obj is None:
            annotation_obj = Annotation(**data)
        else:
            annotation_obj.update(**data)

        return annotation_obj

    def on_add_annotation(self, _, annotation_obj=None):
        """Set annotation in the table and display it in the plot"""
        t_start = time.time()
        if self.item_loading_lock:
            return

        item_id = -1
        if annotation_obj is None:
            annotation_obj = self.get_annotation_obj_from_gui()
            item_id = self.on_find_item("name", annotation_obj.name)

        if item_id == -1:
            self.on_add_to_table(annotation_obj.to_dict())
        else:
            self.on_update_annotation_in_table(item_id, annotation_obj)
        self.annotations.add(annotation_obj.name, annotation_obj)
        self.data_obj.set_annotations(self.annotations)
        self.on_plot_annotations()
        logger.debug(f"Set annotations in {report_time(t_start)}")

    def on_update_annotation(self, evt, obj_name: str = None, obj_value=None):
        """Update annotation in the DocumentStore"""
        if obj_name is None and obj_value is None:
            obj = evt.GetEventObject()
            obj_name = obj.GetName()
            obj_value = obj.GetValue()

        if obj_name == "":
            return

        name = self.name_value.GetValue()
        item_id = self.on_find_item("name", name)
        if item_id == -1:
            return

        annotation_obj = self.annotations.get(name)
        if annotation_obj is None:
            return

        print(obj_name)
        if obj_name == "patch_show":
            annotation_obj.patch_show = obj_value
        elif obj_name == "arrow_show":
            annotation_obj.patch_show = obj_value
        elif obj_name == "label_color":
            annotation_obj.label_color = obj_value
        elif obj_name == "patch_color":
            annotation_obj.patch_color = obj_value

        self.on_update_annotation_in_table(item_id, annotation_obj)
        self.annotations.add(annotation_obj.name, annotation_obj)
        self.data_obj.set_annotations(self.annotations)
        self.on_plot_annotations()

    def on_update_annotation_in_table(self, item_id: int, annotation_obj: Annotation):
        """Update annotation values in the table"""
        self.on_change_item_value(item_id, self.TABLE_COLUMN_INDEX.label, str(annotation_obj.label))
        self.on_change_item_value(item_id, self.TABLE_COLUMN_INDEX.arrow, str(annotation_obj.arrow_show))
        self.on_change_item_value(item_id, self.TABLE_COLUMN_INDEX.patch, str(annotation_obj.patch_show))
        self.on_change_item_value(
            item_id, self.TABLE_COLUMN_INDEX.label_color, str(round_rgb(annotation_obj.label_color))
        )
        self.on_change_item_value(
            item_id, self.TABLE_COLUMN_INDEX.patch_color, str(round_rgb(annotation_obj.patch_color))
        )

    def on_delete_annotation(self, _evt, name=None, flush: bool = True, get_next: bool = False):
        """Remove annotation"""
        if name is None:
            name = self.name_value.GetValue()

        item_id = self.on_find_item("name", name)
        if item_id != -1:
            self.annotations.pop(name)
            self.peaklist.DeleteItem(item_id)

            if get_next:
                next_id = self._get_next_id(item_id)
                if next_id >= 0:
                    self.peaklist.Select(next_id)
                else:
                    self.clear_gui()

        if flush:
            self.on_plot_annotations()
            self.data_obj.set_annotations(self.annotations)

    def _get_next_id(self, current_id: int):
        """Get next id that can be used to setup another item"""
        n_rows = self.n_rows
        if n_rows == 0:
            return -1
        if n_rows == 1:
            return 0
        if current_id < n_rows:
            return current_id
        return current_id - 1

    def on_copy_annotations(self, _):
        """Copy annotations by duplicating existing annotations and giving them new name - this allows for quick
        creation of many instances of annotations"""
        from copy import deepcopy
        from origami.gui_elements.misc_dialogs import DialogNumberAsk

        checked = self.get_checked_items()
        if not checked:
            raise MessageError("Error", "Please check at least one annotation in the table")

        n_duplicates = DialogNumberAsk("How many times would you like to duplicate this annotations?", value=1)
        n_duplicates = int(n_duplicates)
        for item_id in checked:
            for _ in range(n_duplicates):
                name = self.on_get_item_information(item_id)["name"]
                annotation = self.annotations.get(name)
                if annotation is None:
                    continue
                annotation_copy = deepcopy(annotation)
                annotation_copy.name = get_short_hash()
                self.annotations.add(annotation_copy.name, annotation_copy)
                self.on_add_to_table(annotation_copy.to_dict())
        self.data_obj.set_annotations(self.annotations)

    # def on_save_peaklist(self, _):
    #     from pandas import DataFrame
    #
    #     peaklist = []
    #     for key in self.kwargs["annotations"]:
    #         annotation = self.kwargs["annotations"][key]
    #         intensity = str2num(annotation["intensity"])
    #         charge = annotation["charge"]
    #         label = annotation["label"]
    #         min_value = annotation["min"]
    #         max_value = annotation["max"]
    #         isotopic_x = annotation.get("isotopic_x", "")
    #         peaklist.append([min_value, max_value, isotopic_x, intensity, charge, label])
    #
    #     # make dataframe
    #     columns = ["min", "max", "position", "intensity", "charge", "label"]
    #     df = DataFrame(data=peaklist, columns=columns)
    #
    #     # save
    #     wildcard = (
    #         "CSV (Comma delimited) (*.csv)|*.csv|"
    #         + "Text (Tab delimited) (*.txt)|*.txt|"
    #         + "Text (Space delimited (*.txt)|*.txt"
    #     )
    #
    #     wildcard_dict = {",": 0, "\t": 1, " ": 2}
    #     dlg = wx.FileDialog(
    #         self,
    #         "Please select a name for the file",
    #         "",
    #         "",
    #         wildcard=wildcard,
    #         style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
    #     )
    #     dlg.CentreOnParent()
    #     if dlg.ShowModal() == wx.ID_OK:
    #         filename = dlg.GetPath()
    #         separator = list(wildcard_dict.keys())[list(wildcard_dict.values()).index(dlg.GetFilterIndex())]
    #         try:
    #             df.to_csv(path_or_buf=filename, sep=separator)
    #             print("Saved peaklist to {}".format(filename))
    #         except IOError:
    #             print("Could not save file as it is currently open in another program")

    def on_plot(self, _evt=None):
        """Plot data"""
        self.plot_view.plot(obj=self.data_obj)

    def on_plot_annotations(self, _evt=None):
        """Annotate plot area with annotations"""
        annotations = self.annotations

        self.on_annotate_spectrum_with_labels(None, repaint=False, annotations=annotations)
        self.on_annotate_spectrum_with_patches(None, repaint=False, annotations=annotations)
        self.on_annotate_spectrum_with_arrows(None, repaint=False, annotations=annotations)

        self.plot_view.repaint()

    def on_setup_plot_on_startup(self):
        """Setup plot on startup of the window"""
        self.on_plot()
        self.on_plot_annotations()

    def on_annotate_spectrum_with_patches(self, evt, repaint: bool = True, annotations: Annotations = None):
        """Annotate peaks on spectrum with patches"""
        t_start = time.time()

        if annotations is None:
            annotations = self.annotations

        if CONFIG.peak_panel_highlight:
            show_patch = annotations.patch_show
            x_left = annotations.patch_x_min[show_patch]
            y_bottom = annotations.patch_y_min[show_patch]
            height = annotations.height[show_patch]
            width = annotations.width[show_patch]
            names = annotations.names[show_patch]
            color = annotations.patch_colors[show_patch]
            self.plot_view.remove_patches(repaint=False)
            self.plot_view.add_patches(x_left, y_bottom, width, height, names, color, repaint=False)
        else:
            self.plot_view.remove_patches(repaint=False)

        if repaint:
            self.plot_view.repaint()

        logger.info(f"Annotated plot with patches in {report_time(t_start)}")

        if evt is not None:
            evt.Skip()

    # noinspection DuplicatedCode
    def on_annotate_spectrum_with_labels(
        self, evt, repaint: bool = True, annotations: Union[Annotations, Annotation] = None
    ):
        """Annotate peaks on spectrum with labels"""
        t_start = time.time()

        if annotations is None:
            annotations = self.annotations

        # get annotations data
        if isinstance(annotations, Annotations):
            x = annotations.label_position_x
            y = annotations.label_position_y
            names = annotations.names
            labels = annotations.labels
            color = annotations.label_colors
        else:
            x = [annotations.label_position_x]
            y = [annotations.label_position_y]
            names = [annotations.name]
            labels = [annotations.label]
            color = [annotations.label_color]

        # plot data
        self.plot_view.remove_labels(repaint=False)
        self.plot_view.add_labels(x, y, labels, names, color=color, repaint=False)

        if repaint:
            self.plot_view.repaint()

        if evt is not None:
            evt.Skip()

        logger.info(f"Annotated spectrum with labels in {report_time(t_start)}")

    # noinspection DuplicatedCode
    def on_annotate_spectrum_with_arrows(
        self, evt, repaint: bool = True, annotations: Union[Annotations, Annotation] = None
    ):
        """Annotate peaks on spectrum with arrows"""
        t_start = time.time()

        if annotations is None:
            annotations = self.annotations

        # get annotations data
        if isinstance(annotations, Annotations):
            show_arrow = annotations.arrow_show
            arrow_values = annotations.arrow_positions[show_arrow]
            names = annotations.names[show_arrow]
        else:
            arrow_values = [annotations.arrow_positions]
            names = [annotations.name]

        # plot data
        self.plot_view.remove_arrows(repaint=False)
        self.plot_view.add_arrows(arrow_values, name=names, repaint=False)

        if repaint:
            self.plot_view.repaint()

        if evt is not None:
            evt.Skip()

        logger.info(f"Annotated spectrum with labels in {report_time(t_start)}")

    def on_clear_from_plot(self, _evt):
        """Clear peaks and various annotations"""
        self.plot_view.remove_arrows(repaint=False)
        self.plot_view.remove_patches(repaint=False)
        self.plot_view.remove_labels(repaint=False)
        self.plot_view.repaint()

    def on_clear_plot(self, _evt):
        """Clear plot area"""
        self.plot_window.clear()

    def on_save_figure(self, _evt):
        """Save figure"""
        filename = "annotated"
        self.plot_view.save_figure(filename)

    def on_resize_check(self, _evt):
        """Resize checkbox"""
        self.panel_plot.on_resize_check(None)

    def on_copy_to_clipboard(self, _evt):
        """Copy plot to clipboard"""
        self.plot_window.copy_to_clipboard()

    def on_customise_plot(self, _evt):
        """Customise plot"""
        raise NotImplementedError("Must implement method")
        # self.panel_plot.on_customise_plot(None, plot="MS...", plot_obj=self.plot_window)

    def on_customise_parameters(self, _):
        """Open configuration panel"""
        from origami.gui_elements.dialog_customise_user_annotations import DialogCustomiseUserAnnotations

        dlg = DialogCustomiseUserAnnotations(self)
        dlg.ShowModal()


class TestPopup(TestPanel):
    """Test the popup window"""

    def __init__(self, parent):
        super().__init__(parent)

        self.btn_1.Bind(wx.EVT_BUTTON, self.on_popup)

    def on_popup(self, evt):
        """Activate popup"""
        p = PopupAnnotationSettings(self)
        p.position_on_event(evt)
        p.Show()


def _main_popup():
    app = wx.App()

    dlg = TestPopup(None)
    dlg.Show()

    app.MainLoop()


def _main():
    from origami.icons.assets import Icons

    app = wx.App()
    icons = Icons()
    ex = PanelAnnotationEditorUI(None, icons, "mass_spectrum")

    ex.Show()
    app.MainLoop()


if __name__ == "__main__":
    _main()
