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


# from origamiConfig import IconContainer as icons
from dialogs import panelRenameItem, panelAnnotatePeaks
from panelCompareMS import panelCompareMS
from ids import *
from panelInformation import panelDocumentInfo
from toolbox import str2num, saveAsText, convertRGB255to1, randomIntegerGenerator, randomColorGenerator, convertRGB1to255
from wx import ID_ANY
import dialogs as dialogs
import numpy as np
import pandas as pd
import re
import wx
import time
from massLynxFcns import normalize1D, subtractMS, textOpen2DIMSdata
from styles import makeMenuItem
from operator import itemgetter
import gc
import os

class panelDocuments ( wx.Panel ):
    """
    Make documents panel to store all information about open files
    """
    
    def __init__( self, parent, config, icons,  presenter ):
        wx.Panel.__init__ ( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, 
                            size = wx.Size( 250,-1 ), style = wx.TAB_TRAVERSAL )

        self.parent = parent
        self.config = config
        self.presenter = presenter
        self.icons = icons

               
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.topP = topPanel(self, self.parent, self.icons, self.presenter, self.config)
        self.sizer.Add(self.topP, 1, wx.EXPAND, 0)
        self.sizer.Fit(self)
        self.SetSizer(self.sizer)           
        
    def __del__( self ):
         pass

