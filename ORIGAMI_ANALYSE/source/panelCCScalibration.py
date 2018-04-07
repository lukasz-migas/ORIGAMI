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


from ids import *
from numpy import arange, round
from operator import itemgetter
from styles import validator, layout
from toolbox import str2num, str2int, isnumber
import dialogs as dialogs
import itertools
import wx
import wx.lib.mixins.listctrl as listmix


class panelCCScalibration(wx.Panel):
    def __init__( self, parent, config, icons, presenter ):
        wx.Panel.__init__ ( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, 
                            size = wx.Size( 300,400 ), style = wx.TAB_TRAVERSAL )

        self.parent = parent
        self.config = config  
        self.presenter = presenter
        self.currentItem = None
        self.currentItemBottom = None
        self.icons = icons
        
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.topP = topPanel(self, self.config, self.icons,  self.presenter)
        self.sizer.Add(self.topP, 1, wx.EXPAND | wx.ALL, 1)
        self.topP.SetMinSize((250,200))
        self.bottomP = bottomPanel(self, self.config, self.icons, self.presenter, self.topP)
        self.sizer.Add(self.bottomP, 0, wx.EXPAND | wx.ALL, 1)
        self.bottomP.SetMinSize((250,200))
        self.SetSizerAndFit(self.sizer)
        self.Layout()
        
    def showHidePanel(self, evt=None):
        """ Reset the sizer and refresh the manager """
        layout(self, self.sizer)
        self.parent._mgr.Update()
      
    def showHideList(self, flag=False, evt=None):
        """ Reset the sizer and refresh the manager """
        if flag:
            self.bottomP.Hide()
        else:
            self.bottomP.Show()
        layout(self, self.sizer)
        self.parent._mgr.Update()
        
class ListCtrl(wx.ListCtrl, listmix.CheckListCtrlMixin):
    """ListCtrl"""
     
    def __init__(self, parent, id=-1, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.LC_REPORT):
        wx.ListCtrl.__init__(self, parent, id, pos, size, style)
        listmix.CheckListCtrlMixin.__init__(self)
        
class EditableListCtrl(wx.ListCtrl,
                       listmix.TextEditMixin, listmix.CheckListCtrlMixin, listmix.ColumnSorterMixin):
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
        # Block any attempts to change columns 0 and 1
        if event.m_col == 0 or event.m_col == 1:
            event.Veto()
        else:
            event.Skip()
            
    def GetListCtrl(self):
        return self
     
class topPanel(wx.Panel):
    def __init__(self, parent, config, icons, presenter):
        wx.Panel.__init__(self, parent=parent)
        
        self.parent = parent
        self.config = config
        self.presenter = presenter # wx.App
        self.icons = icons

        # used to enable modification of bottom panel document
        self.currentItemBottom = None
        self.data = None
        self.filename = None
        self.rangeName = None
        self.docs = None
        
        self.currentItem = None
        self.flag = False # flag to either show or hide annotation panel
        self.hideList = False
        
        self.allChecked = True
        self.listOfSelected = []
        self.reverse = False
        self.lastColumn = None
        
        self.makeGUI()

    def makeListCtrl(self):

        self.peaklist = ListCtrl(self, style=wx.LC_REPORT)

        self.peaklist.InsertColumn(0,u'File', width=80)
        self.peaklist.InsertColumn(1,u'Start m/z', width=55)
        self.peaklist.InsertColumn(2,u'End m/z', width=55)
        self.peaklist.InsertColumn(3,u'Protein', width=60)
        self.peaklist.InsertColumn(4,u'z', width=30)
        self.peaklist.InsertColumn(5,u'Ω', width=40)
        self.peaklist.InsertColumn(6,u'tD', width=50)
        
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnRightClickMenu)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.disableBottomAnnotation)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onItemSelected)
        self.Bind(wx.EVT_LIST_COL_CLICK, self.OnGetColumnClick)
        self.Bind(wx.EVT_LIST_INSERT_ITEM, self.disableBottomAnnotation)
        
    def disableBottomAnnotation(self, evt):
        self.currentItemBottom = None
        self.data = None
        self.filename = None
        self.rangeName = None
        
        evt.Skip()
        
    def makeGUI(self):
        """ Make panel GUI """
         # make toolbar
        toolbar = self.makeToolbar()
        self.makeListCtrl()
        self.calibrationSubPanel = self.makeCalibrationSubPanel() 
        
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(toolbar, 0, wx.EXPAND, 0)
        self.mainSizer.Add(self.peaklist, 1, wx.EXPAND, 0)
        self.mainSizer.Add(self.calibrationSubPanel, 0, wx.EXPAND)
        
        if self.flag:
            self.mainSizer.Show(2)
        
        # fit layout
        self.mainSizer.Fit(self)
        self.SetSizer(self.mainSizer)
    
    def makeToolbar(self):
        
        # Make bindings
        self.Bind(wx.EVT_TOOL, self.onAddTool, id=ID_addCCScalibrantMenu)
        self.Bind(wx.EVT_TOOL, self.onRemoveTool, id=ID_removeCCScalibrantMenu)
        self.Bind(wx.EVT_TOOL, self.onSaveTool, id=ID_saveCCScalibrantMenu)
        self.Bind(wx.EVT_TOOL, self.onExtractTool, id=ID_extractCCScalibrantMenu)
        self.Bind(wx.EVT_TOOL, self.onProcessTool, id=ID_processCCScalibrantMenu)
        self.Bind(wx.EVT_TOOL, self.onPlotTool, id=ID_plotCCScalibrationMenu)
        self.Bind(wx.EVT_TOOL, self.onShowHidePanel, id=ID_showHidePanelCCSMenu)
        self.Bind(wx.EVT_TOOL, self.onShowHideListCtrl, id=ID_showHideListCCSMenu)
        
        self.Bind(wx.EVT_TOOL, self.OnCheckAllItems, id=ID_checkAllItems_caliMS)
        
        # Create toolbar for the table
        toolbar = wx.ToolBar(self, style=wx.TB_HORIZONTAL | wx.TB_DOCKABLE, id = wx.ID_ANY) 
        toolbar.SetToolBitmapSize((16, 20)) 
        toolbar.AddTool(ID_checkAllItems_caliMS, self.icons.iconsLib['check16'] , 
                              shortHelpString="Check all items")
        toolbar.AddTool(ID_addCCScalibrantMenu, self.icons.iconsLib['add16'], 
                              shortHelpString="Add...") 
        toolbar.AddTool(ID_removeCCScalibrantMenu, self.icons.iconsLib['remove16'], 
                             shortHelpString="Remove...")
        toolbar.AddTool(ID_extractCCScalibrantMenu, self.icons.iconsLib['extract16'],
                             shortHelpString="Extract...")
        toolbar.AddTool(ID_processCCScalibrantMenu, self.icons.iconsLib['process16'],
                             shortHelpString="Process...")
