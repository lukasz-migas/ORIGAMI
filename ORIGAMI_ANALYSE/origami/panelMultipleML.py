# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
#    Copyright (C) 2017-2018 Lukasz G. Migas 
#    <lukasz.migas@manchester.ac.uk> OR <lukas.migas@yahoo.com>
# 
#	 GitHub : https://github.com/lukasz-migas/ORIGAMI
#	 University of Manchester IP : https://www.click2go.umip.com/i/s_w/ORIGAMI.html
#	 Cite : 10.1016/j.ijms.2017.08.014
#
#    This program is free software. Feel free to redistribute it and/or 
#    modify it under the condition you cite and credit the authors whenever 
#    appropriate. 
#    The program is distributed in the hope that it will be useful but is 
#    provided WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE
# -------------------------------------------------------------------------
# __author__ lukasz.g.migas

import wx, time
import wx.lib.mixins.listctrl as listmix
import numpy as np
from os.path import splitext
from operator import itemgetter
from natsort import natsorted

from styles import makeTooltip, makeMenuItem
from ids import *
import dialogs as dialogs
from toolbox import (str2num, str2int, removeListDuplicates, convertRGB255to1, 
                             convertRGB1to255, isempty, mlen, determineFontColor,
                             randomColorGenerator, roundRGB)
from processing.spectra import interpolate



# TODO: Move opening files to new function and check if files are on a network drive (process locally maybe?)

"""
Panel to load and combine multiple ML files
"""

