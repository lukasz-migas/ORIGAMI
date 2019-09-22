# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import logging
from ast import literal_eval

import wx
from gui_elements.dialog_ask import DialogAsk
from gui_elements.dialog_color_picker import DialogColorPicker
from gui_elements.misc_dialogs import DialogBox
from ids import ID_extractAllIons
from ids import ID_extractNewIon
from ids import ID_extractSelectedIon
from ids import ID_highlightRectAllIons
from ids import ID_ionPanel_annotate_alpha
from ids import ID_ionPanel_annotate_charge_state
from ids import ID_ionPanel_annotate_mask
from ids import ID_ionPanel_annotate_max_threshold
from ids import ID_ionPanel_annotate_min_threshold
from ids import ID_ionPanel_assignColor
from ids import ID_ionPanel_automaticExtract
from ids import ID_ionPanel_changeColorBatch_color
from ids import ID_ionPanel_changeColorBatch_colormap
from ids import ID_ionPanel_changeColorBatch_palette
from ids import ID_ionPanel_changeColormapBatch
from ids import ID_ionPanel_check_all
from ids import ID_ionPanel_check_selected
from ids import ID_ionPanel_clear_all
from ids import ID_ionPanel_clear_selected
from ids import ID_ionPanel_delete_all
from ids import ID_ionPanel_delete_rightClick
from ids import ID_ionPanel_delete_selected
from ids import ID_ionPanel_editItem
from ids import ID_ionPanel_show_chromatogram
from ids import ID_ionPanel_show_heatmap
from ids import ID_ionPanel_show_mobilogram
from ids import ID_ionPanel_show_process_heatmap
from ids import ID_ionPanel_show_zoom_in_MS
from ids import ID_ionPanel_table_alpha
from ids import ID_ionPanel_table_charge
from ids import ID_ionPanel_table_color
from ids import ID_ionPanel_table_colormap
from ids import ID_ionPanel_table_document
from ids import ID_ionPanel_table_hideAll
from ids import ID_ionPanel_table_intensity
from ids import ID_ionPanel_table_label
from ids import ID_ionPanel_table_mask
from ids import ID_ionPanel_table_method
from ids import ID_ionPanel_table_restoreAll
from ids import ID_ionPanel_table_startMS
from ids import ID_window_ionList
from styles import ListCtrl
from styles import makeMenuItem
from styles import makeTooltip
from utils.check import isempty
from utils.color import convertRGB1to255
from utils.color import convertRGB255to1
from utils.color import determineFontColor
from utils.color import randomColorGenerator
from utils.color import roundRGB
from utils.exceptions import MessageError
from utils.labels import get_ion_name_from_label
from utils.random import get_random_int

logger = logging.getLogger("origami")