#         toolbar.AddTool(ID_saveCCScalibrantMenu, self.icons.iconsLib['save16'],
#                              shortHelpString="Save...")
#         toolbar.AddTool(wx.ID_ANY, self.icons.iconsLib['scatter16'], 
#                              shortHelpString="Plot...")
        self.gasCombo = wx.ComboBox(toolbar, wx.ID_ANY, value= "Nitrogen",
                                 choices=["Nitrogen", "Helium"], 
                                 style=wx.CB_READONLY)
        toolbar.AddControl(self.gasCombo)
        toolbar.AddTool(ID_showHidePanelCCSMenu, self.icons.iconsLib['document16'], 
                            shortHelpString="Show/Hide annotation panel")
        toolbar.AddTool(ID_showHideListCCSMenu, self.icons.iconsLib['bars16'], 
                            shortHelpString="Show/Hide list below")
        toolbar.Realize()
        
        return toolbar

    def onShowHideListCtrl(self, evt):
        """ Show/hide 'apply CCS panel' below = bottomPanel """
        if self.hideList:
            self.parent.showHideList(flag=self.hideList, evt=None)
            self.hideList = False
        else:
            self.parent.showHideList(flag=self.hideList, evt=None)
            self.hideList = True

    def onShowHidePanel(self, evt):
        """ Show/hide annotation panel """
        if self.flag:
            self.mainSizer.Show(2)
            self.flag = False
        else:
            self.mainSizer.Hide(2)
            self.flag = True

        layout(self, self.mainSizer)
        self.parent.showHidePanel(evt=None)

    def makeCalibrationSubPanel(self):
        self.annotationBox = wx.StaticBox(self, -1, "Annotating: ", size=(200,200))
        
        mainSizer = wx.StaticBoxSizer(self.annotationBox, wx.VERTICAL)
        
        TEXT_SIZE = 240
        TEXT_SIZE_SMALL = 80
        TEXT_SIZE_SMALL_LEFT = 100
        BTN_SIZE = 60
        
        file_label = wx.StaticText(self, -1, "File:")
        self.file_value = wx.TextCtrl(self, -1, "", size=(265, -1))
        self.file_value.Disable()
        file_label.SetFont(wx.SMALL_FONT)
        self.file_value.SetFont(wx.SMALL_FONT)
                
        protein_label = wx.StaticText(self, -1, "Protein:")
        self.protein_value = wx.TextCtrl(self, -1, "", size=(TEXT_SIZE, -1), style=wx.TE_PROCESS_ENTER)
        protein_label.SetFont(wx.SMALL_FONT)
        self.protein_value.SetFont(wx.SMALL_FONT)
        
        self.selectBtn = wx.Button( self, ID_selectCalibrant,
                                    u"...", wx.DefaultPosition, 
                                    wx.Size( 25,-1 ), 0 )
        
        ion_label = wx.StaticText(self, -1, "m/z:")
        self.ion_value = wx.TextCtrl(self, -1, "", size=(TEXT_SIZE_SMALL, -1), validator=validator('float'))
        ion_label.SetFont(wx.SMALL_FONT)
        self.ion_value.SetFont(wx.SMALL_FONT)
        
        mw_label = wx.StaticText(self, -1, "MW (Da):")
        self.mw_value = wx.TextCtrl(self, -1, "", size=(TEXT_SIZE_SMALL, -1), validator=validator('float'),
                                    style=wx.TE_PROCESS_ENTER)
        mw_label.SetFont(wx.SMALL_FONT)
        self.mw_value.SetFont(wx.SMALL_FONT)
        
        charge_label = wx.StaticText(self, -1, "Charge:")
        self.charge_value = wx.TextCtrl(self, -1, "", size=(TEXT_SIZE_SMALL, -1), validator=validator('int'),
                                        style=wx.TE_PROCESS_ENTER)
        charge_label.SetFont(wx.SMALL_FONT)
        self.charge_value.SetFont(wx.SMALL_FONT)
        
        ccs_label = wx.StaticText(self, -1, u"CCS (Å²):")
        self.ccs_value = wx.TextCtrl(self, -1, "", size=(TEXT_SIZE_SMALL, -1), validator=validator('float'),
                                     style=wx.TE_PROCESS_ENTER)
        ccs_label.SetFont(wx.SMALL_FONT)
        self.ccs_value.SetFont(wx.SMALL_FONT)
        
        tD_label = wx.StaticText(self, -1, u"DT (ms):")
        self.tD_value = wx.TextCtrl(self, ID_calibration_changeTD, "", size=(TEXT_SIZE_SMALL, -1), 
                                    validator=validator('float'), style=wx.TE_PROCESS_ENTER)
        tD_label.SetFont(wx.SMALL_FONT)
        self.tD_value.SetFont(wx.SMALL_FONT)
        
        gas_label = wx.StaticText(self, -1, u"Gas:")
        self.gas_value = wx.ComboBox(self, -1, value= "Nitrogen",
                                     choices=["Nitrogen", "Helium"], 
                                     style=wx.CB_READONLY)
        tD_label.SetFont(wx.SMALL_FONT)
        self.tD_value.SetFont(wx.SMALL_FONT)
        
        self.applyBtn = wx.Button( self, ID_calibration_changeTD, u"Apply", wx.DefaultPosition, 
                                   wx.Size( BTN_SIZE,-1 ), 0 )
        
        grid = wx.GridBagSizer(2, 2)
        y = 0
        grid.Add(file_label, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.file_value, (y,1), wx.GBSpan(1,4), flag=wx.ALIGN_RIGHT)
        y = 1
        grid.Add(protein_label, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.protein_value, (y,1), wx.GBSpan(1,3), flag=wx.ALIGN_RIGHT)
        grid.Add(self.selectBtn, (y,4), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT)
        y = 2
        grid.Add(gas_label, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.gas_value, (y,1), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT)
        grid.Add(ion_label, (y,2), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.ion_value, (y,3), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT)
        y = 3
        grid.Add(charge_label, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.charge_value, (y,1), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT)
        grid.Add(mw_label, (y,2), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.mw_value, (y,3), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT)
        y = 4
        grid.Add(tD_label, (y,0), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.tD_value, (y,1), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT)
        grid.Add(ccs_label, (y,2), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.ccs_value, (y,3), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT)
        y = 5
        grid.Add(self.applyBtn, (y,0), wx.GBSpan(1,2), flag=wx.ALIGN_RIGHT)
        
        mainSizer.Add(grid, 0, wx.EXPAND|wx.ALIGN_CENTER|wx.ALL, 2)

        # bind
        self.applyBtn.Bind(wx.EVT_BUTTON, self.onAnnotateItems)
        self.selectBtn.Bind(wx.EVT_BUTTON, self.presenter.onSelectProtein, 
                            id=ID_selectCalibrant)
        
        self.tD_value.Bind(wx.EVT_TEXT_ENTER, self.onAnnotateItems, 
                           id=ID_calibration_changeTD)
        
        self.protein_value.Bind(wx.EVT_TEXT_ENTER, self.onAnnotateItems)
        self.ion_value.Bind(wx.EVT_TEXT_ENTER, self.onAnnotateItems)
        self.mw_value.Bind(wx.EVT_TEXT_ENTER, self.onAnnotateItems)
        self.charge_value.Bind(wx.EVT_TEXT_ENTER, self.onAnnotateItems)
        self.ccs_value.Bind(wx.EVT_TEXT_ENTER, self.onAnnotateItems)
        self.gas_value.Bind(wx.EVT_COMBOBOX, self.onAnnotateItems)      
                    
        return mainSizer

    def onItemSelected(self, evt):
        """ Populate text fields based on selection """

        # Enable what was disabled by the other panel  
        self.ccs_value.Enable()
        self.tD_value.Enable()
        self.gas_value.Enable()
        self.selectBtn.Enable()
        
        self.currentItem = evt.m_itemIndex
        if self.currentItem == None: return
        
        filename = self.peaklist.GetItem(self.currentItem,self.config.ccsTopColNames['filename']).GetText()
        mzStart = self.peaklist.GetItem(self.currentItem,self.config.ccsTopColNames['start']).GetText()
        mzEnd = self.peaklist.GetItem(self.currentItem,self.config.ccsTopColNames['end']).GetText()
        protein = self.peaklist.GetItem(self.currentItem,self.config.ccsTopColNames['protein']).GetText()
        charge = self.peaklist.GetItem(self.currentItem,self.config.ccsTopColNames['charge']).GetText()
        ccs = self.peaklist.GetItem(self.currentItem,self.config.ccsTopColNames['ccs']).GetText()
        tD = self.peaklist.GetItem(self.currentItem,self.config.ccsTopColNames['tD']).GetText()
        gas = self.gasCombo.GetStringSelection()
        
        # Get data from dictionary
        rangeName = ''.join([str(mzStart),'-',str(mzEnd)])
        try:
            self.docs = self.presenter.documentsDict[filename]
        except KeyError:
            return
        
        # Change window label
        boxLabel = ''.join(["Calibrant: ",rangeName,", Document: ", filename])
        self.annotationBox.SetLabel(boxLabel)
        
        # Check that data was extracted for this item
        try: self.docs.calibration[rangeName]
        except KeyError: 
            self.presenter.view.SetStatusText('No data for this ion - please extract data first', 3)
            return
        
        mw = self.docs.calibration[rangeName]['mw']
        gasItemDoc = self.docs.calibration[rangeName]['gas']
        proteinItemDoc = self.docs.calibration[rangeName]['protein']
        proteinDoc = self.docs.moleculeDetails.get('protein', None)
        
        # Check whether document has more up-to-date information
        if gasItemDoc != None:
            gas = gasItemDoc 
        
        # Check whether protein is present in the document instance
        if proteinDoc != None: # Document overrides
            protein = proteinDoc
            if proteinItemDoc != None: # item overrides
                protein = proteinItemDoc
                
        # Get xcentre (m/z)
        xcentre = self.docs.calibration[rangeName].get('xcentre', None)
        
        self.file_value.SetValue(filename)
        self.ion_value.SetValue(str(xcentre))
        self.protein_value.SetValue(protein)
        self.charge_value.SetValue(charge)
        self.ccs_value.SetValue(ccs)
        self.tD_value.SetValue(tD)
        self.gas_value.SetStringSelection(gas)
        self.mw_value.SetValue(str(mw))
        
        evt.Skip()
        
    def onAnnotateItems(self, evt, addProtein=False):
