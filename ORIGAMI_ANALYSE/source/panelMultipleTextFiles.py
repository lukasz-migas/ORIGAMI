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
# import origamiIcons as icons
from ids import *
import wx.lib.mixins.listctrl  as  listmix
from wx.lib.agw import ultimatelistctrl as ULC
import dialogs as dialogs
from toolbox import isempty, str2num
from operator import itemgetter
import itertools
from numpy import arange


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
     
        
class EditableListCtrl(wx.ListCtrl, listmix.TextEditMixin, listmix.CheckListCtrlMixin):
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
        if event.m_col == 0 or event.m_col == 6 or event.m_col==7:
            event.Veto()
        else:
            event.Skip()

        
class topPanel(wx.Panel):
    def __init__(self, parent, icons, presenter, config):
        wx.Panel.__init__(self, parent=parent)
        
        self.presenter = presenter # wx.App
        self.config = config
        self.icons = icons
        self.makeToolbar()
        self.makeListCtrl()
        self.allChecked = True
        self.reverse = False
        self.lastColumn = None
        self.listOfSelected = []
        
    def makeListCtrl(self):
        mainSizer = wx.BoxSizer( wx.VERTICAL )
        self.filelist = EditableListCtrl(self, style=wx.LC_REPORT)
        self.filelist.InsertColumn(0, u'File name', width=80)
        self.filelist.InsertColumn(1, u'Start CE', width=50)
        self.filelist.InsertColumn(2, u'End CE', width=45)
        self.filelist.InsertColumn(3, u'Colormap', width=80)
        self.filelist.InsertColumn(4, u'\N{GREEK SMALL LETTER ALPHA}', width=40)
        self.filelist.InsertColumn(5, u'Label', width=50)
        self.filelist.InsertColumn(6, u'Shape', width=80)
        self.filelist.InsertColumn(7, u'Tag', width=50)

        mainSizer.Add(self.toolbar, 0, wx.EXPAND, 0)
        mainSizer.Add(self.filelist, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizer( mainSizer )
        
        self.Bind(wx.EVT_LIST_COL_CLICK, self.OnGetColumnClick)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnRightClickMenu)
        
    def makeToolbar(self):
        
        # Make bindings
        self.Bind(wx.EVT_TOOL, self.onAddItems, id=ID_addTextFilesToList)
        self.Bind(wx.EVT_TOOL, self.onRemoveItems, id=ID_removeTextFilesMenu)
        self.Bind(wx.EVT_TOOL, self.onProcessItems, id=ID_processTextFilesMenu)
        self.Bind(wx.EVT_TOOL, self.OnCheckAllItems, id=ID_checkAllItems_Text)
        
        
        # Create toolbar for the table        
        self.toolbar = wx.ToolBar(self, style=wx.TB_HORIZONTAL | wx.TB_DOCKABLE, id = wx.ID_ANY) 
        self.toolbar.SetToolBitmapSize((16, 16))
        self.toolbar.AddTool(ID_checkAllItems_Text, self.icons.iconsLib['check16'] , 
                              shortHelpString="Check all items") 
        self.toolbar.AddTool(ID_addTextFilesToList, self.icons.iconsLib['add16'] , 
                              shortHelpString="Add...") 
        self.toolbar.AddTool(ID_removeTextFilesMenu, self.icons.iconsLib['remove16'], 
                             shortHelpString="Remove...")
        self.toolbar.AddTool(ID_processTextFilesMenu, self.icons.iconsLib['process16'], 
                             shortHelpString="Process...")
        self.toolbar.AddTool(ID_overlayTextFromList, self.icons.iconsLib['overlay16'], 
                             shortHelpString="Overlay currently selected ions\tAlt+W")
        self.combo = wx.ComboBox(self.toolbar, ID_textSelectOverlayMethod, value= "Mask",
                                 choices=self.config.overlayChoices,
                                 style=wx.CB_READONLY, size=(110,-1))
        self.toolbar.AddControl(self.combo)
        self.toolbar.AddSeparator()

        self.toolbar.Realize()     
        
    def onAddItems(self, evt):
        
        self.Bind(wx.EVT_MENU, self.presenter.onAddBlankDocument, id=ID_addNewOverlayDoc)
        
        menu = wx.Menu()
        menu.Append(ID_openTextFiles, "Add files\tCtrl+W")
        menu.AppendSeparator()
        menu.Append(ID_addNewOverlayDoc, "Add new document\tAlt+D")
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()
        
    def onRemoveItems(self, evt):
        
        # Make bindings 
        self.Bind(wx.EVT_MENU, self.OnDeleteAll, id=ID_removeAllFilesFromList)
        self.Bind(wx.EVT_MENU, self.OnDeleteAll, id=ID_removeSelectedFilesFromList)
        self.Bind(wx.EVT_MENU, self.OnClearTable, id=ID_clearTableText)
        
        menu = wx.Menu()
        menu.Append(ID_clearTableText, "Clear table")
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

    def OnRightClickMenu(self, evt): 
        
        # Make bindings
        self.Bind(wx.EVT_MENU, self.OnListGet2DIMMS, id=ID_get2DplotText)
        self.Bind(wx.EVT_MENU, self.OnListGet2DIMMS, id=ID_get2DplotTextWithProcss)
        self.Bind(wx.EVT_MENU, self.OnDeleteAll, id=ID_removeFileFromListPopup)
        
        self.currentItem, flags = self.filelist.HitTest(evt.GetPosition())
        menu = wx.Menu()
        menu.Append(ID_get2DplotText, "Show 2D IM-MS plot")
        menu.Append(ID_get2DplotTextWithProcss, "Process and show 2D IM-MS plot")
        menu.AppendSeparator()
        menu.Append(ID_removeFileFromListPopup, "Remove item")
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()
        
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
        
    def OnListGet2DIMMS(self, evt):
        """
        This function extracts 2D array and plots it in 2D/3D
        """
        
        selectedItem = self.filelist.GetItem(self.currentItem,
                                             self.config.textlistColNames['filename']).GetText()
        tag = self.filelist.GetItem(self.currentItem,
                                    self.config.textlistColNames['tag']).GetText()
