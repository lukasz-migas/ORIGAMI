# -*- coding: utf-8 -*-

# Load libraries
import wx       
from ids import ID_addNewOverlayDoc 
import wx.lib.mixins.listctrl as listmix
import itertools
from operator import itemgetter
from origamiStyles import *
from pandas import DataFrame
from toolbox import isempty, str2num, str2int, isnumber
from numpy import arange


def dlgBox(exceptionTitle="", exceptionMsg="", type="Error"):
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
     

     
    dlg = wx.MessageDialog(None, exceptionMsg, exceptionTitle, dlgStyle)
    result = dlg.ShowModal()
    
    if type == "Question":
        return result

def dlgAsk(message='', defaultValue=''):
    dlg = wx.TextEntryDialog(None, # parent
                             message, 
                             defaultValue=defaultValue)
    dlg.ShowModal()
    result = dlg.GetValue()
    dlg.Destroy()
    return result

class ListCtrl(wx.ListCtrl):
    """ListCtrl"""
     
    def __init__(self, parent, id=-1, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.LC_REPORT):
        wx.ListCtrl.__init__(self, parent, id, pos, size, style)
#         listmix.CheckListCtrlMixin.__init__(self)

class panelCompareMS(wx.MiniFrame):
    """
    Simple GUI panel to select two MS amd plot them together
    """
    def __init__(self, parent, presenter, keyList):
        wx.MiniFrame.__init__(self, parent,-1, 'Select MS to compare...', size=(420, 300), 
                              style=wx.DEFAULT_FRAME_STYLE & ~ 
                              (wx.RESIZE_BORDER | wx.RESIZE_BOX | wx.MAXIMIZE_BOX))

        self.parent = parent
        self.presenter = presenter
        self.documentList = keyList
    
        # make gui items
        self.makeGUI()
        
        wx.EVT_CLOSE(self, self.onClose)

    def onClose(self, evt):
        """Destroy this frame."""
        
        # If pressed Close, return nothing of value
        self.presenter.currentDoc == None
        
        self.Destroy()
    # ----
    
    def makeGUI(self):
               
        # make panel
        panel = self.makeSelectionPanel()
        
        # pack element
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(panel, 0, wx.EXPAND, 0)
        
        
    def makeSelectionPanel(self):

        panel = wx.Panel(self, -1)
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        
        msFile1_label = wx.StaticText(panel, -1, "File 1:")
        self.msFile1_choice = wx.Choice(panel, -1, 
                                             choices=self.documentList, 
                                             size=(300, -1))
        self.documentList_choice.Select(0)
        
        msFile2_label = wx.StaticText(panel, -1, "File 2:")
        self.msFile2_choice = wx.Choice(panel, -1, 
                                             choices=self.documentList, 
                                             size=(300, -1))
        self.invertAxes = makeCheckbox(panel, 
                                              u"Invert axes")
               
        self.okBtn = wx.Button(panel, wx.ID_OK, "Select", size=(-1, 22))
        self.showBtn = wx.Button(panel, -1, "Show", 
                                size=(-1, 22))
        self.cancelBtn = wx.Button(panel, -1, "Cancel", size=(-1, 22))
        
        GRIDBAG_VSPACE = 7
        GRIDBAG_HSPACE = 5
        PANEL_SPACE_MAIN = 10
        
        # pack elements
        grid = wx.GridBagSizer(GRIDBAG_VSPACE, GRIDBAG_HSPACE)

        grid.Add(msFile1_label, (0,0))
        grid.Add(self.msFile1_choice, (0,1), wx.GBSpan(1,3))
        grid.Add(msFile2_label, (1,0))
        grid.Add(self.msFile2_choice, (1,1), wx.GBSpan(1,3))
        grid.Add(self.invertAxes, (2,0), wx.GBSpan(1,1))
        
        grid.Add(self.okBtn, (3,0), wx.GBSpan(1,1))
        grid.Add(self.showBtn, (3,1), wx.GBSpan(1,1))
        grid.Add(self.cancelBtn, (3,2), wx.GBSpan(1,1))

        mainSizer.Add(grid, 0, wx.ALIGN_CENTER|wx.ALL, PANEL_SPACE_MAIN)
        
        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)

        return panel

