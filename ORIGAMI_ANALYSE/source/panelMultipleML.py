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
from origamiStyles import *
from analysisFcns import normalizeMS
from ids import *
import wx.lib.mixins.listctrl  as  listmix
import dialogs as dialogs
from collections import OrderedDict
from toolbox import str2num, num2str
from operator import itemgetter
from wx import ID_ANY
import numpy as np

"""
Panel to load and combine multiple ML files
"""

class panelMML ( wx.Panel ):
    
    def __init__( self, parent, config, icons,  presenter ):
        wx.Panel.__init__ ( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, 
                            size = wx.Size( 300,600 ), style = wx.TAB_TRAVERSAL )

        self.parent = parent
        self.config = config
        self.presenter = presenter
        self.icons = icons
               
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.topP = topPanel(self, self.icons, self.presenter, self.config)
        sizer.Add(self.topP, 1, wx.EXPAND | wx.ALL, 1)
        self.SetSizer(sizer)           
        
    def __del__( self ):
         pass
        
class EditableListCtrl(wx.ListCtrl, listmix.TextEditMixin, listmix.CheckListCtrlMixin,
                       listmix.ColumnSorterMixin):
    """
    Editable list
    """
    # TODO Add checkbox to the first column - useful for selecting ions to plot?
    def __init__(self, parent, ID=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0): 
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.TextEditMixin.__init__(self)
        listmix.CheckListCtrlMixin.__init__(self)


            
        
class topPanel(wx.Panel):
    def __init__(self, parent, icons,  presenter, config):
        wx.Panel.__init__(self, parent=parent)
        self.icons = icons
        self.config = config
        self.presenter = presenter # wx.App
        self.makeToolbar()
        self.makeListCtrl()
        self.currentItem = None
        self.currentXlabels = 'bins'
        self.allChecked = True
        
        panelSizer = wx.BoxSizer( wx.VERTICAL )
        panelSizer.Add(self.toolbar, 0, wx.EXPAND, 0)
        panelSizer.Add(self.filelist, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizer( panelSizer )

        self.reverse = False
        self.lastColumn = None


    def makeListCtrl(self):
        # Create toolbar for the table
        self.filelist = EditableListCtrl(self, style=wx.LC_REPORT)
        self.filelist.InsertColumn(0,u'File name', width=220)
        self.filelist.InsertColumn(1,u'Energy', width=50)
        self.filelist.InsertColumn(2,u'Document', width=80)
        filelistTooltip = makeTooltip(delay=3000, reshow=3000, 
                                      text="""List of files and their respective energy values. This panel is relatively universal and can be used for aIMMS, CIU, SID or any other activation technique where energy was increased for separate files.""")
        self.filelist.SetToolTip(filelistTooltip)
        
        self.Bind(wx.EVT_LIST_COL_CLICK, self.OnGetColumnClick)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnRightClickMenu)

    def makeToolbar(self):
        
        self.Bind(wx.EVT_TOOL, self.onRemoveTool, id=ID_removeFilesMenu)
#         self.Bind(wx.EVT_TOOL, self.onSaveTool, id=ID_saveFilesMenu)
        self.Bind(wx.EVT_TOOL, self.onProcessTool, id=ID_processFilesMenu)
        self.Bind(wx.EVT_TOOL, self.OnCheckAllItems, id=ID_checkAllItems_MML)

        self.Bind(wx.EVT_TOOL, self.presenter.onOpenMultipleMLFiles, id=ID_openMassLynxFiles)
        
        self.toolbar = wx.ToolBar(self, style=wx.TB_HORIZONTAL | wx.TB_DOCKABLE, id = wx.ID_ANY) 
        self.toolbar.SetToolBitmapSize((16, 16)) 
        self.toolbar.AddTool(ID_checkAllItems_MML, self.icons.iconsLib['check16'] , 
                              shortHelpString="Check all items")
        self.toolbar.AddTool(ID_openMassLynxFiles, self.icons.iconsLib['add16'] , 
                              shortHelpString="Add files...") 
        self.toolbar.AddTool(ID_removeFilesMenu, self.icons.iconsLib['remove16'], 
                             shortHelpString="Remove...")
        self.toolbar.AddTool(ID_processFilesMenu, self.icons.iconsLib['process16'], 
                             shortHelpString="Process...")
#         self.toolbar.AddTool(ID_saveFilesMenu, self.icons.iconsLib['save16'], 
#                              shortHelpString="Save...")
        self.toolbar.AddSeparator()
        self.toolbar.Realize()   
                      
    def onRemoveTool(self, evt):
        # Make bindings
        self.Bind(wx.EVT_MENU, self.OnDeleteAll, id=ID_removeSelectedFile)
        self.Bind(wx.EVT_MENU, self.OnDeleteAll, id=ID_removeAllFiles)
        self.Bind(wx.EVT_MENU, self.OnClearTable, id=ID_clearTableMML)
        
        menu = wx.Menu()
        menu.Append(ID_clearTableMML, "Clear table")
        menu.AppendSeparator()
        menu.Append(ID_removeSelectedFile, "Remove selected file")
        menu.Append(ID_removeAllFiles, "Remove all files")
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