class documentsTree(wx.TreeCtrl):
    """
    Documents tree
    """
    
    def __init__(self, parent, mainParent, presenter, icons, config, id,  size=(-1,-1), 
                 style=wx.TR_TWIST_BUTTONS|wx.TR_HAS_BUTTONS | wx.TR_FULL_ROW_HIGHLIGHT):
        wx.TreeCtrl.__init__(self, parent, id, size=size, style=style)

        self.parent = parent
        self.mainParent = mainParent
        self.presenter = presenter
        self.icons = icons
        self.config = config
        
        self.itemType = None
        self.extractData = None
        self.itemData = None
        self.currentDocument = None
        self.indent = None
    
        # set font and colour
        self.SetFont(wx.SMALL_FONT)
        
        # init bullets
        self.bullets = wx.ImageList(13, 12)
        self.SetImageList(self.bullets)
        self._resetBullets()
        
        # add root
        root = self.AddRoot("Current documents")
        self.SetItemImage(root, 0, wx.TreeItemIcon_Normal)
        
        # Add bindings
        self.Bind(wx.EVT_TREE_KEY_DOWN, self.onKey, id=wx.ID_ANY)
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.enableCurrentDocument, id=wx.ID_ANY)
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.enableCurrentDocument, id=wx.ID_ANY)
        self.Bind(wx.EVT_TREE_ITEM_MENU, self.OnRightClickMenu, id=wx.ID_ANY)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnDoubleClick)
        
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.enableCurrentDocument, id=wx.ID_ANY)
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.onItemSelection, id=wx.ID_ANY)
        
    
        if self.config.quickDisplay:
            self.Bind(wx.EVT_TREE_SEL_CHANGED, self.onChangePlot, id=wx.ID_ANY)
                             
    def onKey(self, evt):
        """ Shortcut to navigate through Document Tree """
        # Intended use: deleting and selecting items
        # get key
        key = evt.GetKeyCode()

        # Delete item/document
        if key == 127:
            item = self.GetSelection()
            indent = self.getItemIndent(item)
            # Delete all documents
            if indent == 0:
                self.onDeleteAllDocuments(evt=None)
            # Delete single document
            elif indent == 1:
                self.removeDocument(evt=ID_removeDocument)
            else:
                self.onDeleteItem(evt=None)
        elif key == 80:
            if self.itemType in ['Drift time (2D)', 'Drift time (2D, processed)']:
                self.onProcess2D(evt=None)
            elif (self.itemType in ['Drift time (2D, EIC)', 'Drift time (2D, combined voltages, EIC)', 
                                    'Drift time (2D, processed, EIC)', 'Input data', 'Statistical'] and
                  self.extractData not in  ['Drift time (2D, EIC)', 'Drift time (2D, combined voltages, EIC)', 
                                            'Drift time (2D, processed, EIC)', 'Input data', 'Statistical']):
                self.onProcess2D(evt=None)
            elif (self.itemType in ['Mass Spectrum', 'Mass Spectrum (processed)', 'Mass Spectra'] and
                  self.extractData != 'Mass Spectra'):
                self.onProcessMS(evt=None)
         
    def OnDoubleClick(self, evt):
        
        tstart = time.clock()
        # Get selected item
        item = self.GetSelection()
        self.currentItem = item
        # Get the current text value for selected item
        itemType = self.GetItemText(item)
        if itemType == 'Current documents':
            menu = wx.Menu()
            menu.Append(ID_saveAllDocuments, 'Save all documents')
            menu.Append(ID_removeAllDocuments, 'Delete all documents')
            self.PopupMenu(menu) 
            menu.Destroy()
            self.SetFocus()
            return
        # Get indent level for selected item
        self.indent = self.getItemIndent(item)
        if self.indent > 1:
            extract = item # Specific Ion/file name
            item = self.getParentItem(item,2) # Item type
            itemType = self.GetItemText(item)
        else:
            extract = None

        # split
        try: self.splitText = re.split('-|,|:|__| \(', self.extractData)
        except: self.splitText = []
        # Get the ion/file name from deeper indent
        if extract == None: 
            self.extractData = None
            self.extractParent = None
        else: 
            self.extractParent = self.GetItemText(self.GetItemParent(extract))
            self.extractData = self.GetItemText(extract)
            
            
        try:            
            if self.itemType == 'UniDec':
                if self.indent == 2:
                    self.onShowUnidec(None)
                elif self.indent == 3 and self.extractParent != "Mass Spectra":
                    self.onShowUnidec(None, plot_type=self.extractData)
            elif "UniDec" in self.extractData or "UniDec" in self.extractParent:
                if self.indent == 3:
                    self.onShowUnidec(None)
                elif self.indent == 4:
                    self.onShowUnidec(None, plot_type=self.extractData)
            elif self.itemType == 'Mass Spectra' and self.extractData == 'Mass Spectra':
                self.onCompareMS(evt=None)
            elif self.itemType in ['Mass Spectrum', 'Mass Spectrum (processed)', 'Mass Spectra']:
                self.onShowPlot(evt=ID_showPlotDocument)
            elif self.itemType in ['Chromatogram', 'Chromatograms (EIC)']:
                self.onShowPlot(evt=None)
            elif self.itemType == 'Chromatograms (combined voltages, EIC)':
                self.onShowPlot(evt=None)
            elif self.itemType in ['Drift time (1D)', 'Drift time (1D, EIC, DT-IMS)', 'Drift time (1D, EIC)']:
                self.onShowPlot(evt=None)
            elif self.itemType in ['Drift time (2D)', 'Drift time (2D, processed)', 'Drift time (2D, EIC)',
                                   'Drift time (2D, combined voltages, EIC)', 'Drift time (2D, processed, EIC)',
                                   'Input data', 'Statistical', 'Overlay', 'DT/MS']:
                self.onShowPlot(evt=None)
            elif self.itemType == 'Sample information':
                self.onShowSampleInfo(evt=None)
            elif self.indent == 1:
                self.onOpenDocInfo(evt=None)
        except: pass
            
        tend = time.clock()
        print('It took: %s seconds.' % str(np.round((tend-tstart),4)))
        
    def onNotUseQuickDisplay(self, evt):
        """ 
        Function to either allow or disallow quick plotting selection of datasets
        """

        if self.config.quickDisplay:
            self.Bind(wx.EVT_TREE_SEL_CHANGED, self.onChangePlot, id=wx.ID_ANY)
        else:
            self.Unbind(wx.EVT_TREE_SEL_CHANGED, id=wx.ID_ANY)
                
        if evt != None:
            evt.Skip()
                             
    def _resetBullets(self):
        """Erase all bullets and make defaults."""
        self.bullets.RemoveAll()
        self.bullets.Add(self.icons.bulletsLib['bulletsDoc']) 
        self.bullets.Add(self.icons.bulletsLib['bulletsMS'])
        self.bullets.Add(self.icons.bulletsLib['bulletsDT'])
        self.bullets.Add(self.icons.bulletsLib['bulletsRT'])
        self.bullets.Add(self.icons.bulletsLib['bulletsDot'])
        self.bullets.Add(self.icons.bulletsLib['bulletsAnnot'])
        self.bullets.Add(self.icons.bulletsLib['bullets2DT'])
        self.bullets.Add(self.icons.bulletsLib['bulletsCalibration'])
        self.bullets.Add(self.icons.bulletsLib['bulletsOverlay'])
        
        self.bullets.Add(self.icons.bulletsLib['bulletsDocOn'])
        self.bullets.Add(self.icons.bulletsLib['bulletsMSIon'])
        self.bullets.Add(self.icons.bulletsLib['bulletsDTIon'])
        self.bullets.Add(self.icons.bulletsLib['bulletsRTIon'])
        self.bullets.Add(self.icons.bulletsLib['bulletsDotOn'])
        self.bullets.Add(self.icons.bulletsLib['bulletsAnnotIon'])
        self.bullets.Add(self.icons.bulletsLib['bullets2DTIon'])
        self.bullets.Add(self.icons.bulletsLib['bulletsCalibrationIon'])
        self.bullets.Add(self.icons.bulletsLib['bulletsOverlayIon'])
        
        self.bulets_dict = {'document':0, 'mass_spec':1, 'drift_time':2,
                            'rt':3, 'dots':4, 'annot':5, 'heatmap':6,
                            'calibration':7, 'overlay':8, 
                            'document_on':9, 'mass_spec_on':10, 'drift_time_on':11,
                            'rt_on':12, 'dots_on':13, 'annot_on':14, 'heatmap_on':15,
                            'calibration_on':16, 'overlay_on':17}
        
    def onGetItemData(self, dataType=None, evt=None):
        """
        This function retrieves data for currently selected item
        """
        if self.itemData == None:
            return
        
        # Get data
        if self.itemType == 'Drift time (2D)':
            data = self.itemData.IMS2D
        elif self.itemType == 'Drift time (2D, processed)':
            data = self.itemData.IMS2Dprocess
        elif self.itemType == 'Drift time (2D, EIC)':
            if self.extractData == 'Drift time (2D, EIC)': return
            data = self.itemData.IMS2Dions[self.extractData]
        elif self.itemType == 'Drift time (2D, combined voltages, EIC)':
            if self.extractData == 'Drift time (2D, combined voltages, EIC)': return
            data = self.itemData.IMS2DCombIons[self.extractData]
        elif self.itemType == 'Drift time (2D, processed, EIC)':
            if self.extractData == 'Drift time (2D, processed, EIC)': return
            data = self.itemData.IMS2DionsProcess[self.extractData]
        elif self.itemType == 'Input data':
            if self.extractData == 'Input data': return
            data = self.itemData.IMS2DcompData[self.extractData]
        elif self.itemType == 'Statistical':
            if self.extractData == 'Statistical': return
            data = self.itemData.IMS2DstatsData[self.extractData]
        elif self.itemType == 'Chromatograms (combined voltages, EIC)':
            if self.extractData == 'Chromatograms (combined voltages, EIC)': return
            data = self.itemData.IMSRTCombIons[self.extractData]
        elif self.itemType == 'Drift time (1D, EIC, DT-IMS)':
            if self.extractData == 'Drift time (1D, EIC, DT-IMS)': return
            data = self.itemData.IMS1DdriftTimes[self.extractData]
        elif self.itemType == 'Drift time (1D, EIC)':
            if self.extractData == 'Drift time (1D, EIC)': return
            data = self.itemData.multipleDT[self.extractData]


        
        # Retrieve dataType
        if dataType == 'charge':
            dataOut = data.get('charge', None)
        elif dataType == 'cmap':
            dataOut = data.get('cmap', self.config.currentCmap)
            
        # Return data
        return dataOut
         
    def checkCurrentXYlabels(self):
        """
        This function checks what is the current X/Y-axis label
        Its kind of dirty and needs to be improved in future!
        """
        
        # Select dataset
        if self.itemType == 'Drift time (2D)':
            data = self.itemData.IMS2D
        elif self.itemType == 'Drift time (2D, processed)':
            data = self.itemData.IMS2Dprocess
        elif self.itemType == 'Drift time (2D, EIC)':
            if self.extractData == 'Drift time (2D, EIC)': return None, None
            data = self.itemData.IMS2Dions[self.extractData]
        elif self.itemType == 'Drift time (2D, combined voltages, EIC)':
            if self.extractData == 'Drift time (2D, combined voltages, EIC)': return None, None
            data = self.itemData.IMS2DCombIons[self.extractData]
        elif self.itemType == 'Drift time (2D, processed, EIC)':
            if self.extractData == 'Drift time (2D, processed, EIC)': return None, None
            data = self.itemData.IMS2DionsProcess[self.extractData]
        elif self.itemType == 'Input data':
            if self.extractData == 'Input data': return None, None
            data = self.itemData.IMS2DcompData[self.extractData]
        
        # Get labels
        try:
            xlabel, ylabel = data['xlabels'], data['ylabels']
        
            if xlabel == 'Scans': idX = ID_xlabel2Dscans
            elif xlabel == 'Collision Voltage (V)': idX = ID_xlabel2DcolVolt
            elif xlabel == 'Activation Voltage (V)': idX = ID_xlabel2DactVolt
            elif xlabel == 'Lab Frame Energy (eV)': idX = ID_xlabel2DlabFrame
            elif xlabel == 'Activation Energy (eV)': idX = ID_xlabel2DactlabFrame
            elif xlabel == 'Mass-to-charge (Da)': idX = ID_xlabel2DmassToCharge
            elif xlabel == 'm/z (Da)': idX = ID_xlabel2Dmz
            elif xlabel == u'Wavenumber (cm⁻¹)': idX = ID_xlabel2Dwavenumber
            else: idX = ID_xlabel2Dscans
                
            if ylabel == 'Drift time (bins)': idY = ID_ylabel2Dbins
            elif ylabel == 'Drift time (ms)': idY = ID_ylabel2Dms
            elif ylabel == 'Arrival time (ms)': idY = ID_ylabel2Dms_arrival
            elif ylabel == u'Collision Cross Section (Å²)': idY = ID_ylabel2Dccs
            else:  idY = ID_ylabel2Dbins
            
            return idX, idY 
        except:
            return None, None
        
    def checkCurrentXYlabels1D(self):
        if self.itemType == 'Drift time (1D)':
            data = self.itemData.DT
            
        # Get labels
        xlabel = data['xlabels']
        
        if xlabel == 'Drift time (bins)': idX = ID_ylabel1Dbins
        elif xlabel == 'Drift time (ms)': idX = ID_ylabel1Dms
        elif xlabel == 'Arrival time (ms)': idX = ID_ylabel1Dms_arrival
        elif xlabel == u'Collision Cross Section (Å²)': idX = ID_ylabel1Dccs
        else:  idX = ID_ylabel2Dbins
        
        return idX
    
    def checkCurrentXYlabelsMSDT(self):
        if self.itemType == 'DT/MS':
            data = self.itemData.DTMZ
            
        # Get labels
        ylabel = data['ylabels']
        
        if ylabel == 'Drift time (bins)': idX = ID_ylabelDTMSbins
        elif ylabel == 'Drift time (ms)': idX = ID_ylabelDTMSms
        elif ylabel == 'Arrival time (ms)': idX = ID_ylabelDTMSms_arrival
        else:  idX = ID_ylabelDTMSbins
        
        return idX
    
    # def checkCurrentDataType(self):
        # """
        # This function checks what sort of dataset it is
        # """
        
        # if self.itemData.dataType == 'Type: ORIGAMI':
            # self.config.ciuMode = 'ORIGAMI'
        # elif self.itemData.dataType == 'Type: MANUAL':
            # self.config.ciuMode = 'MANUAL'
        # elif self.itemData.dataType == 'Type: Multifield Linear DT':
            # self.config.ciuMode = 'LinearDT'

        # if any([self.itemData.gotExtractedIons, self.itemData.got2DprocessIons, 
               # self.itemData.gotCombinedExtractedIonsRT, self.itemData.gotCombinedExtractedIons]):
            # self.config.extractMode = 'multipleIons'
        # else:
            # self.config.extractMode = 'singleIon'
        
        # return

    def onLoadInteractiveData(self, evt):
        """
        Load data into interactive document
        """
        
        # get document
        document = self.itemData
        evtID = evt.GetId()
        wildcard = "Text file (*.txt, *.csv, *.tab)| *.txt;*.csv;*.tab"
        dlg = wx.FileDialog(self.presenter.view, "Choose data [MS, RT, DT]...",
                            wildcard = wildcard,
                            style=wx.FD_MULTIPLE | wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            pathlist = dlg.GetPaths()
            filenames = dlg.GetFilenames()
            for path, fname in zip(pathlist, filenames):   
                if evtID == ID_docTree_add_MS_to_interactive:
                    msDataX, msDataY, dirname, xlimits = self.presenter.onMSTextFileFcn(path=path, return_data=True)
                    document.gotMultipleMS = True
                    document.multipleMassSpectrum[fname] = {'xvals':msDataX, 
                                                            'yvals':msDataY,
                                                            'xlabels':'m/z (Da)',
                                                            'xlimits':xlimits,
                                                            'file_path':path}
                elif evtID == ID_docTree_add_RT_to_interactive:
                    rtDataX, rtDataY, dirname, xlimits = self.presenter.onMSTextFileFcn(path=path, return_data=True)
                    document.gotMultipleRT = True
                    document.multipleRT[fname] = {'xvals':rtDataX, 
                                                  'yvals':rtDataY,
                                                  'xlabels':'Scans',
                                                  'ylabels':'Intensity',
                                                  'xlimits':xlimits,
                                                  'file_path':path}
                elif evtID == ID_docTree_add_DT_to_interactive:
                    dtDataX, dtDataY, dirname, xlimits = self.presenter.onMSTextFileFcn(path=path, return_data=True)
                    document.multipleDT[fname] = {'xvals':dtDataX, 
                                                  'yvals':dtDataY,
                                                  'xlabels':'Drift time (bins)',
                                                  'ylabels':'Intensity',
                                                  'xlimits':xlimits,
                                                  'file_path':path}
                    
                elif evtID == ID_docTree_add_2DT_to_interactive:
                    imsData2D, xAxisLabels, yAxisLabels = textOpen2DIMSdata(fileNameLocation=path, norm=False)
                    imsData1D = np.sum(imsData2D, axis=1).T
                    rtDataY = np.sum(imsData2D, axis=0)
                    color = convertRGB255to1(self.config.customColors[randomIntegerGenerator(0,15)])
                    document.gotExtractedIons = True
                    document.IMS2Dions[fname] = {'zvals':imsData2D,
                                                 'xvals':xAxisLabels,
                                                 'xlabels':'Scans',
                                                 'yvals':yAxisLabels,
                                                 'ylabels':'Drift time (bins)',
                                                 'yvals1D':imsData1D,
                                                 'yvalsRT':rtDataY,
                                                 'cmap':self.config.currentCmap,
                                                 'mask':self.config.overlay_defaultMask,
                                                 'alpha':self.config.overlay_defaultAlpha,
                                                 'min_threshold':0, 'max_threshold':1,
                                                 'color':color}
            
        dlg.Destroy()
            
        self.presenter.OnUpdateDocument(document, 'document')
            
    def onChangePlot(self, evt):
        
        # Get selected item
        item = self.GetSelection()
        self.currentItem = item
        # Get the current text value for selected item
        itemType = self.GetItemText(item)
        if itemType == 'Current documents':
            return
        
        # Get indent level for selected item
        indent = self.getItemIndent(item)
        if indent > 1:
            parent = self.getParentItem(item,1) # File name
            extract = item # Specific Ion/file name
            item = self.getParentItem(item,2) # Item type
            itemType = self.GetItemText(item)
        else:
            extract = None
            parent = item
        
        # Get the ion/file name from deeper indent
        if extract == None: pass
        else:
            self.extractData = self.GetItemText(extract)
            
        # Check item
        if not item:
            return      
        # Get item data for specified item
        self.itemData = self.GetPyData(parent)
        self.itemType = itemType
        
        self.onShowPlot(evt=None)
        
        if evt != None:
            evt.Skip()
        
    def onDeleteItem(self, evt):
        """
        Delete selected item from document
        ---
        This function is not efficient. At the moment, it deletes the item from
        document dictionary and then adds each document (and all children) 
        afterwards - we should be directly deleting an item AND then removing 
        the item from the dictionary
        """

        currentDoc = self.itemData.title
        document = self.presenter.documentsDict[currentDoc]
   
        # Check what is going to be deleted
        # MS
        if self.itemType == 'Mass Spectrum':
            del self.presenter.documentsDict[currentDoc].massSpectrum
            self.presenter.documentsDict[currentDoc].gotMS = False
            
        if self.itemType == 'Mass Spectrum (processed)':
            self.presenter.documentsDict[currentDoc].smoothMS = {}

        elif self.itemType == 'Mass Spectra':
            if self.extractData == 'Mass Spectra':
                self.presenter.documentsDict[currentDoc].multipleMassSpectrum = {}
                self.presenter.documentsDict[currentDoc].gotMultipleMS = False
            elif "UniDec" in self.extractParent and self.indent == 4:
                pass
            else:
                if "UniDec" in self.extractData:
                    del_item = re.split('UniDec \(', self.extractData)[1][:-1]
                    del self.presenter.documentsDict[currentDoc].multipleMassSpectrum[del_item]['unidec']
                    try: del self.presenter.documentsDict[currentDoc].multipleMassSpectrum[del_item]['temporary_unidec']
                    except: pass
                else:
                    del self.presenter.documentsDict[currentDoc].multipleMassSpectrum[self.extractData]
                if len(self.presenter.documentsDict[currentDoc].multipleMassSpectrum) == 0: 
                    self.presenter.documentsDict[currentDoc].gotMultipleMS = False
                    
        # MS/DT
        if self.itemType == 'DT/MS':
            del self.presenter.documentsDict[currentDoc].DTMZ
            self.presenter.documentsDict[currentDoc].gotDTMZ = False
            
        if self.itemType == "UniDec":
            del self.presenter.documentsDict[currentDoc].massSpectrum['unidec']
            try: del self.presenter.documentsDict[currentDoc].multipleMassSpectrum['temporary_unidec']
            except: pass
                            
        # DT
        elif self.itemType == 'Drift time (1D)':
            del self.presenter.documentsDict[currentDoc].DT
            self.presenter.documentsDict[currentDoc].got1DT = False
            
        elif self.itemType == 'Drift time (1D, EIC, DT-IMS)':
            if self.extractData == 'Drift time (1D, EIC, DT-IMS)':
                self.presenter.documentsDict[currentDoc].IMS1DdriftTimes = {}
                self.presenter.documentsDict[currentDoc].gotExtractedDriftTimes = False
            else:
                del self.presenter.documentsDict[currentDoc].IMS1DdriftTimes[self.extractData]
                if len(self.presenter.documentsDict[currentDoc].IMS1DdriftTimes) == 0: 
                    self.presenter.documentsDict[currentDoc].gotExtractedDriftTimes = False
        
        elif self.itemType == 'Drift time (1D, EIC)':
            if self.extractData == 'Drift time (1D, EIC)':
                self.presenter.documentsDict[currentDoc].multipleDT = {}
                self.presenter.documentsDict[currentDoc].gotMultipleDT = False
            else:
                del self.presenter.documentsDict[currentDoc].multipleDT[self.extractData]
                if len(self.presenter.documentsDict[currentDoc].multipleDT) == 0: 
                    self.presenter.documentsDict[currentDoc].gotMultipleDT = False
        
        # RT
        elif self.itemType == 'Chromatogram':
            del self.presenter.documentsDict[currentDoc].RT
            self.presenter.documentsDict[currentDoc].got1RT = False
            
        elif self.itemType == 'Chromatograms (combined voltages, EIC)':
            if self.extractData == 'Chromatograms (combined voltages, EIC)':
                self.presenter.documentsDict[currentDoc].IMSRTCombIons = {}
                self.presenter.documentsDict[currentDoc].gotCombinedExtractedIonsRT = False
            else:
                del self.presenter.documentsDict[currentDoc].IMSRTCombIons[self.extractData]
                if len(self.presenter.documentsDict[currentDoc].IMSRTCombIons) == 0: 
                    self.presenter.documentsDict[currentDoc].gotCombinedExtractedIonsRT = False
                    
        elif self.itemType == 'Chromatograms (EIC)':
            if self.extractData == 'Chromatograms (EIC)':
                self.presenter.documentsDict[currentDoc].multipleRT = {}
                self.presenter.documentsDict[currentDoc].gotMultipleRT = False
            else:
                del self.presenter.documentsDict[currentDoc].multipleRT[self.extractData]
                if len(self.presenter.documentsDict[currentDoc].multipleRT) == 0: 
                    self.presenter.documentsDict[currentDoc].gotMultipleRT = False
            
        # 2D
        elif self.itemType == 'Drift time (2D)':
            self.presenter.documentsDict[currentDoc].IMS2D = {}
            self.presenter.documentsDict[currentDoc].got2DIMS = False
            
        elif self.itemType == 'Drift time (2D, processed)':
            self.presenter.documentsDict[currentDoc].IMS2Dprocess = {}
            self.presenter.documentsDict[currentDoc].got2Dprocess = False
            
        elif self.itemType == 'Drift time (2D, EIC)':
            if self.extractData == 'Drift time (2D, EIC)':
                self.presenter.documentsDict[currentDoc].IMS2Dions = {}
                self.presenter.documentsDict[currentDoc].gotExtractedIons = False
            else:
                del self.presenter.documentsDict[currentDoc].IMS2Dions[self.extractData]
                if len(self.presenter.documentsDict[currentDoc].IMS2Dions) == 0: 
                    self.presenter.documentsDict[currentDoc].gotExtractedIons = False
                
        elif self.itemType == 'Drift time (2D, combined voltages, EIC)':
            if self.extractData == 'Drift time (2D, combined voltages, EIC)':
                self.presenter.documentsDict[currentDoc].IMS2DCombIons = {}
                self.presenter.documentsDict[currentDoc].gotCombinedExtractedIons = False
            else:
                del self.presenter.documentsDict[currentDoc].IMS2DCombIons[self.extractData]
                if len(self.presenter.documentsDict[currentDoc].IMS2DCombIons) == 0: 
                    self.presenter.documentsDict[currentDoc].gotCombinedExtractedIons = False
                
        elif self.itemType == 'Drift time (2D, processed, EIC)': 
            if self.extractData == 'Drift time (2D, processed, EIC)':
                self.presenter.documentsDict[currentDoc].IMS2DionsProcess = {}
                self.presenter.documentsDict[currentDoc].got2DprocessIons = False
            else:
                del self.presenter.documentsDict[currentDoc].IMS2DionsProcess[self.extractData]
                if len(self.presenter.documentsDict[currentDoc].IMS2DionsProcess) == 0: 
                    self.presenter.documentsDict[currentDoc].got2DprocessIons = False
                 
        elif self.itemType == 'Input data': 
            if self.extractData == 'Input data': 
                self.presenter.documentsDict[currentDoc].IMS2DcompData = {}
                self.presenter.documentsDict[currentDoc].gotComparisonData = False
            else:
                del self.presenter.documentsDict[currentDoc].IMS2DcompData[self.extractData]
                if len(self.presenter.documentsDict[currentDoc].IMS2DcompData) == 0: 
                    self.presenter.documentsDict[currentDoc].gotComparisonData = False
                
        elif self.itemType == 'Statistical': 
            if self.extractData == 'Statistical': 
                self.presenter.documentsDict[currentDoc].IMS2DstatsData = {}
                self.presenter.documentsDict[currentDoc].gotStatsData = False
            else:
                del self.presenter.documentsDict[currentDoc].IMS2DstatsData[self.extractData]
                if len(self.presenter.documentsDict[currentDoc].IMS2DstatsData) == 0: 
                    self.presenter.documentsDict[currentDoc].gotStatsData = False
        
        elif self.itemType == 'Overlay': 
            if self.extractData == 'Overlay': 
                self.presenter.documentsDict[currentDoc].IMS2DoverlayData = {}
                self.presenter.documentsDict[currentDoc].gotOverlay = False
            else:
                del self.presenter.documentsDict[currentDoc].IMS2DoverlayData[self.extractData]
                if len(self.presenter.documentsDict[currentDoc].IMS2DoverlayData) == 0: 
                    self.presenter.documentsDict[currentDoc].gotOverlay = False
                    
        # Calibration
        elif self.itemType == 'Calibration peaks': 
            if self.extractData == 'Calibration peaks':
                self.presenter.documentsDict[currentDoc].calibration = {}
                self.presenter.documentsDict[currentDoc].gotCalibration = False
            else:
                del self.presenter.documentsDict[currentDoc].calibration[self.extractData]
                if len(self.presenter.documentsDict[currentDoc].calibration) == 0: 
                    self.presenter.documentsDict[currentDoc].gotCalibration = False
        
        elif self.itemType == 'Calibrants': 
            if self.extractData == 'Calibrants':
                self.presenter.documentsDict[currentDoc].calibrationDataset = {}
                self.presenter.documentsDict[currentDoc].gotCalibrationDataset = False
            else:
                del self.presenter.documentsDict[currentDoc].calibrationDataset[self.extractData]
                if len(self.presenter.documentsDict[currentDoc].calibrationDataset) == 0: 
                    self.presenter.documentsDict[currentDoc].gotCalibrationDataset = False
                                
        # Add modified document to the dictionary
        self.presenter.documentsDict[currentDoc] = document
            
        # Update documents tree
        self.addDocument(docData = document)
        
        # Expand item
        
    def onDeleteAllDocuments(self, evt):
        """ Alternative function to delete documents """
        
        dlg = dialogs.dlgBox(exceptionTitle='Are you sure?', 
                             exceptionMsg= ''.join(["Are you sure you would like to delete ALL documents?"]),
                             type="Question")
        if dlg == wx.ID_NO:
            msg = 'Cancelled operation'
            self.presenter.view.SetStatusText(msg, 3)
            return
        else:
            self.presenter.onClearAllPlots()
            doc_keys = self.presenter.documentsDict.keys()
            for document in doc_keys:
                try:
                    self.removeDocument(evt=None, 
                                        deleteItem=document,
                                        ask_permission=False)
                except:
                    pass
          
    def onItemSelection(self, evt):
        # Get selected item
        item = self.GetSelection()     
        self.currentItem = item
        
        # Get the current text value for selected item
        itemType = self.GetItemText(item)
        
        # Get indent level for selected item
        self.indent = self.getItemIndent(item)
        if self.indent > 1:
            parent = self.getParentItem(item,1) # File name
            extract = item # Specific Ion/file name
            item = self.getParentItem(item,2) # Item type
            itemType = self.GetItemText(item)
        else:
            extract = None
            parent = item
        
        # Get the ion/file name from deeper indent
        if extract == None: 
            self.extractData = None
            pass
        else:
            self.extractData = self.GetItemText(extract)
            
        # Check item
        if not item:
            return      
        # Get item data for specified item
        self.itemData = self.GetPyData(parent)
        self.itemType = itemType
        
        if evt != None:
            evt.Skip()
          
    def onAddAnnotation(self, evt):
        data = self.GetPyData(self.currentItem)
        if "annotations" in data:
            annotations = data['annotations']
        else:
            annotations = {}
            
        kwargs = {"document":self.itemData.title,
                  "dataset":self.extractData,
                  "data":np.transpose([data["xvals"], data["yvals"]]),
                  "annotations":annotations}
        self.annotateDlg = panelAnnotatePeaks(self.parent, self, self.config, 
                                              self.icons, **kwargs)
        self.annotateDlg.Show()
        
    def onUpdateAnotations(self, annotations, document, dataset):
        document = self.presenter.documentsDict[document]
        if dataset == "Mass Spectrum":
            document.massSpectrum['annotations'] = annotations
        else: 
            document.multipleMassSpectrum[dataset]['annotations'] = annotations
        
        self.presenter.OnUpdateDocument(document, 'document')        
          
    def OnRightClickMenu(self, evt):
        """ Create and show up popup menu"""
        
        # Make some bindings
        self.Bind(wx.EVT_MENU, self.presenter.onSaveDocument, id=ID_saveAllDocuments)
        self.Bind(wx.EVT_MENU, self.onDeleteAllDocuments, id=ID_removeAllDocuments)
        
        # Get selected item
        item = self.GetSelection()
        self.currentItem = item
        # Get the current text value for selected item
        itemType = self.GetItemText(item)
        if itemType == 'Current documents':
            menu = wx.Menu()
            menu.Append(ID_saveAllDocuments, 'Save all documents')
            menu.Append(ID_removeAllDocuments, 'Delete all documents')
            self.PopupMenu(menu) 
            menu.Destroy()
            self.SetFocus()
            return
        # Get indent level for selected item
        self.indent = self.getItemIndent(item)
        if self.indent > 1:
            parent = self.getParentItem(item,1) # File name
            extract = item # Specific Ion/file name
            item = self.getParentItem(item,2) # Item type
            itemType = self.GetItemText(item)
        else:
            extract = None
            parent = item
        
        # Get the ion/file name from deeper indent
        if extract == None: 
            self.extractData = None
            self.extractParent = None
        else: 
            self.extractParent = self.GetItemText(self.GetItemParent(extract))
            self.extractData = self.GetItemText(extract)
            
        # split
        try:
            self.splitText = re.split('-|,|:|__', self.extractData)
        except:
            self.splitText = []
            
        # Check item
        if not item:
            return      
        
        # Get item data for specified item
        self.itemData = self.GetPyData(parent)
        self.itemType = itemType
        try:
            self.currentData = self.GetPyData(self.currentItem)
        except:
            self.currentData = None
        
        
        print('item: %s | extractParent: %s | extract: %s | indent: %s' % (self.itemType, self.extractParent, 
                                                                           self.extractData, self.indent)) 

        
        # Check current data types
#         self.checkCurrentDataType()
        
        # Change x-axis label (2D)
        xlabel2DMenu = wx.Menu()
        xlabel2DMenu.Append(ID_xlabel2Dscans, 'Scans', "",wx.ITEM_RADIO)
        xlabel2DMenu.Append(ID_xlabel2DcolVolt, 'Collision Voltage (V)',"",wx.ITEM_RADIO)
        xlabel2DMenu.Append(ID_xlabel2DactVolt, 'Activation Energy (V)',"",wx.ITEM_RADIO)
        xlabel2DMenu.Append(ID_xlabel2DlabFrame, 'Lab Frame Energy (eV)',"",wx.ITEM_RADIO)
        xlabel2DMenu.Append(ID_xlabel2DactlabFrame, 'Activation Energy (eV)',"",wx.ITEM_RADIO)
        xlabel2DMenu.Append(ID_xlabel2DmassToCharge, 'Mass-to-charge (Da)',"",wx.ITEM_RADIO)
        xlabel2DMenu.Append(ID_xlabel2Dmz, 'm/z (Da)',"",wx.ITEM_RADIO)
        xlabel2DMenu.Append(ID_xlabel2Dwavenumber, u'Wavenumber (cm⁻¹)',"",wx.ITEM_RADIO)
        xlabel2DMenu.AppendSeparator()
        xlabel2DMenu.Append(ID_xlabel2Drestore, 'Restore default', "")
        
        # Change y-axis label (2D)
        ylabel2DMenu = wx.Menu()
        ylabel2DMenu.Append(ID_ylabel2Dbins, 'Drift time (bins)',"",wx.ITEM_RADIO)
        ylabel2DMenu.Append(ID_ylabel2Dms, 'Drift time (ms)',"",wx.ITEM_RADIO)
        ylabel2DMenu.Append(ID_ylabel2Dms_arrival, 'Arrival time (ms)',"",wx.ITEM_RADIO)
        ylabel2DMenu.Append(ID_ylabel2Dccs, u'Collision Cross Section (Å²)',"",wx.ITEM_RADIO)
        ylabel2DMenu.AppendSeparator()
        ylabel2DMenu.Append(ID_ylabel2Drestore, 'Restore default', "")
        
        # Check xy axis labels
        if any(self.itemType in itemType for itemType in ['Drift time (2D)', 'Drift time (2D, processed)',
                                                          'Drift time (2D, EIC)',
                                                          'Drift time (2D, combined voltages, EIC)',
                                                          'Drift time (2D, processed, EIC)',
                                                          'Input data']):
            # Check if right click was performed on a header of a sub-tree
            if any(self.extractData in itemType for itemType in ['Drift time (2D, EIC)',
                                                                 'Drift time (2D, combined voltages, EIC)',
                                                                 'Drift time (2D, processed, EIC)',
                                                                 'Input data']):
                pass
                
            # Check what is the current label for this particular dataset
            try:
                idX, idY = self.checkCurrentXYlabels()
            except UnboundLocalError: 
                return
            if idX == ID_xlabel2Dscans: xlabel2DMenu.Check(ID_xlabel2Dscans, True)
            elif idX == ID_xlabel2DcolVolt: xlabel2DMenu.Check(ID_xlabel2DcolVolt, True)
            elif idX == ID_xlabel2DactVolt: xlabel2DMenu.Check(ID_xlabel2DactVolt, True)
            elif idX == ID_xlabel2DlabFrame: xlabel2DMenu.Check(ID_xlabel2DlabFrame, True)
            elif idX == ID_xlabel2DactlabFrame: xlabel2DMenu.Check(ID_xlabel2DactlabFrame, True)
            elif idX == ID_xlabel2DmassToCharge: xlabel2DMenu.Check(ID_xlabel2DmassToCharge, True)
            elif idX == ID_xlabel2Dmz: xlabel2DMenu.Check(ID_xlabel2Dmz, True)
            elif idX == ID_xlabel2Dwavenumber: xlabel2DMenu.Check(ID_xlabel2Dwavenumber, True)
            else: xlabel2DMenu.Check(ID_xlabel2Dscans, True)

            if idY == ID_ylabel2Dbins: ylabel2DMenu.Check(ID_ylabel2Dbins, True)
            elif idY == ID_ylabel2Dms: ylabel2DMenu.Check(ID_ylabel2Dms, True)
            elif idY == ID_ylabel2Dms_arrival: ylabel2DMenu.Check(ID_ylabel2Dms_arrival, True)
            elif idY == ID_ylabel2Dccs: ylabel2DMenu.Check(ID_ylabel2Dccs, True)
            else: ylabel2DMenu.Check(ID_ylabel2Dbins, True)

        # Change x-axis label (1D)
        xlabel1DMenu = wx.Menu()
        xlabel1DMenu.Append(ID_ylabel1Dbins, 'Drift time (bins)',"",wx.ITEM_RADIO)
        xlabel1DMenu.Append(ID_ylabel1Dms, 'Drift time (ms)',"",wx.ITEM_RADIO)
        xlabel1DMenu.Append(ID_ylabel1Dms_arrival, 'Arrival time (ms)',"",wx.ITEM_RADIO)
        xlabel1DMenu.Append(ID_ylabel1Dccs, u'Collision Cross Section (Å²)',"",wx.ITEM_RADIO)
        
        if self.itemType == 'Drift time (1D)':
            try: idX = self.checkCurrentXYlabels1D()
            except UnboundLocalError: return
            
            if idX == ID_ylabel1Dbins: xlabel1DMenu.Check(ID_ylabel1Dbins, True)
            elif idX == ID_ylabel1Dms: xlabel1DMenu.Check(ID_ylabel1Dms, True)
            elif idX == ID_ylabel1Dms: ID_ylabel1Dms_arrival.Check(ID_ylabel1Dms_arrival, True)
            elif idX == ID_ylabel1Dccs: xlabel1DMenu.Check(ID_ylabel1Dccs, True)
            else: xlabel1DMenu.Check(ID_ylabel1Dbins, True)
                
        
        # change y-axis label (DT/MS)
        ylabelDTMSMenu = wx.Menu()
        ylabelDTMSMenu.Append(ID_ylabelDTMSbins, 'Drift time (bins)',"",wx.ITEM_RADIO)
        ylabelDTMSMenu.Append(ID_ylabelDTMSms, 'Drift time (ms)',"",wx.ITEM_RADIO)
        ylabelDTMSMenu.Append(ID_ylabelDTMSms_arrival, 'Arrival time (ms)',"",wx.ITEM_RADIO)
        ylabelDTMSMenu.AppendSeparator()
        ylabelDTMSMenu.Append(ID_ylabelDTMSrestore, 'Restore default', "")
        
        if self.itemType == 'DT/MS':
            try: idX = self.checkCurrentXYlabelsMSDT()
            except UnboundLocalError: return
            
            if idX == ID_ylabelDTMSbins: ylabelDTMSMenu.Check(ID_ylabelDTMSbins, True)
            elif idX == ID_ylabelDTMSms: ylabelDTMSMenu.Check(ID_ylabelDTMSms, True)
            elif idX == ID_ylabelDTMSms_arrival: ylabelDTMSMenu.Check(ID_ylabelDTMSms_arrival, True)
            else: xlabel1DMenu.Check(ID_ylabelDTMSbins, True)
        
        
        # Save as interactive Bokeh figures
        bokehSaveMenu = wx.Menu()
        bokehSaveMenu.Append(ID_save2DhtmlDocumentImage, 'Save and open figure as interactive .html (image)')
        bokehSaveMenu.Append(ID_save2DhtmlDocumentHeatmap, 'Save and open figure as interactive .html (heatmap)')

    # Bind events
        self.Bind(wx.EVT_MENU, self.onShowPlot, id=ID_showPlotDocument)
        self.Bind(wx.EVT_MENU, self.onShowPlot, id=ID_showPlot1DDocument)
        self.Bind(wx.EVT_MENU, self.onShowPlot, id=ID_showPlotRTDocument)
        self.Bind(wx.EVT_MENU, self.onShowPlot, id=ID_showPlotMSDocument)
        self.Bind(wx.EVT_MENU, self.presenter.onSmooth1Ddata, id=ID_smooth1DdataMS)
        self.Bind(wx.EVT_MENU, self.presenter.onPickPeaks, id=ID_pickMSpeaksDocument)
        self.Bind(wx.EVT_MENU, self.onProcess, id=ID_process2DDocument)    
        self.Bind(wx.EVT_MENU, self.presenter.onDocumentColour, id=ID_getNewColour)
        self.Bind(wx.EVT_MENU, self.presenter.onChangeChargeState, id=ID_assignChargeState)
        self.Bind(wx.EVT_MENU, self.onGoToDirectory, id=ID_goToDirectory)
        self.Bind(wx.EVT_MENU, self.onSaveCSV, id=ID_saveDataCSVDocument)
        self.Bind(wx.EVT_MENU, self.onSaveCSV, id=ID_saveDataCSVDocument1D)
        self.Bind(wx.EVT_MENU, self.onSaveCSV, id=ID_saveAsDataCSVDocument)
        self.Bind(wx.EVT_MENU, self.onSaveCSV, id=ID_saveAsDataCSVDocument1D) 
        self.Bind(wx.EVT_MENU, self.onSaveHTML, id=ID_save2DhtmlDocumentImage)
        self.Bind(wx.EVT_MENU, self.onSaveHTML, id=ID_save2DhtmlDocumentHeatmap)
        self.Bind(wx.EVT_MENU, self.onRenameItem, id=ID_renameItem)
        self.Bind(wx.EVT_MENU, self.onDuplicateItem, id=ID_duplicateItem)
        self.Bind(wx.EVT_MENU, self.presenter.saveCCScalibrationToPickle, id=ID_saveDataCCSCalibrantDocument)
#         self.Bind(wx.EVT_MENU, self.onAddToCCSTable, id=ID_add2CCStable1DDocument)
        self.Bind(wx.EVT_MENU, self.onAddToCCSTable, id=ID_add2CCStable2DDocument)
        self.Bind(wx.EVT_MENU, self.presenter.onSaveDocument, id=ID_saveDocument)
        self.Bind(wx.EVT_MENU, self.onShowSampleInfo, id=ID_showSampleInfo)
        self.Bind(wx.EVT_MENU, self.onSaveImage, id=ID_saveImageDocument)
        self.Bind(wx.EVT_MENU, self.mainParent.openSaveAsDlg, id=ID_saveAsInteractive)
        self.Bind(wx.EVT_MENU, self.presenter.restoreComparisonToList, id=ID_restoreComparisonData)
        
        self.Bind(wx.EVT_MENU, self.onCompareMS, id=ID_docTree_compareMS)
        self.Bind(wx.EVT_MENU, self.onShowMassSpectra, id=ID_docTree_showMassSpectra)
        self.Bind(wx.EVT_MENU, self.onProcessMS, id=ID_docTree_processMS)
        self.Bind(wx.EVT_MENU, self.onProcess2D, id=ID_docTree_process2D)
        self.Bind(wx.EVT_MENU, self.presenter.onReExtractDTMS, id=ID_docTree_extractDTMS)
        self.Bind(wx.EVT_MENU, self.onProcessMS, id=ID_docTree_UniDec)
        self.Bind(wx.EVT_MENU, self.onAddToTable, id=ID_docTree_addToMMLTable)
        self.Bind(wx.EVT_MENU, self.onAddToTable, id=ID_docTree_addOneToMMLTable)
        self.Bind(wx.EVT_MENU, self.onAddToTable, id=ID_docTree_addToTextTable)
        self.Bind(wx.EVT_MENU, self.onAddToTable, id=ID_docTree_addOneToTextTable)
        
        self.Bind(wx.EVT_MENU, self.onAddToTable, id=ID_docTree_addInteractiveToTextTable)
        self.Bind(wx.EVT_MENU, self.onAddToTable, id=ID_docTree_addOneInteractiveToTextTable)
        self.Bind(wx.EVT_MENU, self.onAddAnnotation, id=ID_docTree_add_annotations)
        
        # Change axis labels
        for xID in [ID_xlabel2Dscans, ID_xlabel2DcolVolt, ID_xlabel2DactVolt,
                    ID_xlabel2DlabFrame, ID_xlabel2DactlabFrame,ID_xlabel2DmassToCharge, 
                    ID_xlabel2Dmz, ID_xlabel2Dwavenumber, ID_xlabel2Drestore]:
            self.Bind(wx.EVT_MENU, self.presenter.onUpdateXYaxisLabels, id=xID)
            
        for yID in [ID_ylabel2Dbins, ID_ylabel2Dms, ID_ylabel2Dms_arrival,
                    ID_ylabel2Dccs, ID_ylabel2Drestore]:
            self.Bind(wx.EVT_MENU, self.presenter.onUpdateXYaxisLabels, id=yID)
        # 1D
        for yID in [ID_ylabel1Dbins, ID_ylabel1Dms, ID_ylabel1Dms_arrival,
                    ID_ylabel1Dccs]:
            self.Bind(wx.EVT_MENU, self.presenter.onUpdateXYaxisLabels, id=yID)
        # DT/MS
        for yID in [ID_ylabelDTMSbins, ID_ylabelDTMSms, ID_ylabelDTMSms_arrival, 
                    ID_ylabelDTMSrestore]:
            self.Bind(wx.EVT_MENU, self.presenter.onUpdateXYaxisLabels, id=yID)
        
        # Remove document
        self.Bind(wx.EVT_MENU, self.onDeleteItem, id=ID_removeItemDocument)
        self.Bind(wx.EVT_MENU, self.removeDocument, id=ID_removeDocument)
        self.Bind(wx.EVT_MENU, self.onOpenDocInfo, id=ID_openDocInfo)   

        # Save images
        self.Bind(wx.EVT_MENU, self.onShow_and_SavePlot, id=ID_saveMSImageDoc)
        self.Bind(wx.EVT_MENU, self.onShow_and_SavePlot, id=ID_saveRTImageDoc)
        self.Bind(wx.EVT_MENU, self.onShow_and_SavePlot, id=ID_save1DImageDoc)
        self.Bind(wx.EVT_MENU, self.onShow_and_SavePlot, id=ID_save2DImageDoc)
        self.Bind(wx.EVT_MENU, self.onShow_and_SavePlot, id=ID_saveMZDTImage)
        self.Bind(wx.EVT_MENU, self.onShow_and_SavePlot, id=ID_save3DImageDoc)
        self.Bind(wx.EVT_MENU, self.onShow_and_SavePlot, id=ID_saveRMSDImageDoc)
        self.Bind(wx.EVT_MENU, self.onShow_and_SavePlot, id=ID_saveRMSFImageDoc)
        self.Bind(wx.EVT_MENU, self.onShow_and_SavePlot, id=ID_saveOverlayImageDoc)
        self.Bind(wx.EVT_MENU, self.onShow_and_SavePlot, id=ID_saveWaterfallImageDoc)
        self.Bind(wx.EVT_MENU, self.onShow_and_SavePlot, id=ID_saveRMSDmatrixImageDoc)
        
        self.Bind(wx.EVT_MENU, self.onLoadInteractiveData, id=ID_docTree_add_MS_to_interactive)
        self.Bind(wx.EVT_MENU, self.onLoadInteractiveData, id=ID_docTree_add_RT_to_interactive)
        self.Bind(wx.EVT_MENU, self.onLoadInteractiveData, id=ID_docTree_add_DT_to_interactive)
        self.Bind(wx.EVT_MENU, self.onLoadInteractiveData, id=ID_docTree_add_2DT_to_interactive)
        
        self.Bind(wx.EVT_MENU, self.onSaveDF, id=ID_saveData_csv)
        self.Bind(wx.EVT_MENU, self.onSaveDF, id=ID_saveData_pickle)
        self.Bind(wx.EVT_MENU, self.onSaveDF, id=ID_saveData_excel)
        self.Bind(wx.EVT_MENU, self.onSaveDF, id=ID_saveData_hdf)
        
        self.Bind(wx.EVT_MENU, self.onShowUnidec, id=ID_docTree_show_unidec)
        self.Bind(wx.EVT_MENU, self.onSaveUnidec, id=ID_docTree_save_unidec)
        
        
        
        # save dataframe
        saveDFSubMenu = wx.Menu()
        saveDFSubMenu.Append(ID_saveData_csv, 'Save to .csv file')
        saveDFSubMenu.Append(ID_saveData_pickle, 'Save to .pickle file')
        saveDFSubMenu.Append(ID_saveData_hdf, 'Save to .hdf file (slow)')
        saveDFSubMenu.Append(ID_saveData_excel, 'Save to .excel file (v. slow)')
        
        saveImageLabel = ''.join(['Save figure (.', self.config.imageFormat,')'])
        saveImageLabelAll = ''.join(['Save figures (.', self.config.imageFormat,')'])
        saveCSVLabel = ''.join(['Save data (',  self.config.saveExtension, ')\tAlt+V'])
        saveCSVLabel1D = ''.join(['Save data (1D, ',  self.config.saveExtension, ')'])
        saveCSVLabel2D = ''.join(['Save data (2D, ',  self.config.saveExtension, ')'])
        
        # Get label
        if self.extractData != None:
            try:
                plotLabel = self.extractData.split(':')
            except AttributeError: pass 
        
        menu = wx.Menu()
        if self.itemData.dataType == 'Type: Interactive':
            if (self.itemType in ['Drift time (2D)', 'Drift time (2D, processed)']
                or (self.itemType == 'Drift time (2D, EIC)' and self.extractData != self.itemType)
                ):
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_showPlotDocument,
                                             text='Show heatmap\tAlt+S', 
                                             bitmap=self.icons.iconsLib['heatmap_16']))
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_process2D,
                                             text='Process...\tP', 
                                             bitmap=self.icons.iconsLib['process_2d_16']))
                menu.AppendSeparator()
