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

import wx, csv, time
import wx.lib.mixins.listctrl as listmix
from ast import literal_eval
from operator import itemgetter
from numpy import arange, vstack, insert
from pandas import read_csv
from natsort import natsorted

from ids import *
import dialogs as dialogs
from dialogs import panelAsk
from gui_elements.panel_modifyIonSettings import panelModifyIonSettings
from toolbox import (isempty, str2num, str2int, saveAsText, convertRGB1to255, 
                             convertRGB255to1, randomIntegerGenerator, removeListDuplicates,
                             checkExtension, roundRGB, randomColorGenerator,
                             determineFontColor)
from styles import gauge, makeMenuItem


class panelMultipleIons ( wx.Panel ):
    
    def __init__( self, parent, config, icons, helpInfo, presenter ):
        wx.Panel.__init__ ( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, 
                            size = wx.Size( 300,400 ), style = wx.TAB_TRAVERSAL )

        self.parent = parent
        self.config = config  
        self.help = helpInfo
        self.presenter = presenter
        self.currentItem = None
        self.icons = icons

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.topP = topPanel(self, self.config, self.icons, self.help, self.presenter)
        sizer.Add(self.topP, 1, wx.EXPAND | wx.ALL, 1)
        self.SetSizer(sizer)

class ListCtrl(wx.ListCtrl, listmix.CheckListCtrlMixin):
    """ListCtrl"""
     
    def __init__(self, parent, id=-1, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.LC_REPORT):
        wx.ListCtrl.__init__(self, parent, id, pos, size, style)
        listmix.CheckListCtrlMixin.__init__(self)
        
class topPanel(wx.Panel):
    def __init__(self, parent, config, icons, helpInfo, presenter):
        wx.Panel.__init__(self, parent=parent)
        
        self.config = config
        self.help = helpInfo
        self.presenter = presenter # wx.App
        self.icons = icons
        self.view = parent.parent
        
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
        self.currentItem = None
        self.ask_value = None
        self.flag = False # flag to either show or hide annotation panel
        self.useInternalParams = self.config.useInternalParamsCombine
        self.process = False
        
        self.data_processing = self.view.data_processing
        
        self.makeGUI()
        
        if self.plotAutomatically:
            self.combo.Bind(wx.EVT_COMBOBOX, self.on_overlay_heatmap)
        
        # add a couple of accelerators
        accelerators = [
            (wx.ACCEL_NORMAL, ord('A'), ID_ionPanel_addToDocument),
            (wx.ACCEL_NORMAL, ord('B'), ID_combinedCV_binMSCombinedMenu),
            (wx.ACCEL_NORMAL, ord('C'), ID_ionPanel_assignColor),
            (wx.ACCEL_NORMAL, ord('E'), ID_ionPanel_editItem),
            (wx.ACCEL_NORMAL, ord('H'), ID_highlightRectAllIons),
            (wx.ACCEL_NORMAL, ord('I'), ID_useInternalParamsCombinedMenu),
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
        wx.EVT_MENU(self, ID_useInternalParamsCombinedMenu, self.onCheckTool)
        wx.EVT_MENU(self, ID_useProcessedCombinedMenu, self.onCheckTool)
        wx.EVT_MENU(self, ID_ionPanel_normalize1D, self.onCheckTool)
        wx.EVT_MENU(self, ID_combinedCV_binMSCombinedMenu, self.onCheckTool)
        wx.EVT_MENU(self, ID_highlightRectAllIons, self.presenter.onShowExtractedIons)
        wx.EVT_MENU(self, ID_ionPanel_check_all, self.OnCheckAllItems)
        wx.EVT_MENU(self, ID_ionPanel_assignColor, self.OnAssignColor)
        wx.EVT_MENU(self, ID_ionPanel_show_zoom_in_MS, self.on_plot)
        wx.EVT_MENU(self, ID_ionPanel_show_mobiligram, self.on_plot)
        wx.EVT_MENU(self, ID_ionPanel_check_selected, self.on_check_selected)
        wx.EVT_MENU(self, ID_ionPanel_delete_rightClick, self.OnDeleteAll)
        
    def makeGUI(self):
        """ Make panel GUI """
         # make toolbar
        toolbar = self.makeToolbar()
        self.makeListCtrl()
        
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(toolbar, 0, wx.EXPAND, 0)
        self.mainSizer.Add(self.peaklist, 1, wx.EXPAND, 0)
        
        # fit layout
        self.mainSizer.Fit(self)
        self.SetSizer(self.mainSizer)
            
    def makeToolbar(self):
        
        # Make bindings
        self.Bind(wx.EVT_TOOL, self.onAddTool, id=ID_addIonsMenu)  
        self.Bind(wx.EVT_TOOL, self.onRemoveTool, id=ID_removeIonsMenu)
        self.Bind(wx.EVT_TOOL, self.onExtractTool, id=ID_extractIonsMenu)
        self.Bind(wx.EVT_TOOL, self.onProcessTool, id=ID_processIonsMenu)
        self.Bind(wx.EVT_TOOL, self.onSaveTool, id=ID_saveIonsMenu)
        self.Bind(wx.EVT_TOOL, self.onAnnotateTool, id=ID_showIonsMenu)
        self.Bind(wx.EVT_TOOL, self.onOverlayTool, id=ID_overlayIonsMenu)
        self.Bind(wx.EVT_TOOL, self.OnCheckAllItems, id=ID_ionPanel_check_all)
        
        # Create toolbar for the table
        toolbar = wx.ToolBar(self, style=wx.TB_HORIZONTAL | wx.TB_DOCKABLE, id = wx.ID_ANY) 
        toolbar.SetToolBitmapSize((16, 16)) 
        toolbar.AddTool(ID_ionPanel_check_all, self.icons.iconsLib['check16'] , 
                        shortHelpString="Check all items\tX")
        toolbar.AddTool(ID_addIonsMenu, self.icons.iconsLib['add16'], 
                              shortHelpString="Add...") 
        toolbar.AddTool(ID_removeIonsMenu, self.icons.iconsLib['remove16'],
                             shortHelpString="Remove...")
        toolbar.AddTool(ID_showIonsMenu, self.icons.iconsLib['annotate16'],
                             shortHelpString="Annotate...")
        toolbar.AddTool(ID_extractIonsMenu, self.icons.iconsLib['extract16'],
                             shortHelpString="Extract...")
        toolbar.AddTool(ID_processIonsMenu, self.icons.iconsLib['process16'], 
                             shortHelpString="Process...")
        toolbar.AddTool(ID_overlayIonsMenu, self.icons.iconsLib['overlay16'],
                             shortHelpString="Overlay selected ions")
        self.combo = wx.ComboBox(toolbar, ID_selectOverlayMethod, value= "Transparent",
                                 choices=self.config.overlayChoices,
                                 style=wx.CB_READONLY, size=(110, -1))
        toolbar.AddControl(self.combo)
        toolbar.AddTool(ID_saveIonsMenu, self.icons.iconsLib['save16'], 
                             shortHelpString="Save...")

        toolbar.Realize()     
        
        return toolbar
              
    def makeListCtrl(self):

        self.peaklist = ListCtrl(self, style=wx.LC_REPORT|wx.LC_VRULES)
        for item in self.config._peakListSettings:
            order = item['order']
            name = item['name']
            if item['show']: 
                width = item['width']
            else: 
                width = 0
            self.peaklist.InsertColumn(order, name, width=width, format=wx.LIST_FORMAT_CENTER)

        self.peaklist.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnRightClickMenu)
        self.peaklist.Bind(wx.EVT_LIST_COL_CLICK, self.OnGetColumnClick)
        self.peaklist.Bind(wx.EVT_LEFT_DCLICK, self.onItemActivated)
        self.peaklist.Bind(wx.EVT_LIST_KEY_DOWN, self.onItemSelected)
        self.peaklist.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onItemSelected)
        self.peaklist.Bind(wx.EVT_LIST_COL_RIGHT_CLICK, self.onColumnRightClickMenu)
                
    def onItemActivated(self, evt):
        """Create annotation for activated peak."""
        
        self.currentItem, __ = self.peaklist.HitTest(evt.GetPosition())
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
    # ----
    def onRenameItem(self, old_name, new_name, item_type="Document"):
        for row in range(self.peaklist.GetItemCount()):
            itemInfo = self.OnGetItemInformation(itemID=row)
            if item_type == "document":
                if itemInfo['document'] == old_name:
                    self.peaklist.SetStringItem(index=row,
                                                col=self.config.peaklistColNames['filename'],
                                                label=new_name)
