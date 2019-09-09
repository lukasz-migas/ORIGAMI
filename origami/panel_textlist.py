# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import logging
import re
from ast import literal_eval

import wx
from gui_elements.dialog_ask import DialogAsk
from gui_elements.dialog_color_picker import DialogColorPicker
from gui_elements.misc_dialogs import DialogBox
from ids import ID_addNewOverlayDoc
from ids import ID_ionPanel_edit_all
from ids import ID_load_multiple_text_2D
from ids import ID_textPanel_annotate_alpha
from ids import ID_textPanel_annotate_charge_state
from ids import ID_textPanel_annotate_mask
from ids import ID_textPanel_annotate_max_threshold
from ids import ID_textPanel_annotate_min_threshold
from ids import ID_textPanel_assignColor
from ids import ID_textPanel_changeColorBatch_color
from ids import ID_textPanel_changeColorBatch_colormap
from ids import ID_textPanel_changeColorBatch_palette
from ids import ID_textPanel_changeColormapBatch
from ids import ID_textPanel_check_all
from ids import ID_textPanel_check_selected
from ids import ID_textPanel_clear_all
from ids import ID_textPanel_clear_selected
from ids import ID_textPanel_delete_all
from ids import ID_textPanel_delete_rightClick
from ids import ID_textPanel_delete_selected
from ids import ID_textPanel_edit_selected
from ids import ID_textPanel_editItem
from ids import ID_textPanel_show_chromatogram
from ids import ID_textPanel_show_heatmap
from ids import ID_textPanel_show_mobiligram
from ids import ID_textPanel_show_process_heatmap
from ids import ID_textPanel_table_alpha
from ids import ID_textPanel_table_charge
from ids import ID_textPanel_table_color
from ids import ID_textPanel_table_colormap
from ids import ID_textPanel_table_document
from ids import ID_textPanel_table_endCE
from ids import ID_textPanel_table_hideAll
from ids import ID_textPanel_table_label
from ids import ID_textPanel_table_mask
from ids import ID_textPanel_table_restoreAll
from ids import ID_textPanel_table_shape
from ids import ID_textPanel_table_startCE
from numpy import arange
from styles import ListCtrl
from styles import makeMenuItem
from styles import makeTooltip
from toolbox import removeListDuplicates
from utils.check import isempty
from utils.color import convertRGB1to255
from utils.color import convertRGB255to1
from utils.color import determineFontColor
from utils.color import randomColorGenerator
from utils.color import roundRGB
from utils.random import get_random_int

logger = logging.getLogger("origami")


