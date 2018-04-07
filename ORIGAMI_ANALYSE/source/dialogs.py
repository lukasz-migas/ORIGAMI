# -*- coding: utf-8 -*-

# Load libraries
import itertools
from operator import itemgetter
from numpy import arange
import wx       
from ids import (ID_addNewOverlayDoc, ID_extraSettings_plot1D, ID_processSettings_MS,
                 ID_extraSettings_legend)
from styles import makeCheckbox, validator, makeSuperTip, makeStaticBox
from toolbox import (str2num, str2int, convertRGB1to255, convertRGB255to1, num2str,
                     isnumber)
from help import OrigamiHelp as help
from icons import IconContainer as icons


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
    
    if dlg.ShowModal() == wx.ID_CANCEL: 
        return False
    
    result = dlg.GetValue()
    dlg.Destroy()
    return result

class ListCtrl(wx.ListCtrl):
    """ListCtrl"""
     
    def __init__(self, parent, id=-1, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.LC_REPORT):
        wx.ListCtrl.__init__(self, parent, id, pos, size, style)

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

class panelCompareMS(wx.MiniFrame):
    """
    Simple GUI to select mass spectra to compare
    """
    
    def __init__(self, parent, presenter, config, icons, mass_spectra):
        wx.MiniFrame.__init__(self, parent,-1, 'Compare mass spectra...', size=(-1, -1), 
                              style=wx.DEFAULT_FRAME_STYLE & ~wx.RESIZE_BORDER)
        
        self.parent = parent
        self.presenter = presenter
        self.config = config
        self.icons = icons
        
        self.help = help()
        
        self.currentItem = None
    
        self.mass_spectra = mass_spectra
                
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
        
        self.updateMS(evt=None)
        self.Destroy()
    # ----
        
    def onSelect(self, evt):
        
        self.updateMS(evt=None)
        self.parent.documents.updateComparisonMS(evt=None)
        self.Destroy()
        
    def onPlot (self, evt):
        """
        Update plot with currently selected PCs
        """
        self.updateMS(evt=None)
        self.parent.documents.updateComparisonMS(evt=None)
        
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
        
        ms1_staticBox = makeStaticBox(panel, "Mass spectrum - 1", size=(-1, -1), color=wx.BLACK)
        ms1_staticBox.SetSize((-1,-1))
        ms1_box_sizer = wx.StaticBoxSizer(ms1_staticBox, wx.HORIZONTAL)    
        
        ms2_staticBox = makeStaticBox(panel, "Mass spectrum - 2", size=(-1, -1), color=wx.BLACK)
        ms2_staticBox.SetSize((-1,-1))
        ms2_box_sizer = wx.StaticBoxSizer(ms2_staticBox, wx.HORIZONTAL)    
        
        document1_label = wx.StaticText(panel, -1, "Document:")
        msSpectrum1_spectrum_label = wx.StaticText(panel, -1, "Spectrum:")
        msSpectrum1_color_label = wx.StaticText(panel, -1, "Color:")
        msSpectrum1_transparency_label = wx.StaticText(panel, -1, "Transparency:")
        msSpectrum1_lineStyle_label = wx.StaticText(panel, -1, "Line style:")
        
        document2_label = wx.StaticText(panel, -1, "Document:")
        msSpectrum2_spectrum_label = wx.StaticText(panel, -1, "Spectrum:")
        msSpectrum2_color_label = wx.StaticText(panel, -1, "Color:")
        msSpectrum2_transparency_label = wx.StaticText(panel, -1, "Transparency:")
        msSpectrum2_lineStyle_label = wx.StaticText(panel, -1, "Line style:")
        
        self.document1_value = wx.ComboBox(panel, wx.ID_ANY, 
                                            wx.EmptyString, wx.DefaultPosition, 
                                            wx.Size( -1,-1 ), 
                                            self.mass_spectra, 
                                            wx.CB_READONLY, wx.DefaultValidator)
        self.document1_value.Disable()
        
        self.document2_value = wx.ComboBox(panel, wx.ID_ANY, 
                                            wx.EmptyString, wx.DefaultPosition, 
                                            wx.Size( -1,-1 ), 
                                            self.mass_spectra, 
                                            wx.CB_READONLY, wx.DefaultValidator)
        self.document2_value.Disable()
        
        
        self.msSpectrum1_value = wx.ComboBox(panel, wx.ID_ANY, 
                                            wx.EmptyString, wx.DefaultPosition, 
                                            wx.Size( -1,-1 ), 
                                            self.mass_spectra, 
                                            wx.CB_READONLY, wx.DefaultValidator)
        self.msSpectrum1_value.SetStringSelection(self.mass_spectra[0])
        self.msSpectrum2_value = wx.ComboBox(panel, wx.ID_ANY, 
                                            wx.EmptyString, wx.DefaultPosition, 
                                            wx.Size( -1,-1 ), 
                                            self.mass_spectra, 
                                            wx.CB_READONLY, wx.DefaultValidator)
        self.msSpectrum2_value.SetStringSelection(self.mass_spectra[1])
        
        self.msSpectrum1_colorBtn = wx.Button(panel, wx.ID_ANY, u"", wx.DefaultPosition, 
                                              wx.Size( 26, 26 ), 0 )
        self.msSpectrum1_colorBtn.SetBackgroundColour(convertRGB1to255(self.config.lineColour_MS1))
        
        self.msSpectrum2_colorBtn = wx.Button(panel, wx.ID_ANY,
                                              u"", wx.DefaultPosition, 
                                              wx.Size( 26, 26 ), 0 )
        self.msSpectrum2_colorBtn.SetBackgroundColour(convertRGB1to255(self.config.lineColour_MS2))
        
        self.msSpectrum1_transparency = wx.SpinCtrlDouble(panel, -1, 
                                               value=str(self.config.lineTransparency_MS1*100), 
                                               min=0, max=100, initial=self.config.lineTransparency_MS1*100, 
                                               inc=10, size=(90, -1))
        self.msSpectrum2_transparency = wx.SpinCtrlDouble(panel, -1, 
                                               value=str(self.config.lineTransparency_MS1*100), 
                                               min=0, max=100, initial=self.config.lineTransparency_MS1*100, 
                                               inc=10, size=(90, -1))
        
        self.msSpectrum1_lineStyle_value = wx.ComboBox(panel, wx.ID_ANY, 
                                            wx.EmptyString, wx.DefaultPosition, 
                                            wx.Size( -1,-1 ), 
                                            self.config.lineStylesList, 
                                            wx.CB_READONLY, wx.DefaultValidator)
        self.msSpectrum1_lineStyle_value.SetStringSelection(self.config.lineStyle_MS1)
        
        self.msSpectrum2_lineStyle_value = wx.ComboBox(panel, wx.ID_ANY, 
                                            wx.EmptyString, wx.DefaultPosition, 
                                            wx.Size( -1,-1 ), 
                                            self.config.lineStylesList, 
                                            wx.CB_READONLY, wx.DefaultValidator)
        self.msSpectrum2_lineStyle_value.SetStringSelection(self.config.lineStyle_MS2)
         
        processing_staticBox = makeStaticBox(panel, "Processing", 
                                                 size=(-1, -1), color=wx.BLACK)
        processing_staticBox.SetSize((-1,-1))
        processing_box_sizer = wx.StaticBoxSizer(processing_staticBox, wx.HORIZONTAL)    
         
        self.preprocess_check = makeCheckbox(panel, u"Preprocess")
        self.preprocess_check.SetValue(self.config.compare_massSpectrumParams['preprocess'])
        self.preprocess_tip = makeSuperTip(self.preprocess_check, delay=7, **self.help.compareMS_preprocess)
         
        self.normalize_check = makeCheckbox(panel, u"Normalize")
        self.normalize_check.SetValue(self.config.compare_massSpectrumParams['normalize'])
        
        self.inverse_check = makeCheckbox(panel, u"Inverse")
        self.inverse_check.SetValue(self.config.compare_massSpectrumParams['inverse'])
        
        self.subtract_check = makeCheckbox(panel, u"Subtract")
        self.subtract_check.SetValue(self.config.compare_massSpectrumParams['subtract'])
        
        settings_label = wx.StaticText(panel, wx.ID_ANY, u"Settings:")
        self.settingsBtn = wx.BitmapButton(panel, ID_extraSettings_plot1D,
                                           self.icons.iconsLib['panel_plot1D_16'],
                                           size=(26, 26), 
                                           style=wx.BORDER_DEFAULT | wx.ALIGN_CENTER_VERTICAL)
        self.settingsBtn.SetBackgroundColour((240,240,240))
        self.settingsBtn_tip = makeSuperTip(self.settingsBtn, delay=7, **self.help.compareMS_open_plot1D_settings)
        
        self.legendBtn = wx.BitmapButton(panel, ID_extraSettings_legend,
                                           self.icons.iconsLib['panel_legend_16'],
                                           size=(26, 26), 
                                           style=wx.BORDER_DEFAULT | wx.ALIGN_CENTER_VERTICAL)
        self.legendBtn.SetBackgroundColour((240,240,240))
        self.legendBtn_tip = makeSuperTip(self.legendBtn, delay=7, **self.help.compareMS_open_legend_settings)
        
        self.processingBtn = wx.BitmapButton(panel, ID_processSettings_MS,
                                           self.icons.iconsLib['process_ms_16'],
                                           size=(26, 26), 
                                           style=wx.BORDER_DEFAULT | wx.ALIGN_CENTER_VERTICAL)
        self.processingBtn.SetBackgroundColour((240,240,240))
        self.processingBtn_tip = makeSuperTip(self.processingBtn, delay=7, **self.help.compareMS_open_processMS_settings)
        
        horizontal_line_1 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        horizontal_line_2 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        
        self.selectBtn = wx.Button(panel, wx.ID_OK, "Select", size=(-1, 22))
        self.plotBtn = wx.Button(panel, wx.ID_OK, "Update", size=(-1, 22))
        self.cancelBtn = wx.Button(panel, wx.ID_OK, "Cancel", size=(-1, 22))
        
        
        self.msSpectrum1_value.Bind(wx.EVT_COMBOBOX, self.updateMS)
        self.msSpectrum2_value.Bind(wx.EVT_COMBOBOX, self.updateMS)
        self.preprocess_check.Bind(wx.EVT_CHECKBOX, self.updateMS)
        self.normalize_check.Bind(wx.EVT_CHECKBOX, self.updateMS)
        self.inverse_check.Bind(wx.EVT_CHECKBOX, self.updateMS)
        self.subtract_check.Bind(wx.EVT_CHECKBOX, self.updateMS)

        self.msSpectrum1_colorBtn.Bind(wx.EVT_BUTTON, self.onUpdateMS1color)
        self.msSpectrum2_colorBtn.Bind(wx.EVT_BUTTON, self.onUpdateMS2color)

        self.msSpectrum1_value.Bind(wx.EVT_COMBOBOX, self.onPlot)
        self.msSpectrum2_value.Bind(wx.EVT_COMBOBOX, self.onPlot)
        self.preprocess_check.Bind(wx.EVT_CHECKBOX, self.onPlot)
        self.normalize_check.Bind(wx.EVT_CHECKBOX, self.onPlot)
        self.inverse_check.Bind(wx.EVT_CHECKBOX, self.onPlot)
        self.subtract_check.Bind(wx.EVT_CHECKBOX, self.onPlot)

        self.selectBtn.Bind(wx.EVT_BUTTON, self.onSelect)
        self.plotBtn.Bind(wx.EVT_BUTTON, self.onPlot)
        self.cancelBtn.Bind(wx.EVT_BUTTON, self.onClose)
        
        self.settingsBtn.Bind(wx.EVT_BUTTON, self.presenter.view.onPlotParameters)
        self.legendBtn.Bind(wx.EVT_BUTTON, self.presenter.view.onPlotParameters)
        self.processingBtn.Bind(wx.EVT_BUTTON, self.presenter.view.onProcessParameters)
            
        GRIDBAG_VSPACE = 7
        GRIDBAG_HSPACE = 5
        
        # button grid
        btn_grid = wx.GridBagSizer(GRIDBAG_VSPACE, GRIDBAG_HSPACE)
        y = 0
        btn_grid.Add(self.settingsBtn, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
        btn_grid.Add(self.legendBtn, (y,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL) 
        btn_grid.Add(self.processingBtn, (y,2), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)  
        
        # pack elements
        
        ms1_grid = wx.GridBagSizer(2, 2)
        y = 0
        ms1_grid.Add(document1_label, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        ms1_grid.Add(self.document1_value, (y,1), wx.GBSpan(1,6), flag=wx.EXPAND)
        y = y+1
        ms1_grid.Add(msSpectrum1_spectrum_label, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        ms1_grid.Add(self.msSpectrum1_value, (y,1), wx.GBSpan(1,6), flag=wx.EXPAND)
        y = y+1
        ms1_grid.Add(msSpectrum1_color_label, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        ms1_grid.Add(self.msSpectrum1_colorBtn, (y,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        ms1_grid.Add(msSpectrum1_transparency_label, (y,2), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        ms1_grid.Add(self.msSpectrum1_transparency, (y,3), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        ms1_grid.Add(msSpectrum1_lineStyle_label, (y,4), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        ms1_grid.Add(self.msSpectrum1_lineStyle_value, (y,5), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        ms1_box_sizer.Add(ms1_grid, 0, wx.EXPAND, 10)
        
        ms2_grid = wx.GridBagSizer(2, 2)
        y = 0
        ms2_grid.Add(document2_label, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        ms2_grid.Add(self.document2_value, (y,1), wx.GBSpan(1,6), flag=wx.EXPAND)
        y = y+1
        ms2_grid.Add(msSpectrum2_spectrum_label, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        ms2_grid.Add(self.msSpectrum2_value, (y,1), wx.GBSpan(1,6), flag=wx.EXPAND)
        y = y+1
        ms2_grid.Add(msSpectrum2_color_label, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        ms2_grid.Add(self.msSpectrum2_colorBtn, (y,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        ms2_grid.Add(msSpectrum2_transparency_label, (y,2), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        ms2_grid.Add(self.msSpectrum2_transparency, (y,3), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        ms2_grid.Add(msSpectrum2_lineStyle_label, (y,4), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        ms2_grid.Add(self.msSpectrum2_lineStyle_value, (y,5), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        ms2_box_sizer.Add(ms2_grid, 0, wx.EXPAND, 10)
        
        processing_grid = wx.GridBagSizer(2, 2)
        y = 0
        processing_grid.Add(self.preprocess_check, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        processing_grid.Add(self.normalize_check, (y,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        processing_grid.Add(self.inverse_check, (y,2), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        processing_grid.Add(self.subtract_check, (y,3), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT)
        processing_box_sizer.Add(processing_grid, 0, wx.EXPAND, 10)
        
        grid = wx.GridBagSizer(GRIDBAG_VSPACE, GRIDBAG_HSPACE)
        y = 0
        grid.Add(ms1_box_sizer, (y,0), wx.GBSpan(1,6), flag=wx.EXPAND)
        y = y+1
        grid.Add(ms2_box_sizer, (y,0), wx.GBSpan(1,6), flag=wx.EXPAND)
        y = y+1
        grid.Add(processing_box_sizer, (y,0), wx.GBSpan(1,6), flag=wx.EXPAND)
        y = y+1
        grid.Add(horizontal_line_1, (y,0), wx.GBSpan(1,6), flag=wx.EXPAND)
        y = y + 1
        grid.Add(settings_label, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        grid.Add(btn_grid, (y,1), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
        y = y+1
        grid.Add(horizontal_line_2, (y,0), wx.GBSpan(1,6), flag=wx.EXPAND)
        y = y+1
        grid.Add(self.selectBtn, (y,2), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(self.plotBtn, (y,3), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
        grid.Add(self.cancelBtn, (y,4), wx.GBSpan(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
        
        mainSizer.Add(grid, 0, wx.EXPAND, 10)

        # fit layout
        mainSizer.Fit(panel)
        panel.SetSizerAndFit(mainSizer)

        return panel
   
    def updateMS(self, evt):
        self.config.compare_massSpectrum = [self.msSpectrum1_value.GetStringSelection(),
                                            self.msSpectrum2_value.GetStringSelection()]
        self.config.lineTransparency_MS1 = str2num(self.msSpectrum1_transparency.GetValue())/100
        self.config.lineStyle_MS1 = self.msSpectrum1_lineStyle_value.GetStringSelection()
        
        self.config.lineTransparency_MS2 = str2num(self.msSpectrum2_transparency.GetValue())/100
        self.config.lineStyle_MS2 = self.msSpectrum2_lineStyle_value.GetStringSelection()
        
        self.config.compare_massSpectrumParams['preprocess'] = self.preprocess_check.GetValue()
        self.config.compare_massSpectrumParams['inverse'] = self.inverse_check.GetValue()
        self.config.compare_massSpectrumParams['normalize'] = self.normalize_check.GetValue()
        self.config.compare_massSpectrumParams['subtract'] = self.subtract_check.GetValue()
        
        if evt != None:
            evt.Skip() 
           
    def onUpdateMS1color(self, evt):
        # Restore custom colors
        custom = wx.ColourData()
        for key in self.config.customColors:
            custom.SetCustomColour(key, self.config.customColors[key])
        dlg = wx.ColourDialog(self, custom)
        dlg.GetColourData().SetChooseFull(True)
        
        # Show dialog and get new colour
        if dlg.ShowModal() == wx.ID_OK:
            data = dlg.GetColourData()
            newColour = list(data.GetColour().Get())
            self.config.lineColour_MS1 = convertRGB255to1(newColour)
            dlg.Destroy()
            # Retrieve custom colors
            for i in xrange(15):
                self.config.customColors[i] = data.GetCustomColour(i)
        else:
            return
        self.msSpectrum1_colorBtn.SetBackgroundColour(newColour)
         
    def onUpdateMS2color(self, evt):
        # Restore custom colors
        custom = wx.ColourData()
        for key in self.config.customColors:
            custom.SetCustomColour(key, self.config.customColors[key])
        dlg = wx.ColourDialog(self, custom)
        dlg.GetColourData().SetChooseFull(True)
        
        # Show dialog and get new colour
        if dlg.ShowModal() == wx.ID_OK:
            data = dlg.GetColourData()
            newColour = list(data.GetColour().Get())
            self.config.lineColour_MS2 = convertRGB255to1(newColour)
            dlg.Destroy()
            # Retrieve custom colors
            for i in xrange(15):
                self.config.customColors[i] = data.GetCustomColour(i)
        else:
            return
        self.msSpectrum2_colorBtn.SetBackgroundColour(newColour)

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
            self.parent.peaklist.SetItemTextColour(self.itemInfo['id'], color)
              
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
            self.parent.filelist.SetItemTextColour(self.itemInfo['id'], color)
              
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
        

      