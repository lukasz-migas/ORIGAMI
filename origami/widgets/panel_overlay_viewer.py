# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
# Load libraries
import logging

import wx
from styles import ListCtrl
from styles import makeCheckbox
from styles import makeMenuItem
from styles import MiniFrame
from utils import color
from utils.color import check_color_format
from utils.color import convertRGB255to1
from utils.color import determineFontColor
from utils.color import roundRGB
from utils.random import get_random_int
from utils.screen import calculate_window_size
from visuals import mpl_plots

# from gui_elements.dialog_color_picker import DialogColorPicker

logger = logging.getLogger("origami")


class PanelOverlayViewer(MiniFrame):
    """Overlay viewer and editor"""

    def __init__(self, parent, presenter, config, icons, **kwargs):
        MiniFrame.__init__(
            self,
            parent,
            title="Overlay viewer & editor...",
            style=wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX,
        )

        self.parent = parent
        self.presenter = presenter
        self.config = config
        self.icons = icons

        self.data_handling = presenter.data_handling
        self.data_processing = presenter.data_processing
        self.data_visualisation = presenter.data_visualisation

        self.panel_plot = self.presenter.view.panelPlots
        self.document_tree = self.presenter.view.panelDocuments.documents

        self._display_size = wx.GetDisplaySize()
        self._display_resolution = wx.ScreenDC().GetPPI()
        self._window_size = calculate_window_size(self._display_size, 0.9)

        self.generate_peaklist_config()

        # make gui items
        self.make_gui()

        # bind
        self.Bind(wx.EVT_CONTEXT_MENU, self.on_right_click)

    def generate_peaklist_config(self):

        # peaklist list
        self._peaklist_peaklist = {
            0: {"name": "", "tag": "check", "type": "bool", "width": 25, "show": True},
            1: {"name": "name", "tag": "dataset_name", "type": "str", "width": 130, "show": True},
            2: {"name": "type", "tag": "dataset_type", "type": "str", "width": 100, "show": True},
            3: {"name": "document", "tag": "document", "type": "str", "width": 100, "show": True},
            4: {"name": "shape", "tag": "shape", "type": "str", "width": 65, "show": True},
            5: {"name": "color", "tag": "color", "type": "color", "width": 65, "show": True},
            6: {"name": "colormap", "tag": "colormap", "type": "str", "width": 60, "show": True},
            7: {"name": "\N{GREEK SMALL LETTER ALPHA}", "tag": "alpha", "type": "float", "width": 35, "show": True},
            8: {"name": "mask", "tag": "mask", "type": "float", "width": 40, "show": True},
            9: {"name": "label", "tag": "label", "type": "str", "width": 50, "show": True},
            10: {"name": "min", "tag": "min_threshold", "type": "float", "width": 50, "show": True},
            11: {"name": "max", "tag": "max_threshold", "type": "float", "width": 50, "show": True},
            12: {"name": "processed", "tag": "processed", "type": "str", "width": 65, "show": True},
            13: {"name": "#", "tag": "order", "type": "int", "width": 25, "show": True},
        }

    def on_right_click(self, evt):

        menu = wx.Menu()
        menu_action_customise_plot = makeMenuItem(
            parent=menu, text="Customise plot...", bitmap=self.icons.iconsLib["change_xlabels_16"]
        )
        menu.AppendItem(menu_action_customise_plot)
        menu.AppendSeparator()
        self.resize_plot_check = menu.AppendCheckItem(-1, "Resize on saving")
        self.resize_plot_check.Check(self.config.resize)
        save_figure_menu_item = makeMenuItem(
            menu, id=wx.ID_ANY, text="Save figure as...", bitmap=self.icons.iconsLib["save16"]
        )
        menu.AppendItem(save_figure_menu_item)
        menu_action_copy_to_clipboard = makeMenuItem(
            parent=menu, id=wx.ID_ANY, text="Copy plot to clipboard", bitmap=self.icons.iconsLib["filelist_16"]
        )
        menu.AppendItem(menu_action_copy_to_clipboard)

        menu.AppendSeparator()
        clear_plot_menu_item = makeMenuItem(
            menu, id=wx.ID_ANY, text="Clear plot", bitmap=self.icons.iconsLib["clear_16"]
        )
        menu.AppendItem(clear_plot_menu_item)

        self.Bind(wx.EVT_MENU, self.on_resize_check, self.resize_plot_check)
        self.Bind(wx.EVT_MENU, self.on_customise_plot, menu_action_customise_plot)
        self.Bind(wx.EVT_MENU, self.on_save_figure, save_figure_menu_item)
        self.Bind(wx.EVT_MENU, self.on_copy_to_clipboard, menu_action_copy_to_clipboard)
        self.Bind(wx.EVT_MENU, self.on_clear_plot, clear_plot_menu_item)

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def on_clear_plot(self, evt):
        self.plot_window.clearPlot()

    def on_resize_check(self, evt):
        self.panel_plot.on_resize_check(None)

    def on_copy_to_clipboard(self, evt):
        self.plot_window.copy_to_clipboard()

    def on_customise_plot(self, evt):
        self.panel_plot.on_customise_plot(None, plot="Overlay...", plot_obj=self.plot_window)

    def on_save_figure(self, evt):
        plot_title = "overlay"

        self.panel_plot.save_images(None, None, plot_obj=self.plot_window, image_name=plot_title)

    def make_gui(self):

        # make panel
        panel = wx.Panel(self, -1, size=(-1, -1), name="main")

        settings_panel = self.make_settings_panel(panel)
        self._settings_panel_size = settings_panel.GetSize()

        plot_panel = self.make_plot_panel(panel)

        # pack elements
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

    def make_settings_panel(self, split_panel):
        panel = wx.Panel(split_panel, -1, size=(-1, -1), name="settings")

        dataset_type_choice = wx.StaticText(panel, -1, "Editor type:")
        self.dataset_type_choice = wx.ComboBox(
            panel, choices=["Mass spectra", "Chromatograms", "Mobilograms", "Heatmaps"], style=wx.CB_READONLY
        )
        self.dataset_type_choice.SetStringSelection("Heatmaps")

        overlay_method_choice = wx.StaticText(panel, -1, "Overlay method:")
        self.overlay_method_choice = wx.ComboBox(panel, choices=self.config.overlayChoices, style=wx.CB_READONLY)
        self.overlay_method_choice.SetStringSelection(self.config.overlayMethod)

        self.use_processed_data_check = makeCheckbox(panel, "Use processed data (if available)")
        self.use_processed_data_check.SetValue(False)

        self.normalize_1D_check = makeCheckbox(panel, "Normalize before plotting")
        self.normalize_1D_check.SetValue(self.config.compare_massSpectrumParams["normalize"])

        self.make_listctrl_panel(panel)

        horizontal_line_99 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        self.plot_btn = wx.Button(panel, wx.ID_OK, "Plot", size=(-1, 22))
        self.add_to_document_btn = wx.Button(panel, wx.ID_OK, "Add to document", size=(-1, 22))
        self.cancel_btn = wx.Button(panel, wx.ID_OK, "Cancel", size=(-1, 22))

        self.plot_btn.Bind(wx.EVT_BUTTON, self.on_populate_item_list)
        self.add_to_document_btn.Bind(wx.EVT_BUTTON, self.on_overlay)
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_close)

        btn_grid = wx.GridBagSizer(2, 2)
        n = 0
        btn_grid.Add(self.plot_btn, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        btn_grid.Add(
            self.add_to_document_btn,
            (n, 1),
            wx.GBSpan(1, 1),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL,
        )
        btn_grid.Add(
            self.cancel_btn, (n, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL
        )

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(dataset_type_choice, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_RIGHT | wx.EXPAND)
        grid.Add(
            self.dataset_type_choice,
            (n, 1),
            wx.GBSpan(1, 1),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL | wx.EXPAND,
        )
        n += 1
        grid.Add(overlay_method_choice, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_RIGHT | wx.EXPAND)
        grid.Add(
            self.overlay_method_choice,
            (n, 1),
            wx.GBSpan(1, 1),
            flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL | wx.EXPAND,
        )
        n += 1
        #         grid.Add(horizontal_line_1, (n, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
        n += 1
        grid.Add(self.use_processed_data_check, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_RIGHT | wx.EXPAND)
        n += 1
        grid.Add(self.normalize_1D_check, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_RIGHT | wx.EXPAND)
        n += 1
        #         grid.Add(horizontal_line_99, (n, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
        #         n += 1
        #         grid.Add(btn_grid, (n, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 0, wx.EXPAND, 10)
        main_sizer.Add(horizontal_line_99, 0, wx.EXPAND, 10)
        main_sizer.Add(btn_grid, 0, wx.ALIGN_CENTRE_HORIZONTAL, 10)
        main_sizer.Add(self.peaklist, 1, wx.EXPAND, 10)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def make_listctrl_panel(self, panel):

        self.peaklist = ListCtrl(
            panel, style=wx.LC_REPORT | wx.LC_VRULES, column_info=self._peaklist_peaklist, use_simple_sorter=True
        )
        for col in range(len(self._peaklist_peaklist)):
            item = self._peaklist_peaklist[col]
            order = col
            name = item["name"]
            width = 0
            if item["show"]:
                width = item["width"]
            self.peaklist.InsertColumn(order, name, width=width, format=wx.LIST_FORMAT_CENTER)
            self.peaklist.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        max_peaklist_size = (int(self._window_size[0] * 0.3), -1)
        self.peaklist.SetSize(max_peaklist_size)
        self.peaklist.SetMaxClientSize(max_peaklist_size)

    def make_plot_panel(self, split_panel):

        panel = wx.Panel(split_panel, -1, size=(-1, -1), name="plot")
        self.plot_panel = wx.Panel(panel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)

        pixel_size = [(self._window_size[0] - self._settings_panel_size[0]), (self._window_size[1] - 50)]
        figsize = [pixel_size[0] / self._display_resolution[0], pixel_size[1] / self._display_resolution[1]]

        self.plot_window = mpl_plots.plots(self.plot_panel, figsize=figsize, config=self.config)

        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(self.plot_window, 1, wx.EXPAND)
        box.Fit(self.plot_panel)

        #         self.plot_window.SetSize(pixel_size)
        self.plot_panel.SetSizer(box)
        self.plot_panel.Layout()

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.plot_panel, 1, wx.EXPAND, 2)
        # fit layout
        panel.SetSizer(main_sizer)
        main_sizer.Fit(panel)

        return panel

    def on_populate_item_list(self, evt):
        self.peaklist.DeleteAllItems()

        item_list = self.data_handling.generate_item_list("heatmap")

        for add_dict in item_list:
            color = add_dict.get("color", self.config.customColors[get_random_int(0, 15)])
            color = check_color_format(color)

            self.peaklist.Append(
                [
                    "",
                    str(add_dict.get("dataset_name", "")),
                    str(add_dict.get("dataset_type", "")),
                    str(add_dict.get("document_title", "")),
                    str(add_dict.get("shape", "")),
                    str(roundRGB(convertRGB255to1(color))),
                    str(add_dict.get("cmap", "")),
                    str(add_dict.get("alpha", "")),
                    str(add_dict.get("mask", "")),
                    str(add_dict.get("label", "")),
                    str(add_dict.get("min_threshold", "")),
                    str(add_dict.get("max_threshold", "")),
                    str(add_dict.get("processed", "")),
                    str(add_dict.get("overlay_order", "")),
                ]
            )
            item_count = self.peaklist.GetItemCount() - 1
            self.peaklist.SetItemBackgroundColour(item_count, color)
            self.peaklist.SetItemTextColour(item_count, determineFontColor(color, return_rgb=True))

    def get_selected_items(self):
        item_count = self.peaklist.GetItemCount()

        # generate list of document_title and dataset_name
        item_list = []
        for item_id in range(item_count):
            information = self.on_get_item_information(item_id)
            if information["select"]:
                item_list.append(information)

        return item_list

    def on_get_item_information(self, itemID, return_list=False):
        information = self.peaklist.on_get_item_information(itemID)

        # add additional data
        information["color_255to1"] = convertRGB255to1(information["color"], decimals=3)

        return information

    def on_overlay(self, evt):
        item_list = self.get_selected_items()

        editor_type = self.dataset_type_choice.GetStringSelection()
        #         overlay_method = self.overlay_method_choice.GetStringSelection()

        print(editor_type)

        if editor_type == "Chromatograms":
            self.data_visualisation.on_overlay_chromatogram(
                item_list, plot=None, plot_obj=self.plot_window, normalize_dataset=self.normalize_1D_check.GetValue()
            )
        elif editor_type == "Mobilograms":
            self.data_visualisation.on_overlay_mobilogram(
                item_list, plot=None, plot_obj=self.plot_window, normalize_dataset=self.normalize_1D_check.GetValue()
            )