#         print(self.currentItem, self.currentItemBottom)
        if self.currentItem != None and self.currentItemBottom != None:
            self.currentItemBottom = None
        
        if self.currentItemBottom == None:
            if self.currentItem == None: return
            # Constants
            filename = self.file_value.GetValue()
            # Get range name
            rangeName = self.annotationBox.GetLabelText()
            rangeName = rangeName.split(" ")
            rangeName = rangeName[1][:-1]
            
            # Can be modified
            protein = self.protein_value.GetValue()
            charge = self.charge_value.GetValue()
            mw = self.mw_value.GetValue()
            gas = self.gas_value.GetStringSelection()
            xcentre = self.ion_value.GetValue()
            ccs = self.ccs_value.GetValue()
            tD = self.tD_value.GetValue()
            gas = self.gas_value.GetStringSelection()
            
            if addProtein:
                protein = self.config.proteinData[0]
                mw = str(str2num(self.config.proteinData[1]) * 1000) # convert to Da
                charge = self.config.proteinData[3]
                tempXcentre = self.config.proteinData[4]
                # Need to add polarity!
                if gas == 'Helium': tempCCS = self.config.proteinData[4]
                else: tempCCS = self.config.proteinData[5]
                    
                if str2num(tempCCS) != 0: ccs = tempCCS
                if str2num(tempXcentre) != 0: xcentre = tempXcentre
                    
                # Change fields now
                self.protein_value.SetValue(protein)
                self.charge_value.SetValue(charge)
                self.mw_value.SetValue(mw)
                self.ccs_value.SetValue(ccs)
            
            # Get data from dictionary
            self.docs = self.presenter.documentsDict[filename]
            # If we have molecular weight and charge state, modify the 'xcentre' value
            if isnumber(str2int(charge)) and isnumber(str2num(mw)):
                xcentre = ((self.config.elementalMass['Hydrogen']*str2int(charge)+
                           str2num(mw))/str2int(charge))
                
            self.docs.calibration[rangeName]['charge'] = str2int(charge)
            self.docs.calibration[rangeName]['ccs'] = str2num(ccs)
            self.docs.calibration[rangeName]['tD'] = str2num(tD)
            self.docs.calibration[rangeName]['gas'] = gas
            self.docs.calibration[rangeName]['protein'] = protein
            self.docs.calibration[rangeName]['mw'] = str2num(mw)
            self.docs.calibration[rangeName]['peak'][0] = str2num(tD)
            self.docs.calibration[rangeName]['xcentre'] = xcentre
            
            # Set new text for labels
            self.peaklist.SetStringItem(index=self.currentItem,
                                         col=self.config.ccsTopColNames['protein'], 
                                         label=protein)
            self.peaklist.SetStringItem(index=self.currentItem,
                                         col=self.config.ccsTopColNames['charge'], 
                                         label=charge)
            self.peaklist.SetStringItem(index=self.currentItem,
                                         col=self.config.ccsTopColNames['ccs'], 
                                         label=ccs)
            self.peaklist.SetStringItem(index=self.currentItem,
                                         col=self.config.ccsTopColNames['tD'], 
                                         label=tD)
            
            self.presenter.documentsDict[filename] = self.docs

            # Plot on change
            if evt != None:
                if evt.GetId() == ID_calibration_changeTD:
                    self.onPlot(evt=None)
        else:
            protein = self.protein_value.GetValue()
            charge = self.charge_value.GetValue()
            mw = self.mw_value.GetValue()
            gas = self.gas_value.GetStringSelection()
            if isnumber(str2int(charge)) and isnumber(str2num(mw)):
                xcentre = ((self.config.elementalMass['Hydrogen']*str2int(charge)+
                            str2num(mw))/str2int(charge))
            else:
                xcentre = self.parent.bottomP.peaklist.GetItem(self.currentItemBottom,
                                                               self.config.ccsBottomColNames['ion']).GetText()

            if self.data != None:
                self.data['mw'] = str2num(mw)
                self.data['charge'] = str2int(charge)
                self.data['gas'] = gas
                self.data['protein'] = str(protein)
                self.data['xcentre'] = str2num(round(xcentre,4))
                
                # Get appropriate data for format
                if self.format == '2D, extracted':
                    self.docs.IMS2Dions[self.rangeName] = self.data
                elif self.format == '2D, combined':
                    self.docs.IMS2DCombIons[self.rangeName] = self.data
                elif format == '2D, processed':
                    self.docs.IMS2DionsProcess[self.rangeName] = self.data
                elif self.format == 'Input data':
                    self.docs.IMS2DcompData[self.rangeName] = self.data
                
                self.presenter.documentsDict[self.filename] = self.docs
                    
            self.parent.bottomP.peaklist.SetStringItem(index=self.currentItemBottom,
                                         col=self.config.ccsBottomColNames['protein'], 
                                         label=protein)
            self.parent.bottomP.peaklist.SetStringItem(index=self.currentItemBottom,
                                         col=self.config.ccsBottomColNames['charge'], 
                                         label=charge)
            self.parent.bottomP.peaklist.SetStringItem(index=self.currentItemBottom,
                                         col=self.config.ccsBottomColNames['ion'], 
                                         label=str(xcentre))   
        
    def onPlot(self, evt):
        """ Plot data for selected item """
        if self.currentItem == None: return
        filename = self.peaklist.GetItem(self.currentItem,self.config.ccsTopColNames['filename']).GetText()
        mzStart = self.peaklist.GetItem(self.currentItem,self.config.ccsTopColNames['start']).GetText()
        mzEnd = self.peaklist.GetItem(self.currentItem,self.config.ccsTopColNames['end']).GetText()
        # Get data from dictionary
        rangeName = ''.join([str(mzStart),'-',str(mzEnd)])
        
        self.docs = self.presenter.documentsDict[filename]
        
        if (self.docs.fileFormat == 'Format: MassLynx (.raw)' or
            self.docs.fileFormat == 'Format: DataFrame'):
            dtX = self.docs.calibration[rangeName]['xvals']
            dtY = self.docs.calibration[rangeName]['yvals']
            xlabel = self.docs.calibration[rangeName]['xlabels']
            color = self.docs.lineColour
            peak = self.docs.calibration[rangeName]['peak']

        # Plot
        self.presenter.onPlotMSDTCalibration(dtX=dtX, dtY=dtY, color=color,
                                             xlabelDT=xlabel, plotType='1DT')
        
        if peak[0] != "" and peak[1] != "" and peak[0] != None and peak[1] != None:
            self.presenter.addMarkerMS(xvals=peak[0], 
                                       yvals=peak[1],
                                       color=self.config.annotColor, 
                                       marker=self.config.markerShape,
                                       size=self.config.markerSize, 
                                       plot='CalibrationDT')
        
    def onPlotTool(self, evt):
        menu = wx.Menu()
        menu.Append(wx.ID_ANY, "Plot calibration curve")
        menu.Append(wx.ID_ANY, "Overlay selected 1D IM-MS plots")
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def onAddTool(self, evt):
        
        self.Bind(wx.EVT_MENU, self.presenter.onCalibrantRawDirectory, 
                  id=ID_addCCScalibrantFile)
        self.Bind(wx.EVT_MENU, self.presenter.onAddBlankDocument, 
                  id=ID_addNewCalibrationDoc)
        self.Bind(wx.EVT_MENU, self.presenter.onImportCCSDatabase, 
                  id=ID_openCCScalibrationDatabse)
        
        menu = wx.Menu()
        menu.Append(ID_addCCScalibrantFile, "Add file")
