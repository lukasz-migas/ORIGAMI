"""Panel to load and combine multiple ML files"""
# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import logging
from os.path import splitext

import numpy as np
import wx
from gui_elements.dialog_color_picker import DialogColorPicker
from gui_elements.misc_dialogs import DialogBox
from gui_elements.panel_modifyManualFiles import panelModifyManualFiles
from ids import ID_mmlPanel_about_info
from ids import ID_mmlPanel_add_files_toCurrentDoc
from ids import ID_mmlPanel_add_files_toNewDoc
from ids import ID_mmlPanel_add_manualDoc
from ids import ID_mmlPanel_add_menu
from ids import ID_mmlPanel_addToDocument
from ids import ID_mmlPanel_annotateTool
from ids import ID_mmlPanel_assignColor
from ids import ID_mmlPanel_batchRunUniDec
from ids import ID_mmlPanel_changeColorBatch_color
from ids import ID_mmlPanel_changeColorBatch_colormap
from ids import ID_mmlPanel_changeColorBatch_palette
from ids import ID_mmlPanel_check_all
from ids import ID_mmlPanel_check_selected
from ids import ID_mmlPanel_clear_all
from ids import ID_mmlPanel_clear_selected
from ids import ID_mmlPanel_data_combineMS
from ids import ID_mmlPanel_delete_all
from ids import ID_mmlPanel_delete_rightClick
from ids import ID_mmlPanel_delete_selected
from ids import ID_mmlPanel_overlay_menu
from ids import ID_mmlPanel_overlayChargeStates
from ids import ID_mmlPanel_overlayFittedSpectra
from ids import ID_mmlPanel_overlayFoundPeaks
from ids import ID_mmlPanel_overlayMW
from ids import ID_mmlPanel_overlayProcessedSpectra
from ids import ID_mmlPanel_overlayWaterfall
from ids import ID_mmlPanel_plot_combined_MS
from ids import ID_mmlPanel_plot_DT
from ids import ID_mmlPanel_plot_MS
from ids import ID_mmlPanel_preprocess
from ids import ID_mmlPanel_processTool
from ids import ID_mmlPanel_remove_menu
from ids import ID_mmlPanel_showLegend
from ids import ID_mmlPanel_table_document
from ids import ID_mmlPanel_table_filename
from ids import ID_mmlPanel_table_hideAll
from ids import ID_mmlPanel_table_label
from ids import ID_mmlPanel_table_restoreAll
from ids import ID_mmlPanel_table_variable
from processing.spectra import interpolate
from styles import ListCtrl
from styles import makeMenuItem
from styles import makeTooltip
from utils.color import convertRGB1to255
from utils.color import convertRGB255to1
from utils.color import determineFontColor
from utils.color import randomColorGenerator
from utils.random import get_random_int
logger = logging.getLogger('origami')
# TODO: Move opening files to new function and check if files are on a network drive (process locally maybe?)