#                 menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_addInteractiveToTextTable,
#                                              text='Add to text file table', 
#                                              bitmap=None))    
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_assignChargeState,
                                         text='Assign a charge state...\tAlt+Z', 
                                         bitmap=self.icons.iconsLib['assign_charge_16']))
                menu.AppendMenu(ID_ANY, 'Set X-axis label as...', xlabel2DMenu)
                menu.AppendMenu(ID_ANY, 'Set Y-axis label as...', ylabel2DMenu)
                menu.AppendSeparator()
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_save2DImageDoc,
                                         text=saveImageLabel, 
                                         bitmap=self.icons.iconsLib['file_png_16']))
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveDataCSVDocument1D,
                                         text=saveCSVLabel1D, 
                                         bitmap=self.icons.iconsLib['file_csv_16']))         
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveDataCSVDocument,
                                         text=saveCSVLabel2D, 
                                         bitmap=self.icons.iconsLib['file_csv_16']))                
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_removeItemDocument,
                                             text='Delete item\tDelete', 
                                             bitmap=self.icons.iconsLib['clear_16']))
                if not any(itemType in type for type in ['Drift time (2D)', 
                                                         'Drift time (2D, processed)']):
                    menu.PrependItem(makeMenuItem(parent=menu, id=ID_showPlot1DDocument,
                                              text='Show mobiligram', 
                                              bitmap=self.icons.iconsLib['mobiligram_16']))
                    menu.PrependItem(makeMenuItem(parent=menu, id=ID_showPlotRTDocument,
                                              text='Show chromatogram', 
                                              bitmap=self.icons.iconsLib['chromatogram_16']))
            elif self.itemType == 'Drift time (2D, EIC)' and self.extractData == self.itemType:
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_addInteractiveToTextTable,
                                             text='Add to text file table', 
                                             bitmap=None))    
            elif (itemType == 'Mass Spectrum' or 
                  itemType == 'Mass Spectra' or 
                  itemType == 'Mass Spectrum (processed)'):
                if self.itemType == 'Mass Spectrum' or itemType == 'Mass Spectrum (processed)':
                    menu.AppendItem(makeMenuItem(parent=menu, id=ID_showPlotDocument,
                                                 text='Show mass spectrum\tAlt+S', 
                                                 bitmap=self.icons.iconsLib['mass_spectrum_16']))
                    menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_add_annotations,
                                                 text='Add annotation...', 
                                                 bitmap=self.icons.iconsLib['annotate16']))
                    # check if deconvolution results exist
                    if 'unidec' in self.currentData:
                        menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_show_unidec, 
                                                 text='Show UniDec results', 
                                                 bitmap=None))
                        menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_save_unidec, 
                                                 text='Save UniDec results ({})'.format(self.config.saveExtension), 
                                                 bitmap=None))
                    menu.AppendSeparator()                
                    menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_processMS,
                                                 text='Process...\tP', 
                                                 bitmap=self.icons.iconsLib['process_ms_16']))
                    menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_UniDec,
                                                 text='Deconvolute using UniDec...', 
                                                 bitmap=self.icons.iconsLib['process_unidec_16']))
                    menu.AppendSeparator()
                    menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveMSImageDoc,
                                             text=saveImageLabel, 
                                             bitmap=self.icons.iconsLib['file_png_16']))
                    menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveDataCSVDocument,
                                             text=saveCSVLabel, 
                                             bitmap=self.icons.iconsLib['file_csv_16']))
                    menu.AppendItem(makeMenuItem(parent=menu, id=ID_removeItemDocument,
                                                 text='Delete item\tDelete', 
                                                 bitmap=self.icons.iconsLib['clear_16']))
                else:
                    if self.extractData == 'Mass Spectra':
                        menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_compareMS,
                                                     text='Compare mass spectra...', 
                                                     bitmap=self.icons.iconsLib['compare_mass_spectra_16']))
                        menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_showMassSpectra,
                                                     text='Show mass spectra (waterfall)', 
                                                     bitmap=None))
                        menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_addToMMLTable,
                                                     text='Add spectra to multiple files panel', 
                                                     bitmap=None))
                        menu.AppendSeparator() 
                        menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveDataCSVDocument,
                                                 text=saveCSVLabel, 
                                                 bitmap=self.icons.iconsLib['file_csv_16']))
                        menu.AppendMenu(wx.ID_ANY, 'Save to file...', saveDFSubMenu)
                    elif self.extractData != 'Mass Spectra' and "UniDec (" not in self.extractData and self.indent < 4:
                        menu.AppendItem(makeMenuItem(parent=menu, id=ID_showPlotDocument,
                                                     text='Show mass spectrum\tAlt+S', 
                                                     bitmap=self.icons.iconsLib['mass_spectrum_16']))
                        menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_add_annotations,
                                                     text='Add annotation...', 
                                                     bitmap=self.icons.iconsLib['annotate16']))
                        menu.AppendSeparator()
                        menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_processMS,
                                                     text='Process...\tP', 
                                                     bitmap=self.icons.iconsLib['process_ms_16']))
                        menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_UniDec,
                                                     text='Deconvolute using UniDec...', 
                                                     bitmap=self.icons.iconsLib['process_unidec_16']))
                        menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_addOneToMMLTable,
                                                     text='Add spectrum to multiple files panel', 
                                                     bitmap=None))
                        menu.Append(ID_duplicateItem, 'Duplicate item')
                        menu.Append(ID_renameItem, 'Rename\tAlt+R')
                        menu.AppendSeparator()
                        menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveMSImageDoc,
                                                 text=saveImageLabel, 
                                                 bitmap=self.icons.iconsLib['file_png_16']))
                        menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveDataCSVDocument,
                                                 text=saveCSVLabel, 
                                                 bitmap=self.icons.iconsLib['file_csv_16']))
                    elif self.extractData != 'Mass Spectra' and "UniDec (" in self.extractData:
                        menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_show_unidec, 
                                                     text='Show UniDec results', 
                                                     bitmap=None))
                        menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_save_unidec, 
                                                 text='Save UniDec results ({})'.format(self.config.saveExtension), 
                                                 bitmap=None))
                    elif self.extractData != 'Mass Spectra' and "UniDec (" in self.extractParent:
                        menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_save_unidec, 
                                                 text='Save UniDec results ({})'.format(self.config.saveExtension), 
                                                 bitmap=None))
                    menu.AppendItem(makeMenuItem(parent=menu, id=ID_removeItemDocument,
                                                 text='Delete item\tDelete', 
                                                 bitmap=self.icons.iconsLib['clear_16']))
            elif itemType == 'UniDec' or itemType == "UniDec (processed)":
                    menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_show_unidec, 
                                             text='Show UniDec results', 
                                             bitmap=None))
                    menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_save_unidec, 
                                             text='Save UniDec results ({})'.format(self.config.saveExtension), 
                                             bitmap=None))
                    menu.AppendSeparator() 
                    menu.AppendItem(makeMenuItem(parent=menu, id=ID_removeItemDocument,
                                                 text='Delete item\tDelete', 
                                                 bitmap=self.icons.iconsLib['clear_16']))
            elif itemType in ['Chromatogram', 'Chromatograms (EIC)']:
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_showPlotDocument,
                                             text='Show chromatogram\tAlt+S', 
                                             bitmap=self.icons.iconsLib['chromatogram_16']))
                menu.AppendSeparator()
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveRTImageDoc,
                                         text=saveImageLabel, 
                                         bitmap=self.icons.iconsLib['file_png_16']))
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveDataCSVDocument,
                                         text=saveCSVLabel, 
                                         bitmap=self.icons.iconsLib['file_csv_16']))
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_removeItemDocument,
                                             text='Delete item\tDelete', 
                                             bitmap=self.icons.iconsLib['clear_16']))
            elif itemType in ['Drift time (1D)', "Drift time (1D, EIC)"]:
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_showPlotDocument,
                                             text='Show mobiligram\tAlt+S', 
                                             bitmap=self.icons.iconsLib['mobiligram_16']))
                menu.AppendSeparator()
                menu.AppendMenu(ID_ANY, 'Change x-axis to...', xlabel1DMenu)
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_save1DImageDoc,
                                         text=saveImageLabel, 
                                         bitmap=self.icons.iconsLib['file_png_16']))
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveDataCSVDocument,
                                         text=saveCSVLabel, 
                                         bitmap=self.icons.iconsLib['file_csv_16']))
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_removeItemDocument,
                                             text='Delete item\tDelete', 
                                             bitmap=self.icons.iconsLib['clear_16']))             
            if menu.MenuItemCount > 0:
                menu.AppendSeparator()  
            menu.Append(ID_docTree_add_MS_to_interactive, 'Add mass spectra')
            menu.Append(ID_docTree_add_RT_to_interactive, 'Add chromatogram(s)')
            menu.Append(ID_docTree_add_DT_to_interactive, 'Add mobiligram(s)')
            menu.Append(ID_docTree_add_2DT_to_interactive, 'Add heatmap(s)')
            
        elif (itemType == 'Mass Spectrum' or 
              itemType == 'Mass Spectra' or 
              itemType == 'Mass Spectrum (processed)'):
            if self.itemType == 'Mass Spectrum' or itemType == 'Mass Spectrum (processed)':
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_showPlotDocument,
                                             text='Show mass spectrum\tAlt+S', 
                                             bitmap=self.icons.iconsLib['mass_spectrum_16']))
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_add_annotations,
                                             text='Add annotation...', 
                                             bitmap=self.icons.iconsLib['annotate16']))
                # check if deconvolution results exist
                if 'unidec' in self.currentData:
                    menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_show_unidec, 
                                             text='Show UniDec results', 
                                             bitmap=None))
                    menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_save_unidec, 
                                             text='Save UniDec results ({})'.format(self.config.saveExtension), 
                                             bitmap=None))
                menu.AppendSeparator()                
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_processMS,
                                             text='Process...\tP', 
                                             bitmap=self.icons.iconsLib['process_ms_16']))
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_UniDec,
                                             text='Deconvolute using UniDec...', 
                                             bitmap=self.icons.iconsLib['process_unidec_16']))
                menu.AppendSeparator()
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveMSImageDoc,
                                         text=saveImageLabel, 
                                         bitmap=self.icons.iconsLib['file_png_16']))
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveDataCSVDocument,
                                         text=saveCSVLabel, 
                                         bitmap=self.icons.iconsLib['file_csv_16']))
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_removeItemDocument,
                                             text='Delete item\tDelete', 
                                             bitmap=self.icons.iconsLib['clear_16']))
            else:
                if self.extractData == 'Mass Spectra':
                    menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_compareMS,
                                                 text='Compare mass spectra...', 
                                                 bitmap=self.icons.iconsLib['compare_mass_spectra_16']))
                    menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_showMassSpectra,
                                                 text='Show mass spectra (waterfall)', 
                                                 bitmap=None))
                    menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_addToMMLTable,
                                                 text='Add spectra to multiple files panel', 
                                                 bitmap=None))
                    menu.AppendSeparator() 
                    menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveDataCSVDocument,
                                             text=saveCSVLabel, 
                                             bitmap=self.icons.iconsLib['file_csv_16']))
                    menu.AppendMenu(wx.ID_ANY, 'Save to file...', saveDFSubMenu)
                elif self.extractData != 'Mass Spectra' and "UniDec (" not in self.extractData and self.indent != 4:
                    menu.AppendItem(makeMenuItem(parent=menu, id=ID_showPlotDocument,
                                                 text='Show mass spectrum\tAlt+S', 
                                                 bitmap=self.icons.iconsLib['mass_spectrum_16']))
                    menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_add_annotations,
                                                 text='Add annotation...', 
                                                 bitmap=self.icons.iconsLib['annotate16']))
                    menu.AppendSeparator()
                    menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_processMS,
                                                 text='Process...\tP', 
                                                 bitmap=self.icons.iconsLib['process_ms_16']))
                    menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_UniDec,
                                                 text='Deconvolute using UniDec...', 
                                                 bitmap=self.icons.iconsLib['process_unidec_16']))
                    menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_addOneToMMLTable,
                                                 text='Add spectrum to multiple files panel', 
                                                 bitmap=None))
                    menu.Append(ID_duplicateItem, 'Duplicate item')
                    menu.Append(ID_renameItem, 'Rename\tAlt+R')
                    menu.AppendSeparator()
                    menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveMSImageDoc,
                                             text=saveImageLabel, 
                                             bitmap=self.icons.iconsLib['file_png_16']))
                    menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveDataCSVDocument,
                                             text=saveCSVLabel, 
                                             bitmap=self.icons.iconsLib['file_csv_16']))
                elif "UniDec (" in self.extractData:
                    menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_show_unidec, 
                                             text='Show UniDec results', 
                                             bitmap=None))
                    menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_save_unidec, 
                                             text='Save UniDec results ({})'.format(self.config.saveExtension), 
                                             bitmap=None))
                    
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_removeItemDocument,
                                             text='Delete item\tDelete', 
                                             bitmap=self.icons.iconsLib['clear_16']))
        elif itemType == 'UniDec' or itemType == "UniDec (processed)":
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_show_unidec, 
                                         text='Show UniDec results', 
                                         bitmap=None))
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_save_unidec, 
                                         text='Save UniDec results ({})'.format(self.config.saveExtension), 
                                         bitmap=None))
                menu.AppendSeparator() 
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_removeItemDocument,
                                             text='Delete item\tDelete', 
                                             bitmap=self.icons.iconsLib['clear_16']))
        # Sample information
        elif itemType == 'Sample information':
            menu.Append(ID_showSampleInfo, 'Show sample information')
        # Chromatogram
        elif itemType in ['Chromatogram', 'Chromatograms (EIC)']:
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_showPlotDocument,
                                         text='Show chromatogram\tAlt+S', 
                                         bitmap=self.icons.iconsLib['chromatogram_16']))
            menu.AppendSeparator()
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveRTImageDoc,
                                     text=saveImageLabel, 
                                     bitmap=self.icons.iconsLib['file_png_16']))
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveDataCSVDocument,
                                     text=saveCSVLabel, 
                                     bitmap=self.icons.iconsLib['file_csv_16']))
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_removeItemDocument,
                                         text='Delete item\tDelete', 
                                         bitmap=self.icons.iconsLib['clear_16']))
        # Drift time (1D)
        elif itemType == 'Drift time (1D)':
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_showPlotDocument,
                                         text='Show mobiligram\tAlt+S', 
                                         bitmap=self.icons.iconsLib['mobiligram_16']))
            menu.AppendSeparator()
            menu.AppendMenu(ID_ANY, 'Change x-axis to...', xlabel1DMenu)
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_save1DImageDoc,
                                     text=saveImageLabel, 
                                     bitmap=self.icons.iconsLib['file_png_16']))
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveDataCSVDocument,
                                     text=saveCSVLabel, 
                                     bitmap=self.icons.iconsLib['file_csv_16']))
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_removeItemDocument,
                                         text='Delete item\tDelete', 
                                         bitmap=self.icons.iconsLib['clear_16']))
        # Drift time (2D)   
        elif any(itemType in type for type in ['Drift time (2D)', 
                                               'Drift time (2D, processed)',
                                               'Drift time (2D, EIC)',
                                               'Drift time (2D, combined voltages, EIC)',
                                               'Drift time (2D, processed, EIC)',
                                               ]):
            # Only if clicked on an item and not header
            if (self.itemType in ['Drift time (2D)', 'Drift time (2D, processed)']
                or (self.itemType == 'Drift time (2D, EIC)' and self.extractData != self.itemType)
                or (self.itemType == 'Drift time (2D, combined voltages, EIC)' and self.extractData != self.itemType)
                or (self.itemType == 'Drift time (2D, processed, EIC)' and self.extractData != self.itemType)
                ):
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_showPlotDocument,
                                             text='Show heatmap\tAlt+S', 
                                             bitmap=self.icons.iconsLib['heatmap_16']))
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_process2D,
                                             text='Process...\tP', 
                                             bitmap=self.icons.iconsLib['process_2d_16']))
                menu.AppendSeparator()
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_assignChargeState,
                                         text='Assign a charge state...\tAlt+Z', 
                                         bitmap=self.icons.iconsLib['assign_charge_16']))
                menu.AppendMenu(ID_ANY, 'Set X-axis label as...', xlabel2DMenu)
                menu.AppendMenu(ID_ANY, 'Set Y-axis label as...', ylabel2DMenu)
                
#                 menu.Append(ID_add2CCStable2DDocument, 'Add to CCS calibration window')
                menu.AppendSeparator()
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_save2DImageDoc,
                                         text=saveImageLabel, 
                                         bitmap=self.icons.iconsLib['file_png_16']))
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveDataCSVDocument1D,
                                         text=saveCSVLabel1D, 
                                         bitmap=self.icons.iconsLib['file_csv_16']))         
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveDataCSVDocument,
                                         text=saveCSVLabel2D, 
                                         bitmap=self.icons.iconsLib['file_csv_16']))                
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_removeItemDocument,
                                             text='Delete item\tDelete', 
                                             bitmap=self.icons.iconsLib['clear_16']))
                if not any(itemType in type for type in ['Drift time (2D)', 
                                                         'Drift time (2D, processed)']):
                    menu.PrependItem(makeMenuItem(parent=menu, id=ID_showPlot1DDocument,
                                              text='Show mobiligram', 
                                              bitmap=self.icons.iconsLib['mobiligram_16']))
                    menu.PrependItem(makeMenuItem(parent=menu, id=ID_showPlotRTDocument,
                                              text='Show chromatogram', 
                                              bitmap=self.icons.iconsLib['chromatogram_16']))
                    menu.PrependItem(makeMenuItem(parent=menu, id=ID_showPlotMSDocument,
                                              text='Highlight ion in mass spectrum\tAlt+X', 
                                              bitmap=self.icons.iconsLib['zoom_16']))
            # Only if clicked on a header
            else:
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveImageDocument,
                                         text=saveImageLabelAll, 
                                         bitmap=self.icons.iconsLib['file_png_16']))
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveDataCSVDocument1D,
                                         text=saveCSVLabel1D, 
                                         bitmap=self.icons.iconsLib['file_csv_16']))
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveDataCSVDocument,
                                         text=saveCSVLabel2D, 
                                         bitmap=self.icons.iconsLib['file_csv_16']))          
#                 menu.Append(ID_add2CCStable2DDocument, 'Add to CCS calibration window')
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_removeItemDocument,
                                             text='Delete item\tDelete', 
                                             bitmap=self.icons.iconsLib['clear_16']))
        # Input data
        elif self.itemType == 'Input data':
            if (self.itemType == 'Input data' and self.extractData != self.itemType):
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_showPlotDocument,
                                             text='Show heatmap\tAlt+S', 
                                             bitmap=self.icons.iconsLib['heatmap_16']))
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_process2D,
                                             text='Process...\tP', 
                                             bitmap=self.icons.iconsLib['process_2d_16']))
                menu.AppendSeparator()
                menu.AppendMenu(ID_ANY, 'Set X-axis label as...', xlabel2DMenu)
                menu.AppendMenu(ID_ANY, 'Set Y-axis label as...', ylabel2DMenu)
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_save2DImageDoc,
                                         text=saveImageLabel, 
                                         bitmap=self.icons.iconsLib['file_png_16']))
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveDataCSVDocument,
                                         text=saveCSVLabel, 
                                         bitmap=self.icons.iconsLib['file_csv_16']))     
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_removeItemDocument,
                                             text='Delete item\tDelete', 
                                             bitmap=self.icons.iconsLib['clear_16']))
            # Only if clicked on a header
            else:
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_addToTextTable,
                                             text='Add to text file table', 
                                             bitmap=None))
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveImageDocument,
                                         text=saveImageLabelAll, 
                                         bitmap=self.icons.iconsLib['file_png_16']))
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveDataCSVDocument,
                                         text=saveCSVLabel, 
                                         bitmap=self.icons.iconsLib['file_csv_16']))     
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_removeItemDocument,
                                             text='Delete item\tDelete', 
                                             bitmap=self.icons.iconsLib['clear_16']))
        # Statistical method
        elif self.itemType == 'Statistical':
            # Only if clicked on an item and not header
            if self.extractData != self.itemType:
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_showPlotDocument,
                                             text='Show heatmap\tAlt+S', 
                                             bitmap=self.icons.iconsLib['heatmap_16']))
                menu.AppendSeparator()
                if plotLabel[0] == 'RMSF': 
                    menu.Append(ID_saveRMSFImageDoc, saveImageLabel)
                elif plotLabel[0] == 'RMSD Matrix': 
                    menu.Append(ID_saveRMSDmatrixImageDoc, saveImageLabel)
                else: 
                    menu.Append(ID_save2DImageDoc, saveImageLabel)
                menu.Append(ID_saveDataCSVDocument, saveCSVLabel)
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_removeItemDocument,
                                             text='Delete item\tDelete', 
                                             bitmap=self.icons.iconsLib['clear_16']))
                menu.AppendSeparator()
                menu.Append(ID_renameItem, 'Rename\tAlt+R')
            # Only if on a header
            else:
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveImageDocument,
                                         text=saveImageLabelAll, 
                                         bitmap=self.icons.iconsLib['file_png_16']))
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveDataCSVDocument,
                                         text=saveCSVLabel, 
                                         bitmap=self.icons.iconsLib['file_csv_16']))   
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_removeItemDocument,
                                             text='Delete item\tDelete', 
                                             bitmap=self.icons.iconsLib['clear_16']))
        # Drift time (1D) (batch) 
        elif itemType in ['Drift time (1D, EIC, DT-IMS)', 'Drift time (1D, EIC)'] :
            # Only if clicked on an item and not header
            if (not self.extractData ==  'Drift time (1D, EIC, DT-IMS)' and 
                itemType != 'Drift time (1D, EIC)'):
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_showPlotMSDocument,
                                             text='Highlight ion in mass spectrum\tAlt+X', 
                                             bitmap=self.icons.iconsLib['zoom_16']))
            if not self.extractData ==  'Drift time (1D, EIC, DT-IMS)':
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_showPlotDocument,
                                             text='Show mobiligram (EIC)\tAlt+S', 
                                             bitmap=self.icons.iconsLib['mobiligram_16']))       
                menu.AppendSeparator()
                menu.Append(ID_assignChargeState, 'Assign a charge state...\tAlt+Z')
                menu.AppendSeparator()
                menu.Append(ID_save1DImageDoc, saveImageLabel)
                menu.Append(ID_saveDataCSVDocument, saveCSVLabel)
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_removeItemDocument,
                                             text='Delete item\tDelete', 
                                             bitmap=self.icons.iconsLib['clear_16']))
            # Only if on a header
            else:
                menu.Append(ID_saveDataCSVDocument, saveCSVLabel)
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_removeItemDocument,
                                             text='Delete item\tDelete', 
                                             bitmap=self.icons.iconsLib['clear_16']))
        elif itemType == 'Chromatograms (combined voltages, EIC)':
            # Only if clicked on an item and not header
            if not self.extractData ==  'Chromatograms (combined voltages, EIC)':
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_showPlotDocument,
                                             text='Show chromatogram\tAlt+S', 
                                             bitmap=self.icons.iconsLib['chromatogram_16']))
                menu.AppendSeparator()
                menu.Append(ID_assignChargeState, 'Assign a charge state...\tAlt+Z')
                menu.AppendSeparator()
                menu.Append(ID_saveRTImageDoc, saveImageLabel)
                menu.Append(ID_saveDataCSVDocument, saveCSVLabel)
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_removeItemDocument,
                                             text='Delete item\tDelete', 
                                             bitmap=self.icons.iconsLib['bin16']))
            # Only if on a header
            else:
                menu.Append(ID_saveDataCSVDocument, saveCSVLabel)    
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_removeItemDocument,
                                             text='Delete item\tDelete', 
                                             bitmap=self.icons.iconsLib['clear_16']))
        elif itemType == 'Calibration Parameters':
            menu.Append(ID_saveDataCSVDocument, saveCSVLabel)
            menu.Append(ID_saveDataCCSCalibrantDocument, "Save CCS calibration to file")
            menu.Append(ID_removeItemDocument, 'Delete item')
        elif (itemType == 'Calibration peaks' or
              itemType == 'Calibrants'):
            if self.itemType != self.extractData:
                menu.Append(ID_showPlotDocument, 'Show \tAlt+S')
                menu.AppendSeparator()
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_removeItemDocument,
                                             text='Delete item\tDelete', 
                                             bitmap=self.icons.iconsLib['clear_16']))        
        elif itemType == 'Overlay':
            if self.itemType != self.extractData:
                if self.splitText[0] in  ["Waterfall (Raw)", "Waterfall (Processed)", "Waterfall (Fitted)",
                                          "Waterfall (Deconvoluted MW)", "Waterfall (Charge states)"]:
                    menu.AppendItem(makeMenuItem(parent=menu, id=ID_showPlotDocument,
                                                 text='Show\tAlt+S', bitmap=None))
                elif self.splitText[0] not in ['1D', 'RT']:
                    menu.AppendItem(makeMenuItem(parent=menu, id=ID_showPlotDocument,
                                                 text='Show heatmap\tAlt+S', 
                                                 bitmap=self.icons.iconsLib['overlay_2D_16']))
                else: menu.AppendItem(makeMenuItem(parent=menu, id=ID_showPlotDocument,
                                                 text='Show\tAlt+S', bitmap=None))
                # Depending which plot is being saved, different event ID is used
                if self.splitText[0] == 'RMSF': menu.Append(ID_saveRMSFImageDoc, saveImageLabel)
                elif self.splitText[0] == '1D': menu.Append(ID_save1DImageDoc, saveImageLabel)
                elif self.splitText[0] == 'RT': menu.Append(ID_saveRTImageDoc, saveImageLabel)
                elif self.splitText[0] == 'Mask' or plotLabel[0] == 'Transparent': 
                    menu.Append(ID_saveOverlayImageDoc, saveImageLabel)
                elif self.splitText[0] in  ["Waterfall (Raw)", "Waterfall (Processed)", "Waterfall (Fitted)",
                                              "Waterfall (Deconvoluted MW)", "Waterfall (Charge states)"]:
                    menu.Append(ID_saveWaterfallImageDoc, saveImageLabel)
                else: menu.Append(ID_save2DImageDoc, saveImageLabel)
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_removeItemDocument,
                                             text='Delete item\tDelete', 
                                             bitmap=self.icons.iconsLib['clear_16']))
                menu.AppendSeparator()
                menu.Append(ID_renameItem, 'Rename\tAlt+R')
            # Header only
            else:
                menu.AppendSeparator()
                menu.Append(ID_saveImageDocument, saveImageLabelAll)
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_removeItemDocument,
                                             text='Delete item\tDelete', 
                                             bitmap=self.icons.iconsLib['clear_16']))
        elif (itemType == 'DT/MS'):
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_showPlotDocument,
                                         text='Show heatmap\tAlt+S', 
                                         bitmap=self.icons.iconsLib['heatmap_16']))
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_process2D,
                                         text='Process...\tP', bitmap=self.icons.iconsLib['process_2d_16']))
