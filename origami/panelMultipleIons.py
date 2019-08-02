# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import csv
import logging
from ast import literal_eval

import wx
from gui_elements.dialog_ask import DialogAsk
from gui_elements.dialog_color_picker import DialogColorPicker
from gui_elements.misc_dialogs import DialogBox
from ids import ID_addIonsMenu
from ids import ID_addManyIonsCSV
from ids import ID_addNewOverlayDoc
from ids import ID_combineCEscans
from ids import ID_combineCEscansSelectedIons
from ids import ID_exportAllAsCSV_ion
from ids import ID_exportAllAsImage_ion
from ids import ID_exportSelectedAsCSV_ion
from ids import ID_exportSeletedAsImage_ion
from ids import ID_extractAllIons
from ids import ID_extractIonsMenu
from ids import ID_extractNewIon
from ids import ID_extractSelectedIon
from ids import ID_highlightRectAllIons
from ids import ID_ionPanel_about_info
from ids import ID_ionPanel_addToDocument
from ids import ID_ionPanel_annotate_alpha
from ids import ID_ionPanel_annotate_charge_state
from ids import ID_ionPanel_annotate_mask
from ids import ID_ionPanel_annotate_max_threshold
from ids import ID_ionPanel_annotate_min_threshold
from ids import ID_ionPanel_assignColor
from ids import ID_ionPanel_automaticExtract
from ids import ID_ionPanel_automaticOverlay
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
from ids import ID_ionPanel_edit_all
from ids import ID_ionPanel_edit_selected
from ids import ID_ionPanel_editItem
from ids import ID_ionPanel_normalize1D
from ids import ID_ionPanel_show_chromatogram
from ids import ID_ionPanel_show_heatmap
from ids import ID_ionPanel_show_mobiligram
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
from ids import ID_overlayIonsMenu
from ids import ID_overlayMZfromList
from ids import ID_overlayMZfromList1D
from ids import ID_overlayMZfromListRT
from ids import ID_overrideCombinedMenu
from ids import ID_processAllIons
from ids import ID_processIonsMenu
from ids import ID_processSaveMenu
from ids import ID_processSelectedIons
from ids import ID_removeIonsMenu
from ids import ID_saveIonListCSV
from ids import ID_saveIonsMenu
from ids import ID_selectOverlayMethod
from ids import ID_showIonsMenu
from ids import ID_useProcessedCombinedMenu
from ids import ID_window_ionList
from pandas import read_csv
from styles import ListCtrl
from styles import makeMenuItem
from styles import makeTooltip
from toolbox import checkExtension
from utils.check import isempty
from utils.color import convertRGB1to255
from utils.color import convertRGB255to1
from utils.color import determineFontColor
from utils.color import randomColorGenerator
from utils.color import roundRGB
from utils.converters import str2num
from utils.exceptions import MessageError
from utils.labels import get_ion_name_from_label
from utils.random import get_random_int

logger = logging.getLogger("origami")


