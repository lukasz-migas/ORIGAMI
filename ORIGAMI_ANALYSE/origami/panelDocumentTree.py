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

# TODO: Add converter of RT scale from scans to mins
# TODO: Add converter of MS from m/z to m/z (Da) to m/z (kDa)
# TODO: Fix on_enable_document

import wx, gc, os, re, time, threading
import numpy as np
import pandas as pd
from operator import itemgetter
from copy import deepcopy
from natsort import natsorted

from dialogs import panelRenameItem, panelSelectDataset, dlgBox
from gui_elements.dialog_askOverride import dialogAskOverride
from panelAnnotatePeaks import panelAnnotatePeaks
from panelCompareMS import panelCompareMS
from panelInformation import panelDocumentInfo
from panelTandemSpectra import panelTandemSpectra
from ids import *
from toolbox import (str2num, saveAsText, convertRGB255to1, randomIntegerGenerator,
                             randomColorGenerator, convertRGB1to255, str2int, convertHEXtoRGB1,
                             merge_two_dicts, determineFontColor, _replace_labels)
import dialogs as dialogs
from processing.spectra import normalize_1D, subtract_1D
from readers.io_text_files import text_heatmap_open
from styles import makeMenuItem
import readers.io_mgf as io_mgf
import readers.io_mzid as io_mzid
import readers.io_mzml as io_mzml
import readers.io_thermo_raw as io_thermo  # @UnresolvedImport
# import readers.io_waters_raw_api as io_waters_raw_api


class panelDocuments (wx.Panel):
    """
    Make documents panel to store all information about open files
    """

    def __init__(self, parent, config, icons, presenter):
        wx.Panel.__init__ (self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                           size=wx.Size(250, -1), style=wx.TAB_TRAVERSAL)

        self.parent = parent
        self.config = config
        self.presenter = presenter
        self.icons = icons

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.topP = topPanel(self, self.parent, self.icons, self.presenter, self.config)
        self.sizer.Add(self.topP, 1, wx.EXPAND, 0)
        self.sizer.Fit(self)
        self.SetSizer(self.sizer)

    def __del__(self):
         pass


