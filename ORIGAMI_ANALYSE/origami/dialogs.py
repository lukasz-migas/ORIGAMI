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

# Load libraries
import wx, itertools, os, webbrowser, wx.html
from operator import itemgetter
from numpy import arange, transpose, argmax, round, max, median, min, argmin
from numpy import sum as npsum
from wx.lib.pubsub import pub
import wx.lib.mixins.listctrl as listmix

from help import OrigamiHelp as help
from icons import IconContainer as icons
import plots as plots
from ids import (ID_addNewOverlayDoc, ID_helpNewVersion, ID_saveAllDocuments)
from styles import makeCheckbox, validator, makeSuperTip, makeStaticBox, makeToggleBtn
from toolbox import (str2num, str2int, convertRGB1to255, convertRGB255to1, num2str,
                             isnumber, getNarrow1Ddata, dir_extra, findPeakMax, find_nearest,
                             MidpointNormalize)
from unidec_modules.unidectools import make_peak_shape, isolated_peak_fit


def dlgBox(exceptionTitle="", exceptionMsg="", type="Error", exceptionPrint=True):
    """
    Generic message box
    """

    if type == "Error":
        dlgStyle = wx.OK | wx.ICON_ERROR
    elif type == "Info":
        dlgStyle = wx.OK | wx.ICON_INFORMATION
    elif type == "Stop":
        dlgStyle = wx.OK | wx.ICON_STOP
    elif type == "Warning":
        dlgStyle = wx.OK | wx.ICON_EXCLAMATION
    elif type == "Question":
        dlgStyle = wx.YES_NO | wx.ICON_QUESTION

    if exceptionPrint:
        print(exceptionMsg)
    dlg = wx.MessageDialog(None, exceptionMsg, exceptionTitle, dlgStyle)
    result = dlg.ShowModal()

    if type == "Question":
        return result


def dlgAsk(message='', defaultValue=''):
    dlg = wx.TextEntryDialog(None,  # parent
                             message,
                             defaultValue=defaultValue)
    if dlg.ShowModal() == wx.ID_CANCEL:
        return False

    result = dlg.GetValue()
    dlg.Destroy()
    return result


class ListCtrl(wx.ListCtrl):
    """ListCtrl"""

    def __init__(self, parent, id=-1, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.LC_REPORT):
        wx.ListCtrl.__init__(self, parent, id, pos, size, style)


class SortedCheckListCtrl(wx.ListCtrl,
                          listmix.CheckListCtrlMixin,
                          listmix.ColumnSorterMixin):
    """ListCtrl"""

    def __init__(self, parent, id=-1, pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=wx.LC_REPORT, columns=0):
        wx.ListCtrl.__init__(self, parent, id, pos, size, style)
        listmix.CheckListCtrlMixin.__init__(self)
        listmix.ColumnSorterMixin.__init__(self, columns)

        self.itemDataMap = []

    def GetListCtrl(self):
        return self


class EditableListCtrl(wx.ListCtrl, listmix.CheckListCtrlMixin):
    """
    Editable list
    """

    def __init__(self, parent, ID=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.CheckListCtrlMixin.__init__(self)


class panelAsk(wx.Dialog):
    """
    Duplicate ions
    """

    def __init__(self, parent, presenter, **kwargs):
        wx.Dialog.__init__(self, parent, -1, 'Edit parameters...', size=(400, 300),
                              style=wx.DEFAULT_FRAME_STYLE & ~
                              (wx.RESIZE_BORDER | wx.RESIZE_BOX | wx.MAXIMIZE_BOX))

        self.parent = parent
        self.presenter = presenter

        self.item_label = kwargs['static_text']
        self.item_value = kwargs['value_text']
        self.item_validator = kwargs['validator']

        if kwargs['keyword'] == 'charge': self.SetTitle("Assign charge...")
        elif kwargs['keyword'] == 'alpha': self.SetTitle("Assign transparency...")
        elif kwargs['keyword'] == 'mask': self.SetTitle("Assign mask...")
        elif kwargs['keyword'] == 'min_threshold': self.SetTitle("Assign minimum threshold...")
        elif kwargs['keyword'] == 'max_threshold': self.SetTitle("Assign maximum threshold...")
        elif kwargs['keyword'] == 'label': self.SetTitle("Assign label...")

        # make gui items
        self.makeGUI()

        wx.EVT_CLOSE(self, self.onClose)
        self.Bind(wx.EVT_CHAR_HOOK, self.OnKey)

    def OnKey(self, evt):
        keyCode = evt.GetKeyCode()
        if keyCode == wx.WXK_ESCAPE:
            self.onClose(None)
        elif keyCode in [wx.WXK_RETURN, 370]:  # enter or enter on numpad
            self.onOK(None)

        if evt != None:
            evt.Skip()

    def onClose(self, evt):
        """Destroy this frame."""

#         self.onApply(evt=None)
#         if self.item_validator == 'integer':
#             self.parent.ask_value = int(self.item_value)
#         elif self.item_validator == 'float':
#             self.parent.ask_value = float(self.item_value)

        self.parent.ask_value = None
        self.Destroy()
    # ----

    def onOK(self, evt):
        self.onApply(evt=None)

        if self.item_validator == 'integer':
            self.parent.ask_value = int(self.item_value)
        elif self.item_validator == 'float':
            self.parent.ask_value = float(self.item_value)
        elif self.item_validator == 'str':
            self.parent.ask_value = self.item_value

        self.EndModal(wx.OK)

    def makeGUI(self):

        # make panel
        panel = self.makePanel()

        # pack element
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(panel, 0, wx.EXPAND, 0)

        # bind
        self.okBtn.Bind(wx.EVT_BUTTON, self.onOK, id=wx.ID_OK)
        self.cancelBtn.Bind(wx.EVT_BUTTON, self.onClose)

        # fit layout
        self.mainSizer.Fit(self)
        self.SetSizer(self.mainSizer)

    def makePanel(self):

        panel = wx.Panel(self, -1)
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        self.input_label = wx.StaticText(panel, -1, "Enter value:")
        self.input_label.SetLabel(self.item_label)

        if self.item_validator == 'integer':
            self.input_value = wx.SpinCtrlDouble(panel, -1,
                                                 value=str(self.item_value),
                                                 min=1, max=200, initial=0, inc=1,
                                                 size=(90, -1))
        elif self.item_validator == 'float':
            self.input_value = wx.SpinCtrlDouble(panel, -1,
                                                 value=str(self.item_value),
                                                 min=0, max=1, initial=0, inc=0.1,
                                                 size=(90, -1))

        self.input_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)

        self.okBtn = wx.Button(panel, wx.ID_OK, "Select", size=(-1, 22))
        self.cancelBtn = wx.Button(panel, -1, "Cancel", size=(-1, 22))

        GRIDBAG_VSPACE = 7
        GRIDBAG_HSPACE = 5
        PANEL_SPACE_MAIN = 10

        # pack elements
        grid = wx.GridBagSizer(GRIDBAG_VSPACE, GRIDBAG_HSPACE)

        grid.Add(self.input_label, (0, 0), wx.GBSpan(2, 3), flag=wx.ALIGN_RIGHT | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)

        grid.Add(self.input_value, (0, 3), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)

        grid.Add(self.okBtn, (2, 2), wx.GBSpan(1, 1))
        grid.Add(self.cancelBtn, (2, 3), wx.GBSpan(1, 1))

        mainSizer.Add(grid, 0, wx.ALIGN_CENTER | wx.ALL, PANEL_SPACE_MAIN)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)

        return panel

    def onApply(self, evt):
        self.item_value = self.input_value.GetValue()

        if evt != None:
            evt.Skip()