#             elif item_type == "filename":
#                 if itemInfo['filename'] == old_name:
#                     self.peaklist.SetStringItem(index=row,
#                                                 col=self.config.peaklistColNames['filename'],
#                                                 label=new_name)
          
    def onColumnRightClickMenu(self, evt):
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_ionPanel_table_startMS)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_ionPanel_table_endMS)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_ionPanel_table_color)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_ionPanel_table_colormap)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_ionPanel_table_charge)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_ionPanel_table_intensity)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_ionPanel_table_document)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_ionPanel_table_alpha)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_ionPanel_table_mask)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_ionPanel_table_document)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_ionPanel_table_label)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_ionPanel_table_method)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_ionPanel_table_hideAll)
        self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_ionPanel_table_restoreAll)
        

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
           
    def OnRightClickMenu(self, evt):
        
        # Menu events
        self.Bind(wx.EVT_MENU, self.on_plot, id=ID_ionPanel_show_zoom_in_MS)
        self.Bind(wx.EVT_MENU, self.on_plot, id=ID_ionPanel_show_mobiligram)
        self.Bind(wx.EVT_MENU, self.on_plot, id=ID_ionPanel_show_chromatogram)
        self.Bind(wx.EVT_MENU, self.on_plot, id=ID_ionPanel_show_heatmap)
        self.Bind(wx.EVT_MENU, self.on_plot, id=ID_ionPanel_show_process_heatmap)
        self.Bind(wx.EVT_MENU, self.OnOpenEditor, id=ID_ionPanel_editItem)
        self.Bind(wx.EVT_MENU, self.OnAssignColor, id=ID_ionPanel_assignColor)
        self.Bind(wx.EVT_MENU, self.OnDeleteAll, id=ID_ionPanel_delete_rightClick)
        
        self.currentItem, __ = self.peaklist.HitTest(evt.GetPosition())
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
                 
    def onAnnotateTool(self, evt):
        self.Bind(wx.EVT_MENU, self.presenter.onShowExtractedIons, id=ID_highlightRectAllIons)
        self.Bind(wx.EVT_MENU, self.onChangeParameter, id=ID_assignChargeStateIons)
        self.Bind(wx.EVT_MENU, self.onChangeParameter, id=ID_assignAlphaIons)
        self.Bind(wx.EVT_MENU, self.onChangeParameter, id=ID_assignMaskIons)
        self.Bind(wx.EVT_MENU, self.onChangeParameter, id=ID_assignMinThresholdIons)
        self.Bind(wx.EVT_MENU, self.onChangeParameter, id=ID_assignMaxThresholdIons)
        self.Bind(wx.EVT_MENU, self.onChangeColorBatch, id=ID_ionPanel_changeColorBatch_color)
        self.Bind(wx.EVT_MENU, self.onChangeColorBatch, id=ID_ionPanel_changeColorBatch_palette)
        self.Bind(wx.EVT_MENU, self.onChangeColorBatch, id=ID_ionPanel_changeColorBatch_colormap)
        self.Bind(wx.EVT_MENU, self.onChangeColormap, id=ID_ionPanel_changeColormapBatch)
        
        menu = wx.Menu()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_highlightRectAllIons,
                                     text='Highlight extracted items on MS plot\tH', 
                                     bitmap=self.icons.iconsLib['highlight_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_assignChargeStateIons,
                                     text='Assign charge state to selected ions', 
                                     bitmap=self.icons.iconsLib['assign_charge_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_assignAlphaIons,
                                     text='Assign transparency value to selected ions', 
                                     bitmap=self.icons.iconsLib['transparency_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_assignMaskIons,
                                     text='Assign mask value to selected ions', 
                                     bitmap=self.icons.iconsLib['mask_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_assignMinThresholdIons,
                                     text='Assign minimum threshold to selected ions', 
                                     bitmap=self.icons.iconsLib['min_threshold_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_assignMaxThresholdIons,
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

    def onAddTool(self, evt):
        
        self.Bind(wx.EVT_MENU, self.onOpenPeakList, id=ID_addManyIonsCSV)
        self.Bind(wx.EVT_MENU, self.onDuplicateIons, id=ID_duplicateIons)
        self.Bind(wx.EVT_MENU, self.on_add_blank_document_overlay, id=ID_addNewOverlayDoc)
       
        menu = wx.Menu()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_addManyIonsCSV,
                                     text='Add list of ions (.csv/.txt)\tCtrl+L', 
                                     bitmap=self.icons.iconsLib['filelist_16'],
                                     help_text='Format: min, max, charge (optional), label (optional), color (optional)'))
        menu.AppendSeparator()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_addNewOverlayDoc,
                                     text='Create blank COMPARISON document\tAlt+D', 
                                     bitmap=self.icons.iconsLib['new_document_16']))
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()
        
    def onExtractTool(self, evt):
        
        self.Bind(wx.EVT_MENU, self.onCheckTool, id=ID_ionPanel_automaticExtract)
        self.Bind(wx.EVT_MENU, self.on_extract_all, id=ID_extractAllIons)
        self.Bind(wx.EVT_MENU, self.on_extract_selected, id=ID_extractSelectedIon)
        self.Bind(wx.EVT_MENU, self.on_extract_new, id=ID_extractNewIon)
        
        menu = wx.Menu()
        self.automaticExtract_check = menu.AppendCheckItem(ID_ionPanel_automaticExtract, "Extract automatically",
                                                           help="Ions will be extracted automatically")
        self.automaticExtract_check.Check(self.extractAutomatically)
        menu.AppendSeparator()
        menu.Append(ID_extractNewIon, "Extract new ions")
        menu.Append(ID_extractSelectedIon, "Extract selected ions")
        menu.Append(ID_extractAllIons, "Extract all ions\tAlt+E")
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()
        
    def onOverlayTool(self, evt):

        self.Bind(wx.EVT_TOOL, self.on_overlay_heatmap, id=ID_overlayMZfromList)
        self.Bind(wx.EVT_TOOL, self.on_overlay_mobiligram, id=ID_overlayMZfromList1D)
        self.Bind(wx.EVT_TOOL, self.on_overlay_chromatogram, id=ID_overlayMZfromListRT)
        self.Bind(wx.EVT_MENU, self.onCheckTool, id=ID_useProcessedCombinedMenu)
        self.Bind(wx.EVT_TOOL, self.onCheckTool, id=ID_ionPanel_addToDocument)
        self.Bind(wx.EVT_TOOL, self.onCheckTool, id=ID_ionPanel_normalize1D)
        self.Bind(wx.EVT_TOOL, self.onCheckTool, id=ID_ionPanel_automaticOverlay)
        
        menu = wx.Menu()
        self.addToDocument_check = menu.AppendCheckItem(ID_ionPanel_addToDocument, "Add overlay plots to document\tA",
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
              
    def onRemoveTool(self, evt):
        # Make bindings
        self.Bind(wx.EVT_MENU, self.OnDeleteAll, id=ID_ionPanel_delete_selected)
        self.Bind(wx.EVT_MENU, self.OnDeleteAll, id=ID_ionPanel_delete_all)
        self.Bind(wx.EVT_MENU, self.OnClearTable, id=ID_ionPanel_clear_all)
        self.Bind(wx.EVT_MENU, self.OnClearTable, id=ID_ionPanel_clear_selected)
        self.Bind(wx.EVT_MENU, self.onRemoveDuplicates, id=ID_removeDuplicatesTable)
        
        menu = wx.Menu()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_ionPanel_clear_all,
                                     text='Clear table', 
                                     bitmap=self.icons.iconsLib['clear_16']))
        menu.Append(ID_ionPanel_clear_selected, "Clear selected")
        menu.AppendSeparator()
        menu.Append(ID_removeDuplicatesTable, "Remove duplicates")
        menu.Append(ID_ionPanel_delete_selected, "Remove selected ions")
        menu.Append(ID_ionPanel_delete_all, "Remove all ions")
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def onProcessTool(self, evt):
        
        self.Bind(wx.EVT_MENU, self.presenter.onCombineCEvoltagesMultiple, id=ID_combineCEscansSelectedIons)
        self.Bind(wx.EVT_MENU, self.presenter.onCombineCEvoltagesMultiple, id=ID_combineCEscans)
        
        self.Bind(wx.EVT_MENU, self.presenter.onProcessMultipleIonsIons, id=ID_processSelectedIons)
        self.Bind(wx.EVT_MENU, self.presenter.onProcessMultipleIonsIons, id=ID_processAllIons)
        self.Bind(wx.EVT_MENU, self.presenter.onExtractMSforEachCollVoltage, id=ID_extractMSforCVs)
        
        self.Bind(wx.EVT_MENU, self.onCheckTool, id=ID_overrideCombinedMenu)
        self.Bind(wx.EVT_MENU, self.onCheckTool, id=ID_useInternalParamsCombinedMenu)
        self.Bind(wx.EVT_MENU, self.onCheckTool, id=ID_combinedCV_binMSCombinedMenu)
        
        menu = wx.Menu()
        menu.Append(ID_processSelectedIons, "Process selected ions")
        menu.Append(ID_processAllIons, "Process all ions")
        menu.AppendSeparator()
        self.override_check = menu.AppendCheckItem(ID_overrideCombinedMenu, "Overwrite results\tO",
                                                   help="When checked, any previous results for the selected item(s) will be overwritten based on the current parameters.")
        self.override_check.Check(self.config.overrideCombine)
        self.useInternalParams_check = menu.AppendCheckItem(ID_useInternalParamsCombinedMenu, "Use internal parameters\tI", 
                                                            help="When checked, collision voltage scans will be combined based on parameters present in the ORIGAMI document.")
        self.useInternalParams_check.Check(self.config.useInternalParamsCombine)
        menu.Append(ID_combineCEscansSelectedIons, "Combine collision voltages for selected ions (ORIGAMI)")
        menu.Append(ID_combineCEscans, "Combine collision voltages for all ions (ORIGAMI)\tAlt+C")
        menu.AppendSeparator()
        self.binCombinedCV_MS_check = menu.AppendCheckItem(ID_combinedCV_binMSCombinedMenu, "Bin mass spectra during extraction\tB", 
                                                            help="")
        self.binCombinedCV_MS_check.Check(self.config.binCVdata)
        menu.Append(ID_extractMSforCVs, "Extract mass spectra for each collision voltage (ORIGAMI)")


        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()
        
    def onSaveTool(self, evt):
        self.Bind(wx.EVT_MENU, self.OnSaveSelectedPeakList, id=ID_saveSelectIonListCSV)
        self.Bind(wx.EVT_MENU, self.OnSavePeakList, id=ID_saveIonListCSV)
        
        self.Bind(wx.EVT_MENU, self.onSaveAsData, id=ID_exportSeletedAsImage_ion)
        self.Bind(wx.EVT_MENU, self.onSaveAsData, id=ID_exportAllAsImage_ion)
        self.Bind(wx.EVT_MENU, self.onSaveAsData, id=ID_exportSelectedAsCSV_ion)
        self.Bind(wx.EVT_MENU, self.onSaveAsData, id=ID_exportAllAsCSV_ion)
        
        self.Bind(wx.EVT_MENU, self.onCheckTool, id=ID_processSaveMenu)
        
        saveImageLabel = ''.join(['Save all figures (.', self.config.imageFormat,')'])
        saveSelectedImageLabel = ''.join(['Save selected figure (.', self.config.imageFormat,')'])
        
        saveTextLabel = ''.join(['Save all 2D (', self.config.saveDelimiterTXT,' delimited)'])
        saveSelectedTextLabel = ''.join(['Save selected 2D (', self.config.saveDelimiterTXT,' delimited)'])
        
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
        