class panelMML(wx.Panel):

    def __init__(self, parent, config, icons, presenter):
        wx.Panel.__init__(
            self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
            size=wx.Size(300, -1), style=wx.TAB_TRAVERSAL,
        )

        self.view = parent
        self.config = config
        self.presenter = presenter
        self.icons = icons

        self.editingItem = None
        self.allChecked = True
        self.preprocessMS = False
        self.showLegend = True
        self.addToDocument = False
        self.reverse = False
        self.lastColumn = None

        self._filePanel_peaklist = {
            0: {'name': '', 'tag': 'check', 'type': 'bool'},
            1: {'name': 'filename', 'tag': 'filename', 'type': 'str'},
            2: {'name': 'variable', 'tag': 'energy', 'type': 'float'},
            3: {'name': 'document', 'tag': 'document', 'type': 'str'},
            4: {'name': 'label', 'tag': 'label', 'type': 'str'},
            -1: {'name': 'color', 'tag': 'color', 'type': 'color'},
        }

        self.make_gui()

        file_drop_target = DragAndDrop(self)
        self.SetDropTarget(file_drop_target)

        # add a couple of accelerators
        accelerators = [
            (wx.ACCEL_NORMAL, ord('A'), ID_mmlPanel_addToDocument),
            (wx.ACCEL_NORMAL, ord('C'), ID_mmlPanel_assignColor),
            (wx.ACCEL_NORMAL, ord('D'), ID_mmlPanel_plot_DT),
            (wx.ACCEL_NORMAL, ord('M'), ID_mmlPanel_plot_MS),
            (wx.ACCEL_NORMAL, ord('X'), ID_mmlPanel_check_all),
            (wx.ACCEL_NORMAL, ord('S'), ID_mmlPanel_check_selected),
            (wx.ACCEL_NORMAL, wx.WXK_DELETE, ID_mmlPanel_delete_rightClick),
        ]
        self.SetAcceleratorTable(wx.AcceleratorTable(accelerators))

        wx.EVT_MENU(self, ID_mmlPanel_assignColor, self.on_assign_color)
        wx.EVT_MENU(self, ID_mmlPanel_plot_MS, self.on_plot_MS)
        wx.EVT_MENU(self, ID_mmlPanel_plot_DT, self.on_plot_1D)
        wx.EVT_MENU(self, ID_mmlPanel_check_selected, self.on_check_selected)
        wx.EVT_MENU(self, ID_mmlPanel_delete_rightClick, self.on_delete_item)
        wx.EVT_MENU(self, ID_mmlPanel_addToDocument, self.onCheckTool)

    def __del__(self):
        pass

    def _setup_handling_and_processing(self):
        self.data_processing = self.view.data_processing
        self.data_handling = self.view.data_handling

    def make_gui(self):
        """ Make panel GUI """

        self.toolbar = self.make_toolbar()
        self.make_peaklist()
        panelSizer = wx.BoxSizer(wx.VERTICAL)
        panelSizer.Add(self.toolbar, 0, wx.EXPAND, 0)
        panelSizer.Add(self.peaklist, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(panelSizer)
        self.SetSize((300, -1))
        self.Layout()

    def on_check_selected(self, evt):
        check = not self.peaklist.IsChecked(index=self.peaklist.item_id)
        self.on_update_value_in_peaklist(self.peaklist.item_id, 'check', check)

    def on_open_info_panel(self, evt):
        pass

    def make_toolbar(self):

        self.Bind(wx.EVT_BUTTON, self.menu_add_tools, id=ID_mmlPanel_add_menu)
        self.Bind(wx.EVT_BUTTON, self.menu_remove_tools, id=ID_mmlPanel_remove_menu)
        self.Bind(wx.EVT_BUTTON, self.menu_overlay_tools, id=ID_mmlPanel_overlay_menu)
        self.Bind(wx.EVT_BUTTON, self.menu_annotate_tools, id=ID_mmlPanel_annotateTool)
        self.Bind(wx.EVT_BUTTON, self.menu_process_tools, id=ID_mmlPanel_processTool)
        self.Bind(wx.EVT_BUTTON, self.on_open_info_panel, id=ID_mmlPanel_about_info)

        self.add_btn = wx.BitmapButton(
            self, ID_mmlPanel_add_menu, self.icons.iconsLib['add16'],
            size=(18, 18), style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL,
        )
        self.add_btn.SetToolTip(makeTooltip('Add...'))

        self.remove_btn = wx.BitmapButton(
            self, ID_mmlPanel_remove_menu, self.icons.iconsLib['remove16'],
            size=(18, 18), style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL,
        )
        self.remove_btn.SetToolTip(makeTooltip('Remove...'))

        self.annotate_btn = wx.BitmapButton(
            self, ID_mmlPanel_annotateTool, self.icons.iconsLib['annotate16'],
            size=(18, 18), style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL,
        )
        self.annotate_btn.SetToolTip(makeTooltip('Annotate...'))

        self.process_btn = wx.BitmapButton(
            self, ID_mmlPanel_processTool, self.icons.iconsLib['process16'],
            size=(18, 18), style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL,
        )
        self.process_btn.SetToolTip(makeTooltip('Process...'))

        self.overlay_btn = wx.BitmapButton(
            self, ID_mmlPanel_overlay_menu, self.icons.iconsLib['overlay16'],
            size=(18, 18), style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL,
        )
        self.overlay_btn.SetToolTip(makeTooltip('Visualise mass spectra...'))

        vertical_line_1 = wx.StaticLine(self, -1, style=wx.LI_VERTICAL)

        self.info_btn = wx.BitmapButton(
            self, ID_mmlPanel_about_info, self.icons.iconsLib['info16'],
            size=(18, 18), style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL,
        )
        self.info_btn.SetToolTip(makeTooltip('Information...'))

        # button grid
        btn_grid_vert = wx.GridBagSizer(2, 2)
        x = 0
        btn_grid_vert.Add(
            self.add_btn, (x, 0), wx.GBSpan(
                1, 1,
            ), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL,
        )
        btn_grid_vert.Add(
            self.remove_btn, (x, 1), wx.GBSpan(
                1, 1,
            ), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL,
        )
        btn_grid_vert.Add(
            self.annotate_btn, (x, 2), wx.GBSpan(
                1, 1,
            ), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL,
        )
        btn_grid_vert.Add(
            self.process_btn, (x, 3), wx.GBSpan(
                1, 1,
            ), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL,
        )
        btn_grid_vert.Add(
            self.overlay_btn, (x, 4), wx.GBSpan(
                1, 1,
            ), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL,
        )
        btn_grid_vert.Add(vertical_line_1, (x, 5), wx.GBSpan(1, 1), flag=wx.EXPAND)
        btn_grid_vert.Add(
            self.info_btn, (x, 6), wx.GBSpan(
                1, 1,
            ), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL,
        )

        return btn_grid_vert

    def make_peaklist(self):

        # init table
        self.peaklist = ListCtrl(
            self, style=wx.LC_REPORT | wx.LC_VRULES,
            column_info=self._filePanel_peaklist,
        )  # EditableListCtrl(self, style=wx.LC_REPORT | wx.LC_VRULES)
        for item in self.config._multipleFilesSettings:
            order = item['order']
            name = item['name']
            if item['show']:
                width = item['width']
            else:
                width = 0
            self.peaklist.InsertColumn(order, name, width=width, format=wx.LIST_FORMAT_LEFT)

        tooltip_text = \
            """
        List of files and their respective energy values. This panel is relatively universal and can be used for
        aIMMS, CIU, SID or any other activation technique where energy was increased for separate files.
        """

        filelistTooltip = makeTooltip(
            delay=5000, reshow=3000,
            text=tooltip_text,
        )
        self.peaklist.SetToolTip(filelistTooltip)

        self.peaklist.Bind(wx.EVT_LEFT_DCLICK, self.on_double_click_on_item)
        self.peaklist.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.on_right_click_menu)
        self.peaklist.Bind(wx.EVT_LIST_COL_RIGHT_CLICK, self.menu_column_right_click)

    def on_double_click_on_item(self, evt):
        if self.peaklist.item_id != -1:
            self.on_open_editor(evt=None)

    def on_right_click_menu(self, evt):

        self.Bind(wx.EVT_MENU, self.on_plot_MS, id=ID_mmlPanel_plot_MS)
        self.Bind(wx.EVT_MENU, self.on_plot_1D, id=ID_mmlPanel_plot_DT)
        self.Bind(wx.EVT_MENU, self.on_delete_item, id=ID_mmlPanel_delete_rightClick)
        self.Bind(wx.EVT_MENU, self.on_assign_color, id=ID_mmlPanel_assignColor)
        self.Bind(wx.EVT_MENU, self.on_plot_MS, id=ID_mmlPanel_plot_combined_MS)

        # Capture which item was clicked
        self.peaklist.item_id = evt.GetIndex()
        # Create popup menu
        menu = wx.Menu()
        menu.AppendItem(
            makeMenuItem(
                parent=menu, id=ID_mmlPanel_plot_MS,
                text='Show mass spectrum\tM',
                bitmap=self.icons.iconsLib['mass_spectrum_16'],
            ),
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu, id=ID_mmlPanel_plot_DT,
                text='Show mobiligram\tD',
                bitmap=self.icons.iconsLib['mobiligram_16'],
            ),
        )
        menu.Append(ID_mmlPanel_plot_combined_MS, 'Show mass spectrum (average)')
        menu.AppendSeparator()
        menu.AppendItem(
            makeMenuItem(
                parent=menu, id=ID_mmlPanel_assignColor,
                text='Assign new color\tC',
                bitmap=self.icons.iconsLib['color_panel_16'],
            ),
        )
        menu.AppendSeparator()
        menu.AppendItem(
            makeMenuItem(
                parent=menu, id=ID_mmlPanel_delete_rightClick,
                text='Remove item\tDelete',
                bitmap=self.icons.iconsLib['bin16'],
            ),
        )
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def menu_annotate_tools(self, evt):
        self.Bind(wx.EVT_MENU, self.on_change_item_color_batch, id=ID_mmlPanel_changeColorBatch_color)
        self.Bind(wx.EVT_MENU, self.on_change_item_color_batch, id=ID_mmlPanel_changeColorBatch_palette)
        self.Bind(wx.EVT_MENU, self.on_change_item_color_batch, id=ID_mmlPanel_changeColorBatch_colormap)

        menu = wx.Menu()
        menu.AppendItem(
            makeMenuItem(
                parent=menu, id=ID_mmlPanel_changeColorBatch_color,
                text='Assign color for selected items',
                bitmap=self.icons.iconsLib['color_panel_16'],
            ),
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu, id=ID_mmlPanel_changeColorBatch_palette,
                text='Color selected items using color palette',
                bitmap=self.icons.iconsLib['blank_16'],
            ),
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu, id=ID_mmlPanel_changeColorBatch_colormap,
                text='Color selected items using colormap',
                bitmap=self.icons.iconsLib['blank_16'],
            ),
        )
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def menu_add_tools(self, evt):

        self.Bind(wx.EVT_TOOL, self.on_open_multiple_files_add, id=ID_mmlPanel_add_files_toCurrentDoc)
        self.Bind(wx.EVT_TOOL, self.on_open_multiple_files_new, id=ID_mmlPanel_add_files_toNewDoc)
        self.Bind(wx.EVT_TOOL, self.on_add_blank_document_manual, id=ID_mmlPanel_add_manualDoc)

        menu = wx.Menu()
        menu.Append(ID_mmlPanel_add_files_toCurrentDoc, 'Add files to current MANUAL document')
        menu.AppendItem(
            makeMenuItem(
                parent=menu, id=ID_mmlPanel_add_files_toNewDoc,
                text='Add files to blank MANUAL document',
                bitmap=self.icons.iconsLib['new_document_16'],
            ),
        )
        menu.AppendSeparator()
        menu.AppendItem(
            makeMenuItem(
                parent=menu, id=ID_mmlPanel_add_manualDoc,
                text='Create blank MANUAL document',
                bitmap=self.icons.iconsLib['guide_16'],
            ),
        )
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def menu_remove_tools(self, evt):
        # Make bindings
        self.Bind(wx.EVT_MENU, self.peaklist.on_clear_table_all, id=ID_mmlPanel_clear_all)
        self.Bind(wx.EVT_MENU, self.peaklist.on_clear_table_selected, id=ID_mmlPanel_clear_selected)

        self.Bind(wx.EVT_MENU, self.on_delete_all, id=ID_mmlPanel_delete_all)
        self.Bind(wx.EVT_MENU, self.on_delete_selected, id=ID_mmlPanel_delete_selected)

        menu = wx.Menu()
        menu.Append(ID_mmlPanel_clear_selected, 'Clear selected items')
        menu.AppendItem(
            makeMenuItem(
                parent=menu, id=ID_mmlPanel_clear_all,
                text='Clear all items',
                bitmap=self.icons.iconsLib['clear_16'],
            ),
        )
        menu.AppendSeparator()
        menu.Append(ID_mmlPanel_delete_selected, 'Delete selected items')
        menu.Append(ID_mmlPanel_delete_all, 'Delete all items')
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def menu_overlay_tools(self, evt):

        self.Bind(wx.EVT_TOOL, self.onCheckTool, id=ID_mmlPanel_preprocess)
        self.Bind(wx.EVT_TOOL, self.onCheckTool, id=ID_mmlPanel_addToDocument)
        self.Bind(wx.EVT_TOOL, self.onCheckTool, id=ID_mmlPanel_showLegend)
        self.Bind(wx.EVT_TOOL, self.on_overlay_plots, id=ID_mmlPanel_overlayWaterfall)
        self.Bind(wx.EVT_TOOL, self.on_overlay_plots, id=ID_mmlPanel_overlayChargeStates)
        self.Bind(wx.EVT_TOOL, self.on_overlay_plots, id=ID_mmlPanel_overlayMW)
        self.Bind(wx.EVT_TOOL, self.on_overlay_plots, id=ID_mmlPanel_overlayProcessedSpectra)
        self.Bind(wx.EVT_TOOL, self.on_overlay_plots, id=ID_mmlPanel_overlayFittedSpectra)
        self.Bind(wx.EVT_TOOL, self.on_overlay_plots, id=ID_mmlPanel_overlayFoundPeaks)

        menu = wx.Menu()
        self.showLegend_check = menu.AppendCheckItem(
            ID_mmlPanel_showLegend, 'Show legend',
            help='Show legend on overlay plots',
        )
        self.showLegend_check.Check(self.showLegend)
        self.addToDocument_check = menu.AppendCheckItem(
            ID_mmlPanel_addToDocument, 'Add overlay plots to document\tA',
            help='Add overlay results to comparison document',
        )
        self.addToDocument_check.Check(self.addToDocument)
        menu.AppendSeparator()
        self.preProcess_check = menu.AppendCheckItem(
            ID_mmlPanel_preprocess,
            'Pre-process mass spectra',
            help='Pre-process MS before generating waterfall plot (i.e. linearization, normalisation, smoothing, etc',
        )
        self.preProcess_check.Check(self.preprocessMS)
        menu.AppendItem(
            makeMenuItem(
                parent=menu, id=ID_mmlPanel_overlayWaterfall,
                text='Overlay raw mass spectra',
                bitmap=self.icons.iconsLib['panel_waterfall_16'],
            ),
        )
        menu.AppendSeparator()
        menu.AppendItem(
            makeMenuItem(
                parent=menu, id=ID_mmlPanel_overlayProcessedSpectra,
                text='Overlay processed spectra (UniDec)',
                bitmap=self.icons.iconsLib['blank_16'],
            ),
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu, id=ID_mmlPanel_overlayFittedSpectra,
                text='Overlay fitted spectra (UniDec)',
                bitmap=self.icons.iconsLib['blank_16'],
            ),
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu, id=ID_mmlPanel_overlayMW,
                text='Overlay molecular weight distribution (UniDec)',
                bitmap=self.icons.iconsLib['blank_16'],
            ),
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu, id=ID_mmlPanel_overlayChargeStates,
                text='Overlay charge state distribution (UniDec)',
                bitmap=self.icons.iconsLib['blank_16'],
            ),
        )
