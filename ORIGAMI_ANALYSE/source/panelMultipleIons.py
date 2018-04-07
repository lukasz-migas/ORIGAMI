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
import wx.lib.mixins.listctrl as listmix
import dialogs as dialogs
from dialogs import panelModifyIonSettings, panelAsk
from toolbox import (isempty, str2num, str2int, saveAsText, convertRGB1to255, 
                     convertRGB255to1, randomIntegerGenerator, removeListDuplicates)
from ast import literal_eval
from operator import itemgetter
from numpy import arange, vstack, insert
import csv
from matplotlib import style
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
  #       

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
        self.listOfSelected = []
        self.allChecked = True
        self.override = self.config.overrideCombine
        
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
        
        self.makeGUI()
        
        # add a couple of accelerators
        accelerators = [
            (wx.ACCEL_NORMAL, ord('E'), ID_ionPanel_editItem),
            (wx.ACCEL_NORMAL, ord('O'), ID_overrideCombinedMenu),
            (wx.ACCEL_NORMAL, ord('I'), ID_useInternalParamsCombinedMenu),
            (wx.ACCEL_NORMAL, ord('P'), ID_useProcessedCombinedMenu),
            (wx.ACCEL_NORMAL, ord('B'), ID_combinedCV_binMSCombinedMenu),
            (wx.ACCEL_NORMAL, ord('H'), ID_highlightRectAllIons),
            (wx.ACCEL_NORMAL, ord('X'), ID_checkAllItems_Ions),
            (wx.ACCEL_NORMAL, ord('C'), ID_ionPanel_assignColor),
            (wx.ACCEL_NORMAL, ord('Z'), ID_showMSplotIon)
            ]
        self.SetAcceleratorTable(wx.AcceleratorTable(accelerators))
        
        wx.EVT_MENU(self, ID_ionPanel_editItem, self.OnOpenEditor)
        wx.EVT_MENU(self, ID_overrideCombinedMenu, self.setupMenus)
        wx.EVT_MENU(self, ID_useInternalParamsCombinedMenu, self.setupMenus)
        wx.EVT_MENU(self, ID_useProcessedCombinedMenu, self.setupMenus)
        wx.EVT_MENU(self, ID_combinedCV_binMSCombinedMenu, self.setupMenus)
        wx.EVT_MENU(self, ID_highlightRectAllIons, self.presenter.onShowExtractedIons)
        wx.EVT_MENU(self, ID_checkAllItems_Ions, self.OnCheckAllItems)
        wx.EVT_MENU(self, ID_ionPanel_assignColor, self.OnAssignColor)
        wx.EVT_MENU(self, ID_showMSplotIon, self.OnListGetIMMS)
                
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
        self.Bind(wx.EVT_TOOL, self.OnCheckAllItems, id=ID_checkAllItems_Ions)
        self.Bind(wx.EVT_COMBOBOX, self.onUpdateOverlayMethod, id=ID_selectOverlayMethod)
        self.Bind(wx.EVT_TOOL, self.onTableTool, id=ID_ionPanel_guiMenuTool)
        
        # Create toolbar for the table
        toolbar = wx.ToolBar(self, style=wx.TB_HORIZONTAL | wx.TB_DOCKABLE, id = wx.ID_ANY) 
        toolbar.SetToolBitmapSize((16, 16)) 
        toolbar.AddTool(ID_checkAllItems_Ions, self.icons.iconsLib['check16'] , 
                        shortHelpString="Check all items\tX")
        toolbar.AddSeparator()
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
                             shortHelpString="Overlay currently selected ions")
        self.combo = wx.ComboBox(toolbar, ID_selectOverlayMethod, value= "Transparent",
                                 choices=self.config.overlayChoices,
                                 style=wx.CB_READONLY)
        toolbar.AddControl(self.combo)
        toolbar.AddTool(ID_saveIonsMenu, self.icons.iconsLib['save16'], 
                             shortHelpString="Save...")
        toolbar.AddSeparator()
        toolbar.AddTool(ID_ionPanel_guiMenuTool, self.icons.iconsLib['setting16'], 
                             shortHelpString="Table settings...")

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
          
    def onStatusHelp(self, evt):
        evtID = evt.GetId()
        
        print('help')
        
        if evtID == ID_addManyIonsCSV:
            print('list')
            
        if evt != None:
            evt.Skip()
                
    def OnRightClickMenu(self, evt):
        
        # Menu events
        self.Bind(wx.EVT_MENU, self.OnListGetIMMS, id=ID_showMSplotIon)
        self.Bind(wx.EVT_MENU, self.OnListGetIMMS, id=ID_get1DplotIon)
        self.Bind(wx.EVT_MENU, self.OnListGetIMMS, id=ID_get2DplotIon)
        self.Bind(wx.EVT_MENU, self.OnListGetIMMS, id=ID_get2DplotIonWithProcss)
        self.Bind(wx.EVT_MENU, self.OnOpenEditor, id=ID_ionPanel_editItem)
        self.Bind(wx.EVT_MENU, self.OnAssignColor, id=ID_ionPanel_assignColor)
        self.Bind(wx.EVT_MENU, self.OnDeleteAll, id=ID_removeSelectedIonPopup)
        
        self.currentItem, __ = self.peaklist.HitTest(evt.GetPosition())
        menu = wx.Menu()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_showMSplotIon,
                                     text='Zoom in on the ion\tZ', 
                                     bitmap=self.icons.iconsLib['zoom_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_get1DplotIon,
                                     text='Show mobiligram', 
                                     bitmap=self.icons.iconsLib['chromatogram_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_get2DplotIon,
                                     text='Show heatmap', 
                                     bitmap=self.icons.iconsLib['heatmap_16']))
        menu.Append(ID_get2DplotIonWithProcss, "Process and show heatmap")
        menu.AppendSeparator()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_ionPanel_assignColor,
                                     text='Assign new color\tC', 
                                     bitmap=self.icons.iconsLib['color_panel_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_ionPanel_editItem,
                                     text='Edit ion information\tE', 
                                     bitmap=self.icons.iconsLib['info16']))
        menu.AppendSeparator()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_removeSelectedIonPopup,
                                     text='Remove item', 
                                     bitmap=self.icons.iconsLib['bin16']))