#     def onSaveTool(self, evt):
#         menu = wx.Menu()
#         menu.Append(ID_save1DAllFiles, "Export 1D IM-MS to file (all items)")
#         menu.Append(ID_saveMSAllFiles, "Export MS to file (all items)")
#         menu.Append(ID_ExportWindowFiles, "Export... (new window)")
#         self.PopupMenu(menu)
#         menu.Destroy()
#         self.SetFocus()

    def onProcessTool(self, evt):
        # Make bindings
        self.Bind(wx.EVT_MENU, self.presenter.reBinMSdata, id=ID_reBinMSmanual)
#         self.Bind(wx.EVT_MENU, self.OnListConvertAxis, id=ID_convertSelectedAxisFiles)
#         self.Bind(wx.EVT_MENU, self.OnListConvertAxis, id=ID_convertAllAxisFiles)
#         self.Bind(wx.EVT_MENU, self.presenter.onCombineMultipleMLFiles, id=ID_combineMassLynxFiles)
        
        menu = wx.Menu()
        menu.Append(ID_reBinMSmanual, "Re-bin MS of list of MassLynx files")
#         menu.Append(ID_convertSelectedAxisFiles, "Convert 1D/2D IM-MS from bins to ms (selected)")
#         if self.currentXlabels == 'ms':
#             menu.Append(ID_convertAllAxisFiles, "Convert 1D/2D IM-MS from ms to bins (all)")
#         else:
#             menu.Append(ID_convertAllAxisFiles, "Convert 1D/2D IM-MS from bins to ms (all)")
#         menu.Append(ID_combineMassLynxFiles, "Combine 1D DT to form 2D matrix (ascending energy)")
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()
        
    def OnRightClickMenu(self, evt):
        
        self.Bind(wx.EVT_MENU, self.OnListGetMS, id=ID_getMassSpectrum)
        self.Bind(wx.EVT_MENU, self.OnListGet1DT, id=ID_get1DmobilitySpectrum)
        self.Bind(wx.EVT_MENU, self.OnDeleteAll, id=ID_removeSelectedFilePopup)
        
        self.Bind(wx.EVT_MENU, self.OnListGetMS, id=ID_getCombinedMassSpectrum)
#         self.Bind(wx.EVT_MENU, self.OnListConvertAxis, id=ID_convertAxisFilesPopup)
        
        
        # Capture which item was clicked
        self.currentItem, flags = self.filelist.HitTest(evt.GetPosition())
        # Create popup menu
        menu = wx.Menu()
        menu.Append(ID_getMassSpectrum, "Show mass spectrum (selected item)")
        menu.Append(ID_get1DmobilitySpectrum, "Show 1D IM-MS (selected item)")
#         menu.Append(ID_convertAxisFilesPopup, "Convert 1D/2D IM-MS to drift time (ms)")
        menu.Append(ID_getCombinedMassSpectrum, "Show mass spectrum (all items)")
