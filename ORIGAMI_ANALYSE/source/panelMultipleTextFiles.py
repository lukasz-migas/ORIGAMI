# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
#    Copyright (C) 2017 Lukasz G. Migas <lukasz.migas@manchester.ac.uk>
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

import wx
from ids import *
import wx.lib.mixins.listctrl  as  listmix
import dialogs as dialogs
from dialogs import panelModifyTextSettings, panelAsk
from toolbox import (isempty, str2num, str2int, removeListDuplicates, convertRGB1to255,
                     convertRGB255to1, literal_eval, randomIntegerGenerator)
from operator import itemgetter
from numpy import arange
from styles import makeMenuItem
import re

class panelMultipleTextFiles ( wx.Panel ):
    
    def __init__( self, parent, config, icons, presenter ):
        wx.Panel.__init__ ( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, 
                            size = wx.Size( 300,400 ), style = wx.TAB_TRAVERSAL )

        self.parent = parent
        self.config = config  
        self.presenter = presenter
        self.icons = icons
        self.currentItem = None
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.topP = topPanel(self, self.icons, self.presenter, self.config)
        sizer.Add(self.topP, 1, wx.EXPAND | wx.ALL, 1)
        self.SetSizer(sizer)     


    def __del__( self ):
         pass
        
class EditableListCtrl(wx.ListCtrl, listmix.CheckListCtrlMixin):
    """
    Editable list
    """
    def __init__(self, parent, ID=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0): 
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.CheckListCtrlMixin.__init__(self)
        