class PanelPeaklist(wx.Panel):
    keyword_alias = {"colormap": "cmap"}

    def __init__(self, parent, config, icons, helpInfo, presenter):
        wx.Panel.__init__(
            self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.Size(300, -1), style=wx.TAB_TRAVERSAL
        )

        self.view = parent
        self.config = config
        self.help = helpInfo
        self.presenter = presenter
        self.icons = icons

        self.allChecked = True
        self.override = self.config.overrideCombine
        self.addToDocument = False
        self.normalize1D = False
        self.extractAutomatically = False
        self.plotAutomatically = True

        self.item_editor = None
        self.onSelectingItem = True
        self.ask_value = None
        self.flag = False  # flag to either show or hide annotation panel
        self.process = False

        self._ionPanel_peaklist = {
            0: {"name": "", "tag": "check", "type": "bool"},
            1: {"name": "ion name", "tag": "ion_name", "type": "str"},
            2: {"name": "z", "tag": "charge", "type": "int"},
            3: {"name": "int", "tag": "intensity", "type": "float"},
            4: {"name": "color", "tag": "color", "type": "color"},
            5: {"name": "colormap", "tag": "colormap", "type": "str"},
            6: {"name": "\N{GREEK SMALL LETTER ALPHA}", "tag": "alpha", "type": "float"},
            7: {"name": "mask", "tag": "mask", "type": "float"},
            8: {"name": "label", "tag": "label", "type": "str"},
            9: {"name": "method", "tag": "method", "type": "str"},
            10: {"name": "document", "tag": "document", "type": "str"},
        }

        self.make_gui()

        # add a couple of accelerators
        accelerators = [
            (wx.ACCEL_NORMAL, ord("C"), ID_ionPanel_assignColor),
            (wx.ACCEL_NORMAL, ord("E"), ID_ionPanel_editItem),
            (wx.ACCEL_NORMAL, ord("H"), ID_highlightRectAllIons),
            (wx.ACCEL_NORMAL, ord("M"), ID_ionPanel_show_mobilogram),
            (wx.ACCEL_NORMAL, ord("S"), ID_ionPanel_check_selected),
            (wx.ACCEL_NORMAL, ord("X"), ID_ionPanel_check_all),
            (wx.ACCEL_NORMAL, ord("Z"), ID_ionPanel_show_zoom_in_MS),
            (wx.ACCEL_NORMAL, wx.WXK_DELETE, ID_ionPanel_delete_rightClick),
        ]
        self.SetAcceleratorTable(wx.AcceleratorTable(accelerators))

        wx.EVT_MENU(self, ID_ionPanel_editItem, self.on_open_editor)
        wx.EVT_MENU(self, ID_ionPanel_assignColor, self.on_assign_color)
        wx.EVT_MENU(self, ID_ionPanel_show_zoom_in_MS, self.on_plot)
        wx.EVT_MENU(self, ID_ionPanel_show_mobilogram, self.on_plot)
        wx.EVT_MENU(self, ID_ionPanel_check_selected, self.on_check_selected)
        wx.EVT_MENU(self, ID_ionPanel_delete_rightClick, self.on_delete_item)

    def _setup_handling_and_processing(self):
        self.data_processing = self.view.data_processing
        self.data_handling = self.view.data_handling
        self.data_visualisation = self.view.data_visualisation
        self.document_tree = self.presenter.view.panelDocuments.documents

    def on_open_info_panel(self, evt):
        logger.error("This function is not implemented yet")

    def make_gui(self):
        """ Make panel GUI """
        toolbar = self.make_toolbar()
        self.make_listctrl()

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.Add(toolbar, 0, wx.EXPAND, 0)
        self.main_sizer.Add(self.peaklist, 1, wx.EXPAND, 0)

        # fit layout
        self.main_sizer.Fit(self)
        self.SetSizer(self.main_sizer)
        self.SetSize((300, -1))
        self.Layout()

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

        self.extract_btn = wx.BitmapButton(
            self, -1, self.icons.iconsLib["extract16"], size=(18, 18), style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL
        )
        self.extract_btn.SetToolTip(makeTooltip("Extract..."))

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
        self.Bind(wx.EVT_BUTTON, self.menu_extract_tools, self.extract_btn)
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
        btn_grid_vert.Add(self.extract_btn, (x, n), flag=wx.ALIGN_CENTER)
        n += 1
        btn_grid_vert.Add(self.process_btn, (x, n), flag=wx.ALIGN_CENTER)
        n += 1
        btn_grid_vert.Add(self.save_btn, (x, n), flag=wx.ALIGN_CENTER)
        n += 1
        btn_grid_vert.Add(vertical_line_1, (x, n), flag=wx.EXPAND)
        n += 1
        btn_grid_vert.Add(self.info_btn, (x, n), flag=wx.ALIGN_CENTER)

        return btn_grid_vert

    def make_listctrl(self):

        self.peaklist = ListCtrl(self, style=wx.LC_REPORT | wx.LC_VRULES, column_info=self._ionPanel_peaklist)
        for item in self.config._peakListSettings:
            order = item["order"]
            name = item["name"]
            width = 0
            if item["show"]:
                width = item["width"]
            self.peaklist.InsertColumn(order, name, width=width, format=wx.LIST_FORMAT_CENTER)

        self.peaklist.Bind(wx.EVT_LEFT_DCLICK, self.on_double_click_on_item)
        self.peaklist.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.on_right_click)
        self.peaklist.Bind(wx.EVT_LIST_COL_RIGHT_CLICK, self.menu_column_right_click)

    def on_double_click_on_item(self, evt):
        """Create annotation for activated peak."""

        if self.peaklist.item_id != -1:
            if not self.item_editor:
                self.on_open_editor(evt=None)
            else:
                self.item_editor.on_update_gui(self.on_get_item_information(self.peaklist.item_id))

    def onRenameItem(self, old_name, new_name, item_type="Document"):
        for row in range(self.peaklist.GetItemCount()):
            itemInfo = self.on_get_item_information(itemID=row)
            if item_type == "document":
                if itemInfo["document"] == old_name:
                    self.peaklist.SetStringItem(row, self.config.peaklistColNames["filename"], new_name)

    def menu_column_right_click(self, evt):
        self.Bind(wx.EVT_MENU, self.on_update_peaklist_table, id=ID_ionPanel_table_startMS)
        self.Bind(wx.EVT_MENU, self.on_update_peaklist_table, id=ID_ionPanel_table_color)
        self.Bind(wx.EVT_MENU, self.on_update_peaklist_table, id=ID_ionPanel_table_colormap)
        self.Bind(wx.EVT_MENU, self.on_update_peaklist_table, id=ID_ionPanel_table_charge)
        self.Bind(wx.EVT_MENU, self.on_update_peaklist_table, id=ID_ionPanel_table_intensity)
        self.Bind(wx.EVT_MENU, self.on_update_peaklist_table, id=ID_ionPanel_table_document)
        self.Bind(wx.EVT_MENU, self.on_update_peaklist_table, id=ID_ionPanel_table_alpha)
        self.Bind(wx.EVT_MENU, self.on_update_peaklist_table, id=ID_ionPanel_table_mask)
        self.Bind(wx.EVT_MENU, self.on_update_peaklist_table, id=ID_ionPanel_table_label)
        self.Bind(wx.EVT_MENU, self.on_update_peaklist_table, id=ID_ionPanel_table_method)
        self.Bind(wx.EVT_MENU, self.on_update_peaklist_table, id=ID_ionPanel_table_hideAll)
        self.Bind(wx.EVT_MENU, self.on_update_peaklist_table, id=ID_ionPanel_table_restoreAll)

        menu = wx.Menu()
        n = 1
        self.table_start = menu.AppendCheckItem(ID_ionPanel_table_startMS, "Table: Ion name")
        self.table_start.Check(self.config._peakListSettings[n]["show"])
        n += 1
        self.table_charge = menu.AppendCheckItem(ID_ionPanel_table_charge, "Table: Charge")
        self.table_charge.Check(self.config._peakListSettings[n]["show"])
        n += 1
        self.table_intensity = menu.AppendCheckItem(ID_ionPanel_table_intensity, "Table: Intensity")
        self.table_intensity.Check(self.config._peakListSettings[n]["show"])
        n += 1
        self.table_color = menu.AppendCheckItem(ID_ionPanel_table_color, "Table: Color")
        self.table_color.Check(self.config._peakListSettings[n]["show"])
        n += 1
        self.table_colormap = menu.AppendCheckItem(ID_ionPanel_table_colormap, "Table: Colormap")
        self.table_colormap.Check(self.config._peakListSettings[n]["show"])
        n += 1
        self.table_alpha = menu.AppendCheckItem(ID_ionPanel_table_alpha, "Table: Transparency")
        self.table_alpha.Check(self.config._peakListSettings[n]["show"])
        n += 1
        self.table_mask = menu.AppendCheckItem(ID_ionPanel_table_mask, "Table: Mask")
        self.table_mask.Check(self.config._peakListSettings[n]["show"])
        n += 1
        self.table_label = menu.AppendCheckItem(ID_ionPanel_table_label, "Table: Label")
        self.table_label.Check(self.config._peakListSettings[n]["show"])
        n += 1
        self.table_method = menu.AppendCheckItem(ID_ionPanel_table_method, "Table: Method")
        self.table_method.Check(self.config._peakListSettings[n]["show"])
        n += 1
        self.table_document = menu.AppendCheckItem(ID_ionPanel_table_document, "Table: Document")
        self.table_document.Check(self.config._peakListSettings[n]["show"])
        menu.AppendSeparator()
        self.table_index = menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_ionPanel_table_hideAll,
                text="Table: Hide all",
                bitmap=self.icons.iconsLib["hide_table_16"],
            )
        )
        self.table_index = menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_ionPanel_table_restoreAll,
                text="Table: Restore all",
                bitmap=self.icons.iconsLib["show_table_16"],
            )
        )

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def on_right_click(self, evt):

        self.peaklist.item_id = evt.GetIndex()
        menu = wx.Menu()
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_ionPanel_show_zoom_in_MS,
                text="Zoom in on the ion\tZ",
                bitmap=self.icons.iconsLib["zoom_16"],
            )
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_ionPanel_show_chromatogram,
                text="Show chromatogram",
                bitmap=self.icons.iconsLib["chromatogram_16"],
            )
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_ionPanel_show_mobilogram,
                text="Show mobilogram\tM",
                bitmap=self.icons.iconsLib["mobilogram_16"],
            )
        )
        menu_action_show_heatmap = makeMenuItem(
            parent=menu, id=ID_ionPanel_show_heatmap, text="Show heatmap", bitmap=self.icons.iconsLib["heatmap_16"]
        )
        menu.AppendItem(menu_action_show_heatmap)

        menu_action_process_heatmap = makeMenuItem(parent=menu, id=ID_ionPanel_show_heatmap, text="Process heatmap...")
        menu.AppendItem(menu_action_process_heatmap)
        menu.AppendSeparator()
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_ionPanel_assignColor,
                text="Assign new color\tC",
                bitmap=self.icons.iconsLib["color_panel_16"],
            )
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_ionPanel_editItem,
                text="Edit ion information\tE",
                bitmap=self.icons.iconsLib["info16"],
            )
        )
        menu.AppendSeparator()
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_ionPanel_delete_rightClick,
                text="Remove item\tDelete",
                bitmap=self.icons.iconsLib["bin16"],
            )
        )

        # bind events
        self.Bind(wx.EVT_MENU, self.on_plot, id=ID_ionPanel_show_zoom_in_MS)
        self.Bind(wx.EVT_MENU, self.on_plot, id=ID_ionPanel_show_mobilogram)
        self.Bind(wx.EVT_MENU, self.on_plot, id=ID_ionPanel_show_chromatogram)
        self.Bind(wx.EVT_MENU, self.on_plot, id=ID_ionPanel_show_heatmap)
        self.Bind(wx.EVT_MENU, self.on_plot, menu_action_process_heatmap, id=ID_ionPanel_show_process_heatmap)
        self.Bind(wx.EVT_MENU, self.on_open_editor, id=ID_ionPanel_editItem)
        self.Bind(wx.EVT_MENU, self.on_assign_color, id=ID_ionPanel_assignColor)
        self.Bind(wx.EVT_MENU, self.on_delete_item, id=ID_ionPanel_delete_rightClick)

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def menu_annotate_tools(self, evt):
        self.Bind(wx.EVT_MENU, self.data_handling.on_highlight_selected_ions, id=ID_highlightRectAllIons)
        self.Bind(wx.EVT_MENU, self.on_change_item_parameter, id=ID_ionPanel_annotate_charge_state)
        self.Bind(wx.EVT_MENU, self.on_change_item_parameter, id=ID_ionPanel_annotate_alpha)
        self.Bind(wx.EVT_MENU, self.on_change_item_parameter, id=ID_ionPanel_annotate_mask)
        self.Bind(wx.EVT_MENU, self.on_change_item_parameter, id=ID_ionPanel_annotate_min_threshold)
        self.Bind(wx.EVT_MENU, self.on_change_item_parameter, id=ID_ionPanel_annotate_max_threshold)
        self.Bind(wx.EVT_MENU, self.on_change_item_color_batch, id=ID_ionPanel_changeColorBatch_color)
        self.Bind(wx.EVT_MENU, self.on_change_item_color_batch, id=ID_ionPanel_changeColorBatch_palette)
        self.Bind(wx.EVT_MENU, self.on_change_item_color_batch, id=ID_ionPanel_changeColorBatch_colormap)
        self.Bind(wx.EVT_MENU, self.on_change_item_colormap, id=ID_ionPanel_changeColormapBatch)

        menu = wx.Menu()
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_highlightRectAllIons,
                text="Highlight extracted items on MS plot (all)\tH",
                bitmap=self.icons.iconsLib["highlight_16"],
            )
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_ionPanel_annotate_charge_state,
                text="Assign charge state (selected)",
                bitmap=self.icons.iconsLib["assign_charge_16"],
            )
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_ionPanel_annotate_alpha,
                text="Assign transparency value (selected)",
                bitmap=self.icons.iconsLib["transparency_16"],
            )
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_ionPanel_annotate_mask,
                text="Assign mask value (selected)",
                bitmap=self.icons.iconsLib["mask_16"],
            )
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_ionPanel_annotate_min_threshold,
                text="Assign minimum threshold (selected)",
                bitmap=self.icons.iconsLib["min_threshold_16"],
            )
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_ionPanel_annotate_max_threshold,
                text="Assign maximum threshold (selected)",
                bitmap=self.icons.iconsLib["max_threshold_16"],
            )
        )
        menu.AppendSeparator()
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_ionPanel_changeColorBatch_color,
                text="Assign new color using color picker (selected)",
                bitmap=self.icons.iconsLib["color_panel_16"],
            )
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_ionPanel_changeColorBatch_palette,
                text="Assign new color using color palette (selected)",
                bitmap=self.icons.iconsLib["blank_16"],
            )
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_ionPanel_changeColorBatch_colormap,
                text="Assign new color using colormap (selected)",
                bitmap=self.icons.iconsLib["blank_16"],
            )
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_ionPanel_changeColormapBatch,
                text="Assign new colormap (selected)",
                bitmap=self.icons.iconsLib["randomize_16"],
            )
        )

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def menu_add_tools(self, evt):
        menu = wx.Menu()
        menu_action_load_peaklist = makeMenuItem(
            parent=menu,
            text="Add list of ions (.csv/.txt)",
            bitmap=self.icons.iconsLib["filelist_16"],
            help_text="Format: mz_start, mz_end, charge (optional), label (optional), color (optional)...",
        )
        menu.AppendItem(menu_action_load_peaklist)
        menu.AppendSeparator()
        menu_action_restore_peaklist = makeMenuItem(
            parent=menu,
            text="Restore items to peaklist",
            help_text="Restore items for selected document to the peaklist",
        )
        menu.AppendItem(menu_action_restore_peaklist)

        # bind events
        self.Bind(wx.EVT_MENU, self.on_load_peaklist, menu_action_load_peaklist)
        self.Bind(wx.EVT_MENU, self.on_restore_to_peaklist, menu_action_restore_peaklist)

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def menu_extract_tools(self, evt):
        # TODO: add Extract chromatographic data only
        # TODO: add extract mobilogram data only

        self.Bind(wx.EVT_MENU, self.on_check_tool, id=ID_ionPanel_automaticExtract)
        self.Bind(wx.EVT_MENU, self.on_extract_all, id=ID_extractAllIons)
        self.Bind(wx.EVT_MENU, self.on_extract_selected, id=ID_extractSelectedIon)
        self.Bind(wx.EVT_MENU, self.on_extract_new, id=ID_extractNewIon)

        menu = wx.Menu()
        self.automaticExtract_check = menu.AppendCheckItem(
            ID_ionPanel_automaticExtract,
            "Automatically extract data",
            help="Data will be automatically extracted as its added to the peaklist",
        )
        self.automaticExtract_check.Check(self.extractAutomatically)
        menu.AppendSeparator()
        menu.Append(ID_extractNewIon, "Extract heatmap data (new)")
        menu.Append(ID_extractSelectedIon, "Extract heatmap data (selected)")
        menu.Append(ID_extractAllIons, "Extract heatmap data (all)\tAlt+E")
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def menu_remove_tools(self, evt):
        # Make bindings
        self.Bind(wx.EVT_MENU, self.on_delete_selected, id=ID_ionPanel_delete_selected)
        self.Bind(wx.EVT_MENU, self.on_delete_all, id=ID_ionPanel_delete_all)
        self.Bind(wx.EVT_MENU, self.peaklist.on_clear_table_all, id=ID_ionPanel_clear_all)
        self.Bind(wx.EVT_MENU, self.peaklist.on_clear_table_selected, id=ID_ionPanel_clear_selected)

        menu = wx.Menu()
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_ionPanel_clear_selected,
                text="Remove from list (selected)",
                bitmap=self.icons.iconsLib["clear_16"],
            )
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_ionPanel_clear_all,
                text="Remove from list (all)",
                bitmap=self.icons.iconsLib["clear_16"],
            )
        )

        menu.AppendSeparator()
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_ionPanel_delete_selected,
                text="Remove from file (selected)",
                bitmap=self.icons.iconsLib["bin16"],
            )
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_ionPanel_delete_all,
                text="Remove from file (all)",
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

        menu.AppendSeparator()
        menu_action_setup_origami_parameters = makeMenuItem(parent=menu, text="ORIGAMI-MS: Setup parameters..")
        menu.AppendItem(menu_action_setup_origami_parameters)

        menu_action_combine_voltages = makeMenuItem(
            parent=menu, text="ORIGAMI-MS: Combine collision voltages (selected)"
        )
        menu.AppendItem(menu_action_combine_voltages)

        menu_action_extract_spectrum = makeMenuItem(
            parent=menu, text="ORIGAMI-MS: Extract mass spectra for each collision voltage..."
        )
        menu.AppendItem(menu_action_extract_spectrum)

        # bind events
        self.Bind(wx.EVT_MENU, self.on_process_heatmap_selected, menu_action_process_heatmap)
        self.Bind(wx.EVT_MENU, self.data_processing.on_combine_origami_collision_voltages, menu_action_combine_voltages)
        self.Bind(wx.EVT_MENU, self.on_open_ORIGAMI_MS_panel, menu_action_setup_origami_parameters)
        self.Bind(wx.EVT_MENU, self.on_open_ORIGAMI_MS_panel, menu_action_extract_spectrum)

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def menu_save_tools(self, evt):

        menu = wx.Menu()
        menu_action_save_peaklist = makeMenuItem(parent=menu, text="Export peak list to file...")
        menu.AppendItem(menu_action_save_peaklist)

        menu.AppendSeparator()
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
        self.Bind(wx.EVT_MENU, self.on_save_peaklist, menu_action_save_peaklist)

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

    def on_check_tool(self, evt):
        """ Check/uncheck menu item """

        evtID = evt.GetId()

        if evtID == ID_ionPanel_automaticExtract:
            self.extractAutomatically = not self.extractAutomatically
            args = ("Automatic extraction was set to: {}".format(self.extractAutomatically), 4)
            self.presenter.onThreading(evt, args, action="updateStatusbar")

    def on_update_peaklist_table(self, evt):
        evtID = evt.GetId()

        # check which event was triggered
        if evtID == ID_ionPanel_table_startMS:
            col_index = self.config.peaklistColNames["ion_name"]
        elif evtID == ID_ionPanel_table_charge:
            col_index = self.config.peaklistColNames["charge"]
        elif evtID == ID_ionPanel_table_intensity:
            col_index = self.config.peaklistColNames["intensity"]
        elif evtID == ID_ionPanel_table_color:
            col_index = self.config.peaklistColNames["color"]
        elif evtID == ID_ionPanel_table_colormap:
            col_index = self.config.peaklistColNames["colormap"]
        elif evtID == ID_ionPanel_table_alpha:
            col_index = self.config.peaklistColNames["alpha"]
        elif evtID == ID_ionPanel_table_mask:
            col_index = self.config.peaklistColNames["mask"]
        elif evtID == ID_ionPanel_table_label:
            col_index = self.config.peaklistColNames["label"]
        elif evtID == ID_ionPanel_table_method:
            col_index = self.config.peaklistColNames["method"]
        elif evtID == ID_ionPanel_table_document:
            col_index = self.config.peaklistColNames["filename"]
        elif evtID == ID_ionPanel_table_restoreAll:
            for i in range(len(self.config._peakListSettings)):
                self.config._peakListSettings[i]["show"] = True
                col_width = self.config._peakListSettings[i]["width"]
                self.peaklist.SetColumnWidth(i, col_width)
            return
        elif evtID == ID_ionPanel_table_hideAll:
            for i in range(len(self.config._peakListSettings)):
                self.config._peakListSettings[i]["show"] = False
                col_width = 0
                self.peaklist.SetColumnWidth(i, col_width)
            return

        # check values
        col_check = not self.config._peakListSettings[col_index]["show"]
        self.config._peakListSettings[col_index]["show"] = col_check
        if col_check:
            col_width = self.config._peakListSettings[col_index]["width"]
        else:
            col_width = 0
        # set new column width
        self.peaklist.SetColumnWidth(col_index, col_width)

    def on_change_item_parameter(self, evt):
        """ Iterate over list to assign charge state """

        rows = self.peaklist.GetItemCount()
        if rows == 0:
            return

        if evt.GetId() == ID_ionPanel_annotate_charge_state:
            ask_kwargs = {
                "static_text": "Assign charge state to selected items.",
                "value_text": "",
                "validator": "integer",
                "keyword": "charge",
            }
        elif evt.GetId() == ID_ionPanel_annotate_alpha:
            static_text = (
                "Assign new transparency value to selected items \nTypical transparency values: 0.5" + "\nRange 0-1"
            )
            ask_kwargs = {"static_text": static_text, "value_text": 0.5, "validator": "float", "keyword": "alpha"}
        elif evt.GetId() == ID_ionPanel_annotate_mask:
            ask_kwargs = {
                "static_text": "Assign new mask value to selected items \nTypical mask values: 0.25\nRange 0-1",
                "value_text": 0.25,
                "validator": "float",
                "keyword": "mask",
            }
        elif evt.GetId() == ID_ionPanel_annotate_min_threshold:
            ask_kwargs = {
                "static_text": "Assign minimum threshold value to selected items \nTypical mask values: 0.0\nRange 0-1",
                "value_text": 0.0,
                "validator": "float",
                "keyword": "min_threshold",
            }
        elif evt.GetId() == ID_ionPanel_annotate_max_threshold:
            ask_kwargs = {
                "static_text": "Assign maximum threshold value to selected items \nTypical mask values: 1.0\nRange 0-1",
                "value_text": 1.0,
                "validator": "float",
                "keyword": "max_threshold",
            }

        ask = DialogAsk(self, **ask_kwargs)
        ask.ShowModal()

        if self.ask_value is None:
            logger.info("Action was cancelled")
            return

        for row in range(rows):
            if self.peaklist.IsChecked(index=row):
                itemInfo = self.on_get_item_information(row)
                filename = itemInfo["document"]
                selectedText = itemInfo["ionName"]
                document = self.presenter.documentsDict[filename]
                if not ask_kwargs["keyword"] in ["min_threshold", "max_threshold"]:
                    self.peaklist.SetStringItem(
                        row, self.config.peaklistColNames[ask_kwargs["keyword"]], str(self.ask_value)
                    )

                if selectedText in document.IMS2Dions:
                    document.IMS2Dions[selectedText][ask_kwargs["keyword"]] = self.ask_value
                if selectedText in document.IMS2DCombIons:
                    document.IMS2DCombIons[selectedText][ask_kwargs["keyword"]] = self.ask_value
                if selectedText in document.IMS2DionsProcess:
                    document.IMS2DionsProcess[selectedText][ask_kwargs["keyword"]] = self.ask_value
                if selectedText in document.IMSRTCombIons:
                    document.IMSRTCombIons[selectedText][ask_kwargs["keyword"]] = self.ask_value

                # Update document
                self.data_handling.on_update_document(document, "no_refresh")

    def on_check_duplicate(self, ion_name, document):
        """Check whether ion name exist in table"""
        rows = self.peaklist.GetItemCount()

        for row in range(rows):
            ion_name_in_table = self.peaklist.GetItem(row, self.config.peaklistColNames["ion_name"]).GetText()
            document_in_table = self.peaklist.GetItem(row, self.config.peaklistColNames["filename"]).GetText()
            if (ion_name_in_table == ion_name) and (document_in_table == document):
                return True
        return False

    def get_selected_items(self):
        all_eic_datasets = [
            "Drift time (2D, EIC)",
            "Drift time (2D, processed, EIC)",
            "Drift time (2D, combined voltages, EIC)",
            "Input data",
        ]

        item_count = self.peaklist.GetItemCount()

        # generate list of document_title and dataset_name
        process_list = []
        for item_id in range(item_count):
            information = self.on_get_item_information(item_id)
            if information["select"]:
                for dataset_type in all_eic_datasets:
                    document_title = information["document"]
                    ion_name = information["ion_name"]
                    if document_title not in ["", None]:
                        # append raw
                        process_item = [document_title, dataset_type, ion_name]
                        process_list.append(process_item)

                        # append processed
                        process_item = [document_title, dataset_type, f"{ion_name} (processed)"]
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

    def on_plot(self, evt, itemID=None):
        """Plot data"""
        if itemID is not None:
            self.peaklist.item_id = itemID
        if self.peaklist.item_id is None:
            return

        itemInfo = self.on_get_item_information(self.peaklist.item_id)
        document_title = itemInfo["document"]
        rangeName = itemInfo["ionName"]

        # Check if data was extracted
        if document_title == "":
            raise MessageError("Error", "Please extract data first.")

        # Get data from dictionary
        document = self.data_handling._on_get_document(document_title)

        # Preset empty
        data, zvals, xvals, xlabel, yvals, ylabel = None, None, None, None, None, None
        # Check whether its ORIGAMI or MANUAL data type
        if document.dataType == "Type: ORIGAMI":
            if document.gotCombinedExtractedIons:
                data = document.IMS2DCombIons
            elif document.gotExtractedIons:
                data = document.IMS2Dions
        elif document.dataType == "Type: MANUAL":
            if document.gotCombinedExtractedIons:
                data = document.IMS2DCombIons
        else:
            return

        if data is None:
            raise MessageError("No data", "Could not find data for this ion")

        evtID = evt if evt is None else evt.GetId()

        if evtID == ID_ionPanel_show_mobilogram:
            xvals = data[rangeName]["yvals"]  # normally this would be the y-axis
            yvals = data[rangeName]["yvals1D"]
            xlabels = data[rangeName]["ylabels"]  # normally this would be x-axis label
            self.view.panelPlots.on_plot_1D(xvals, yvals, xlabels, set_page=True)

        elif evtID == ID_ionPanel_show_chromatogram:
            xvals = data[rangeName]["xvals"]
            yvals = data[rangeName]["yvalsRT"]
            xlabels = data[rangeName]["xlabels"]  # normally this would be x-axis label
            self.view.panelPlots.on_plot_RT(xvals, yvals, xlabels, set_page=True)

        elif evtID == ID_ionPanel_show_zoom_in_MS:
            mz_start, mz_end = get_ion_name_from_label(rangeName, as_num=True)
            mz_start = mz_start - self.config.zoomWindowX
            mz_end = mz_end + self.config.zoomWindowX

            try:
                self.view.panelPlots.on_zoom_1D_x_axis(startX=mz_start, endX=mz_end, set_page=True, plot="MS")
            except AttributeError:
                logger.error("Failed to zoom-in on an ion - most likely because there is no mass spectrum present")
                return
        else:
            # Unpack data
            zvals, xvals, xlabel, yvals, ylabel, cmap = self.presenter.get2DdataFromDictionary(
                dictionary=data[rangeName], dataType="plot", compact=False
            )

            # Warning in case  there is missing data
            if isempty(xvals) or isempty(yvals) or xvals == "" or yvals == "":
                msg = "Missing x/y-axis labels. Cannot continue! \nAdd x/y-axis labels to each file before continuing."
                print(msg)
                DialogBox(exceptionTitle="Missing data", exceptionMsg=msg, type="Error")
                return
            # Process data
            if evtID == ID_ionPanel_show_process_heatmap:
                xvals, yvals, zvals = self.data_processing.on_process_2D(xvals, yvals, zvals, return_data=True)
            # Plot data
            self.view.panelPlots.on_plot_2D(zvals, xvals, yvals, xlabel, ylabel, cmap, override=True, set_page=True)

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

    def on_save_peaklist(self, evt):
        """Save data in CSV format"""
        from utils.color import convertRGB255toHEX

        rows = self.peaklist.GetItemCount()
        if rows == 0:
            return

        data = []
        # Iterate over row and columns to get data
        for row in range(rows):
            information = self.on_get_item_information(row)
            ion_name = information["ion_name"]
            mz_start, mz_end = get_ion_name_from_label(ion_name, as_num=True)
            charge = information["charge"]
            intensity = information["intensity"]
            color = convertRGB255toHEX(information["color"])
            colormap = information["colormap"]
            alpha = information["alpha"]
            mask = information["mask"]
            label = information["label"]
            method = information["method"]
            document = information["document"]
            data.append(
                [ion_name, mz_start, mz_end, charge, intensity, color, colormap, alpha, mask, label, method, document]
            )
        fmt = ["%s", "%.4f", "%.4f", "%i", "%.4f", "%s", "%s", "%.2f", "%.2f", "%s", "%s", "%s"]
        header = [
            "ion_name",
            "mz_start",
            "mz_end",
            "charge",
            "intensity",
            "color",
            "colormap",
            "alpha",
            "mask",
            "label",
            "method",
            "document",
        ]

        self.data_handling.on_save_data_as_text(data, header, fmt, as_object=True)

    def on_find_item(self, ion_name, filename):
        """Find index of item with the provided parameters"""
        item_count = self.peaklist.GetItemCount()

        for item_id in range(item_count):
            information = self.on_get_item_information(item_id)
            if ion_name == information["ionName"] and filename == information["document"]:
                return item_id

    def on_get_item_information(self, itemID, return_list=False):
        information = self.peaklist.on_get_item_information(itemID)

        # add additional data
        information["ionName"] = information["ion_name"]
        information["color_255to1"] = convertRGB255to1(information["color"], decimals=3)

        # get document
        document = self.data_handling._on_get_document(information["document"])

        # check whether the ion has any previous information
        min_threshold, max_threshold = 0, 1
        try:
            if information["ionName"] in document.IMS2Dions:
                min_threshold = document.IMS2Dions[information["ionName"]].get("min_threshold", 0)
                max_threshold = document.IMS2Dions[information["ionName"]].get("max_threshold", 1)
        except AttributeError:
            pass

        datasets = []
        if information["ionName"] in document.IMS2Dions:
            datasets.append("Drift time (2D, EIC)")
        if information["ionName"] in document.IMS2DionsProcess:
            datasets.append("Drift time (2D, processed, EIC)")
        if information["ionName"] in document.IMS2DCombIons:
            datasets.append("Drift time (2D, combined voltages, EIC)")

        if not datasets:
            datasets = ["Not extracted yet"]

        information["min_threshold"] = min_threshold
        information["max_threshold"] = max_threshold
        information["datasets"] = datasets

        # Check whether the ion has combined ions
        parameters = None
        try:
            parameters = document.IMS2DCombIons[information["ionName"]].get("parameters", None)
        except (KeyError, AttributeError):
            pass
        information["parameters"] = parameters

        return information

    def on_get_value(self, value_type="color"):
        information = self.on_get_item_information(self.peaklist.item_id)

        if value_type == "ion_name":
            return information["ion_name"]
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
        elif value_type == "method":
            return information["method"]
        elif value_type == "document":
            return information["document"]
        elif value_type == "label":
            return information["label"]
        elif value_type == "ionName":
            return information["ionName"]

    def on_find_and_update_values(self, ion_name, **kwargs):
        item_count = self.peaklist.GetItemCount()

        for item_id in range(item_count):
            information = self.on_get_item_information(item_id)
            if ion_name == information["ionName"]:
                for keyword in kwargs:
                    self.on_update_value_in_peaklist(item_id, keyword, kwargs[keyword])

    def on_update_value_in_peaklist(self, item_id, value_type, value):

        if value_type == "ion_name":
            self.peaklist.SetStringItem(item_id, self.config.peaklistColNames["ion_name"], str(value))
        elif value_type == "charge":
            self.peaklist.SetStringItem(item_id, self.config.peaklistColNames["charge"], str(value))
        elif value_type == "intensity":
            self.peaklist.SetStringItem(item_id, self.config.peaklistColNames["intensity"], str(value))
        elif value_type == "color":
            color_255, color_1, font_color = value
            self.peaklist.SetItemBackgroundColour(item_id, color_255)
            self.peaklist.SetStringItem(item_id, self.config.peaklistColNames["color"], str(color_1))
            self.peaklist.SetItemTextColour(item_id, font_color)
        elif value_type == "color_text":
            self.peaklist.SetItemBackgroundColour(item_id, value)
            self.peaklist.SetStringItem(item_id, self.config.peaklistColNames["color"], str(convertRGB255to1(value)))
            self.peaklist.SetItemTextColour(item_id, determineFontColor(value, return_rgb=True))
        elif value_type == "colormap":
            self.peaklist.SetStringItem(item_id, self.config.peaklistColNames["colormap"], str(value))
        elif value_type == "alpha":
            self.peaklist.SetStringItem(item_id, self.config.peaklistColNames["alpha"], str(value))
        elif value_type == "mask":
            self.peaklist.SetStringItem(item_id, self.config.peaklistColNames["mask"], str(value))
        elif value_type == "label":
            self.peaklist.SetStringItem(item_id, self.config.peaklistColNames["label"], str(value))
        elif value_type == "method":
            self.peaklist.SetStringItem(item_id, self.config.peaklistColNames["method"], str(value))
        elif value_type == "document":
            self.peaklist.SetStringItem(item_id, self.config.peaklistColNames["filename"], str(value))

    def on_open_editor(self, evt):
        from gui_elements.panel_modify_item_settings import PanelModifyItemSettings

        if self.peaklist.item_id is None:
            logger.warning("Please select an item")
            return

        if self.peaklist.item_id < 0:
            print("Please select item in the table first.")
            return

        information = self.on_get_item_information(self.peaklist.item_id)

        self.item_editor = PanelModifyItemSettings(self, self.presenter, self.config, **information)
        self.item_editor.Centre()
        self.item_editor.Show()

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

        if itemID is None:
            itemID = self.peaklist.item_id

        if itemID is None:
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

            self.on_update_value_in_peaklist(itemID, "color_text", color_255)
            if give_value:
                return color_255

    def on_get_color(self, evt):
        dlg = DialogColorPicker(self, self.config.customColors)
        if dlg.ShowModal() == "ok":
            color_255, color_1, font_color = dlg.GetChosenColour()
            self.config.customColors = dlg.GetCustomColours()

            return color_255, color_1, font_color
        else:
            return None, None, None

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
                self.peaklist.SetStringItem(row, self.config.peaklistColNames["colormap"], str(colormap))

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

        if evt.GetId() == ID_ionPanel_changeColorBatch_palette:
            colors = self.view.panelPlots.on_change_color_palette(None, n_colors=check_count, return_colors=True)
        elif evt.GetId() == ID_ionPanel_changeColorBatch_color:
            __, color_1, __ = self.on_get_color(None)
            if color_1 is None:
                return
            colors = [color_1] * check_count
        else:
            colors = self.view.panelPlots.on_get_colors_from_colormap(n_colors=check_count)

        check_count = 0
        for row in range(self.peaklist.GetItemCount()):
            if self.peaklist.IsChecked(index=row):
                self.peaklist.item_id = row
                color_255 = convertRGB1to255(colors[check_count])
                self.on_update_value_in_peaklist(row, "color_text", color_255)
                check_count += 1

            # update document
            try:
                self.on_update_document(evt=None)
            except TypeError:
                print("Please select an item")

    def on_update_document(self, evt, itemInfo=None):
        """Update document data"""

        # get item info
        if itemInfo is None:
            itemInfo = self.on_get_item_information(self.peaklist.item_id)

        # get item
        document = self.data_handling._on_get_document(itemInfo["document"])

        processed_name = "{} (processed)".format(itemInfo["ionName"])
        keywords = ["color", "colormap", "alpha", "mask", "label", "min_threshold", "max_threshold", "charge"]

        if itemInfo["ionName"] in document.IMS2Dions:
            for keyword in keywords:
                keyword_name = self.keyword_alias.get(keyword, keyword)
                document.IMS2Dions[itemInfo["ionName"]][keyword_name] = itemInfo[keyword]
                if processed_name in document.IMS2Dions:
                    document.IMS2Dions[processed_name][keyword_name] = itemInfo[keyword]

        if f"{itemInfo['ionName']} (processed)" in document.IMS2Dions:
            for keyword in keywords:
                keyword_name = self.keyword_alias.get(keyword, keyword)
                document.IMS2Dions[itemInfo["ionName"]][keyword_name] = itemInfo[keyword]
                if processed_name in document.IMS2Dions:
                    document.IMS2Dions[processed_name][keyword_name] = itemInfo[keyword]

        if itemInfo["ionName"] in document.IMS2DCombIons:
            for keyword in keywords:
                keyword_name = self.keyword_alias.get(keyword, keyword)
                document.IMS2DCombIons[itemInfo["ionName"]][keyword_name] = itemInfo[keyword]
                if processed_name in document.IMS2DCombIons:
                    document.IMS2DCombIons[processed_name][keyword_name] = itemInfo[keyword]

        if itemInfo["ionName"] in document.IMS2DionsProcess:
            for keyword in keywords:
                keyword_name = self.keyword_alias.get(keyword, keyword)
                document.IMS2DionsProcess[itemInfo["ionName"]][keyword_name] = itemInfo[keyword]
                if processed_name in document.IMS2DionsProcess:
                    document.IMS2DionsProcess[processed_name][keyword_name] = itemInfo[keyword]

        if itemInfo["ionName"] in document.IMSRTCombIons:
            for keyword in keywords:
                keyword_name = self.keyword_alias.get(keyword, keyword)
                document.IMSRTCombIons[itemInfo["ionName"]][keyword_name] = itemInfo[keyword]
                if processed_name in document.IMSRTCombIons:
                    document.IMSRTCombIons[processed_name][keyword_name] = itemInfo[keyword]

        # Update document
        self.data_handling.on_update_document(document, "no_refresh")

    def on_remove_deleted_item(self, document):
        """
        document : document object
            title of the document to be removed from the list
        """
        row = self.peaklist.GetItemCount() - 1
        while row >= 0:
            info = self.on_get_item_information(itemID=row)
            if info["document"] == document:
                self.peaklist.DeleteItem(row)
            row -= 1

    def on_open_ORIGAMI_MS_panel(self, evt):
        document = self.data_handling._get_document_of_type(["Type: ORIGAMI"], allow_creation=False)
        if document is None:
            raise MessageError("Error", "Please create/load ORIGAMI document first")

        self.document_tree.on_action_ORIGAMI_MS(None, document.title)

    def on_load_peaklist(self, evt):
        """This function opens a formatted CSV file with peaks"""

        document = self.data_handling._get_document_of_type(
            ["Type: MANUAL", "Type: ORIGAMI", "Type: Infrared"], allow_creation=False
        )
        if document is None:
            raise MessageError("Error", "Please load/create a document before loading peaklist")

        document_title = document.title
        peaklist = self.data_handling.on_load_user_list_fcn(data_type="peaklist")

        for add_dict in peaklist:
            add_dict["document"] = document_title
            self.on_add_to_table(add_dict, check_color=False)
        self.peaklist.on_remove_duplicates()
        self.view.on_toggle_panel(evt=ID_window_ionList, check=True)

    def on_restore_to_peaklist(self, evt):
        document = self.data_handling._get_document_of_type(
            ["Type: MANUAL", "Type: ORIGAMI", "Type: Infrared"], allow_creation=False
        )
        if document is not None:
            self.data_handling._load_document_data_peaklist(document)

    def on_check_selected(self, evt):
        """Check current item when letter S is pressed on the keyboard"""
        if self.peaklist.item_id is None:
            return

        check = not self.peaklist.IsChecked(index=self.peaklist.item_id)
        self.peaklist.CheckItem(self.peaklist.item_id, check=check)

    def on_extract_all(self, evt):
        self.data_handling.on_extract_2D_from_mass_range_fcn(None, extract_type="all")

    def on_extract_selected(self, evt):
        self.data_handling.on_extract_2D_from_mass_range_fcn(None, extract_type="selected")

    def on_extract_new(self, evt):
        self.data_handling.on_extract_2D_from_mass_range_fcn(None, extract_type="new")

    def on_add_to_table(self, add_dict, check_color=True):

        # get color
        color = add_dict.get("color", next(self.config.custom_color_cycle))
        # check for duplicate color
        if check_color:
            color = self.on_check_duplicate_colors(color)

        # add to peaklist
        self.peaklist.Append(
            [
                "",
                str(add_dict.get("ion_name", "")),
                str(add_dict.get("charge", "")),
                str(add_dict.get("mz_ymax", "")),
                str(roundRGB(convertRGB255to1(color))),
                str(add_dict.get("colormap", next(self.config.overlay_cmap_cycle))),
                str(add_dict.get("alpha", "")),
                str(add_dict.get("mask", "")),
                str(add_dict.get("label", "")),
                str(add_dict.get("method", "")),
                str(add_dict.get("document", "")),
            ]
        )
        self.peaklist.SetItemBackgroundColour(self.peaklist.GetItemCount() - 1, color)
        self.peaklist.SetItemTextColour(self.peaklist.GetItemCount() - 1, determineFontColor(color, return_rgb=True))

    def on_check_duplicate_colors(self, new_color):
        """Check whether newly assigned color is already in the table and if so, return a different one"""
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

            return randomColorGenerator(return_as_255=True)

        return new_color

    def on_delete_item(self, evt):
        """Delete one item from the file"""

        itemInfo = self.on_get_item_information(itemID=self.peaklist.item_id)
        dlg = DialogBox(
            "Delete item from document",
            "Are you sure you would like to delete {} from {}?\nThis action cannot be undone.".format(
                itemInfo["ionName"], itemInfo["document"]
            ),
            "Question",
        )
        if dlg == wx.ID_NO:
            print("The operation was cancelled")
            return

        document = self.data_handling._on_get_document(itemInfo["document"])

        __, __ = self.view.panelDocuments.documents.on_delete_data__heatmap(
            document, itemInfo["document"], delete_type="heatmap.all.one", ion_name=itemInfo["ionName"]
        )

    def on_delete_selected(self, evt):
        """Delete selected item(s) from the file"""

        itemID = self.peaklist.GetItemCount() - 1
        while itemID >= 0:
            if self.peaklist.IsChecked(index=itemID):
                itemInfo = self.on_get_item_information(itemID=itemID)
                msg = "Are you sure you would like to delete {} from {}?\nThis action cannot be undone.".format(
                    itemInfo["ionName"], itemInfo["document"]
                )
                dlg = DialogBox(exceptionMsg=msg, type="Question")
                if dlg == wx.ID_NO:
                    print("The operation was cancelled")
                    itemID -= 1
                    continue

                document = self.data_handling._on_get_document(itemInfo["document"])
                __, __ = self.view.panelDocuments.documents.on_delete_data__heatmap(
                    document, itemInfo["document"], delete_type="heatmap.all.one", ion_name=itemInfo["ionName"]
                )
            itemID -= 1

    def on_delete_all(self, evt):
        """Delete all items from all files"""
        msg = "Are you sure you would like to delete all ions from all documents?\nThis action cannot be undone."
        dlg = DialogBox(exceptionMsg=msg, type="Question")
        if dlg == wx.ID_NO:
            print("The operation was cancelled")
            return

        itemID = self.peaklist.GetItemCount() - 1
        while itemID >= 0:
            itemInfo = self.on_get_item_information(itemID=itemID)
            document = self.data_handling._on_get_document(itemInfo["document"])
            __, __ = self.view.panelDocuments.documents.on_delete_data__heatmap(
                document, itemInfo["document"], delete_type="heatmap.all.one", ion_name=itemInfo["ionName"]
            )
            itemID -= 1

    def delete_row_from_table(self, delete_item_name=None, delete_document_title=None):
        rows = self.peaklist.GetItemCount() - 1
        while rows >= 0:
            itemInfo = self.on_get_item_information(rows)

            if itemInfo["ionName"] == delete_item_name and itemInfo["document"] == delete_document_title:
                self.peaklist.DeleteItem(rows)
                rows = 0
                return
            elif delete_item_name is None and itemInfo["document"] == delete_document_title:
                self.peaklist.DeleteItem(rows)
            rows -= 1