class documentsTree(wx.TreeCtrl):
    """
    Documents tree
    """

    def __init__(self, parent, mainParent, presenter, icons, config, id, size=(-1, -1),
                 style=wx.TR_TWIST_BUTTONS | wx.TR_HAS_BUTTONS | wx.TR_FULL_ROW_HIGHLIGHT):
        wx.TreeCtrl.__init__(self, parent, id, size=size, style=style)

        self.parent = parent
        self.mainParent = mainParent
        self.presenter = presenter
        self.icons = icons
        self.config = config

        self.indent = None
        self.itemType = None
        self.extractData = None
        self.extractParent = None
        self.extractGrandparent = None

        self.itemData = None
        self.currentDocument = None
        self.annotateDlg = None

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
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_enable_document, id=wx.ID_ANY)
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.on_enable_document, id=wx.ID_ANY)
        self.Bind(wx.EVT_TREE_ITEM_MENU, self.OnRightClickMenu, id=wx.ID_ANY)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnDoubleClick)

        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_enable_document, id=wx.ID_ANY)
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.onItemSelection, id=wx.ID_ANY)
        self.Bind(wx.EVT_CHAR_HOOK, self.onKey, id=wx.ID_ANY)

        if self.config.quickDisplay:
            self.Bind(wx.EVT_TREE_SEL_CHANGED, self.onChangePlot, id=wx.ID_ANY)

    def set_data_processing(self):
        self.data_processing = self.presenter.data_processing

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
#             # Delete single document
#             elif indent == 1:
#                 self.removeDocument(evt=ID_removeDocument)
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
        elif key == 341:  # F2
            self.onRenameItem(None)

    def OnDoubleClick(self, evt):

        tstart = time.clock()
        # Get selected item
        item = self.GetSelection()
        self.currentItem = item

        # Get the current text value for selected item
        itemType = self.GetItemText(item)
        if itemType == 'Current documents':
            menu = wx.Menu()
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveAllDocuments,
                                         text='Save all documents',
                                         bitmap=self.icons.iconsLib['save_multiple_16']))
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_removeAllDocuments,
                                         text='Delete all documents',
                                         bitmap=self.icons.iconsLib['bin16']))
            self.PopupMenu(menu)
            menu.Destroy()
            self.SetFocus()
            return

        # Get indent level for selected item
        self.indent = self.getItemIndent(item)
        if self.indent > 1:
            extract = item  # Specific Ion/file name
            item = self.getParentItem(item, 2)  # Item type
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
            self.extractGrandparent = None
        else:
            self.extractData = self.GetItemText(extract)
            self.extractParent = self.GetItemText(self.GetItemParent(extract))
            self.extractGrandparent = self.GetItemText(self.GetItemParent(self.GetItemParent(extract)))

        self.title = self.itemData.title

        if self.indent == 1 and self.extractData == None:
            self.on_refresh_document()
        elif self.itemType == 'Mass Spectra' and self.extractData == 'Mass Spectra':
            self.onCompareMS(evt=None)
        elif self.itemType in ['Mass Spectrum', 'Mass Spectrum (processed)', 'Mass Spectra']:
            if (self.extractData in ['Mass Spectrum', 'Mass Spectrum (processed)', 'Mass Spectra']
                or self.extractParent == "Mass Spectra"):
                self.onShowPlot(evt=ID_showPlotDocument)
            elif self.extractData == "UniDec":
                self.onShowUnidec(None)
            elif self.extractParent == "UniDec":
                self.onShowUnidec(None, plot_type=self.extractData)
            elif self.extractData == "Annotations":
                self.onAddAnnotation(None)
        elif self.itemType in ['Chromatogram', 'Chromatograms (EIC)', "Annotated data",
                               'Drift time (1D)', 'Drift time (1D, EIC, DT-IMS)', 'Drift time (1D, EIC)',
                               'Chromatograms (combined voltages, EIC)',
                               'Drift time (2D)', 'Drift time (2D, processed)', 'Drift time (2D, EIC)',
                               'Drift time (2D, combined voltages, EIC)', 'Drift time (2D, processed, EIC)',
                               'Input data', 'Statistical', 'Overlay', 'DT/MS', 'Tandem Mass Spectra']:
            self.onShowPlot(evt=None)
        elif self.itemType == 'Sample information':
            self.onShowSampleInfo(evt=None)
        elif self.indent == 1:
            self.onOpenDocInfo(evt=None)

        tend = time.clock()
        print('It took: %s seconds to process double-click.' % str(np.round((tend - tstart), 4)))

    def onThreading(self, evt, args, action):
        if action == "add_mzidentml_annotations":
            th = threading.Thread(target=self.on_add_mzID_file, args=(evt,))
        elif action == "load_mgf":
            th = threading.Thread(target=self.on_open_MGF_file, args=(evt,))
        elif action == "load_mzML":
            th = threading.Thread(target=self.on_open_mzML_file, args=(evt,))
        elif action == "load_thermo_RAW":
            th = threading.Thread(target=self.on_open_thermo_file, args=(evt,))

        # Start thread
        try:
            th.start()
        except:
            print("Failed to execute the '{}' operation in threaded mode. Consider switching it off?".format(action))

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

    def on_refresh_document(self, evt=None):
        document = self.presenter.documentsDict.get(self.title, None)
        if document == None:
            return

        # set what to plot
        mass_spectrum, chromatogram, mobiligram, heatmap = False, False, False, False
        # check document
        if document.dataType == 'Type: ORIGAMI':
            mass_spectrum, chromatogram, mobiligram, heatmap = True, True, True, True
            go_to_page = self.config.panelNames['MS']
        elif document.dataType == 'Type: MANUAL':
            mass_spectrum, chromatogram, mobiligram, heatmap = True, False, False, False
            go_to_page = self.config.panelNames['MS']
        elif document.dataType == 'Type: Multifield Linear DT':
            mass_spectrum, chromatogram, mobiligram, heatmap = True, True, True, True
            go_to_page = self.config.panelNames['MS']
        elif document.dataType == 'Type: 2D IM-MS':
            mass_spectrum, chromatogram, mobiligram, heatmap = False, False, False, True
            go_to_page = self.config.panelNames['2D']
        else:
            return

        # clear all plots
        self.presenter.view.panelPlots.on_clear_all_plots()

        if mass_spectrum:
            try:
                msX = document.massSpectrum['xvals']
                msY = document.massSpectrum['yvals']
                try: xlimits = document.massSpectrum['xlimits']
                except KeyError: xlimits = [document.parameters['startMS'], document.parameters['endMS']]
                name_kwargs = {"document":document.title, "dataset": "Mass Spectrum"}
                self.presenter.view.panelPlots.on_plot_MS(msX, msY, xlimits=xlimits, set_page=False, **name_kwargs)
            except: pass

        if chromatogram:
            try:
                rtX = document.RT['xvals']
                rtY = document.RT['yvals']
                xlabel = document.RT['xlabels']
                self.presenter.view.panelPlots.on_plot_RT(rtX, rtY, xlabel, set_page=False)
            except: pass

        if mobiligram:
            try:
                dtX = document.DT['xvals']
                dtY = document.DT['yvals']
                if len(dtY) >= 1:
                    try: dtY = document.DT['yvalsSum']
                    except KeyError: pass
                xlabel = document.DT['xlabels']
                self.presenter.view.panelPlots.on_plot_1D(dtX, dtY, xlabel, set_page=False)
            except: pass

        if heatmap:
            try:
                zvals = document.IMS2D['zvals']
                xvals = document.IMS2D['xvals']
                yvals = document.IMS2D['yvals']
                xlabel = document.IMS2D['xlabels']
                ylabel = document.IMS2D['ylabels']
                self.presenter.view.panelPlots.on_plot_2D(zvals, xvals, yvals, xlabel, ylabel, override=True)
            except: pass

        # go to page
        self.presenter.view.panelPlots.mainBook.SetSelection(go_to_page)

    def on_check_xlabels_RT(self):

        data = self.GetPyData(self.currentItem)
        xlabel = data['xlabels']

        if xlabel == 'Scans': idX = ID_xlabel_RT_scans
        elif xlabel == 'Time (min)': idX = ID_xlabel_RT_time_min
        elif xlabel == 'Retention time (min)': idX = ID_xlabel_RT_retTime_min

        return idX

    def on_check_xylabels_2D(self):  # checkCurrentXYlabels
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

            if xlabel == 'Scans': idX = ID_xlabel_2D_scans
            elif xlabel == 'Time (min)': idX = ID_xlabel_2D_time_min
            elif xlabel == 'Retention time (min)': idX = ID_xlabel_2D_retTime_min
            elif xlabel == 'Collision Voltage (V)': idX = ID_xlabel_2D_colVolt
            elif xlabel == 'Activation Voltage (V)': idX = ID_xlabel_2D_actVolt
            elif xlabel == 'Lab Frame Energy (eV)': idX = ID_xlabel_2D_labFrame
            elif xlabel == 'Activation Energy (eV)': idX = ID_xlabel_2D_actLabFrame
            elif xlabel == 'Mass-to-charge (Da)': idX = ID_xlabel_2D_massToCharge
            elif xlabel == 'm/z (Da)': idX = ID_xlabel_2D_mz
            elif xlabel == u'Wavenumber (cm⁻¹)': idX = ID_xlabel_2D_wavenumber
            elif xlabel == 'Charge': idX = ID_xlabel_2D_charge
            elif xlabel == u'Collision Cross Section (Å²)': idX = ID_xlabel_2D_ccs
            else: idX = ID_xlabel_2D_custom

            if ylabel == 'Drift time (bins)': idY = ID_ylabel_2D_bins
            elif ylabel == 'Drift time (ms)': idY = ID_ylabel_2D_ms
            elif ylabel == 'Arrival time (ms)': idY = ID_ylabel_2D_ms_arrival
            elif ylabel == u'Collision Cross Section (Å²)': idY = ID_ylabel_2D_ccs
            else:  idY = ID_ylabel_2D_custom

            return idX, idY
        except:
            return None, None

    def on_check_xlabels_1D(self):  # checkCurrentXYlabels1D
        if self.itemType == 'Drift time (1D)':
            data = self.itemData.DT

        # Get labels
        xlabel = data['xlabels']

        if xlabel == 'Drift time (bins)': idX = ID_xlabel_1D_bins
        elif xlabel == 'Drift time (ms)': idX = ID_xlabel_1D_ms
        elif xlabel == 'Arrival time (ms)': idX = ID_xlabel_1D_ms_arrival
        elif xlabel == u'Collision Cross Section (Å²)': idX = ID_xlabel_1D_ccs
        else:  idX = ID_ylabel_2D_bins

        return idX

    def on_check_xlabels_DTMS(self):  # checkCurrentXYlabelsMSDT
        if self.itemType == 'DT/MS':
            data = self.itemData.DTMZ

        # Get labels
        ylabel = data['ylabels']

        if ylabel == 'Drift time (bins)': idX = ID_ylabel_DTMS_bins
        elif ylabel == 'Drift time (ms)': idX = ID_ylabel_DTMS_ms
        elif ylabel == 'Arrival time (ms)': idX = ID_ylabel_DTMS_ms_arrival
        else:  idX = ID_ylabel_DTMS_bins

        return idX

    def onLoadInteractiveData(self, evt):
        """
        Load data into interactive document
        """

        # get document
        document = self.itemData
        evtID = evt.GetId()
        wildcard = "Text file (*.txt, *.csv, *.tab)| *.txt;*.csv;*.tab"
        dlg = wx.FileDialog(self.presenter.view, "Choose data [MS, RT, DT]...",
                            wildcard=wildcard,
                            style=wx.FD_MULTIPLE | wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            pathlist = dlg.GetPaths()
            filenames = dlg.GetFilenames()
            for path, fname in zip(pathlist, filenames):
                if evtID == ID_docTree_add_MS_to_interactive:
                    msDataX, msDataY, __, xlimits = self.presenter.onMSTextFileFcn(path=path, return_data=True)
                    document.gotMultipleMS = True
                    data = {'xvals':msDataX, 'yvals':msDataY, 'xlabels':'m/z (Da)',
                            'xlimits':xlimits, 'file_path':path}

                    if fname in document.multipleMassSpectrum:
                        if not self.config.import_duplicate_ask:
                            msg = "{} already exists in the document. What would you like to do about it?".format(fname)
                            dlg = dialogAskOverride(self, self.config, msg)
                            dlg.ShowModal()
                        if self.config.import_duplicate_action == "merge":
                            # retrieve and merge
                            old_data = document.multipleMassSpectrum[fname]
                            data = merge_two_dicts(old_data, data)
                        elif self.config.import_duplicate_action == "duplicate":
                            title = "{} (2)".format(fname)

                    document.multipleMassSpectrum[fname] = data

                elif evtID == ID_docTree_add_RT_to_interactive:
                    rtDataX, rtDataY, __, xlimits = self.presenter.onMSTextFileFcn(path=path, return_data=True)
                    document.gotMultipleRT = True
                    data = {'xvals':rtDataX, 'yvals':rtDataY, 'xlabels':'Scans',
                            'ylabels':'Intensity', 'xlimits':xlimits, 'file_path':path}

                    if fname in document.multipleRT:
                        if not self.config.import_duplicate_ask:
                            msg = "{} already exists in the document. What would you like to do about it?".format(fname)
                            dlg = dialogAskOverride(self, self.config, msg)
                            dlg.ShowModal()
                        if self.config.import_duplicate_action == "merge":
                            # retrieve and merge
                            old_data = document.multipleRT[fname]
                            data = merge_two_dicts(old_data, data)
                        elif self.config.import_duplicate_action == "duplicate":
                            title = "{} (2)".format(fname)

                    document.multipleRT[fname] = data

                elif evtID == ID_docTree_add_DT_to_interactive:
                    dtDataX, dtDataY, __, xlimits = self.presenter.onMSTextFileFcn(path=path, return_data=True)
                    data = {'xvals':dtDataX, 'yvals':dtDataY, 'xlabels':'Drift time (bins)',
                            'ylabels':'Intensity', 'xlimits':xlimits, 'file_path':path}

                    if fname in document.multipleDT:
                        if not self.config.import_duplicate_ask:
                            msg = "{} already exists in the document. What would you like to do about it?".format(fname)
                            dlg = dialogAskOverride(self, self.config, msg)
                            dlg.ShowModal()
                        if self.config.import_duplicate_action == "merge":
                            # retrieve and merge
                            old_data = document.multipleDT[fname]
                            data = merge_two_dicts(old_data, data)
                        elif self.config.import_duplicate_action == "duplicate":
                            title = "{} (2)".format(fname)

                    document.multipleDT[fname] = data

                elif evtID == ID_docTree_add_2DT_to_interactive:
                    imsData2D, xAxisLabels, yAxisLabels = text_heatmap_open(path=path)
                    imsData1D = np.sum(imsData2D, axis=1).T
                    rtDataY = np.sum(imsData2D, axis=0)
                    color = convertRGB255to1(self.config.customColors[randomIntegerGenerator(0, 15)])
                    document.gotExtractedIons = True
                    data = {'zvals':imsData2D, 'xvals':xAxisLabels,
                            'xlabels':'Scans', 'yvals':yAxisLabels,
                            'ylabels':'Drift time (bins)', 'yvals1D':imsData1D,
                            'yvalsRT':rtDataY, 'cmap':self.config.currentCmap,
                            'mask':self.config.overlay_defaultMask,
                            'alpha':self.config.overlay_defaultAlpha,
                            'min_threshold':0, 'max_threshold':1, 'color':color}
                    if fname in document.IMS2Dions:
                        if not self.config.import_duplicate_ask:
                            msg = "{} already exists in the document. What would you like to do about it?".format(fname)
                            dlg = dialogAskOverride(self, self.config, msg)
                            dlg.ShowModal()
                        if self.config.import_duplicate_action == "merge":
                            # retrieve and merge
                            old_data = document.IMS2Dions[fname]
                            data = merge_two_dicts(old_data, data)
                        elif self.config.import_duplicate_action == "duplicate":
                            title = "{} (2)".format(fname)

                    document.IMS2Dions[fname] = data

                elif evtID == ID_docTree_add_other_to_interactive:
                    try:
                        title, data = self.onLoadOtherData(path)
                        if title is None or data is None:
                            return
                        if title in document.other_data:
                            if not self.config.import_duplicate_ask:
                                msg = "{} already exists in the document. What would you like to do about it?".format(title)
                                dlg = dialogAskOverride(self, self.config, msg)
                                dlg.ShowModal()

                            if self.config.import_duplicate_action == "merge":
                                # retrieve and merge
                                old_data = document.other_data[title]
                                data = merge_two_dicts(old_data, data)
                            elif self.config.import_duplicate_action == "duplicate":
                                title = "{} (2)".format(title)

                        document.other_data[title] = data
                    except Exception, e:
                        print(e)
                        self.presenter.onThreading(None,
                                                   ("Failed to load data for: {}".format(path), 4, 5),
                                                   action='updateStatusbar')

                elif evtID == ID_docTree_add_matrix_to_interactive:
                    df = pd.read_csv(fname, sep='\t|,', engine='python', header=None)
                    labels = list(df.iloc[:, 0].dropna())
                    zvals = df.iloc[1::, 1::].astype('float32').as_matrix()

                    title = "Matrix: {}".format(os.path.basename(fname))
                    data = {"plot_type":"matrix", 'zvals':zvals,
                            'cmap':self.config.currentCmap, 'matrixLabels':labels,
                            "path":fname, "plot_modifiers":{}}
                    if title in document.other_data:
                        if not self.config.import_duplicate_ask:
                            msg = "{} already exists in the document. What would you like to do about it?".format(title)
                            dlg = dialogAskOverride(self, self.config, msg)
                            dlg.ShowModal()

                        if self.config.import_duplicate_action == "merge":
                            # retrieve and merge
                            old_data = document.other_data[title]
                            data = merge_two_dicts(old_data, data)
                        elif self.config.import_duplicate_action == "duplicate":
                            title = "{} (2)".format(title)

                    document.other_data[title] = data

                elif evtID == ID_docTree_add_comparison_to_interactive:
                    print("Load comparison")

        dlg.Destroy()

        self.presenter.OnUpdateDocument(document, 'document')

    def onLoadOtherData(self, fname):
        if fname.endswith(".csv"):
            df = pd.read_csv(fname, sep=',', engine='python', header=None)
        elif fname.endswith(".txt"):
            df = pd.read_csv(fname, sep='\t', engine='python', header=None)

        title = os.path.basename(fname)
        plot_type = "multi-line"
        plot_modifiers = {}
        if "title" in list(df.iloc[:, 0]):
            idx = list(df.iloc[:, 0]).index("title")
            title = list(df.iloc[idx, 1::])[0]

        row_labels = list(df.iloc[:, 0])
        if "plot_type" in row_labels:
            idx = row_labels.index("plot_type")
            plot_type = list(df.iloc[idx, 1::])[0]

        if "x_label" in row_labels:
            idx = row_labels.index("x_label")
            x_label = list(df.iloc[idx, 1::])[0]
        else: x_label = ""

        if "y_label" in row_labels:
            idx = row_labels.index("y_label")
            y_label = list(df.iloc[idx, 1::])[0]
        else: y_label = ""

        if "x_unit" in row_labels:
            idx = row_labels.index("x_unit")
            x_unit = list(df.iloc[idx, 1::])[0]
        else: x_unit = ""

        if "y_unit" in row_labels:
            idx = row_labels.index("y_unit")
            y_unit = list(df.iloc[idx, 1::])[0]
        else: y_unit = ""

        if "order" in row_labels:
            idx = row_labels.index("order")
            order = list(df.iloc[idx, 1::])
        else: order = []

        if "label" in row_labels:
            idx = row_labels.index("label")
            labels = list(df.iloc[idx, 1::].dropna())
        elif "labels" in row_labels:
            idx = row_labels.index("labels")
            labels = list(df.iloc[idx, 1::].dropna())
        else: labels = []

        if "x_labels" in row_labels:
            idx = row_labels.index("x_labels")
            x_labels = list(df.iloc[idx, 1::].dropna())
        else: x_labels = []

        if "y_labels" in row_labels:
            idx = row_labels.index("y_labels")
            y_labels = list(df.iloc[idx, 1::].dropna())
        else: y_labels = []

        if "xlimits" in row_labels:
            idx = row_labels.index("xlimits")
            xlimits = list(df.iloc[idx, 1:3].dropna().astype('float32'))
        else: xlimits = [None, None]

        if "ylimits" in row_labels:
            idx = row_labels.index("ylimits")
            ylimits = list(df.iloc[idx, 1:3].dropna().astype('float32'))
        else: ylimits = [None, None]

        if "color" in row_labels:
            idx = row_labels.index("color")
            colors = list(df.iloc[idx, 1::].dropna())
        elif "colors" in row_labels:
            idx = row_labels.index("colors")
            colors = list(df.iloc[idx, 1::].dropna())
        else: colors = []

        if "column_type" in row_labels:
            idx = row_labels.index("column_type")
            column_types = list(df.iloc[idx, 1::].dropna())
        else: column_types = []

        if "legend_labels" in row_labels:
            idx = row_labels.index("legend_labels")
            legend_labels = list(df.iloc[idx, 1::].dropna())
        else: legend_labels = []

        if "legend_colors" in row_labels:
            idx = row_labels.index("legend_colors")
            legend_colors = list(df.iloc[idx, 1::].dropna())
        else: legend_colors = []

        if "hover_labels" in row_labels:
            idx = row_labels.index("hover_labels")
            hover_labels = list(df.iloc[idx, 1::].dropna())
        else: hover_labels = []

        plot_modifiers.update(legend_labels=legend_labels, legend_colors=legend_colors,
                              xlimits=xlimits, ylimits=ylimits)
        xvals, yvals, zvals, xvalsErr, yvalsErr, itemColors, itemLabels = [], [], [], [], [], [], []
        xyvals, urls = [], []
        axis_y_min, axis_y_max, axis_note = [], [], []
        xy_labels = []

        # get first index
        first_num_idx = pd.to_numeric(df.iloc[:, 0], errors='coerce').notnull().idxmax()

        # check if axis labels have been provided
        for xy_axis in ["axis_x", "axis_y", "axis_xerr", "axis_yerr", "axis_color", "axis_colors",
                        "axis_label", "axis_labels", "axis_y_min", "axis_y_max", "axis_xy",
                        "axis_url"]:
            if xy_axis in row_labels:
                idx = row_labels.index(xy_axis)
                xy_labels = list(df.iloc[idx, :])

        if len(xy_labels) == df.shape[1]:
            df = df.iloc[first_num_idx:, :]  # [pd.to_numeric(df.iloc[:,0], errors='coerce').notnull()]
            for i, xy_label in enumerate(xy_labels):
                if xy_label == "axis_x":
                    xvals.append(np.asarray(df.iloc[:, i].dropna().astype('float32')))
                if xy_label == "axis_y":
                    yvals.append(np.asarray(df.iloc[:, i].dropna().astype('float32')))
                if xy_label == "axis_xerr":
                    xvalsErr.append(np.asarray(df.iloc[:, i].dropna().astype('float32')))
                if xy_label == "axis_yerr":
                    yvalsErr.append(np.asarray(df.iloc[:, i].dropna().astype('float32')))
                if xy_label == "axis_y_min":
                    axis_y_min.append(np.asarray(df.iloc[:, i].dropna().astype('float32')))
                if xy_label == "axis_y_max":
                    axis_y_max.append(np.asarray(df.iloc[:, i].dropna().astype('float32')))
                if xy_label in ["axis_xy", "axis_yx"]:
                    xyvals.append(np.asarray(df.iloc[:, i].dropna().astype('float32')))
                if xy_label in ["axis_color", "axis_colors"]:
                    _colors = list(df.iloc[:, i].dropna().astype("str"))
                    _colorsRGB = []
                    for _color in _colors:
                        _colorsRGB.append(convertHEXtoRGB1(str(_color)))
                    itemColors.append(_colorsRGB)
                    plot_modifiers['color_items'] = True
                if xy_label in ["axis_label", "axis_labels"]:
                    itemLabels.append(list(df.iloc[:, i].replace(np.nan, '', regex=True).astype("str")))
                    plot_modifiers['label_items'] = True
                if xy_label == "axis_note":
                    axis_note.append(np.asarray(df.iloc[:, i].replace(np.nan, '', regex=True).astype('str')))
                if xy_label == "axis_url":
                    urls.append(np.asarray(df.iloc[:, i].astype('str')))
        else:
            # drop all other non-numeric rows
            df = df[pd.to_numeric(df.iloc[:, 0], errors='coerce').notnull()]
            df = df.astype('float32')

            # extract x, y and zvals
            if df.shape[1] >= 2:
                xvals = list(df.iloc[:, 0])
            else:
                return None, None

            if df.shape[1] == 2:
                yvals = list(df.iloc[:, 1])

            if df.shape[1] > 2:
                zvals = df.iloc[:, 1::].as_matrix()

            if plot_type in ["multi-line", "waterfall", "scatter", "grid-line", "grid-scatter"]:
                yvals_new = []
                for item in xrange(zvals.shape[1]):
                    yvals_new.append(zvals[:, item])

                # replace
                xvals = [xvals]
                yvals = yvals_new
                zvals = []
                if len(labels) != len(yvals):
                    labels = [""] * len(yvals)

        # create combination of x y columns
        if len(xyvals) > 0:
            from itertools import product
            xyproduct = list(product(xyvals, xyvals))
            xvals, yvals = [], []
            for iprod in xyproduct:
                xvals.append(iprod[0])
                yvals.append(iprod[1])
            if len(x_labels) == len(xyvals) and len(y_labels) == len(xyvals):
                xyproduct = list(product(x_labels, y_labels))
                x_labels, y_labels = [], []
                for iprod in xyproduct:
                    x_labels.append(iprod[0])
                    y_labels.append(iprod[1])

        if plot_type in ["grid-line", "grid-scatter", "grid-mixed"]:
            n_xvals = len(xvals)
            n_yvals = len(yvals)
            n_grid = max([n_xvals, n_yvals])
            if n_grid in [2]: n_rows, n_cols = 1, 2
            elif n_grid in [3, 4]: n_rows, n_cols = 2, 2
            elif n_grid in [5, 6]: n_rows, n_cols = 2, 3
            elif n_grid in [7, 8, 9]: n_rows, n_cols = 3, 3
            elif n_grid in [10, 11, 12]: n_rows, n_cols = 3, 4
            elif n_grid in [13, 14, 15, 16]: n_rows, n_cols = 4, 4
            elif n_grid in [17, 18, 19, 20, 21, 22, 23, 24, 25]: n_rows, n_cols = 5, 5
            else:
                dialogs.dlgBox(exceptionTitle='Error',
                               exceptionMsg="Cannot plot grid larger than 5 x 5 (25 cells). You have selected {}".format(n_grid),
                               type="Error", exceptionPrint=True)
                return
            plot_modifiers.update(n_grid=n_grid, n_rows=n_rows, n_cols=n_cols)

        # check if we need to add any metadata
        if len(colors) == 0 or len(colors) < len(yvals):
            colors = self.presenter.view.panelPlots.onChangePalette(None,
                                                                    n_colors=len(yvals),
                                                                    return_colors=True)

        if len(labels) != len(yvals):
            labels = [""] * len(yvals)

        msg = "Item {} has: x-columns ({}), x-errors ({}), y-columns ({}), x-errors ({}), ".format(os.path.basename(fname), len(xvals), len(xvalsErr), len(yvals), len(yvalsErr)) + \
              "labels ({}), colors ({})".format(len(labels), len(colors))
        print(msg)

        # update title
        _plot_types = {"multi-line":"Multi-line", "scatter":"Scatter",
                       "line":"Line", "waterfall":"Waterfall",
                       "grid-line":"Grid-line", "grid-scatter":"Grid-scatter",
                       "vertical-bar":"V-bar", "horizontal-bar":"H-bar"}

        title = "{}: {}".format(_plot_types[plot_type], title)
        other_data = {"plot_type":plot_type,
                      "xvals":xvals,
                      "yvals":yvals,
                      "zvals":zvals,
                      "xvalsErr":xvalsErr,
                      "yvalsErr":yvalsErr,
                      "yvals_min":axis_y_min,
                      "yvals_max":axis_y_max,
                      "itemColors":itemColors,
                      "itemLabels":itemLabels,
                      "xlabel":_replace_labels(x_label),
                      "ylabel":_replace_labels(y_label),
                      "xlimits":xlimits,
                      "ylimits":ylimits,
                      "xlabels":x_labels,
                      "ylabels":y_labels,
                      "hover_labels":hover_labels,
                      "x_unit":x_unit,
                      "y_unit":y_unit,
                      "colors":colors,
                      "labels":labels,
                      "urls":urls,
                      "column_types":column_types,
                      "column_order":order,
                      "path":fname,
                      "plot_modifiers":plot_modifiers}

        return title, other_data

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
            parent = self.getParentItem(item, 1)  # File name
            extract = item  # Specific Ion/file name
            item = self.getParentItem(item, 2)  # Item type
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

        try: currentDoc = self.itemData.title
        except:
            print("Please select document in the document tree. Sometimes you might have to right-click on it.")
            return
        document = self.presenter.documentsDict[currentDoc]

        # Check what is going to be deleted
        # MS
        if self.itemType == 'Mass Spectrum':
            # remove annotations
            if "Annotations" in self.extractData and self.extractParent == "Mass Spectrum":
                del self.presenter.documentsDict[currentDoc].massSpectrum['annotations']
            elif self.extractParent == "Annotations":
                del self.presenter.documentsDict[currentDoc].massSpectrum['annotations'][self.extractData]
            # remove unidec data
            elif "UniDec" in self.extractData and self.extractParent == "Mass Spectrum":
                del self.presenter.documentsDict[currentDoc].massSpectrum['unidec']
            elif self.extractParent == "UniDec":
                del self.presenter.documentsDict[currentDoc].massSpectrum['unidec'][self.extractData]
            # remove mass spectrum
            else:
                del self.presenter.documentsDict[currentDoc].massSpectrum
                self.presenter.documentsDict[currentDoc].gotMS = False

        if self.itemType == 'Mass Spectrum (processed)':
            # remove annotations
            if "Annotations" in self.extractData and self.extractParent == "Mass Spectrum (processed)":
                del self.presenter.documentsDict[currentDoc].smoothMS['annotations']
            elif self.extractParent == "Annotations":
                del self.presenter.documentsDict[currentDoc].smoothMS['annotations'][self.extractData]
            # remove unidec data
            elif "UniDec" in self.extractData and self.extractParent == "Mass Spectrum (processed)":
                del self.presenter.documentsDict[currentDoc].smoothMS['unidec']
            elif self.extractParent == "UniDec":
                del self.presenter.documentsDict[currentDoc].smoothMS['unidec'][self.extractData]
            # remove mass spectrum
            else:
                del self.presenter.documentsDict[currentDoc].smoothMS

        elif self.itemType == 'Mass Spectra':
            # remove unidec data
            if self.extractData == "UniDec" and self.indent == 4:
                del self.presenter.documentsDict[currentDoc].multipleMassSpectrum[self.extractParent]['unidec']
            elif self.extractParent == "UniDec" and self.indent == 5:
                del self.presenter.documentsDict[currentDoc].multipleMassSpectrum[self.extractGrandparent]['unidec'][self.extractData]
            # remove annotations
            elif "Annotations" in self.extractData and self.indent == 4:
                del self.presenter.documentsDict[currentDoc].multipleMassSpectrum[self.extractParent]['annotations']
            elif "Annotations" in self.extractParent and self.indent == 5:
                del self.presenter.documentsDict[currentDoc].multipleMassSpectrum[self.extractGrandparent]['annotations'][self.extractData]
            # remove mass spectra
            elif self.extractParent == "Mass Spectra":
                del self.presenter.documentsDict[currentDoc].multipleMassSpectrum[self.extractData]
            elif self.extractData == "Mass Spectra":
                self.presenter.documentsDict[currentDoc].multipleMassSpectrum = {}
            # check length
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

        elif self.itemType == 'Annotated data':
            # remove annotations
            if "Annotations" in self.extractData and self.indent == 4:
                del self.presenter.documentsDict[currentDoc].other_data[self.extractParent]['annotations']
            elif "Annotations" in self.extractParent and self.indent == 5:
                del self.presenter.documentsDict[currentDoc].other_data[self.extractGrandparent]['annotations'][self.extractData]
            elif self.extractData == 'Annotated data':
                self.presenter.documentsDict[currentDoc].other_data = {}
            else:
                del self.presenter.documentsDict[currentDoc].other_data[self.extractData]

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
        self.addDocument(docData=document)

        # Expand item

    def setDocument(self, document_old, document_new):
        # try to get dataset object
        try: docItem = self.getItemByData(document_old)
        except: docItem = False

        if docItem is not False:
            try:
                self.SetPyData(docItem, document_new)
            except:
                self.presenter.OnUpdateDocument(document_new, 'document')
        else:
            self.presenter.OnUpdateDocument(document_new, 'document')

    def onDeleteAllDocuments(self, evt):
        """ Alternative function to delete documents """

        dlg = dialogs.dlgBox(exceptionTitle='Are you sure?',
                             exceptionMsg=''.join(["Are you sure you would like to delete ALL documents?"]),
                             type="Question")
        if dlg == wx.ID_NO:
            self.presenter.onThreading(None, ('Cancelled operation', 4, 5)    , action='updateStatusbar')
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
            parent = self.getParentItem(item, 1)  # File name
            extract = item  # Specific Ion/file name
            item = self.getParentItem(item, 2)  # Item type
            itemType = self.GetItemText(item)
        else:
            extract = None
            parent = item

        # Get the ion/file name from deeper indent
        if extract == None:
            self.extractData = None
            self.extractParent = None
            self.extractGrandparent = None
        else:
            self.extractParent = self.GetItemText(self.GetItemParent(extract))
            self.extractData = self.GetItemText(extract)
            self.extractGrandparent = self.GetItemText(self.GetItemParent(self.GetItemParent(extract)))

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

        document = self.itemData.title
        dataset = self.extractData

        if data is None:
            if self.itemType == "Mass Spectrum":
                data = self.itemData.massSpectrum
                dataset = "Mass Spectrum"
            elif self.itemType == "Mass Spectrum (processed)":
                data = self.itemData.smoothMS
                dataset = "Mass Spectrum (processed)"
            elif self.itemType == "Mass Spectra" and self.extractData == "Annotations":
                data = self.itemData.multipleMassSpectrum[self.extractParent]
                dataset = self.extractParent
            elif "Annotated data" in self.itemType and self.extractData == "Annotations":
                data = self.itemData.other_data[self.extractParent]
                dataset = self.extractParent

        if "annotations" in data:
            annotations = data['annotations']
        else:
            annotations = {}

        if self.annotateDlg is not None:
            msg = "An instance of annotation window is already open. Please close it first."
            args = (msg, 4, 5)
            self.presenter.onThreading(None, args, action='updateStatusbar')
            dialogs.dlgBox(exceptionTitle="Window already open",
                           exceptionMsg=msg, type="Error")
            return

        # waterfall plot
        if ("Waterfall (Raw):" in self.extractData):
            data = None
            plot = self.presenter.view.panelPlots.plotWaterfallIMS
        # Annotated data
        elif ("Multi-line: " in self.extractData or "Multi-line: " in self.extractParent or
              "V-bar: " in self.extractData or "V-bar: " in self.extractParent or
              "H-bar: " in self.extractData or "H-bar: " in self.extractParent or
              "Scatter: " in self.extractData or "Scatter: " in self.extractParent or
              "Waterfall: " in self.extractData or "Waterfall: " in self.extractParent or
              "Line: " in self.extractData or "Line: " in self.extractParent):
            data = None
            plot = self.presenter.view.panelPlots.plotOther
        # mass spectra
        else:
            data = np.transpose([data["xvals"], data["yvals"]])
            plot = self.presenter.view.panelPlots.plot1

        _plot_types = {"multi-line":"Multi-line", "scatter":"Scatter",
                       "line":"Line", "waterfall":"Waterfall",
                       "grid-line":"Grid-line", "grid-scatter":"Grid-scatter",
                       "vertical-bar":"V-bar", "horizontal-bar":"H-bar"}

        kwargs = {"document":document, "dataset":dataset,
                  "data":data, "plot":plot,
                  "annotations":annotations}

        self.annotateDlg = panelAnnotatePeaks(self.parent, self, self.config,
                                              self.icons, **kwargs)
        self.annotateDlg.Show()

    def on_get_annotation_dataset(self, document, dataset):
        document = self.presenter.documentsDict[document]
        annotations = None
        if dataset == "Mass Spectrum":
            annotations = document.massSpectrum['annotations']
        elif dataset == "Mass Spectrum (processed)":
            annotations = document.smoothMS['annotations']
        elif "Waterfall (Raw):" in dataset:
            annotations = document.IMS2DoverlayData[dataset]['annotations']
        elif ("Multi-line: " in dataset or "V-bar: " in dataset or
              "H-bar: " in dataset or "Scatter: " in dataset or
              "Waterfall: " in dataset or "Line: " in dataset):
            annotations = document.other_data[dataset]['annotations']
        else:
            annotations = document.multipleMassSpectrum[dataset]['annotations']

        return document, annotations

    def onUpdateAnotations(self, annotations, document, dataset, set_data_only=False):
        """
        Update annotations in specified document/dataset
        ----------
        Parameters
        ----------
        annotations : dict
            dictionary with annotations
        document : str
            name of the document
        dataset : str
            name of the dataset
        set_data_only : bool
            specify whether all annotations should be removed and readded or if
            we it should simply set data
        """

        document = self.presenter.documentsDict[document]
        item = False
        docItem = False
        if dataset == "Mass Spectrum":
            item = self.getItemByData(document.massSpectrum)
            document.massSpectrum['annotations'] = annotations
            annotation_data = document.massSpectrum['annotations']
        elif dataset == "Mass Spectrum (processed)":
            item = self.getItemByData(document.smoothMS)
            document.smoothMS['annotations'] = annotations
            annotation_data = document.smoothMS['annotations']
        elif "Waterfall (Raw):" in dataset:
            item = self.getItemByData(document.IMS2DoverlayData[dataset])
            document.IMS2DoverlayData[dataset]['annotations'] = annotations
            annotation_data = document.IMS2DoverlayData[dataset]['annotations']
        elif ("Multi-line: " in dataset or "V-bar: " in dataset or
              "H-bar: " in dataset or "Scatter: " in dataset or
              "Waterfall: " in dataset or "Line: " in dataset):
            item = self.getItemByData(document.other_data[dataset])
            document.other_data[dataset]['annotations'] = annotations
            annotation_data = document.other_data[dataset]['annotations']
        else:
            item = self.getItemByData(document.multipleMassSpectrum[dataset])
            document.multipleMassSpectrum[dataset]['annotations'] = annotations
            annotation_data = document.multipleMassSpectrum[dataset]['annotations']

        if item is not False and not set_data_only:
            self.append_annotation(item, annotation_data)
            self.presenter.OnUpdateDocument(document, 'no_refresh')
        else:
            try: docItem = self.getItemByData(document)
            except: docItem = False
            if docItem is not False:
                self.SetPyData(docItem, document)
                self.presenter.documentsDict[document.title] = document
            else:
                self.presenter.OnUpdateDocument(document, 'document')

    def append_annotation(self, item, annotation_data, expand=True):
        """
        Update annotations in the document tree
        ----------
        Parameters
        ----------
        item : wxPython document tree item
            item in the document tree that should be cleared and re-filled           
        annotation_data : dict
            dictionary with annotations
        expand : bool
            specify if tree item should be expanded

        """
        child, cookie = self.GetFirstChild(item)
        while child.IsOk():
            if self.GetItemText(child) == "Annotations":
                self.Delete(child)
            child, cookie = self.GetNextChild(item, cookie)

        if len(annotation_data) == 0:
            return

        itemAnnot = self.AppendItem(item, 'Annotations')
        self.SetItemImage(itemAnnot, self.bulets_dict["annot"], wx.TreeItemIcon_Normal)
        for key in annotation_data:
            itemAnnotIndividual = self.AppendItem(itemAnnot, key)
            self.SetPyData(itemAnnotIndividual, annotation_data[key])
            self.SetItemImage(itemAnnotIndividual, self.bulets_dict["annot"], wx.TreeItemIcon_Normal)

        if expand:
            self.Expand(itemAnnot)

    def onDuplicateAnnotations(self, evt):
        """
        Duplicate annotations from one spectrum to another
        ----------
        Parameters
        ----------
        evt : wxPython event
            unused
        """

        # get document and annotations
        document = self.presenter.documentsDict[self.itemData.title]
        if self.itemType == "Mass Spectrum":
            annotations = deepcopy(document.massSpectrum.get('annotations', None))
        elif self.itemType == "Mass Spectrum (processed)":
            annotations = deepcopy(document.smoothMS.get('annotations', None))
        else:
            annotations = deepcopy(document.multipleMassSpectrum[self.extractData].get('annotations', None))

        if annotations is None or len(annotations) == 0:
            self.presenter.onThreading(None, ("This item has no annotations to duplicate.", 4, 5),
                                       action='updateStatusbar')
            return

        # ask which document to add it to
        document_list, document_spectrum_list = [], {}
        for document_title in self.presenter.documentsDict:
            document_spectrum_list[document_title] = []
            if self.presenter.documentsDict[document_title].gotMultipleMS:
                document_spectrum_list[document_title].extend(self.presenter.documentsDict[document_title].multipleMassSpectrum.keys())
            if len(self.presenter.documentsDict[document_title].massSpectrum) > 0:
                document_spectrum_list[document_title].append("Mass Spectrum")
            if len(self.presenter.documentsDict[document_title].smoothMS) > 0:
                document_spectrum_list[document_title].append("Mass Spectrum (processed)")
            if len(self.presenter.documentsDict[document_title].IMS2DoverlayData) > 0:
                for key in self.presenter.documentsDict[document_title].IMS2DoverlayData:
                    if "Waterfall (Raw):" in key: document_spectrum_list[document_title].append(key)

            if len(document_spectrum_list[document_title]) > 0:
                document_list.append(document_title)

        kwargs = dict(set_document=document.title)
        duplicateDlg = panelSelectDataset(self.presenter.view, self, document_list, document_spectrum_list, **kwargs)
        if duplicateDlg.ShowModal() == wx.ID_OK:
            pass

        duplicate_document = duplicateDlg.document
        duplicate_dataset = duplicateDlg.dataset

        if duplicate_document is None or duplicate_dataset is None:
            self.presenter.onThreading(None, ("Operation was cancelled.", 4, 5),
                                       action='updateStatusbar')
            return

        item = False
        # add annotations to document
        duplicate_document = self.presenter.documentsDict[duplicate_document]
        if duplicate_dataset == "Mass Spectrum":
            item = self.getItemByData(duplicate_document.massSpectrum)
            duplicate_document.massSpectrum["annotations"] = annotations
            annotation_data = duplicate_document.massSpectrum["annotations"]
        elif duplicate_dataset == "Mass Spectrum (processed)":
            item = self.getItemByData(duplicate_document.massSpectrum)
            duplicate_document.smoothMS["annotations"] = annotations
            annotation_data = duplicate_document.smoothMS["annotations"]
        elif "Waterfall (Raw):" in duplicate_dataset:
            item = self.getItemByData(duplicate_document.IMS2DoverlayData[duplicate_dataset])
            duplicate_document.IMS2DoverlayData[duplicate_dataset]["annotations"] = annotations
            annotation_data = duplicate_document.IMS2DoverlayData[duplicate_dataset]["annotations"]
        else:
            item = self.getItemByData(duplicate_document.multipleMassSpectrum[duplicate_dataset])
            duplicate_document.multipleMassSpectrum[duplicate_dataset]["annotations"] = annotations
            annotation_data = duplicate_document.multipleMassSpectrum[duplicate_dataset]["annotations"]

        if item is not False:
            self.append_annotation(item, annotation_data)
            self.presenter.OnUpdateDocument(duplicate_document, 'no_refresh')
        else:
            self.presenter.OnUpdateDocument(duplicate_document, 'document')

        msg = "Duplicated annotations to {} - {}".format(duplicate_document.title,
                                                         duplicate_dataset)
        self.presenter.onThreading(None, (msg, 4, 5), action='updateStatusbar')

    def onShowAnnotations(self, evt):
        """
        Show annotations in the currently shown mass spectrum
        ----------
        Parameters
        ----------
        evt : wxPython event
            unused
        """
        document = self.presenter.documentsDict[self.itemData.title]
        plot_obj = self.presenter.view.panelPlots.plot1
        if self.itemType == "Mass Spectrum":
            annotations = document.massSpectrum['annotations']
        elif self.itemType == "Mass Spectrum (processed)":
            annotations = document.smoothMS['annotations']
        elif self.itemType == "Mass Spectra":
            annotations = document.multipleMassSpectrum[self.extractParent]['annotations']
        elif (self.itemType == "Annotated data" and
              ("Waterfall: " in self.extractParent or "Multi-line: " in self.extractParent or
               "V-bar: " in self.extractParent or "H-bar: " in self.extractParent or
               "Scatter: " in self.extractParent or "Line: " in self.extractParent)):
            annotations = document.other_data[self.extractParent]['annotations']
            plot_obj = self.presenter.view.panelPlots.plotOther

        plot_obj.plot_remove_text_and_lines()
        _ymax = []

        label_kwargs = self.presenter.view.panelPlots._buildPlotParameters(plotType="label")
        for key in annotations:
            annotation = annotations[key]
            intensity = str2num(annotation['intensity'])
            charge = annotation['charge']
            min_x_value = annotation['min']
            max_x_value = annotation['max']
            color_value = annotation.get('color', self.config.interactive_ms_annotations_color)
            add_arrow = annotation.get('add_arrow', False)
            show_label = annotation['label']

            if 'isotopic_x' in annotation:
                mz_value = annotation['isotopic_x']
                if mz_value in ["", 0] or mz_value < min_x_value:
                    mz_value = max_x_value - ((max_x_value - min_x_value) / 2)
            else:
                mz_value = max_x_value - ((max_x_value - min_x_value) / 2)

            label_x_position = annotation.get('position_label_x', mz_value)
            label_y_position = annotation.get('position_label_y', intensity)

            if show_label == "":
                show_label = "{}, {}\nz={}".format(round(mz_value, 4),
                                                   intensity,
                                                   charge)

            # add  custom name tag
            try:
                obj_name_tag = "{}|-|{}|-|{} - {}|-|{}".format(self.itemData.title,
                                                               self.extractParent,
                                                               min_x_value, max_x_value,
                                                               "annotation")
                label_kwargs['text_name'] = obj_name_tag
            except: pass

            if add_arrow:
                arrow_x_position = label_x_position
                label_x_position = annotation.get('position_label_x', label_x_position)
                arrow_dx = label_x_position - arrow_x_position
                arrow_y_position = label_y_position
                label_y_position = annotation.get('position_label_y', label_y_position)
                arrow_dy = label_y_position - arrow_y_position

            plot_obj.plot_add_text_and_lines(
                xpos=label_x_position, yval=label_y_position,
                label=show_label, vline=False, stick_to_intensity=True,
                yoffset=self.config.annotation_label_y_offset,
                color=color_value, **label_kwargs)

            _ymax.append(label_y_position)
            if add_arrow:
                arrow_list = [arrow_x_position, arrow_y_position, arrow_dx, arrow_dy]
                plot_obj.plot_add_arrow(arrow_list, stick_to_intensity=True)

        if self.config.annotation_zoom_y:
            try: plot_obj.on_zoom_y_axis(endY=np.amax(_ymax) * self.config.annotation_zoom_y_multiplier)
            except TypeError: pass

        plot_obj.repaint()

    def OnRightClickMenu(self, evt):
        """ Create and show up popup menu"""

        # Make some bindings
        self.Bind(wx.EVT_MENU, self.presenter.on_save_all_documents, id=ID_saveAllDocuments)
        self.Bind(wx.EVT_MENU, self.onDeleteAllDocuments, id=ID_removeAllDocuments)

        # Get selected item
        item = self.GetSelection()
        self.currentItem = item
        # Get the current text value for selected item
        itemType = self.GetItemText(item)
        if itemType == 'Current documents':
            menu = wx.Menu()
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveAllDocuments,
                                         text='Save all documents',
                                         bitmap=self.icons.iconsLib['save_multiple_16']))
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_removeAllDocuments,
                                         text='Delete all documents',
                                         bitmap=self.icons.iconsLib['bin16']))
            self.PopupMenu(menu)
            menu.Destroy()
            self.SetFocus()
            return

        # Get indent level for selected item
        self.indent = self.getItemIndent(item)
        if self.indent > 1:
            parent = self.getParentItem(item, 1)  # File name
            extract = item  # Specific Ion/file name
            item = self.getParentItem(item, 2)  # Item type
            itemType = self.GetItemText(item)
        else:
            extract = None
            parent = item

        # Get the ion/file name from deeper indent
        if extract == None:
            self.extractData = None
            self.extractParent = None
            self.extractGrandparent = None
        else:
            self.extractParent = self.GetItemText(self.GetItemParent(extract))
            self.extractData = self.GetItemText(extract)
            self.extractGrandparent = self.GetItemText(self.GetItemParent(self.GetItemParent(extract)))

        try:
            self.title = self.itemData.title
        except:
            self.title = None

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

        if self.config.debug:
            msg = "Item: {} | extract: {} | extract parent: {} | extract grandparent: {} | indent: {}".format(
                self.itemType, self.extractData, self.extractParent, self.extractGrandparent, self.indent)
            print(msg)

        # load data
        loadDataMenu = wx.Menu()
        loadDataMenu.Append(ID_docTree_add_MS_to_interactive, 'Import mass spectrum')
        loadDataMenu.Append(ID_docTree_add_RT_to_interactive, 'Import chromatogram')
        loadDataMenu.Append(ID_docTree_add_DT_to_interactive, 'Import mobiligram')
        loadDataMenu.Append(ID_docTree_add_2DT_to_interactive, 'Import heatmap')
        loadDataMenu.Append(ID_docTree_add_matrix_to_interactive, 'Import matrix')
        loadDataMenu.Append(ID_docTree_add_comparison_to_interactive, 'Import comparison')
        loadDataMenu.AppendSeparator()
        loadDataMenu.Append(ID_docTree_add_other_to_interactive, 'Import data with metadata...')

        # Change x-axis label (2D)
        xlabel2DMenu = wx.Menu()
        xlabel2DMenu.Append(ID_xlabel_2D_scans, 'Scans', "", wx.ITEM_RADIO)
        xlabel2DMenu.Append(ID_xlabel_2D_time_min, 'Time (min)', "", wx.ITEM_RADIO)
        xlabel2DMenu.Append(ID_xlabel_2D_retTime_min, 'Retention time (min)', "", wx.ITEM_RADIO)
        xlabel2DMenu.Append(ID_xlabel_2D_colVolt, 'Collision Voltage (V)', "", wx.ITEM_RADIO)
        xlabel2DMenu.Append(ID_xlabel_2D_actVolt, 'Activation Energy (V)', "", wx.ITEM_RADIO)
        xlabel2DMenu.Append(ID_xlabel_2D_labFrame, 'Lab Frame Energy (eV)', "", wx.ITEM_RADIO)
        xlabel2DMenu.Append(ID_xlabel_2D_actLabFrame, 'Activation Energy (eV)', "", wx.ITEM_RADIO)
        xlabel2DMenu.Append(ID_xlabel_2D_massToCharge, 'Mass-to-charge (Da)', "", wx.ITEM_RADIO)
        xlabel2DMenu.Append(ID_xlabel_2D_mz, 'm/z (Da)', "", wx.ITEM_RADIO)
        xlabel2DMenu.Append(ID_xlabel_2D_wavenumber, u'Wavenumber (cm⁻¹)', "", wx.ITEM_RADIO)
        xlabel2DMenu.Append(ID_xlabel_2D_charge, 'Charge', "", wx.ITEM_RADIO)
        xlabel2DMenu.Append(ID_xlabel_2D_ccs, u'Collision Cross Section (Å²)', "", wx.ITEM_RADIO)
        xlabel2DMenu.Append(ID_xlabel_2D_custom, 'Custom label...', "", wx.ITEM_RADIO)
        xlabel2DMenu.AppendSeparator()
        xlabel2DMenu.Append(ID_xlabel_2D_restore, 'Restore default', "")

        # Change y-axis label (2D)
        ylabel2DMenu = wx.Menu()
        ylabel2DMenu.Append(ID_ylabel_2D_bins, 'Drift time (bins)', "", wx.ITEM_RADIO)
        ylabel2DMenu.Append(ID_ylabel_2D_ms, 'Drift time (ms)', "", wx.ITEM_RADIO)
        ylabel2DMenu.Append(ID_ylabel_2D_ms_arrival, 'Arrival time (ms)', "", wx.ITEM_RADIO)
        ylabel2DMenu.Append(ID_ylabel_2D_ccs, u'Collision Cross Section (Å²)', "", wx.ITEM_RADIO)
        ylabel2DMenu.Append(ID_ylabel_2D_custom, 'Custom label...', "", wx.ITEM_RADIO)
        ylabel2DMenu.AppendSeparator()
        ylabel2DMenu.Append(ID_ylabel_2D_restore, 'Restore default', "")

        # Check xy axis labels
        if self.itemType in ['Drift time (2D)', 'Drift time (2D, processed)', 'Drift time (2D, EIC)',
                             'Drift time (2D, combined voltages, EIC)', 'Drift time (2D, processed, EIC)',
                             'Input data']:
            # Check if right click was performed on a header of a sub-tree
            if self.extractData in ['Drift time (2D, EIC)', 'Drift time (2D, combined voltages, EIC)',
                                    'Drift time (2D, processed, EIC)', 'Input data']:
                pass

            # Check what is the current label for this particular dataset
            try: idX, idY = self.on_check_xylabels_2D()
            except UnboundLocalError: return

            if idX == ID_xlabel_2D_scans: xlabel2DMenu.Check(ID_xlabel_2D_scans, True)
            elif idX == ID_xlabel_2D_time_min: xlabel2DMenu.Check(ID_xlabel_2D_time_min, True)
            elif idX == ID_xlabel_2D_retTime_min: xlabel2DMenu.Check(ID_xlabel_2D_retTime_min, True)
            elif idX == ID_xlabel_2D_colVolt: xlabel2DMenu.Check(ID_xlabel_2D_colVolt, True)
            elif idX == ID_xlabel_2D_actVolt: xlabel2DMenu.Check(ID_xlabel_2D_actVolt, True)
            elif idX == ID_xlabel_2D_labFrame: xlabel2DMenu.Check(ID_xlabel_2D_labFrame, True)
            elif idX == ID_xlabel_2D_actLabFrame: xlabel2DMenu.Check(ID_xlabel_2D_actLabFrame, True)
            elif idX == ID_xlabel_2D_massToCharge: xlabel2DMenu.Check(ID_xlabel_2D_massToCharge, True)
            elif idX == ID_xlabel_2D_mz: xlabel2DMenu.Check(ID_xlabel_2D_mz, True)
            elif idX == ID_xlabel_2D_wavenumber: xlabel2DMenu.Check(ID_xlabel_2D_wavenumber, True)
            elif idX == ID_xlabel_2D_charge: xlabel2DMenu.Check(ID_xlabel_2D_charge, True)
            elif idX == ID_xlabel_2D_ccs: xlabel2DMenu.Check(ID_xlabel_2D_ccs, True)
            else: xlabel2DMenu.Check(ID_xlabel_2D_custom, True)

            if idY == ID_ylabel_2D_bins: ylabel2DMenu.Check(ID_ylabel_2D_bins, True)
            elif idY == ID_ylabel_2D_ms: ylabel2DMenu.Check(ID_ylabel_2D_ms, True)
            elif idY == ID_ylabel_2D_ms_arrival: ylabel2DMenu.Check(ID_ylabel_2D_ms_arrival, True)
            elif idY == ID_ylabel_2D_ccs: ylabel2DMenu.Check(ID_ylabel_2D_ccs, True)
            else: ylabel2DMenu.Check(ID_ylabel_2D_custom, True)

        # Change x-axis label (1D)
        xlabel1DMenu = wx.Menu()
        xlabel1DMenu.Append(ID_xlabel_1D_bins, 'Drift time (bins)', "", wx.ITEM_RADIO)
        xlabel1DMenu.Append(ID_xlabel_1D_ms, 'Drift time (ms)', "", wx.ITEM_RADIO)
        xlabel1DMenu.Append(ID_xlabel_1D_ms_arrival, 'Arrival time (ms)', "", wx.ITEM_RADIO)
        xlabel1DMenu.Append(ID_xlabel_1D_ccs, u'Collision Cross Section (Å²)', "", wx.ITEM_RADIO)
        xlabel1DMenu.AppendSeparator()
        xlabel1DMenu.Append(ID_xlabel_1D_restore, 'Restore default', "")

        if self.itemType == 'Drift time (1D)':
            try: idX = self.on_check_xlabels_1D()
            except UnboundLocalError: return

            if idX == ID_xlabel_1D_bins: xlabel1DMenu.Check(ID_xlabel_1D_bins, True)
            elif idX == ID_xlabel_1D_ms: xlabel1DMenu.Check(ID_xlabel_1D_ms, True)
            elif idX == ID_xlabel_1D_ms_arrival: xlabel1DMenu.Check(ID_xlabel_1D_ms_arrival, True)
            elif idX == ID_xlabel_1D_ccs: xlabel1DMenu.Check(ID_xlabel_1D_ccs, True)
            else: xlabel1DMenu.Check(ID_xlabel_1D_bins, True)

        # Change x-axis label (RT)
        xlabelRTMenu = wx.Menu()
        xlabelRTMenu.Append(ID_xlabel_RT_scans, 'Scans', "", wx.ITEM_RADIO)
        xlabelRTMenu.Append(ID_xlabel_RT_time_min, 'Time (min)', "", wx.ITEM_RADIO)
        xlabelRTMenu.Append(ID_xlabel_RT_retTime_min, 'Retention time (min)', "", wx.ITEM_RADIO)
        xlabelRTMenu.AppendSeparator()
        xlabelRTMenu.Append(ID_xlabel_RT_restore, 'Restore default', "")

        if self.itemType in ['Chromatogram', 'Chromatograms (EIC)', 'Chromatograms (combined voltages, EIC)']:
            try: idX = self.on_check_xlabels_RT()
            except UnboundLocalError: return

            if idX == ID_xlabel_RT_scans: xlabelRTMenu.Check(ID_xlabel_RT_scans, True)
            elif idX == ID_xlabel_RT_time_min: xlabelRTMenu.Check(ID_xlabel_RT_time_min, True)
            elif idX == ID_xlabel_RT_retTime_min: xlabelRTMenu.Check(ID_xlabel_RT_retTime_min, True)
            else: xlabelRTMenu.Check(ID_xlabel_RT_scans, True)

        # change y-axis label (DT/MS)
        ylabelDTMSMenu = wx.Menu()
        ylabelDTMSMenu.Append(ID_ylabel_DTMS_bins, 'Drift time (bins)', "", wx.ITEM_RADIO)
        ylabelDTMSMenu.Append(ID_ylabel_DTMS_ms, 'Drift time (ms)', "", wx.ITEM_RADIO)
        ylabelDTMSMenu.Append(ID_ylabel_DTMS_ms_arrival, 'Arrival time (ms)', "", wx.ITEM_RADIO)
        ylabelDTMSMenu.AppendSeparator()
        ylabelDTMSMenu.Append(ID_ylabel_DTMS_restore, 'Restore default', "")

        if self.itemType == 'DT/MS':
            try: idX = self.on_check_xlabels_DTMS()
            except UnboundLocalError: return

            if idX == ID_ylabel_DTMS_bins: ylabelDTMSMenu.Check(ID_ylabel_DTMS_bins, True)
            elif idX == ID_ylabel_DTMS_ms: ylabelDTMSMenu.Check(ID_ylabel_DTMS_ms, True)
            elif idX == ID_ylabel_DTMS_ms_arrival: ylabelDTMSMenu.Check(ID_ylabel_DTMS_ms_arrival, True)
            else: xlabel1DMenu.Check(ID_ylabel_DTMS_bins, True)

    # Bind events
        self.Bind(wx.EVT_MENU, self.onShowPlot, id=ID_showPlotDocument)
        self.Bind(wx.EVT_MENU, self.onShowPlot, id=ID_showPlotDocument_violin)
        self.Bind(wx.EVT_MENU, self.onShowPlot, id=ID_showPlotDocument_waterfall)
        self.Bind(wx.EVT_MENU, self.onShowPlot, id=ID_showPlot1DDocument)
        self.Bind(wx.EVT_MENU, self.onShowPlot, id=ID_showPlotRTDocument)
        self.Bind(wx.EVT_MENU, self.onShowPlot, id=ID_showPlotMSDocument)
        self.Bind(wx.EVT_MENU, self.onProcess, id=ID_process2DDocument)
        self.Bind(wx.EVT_MENU, self.presenter.onDocumentColour, id=ID_getNewColour)
        self.Bind(wx.EVT_MENU, self.presenter.onChangeChargeState, id=ID_assignChargeState)
        self.Bind(wx.EVT_MENU, self.onGoToDirectory, id=ID_goToDirectory)
        self.Bind(wx.EVT_MENU, self.onSaveCSV, id=ID_saveDataCSVDocument)
        self.Bind(wx.EVT_MENU, self.onSaveCSV, id=ID_saveDataCSVDocument1D)
        self.Bind(wx.EVT_MENU, self.onSaveCSV, id=ID_saveAsDataCSVDocument)
        self.Bind(wx.EVT_MENU, self.onSaveCSV, id=ID_saveAsDataCSVDocument1D)
        self.Bind(wx.EVT_MENU, self.onRenameItem, id=ID_renameItem)
        self.Bind(wx.EVT_MENU, self.onDuplicateItem, id=ID_duplicateItem)
        self.Bind(wx.EVT_MENU, self.presenter.saveCCScalibrationToPickle, id=ID_saveDataCCSCalibrantDocument)
        self.Bind(wx.EVT_MENU, self.onAddToCCSTable, id=ID_add2CCStable2DDocument)
        self.Bind(wx.EVT_MENU, self.presenter.on_save_document, id=ID_saveDocument)
        self.Bind(wx.EVT_MENU, self.onShowSampleInfo, id=ID_showSampleInfo)
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
        self.Bind(wx.EVT_MENU, self.onShowAnnotations, id=ID_docTree_show_annotations)
        self.Bind(wx.EVT_MENU, self.onDuplicateAnnotations, id=ID_docTree_duplicate_annotations)

        self.Bind(wx.EVT_MENU, self.onDuplicateItem, id=ID_docTree_duplicate_document)
        self.Bind(wx.EVT_MENU, self.on_refresh_document, id=ID_docTree_show_refresh_document)
        self.Bind(wx.EVT_MENU, self.on_open_extract_DTMS, id=ID_docTree_open_extractDTMS)

        # Change axis labels
        for xID in [ID_xlabel_2D_scans, ID_xlabel_2D_colVolt, ID_xlabel_2D_actVolt,
                    ID_xlabel_2D_labFrame, ID_xlabel_2D_actLabFrame, ID_xlabel_2D_massToCharge,
                    ID_xlabel_2D_mz, ID_xlabel_2D_wavenumber, ID_xlabel_2D_restore,
                    ID_xlabel_2D_ccs, ID_xlabel_2D_charge, ID_xlabel_2D_custom,
                    ID_xlabel_2D_time_min, ID_xlabel_2D_retTime_min]:
            self.Bind(wx.EVT_MENU, self.on_change_xy_values_and_labels, id=xID)

        for yID in [ID_ylabel_2D_bins, ID_ylabel_2D_ms, ID_ylabel_2D_ms_arrival,
                    ID_ylabel_2D_ccs, ID_ylabel_2D_restore, ID_ylabel_2D_custom]:
            self.Bind(wx.EVT_MENU, self.on_change_xy_values_and_labels, id=yID)
        # 1D
        for yID in [ID_xlabel_1D_bins, ID_xlabel_1D_ms, ID_xlabel_1D_ms_arrival,
                    ID_xlabel_1D_ccs, ID_xlabel_1D_restore]:
            self.Bind(wx.EVT_MENU, self.on_change_xy_values_and_labels, id=yID)
        # RT
        for yID in [ID_xlabel_RT_scans, ID_xlabel_RT_time_min, ID_xlabel_RT_retTime_min,
                    ID_xlabel_RT_restore]:
            self.Bind(wx.EVT_MENU, self.on_change_xy_values_and_labels, id=yID)
        # DT/MS
        for yID in [ID_ylabel_DTMS_bins, ID_ylabel_DTMS_ms, ID_ylabel_DTMS_ms_arrival,
                    ID_ylabel_DTMS_restore]:
            self.Bind(wx.EVT_MENU, self.on_change_xy_values_and_labels, id=yID)

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
        self.Bind(wx.EVT_MENU, self.onShow_and_SavePlot, id=ID_saveOtherImageDoc)
        self.Bind(wx.EVT_MENU, self.on_process_UVPD, id=ID_docTree_plugin_UVPD)

        self.Bind(wx.EVT_MENU, self.onLoadInteractiveData, id=ID_docTree_add_MS_to_interactive)
        self.Bind(wx.EVT_MENU, self.onLoadInteractiveData, id=ID_docTree_add_RT_to_interactive)
        self.Bind(wx.EVT_MENU, self.onLoadInteractiveData, id=ID_docTree_add_DT_to_interactive)
        self.Bind(wx.EVT_MENU, self.onLoadInteractiveData, id=ID_docTree_add_2DT_to_interactive)
        self.Bind(wx.EVT_MENU, self.onLoadInteractiveData, id=ID_docTree_add_other_to_interactive)
        self.Bind(wx.EVT_MENU, self.onLoadInteractiveData, id=ID_docTree_add_matrix_to_interactive)
        self.Bind(wx.EVT_MENU, self.onLoadInteractiveData, id=ID_docTree_add_comparison_to_interactive)

        self.Bind(wx.EVT_MENU, self.onSaveDF, id=ID_saveData_csv)
        self.Bind(wx.EVT_MENU, self.onSaveDF, id=ID_saveData_pickle)
        self.Bind(wx.EVT_MENU, self.onSaveDF, id=ID_saveData_excel)
        self.Bind(wx.EVT_MENU, self.onSaveDF, id=ID_saveData_hdf)

        self.Bind(wx.EVT_MENU, self.onShowUnidec, id=ID_docTree_show_unidec)
        self.Bind(wx.EVT_MENU, self.onSaveUnidec, id=ID_docTree_save_unidec)

        self.Bind(wx.EVT_MENU, self.on_add_mzID_file_fcn, id=ID_docTree_add_mzIdentML)

        # save dataframe
        saveDFSubMenu = wx.Menu()
        saveDFSubMenu.Append(ID_saveData_csv, 'Save to .csv file')
        saveDFSubMenu.Append(ID_saveData_pickle, 'Save to .pickle file')
        saveDFSubMenu.Append(ID_saveData_hdf, 'Save to .hdf file (slow)')
        saveDFSubMenu.Append(ID_saveData_excel, 'Save to .excel file (v. slow)')

        saveImageLabel = ''.join(['Save figure (.', self.config.imageFormat, ')'])
        saveImageLabelAll = ''.join(['Save figures (.', self.config.imageFormat, ')'])
        saveCSVLabel = ''.join(['Save data (', self.config.saveExtension, ')\tAlt+V'])
        saveCSVLabel1D = ''.join(['Save data (1D, ', self.config.saveExtension, ')'])
        saveCSVLabel2D = ''.join(['Save data (2D, ', self.config.saveExtension, ')'])

        # Get label
        if self.extractData != None:
            try:
                plotLabel = self.extractData.split(':')
            except AttributeError: pass

        menu = wx.Menu()
        if self.itemData.dataType == 'Type: Interactive':
            if self.itemType == "Annotated data" and self.extractData != self.itemType:
                if self.extractData == "Annotations":
                    menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_add_annotations,
                                                 text='Show annotations panel...',
                                                 bitmap=self.icons.iconsLib['annotate16']))
                    menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_show_annotations,
                                                 text='Show annotations on plot',
                                                 bitmap=self.icons.iconsLib['highlight_16']))
                else:
                    menu.AppendItem(makeMenuItem(parent=menu, id=ID_showPlotDocument,
                                                 text='Show plot',
                                                 bitmap=self.icons.iconsLib['blank_16']))

                if ("Multi-line: " in self.extractData or "V-bar: " in self.extractData or
                    "H-bar: " in self.extractData or "Scatter: " in self.extractData or
                    "Waterfall: " in self.extractData or "Line: " in self.extractData):
                    menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_add_annotations,
                                                 text='Show annotations panel...',
                                                 bitmap=self.icons.iconsLib['annotate16']))
                menu.AppendSeparator()
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveOtherImageDoc,
                                         text=saveImageLabel,
                                         bitmap=self.icons.iconsLib['file_png_16']))
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_removeItemDocument,
                                             text='Delete item\tDelete',
                                             bitmap=self.icons.iconsLib['clear_16']))
            if (self.itemType in ['Drift time (2D)', 'Drift time (2D, processed)']
                or (self.itemType == 'Drift time (2D, EIC)' and self.extractData != self.itemType)
                ):
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_showPlotDocument,
                                             text='Show heatmap\tAlt+S',
                                             bitmap=self.icons.iconsLib['heatmap_16']))
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_showPlotDocument_violin,
                                             text='Show violin plot',
                                             bitmap=self.icons.iconsLib['panel_violin_16']))
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_showPlotDocument_waterfall,
                                             text='Show waterfall plot',
                                             bitmap=self.icons.iconsLib['panel_waterfall_16']))
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_process2D,
                                             text='Process...\tP',
                                             bitmap=self.icons.iconsLib['process_2d_16']))
                menu.AppendSeparator()
                menu.Append(ID_renameItem, 'Rename\tF2')
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_assignChargeState,
                                         text='Assign charge state...\tAlt+Z',
                                         bitmap=self.icons.iconsLib['assign_charge_16']))
                menu.AppendMenu(wx.ID_ANY, 'Set X-axis label as...', xlabel2DMenu)
                menu.AppendMenu(wx.ID_ANY, 'Set Y-axis label as...', ylabel2DMenu)
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
                if not itemType in ['Drift time (2D)', 'Drift time (2D, processed)']:
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
            elif self.itemType in ['Mass Spectra']:
                if self.extractData == "Annotations":
                    menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_add_annotations,
                                                 text='Show annotations panel...',
                                                 bitmap=self.icons.iconsLib['annotate16']))
                    menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_show_annotations,
                                                 text='Show annotations on mass spectrum',
                                                 bitmap=self.icons.iconsLib['highlight_16']))
                    menu.AppendItem(makeMenuItem(parent=menu, id=ID_removeItemDocument,
                                                 text='Delete item\tDelete',
                                                 bitmap=self.icons.iconsLib['clear_16']))
                elif ((self.itemType in ["Mass Spectra"]) and self.extractData == "UniDec"):
                    menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_show_unidec,
                                             text='Show UniDec results',
                                             bitmap=None))
                    menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_save_unidec,
                                             text='Save UniDec results ({})'.format(self.config.saveExtension),
                                             bitmap=None))
                    menu.AppendItem(makeMenuItem(parent=menu, id=ID_removeItemDocument,
                                                 text='Delete item\tDelete',
                                                 bitmap=self.icons.iconsLib['clear_16']))
                elif ((self.itemType in ["Mass Spectra"]) and self.extractParent == "UniDec"):
                    menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_show_unidec,
                                             text='Show plot - {}'.format(self.extractData),
                                             bitmap=None))
                    menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_save_unidec,
                                             text='Save results - {} ({})'.format(self.extractData, self.config.saveExtension),
                                             bitmap=None))
                    menu.AppendItem(makeMenuItem(parent=menu, id=ID_removeItemDocument,
                                                 text='Delete item\tDelete',
                                                 bitmap=self.icons.iconsLib['clear_16']))
                elif self.itemType in ['Mass Spectrum' 'Mass Spectrum (processed)']:
                    menu.AppendItem(makeMenuItem(parent=menu, id=ID_showPlotDocument,
                                                 text='Show mass spectrum\tAlt+S',
                                                 bitmap=self.icons.iconsLib['mass_spectrum_16']))
                    menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_add_annotations,
                                                 text='Show annotations panel...',
                                                 bitmap=self.icons.iconsLib['annotate16']))
                    menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_duplicate_annotations,
                                                 text='Duplicate annotations...',
                                                 bitmap=self.icons.iconsLib['blank_16']))
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
                                                     text='Show annotations panel...',
                                                     bitmap=self.icons.iconsLib['annotate16']))
                        menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_duplicate_annotations,
                                                     text='Duplicate annotations...',
                                                     bitmap=self.icons.iconsLib['blank_16']))
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
                        menu.Append(ID_renameItem, 'Rename\tF2')
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
                menu.AppendMenu(wx.ID_ANY, 'Set X-axis label as...', xlabelRTMenu)
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
                menu.AppendMenu(wx.ID_ANY, 'Change x-axis to...', xlabel1DMenu)
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
            menu.AppendMenu(wx.ID_ANY, 'Import data...', loadDataMenu)

        # all other files!
        elif (self.itemType in ['Mass Spectrum', 'Mass Spectrum (processed)', "Mass Spectra"]):
            if ((self.itemType in ['Mass Spectrum', 'Mass Spectrum (processed)', "Mass Spectra"]) and
                self.extractData == "Annotations"):
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_add_annotations,
                                             text='Show annotations panel...',
                                             bitmap=self.icons.iconsLib['annotate16']))
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_show_annotations,
                                             text='Show annotations on mass spectrum',
                                             bitmap=self.icons.iconsLib['highlight_16']))
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_removeItemDocument,
                                             text='Delete item\tDelete',
                                             bitmap=self.icons.iconsLib['clear_16']))
            elif ((self.itemType in ['Mass Spectrum', 'Mass Spectrum (processed)', "Mass Spectra"]) and
                  self.extractData == "UniDec"):
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_show_unidec,
                                         text='Show UniDec results',
                                         bitmap=None))
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_save_unidec,
                                         text='Save UniDec results ({})'.format(self.config.saveExtension),
                                         bitmap=None))
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_removeItemDocument,
                                             text='Delete item\tDelete',
                                             bitmap=self.icons.iconsLib['clear_16']))
            elif ((self.itemType in ['Mass Spectrum', 'Mass Spectrum (processed)', "Mass Spectra"]) and
                  self.extractParent == "UniDec"):
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_show_unidec,
                                         text='Show plot - {}'.format(self.extractData),
                                         bitmap=None))
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_save_unidec,
                                         text='Save results - {} ({})'.format(self.extractData, self.config.saveExtension),
                                         bitmap=None))
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_removeItemDocument,
                                             text='Delete item\tDelete',
                                             bitmap=self.icons.iconsLib['clear_16']))
            elif self.itemType in ['Mass Spectrum', 'Mass Spectrum (processed)'] and self.indent == 2:
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_showPlotDocument,
                                             text='Show mass spectrum\tAlt+S',
                                             bitmap=self.icons.iconsLib['mass_spectrum_16']))
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_add_annotations,
                                             text='Show annotations panel...',
                                             bitmap=self.icons.iconsLib['annotate16']))
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_duplicate_annotations,
                                             text='Duplicate annotations...',
                                             bitmap=self.icons.iconsLib['blank_16']))
                # check if deconvolution results are present
                try:
                    if 'unidec' in self.currentData:
                        menu.AppendSeparator()
                        menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_show_unidec,
                                                 text='Show UniDec results',
                                                 bitmap=None))
                        menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_save_unidec,
                                                 text='Save UniDec results ({})'.format(self.config.saveExtension),
                                                 bitmap=None))
                except: pass
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
            elif self.extractParent == "Annotations" and self.indent in [4, 5]:
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
                                                 text='Show annotations panel...',
                                                 bitmap=self.icons.iconsLib['annotate16']))
                    menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_duplicate_annotations,
                                                 text='Duplicate annotations...',
                                                 bitmap=self.icons.iconsLib['blank_16']))
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
                    menu.Append(ID_renameItem, 'Rename\tF2')
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

        # tandem MS
        elif itemType == "Tandem Mass Spectra" and self.indent == 2:
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_add_mzIdentML,
                                         text='Add identification information (.mzIdentML, .mzid, .mzid.gz)',
                                         bitmap=None))