#     def onTableTool(self, evt):
#         self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_ionPanel_table_startMS)
#         self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_ionPanel_table_endMS)
#         self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_ionPanel_table_color)
#         self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_ionPanel_table_colormap)
#         self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_ionPanel_table_charge)
#         self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_ionPanel_table_intensity)
#         self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_ionPanel_table_document)
#         self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_ionPanel_table_alpha)
#         self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_ionPanel_table_mask)
#         self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_ionPanel_table_document)
#         self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_ionPanel_table_label)
#         self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_ionPanel_table_method)
#         self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_ionPanel_table_hideAll)
#         self.Bind(wx.EVT_MENU, self.onUpdateTable, id=ID_ionPanel_table_restoreAll)
#         
# 
#         menu = wx.Menu()
#         n = 0
#         self.table_start = menu.AppendCheckItem(ID_ionPanel_table_startMS, 'Table: Minimum m/z')
#         self.table_start.Check(self.config._peakListSettings[n]['show'])
#         n = n + 1
#         self.table_end = menu.AppendCheckItem(ID_ionPanel_table_endMS, 'Table: Maximum m/z')
#         self.table_end.Check(self.config._peakListSettings[n]['show'])
#         n = n + 1
#         self.table_charge = menu.AppendCheckItem(ID_ionPanel_table_charge, 'Table: Charge')
#         self.table_charge.Check(self.config._peakListSettings[n]['show'])
#         n = n + 1
#         self.table_intensity = menu.AppendCheckItem(ID_ionPanel_table_intensity, 'Table: Intensity')
#         self.table_intensity.Check(self.config._peakListSettings[n]['show'])
#         n = n + 1
#         self.table_color = menu.AppendCheckItem(ID_ionPanel_table_color, 'Table: Color')
#         self.table_color.Check(self.config._peakListSettings[n]['show'])
#         n = n + 1
#         self.table_colormap = menu.AppendCheckItem(ID_ionPanel_table_colormap, 'Table: Colormap')
#         self.table_colormap.Check(self.config._peakListSettings[n]['show'])
#         n = n + 1
#         self.table_alpha = menu.AppendCheckItem(ID_ionPanel_table_alpha, 'Table: Transparency')
#         self.table_alpha.Check(self.config._peakListSettings[n]['show'])
#         n = n + 1
#         self.table_mask = menu.AppendCheckItem(ID_ionPanel_table_mask, 'Table: Mask')
#         self.table_mask.Check(self.config._peakListSettings[n]['show'])
#         n = n + 1
#         self.table_label = menu.AppendCheckItem(ID_ionPanel_table_label, 'Table: Label')
#         self.table_label.Check(self.config._peakListSettings[n]['show'])
#         n = n + 1
#         self.table_method = menu.AppendCheckItem(ID_ionPanel_table_method, 'Table: Method')
#         self.table_method.Check(self.config._peakListSettings[n]['show'])
#         n = n + 1
#         self.table_document = menu.AppendCheckItem(ID_ionPanel_table_document, 'Table: Document')
#         self.table_document.Check(self.config._peakListSettings[n]['show'])
#         menu.AppendSeparator()
#         self.table_index = menu.AppendItem(makeMenuItem(parent=menu, id=ID_ionPanel_table_hideAll,
#                                      text='Table: Hide all', 
#                                      bitmap=self.icons.iconsLib['hide_table_16']))
#         self.table_index = menu.AppendItem(makeMenuItem(parent=menu, id=ID_ionPanel_table_restoreAll,
#                                      text='Table: Restore all', 
#                                      bitmap=self.icons.iconsLib['show_table_16']))
#         
#         self.PopupMenu(menu)
#         menu.Destroy()
#         self.SetFocus()
    
    def onCheckTool(self, evt):
        """ Check/uncheck menu item """
        
        evtID = evt.GetId()
        
        # check which event was triggered
        if evtID == ID_overrideCombinedMenu:
            self.config.overrideCombine = not self.config.overrideCombine
            args = ("Peak list panel: 'Override' combined IM-MS data was switched to %s" % self.config.overrideCombine, 4)
            self.presenter.onThreading(evt, args, action='updateStatusbar')
            
        if evtID == ID_useInternalParamsCombinedMenu:
            self.config.useInternalParamsCombine = not self.config.useInternalParamsCombine
            args = ("Peak list panel: 'Use internal parameters' was switched to  %s" % self.config.useInternalParamsCombine, 4)
            self.presenter.onThreading(evt, args, action='updateStatusbar')
            
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
                
    def onUpdateTable(self, evt):
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
        if col_check: col_width = self.config._peakListSettings[col_index]['width']
        else: col_width = 0
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
        
        if evt != None:
            evt.Skip()
    
    def onChangeParameter(self, evt):
        """ Iterate over list to assign charge state """
        
        rows = self.peaklist.GetItemCount()
        if rows == 0: return
        

        
        if evt.GetId() == ID_assignChargeStateIons:
            ask_kwargs = {'static_text':'Assign charge state to selected items.',
                          'value_text':"", 
                          'validator':'integer',
                          'keyword':'charge'}
        elif evt.GetId() == ID_assignAlphaIons:
            ask_kwargs = {'static_text':'Assign new transparency value to selected items \nTypical transparency values: 0.5\nRange 0-1',
                          'value_text':0.5, 
                          'validator':'float',
                          'keyword':'alpha'}
        elif evt.GetId() == ID_assignMaskIons:
            ask_kwargs = {'static_text':'Assign new mask value to selected items \nTypical mask values: 0.25\nRange 0-1',
                          'value_text':0.25, 
                          'validator':'float',
                          'keyword':'mask'}
        elif evt.GetId() == ID_assignMinThresholdIons:
            ask_kwargs = {'static_text':'Assign minimum threshold value to selected items \nTypical mask values: 0.0\nRange 0-1',
                          'value_text':0.0, 
                          'validator':'float',
                          'keyword':'min_threshold'}
        elif evt.GetId() == ID_assignMaxThresholdIons:
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
            if self.peaklist.IsChecked(index=row):
                itemInfo = self.OnGetItemInformation(row)            
                filename = itemInfo['document']
                selectedText = itemInfo['ionName']
                document = self.presenter.documentsDict[filename]
                if not ask_kwargs['keyword'] in ['min_threshold', 'max_threshold']:
                    self.peaklist.SetStringItem(index=row, 
                                                col=self.config.peaklistColNames[ask_kwargs['keyword']], 
                                                label=str(self.ask_value))
                
                if selectedText in document.IMS2Dions:
                    document.IMS2Dions[selectedText][ask_kwargs['keyword']] = self.ask_value
                if selectedText in document.IMS2DCombIons:
                    document.IMS2DCombIons[selectedText][ask_kwargs['keyword']] = self.ask_value
                if selectedText in document.IMS2DionsProcess:
                    document.IMS2DionsProcess[selectedText][ask_kwargs['keyword']] = self.ask_value
                if selectedText in document.IMSRTCombIons:
                    document.IMSRTCombIons[selectedText][ask_kwargs['keyword']] = self.ask_value
                # update document
                self.presenter.documentsDict[document.title] = document

    def onSaveAsData(self, evt):
        count = self.peaklist.GetItemCount()
        self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['2D'])
        for ion in range(count):
            if evt.GetId() == ID_exportAllAsCSV_ion or evt.GetId() == ID_exportAllAsImage_ion:
                pass
            else:
                if self.peaklist.IsChecked(index=ion): pass
                else: continue
            # Get names
            itemInfo = self.OnGetItemInformation(ion)       
            rangeName = itemInfo['ionName']
            filename = itemInfo['document']
            # Get data
            currentDocument = self.presenter.documentsDict[filename]
            
            # Check whether its ORIGAMI or MANUAL data type
            if currentDocument.dataType == 'Type: ORIGAMI':
                if currentDocument.gotCombinedExtractedIons == True:
                    data = currentDocument.IMS2DCombIons
                elif currentDocument.gotExtractedIons == True:
                    data = currentDocument.IMS2Dions
            elif currentDocument.dataType == 'Type: MANUAL':
                if currentDocument.gotCombinedExtractedIons == True:
                    data = currentDocument.IMS2DCombIons
            else: continue
            zvals, xvals, xlabel, yvals, ylabel, cmap = self.presenter.get2DdataFromDictionary(dictionary=data[rangeName],
                                                                                               dataType='plot', compact=False)
            if self.process:
                zvals = self.data_processing.on_process_2D(zvals=zvals, return_data=True)
