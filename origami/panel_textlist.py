# Standard library imports
import re
import logging
from enum import IntEnum

# Third-party imports
import wx

# Local imports
from origami.ids import ID_addNewOverlayDoc
from origami.ids import ID_ionPanel_edit_all
from origami.ids import ID_textPanel_editItem
from origami.ids import ID_textPanel_check_all
from origami.ids import ID_textPanel_clear_all
from origami.ids import ID_textPanel_delete_all
from origami.ids import ID_load_multiple_text_2D
from origami.ids import ID_textPanel_assignColor
from origami.ids import ID_textPanel_show_heatmap
from origami.ids import ID_textPanel_annotate_mask
from origami.ids import ID_textPanel_edit_selected
from origami.ids import ID_textPanel_annotate_alpha
from origami.ids import ID_textPanel_check_selected
from origami.ids import ID_textPanel_clear_selected
from origami.ids import ID_textPanel_delete_selected
from origami.ids import ID_textPanel_show_mobilogram
from origami.ids import ID_textPanel_delete_rightClick
from origami.ids import ID_textPanel_show_chromatogram
from origami.ids import ID_textPanel_changeColormapBatch
from origami.ids import ID_textPanel_show_process_heatmap
from origami.ids import ID_textPanel_annotate_charge_state
from origami.ids import ID_textPanel_annotate_max_threshold
from origami.ids import ID_textPanel_annotate_min_threshold
from origami.ids import ID_textPanel_changeColorBatch_color
from origami.ids import ID_textPanel_changeColorBatch_palette
from origami.ids import ID_textPanel_changeColorBatch_colormap
from origami.styles import make_tooltip
from origami.styles import make_menu_item
from origami.utils.check import isempty
from origami.utils.color import get_font_color
from origami.utils.color import convert_rgb_1_to_255
from origami.config.config import CONFIG
from origami.config.environment import ENV
from origami.gui_elements.dialog_ask import DialogAsk
from origami.gui_elements.panel_base import TablePanelBase
from origami.gui_elements.misc_dialogs import DialogBox

LOGGER = logging.getLogger(__name__)


class TableColumnIndex(IntEnum):
    check = 0
    start = 1
    end = 2
    charge = 3
    color = 4
    colormap = 5
    alpha = 6
    mask = 7
    label = 8
    shape = 9
    document = 10
    key = 11