#         elif itemType == "Tandem Mass Spectra" and self.indent == 3:
#             menu.AppendItem(makeMenuItem(parent=menu, id=ID_showPlotDocument,
#                                          text='Show mass spectrum\tAlt+S',
#                                          bitmap=self.icons.iconsLib['mass_spectrum_16']))
        # Sample information
        elif itemType == 'Sample information':
            menu.Append(ID_showSampleInfo, 'Show sample information')
        # Chromatogram
        elif itemType in ['Chromatogram', 'Chromatograms (EIC)']:
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_showPlotDocument,
                                         text='Show chromatogram\tAlt+S',
                                         bitmap=self.icons.iconsLib['chromatogram_16']))
            menu.AppendSeparator()
            menu.AppendMenu(wx.ID_ANY, 'Change x-axis to...', xlabelRTMenu)
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
            menu.AppendMenu(wx.ID_ANY, 'Change x-axis to...', xlabel1DMenu)
            menu.AppendSeparator()
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
        elif itemType in ['Drift time (2D)', 'Drift time (2D, processed)',
                          'Drift time (2D, EIC)', 'Drift time (2D, combined voltages, EIC)',
                          'Drift time (2D, processed, EIC)']:
            # Only if clicked on an item and not header
            if (self.itemType in ['Drift time (2D)', 'Drift time (2D, processed)']
                or (self.itemType == 'Drift time (2D, EIC)' and self.extractData != self.itemType)
                or (self.itemType == 'Drift time (2D, combined voltages, EIC)' and self.extractData != self.itemType)
                or (self.itemType == 'Drift time (2D, processed, EIC)' and self.extractData != self.itemType)
                ):
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_showPlotDocument,
                                             text='Show heatmap\tAlt+S',
                                             bitmap=self.icons.iconsLib['heatmap_16']))
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_showPlotDocument_violin,
                                             text='Show violin plot',
                                             bitmap=self.icons.iconsLib['panel_violin_16']))
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_showPlotDocument_waterfall,
                                             text='Show waterfall plot',
                                             bitmap=self.icons.iconsLib['panel_waterfall_16']))
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_process2D,
                                             text='Process...\tP',
                                             bitmap=self.icons.iconsLib['process_2d_16']))
                menu.AppendSeparator()
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_assignChargeState,
                                         text='Assign charge state...\tAlt+Z',
                                         bitmap=self.icons.iconsLib['assign_charge_16']))
                menu.AppendMenu(wx.ID_ANY, 'Set X-axis label as...', xlabel2DMenu)
                menu.AppendMenu(wx.ID_ANY, 'Set Y-axis label as...', ylabel2DMenu)

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
#                 menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveImageDocument,
#                                          text=saveImageLabelAll,
#                                          bitmap=self.icons.iconsLib['file_png_16']))
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
                menu.AppendMenu(wx.ID_ANY, 'Set X-axis label as...', xlabel2DMenu)
                menu.AppendMenu(wx.ID_ANY, 'Set Y-axis label as...', ylabel2DMenu)
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
#                 menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveImageDocument,
#                                          text=saveImageLabelAll,
#                                          bitmap=self.icons.iconsLib['file_png_16']))
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
                menu.Append(ID_renameItem, 'Rename\tF2')
            # Only if on a header
            else:
