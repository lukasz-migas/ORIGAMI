# -*- coding: utf-8 -*-

# Load libraries
import itertools
from operator import itemgetter
from numpy import arange, transpose, argmax, round, max, median
from numpy import sum as npsum
import wx
from wx.lib.pubsub import pub 
import wx.lib.mixins.listctrl as listmix
from ids import (ID_addNewOverlayDoc, ID_extraSettings_plot1D, ID_processSettings_MS,
                 ID_extraSettings_legend, ID_compareMS_MS_1, ID_compareMS_MS_2,
                 ID_helpNewVersion, ID_saveAllDocuments)
from styles import makeCheckbox, validator, makeSuperTip, makeStaticBox, makeToggleBtn
from toolbox import (str2num, str2int, convertRGB1to255, convertRGB255to1, num2str, 
                     isnumber, getNarrow1Ddata, dir_extra, findPeakMax, find_nearest,
                     MidpointNormalize)
from help import OrigamiHelp as help
from icons import IconContainer as icons
import wx.html
import webbrowser
import plots as plots
from unidec_modules.unidectools import make_peak_shape, isolated_peak_fit
import os
import matplotlib
import matplotlib.ticker as ticker

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
    dlg = wx.TextEntryDialog(None, # parent 
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

class panelAsk(wx.Dialog):
    """
    Duplicate ions
    """
    def __init__(self, parent, presenter, **kwargs):
        wx.Dialog.__init__(self, parent,-1, 'Edit parameters...', size=(400, 300), 
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
        
    
        # make gui items
        self.makeGUI()
        
        wx.EVT_CLOSE(self, self.onClose)
        self.Bind(wx.EVT_CHAR_HOOK, self.OnKey)

    def OnKey(self, evt):
        keyCode = evt.GetKeyCode()
        if keyCode == wx.WXK_ESCAPE:
            self.onClose(evt=None)
            
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
        
        grid.Add(self.input_label, (0,0), wx.GBSpan(2,3), 
                 flag=wx.ALIGN_RIGHT|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        
        grid.Add(self.input_value, (0,3), wx.GBSpan(1,1), 
                 flag=wx.ALIGN_CENTER_VERTICAL)
        
        grid.Add(self.okBtn, (2,2), wx.GBSpan(1,1))
        grid.Add(self.cancelBtn, (2,3), wx.GBSpan(1,1))

        mainSizer.Add(grid, 0, wx.ALIGN_CENTER|wx.ALL, PANEL_SPACE_MAIN)
        
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
        self.presenter.currentDoc = None
        
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
    def __init__(self, parent, presenter, title, **kwargs):
        wx.Dialog.__init__(self, parent,-1, 'Rename...', size=(400, 300), 
                           style=wx.DEFAULT_FRAME_STYLE & ~ 
                           (wx.RESIZE_BORDER | wx.RESIZE_BOX | wx.MAXIMIZE_BOX))

        self.parent = parent
        self.presenter = presenter
        self.title = title
        self.SetTitle('Document: '+ self.title)
        
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
        if keyCode == wx.WXK_ESCAPE: # key = esc
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
        self.oldName_value =  wx.TextCtrl(panel, -1, "", size=(BOX_SIZE, 40),
                                          style=wx.TE_READONLY|wx.TE_WORDWRAP)
        self.oldName_value.SetValue(self.kwargs['current_name'])
        
        newName_label = wx.StaticText(panel, -1, "Edit name:")
        self.newName_value =  wx.TextCtrl(panel, -1, "", size=(BOX_SIZE, -1), style=wx.TE_PROCESS_ENTER)
        self.newName_value.SetValue(self.kwargs['current_name'])
        self.newName_value.SetFocus()

        
        note_label = wx.StaticText(panel, -1, "Final name:")
        self.note_value = wx.StaticText(panel, -1, "", size=(BOX_SIZE, 40))
        self.note_value.Wrap(BOX_SIZE)
               
        self.okBtn = wx.Button(panel, wx.ID_OK, "Rename", size=(-1, 22))
        self.cancelBtn = wx.Button(panel, wx.ID_CANCEL, "Cancel", size=(-1, 22))

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
        wx.MiniFrame.__init__(self, parent,-1, 'Sequence analysis...', size=(-1, -1), 
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
        if keyCode == wx.WXK_ESCAPE: # key = esc
            self.onClose(evt=None)
        elif keyCode == 83: # key = s
            self.onSelect(evt=None)
        elif keyCode == 85: # key = u
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

        panel = wx.Panel(self, -1, size=(-1,-1))
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        
        # make editor
        sequence_label = wx.StaticText(panel, -1, "Sequence:")
        self.sequence_value = wx.TextCtrl(panel, -1, "", size=(400, 200))

        self.sequence_loadBtn = wx.BitmapButton(panel, wx.ID_ANY,
                                                self.icons.iconsLib['load16'],
                                                size=(26, 26),
                                                style=wx.BORDER_DOUBLE | wx.ALIGN_CENTER_VERTICAL)
        
        self.sequence_converter = wx.BitmapButton(panel, wx.ID_ANY,
                                                  self.icons.iconsLib['load16'], # change to 3 <-> 1
                                                  size=(26, 26),
                                                  style=wx.BORDER_DOUBLE | wx.ALIGN_CENTER_VERTICAL)
        
        minCCS_label = wx.StaticText(panel, -1, u"Compact CCS (Å²):")
        maxCCS_label = wx.StaticText(panel, -1, u"Extended CCS (Å²):")
        kappa_label = wx.StaticText(panel, -1, u"κ value:")
        
        self.minCCS_value = wx.StaticText(panel, -1, "")
        self.maxCCS_value = wx.StaticText(panel, -1, "")
        self.kappa_value = wx.StaticText(panel, -1, "")                     
        
        # make buttons
        self.calculateBtn = wx.Button(panel, wx.ID_OK, "Calculate", size=(-1, 22))
        self.plotBtn = wx.Button(panel, wx.ID_OK, "Plot", size=(-1, 22))
        self.cancelBtn = wx.Button(panel, wx.ID_OK, "Cancel", size=(-1, 22))

        self.calculateBtn.Bind(wx.EVT_BUTTON, self.onSelect)
        self.plotBtn.Bind(wx.EVT_BUTTON, self.onPlot)
        self.cancelBtn.Bind(wx.EVT_BUTTON, self.onClose)

        # pack elements
        grid = wx.GridBagSizer(5, 5)
        y = 0
        grid.Add(sequence_label, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_TOP)
        grid.Add(self.sequence_value, (y,1), wx.GBSpan(2,6), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.sequence_loadBtn, (y,7), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT|wx.ALIGN_TOP)
        y = y + 1
        grid.Add(self.sequence_converter, (y,7), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT|wx.ALIGN_TOP)
        y = y+1
        grid.Add(minCCS_label, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.minCCS_value, (y,1), wx.GBSpan(1,6), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        y = y+1
        grid.Add(maxCCS_label, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.maxCCS_value, (y,1), wx.GBSpan(1,6), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        y = y+1
        grid.Add(kappa_label, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.kappa_value, (y,1), wx.GBSpan(1,6), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        y = y+1
        grid.Add(self.calculateBtn, (y,2), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(self.plotBtn, (y,3), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(self.cancelBtn, (y,4), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
         
        mainSizer.Add(grid, 0, wx.EXPAND, 10)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizerAndFit(mainSizer)

        return panel
   
    def updateMS(self, evt):
        pass

        if evt != None:
            evt.Skip() 

class panelModifyIonSettings(wx.MiniFrame):
    """
    """
    
    def __init__(self, parent, presenter, config, **kwargs):
        wx.MiniFrame.__init__(self, parent,-1, 'Modify settings...', size=(-1, -1), 
                              style=wx.DEFAULT_FRAME_STYLE & ~wx.RESIZE_BORDER)
        
        self.parent = parent
        self.presenter = presenter
        self.config = config
        self.icons = icons()
        self.importEvent = False
                
        self.SetTitle(kwargs['ionName'])
        self.itemInfo = kwargs
        
        # check values
        if self.itemInfo['mask'] in ['', None, 'None']:
            self.itemInfo['mask'] = 1
            
        if self.itemInfo['alpha'] in ['', None, 'None']:
            self.itemInfo['alpha'] = 1
            
        if self.itemInfo['colormap'] in ['', None, 'None']:
            self.itemInfo['colormap'] = self.config.currentCmap
            
        if self.itemInfo['color'][0] == -1:
              self.itemInfo['color'] = (1, 1, 1, 255)
                
        if self.itemInfo['charge'] in ['', None, 'None']:
            self.itemInfo['charge'] = ""
                
        # make gui items
        self.makeGUI()
        
        self.Centre()
        self.Layout()
        self.SetFocus()

        # bind
        wx.EVT_CLOSE(self, self.onClose)
        self.Bind(wx.EVT_CHAR_HOOK, self.OnKey)
        
        # fire-up events
        self.onSetupParameters(evt=None)
    # ----
    
    def OnKey(self, evt):
        keyCode = evt.GetKeyCode()
        if keyCode == wx.WXK_ESCAPE:
            self.onClose(evt=None)
#         elif keyCode == 83:
#             self.onSelect(evt=None)
        
        evt.Skip()
                
    def onClose(self, evt):
        """Destroy this frame."""
        
        self.Destroy()
    # ----
        
    def onSelect(self, evt):
        self.OnAssignColor(evt=None)
        self.parent.onUpdateDocument(itemInfo=self.itemInfo, evt=None)
        self.Destroy()
        
    def makeGUI(self):
        
        # make panel
        panel = self.makePanel()
        
        # pack element
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(panel, 1, wx.EXPAND, 0)
        
        # fit layout
        self.mainSizer.Fit(self)
        self.SetSizer(self.mainSizer)
        
    def makePanel(self):

        panel = wx.Panel(self, -1, size=(-1,-1))
        mainSizer = wx.BoxSizer(wx.VERTICAL)
                
        select_label = wx.StaticText(panel, wx.ID_ANY, u"Select:")
        self.origami_select_value = makeCheckbox(panel, u"")
        self.origami_select_value.Bind(wx.EVT_CHECKBOX, self.onApply)
        
        filename_label = wx.StaticText(panel, wx.ID_ANY, u"Filename:")
        self.origami_filename_value = wx.TextCtrl(panel, wx.ID_ANY, u"", style=wx.TE_READONLY)
        
        ion_label = wx.StaticText(panel, wx.ID_ANY, u"Ion:")
        self.origami_ion_value = wx.TextCtrl(panel, wx.ID_ANY, u"", style=wx.TE_READONLY)

        label_label = wx.StaticText(panel, wx.ID_ANY,
                                    u"Label:", wx.DefaultPosition, 
                                    wx.DefaultSize, wx.ALIGN_LEFT)
        self.origami_label_value = wx.TextCtrl(panel, -1, "", size=(90, -1))
        self.origami_label_value.SetValue(self.itemInfo['label'])
        self.origami_label_value.Bind(wx.EVT_TEXT, self.onApply)

        charge_label = wx.StaticText(panel, wx.ID_ANY, u"Charge:")
        self.origami_charge_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('intPos'))
        self.origami_charge_value.Bind(wx.EVT_TEXT, self.onApply)
        
        min_threshold_label = wx.StaticText(panel, wx.ID_ANY, u"Min threshold:")
        self.origami_min_threshold_value = wx.SpinCtrlDouble(panel, wx.ID_ANY,
                                            value="1",min=0.0, max=1.0,
                                            initial=1.0, inc=0.05, size=(60,-1))
        self.origami_min_threshold_value.SetValue(self.itemInfo['min_threshold'])
        self.origami_min_threshold_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)

        max_threshold_label = wx.StaticText(panel, wx.ID_ANY, u"Max threshold:")
        self.origami_max_threshold_value = wx.SpinCtrlDouble(panel, wx.ID_ANY,
                                            value="1",min=0.0, max=1.0,
                                            initial=1.0, inc=0.05, size=(60,-1))
        self.origami_max_threshold_value.SetValue(self.itemInfo['max_threshold'])
        self.origami_max_threshold_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        
        mask_label = wx.StaticText(panel, wx.ID_ANY, u"Mask:")
        self.origami_mask_value = wx.SpinCtrlDouble(panel, wx.ID_ANY,
                                            value="1",min=0.0, max=1.0,
                                            initial=1.0, inc=0.05, size=(60,-1))
        self.origami_mask_value.SetValue(self.itemInfo['mask'])
        self.origami_mask_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        
        transparency_label = wx.StaticText(panel, wx.ID_ANY, u"Transparency:")
        self.origami_transparency_value = wx.SpinCtrlDouble(panel, wx.ID_ANY,
                                                    value="1",min=0.0, max=1.0,
                                                    initial=1.0, inc=0.05, size=(60,-1))
        self.origami_transparency_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        
        colormap_label = wx.StaticText(panel, -1, "Colormap:")
        self.origami_colormap_value= wx.Choice(panel, -1, 
                                               choices=self.config.cmaps2,
                                               size=(-1, -1))
        self.origami_colormap_value.Bind(wx.EVT_CHOICE, self.onApply)
        
        self.origami_restrictColormap_value = makeCheckbox(panel, u"")
        self.origami_restrictColormap_value.Bind(wx.EVT_CHECKBOX, self.onRestrictCmaps)
        
        color_label = wx.StaticText(panel, -1, "Color:")
        self.origami_color_value = wx.Button(panel, wx.ID_ANY, u"", wx.DefaultPosition, 
                                     wx.Size( 26, 26 ), 0)
        self.origami_color_value.SetBackgroundColour(self.itemInfo['color'])
        self.origami_color_value.Bind(wx.EVT_BUTTON, self.OnAssignColor)

        origami_staticBox = makeStaticBox(panel, "Collision voltage parameters", size=(-1, -1), color=wx.BLACK)
        origami_staticBox.SetSize((-1,-1))
        origami_box_sizer = wx.StaticBoxSizer(origami_staticBox, wx.HORIZONTAL)   

        method_label = wx.StaticText(panel, -1, "Acquisition method:")
        self.origami_method_value= wx.Choice(panel, -1, 
                                             choices=self.config.origami_acquisition_choices,
                                             size=(-1, -1))
        self.origami_method_value.SetStringSelection(self.itemInfo['method'])
        self.origami_method_value.Bind(wx.EVT_CHOICE, self.enableDisableBoxes)
        self.origami_method_value.Bind(wx.EVT_CHOICE, self.onApply)
        
        self.origami_loadParams = wx.BitmapButton(panel, wx.ID_ANY,
                                                  self.icons.iconsLib['load16'],
                                                  size=(26, 26),
                                                  style=wx.BORDER_DOUBLE | wx.ALIGN_CENTER_VERTICAL)
                
        spv_label = wx.StaticText(panel, wx.ID_ANY, u"Scans per voltage:")
        self.origami_scansPerVoltage_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('intPos'))
        self.origami_scansPerVoltage_value.SetValue(str(self.config.origami_spv))
        self.origami_scansPerVoltage_value.Bind(wx.EVT_TEXT, self.onApply)
        
        scan_label = wx.StaticText(panel, wx.ID_ANY, u"First scan:")
        self.origami_startScan_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('intPos'))
        self.origami_startScan_value.Bind(wx.EVT_TEXT, self.onApply)
        
        startVoltage_label = wx.StaticText(panel, wx.ID_ANY, u"First voltage:")
        self.origami_startVoltage_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('floatPos'))
        self.origami_startVoltage_value.Bind(wx.EVT_TEXT, self.onApply)
        
        endVoltage_label = wx.StaticText(panel, wx.ID_ANY, u"Final voltage:")
        self.origami_endVoltage_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('floatPos'))
        self.origami_endVoltage_value.Bind(wx.EVT_TEXT, self.onApply)
        
        stepVoltage_label = wx.StaticText(panel, wx.ID_ANY, u"Voltage step:")
        self.origami_stepVoltage_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('floatPos'))
        self.origami_stepVoltage_value.Bind(wx.EVT_TEXT, self.onApply)
        
        boltzmann_label = wx.StaticText(panel, wx.ID_ANY, u"Boltzmann offset:")
        self.origami_boltzmannOffset_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                                         validator=validator('floatPos'))
        self.origami_boltzmannOffset_value.Bind(wx.EVT_TEXT, self.onApply)
        
        exponentialPercentage_label = wx.StaticText(panel, wx.ID_ANY, u"Exponential percentage:")
        self.origami_exponentialPercentage_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('floatPos'))
        self.origami_exponentialPercentage_value.Bind(wx.EVT_TEXT, self.onApply)
        
        exponentialIncrement_label = wx.StaticText(panel, wx.ID_ANY, u"Exponential increment:")
        self.origami_exponentialIncrement_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('floatPos'))
        self.origami_exponentialIncrement_value.Bind(wx.EVT_TEXT, self.onApply)
       
        
        horizontal_line = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        
        self.combineBtn = wx.Button(panel, wx.ID_OK, "Combine", size=(-1, 22))
        self.applyBtn = wx.Button(panel, wx.ID_OK, "Apply", size=(-1, 22))
        self.cancelBtn = wx.Button(panel, wx.ID_OK, "Cancel", size=(-1, 22))
        
        self.applyBtn.Bind(wx.EVT_BUTTON, self.onSelect)
        self.cancelBtn.Bind(wx.EVT_BUTTON, self.onClose)
        
        # pack elements
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(select_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.origami_select_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(filename_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.origami_filename_value, (n,1), wx.GBSpan(1,2), flag=wx.EXPAND)
        n = n + 1
        grid.Add(ion_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.origami_ion_value, (n,1), wx.GBSpan(1,2), flag=wx.EXPAND)
        n = n + 1
        grid.Add(label_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.origami_label_value, (n,1), wx.GBSpan(1,2), flag=wx.EXPAND)
        n = n + 1
        grid.Add(charge_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.origami_charge_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(min_threshold_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.origami_min_threshold_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(max_threshold_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.origami_max_threshold_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(colormap_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.origami_colormap_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        grid.Add(self.origami_restrictColormap_value, (n,2), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(color_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.origami_color_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(mask_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.origami_mask_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(transparency_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.origami_transparency_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        
        
        origami_grid = wx.GridBagSizer(2, 2)
        n = 0
        origami_grid.Add(method_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        origami_grid.Add(self.origami_method_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        origami_grid.Add(self.origami_loadParams, (n,2), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT)
        n = n + 1
        origami_grid.Add(spv_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        origami_grid.Add(self.origami_scansPerVoltage_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        origami_grid.Add(scan_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        origami_grid.Add(self.origami_startScan_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        origami_grid.Add(startVoltage_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        origami_grid.Add(self.origami_startVoltage_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        origami_grid.Add(endVoltage_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        origami_grid.Add(self.origami_endVoltage_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        origami_grid.Add(stepVoltage_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        origami_grid.Add(self.origami_stepVoltage_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        origami_grid.Add(boltzmann_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        origami_grid.Add(self.origami_boltzmannOffset_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        origami_grid.Add(exponentialPercentage_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        origami_grid.Add(self.origami_exponentialPercentage_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        origami_grid.Add(exponentialIncrement_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        origami_grid.Add(self.origami_exponentialIncrement_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        origami_box_sizer.Add(origami_grid, 0, wx.EXPAND, 10)

        n = 11
        grid.Add(origami_box_sizer, (n,0), wx.GBSpan(1,3), flag=wx.EXPAND)
        n = n + 1
        grid.Add(horizontal_line, (n,0), wx.GBSpan(1,3), flag=wx.EXPAND)
        n = n + 1
        grid.Add(self.combineBtn, (n,0), wx.GBSpan(1,1))
        grid.Add(self.applyBtn, (n,1), wx.GBSpan(1,1))
        grid.Add(self.cancelBtn, (n,2), wx.GBSpan(1,1))
        
        mainSizer.Add(grid, 0, wx.EXPAND, 10)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizerAndFit(mainSizer)
        
        self.enableDisableBoxes(evt=None)

        return panel
           
    def onApply(self, evt):
        if self.importEvent: return
        self.parent.peaklist.CheckItem(self.itemInfo['id'], self.origami_select_value.GetValue())
        self.parent.peaklist.SetStringItem(self.itemInfo['id'], self.config.peaklistColNames['charge'], 
                                           self.origami_charge_value.GetValue())
        self.parent.peaklist.SetStringItem(self.itemInfo['id'], self.config.peaklistColNames['colormap'], 
                                           self.origami_colormap_value.GetStringSelection())
        self.parent.peaklist.SetStringItem(self.itemInfo['id'], self.config.peaklistColNames['mask'], 
                                           num2str(self.origami_mask_value.GetValue()))
        self.parent.peaklist.SetStringItem(self.itemInfo['id'], self.config.peaklistColNames['alpha'], 
                                           num2str(self.origami_transparency_value.GetValue()))
        self.parent.peaklist.SetStringItem(self.itemInfo['id'], self.config.peaklistColNames['method'], 
                                           self.origami_method_value.GetStringSelection())
        self.parent.peaklist.SetStringItem(self.itemInfo['id'], self.config.peaklistColNames['label'], 
                                           self.origami_label_value.GetValue())
        
        if self.itemInfo['parameters'] == None:
            self.itemInfo['parameters'] = {}
        self.itemInfo['parameters']['firstVoltage'] = str2int(self.origami_startScan_value.GetValue())
        self.itemInfo['parameters']['startV'] = str2num(self.origami_startVoltage_value.GetValue())
        self.itemInfo['parameters']['endV'] = str2num(self.origami_endVoltage_value.GetValue())
        self.itemInfo['parameters']['stepV'] = str2num(self.origami_stepVoltage_value.GetValue())
        self.itemInfo['parameters']['spv'] = str2int(self.origami_scansPerVoltage_value.GetValue())
        self.itemInfo['parameters']['expIncrement'] = str2num(self.origami_exponentialIncrement_value.GetValue())
        self.itemInfo['parameters']['expPercent'] = str2num(self.origami_exponentialPercentage_value.GetValue())
        self.itemInfo['parameters']['dx'] = str2num(self.origami_boltzmannOffset_value.GetValue())
        
        # update ion information
        self.itemInfo['charge'] = self.origami_charge_value.GetValue()
        self.itemInfo['colormap'] = self.origami_colormap_value.GetStringSelection()
        self.itemInfo['mask'] = self.origami_mask_value.GetValue()
        self.itemInfo['alpha'] = self.origami_transparency_value.GetValue()
        self.itemInfo['label'] = self.origami_label_value.GetValue()
        self.itemInfo['min_threshold'] = self.origami_min_threshold_value.GetValue()
        self.itemInfo['max_threshold'] = self.origami_max_threshold_value.GetValue()
        
        # update ion value
        try:
            charge = str2int(self.itemInfo['charge'])
            ion_centre = (str2num(self.itemInfo['mzStart']) + str2num(self.itemInfo['mzEnd']))/2
            mw = (ion_centre - self.config.elementalMass['Hydrogen'] * charge) * charge
            ion_value = (u"%s  ~%.2f Da") % (self.itemInfo['ionName'], mw)
            self.origami_ion_value.SetValue(ion_value)
        except:
            self.origami_ion_value.SetValue(self.itemInfo['ionName'])
        
        self.OnAssignColor(evt=None)
        self.parent.onUpdateDocument(itemInfo=self.itemInfo, evt=None)
        
        if evt != None:
            evt.Skip() 
         
    def onSetupParameters(self, evt):
        self.importEvent = True
        self.origami_select_value.SetValue(self.itemInfo['select'])
        self.origami_filename_value.SetValue(self.itemInfo['document'])
        
        try:
            charge = str2int(self.itemInfo['charge'])
            ion_centre = (str2num(self.itemInfo['mzStart']) + str2num(self.itemInfo['mzEnd']))/2
            mw = (ion_centre - self.config.elementalMass['Hydrogen'] * charge) * charge
            ion_value = (u"%s  ~%.2f Da") % (self.itemInfo['ionName'], mw)
            self.origami_ion_value.SetValue(ion_value)
        except:
            self.origami_ion_value.SetValue(self.itemInfo['ionName'])
            
        self.origami_charge_value.SetValue(str(self.itemInfo['charge']))
        self.origami_label_value.SetValue(self.itemInfo['label'])
        self.origami_colormap_value.SetStringSelection(self.itemInfo['colormap'])
        self.origami_mask_value.SetValue(self.itemInfo['mask'])
        self.origami_transparency_value.SetValue(self.itemInfo['alpha'])
        self.origami_color_value.SetBackgroundColour(self.itemInfo['color'])
        self.origami_min_threshold_value.SetValue(self.itemInfo['min_threshold'])
        self.origami_max_threshold_value.SetValue(self.itemInfo['max_threshold'])
    
        if self.itemInfo['parameters'] != None:
            self.origami_method_value.SetStringSelection(self.itemInfo['parameters']['method'])
            self.origami_startScan_value.SetValue(str(self.itemInfo['parameters'].get('firstVoltage', '')))
            self.origami_scansPerVoltage_value.SetValue(str(self.itemInfo['parameters'].get('spv', '')))
            self.origami_startVoltage_value.SetValue(str(self.itemInfo['parameters'].get('startV', '')))
            self.origami_endVoltage_value.SetValue(str(self.itemInfo['parameters'].get('endV', '')))
            self.origami_stepVoltage_value.SetValue(str(self.itemInfo['parameters'].get('stepV', '')))
            self.origami_exponentialIncrement_value.SetValue(str(self.itemInfo['parameters'].get('expIncrement', '')))
            self.origami_exponentialPercentage_value.SetValue(str(self.itemInfo['parameters'].get('expPercent', '')))
            self.origami_boltzmannOffset_value.SetValue(str(self.itemInfo['parameters'].get('dx', '')))
        else:
            self.origami_startScan_value.SetValue(str(self.config.origami_startScan))
            self.origami_scansPerVoltage_value.SetValue(str(self.config.origami_spv))
            self.origami_startVoltage_value.SetValue(str(self.config.origami_startVoltage))
            self.origami_endVoltage_value.SetValue(str(self.config.origami_endVoltage))
            self.origami_stepVoltage_value.SetValue(str(self.config.origami_stepVoltage))
            self.origami_exponentialIncrement_value.SetValue(str(self.config.origami_exponentialIncrement))
            self.origami_exponentialPercentage_value.SetValue(str(self.config.origami_exponentialPercentage))
            self.origami_boltzmannOffset_value.SetValue(str(self.config.origami_boltzmannOffset))
            self.origami_method_value.SetStringSelection(self.config.origami_acquisition)
            
        self.enableDisableBoxes(evt=None)
        self.importEvent = False
        
    def onUpdateGUI(self, itemInfo):
        """
        @param itemInfo (dict): updating GUI with new item information
        """
        self.itemInfo = itemInfo
        self.SetTitle(self.itemInfo['ionName'])
        
        # check values
        if self.itemInfo['mask'] in ['', None, 'None']:
            self.itemInfo['mask'] = 1

        if self.itemInfo['alpha'] in ['', None, 'None']:
            self.itemInfo['alpha'] = 1
            
        if self.itemInfo['colormap'] in ['', None, 'None']:
            self.itemInfo['colormap'] = self.config.currentCmap
            
        if self.itemInfo['color'][0] == -1:
              self.itemInfo['color'] = (1, 1, 1, 255)
              
        if self.itemInfo['charge'] in ['', None, 'None']:
            self.itemInfo['charge'] = ""
              
        # setup values
        self.onSetupParameters(evt=None)
        
        self.SetFocus()
            
    def enableDisableBoxes(self, evt):
        
        method = self.origami_method_value.GetStringSelection()
        enableList, disableList = [], []
        if method == 'Linear':
            disableList = [self.origami_boltzmannOffset_value,self.origami_exponentialIncrement_value,
                           self.origami_exponentialPercentage_value]
            enableList = [self.origami_scansPerVoltage_value, self.origami_loadParams, 
                          self.origami_startScan_value, self.origami_startVoltage_value,
                          self.origami_endVoltage_value, self.origami_stepVoltage_value]
        elif method == 'Exponential':
            disableList = [self.origami_boltzmannOffset_value]
            enableList = [self.origami_scansPerVoltage_value, self.origami_loadParams, 
                          self.origami_startScan_value, self.origami_startVoltage_value,
                          self.origami_endVoltage_value, self.origami_stepVoltage_value,
                          self.origami_exponentialIncrement_value,
                          self.origami_exponentialPercentage_value]
        elif method == 'Boltzmann':
            disableList = []
            enableList = [self.origami_scansPerVoltage_value, 
                          self.origami_startScan_value, self.origami_startVoltage_value,
                          self.origami_endVoltage_value, self.origami_stepVoltage_value,
                          self.origami_exponentialIncrement_value,
                          self.origami_exponentialPercentage_value,
                          self.origami_boltzmannOffset_value, self.origami_loadParams]
        elif method == 'User-defined':
            disableList = [self.origami_scansPerVoltage_value, 
                          self.origami_startVoltage_value,
                          self.origami_endVoltage_value, self.origami_stepVoltage_value,
                          self.origami_exponentialIncrement_value,
                          self.origami_exponentialPercentage_value,
                          self.origami_boltzmannOffset_value]
            enableList = [self.origami_loadParams, self.origami_startScan_value]
        elif method == 'Manual':
            disableList = [self.origami_scansPerVoltage_value, 
                          self.origami_startScan_value, self.origami_startVoltage_value,
                          self.origami_endVoltage_value, self.origami_stepVoltage_value,
                          self.origami_exponentialIncrement_value,
                          self.origami_exponentialPercentage_value,
                          self.origami_boltzmannOffset_value, self.origami_loadParams]
            enableList = []
            
        for item in enableList:
            item.Enable()
        for item in disableList:
            item.Disable()
        
        if evt != None:
            evt.Skip() 

    def OnAssignColor(self, evt):
        if evt:
            color = self.parent.OnAssignColor(evt=None, 
                                                   itemID=self.itemInfo['id'], 
                                                   give_value=True)
                 
            self.origami_color_value.SetBackgroundColour(color)
        else:
            color = self.origami_color_value.GetBackgroundColour()
            self.parent.peaklist.SetItemBackgroundColour(self.itemInfo['id'], color)
              
    def onRestrictCmaps(self, evt):
        """
        The cmap list will be restricted to more limited selection
        """
        currentCmap = self.origami_colormap_value.GetStringSelection()
        narrowList = self.config.narrowCmapList
        narrowList.append(currentCmap)
        
        # remove duplicates
        narrowList = sorted(list(set(narrowList)))
         
        if self.origami_restrictColormap_value.GetValue():
            self.origami_colormap_value.Clear()
            for item in narrowList:
                self.origami_colormap_value.Append(item)
            self.origami_colormap_value.SetStringSelection(currentCmap)
        else:
            self.origami_colormap_value.Clear()
            for item in self.config.cmaps2:
                self.origami_colormap_value.Append(item)
            self.origami_colormap_value.SetStringSelection(currentCmap)
      
class panelModifyTextSettings(wx.MiniFrame):
    """
    """
    
    def __init__(self, parent, presenter, config, **kwargs):
        wx.MiniFrame.__init__(self, parent,-1, 'Modify settings...', size=(-1, -1), 
                              style=wx.DEFAULT_FRAME_STYLE & ~wx.RESIZE_BORDER)
        
        self.parent = parent
        self.presenter = presenter
        self.config = config
        self.icons = icons()
        self.importEvent = False
                
        self.SetTitle(kwargs['document'])
        self.itemInfo = kwargs
        
        # check values
        if self.itemInfo['mask'] in ['', None, 'None']:
            self.itemInfo['mask'] = 1
            
        if self.itemInfo['alpha'] in ['', None, 'None']:
            self.itemInfo['alpha'] = 1
            
        if self.itemInfo['colormap'] in ['', None, 'None']:
            self.itemInfo['colormap'] = self.config.currentCmap
            
        if self.itemInfo['color'][0] == -1:
              self.itemInfo['color'] = (1, 1, 1, 255)
              
        if self.itemInfo['charge'] in ['', None, 'None']:
            self.itemInfo['charge'] = ""
                
        # make gui items
        self.makeGUI()
                      
        self.Centre()
        self.Layout()
        self.SetFocus()
        
        # bind
        wx.EVT_CLOSE(self, self.onClose)
        self.Bind(wx.EVT_CHAR_HOOK, self.OnKey)
        
        # fire-up events
        self.onSetupParameters(evt=None)
    # ----
    
    def OnKey(self, evt):
        keyCode = evt.GetKeyCode()
        if keyCode == wx.WXK_ESCAPE:
            self.onClose(evt=None)
#         elif keyCode == 83:
#             self.onSelect(evt=None)
        
        evt.Skip()
                
    def onClose(self, evt):
        """Destroy this frame."""
        
        self.Destroy()
    # ----
        
    def onSelect(self, evt):
        self.OnAssignColor(evt=None)
        self.parent.onUpdateDocument(itemInfo=self.itemInfo, evt=None)
        self.Destroy()
        
    def makeGUI(self):
        
        # make panel
        panel = self.makePanel()
        
        # pack element
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(panel, 1, wx.EXPAND, 0)
        
        # fit layout
        self.mainSizer.Fit(self)
        self.SetSizer(self.mainSizer)
        
    def makePanel(self):

        panel = wx.Panel(self, -1, size=(-1,-1))
        mainSizer = wx.BoxSizer(wx.VERTICAL)
                
        select_label = wx.StaticText(panel, wx.ID_ANY, u"Select:")
        self.text_select_value = makeCheckbox(panel, u"")
        self.text_select_value.Bind(wx.EVT_CHECKBOX, self.onApply)
        
        filename_label = wx.StaticText(panel, wx.ID_ANY, u"Filename:")
        self.text_filename_value = wx.TextCtrl(panel, wx.ID_ANY, u"", style=wx.TE_READONLY)
        
        ion_label = wx.StaticText(panel, wx.ID_ANY, u"Ion:")
        self.text_ion_value = wx.TextCtrl(panel, wx.ID_ANY, u"", style=wx.TE_READONLY)

        label_label = wx.StaticText(panel, wx.ID_ANY,
                                    u"Label:", wx.DefaultPosition, 
                                    wx.DefaultSize, wx.ALIGN_LEFT)
        self.text_label_value = wx.TextCtrl(panel, -1, "", size=(90, -1))
        self.text_label_value.SetValue(self.itemInfo['label'])
        self.text_label_value.Bind(wx.EVT_TEXT, self.onApply)

        charge_label = wx.StaticText(panel, wx.ID_ANY, u"Charge:")
        self.text_charge_value = wx.TextCtrl(panel, -1, "", size=(-1, -1),
                                          validator=validator('intPos'))
        self.text_charge_value.Bind(wx.EVT_TEXT, self.onApply)
        
        min_threshold_label = wx.StaticText(panel, wx.ID_ANY, u"Min threshold:")
        self.text_min_threshold_value = wx.SpinCtrlDouble(panel, wx.ID_ANY,
                                            value="1",min=0.0, max=1.0,
                                            initial=1.0, inc=0.05, size=(60,-1))
        self.text_min_threshold_value.SetValue(self.itemInfo['min_threshold'])
        self.text_min_threshold_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)

        max_threshold_label = wx.StaticText(panel, wx.ID_ANY, u"Max threshold:")
        self.text_max_threshold_value = wx.SpinCtrlDouble(panel, wx.ID_ANY,
                                            value="1",min=0.0, max=1.0,
                                            initial=1.0, inc=0.05, size=(60,-1))
        self.text_max_threshold_value.SetValue(self.itemInfo['max_threshold'])
        self.text_max_threshold_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        
        mask_label = wx.StaticText(panel, wx.ID_ANY, u"Mask:")
        self.text_mask_value = wx.SpinCtrlDouble(panel, wx.ID_ANY,
                                            value="1",min=0.0, max=1.0,
                                            initial=1.0, inc=0.05, size=(60,-1))
        self.text_mask_value.SetValue(self.itemInfo['mask'])
        self.text_mask_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        
        transparency_label = wx.StaticText(panel, wx.ID_ANY, u"Transparency:")
        self.text_transparency_value = wx.SpinCtrlDouble(panel, wx.ID_ANY,
                                                    value="1",min=0.0, max=1.0,
                                                    initial=1.0, inc=0.05, size=(60,-1))
        self.text_transparency_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply)
        
        colormap_label = wx.StaticText(panel, -1, "Colormap:")
        self.text_colormap_value= wx.Choice(panel, -1, 
                                               choices=self.config.cmaps2,
                                               size=(-1, -1))
        self.text_colormap_value.Bind(wx.EVT_CHOICE, self.onApply)
        
        self.text_restrictColormap_value = makeCheckbox(panel, u"")
        self.text_restrictColormap_value.Bind(wx.EVT_CHECKBOX, self.onRestrictCmaps)
        
        color_label = wx.StaticText(panel, -1, "Color:")
        self.text_color_value = wx.Button(panel, wx.ID_ANY, u"", wx.DefaultPosition, 
                                          wx.Size( 26, 26 ), 0)
        self.text_color_value.SetBackgroundColour(self.itemInfo['color'])
        self.text_color_value.Bind(wx.EVT_BUTTON, self.OnAssignColor)
      
        horizontal_line = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        
#         self.combineBtn = wx.Button(panel, wx.ID_OK, "Combine", size=(-1, 22))
        self.applyBtn = wx.Button(panel, wx.ID_OK, "Apply", size=(-1, 22))
        self.cancelBtn = wx.Button(panel, wx.ID_OK, "Cancel", size=(-1, 22))
        
        self.applyBtn.Bind(wx.EVT_BUTTON, self.onSelect)
        self.cancelBtn.Bind(wx.EVT_BUTTON, self.onClose)
        
        # pack elements
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(select_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.text_select_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(filename_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.text_filename_value, (n,1), wx.GBSpan(1,2), flag=wx.EXPAND)
        n = n + 1
        grid.Add(ion_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.text_ion_value, (n,1), wx.GBSpan(1,2), flag=wx.EXPAND)
        n = n + 1
        grid.Add(label_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.text_label_value, (n,1), wx.GBSpan(1,2), flag=wx.EXPAND)
        n = n + 1
        grid.Add(charge_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.text_charge_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(min_threshold_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.text_min_threshold_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(max_threshold_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.text_max_threshold_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(colormap_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.text_colormap_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        grid.Add(self.text_restrictColormap_value, (n,2), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        grid.Add(color_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.text_color_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(mask_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.text_mask_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(transparency_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.text_transparency_value, (n,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        n = n + 1
        grid.Add(horizontal_line, (n,0), wx.GBSpan(1,3), flag=wx.EXPAND)
        n = n + 1
#         grid.Add(self.combineBtn, (n,0), wx.GBSpan(1,1))
        grid.Add(self.applyBtn, (n,1), wx.GBSpan(1,1))
        grid.Add(self.cancelBtn, (n,2), wx.GBSpan(1,1))
        
        mainSizer.Add(grid, 0, wx.EXPAND, 10)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizerAndFit(mainSizer)
        
        self.enableDisableBoxes(evt=None)

        return panel
           
    def onApply(self, evt):
        if self.importEvent: return
        self.parent.filelist.CheckItem(self.itemInfo['id'], self.text_select_value.GetValue())
        self.parent.filelist.SetStringItem(self.itemInfo['id'], self.config.textlistColNames['charge'], 
                                           self.text_charge_value.GetValue())
        self.parent.filelist.SetStringItem(self.itemInfo['id'], self.config.textlistColNames['colormap'], 
                                           self.text_colormap_value.GetStringSelection())
        self.parent.filelist.SetStringItem(self.itemInfo['id'], self.config.textlistColNames['mask'], 
                                           num2str(self.text_mask_value.GetValue()))
        self.parent.filelist.SetStringItem(self.itemInfo['id'], self.config.textlistColNames['alpha'], 
                                           num2str(self.text_transparency_value.GetValue()))
        self.parent.filelist.SetStringItem(self.itemInfo['id'], self.config.textlistColNames['label'], 
                                           self.text_label_value.GetValue())
        
        # update ion information        
        self.itemInfo['charge'] = self.text_charge_value.GetValue()
        self.itemInfo['colormap'] = self.text_colormap_value.GetStringSelection()
        self.itemInfo['mask'] = self.text_mask_value.GetValue()
        self.itemInfo['alpha'] = self.text_transparency_value.GetValue()
        self.itemInfo['label'] = self.text_label_value.GetValue()
        self.itemInfo['min_threshold'] = self.text_min_threshold_value.GetValue()
        self.itemInfo['max_threshold'] = self.text_max_threshold_value.GetValue()
        
        # update ion value
                
        self.OnAssignColor(evt=None)
        self.parent.onUpdateDocument(itemInfo=self.itemInfo, evt=None)
        
        if evt != None:
            evt.Skip() 
         
    def onSetupParameters(self, evt):
        self.importEvent = True
        self.text_select_value.SetValue(self.itemInfo['select'])
        self.text_filename_value.SetValue(self.itemInfo['document'])
        
        self.text_charge_value.SetValue(str(self.itemInfo['charge']))
        self.text_label_value.SetValue(self.itemInfo['label'])
        self.text_colormap_value.SetStringSelection(self.itemInfo['colormap'])
        self.text_mask_value.SetValue(self.itemInfo['mask'])
        self.text_transparency_value.SetValue(self.itemInfo['alpha'])
        self.text_color_value.SetBackgroundColour(self.itemInfo['color'])
        self.text_min_threshold_value.SetValue(self.itemInfo['min_threshold'])
        self.text_max_threshold_value.SetValue(self.itemInfo['max_threshold'])
    
            
        self.enableDisableBoxes(evt=None)
        self.importEvent = False
        
    def onUpdateGUI(self, itemInfo):
        """
        @param itemInfo (dict): updating GUI with new item information
        """
        self.itemInfo = itemInfo
        self.SetTitle(self.itemInfo['document'])
        
        # check values
        if self.itemInfo['mask'] in ['', None, 'None']:
            self.itemInfo['mask'] = 1

        if self.itemInfo['alpha'] in ['', None, 'None']:
            self.itemInfo['alpha'] = 1
            
        if self.itemInfo['colormap'] in ['', None, 'None']:
            self.itemInfo['colormap'] = self.config.currentCmap
            
        if self.itemInfo['color'][0] == -1:
              self.itemInfo['color'] = (1, 1, 1, 255)
              
        if self.itemInfo['charge'] in ['', None, 'None']:
            self.itemInfo['charge'] = ""
              
        # setup values
        self.onSetupParameters(evt=None)
        
        self.SetFocus()
            
    def enableDisableBoxes(self, evt):
        
        enableList, disableList = [], []
            
        for item in enableList:
            item.Enable()
        for item in disableList:
            item.Disable()
        
        if evt != None:
            evt.Skip() 

    def OnAssignColor(self, evt):
        if evt:
            color = self.parent.OnAssignColor(evt=None, 
                                              itemID=self.itemInfo['id'], 
                                              give_value=True)
                 
            self.text_color_value.SetBackgroundColour(color)
        else:
            color = self.text_color_value.GetBackgroundColour()
            self.parent.filelist.SetItemBackgroundColour(self.itemInfo['id'], color)
              
    def onRestrictCmaps(self, evt):
        """
        The cmap list will be restricted to more limited selection
        """
        currentCmap = self.text_colormap_value.GetStringSelection()
        narrowList = self.config.narrowCmapList
        narrowList.append(currentCmap)
        
        # remove duplicates
        narrowList = sorted(list(set(narrowList)))
         
        if self.text_restrictColormap_value.GetValue():
            self.text_colormap_value.Clear()
            for item in narrowList:
                self.text_colormap_value.Append(item)
            self.text_colormap_value.SetStringSelection(currentCmap)
        else:
            self.text_colormap_value.Clear()
            for item in self.config.cmaps2:
                self.text_colormap_value.Append(item)
            self.text_colormap_value.SetStringSelection(currentCmap)
      
class panelExportSettings(wx.MiniFrame):
    
    def __init__(self, parent, presenter, config, icons, **kwargs):
        wx.MiniFrame.__init__(self, parent,-1, 'Import/Export parameters', size=(-1, -1), 
                              style= (wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BOX | 
                                      wx.MAXIMIZE_BOX | wx.CLOSE_BOX))
        
        self.parent = parent
        self.presenter = presenter
        self.config = config
        self.icons = icons
        self.help = help()
        
        self.importEvent = False
        self.windowSizes = {'Peaklist':(250, 110), 'Image':(250,150), 
                            'Files':(310,140)}
      
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
        if keyCode == wx.WXK_ESCAPE: # key = esc
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
        
        self.mainSizer.Add(self.mainBook, 1, wx.EXPAND |wx.ALL, 2)
        
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
        grid = wx.GridBagSizer(2,2)
        n = 0
        grid.Add(useInternal_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.peaklist_useInternalWindow_check, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        n = n +1
        grid.Add(windowSize_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.peaklist_windowSize_value, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
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
        grid = wx.GridBagSizer(2,2)
        n = 0
        grid.Add(fileFormat_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.image_fileFormat_choice, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        n = n + 1
        grid.Add(resolution_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.image_resolution, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        n = n + 1
        grid.Add(transparency_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.image_transparency_check, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        n = n + 1
        grid.Add(resize_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.image_resize_check, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
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
        self.file_default_name_choice = wx.Choice(panel, -1, choices=self.config._plotSettings.keys(),
                                                 size=(-1, -1))
        self.file_default_name_choice.SetSelection(0)
        self.file_default_name_choice.Bind(wx.EVT_CHOICE, self.onSetupPlotName)
        
        self.file_default_name = wx.TextCtrl(panel, -1, "", size=(210, -1))
        self.file_default_name.SetValue(self.config._plotSettings[self.file_default_name_choice.GetStringSelection()]['default_name'])
        self.file_default_name.Bind(wx.EVT_TEXT, self.onApply)

        # add to grid
        grid = wx.GridBagSizer(2,2)
        n = 0
        grid.Add(delimiter_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.file_delimiter_choice, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        n = n + 1
        grid.Add(default_name_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.file_default_name_choice, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        n = n + 1
        grid.Add(self.file_default_name, (n,1), wx.GBSpan(1,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT|wx.EXPAND)
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
        wx.MiniFrame.__init__(self, parent,-1, 'HTML viewer', size=(-1, -1), 
                              style= (wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BOX | 
                                      wx.MAXIMIZE_BOX | wx.CLOSE_BOX))
        
        self.parent = parent
        self.config = config

        self.label_header = wx.html.HtmlWindow(self, style=wx.TE_READONLY |
                                               wx.TE_MULTILINE | wx.html.HW_SCROLLBAR_AUTO | wx.BORDER_NONE| wx.html.HTML_URL_IMAGE)
        
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
        
        if 'window_size' in kwargs:
            self.SetSize(kwargs['window_size'])
            
        self.Show(True)
        self.CentreOnParent()
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
        wx.MiniFrame.__init__(self, parent,-1, 'UniDec peak width tool...', size=(600, 500), 
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
        peak_grid.Add(unidec_peakShape_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        peak_grid.Add(self.unidec_peakFcn_choice, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        peak_grid.Add(unidec_peakWidth_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        peak_grid.Add(self.unidec_fit_peakWidth_value, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        peak_grid.Add(unidec_error_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        peak_grid.Add(self.unidec_error, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        peak_grid.Add(unidec_resolution_label, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        peak_grid.Add(self.unidec_resolution, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL)
        n = n + 1
        peak_grid.Add(self.fitBtn, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL)
   
        # pack elements
        grid = wx.GridBagSizer(5, 5)
        grid.Add(self.plotMS, (0,0), wx.GBSpan(3, 2))
        grid.Add(peak_grid, (0,3), wx.GBSpan(1, 2))
        grid.Add(self.okBtn, (3,3), wx.GBSpan(1,1))
        grid.Add(self.cancelBtn, (3,4), wx.GBSpan(1,1))

        mainSizer.Add(grid, 0, wx.ALIGN_CENTER|wx.ALL, 10)
        
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
        plt_kwargs = self.presenter._buildPlotParameters(plotType='1D')
        
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
        plt_kwargs = self.presenter._buildPlotParameters(plotType='1D')

            
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
        wx.Dialog.__init__(self, parent,-1, 'New version of ORIGAMI is available!', size=(-1, -1), 
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
                                               size=(500,400))
        self.label_header.SetPage(self.message)
                  
        self.goToDownload = wx.Button(panel, ID_helpNewVersion, "Download Now", size=(-1, 22))
        self.cancelBtn = wx.Button(panel, -1, "Cancel", size=(-1, 22))

        btn_grid = wx.GridBagSizer(1, 1)
        btn_grid.Add(self.goToDownload, (0,1), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT)
        btn_grid.Add(self.cancelBtn, (0,2), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT)
        
        horizontal_line_1 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_2 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        
        # pack elements
        grid = wx.GridBagSizer(5, 5)
        grid.Add(image, (0,0), wx.GBSpan(1,3), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(horizontal_line_1, (1,0), wx.GBSpan(1,3), flag=wx.EXPAND)
        grid.Add(self.label_header, (2,0), wx.GBSpan(2,3), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(horizontal_line_2, (4,0), wx.GBSpan(1,3), flag=wx.EXPAND)
        grid.Add(btn_grid, (5,1), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT)

        mainSizer.Add(grid, 0, wx.ALIGN_CENTER|wx.ALL, 10)
        
        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)

        return panel

class panelNotifyOpenDocuments(wx.Dialog):
    def __init__(self, parent, presenter, message, **kwargs):
        wx.Dialog.__init__(self, parent,-1, 'Documents are still open...!', size=(-1, -1), 
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
    
    def makeGUI(self):
               
        # make panel
        panel = self.makePanel()
        
        # pack element
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(panel, 0, wx.EXPAND, 0)
        
        # bind
        self.saveAllBtn.Bind(wx.EVT_BUTTON, self.presenter.onSaveDocument, id=ID_saveAllDocuments)
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
        grid.Add(self.input_label, (0,0), wx.GBSpan(2,3), flag=wx.ALIGN_RIGHT|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        
        grid.Add(self.saveAllBtn, (2,1), wx.GBSpan(1,1))
        grid.Add(self.continueBtn, (2,2), wx.GBSpan(1,1))
        grid.Add(self.cancelBtn, (2,3), wx.GBSpan(1,1))

        mainSizer.Add(grid, 0, wx.ALIGN_CENTER|wx.ALL, 10)
        
        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)

        return panel

class panelCustomisePlot(wx.Dialog):
    def __init__(self, parent, presenter, config, **kwargs):
        wx.Dialog.__init__(self, parent,-1, 'Customise plot...', size=(-1, -1), 
                              style=wx.DEFAULT_FRAME_STYLE & ~ 
                              (wx.RESIZE_BORDER | wx.RESIZE_BOX | wx.MAXIMIZE_BOX))

        self.parent = parent
        self.presenter = presenter
        self.config = config
        
        self.plot = kwargs['plot']
        self.kwargs = kwargs
        self.loading = True
        
        self.makeGUI()
        self.CentreOnParent()
        self.onPopulatePanel()
        self.loading = False
        
        self.Bind(wx.EVT_CHAR_HOOK, self.OnKey)

    def OnKey(self, evt):
        keyCode = evt.GetKeyCode()
        if keyCode == wx.WXK_ESCAPE: # key = esc
            self.onClose(evt=None)
            
        if evt != None:
            evt.Skip()
        
    def onClose(self, evt):
        """Destroy this frame."""
        
        self.Destroy()
    # ----
    
    def onOK(self, evt):
        
        self.EndModal(wx.OK)
        
    def makeGUI(self):
        
        # make panel
        panel = self.makePanel()
        
        # pack element
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(panel, 0, wx.EXPAND, 0)
        
        # bind
        self.resetBtn.Bind(wx.EVT_BUTTON, self.onReset)
        
        self.saveImageBtn.Bind(wx.EVT_BUTTON, self.saveImage)
        self.cancelBtn.Bind(wx.EVT_BUTTON, self.onClose)
        
        # fit layout
        self.mainSizer.Fit(self)
        self.SetSizer(self.mainSizer)
        
    def makePanel(self):
        
        TEXT_SIZE = 100
        TEXT_SIZE_SMALL = TEXT_SIZE / 2
        
        panel = wx.Panel(self, -1)
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        
        min_label = wx.StaticText(panel, -1, "Min:")
        max_label = wx.StaticText(panel, -1, "Max:")
        major_tickFreq_label = wx.StaticText(panel, -1, "Major tick \nfrequency:")
        minor_tickFreq_label = wx.StaticText(panel, -1, "Minor tick \nfrequency:")
        xaxis_label = wx.StaticText(panel, -1, "X-axis:")
        yaxis_label = wx.StaticText(panel, -1, "Y-axis:")
        
        self.xaxis_min_value = wx.TextCtrl(panel, -1, "", size=(TEXT_SIZE, -1), validator=validator('float'))
        self.xaxis_max_value = wx.TextCtrl(panel, -1, "", size=(TEXT_SIZE, -1), validator=validator('float'))
        self.xaxis_minor_tickreq_value = wx.TextCtrl(panel, -1, "", size=(TEXT_SIZE, -1), validator=validator('float'))
        self.xaxis_major_tickreq_value = wx.TextCtrl(panel, -1, "", size=(TEXT_SIZE, -1), validator=validator('float'))
        
        self.yaxis_min_value = wx.TextCtrl(panel, -1, "", size=(TEXT_SIZE, -1), validator=validator('float'))
        self.yaxis_max_value = wx.TextCtrl(panel, -1, "", size=(TEXT_SIZE, -1), validator=validator('float'))
        self.yaxis_major_tickreq_value = wx.TextCtrl(panel, -1, "", size=(TEXT_SIZE, -1), validator=validator('float'))
        self.yaxis_minor_tickreq_value = wx.TextCtrl(panel, -1, "", size=(TEXT_SIZE, -1), validator=validator('float'))
        self.override_defaults = makeCheckbox(panel, u"Override extents")
        
        self.applyBtn = wx.Button(panel, wx.ID_ANY, "Apply scales", size=(-1, 22))
        self.applyBtn.Bind(wx.EVT_BUTTON, self.onApply_scales)
        
        scales_grid = wx.GridBagSizer(2, 2)
        y = 0
        scales_grid.Add(min_label, (y,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
        scales_grid.Add(max_label, (y,2), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
        scales_grid.Add(minor_tickFreq_label, (y,3), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
        scales_grid.Add(major_tickFreq_label, (y,4), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
        y = y+1
        scales_grid.Add(xaxis_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        scales_grid.Add(self.xaxis_min_value, (y,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        scales_grid.Add(self.xaxis_max_value, (y,2), wx.GBSpan(1,1), flag=wx.EXPAND)
        scales_grid.Add(self.xaxis_minor_tickreq_value , (y,3), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        scales_grid.Add(self.xaxis_major_tickreq_value, (y,4), wx.GBSpan(1,1), flag=wx.EXPAND)
        y = y+1
        scales_grid.Add(yaxis_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        scales_grid.Add(self.yaxis_min_value, (y,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        scales_grid.Add(self.yaxis_max_value, (y,2), wx.GBSpan(1,1), flag=wx.EXPAND)
        scales_grid.Add(self.yaxis_minor_tickreq_value , (y,3), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        scales_grid.Add(self.yaxis_major_tickreq_value, (y,4), wx.GBSpan(1,1), flag=wx.EXPAND)
        y = y+1
        scales_grid.Add(self.override_defaults, (y,0), wx.GBSpan(1,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
        scales_grid.Add(self.applyBtn, (y,4), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)

        
        lineWidth_label = wx.StaticText(panel, -1, "Line width:")
        self.line_width_value = wx.SpinCtrlDouble(panel, -1, value="", min=1, max=10, initial=0, 
                                                  inc=1, size=(TEXT_SIZE, -1))
        self.line_width_value.Bind(wx.EVT_TEXT, self.onApply_plotSettings)     
        
        lineStyle_label = wx.StaticText(panel, -1, "Line style:")
        self.line_style_value= wx.Choice(panel, -1, choices=self.config.lineStylesList,
                                                  size=(TEXT_SIZE, -1))
        self.line_style_value.Bind(wx.EVT_CHOICE, self.onApply_plotSettings)
        
        shade_alpha_label = wx.StaticText(panel, -1, "Shade transparency:")
        self.shade_alpha_value = wx.SpinCtrlDouble(panel, -1, value="", min=0, max=1, initial=0.25, 
                                                  inc=0.25, size=(TEXT_SIZE, -1))
        self.shade_alpha_value.Bind(wx.EVT_TEXT, self.onApply_plotSettings)     
        
        line_grid = wx.GridBagSizer(2, 2)
        y = 0
        line_grid.Add(lineWidth_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        line_grid.Add(self.line_width_value, (y,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        line_grid.Add(lineStyle_label, (y,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        line_grid.Add(self.line_style_value, (y,3), wx.GBSpan(1,1), flag=wx.EXPAND)
        y = y+1
        line_grid.Add(shade_alpha_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        line_grid.Add(self.shade_alpha_value, (y,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        
        legend_fontSize_label = wx.StaticText(panel, -1, "Legend font size:")
        self.legend_fontSize_value= wx.Choice(panel, -1, 
                                   choices=self.config.legendFontChoice,
                                    size=(-1, -1))
        self.legend_fontSize_value.Bind(wx.EVT_CHOICE, self.onApply_legendSettings)
        
        legend_patch_alpha_label = wx.StaticText(panel, -1, "Patch transparency:")
        self.legend_patch_alpha_value = wx.SpinCtrlDouble(panel, -1, value="", min=0, max=1, initial=0.25, 
                                                  inc=0.25, size=(TEXT_SIZE, -1))
        self.legend_patch_alpha_value.Bind(wx.EVT_TEXT, self.onApply_legendSettings)     
        
        self.legend_frame_check = makeCheckbox(panel, u"Frame")
        self.legend_frame_check.Bind(wx.EVT_CHECKBOX, self.onApply_legendSettings)
        
        legend_grid = wx.GridBagSizer(2, 2)
        y = 0
        legend_grid.Add(legend_fontSize_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        legend_grid.Add(self.legend_fontSize_value, (y,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        legend_grid.Add(legend_patch_alpha_label, (y,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        legend_grid.Add(self.legend_patch_alpha_value, (y,3), wx.GBSpan(1,1), flag=wx.EXPAND)
        legend_grid.Add(self.legend_frame_check, (y,4), wx.GBSpan(1,1), flag=wx.EXPAND)
        
        colormap_label = wx.StaticText(panel, -1, "Colormap:")
        self.colormap_value= wx.Choice(panel, -1, choices=self.config.cmaps2,
                                       size=(-1, -1), name="color")
        self.colormap_value.Bind(wx.EVT_CHOICE, self.onApply_colormap)
        
        colormap_min_label = wx.StaticText(panel, -1, "Min:")
        self.cmap_min_value = wx.SpinCtrlDouble(panel, -1, value="", min=0, max=100, initial=0, 
                                                  inc=10, size=(TEXT_SIZE_SMALL, -1))
        self.cmap_min_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_colormap)
        
        colormap_mid_label = wx.StaticText(panel, -1, "Mid:")
        self.cmap_mid_value = wx.SpinCtrlDouble(panel, -1, value="", min=0, max=100, initial=0, 
                                                  inc=10, size=(TEXT_SIZE_SMALL, -1))
        self.cmap_mid_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_colormap)    
        
        colormap_max_label = wx.StaticText(panel, -1, "Max:")
        self.cmap_max_value = wx.SpinCtrlDouble(panel, -1, value="", min=0, max=100, initial=0, 
                                                  inc=10, size=(TEXT_SIZE_SMALL, -1))
        self.cmap_max_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_colormap)    
        
        colormap_grid = wx.GridBagSizer(2, 2)
        y = 0
        colormap_grid.Add(colormap_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        colormap_grid.Add(self.colormap_value, (y,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        colormap_grid.Add(colormap_min_label, (y,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        colormap_grid.Add(self.cmap_min_value, (y,3), wx.GBSpan(1,1), flag=wx.EXPAND)
        colormap_grid.Add(colormap_mid_label, (y,4), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        colormap_grid.Add(self.cmap_mid_value, (y,5), wx.GBSpan(1,1), flag=wx.EXPAND)
        colormap_grid.Add(colormap_max_label, (y,6), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        colormap_grid.Add(self.cmap_max_value, (y,7), wx.GBSpan(1,1), flag=wx.EXPAND)
        
        spines_label = wx.StaticText(panel, -1, "Line:")
        self.leftSpines_check = makeCheckbox(panel, u"Left")
        self.leftSpines_check.Bind(wx.EVT_CHECKBOX, self.onApply_frame)
        
        self.rightSpines_check = makeCheckbox(panel, u"Right")
        self.rightSpines_check.Bind(wx.EVT_CHECKBOX, self.onApply_frame)
        
        self.topSpines_check = makeCheckbox(panel, u"Top")
        self.topSpines_check.SetValue(self.config.spines_top_1D)
        self.topSpines_check.Bind(wx.EVT_CHECKBOX, self.onApply_frame)
        
        self.bottomSpines_check = makeCheckbox(panel, u"Bottom")
        self.bottomSpines_check.Bind(wx.EVT_CHECKBOX, self.onApply_frame)
        
        ticks_label = wx.StaticText(panel, -1, "Ticks:")
        self.leftTicks_check = makeCheckbox(panel, u"Left")
        self.leftTicks_check.Bind(wx.EVT_CHECKBOX, self.onApply_frame)
        
        self.rightTicks_check = makeCheckbox(panel, u"Right")
        self.rightTicks_check.Bind(wx.EVT_CHECKBOX, self.onApply_frame)
        
        self.topTicks_check = makeCheckbox(panel, u"Top")
        self.topTicks_check.Bind(wx.EVT_CHECKBOX, self.onApply_frame)
        
        self.bottomTicks_check = makeCheckbox(panel, u"Bottom")
        self.bottomTicks_check.Bind(wx.EVT_CHECKBOX, self.onApply_frame)
        
        tickLabels_label = wx.StaticText(panel, -1, "Tick labels:")
        self.leftTickLabels_check = makeCheckbox(panel, u"Left")
        self.leftTickLabels_check.Bind(wx.EVT_CHECKBOX, self.onApply_frame)
        
        self.rightTickLabels_check = makeCheckbox(panel, u"Right")
        self.rightTickLabels_check.Bind(wx.EVT_CHECKBOX, self.onApply_frame)
        
        self.topTickLabels_check = makeCheckbox(panel, u"Top")
        self.topTickLabels_check.Bind(wx.EVT_CHECKBOX, self.onApply_frame)
        
        self.bottomTickLabels_check = makeCheckbox(panel, u"Bottom")
        self.bottomTickLabels_check.Bind(wx.EVT_CHECKBOX, self.onApply_frame)
        
        frame_lineWidth_label = wx.StaticText(panel, -1, "Frame width:")
        self.frame_width_value = wx.SpinCtrlDouble(panel, -1, value="1", min=1, max=10, initial=1, 
                                                   inc=1, size=(TEXT_SIZE, -1))
        self.frame_width_value.Bind(wx.EVT_TEXT, self.onApply_frame)     
        
        # axes parameters
        axis_grid = wx.GridBagSizer(2, 2)
        y = 0
        axis_grid.Add(spines_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        axis_grid.Add(self.leftSpines_check, (y,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        axis_grid.Add(self.rightSpines_check, (y,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        axis_grid.Add(self.topSpines_check, (y,3), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        axis_grid.Add(self.bottomSpines_check, (y,4), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        y = y+1
        axis_grid.Add(ticks_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        axis_grid.Add(self.leftTicks_check, (y,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        axis_grid.Add(self.rightTicks_check, (y,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        axis_grid.Add(self.topTicks_check, (y,3), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        axis_grid.Add(self.bottomTicks_check, (y,4), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        y = y+1
        axis_grid.Add(tickLabels_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        axis_grid.Add(self.leftTickLabels_check, (y,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        axis_grid.Add(self.rightTickLabels_check, (y,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        axis_grid.Add(self.topTickLabels_check, (y,3), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        axis_grid.Add(self.bottomTickLabels_check, (y,4), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        y = y+1
        axis_grid.Add(frame_lineWidth_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        axis_grid.Add(self.frame_width_value, (y,1), wx.GBSpan(1,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        
        
        xaxis_label_label = wx.StaticText(panel, -1, "X axis label:")
        self.xlabel_value = wx.TextCtrl(panel, -1, "", size=(TEXT_SIZE, -1))
        self.xlabel_value.Bind(wx.EVT_TEXT, self.onApply_fonts)
        
        yaxis_label_label = wx.StaticText(panel, -1, "Y axis label:")
        self.ylabel_value = wx.TextCtrl(panel, -1, "", size=(TEXT_SIZE, -1))
        self.ylabel_value.Bind(wx.EVT_TEXT, self.onApply_fonts)
        
        title_label = wx.StaticText(panel, -1, "Title:")
        self.title_value = wx.TextCtrl(panel, -1, "", size=(TEXT_SIZE, -1))
        self.title_value.Bind(wx.EVT_TEXT, self.onApply_fonts)
        
        padding_label = wx.StaticText(panel, -1, "Label pad:")
        self.padding_value = wx.SpinCtrlDouble(panel, -1, 
                                               min=0, max=100, 
                                               inc=5, size=(90, -1))
        self.padding_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_fonts)
        
        titleFontSize_label = wx.StaticText(panel, -1, "Title font size:")
        self.titleFontSize_value = wx.SpinCtrlDouble(panel, -1, 
                                               min=0, max=32, 
                                               inc=2, size=(90, -1))
        self.titleFontSize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_fonts)

        self.titleFontWeight_check = makeCheckbox(panel, u"Bold")
        self.titleFontWeight_check.Bind(wx.EVT_CHECKBOX, self.onApply_fonts)
        
        labelFontSize_label = wx.StaticText(panel, -1, "Label font size:")
        self.labelFontSize_value = wx.SpinCtrlDouble(panel, -1, 
                                               min=0, max=32, 
                                               inc=2, size=(90, -1))
        self.labelFontSize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_fonts)

        self.labelFontWeight_check = makeCheckbox(panel, u"Bold")
        self.labelFontWeight_check.Bind(wx.EVT_CHECKBOX, self.onApply_fonts)
        
        tickFontSize_label = wx.StaticText(panel, -1, "Tick font size:")
        self.tickFontSize_value = wx.SpinCtrlDouble(panel, -1, 
                                               min=0, max=32, 
                                               inc=2, size=(90, -1))
        self.tickFontSize_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_fonts)
        
        self.tickFontWeight_check = makeCheckbox(panel, u"Bold")
        self.tickFontWeight_check.Bind(wx.EVT_CHECKBOX, self.onApply_fonts)
        self.tickFontWeight_check.Disable()
        
        # font parameters
        font_grid = wx.GridBagSizer(2, 2)
        y = 0
        font_grid.Add(title_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        font_grid.Add(self.title_value, (y,1), wx.GBSpan(1,5), flag=wx.EXPAND)
        y = y+1
        font_grid.Add(xaxis_label_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        font_grid.Add(self.xlabel_value, (y,1), wx.GBSpan(1,5), flag=wx.EXPAND)
        y = y+1
        font_grid.Add(yaxis_label_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        font_grid.Add(self.ylabel_value, (y,1), wx.GBSpan(1,5), flag=wx.EXPAND)
        y = y+1
        font_grid.Add(padding_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        font_grid.Add(self.padding_value, (y,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        font_grid.Add(titleFontSize_label, (y,3), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        font_grid.Add(self.titleFontSize_value, (y,4), wx.GBSpan(1,1), flag=wx.EXPAND)
        font_grid.Add(self.titleFontWeight_check, (y,5), wx.GBSpan(1,1), flag=wx.EXPAND)
        y = y+1
        font_grid.Add(labelFontSize_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        font_grid.Add(self.labelFontSize_value, (y,1), wx.GBSpan(1,1), flag=wx.EXPAND)
        font_grid.Add(self.labelFontWeight_check, (y,2), wx.GBSpan(1,1), flag=wx.EXPAND)
        font_grid.Add(tickFontSize_label, (y,3), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        font_grid.Add(self.tickFontSize_value, (y,4), wx.GBSpan(1,1), flag=wx.EXPAND)
        font_grid.Add(self.tickFontWeight_check, (y,5), wx.GBSpan(1,1), flag=wx.EXPAND)
        
        plotSize_label = wx.StaticText(panel, -1, "Plot size (proportion)")
        
        left_label = wx.StaticText(panel, -1, "Left")
        self.left_value = wx.SpinCtrlDouble(panel, -1, value=str(0), 
                                            min=0.0, max=1, initial=0, inc=0.05,
                                            size=(60, -1))
        self.left_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_axes)
        
        bottom_label = wx.StaticText(panel, -1, "Bottom")
        self.bottom_value = wx.SpinCtrlDouble(panel, -1, value=str(0), 
                                                    min=0.0, max=1, initial=0, inc=0.05,
                                                    size=(60, -1))
        self.bottom_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_axes)
        
        width_label = wx.StaticText(panel, -1, "Width")
        self.width_value = wx.SpinCtrlDouble(panel, -1, value=str(0), 
                                                    min=0.0, max=1, initial=0, inc=0.05,
                                                    size=(60, -1))
        self.width_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_axes)
        
        height_label = wx.StaticText(panel, -1, "Height")
        self.height_value = wx.SpinCtrlDouble(panel, -1, value=str(0), 
                                                    min=0.0, max=1, initial=0, inc=0.05,
                                                    size=(60, -1))
        self.height_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_axes)

        plotSize_window_inch_label= wx.StaticText(panel, -1, "Plot size (inch)")
        width_window_inch_label = wx.StaticText(panel, -1, "Width")
        self.width_window_inch_value = wx.SpinCtrlDouble(panel, -1, value=str(0), 
                                                    min=0.0, max=20, initial=0, inc=.5,
                                                    size=(60, -1))
        self.width_window_inch_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_size)
        
        height_window_inch_label = wx.StaticText(panel, -1, "Height")
        self.height_window_inch_value = wx.SpinCtrlDouble(panel, -1, value=str(0), 
                                                          min=0.0, max=20, initial=0, inc=.5,
                                                          size=(60, -1))
        self.height_window_inch_value.Bind(wx.EVT_SPINCTRLDOUBLE, self.onApply_size)
        
        # add elements to grids
        axes_grid = wx.GridBagSizer(2, 2)
        y = 0
        axes_grid.Add(left_label, (y,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        axes_grid.Add(bottom_label, (y,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        axes_grid.Add(width_label, (y,3), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        axes_grid.Add(height_label, (y,4), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        y = y+1
        axes_grid.Add(plotSize_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        axes_grid.Add(self.left_value, (y,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        axes_grid.Add(self.bottom_value, (y,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        axes_grid.Add(self.width_value, (y,3), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        axes_grid.Add(self.height_value, (y,4), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        y = y+1
        axes_grid.Add(width_window_inch_label, (y,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        axes_grid.Add(height_window_inch_label, (y,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        y = y+1
        axes_grid.Add(plotSize_window_inch_label, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        axes_grid.Add(self.width_window_inch_value, (y,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        axes_grid.Add(self.height_window_inch_value, (y,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER)
        
        self.lock_plot = makeCheckbox(panel, u"Lock plot")
        self.lock_plot.SetValue(self.plot.lock_plot_from_updating)
        self.lock_plot.Bind(wx.EVT_CHECKBOX, self.onLockPlot)
        
        horizontal_line_1 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_2 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_3 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_4 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_5 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_6 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_7 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL) 
        self.resetBtn = wx.Button(panel, wx.ID_ANY, "Reset", size=(-1, 22))
        self.cancelBtn = wx.Button(panel, -1, "Cancel", size=(-1, 22))
        self.saveImageBtn = wx.Button(panel, wx.ID_ANY, "Save image", size=(-1, 22))

        # pack elements
        grid = wx.GridBagSizer(5, 5)
        n = 0 
        grid.Add(scales_grid, (n,0), wx.GBSpan(1,4), flag=wx.EXPAND)
        n = n + 1
        grid.Add(horizontal_line_1, (n,0), wx.GBSpan(1,4), flag=wx.EXPAND)
        n = n + 1 
        grid.Add(line_grid, (n,0), wx.GBSpan(1,4), flag=wx.EXPAND)
        n = n + 1
        grid.Add(horizontal_line_2, (n,0), wx.GBSpan(1,4), flag=wx.EXPAND)
        n = n + 1
        grid.Add(legend_grid, (n,0), wx.GBSpan(1,4), flag=wx.EXPAND)
        n = n + 1
        grid.Add(horizontal_line_7, (n,0), wx.GBSpan(1,4), flag=wx.EXPAND)
        n = n + 1
        grid.Add(colormap_grid, (n,0), wx.GBSpan(1,4), flag=wx.EXPAND)
        n = n + 1
        grid.Add(horizontal_line_3, (n,0), wx.GBSpan(1,4), flag=wx.EXPAND)
        n = n + 1
        grid.Add(axis_grid, (n,0), wx.GBSpan(1,4), flag=wx.EXPAND)
        n = n + 1 
        grid.Add(horizontal_line_4, (n,0), wx.GBSpan(1,4), flag=wx.EXPAND)
        n = n + 1
        grid.Add(font_grid, (n,0), wx.GBSpan(1,4), flag=wx.EXPAND)
        n = n + 1
        grid.Add(horizontal_line_5, (n,0), wx.GBSpan(1,4), flag=wx.EXPAND)
        n = n + 1
        grid.Add(axes_grid, (n,0), wx.GBSpan(1,4), flag=wx.EXPAND)
        n = n + 1 
        grid.Add(horizontal_line_6, (n,0), wx.GBSpan(1,4), flag=wx.EXPAND)
        n = n + 1
        grid.Add(self.resetBtn, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(self.saveImageBtn, (n,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(self.cancelBtn, (n,2), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_HORIZONTAL)
        
        n = n + 1
        grid.Add(self.lock_plot, (n,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_HORIZONTAL)
        
        mainSizer.Add(grid, 0, wx.ALIGN_CENTER|wx.ALL, 10)
        
        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizer(mainSizer)

        return panel

    def onPopulatePanel(self):
        # populate all together
        self.xaxis_min_value.SetValue(str(self.kwargs['xmin']))
        self.xaxis_max_value.SetValue(str(self.kwargs['xmax']))
        self.yaxis_min_value.SetValue(str(self.kwargs['ymin']))
        self.yaxis_max_value.SetValue(str(self.kwargs['ymax']))
        self.line_width_value.SetValue(self.plot.plot_parameters.get('line_width', 1.0))
        try:
            self.line_style_value.SetStringSelection(self.config.lineStylesDict[self.plot.plot_parameters.get('line_style', "-")])
        except:
            self.line_style_value.SetStringSelection(self.plot.plot_parameters.get('line_style', "-"))
        
        self.leftSpines_check.SetValue(self.plot.plot_parameters['spines_left'])
        self.rightSpines_check.SetValue(self.plot.plot_parameters['spines_right'])
        self.topSpines_check.SetValue(self.plot.plot_parameters['spines_top'])
        self.bottomSpines_check.SetValue(self.plot.plot_parameters['spines_bottom'])
        self.leftTicks_check.SetValue(self.plot.plot_parameters['ticks_left'])
        self.rightTicks_check.SetValue(self.plot.plot_parameters['ticks_right'])
        self.topTicks_check.SetValue(self.plot.plot_parameters['ticks_top'])
        self.bottomTicks_check.SetValue(self.plot.plot_parameters['ticks_bottom'])
        self.leftTickLabels_check.SetValue(self.plot.plot_parameters['tickLabels_left'])
        self.rightTickLabels_check.SetValue(self.plot.plot_parameters['tickLabels_right'])
        self.topTickLabels_check.SetValue(self.plot.plot_parameters['tickLabels_top'])
        self.bottomTickLabels_check.SetValue(self.plot.plot_parameters['tickLabels_bottom'])
        
        self.frame_width_value.SetValue(self.plot.plot_parameters.get('frame_width', 1.0))
        

        self.xlabel_value.SetValue(self.kwargs['xlabel'])
        self.ylabel_value.SetValue(self.kwargs['ylabel'])
        self.title_value.SetValue(self.kwargs['title'])
        
        self.padding_value.SetValue(self.plot.plot_parameters['label_pad'])
        self.titleFontSize_value.SetValue(self.plot.plot_parameters['title_size'])
        self.labelFontSize_value.SetValue(self.plot.plot_parameters['label_size'])
        self.tickFontSize_value.SetValue(self.plot.plot_parameters['tick_size'])

        if not isinstance(self.plot.plot_parameters['title_weight'], bool):
            if self.plot.plot_parameters['title_weight'] == 'normal': 
                self.plot.plot_parameters['title_weight'] = False
            else:
                self.plot.plot_parameters['title_weight'] = True
                
        if not isinstance(self.plot.plot_parameters['label_weight'], bool):
            if self.plot.plot_parameters['label_weight'] == 'normal': 
                self.plot.plot_parameters['label_weight'] = False
            else:
                self.plot.plot_parameters['label_weight'] = True
                
        if not isinstance(self.plot.plot_parameters['tick_weight'], bool):
            if self.plot.plot_parameters['tick_weight'] == 'normal': 
                self.plot.plot_parameters['tick_weight'] = False
            else:
                self.plot.plot_parameters['tick_weight'] = True
            
        self.titleFontWeight_check.SetValue(self.plot.plot_parameters['title_weight'])
        self.labelFontWeight_check.SetValue(self.plot.plot_parameters['label_weight'])
        self.tickFontWeight_check.SetValue(self.plot.plot_parameters['tick_weight'])

        self.width_window_inch_value.SetValue(self.kwargs['plot_size'][0])
        self.height_window_inch_value.SetValue(self.kwargs['plot_size'][1])

        self.left_value.SetValue(self.kwargs['plot_axes'][0])
        self.bottom_value.SetValue(self.kwargs['plot_axes'][1])
        self.width_value.SetValue(self.kwargs['plot_axes'][2])
        self.height_value.SetValue(self.kwargs['plot_axes'][3])
        
        self.shade_alpha_value.SetValue(self.plot.plot_parameters.get("shade_under_transparency", 0.25))
        
        self.legend_patch_alpha_value.SetValue(self.plot.plot_parameters.get("legend_patch_transparency", 0.25))
        self.legend_fontSize_value.SetStringSelection(self.plot.plot_parameters.get("legend_font_size", "large"))
        self.legend_frame_check.SetValue(self.plot.plot_parameters.get('legend_frame_on', False))
        
        colormap = self.plot.plot_parameters.get('colormap', self.config.currentCmap)
        if colormap not in self.config.cmaps2: colormap = self.config.currentCmap
        self.colormap_value.SetStringSelection(colormap)
        self.cmap_min_value.SetValue(self.plot.plot_parameters.get("colormap_min", 0))
        self.cmap_mid_value.SetValue(self.plot.plot_parameters.get("colormap_mid", 50))
        self.cmap_max_value.SetValue(self.plot.plot_parameters.get("colormap_max", 100))
        
    def onApply_colormap(self, evt):
        colormap = self.colormap_value.GetStringSelection()
        cmap_min = self.cmap_min_value.GetValue()
        cmap_mid = self.cmap_mid_value.GetValue()
        cmap_max = self.cmap_max_value.GetValue()
        
        self.plot.cax.set_cmap(colormap)
        if hasattr(self.plot, "plot_data"):
            if 'zvals' in self.plot.plot_data:
                # normalize
                zvals_max = max(self.plot.plot_data['zvals'])
                cmap_min = (zvals_max*cmap_min)/100.
                cmap_mid = (zvals_max*cmap_mid)/100.
                cmap_max = (zvals_max*cmap_max)/100.
                
                cmap_norm = MidpointNormalize(midpoint=cmap_mid, vmin=cmap_min, vmax=cmap_max)
                self.plot.plot_parameters['colormap_norm'] = cmap_norm
                
                if 'colormap_norm' in self.plot.plot_parameters:
                    self.plot.cax.set_norm(self.plot.plot_parameters['colormap_norm'])
#                     cbar_ticks = [cmap_min, median([cmap_min + cmap_max]), cmap_max]
                    
                    
        self.plot.lock_plot_from_updating = False
        self.plot.plot_2D_colorbar_update( **self.plot.plot_parameters)
        self.plot.lock_plot_from_updating = True
        self.plot.repaint()
        
        # update kwargs
        self.plot.plot_parameters['colormap_min'] = self.cmap_min_value.GetValue()
        self.plot.plot_parameters['colormap_mid'] = self.cmap_mid_value.GetValue()
        self.plot.plot_parameters['colormap_max'] = self.cmap_max_value.GetValue()
        self.plot.plot_parameters['colormap'] = colormap
        
    def onApply_legendSettings(self, evt):
        
        leg = self.plot.plotMS.axes.get_legend()
        leg.set_frame_on(self.legend_frame_check.GetValue())
        
#         print(self.plot.cbar.get_ylim())
#         print(dir(self.plot.cbar))
#         print(dir_extra(dir(self.plot.cbar), "get"))
        try:
            patches = leg.get_patches()
            legend_alpha = self.legend_patch_alpha_value.GetValue()
            for i in range(len(patches)):
                color = patches[i].get_facecolor()
                patches[i].set_alpha(legend_alpha)
                patches[i].set_facecolor(color)
        except: pass
        
        try:
            texts = leg.get_texts()
            text_size = self.legend_fontSize_value.GetStringSelection()
            for i in range(len(texts)):
                texts[i].set_fontsize(text_size)
        except: pass
        
        self.plot.repaint()
        
        self.plot.plot_parameters['legend_font_size'] = self.legend_fontSize_value.GetStringSelection()
        self.plot.plot_parameters['legend_patch_transparency'] = self.legend_patch_alpha_value.GetValue()
        self.plot.plot_parameters['legend_frame_on'] = self.legend_frame_check.GetValue()
        
        
    def onApply_plotSettings(self, evt):
        if self.loading: return
        try:
            line_width = self.line_width_value.GetValue()
            line_style = self.line_style_value.GetStringSelection()
            lines = self.plot.plotMS.get_lines()
            for line in lines:
                line.set_linewidth(line_width)
                line.set_linestyle(line_style)
        except: pass
        
        try:
            shade_value = self.shade_alpha_value.GetValue()
            for i in range(len(self.plot.plotMS.collections)):
                self.plot.plotMS.collections[i].set_alpha(shade_value)
        except: pass
        
        self.plot.repaint()
        
        
        self.plot.plot_parameters['line_width'] = self.line_width_value.GetValue()
        self.plot.plot_parameters['line_style'] = self.line_style_value.GetStringSelection()
        self.plot.plot_parameters['shade_under_transparency'] = self.shade_alpha_value.GetValue()
        
    def onApply_frame(self, evt):
        if self.loading: return
        
        
        self.plot.plotMS.tick_params(axis='both',  
                                     left=self.leftTicks_check.GetValue(), 
                                     right=self.rightTicks_check.GetValue(), 
                                     top=self.topTicks_check.GetValue(), 
                                     bottom=self.bottomTicks_check.GetValue(), 
                                     labelleft=self.leftTickLabels_check.GetValue(), 
                                     labelright=self.rightTickLabels_check.GetValue(), 
                                     labeltop=self.topTickLabels_check.GetValue(), 
                                     labelbottom=self.bottomTickLabels_check.GetValue())
        
        self.plot.plotMS.spines['left'].set_visible(self.leftSpines_check.GetValue())
        self.plot.plotMS.spines['right'].set_visible(self.rightSpines_check.GetValue())
        self.plot.plotMS.spines['top'].set_visible(self.topSpines_check.GetValue())
        self.plot.plotMS.spines['bottom'].set_visible(self.bottomSpines_check.GetValue())
        
        frame_width = self.frame_width_value.GetValue()
        [i.set_linewidth(frame_width) for i in self.plot.plotMS.spines.itervalues()]
        self.plot.repaint()
        
        self.plot.plot_parameters['spines_left'] = self.leftSpines_check.GetValue()
        self.plot.plot_parameters['spines_right'] = self.rightSpines_check.GetValue()
        self.plot.plot_parameters['spines_top'] = self.topSpines_check.GetValue()
        self.plot.plot_parameters['spines_bottom'] = self.bottomSpines_check.GetValue()
        self.plot.plot_parameters['ticks_left'] = self.leftTicks_check.GetValue()
        self.plot.plot_parameters['ticks_right'] = self.rightTicks_check.GetValue()
        self.plot.plot_parameters['ticks_top'] = self.topTicks_check.GetValue()
        self.plot.plot_parameters['ticks_bottom'] = self.bottomTicks_check.GetValue()
        self.plot.plot_parameters['tickLabels_left'] = self.leftTickLabels_check.GetValue()
        self.plot.plot_parameters['tickLabels_right'] = self.rightTickLabels_check.GetValue()
        self.plot.plot_parameters['tickLabels_top'] = self.topTickLabels_check.GetValue()
        self.plot.plot_parameters['tickLabels_bottom'] = self.bottomTickLabels_check.GetValue()
        self.plot.plot_parameters['frame_width'] = frame_width
    
    def onApply_fonts(self, evt):
        if self.loading: return
        
#         leg = self.plot.plotMS.axes.get_legend()
#         leg.set_title("TESTST")
#         leg.set_frame_on(True)
#         leg.set_alpha(0.0)
#         print(dir_extra(dir(leg), "set"))
        
        # convert weights
        if self.titleFontWeight_check.GetValue(): title_weight = "heavy"
        else: title_weight = "normal"
        
        if self.labelFontWeight_check.GetValue(): label_weight = "heavy"
        else: label_weight = "normal"
        
        if self.tickFontWeight_check.GetValue(): tick_weight = "heavy"
        else: tick_weight = "normal"

        # update title
        self.plot.plotMS.set_title(self.title_value.GetValue(),
                                   fontsize=self.titleFontSize_value.GetValue(), 
                                   weight=title_weight)
               
        # update labels
        self.plot.plotMS.set_xlabel(self.xlabel_value.GetValue(), 
                                    labelpad=self.padding_value.GetValue(), 
                                    fontsize=self.labelFontSize_value.GetValue(), 
                                    weight=label_weight)
        self.plot.plotMS.set_ylabel(self.ylabel_value.GetValue(),
                                    labelpad=self.padding_value.GetValue(), 
                                    fontsize=self.labelFontSize_value.GetValue(), 
                                    weight=label_weight)
        
        # Setup font size info
        self.plot.plotMS.tick_params(labelsize=self.tickFontSize_value.GetValue())
        self.plot.repaint()
        
        # update plot kwargs
        self.plot.plot_parameters['label_pad'] = self.padding_value.GetValue()
        self.plot.plot_parameters['label_size'] = self.labelFontSize_value.GetValue()
        self.plot.plot_parameters['label_weight'] = label_weight
        self.plot.plot_parameters['tick_size'] = self.tickFontSize_value.GetValue()
        self.plot.plot_parameters['tick_weight'] = tick_weight
        self.plot.plot_parameters['title_size'] = self.titleFontSize_value.GetValue()
        self.plot.plot_parameters['title_weight'] = title_weight
    
    def onApply_size(self, evt):
        if self.loading: return
        dpi = wx.ScreenDC().GetPPI()
        figuire_size = (int(self.width_window_inch_value.GetValue()*dpi[0]),
                        int(self.height_window_inch_value.GetValue()*dpi[1]))
        self.plot.SetSize(figuire_size)
        self.plot.repaint()
        
        self.plot.plot_parameters['panel_size'] = figuire_size
        
    def onApply_axes(self, evt):
        if self.loading: return
        axes_sizes = [self.left_value.GetValue(),
                      self.bottom_value.GetValue(),
                      self.width_value.GetValue(),
                      self.height_value.GetValue()]
        
        self.plot.plot_update_axes(axes_sizes)
        self.plot.repaint()
        
        self.plot._axes = axes_sizes
        
    def onApply_scales(self, evt):
        
        if self.loading: return
        new_xmin = str2num(self.xaxis_min_value.GetValue())
        new_xmax = str2num(self.xaxis_max_value.GetValue())
        self.plot.plotMS.set_xlim((new_xmin, new_xmax))
        
        new_ymin = str2num(self.yaxis_min_value.GetValue())
        new_ymax = str2num(self.yaxis_max_value.GetValue())
        self.plot.plotMS.set_ylim((new_ymin, new_ymax))
        
        try:
            new_xticks = str2num(self.xaxis_major_tickreq_value.GetValue())
            self.plot.plotMS.xaxis.set_major_locator(ticker.MultipleLocator(new_xticks))
        except: 
            pass
        
        try:
            new_xticks = str2num(self.xaxis_minor_tickreq_value.GetValue())
            self.plot.plotMS.xaxis.set_minor_locator(ticker.MultipleLocator(new_xticks))
        except: 
            pass
        
        try:
            new_yticks = str2num(self.yaxis_major_tickreq_value.GetValue())
            self.plot.plotMS.yaxis.set_major_locator(ticker.MultipleLocator(new_yticks))
        except: 
            pass
        
        try:
            new_yticks = str2num(self.yaxis_minor_tickreq_value.GetValue())
            self.plot.plotMS.yaxis.set_minor_locator(ticker.MultipleLocator(new_yticks))
        except: 
            pass
        
        if self.override_defaults.GetValue():
            extent= [new_xmin, new_ymin, new_xmax, new_ymax]
            self.plot.update_extents(extent)
            self.plot.plot_limits = [extent[0], extent[2], extent[1], extent[3]]
        
        self.plot.repaint()
    
    def onTickFrequency(self, evt):
#         print(dir_extra(dir(self.plot.plotMS.xaxis), keywords="set"))
        try:
            new_xticks = str2num(self.xaxis_major_tickreq_value.GetValue())
            self.plot.plotMS.xaxis.set_major_locator(ticker.MultipleLocator(new_xticks))
        except: 
            pass
        
        try:
            new_xticks = str2num(self.xaxis_minor_tickreq_value.GetValue())
            self.plot.plotMS.xaxis.set_minor_locator(ticker.MultipleLocator(new_xticks))
        except: 
            pass
        
        try:
            new_yticks = str2num(self.yaxis_major_tickreq_value.GetValue())
            self.plot.plotMS.yaxis.set_major_locator(ticker.MultipleLocator(new_yticks))
        except: 
            pass
        
        try:
            new_yticks = str2num(self.yaxis_minor_tickreq_value.GetValue())
            self.plot.plotMS.yaxis.set_minor_locator(ticker.MultipleLocator(new_yticks))
        except: 
            pass
        
        self.plot.repaint()
    
    def onReset(self, evt):
        
        # reset range
        self.plot.plotMS.set_xlim((self.kwargs['xmin'], self.kwargs['xmax']))
        self.plot.plotMS.set_ylim((self.kwargs['ymin'], self.kwargs['ymax']))
        
        # reset tickers
        self.plot.plotMS.xaxis.set_major_locator(self.kwargs['major_xticker'])
        self.plot.plotMS.yaxis.set_major_locator(self.kwargs['major_yticker'])
        
        self.plot.plotMS.xaxis.set_minor_locator(self.kwargs['minor_xticker'])
        self.plot.plotMS.yaxis.set_minor_locator(self.kwargs['minor_yticker'])
        
        self.plot.repaint()        
        self.onPopulatePanel()
    
    def onLockPlot(self, evt):
        if self.lock_plot.GetValue():
            self.plot.lock_plot_from_updating = True
        else:
            self.plot.lock_plot_from_updating = False
          
    def saveImage(self, evt):
        wildcard = "SVG Scalable Vector Graphic (*.svg)|*.svg|" + \
                   "SVGZ Compressed Scalable Vector Graphic (*.svgz)|*.svgz|" + \
                   "PNG Portable Network Graphic (*.png)|*.png|" + \
                   "Enhanced Windows Metafile (*.eps)|*.eps|" + \
                   "JPEG File Interchange Format (*.jpeg)|*.jpeg|" + \
                   "TIFF Tag Image File Format (*.tiff)|*.tiff|" + \
                   "RAW Image File Format (*.raw)|*.raw|" + \
                   "PS PostScript Image File Format (*.ps)|*.ps|" + \
                   "PDF Portable Document Format (*.pdf)|*.pdf"
                   
        wildcard_dict = {'svg':0, 'svgz':1, 'png':2, 'eps':3, 'jpeg':4,
                         'tiff':5, 'raw':6, 'ps':7, 'pdf':8}
                   
        dlg =  wx.FileDialog(self, "Please select a name for the file", 
                             "", "", wildcard=wildcard, style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        dlg.CentreOnParent()
        try: dlg.SetFilterIndex(wildcard_dict[self.config.imageFormat])
        except: pass
        
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
            __, extension = os.path.splitext(filename)
            self.config.imageFormat = extension[1::]
                        
            # Build kwargs
            kwargs = {"transparent":self.config.transparent,
                      "dpi":self.config.dpi, 
                      'format':extension[1::],
                      'compression':"zlib",
                      'resize': None}
            
            self.plot.saveFigure2(path=filename, **kwargs)        

class panelAnnotatePeaks(wx.MiniFrame):
    """
    Simple GUI to view and annotate mass spectra
    """
    
    def __init__(self, parent, documentTree, config, icons, **kwargs):
        wx.MiniFrame.__init__(self, parent,-1, 'Annotation...', size=(-1, -1), 
                              style=wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER)
        
        self.parent = parent
        self.documentTree = documentTree
        self.panelPlot = documentTree.presenter.view.panelPlots
        self.config = config
        self.icons = icons
        self.help = help()
                
        self.kwargs = kwargs
                
        # make gui items
        self.makeGUI()
                      
        self.CentreOnScreen()
        self.Layout()
        self.SetFocus()
        
        self.table_data = []
        
        # bind
        wx.EVT_CLOSE(self, self.onClose)
        self.Bind(wx.EVT_CHAR_HOOK, self.OnKey)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onItemSelected)
        self.onPopulateTable()
        
        # add listener
        pub.subscribe(self.add_annotation, 'mark_annotation')
        
    # ----
    
    def OnKey(self, evt):
        keyCode = evt.GetKeyCode()
        if keyCode == wx.WXK_ESCAPE: # key = esc
            self.onClose(evt=None)
        
        evt.Skip()
        
    def onClose(self, evt):
        """Destroy this frame."""
        # reset state
        self.panelPlot.plot1._on_mark_annotation(state=False)
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
        
        panel = wx.Panel(self, -1, size=(-1,-1))
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        
        self.peaklist = SortedCheckListCtrl(panel, style=wx.LC_REPORT|wx.LC_VRULES, columns=5)
        self.peaklist.InsertColumn(0,u'min', width=75)
        self.peaklist.InsertColumn(1,u'max', width=75)
        self.peaklist.InsertColumn(2,u'intensity', width=75)
        self.peaklist.InsertColumn(3,u'charge', width=50)
        self.peaklist.InsertColumn(4,u'label', width=100)
#         self.peaklist.InsertColumn(5,u'charge', width=100)
#         self.peaklist.InsertColumn(6,u'label', width=100)
        
        # make editor
        min_label = wx.StaticText(panel, -1, u"min:")
        self.min_value = wx.TextCtrl(panel, -1, "")
        self.min_value.Bind(wx.EVT_TEXT, self.onApply)
        
        max_label = wx.StaticText(panel, -1, u"max:")
        self.max_value = wx.TextCtrl(panel, -1, "")
        self.max_value.Bind(wx.EVT_TEXT, self.onApply)
        
        charge_label = wx.StaticText(panel, -1, u"charge:")
        self.charge_value = wx.TextCtrl(panel, -1, "")
        self.charge_value.Bind(wx.EVT_TEXT, self.onApply)
        
        
#         self.preset_preset1 = wx.Button(panel, wx.ID_OK, u"[M+1H]⁺¹", size=(-1, 22))

        label_label = wx.StaticText(panel, -1, u"label:")
        self.label_value = wx.TextCtrl(panel, -1, "", style=wx.TE_RICH2)
        self.label_value.Bind(wx.EVT_TEXT, self.onApply) 
#         
#         color_label = wx.StaticText(panel, -1, u"color:")
#         self.colorBtn = wx.Button(panel, wx.ID_ANY,
#                                   u"", wx.DefaultPosition, 
#                                   wx.Size( 26, 26 ), 0)
#         self.colorBtn.SetBackgroundColour(convertRGB1to255(self.config.markerEdgeColor_3D))
#         self.colorBtn.Bind(wx.EVT_BUTTON, self.onChangeColour)
        
        # make buttons
        self.markTgl = makeToggleBtn(panel, 'Annotating: Off', wx.RED, size=(-1, -1))
        self.markTgl.SetLabel('Annotating: Off')
        self.markTgl.SetForegroundColour(wx.WHITE)
        self.markTgl.SetBackgroundColour(wx.RED)
        
        self.addBtn = wx.Button(panel, wx.ID_OK, "Add annotation", size=(-1, 22))
        self.removeBtn = wx.Button(panel, wx.ID_OK, "Remove", size=(-1, 22))
        self.cancelBtn = wx.Button(panel, wx.ID_OK, "Cancel", size=(-1, 22))

        self.markTgl.Bind(wx.EVT_TOGGLEBUTTON, self.onMarkOnSpectrum)
        self.addBtn.Bind(wx.EVT_BUTTON, self.onAdd)
        self.removeBtn.Bind(wx.EVT_BUTTON, self.onRemove)
        self.cancelBtn.Bind(wx.EVT_BUTTON, self.onClose)
        

        # button grid
        btn_grid = wx.GridBagSizer(5, 5)
        y = 0
        btn_grid.Add(self.markTgl, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
        btn_grid.Add(self.addBtn, (y,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
        btn_grid.Add(self.removeBtn, (y,2), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
        btn_grid.Add(self.cancelBtn, (y,3), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
         

        # pack elements
        grid = wx.GridBagSizer(5, 5)
        y = 0
        grid.Add(min_label, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.min_value, (y,1), wx.GBSpan(1,1), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(max_label, (y,2), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.max_value, (y,3), wx.GBSpan(1,1), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(charge_label, (y,4), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.charge_value, (y,5), wx.GBSpan(1,1), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        y = y+1
        grid.Add(label_label, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(self.label_value, (y,1), wx.GBSpan(1,5), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        y = y+1
        grid.Add(btn_grid, (y,0), wx.GBSpan(1,6), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
         
        mainSizer.Add(grid, 0, wx.EXPAND, 10)
        mainSizer.Add(self.peaklist, 1, wx.EXPAND|wx.ALL, 2)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizerAndFit(mainSizer)

        return panel
    
    def GetListCtrl(self):
        return self.list

    def OnColClick(self, evt):
        evt.Skip()
    
    def onApply(self, evt):
        pass
    
    def onItemSelected(self, evt):
        self.currentItem = evt.m_itemIndex
        
        # populate values
        self.min_value.SetValue(self.peaklist.GetItem(self.currentItem, 0).GetText())
        self.max_value.SetValue(self.peaklist.GetItem(self.currentItem, 1).GetText())
        self.charge_value.SetValue(self.peaklist.GetItem(self.currentItem, 3).GetText())
        self.label_value.SetValue(self.peaklist.GetItem(self.currentItem, 4).GetText())
        
    def onPopulateTable(self):
       
        itemDataMap = {}
        for i, key in enumerate(self.kwargs["annotations"]):
            itemDataMap[i] = tuple([self.kwargs["annotations"][key]['min'],
                                    self.kwargs["annotations"][key]['max'],
                                    self.kwargs["annotations"][key]['intensity'],
                                    self.kwargs["annotations"][key]['charge'],
                                    self.kwargs["annotations"][key]['label']])
            self.peaklist.Append([self.kwargs["annotations"][key]['min'],
                                  self.kwargs["annotations"][key]['max'],
                                  self.kwargs["annotations"][key]['intensity'],
                                  self.kwargs["annotations"][key]['charge'],
                                  self.kwargs["annotations"][key]['label']])
        self.peaklist.itemDataMap = itemDataMap
   
    def string_to_unicode(self, s, return_type="simple"):
        if return_type == "simple":
            unicode_string = u''.join(dict(zip(u"+-0123456789", u"⁺⁻⁰¹²³⁴⁵⁶⁷⁸⁹")).get(c, c) for c in s)
            return unicode_string
        elif return_type == "M+nH":
            if "+" not in s and "-" not in s:
                s = "+{}".format(s)
            unicode_string = u''.join(dict(zip(u"+-0123456789", u"⁺⁻⁰¹²³⁴⁵⁶⁷⁸⁹")).get(c, c) for c in s)
            modified_label = u"[M{}H]{}".format(s, unicode_string)
            return modified_label
        
    def add_annotation(self, xvalsMin, xvalsMax):
        # set them in correct order
        if xvalsMax < xvalsMin: xvalsMin, xvalsMax = xvalsMax, xvalsMin
        
        # set to 4 decimal places
        xvalsMin = round(xvalsMin, 4)
        xvalsMax = round(xvalsMax, 4)
        
        # set values
        try:
            self.min_value.SetValue(str(xvalsMin))
            self.max_value.SetValue(str(xvalsMax))
            self.charge_value.SetValue("")
            self.label_value.SetValue("")
        except: pass
   
    def onMarkOnSpectrum(self, evt):
        marking_state = self.markTgl.GetValue()
        if not marking_state:
            self.markTgl.SetLabel('Annotating: Off')
            self.markTgl.SetForegroundColour(wx.WHITE)
            self.markTgl.SetBackgroundColour(wx.RED)
        else:
            self.markTgl.SetLabel('Annotating: On')
            self.markTgl.SetForegroundColour(wx.WHITE)
            self.markTgl.SetBackgroundColour(wx.BLUE)
            
        self.panelPlot.plot1._on_mark_annotation(state=marking_state)
   
    def onAdd(self, evt):
        min_value = str2num(self.min_value.GetValue())
        max_value = str2num(self.max_value.GetValue())
        charge_value = str2int(self.charge_value.GetValue())
        label_value = self.label_value.GetValue()
        
#         print(self.string_to_unicode(str(charge_value), return_type="M+nH"))
        
        name = "{} - {}".format(min_value, max_value)
        
        # check for duplicate
        in_table, index = self.checkDuplicate(min_value, max_value)
        if in_table: 
            # annotate duplicate item
            if index != -1:
                self.kwargs['annotations'][name]['charge'] = charge_value
                self.peaklist.SetStringItem(index, 3, str(charge_value))
                
                self.kwargs['annotations'][name]['label'] = label_value
                self.peaklist.SetStringItem(index, 4, label_value)
                
            self.documentTree.onUpdateAnotations(self.kwargs['annotations'],
                                                 self.kwargs['document'],
                                                 self.kwargs['dataset'])
            return
        
        if min_value == None or max_value == None or charge_value == None:
            dlgBox("Error", "Please fill min, max and charge fields at least!", 
                   type="Error")
            return
        
        intensity = round(findPeakMax(getNarrow1Ddata(self.kwargs["data"], 
                                                         mzRange=[min_value, max_value])),2)
        
        annotation_dict = {"min":min_value, 
                           "max":max_value,
                           "charge":charge_value,
                           "intensity":intensity,
                           "label":label_value}
        
        self.kwargs['annotations'][name] = annotation_dict
        
        self.table_data.append([min_value, max_value, intensity, charge_value, label_value])
        self.peaklist.Append([min_value, max_value, intensity, charge_value, label_value])
        
        
        itemDataMap = {}
        for i in xrange(len(self.table_data)):
            itemDataMap[i] = tuple(self.table_data[i])
            self.peaklist.SetItemData(i, i)
        self.peaklist.itemDataMap = itemDataMap
        
        self.documentTree.onUpdateAnotations(self.kwargs['annotations'],
                                             self.kwargs['document'],
                                             self.kwargs['dataset'])

    def checkDuplicate(self, min, max):
        count = self.peaklist.GetItemCount()
        for i in range(count):
            table_min = str2num(self.peaklist.GetItem(i, 0).GetText())
            table_max = str2num(self.peaklist.GetItem(i, 1).GetText())
            
            if min == table_min and max == table_max:
                return True, i
            else:
                continue
        return False, -1
      
    def onRemove(self, evt):
        min_value = str2num(self.min_value.GetValue())
        max_value = str2num(self.max_value.GetValue())
        __, index = self.checkDuplicate(min_value, max_value)
        
        if index != -1:
            self.peaklist.DeleteItem(index)
            name = "{} - {}".format(min_value, max_value)
            del self.kwargs['annotations'][name]
        
            # update annotations
            self.documentTree.onUpdateAnotations(self.kwargs['annotations'],
                                                 self.kwargs['document'],
                                                 self.kwargs['dataset'])

# class panelProcessSpectra(wx.MiniFrame):
#     """
#     Simple GUI to view and process mass spectra
#     """
#     
#     def __init__(self, parent, documentTree, config, icons, **kwargs):
#         wx.MiniFrame.__init__(self, parent,-1, 'Annotation...', size=(-1, -1), 
#                               style=wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER)
#         
#         self.parent = parent
#         self.documentTree = documentTree
#         self.panelPlot = documentTree.presenter.view.panelPlots
#         self.config = config
#         self.icons = icons
#         self.help = help()
#                 
#         self.kwargs = kwargs
#                 
#         # make gui items
#         self.makeGUI()
#                       
#         self.CentreOnScreen()
#         self.Layout()
#         self.SetFocus()
#         
#         self.table_data = []
#         
#         # bind
#         wx.EVT_CLOSE(self, self.onClose)
#         self.Bind(wx.EVT_CHAR_HOOK, self.OnKey)
# 
#     def OnKey(self, evt):
#         keyCode = evt.GetKeyCode()
#         if keyCode == wx.WXK_ESCAPE: # key = esc
#             self.onClose(evt=None)
#         
#         evt.Skip()
#         
#     def onClose(self, evt):
#         """Destroy this frame."""
#         # reset state
#         self.Destroy()
#     # ----
#         
#     def makeGUI(self):
#         
#         # make panel
#         panel = self.makePanel()
#         
#         # pack element
#         self.mainSizer = wx.BoxSizer(wx.VERTICAL)
#         self.mainSizer.Add(panel, 1, wx.EXPAND, 5)
#         
#         # fit layout
#         self.mainSizer.Fit(self)
#         self.SetSizer(self.mainSizer)
#         
#     def makePanel(self):
#         
#         panel = wx.Panel(self, -1, size=(-1,-1))
#         mainSizer = wx.BoxSizer(wx.VERTICAL)
#         # make editor
#         min_label = wx.StaticText(panel, -1, u"m/z start:")
#         self.min_value = wx.TextCtrl(panel, -1, "")
#         self.min_value.Bind(wx.EVT_TEXT, self.onApply)
#         
#         max_label = wx.StaticText(panel, -1, u"m/z end:")
#         self.max_value = wx.TextCtrl(panel, -1, "")
#         self.max_value.Bind(wx.EVT_TEXT, self.onApply)
#         
#         charge_label = wx.StaticText(panel, -1, u"charge:")
#         self.charge_value = wx.TextCtrl(panel, -1, "")
#         self.charge_value.Bind(wx.EVT_TEXT, self.onApply)
#         
#         
# #         self.preset_preset1 = wx.Button(panel, wx.ID_OK, u"[M+1H]⁺¹", size=(-1, 22))
# 
#         label_label = wx.StaticText(panel, -1, u"label:")
#         self.label_value = wx.TextCtrl(panel, -1, "", style=wx.TE_RICH2)
#         self.label_value.Bind(wx.EVT_TEXT, self.onApply) 
# 
#         # make buttons
#         self.markTgl = makeToggleBtn(panel, 'Annotating: Off', wx.RED, size=(-1, -1))
#         self.markTgl.SetLabel('Annotating: Off')
#         self.markTgl.SetForegroundColour(wx.WHITE)
#         self.markTgl.SetBackgroundColour(wx.RED)
#         
#         self.addBtn = wx.Button(panel, wx.ID_OK, "Add annotation", size=(-1, 22))
#         self.removeBtn = wx.Button(panel, wx.ID_OK, "Remove", size=(-1, 22))
#         self.cancelBtn = wx.Button(panel, wx.ID_OK, "Cancel", size=(-1, 22))
# 
#         self.markTgl.Bind(wx.EVT_TOGGLEBUTTON, self.onMarkOnSpectrum)
#         self.addBtn.Bind(wx.EVT_BUTTON, self.onAdd)
#         self.removeBtn.Bind(wx.EVT_BUTTON, self.onRemove)
#         self.cancelBtn.Bind(wx.EVT_BUTTON, self.onClose)
#         
# 
#         # button grid
#         btn_grid = wx.GridBagSizer(5, 5)
#         y = 0
#         btn_grid.Add(self.markTgl, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
#         btn_grid.Add(self.addBtn, (y,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
#         btn_grid.Add(self.removeBtn, (y,2), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
#         btn_grid.Add(self.cancelBtn, (y,3), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
#          
# 
#         # pack elements
#         grid = wx.GridBagSizer(5, 5)
#         y = 0
#         grid.Add(min_label, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
#         grid.Add(self.min_value, (y,1), wx.GBSpan(1,1), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
#         grid.Add(max_label, (y,2), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
#         grid.Add(self.max_value, (y,3), wx.GBSpan(1,1), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
#         grid.Add(charge_label, (y,4), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
#         grid.Add(self.charge_value, (y,5), wx.GBSpan(1,1), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
#         y = y+1
#         grid.Add(label_label, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
#         grid.Add(self.label_value, (y,1), wx.GBSpan(1,5), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
#         y = y+1
#         grid.Add(btn_grid, (y,0), wx.GBSpan(1,6), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
#          
#         mainSizer.Add(grid, 0, wx.EXPAND, 10)
#         mainSizer.Add(self.peaklist, 1, wx.EXPAND|wx.ALL, 2)
# 
#         # fit layout
#         mainSizer.Fit(panel)
#         panel.SetSizerAndFit(mainSizer)
# 
#         return panel
    