#         menu.Append(ID_addCCScalibrantFiles, "Add multiple files")
#         menu.Append(ID_addCCScalibrantFilelist, "Open file list")
#         menu.AppendSeparator()
        menu.Append(ID_openDocument, "Open CCS calibration document")
        menu.AppendSeparator()
        menu.Append(ID_addNewCalibrationDoc, "Add new calibration document")
        menu.AppendSeparator()
        menu.Append(ID_openCCScalibrationDatabse, "Open CCS calibration database (.csv)")
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()
        
    def onRemoveTool(self, evt):
        # Make bindings
        self.Bind(wx.EVT_MENU, self.OnDeleteAll, id=ID_removeCCScalibrantFiles)
        self.Bind(wx.EVT_MENU, self.OnDeleteAll, id=ID_removeCCScalibrantFile)
        self.Bind(wx.EVT_MENU, self.OnClearTable, id=ID_clearTableCaliMS)

        menu = wx.Menu()
        menu.Append(ID_clearTableCaliMS, "Clear table")
        menu.AppendSeparator()
        menu.Append(ID_removeCCScalibrantFile, "Remove selected files")
        menu.Append(ID_removeCCScalibrantFiles, "Remove all files")
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()
        
    def onSaveTool(self, evt):
        menu = wx.Menu()