class panelMultipleIons(wx.Panel):
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

        if self.plotAutomatically:
            self.combo.Bind(wx.EVT_COMBOBOX, self.on_overlay_heatmap)

        # add a couple of accelerators
        accelerators = [
            (wx.ACCEL_NORMAL, ord("A"), ID_ionPanel_addToDocument),
            (wx.ACCEL_NORMAL, ord("C"), ID_ionPanel_assignColor),
            (wx.ACCEL_NORMAL, ord("E"), ID_ionPanel_editItem),
            (wx.ACCEL_NORMAL, ord("H"), ID_highlightRectAllIons),
            (wx.ACCEL_NORMAL, ord("M"), ID_ionPanel_show_mobiligram),
            (wx.ACCEL_NORMAL, ord("N"), ID_ionPanel_normalize1D),
            (wx.ACCEL_NORMAL, ord("O"), ID_overrideCombinedMenu),
            (wx.ACCEL_NORMAL, ord("P"), ID_useProcessedCombinedMenu),
            (wx.ACCEL_NORMAL, ord("S"), ID_ionPanel_check_selected),
            (wx.ACCEL_NORMAL, ord("X"), ID_ionPanel_check_all),
            (wx.ACCEL_NORMAL, ord("Z"), ID_ionPanel_show_zoom_in_MS),
            (wx.ACCEL_NORMAL, wx.WXK_DELETE, ID_ionPanel_delete_rightClick),
        ]
        self.SetAcceleratorTable(wx.AcceleratorTable(accelerators))

        wx.EVT_MENU(self, ID_ionPanel_editItem, self.on_open_editor)
        wx.EVT_MENU(self, ID_ionPanel_addToDocument, self.onCheckTool)
        wx.EVT_MENU(self, ID_overrideCombinedMenu, self.onCheckTool)
        wx.EVT_MENU(self, ID_useProcessedCombinedMenu, self.onCheckTool)
        wx.EVT_MENU(self, ID_ionPanel_normalize1D, self.onCheckTool)
        wx.EVT_MENU(self, ID_ionPanel_assignColor, self.on_assign_color)
        wx.EVT_MENU(self, ID_ionPanel_show_zoom_in_MS, self.on_plot)
        wx.EVT_MENU(self, ID_ionPanel_show_mobiligram, self.on_plot)
        wx.EVT_MENU(self, ID_ionPanel_check_selected, self.on_check_selected)
        wx.EVT_MENU(self, ID_ionPanel_delete_rightClick, self.on_delete_item)

    def _setup_handling_and_processing(self):
        self.data_processing = self.view.data_processing
        self.data_handling = self.view.data_handling
        self.document_tree = self.presenter.view.panelDocuments.documents

    def on_open_info_panel(self, evt):
        pass

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

        # Make bindings
        self.Bind(wx.EVT_BUTTON, self.menu_add_tools, id=ID_addIonsMenu)
        self.Bind(wx.EVT_BUTTON, self.menu_remove_tools, id=ID_removeIonsMenu)
        self.Bind(wx.EVT_BUTTON, self.menu_extract_tools, id=ID_extractIonsMenu)
        self.Bind(wx.EVT_BUTTON, self.menu_process_tools, id=ID_processIonsMenu)
        self.Bind(wx.EVT_BUTTON, self.menu_save_tools, id=ID_saveIonsMenu)
        self.Bind(wx.EVT_BUTTON, self.menu_annotate_tools, id=ID_showIonsMenu)
        self.Bind(wx.EVT_BUTTON, self.menu_overlay_tools, id=ID_overlayIonsMenu)
        self.Bind(wx.EVT_BUTTON, self.on_open_info_panel, id=ID_ionPanel_about_info)

        self.add_btn = wx.BitmapButton(
            self,
            ID_addIonsMenu,
            self.icons.iconsLib["add16"],
            size=(18, 18),
            style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL,
        )
        self.add_btn.SetToolTip(makeTooltip("Add..."))

        self.remove_btn = wx.BitmapButton(
            self,
            ID_removeIonsMenu,
            self.icons.iconsLib["remove16"],
            size=(18, 18),
            style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL,
        )
        self.remove_btn.SetToolTip(makeTooltip("Remove..."))

        self.annotate_btn = wx.BitmapButton(
            self,
            ID_showIonsMenu,
            self.icons.iconsLib["annotate16"],
            size=(18, 18),
            style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL,
        )
        self.annotate_btn.SetToolTip(makeTooltip("Annotate..."))

        self.extract_btn = wx.BitmapButton(
            self,
            ID_extractIonsMenu,
            self.icons.iconsLib["extract16"],
            size=(18, 18),
            style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL,
        )
        self.extract_btn.SetToolTip(makeTooltip("Extract..."))

        self.process_btn = wx.BitmapButton(
            self,
            ID_processIonsMenu,
            self.icons.iconsLib["process16"],
            size=(18, 18),
            style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL,
        )
        self.process_btn.SetToolTip(makeTooltip("Process..."))

        self.overlay_btn = wx.BitmapButton(
            self,
            ID_overlayIonsMenu,
            self.icons.iconsLib["overlay16"],
            size=(18, 18),
            style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL,
        )
        self.overlay_btn.SetToolTip(makeTooltip("Overlay selected ions..."))

        self.combo = wx.ComboBox(
            self, ID_selectOverlayMethod, size=(105, -1), choices=self.config.overlayChoices, style=wx.CB_READONLY
        )
        self.combo.SetStringSelection(self.config.overlayMethod)

        self.save_btn = wx.BitmapButton(
            self,
            ID_saveIonsMenu,
            self.icons.iconsLib["save16"],
            size=(18, 18),
            style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL,
        )
        self.save_btn.SetToolTip(makeTooltip("Save..."))

        vertical_line_1 = wx.StaticLine(self, -1, style=wx.LI_VERTICAL)

        self.info_btn = wx.BitmapButton(
            self,
            ID_ionPanel_about_info,
            self.icons.iconsLib["info16"],
            size=(18, 18),
            style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL,
        )
        self.info_btn.SetToolTip(makeTooltip("Information..."))

        # button grid
        btn_grid_vert = wx.GridBagSizer(2, 2)
        x = 0
        btn_grid_vert.Add(
            self.add_btn, (x, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL
        )
        btn_grid_vert.Add(
            self.remove_btn, (x, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL
        )
        btn_grid_vert.Add(
            self.annotate_btn, (x, 3), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL
        )
        btn_grid_vert.Add(
            self.extract_btn, (x, 4), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL
        )
        btn_grid_vert.Add(
            self.process_btn, (x, 5), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL
        )
        btn_grid_vert.Add(
            self.overlay_btn, (x, 6), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL
        )
        btn_grid_vert.Add(
            self.combo, (x, 7), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL
        )
        btn_grid_vert.Add(
            self.save_btn, (x, 8), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL
        )
        btn_grid_vert.Add(vertical_line_1, (x, 9), wx.GBSpan(1, 1), flag=wx.EXPAND)
        btn_grid_vert.Add(
            self.info_btn, (x, 10), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL
        )

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
                self.item_editor.on_update_gui(self.OnGetItemInformation(self.peaklist.item_id))

    def onRenameItem(self, old_name, new_name, item_type="Document"):
        for row in range(self.peaklist.GetItemCount()):
            itemInfo = self.OnGetItemInformation(itemID=row)
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

        # Menu events
        self.Bind(wx.EVT_MENU, self.on_plot, id=ID_ionPanel_show_zoom_in_MS)
        self.Bind(wx.EVT_MENU, self.on_plot, id=ID_ionPanel_show_mobiligram)
        self.Bind(wx.EVT_MENU, self.on_plot, id=ID_ionPanel_show_chromatogram)
        self.Bind(wx.EVT_MENU, self.on_plot, id=ID_ionPanel_show_heatmap)
        self.Bind(wx.EVT_MENU, self.on_plot, id=ID_ionPanel_show_process_heatmap)
        self.Bind(wx.EVT_MENU, self.on_open_editor, id=ID_ionPanel_editItem)
        self.Bind(wx.EVT_MENU, self.on_assign_color, id=ID_ionPanel_assignColor)
        self.Bind(wx.EVT_MENU, self.on_delete_item, id=ID_ionPanel_delete_rightClick)

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
                id=ID_ionPanel_show_mobiligram,
                text="Show mobiligram\tM",
                bitmap=self.icons.iconsLib["mobiligram_16"],
            )
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu, id=ID_ionPanel_show_heatmap, text="Show heatmap", bitmap=self.icons.iconsLib["heatmap_16"]
            )
        )
        menu.Append(ID_ionPanel_show_process_heatmap, "Process and show heatmap")
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
                text="Highlight extracted items on MS plot\tH",
                bitmap=self.icons.iconsLib["highlight_16"],
            )
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_ionPanel_annotate_charge_state,
                text="Assign charge state to selected ions",
                bitmap=self.icons.iconsLib["assign_charge_16"],
            )
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_ionPanel_annotate_alpha,
                text="Assign transparency value to selected ions",
                bitmap=self.icons.iconsLib["transparency_16"],
            )
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_ionPanel_annotate_mask,
                text="Assign mask value to selected ions",
                bitmap=self.icons.iconsLib["mask_16"],
            )
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_ionPanel_annotate_min_threshold,
                text="Assign minimum threshold to selected ions",
                bitmap=self.icons.iconsLib["min_threshold_16"],
            )
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_ionPanel_annotate_max_threshold,
                text="Assign maximum threshold to selected ions",
                bitmap=self.icons.iconsLib["max_threshold_16"],
            )
        )
        menu.AppendSeparator()
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_ionPanel_changeColorBatch_color,
                text="Assign color for selected items",
                bitmap=self.icons.iconsLib["color_panel_16"],
            )
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_ionPanel_changeColorBatch_palette,
                text="Color selected items using color palette",
                bitmap=self.icons.iconsLib["blank_16"],
            )
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_ionPanel_changeColorBatch_colormap,
                text="Color selected items using colormap",
                bitmap=self.icons.iconsLib["blank_16"],
            )
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_ionPanel_changeColormapBatch,
                text="Assign new colormap for selected items",
                bitmap=self.icons.iconsLib["randomize_16"],
            )
        )

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def menu_add_tools(self, evt):
        # TODO: add "Restore items from document"
        self.Bind(wx.EVT_MENU, self.on_open_peak_list, id=ID_addManyIonsCSV)

        menu = wx.Menu()
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_addManyIonsCSV,
                text="Add list of ions (.csv/.txt)\tCtrl+L",
                bitmap=self.icons.iconsLib["filelist_16"],
                help_text="Format: min, max, charge (optional), label (optional), color (optional)",
            )
        )
        #         menu.AppendSeparator()
        #         menu.AppendItem(makeMenuItem(parent=menu, id=ID_addNewOverlayDoc,
        #                                      text='Create blank COMPARISON document\tAlt+D',
        #                                      bitmap=self.icons.iconsLib['new_document_16']))
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def menu_extract_tools(self, evt):
        # TODO: add Extract chromatographic data only
        # TODO: add extract mobilogram data only

        self.Bind(wx.EVT_MENU, self.onCheckTool, id=ID_ionPanel_automaticExtract)
        self.Bind(wx.EVT_MENU, self.on_extract_all, id=ID_extractAllIons)
        self.Bind(wx.EVT_MENU, self.on_extract_selected, id=ID_extractSelectedIon)
        self.Bind(wx.EVT_MENU, self.on_extract_new, id=ID_extractNewIon)

        menu = wx.Menu()
        self.automaticExtract_check = menu.AppendCheckItem(
            ID_ionPanel_automaticExtract, "Extract data automatically", help="Ions will be extracted automatically"
        )
        self.automaticExtract_check.Check(self.extractAutomatically)
        menu.AppendSeparator()
        menu.Append(ID_extractNewIon, "Extract data for new ions")
        menu.Append(ID_extractSelectedIon, "Extract data for selected ions")
        menu.Append(ID_extractAllIons, "Extract for all ions\tAlt+E")
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def menu_overlay_tools(self, evt):

        self.Bind(wx.EVT_TOOL, self.on_overlay_heatmap, id=ID_overlayMZfromList)
        self.Bind(wx.EVT_TOOL, self.on_overlay_mobiligram, id=ID_overlayMZfromList1D)
        self.Bind(wx.EVT_TOOL, self.on_overlay_chromatogram, id=ID_overlayMZfromListRT)
        self.Bind(wx.EVT_MENU, self.onCheckTool, id=ID_useProcessedCombinedMenu)
        self.Bind(wx.EVT_TOOL, self.onCheckTool, id=ID_ionPanel_addToDocument)
        self.Bind(wx.EVT_TOOL, self.onCheckTool, id=ID_ionPanel_normalize1D)
        self.Bind(wx.EVT_TOOL, self.onCheckTool, id=ID_ionPanel_automaticOverlay)
        self.Bind(wx.EVT_MENU, self.on_add_blank_document_overlay, id=ID_addNewOverlayDoc)

        menu = wx.Menu()
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_addNewOverlayDoc,
                text="Create blank COMPARISON document\tAlt+D",
                bitmap=self.icons.iconsLib["new_document_16"],
            )
        )
        menu.AppendSeparator()
        self.addToDocument_check = menu.AppendCheckItem(
            ID_ionPanel_addToDocument,
            "Add overlay plots to document\tA",
            help="Add overlay results to comparison document",
        )
        self.addToDocument_check.Check(self.addToDocument)
        menu.AppendSeparator()
        self.normalize1D_check = menu.AppendCheckItem(
            ID_ionPanel_normalize1D,
            "Normalize mobiligram/chromatogram dataset\tN",
            help="Normalize mobiligram/chromatogram before overlaying",
        )
        self.normalize1D_check.Check(self.normalize1D)
        menu.Append(ID_overlayMZfromList1D, "Overlay mobiligrams (selected)")
        menu.Append(ID_overlayMZfromListRT, "Overlay chromatograms (selected)")
        menu.AppendSeparator()
        self.useProcessed_check = menu.AppendCheckItem(
            ID_useProcessedCombinedMenu,
            "Use processed data (when available)\tP",
            help="When checked, processed data is used in the overlay (2D) plots.",
        )
        self.useProcessed_check.Check(self.config.overlay_usedProcessed)
        menu.AppendSeparator()
        self.automaticPlot_check = menu.AppendCheckItem(
            ID_ionPanel_automaticOverlay, "Overlay automatically", help="Ions will be extracted automatically"
        )
        self.automaticPlot_check.Check(self.plotAutomatically)
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_overlayMZfromList,
                text="Overlay heatmaps (selected)\tAlt+Q",
                bitmap=self.icons.iconsLib["heatmap_grid_16"],
            )
        )
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

        self.Bind(
            wx.EVT_MENU, self.data_processing.on_combine_origami_collision_voltages, id=ID_combineCEscansSelectedIons
        )
        self.Bind(wx.EVT_MENU, self.data_processing.on_combine_origami_collision_voltages, id=ID_combineCEscans)
        self.Bind(wx.EVT_MENU, self.presenter.onProcessMultipleIonsIons, id=ID_processSelectedIons)
        self.Bind(wx.EVT_MENU, self.presenter.onProcessMultipleIonsIons, id=ID_processAllIons)
        self.Bind(wx.EVT_MENU, self.onCheckTool, id=ID_overrideCombinedMenu)

        menu = wx.Menu()
        menu.Append(ID_processSelectedIons, "Process selected ions")
        menu.Append(ID_processAllIons, "Process all ions")
        menu.AppendSeparator()
        help_msg = (
            "When checked, any previous results for the selected item(s) will be overwritten"
            + " based on the current parameters."
        )
        self.override_check = menu.AppendCheckItem(ID_overrideCombinedMenu, "Overwrite results\tO", help=help_msg)
        self.override_check.Check(self.config.overrideCombine)
        help_msg = (
            "When checked, collision voltage scans will be combined based on parameters present"
            + " in the ORIGAMI document."
        )
        menu.Append(ID_combineCEscansSelectedIons, "Combine collision voltages for selected items (ORIGAMI-MS)")
        menu.Append(ID_combineCEscans, "Combine collision voltages for all items (ORIGAMI-MS)\tAlt+C")
        menu.AppendSeparator()

        menu_action_extract_spectrum = makeMenuItem(
            parent=menu, text="Extract mass spectra for each collision voltage (ORIGAMI-MS)"
        )
        menu.AppendItem(menu_action_extract_spectrum)
        self.Bind(wx.EVT_MENU, self.document_tree.on_action_ORIGAMI_MS, menu_action_extract_spectrum)

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def menu_save_tools(self, evt):
        self.Bind(wx.EVT_MENU, self.on_save_peaklist, id=ID_saveIonListCSV)
        #         self.Bind(wx.EVT_MENU, self.onSaveAsData, id=ID_exportAllAsCSV_ion)

        self.Bind(wx.EVT_MENU, self.onCheckTool, id=ID_processSaveMenu)

        saveImageLabel = "".join(["Save all figures (.", self.config.imageFormat, ")"])
        saveSelectedImageLabel = "".join(["Save selected figure (.", self.config.imageFormat, ")"])

        saveTextLabel = "".join(["Save all 2D (", self.config.saveDelimiterTXT, " delimited)"])
        saveSelectedTextLabel = "".join(["Save selected 2D (", self.config.saveDelimiterTXT, " delimited)"])

        menu = wx.Menu()
        menu.Append(ID_saveIonListCSV, "Export peak list as .csv")

        self.processSave_check = menu.AppendCheckItem(
            ID_processSaveMenu, "Process before saving", help="Process each item before saving"
        )
        self.processSave_check.Check(self.process)
        menu.AppendSeparator()
        menu.Append(ID_exportSeletedAsImage_ion, saveSelectedImageLabel)
        menu.Append(ID_exportAllAsImage_ion, saveImageLabel)
        menu.AppendSeparator()
        menu.Append(ID_exportSelectedAsCSV_ion, saveSelectedTextLabel)
        menu.Append(ID_exportAllAsCSV_ion, saveTextLabel)
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def onCheckTool(self, evt):
        """ Check/uncheck menu item """

        evtID = evt.GetId()

        # check which event was triggered
        if evtID == ID_overrideCombinedMenu:
            self.config.overrideCombine = not self.config.overrideCombine
            args = (
                "Peak list panel: 'Override' combined IM-MS data was switched to %s" % self.config.overrideCombine,
                4,
            )
            self.presenter.onThreading(evt, args, action="updateStatusbar")

        if evtID == ID_processSaveMenu:
            self.process = not self.process
            args = ("Override was switched to %s" % self.override, 4)
            self.presenter.onThreading(evt, args, action="updateStatusbar")

        if evtID == ID_useProcessedCombinedMenu:
            self.config.overlay_usedProcessed = not self.config.overlay_usedProcessed
            args = ("Peak list panel: Using processing data was switched to %s" % self.config.overlay_usedProcessed, 4)
            self.presenter.onThreading(evt, args, action="updateStatusbar")

        if evtID == ID_ionPanel_addToDocument:
            self.addToDocument = not self.addToDocument
            args = ("Adding data to comparison document was set to: %s" % self.addToDocument, 4)
            self.presenter.onThreading(evt, args, action="updateStatusbar")

        if evtID == ID_ionPanel_normalize1D:
            self.normalize1D = not self.normalize1D
            args = ("Normalization of mobiligrams/chromatograms was set to: %s" % self.normalize1D, 4)
            self.presenter.onThreading(evt, args, action="updateStatusbar")

        if evtID == ID_ionPanel_automaticExtract:
            self.extractAutomatically = not self.extractAutomatically
            args = ("Automatic extraction was set to: {}".format(self.extractAutomatically), 4)
            self.presenter.onThreading(evt, args, action="updateStatusbar")

        if evtID == ID_ionPanel_automaticOverlay:
            self.plotAutomatically = not self.plotAutomatically
            args = ("Automatic 2D overlaying was set to: {}".format(self.plotAutomatically), 4)
            self.presenter.onThreading(evt, args, action="updateStatusbar")

            if self.plotAutomatically:
                self.combo.Bind(wx.EVT_COMBOBOX, self.on_overlay_heatmap)
            else:
                self.combo.Unbind(wx.EVT_COMBOBOX)

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

    def onUpdateOverlayMethod(self, evt):
        self.config.overlayMethod = self.combo.GetStringSelection()

        if evt is not None:
            evt.Skip()

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
                itemInfo = self.OnGetItemInformation(row)
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

    def on_plot(self, evt):
        """
        This function extracts 2D array and plots it in 2D/3D
        """
        itemInfo = self.OnGetItemInformation(self.peaklist.item_id)
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

        if evt.GetId() == ID_ionPanel_show_mobiligram:
            xvals = data[rangeName]["yvals"]  # normally this would be the y-axis
            yvals = data[rangeName]["yvals1D"]
            xlabels = data[rangeName]["ylabels"]  # normally this would be x-axis label
            self.view.panelPlots.on_plot_1D(xvals, yvals, xlabels, set_page=True)

        elif evt.GetId() == ID_ionPanel_show_chromatogram:
            xvals = data[rangeName]["xvals"]
            yvals = data[rangeName]["yvalsRT"]
            xlabels = data[rangeName]["xlabels"]  # normally this would be x-axis label
            self.view.panelPlots.on_plot_RT(xvals, yvals, xlabels, set_page=True)

        elif evt.GetId() == ID_ionPanel_show_zoom_in_MS:
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
            if evt.GetId() == ID_ionPanel_show_process_heatmap:
                xvals, yvals, zvals = self.data_processing.on_process_2D(xvals, yvals, zvals, return_data=True)
            # Plot data
            self.view.panelPlots.on_plot_2D(zvals, xvals, yvals, xlabel, ylabel, cmap, override=True, set_page=True)

    def on_save_peaklist(self, evt):
        """Save data in CSV format"""
        from utils.color import convertRGB255toHEX

        columns = self.peaklist.GetColumnCount()
        rows = self.peaklist.GetItemCount()
        #         tempData = ['start m/z, end m/z, z, color, alpha, filename, method, intensity, label']

        if rows == 0:
            return
        # Ask for a name and path
        saveDlg = wx.FileDialog(
            self,
            "Save peak list to file...",
            "",
            "",
            "Comma delimited file (*.csv)|*.csv",
            wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        )
        if saveDlg.ShowModal() == wx.ID_OK:
            filepath = saveDlg.GetPath()

            data = []
            # Iterate over row and columns to get data
            for row in range(rows):
                information = self.OnGetItemInformation(row)
                mz_start, mz_end = get_ion_name_from_label(information["ion_name"], as_num=True)
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
                    f"{mz_start}, {mz_end}, {charge}, {intensity}, {color}, {colormap}, {alpha}, {mask}, {label}, {method}, {document}"
                )

            print(data)

            # Save to file
            with open(filepath, "wb") as f:
                writer = csv.writer(f)
                for row in data:
                    print(row)
                    writer.writerows(row)

    def on_find_item(self, ion_name, filename):
        """Find index of item with the provided parameters"""
        item_count = self.peaklist.GetItemCount()

        for item_id in range(item_count):
            information = self.OnGetItemInformation(item_id)
            if ion_name == information["ionName"] and filename == information["document"]:
                return item_id

    def OnGetItemInformation(self, itemID, return_list=False):
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

        information["min_threshold"] = min_threshold
        information["max_threshold"] = max_threshold

        # Check whether the ion has combined ions
        parameters = None
        try:
            parameters = document.IMS2DCombIons[information["ionName"]].get("parameters", None)
        except (KeyError, AttributeError):
            pass
        information["parameters"] = parameters

        return information

    def on_get_value(self, value_type="color"):
        information = self.OnGetItemInformation(self.peaklist.item_id)

        if value_type == "start":
            return information["start"]
        elif value_type == "end":
            return information["end"]
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
            information = self.OnGetItemInformation(item_id)
            if ion_name == information["ionName"]:
                for keyword in kwargs:
                    self.on_update_value_in_peaklist(item_id, keyword, kwargs[keyword])

    def on_update_value_in_peaklist(self, item_id, value_type, value):

        if value_type == "start":
            self.peaklist.SetStringItem(item_id, self.config.peaklistColNames["start"], str(value))
        elif value_type == "end":
            self.peaklist.SetStringItem(item_id, self.config.peaklistColNames["end"], str(value))
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
        from gui_elements.panel_modify_ion_settings import PanelModifyIonSettings

        if evt is None:
            evtID = ID_ionPanel_editItem
        else:
            evtID = evt.GetId()

        if self.peaklist.item_id is None:
            logger.warning("Please select an item")
            return

        rows = self.peaklist.GetItemCount() - 1
        if evtID == ID_ionPanel_editItem:
            if self.peaklist.item_id < 0:
                print("Please select item in the table first.")
                return
            dlg_kwargs = self.OnGetItemInformation(self.peaklist.item_id)

            self.item_editor = PanelModifyIonSettings(self, self.presenter, self.config, **dlg_kwargs)
            self.item_editor.Centre()
            self.item_editor.Show()
        elif evtID == ID_ionPanel_edit_selected:
            while rows >= 0:
                if self.peaklist.IsChecked(rows):
                    information = self.OnGetItemInformation(rows)

                    dlg_kwargs = {
                        "select": self.peaklist.IsChecked(rows),
                        "color": information["color"],
                        "title": information["ionName"],
                        "min_threshold": information["min_threshold"],
                        "max_threshold": information["max_threshold"],
                        "label": information["label"],
                        "id": rows,
                    }

                    self.item_editor = PanelModifyIonSettings(self, self.presenter, self.config, **dlg_kwargs)
                    self.item_editor.Show()
                rows -= 1
        elif evtID == ID_ionPanel_edit_all:
            for row in range(rows):
                information = self.OnGetItemInformation(row)

                dlg_kwargs = {
                    "select": self.peaklist.IsChecked(row),
                    "color": information["color"],
                    "title": information["ionName"],
                    "min_threshold": information["min_threshold"],
                    "max_threshold": information["max_threshold"],
                    "label": information["label"],
                    "id": row,
                }

                self.item_editor = PanelModifyIonSettings(self, self.presenter, self.config, **dlg_kwargs)
                self.item_editor.Show()

    def on_assign_color(self, evt, itemID=None, give_value=False):
        """
        evt: wxPython event
            unused
        itemID: int
            value for item in table
        give_value: bool
            should/not return color
        """
        if itemID is not None:
            self.peaklist.item_id = itemID

        if itemID is None:
            itemID = self.peaklist.item_id

        dlg = DialogColorPicker(self, self.config.customColors)
        if dlg.ShowModal() == "ok":
            color_255, color_1, font_color = dlg.GetChosenColour()
            self.config.customColors = dlg.GetCustomColours()
            self.on_update_value_in_peaklist(itemID, "color", [color_255, color_1, font_color])

            # update document
            self.onUpdateDocument(evt=None)

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
                    self.onUpdateDocument(evt=None)
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
                self.onUpdateDocument(evt=None)
            except TypeError:
                print("Please select an item")

    def onUpdateDocument(self, evt, itemInfo=None):
        """Update document data"""

        # get item info
        if itemInfo is None:
            itemInfo = self.OnGetItemInformation(self.peaklist.item_id)

        # get item
        document = self.data_handling._on_get_document(itemInfo["document"])

        processed_name = "{} (processed)".format(itemInfo["ionName"])
        keywords = ["color", "colormap", "alpha", "mask", "label", "min_threshold", "max_threshold", "charge"]

        if itemInfo["ionName"] in document.IMS2Dions:
            for keyword in keywords:
                keyword_name = self.__check_keyword(keyword)
                document.IMS2Dions[itemInfo["ionName"]][keyword_name] = itemInfo[keyword]
                if processed_name in document.IMS2Dions:
                    document.IMS2Dions[processed_name][keyword_name] = itemInfo[keyword]

        if itemInfo["ionName"] in document.IMS2DCombIons:
            for keyword in keywords:
                keyword_name = self.__check_keyword(keyword)
                document.IMS2DCombIons[itemInfo["ionName"]][keyword_name] = itemInfo[keyword]
                if processed_name in document.IMS2DCombIons:
                    document.IMS2DCombIons[processed_name][keyword_name] = itemInfo[keyword]

        if itemInfo["ionName"] in document.IMS2DionsProcess:
            for keyword in keywords:
                keyword_name = self.__check_keyword(keyword)
                document.IMS2DionsProcess[itemInfo["ionName"]][keyword_name] = itemInfo[keyword]
                if processed_name in document.IMS2DionsProcess:
                    document.IMS2DionsProcess[processed_name][keyword_name] = itemInfo[keyword]

        if itemInfo["ionName"] in document.IMSRTCombIons:
            for keyword in keywords:
                keyword_name = self.__check_keyword(keyword)
                document.IMSRTCombIons[itemInfo["ionName"]][keyword_name] = itemInfo[keyword]
                if processed_name in document.IMSRTCombIons:
                    document.IMSRTCombIons[processed_name][keyword_name] = itemInfo[keyword]

        # Update document
        self.data_handling.on_update_document(document, "no_refresh")

    def on_remove_deleted_item(self, document):
        """
        @param document: title of the document to be removed from the list
        """
        row = self.peaklist.GetItemCount() - 1
        while row >= 0:
            info = self.OnGetItemInformation(itemID=row)
            if info["document"] == document:
                self.peaklist.DeleteItem(row)
                row -= 1
            else:
                row -= 1

    def on_open_peak_list(self, evt):
        """This function opens a formatted CSV file with peaks"""
        from gui_elements.dialog_select_document import DialogSelectDocument

        dlg = wx.FileDialog(
            self.view,
            "Choose a text file (m/z, window size, charge):",
            wildcard="*.csv;*.txt",
            style=wx.FD_DEFAULT_STYLE | wx.FD_CHANGE_DIR,
        )
        if dlg.ShowModal() == wx.ID_CANCEL:
            return
        else:

            manual = self.presenter.checkIfAnyDocumentsAreOfType(type="Type: MANUAL")
            origami = self.presenter.checkIfAnyDocumentsAreOfType(type="Type: ORIGAMI")
            infrared = self.presenter.checkIfAnyDocumentsAreOfType(type="Type: Infrared")
            docList = manual + origami + infrared
            if len(docList) == 0:
                args = ("Please create open or create a new document which can extract MS/IM-MS data", 4, 5)
                self.presenter.onThreading(evt, args, action="updateStatusbar")
                return
            elif len(docList) == 1:
                document_title = docList[0]
            else:
                document_panel = DialogSelectDocument(
                    self.view, presenter=self.presenter, document_list=docList, allow_new_document=False
                )
                if document_panel.ShowModal() == wx.ID_OK:
                    pass

                document_title = document_panel.current_document
                if document_title is None:
                    return

            # Create shortcut
            delimiter, __ = checkExtension(input=dlg.GetPath().encode("ascii", "replace"))
            peaklist = read_csv(dlg.GetPath(), delimiter=delimiter)
            peaklist = peaklist.fillna("")
            columns = peaklist.columns.values.tolist()
            for min_name in ["min", "min m/z"]:
                if min_name in columns:
                    break
                else:
                    continue
            if min_name not in columns:
                min_name = None

            for max_name in ["max", "max m/z"]:
                if max_name in columns:
                    break
                else:
                    continue
            if max_name not in columns:
                max_name = None

            for charge_name in ["z", "charge"]:
                if charge_name in columns:
                    break
                else:
                    continue
            if charge_name not in columns:
                charge_name = None

            for label_name in ["label", "information"]:
                if label_name in columns:
                    break
                else:
                    continue
            if label_name not in columns:
                label_name = None

            for color_name in ["color", "colour"]:
                if color_name in columns:
                    break
                else:
                    continue
            if color_name not in columns:
                color_name = None

            if min_name is None or max_name is None:
                return

            # get colorlist beforehand
            count = self.peaklist.GetItemCount() + len(peaklist)
            colors = self.view.panelPlots.on_change_color_palette(None, n_colors=count + 1, return_colors=True)

            # iterate
            for peak in range(len(peaklist)):
                min_value = peaklist[min_name][peak]
                max_value = peaklist[max_name][peak]

                if charge_name is not None:
                    charge_value = peaklist[charge_name][peak]
                else:
                    charge_value = ""

                if label_name is not None:
                    label_value = peaklist[label_name][peak]
                else:
                    label_value = ""

                if color_name is not None:
                    color_value = peaklist[color_name][peak]
                    try:
                        color_value = literal_eval(color_value)
                    except Exception:
                        pass
                else:
                    color_value = colors[peak]

                self.peaklist.Append(
                    [
                        str(min_value),
                        str(max_value),
                        str(charge_value),
                        "",
                        str(roundRGB(color_value)),
                        self.config.overlay_cmaps[get_random_int(0, len(self.config.overlay_cmaps))],
                        str(self.config.overlay_defaultAlpha),
                        str(self.config.overlay_defaultMask),
                        str(label_value),
                        "",
                        document_title,
                    ]
                )
                try:
                    color_value = convertRGB1to255(color_value)
                    self.peaklist.SetItemBackgroundColour(self.peaklist.GetItemCount() - 1, color_value)
                    self.peaklist.SetItemTextColour(
                        self.peaklist.GetItemCount() - 1, determineFontColor(color_value, return_rgb=True)
                    )
                except Exception:
                    pass
            self.view.on_toggle_panel(evt=ID_window_ionList, check=True)
            dlg.Destroy()

    def on_check_selected(self, evt):
        """Check current item when letter S is pressed on the keyboard"""
        check = not self.peaklist.IsChecked(index=self.peaklist.item_id)
        self.peaklist.CheckItem(self.peaklist.item_id, check=check)

    def on_add_blank_document_overlay(self, evt):
        self.presenter.onAddBlankDocument(evt=None, document_type="overlay")

    def on_extract_all(self, evt):
        self.data_handling.on_extract_2D_from_mass_range_fcn(None, extract_type="all")

    def on_extract_selected(self, evt):
        self.data_handling.on_extract_2D_from_mass_range_fcn(None, extract_type="selected")

    def on_extract_new(self, evt):
        self.data_handling.on_extract_2D_from_mass_range_fcn(None, extract_type="new")

    def on_overlay_mobiligram(self, evt):
        self.data_handling.on_overlay_1D(source="ion", plot_type="mobiligram")

    def on_overlay_chromatogram(self, evt):
        self.data_handling.on_overlay_1D(source="ion", plot_type="chromatogram")

    def on_overlay_heatmap(self, evt):
        self.presenter.on_overlay_2D(source="ion")

    def on_add_to_table(self, add_dict, check_color=True):

        # get color
        color = add_dict.get("color", self.config.customColors[get_random_int(0, 15)])
        # check for duplicate color
        if check_color:
            color = self.on_check_duplicate_colors(color)

        # add to peaklist
        self.peaklist.Append(
            [
                "",
                str(add_dict.get("ion_name", "")),
                #                 str(add_dict.get("mz_start", "")),
                #                 str(add_dict.get("mz_end", "")),
                str(add_dict.get("charge", "")),
                str(add_dict.get("mz_ymax", "")),
                str(roundRGB(convertRGB255to1(color))),
                str(add_dict.get("colormap", "")),
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

        itemInfo = self.OnGetItemInformation(itemID=self.peaklist.item_id)
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
                itemInfo = self.OnGetItemInformation(itemID=itemID)
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
            itemInfo = self.OnGetItemInformation(itemID=itemID)
            document = self.data_handling._on_get_document(itemInfo["document"])
            __, __ = self.view.panelDocuments.documents.on_delete_data__heatmap(
                document, itemInfo["document"], delete_type="heatmap.all.one", ion_name=itemInfo["ionName"]
            )
            itemID -= 1

    def delete_row_from_table(self, delete_item_name=None, delete_document_title=None):
        rows = self.peaklist.GetItemCount() - 1
        while rows >= 0:
            itemInfo = self.OnGetItemInformation(rows)

            if itemInfo["ionName"] == delete_item_name and itemInfo["document"] == delete_document_title:
                self.peaklist.DeleteItem(rows)
                rows = 0
                return
            elif delete_item_name is None and itemInfo["document"] == delete_document_title:
                self.peaklist.DeleteItem(rows)
            rows -= 1

    @staticmethod
    def __check_keyword(keyword_name):
        if keyword_name == "colormap":
            keyword_name = "cmap"
        return keyword_name
