# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
#    Copyright (C) 2017-2018 Lukasz G. Migas
#    <lukasz.migas@manchester.ac.uk> OR <lukas.migas@yahoo.com>
#
# 	 GitHub : https://github.com/lukasz-migas/ORIGAMI
# 	 University of Manchester IP : https://www.click2go.umip.com/i/s_w/ORIGAMI.html
# 	 Cite : 10.1016/j.ijms.2017.08.014
#
#    This program is free software. Feel free to redistribute it and/or
#    modify it under the condition you cite and credit the authors whenever
#    appropriate.
#    The program is distributed in the hope that it will be useful but is
#    provided WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE
# -------------------------------------------------------------------------
# __author__ lukasz.g.migas

import wx
import csv
from ast import literal_eval
from pandas import read_csv

from gui_elements.panel_modifyIonSettings import panelModifyIonSettings
from gui_elements.dialog_color_picker import DialogColorPicker
from toolbox import checkExtension
from styles import makeMenuItem, makeTooltip
from gui_elements.dialog_select_document import DialogSelectDocument
from gui_elements.dialog_ask import DialogAsk
from gui_elements.misc_dialogs import dlgBox
from utils.converters import str2num
from ids import ID_ionPanel_addToDocument, ID_combinedCV_binMSCombinedMenu, ID_ionPanel_assignColor, \
    ID_ionPanel_editItem, ID_highlightRectAllIons, ID_useInternalParamsCombinedMenu, ID_ionPanel_show_mobiligram, \
    ID_ionPanel_normalize1D, ID_overrideCombinedMenu, ID_useProcessedCombinedMenu, ID_ionPanel_check_selected, \
    ID_ionPanel_check_all, ID_ionPanel_show_zoom_in_MS, ID_ionPanel_delete_rightClick, ID_addIonsMenu, ID_removeIonsMenu, \
    ID_extractIonsMenu, ID_processIonsMenu, ID_saveIonsMenu, ID_showIonsMenu, ID_overlayIonsMenu, ID_selectOverlayMethod, \
    ID_ionPanel_table_startMS, ID_ionPanel_table_endMS, ID_ionPanel_table_color, ID_ionPanel_table_colormap, \
    ID_ionPanel_table_charge, ID_ionPanel_table_intensity, ID_ionPanel_table_document, ID_ionPanel_table_alpha, \
    ID_ionPanel_table_mask, ID_ionPanel_table_label, ID_ionPanel_table_method, ID_ionPanel_table_hideAll, \
    ID_ionPanel_table_restoreAll, ID_ionPanel_show_chromatogram, ID_ionPanel_show_heatmap, \
    ID_ionPanel_show_process_heatmap, ID_ionPanel_annotate_charge_state, ID_ionPanel_annotate_alpha, ID_ionPanel_annotate_mask, \
    ID_ionPanel_annotate_min_threshold, ID_ionPanel_annotate_max_threshold, ID_ionPanel_changeColorBatch_color, \
    ID_ionPanel_changeColorBatch_palette, ID_ionPanel_changeColorBatch_colormap, ID_ionPanel_changeColormapBatch, \
    ID_addManyIonsCSV, ID_duplicateIons, ID_addNewOverlayDoc, ID_ionPanel_automaticExtract, ID_extractAllIons, \
    ID_extractSelectedIon, ID_extractNewIon, ID_overlayMZfromList, ID_overlayMZfromList1D, ID_overlayMZfromListRT, \
    ID_ionPanel_automaticOverlay, ID_ionPanel_delete_selected, ID_ionPanel_delete_all, ID_ionPanel_clear_all, \
    ID_ionPanel_clear_selected, ID_combineCEscansSelectedIons, ID_combineCEscans, \
    ID_processSelectedIons, ID_processAllIons, ID_extractMSforCVs, ID_saveSelectIonListCSV, ID_saveIonListCSV, \
    ID_exportSeletedAsImage_ion, ID_exportAllAsImage_ion, ID_exportSelectedAsCSV_ion, ID_exportAllAsCSV_ion, \
    ID_processSaveMenu, ID_ionPanel_edit_selected, ID_ionPanel_edit_all, ID_window_ionList, ID_ionPanel_about_info

from styles import ListCtrl
from utils.color import convertRGB255to1, determineFontColor, randomColorGenerator, convertRGB1to255, roundRGB
from utils.random import randomIntegerGenerator

import logging
from utils.check import isempty
logger = logging.getLogger("origami")


class panelMultipleIons(wx.Panel):

    def __init__(self, parent, config, icons, helpInfo, presenter):
        wx.Panel.__init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                          size=wx.Size(300, -1), style=wx.TAB_TRAVERSAL)

        self.view = parent
        self.config = config
        self.help = helpInfo
        self.presenter = presenter
        self.icons = icons

        self.listOfSelected = []
        self.allChecked = True
        self.override = self.config.overrideCombine
        self.addToDocument = False
        self.normalize1D = False
        self.extractAutomatically = False
        self.plotAutomatically = True

        self.editItemDlg = None
        self.onSelectingItem = True
        self.docs = None
        self.reverse = False
        self.lastColumn = None
        self.ask_value = None
        self.flag = False  # flag to either show or hide annotation panel
        self.useInternalParams = self.config.useInternalParamsCombine
        self.process = False

        self._ionPanel_peaklist = {
            0: {"name": "", "tag": "check", "type": "bool"},
            1: {"name": "min m/z", "tag": "start", "type": "float"},
            2: {"name": "max m/z", "tag": "end", "type": "float"},
            3: {"name": "z", "tag": "charge", "type": "int"},
            4: {"name": "% int", "tag": "intensity", "type": "float"},
            5: {"name": "color", "tag": "color", "type": "color"},
            6: {"name": "colormap", "tag": "colormap", "type": "str"},
            7: {"name": "\N{GREEK SMALL LETTER ALPHA}", "tag": "alpha", "type": "float"},
            8: {"name": "mask", "tag": "mask", "type": "float"},
            9: {"name": "label", "tag": "label", "type": "float"},
            10: {"name": "method", "tag": "method", "type": "str"},
            11: {"name": "file", "tag": "document", "type": "str"},
        }

        self.make_gui()

        if self.plotAutomatically:
            self.combo.Bind(wx.EVT_COMBOBOX, self.on_overlay_heatmap)

        # add a couple of accelerators
        accelerators = [
            (wx.ACCEL_NORMAL, ord('A'), ID_ionPanel_addToDocument),
            (wx.ACCEL_NORMAL, ord('B'), ID_combinedCV_binMSCombinedMenu),
            (wx.ACCEL_NORMAL, ord('C'), ID_ionPanel_assignColor),
            (wx.ACCEL_NORMAL, ord('E'), ID_ionPanel_editItem),
            (wx.ACCEL_NORMAL, ord('H'), ID_highlightRectAllIons),
            #             (wx.ACCEL_NORMAL, ord('I'), ID_useInternalParamsCombinedMenu),
            (wx.ACCEL_NORMAL, ord('M'), ID_ionPanel_show_mobiligram),
            (wx.ACCEL_NORMAL, ord('N'), ID_ionPanel_normalize1D),
            (wx.ACCEL_NORMAL, ord('O'), ID_overrideCombinedMenu),
            (wx.ACCEL_NORMAL, ord('P'), ID_useProcessedCombinedMenu),
            (wx.ACCEL_NORMAL, ord('S'), ID_ionPanel_check_selected),
            (wx.ACCEL_NORMAL, ord('X'), ID_ionPanel_check_all),
            (wx.ACCEL_NORMAL, ord('Z'), ID_ionPanel_show_zoom_in_MS),
            (wx.ACCEL_NORMAL, wx.WXK_DELETE, ID_ionPanel_delete_rightClick),
        ]
        self.SetAcceleratorTable(wx.AcceleratorTable(accelerators))

        wx.EVT_MENU(self, ID_ionPanel_editItem, self.OnOpenEditor)
        wx.EVT_MENU(self, ID_ionPanel_addToDocument, self.onCheckTool)
        wx.EVT_MENU(self, ID_overrideCombinedMenu, self.onCheckTool)
#         wx.EVT_MENU(self, ID_useInternalParamsCombinedMenu, self.onCheckTool)
        wx.EVT_MENU(self, ID_useProcessedCombinedMenu, self.onCheckTool)
        wx.EVT_MENU(self, ID_ionPanel_normalize1D, self.onCheckTool)
        wx.EVT_MENU(self, ID_combinedCV_binMSCombinedMenu, self.onCheckTool)