#         menu.Append(ID_saveCCScalibrantFilelist, "Save file list")

        
        self.Bind(wx.EVT_MENU, self.presenter.saveCCScalibrationToPickle, 
                  id=ID_saveCCScalibration)
        
        menu.Append(ID_saveCCScalibration, "Save CCS calibration to file")
#         menu.Append(ID_saveCCScalibrationCSV, "Save as .csv")
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()
              
    def onProcessTool(self, evt):

        self.Bind(wx.EVT_MENU, self.presenter.OnBuildCCSCalibrationDataset, id=ID_buildCalibrationDataset)
 
        menu = wx.Menu()
        menu.Append(ID_buildCalibrationDataset, "Build calibration curve (selected items)")
#         menu.AppendSeparator()
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()
        
    def onExtractTool(self, evt):
        
        self.Bind(wx.EVT_MENU, self.presenter.onAddCalibrantMultiple, id=ID_extractCCScalibrantSelected)
        self.Bind(wx.EVT_MENU, self.presenter.onAddCalibrantMultiple, id=ID_extractCCScalibrantAll)
        
        menu = wx.Menu()
        menu.Append(ID_extractCCScalibrantSelected, "Extract 1D IM-MS for selected ion")
        menu.Append(ID_extractCCScalibrantAll, "Extract 1D IM-MS for all ion")
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()
                      
    def OnRightClickMenu(self, evt):
        
        self.Bind(wx.EVT_MENU, self.OnDeleteAll, id=ID_removeItemCCSCalibrantPopup)
        self.Bind(wx.EVT_MENU, self.onPlot, id=ID_calibrationPlot1D)
        self.Bind(wx.EVT_MENU, self.presenter.onSelectProtein, id=ID_selectCalibrant)
        
        self.currentItem, flags = self.peaklist.HitTest(evt.GetPosition())
        self.menu = wx.Menu()
        self.menu.Append(ID_calibrationPlot1D, "Show 1D IM-MS plot")
        self.menu.Append(ID_selectCalibrant, "Select calibrant")
#         self.menu.Append(wx.ID_ANY, "Smooth 1D IM-MS curve")
#         self.menu.Append(wx.ID_ANY, "Add protein to CCS calibration")
        self.menu.AppendSeparator()
#         self.menu.Append(wx.ID_ANY, "Save to .csv file...")
#         self.menu.Append(wx.ID_ANY, 'Save figure as .png (selected ion)')
        self.menu.Append(ID_removeItemCCSCalibrantPopup, "Remove item")
        self.PopupMenu(self.menu)
        self.menu.Destroy()
        self.SetFocus()
        
        if evt != None:
            evt.Skip()
        
    def onCheckForDuplicates(self, mzCentre=None):
        """
        Check whether the value being added is already present in the table
        """
        currentItems = self.peaklist.GetItemCount()-1
        while (currentItems >= 0):
            ionInTable = self.peaklist.GetItem(currentItems,1).GetText()
            print(ionInTable, mzCentre)
            if ionInTable == mzCentre:
                print('Ion already in the table')
                currentItems = 0
                return True
            else:
                currentItems-=1
        return False
         
    def OnDeleteAll(self, evt, ticked=False, selected=False, itemID=None):
        """ 
        This function removes selected or all text documents
        """
        if evt.GetId() == ID_removeCCScalibrantFile:
            currentItems = self.peaklist.GetItemCount()-1
            while (currentItems >= 0):
                if self.peaklist.IsChecked(index=currentItems):
                    selectedItem = self.peaklist.GetItem(currentItems, 
                                                         col=self.config.ccsTopColNames['filename']).GetText()
                    mzStart = self.peaklist.GetItem(itemId=currentItems,
                                                     col=self.config.ccsTopColNames['start']).GetText()
                    mzEnd = self.peaklist.GetItem(itemId=currentItems, 
                                                  col=self.config.ccsTopColNames['end']).GetText()
                    rangeName = ''.join([str(mzStart),'-',str(mzEnd)])
                    try: 
                        del self.presenter.documentsDict[selectedItem].calibration[rangeName]
                        if len(self.presenter.documentsDict[selectedItem].calibration.keys()) == 0:
                            self.presenter.documentsDict[selectedItem].gotCalibration = False
                    except KeyError: pass
                    self.peaklist.DeleteItem(currentItems)
                    # Remove reference to calibrants if there are none remaining for the document
                    try:
                        self.presenter.view.panelDocuments.topP.documents.addDocument(docData = self.presenter.documentsDict[selectedItem])
                    except KeyError: pass    
                    currentItems-=1
                else:
                    currentItems-=1
        elif evt.GetId() == ID_removeItemCCSCalibrantPopup:
            selectedItem = self.peaklist.GetItem(self.currentItem, 
                                                 col=self.config.ccsTopColNames['filename']).GetText()
            mzStart = self.peaklist.GetItem(itemId=self.currentItem,
                                             col=self.config.ccsTopColNames['start']).GetText()
            mzEnd = self.peaklist.GetItem(itemId=self.currentItem, 
                                          col=self.config.ccsTopColNames['end']).GetText()
            rangeName = ''.join([str(mzStart),'-',str(mzEnd)])
            try: 
                del self.presenter.documentsDict[selectedItem].calibration[rangeName]
                if len(self.presenter.documentsDict[selectedItem].calibration.keys()) == 0:
                    self.presenter.documentsDict[selectedItem].gotCalibration = False
            except KeyError: pass
            self.peaklist.DeleteItem(self.currentItem)
            # Remove reference to calibrants if there are none remaining for the document
            try:
                self.presenter.view.panelDocuments.topP.documents.addDocument(docData = self.presenter.documentsDict[selectedItem])
            except KeyError: pass  
        else:
        # Ask if you are sure to delete it!
            dlg = dialogs.dlgBox(exceptionTitle='Are you sure?', 
                                 exceptionMsg= "Are you sure you would like to delete ALL text documents?",
                                 type="Question")
            if dlg == wx.ID_NO:
                print('Cancelled operation')
                return
            else:
#                 for textID in range(self.peaklist.GetItemCount()):
                currentItems = self.peaklist.GetItemCount()-1
                while (currentItems >= 0):
                    selectedItem = self.peaklist.GetItem(currentItems, 
                                                         col=self.config.ccsTopColNames['filename']).GetText()
                    mzStart = self.peaklist.GetItem(itemId=currentItems,
                                                     col=self.config.ccsTopColNames['start']).GetText()
                    mzEnd = self.peaklist.GetItem(itemId=currentItems, 
                                                  col=self.config.ccsTopColNames['end']).GetText()
                    rangeName = ''.join([str(mzStart),'-',str(mzEnd)])

                    # Delete selected document from dictionary + table     
                    try:
                        del self.presenter.documentsDict[selectedItem].calibration[rangeName]
                    # Remove reference to calibrants
                        self.presenter.documentsDict[selectedItem].gotCalibration = False
                    except KeyError: pass
                    try:
                        self.presenter.view.panelDocuments.topP.documents.addDocument(docData = self.presenter.documentsDict[selectedItem])
                    except KeyError: pass   
                    self.peaklist.DeleteItem(currentItems)
                    currentItems-=1
        print(''.join(["Remaining documents: ", str(len(self.presenter.documentsDict))]))
            
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
                if (col==self.config.ccsTopColNames['start'] or 
                    col==self.config.ccsTopColNames['end'] or 
                    col==self.config.ccsTopColNames['ccs'] or
                    col==self.config.ccsTopColNames['tD']):
                    itemData = str2num(item.GetText())
                    if itemData == None: itemData = 0
                    tempRow.append(itemData)
                elif col==self.config.ccsTopColNames['charge']:
                    itemData = str2int(item.GetText())
                    if itemData == None: itemData = 0
                    tempRow.append(itemData)
                else:
                    tempRow.append(item.GetText())
            tempData.append(tempRow)
        tempData.sort()
        tempData = list(item for item,_ in itertools.groupby(tempData))
        rows = len(tempData)
        self.peaklist.DeleteAllItems()
        msg = 'Removing duplicates'
        self.presenter.view.SetStatusText(msg, 3)
        for row in range(rows):
            self.peaklist.Append(tempData[row])
            
        if evt is None: return
        else:
            evt.Skip()
    
    def OnCheckAllItems(self, evt, check=True, 
                        override=False):
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
                
        if evt != None:
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
                #  We want to make sure certain columns are numbers
                if (col==self.config.ccsTopColNames['start'] or 
                    col==self.config.ccsTopColNames['end'] or 
                    col==self.config.ccsTopColNames['charge'] or 
                    col==self.config.ccsTopColNames['ccs'] or
                    col==self.config.ccsTopColNames['tD']):
                    itemData = str2num(item.GetText())
                    if itemData == None: itemData = 0
                    tempRow.append(itemData)
                else:
                    tempRow.append(item.GetText())
            tempRow.append(self.peaklist.IsChecked(index=row))
            tempData.append(tempRow)
            
       
        # Sort data  
        tempData.sort(key = itemgetter(column), reverse=self.reverse)
        # Clear table
        self.peaklist.DeleteAllItems()
        
        checkData = []
        for check in tempData:
            checkData.append(check[-1])
            del check[-1]
        
        # Reinstate data
        rowList = arange(len(tempData))
        for row, check in zip(rowList,checkData):
            self.peaklist.Append(tempData[row])
            self.peaklist.CheckItem(row, check)
    
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
    
