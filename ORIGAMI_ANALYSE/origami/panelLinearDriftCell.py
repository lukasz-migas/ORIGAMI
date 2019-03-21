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

import wx, itertools
import wx.lib.mixins.listctrl as listmix
from operator import itemgetter

from ids import *
from toolbox import  str2num, str2int
from gui_elements.misc_dialogs import dlgBox


class panelLinearDriftCell(wx.Panel):

    def __init__(self, parent, config, icons, presenter):
        wx.Panel.__init__ (self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                            size=wx.Size(300, 400), style=wx.TAB_TRAVERSAL)

        self.parent = parent
        self.config = config
        self.presenter = presenter
        self.currentItem = None
        self.icons = icons

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.topP = topPanel(self, self.config, self.icons, self.presenter)
        sizer.Add(self.topP, 1, wx.EXPAND | wx.ALL, 1)
        self.bottomP = bottomPanel(self, self.config, self.icons, self.presenter)
        sizer.Add(self.bottomP, 1, wx.EXPAND | wx.ALL, 1)
        self.SetSizer(sizer)


class EditableListCtrl(wx.ListCtrl, listmix.TextEditMixin, listmix.CheckListCtrlMixin):
    """
    Editable list
    """

    def __init__(self, parent, ID=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.TextEditMixin.__init__(self)
        listmix.CheckListCtrlMixin.__init__(self)


class topPanel(wx.Panel):
    """
    Panel for Retention time list
    """

    def __init__(self, parent, config, icons, presenter):
        wx.Panel.__init__(self, parent=parent)

        self.config = config
        self.presenter = presenter  # wx.App
        self.icons = icons
        self.makeToolbar()
        self.makeListCtrl()

        self.reverse = False
        self.lastColumn = None

    def makeToolbar(self):
        # Create toolbar for the table

        self.Bind(wx.EVT_TOOL, self.onRemoveTool, id=ID_removeFilesMenuDT_RT)

        self.toolbar = wx.ToolBar(self, style=wx.TB_HORIZONTAL | wx.TB_DOCKABLE, id=wx.ID_ANY)
        self.toolbar.SetToolBitmapSize((16, 16))
        self.toolbar.AddLabelTool(ID_removeFilesMenuDT_RT, "", self.icons.iconsLib['remove16'],
                             shortHelp="Remove one from table")
        self.toolbar.AddLabelTool(ID_extractDriftVoltagesForEachIon, "", self.icons.iconsLib['extract16'],
                             shortHelp="Extract drift voltages listed in the table")
        self.toolbar.AddLabelTool(ID_processIons, "", self.icons.iconsLib['process16'],
                             shortHelp="Process ions")
        self.toolbar.AddLabelTool(ID_saveMZList, "", self.icons.iconsLib['save16'],
                             shortHelp="Save current list to .csv files")
        self.toolbar.AddLabelTool(ID_removeAllMZfromList, "", self.icons.iconsLib['bin16'],
                             shortHelp="Clear all ions from the table")
        self.toolbar.Realize()

    def onRemoveTool(self, evt):
        # Make bindings
        self.Bind(wx.EVT_MENU, self.OnDeleteAll, id=ID_removeSelectedFileDT_RT)
        self.Bind(wx.EVT_MENU, self.OnDeleteAll, id=ID_removeAllFilesDT_RT)
        self.Bind(wx.EVT_MENU, self.OnClearTable, id=ID_clearTableDT_RT)

        menu = wx.Menu()
        menu.Append(ID_clearTableDT_RT, "Clear table")
        menu.AppendSeparator()
        menu.Append(ID_removeSelectedFileDT_RT, "Remove selected item")
        menu.Append(ID_removeAllFilesDT_RT, "Remove all item")
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def makeListCtrl(self):
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.peaklist = EditableListCtrl(self, style=wx.LC_REPORT)
        self.peaklist.InsertColumn(0, 'min RT', width=70)
        self.peaklist.InsertColumn(1, 'max RT', width=60)
        self.peaklist.InsertColumn(2, '# scans', width=60)
        self.peaklist.InsertColumn(3, 'dv (V)', width=60)
        self.peaklist.InsertColumn(4, 'file', width=60)

        mainSizer.Add(self.toolbar, 0, wx.EXPAND, 0)
        mainSizer.Add(self.peaklist, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(mainSizer)

        self.Bind(wx.EVT_LIST_COL_CLICK, self.OnGetColumnClick)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnRightClickMenu)

    def OnRightClickMenu(self, evt):

        self.Bind(wx.EVT_MENU, self.OnDeleteAll, id=ID_removeSelectedPopupDT_RT)

        # Capture which item was clicked
        self.currentItem, __ = self.peaklist.HitTest(evt.GetPosition())
        self.menu = wx.Menu()
        self.menu.Append(ID_removeSelectedPopupDT_RT, "Remove item")
        self.PopupMenu(self.menu)
        self.menu.Destroy()
        self.SetFocus()

    def onCheckForDuplicates(self, rtStart=None, rtEnd=None):
        """
        Check whether the value being added is already present in the table
        """
        currentItems = self.peaklist.GetItemCount() - 1
        while (currentItems >= 0):
            rtStartInTable = self.peaklist.GetItem(currentItems, 0).GetText()
            rtEndInTable = self.peaklist.GetItem(currentItems, 1).GetText()
            if rtStartInTable == rtStart and rtEndInTable == rtEnd:
                print('Item already in the table.')
                currentItems = 0
                return True
            else:
                currentItems -= 1
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
                #  We want to make sure the first 3 columns are numbers
                if col == 0 or col == 1 or col == 2 or col == 3:
                    itemData = str2num(item.GetText())
                    if itemData == None: itemData = 0
                    tempRow.append(itemData)
                else:
                    tempRow.append(item.GetText())
            tempData.append(tempRow)

        # Sort data
        tempData.sort(key=itemgetter(column), reverse=self.reverse)
        # Clear table and reinsert data
        self.peaklist.DeleteAllItems()
        for row in range(rows):
            self.peaklist.Append(tempData[row])

    def onReplotRectanglesDT_RT(self, evt):
        """
        This function replots the rectangles in the RT window during Linear DT mode
        """
        count = self.peaklist.GetItemCount()
        currentDoc = self.presenter.currentDoc
        if currentDoc == "Current documents": return
        document = self.presenter.documentsDict[currentDoc]
        # Replot RT for current document
        rtX = document.RT['xvals']
        rtY = document.RT['yvals']
        xlabel = document.RT['xlabels']
        color = document.lineColour
        style = document.style
        # Change panel and plot
        self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['RT'])
        self.presenter.onPlotRT2(rtX, rtY, xlabel, color, style)
        if count == 0: return
        ymin = 0
        height = 1.0
        last = self.peaklist.GetItemCount() - 1
        # Iterate over the list and plot rectangle one by one
        for row in range(count):
            xmin = str2num(self.peaklist.GetItem(itemId=row, col=0).GetText())
            xmax = str2num(self.peaklist.GetItem(itemId=row, col=1).GetText())
            width = xmax - xmin
            if row == last:
                self.presenter.addRectRT(xmin, ymin, width, height, color=self.config.annotColor,
                               alpha=(self.config.annotTransparency / 100),
                               repaint=True)
            else:
                self.presenter.addRectRT(xmin, ymin, width, height, color=self.config.annotColor,
                               alpha=(self.config.annotTransparency / 100),
                               repaint=False)

    def OnDeleteAll(self, evt, ticked=False, selected=False, itemID=None):
        """ 
        This function removes selected or all MassLynx files from the 
        combined document
        """
        currentItems = self.peaklist.GetItemCount() - 1
        if evt.GetId() == ID_removeSelectedFileDT_RT:
            while (currentItems >= 0):
                item = self.peaklist.IsChecked(index=currentItems)
                if item == True:
                    self.peaklist.DeleteItem(currentItems)
                    currentItems -= 1
                else:
                    currentItems -= 1
        elif evt.GetId() == ID_removeSelectedPopupDT_RT:
            self.peaklist.DeleteItem(self.currentItem)
        else:
            # Ask if you want to delete all items
            dlg = dlgBox(exceptionTitle='Are you sure?',
                                 exceptionMsg="Are you sure you would like to delete ALL RT peaks from the table?",
                                 type="Question")
            if dlg == wx.ID_NO:
                print('Cancelled operation')
                return
            # Iterate over all items
            while (currentItems >= 0):
                self.peaklist.DeleteItem(currentItems)
                currentItems -= 1

        # Replot rectangles
        self.onReplotRectanglesDT_RT(evt=None)

    def OnClearTable(self, evt):
        """
        This function clears the table without deleting any items from the document tree
        """
        # Ask if you want to delete all items
        dlg = dlgBox(exceptionTitle='Are you sure?',
                             exceptionMsg="Are you sure you would like to clear the table??",
                             type="Question")
        if dlg == wx.ID_NO:
            print('Cancelled operation')
            return
        self.peaklist.DeleteAllItems()

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
                item = self.peaklist.GetItem(itemId=row, col=col)
                #  We want to make sure certain columns are numbers
                if col == 0 or col == 1 or col == 2 or col == 3:
                    itemData = str2num(item.GetText())
                    if itemData == None: itemData = 0
                    tempRow.append(itemData)
                else:
                    tempRow.append(item.GetText())
            tempData.append(tempRow)
        tempData.sort()
        tempData = list(item for item, _ in itertools.groupby(tempData))
        rows = len(tempData)
        self.peaklist.DeleteAllItems()
        print('Removing duplicates')
        for row in range(rows):
            self.peaklist.Append(tempData[row])

        if evt is None: return
        else:
            evt.Skip()

    def OnGetItemInformation(self, itemID, return_list=False):
        # get item information
        information = {'start':str2int(self.peaklist.GetItem(itemID, self.config.driftTopColNames['start']).GetText()),
                       'end':str2int(self.peaklist.GetItem(itemID, self.config.driftTopColNames['end']).GetText()),
                       'scans':str2int(self.peaklist.GetItem(itemID, self.config.driftTopColNames['end']).GetText()),
                       'drift_voltage':str2num(self.peaklist.GetItem(itemID, self.config.driftTopColNames['drift_voltage']).GetText()),
                       'document':self.peaklist.GetItem(itemID, self.config.driftTopColNames['filename']).GetText()
                       }

        if return_list:
            start = information['start']
            end = information['end']
            scans = information['scans']
            drift_voltage = information['drift_voltage']
            document = information['document']
            return start, end, scans, drift_voltage, document

        return information

    def onClearItems(self, document):
        """
        @param document: title of the document to be removed from the list
        """
        row = self.peaklist.GetItemCount() - 1
        while (row >= 0):
            info = self.OnGetItemInformation(itemID=row)
            print(info)
            if info['document'] == document:
                self.peaklist.DeleteItem(row)
                row -= 1
            else:
                row -= 1