#         menu.AppendItem(makeMenuItem(parent=menu, id=ID_mmlPanel_overlayFoundPeaks,
#                                      text='Overlay isolated species',
#                                      bitmap=self.icons.iconsLib['blank_16']))

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def menu_process_tools(self, evt):
        self.Bind(wx.EVT_TOOL, self.data_handling.on_combine_mass_spectra, id=ID_mmlPanel_data_combineMS)
        self.Bind(wx.EVT_TOOL, self.onAutoUniDec, id=ID_mmlPanel_batchRunUniDec)

        menu = wx.Menu()
        menu.Append(ID_mmlPanel_data_combineMS, 'Average mass spectra (current document)')
        menu.AppendItem(
            makeMenuItem(
                parent=menu, id=ID_mmlPanel_batchRunUniDec,
                text='Run UniDec for selected items',
                bitmap=self.icons.iconsLib['process_unidec_16'],
            ),
        )
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def menu_column_right_click(self, evt):
        self.Bind(wx.EVT_MENU, self.on_update_peaklist_table, id=ID_mmlPanel_table_filename)
        self.Bind(wx.EVT_MENU, self.on_update_peaklist_table, id=ID_mmlPanel_table_variable)
        self.Bind(wx.EVT_MENU, self.on_update_peaklist_table, id=ID_mmlPanel_table_document)
        self.Bind(wx.EVT_MENU, self.on_update_peaklist_table, id=ID_mmlPanel_table_label)
        self.Bind(wx.EVT_MENU, self.on_update_peaklist_table, id=ID_mmlPanel_table_hideAll)
        self.Bind(wx.EVT_MENU, self.on_update_peaklist_table, id=ID_mmlPanel_table_restoreAll)

        menu = wx.Menu()
        n = 0
        self.table_filename = menu.AppendCheckItem(ID_mmlPanel_table_filename, 'Table: Filename')
        self.table_filename.Check(self.config._multipleFilesSettings[n]['show'])
        n = n + 1
        self.table_variable = menu.AppendCheckItem(ID_mmlPanel_table_variable, 'Table: Variable')
        self.table_variable.Check(self.config._multipleFilesSettings[n]['show'])
        n = n + 1
        self.table_document = menu.AppendCheckItem(ID_mmlPanel_table_document, 'Table: Document')
        self.table_document.Check(self.config._multipleFilesSettings[n]['show'])
        n = n + 1
        self.table_label = menu.AppendCheckItem(ID_mmlPanel_table_label, 'Table: Label')
        self.table_label.Check(self.config._multipleFilesSettings[n]['show'])
        menu.AppendSeparator()
        self.table_hide = menu.AppendItem(
            makeMenuItem(
                parent=menu, id=ID_mmlPanel_table_hideAll,
                text='Table: Hide all',
                bitmap=self.icons.iconsLib['hide_table_16'],
            ),
        )
        self.table_restore = menu.AppendItem(
            makeMenuItem(
                parent=menu, id=ID_mmlPanel_table_restoreAll,
                text='Table: Restore all',
                bitmap=self.icons.iconsLib['show_table_16'],
            ),
        )

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def onCheckTool(self, evt):
        evtID = evt.GetId()

        if evtID == ID_mmlPanel_preprocess:
            self.preprocessMS = self.preProcess_check.IsChecked()
            self.preProcess_check.Check(self.preprocessMS)
        elif evtID == ID_mmlPanel_showLegend:
            self.showLegend = self.showLegend_check.IsChecked()
            self.showLegend_check.Check(self.showLegend)
        elif evtID == ID_mmlPanel_addToDocument:
            self.addToDocument = self.addToDocument_check.IsChecked()
            self.addToDocument_check.Check(self.addToDocument)

    def _updateTable(self):
        self.onUpdateDocument(itemID=self.editingItem)

    def on_change_item_color_batch(self, evt):
        # get number of checked items
        check_count = 0
        for row in range(self.peaklist.GetItemCount()):
            if self.peaklist.IsChecked(index=row):
                check_count += 1

        if evt.GetId() == ID_mmlPanel_changeColorBatch_palette:
            colors = self.presenter.view.panelPlots.on_change_color_palette(
                None, n_colors=check_count, return_colors=True,
            )
        elif evt.GetId() == ID_mmlPanel_changeColorBatch_color:
            color = self.OnGetColor(None)
            colors = [color] * check_count
        else:
            colors = self.presenter.view.panelPlots.on_get_colors_from_colormap(n_colors=check_count)

        for row in range(self.peaklist.GetItemCount()):
            if self.peaklist.IsChecked(index=row):
                color = colors[row]
                self.peaklist.SetItemBackgroundColour(row, convertRGB1to255(color))
                self.peaklist.SetItemTextColour(
                    row, determineFontColor(
                        convertRGB1to255(color),
                        return_rgb=True,
                    ),
                )

    def onAutoUniDec(self, evt):

        for row in range(self.peaklist.GetItemCount()):
            if not self.peaklist.IsChecked(index=row):
                continue
            itemInfo = self.OnGetItemInformation(itemID=row)

            # get mass spectrum information
            document = self.presenter.documentsDict[itemInfo['document']]
            dataset = itemInfo['filename']
            self.data_processing.on_run_unidec(dataset, task='auto_unidec')

            print(
                'Pre-processing mass spectra using m/z range {} - {} with {} bin size'.format(
                    self.config.unidec_mzStart,
                    self.config.unidec_mzEnd,
                    self.config.unidec_mzBinSize,
                ),
            )

    def onRenameItem(self, old_name, new_name, item_type='Document'):
        for row in range(self.peaklist.GetItemCount()):
            itemInfo = self.OnGetItemInformation(itemID=row)
            if item_type == 'document':
                if itemInfo['document'] == old_name:
                    self.peaklist.SetStringItem(
                        index=row,
                        col=self.config.multipleMLColNames['document'],
                        label=new_name,
                    )
            elif item_type == 'filename':
                if itemInfo['filename'] == old_name:
                    self.peaklist.SetStringItem(
                        index=row,
                        col=self.config.multipleMLColNames['filename'],
                        label=new_name,
                    )

    def on_update_peaklist_table(self, evt):
        evtID = evt.GetId()

        # check which event was triggered
        if evtID == ID_mmlPanel_table_filename:
            col_index = self.config.multipleMLColNames['filename']
        elif evtID == ID_mmlPanel_table_variable:
            col_index = self.config.multipleMLColNames['energy']
        elif evtID == ID_mmlPanel_table_document:
            col_index = self.config.multipleMLColNames['document']
        elif evtID == ID_mmlPanel_table_label:
            col_index = self.config.multipleMLColNames['label']
        elif evtID == ID_mmlPanel_table_restoreAll:
            for i in range(len(self.config._multipleFilesSettings)):
                self.config._multipleFilesSettings[i]['show'] = True
                col_width = self.config._multipleFilesSettings[i]['width']
                self.peaklist.SetColumnWidth(i, col_width)
            return
        elif evtID == ID_mmlPanel_table_hideAll:
            for i in range(len(self.config._multipleFilesSettings)):
                self.config._multipleFilesSettings[i]['show'] = False
                col_width = 0
                self.peaklist.SetColumnWidth(i, col_width)
            return

        # check values
        col_check = not self.config._multipleFilesSettings[col_index]['show']
        self.config._multipleFilesSettings[col_index]['show'] = col_check
        if col_check:
            col_width = self.config._multipleFilesSettings[col_index]['width']
        else:
            col_width = 0
        # set new column width
        self.peaklist.SetColumnWidth(col_index, col_width)

    def onOpenFile_DnD(self, pathlist):
        self.data_handling.on_open_multiple_ML_files_fcn(
            open_type='multiple_files_add', pathlist=pathlist,
        )

    def on_plot_MS(self, evt):
        """
        Function to plot selected MS in the mainWindow
        """

        itemInfo = self.OnGetItemInformation(itemID=self.peaklist.item_id)
        document = self.presenter.documentsDict[itemInfo['document']]
        if document is None:
            return

        if evt.GetId() == ID_mmlPanel_plot_MS:
            itemName = itemInfo['filename']
            try:
                msX = document.multipleMassSpectrum[itemName]['xvals']
                msY = document.multipleMassSpectrum[itemName]['yvals']
            except KeyError:
                return
            parameters = document.multipleMassSpectrum[itemName].get(
                'parameters', {
                    'startMS': np.min(msX),
                    'endMS': np.max(msX),
                },
            )
            xlimits = [parameters['startMS'], parameters['endMS']]
            name_kwargs = {'document': itemInfo['document'], 'dataset': itemName}

        elif evt.GetId() == ID_mmlPanel_plot_combined_MS:
            try:
                msX = document.massSpectrum['xvals']
                msY = document.massSpectrum['yvals']
                xlimits = document.massSpectrum['xlimits']
                name_kwargs = {'document': itemInfo['document'], 'dataset': 'Mass Spectrum'}
            except KeyError:
                DialogBox(
                    exceptionTitle='Error',
                    exceptionMsg='Document does not have averaged mass spectrum',
                    type='Error',
                )
                return

        # Plot data
        self.presenter.view.panelPlots.on_plot_MS(
            msX, msY, xlimits=xlimits, full_repaint=True,
            set_page=True, **name_kwargs
        )

    def on_plot_1D(self, evt):
        """
        Function to plot selected 1DT in the mainWindow
        """
        itemInfo = self.OnGetItemInformation(itemID=self.peaklist.item_id)
        document = self.presenter.documentsDict[itemInfo['document']]

        if document is None:
            return
        try:
            itemName = itemInfo['filename']
            dtX = document.multipleMassSpectrum[itemName]['ims1DX']
            dtY = document.multipleMassSpectrum[itemName]['ims1D']
            xlabel = document.multipleMassSpectrum[itemName]['xlabel']

            self.presenter.view.panelPlots.on_plot_1D(dtX, dtY, xlabel, full_repaint=True, set_page=True)
        except KeyError:
            DialogBox(
                exceptionTitle='Error',
                exceptionMsg='No mobility data present for selected item',
                type='Error',
            )
            return

    def OnGetItemInformation(self, itemID, return_list=False):
        information = self.peaklist.on_get_item_information(itemID)
        return information

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

    def onUpdateDocument(self, itemInfo=None, itemID=None):
        """
        evt : wxPython event
            unused
        itemInfo : dictionary
            dictionary with information about item to annotate
        itemID : int
            number of the item to be annotated
        """

        # get item info
        if itemInfo is None:
            if itemID is None:
                itemInfo = self.OnGetItemInformation(self.peaklist.item_id)
            else:
                itemInfo = self.OnGetItemInformation(itemID)

        # get item
        document = self.data_handling._on_get_document(itemInfo['document'])

        keywords = ['color', 'energy', 'label']
        for keyword in keywords:
            keyword_name = self.__check_keyword(keyword)
            document.multipleMassSpectrum[itemInfo['filename']][keyword_name] = itemInfo[keyword]

        self.data_handling.on_update_document(document, 'no_refresh')

    def on_overlay_plots(self, evt):
        evtID = evt.GetId()

        _interpolate = True
        show_legend = self.showLegend_check.IsChecked()
        names, colors, xvals_list, yvals_list = [], [], [], []
        for row in range(self.peaklist.GetItemCount()):
            if not self.peaklist.IsChecked(index=row):
                continue
            itemInfo = self.OnGetItemInformation(itemID=row)
            names.append(itemInfo['label'])
            # get mass spectrum information
            document = self.presenter.documentsDict[itemInfo['document']]
            data = document.multipleMassSpectrum[itemInfo['filename']]

            # check if unidec dataset is present
            if 'unidec' not in data and evtID in [
                ID_mmlPanel_overlayMW,
                ID_mmlPanel_overlayProcessedSpectra,
                ID_mmlPanel_overlayFittedSpectra,
                ID_mmlPanel_overlayChargeStates,
                ID_mmlPanel_overlayFoundPeaks,
            ]:
                print(
                    'Selected item {} ({}) does not have UniDec results'.format(
                        itemInfo['document'],
                        itemInfo['filename'],
                    ),
                )
                continue
            if evtID == ID_mmlPanel_overlayWaterfall:
                _interpolate = False
                xvals = document.multipleMassSpectrum[itemInfo['filename']]['xvals'].copy()
                yvals = document.multipleMassSpectrum[itemInfo['filename']]['yvals'].copy()
                if self.preprocessMS:
                    xvals, yvals = self.data_processing.on_process_MS(msX=xvals, msY=yvals, return_data=True)

            elif evtID == ID_mmlPanel_overlayMW:
                xvals = data['unidec']['MW distribution']['xvals']
                yvals = data['unidec']['MW distribution']['yvals']

            elif evtID == ID_mmlPanel_overlayProcessedSpectra:
                xvals = data['unidec']['Processed']['xvals']
                yvals = data['unidec']['Processed']['yvals']
            elif evtID == ID_mmlPanel_overlayFittedSpectra:
                xvals = data['unidec']['Fitted']['xvals'][0]
                yvals = data['unidec']['Fitted']['yvals'][1]
            elif evtID == ID_mmlPanel_overlayChargeStates:
                xvals = data['unidec']['Charge information'][:, 0]
                yvals = data['unidec']['Charge information'][:, 1]
            elif evtID == ID_mmlPanel_overlayFoundPeaks:
                data['unidec']['m/z with isolated species']
                xvals = []
                yvals = []

            xvals_list.append(xvals)
            yvals_list.append(yvals)
            colors.append(convertRGB255to1(itemInfo['color']))

        if len(xvals_list) == 0:
            print('No data in selected items')
            return

        # check that lengths are correct
        if _interpolate:
            x_long = max(xvals_list, key=len)
            for i, xlist in enumerate(xvals_list):
                if len(xlist) < len(x_long):
                    xlist_new, ylist_new = interpolate(
                        xvals_list[i],
                        yvals_list[i],
                        x_long,
                    )
                    xvals_list[i] = xlist_new
                    yvals_list[i] = ylist_new

        # sum mw
        if evtID == ID_mmlPanel_overlayMW:
            xvals_list.insert(0, np.average(xvals_list, axis=0))
            yvals_list.insert(0, np.average(yvals_list, axis=0))
            colors.insert(0, ((0, 0, 0)))
            names.insert(0, ('Average'))

        kwargs = {'show_y_labels': True, 'labels': names, 'add_legend': show_legend}
        if evtID == ID_mmlPanel_overlayWaterfall:
            overlay_type = 'Waterfall (Raw)'
            xlabel, ylabel = 'm/z', 'Offset Intensity'
            self.presenter.view.panelPlots.on_plot_waterfall(
                xvals_list, yvals_list, None, colors=colors,
                xlabel=xlabel, ylabel=ylabel, **kwargs
            )
        if evtID == ID_mmlPanel_overlayMW:
            overlay_type = 'Waterfall (Deconvoluted MW)'
            xlabel, ylabel = 'Mass (Da)', 'Offset Intensity'
            self.presenter.view.panelPlots.on_plot_waterfall(
                xvals_list, yvals_list, None, colors=colors,
                xlabel=xlabel, ylabel=ylabel, set_page=True,
                **kwargs
            )

        elif evtID == ID_mmlPanel_overlayProcessedSpectra:
            overlay_type = 'Waterfall (Processed)'
            xlabel, ylabel = 'm/z', 'Offset Intensity'
            self.presenter.view.panelPlots.on_plot_waterfall(
                xvals_list, yvals_list, None, colors=colors,
                xlabel=xlabel, ylabel=ylabel, set_page=True,
                **kwargs
            )
        elif evtID == ID_mmlPanel_overlayFittedSpectra:
            overlay_type = 'Waterfall (Fitted)'
            xlabel, ylabel = 'm/z', 'Offset Intensity'
            self.presenter.view.panelPlots.on_plot_waterfall(
                xvals_list, yvals_list, None, colors=colors,
                xlabel=xlabel, ylabel=ylabel, set_page=True,
                **kwargs
            )
        elif evtID == ID_mmlPanel_overlayChargeStates:
            overlay_type = 'Waterfall (Charge states)'
            xlabel, ylabel = 'Charge', 'Intensity'
            kwargs = {'show_y_labels': True, 'labels': names, 'increment': 0.000001, 'add_legend': show_legend}
            self.presenter.view.panelPlots.on_plot_waterfall(
                xvals_list, yvals_list, None, colors=colors,
                xlabel=xlabel, ylabel=ylabel, set_page=True,
                **kwargs
            )

        if self.addToDocument:
            self.on_add_overlay_data_to_document(xvals_list, yvals_list, colors, xlabel, ylabel, overlay_type, **kwargs)

    def on_add_overlay_data_to_document(
        self, xvals, yvals, colors, xlabel, ylabel,
        overlay_type, **kwargs
    ):
        overlay_labels = ', '.join(kwargs['labels'])
        overlay_title = '{}: {}'.format(overlay_type, overlay_labels)

        document = self.presenter.get_overlay_document()
        if document is None:
            self.presenter.onThreading(None, ('No document was selected', 4), action='updateStatusbar')
            return
        document.gotOverlay = True
        document.IMS2DoverlayData[overlay_title] = {
            'xvals': xvals, 'yvals': yvals,
            'xlabel': xlabel, 'ylabel': ylabel,
            'colors': colors, 'labels': kwargs['labels'],
            'waterfall_kwargs': kwargs,
        }

        # update document
        self.data_handling.on_update_document(
            document, expand_item='overlay',
            expand_item_title=overlay_title,
        )

    def on_add_blank_document_manual(self, evt):
        self.presenter.onAddBlankDocument(evt=None, document_type='manual')

    def on_check_duplicate_colors(self, new_color, document_name):
        """
        Check whether newly assigned color is already in the table and if so,
        return a different one
        """
        count = self.peaklist.GetItemCount()
        color_list = []
        for row in range(count):
            itemInfo = self.OnGetItemInformation(itemID=row)
            if itemInfo['document'] == document_name:
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

    def on_open_multiple_files_new(self, evt):
        self.data_handling.on_open_multiple_ML_files_fcn(
            open_type='multiple_files_new_document',
        )

    def on_open_multiple_files_add(self, evt):
        self.data_handling.on_open_multiple_ML_files_fcn(
            open_type='multiple_files_add',
        )

    def on_combine_mass_spectra(self, evt, document_name=None):
        self.data_handling.on_combine_mass_spectra(document_name=document_name)

    def on_add_to_table(self, add_dict, check_color=True):

        # check if item already exists
        if self._check_item_in_table(add_dict):
            logger.info(
                'Item {}:{} is already present in the document'.format(
                    add_dict['document'], add_dict['filename'],
                ),
            )
            return

        # get color
        color = add_dict.get('color', self.config.customColors[get_random_int(0, 15)])
        color = convertRGB1to255(color)

        document_title = add_dict.get('document', None)
        # check for duplicate color
        if check_color:
            color = self.on_check_duplicate_colors(color, document_title)

        # add to peaklist
        self.peaklist.Append([
            '',
            str(add_dict.get('filename', '')),
            str(add_dict.get('variable', '')),
            str(add_dict.get('document', '')),
            str(add_dict.get('label', '')),
        ])
        self.peaklist.SetItemBackgroundColour(self.peaklist.GetItemCount() - 1, color)
        self.peaklist.SetItemTextColour(
            self.peaklist.GetItemCount() - 1,
            determineFontColor(color, return_rgb=True),
        )

    def _check_item_in_table(self, add_dict):
        count = self.peaklist.GetItemCount()
        for row in range(count):
            item_info = self.OnGetItemInformation(itemID=row)
            if add_dict['filename'] == item_info['filename'] and \
                    add_dict['document'] == item_info['document']:
                return True

        return False

    def delete_row_from_table(self, delete_item_name=None, delete_document_title=None):

        rows = self.peaklist.GetItemCount() - 1
        while rows >= 0:
            itemInfo = self.OnGetItemInformation(rows)

            if itemInfo['filename'] == delete_item_name and itemInfo['document'] == delete_document_title:
                self.peaklist.DeleteItem(rows)
                rows = 0
                return
            elif delete_item_name is None and itemInfo['document'] == delete_document_title:
                self.peaklist.DeleteItem(rows)
            rows -= 1

    def on_delete_item(self, evt):

        itemInfo = self.OnGetItemInformation(itemID=self.peaklist.item_id)
        dlg = DialogBox(
            type='Question',
            exceptionMsg='Are you sure you would like to delete {} from {}?\nThis action cannot be undone.'.format(
                itemInfo['filename'],
                itemInfo['document'],
            ),
        )
        if dlg == wx.ID_NO:
            print('The operation was cancelled')
            return

        document = self.data_handling._on_get_document(itemInfo['document'])

        __, __ = self.view.panelDocuments.documents.on_delete_data__mass_spectra(
            document, itemInfo['document'], delete_type='spectrum.one',
            spectrum_name=itemInfo['filename'],
        )

    def on_delete_selected(self, evt):

        itemID = self.peaklist.GetItemCount() - 1
        while (itemID >= 0):
            if self.peaklist.IsChecked(index=itemID):
                itemInfo = self.OnGetItemInformation(itemID=itemID)
                msg = 'Are you sure you would like to delete {} from {}?\nThis action cannot be undone.'.format(
                    itemInfo['filename'], itemInfo['document'],
                )
                dlg = DialogBox(exceptionMsg=msg, type='Question')
                if dlg == wx.ID_NO:
                    print('The operation was cancelled')
                    continue

                document = self.data_handling._on_get_document(itemInfo['document'])
                __, __ = self.view.panelDocuments.documents.on_delete_data__mass_spectra(
                    document, itemInfo['document'], delete_type='spectrum.one',
                    spectrum_name=itemInfo['filename'],
                )
            itemID -= 1

    def on_delete_all(self, evt):

        msg = 'Are you sure you would like to delete all classifiers from all documents?\nThis action cannot be undone.'
        dlg = DialogBox(exceptionMsg=msg, type='Question')
        if dlg == wx.ID_NO:
            print('The operation was cancelled')
            return

        item_count = self.peaklist.GetItemCount() - 1
        while (item_count >= 0):
            itemInfo = self.OnGetItemInformation(itemID=item_count)
            document = self.data_handling._on_get_document(itemInfo['document'])
            __, __ = self.view.panelDocuments.documents.on_delete_data__mass_spectra(
                document, itemInfo['document'], delete_type='spectrum.one',
                spectrum_name=itemInfo['filename'],
            )
            item_count -= 1

    def on_remove_deleted_item(self, document):
        row = self.peaklist.GetItemCount() - 1
        while (row >= 0):
            info = self.OnGetItemInformation(itemID=row)
            if info['document'] == document:
                self.peaklist.DeleteItem(row)
                row -= 1
            else:
                row -= 1

    def on_open_editor(self, evt):
        information = self.OnGetItemInformation(self.peaklist.item_id)

        dlg = panelModifyManualFiles(
            self,
            self.presenter,
            self.config,
            **information
        )
        dlg.Show()

    def on_update_value_in_peaklist(self, item_id, value_type, value):

        if value_type == 'check':
            self.peaklist.CheckItem(item_id, value)
        elif value_type == 'filename':
            self.peaklist.SetStringItem(item_id, self.config.multipleMLColNames['filename'], str(value))
        elif value_type == 'energy':
            self.peaklist.SetStringItem(item_id, self.config.multipleMLColNames['energy'], str(value))
        elif value_type == 'color':
            color_255, color_1, font_color = value
            self.peaklist.SetItemBackgroundColour(item_id, color_255)
            self.peaklist.SetItemTextColour(item_id, font_color)
        elif value_type == 'color_text':
            self.peaklist.SetItemBackgroundColour(item_id, value)
            self.peaklist.SetItemTextColour(item_id, determineFontColor(value, return_rgb=True))
        elif value_type == 'label':
            self.peaklist.SetStringItem(item_id, self.config.multipleMLColNames['label'], str(value))
        elif value_type == 'document':
            self.peaklist.SetStringItem(item_id, self.config.multipleMLColNames['filename'], str(value))

    def on_assign_color(self, evt, itemID=None, return_value=False):
        """
        @param itemID (int): value for item in table
        @param return_value (bool): should/not return color
        """
        if itemID is not None:
            self.peaklist.item_id = itemID

        if itemID is None:
            itemID = self.peaklist.item_id

        dlg = DialogColorPicker(self, self.config.customColors)
        if dlg.ShowModal() == 'ok':
            color_255, color_1, font_color = dlg.GetChosenColour()
            self.config.customColors = dlg.GetCustomColours()
            self.on_update_value_in_peaklist(itemID, 'color', [color_255, color_1, font_color])

            if return_value:
                return color_255

    @staticmethod
    def __check_keyword(keyword_name):
        if keyword_name == 'energy':
            keyword_name = 'trap'
        return keyword_name


class DragAndDrop(wx.FileDropTarget):

    # ----------------------------------------------------------------------
    def __init__(self, window):
        """Constructor"""
        wx.FileDropTarget.__init__(self)
        self.window = window

    # ----------------------------------------------------------------------

    def OnDropFiles(self, x, y, filenames):
        """
        When files are dropped, write where they were dropped and then
        the file paths themselves
        """
        pathlist = []
        for filename in filenames:

            __, file_extension = splitext(filename)
            if file_extension in ['.raw']:
                print('Added {} file to the list'.format(filename))
                pathlist.append(filename)
            else:
                print('Dropped file {} is not supported'.format(filename))

        if len(pathlist) > 0:
            self.window.onOpenFile_DnD(pathlist)