class panelMML( wx.Panel ):
    
    def __init__( self, parent, config, icons,  presenter ):
        wx.Panel.__init__ ( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, 
                            size = wx.Size( 300,-1 ), style = wx.TAB_TRAVERSAL )

        self.view = parent
        self.config = config
        self.presenter = presenter
        self.icons = icons
        
        self.currentItem = None
        self.editingItem = None
        self.allChecked = True
        self.preprocessMS = False
        self.showLegend = True
        self.addToDocument = False
        
        self.makeGUI()
        
        self.reverse = False
        self.lastColumn = None
        
        self.data_processing = self.view.data_processing
        
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
         
        wx.EVT_MENU(self, ID_mmlPanel_assignColor, self.OnAssignColor)
        wx.EVT_MENU(self, ID_mmlPanel_plot_MS, self.on_plot_MS)
        wx.EVT_MENU(self, ID_mmlPanel_plot_DT, self.on_plot_1D)
        wx.EVT_MENU(self, ID_mmlPanel_check_all, self.OnCheckAllItems)
        wx.EVT_MENU(self, ID_mmlPanel_check_selected, self.on_check_selected)
        wx.EVT_MENU(self, ID_mmlPanel_delete_rightClick, self.OnDeleteAll)
        wx.EVT_MENU(self, ID_mmlPanel_addToDocument, self.onCheckTool)
        
    def makeGUI(self):
        """ Make panel GUI """
        
        self.makeToolbar()
        self.makeListCtrl()
        panelSizer = wx.BoxSizer( wx.VERTICAL )
        panelSizer.Add(self.toolbar, 0, wx.EXPAND, 0)
        panelSizer.Add(self.filelist, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(panelSizer)
        self.SetSize((300, -1))
        self.Layout()
        
    def __del__( self ):
         pass
        
    def on_check_selected(self, evt):
        check = not self.filelist.IsChecked(index=self.currentItem)
        self.filelist.CheckItem(self.currentItem, check)
        
    def makeListCtrl(self):
        
        # init table
        self.filelist = EditableListCtrl(self, style=wx.LC_REPORT|wx.LC_VRULES)
        for item in self.config._multipleFilesSettings:
            order = item['order']
            name = item['name']
            if item['show']: 
                width = item['width']
            else: 
                width = 0
            self.filelist.InsertColumn(order, name, width=width, format=wx.LIST_FORMAT_LEFT)

        filelistTooltip = makeTooltip(delay=3000, reshow=3000, 
                                      text="""List of files and their respective energy values. This panel is relatively universal and can be used for aIMMS, CIU, SID or any other activation technique where energy was increased for separate files.""")
        self.filelist.SetToolTip(filelistTooltip)
        
        self.Bind(wx.EVT_LIST_COL_CLICK, self.OnGetColumnClick)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnRightClickMenu)
        self.Bind(wx.EVT_LIST_BEGIN_LABEL_EDIT, self.onStartEditingItem)
        self.Bind(wx.EVT_LIST_END_LABEL_EDIT, self.onFinishEditingItem)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onItemSelected)
        self.filelist.Bind(wx.EVT_LIST_COL_RIGHT_CLICK, self.onColumnRightClickMenu)

    def onItemSelected(self, evt):
        self.currentItem = evt.m_itemIndex
    
    def onStartEditingItem(self, evt):
        self.editingItem = evt.m_itemIndex
        
        # unbind shortcuts
        self.SetAcceleratorTable(wx.AcceleratorTable([]))
        
    def _updateTable(self):
        self.onUpdateDocument(None, itemID=self.editingItem)
        
    def onFinishEditingItem(self, evt):
        # bind events
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
         
        wx.EVT_MENU(self, ID_mmlPanel_assignColor, self.OnAssignColor)
        wx.EVT_MENU(self, ID_mmlPanel_plot_MS, self.on_plot_MS)
        wx.EVT_MENU(self, ID_mmlPanel_plot_DT, self.on_plot_1D)
        wx.EVT_MENU(self, ID_mmlPanel_check_all, self.OnCheckAllItems)
        wx.EVT_MENU(self, ID_mmlPanel_check_selected, self.on_check_selected)
        wx.EVT_MENU(self, ID_mmlPanel_delete_rightClick, self.OnDeleteAll)
        wx.EVT_MENU(self, ID_mmlPanel_addToDocument, self.onCheckTool)
        
        wx.CallAfter(self._updateTable)

    def makeToolbar(self):
        
        self.Bind(wx.EVT_TOOL, self.onAddTool, id=ID_addFilesMenu)
        self.Bind(wx.EVT_TOOL, self.onRemoveTool, id=ID_removeFilesMenu)
        self.Bind(wx.EVT_TOOL, self.OnCheckAllItems, id=ID_mmlPanel_check_all)
        self.Bind(wx.EVT_TOOL, self.onOverlayTool, id=ID_overlayFilesMenu)
        self.Bind(wx.EVT_TOOL, self.onAnnotateTool, id=ID_mmlPanel_annotateTool)
        self.Bind(wx.EVT_TOOL, self.onProcessTool, id=ID_mmlPanel_processTool)
        
        self.toolbar = wx.ToolBar(self, style=wx.TB_HORIZONTAL | wx.TB_DOCKABLE, id = wx.ID_ANY) 
        self.toolbar.SetToolBitmapSize((16, 16)) 
        self.toolbar.AddTool(ID_mmlPanel_check_all, self.icons.iconsLib['check16'] , 
                              shortHelpString="Check all items")
        self.toolbar.AddTool(ID_addFilesMenu, self.icons.iconsLib['add16'],
                             shortHelpString="Add files...") 
        self.toolbar.AddTool(ID_removeFilesMenu, self.icons.iconsLib['remove16'], 
                             shortHelpString="Remove...")
        self.toolbar.AddTool(ID_mmlPanel_annotateTool, self.icons.iconsLib['annotate16'],
                             shortHelpString="Annotate...")
        self.toolbar.AddTool(ID_mmlPanel_processTool, self.icons.iconsLib['process16'],
                             shortHelpString="Process...")
        self.toolbar.AddTool(ID_overlayFilesMenu, self.icons.iconsLib['overlay16'],
                             shortHelpString="Visualise mass spectra...")
        self.toolbar.AddSeparator()
        self.toolbar.Realize()   
            
    def onAnnotateTool(self, evt):
        self.Bind(wx.EVT_MENU, self.onChangeColorBatch, id=ID_mmlPanel_changeColorBatch_color)
        self.Bind(wx.EVT_MENU, self.onChangeColorBatch, id=ID_mmlPanel_changeColorBatch_palette)
        self.Bind(wx.EVT_MENU, self.onChangeColorBatch, id=ID_mmlPanel_changeColorBatch_colormap)
        
        menu = wx.Menu()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_mmlPanel_changeColorBatch_color,
                                     text='Assign color for selected items', 
                                     bitmap=self.icons.iconsLib['color_panel_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_mmlPanel_changeColorBatch_palette,
                                     text='Color selected items using color palette', 
                                     bitmap=self.icons.iconsLib['blank_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_mmlPanel_changeColorBatch_colormap,
                                     text='Color selected items using colormap', 
                                     bitmap=self.icons.iconsLib['blank_16']))
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()
            
    def onAddTool(self, evt):
        
        self.Bind(wx.EVT_TOOL, self.on_open_multiple_files_add, id=ID_mmlPanel_add_files_toCurrentDoc)
        self.Bind(wx.EVT_TOOL, self.on_open_multiple_files, id=ID_mmlPanel_add_files_toNewDoc)
        self.Bind(wx.EVT_TOOL, self.on_add_blank_document_manual, id=ID_mmlPanel_add_manualDoc)
        
        menu = wx.Menu()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_mmlPanel_add_files_toNewDoc,
                                     text='Add files to blank MANUAL document', 
                                     bitmap=self.icons.iconsLib['new_document_16']))
        menu.Append(ID_mmlPanel_add_files_toCurrentDoc, "Add files to current MANUAL document")
        menu.AppendSeparator()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_mmlPanel_add_manualDoc,
                                     text='Create blank MANUAL document', 
                                     bitmap=self.icons.iconsLib['guide_16']))
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()        
          
    def onRemoveTool(self, evt):
        # Make bindings
        self.Bind(wx.EVT_MENU, self.OnDeleteAll, id=ID_mmlPanel_delete_selected)
        self.Bind(wx.EVT_MENU, self.OnDeleteAll, id=ID_mmlPanel_delete_all)
        self.Bind(wx.EVT_MENU, self.OnClearTable, id=ID_mmlPanel_clear_all) 
        self.Bind(wx.EVT_MENU, self.OnClearTable, id=ID_mmlPanel_clear_selected)
        
        menu = wx.Menu()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_mmlPanel_clear_all,
                                     text='Clear table', 
                                     bitmap=self.icons.iconsLib['clear_16']))
        menu.Append(ID_mmlPanel_clear_selected, "Clear selected")
        menu.AppendSeparator()
        menu.Append(ID_mmlPanel_delete_selected, "Remove selected file")
        menu.Append(ID_mmlPanel_delete_all, "Remove all files")
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def onOverlayTool(self, evt):
        
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
        self.showLegend_check = menu.AppendCheckItem(ID_mmlPanel_showLegend, "Show legend",
                                                     help="Show legend on overlay plots")
        self.showLegend_check.Check(self.showLegend)
        self.addToDocument_check = menu.AppendCheckItem(ID_mmlPanel_addToDocument, "Add overlay plots to document\tA",
                                                        help="Add overlay results to comparison document")
        self.addToDocument_check.Check(self.addToDocument)
        menu.AppendSeparator()
        self.preProcess_check = menu.AppendCheckItem(ID_mmlPanel_preprocess, "Pre-process mass spectra",
                                                     help="Pre-process MS before generating waterfall plot (i.e. linearization, normalisation, smoothing, etc")
        self.preProcess_check.Check(self.preprocessMS)
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_mmlPanel_overlayWaterfall,
                                     text='Overlay raw mass spectra', 
                                     bitmap=self.icons.iconsLib['panel_waterfall_16']))
        menu.AppendSeparator()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_mmlPanel_overlayProcessedSpectra,
                                     text='Overlay processed spectra (UniDec)', 
                                     bitmap=self.icons.iconsLib['blank_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_mmlPanel_overlayFittedSpectra,
                                     text='Overlay fitted spectra (UniDec)', 
                                     bitmap=self.icons.iconsLib['blank_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_mmlPanel_overlayMW,
                                     text='Overlay molecular weight distribution (UniDec)',
                                     bitmap=self.icons.iconsLib['blank_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_mmlPanel_overlayChargeStates,
                                     text='Overlay charge state distribution (UniDec)', 
                                     bitmap=self.icons.iconsLib['blank_16']))
#         menu.AppendItem(makeMenuItem(parent=menu, id=ID_mmlPanel_overlayFoundPeaks,
#                                      text='Overlay isolated species', 
#                                      bitmap=self.icons.iconsLib['blank_16']))
        
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()
        
    def onProcessTool(self, evt):
        self.Bind(wx.EVT_TOOL, self.on_combine_mass_spectra, id=ID_mmlPanel_data_combineMS)
        self.Bind(wx.EVT_TOOL, self.onAutoUniDec, id=ID_mmlPanel_batchRunUniDec)
        
        menu = wx.Menu()
        menu.Append(ID_mmlPanel_data_combineMS, "Average mass spectra (current document)")
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_mmlPanel_batchRunUniDec,
                                     text='Run UniDec for selected items', 
                                     bitmap=self.icons.iconsLib['process_unidec_16']))
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
        
    def OnRightClickMenu(self, evt):
        
        self.Bind(wx.EVT_MENU, self.on_plot_MS, id=ID_mmlPanel_plot_MS)
        self.Bind(wx.EVT_MENU, self.on_plot_1D, id=ID_mmlPanel_plot_DT)
        self.Bind(wx.EVT_MENU, self.OnDeleteAll, id=ID_mmlPanel_delete_rightClick)
        self.Bind(wx.EVT_MENU, self.OnAssignColor, id=ID_mmlPanel_assignColor)
        self.Bind(wx.EVT_MENU, self.on_plot_MS, id=ID_mmlPanel_plot_combined_MS)
        
        
        # Capture which item was clicked
        self.currentItem, __ = self.filelist.HitTest(evt.GetPosition())
        # Create popup menu
        menu = wx.Menu()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_mmlPanel_plot_MS,
                                     text='Show mass spectrum\tM', 
                                     bitmap=self.icons.iconsLib['mass_spectrum_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_mmlPanel_plot_DT,
                                     text='Show mobiligram\tD', 
                                     bitmap=self.icons.iconsLib['mobiligram_16']))
        menu.Append(ID_mmlPanel_plot_combined_MS, "Show mass spectrum (average)")
        menu.AppendSeparator()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_mmlPanel_assignColor,
                                     text='Assign new color\tC', 
                                     bitmap=self.icons.iconsLib['color_panel_16']))
        menu.AppendSeparator()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_mmlPanel_delete_rightClick,
                                     text='Remove item\tDelete', 
                                     bitmap=self.icons.iconsLib['bin16']))
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()
        
    def onChangeColorBatch(self, evt):
        # get number of checked items
        check_count = 0
        for row in range(self.filelist.GetItemCount()):
            if self.filelist.IsChecked(index=row):
                check_count += 1 
                
        if evt.GetId() == ID_mmlPanel_changeColorBatch_palette:
            colors = self.presenter.view.panelPlots.onChangePalette(None, n_colors=check_count, return_colors=True)
        elif evt.GetId() == ID_mmlPanel_changeColorBatch_color:
            color = self.OnGetColor(None)
            colors = [color] * check_count
        else:
            colors = self.presenter.view.panelPlots.onGetColormapList(n_colors=check_count)
            
        for row in range(self.filelist.GetItemCount()):
            if self.filelist.IsChecked(index=row):
                color = colors[row]
                self.filelist.SetItemBackgroundColour(row, convertRGB1to255(color))
                self.filelist.SetItemTextColour(row, determineFontColor(convertRGB1to255(color), 
                                                                        return_rgb=True))
          
    # ----
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
            for i in xrange(len(self.config.customColors)): 
                self.config.customColors[i] = data.GetCustomColour(i)
                
            return convertRGB255to1(newColour)
          
    def onAutoUniDec(self, evt):
        
        for row in range(self.filelist.GetItemCount()):
            if not self.filelist.IsChecked(index=row): 
                continue
            itemInfo = self.OnGetItemInformation(itemID=row)
            
            # get mass spectrum information
            document = self.presenter.documentsDict[itemInfo["document"]]
            dataset = itemInfo["filename"]           
            self.data_processing.on_run_unidec(dataset, task="auto_unidec")
             
            print("Pre-processing mass spectra using m/z range {} - {} with {} bin size".format(self.config.unidec_mzStart,
                                                                                                self.config.unidec_mzEnd,
                                                                                                self.config.unidec_mzBinSize))

    def onRenameItem(self, old_name, new_name, item_type="Document"):
        for row in range(self.filelist.GetItemCount()):
            itemInfo = self.OnGetItemInformation(itemID=row)
            if item_type == "document":
                if itemInfo['document'] == old_name:
                    self.filelist.SetStringItem(index=row,
                                                col=self.config.multipleMLColNames['document'],
                                                label=new_name)
            elif item_type == "filename":
                if itemInfo['filename'] == old_name:
                    self.filelist.SetStringItem(index=row,
                                                col=self.config.multipleMLColNames['filename'],
                                                label=new_name)
       
    def onColumnRightClickMenu(self, evt):
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_mmlPanel_table_filename)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_mmlPanel_table_variable)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_mmlPanel_table_document)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_mmlPanel_table_label)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_mmlPanel_table_hideAll)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_mmlPanel_table_restoreAll)
        

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
        self.table_hide = menu.AppendItem(makeMenuItem(parent=menu, id=ID_mmlPanel_table_hideAll,
                                     text='Table: Hide all', 
                                     bitmap=self.icons.iconsLib['hide_table_16']))
        self.table_restore = menu.AppendItem(makeMenuItem(parent=menu, id=ID_mmlPanel_table_restoreAll,
                                     text='Table: Restore all', 
                                     bitmap=self.icons.iconsLib['show_table_16']))
        
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()
        
    def onUpdateTable(self, evt):
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
                self.filelist.SetColumnWidth(i, col_width)
            return
        elif evtID == ID_mmlPanel_table_hideAll:
            for i in range(len(self.config._multipleFilesSettings)):
                self.config._multipleFilesSettings[i]['show'] = False
                col_width = 0
                self.filelist.SetColumnWidth(i, col_width)
            return 
        
        # check values
        col_check = not self.config._multipleFilesSettings[col_index]['show']
        self.config._multipleFilesSettings[col_index]['show'] = col_check
        if col_check: col_width = self.config._multipleFilesSettings[col_index]['width']
        else: col_width = 0
        # set new column width
        self.filelist.SetColumnWidth(col_index, col_width)

    def onOpenFile_DnD(self, pathlist):
        self.presenter.on_open_multiple_ML_files(open_type="multiple_files_add", 
                                                 pathlist=pathlist)

    def on_plot_MS(self, evt):
        """
        Function to plot selected MS in the mainWindow
        """
        
        itemInfo = self.OnGetItemInformation(itemID=self.currentItem)
        document = self.presenter.documentsDict[itemInfo['document']]
        if document == None: 
            return
        
        if evt.GetId() == ID_mmlPanel_plot_MS:
            itemName = itemInfo['filename']
            try:
                msX = document.multipleMassSpectrum[itemName]['xvals']
                msY = document.multipleMassSpectrum[itemName]['yvals']
            except KeyError: 
                return
            parameters = document.multipleMassSpectrum[itemName].get('parameters', {'startMS':np.min(msX), 
                                                                                    'endMS':np.max(msX)})
            xlimits = [parameters['startMS'],parameters['endMS']]
            name_kwargs = {"document":itemInfo['document'], "dataset": itemName}
            
        elif evt.GetId() == ID_mmlPanel_plot_combined_MS:
            try:
                msX = document.massSpectrum['xvals']
                msY = document.massSpectrum['yvals']
                xlimits = document.massSpectrum['xlimits']
                name_kwargs = {"document":itemInfo['document'], "dataset": "Mass Spectrum"}
            except KeyError:
                dialogs.dlgBox(exceptionTitle="Error",
                               exceptionMsg="Document does not have averaged mass spectrum", 
                               type="Error")
                return
        
        # Plot data
        self.presenter.view.panelPlots.on_plot_MS(msX, msY, xlimits=xlimits, full_repaint=True, 
                                                  set_page=True, **name_kwargs)
        
    def on_plot_1D(self, evt):
        """
        Function to plot selected 1DT in the mainWindow
        """
        itemInfo = self.OnGetItemInformation(itemID=self.currentItem)
        document = self.presenter.documentsDict[itemInfo['document']]
        
        if document == None: return
        try:
            itemName = itemInfo['filename']
            dtX = document.multipleMassSpectrum[itemName]['ims1DX']
            dtY = document.multipleMassSpectrum[itemName]['ims1D']
            xlabel = document.multipleMassSpectrum[itemName]['xlabel']
            
            self.presenter.view.panelPlots.on_plot_1D(dtX, dtY, xlabel, full_repaint=True, set_page=True)
        except KeyError: 
            dialogs.dlgBox(exceptionTitle="Error",
                           exceptionMsg="No mobility data present for selected item", 
                           type="Error")
            return
            
    def OnGetColumnClick(self, evt):
        self.OnSortByColumn(column=evt.GetColumn())
            
    def OnCheckAllItems(self, evt, check=True, override=False):
        """
        Check/uncheck all items in the list
        ===
        Parameters:
        check : boolean, sets items to specified state
        override : boolean, skips settings self.allChecked value
        """
        rows = self.filelist.GetItemCount()
        
        if not override: 
            if self.allChecked:
                self.allChecked = False
                check = True
            else:
                self.allChecked = True
                check = False 
            
        if rows > 0:
            for row in range(rows):
                self.filelist.CheckItem(row, check=check)
             
    def OnSortByColumn(self, column, overrideReverse=False):
        """
        Sort data in filelist based on pressed column
        """
        
        # Override reverse
        if overrideReverse:
            self.reverse = True
        
        # Check if it should be reversed
        if self.lastColumn == None:
            self.lastColumn = column
        elif self.lastColumn == column:
            if self.reverse == True:
                self.reverse = False
            else:
                self.reverse = True
        else:
            self.reverse = False
            self.lastColumn = column
        
        columns = self.filelist.GetColumnCount()
        rows = self.filelist.GetItemCount()
        tempData = []
        # Iterate over row and columns to get data
        for row in range(rows):
            tempRow = []
            for col in range(columns):
                item = self.filelist.GetItem(itemId=row, col=col)
                tempRow.append(item.GetText())
            tempRow.append(self.filelist.IsChecked(index=row))
            tempRow.append(self.filelist.GetItemBackgroundColour(row))
            tempRow.append(self.filelist.GetItemTextColour(row))
            tempData.append(tempRow)

        # Sort data (always by document + another variable
        tempData = natsorted(tempData, key=itemgetter(2, column), reverse=self.reverse)  
        
        # Clear table
        self.filelist.DeleteAllItems()
        
        checkData, bg_rgb, fg_rgb = [], [], []
        for check in tempData:
            fg_rgb.append(check[-1])
            del check[-1]
            bg_rgb.append(check[-1])
            del check[-1]
            checkData.append(check[-1])
            del check[-1]
            
        # Reinstate data
        rowList = np.arange(len(tempData))
        for row, check, bg_rgb, fg_color in zip(rowList, checkData, bg_rgb, fg_rgb):
            self.filelist.Append(tempData[row])
            self.filelist.CheckItem(row, check)
            self.filelist.SetItemBackgroundColour(row, bg_rgb)
            self.filelist.SetItemTextColour(row, fg_color)
        
        # Now insert it into the document
        for row in range(rows):
            itemName = self.filelist.GetItem(itemId=row, 
                                             col=self.config.multipleMLColNames['filename']).GetText()
            docName = self.filelist.GetItem(itemId=row, 
                                            col=self.config.multipleMLColNames['document']).GetText()
            trapCV = str2num(self.filelist.GetItem(itemId=row, 
                                                   col=self.config.multipleMLColNames['energy']).GetText())
            
            self.presenter.documentsDict[docName].multipleMassSpectrum[itemName]['trap'] = trapCV

    def OnDeleteAll(self, evt, ticked=False, selected=False, itemID=None):
        """ 
        This function removes selected or all MassLynx files from the 
        combined document
        """
        
        try:
            itemInfo = self.OnGetItemInformation(self.currentItem)
            currentDoc = itemInfo['document']
        except TypeError:
            pass
        currentItems = self.filelist.GetItemCount()-1
        if evt.GetId() == ID_mmlPanel_delete_selected:
            while (currentItems >= 0):
                itemInfo = self.OnGetItemInformation(itemID=currentItems)
                item = self.filelist.IsChecked(index=currentItems)
                if item == True:
                    msg = "Deleted {} from {}".format(itemInfo['filename'], itemInfo['document'])
                    self.presenter.onThreading(evt, (msg, 4, 3), action='updateStatusbar')
                    try: 
                        del self.presenter.documentsDict[itemInfo['document']].multipleMassSpectrum[itemInfo['filename']]
                        if len(self.presenter.documentsDict[itemInfo['document']].multipleMassSpectrum.keys()) == 0: 
                            self.presenter.documentsDict[itemInfo['document']].gotMultipleMS = False
                    except KeyError: pass
                    self.filelist.DeleteItem(currentItems)
                currentItems-=1
            try: self.presenter.view.panelDocuments.topP.documents.addDocument(docData = self.presenter.documentsDict[itemInfo['document']])
            except KeyError: pass
              
        elif evt.GetId() == ID_mmlPanel_delete_rightClick:
            itemInfo = self.OnGetItemInformation(itemID=self.currentItem)
            msg = "Deleted {} from {}".format(itemInfo['filename'], itemInfo['document'])
            self.presenter.onThreading(evt, (msg, 4, 3), action='updateStatusbar')
            try: 
                del self.presenter.documentsDict[itemInfo['document']].multipleMassSpectrum[itemInfo['filename']]
                if len(self.presenter.documentsDict[itemInfo['document']].multipleMassSpectrum.keys()) == 0: 
                    self.presenter.documentsDict[itemInfo['document']].gotMultipleMS = False
            except KeyError: pass
            self.filelist.DeleteItem(self.currentItem)
            try: self.presenter.view.panelDocuments.topP.documents.addDocument(docData = self.presenter.documentsDict[itemInfo['document']])
            except KeyError: pass  
            # Combine mass spectra 
            self.on_combine_mass_spectra(None, document_name=itemInfo['document'])
            
        else:
            # Ask if you want to delete all items
            dlg = dialogs.dlgBox(exceptionTitle='Are you sure?', 
                                 exceptionMsg= "Are you sure you would like to delete ALL MassLynx files from the document?",
                                 type="Question")
            if dlg == wx.ID_NO:
                msg = 'Cancelled deletion operation'
                self.presenter.view.SetStatusText(msg, 3)
                return
            # Iterate over all items
            while (currentItems >= 0):
                itemInfo = self.OnGetItemInformation(currentItems)
                msg = "Deleted {} from {}".format(itemInfo['filename'], itemInfo['document'])
                self.presenter.onThreading(evt, (msg, 4, 3), action='updateStatusbar')
                try: 
                    del self.presenter.documentsDict[itemInfo['document']].multipleMassSpectrum[itemInfo['filename']]
                    if len(self.presenter.documentsDict[itemInfo['document']].multipleMassSpectrum.keys()) == 0: 
                        self.presenter.documentsDict[itemInfo['document']].gotMultipleMS = False
                except KeyError: pass
                self.filelist.DeleteItem(currentItems)
                currentItems-=1
            # Update tree with new document
            try: self.presenter.view.panelDocuments.topP.documents.addDocument(docData = self.presenter.documentsDict[itemInfo['document']])
            except KeyError: pass  

    def OnClearTable(self, evt):
        """
        This function clears the table without deleting any items from the document tree
        """
        # Ask if you want to delete all items
        evtID = evt.GetId()
        
        if evtID == ID_mmlPanel_clear_selected:
            row = self.filelist.GetItemCount() - 1
            while (row >= 0):
                if self.filelist.IsChecked(index=row):
                    self.filelist.DeleteItem(row)
                row-=1
        else:
            dlg = dialogs.dlgBox(exceptionTitle='Are you sure?', 
                                 exceptionMsg= "Are you sure you would like to clear the table?",
                                 type="Question")
            if dlg == wx.ID_NO:
                msg = 'Cancelled clearing operation'
                self.presenter.view.SetStatusText(msg, 3)
                return
            self.filelist.DeleteAllItems()
        
    def onRemoveDuplicates(self, evt, limitCols=False):
        """
        This function removes duplicates from the list
        Its not very efficient!
        """
        
        columns = self.filelist.GetColumnCount()
        rows = self.filelist.GetItemCount()

        tempData = []
        # Iterate over row and columns to get data
        for row in range(rows):
            tempRow = []
            for col in range(columns):
                item = self.filelist.GetItem(itemId=row, col=col)
                
                #  We want to make sure certain columns are numbers
                if col in [self.config.multipleMLColNames['energy']]:
                    itemData = str2num(item.GetText())
                    if itemData == None: itemData = 0
                    tempRow.append(itemData)
                else:
                    tempRow.append(item.GetText())
            tempRow.append(self.filelist.IsChecked(index=row))
            tempRow.append(self.filelist.GetItemBackgroundColour(row))
            tempRow.append(self.filelist.GetItemTextColour(row))
            tempData.append(tempRow)
        
        # Remove duplicates
        tempData = removeListDuplicates(input=tempData,
                                        columnsIn=['filename', 'energy', 'document', 'label', 'check', 'rgb', 'rgb_fg'],
                                        limitedCols=['filename', 'document'])     
        rows = len(tempData)
        # Clear table
        self.filelist.DeleteAllItems()
        
        checkData, bg_rgb, fg_rgb = [], [], []
        for check in tempData:
            fg_rgb.append(check[-1])
            del check[-1]
            bg_rgb.append(check[-1])
            del check[-1]
            checkData.append(check[-1])
            del check[-1]
            
        # Reinstate data
        rowList = np.arange(len(tempData))
        for row, check, bg_rgb, fg_color in zip(rowList, checkData, bg_rgb, fg_rgb):
            self.filelist.Append(tempData[row])
            self.filelist.CheckItem(row, check)
            self.filelist.SetItemBackgroundColour(row, bg_rgb)
            self.filelist.SetItemTextColour(row, fg_color)
            
        if evt is None: return
        else:
            evt.Skip()
           
    def OnGetItemInformation(self, itemID, return_list=False):
        # get item information
        information = {'filename':self.filelist.GetItem(itemID, self.config.multipleMLColNames['filename']).GetText(),
                       'energy':str2num(self.filelist.GetItem(itemID, self.config.multipleMLColNames['energy']).GetText()),
                       'document':self.filelist.GetItem(itemID, self.config.multipleMLColNames['document']).GetText(),
                       'label':self.filelist.GetItem(itemID, self.config.multipleMLColNames['label']).GetText(),
                       'color':self.filelist.GetItemBackgroundColour(item=itemID),
                       }
           
        if return_list:
            filename = information['filename']
            energy = information['energy']
            document = information['document']
            label = information['label']
            color = information['color']
            return filename, energy, document, label, color
            
        return information
    
    def onClearItems(self, document):
        """
        @param document: title of the document to be removed from the list
        """
        row = self.filelist.GetItemCount() - 1
        while (row >= 0):
            info = self.OnGetItemInformation(itemID=row)
            if info['document'] == document:
                self.filelist.DeleteItem(row)
                row-=1
            else:
                row-=1
        
    def OnAssignColor(self, evt):
        """
        @param itemID (int): value for item in table
        @param give_value (bool): should/not return color
        """ 
            
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
            self.filelist.SetItemBackgroundColour(self.currentItem, newColour)
            self.filelist.SetItemTextColour(self.currentItem, determineFontColor(newColour, return_rgb=True))
            # Retrieve custom colors
            for i in xrange(15): 
                self.config.customColors[i] = data.GetCustomColour(i)
            
            # update document
            self.onUpdateDocument(evt=None)

    def onUpdateDocument(self, evt, itemInfo=None, itemID=None):
        """
        evt : wxPython event
            unused
        itemInfo : dictionary
            dictionary with information about item to annotate
        itemID : int
            number of the item to be annotated
        """
        
        # get item info
        if itemInfo == None:
            if itemID == None:
                itemInfo = self.OnGetItemInformation(self.currentItem)
            else:
                itemInfo = self.OnGetItemInformation(itemID)
        
        # get item
        document = self.presenter.documentsDict[itemInfo['document']]
        
        keywords = ['color', 'energy', 'label']
        for keyword in keywords:
            if keyword == 'energy': keyword_name = 'trap'
            else: keyword_name = keyword
            document.multipleMassSpectrum[itemInfo['filename']][keyword_name] = itemInfo[keyword] 
        
        # Update file list
        self.presenter.OnUpdateDocument(document, expand_item='mass_spectra',
                                        expand_item_title=itemInfo['filename'])

    def on_overlay_plots(self, evt):
        evtID = evt.GetId()
        
        _interpolate = True
        show_legend = self.showLegend_check.IsChecked()
        names, colors, xvals_list, yvals_list = [], [], [], []
        for row in range(self.filelist.GetItemCount()):
            if not self.filelist.IsChecked(index=row): continue
            itemInfo = self.OnGetItemInformation(itemID=row)
            names.append(itemInfo['label'])
            # get mass spectrum information
            document = self.presenter.documentsDict[itemInfo["document"]]
            data = document.multipleMassSpectrum[itemInfo["filename"]]
            
            # check if unidec dataset is present
            if 'unidec' not in data and evtID in [ID_mmlPanel_overlayMW,
                                                  ID_mmlPanel_overlayProcessedSpectra,
                                                  ID_mmlPanel_overlayFittedSpectra,
                                                  ID_mmlPanel_overlayChargeStates,
                                                  ID_mmlPanel_overlayFoundPeaks]:
                print("Selected item {} ({}) does not have UniDec results".format(itemInfo['document'],
                                                                                   itemInfo['filename']))
                continue
            if evtID == ID_mmlPanel_overlayWaterfall:
                _interpolate = False
                xvals = document.multipleMassSpectrum[itemInfo["filename"]]['xvals'].copy()
                yvals = document.multipleMassSpectrum[itemInfo["filename"]]['yvals'].copy()
                if self.preprocessMS:
                    xvals, yvals = self.presenter.processMSdata(msX=xvals, 
                                                                msY=yvals, 
                                                                return_data=True)
                    
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
                xvals = data['unidec']['Charge information'][:,0]
                yvals = data['unidec']['Charge information'][:,1]
            elif evtID == ID_mmlPanel_overlayFoundPeaks:
                data['unidec']['m/z with isolated species']
                xvals = []
                yvals = []
                
          
            xvals_list.append(xvals)
            yvals_list.append(yvals)
            colors.append(convertRGB255to1(itemInfo['color']))
        
        if len(xvals_list) == 0:
            print("No data in selected items")
            return
        
        # check that lengths are correct
        if _interpolate:
            x_long = max(xvals_list,key=len)
            for i, xlist in enumerate(xvals_list):
                if len(xlist) < len(x_long):
                    xlist_new, ylist_new = interpolate(xvals_list[i],
                                                       yvals_list[i],
                                                       x_long)
                    xvals_list[i] = xlist_new
                    yvals_list[i] = ylist_new
        
        # sum mw 
        if evtID == ID_mmlPanel_overlayMW:
            xvals_list.insert(0, np.average(xvals_list, axis=0))
            yvals_list.insert(0, np.average(yvals_list, axis=0))
            colors.insert(0, ((0, 0, 0)))
            names.insert(0, ("Average"))
            
        kwargs = {'show_y_labels':True, 'labels':names, 'add_legend':show_legend}
        if evtID == ID_mmlPanel_overlayWaterfall:
            overlay_type = "Waterfall (Raw)"
            xlabel, ylabel = "m/z", "Offset Intensity"
            self.presenter.view.panelPlots.on_plot_waterfall(xvals_list, yvals_list, None, colors=colors, 
                                                             xlabel=xlabel, ylabel=ylabel, **kwargs)
        if evtID == ID_mmlPanel_overlayMW:
            overlay_type = "Waterfall (Deconvoluted MW)"
            xlabel, ylabel = "Mass (Da)", "Offset Intensity"
            self.presenter.view.panelPlots.on_plot_waterfall(xvals_list, yvals_list, None, colors=colors, 
                                                             xlabel=xlabel, ylabel=ylabel, set_page=True,
                                                             **kwargs)
            
        elif evtID == ID_mmlPanel_overlayProcessedSpectra:
            overlay_type = "Waterfall (Processed)"
            xlabel, ylabel = "m/z", "Offset Intensity"
            self.presenter.view.panelPlots.on_plot_waterfall(xvals_list, yvals_list, None, colors=colors, 
                                                             xlabel=xlabel, ylabel=ylabel, set_page=True,
                                                             **kwargs)
        elif evtID == ID_mmlPanel_overlayFittedSpectra:
            overlay_type = "Waterfall (Fitted)"
            xlabel, ylabel = "m/z", "Offset Intensity"
            self.presenter.view.panelPlots.on_plot_waterfall(xvals_list, yvals_list, None, colors=colors, 
                                                             xlabel=xlabel, ylabel=ylabel, set_page=True,
                                                             **kwargs)
        elif evtID == ID_mmlPanel_overlayChargeStates:
            overlay_type = "Waterfall (Charge states)"
            xlabel, ylabel = "Charge", "Intensity"
            kwargs = {'show_y_labels':True, 'labels':names, 'increment':0.000001, 'add_legend':show_legend}
            self.presenter.view.panelPlots.on_plot_waterfall(xvals_list, yvals_list, None, colors=colors, 
                                                             xlabel=xlabel, ylabel=ylabel, set_page=True,
                                                             **kwargs)
            
        if self.addToDocument:
            self.on_add_overlay_data_to_document(xvals_list, yvals_list, colors, xlabel, ylabel, overlay_type, **kwargs)
            
    def on_add_overlay_data_to_document(self, xvals, yvals, colors, xlabel, ylabel, 
                                        overlay_type, **kwargs):
        overlay_labels = ", ".join(kwargs['labels'])
        overlay_title = "{}: {}".format(overlay_type, overlay_labels)
        
        document = self.presenter.get_overlay_document()
        if document is None: 
            self.presenter.onThreading(None, ("No document was selected", 4), action='updateStatusbar')
            return
        document.gotOverlay = True
        document.IMS2DoverlayData[overlay_title] = {'xvals':xvals, 'yvals':yvals,
                                                    'xlabel':xlabel, 'ylabel':ylabel,
                                                    'colors':colors, 'labels':kwargs['labels'],
                                                    'waterfall_kwargs':kwargs}
        
        # update document
        self.presenter.OnUpdateDocument(document, expand_item='overlay',
                                        expand_item_title=overlay_title)

    def on_add_blank_document_manual(self, evt):
        self.presenter.onAddBlankDocument(evt=None, document_type='manual')
    
    def on_check_duplicate_colors(self, new_color, document_name):
        """ 
        Check whether newly assigned color is already in the table and if so, 
        return a different one
        """
        count = self.filelist.GetItemCount()
        color_list = []
        for row in xrange(count):
            itemInfo = self.OnGetItemInformation(itemID=row)
            if itemInfo['document'] == document_name:
                color_list.append(self.filelist.GetItemBackgroundColour(item=row))
        
        if new_color in color_list:
            counter = len(self.config.customColors)-1
            while counter > 0:
                config_color = self.config.customColors[counter]
                if config_color not in color_list:
                    return config_color
                
                counter -= 1
            return randomColorGenerator(True)
        return new_color
        
    def on_open_multiple_files(self, evt):
        self.presenter.on_open_multiple_ML_files(open_type="multiple_files_new_document")
        
    def on_open_multiple_files_add(self, evt):
        self.presenter.on_open_multiple_ML_files(open_type="multiple_files_add")
    
    def on_combine_mass_spectra(self, evt, document_name=None):
        self.presenter.on_combine_mass_spectra(document_name=document_name)
        