class bottomPanel(wx.Panel):
    def __init__(self, parent, config, icons, presenter, panel):
        wx.Panel.__init__(self, parent=parent)
        
        self.config = config
        self.presenter = presenter # wx.App
        self.icons = icons
        self.topPanel = panel
        
        self.currentItem = None
        self.allChecked = True
        self.listOfSelected = []
        self.reverse = False
        self.lastColumn = None
        self.makeToolbar()
        self.makeListCtrl()
        
    def makeToolbar(self):
        
        self.Bind(wx.EVT_TOOL, self.onProcessTool, id=ID_processApplyCCScalibrantMenu)
        self.Bind(wx.EVT_TOOL, self.OnCheckAllItems, id=ID_checkAllItems_caliApply)
        self.Bind(wx.EVT_TOOL, self.onRemoveTool, id=ID_removeApplyCCScalibrantMenu)
        self.Bind(wx.EVT_TOOL, self.onRemoveTool, id=ID_removeApplyCCScalibrantMenu)
        
        # Create toolbar for the table
        self.toolbar = wx.ToolBar(self, style=wx.TB_HORIZONTAL | wx.TB_DOCKABLE, id = wx.ID_ANY) 
        self.toolbar.SetToolBitmapSize((16, 20)) 
        self.toolbar.AddTool(ID_checkAllItems_caliApply, self.icons.iconsLib['check16'] , 
                              shortHelpString="Check all items")
        self.toolbar.AddTool(wx.ID_ANY, self.icons.iconsLib['add16'], 
                              shortHelpString="Add...") 
        self.toolbar.AddTool(ID_removeApplyCCScalibrantMenu, self.icons.iconsLib['remove16'], 
                             shortHelpString="Remove...")
        self.calibrationMode = wx.ComboBox(self.toolbar, wx.ID_ANY, value= "Log",
                                           choices=["Linear", "Power"], 
                                           style=wx.CB_READONLY)
        self.toolbar.AddControl(self.calibrationMode)
        self.toolbar.AddTool(ID_processApplyCCScalibrantMenu, self.icons.iconsLib['process16'], 
                             shortHelpString="Process...")
        self.toolbar.Realize()
         
    def disableTopAnnotation(self, evt):
        self.topPanel.currentItem = None
        self.topPanel.currentItemBottom = evt.m_itemIndex
        evt.Skip()
         
    def onItemSelected(self, evt):
        self.currentItem = evt.m_itemIndex
        """ Populate text fields based on selection """
         
        # Change the state of the top panel, otherwise it will constantly try to
        # fire events
        self.topPanel.currentItem = None
         
        self.currentItem = evt.m_itemIndex
        self.topPanel.currentItemBottom = evt.m_itemIndex
        if self.currentItem == None: return

        # Change a couple of labels beforehand
        self.topPanel.ccs_value.Disable()
        self.topPanel.tD_value.Disable()
        self.topPanel.gas_value.Disable()
        self.topPanel.selectBtn.Disable()
        
        # Extract values from the table
        filename = self.peaklist.GetItem(self.currentItem,self.config.ccsBottomColNames['filename']).GetText()
        mzStart = self.peaklist.GetItem(self.currentItem,self.config.ccsBottomColNames['start']).GetText()
        mzEnd = self.peaklist.GetItem(self.currentItem,self.config.ccsBottomColNames['end']).GetText()
        xcentre = self.peaklist.GetItem(self.currentItem,self.config.ccsBottomColNames['ion']).GetText()
        protein = self.peaklist.GetItem(self.currentItem,self.config.ccsBottomColNames['protein']).GetText()
        charge = self.peaklist.GetItem(self.currentItem,self.config.ccsBottomColNames['charge']).GetText()
        format = self.peaklist.GetItem(self.currentItem,self.config.ccsBottomColNames['format']).GetText()
        
        # Get data from dictionary
        rangeName = ''.join([str(mzStart),'-',str(mzEnd)])
        try:
            self.docs = self.presenter.documentsDict[filename]
        except KeyError:
            self.presenter.view.SetStatusText('No data for this ion', 3)
            return
         
        # Change window label
        boxLabel = ''.join(["Ion: ",rangeName,", Document: ", filename])
        self.topPanel.annotationBox.SetLabel(boxLabel)
        
        # Get appropriate data for format
        if format == '2D, extracted':
            data = self.docs.IMS2Dions[rangeName]
        elif format == '2D, combined':
            data = self.docs.IMS2DCombIons[rangeName]
        elif format == '2D, processed':
            data = self.docs.IMS2DionsProcess[rangeName]
        elif format == 'Input data':
            data = self.docs.IMS2DcompData[rangeName]
        else: 
            print('Data was empty')
            
        mw = data.get('mw', None)
        if mw == None:
            mw = self.docs.moleculeDetails.get('molWeight', None)
        
        chargeItemDoc = data.get('charge', None)
        if chargeItemDoc != str2int(charge): # overriding charge
            charge = chargeItemDoc
            