class PanelTextlist(TablePanelBase):
    KEYWORD_ALIAS = {"cmap": "colormap"}
    TABLE_DICT = {
        0: {
            "name": "",
            "tag": "check",
            "type": "bool",
            "order": 0,
            "id": wx.NewIdRef(),
            "show": True,
            "width": 25,
            "hidden": True,
        },
        1: {
            "name": "min (x)",
            "tag": "start",
            "type": "float",
            "order": 1,
            "id": wx.NewIdRef(),
            "show": True,
            "width": 65,
        },
        2: {
            "name": "max (x)",
            "tag": "end",
            "type": "float",
            "order": 2,
            "id": wx.NewIdRef(),
            "show": True,
            "width": 65,
        },
        3: {"name": "z", "tag": "charge", "type": "int", "order": 3, "id": wx.NewIdRef(), "show": True, "width": 25},
        4: {
            "name": "color",
            "tag": "color",
            "type": "color",
            "order": 4,
            "id": wx.NewIdRef(),
            "show": True,
            "width": 60,
        },
        5: {
            "name": "colormap",
            "tag": "colormap",
            "type": "str",
            "order": 5,
            "id": wx.NewIdRef(),
            "show": True,
            "width": 70,
        },
        6: {
            "name": "\N{GREEK SMALL LETTER ALPHA}",
            "tag": "alpha",
            "type": "float",
            "order": 6,
            "id": wx.NewIdRef(),
            "show": True,
            "width": 35,
        },
        7: {"name": "mask", "tag": "mask", "type": "float", "order": 7, "id": wx.NewIdRef(), "show": True, "width": 40},
        8: {"name": "label", "tag": "label", "type": "str", "order": 8, "id": wx.NewIdRef(), "show": True, "width": 50},
        9: {"name": "shape", "tag": "shape", "type": "str", "order": 9, "id": wx.NewIdRef(), "show": True, "width": 70},
        10: {
            "name": "document",
            "tag": "document",
            "type": "str",
            "order": 10,
            "id": wx.NewIdRef(),
            "show": True,
            "width": 100,
        },
        11: {
            "name": "key",
            "tag": "key",
            "type": "str",
            "order": 11,
            "id": wx.NewIdRef(),
            "show": True,
            "width": 0,
            "hidden": True,
        },
    }
    TABLE_COLUMN_INDEX = TableColumnIndex

    def __init__(self, parent, icons, presenter):
        TablePanelBase.__init__(self, parent, icons, presenter)

        self.addToDocument = False
        self.normalize1D = True
        self.plotAutomatically = True
        self.item_editor = None

        # add a couple of accelerators
        accelerators = [
            (wx.ACCEL_NORMAL, ord("C"), ID_textPanel_assignColor),
            (wx.ACCEL_NORMAL, ord("E"), ID_textPanel_editItem),
            (wx.ACCEL_NORMAL, ord("H"), ID_textPanel_show_heatmap),
            (wx.ACCEL_NORMAL, ord("M"), ID_textPanel_show_mobilogram),
            (wx.ACCEL_NORMAL, ord("S"), ID_textPanel_check_selected),
            (wx.ACCEL_NORMAL, ord("X"), ID_textPanel_check_all),
            (wx.ACCEL_NORMAL, wx.WXK_DELETE, ID_textPanel_delete_rightClick),
        ]
        self.SetAcceleratorTable(wx.AcceleratorTable(accelerators))

        wx.EVT_MENU(self, ID_textPanel_editItem, self.on_open_editor)
        wx.EVT_MENU(self, ID_textPanel_assignColor, self.on_assign_color)
        wx.EVT_MENU(self, ID_textPanel_show_heatmap, self.on_plot)
        wx.EVT_MENU(self, ID_textPanel_show_mobilogram, self.on_plot)
        wx.EVT_MENU(self, ID_textPanel_check_selected, self.on_check_selected)
        wx.EVT_MENU(self, ID_textPanel_delete_rightClick, self.on_delete_item)

    def setup_handling_and_processing(self):
        self.data_processing = self.view.data_processing
        self.data_handling = self.view.data_handling
        self.data_visualisation = self.view.data_visualisation
        self.document_tree = self.presenter.view.panelDocuments.documents

    def on_double_click_on_item(self, evt):
        if self.peaklist.item_id != -1:
            if not self.item_editor:
                self.on_open_editor(evt=None)
            else:
                self.item_editor.onUpdateGUI(self.on_get_item_information(self.peaklist.item_id))

    def on_add_blank_document_overlay(self, evt):
        self.presenter.onAddBlankDocument(evt=None, document_type="overlay")

    def on_open_info_panel(self, evt):
        LOGGER.error("This function is not implemented yet")

    # noinspection DuplicatedCode
    def make_toolbar(self):

        add_btn = wx.BitmapButton(
            self, -1, self.icons.iconsLib["add16"], size=(18, 18), style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL
        )
        add_btn.SetToolTip(make_tooltip("Add..."))

        remove_btn = wx.BitmapButton(
            self, -1, self.icons.iconsLib["remove16"], size=(18, 18), style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL
        )
        remove_btn.SetToolTip(make_tooltip("Remove..."))

        annotate_btn = wx.BitmapButton(
            self, -1, self.icons.iconsLib["annotate16"], size=(18, 18), style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL
        )
        annotate_btn.SetToolTip(make_tooltip("Annotate..."))

        process_btn = wx.BitmapButton(
            self, -1, self.icons.iconsLib["process16"], size=(18, 18), style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL
        )
        process_btn.SetToolTip(make_tooltip("Process..."))

        save_btn = wx.BitmapButton(
            self, -1, self.icons.iconsLib["save16"], size=(18, 18), style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL
        )
        save_btn.SetToolTip(make_tooltip("Save..."))

        vertical_line_1 = wx.StaticLine(self, -1, style=wx.LI_VERTICAL)

        info_btn = wx.BitmapButton(
            self, -1, self.icons.iconsLib["info16"], size=(18, 18), style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL
        )
        info_btn.SetToolTip(make_tooltip("Information..."))

        # bind events
        self.Bind(wx.EVT_BUTTON, self.menu_add_tools, add_btn)
        self.Bind(wx.EVT_BUTTON, self.menu_remove_tools, remove_btn)
        self.Bind(wx.EVT_BUTTON, self.menu_process_tools, process_btn)
        self.Bind(wx.EVT_BUTTON, self.menu_save_tools, save_btn)
        self.Bind(wx.EVT_BUTTON, self.menu_annotate_tools, annotate_btn)
        self.Bind(wx.EVT_BUTTON, self.on_open_info_panel, info_btn)

        # button grid
        toolbar = wx.BoxSizer(wx.HORIZONTAL)
        toolbar.Add(add_btn, 0, wx.ALIGN_CENTER)
        toolbar.Add(remove_btn, 0, wx.ALIGN_CENTER)
        toolbar.Add(annotate_btn, 0, wx.ALIGN_CENTER)
        toolbar.Add(process_btn, 0, wx.ALIGN_CENTER)
        toolbar.Add(save_btn, 0, wx.ALIGN_CENTER)
        toolbar.AddSpacer(5)
        toolbar.Add(vertical_line_1, 0, wx.EXPAND)
        toolbar.AddSpacer(5)
        toolbar.Add(info_btn, 0, wx.ALIGN_CENTER)

        return toolbar

    def on_menu_item_right_click(self, evt):

        # Make bindings
        self.Bind(wx.EVT_MENU, self.on_plot, id=ID_textPanel_show_chromatogram)
        self.Bind(wx.EVT_MENU, self.on_plot, id=ID_textPanel_show_mobilogram)
        self.Bind(wx.EVT_MENU, self.on_plot, id=ID_textPanel_show_heatmap)
        self.Bind(wx.EVT_MENU, self.on_plot, id=ID_textPanel_show_process_heatmap)
        self.Bind(wx.EVT_MENU, self.on_delete_item, id=ID_textPanel_delete_rightClick)
        self.Bind(wx.EVT_MENU, self.on_open_editor, id=ID_textPanel_editItem)
        self.Bind(wx.EVT_MENU, self.on_assign_color, id=ID_textPanel_assignColor)

        self.peaklist.item_id = evt.GetIndex()
        menu = wx.Menu()
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_textPanel_show_chromatogram,
                text="Show chromatogram",
                bitmap=self.icons.iconsLib["chromatogram_16"],
            )
        )
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_textPanel_show_mobilogram,
                text="Show mobilogram\tM",
                bitmap=self.icons.iconsLib["mobilogram_16"],
            )
        )
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_textPanel_show_heatmap,
                text="Show heatmap\tH",
                bitmap=self.icons.iconsLib["heatmap_16"],
            )
        )
        menu.Append(ID_textPanel_show_process_heatmap, "Process and show heatmap")
        menu.AppendSeparator()
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_textPanel_assignColor,
                text="Assign new color\tC",
                bitmap=self.icons.iconsLib["color_panel_16"],
            )
        )
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_textPanel_editItem,
                text="Edit file information\tE",
                bitmap=self.icons.iconsLib["info16"],
            )
        )
        menu.AppendSeparator()
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_textPanel_delete_rightClick,
                text="Remove item\tDelete",
                bitmap=self.icons.iconsLib["bin16"],
            )
        )
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def menu_annotate_tools(self, evt):
        self.Bind(wx.EVT_MENU, self.on_change_item_parameter, id=ID_textPanel_annotate_charge_state)
        self.Bind(wx.EVT_MENU, self.on_change_item_parameter, id=ID_textPanel_annotate_alpha)
        self.Bind(wx.EVT_MENU, self.on_change_item_parameter, id=ID_textPanel_annotate_mask)
        self.Bind(wx.EVT_MENU, self.on_change_item_parameter, id=ID_textPanel_annotate_min_threshold)
        self.Bind(wx.EVT_MENU, self.on_change_item_parameter, id=ID_textPanel_annotate_max_threshold)
        self.Bind(wx.EVT_MENU, self.on_change_item_color_batch, id=ID_textPanel_changeColorBatch_color)
        self.Bind(wx.EVT_MENU, self.on_change_item_color_batch, id=ID_textPanel_changeColorBatch_palette)
        self.Bind(wx.EVT_MENU, self.on_change_item_color_batch, id=ID_textPanel_changeColorBatch_colormap)
        self.Bind(wx.EVT_MENU, self.on_change_item_colormap, id=ID_textPanel_changeColormapBatch)

        menu = wx.Menu()
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_textPanel_annotate_charge_state,
                text="Assign charge state (selected)",
                bitmap=self.icons.iconsLib["assign_charge_16"],
            )
        )
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_textPanel_annotate_alpha,
                text="Assign transparency value (selected)",
                bitmap=self.icons.iconsLib["transparency_16"],
            )
        )
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_textPanel_annotate_mask,
                text="Assign mask value (selected)",
                bitmap=self.icons.iconsLib["mask_16"],
            )
        )
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_textPanel_annotate_min_threshold,
                text="Assign minimum threshold (selected)",
                bitmap=self.icons.iconsLib["min_threshold_16"],
            )
        )
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_textPanel_annotate_max_threshold,
                text="Assign maximum threshold (selected)",
                bitmap=self.icons.iconsLib["max_threshold_16"],
            )
        )
        menu.AppendSeparator()
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_textPanel_changeColorBatch_color,
                text="Assign new color using color picker (selected)",
                bitmap=self.icons.iconsLib["color_panel_16"],
            )
        )
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_textPanel_changeColorBatch_palette,
                text="Assign new color using color palette (selected)",
                bitmap=self.icons.iconsLib["blank_16"],
            )
        )
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_textPanel_changeColorBatch_colormap,
                text="Assign new color using colormap (selected)",
                bitmap=self.icons.iconsLib["blank_16"],
            )
        )
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_textPanel_changeColormapBatch,
                text="Assign new colormap (selected)",
                bitmap=self.icons.iconsLib["randomize_16"],
            )
        )

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def menu_add_tools(self, evt):
        self.Bind(wx.EVT_MENU, self.presenter.onAddBlankDocument, id=ID_addNewOverlayDoc)
        self.Bind(wx.EVT_MENU, self.on_add_blank_document_overlay, id=ID_addNewOverlayDoc)

        menu = wx.Menu()
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_load_multiple_text_2D,
                text="Add files\tCtrl+W",
                bitmap=self.icons.iconsLib["file_csv_16"],
            )
        )
        menu.AppendSeparator()
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_addNewOverlayDoc,
                text="Create blank COMPARISON document\tAlt+D",
                bitmap=self.icons.iconsLib["new_document_16"],
            )
        )
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def menu_remove_tools(self, evt):

        # Make bindings
        self.Bind(wx.EVT_MENU, self.on_delete_all, id=ID_textPanel_delete_all)
        self.Bind(wx.EVT_MENU, self.on_delete_selected, id=ID_textPanel_delete_selected)
        self.Bind(wx.EVT_MENU, self.peaklist.on_clear_table_selected, id=ID_textPanel_clear_all)
        self.Bind(wx.EVT_MENU, self.peaklist.on_clear_table_all, id=ID_textPanel_clear_selected)

        menu = wx.Menu()
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_textPanel_clear_selected,
                text="Remove from list (selected)",
                bitmap=self.icons.iconsLib["clear_16"],
            )
        )
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_textPanel_clear_all,
                text="Remove from list (all)",
                bitmap=self.icons.iconsLib["clear_16"],
            )
        )

        menu.AppendSeparator()
        menu.AppendSeparator()
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_textPanel_delete_selected,
                text="Delete documents (selected)",
                bitmap=self.icons.iconsLib["bin16"],
            )
        )
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                id=ID_textPanel_delete_all,
                text="Delete documents (all)",
                bitmap=self.icons.iconsLib["bin16"],
            )
        )

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def menu_process_tools(self, evt):

        menu = wx.Menu()
        menu_action_process_heatmap = make_menu_item(parent=menu, text="Process heatmap data (selected)")
        menu.AppendItem(menu_action_process_heatmap)

        # bind events
        self.Bind(wx.EVT_MENU, self.on_process_heatmap_selected, menu_action_process_heatmap)

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def menu_save_tools(self, evt):

        menu = wx.Menu()
        menu_action_save_chromatogram = make_menu_item(parent=menu, text="Save figure(s) as chromatogram (selected)")
        menu.AppendItem(menu_action_save_chromatogram)

        menu_action_save_mobilogram = make_menu_item(parent=menu, text="Save figure(s) as mobilogram (selected)")
        menu.AppendItem(menu_action_save_mobilogram)

        menu_action_save_heatmap = make_menu_item(parent=menu, text="Save figure(s) as heatmap (selected)")
        menu.AppendItem(menu_action_save_heatmap)

        menu_action_save_waterfall = make_menu_item(parent=menu, text="Save figure(s) as waterfall (selected)")
        menu.AppendItem(menu_action_save_waterfall)

        menu.AppendSeparator()
        menu_action_save_data_chromatogram = make_menu_item(parent=menu, text="Save chromatographic data (selected)")
        menu.AppendItem(menu_action_save_data_chromatogram)

        menu_action_save_data_mobilogram = make_menu_item(parent=menu, text="Save mobilogram data (selected)")
        menu.AppendItem(menu_action_save_data_mobilogram)

        menu_action_save_data_heatmap = make_menu_item(parent=menu, text="Save heatmap data (selected)")
        menu.AppendItem(menu_action_save_data_heatmap)

        # bind events
        self.Bind(wx.EVT_MENU, self.on_save_figures_chromatogram, menu_action_save_chromatogram)
        self.Bind(wx.EVT_MENU, self.on_save_figures_mobilogram, menu_action_save_mobilogram)
        self.Bind(wx.EVT_MENU, self.on_save_figures_heatmap, menu_action_save_heatmap)
        self.Bind(wx.EVT_MENU, self.on_save_figures_waterfall, menu_action_save_waterfall)

        self.Bind(wx.EVT_MENU, self.on_save_data_chromatogram, menu_action_save_data_chromatogram)
        self.Bind(wx.EVT_MENU, self.on_save_data_mobilogram, menu_action_save_data_mobilogram)
        self.Bind(wx.EVT_MENU, self.on_save_data_heatmap, menu_action_save_data_heatmap)

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def get_selected_items(self):
        all_eic_datasets = ["Drift time (2D)", "Drift time (2D, processed)"]

        item_count = self.peaklist.GetItemCount()

        # generate list of document_title and dataset_name
        process_list = []
        for item_id in range(item_count):
            information = self.on_get_item_information(item_id)
            if information["select"]:
                for dataset_type in all_eic_datasets:
                    document_title = information["document"]
                    if document_title not in ["", None]:
                        # append raw
                        process_item = [document_title, dataset_type, None]
                        process_list.append(process_item)

        return process_list

    def on_process_heatmap_selected(self, evt):
        """Collect list of titles and dataset names and open processing panel"""
        process_list = self.get_selected_items()

        n_items = len(process_list)
        if n_items > 0:
            # open-up panel
            self.document_tree.on_open_process_2D_settings(
                process_all=True, process_list=True, data=process_list, disable_plot=True, disable_process=False
            )

    def on_save_figures(self, plot_type):
        """Save figure(s) for selected item(s)

        Parameters
        ----------
        plot_type : str
            type of plot to be plotted
        """
        process_list = self.get_selected_items()
        self.data_handling.on_save_heatmap_figures(plot_type, process_list)

    def on_save_figures_chromatogram(self, evt):
        self.on_save_figures("chromatogram")

    def on_save_figures_mobilogram(self, evt):
        self.on_save_figures("mobilogram")

    def on_save_figures_heatmap(self, evt):
        self.on_save_figures("heatmap")

    def on_save_figures_waterfall(self, evt):
        self.on_save_figures("waterfall")

    def on_save_data(self, data_type):
        """Save figure(s) for selected item(s)

        Parameters
        ----------
        data_type : str
            type of data to be saved
        """
        process_list = self.get_selected_items()
        self.data_handling.on_save_heatmap_data(data_type, process_list)

    def on_save_data_chromatogram(self, evt):
        self.on_save_data("chromatogram")

    def on_save_data_mobilogram(self, evt):
        self.on_save_data("mobilogram")

    def on_save_data_heatmap(self, evt):
        self.on_save_data("heatmap")

    # def on_change_item_colormap(self, evt):
    #     # get number of checked items
    #     check_count = 0
    #     for row in range(self.peaklist.GetItemCount()):
    #         if self.peaklist.IsChecked(index=row):
    #             check_count += 1
    #
    #     if check_count > len(CONFIG.narrowCmapList):
    #         colormaps = CONFIG.narrowCmapList
    #     else:
    #         colormaps = CONFIG.narrowCmapList + CONFIG.cmaps2
    #
    #     for row in range(self.peaklist.GetItemCount()):
    #         if self.peaklist.IsChecked(index=row):
    #             self.peaklist.item_id = row
    #             colormap = colormaps[row]
    #             self.peaklist.SetItem(row, CONFIG.textlistColNames["colormap"], str(colormap))
    #
    #             # update document
    #             try:
    #                 self.on_update_document(evt=None)
    #             except TypeError:
    #                 print("Please select item")

    def on_change_item_color_batch(self, evt):
        # get number of checked items
        check_count = 0
        for row in range(self.peaklist.GetItemCount()):
            if self.peaklist.IsChecked(index=row):
                check_count += 1

        if evt.GetId() == ID_textPanel_changeColorBatch_palette:
            colors = self.presenter.view.panelPlots.on_change_color_palette(
                None, n_colors=check_count, return_colors=True
            )
        elif evt.GetId() == ID_textPanel_changeColorBatch_color:
            color = self.on_get_color(None)
            colors = [color] * check_count
        else:
            colors = self.presenter.view.panelPlots.on_get_colors_from_colormap(n_colors=check_count)

        check_count = 0
        for row in range(self.peaklist.GetItemCount()):
            self.peaklist.item_id = row
            if self.peaklist.IsChecked(index=row):
                color = colors[check_count]
                self.peaklist.SetItemBackgroundColour(row, convert_rgb_1_to_255(color))
                self.peaklist.SetItemTextColour(row, get_font_color(convert_rgb_1_to_255(color), return_rgb=True))
                check_count += 1

            self.on_update_document(evt=None)

    def on_change_item_parameter(self, evt):
        """ Iterate over list to assign charge state """

        rows = self.peaklist.GetItemCount()
        if rows == 0:
            return

        if evt.GetId() == ID_textPanel_annotate_charge_state:
            static_text = "Assign charge state to selected items."
            ask_kwargs = {"static_text": static_text, "value_text": "", "validator": "integer", "keyword": "charge"}

        elif evt.GetId() == ID_textPanel_annotate_alpha:
            static_text = (
                "Assign new transparency value to selected items \n" + "Typical transparency values: 0.5\nRange 0-1"
            )
            ask_kwargs = {"static_text": static_text, "value_text": 0.5, "validator": "float", "keyword": "alpha"}

        elif evt.GetId() == ID_textPanel_annotate_mask:
            static_text = "Assign new mask value to selected items \nTypical mask values: 0.25\nRange 0-1"
            ask_kwargs = {"static_text": static_text, "value_text": 0.25, "validator": "float", "keyword": "mask"}

        elif evt.GetId() == ID_textPanel_annotate_min_threshold:
            static_text = "Assign minimum threshold value to selected items \nTypical mask values: 0.0\nRange 0-1"
            ask_kwargs = {
                "static_text": static_text,
                "value_text": 0.0,
                "validator": "float",
                "keyword": "min_threshold",
            }

        elif evt.GetId() == ID_textPanel_annotate_max_threshold:
            static_text = "Assign maximum threshold value to selected items \nTypical mask values: 1.0\nRange 0-1"
            ask_kwargs = {
                "static_text": static_text,
                "value_text": 1.0,
                "validator": "float",
                "keyword": "max_threshold",
            }
        else:
            raise ValueError("Not sure what to do...")

        ask = DialogAsk(self, **ask_kwargs)
        ask.ShowModal()
        return_value = ask.return_value
        if return_value is None:
            LOGGER.info("Action was cancelled")
            return

        for row in range(rows):
            if self.peaklist.IsChecked(index=row):
                itemInfo = self.on_get_item_information(row)
                document = self.data_handling.on_get_document(itemInfo["document"])

                if not ask_kwargs["keyword"] in ["min_threshold", "max_threshold"]:
                    self.peaklist.SetItem(row, CONFIG.textlistColNames[ask_kwargs["keyword"]], str(return_value))

                # set value in document
                if document.got2DIMS:
                    document.IMS2D[ask_kwargs["keyword"]] = return_value
                if document.got2Dprocess:
                    document.IMS2Dprocess[ask_kwargs["keyword"]] = return_value

                self.data_handling.on_update_document(document, "no_refresh")

    def on_plot(self, evt, item_id=None):
        """Plot data"""

        if item_id is not None:
            self.peaklist.item_id = item_id

        if self.peaklist.item_id is None:
            return

        item_info = self.on_get_item_information(self.peaklist.item_id)

        try:
            document_title = item_info["document"]
            document = ENV[document_title]

            # get data
            data = document.IMS2D
        except Exception:
            document_title, ion_title = re.split(": ", item_info["document"])
            document = ENV[document_title]
            try:
                data = document.IMS2DcompData[ion_title]
            except KeyError:
                try:
                    data = document.IMS2Dions[ion_title]
                except Exception:
                    return

        if evt is not None:
            evtID = evt.GetId()
        else:
            evtID = evt

        if evtID == ID_textPanel_show_mobilogram:
            xvals = data["yvals"]  # normally this would be the y-axis
            yvals = data["yvals1D"]
            xlabels = data["ylabels"]  # normally this would be x-axis label
            self.presenter.view.panelPlots.on_plot_1D(xvals, yvals, xlabels, set_page=True)

        elif evtID == ID_textPanel_show_chromatogram:
            xvals = data["xvals"]
            yvals = data["yvalsRT"]
            xlabels = data["xlabels"]  # normally this would be x-axis label
            self.presenter.view.panelPlots.on_plot_RT(xvals, yvals, xlabels, set_page=True)

        else:
            # Extract 2D data from the document
            zvals, xvals, xlabel, yvals, ylabel, cmap = self.presenter.get2DdataFromDictionary(
                dictionary=data, dataType="plot", compact=False
            )

            if isempty(xvals) or isempty(yvals) or xvals == "" or yvals == "":
                msg1 = "Missing x- and/or y-axis labels. Cannot continue!"
                msg2 = "Add x- and/or y-axis labels to each file before continuing!"
                msg = "\n".join([msg1, msg2])
                DialogBox(title="Missing data", msg=msg, kind="Error")
                return

            # Process data
            # TODO: this function is temporarily disabled! Needs to be fixed before next release
            if evtID == ID_textPanel_show_process_heatmap:
                pass
                # zvals = self.presenter.process2Ddata(zvals=zvals.copy(), return_data=True)

            self.presenter.view.panelPlots.on_plot_2D(
                zvals, xvals, yvals, xlabel, ylabel, cmap, override=True, set_page=True
            )

    def on_check_existing(self, fileName):
        currentItems = self.peaklist.GetItemCount() - 1
        while currentItems >= 0:
            itemInfo = self.on_get_item_information(currentItems)
            if itemInfo["document"] == fileName:
                LOGGER.info("File {} already in the table - skipping".format(itemInfo["document"]))
                currentItems = 0
                return True
            currentItems -= 1
        return False

    def on_get_item_information(self, item_id, return_list=False):
        information = self.peaklist.on_get_item_information(item_id)

        #         document = self.data_handling.on_get_document(information["document"])
        # check whether the ion has any previous information
        min_threshold, max_threshold = 0, 1
        #         if document:
        #             try:
        #                 min_threshold = document.IMS2D.get("min_threshold", 0)
        #                 max_threshold = document.IMS2D.get("max_threshold", 1)
        #             except AttributeError:
        #                 min_threshold = document.IMS2Dprocess.get("min_threshold", 0)
        #                 max_threshold = document.IMS2Dprocess.get("max_threshold", 1)

        information["min_threshold"] = min_threshold
        information["max_threshold"] = max_threshold

        return information

    def on_update_document(self, evt, itemInfo=None):
        # TODO: fix this so document data is updated

        # get item info
        if itemInfo is None:
            itemInfo = self.on_get_item_information(self.peaklist.item_id)

        keywords = ["color", "colormap", "alpha", "mask", "label", "min_threshold", "max_threshold", "charge", "cmap"]

        # get item

    #         try:
    #             document = ENV[itemInfo["document"]]
    #             for keyword in keywords:
    #                 keyword_name = self.KEYWORD_ALIAS.get(keyword, keyword)
    #                 if document.got2DIMS:
    #                     document.IMS2D[keyword] = itemInfo[keyword_name]
    #                 if document.got2Dprocess:
    #                     document.IMS2Dprocess[keyword] = itemInfo[keyword_name]
    #         except Exception as err:
    #             LOGGER.error(err)
    #             document_title, ion_title = re.split(": ", itemInfo["document"])
    #             document = ENV[document_title]
    #             for keyword in keywords:
    #                 keyword_name = self.KEYWORD_ALIAS.get(keyword, keyword)
    #                 if ion_title in document.IMS2DcompData:
    #                     document.IMS2DcompData[ion_title][keyword] = itemInfo[keyword_name]
    #                 else:
    #                     document.IMS2Dions[ion_title][keyword] = itemInfo[keyword_name]
    #
    #         # Update file list
    #         self.data_handling.on_update_document(document, "no_refresh")

    def on_open_editor(self, evt):
        from origami.gui_elements.panel_modify_item_settings import PanelModifyItemSettings

        if evt is None:
            evtID = ID_textPanel_editItem
        else:
            evtID = evt.GetId()

        rows = self.peaklist.GetItemCount() - 1
        if evtID == ID_textPanel_editItem:
            if self.peaklist.item_id is None or self.peaklist.item_id < 0:
                print("Please select item in the table first.")
                return

            dlg_kwargs = self.on_get_item_information(self.peaklist.item_id)

            self.item_editor = PanelModifyItemSettings(self, self.presenter, CONFIG, **dlg_kwargs)
            self.item_editor.Centre()
            self.item_editor.Show()
        elif evtID == ID_textPanel_edit_selected:
            while rows >= 0:
                if self.peaklist.IsChecked(rows):
                    information = self.on_get_item_information(rows)

                    dlg_kwargs = {
                        "select": self.peaklist.IsChecked(rows),
                        "color": information["color"],
                        "title": information["document"],
                        "min_threshold": information["min_threshold"],
                        "max_threshold": information["max_threshold"],
                        "label": information["label"],
                        "id": rows,
                    }

                    self.item_editor = PanelModifyItemSettings(self, self.presenter, CONFIG, **dlg_kwargs)
                    self.item_editor.Show()
                rows -= 1
        elif evtID == ID_ionPanel_edit_all:
            for row in range(rows):
                information = self.on_get_item_information(row)

                dlg_kwargs = {
                    "select": self.peaklist.IsChecked(row),
                    "color": information["color"],
                    "title": information["document"],
                    "min_threshold": information["min_threshold"],
                    "max_threshold": information["max_threshold"],
                    "label": information["label"],
                    "id": row,
                }

                self.item_editor = PanelModifyItemSettings(self, self.presenter, CONFIG, **dlg_kwargs)
                self.item_editor.Show()