class panelSelectDocument(wx.Dialog):
    """
    Duplicate ions
    """

    def __init__(self, parent, presenter, keyList, allowNewDoc=True):
        wx.Dialog.__init__(self, parent, -1, 'Select document...', size=(400, 300),
                              style=wx.DEFAULT_FRAME_STYLE & ~
                              (wx.RESIZE_BORDER | wx.RESIZE_BOX | wx.MAXIMIZE_BOX))

        self.parent = parent
        self.presenter = presenter
        self.documentList = keyList
        self.allowNewDoc = allowNewDoc

        # make gui items
        self.makeGUI()
        self.CentreOnParent()
        self.SetFocus()

        wx.EVT_CLOSE(self, self.onClose)

    def onClose(self, evt):
        """Destroy this frame."""
        # If pressed Close, return nothing of value
        self.presenter.currentDoc = None
        self.current_document = None

        self.Destroy()
    # ----

    def makeGUI(self):

        # make panel
        panel = self.makeSelectionPanel()

        # pack element
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(panel, 0, wx.EXPAND, 0)

        # bind
        self.okBtn.Bind(wx.EVT_BUTTON, self.onSelectDocument, id=wx.ID_ANY)
        self.addBtn.Bind(wx.EVT_BUTTON, self.onNewDocument, id=ID_addNewOverlayDoc)
        self.cancelBtn.Bind(wx.EVT_BUTTON, self.onClose)

        # fit layout
        self.mainSizer.Fit(self)
        self.SetSizer(self.mainSizer)

    def makeSelectionPanel(self):

        panel = wx.Panel(self, -1)
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        documentList_label = wx.StaticText(panel, -1, "Select document:")
        self.documentList_choice = wx.Choice(panel, -1, choices=self.documentList, size=(300, -1))
        self.documentList_choice.Select(0)

        self.okBtn = wx.Button(panel, wx.ID_OK, "Select", size=(-1, 22))
        self.addBtn = wx.Button(panel, ID_addNewOverlayDoc, "Add new document", size=(-1, 22))
        self.cancelBtn = wx.Button(panel, -1, "Cancel", size=(-1, 22))

        # In some cases, we don't want to be able to create new document!
        if not self.allowNewDoc: self.addBtn.Disable()
        else: self.addBtn.Enable()

        GRIDBAG_VSPACE = 7
        GRIDBAG_HSPACE = 5
        PANEL_SPACE_MAIN = 10

        # pack elements
        grid = wx.GridBagSizer(GRIDBAG_VSPACE, GRIDBAG_HSPACE)

        grid.Add(documentList_label, (0, 0))
        grid.Add(self.documentList_choice, (0, 1), wx.GBSpan(1, 3))

        grid.Add(self.okBtn, (1, 0), wx.GBSpan(1, 1))
        grid.Add(self.addBtn, (1, 1), wx.GBSpan(1, 1))
        grid.Add(self.cancelBtn, (1, 2), wx.GBSpan(1, 1))

        mainSizer.Add(grid, 0, wx.ALIGN_CENTER | wx.ALL, PANEL_SPACE_MAIN)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)

        return panel

    def onSelectDocument(self, evt):

        docName = self.documentList_choice.GetStringSelection()
        self.presenter.currentDoc = docName
        self.current_document = docName
        self.EndModal(wx.OK)

    def onNewDocument(self, evt):
        self.presenter.onAddBlankDocument(evt=evt)
        self.EndModal(wx.OK)


class panelSelectDataset(wx.Dialog):
    """
    """

    def __init__(self, parent, presenter, docList, dataList, **kwargs):
        wx.Dialog.__init__(self, parent, -1, 'Copy annotations to document/dataset...', size=(400, 300),
                              style=wx.DEFAULT_FRAME_STYLE & ~
                              (wx.RESIZE_BORDER | wx.RESIZE_BOX | wx.MAXIMIZE_BOX))

        self.parent = parent
        self.presenter = presenter
        self.documentList = docList
        self.datasetList = dataList

        # make gui items
        self.makeGUI()
        if "set_document" in kwargs:
            self.documentList_choice.SetStringSelection(kwargs['set_document'])
        else:
            self.documentList_choice.SetSelection(0)
        self.onUpdateGUI(None)

        self.CentreOnParent()
        self.SetFocus()

        wx.EVT_CLOSE(self, self.onClose)

    def onClose(self, evt):
        """Destroy this frame."""

        # If pressed Close, return nothing of value
        self.document = None
        self.dataset = None

        self.Destroy()
    # ----

    def makeGUI(self):

        # make panel
        panel = self.makeSelectionPanel()

        # pack element
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(panel, 0, wx.EXPAND, 0)

        # bind
        self.okBtn.Bind(wx.EVT_BUTTON, self.onSelectDocument, id=wx.ID_OK)
        self.cancelBtn.Bind(wx.EVT_BUTTON, self.onClose)

        # fit layout
        self.mainSizer.Fit(self)
        self.SetSizer(self.mainSizer)

    def makeSelectionPanel(self):

        panel = wx.Panel(self, -1)
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        documentList_label = wx.StaticText(panel, -1, "Document:")
        self.documentList_choice = wx.ComboBox(panel, -1, choices=self.documentList, size=(300, -1), style=wx.CB_READONLY)
        self.documentList_choice.Select(0)
        self.documentList_choice.Bind(wx.EVT_COMBOBOX, self.onUpdateGUI)

        datasetList_label = wx.StaticText(panel, -1, "Dataset:")
        self.datasetList_choice = wx.ComboBox(panel, -1, choices=[], size=(300, -1), style=wx.CB_READONLY)

        self.okBtn = wx.Button(panel, wx.ID_OK, "Select", size=(-1, 22))
        self.cancelBtn = wx.Button(panel, -1, "Cancel", size=(-1, 22))

        GRIDBAG_VSPACE = 7
        GRIDBAG_HSPACE = 5
        PANEL_SPACE_MAIN = 10

        # pack elements
        grid = wx.GridBagSizer(GRIDBAG_VSPACE, GRIDBAG_HSPACE)
        grid.Add(documentList_label, (0, 0))
        grid.Add(self.documentList_choice, (0, 1), wx.GBSpan(1, 3))
        grid.Add(datasetList_label, (1, 0))
        grid.Add(self.datasetList_choice, (1, 1), wx.GBSpan(1, 3))
        grid.Add(self.okBtn, (2, 1), wx.GBSpan(1, 1))
        grid.Add(self.cancelBtn, (2, 2), wx.GBSpan(1, 1))

        mainSizer.Add(grid, 0, wx.ALIGN_CENTER | wx.ALL, PANEL_SPACE_MAIN)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)

        return panel

    def onUpdateGUI(self, evt):
        document = self.documentList_choice.GetStringSelection()
        spectrum = self.datasetList[document]

        self.datasetList_choice.SetItems(spectrum)
        self.datasetList_choice.SetStringSelection(spectrum[0])

    def onSelectDocument(self, evt):

        document = self.documentList_choice.GetStringSelection()
        dataset = self.datasetList_choice.GetStringSelection()
        self.document = document
        self.dataset = dataset
        self.EndModal(wx.OK)