class panelSelectDocument(wx.Dialog):
    """
    Duplicate ions
    """
    def __init__(self, parent, presenter, keyList, allowNewDoc=True):
        wx.Dialog.__init__(self, parent,-1, 'Select document...', size=(400, 300), 
                              style=wx.DEFAULT_FRAME_STYLE & ~ 
                              (wx.RESIZE_BORDER | wx.RESIZE_BOX | wx.MAXIMIZE_BOX))

        self.parent = parent
        self.presenter = presenter
        self.documentList = keyList
        self.allowNewDoc = allowNewDoc
    
        # make gui items
        self.makeGUI()
        
        wx.EVT_CLOSE(self, self.onClose)

    def onClose(self, evt):
        """Destroy this frame."""
        
        # If pressed Close, return nothing of value
        self.presenter.currentDoc == None
        
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

        grid.Add(documentList_label, (0,0))
        grid.Add(self.documentList_choice, (0,1), wx.GBSpan(1,3))
        
        grid.Add(self.okBtn, (1,0), wx.GBSpan(1,1))
        grid.Add(self.addBtn, (1,1), wx.GBSpan(1,1))
        grid.Add(self.cancelBtn, (1,2), wx.GBSpan(1,1))

        mainSizer.Add(grid, 0, wx.ALIGN_CENTER|wx.ALL, PANEL_SPACE_MAIN)
        
        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)

        return panel
    
    def onSelectDocument(self, evt):
        
        docName = self.documentList_choice.GetStringSelection()
        self.presenter.currentDoc = docName
        self.EndModal(wx.OK)
        
    def onNewDocument(self, evt):
        self.presenter.onAddBlankDocument(evt=evt)
        self.EndModal(wx.OK)
       