class PanelTextlist(wx.Panel):
    keyword_alias = {"cmap": "colormap"}

    def __init__(self, parent, config, icons, presenter):
        wx.Panel.__init__(
            self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.Size(300, -1), style=wx.TAB_TRAVERSAL
        )

        self.view = parent
        self.config = config
        self.presenter = presenter
        self.icons = icons

        self.addToDocument = False
        self.normalize1D = True
        self.plotAutomatically = True

        self._textPanel_peaklist = {
            0: {"name": "", "tag": "check", "type": "bool"},
            1: {"name": "min (x)", "tag": "start", "type": "float"},
            2: {"name": "max (x)", "tag": "end", "type": "float"},
            3: {"name": "z", "tag": "charge", "type": "int"},
            4: {"name": "color", "tag": "color", "type": "color"},
            5: {"name": "colormap", "tag": "colormap", "type": "str"},
            6: {"name": "\N{GREEK SMALL LETTER ALPHA}", "tag": "alpha", "type": "float"},
            7: {"name": "mask", "tag": "mask", "type": "float"},
            8: {"name": "label", "tag": "label", "type": "str"},
            9: {"name": "shape", "tag": "shape", "type": "str"},
            10: {"name": "document", "tag": "document", "type": "str"},
        }

        self.item_editor = None

        self.make_panel_gui()

        # add a couple of accelerators
        accelerators = [
            (wx.ACCEL_NORMAL, ord("C"), ID_textPanel_assignColor),
            (wx.ACCEL_NORMAL, ord("E"), ID_textPanel_editItem),
            (wx.ACCEL_NORMAL, ord("H"), ID_textPanel_show_heatmap),
            (wx.ACCEL_NORMAL, ord("M"), ID_textPanel_show_mobiligram),
            (wx.ACCEL_NORMAL, ord("S"), ID_textPanel_check_selected),
            (wx.ACCEL_NORMAL, ord("X"), ID_textPanel_check_all),
            (wx.ACCEL_NORMAL, wx.WXK_DELETE, ID_textPanel_delete_rightClick),
        ]
        self.SetAcceleratorTable(wx.AcceleratorTable(accelerators))

        wx.EVT_MENU(self, ID_textPanel_editItem, self.on_open_editor)
        wx.EVT_MENU(self, ID_textPanel_assignColor, self.on_assign_color)
        wx.EVT_MENU(self, ID_textPanel_show_heatmap, self.on_plot)
        wx.EVT_MENU(self, ID_textPanel_show_mobiligram, self.on_plot)
        wx.EVT_MENU(self, ID_textPanel_check_selected, self.on_check_selected)
        wx.EVT_MENU(self, ID_textPanel_delete_rightClick, self.on_delete_item)

    def __del__(self):
        pass

    def _setup_handling_and_processing(self):
        self.data_processing = self.view.data_processing
        self.data_handling = self.view.data_handling
        self.data_visualisation = self.view.data_visualisation
        self.document_tree = self.presenter.view.panelDocuments.documents

    def make_panel_gui(self):
        """ Make panel GUI """
        # make toolbar
        toolbar = self.make_toolbar()
        self.makeListCtrl()

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.Add(toolbar, 0, wx.EXPAND, 0)
        self.main_sizer.Add(self.peaklist, 1, wx.EXPAND, 0)

        # fit layout
        self.main_sizer.Fit(self)
        self.SetSizer(self.main_sizer)
        self.SetSize((300, -1))
        self.Layout()

    def makeListCtrl(self):

        self.peaklist = ListCtrl(self, style=wx.LC_REPORT | wx.LC_VRULES, column_info=self._textPanel_peaklist)

        for item in self.config._textlistSettings:
            order = item["order"]
            name = item["name"]
            if item["show"]:
                width = item["width"]
            else:
                width = 0
            self.peaklist.InsertColumn(order, name, width=width, format=wx.LIST_FORMAT_CENTER)

        self.peaklist.Bind(wx.EVT_LEFT_DCLICK, self.on_double_click_on_item)
        self.peaklist.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.menu_right_click)
        self.peaklist.Bind(wx.EVT_LIST_COL_RIGHT_CLICK, self.menu_column_right_click)

    def on_double_click_on_item(self, evt):
        if self.peaklist.item_id != -1:
            if not self.item_editor:
                self.on_open_editor(evt=None)
            else:
                self.item_editor.onUpdateGUI(self.on_get_item_information(self.peaklist.item_id))

    def on_add_blank_document_overlay(self, evt):
        self.presenter.onAddBlankDocument(evt=None, document_type="overlay")

    def on_open_info_panel(self, evt):
        logger.error("This function is not implemented yet")

    def make_toolbar(self):

        self.add_btn = wx.BitmapButton(
            self, -1, self.icons.iconsLib["add16"], size=(18, 18), style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL
        )
        self.add_btn.SetToolTip(makeTooltip("Add..."))

        self.remove_btn = wx.BitmapButton(
            self, -1, self.icons.iconsLib["remove16"], size=(18, 18), style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL
        )
        self.remove_btn.SetToolTip(makeTooltip("Remove..."))

        self.annotate_btn = wx.BitmapButton(
            self, -1, self.icons.iconsLib["annotate16"], size=(18, 18), style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL
        )
        self.annotate_btn.SetToolTip(makeTooltip("Annotate..."))

        self.process_btn = wx.BitmapButton(
            self, -1, self.icons.iconsLib["process16"], size=(18, 18), style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL
        )
        self.process_btn.SetToolTip(makeTooltip("Process..."))

        self.save_btn = wx.BitmapButton(
            self, -1, self.icons.iconsLib["save16"], size=(18, 18), style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL
        )
        self.save_btn.SetToolTip(makeTooltip("Save..."))

        vertical_line_1 = wx.StaticLine(self, -1, style=wx.LI_VERTICAL)

        self.info_btn = wx.BitmapButton(
            self, -1, self.icons.iconsLib["info16"], size=(18, 18), style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL
        )
        self.info_btn.SetToolTip(makeTooltip("Information..."))

        # bind events
        self.Bind(wx.EVT_BUTTON, self.menu_add_tools, self.add_btn)
        self.Bind(wx.EVT_BUTTON, self.menu_remove_tools, self.remove_btn)
        self.Bind(wx.EVT_BUTTON, self.menu_process_tools, self.process_btn)
        self.Bind(wx.EVT_BUTTON, self.menu_save_tools, self.save_btn)
        self.Bind(wx.EVT_BUTTON, self.menu_annotate_tools, self.annotate_btn)
        self.Bind(wx.EVT_BUTTON, self.on_open_info_panel, self.info_btn)

        # button grid
        btn_grid_vert = wx.GridBagSizer(2, 2)
        x = 0
        n = 0
        btn_grid_vert.Add(self.add_btn, (x, n), flag=wx.ALIGN_CENTER)
        n += 1
        btn_grid_vert.Add(self.remove_btn, (x, n), flag=wx.ALIGN_CENTER)
        n += 1
        btn_grid_vert.Add(self.annotate_btn, (x, n), flag=wx.ALIGN_CENTER)
        n += 1
        btn_grid_vert.Add(self.process_btn, (x, n), flag=wx.ALIGN_CENTER)
        n += 1
        btn_grid_vert.Add(self.save_btn, (x, n), flag=wx.ALIGN_CENTER)
        n += 1
        btn_grid_vert.Add(vertical_line_1, (x, n), flag=wx.EXPAND)
        n += 1
        btn_grid_vert.Add(self.info_btn, (x, n), flag=wx.ALIGN_CENTER)

        return btn_grid_vert

    def menu_right_click(self, evt):

        # Make bindings
        self.Bind(wx.EVT_MENU, self.on_plot, id=ID_textPanel_show_chromatogram)
        self.Bind(wx.EVT_MENU, self.on_plot, id=ID_textPanel_show_mobiligram)
        self.Bind(wx.EVT_MENU, self.on_plot, id=ID_textPanel_show_heatmap)
        self.Bind(wx.EVT_MENU, self.on_plot, id=ID_textPanel_show_process_heatmap)
        self.Bind(wx.EVT_MENU, self.on_delete_item, id=ID_textPanel_delete_rightClick)
        self.Bind(wx.EVT_MENU, self.on_open_editor, id=ID_textPanel_editItem)
        self.Bind(wx.EVT_MENU, self.on_assign_color, id=ID_textPanel_assignColor)

        self.peaklist.item_id = evt.GetIndex()
        menu = wx.Menu()
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_textPanel_show_chromatogram,
                text="Show chromatogram",
                bitmap=self.icons.iconsLib["chromatogram_16"],
            )
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_textPanel_show_mobiligram,
                text="Show mobiligram\tM",
                bitmap=self.icons.iconsLib["mobiligram_16"],
            )
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_textPanel_show_heatmap,
                text="Show heatmap\tH",
                bitmap=self.icons.iconsLib["heatmap_16"],
            )
        )
        menu.Append(ID_textPanel_show_process_heatmap, "Process and show heatmap")
        menu.AppendSeparator()
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_textPanel_assignColor,
                text="Assign new color\tC",
                bitmap=self.icons.iconsLib["color_panel_16"],
            )
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_textPanel_editItem,
                text="Edit file information\tE",
                bitmap=self.icons.iconsLib["info16"],
            )
        )
        menu.AppendSeparator()
        menu.AppendItem(
            makeMenuItem(
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
            makeMenuItem(
                parent=menu,
                id=ID_textPanel_annotate_charge_state,
                text="Assign charge state (selected)",
                bitmap=self.icons.iconsLib["assign_charge_16"],
            )
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_textPanel_annotate_alpha,
                text="Assign transparency value (selected)",
                bitmap=self.icons.iconsLib["transparency_16"],
            )
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_textPanel_annotate_mask,
                text="Assign mask value (selected)",
                bitmap=self.icons.iconsLib["mask_16"],
            )
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_textPanel_annotate_min_threshold,
                text="Assign minimum threshold (selected)",
                bitmap=self.icons.iconsLib["min_threshold_16"],
            )
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_textPanel_annotate_max_threshold,
                text="Assign maximum threshold (selected)",
                bitmap=self.icons.iconsLib["max_threshold_16"],
            )
        )
        menu.AppendSeparator()
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_textPanel_changeColorBatch_color,
                text="Assign new color using color picker (selected)",
                bitmap=self.icons.iconsLib["color_panel_16"],
            )
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_textPanel_changeColorBatch_palette,
                text="Assign new color using color palette (selected)",
                bitmap=self.icons.iconsLib["blank_16"],
            )
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_textPanel_changeColorBatch_colormap,
                text="Assign new color using colormap (selected)",
                bitmap=self.icons.iconsLib["blank_16"],
            )
        )
        menu.AppendItem(
            makeMenuItem(
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
            makeMenuItem(
                parent=menu,
                id=ID_load_multiple_text_2D,
                text="Add files\tCtrl+W",
                bitmap=self.icons.iconsLib["file_csv_16"],
            )
        )
        menu.AppendSeparator()
        menu.AppendItem(
            makeMenuItem(
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
            makeMenuItem(
                parent=menu,
                id=ID_textPanel_clear_selected,
                text="Remove from list (selected)",
                bitmap=self.icons.iconsLib["clear_16"],
            )
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_textPanel_clear_all,
                text="Remove from list (all)",
                bitmap=self.icons.iconsLib["clear_16"],
            )
        )

        menu.AppendSeparator()
        menu.AppendSeparator()
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_textPanel_delete_selected,
                text="Delete documents (selected)",
                bitmap=self.icons.iconsLib["bin16"],
            )
        )
        menu.AppendItem(
            makeMenuItem(
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
        menu_action_process_heatmap = makeMenuItem(parent=menu, text="Process heatmap data (selected)")
        menu.AppendItem(menu_action_process_heatmap)

        # bind events
        self.Bind(wx.EVT_MENU, self.on_process_heatmap_selected, menu_action_process_heatmap)

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def menu_save_tools(self, evt):

        menu = wx.Menu()
        menu_action_save_chromatogram = makeMenuItem(parent=menu, text="Save figure(s) as chromatogram (selected)")
        menu.AppendItem(menu_action_save_chromatogram)

        menu_action_save_mobilogram = makeMenuItem(parent=menu, text="Save figure(s) as mobilogram (selected)")
        menu.AppendItem(menu_action_save_mobilogram)

        menu_action_save_heatmap = makeMenuItem(parent=menu, text="Save figure(s) as heatmap (selected)")
        menu.AppendItem(menu_action_save_heatmap)

        menu_action_save_waterfall = makeMenuItem(parent=menu, text="Save figure(s) as waterfall (selected)")
        menu.AppendItem(menu_action_save_waterfall)

        menu.AppendSeparator()
        menu_action_save_data_chromatogram = makeMenuItem(parent=menu, text="Save chromatographic data (selected)")
        menu.AppendItem(menu_action_save_data_chromatogram)

        menu_action_save_data_mobilogram = makeMenuItem(parent=menu, text="Save mobilogram data (selected)")
        menu.AppendItem(menu_action_save_data_mobilogram)

        menu_action_save_data_heatmap = makeMenuItem(parent=menu, text="Save heatmap data (selected)")
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

    def menu_column_right_click(self, evt):
        self.Bind(wx.EVT_MENU, self.on_update_peaklist_table, id=ID_textPanel_table_startCE)
        self.Bind(wx.EVT_MENU, self.on_update_peaklist_table, id=ID_textPanel_table_endCE)
        self.Bind(wx.EVT_MENU, self.on_update_peaklist_table, id=ID_textPanel_table_charge)
        self.Bind(wx.EVT_MENU, self.on_update_peaklist_table, id=ID_textPanel_table_color)
        self.Bind(wx.EVT_MENU, self.on_update_peaklist_table, id=ID_textPanel_table_colormap)
        self.Bind(wx.EVT_MENU, self.on_update_peaklist_table, id=ID_textPanel_table_alpha)
        self.Bind(wx.EVT_MENU, self.on_update_peaklist_table, id=ID_textPanel_table_mask)
        self.Bind(wx.EVT_MENU, self.on_update_peaklist_table, id=ID_textPanel_table_document)
        self.Bind(wx.EVT_MENU, self.on_update_peaklist_table, id=ID_textPanel_table_label)
        self.Bind(wx.EVT_MENU, self.on_update_peaklist_table, id=ID_textPanel_table_shape)
        self.Bind(wx.EVT_MENU, self.on_update_peaklist_table, id=ID_textPanel_table_hideAll)
        self.Bind(wx.EVT_MENU, self.on_update_peaklist_table, id=ID_textPanel_table_restoreAll)

        menu = wx.Menu()
        n = 0
        self.table_start = menu.AppendCheckItem(ID_textPanel_table_startCE, "Table: Minimum energy")
        self.table_start.Check(self.config._textlistSettings[n]["show"])
        n = n + 1
        self.table_end = menu.AppendCheckItem(ID_textPanel_table_endCE, "Table: Maximum energy")
        self.table_end.Check(self.config._textlistSettings[n]["show"])
        n = n + 1
        self.table_color = menu.AppendCheckItem(ID_textPanel_table_charge, "Table: Charge")
        self.table_color.Check(self.config._textlistSettings[n]["show"])
        n = n + 1
        self.table_color = menu.AppendCheckItem(ID_textPanel_table_color, "Table: Color")
        self.table_color.Check(self.config._textlistSettings[n]["show"])
        n = n + 1
        self.table_colormap = menu.AppendCheckItem(ID_textPanel_table_colormap, "Table: Colormap")
        self.table_colormap.Check(self.config._textlistSettings[n]["show"])
        n = n + 1
        self.table_alpha = menu.AppendCheckItem(ID_textPanel_table_alpha, "Table: Transparency")
        self.table_alpha.Check(self.config._textlistSettings[n]["show"])
        n = n + 1
        self.table_mask = menu.AppendCheckItem(ID_textPanel_table_mask, "Table: Mask")
        self.table_mask.Check(self.config._textlistSettings[n]["show"])
        n = n + 1
        self.table_label = menu.AppendCheckItem(ID_textPanel_table_label, "Table: Label")
        self.table_label.Check(self.config._textlistSettings[n]["show"])
        n = n + 1
        self.table_shape = menu.AppendCheckItem(ID_textPanel_table_shape, "Table: Shape")
        self.table_shape.Check(self.config._textlistSettings[n]["show"])
        n = n + 1
        self.table_filename = menu.AppendCheckItem(ID_textPanel_table_document, "Table: Filename")
        self.table_filename.Check(self.config._textlistSettings[n]["show"])
        menu.AppendSeparator()
        self.table_index = menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_textPanel_table_hideAll,
                text="Table: Hide all",
                bitmap=self.icons.iconsLib["hide_table_16"],
            )
        )
        self.table_index = menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_textPanel_table_restoreAll,
                text="Table: Restore all",
                bitmap=self.icons.iconsLib["show_table_16"],
            )
        )

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def get_selected_items(self):
        all_eic_datasets = ["Drift time (2D)", "Drift time(2D, processed)"]

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

    def on_change_item_colormap(self, evt):
        # get number of checked items
        check_count = 0
        for row in range(self.peaklist.GetItemCount()):
            if self.peaklist.IsChecked(index=row):
                check_count += 1

        if check_count > len(self.config.narrowCmapList):
            colormaps = self.config.narrowCmapList
        else:
            colormaps = self.config.narrowCmapList + self.config.cmaps2

        for row in range(self.peaklist.GetItemCount()):
            if self.peaklist.IsChecked(index=row):
                self.peaklist.item_id = row
                colormap = colormaps[row]
                self.peaklist.SetItem(row, self.config.textlistColNames["colormap"], str(colormap))

                # update document
                try:
                    self.on_update_document(evt=None)
                except TypeError:
                    print("Please select item")

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
                self.peaklist.SetItemBackgroundColour(row, convertRGB1to255(color))
                self.peaklist.SetItemTextColour(row, determineFontColor(convertRGB1to255(color), return_rgb=True))
                check_count += 1

            self.on_update_document(evt=None)

    def on_update_peaklist_table(self, evt):
        evtID = evt.GetId()

        # check which event was triggered
        if evtID == ID_textPanel_table_startCE:
            col_index = self.config.textlistColNames["start"]
        elif evtID == ID_textPanel_table_endCE:
            col_index = self.config.textlistColNames["end"]
        elif evtID == ID_textPanel_table_charge:
            col_index = self.config.textlistColNames["charge"]
        elif evtID == ID_textPanel_table_color:
            col_index = self.config.textlistColNames["color"]
        elif evtID == ID_textPanel_table_colormap:
            col_index = self.config.textlistColNames["colormap"]
        elif evtID == ID_textPanel_table_alpha:
            col_index = self.config.textlistColNames["alpha"]
        elif evtID == ID_textPanel_table_mask:
            col_index = self.config.textlistColNames["mask"]
        elif evtID == ID_textPanel_table_label:
            col_index = self.config.textlistColNames["label"]
        elif evtID == ID_textPanel_table_shape:
            col_index = self.config.textlistColNames["shape"]
        elif evtID == ID_textPanel_table_document:
            col_index = self.config.textlistColNames["filename"]
        elif evtID == ID_textPanel_table_restoreAll:
            for i in range(len(self.config._textlistSettings)):
                self.config._textlistSettings[i]["show"] = True
                col_width = self.config._textlistSettings[i]["width"]
                self.peaklist.SetColumnWidth(i, col_width)
            return
        elif evtID == ID_textPanel_table_hideAll:
            for i in range(len(self.config._textlistSettings)):
                self.config._textlistSettings[i]["show"] = False
                col_width = 0
                self.peaklist.SetColumnWidth(i, col_width)
            return

        # check values
        col_check = not self.config._textlistSettings[col_index]["show"]
        self.config._textlistSettings[col_index]["show"] = col_check
        if col_check:
            col_width = self.config._textlistSettings[col_index]["width"]
        else:
            col_width = 0
        # set new column width
        self.peaklist.SetColumnWidth(col_index, col_width)

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

        ask_dialog = DialogAsk(self, **ask_kwargs)
        if ask_dialog.ShowModal() != wx.ID_OK:
            return

        return_value = ask_dialog.return_value
        if return_value is None:
            return

        for row in range(rows):
            if self.peaklist.IsChecked(index=row):
                itemInfo = self.on_get_item_information(row)
                document = self.data_handling._on_get_document(itemInfo["document"])

                if not ask_kwargs["keyword"] in ["min_threshold", "max_threshold"]:
                    column = self.config.textlistColNames[ask_kwargs["keyword"]]
                    self.peaklist.SetItem(row, column, str(return_value))

                # set value in document
                if document.got2DIMS:
                    document.IMS2D[ask_kwargs["keyword"]] = return_value
                if document.got2Dprocess:
                    document.IMS2Dprocess[ask_kwargs["keyword"]] = return_value

                # update document
                self.presenter.documentsDict[document.title] = document

    def on_check_selected(self, evt):
        """Check current item when letter S is pressed on the keyboard"""
        if self.peaklist.item_id is None:
            return

        check = not self.peaklist.IsChecked(index=self.peaklist.item_id)
        self.peaklist.CheckItem(self.peaklist.item_id, check=check)

    def on_plot(self, evt, itemID=None):
        """Plot data"""

        if itemID is not None:
            self.peaklist.item_id = itemID

        if self.peaklist.item_id is None:
            return

        itemInfo = self.on_get_item_information(self.peaklist.item_id)

        try:
            selectedItem = itemInfo["document"]
            currentDocument = self.presenter.documentsDict[selectedItem]

            # get data
            data = currentDocument.IMS2D
        except Exception:
            document_title, ion_title = re.split(": ", itemInfo["document"])
            document = self.presenter.documentsDict[document_title]
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

        if evtID == ID_textPanel_show_mobiligram:
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
                DialogBox(exceptionTitle="Missing data", exceptionMsg=msg, type="Error")
                return

            # Process data
            # TODO: this function is temporarily disabled! Needs to be fixed before next release
            if evtID == ID_textPanel_show_process_heatmap:
                pass
                # zvals = self.presenter.process2Ddata(zvals=zvals.copy(), return_data=True)

            self.presenter.view.panelPlots.on_plot_2D(
                zvals, xvals, yvals, xlabel, ylabel, cmap, override=True, set_page=True
            )

    def onCheckDuplicates(self, fileName):
        currentItems = self.peaklist.GetItemCount() - 1
        while currentItems >= 0:
            itemInfo = self.on_get_item_information(currentItems)
            if itemInfo["document"] == fileName:
                logger.info("File {} already in the table - skipping".format(itemInfo["document"]))
                currentItems = 0
                return True
            currentItems -= 1
        return False

    def onRemoveDuplicates(self, evt):
        """
        This function removes duplicates from the list
        Its not very efficient!
        """

        columns = self.peaklist.GetColumnCount()
        rows = self.peaklist.GetItemCount()
        tempData = []
        # Iterate over row and columns to get data
        for row in range(rows):
            tempRow = []
            for col in range(columns):
                item = self.peaklist.GetItem(row, col=col)
                tempRow.append(item.GetText())
            tempRow.append(self.peaklist.IsChecked(index=row))
            tempRow.append(self.peaklist.GetItemBackgroundColour(row))
            tempRow.append(self.peaklist.GetItemTextColour(row))
            tempData.append(tempRow)

        # Remove duplicates
        tempData = removeListDuplicates(
            input=tempData,
            columnsIn=[
                "check",
                "start",
                "end",
                "charge",
                "color",
                "colormap",
                "alpha",
                "mask",
                "label",
                "shape",
                "filename",
                "check",
                "rgb",
                "font_color",
            ],
            limitedCols=["filename"],
        )
        rows = len(tempData)
        # Clear table
        self.peaklist.DeleteAllItems()

        checkData, bg_rgb, fg_rgb = [], [], []
        for check in tempData:
            fg_rgb.append(check[-1])
            del check[-1]
            bg_rgb.append(check[-1])
            del check[-1]
            checkData.append(check[-1])
            del check[-1]

        # Reinstate data
        rowList = arange(len(tempData))
        for row, check, bg_rgb, fg_color in zip(rowList, checkData, bg_rgb, fg_rgb):
            self.peaklist.Append(tempData[row])
            self.peaklist.CheckItem(row, check)
            self.peaklist.SetItemBackgroundColour(row, bg_rgb)
            self.peaklist.SetItemTextColour(row, fg_color)

        if evt is None:
            return
        else:
            evt.Skip()

    def onUpdateOverlayMethod(self, evt):
        self.config.overlayMethod = self.combo.GetStringSelection()

        if evt is not None:
            evt.Skip()

    def on_get_item_information(self, itemID, return_list=False):

        information = self.peaklist.on_get_item_information(itemID)

        document = self.data_handling._on_get_document(information["document"])
        # check whether the ion has any previous information
        min_threshold, max_threshold = 0, 1
        if document is not None:
            try:
                min_threshold = document.IMS2D.get("min_threshold", 0)
                max_threshold = document.IMS2D.get("max_threshold", 1)
            except AttributeError:
                min_threshold = document.IMS2Dprocess.get("min_threshold", 0)
                max_threshold = document.IMS2Dprocess.get("max_threshold", 1)

        information["min_threshold"] = min_threshold
        information["max_threshold"] = max_threshold

        return information

    def on_get_value(self, value_type="color"):
        information = self.on_get_item_information(self.peaklist.item_id)

        if value_type == "minCE":
            return information["minCE"]
        elif value_type == "maxCE":
            return information["maxCE"]
        elif value_type == "color":
            return information["color"]
        elif value_type == "charge":
            return information["charge"]
        elif value_type == "colormap":
            return information["colormap"]
        elif value_type == "intensity":
            return information["intensity"]
        elif value_type == "mask":
            return information["mask"]
        elif value_type == "label":
            return information["label"]
        elif value_type == "shape":
            return information["shape"]
        elif value_type == "document":
            return information["document"]

    def on_update_value_in_peaklist(self, item_id, value_type, value):
        if value_type == "color":
            color_255, color_1, font_color = value
            self.peaklist.SetItemBackgroundColour(item_id, color_255)
            self.peaklist.SetStringItem(item_id, self.config.textlistColNames["color"], str(color_1))
            self.peaklist.SetItemTextColour(item_id, font_color)
        elif value_type == "color_text":
            self.peaklist.SetItemBackgroundColour(item_id, value)
            self.peaklist.SetStringItem(item_id, self.config.textlistColNames["color"], str(convertRGB255to1(value)))
            self.peaklist.SetItemTextColour(item_id, determineFontColor(value, return_rgb=True))

    def on_get_color(self, evt):

        dlg = DialogColorPicker(self, self.config.customColors)
        if dlg.ShowModal() == "ok":
            __, color_1, __ = dlg.GetChosenColour()
            self.config.customColors = dlg.GetCustomColours()

            return color_1

    def on_assign_color(self, evt, itemID=None, give_value=False):
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

        if itemID is not None:
            self.peaklist.item_id = itemID

        if self.peaklist.item_id is None:
            return

        dlg = DialogColorPicker(self, self.config.customColors)
        if dlg.ShowModal() == "ok":
            color_255, color_1, font_color = dlg.GetChosenColour()
            self.config.customColors = dlg.GetCustomColours()
            self.on_update_value_in_peaklist(itemID, "color", [color_255, color_1, font_color])

            # update document
            self.on_update_document(evt=None)

            if give_value:
                return color_255
        else:
            try:
                color_255 = convertRGB1to255(literal_eval(self.on_get_value(value_type="color")), 3)
            except Exception:
                color_255 = self.config.customColors[get_random_int(0, 15)]
            self.on_update_value_in_peaklist(self.peaklist.item_id, "color", [color_255, color_1, font_color])
            if give_value:
                return color_255

    def on_update_document(self, evt, itemInfo=None):

        # get item info
        if itemInfo is None:
            itemInfo = self.on_get_item_information(self.peaklist.item_id)

        keywords = ["color", "colormap", "alpha", "mask", "label", "min_threshold", "max_threshold", "charge", "cmap"]

        # get item
        try:
            document = self.presenter.documentsDict[itemInfo["document"]]
            for keyword in keywords:
                keyword_name = self.keyword_alias.get(keyword, keyword)
                if document.got2DIMS:
                    document.IMS2D[keyword] = itemInfo[keyword_name]
                if document.got2Dprocess:
                    document.IMS2Dprocess[keyword] = itemInfo[keyword_name]
        except Exception as err:
            logger.error(err)
            document_title, ion_title = re.split(": ", itemInfo["document"])
            document = self.presenter.documentsDict[document_title]
            for keyword in keywords:
                keyword_name = self.keyword_alias.get(keyword, keyword)
                if ion_title in document.IMS2DcompData:
                    document.IMS2DcompData[ion_title][keyword] = itemInfo[keyword_name]
                else:
                    document.IMS2Dions[ion_title][keyword] = itemInfo[keyword_name]

        # Update file list
        self.data_handling.on_update_document(document, "no_refresh")

    def on_open_editor(self, evt):
        from gui_elements.panel_modify_item_settings import PanelModifyItemSettings

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

            self.item_editor = PanelModifyItemSettings(self, self.presenter, self.config, **dlg_kwargs)
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

                    self.item_editor = PanelModifyItemSettings(self, self.presenter, self.config, **dlg_kwargs)
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

                self.item_editor = PanelModifyItemSettings(self, self.presenter, self.config, **dlg_kwargs)
                self.item_editor.Show()

    def on_remove_deleted_item(self, document):
        """
        document: str
            name of the deleted document
        """
        row = self.peaklist.GetItemCount() - 1

        if isinstance(document, str):
            document = [document]

        document_list = document

        while row >= 0:
            info = self.on_get_item_information(itemID=row)
            for document_title in document_list:
                if info["document"] == document_title or document_title in info["document"]:
                    self.peaklist.DeleteItem(row)
                    del document_list[document_list.index(document_title)]
            row -= 1

    def on_check_duplicate_colors(self, new_color):
        """
        Check whether newly assigned color is already in the table and if so,
        return a different one
        """
        count = self.peaklist.GetItemCount()
        color_list = []
        for row in range(count):
            color_list.append(self.peaklist.GetItemBackgroundColour(item=row))

        if new_color in color_list:
            counter = len(self.config.customColors) - 1
            while counter > 0:
                config_color = self.config.customColors[counter]
                if config_color not in color_list:
                    return config_color

                counter -= 1

            return randomColorGenerator(True)
        return new_color

    def on_add_to_table(self, add_dict, check_color=True, return_color=False):

        # get color
        color = add_dict.get("color", self.config.customColors[get_random_int(0, 15)])
        # check for duplicate color
        if check_color:
            color = self.on_check_duplicate_colors(color)

        # add to filelist
        self.peaklist.Append(
            [
                "",
                str(add_dict.get("energy_start", "")),
                str(add_dict.get("energy_end", "")),
                str(add_dict.get("charge", "")),
                str(roundRGB(convertRGB255to1(color))),
                str(add_dict.get("colormap", "")),
                str(add_dict.get("alpha", "")),
                str(add_dict.get("mask", "")),
                str(add_dict.get("label", "")),
                str(add_dict.get("shape", "")),
                str(add_dict.get("document", "")),
            ]
        )
        self.peaklist.SetItemBackgroundColour(self.peaklist.GetItemCount() - 1, color)

        font_color = determineFontColor(color, return_rgb=True)
        self.peaklist.SetItemTextColour(self.peaklist.GetItemCount() - 1, font_color)

        if return_color:
            return color

    def on_delete_item(self, evt):

        itemInfo = self.on_get_item_information(itemID=self.peaklist.item_id)
        msg = "Are you sure you would like to delete {}?\nThis action cannot be undone.".format(itemInfo["document"])
        dlg = DialogBox(type="Question", exceptionMsg=msg)
        if dlg == wx.ID_NO:
            print("The operation was cancelled")
            return

        self.view.panelDocuments.documents.on_delete_data__document(itemInfo["document"], ask_permission=False)

    def on_delete_selected(self, evt):

        itemID = self.peaklist.GetItemCount() - 1

        while itemID >= 0:
            if self.peaklist.IsChecked(index=itemID):
                itemInfo = self.on_get_item_information(itemID=itemID)
                msg = "Are you sure you would like to delete {}?\nThis action cannot be undone.".format(
                    itemInfo["document"]
                )
                dlg = DialogBox(exceptionMsg=msg, type="Question")
                if dlg == wx.ID_NO:
                    print("The operation was cancelled")
                    continue
                try:
                    self.view.panelDocuments.documents.on_delete_data__document(
                        itemInfo["document"], ask_permission=False
                    )
                # item does not exist
                except KeyError:
                    self.on_remove_deleted_item(itemInfo["document"])

            itemID -= 1

    def on_delete_all(self, evt):

        msg = (
            "Are you sure you would like to delete all [2D IM-MS documents]"
            + " from the list?\nThis action cannot be undone."
        )
        dlg = DialogBox(exceptionMsg=msg, type="Question")
        if dlg == wx.ID_NO:
            print("The operation was cancelled")
            return

        itemID = self.peaklist.GetItemCount() - 1
        while itemID >= 0:
            itemInfo = self.on_get_item_information(itemID=itemID)
            self.view.panelDocuments.documents.on_delete_data__document(itemInfo["document"], ask_permission=False)
            itemID -= 1

    def delete_row_from_table(self, delete_document_title=None):
        rows = self.peaklist.GetItemCount() - 1
        while rows >= 0:
            itemInfo = self.on_get_item_information(rows)

            if itemInfo["document"] == delete_document_title:
                self.peaklist.DeleteItem(rows)
            rows -= 1