class panelCalibrantDB(wx.MiniFrame):
    """
    Simple GUI panel to display CCS calibrant database selection
    """

    def __init__(self, parent, presenter, config, mode):
        wx.MiniFrame.__init__(self, parent, -1, 'Select protein...', size=(-1, -1),
                              style=wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER |
                              wx.RESIZE_BOX | wx.MAXIMIZE_BOX)

        self.parent = parent
        self.presenter = presenter
        self.config = config

        # modes = calibrants/proteins
        self.currentItem = None
        self.mode = mode
        self.ccsDB = self.config.ccsDB
        self.reverse = False
        self.lastColumn = None
        self.dataOut = None
        # make gui items
        self.makeGUI()
        # Populate the table
        self.onPopulateTable()
        wx.EVT_CLOSE(self, self.onClose)

        self.Centre()
        self.Layout()
        self.SetSize((850, 300))
        self.SetMinSize((850, 300))
        self.peaklist.SetFocus()
        self.CentreOnParent()

    def onClose(self, evt):
        """Destroy this frame."""

        if self.dataOut == None:
            self.config.proteinData = None

        self.Destroy()

    # ----

    def makeGUI(self):

        # make panel
        panel = self.makeDatabasePanel()

        # pack element
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(panel, 1, wx.EXPAND, 0)

        if self.mode == 'calibrants':
            size = (800, 400)
        else:
            size = (400, 400)

        # fit layout
        self.mainSizer.Fit(self)
        self.SetSizer(self.mainSizer)
        self.SetMinSize(size)

    def makeDatabasePanel(self):

        panel = wx.Panel(self, -1, size=(-1, -1))
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        self.peaklist = ListCtrl(panel, style=wx.LC_REPORT)
        self.peaklist.InsertColumn(0, u'protein', width=150)
        self.peaklist.InsertColumn(1, u'MW (kDa)', width=80)
        self.peaklist.InsertColumn(2, u'units', width=60)
        if self.mode == 'calibrants':
            # TODO : add m/z
            self.peaklist.InsertColumn(3, u'z', width=40)
            self.peaklist.InsertColumn(4, u'm/z (kDa)', width=80)
            self.peaklist.InsertColumn(5, u'He⁺', width=60)
            self.peaklist.InsertColumn(6, u'N2⁺', width=60)
            self.peaklist.InsertColumn(7, u'He⁻', width=60)
            self.peaklist.InsertColumn(8, u'N2⁻', width=60)
            self.peaklist.InsertColumn(9, u'state', width=100)
            self.peaklist.InsertColumn(10, u'source', width=60)

        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onItemSelected)
        self.Bind(wx.EVT_LIST_COL_CLICK, self.OnGetColumnClick)

        self.addBtn = wx.Button(panel, wx.ID_OK, "Add", size=(-1, 22))
        self.addBtn.Hide()
        self.selectBtn = wx.Button(panel, wx.ID_OK, "Select", size=(-1, 22))
        self.cancelBtn = wx.Button(panel, wx.ID_OK, "Cancel", size=(-1, 22))

        self.selectBtn.Bind(wx.EVT_BUTTON, self.onSelect)
        self.cancelBtn.Bind(wx.EVT_BUTTON, self.onClose)

        GRIDBAG_VSPACE = 7
        GRIDBAG_HSPACE = 5

        # pack elements
        grid = wx.GridBagSizer(GRIDBAG_VSPACE, GRIDBAG_HSPACE)
        grid.Add(self.addBtn, (0, 0), wx.GBSpan(1, 1))
        grid.Add(self.selectBtn, (0, 1), wx.GBSpan(1, 1))
        grid.Add(self.cancelBtn, (0, 2), wx.GBSpan(1, 1))

        mainSizer.Add(self.peaklist, 1, wx.EXPAND, 2)
        mainSizer.Add(grid, 0, wx.ALIGN_CENTER_HORIZONTAL, 10)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizerAndFit(mainSizer)

        return panel

    def onItemSelected(self, evt):
        self.currentItem = evt.m_itemIndex
        if self.currentItem == None: return

    def onSelect(self, evt):
        if self.currentItem == None: return

        if self.mode == 'calibrants':

            columns = self.peaklist.GetColumnCount()
            tempRow = []
            for col in range(columns):
                item = self.peaklist.GetItem(itemId=self.currentItem, col=col)
                tempRow.append(item.GetText())

            self.config.proteinData = tempRow
            # If dataOut is empty, self.config.proteinData will be reset (in case of cancel)
            self.dataOut = tempRow

            # Now, annotate item
            if len(tempRow) != 0:
                self.parent.panelCCS.topP.onAnnotateItems(evt=None, addProtein=True)

        elif self.mode == 'proteins':
            protein = self.peaklist.GetItem(self.currentItem, self.config.ccsDBColNames['protein']).GetText()
            mw = self.peaklist.GetItem(self.currentItem, self.config.ccsDBColNames['mw']).GetText()

            self.config.proteinData = [protein, mw]
            self.dataOut = [protein, mw]

            # Now annotate item
            if len(self.dataOut) != 0:
                self.parent.panelDocuments.topP.documents.panelInfo.onAnnotateProteinInfo(data=self.config.proteinData)

    def onPopulateTable(self):

        if self.mode == 'calibrants':
            try:
                if self.ccsDB != None:
                    pass
            except TypeError:
                ccsDBlist = self.ccsDB.values.tolist()
                for row in ccsDBlist:
                    self.peaklist.Append(row)

        elif self.mode == 'proteins':
            try:
                if self.ccsDB != None:
                    pass
            except TypeError:
                # Convert the DB to dictionary --> list of lists
                ccsDBDict = self.ccsDB.to_dict(orient='index')
                tempData = []
                for key in ccsDBDict:
                    tempData.append([ccsDBDict[key]['Protein'],
                                     ccsDBDict[key]['MW'],
                                     str(ccsDBDict[key]['Subunits'])])

                tempData.sort()
                tempData = list(item for item, _ in itertools.groupby(tempData))
                for row in tempData:
                    self.peaklist.Append(row)

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
                if (col == self.config.ccsDBColNames['mw'] or
                    col == self.config.ccsDBColNames['ion'] or
                    col == self.config.ccsDBColNames['hePos'] or
                    col == self.config.ccsDBColNames['n2Pos'] or
                    col == self.config.ccsDBColNames['heNeg'] or
                    col == self.config.ccsDBColNames['n2Neg']):
                    itemData = str2num(item.GetText())
                    if itemData == None: itemData = 0
                    tempRow.append(itemData)
                # Integers
                elif (col == self.config.ccsDBColNames['units'] or
                    col == self.config.ccsDBColNames['charge']):
                    itemData = str2int(item.GetText())
                    if itemData == None: itemData = 0
                    tempRow.append(itemData)
                # Text
                else:
                    tempRow.append(item.GetText())
            tempData.append(tempRow)

        # Sort data
        tempData.sort(key=itemgetter(column), reverse=self.reverse)
        # Clear table
        self.peaklist.DeleteAllItems()

        # Reinstate data
        rowList = arange(len(tempData))
        for row in rowList:
            self.peaklist.Append(tempData[row])