#             menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_extractDTMS,
#                                          text='Re-extract data', bitmap=None))
            
            menu.AppendSeparator()
            menu.AppendMenu(ID_ANY, 'Set Y-axis label as...', ylabelDTMSMenu)
            menu.AppendSeparator()
            menu.Append(ID_saveMZDTImage, saveImageLabel)
            menu.Append(ID_saveDataCSVDocument, saveCSVLabel)
 
        if menu.MenuItemCount > 0:
            menu.AppendSeparator()  
        
        if self.indent == 1:
            menu.Append(ID_renameItem, 'Rename document\tAlt+R')
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_openDocInfo,
                                     text='Notes, Information, Labels...\tCtrl+I', 
                                     bitmap=self.icons.iconsLib['info16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_goToDirectory,
                                     text='Go to folder...\tCtrl+G', 
                                     bitmap=self.icons.iconsLib['folder_path_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveAsInteractive,
                                     text='Open interactive output panel...\tShift+Z', 
                                     bitmap=self.icons.iconsLib['bokehLogo_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveDocument,
                                     text='Save document to file\tCtrl+P', 
                                     bitmap=self.icons.iconsLib['pickle_16']))
        menu.AppendSeparator()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_removeDocument,
                                     text='Delete document\tDelete', 
                                     bitmap=self.icons.iconsLib['bin16']))
        self.PopupMenu(menu) 
        menu.Destroy()
        self.SetFocus()
   
    def onAddToTable(self, evt):
        evtID = evt.GetId()
        
        filelist = self.presenter.view.panelMML.topP.filelist
        textlist = self.presenter.view.panelMultipleText.topP.filelist
        if evtID == ID_docTree_addToMMLTable:
            data = self.itemData.multipleMassSpectrum
            document_title = self.itemData.title
            n_rows = len(data)
            colors = self.presenter.view.panelPlots.onChangePalette(None, n_colors=n_rows, return_colors=True)
            for i, key in enumerate(data):
                count = filelist.GetItemCount()
                label = data[key].get('label', os.path.splitext(key)[0])
                color = data[key].get('color', colors[i])
                if np.sum(color) > 4: color = convertRGB255to1(color)
                filelist.Append([key, data[key].get('trap', 0), document_title, label])
                filelist.SetItemBackgroundColour(count, convertRGB1to255(color))
                
        elif evtID == ID_docTree_addOneToMMLTable:
            data = self.itemData.multipleMassSpectrum
            count = filelist.GetItemCount()
            colors = self.presenter.view.panelPlots.onChangePalette(None, n_colors=count+1, return_colors=True)
            key = self.extractData
            document_title = self.itemData.title
            label = data.get('label', key)
            color = data[key].get('color', colors[-1]) 
            if np.sum(color) > 4: color = convertRGB255to1(color)
            filelist.Append([key, data[key].get('trap', 0), document_title, label])
            filelist.SetItemBackgroundColour(count, convertRGB1to255(color))
        elif evtID == ID_docTree_addToTextTable:
            data = self.itemData.IMS2DcompData
            document_title = self.itemData.title
            n_rows = len(data)
            colors = self.presenter.view.panelPlots.onChangePalette(None, n_colors=n_rows, return_colors=True)
            for i, key in enumerate(data):
                count = textlist.GetItemCount()
                label = data[key].get('label', os.path.splitext(key)[0])
                color = data[key].get('color', colors[i])
                if np.sum(color) > 4: color = convertRGB255to1(color)
                minCE, maxCE = np.min(data[key]['xvals']), np.max(data[key]['xvals'])  
                document_label = "{}: {}".format(document_title, key)
                textlist.Append([minCE, maxCE, data[key]['charge'], color, data[key]['cmap'],
                                 data[key]['alpha'], data[key]['mask'], label, data[key]['zvals'].shape,
                                 document_label])
                textlist.SetItemBackgroundColour(count, convertRGB1to255(color))
        elif evtID == ID_docTree_addInteractiveToTextTable:
            data = self.itemData.IMS2Dions
            document_title = self.itemData.title
            n_rows = len(data)
            colors = self.presenter.view.panelPlots.onChangePalette(None, n_colors=n_rows, return_colors=True)
            for i, key in enumerate(data):
                count = textlist.GetItemCount()
                label = data[key].get('label', os.path.splitext(key)[0])
                color = data[key].get('color', colors[i])
                if np.sum(color) > 4: color = convertRGB255to1(color)
                minCE, maxCE = np.min(data[key]['xvals']), np.max(data[key]['xvals'])  
                document_label = "{}: {}".format(document_title, key)
                textlist.Append([minCE, maxCE, data[key].get('charge',""), color, data[key]['cmap'],
                                 data[key]['alpha'], data[key]['mask'], label, data[key]['zvals'].shape,
                                 document_label])
                textlist.SetItemBackgroundColour(count, convertRGB1to255(color))
        
        
        if evtID in [ID_docTree_addToMMLTable, ID_docTree_addOneToMMLTable]:
            # sort items
            self.presenter.view.panelMML.topP.OnSortByColumn(column=1, overrideReverse=True)
            self.presenter.view.panelMML.topP.onRemoveDuplicates(None)
            self.presenter.view.onPaneOnOff(evt=ID_window_multipleMLList, check=True)
        elif evtID in [ID_docTree_addToTextTable, ID_docTree_addOneToTextTable, ID_docTree_addInteractiveToTextTable]:
            # sort items
            self.presenter.view.panelMultipleText.topP.onRemoveDuplicates(None)
            self.presenter.view.onPaneOnOff(evt=ID_window_textList, check=True)
            
    def onShowMassSpectra(self, evt):
        
        data = self.itemData.multipleMassSpectrum
        if len(data.keys()) > 50:
            print("Warning - this file has a lot of MS features.")
        
        # Check for energy
        energy_name = []
        for key in data:
            energy_name.append([key, data[key].get('trap', 0)])
        # sort 
        energy_name.sort(key=itemgetter(1))
        
        names, colors, xvals_list, yvals_list = [], [], [], []
        for row in energy_name:
            key = row[0]
            xvals_list.append(data[key]['xvals'])
            yvals_list.append(data[key]['yvals'])
            names.append(key)
        
        kwargs = {'show_y_labels':True, 'labels':names}
        self.presenter.view.panelPlots.on_plot_waterfall(xvals_list, yvals_list, None, colors=colors, 
                                                         xlabel="m/z", ylabel="", **kwargs)
        self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['Waterfall'])
        
    def onCompareMS(self, evt):
        if self.currentItem == None: 
            return

        if self.indent == 2:
            document_list, document_spectrum_list = [], {}
            for document_title in self.presenter.documentsDict:
                if self.presenter.documentsDict[document_title].gotMultipleMS:
                    document_list.append(document_title)
                    document_spectrum_list[document_title] = self.presenter.documentsDict[document_title].multipleMassSpectrum.keys()
            
            data = self.itemData.multipleMassSpectrum
            if len(data.keys()) < 2: 
                print('You must have more than two mass spectra to compare MS')
                return 
            
            kwargs = {'current_document':self.itemData.title,
                      'document_list':document_list,
                      'spectrum_list':data.keys(),
                      'document_spectrum_list':document_spectrum_list}
            
            self.compareMSDlg = panelCompareMS(self.parent, 
                                               self.presenter, 
                                               self.config, 
                                               self.icons,
                                               **kwargs)
            self.compareMSDlg.Show()
            
    def onProcess2D(self, evt):
        if self.itemType in ['Drift time (2D)','Drift time (2D, processed)']:
            dataset = self.itemType
            ionName = ""
        elif self.itemType in ['Drift time (2D, EIC)', 'Drift time (2D, combined voltages, EIC)',
                               'Drift time (2D, processed, EIC)','Input data',
                               'Statistical'] and self.indent > 2:
            dataset = self.itemType
            ionName = self.extractData
        elif self.itemType == "DT/MS":
            dataset = self.itemType
            ionName = ""
#         elif self.itemType in ['Drift time (2D, EIC)', 'Drift time (2D, combined voltages, EIC)',
#                                'Drift time (2D, processed, EIC)','Input data',
#                                'Statistical'] and self.indent == 2:
#             dataset = self.itemType
#             ionName = 'all'
            
        # create processing kwargs
        pKwargs = {'document_2D':self.itemData.title, 
                   'dataset_2D':dataset, 
                   'ionName_2D':ionName,
                   'update_mode':'2D'}
        # call function
        self.presenter.view.onProcessParameters(evt=ID_processSettings_2D,
                                                **pKwargs)
            
    def onProcessMS(self, evt):
        evtID = evt.GetId()
        
        pKwargs = {'document_MS':self.itemData.title,
                   'dataset_MS':self.extractData,
                   'ionName_MS':"",
                   'update_mode':'MS'}
        # call function
        if evtID == ID_docTree_UniDec:
            self.presenter.view.onProcessParameters(evt=ID_processSettings_UniDec,
                                                    **pKwargs)
        else:
            self.presenter.view.onProcessParameters(evt=ID_processSettings_MS,
                                                    **pKwargs)
         
    def onProcess(self, evt=None):
        if self.itemData == None:
            return
        
        if self.itemType == 'Mass Spectrum': pass
        elif any(self.itemType in itemType for itemType in ['Drift time (2D)', 'Drift time (2D, processed)',
                                                            'Drift time (2D, EIC)',
                                                            'Drift time (2D, combined voltages, EIC)',
                                                            'Drift time (2D, processed, EIC)',
                                                            'Input data', 'Statistical']):
            self.presenter.process2Ddata2()
            self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['2D'])

        elif self.itemType == 'DT/MS':
            self.presenter.process2Ddata2(mode='MSDT')
            self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['MZDT'])
            
    def updateComparisonMS(self, evt):
        print("Comparing {} vs {}".format(self.compareMSDlg.output["spectrum_1"][1], 
                                          self.compareMSDlg.output["spectrum_2"][1]))
        # get data
        try:
            data_1 = self.presenter.documentsDict[self.compareMSDlg.output["spectrum_1"][0]].multipleMassSpectrum
            spectrum_1 = data_1[self.compareMSDlg.output["spectrum_1"][1]]
        except: 
            dialogs.dlgBox(exceptionTitle="Incorrect data", 
                           exceptionMsg= "Could not find requested dataset. Try resellecting the document in the Documents Panel or opening this dialog again.",
                           type="Error")
            return
        try:
            data_2 = self.presenter.documentsDict[self.compareMSDlg.output["spectrum_2"][0]].multipleMassSpectrum
            spectrum_2 = data_2[self.compareMSDlg.output["spectrum_2"][1]]
        except: 
            dialogs.dlgBox(exceptionTitle="Incorrect data", 
                           exceptionMsg= "Could not find requested dataset. Try resellecting the document in the Documents Panel or opening this dialog again.",
                           type="Error")
            return
        
        try:
            msX = spectrum_1['xvals']
            msX_1 = spectrum_1['xvals']
            msX_2 = spectrum_2['xvals']
            msY_1 = spectrum_1['yvals']
            msY_2 = spectrum_2['yvals']
        except KeyError:
            dialogs.dlgBox(exceptionTitle="Incorrect data", 
                           exceptionMsg= "Could not find requested dataset. Try resellecting the document in the Documents Panel or opening this dialog again.",
                           type="Error")
            return
        
        
        # Pre-process
        if self.config.compare_massSpectrumParams['preprocess']:
            msY_1 = self.presenter.processMSdata(msY=msY_1, return_data=True)
            msY_2 = self.presenter.processMSdata(msY=msY_2, return_data=True)
                
        # Normalize 1D data
        if self.config.compare_massSpectrumParams['normalize']:
            msY_1 = normalize1D(inputData=msY_1)
            msY_2 = normalize1D(inputData=msY_2)
        
        if self.config.compare_massSpectrumParams['subtract']:
            if len(msX) != len(msY_1) or  len(msX) != len(msY_2) or len(msY_1) != len(msY_2):
                msg = "Mass spectra are not of the same size. X-axis: %s Y-axis (1): %s | Y-axis (2): %s" % (len(msX), len(msY_1), len(msY_2))
                args = (msg, 4, 5)            
                self.presenter.onThreading(None, args, action='updateStatusbar')
                dialogs.dlgBox(exceptionTitle="Incorrect size", 
                               exceptionMsg= msg,
                               type="Error")
                return
            # If normalizing, there should be no issues in signal intensity
            if self.config.compare_massSpectrumParams['normalize']:
                self.config.compare_massSpectrumParams['subtract'] = False
                msY_1, msY_2 = subtractMS(msY_1, msY_2)
                self.presenter.view.panelPlots.plot_compare(msX=msX, 
                                                            msY_1=msY_1, 
                                                            msY_2=msY_2, 
                                                            xlimits=None)
            # Sometimes, it is necessary to plot the MS as ordinary 1 color plots
            else:
                msY = msY_1 - msY_2
                self.presenter.plot_compareMS(msX=msX, msY=msY, 
                                              msY_1=msY_1, msY_2=msY_2)
        else:
            self.presenter.view.panelPlots.plot_compare(msX_1=msX_1,
                                                        msX_2=msX_2,
                                                        msY_1=msY_1, 
                                                        msY_2=msY_2, 
                                                        xlimits=None)
   
    def onShow_and_SavePlot(self, evt):
        """
        This function replots selected item and subsequently saves said item to 
        figure
        """
        
        # Show plot first
        self.onShowPlot(evt=None, save_image=True)
#         # Save plot second
#         self.presenter.view.panelPlots.save_images(evt=evt)
      
    def onDuplicateItem(self, evt):
        if self.itemType == "Mass Spectra" and self.extractData != 'Mass Spectra':
            # Change document tree
            title = self.itemData.title
            docItem = self.getItemByData(self.presenter.documentsDict[title].multipleMassSpectrum[self.extractData])
            copy_name = "{} - copy".format(self.extractData)
            # Change dictionary key
            self.presenter.documentsDict[title].multipleMassSpectrum[copy_name] = self.presenter.documentsDict[self.title].multipleMassSpectrum[self.extractData].copy()
            document = self.presenter.documentsDict[title]
            self.presenter.OnUpdateDocument(document, 'document')   
            self.Expand(docItem)
              
    def onRenameItem(self, evt):
        
        if self.itemData == None:
            return
        
        if self.indent == 1:
            prepend_name = False
        elif self.itemType == 'Statistical' and self.extractData != 'Statistical': 
            prepend_name = True
        elif self.itemType == 'Overlay' and self.extractData != 'Overlay':
            prepend_name = True 
        elif self.itemType == "Mass Spectra" and self.extractData != 'Mass Spectra':
            prepend_name = False
        else: 
            return
        
        try:
            current_name = re.split('-|,|:|__', self.extractData.replace(' ',''))[0]
        except AttributeError: 
            current_name = self.itemData.title
            
        if current_name == 'Grid(nxn)': current_name = 'Grid (n x n)'
        elif current_name == 'Grid(2': current_name = 'Grid (2->1)'
        elif current_name == 'RMSDMatrix': current_name = 'RMSD Matrix'
        elif current_name == 'Waterfall(Raw)': current_name = 'Waterfall (Raw)'
        elif current_name == 'Waterfall(Processed)': current_name = 'Waterfall (Processed)'
        elif current_name == 'Waterfall(Fitted)': current_name = 'Waterfall (Fitted)'
        elif current_name == 'Waterfall(DeconvolutedMW)': current_name = 'Waterfall (Deconvoluted MW)'

            
        kwargs = {'current_name':current_name, 'prepend_name':prepend_name}
        renameDlg = panelRenameItem(self, self.presenter, self.title, **kwargs)
        renameDlg.CentreOnScreen()
        renameDlg.ShowModal()
        new_name = renameDlg.new_name
        
        if new_name == current_name: 
            print('Names are the same - ignoring')
        elif new_name == '' or new_name == None:
            print('Incorrect name')
        else:
            # Actual new name, prepended
            if self.indent == 1:
                # Change document tree
                docItem = self.getItemByData(self.presenter.documentsDict[current_name])
                document = self.presenter.documentsDict[current_name]
                document.title = new_name
                docItem.title = new_name
                parent = self.GetItemParent(docItem)
                del self.presenter.documentsDict[current_name]
                self.SetItemText(docItem, new_name)
                # Change dictionary key
                self.presenter.OnUpdateDocument(document, 'document')    
                self.Expand(docItem)
                
                # check if item is in other panels
                try: self.presenter.view.panelMML.topP.onRenameItem(current_name, new_name, item_type="document")
                except: pass
                try: self.presenter.view.panelMultipleIons.topP.onRenameItem(current_name, new_name, item_type="document")
                except: pass