#         self.menu.Append(ID_ANY, "Save to .csv file...")
#         self.menu.Append(ID_ANY, 'Save figure as .png (selected ion)')
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
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def onAddTool(self, evt):
        
        self.Bind(wx.EVT_MENU, self.presenter.onOpenPeakListCSV, id=ID_addManyIonsCSV)
        self.Bind(wx.EVT_MENU, self.onDuplicateIons, id=ID_duplicateIons)
        self.Bind(wx.EVT_MENU, self.presenter.onAddBlankDocument, id=ID_addNewOverlayDoc)
        
        self.Bind(wx.EVT_MENU_HIGHLIGHT, self.onStatusHelp, id=ID_addManyIonsCSV)
       
        menu = wx.Menu()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_addManyIonsCSV,
                                     text='Add list of ions (.csv/.txt)\tCtrl+L', 
                                     bitmap=self.icons.iconsLib['filelist_16'],
                                     help_text='Format: m/z, window size, charge'))
        menu.AppendSeparator()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_addNewOverlayDoc,
                                     text='Add new comparison document\tAlt+D', 
                                     bitmap=self.icons.iconsLib['new_document_16']))
#         menu.AppendSeparator()
#         menu.Append(ID_duplicateIons, "Duplicate selected items to another document")
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()
        
    def onExtractTool(self, evt):
        
        self.Bind(wx.EVT_MENU, self.presenter.onExtract2DimsOverMZrangeMultiple, 
                  id=ID_extractNewIon)
        self.Bind(wx.EVT_MENU, self.presenter.onExtract2DimsOverMZrangeMultiple, 
                  id=ID_extractSelectedIon)
        self.Bind(wx.EVT_MENU, self.presenter.onExtract2DimsOverMZrangeMultiple, 
                  id=ID_extractAllIons)
        
        menu = wx.Menu()
        menu.Append(ID_extractNewIon, "Extract new ions")
        menu.Append(ID_extractSelectedIon, "Extract selected ions")
        menu.Append(ID_extractAllIons, "Extract all ions\tAlt+E")
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()
        
    def onOverlayTool(self, evt):

        self.Bind(wx.EVT_TOOL, self.presenter.onOverlayMultipleIons,
                  id=ID_overlayMZfromList)
        self.Bind(wx.EVT_TOOL, self.presenter.onOverlayMultipleIons1D,
                  id=ID_overlayMZfromList1D)
        self.Bind(wx.EVT_TOOL, self.presenter.onOverlayMultipleIons1D,
                  id=ID_overlayMZfromListRT)
        self.Bind(wx.EVT_MENU, self.setupMenus, id=ID_useProcessedCombinedMenu)
        
        menu = wx.Menu()
        menu.Append(ID_overlayMZfromList1D, "Overlay mobiligrams (selected)")
        menu.Append(ID_overlayMZfromListRT, "Overlay chromatograms (selected)")
        menu.AppendSeparator()
        self.useProcessed_check = menu.AppendCheckItem(ID_useProcessedCombinedMenu, "Use processed data (when available)\tP",
                                                       help="When checked, processed data is used in the overlay (2D) plots.")
        self.useProcessed_check.Check(self.config.overlay_usedProcessed)
        menu.AppendSeparator()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_overlayMZfromList,
                                     text='Overlay heatmaps (selected)\tAlt+Q', 
                                     bitmap=self.icons.iconsLib['heatmap_grid_16']))
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()
              
    def onRemoveTool(self, evt):
        # Make bindings
        self.Bind(wx.EVT_MENU, self.OnDeleteAll, id=ID_removeSelectedIon)
        self.Bind(wx.EVT_MENU, self.OnDeleteAll, id=ID_removeAllIons)
        self.Bind(wx.EVT_MENU, self.OnClearTable, id=ID_clearTableIons)
        self.Bind(wx.EVT_MENU, self.onRemoveDuplicates, id=ID_removeDuplicatesTable)
        
        menu = wx.Menu()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_clearTableIons,
                                     text='Clear table', 
                                     bitmap=self.icons.iconsLib['clear_16']))
        menu.AppendSeparator()
        menu.Append(ID_removeDuplicatesTable, "Remove duplicates")
        menu.Append(ID_removeSelectedIon, "Remove selected ions")
        menu.Append(ID_removeAllIons, "Remove all ions")
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def onProcessTool(self, evt):
        
        self.Bind(wx.EVT_MENU, self.presenter.onCombineCEvoltagesMultiple, id=ID_combineCEscansSelectedIons)
        self.Bind(wx.EVT_MENU, self.presenter.onCombineCEvoltagesMultiple, id=ID_combineCEscans)
        
        self.Bind(wx.EVT_MENU, self.presenter.onProcessMultipleIonsIons, id=ID_processSelectedIons)
        self.Bind(wx.EVT_MENU, self.presenter.onProcessMultipleIonsIons, id=ID_processAllIons)
        self.Bind(wx.EVT_MENU, self.presenter.onExtractMSforEachCollVoltage, id=ID_extractMSforCVs)
        
        self.Bind(wx.EVT_MENU, self.setupMenus, id=ID_overrideCombinedMenu)
        self.Bind(wx.EVT_MENU, self.setupMenus, id=ID_useInternalParamsCombinedMenu)
        self.Bind(wx.EVT_MENU, self.setupMenus, id=ID_combinedCV_binMSCombinedMenu)
        
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
        menu.Append(ID_combineCEscansSelectedIons, "Combine CVs for selected ions (ORIGAMI)")
        menu.Append(ID_combineCEscans, "Combine CVs for all ions (ORIGAMI)\tAlt+C")
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
        
        self.Bind(wx.EVT_MENU, self.setupMenus, id=ID_processSaveMenu)
        
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
        
    def onTableTool(self, evt):
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
           
    def setupMenus(self, evt):
        """ Check/uncheck menu item """
        
        evtID = evt.GetId()
        
        # check which event was triggered
        if evtID == ID_overrideCombinedMenu:
            check_value = not self.config.overrideCombine
            self.config.overrideCombine = check_value
            args = ("Peak list panel: 'Override' combined IM-MS data was switched to %s" % self.config.overrideCombine, 4)
            self.presenter.onThreading(evt, args, action='updateStatusbar')
            
        if evtID == ID_useInternalParamsCombinedMenu:
            check_value = not self.config.useInternalParamsCombine
            self.config.useInternalParamsCombine = check_value
            args = ("Peak list panel: 'Use internal parameters' was switched to  %s" % self.config.useInternalParamsCombine, 4)
            self.presenter.onThreading(evt, args, action='updateStatusbar')
            
        if evtID == ID_processSaveMenu:
            check_value = not self.process
            self.process = check_value
            args = ("Override was switched to %s" % self.override, 4)
            self.presenter.onThreading(evt, args, action='updateStatusbar')
            
        if evtID == ID_useProcessedCombinedMenu:
            check_value = not self.config.overlay_usedProcessed
            self.config.overlay_usedProcessed = check_value
            args = ("Peak list panel: Using processing data was switched to %s" % self.config.overlay_usedProcessed, 4)
            self.presenter.onThreading(evt, args, action='updateStatusbar')
            
        if evtID == ID_combinedCV_binMSCombinedMenu:
            check_value = not self.config.binCVdata
            self.config.binCVdata = check_value
            args = ("Binning mass spectra from ORIGAMI files was switched to %s" % self.config.binCVdata, 4)
            self.presenter.onThreading(evt, args, action='updateStatusbar')
            
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
                filename = self.peaklist.GetItem(row, self.config.peaklistColNames['filename']).GetText()
                selectedText = self.getCurrentIon(index=row, evt=None)
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
            mzStart = self.peaklist.GetItem(ion,self.config.peaklistColNames['start']).GetText()
            mzEnd = self.peaklist.GetItem(ion,self.config.peaklistColNames['end']).GetText()
            rangeName = ''.join([str(mzStart),'-',str(mzEnd)])
            filename = self.peaklist.GetItem(ion,self.config.peaklistColNames['filename']).GetText()
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
                zvals = self.presenter.process2Ddata(zvals=zvals)
                
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
                savename = ''.join([currentDocument.path, "\\", saveFileName, rangeName,'.']) # extension is added later
                self.presenter.onPlot2DIMS2(zvals, xvals, yvals, xlabel, ylabel, cmap)
                self.presenter.save2DIMSImage(path=savename)
        msg = 'Finished saving data'
        self.presenter.view.SetStatusText(msg, 3)
        
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
            mzStartInTable = self.peaklist.GetItem(currentItems,0).GetText()
            mzEndInTable = self.peaklist.GetItem(currentItems,1).GetText()
            if mzStartInTable == mzStart and mzEndInTable == mzEnd:
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
                #  We want to make sure certain columns are numbers
                if (col==self.config.peaklistColNames['start'] or 
                    col==self.config.peaklistColNames['end'] or 
                    col==self.config.peaklistColNames['intensity']):
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
            tempRow.append(self.peaklist.GetItemTextColour(row))
            tempData.append(tempRow)
            
        # Sort data  
        tempData.sort(key = itemgetter(column), reverse=self.reverse)
        # Clear table
        self.peaklist.DeleteAllItems()
        
        checkData, rgbData = [], []
        for check in tempData:
            rgbData.append(check[-1])
            del check[-1]
            checkData.append(check[-1])
            del check[-1]

        # Reinstate data
        rowList = arange(len(tempData))
        for row, check, rgb in zip(rowList, checkData, rgbData):
            self.peaklist.Append(tempData[row])
            self.peaklist.CheckItem(row, check)
            self.peaklist.SetItemTextColour(row, rgb)
            
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
                if col in [0, 1, 3, 6, 7]:
                    itemData = str2num(item.GetText())
                    if itemData == None: itemData = 0
                    tempRow.append(itemData)
                elif col==2:
                    itemData = str2int(item.GetText())
                    if itemData == None: itemData = 0
                    tempRow.append(itemData)
                else:
                    tempRow.append(item.GetText())
            tempRow.append(self.peaklist.IsChecked(index=row))
            tempRow.append(self.peaklist.GetItemTextColour(row))
            tempData.append(tempRow)

        # Remove duplicates
        tempData = removeListDuplicates(input=tempData,
                                        columnsIn=['start', 'end', 'charge', 'intensity', 
                                        'color', 'colormap', 'alpha', 'mask', 
                                        'label', 'method', 'filename', 'check', 'rgb'],
                                        limitedCols=['start','end','filename'])     
        rows = len(tempData)
        # Clear table
        self.peaklist.DeleteAllItems()
        
        checkData, rgbData = [], []
        for check in tempData:
            rgbData.append(check[-1])
            del check[-1]
            checkData.append(check[-1])
            del check[-1]
        
        # Reinstate data
        rowList = arange(len(tempData))
        for row, check, rgb in zip(rowList, checkData, rgbData):
            self.peaklist.Append(tempData[row])
            self.peaklist.CheckItem(row, check)
            self.peaklist.SetItemTextColour(row, rgb)
            
        if evt is None: return
        else:
            evt.Skip()
                  
    def OnListGetIMMS(self, evt):
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
            msg = "Please extract data before trying to view it"
            self.presenter.view.SetStatusText(msg, 3)
            return
                
        if evt.GetId() == ID_get1DplotIon:
            xvals = data[rangeName]['yvals'] # normally this would be the y-axis
            yvals = data[rangeName]['yvals1D']
            xlabels = data[rangeName]['ylabels'] # normally this would be x-axis label
            lineColour = currentDocument.lineColour
            style = currentDocument.style
            self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['1D'])
            self.presenter.onPlot1DIMS2(xvals, yvals, xlabels, lineColour, style)
        elif evt.GetId() == ID_showMSplotIon:
            """
            This simply zooms in on an ion
            """
            if selectedItem != self.presenter.currentDoc: 
                print('This ion belongs to different document')
            startX = str2num(mzStart)-self.config.zoomWindowX
            endX = str2num(mzEnd)+self.config.zoomWindowX
            try:
                endY = str2num(intensity)/100
            except TypeError: 
                endY = 1.001
            if endY == 0: endY = 1.001
            self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['MS'])
            self.presenter.onZoomMS(startX=startX,endX=endX, endY=endY)
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
            if evt.GetId() == ID_get2DplotIonWithProcss:
                zvals = self.presenter.process2Ddata(zvals=zvals, return_data=True)
            # Plot data
            self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['2D'])
            self.presenter.onPlot2DIMS2(zvals, xvals, yvals, xlabel, ylabel, cmap)
     
    def getCurrentIon(self, index=None, evt=None):
        """
        This function is responsible to obtain the currently clicked on item
        """
        
        if index == None:
            index = self.currentItem
            
        mzStart = self.peaklist.GetItem(index, self.config.peaklistColNames['start']).GetText()
        mzEnd = self.peaklist.GetItem(index, self.config.peaklistColNames['end']).GetText()
        selectedItem = ''.join([str(mzStart),'-',str(mzEnd)])
        return selectedItem
                   
    def OnDeleteAll(self, evt, ticked=False, selected=False, itemID=None):
        """ 
        This function removes selected or all text documents
        """
        if evt.GetId() == ID_removeSelectedIon:
            currentItems = self.peaklist.GetItemCount()-1
            while (currentItems >= 0):
                if self.peaklist.IsChecked(index=currentItems):
                    selectedItem = self.peaklist.GetItem(currentItems,5).GetText()
                    mzStart = self.peaklist.GetItem(currentItems,0).GetText()
                    mzEnd = self.peaklist.GetItem(currentItems,1).GetText()
                    selectedIon = ''.join([str(mzStart),'-',str(mzEnd)])
                    print(''.join(["Deleting ",selectedIon, " from ", selectedItem]))
                    # Delete selected document from dictionary + table
                    try: 
                        del self.presenter.documentsDict[selectedItem].IMS2Dions[selectedIon]
                        if len(self.presenter.documentsDict[selectedItem].IMS2Dions.keys()) == 0: 
                            self.presenter.documentsDict[selectedItem].gotExtractedIons = False
                    except KeyError: pass
                    try: 
                        del self.presenter.documentsDict[selectedItem].IMS2DionsProcess[selectedIon]
                        if len(self.presenter.documentsDict[selectedItem].IMS2DionsProcess.keys()) == 0: 
                            self.presenter.documentsDict[selectedItem].got2DprocessIons = False
                    except KeyError: pass
                    try: 
                        del self.presenter.documentsDict[selectedItem].IMSRTCombIons[selectedIon]
                        if len(self.presenter.documentsDict[selectedItem].IMSRTCombIons.keys()) == 0: 
                            self.presenter.documentsDict[selectedItem].gotCombinedExtractedIonsRT = False
                    except KeyError: pass
                    try: 
                        del self.presenter.documentsDict[selectedItem].IMS2DCombIons[selectedIon]
                        if len(self.presenter.documentsDict[selectedItem].IMS2DCombIons.keys()) == 0: 
                            self.presenter.documentsDict[selectedItem].gotCombinedExtractedIons = False
                    except KeyError: pass
                    self.peaklist.DeleteItem(currentItems)
                    try:
                        self.presenter.view.panelDocuments.topP.documents.addDocument(docData = self.presenter.documentsDict[selectedItem])
                    except KeyError: pass    
                    currentItems-=1
                else:
                    currentItems-=1
        elif evt.GetId() == ID_removeSelectedIonPopup:
            
            selectedItem = self.peaklist.GetItem(self.currentItem,5).GetText()
            mzStart = self.peaklist.GetItem(self.currentItem,0).GetText()
            mzEnd = self.peaklist.GetItem(self.currentItem,1).GetText()
            selectedIon = ''.join([str(mzStart),'-',str(mzEnd)])
            itemID= [selectedItem, selectedIon, self.currentItem]
            if itemID != None:
                selectedItem, selectedIon, currentItems = itemID
                print(''.join(["Deleting ",selectedIon, " from ", selectedItem]))
                # Delete selected document from dictionary + table   
                try: 
                    del self.presenter.documentsDict[selectedItem].IMS2Dions[selectedIon]
                    if len(self.presenter.documentsDict[selectedItem].IMS2Dions.keys()) == 0: 
                        self.presenter.documentsDict[selectedItem].gotExtractedIons = False
                except KeyError: pass
                try: 
                    del self.presenter.documentsDict[selectedItem].IMS2DionsProcess[selectedIon]
                    if len(self.presenter.documentsDict[selectedItem].IMS2DionsProcess.keys()) == 0: 
                        self.presenter.documentsDict[selectedItem].got2DprocessIons = False
                except KeyError: pass
                try: 
                    del self.presenter.documentsDict[selectedItem].IMSRTCombIons[selectedIon]
                    if len(self.presenter.documentsDict[selectedItem].IMSRTCombIons.keys()) == 0: 
                        self.presenter.documentsDict[selectedItem].gotCombinedExtractedIonsRT = False
                except KeyError: pass
                try: 
                    del self.presenter.documentsDict[selectedItem].IMS2DCombIons[selectedIon]
                    if len(self.presenter.documentsDict[selectedItem].IMS2DCombIons.keys()) == 0: 
                        self.presenter.documentsDict[selectedItem].gotCombinedExtractedIons = False
                except KeyError: pass
                self.peaklist.DeleteItem(currentItems)
                try:
                    self.presenter.view.panelDocuments.topP.documents.addDocument(docData = self.presenter.documentsDict[selectedItem])
                except KeyError: pass  
                # Remove reference to calibrants if there are none remaining for the document
        else:
        # Ask if you are sure to delete it!
            dlg = dialogs.dlgBox(exceptionTitle='Are you sure?', 
                                 exceptionMsg= "Are you sure you would like to delete ALL ions?",
                                 type="Question")
            if dlg == wx.ID_NO:
                print('Cancelled operation')
                return
            else:
#                 for textID in range(self.peaklist.GetItemCount()):
                currentItems = self.peaklist.GetItemCount()-1
                while (currentItems >= 0):
                    selectedItem = self.peaklist.GetItem(currentItems,5).GetText()
                    mzStart = self.peaklist.GetItem(currentItems,0).GetText()
                    mzEnd = self.peaklist.GetItem(currentItems,1).GetText()
                    selectedIon = ''.join([str(mzStart),'-',str(mzEnd)])
                    print(''.join(["Deleting ",selectedIon, " from ", selectedItem]))
                    try: 
                        del self.presenter.documentsDict[selectedItem].IMS2Dions[selectedIon]
                        if len(self.presenter.documentsDict[selectedItem].IMS2Dions.keys()) == 0: 
                            self.presenter.documentsDict[selectedItem].gotExtractedIons = False
                    except KeyError: pass
                    try: 
                        del self.presenter.documentsDict[selectedItem].IMS2DionsProcess[selectedIon]
                        if len(self.presenter.documentsDict[selectedItem].IMS2DionsProcess.keys()) == 0: 
                            self.presenter.documentsDict[selectedItem].got2DprocessIons = False
                    except KeyError: pass
                    try: 
                        del self.presenter.documentsDict[selectedItem].IMSRTCombIons[selectedIon]
                        if len(self.presenter.documentsDict[selectedItem].IMSRTCombIons.keys()) == 0: 
                            self.presenter.documentsDict[selectedItem].gotCombinedExtractedIonsRT = False
                    except KeyError: pass
                    try: 
                        del self.presenter.documentsDict[selectedItem].IMS2DCombIons[selectedIon]
                        if len(self.presenter.documentsDict[selectedItem].IMS2DCombIons.keys()) == 0: 
                            self.presenter.documentsDict[selectedItem].gotCombinedExtractedIons = False
                    except KeyError: pass
                    self.peaklist.DeleteItem(currentItems)
                    try:
                        self.presenter.view.panelDocuments.topP.documents.addDocument(docData = self.presenter.documentsDict[selectedItem])
                    except KeyError: pass  
                    self.peaklist.DeleteItem(currentItems)
                    currentItems-=1
        msg = ''.join(["Remaining documents: ", str(len(self.presenter.documentsDict))])
        self.presenter.view.SetStatusText(msg, 3)
        self.onReplotRectanglesDT_MZ(evt=None)
            
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
        # Ask if you want to delete all items
        dlg = dialogs.dlgBox(exceptionTitle='Are you sure?', 
                             exceptionMsg= "Are you sure you would like to clear the table??",
                             type="Question")
        if dlg == wx.ID_NO:
            msg = 'Cancelled operation'
            self.presenter.view.SetStatusText(msg, 3)
            return
        self.peaklist.DeleteAllItems()
        
    def onDuplicateIons(self, evt):
        
        # Create a list of keys in the dictionary
        keyList = []
        if len(self.presenter.documentsDict) == 0: 
            msg = 'There are no documents to copy peaks to!'
            self.presenter.view.SetStatusText(msg, 3)
            return
        elif self.peaklist.GetItemCount() == 0: 
            msg = 'There are no peaks in the table. Try adding some first!'
            self.presenter.view.SetStatusText(msg, 3)
            return
        
        keyList.append('all')
        for key in self.presenter.documentsDict:
            keyList.append(key)
        
        self.duplicateDlg = panelDuplicateIons(self, keyList)
        self.duplicateDlg.Show()
   
    def onReplotRectanglesDT_MZ(self, evt):
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
        color = document.lineColour
        style = document.style
        # Change panel and plot 
        self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['MS'])
         
        self.presenter.onPlotMS2(msX, msY, xlimits=xlimits)
        if count == 0: return
        ymin = 0
        height = 1.0
        last = self.peaklist.GetItemCount()-1
        # Iterate over the list and plot rectangle one by one
        for row in range(count):
            xmin = str2num(self.peaklist.GetItem(itemId=row, col=0).GetText())
            xmax = str2num(self.peaklist.GetItem(itemId=row, col=1).GetText())
            width = xmax-xmin
            if row == last:
                self.presenter.addRectMS(xmin, ymin, width, height, color=self.config.annotColor, 
                                         alpha=(self.config.annotTransparency/100),
                                         repaint=True)
            else:
                self.presenter.addRectMS(xmin, ymin, width, height, color=self.config.annotColor, 
                                         alpha=(self.config.annotTransparency/100),
                                         repaint=False)
     
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
                       'color':self.peaklist.GetItemTextColour(item=itemID),
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
        
        if information['ionName'] in self.docs.IMS2Dions:
            min_threshold = self.docs.IMS2Dions[information['ionName']].get('min_threshold', 0)
            max_threshold = self.docs.IMS2Dions[information['ionName']].get('max_threshold', 1)
        
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
            self.peaklist.SetItemTextColour(itemID, value)
            self.peaklist.SetStringItem(itemID, 4, str(value))
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
            self.peaklist.SetItemTextColour(self.currentItem, newColour)
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
            self.peaklist.SetItemTextColour(self.currentItem, newColour)
            if give_value:
                return newColour
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
                if keyword == 'colormap': keyword_name = 'cmap'
                else: keyword_name = keyword
                document.IMSRTCombIons[itemInfo['ionName']][keyword_name] = itemInfo[keyword]
                try: document.IMSRTCombIons[processed_name][keyword_name] = itemInfo[keyword]
                except: pass  
        
        # Update file list
        self.presenter.OnUpdateDocument(document, 'no_refresh')
        

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
        


        