class panelRenameItem(wx.Dialog):

    def __init__(self, parent, presenter, title, **kwargs):
        wx.Dialog.__init__(self, parent, -1, 'Rename...', size=(400, 300),
                           style=wx.DEFAULT_FRAME_STYLE & ~
                           (wx.RESIZE_BORDER | wx.RESIZE_BOX | wx.MAXIMIZE_BOX))

        self.parent = parent
        self.presenter = presenter
        self.title = title
        self.SetTitle('Document: ' + self.title)

        self.new_name = None
        self.kwargs = kwargs
        # make gui items
        self.makeGUI()

        wx.EVT_CLOSE(self, self.onClose)
        self.Bind(wx.EVT_CHAR_HOOK, self.OnKey)

        self.Centre()
        self.Layout()

    # ----

    def OnKey(self, evt):
        keyCode = evt.GetKeyCode()
        if keyCode == wx.WXK_ESCAPE:  # key = esc
            self.onClose(evt=None)

        if evt != None:
            evt.Skip()

    def onClose(self, evt):
        """Destroy this frame."""
        self.new_name = None
        self.Destroy()
    # ----

    def makeGUI(self):

        # make panel
        panel = self.makeSelectionPanel()

        # pack element
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(panel, 1, wx.EXPAND, 10)

        # bind
        self.newName_value.Bind(wx.EVT_TEXT_ENTER, self.onFinishLabelChanging)
        self.okBtn.Bind(wx.EVT_BUTTON, self.onChangeLabel)
        self.cancelBtn.Bind(wx.EVT_BUTTON, self.onClose)

        # fit layout
        self.mainSizer.Fit(self)
        self.SetSizer(self.mainSizer)
        self.SetMinSize((500, 100))

    def makeSelectionPanel(self):

        panel = wx.Panel(self, -1)
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        BOX_SIZE = 400
        oldName_label = wx.StaticText(panel, -1, "Current name:")
        self.oldName_value = wx.TextCtrl(panel, -1, "", size=(BOX_SIZE, 40),
                                          style=wx.TE_READONLY | wx.TE_WORDWRAP)
        self.oldName_value.SetValue(self.kwargs['current_name'])

        newName_label = wx.StaticText(panel, -1, "Edit name:")
        self.newName_value = wx.TextCtrl(panel, -1, "", size=(BOX_SIZE, -1), style=wx.TE_PROCESS_ENTER)
        self.newName_value.SetValue(self.kwargs['current_name'])
        self.newName_value.SetFocus()

        note_label = wx.StaticText(panel, -1, "Final name:")
        self.note_value = wx.StaticText(panel, -1, "", size=(BOX_SIZE, 40))
        self.note_value.Wrap(BOX_SIZE)

        self.okBtn = wx.Button(panel, wx.ID_OK, "Rename", size=(-1, 22))
        self.cancelBtn = wx.Button(panel, wx.ID_CANCEL, "Cancel", size=(-1, 22))

        # pack elements
        grid = wx.GridBagSizer(5, 5)

        grid.Add(oldName_label, (0, 0))
        grid.Add(self.oldName_value, (0, 1), wx.GBSpan(1, 5))
        grid.Add(newName_label, (1, 0))
        grid.Add(self.newName_value, (1, 1), wx.GBSpan(1, 5))
        grid.Add(note_label, (2, 0))
        grid.Add(self.note_value, (2, 1), wx.GBSpan(2, 5))

        grid.Add(self.okBtn, (4, 0), wx.GBSpan(1, 1))
        grid.Add(self.cancelBtn, (4, 1), wx.GBSpan(1, 1))

        mainSizer.Add(grid, 0, wx.EXPAND, 10)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizerAndFit(mainSizer)

        return panel

    def onFinishLabelChanging(self, evt):
        self.onChangeLabel(wx.ID_OK)

    def onChangeLabel(self, evt):
        """ change label of the selected item """

        if self.kwargs['prepend_name']:
            self.new_name = "{}: {}".format(self.kwargs['current_name'], self.newName_value.GetValue())
        else:
            self.new_name = "{}".format(self.newName_value.GetValue())
        self.note_value.SetLabel(self.new_name)

        if isinstance(evt, int):
            evtID = evt
        else:
            evtID = evt.GetId()

        if evtID == wx.ID_OK:
            self.Destroy()