#                 menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveImageDocument,
#                                          text=saveImageLabelAll,
#                                          bitmap=self.icons.iconsLib['file_png_16']))
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_saveDataCSVDocument,
                                         text=saveCSVLabel,
                                         bitmap=self.icons.iconsLib['file_csv_16']))
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_removeItemDocument,
                                             text='Delete item\tDelete',
                                             bitmap=self.icons.iconsLib['clear_16']))
        # Drift time (1D) (batch)
        elif itemType in ['Drift time (1D, EIC, DT-IMS)', 'Drift time (1D, EIC)'] :
            # Only if clicked on an item and not header
            if (not self.extractData == 'Drift time (1D, EIC, DT-IMS)' and
                itemType != 'Drift time (1D, EIC)'):
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_showPlotMSDocument,
                                             text='Highlight ion in mass spectrum\tAlt+X',
                                             bitmap=self.icons.iconsLib['zoom_16']))
            if not self.extractData == 'Drift time (1D, EIC, DT-IMS)':
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_showPlotDocument,
                                             text='Show mobiligram (EIC)\tAlt+S',
                                             bitmap=self.icons.iconsLib['mobiligram_16']))
                menu.AppendSeparator()
                menu.Append(ID_assignChargeState, 'Assign charge state...\tAlt+Z')
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
            if not self.extractData == 'Chromatograms (combined voltages, EIC)':
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_showPlotDocument,
                                             text='Show chromatogram\tAlt+S',
                                             bitmap=self.icons.iconsLib['chromatogram_16']))
                menu.AppendSeparator()
                menu.Append(ID_assignChargeState, 'Assign charge state...\tAlt+Z')
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
                    if self.splitText[0] in  ["Waterfall (Raw)", "Waterfall (Processed)"]:
                        menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_add_annotations,
                                                     text='Show annotations panel...',
                                                     bitmap=self.icons.iconsLib['annotate16']))
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
                menu.Append(ID_renameItem, 'Rename\tF2')
            # Header only
            else:
                menu.AppendSeparator()
                menu.AppendItem(makeMenuItem(parent=menu, id=ID_removeItemDocument,
                                             text='Delete item\tDelete',
                                             bitmap=self.icons.iconsLib['clear_16']))
        elif (itemType == 'DT/MS'):
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_showPlotDocument,
                                         text='Show heatmap\tAlt+S',
                                         bitmap=self.icons.iconsLib['heatmap_16']))
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_process2D,
                                         text='Process...\tP', bitmap=self.icons.iconsLib['process_2d_16']))
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_extractDTMS,
                                         text='Re-extract data', bitmap=None))
            menu.AppendSeparator()
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_open_extractDTMS,
                                         text='Open extraction panel...', bitmap=None))

            menu.AppendSeparator()
            menu.AppendMenu(wx.ID_ANY, 'Set Y-axis label as...', ylabelDTMSMenu)
            menu.AppendSeparator()
            menu.Append(ID_saveMZDTImage, saveImageLabel)
            menu.Append(ID_saveDataCSVDocument, saveCSVLabel)
        else:
            menu.Append(ID_docTree_add_MS_to_interactive, 'Add mass spectra')
            menu.Append(ID_docTree_add_other_to_interactive, 'Add other...')

        if menu.MenuItemCount > 0:
            menu.AppendSeparator()

        if self.indent == 1:
            menu.Append(ID_docTree_show_refresh_document, 'Refresh document')
            menu.AppendItem(makeMenuItem(parent=menu, id=ID_docTree_duplicate_document,
                                         text='Duplicate document\tShift+D',
                                         bitmap=self.icons.iconsLib['duplicate_16']))
            menu.Append(ID_renameItem, 'Rename document\tF2')
            menu.AppendSeparator()

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
                                     text='Delete document',
                                     bitmap=self.icons.iconsLib['bin16']))
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def on_change_xy_values_and_labels(self, evt):  # onUpdateXYaxisLabels
        """ 
        Change xy-axis labels
        """

        # Get current document info
        document_title, selectedItem, selectedText = self.on_enable_document(getSelected=True)
        indent = self.getItemIndent(selectedItem)
        selectedItemParentText = None
        if indent > 2: __, selectedItemParentText = self.getParentItem(selectedItem, 2, getSelected=True)
        else: pass
        document = self.presenter.documentsDict[document_title]

        # get event
        evtID = evt.GetId()

        # Determine which dataset is used
        if selectedText == None:
            data = document.IMS2D
        elif selectedText == 'Drift time (2D)':
            data = document.IMS2D
        elif selectedText == 'Drift time (2D, processed)':
            data = document.IMS2Dprocess
        elif selectedItemParentText == 'Drift time (2D, EIC)' and selectedText != None:
            data = document.IMS2Dions[selectedText]
        elif selectedItemParentText == 'Drift time (2D, combined voltages, EIC)' and selectedText != None:
            data = document.IMS2DCombIons[selectedText]
        elif selectedItemParentText == 'Drift time (2D, processed, EIC)' and selectedText != None:
            data = document.IMS2DionsProcess[selectedText]
        elif selectedItemParentText == 'Input data' and selectedText != None:
            data = document.IMS2DcompData[selectedText]

        # 1D data
        elif selectedText == 'Drift time (1D)':
            data = document.DT
        elif selectedItemParentText == 'Drift time (1D, EIC)' and selectedText != None:
            data = document.multipleDT[selectedText]

        # chromatograms
        elif selectedText == 'Chromatogram':
            data = document.RT
        elif selectedItemParentText == 'Chromatograms (EIC)' and selectedText != None:
            data = document.multipleRT[selectedText]
        elif selectedItemParentText == 'Chromatograms (combined voltages, EIC)' and selectedText != None:
            data = document.IMSRTCombIons[selectedText]

        # DTMS
        elif selectedText == 'DT/MS':
            data = document.DTMZ

        # try to get dataset object
        try: docItem = self.getItemByData(data)
        except: docItem = False

        # Add default values
        if 'defaultX' not in data:
            data['defaultX'] = {'xlabels': data['xlabels'],
                                 'xvals': data['xvals']}
        if 'defaultY' not in data:
            data['defaultY'] = {'ylabels': data.get('ylabels', 'Intensity'),
                                 'yvals': data['yvals']}

        # If either label is none, then ignore it
        newXlabel, newYlabel = None, None
        restoreX, restoreY = False, False

        # Determine what the new label should be
        if evtID in [ID_xlabel_2D_scans, ID_xlabel_2D_colVolt,
                     ID_xlabel_2D_actVolt, ID_xlabel_2D_labFrame,
                     ID_xlabel_2D_massToCharge, ID_xlabel_2D_actLabFrame,
                     ID_xlabel_2D_massToCharge, ID_xlabel_2D_mz,
                     ID_xlabel_2D_wavenumber, ID_xlabel_2D_wavenumber,
                     ID_xlabel_2D_custom, ID_xlabel_2D_charge, ID_xlabel_2D_ccs,
                     ID_xlabel_2D_retTime_min, ID_xlabel_2D_time_min,
                     ID_xlabel_2D_restore]:

            # If changing X-labels
            newXlabel = 'Scans'
            restoreX = False
            if evtID == ID_xlabel_2D_scans: newXlabel = 'Scans'
            elif evtID == ID_xlabel_2D_time_min: newXlabel = 'Time (min)'
            elif evtID == ID_xlabel_2D_retTime_min: newXlabel = 'Retention time (min)'
            elif evtID == ID_xlabel_2D_colVolt: newXlabel = 'Collision Voltage (V)'
            elif evtID == ID_xlabel_2D_actVolt: newXlabel = 'Activation Voltage (V)'
            elif evtID == ID_xlabel_2D_labFrame: newXlabel = 'Lab Frame Energy (eV)'
            elif evtID == ID_xlabel_2D_actLabFrame: newXlabel = 'Activation Energy (eV)'
            elif evtID == ID_xlabel_2D_massToCharge: newXlabel = 'Mass-to-charge (Da)'
            elif evtID == ID_xlabel_2D_mz: newXlabel = 'm/z (Da)'
            elif evtID == ID_xlabel_2D_wavenumber: newXlabel = u'Wavenumber (cm⁻¹)'
            elif evtID == ID_xlabel_2D_charge: newXlabel = 'Charge'
            elif evtID == ID_xlabel_2D_ccs: newXlabel = u'Collision Cross Section (Å²)'
            elif evtID == ID_xlabel_2D_custom:
                newXlabel = dialogs.dlgAsk('Please type in your new label...')
            elif evtID == ID_xlabel_2D_restore:
                newXlabel = data['defaultX']['xlabels']
                restoreX = True
            elif newXlabel == "" or newXlabel == None:
                newXlabel = 'Scans'

        if evtID in [ID_ylabel_2D_bins, ID_ylabel_2D_ms, ID_ylabel_2D_ms_arrival,
                     ID_ylabel_2D_ccs, ID_ylabel_2D_restore, ID_ylabel_2D_custom]:
            # If changing Y-labels
            newYlabel = 'Drift time (bins)'
            restoreY = False
            if evtID == ID_ylabel_2D_bins: newYlabel = 'Drift time (bins)'
            elif evtID == ID_ylabel_2D_ms: newYlabel = 'Drift time (ms)'
            elif evtID == ID_ylabel_2D_ms_arrival: newYlabel = 'Arrival time (ms)'
            elif evtID == ID_ylabel_2D_ccs: newYlabel = u'Collision Cross Section (Å²)'
            elif evtID == ID_ylabel_2D_custom:
                newYlabel = dialogs.dlgAsk('Please type in your new label...')
            elif evtID == ID_ylabel_2D_restore:
                newYlabel = data['defaultY']['ylabels']
                restoreY = True
            elif newYlabel == "" or newYlabel == None: newYlabel = 'Drift time (bins)'

        # 1D data
        if evtID in [ID_xlabel_1D_bins, ID_xlabel_1D_ms, ID_xlabel_1D_ms_arrival,
                     ID_xlabel_1D_ccs, ID_xlabel_1D_restore]:
            newXlabel = 'Drift time (bins)'
            restoreX = False
            if evtID == ID_xlabel_1D_bins: newXlabel = 'Drift time (bins)'
            elif evtID == ID_xlabel_1D_ms: newXlabel = 'Drift time (ms)'
            elif evtID == ID_xlabel_1D_ms_arrival: newXlabel = 'Arrival time (ms)'
            elif evtID == ID_xlabel_1D_ccs: newXlabel = u'Collision Cross Section (Å²)'
            elif evtID == ID_xlabel_1D_restore:
                newXlabel = data['defaultX']['xlabels']
                restoreX = True

        # 1D data
        if evtID in [ID_xlabel_RT_scans, ID_xlabel_RT_time_min, ID_xlabel_RT_retTime_min,
                     ID_xlabel_RT_restore]:
            newXlabel = 'Drift time (bins)'
            restoreX = False
            if evtID == ID_xlabel_RT_scans: newXlabel = 'Scans'
            elif evtID == ID_xlabel_RT_time_min: newXlabel = 'Time (min)'
            elif evtID == ID_xlabel_RT_retTime_min: newXlabel = 'Retention time (min)'
            elif evtID == ID_xlabel_RT_restore:
                newXlabel = data['defaultX']['xlabels']
                restoreX = True

        # DT/MS
        if evtID in [ID_ylabel_DTMS_bins, ID_ylabel_DTMS_ms, ID_ylabel_DTMS_ms_arrival,
                     ID_ylabel_DTMS_restore]:
            newYlabel = 'Drift time (bins)'
            restoreX = False
            if evtID == ID_ylabel_DTMS_bins: newYlabel = 'Drift time (bins)'
            elif evtID == ID_ylabel_DTMS_ms: newYlabel = 'Drift time (ms)'
            elif evtID == ID_ylabel_DTMS_ms_arrival: newYlabel = 'Arrival time (ms)'
            elif evtID == ID_ylabel_DTMS_restore:
                newYlabel = data['defaultY']['ylabels']
                restoreY = True
            elif newYlabel == "" or newYlabel == None: newYlabel = 'Drift time (bins)'

        if restoreX:
            newXvals = data['defaultX']['xvals']
            data['xvals'] = newXvals
            data['xlabels'] = newXlabel

        if restoreY:
            newYvals = data['defaultY']['yvals']
            data['yvals'] = newYvals
            data['ylabels'] = newYlabel

        # Change labels
        if newXlabel != None:
            oldXLabel = data['xlabels']
            data['xlabels'] = newXlabel  # Set new x-label
            newXvals = self.on_change_xy_axis(data['xvals'],
                                             oldXLabel, newXlabel,
                                             charge=data.get('charge', 1),
                                             pusherFreq=document.parameters.get('pusherFreq', 1000),
                                             scanTime=document.parameters.get('scanTime', 1.0),
                                             defaults=data['defaultX'])
            data['xvals'] = newXvals  # Set new x-values

        if newYlabel != None:
            oldYLabel = data['ylabels']
            data['ylabels'] = newYlabel
            newYvals = self.on_change_xy_axis(data['yvals'],
                                             oldYLabel, newYlabel,
                                             pusherFreq=document.parameters.get('pusherFreq', 1000),
                                             scanTime=document.parameters.get('scanTime', 1.0),
                                             defaults=data['defaultY'])
            data['yvals'] = newYvals

        expand_item = 'document'
        expand_item_title = None
        replotID = evtID
        # Replace data in the dictionary
        if selectedText == None:
            document.IMS2D = data
            replotID = ID_showPlotDocument
        elif selectedText == 'Drift time (2D)':
            document.IMS2D = data
            replotID = ID_showPlotDocument
        elif selectedText == 'Drift time (2D, processed)':
            document.IMS2Dprocess = data
            replotID = ID_showPlotDocument
        elif selectedItemParentText == 'Drift time (2D, EIC)' and selectedText != None:
            document.IMS2Dions[selectedText] = data
            expand_item, expand_item_title = "ions", selectedText
            replotID = ID_showPlotDocument
        elif selectedItemParentText == 'Drift time (2D, combined voltages, EIC)' and selectedText != None:
            document.IMS2DCombIons[selectedText] = data
            expand_item, expand_item_title = "combined_ions", selectedText
            replotID = ID_showPlotDocument
        elif selectedItemParentText == 'Drift time (2D, processed, EIC)' and selectedText != None:
            document.IMS2DionsProcess[selectedText] = data
            expand_item, expand_item_title = "processed_ions", selectedText
            replotID = ID_showPlotDocument
        elif selectedItemParentText == 'Input data' and selectedText != None:
            document.IMS2DcompData[selectedText] = data
            expand_item_title = selectedText
            replotID = ID_showPlotDocument

        # 1D data
        elif selectedText == 'Drift time (1D)':
            document.DT = data
        elif selectedItemParentText == 'Drift time (1D, EIC)' and selectedText != None:
            document.multipleDT[selectedText] = data
            expand_item, expand_item_title = "ions_1D", selectedText

        # Chromatograms
        elif selectedText == 'Chromatogram':
            document.RT = data
            replotID = ID_showPlotDocument
        elif selectedItemParentText == 'Chromatograms (EIC)' and selectedText != None:
            data = document.multipleRT[selectedText] = data
        elif selectedItemParentText == 'Chromatograms (combined voltages, EIC)' and selectedText != None:
            data = document.IMSRTCombIons[selectedText] = data

        # DT/MS
        elif selectedText == 'DT/MS':
            document.DTMZ = data
        else:
            document.IMS2D

        # update document
        if docItem is not False:
            try:
                self.SetPyData(docItem, data)
                self.presenter.documentsDict[document.title] = document
            except:
                self.presenter.OnUpdateDocument(document, expand_item,
                                                expand_item_title=expand_item_title)
        else:
            self.presenter.OnUpdateDocument(document, expand_item,
                                            expand_item_title=expand_item_title)

        # Try to plot that data
        try:
            self.onShowPlot(evt=replotID)
        except:
            pass