#         wx.EVT_MENU(self, ID_highlightRectAllIons, self.data_handling.on_highlight_selected_ions)
        wx.EVT_MENU(self, ID_ionPanel_check_all, self.OnCheckAllItems)
        wx.EVT_MENU(self, ID_ionPanel_assignColor, self.on_assign_color)
        wx.EVT_MENU(self, ID_ionPanel_show_zoom_in_MS, self.on_plot)
        wx.EVT_MENU(self, ID_ionPanel_show_mobiligram, self.on_plot)
        wx.EVT_MENU(self, ID_ionPanel_check_selected, self.on_check_selected)
        wx.EVT_MENU(self, ID_ionPanel_delete_rightClick, self.on_delete_item)

    def _setup_handling_and_processing(self):
        self.data_processing = self.view.data_processing
        self.data_handling = self.view.data_handling

    def on_open_info_panel(self, evt):
        pass

    def make_gui(self):
        """ Make panel GUI """
        toolbar = self.make_toolbar()
        self.make_listctrl()

        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(toolbar, 0, wx.EXPAND, 0)
        self.mainSizer.Add(self.peaklist, 1, wx.EXPAND, 0)

        # fit layout
        self.mainSizer.Fit(self)
        self.SetSizer(self.mainSizer)
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
            self, ID_addIonsMenu, self.icons.iconsLib['add16'],
            size=(18, 18), style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL)
        self.add_btn.SetToolTip(makeTooltip("Add..."))

        self.remove_btn = wx.BitmapButton(
            self, ID_removeIonsMenu, self.icons.iconsLib['remove16'],
            size=(18, 18), style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL)
        self.remove_btn.SetToolTip(makeTooltip("Remove..."))

        self.annotate_btn = wx.BitmapButton(
            self, ID_showIonsMenu, self.icons.iconsLib['annotate16'],
            size=(18, 18), style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL)
        self.annotate_btn.SetToolTip(makeTooltip("Annotate..."))

        self.extract_btn = wx.BitmapButton(
            self, ID_extractIonsMenu, self.icons.iconsLib['extract16'],
            size=(18, 18), style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL)
        self.extract_btn.SetToolTip(makeTooltip("Extract..."))

        self.process_btn = wx.BitmapButton(
            self, ID_processIonsMenu, self.icons.iconsLib['process16'],
            size=(18, 18), style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL)
        self.process_btn.SetToolTip(makeTooltip("Process..."))

        self.overlay_btn = wx.BitmapButton(
            self, ID_overlayIonsMenu, self.icons.iconsLib['overlay16'],
            size=(18, 18), style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL)
        self.overlay_btn.SetToolTip(makeTooltip("Overlay selected ions..."))

        self.combo = wx.ComboBox(self, ID_selectOverlayMethod,
                                 size=(105, -1), choices=self.config.overlayChoices,
                                 style=wx.CB_READONLY)
        self.combo.SetStringSelection(self.config.overlayMethod)

        self.save_btn = wx.BitmapButton(
            self, ID_saveIonsMenu, self.icons.iconsLib['save16'],
            size=(18, 18), style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL)
        self.save_btn.SetToolTip(makeTooltip("Save..."))

        vertical_line_1 = wx.StaticLine(self, -1, style=wx.LI_VERTICAL)

        self.info_btn = wx.BitmapButton(
            self, ID_ionPanel_about_info, self.icons.iconsLib['info16'],
            size=(18, 18), style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL)
        self.info_btn.SetToolTip(makeTooltip("Information..."))

        # button grid
        btn_grid_vert = wx.GridBagSizer(2, 2)
        x = 0
        btn_grid_vert.Add(self.add_btn, (x, 0), wx.GBSpan(
            1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        btn_grid_vert.Add(self.remove_btn, (x, 1), wx.GBSpan(
            1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        btn_grid_vert.Add(self.annotate_btn, (x, 3), wx.GBSpan(
            1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        btn_grid_vert.Add(self.extract_btn, (x, 4), wx.GBSpan(
            1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        btn_grid_vert.Add(self.process_btn, (x, 5), wx.GBSpan(
            1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        btn_grid_vert.Add(self.overlay_btn, (x, 6), wx.GBSpan(
            1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        btn_grid_vert.Add(self.combo, (x, 7), wx.GBSpan(
            1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        btn_grid_vert.Add(self.save_btn, (x, 8), wx.GBSpan(
            1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        btn_grid_vert.Add(vertical_line_1, (x, 9), wx.GBSpan(1, 1), flag=wx.EXPAND)
        btn_grid_vert.Add(self.info_btn, (x, 10), wx.GBSpan(
            1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)

        return btn_grid_vert

    def make_listctrl(self):

        self.peaklist = ListCtrl(self, style=wx.LC_REPORT | wx.LC_VRULES, column_info=self._ionPanel_peaklist)
        for item in self.config._peakListSettings:
            order = item['order']
            name = item['name']
            if item['show']:
                width = item['width']
            else:
                width = 0
            self.peaklist.InsertColumn(order, name, width=width, format=wx.LIST_FORMAT_CENTER)

        self.peaklist.Bind(wx.EVT_LEFT_DCLICK, self.on_double_click_on_item)
        self.peaklist.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.on_right_click)
        self.peaklist.Bind(wx.EVT_LIST_COL_RIGHT_CLICK, self.menu_column_right_click)

    def on_double_click_on_item(self, evt):
        """Create annotation for activated peak."""

        if self.peaklist.item_id != -1:
            if not self.editItemDlg:
                self.OnOpenEditor(evt=None)
            else:
                self.editItemDlg.onUpdateGUI(self.OnGetItemInformation(self.peaklist.item_id))

    def onRenameItem(self, old_name, new_name, item_type="Document"):
        for row in range(self.peaklist.GetItemCount()):
            itemInfo = self.OnGetItemInformation(itemID=row)
            if item_type == "document":
                if itemInfo['document'] == old_name:
                    self.peaklist.SetStringItem(row,
                                                self.config.peaklistColNames['filename'],
                                                new_name)

    def menu_column_right_click(self, evt):
        self.Bind(wx.EVT_MENU, self.on_update_peaklist_table, id=ID_ionPanel_table_startMS)
        self.Bind(wx.EVT_MENU, self.on_update_peaklist_table, id=ID_ionPanel_table_endMS)
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
        n = 0
        self.table_start = menu.AppendCheckItem(ID_ionPanel_table_startMS, 'Table: Minimum m/z')
        self.table_start.Check(self.config._peakListSettings[n]['show'])
        n = n + 1
        self.table_end = menu.AppendCheckItem(ID_ionPanel_table_endMS, 'Table: Maximum m/z')
        self.table_end.Check(self.config._peakListSettings[n]['show'])
        n = n + 1
        self.table_charge = menu.AppendCheckItem(ID_ionPanel_table_charge, 'Table: Charge')
        self.table_charge.Check(self.config._peakListSettings[n]['show'])
        n = n + 1
        self.table_intensity = menu.AppendCheckItem(ID_ionPanel_table_intensity, 'Table: Intensity')
        self.table_intensity.Check(self.config._peakListSettings[n]['show'])
        n = n + 1
        self.table_color = menu.AppendCheckItem(ID_ionPanel_table_color, 'Table: Color')
        self.table_color.Check(self.config._peakListSettings[n]['show'])
        n = n + 1
        self.table_colormap = menu.AppendCheckItem(ID_ionPanel_table_colormap, 'Table: Colormap')
        self.table_colormap.Check(self.config._peakListSettings[n]['show'])
        n = n + 1
        self.table_alpha = menu.AppendCheckItem(ID_ionPanel_table_alpha, 'Table: Transparency')
        self.table_alpha.Check(self.config._peakListSettings[n]['show'])
        n = n + 1
        self.table_mask = menu.AppendCheckItem(ID_ionPanel_table_mask, 'Table: Mask')
        self.table_mask.Check(self.config._peakListSettings[n]['show'])
        n = n + 1
        self.table_label = menu.AppendCheckItem(ID_ionPanel_table_label, 'Table: Label')
        self.table_label.Check(self.config._peakListSettings[n]['show'])
        n = n + 1
        self.table_method = menu.AppendCheckItem(ID_ionPanel_table_method, 'Table: Method')
        self.table_method.Check(self.config._peakListSettings[n]['show'])
        n = n + 1
        self.table_document = menu.AppendCheckItem(ID_ionPanel_table_document, 'Table: Document')
        self.table_document.Check(self.config._peakListSettings[n]['show'])
        menu.AppendSeparator()
        self.table_index = menu.AppendItem(makeMenuItem(parent=menu, id=ID_ionPanel_table_hideAll,
                                                        text='Table: Hide all',
                                                        bitmap=self.icons.iconsLib['hide_table_16']))
        self.table_index = menu.AppendItem(makeMenuItem(parent=menu, id=ID_ionPanel_table_restoreAll,
                                                        text='Table: Restore all',
                                                        bitmap=self.icons.iconsLib['show_table_16']))

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
        self.Bind(wx.EVT_MENU, self.OnOpenEditor, id=ID_ionPanel_editItem)
        self.Bind(wx.EVT_MENU, self.on_assign_color, id=ID_ionPanel_assignColor)
        self.Bind(wx.EVT_MENU, self.on_delete_item, id=ID_ionPanel_delete_rightClick)

        self.peaklist.item_id = evt.GetIndex()

        menu = wx.Menu()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_ionPanel_show_zoom_in_MS,
                                     text='Zoom in on the ion\tZ',
                                     bitmap=self.icons.iconsLib['zoom_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_ionPanel_show_chromatogram,
                                     text='Show chromatogram',
                                     bitmap=self.icons.iconsLib['chromatogram_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_ionPanel_show_mobiligram,
                                     text='Show mobiligram\tM',
                                     bitmap=self.icons.iconsLib['mobiligram_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_ionPanel_show_heatmap,
                                     text='Show heatmap',
                                     bitmap=self.icons.iconsLib['heatmap_16']))
        menu.Append(ID_ionPanel_show_process_heatmap, "Process and show heatmap")
        menu.AppendSeparator()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_ionPanel_assignColor,
                                     text='Assign new color\tC',
                                     bitmap=self.icons.iconsLib['color_panel_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_ionPanel_editItem,
                                     text='Edit ion information\tE',
                                     bitmap=self.icons.iconsLib['info16']))
        menu.AppendSeparator()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_ionPanel_delete_rightClick,
                                     text='Remove item\tDelete',
                                     bitmap=self.icons.iconsLib['bin16']))
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
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_highlightRectAllIons,
                                     text='Highlight extracted items on MS plot\tH',
                                     bitmap=self.icons.iconsLib['highlight_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_ionPanel_annotate_charge_state,
                                     text='Assign charge state to selected ions',
                                     bitmap=self.icons.iconsLib['assign_charge_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_ionPanel_annotate_alpha,
                                     text='Assign transparency value to selected ions',
                                     bitmap=self.icons.iconsLib['transparency_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_ionPanel_annotate_mask,
                                     text='Assign mask value to selected ions',
                                     bitmap=self.icons.iconsLib['mask_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_ionPanel_annotate_min_threshold,
                                     text='Assign minimum threshold to selected ions',
                                     bitmap=self.icons.iconsLib['min_threshold_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_ionPanel_annotate_max_threshold,
                                     text='Assign maximum threshold to selected ions',
                                     bitmap=self.icons.iconsLib['max_threshold_16']))
        menu.AppendSeparator()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_ionPanel_changeColorBatch_color,
                                     text='Assign color for selected items',
                                     bitmap=self.icons.iconsLib['color_panel_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_ionPanel_changeColorBatch_palette,
                                     text='Color selected items using color palette',
                                     bitmap=self.icons.iconsLib['blank_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_ionPanel_changeColorBatch_colormap,
                                     text='Color selected items using colormap',
                                     bitmap=self.icons.iconsLib['blank_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_ionPanel_changeColormapBatch,
                                     text='Randomize colormap for selected items',
                                     bitmap=self.icons.iconsLib['randomize_16']))

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def menu_add_tools(self, evt):
        # TODO: add "Restore items from document"
        self.Bind(wx.EVT_MENU, self.on_open_peak_list, id=ID_addManyIonsCSV)

        menu = wx.Menu()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_addManyIonsCSV,
                                     text='Add list of ions (.csv/.txt)\tCtrl+L',
                                     bitmap=self.icons.iconsLib['filelist_16'],
                                     help_text='Format: min, max, charge (optional), label (optional), color (optional)'))
#         menu.AppendSeparator()
#         menu.AppendItem(makeMenuItem(parent=menu, id=ID_addNewOverlayDoc,
#                                      text='Create blank COMPARISON document\tAlt+D',
#                                      bitmap=self.icons.iconsLib['new_document_16']))
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    # TODO: add Extract chromatographic data only
    # TODO: add extract mobilogram data only
    def menu_extract_tools(self, evt):

        self.Bind(wx.EVT_MENU, self.onCheckTool, id=ID_ionPanel_automaticExtract)
        self.Bind(wx.EVT_MENU, self.on_extract_all, id=ID_extractAllIons)
        self.Bind(wx.EVT_MENU, self.on_extract_selected, id=ID_extractSelectedIon)
        self.Bind(wx.EVT_MENU, self.on_extract_new, id=ID_extractNewIon)

        menu = wx.Menu()
        self.automaticExtract_check = menu.AppendCheckItem(ID_ionPanel_automaticExtract, "Extract data automatically",
                                                           help="Ions will be extracted automatically")
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
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_addNewOverlayDoc,
                                     text='Create blank COMPARISON document\tAlt+D',
                                     bitmap=self.icons.iconsLib['new_document_16']))
        menu.AppendSeparator()
        self.addToDocument_check = menu.AppendCheckItem(ID_ionPanel_addToDocument,
                                                        "Add overlay plots to document\tA",
                                                        help="Add overlay results to comparison document")
        self.addToDocument_check.Check(self.addToDocument)
        menu.AppendSeparator()
        self.normalize1D_check = menu.AppendCheckItem(ID_ionPanel_normalize1D, "Normalize mobiligram/chromatogram dataset\tN",
                                                      help="Normalize mobiligram/chromatogram before overlaying")
        self.normalize1D_check.Check(self.normalize1D)
        menu.Append(ID_overlayMZfromList1D, "Overlay mobiligrams (selected)")
        menu.Append(ID_overlayMZfromListRT, "Overlay chromatograms (selected)")
        menu.AppendSeparator()
        self.useProcessed_check = menu.AppendCheckItem(ID_useProcessedCombinedMenu, "Use processed data (when available)\tP",
                                                       help="When checked, processed data is used in the overlay (2D) plots.")
        self.useProcessed_check.Check(self.config.overlay_usedProcessed)
        menu.AppendSeparator()
        self.automaticPlot_check = menu.AppendCheckItem(ID_ionPanel_automaticOverlay, "Overlay automatically",
                                                        help="Ions will be extracted automatically")
        self.automaticPlot_check.Check(self.plotAutomatically)
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_overlayMZfromList,
                                     text='Overlay heatmaps (selected)\tAlt+Q',
                                     bitmap=self.icons.iconsLib['heatmap_grid_16']))
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
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_ionPanel_clear_selected,
                                     text='Remove from list (selected)',
                                     bitmap=self.icons.iconsLib['clear_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_ionPanel_clear_all,
                                     text='Remove from list (all)',
                                     bitmap=self.icons.iconsLib['clear_16']))

        menu.AppendSeparator()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_ionPanel_delete_selected,
                                     text='Remove from file (selected)',
                                     bitmap=self.icons.iconsLib['bin16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_ionPanel_delete_all,
                                     text='Remove from file (all)',
                                     bitmap=self.icons.iconsLib['bin16']))
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def menu_process_tools(self, evt):

        self.Bind(wx.EVT_MENU, self.data_processing.on_combine_origami_collision_voltages,
                  id=ID_combineCEscansSelectedIons)
        self.Bind(wx.EVT_MENU, self.data_processing.on_combine_origami_collision_voltages,
                  id=ID_combineCEscans)

        self.Bind(wx.EVT_MENU, self.presenter.onProcessMultipleIonsIons, id=ID_processSelectedIons)
        self.Bind(wx.EVT_MENU, self.presenter.onProcessMultipleIonsIons, id=ID_processAllIons)
        self.Bind(wx.EVT_MENU, self.data_handling.on_extract_mass_spectrum_for_each_collision_voltage,
                  id=ID_extractMSforCVs)

        self.Bind(wx.EVT_MENU, self.onCheckTool, id=ID_overrideCombinedMenu)
#         self.Bind(wx.EVT_MENU, self.onCheckTool, id=ID_useInternalParamsCombinedMenu)
        self.Bind(wx.EVT_MENU, self.onCheckTool, id=ID_combinedCV_binMSCombinedMenu)

        menu = wx.Menu()
        menu.Append(ID_processSelectedIons, "Process selected ions")
        menu.Append(ID_processAllIons, "Process all ions")
        menu.AppendSeparator()
        help_msg = "When checked, any previous results for the selected item(s) will be overwritten" + \
                   " based on the current parameters."
        self.override_check = menu.AppendCheckItem(
            ID_overrideCombinedMenu, "Overwrite results\tO",
            help=help_msg)
        self.override_check.Check(self.config.overrideCombine)
        help_msg = "When checked, collision voltage scans will be combined based on parameters present" + \
                   " in the ORIGAMI document."
#         self.useInternalParams_check = menu.AppendCheckItem(
#             ID_useInternalParamsCombinedMenu, "Use internal parameters\tI",
#             help=help_msg)
#         self.useInternalParams_check.Check(self.config.useInternalParamsCombine)
        menu.Append(ID_combineCEscansSelectedIons,
                    "Combine collision voltages for selected items (ORIGAMI-MS)")
        menu.Append(ID_combineCEscans,
                    "Combine collision voltages for all items (ORIGAMI-MS)\tAlt+C")
        menu.AppendSeparator()
        self.binCombinedCV_MS_check = menu.AppendCheckItem(
            ID_combinedCV_binMSCombinedMenu, "Bin mass spectra during extraction\tB", help="")
        self.binCombinedCV_MS_check.Check(self.config.binCVdata)
        menu.Append(ID_extractMSforCVs, "Extract mass spectra for each collision voltage (ORIGAMI)")

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def menu_save_tools(self, evt):
        # TODO: Move all the saveAsData functions to data_handling panel!
        self.Bind(wx.EVT_MENU, self.OnSaveSelectedPeakList, id=ID_saveSelectIonListCSV)
        self.Bind(wx.EVT_MENU, self.OnSavePeakList, id=ID_saveIonListCSV)

#         self.Bind(wx.EVT_MENU, self.onSaveAsData, id=ID_exportSeletedAsImage_ion)
#         self.Bind(wx.EVT_MENU, self.onSaveAsData, id=ID_exportAllAsImage_ion)
#         self.Bind(wx.EVT_MENU, self.onSaveAsData, id=ID_exportSelectedAsCSV_ion)
#         self.Bind(wx.EVT_MENU, self.onSaveAsData, id=ID_exportAllAsCSV_ion)

        self.Bind(wx.EVT_MENU, self.onCheckTool, id=ID_processSaveMenu)

        saveImageLabel = ''.join(['Save all figures (.', self.config.imageFormat, ')'])
        saveSelectedImageLabel = ''.join(['Save selected figure (.', self.config.imageFormat, ')'])

        saveTextLabel = ''.join(['Save all 2D (', self.config.saveDelimiterTXT, ' delimited)'])
        saveSelectedTextLabel = ''.join(['Save selected 2D (', self.config.saveDelimiterTXT, ' delimited)'])

        menu = wx.Menu()
        menu.Append(ID_saveIonListCSV, "Export peak list as .csv")

        self.processSave_check = menu.AppendCheckItem(ID_processSaveMenu, "Process before saving",
                                                      help="Process each item before saving")
        self.processSave_check.Check(self.process)
        menu.AppendSeparator()
        menu.Append(ID_exportSeletedAsImage_ion, saveSelectedImageLabel)
        menu.Append(ID_exportAllAsImage_ion, saveImageLabel)
        menu.AppendSeparator()
        menu.Append(ID_exportSelectedAsCSV_ion, saveSelectedTextLabel)
        menu.Append(ID_exportAllAsCSV_ion, saveTextLabel)
#         menu.Append(ID_saveSelectIonListCSV, "Export peak list...") # disabled for now
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def onCheckTool(self, evt):
        """ Check/uncheck menu item """

        evtID = evt.GetId()

        # check which event was triggered
        if evtID == ID_overrideCombinedMenu:
            self.config.overrideCombine = not self.config.overrideCombine
            args = ("Peak list panel: 'Override' combined IM-MS data was switched to %s" %
                    self.config.overrideCombine, 4)
            self.presenter.onThreading(evt, args, action='updateStatusbar')

#         if evtID == ID_useInternalParamsCombinedMenu:
#             self.config.useInternalParamsCombine = not self.config.useInternalParamsCombine
#             args = ("Peak list panel: 'Use internal parameters' was switched to  %s" % self.config.useInternalParamsCombine, 4)
#             self.presenter.onThreading(evt, args, action='updateStatusbar')

        if evtID == ID_processSaveMenu:
            self.process = not self.process
            args = ("Override was switched to %s" % self.override, 4)
            self.presenter.onThreading(evt, args, action='updateStatusbar')

        if evtID == ID_useProcessedCombinedMenu:
            self.config.overlay_usedProcessed = not self.config.overlay_usedProcessed
            args = ("Peak list panel: Using processing data was switched to %s" % self.config.overlay_usedProcessed, 4)
            self.presenter.onThreading(evt, args, action='updateStatusbar')

        if evtID == ID_combinedCV_binMSCombinedMenu:
            self.config.binCVdata = not self.config.binCVdata
            args = ("Binning mass spectra from ORIGAMI files was switched to %s" % self.config.binCVdata, 4)
            self.presenter.onThreading(evt, args, action='updateStatusbar')

        if evtID == ID_ionPanel_addToDocument:
            self.addToDocument = not self.addToDocument
            args = ("Adding data to comparison document was set to: %s" % self.addToDocument, 4)
            self.presenter.onThreading(evt, args, action='updateStatusbar')

        if evtID == ID_ionPanel_normalize1D:
            self.normalize1D = not self.normalize1D
            args = ("Normalization of mobiligrams/chromatograms was set to: %s" % self.normalize1D, 4)
            self.presenter.onThreading(evt, args, action='updateStatusbar')

        if evtID == ID_ionPanel_automaticExtract:
            self.extractAutomatically = not self.extractAutomatically
            args = ("Automatic extraction was set to: {}".format(self.extractAutomatically), 4)
            self.presenter.onThreading(evt, args, action='updateStatusbar')

        if evtID == ID_ionPanel_automaticOverlay:
            self.plotAutomatically = not self.plotAutomatically
            args = ("Automatic 2D overlaying was set to: {}".format(self.plotAutomatically), 4)
            self.presenter.onThreading(evt, args, action='updateStatusbar')

            if self.plotAutomatically:
                self.combo.Bind(wx.EVT_COMBOBOX, self.on_overlay_heatmap)
            else:
                self.combo.Unbind(wx.EVT_COMBOBOX)

    def on_update_peaklist_table(self, evt):
        evtID = evt.GetId()

        # check which event was triggered
        if evtID == ID_ionPanel_table_startMS:
            col_index = self.config.peaklistColNames['start']
        elif evtID == ID_ionPanel_table_endMS:
            col_index = self.config.peaklistColNames['end']
        elif evtID == ID_ionPanel_table_charge:
            col_index = self.config.peaklistColNames['charge']
        elif evtID == ID_ionPanel_table_intensity:
            col_index = self.config.peaklistColNames['intensity']
        elif evtID == ID_ionPanel_table_color:
            col_index = self.config.peaklistColNames['color']
        elif evtID == ID_ionPanel_table_colormap:
            col_index = self.config.peaklistColNames['colormap']
        elif evtID == ID_ionPanel_table_alpha:
            col_index = self.config.peaklistColNames['alpha']
        elif evtID == ID_ionPanel_table_mask:
            col_index = self.config.peaklistColNames['mask']
        elif evtID == ID_ionPanel_table_label:
            col_index = self.config.peaklistColNames['label']
        elif evtID == ID_ionPanel_table_method:
            col_index = self.config.peaklistColNames['method']
        elif evtID == ID_ionPanel_table_document:
            col_index = self.config.peaklistColNames['filename']
        elif evtID == ID_ionPanel_table_restoreAll:
            for i in range(len(self.config._peakListSettings)):
                self.config._peakListSettings[i]['show'] = True
                col_width = self.config._peakListSettings[i]['width']
                self.peaklist.SetColumnWidth(i, col_width)
            return
        elif evtID == ID_ionPanel_table_hideAll:
            for i in range(len(self.config._peakListSettings)):
                self.config._peakListSettings[i]['show'] = False
                col_width = 0
                self.peaklist.SetColumnWidth(i, col_width)
            return

        # check values
        col_check = not self.config._peakListSettings[col_index]['show']
        self.config._peakListSettings[col_index]['show'] = col_check
        if col_check:
            col_width = self.config._peakListSettings[col_index]['width']
        else:
            col_width = 0
        # set new column width
        self.peaklist.SetColumnWidth(col_index, col_width)

    def OnCheckAllItems(self, evt, check=True, override=False):
        """
        Check/uncheck all items in the list
        ===
        Parameters:
        check : boolean, sets items to specified state
        override : boolean, skips settings self.allChecked value
        """
        rows = self.peaklist.GetItemCount()

        if not override:
            if self.allChecked:
                self.allChecked = False
                check = True
            else:
                self.allChecked = True
                check = False

        if rows > 0:
            for row in range(rows):
                self.peaklist.CheckItem(row, check=check)

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
                'static_text': 'Assign charge state to selected items.',
                'value_text': "",
                'validator': 'integer',
                'keyword': 'charge'}
        elif evt.GetId() == ID_ionPanel_annotate_alpha:
            static_text = "Assign new transparency value to selected items \nTypical transparency values: 0.5" + \
                          "\nRange 0-1"
            ask_kwargs = {
                'static_text': static_text,
                'value_text': 0.5,
                'validator': 'float',
                'keyword': 'alpha'}
        elif evt.GetId() == ID_ionPanel_annotate_mask:
            ask_kwargs = {
                'static_text': 'Assign new mask value to selected items \nTypical mask values: 0.25\nRange 0-1',
                'value_text': 0.25,
                'validator': 'float',
                'keyword': 'mask'}
        elif evt.GetId() == ID_ionPanel_annotate_min_threshold:
            ask_kwargs = {
                'static_text': 'Assign minimum threshold value to selected items \nTypical mask values: 0.0\nRange 0-1',
                'value_text': 0.0,
                'validator': 'float',
                'keyword': 'min_threshold'}
        elif evt.GetId() == ID_ionPanel_annotate_max_threshold:
            ask_kwargs = {
                'static_text': 'Assign maximum threshold value to selected items \nTypical mask values: 1.0\nRange 0-1',
                'value_text': 1.0,
                'validator': 'float',
                'keyword': 'max_threshold'}

        ask = DialogAsk(self, **ask_kwargs)
        ask.ShowModal()

        if self.ask_value is None:
            logger.info("Action was cancelled")
            return

        for row in range(rows):
            if self.peaklist.IsChecked(index=row):
                itemInfo = self.OnGetItemInformation(row)
                filename = itemInfo['document']
                selectedText = itemInfo['ionName']
                document = self.presenter.documentsDict[filename]
                if not ask_kwargs['keyword'] in ['min_threshold', 'max_threshold']:
                    self.peaklist.SetStringItem(row,
                                                self.config.peaklistColNames[ask_kwargs['keyword']],
                                                str(self.ask_value))

                if selectedText in document.IMS2Dions:
                    document.IMS2Dions[selectedText][ask_kwargs['keyword']] = self.ask_value
                if selectedText in document.IMS2DCombIons:
                    document.IMS2DCombIons[selectedText][ask_kwargs['keyword']] = self.ask_value
                if selectedText in document.IMS2DionsProcess:
                    document.IMS2DionsProcess[selectedText][ask_kwargs['keyword']] = self.ask_value
                if selectedText in document.IMSRTCombIons:
                    document.IMSRTCombIons[selectedText][ask_kwargs['keyword']] = self.ask_value

                # Update document
                self.data_handling.on_update_document(document, "no_refresh")

#     def onSaveAsData(self, evt):
#         count = self.peaklist.GetItemCount()
#         self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['2D'])
#         for ion in range(count):
#             if evt.GetId() == ID_exportAllAsCSV_ion or evt.GetId() == ID_exportAllAsImage_ion:
#                 pass
#             else:
#                 if self.peaklist.IsChecked(index=ion): pass
#                 else: continue
#             # Get names
#             itemInfo = self.OnGetItemInformation(ion)
#             rangeName = itemInfo['ionName']
#             filename = itemInfo['document']
#             # Get data
#             currentDocument = self.presenter.documentsDict[filename]
#
#             # Check whether its ORIGAMI or MANUAL data type
#             if currentDocument.dataType == 'Type: ORIGAMI':
#                 if currentDocument.gotCombinedExtractedIons :
#                     data = currentDocument.IMS2DCombIons
#                 elif currentDocument.gotExtractedIons :
#                     data = currentDocument.IMS2Dions
#             elif currentDocument.dataType == 'Type: MANUAL':
#                 if currentDocument.gotCombinedExtractedIons :
#                     data = currentDocument.IMS2DCombIons
#             else: continue
#             zvals, xvals, xlabel, yvals, ylabel, cmap = self.presenter.get2DdataFromDictionary(
#                 dictionary=data[rangeName], dataType='plot', compact=False)
#             if self.process:
#                 zvals = self.data_processing.on_process_2D(zvals=zvals, return_data=True)
#
#             # Save CSV
#             if evt.GetId() == ID_exportAllAsCSV_ion or evt.GetId() == ID_exportSelectedAsCSV_ion:
#                 savename = ''.join([currentDocument.path, '/DT_2D_', rangeName, self.config.saveExtension])
#                 # Y-axis labels need a value for [0,0]
#                 yvals = np.insert(yvals, 0, 0)  # array, index, value
#                 # Combine x-axis with data
#                 saveData = np.vstack((xvals, zvals))
#                 saveData = np.vstack((yvals, saveData.T))
#                 # Save 2D array
#                 saveAsText(filename=savename,
#                            data=saveData,
#                            format='%.2f',
#                            delimiter=self.config.saveDelimiter,
#                            header="")
#             # Save Image
#             elif evt.GetId() == ID_exportAllAsImage_ion or evt.GetId() == ID_exportSeletedAsImage_ion:
#                 saveFileName = 'DT_2D_'
#                 self.presenter.view.panelPlots.on_plot_2D(zvals, xvals, yvals, xlabel, ylabel, cmap, override=True)
#                 save_kwargs = {'image_name':"{}_{}".format(saveFileName, rangeName)}
#                 self.presenter.view.panelPlots.save_images(evt=ID_save2DImageDoc, **save_kwargs)
#         self.presenter.onThreading(evt, ('Finished saving data', 4), action='updateStatusbar')

    def onRecalculateCombinedORIGAMI(self, evt):
        # Apply all fields for item
        self.onAnnotateItems(evt=None)
        # Check item to recalculate
        self.peaklist.CheckItem(self.peaklist.item_id, check=True)
        # Recalculate
        self.presenter.onCombineCEvoltagesMultiple(evt=evt)
        # Uncheck item
        self.peaklist.CheckItem(self.peaklist.item_id, check=False)

    def onCheckForDuplicates(self, mzStart=None, mzEnd=None):
        """
        Check whether the value being added is already present in the table
        """
        currentItems = self.peaklist.GetItemCount() - 1
        while (currentItems >= 0):
            itemInfo = self.OnGetItemInformation(currentItems)
            if itemInfo['start'] == mzStart and itemInfo['end'] == mzEnd:
                print('Ion already in the table')
                currentItems = 0
                return True
            else:
                currentItems -= 1
        return False

#     def onRemoveDuplicates(self, evt, limitCols=False):
#         """
#         This function removes duplicates from the list
#         Its not very efficient!
#         """
#
#         columns = self.peaklist.GetColumnCount()
#         rows = self.peaklist.GetItemCount()
#
#         tempData = []
#         # Iterate over row and columns to get data
#         for row in range(rows):
#             tempRow = []
#             for col in range(columns):
#                 item = self.peaklist.GetItem(itemId=row, col=col)
#                 #  We want to make sure certain columns are numbers
#                 if col in [self.config.peaklistColNames['start'],
#                            self.config.peaklistColNames['end'],
#                            self.config.peaklistColNames['intensity'],
#                            self.config.peaklistColNames['alpha'],
#                            self.config.peaklistColNames['mask']]:
#                     itemData = str2num(item.GetText())
#                     if itemData is None: itemData = 0
#                     tempRow.append(itemData)
#                 elif col == self.config.peaklistColNames['charge']:
#                     itemData = str2int(item.GetText())
#                     if itemData is None: itemData = 0
#                     tempRow.append(itemData)
#                 else:
#                     tempRow.append(item.GetText())
#             tempRow.append(self.peaklist.IsChecked(index=row))
#             tempRow.append(self.peaklist.GetItemBackgroundColour(row))
#             tempRow.append(self.peaklist.GetItemTextColour(row))
#             tempData.append(tempRow)
#
#         # Remove duplicates
#         tempData = removeListDuplicates(input=tempData,
#                                         columnsIn=['start', 'end', 'charge', 'intensity',
#                                         'color', 'colormap', 'alpha', 'mask',
#                                         'label', 'method', 'filename', 'check', 'rgb', 'font_color'],
#                                          limitedCols=['start', 'end', 'filename'])
#         rows = len(tempData)
#         # Clear table
#         self.peaklist.DeleteAllItems()
#
#         checkData, bg_rgb, fg_rgb = [], [], []
#         for check in tempData:
#             fg_rgb.append(check[-1])
#             del check[-1]
#             bg_rgb.append(check[-1])
#             del check[-1]
#             checkData.append(check[-1])
#             del check[-1]
#
#         # Reinstate data
#         rowList = arange(len(tempData))
#         for row, check, bg_rgb, fg_color in zip(rowList, checkData, bg_rgb, fg_rgb):
#             self.peaklist.Append(tempData[row])
#             self.peaklist.CheckItem(row, check)
#             self.peaklist.SetItemBackgroundColour(row, bg_rgb)
#             self.peaklist.SetItemTextColour(row, fg_color)
#
#         if evt is None: return
#         else:
#             evt.Skip()

    def on_check_duplicate(self, mz_min, mz_max, document):
        rows = self.peaklist.GetItemCount()

        for row in range(rows):
            mzStart_in_table = str2num(self.peaklist.GetItem(row, self.config.peaklistColNames['start']).GetText())
            mzEnd_in_table = str2num(self.peaklist.GetItem(row, self.config.peaklistColNames['end']).GetText())
            document_in_table = self.peaklist.GetItem(row, self.config.peaklistColNames['filename']).GetText()
            if (mzStart_in_table == mz_min and
                mzEnd_in_table == mz_max and
                    document_in_table == document):
                return True

        return False

    def on_plot(self, evt):
        """
        This function extracts 2D array and plots it in 2D/3D
        """
        itemInfo = self.OnGetItemInformation(self.peaklist.item_id)
        mzStart = itemInfo['start']
        mzEnd = itemInfo['end']
        intensity = itemInfo['intensity']
        selectedItem = itemInfo['document']
        rangeName = itemInfo['ionName']

        # Check if data was extracted
        if selectedItem == '':
            dlgBox(exceptionTitle='Extract data first',
                   exceptionMsg="Please extract data first",
                   type="Error")
            return
        # Get data from dictionary
        currentDocument = self.presenter.documentsDict[selectedItem]

        # Preset empty
        data, zvals, xvals, xlabel, yvals, ylabel = None, None, None, None, None, None
        # Check whether its ORIGAMI or MANUAL data type
        if currentDocument.dataType == 'Type: ORIGAMI':
            if currentDocument.gotCombinedExtractedIons:
                data = currentDocument.IMS2DCombIons
            elif currentDocument.gotExtractedIons:
                data = currentDocument.IMS2Dions
        elif currentDocument.dataType == 'Type: MANUAL':
            if currentDocument.gotCombinedExtractedIons:
                data = currentDocument.IMS2DCombIons
        else:
            return

        if data is None:
            self.presenter.onThreading(evt, ("Please extract data before trying to view it", 4, 3),
                                       action='updateStatusbar')
            if evt.GetId() == ID_ionPanel_show_zoom_in_MS:
                try:
                    self.presenter.view.panelPlots.on_zoom_1D_x_axis(str2num(mzStart) - self.config.zoomWindowX,
                                                                     str2num(mzEnd) + self.config.zoomWindowX,
                                                                     set_page=True)
                except Exception:
                    pass
            return

        if evt.GetId() == ID_ionPanel_show_mobiligram:
            xvals = data[rangeName]['yvals']  # normally this would be the y-axis
            yvals = data[rangeName]['yvals1D']
            xlabels = data[rangeName]['ylabels']  # normally this would be x-axis label
            self.presenter.view.panelPlots.on_plot_1D(xvals, yvals, xlabels, set_page=True)

        elif evt.GetId() == ID_ionPanel_show_chromatogram:
            xvals = data[rangeName]['xvals']
            yvals = data[rangeName]['yvalsRT']
            xlabels = data[rangeName]['xlabels']  # normally this would be x-axis label
            self.presenter.view.panelPlots.on_plot_RT(xvals, yvals, xlabels, set_page=True)

        elif evt.GetId() == ID_ionPanel_show_zoom_in_MS:
            """
            This simply zooms in on an ion
            """
            if selectedItem != self.presenter.currentDoc:
                self.presenter.onThreading(evt, ("This ion belongs to different document", 4, 3),
                                           action='updateStatusbar')
            startX = str2num(mzStart) - self.config.zoomWindowX
            endX = str2num(mzEnd) + self.config.zoomWindowX
            try:
                endY = str2num(intensity) / 100
            except TypeError:
                endY = 1.001
            if endY == 0:
                endY = 1.001
            try:
                self.presenter.view.panelPlots.on_zoom_1D(startX=startX, endX=endX, endY=endY, set_page=True)
            except AttributeError:
                self.presenter.onThreading(evt, (
                    "Failed to zoom-in on the ion. Please replot the mass spectrum and try again.", 4, 3),
                    action='updateStatusbar')
                return

        else:
            # Unpack data
            zvals, xvals, xlabel, yvals, ylabel, cmap = self.presenter.get2DdataFromDictionary(
                dictionary=data[rangeName], dataType='plot', compact=False)

            # Warning in case  there is missing data
            if isempty(xvals) or isempty(yvals) or xvals is "" or yvals is "":
                msg = "Missing x/y-axis labels. Cannot continue! \nAdd x/y-axis labels to each file before continuing."
                print(msg)
                dlgBox(exceptionTitle='Missing data',
                       exceptionMsg=msg,
                       type="Error")
                return
            # Process data
            if evt.GetId() == ID_ionPanel_show_process_heatmap:
                zvals = self.data_processing.on_process_2D(zvals=zvals, return_data=True)
            # Plot data
            self.presenter.view.panelPlots.on_plot_2D(zvals, xvals, yvals, xlabel, ylabel, cmap, override=True,
                                                      set_page=True)

    def OnSavePeakList(self, evt):
        """
        Save data in CSV format
        """
        columns = self.peaklist.GetColumnCount()
        rows = self.peaklist.GetItemCount()
#         tempData = ['start m/z, end m/z, z, color, alpha, filename, method, intensity, label']
        tempData = []
        if rows == 0:
            return
        # Ask for a name and path
        saveDlg = wx.FileDialog(self, "Save peak list to file...", "", "",
                                "Comma delimited file (*.csv)|*.csv",
                                wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if saveDlg.ShowModal() == wx.ID_CANCEL:
            return
        else:
            filepath = saveDlg.GetPath()
#             print(filepath)

        # Iterate over row and columns to get data
        for row in range(rows):
            tempRow = []
            for col in range(columns):
                item = self.peaklist.GetItem(itemId=row, col=col)
                #  We want to make sure the first 3 columns are numbers
                if col == 0 or col == 1 or col == 2:
                    itemData = str2num(item.GetText())
                    if itemData is None:
                        itemData = 0
                    tempRow.append(itemData)
                else:
                    tempRow.append(item.GetText())
            tempData.append(tempRow)

        # Save to file
        with open(filepath, "wb") as f:
            writer = csv.writer(f)
            writer.writerows(tempData)

    def OnSaveSelectedPeakList(self, evt):
        # Create new instance of the object
        self.exportDlg = panelExportData(self, self.icons)
        self.exportDlg.Show()
#         if dlg.ShowModal() == wx.ID_OK:
#             print('Yes')
#         dlg.Destroy()

    def OnShowAllPeaks(self, evt):
        """
        This function will show all peak lists from a file
        """
        print()

    def onDuplicateIons(self, evt):

        # Create a list of keys in the dictionary
        keyList = []
        if len(self.presenter.documentsDict) == 0:
            self.presenter.onThreading(None, ('There are no documents to copy peaks to!', 4),
                                       action='updateStatusbar')
            return
        elif self.peaklist.GetItemCount() == 0:
            self.presenter.onThreading(None, ('There are no peaks in the table. Try adding some first!', 4),
                                       action='updateStatusbar')
            return

        keyList.append('all')
        for key in self.presenter.documentsDict:
            keyList.append(key)

        self.duplicateDlg = panelDuplicateIons(self, keyList)
        self.duplicateDlg.Show()

    def findItem(self, mzStart, mzEnd, filename):
        """ find index of item with the provided parameters """

        columns = [self.config.peaklistColNames['start'],
                   self.config.peaklistColNames['end'],
                   self.config.peaklistColNames['filename']]
        rows = self.peaklist.GetItemCount()

        # Iterate over row and columns to get data
        for row in range(rows):
            tempRow = []
            for col in columns:
                itemData = self.peaklist.GetItem(itemId=row, col=col).GetText()
                # Add to list
                tempRow.append(itemData)
            # Check if correct
            if tempRow[0] == mzStart and tempRow[1] == mzEnd and tempRow[2] == filename:
                return row

        # If found nothing, return nothing
        return None

    def OnGetItemInformation(self, itemID, return_list=False):
        information = self.peaklist.on_get_item_information(itemID)

        # add additional data
        information['ionName'] = "{}-{}".format(information['start'], information['end'])
        information['color_255to1'] = convertRGB255to1(information['color'], decimals=3)

        # get document
        document = self.data_handling._on_get_document(information["document"])

        # check whether the ion has any previous information
        min_threshold, max_threshold = 0, 1
        try:
            if information['ionName'] in document.IMS2Dions:
                min_threshold = document.IMS2Dions[information['ionName']].get('min_threshold', 0)
                max_threshold = document.IMS2Dions[information['ionName']].get('max_threshold', 1)
        except AttributeError:
            pass

        information['min_threshold'] = min_threshold
        information['max_threshold'] = max_threshold

        # Check whether the ion has combined ions
        parameters = None
        try:
            parameters = document.IMS2DCombIons[information['ionName']].get('parameters', None)
        except (KeyError, AttributeError):
            pass
        information['parameters'] = parameters

        return information

    def OnGetValue(self, value_type='color'):
        information = self.OnGetItemInformation(self.peaklist.item_id)

        if value_type == 'start':
            return information['start']
        elif value_type == 'end':
            return information['end']
        elif value_type == 'color':
            return information['color']
        elif value_type == 'charge':
            return information['charge']
        elif value_type == 'colormap':
            return information['colormap']
        elif value_type == 'intensity':
            return information['intensity']
        elif value_type == 'mask':
            return information['mask']
        elif value_type == 'method':
            return information['method']
        elif value_type == 'document':
            return information['document']
        elif value_type == 'label':
            return information['label']
        elif value_type == 'ionName':
            return information['ionName']

    def on_update_value_in_peaklist(self, item_id, value_type, value):

        if value_type == 'start':
            self.peaklist.SetStringItem(item_id, self.config.peaklistColNames["start"], str(value))
        elif value_type == 'end':
            self.peaklist.SetStringItem(item_id, self.config.peaklistColNames["end"], str(value))
        elif value_type == 'charge':
            self.peaklist.SetStringItem(item_id, self.config.peaklistColNames["charge"], str(value))
        elif value_type == 'intensity':
            self.peaklist.SetStringItem(item_id, self.config.peaklistColNames["intensity"], str(value))
        elif value_type == 'color':
            color_255, color_1, font_color = value
            self.peaklist.SetItemBackgroundColour(item_id, color_255)
            self.peaklist.SetStringItem(item_id, self.config.peaklistColNames["color"], str(color_1))
            self.peaklist.SetItemTextColour(item_id, font_color)
        elif value_type == 'color_text':
            self.peaklist.SetItemBackgroundColour(item_id, value)
            self.peaklist.SetStringItem(item_id, self.config.peaklistColNames["color"],
                                        str(convertRGB255to1(value)))
            self.peaklist.SetItemTextColour(item_id, determineFontColor(value, return_rgb=True))
        elif value_type == 'colormap':
            self.peaklist.SetStringItem(item_id, self.config.peaklistColNames["colormap"], str(value))
        elif value_type == 'alpha':
            self.peaklist.SetStringItem(item_id, self.config.peaklistColNames["alpha"], str(value))
        elif value_type == 'mask':
            self.peaklist.SetStringItem(item_id, self.config.peaklistColNames["mask"], str(value))
        elif value_type == 'label':
            self.peaklist.SetStringItem(item_id, self.config.peaklistColNames["label"], str(value))
        elif value_type == 'method':
            self.peaklist.SetStringItem(item_id, self.config.peaklistColNames["method"], str(value))
        elif value_type == 'document':
            self.peaklist.SetStringItem(item_id, self.config.peaklistColNames["filename"], str(value))

    def OnOpenEditor(self, evt):

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
                print('Please select item in the table first.')
                return
            dlg_kwargs = self.OnGetItemInformation(self.peaklist.item_id)

            self.editItemDlg = panelModifyIonSettings(self,
                                                      self.presenter,
                                                      self.config,
                                                      **dlg_kwargs)
            self.editItemDlg.Centre()
            self.editItemDlg.Show()
        elif evtID == ID_ionPanel_edit_selected:
            while rows >= 0:
                if self.peaklist.IsChecked(rows):
                    information = self.OnGetItemInformation(rows)

                    dlg_kwargs = {'select': self.peaklist.IsChecked(rows),
                                  'color': information['color'],
                                  'title': information['ionName'],
                                  'min_threshold': information['min_threshold'],
                                  'max_threshold': information['max_threshold'],
                                  'label': information['label'],
                                  'id': rows
                                  }

                    self.editItemDlg = panelModifyIonSettings(self,
                                                              self.presenter,
                                                              self.config,
                                                              **dlg_kwargs)
                    self.editItemDlg.Show()
                rows -= 1
        elif evtID == ID_ionPanel_edit_all:
            for row in range(rows):
                information = self.OnGetItemInformation(row)

                dlg_kwargs = {'select': self.peaklist.IsChecked(row),
                              'color': information['color'],
                              'title': information['ionName'],
                              'min_threshold': information['min_threshold'],
                              'max_threshold': information['max_threshold'],
                              'label': information['label'],
                              'id': row
                              }

                self.editItemDlg = panelModifyIonSettings(self,
                                                          self.presenter,
                                                          self.config,
                                                          **dlg_kwargs)
                self.editItemDlg.Show()

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
                color_255 = convertRGB1to255(literal_eval(self.OnGetValue(value_type='color')), 3)
            except Exception:
                color_255 = self.config.customColors[randomIntegerGenerator(0, 15)]

            self.on_update_value_in_peaklist(itemID, "color_text", color_255)
            if give_value:
                return color_255

    def OnGetColor(self, evt):
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
                self.peaklist.SetStringItem(row,
                                            self.config.peaklistColNames['colormap'],
                                            str(colormap))

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
            colors = self.presenter.view.panelPlots.onChangePalette(
                None, n_colors=check_count, return_colors=True)
        elif evt.GetId() == ID_ionPanel_changeColorBatch_color:
            __, color_1, __ = self.OnGetColor(None)
            if color_1 is None:
                return
            colors = [color_1] * check_count
        else:
            colors = self.presenter.view.panelPlots.onGetColormapList(
                n_colors=check_count)

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

        # get item info
        if itemInfo is None:
            itemInfo = self.OnGetItemInformation(self.peaklist.item_id)

        # get item
        document = self.data_handling._on_get_document(itemInfo['document'])

        processed_name = "{} (processed)".format(itemInfo['ionName'])
        keywords = ['color', 'colormap', 'alpha', 'mask', 'label', 'min_threshold', 'max_threshold', 'charge']

        if itemInfo['ionName'] in document.IMS2Dions:
            for keyword in keywords:
                keyword_name = self.__check_keyword(keyword)
                document.IMS2Dions[itemInfo['ionName']][keyword_name] = itemInfo[keyword]
                try:
                    document.IMS2Dions[processed_name][keyword_name] = itemInfo[keyword]
                except KeyError:
                    pass

        if itemInfo['ionName'] in document.IMS2DCombIons:
            for keyword in keywords:
                keyword_name = self.__check_keyword(keyword)
                document.IMS2DCombIons[itemInfo['ionName']][keyword_name] = itemInfo[keyword]
                try:
                    document.IMS2DCombIons[processed_name][keyword_name] = itemInfo[keyword]
                except Exception:
                    pass

        if itemInfo['ionName'] in document.IMS2DionsProcess:
            for keyword in keywords:
                keyword_name = self.__check_keyword(keyword)
                document.IMS2DionsProcess[itemInfo['ionName']][keyword_name] = itemInfo[keyword]
                try:
                    document.IMS2DionsProcess[processed_name][keyword_name] = itemInfo[keyword]
                except KeyError:
                    pass
        if itemInfo['ionName'] in document.IMSRTCombIons:
            for keyword in keywords:
                keyword_name = self.__check_keyword(keyword)
                document.IMSRTCombIons[itemInfo['ionName']][keyword_name] = itemInfo[keyword]
                try:
                    document.IMSRTCombIons[processed_name][keyword_name] = itemInfo[keyword]
                except KeyError:
                    pass

        # Update document
        self.data_handling.on_update_document(document, "no_refresh")

    def on_remove_deleted_item(self, document):
        """
        @param document: title of the document to be removed from the list
        """
        row = self.peaklist.GetItemCount() - 1
        while (row >= 0):
            info = self.OnGetItemInformation(itemID=row)
            if info['document'] == document:
                self.peaklist.DeleteItem(row)
                row -= 1
            else:
                row -= 1

    def on_open_peak_list(self, evt):
        """
        This function opens a formatted CSV file with peaks
        """
        dlg = wx.FileDialog(self.presenter.view, "Choose a text file (m/z, window size, charge):",
                            wildcard="*.csv;*.txt",
                            style=wx.FD_DEFAULT_STYLE | wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_CANCEL:
            return
        else:

            manual = self.presenter.checkIfAnyDocumentsAreOfType(type='Type: MANUAL')
            origami = self.presenter.checkIfAnyDocumentsAreOfType(type='Type: ORIGAMI')
            infrared = self.presenter.checkIfAnyDocumentsAreOfType(type='Type: Infrared')
            docList = manual + origami + infrared
            if len(docList) == 0:
                args = ("Please create open or create a new document which can extract MS/IM-MS data", 4, 5)
                self.presenter.onThreading(evt, args, action='updateStatusbar')
                return
            elif len(docList) == 1:
                document_title = docList[0]
            else:
                document_panel = DialogSelectDocument(
                    self.presenter.view, presenter=self.presenter, document_list=docList, allow_new_document=False)
                if document_panel.ShowModal() == wx.ID_OK:
                    pass

                document_title = document_panel.current_document
                if document_title is None:
                    return

            # Create shortcut
            delimiter, __ = checkExtension(input=dlg.GetPath().encode('ascii', 'replace'))
            peaklist = read_csv(dlg.GetPath(), delimiter=delimiter)
            peaklist = peaklist.fillna("")
            print(peaklist)
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
            colors = self.presenter.view.panelPlots.onChangePalette(None, n_colors=count + 1, return_colors=True)

            # iterate
            for peak in range(len(peaklist)):
                print(peak)
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

                self.peaklist.Append([
                    str(min_value),
                    str(max_value),
                    str(charge_value),
                    "",
                    str(roundRGB(color_value)),
                    self.config.overlay_cmaps[randomIntegerGenerator(0, len(self.config.overlay_cmaps))],
                    str(self.config.overlay_defaultAlpha),
                    str(self.config.overlay_defaultMask),
                    str(label_value),
                    '',
                    document_title])
                try:
                    color_value = convertRGB1to255(color_value)
                    self.peaklist.SetItemBackgroundColour(self.peaklist.GetItemCount() - 1,
                                                          color_value)
                    self.peaklist.SetItemTextColour(self.peaklist.GetItemCount() - 1,
                                                    determineFontColor(color_value, return_rgb=True))
                except Exception:
                    pass
            self.presenter.view.on_toggle_panel(evt=ID_window_ionList, check=True)
            dlg.Destroy()

    def on_check_selected(self, evt):
        """
        Check current item when letter S is pressed on the keyboard
        """
        check = not self.peaklist.IsChecked(index=self.peaklist.item_id)
        self.peaklist.CheckItem(self.peaklist.item_id, check=check)

    def on_add_blank_document_overlay(self, evt):
        self.presenter.onAddBlankDocument(evt=None, document_type='overlay')

    def on_extract_all(self, evt):
        self.data_handling.on_extract_2D_from_mass_range_fcn(None, extract_type="all")

    def on_extract_selected(self, evt):
        self.data_handling.on_extract_2D_from_mass_range_fcn(None, extract_type="selected")

    def on_extract_new(self, evt):
        self.data_handling.on_extract_2D_from_mass_range_fcn(None, extract_type="new")

    def on_overlay_mobiligram(self, evt):
        self.presenter.on_overlay_1D(source="ion", plot_type="mobiligram")

    def on_overlay_chromatogram(self, evt):
        self.presenter.on_overlay_1D(source="ion", plot_type="chromatogram")

    def on_overlay_heatmap(self, evt):
        self.presenter.on_overlay_2D(source="ion")

    def on_add_to_table(self, add_dict, check_color=True):

        # get color
        color = add_dict.get("color", self.config.customColors[randomIntegerGenerator(0, 15)])
        # check for duplicate color
        if check_color:
            color = self.on_check_duplicate_colors(color)

        # add to peaklist
        self.peaklist.Append(["",
                              str(add_dict.get("mz_start", "")),
                              str(add_dict.get("mz_end", "")),
                              str(add_dict.get("charge", "")),
                              str(add_dict.get("mz_ymax", "")),
                              str(roundRGB(convertRGB255to1(color))),
                              str(add_dict.get("colormap", "")),
                              str(add_dict.get("alpha", "")),
                              str(add_dict.get("mask", "")),
                              str(add_dict.get("label", "")),
                              str(add_dict.get("method", "")),
                              str(add_dict.get("document", ""))])
        self.peaklist.SetItemBackgroundColour(self.peaklist.GetItemCount() - 1,
                                              color)
        self.peaklist.SetItemTextColour(self.peaklist.GetItemCount() - 1,
                                        determineFontColor(color, return_rgb=True))

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

            return randomColorGenerator(return_as_255=True)

        return new_color

    def on_replot_patch_on_MS(self, evt):
        """
        This function replots the rectangles in the RT window during Linear DT mode
        """

        count = self.peaklist.GetItemCount()
        currentDoc = self.presenter.currentDoc
        if currentDoc == "Documents" or currentDoc is None:
            return
        document = self.presenter.documentsDict[currentDoc]

        # Replot RT for current document
        msX = document.massSpectrum['xvals']
        msY = document.massSpectrum['yvals']
        try:
            xlimits = document.massSpectrum['xlimits']
        except KeyError:
            xlimits = [document.parameters['startMS'], document.parameters['endMS']]
        # Change panel and plot
        self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['MS'])

        if not self.presenter.view.panelPlots._on_check_plot_names(document.title, "Mass Spectrum", "MS"):
            name_kwargs = {"document": document.title, "dataset": "Mass Spectrum"}
            self.presenter.view.panelPlots.on_plot_MS(msX, msY, xlimits=xlimits, replot=True,
                                                      set_page=True, **name_kwargs)

        if count == 0:
            self.presenter.view.panelPlots.on_clear_patches(plot="MS", repaint=True)
            return

        ymin, height = 0, 100000000000
        last = self.peaklist.GetItemCount() - 1
        self.presenter.view.panelPlots.on_clear_patches(plot="MS", repaint=False)
        # Iterate over the list and plot rectangle one by one
        for row in range(count):
            itemInfo = self.OnGetItemInformation(itemID=row)
            xmin = itemInfo['start']
            xmax = itemInfo['end']
            color = itemInfo['color_255to1']
            width = xmax - xmin
            if row == last:
                self.presenter.view.panelPlots.on_plot_patches(xmin, ymin, width, height, color=color,
                                                               alpha=self.config.markerTransparency_1D, plot="MS",
                                                               repaint=True)
            else:
                self.presenter.view.panelPlots.on_plot_patches(xmin, ymin, width, height, color=color,
                                                               alpha=self.config.markerTransparency_1D, plot="MS",
                                                               repaint=False)

        self.on_replot_patch_on_MS(evt=None)

    def on_delete_item(self, evt):

        itemInfo = self.OnGetItemInformation(itemID=self.peaklist.item_id)
        dlg = dlgBox(
            type="Question",
            exceptionMsg="Are you sure you would like to delete {} from {}?\nThis action cannot be undone.".format(
                itemInfo['ionName'],
                itemInfo['document']))
        if dlg == wx.ID_NO:
            print("The operation was cancelled")
            return

        document = self.data_handling._on_get_document(itemInfo['document'])

        __, __ = self.view.panelDocuments.documents.on_delete_data__heatmap(
            document, itemInfo['document'], delete_type="heatmap.all.one",
            ion_name=itemInfo['ionName'])

    def on_delete_selected(self, evt):

        itemID = self.peaklist.GetItemCount() - 1
        while (itemID >= 0):
            if self.peaklist.IsChecked(index=itemID):
                itemInfo = self.OnGetItemInformation(itemID=itemID)
                msg = "Are you sure you would like to delete {} from {}?\nThis action cannot be undone.".format(
                    itemInfo['ionName'], itemInfo['document'])
                dlg = dlgBox(exceptionMsg=msg, type="Question")
                if dlg == wx.ID_NO:
                    print("The operation was cancelled")
                    continue

                document = self.data_handling._on_get_document(itemInfo['document'])
                __, __ = self.view.panelDocuments.documents.on_delete_data__heatmap(
                    document, itemInfo['document'], delete_type="heatmap.all.one",
                    ion_name=itemInfo['ionName'])
            itemID -= 1

    def on_delete_all(self, evt):

        msg = "Are you sure you would like to delete all classifiers from all documents?\nThis action cannot be undone."
        dlg = dlgBox(exceptionMsg=msg, type="Question")
        if dlg == wx.ID_NO:
            print("The operation was cancelled")
            return

        itemID = self.peaklist.GetItemCount() - 1
        while (itemID >= 0):
            itemInfo = self.OnGetItemInformation(itemID=itemID)
            document = self.data_handling._on_get_document(itemInfo['document'])
            __, __ = self.view.panelDocuments.documents.on_delete_data__heatmap(
                document, itemInfo['document'], delete_type="heatmap.all.all")
            itemID -= 1

    def delete_row_from_table(self, delete_item_name=None, delete_document_title=None):

        rows = self.peaklist.GetItemCount() - 1
        while rows >= 0:
            itemInfo = self.OnGetItemInformation(rows)

            if itemInfo['ionName'] == delete_item_name and itemInfo['document'] == delete_document_title:
                self.peaklist.DeleteItem(rows)
                rows = 0
                return
            elif delete_item_name is None and itemInfo['document'] == delete_document_title:
                self.peaklist.DeleteItem(rows)
            rows -= 1

    @staticmethod
    def __check_keyword(keyword_name):
        if keyword_name == 'colormap':
            keyword_name = 'cmap'
        return keyword_name


class panelExportData(wx.MiniFrame):
    """
    Export data from table
    """

    def __init__(self, parent, icons):
        wx.MiniFrame.__init__(self, parent, -1, 'Export', size=(400, 300),
                              style=wx.DEFAULT_FRAME_STYLE & ~
                              (wx.RESIZE_BORDER | wx.MAXIMIZE_BOX))

        self.parent = parent
        self.icons = icons

        # make gui items
        self.make_gui()
        wx.EVT_CLOSE(self, self.on_close)

    def make_gui(self):

        # make panel
        peaklist = self.makePeaklistPanel()

        # pack element
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(peaklist, 0, wx.EXPAND, 0)

        # fit layout
        self.mainSizer.Fit(self)
        self.SetSizer(self.mainSizer)
        self.Center()

    def on_close(self, evt):
        """Destroy this frame."""

        self.Destroy()
    # ----

    def makePeaklistPanel(self):
        """Peaklist export panel."""

        panel = wx.Panel(self, -1)

        # make elements
        self.peaklistColstartMZ_check = wx.CheckBox(panel, -1, "start m/z")
        self.peaklistColstartMZ_check.SetValue(True)

        self.peaklistColendMZ_check = wx.CheckBox(panel, -1, "end m/z")
        self.peaklistColendMZ_check.SetValue(True)

        self.peaklistColCharge_check = wx.CheckBox(panel, -1, "z")
        self.peaklistColCharge_check.SetValue(True)

        self.peaklistColFilename_check = wx.CheckBox(panel, -1, "file")
        self.peaklistColFilename_check.SetValue(True)

        self.peaklistColMethod_check = wx.CheckBox(panel, -1, "method")
        self.peaklistColMethod_check.SetValue(True)

        self.peaklistColRelIntensity_check = wx.CheckBox(panel, -1, "relative intensity")
        self.peaklistColRelIntensity_check.SetValue(True)

#         peaklistSelect_label = wx.StaticText(panel, -1, "Export:")
#         self.peaklistSelect_choice = wx.Choice(panel, -1, choices=['All Peaks', 'Selected Peaks'], size=(200, -1))
#         self.peaklistSelect_choice.Select(0)

        peaklistFormat_label = wx.StaticText(panel, -1, "Format:")
        self.peaklistFormat_choice = wx.Choice(panel, -1, choices=['ASCII', 'ASCII with Headers'], size=(200, -1))
        self.peaklistFormat_choice.Select(1)

        peaklistSeparator_label = wx.StaticText(panel, -1, "Separator:")
        self.peaklistSeparator_choice = wx.Choice(panel, -1, choices=['Comma', 'Semicolon', 'Tab'], size=(200, -1))
        self.peaklistSeparator_choice.Select(0)

        self.exportBtn = wx.Button(panel, -1, "Export", size=(-1, 22))

        GRIDBAG_VSPACE = 7
        GRIDBAG_HSPACE = 5
        PANEL_SPACE_MAIN = 10

        # pack elements
        grid1 = wx.GridBagSizer(GRIDBAG_VSPACE, GRIDBAG_HSPACE)
        grid1.Add(self.peaklistColstartMZ_check, (0, 0))
        grid1.Add(self.peaklistColendMZ_check, (1, 0))
        grid1.Add(self.peaklistColCharge_check, (2, 0))
        grid1.Add(self.peaklistColFilename_check, (0, 2))
        grid1.Add(self.peaklistColMethod_check, (1, 2))
        grid1.Add(self.peaklistColRelIntensity_check, (2, 2))

        grid2 = wx.GridBagSizer(GRIDBAG_VSPACE, GRIDBAG_HSPACE)
#         grid2.Add(peaklistSelect_label, (0,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
#         grid2.Add(self.peaklistSelect_choice, (0,1))
        grid2.Add(peaklistFormat_label, (1, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid2.Add(self.peaklistFormat_choice, (1, 1))
        grid2.Add(peaklistSeparator_label, (2, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid2.Add(self.peaklistSeparator_choice, (2, 1))

        grid2.Add(self.exportBtn, (3, 0))

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(grid1, 0, wx.ALIGN_CENTER | wx.ALL, PANEL_SPACE_MAIN)
        mainSizer.Add(grid2, 0, wx.ALIGN_CENTER | wx.ALL, PANEL_SPACE_MAIN)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)

        self.exportBtn.Bind(wx.EVT_BUTTON, self.onExportFile)

        return panel

    def onExportParameters(self):
        choicesData = {0: 'ASCII', 1: 'ASCII with Headers'}
        choicesDelimiter = {0: ',', 1: ';', 2: 'tab'}

        self.useStartMZ = self.peaklistColstartMZ_check.GetValue()
        self.useEndMZ = self.peaklistColendMZ_check.GetValue()
        self.useCharge = self.peaklistColCharge_check.GetValue()
        self.useFilename = self.peaklistColFilename_check.GetValue()
        self.useMethod = self.peaklistColMethod_check.GetValue()
        self.useRelIntensity = self.peaklistColRelIntensity_check.GetValue()

        self.dataChoice = choicesData[self.peaklistFormat_choice.GetSelection()]
        self.delimiter = choicesDelimiter[self.peaklistSeparator_choice.GetSelection()]

    def onExportFile(self, evt):

        fileName = 'peaklist.txt'
        fileType = "ASCII file|*.txt"

        self.onExportParameters()

        dlg = wx.FileDialog(self, "Save peak list to file...", "", "", fileType,
                            wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            dlg.Destroy()
        else:
            dlg.Destroy()
            return


class panelDuplicateIons(wx.MiniFrame):
    """
    Duplicate ions
    """

    def __init__(self, parent, keyList):
        wx.MiniFrame.__init__(self, parent, -1, 'Duplicate...', size=(400, 300),
                              style=wx.DEFAULT_FRAME_STYLE & ~
                              (wx.RESIZE_BORDER | wx.MAXIMIZE_BOX))

        self.parent = parent
        self.duplicateList = keyList

        # make gui items
        self.make_gui()

        wx.EVT_CLOSE(self, self.on_close)

    def on_close(self, evt):
        """Destroy this frame."""

        self.Destroy()
    # ----

    def make_gui(self):

        # make panel
        panel = self.makeDuplicatePanel()

        # pack element
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(panel, 0, wx.EXPAND, 0)

        # bind
        self.okBtn.Bind(wx.EVT_BUTTON, self.onDuplicate)
        self.cancelBtn.Bind(wx.EVT_BUTTON, self.on_close)

        # fit layout
        self.mainSizer.Fit(self)
        self.SetSizer(self.mainSizer)

    def makeDuplicatePanel(self):

        panel = wx.Panel(self, -1)
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        duplicateFrom_label = wx.StaticText(panel, -1, "Duplicate from:")
        self.documentListFrom_choice = wx.Choice(panel, -1, choices=self.duplicateList, size=(300, -1))
        self.documentListFrom_choice.Select(1)

        duplicateTo_label = wx.StaticText(panel, -1, "to:")
        self.documentListTo_choice = wx.Choice(panel, -1, choices=self.duplicateList, size=(300, -1))
        self.documentListTo_choice.Select(0)

        selection_label = wx.StaticText(panel, -1, "Which ions:")
        self.all_radio = wx.RadioButton(panel, -1, 'All')
        self.all_radio.SetValue(True)
        self.selected_radio = wx.RadioButton(panel, -1, 'Selected')

        self.okBtn = wx.Button(panel, -1, "Duplicate", size=(-1, 22))
        self.cancelBtn = wx.Button(panel, -1, "Cancel", size=(-1, 22))

        GRIDBAG_VSPACE = 7
        GRIDBAG_HSPACE = 5
        PANEL_SPACE_MAIN = 10

        # pack elements
        grid = wx.GridBagSizer(GRIDBAG_VSPACE, GRIDBAG_HSPACE)

        grid.Add(selection_label, (0, 0))
        grid.Add(self.all_radio, (0, 1), wx.GBSpan(1, 1))
        grid.Add(self.selected_radio, (0, 2), wx.GBSpan(1, 1))

        grid.Add(duplicateFrom_label, (1, 0))
        grid.Add(self.documentListFrom_choice, (1, 1), wx.GBSpan(1, 2))

        grid.Add(duplicateTo_label, (2, 0))
        grid.Add(self.documentListTo_choice, (2, 1), wx.GBSpan(1, 2))

        grid.Add(self.okBtn, (3, 1), wx.GBSpan(1, 1))
        grid.Add(self.cancelBtn, (3, 2), wx.GBSpan(1, 1))

        mainSizer.Add(grid, 0, wx.ALIGN_CENTER | wx.ALL, PANEL_SPACE_MAIN)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)

        return panel

    def onDuplicate(self, evt):
        # Which ions to duplicate
        if self.all_radio.GetValue():
            duplicateWhich = 'all'
        else:
            duplicateWhich = 'selected'

        # How many in the list

        rows = self.parent.peaklist.GetItemCount()
        columns = 3  # start, end, z

        # Which from and to which
        docFrom = self.documentListFrom_choice.GetStringSelection()
        docTo = self.documentListTo_choice.GetStringSelection()

        tempData = []
        if duplicateWhich == 'all':
            for i in range(1, self.documentListTo_choice.GetCount()):
                key = self.documentListTo_choice.GetString(i)
                if key == docFrom:
                    continue
                # Iterate over row and columns to get data
                for row in range(rows):
                    tempRow = []
                    for col in range(columns):
                        item = self.parent.peaklist.GetItem(itemId=row, col=col)
                        tempRow.append(item.GetText())
                    tempRow.append("")
                    tempRow.append("")
                    tempRow.append(key)
                    tempData.append(tempRow)
        elif duplicateWhich == 'selected':
            if docTo == docFrom:
                docTo = ''
            elif docTo == 'all':
                docTo = ''
            # Iterate over row and columns to get data
            for row in range(rows):
                if not self.parent.peaklist.IsChecked(index=row):
                    continue
                tempRow = []
                for col in range(columns):
                    item = self.parent.peaklist.GetItem(itemId=row, col=col)
                    tempRow.append(item.GetText())
                tempRow.append("")
                tempRow.append("")
                tempRow.append(docTo)
                tempData.append(tempRow)
#         print(tempData)

        # Add to table
        for row in tempData:
            self.parent.peaklist.Append(row)
        # Remove duplicates
        self.parent.onRemoveDuplicates(evt=None)