#         menu.Append(ID_ANY, "Show 2D IM-MS (all items)")
#         menu.AppendSeparator()
# #         menu.Append(ID_ANY, "Fill Energy column")
#         menu.AppendSeparator()
#         menu.Append(ID_ANY, "Save mass spectrum to .csv file")
#         menu.Append(ID_ANY, "Save 1D IM-MS to .csv file")
#         menu.Append(ID_ANY, "Save 2D IM-MS to .csv file")
        menu.AppendSeparator()
        menu.Append(ID_removeSelectedFilePopup, "Remove from the list")
                    
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def OnListConvertAxis(self, evt):
        """
        Function to convert x and y axis labels to/from bins-ms-ccs
        """
        document = self.getCurrentDocument()
        if document == None: return
        currentItems = self.filelist.GetItemCount()-1
        if evt.GetId() == ID_convertSelectedAxisFiles: pass
        elif evt.GetId() == ID_convertAxisFilesPopup:
            selectedItem = self.filelist.GetItem(self.currentItem,0).GetText()
            xlabel = document.multipleMassSpectrum[selectedItem]['xlabel']
            pusherFreq = document.multipleMassSpectrum[selectedItem]['parameters']['pusherFreq']
            # This should try to use the global pusher!
            if pusherFreq == None: 
                pusherFreq = document.parameters['pusherFreq']
                # If still fails, this should open a pupup for manual
                # TODO: prompt for manual pusher value
                if pusherFreq == None:  return
            if xlabel == 'Drift time(bins)':
                dtX = (document.multipleMassSpectrum[selectedItem]['ims1DX'] * pusherFreq)/1000
                document.multipleMassSpectrum[selectedItem]['ims1DX'] = dtX
                document.multipleMassSpectrum[selectedItem]['xlabel'] = 'Drift time (ms)'
            elif xlabel == 'Drift time (ms)':
                dtX = (document.multipleMassSpectrum[selectedItem]['ims1DX'] / pusherFreq)*1000
                document.multipleMassSpectrum[selectedItem]['ims1DX'] = dtX
                document.multipleMassSpectrum[selectedItem]['xlabel'] = 'Drift time(bins)'    
            # Call and plot that plot
            self.OnListGet1DT(evt)  
        else: 
            while (currentItems >= 0):
                selectedItem = self.filelist.GetItem(currentItems,0).GetText()
                xlabel = document.multipleMassSpectrum[selectedItem]['xlabel']
                pusherFreq = document.multipleMassSpectrum[selectedItem]['parameters']['pusherFreq']
                # This should try to use the global pusher!
                if pusherFreq == None: 
                    pusherFreq = document.parameters['pusherFreq']
                    # If still fails, this should open a pupup for manual
                    # TODO: prompt for manual pusher value
                    if pusherFreq == None:  
                        currentItems-=1
                        continue
                if xlabel == 'Drift time(bins)':
                    self.currentXlabels = "ms"
                    dtX = (document.multipleMassSpectrum[selectedItem]['ims1DX'] * pusherFreq)/1000
                    document.multipleMassSpectrum[selectedItem]['ims1DX'] = dtX
                    document.multipleMassSpectrum[selectedItem]['xlabel'] = 'Drift time (ms)'
                elif xlabel == 'Drift time (ms)':
                    self.currentXlabels = 'bins'
                    dtX = (document.multipleMassSpectrum[selectedItem]['ims1DX'] / pusherFreq)*1000
                    document.multipleMassSpectrum[selectedItem]['ims1DX'] = dtX
                    document.multipleMassSpectrum[selectedItem]['xlabel'] = 'Drift time(bins)'    
                currentItems-=1
        # Update document dictionary and tree
        self.presenter.documentsDict[document.title] = document
        try:
            self.presenter.view.panelDocuments.topP.documents.addDocument(docData = self.presenter.documentsDict[document.title])
        except KeyError: pass 
        
    def OnListGetMS(self, evt):
        """
        Function to plot selected MS in the mainWindow
        """
        
        document = self.getCurrentDocument()
        if document == None: return
        
        if evt.GetId() == ID_getMassSpectrum:
            itemName = self.filelist.GetItem(self.currentItem,0).GetText()
            try:
                msX = document.multipleMassSpectrum[itemName]['xvals']
                msY = document.multipleMassSpectrum[itemName]['yvals']
            except KeyError: return
            parameters = document.multipleMassSpectrum[itemName]['parameters']
            xlimits = [parameters['startMS'],parameters['endMS']]
        elif evt.GetId() == ID_getCombinedMassSpectrum:
            msX = document.massSpectrum['xvals']
            msY = document.massSpectrum['yvals']
            xlimits = document.massSpectrum['xlimits']
        
        # Plot data
        self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['MS'])
        self.presenter.onPlotMS2(msX, msY, document.lineColour,
                                 document.style, xlimits=xlimits)
        
    def OnListGet1DT(self, evt):
        """
        Function to plot selected 1DT in the mainWindow
        """
        document = self.getCurrentDocument()
        if document == None: return
        itemName = self.filelist.GetItem(self.currentItem,0).GetText()
        dtX = document.multipleMassSpectrum[itemName]['ims1DX']
        dtY = document.multipleMassSpectrum[itemName]['ims1D']
        xlabel = document.multipleMassSpectrum[itemName]['xlabel']
        
        self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['1D'])
        self.presenter.onPlot1DIMS2(dtX, dtY, xlabel, 
                                    document.lineColour, 
                                    document.style)
            
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

        if evt != None:
            evt.Skip()
             
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
        
        columns = self.filelist.GetColumnCount()
        rows = self.filelist.GetItemCount()
        tempData = []
        # Iterate over row and columns to get data
        for row in range(rows):
            tempRow = []
            for col in range(columns):
                item = self.filelist.GetItem(itemId=row, col=col)
                #  We want to make sure the first 3 columns are numbers
                if col==1:
                    itemData = str2num(item.GetText())
                    if itemData == None: itemData = 0
                    tempRow.append(itemData)
                else:
                    tempRow.append(item.GetText())
            tempData.append(tempRow)
        
        # Sort data  
        tempData.sort(key = itemgetter(column), reverse=self.reverse)
        # Clear table and reinsert data
        self.filelist.DeleteAllItems()
        for row in range(rows):
            self.filelist.Append(tempData[row])
        
        # Now insert it into the document
