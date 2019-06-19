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

import re
from copy import deepcopy
from os.path import split
import wx
from numpy import arange

from document import document as documents
from gui_elements.panel_modifyTextSettings import panelModifyTextSettings
from styles import makeMenuItem, makeTooltip, ListCtrl
from toolbox import (literal_eval, merge_two_dicts, removeListDuplicates, roundRGB)
from gui_elements.dialog_selectDocument import panelSelectDocument
from gui_elements.dialog_panelAsk import panelAsk
from gui_elements.misc_dialogs import dlgBox
from ids import ID_textPanel_addToDocument, ID_textPanel_assignColor, ID_textPanel_editItem, ID_textPanel_show_heatmap, \
    ID_textPanel_show_mobiligram, ID_textPanel_normalize1D, ID_useProcessedCombinedMenu, ID_textPanel_automaticOverlay, \
    ID_textPanel_check_selected, ID_textPanel_check_all, ID_textPanel_delete_rightClick, ID_textPanel_add_menu, \
    ID_textPanel_annotate_menu, ID_textPanel_remove_menu, ID_textPanel_process_menu, ID_textPanel_overlay_menu, \
    ID_textSelectOverlayMethod, ID_textPanel_show_chromatogram, ID_textPanel_show_process_heatmap, \
    ID_textPanel_annotate_charge_state, ID_textPanel_annotate_alpha, ID_textPanel_annotate_mask, ID_textPanel_annotate_min_threshold, \
    ID_textPanel_annotate_max_threshold, ID_textPanel_changeColorBatch_color, ID_textPanel_changeColorBatch_palette, \
    ID_textPanel_changeColorBatch_colormap, ID_textPanel_changeColormapBatch, ID_addNewOverlayDoc, ID_ionPanel_edit_all, \
    ID_textPanel_edit_selected, ID_textPanel_clear_selected, ID_textPanel_table_startCE, ID_textPanel_delete_all, \
    ID_textPanel_delete_selected, ID_textPanel_clear_all, ID_textPanel_process_selected, ID_textPanel_process_all, \
    ID_overlayTextfromList1D, ID_overlayTextfromListRT, ID_overlayTextFromList, ID_overlayTextfromListWaterfall, \
    ID_load_multiple_text_2D, ID_textPanel_table_endCE, ID_textPanel_table_charge, ID_textPanel_table_color, \
    ID_textPanel_table_colormap, ID_textPanel_table_alpha, ID_textPanel_table_mask, ID_textPanel_table_document, \
    ID_textPanel_table_label, ID_textPanel_table_shape, ID_textPanel_table_hideAll, ID_textPanel_table_restoreAll, \
    ID_textPanel_about_info
from utils.color import convertRGB1to255, determineFontColor, convertRGB255to1, randomColorGenerator
from utils.check import isempty
from utils.time import getTime
from utils.random import randomIntegerGenerator

import logging
logger = logging.getLogger("origami")