#                 zvals = self.presenter.process2Ddata(zvals=zvals, return_data=True)
                
            # Save CSV
            if evt.GetId() == ID_exportAllAsCSV_ion or evt.GetId() == ID_exportSelectedAsCSV_ion:
                savename = ''.join([currentDocument.path,'/DT_2D_',rangeName, self.config.saveExtension])
                # Y-axis labels need a value for [0,0]
                yvals = insert(yvals, 0, 0) # array, index, value
                # Combine x-axis with data
                saveData = vstack((xvals, zvals))
                saveData = vstack((yvals, saveData.T))
                # Save 2D array
                saveAsText(filename=savename, 
                           data=saveData, 
                           format='%.2f',
                           delimiter=self.config.saveDelimiter,
                           header="")
            # Save Image
            elif evt.GetId() == ID_exportAllAsImage_ion or evt.GetId() == ID_exportSeletedAsImage_ion:
                saveFileName = 'DT_2D_'
                self.presenter.view.panelPlots.on_plot_2D(zvals, xvals, yvals, xlabel, ylabel, cmap, override=True)
                save_kwargs = {'image_name':"{}_{}".format(saveFileName, rangeName)}
                self.presenter.view.panelPlots.save_images(evt=ID_save2DImageDoc, **save_kwargs)
        self.presenter.onThreading(evt, ('Finished saving data', 4), action='updateStatusbar')
        
    def onRecalculateCombinedORIGAMI(self, evt):
        # Apply all fields for item
        self.onAnnotateItems(evt=None)
        # Check item to recalculate
        self.peaklist.CheckItem(self.currentItem, check=True)
        # Recalculate
        self.presenter.onCombineCEvoltagesMultiple(evt=evt)
        # Uncheck item
        self.peaklist.CheckItem(self.currentItem, check=False)

    def onCheckForDuplicates(self, mzStart=None, mzEnd=None):
        """
        Check whether the value being added is already present in the table
        """
        currentItems = self.peaklist.GetItemCount()-1
        while (currentItems >= 0):
            itemInfo = self.OnGetItemInformation(currentItems)
            if itemInfo['mzStart'] == mzStart and itemInfo['mzEnd'] == mzEnd:
                print('Ion already in the table')
                currentItems = 0
                return True
            else:
                currentItems-=1
        return False
        
    def OnGetColumnClick(self, evt):
        self.OnSortByColumn(column=evt.GetColumn())
     
    def OnSortByColumn(self, column):
        """
        Sort data in peaklist based on pressed column
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
        
        columns = self.peaklist.GetColumnCount()
        rows = self.peaklist.GetItemCount()
        
        tempData = []
        # Iterate over row and columns to get data
        for row in range(rows):
            tempRow = []
            for col in range(columns):
                item = self.peaklist.GetItem(itemId=row, col=col)
                tempRow.append(item.GetText())
            tempRow.append(self.peaklist.IsChecked(index=row))
            tempRow.append(self.peaklist.GetItemBackgroundColour(row))
            tempRow.append(self.peaklist.GetItemTextColour(row))
            tempData.append(tempRow)
            
        # Sort data
        tempData = natsorted(tempData, key=itemgetter(column), reverse=self.reverse)  
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
            
    def onRemoveDuplicates(self, evt, limitCols=False):
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
                item = self.peaklist.GetItem(itemId=row, col=col)
                #  We want to make sure certain columns are numbers
                if col in [self.config.peaklistColNames['start'], 
                           self.config.peaklistColNames['end'], 
                           self.config.peaklistColNames['intensity'], 
                           self.config.peaklistColNames['alpha'], 
                           self.config.peaklistColNames['mask']]:
                    itemData = str2num(item.GetText())
                    if itemData == None: itemData = 0
                    tempRow.append(itemData)
                elif col==self.config.peaklistColNames['charge']:
                    itemData = str2int(item.GetText())
                    if itemData == None: itemData = 0
                    tempRow.append(itemData)
                else:
                    tempRow.append(item.GetText())
            tempRow.append(self.peaklist.IsChecked(index=row))
            tempRow.append(self.peaklist.GetItemBackgroundColour(row))
            tempRow.append(self.peaklist.GetItemTextColour(row))
            tempData.append(tempRow)

        # Remove duplicates
        tempData = removeListDuplicates(input=tempData,
                                        columnsIn=['start', 'end', 'charge', 'intensity', 
                                        'color', 'colormap', 'alpha', 'mask', 
                                        'label', 'method', 'filename', 'check', 'rgb', 'font_color'],
                                         limitedCols=['start','end','filename'])     
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
            
        if evt is None: return
        else:
            evt.Skip()
          
    def on_check_duplicate(self, mz_min, mz_max, document):
        rows = self.peaklist.GetItemCount()
        
        for row in xrange(rows):
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
        itemInfo = self.OnGetItemInformation(self.currentItem)
        mzStart = itemInfo['mzStart']
        mzEnd = itemInfo['mzEnd']
        intensity = itemInfo['intensity']
        selectedItem = itemInfo['document']
        rangeName = itemInfo['ionName']

        # Check if data was extracted
        if selectedItem == '':
            dialogs.dlgBox(exceptionTitle='Extract data first', 
                           exceptionMsg= "Please extract data first",
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
        else: return
        
        if data == None:
            self.presenter.onThreading(evt, ("Please extract data before trying to view it", 4, 3), 
                                       action='updateStatusbar')
            if evt.GetId() == ID_ionPanel_show_zoom_in_MS:
                try: self.presenter.view.panelPlots.on_zoom_1D_x_axis(str2num(mzStart)-self.config.zoomWindowX, 
                                                                      str2num(mzEnd)+self.config.zoomWindowX, 
                                                                      set_page=True)
                except: pass
            return
                
        if evt.GetId() == ID_ionPanel_show_mobiligram:
            xvals = data[rangeName]['yvals'] # normally this would be the y-axis
            yvals = data[rangeName]['yvals1D']
            xlabels = data[rangeName]['ylabels'] # normally this would be x-axis label
            self.presenter.view.panelPlots.on_plot_1D(xvals, yvals, xlabels, set_page=True)
        
        elif evt.GetId() == ID_ionPanel_show_chromatogram:
            xvals = data[rangeName]['xvals']
            yvals = data[rangeName]['yvalsRT']
            xlabels = data[rangeName]['xlabels'] # normally this would be x-axis label
            self.presenter.view.panelPlots.on_plot_RT(xvals, yvals, xlabels, set_page=True)

        elif evt.GetId() == ID_ionPanel_show_zoom_in_MS:
            """
            This simply zooms in on an ion
            """
            if selectedItem != self.presenter.currentDoc:
                self.presenter.onThreading(evt, ("This ion belongs to different document", 4, 3), 
                                           action='updateStatusbar')
            startX = str2num(mzStart)-self.config.zoomWindowX
            endX = str2num(mzEnd)+self.config.zoomWindowX
            try: endY = str2num(intensity)/100
            except TypeError: endY = 1.001
            if endY == 0: endY = 1.001
            try: self.presenter.view.panelPlots.on_zoom_1D(startX=startX,endX=endX, endY=endY, set_page=True)
            except AttributeError:
                self.presenter.onThreading(evt, ("Failed to zoom-in on the ion. Please replot the mass spectrum and try again.", 4, 3), 
                                           action='updateStatusbar')
                return
            
        else:
            # Unpack data
            zvals, xvals, xlabel, yvals, ylabel, cmap = self.presenter.get2DdataFromDictionary(dictionary=data[rangeName],
                                                                                               dataType='plot',compact=False)
            
            # Warning in case  there is missing data
            if isempty(xvals) or isempty(yvals) or xvals is "" or yvals is "":
                msg = "Missing x/y-axis labels. Cannot continue! \nAdd x/y-axis labels to each file before continuing."
                print(msg)
                dialogs.dlgBox(exceptionTitle='Missing data', 
                               exceptionMsg= msg,
                               type="Error")
                return
            # Process data
            if evt.GetId() == ID_ionPanel_show_process_heatmap:
                zvals = self.data_processing.on_process_2D(zvals=zvals, return_data=True)
            # Plot data
            self.presenter.view.panelPlots.on_plot_2D(zvals, xvals, yvals, xlabel, ylabel, cmap, override=True, set_page=True)
                        
    def OnDeleteAll(self, evt, ticked=False, selected=False, itemID=None):
        """ 
        This function removes selected or all text documents
        """
        if evt.GetId() == ID_ionPanel_delete_selected:
            currentItems = self.peaklist.GetItemCount()-1
            while (currentItems >= 0):
                if self.peaklist.IsChecked(index=currentItems):
                    itemInfo = self.OnGetItemInformation(itemID=currentItems)
                    msg = "Deleted {} from {}".format(itemInfo['ionName'], itemInfo['document'])
                    self.presenter.onThreading(evt, (msg, 4, 3), action='updateStatusbar')
                    try: 
                        del self.presenter.documentsDict[itemInfo['document']].IMS2Dions[itemInfo['ionName']]
                        if len(self.presenter.documentsDict[itemInfo['document']].IMS2Dions.keys()) == 0: 
                            self.presenter.documentsDict[itemInfo['document']].gotExtractedIons = False
                    except KeyError: pass
                    try: 
                        del self.presenter.documentsDict[itemInfo['document']].IMS2DionsProcess[itemInfo['ionName']]
                        if len(self.presenter.documentsDict[itemInfo['document']].IMS2DionsProcess.keys()) == 0: 
                            self.presenter.documentsDict[itemInfo['document']].got2DprocessIons = False
                    except KeyError: pass
                    try: 
                        del self.presenter.documentsDict[itemInfo['document']].IMSRTCombIons[itemInfo['ionName']]
                        if len(self.presenter.documentsDict[itemInfo['document']].IMSRTCombIons.keys()) == 0: 
                            self.presenter.documentsDict[itemInfo['document']].gotCombinedExtractedIonsRT = False
                    except KeyError: pass
                    try: 
                        del self.presenter.documentsDict[itemInfo['document']].IMS2DCombIons[itemInfo['ionName']]
                        if len(self.presenter.documentsDict[itemInfo['document']].IMS2DCombIons.keys()) == 0: 
                            self.presenter.documentsDict[itemInfo['document']].gotCombinedExtractedIons = False
                    except KeyError: pass
                    self.peaklist.DeleteItem(currentItems)
                    # update document
                    try: self.presenter.OnUpdateDocument(self.presenter.documentsDict[itemInfo['document']], expand_item='ions')
                    except KeyError: pass
                currentItems-=1
                    
        elif evt.GetId() == ID_ionPanel_delete_rightClick:
            itemInfo = self.OnGetItemInformation(itemID=self.currentItem)
            msg = "Deleted {} from {}".format(itemInfo['ionName'], itemInfo['document'])
            self.presenter.onThreading(evt, (msg, 4, 3), action='updateStatusbar')
            itemID= [itemInfo['document'], itemInfo['ionName'], self.currentItem]
            if itemID != None:
                msg = "Deleted {} from {}".format(itemInfo['ionName'], itemInfo['document'])
                self.presenter.onThreading(evt, (msg, 4, 3), action='updateStatusbar')
                # Delete selected document from dictionary + table   
                try: 
                    del self.presenter.documentsDict[itemInfo['document']].IMS2Dions[itemInfo['ionName']]
                    if len(self.presenter.documentsDict[itemInfo['document']].IMS2Dions.keys()) == 0: 
                        self.presenter.documentsDict[itemInfo['document']].gotExtractedIons = False
                except KeyError: pass
                try: 
                    del self.presenter.documentsDict[itemInfo['document']].IMS2DionsProcess[itemInfo['ionName']]
                    if len(self.presenter.documentsDict[itemInfo['document']].IMS2DionsProcess.keys()) == 0: 
                        self.presenter.documentsDict[itemInfo['document']].got2DprocessIons = False
                except KeyError: pass
                try: 
                    del self.presenter.documentsDict[itemInfo['document']].IMSRTCombIons[itemInfo['ionName']]
                    if len(self.presenter.documentsDict[itemInfo['document']].IMSRTCombIons.keys()) == 0: 
                        self.presenter.documentsDict[itemInfo['document']].gotCombinedExtractedIonsRT = False
                except KeyError: pass
                try: 
                    del self.presenter.documentsDict[itemInfo['document']].IMS2DCombIons[itemInfo['ionName']]
                    if len(self.presenter.documentsDict[itemInfo['document']].IMS2DCombIons.keys()) == 0: 
                        self.presenter.documentsDict[itemInfo['document']].gotCombinedExtractedIons = False
                except KeyError: pass
                self.peaklist.DeleteItem(self.currentItem)
                # update document
                try: self.presenter.OnUpdateDocument(self.presenter.documentsDict[itemInfo['document']], expand_item='ions')
                except KeyError: pass
             
             
   
        else:
        # Ask if you are sure to delete it!
            dlg = dialogs.dlgBox(exceptionTitle='Are you sure?', 
                                 exceptionMsg= "Are you sure you would like to delete ALL ions?",
                                 type="Question")
            if dlg == wx.ID_NO:
                self.presenter.onThreading(evt, ("Cancelled operation", 4, 3), action='updateStatusbar') 
                return
            else:
                currentItems = self.peaklist.GetItemCount()-1
                while (currentItems >= 0):
                    itemInfo = self.OnGetItemInformation(itemID=currentItems)
                    msg = "Deleted {} from {}".format(itemInfo['ionName'], itemInfo['document'])
                    self.presenter.onThreading(evt, (msg, 4, 3), action='updateStatusbar')
                    try: 
                        del self.presenter.documentsDict[itemInfo['document']].IMS2Dions[itemInfo['ionName']]
                        if len(self.presenter.documentsDict[itemInfo['document']].IMS2Dions.keys()) == 0: 
                            self.presenter.documentsDict[itemInfo['document']].gotExtractedIons = False
                    except KeyError: pass
                    try: 
                        del self.presenter.documentsDict[itemInfo['document']].IMS2DionsProcess[itemInfo['ionName']]
                        if len(self.presenter.documentsDict[itemInfo['document']].IMS2DionsProcess.keys()) == 0: 
                            self.presenter.documentsDict[itemInfo['document']].got2DprocessIons = False
                    except KeyError: pass
                    try: 
                        del self.presenter.documentsDict[itemInfo['document']].IMSRTCombIons[itemInfo['ionName']]
                        if len(self.presenter.documentsDict[itemInfo['document']].IMSRTCombIons.keys()) == 0: 
                            self.presenter.documentsDict[itemInfo['document']].gotCombinedExtractedIonsRT = False
                    except KeyError: pass
                    try: 
                        del self.presenter.documentsDict[itemInfo['document']].IMS2DCombIons[itemInfo['ionName']]
                        if len(self.presenter.documentsDict[itemInfo['document']].IMS2DCombIons.keys()) == 0: 
                            self.presenter.documentsDict[itemInfo['document']].gotCombinedExtractedIons = False
                    except KeyError: pass
                    self.peaklist.DeleteItem(currentItems)
                    # update document
                    try: self.presenter.OnUpdateDocument(self.presenter.documentsDict[itemInfo['document']], expand_item='ions')
                    except KeyError: pass
                    self.peaklist.DeleteItem(currentItems)
                    currentItems-=1
                    
        self.on_replot_patch_on_MS(evt=None)
            
    def OnSavePeakList(self, evt):
        """
        Save data in CSV format
        """
        columns = self.peaklist.GetColumnCount()
        rows = self.peaklist.GetItemCount()
#         tempData = ['start m/z, end m/z, z, color, alpha, filename, method, intensity, label']
        tempData = []
        if rows == 0: return
        # Ask for a name and path
        saveDlg = wx.FileDialog(self, "Save peak list to file...", "", "",
                                "Comma delimited file (*.csv)|*.csv",
                                wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if saveDlg.ShowModal() == wx.ID_CANCEL: return
        else:
            filepath = saveDlg.GetPath()
#             print(filepath)

        # Iterate over row and columns to get data
        for row in range(rows):
            tempRow = []
            for col in range(columns):
                item = self.peaklist.GetItem(itemId=row, col=col)
                #  We want to make sure the first 3 columns are numbers
                if col==0 or col==1 or col==2:
                    itemData = str2num(item.GetText())
                    if itemData == None: itemData = 0
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
        
    def OnClearTable(self, evt):
        """
        This function clears the table without deleting any items from the document tree
        """
        evtID = evt.GetId()
        
        if evtID == ID_ionPanel_clear_selected:
            row = self.peaklist.GetItemCount() - 1
            while (row >= 0):
                if self.peaklist.IsChecked(index=row):
                    self.peaklist.DeleteItem(row)
                row-=1
        else:
            # Ask if you want to delete all items
            dlg = dialogs.dlgBox(exceptionTitle='Are you sure?', 
                                 exceptionMsg= "Are you sure you would like to clear the table?",
                                 type="Question")
            if dlg == wx.ID_NO:
                self.presenter.onThreading(evt, ('Cancelled operation', 4), action='updateStatusbar')
                return
            self.peaklist.DeleteAllItems()
            
        self.on_replot_patch_on_MS(evt=None)
        
    def onDuplicateIons(self, evt):
        
        # Create a list of keys in the dictionary
        keyList = []
        if len(self.presenter.documentsDict) == 0: 
            self.presenter.onThreading(None, ('There are no documents to copy peaks to!', 4), action='updateStatusbar')
            return
        elif self.peaklist.GetItemCount() == 0: 
            self.presenter.onThreading(None, ('There are no peaks in the table. Try adding some first!', 4), action='updateStatusbar')
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
        
        checkData = [mzStart, mzEnd, filename]
        
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
        
        # get item information
        information = {'mzStart':str2num(self.peaklist.GetItem(itemID, self.config.peaklistColNames['start']).GetText()),
                       'mzEnd':str2num(self.peaklist.GetItem(itemID, self.config.peaklistColNames['end']).GetText()),
                       'intensity':str2num(self.peaklist.GetItem(itemID, self.config.peaklistColNames['intensity']).GetText()),
                       'charge':str2int(self.peaklist.GetItem(itemID, self.config.peaklistColNames['charge']).GetText()),
                       'color':self.peaklist.GetItemBackgroundColour(item=itemID),
                       'color_255to1':convertRGB255to1(self.peaklist.GetItemBackgroundColour(item=itemID), decimals=3),
                       'colormap':self.peaklist.GetItem(itemID, self.config.peaklistColNames['colormap']).GetText(),
                       'alpha':str2num(self.peaklist.GetItem(itemID, self.config.peaklistColNames['alpha']).GetText()),
                       'mask':str2num(self.peaklist.GetItem(itemID, self.config.peaklistColNames['mask']).GetText()),
                       'document':self.peaklist.GetItem(itemID, self.config.peaklistColNames['filename']).GetText(),
                       'method':self.peaklist.GetItem(itemID, self.config.peaklistColNames['method']).GetText(),
                       'label':self.peaklist.GetItem(itemID, self.config.peaklistColNames['label']).GetText(),
                       'select':self.peaklist.IsChecked(itemID),
                       'id':itemID}
        information['ionName'] = "%s-%s" % (information['mzStart'], information['mzEnd']) 
        
        try:
            self.docs = self.presenter.documentsDict[self.peaklist.GetItem(itemID, self.config.peaklistColNames['filename']).GetText()]
        except KeyError:
            pass
        # check whether the ion has any previous information
        min_threshold, max_threshold = 0, 1
        try:
            if information['ionName'] in self.docs.IMS2Dions:
                min_threshold = self.docs.IMS2Dions[information['ionName']].get('min_threshold', 0)
                max_threshold = self.docs.IMS2Dions[information['ionName']].get('max_threshold', 1)
        except AttributeError: pass
        
        information['min_threshold'] = min_threshold
        information['max_threshold'] = max_threshold
        
        # Check whether the ion has combined ions
        parameters = None
        if hasattr(self.docs, 'gotCombinedExtractedIons'):
            try:
                parameters = self.docs.IMS2DCombIons[information['ionName']].get('parameters', None)
            except KeyError: 
                pass
        information['parameters'] = parameters
        
        if return_list:
            mzStart = information['mzStart']
            mzEnd = information['mzEnd']
            charge = information['charge']
            color = information['color']
            colormap = information['colormap']
            alpha = information['alpha']
            mask = information['mask']
            label = information['label']
            document = information['document']
            ionName = information['ionName']
            min_threshold = information['min_threshold']
            max_threshold = information['max_threshold']
            return mzStart, mzEnd, charge, color, colormap, alpha, mask, label, document, ionName, min_threshold, max_threshold

        return information
    # ----
    
    def OnGetValue(self, value_type='color'):
        information = self.OnGetItemInformation(self.currentItem)
        
        if value_type == 'mzStart':
            return information['mzStart']
        elif value_type == 'mzEnd':
            return information['mzEnd']
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
    # ----
    def OnSetValue(self, value=None, value_type=None):
        itemID = self.peaklist.GetItemCount()-1
        
        if value_type == 'mzStart':
            self.peaklist.SetStringItem(itemID, 0, str(value_type))
        elif value_type == 'mzEnd':
            self.peaklist.SetStringItem(itemID, 1, str(value_type))
        elif value_type == 'charge':
            self.peaklist.SetStringItem(itemID, 2, str(value_type))
        elif value_type == 'intensity':
            self.peaklist.SetStringItem(itemID, 3, str(value_type))
        elif value_type == 'color_text':
            self.peaklist.SetItemBackgroundColour(itemID, value)
            self.peaklist.SetStringItem(itemID, 4, str(value))
            self.peaklist.SetItemTextColour(itemID, determineFontColor(value, return_rgb=True))
        elif value_type == 'colormap':
            self.peaklist.SetStringItem(itemID, 5, str(value_type))
        elif value_type == 'alpha':
            self.peaklist.SetStringItem(itemID, 6, str(value_type))
        elif value_type == 'mask':
            self.peaklist.SetStringItem(itemID, 7, str(value_type))
        elif value_type == 'label':
            self.peaklist.SetStringItem(itemID, 8, str(value_type))
        elif value_type == 'method':
            self.peaklist.SetStringItem(itemID, 9, str(value_type))
        elif value_type == 'document':
            self.peaklist.SetStringItem(itemID, 10, str(value_type))
    # ----
    def OnOpenEditor(self, evt):
        
        if evt == None: 
            evtID = ID_ionPanel_editItem
        else:
            evtID = evt.GetId()

        rows = self.peaklist.GetItemCount() - 1
        if evtID == ID_ionPanel_editItem:
            if self.currentItem  < 0:
                print('Please select item in the table first.')
                return
            dlg_kwargs = self.OnGetItemInformation(self.currentItem)
            
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
                                  'id':rows
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
                              'id':row
                              }
                 
                self.editItemDlg = panelModifyIonSettings(self, 
                                                          self.presenter, 
                                                          self.config,
                                                          **dlg_kwargs)
                self.editItemDlg.Show()
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
            self.peaklist.SetStringItem(self.currentItem, 
                                        self.config.peaklistColNames['color'], 
                                        str(convertRGB255to1(newColour)))
            self.peaklist.SetItemBackgroundColour(self.currentItem, newColour)
            self.peaklist.SetItemTextColour(self.currentItem, determineFontColor(newColour, return_rgb=True))
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
            self.peaklist.SetStringItem(self.currentItem, 
                                        self.config.peaklistColNames['color'], 
                                        str(convertRGB255to1(newColour)))
            self.peaklist.SetItemBackgroundColour(self.currentItem, newColour)
            self.peaklist.SetItemTextColour(self.currentItem, determineFontColor(newColour, return_rgb=True))
            if give_value:
                return newColour
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
    
    def onChangeColormap(self, evt):
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
                self.currentItem = row
                colormap = colormaps[row]
                self.peaklist.SetStringItem(row, 
                                            self.config.peaklistColNames['colormap'], 
                                            str(colormap))
                
                # update document
                try:
                    self.onUpdateDocument(evt=None)
                except TypeError:
                    print("Please select item")
        
    def onChangeColorBatch(self, evt):
        # get number of checked items
        check_count = 0
        for row in range(self.peaklist.GetItemCount()):
            if self.peaklist.IsChecked(index=row):
                check_count += 1 
                
        if evt.GetId() == ID_ionPanel_changeColorBatch_palette:
            colors = self.presenter.view.panelPlots.onChangePalette(None, n_colors=check_count, return_colors=True)
        elif evt.GetId() == ID_ionPanel_changeColorBatch_color:
            color = self.OnGetColor(None)
            colors = [color] * check_count
        else:
            colors = self.presenter.view.panelPlots.onGetColormapList(n_colors=check_count)
        
        check_count = 0
        for row in range(self.peaklist.GetItemCount()):
            if self.peaklist.IsChecked(index=row):
                self.currentItem = row
                color = colors[check_count]
                self.peaklist.SetStringItem(row, self.config.peaklistColNames['color'], 
                                            str(color))
                self.peaklist.SetItemBackgroundColour(row, convertRGB1to255(color))
                self.peaklist.SetItemTextColour(self.currentItem, determineFontColor(convertRGB1to255(color), return_rgb=True))
                check_count += 1
                
            # update document
            try:
                self.onUpdateDocument(evt=None)
            except TypeError:
                print("Please select item")
    # ----
    def onUpdateDocument(self, evt, itemInfo=None):
        
        # get item info
        if itemInfo == None:
            itemInfo = self.OnGetItemInformation(self.currentItem)
        
        # get item
        document = self.presenter.documentsDict[itemInfo['document']]
        
        processed_name = "{} (processed)".format(itemInfo['ionName'])
        keywords = ['color', 'colormap', 'alpha', 'mask', 'label', 'min_threshold',
                    'max_threshold', 'charge']
        if itemInfo['ionName'] in document.IMS2Dions:
            for keyword in keywords:
                if keyword == 'colormap': keyword_name = 'cmap'
                else: keyword_name = keyword
                document.IMS2Dions[itemInfo['ionName']][keyword_name] = itemInfo[keyword]
                try: document.IMS2Dions[processed_name][keyword_name] = itemInfo[keyword]
                except: pass  
                
        if itemInfo['ionName'] in document.IMS2DCombIons:
            for keyword in keywords:
                if keyword == 'colormap': keyword_name = 'cmap'
                else: keyword_name = keyword
                document.IMS2DCombIons[itemInfo['ionName']][keyword_name] = itemInfo[keyword]
                try: document.IMS2DCombIons[processed_name][keyword_name] = itemInfo[keyword]
                except: pass  
                
        if itemInfo['ionName'] in document.IMS2DionsProcess:
            for keyword in keywords:
                if keyword == 'colormap': keyword_name = 'cmap'
                else: keyword_name = keyword
                document.IMS2DionsProcess[itemInfo['ionName']][keyword_name] = itemInfo[keyword]
                try: document.IMS2DionsProcess[processed_name][keyword_name] = itemInfo[keyword]
                except: pass  
                
        if itemInfo['ionName'] in document.IMSRTCombIons:
            for keyword in keywords:
                if keyword == 'colormap': 
                    keyword_name = 'cmap'
                    itemInfo['colormap'] = convertRGB255to1(itemInfo['color']) 
                else: keyword_name = keyword
                document.IMSRTCombIons[itemInfo['ionName']][keyword_name] = itemInfo[keyword]
                try: document.IMSRTCombIons[processed_name][keyword_name] = itemInfo[keyword]
                except: pass  
        
        # Update file list
        self.presenter.OnUpdateDocument(document, 'no_refresh')

    def onClearItems(self, document):
        """
        @param document: title of the document to be removed from the list
        """
        row = self.peaklist.GetItemCount() - 1
        while (row >= 0):
            info = self.OnGetItemInformation(itemID=row)
            if info['document'] == document:
                self.peaklist.DeleteItem(row)
                row-=1
            else:
                row-=1
        
    def onOpenPeakList(self, evt):
        """
        This function opens a formatted CSV file with peaks
        """
        dlg = wx.FileDialog(self.presenter.view, "Choose a text file (m/z, window size, charge):", 
                            wildcard = "*.csv;*.txt",
                            style=wx.FD_DEFAULT_STYLE | wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_CANCEL: return
        else:
            
            manual = self.presenter.checkIfAnyDocumentsAreOfType(type='Type: MANUAL') 
            origami = self.presenter.checkIfAnyDocumentsAreOfType(type='Type: ORIGAMI') 
            infrared = self.presenter.checkIfAnyDocumentsAreOfType(type='Type: Infrared')
            docList = manual + origami + infrared 
            if len(docList) == 0: 
                args = ("Please create open or create a new document which can extract MS/IM-MS data", 4, 5)
                self.presenter.onThreading(evt, args, action='updateStatusbar')
                return
            elif len(docList) == 1: document_title = docList[0]
            else:
                document_panel = dialogs.panelSelectDocument(self.presenter.view, self.presenter, docList, False)
                if document_panel.ShowModal() == wx.ID_OK: 
                    pass
                
                document_title = document_panel.current_document
                if document_title == None:
                    return
        
            # Create shortcut                
            delimiter, __ = checkExtension(input=dlg.GetPath().encode('ascii', 'replace') )
            peaklist = read_csv(dlg.GetPath(), delimiter=delimiter)
            peaklist = peaklist.fillna("")
            print(peaklist)
            columns = peaklist.columns.values.tolist()
            for min_name in ["min", "min m/z"]:
                if min_name in columns: 
                    break
                else: continue
            if min_name not in columns: min_name = None
                
            for max_name in ["max", "max m/z"]:
                if max_name in columns: 
                    break
                else: continue
            if max_name not in columns: max_name = None
            
            for charge_name in ["z", "charge"]:
                if charge_name in columns: 
                    break
                else: continue
            if charge_name not in columns: charge_name = None
                
            for label_name in ["label", "information"]:
                if label_name in columns: 
                    break
                else: continue
            if label_name not in columns: label_name = None
            
            for color_name in ["color", "colour"]:
                if color_name in columns: 
                    break
                else: continue
            if color_name not in columns: color_name = None
            
            if min_name is None or max_name is None:
                return
            
            # get colorlist beforehand
            count = self.peaklist.GetItemCount() + len(peaklist)
            colors = self.presenter.view.panelPlots.onChangePalette(None, n_colors=count+1, return_colors=True)
            
            # iterate
            for peak in xrange(len(peaklist)):
                print(peak)
                min_value = peaklist[min_name][peak]
                max_value = peaklist[max_name][peak]
                 
                if charge_name is not None: charge_value = peaklist[charge_name][peak]
                else: charge_value = ""
                 
                if label_name is not None: label_value = peaklist[label_name][peak]
                else: label_value = "" 
 
                if color_name is not None: 
                    color_value = peaklist[color_name][peak]
                    try: color_value = literal_eval(color_value)
                    except:pass
                else: color_value = colors[peak]

                self.peaklist.Append([str(min_value), 
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
                    self.peaklist.SetItemBackgroundColour(self.peaklist.GetItemCount()-1,
                                                          color_value)
                    self.peaklist.SetItemTextColour(self.peaklist.GetItemCount()-1,
                                                    determineFontColor(color_value, return_rgb=True))
                except: pass
            self.presenter.view.onPaneOnOff(evt=ID_window_ionList, check=True)
            dlg.Destroy()
     
    def on_check_selected(self, evt):
        """
        Check current item when letter S is pressed on the keyboard
        """
        check = not self.peaklist.IsChecked(index=self.currentItem)
        self.peaklist.CheckItem(self.currentItem, check=check)
                
    def on_add_blank_document_overlay(self, evt):
        self.presenter.onAddBlankDocument(evt=None, document_type='overlay')
                
    def on_extract_all(self, evt): 
        self.presenter.on_extract_2D_from_mass_range_threaded(None, extract_type="all")
    
    def on_extract_selected(self, evt): 
        self.presenter.on_extract_2D_from_mass_range_threaded(None, extract_type="selected")
    
    def on_extract_new(self, evt): 
        self.presenter.on_extract_2D_from_mass_range_threaded(None, extract_type="new")
      
    def on_overlay_mobiligram(self, evt):
        self.presenter.on_overlay_1D(source="ion", plot_type="mobiligram")
    
    def on_overlay_chromatogram(self, evt):
        self.presenter.on_overlay_1D(source="ion", plot_type="chromatogram")
        
    def on_overlay_heatmap(self, evt):
        self.presenter.on_overlay_2D(source="ion") 
            
    def on_add_to_table(self, add_dict, check_color=True):
        
        # get color
        color = add_dict.get("color", self.config.customColors[randomIntegerGenerator(0,15)])
        # check for duplicate color
        if check_color:
            color = self.on_check_duplicate_colors(color)
        
        
        
        # add to peaklist
        self.peaklist.Append([str(add_dict.get("mz_start", "")), 
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
        self.peaklist.SetItemBackgroundColour(self.peaklist.GetItemCount()-1,
                                              color)
        
        self.peaklist.SetItemTextColour(self.peaklist.GetItemCount()-1,
                                        determineFontColor(color, return_rgb=True))
    
    def on_check_duplicate_colors(self, new_color):
        """ 
        Check whether newly assigned color is already in the table and if so, 
        return a different one
        """
        count = self.peaklist.GetItemCount()
        color_list = []
        for row in xrange(count):
            color_list.append(self.peaklist.GetItemBackgroundColour(item=row))
        
        if new_color in color_list:
            counter = len(self.config.customColors)-1
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
        if currentDoc == "Current documents" or currentDoc == None: 
            return
        document = self.presenter.documentsDict[currentDoc]
        
        # Replot RT for current document
        msX = document.massSpectrum['xvals']
        msY = document.massSpectrum['yvals']
        try: xlimits = document.massSpectrum['xlimits']
        except KeyError: 
            xlimits = [document.parameters['startMS'],document.parameters['endMS']]
        # Change panel and plot 
        self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['MS'])
        
        if not self.presenter.view.panelPlots._on_check_plot_names(document.title, "Mass Spectrum", "MS"):
            name_kwargs = {"document":document.title, "dataset": "Mass Spectrum"}
            self.presenter.view.panelPlots.on_plot_MS(msX, msY, xlimits=xlimits, replot=True,
                                                      set_page=True, **name_kwargs)
            
        if count == 0: 
            self.presenter.view.panelPlots.on_clear_patches(plot="MS", repaint=True)
            return
        
        ymin, height = 0, 100000000000
        last = self.peaklist.GetItemCount()-1
        self.presenter.view.panelPlots.on_clear_patches(plot="MS", repaint=False)
        # Iterate over the list and plot rectangle one by one
        for row in range(count):
            itemInfo = self.OnGetItemInformation(itemID=row)
            xmin = itemInfo['mzStart']
            xmax = itemInfo['mzEnd']
            color = itemInfo['color_255to1']
            width = xmax-xmin
            if row == last:
                self.presenter.view.panelPlots.on_plot_patches(xmin, ymin, width, height, color=color, 
                                                               alpha=self.config.markerTransparency_1D, plot="MS",
                                                               repaint=True)
            else:
                self.presenter.view.panelPlots.on_plot_patches(xmin, ymin, width, height, color=color, 
                                                               alpha=self.config.markerTransparency_1D, plot="MS",
                                                               repaint=False)
     
    def on_delete_item(self, mz_start, mz_end, document):
        row = self.findItem(mz_start, mz_end, document)
        if row is not None:
            self.peaklist.DeleteItem(row)
        
                
class panelExportData(wx.MiniFrame):
    """
    Export data from table
    """
    
    def __init__(self, parent, icons):
        wx.MiniFrame.__init__(self, parent ,-1, 'Export', size=(400, 300), 
                              style=wx.DEFAULT_FRAME_STYLE & ~ 
                              (wx.RESIZE_BORDER | wx.RESIZE_BOX | wx.MAXIMIZE_BOX))

        self.parent = parent
        self.icons = icons
    
        # make gui items
        self.makeGUI()
        wx.EVT_CLOSE(self, self.onClose)

    def makeGUI(self):
               
        # make panel
        peaklist = self.makePeaklistPanel()
        gauge = self.makeGaugePanel()
        
        # pack element
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(peaklist, 0, wx.EXPAND, 0)
        self.mainSizer.Add(gauge, 0, wx.EXPAND, 0)

        
        # fit layout
        self.mainSizer.Fit(self)
        self.SetSizer(self.mainSizer)
        self.Center()

    def onClose(self, evt):
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
        grid1.Add(self.peaklistColstartMZ_check, (0,0))
        grid1.Add(self.peaklistColendMZ_check, (1,0))
        grid1.Add(self.peaklistColCharge_check, (2,0))
        grid1.Add(self.peaklistColFilename_check, (0,2))
        grid1.Add(self.peaklistColMethod_check, (1,2))
        grid1.Add(self.peaklistColRelIntensity_check, (2,2))
        
        grid2 = wx.GridBagSizer(GRIDBAG_VSPACE, GRIDBAG_HSPACE)
#         grid2.Add(peaklistSelect_label, (0,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
#         grid2.Add(self.peaklistSelect_choice, (0,1))
        grid2.Add(peaklistFormat_label, (1,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid2.Add(self.peaklistFormat_choice, (1,1))
        grid2.Add(peaklistSeparator_label, (2,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid2.Add(self.peaklistSeparator_choice, (2,1))
        
        grid2.Add(self.exportBtn, (3,0))
        
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(grid1, 0, wx.ALIGN_CENTER|wx.ALL, PANEL_SPACE_MAIN)
        mainSizer.Add(grid2, 0, wx.ALIGN_CENTER|wx.ALL, PANEL_SPACE_MAIN)
        
        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)
        
        self.exportBtn.Bind(wx.EVT_BUTTON, self.onExportFile)
        
        
        return panel

    def onExportParameters(self):
        choicesData = {0:'ASCII', 1:'ASCII with Headers'}
        choicesDelimiter = {0:',', 1:';', 2:'tab'}
        
        self.useStartMZ = self.peaklistColstartMZ_check.GetValue()
        self.useEndMZ = self.peaklistColendMZ_check.GetValue()
        self.useCharge = self.peaklistColCharge_check.GetValue()
        self.useFilename = self.peaklistColFilename_check.GetValue()
        self.useMethod= self.peaklistColMethod_check.GetValue()
        self.useRelIntensity = self.peaklistColRelIntensity_check.GetValue()
        
        self.dataChoice = choicesData[self.peaklistFormat_choice.GetSelection()]
        self.delimiter = choicesDelimiter[self.peaklistSeparator_choice.GetSelection()]
          
    def onExportFile(self, evt):
         
        fileName = 'peaklist.txt'
        fileType = "ASCII file|*.txt"
        
        self.onExportParameters()
        
        dlg =  wx.FileDialog(self, "Save peak list to file...", "", "", fileType,
                                wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            dlg.Destroy()
        else:
            dlg.Destroy()
            return

    def makeGaugePanel(self):
        """Make processing gauge."""
        
        panel = wx.Panel(self, -1)
        
        # make elements
        self.gauge = gauge(panel, -1)
        
        # pack elements
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(self.gauge, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 10)
        
        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)
        
        return panel
    # ----

class panelDuplicateIons(wx.MiniFrame):
    """
    Duplicate ions
    """
    
    def __init__(self, parent, keyList):
        wx.MiniFrame.__init__(self, parent ,-1, 'Duplicate...', size=(400, 300), 
                              style=wx.DEFAULT_FRAME_STYLE & ~ 
                              (wx.RESIZE_BORDER | wx.RESIZE_BOX | wx.MAXIMIZE_BOX))

        self.parent = parent
        self.duplicateList = keyList
    
        # make gui items
        self.makeGUI()
        
        wx.EVT_CLOSE(self, self.onClose)

    def onClose(self, evt):
        """Destroy this frame."""
        
        self.Destroy()
    # ----
    
    def makeGUI(self):
               
        # make panel
        panel = self.makeDuplicatePanel()
        
        # pack element
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(panel, 0, wx.EXPAND, 0)
        
        # bind
        self.okBtn.Bind(wx.EVT_BUTTON, self.onDuplicate)
        self.cancelBtn.Bind(wx.EVT_BUTTON, self.onClose)
        
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

        grid.Add(selection_label, (0,0))
        grid.Add(self.all_radio, (0,1), wx.GBSpan(1,1))
        grid.Add(self.selected_radio, (0,2), wx.GBSpan(1,1))
        
        
        
        grid.Add(duplicateFrom_label, (1,0))
        grid.Add(self.documentListFrom_choice, (1,1), wx.GBSpan(1,2))
        
        grid.Add(duplicateTo_label, (2,0))
        grid.Add(self.documentListTo_choice, (2,1), wx.GBSpan(1,2))
        
        grid.Add(self.okBtn, (3,1), wx.GBSpan(1,1))
        grid.Add(self.cancelBtn, (3,2), wx.GBSpan(1,1))

        mainSizer.Add(grid, 0, wx.ALIGN_CENTER|wx.ALL, PANEL_SPACE_MAIN)
        
        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)

        return panel

    def onDuplicate(self, evt):
        # Which ions to duplicate
        if self.all_radio.GetValue(): duplicateWhich = 'all'
        else: duplicateWhich = 'selected'
        
        # How many in the list
        
        rows = self.parent.peaklist.GetItemCount()
        columns = 3 # start, end, z
        
        # Which from and to which
        docFrom = self.documentListFrom_choice.GetStringSelection()
        docTo = self.documentListTo_choice.GetStringSelection()

        tempData = []
        if duplicateWhich == 'all':
            for i in range(1,self.documentListTo_choice.GetCount()):
                key = self.documentListTo_choice.GetString(i)
                if key == docFrom: continue
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
            if docTo == docFrom: docTo=''
            elif docTo == 'all': docTo =''
            # Iterate over row and columns to get data
            for row in range(rows):
                if not self.parent.peaklist.IsChecked(index=row): continue
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
        


        