#         document = self.getCurrentDocument()
#         if document == None: return
        for row in range(rows):
            itemName = self.filelist.GetItem(itemId=row, 
                                             col=self.config.multipleMLColNames['filename']).GetText()
            docName = self.filelist.GetItem(itemId=row, 
                                            col=self.config.multipleMLColNames['document']).GetText()
            trapCV = str2num(self.filelist.GetItem(itemId=row, 
                                                   col=self.config.multipleMLColNames['energy']).GetText())
            
            self.presenter.documentsDict[docName].multipleMassSpectrum[itemName]['trap'] = trapCV

    def getCurrentDocument(self, docNameOnly=False):
        """
        Determines what is the currently selected document
        Gives an 'None' error when wrong document has been selected
        """
        # Now insert it into the document
        try:
            currentDoc = self.presenter.view.panelDocuments.topP.documents.enableCurrentDocument()
        except: 
            return None
        if currentDoc == 'Current documents':
            msg = 'There are no documents in the tree'
            self.presenter.view.SetStatusText(msg, 3)
            return currentDoc
        document = self.presenter.documentsDict[currentDoc]
        if document.dataType != 'Type: MANUAL': 
            msg = 'Make sure you select the correct dataset - MANUAL'
            self.presenter.view.SetStatusText(msg, 3)
            return None
        if docNameOnly: return currentDoc
        else: return document
        
    def OnDeleteAll(self, evt, ticked=False, selected=False, itemID=None):
        """ 
        This function removes selected or all MassLynx files from the 
        combined document
        """
        
        currentDoc = self.getCurrentDocument(docNameOnly=True)
        if currentDoc == None: return
        currentItems = self.filelist.GetItemCount()-1
        if evt.GetId() == ID_removeSelectedFile:
            while (currentItems >= 0):
                item = self.filelist.IsChecked(index=currentItems)
                if item == True:
                    selectedItem = self.filelist.GetItem(currentItems,0).GetText()
                    print(''.join(["Deleting ",selectedItem, " from ", currentDoc]))
                    try: 
                        del self.presenter.documentsDict[currentDoc].multipleMassSpectrum[selectedItem]
                        if len(self.presenter.documentsDict[currentDoc].multipleMassSpectrum.keys()) == 0: 
                            self.presenter.documentsDict[currentDoc].gotMultipleMS = False
                    except KeyError: pass
                    self.filelist.DeleteItem(currentItems)
                    currentItems-=1
                else:
                    currentItems-=1
            try:
                self.presenter.view.panelDocuments.topP.documents.addDocument(docData = self.presenter.documentsDict[currentDoc])
            except KeyError: pass  
        elif evt.GetId() == ID_removeSelectedFilePopup:
            selectedItem = self.filelist.GetItem(self.currentItem,0).GetText()
            print(''.join(["Deleting ",selectedItem, " from ", currentDoc]))
            try: 
                del self.presenter.documentsDict[currentDoc].multipleMassSpectrum[selectedItem]
                if len(self.presenter.documentsDict[currentDoc].multipleMassSpectrum.keys()) == 0: 
                    self.presenter.documentsDict[currentDoc].gotMultipleMS = False
            except KeyError: pass
            self.filelist.DeleteItem(self.currentItem)
            try:
                self.presenter.view.panelDocuments.topP.documents.addDocument(docData = self.presenter.documentsDict[currentDoc])
            except KeyError: pass  
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
                selectedItem = self.filelist.GetItem(currentItems,0).GetText()
                print(''.join(["Deleting ",selectedItem, " from ", currentDoc]))
                try: 
                    del self.presenter.documentsDict[currentDoc].multipleMassSpectrum[selectedItem]
                    if len(self.presenter.documentsDict[currentDoc].multipleMassSpectrum.keys()) == 0: 
                        self.presenter.documentsDict[currentDoc].gotMultipleMS = False
                except KeyError: pass
                self.filelist.DeleteItem(currentItems)
                currentItems-=1
            # Update tree with new document
            try:
                self.presenter.view.panelDocuments.topP.documents.addDocument(docData = self.presenter.documentsDict[currentDoc])
            except KeyError: pass  

    def OnClearTable(self, evt):
        """
        This function clears the table without deleting any items from the document tree
        """
        # Ask if you want to delete all items
        dlg = dialogs.dlgBox(exceptionTitle='Are you sure?', 
                             exceptionMsg= "Are you sure you would like to clear the table??",
                             type="Question")
        if dlg == wx.ID_NO:
            msg = 'Cancelled clearing operation'
            self.presenter.view.SetStatusText(msg, 3)
            return
        self.filelist.DeleteAllItems()
        