class bottomPanel(wx.Panel):
    """
    Panel for ion list
    """

    def __init__(self, parent, config, icons, presenter):
        wx.Panel.__init__(self, parent=parent)

        self.config = config
        self.presenter = presenter  # wx.App
        self.icons = icons
        self.makeToolbar()
        self.makeListCtrl()

        self.reverse = False
        self.lastColumn = None

    def makeToolbar(self):
        # Create toolbar for the table

        self.Bind(wx.EVT_TOOL, self.onAddTool, id=ID_addFilesMenuDT)
        self.Bind(wx.EVT_TOOL, self.onRemoveTool, id=ID_removeFilesMenuDT)
        self.Bind(wx.EVT_TOOL, self.onSaveTool, id=ID_saveFilesMenuDT)

        self.toolbar = wx.ToolBar(self, style=wx.TB_HORIZONTAL | wx.TB_DOCKABLE, id=wx.ID_ANY)
        self.toolbar.SetToolBitmapSize((16, 16))
        self.toolbar.AddLabelTool(ID_addFilesMenuDT, "", self.icons.iconsLib['add16'],
                             shortHelp="Add...")
        self.toolbar.AddLabelTool(ID_removeFilesMenuDT, "", self.icons.iconsLib['remove16'],
                             shortHelp="Remove...")
        self.toolbar.AddLabelTool(ID_saveFilesMenuDT, "", self.icons.iconsLib['save16'],
                             shortHelp="Save...")
        self.toolbar.Realize()

    def makeListCtrl(self):

        self.Bind(wx.EVT_TOOL, self.onRemoveTool, id=ID_removeFilesMenuDT)

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.peaklist = EditableListCtrl(self, style=wx.LC_REPORT)
        self.peaklist.InsertColumn(0, 'min m/z', width=70)
        self.peaklist.InsertColumn(1, 'max m/z', width=60)
        self.peaklist.InsertColumn(2, '% int', width=40)
        self.peaklist.InsertColumn(3, 'z', width=40)
        self.peaklist.InsertColumn(4, 'file', width=40)

        mainSizer.Add(self.toolbar, 0, wx.EXPAND, 0)
        mainSizer.Add(self.peaklist, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(mainSizer)

        self.Bind(wx.EVT_LIST_COL_CLICK, self.OnGetColumnClick)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnRightClickMenu)

    def OnRightClickMenu(self, evt):

        self.Bind(wx.EVT_MENU, self.OnDeleteAll, id=ID_removeSelectedPopupDT)

        # Capture which item was clicked
        self.currentItem, __ = self.peaklist.HitTest(evt.GetPosition())
        self.menu = wx.Menu()
        self.menu.Append(ID_removeSelectedPopupDT, "Remove item")
        self.PopupMenu(self.menu)
        self.menu.Destroy()
        self.SetFocus()

    def onAddTool(self, evt):
        # Make bindings