#         self.filelist.SetItemBackgroundColour(item=self.currentItem, col=wx.RED)
        currentDocument = self.presenter.documentsDict[selectedItem]
        
        if currentDocument.dataType == 'Type: Comparison':
            data = currentDocument.IMS2DcompData[tag]
        else:
            data = currentDocument.IMS2D
            
        # Extract 2D data from the document
        zvals, xvals, xlabel, yvals, ylabel, cmap = self.presenter.get2DdataFromDictionary(dictionary=data,
                                                                                           dataType='plot',compact=False)
        
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
            zvals = self.presenter.process2Ddata(zvals=zvals)
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
                    selectedItem = self.filelist.GetItem(currentItems,0).GetText()
                    print('TEXT:', selectedItem)
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
            selectedItem = self.filelist.GetItem(self.currentItem,0).GetText()
            
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
                    selectedItem = self.filelist.GetItem(currentItems,0).GetText()
                    print('TEXT:', selectedItem)
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
            fileInTable = self.filelist.GetItem(currentItems,0).GetText()
            if fileInTable == fileName:
                print('File '+ fileInTable + ' already in table - skipping')
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
                if col==1 or col==2 or col==4:
                    itemData = str2num(item.GetText())
                    if itemData == None: itemData = 0
                    tempRow.append(itemData)
                else:
                    tempRow.append(item.GetText())
            tempData.append(tempRow)
        tempData.sort()
        tempData = list(item for item,_ in itertools.groupby(tempData))
        rows = len(tempData)
        self.filelist.DeleteAllItems()
        print('Removing duplicates')
        for row in range(rows):
            self.filelist.Append(tempData[row])
            
        if evt is None: return
        else:
            evt.Skip()

    def OnClearTable(self, evt):
        """
        This function clears the table without deleting any items from the document tree
        """
        # Ask if you want to delete all items
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
                #  We want to make sure the first 3 columns are numbers
                if col==1 or col==2 or col==4:
                    itemData = str2num(item.GetText())
                    if itemData == None: itemData = 0
                    tempRow.append(itemData)
                else:
                    tempRow.append(item.GetText())
            tempRow.append(self.filelist.IsChecked(index=row))
            tempData.append(tempRow)
            
        
        # Sort data  
        tempData.sort(key = itemgetter(column), reverse=self.reverse)
        # Clear table and reinsert data
        self.filelist.DeleteAllItems()
        
        checkData = []
        for check in tempData:
            checkData.append(check[-1])
            del check[-1]
            
        # Reinstate data
        rowList = arange(len(tempData))
        for row, check in zip(rowList,checkData):
            self.filelist.Append(tempData[row])
            self.filelist.CheckItem(row, check)