# ---
    def on_change_xy_axis(self, data, oldLabel, newLabel, charge=1,
                          pusherFreq=1000, scanTime=1.0, defaults=None):
        """
        This function changes the X and Y axis labels
        Parameters
        ----------
        data : array/list, 1D array of old X/Y-axis labels
        oldLabel : string, old X/Y-axis labels
        newLabel : string, new X/Y-axis labels
        charge : integer, charge of the ion
        pusherFreq : float, pusher frequency
        mode : string, 1D/2D modes available
        Returns
        -------
        newVals : array/list, 1D array of new X/Y-axis labels
        """

        # Make sure we have charge and pusher values
        if charge == "None" or charge == "": charge = 1
        else: charge = str2int(charge)

        if pusherFreq == "None" or pusherFreq == "": pusherFreq = 1000
        else: pusherFreq = str2num(pusherFreq)

        msg = 'Currently just changing label. Proper conversion will be coming soon'
        # Check whether labels were changed
        if oldLabel != newLabel:
            # Convert Y-axis labels
            if (oldLabel == 'Drift time (bins)' and
                newLabel in ['Drift time (ms)', 'Arrival time (ms)']):
                newVals = (data * pusherFreq) / 1000
                return newVals
            elif (oldLabel in ['Drift time (ms)', 'Arrival time (ms)'] and
                  newLabel == 'Drift time (bins)'):
                newVals = (data / pusherFreq) * 1000
                return newVals
            elif (oldLabel in ['Drift time (ms)', 'Arrival time (ms)'] and
                  newLabel == u'Collision Cross Section (Å²)'):
                self.presenter.onThreading(None, (msg, 4, 7), action='updateStatusbar')
                newVals = data
            elif (oldLabel == u'Collision Cross Section (Å²)' and
                  newLabel in ['Drift time (ms)', 'Arrival time (ms)']):
                self.presenter.onThreading(None, (msg, 4, 7), action='updateStatusbar')
                newVals = data
            elif (oldLabel == 'Drift time (bins)' and
                  newLabel == u'Collision Cross Section (Å²)'):
                self.presenter.onThreading(None, (msg, 4, 7), action='updateStatusbar')
                newVals = data
            elif (oldLabel == u'Collision Cross Section (Å²)' and
                  newLabel == 'Drift time (bins)'):
                self.presenter.onThreading(None, (msg, 4, 7), action='updateStatusbar')
                newVals = data
            elif (oldLabel == 'Drift time (ms)' and newLabel == 'Arrival time (ms)' or
                  oldLabel == 'Arrival time (ms)' and newLabel == 'Drift time (ms)'):
                newVals = data
            else:
                newVals = data

            # Convert X-axis labels
            # Convert CV --> LFE
            if (oldLabel in ['Collision Voltage (V)', 'Activation Energy (V)'] and
                newLabel in ['Lab Frame Energy (eV)', 'Activation Energy (eV)']):
                if isinstance(data, list):
                    newVals = [value * charge for value in data]
                else:
                    newVals = data * charge
            # If labels involve no conversion
            elif ((oldLabel == 'Activation Energy (V)' and newLabel == 'Collision Voltage (V)') or
                (oldLabel == 'Collision Voltage (V)' and newLabel == 'Activation Energy (V)') or
                (oldLabel == 'Lab Frame Energy (eV)' and newLabel == 'Activation Energy (eV)') or
                (oldLabel == 'Activation Energy (eV)' and newLabel == 'Lab Frame Energy (eV)')):
                if isinstance(data, list):
                    newVals = [value for value in data]
                else:
                    newVals = data
            # Convert Lab frame energy --> collision voltage
            elif (newLabel in ['Collision Voltage (V)', 'Activation Energy (V)'] and
                  oldLabel in ['Lab Frame Energy (eV)', 'Activation Energy (eV)']):
                if isinstance(data, list):
                    newVals = [value / charge for value in data]
                else:
                    newVals = data / charge
            # Convert LFE/CV --> scans
            elif (newLabel == 'Scans' and
                  oldLabel in ['Lab Frame Energy (eV)', 'Collision Voltage (V)',
                               'Activation Energy (eV)', 'Activation Energy (V)']):
                newVals = 1 + np.arange(len(data))
            # Convert Scans --> LFE/CV
            elif (oldLabel == 'Scans' and
                  newLabel in ['Lab Frame Energy (eV)', 'Collision Voltage (V)',
                               'Activation Energy (eV)', 'Activation Energy (V)']):
                # Check if defaults were provided
                if defaults is None: newVals = data
                else:
                    if (defaults['xlabels'] == 'Lab Frame Energy (eV)' or
                        defaults['xlabels'] == 'Collision Voltage (V)'):
                        newVals = defaults['xvals']
                    else: newVals = data
            # Convert Scans -> Time
            elif (newLabel in ['Retention time (min)', 'Time (min)'] and
                  oldLabel == 'Scans'):
                newVals = (data * scanTime) / 60
                return newVals
            elif (oldLabel in ['Retention time (min)', 'Time (min)'] and
                  newLabel == 'Scans'):
                newVals = (data / scanTime) * 60
                return newVals
            elif (oldLabel in ['Retention time (min)', 'Time (min)'] and
                  newLabel == ['Retention time (min)', 'Time (min)']):
                return data

            else: newVals = data

            # Return new values
            return newVals
        # labels were not changed
        else:
            return data

    def onAddToTable(self, evt):
        evtID = evt.GetId()

        filelist = self.presenter.view.panelMML.filelist
        textlist = self.presenter.view.panelMultipleText.filelist
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
                color = convertRGB1to255(color)
                filelist.SetItemBackgroundColour(count, color)
                filelist.SetItemTextColour(count, determineFontColor(color, return_rgb=True))

        elif evtID == ID_docTree_addOneToMMLTable:
            data = self.itemData.multipleMassSpectrum
            count = filelist.GetItemCount()
            colors = self.presenter.view.panelPlots.onChangePalette(None, n_colors=count + 1, return_colors=True)
            key = self.extractData
            document_title = self.itemData.title
            label = data.get('label', key)
            color = data[key].get('color', colors[-1])
            if np.sum(color) > 4: color = convertRGB255to1(color)
            filelist.Append([key, data[key].get('trap', 0), document_title, label])
            color = convertRGB1to255(color)
            filelist.SetItemBackgroundColour(count, color)
            filelist.SetItemTextColour(count, determineFontColor(color, return_rgb=True))

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
                color = convertRGB1to255(color)
                textlist.SetItemBackgroundColour(count, color)
                textlist.SetItemTextColour(count, determineFontColor(color, return_rgb=True))

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
                textlist.Append([minCE, maxCE, data[key].get('charge', ""), color, data[key]['cmap'],
                                 data[key]['alpha'], data[key]['mask'], label, data[key]['zvals'].shape,
                                 document_label])
            color = convertRGB1to255(color)
            textlist.SetItemBackgroundColour(count, color)
            textlist.SetItemTextColour(count, determineFontColor(color, return_rgb=True))

        if evtID in [ID_docTree_addToMMLTable, ID_docTree_addOneToMMLTable]:
            # sort items
            self.presenter.view.panelMML.OnSortByColumn(column=1, overrideReverse=True)
            self.presenter.view.panelMML.onRemoveDuplicates(None)
            self.presenter.view.onPaneOnOff(evt=ID_window_multipleMLList, check=True)

        elif evtID in [ID_docTree_addToTextTable, ID_docTree_addOneToTextTable, ID_docTree_addInteractiveToTextTable]:
            # sort items
            self.presenter.view.panelMultipleText.onRemoveDuplicates(None)
            self.presenter.view.onPaneOnOff(evt=ID_window_textList, check=True)

    def onShowMassSpectra(self, evt):

        data = self.itemData.multipleMassSpectrum
        spectra_count = len(data.keys())
        if spectra_count > 50:
            dlg = dialogs.dlgBox(exceptionTitle='Would you like to continue?',
                                 exceptionMsg="There are {} mass spectra in this document. Would you like to continue?".format(spectra_count),
                                 type="Question")
            if dlg == wx.ID_NO:
                msg = 'Cancelled was operation'
                self.presenter.view.SetStatusText(msg, 3)
                return

        # Check for energy
        energy_name = []
        for key in data:
            energy_name.append([key, data[key].get('trap', 0)])
        # sort
        energy_name.sort(key=itemgetter(1))

        names, xvals_list, yvals_list = [], [], []
        for row in energy_name:
            key = row[0]
            xvals_list.append(data[key]['xvals'])
            yvals_list.append(data[key]['yvals'])
            names.append(key)

        kwargs = {'show_y_labels':True, 'labels':names}
        self.presenter.view.panelPlots.on_plot_waterfall(xvals_list, yvals_list, None, colors=[],
                                                         xlabel="m/z", ylabel="", set_page=True,
                                                         **kwargs)

    def onCompareMS(self, evt):
        """ Open panel where user can select mas spectra to compare """

        if self.currentItem == None:
            return

        if self.itemData is None:
            self.presenter.onThreading(None, ("Please click on any document in the document tree.", 4, 5),
                                       action='updateStatusbar')
            return

        document_list, document_spectrum_list = [], {}
        count = 0
        for document_title in self.presenter.documentsDict:
            document_spectrum_list[document_title] = []
            if self.presenter.documentsDict[document_title].gotMultipleMS:
                for key in self.presenter.documentsDict[document_title].multipleMassSpectrum:
                    document_spectrum_list[document_title].append(key)
                    count += 1
            if self.presenter.documentsDict[document_title].gotMS:
                document_spectrum_list[document_title].append("Mass Spectrum")
                count += 1
            if self.presenter.documentsDict[document_title].smoothMS:
                document_spectrum_list[document_title].append("Mass Spectrum (processed)")
                count += 1

            # clean anything that is empty from the list
            if len(document_spectrum_list[document_title]) > 0:
                document_list.append(document_title)
            else:
                del document_spectrum_list[document_title]

        if count < 2:
            msg = "There must be at least two mass spectra to compare!"
            self.presenter.onThreading(None, (msg, 4, 5), action='updateStatusbar')
            return

        kwargs = {'current_document':self.itemData.title,
                  'document_list':document_list,
                  'document_spectrum_list':document_spectrum_list}

        self.compareMSDlg = panelCompareMS(self.parent,
                                           self.presenter,
                                           self.config,
                                           self.icons,
                                           **kwargs)
        self.compareMSDlg.Show()

    def onProcess2D(self, evt):
        if self.itemType in ['Drift time (2D)', 'Drift time (2D, processed)']:
            dataset = self.itemType
            ionName = ""
        elif self.itemType in ['Drift time (2D, EIC)', 'Drift time (2D, combined voltages, EIC)',
                               'Drift time (2D, processed, EIC)', 'Input data',
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
        try:
            evtID = evt.GetId()
        except:
            evtID = ID_processSettings_MS

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
        msg = "Comparing {} ({}) vs {} ({})".format(self.compareMSDlg.output["spectrum_1"][1],
                                                    self.compareMSDlg.output["spectrum_1"][0],
                                                    self.compareMSDlg.output["spectrum_2"][1],
                                                    self.compareMSDlg.output["spectrum_2"][0])
        self.presenter.onThreading(None, (msg, 4, 5), action='updateStatusbar')
        # get data
        try:
            document_1 = self.compareMSDlg.output["spectrum_1"][0]
            dataset_1 = self.compareMSDlg.output["spectrum_1"][1]
            if dataset_1 == "Mass Spectrum": spectrum_1 = self.presenter.documentsDict[document_1].massSpectrum
            elif dataset_1 == "Mass Spectrum (processed)": spectrum_1 = self.presenter.documentsDict[document_1].smoothMS
            else: spectrum_1 = self.presenter.documentsDict[document_1].multipleMassSpectrum[dataset_1]
        except:
            dialogs.dlgBox(exceptionTitle="Incorrect data",
                           exceptionMsg="Could not find requested dataset. Try resellecting the document in the Documents Panel or opening this dialog again.",
                           type="Error")
            return
        try:
            document_2 = self.compareMSDlg.output["spectrum_2"][0]
            dataset_2 = self.compareMSDlg.output["spectrum_2"][1]
            if dataset_2 == "Mass Spectrum": spectrum_2 = self.presenter.documentsDict[document_2].massSpectrum
            elif dataset_2 == "Mass Spectrum (processed)": spectrum_2 = self.presenter.documentsDict[document_2].smoothMS
            else: spectrum_2 = self.presenter.documentsDict[document_2].multipleMassSpectrum[dataset_2]
        except:
            dialogs.dlgBox(exceptionTitle="Incorrect data",
                           exceptionMsg="Could not find requested dataset. Try resellecting the document in the Documents Panel or opening this dialog again.",
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
                           exceptionMsg="Could not find requested dataset. Try resellecting the document in the Documents Panel or opening this dialog again.",
                           type="Error")
            return

        # Pre-process
        if self.config.compare_massSpectrumParams['preprocess']:
            msX_1, msY_1 = self.data_processing.on_process_MS(msX=msX_1, msY=msY_1, return_data=True)
            msX_2, msY_2 = self.data_processing.on_process_MS(msX=msX_2, msY=msY_2, return_data=True)

        if len(msX_1) == len(msX_2):
            msX = msX_1

        # Normalize 1D data
        if self.config.compare_massSpectrumParams['normalize']:
            msY_1 = normalize_1D(inputData=msY_1)
            msY_2 = normalize_1D(inputData=msY_2)

        if self.config.compare_massSpectrumParams['subtract']:
            if len(msX) != len(msY_1) or  len(msX) != len(msY_2) or len(msY_1) != len(msY_2):
                try: self.compareMSDlg.error_handler(flag="subtract")
                except: pass
                msg = "Mass spectra are not of the same size. X-axis: %s Y-axis (1): %s | Y-axis (2): %s" % (
                    len(msX), len(msY_1), len(msY_2))
                self.presenter.onThreading(None, (msg, 4, 5)  , action='updateStatusbar')
                dialogs.dlgBox(exceptionTitle="Incorrect size",
                               exceptionMsg=msg,
                               type="Error")
                return
            # If normalizing, there should be no issues in signal intensity
            if self.config.compare_massSpectrumParams['normalize']:
                self.config.compare_massSpectrumParams['subtract'] = False
                msY_1, msY_2 = subtract_1D(msY_1, msY_2)
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

    def onDuplicateItem(self, evt):
        evtID = evt.GetId()
        if evtID == ID_duplicateItem:
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
        elif evtID == ID_docTree_duplicate_document:
            title = self.itemData.title
            document = deepcopy(self.presenter.documentsDict[title])
            document.title = "{} - copy".format(title)

            self.presenter.OnUpdateDocument(document, 'document')

    def onRenameItem(self, evt):

        if self.itemData == None:
            return

        current_name = None
        prepend_name = False
        if self.indent == 1 and self.extractData is None:
            prepend_name = False
        elif self.itemType == 'Statistical' and self.extractData != 'Statistical':
            prepend_name = True
        elif self.itemType == 'Overlay' and self.extractData != 'Overlay':
            prepend_name = True
        elif self.itemType == "Mass Spectra" and self.extractData != 'Mass Spectra':
            current_name = self.extractData
        elif self.itemData.dataType == 'Type: Interactive':
            if self.itemType not in ["Drift time (2D, EIC)"]:
                return
            current_name = self.extractData
        else:
            return

        if current_name is None:
            try:
                current_name = re.split('-|,|:|__', self.extractData.replace(' ', ''))[0]
            except AttributeError:
                current_name = self.itemData.title

        if current_name == 'Grid(nxn)': current_name = 'Grid (n x n)'
        elif current_name == 'Grid(2': current_name = 'Grid (2->1)'
        elif current_name == 'RMSDMatrix': current_name = 'RMSD Matrix'
        elif current_name == 'Waterfall(Raw)': current_name = 'Waterfall (Raw)'
        elif current_name == 'Waterfall(Processed)': current_name = 'Waterfall (Processed)'
        elif current_name == 'Waterfall(Fitted)': current_name = 'Waterfall (Fitted)'
        elif current_name == 'Waterfall(DeconvolutedMW)': current_name = 'Waterfall (Deconvoluted MW)'
        elif current_name == 'Waterfalloverlay': current_name = 'Waterfall overlay'

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
                # TODO: implement for other panels
                try: self.presenter.view.panelMML.onRenameItem(current_name,
                                                                    new_name,
                                                                    item_type="document")
                except: pass
                try: self.presenter.view.panelMultipleIons.onRenameItem(current_name,
                                                                             new_name,
                                                                             item_type="document")
                except: pass
#                 try: self.presenter.view.panelMultipleText.onClearItems(title)
#                 except: pass
#                 try: self.presenter.view.panelMML.onClearItems(title)
#                 except: pass
#                 try: self.presenter.view.panelLinearDT.topP.onClearItems(title)
#                 except: pass
#                 try: self.presenter.view.panelLinearDT.bottomP.onClearItems(title)
#                 except: pass

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
                try: self.presenter.view.panelMML.onRenameItem(current_name, new_name, item_type="filename")
                except: pass
            elif self.itemType == "Drift time (2D, EIC)":
                new_name = new_name.replace(": ", " : ")
                # Change document tree
                docItem = self.getItemByData(self.presenter.documentsDict[self.title].IMS2Dions[self.extractData])
                parent = self.GetItemParent(docItem)
                self.SetItemText(docItem, new_name)
                # check if ":" found in the new name

                # TODO: check if iterm is in the peaklist
                # Change dictionary key
                self.presenter.documentsDict[self.title].IMS2Dions[new_name] = self.presenter.documentsDict[self.title].IMS2Dions.pop(self.extractData)
                self.Expand(docItem)
            else:
                return

            # just a msg
            args = ("Renamed {} to {}".format(current_name, new_name), 4)
            self.presenter.onThreading(None, args, action='updateStatusbar')

            # Expand parent
            try: self.Expand(parent)
            except: pass

            self.SetFocus()

    def onGoToDirectory(self, evt=None):
        '''
        Go to selected directory
        '''
        self.presenter.openDirectory()

    def onSaveUnidec(self, evt, data_type="all"):
        basename = os.path.splitext(self.itemData.title)[0]

        if ((self.itemType == "Mass Spectrum" and self.extractData == "UniDec") or
            (self.itemType == "UniDec" and self.indent == 2)):
            unidec_engine_data = self.itemData.massSpectrum['unidec']
            data_type = "all"
        elif (self.itemType == "Mass Spectrum" and self.extractParent == "UniDec" and
              self.indent == 4):
            unidec_engine_data = self.itemData.massSpectrum['unidec']
            data_type = self.extractData
        elif self.itemType == "Mass Spectra" and self.extractData == "UniDec":
            unidec_engine_data = self.itemData.multipleMassSpectrum[self.extractParent]['unidec']
            data_type = "all"
        elif self.itemType == "Mass Spectra" and self.extractParent == "UniDec":
            unidec_engine_data = self.itemData.multipleMassSpectrum[self.extractGrandparent]['unidec']
            data_type = self.extractData

        # replace strings in the title
        basename = basename.replace(".csv", "").replace(".txt", "").replace(".raw", "").replace(".d", "")

        try:
            if data_type in ["all", "MW distribution"]:
                data_type_name = "MW distribution"
                defaultValue = "unidec_MW_{}{}".format(basename, self.config.saveExtension)

                data = unidec_engine_data[data_type_name]
                kwargs = {'default_name':defaultValue}
                data = [data['xvals'], data['yvals']]
                labels = ['MW(Da)', 'Intensity']
                self.onSaveData(data=data, labels=labels, data_format='%.4f', **kwargs)
        except:
            print("Failed to save MW distributions")

        try:
            if data_type in ["all", "m/z with isolated species"]:
                data_type_name = "m/z with isolated species"
                defaultValue = "unidec_mz_species_{}{}".format(basename, self.config.saveExtension)
                data = unidec_engine_data[data_type_name]

                i, save_data, labels = 0, [], ["m/z"]
                for key in data:
                    if key.split(" ")[0] != "MW:":
                        continue
                    xvals = data[key]['line_xvals']
                    if i == 0:
                        save_data.append(xvals)
                    yvals = data[key]['line_yvals']
                    save_data.append(yvals)
                    labels.append(key)
                    i = +1
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
                labels = ['m/z(Da)', 'Intensity(raw)', 'Intensity(fitted)']
                self.onSaveData(data=data, labels=labels, data_format='%.4f', **kwargs)
        except: pass

        try:
            if data_type in ["all", "Processed"]:
                data_type_name = "Processed"
                defaultValue = "unidec_processed_{}{}".format(basename, self.config.saveExtension)
                data = unidec_engine_data[data_type_name]

                kwargs = {'default_name':defaultValue}
                data = [data['xvals'], data['yvals']]
                labels = ['m/z(Da)', 'Intensity']
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
                for label in yvals:
                    labels.append(label)

                kwargs = {'default_name':defaultValue}
                self.onSaveData(data=save_data, labels=labels, data_format='%.4f', **kwargs)
        except: pass

        try:
            if data_type in ["all", "Barchart"]:
                data_type_name = "Barchart"
                defaultValue = "unidec_Barchart_{}{}".format(basename, self.config.saveExtension)
                data = unidec_engine_data[data_type_name]

                xvals = data['xvals']
                yvals = data['yvals']
                legend_text = data['legend_text']

                # get labels from legend
                labels = []
                for item in legend_text:
                    labels.append(item[1])

                save_data = [xvals, yvals, labels]

                kwargs = {'default_name':defaultValue}
                self.onSaveData(data=save_data, labels=["position", "intensity", "label"], data_format='%s', **kwargs)
        except: pass

        try:
            if data_type in ["all", "Charge information"]:
                data_type_name = "Charge information"
                defaultValue = "unidec_ChargeInformation_{}{}".format(basename, self.config.saveExtension)
                data = unidec_engine_data[data_type_name]

                save_data = [data[:, 0], data[:, 1]]

                kwargs = {'default_name':defaultValue}
                self.onSaveData(data=save_data, labels=["charge", "intensity"], data_format='%s', **kwargs)
        except: pass

    def onShowUnidec(self, evt, plot_type="all"):

        # MS - all
        if self.itemType == "Mass Spectrum" and self.extractData == "UniDec":
            unidec_engine_data = self.itemData.massSpectrum['unidec']
        elif self.itemType == "Mass Spectrum" and self.extractParent == "UniDec":
            unidec_engine_data = self.itemData.massSpectrum['unidec']
            plot_type = self.extractData
        # Processed MS - all
        elif self.itemType == "Mass Spectrum (processed)" and self.extractData == "UniDec":
            unidec_engine_data = self.itemData.smoothMS['unidec']
        elif self.itemType == "Mass Spectrum (processed)" and self.extractParent == "UniDec":
            unidec_engine_data = self.itemData.smoothMS['unidec']
            plot_type = self.extractData
        # Multiple MS - all
        elif self.itemType == "Mass Spectra" and self.extractData == "UniDec":
            unidec_engine_data = self.itemData.multipleMassSpectrum[self.extractParent]['unidec']
        # Multiple MS - selected
        elif self.itemType == "Mass Spectra" and self.extractParent == "UniDec":
            unidec_engine_data = self.itemData.multipleMassSpectrum[self.extractGrandparent]['unidec']
            plot_type = self.extractData

        if self.config.unidec_plot_panel_view == "Tabbed view" and plot_type != "all":
            change_page = True
        else:
            change_page = False

        kwargs = {'show_markers':self.config.unidec_show_markers,
                  'show_individual_lines':self.config.unidec_show_individualComponents,
                  'speedy':self.config.unidec_speedy,
                  'set_page':change_page}

        # change page
        self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['UniDec'])

        if plot_type == "all":
            self.presenter.view.panelPlots.on_clear_unidec()

        if plot_type in ["all", "Fitted", "Processed"]:
            try:
                self.presenter.view.panelPlots.on_plot_unidec_MS_v_Fit(replot=unidec_engine_data['Fitted'],
                                                                       **kwargs)
            except:
                print("Failed to plot MS vs Fit plot")
                try: self.presenter.view.panelPlots.on_plot_unidec_MS(replot=unidec_engine_data['Processed'],
                                                                      **kwargs)
                except: print("Failed to plot MS plot")

        if plot_type in ["all", "MW distribution"]:
            try:
                self.presenter.view.panelPlots.on_plot_unidec_mwDistribution(replot=unidec_engine_data['MW distribution'],
                                                                             **kwargs)
                try:
                    self.presenter.view.panelPlots.on_plot_unidec_MW_add_markers(unidec_engine_data['m/z with isolated species'],
                                                                                 unidec_engine_data['MW distribution'],
                                                                                 **kwargs)
                except: pass
            except: print("Failed to plot MW distribution plot")

        if plot_type in ["all", "m/z vs Charge"]:
            try:
                self.presenter.view.panelPlots.on_plot_unidec_mzGrid(replot=unidec_engine_data['m/z vs Charge'],
                                                                     **kwargs)
            except: print("Failed to plot m/z vs charge plot")

        if plot_type in ["all", "m/z with isolated species"]:
            try:
                self.presenter.view.panelPlots.on_plot_unidec_individualPeaks(replot=unidec_engine_data['m/z with isolated species'],
                                                                              **kwargs)
            except: print("Failed to plot individual MS plot")

        if plot_type in ["all", "MW vs Charge"]:
            try: self.presenter.view.panelPlots.on_plot_unidec_MW_v_Charge(replot=unidec_engine_data['MW vs Charge'],
                                                                           **kwargs)
            except: print("Failed to plot MW vs charge plot")

        if plot_type in ["all", "Barchart"]:
            try: self.presenter.view.panelPlots.on_plot_unidec_barChart(replot=unidec_engine_data['Barchart'],
                                                                        **kwargs)
            except: print("Failed to plot barplot")

        if plot_type in ["all", "Charge information"]:
            try:
                self.presenter.view.panelPlots.on_plot_unidec_ChargeDistribution(unidec_engine_data['Charge information'][:, 0],
                                                                                 unidec_engine_data['Charge information'][:, 1],
                                                                                  **kwargs)
            except: print("Failed to plot charge distribution")

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
        defaultValue, save_kwargs = None, {}
        if self.itemType in "Annotated data":
            if self.extractData == "Annotated data":
                return
            if self.extractData == "Annotations":
                self.onAddAnnotation(None)
                return
            data = deepcopy(self.GetPyData(self.currentItem))
            try: plot_type = data['plot_type']
            except KeyError: return
            if plot_type in ["scatter", "waterfall", "line", "multi-line", "grid-scatter",
                             "grid-line", "vertical-bar", "horizontal-bar"]:
                xlabel = data['xlabel']
                ylabel = data['ylabel']
                labels = data['labels']
                colors = data['colors']
                xvals = data['xvals']
                yvals = data['yvals']
                zvals = data['zvals']

                kwargs = {"plot_modifiers": data["plot_modifiers"],
                          "item_colors": data["itemColors"],
                          "item_labels": data["itemLabels"],
                          "xerrors":data['xvalsErr'], "yerrors":data['yvalsErr'],
                          "xlabels":data['xlabels'], "ylabels":data["ylabels"]}

            if plot_type == "scatter":
                self.presenter.view.panelPlots.on_plot_other_scatter(xvals, yvals, zvals, xlabel, ylabel, colors, labels,
                                                                     set_page=True, **kwargs)
            elif plot_type == "waterfall":
                kwargs = {"labels":labels}
                self.presenter.view.panelPlots.on_plot_other_waterfall(xvals, yvals, None, xlabel, ylabel, colors=colors,
                                                                       set_page=True, **kwargs)
            elif plot_type == "multi-line":
                self.presenter.view.panelPlots.on_plot_other_overlay(xvals, yvals, xlabel, ylabel, colors=colors,
                                                                     set_page=True, labels=labels)
            elif plot_type == "line":
                kwargs = {"line_color":colors[0], "shade_under_color":colors[0],
                          "plot_modifiers": data["plot_modifiers"]}
                self.presenter.view.panelPlots.on_plot_other_1D(xvals, yvals, xlabel, ylabel, **kwargs)
            elif plot_type == "grid-line":
                self.presenter.view.panelPlots.on_plot_other_grid_1D(xvals, yvals, xlabel, ylabel, colors=colors,
                                                                     labels=labels, set_page=True, **kwargs)
            elif plot_type == "grid-scatter":
                self.presenter.view.panelPlots.on_plot_other_grid_scatter(xvals, yvals, xlabel, ylabel, colors=colors,
                                                                          labels=labels, set_page=True, **kwargs)

            elif plot_type in ["vertical-bar", "horizontal-bar"]:
                kwargs.update(orientation=plot_type)
                self.presenter.view.panelPlots.on_plot_other_bars(xvals, data['yvals_min'], data['yvals_max'],
                                                                  xlabel, ylabel, colors, set_page=True, **kwargs)
            elif plot_type in ['matrix']:
                zvals, yxlabels, cmap = self.presenter.get2DdataFromDictionary(dictionary=data,
                                                                               plotType='Matrix',
                                                                               compact=False)
                self.presenter.view.panelPlots.on_plot_matrix(zvals=zvals, xylabels=yxlabels, cmap=cmap,
                                                              set_page=True)
            else:
                msg = "Plot: {} is not supported yet. Please contact Lukasz Migas \n".format(plot_type) + \
                      "if you would like to include a new plot type in ORIGAMI. Currently \n" + \
                      "supported plots include: line, multi-line, waterfall, scatter and grid."
                dialogs.dlgBox(exceptionTitle='Plot type not supported',
                               exceptionMsg=msg,
                               type="Error")

            if save_image:
                defaultValue = "Custom_{}_{}".format(basename, os.path.splitext(self.extractData)[0]).replace(":", "").replace(" ", "")
                save_kwargs = {'image_name':defaultValue}
                self.presenter.view.panelPlots.save_images(evt=ID_saveOtherImageDoc, **save_kwargs)

        elif self.itemType == "Tandem Mass Spectra":
            if self.extractData == "Tandem Mass Spectra":
                data = self.itemData.tandem_spectra
                kwargs = {'document':self.itemData.title,
                          'tandem_spectra':data}
                self.on_open_MSMS_viewer(**kwargs)
                return

            data = self.GetPyData(self.currentItem)
            title = "Precursor: {:.4f} [{}]".format(data['scan_info']['precursor_mz'],
                                                data['scan_info']['precursor_charge'])

            self.presenter.view.panelPlots.on_plot_centroid_MS(data['xvals'], data['yvals'], title=title)
        #=======================================================================
        #  MASS SPECTRUM
        #=======================================================================
        elif any(self.itemType in itemType for itemType in ['Mass Spectrum',
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

            # setup kwargs
            if self.itemType in ['Mass Spectrum']:
                name_kwargs = {"document":self.itemData.title, "dataset": "Mass Spectrum"}
            elif self.itemType in ['Mass Spectrum (processed)']:
                name_kwargs = {"document":self.itemData.title, "dataset": "Mass Spectrum (processed)"}
            elif self.itemType == 'Mass Spectra' and self.extractData != self.itemType:
                name_kwargs = {"document":self.itemData.title, "dataset":self.extractData}

            # plot
            if self.itemData.dataType != 'Type: CALIBRANT':
                self.presenter.view.panelPlots.on_plot_MS(msX, msY, xlimits=xlimits, set_page=True, **name_kwargs)
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
                self.presenter.view.panelPlots.on_plot_MS_DT_calibration(msX=msX, msY=msY, xlimits=xlimits,
                                                                         plotType='MS', set_page=True)
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
                out = re.split('-|,|', self.extractData)
                startX = str2num(out[0]) - self.config.zoomWindowX
                endX = str2num(out[1]) + self.config.zoomWindowX
                endY = 1.02
                try:
                    startX = (data['xylimits'][0] - self.config.zoomWindowX)
                    endX = (data['xylimits'][1] + self.config.zoomWindowX)
                    endY = ((self.config.zoomWindowY + data['xylimits'][2]) / 100)
                except KeyError: pass
                self.presenter.view.panelPlots.on_zoom_1D(startX=startX, endX=endX, endY=endY, set_page=True)
                return
            # extract x/y axis values
            dtX = data['xvals']
            dtY = data['yvals']
            if len(dtY) >= 1:
                try: dtY = data['yvalsSum']
                except KeyError: pass
            xlabel = data['xlabels']
            if self.itemData.dataType != 'Type: CALIBRANT':
                self.presenter.view.panelPlots.on_plot_1D(dtX, dtY, xlabel, set_page=True)
                if save_image:
                    save_kwargs = {'image_name':defaultValue}
                    self.presenter.view.panelPlots.save_images(evt=ID_save1DImageDoc, **save_kwargs)
            else:
                self.presenter.view.panelPlots.on_plot_MS_DT_calibration(dtX=dtX, dtY=dtY, xlabelDT=xlabel,
                                                                         plotType='1DT', set_page=True)
                self.presenter.view.panelPlots.on_add_marker(xvals=data['peak'][0],
                                                             yvals=data['peak'][1],
                                                             color=self.config.annotColor,
                                                             marker=self.config.markerShape,
                                                             size=self.config.markerSize,
                                                             plot='CalibrationDT')
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
            self.presenter.view.panelPlots.on_plot_RT(rtX, rtY, xlabel, set_page=True)
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
                    startX = str2num(out[0]) - self.config.zoomWindowX
                    endX = str2num(out[1]) + self.config.zoomWindowX
                except TypeError:
                    return
                endY = 1.05
                try:
                    startX = (data['xylimits'][0] - self.config.zoomWindowX)
                    endX = (data['xylimits'][1] + self.config.zoomWindowX)
                    endY = (data['xylimits'][2] / 100)
                except KeyError: pass
                self.presenter.view.panelPlots.on_zoom_1D(startX=startX, endX=endX, endY=endY, set_page=True)
                return
            elif evtID == ID_showPlot1DDocument:
                self.presenter.view.panelPlots.on_plot_1D(data['yvals'],  # normally this would be the y-axis
                                                          data['yvals1D'],
                                                          data['ylabels'],  # data was rotated so using ylabel for xlabel
                                                          set_page=True)
                return
            elif evtID == ID_showPlotRTDocument:
                self.presenter.view.panelPlots.on_plot_RT(data['xvals'], data['yvalsRT'],
                                                          data['xlabels'], set_page=True)
                return
            elif evtID == ID_showPlotDocument_violin:
                dataOut = self.presenter.get2DdataFromDictionary(dictionary=data, dataType='plot', compact=True)
                self.presenter.view.panelPlots.on_plot_violin(data=dataOut, set_page=True)
                return
            elif evtID == ID_showPlotDocument_waterfall:
                zvals, xvals, xlabel, yvals, ylabel, cmap = self.presenter.get2DdataFromDictionary(dictionary=data, dataType='plot', compact=False)
                if len(xvals) > 500:
                    dlg = dialogs.dlgBox(exceptionTitle='Would you like to continue?',
                                 exceptionMsg="There are {} scans in this dataset (this could be slow...). Would you like to continue?".format(len(xvals)),
                                 type="Question")
                    if dlg == wx.ID_NO:
                        return

                self.presenter.view.panelPlots.on_plot_waterfall(yvals=xvals, xvals=yvals, zvals=zvals,
                                                                xlabel=xlabel, ylabel=ylabel, set_page=True)
                return
            else: pass
            # Unpack data
            if len(data) == 0:
                return

            dataOut = self.presenter.get2DdataFromDictionary(dictionary=data, dataType='plot', compact=True)
            # Change panel and plot data
            self.presenter.view.panelPlots.on_plot_2D_data(data=dataOut)
            if not self.config.waterfall:
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
                                                              data['ylabels'],
                                                              set_page=True)
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
                                                            data['cmap_2'],
                                                            set_page=True)

                # Add RMSD label
                rmsdXpos, rmsdYpos = self.presenter.onCalculateRMSDposition(xlist=data['xvals'], ylist=data['yvals'])
                if rmsdXpos != None and rmsdYpos != None:
                    self.presenter.addTextRMSD(rmsdXpos, rmsdYpos, data['rmsdLabel'], 0, plot='Grid')

                if save_image:
                    save_kwargs = {'image_name':defaultValue}
                    self.presenter.view.panelPlots.save_images(evt=ID_saveOverlayImageDoc, **save_kwargs)
            elif (out[0] == 'Mask'  or out[0] == 'Transparent'):
                zvals1, zvals2, cmap1, cmap2, alpha1, alpha2, __, __, xvals, yvals, xlabels, ylabels = self.presenter.getOverlayDataFromDictionary(dictionary=data,
                                                                                                                                           dataType='plot',
                                                                                                                                           compact=False)
                if out[0] == 'Mask':
                    defaultValue = "Overlay_mask_{}".format(basename)
                    self.presenter.view.panelPlots.on_plot_overlay_2D(zvalsIon1=zvals1, cmapIon1=cmap1,
                                                                      alphaIon1=1, zvalsIon2=zvals2,
                                                                      cmapIon2=cmap2, alphaIon2=1,
                                                                      xvals=xvals, yvals=yvals,
                                                                      xlabel=xlabels, ylabel=ylabels,
                                                                      flag='Text', set_page=True)
                elif out[0] == 'Transparent':
                    defaultValue = "Overlay_transparent_{}".format(basename)
                    self.presenter.view.panelPlots.on_plot_overlay_2D(zvalsIon1=zvals1, cmapIon1=cmap1,
                                                                     alphaIon1=alpha1, zvalsIon2=zvals2,
                                                                     cmapIon2=cmap2, alphaIon2=alpha2,
                                                                     xvals=xvals, yvals=yvals,
                                                                     xlabel=xlabels, ylabel=ylabels,
                                                                     flag='Text', set_page=True)
                # Change window view
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
                                                             plotType="RMSD",
                                                             set_page=True)
                # Add RMSD label
                rmsdXpos, rmsdYpos = self.presenter.onCalculateRMSDposition(xlist=xvals, ylist=yvals)
                if rmsdXpos != None and rmsdYpos != None:
                    self.presenter.addTextRMSD(rmsdXpos, rmsdYpos, rmsdLabel, 0, plot='RMSF')

                if save_image:
                    save_kwargs = {'image_name':defaultValue}
                    self.presenter.view.panelPlots.save_images(evt=ID_saveRMSFImageDoc, **save_kwargs)

            elif out[0] == 'RGB':
                defaultValue = "Overlay_RGB_{}".format(basename)
                data = self.GetPyData(self.currentItem)
                rgb_plot, xAxisLabels, xlabel, yAxisLabels, ylabel, __ = \
                self.presenter.get2DdataFromDictionary(dictionary=data, plotType='2D', compact=False)
                legend_text = data['legend_text']
                self.presenter.view.panelPlots.on_plot_rgb(rgb_plot, xAxisLabels, yAxisLabels, xlabel,
                                                          ylabel, legend_text, set_page=True)
                if save_image:
                    save_kwargs = {'image_name':defaultValue}
                    self.presenter.view.panelPlots.save_images(evt=ID_save2DImageDoc, **save_kwargs)

            elif out[0] == 'RMSD':
                defaultValue = "Overlay_RMSD_{}".format(basename)
                zvals, xaxisLabels, xlabel, yaxisLabels, ylabel, rmsdLabel, cmap = self.presenter.get2DdataFromDictionary(dictionary=data,
                                                                                                                          plotType='RMSD',
                                                                                                                          compact=True)
                self.presenter.view.panelPlots.on_plot_RMSD(zvals, xaxisLabels, yaxisLabels, xlabel, ylabel,
                                                             cmap, plotType="RMSD", set_page=True)
                self.presenter.view.panelPlots.on_plot_3D(zvals=zvals, labelsX=xaxisLabels, labelsY=yaxisLabels,
                                                          xlabel=xlabel, ylabel=ylabel, zlabel='Intensity',
                                                          cmap=cmap)
                # Add RMSD label
                rmsdXpos, rmsdYpos = self.presenter.onCalculateRMSDposition(xlist=xaxisLabels,
                                                                            ylist=yaxisLabels)
                if rmsdXpos != None and rmsdYpos != None:
                    self.presenter.addTextRMSD(rmsdXpos, rmsdYpos, rmsdLabel, 0, plot='RMSD')

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
                                                                 set_page=True,
                                                                 **data['waterfall_kwargs'])
                if save_image:
                    save_kwargs = {'image_name':defaultValue}
                    self.presenter.view.panelPlots.save_images(evt=ID_saveWaterfallImageDoc, **save_kwargs)

            elif out[0] == "Waterfall overlay":
                self.presenter.view.panelPlots.on_plot_waterfall_overlay(data['xvals'], data['yvals'],
                                                                         data['zvals'], data['colors'],
                                                                         data['xlabel'], data['ylabel'],
                                                                         data['labels'], set_page=True)
                if save_image:
                    defaultValue = "Waterfall_overlay_{}".format(basename)
                    save_kwargs = {'image_name':defaultValue}
                    self.presenter.view.panelPlots.save_images(evt=ID_saveWaterfallImageDoc, **save_kwargs)

            # Overlayed 1D data
            elif out[0] == u'1D' or out[0] == u'RT':
                xvals, yvals, xlabels, colors, labels, xlimits = self.presenter.get2DdataFromDictionary(dictionary=data,
                                                                                                        plotType='Overlay1D',
                                                                                                        compact=True)
                if out[0] == '1D':
                    defaultValue = "Overlay_DT_1D_{}".format(basename)
                    self.presenter.view.panelPlots.on_plot_overlay_DT(xvals=xvals, yvals=yvals, xlabel=xlabels, colors=colors,
                                                                      xlimits=xlimits, labels=labels, set_page=True)
                    if save_image:
                        save_kwargs = {'image_name':defaultValue}
                        self.presenter.view.panelPlots.save_images(evt=ID_save1DImageDoc, **save_kwargs)
                elif out[0] == 'RT':
                    defaultValue = "Overlay_RT_{}".format(basename)
                    self.presenter.view.panelPlots.on_plot_overlay_RT(xvals=xvals, yvals=yvals, xlabel=xlabels, colors=colors,
                                                                      xlimits=xlimits, labels=labels, set_page=True)
                    if save_image:
                        save_kwargs = {'image_name':defaultValue}
                        self.presenter.view.panelPlots.save_images(evt=ID_saveRTImageDoc, **save_kwargs)

        elif self.itemType == 'Statistical':
            if self.extractData == 'Statistical': return

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
                self.presenter.view.panelPlots.on_plot_2D_data(data=dataOut)
                self.presenter.view.panelPlots.mainBook.SetSelection(self.config.panelNames['2D'])
                if save_image:
                    save_kwargs = {'image_name':defaultValue}
                    self.presenter.view.panelPlots.save_images(evt=ID_save2DImageDoc, **save_kwargs)

            elif out[0] == 'RMSD Matrix':
                defaultValue = "Overlay_matrix_{}".format(basename)
                zvals, yxlabels, cmap = self.presenter.get2DdataFromDictionary(dictionary=data,
                                                                               plotType='Matrix',
                                                                               compact=False)
                self.presenter.view.panelPlots.on_plot_matrix(zvals=zvals, xylabels=yxlabels, cmap=cmap, set_page=True)
                if save_image:
                    save_kwargs = {'image_name':defaultValue}
                    self.presenter.view.panelPlots.save_images(evt=ID_saveRMSDmatrixImageDoc, **save_kwargs)
        elif self.itemType == 'DT/MS' or evtID in [ID_ylabel_DTMS_bins, ID_ylabel_DTMS_ms, ID_ylabel_DTMS_restore]:
            defaultValue = "DTMS_{}".format(basename)
            data = self.GetPyData(self.currentItem)
            self.presenter.view.panelPlots.on_plot_MSDT(data['zvals'], data['xvals'], data['yvals'],
                                                        data['xlabels'], data['ylabels'], set_page=True)
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
                        msY = msY / max(msY)
                    msFilenames.append(key)
                    if i == 0:
                        tempArray = msY
                    else:
                        tempArray = np.concatenate((tempArray, msY), axis=0)
                try:
                    # Form pandas dataframe
                    msX = self.itemData.multipleMassSpectrum[key]['xvals']
                    combMSOut = np.concatenate((msX, tempArray), axis=0)
                    combMSOut = combMSOut.reshape((len(msY), int(i + 2)), order='F')
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

                print('Dataframe was saved in %s. It took: %s s.' % (filename, str(np.round(time.time() - tstart, 4))))
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

        if kwargs.get("ask_permission", False):
            style = wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        else:
            style = wx.FD_SAVE

        dlg = wx.FileDialog(self.presenter.view, "Please select a name for the file",
                             "", "", wildcard=wildcard, style=style)
        dlg.CentreOnParent()

        if "default_name" in kwargs:
            defaultName = kwargs.pop("default_name")
        else:
            defaultName = ""
        defaultName = defaultName.replace(' ', '').replace(':', '').replace(" ", "").replace(".csv", "").replace(".txt", "").replace(".raw", "").replace(".d", "").replace(".", "_")

        dlg.SetFilename(defaultName)

        try: dlg.SetFilterIndex(wildcard_dict[self.config.saveDelimiter])
        except: pass

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
                self.presenter.onThreading(None, ('Cancelled operation', 4, 5)    , action='updateStatusbar')
        else:
            if dlg.ShowModal() == wx.ID_OK:
                filename = dlg.GetPath()
                basename, extension = os.path.splitext(filename)

                return filename, basename, extension
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
            data = [msXnew, msYnew]
            labels = ['m/z', 'Intensity']
            self.onSaveData(data=data, labels=labels,
                            data_format='%.4f', **kwargs)

        # Save MS - multiple MassLynx fiels
        elif self.itemType == 'Mass Spectra' and self.extractData == 'Mass Spectra':
            for key in self.itemData.multipleMassSpectrum:
                stripped_key_name = key.replace(" ", "").replace(".csv", "").replace(".txt", "").replace(".raw", "").replace(".d", "")
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
                data = [msXnew, msYnew]
                kwargs = {'default_name':defaultValue}
                self.onSaveData(data=data, labels=[xlabel, 'Intensity'],
                                data_format='%.4f', **kwargs)

        # Save calibration parameters - single
        elif self.itemType == 'Calibration Parameters':
            if evt.GetId() == ID_saveDataCSVDocument:
                saveFileName = self.presenter.getImageFilename(prefix=True, csv=True,
                                                               defaultValue='calibrationTable')
                if saveFileName == '' or saveFileName == None:
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
                self.onSaveData(data=[rtX, rtY], labels=[xlabel, 'Intensity'],
                                data_format='%.4f', **kwargs)

        # Save 1D - single
        elif self.itemType == 'Drift time (1D)':
            if evt.GetId() == ID_saveDataCSVDocument:
                defaultValue = "DT_1D_{}{}".format(basename, self.config.saveExtension)
                dtX = self.itemData.DT['xvals']
                dtY = self.itemData.DT['yvals']
                ylabel = self.itemData.DT['xlabels']
                kwargs = {'default_name':defaultValue}
                self.onSaveData(data=[dtX, dtY], labels=[ylabel, 'Intensity'],
                                data_format='%.2f', **kwargs)

        # Save RT (combined voltages) - batch + single
        elif self.itemType == 'Chromatograms (combined voltages, EIC)':
            # Batch mode
            if self.extractData == 'Chromatograms (combined voltages, EIC)':
                for key in self.itemData.IMSRTCombIons:
                    stripped_key_name = key.replace(" ", "")
                    defaultValue = "RT_{}_{}{}".format(basename, stripped_key_name, self.config.saveExtension)
                    rtX = self.itemData.IMSRTCombIons[key]['xvals']
                    rtY = self.itemData.IMSRTCombIons[key]['yvals']
                    xlabel = self.itemData.IMSRTCombIons[key]['xlabels']
                    kwargs = {'default_name':defaultValue}
                    self.onSaveData(data=[rtX, rtY], labels=[xlabel, 'Intensity'],
                                    data_format='%.4f', **kwargs)