class panelCalibrantDB(wx.MiniFrame):
    """
    Simple GUI panel to display CCS calibrant database selection
    """
    def __init__(self, parent, presenter, config, mode):
        wx.MiniFrame.__init__(self, parent,-1, 'Select protein...', size=(-1, -1), 
                              style=wx.DEFAULT_FRAME_STYLE |wx.RESIZE_BORDER | 
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

        panel = wx.Panel(self, -1, size=(-1,-1))
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        
        self.peaklist = ListCtrl(panel, style=wx.LC_REPORT)
        self.peaklist.InsertColumn(0,u'Protein', width=150)
        self.peaklist.InsertColumn(1,u'MW (kDa)', width=80)
        self.peaklist.InsertColumn(2,u'Units', width=60)
        if self.mode == 'calibrants':
            # TODO : add m/z
            self.peaklist.InsertColumn(3,u'z', width=40)
            self.peaklist.InsertColumn(4,u'm/z (kDa)', width=80)
            self.peaklist.InsertColumn(5,u'He(+)', width=60)
            self.peaklist.InsertColumn(6,u'N2(+)', width=60)
            self.peaklist.InsertColumn(7,u'He(-)', width=60)
            self.peaklist.InsertColumn(8,u'N2(-)', width=60)
            self.peaklist.InsertColumn(9,u'State', width=100)
            self.peaklist.InsertColumn(10,u'Source', width=60)


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
        PANEL_SPACE_MAIN = 10
        
        # pack elements
        grid = wx.GridBagSizer(GRIDBAG_VSPACE, GRIDBAG_HSPACE)
        grid.Add(self.addBtn, (0,0), wx.GBSpan(1,1))
        grid.Add(self.selectBtn, (0,1), wx.GBSpan(1,1))
        grid.Add(self.cancelBtn, (0,2), wx.GBSpan(1,1))
        
        mainSizer.Add(self.peaklist, 1, wx.EXPAND, 2)
        mainSizer.Add(grid, 0, wx.EXPAND, 10)

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
            protein = self.peaklist.GetItem(self.currentItem,self.config.ccsDBColNames['protein']).GetText()
            mw = self.peaklist.GetItem(self.currentItem,self.config.ccsDBColNames['mw']).GetText()
            
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
                tempData = list(item for item,_ in itertools.groupby(tempData))
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
                if (col==self.config.ccsDBColNames['mw'] or 
                    col==self.config.ccsDBColNames['ion'] or 
                    col==self.config.ccsDBColNames['hePos'] or 
                    col==self.config.ccsDBColNames['n2Pos'] or 
                    col==self.config.ccsDBColNames['heNeg'] or 
                    col==self.config.ccsDBColNames['n2Neg']):
                    itemData = str2num(item.GetText())
                    if itemData == None: itemData = 0
                    tempRow.append(itemData)
                # Integers
                elif (col==self.config.ccsDBColNames['units'] or 
                    col==self.config.ccsDBColNames['charge']):
                    itemData = str2int(item.GetText())
                    if itemData == None: itemData = 0
                    tempRow.append(itemData)
                # Text
                else:
                    tempRow.append(item.GetText())
            tempData.append(tempRow)
            
        # Sort data  
        tempData.sort(key = itemgetter(column), reverse=self.reverse)
        # Clear table
        self.peaklist.DeleteAllItems()
        
        # Reinstate data
        rowList = arange(len(tempData))
        for row in rowList:
            self.peaklist.Append(tempData[row])
     
class panelRenameItem(wx.Dialog):
    def __init__(self, parent, presenter, title):
        wx.Dialog.__init__(self, parent,-1, 'Rename...', size=(400, 300), 
                              style=wx.DEFAULT_FRAME_STYLE & ~ 
                              (wx.RESIZE_BORDER | wx.RESIZE_BOX | wx.MAXIMIZE_BOX))

        self.parent = parent
        self.presenter = presenter
        self.title = title
        self.SetTitle('Document: '+ self.title)

        # make gui items
        self.makeGUI()
        
        wx.EVT_CLOSE(self, self.onClose)
        
        self.Centre()
        self.Layout()
        
    def onClose(self, evt):
        """Destroy this frame."""
        
        self.Destroy()
    # ----
    
    def makeGUI(self):
               
        # make panel
        panel = self.makeSelectionPanel()
        
        # pack element
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(panel, 1, wx.EXPAND, 10)
        
        # bind
        self.okBtn.Bind(wx.EVT_BUTTON, self.onChangeLabel, id=wx.ID_OK)
        self.cancelBtn.Bind(wx.EVT_BUTTON, self.onClose)
        self.newName_value.Bind(wx.EVT_TEXT, self.onChangeLabel)
        
        # fit layout
        self.mainSizer.Fit(self)
        self.SetSizer(self.mainSizer)
        self.SetMinSize((500, 100))
    
    def makeSelectionPanel(self):

        panel = wx.Panel(self, -1)
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        BOX_SIZE = 400
        oldName_label = wx.StaticText(panel, -1, "Old name:")
        self.oldName_value =  wx.TextCtrl(panel, -1, "", size=(BOX_SIZE, 40),
                                          style=wx.TE_READONLY|wx.TE_WORDWRAP)
        self.oldName_value.SetValue(self.parent.extractData)
        
        newName_label = wx.StaticText(panel, -1, "New name:")
        self.newName_value =  wx.TextCtrl(panel, -1, "", size=(BOX_SIZE, -1))
        
        note_label = wx.StaticText(panel, -1, "Note:")
        self.note_value = wx.StaticText(panel, -1, "", size=(BOX_SIZE, 40))
        self.note_value.Wrap(BOX_SIZE)
        self.note_value.SetLabel(self.parent.renameNote)
               
        self.okBtn = wx.Button(panel, wx.ID_OK, "Ok", size=(-1, 22))
        self.cancelBtn = wx.Button(panel, -1, "Cancel", size=(-1, 22))

        # pack elements
        grid = wx.GridBagSizer(5, 5)

        grid.Add(oldName_label, (0,0))
        grid.Add(self.oldName_value, (0,1), wx.GBSpan(1,5))
        grid.Add(newName_label, (1,0))
        grid.Add(self.newName_value, (1,1), wx.GBSpan(1,5))
        grid.Add(note_label, (2,0))
        grid.Add(self.note_value, (2,1), wx.GBSpan(2,5))
        
        grid.Add(self.okBtn, (4,0), wx.GBSpan(1,1))
        grid.Add(self.cancelBtn, (4,1), wx.GBSpan(1,1))

        mainSizer.Add(grid, 0, wx.EXPAND, 10)
        
        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizerAndFit(mainSizer)

        return panel
    
    def onChangeLabel(self, evt):
        """ change label of the selected item """
        
        self.parent.newName = self.newName_value.GetValue()
        
        if evt.GetId() == wx.ID_OK:
            self.onClose(evt=None)


        
        
        