#                         try: self.presenter.view.panelMultipleText.topP.onClearItems(title)
#                         except: pass
#                         try: self.presenter.view.panelMML.topP.onClearItems(title)
#                         except: pass
#                         try: self.presenter.view.panelLinearDT.topP.onClearItems(title)
#                         except: pass
#                         try: self.presenter.view.panelLinearDT.bottomP.onClearItems(title)
#                         except: pass
                
                
            elif self.itemType == 'Statistical':
                # Change document tree
                docItem = self.getItemByData(self.presenter.documentsDict[self.title].IMS2DstatsData[self.extractData])
                parent = self.GetItemParent(docItem)
                self.SetItemText(docItem, new_name)
                # Change dictionary key
                self.presenter.documentsDict[self.title].IMS2DstatsData[new_name] = self.presenter.documentsDict[self.title].IMS2DstatsData.pop(self.extractData)
                self.Expand(docItem)
            elif self.itemType == 'Overlay':
                # Change document tree
                docItem = self.getItemByData(self.presenter.documentsDict[self.title].IMS2DoverlayData[self.extractData])
                parent = self.GetItemParent(docItem)
                self.SetItemText(docItem, new_name)
                # Change dictionary key
                self.presenter.documentsDict[self.title].IMS2DoverlayData[new_name] = self.presenter.documentsDict[self.title].IMS2DoverlayData.pop(self.extractData)
                self.Expand(docItem)
            elif self.itemType == "Mass Spectra":
                # Change document tree
                docItem = self.getItemByData(self.presenter.documentsDict[self.title].multipleMassSpectrum[self.extractData])
                parent = self.GetItemParent(docItem)
                self.SetItemText(docItem, new_name)
                # Change dictionary key
                self.presenter.documentsDict[self.title].multipleMassSpectrum[new_name] = self.presenter.documentsDict[self.title].multipleMassSpectrum.pop(self.extractData)
                self.Expand(docItem)
                # check if item is in other panels
                try: self.presenter.view.panelMML.topP.onRenameItem(current_name, new_name, item_type="filename")
                except: pass

            # Expand parent
            try: self.Expand(parent)
            except: pass
            
    def onGoToDirectory(self, evt=None):
        '''
        Go to selected directory
        '''
        self.presenter.openDirectory()
         
    def onSaveUnidec(self, evt, data_type="all"):
        basename = os.path.splitext(self.itemData.title)[0]
        
        if self.itemType == "UniDec" and self.indent == 2:
            unidec_engine_data = self.itemData.massSpectrum['unidec']
            data_type = "all"
        elif self.itemType == "UniDec" and self.indent == 3:
            unidec_engine_data = self.itemData.massSpectrum['unidec']
            data_type = self.extractData
        elif self.itemType == "Mass Spectrum (processed)":
            unidec_engine_data = self.currentData['unidec']
            print("2")
        elif self.itemType == "UniDec (processed)":
            unidec_engine_data = self.itemData.smoothMS['unidec']
            print("3")
        elif self.itemType == "Mass Spectra" and self.indent == 3:
            title = re.split('UniDec \(', self.extractData)[1][:-1]
            unidec_engine_data = self.itemData.multipleMassSpectrum[title]['unidec']
            data_type = "all"
        elif self.itemType == "Mass Spectra" and self.indent == 4:
            title = re.split('UniDec \(', self.extractParent)[1][:-1]
            unidec_engine_data = self.itemData.multipleMassSpectrum[title]['unidec']
            data_type = self.extractData
            basename = "{}_{}".format(basename, title)

        # replace strings in the title
        basename = basename.replace(".csv","").replace(".txt","").replace(".raw","").replace(".d","")
        
        try:
            if data_type in ["all", "MW distribution"]:
                data_type_name = "MW distribution"
                defaultValue = "unidec_MW_{}{}".format(basename, self.config.saveExtension)
                
                data = unidec_engine_data[data_type_name]
                kwargs = {'default_name':defaultValue}
                data = [data['xvals'], data['yvals']]
                labels = ['MW(Da)','Intensity']
                self.onSaveData(data=data, labels=labels, data_format='%.4f', **kwargs)
        except: pass
        
        try:
            if data_type in ["all", "m/z with isolated species"]:
                data_type_name = "m/z with isolated species"
                defaultValue = "unidec_mz_species_{}{}".format(basename, self.config.saveExtension)
                data = unidec_engine_data[data_type_name]
    
                i, save_data, labels = 0, [], ["m/z"]
                for key in data:
                    if key.split(" ")[0] != "MW:": continue
                    xvals = data[key]['line_xvals']
                    if i == 0: save_data.append(xvals)
                    yvals = data[key]['line_yvals']
                    save_data.append(yvals)
                    labels.append(key)
                    i =+ 1
                save_data = np.column_stack(save_data).T
                
                kwargs = {'default_name':defaultValue}
                self.onSaveData(data=save_data, labels=labels, data_format='%.4f', **kwargs)
        except: pass
        
        try:
            if data_type in ["all", "Fitted"]:
                data_type_name = "Fitted"
                defaultValue = "unidec_fitted_{}{}".format(basename, self.config.saveExtension)
                data = unidec_engine_data[data_type_name]
                
                kwargs = {'default_name':defaultValue}
                data = [data['xvals'][0], data['yvals'][0], data['yvals'][1]]
                labels = ['m/z(Da)','Intensity(raw)', 'Intensity(fitted)']
                self.onSaveData(data=data, labels=labels, data_format='%.4f', **kwargs)
        except: pass
        
        try:  
            if data_type in ["all", "Processed"]:
                data_type_name = "Processed"
                defaultValue = "unidec_processed_{}{}".format(basename, self.config.saveExtension)
                data = unidec_engine_data[data_type_name]
                
                kwargs = {'default_name':defaultValue}
                data = [data['xvals'], data['yvals']]
                labels = ['m/z(Da)','Intensity']
                self.onSaveData(data=data, labels=labels, data_format='%.4f', **kwargs)
        except: pass
        
        try:       
            if  data_type in ["all", "m/z vs Charge"]:
                data_type_name = "m/z vs Charge"
                defaultValue = "unidec_mzVcharge_{}{}".format(basename, self.config.saveExtension)
                data = unidec_engine_data[data_type_name]['grid']
    
                zvals = data[:, 2]
                xvals = np.unique(data[:, 0])
                yvals = np.unique(data[:, 1])
    
                # reshape data
                xlen = len(xvals)
                ylen = len(yvals)
                zvals = np.reshape(zvals, (xlen, ylen))
    
                # Combine x-axis with data
                save_data = np.column_stack((xvals, zvals)).T
                yvals = map(str, yvals.tolist())
                labels = ["m/z(Da)"]
                for label in yvals: labels.append(label)
                
                kwargs = {'default_name':defaultValue}
                self.onSaveData(data=save_data, labels=labels, data_format='%.4f', **kwargs)
        except: pass
        
        try:
            if data_type in ["all", "MW vs Charge"]:
                data_type_name = "MW vs Charge"
                defaultValue = "unidec_MWvCharge_{}{}".format(basename, self.config.saveExtension)
                data = unidec_engine_data[data_type_name]

                xvals = data['xvals']
                yvals = data['yvals']
                zvals = data['zvals']
                # reshape data
                xlen = len(xvals)
                ylen = len(yvals)
                zvals = np.reshape(zvals, (xlen, ylen))
                
                # Combine x-axis with data
                save_data = np.column_stack((xvals, zvals)).T
                yvals = map(str, yvals.tolist())
                labels = ["MW(Da)"]
                for label in yvals: labels.append(label)
                
                kwargs = {'default_name':defaultValue}
                self.onSaveData(data=save_data, labels=labels, data_format='%.4f', **kwargs)
        except: pass

    def onShowUnidec(self, evt, plot_type="all"):
        
        if self.itemType == "Mass Spectrum":
            unidec_engine_data = self.currentData['unidec']
        elif self.itemType == "UniDec":
            unidec_engine_data = self.itemData.massSpectrum['unidec']
        elif self.itemType == "Mass Spectrum (processed)":
            unidec_engine_data = self.currentData['unidec']
        elif self.itemType == "UniDec (processed)":
            unidec_engine_data = self.itemData.smoothMS['unidec']
        elif self.itemType == "Mass Spectra" and self.indent == 3:
            title = re.split('UniDec \(', self.extractData)[1][:-1]
            unidec_engine_data = self.itemData.multipleMassSpectrum[title]['unidec']
        elif self.itemType == "Mass Spectra" and self.indent == 4:
            title = re.split('UniDec \(', self.extractParent)[1][:-1]
            unidec_engine_data = self.itemData.multipleMassSpectrum[title]['unidec']

        kwargs = {'show_markers':self.config.unidec_show_markers,
                  'show_individual_lines':self.config.unidec_show_individualComponents,
                  'speedy':self.config.unidec_speedy}
        if plot_type == "all":
            self.presenter.view.panelPlots.on_clear_unidec()
        
        if plot_type in ["all", "Fitted", "Processed"]:
            try: 
                self.presenter.view.panelPlots.on_plot_unidec_MS_v_Fit(unidec_eng_data=None,
                                                                       replot=unidec_engine_data['Fitted'], 
                                                                       **kwargs)
            except: 
                print("Failed to plot MS vs Fit plot")
                try: self.presenter.view.panelPlots.on_plot_unidec_MS(unidec_eng_data=None,
                                                                      replot=unidec_engine_data['Processed'], 
                                                                      **kwargs)
                except: print("Failed to plot MS plot")
        
        if plot_type in ["all", "MW distribution"]: 
            try: 
                self.presenter.view.panelPlots.on_plot_unidec_mwDistribution(unidec_eng_data=None,
                                                                             replot=unidec_engine_data['MW distribution'], 
                                                                             **kwargs)
            except: print("Failed to plot MW distribution plot")
            
        if plot_type in ["all", "m/z vs Charge"]:
            try: 
                self.presenter.view.panelPlots.on_plot_unidec_mzGrid(unidec_eng_data=None,
                                                                     replot=unidec_engine_data['m/z vs Charge'], 
                                                                     **kwargs)
            except: print("Failed to plot m/z vs charge plot")
        
        if plot_type in ["all", "m/z with isolated species"]:
            try: 
                self.presenter.view.panelPlots.on_plot_unidec_individualPeaks(unidec_eng_data=None,
                                                                              replot=unidec_engine_data['m/z with isolated species'], 
                                                                              **kwargs)
            except: print("Failed to plot individual MS plot")
        
        if plot_type in ["all", "MW vs Charge"]:
            try: self.presenter.view.panelPlots.on_plot_unidec_MW_v_Charge(unidec_eng_data=None,
                                                                           replot=unidec_engine_data['MW vs Charge'], 
                                                                           **kwargs)
            except: print("Failed to plot MW vs charge plot")
            
        if plot_type in ["all", "Barchart"]:
            try: self.presenter.view.panelPlots.on_plot_unidec_barChart(unidec_eng_data=None,
                                                                        replot=unidec_engine_data['Barchart'], 
                                                                        **kwargs)
            except: print("Failed to plot barplot")
         
    def onShowPlot(self, evt, data_type=None, save_image=False):
        """ This will send data, plot and change window"""
        if self.itemData == None:
            return
        
        if not evt and data_type:
            pass
        elif isinstance(evt, int):
            evtID = evt
        elif evt == None:
            evtID = None
        else:
            evtID = evt.GetId()
            
        self.presenter.currentDoc = self.itemData.title
        basename = os.path.splitext(self.itemData.title)[0]
        defaultValue = None
        save_kwargs = {}
        #=======================================================================
        #  MASS SPECTRUM
        #=======================================================================
        if any(self.itemType in itemType for itemType in ['Mass Spectrum', 
                                                          'Mass Spectra',
                                                          'Mass Spectrum (processed)']):
            # Select dataset
            if self.extractData == 'Mass Spectra': return
            data = self.GetPyData(self.currentItem)
            try:
                msX = data['xvals']
                msY = data['yvals']
            except TypeError: return

            try: xlimits = data['xlimits']
            except KeyError: 
                xlimits = [self.itemData.parameters['startMS'], 
                           self.itemData.parameters['endMS']]
                
            # plot
            if self.itemData.dataType != 'Type: CALIBRANT':
                self.presenter.view.panelPlots.on_plot_MS(msX, msY, xlimits=xlimits)
                self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['MS'])
                if save_image:
                    if self.itemType == 'Mass Spectrum': 
                        defaultValue = "MS_{}".format(basename)
                    elif self.itemType == 'Mass Spectrum (processed)': 
                        defaultValue = "MS_processed_{}".format(basename)
                    elif self.itemType == 'Mass Spectra' and self.extractData != self.itemType:
                        defaultValue = "MS_{}_{}".format(basename, os.path.splitext(self.extractData)[0]).replace(":", "")
                    save_kwargs = {'image_name':defaultValue}
                    self.presenter.view.panelPlots.save_images(evt=ID_saveMSImage, **save_kwargs)
            else:
                self.presenter.onPlotMSDTCalibration(msX=msX, msY=msY, xlimits=xlimits, plotType='MS')
                self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['Calibration'])
        #=======================================================================
        # 1D IM-MS
        #=======================================================================
        elif any(self.itemType in itemType for itemType in ['Drift time (1D)',
                                                            'Drift time (1D, EIC, DT-IMS)',
                                                            'Drift time (1D, EIC)',
                                                            'Calibration peaks',
                                                            'Calibrants']):
            if self.itemType == 'Drift time (1D)':
                data = self.itemData.DT
                defaultValue = "DT_1D_{}".format(basename)
            elif self.itemType == 'Drift time (1D, EIC, DT-IMS)':
                if self.extractData == 'Drift time (1D, EIC, DT-IMS)': return
                data = self.itemData.IMS1DdriftTimes[self.extractData]
                defaultValue = "DTIMS_1D_{}_{}".format(basename, self.extractData)
            elif self.itemType == 'Drift time (1D, EIC)':
                if self.extractData == 'Drift time (1D, EIC)': return
                data = self.itemData.multipleDT[self.extractData]
                defaultValue = "DT_1D_{}_{}".format(basename, self.extractData)
            elif self.itemType == 'Calibration peaks':
                if self.extractData == 'Calibration peaks': return
                data = self.itemData.calibration[self.extractData]
                defaultValue = "DT_calibrantPeaks_{}_{}".format(basename, self.extractData)
            elif self.itemType == 'Calibrants':
                if self.extractData == 'Calibrants': return
                data = self.itemData.calibrationDataset[self.extractData]['data']
                defaultValue = "DT_calibrants_{}_{}".format(basename, self.extractData)
            
            # Check to see if we should zoom-in on MS peak
            # triggered when clicked on the 1D plot but asking for the MS
            if evtID == ID_showPlotMSDocument and self.itemType == 'Drift time (1D, EIC, DT-IMS)': 
                self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['MS'])
                out = re.split('-|,|', self.extractData)
                startX = str2num(out[0])-self.config.zoomWindowX
                endX = str2num(out[1])+self.config.zoomWindowX
                endY = 1.02
                try:
                    startX = (data['xylimits'][0]-self.config.zoomWindowX)
                    endX = (data['xylimits'][1]+self.config.zoomWindowX)
                    endY = ((self.config.zoomWindowY + data['xylimits'][2])/100)
                except KeyError: pass
                self.presenter.onZoomMS(startX=startX,endX=endX, endY=endY)
                return
            # extract x/y axis values
            dtX = data['xvals']
            dtY = data['yvals']
            if len(dtY) >= 1:
                try:
                    dtY = data['yvalsSum']
                except KeyError: pass
            xlabel = data['xlabels']
            color = self.itemData.lineColour
            style = self.itemData.style
            if self.itemData.dataType != 'Type: CALIBRANT':
                self.presenter.view.panelPlots.on_plot_1D(dtX, dtY, xlabel, color, style)
                self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['1D'])
                if save_image:
                    save_kwargs = {'image_name':defaultValue}
                    self.presenter.view.panelPlots.save_images(evt=ID_save1DImageDoc, **save_kwargs)
            else:
                self.presenter.onPlotMSDTCalibration(dtX=dtX, dtY=dtY, color=color,
                                                     xlabelDT=xlabel, plotType='1DT')
                self.presenter.addMarkerMS(xvals=data['peak'][0], 
                                           yvals=data['peak'][1],
                                           color=self.config.annotColor, 
                                           marker=self.config.markerShape,
                                           size=self.config.markerSize, 
                                           plot='CalibrationDT')
                self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['Calibration'])
        #=======================================================================
        #  Chromatogram
        #=======================================================================
        elif any(self.itemType in itemType for itemType in ['Chromatogram',
                                                            'Chromatograms (EIC)',
                                                            'Chromatograms (combined voltages, EIC)']):
            # Select dataset
            if self.itemType == 'Chromatogram':
                data = self.GetPyData(self.currentItem)
                defaultValue = "RT_{}".format(basename)
            elif self.itemType == 'Chromatograms (combined voltages, EIC)':
                if self.extractData == 'Chromatograms (combined voltages, EIC)': return
                data = self.GetPyData(self.currentItem)
                defaultValue = "RT_CV_{}_{}".format(basename, self.extractData)
            elif self.itemType == 'Chromatograms (EIC)':
                if self.extractData == 'Chromatograms (EIC)': return
                data = self.GetPyData(self.currentItem)
                defaultValue = "RT_{}_{}".format(basename, self.extractData)
            # Unpack data
            rtX = data['xvals']
            rtY = data['yvals']
            xlabel = data['xlabels']
            # Change panel and plot 
            self.presenter.view.panelPlots.on_plot_RT(rtX, rtY, xlabel)
            self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['RT'])
            if save_image:
                save_kwargs = {'image_name':defaultValue}
                self.presenter.view.panelPlots.save_images(evt=ID_saveRTImageDoc, **save_kwargs)
        #=======================================================================
        #  2D IM-MS
        #=======================================================================
        elif any(self.itemType in itemType for itemType in ['Drift time (2D)', 
                                                            'Drift time (2D, processed)',
                                                            'Drift time (2D, EIC)',
                                                            'Drift time (2D, combined voltages, EIC)',
                                                            'Drift time (2D, processed, EIC)',
                                                            'Input data']):
            # check appropriate data is selected
            if self.itemType == 'Drift time (2D, EIC)':
                if self.extractData == 'Drift time (2D, EIC)': return
                defaultValue = "DT_2D_{}_{}".format(basename, self.extractData)
            elif self.itemType == 'Drift time (2D, combined voltages, EIC)':
                if self.extractData == 'Drift time (2D, combined voltages, EIC)': return
                defaultValue = "DT_2D_CV_{}_{}".format(basename, self.extractData)
            elif self.itemType == 'Drift time (2D, processed, EIC)':
                if self.extractData == 'Drift time (2D, processed, EIC)': return
                defaultValue = "DT_2D_processed_{}_{}".format(basename, self.extractData)
            elif self.itemType == 'Input data':
                if self.extractData == 'Input data': return
                defaultValue = "DT_2D_{}_{}".format(basename, self.extractData)
            elif self.itemType == 'Statistical':
                if self.extractData == 'Statistical': return
                defaultValue = "DT_2D_{}_{}".format(basename, self.extractData)
            elif self.itemType == 'Drift time (2D)':
                defaultValue = "DT_2D_{}".format(basename)
            elif self.itemType == 'Drift time (2D, processed)': 
                defaultValue = "DT_2D_processed_{}".format(basename)
            else:
                self.presenter.view.SetStatusText('No data found', 3)
                return
            
            # get data for selected item
            data = self.GetPyData(self.currentItem)
            if evtID == ID_showPlotMSDocument:
                out = re.split('-|,| ', self.extractData)
                try:
                    startX = str2num(out[0])-self.config.zoomWindowX
                    endX = str2num(out[1])+self.config.zoomWindowX
                except TypeError:
                    return          
                self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['MS'])
                endY = 1.05
                try:
                    startX = (data['xylimits'][0]-self.config.zoomWindowX)
                    endX = (data['xylimits'][1]+self.config.zoomWindowX)
                    endY = (data['xylimits'][2]/100)
                except KeyError: pass
                self.presenter.onZoomMS(startX=startX,endX=endX, endY=endY)
                return
            elif evtID == ID_showPlot1DDocument: 
                self.presenter.onPlot1DIMS2(data['yvals'], # normally this would be the y-axis
                                            data['yvals1D'], 
                                            data['ylabels']) # data was rotated so using ylabel for xlabel
                self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['1D'])
                return
            elif evtID == ID_showPlotRTDocument: 
                self.presenter.onPlotRT2(data['xvals'], 
                                         data['yvalsRT'], 
                                         data['xlabels'])
                self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['RT'])
                return
            else: pass
            # Unpack data
            if len(data) == 0: return
            
            dataOut = self.presenter.get2DdataFromDictionary(dictionary=data, dataType='plot', compact=True)
            # Change panel and plot data
            self.presenter.view.panelPlots.on_plot_2D_data(data=dataOut)
            self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['2D'])
            if save_image:
                save_kwargs = {'image_name':defaultValue}
                self.presenter.view.panelPlots.save_images(evt=ID_save2DImageDoc, **save_kwargs)
        #=======================================================================
        #  OVERLAY PLOTS
        #=======================================================================
        elif self.itemType == 'Overlay':
            if self.extractData == 'Overlay': return
            # Determine type
            out = re.split('-|,|__|:', self.extractData)
            data = self.itemData.IMS2DoverlayData.get(self.extractData, {})
            if len(data) == 0:
                keys = self.itemData.IMS2DoverlayData.keys()
                for key in keys:
                    if self.extractData in key:
                        self.extractData = key
                        data = self.itemData.IMS2DoverlayData.get(self.extractData, {})
            
            if out[0] == "Grid (n x n)":
                defaultValue = "Overlay_Grid_NxN_{}".format(basename)
                self.presenter.view.panelPlots.on_plot_n_grid(data['zvals_list'], 
                                                              data['cmap_list'], 
                                                              data['title_list'], 
                                                              data['xvals'], 
                                                              data['yvals'], 
                                                              data['xlabels'], 
                                                              data['ylabels'])
                self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['Overlay'])
                if save_image:
                    save_kwargs = {'image_name':defaultValue}
                    self.presenter.view.panelPlots.save_images(evt=ID_saveOverlayImageDoc, **save_kwargs)
            elif out[0] == "Grid (2":
                defaultValue = "Overlay_Grid_2to1_{}".format(basename)
                self.presenter.view.panelPlots.on_plot_grid(data['zvals_1'], 
                                                            data['zvals_2'], 
                                                            data['zvals_cum'], 
                                                            data['xvals'], 
                                                            data['yvals'], 
                                                            data['xlabels'], 
                                                            data['ylabels'], 
                                                            data['cmap_1'], 
                                                            data['cmap_2'])
                self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['Overlay'])
                
                # Add RMSD label
                rmsdXpos, rmsdYpos = self.presenter.onCalculateRMSDposition(xlist=data['xvals'], ylist=data['yvals'])
                if rmsdXpos != None and rmsdYpos != None:
                    self.presenter.addTextRMSD(rmsdXpos,rmsdYpos, data['rmsdLabel'], 0, plot='Grid')
                    
                if save_image:
                    save_kwargs = {'image_name':defaultValue}
                    self.presenter.view.panelPlots.save_images(evt=ID_saveOverlayImageDoc, **save_kwargs)
            elif (out[0] == 'Mask'  or out[0] == 'Transparent'):
                zvals1, zvals2, cmap1, cmap2, alpha1, alpha2, __, __, xvals, yvals, xlabels, ylabels = self.presenter.getOverlayDataFromDictionary(dictionary=data,
                                                                                                                                           dataType='plot',
                                                                                                                                           compact=False)
                if out[0] == 'Mask': 
                    defaultValue = "Overlay_mask_{}".format(basename)
                    self.presenter.onPlotOverlayMultipleIons2(zvalsIon1=zvals1,cmapIon1=cmap1,
                                                              alphaIon1=1, zvalsIon2=zvals2, 
                                                              cmapIon2=cmap2, alphaIon2=1,
                                                              xvals=xvals,yvals=yvals, 
                                                              xlabel=xlabels, ylabel=ylabels,
                                                              flag='Text')
                elif out[0] == 'Transparent':
                    defaultValue = "Overlay_transparent_{}".format(basename)
                    self.presenter.onPlotOverlayMultipleIons2(zvalsIon1=zvals1,cmapIon1=cmap1,
                                                              alphaIon1=alpha1,zvalsIon2=zvals2, 
                                                              cmapIon2=cmap2,  alphaIon2=alpha2,
                                                              xvals=xvals, yvals=yvals, 
                                                              xlabel=xlabels, ylabel=ylabels,
                                                              flag='Text')
                # Change window view
                self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['Overlay'])
                if save_image:
                    save_kwargs = {'image_name':defaultValue}
                    self.presenter.view.panelPlots.save_images(evt=ID_saveOverlayImageDoc, **save_kwargs)
                    
            elif out[0] == 'RMSF': 
                zvals, yvalsRMSF, xvals, yvals, xlabelRMSD, ylabelRMSD, ylabelRMSF, color, cmap, rmsdLabel = self.presenter.get2DdataFromDictionary(dictionary=data,
                                                                                                                              plotType='RMSF',
                                                                                                                              compact=True)
                defaultValue = "Overlay_RMSF_{}".format(basename)
                self.presenter.view.panelPlots.on_plot_RMSDF(yvalsRMSF=yvalsRMSF, 
                                                             zvals=zvals, 
                                                             xvals=xvals, 
                                                             yvals=yvals, 
                                                             xlabelRMSD=xlabelRMSD, 
                                                             ylabelRMSD=ylabelRMSD,
                                                             ylabelRMSF=ylabelRMSF,
                                                             color=color, 
                                                             cmap=cmap, 
                                                             plotType="RMSD")
                # Add RMSD label
                rmsdXpos, rmsdYpos = self.presenter.onCalculateRMSDposition(xlist=xvals, ylist=yvals)
                if rmsdXpos != None and rmsdYpos != None:
                    self.presenter.addTextRMSD(rmsdXpos,rmsdYpos, rmsdLabel, 0, plot='RMSF')
                    
                self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['RMSF'])
                if save_image:
                    save_kwargs = {'image_name':defaultValue}
                    self.presenter.view.panelPlots.save_images(evt=ID_saveRMSFImageDoc, **save_kwargs)
            
            elif out[0] == 'RGB':
                defaultValue = "Overlay_RGB_{}".format(basename)
                data = self.GetPyData(self.currentItem)
                rgb_plot, xAxisLabels, xlabel, yAxisLabels, ylabel, __ = \
                self.presenter.get2DdataFromDictionary(dictionary=data, plotType='2D', compact=False)
                legend_text = data['legend_text']
                
                self.presenter.plot2D_rgb(rgb_plot, xAxisLabels, yAxisLabels, xlabel,
                                          ylabel, legend_text, evt=None)
                self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['2D'])
                if save_image:
                    save_kwargs = {'image_name':defaultValue}
                    self.presenter.view.panelPlots.save_images(evt=ID_save2DImageDoc, **save_kwargs)
                
            elif out[0] == 'RMSD':
                defaultValue = "Overlay_RMSD_{}".format(basename)
                zvals, xaxisLabels, xlabel, yaxisLabels, ylabel, rmsdLabel, cmap = self.presenter.get2DdataFromDictionary(dictionary=data,
                                                                                                                          plotType='RMSD',
                                                                                                                          compact=True)
                self.presenter.view.panelPlots.on_plot_RMSD(zvals, xaxisLabels, yaxisLabels, xlabel, ylabel, 
                                                             cmap, plotType="RMSD")
                self.presenter.onPlot3DIMS(zvals=zvals, labelsX=xaxisLabels, labelsY=yaxisLabels, 
                                           xlabel=xlabel, ylabel=ylabel, zlabel='Intensity', 
                                           cmap=cmap)
                # Add RMSD label
                rmsdXpos, rmsdYpos = self.presenter.onCalculateRMSDposition(xlist=xaxisLabels,
                                                                            ylist=yaxisLabels)
                if rmsdXpos != None and rmsdYpos != None:
                    self.presenter.addTextRMSD(rmsdXpos,rmsdYpos, rmsdLabel, 0, plot='RMSD')
                    
                self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['RMSF'])
                if save_image:
                    save_kwargs = {'image_name':defaultValue}
                    self.presenter.view.panelPlots.save_images(evt=ID_saveRMSDImageDoc, **save_kwargs)
            elif out[0] in ["Waterfall (Raw)", "Waterfall (Processed)", "Waterfall (Fitted)",
                            "Waterfall (Deconvoluted MW)", "Waterfall (Charge states)"]:
                if out[0] == "Waterfall (Raw)":
                    defaultValue = "MS_Waterfall_raw_{}".format(basename)
                elif out[0] == "Waterfall (Processed)":
                    defaultValue = "MS_Waterfall_processed_{}".format(basename)
                elif out[0] == "Waterfall (Fitted)":
                    defaultValue = "MS_Waterfall_fitted_{}".format(basename)
                elif out[0] == "Waterfall (Deconvoluted MW)":
                    defaultValue = "MS_Waterfall_deconvolutedMW_{}".format(basename)
                elif out[0] == "Waterfall (Charge states)":
                    defaultValue = "MS_Waterfall_charges_{}".format(basename)
                
                
                self.presenter.view.panelPlots.on_plot_waterfall(data['xvals'], 
                                                                 data['yvals'], None, 
                                                                 colors=data['colors'], 
                                                                 xlabel=data['xlabel'], 
                                                                 ylabel=data['ylabel'], 
                                                                 **data['waterfall_kwargs'])
                self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['Waterfall'])
                if save_image:
                    save_kwargs = {'image_name':defaultValue}
                    self.presenter.view.panelPlots.save_images(evt=ID_saveWaterfallImageDoc, **save_kwargs)
                
            # Overlayed 1D data
            elif out[0] == u'1D' or out[0] == u'RT': 
                xvals, yvals, xlabels, colors, labels, xlimits = self.presenter.get2DdataFromDictionary(dictionary=data,
                                                                                                        plotType='Overlay1D',
                                                                                                        compact=True)
                if out[0] == '1D':
                    defaultValue = "Overlay_DT_1D_{}".format(basename)
                    self.presenter.onOverlayDT(xvals=xvals, yvals=yvals, xlabel=xlabels, colors=colors,
                                               xlimits=xlimits, labels=labels)
                    self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['1D'])
                    if save_image:
                        save_kwargs = {'image_name':defaultValue}
                        self.presenter.view.panelPlots.save_images(evt=ID_save1DImageDoc, **save_kwargs)
                elif out[0] == 'RT':
                    defaultValue = "Overlay_RT_{}".format(basename)
                    self.presenter.onOverlayRT(xvals=xvals, yvals=yvals, xlabel=xlabels, colors=colors,
                                               xlimits=xlimits, labels=labels)
                    self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['RT'])
                    if save_image:
                        save_kwargs = {'image_name':defaultValue}
                        self.presenter.view.panelPlots.save_images(evt=ID_saveRTImageDoc, **save_kwargs)
                
        elif self.itemType == 'Statistical':
            if self.extractData == 'Statistical': 
                return
            out = self.extractData.split(':')
            data = self.itemData.IMS2DstatsData[self.extractData]
            # Variance, Mean, Std Dev are of the same format
            if out[0] in ['Variance', 'Mean', 'Standard Deviation']:
                if out[0] == "Variance":
                    defaultValue = "Overlay_variance_{}".format(basename)
                elif out[0] == "Mean":
                    defaultValue = "Overlay_mean_{}".format(basename)
                elif out[0] == "Standard Deviation":
                    defaultValue = "Overlay_std_{}".format(basename)
                    
                # Unpack data
                dataOut = self.presenter.get2DdataFromDictionary(dictionary=data,
                                                                 dataType='plot',
                                                                 compact=True)
                # Change panel and plot data
                self.presenter.plot2Ddata2(data=dataOut)
                self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['2D'])
                if save_image:
                    save_kwargs = {'image_name':defaultValue}
                    self.presenter.view.panelPlots.save_images(evt=ID_save2DImageDoc, **save_kwargs)
            
            elif out[0] == 'RMSD Matrix': 
                defaultValue = "Overlay_matrix_{}".format(basename)
                zvals, yxlabels, cmap = self.presenter.get2DdataFromDictionary(dictionary=data,
                                                                               plotType='Matrix',
                                                                               compact=False)
                self.presenter.view.panelPlots.on_plot_matrix(zvals=zvals, xylabels=yxlabels, cmap=cmap)
                self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['Comparison'])
                if save_image:
                    save_kwargs = {'image_name':defaultValue}
                    self.presenter.view.panelPlots.save_images(evt=ID_saveRMSDmatrixImageDoc, **save_kwargs)
        elif self.itemType == 'DT/MS' or evtID in [ID_ylabelDTMSbins, ID_ylabelDTMSms, ID_ylabelDTMSrestore]:
            defaultValue = "DTMS_{}".format(basename)
            data = self.GetPyData(self.currentItem)
            self.presenter.onPlotMZDT(data['zvals'], data['xvals'], data['yvals'], 
                                      data['xlabels'], data['ylabels'])
            self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['MZDT'])
            if save_image:
                self.presenter.view.panelPlots.save_images(evt=ID_saveMZDTImageDoc, **save_kwargs)
        else: 
            return

    def onSaveDF(self, evt):
        
        print('Saving dataframe...')
        tstart = time.time()
        
        if self.itemType == 'Mass Spectra' and self.extractData == 'Mass Spectra':
            dataframe = self.itemData.massSpectraSave
            if len(self.itemData.massSpectraSave) == 0:
                msFilenames = ["m/z"]
                for i, key in enumerate(self.itemData.multipleMassSpectrum):
                    msY = self.itemData.multipleMassSpectrum[key]['yvals']
                    if self.config.normalizeMultipleMS:
                        msY = msY/max(msY)
                    msFilenames.append(key)
                    if i == 0:
                        tempArray = msY
                    else:
                        tempArray = np.concatenate((tempArray, msY), axis=0)
                try:
                    # Form pandas dataframe
                    msX = self.itemData.multipleMassSpectrum[key]['xvals']
                    combMSOut = np.concatenate((msX, tempArray), axis=0)
                    combMSOut = combMSOut.reshape((len(msY), int(i+2)), order='F') 
                    dataframe = pd.DataFrame(data=combMSOut, columns=msFilenames)
                except: self.presenter.view.SetStatusText('Mass spectra are not of the same size. Please export each item separately', 3)
            try:
                # Save data
                if evt.GetId() == ID_saveData_csv:
                    filename = self.presenter.getImageFilename(defaultValue='MS_multiple', withPath=True, extension=self.config.saveExtension)
                    if filename is None: return
                    dataframe.to_csv(path_or_buf=filename, 
                                     sep=self.config.saveDelimiter,
                                     header=True, index=True)
                elif evt.GetId() == ID_saveData_pickle:
                    filename = self.presenter.getImageFilename(defaultValue='MS_multiple', withPath=True, extension='.pickle')
                    if filename is None: return
                    dataframe.to_pickle(path=filename, protocol=2)
                elif evt.GetId() == ID_saveData_excel:
                    filename = self.presenter.getImageFilename(defaultValue='MS_multiple', withPath=True, extension='.xlsx')
                    if filename is None: return
                    dataframe.to_excel(excel_writer=filename, sheet_name='data')
                elif evt.GetId() == ID_saveData_hdf:
                    filename = self.presenter.getImageFilename(defaultValue='MS_multiple', withPath=True, extension='.h5')
                    if filename is None: return
                    dataframe.to_hdf(path_or_buf=filename, key='data')
                
                print('Dataframe was saved in %s. It took: %s s.' % (filename, str(np.round(time.time()-tstart, 4))))
            except AttributeError:
                args = ("This document does not have correctly formatted MS data. Please export each item separately", 4) 
                self.presenter.onThreading(None, args, action='updateStatusbar')

    def onSaveData(self, data=None, labels=None, data_format='%.4f', **kwargs):
        """
        Helper function to save data in consistent manner
        """
        wildcard = "CSV (Comma delimited) (*.csv)|*.csv|" + \
                   "Text (Tab delimited) (*.txt)|*.txt|" + \
                   "Text (Space delimited (*.txt)|*.txt"
                   
        wildcard_dict = {',':0, '\t':1, ' ':2}
        dlg =  wx.FileDialog(self.presenter.view, "Please select a name for the file", 
                             "", "", wildcard=wildcard, style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        dlg.CentreOnParent()
        dlg.SetFilename(kwargs.get("default_name", ""))
        
        try: 
            dlg.SetFilterIndex(wildcard_dict[self.config.saveDelimiter])
        except: 
            pass
        
        if not kwargs.get("return_filename", False):
            if dlg.ShowModal() == wx.ID_OK:
                filename = dlg.GetPath()
                __, extension = os.path.splitext(filename)
                self.config.saveExtension = extension
                self.config.saveDelimiter = wildcard_dict.keys()[wildcard_dict.values().index(dlg.GetFilterIndex())]
                saveAsText(filename=filename, 
                           data=data, 
                           format=data_format,
                           delimiter=self.config.saveDelimiter,
                           header=self.config.saveDelimiter.join(labels))
            else:
                print("Cancelled operation")
        else:
            if dlg.ShowModal() == wx.ID_OK:
                path = dlg.GetPath()
                basename, extension = os.path.splitext(filename)
            
                return path, basename, extension
            else:
                return None, None, None
        
    def onSaveCSV(self, evt):
        """
        This function extracts the 1D or 2D data and saves it in a CSV format
        """
        if self.itemData == None:
            return
        
        saveFileName = None
        basename = os.path.splitext(self.itemData.title)[0]
        # Save MS - single
        if (self.itemType == 'Mass Spectrum' or self.itemType == 'Mass Spectrum (processed)' or
            self.itemType == 'Mass Spectra' and self. extractData != self.itemType):
            # Default name
            defaultValue = 'MSout'
            # Saves MS to file. Automatically removes values with 0s from the array
            # Get data
            if self.itemType == 'Mass Spectrum':
                data = self.itemData.massSpectrum
                defaultValue = "MS_{}{}".format(basename, self.config.saveExtension)
            elif self.itemType == 'Mass Spectrum (processed)':
                data = self.itemData.smoothMS
                defaultValue = "MS_processed_{}{}".format(basename, self.config.saveExtension)
            elif self.itemType == 'Mass Spectra' and self.extractData != self.itemType:
                data = self.itemData.multipleMassSpectrum[self.extractData]
                extractBasename = os.path.splitext(self.extractData)[0]
                defaultValue = "MS_{}_{}{}".format(basename, extractBasename, self.config.saveExtension).replace(":", "")
            
            # Extract MS and find where items are equal to 0 = to reduce filesize
            msX = data['xvals']
            msXzero = np.where(msX == 0)[0]
            msY = data['yvals']
            msYzero = np.where(msY == 0)[0]
            # Find which index to use for removal
            removeIdx = np.concatenate((msXzero, msYzero), axis=0)
            msXnew = np.delete(msX, removeIdx)
            msYnew = np.delete(msY, removeIdx)            
            
            kwargs = {'default_name':defaultValue}
            data = [msXnew,msYnew]
            labels = ['m/z','Intensity']
            self.onSaveData(data=data, labels=labels, 
                            data_format='%.4f', **kwargs)

                
        # Save MS - multiple MassLynx fiels
        elif self.itemType == 'Mass Spectra' and self.extractData == 'Mass Spectra':
            for key in self.itemData.multipleMassSpectrum:
                stripped_key_name = key.replace(" ","").replace(".csv","").replace(".txt","").replace(".raw","").replace(".d","")
                defaultValue = "MS_{}_{}{}".format(basename, stripped_key_name, self.config.saveExtension)
                msX = self.itemData.multipleMassSpectrum[key]['xvals']
                msY = self.itemData.multipleMassSpectrum[key]['yvals']
                # Extract MS and find where items are equal to 0 = to reduce filesize
                msXzero = np.where(msX == 0)[0]
                msYzero = np.where(msY == 0)[0]
                # Find which index to use for removal
                removeIdx = np.concatenate((msXzero, msYzero), axis=0)
                msXnew = np.delete(msX, removeIdx)
                msYnew = np.delete(msY, removeIdx)      
                xlabel = "m/z(Da)"
                data = [msXnew,msYnew]
                kwargs = {'default_name':defaultValue}
                self.onSaveData(data=data, labels=[xlabel,'Intensity'], 
                                data_format='%.4f', **kwargs)               
                                 
        # Save calibration parameters - single
        elif self.itemType == 'Calibration Parameters':
            if evt.GetId() == ID_saveDataCSVDocument:
                saveFileName = self.presenter.getImageFilename(prefix=True, csv=True, 
                                                               defaultValue='calibrationTable')
                if saveFileName =='' or saveFileName == None: 
                    saveFileName = 'calibrationTable'

            filename = ''.join([self.itemData.path, '\\', saveFileName, self.config.saveExtension])
            
            df = self.itemData.calibrationParameters['dataframe']
            df.to_csv(path_or_buf=filename, sep=self.config.saveDelimiter)
            
        # Save RT - single
        elif self.itemType == 'Chromatogram':
            if evt.GetId() == ID_saveDataCSVDocument:
                defaultValue = "RT_{}{}".format(basename, self.config.saveExtension)
                rtX = self.itemData.RT['xvals']
                rtY = self.itemData.RT['yvals']
                xlabel = self.itemData.RT['xlabels'] 
                kwargs = {'default_name':defaultValue}
                self.onSaveData(data=[rtX,  rtY], labels=[xlabel,'Intensity'], 
                                data_format='%.4f', **kwargs)                

            
        # Save 1D - single
        elif self.itemType == 'Drift time (1D)':
            if evt.GetId() == ID_saveDataCSVDocument:
                defaultValue = "DT_1D_{}{}".format(basename, self.config.saveExtension)
                dtX = self.itemData.DT['xvals']
                dtY = self.itemData.DT['yvals']
                ylabel = self.itemData.DT['xlabels']
                kwargs = {'default_name':defaultValue}
                self.onSaveData(data=[dtX,dtY], labels=[ylabel,'Intensity'], 
                                data_format='%.2f', **kwargs)   
            
        # Save RT (combined voltages) - batch + single
        elif self.itemType == 'Chromatograms (combined voltages, EIC)':
            # Batch mode
            if self.extractData == 'Chromatograms (combined voltages, EIC)':
                for key in self.itemData.IMSRTCombIons:
                    stripped_key_name = key.replace(" ","")
                    defaultValue = "RT_{}_{}{}".format(basename, stripped_key_name, self.config.saveExtension)
                    rtX = self.itemData.IMSRTCombIons[key]['xvals']
                    rtY = self.itemData.IMSRTCombIons[key]['yvals']
                    xlabel = self.itemData.IMSRTCombIons[key]['xlabels']
                    kwargs = {'default_name':defaultValue}
                    self.onSaveData(data=[rtX,rtY], labels=[xlabel,'Intensity'], 
                                    data_format='%.4f', **kwargs)   
#             # Single mode
            else:
                defaultValue = "RT_{}_{}{}".format(basename, self.extractData, self.config.saveExtension)
                rtX = self.itemData.IMSRTCombIons[self.extractData]['xvals']
                rtY = self.itemData.IMSRTCombIons[self.extractData]['yvals']
                xlabel = self.itemData.IMSRTCombIons[self.extractData]['xlabels']
                kwargs = {'default_name':defaultValue}
                self.onSaveData(data=[rtX,rtY], labels=[xlabel,'Intensity'], 
                                data_format='%.4f', **kwargs)   
                   
        # Save 1D - batch + single
        elif self.itemType == 'Drift time (1D, EIC, DT-IMS)':
            if evt.GetId() == ID_saveDataCSVDocument:
                saveFileName = self.presenter.getImageFilename(prefix=True, csv=True, 
                                                               defaultValue='DT_1D_')
                if saveFileName =='' or saveFileName == None: 
                    saveFileName = 'DT_1D_'
            # Batch mode
            if self.extractData == 'Drift time (1D, EIC, DT-IMS)': 
                for key in self.itemData.IMS1DdriftTimes:
                    if self.itemData.dataType == 'Type: MANUAL':
                        name = re.split(', File: |.raw', key)
                        filename = ''.join([self.itemData.path,'\\', saveFileName, 
                                            name[0],'_',name[1], 
                                            self.config.saveExtension])
                        dtX = self.itemData.IMS1DdriftTimes[key]['xvals']
                        dtY = self.itemData.IMS1DdriftTimes[key]['yvals']
                        xlabel = self.itemData.IMS1DdriftTimes[key]['xlabels']
                        saveAsText(filename=filename, 
                                   data=[dtX,dtY], 
                                   format='%.4f',
                                   delimiter=self.config.saveDelimiter,
                                   header=self.config.saveDelimiter.join([xlabel,'Intensity']))
                    else:
                        filename = ''.join([self.itemData.path,'\\', saveFileName, 
                                            key, self.config.saveExtension])
                        zvals = self.itemData.IMS1DdriftTimes[key]['yvals']
                        yvals = self.itemData.IMS1DdriftTimes[key]['xvals']
                        xvals = np.asarray(self.itemData.IMS1DdriftTimes[key]['driftVoltage']) 
                        # Y-axis labels need a value for [0,0]
                        yvals = np.insert(yvals, 0, 0) # array, index, value
                        # Combine x-axis with data
                        saveData = np.vstack((xvals, zvals.T))
                        saveData = np.vstack((yvals, saveData.T))
                        # Save data
                        saveAsText(filename=filename, 
                                   data=saveData, 
                                   format='%.2f',
                                   delimiter=self.config.saveDelimiter,
                                   header="")
            
            # Single mode
            else:
                if self.itemData.dataType == 'Type: MANUAL':
                    name = re.split(', File: |.raw', self.extractData)
                    filename = ''.join([self.itemData.path,'\\', saveFileName, 
                                        name[0],'_',name[1], 
                                        self.config.saveExtension])
                    dtX = self.itemData.IMS1DdriftTimes[self.extractData]['xvals']
                    dtY = self.itemData.IMS1DdriftTimes[self.extractData]['yvals']
                    xlabel = self.itemData.IMS1DdriftTimes[self.extractData]['xlabels']
                    saveAsText(filename=filename, 
                               data=[dtX,dtY], 
                               format='%.4f',
                               delimiter=self.config.saveDelimiter,
                               header=self.config.saveDelimiter.join([xlabel,'Intensity']))
                else:
                    filename = ''.join([self.itemData.path,'\\', saveFileName, 
                                        self.extractData, 
                                        self.config.saveExtension])
                    zvals = self.itemData.IMS1DdriftTimes[self.extractData]['yvals']
                    yvals = self.itemData.IMS1DdriftTimes[self.extractData]['xvals']
                    xvals = np.asarray(self.itemData.IMS1DdriftTimes[self.extractData].get('driftVoltage', " "))   
                    # Y-axis labels need a value for [0,0]
                    yvals = np.insert(yvals, 0, 0) # array, index, value
                    # Combine x-axis with data
                    saveData = np.vstack((xvals, zvals.T))
                    saveData = np.vstack((yvals, saveData.T))
                    saveAsText(filename=filename, 
                               data=saveData, 
                               format='%.2f',
                               delimiter=self.config.saveDelimiter,
                               header="")
        # Save DT/MS
        elif self.itemType == 'DT/MS':
            data = self.GetPyData(self.currentItem)
            zvals = data['zvals']
            xvals = data['xvals']
            yvals = data['yvals']

            if evt.GetId() == ID_saveDataCSVDocument:
                defaultValue = "MSDT_{}{}".format(basename, self.config.saveExtension)
                saveData = np.vstack((yvals, zvals.T))
                xvals = map(str, xvals.tolist())
                labels = ["DT"]
                for label in xvals: labels.append(label)
                # Save 2D array
                kwargs = {'default_name':defaultValue}
                self.onSaveData(data=[saveData], labels=labels, 
                                data_format='%.2f', **kwargs)           

        # Save 1D/2D - batch + single
        elif any(self.itemType in itemType for itemType in ['Drift time (2D)',
                                                            'Drift time (2D, processed)',
                                                            'Drift time (2D, EIC)',
                                                            'Drift time (2D, combined voltages, EIC)',
                                                            'Drift time (2D, processed, EIC)',
                                                            'Input data', 
                                                            'Statistical']):
            # Select dataset
            if self.itemType in ['Drift time (2D)', 'Drift time (2D, processed)']:
                if self.itemType == 'Drift time (2D)':
                    data = self.itemData.IMS2D
                    defaultValue = "DT_2D_raw_{}{}".format(basename, self.config.saveExtension)
                    
                elif self.itemType == 'Drift time (2D, processed)':
                    data = self.itemData.IMS2Dprocess
                    defaultValue = "DT_2D_processed_{}{}".format(basename, self.config.saveExtension)
                    
                # Save 2D
                if evt.GetId() == ID_saveDataCSVDocument:
                    # Prepare data for saving
                    zvals, xvals, xlabel, yvals, ylabel, __ = self.presenter.get2DdataFromDictionary(dictionary=data,
                                                                                                       dataType='plot',
                                                                                                       compact=False)
                    saveData = np.vstack((yvals, zvals.T))
                    xvals = map(str, xvals.tolist())
                    labels = ["DT"]
                    for label in xvals: labels.append(label)
                    # Save 2D array
                    kwargs = {'default_name':defaultValue}
                    self.onSaveData(data=[saveData], labels=labels, 
                                    data_format='%.2f', **kwargs)

                # Save 1D
                elif evt.GetId() == ID_saveDataCSVDocument1D:
                    if self.itemType == 'Drift time (2D)':
                        defaultValue = "DT_1D_raw_{}{}".format(basename, self.config.saveExtension)
                        
                    elif self.itemType == 'Drift time (2D, processed)':
                        defaultValue = "DT_1D_processed_{}{}".format(basename, self.config.saveExtension)
                    # Get data from the document
                    dtX = data['yvals']
                    ylabel = data['xlabels']
                    try: dtY = data['yvals1D']
                    except KeyError: 
                        msg = 'Missing data. Cancelling operation.'
                        self.presenter.view.SetStatusText(msg, 3)
                        return
                    kwargs = {'default_name':defaultValue}
                    self.onSaveData(data=[dtX,dtY], labels=[ylabel,'Intensity'], 
                                    data_format='%.4f', **kwargs)   
                    
            # Save 1D/2D - single + batch
            elif any(self.itemType in itemType for itemType in ['Drift time (2D, EIC)',
                                                                'Drift time (2D, combined voltages, EIC)',
                                                                'Drift time (2D, processed, EIC)',
                                                                'Input data', 'Statistical']):
                # Save 1D/2D - batch
                if any(self.extractData in extractData for extractData in ['Drift time (2D, EIC)',
                                                                           'Drift time (2D, combined voltages, EIC)',
                                                                           'Drift time (2D, processed, EIC)',
                                                                           'Input data', 'Statistical']):
                    name_modifier = ""
                    if self.itemType == 'Drift time (2D, EIC)':
                        data = self.itemData.IMS2Dions
                    elif self.itemType == 'Drift time (2D, combined voltages, EIC)':
                        data = self.itemData.IMS2DCombIons
                        name_modifier = "_CV_"
                    elif self.itemType == 'Drift time (2D, processed, EIC)':
                        data = self.itemData.IMS2DionsProcess
                    elif self.itemType == 'Input data':
                        data = self.itemData.IMS2DcompData
                    elif self.itemType == 'Statistical':
                        data = self.itemData.IMS2DstatsData
                                                    
                    # 2D - batch
                    if evt.GetId() == ID_saveDataCSVDocument:
                        # Iterate over dictionary    
                        for key in data:
                            stripped_key_name = key.replace(" ","")
                            defaultValue = "DT_2D_{}_{}{}{}".format(basename, name_modifier, stripped_key_name, self.config.saveExtension)
                            # Prepare data for saving
                            zvals, xvals, xlabel, yvals, ylabel, __ = self.presenter.get2DdataFromDictionary(dictionary=data[key],
                                                                                                             dataType='plot',compact=False)
                            saveData = np.vstack((yvals, zvals.T))
                            xvals = map(str, xvals.tolist())
                            labels = ["DT"]
                            for label in xvals: labels.append(label)
                            # Save 2D array
                            kwargs = {'default_name':defaultValue}
                            self.onSaveData(data=[saveData], labels=labels, 
                                            data_format='%.2f', **kwargs)
                    # 1D - batch
                    elif evt.GetId() == ID_saveDataCSVDocument1D:
                        if not (self.itemType == 'Input data'
                            or self.itemType == 'Statistical'): 
                            for key in data:
                                stripped_key_name = key.replace(" ","")
                                defaultValue = "DT_1D_{}_{}{}{}".format(basename, name_modifier, stripped_key_name, self.config.saveExtension)
                                # Get data from the document
                                dtX = data[key]['yvals']
                                ylabel = data[key]['xlabels']
                                try: dtY = data[key]['yvals1D']
                                except KeyError: 
                                    msg = 'Missing data. Cancelling operation.'
                                    self.presenter.view.SetStatusText(msg, 3)
                                    continue
                                kwargs = {'default_name':defaultValue}
                                self.onSaveData(data=[dtX,dtY], labels=[ylabel,'Intensity'], 
                                                data_format='%.4f', **kwargs)
                    
                # Save 1D/2D - single
                else:
                    name_modifier = ""
                    if self.itemType == 'Drift time (2D, EIC)':
                        data = self.itemData.IMS2Dions
                    elif self.itemType == 'Drift time (2D, combined voltages, EIC)':
                        data = self.itemData.IMS2DCombIons
                        name_modifier = "_CV_"
                    elif self.itemType == 'Drift time (2D, processed, EIC)':
                        data = self.itemData.IMS2DionsProcess
                    elif self.itemType == 'Input data':
                        data = self.itemData.IMS2DcompData
                    elif self.itemType == 'Statistical':
                        data = self.itemData.IMS2DstatsData
                    # Save RMSD matrix
                    out = self.extractData.split(':')
                    if out[0] == 'RMSD Matrix':
                        if evt.GetId() == ID_saveDataCSVDocument:
                            saveFileName = self.presenter.getImageFilename(prefix=True, csv=True, 
                                                                           defaultValue='DT_')
                        if saveFileName =='' or saveFileName == None: 
                            saveFileName = 'DT_'
                                
                        # Its a bit easier to save data with text labels using pandas df, 
                        # so data is reshuffled to pandas dataframe and then saved
                        # in a standard .csv format
                        filename = ''.join([self.itemData.path,'\\', saveFileName, self.extractData, self.config.saveExtension])
                        zvals, xylabels, __ = self.presenter.get2DdataFromDictionary(dictionary=data[self.extractData],
                                                                                       plotType='Matrix',compact=False)
                        saveData = pd.DataFrame(data=zvals, index=xylabels, columns=xylabels)
                        saveData.to_csv(path_or_buf=filename, 
                                        sep=self.config.saveDelimiter, 
                                        header=True, 
                                        index=True)
                    # Save 2D - single
                    elif self.extractData != 'RMSD Matrix' and evt.GetId() == ID_saveDataCSVDocument:
                        defaultValue = "DT_2D_{}_{}{}{}".format(basename, name_modifier, self.extractData, self.config.saveExtension)
                        
                        zvals, xvals, xlabel, yvals, ylabel, __ = self.presenter.get2DdataFromDictionary(dictionary=data[self.extractData],
                                                                                                           dataType='plot',compact=False)
                        saveData = np.vstack((yvals, zvals.T))
                        xvals = map(str, xvals.tolist())
                        labels = ["DT"]
                        for label in xvals: labels.append(label)
                        # Save 2D array
                        kwargs = {'default_name':defaultValue}
                        self.onSaveData(data=[saveData], labels=labels, 
                                        data_format='%.2f', **kwargs)
                    # Save 1D - single
                    elif self.extractData != 'RMSD Matrix' and evt.GetId() == ID_saveDataCSVDocument1D:
                        defaultValue = "DT_1D_{}_{}{}{}".format(basename, name_modifier, self.extractData, self.config.saveExtension)
                        
                        # Get data from the document
                        dtX = data[self.extractData]['yvals']
                        ylabel = data[self.extractData]['xlabels']
                        try: 
                            dtY = data[self.extractData]['yvals1D']
                        except KeyError: 
                            msg = 'Missing data. Cancelling operation.'
                            self.presenter.view.SetStatusText(msg, 3)
                            return
                        kwargs = {'default_name':defaultValue}
                        self.onSaveData(data=[dtX,dtY], labels=[ylabel,'Intensity'], 
                                        data_format='%.4f', **kwargs)   
        else: 
            return
        
    def onSaveImage(self, evt):
        """
        This function saves the image to file
        """
        
        if any(self.extractData in extractData for extractData in ['Drift time (2D, EIC)',
                                                                   'Drift time (2D, combined voltages, EIC)',
                                                                   'Drift time (2D, processed, EIC)',
                                                                   'Input data']):
            
            if self.itemType == 'Drift time (2D, EIC)':
                data = self.itemData.IMS2Dions
            elif self.itemType == 'Drift time (2D, combined voltages, EIC)':
                data = self.itemData.IMS2DCombIons
            elif self.itemType == 'Drift time (2D, processed, EIC)':
                data = self.itemData.IMS2DionsProcess
            elif self.itemType == 'Input data':
                data = self.itemData.IMS2DcompData
            
            # Save as doc
            if evt.GetId() == ID_saveImageDocument:
                saveFileName = self.presenter.getImageFilename(prefix=True, csv=False, 
                                                               defaultValue='DT_2D_')
                if saveFileName =='' or saveFileName == None: 
                    saveFileName = 'DT_2D_'
            
            # Iterate
            self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['2D'])
            for key in data:
                filename = ''.join([self.itemData.path, "\\", saveFileName, key,'.']) # extension is added later 
                dataOut = self.presenter.get2DdataFromDictionary(dictionary=data[key],
                                                                 dataType='plot',
                                                                 compact=True)
                # Change panel and plot data
                self.presenter.plot2Ddata2(data=dataOut)
                self.presenter.save2DIMSImage(path=filename)
        elif self.extractData == 'Mass Spectra':
            pass
        elif self.extractData == 'Overlay':
            # Get data
            data = self.itemData.IMS2DoverlayData
            for key in data:
                out = key.split(':')
                if evt.GetId() == ID_saveImageDocument:
                    saveFileName = self.presenter.getImageFilename(prefix=True, csv=False, 
                                                                   defaultValue=''.join(['Overlay',"_",key]))
                if saveFileName =='' or saveFileName == None: 
                    saveFileName = ''.join(['Overlay',"_",key])
                    
                # Create filename
                saveFileName = saveFileName.replace('.raw','')
                filename = ''.join([self.itemData.path, "\\", saveFileName,'.']) # extension is added later 
                
                if (out[0] == 'Mask'  or out[0] == 'Transparent'):                
                    zvals1, zvals2, cmap1, cmap2, alpha1, alpha2, xvals, yvals, xlabels, ylabels = self.presenter.getOverlayDataFromDictionary(dictionary=data[key],
                                                                                                                                               dataType='plot',
                                                                                                                                               compact=False)
                    if out[0] == 'Mask': 
                        self.presenter.onPlotOverlayMultipleIons2(zvalsIon1=zvals1,cmapIon1=cmap1,
                                                                  alphaIon1=1, zvalsIon2=zvals2, 
                                                                  cmapIon2=cmap2, alphaIon2=1,
                                                                  xvals=xvals,yvals=yvals, 
                                                                  xlabel=xlabels, ylabel=ylabels,
                                                                  flag='Text')
                    elif out[0] == 'Transparent':
                        self.presenter.onPlotOverlayMultipleIons2(zvalsIon1=zvals1,cmapIon1=cmap1,
                                                                  alphaIon1=alpha1,zvalsIon2=zvals2, 
                                                                  cmapIon2=cmap2,  alphaIon2=alpha2,
                                                                  xvals=xvals, yvals=yvals, 
                                                                  xlabel=xlabels, ylabel=ylabels,
                                                                  flag='Text')
                    # Change window view
                    self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['Overlay'])
                    self.presenter.saveOverlayImage(path=filename)
                elif out[0] == 'RMSF': 
                    zvals, yvalsRMSF, xvals, yvals, xlabelRMSD, ylabelRMSD, ylabelRMSF, color, cmap, rmsdLabel = self.presenter.get2DdataFromDictionary(dictionary=data[key],
                                                                                                                                  plotType='RMSF',
                                                                                                                                  compact=True)
                    self.presenter.onPlotRMSDF(yvalsRMSF=yvalsRMSF, 
                                               zvals=zvals, 
                                               xvals=xvals, 
                                               yvals=yvals, 
                                               xlabelRMSD=xlabelRMSD, 
                                               ylabelRMSD=ylabelRMSD,
                                               ylabelRMSF=ylabelRMSF,
                                               color=color, 
                                               cmap=cmap, 
                                               plotType="RMSD")
                    # Add RMSD label
                    rmsdXpos, rmsdYpos = self.presenter.onCalculateRMSDposition(xlist=xvals,
                                                                                ylist=yvals)
                    if rmsdXpos != None and rmsdYpos != None:
                        self.presenter.addTextRMSD(rmsdXpos,rmsdYpos, rmsdLabel, 0, plot='RMSF')
                        
                    self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['RMSF'])
                    self.presenter.saveRMSFImage(path=filename)
                elif out[0] == 'RMSD': 
                    zvals, xaxisLabels, xlabel, yaxisLabels, ylabel, rmsdLabel, cmap = self.presenter.get2DdataFromDictionary(dictionary=data[key],
                                                                                                                    plotType='RMSD',
                                                                                                                    compact=True)
                    self.presenter.onPlot2DIMS2(zvals, xaxisLabels, yaxisLabels, xlabel, ylabel, 
                                      cmap, plotType="RMSD")
                    self.presenter.onPlot3DIMS(zvals=zvals, labelsX=xaxisLabels, labelsY=yaxisLabels, 
                                     xlabel=xlabel, ylabel=ylabel, zlabel='Intensity', 
                                     cmap=cmap)
                    # Add RMSD label
                    rmsdXpos, rmsdYpos = self.presenter.onCalculateRMSDposition(xlist=xaxisLabels,
                                                                                ylist=yaxisLabels)
                    if rmsdXpos != None and rmsdYpos != None:
                        self.presenter.addTextRMSD(rmsdXpos,rmsdYpos, rmsdLabel, 0, plot='RMSD')
                        
                    self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['2D'])
                    self.presenter.save2DIMSImage(path=filename)
                
        elif self.extractData == 'Statistical':
            data = self.itemData.IMS2DstatsData
            for key in data:
                # Get save name
                if evt.GetId() == ID_saveImageDocument:
                    saveFileName = self.presenter.getImageFilename(prefix=True, csv=False, 
                                                                   defaultValue=''.join(['Statistical',"_",key]))
                if saveFileName =='' or saveFileName == None:
                    saveFileName = ''.join(['Statistical',"_",key])
                    
                # Create filename
                saveFileName = saveFileName.replace('.raw','')
                filename = ''.join([self.itemData.path, "\\", saveFileName,'.']) # extension is added later 
                
                # Variance, Mean, Std Dev are of the same format
                keyName = key.split(':')
                if (keyName[0] == 'Variance' or keyName[0] == 'Mean' or keyName[0] == 'Standard Deviation'): 
                    # Unpack data
                    dataOut = self.presenter.get2DdataFromDictionary(dictionary=data[key],
                                                                     dataType='plot',
                                                                     compact=True)
                    # Change panel and plot data
                    self.presenter.plot2Ddata2(data=dataOut)
                    self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['2D'])
                    self.presenter.save2DIMSImage(path=filename)
                elif keyName[0] == 'RMSD Matrix': 
                    zvals, yxlabels, cmap = self.presenter.get2DdataFromDictionary(dictionary=data[key],
                                                                                   plotType='Matrix',
                                                                                   compact=False)
                    self.presenter.onPlotRMSDmatrix(zvals=zvals, xylabels=yxlabels,cmap=cmap)
                    self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['Comparison'])
                    self.presenter.saveMatrixImage(path=filename)
                else:
                    self.presenter.onThreading(None, ("Could not complete the task", 4), 
                                               action='updateStatusbar')
                    return
                
    def onAddToCCSTable(self, evt):
        """
        Add currently selected item to the CCS calibration window
        """        
        if self.itemData == None:
            return
        
        label, item_format, batchMode = None, None, False
        if self.itemType == 'Drift time (2D, EIC)':
            if self.extractData != 'Drift time (2D, EIC)':
                data = self.itemData.IMS2Dions[self.extractData]
            else:
                data = self.itemData.IMS2Dions
                batchMode = True
            item_format = '2D, extracted'
        elif self.itemType == 'Drift time (2D, combined voltages, EIC)':
            if self.extractData != 'Drift time (2D, combined voltages, EIC)':
                data = self.itemData.IMS2DCombIons[self.extractData]
            else:
                data = self.itemData.IMS2DCombIons
                batchMode = True
            item_format = '2D, combined'
        elif self.itemType == 'Drift time (2D, processed, EIC)':
            if self.extractData != 'Drift time (2D, processed, EIC)':
                data = self.itemData.IMS2DionsProcess[self.extractData]
            else:
                data = self.itemData.IMS2DionsProcess
                batchMode = True
            item_format = '2D, processed'
        elif self.itemType == 'Input data':
            if self.extractData != 'Input data':
                data = self.itemData.IMS2DcompData[self.extractData]
            else:
                data = self.itemData.IMS2DcompData
                batchMode = True
            item_format = '2D'
        else: 
            return
        
        # If in batch mode (i.e. add all from within the header)
        if not batchMode:
            label = self.extractData
        
            # Split label
            mz = label.replace('-', ' ').split(' ')
            mzStart, mzEnd = float(mz[0]), float(mz[1]) 
            mzCentre = round((mzStart+mzEnd)/2,2)
            charge = data.get('charge', None)
            protein = data.get('protein', None)
            
            self.itemData.moleculeDetails.get('molWeight', None)
            
            self.presenter.OnAddDataToCCSTable(filename=self.itemData.title,
                                               format=item_format, mzStart=mzStart,
                                               mzEnd=mzEnd, mzCentre=mzCentre,
                                               charge=charge, protein=protein)
        else:
            for key in data:
                label = key
                # Split label
                mz = label.replace('-', ' ').split(' ')
                mzStart, mzEnd = float(mz[0]), float(mz[1]) 
                mzCentre = round((mzStart+mzEnd)/2,2)
                charge = data[key].get('charge', None)
                protein = data[key].get('protein', None)
                
                self.itemData.moleculeDetails.get('molWeight', None)
                
                self.presenter.OnAddDataToCCSTable(filename=self.itemData.title,
                                                   format=item_format, mzStart=mzStart,
                                                   mzEnd=mzEnd, mzCentre=mzCentre,
                                                   charge=charge, protein=protein)
        
    def onSaveHTML(self, evt):
        
        label = None
        # Select dataset
        if self.itemType == 'Drift time (2D)':
            data = self.itemData.IMS2D
        elif self.itemType == 'Drift time (2D, processed)':
            data = self.itemData.IMS2D
        elif self.itemType == 'Drift time (2D, EIC)':
            if self.extractData == 'Drift time (2D, EIC)': return
            data = self.itemData.IMS2Dions[self.extractData]
            label = self.extractData
        elif self.itemType == 'Drift time (2D, combined voltages, EIC)':
            if self.extractData == 'Drift time (2D, combined voltages, EIC)': return
            data = self.itemData.IMS2DCombIons[self.extractData]
            label = self.extractData
        elif self.itemType == 'Drift time (2D, processed, EIC)':
            if self.extractData == 'Drift time (2D, processed, EIC)': return
            data = self.itemData.IMS2DionsProcess[self.extractData]
            label = self.extractData
        else:
            return
        # Unpack elements
        zvals, xvals, xlabel, yvals, ylabel, cmap = self.presenter.get2DdataFromDictionary(dictionary=data,
                                                                                           dataType='plot',
                                                                                           compact=False)
        # Get path and cmap
        path = self.itemData.path
        # Determine which plot is to be plotted
        if evt.GetId() == ID_save2DhtmlDocumentImage:
            plotType = 'image'
        elif evt.GetId() == ID_save2DhtmlDocumentHeatmap:
            plotType = 'heatmap'
        # Parse data to Bokeh HTML outputter            
        self.presenter.save2DHTML(path, zvals, xvals, yvals, xlabel, ylabel, cmap,
                                  label=label, plotType=plotType, openFile=True)
          
    def onOpenDocInfo(self, evt):
        
        self.presenter.currentDoc = self.enableCurrentDocument()
        document_title = self.enableCurrentDocument()
        if self.presenter.currentDoc == 'Current documents': return
        document = self.presenter.documentsDict.get(document_title, None)
        
        if document is None: return
        
        for key in self.presenter.documentsDict:
            print(self.presenter.documentsDict[key].title)
 
        if self.indent == 2 and any(self.itemType in itemType for itemType in ['Drift time (2D)', 
                                                                               'Drift time (2D, processed)']):
            kwargs = {'currentTool':'plot2D', 
                      'itemType':self.itemType,
                      'extractData':None}
            self.panelInfo = panelDocumentInfo(self, self.presenter, self.config, self.icons, 
                                               document, **kwargs)
        elif self.indent == 3 and any(self.itemType in itemType for itemType in ['Drift time (2D, EIC)',
                                                                                 'Drift time (2D, combined voltages, EIC)',
                                                                                 'Drift time (2D, processed, EIC)',
                                                                                 'Input data']):
            kwargs = {'currentTool':'plot2D', 
                      'itemType':self.itemType,
                      'extractData':self.extractData}
            self.panelInfo = panelDocumentInfo(self, self.presenter, self.config, self.icons, 
                                               document, **kwargs)
        else:

            kwargs = {'currentTool':'summary', 
                      'itemType':None,
                      'extractData':None}
            self.panelInfo = panelDocumentInfo(self, self.presenter, self.config, self.icons, 
                                                document, **kwargs)
             
        self.panelInfo.Show()
          
    def addDocument(self, docData, expandAll=False, expandItem=None):
        """
        Append document to tree
        expandItem : object data, to expand specified item
        """
        # Get title for added data
        title = docData.title
        if not title:
            title = 'Document'        
        # Get root
        root = self.GetRootItem()
        
        item, cookie = self.GetFirstChild(self.GetRootItem())
        while item.IsOk():
            if self.GetItemText(item) == title:
                self.Delete(item)
            item, cookie = self.GetNextChild(root, cookie)
    

        # Add document
        docItem = self.AppendItem(self.GetRootItem(), title)
        self.SetFocusedItem(docItem)
        self.SetItemImage(docItem, self.bulets_dict["document_on"], wx.TreeItemIcon_Normal)
        self.currentDocument = docItem
        self.title = title
        self.SetPyData(docItem, docData)

        # Add annotations
        if hasattr(docData, 'dataType'):
            annotsItem = self.AppendItem(docItem, docData.dataType)
            self.SetItemImage(annotsItem, self.bulets_dict["annot_on"], wx.TreeItemIcon_Normal)
            self.SetPyData(annotsItem, docData.dataType)
        if hasattr(docData, 'fileFormat'):
            annotsItem = self.AppendItem(docItem, docData.fileFormat)
            self.SetItemImage(annotsItem, self.bulets_dict["annot_on"], wx.TreeItemIcon_Normal)
            self.SetPyData(annotsItem, docData.fileFormat)
        if hasattr(docData, 'fileInformation'):
            if docData.fileInformation != None:
                annotsItem = self.AppendItem(docItem, 'Sample information')
                self.SetPyData(annotsItem, docData.fileInformation)
                self.SetItemImage(annotsItem, self.bulets_dict["annot_on"], wx.TreeItemIcon_Normal)
        if docData.gotMS == True:
            annotsItemParent = self.AppendItem(docItem, 'Mass Spectrum')
            self.SetPyData(annotsItemParent, docData.massSpectrum)
            self.SetItemImage(annotsItemParent, self.bulets_dict["mass_spec"], wx.TreeItemIcon_Normal)
            if 'unidec' in docData.massSpectrum:
                docIonItem =  self.AppendItem(docItem, 'UniDec')
                self.SetItemImage(docIonItem, self.bulets_dict["mass_spec"], wx.TreeItemIcon_Normal)
                for annotData in docData.massSpectrum['unidec']:
                    annotsItem =  self.AppendItem(docIonItem, annotData)
                    self.SetPyData(annotsItem, docData.massSpectrum['unidec'][annotData])
                    self.SetItemImage(annotsItem, self.bulets_dict["mass_spec"], wx.TreeItemIcon_Normal)