class DragAndDrop(wx.FileDropTarget):
    
    #----------------------------------------------------------------------
    def __init__(self, window):
        """Constructor"""
        wx.FileDropTarget.__init__(self)
        self.window = window

    #----------------------------------------------------------------------
    
    def OnDropFiles(self, x, y, filenames):
        """
        When files are dropped, write where they were dropped and then
        the file paths themselves
        """
        pathlist = []
        for filename in filenames:
            
            __, file_extension = splitext(filename)
            if file_extension in ['.raw']:
                print("Added {} file to the list".format(filename))
                pathlist.append(filename)
            else:
                print("Dropped file {} is not supported".format(filename))
                
        if len(pathlist) > 0:
            self.window.onOpenFile_DnD(pathlist)
                      
class EditableListCtrl(wx.ListCtrl, listmix.TextEditMixin, listmix.CheckListCtrlMixin,
                       listmix.ColumnSorterMixin):
    """
    Editable list
    """
    def __init__(self, parent, ID=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0): 
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.TextEditMixin.__init__(self)
        listmix.CheckListCtrlMixin.__init__(self)

        self.Bind(wx.EVT_LIST_BEGIN_LABEL_EDIT, self.OnBeginLabelEdit)

    def OnBeginLabelEdit(self, event):
        # Block any attempts to change columns 0 and 1
        if event.m_col == 0 or event.m_col == 2:
            event.Veto()
        else:
            event.Skip()