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
from ids import *
import wx.lib.mixins.listctrl as listmix
from wx import ID_ANY
import dialogs as dialogs
from toolbox import isempty, str2num, str2int, saveAsText
from operator import itemgetter
from numpy import arange, vstack, insert
import csv
import itertools
from matplotlib import style
from origamiStyles import makeCheckbox


class panelMultipleIons ( wx.Panel ):
    
    def __init__( self, parent, config, icons, presenter ):
        wx.Panel.__init__ ( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, 
                            size = wx.Size( 300,400 ), style = wx.TAB_TRAVERSAL )

        self.parent = parent
        self.config = config  
        self.presenter = presenter
        self.currentItem = None
        self.icons = icons
               

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.topP = topPanel(self, self.config, self.icons,  self.presenter)
        sizer.Add(self.topP, 1, wx.EXPAND | wx.ALL, 1)
        self.SetSizer(sizer)
  #       
class ListCtrl(wx.ListCtrl, listmix.CheckListCtrlMixin):
    """ListCtrl"""
     
    def __init__(self, parent, id=-1, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.LC_REPORT):
        wx.ListCtrl.__init__(self, parent, id, pos, size, style)
        listmix.CheckListCtrlMixin.__init__(self)
        
class topPanel(wx.Panel):
    def __init__(self, parent, config, icons, presenter):
        wx.Panel.__init__(self, parent=parent)
        
        self.config = config
        self.presenter = presenter # wx.App
        self.icons = icons
        self.listOfSelected = []
        self.allChecked = True
        self.override = self.config.overrideCombine
        
        self.onSelectingItem = True
        
        self.docs = None
        self.reverse = False
        self.lastColumn = None
        self.currentItem = None
        
        self.flag = False # flag to either show or hide annotation panel
        
        self.useInternalParams = self.config.useInternalParamsCombine
        self.process = False
        
        self.makeGUI()
        self.onChangeOrigamiMethod(evt=None)
        
    def makeGUI(self):
        """ Make panel GUI """
         # make toolbar
        toolbar = self.makeToolbar()
        self.makeListCtrl()
        self.makeOrigamiSubPanel = self.makeOrigamiSubPanel() 
        
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainSizer.Add(toolbar, 0, wx.EXPAND, 0)
        self.mainSizer.Add(self.peaklist, 1, wx.EXPAND, 0)
        self.mainSizer.Add(self.makeOrigamiSubPanel, 0, wx.EXPAND)
        
        if self.flag:
            self.mainSizer.Show(2)
        
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
        
        # Create toolbar for the table
        toolbar = wx.ToolBar(self, style=wx.TB_HORIZONTAL | wx.TB_DOCKABLE, id = wx.ID_ANY) 
        toolbar.SetToolBitmapSize((16, 16)) 
        toolbar.AddTool(ID_checkAllItems_Ions, self.icons.iconsLib['check16'] , 
                              shortHelpString="Check all items")
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

        toolbar.Realize()     
        
        return toolbar
              
    def makeListCtrl(self):


        self.peaklist = ListCtrl(self, style=wx.LC_REPORT)
        self.peaklist.InsertColumn(0,u'Start m/z', width=70)
        self.peaklist.InsertColumn(1,u'End m/z', width=60)
        self.peaklist.InsertColumn(2,u'z', width=40)
        self.peaklist.InsertColumn(3,u'Colormap', width=60)
        self.peaklist.InsertColumn(4,u'\N{GREEK SMALL LETTER ALPHA}', width=40)
        self.peaklist.InsertColumn(5,u'File', width=50)
        self.peaklist.InsertColumn(6,u'Method', width=80)
        self.peaklist.InsertColumn(7,u'%', width=70)
        self.peaklist.InsertColumn(8,u'Label', width=50)

        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onItemSelected)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnRightClickMenu)
        self.Bind(wx.EVT_LIST_COL_CLICK, self.OnGetColumnClick)
                
    def makeOrigamiSubPanel(self):
        mainSizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, "Annotations", size=(200,200)), wx.VERTICAL)
        
        TEXT_SIZE = 262
        TEXT_SIZE_SMALL = 45
        TEXT_SIZE_SMALL_LEFT = 100
        BTN_SIZE = 60
        
        file_label = wx.StaticText(self, -1, "File:")
        self.file_value = wx.TextCtrl(self, -1, "", size=(TEXT_SIZE, -1))
        self.file_value.Disable()
        file_label.SetFont(wx.SMALL_FONT)
        self.file_value.SetFont(wx.SMALL_FONT)
        
        ion_label = wx.StaticText(self, -1, "Ion:")
        self.ion_value = wx.TextCtrl(self, -1, "", size=(TEXT_SIZE_SMALL_LEFT, -1), 
                                     validator=validator('float'))
        ion_label.SetFont(wx.SMALL_FONT)
        self.ion_value.SetFont(wx.SMALL_FONT)
        self.ion_value.Disable()
        
        charge_label = wx.StaticText(self, -1, "Charge")
        self.charge_value = wx.TextCtrl(self, -1, "", size=(TEXT_SIZE_SMALL, -1), 
                                        style=wx.TE_PROCESS_ENTER)
        charge_label.SetFont(wx.SMALL_FONT)
        self.charge_value.SetFont(wx.SMALL_FONT)
        
        startScan_label = wx.StaticText(self, -1, "Start scan")
        self.startScan_value = wx.TextCtrl(self, -1, "", size=(TEXT_SIZE_SMALL, -1))
        startScan_label.SetFont(wx.SMALL_FONT)
        self.startScan_value.SetFont(wx.SMALL_FONT)
         
        spv_label = wx.StaticText(self, -1, "SPV:")
        self.spv_value = wx.TextCtrl(self, -1, "", 
                                     size=(TEXT_SIZE_SMALL, -1), validator=validator('int'))
        spv_label.SetFont(wx.SMALL_FONT)
        self.spv_value.SetFont(wx.SMALL_FONT)
         
        startV_label = wx.StaticText(self, -1, "Start V:")
        self.startV_value = wx.TextCtrl(self, -1, "", 
                                        size=(TEXT_SIZE_SMALL, -1), validator=validator('float'))
        startV_label.SetFont(wx.SMALL_FONT)
        self.startV_value.SetFont(wx.SMALL_FONT)
         
        endV_label = wx.StaticText(self, -1, "End V:")
        self.endV_value = wx.TextCtrl(self, -1, "", 
                                      size=(TEXT_SIZE_SMALL, -1), validator=validator('float'))
        endV_label.SetFont(wx.SMALL_FONT)
        self.endV_value.SetFont(wx.SMALL_FONT)
         
        stepV_label = wx.StaticText(self, -1, u"Step V:")
        self.stepV_value = wx.TextCtrl(self, ID_calibration_changeTD, "", 
                                       size=(TEXT_SIZE_SMALL, -1), validator=validator('float'))
        stepV_label.SetFont(wx.SMALL_FONT)
        self.stepV_value.SetFont(wx.SMALL_FONT)
        
        boltzman_label = wx.StaticText(self, -1, "Boltzmann \nOffset:")
        self.boltzman_value = wx.TextCtrl(self, -1, "", 
                                     size=(TEXT_SIZE_SMALL, -1), validator=validator('float'))
        boltzman_label.SetFont(wx.SMALL_FONT)
        self.boltzman_value.SetFont(wx.SMALL_FONT)
         
        expPerc_label = wx.StaticText(self, -1, "Exp %:")
        self.expPerc_value = wx.TextCtrl(self, -1, "", 
                                        size=(TEXT_SIZE_SMALL, -1), validator=validator('float'))
        expPerc_label.SetFont(wx.SMALL_FONT)
        self.expPerc_value.SetFont(wx.SMALL_FONT)
         
        expIncr_label = wx.StaticText(self, -1, "Exp \nincrement:")
        self.expIncr_value = wx.TextCtrl(self, -1, "", 
                                      size=(TEXT_SIZE_SMALL, -1), validator=validator('float'))
        expIncr_label.SetFont(wx.SMALL_FONT)
        self.expIncr_value.SetFont(wx.SMALL_FONT)
        
        transMask_label = wx.StaticText(self, -1, u"\N{GREEK SMALL LETTER ALPHA}/Mask:")
        self.transMask_value = wx.TextCtrl(self, -1, "", 
                                      size=(TEXT_SIZE_SMALL, -1), validator=validator('float'))
        expIncr_label.SetFont(wx.SMALL_FONT)
        self.expIncr_value.SetFont(wx.SMALL_FONT)
        
        label_label = wx.StaticText(self, -1, "Label:")
        self.label_value = wx.TextCtrl(self, -1, "", 
                                      size=(TEXT_SIZE, -1))
        expIncr_label.SetFont(wx.SMALL_FONT)
        self.expIncr_value.SetFont(wx.SMALL_FONT)
         
        acqMethod_label = wx.StaticText(self, -1, u"Method:")
        self.acqMethod_value = wx.ComboBox(self, -1, value= "Linear",
                                     choices=["Linear", "Exponential", "Fitted",
                                              "User-defined", "Manual"], 
                                     style=wx.CB_READONLY)
        
        colormap_label = wx.StaticText(self, -1, u"Colormap:")
        self.colormap_value = wx.ComboBox(self, -1, value=self.config.currentCmap,
                                     choices=self.config.cmaps2, 
                                     style=wx.CB_READONLY)

        self.restrictCmaps = makeCheckbox(self, u"")
        self.restrictCmaps.SetToolTip(makeTooltip(text="Restrict the selection of colormaps to much narrower range."))
        self.restrictCmaps.SetValue(False)
        
        
        self.applyBtn = wx.Button( self, ID_changeParams_multiIon, u"Apply", wx.DefaultPosition, 
                                   wx.Size( BTN_SIZE,-1 ), 0 )
        self.recalculateBtn = wx.Button( self, ID_recalculateORIGAMI, u"Recalculate", wx.DefaultPosition, 
                                   wx.Size( 70,-1 ), 0 )
        self.recalculateBtn.Hide()
        self.replotBtn = wx.Button( self, ID_ANY, u"Plot", wx.DefaultPosition, 
                                   wx.Size( BTN_SIZE,-1 ), 0 )
        self.replotBtn.Hide()
        
        self.recalculateBtn.Disable()
        
        self.applyBtn.Bind(wx.EVT_BUTTON, self.onAnnotateItems)
        self.recalculateBtn.Bind(wx.EVT_BUTTON, 
                                 self.onRecalculateCombinedORIGAMI, 
                                 id=ID_recalculateORIGAMI)
        
        
        self.charge_value.Bind(wx.EVT_TEXT_ENTER, self.onAnnotateItems)
        self.transMask_value.Bind(wx.EVT_TEXT, self.onAnnotateItems)
        self.label_value.Bind(wx.EVT_TEXT, self.onAnnotateItems)
        self.acqMethod_value.Bind(wx.EVT_COMBOBOX, self.onChangeOrigamiMethod)
        self.restrictCmaps.Bind(wx.EVT_CHECKBOX, self.onRestrictCmaps)
        
        
        grid = wx.GridBagSizer(2, 2)
        grid.Add(file_label, (0,0), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.file_value, (0,1), wx.GBSpan(1,5), flag=wx.ALIGN_LEFT)
         
        grid.Add(ion_label, (1,0), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.ion_value, (1,1), wx.GBSpan(1,2), flag=wx.ALIGN_LEFT)
          
        grid.Add(acqMethod_label, (1,3), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.acqMethod_value, (1,4), wx.GBSpan(1,2), flag=wx.ALIGN_LEFT|wx.EXPAND)

        grid.Add(charge_label, (2,0), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.charge_value, (2,1), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT)

        grid.Add(startScan_label, (2,2), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.startScan_value, (2,3), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT)

        grid.Add(spv_label, (2,4), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.spv_value, (2,5), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT)
  
        grid.Add(startV_label, (3,0), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.startV_value, (3,1), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT)
          
        grid.Add(endV_label, (3,2), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.endV_value, (3,3), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
          
        grid.Add(stepV_label, (3,4), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.stepV_value, (3,5), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        
        grid.Add(boltzman_label, (4,0), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.boltzman_value, (4,1), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
          
        grid.Add(expIncr_label, (4,2), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.expIncr_value, (4,3), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        
        grid.Add(expPerc_label, (4,4), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.expPerc_value, (4,5), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)

        grid.Add(transMask_label, (5,0), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.transMask_value, (5,1), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        
        grid.Add(colormap_label, (5,2), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.colormap_value, (5,3), wx.GBSpan(1,2), flag=wx.ALIGN_LEFT|wx.EXPAND)
        grid.Add(self.restrictCmaps, (5,5), wx.GBSpan(1,1), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        
        grid.Add(label_label, (6,0), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.label_value, (6,1), wx.GBSpan(1,5), flag=wx.ALIGN_LEFT)
        
        grid.Add(self.applyBtn, (7,0), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT)
        grid.Add(self.replotBtn, (7,1), wx.GBSpan(1,1), flag=wx.ALIGN_RIGHT)
        grid.Add(self.recalculateBtn, (7,2), wx.GBSpan(1,2), flag=wx.ALIGN_LEFT)
        
        mainSizer.Add(grid, 0, wx.EXPAND|wx.ALIGN_CENTER|wx.ALL, 2)
        
        return mainSizer
        
    def onChangeOrigamiMethod(self, evt):
        
        if self.acqMethod_value.GetValue() == "Linear":
            enableList  = [self.spv_value, self.startV_value, self.endV_value,
                           self.stepV_value, self.startScan_value]
            disableList = [self.expIncr_value, self.expPerc_value, self.boltzman_value]
        elif self.acqMethod_value.GetValue() == "Exponential":
            enableList  = [self.spv_value, self.startV_value, self.endV_value,
                           self.stepV_value, self.expIncr_value, self.expPerc_value,
                           self.startScan_value]
            disableList = [self.boltzman_value]
        elif self.acqMethod_value.GetValue() == "Fitted":
            enableList  = [self.spv_value, self.startV_value, self.endV_value,
                           self.stepV_value, self.boltzman_value,
                           self.startScan_value]
            disableList = [self.expPerc_value, self.expIncr_value]
        elif self.acqMethod_value.GetValue() == "User-defined":
            enableList  = [self.startScan_value]
            disableList = [self.expPerc_value, self.expIncr_value, self.spv_value, self.startV_value, self.endV_value,
                           self.stepV_value, self.boltzman_value]
        elif self.acqMethod_value.GetValue() == "Manual":
            enableList  = []
            disableList =  [self.startScan_value, self.spv_value,
                            self.startV_value, self.endV_value,
                            self.stepV_value, self.boltzman_value,
                            self.expIncr_value, self.expPerc_value]
            
        for item in enableList:
            item.Enable()
        for item in disableList:
            item.Disable()
        
        if evt != None:
            evt.Skip()
        
    def onItemSelected(self, evt):

        self.onSelectingItem = True
        self.currentItem = evt.m_itemIndex
        filename = self.peaklist.GetItem(self.currentItem,self.config.peaklistColNames['filename']).GetText()
        mzStart = self.peaklist.GetItem(self.currentItem,self.config.peaklistColNames['start']).GetText()
        mzEnd = self.peaklist.GetItem(self.currentItem,self.config.peaklistColNames['end']).GetText()
        charge = self.peaklist.GetItem(self.currentItem,self.config.peaklistColNames['charge']).GetText()
        transparency = self.peaklist.GetItem(self.currentItem,self.config.peaklistColNames['alpha']).GetText()
        colormap = self.peaklist.GetItem(self.currentItem,self.config.peaklistColNames['color']).GetText()
        method = self.peaklist.GetItem(self.currentItem,self.config.peaklistColNames['method']).GetText()
        label = self.peaklist.GetItem(self.currentItem,self.config.peaklistColNames['label']).GetText()
               
        
        rangeName = ''.join([str(mzStart),'-',str(mzEnd)])
        try:
            self.docs = self.presenter.documentsDict[filename]
        except KeyError:
            return
        
        # Check whether the ion has combined ions
        parameters = None
        if self.docs.gotCombinedExtractedIons:
            try: 
                parameters = self.docs.IMS2DCombIons[rangeName].get('parameters', None)
            except KeyError: 
                parameters = None
                pass
            
        if method == 'Manual':
            self.acqMethod_value.SetStringSelection(method)
            
        if parameters != None:
            method = parameters.get('method', None)
            if method != None:
                try:
                    self.acqMethod_value.SetStringSelection(method)
                except TypeError: 
                    print('method', method)
                    pass
                
            firstVoltage = parameters.get('firstVoltage', None)
            scansPerVoltage = parameters.get('spv', None)
            startVoltage = parameters.get('startV', None)
            endVoltage = parameters.get('endV', None)
            stepVoltage = parameters.get('stepV', None)
            expIncrement = parameters.get('expIncrement', None)
            expPercent = parameters.get('expPercent', None)
            dx = parameters.get('dx', None)
            
            self.startScan_value.SetValue(str(firstVoltage))
            self.spv_value.SetValue(str(scansPerVoltage))
            self.startV_value.SetValue(str(startVoltage))
            self.endV_value.SetValue(str(endVoltage))
            self.stepV_value.SetValue(str(stepVoltage))
            self.boltzman_value.SetValue(str(dx))
            self.expIncr_value.SetValue(str(expIncrement))
            self.expPerc_value.SetValue(str(expPercent))            
            self.recalculateBtn.Enable()
        else: 
            self.recalculateBtn.Disable()


        # Make sure values are not None
        if charge == None: charge =''            
        if label == None: label =''
        if transparency == None: transparency =''
        
        self.file_value.SetValue(filename)
        self.ion_value.SetValue(rangeName)
        self.charge_value.SetValue(str(charge))
        self.label_value.SetValue(str(label))
        
        self.colormap_value.SetStringSelection(colormap)
        self.transMask_value.SetValue(str(transparency))
        
        self.onSelectingItem = False
        
        # Enable/disable boxes
        enableList, disableList = [], []
        if self.acqMethod_value.GetValue() == "Linear":
            enableList  = [self.spv_value, self.startV_value, self.endV_value,
                           self.stepV_value, self.startScan_value]
            disableList = [self.expIncr_value, self.expPerc_value, self.boltzman_value]
        elif self.acqMethod_value.GetValue() == "Exponential":
            enableList  = [self.spv_value, self.startV_value, self.endV_value,
                           self.stepV_value, self.expIncr_value, self.expPerc_value]
            disableList = [self.boltzman_value]
        elif self.acqMethod_value.GetValue() == "Fitted":
            enableList  = [self.spv_value, self.startV_value, self.endV_value,
                           self.stepV_value, self.boltzman_value, self.startScan_value]
            disableList = [self.expPerc_value, self.expIncr_value]
        elif self.acqMethod_value.GetValue() == "User-defined":
            enableList  = [self.startScan_value]
            disableList = [self.expPerc_value, self.expIncr_value, self.spv_value, self.startV_value, self.endV_value,
                           self.stepV_value, self.boltzman_value]
        elif (self.docs.dataType == 'Type: ORIGAMI' or 
              self.acqMethod_value.GetValue() == 'None' or
              self.acqMethod_value.GetValue() == 'Manual'):
            enableList  = []
            disableList = [self.expPerc_value, self.expIncr_value, self.spv_value, self.startV_value, self.endV_value,
                           self.stepV_value, self.boltzman_value, self.startScan_value]
            
            
        for item in enableList:
            item.Enable()
        for item in disableList:
            item.Disable()
            try: item.SetValue('')
            except: pass
        
    def onAnnotateItems(self, evt):
        
        if self.onSelectingItem: return
        filename = self.file_value.GetValue()
        rangeName = self.ion_value.GetValue()
        
        method = self.acqMethod_value.GetValue()
        
        firstVoltage = str2int(self.startScan_value.GetValue())
        scansPerVoltage = str2int(self.spv_value.GetValue())
        startVoltage = str2num(self.startV_value.GetValue())
        endVoltage = str2num(self.endV_value.GetValue())
        stepVoltage = str2num(self.stepV_value.GetValue())
        dx = str2num(self.boltzman_value.GetValue())
        expIncrement = str2num(self.expIncr_value.GetValue())
        expPercent = str2num(self.expPerc_value.GetValue())
        charge = str2int(self.charge_value.GetValue())
        colormap = self.colormap_value.GetStringSelection()
        transparency = str2num(self.transMask_value.GetValue())
        label = self.label_value.GetValue()
        
        
        print(charge)
        
        if self.docs == None: return
        
        # Add to dictionary
        if self.docs.gotCombinedExtractedIons:
            try: self.docs.IMS2DCombIons[rangeName]
            except KeyError: return
            if self.docs.IMS2DCombIons[rangeName] and self.docs.dataType == 'Type: ORIGAMI':
                self.docs.IMS2DCombIons[rangeName]['parameters']['firstVoltage'] = firstVoltage
                self.docs.IMS2DCombIons[rangeName]['parameters']['spv'] = scansPerVoltage
                self.docs.IMS2DCombIons[rangeName]['parameters']['startV'] = startVoltage
                self.docs.IMS2DCombIons[rangeName]['parameters']['endV'] = endVoltage
                self.docs.IMS2DCombIons[rangeName]['parameters']['stepV'] = stepVoltage
                self.docs.IMS2DCombIons[rangeName]['parameters']['expIncrement'] = expIncrement
                self.docs.IMS2DCombIons[rangeName]['parameters']['expPercent'] = expPercent
                self.docs.IMS2DCombIons[rangeName]['parameters']['dx'] = dx
                self.docs.IMS2DCombIons[rangeName]['parameters']['method'] = method
                
        # Update general keys 
        try:
            if self.docs.IMS2Dions[rangeName]:
                self.docs.IMS2Dions[rangeName]['charge'] = charge
                self.docs.IMS2Dions[rangeName]['cmap'] = colormap
                self.docs.IMS2Dions[rangeName]['label'] = label
                self.docs.IMS2Dions[rangeName]['alpha'] = transparency
        except KeyError: 
            pass
        try:
            if self.docs.IMS2DCombIons[rangeName]:
                self.docs.IMS2DCombIons[rangeName]['charge'] = charge
                self.docs.IMS2DCombIons[rangeName]['cmap'] = colormap
                self.docs.IMS2DCombIons[rangeName]['label'] = label
                self.docs.IMS2DCombIons[rangeName]['alpha'] = transparency
        except KeyError: 
            pass
        try:
            if self.docs.IMS2DionsProcess[rangeName]:
                self.docs.IMS2DionsProcess[rangeName]['charge'] = charge
                self.docs.IMS2DionsProcess[rangeName]['cmap'] = colormap
                self.docs.IMS2DionsProcess[rangeName]['label'] = label
                self.docs.IMS2DionsProcess[rangeName]['alpha'] = transparency
        except KeyError: 
            pass
        
        
        # Update list
        self.peaklist.SetStringItem(index=self.currentItem, col=self.config.peaklistColNames['charge'], 
                                         label=str(charge))
        self.peaklist.SetStringItem(index=self.currentItem, col=self.config.peaklistColNames['color'], 
                                         label=colormap)
        self.peaklist.SetStringItem(index=self.currentItem, col=self.config.peaklistColNames['alpha'], 
                                         label=str(transparency))
        self.peaklist.SetStringItem(index=self.currentItem, col=self.config.peaklistColNames['label'], 
                                         label=label)

        self.presenter.documentsDict[filename] = self.docs
        
    def onAnnotateTool(self, evt):
#         self.Bind(wx.EVT_MENU, self.presenter.onCalibrantRawDirectory, id=ID_addOneIon)
#         self.Bind(wx.EVT_MENU, self., id=ID_addManyIonsCSV)
       
        self.Bind(wx.EVT_MENU, self.presenter.onShowExtractedIons, id=ID_highlightRectAllIons)
        self.Bind(wx.EVT_MENU, self.onAssignChargeStates, id=ID_assignChargeStateIons)
        self.Bind(wx.EVT_MENU, self.onAssignChargeStates, id=ID_assignAlphaMaskIons)
        
        
        menu = wx.Menu()
        menu.Append(ID_assignChargeStateIons, "Assign charge state to selected ions")
        menu.Append(ID_assignAlphaMaskIons, "Assign mask/transparency value to selected ions")
        menu.Append(ID_highlightRectAllIons, "Highlight extracted items on MS plot")
        
#         menu.Append(ID_assignCmapIons, "Assign charge state to selected ions")
        
#         menu.Append(ID_ANY, "Annotate peaks")
#         menu.Append(ID_showAllIons, "Show all peaks for current document")
#         menu.Append(ID_showSelectedIons, "Show selected peaks for current document")
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()
        
    def onAddTool(self, evt):
        
        self.Bind(wx.EVT_MENU, self.presenter.onOpenPeakListCSV, id=ID_addManyIonsCSV)
        self.Bind(wx.EVT_MENU, self.onDuplicateIons, id=ID_duplicateIons)
        self.Bind(wx.EVT_MENU, self.presenter.onAddBlankDocument, id=ID_addNewOverlayDoc)
       
        menu = wx.Menu()
        menu.Append(ID_addManyIonsCSV, "Add list of ions (.csv/.txt)\tCtrl+L", 
                    help='Format: m/z, window size, charge')
        menu.AppendSeparator()
        menu.Append(ID_addNewOverlayDoc, "Add new comparison document\tAlt+D")
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
        
        
        menu = wx.Menu()
        menu.Append(ID_overlayMZfromList1D, "Overlay 1D (selected)")
        menu.Append(ID_overlayMZfromListRT, "Overlay RT (selected)")
        menu.Append(ID_overlayMZfromList, "Overlay 2D (selected)\tAlt+Q")
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
        menu.Append(ID_clearTableIons, "Clear table")
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
        
        self.Bind(wx.EVT_MENU, self.overrideCombine, id=ID_overrideCombinedMenu)
        self.Bind(wx.EVT_MENU, self.overrideCombine, id=ID_useInternalParamsCombinedMenu)
        
        menu = wx.Menu()
        menu.Append(ID_processSelectedIons, "Process selected ions")
        menu.Append(ID_processAllIons, "Process all ions")
        menu.AppendSeparator()
        self.override_check = menu.AppendCheckItem(ID_overrideCombinedMenu, "Override", 
                                                   help="Override already combined items with new settings")
        self.override_check.Check(self.override)
        self.useInternalParams_check = menu.AppendCheckItem(ID_useInternalParamsCombinedMenu, "Use internal parameters", 
                                                            help="When combining CVs, use ORIGAMI parameters pre-set for each item")
        self.useInternalParams_check.Check(self.useInternalParams)
        
        menu.Append(ID_combineCEscansSelectedIons, "Combine CVs for selected ions (ORIGAMI)")
        menu.Append(ID_combineCEscans, "Combine CVs for all ions (ORIGAMI)\tAlt+C")
        menu.AppendSeparator()
        menu.Append(ID_extractMSforCVs, "Extract MS for each CV (ORIGAMI)")


        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()
        
    def onRestrictCmaps(self, evt):
        """
        The cmap list will be restricted to more limited selection
        """

        currentCmap = self.colormap_value.GetValue()
        narrowList = self.config.narrowCmapList
        narrowList.append(self.colormap_value.GetValue())
        
        if self.restrictCmaps.GetValue():
            self.colormap_value.Clear()
            for item in narrowList:
                self.colormap_value.Append(item)
            self.colormap_value.SetStringSelection(currentCmap)
        else:
            self.colormap_value.Clear()
            for item in self.config.cmaps2:
                self.colormap_value.Append(item)
            self.colormap_value.SetStringSelection(currentCmap)
             
    def overrideCombine(self, evt):
        """ Check/uncheck menu item """
        
        if evt.GetId() == ID_overrideCombinedMenu:
            if self.override:
                self.override = False
                self.override_check.Check(False)
                self.config.overrideCombine = False
            else: 
                self.override = True
                self.override_check.Check(True)
                self.config.overrideCombine = True
            
        if evt.GetId() == ID_useInternalParamsCombinedMenu:
            if self.useInternalParams:
                self.useInternalParams = False
                self.useInternalParams_check.Check(False)
                self.config.useInternalParamsCombine = False
            else: 
                self.useInternalParams = True
                self.useInternalParams_check.Check(True)
                self.config.useInternalParamsCombine = True    
        
        if evt.GetId() == ID_processSaveMenu:
            if self.process:
                self.process = False
                self.processSave_check.Check(False)
            else: 
                self.process = True
                self.processSave_check.Check(True)

    def onAssignChargeStates(self, evt):
        """ Iterate over list to assign charge state """
        
        rows = self.peaklist.GetItemCount()
        if rows == 0: return
        
        if evt.GetId() == ID_assignChargeStateIons:
            value = dialogs.dlgAsk('Assign charge state to selected items.',
                                    defaultValue="")
            keyword = 'charge'
            if value == '' or value == 'None': return
            else:
                value = str2int(value)

        elif evt.GetId() == ID_assignAlphaMaskIons:
            value = dialogs.dlgAsk('Assign transparency or mask value to selected items. Typical values: Mask = 0.25 | Transparency = 0.5',
                                    defaultValue="")
            keyword = 'alpha'

            
        for row in range(rows):
            if self.peaklist.IsChecked(index=row):
                filename = self.peaklist.GetItem(row, self.config.peaklistColNames['filename']).GetText()
                
                document = self.presenter.documentsDict[filename]
                selectedText = self.getCurrentIon(index=row, evt=None)
                self.peaklist.SetStringItem(index=row,
                                            col=self.config.peaklistColNames[keyword], 
                                            label=str(value))
                
                if selectedText in document.IMS2Dions:
                    document.IMS2Dions[selectedText][keyword] = value
                if selectedText in document.IMS2DCombIons:
                    document.IMS2DCombIons[selectedText][keyword] = value
                if selectedText in document.IMS2DionsProcess:
                    document.IMS2DionsProcess[selectedText][keyword] = value
                if selectedText in document.IMSRTCombIons:
                    document.IMSRTCombIons[selectedText][keyword] = value
                
                self.presenter.documentsDict[document.title] = document

    def onSaveTool(self, evt):
        self.Bind(wx.EVT_MENU, self.OnSaveSelectedPeakList, id=ID_saveSelectIonListCSV)
        self.Bind(wx.EVT_MENU, self.OnSavePeakList, id=ID_saveIonListCSV)
        
        self.Bind(wx.EVT_MENU, self.onSaveAsData, id=ID_exportSeletedAsImage_ion)
        self.Bind(wx.EVT_MENU, self.onSaveAsData, id=ID_exportAllAsImage_ion)
        self.Bind(wx.EVT_MENU, self.onSaveAsData, id=ID_exportSelectedAsCSV_ion)
        self.Bind(wx.EVT_MENU, self.onSaveAsData, id=ID_exportAllAsCSV_ion)
        
        self.Bind(wx.EVT_MENU, self.overrideCombine, id=ID_processSaveMenu)
        
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
                
        if evt != None:
            evt.Skip()
        
    def OnRightClickMenu(self, evt):
 
        self.Bind(wx.EVT_MENU, self.OnListGetIMMS, id=ID_showMSplotIon)
        self.Bind(wx.EVT_MENU, self.OnListGetIMMS, id=ID_get1DplotIon)
        self.Bind(wx.EVT_MENU, self.OnListGetIMMS, id=ID_get2DplotIon)
        self.Bind(wx.EVT_MENU, self.OnListGetIMMS, id=ID_get2DplotIonWithProcss)

        self.Bind(wx.EVT_MENU, self.OnDeleteAll, id=ID_removeSelectedIonPopup)
        
        self.currentItem, flags = self.peaklist.HitTest(evt.GetPosition())
        self.menu = wx.Menu()
        self.menu.Append(ID_showMSplotIon, "Zoom in on the ion")
        self.menu.Append(ID_get1DplotIon, "Show 1D IM-MS plot")
        self.menu.Append(ID_get2DplotIon, "Show 2D IM-MS plot")
        self.menu.Append(ID_get2DplotIonWithProcss, "Process and show 2D IM-MS plot")
        self.menu.AppendSeparator()
#         self.menu.Append(ID_ANY, "Save to .csv file...")
#         self.menu.Append(ID_ANY, 'Save figure as .png (selected ion)')
        self.menu.Append(ID_removeSelectedIonPopup, "Remove item")
        self.PopupMenu(self.menu)
        self.menu.Destroy()
        self.SetFocus()
        
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
                if col==0 or col==1 or col==7:
                    itemData = str2num(item.GetText())
                    if itemData == None: itemData = 0
                    tempRow.append(itemData)
                elif col==2:
                    itemData = str2int(item.GetText())
                    if itemData == None: itemData = 0
                    tempRow.append(itemData)
                else:
                    tempRow.append(item.GetText())
            tempData.append(tempRow)
        
        # Remove duplicates
        tempData = self.presenter.removeDuplicates(input=tempData, 
                                                   columnsIn=self.config.peaklistColNames.keys(),
                                                   limitedCols=['start','end','filename'])     
        rows = len(tempData)
        self.peaklist.DeleteAllItems()
        for row in range(rows):
            self.peaklist.Append(tempData[row])
            
        if evt is None: return
        else:
            evt.Skip()
                  
    def OnListGetIMMS(self, evt):
        """
        This function extracts 2D array and plots it in 2D/3D
        """
        mzStart = self.peaklist.GetItem(self.currentItem,0).GetText()
        mzEnd = self.peaklist.GetItem(self.currentItem,1).GetText()
        rangeName = ''.join([str(mzStart),'-',str(mzEnd)])
        selectedItem = self.peaklist.GetItem(self.currentItem,5).GetText() # check filename
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
            if currentDocument.gotCombinedExtractedIons == True:
                data = currentDocument.IMS2DCombIons
            elif currentDocument.gotExtractedIons == True:
                data = currentDocument.IMS2Dions
        elif currentDocument.dataType == 'Type: MANUAL':
            if currentDocument.gotCombinedExtractedIons == True:
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
            startX = str2num(self.peaklist.GetItem(self.currentItem,0).GetText())-10
            endX = str2num(self.peaklist.GetItem(self.currentItem,1).GetText())+10
            try:
                endY = str2num(self.peaklist.GetItem(self.currentItem,7).GetText())/100
            except TypeError: endY = 1.001
            if endY == 0: endY = 1.001
            self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['MS'])
            self.presenter.onZoomMS(startX=startX,endX=endX, endY=endY)
        else:
            # Unpack data
            zvals, xvals, xlabel, yvals, ylabel, cmap = self.presenter.get2DdataFromDictionary(dictionary=data[rangeName],
                                                                                     dataType='plot',compact=False)
            
            # Warning in case  there is missing data
            if isempty(xvals) or isempty(yvals) or xvals is "" or yvals is "":
                msg1 = "Missing x- and/or y-axis labels. Cannot continue!"
                msg2 = "Add x- and/or y-axis labels to each file before continuing!"
                msg = '\n'.join([msg1,msg2])
                dialogs.dlgBox(exceptionTitle='Missing data', 
                               exceptionMsg= msg,
                               type="Error")
                return
            # Process data
            if evt.GetId() == ID_get2DplotIonWithProcss:
                zvals = self.presenter.process2Ddata(zvals=zvals)
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
                                 exceptionMsg= "Are you sure you would like to delete ALL text documents?",
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
            print(filepath)

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
         
        self.presenter.onPlotMS2(msX, msY, color, style, xlimits=xlimits)
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
            print(path)
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
        
        print(rows, duplicateWhich, docFrom, docTo)


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
        print(tempData)
        
        # Add to table
        for row in tempData:
            self.parent.peaklist.Append(row)
        # Remove duplicates
        self.parent.onRemoveDuplicates(evt=None)
        


        