#                     
#             if 'unidec' in docData.massSpectrum:
#                 docIonItem =  self.AppendItem(annotsItemParent, 'UniDec')
#                 self.SetItemImage(docIonItem, self.bulets_dict["mass_spec"], wx.TreeItemIcon_Normal)
#                 for annotData in docData.massSpectrum['unidec']:
#                     annotsItem =  self.AppendItem(docIonItem, annotData)
#                     self.SetPyData(annotsItem, docData.massSpectrum['unidec'][annotData])
#                     self.SetItemImage(annotsItem, self.bulets_dict["mass_spec"], wx.TreeItemIcon_Normal)
            if 'annotations' in docData.massSpectrum and len(docData.massSpectrum['annotations']) > 0:
                docIonItem =  self.AppendItem(annotsItemParent, 'Annotations')
                self.SetItemImage(docIonItem, self.bulets_dict["annot"], wx.TreeItemIcon_Normal)
                for annotData in docData.massSpectrum['annotations']:
                    annotsItem =  self.AppendItem(docIonItem, annotData)
                    self.SetPyData(annotsItem, docData.massSpectrum['annotations'][annotData])
                    self.SetItemImage(annotsItem, self.bulets_dict["annot"], wx.TreeItemIcon_Normal)
                    
        if bool(docData.smoothMS):
            annotsItemParent = self.AppendItem(docItem, 'Mass Spectrum (processed)')
            self.SetPyData(annotsItemParent, docData.smoothMS)
            self.SetItemImage(annotsItemParent, self.bulets_dict["mass_spec"], wx.TreeItemIcon_Normal)
            if 'unidec' in docData.smoothMS:
                docIonItem =  self.AppendItem(docItem, 'UniDec (processed)')
                self.SetItemImage(docIonItem, self.bulets_dict["mass_spec"], wx.TreeItemIcon_Normal)
                for annotData in docData.smoothMS['unidec']:
                    annotsItem =  self.AppendItem(docIonItem, annotData)
                    self.SetPyData(annotsItem, docData.smoothMS['unidec'][annotData])
                    self.SetItemImage(annotsItem, self.bulets_dict["mass_spec"], wx.TreeItemIcon_Normal)
            