class panelSequenceAnalysis(wx.MiniFrame):
    """
    Simple GUI to view and analyse sequences
    """

    def __init__(self, parent, presenter, config, icons):
        wx.MiniFrame.__init__(self, parent, -1, 'Sequence analysis...', size=(-1, -1),
                              style=wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER)

        self.parent = parent
        self.presenter = presenter
        self.config = config
        self.icons = icons

        self.help = help()

        # make gui items
        self.makeGUI()

        self.Centre()
        self.Layout()
        self.SetFocus()

        # bind
        wx.EVT_CLOSE(self, self.onClose)
        self.Bind(wx.EVT_CHAR_HOOK, self.OnKey)
    # ----

    def OnKey(self, evt):
        keyCode = evt.GetKeyCode()
        if keyCode == wx.WXK_ESCAPE:  # key = esc
            self.onClose(evt=None)
        elif keyCode == 83:  # key = s
            self.onSelect(evt=None)
        elif keyCode == 85:  # key = u
            self.onPlot(evt=None)

        evt.Skip()

    def onClose(self, evt):
        """Destroy this frame."""

        self.Destroy()
    # ----

    def onSelect(self, evt):

        self.Destroy()

    def onPlot (self, evt):
        """
        Update plot with currently selected PCs
        """
        pass

    def makeGUI(self):

        # make panel
        panel = self.makePanel()

        # pack element
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(panel, 1, wx.EXPAND, 5)

        # fit layout
        self.mainSizer.Fit(self)
        self.SetSizer(self.mainSizer)

    def makePanel(self):

        panel = wx.Panel(self, -1, size=(-1, -1))
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        # make editor
        title_label = wx.StaticText(panel, -1, "Title::")
        self.title_value = wx.TextCtrl(panel, -1, "", size=(-1, -1), style=wx.BORDER_SUNKEN)

        sequence_label = wx.StaticText(panel, -1, "Sequence:")
        self.sequence_value = wx.TextCtrl(panel, -1, "", size=(400, 200), style=wx.BORDER_SUNKEN)

        self.sequence_loadBtn = wx.BitmapButton(panel, wx.ID_ANY,
                                                self.icons.iconsLib['load16'],
                                                size=(26, 26),
                                                style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL)

        self.sequence_converter = wx.BitmapButton(panel, wx.ID_ANY,
                                                  self.icons.iconsLib['aa3to1_16'],  # change to 3 <-> 1
                                                  size=(26, 26),
                                                  style=wx.BORDER_NONE | wx.ALIGN_CENTER_VERTICAL)

        horizontal_line = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        vertical_line_1 = wx.StaticLine(panel, -1, style=wx.LI_VERTICAL)
        vertical_line_2 = wx.StaticLine(panel, -1, style=wx.LI_VERTICAL)
        vertical_line_3 = wx.StaticLine(panel, -1, style=wx.LI_VERTICAL)
        vertical_line_4 = wx.StaticLine(panel, -1, style=wx.LI_VERTICAL)

        LABEL_SIZE = (100, -1)
        TEXT_SIZE = (60, -1)
        length_label = wx.StaticText(panel, -1, u"Length:", size=LABEL_SIZE)
        mw_label = wx.StaticText(panel, -1, u"Av. mass:", size=LABEL_SIZE)
        pI_label = wx.StaticText(panel, -1, u"pI:", size=LABEL_SIZE)

        self.length_value = wx.StaticText(panel, -1, "", size=TEXT_SIZE)
        self.mw_value = wx.StaticText(panel, -1, "", size=TEXT_SIZE)
        self.pI_value = wx.StaticText(panel, -1, "", size=(50, -1))

        minCCS_label = wx.StaticText(panel, -1, u"Compact CCS (Å²):", size=LABEL_SIZE)
        maxCCS_label = wx.StaticText(panel, -1, u"Extended CCS (Å²):", size=LABEL_SIZE)
        kappa_label = wx.StaticText(panel, -1, u"κ value:", size=(50, -1))

        self.minCCS_value = wx.StaticText(panel, -1, "", size=TEXT_SIZE)
        self.maxCCS_value = wx.StaticText(panel, -1, "", size=TEXT_SIZE)
        self.kappa_value = wx.StaticText(panel, -1, "", size=TEXT_SIZE)

        # make buttons
        self.calculateBtn = wx.Button(panel, wx.ID_OK, "Calculate", size=(-1, 22))
        self.plotBtn = wx.Button(panel, wx.ID_OK, "Plot", size=(-1, 22))
        self.cancelBtn = wx.Button(panel, wx.ID_OK, "Cancel", size=(-1, 22))

        self.calculateBtn.Bind(wx.EVT_BUTTON, self.onSelect)
        self.plotBtn.Bind(wx.EVT_BUTTON, self.onPlot)
        self.cancelBtn.Bind(wx.EVT_BUTTON, self.onClose)

        btn_grid = wx.GridBagSizer(5, 5)
        y = 0
        btn_grid.Add(self.calculateBtn, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        btn_grid.Add(self.plotBtn, (y, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        btn_grid.Add(self.cancelBtn, (y, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)

        info_grid = wx.GridBagSizer(5, 5)
        y = 0
        info_grid.Add(length_label, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        info_grid.Add(self.length_value, (y, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        info_grid.Add(vertical_line_1, (y, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        info_grid.Add(mw_label, (y, 3), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        info_grid.Add(self.mw_value, (y, 4), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        info_grid.Add(vertical_line_2, (y, 5), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND | wx.ALIGN_LEFT)
        info_grid.Add(pI_label, (y, 6), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        info_grid.Add(self.pI_value, (y, 7), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        y = y + 1
        info_grid.Add(minCCS_label, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        info_grid.Add(self.minCCS_value, (y, 1), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        info_grid.Add(vertical_line_3, (y, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        info_grid.Add(maxCCS_label, (y, 3), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        info_grid.Add(self.maxCCS_value, (y, 4), wx.GBSpan(1, 1), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        info_grid.Add(vertical_line_4, (y, 5), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        info_grid.Add(kappa_label, (y, 6), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        info_grid.Add(self.kappa_value, (y, 7), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)

        # pack elements
        grid = wx.GridBagSizer(5, 5)
        y = 0
        grid.Add(title_label, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_RIGHT | wx.ALIGN_TOP)
        grid.Add(self.title_value, (y, 1), wx.GBSpan(1, 6), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        y = y + 1
        grid.Add(sequence_label, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_RIGHT | wx.ALIGN_TOP)
        grid.Add(self.sequence_value, (y, 1), wx.GBSpan(2, 6), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.sequence_loadBtn, (y, 7), wx.GBSpan(1, 1), flag=wx.ALIGN_LEFT | wx.ALIGN_TOP)
        y = y + 1
        grid.Add(self.sequence_converter, (y, 7), wx.GBSpan(1, 1), flag=wx.ALIGN_LEFT | wx.ALIGN_TOP)
        y = y + 1
        grid.Add(horizontal_line, (y, 0), wx.GBSpan(1, 8), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        y = y + 1
        grid.Add(info_grid, (y, 0), wx.GBSpan(1, 8), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        y = y + 1
        grid.Add(btn_grid, (y, 0), wx.GBSpan(1, 8), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)

        mainSizer.Add(grid, 0, wx.EXPAND, 10)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizerAndFit(mainSizer)

        return panel

    def updateMS(self, evt):
        pass

        if evt != None:
            evt.Skip()


class panelExportSettings(wx.MiniFrame):

    def __init__(self, parent, presenter, config, icons, **kwargs):
        wx.MiniFrame.__init__(self, parent, -1, 'Import/Export parameters', size=(-1, -1),
                              style=(wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BOX |
                                      wx.MAXIMIZE_BOX | wx.CLOSE_BOX))

        self.parent = parent
        self.presenter = presenter
        self.config = config
        self.icons = icons
        self.help = help()

        self.importEvent = False
        self.windowSizes = {'Peaklist':(250, 110), 'Image':(250, 150),
                            'Files':(310, 140)}

        # make gui items
        self.makeGUI()
        self.mainBook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.onPageChanged)
        self.mainBook.SetSelection(self.config.importExportParamsWindow[kwargs['window']])

        # bind
        wx.EVT_CLOSE(self, self.onClose)
        self.Bind(wx.EVT_CHAR_HOOK, self.OnKey)

        self.mainSizer.Fit(self)
        self.Centre()
        self.Layout()
        self.Show(True)
        self.SetFocus()

        # fire-up start events
        self.onPageChanged(evt=None)
        self.enableDisableBoxes(evt=None)

    def OnKey(self, evt):
        keyCode = evt.GetKeyCode()
        if keyCode == wx.WXK_ESCAPE:  # key = esc
            self.onClose(evt=None)

        if evt != None:
            evt.Skip()

    def onPageChanged(self, evt):
        self.currentPage = self.mainBook.GetPageText(self.mainBook.GetSelection())
        self.SetSize(self.windowSizes[self.currentPage])
        self.Layout()

    def onSetPage(self, **kwargs):
        self.mainBook.SetSelection(self.config.importExportParamsWindow[kwargs['window']])
        self.onPageChanged(evt=None)

    def onSelect(self, evt):
        self.Destroy()

    def onClose(self, evt):
        """Destroy this frame."""
        self.config.importExportParamsWindow_on_off = False
        self.Destroy()
    # ----

    def makeGUI(self):

        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        # Setup notebook
        self.mainBook = wx.Notebook(self, wx.ID_ANY, wx.DefaultPosition,
                                    wx.DefaultSize, style=wx.NB_MULTILINE)

        self.parameters_peaklist = wx.Panel(self.mainBook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.mainBook.AddPage(self.makePanel_Peaklist(self.parameters_peaklist), u"Peaklist", False)
        # ------
        self.parameters_image = wx.Panel(self.mainBook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.mainBook.AddPage(self.makePanel_Image(self.parameters_image), u"Image", False)
        # ------
        self.parameters_files = wx.Panel(self.mainBook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.mainBook.AddPage(self.makePanel_Files(self.parameters_files), u"Files", False)

        self.mainSizer.Add(self.mainBook, 1, wx.EXPAND | wx.ALL, 2)

        # setup color
        self.mainBook.SetBackgroundColour((240, 240, 240))

    def makePanel_Peaklist(self, panel):
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        useInternal_label = wx.StaticText(panel, wx.ID_ANY, u"Override imported values:")
        self.peaklist_useInternalWindow_check = makeCheckbox(panel, u"")
        self.peaklist_useInternalWindow_check.SetValue(self.config.useInternalMZwindow)
        self.peaklist_useInternalWindow_check.Bind(wx.EVT_CHECKBOX, self.onApply)
        self.peaklist_useInternalWindow_check.Bind(wx.EVT_CHECKBOX, self.enableDisableBoxes)

        windowSize_label = wx.StaticText(panel, wx.ID_ANY, u"± m/z (Da):")
        self.peaklist_windowSize_value = wx.SpinCtrlDouble(panel, -1, value=str(0),
                                                  min=0.5, max=50, initial=0, inc=1,
                                                  size=(60, -1))
        self.peaklist_windowSize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        self.peaklist_windowSize_value.SetValue(self.config.mzWindowSize)

        # add to grid
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(useInternal_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.peaklist_useInternalWindow_check, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        n = n + 1
        grid.Add(windowSize_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.peaklist_windowSize_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        mainSizer.Add(grid, 0, wx.ALIGN_CENTER_HORIZONTAL, 10)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizerAndFit(mainSizer)

        return panel

    def makePanel_Image(self, panel):
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        fileFormat_label = wx.StaticText(panel, wx.ID_ANY, u"File format:")
        self.image_fileFormat_choice = wx.Choice(panel, -1, choices=self.config.imageFormatType,
                                                 size=(-1, -1))
        self.image_fileFormat_choice.SetStringSelection(self.config.imageFormat)
        self.image_fileFormat_choice.Bind(wx.EVT_CHOICE, self.onApply)

        resolution_label = wx.StaticText(panel, wx.ID_ANY, u"Resolution:")
        self.image_resolution = wx.SpinCtrlDouble(panel, -1, value=str(0),
                                                  min=50, max=600, initial=0, inc=50,
                                                  size=(60, -1))
        self.image_resolution.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        self.image_resolution.SetValue(self.config.dpi)

        transparency_label = wx.StaticText(panel, wx.ID_ANY, u"Transparent:")
        self.image_transparency_check = makeCheckbox(panel, u"")
        self.image_transparency_check.SetValue(self.config.transparent)
        self.image_transparency_check.Bind(wx.EVT_CHECKBOX, self.onApply)

        resize_label = wx.StaticText(panel, wx.ID_ANY, u"Resize:")
        self.image_resize_check = makeCheckbox(panel, u"")
        self.image_resize_check.SetValue(self.config.resize)
        self.image_resize_check.Bind(wx.EVT_CHECKBOX, self.onApply)

        # add to grid
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(fileFormat_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.image_fileFormat_choice, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        n = n + 1
        grid.Add(resolution_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.image_resolution, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        n = n + 1
        grid.Add(transparency_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.image_transparency_check, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        n = n + 1
        grid.Add(resize_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.image_resize_check, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        mainSizer.Add(grid, 0, wx.ALIGN_CENTER_HORIZONTAL, 10)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizerAndFit(mainSizer)

        return panel

    def makePanel_Files(self, panel):
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        delimiter_label = wx.StaticText(panel, wx.ID_ANY, u"Delimiter:")
        self.file_delimiter_choice = wx.Choice(panel, -1, choices=self.config.textOutputDict.keys(),
                                                 size=(-1, -1))
        self.file_delimiter_choice.SetStringSelection(self.config.saveDelimiterTXT)
        self.file_delimiter_choice.Bind(wx.EVT_CHOICE, self.onApply)

        default_name_label = wx.StaticText(panel, wx.ID_ANY, u"Default name:")
        self.file_default_name_choice = wx.Choice(panel, -1, choices=sorted(self.config._plotSettings.keys()),
                                                 size=(-1, -1))
        self.file_default_name_choice.SetSelection(0)
        self.file_default_name_choice.Bind(wx.EVT_CHOICE, self.onSetupPlotName)

        self.file_default_name = wx.TextCtrl(panel, -1, "", size=(210, -1))
        self.file_default_name.SetValue(self.config._plotSettings[self.file_default_name_choice.GetStringSelection()]['default_name'])
        self.file_default_name.Bind(wx.EVT_TEXT, self.onApply)

        # add to grid
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(delimiter_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.file_delimiter_choice, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        n = n + 1
        grid.Add(default_name_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.file_default_name_choice, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT)
        n = n + 1
        grid.Add(self.file_default_name, (n, 1), wx.GBSpan(1, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT | wx.EXPAND)
        mainSizer.Add(grid, 0, wx.ALIGN_LEFT, 10)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizerAndFit(mainSizer)

        return panel

    def onApply(self, evt):

        # prevent updating config
        if self.importEvent: return

        # Peaklist
        self.config.useInternalMZwindow = self.peaklist_useInternalWindow_check.GetValue()
        self.config.mzWindowSize = self.peaklist_windowSize_value.GetValue()

        # Images
        self.config.dpi = self.image_resolution.GetValue()
        self.config.transparent = self.image_transparency_check.GetValue()
        self.config.resize = self.image_resize_check.GetValue()
        self.config.imageFormat = self.image_fileFormat_choice.GetStringSelection()

        # Files
        self.config.saveDelimiterTXT = self.file_delimiter_choice.GetStringSelection()
        self.config.saveDelimiter = self.config.textOutputDict[self.config.saveDelimiterTXT]
        self.config.saveExtension = self.config.textExtensionDict[self.config.saveDelimiterTXT]

    def enableDisableBoxes(self, evt):
        self.config.useInternalMZwindow = self.peaklist_useInternalWindow_check.GetValue()

        if self.config.useInternalMZwindow:
            self.peaklist_windowSize_value.Enable()
        else:
            self.peaklist_windowSize_value.Disable()

        if evt != None:
            evt.Skip()

    def onSetupPlotName(self, evt):
        # get current plot name
        plotName = self.file_default_name_choice.GetStringSelection()
        # get name
        plotName = self.config._plotSettings[plotName]['default_name']

        self.file_default_name.SetValue(plotName)


class panelHTMLViewer(wx.MiniFrame):

    def __init__(self, parent, config, msg=None, title=None, **kwargs):
        wx.MiniFrame.__init__(self, parent, -1, 'HTML viewer', size=(-1, -1),
                              style=(wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BOX |
                                      wx.MAXIMIZE_BOX | wx.CLOSE_BOX))

        self.parent = parent
        self.config = config

        self.label_header = wx.html.HtmlWindow(self, style=wx.TE_READONLY |
                                               wx.TE_MULTILINE | wx.html.HW_SCROLLBAR_AUTO | wx.BORDER_NONE | wx.html.HTML_URL_IMAGE)

        if msg is None:
            msg = kwargs['html_msg']
        if title is None:
            title = kwargs['title']

        # get current working directory and temporarily change path
        cwd = os.getcwd()
        os.chdir(self.config.cwd)

        self.label_header.SetPage(msg)
        self.label_header.Bind(wx.html.EVT_HTML_LINK_CLICKED, self.onURL)
        self.SetTitle(title)

        try:
            _main_position = self.parent.GetPosition()
            position_diff = []
            for idx in range(wx.Display.GetCount()):
                d = wx.Display(idx)
                position_diff.append(_main_position[0] - d.GetGeometry()[0])

            currentDisplaySize = wx.Display(position_diff.index(min(position_diff))).GetGeometry()
        except:
            currentDisplaySize = None

        if 'window_size' in kwargs:
            if currentDisplaySize is not None:
                screen_width, screen_height = currentDisplaySize[2], currentDisplaySize[3]
                kwargs['window_size'] = list(kwargs['window_size'])

                if kwargs['window_size'][0] > screen_width:
                    kwargs['window_size'][0] = screen_width

                if kwargs['window_size'][1] > screen_height:
                    kwargs['window_size'][1] = screen_height - 75

            self.SetSize(kwargs['window_size'])

        self.Show(True)
        self.CentreOnParent()
        self.SetFocus()
        wx.EVT_CLOSE(self, self.onClose)

        # reset working directory
        os.chdir(cwd)

    def onURL(self, evt):
        link = evt.GetLinkInfo()
        webbrowser.open(link.GetHref())
        return

    def onClose(self, evt):
        """Destroy this frame."""

        self.Destroy()
    # ----


class panelPeakWidthTool(wx.MiniFrame):
    """
    """

    def __init__(self, parent, presenter, config, **kwargs):
        wx.MiniFrame.__init__(self, parent, -1, 'UniDec peak width tool...', size=(600, 500),
                              style=wx.DEFAULT_FRAME_STYLE & ~
                              (wx.RESIZE_BORDER | wx.RESIZE_BOX | wx.MAXIMIZE_BOX))

        self.parent = parent
        self.config = config
        self.presenter = presenter
        self.kwargs = kwargs
        self.help = help()
        # make gui items
        self.makeGUI()
        self.on_plot_MS(kwargs['xvals'], kwargs['yvals'])
        self.SetFocus()
        wx.EVT_CLOSE(self, self.onClose)

    def onClose(self, evt):
        """Destroy this frame."""
        self.Destroy()
    # ----

    def makeGUI(self):
        # make panel
        panel = self.makeSelectionPanel()

        # pack element
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(panel, 0, wx.EXPAND, 0)

        # bind events
        self.cancelBtn.Bind(wx.EVT_BUTTON, self.onClose)
        self.fitBtn.Bind(wx.EVT_BUTTON, self.on_fit_peak)
        self.okBtn.Bind(wx.EVT_BUTTON, self.on_OK)

        # fit layout
        self.mainSizer.Fit(self)
        self.SetSizer(self.mainSizer)

    def makeSelectionPanel(self):

        panel = wx.Panel(self, -1)
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        self.plotMS = plots.plots(panel, figsize=(6, 3), config=self.config)

        unidec_peakShape_label = wx.StaticText(panel, wx.ID_ANY, u"Peak Shape:")
        self.unidec_peakFcn_choice = wx.Choice(panel, -1, choices=self.config.unidec_peakFunction_choices.keys(),
                                          size=(-1, -1))
        self.unidec_peakFcn_choice.SetStringSelection(self.config.unidec_peakFunction)
        self.unidec_peakFcn_choice.Bind(wx.EVT_CHOICE, self.on_fit_peak)

        unidec_peakWidth_label = wx.StaticText(panel, wx.ID_ANY, u"Peak FWHM (Da):")
        self.unidec_fit_peakWidth_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('floatPos'))
        _tip = makeSuperTip(self.unidec_fit_peakWidth_value, **self.help.unidec_peak_FWHM)

        unidec_error_label = wx.StaticText(panel, wx.ID_ANY, u"Error:")
        self.unidec_error = wx.StaticText(panel, wx.ID_ANY, u"")
        unidec_resolution_label = wx.StaticText(panel, wx.ID_ANY, u"Resolution (M/FWHM):")
        self.unidec_resolution = wx.StaticText(panel, wx.ID_ANY, u"")

        self.fitBtn = wx.Button(panel, -1, "Fit", size=(-1, 22))
        msg = "To determine peak width, please zoom-in on a desired peak, \n" + \
              "select peak shape and press fit. When you are finished, press on \n" + \
              "OK and continue."
        help_peak = {'help_title':'Peak width fitting', 'help_msg':msg,
                                 'header_img': None, 'header_line':True,
                                 'footer_line':False}
        _tip = makeSuperTip(self.fitBtn, **help_peak)

        self.okBtn = wx.Button(panel, wx.ID_OK, "OK", size=(-1, 22))
        self.cancelBtn = wx.Button(panel, -1, "Cancel", size=(-1, 22))

        peak_grid = wx.GridBagSizer(2, 2)
        n = 0
        peak_grid.Add(unidec_peakShape_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        peak_grid.Add(self.unidec_peakFcn_choice, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        peak_grid.Add(unidec_peakWidth_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        peak_grid.Add(self.unidec_fit_peakWidth_value, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        peak_grid.Add(unidec_error_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        peak_grid.Add(self.unidec_error, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        peak_grid.Add(unidec_resolution_label, (n, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        peak_grid.Add(self.unidec_resolution, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        peak_grid.Add(self.fitBtn, (n, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL)

        # pack elements
        grid = wx.GridBagSizer(5, 5)
        grid.Add(self.plotMS, (0, 0), wx.GBSpan(3, 2))
        grid.Add(peak_grid, (0, 3), wx.GBSpan(1, 2))
        grid.Add(self.okBtn, (3, 3), wx.GBSpan(1, 1))
        grid.Add(self.cancelBtn, (3, 4), wx.GBSpan(1, 1))

        mainSizer.Add(grid, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)

        return panel

    def on_OK(self, evt):
        width = self.unidec_fit_peakWidth_value.GetValue()
        function = self.unidec_peakFcn_choice.GetStringSelection()
        if width == "" or width == None:
            dlgBox(exceptionTitle="Error",
                   exceptionMsg="Could not complete action. Pick peaks first?",
                   type="Error")
            return
        else:
            self.parent.unidec_fit_peakWidth_value.SetValue("{:.4f}".format(str2num(width)))
            self.parent.unidec_peakFcn_choice.SetStringSelection(function)
        self.Destroy()

    def on_crop_data(self):
        xlimits = self.plotMS.plotMS.get_xlim()
        ms_spectrum = transpose([self.kwargs['xvals'], self.kwargs['yvals']])
        ms_narrow = getNarrow1Ddata(data=ms_spectrum, mzRange=xlimits)
        return ms_narrow, xlimits

    def on_fit_peak(self, evt):
        ms_narrow, xlimits = self.on_crop_data()
        peakfcn = self.config.unidec_peakFunction_choices[self.unidec_peakFcn_choice.GetStringSelection()]
        try:
            fitout, fit_yvals = isolated_peak_fit(ms_narrow[:, 0], ms_narrow[:, 1], peakfcn)
        except RuntimeError:
            print("Failed to fit a peak. Try again in larger window")
            return

        fitout = fitout[:, 0]
        width = fitout[0]
        resolution = ms_narrow[argmax(ms_narrow[:, 1]), 0] / fitout[0]
        error = npsum((fit_yvals - ms_narrow[:, 1]) * (fit_yvals - ms_narrow[:, 1]))

        # setup labels
        self.unidec_resolution.SetLabel("{:.4f}".format(resolution))
        self.unidec_error.SetLabel("{:.4f}".format(error))
        self.unidec_fit_peakWidth_value.SetValue("{:.4f}".format(width))
        self.on_plot_MS_with_Fit(self.kwargs['xvals'], self.kwargs['yvals'], ms_narrow[:, 0], fit_yvals, xlimits)

    def on_plot_MS(self, msX=None, msY=None, xlimits=None, override=True, replot=False,
                   full_repaint=False, e=None):

        # Build kwargs
        plt_kwargs = self.presenter.view.panelPlots._buildPlotParameters(plotType='1D')

        self.plotMS.clearPlot()
        self.plotMS.plot_1D(xvals=msX, yvals=msY,
                            xlimits=xlimits,
                            xlabel="m/z", ylabel="Intensity",
                            axesSize=[0.1, 0.2, 0.8, 0.75],
                            plotType='MS',
                            **plt_kwargs)
        # Show the mass spectrum
        self.plotMS.repaint()

    def on_plot_MS_with_Fit(self, xvals, yvals, fit_xvals, fit_yvals, xlimits=None, **kwargs):
        """

        """

        # Build kwargs
        plt_kwargs = self.presenter.view.panelPlots._buildPlotParameters(plotType='1D')

        # Plot MS
        self.plotMS.clearPlot()
        self.plotMS.plot_1D(xvals=xvals, yvals=yvals,
#                             xlimits=xlimits,
                            xlabel="m/z",
                            ylabel="Intensity",
                            axesSize=[0.1, 0.2, 0.8, 0.75],
                            plotType='MS', label="Raw",
                            allowWheel=False,
                            **plt_kwargs)
        self.plotMS.plot_1D_add(fit_xvals, fit_yvals, color="red", label="Fit", setup_zoom=False)

        self.plotMS.plotMS.set_xlim(xlimits)
        self.plotMS.repaint()


class panelNotifyNewVersion(wx.Dialog):

    def __init__(self, parent, presenter, message, **kwargs):
        wx.Dialog.__init__(self, parent, -1, 'New version of ORIGAMI is available!', size=(-1, -1),
                              style=wx.DEFAULT_FRAME_STYLE & ~
                              (wx.RESIZE_BORDER | wx.RESIZE_BOX | wx.MAXIMIZE_BOX))

        self.parent = parent
        self.presenter = presenter
        self.icons = presenter.icons
        self.message = message

        self.makeGUI()
        self.CentreOnParent()
        self.Show(True)
        self.SetFocus()
        self.Raise()

    def onClose(self, evt):
        """Destroy this frame."""

        self.Destroy()
    # ----

    def onOK(self, evt):

        self.presenter.onLibraryLink(evt)
        self.EndModal(wx.OK)

    def makeGUI(self):

        # make panel
        panel = self.makePanel()

        # pack element
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(panel, 0, wx.EXPAND, 0)

        # bind
        self.goToDownload.Bind(wx.EVT_BUTTON, self.onOK, id=ID_helpNewVersion)
        self.cancelBtn.Bind(wx.EVT_BUTTON, self.onClose)

        # fit layout
        self.mainSizer.Fit(self)
        self.SetSizer(self.mainSizer)

    def makePanel(self):

        panel = wx.Panel(self, -1)
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        image = wx.StaticBitmap(panel, -1, self.icons.getLogo)

        self.label_header = wx.html.HtmlWindow(panel, style=wx.TE_READONLY | wx.TE_MULTILINE | wx.html.HW_SCROLLBAR_AUTO ,
                                               size=(500, 400))
        self.label_header.SetPage(self.message)

        self.goToDownload = wx.Button(panel, ID_helpNewVersion, "Download Now", size=(-1, 22))
        self.cancelBtn = wx.Button(panel, -1, "Cancel", size=(-1, 22))

        btn_grid = wx.GridBagSizer(1, 1)
        btn_grid.Add(self.goToDownload, (0, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_RIGHT)
        btn_grid.Add(self.cancelBtn, (0, 2), wx.GBSpan(1, 1), flag=wx.ALIGN_RIGHT)

        horizontal_line_1 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_2 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        # pack elements
        grid = wx.GridBagSizer(5, 5)
        grid.Add(image, (0, 0), wx.GBSpan(1, 3), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(horizontal_line_1, (1, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
        grid.Add(self.label_header, (2, 0), wx.GBSpan(2, 3), flag=wx.EXPAND | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(horizontal_line_2, (4, 0), wx.GBSpan(1, 3), flag=wx.EXPAND)
        grid.Add(btn_grid, (5, 1), wx.GBSpan(1, 1), flag=wx.ALIGN_RIGHT)

        mainSizer.Add(grid, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)

        return panel


class panelNotifyOpenDocuments(wx.Dialog):

    def __init__(self, parent, presenter, message, **kwargs):
        wx.Dialog.__init__(self, parent, -1, 'Documents are still open...!', size=(-1, -1),
                              style=wx.DEFAULT_FRAME_STYLE & ~
                              (wx.RESIZE_BORDER | wx.RESIZE_BOX | wx.MAXIMIZE_BOX))

        self.parent = parent
        self.presenter = presenter
        self.message = message

        self.makeGUI()
        self.CentreOnParent()

    def onClose(self, evt):
        """Destroy this frame."""
        self.EndModal(wx.ID_NO)
    # ----

    def onOK(self, evt):
        self.EndModal(wx.OK)

    def onSaveDocument(self, evt):
        self.presenter.on_save_all_documents(ID_saveAllDocuments)
        self.EndModal(wx.OK)

    def makeGUI(self):

        # make panel
        panel = self.makePanel()

        # pack element
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(panel, 0, wx.EXPAND, 0)

        # bind
        self.saveAllBtn.Bind(wx.EVT_BUTTON, self.onSaveDocument, id=ID_saveAllDocuments)
        self.continueBtn.Bind(wx.EVT_BUTTON, self.onOK, id=wx.ID_OK)
        self.cancelBtn.Bind(wx.EVT_BUTTON, self.onClose, id=wx.ID_CANCEL)

        # fit layout
        self.mainSizer.Fit(self)
        self.SetSizer(self.mainSizer)

    def makePanel(self):

        panel = wx.Panel(self, -1)
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        self.input_label = wx.StaticText(panel, -1, "")
        self.input_label.SetLabel(self.message)

        self.saveAllBtn = wx.Button(panel, ID_saveAllDocuments, "Save all", size=(-1, 22))
        self.continueBtn = wx.Button(panel, wx.ID_OK, "Continue", size=(-1, 22))
        self.cancelBtn = wx.Button(panel, wx.ID_CANCEL, "Cancel", size=(-1, 22))

        # pack elements
        grid = wx.GridBagSizer(5, 5)
        grid.Add(self.input_label, (0, 0), wx.GBSpan(2, 3), flag=wx.ALIGN_RIGHT | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)

        grid.Add(self.saveAllBtn, (2, 1), wx.GBSpan(1, 1))
        grid.Add(self.continueBtn, (2, 2), wx.GBSpan(1, 1))
        grid.Add(self.cancelBtn, (2, 3), wx.GBSpan(1, 1))

        mainSizer.Add(grid, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)

        return panel


class panelInformation(wx.MiniFrame):
    """
    """

    def __init__(self, parent, **kwargs):
        wx.MiniFrame.__init__(self, parent, -1, 'Sample information', size=(300, 200),
                              style=wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER)

        self.parent = parent

        # make gui items
        self.makeGUI()

        self.Centre()
        self.SetSize((450, 140))
        self.Layout()
        self.SetFocus()

        if "title" in kwargs:
            self.SetTitle(kwargs['title'])

        if "information" in kwargs:
            self.information.SetLabel(kwargs['information'])
            self.information.Wrap(425)

        # bind
        wx.EVT_CLOSE(self, self.onClose)
        self.Bind(wx.EVT_CHAR_HOOK, self.OnKey)
    # ----

    def OnKey(self, evt):
        keyCode = evt.GetKeyCode()

        if keyCode == wx.WXK_ESCAPE:  # key = esc
            self.onClose(evt=None)

        evt.Skip()

    def onClose(self, evt):
        """Destroy this frame."""

        self.Destroy()
    # ----

    def makeGUI(self):

        # make panel
        panel = self.makePanel()

        # pack element
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(panel, 1, wx.EXPAND, 5)

        # fit layout
        self.mainSizer.Fit(self)
        self.SetSizer(self.mainSizer)

    def makePanel(self):

        panel = wx.Panel(self, -1, size=(-1, -1))
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        # make editor
        self.information = wx.StaticText(panel, -1, "", size=(-1, -1))

        # make buttons
        self.okBtn = wx.Button(panel, wx.ID_OK, "OK", size=(-1, 22))
        self.okBtn.Bind(wx.EVT_BUTTON, self.onClose)

        btn_grid = wx.GridBagSizer(5, 5)
        y = 0
        btn_grid.Add(self.okBtn, (y, 0), wx.GBSpan(1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)

        # pack elements
        grid = wx.GridBagSizer(5, 5)
        y = 0
        grid.Add(self.information, (0, 0), wx.GBSpan(4, 8), flag=wx.ALIGN_TOP | wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(btn_grid, (4, 0), wx.GBSpan(1, 8), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
        mainSizer.Add(grid, 0, wx.EXPAND, 10)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizerAndFit(mainSizer)

        return panel

