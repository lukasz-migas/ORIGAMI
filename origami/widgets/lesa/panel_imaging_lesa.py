# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
# Load libraries
import logging

import wx
from styles import ListCtrl
from styles import make_menu_item
from styles import MiniFrame
from utils.exceptions import MessageError
from utils.screen import calculate_window_size

logger = logging.getLogger("origami")


class PanelImagingLESAViewer(MiniFrame):
    """LESA viewer and editor"""

    _peaklist_peaklist = {
        0: {"name": "", "tag": "check", "type": "bool", "show": True, "width": 20},
        1: {"name": "ion name", "tag": "ion_name", "type": "str", "show": True, "width": 80},
        2: {"name": "z", "tag": "charge", "type": "int", "show": True, "width": 35},
        3: {"name": "int", "tag": "intensity", "type": "float", "show": True, "width": 50},
        4: {"name": "color", "tag": "color", "type": "color", "show": True, "width": 80},
        5: {"name": "colormap", "tag": "colormap", "type": "str", "show": True, "width": 80},
        6: {"name": "label", "tag": "label", "type": "str", "show": True, "width": 70},
        7: {"name": "document", "tag": "document", "type": "str", "show": True, "width": 70},
    }

    keyword_alias = {"colormap": "cmap"}

    def __init__(self, parent, presenter, config, icons, **kwargs):
        MiniFrame.__init__(
            self,
            parent,
            title="Imaging: LESA",
            style=wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX,
            bind_key_events=False,
        )

        self.parent = parent
        self.presenter = presenter
        self.view = presenter.view
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

        # make gui items
        self.make_gui()
        self.on_toggle_controls(None)

        # bind
        self.Bind(wx.EVT_CONTEXT_MENU, self.on_right_click)

    def on_right_click(self, evt):
        # ensure that user clicked inside the plot area
        if not hasattr(evt.EventObject, "figure"):
            return

    #         menu = wx.Menu()
    #         menu_action_customise_plot = make_menu_item(
    #             parent=menu, text="Customise plot...", bitmap=self.icons.iconsLib["change_xlabels_16"]
    #         )
    #         menu.AppendItem(menu_action_customise_plot)
    #         menu.AppendSeparator()
    #         self.resize_plot_check = menu.AppendCheckItem(-1, "Resize on saving")
    #         self.resize_plot_check.Check(self.config.resize)
    #         save_figure_menu_item = make_menu_item(
    #             menu, id=wx.ID_ANY, text="Save figure as...", bitmap=self.icons.iconsLib["save16"]
    #         )
    #         menu.AppendItem(save_figure_menu_item)
    #         menu_action_copy_to_clipboard = make_menu_item(
    #             parent=menu, id=wx.ID_ANY, text="Copy plot to clipboard", bitmap=self.icons.iconsLib["filelist_16"]
    #         )
    #         menu.AppendItem(menu_action_copy_to_clipboard)
    #
    #         menu.AppendSeparator()
    #         clear_plot_menu_item = make_menu_item(
    #             menu, id=wx.ID_ANY, text="Clear plot", bitmap=self.icons.iconsLib["clear_16"]
    #         )
    #         menu.AppendItem(clear_plot_menu_item)
    #
    #         self.Bind(wx.EVT_MENU, self.on_resize_check, self.resize_plot_check)
    #         self.Bind(wx.EVT_MENU, self.on_customise_plot, menu_action_customise_plot)
    #         self.Bind(wx.EVT_MENU, self.on_save_figure, save_figure_menu_item)
    #         self.Bind(wx.EVT_MENU, self.on_copy_to_clipboard, menu_action_copy_to_clipboard)
    #         self.Bind(wx.EVT_MENU, self.on_clear_plot, clear_plot_menu_item)
    #
    #         self.PopupMenu(menu)
    #         menu.Destroy()
    #         self.SetFocus()

    def _get_accepted_keywords_from_dict(self, item_info):
        keywords = ["color", "colormap", "alpha", "mask", "label", "min_threshold", "max_threshold", "charge", "cmap"]
        keys = list(item_info.keys())
        for key in keys:
            if key not in keywords:
                item_info.pop(key)

        for bad_key, good_key in self.keyword_alias.items():
            item_info[good_key] = item_info[bad_key]

        return item_info

    def on_close(self, evt):
        """Destroy this frame"""

        #         n_overlay_items = len(self.overlay_data)
        #         if n_overlay_items > 0:
        #             from gui_elements.misc_dialogs import DialogBox
        #
        #             msg = (
        #                 f"Found {n_overlay_items} overlay item(s) in the clipboard. Closing this window will lose"
        #                 + " your overlay plots. Would you like to continue?"
        #             )
        #             dlg = DialogBox(exceptionTitle="Clipboard is not empty", exceptionMsg=msg, type="Question")
        #             if dlg == wx.ID_NO:
        #                 msg = "Action was cancelled"
        #                 return

        self.Destroy()

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
        settings_panel = self.make_settings_panel(self)
        self._settings_panel_size = settings_panel.GetSize()
        settings_panel.SetMinSize((400, -1))

        plot_panel = self.make_plot_panel(self)

        # pack elements
        self.main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.main_sizer.Add(plot_panel, 1, wx.EXPAND, 0)
        self.main_sizer.Add(settings_panel, 0, wx.EXPAND, 0)

        # fit layout
        self.main_sizer.Fit(self)
        self.SetSizer(self.main_sizer)
        self.SetSize(self._window_size)
        self.Layout()
        self.Show(True)

        self.CentreOnScreen()
        self.SetFocus()

    def on_toggle_controls(self, evt):
        #         editor_type = self.dataset_type_choice.GetStringSelection()
        #         heatmap, spectra = False, True
        #         if editor_type == "Heatmaps":
        #             heatmap, spectra = True, False
        #
        #         obj_list = []
        #         for item in obj_list:
        #             item.Enable(enable=heatmap)
        #         obj_list = [self.normalize_1D_check]
        #         for item in obj_list:
        #             item.Enable(enable=spectra)

        if evt is not None:
            evt.Skip()

    def on_apply(self, evt):

        if evt is not None:
            evt.Skip()

    def make_settings_panel(self, split_panel):

        panel = wx.Panel(split_panel, -1, size=(-1, -1), name="settings")

        # make listctrl
        self.make_listctrl_panel(panel)

        # pack buttons
        #         btn_grid = wx.GridBagSizer(2, 2)
        #         n = 0
        #         btn_grid.Add(self.action_btn, (n, 0), flag=wx.ALIGN_CENTER)
        #         btn_grid.Add(self.plot_btn, (n, 1), flag=wx.ALIGN_CENTER)
        #         btn_grid.Add(self.add_to_document_btn, (n, 2), flag=wx.ALIGN_CENTER)
        #         btn_grid.Add(self.cancel_btn, (n, 3), flag=wx.ALIGN_CENTER)
        #         btn_grid.Add(self.hot_plot_check, (n, 4), flag=wx.ALIGN_CENTER)

        #         # pack heatmap items
        #         grid = wx.GridBagSizer(2, 2)
        #         n = 0
        #         grid.Add(dataset_type_choice, (n, 0), flag=wx.ALIGN_RIGHT | wx.EXPAND)
        #         grid.Add(self.dataset_type_choice, (n, 1), flag=wx.ALIGN_CENTER | wx.EXPAND)
        #         grid.Add(self.refresh_btn, (n, 2), flag=wx.ALIGN_CENTER)
        #         n += 1
        #         grid.Add(overlay_method_choice, (n, 0), flag=wx.ALIGN_RIGHT | wx.EXPAND)
        #         grid.Add(self.overlay_method_choice, (n, 1), flag=wx.ALIGN_CENTER | wx.EXPAND)
        #         n += 1
        #         grid.Add(horizontal_line_2, (n, 0), wx.GBSpan(1, 4), flag=wx.EXPAND)
        #         n += 1
        #         grid.Add(self.normalize_1D_check, (n, 1), flag=wx.ALIGN_RIGHT | wx.EXPAND)
        #
        #         # setup growable column
        #         grid.AddGrowableCol(3)
        #
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        #         main_sizer.Add(grid, 0, wx.ALL | wx.EXPAND, 5)
        #         main_sizer.Add(horizontal_line_99, 0, wx.EXPAND, 10)
        #         main_sizer.Add(btn_grid, 0, wx.ALIGN_CENTRE_HORIZONTAL, 10)
        main_sizer.Add(self.peaklist, 1, wx.EXPAND, 10)
        #
        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def make_plot_panel(self, split_panel):

        #         pixel_size = [(self._window_size[0] - self._settings_panel_size[0]), (self._window_size[1] - 50)]
        #         figsize = [pixel_size[0] / self._display_resolution[0], pixel_size[1] / self._display_resolution[1]]

        panel = wx.SplitterWindow(split_panel, wx.ID_ANY, style=wx.TAB_TRAVERSAL | wx.SP_3DSASH, name="plot")

        self.plot_panel_MS, self.plot_window_MS, __ = self.panel_plot.make_plot(
            panel, self.config._plotSettings["MS"]["gui_size"]
        )
        self.plot_panel_img, self.plot_window_img, __ = self.panel_plot.make_plot(
            panel, self.config._plotSettings["2D"]["gui_size"]
        )

        panel.SplitHorizontally(self.plot_panel_MS, self.plot_panel_img)
        panel.SetMinimumPaneSize(300)
        panel.SetSashGravity(0.5)
        panel.SetSashSize(5)

        #         box = wx.BoxSizer(wx.VERTICAL)
        #         box.Add(self.plot_window, 1, wx.EXPAND)
        #         box.Fit(self.plot_panel)
        #         self.plot_panel.SetSizer(box)
        #         self.plot_panel.Layout()
        #
        #         main_sizer = wx.BoxSizer(wx.VERTICAL)
        #         main_sizer.Add(self.plot_panel, 1, wx.EXPAND, 2)
        #         # fit layout
        #         panel.SetSizer(main_sizer)
        #         main_sizer.Fit(panel)

        return panel

    def make_listctrl_panel(self, panel):

        self.peaklist = ListCtrl(panel, style=wx.LC_REPORT | wx.LC_VRULES, column_info=self._peaklist_peaklist)
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
        self.peaklist.SetMaxClientSize(max_peaklist_size)

        #         self.peaklist.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.menu_right_click)
        #         self.peaklist.Bind(wx.EVT_LIST_COL_RIGHT_CLICK, self.menu_column_right_click)
        self.peaklist.Bind(wx.EVT_LEFT_DCLICK, self.on_double_click_on_item)

    def on_double_click_on_item(self, evt):
        """Create annotation for activated peak."""

        if self.peaklist.item_id != -1:
            if not self.item_editor:
                self.on_open_editor(evt=None)
                return
            self.item_editor.on_update_gui(self.on_get_item_information(self.peaklist.item_id))

    def on_open_editor(self, evt):
        #         from gui_elements.panel_modify_item_settings import PanelModifyItemSettings

        if self.peaklist.item_id is None or self.peaklist.item_id < 0:
            raise MessageError("Error", "Please select an item in the table")

        information = self.on_get_item_information(self.peaklist.item_id)
        print(information)

    #         editor_type = self.dataset_type_choice.GetStringSelection()
    #         if editor_type in ["Heatmaps", "Chromatograms", "Mobilograms"]:
    #             overlay_type = "overlay.full"
    #         else:
    #             overlay_type = "overlay.simple"
    #
    #         self.item_editor = PanelModifyItemSettings(
    #             self, self.presenter, self.config, alt_parent=self.view, overlay_type=overlay_type, **information
    #         )
    #         self.item_editor.Centre()
    #         self.item_editor.Show()

    def on_action_tools(self, evt):

        menu = wx.Menu()

        menu_action_create_blank_document = make_menu_item(
            parent=menu,
            text="Create blank IMAGING document",
            bitmap=self.icons.iconsLib["new_document_16"],
            help_text="",
        )

        menu.AppendItem(menu_action_create_blank_document)

        # bind events
        self.Bind(wx.EVT_MENU, self.on_create_blank_document, menu_action_create_blank_document)

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def on_create_blank_document(self, evt):
        self.data_handling.create_new_document_of_type(document_type="imaging")

    #     def on_double_click_on_item(self, evt):
    #         logger.error("Method not implemented yet")
    #
    #     def menu_right_click(self, evt):
    #         logger.error("Method not implemented yet")
    #
    #     def menu_column_right_click(self, evt):
    #         logger.error("Method not implemented yet")

    def on_assign_color(self, evt, item_id=None, give_value=False):
        """Assign new color

        Parameters
        ----------
        evt : wxPython event
            unused
        itemID : int
            value for item in table
        give_value : bool
            should/not return color
        """
        #         from gui_elements.dialog_color_picker import DialogColorPicker
        pass

    #         if item_id is not None:
    #             self.peaklist.item_id = item_id
    #
    #         if item_id is None:
    #             item_id = self.peaklist.item_id
    #
    #         if item_id is None:
    #             return
    #
    #         dlg = DialogColorPicker(self, self.config.customColors)
    #         if dlg.ShowModal() == "ok":
    #             color_255, color_1, font_color = dlg.GetChosenColour()
    #             self.config.customColors = dlg.GetCustomColours()
    #             self.on_update_value_in_peaklist(item_id, "color", [color_255, color_1, font_color])
    #
    #             # update document
    #             self.on_update_document(evt=None)
    #
    #             if give_value:
    #                 return color_255

    def on_update_value_in_peaklist(self, item_id, value_type, value):
        pass

    #         if value_type == "color":
    #             color_255, color_1, font_color = value
    #             self.peaklist.SetItemBackgroundColour(item_id, color_255)
    #             self.peaklist.SetStringItem(item_id, self.config.overlay_list_col_names["color"], str(color_1))
    #             self.peaklist.SetItemTextColour(item_id, font_color)
    #         elif value_type == "color_text":
    #             self.peaklist.SetItemBackgroundColour(item_id, value)
    #             self.peaklist.SetStringItem(
    #                 item_id, self.config.overlay_list_col_names["color"], str(convert_rgb_255_to_1(value))
    #             )
    #             self.peaklist.SetItemTextColour(item_id, get_font_color(value, return_rgb=True))

    def on_toggle_table_columns(self, data_type):
        """Toggle table columns based on the dataset type"""

    #
    #         show_columns = [
    #             "check",
    #             "dataset_name",
    #             "dataset_type",
    #             "document",
    #             "shape",
    #             "color",
    #             "colormap",
    #             "alpha",
    #             "mask",
    #             "label",
    #             "min_threshold",
    #             "max_threshold",
    #             "processed",
    #             "order",
    #         ]
    #         if data_type in ["mass_spectra", "chromatogram", "mobilogram"]:
    #             show_columns = [
    #                 "check",
    #                 "dataset_name",
    #                 "dataset_type",
    #                 "document",
    #                 "shape",
    #                 "color",
    #                 "label",
    #                 "processed",
    #                 "order",
    #             ]
    #
    #         for column_id in self._peaklist_peaklist:
    #             width = self._peaklist_peaklist[column_id]["width"]
    #             if self._peaklist_peaklist[column_id]["tag"] not in show_columns:
    #                 width = 0
    #             self.peaklist.SetColumnWidth(column_id, width)

    def on_get_item_information(self, item_id):
        information = self.peaklist.on_get_item_information(item_id)

        # add additional data
        #         information["color_255to1"] = convert_rgb_255_to_1(information["color"], decimals=3)
        #         information["color"] = list(information["color"])[0:3]
        #         information["item_name"] = "{}::{}::{}".format(
        #             information["dataset_name"], information["dataset_type"], information["document"]
        #         )

        return information