#             if 'unidec' in docData.smoothMS:
#                 docIonItem =  self.AppendItem(annotsItemParent, 'UniDec')
#                 self.SetItemImage(docIonItem, self.bulets_dict["mass_spec"], wx.TreeItemIcon_Normal)
#                 for annotData in docData.smoothMS['unidec']:
#                     annotsItem =  self.AppendItem(docIonItem, annotData)
#                     self.SetPyData(annotsItem, docData.smoothMS['unidec'][annotData])
#                     self.SetItemImage(annotsItem, self.bulets_dict["mass_spec"], wx.TreeItemIcon_Normal)
            if 'annotations' in docData.smoothMS and len(docData.smoothMS['annotations']) > 0:
                docIonItem =  self.AppendItem(annotsItemParent, 'Annotations')
                self.SetItemImage(docIonItem, self.bulets_dict["annot"], wx.TreeItemIcon_Normal)
                for annotData in docData.smoothMS['annotations']:
                    annotsItem =  self.AppendItem(docIonItem, annotData)
                    self.SetPyData(annotsItem, docData.smoothMS['annotations'][annotData])
                    self.SetItemImage(annotsItem, self.bulets_dict["annot"], wx.TreeItemIcon_Normal)
            
        if docData.gotMultipleMS == True:
            docIonItem =  self.AppendItem(docItem, 'Mass Spectra')
            self.SetItemImage(docIonItem, self.bulets_dict["mass_spec"], wx.TreeItemIcon_Normal)
            for annotData in docData.multipleMassSpectrum:
                annotsItem =  self.AppendItem(docIonItem, annotData)
                self.SetPyData(annotsItem, docData.multipleMassSpectrum[annotData])
                self.SetItemImage(annotsItem, self.bulets_dict["mass_spec_on"], wx.TreeItemIcon_Normal)
                if 'unidec' in docData.multipleMassSpectrum[annotData]:
                    unidec_title = "UniDec ({})".format(annotData)
                    docIonItemInner =  self.AppendItem(docIonItem, unidec_title)
                    self.SetItemImage(docIonItemInner, self.bulets_dict["mass_spec_on"], wx.TreeItemIcon_Normal)
                    for annotDataInner in docData.multipleMassSpectrum[annotData]['unidec']:
                        annotsItemInner =  self.AppendItem(docIonItemInner, annotDataInner)
                        self.SetPyData(annotsItemInner, docData.multipleMassSpectrum[annotData]['unidec'][annotDataInner])
                        self.SetItemImage(annotsItemInner, self.bulets_dict["mass_spec_on"], wx.TreeItemIcon_Normal)
                        
        if docData.got1RT == True:
            annotsItem = self.AppendItem(docItem, 'Chromatogram')
            self.SetPyData(annotsItem, docData.RT)
            self.SetItemImage(annotsItem, self.bulets_dict["rt"], wx.TreeItemIcon_Normal)
            
        if hasattr(docData, 'gotMultipleRT'):
            if docData.gotMultipleRT == True:
                docIonItem = self.AppendItem(docItem, 'Chromatograms (EIC)')
                self.SetItemImage(docIonItem, self.bulets_dict["rt"], wx.TreeItemIcon_Normal)
                for annotData, __ in sorted(docData.multipleRT.items()):
                    annotsItem =  self.AppendItem(docIonItem, annotData)
                    self.SetPyData(annotsItem, docData.multipleRT[annotData])
                    self.SetItemImage(annotsItem, self.bulets_dict["rt_on"], wx.TreeItemIcon_Normal)
        if docData.got1DT == True:
            annotsItem  = self.AppendItem(docItem, 'Drift time (1D)')
            self.SetPyData(annotsItem, docData.DT)
            self.SetItemImage(annotsItem, self.bulets_dict["drift_time"], wx.TreeItemIcon_Normal)
        if hasattr(docData, 'gotMultipleDT'):
            if docData.gotMultipleDT == True:
                docIonItem = self.AppendItem(docItem, 'Drift time (1D, EIC)')
                self.SetItemImage(docIonItem, self.bulets_dict["drift_time"], wx.TreeItemIcon_Normal)
                for annotData, __ in sorted(docData.multipleDT.items()):
                    annotsItem =  self.AppendItem(docIonItem, annotData)
                    self.SetPyData(annotsItem, docData.multipleDT[annotData])
                    self.SetItemImage(annotsItem, self.bulets_dict["drift_time_on"], wx.TreeItemIcon_Normal)
        if docData.gotExtractedDriftTimes == True:
            docIonItem = self.AppendItem(docItem, 'Drift time (1D, EIC, DT-IMS)')
            self.SetItemImage(docIonItem, self.bulets_dict["drift_time"], wx.TreeItemIcon_Normal)
            for annotData, __ in sorted(docData.IMS1DdriftTimes.items()):
                annotsItem =  self.AppendItem(docIonItem, annotData)
                self.SetPyData(annotsItem, docData.IMS1DdriftTimes[annotData])
                self.SetItemImage(annotsItem, self.bulets_dict["drift_time_on"], wx.TreeItemIcon_Normal)
        if docData.got2DIMS == True:
            annotsItem = self.AppendItem(docItem, 'Drift time (2D)')
            self.SetPyData(annotsItem, docData.IMS2D)
            self.SetItemImage(annotsItem, self.bulets_dict["heatmap"], wx.TreeItemIcon_Normal)
        if docData.got2Dprocess == True or len(docData.IMS2Dprocess) > 0:
            annotsItem =  self.AppendItem(docItem, 'Drift time (2D, processed)')
            self.SetPyData(annotsItem, docData.IMS2Dprocess)
            self.SetItemImage(annotsItem, self.bulets_dict["heatmap"], wx.TreeItemIcon_Normal)
        if docData.gotExtractedIons == True:
            docIonItem = self.AppendItem(docItem, 'Drift time (2D, EIC)')
            self.SetItemImage(docIonItem, self.bulets_dict["heatmap"], wx.TreeItemIcon_Normal)
            for annotData, __ in sorted(docData.IMS2Dions.items()):
                annotsItem =  self.AppendItem(docIonItem, annotData)
                self.SetPyData(annotsItem, docData.IMS2Dions[annotData])
                self.SetItemImage(annotsItem, self.bulets_dict["heatmap_on"], wx.TreeItemIcon_Normal)
        if docData.gotCombinedExtractedIons == True:
            docIonItem = self.AppendItem(docItem, 'Drift time (2D, combined voltages, EIC)')
            self.SetItemImage(docIonItem, self.bulets_dict["heatmap"], wx.TreeItemIcon_Normal)
            for annotData, __ in sorted(docData.IMS2DCombIons.items()):
                annotsItem =  self.AppendItem(docIonItem, annotData)
                self.SetPyData(annotsItem, docData.IMS2DCombIons[annotData])
                self.SetItemImage(annotsItem, self.bulets_dict["heatmap_on"], wx.TreeItemIcon_Normal)
                
        if docData.gotCombinedExtractedIonsRT == True:
            docIonItem = self.AppendItem(docItem, 'Chromatograms (combined voltages, EIC)')
            self.SetItemImage(docIonItem, self.bulets_dict["rt"], wx.TreeItemIcon_Normal)
            for annotData, __ in sorted(docData.IMSRTCombIons.items()):
                annotsItem =  self.AppendItem(docIonItem, annotData)
                self.SetPyData(annotsItem, docData.IMSRTCombIons[annotData])
                self.SetItemImage(annotsItem, self.bulets_dict["rt_on"], wx.TreeItemIcon_Normal)
                
        if docData.got2DprocessIons == True:
            docIonItem = self.AppendItem(docItem, 'Drift time (2D, processed, EIC)')
            self.SetItemImage(docIonItem, self.bulets_dict["heatmap"], wx.TreeItemIcon_Normal)
            for annotData, __ in sorted(docData.IMS2DionsProcess.items()):
                annotsItem =  self.AppendItem(docIonItem, annotData)
                self.SetPyData(annotsItem, docData.IMS2DionsProcess[annotData])
                self.SetItemImage(annotsItem, self.bulets_dict["heatmap_on"], wx.TreeItemIcon_Normal)
                
        if docData.gotCalibration == True:
            docIonItem = self.AppendItem(docItem, 'Calibration peaks')
            self.SetItemImage(docIonItem, self.bulets_dict["calibration"], wx.TreeItemIcon_Normal)
            for annotData, __ in sorted(docData.calibration.items()):
                annotsItem =  self.AppendItem(docIonItem, annotData)
                self.SetPyData(annotsItem, docData.calibration[annotData])
                self.SetItemImage(annotsItem, self.bulets_dict["dots_on"], wx.TreeItemIcon_Normal)
        if docData.gotCalibrationDataset == True:
            docIonItem = self.AppendItem(docItem, 'Calibrants')
            self.SetItemImage(docIonItem, self.bulets_dict["calibration_on"], wx.TreeItemIcon_Normal)
            for annotData in docData.calibrationDataset:
                annotsItem =  self.AppendItem(docIonItem, annotData)
                self.SetPyData(annotsItem, docData.calibrationDataset[annotData])
                self.SetItemImage(annotsItem, self.bulets_dict["dots_on"], wx.TreeItemIcon_Normal)
        if docData.gotCalibrationParameters == True:
            annotsItem =  self.AppendItem(docItem, 'Calibration parameters')
            self.SetPyData(annotsItem, docData.calibrationParameters)
            self.SetItemImage(annotsItem, self.bulets_dict["calibration"], wx.TreeItemIcon_Normal)                
        if docData.gotComparisonData == True:
            docIonItem =  self.AppendItem(docItem, 'Input data')
            self.SetItemImage(docIonItem, self.bulets_dict["overlay"], wx.TreeItemIcon_Normal)
            for annotData, __ in sorted(docData.IMS2DcompData.items()):
                annotsItem =  self.AppendItem(docIonItem, annotData)
                self.SetPyData(annotsItem, docData.IMS2DcompData[annotData])
                self.SetItemImage(annotsItem, self.bulets_dict["heatmap_on"], wx.TreeItemIcon_Normal)
        if docData.gotOverlay == True:
            docIonItem =  self.AppendItem(docItem, 'Overlay')
            self.SetItemImage(docIonItem, self.bulets_dict["overlay"], wx.TreeItemIcon_Normal)
            for annotData, __ in sorted(docData.IMS2DoverlayData.items()):
                annotsItem =  self.AppendItem(docIonItem, annotData)
                self.SetPyData(annotsItem, docData.IMS2DoverlayData[annotData])
                self.SetItemImage(annotsItem, self.bulets_dict["heatmap_on"], wx.TreeItemIcon_Normal)
        if docData.gotStatsData == True:
            docIonItem =  self.AppendItem(docItem, 'Statistical')
            self.SetItemImage(docIonItem, self.bulets_dict["overlay"], wx.TreeItemIcon_Normal)
            for annotData, __ in sorted(docData.IMS2DstatsData.items()):
                annotsItem =  self.AppendItem(docIonItem, annotData)
                self.SetPyData(annotsItem, docData.IMS2DstatsData[annotData])
                self.SetItemImage(annotsItem, self.bulets_dict["heatmap_on"], wx.TreeItemIcon_Normal)
        if hasattr(docData, "DTMZ"):
            if docData.gotDTMZ:
                annotsItem =  self.AppendItem(docItem, 'DT/MS')
                self.SetPyData(annotsItem, docData.DTMZ)
                self.SetItemImage(annotsItem, self.bulets_dict["heatmap"], wx.TreeItemIcon_Normal)

        # Recursively check currently selected document
        self.enableCurrentDocument(loadingData=True, expandAll=expandAll, evt=None)
        
        # If expandItem is not empty, the Tree will expand specified item
        if expandItem != None:
            # Change document tree
            try:
                docItem = self.getItemByData(expandItem)
                parent = self.GetItemParent(docItem)
                self.Expand(parent)
            except: pass
                
    def removeDocument(self, evt, deleteItem="", ask_permission=True):
        """
        Remove selected document from the document tree
        """
        # Find the root first
        root = None
        if root == None:
            root = self.GetRootItem()
        
        try:
            evtID = evt.GetId()
        except AttributeError:
            evtID = None
            
        if evtID == ID_removeDocument or (evtID == None and deleteItem == ""):
            __, cookie = self.GetFirstChild(self.GetRootItem())
            
            if ask_permission:
                dlg = dialogs.dlgBox(exceptionTitle='Are you sure?', 
                                     exceptionMsg= ''.join(["Are you sure you would like to delete: ", 
                                                            self.itemData.title,"?"]),
                                     type="Question")
                if dlg == wx.ID_NO:
                    msg = 'Cancelled operation'
                    self.presenter.view.SetStatusText(msg, 3)
                    return
                else:
                    deleteItem = self.itemData.title #self.GetItemText(item)
                    
            # Clear all plots
            if self.presenter.currentDoc == deleteItem:
                self.presenter.onClearAllPlots()
                self.presenter.currentDoc = None            
                
        if deleteItem == '': return
        
        # Delete item from the list
        if self.ItemHasChildren(root):
            child, cookie = self.GetFirstChild(self.GetRootItem())
            title = self.GetItemText(child)
            iters=0
            while deleteItem != title and iters < 500:
                child, cookie = self.GetNextChild(self.GetRootItem(), cookie)
                try:
                    title = self.GetItemText(child)
                    iters += 1
                except: pass
                
            if deleteItem == title:
                if child:
                    print(''.join(["Deleted: ", deleteItem]))
                    self.Delete(child)
                    # Remove data from dictionary if removing whole document
                    if evtID == ID_removeDocument  or evtID == None:
                        # make sure to clean-up various tables
                        try: self.presenter.view.panelMultipleIons.topP.onClearItems(title)
                        except: pass
                        try: self.presenter.view.panelMultipleText.topP.onClearItems(title)
                        except: pass
                        try: self.presenter.view.panelMML.topP.onClearItems(title)
                        except: pass
                        try: self.presenter.view.panelLinearDT.topP.onClearItems(title)
                        except: pass
                        try: self.presenter.view.panelLinearDT.bottomP.onClearItems(title)
                        except: pass
                        
                        # delete document
                        del self.presenter.documentsDict[title]
                        self.presenter.currentDoc = None
                        gc.collect()
                        
                    return True
            else: return False       

    def getItemIDbyName(self, root, title):
        item, cookie = self.GetFirstChild(root)
        
        while item.IsOk():
            text = self.GetItemText(item)
            if text == title:
                return item
            if self.ItemHasChildren(item):
                match = self.getItemIDbyName(item, title)
                if match.IsOk():
                    return match
            item, cookie = self.GetNextChild(root, cookie)
    
        return wx.TreeItemId()

    def setAsCurrentDocument(self, title):
