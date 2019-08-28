# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import copy
import logging

import numpy as np
import processing.utils as pr_utils
import wx
from gui_elements.dialog_color_picker import DialogColorPicker
from gui_elements.dialog_customise_user_annotations import DialogCustomiseUserAnnotations
from gui_elements.misc_dialogs import DialogSimpleAsk
from objects.annotations import check_annotation_input
from pubsub import pub
from styles import ListCtrl
from styles import makeCheckbox
from styles import makeMenuItem
from styles import validator
from utils.check import check_value_order
from utils.color import convertRGB1to255
from utils.color import convertRGB255to1
from utils.color import determineFontColor
from utils.color import get_all_color_types
from utils.color import roundRGB
from utils.converters import rounder
from utils.converters import str2int
from utils.converters import str2num
from utils.exceptions import MessageError
from utils.labels import sanitize_string
from utils.screen import calculate_window_size
from visuals import mpl_plots

logger = logging.getLogger("origami")


# TODO: need to override the on_select_item with the built-in method OR call after with similar method
class PanelPeakAnnotationEditor(wx.MiniFrame):
    """
    Simple GUI to view and annotate mass spectra
    """

    def __init__(self, parent, documentTree, config, icons, **kwargs):
        wx.MiniFrame.__init__(
            self, parent, -1, "Annotation...", size=(-1, -1), style=wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER
        )

        self.parent = parent
        self.documentTree = documentTree
        self.panel_plot = documentTree.presenter.view.panelPlots
        self.config = config
        self.icons = icons

        self.data_processing = self.parent.presenter.data_processing
        self.data_handling = self.parent.presenter.data_handling

        self.query = kwargs["query"]
        self.plot_type = kwargs["plot_type"]
        self.document_title = kwargs["document_title"]
        self.dataset_type = kwargs["dataset_type"]
        self.dataset_name = kwargs["dataset_name"]
        self.annotations_obj = kwargs.pop("annotations")
        self.data = kwargs["data"]

        #         for i in range(wx.Display.GetCount()):
        #             display = wx.Display(i)
        #             print(display.IsPrimary(), display.GetGeometry(), self.GetPosition())

        self._display_size = wx.GetDisplaySize()
        self._display_resolution = wx.ScreenDC().GetPPI()
        self._window_size = calculate_window_size(self._display_size, 0.9)

        # presets
        self._menu_show_all = True
        self._menu_pin_label_to_intensity = True
        self._menu_autofix_label_position = False
        self.item_loading_lock = False

        self.config.annotation_patch_transparency = 0.2
        self.config.annotation_patch_width = 3

        # self.data_xmin = None
        # self.data_ymin = None
        # self.manual_add_only = False
        # if "data" in self.kwargs and self.data is not None:
        #     self.data_xmin = min(self.data[:, 0])
        #     self.data_ymin = max(self.data[:, 0])
        # elif self.data is None:
        #     self.manual_add_only = True

        # make gui items
        self.make_gui()
        self._update_title()
        self.on_populate_table()
        self.on_toggle_controls(None)

        self.plot = self.plot_window

        if self.plot_type == "mass_spectrum":
            self.on_plot_spectrum(self.data[:, 0], self.data[:, 1])
            self.plot_window._on_mark_annotation(True)

        # bind
        wx.EVT_CLOSE(self, self.on_close)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_event)

        # add listener
        pub.subscribe(self.add_annotation_from_mouse_evt, "mark_annotation")
        self.Bind(wx.EVT_CONTEXT_MENU, self.on_right_click)

    def on_right_click(self, evt):

        menu = wx.Menu()
        save_figure_menu_item = makeMenuItem(
            menu, id=wx.ID_ANY, text="Save figure as...", bitmap=self.icons.iconsLib["save16"]
        )
        menu.AppendItem(save_figure_menu_item)

        menu_action_copy_to_clipboard = makeMenuItem(
            parent=menu, id=wx.ID_ANY, text="Copy plot to clipboard", bitmap=self.icons.iconsLib["filelist_16"]
        )
        menu.AppendItem(menu_action_copy_to_clipboard)

        #         clear_plot_menu_item = makeMenuItem(
        #             menu, id=wx.ID_ANY, text="Clear plot", bitmap=self.icons.iconsLib["clear_16"]
        #         )
        #         menu.AppendSeparator()
        #         menu.AppendItem(clear_plot_menu_item)

        self.Bind(wx.EVT_MENU, self.on_save_figure, save_figure_menu_item)
        #         self.Bind(wx.EVT_MENU, self.on_clear_plot, clear_plot_menu_item)
        self.Bind(wx.EVT_MENU, self.on_copy_to_clipboard, menu_action_copy_to_clipboard)

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def _update_title(self):
        """Update widget title"""
        self.SetTitle(f"Annotationg: {self.document_title} :: {self.dataset_type} :: {self.dataset_name}")

    def get_annotation_data(self):
        """Quickly retrieve annotations object"""
        return self.data_handling.get_annotations_data(self.query, self.plot_type)

    def set_annotation_data(self):
        """Set annotations object"""
        raise NotImplementedError("Error")

    def on_key_event(self, evt):
        key_code = evt.GetKeyCode()
        if key_code == wx.WXK_ESCAPE:  # key = esc
            self.on_close(evt=None)
        evt.Skip()

    def on_close(self, evt):
        """Destroy this frame."""
        # reset state
        try:
            self.plot.plot_remove_temporary(repaint=True)
        except (AttributeError, TypeError):
            logger.warning("Failed to remove temporary marker")

        try:
            self.plot._on_mark_annotation(state=False)
        except AttributeError:
            logger.warning("Failed to unmark annotation state")

        try:
            pub.unsubscribe(self.add_annotation_from_mouse_evt, "mark_annotation")
        except Exception as err:
            logger.warning(f"Failed to unsubscribe from `mark_annotation`: {err}")

        self.documentTree.annotateDlg = None
        self.Destroy()

    def make_gui(self):

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

    def make_peaklist(self, panel):

        self.annotation_list = {
            "check": 0,
            "name": 1,
            "label": 2,
            "label_position": 3,
            "charge": 4,
            "patch_position": 5,
            "patch_color": 6,
            "color": 5,
            "arrow": 7,
            "arrow_show": 7,
        }

        self._annotations_peaklist = {
            0: {"name": "", "tag": "check", "type": "bool", "width": 20, "show": True},
            1: {"name": "name", "tag": "name", "type": "str", "width": 70, "show": True},
            2: {"name": "label", "tag": "label", "type": "str", "width": 100, "show": True},
            3: {"name": "label position", "tag": "label_position", "type": "list", "width": 100, "show": True},
            4: {"name": "z", "tag": "charge", "type": "int", "width": 30, "show": True},
            5: {"name": "patch position", "tag": "patch_position", "type": "list", "width": 100, "show": True},
            6: {"name": "patch color", "tag": "color", "type": "color", "width": 75, "show": True},
            7: {"name": "arrow", "tag": "arrow", "type": "str", "width": 45, "show": True},
        }

        self.peaklist = ListCtrl(panel, style=wx.LC_REPORT | wx.LC_VRULES, column_info=self._annotations_peaklist)
        for order, item in self._annotations_peaklist.items():
            name = item["name"]
            width = 0
            if item["show"]:
                width = item["width"]
            self.peaklist.InsertColumn(order, name, width=width, format=wx.LIST_FORMAT_CENTER)

        max_peaklist_size = (int(self._window_size[0] * 0.3), -1)
        self.peaklist.SetMaxClientSize(max_peaklist_size)

        self.peaklist.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_select_item)

    def make_plot_panel(self, split_panel):

        panel = wx.Panel(split_panel, -1, size=(-1, -1), name="plot")
        self.plot_panel = wx.Panel(panel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)

        pixel_size = [(self._window_size[0] - self._settings_panel_size[0]), (self._window_size[1] - 50)]
        figsize = [pixel_size[0] / self._display_resolution[0], pixel_size[1] / self._display_resolution[1]]

        self.plot_window = mpl_plots.plots(self.plot_panel, figsize=figsize, config=self.config)

        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(self.plot_window, 1, wx.EXPAND)
        box.Fit(self.plot_panel)
        self.plot_panel.SetSizer(box)
        self.plot_panel.Layout()

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.plot_panel, 1, wx.EXPAND, 2)
        # fit layout
        panel.SetSizer(main_sizer)
        main_sizer.Fit(panel)

        return panel

    def make_settings_panel(self, split_panel):

        panel = wx.Panel(split_panel, -1, size=(-1, -1), name="settings")

        # make peaklist
        self.make_peaklist(panel)

        name_value = wx.StaticText(panel, -1, "name:")
        self.name_value = wx.TextCtrl(panel, -1, "", style=wx.TE_RICH2)
        self.name_value.Disable()

        label_value = wx.StaticText(panel, -1, "annotation:")
        self.label_value = wx.TextCtrl(panel, -1, "", style=wx.TE_RICH2 | wx.TE_MULTILINE)
        self.label_value.SetBackgroundColour((255, 230, 239))
        #          self.intensity_value.SetToolTip(wx.ToolTip("Value (y) could represent intensity of an ion in a mass spectrum."))

        label_general = wx.StaticText(panel, -1, "label:")

        label_position_x = wx.StaticText(panel, -1, "label position (x):")
        self.label_position_x = wx.TextCtrl(panel, -1, "", validator=validator("float"))
        self.label_position_x.SetBackgroundColour((255, 230, 239))

        label_position_y = wx.StaticText(panel, -1, "label position (y):")
        self.label_position_y = wx.TextCtrl(panel, -1, "", validator=validator("float"))
        self.label_position_y.SetBackgroundColour((255, 230, 239))

        charge_value = wx.StaticText(panel, -1, "charge:")
        self.charge_value = wx.TextCtrl(panel, -1, "", validator=validator("int"))

        label_color = wx.StaticText(panel, -1, "label color:")
        self.label_color_btn = wx.Button(panel, wx.ID_ANY, "", size=wx.Size(26, 26), name="color.label")
        self.label_color_btn.SetBackgroundColour([0, 0, 0])
        self.label_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        add_arrow_to_peak = wx.StaticText(panel, -1, "add arrow:")
        self.add_arrow_to_peak = makeCheckbox(panel, "")
        self.add_arrow_to_peak.SetValue(False)
        self.add_arrow_to_peak.Bind(wx.EVT_CHECKBOX, self.on_add_annotation)

        patch_general = wx.StaticText(panel, -1, "patch:")

        patch_min_x = wx.StaticText(panel, -1, "position (x):")
        self.patch_min_x = wx.TextCtrl(panel, -1, "", validator=validator("float"))
        self.patch_min_x.SetBackgroundColour((255, 230, 239))

        patch_min_y = wx.StaticText(panel, -1, "position (y):")
        self.patch_min_y = wx.TextCtrl(panel, -1, "", validator=validator("float"))
        self.patch_min_y.SetBackgroundColour((255, 230, 239))

        patch_width = wx.StaticText(panel, -1, "width:")
        self.patch_width = wx.TextCtrl(panel, -1, "", validator=validator("float"))

        patch_height = wx.StaticText(panel, -1, "height:")
        self.patch_height = wx.TextCtrl(panel, -1, "", validator=validator("float"))

        patch_color = wx.StaticText(panel, -1, "patch color:")
        self.patch_color_btn = wx.Button(panel, wx.ID_ANY, "", size=wx.Size(26, 26), name="color.patch")
        self.patch_color_btn.SetBackgroundColour(convertRGB1to255(self.config.interactive_ms_annotations_color))
        self.patch_color_btn.Bind(wx.EVT_BUTTON, self.on_assign_color)

        horizontal_line_1 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_2 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_3 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        # make buttons
        self.add_btn = wx.Button(panel, wx.ID_OK, "Add", size=(-1, 22))
        self.remove_btn = wx.Button(panel, wx.ID_OK, "Remove", size=(-1, 22))
        self.cancel_btn = wx.Button(panel, wx.ID_OK, "Cancel", size=(-1, 22))
        self.show_btn = wx.Button(panel, wx.ID_OK, "Show ▼", size=(-1, 22))
        self.action_btn = wx.Button(panel, wx.ID_OK, "Action ▼", size=(-1, 22))

        self.highlight_on_selection = makeCheckbox(panel, "highlight")
        self.highlight_on_selection.SetValue(True)
        self.highlight_on_selection.Bind(wx.EVT_CHECKBOX, self.on_toggle_controls)

        self.zoom_on_selection = makeCheckbox(panel, "zoom-in")
        self.zoom_on_selection.SetValue(False)

        window_size = wx.StaticText(panel, wx.ID_ANY, "window size:")
        self.zoom_window_size = wx.SpinCtrlDouble(
            panel, -1, value=str(5), min=0.0001, max=250, initial=5, inc=25, size=(90, -1)
        )
        #
        #         label_format = wx.StaticText(panel, -1, "auto-label format:")
        #         self.label_format = wx.ComboBox(
        #             panel,
        #             -1,
        #             choices=["None", "charge-only [n+]", "charge-only [+n]", "superscript", "M+nH", "2M+nH", "3M+nH", "4M+nH"],
        #             value="None",
        #             style=wx.CB_READONLY,
        #             size=(-1, -1),
        #         )
        #
        self.add_btn.Bind(wx.EVT_BUTTON, self.on_add_annotation)
        self.remove_btn.Bind(wx.EVT_BUTTON, self.on_delete_annotation)
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_close)
        self.show_btn.Bind(wx.EVT_BUTTON, self.on_plot_tools)
        self.action_btn.Bind(wx.EVT_BUTTON, self.on_action_tools)
        #         self.label_format.Bind(wx.EVT_COMBOBOX, self.on_update_label)
        #
        # button grid
        btn_grid = wx.GridBagSizer(5, 5)
        y = 0
        btn_grid.Add(self.add_btn, (y, 0), flag=wx.ALIGN_CENTER)
        btn_grid.Add(self.remove_btn, (y, 1), flag=wx.ALIGN_CENTER)
        btn_grid.Add(self.show_btn, (y, 2), flag=wx.ALIGN_CENTER)
        btn_grid.Add(self.action_btn, (y, 3), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        btn_grid.Add(self.cancel_btn, (y, 4), flag=wx.ALIGN_CENTER)
        #         btn_grid.Add(label_format, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        #         btn_grid.Add(self.label_format, (y, 1), (1, 2), flag=wx.ALIGN_CENTER_VERTICAL)

        # pack elements
        grid = wx.GridBagSizer(5, 5)
        y = 0
        grid.Add(name_value, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.name_value, (y, 1), wx.GBSpan(1, 4), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y += 1
        grid.Add(label_value, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.label_value, (y, 1), wx.GBSpan(4, 4), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y += 4
        grid.Add(label_position_x, (y, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(label_position_y, (y, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        y += 1
        grid.Add(label_general, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.label_position_x, (y, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.label_position_y, (y, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        y += 1
        grid.Add(charge_value, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.charge_value, (y, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        y += 1
        grid.Add(label_color, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.label_color_btn, (y, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)
        y += 1
        grid.Add(add_arrow_to_peak, (y, 0), flag=wx.ALIGN_CENTER)
        grid.Add(self.add_arrow_to_peak, (y, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        y += 1
        grid.Add(horizontal_line_1, (y, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        y += 1
        grid.Add(patch_min_x, (y, 1), flag=wx.ALIGN_CENTER)
        grid.Add(patch_min_y, (y, 2), flag=wx.ALIGN_CENTER)
        grid.Add(patch_width, (y, 3), flag=wx.ALIGN_CENTER)
        grid.Add(patch_height, (y, 4), flag=wx.ALIGN_CENTER)
        y += 1
        grid.Add(patch_general, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.patch_min_x, (y, 1), flag=wx.ALIGN_CENTER)
        grid.Add(self.patch_min_y, (y, 2), flag=wx.ALIGN_CENTER)
        grid.Add(self.patch_width, (y, 3), flag=wx.ALIGN_CENTER)
        grid.Add(self.patch_height, (y, 4), flag=wx.ALIGN_CENTER)
        y += 1
        grid.Add(patch_color, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.patch_color_btn, (y, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        y += 1
        grid.Add(horizontal_line_2, (y, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        y += 1
        grid.Add(btn_grid, (y, 0), wx.GBSpan(1, 5), flag=wx.ALIGN_CENTER)
        y += 1
        grid.Add(horizontal_line_3, (y, 0), wx.GBSpan(1, 5), flag=wx.EXPAND)
        y += 1
        grid.Add(self.highlight_on_selection, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(self.zoom_on_selection, (y, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        grid.Add(window_size, (y, 2), flag=wx.ALIGN_CENTER)
        grid.Add(self.zoom_window_size, (y, 3), flag=wx.ALIGN_CENTER)

        # setup growable column
        grid.AddGrowableCol(4)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 0, wx.EXPAND, 0)
        main_sizer.Add(self.peaklist, 1, wx.EXPAND, 2)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def on_toggle_controls(self, evt):
        """Toggle various items in the UI based on event triggers"""

        if not self.highlight_on_selection.GetValue():
            self.plot_window.plot_remove_temporary(True)

        if evt is not None:
            evt.Skip()

    def on_copy_annotations(self, evt):
        rows = self.peaklist.GetItemCount()
        checked = []

        for row in range(rows):
            if self.peaklist.IsChecked(row):
                checked.append(row)

        if len(checked) == 0:
            print("Please check at least one annotation the table...")
            return

        annotations_obj = self.get_annotation_data()

        n_duplicates = DialogSimpleAsk(
            "How many times would you like to duplicate this annotations?", defaultValue="1", value_type="intPos"
        )
        n_duplicates = int(n_duplicates)
        for row in checked:
            __, annotation_obj = self.on_get_annotation_obj(row)

            for n_duplicate in range(1, n_duplicates + 1):
                annotation_obj_copy = copy.deepcopy(annotation_obj)
                annotation_obj_copy.name = annotation_obj_copy.name + f" ({n_duplicate})"
                annotations_obj.append_annotation(annotation_obj_copy)
                self.on_add_to_table(None, annotation_obj_copy)

        self.annotations_obj = annotations_obj
        self.documentTree.on_update_annotation(
            self.annotations_obj, self.document_title, self.dataset_type, self.dataset_name
        )

    def on_action_tools(self, evt):
        #         label_format = self.label_format.GetStringSelection()

        menu = wx.Menu()

        menu_action_customise = makeMenuItem(
            parent=menu, text="Customise other settings...", bitmap=self.icons.iconsLib["settings16_2"], help_text=""
        )
        menu_action_multiply = makeMenuItem(
            parent=menu, text="Create (similar) copies of selected annotations", bitmap=None
        )
        menu_action_edit_charge = makeMenuItem(
            parent=menu, text="Set charge state (selected)", bitmap=self.icons.iconsLib["assign_charge_16"]
        )
        menu_action_edit_patch_color = makeMenuItem(parent=menu, text="Set patch color (selected)")
        menu_action_edit_text_color = makeMenuItem(parent=menu, text="Set label color (selected)")

        menu_action_fix_label_intensity = makeMenuItem(parent=menu, text="Fix intensity / label position (selected)")
        #         menu_action_auto_generate_labels = makeMenuItem(
        #                 parent=menu,
        #                 text="Auto-generate labels ({})",  # TODO: add option for specifying type
        #             )
        menu_action_delete = makeMenuItem(parent=menu, text="Delete (selected)", bitmap=self.icons.iconsLib["bin16"])
        #         menu_action_add_from_csv = makeMenuItem(
        #                 parent=menu,
        #                 text="Add list of ions (.csv/.txt)",
        #                 bitmap=self.icons.iconsLib["filelist_16"],
        #                 help_text="Format: min, max, charge (optional), label (optional), color (optional)",
        #             )
        #         menu_action_save_to_csv = makeMenuItem(
        #                 parent=menu,
        #                 text="Save peaks to file (all)",
        #                 bitmap=self.icons.iconsLib["file_csv_16"],
        #             )

        menu.Append(menu_action_customise)
        menu.AppendSeparator()
        menu.Append(menu_action_multiply)
        #         menu.Append(menu_action_add_from_csv)
        menu.AppendSeparator()
        menu.Append(menu_action_edit_text_color)
        menu.Append(menu_action_edit_patch_color)
        menu.Append(menu_action_edit_charge)
        menu.Append(menu_action_fix_label_intensity)
        #         menu.Append(menu_action_auto_generate_labels)
        #         menu.AppendSeparator()
        #         menu.Append(menu_action_save_to_csv)
        menu.AppendSeparator()
        menu.Append(menu_action_delete)

        # bind events
        self.Bind(wx.EVT_MENU, self.on_change_item_parameter, menu_action_edit_charge)
        self.Bind(wx.EVT_MENU, self.on_delete_items, menu_action_delete)
        self.Bind(wx.EVT_MENU, self.on_assign_color, menu_action_edit_patch_color)
        self.Bind(wx.EVT_MENU, self.on_assign_color, menu_action_edit_text_color)
        self.Bind(wx.EVT_MENU, self.on_fix_intensity, menu_action_fix_label_intensity)
        #         self.Bind(wx.EVT_MENU, self.on_update_label, menu_action_auto_generate_labels)
        #         self.Bind(wx.EVT_MENU, self.on_load_peaklist, menu_action_add_from_csv)
        #         self.Bind(wx.EVT_MENU, self.on_save_peaklist, menu_action_save_to_csv)
        self.Bind(wx.EVT_MENU, self.on_customise_parameters, menu_action_customise)
        self.Bind(wx.EVT_MENU, self.on_copy_annotations, menu_action_multiply)

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def on_plot_tools(self, evt):

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
        menu_plot_show_mz_int_charge = menu.Append(wx.ID_ANY, "Show m/z, intensity, charge")
        menu_plot_show_charge = menu.Append(wx.ID_ANY, "Show charge")
        menu_plot_show_label = menu.Append(wx.ID_ANY, "Show label")

        # bind events
        self.Bind(wx.EVT_MENU, self.on_show_on_plot, menu_plot_show_charge)
        self.Bind(wx.EVT_MENU, self.on_show_on_plot, menu_plot_show_label)
        self.Bind(wx.EVT_MENU, self.on_show_on_plot, menu_plot_show_mz_int_charge)

        self.Bind(wx.EVT_TOOL, self.on_check_tools, self._menu_show_all_check)
        self.Bind(wx.EVT_TOOL, self.on_check_tools, self._menu_pin_label_to_intensity_check)
        self.Bind(wx.EVT_TOOL, self.on_check_tools, self._menu_autofix_label_position_check)

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def on_check_tools(self, evt):
        """ Check/uncheck menu item """
        name = evt.GetEventObject().FindItemById(evt.GetId()).GetLabel()

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
            print(self._menu_show_all)

    def on_customise_parameters(self, evt):

        dlg = DialogCustomiseUserAnnotations(self, config=self.config)
        dlg.ShowModal()

    def on_fix_intensity(self, evt):

        rows = self.peaklist.GetItemCount()
        if rows == 0:
            return

        for row in range(rows):
            if self.peaklist.IsChecked(index=row):

                __, annotation_obj = self.on_get_annotation_obj(row)

                mz_narrow = pr_utils.get_narrow_data_range(
                    data=self.data, mzRange=[annotation_obj.span_min, annotation_obj.span_max]
                )
                intensity = pr_utils.find_peak_maximum(mz_narrow)
                max_index = np.where(mz_narrow[:, 1] == intensity)[0]
                intensity = np.round(intensity, 2)
            try:
                position = mz_narrow[max_index, 0][0]
            except (IndexError, TypeError) as err:
                logger.warning(err)
                position = annotation_obj.label_position_x

            self.on_update_annotation(row, ["label_position"], **{"label_position": [position, intensity]})

    # def on_load_peaklist(self, evt):
    #     """
    #     This function opens a formatted CSV file with peaks
    #     """
    #     # TODO: Move to data handling
    #     raise MessageError("Function was removed", "Need to re-implement this...")

    #         dlg = wx.FileDialog(
    #             self,
    #             "Choose a text file (m/z, window size, charge):",
    #             wildcard="*.csv;*.txt",
    #             style=wx.FD_DEFAULT_STYLE | wx.FD_CHANGE_DIR,
    #         )
    #         if dlg.ShowModal() == wx.ID_CANCEL:
    #             return
    #         else:
    #
    #             # Create shortcut
    #             delimiter, __ = checkExtension(input=dlg.GetPath().encode("ascii", "replace"))
    #             peaklist = read_csv(dlg.GetPath(), delimiter=delimiter)
    #             peaklist = peaklist.fillna("")
    #
    #             columns = peaklist.columns.values.tolist()
    #             for min_name in ["min", "min m/z"]:
    #                 if min_name in columns:
    #                     break
    #                 else:
    #                     continue
    #             if min_name not in columns:
    #                 min_name = None
    #
    #             for max_name in ["max", "max m/z"]:
    #                 if max_name in columns:
    #                     break
    #                 else:
    #                     continue
    #             if max_name not in columns:
    #                 max_name = None
    #
    #             for position_name in ["position"]:
    #                 if position_name in columns:
    #                     break
    #                 else:
    #                     continue
    #             if position_name not in columns:
    #                 position_name = None
    #
    #             for charge_name in ["z", "charge"]:
    #                 if charge_name in columns:
    #                     break
    #                 else:
    #                     continue
    #             if charge_name not in columns:
    #                 charge_name = None
    #
    #             for label_name in ["label", "information"]:
    #                 if label_name in columns:
    #                     break
    #                 else:
    #                     continue
    #             if label_name not in columns:
    #                 label_name = None
    #
    #             for color_name in ["color", "colour"]:
    #                 if color_name in columns:
    #                     break
    #                 else:
    #                     continue
    #             if color_name not in columns:
    #                 color_name = None
    #
    #             for intensity_name in ["intensity"]:
    #                 if intensity_name in columns:
    #                     break
    #                 else:
    #                     continue
    #             if intensity_name not in columns:
    #                 intensity_name = None
    #
    #             if min_name is None or max_name is None:
    #                 return
    #
    #             # iterate
    #             color_value = str(convertRGB255to1(self.patch_color_btn.GetBackgroundColour()))
    #             arrow = False
    #             for peak in range(len(peaklist)):
    #                 min_value = peaklist[min_name][peak]
    #                 max_value = peaklist[max_name][peak]
    #                 if position_name is not None:
    #                     position = peaklist[position_name][peak]
    #                 else:
    #                     position = max_value - ((max_value - min_value) / 2)
    #
    #                 in_table, __ = self.checkDuplicate(min_value, max_value)
    #
    #                 if in_table:
    #                     continue
    #
    #                 if intensity_name is not None:
    #                     intensity = peaklist[intensity_name][peak]
    #                 else:
    #                     intensity = np.round(
    #                         pr_utils.find_peak_maximum(
    #                             pr_utils.get_narrow_data_range(data=self.data, mzRange=[min_value, max_value]),
    #                             fail_value=0.0,
    #                         ),
    #                         2,
    #                     )
    #                 if charge_name is not None:
    #                     charge_value = peaklist[charge_name][peak]
    #                 else:
    #                     charge_value = ""
    #
    #                 if label_name is not None:
    #                     label_value = peaklist[label_name][peak]
    #                 else:
    #                     label_value = ""
    #
    #                 self.peaklist.Append(
    #                     [
    #                         "",
    #                         str(min_value),
    #                         str(max_value),
    #                         str(position),
    #                         str(intensity),
    #                         str(charge_value),
    #                         str(label_value),
    #                         str(color_value),
    #                         str(arrow),
    #                     ]
    #                 )
    #
    #                 annotation_dict = {
    #                     "min": min_value,
    #                     "max": max_value,
    #                     "charge": charge_value,
    #                     "intensity": intensity,
    #                     "label": label_value,
    #                     "color": literal_eval(color_value),
    #                     "isotopic_x": position,
    #                     "isotopic_y": intensity,
    #                 }
    #
    #                 name = "{} - {}".format(min_value, max_value)
    #                 self.kwargs["annotations"][name] = annotation_dict
    #
    #             self.documentTree.on_update_annotation(
    #                 self.kwargs["annotations"], self.kwargs["document"], self.kwargs["dataset"]
    #             )
    #
    #             dlg.Destroy()

    def on_change_item_parameter(self, evt):
        """ Iterate over list to assign charge state """

        rows = self.peaklist.GetItemCount()
        if rows == 0:
            return

        if evt == "label":
            value = DialogSimpleAsk("Assign label for selected item(s)", defaultValue="")
            update_dict = {"label": value}
            update_item = ["label"]
        else:
            value = DialogSimpleAsk("Assign charge state for selected item(s)", defaultValue="1", value_type="int")
            update_dict = {"charge": value}
            update_item = ["charge"]

        if value is None:
            raise MessageError("Incorrect value", "Please type-in appropriate value next time")

        for row in range(rows):
            if self.peaklist.IsChecked(index=row):
                self.on_update_annotation(row, update_item, **update_dict)

    def on_delete_items(self, evt):
        rows = self.peaklist.GetItemCount() - 1

        while rows >= 0:
            if self.peaklist.IsChecked(index=rows):
                information = self.on_get_item_information(rows)
                self.on_delete_annotation(None, information["name"])
            rows -= 1

    def on_assign_color(self, evt):

        dlg = DialogColorPicker(self, self.config.customColors)
        if dlg.ShowModal() == "ok":
            color_255, color_1, __ = dlg.GetChosenColour()
            self.config.customColors = dlg.GetCustomColours()
        else:
            return

        try:
            name = evt.GetEventObject().GetName()
            if name == "color.patch":
                self.patch_color_btn.SetBackgroundColour(color_255)
            elif name == "color.label":
                self.label_color_btn.SetBackgroundColour(color_255)
        except AttributeError:
            name = evt.GetEventObject().FindItemById(evt.GetId()).GetLabel()
            if "label" in name:
                update_item = ["label_color"]
                update_dict = {"label_color": color_1}
            else:
                update_item = ["patch_color"]
                update_dict = {"patch_color": color_1}

            rows = self.peaklist.GetItemCount()
            for row in range(rows):
                if self.peaklist.IsChecked(index=row):
                    self.on_update_annotation(row, update_item, **update_dict)

    def on_get_item_information(self, item_id=None):
        if item_id is None:
            item_id = self.peaklist.item_id

        information = self.peaklist.on_get_item_information(item_id)
        information["color_255to1"] = convertRGB255to1(information["color"], decimals=3)

        return information

    def on_get_annotation_obj(self, item_id=None):
        if item_id is None:
            item_id = self.peaklist.item_id

        information = self.on_get_item_information(item_id)
        annotations_obj = self.get_annotation_data()
        annotation_obj = annotations_obj[information["name"]]

        return information, annotation_obj

    def on_select_item(self, evt):

        # disable automatic addition
        self.item_loading_lock = True

        # get data
        __, annotation_obj = self.on_get_annotation_obj(evt.GetIndex())

        # set data in GUI
        self.set_annotation_in_gui(None, annotation_obj)
        self.item_loading_lock = False

        # put a red patch around the peak of interest and zoom-in on the peak
        intensity = annotation_obj.intensity * 10

        if self.highlight_on_selection.GetValue():
            self.plot.plot_add_patch(
                annotation_obj.span_min,
                0,
                annotation_obj.width,
                intensity * 10,
                color="r",
                alpha=self.config.annotation_patch_transparency,
                add_temporary=True,
            )
            self.plot.repaint()

        if self.zoom_on_selection.GetValue():
            window_size = self.zoom_window_size.GetValue()
            self.plot.on_zoom(annotation_obj.span_min - window_size, annotation_obj.span_max + window_size, intensity)

    def on_populate_table(self):
        """Populate table with current annotations"""
        annotations = self.get_annotation_data()
        if annotations is None:
            return

        for annot_obj in annotations.values():
            self.on_add_to_table(None, annot_obj)

    def on_update_annotation(self, index, update_item, **annotation_dict):
        if not isinstance(update_item, list):
            update_item = list(update_item)

        information = self.on_get_item_information(index)

        annotations_obj = self.get_annotation_data()
        annotations_obj.update_annotation(information["name"], annotation_dict)
        self.annotations_obj = annotations_obj
        self.documentTree.on_update_annotation(
            self.annotations_obj, self.document_title, self.dataset_type, self.dataset_name
        )

        try:
            self.on_update_value_in_peaklist(index, update_item, annotation_dict)
        except KeyError as err:
            logger.info(err)

    def get_values_from_data(self, xmin, xmax, ymin, ymax):

        intensity = np.round(np.average([ymin, ymax]), 4)
        # try to get position and intensity from data
        try:
            # get narrow data values
            mz_narrow = pr_utils.get_narrow_data_range(data=self.data, mzRange=[xmin, xmax])
            # get maximum intensity from the subselected data
            intensity = pr_utils.find_peak_maximum(mz_narrow)
            # retrieve index value
            max_index = np.where(mz_narrow[:, 1] == intensity)[0]
            position = mz_narrow[max_index, 0][0]
        except (IndexError, TypeError) as err:
            position = xmax - ((xmax - xmin) / 2)
            logger.warning(f"Failed to get annotation intensity / position. {err}", exc_info=True)

        charge = self.data_processing.predict_charge_state(
            self.data[:, 0], self.data[:, 1], [xmin - 2, xmax + 2], std_dev=self.config.annotation_charge_std_dev
        )

        label = f"x={position:.4f}\ny={intensity:.2f}\ncharge={charge:d}"
        name = f"x={position:.4f}; y={intensity:.2f}"
        height = ymax - ymin
        width = xmax - xmin

        if self.plot_type in ["mass_spectrum", "1D"]:
            height = intensity

        return intensity, position, charge, height, width, label, name

    def set_annotation_in_gui(self, info_dict=None, annotation_obj=None):
        if info_dict is None and annotation_obj is None:
            raise MessageError(
                "Error", "You must provide either `info_dict` or `annotation_obj` to complete this action"
            )

        if info_dict is None:
            name = annotation_obj.name
            label = annotation_obj.label
            label_position_x = annotation_obj.label_position_x
            label_position_y = annotation_obj.label_position_y
            charge = annotation_obj.charge
            arrow_show = annotation_obj.arrow_show
            color = annotation_obj.patch_color
            label_color = annotation_obj.label_color
            patch_position = annotation_obj.patch_position
        else:
            name = info_dict["name"]
            label = info_dict["label"]
            label_position_x = info_dict["label_position_x"]
            label_position_y = info_dict["label_position_y"]
            charge = info_dict["charge"]
            arrow_show = info_dict["arrow"]
            label_color = info_dict["label_color"]
            color = info_dict["color"]
            patch_position = info_dict["patch_position"]

        # set values in GUI
        self.name_value.SetValue(name)
        self.label_value.SetValue(label)
        self.label_position_x.SetValue(rounder(label_position_x, 4))
        self.label_position_y.SetValue(rounder(label_position_y, 4))
        self.charge_value.SetValue(str(charge))
        self.add_arrow_to_peak.SetValue(arrow_show)
        self.patch_color_btn.SetBackgroundColour(convertRGB1to255(color))
        self.label_color_btn.SetBackgroundColour(convertRGB1to255(label_color))
        self.patch_min_x.SetValue(rounder(patch_position[0], 4))
        self.patch_min_y.SetValue(rounder(patch_position[1], 4))
        self.patch_width.SetValue(rounder(patch_position[2], 4))
        self.patch_height.SetValue(rounder(patch_position[3], 4))

    def get_annotation_from_gui(self):
        info_dict = {
            "name": self.name_value.GetValue(),
            "label": self.label_value.GetValue(),
            "label_position": [str2num(self.label_position_x.GetValue()), str2num(self.label_position_y.GetValue())],
            "charge": str2int(self.charge_value.GetValue()),
            "label_color": convertRGB255to1(self.label_color_btn.GetBackgroundColour()),
            "arrow_show": self.add_arrow_to_peak.GetValue(),
            "patch_position": [
                str2num(self.patch_min_x.GetValue()),
                str2num(self.patch_min_y.GetValue()),
                str2num(self.patch_width.GetValue()),
                str2num(self.patch_height.GetValue()),
            ],
            "color": convertRGB255to1(self.patch_color_btn.GetBackgroundColour()),
        }

        return info_dict

    def check_for_duplcate(self, name):
        """Check for duplicate items with the same name"""
        count = self.peaklist.GetItemCount()
        for i in range(count):
            information = self.on_get_item_information(i)

            if information["name"] == name:
                return True, i

        return False, -1

    def add_annotation_from_mouse_evt(self, xmin, xmax, ymin, ymax):
        """Add annotations from mouse event"""

        xmin, xmax = check_value_order(xmin, xmax)
        ymin, ymax = check_value_order(ymin, ymax)

        intensity, position, charge, height, width, label, name = self.get_values_from_data(xmin, xmax, ymin, ymax)

        info_dict = {
            "name": name,
            "label": label,
            "label_position_x": position,
            "label_position_y": intensity,
            "label_position": [position, intensity],
            "arrow": False,
            "width": width,
            "height": height,
            "charge": charge,
            "color": self.config.interactive_ms_annotations_color,
            "label_color": (0.0, 0.0, 0.0),
            "patch_position": [xmin, ymin, width, height],
        }

        self.set_annotation_in_gui(info_dict)
        self.add_btn.SetFocus()

    def on_add_annotation(self, evt):
        if self.item_loading_lock:
            return

        # trigger events
        self.on_toggle_controls(None)

        annotation_dict = self.get_annotation_from_gui()
        name = sanitize_string(annotation_dict["name"])
        annotation_dict["name"] = name

        try:
            annotation_dict = check_annotation_input(annotation_dict)
        except ValueError as err:
            logger.error(err, exc_info=True)
            raise MessageError("Incorrect input", str(err))

        in_table, item_id = self.check_for_duplcate(name)
        annotations_obj = self.get_annotation_data()

        if in_table:
            annotations_obj.update_annotation(name, annotation_dict)
            self.on_update_value_in_peaklist(
                item_id, ["color", "charge", "label_position", "patch_position", "label", "arrow_show"], annotation_dict
            )
        else:
            annotations_obj.add_annotation(name, annotation_dict)
            self.on_add_to_table(None, annotations_obj[name])

        self.annotations_obj = annotations_obj

        #         label_format = self.label_format.GetStringSelection()
        #         if label_value in ["", None, "None"]:
        #             label_value = ut_labels.convert_str_to_unicode(str(charge_value), return_type=label_format)
        #
        #
        #
        #         # check for duplicate
        #         in_table, index = self.checkDuplicate(min_value, max_value)
        #         if in_table:
        #             # annotate duplicate item
        #             if index != -1:
        #                 self.kwargs["annotations"][name]["charge"] = charge_value
        #                 self.peaklist.SetStringItem(index, self.annotation_list["charge"], str(charge_value))
        #
        #                 if intensity not in ["", "None", None, False]:
        #                     self.kwargs["annotations"][name]["intensity"] = intensity
        #                     self.kwargs["annotations"][name]["isotopic_y"] = intensity
        #                     self.peaklist.SetStringItem(index, self.annotation_list["intensity"], str(intensity))
        #
        #                 if position not in ["", "None", None, False]:
        #                     self.kwargs["annotations"][name]["isotopic_x"] = position
        #                     self.peaklist.SetStringItem(index, self.annotation_list["position"], str(position))
        #
        #                 self.kwargs["annotations"][name]["add_arrow"] = add_arrow
        #                 self.peaklist.SetStringItem(index, self.annotation_list["arrow"], str(add_arrow))
        #
        #                 self.kwargs["annotations"][name]["position_label_x"] = position_label_x
        #                 self.kwargs["annotations"][name]["position_label_y"] = position_label_y
        #
        #                 self.kwargs["annotations"][name]["label"] = label_value
        #                 self.peaklist.SetStringItem(index, self.annotation_list["label"], label_value)
        #
        #                 self.kwargs["annotations"][name]["color"] = literal_eval(color_value)
        #                 self.peaklist.SetStringItem(index, self.annotation_list["color"], color_value)
        #
        #             self.documentTree.on_update_annotation(
        #                 self.kwargs["annotations"], self.kwargs["document"], self.kwargs["dataset"], set_data_only=True
        #             )
        #             return
        #
        #         if min_value is None or max_value is None:
        #             DialogBox("Error", "Please fill min, max fields at least!", type="Error")
        #             return
        #
        #         if charge_value is None:
        #             charge_value = 0
        #
        #         if intensity in ["", "None", None, False] and self.data and not self.manual_add_only:
        #             mz_narrow = pr_utils.get_narrow_data_range(data=self.data, mzRange=[min_value, max_value])
        #             intensity = pr_utils.find_peak_maximum(mz_narrow)
        #             max_index = np.where(mz_narrow[:, 1] == intensity)[0]
        #             intensity = np.round(intensity, 2)
        #
        #         if position in ["", "None", None, False]:
        #             try:
        #                 position = mz_narrow[max_index, 0]
        #             except Exception:
        #                 position = max_value - ((max_value - min_value) / 2)
        #
        #         try:
        #             if len(position) > 1:
        #                 position = position[0]
        #         except Exception:
        #             pass
        #
        #         annotation_dict = {
        #             "min": min_value,
        #             "max": max_value,
        #             "charge": charge_value,
        #             "intensity": intensity,
        #             "label": label_value,
        #             "color": literal_eval(color_value),
        #             "isotopic_x": position,
        #             "isotopic_y": intensity,
        #             "add_arrow": add_arrow,
        #             "position_label_x": position_label_x,
        #             "position_label_y": position_label_y,
        #         }
        #
        #         self.kwargs["annotations"][name] = annotation_dict
        #         self.peaklist.Append(
        #             ["", min_value, max_value, position, intensity, charge_value, label_value, color_value, str(add_arrow)]
        #         )
        #
        #         if not self.manual_add_only:
        #             plt_kwargs = self._buildPlotParameters(plotType="label")
        #             self.plot.plot_add_text_and_lines(xpos=position, yval=intensity, label=charge_value, **plt_kwargs)
        #             self.plot.repaint()
        #

        self.documentTree.on_update_annotation(
            self.annotations_obj, self.document_title, self.dataset_type, self.dataset_name
        )
        self.on_add_label_to_plot(annotations_obj[name])

    def on_delete_annotation(self, evt, name=None):

        # get name if one is not provided
        if name is None:
            name = self.name_value.GetValue()

        # get item index
        __, index = self.check_for_duplcate(name)

        if index != -1:
            annotations_obj = self.get_annotation_data()
            annotations_obj.remove_annotation(name)
            self.peaklist.DeleteItem(index)

            self.annotations_obj = annotations_obj
            self.documentTree.on_update_annotation(
                self.annotations_obj, self.document_title, self.dataset_type, self.dataset_name
            )

    def on_add_to_table(self, add_dict, annot_obj=None):
        """Add data to table"""

        # add using dictionary
        if add_dict:
            color = add_dict["color"]
            self.peaklist.Append(
                [
                    "",
                    add_dict["xmin"],
                    add_dict["xmax"],
                    add_dict["position"],
                    add_dict["intensity"],
                    add_dict["charge"],
                    add_dict["label"],
                    str(roundRGB(convertRGB255to1(color))),
                    str(add_dict["add_arrow"]),
                ]
            )
        # add using nanotations object
        else:
            color = convertRGB1to255(annot_obj.patch_color)
            self.peaklist.Append(
                [
                    "",
                    annot_obj.name,
                    annot_obj.label,
                    annot_obj.label_position,
                    annot_obj.charge,
                    annot_obj.patch_position,
                    str(roundRGB(convertRGB255to1(color))),
                    str(annot_obj.arrow_show),
                ]
            )
        self.peaklist.SetItemBackgroundColour(self.peaklist.GetItemCount() - 1, color)
        self.peaklist.SetItemTextColour(self.peaklist.GetItemCount() - 1, determineFontColor(color, return_rgb=True))

    def on_update_value_in_peaklist(self, item_id, value_types, values):

        if not isinstance(value_types, list):
            value_types = [value_types]

        for value_type in value_types:
            value = values[value_type]
            if value_type in ["color", "patch_color"]:
                color_255, color_1, font_color = get_all_color_types(value)
                self.peaklist.SetItemBackgroundColour(item_id, color_255)
                self.peaklist.SetStringItem(item_id, self.annotation_list["patch_color"], str(color_1))
                self.peaklist.SetItemTextColour(item_id, font_color)
            else:
                column_id = self.annotation_list[value_type]
                self.peaklist.SetStringItem(item_id, column_id, str(value))

    def on_add_label_to_plot(self, annotation_obj):
        label_kwargs = self.panel_plot._buildPlotParameters(plotType="label")

        show_label = "{:.2f}, {}\nz={}".format(annotation_obj.position, annotation_obj.intensity, annotation_obj.charge)

        # add  custom name tag
        obj_name_tag = "{}|-|{}|-|{} - {}|-|{}".format(
            self.document_title, self.dataset_name, annotation_obj.span_min, annotation_obj.span_max, "annotation"
        )
        label_kwargs["text_name"] = obj_name_tag

        # add label to the plot
        self.plot.plot_add_text_and_lines(
            xpos=annotation_obj.label_position_x,
            yval=annotation_obj.label_position_y,
            label=show_label,
            vline=False,
            vline_position=annotation_obj.position,
            stick_to_intensity=self._menu_pin_label_to_intensity,
            yoffset=self.config.annotation_label_y_offset,
            color=annotation_obj.label_color,
            **label_kwargs,
        )
        self.plot.repaint()

    def on_show_on_plot(self, evt):

        menu_name = evt.GetEventObject().FindItemById(evt.GetId()).GetLabel()

        label_fmt = "all"
        if "Show charge" in menu_name:
            label_fmt = "charge"
        elif "Show label" in menu_name:
            label_fmt = "label"

        annotations_obj = self.get_annotation_data()
        self.panel_plot.on_plot_1D_annotations(
            annotations_obj,
            plot=None,
            plot_obj=self.plot,
            label_fmt=label_fmt,
            pin_to_intensity=self._menu_pin_label_to_intensity,
            document_title=self.document_title,
            dataset_name=self.dataset_name,
        )

    #         # clear plot
    #         self.plot.plot_remove_text_and_lines()
    #         # prepare plot kwargs
    #         label_kwargs = self.panel_plot._buildPlotParameters(plotType="label")
    #         arrow_kwargs = self.panel_plot._buildPlotParameters(plotType="arrow")
    #         vline = False
    #         _ymax = []
    #
    #         annotations_obj = self.get_annotation_data()
    #         for name, annotation_obj in annotations_obj.items():
    #             __, index = self.check_for_duplcate(name)
    #             if self._menu_show_all or self.peaklist.IsChecked(index):
    #                 #         for key in self.kwargs["annotations"]:
    #                 #             # get annotation
    #                 #             annotation = self.kwargs["annotations"][key]
    #                 #             print(annotation)
    #                 #             intensity = str2num(annotation["intensity"])
    #                 #             charge = annotation["charge"]
    #                 #             label = annotation["label"]
    #                 #             min_x_value = annotation["min"]
    #                 #             max_x_value = annotation["max"]
    #                 #             color_value = annotation.get("color", self.config.interactive_ms_annotations_color)
    #                 #             add_arrow = annotation.get("add_arrow", False)
    #                 #
    #                 #             if "isotopic_x" in annotation:
    #                 #                 mz_value = annotation["isotopic_x"]
    #                 #                 if mz_value in ["", 0] or mz_value < min_x_value:
    #                 #                     mz_value = max_x_value - ((max_x_value - min_x_value) / 2)
    #                 #             else:
    #                 #                 mz_value = max_x_value - ((max_x_value - min_x_value) / 2)
    #                 #
    #                 #             label_x_position = annotation.get("position_label_x", mz_value)
    #                 #             label_y_position = annotation.get("position_label_y", intensity)
    #                 #
    #                 if "Show charge" in menu_name:
    #                     show_label = annotation_obj.charge
    #                 elif "Show label" in menu_name:
    #                     show_label = ut_labels._replace_labels(annotation_obj.label)
    #                 else:
    #                     show_label = "{:.2f}, {}\nz={}".format(
    #                         annotation_obj.position, annotation_obj.intensity, annotation_obj.charge
    #                     )
    #
    #                 if show_label == "":
    #                     continue
    #
    #             # arrows have 4 positional parameters:
    #             #    xpos, ypos = correspond to the label position
    #             #    dx, dy = difference between label position and peak position
    #             if annotation_obj.arrow_show and self._menu_pin_label_to_intensity:
    #                 arrow_list, arrow_x_end, arrow_y_end = annotation_obj.get_arrow_position()
    #
    #             # add  custom name tag
    #             obj_name_tag = "{}|-|{}|-|{} - {}|-|{}".format(
    #                 self.document_title,
    #                 self.dataset_name,
    #                 annotation_obj.span_min,
    #                 annotation_obj.span_max,
    #                 "annotation",
    #             )
    #             label_kwargs["text_name"] = obj_name_tag
    #
    #             # add label to the plot
    #             self.plot.plot_add_text_and_lines(
    #                 xpos=annotation_obj.label_position_x,
    #                 yval=annotation_obj.label_position_y,
    #                 label=show_label,
    #                 vline=vline,
    #                 vline_position=annotation_obj.position,
    #                 stick_to_intensity=self._menu_pin_label_to_intensity,
    #                 yoffset=self.config.annotation_label_y_offset,
    #                 color=annotation_obj.label_color,
    #                 **label_kwargs,
    #             )
    #
    #             _ymax.append(annotation_obj.label_position_y)
    #             if annotation_obj.arrow_show and self._menu_pin_label_to_intensity:
    #                 arrow_kwargs["text_name"] = obj_name_tag
    #                 arrow_kwargs["props"] = [arrow_x_end, arrow_y_end]
    #                 print(arrow_list)
    #                 self.plot.plot_add_arrow(
    #                     arrow_list, stick_to_intensity=self._menu_pin_label_to_intensity, **arrow_kwargs
    #                 )
    #
    #         if self._menu_autofix_label_position:
    #             self.plot._fix_label_positions()
    #
    #         # update intensity
    #         if self.config.annotation_zoom_y:
    #             try:
    #                 self.plot.on_zoom_y_axis(endY=np.amax(_ymax) * self.config.annotation_zoom_y_multiplier)
    #             except TypeError:
    #                 pass
    #
    #         self.plot.repaint()

    #     def on_update_label(self, evt):
    #         evtID = evt.GetId()
    #         label_format = self.label_format.GetStringSelection()
    #             rows = self.peaklist.GetItemCount()
    #             for row in range(rows):
    #                 if self.peaklist.IsChecked(index=row):
    #                     charge_value = self.peaklist.GetItem(row, self.annotation_list["charge"]).GetText()
    #                     label_value = ut_labels.convert_str_to_unicode(str(charge_value), return_type=label_format)
    #                     self.peaklist.SetStringItem(row, self.annotation_list["label"], label=label_value)
    #                     self.onUpdateAnnotation(row)
    #
    #             # update document
    #             self.documentTree.on_update_annotation(
    #                 self.kwargs["annotations"], self.kwargs["document"], self.kwargs["dataset"]
    #             )
    #         else:
    #             if self.peaklist.item_id is None:
    #                 return
    #
    #             charge_value = self.peaklist.GetItem(self.peaklist.item_id, self.annotation_list["charge"]).GetText()
    #             label_value = ut_labels.convert_str_to_unicode(str(charge_value), return_type=label_format)
    #             self.label_value.SetValue(label_value)

    def on_save_peaklist(self, evt):
        from pandas import DataFrame

        peaklist = []
        for key in self.kwargs["annotations"]:
            annotation = self.kwargs["annotations"][key]
            intensity = str2num(annotation["intensity"])
            charge = annotation["charge"]
            label = annotation["label"]
            min_value = annotation["min"]
            max_value = annotation["max"]
            isotopic_x = annotation.get("isotopic_x", "")
            peaklist.append([min_value, max_value, isotopic_x, intensity, charge, label])

        # make dataframe
        columns = ["min", "max", "position", "intensity", "charge", "label"]
        df = DataFrame(data=peaklist, columns=columns)

        # save
        wildcard = (
            "CSV (Comma delimited) (*.csv)|*.csv|"
            + "Text (Tab delimited) (*.txt)|*.txt|"
            + "Text (Space delimited (*.txt)|*.txt"
        )

        wildcard_dict = {",": 0, "\t": 1, " ": 2}
        dlg = wx.FileDialog(
            self,
            "Please select a name for the file",
            "",
            "",
            wildcard=wildcard,
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        )
        dlg.CentreOnParent()
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
            separator = list(wildcard_dict.keys())[list(wildcard_dict.values()).index(dlg.GetFilterIndex())]
            try:
                df.to_csv(path_or_buf=filename, sep=separator)
                print("Saved peaklist to {}".format(filename))
            except IOError:
                print("Could not save file as it is currently open in another program")

    def checkDuplicate(self, min_value, max_value):
        count = self.peaklist.GetItemCount()
        for i in range(count):
            table_min = str2num(self.peaklist.GetItem(i, self.annotation_list["min"]).GetText())
            table_max = str2num(self.peaklist.GetItem(i, self.annotation_list["max"]).GetText())

            if min_value == table_min and max_value == table_max:
                return True, i
            else:
                continue

        return False, -1

    def on_plot_spectrum(self, mz_x, mz_y):
        """Plot mass spectrum"""
        self.panel_plot.on_plot_MS(
            mz_x,
            mz_y,
            show_in_window="peak_picker",
            plot_obj=self.plot_window,
            override=False,
            prevent_extraction=False,
        )

    def on_clear_plot(self, evt):
        self.plot_window.clearPlot()

    def on_save_figure(self, evt):

        plot_title = f"{self.document_title}_{self.dataset_name}".replace(" ", "-").replace(":", "")
        self.panel_plot.save_images(None, None, plot_obj=self.plot_window, image_name=plot_title)

    def on_copy_to_clipboard(self, evt):
        self.plot_window.copy_to_clipboard()