#         self.Bind(wx.EVT_MENU, self.OnDeleteAll, id=ID_removeSelectedFileDT)

        menu = wx.Menu()
        menu.Append(ID_addIonListDT, "Add list...")
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def onRemoveTool(self, evt):
        # Make bindings
        self.Bind(wx.EVT_MENU, self.OnDeleteAll, id=ID_removeSelectedFileDT)
        self.Bind(wx.EVT_MENU, self.OnDeleteAll, id=ID_removeAllFilesDT)
        self.Bind(wx.EVT_MENU, self.OnClearTable, id=ID_clearTableDT)

        menu = wx.Menu()
        menu.Append(ID_clearTableDT, "Clear table")
        menu.Append(ID_removeSelectedFileDT, "Remove selected item")
        menu.Append(ID_removeAllFilesDT, "Remove all item")
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def onSaveTool(self, evt):
        # Make bindings
#         self.Bind(wx.EVT_MENU, self.OnDeleteAll, id=ID_removeSelectedFileDT)

        menu = wx.Menu()
        menu.Append(ID_saveAllIon1D_DT, "Export 1D IM-MS to .csv (all)")
        menu.Append(ID_saveSelectedIon1D_DT, "Export 1D IM-MS to .csv (selected)")
        menu.AppendSeparator()
        menu.Append(ID_saveIonListDT, "Export peak list...")
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def onCheckForDuplicates(self, mzStart=None, mzEnd=None):
        """
        Check whether the value being added is already present in the table
        """
        currentItems = self.peaklist.GetItemCount() - 1
        while (currentItems >= 0):
            mzStartInTable = self.peaklist.GetItem(currentItems, 0).GetText()
            mzEndInTable = self.peaklist.GetItem(currentItems, 1).GetText()
            if mzStartInTable == mzStart and mzEndInTable == mzEnd:
                print('Ion already in the table')
                currentItems = 0
                return True
            else:
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
                item = self.peaklist.GetItem(itemId=row, col=col)
                #  We want to make sure certain columns are numbers
                if col == 0 or col == 1 or col == 2 or col == 3:
                    itemData = str2num(item.GetText())
                    if itemData == None: itemData = 0
                    tempRow.append(itemData)
                else:
                    tempRow.append(item.GetText())
            tempData.append(tempRow)
        tempData.sort()
        tempData = list(item for item, _ in itertools.groupby(tempData))
        rows = len(tempData)
        self.peaklist.DeleteAllItems()
        print('Removing duplicates')

        for row in range(rows):
            self.peaklist.Append(tempData[row])

        if evt is None: return
        else:
            evt.Skip()

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
                #  We want to make sure the first 3 columns are numbers
                if col == 0 or col == 1 or col == 2:
                    itemData = str2num(item.GetText())
                    if itemData == None: itemData = 0
                    tempRow.append(itemData)
                elif col == 3:
                    itemData = str2int(item.GetText())
                    if itemData == None: itemData = 0
                    tempRow.append(itemData)
                else:
                    tempRow.append(item.GetText())
            tempData.append(tempRow)

        # Sort data
        tempData.sort(key=itemgetter(column), reverse=self.reverse)
        # Clear table and reinsert data
        self.peaklist.DeleteAllItems()
        for row in range(rows):
            self.peaklist.Append(tempData[row])

    def OnClearTable(self, evt):
        """
        This function clears the table without deleting any items from the document tree
        """
        # Ask if you want to delete all items
        dlg = dlgBox(exceptionTitle='Are you sure?',
                             exceptionMsg="Are you sure you would like to clear the table??",
                             type="Question")
        if dlg == wx.ID_NO:
            print('Cancelled operation')
            return
        self.peaklist.DeleteAllItems()

    def getCurrentDocument(self, docNameOnly=False):
        """
        Determines what is the currently selected document
        Gives an 'None' error when wrong document has been selected
        """
        # Now insert it into the document
        try:
            currentDoc = self.presenter.view.panelDocuments.documents.enableCurrentDocument()
        except:
            return None
        if currentDoc == 'Current documents':
            print('There are no documents in the tree')
            return currentDoc
        document = self.presenter.documentsDict[currentDoc]
        if document.dataType != 'Type: Multifield Linear DT':
            print('Make sure you select the correct dataset - Multifield Linear DT')
            return None
        if docNameOnly: return currentDoc
        else: return document

    def OnDeleteAll(self, evt, ticked=False, selected=False, itemID=None):
        """ 
        This function removes selected or all MassLynx files from the 
        combined document
        """
        currentItems = self.peaklist.GetItemCount() - 1
        if evt.GetId() == ID_removeSelectedFileDT:
            while (currentItems >= 0):
                item = self.peaklist.IsChecked(index=currentItems)
                if item == True:
                    selectedItem = self.peaklist.GetItem(currentItems, 4).GetText()
                    mzStart = self.peaklist.GetItem(currentItems, 0).GetText()
                    mzEnd = self.peaklist.GetItem(currentItems, 1).GetText()
                    selectedIon = ''.join([str(mzStart), '-', str(mzEnd)])
                    print((''.join(["Deleting ", selectedIon, " from ", selectedItem])))
                    try:
                        del self.presenter.documentsDict[selectedItem].IMS1DdriftTimes[selectedIon]
                        if len(list(self.presenter.documentsDict[selectedItem].IMS1DdriftTimes.keys())) == 0:
                            self.presenter.documentsDict[selectedItem].gotExtractedDriftTimes = False
                    except KeyError:
                        pass
                    self.peaklist.DeleteItem(currentItems)
                    currentItems -= 1
                else:
                    currentItems -= 1
            try:
                self.presenter.view.panelDocuments.documents.addDocument(docData=self.presenter.documentsDict[selectedItem])
            except KeyError: pass
        elif evt.GetId() == ID_removeSelectedPopupDT:
            selectedItem = self.peaklist.GetItem(self.currentItem, 4).GetText()
            mzStart = self.peaklist.GetItem(self.currentItem, 0).GetText()
            mzEnd = self.peaklist.GetItem(self.currentItem, 1).GetText()
            selectedIon = ''.join([str(mzStart), '-', str(mzEnd)])
            print((''.join(["Deleting ", selectedIon, " from ", selectedItem])))
            try:
                del self.presenter.documentsDict[selectedItem].IMS1DdriftTimes[selectedIon]
                if len(list(self.presenter.documentsDict[selectedItem].IMS1DdriftTimes.keys())) == 0:
                    self.presenter.documentsDict[selectedItem].gotExtractedDriftTimes = False
            except KeyError:
                pass
            self.peaklist.DeleteItem(self.currentItem)
        else:
            # Ask if you want to delete all items
            dlg = dlgBox(exceptionTitle='Are you sure?',
                                 exceptionMsg="Are you sure you would like to delete ALL ions from the table?",
                                 type="Question")
            if dlg == wx.ID_NO:
                print('Cancelled operation')
                return
            # Iterate over all items
            while (currentItems >= 0):
                selectedItem = self.peaklist.GetItem(currentItems, 4).GetText()
                mzStart = self.peaklist.GetItem(currentItems, 0).GetText()
                mzEnd = self.peaklist.GetItem(currentItems, 1).GetText()
                selectedIon = ''.join([str(mzStart), '-', str(mzEnd)])
                print((''.join(["Deleting ", selectedIon, " from ", selectedItem])))
                try:
                    del self.presenter.documentsDict[selectedItem].IMS1DdriftTimes[selectedIon]
                    if len(list(self.presenter.documentsDict[selectedItem].IMS1DdriftTimes.keys())) == 0:
                        self.presenter.documentsDict[selectedItem].gotExtractedDriftTimes = False
                except KeyError:
                    pass
                self.peaklist.DeleteItem(currentItems)
                currentItems -= 1
                try:
                    self.presenter.view.panelDocuments.documents.addDocument(docData=self.presenter.documentsDict[selectedItem])
                except KeyError: pass

        self.onReplotRectanglesDT_MZ(evt=None)

    def onReplotRectanglesDT_MZ(self, evt):
        """
        This function replots the rectangles in the RT window during Linear DT mode
        """
        count = self.peaklist.GetItemCount()
        currentDoc = self.presenter.currentDoc
        if currentDoc == "Current documents": return
        document = self.presenter.documentsDict[currentDoc]
        # Replot RT for current document
        msX = document.massSpectrum['xvals']
        msY = document.massSpectrum['yvals']
        try: xlimits = document.massSpectrum['xlimits']
        except KeyError:
            xlimits = [document.parameters['startMS'], document.parameters['endMS']]
        # Change panel and plot
        self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['MS'])

        name_kwargs = {"document":document.title, "dataset": "Mass Spectrum"}
        self.presenter.view.panelPlots.on_plot_MS(msX, msY, xlimits=xlimits, **name_kwargs)
        if count == 0: return
        ymin = 0
        height = 1.0
        last = self.peaklist.GetItemCount() - 1
        # Iterate over the list and plot rectangle one by one
        for row in range(count):
            xmin = str2num(self.peaklist.GetItem(itemId=row, col=0).GetText())
            xmax = str2num(self.peaklist.GetItem(itemId=row, col=1).GetText())
            width = xmax - xmin
            if row == last:
                self.presenter.addRectMS(xmin, ymin, width, height, color=self.config.annotColor,
                                         alpha=(self.config.annotTransparency / 100),
                                         repaint=True)
            else:
                self.presenter.addRectMS(xmin, ymin, width, height, color=self.config.annotColor,
                                         alpha=(self.config.annotTransparency / 100),
                                         repaint=False)

    def OnGetItemInformation(self, itemID, return_list=False):
        # get item information
        information = {'start':str2num(self.peaklist.GetItem(itemID, self.config.driftBottomColNames['start']).GetText()),
                       'end':str2num(self.peaklist.GetItem(itemID, self.config.driftBottomColNames['end']).GetText()),
                       'intensity':str2num(self.peaklist.GetItem(itemID, self.config.driftBottomColNames['intensity']).GetText()),
                       'charge':str2int(self.peaklist.GetItem(itemID, self.config.driftBottomColNames['charge']).GetText()),
                       'document':self.peaklist.GetItem(itemID, self.config.driftBottomColNames['filename']).GetText()
                       }

        if return_list:
            start = information['start']
            end = information['end']
            intensity = information['intensity']
            charge = information['charge']
            document = information['document']
            return start, end, intensity, charge, document

        return information

    def onClearItems(self, document):
        """
        @param document: title of the document to be removed from the list
        """
        row = self.peaklist.GetItemCount() - 1
        while (row >= 0):
            info = self.OnGetItemInformation(itemID=row)
            print(info)
            if info['document'] == document:
                self.peaklist.DeleteItem(row)
                row -= 1
            else:
                row -= 1