#         docItem = self.AppendItem(self.GetRootItem(), title)
        
        docItem = self.getItemIDbyName(self.GetRootItem(), title)
        self.SetFocusedItem(docItem)
            
    def getCurrentDocument(self, e=None):
        item = self.GetSelection()
        if not item: return
        while self.GetItemParent(item):
            text = self.GetItemText(item)
            return text

    def onShowSampleInfo(self, evt=None):
        
        msg = self.itemData.fileInformation.get('SampleDescription', 'None')
        dialogs.dlgBox(exceptionTitle='Sample information', exceptionMsg=msg,
                       type='Info')

    def enableCurrentDocument(self, getSelected=False, loadingData=False, 
                              highlightSelected=False, expandAll=False,
                              expandSelected=None, evt=None):
        """
        Highlights and returns currently selected document
        ---
        Parameters
        ----------
        getSelected
        loadingData: booleat, flag to tell the function that we are loading data
        highlightSelected
        expandAll : boolean, flag to expand or not of the tree
        expandSelected : string, name of item to expand
        """
        root = self.GetRootItem()
        selected = self.GetSelection()
        item, cookie = self.GetFirstChild(root)

        try:
            evtID = evt.GetId()
        except AttributeError:
            evtID = None
        while item.IsOk():
            self.SetItemBold(item, False)
            if loadingData == True:
                self.CollapseAllChildren(item)
            item, cookie = self.GetNextChild(root, cookie)
        
        # Select parent document
        if selected != None:
            item = self.getParentItem(selected, 1)
            try:
                self.SetItemBold(item, True)
            except wx._core.PyAssertionError: pass
            if loadingData == True or evtID == ID_getSelectedDocument:
                self.Expand(item) # Parent item
                if expandAll:
                    self.ExpandAllChildren(item)
                    
            # window label
            try:
                text = self.GetItemText(item)
                if text != 'Current documents':
                    self.presenter.currentDoc = text
                    self.mainParent.SetTitle("ORIGAMI - %s - %s (%s)" % (self.config.version, text, self.itemData.dataType)) 
            except:
                self.mainParent.SetTitle(" - ".join(["ORIGAMI", self.config.version]))
                
            # In case we also interested in selected item
            if getSelected:
                selectedText = self.GetItemText(selected)
                if highlightSelected == True:
                    self.SetItemBold(selected, True)
                return text, selected, selectedText
            else:
                return text
        
        if evt != None:
            evt.Skip()

    def onExpandItem(self, item, evt):
        """ function to expand selected item """
        pass
        
    def setCurrentDocument(self, docTitle, e=None):
        """ Highlight currently selected document from tables """
        root = None
        if root == None:
            root = self.GetRootItem()
        
        if self.ItemHasChildren(root):
            firstchild, cookie = self.GetFirstChild(self.GetRootItem())
            title = self.GetItemText(firstchild)
            if title == docTitle:
                self.SetItemBold(firstchild, True)
                self.presenter.currentDoc = docTitle
                
        self.itemData = self.presenter.documentsDict[docTitle]        
      
    def getItemIndent(self, item):
        # Check item first
        if not item.IsOk():
            return False
        
        # Get Indent
        indent = 0
        root = self.GetRootItem()
        while item.IsOk():
            if item == root:
                return indent
            else:
                item = self.GetItemParent(item)
                indent += 1
        return indent
                
    def getParentItem(self, item, level, getSelected=False):
        """ Get parent item for selected item and level"""
        # Get item
        for x in xrange(level, self.getItemIndent(item)):
            item = self.GetItemParent(item)
        
        if getSelected:
            itemText = self.GetItemText(item)
            return item, itemText
        else:
            return item
  
    def getItemByData(self, data, root=None, cookie=0):
        """Get item by its data."""
        
        # get root
        if root == None:
            root = self.GetRootItem()
        
        # check children
        if self.ItemHasChildren(root):
            firstchild, cookie = self.GetFirstChild(root)
            if self.GetPyData(firstchild) is data:
                return firstchild
            matchedItem = self.getItemByData(data, firstchild, cookie)
            if matchedItem:
                return matchedItem
        
        # check siblings
        child = self.GetNextSibling(root)
        if child and child.IsOk():
            if self.GetPyData(child) is data:
                return child
            matchedItem = self.getItemByData(data, child, cookie)
            if matchedItem:
                return matchedItem
        
        # no such item found
        return False
    
#     def updateDocument(self, document, itemType='all'):
#         
#         if itemType in ['all', 'mass_spectra']:
#             if document.gotMultipleMS:
#                 docIonItem =  self.AppendItem(document, 'Mass Spectra')
#                 self.SetItemImage(docIonItem, 1, wx.TreeItemIcon_Normal)
#                 for annotData in document.multipleMassSpectrum:
#                     annotsItem =  self.AppendItem(docIonItem, annotData)
#                     self.SetPyData(annotsItem, document.multipleMassSpectrum[annotData])
#                     self.SetItemImage(annotsItem, 1, wx.TreeItemIcon_Normal)
#         
#         if hasattr(docData, 'dataType'):
#             annotsItem = self.AppendItem(docItem, docData.dataType)
#             self.SetItemImage(annotsItem, 14, wx.TreeItemIcon_Normal)
#             self.SetPyData(annotsItem, docData.dataType)
#         if hasattr(docData, 'fileFormat'):
#             annotsItem = self.AppendItem(docItem, docData.fileFormat)
#             self.SetItemImage(annotsItem, 14, wx.TreeItemIcon_Normal)
#             self.SetPyData(annotsItem, docData.fileFormat)
#         if hasattr(docData, 'fileInformation'):
#             if docData.fileInformation != None:
#                 annotsItem = self.AppendItem(docItem, 'Sample information')
#                 self.SetPyData(annotsItem, docData.fileInformation)
#                 self.SetItemImage(annotsItem, 14, wx.TreeItemIcon_Normal)
#         if docData.gotMS == True:
#             annotsItem = self.AppendItem(docItem, 'Mass Spectrum')
#             self.SetPyData(annotsItem, docData.massSpectrum)
#             self.SetItemImage(annotsItem, 1, wx.TreeItemIcon_Normal)
#         if bool(docData.smoothMS):
#             annotsItem = self.AppendItem(docItem, 'Mass Spectrum (processed)')
#             self.SetPyData(annotsItem, docData.smoothMS)
#             self.SetItemImage(annotsItem, 1, wx.TreeItemIcon_Normal)
#         if docData.gotMultipleMS == True:
#             docIonItem =  self.AppendItem(docItem, 'Mass Spectra')
#             self.SetItemImage(docIonItem, 1, wx.TreeItemIcon_Normal)
#             for annotData in docData.multipleMassSpectrum:
#                 annotsItem =  self.AppendItem(docIonItem, annotData)
#                 self.SetPyData(annotsItem, docData.multipleMassSpectrum[annotData])
#                 self.SetItemImage(annotsItem, 1, wx.TreeItemIcon_Normal)
#         if docData.got1RT == True:
#             annotsItem = self.AppendItem(docItem, 'Chromatogram')
#             self.SetPyData(annotsItem, docData.RT)
#             self.SetItemImage(annotsItem, 3, wx.TreeItemIcon_Normal)
#         if hasattr(docData, 'gotMultipleRT'):
#             if docData.gotMultipleRT == True:
#                 docIonItem = self.AppendItem(docItem, 'Chromatograms (EIC)')
#                 self.SetItemImage(docIonItem, 12, wx.TreeItemIcon_Normal)
#                 for annotData, __ in sorted(docData.multipleRT.items()):
#                     annotsItem =  self.AppendItem(docIonItem, annotData)
#                     self.SetPyData(annotsItem, docData.multipleRT[annotData])
#                     self.SetItemImage(annotsItem, 12, wx.TreeItemIcon_Normal)
#         if docData.got1DT == True:
#             annotsItem  = self.AppendItem(docItem, 'Drift time (1D)')
#             self.SetPyData(annotsItem, docData.DT)
#             self.SetItemImage(annotsItem, 2, wx.TreeItemIcon_Normal)
#         if hasattr(docData, 'gotMultipleDT'):
#             if docData.gotMultipleDT == True:
#                 docIonItem = self.AppendItem(docItem, 'Drift time (1D, EIC)')
#                 self.SetItemImage(docIonItem, 12, wx.TreeItemIcon_Normal)
#                 for annotData, __ in sorted(docData.multipleDT.items()):
#                     annotsItem =  self.AppendItem(docIonItem, annotData)
#                     self.SetPyData(annotsItem, docData.multipleDT[annotData])
#                     self.SetItemImage(annotsItem, 12, wx.TreeItemIcon_Normal)
#         if docData.gotExtractedDriftTimes == True:
#             docIonItem = self.AppendItem(docItem, 'Drift time (1D, EIC, DT-IMS)')
#             self.SetItemImage(docIonItem, 11, wx.TreeItemIcon_Normal)
#             for annotData, __ in sorted(docData.IMS1DdriftTimes.items()):
#                 annotsItem =  self.AppendItem(docIonItem, annotData)
#                 self.SetPyData(annotsItem, docData.IMS1DdriftTimes[annotData])
#                 self.SetItemImage(annotsItem, 11, wx.TreeItemIcon_Normal)
#         if docData.got2DIMS == True:
#             annotsItem = self.AppendItem(docItem, 'Drift time (2D)')
#             self.SetPyData(annotsItem, docData.IMS2D)
#             self.SetItemImage(annotsItem, 6, wx.TreeItemIcon_Normal)
#         if docData.got2Dprocess == True:
#             annotsItem =  self.AppendItem(docItem, 'Drift time (2D, processed)')
#             self.SetPyData(annotsItem, docData.IMS2Dprocess)
#             self.SetItemImage(annotsItem, 6, wx.TreeItemIcon_Normal)
#         if docData.gotExtractedIons == True:
#             docIonItem = self.AppendItem(docItem, 'Drift time (2D, EIC)')
#             self.SetItemImage(docIonItem, 15, wx.TreeItemIcon_Normal)
#             for annotData, __ in sorted(docData.IMS2Dions.items()):
#                 annotsItem =  self.AppendItem(docIonItem, annotData)
#                 self.SetPyData(annotsItem, docData.IMS2Dions[annotData])
#                 self.SetItemImage(annotsItem, 15, wx.TreeItemIcon_Normal)
#         if docData.gotCombinedExtractedIons == True:
#             docIonItem = self.AppendItem(docItem, 'Drift time (2D, combined voltages, EIC)')
#             self.SetItemImage(docIonItem, 15, wx.TreeItemIcon_Normal)
#             for annotData, __ in sorted(docData.IMS2DCombIons.items()):
#                 annotsItem =  self.AppendItem(docIonItem, annotData)
#                 self.SetPyData(annotsItem, docData.IMS2DCombIons[annotData])
#                 self.SetItemImage(annotsItem, 15, wx.TreeItemIcon_Normal)
#         if docData.gotCombinedExtractedIonsRT == True:
#             docIonItem = self.AppendItem(docItem, 'Chromatograms (combined voltages, EIC)')
#             self.SetItemImage(docIonItem, 12, wx.TreeItemIcon_Normal)
#             for annotData, __ in sorted(docData.IMSRTCombIons.items()):
#                 annotsItem =  self.AppendItem(docIonItem, annotData)
#                 self.SetPyData(annotsItem, docData.IMSRTCombIons[annotData])
#                 self.SetItemImage(annotsItem, 12, wx.TreeItemIcon_Normal)
#         if docData.got2DprocessIons == True:
#             docIonItem = self.AppendItem(docItem, 'Drift time (2D, processed, EIC)')
#             self.SetItemImage(docIonItem, 15, wx.TreeItemIcon_Normal)
#             for annotData, __ in sorted(docData.IMS2DionsProcess.items()):
#                 annotsItem =  self.AppendItem(docIonItem, annotData)
#                 self.SetPyData(annotsItem, docData.IMS2DionsProcess[annotData])
#                 self.SetItemImage(annotsItem, 15, wx.TreeItemIcon_Normal)
#         if docData.gotCalibration == True:
#             docIonItem = self.AppendItem(docItem, 'Calibration peaks')
#             self.SetItemImage(docIonItem, 10, wx.TreeItemIcon_Normal)
#             for annotData, __ in sorted(docData.calibration.items()):
#                 annotsItem =  self.AppendItem(docIonItem, annotData)
#                 self.SetPyData(annotsItem, docData.calibration[annotData])
#                 self.SetItemImage(annotsItem, 6, wx.TreeItemIcon_Normal)
#         if docData.gotCalibrationDataset == True:
#             docIonItem = self.AppendItem(docItem, 'Calibrants')
#             self.SetItemImage(docIonItem, 16, wx.TreeItemIcon_Normal)
#             for annotData in docData.calibrationDataset:
#                 annotsItem =  self.AppendItem(docIonItem, annotData)
#                 self.SetPyData(annotsItem, docData.calibrationDataset[annotData])
#                 self.SetItemImage(annotsItem, 13, wx.TreeItemIcon_Normal)
#         if docData.gotCalibrationParameters == True:
#             annotsItem =  self.AppendItem(docItem, 'Calibration parameters')
#             self.SetPyData(annotsItem, docData.calibrationParameters)
#             self.SetItemImage(annotsItem, 5, wx.TreeItemIcon_Normal)                
#         if docData.gotComparisonData == True:
#             docIonItem =  self.AppendItem(docItem, 'Input data')
#             self.SetItemImage(docIonItem, 8, wx.TreeItemIcon_Normal)
#             for annotData, __ in sorted(docData.IMS2DcompData.items()):
#                 annotsItem =  self.AppendItem(docIonItem, annotData)
#                 self.SetPyData(annotsItem, docData.IMS2DcompData[annotData])
#                 self.SetItemImage(annotsItem, 15, wx.TreeItemIcon_Normal)
#         if docData.gotOverlay == True:
#             docIonItem =  self.AppendItem(docItem, 'Overlay')
#             self.SetItemImage(docIonItem, 8, wx.TreeItemIcon_Normal)
#             for annotData, __ in sorted(docData.IMS2DoverlayData.items()):
#                 annotsItem =  self.AppendItem(docIonItem, annotData)
#                 self.SetPyData(annotsItem, docData.IMS2DoverlayData[annotData])
#                 self.SetItemImage(annotsItem, 17, wx.TreeItemIcon_Normal)
#         if docData.gotStatsData == True:
#             docIonItem =  self.AppendItem(docItem, 'Statistical')
#             self.SetItemImage(docIonItem, 8, wx.TreeItemIcon_Normal)
#             for annotData, __ in sorted(docData.IMS2DstatsData.items()):
#                 annotsItem =  self.AppendItem(docIonItem, annotData)
#                 self.SetPyData(annotsItem, docData.IMS2DstatsData[annotData])
#                 self.SetItemImage(annotsItem, 17, wx.TreeItemIcon_Normal)
#         if hasattr(docData, "DTMZ"):
#             if docData.gotDTMZ:
#                 annotsItem =  self.AppendItem(docItem, 'DT/MS')
#                 self.SetPyData(annotsItem, docData.DTMZ)
#                 self.SetItemImage(annotsItem, 6, wx.TreeItemIcon_Normal)

class topPanel(wx.Panel):
    def __init__(self, parent, mainParent,icons, presenter, config):
        wx.Panel.__init__(self, parent=parent)
        self.parent = parent
        self.mainParent = mainParent
        self.icons = icons
        self.presenter = presenter 
        self.config = config
        self.makeTreeCtrl()
            
        self.panelSizer = wx.BoxSizer( wx.VERTICAL )
        self.panelSizer.Add(self.documents, 1, wx.EXPAND, 0)

        self.SetSizer(self.panelSizer)

    def makeTreeCtrl(self):
        self.documents = documentsTree(self, 
                                       self.mainParent, 
                                       self.presenter, 
                                       self.icons, 
                                       self.config, -1, 
                                       size=(250, -1))
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        