class panelMultipleTextFiles (wx.Panel):

    def __init__(self, parent, config, icons, presenter):
        wx.Panel.__init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                          size=wx.Size(300, -1), style=wx.TAB_TRAVERSAL)

        self.view = parent
        self.config = config
        self.presenter = presenter
        self.icons = icons

        self.allChecked = True
        self.reverse = False
        self.lastColumn = None
        self.listOfSelected = []
        self.addToDocument = False
        self.normalize1D = True
        self.plotAutomatically = True

        self._textPanel_peaklist = {
            0: {"name": "", "tag": "check", "type": "bool"},
            1: {"name": "min CE", "tag": "start", "type": "float"},
            2: {"name": "max CE", "tag": "end", "type": "float"},
            3: {"name": "z", "tag": "charge", "type": "int"},
            4: {"name": "color", "tag": "color", "type": "color"},
            5: {"name": "colormap", "tag": "colormap", "type": "str"},
            6: {"name": "\N{GREEK SMALL LETTER ALPHA}", "tag": "alpha", "type": "float"},
            7: {"name": "mask", "tag": "mask", "type": "float"},
            8: {"name": "label", "tag": "label", "type": "str"},
            9: {"name": "shape", "tag": "shape", "type": "str"},
            10: {"name": "file", "tag": "document", "type": "str"}}

        self.editItemDlg = None

        self.make_panel_gui()

        if self.plotAutomatically:
            self.combo.Bind(wx.EVT_COMBOBOX, self.on_overlay_heatmap)

        # add a couple of accelerators
        accelerators = [
            (wx.ACCEL_NORMAL, ord('A'), ID_textPanel_addToDocument),
            (wx.ACCEL_NORMAL, ord('C'), ID_textPanel_assignColor),
            (wx.ACCEL_NORMAL, ord('E'), ID_textPanel_editItem),
            (wx.ACCEL_NORMAL, ord('H'), ID_textPanel_show_heatmap),
            (wx.ACCEL_NORMAL, ord('M'), ID_textPanel_show_mobiligram),
            (wx.ACCEL_NORMAL, ord('N'), ID_textPanel_normalize1D),
            (wx.ACCEL_NORMAL, ord('P'), ID_useProcessedCombinedMenu),
            (wx.ACCEL_NORMAL, ord('O'), ID_textPanel_automaticOverlay),
            (wx.ACCEL_NORMAL, ord('S'), ID_textPanel_check_selected),
            (wx.ACCEL_NORMAL, ord('X'), ID_textPanel_check_all),
            (wx.ACCEL_NORMAL, wx.WXK_DELETE, ID_textPanel_delete_rightClick),
        ]
        self.SetAcceleratorTable(wx.AcceleratorTable(accelerators))

        wx.EVT_MENU(self, ID_textPanel_editItem, self.OnOpenEditor)
        wx.EVT_MENU(self, ID_textPanel_assignColor, self.on_assign_color)
        wx.EVT_MENU(self, ID_useProcessedCombinedMenu, self.on_enable_disable_tools)
        wx.EVT_MENU(self, ID_textPanel_automaticOverlay, self.on_enable_disable_tools)
        wx.EVT_MENU(self, ID_textPanel_addToDocument, self.on_enable_disable_tools)
        wx.EVT_MENU(self, ID_textPanel_normalize1D, self.on_enable_disable_tools)
        wx.EVT_MENU(self, ID_textPanel_show_heatmap, self.on_plot)
        wx.EVT_MENU(self, ID_textPanel_show_mobiligram, self.on_plot)
        wx.EVT_MENU(self, ID_textPanel_check_selected, self.on_check_selected)
        wx.EVT_MENU(self, ID_textPanel_delete_rightClick, self.on_delete_item)

    def __del__(self):
        pass

    def _setup_handling_and_processing(self):
        self.data_processing = self.view.data_processing
        self.data_handling = self.view.data_handling

    def make_panel_gui(self):
        """ Make panel GUI """
        # make toolbar
        toolbar = self.make_toolbar()
        self.makeListCtrl()

        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(toolbar, 0, wx.EXPAND, 0)
        self.mainSizer.Add(self.peaklist, 1, wx.EXPAND, 0)

        # fit layout
        self.mainSizer.Fit(self)
        self.SetSizer(self.mainSizer)
        self.SetSize((300, -1))
        self.Layout()

    def makeListCtrl(self):

        self.peaklist = ListCtrl(self, style=wx.LC_REPORT | wx.LC_VRULES, column_info=self._textPanel_peaklist)

        for item in self.config._textlistSettings:
            order = item['order']
            name = item['name']
            if item['show']:
                width = item['width']
            else:
                width = 0
            self.peaklist.InsertColumn(order, name, width=width,
                                       format=wx.LIST_FORMAT_CENTER)

        self.peaklist.Bind(wx.EVT_LEFT_DCLICK, self.on_double_click_on_item)
        self.peaklist.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.menu_right_click)
        self.peaklist.Bind(wx.EVT_LIST_COL_RIGHT_CLICK, self.menu_column_right_click)

    def on_double_click_on_item(self, evt):
        if self.peaklist.item_id != -1:
            if not self.editItemDlg:
                self.OnOpenEditor(evt=None)
            else:
                self.editItemDlg.onUpdateGUI(self.OnGetItemInformation(self.peaklist.item_id))

    def on_add_blank_document_overlay(self, evt):
        self.presenter.onAddBlankDocument(evt=None, document_type='overlay')

    def make_toolbar(self):

        # Make bindings
        self.Bind(wx.EVT_BUTTON, self.menu_add_tools, id=ID_textPanel_add_menu)
        self.Bind(wx.EVT_BUTTON, self.menu_annotate_tools, id=ID_textPanel_annotate_menu)
        self.Bind(wx.EVT_BUTTON, self.menu_remove_tools, id=ID_textPanel_remove_menu)
        self.Bind(wx.EVT_BUTTON, self.menu_process_tools, id=ID_textPanel_process_menu)
        self.Bind(wx.EVT_BUTTON, self.menu_overlay_tools, id=ID_textPanel_overlay_menu)

        self.add_btn = wx.BitmapButton(
            self, ID_textPanel_add_menu, self.icons.iconsLib['add16'],
            size=(18, 18), style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL)
        self.add_btn.SetToolTip(makeTooltip("Add..."))

        self.remove_btn = wx.BitmapButton(
            self, ID_textPanel_remove_menu, self.icons.iconsLib['remove16'],
            size=(18, 18), style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL)
        self.remove_btn.SetToolTip(makeTooltip("Remove..."))

        self.annotate_btn = wx.BitmapButton(
            self, ID_textPanel_annotate_menu, self.icons.iconsLib['annotate16'],
            size=(18, 18), style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL)
        self.annotate_btn.SetToolTip(makeTooltip("Annotate..."))

        self.process_btn = wx.BitmapButton(
            self, ID_textPanel_process_menu, self.icons.iconsLib['process16'],
            size=(18, 18), style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL)
        self.process_btn.SetToolTip(makeTooltip("Process..."))

        self.overlay_btn = wx.BitmapButton(
            self, ID_textPanel_overlay_menu, self.icons.iconsLib['overlay16'],
            size=(18, 18), style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL)
        self.overlay_btn.SetToolTip(makeTooltip("Overlay selected ions..."))

        self.combo = wx.ComboBox(self,
                                 ID_textSelectOverlayMethod,
                                 size=(105, -1),
                                 choices=self.config.overlayChoices,
                                 style=wx.CB_READONLY)

        vertical_line_1 = wx.StaticLine(self, -1, style=wx.LI_VERTICAL)

        self.info_btn = wx.BitmapButton(
            self, ID_textPanel_about_info, self.icons.iconsLib['info16'],
            size=(18, 18), style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL)
        self.info_btn.SetToolTip(makeTooltip("Information..."))

        # button grid
        btn_grid_vert = wx.GridBagSizer(2, 2)
        x = 0
        btn_grid_vert.Add(self.add_btn, (x, 0), wx.GBSpan(
            1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        btn_grid_vert.Add(self.remove_btn, (x, 1), wx.GBSpan(
            1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        btn_grid_vert.Add(self.annotate_btn, (x, 2), wx.GBSpan(
            1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        btn_grid_vert.Add(self.process_btn, (x, 3), wx.GBSpan(
            1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        btn_grid_vert.Add(self.overlay_btn, (x, 4), wx.GBSpan(
            1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        btn_grid_vert.Add(self.combo, (x, 5), wx.GBSpan(
            1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        btn_grid_vert.Add(vertical_line_1, (x, 6), wx.GBSpan(1, 1), flag=wx.EXPAND)
        btn_grid_vert.Add(self.info_btn, (x, 7), wx.GBSpan(
            1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)

        return btn_grid_vert

    def menu_right_click(self, evt):

        # Make bindings
        self.Bind(wx.EVT_MENU, self.on_plot, id=ID_textPanel_show_chromatogram)
        self.Bind(wx.EVT_MENU, self.on_plot, id=ID_textPanel_show_mobiligram)
        self.Bind(wx.EVT_MENU, self.on_plot, id=ID_textPanel_show_heatmap)
        self.Bind(wx.EVT_MENU, self.on_plot, id=ID_textPanel_show_process_heatmap)
        self.Bind(wx.EVT_MENU, self.on_delete_item, id=ID_textPanel_delete_rightClick)
        self.Bind(wx.EVT_MENU, self.OnOpenEditor, id=ID_textPanel_editItem)
        self.Bind(wx.EVT_MENU, self.on_assign_color, id=ID_textPanel_assignColor)

        self.peaklist.item_id = evt.GetIndex()
        menu = wx.Menu()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_textPanel_show_chromatogram,
                                     text='Show chromatogram',
                                     bitmap=self.icons.iconsLib['chromatogram_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_textPanel_show_mobiligram,
                                     text='Show mobiligram\tM',
                                     bitmap=self.icons.iconsLib['mobiligram_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_textPanel_show_heatmap,
                                     text='Show heatmap\tH',
                                     bitmap=self.icons.iconsLib['heatmap_16']))
        menu.Append(ID_textPanel_show_process_heatmap, "Process and show heatmap")
        menu.AppendSeparator()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_textPanel_assignColor,
                                     text='Assign new color\tC',
                                     bitmap=self.icons.iconsLib['color_panel_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_textPanel_editItem,
                                     text='Edit file information\tE',
                                     bitmap=self.icons.iconsLib['info16']))
        menu.AppendSeparator()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_textPanel_delete_rightClick,
                                     text='Remove item\tDelete',
                                     bitmap=self.icons.iconsLib['bin16']))
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
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_textPanel_annotate_charge_state,
                                     text='Assign charge state to selected items',
                                     bitmap=self.icons.iconsLib['assign_charge_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_textPanel_annotate_alpha,
                                     text='Assign transparency value to selected ions',
                                     bitmap=self.icons.iconsLib['transparency_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_textPanel_annotate_mask,
                                     text='Assign mask value to selected items',
                                     bitmap=self.icons.iconsLib['mask_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_textPanel_annotate_min_threshold,
                                     text='Assign minimum threshold to selected items',
                                     bitmap=self.icons.iconsLib['min_threshold_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_textPanel_annotate_max_threshold,
                                     text='Assign maximum threshold to selected items',
                                     bitmap=self.icons.iconsLib['max_threshold_16']))
        menu.AppendSeparator()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_textPanel_changeColorBatch_color,
                                     text='Assign color for selected items',
                                     bitmap=self.icons.iconsLib['color_panel_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_textPanel_changeColorBatch_palette,
                                     text='Color selected items using color palette',
                                     bitmap=self.icons.iconsLib['blank_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_textPanel_changeColorBatch_colormap,
                                     text='Color selected items using colormap',
                                     bitmap=self.icons.iconsLib['blank_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_textPanel_changeColormapBatch,
                                     text='Randomize colormap for selected items',
                                     bitmap=self.icons.iconsLib['randomize_16']))

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def menu_add_tools(self, evt):
        self.Bind(wx.EVT_MENU, self.presenter.onAddBlankDocument, id=ID_addNewOverlayDoc)
        self.Bind(wx.EVT_MENU, self.on_add_blank_document_overlay, id=ID_addNewOverlayDoc)

        menu = wx.Menu()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_load_multiple_text_2D,
                                     text='Add files\tCtrl+W',
                                     bitmap=self.icons.iconsLib['file_csv_16']))
        menu.AppendSeparator()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_addNewOverlayDoc,
                                     text='Create blank COMPARISON document\tAlt+D',
                                     bitmap=self.icons.iconsLib['new_document_16']))
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
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_textPanel_clear_all,
                                     text='Clear table',
                                     bitmap=self.icons.iconsLib['clear_16']))
        menu.Append(ID_textPanel_clear_selected, "Clear selected")
        menu.AppendSeparator()
        menu.Append(ID_textPanel_delete_selected, "Delete selected files")
        menu.Append(ID_textPanel_delete_all, "Delete all files")
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def menu_process_tools(self, evt):

        self.Bind(wx.EVT_TOOL, self.presenter.onProcessMultipleTextFiles, id=ID_textPanel_process_selected)
        self.Bind(wx.EVT_TOOL, self.presenter.onProcessMultipleTextFiles, id=ID_textPanel_process_all)

        menu = wx.Menu()
        menu.Append(ID_textPanel_process_selected, "Process selected files")
        menu.Append(ID_textPanel_process_all, "Process all files")
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def menu_overlay_tools(self, evt):

        self.Bind(wx.EVT_TOOL, self.on_overlay_mobiligram, id=ID_overlayTextfromList1D)
        self.Bind(wx.EVT_TOOL, self.on_overlay_chromatogram, id=ID_overlayTextfromListRT)
        self.Bind(wx.EVT_TOOL, self.on_overlay_heatmap, id=ID_overlayTextFromList)
        self.Bind(wx.EVT_TOOL, self.onOverlayWaterfall, id=ID_overlayTextfromListWaterfall)
        self.Bind(wx.EVT_MENU, self.on_enable_disable_tools, id=ID_useProcessedCombinedMenu)
        self.Bind(wx.EVT_TOOL, self.on_enable_disable_tools, id=ID_textPanel_addToDocument)
        self.Bind(wx.EVT_TOOL, self.on_enable_disable_tools, id=ID_textPanel_normalize1D)
        self.Bind(wx.EVT_TOOL, self.on_enable_disable_tools, id=ID_textPanel_automaticOverlay)

        menu = wx.Menu()
        self.addToDocument_check = menu.AppendCheckItem(
            ID_textPanel_addToDocument, "Add overlay plots to document\tA",
            help="Add overlay results to comparison document")
        self.addToDocument_check.Check(self.addToDocument)
        menu.AppendSeparator()
        self.normalize1D_check = menu.AppendCheckItem(
            ID_textPanel_normalize1D, "Normalize mobiligram/chromatogram dataset\tN",
            help="Normalize mobiligram/chromatogram before overlaying")
        self.normalize1D_check.Check(self.normalize1D)
        menu.Append(ID_overlayTextfromList1D, "Overlay mobiligrams (selected)")
        menu.Append(ID_overlayTextfromListRT, "Overlay chromatograms (selected)")
        menu.AppendSeparator()
        self.useProcessed_check = menu.AppendCheckItem(
            ID_useProcessedCombinedMenu, "Use processed data (when available)\tP",
            help="When checked, processed data is used in the overlay (2D) plots.")
        self.useProcessed_check.Check(self.config.overlay_usedProcessed)
        menu.AppendSeparator()
        self.automaticPlot_check = menu.AppendCheckItem(
            ID_textPanel_automaticOverlay, "Overlay automatically\tO",
            help="Ions will be extracted automatically")
        self.automaticPlot_check.Check(self.plotAutomatically)
        menu.Append(ID_overlayTextfromListWaterfall, "Overlay as waterfall (selected)")
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_overlayTextFromList,
                                     text='Overlay heatmaps (selected)\tAlt+W',
                                     bitmap=self.icons.iconsLib['heatmap_grid_16']))
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
        self.table_start = menu.AppendCheckItem(ID_textPanel_table_startCE, 'Table: Minimum energy')
        self.table_start.Check(self.config._textlistSettings[n]['show'])
        n = n + 1
        self.table_end = menu.AppendCheckItem(ID_textPanel_table_endCE, 'Table: Maximum energy')
        self.table_end.Check(self.config._textlistSettings[n]['show'])
        n = n + 1
        self.table_color = menu.AppendCheckItem(ID_textPanel_table_charge, 'Table: Charge')
        self.table_color.Check(self.config._textlistSettings[n]['show'])
        n = n + 1
        self.table_color = menu.AppendCheckItem(ID_textPanel_table_color, 'Table: Color')
        self.table_color.Check(self.config._textlistSettings[n]['show'])
        n = n + 1
        self.table_colormap = menu.AppendCheckItem(ID_textPanel_table_colormap, 'Table: Colormap')
        self.table_colormap.Check(self.config._textlistSettings[n]['show'])
        n = n + 1
        self.table_alpha = menu.AppendCheckItem(ID_textPanel_table_alpha, 'Table: Transparency')
        self.table_alpha.Check(self.config._textlistSettings[n]['show'])
        n = n + 1
        self.table_mask = menu.AppendCheckItem(ID_textPanel_table_mask, 'Table: Mask')
        self.table_mask.Check(self.config._textlistSettings[n]['show'])
        n = n + 1
        self.table_label = menu.AppendCheckItem(ID_textPanel_table_label, 'Table: Label')
        self.table_label.Check(self.config._textlistSettings[n]['show'])
        n = n + 1
        self.table_shape = menu.AppendCheckItem(ID_textPanel_table_shape, 'Table: Shape')
        self.table_shape.Check(self.config._textlistSettings[n]['show'])
        n = n + 1
        self.table_filename = menu.AppendCheckItem(ID_textPanel_table_document, 'Table: Filename')
        self.table_filename.Check(self.config._textlistSettings[n]['show'])
        menu.AppendSeparator()
        self.table_index = menu.AppendItem(makeMenuItem(parent=menu, id=ID_textPanel_table_hideAll,
                                                        text='Table: Hide all',
                                                        bitmap=self.icons.iconsLib['hide_table_16']))
        self.table_index = menu.AppendItem(makeMenuItem(parent=menu, id=ID_textPanel_table_restoreAll,
                                                        text='Table: Restore all',
                                                        bitmap=self.icons.iconsLib['show_table_16']))

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

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
                self.peaklist.SetItem(row, self.config.textlistColNames['colormap'], str(colormap))

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

        if evt.GetId() == ID_textPanel_changeColorBatch_palette:
            colors = self.presenter.view.panelPlots.onChangePalette(None, n_colors=check_count, return_colors=True)
        elif evt.GetId() == ID_textPanel_changeColorBatch_color:
            color = self.OnGetColor(None)
            colors = [color] * check_count
        else:
            colors = self.presenter.view.panelPlots.onGetColormapList(n_colors=check_count)

        check_count = 0
        for row in range(self.peaklist.GetItemCount()):
            self.peaklist.item_id = row
            if self.peaklist.IsChecked(index=row):
                color = colors[check_count]
                self.peaklist.SetItemBackgroundColour(row, convertRGB1to255(color))
                self.peaklist.SetItemTextColour(row, determineFontColor(convertRGB1to255(color), return_rgb=True))
                check_count += 1

            self.onUpdateDocument(evt=None)

    def on_update_peaklist_table(self, evt):
        evtID = evt.GetId()

        # check which event was triggered
        if evtID == ID_textPanel_table_startCE:
            col_index = self.config.textlistColNames['start']
        elif evtID == ID_textPanel_table_endCE:
            col_index = self.config.textlistColNames['end']
        elif evtID == ID_textPanel_table_charge:
            col_index = self.config.textlistColNames['charge']
        elif evtID == ID_textPanel_table_color:
            col_index = self.config.textlistColNames['color']
        elif evtID == ID_textPanel_table_colormap:
            col_index = self.config.textlistColNames['colormap']
        elif evtID == ID_textPanel_table_alpha:
            col_index = self.config.textlistColNames['alpha']
        elif evtID == ID_textPanel_table_mask:
            col_index = self.config.textlistColNames['mask']
        elif evtID == ID_textPanel_table_label:
            col_index = self.config.textlistColNames['label']
        elif evtID == ID_textPanel_table_shape:
            col_index = self.config.textlistColNames['shape']
        elif evtID == ID_textPanel_table_document:
            col_index = self.config.textlistColNames['filename']
        elif evtID == ID_textPanel_table_restoreAll:
            for i in range(len(self.config._textlistSettings)):
                self.config._textlistSettings[i]['show'] = True
                col_width = self.config._textlistSettings[i]['width']
                self.peaklist.SetColumnWidth(i, col_width)
            return
        elif evtID == ID_textPanel_table_hideAll:
            for i in range(len(self.config._textlistSettings)):
                self.config._textlistSettings[i]['show'] = False
                col_width = 0
                self.peaklist.SetColumnWidth(i, col_width)
            return

        # check values
        col_check = not self.config._textlistSettings[col_index]['show']
        self.config._textlistSettings[col_index]['show'] = col_check
        if col_check:
            col_width = self.config._textlistSettings[col_index]['width']
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
            static_text = 'Assign charge state to selected items.'
            ask_kwargs = {
                'static_text': static_text,
                'value_text': "",
                'validator': 'integer',
                'keyword': 'charge'}

        elif evt.GetId() == ID_textPanel_annotate_alpha:
            static_text = "Assign new transparency value to selected items \n" + \
                          "Typical transparency values: 0.5\nRange 0-1"
            ask_kwargs = {'static_text': static_text,
                          'value_text': 0.5,
                          'validator': 'float',
                          'keyword': 'alpha'}

        elif evt.GetId() == ID_textPanel_annotate_mask:
            static_text = 'Assign new mask value to selected items \nTypical mask values: 0.25\nRange 0-1'
            ask_kwargs = {'static_text': static_text,
                          'value_text': 0.25,
                          'validator': 'float',
                          'keyword': 'mask'}

        elif evt.GetId() == ID_textPanel_annotate_min_threshold:
            static_text = 'Assign minimum threshold value to selected items \nTypical mask values: 0.0\nRange 0-1'
            ask_kwargs = {'static_text': static_text,
                          'value_text': 0.0,
                          'validator': 'float',
                          'keyword': 'min_threshold'}

        elif evt.GetId() == ID_textPanel_annotate_max_threshold:
            static_text = 'Assign maximum threshold value to selected items \nTypical mask values: 1.0\nRange 0-1'
            ask_kwargs = {'static_text': static_text,
                          'value_text': 1.0,
                          'validator': 'float',
                          'keyword': 'max_threshold'}

        ask_dialog = panelAsk(self, self.presenter, **ask_kwargs)
        if ask_dialog.ShowModal() != wx.ID_OK:
            return

        return_value = ask_dialog.return_value
        if return_value is None:
            return

        for row in range(rows):
            if self.peaklist.IsChecked(index=row):
                itemInfo = self.OnGetItemInformation(row)
                document = self.data_handling._on_get_document(itemInfo["document"])

                if not ask_kwargs['keyword'] in ['min_threshold', 'max_threshold']:
                    column = self.config.textlistColNames[ask_kwargs['keyword']]
                    self.peaklist.SetItem(row, column, str(return_value))

                # set value in document
                if document.got2DIMS:
                    document.IMS2D[ask_kwargs['keyword']] = return_value
                if document.got2Dprocess:
                    document.IMS2Dprocess[ask_kwargs['keyword']] = return_value

                # update document
                self.presenter.documentsDict[document.title] = document

    def on_enable_disable_tools(self, evt):
        """ Check/uncheck menu item """
        evtID = evt.GetId()

        if evtID == ID_useProcessedCombinedMenu:
            self.config.overlay_usedProcessed = not self.config.overlay_usedProcessed
            msg = "Peak list panel: Using processing data was switched to {}".format(self.config.overlay_usedProcessed)

        elif evtID == ID_textPanel_addToDocument:
            self.addToDocument = not self.addToDocument
            msg = "Adding data to comparison document was set to: {}".format(self.addToDocument)

        if evtID == ID_textPanel_normalize1D:
            self.normalize1D = not self.normalize1D
            msg = "Normalization of mobiligrams/chromatograms was set to: {}".format(self.normalize1D)

        if evtID == ID_textPanel_automaticOverlay:
            self.plotAutomatically = not self.plotAutomatically
            msg = "Automatic 2D overlaying was set to: {}".format(self.plotAutomatically)

            if self.plotAutomatically:
                self.combo.Bind(wx.EVT_COMBOBOX, self.on_overlay_heatmap)
            else:
                self.combo.Unbind(wx.EVT_COMBOBOX)

        self.presenter.onThreading(evt, args=(msg, 4), action='updateStatusbar')
        wx.Bell()

    def on_check_selected(self, evt):
        """
        Check current item when letter S is pressed on the keyboard
        """
        check = not self.peaklist.IsChecked(index=self.peaklist.item_id)
        self.peaklist.CheckItem(self.peaklist.item_id, check=check)

    def on_plot(self, evt, itemID=None):
        """
        This function extracts 2D array and plots it in 2D/3D
        """

        if itemID is not None:
            self.peaklist.item_id = itemID

        itemInfo = self.OnGetItemInformation(self.peaklist.item_id)

        try:
            selectedItem = itemInfo['document']
            currentDocument = self.presenter.documentsDict[selectedItem]

            # get data
            data = currentDocument.IMS2D
        except:
            document_title, ion_title = re.split(': ', itemInfo['document'])
            document = self.presenter.documentsDict[document_title]
            try:
                data = document.IMS2DcompData[ion_title]
            except KeyError:
                try:
                    data = document.IMS2Dions[ion_title]
                except:
                    return

        if evt is not None:
            evtID = evt.GetId()
        else:
            evtID = evt

        if evtID == ID_textPanel_show_mobiligram:
            xvals = data['yvals']  # normally this would be the y-axis
            yvals = data['yvals1D']
            xlabels = data['ylabels']  # normally this would be x-axis label
            self.presenter.view.panelPlots.on_plot_1D(xvals, yvals, xlabels, set_page=True)

        elif evtID == ID_textPanel_show_chromatogram:
            xvals = data['xvals']
            yvals = data['yvalsRT']
            xlabels = data['xlabels']  # normally this would be x-axis label
            self.presenter.view.panelPlots.on_plot_RT(xvals, yvals, xlabels, set_page=True)

        else:
            # Extract 2D data from the document
            zvals, xvals, xlabel, yvals, ylabel, cmap = self.presenter.get2DdataFromDictionary(dictionary=data,
                                                                                               dataType='plot',
                                                                                               compact=False)

            if isempty(xvals) or isempty(yvals) or xvals is "" or yvals is "":
                msg1 = "Missing x- and/or y-axis labels. Cannot continue!"
                msg2 = "Add x- and/or y-axis labels to each file before continuing!"
                msg = '\n'.join([msg1, msg2])
                dlgBox(exceptionTitle='Missing data',
                       exceptionMsg=msg,
                       type="Error")
                return

            # Process data
            # TODO: this function is temporarily disabled! Needs to be fixed before next release
            if evtID == ID_textPanel_show_process_heatmap:
                pass
                # zvals = self.presenter.process2Ddata(zvals=zvals.copy(), return_data=True)

            self.presenter.view.panelPlots.on_plot_2D(
                zvals, xvals, yvals, xlabel, ylabel, cmap, override=True, set_page=True)

    def onOverlayWaterfall(self, evt):
        rows = self.peaklist.GetItemCount()

        # Iterate over row and columns to get data
        xvals, yvals, zvals, colors, labels = [], [], [], [], []
        item_name = "Waterfall overlay:"
        for row in range(rows):
            if not self.peaklist.IsChecked(index=row):
                continue

            itemInfo = self.OnGetItemInformation(row)
            try:
                ion_title = itemInfo['document']
                document = self.presenter.documentsDict[ion_title]

                # get data
                data = document.IMS2D
            except:
                document_title, ion_title = re.split(': ', itemInfo['document'])
                document = self.presenter.documentsDict[document_title]
                try:
                    data = document.IMS2DcompData[ion_title]
                except KeyError:
                    try:
                        data = document.IMS2Dions[ion_title]
                    except:
                        data = None

            if data is None:
                continue

            xvals.append(deepcopy(data['yvals']))
            yvals.append(deepcopy(data['xvals']))
            zvals.append(deepcopy(data['zvals']))
            colors.append(convertRGB255to1(itemInfo['color']))
            labels.append(itemInfo['label'])

            if self.addToDocument:
                if itemInfo['label'] != "":
                    item_label = itemInfo['label']
                else:
                    item_label = ion_title

                if len(xvals) == 1:
                    item_name = "{} {}".format(item_name, item_label)
                else:
                    item_name = "{}, {}".format(item_name, item_label)

        if len(xvals) > 0:
            xlabel = data['xlabels']
            ylabel = data['ylabels']
            self.presenter.view.panelPlots.on_plot_waterfall_overlay(
                xvals, yvals, zvals, colors, xlabel, ylabel, labels)
            self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['Waterfall'])

        # add data to document
        if self.addToDocument:
            _document = self.onGetOverlayDocument()
            checkExist = _document.IMS2DoverlayData.get(item_name, None)
            data = {"xvals": xvals, "yvals": yvals, "zvals": zvals,
                    "colors": colors, "xlabel": xlabel, "ylabel": ylabel,
                    "labels": labels}
            if checkExist is not None:
                # retrieve and merge
                old_data = document.IMS2DoverlayData.get(item_name, {})
                data = merge_two_dicts(old_data, data)
            else:
                data.update(title="", header="", footnote="")

            _document.gotOverlay = True
            _document.IMS2DoverlayData[item_name] = data

            self.presenter.OnUpdateDocument(_document, 'document')

    def onGetOverlayDocument(self):

        if self.presenter.documentsDict[self.presenter.currentDoc].dataType == 'Type: Comparison':
            document = self.presenter.documentsDict[self.presenter.currentDoc]
        else:
            docList = self.presenter.checkIfAnyDocumentsAreOfType(type='Type: Comparison')
            if len(docList) == 0:
                dlg = wx.FileDialog(self.presenter.view, "Please select a name for the comparison document",
                                    "", "", "", wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
                if dlg.ShowModal() == wx.ID_OK:
                    path, idName = split(dlg.GetPath())
                else:
                    return
                # Create document
                document = documents()
                document.title = idName
                document.path = path
                document.userParameters = self.config.userParameters
                document.userParameters['date'] = getTime()
                document.dataType = 'Type: Comparison'
                document.fileFormat = 'Format: ORIGAMI'
            else:
                selectDlg = panelSelectDocument(self.presenter.view, self, docList)
                if selectDlg.ShowModal() == wx.ID_OK:
                    pass

                # Check that document exists
                if self.presenter.currentDoc is None:
                    self.presenter.onThreading(None, ('Please select comparison document', 4),
                                               action='updateStatusbar')
                    return
                document = self.presenter.documentsDict[self.presenter.currentDoc]

        if document.dataType != "Type: Comparison":
            print("This is not a comparison document")
            docList = self.presenter.checkIfAnyDocumentsAreOfType(type='Type: Comparison')
            if len(docList) == 1:
                document = self.presenter.documentsDict[docList[0]]

        args = ("Using document: {}".format(document.title), 4)
        self.presenter.onThreading(None, args, action='updateStatusbar')
        return document

    def onCheckDuplicates(self, fileName):
        currentItems = self.peaklist.GetItemCount() - 1
        while (currentItems >= 0):
            itemInfo = self.OnGetItemInformation(currentItems)
            if itemInfo['document'] == fileName:
                logger.info("File {} already in the table - skipping".format(itemInfo['document']))
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
        tempData = removeListDuplicates(input=tempData,
                                        columnsIn=["check", 'start', 'end', 'charge',
                                                   'color', 'colormap', 'alpha', 'mask',
                                                   'label', 'shape', 'filename', 'check', 'rgb',
                                                   'font_color'],
                                        limitedCols=['filename'])
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

        if evt != None:
            evt.Skip()

    def OnGetItemInformation(self, itemID, return_list=False):

        information = self.peaklist.on_get_item_information(itemID)

        try:
            flag_error = False
            document = self.data_handling._on_get_document(information["document"])
        except KeyError as e:
            logger.error("File: {} is missing. Error: {}".format(information["document"], e))
            flag_error = True
            try:
                document_title, ion_title = re.split(': ', information['document'])
                document = self.presenter.documentsDict[document_title]
            except ValueError:
                return information

        # check whether the ion has any previous information
        min_threshold, max_threshold = 0, 1

        if not flag_error:
            if document.IMS2D:
                min_threshold = document.IMS2D.get('min_threshold', 0)
                max_threshold = document.IMS2D.get('max_threshold', 1)
            else:
                min_threshold = document.IMS2DcompData[ion_title].get('min_threshold', 0)
                max_threshold = document.IMS2DcompData[ion_title].get('max_threshold', 0)

        information['min_threshold'] = min_threshold
        information['max_threshold'] = max_threshold

        return information

    def OnGetValue(self, value_type='color'):
        information = self.OnGetItemInformation(self.peaklist.item_id)

        if value_type == 'minCE':
            return information['minCE']
        elif value_type == 'maxCE':
            return information['maxCE']
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
        elif value_type == 'label':
            return information['label']
        elif value_type == 'shape':
            return information['shape']
        elif value_type == 'document':
            return information['document']

    def OnGetColor(self, evt):
        # Restore custom colors
        custom = wx.ColourData()
        for key in self.config.customColors:
            custom.SetCustomColour(key, self.config.customColors[key])
        dlg = wx.ColourDialog(self, custom)
        dlg.Centre()
        dlg.GetColourData().SetChooseFull(True)

        # Show dialog and get new colour
        if dlg.ShowModal() == wx.ID_OK:
            data = dlg.GetColourData()
            newColour = list(data.GetColour().Get())
            dlg.Destroy()

            # Retrieve custom colors
            for i in range(len(self.config.customColors)):
                self.config.customColors[i] = data.GetCustomColour(i)

            return convertRGB255to1(newColour)

    def on_assign_color(self, evt, itemID=None, give_value=False):
        """
        @param itemID (int): value for item in table
        @param give_value (bool): should/not return color
        """

        if itemID != None:
            self.peaklist.item_id = itemID

        # Restore custom colors
        custom = wx.ColourData()
        for key in self.config.customColors:
            custom.SetCustomColour(key, self.config.customColors[key])
        dlg = wx.ColourDialog(self, custom)
        dlg.Centre()
        dlg.GetColourData().SetChooseFull(True)

        # Show dialog and get new colour
        if dlg.ShowModal() == wx.ID_OK:
            data = dlg.GetColourData()
            newColour = list(data.GetColour().Get())
            dlg.Destroy()
            # Assign color
            self.peaklist.SetItem(self.peaklist.item_id,
                                  self.config.textlistColNames['color'],
                                  str(convertRGB255to1(newColour)))
            self.peaklist.SetItemBackgroundColour(self.peaklist.item_id, newColour)
            self.peaklist.SetItemTextColour(self.peaklist.item_id, determineFontColor(newColour, return_rgb=True))
            # Retrieve custom colors
            for i in range(len(self.config.customColors)):
                self.config.customColors[i] = data.GetCustomColour(i)

            # update document
            self.onUpdateDocument(evt=None)

            if give_value:
                return newColour
        else:
            try:
                newColour = convertRGB1to255(literal_eval(self.OnGetValue(value_type='color')), 3)
            except:
                newColour = self.config.customColors[randomIntegerGenerator(0, 15)]
            # Assign color
            self.peaklist.SetItem(self.peaklist.item_id, self.config.textlistColNames['color'],
                                  str(convertRGB255to1(newColour)))
            self.peaklist.SetItemBackgroundColour(self.peaklist.item_id, newColour)
            self.peaklist.SetItemTextColour(self.peaklist.item_id, determineFontColor(newColour, return_rgb=True))
            if give_value:
                return newColour

    def onUpdateDocument(self, evt, itemInfo=None):

        # get item info
        if itemInfo is None:
            itemInfo = self.OnGetItemInformation(self.peaklist.item_id)

        keywords = ['color', 'colormap', 'alpha', 'mask', 'label', 'min_threshold',
                    'max_threshold', 'charge', 'cmap']

        # get item
        try:
            document = self.presenter.documentsDict[itemInfo['document']]
            for keyword in keywords:
                if keyword == "cmap":
                    keyword_name = "colormap"
                else:
                    keyword_name = keyword
                if document.got2DIMS:
                    document.IMS2D[keyword] = itemInfo[keyword_name]
                if document.got2Dprocess:
                    document.IMS2Dprocess[keyword] = itemInfo[keyword_name]
        except:
            document_title, ion_title = re.split(': ', itemInfo['document'])
            document = self.presenter.documentsDict[document_title]
            for keyword in keywords:
                if keyword == "cmap":
                    keyword_name = "colormap"
                else:
                    keyword_name = keyword
                if ion_title in document.IMS2DcompData:
                    document.IMS2DcompData[ion_title][keyword] = itemInfo[keyword_name]
                else:
                    document.IMS2Dions[ion_title][keyword] = itemInfo[keyword_name]

        # Update file list
        self.presenter.OnUpdateDocument(document, 'no_refresh')

    def OnOpenEditor(self, evt):

        if evt is None:
            evtID = ID_textPanel_editItem
        else:
            evtID = evt.GetId()

        rows = self.peaklist.GetItemCount() - 1
        if evtID == ID_textPanel_editItem:
            if self.peaklist.item_id < 0:
                print('Please select item in the table first.')
                return

            dlg_kwargs = self.OnGetItemInformation(self.peaklist.item_id)

            self.editItemDlg = panelModifyTextSettings(
                self, self.presenter, self.config, **dlg_kwargs)
            self.editItemDlg.Centre()
            self.editItemDlg.Show()
        elif evtID == ID_textPanel_edit_selected:
            while rows >= 0:
                if self.peaklist.IsChecked(rows):
                    information = self.OnGetItemInformation(rows)

                    dlg_kwargs = {'select': self.peaklist.IsChecked(rows),
                                  'color': information['color'],
                                  'title': information['document'],
                                  'min_threshold': information['min_threshold'],
                                  'max_threshold': information['max_threshold'],
                                  'label': information['label'],
                                  'id': rows
                                  }

                    self.editItemDlg = panelModifyTextSettings(self,
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
                              'title': information['document'],
                              'min_threshold': information['min_threshold'],
                              'max_threshold': information['max_threshold'],
                              'label': information['label'],
                              'id': row
                              }

                self.editItemDlg = panelModifyTextSettings(self,
                                                           self.presenter,
                                                           self.config,
                                                           **dlg_kwargs)
                self.editItemDlg.Show()

    def on_remove_deleted_item(self, document):
        """
        document: str
            name of the deleted document
        """
        row = self.peaklist.GetItemCount() - 1

        if isinstance(document, str):
            document = [document]

        document_list = document

        while (row >= 0):
            info = self.OnGetItemInformation(itemID=row)
            for document_title in document_list:
                if info['document'] == document_title or document_title in info["document"]:
                    self.peaklist.DeleteItem(row)
                    del document_list[document_list.index(document_title)]
            row -= 1

    def on_overlay_mobiligram(self, evt):
        self.data_handling.on_overlay_1D(source="text", plot_type="mobiligram")

    def on_overlay_chromatogram(self, evt):
        self.data_handling.on_overlay_1D(source="text", plot_type="chromatogram")

    def on_overlay_heatmap(self, evt):
        self.presenter.on_overlay_2D(source="text")

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
        color = add_dict.get("color", self.config.customColors[randomIntegerGenerator(0, 15)])
        # check for duplicate color
        if check_color:
            color = self.on_check_duplicate_colors(color)

        # add to filelist
        self.peaklist.Append(["",
                              str(add_dict.get("energy_start", "")),
                              str(add_dict.get("energy_end", "")),
                              str(add_dict.get("charge", "")),
                              str(roundRGB(convertRGB255to1(color))),
                              str(add_dict.get("colormap", "")),
                              str(add_dict.get("alpha", "")),
                              str(add_dict.get("mask", "")),
                              str(add_dict.get("label", "")),
                              str(add_dict.get("shape", "")),
                              str(add_dict.get("document", ""))])
        self.peaklist.SetItemBackgroundColour(self.peaklist.GetItemCount() - 1,
                                              color)

        font_color = determineFontColor(color, return_rgb=True)
        self.peaklist.SetItemTextColour(self.peaklist.GetItemCount() - 1,
                                        font_color)

        if return_color:
            return color

    def on_delete_item(self, evt):

        itemInfo = self.OnGetItemInformation(itemID=self.peaklist.item_id)
        msg = "Are you sure you would like to delete {}?\nThis action cannot be undone.".format(
            itemInfo['document'])
        dlg = dlgBox(type="Question",
                     exceptionMsg=msg)
        if dlg == wx.ID_NO:
            print("The operation was cancelled")
            return

        self.view.panelDocuments.documents.on_delete_data__document(
            itemInfo['document'], ask_permission=False)

    def on_delete_selected(self, evt):

        itemID = self.peaklist.GetItemCount() - 1

        while (itemID >= 0):
            if self.peaklist.IsChecked(index=itemID):
                itemInfo = self.OnGetItemInformation(itemID=itemID)
                msg = "Are you sure you would like to delete {}?\nThis action cannot be undone.".format(
                    itemInfo['document'])
                dlg = dlgBox(exceptionMsg=msg, type="Question")
                if dlg == wx.ID_NO:
                    print("The operation was cancelled")
                    continue
                try:
                    self.view.panelDocuments.documents.on_delete_data__document(
                        itemInfo['document'], ask_permission=False)
                # item does not exist
                except KeyError:
                    self.on_remove_deleted_item(itemInfo['document'])

            itemID -= 1

    def on_delete_all(self, evt):

        msg = "Are you sure you would like to delete all [2D IM-MS documents] from the list?\nThis action cannot be undone."
        dlg = dlgBox(exceptionMsg=msg, type="Question")
        if dlg == wx.ID_NO:
            print("The operation was cancelled")
            return

        itemID = self.peaklist.GetItemCount() - 1
        while (itemID >= 0):
            itemInfo = self.OnGetItemInformation(itemID=itemID)
            self.view.panelDocuments.documents.on_delete_data__document(
                itemInfo['document'], ask_permission=False)
            itemID -= 1