#         # Get xcentre (m/z)
#         xcentre = data.get('xcentre', None)
#         if xcentre == None: 
#             if isnumber(str2int(charge)) and isnumber(str2num(mw)):
#                 xcentre = ((self.config.elementalMass['Hydrogen']*str2int(charge)+
#                            str2num(mw))/str2int(charge))
                
        print('xcentre', xcentre)
        
        # Check whether there is a calibration file/object available
        if len(self.presenter.currentCalibrationParams) == 0:
            print('No global calibration parameters were found')
            if self.docs.gotCalibrationParameters:
                self.presenter.currentCalibrationParams = self.docs.calibrationParameters
                print('Found calibration parameters in the %s file' % self.docs.title)
                print(len(self.presenter.currentCalibrationParams))
            
        
         
        self.topPanel.file_value.SetValue(filename)
        self.topPanel.ion_value.SetValue(xcentre)
        self.topPanel.protein_value.SetValue(protein)
        self.topPanel.charge_value.SetValue(str(charge))
        self.topPanel.mw_value.SetValue(str(mw))
        self.topPanel.tD_value.SetValue("")
        self.topPanel.ccs_value.SetValue("")
        
        # Setup parameters for annotation
        self.topPanel.data = data
        self.topPanel.docs = self.docs
        self.topPanel.filename = filename
        self.topPanel.rangeName = rangeName
        self.topPanel.format = format

        evt.Skip()

    def makeListCtrl(self):
        mainSizer = wx.BoxSizer( wx.VERTICAL )
        self.peaklist = ListCtrl(self, style=wx.LC_REPORT)
        self.peaklist.InsertColumn(0,u'File', width=50)
        self.peaklist.InsertColumn(1,u'Start m/z ', width=55)
        self.peaklist.InsertColumn(2,u'End m/z ', width=55)
        self.peaklist.InsertColumn(3,u'm/z', width=45)
        self.peaklist.InsertColumn(4,u'Protein', width=60)
        self.peaklist.InsertColumn(5,u'z',width=30)
        self.peaklist.InsertColumn(6,u'Format',width=80)

        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnRightClickMenu)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.disableTopAnnotation)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onItemSelected)
        self.Bind(wx.EVT_LIST_COL_CLICK, self.OnGetColumnClick)

        mainSizer.Add(self.toolbar, 0, wx.EXPAND, 0)
        mainSizer.Add(self.peaklist, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(mainSizer)
        
    def onRemoveTool(self, evt):
        # Make bindings
        self.Bind(wx.EVT_MENU, self.OnDeleteAll, id=ID_removeCCScalibrantBottomPanel)
        self.Bind(wx.EVT_MENU, self.OnDeleteAll, id=ID_clearTableCaliMS)

        menu = wx.Menu()
        menu.Append(ID_clearTableCaliMS, "Clear table")
        menu.AppendSeparator()
        menu.Append(ID_removeCCScalibrantBottomPanel, "Remove selected ions")
        menu.Append(ID_clearTableCaliMS, "Remove all ions")
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()        
     
    def OnRightClickMenu(self, evt):
        
        self.Bind(wx.EVT_MENU, self.OnDeleteAll, id=ID_removeCCScalibrantBottomPanelPopup)
        
        
        self.currentItem, flags = self.peaklist.HitTest(evt.GetPosition())
        self.menu = wx.Menu()
#         self.menu.Append(ID_calibrationPlot1D, "Show 1D IM-MS plot")
        self.menu.AppendSeparator()
        self.menu.Append(ID_removeCCScalibrantBottomPanelPopup, "Remove item")
        self.PopupMenu(self.menu)
        self.menu.Destroy()
        self.SetFocus()
        
        if evt != None:
            evt.Skip()

    def onProcessTool(self, evt):
#         self.Bind(wx.EVT_MENU, self.onPrepareDataFrame, id=ID_prepareCCSCalibrant)
#         self.Bind(wx.EVT_MENU, self.presenter.OnBuildCCSCalibrationDataset,
#                   id=ID_buildApplyCalibrationDataset)
        self.Bind(wx.EVT_MENU, self.presenter.OnApplyCCSCalibrationToSelectedIons, 
                  id=ID_applyCalibrationOnDataset)
#         self.Bind(wx.EVT_MENU, self.onCCSCalibrate, id=ID_calibranteCCScalibrant)
        
                
        menu = wx.Menu()
#         menu.Append(ID_detectMZpeaksApplyCCScalibrant, "Detect m/z peaks")
#         menu.Append(ID_detectATDpeaksApplyCCScalibrant, "Detect ATD peaks")
#         menu.AppendSeparator()
#         menu.Append(ID_buildApplyCalibrationDataset, "Build calibration dataset (selected items)")
#         menu.AppendSeparator()
#         menu.Append(ID_prepareCCSCalibrant, "Prepare calibration parameters")
#         menu.Append(ID_prepare2DCCSCalibrant, "Prepare selected dataset for calibration")
#         menu.Append(ID_calibranteCCScalibrant, "Calibrate")
        menu.Append(ID_applyCalibrationOnDataset, "Apply calibration to selected items")
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()
        
    def onCheckForDuplicates(self, mzCentre=None):
        """
        Check whether the value being added is already present in the table
        """
        currentItems = self.peaklist.GetItemCount()-1
        while (currentItems >= 0):
            ionInTable = self.peaklist.GetItem(currentItems,1).GetText()
            print(ionInTable, mzCentre)
            if ionInTable == mzCentre:
                print('Ion already in the table')
                currentItems = 0
                return True
            else:
                currentItems-=1
        return False
            
    def OnDeleteAll(self, evt, ticked=False, selected=False, itemID=None):
        """ 
        This function removes selected or all text documents
        """
        if evt.GetId() == ID_removeCCScalibrantBottomPanel:
            currentItems = self.peaklist.GetItemCount()-1
            while (currentItems >= 0):
                if self.peaklist.IsChecked(index=currentItems):
                    selectedItem = self.peaklist.GetItem(currentItems, col=self.config.ccsTopColNames['filename']).GetText()
                    mzStart = self.peaklist.GetItem(itemId=currentItems, col=self.config.ccsTopColNames['start']).GetText()
                    mzEnd = self.peaklist.GetItem(itemId=currentItems,  col=self.config.ccsTopColNames['end']).GetText()
                    rangeName = ''.join([str(mzStart),'-',str(mzEnd)])
                    self.peaklist.DeleteItem(currentItems)
                    currentItems-=1
                else:
                    currentItems-=1
        elif evt.GetId() == ID_removeCCScalibrantBottomPanelPopup:
            selectedItem = self.peaklist.GetItem(self.currentItem, col=self.config.ccsTopColNames['filename']).GetText()
            mzStart = self.peaklist.GetItem(itemId=self.currentItem, col=self.config.ccsTopColNames['start']).GetText()
            mzEnd = self.peaklist.GetItem(itemId=self.currentItem, col=self.config.ccsTopColNames['end']).GetText()
            rangeName = ''.join([str(mzStart),'-',str(mzEnd)])
            self.peaklist.DeleteItem(self.currentItem)
        else:
            self.OnClearTable(evt=None)

        print(''.join(["Remaining documents: ", str(len(self.presenter.documentsDict))]))
        
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
                if (col==self.config.ccsBottomColNames['start'] or 
                    col==self.config.ccsBottomColNames['end'] or 
                    col==self.config.ccsBottomColNames['ion']):
                    itemData = str2num(item.GetText())
                    if itemData == None: itemData = 0
                    tempRow.append(itemData)
                elif col==self.config.ccsTopColNames['charge']:
                    itemData = str2int(item.GetText())
                    if itemData == None: itemData = 0
                    tempRow.append(itemData)
                else:
                    tempRow.append(item.GetText())
            tempData.append(tempRow)
        tempData.sort()
        tempData = list(item for item,_ in itertools.groupby(tempData))
        rows = len(tempData)
        self.peaklist.DeleteAllItems()
        msg = 'Removing duplicates'
        self.presenter.view.SetStatusText(msg, 3)
        for row in range(rows):
            self.peaklist.Append(tempData[row])
            
        if evt is None: return
        else:
            evt.Skip()
    
    def OnCheckAllItems(self, evt, check=True, 
                        override=False):
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
                
        if evt != None:
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
                #  We want to make sure certain columns are numbers
                if (col==self.config.ccsBottomColNames['start'] or 
                    col==self.config.ccsBottomColNames['end'] or 
                    col==self.config.ccsBottomColNames['charge'] or 
                    col==self.config.ccsBottomColNames['ion']):
                    itemData = str2num(item.GetText())
                    if itemData == None: itemData = 0
                    tempRow.append(itemData)
                else:
                    tempRow.append(item.GetText())
            tempRow.append(self.peaklist.IsChecked(index=row))
            tempData.append(tempRow)
            
       
        # Sort data  
        tempData.sort(key = itemgetter(column), reverse=self.reverse)
        # Clear table
        self.peaklist.DeleteAllItems()
        
        checkData = []
        for check in tempData:
            checkData.append(check[-1])
            del check[-1]
        
        # Reinstate data
        rowList = arange(len(tempData))
        for row, check in zip(rowList,checkData):
            self.peaklist.Append(tempData[row])
            self.peaklist.CheckItem(row, check)
    
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
    
    