class topPanel(wx.Panel):
    def __init__(self, parent, icons, presenter, config):
        wx.Panel.__init__(self, parent=parent)
        
        self.presenter = presenter # wx.App
        self.config = config
        self.icons = icons
        self.allChecked = True
        self.reverse = False
        self.lastColumn = None
        self.listOfSelected = []
                
        self.editItemDlg = None
                
        self.makeGUI()
                
        # add a couple of accelerators
        accelerators = [
            (wx.ACCEL_NORMAL, ord('X'), ID_checkAllItems_Text),
            (wx.ACCEL_NORMAL, ord('C'), ID_textPanel_assignColor),
            (wx.ACCEL_NORMAL, ord('E'), ID_textPanel_editItem),
            (wx.ACCEL_NORMAL, ord('P'), ID_useProcessedCombinedMenu),
            (wx.ACCEL_NORMAL, ord('H'), ID_get2DplotText),
            ]
        self.SetAcceleratorTable(wx.AcceleratorTable(accelerators))
                
        wx.EVT_MENU(self, ID_textPanel_editItem, self.OnOpenEditor)
        wx.EVT_MENU(self, ID_checkAllItems_Text, self.OnCheckAllItems)
        wx.EVT_MENU(self, ID_textPanel_assignColor, self.OnAssignColor)
        wx.EVT_MENU(self, ID_useProcessedCombinedMenu, self.setupMenus)
        wx.EVT_MENU(self, ID_get2DplotText, self.OnListGet2DIMMS)
        
    def makeGUI(self):
        """ Make panel GUI """
         # make toolbar
        toolbar = self.makeToolbar()
        self.makeListCtrl()
        
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(toolbar, 0, wx.EXPAND, 0)
        self.mainSizer.Add(self.filelist, 1, wx.EXPAND, 0)
        
        # fit layout
        self.mainSizer.Fit(self)
        self.SetSizer(self.mainSizer)
        
    def makeListCtrl(self):

        self.filelist = EditableListCtrl(self, style=wx.LC_REPORT|wx.LC_VRULES)

        for item in self.config._textlistSettings:
            order = item['order']
            name = item['name']
            if item['show']: 
                width = item['width']
            else: 
                width = 0
            self.filelist.InsertColumn(order, name, width=width, 
                                       format=wx.LIST_FORMAT_CENTER)
        
        self.filelist.Bind(wx.EVT_LIST_COL_CLICK, self.OnGetColumnClick)
        self.filelist.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnRightClickMenu)
        self.filelist.Bind(wx.EVT_LEFT_DCLICK, self.onItemActivated)
        self.filelist.Bind(wx.EVT_LIST_KEY_DOWN, self.onItemSelected)
        self.filelist.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onItemSelected)
        
    def onItemActivated(self, evt):
        self.currentItem, __ = self.filelist.HitTest(evt.GetPosition())
        if self.currentItem != -1:
            if not self.editItemDlg:
                self.OnOpenEditor(evt=None)
            else:
                self.editItemDlg.onUpdateGUI(self.OnGetItemInformation(self.currentItem))

    def onItemSelected(self, evt):
        keyCode = evt.GetKeyCode()
        if keyCode == wx.WXK_UP or keyCode == wx.WXK_DOWN:
            self.currentItem = evt.m_itemIndex
        else:
            self.currentItem = evt.m_itemIndex

        if evt != None:
            evt.Skip()
            
    def makeToolbar(self):
        
        # Make bindings
        self.Bind(wx.EVT_TOOL, self.onAddItems, id=ID_addTextFilesToList)
        self.Bind(wx.EVT_TOOL, self.onAnnotateTool, id=ID_annotateTextFilesMenu)
        self.Bind(wx.EVT_TOOL, self.onRemoveItems, id=ID_removeTextFilesMenu)
        self.Bind(wx.EVT_TOOL, self.onProcessItems, id=ID_processTextFilesMenu)
        self.Bind(wx.EVT_TOOL, self.OnCheckAllItems, id=ID_checkAllItems_Text)
        self.Bind(wx.EVT_COMBOBOX, self.onUpdateOverlayMethod, id=ID_textSelectOverlayMethod)
        self.Bind(wx.EVT_TOOL, self.onTableTool, id=ID_textPanel_guiMenuTool)
        self.Bind(wx.EVT_TOOL, self.onOverlayTool, id=ID_overlayTextFilesMenu)
        
        
        # Create toolbar for the table        
        toolbar = wx.ToolBar(self, style=wx.TB_HORIZONTAL | wx.TB_DOCKABLE, id = wx.ID_ANY) 
        toolbar.SetToolBitmapSize((16, 16))
        toolbar.AddTool(ID_checkAllItems_Text, self.icons.iconsLib['check16'] , 
                        shortHelpString="Check all items") 
        toolbar.AddTool(ID_addTextFilesToList, self.icons.iconsLib['add16'] , 
                        shortHelpString="Add...") 
        toolbar.AddTool(ID_removeTextFilesMenu, self.icons.iconsLib['remove16'], 
                        shortHelpString="Remove...")
        toolbar.AddTool(ID_annotateTextFilesMenu, self.icons.iconsLib['annotate16'],
                        shortHelpString="Annotate...")
        toolbar.AddTool(ID_processTextFilesMenu, self.icons.iconsLib['process16'], 
                        shortHelpString="Process...")
        toolbar.AddTool(ID_overlayTextFilesMenu, self.icons.iconsLib['overlay16'], 
                        shortHelpString="Overlay currently selected ions\tAlt+W")
        self.combo = wx.ComboBox(toolbar, ID_textSelectOverlayMethod, value= "Mask",
                                 choices=self.config.overlayChoices,
                                 style=wx.CB_READONLY, size=(110,-1))
        toolbar.AddControl(self.combo)
        toolbar.AddSeparator()
        toolbar.AddTool(ID_textPanel_guiMenuTool, self.icons.iconsLib['setting16'], 
                             shortHelpString="Table settings...")
        toolbar.Realize()
        
        return toolbar
        
    def OnRightClickMenu(self, evt): 
        
        # Make bindings
        self.Bind(wx.EVT_MENU, self.OnListGet2DIMMS, id=ID_get2DplotText)
        self.Bind(wx.EVT_MENU, self.OnListGet2DIMMS, id=ID_get2DplotTextWithProcss)
        self.Bind(wx.EVT_MENU, self.OnDeleteAll, id=ID_removeFileFromListPopup)
        self.Bind(wx.EVT_MENU, self.OnOpenEditor, id=ID_textPanel_editItem)
        self.Bind(wx.EVT_MENU, self.OnAssignColor, id=ID_textPanel_assignColor)
        
        self.currentItem, __ = self.filelist.HitTest(evt.GetPosition())
        menu = wx.Menu()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_get2DplotText,
                                     text='Show heatmap\tH', 
                                     bitmap=self.icons.iconsLib['heatmap_16']))
        menu.Append(ID_get2DplotTextWithProcss, "Process and show heatmap")
        menu.AppendSeparator()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_textPanel_assignColor,
                                     text='Assign new color\tC', 
                                     bitmap=self.icons.iconsLib['color_panel_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_textPanel_editItem,
                                     text='Edit file information\tE', 
                                     bitmap=self.icons.iconsLib['info16']))
        menu.AppendSeparator()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_removeFileFromListPopup,
                                     text='Remove item', 
                                     bitmap=self.icons.iconsLib['bin16']))
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()
        
    def onAnnotateTool(self, evt):
        self.Bind(wx.EVT_MENU, self.onChangeParameter, id=ID_assignChargeStateText)
        self.Bind(wx.EVT_MENU, self.onChangeParameter, id=ID_assignAlphaText)
        self.Bind(wx.EVT_MENU, self.onChangeParameter, id=ID_assignMaskText)
        self.Bind(wx.EVT_MENU, self.onChangeParameter, id=ID_assignMinThresholdText)
        self.Bind(wx.EVT_MENU, self.onChangeParameter, id=ID_assignMaxThresholdText)
        self.Bind(wx.EVT_MENU, self.onChangeColorBatch, id=ID_textPanel_changeColorBatch_palette)
        self.Bind(wx.EVT_MENU, self.onChangeColorBatch, id=ID_textPanel_changeColorBatch_colormap)
        self.Bind(wx.EVT_MENU, self.onChangeColormap, id=ID_textPanel_changeColormapBatch)
        
        menu = wx.Menu()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_assignChargeStateText,
                                     text='Assign charge state to selected ions', 
                                     bitmap=self.icons.iconsLib['assign_charge_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_assignAlphaText,
                                     text='Assign transparency value to selected ions', 
                                     bitmap=self.icons.iconsLib['transparency_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_assignMaskText,
                                     text='Assign mask value to selected ions', 
                                     bitmap=self.icons.iconsLib['mask_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_assignMinThresholdText,
                                     text='Assign minimum threshold to selected ions', 
                                     bitmap=self.icons.iconsLib['min_threshold_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_assignMaxThresholdText,
                                     text='Assign maximum threshold to selected ions', 
                                     bitmap=self.icons.iconsLib['max_threshold_16']))
        menu.AppendSeparator()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_textPanel_changeColormapBatch,
                                     text='Randomize colormap for selected items', 
                                     bitmap=self.icons.iconsLib['blank_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_textPanel_changeColorBatch_palette,
                                     text='Colour selected items using color palette', 
                                     bitmap=self.icons.iconsLib['blank_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_textPanel_changeColorBatch_colormap,
                                     text='Colour selected items using colormap', 
                                     bitmap=self.icons.iconsLib['blank_16']))
        
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()
        
    def onAddItems(self, evt):
        
        self.Bind(wx.EVT_MENU, self.presenter.onAddBlankDocument, id=ID_addNewOverlayDoc)
        
        menu = wx.Menu()
        menu.Append(ID_openTextFiles, "Add files\tCtrl+W")
        menu.AppendSeparator()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_addNewOverlayDoc,
                                     text='Add new comparison document\tAlt+D', 
                                     bitmap=self.icons.iconsLib['new_document_16']))
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()
        
    def onRemoveItems(self, evt):
        
        # Make bindings 
        self.Bind(wx.EVT_MENU, self.OnDeleteAll, id=ID_removeAllFilesFromList)
        self.Bind(wx.EVT_MENU, self.OnDeleteAll, id=ID_removeSelectedFilesFromList)
        self.Bind(wx.EVT_MENU, self.OnClearTable, id=ID_clearTableText)
        self.Bind(wx.EVT_MENU, self.OnClearTable, id=ID_clearSelectedText)
        
        menu = wx.Menu()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_clearTableText,
                                     text='Clear table', 
                                     bitmap=self.icons.iconsLib['clear_16']))
        menu.Append(ID_clearSelectedText, "Clear selected")
        menu.AppendSeparator()
        menu.Append(ID_removeSelectedFilesFromList, "Remove selected files")
        menu.Append(ID_removeAllFilesFromList, "Remove all files")
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()
        
    def onProcessItems(self, evt):
        
        self.Bind(wx.EVT_TOOL, self.presenter.onProcessMultipleTextFiles, id=ID_processTextFiles)
        self.Bind(wx.EVT_TOOL, self.presenter.onProcessMultipleTextFiles, id=ID_processAllTextFiles)
        
        menu = wx.Menu()
        menu.Append(ID_processTextFiles, "Process selected files")
        menu.Append(ID_processAllTextFiles, "Process all files")
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()
        
    def onOverlayTool(self, evt):

        self.Bind(wx.EVT_TOOL, self.presenter.onOverlayMultipleIons1D, id=ID_overlayTextfromList1D)
        self.Bind(wx.EVT_TOOL, self.presenter.onOverlayMultipleIons1D, id=ID_overlayTextfromListRT)
        self.Bind(wx.EVT_TOOL, self.presenter.onOverlayMultipleIons, id=ID_overlayTextFromList)
        self.Bind(wx.EVT_MENU, self.setupMenus, id=ID_useProcessedCombinedMenu)
        
        menu = wx.Menu()
        menu.Append(ID_overlayTextfromList1D, "Overlay mobiligrams (selected)")
        menu.Append(ID_overlayTextfromListRT, "Overlay chromatograms (selected)")
        menu.AppendSeparator()
        self.useProcessed_check = menu.AppendCheckItem(ID_useProcessedCombinedMenu, "Use processed data (when available)\tP",
                                                       help="When checked, processed data is used in the overlay (2D) plots.")
        self.useProcessed_check.Check(self.config.overlay_usedProcessed)
        menu.AppendSeparator()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_overlayTextFromList,
                                     text='Overlay heatmaps (selected)\tAlt+W', 
                                     bitmap=self.icons.iconsLib['heatmap_grid_16']))
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()
        
    def onTableTool(self, evt):
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_textPanel_table_startCE)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_textPanel_table_endCE)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_textPanel_table_charge)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_textPanel_table_color)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_textPanel_table_colormap)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_textPanel_table_alpha)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_textPanel_table_mask)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_textPanel_table_document)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_textPanel_table_label)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_textPanel_table_shape)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_textPanel_table_hideAll)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_textPanel_table_restoreAll)
        

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
        
    def onChangeColormap(self, evt):
        # get number of checked items
        check_count = 0
        for row in range(self.filelist.GetItemCount()):
            if self.filelist.IsChecked(index=row):
                check_count += 1 
        
        if check_count > len(self.config.narrowCmapList):
            colormaps = self.config.narrowCmapList
        else:
            colormaps = self.config.narrowCmapList + self.config.cmaps2
        
        for row in range(self.filelist.GetItemCount()):
            if self.filelist.IsChecked(index=row):
                self.currentItem = row
                colormap = colormaps[row]
                self.filelist.SetStringItem(row, 
                                            self.config.textlistColNames['colormap'], 
                                            str(colormap))
                
                # update document
                try:
                    self.onUpdateDocument(evt=None)
                except TypeError:
                    print("Please select item")
        
    def onChangeColorBatch(self, evt):
        # get number of checked items
        check_count = 0
        for row in range(self.filelist.GetItemCount()):
            if self.filelist.IsChecked(index=row):
                check_count += 1 
                
        if evt.GetId() == ID_textPanel_changeColorBatch_palette:
            colors = self.presenter.view.panelPlots.onChangePalette(None, n_colors=check_count, return_colors=True)
        else:
            colors = self.presenter.view.panelPlots.onGetColormapList(n_colors=check_count)
            
        for row in range(self.filelist.GetItemCount()):
            self.currentItem = row
            if self.filelist.IsChecked(index=row):
                color = colors[row]
                self.filelist.SetItemBackgroundColour(row, convertRGB1to255(color))
                
            self.onUpdateDocument(evt=None)
        
    def onUpdateTable(self, evt):
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
                self.filelist.SetColumnWidth(i, col_width)
            return
        elif evtID == ID_textPanel_table_hideAll:
            for i in range(len(self.config._textlistSettings)):
                self.config._textlistSettings[i]['show'] = False
                col_width = 0
                self.filelist.SetColumnWidth(i, col_width)
            return 
        
        # check values
        col_check = not self.config._textlistSettings[col_index]['show']
        self.config._textlistSettings[col_index]['show'] = col_check
        if col_check: col_width = self.config._textlistSettings[col_index]['width']
        else: col_width = 0
        # set new column width
        self.filelist.SetColumnWidth(col_index, col_width)
        
    def onChangeParameter(self, evt):
        """ Iterate over list to assign charge state """
        
        rows = self.filelist.GetItemCount()
        if rows == 0: return
        
        if evt.GetId() == ID_assignChargeStateText:
            ask_kwargs = {'static_text':'Assign charge state to selected items.',
                          'value_text':"", 
                          'validator':'integer',
                          'keyword':'charge'}
        elif evt.GetId() == ID_assignAlphaText:
            ask_kwargs = {'static_text':'Assign new transparency value to selected items \nTypical transparency values: 0.5\nRange 0-1',
                          'value_text':0.5, 
                          'validator':'float',
                          'keyword':'alpha'}
        elif evt.GetId() == ID_assignMaskText:
            ask_kwargs = {'static_text':'Assign new mask value to selected items \nTypical mask values: 0.25\nRange 0-1',
                          'value_text':0.25, 
                          'validator':'float',
                          'keyword':'mask'}
        elif evt.GetId() == ID_assignMinThresholdText:
            ask_kwargs = {'static_text':'Assign minimum threshold value to selected items \nTypical mask values: 0.0\nRange 0-1',
                          'value_text':0.0, 
                          'validator':'float',
                          'keyword':'min_threshold'}
        elif evt.GetId() == ID_assignMaxThresholdText:
            ask_kwargs = {'static_text':'Assign maximum threshold value to selected items \nTypical mask values: 1.0\nRange 0-1',
                          'value_text':1.0, 
                          'validator':'float',
                          'keyword':'max_threshold'}

        ask = panelAsk(self, self.presenter, **ask_kwargs)
        if ask.ShowModal() == wx.ID_OK: 
            pass
        
        if self.ask_value == None: 
            return
        
        for row in range(rows):
            if self.filelist.IsChecked(index=row):                
                filename = self.filelist.GetItem(row, self.config.textlistColNames['filename']).GetText()
                document = self.presenter.documentsDict[filename]
                if not ask_kwargs['keyword'] in ['min_threshold', 'max_threshold']:
                    self.filelist.SetStringItem(index=row, 
                                                col=self.config.textlistColNames[ask_kwargs['keyword']], 
                                                label=str(self.ask_value))
                if document.got2DIMS:
                    document.IMS2D[ask_kwargs['keyword']] = self.ask_value
                if document.got2Dprocess:
                    document.IMS2Dprocess[ask_kwargs['keyword']] = self.ask_value

                # update document
                self.presenter.documentsDict[document.title] = document
        
    def setupMenus(self, evt):
        """ Check/uncheck menu item """
        
        evtID = evt.GetId()
            
        if evtID == ID_useProcessedCombinedMenu:
            check_value = not self.config.overlay_usedProcessed
            self.config.overlay_usedProcessed = check_value
            args = ("Peak list panel: Using processing data was switched to %s" % self.config.overlay_usedProcessed, 4)
            self.presenter.onThreading(evt, args, action='updateStatusbar')
        
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
    
    def OnListGet2DIMMS(self, evt):
        """
        This function extracts 2D array and plots it in 2D/3D
        """
        
        itemInfo = self.OnGetItemInformation(self.currentItem)
        print(re.split(': ', itemInfo['document']))
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
            
        # Extract 2D data from the document
        zvals, xvals, xlabel, yvals, ylabel, cmap = self.presenter.get2DdataFromDictionary(dictionary=data,
                                                                                           dataType='plot',
                                                                                           compact=False)
        
        if isempty(xvals) or isempty(yvals) or xvals is "" or yvals is "":
            msg1 = "Missing x- and/or y-axis labels. Cannot continue!"
            msg2 = "Add x- and/or y-axis labels to each file before continuing!"
            msg = '\n'.join([msg1,msg2])
            dialogs.dlgBox(exceptionTitle='Missing data', 
                           exceptionMsg= msg,
                           type="Error")
            return
        
        # Process data
        if evt.GetId() == ID_get2DplotTextWithProcss:
            zvals = self.presenter.process2Ddata(zvals=zvals.copy(), return_data=True)
        else: pass 
        self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['2D'])
        self.presenter.onPlot2DIMS2(zvals, xvals, yvals, xlabel, ylabel, cmap)
            
    def OnDeleteAll(self, evt):
        """ 
        This function removes files from the document tree, dictionary and table
        Parameters:
        ----------
        evt : Wxpython event
            Normal event from toolbar or context menu
        """
        
        if evt.GetId() == ID_removeSelectedFilesFromList:
            currentItems = self.filelist.GetItemCount()-1
            while (currentItems >= 0):
                if self.filelist.IsChecked(index=currentItems) == True:
                    selectedItem = self.filelist.GetItem(currentItems, 
                                                         self.config.textlistColNames['filename']).GetText()
                    # Delete selected document from dictionary + table        
                    try:
                        outcome = self.presenter.view.panelDocuments.topP.documents.removeDocument(deleteItem=selectedItem, evt=None)
                    except wx._core.PyAssertionError: outcome=False
                    if outcome == False: 
                        print('Failed to delete the item')
                        return
                    # Delete from dictionary
                    try:
                        del self.presenter.documentsDict[selectedItem]
                    except KeyError: pass
                    # Delete from list
                    self.filelist.DeleteItem(currentItems)
                    currentItems-=1
                else:
                    currentItems-=1
        elif evt.GetId() == ID_removeFileFromListPopup:
            selectedItem = self.filelist.GetItem(self.currentItem, self.config.textlistColNames['filename']).GetText()
            
            # Delete selected document from dictionary + table        
            try:
                outcome = self.presenter.view.panelDocuments.topP.documents.removeDocument(deleteItem=selectedItem, evt=None)
            except wx._core.PyAssertionError: outcome=False
            if outcome == False: 
                print('Failed to delete the item')
                return
            try:
                del self.presenter.documentsDict[selectedItem]
            except KeyError: pass
            # Delete from list
            self.filelist.DeleteItem(self.currentItem)
        elif evt.GetId() == ID_removeAllFilesFromList:
        # Ask if you are sure to delete it!
            dlg = dialogs.dlgBox(exceptionTitle='Are you sure?', 
                                 exceptionMsg= "Are you sure you would like to delete ALL text documents?",
                                 type="Question")
            if dlg == wx.ID_NO:
                print('Cancelled operation')
                return
            else:
                currentItems = self.filelist.GetItemCount()-1
                while (currentItems >= 0):
                    selectedItem = self.filelist.GetItem(currentItems, self.config.textlistColNames['filename']).GetText()
                    print(selectedItem)
                    # Delete selected document from dictionary + table        
                    try:
                        outcome = self.presenter.view.panelDocuments.topP.documents.removeDocument(deleteItem=selectedItem, evt=None)
                    except wx._core.PyAssertionError: outcome=True
                    if outcome == False: 
                        print('Failed to delete the item')
                        return
                    try:
                        del self.presenter.documentsDict[selectedItem]
                    except KeyError: pass
                    self.filelist.DeleteItem(currentItems)
                    currentItems-=1
        print(''.join(["Remaining documents: ", str(len(self.presenter.documentsDict))]))
        
    def onCheckDuplicates(self, fileName=None):
        currentItems = self.filelist.GetItemCount()-1
        while (currentItems >= 0):
            fileInTable = self.filelist.GetItem(currentItems,
                                                self.config.textlistColNames['filename']).GetText()
            if fileInTable == fileName:
                print('File '+ fileInTable + ' already in the table')
                currentItems = 0
                return True
            else:
                currentItems-=1
        return False

    def onRemoveDuplicates(self, evt):
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
                if col in [0, 1, 5, 6]: 
                    itemData = str2num(item.GetText())
                    if itemData == None: itemData = 0
                    tempRow.append(itemData)
                elif col == 2:
                    itemData = str2int(item.GetText())
                    if itemData == None: itemData = 0
                    tempRow.append(itemData)
                else:
                    tempRow.append(item.GetText())
            tempRow.append(self.filelist.IsChecked(index=row))
            tempRow.append(self.filelist.GetItemBackgroundColour(row))
            tempData.append(tempRow)
            
        # Remove duplicates
        tempData = removeListDuplicates(input=tempData,
                                        columnsIn=['start', 'end', 'charge', 
                                        'color', 'colormap', 'alpha', 'mask', 
                                        'label', 'shape', 'filename', 'check', 'rgb'],
                                        limitedCols=['filename'])     
        rows = len(tempData)
        # Clear table
        self.filelist.DeleteAllItems()

        checkData, rgbData = [], []
        for check in tempData:
            rgbData.append(check[-1])
            del check[-1]
            checkData.append(check[-1])
            del check[-1]
            
        # Reinstate data
        rowList = arange(len(tempData))
        for row, check, rgb in zip(rowList, checkData, rgbData):
            self.filelist.Append(tempData[row])
            self.filelist.CheckItem(row, check)
            self.filelist.SetItemBackgroundColour(row, rgb)
            
        if evt is None: return
        else:
            evt.Skip()

    def OnClearTable(self, evt):
        """
        This function clears the table without deleting any items from the document tree
        """
        # Ask if you want to delete all items
        evtID = evt.GetId()

        if evtID == ID_clearSelectedText:
            row = self.filelist.GetItemCount() - 1
            while (row >= 0):
                if self.filelist.IsChecked(index=row):
                    self.filelist.DeleteItem(row)
                row-=1
        else:
            dlg = dialogs.dlgBox(exceptionTitle='Are you sure?', 
                                 exceptionMsg= "Are you sure you would like to clear the table??",
                                 type="Question")
            if dlg == wx.ID_NO:
                print('Cancelled operation')
                return
            self.filelist.DeleteAllItems()
        
    def OnGetColumnClick(self, evt):
        self.OnSortByColumn(column=evt.GetColumn())
        
    def OnSortByColumn(self, column):
        """
        Sort data in filelist based on pressed column
        """
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
                #  We want to make sure certain columns are numbers
                if (col==self.config.textlistColNames['start'] or 
                    col==self.config.textlistColNames['end'] or 
                    col==self.config.textlistColNames['alpha'] or 
                    col==self.config.textlistColNames['mask']):
                    itemData = str2num(item.GetText())
                    if itemData == None: itemData = 0
                    tempRow.append(itemData)
                elif col==self.config.textlistColNames['charge']:
                    itemData = str2int(item.GetText())
                    if itemData == None: itemData = 0
                    tempRow.append(itemData)
                else:
                    tempRow.append(item.GetText())
            tempRow.append(self.filelist.IsChecked(index=row))
            tempRow.append(self.filelist.GetItemBackgroundColour(row))
            tempData.append(tempRow)
            
        # Sort data  
        tempData.sort(key = itemgetter(column), reverse=self.reverse)
        # Clear table
        self.filelist.DeleteAllItems()
        
        checkData, rgbData = [], []
        for check in tempData:
            rgbData.append(check[-1])
            del check[-1]
            checkData.append(check[-1])
            del check[-1]

        # Reinstate data
        rowList = arange(len(tempData))
        for row, check, rgb in zip(rowList, checkData, rgbData):
            self.filelist.Append(tempData[row])
            self.filelist.CheckItem(row, check)
            self.filelist.SetItemBackgroundColour(row, rgb)

    def onUpdateOverlayMethod(self, evt):
        self.config.overlayMethod = self.combo.GetStringSelection()

        if evt != None:
            evt.Skip()
            
    def OnGetItemInformation(self, itemID, return_list=False):
        
        # get item information
        information = {'minCE':str2num(self.filelist.GetItem(itemID, self.config.textlistColNames['start']).GetText()),
                       'maxCE':str2num(self.filelist.GetItem(itemID, self.config.textlistColNames['end']).GetText()),
                       'charge':str2int(self.filelist.GetItem(itemID, self.config.textlistColNames['charge']).GetText()),
                       'color':self.filelist.GetItemBackgroundColour(item=itemID),
                       'colormap':self.filelist.GetItem(itemID, self.config.textlistColNames['colormap']).GetText(),
                       'alpha':str2num(self.filelist.GetItem(itemID, self.config.textlistColNames['alpha']).GetText()),
                       'mask':str2num(self.filelist.GetItem(itemID, self.config.textlistColNames['mask']).GetText()),
                       'label':self.filelist.GetItem(itemID, self.config.textlistColNames['label']).GetText(),
                       'shape':self.filelist.GetItem(itemID, self.config.textlistColNames['shape']).GetText(),
                       'document':self.filelist.GetItem(itemID, self.config.textlistColNames['filename']).GetText(),
                       'select':self.filelist.IsChecked(itemID),
                       'id':itemID}

        try:
            flag_error = False
            self.docs = self.presenter.documentsDict[self.filelist.GetItem(itemID, self.config.textlistColNames['filename']).GetText()]
        except KeyError:
            flag_error = True
            document_title, ion_title = re.split(': ', information['document'])
            document = self.presenter.documentsDict[document_title]
        # check whether the ion has any previous information
        min_threshold, max_threshold = 0, 1
        
        if not flag_error:
            if self.docs.IMS2D:
                min_threshold = self.docs.IMS2D.get('min_threshold', 0)
                max_threshold = self.docs.IMS2D.get('max_threshold', 1)
            else:
                min_threshold = self.docs.IMS2DcompData[ion_title].get('min_threshold', 0)
                max_threshold = self.docs.IMS2DcompData[ion_title].get('max_threshold', 0)
                
        information['min_threshold'] = min_threshold
        information['max_threshold'] = max_threshold
                
        if return_list:
            minCE = information['minCE']
            maxCE = information['maxCE']
            charge = information['charge']
            color = information['color']
            colormap = information['colormap']
            alpha = information['alpha']
            mask = information['mask']
            shape = information['shape']
            label = information['label']
            document = information['document']
            min_threshold = information['min_threshold']
            max_threshold = information['max_threshold']
            return minCE, maxCE, charge, color, colormap, alpha, mask, shape, label, document, min_threshold, max_threshold

        return information
    # ----
    
    def OnGetValue(self, value_type='color'):
        information = self.OnGetItemInformation(self.currentItem)
        
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
    # ----
    def OnAssignColor(self, evt, itemID=None, give_value=False):
        """
        @param itemID (int): value for item in table
        @param give_value (bool): should/not return color
        """ 
        
        if itemID != None:
            self.currentItem = itemID
                    
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
            self.filelist.SetStringItem(self.currentItem, 
                                        self.config.textlistColNames['color'], 
                                        str(convertRGB255to1(newColour)))
            self.filelist.SetItemBackgroundColour(self.currentItem, newColour)
            # Retrieve custom colors
            for i in xrange(15): 
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
            self.filelist.SetStringItem(self.currentItem, self.config.textlistColNames['color'],
                                        str(convertRGB255to1(newColour)))
            self.filelist.SetItemBackgroundColour(self.currentItem, newColour)
            if give_value:
                return newColour

    def onUpdateDocument(self, evt, itemInfo=None):
        
        # get item info
        if itemInfo == None:
            itemInfo = self.OnGetItemInformation(self.currentItem)


        keywords = ['color', 'colormap', 'alpha', 'mask', 'label', 'min_threshold',
                    'max_threshold', 'charge', 'cmap']
        
        # get item
        try:
            document = self.presenter.documentsDict[itemInfo['document']]
            for keyword in keywords:
                if keyword == "cmap": keyword_name = "colormap"
                else: keyword_name = keyword
                if document.got2DIMS:
                    document.IMS2D[keyword] = itemInfo[keyword_name]
                if document.got2Dprocess:
                    document.IMS2Dprocess[keyword] = itemInfo[keyword_name]
        except:
            document_title, ion_title = re.split(': ', itemInfo['document'])
            document = self.presenter.documentsDict[document_title]
            for keyword in keywords:
                if keyword == "cmap": keyword_name = "colormap"
                else: keyword_name = keyword
                if ion_title in document.IMS2DcompData:
                    document.IMS2DcompData[ion_title][keyword] = itemInfo[keyword_name]
                else:
                    document.IMS2Dions[ion_title][keyword] = itemInfo[keyword_name]
        
        # Update file list
        self.presenter.OnUpdateDocument(document, 'document')
            
    def OnOpenEditor(self, evt):
        
        if evt == None: 
            evtID = ID_textPanel_editItem
        else:
            evtID = evt.GetId()

        rows = self.filelist.GetItemCount() - 1
        if evtID == ID_textPanel_editItem:
            if self.currentItem  < 0:
                print('Please select item in the table first.')
                return
            dlg_kwargs = self.OnGetItemInformation(self.currentItem)
            
            self.editItemDlg = panelModifyTextSettings(self,
                                                       self.presenter, 
                                                       self.config,
                                                       **dlg_kwargs)
            self.editItemDlg.Centre()
            self.editItemDlg.Show()
        elif evtID == ID_textPanel_edit_selected:
            while rows >= 0:
                if self.filelist.IsChecked(rows):
                    information = self.OnGetItemInformation(rows)
                    
                    dlg_kwargs = {'select': self.filelist.IsChecked(rows),
                                  'color': information['color'],
                                  'title': information['document'],
                                  'min_threshold': information['min_threshold'],
                                  'max_threshold': information['max_threshold'],
                                  'label': information['label'],
                                  'id':rows
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
                 
                dlg_kwargs = {'select': self.filelist.IsChecked(row),
                              'color': information['color'],
                              'title': information['document'],
                              'min_threshold': information['min_threshold'],
                              'max_threshold': information['max_threshold'],
                              'label': information['label'],
                              'id':row
                              }
                 
                self.editItemDlg = panelModifyTextSettings(self, 
                                                           self.presenter, 
                                                           self.config,
                                                           **dlg_kwargs)
                self.editItemDlg.Show()   
            
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
            elif document in info['document'] :
                self.filelist.DeleteItem(row)
                row-=1
            else:
                row-=1
        
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            