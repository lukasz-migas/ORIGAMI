# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
# Load libraries
import logging
from copy import deepcopy

import wx
from styles import ListCtrl
from styles import make_checkbox
from styles import make_menu_item
from styles import make_tooltip
from styles import MiniFrame
from utils.color import check_color_format
from utils.color import convert_rgb_255_to_1
from utils.color import get_font_color
from utils.color import round_rgb
from utils.exceptions import MessageError
from utils.random import get_random_int
from utils.screen import calculate_window_size
from visuals import mpl_plots

# from gui_elements.dialog_color_picker import DialogColorPicker
logger = logging.getLogger("origami")


class PanelOverlayViewer(MiniFrame):
    """Overlay viewer and editor"""

    # peaklist list
    _peaklist_peaklist = {
        0: {"name": "", "tag": "check", "type": "bool", "width": 20, "show": True},
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
    keyword_alias = {"colormap": "cmap"}

    overlay_methods_1D = sorted(["Overlay", "Waterfall", "Subtract (n=2)", "Butterfly (n=2)"])
    overlay_methods_2D = sorted(
        [
            "Mask",
            "Transparent",
            "RGB",
            "Mean",
            "Variance",
            "Standard Deviation",
            "RMSD",
            "RMSF",
            "RMSD Matrix",
            "Grid (2->1)",
            "Grid (n x n)",
        ]
    )

    def __init__(self, parent, presenter, config, icons, **kwargs):
        MiniFrame.__init__(
            self,
            parent,
            title="Overlay viewer & editor...",
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

        # preset
        self.item_editor = None
        self.dataset_type = None
        self.overlay_data = dict()

        # make gui items
        self.make_gui()
        self.on_toggle_controls(None)
        self.on_populate_item_list(None)

        # bind
        self.Bind(wx.EVT_CONTEXT_MENU, self.on_right_click)

    def on_right_click(self, evt):
        # ensure that user clicked inside the plot area
        if not hasattr(evt.EventObject, "figure"):
            return

        menu = wx.Menu()
        menu_action_customise_plot = make_menu_item(
            parent=menu, text="Customise plot...", bitmap=self.icons.iconsLib["change_xlabels_16"]
        )
        menu.AppendItem(menu_action_customise_plot)
        menu.AppendSeparator()
        self.resize_plot_check = menu.AppendCheckItem(-1, "Resize on saving")
        self.resize_plot_check.Check(self.config.resize)
        save_figure_menu_item = make_menu_item(
            menu, id=wx.ID_ANY, text="Save figure as...", bitmap=self.icons.iconsLib["save16"]
        )
        menu.AppendItem(save_figure_menu_item)
        menu_action_copy_to_clipboard = make_menu_item(
            parent=menu, id=wx.ID_ANY, text="Copy plot to clipboard", bitmap=self.icons.iconsLib["filelist_16"]
        )
        menu.AppendItem(menu_action_copy_to_clipboard)

        menu.AppendSeparator()
        clear_plot_menu_item = make_menu_item(
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

    def _get_accepted_keywords_from_dict(self, item_info):
        keywords = ["color", "colormap", "alpha", "mask", "label", "min_threshold", "max_threshold", "charge", "cmap"]
        keys = list(item_info.keys())
        for key in keys:
            if key not in keywords:
                item_info.pop(key)

        for bad_key, good_key in self.keyword_alias.items():
            item_info[good_key] = item_info[bad_key]

        return item_info

    def on_update_document(self, evt, item_info=None):

        # get item info
        if item_info is None:
            item_info = self.on_get_item_information(self.peaklist.item_id)

        editor_type = self.dataset_type_choice.GetStringSelection()
        if editor_type in ["Heatmaps", "Chromatograms", "Mobilograms"]:
            query = [item_info["document"], item_info["dataset_type"], item_info["dataset_name"]]
            item_info = self._get_accepted_keywords_from_dict(deepcopy(item_info))
            document = self.data_handling.set_mobility_chromatographic_keyword_data(query, **item_info)
            #         elif editor_type == "Mass Spectra":
            #             pass

            # Update file list
            self.data_handling.on_update_document(document, "no_refresh")

    def on_close(self, evt):
        """Destroy this frame"""

        n_overlay_items = len(self.overlay_data)
        if n_overlay_items > 0:
            from gui_elements.misc_dialogs import DialogBox

            msg = (
                f"Found {n_overlay_items} overlay item(s) in the clipboard. Closing this window will lose"
                + " your overlay plots. Would you like to continue?"
            )
            dlg = DialogBox(exceptionTitle="Clipboard is not empty", exceptionMsg=msg, type="Question")
            if dlg == wx.ID_NO:
                msg = "Action was cancelled"
                return

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

    def on_toggle_controls(self, evt):
        editor_type = self.dataset_type_choice.GetStringSelection()
        heatmap, spectra = False, True
        if editor_type == "Heatmaps":
            heatmap, spectra = True, False

        obj_list = []
        for item in obj_list:
            item.Enable(enable=heatmap)
        obj_list = [self.normalize_1D_check]
        for item in obj_list:
            item.Enable(enable=spectra)

        if evt is not None:
            evt.Skip()

    def on_apply(self, evt):

        if evt is not None:
            evt.Skip()

    def make_settings_panel(self, split_panel):

        panel = wx.Panel(split_panel, -1, size=(-1, -1), name="settings")

        dataset_type_choice = wx.StaticText(panel, -1, "Dataset type:")
        self.dataset_type_choice = wx.ComboBox(
            panel, choices=sorted(["Mass spectra", "Chromatograms", "Mobilograms", "Heatmaps"]), style=wx.CB_READONLY
        )
        self.dataset_type_choice.SetStringSelection("Heatmaps")
        self.dataset_type_choice.Bind(wx.EVT_COMBOBOX, self.on_apply)
        self.dataset_type_choice.Bind(wx.EVT_COMBOBOX, self.on_toggle_controls)
        self.dataset_type_choice.Bind(wx.EVT_COMBOBOX, self.on_populate_item_list)

        self.refresh_btn = wx.BitmapButton(
            panel,
            -1,
            self.icons.iconsLib["refresh16"],
            size=(22, 22),
            style=wx.BORDER_DEFAULT | wx.ALIGN_CENTER_VERTICAL,
        )
        self.refresh_btn.Bind(wx.EVT_BUTTON, self.on_populate_item_list)
        self.refresh_btn.SetToolTip(
            make_tooltip("Re-populate table for specified dataset. All checkboxes will be erased")
        )

        overlay_method_choice = wx.StaticText(panel, -1, "Overlay method:")
        self.overlay_method_choice = wx.ComboBox(panel, choices=self.overlay_methods_2D, style=wx.CB_READONLY)
        self.overlay_method_choice.SetStringSelection(self.config.overlayMethod)

        self.normalize_1D_check = make_checkbox(panel, "Normalize before plotting")
        self.normalize_1D_check.SetValue(self.config.compare_massSpectrumParams["normalize"])

        # make listctrl
        self.make_listctrl_panel(panel)

        horizontal_line_2 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_99 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        self.action_btn = wx.Button(panel, wx.ID_OK, "Action ▼", size=(-1, 22))
        self.action_btn.Bind(wx.EVT_BUTTON, self.on_action_tools)

        self.plot_btn = wx.Button(panel, wx.ID_OK, "Plot", size=(-1, 22))
        self.plot_btn.Bind(wx.EVT_BUTTON, self.on_overlay)

        self.add_to_document_btn = wx.Button(panel, wx.ID_OK, "Add to document", size=(-1, 22))
        self.add_to_document_btn.Bind(wx.EVT_BUTTON, self.on_add_to_document)

        self.cancel_btn = wx.Button(panel, wx.ID_OK, "Cancel", size=(-1, 22))
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_close)

        self.hot_plot_check = make_checkbox(panel, "Hot plot")
        self.hot_plot_check.SetValue(False)
        self.hot_plot_check.Disable()

        # pack buttonswx.ALIGN_CENTER
        btn_grid = wx.GridBagSizer(2, 2)
        n = 0
        btn_grid.Add(self.action_btn, (n, 0), flag=wx.ALIGN_CENTER)
        btn_grid.Add(self.plot_btn, (n, 1), flag=wx.ALIGN_CENTER)
        btn_grid.Add(self.add_to_document_btn, (n, 2), flag=wx.ALIGN_CENTER)
        btn_grid.Add(self.cancel_btn, (n, 3), flag=wx.ALIGN_CENTER)
        btn_grid.Add(self.hot_plot_check, (n, 4), flag=wx.ALIGN_CENTER)

        # pack heatmap items
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(dataset_type_choice, (n, 0), flag=wx.ALIGN_RIGHT | wx.EXPAND)
        grid.Add(self.dataset_type_choice, (n, 1), flag=wx.ALIGN_CENTER | wx.EXPAND)
        grid.Add(self.refresh_btn, (n, 2), flag=wx.ALIGN_CENTER)
        n += 1
        grid.Add(overlay_method_choice, (n, 0), flag=wx.ALIGN_RIGHT | wx.EXPAND)
        grid.Add(self.overlay_method_choice, (n, 1), flag=wx.ALIGN_CENTER | wx.EXPAND)
        n += 1
        grid.Add(horizontal_line_2, (n, 0), wx.GBSpan(1, 4), flag=wx.EXPAND)
        n += 1
        grid.Add(self.normalize_1D_check, (n, 1), flag=wx.ALIGN_RIGHT | wx.EXPAND)

        # setup growable column
        grid.AddGrowableCol(3)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 0, wx.ALL | wx.EXPAND, 5)
        main_sizer.Add(horizontal_line_99, 0, wx.EXPAND, 10)
        main_sizer.Add(btn_grid, 0, wx.ALIGN_CENTRE_HORIZONTAL, 10)
        main_sizer.Add(self.peaklist, 1, wx.EXPAND, 10)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

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
            else:
                self.item_editor.on_update_gui(self.on_get_item_information(self.peaklist.item_id))

    def on_open_editor(self, evt):
        from gui_elements.panel_modify_item_settings import PanelModifyItemSettings

        if self.peaklist.item_id is None or self.peaklist.item_id < 0:
            raise MessageError("Error", "Please select an item in the table")

        information = self.on_get_item_information(self.peaklist.item_id)
        editor_type = self.dataset_type_choice.GetStringSelection()
        if editor_type in ["Heatmaps", "Chromatograms", "Mobilograms"]:
            overlay_type = "overlay.full"
        else:
            overlay_type = "overlay.simple"

        self.item_editor = PanelModifyItemSettings(
            self, self.presenter, self.config, alt_parent=self.view, overlay_type=overlay_type, **information
        )
        self.item_editor.Centre()
        self.item_editor.Show()

    def on_action_tools(self, evt):

        menu = wx.Menu()

        menu_action_create_blank_document = make_menu_item(
            parent=menu,
            text="Create blank COMPARISON document",
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
        self.data_handling.create_new_document_of_type(document_type="overlay")

    def generate_overlay_plot_list(self):

        item_list = []
        for key in self.overlay_data:
            method = key.split(": ")[0]
            item_list.append([method, key])

        return item_list

    def on_add_to_document(self, evt):
        """Add data to document"""
        from gui_elements.dialog_review_editor import DialogReviewEditor

        # data classifiers
        stats_list = ["Mean", "Standard Deviation", "Variance", "RMSD", "RMSF", "RMSD Matrix"]
        overlay_list = [
            "Overlay (DT)",
            "Overlay (MS)",
            "Overlay (RT)",
            "Butterfly (DT)",
            "Butterfly (MS)",
            "Butterfly (RT)",
            "Subtract (DT)",
            "Subtract (MS)",
            "Subtract (RT)",
            "Waterfall (DT)",
            "Waterfall (MS)",
            "Waterfall (RT)",
            "Mask",
            "Transparent",
            "Grid (2->1)",
            "Grid (n x n)",
            "RGB",
        ]

        # if the list is empty, notify the user
        if not self.overlay_data:
            raise MessageError(
                "Clipboard is empty",
                "There are no items in the clipboard."
                + " Please plot something first before adding it to the document",
            )
        # get document
        document = self.data_handling._get_document_of_type("Type: Comparison")
        if document is None:
            logger.error("Please select valid document title and path")
            return
        document_title = document.title

        # collect list of items in the clipboard
        item_list = self.generate_overlay_plot_list()
        dlg = DialogReviewEditor(self, self.presenter, self.config, item_list, review_type="overlay")
        dlg.ShowModal()
        add_to_document_list = dlg.output_list

        # add data to document while also removing it from the clipboard object
        for key in add_to_document_list:
            data = self.overlay_data.pop(key)
            for method in stats_list:
                if key.startswith(method):
                    self.data_handling.set_overlay_data([document_title, "Statistical", key], data)
                    break
            for method in overlay_list:
                if key.startswith(method):
                    self.data_handling.set_overlay_data([document_title, "Overlay", key], data)
                    break

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
        from gui_elements.dialog_color_picker import DialogColorPicker

        if item_id is not None:
            self.peaklist.item_id = item_id

        if item_id is None:
            item_id = self.peaklist.item_id

        if item_id is None:
            return

        dlg = DialogColorPicker(self, self.config.customColors)
        if dlg.ShowModal() == "ok":
            color_255, color_1, font_color = dlg.GetChosenColour()
            self.config.customColors = dlg.GetCustomColours()
            self.on_update_value_in_peaklist(item_id, "color", [color_255, color_1, font_color])

            # update document
            self.on_update_document(evt=None)

            if give_value:
                return color_255

    def on_update_value_in_peaklist(self, item_id, value_type, value):
        if value_type == "color":
            color_255, color_1, font_color = value
            self.peaklist.SetItemBackgroundColour(item_id, color_255)
            self.peaklist.SetStringItem(item_id, self.config.overlay_list_col_names["color"], str(color_1))
            self.peaklist.SetItemTextColour(item_id, font_color)
        elif value_type == "color_text":
            self.peaklist.SetItemBackgroundColour(item_id, value)
            self.peaklist.SetStringItem(
                item_id, self.config.overlay_list_col_names["color"], str(convert_rgb_255_to_1(value))
            )
            self.peaklist.SetItemTextColour(item_id, get_font_color(value, return_rgb=True))

    def on_overlay(self, evt):
        """Dispatch function"""
        item_list = self.get_selected_items()

        editor_type = self.dataset_type_choice.GetStringSelection()
        method = self.overlay_method_choice.GetStringSelection()

        if editor_type == "Chromatograms":
            self.on_overlay_chromatogram(item_list, method)
        elif editor_type == "Mobilograms":
            self.on_overlay_mobilogram(item_list, method)
        elif editor_type == "Heatmaps":
            self.on_overlay_heatmap(item_list, method)
        elif editor_type == "Mass spectra":
            self.on_overlay_mass_spectra(item_list, method)
        else:
            logger.error("Method not implemented yet")

    def on_overlay_heatmap(self, item_list, method):
        if method == "Transparent":
            overlay_data = self.data_visualisation.on_overlay_heatmap_transparent(
                item_list, plot=None, plot_obj=self.plot_window
            )
        elif method == "Mask":
            overlay_data = self.data_visualisation.on_overlay_heatmap_mask(
                item_list, plot=None, plot_obj=self.plot_window
            )
        elif method in ["Mean", "Standard Deviation", "Variance"]:
            overlay_data = self.data_visualisation.on_overlay_heatmap_statistical(
                item_list, method, plot=None, plot_obj=self.plot_window
            )
        elif method == "RGB":
            overlay_data = self.data_visualisation.on_overlay_heatmap_rgb(
                item_list, plot=None, plot_obj=self.plot_window
            )
        elif method == "Grid (n x n)":
            overlay_data = self.data_visualisation.on_overlay_heatmap_grid_nxn(
                item_list, plot=None, plot_obj=self.plot_window
            )
        elif method == "RMSD Matrix":
            overlay_data = self.data_visualisation.on_overlay_heatmap_rmsd_matrix(
                item_list, plot=None, plot_obj=self.plot_window
            )
        elif method == "RMSD":
            overlay_data = self.data_visualisation.on_overlay_heatmap_rmsd(
                item_list, plot=None, plot_obj=self.plot_window
            )
        elif method == "RMSF":
            overlay_data = self.data_visualisation.on_overlay_heatmap_rmsf(
                item_list, plot=None, plot_obj=self.plot_window
            )
        elif method == "Grid (2->1)":
            overlay_data = self.data_visualisation.on_overlay_heatmap_2to1(
                item_list, plot=None, plot_obj=self.plot_window
            )
        else:
            logger.error("Method not implemented yet")
            return

        self.overlay_data[overlay_data.pop("name")] = overlay_data.pop("data")

    def on_overlay_mass_spectra(self, item_list, method):
        if method == "Overlay":
            overlay_data = self.data_visualisation.on_overlay_spectrum_overlay(
                item_list,
                "mass_spectra",
                plot=None,
                plot_obj=self.plot_window,
                normalize_dataset=self.normalize_1D_check.GetValue(),
            )
        elif method == "Butterfly (n=2)":
            overlay_data = self.data_visualisation.on_overlay_spectrum_butterfly(
                item_list,
                "mass_spectra",
                plot=None,
                plot_obj=self.plot_window,
                normalize_dataset=self.normalize_1D_check.GetValue(),
            )
        elif method == "Subtract (n=2)":
            overlay_data = self.data_visualisation.on_overlay_spectrum_subtract(
                item_list,
                "mass_spectra",
                plot=None,
                plot_obj=self.plot_window,
                normalize_dataset=self.normalize_1D_check.GetValue(),
            )
        elif method == "Waterfall":
            overlay_data = self.data_visualisation.on_overlay_spectrum_waterfall(
                item_list,
                "mass_spectra",
                plot=None,
                plot_obj=self.plot_window,
                normalize_dataset=self.normalize_1D_check.GetValue(),
            )
        else:
            logger.error("Method not implemented yet")
            return

        self.overlay_data[overlay_data.pop("name")] = overlay_data.pop("data")

    def on_overlay_mobilogram(self, item_list, method):
        if method == "Overlay":
            overlay_data = self.data_visualisation.on_overlay_spectrum_overlay(
                item_list,
                "mobilogram",
                plot=None,
                plot_obj=self.plot_window,
                normalize_dataset=self.normalize_1D_check.GetValue(),
            )
        elif method == "Butterfly (n=2)":
            overlay_data = self.data_visualisation.on_overlay_spectrum_butterfly(
                item_list,
                "mobilogram",
                plot=None,
                plot_obj=self.plot_window,
                normalize_dataset=self.normalize_1D_check.GetValue(),
            )
        elif method == "Subtract (n=2)":
            overlay_data = self.data_visualisation.on_overlay_spectrum_subtract(
                item_list,
                "mobilogram",
                plot=None,
                plot_obj=self.plot_window,
                normalize_dataset=self.normalize_1D_check.GetValue(),
            )
        elif method == "Waterfall":
            overlay_data = self.data_visualisation.on_overlay_spectrum_waterfall(
                item_list,
                "mobilogram",
                plot=None,
                plot_obj=self.plot_window,
                normalize_dataset=self.normalize_1D_check.GetValue(),
            )
        else:
            logger.error("Method not implemented yet")
            return

        self.overlay_data[overlay_data.pop("name")] = overlay_data.pop("data")

    def on_overlay_chromatogram(self, item_list, method):
        if method == "Overlay":
            overlay_data = self.data_visualisation.on_overlay_spectrum_overlay(
                item_list,
                "chromatogram",
                plot=None,
                plot_obj=self.plot_window,
                normalize_dataset=self.normalize_1D_check.GetValue(),
            )
        elif method == "Butterfly (n=2)":
            overlay_data = self.data_visualisation.on_overlay_spectrum_butterfly(
                item_list,
                "chromatogram",
                plot=None,
                plot_obj=self.plot_window,
                normalize_dataset=self.normalize_1D_check.GetValue(),
            )
        elif method == "Subtract (n=2)":
            overlay_data = self.data_visualisation.on_overlay_spectrum_subtract(
                item_list,
                "chromatogram",
                plot=None,
                plot_obj=self.plot_window,
                normalize_dataset=self.normalize_1D_check.GetValue(),
            )
        elif method == "Waterfall":
            overlay_data = self.data_visualisation.on_overlay_spectrum_waterfall(
                item_list,
                "chromatogram",
                plot=None,
                plot_obj=self.plot_window,
                normalize_dataset=self.normalize_1D_check.GetValue(),
            )
        else:
            logger.error("Method not implemented yet")
            return

        self.overlay_data[overlay_data.pop("name")] = overlay_data.pop("data")

    def on_populate_item_list(self, evt):
        """Populate table based on the dataset selection"""
        editor_dict = {
            "Heatmaps": "heatmap",
            "Chromatograms": "chromatogram",
            "Mobilograms": "mobilogram",
            "Mass spectra": "mass_spectra",
        }
        dataset_type = editor_dict[self.dataset_type_choice.GetStringSelection()]

        item_list = self.data_handling.generate_item_list(dataset_type)
        self.peaklist.DeleteAllItems()
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
                    str(round_rgb(convert_rgb_255_to_1(color))),
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
            self.peaklist.SetItemTextColour(item_count, get_font_color(color, return_rgb=True))

        self.on_toggle_table_columns(dataset_type)
        self.on_populate_overlay_methods(dataset_type)

        if evt is not None:
            evt.Skip()

    def on_toggle_table_columns(self, data_type):
        """Toggle table columns based on the dataset type"""

        show_columns = [
            "check",
            "dataset_name",
            "dataset_type",
            "document",
            "shape",
            "color",
            "colormap",
            "alpha",
            "mask",
            "label",
            "min_threshold",
            "max_threshold",
            "processed",
            "order",
        ]
        if data_type in ["mass_spectra", "chromatogram", "mobilogram"]:
            show_columns = [
                "check",
                "dataset_name",
                "dataset_type",
                "document",
                "shape",
                "color",
                "label",
                "processed",
                "order",
            ]

        for column_id in self._peaklist_peaklist:
            width = self._peaklist_peaklist[column_id]["width"]
            if self._peaklist_peaklist[column_id]["tag"] not in show_columns:
                width = 0
            self.peaklist.SetColumnWidth(column_id, width)

    def on_populate_overlay_methods(self, data_type):
        """Re-populate method selection"""
        # get current choice
        current_choice = self.overlay_method_choice.GetStringSelection()

        # clear choices
        self.overlay_method_choice.Clear()

        choices = self.overlay_methods_2D
        choice = self.config.overlayMethod
        if data_type in ["mass_spectra", "chromatogram", "mobilogram"]:
            choices = self.overlay_methods_1D
            choice = "Overlay"

        # in case current method is in list of choices
        if current_choice in choices:
            choice = current_choice

        # repopulate and set selection
        self.overlay_method_choice.SetItems(choices)
        self.overlay_method_choice.SetStringSelection(choice)

    def get_selected_items(self):
        item_count = self.peaklist.GetItemCount()

        # generate list of document_title and dataset_name
        item_list = []
        for item_id in range(item_count):
            information = self.on_get_item_information(item_id)
            if information["select"]:
                item_list.append(information)

        return item_list

    def on_get_item_information(self, item_id):
        information = self.peaklist.on_get_item_information(item_id)

        # add additional data
        information["color_255to1"] = convert_rgb_255_to_1(information["color"], decimals=3)
        information["color"] = list(information["color"])[0:3]
        information["item_name"] = "{}::{}::{}".format(
            information["dataset_name"], information["dataset_type"], information["document"]
        )

        return information