#             # Single mode
            else:
                defaultValue = "RT_{}_{}{}".format(basename, self.extractData, self.config.saveExtension)
                rtX = self.itemData.IMSRTCombIons[self.extractData]['xvals']
                rtY = self.itemData.IMSRTCombIons[self.extractData]['yvals']
                xlabel = self.itemData.IMSRTCombIons[self.extractData]['xlabels']
                kwargs = {'default_name':defaultValue}
                self.onSaveData(data=[rtX, rtY], labels=[xlabel, 'Intensity'],
                                data_format='%.4f', **kwargs)

        # Save 1D - batch + single
        elif self.itemType == 'Drift time (1D, EIC, DT-IMS)':
            if evt.GetId() == ID_saveDataCSVDocument:
                saveFileName = self.presenter.getImageFilename(prefix=True, csv=True,
                                                               defaultValue='DT_1D_')
                if saveFileName == '' or saveFileName == None:
                    saveFileName = 'DT_1D_'
            # Batch mode
            if self.extractData == 'Drift time (1D, EIC, DT-IMS)':
                for key in self.itemData.IMS1DdriftTimes:
                    if self.itemData.dataType == 'Type: MANUAL':
                        name = re.split(', File: |.raw', key)
                        filename = ''.join([self.itemData.path, '\\', saveFileName,
                                            name[0], '_', name[1],
                                            self.config.saveExtension])
                        dtX = self.itemData.IMS1DdriftTimes[key]['xvals']
                        dtY = self.itemData.IMS1DdriftTimes[key]['yvals']
                        xlabel = self.itemData.IMS1DdriftTimes[key]['xlabels']
                        saveAsText(filename=filename,
                                   data=[dtX, dtY],
                                   format='%.4f',
                                   delimiter=self.config.saveDelimiter,
                                   header=self.config.saveDelimiter.join([xlabel, 'Intensity']))
                    else:
                        filename = ''.join([self.itemData.path, '\\', saveFileName,
                                            key, self.config.saveExtension])
                        zvals = self.itemData.IMS1DdriftTimes[key]['yvals']
                        yvals = self.itemData.IMS1DdriftTimes[key]['xvals']
                        xvals = np.asarray(self.itemData.IMS1DdriftTimes[key]['driftVoltage'])
                        # Y-axis labels need a value for [0,0]
                        yvals = np.insert(yvals, 0, 0)  # array, index, value
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
                    filename = ''.join([self.itemData.path, '\\', saveFileName,
                                        name[0], '_', name[1],
                                        self.config.saveExtension])
                    dtX = self.itemData.IMS1DdriftTimes[self.extractData]['xvals']
                    dtY = self.itemData.IMS1DdriftTimes[self.extractData]['yvals']
                    xlabel = self.itemData.IMS1DdriftTimes[self.extractData]['xlabels']
                    saveAsText(filename=filename,
                               data=[dtX, dtY],
                               format='%.4f',
                               delimiter=self.config.saveDelimiter,
                               header=self.config.saveDelimiter.join([xlabel, 'Intensity']))
                else:
                    filename = ''.join([self.itemData.path, '\\', saveFileName,
                                        self.extractData,
                                        self.config.saveExtension])
                    zvals = self.itemData.IMS1DdriftTimes[self.extractData]['yvals']
                    yvals = self.itemData.IMS1DdriftTimes[self.extractData]['xvals']
                    xvals = np.asarray(self.itemData.IMS1DdriftTimes[self.extractData].get('driftVoltage', " "))
                    # Y-axis labels need a value for [0,0]
                    yvals = np.insert(yvals, 0, 0)  # array, index, value
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
                saveData = np.vstack((xvals, zvals))
                yvals = map(str, yvals.tolist())
                labels = ["DT"]
                labels.extend(yvals)
                fmts = ["%.4f"] + ["%i"] * len(yvals)

                # Save 2D array
                kwargs = {'default_name':defaultValue}
                self.onSaveData(data=saveData,
                                labels=labels,
                                data_format=fmts,
                                **kwargs)

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
                    for label in xvals:
                        labels.append(label)
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
                    self.onSaveData(data=[dtX, dtY], labels=[ylabel, 'Intensity'],
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
                            stripped_key_name = key.replace(" ", "")
                            defaultValue = "DT_2D_{}_{}{}{}".format(basename, name_modifier, stripped_key_name, self.config.saveExtension)
                            # Prepare data for saving
                            zvals, xvals, xlabel, yvals, ylabel, __ = self.presenter.get2DdataFromDictionary(dictionary=data[key],
                                                                                                             dataType='plot', compact=False)
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
                                stripped_key_name = key.replace(" ", "")
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
                                self.onSaveData(data=[dtX, dtY], labels=[ylabel, 'Intensity'],
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
                        if saveFileName == '' or saveFileName == None:
                            saveFileName = 'DT_'

                        # Its a bit easier to save data with text labels using pandas df,
                        # so data is reshuffled to pandas dataframe and then saved
                        # in a standard .csv format
                        filename = ''.join([self.itemData.path, '\\', saveFileName, self.extractData, self.config.saveExtension])
                        zvals, xylabels, __ = self.presenter.get2DdataFromDictionary(dictionary=data[self.extractData],
                                                                                       plotType='Matrix', compact=False)
                        saveData = pd.DataFrame(data=zvals, index=xylabels, columns=xylabels)
                        saveData.to_csv(path_or_buf=filename,
                                        sep=self.config.saveDelimiter,
                                        header=True,
                                        index=True)
                    # Save 2D - single
                    elif self.extractData != 'RMSD Matrix' and evt.GetId() == ID_saveDataCSVDocument:
                        defaultValue = "DT_2D_{}_{}{}{}".format(basename, name_modifier, self.extractData, self.config.saveExtension)

                        zvals, xvals, xlabel, yvals, ylabel, __ = self.presenter.get2DdataFromDictionary(dictionary=data[self.extractData],
                                                                                                           dataType='plot', compact=False)
                        saveData = np.vstack((yvals, zvals.T))
                        try: xvals = map(str, xvals.tolist())
                        except AttributeError: xvals = map(str, xvals)
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
                        self.onSaveData(data=[dtX, dtY], labels=[ylabel, 'Intensity'],
                                        data_format='%.4f', **kwargs)
        else:
            return

#
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
            mzCentre = round((mzStart + mzEnd) / 2, 2)
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
                mzCentre = round((mzStart + mzEnd) / 2, 2)
                charge = data[key].get('charge', None)
                protein = data[key].get('protein', None)

                self.itemData.moleculeDetails.get('molWeight', None)

                self.presenter.OnAddDataToCCSTable(filename=self.itemData.title,
                                                   format=item_format, mzStart=mzStart,
                                                   mzEnd=mzEnd, mzCentre=mzCentre,
                                                   charge=charge, protein=protein)

    def onOpenDocInfo(self, evt):

        self.presenter.currentDoc = self.on_enable_document()
        document_title = self.on_enable_document()
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

        # update document with new attributes
        if not hasattr(docData, "other_data"):
            setattr(docData, "other_data", {})
            print("Added missing attributute ('other_data') to document")

        if not hasattr(docData, "tandem_spectra"):
            setattr(docData, "tandem_spectra", {})
            print("Added missing attributute ('tandem_spectra') to document")

        if not hasattr(docData, 'file_reader'):
            setattr(docData, "file_reader", {})
            print("Added missing attributute ('file_reader') to document")

        if not hasattr(docData, 'app_data'):
            setattr(docData, "app_data", {})
            print("Added missing attributute ('app_data') to document")

        if not hasattr(docData, 'last_saved'):
            setattr(docData, "last_saved", {})
            print("Added missing attributute ('last_saved') to document")

        # update document to latest version

        # Add document
        docItem = self.AppendItem(self.GetRootItem(), title)
        self.SetFocusedItem(docItem)
        self.SetItemImage(docItem, self.bulets_dict["document_on"], wx.TreeItemIcon_Normal)
        self.currentDocument = docItem
        self.title = title
        self.SetPyData(docItem, docData)

        # Add annotations to document tree
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

            # add unidec results
            if 'unidec' in docData.massSpectrum:
                docIonItem = self.AppendItem(annotsItemParent, 'UniDec')
                self.SetItemImage(docIonItem, self.bulets_dict["mass_spec"], wx.TreeItemIcon_Normal)
                for annotData in docData.massSpectrum['unidec']:
                    annotsItem = self.AppendItem(docIonItem, annotData)
                    self.SetPyData(annotsItem, docData.massSpectrum['unidec'][annotData])
                    self.SetItemImage(annotsItem, self.bulets_dict["mass_spec"], wx.TreeItemIcon_Normal)

            # add annotations
            if 'annotations' in docData.massSpectrum and len(docData.massSpectrum['annotations']) > 0:
                docIonItem = self.AppendItem(annotsItemParent, 'Annotations')
                self.SetItemImage(docIonItem, self.bulets_dict["annot"], wx.TreeItemIcon_Normal)
                for annotData in docData.massSpectrum['annotations']:
                    annotsItem = self.AppendItem(docIonItem, annotData)
                    self.SetPyData(annotsItem, docData.massSpectrum['annotations'][annotData])
                    self.SetItemImage(annotsItem, self.bulets_dict["annot"], wx.TreeItemIcon_Normal)

        if bool(docData.smoothMS):
            annotsItemParent = self.AppendItem(docItem, 'Mass Spectrum (processed)')
            self.SetPyData(annotsItemParent, docData.smoothMS)
            self.SetItemImage(annotsItemParent, self.bulets_dict["mass_spec"], wx.TreeItemIcon_Normal)

            # add unidec results
            if 'unidec' in docData.smoothMS:
                docIonItem = self.AppendItem(annotsItemParent, 'UniDec')
                self.SetItemImage(docIonItem, self.bulets_dict["mass_spec"], wx.TreeItemIcon_Normal)
                for annotData in docData.smoothMS['unidec']:
                    annotsItem = self.AppendItem(docIonItem, annotData)
                    self.SetPyData(annotsItem, docData.smoothMS['unidec'][annotData])
                    self.SetItemImage(annotsItem, self.bulets_dict["mass_spec"], wx.TreeItemIcon_Normal)

            # add annotations
            if 'annotations' in docData.smoothMS and len(docData.smoothMS['annotations']) > 0:
                docIonItem = self.AppendItem(annotsItemParent, 'Annotations')
                self.SetItemImage(docIonItem, self.bulets_dict["annot"], wx.TreeItemIcon_Normal)
                for annotData in docData.smoothMS['annotations']:
                    annotsItem = self.AppendItem(docIonItem, annotData)
                    self.SetPyData(annotsItem, docData.smoothMS['annotations'][annotData])
                    self.SetItemImage(annotsItem, self.bulets_dict["annot"], wx.TreeItemIcon_Normal)

        if docData.gotMultipleMS == True:
            docIonItem = self.AppendItem(docItem, 'Mass Spectra')
            self.SetItemImage(docIonItem, self.bulets_dict["mass_spec"], wx.TreeItemIcon_Normal)
            for annotData in docData.multipleMassSpectrum:
                annotsItem = self.AppendItem(docIonItem, annotData)
                self.SetPyData(annotsItem, docData.multipleMassSpectrum[annotData])
                self.SetItemImage(annotsItem, self.bulets_dict["mass_spec_on"], wx.TreeItemIcon_Normal)

                # add unidec results
                if 'unidec' in docData.multipleMassSpectrum[annotData]:
                    docIonItemInner = self.AppendItem(annotsItem, "UniDec")
                    self.SetItemImage(docIonItemInner, self.bulets_dict["mass_spec_on"], wx.TreeItemIcon_Normal)
                    for annotDataInner in docData.multipleMassSpectrum[annotData]['unidec']:
                        annotsItemInner = self.AppendItem(docIonItemInner, annotDataInner)
                        self.SetPyData(annotsItemInner, docData.multipleMassSpectrum[annotData]['unidec'][annotDataInner])
                        self.SetItemImage(annotsItemInner, self.bulets_dict["mass_spec_on"], wx.TreeItemIcon_Normal)

                # add annotations
                if ('annotations' in docData.multipleMassSpectrum[annotData] and
                    len(docData.multipleMassSpectrum[annotData]['annotations']) > 0):
                    docIonAnnotItem = self.AppendItem(annotsItem, 'Annotations')
                    self.SetItemImage(docIonAnnotItem, self.bulets_dict["annot"], wx.TreeItemIcon_Normal)
                    for annotNameData in docData.multipleMassSpectrum[annotData]['annotations']:
                        annotsAnnotItem = self.AppendItem(docIonAnnotItem, annotNameData)
                        self.SetPyData(annotsAnnotItem, docData.multipleMassSpectrum[annotData]['annotations'][annotNameData])
                        self.SetItemImage(annotsAnnotItem, self.bulets_dict["annot"], wx.TreeItemIcon_Normal)

        if len(docData.tandem_spectra) > 0:
            docIonItem = self.AppendItem(docItem, 'Tandem Mass Spectra')
            self.SetItemImage(docIonItem, self.bulets_dict["mass_spec"], wx.TreeItemIcon_Normal)
            self.SetPyData(docIonItem, docData.tandem_spectra)
#             for annotData in docData.tandem_spectra:
#                 annotsItem =  self.AppendItem(docIonItem, annotData)
#                 self.SetPyData(annotsItem, docData.tandem_spectra[annotData])
#                 self.SetItemImage(annotsItem, self.bulets_dict["mass_spec_on"], wx.TreeItemIcon_Normal)

        if docData.got1RT == True:
            annotsItem = self.AppendItem(docItem, 'Chromatogram')
            self.SetPyData(annotsItem, docData.RT)
            self.SetItemImage(annotsItem, self.bulets_dict["rt"], wx.TreeItemIcon_Normal)

        if hasattr(docData, 'gotMultipleRT'):
            if docData.gotMultipleRT == True:
                docIonItem = self.AppendItem(docItem, 'Chromatograms (EIC)')
                self.SetItemImage(docIonItem, self.bulets_dict["rt"], wx.TreeItemIcon_Normal)
                for annotData, __ in natsorted(docData.multipleRT.items()):
                    annotsItem = self.AppendItem(docIonItem, annotData)
                    self.SetPyData(annotsItem, docData.multipleRT[annotData])
                    self.SetItemImage(annotsItem, self.bulets_dict["rt_on"], wx.TreeItemIcon_Normal)

        if docData.got1DT == True:
            annotsItem = self.AppendItem(docItem, 'Drift time (1D)')
            self.SetPyData(annotsItem, docData.DT)
            self.SetItemImage(annotsItem, self.bulets_dict["drift_time"], wx.TreeItemIcon_Normal)

        if hasattr(docData, 'gotMultipleDT'):
            if docData.gotMultipleDT == True:
                docIonItem = self.AppendItem(docItem, 'Drift time (1D, EIC)')
                self.SetItemImage(docIonItem, self.bulets_dict["drift_time"], wx.TreeItemIcon_Normal)
                for annotData, __ in natsorted(docData.multipleDT.items()):
                    annotsItem = self.AppendItem(docIonItem, annotData)
                    self.SetPyData(annotsItem, docData.multipleDT[annotData])
                    self.SetItemImage(annotsItem, self.bulets_dict["drift_time_on"], wx.TreeItemIcon_Normal)

        if docData.gotExtractedDriftTimes == True:
            docIonItem = self.AppendItem(docItem, 'Drift time (1D, EIC, DT-IMS)')
            self.SetItemImage(docIonItem, self.bulets_dict["drift_time"], wx.TreeItemIcon_Normal)
            for annotData, __ in natsorted(docData.IMS1DdriftTimes.items()):
                annotsItem = self.AppendItem(docIonItem, annotData)
                self.SetPyData(annotsItem, docData.IMS1DdriftTimes[annotData])
                self.SetItemImage(annotsItem, self.bulets_dict["drift_time_on"], wx.TreeItemIcon_Normal)

        if docData.got2DIMS == True:
            annotsItem = self.AppendItem(docItem, 'Drift time (2D)')
            self.SetPyData(annotsItem, docData.IMS2D)
            self.SetItemImage(annotsItem, self.bulets_dict["heatmap"], wx.TreeItemIcon_Normal)

        if docData.got2Dprocess == True or len(docData.IMS2Dprocess) > 0:
            annotsItem = self.AppendItem(docItem, 'Drift time (2D, processed)')
            self.SetPyData(annotsItem, docData.IMS2Dprocess)
            self.SetItemImage(annotsItem, self.bulets_dict["heatmap"], wx.TreeItemIcon_Normal)

        if docData.gotExtractedIons == True:
            docIonItem = self.AppendItem(docItem, 'Drift time (2D, EIC)')
            self.SetItemImage(docIonItem, self.bulets_dict["heatmap"], wx.TreeItemIcon_Normal)
            for annotData, __ in natsorted(docData.IMS2Dions.items()):
                annotsItem = self.AppendItem(docIonItem, annotData)
                self.SetPyData(annotsItem, docData.IMS2Dions[annotData])
                self.SetItemImage(annotsItem, self.bulets_dict["heatmap_on"], wx.TreeItemIcon_Normal)
        if docData.gotCombinedExtractedIons == True:
            docIonItem = self.AppendItem(docItem, 'Drift time (2D, combined voltages, EIC)')
            self.SetItemImage(docIonItem, self.bulets_dict["heatmap"], wx.TreeItemIcon_Normal)
            for annotData, __ in natsorted(docData.IMS2DCombIons.items()):
                annotsItem = self.AppendItem(docIonItem, annotData)
                self.SetPyData(annotsItem, docData.IMS2DCombIons[annotData])
                self.SetItemImage(annotsItem, self.bulets_dict["heatmap_on"], wx.TreeItemIcon_Normal)

        if docData.gotCombinedExtractedIonsRT == True:
            docIonItem = self.AppendItem(docItem, 'Chromatograms (combined voltages, EIC)')
            self.SetItemImage(docIonItem, self.bulets_dict["rt"], wx.TreeItemIcon_Normal)
            for annotData, __ in natsorted(docData.IMSRTCombIons.items()):
                annotsItem = self.AppendItem(docIonItem, annotData)
                self.SetPyData(annotsItem, docData.IMSRTCombIons[annotData])
                self.SetItemImage(annotsItem, self.bulets_dict["rt_on"], wx.TreeItemIcon_Normal)

        if docData.got2DprocessIons == True:
            docIonItem = self.AppendItem(docItem, 'Drift time (2D, processed, EIC)')
            self.SetItemImage(docIonItem, self.bulets_dict["heatmap"], wx.TreeItemIcon_Normal)
            for annotData, __ in natsorted(docData.IMS2DionsProcess.items()):
                annotsItem = self.AppendItem(docIonItem, annotData)
                self.SetPyData(annotsItem, docData.IMS2DionsProcess[annotData])
                self.SetItemImage(annotsItem, self.bulets_dict["heatmap_on"], wx.TreeItemIcon_Normal)

        if docData.gotCalibration == True:
            docIonItem = self.AppendItem(docItem, 'Calibration peaks')
            self.SetItemImage(docIonItem, self.bulets_dict["calibration"], wx.TreeItemIcon_Normal)
            for annotData, __ in natsorted(docData.calibration.items()):
                annotsItem = self.AppendItem(docIonItem, annotData)
                self.SetPyData(annotsItem, docData.calibration[annotData])
                self.SetItemImage(annotsItem, self.bulets_dict["dots_on"], wx.TreeItemIcon_Normal)

        if docData.gotCalibrationDataset == True:
            docIonItem = self.AppendItem(docItem, 'Calibrants')
            self.SetItemImage(docIonItem, self.bulets_dict["calibration_on"], wx.TreeItemIcon_Normal)
            for annotData in docData.calibrationDataset:
                annotsItem = self.AppendItem(docIonItem, annotData)
                self.SetPyData(annotsItem, docData.calibrationDataset[annotData])
                self.SetItemImage(annotsItem, self.bulets_dict["dots_on"], wx.TreeItemIcon_Normal)

        if docData.gotCalibrationParameters == True:
            annotsItem = self.AppendItem(docItem, 'Calibration parameters')
            self.SetPyData(annotsItem, docData.calibrationParameters)
            self.SetItemImage(annotsItem, self.bulets_dict["calibration"], wx.TreeItemIcon_Normal)

        if docData.gotComparisonData == True:
            docIonItem = self.AppendItem(docItem, 'Input data')
            self.SetItemImage(docIonItem, self.bulets_dict["overlay"], wx.TreeItemIcon_Normal)
            for annotData, __ in natsorted(docData.IMS2DcompData.items()):
                annotsItem = self.AppendItem(docIonItem, annotData)
                self.SetPyData(annotsItem, docData.IMS2DcompData[annotData])
                self.SetItemImage(annotsItem, self.bulets_dict["heatmap_on"], wx.TreeItemIcon_Normal)

        if docData.gotOverlay == True or len(docData.IMS2DoverlayData) > 0:
            docIonItem = self.AppendItem(docItem, 'Overlay')
            self.SetItemImage(docIonItem, self.bulets_dict["overlay"], wx.TreeItemIcon_Normal)
            for annotData, __ in natsorted(docData.IMS2DoverlayData.items()):
                annotsItem = self.AppendItem(docIonItem, annotData)
                self.SetPyData(annotsItem, docData.IMS2DoverlayData[annotData])
                self.SetItemImage(annotsItem, self.bulets_dict["heatmap_on"], wx.TreeItemIcon_Normal)

        if docData.gotStatsData == True:
            docIonItem = self.AppendItem(docItem, 'Statistical')
            self.SetItemImage(docIonItem, self.bulets_dict["overlay"], wx.TreeItemIcon_Normal)
            for annotData, __ in natsorted(docData.IMS2DstatsData.items()):
                annotsItem = self.AppendItem(docIonItem, annotData)
                self.SetPyData(annotsItem, docData.IMS2DstatsData[annotData])
                self.SetItemImage(annotsItem, self.bulets_dict["heatmap_on"], wx.TreeItemIcon_Normal)

        if hasattr(docData, "DTMZ"):
            if docData.gotDTMZ:
                annotsItem = self.AppendItem(docItem, 'DT/MS')
                self.SetPyData(annotsItem, docData.DTMZ)
                self.SetItemImage(annotsItem, self.bulets_dict["heatmap"], wx.TreeItemIcon_Normal)

        if len(docData.other_data) > 0:
            docIonItem = self.AppendItem(docItem, 'Annotated data')
            self.SetItemImage(docIonItem, self.bulets_dict["calibration"], wx.TreeItemIcon_Normal)
            for annotData, __ in natsorted(docData.other_data.items()):
                annotsItem = self.AppendItem(docIonItem, annotData)
                self.SetPyData(annotsItem, docData.other_data[annotData])
                self.SetItemImage(annotsItem, self.bulets_dict["calibration_on"], wx.TreeItemIcon_Normal)

                # add annotations
                if ('annotations' in docData.other_data[annotData] and
                    len(docData.other_data[annotData]['annotations']) > 0):
                    docIonAnnotItem = self.AppendItem(annotsItem, 'Annotations')
                    self.SetItemImage(docIonAnnotItem, self.bulets_dict["annot"], wx.TreeItemIcon_Normal)
                    for annotNameData in docData.other_data[annotData]['annotations']:
                        annotsAnnotItem = self.AppendItem(docIonAnnotItem, annotNameData)
                        self.SetPyData(annotsAnnotItem, docData.other_data[annotData]['annotations'][annotNameData])
                        self.SetItemImage(annotsAnnotItem, self.bulets_dict["annot"], wx.TreeItemIcon_Normal)

        # Recursively check currently selected document
        self.on_enable_document(loadingData=True, expandAll=expandAll, evt=None)

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
                                     exceptionMsg=''.join(["Are you sure you would like to delete: ",
                                                            self.itemData.title, "?"]),
                                     type="Question")
                if dlg == wx.ID_NO:
                    self.presenter.onThreading(None, ('Cancelled operation', 4, 5)    , action='updateStatusbar')
                    return
                else:
                    deleteItem = self.itemData.title

            # Clear all plotsf
            if self.presenter.currentDoc == deleteItem:
                self.presenter.onClearAllPlots()
                self.presenter.currentDoc = None

        if deleteItem == '': return

        # Delete item from the list
        if self.ItemHasChildren(root):
            child, cookie = self.GetFirstChild(self.GetRootItem())
            title = self.GetItemText(child)
            iters = 0
            while deleteItem != title and iters < 500:
                child, cookie = self.GetNextChild(self.GetRootItem(), cookie)
                try:
                    title = self.GetItemText(child)
                    iters += 1
                except: pass

            if deleteItem == title:
                if child:
                    print("Deleted {}".format(deleteItem))
                    self.Delete(child)
                    # Remove data from dictionary if removing whole document
                    if evtID == ID_removeDocument  or evtID == None:
                        # make sure to clean-up various tables
                        try: self.presenter.view.panelMultipleIons.onClearItems(title)
                        except: pass
                        try: self.presenter.view.panelMultipleText.onClearItems(title)
                        except: pass
                        try: self.presenter.view.panelMML.onClearItems(title)
                        except: pass
                        try: self.presenter.view.panelLinearDT.topP.onClearItems(title)
                        except: pass
                        try: self.presenter.view.panelLinearDT.bottomP.onClearItems(title)
                        except: pass

                        # delete document
                        del self.presenter.documentsDict[title]
                        self.presenter.currentDoc = None
                        # go to the next document
                        if len(self.presenter.documentsDict) > 0:
                            self.presenter.currentDoc = self.presenter.documentsDict.keys()[0]
                            self.on_enable_document()
                        # collect garbage
                        gc.collect()

                    return True
            else:
                return False

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
        kwargs = {'title':"Sample information...",
                  'information':self.itemData.fileInformation.get('SampleDescription', 'None')}

        info = dialogs.panelInformation(self, **kwargs)
        info.Show()

    def on_enable_document(self, getSelected=False, loadingData=False, highlightSelected=False,
                           expandAll=False, expandSelected=None, evt=None):
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
                self.Expand(item)  # Parent item
                if expandAll:
                    self.ExpandAllChildren(item)

            # window label
            try:
                text = self.GetItemText(item)
                if text != 'Current documents':
#                     try: self.setCurrentDocument(text)
#                     except: pass
                    self.presenter.currentDoc = text
                    self.mainParent.SetTitle("ORIGAMI - v{} - {} ({})".format(self.config.version,
                                                                              text,
                                                                              self.itemData.dataType))
            except:
                self.mainParent.SetTitle("ORIGAMI - v{}".format(self.config.version))

            # status text
            try:
                parameters = self.itemData.parameters
                msg = "{}-{}".format(parameters.get('startMS', ""), parameters.get('endMS', ""))
                if msg == "-": msg = ""
                self.presenter.view.SetStatusText(msg, 1)
                msg = "MSMS: {}".format(parameters.get('setMS', ""))
                if msg == "MSMS: ": msg = ""
                self.presenter.view.SetStatusText(msg, 2)
            except: pass

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
                self.Expand(item)  # Parent item
                if expandAll:
                    self.ExpandAllChildren(item)

            # window label
            try:
                text = self.GetItemText(item)
                if text != 'Current documents':
#                     try: self.setCurrentDocument(text)
#                     except: pass
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
        print(self.itemData)

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

    def on_open_MGF_file(self, evt=None):
        dlg = wx.FileDialog(self.presenter.view, "Open MGF file", wildcard="*.mgf; *.MGF" ,
                           style=wx.FD_DEFAULT_STYLE | wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            tstart = time.time()
            path = dlg.GetPath()
            print("Opening {}...".format(path))
            reader = io_mgf.MGFreader(filename=path)
            print("Created file reader. Loading scans...")

            basename = os.path.basename(path)
            data = reader.get_n_scans(n_scans=50000)
            kwargs = {'data_type':"Type: MS/MS", "file_format":"Format: .mgf"}
            document = self.presenter.on_create_document(basename, path, **kwargs)

            # add data to document
            document.tandem_spectra = data
            document.file_reader = {'data_reader':reader}

            title = "Precursor: {:.4f} [{}]".format(data["Scan 1"]['scan_info']['precursor_mz'],
                                                    data["Scan 1"]['scan_info']['precursor_charge'])
            self.presenter.view.panelPlots.on_plot_centroid_MS(data["Scan 1"]['xvals'],
                                                               data["Scan 1"]['yvals'],
                                                               title=title)

            self.presenter.OnUpdateDocument(document, 'document')
            print("It took {:.4f} seconds to load {}".format(time.time() - tstart, basename))

    def on_open_MGF_file_fcn(self, evt):

        if not self.config.threading:
            self.on_open_MGF_file(evt)
        else:
            self.onThreading(evt, (evt,), action='load_mgf')

    def on_open_mzML_file(self, evt=None):
        dlg = wx.FileDialog(self.presenter.view, "Open mzML file", wildcard="*.mzML; *.MZML" ,
                           style=wx.FD_DEFAULT_STYLE | wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            tstart = time.time()
            path = dlg.GetPath()
            print("Opening {}...".format(path))
            reader = io_mzml.mzMLreader(filename=path)
            print("Created file reader. Loading scans...")

            basename = os.path.basename(path)
            data = reader.get_n_scans(n_scans=999999)
            kwargs = {'data_type':"Type: MS/MS", "file_format":"Format: .mzML"}
            document = self.presenter.on_create_document(basename, path, **kwargs)

            # add data to document
            document.tandem_spectra = data
            document.file_reader = {'data_reader':reader}

            title = "Precursor: {:.4f} [{}]".format(data["Scan 1"]['scan_info']['precursor_mz'],
                                                    data["Scan 1"]['scan_info']['precursor_charge'])
            self.presenter.view.panelPlots.on_plot_centroid_MS(data["Scan 1"]['xvals'],
                                                               data["Scan 1"]['yvals'],
                                                               title=title)

            self.presenter.OnUpdateDocument(document, 'document')
            print("It took {:.4f} seconds to load {}".format(time.time() - tstart, basename))

    def on_open_mzML_file_fcn(self, evt):

        if not self.config.threading:
            self.on_open_mzML_file(evt)
        else:
            self.onThreading(evt, (evt,), action='load_mzML')

    def on_open_MSMS_viewer(self, evt=None, **kwargs):

        self.panelTandemSpectra = panelTandemSpectra(self.presenter.view,
                                                     self.presenter,
                                                     self.config,
                                                     self.icons,
                                                     **kwargs)
        self.panelTandemSpectra.Show()

    def on_process_UVPD(self, evt=None, **kwargs):
        from panelUVPD import panelUVPD
        self.panelUVPD = panelUVPD(self.presenter.view,
                                   self.presenter,
                                   self.config,
                                   self.icons,
                                   **kwargs)
        self.panelUVPD.Show()

    def on_open_extract_DTMS(self, evt):
        from gui_elements.panel_extractDTMS import panel_extractDTMS
        self.panel_extractDTMS = panel_extractDTMS(self.presenter.view,
                                                   self.presenter,
                                                   self.config,
                                                   self.icons)
        self.panel_extractDTMS .Show()

    def on_add_mzID_file(self, evt):
        document = self.data_processing._on_get_document()

        dlg = wx.FileDialog(self.presenter.view, "Open mzIdentML file", wildcard="*.mzid; *.mzid.gz; *mzid.zip" ,
                           style=wx.FD_DEFAULT_STYLE | wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            print("Adding identification information to {}".format(document.title))
            tstart = time.time()
            path = dlg.GetPath()
            reader = io_mzid.MZIdentReader(filename=path)

            # check if data reader is present
            try:
                index_dict = document.file_reader['data_reader'].create_title_map(document.tandem_spectra)
            except KeyError:
                print("Missing file reader. Creating a new instance of the reader...")
                if document.fileFormat == "Format: .mgf":
                    document.file_reader['data_reader'] = io_mgf.MGFreader(filename=document.path)
                elif document.fileFormat == "Format: .mzML":
                    document.file_reader['data_reader'] = io_mzml.mzMLreader(filename=document.path)
                else:
                    dialogs.dlgBox(exceptionTitle='Error',
                                   exceptionMsg="{} not supported yet!".format(document.fileFormat),
                                   type="Error", exceptionPrint=True)
                    return
                try:
                    index_dict = document.file_reader['data_reader'].create_title_map(document.tandem_spectra)
                except AttributeError:
                    dialogs.dlgBox(exceptionTitle='Error',
                                   exceptionMsg="Cannot add identification information to {} yet!".format(document.fileFormat),
                                   type="Error", exceptionPrint=True)
                    return

            tandem_spectra = reader.match_identification_with_peaklist(peaklist=deepcopy(document.tandem_spectra),
                                                                       index_dict=index_dict)

            document.tandem_spectra = tandem_spectra

            self.presenter.OnUpdateDocument(document, 'document')
            print("It took {:.4f} seconds to annotate {}".format(time.time() - tstart, document.title))

    def on_add_mzID_file_fcn(self, evt):

        if not self.config.threading:
            self.on_add_mzID_file(evt)
        else:
            self.onThreading(evt, (evt,), action='add_mzidentml_annotations')

    def on_open_thermo_file_fcn(self, evt):

        if not self.config.threading:
            self.on_open_thermo_file(evt)
        else:
            self.onThreading(evt, (evt,), action='load_thermo_RAW')

    def on_open_thermo_file(self, evt):
        dlg = wx.FileDialog(self.presenter.view, "Open Thermo file", wildcard="*.raw; *.RAW" ,
                           style=wx.FD_DEFAULT_STYLE | wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            tstart = time.time()
            path = dlg.GetPath()
            print("Opening {}...".format(path))
            reader = io_thermo.thermoRAWreader(filename=path)
            print("Created file reader. Loading scans...")

            # get info
            info = reader.get_scan_info()

            # get chromatogram
            rtX, rtY = reader.get_tic()
            self.presenter.view.panelPlots.on_plot_RT(rtX, rtY, "Time (min)", set_page=False)

            mass_spectra = reader.get_spectrum_for_each_filter()
            chromatograms = reader.get_chromatogram_for_each_filter()
#             rtX, rtY = reader._stitch_chromatograms(chromatograms)

            # get average mass spectrum
            msX, msY = reader.get_average_spectrum()
            xlimits = [np.min(msX), np.max(msX)]
            name_kwargs = {"document":None, "dataset": None}
            self.presenter.view.panelPlots.on_plot_MS(
                msX, msY, xlimits=xlimits, set_page=True, **name_kwargs)

            basename = os.path.basename(path)
            kwargs = {'data_type':"Type: MS", "file_format":"Format: Thermo (.RAW)"}
            document = self.presenter.on_create_document(basename, path, **kwargs)

            # add data to document
            document.got1RT = True
            document.RT = {'xvals':rtX, 'yvals':rtY, 'xlabels':'Time (min)'}

            document.gotMS = True
            document.massSpectrum = {'xvals':msX, 'yvals':msY,
                                     'xlabels':'m/z (Da)',
                                     'xlimits':xlimits}

            document.gotMultipleMS = True
            document.multipleMassSpectrum = mass_spectra

            document.gotMultipleRT = True
            document.multipleRT = chromatograms

            document.file_reader = {'data_reader':reader}

            self.presenter.OnUpdateDocument(document, 'document')
            print("It took {:.4f} seconds to load {}".format(time.time() - tstart, document.title))


class topPanel(wx.Panel):

    def __init__(self, parent, mainParent, icons, presenter, config):
        wx.Panel.__init__(self, parent=parent)
        self.parent = parent
        self.mainParent = mainParent
        self.icons = icons
        self.presenter = presenter
        self.config = config
        self.makeTreeCtrl()

        self.panelSizer = wx.BoxSizer(wx.VERTICAL)
        self.panelSizer.Add(self.documents, 1, wx.EXPAND, 0)

        self.SetSizer(self.panelSizer)

    def makeTreeCtrl(self):
        self.documents = documentsTree(self,
                                       self.mainParent,
                                       self.presenter,
                                       self.icons,
                                       self.config, -1,
                                       size=(250, -1))

