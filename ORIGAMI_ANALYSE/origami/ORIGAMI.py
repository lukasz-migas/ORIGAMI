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

# Import libraries
import gc
import logging
import os
import re
import sys
import threading
import time
import warnings
import webbrowser
from math import log, sqrt

import matplotlib.colors as colors
import numpy as np
import pandas as pd
import wx
from numpy.ma import masked_array
from scipy.stats import linregress

import mainWindow as mainWindow
import processing.activation as pr_activation
import processing.heatmap as pr_heatmap
import processing.origami_ms as pr_origami
import processing.spectra as pr_spectra
import readers.io_text_files as io_text
import readers.io_waters_raw as io_waters
import unidec as unidec
from config import OrigamiConfig as config
from document import document as documents
from gui_elements.dialog_selectDocument import panelSelectDocument
from gui_elements.misc_dialogs import dlgAsk, dlgBox
from gui_elements.panel_calibrantDB import panelCalibrantDB
from gui_elements.panel_htmlViewer import panelHTMLViewer
from gui_elements.panel_notifyNewVersion import panelNotifyNewVersion
from help_documentation import OrigamiHelp
from icons import IconContainer as icons
from ids import *
from toolbox import (MidpointNormalize, checkExtension, detectPeaks,
                     find_nearest,
                     removeDuplicates, saveObject)
from utils.check import get_latest_version, compare_versions, isempty, isnumber
from utils.color import (combine_rgb,
                         convertRGB255to1,
                         make_rgb,
                         )
from utils.converters import str2int, str2num
from utils.logging import set_logger, set_logger_level
from utils.random import randomIntegerGenerator
from utils.time import getTime

# needed to avoid annoying warnings to be printed on console
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

logger = logging.getLogger("origami")

# disable MPL logger
logging.getLogger("matplotlib").setLevel(logging.ERROR)


class ORIGAMI(object):

    def __init__(self, *args, **kwargs):
        self.__wx_app = wx.App(redirect=False, filename='ORIGAMI')
        self.view = None
        self.init(*args, **kwargs)

    def start(self):
        self.view.Show()
        self.__wx_app.MainLoop()

    def onRebootWindow(self, evt):
        """
        Reset window
        """
        self.view.Destroy()
        self.view = None
        self.view = mainWindow.MyFrame(self,
                                       config=self.config,
                                       icons=self.icons,
                                       title="ORIGAMI")
        self.view.Show()

    def quit(self):
        # TODO Export config to file
        self.__wx_app.ProcessIdle()
        self.__wx_app.ExitMainLoop()
        self.view.Destroy()
        return True

    def endSession(self):
        wx.CallAfter(self.quit, force=True)

    def init(self, *args, **kwargs):
        self.config = config()
        self.icons = icons()
        self.docs = documents()
        self.help = OrigamiHelp()

        # Load configuration file
        self.onImportConfig(evt=None, onStart=True)

        # Setup variables
        self.initilize_state()
        self.view = mainWindow.MyFrame(self,
                                       config=self.config,
                                       icons=self.icons,
                                       helpInfo=self.help,
                                       title="ORIGAMI - %s " % self.config.version)
        self.__wx_app.SetTopWindow(self.view)
        self.__wx_app.SetAppName("ORIGAMI - %s " % self.config.version)
        self.__wx_app.SetVendorName("Lukasz G. Migas, University of Manchester")

        # Assign standard input/output to variable
        self.config.stdin = sys.stdin
        self.config.stdout = sys.stdout
        self.config.stderr = sys.stderr

        # Set current working directory
        self.config.cwd = os.getcwd()

        # Set unidec directory
        self.config.unidec_path = os.path.join(os.getcwd(), "unidec_bin\\UniDec.exe")

        # Set temporary data path
        temp_data_folder = os.path.join(os.getcwd(), "temporary_data")
        if not os.path.exists(temp_data_folder):
            os.makedirs(temp_data_folder)
        self.config.temporary_data = temp_data_folder

        # Setup plot style
        self.view.panelPlots.onChangePlotStyle(evt=None)
        self.view.panelPlots.onChangePalette(evt=None)
        self.view.updateRecentFiles()

        self.logging = self.config.logging
        self.config._processID = os.getpid()

        # add data processing module
        self.data_processing = self.view.data_processing
        self.data_handling = self.view.data_handling

#         # Load protein/CCS database
#         if self.config.loadCCSAtStart:
#             self.onImportCCSDatabase(evt=None, onStart=True)

        gc.enable()
        self.on_start_logging()

        # add binding to UniDec engine
        self.config.unidec_engine = unidec.UniDec()

        # check version
        self.onCheckVersion()

        if self.config.checkForDriftscopeAtStart:
            self.config.initlizePaths()

        # add data handling and processing modules
        self.view.panelDocuments.documents._setup_handling_and_processing()
        self.view.panelMultipleIons._setup_handling_and_processing()
        self.view.panelMultipleText._setup_handling_and_processing()
        self.view.panelMML._setup_handling_and_processing()
        self.view.panelPlots._setup_handling_and_processing()

#         for file_path in [
# #                         'Z:\###_PhD1_###\RebeccaBeveridge - P27 CdkCyclin Fdc1\p27_data_January2018\SynaptG2\LM_15012017_P27K56_2.pickle'
#                         'Z:\###_PhD2_###\CIU\PythonCIU\ORIGAMI_2\_TEST_DATA\ubb.pickle',
#                         'Z:\###_PhD2_###\CIU\PythonCIU\ORIGAMI_2\_TEST_DATA\ORIGAMI_ConA_z20.pickle'
#                           ]:
#             self.onOpenDocument(evt=None, file_path = file_path)

    def on_start_logging(self):

        log_directory = os.path.join(self.config.cwd, "logs")
        if not os.path.exists(log_directory):
            print("Directory logs did not exist - created a new one in {}".format(log_directory))
            os.makedirs(log_directory)

        # Generate filename
        if self.config.loggingFile_path is None:
            file_path = "origami_{}.log".format(self.config.startTime)
            self.config.loggingFile_path = os.path.join(
                log_directory, file_path)

        set_logger(file_path=self.config.loggingFile_path)
        set_logger_level(verbose="DEBUG")

        logger.info("Logs can be found in {}".format(self.config.loggingFile_path))

    def initilize_state(self):
        """
        Pre-set variables
        """
        self.docsText = {}
        self.documents = []
        self.documentsDict = {}
        self.currentDoc = None
        self.currentCalibrationParams = []
        self.currentPath = None

    def on_create_document(self, name, path, **kwargs):
        """
        Create document
        """

        document = documents()
        document.title = name
        document.path = path
        document.userParameters = self.config.userParameters
        document.userParameters['date'] = getTime()
        document.dataType = kwargs.get("data_type", "Type: Other")
        document.fileFormat = kwargs.get("file_format", "Format: Other")

        return document

    def onThreading(self, evt, args, action='loadOrigami'):
        # Setup thread
#         if action == 'loadOrigami':
#             th = threading.Thread(target=self.onLoadOrigamiDataThreaded, args=(args, evt))

        if action == 'saveFigs':
            target, path, kwargs = args
            th = threading.Thread(target=target.saveFigure2, args=(path,), kwargs=kwargs)

#         elif action == 'extractIons':
#             extract_type = args
#             th = threading.Thread(target=self.on_extract_2D_from_mass_range, args=(extract_type,))

        elif action == 'updateStatusbar':
            if len(args) == 2:
                msg, position = args
                th = threading.Thread(target=self.view.updateStatusbar, args=(msg, position))
            elif len(args) == 3:
                msg, position, delay = args
                th = threading.Thread(target=self.view.updateStatusbar, args=(msg, position, delay))
        elif action == 'export_settings':
            th = threading.Thread(target=self.config.saveConfigXML, args=args)

        # Start thread
        try:
            th.start()
        except Exception:
            print('Failed to execute the operation in threaded mode. Consider switching it off?')

#     def onLinearDTirectory(self, e=None):
#         # self.config.ciuMode = 'LinearDT'
#         # self.config.extractMode = 'singleIon'
#
#         # Reset arrays
#         imsData2D = np.array([])
#         dlg = wx.DirDialog(self.view, "Choose a MassLynx file:",
#                            style=wx.DD_DEFAULT_STYLE)
#         if self.config.dirname == '':
#             pass
#         else:
#             dlg.SetPath(self.config.dirname)
#         if dlg.ShowModal() == wx.ID_OK:
#             tstart = time.clock()
#             print("You chose %s" % dlg.GetPath())
#             # Update statusbar
#             self.onThreading(None, ("Opened: {}".format(dlg.GetPath()), 4), action='updateStatusbar')
#             # Get experimental parameters
#             parameters = self.config.importMassLynxInfFile(path=dlg.GetPath())
#             xlimits = [parameters['startMS'], parameters['endMS']]
#             # Mass spectra
#             extract_kwargs = {'return_data': True}
#             msDataX, msDataY = io_waters.driftscope_extract_MS(path=dlg.GetPath(),
#                                                                 driftscope_path=self.config.driftscopePath,
#                                                                 **extract_kwargs)
#
#             # RT
#             extract_kwargs = {'return_data': True, 'normalize': True}
#             xvalsRT, rtDataY, rtDataYnorm = io_waters.driftscope_extract_RT(path=dlg.GetPath(),
#                                                                              driftscope_path=self.config.driftscopePath,
#                                                                              **extract_kwargs)
#
#             # 2D
#             extract_kwargs = {'return_data': True}
#             imsData2D = io_waters.driftscope_extract_2D(path=dlg.GetPath(),
#                                                           driftscope_path=self.config.driftscopePath,
#                                                           **extract_kwargs)
#             xlabels = 1 + np.arange(len(imsData2D[1, :]))
#             ylabels = 1 + np.arange(len(imsData2D[:, 1]))
#
#             # Update status bar with MS range
#             self.view.SetStatusText("{}-{}".format(parameters.get('startMS', ""), parameters.get('endMS', "")), 1)
#             self.view.SetStatusText("MSMS: {}".format(parameters.get('setMS', "")), 2)
#
#             tend = time.clock()
#             self.onThreading(None, ('Total time to open file: %.2gs' % (tend - tstart), 4), action='updateStatusbar')
#
#             # Add info to document
#             __, idName = os.path.split(dlg.GetPath())
#             idName = (''.join([idName])).encode('ascii', 'replace')
#             self.docs = documents()
#             self.docs.title = idName
#             self.currentDoc = idName  # Currently plotted document
#             self.docs.userParameters = self.config.userParameters
#             self.docs.userParameters['date'] = getTime()
#             self.docs.path = dlg.GetPath()
#             self.docs.parameters = parameters
#             self.docs.dataType = 'Type: Multifield Linear DT'
#             self.docs.fileFormat = 'Format: MassLynx (.raw)'
#             # Add data
#             self.docs.gotMS = True
#             self.docs.massSpectrum = {'xvals': msDataX,
#                                       'yvals': msDataY,
#                                       'xlabels': 'm/z (Da)',
#                                       'xlimits': xlimits}
#             self.docs.got1RT = True
#             self.docs.RT = {'xvals': xvalsRT,
#                             'yvals': rtDataYnorm,
#                             'xlabels': 'Scans'}
#             self.docs.got2DIMS = True
#             # Format: zvals, xvals, xlabel, yvals, ylabel
#             self.docs.IMS2D = {'zvals': imsData2D,
#                                'xvals': xlabels,
#                                 'xlabels': 'Scans',
#                                 'yvals': ylabels,
#                                 'ylabels': 'Drift time (bins)',
#                                 'cmap': self.docs.colormap}
#
#             # Plots
#             self.view.panelPlots.on_plot_RT(xvalsRT, rtDataYnorm, 'Scans')
#             name_kwargs = {"document": self.docs.title, "dataset": "Mass Spectrum"}
#             self.view.panelPlots.on_plot_MS(msDataX, msDataY, xlimits=xlimits, **name_kwargs)
#
#             # Update document
#             self.OnUpdateDocument(self.docs, 'document')
#
#         dlg.Destroy()
#         return None
#
#     def onCalibrantRawDirectory(self, e=None):
#         """
#         This function opens calibrant file
#         """
#
#         # Reset arrays
#         dlg = wx.DirDialog(self.view, "Choose a MassLynx file:",
#                            style=wx.DD_DEFAULT_STYLE)
#
#         if dlg.ShowModal() == wx.ID_OK:
#             tstart = time.clock()
#             # Check whether appropriate calibration file was selected
#             path = self.checkIfRawFile(dlg.GetPath())
#             if path is None:
#                 msg = "Are you sure this was a MassLynx (.raw) file? Please load file in correct file format."
#                 dlgBox(exceptionTitle='Please load MassLynx (.raw) file',
#                        exceptionMsg=msg,
#                        type="Error")
#                 return
#             print("You chose %s" % dlg.GetPath())
#             # Update statusbar
#             self.onThreading(None, ("Opened: {}".format(dlg.GetPath()), 4), action='updateStatusbar')
#             # Get experimental parameters
#             parameters = self.config.importMassLynxInfFile(path=dlg.GetPath())
#             xlimits = [parameters['startMS'], parameters['endMS']]
#             # Mass spectra
#             extract_kwargs = {'return_data': True}
#             msDataX, msDataY = io_waters.driftscope_extract_MS(path=dlg.GetPath(),
#                                                                 driftscope_path=self.config.driftscopePath,
#                                                                 **extract_kwargs)
#             # RT
#             extract_kwargs = {'return_data': True, 'normalize': True}
#             xvalsRT, rtDataY, rtDataYnorm = io_waters.driftscope_extract_RT(path=dlg.GetPath(),
#                                                                              driftscope_path=self.config.driftscopePath,
#                                                                              **extract_kwargs)
#
#             # DT
#             extract_kwargs = {'return_data': True}
#             xvalsDT, imsData1D = io_waters.driftscope_extract_DT(path=dlg.GetPath(),
#                                                                   driftscope_path=self.config.driftscopePath,
#                                                                   **extract_kwargs)
#
#             # Update status bar with MS range
#             self.view.SetStatusText("{}-{}".format(parameters['startMS'], parameters['endMS']), 1)
#             self.view.SetStatusText("MSMS: {}".format(parameters['setMS']), 2)
#             tend = time.clock()
#             self.onThreading(None, ('Total time to open file: %.2gs' % (tend - tstart), 4),
#                              action='updateStatusbar')
#
#             # Add info to document
#             __, idName = os.path.split(dlg.GetPath())
#             idName = (''.join([idName])).encode('ascii', 'replace')
#             self.docs = documents()
#             self.docs.title = idName
#             self.currentDoc = idName  # Currently plotted document
#             self.docs.path = dlg.GetPath()
#             self.docs.userParameters = self.config.userParameters
#             self.docs.userParameters['date'] = getTime()
#             self.docs.parameters = parameters
#             self.docs.dataType = 'Type: CALIBRANT'
#             self.docs.fileFormat = 'Format: MassLynx (.raw)'
#             self.docs.corrC = parameters['corrC']
#             # Add data
#             self.docs.gotMS = True
#             self.docs.massSpectrum = {'xvals': msDataX,
#                                       'yvals': msDataY,
#                                       'xlabels': 'm/z (Da)',
#                                       'xlimits': xlimits}
#             self.docs.got1RT = True
#             self.docs.RT = {'xvals': xvalsRT,
#                             'yvals': rtDataYnorm,
#                             'xlabels': 'Scans'}
#             self.docs.got1DT = True
#             self.docs.DT = {'xvals': xvalsDT,
#                             'yvals': imsData1D,
#                             'xlabels': 'Drift time (bins)',
#                             'ylabels': 'Intensity'}
#
#             # Add plots
#             self.view.panelPlots.on_plot_RT(xvalsRT, rtDataYnorm, 'Scans')
#             self.onPlotMSDTCalibration(msX=msDataX,
#                                        msY=msDataY,
#                                        xlimits=xlimits,
#                                        dtX=xvalsDT,
#                                        dtY=imsData1D,
#                                        xlabelDT='Drift time (bins)',
#                                        color=self.docs.lineColour)
#
#             self.view.panelPlots.mainBook.SetSelection(self.config.panelNames['Calibration'])
#
#             # Update document
#             self.OnUpdateDocument(self.docs, 'document')
#
#         dlg.Destroy()
#         return None
#
#     def onAddCalibrantMultiple(self, evt):
#
#         tempList = self.view.panelCCS.topP.peaklist
#         for row in range(tempList.GetItemCount()):
#             if evt.GetId() == ID_extractCCScalibrantAll:
#                 pass
#             elif evt.GetId() == ID_extractCCScalibrantSelected:
#                 if not tempList.IsChecked(index=row):
#                     continue
#
#             # Get values
#             filename = tempList.GetItem(itemId=row, col=self.config.ccsTopColNames['filename']).GetText()
#             mzStart = str2num(tempList.GetItem(itemId=row, col=self.config.ccsTopColNames['start']).GetText())
#             mzEnd = str2num(tempList.GetItem(itemId=row, col=self.config.ccsTopColNames['end']).GetText())
#             rangeName = ''.join([str(mzStart), '-', str(mzEnd)])
#
#             # Get the document
#             document = self.documentsDict[filename]
#             if document.fileFormat == 'Format: DataFrame':
#                 print(('Skipping %s as this is a DataFrame document.' % rangeName))
#                 continue
#
#             extract_kwargs = {'return_data': True}
#             __, yvalsDT = io_waters.driftscope_extract_DT(path=document.path,
#                                                            driftscope_path=self.config.driftscopePath,
#                                                            **extract_kwargs)
#             mphValue = (max(yvalsDT)) * 0.2  # 20 % cutoff
#             # Get pusher
#             pusherFreq = document.parameters.get('pusherFreq', 1)
#
#             if pusherFreq != 1:
#                 xlabel = 'Drift time (ms)'
#             else:
#                 xlabel = 'Drift time (bins)'
#             # Create x-labels in ms
#             xvalsDT = (np.arange(1, len(yvalsDT) + 1) * pusherFreq) / 1000
#
#             # Detect peak
#             ind = detectPeaks(x=yvalsDT, mph=mphValue)
#             if len(ind) > 1:
#                 self.view.SetStatusText('Found more than one peak. Selected the first one', 3)
#                 tD = np.round(xvalsDT[ind[0]], 2)
#                 print((ind[0], tD))
#                 yval = np.round(yvalsDT[ind[0]], 2)
#                 yval = pr_spectra.normalize_1D(yval)
#             elif len(ind) == 0:
#                 self.view.SetStatusText('Found no peaks', 3)
#                 tD = ""
#             else:
#                 self.view.SetStatusText('Found one peak', 3)
#                 tD = np.round(xvalsDT[ind[0]], 2)
# #                 print(ind[0], tD)
#                 yval = np.round(yvalsDT[ind[0]], 2)
#                 yval = pr_spectra.normalize_1D(yval)
#
#             # Add data to document
#             protein, charge, CCS, gas, mw = None, None, None, None, None
#
#             # Check whether the document has molecular weight
#             mw = document.moleculeDetails.get('molWeight', None)
#             protein = document.moleculeDetails.get('protein', None)
#
#             document.gotCalibration = True
#             document.calibration[rangeName] = {'xrange': [mzStart, mzEnd],
#                                                'xvals': xvalsDT,
#                                                'yvals': yvalsDT,
#                                                'xcentre': ((mzEnd + mzStart) / 2),
#                                                'protein': protein,
#                                                'charge': charge,
#                                                'ccs': CCS, 'tD': tD,
#                                                'gas': gas,
#                                                'xlabels': xlabel,
#                                                'peak': [tD, yval],
#                                                'mw': mw
#                                                }
#             # Plot
#             self.onPlot1DTCalibration(dtX=xvalsDT,
#                                       dtY=yvalsDT,
#                                       xlabel=xlabel,
#                                       color=document.lineColour)
#
#             if tD != "":
#                 self.addMarkerMS(xvals=tD,
#                                  yvals=yval,
#                                  color=self.config.annotColor,
#                                  marker=self.config.markerShape,
#                                  size=self.config.markerSize,
#                                  plot='CalibrationDT')
#
#             # Update document
#             self.OnUpdateDocument(document, 'document')
#
#     def onIRTextFile(self, evt):
#         dlg = wx.FileDialog(self.view, "Choose a text file:", wildcard="*.txt; *.csv",
#                             style=wx.FD_DEFAULT_STYLE | wx.FD_CHANGE_DIR)
#         if dlg.ShowModal() == wx.ID_OK:
#             print("You chose %s" % dlg.GetPath())
#             imsData2D, xAxisLabels, yAxisLabels = None, None, None
#             imsData2D, xAxisLabels, yAxisLabels = io_text.text_infrared_open(path=dlg.GetPath())
#             dataSplit, xAxisLabels, yAxisLabels, dataRT, data1DT = pr_origami.origami_combine_infrared(
#                 inputData=imsData2D, threshold=2000, noiseLevel=500)
#
#             # Add data to document
#             __, idName = os.path.split(dlg.GetPath())
#             idName = (''.join([idName])).encode('ascii', 'replace')
#             self.docs = documents()
#             self.docs.title = idName
#             self.currentDoc = idName  # Currently plotted document
#             self.docs.path = os.path.dirname(dlg.GetPath())
#             self.docs.userParameters = self.config.userParameters
#             self.docs.userParameters['date'] = getTime()
#             self.docs.dataType = 'Type: IR IM-MS'
#             self.docs.fileFormat = 'Format: Text (.csv/.txt)'
#
#             self.docs.got1RT = True
#             self.docs.RT = {'xvals': yAxisLabels,  # bins
#                             'yvals': dataRT,
#                             'xlabels': 'Wavenumber (cm⁻¹)'}
#             self.docs.got1DT = True
#             self.docs.DT = {'xvals': xAxisLabels,
#                             'yvals': data1DT,
#                             'xlabels': 'Drift time (bins)',
#                             'ylabels': 'Intensity'}
#
#             self.docs.got2DIMS = True
#             self.docs.IMS2D = {'zvals': dataSplit,
#                                'xvals': xAxisLabels,
#                                'xlabels': 'Wavenumber (cm⁻¹)',
#                                'yvals': yAxisLabels,
#                                'ylabels': 'Drift time (bins)',
#                                'cmap': self.docs.colormap}
#             # Append to list
#             self.documentsDict[idName] = self.docs
#
#             # Plots
#             self.view.panelPlots.on_plot_1D(yAxisLabels, data1DT, 'Drift time (bins)')
#             self.view.panelPlots.on_plot_RT(xAxisLabels, dataRT, 'Wavenumber (cm⁻¹)')
#             self.view.panelPlots.on_plot_2D_data(
#                 data=[
#         dataSplit,
#         xAxisLabels,
#         'Wavenumber (cm⁻¹)',
#         yAxisLabels,
#         'Drift time (bins)',
#         self.docs.colormap])
#
#             # Update documents tree
#             self.view.panelDocuments.documents.add_document(docData=self.docs)
#
#     def on_extract_2D_from_mass_range(self, extract_type="all"):
#         """ extract multiple ions = threaded """
#
#         # self.config.extractMode = 'multipleIons'
#         tempList = self.view.panelMultipleIons.peaklist  # shortcut
#         for row in range(tempList.GetItemCount()):
#             # Extract ion name
#             itemInfo = self.view.panelMultipleIons.OnGetItemInformation(itemID=row)
#             filename = itemInfo['document']
#             # Check if the ion has been assigned a filename
#             if filename == '':
#                 self.onThreading(None, ('File name column was empty. Using the current document name instead', 4),
#                                  action='updateStatusbar')
#                 tempList.SetStringItem(index=row, col=self.config.peaklistColNames['filename'], label=self.currentDoc)
#                 filename = self.currentDoc
#             else:
#                 pass
#             document = self.documentsDict[filename]
#             # Extract information from the table
#             mzStart = itemInfo['start']
#             mzEnd = itemInfo['end']
#             label = itemInfo['label']
#             charge = itemInfo['charge']
#
#             if charge is None:
#                 charge = 'None'
#             path = document.path
#
#             # Create range name
#             rangeName = itemInfo['ionName']
#
#             # Check that the mzStart/mzEnd are above the acquire MZ value
#             if mzStart < min(document.massSpectrum['xvals']):
#                 tempList.ToggleItem(index=row)
#                 msg = "Ion: {} was below the minimum value in the mass spectrum. Consider removing it from the list.".format(
#                     rangeName)
#                 self.onThreading(None, (msg, 4), action='updateStatusbar')
#                 continue
#
#             # Check whether this ion was already extracted
#             if extract_type == 'new' and document.gotExtractedIons:
#                 try:
#                     if document.IMS2Dions[rangeName]:
#                         self.onThreading(None, ("Data was already extracted for the : {} ion".format(rangeName), 4),
#                                          action='updateStatusbar')
#                         continue
#                 except KeyError:
#                     pass
#
#             elif extract_type == 'new' and document.gotCombinedExtractedIons:
#                 try:
#                     if document.IMS2DCombIons[rangeName]:
#                         self.onThreading(None, ("Data was already extracted for the : {} ion".format(rangeName), 4),
#                                          action='updateStatusbar')
#                         continue
#                 except KeyError:
#                     pass
#
#             # Extract selected ions
#             if extract_type == 'selected' and not tempList.IsChecked(index=row):
#                 continue
#
#             msg = "Extracted: {}/{}".format((row + 1), tempList.GetItemCount())
#
#             if document.dataType == 'Type: ORIGAMI':
#                 # 1D
#                 try:
#                     extract_kwargs = {'return_data': True}
#                     __, imsData1D = io_waters.driftscope_extract_DT(path=path,
#                                                                      driftscope_path=self.config.driftscopePath,
#                                                                      mz_start=mzStart, mz_end=mzEnd,
#                                                                      **extract_kwargs)
#                 except IOError:
#                     msg = "Failed to open the file - most likely because this file no longer exists or has been moved.\n" + \
#                           "You can change the document path by right-clicking on the document in the Document Tree and \n " + \
#                           "selecting Notes, Information, Labels..."
#                     dlgBox(exceptionTitle='Missing folder',
#                            exceptionMsg=msg, type="Error")
#                     return
#                 # RT
#                 extract_kwargs = {'return_data': True, 'normalize': True}
#                 xvalsRT, rtDataY, rtDataYnorm = io_waters.driftscope_extract_RT(
#                     path=path, driftscope_path=self.config.driftscopePath, mz_start=mzStart, mz_end=mzEnd, **extract_kwargs)
#                 # 2D
#                 extract_kwargs = {'return_data': True}
#                 imsData2D = io_waters.driftscope_extract_2D(path=path,
#                                                               driftscope_path=self.config.driftscopePath,
#                                                               mz_start=mzStart, mz_end=mzEnd,
#                                                               **extract_kwargs)
#                 xlabels = 1 + np.arange(len(imsData2D[1, :]))
#                 ylabels = 1 + np.arange(len(imsData2D[:, 1]))
#                 # Update limits
#                 self.setXYlimitsRMSD2D(xlabels, ylabels)
#
#                 # Get height of the peak
#                 ms = np.transpose(np.array([document.massSpectrum['xvals'], document.massSpectrum['yvals']]))
#                 mzYMax = self.view.getYvalue(msList=ms, mzStart=mzStart, mzEnd=mzEnd)
#                 tempList.SetStringItem(row,
#                                        self.config.peaklistColNames['intensity'],
#                                        str(mzYMax))
#
#                 # Add data to document object
#                 document.gotExtractedIons = True
#                 document.IMS2Dions[rangeName] = {'zvals': imsData2D,
#                                                  'xvals': xlabels,
#                                                   'xlabels': 'Scans',
#                                                   'yvals': ylabels,
#                                                   'ylabels': 'Drift time (bins)',
#                                                   'cmap': itemInfo.get('colormap', self.config.currentCmap),
#                                                   'yvals1D': imsData1D,
#                                                   'yvalsRT': rtDataY,
#                                                   'title': label,
#                                                   'label': label,
#                                                   'charge': charge,
#                                                   'alpha': itemInfo['alpha'],
#                                                   'mask': itemInfo['mask'],
#                                                   'color': itemInfo['color'],
#                                                   'min_threshold': itemInfo['min_threshold'],
#                                                   'max_threshold': itemInfo['max_threshold'],
#                                                   'xylimits': [mzStart, mzEnd, mzYMax]}
#                 # Update document
#                 # if auto extract is enabled and the user extracts items rapidly it can
#                 # cause an issue so its a small hack to fix that
#                 try:
#                     self.OnUpdateDocument(document, 'ions', expand_item_title=rangeName)
#                 except wx.PyAssertionError:
#                     time.sleep(0.1)
#                     self.OnUpdateDocument(document, 'ions')
#
#             # Check if manual dataset
#             elif document.dataType == 'Type: MANUAL':
#                 # Shortcut to the file list
#                 nameList = self.view.panelMML.peaklist  # List with MassLynx file information
#                 # Sort data regardless of what user did
#                 self.view.panelMML.OnSortByColumn(column=1, overrideReverse=True)
#                 tempDict = {}
#                 extract_kwargs = {'return_data': True}
#                 for item in range(nameList.GetItemCount()):
#                     # Determine whether the title of the document matches the title of the item in the table
#                     # if it does not, skip the row
#                     docValue = nameList.GetItem(item, self.config.multipleMLColNames['document']).GetText()
#                     if docValue != document.title:
#                         continue
#
#                     nameValue = nameList.GetItem(item, self.config.multipleMLColNames['filename']).GetText()
#                     try:
#                         pathValue = document.multipleMassSpectrum[nameValue]['path']
#                         __, imsData1D = io_waters.driftscope_extract_DT(path=pathValue,
#                                                                          driftscope_path=self.config.driftscopePath,
#                                                                          mz_start=mzStart, mz_end=mzEnd,
#                                                                          **extract_kwargs)
# #
# #                         io_waters.driftscope_extract_DT(path=pathValue,
# #                                                          driftscope_path=self.config.driftscopePath,
# #                                                          mz_start=mzStart, mz_end=mzEnd)
#                     # if the files were moved, we can at least try to with the document path
#                     except IOError:
#                         try:
#                             pathValue = os.path.join(document.path, nameValue)
# #                             io_waters.driftscope_extract_DT(path=pathValue,
# #                                                              driftscope_path=self.config.driftscopePath,
# #                                                              mz_start=mzStart, mz_end=mzEnd)
#                             __, imsData1D = io_waters.driftscope_extract_DT(path=pathValue,
#                                                                              driftscope_path=self.config.driftscopePath,
#                                                                              mz_start=mzStart, mz_end=mzEnd,
#                                                                              **extract_kwargs)
#                             document.multipleMassSpectrum[nameValue]['path'] = pathValue
#                         except Exception:
#                             msg = "It would appear ORIGAMI cannot find the file on your disk. You can try to fix this issue\n" + \
#                                   "by updating the document path by right-clicking on the document and selecting\n" + \
#                                   "'Notes, Information, Labels...' and updating the path to where the dataset is found.\n" + \
#                                   "After that, try again and ORIGAMI will try to stitch the new document path with the file name.\n"
#                             dlgBox(exceptionTitle='Error',
#                                    exceptionMsg=msg,
#                                    type="Error")
#                             return
#
# #                     imsData1D =  io_waters.rawMassLynx_DT_load(path=pathValue)
# #                     io_waters.driftscope_extract_DT(path=pathValue,
# #                                                      driftscope_path=self.config.driftscopePath)
#                     # Get height of the peak
#                     ms = document.massSpectrum
#                     ms = np.transpose([ms['xvals'], ms['yvals']])
#                     mzYMax = self.view.getYvalue(msList=ms, mzStart=mzStart, mzEnd=mzEnd)
#                     tempList.SetStringItem(index=row,
#                                            col=self.config.peaklistColNames['intensity'],
#                                            label=str(mzYMax))
#                     tempList.SetStringItem(index=row,
#                                            col=self.config.peaklistColNames['method'],
#                                            label='Manual')
#                     # Create temporary dictionary for all IMS data
#                     tempDict[nameValue] = [imsData1D]
#                     # Add 1D data to 1D data container
#                     newName = ''.join([rangeName, ', File: ', nameValue])
#                     document.gotExtractedDriftTimes = True
#                     labelX1D = 'Drift time (bins)'
#                     xvals1D = 1 + np.arange(len(imsData1D))
#                     document.IMS1DdriftTimes[newName] = {'xvals': xvals1D,
#                                                          'yvals': imsData1D,
#                                                           'xlabels': labelX1D,
#                                                           'ylabels': 'Intensity',
#                                                           'charge': charge,
#                                                           'xylimits': [mzStart, mzEnd, mzYMax],
#                                                           'filename': nameValue}
#
#                 # Combine the contents in the dictionary - assumes they are ordered!
#                 counter = 0  # needed to start off
#                 xlabelsActual = []
#                 for item in range(nameList.GetItemCount()):
#                     # Determine whether the title of the document matches the title of the item in the table
#                     # if it does not, skip the row
#                     docValue = nameList.GetItem(item, self.config.multipleMLColNames['document']).GetText()
#                     if docValue != document.title:
#                         continue
#                     key = nameList.GetItem(item, self.config.multipleMLColNames['filename']).GetText()
#                     if counter == 0:
#                         tempArray = tempDict[key][0]
#                         xLabelLow = document.multipleMassSpectrum[key]['trap']  # first iteration so first value
#                         xlabelsActual.append(document.multipleMassSpectrum[key]['trap'])
#                         counter += 1
#                     else:
#                         imsList = tempDict[key][0]
#                         tempArray = np.concatenate((tempArray, imsList), axis=0)
#                         xlabelsActual.append(document.multipleMassSpectrum[key]['trap'])
#                         counter += 1
#
#                 # Reshape data to form a 2D array of size 200 x number of files
#                 imsData2D = None
#                 imsData2D = tempArray.reshape((200, int(counter)), order='F')
#                 # Combine 2D array into 1D
#                 rtDataY = np.sum(imsData2D, axis=0)
#                 imsData1D = np.sum(imsData2D, axis=1).T
#                 # Get the x-axis labels
#                 xLabelHigh = document.multipleMassSpectrum[key]['trap']  # after the loop has finished, so last value
#                 xlabels = np.linspace(xLabelLow, xLabelHigh, num=counter)
#                 ylabels = 1 + np.arange(len(imsData2D[:, 1]))
#                 # Update limits
#                 self.setXYlimitsRMSD2D(xlabels, ylabels)
#                 # Add data to the document
#                 document.gotCombinedExtractedIons = True
#                 document.IMS2DCombIons[rangeName] = {'zvals': imsData2D,
#                                                      'xvals': xlabels,
#                                                       'xlabels': 'Collision Voltage (V)',
#                                                       'yvals': ylabels,
#                                                       'ylabels': 'Drift time (bins)',
#                                                       'yvals1D': imsData1D,
#                                                       'yvalsRT': rtDataY,
#                                                       'cmap': document.colormap,
#                                                       'title': label,
#                                                       'label': label,
#                                                       'charge': charge,
#                                                       'alpha': itemInfo['alpha'],
#                                                       'mask': itemInfo['mask'],
#                                                       'color': itemInfo['color'],
#                                                       'min_threshold': itemInfo['min_threshold'],
#                                                       'max_threshold': itemInfo['max_threshold'],
#                                                       'xylimits': [mzStart, mzEnd, mzYMax]}
#
#                 # Update document
#                 self.OnUpdateDocument(document, 'combined_ions')
#             elif document.dataType == 'Type: Infrared':
#                 # 2D
#                 extract_kwargs = {'return_data': True}
#                 imsData2D = io_waters.driftscope_extract_2D(path=path,
#                                                               driftscope_path=self.config.driftscopePath,
#                                                               **extract_kwargs)
#
#                 dataSplit, xAxisLabels, yAxisLabels, dataRT, data1DT = pr_origami.origami_combine_infrared(
#                     inputData=imsData2D, threshold=2000, noiseLevel=500)
#
#                 # Get height of the peak
#                 ms = document.massSpectrum
#                 ms = np.transpose(np.array([ms['xvals'], ms['yvals']]))
#                 mzYMax = self.view.getYvalue(msList=ms, mzStart=mzStart, mzEnd=mzEnd)
#                 tempList.SetStringItem(index=row, col=7, label=str(mzYMax))
#                 # Add data to document object
#                 document.gotExtractedIons = True
#                 document.IMS2Dions[rangeName] = {'zvals': dataSplit,
#                                                  'xvals': xAxisLabels,
#                                                   'xlabels': 'Wavenumber (cm⁻¹)',
#                                                   'yvals': yAxisLabels,
#                                                   'ylabels': 'Drift time (bins)',
#                                                   'cmap': document.colormap,
#                                                   'yvals1D': data1DT,
#                                                   'yvalsRT': dataRT,
#                                                   'title': label,
#                                                   'label': label,
#                                                   'charge': charge,
#                                                   'alpha': itemInfo['alpha'],
#                                                   'mask': itemInfo['mask'],
#                                                   'color': itemInfo['color'],
#                                                   'min_threshold': itemInfo['min_threshold'],
#                                                   'max_threshold': itemInfo['max_threshold'],
#                                                   'xylimits': [mzStart, mzEnd, mzYMax]}
#                 # Update document
#                 self.OnUpdateDocument(document, 'ions')
#             else:
#                 return
#             self.onThreading(None, (msg, 4), action='updateStatusbar')
#
#     def on_extract_2D_from_mass_range_threaded(self, evt, extract_type="all"):
#         """
#         Extract 2D array for each m/z range specified in the table
#         """
#         if evt is None:
#             evt = extract_type
#         else:
#             evt = "all"
#
#         if not self.config.threading:
#             self.on_extract_2D_from_mass_range(evt)
#         else:
#             args = (evt)
#             self.onThreading(evt, args, action='extractIons')
#
#     def on_extract_RT_from_mzdt(self, mzStart, mzEnd, dtStart, dtEnd, units_x="m/z",
#                                 units_y="Drift time (bins)"):  # onExtractRTforMZDTrange
#         """ Function to extract RT data for specified MZ/DT region """
#
#         document = self.data_processing._on_get_document()
#
#         # convert from miliseconds to bins
#         if units_y in ["Drift time (ms)", "Arrival time (ms)"]:
#             pusherFreq = self.docs.parameters.get('pusherFreq', 1000)
#             dtStart = np.ceil(((dtStart / pusherFreq) * 1000)).astype(int)
#             dtEnd = np.ceil(((dtEnd / pusherFreq) * 1000)).astype(int)
#
#         # Load data
#         extract_kwargs = {'return_data': True, 'normalize': False}
#         rtDataX, rtDataY = io_waters.driftscope_extract_RT(path=document.path,
#                                                             driftscope_path=self.config.driftscopePath,
#                                                             mz_start=mzStart, mz_end=mzEnd,
#                                                             dt_start=dtStart, dt_end=dtEnd,
#                                                             **extract_kwargs)
#         self.view.panelPlots.on_plot_RT(rtDataX, rtDataY, 'Scans')
#
#         itemName = "Ion: {}-{} | Drift time: {}-{}".format(np.round(mzStart, 2), np.round(mzEnd),
#                                                            np.round(dtStart, 2), np.round(dtEnd))
#         document.multipleRT[itemName] = {'xvals': rtDataX,
#                                          'yvals': rtDataY,
#                                          'xlabels': 'Scans'}
#         document.gotMultipleRT = True
#
#         msg = "Extracted RT data for m/z: %s-%s | dt: %s-%s" % (mzStart, mzEnd, dtStart, dtEnd)
#         self.onThreading(None, (msg, 3), action='updateStatusbar')
#
#         # Update document
#         self.OnUpdateDocument(document, 'document')#
#     def on_extract_MS_from_mobiligram(self, dtStart=None, dtEnd=None, evt=None, units="Drift time (bins)"):
#         self.currentDoc = self.view.panelDocuments.documents.enableCurrentDocument()
#         if self.currentDoc == 'Current documents':
#             return
#         self.docs = self.documentsDict[self.currentDoc]
#
#         # convert from miliseconds to bins
#         if units in ["Drift time (ms)", "Arrival time (ms)"]:
#             pusherFreq = self.docs.parameters.get('pusherFreq', 1000)
#             dtStart = np.ceil(((dtStart / pusherFreq) * 1000)).astype(int)
#             dtEnd = np.ceil(((dtEnd / pusherFreq) * 1000)).astype(int)
#
#         # Extract data
#         extract_kwargs = {'return_data': True}
#         msX, msY = io_waters.driftscope_extract_MS(path=self.docs.path,
#                                                     driftscope_path=self.config.driftscopePath,
#                                                     dt_start=dtStart, dt_end=dtEnd,
#                                                     **extract_kwargs)
#         xlimits = [self.docs.parameters['startMS'], self.docs.parameters['endMS']]
#
#         # Add data to dictionary
#         itemName = "Drift time: {}-{}".format(dtStart, dtEnd)
#
#         self.docs.gotMultipleMS = True
#         self.docs.multipleMassSpectrum[itemName] = {'xvals': msX, 'yvals': msY,
#                                                     'range': [dtStart, dtEnd],
#                                                     'xlabels': 'm/z (Da)',
#                                                     'xlimits': xlimits}
#
#         # Plot MS
#         name_kwargs = {"document": self.docs.title, "dataset": itemName}
#         self.view.panelPlots.on_plot_MS(msX, msY, xlimits=xlimits, show_in_window="1D", **name_kwargs)
#         # Update document
#         self.OnUpdateDocument(self.docs, 'mass_spectra')
#
#     def on_extract_MS_from_chromatogram(self, startScan=None, endScan=None, units="Scans"):
#         """ Function to extract MS data for specified RT region """
#
#         document_title = self.view.panelDocuments.documents.enableCurrentDocument()
#         if document_title == 'Current documents':
#             return
#         document = self.documentsDict[document_title]
#
#         try:
#             scantime = document.parameters['scanTime']
#         except:
#             scantime = None
#
#         try:
#             xlimits = [document.parameters['startMS'], document.parameters['endMS']]
#         except Exception:
#             try:
#                 xlimits = [np.min(document.massSpectrum['xvals']), np.max(document.massSpectrum['xvals'])]
#             except:
#                 pass
#             xlimits = None
#
#         if not self.config.ms_enable_in_RT and scantime is not None:
#             if units == "Scans":
#                 rtStart = round(startScan * (scantime / 60), 2)
#                 rtEnd = round(endScan * (scantime / 60), 2)
#             elif units in ['Time (min)', 'Retention time (min)']:
#                 rtStart, rtEnd = startScan, endScan
#                 startScan = np.ceil(((startScan / scantime) * 60)).astype(int)
#                 endScan = np.ceil(((endScan / scantime) * 60)).astype(int)
#
#             # Mass spectra
#             try:
#                 extract_kwargs = {'return_data': True}
#                 msX, msY = io_waters.driftscope_extract_MS(path=document.path,
#                                                             driftscope_path=self.config.driftscopePath,
#                                                             rt_start=rtStart, rt_end=rtEnd,
#                                                             **extract_kwargs)
#                 if xlimits is None:
#                     xlimits = [np.min(msX), np.max(msX)]
#             except (IOError, ValueError):
#                 kwargs = {'auto_range': self.config.ms_auto_range,
#                           'mz_min': xlimits[0], 'mz_max': xlimits[1],
#                           'linearization_mode': self.config.ms_linearization_mode}
#                 msDict = io_waters.rawMassLynx_MS_bin(filename=str(document.path), function=1,
#                                                       startScan=startScan, endScan=endScan,
#                                                       binData=self.config.import_binOnImport,
#                                                       # override any settings as this is a accidental extraction
#                                                       mzStart=xlimits[0], mzEnd=xlimits[1],
#                                                       binsize=self.config.ms_mzBinSize,
#                                                       **kwargs)
#                 msX, msY = pr_spectra.sum_1D_dictionary(ydict=msDict)
#
#             xlimits = [np.min(msX), np.max(msX)]
#         else:
#             kwargs = {'auto_range': self.config.ms_auto_range,
#                       'mz_min': xlimits[0], 'mz_max': xlimits[1],
#                       'linearization_mode': self.config.ms_linearization_mode}
#             msDict = io_waters.rawMassLynx_MS_bin(
#                 filename=str(document.path),
#                 function=1,
#                 startScan=startScan, endScan=endScan,
#                 binData=self.config.import_binOnImport,
#                 mzStart=self.config.ms_mzStart,
#                 mzEnd=self.config.ms_mzEnd,
#                 binsize=self.config.ms_mzBinSize,
#                 **kwargs)
#
#             msX, msY = pr_spectra.sum_1D_dictionary(ydict=msDict)
#             xlimits = [np.min(msX), np.max(msX)]
#
#         # Add data to dictionary
#         itemName = "Scans: {}-{}".format(startScan, endScan)
#
#         document.gotMultipleMS = True
#         document.multipleMassSpectrum[itemName] = {'xvals': msX,
#                                                    'yvals': msY,
#                                                     'range': [startScan, endScan],
#                                                     'xlabels': 'm/z (Da)',
#                                                     'xlimits': xlimits}
#
#         self.OnUpdateDocument(document, 'mass_spectra', expand_item_title=itemName)
#         # Plot MS
#         name_kwargs = {"document": document.title, "dataset": itemName}
#         self.view.panelPlots.on_plot_MS(msX, msY, xlimits=xlimits, show_in_window="RT", **name_kwargs)
#         # Set status
#         msg = "Extracted MS data for rt: %s-%s" % (startScan, endScan)
#         self.onThreading(None, (msg, 3), action='updateStatusbar')
#
# #     def on_extract_MS_from_heatmap(self, startScan=None, endScan=None, dtStart=None,
# #                                    dtEnd=None, units_x="Scans", units_y="Drift time (bins)"):
# #         """ Function to extract MS data for specified DT/MS region """
# #
# #         document_title = self.view.panelDocuments.documents.enableCurrentDocument()
# #         if document_title == 'Current documents':
# #             return
# #         document = self.documentsDict[document_title]
# #
# #         try:
# #             scanTime = document.parameters['scanTime']
# #         except:
# #             scanTime = None
# #
# #         try:
# #             pusherFreq = document.parameters['pusherFreq']
# #         except:
# #             pusherFreq = None
# #
# #         try:
# #             xlimits = [document.parameters['startMS'], document.parameters['endMS']]
# #         except Exception:
# #             try:
# #                 xlimits = [np.min(document.massSpectrum['xvals']), np.max(document.massSpectrum['xvals'])]
# #             except:
# #                 return
# #
# #         if units_x == "Scans":
# #             if scanTime is None:
# #                 return
# #             rtStart = round(startScan * (scanTime / 60), 2)
# #             rtEnd = round(endScan * (scanTime / 60), 2)
# #         elif units_x in ['Time (min)', 'Retention time (min)']:
# #             rtStart, rtEnd = startScan, endScan
# #             if scanTime is None:
# #                 return
# #             startScan = np.ceil(((startScan / scanTime) * 60)).astype(int)
# #             endScan = np.ceil(((endScan / scanTime) * 60)).astype(int)
# #
# #         if units_y in ["Drift time (ms)", "Arrival time (ms)"]:
# #             if pusherFreq is None:
# #                 return
# #             dtStart = np.ceil(((dtStart / pusherFreq) * 1000)).astype(int)
# #             dtEnd = np.ceil(((dtEnd / pusherFreq) * 1000)).astype(int)
# #
# #         # Mass spectra
# #         try:
# #             extract_kwargs = {'return_data': True}
# #             msX, msY = io_waters.driftscope_extract_MS(path=document.path,
# #                                                         driftscope_path=self.config.driftscopePath,
# #                                                         rt_start=rtStart, rt_end=rtEnd,
# #                                                         dt_start=dtStart, dt_end=dtEnd,
# #                                                         **extract_kwargs)
# #             if xlimits is None:
# #                 xlimits = [np.min(msX), np.max(msX)]
# #         except (IOError, ValueError):
# #             return
# #
# #         # Add data to dictionary
# #         itemName = "Scans: {}-{} | Drift time: {}-{}".format(startScan, endScan,
# #                                                              dtStart, dtEnd)
# #
# #         document.gotMultipleMS = True
# #         document.multipleMassSpectrum[itemName] = {'xvals': msX,
# #                                                    'yvals': msY,
# #                                                    'range': [startScan, endScan],
# #                                                    'xlabels': 'm/z (Da)',
# #                                                    'xlimits': xlimits}
# #
# #         self.OnUpdateDocument(document, 'mass_spectra', expand_item_title=itemName)
# #         # Plot MS
# #         name_kwargs = {"document": document.title, "dataset": itemName}
# #         self.view.panelPlots.on_plot_MS(msX, msY, xlimits=xlimits, **name_kwargs)
# #         # Set status
# #         msg = "Extracted MS data for rt: %s-%s" % (startScan, endScan)
# #         self.onThreading(None, (msg, 3), action='updateStatusbar')

    def onCombineCEvoltagesMultiple(self, evt):
        # self.config.extractMode = 'multipleIons'

        # Shortcut to ion table
        tempList = self.view.panelMultipleIons.peaklist

        # Make a list of current documents
        for row in range(tempList.GetItemCount()):

            # Check which mode was selected
            if evt.GetId() == ID_combineCEscans:
                pass
            elif evt.GetId() == ID_combineCEscansSelectedIons:
                if not tempList.IsChecked(index=row):
                    continue

            self.currentDoc = tempList.GetItem(itemId=row,
                                               col=self.config.peaklistColNames['filename']).GetText()
            # Check that data was extracted first
            if self.currentDoc == '':
                msg = "Please extract data first"
                dlgBox(exceptionTitle='Extract data first',
                       exceptionMsg=msg,
                       type="Warning")
                continue
            # Get document
            self.docs = self.documentsDict[self.currentDoc]

            # Check that this data was opened in ORIGAMI mode and has extracted data
            if self.docs.dataType == 'Type: ORIGAMI' and self.docs.gotExtractedIons:
                zvals = self.docs.IMS2Dions
            else:
                msg = "Data was not extracted yet. Please extract before continuing."
                dlgBox(exceptionTitle='Missing data',
                       exceptionMsg=msg,
                       type="Error")
                continue

            # Extract ion name
            itemInfo = self.view.panelMultipleIons.OnGetItemInformation(itemID=row)
            selectedItem = itemInfo['ionName']

        # Combine data
        # LINEAR METHOD
            if self.config.origami_acquisition == 'Linear':
                # Check that the user filled in appropriate parameters
                if ((evt.GetId() == ID_recalculateORIGAMI or self.config.useInternalParamsCombine)
                        and self.docs.gotCombinedExtractedIons):
                    try:
                        self.config.origami_startScan = self.docs.IMS2DCombIons[selectedItem]['parameters']['firstVoltage']
                        self.config.origami_startVoltage = self.docs.IMS2DCombIons[selectedItem]['parameters']['startV']
                        self.config.origami_endVoltage = self.docs.IMS2DCombIons[selectedItem]['parameters']['endV']
                        self.config.origami_stepVoltage = self.docs.IMS2DCombIons[selectedItem]['parameters']['stepV']
                        self.config.origami_spv = self.docs.IMS2DCombIons[selectedItem]['parameters']['spv']
                    except Exception:
                        pass
                # Ensure that config is not missing variabels
                elif not any([self.config.origami_startScan, self.config.origami_startVoltage, self.config.origami_endVoltage,
                              self.config.origami_stepVoltage, self.config.origami_spv]):
                    msg = 'Cannot perform action. Missing fields in the ORIGAMI parameters panel'
                    self.onThreading(None, (msg, 3), action='updateStatusbar')
                    return

                # Check if ion/file has specified ORIGAMI method
                if itemInfo['method'] == '':
                    tempList.SetStringItem(index=row, col=self.config.peaklistColNames['method'],
                                           label=self.config.origami_acquisition)
                elif (itemInfo['method'] == self.config.origami_acquisition and self.config.overrideCombine):
                    pass
                # Check if using internal parameters and item is checked
                elif self.config.useInternalParamsCombine and tempList.IsChecked(index=row):
                    pass
                else:
                    continue
                # Combine data
                imsData2D, scanList, parameters = pr_origami.origami_combine_linear(imsDataInput=zvals[selectedItem]['zvals'],
                                                                                    firstVoltage=self.config.origami_startScan,
                                                                                    startVoltage=self.config.origami_startVoltage,
                                                                                    endVoltage=self.config.origami_endVoltage,
                                                                                    stepVoltage=self.config.origami_stepVoltage,
                                                                                    scansPerVoltage=self.config.origami_spv)
            # EXPONENTIAL METHOD
            elif self.config.origami_acquisition == 'Exponential':
                # Check that the user filled in appropriate parameters
                if ((evt.GetId() == ID_recalculateORIGAMI or self.config.useInternalParamsCombine)
                        and self.docs.gotCombinedExtractedIons):
                    try:
                        self.config.origami_startScan = self.docs.IMS2DCombIons[selectedItem]['parameters']['firstVoltage']
                        self.config.origami_startVoltage = self.docs.IMS2DCombIons[selectedItem]['parameters']['startV']
                        self.config.origami_endVoltage = self.docs.IMS2DCombIons[selectedItem]['parameters']['endV']
                        self.config.origami_stepVoltage = self.docs.IMS2DCombIons[selectedItem]['parameters']['stepV']
                        self.config.origami_spv = self.docs.IMS2DCombIons[selectedItem]['parameters']['spv']
                        self.config.origami_exponentialIncrement = self.docs.IMS2DCombIons[
                            selectedItem]['parameters']['expIncrement']
                        self.config.origami_exponentialPercentage = self.docs.IMS2DCombIons[
                            selectedItem]['parameters']['expPercent']
                    except Exception:
                        pass
                # Ensure that config is not missing variabels
                elif not any([self.config.origami_startScan, self.config.origami_startVoltage, self.config.origami_endVoltage,
                              self.config.origami_stepVoltage, self.config.origami_spv, self.config.origami_exponentialIncrement,
                              self.config.origami_exponentialPercentage]):
                    msg = 'Cannot perform action. Missing fields in the ORIGAMI parameters panel'
                    self.onThreading(None, (msg, 3), action='updateStatusbar')
                    return

                # Check if ion/file has specified ORIGAMI method
                if itemInfo['method'] == '':
                    tempList.SetStringItem(index=row, col=self.config.peaklistColNames['method'],
                                           label=self.config.origami_acquisition)
                elif (itemInfo['method'] == self.config.origami_acquisition and
                      self.config.overrideCombine):
                    pass
                # Check if using internal parameters and item is checked
                elif self.config.useInternalParamsCombine and tempList.IsChecked(index=row):
                    pass
                else:
                    continue  # skip
                imsData2D, scanList, parameters = pr_origami.origami_combine_exponential(imsDataInput=zvals[selectedItem]['zvals'],
                                                                                         firstVoltage=self.config.origami_startScan,
                                                                                         startVoltage=self.config.origami_startVoltage,
                                                                                         endVoltage=self.config.origami_endVoltage,
                                                                                         stepVoltage=self.config.origami_stepVoltage,
                                                                                         scansPerVoltage=self.config.origami_spv,
                                                                                         expIncrement=self.config.origami_exponentialIncrement,
                                                                                         expPercentage=self.config.origami_exponentialPercentage)
            # FITTED/BOLTZMANN METHOD
            elif self.config.origami_acquisition == 'Fitted':
                # Check that the user filled in appropriate parameters
                if ((evt.GetId() == ID_recalculateORIGAMI or self.config.useInternalParamsCombine)
                        and self.docs.gotCombinedExtractedIons):
                    try:
                        self.config.origami_startScan = self.docs.IMS2DCombIons[selectedItem]['parameters']['firstVoltage']
                        self.config.origami_startVoltage = self.docs.IMS2DCombIons[selectedItem]['parameters']['startV']
                        self.config.origami_endVoltage = self.docs.IMS2DCombIons[selectedItem]['parameters']['endV']
                        self.config.origami_stepVoltage = self.docs.IMS2DCombIons[selectedItem]['parameters']['stepV']
                        self.config.origami_spv = self.docs.IMS2DCombIons[selectedItem]['parameters']['spv']
                        self.config.origami_boltzmannOffset = self.docs.IMS2DCombIons[selectedItem]['parameters']['dx']
                    except Exception:
                        pass
                # Ensure that config is not missing variabels
                elif not any([self.config.origami_startScan, self.config.origami_startVoltage, self.config.origami_endVoltage,
                              self.config.origami_stepVoltage, self.config .scansPerVoltage, self.config.origami_boltzmannOffset]):
                    msg = 'Cannot perform action. Missing fields in the ORIGAMI parameters panel'
                    self.onThreading(None, (msg, 3), action='updateStatusbar')
                    return

                # Check if ion/file has specified ORIGAMI method
                if itemInfo['method'] == '':
                    tempList.SetStringItem(index=row, col=self.config.peaklistColNames['method'],
                                           label=self.config.origami_acquisition)
                elif (itemInfo['method'] == self.config.origami_acquisition and
                      self.config.overrideCombine):
                    pass
                # Check if using internal parameters and item is checked
                elif self.config.useInternalParamsCombine and tempList.IsChecked(index=row):
                    pass
                else:
                    continue  # skip
                imsData2D, scanList, parameters = pr_origami.origami_combine_boltzmann(imsDataInput=zvals[selectedItem]['zvals'],
                                                                                       firstVoltage=self.config.origami_startScan,
                                                                                       startVoltage=self.config.origami_startVoltage,
                                                                                       endVoltage=self.config.origami_endVoltage,
                                                                                       stepVoltage=self.config.origami_stepVoltage,
                                                                                       scansPerVoltage=self.config.origami_spv,
                                                                                       dx=self.config.origami_boltzmannOffset)
            # USER-DEFINED/LIST METHOD
            elif self.config.origami_acquisition == 'User-defined':
                print((self.config.origamiList, self.config.origami_startScan))
                errorMsg = None
                # Check that the user filled in appropriate parameters
                if evt.GetId() == ID_recalculateORIGAMI or self.config.useInternalParamsCombine:
                    try:
                        self.config.origami_startScan = self.docs.IMS2DCombIons[selectedItem]['parameters']['firstVoltage']
                        self.config.origamiList = self.docs.IMS2DCombIons[selectedItem]['parameters']['inputList']
                    except Exception:
                        pass
                # Ensure that config is not missing variabels
                elif len(self.config.origamiList) == 0:
                    errorMsg = "Please load a text file with ORIGAMI parameters"
                elif not self.config.origami_startScan:
                    errorMsg = "The first scan is incorect (currently: %s)" % self.config.origami_startScan
                elif self.config.origamiList[:, 0].shape != self.config.origamiList[:, 1].shape:
                    errorMsg = "The collision voltage list is of incorrect shape."

                if errorMsg is not None:
                    self.onThreading(None, (errorMsg, 3), action='updateStatusbar')
                    return

                # Check if ion/file has specified ORIGAMI method
                if itemInfo['method'] == '':
                    tempList.SetStringItem(index=row, col=self.config.peaklistColNames['method'],
                                           label=self.config.origami_acquisition)
                elif (itemInfo['method'] == self.config.origami_acquisition and
                      self.config.overrideCombine):
                    pass
                # Check if using internal parameters and item is checked
                elif self.config.useInternalParamsCombine and tempList.IsChecked(index=row):
                    pass
                else:
                    continue  # skip
                imsData2D, xlabels, scanList, parameters = pr_origami.origami_combine_userDefined(
    imsDataInput=zvals[selectedItem]['zvals'], firstVoltage=self.config.origami_startScan, inputList=self.config.origamiList)

            if imsData2D[0] is None:
                msg = "With your current input, there would be too many scans in your file! " + \
                      "There are %s scans in your file and your settings suggest there should be %s" \
                      % (imsData2D[2], imsData2D[1])
                dlgBox(exceptionTitle='Are your settings correct?',
                       exceptionMsg=msg, type="Warning")
                continue

            # Add x-axis and y-axis labels
            if self.config.origami_acquisition != 'User-defined':
                xlabels = np.arange(self.config.origami_startVoltage,
                                    (self.config.origami_endVoltage + self.config.origami_stepVoltage),
                                    self.config.origami_stepVoltage)

            # Y-axis is bins by default
            ylabels = np.arange(1, 201, 1)
            # Combine 2D array into 1D
            imsData1D = np.sum(imsData2D, axis=1).T
            yvalsRT = np.sum(imsData2D, axis=0)
            # Check if item has labels, alpha, charge
            charge = zvals[selectedItem].get('charge', None)
            cmap = zvals[selectedItem].get('cmap', self.config.overlay_cmaps[randomIntegerGenerator(0, 5)])
            color = zvals[selectedItem].get('color', self.config.customColors[randomIntegerGenerator(0, 15)])
            label = zvals[selectedItem].get('label', None)
            alpha = zvals[selectedItem].get('alpha', self.config.overlay_defaultAlpha)
            mask = zvals[selectedItem].get('mask', self.config.overlay_defaultMask)
            min_threshold = zvals[selectedItem].get('min_threshold', 0)
            max_threshold = zvals[selectedItem].get('max_threshold', 1)

            # Add 2D data to document object
            self.docs.gotCombinedExtractedIons = True
            self.docs.IMS2DCombIons[selectedItem] = {'zvals': imsData2D,
                                                     'xvals': xlabels,
                                                     'xlabels': 'Collision Voltage (V)',
                                                     'yvals': ylabels,
                                                     'ylabels': 'Drift time (bins)',
                                                     'yvals1D': imsData1D,
                                                     'yvalsRT': yvalsRT,
                                                     'cmap': cmap,
                                                     'xylimits': zvals[selectedItem]['xylimits'],
                                                     'charge': charge,
                                                     'label': label,
                                                     'alpha': alpha,
                                                     'mask': mask,
                                                     'color': color,
                                                     'min_threshold': min_threshold,
                                                     'max_threshold': max_threshold,
                                                     'scanList': scanList,
                                                     'parameters': parameters}
            self.docs.combineIonsList = scanList
            # Add 1D data to document object
            self.docs.gotCombinedExtractedIonsRT = True
            self.docs.IMSRTCombIons[selectedItem] = {'xvals': xlabels,
                                                     'yvals': np.sum(imsData2D, axis=0),
                                                     'xlabels': 'Collision Voltage (V)'}

            # Update document
            self.OnUpdateDocument(self.docs, 'combined_ions')

    def onExtractMSforEachCollVoltage(self, evt):
        """
        This function extracts 'binned' msX and msY values for each collision
        voltage. The values are extracted for each scan range for particular
        CV, binned and then summed together. These are then stored in the
        document dictionary
        """
        document_title = self.view.panelDocuments.documents.enableCurrentDocument()
        if document_title == 'Current documents':
            return
        document = self.documentsDict[document_title]

        # Make sure the document is of correct type.
        if not document.dataType == 'Type: ORIGAMI':
            self.onThreading(None, ('Please select correct document type - ORIGAMI', 3), action='updateStatusbar')
            return
        # Check that the user combined scans already
        if not document.gotCombinedExtractedIons:
            self.onThreading(None, ('Please combine collision voltages first', 3), action='updateStatusbar')
            return
        # Check that appropriate values were filled in
        if (self.config.ms_mzStart is None or self.config.ms_mzEnd is None
                or self.config.binCVdata == None):
            self.onThreading(
                None,
                ('Please fill in appopriate fields: MS start, MS end and MS bin size',
     3),
                action='updateStatusbar')
            return

        try:
            scantime = self.docs.parameters['scanTime']
        except Exception:
            scantime = None

        # Do actual work
        splitlist = document.combineIonsList
#         msList = []
        msFilenames = ["m/z"]
        document.gotMultipleMS = True

        xlimits = [document.parameters['startMS'], document.parameters['endMS']]
        kwargs = {'auto_range': self.config.ms_auto_range,
                  'mz_min': xlimits[0], 'mz_max': xlimits[1],
                  'linearization_mode': self.config.ms_linearization_mode}

        for counter, item in enumerate(splitlist):
            itemName = "Scans: %s-%s | CV: %s V" % (item[0], item[1], item[2])
            if self.config.binCVdata or scantime is None:
                msDict = io_waters.rawMassLynx_MS_bin(filename=str(document.path),
                                                      function=1,
                                                      startScan=item[0], endScan=item[1],
                                                      binData=self.config.import_binOnImport,
                                                      mzStart=self.config.ms_mzStart,
                                                      mzEnd=self.config.ms_mzEnd,
                                                      binsize=self.config.ms_mzBinSize,
                                                      **kwargs)
                msX, msY = pr_spectra.sum_1D_dictionary(ydict=msDict)
                xlimits = [self.config.ms_mzStart, self.config.ms_mzEnd]
            elif not self.config.binCVdata and scantime is not None:
                # Mass spectra
                rtStart = round(item[0] * (scantime / 60), 2)
                rtEnd = round(item[1] * (scantime / 60), 2)
                extract_kwargs = {'return_data': True}
                msX, msY = io_waters.driftscope_extract_MS(path=document.path,
                                                            driftscope_path=self.config.driftscopePath,
                                                            rt_start=rtStart, rt_end=rtEnd,
                                                            **extract_kwargs)
                xlimits = [document.parameters['startMS'], document.parameters['endMS']]
            # Add data to document
            document.multipleMassSpectrum[itemName] = {'trap': item[2],
                                                       'xvals': msX,
                                                        'yvals': msY,
                                                        'xlabels': 'm/z (Da)',
                                                        'xlimits': xlimits}
            msFilenames.append(str(item[2]))
            if counter == 0:
                tempArray = msY
            else:
                tempArray = np.concatenate((tempArray, msY), axis=0)
        # Form pandas dataframe
        combMSOut = np.concatenate((msX, tempArray), axis=0)
        combMSOut = combMSOut.reshape((len(msY), int(counter + 2)), order='F')

        msSaveData = pd.DataFrame(data=combMSOut, columns=msFilenames)
        document.gotMSSaveData = True
        document.massSpectraSave = msSaveData  # pandas dataframe that can be exported as csv

        # Update document
        self.OnUpdateDocument(document, 'mass_spectra')

    def onExtract2DimsOverMZrange(self, e):
        self.currentDoc = self.view.panelDocuments.documents.enableCurrentDocument()
        if self.currentDoc == 'Current documents':
            return
        self.docs = self.documentsDict[self.currentDoc]
        dataType = self.docs.dataType
        path = self.docs.path
        mzStart = str2num(self.config.mzStart)
        mzEnd = str2num(self.config.mzEnd)
        if isempty(path) or isempty(mzStart) or isempty(mzEnd):
            self.onThreading(None, ('Please enter correct mass range', 3), action='updateStatusbar')
            return
        if mzEnd < mzStart:
            mzEnd_copy = mzStart
            mzStart = mzEnd
            mzEnd = mzEnd_copy
            self.config.mzStart = mzStart
            self.config.mzEnd = mzEnd
#             self.view.panelControls.onUpdateParams()
        else:
            tstart = time.clock()
            # Add to table and show the window
            # Check if this data is already present - if so it stops here
            outcome = self.view.Add2Table(xvalsMin=mzStart, xvalsMax=mzEnd, yvalsMax=0,
                                          currentView='MS', currentDoc=self.currentDoc)
            if outcome:
                return
            # 1D IMMS
            extract_kwargs = {'return_data': True}
            __, imsData1D = io_waters.driftscope_extract_DT(path=path,
                                                             driftscope_path=self.config.driftscopePath,
                                                             mz_start=mzStart, mz_end=mzEnd,
                                                             **extract_kwargs)

            # RT
            extract_kwargs = {'return_data': True, 'normalize': True}
            rtDataX, rtDataY, rtDataYnorm = io_waters.driftscope_extract_RT(path=path,
                                                                             driftscope_path=self.config.driftscopePath,
                                                                             mz_start=mzStart, mz_end=mzEnd,
                                                                             **extract_kwargs)

            # 2D IMMS
            extract_kwargs = {'return_data': True}
            imsData2D = io_waters.driftscope_extract_2D(path=path,
                                                          driftscope_path=self.config.driftscopePath,
                                                          mz_start=mzStart, mz_end=mzEnd,
                                                          **extract_kwargs)
            xlabels = 1 + np.arange(len(imsData2D[1, :]))
            ylabels = 1 + np.arange(len(imsData2D[:, 1]))

            imsData1D = np.sum(imsData2D, axis=1).T  # 'yvals1D':imsData1D,
            self.view.panelPlots.on_plot_2D_data(
                data=[
        imsData2D,
        xlabels,
        'Scans',
        ylabels,
        'Drift time (bins)',
        self.docs.colormap])
            tend = time.clock()
            self.onThreading(None, ('Total time to extract ion: %.2gs' % (tend - tstart), 3), action='updateStatusbar')

            # Update limits
            self.setXYlimitsRMSD2D(xlabels, ylabels)
            # Add data to document object
            self.docs.gotExtractedIons = True
            rangeName = ''.join([str(mzStart), '-', str(mzEnd)])
            self.docs.currentExtractRange = rangeName
            self.docs.IMS2Dions[rangeName] = {'zvals': imsData2D,
                                              'xvals': xlabels,
                                               'xlabels': 'Scans',
                                               'yvals': ylabels,
                                               'yvals1D': imsData1D,
                                               'yvalsRT': rtDataY,
                                               'ylabels': 'Drift time (bins)',
                                               'cmap': self.docs.colormap,
                                               'charge': "None"}

        # Update document
        self.OnUpdateDocument(self.docs, 'ions')

    def get_overlay_document(self):
        try:
            self.currentDoc = self.view.panelDocuments.documents.enableCurrentDocument()
        except Exception:
            return
        if self.currentDoc == "Current documents":
            return

        # Check if current document is a comparison document
        # If so, it will be used
        if self.documentsDict[self.currentDoc].dataType == 'Type: Comparison':
            document = self.documentsDict[self.currentDoc]
            self.onThreading(
                None,
                ('Using document: ' +
     document.title.encode(
        'ascii',
        'replace'),
        4),
                action='updateStatusbar')
        else:
            docList = self.checkIfAnyDocumentsAreOfType(type='Type: Comparison')
            if len(docList) == 0:
                print('Did not find appropriate document.')
                dlg = wx.FileDialog(self.view, "Please select a name for the comparison document",
                                    "", "", "", wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
                if dlg.ShowModal() == wx.ID_OK:
                    path, idName = os.path.split(dlg.GetPath())
                else:
                    return
                # Create document
                document = documents()
                document.title = idName
                document.path = path
                document.userParameters = self.config.userParameters
                document.userParameters['date'] = getTime()
                document.dataType = 'Type: Comparison'
                document.fileFormat = 'Format: ORIGAMI'
            else:
                self.selectDocDlg = panelSelectDocument(self.view, self, docList)
                if self.selectDocDlg.ShowModal() == wx.ID_OK:
                    pass

                # Check that document exists
                if self.currentDoc is None:
                    self.onThreading(None, ('Please select comparison document', 4), action='updateStatusbar')
                    return
                document = self.documentsDict[self.currentDoc]
                self.onThreading(
                    None,
                    ('Using document: ' +
     document.title.encode(
        'ascii',
        'replace'),
        4),
                    action='updateStatusbar')

        return document

    def on_overlay_1D(self, source, plot_type):
        """
        This function enables overlaying of multiple ions together - 1D and RT
        """
        # Check what is the ID
        if source == "ion":
            tempList = self.view.panelMultipleIons.peaklist
            add_data_to_document = self.view.panelMultipleIons.addToDocument
            normalize_dataset = self.view.panelMultipleIons.normalize1D
        elif source == "text":
            tempList = self.view.panelMultipleText.peaklist
            add_data_to_document = self.view.panelMultipleText.addToDocument
            normalize_dataset = self.view.panelMultipleText.normalize1D

        try:
            self.currentDoc = self.view.panelDocuments.documents.enableCurrentDocument()
        except:
            return
        if self.currentDoc == "Current documents":
            return

        # Check if current document is a comparison document
        # If so, it will be used
        if add_data_to_document:
            if self.documentsDict[self.currentDoc].dataType == 'Type: Comparison':
                self.docs = self.documentsDict[self.currentDoc]
                self.onThreading(
                    None,
                    ('Using document: ' +
     self.docs.title.encode(
        'ascii',
        'replace'),
        4),
                    action='updateStatusbar')
            else:
                docList = self.checkIfAnyDocumentsAreOfType(type='Type: Comparison')
                if len(docList) == 0:
                    dlg = wx.FileDialog(self.view, "Please select a name for the comparison document",
                                        "", "", "", wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
                    if dlg.ShowModal() == wx.ID_OK:
                        path, idName = os.path.split(dlg.GetPath())
                    else:
                        return
                    # Create document
                    self.docs = documents()
                    self.docs.title = idName
                    self.docs.path = path
                    self.docs.userParameters = self.config.userParameters
                    self.docs.userParameters['date'] = getTime()
                    self.docs.dataType = 'Type: Comparison'
                    self.docs.fileFormat = 'Format: ORIGAMI'
                else:
                    self.selectDocDlg = panelSelectDocument(self.view, self, docList)
                    if self.selectDocDlg.ShowModal() == wx.ID_OK:
                        pass

                    # Check that document exists
                    if self.currentDoc is None:
                        self.onThreading(None, ('Please select comparison document', 4), action='updateStatusbar')
                        return
                    self.docs = self.documentsDict[self.currentDoc]
                    self.onThreading(
                        None,
                        ('Using document: ' +
     self.docs.title.encode(
        'ascii',
        'replace'),
        4),
                        action='updateStatusbar')

        # Empty lists
        xlist, ylist, colorlist, legend = [], [], [], []
        idName = ""
        # Get data for the dataset
        for row in range(tempList.GetItemCount()):
            if tempList.IsChecked(index=row):
                if source == "ion":
                    # Get current document
                    itemInfo = self.view.panelMultipleIons.OnGetItemInformation(itemID=row)
                    self.currentDoc = itemInfo['document']
                    # Check that data was extracted first
                    if self.currentDoc == '':
                        self.onThreading(None, ('Please extract data first', 3), action='updateStatusbar')
                        continue
                    document = self.documentsDict[self.currentDoc]
                    dataType = document.dataType
                    selectedItem = itemInfo['ionName']
                    label = itemInfo['label']
                    color = convertRGB255to1(itemInfo['color'])
                    itemName = "ion=%s (%s)" % (selectedItem, self.currentDoc)

                    # ORIGAMI dataset
                    if dataType == 'Type: ORIGAMI' and document.gotCombinedExtractedIons:
                        try:
                            data = document.IMS2DCombIons[selectedItem]
                        except KeyError:
                            try:
                                data = document.IMS2Dions[selectedItem]
                            except KeyError:
                                continue
                    elif dataType == 'Type: ORIGAMI' and not document.gotCombinedExtractedIons:
                        try:
                            data = document.IMS2Dions[selectedItem]
                        except KeyError:
                            continue

                    # MANUAL dataset
                    if dataType == 'Type: MANUAL' and document.gotCombinedExtractedIons:
                        try:
                            data = document.IMS2DCombIons[selectedItem]
                        except KeyError:
                            try:
                                data = document.IMS2Dions[selectedItem]
                            except KeyError:
                                continue

                    # Add new label
                    if idName == "":
                        idName = itemName
                    else:
                        idName = "%s, %s" % (idName, itemName)

                    # Add depending which event was triggered
                    if plot_type == "mobiligram":
                        xvals = data['yvals']  # normally this would be the y-axis
                        yvals = data['yvals1D']
                        if normalize_dataset:
                            yvals = pr_spectra.smooth_gaussian_1D(data=yvals, sigma=self.config.overlay_smooth1DRT)
                            yvals = pr_spectra.normalize_1D(inputData=yvals)
                        xlabels = data['ylabels']  # data was rotated so using ylabel for xlabel

                    elif plot_type == "chromatogram":
                        xvals = data['xvals']
                        yvals = data['yvalsRT']
                        if normalize_dataset:
                            yvals = pr_spectra.smooth_gaussian_1D(data=yvals, sigma=self.config.overlay_smooth1DRT)
                            yvals = pr_spectra.normalize_1D(inputData=yvals)
                        xlabels = data['xlabels']

                    # Append data to list
                    xlist.append(xvals)
                    ylist.append(yvals)
                    colorlist.append(color)
                    if label == "":
                        label = selectedItem
                    legend.append(label)
                elif source == "text":
                    __, __, charge, color, colormap, alpha, mask, __, \
                        label, filename, min_threshold, max_threshold \
 = self.view.panelMultipleText.OnGetItemInformation(itemID=row, return_list=True)
                    # get document
                    try:
                        document = self.documentsDict[filename]
                        comparison_flag = False
                        selectedItem = filename
                        itemName = "file=%s" % filename
                    except Exception:
                        comparison_flag = True
                        filename, ion_name = re.split(': ', filename)
                        document = self.documentsDict[filename]
                        selectedItem = ion_name
                        itemName = "file=%s" % ion_name

                    color = convertRGB255to1(color)

                    # Text dataset
                    if comparison_flag:
                        try:
                            data = document.IMS2DcompData[ion_name]
                        except Exception:
                            data = document.IMS2Dions[ion_name]
                    else:
                        try:
                            data = document.IMS2D
                        except Exception:
                            self.onThreading(None, ('No data for selected file', 3), action='updateStatusbar')
                            continue

                    # Add new label
                    if idName == "":
                        idName = itemName
                    else:
                        idName = "%s, %s" % (idName, itemName)

                    # Add depending which event was triggered
                    if plot_type == "mobiligram":
                        xvals = data['yvals']  # normally this would be the y-axis
                        try:
                            yvals = data['yvals1D']
                        except KeyError:
                            yvals = np.sum(data['zvals'], axis=1).T
                        if normalize_dataset:
                            yvals = pr_spectra.smooth_gaussian_1D(data=yvals, sigma=self.config.overlay_smooth1DRT)
                            yvals = pr_spectra.normalize_1D(inputData=yvals)
                        xlabels = data['ylabels']  # data was rotated so using ylabel for xlabel

                    elif plot_type == "chromatogram":
                        xvals = data['xvals']
                        try:
                            yvals = data['yvalsRT']
                        except KeyError:
                            yvals = np.sum(data['zvals'], axis=0)
                        if normalize_dataset:
                            yvals = pr_spectra.smooth_gaussian_1D(data=yvals, sigma=self.config.overlay_smooth1DRT)
                            yvals = pr_spectra.normalize_1D(inputData=yvals)
                        xlabels = data['xlabels']

                    # Append data to list
                    xlist.append(xvals)
                    ylist.append(yvals)
                    colorlist.append(color)
                    if label == "":
                        label = selectedItem
                    legend.append(label)

        # Modify the name to include ion tags
        if plot_type == "mobiligram":
            idName = "1D: %s" % idName
        elif plot_type == "chromatogram":
            idName = "RT: %s" % idName

        # remove unnecessary file extensions from filename
        if len(idName) > 511:
            self.onThreading(None, ("Filename is too long. Reducing...", 4), action='updateStatusbar')
            idName = idName.replace(".csv", "").replace(".txt", "").replace(".raw", "").replace(".d", "")
            idName = idName[:500]

        # Determine x-axis limits for the zoom function
        try:
            xlimits = [min(xvals), max(xvals)]
        except UnboundLocalError:
            self.onThreading(None, ("Please select at least one item in the table.", 4), action='updateStatusbar')
            return
        # Add data to dictionary
        if add_data_to_document:
            self.docs.gotOverlay = True
            self.docs.IMS2DoverlayData[idName] = {'xvals': xlist,
                                                  'yvals': ylist,
                                                  'xlabel': xlabels,
                                                  'colors': colorlist,
                                                  'xlimits': xlimits,
                                                  'labels': legend
                                                  }
            self.currentDoc = self.docs.title
            self.OnUpdateDocument(self.docs, 'comparison_data')

        # Plot
        if plot_type == "mobiligram":
            self.view.panelPlots.on_plot_overlay_DT(xvals=xlist, yvals=ylist, xlabel=xlabels, colors=colorlist,
                                                    xlimits=xlimits, labels=legend, set_page=True)
        elif plot_type == "chromatogram":
            self.view.panelPlots.on_plot_overlay_RT(xvals=xlist, yvals=ylist, xlabel=xlabels, colors=colorlist,
                                                    xlimits=xlimits, labels=legend, set_page=True)

    def on_overlay_2D(self, source):
        """
        This function enables overlaying multiple ions from the same CIU datasets together
        """
        # Check what is the ID
        if source == "ion":
            tempList = self.view.panelMultipleIons.peaklist
            col_order = self.config.peaklistColNames
            add_data_to_document = self.view.panelMultipleIons.addToDocument
            self.config.overlayMethod = self.view.panelMultipleIons.combo.GetStringSelection()
        elif source == "text":
            tempList = self.view.panelMultipleText.peaklist
            col_order = self.config.textlistColNames
            add_data_to_document = self.view.panelMultipleText.addToDocument
            self.config.overlayMethod = self.view.panelMultipleText.combo.GetStringSelection()

        tempAccumulator = 0  # Keeps count of how many items are ticked
        try:
            self.currentDoc = self.view.panelDocuments.documents.enableCurrentDocument()
        except Exception:
            return
        if self.currentDoc == "Current documents":
            return

        # Check if current document is a comparison document
        # If so, it will be used
        if add_data_to_document:
            if self.documentsDict[self.currentDoc].dataType == 'Type: Comparison':
                self.docs = self.documentsDict[self.currentDoc]
                self.onThreading(
                    None,
                    ('Using document: ' +
     self.docs.title.encode(
        'ascii',
        'replace'),
        4),
                    action='updateStatusbar')
                if self.docs.gotComparisonData:
                    compDict = self.docs.IMS2DcompData
                    compList = []
                    for key in self.docs.IMS2DcompData:
                        compList.append(key)
                else:
                    compDict, compList = {}, []
            else:
                self.onThreading(None, ("Checking if there is a comparison document", 4), action='updateStatusbar')
                docList = self.checkIfAnyDocumentsAreOfType(type='Type: Comparison')
                if len(docList) == 0:
                    self.onThreading(
                        None, ("Did not find appropriate document. Creating a new one", 4), action='updateStatusbar')
                    dlg = wx.FileDialog(self.view, "Please select a name for the comparison document",
                                        "", "", "", wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
                    if dlg.ShowModal() == wx.ID_OK:
                        path, idName = os.path.split(dlg.GetPath())
                    else:
                        return

                    # Create document
                    self.docs = documents()
                    self.docs.title = idName
                    self.docs.path = path
                    self.docs.userParameters = self.config.userParameters
                    self.docs.userParameters['date'] = getTime()
                    self.docs.dataType = 'Type: Comparison'
                    self.docs.fileFormat = 'Format: ORIGAMI'
                    # Initiate empty list and dictionary
                    compDict, compList = {}, []
                else:
                    self.selectDocDlg = panelSelectDocument(self.view, self, docList)
                    if self.selectDocDlg.ShowModal() == wx.ID_OK:
                        pass

                    # Check that document exists
                    if self.currentDoc is None:
                        msg = 'Please select comparison document'
                        self.onThreading(None, (msg, 4), action='updateStatusbar')
                        return

                    self.docs = self.documentsDict[self.currentDoc]
                    self.onThreading(
                        None,
                        ('Using document: ' +
     self.docs.title.encode(
        'ascii',
        'replace'),
        4),
                        action='updateStatusbar')
                    if self.docs.gotComparisonData:
                        compDict = self.docs.IMS2DcompData
                        compList = []
                        for key in self.docs.IMS2DcompData:
                            compList.append(key)
                    else:
                        compDict, compList = {}, []
        else:
            compDict, compList = {}, []

        comparisonFlag = False
        # Get data for the dataset
        for row in range(tempList.GetItemCount()):
            if tempList.IsChecked(index=row):
                if source == "ion":
                    # Get data for each ion
                    __, __, charge, color, colormap, alpha, mask, label, \
                        self.currentDoc, ionName, min_threshold, max_threshold \
 = self.view.panelMultipleIons.OnGetItemInformation(itemID=row, return_list=True)

                    # processed name
                    ionNameProcessed = "%s (processed)" % ionName

                    # Check that data was extracted first
                    if self.currentDoc == '':
                        msg = 'Please extract data first'
                        self.onThreading(None, (msg, 4), action='updateStatusbar')
                        continue
                    document = self.documentsDict[self.currentDoc]
                    dataType = document.dataType

                    # ORIGAMI dataset
                    if dataType in ['Type: ORIGAMI', 'Type: MANUAL'] and document.gotCombinedExtractedIons:
                        if self.config.overlay_usedProcessed:
                            try:
                                dataIn = document.IMS2DCombIons[ionNameProcessed]
                            except KeyError:
                                try:
                                    dataIn = document.IMS2DCombIons[ionName]
                                except KeyError:
                                    try:
                                        dataIn = document.IMS2Dions[ionNameProcessed]
                                    except KeyError:
                                        try:
                                            dataIn = document.IMS2Dions[ionName]
                                        except KeyError:
                                            continue
                        else:
                            try:
                                dataIn = document.IMS2DCombIons[ionName]
                            except KeyError:
                                try:
                                    dataIn = document.IMS2Dions[ionName]
                                except KeyError:
                                    continue
                    elif dataType in ['Type: ORIGAMI', 'Type: MANUAL'] and not document.gotCombinedExtractedIons:
                        if self.config.overlay_usedProcessed:
                            try:
                                dataIn = document.IMS2Dions[ionNameProcessed]
                            except KeyError:
                                try:
                                    dataIn = document.IMS2Dions[ionName]
                                except KeyError:
                                    continue
                        else:
                            try:
                                dataIn = document.IMS2Dions[ionName]
                            except KeyError:
                                continue

#                     # MANUAL dataset
#                     if dataType == 'Type: MANUAL' and document.gotCombinedExtractedIons:
#                         try: tempData = document.IMS2DCombIons
#                         except KeyError:
#                             try: tempData = document.IMS2Dions
#                             except KeyError: continue

                    # INFRARED dataset
                    if dataType == 'Type: Infrared' and document.gotCombinedExtractedIons:
                        try:
                            dataIn = document.IMS2DCombIons
                        except KeyError:
                            try:
                                dataIn = document.IMS2Dions
                            except KeyError:
                                continue
                    tempAccumulator = tempAccumulator + 1

                    selectedItemUnique = "ion=%s (%s)" % (ionName, self.currentDoc)
                    zvals, xaxisLabels, xlabel, yaxisLabels, ylabel, cmap = self.get2DdataFromDictionary(
                        dictionary=dataIn, dataType='plot', compact=False)

                elif source == "text":
                    tempAccumulator += 1
                    comparisonFlag = False  # used only in case the user reloaded comparison document
                    # Get data for each ion
                    itemInfo = self.view.panelMultipleText.OnGetItemInformation(itemID=row)
                    charge = itemInfo["charge"]
                    color = itemInfo["color"]
                    colormap = itemInfo["colormap"]
                    alpha = itemInfo["alpha"]
                    mask = itemInfo["mask"]
                    label = itemInfo["label"]
                    filename = itemInfo["document"]
                    min_threshold = itemInfo["min_threshold"]
                    max_threshold = itemInfo["max_threshold"]
                    # get document
                    try:
                        document = self.documentsDict[filename]

                        if self.config.overlay_usedProcessed:
                            if document.got2Dprocess:
                                try:
                                    tempData = document.IMS2Dprocess
                                except Exception:
                                    tempData = document.IMS2D
                            else:
                                tempData = document.IMS2D
                        else:
                            try:
                                tempData = document.IMS2D
                            except Exception:
                                self.onThreading(None, ('No data for selected file', 4), action='updateStatusbar')
                                continue

                        zvals = tempData['zvals']
                        xaxisLabels = tempData['xvals']
                        xlabel = tempData['xlabels']
                        yaxisLabels = tempData['yvals']
                        ylabel = tempData['ylabels']
                        ionName = filename
                        # Populate x-axis labels
                        if isinstance(xaxisLabels, list):
                            pass
                        elif xaxisLabels is "":
                            startX = tempList.GetItem(itemId=row,
                                                      col=self.config.textlistColNames['startX']).GetText()
                            endX = tempList.GetItem(itemId=row,
                                                    col=self.config.textlistColNames['endX']).GetText()
                            stepsX = len(zvals[0])
                            if startX == "" or endX == "":
                                pass
                            else:
                                xaxisLabels = self.onPopulateXaxisTextLabels(startVal=str2num(startX),
                                                                             endVal=str2num(endX),
                                                                             shapeVal=stepsX)
                                document.IMS2D['xvals'] = xaxisLabels

                        if not comparisonFlag:
                            selectedItemUnique = "file:%s" % filename
                    # only triggered when using data from comparison document
                    except Exception:
                        try:
                            comparisonFlag = True
                            dpcument_filename, selectedItemUnique = re.split(': ', filename)
                            document = self.documentsDict[dpcument_filename]
                            tempData = document.IMS2DcompData[selectedItemUnique]
                            # unpack data
                            zvals = tempData['zvals']
                            ionName = tempData['ion_name']
                            xaxisLabels = tempData['xvals']
                            yaxisLabels = tempData['yvals']
                            ylabel = tempData['ylabels']
                            xlabel = tempData['xlabels']
                        # triggered when using data from interactive document
                        except Exception:
                            comparisonFlag = False
                            dpcument_filename, selectedItemUnique = re.split(': ', filename)
                            document = self.documentsDict[dpcument_filename]
                            tempData = document.IMS2Dions[selectedItemUnique]
                            # unpack data
                            zvals = tempData['zvals']
                            ionName = filename
                            xaxisLabels = tempData['xvals']
                            yaxisLabels = tempData['yvals']
                            ylabel = tempData['ylabels']
                            xlabel = tempData['xlabels']

                if not comparisonFlag:
                    if label == '' or label is None:
                        label = ""
                    compList.insert(0, selectedItemUnique)
                    # Check if exists. We need to extract labels (header...)
                    checkExist = compDict.get(selectedItemUnique, None)
                    if checkExist is not None:
                        title = compDict[selectedItemUnique].get('header', "")
                        header = compDict[selectedItemUnique].get('header', "")
                        footnote = compDict[selectedItemUnique].get('footnote', "")
                    else:
                        title, header, footnote = "", "", ""
                    compDict[selectedItemUnique] = {'zvals': zvals,
                                                    'ion_name': ionName,
                                                    'cmap': colormap,
                                                    'color': color,
                                                    'alpha': str2num(alpha),
                                                    'mask': str2num(mask),
                                                    'xvals': xaxisLabels,
                                                    'xlabels': xlabel,
                                                    'yvals': yaxisLabels,
                                                    'charge': charge,
                                                    'min_threshold': min_threshold,
                                                    'max_threshold': max_threshold,
                                                    'ylabels': ylabel,
                                                    'index': row,
                                                    'shape': zvals.shape,
                                                    'label': label,
                                                    'title': title,
                                                    'header': header,
                                                    'footnote': footnote}
                else:
                    compDict[selectedItemUnique] = tempData

        # Check whether the user selected at least two files (and no more than 2 for certain functions)
        if tempAccumulator < 2:
            msg = 'Please select at least two files'
            dlgBox(exceptionTitle='Error', exceptionMsg=msg, type="Error")
            return

        # Remove duplicates from list
        compList = removeDuplicates(compList)

        zvalsIon1plot = compDict[compList[0]]['zvals']
        zvalsIon2plot = compDict[compList[1]]['zvals']
        name1 = compList[0]
        name2 = compList[1]
        # Check if text files are of identical size
        if ((zvalsIon1plot.shape != zvalsIon2plot.shape) and
                self.config.overlayMethod not in ["Grid (n x n)"]):
            msg = "Comparing ions: %s and %s. These files are NOT of identical shape!" % (name1, name2)
            dlgBox(exceptionTitle='Error', exceptionMsg=msg, type="Error")
            return

        defaultVals = ['Reds', 'Greens']
        ylabelRMSF = 'RMSD (%)'
        # Check if the table has information about colormap
        if compDict[compList[0]]['cmap'] == '':
            cmapIon1 = defaultVals[0]  # change here
            compDict[compList[0]]['cmap'] = cmapIon1
            tempList.SetStringItem(index=compDict[compList[0]]['index'],
                                   col=3, label=cmapIon1)
        else:
            cmapIon1 = compDict[compList[0]]['cmap']

        if compDict[compList[1]]['cmap'] == '':
            cmapIon2 = defaultVals[1]
            compDict[compList[1]]['cmap'] = cmapIon1
            tempList.SetStringItem(index=compDict[compList[1]]['index'],
                                   col=3, label=cmapIon2)
        else:
            cmapIon2 = compDict[compList[1]]['cmap']

        # Defaults for alpha and mask
        defaultVals_alpha = [1, 0.5]
        defaultVals_mask = [0.25, 0.25]

        # Check if the user set value of transparency (alpha)
        if compDict[compList[0]]['alpha'] == '' or compDict[compList[0]]['alpha'] is None:
            alphaIon1 = defaultVals_alpha[0]
            compDict[compList[0]]['alpha'] = alphaIon1
            tempList.SetStringItem(index=compDict[compList[0]]['index'], col=col_order['alpha'], label=str(alphaIon1))
        else:
            alphaIon1 = str2num(compDict[compList[0]]['alpha'])

        if compDict[compList[1]]['alpha'] == '' or compDict[compList[1]]['alpha'] is None:
            alphaIon2 = defaultVals_alpha[1]
            compDict[compList[1]]['alpha'] = alphaIon2
            tempList.SetStringItem(index=compDict[compList[1]]['index'], col=col_order['alpha'], label=str(alphaIon2))
        else:
            alphaIon2 = str2num(compDict[compList[1]]['alpha'])

        # Check if the user set value of transparency (mask)
        if compDict[compList[0]]['mask'] == '' or compDict[compList[0]]['mask'] is None:
            maskIon1 = defaultVals_mask[0]
            compDict[compList[0]]['mask'] = maskIon1
            tempList.SetStringItem(index=compDict[compList[0]]['index'], col=col_order['mask'], label=str(maskIon1))
        else:
            maskIon1 = str2num(compDict[compList[0]]['mask'])

        if compDict[compList[1]]['mask'] == '' or compDict[compList[1]]['mask'] is None:
            maskIon2 = defaultVals_mask[1]
            compDict[compList[1]]['mask'] = maskIon2
            tempList.SetStringItem(index=compDict[compList[1]]['index'], col=col_order['mask'], label=str(maskIon2))
        else:
            maskIon2 = str2num(compDict[compList[1]]['mask'])

        # Various comparison plots
        if self.config.overlayMethod == 'Grid (2->1)':
            self.view.panelPlots.mainBook.SetSelection(self.config.panelNames['Overlay'])

            pRMSD, tempArray = pr_activation.compute_RMSD(inputData1=zvalsIon1plot,
                                                          inputData2=zvalsIon2plot)
            rmsdLabel = "RMSD: %2.2f" % pRMSD
            self.onThreading(None, ("RMSD: %2.2f" % pRMSD, 4), action='updateStatusbar')
            self.setXYlimitsRMSD2D(xaxisLabels, yaxisLabels)
            self.view.panelPlots.on_plot_grid(zvalsIon1plot, zvalsIon2plot, tempArray, xaxisLabels,
                                              yaxisLabels, xlabel, ylabel, cmapIon1, cmapIon2)

#             # Add RMSD label
            rmsdXpos, rmsdYpos = self.onCalculateRMSDposition(xlist=xaxisLabels, ylist=yaxisLabels)
            if rmsdXpos is not None and rmsdYpos is not None:
                self.addTextRMSD(rmsdXpos, rmsdYpos, rmsdLabel, 0, plot='Grid')

            # Add data to the dictionary (overlay data)
            idName = '%s, %s' % (compList[0], compList[1])
            idName = "%s: %s" % (self.config.overlayMethod, idName)
            if add_data_to_document:
                self.docs.gotOverlay = True
                # Add to the name to includ the method
                # Check if exists. We need to extract labels (header...)
                checkExist = self.docs.IMS2DoverlayData.get(idName, None)
                if checkExist is not None:
                    title = self.docs.IMS2DoverlayData[idName].get('header', "")
                    header = self.docs.IMS2DoverlayData[idName].get('header', "")
                    footnote = self.docs.IMS2DoverlayData[idName].get('footnote', "")
                else:
                    title, header, footnote = "", "", ""

                self.docs.IMS2DoverlayData[idName] = {'zvals_1': zvalsIon1plot,
                                                      'zvals_2': zvalsIon2plot,
                                                      'zvals_cum': tempArray,
                                                      'cmap_1': cmapIon1,
                                                      'cmap_2': cmapIon2,
                                                      'xvals': xaxisLabels,
                                                      'xlabels': xlabel,
                                                      'yvals': yaxisLabels,
                                                      'ylabels': ylabel,
                                                      'rmsdLabel': rmsdLabel,
                                                      'title': title,
                                                      'header': header,
                                                      'footnote': footnote}
        elif self.config.overlayMethod == "Grid (n x n)":
            zvals_list, xvals_list, yvals_list, cmap_list, title_list, idName = [], [], [], [], [], ""
            for row in range(tempAccumulator):
                key = compList[row]
                zvals_list.append(compDict[key]['zvals'])
                cmap_list.append(compDict[key]['cmap'])
                title_list.append(compDict[key]['label'])
                xvals_list.append(compDict[key]['xvals'])
                yvals_list.append(compDict[key]['yvals'])

                # Add new label
                if idName == "":
                    idName = compList[row]
                else:
                    idName = "%s, %s" % (idName, compList[row])

            n_grid = len(zvals_list)
            if n_grid in [2]:
                n_rows, n_cols = 1, 2
            elif n_grid in [3, 4]:
                n_rows, n_cols = 2, 2
            elif n_grid in [5, 6]:
                n_rows, n_cols = 2, 3
            elif n_grid in [7, 8, 9]:
                n_rows, n_cols = 3, 3
            elif n_grid in [10, 11, 12]:
                n_rows, n_cols = 3, 4
            elif n_grid in [13, 14, 15, 16]:
                n_rows, n_cols = 4, 4
            elif n_grid in list(range(17, 26)):
                n_rows, n_cols = 5, 5
            elif n_grid in list(range(26, 37)):
                n_rows, n_cols = 6, 6
            else:
                dlgBox(exceptionTitle='Error',
                       exceptionMsg="Cannot plot grid larger than 6 x 6. You have selected".format(n_grid),
                       type="Error", exceptionPrint=True)
                return

            checkExist = compDict.get(selectedItemUnique, None)
            if checkExist is not None:
                title = compDict[selectedItemUnique].get('header', "")
                header = compDict[selectedItemUnique].get('header', "")
                footnote = compDict[selectedItemUnique].get('footnote', "")
            else:
                title, header, footnote = "", "", ""
            idName = "%s: %s" % (self.config.overlayMethod, idName)
            # remove unnecessary file extensions from filename
            if len(idName) > 511:
                print("Filename is too long. Reducing...")
                idName = idName.replace(".csv", "").replace(".txt", "").replace(".raw", "").replace(".d", "")
                idName = idName[:500]

            self.view.panelPlots.on_plot_n_grid(zvals_list, cmap_list,
                                                title_list, xvals_list,
                                                yvals_list, xlabel, ylabel)
            if add_data_to_document:
                self.docs.gotOverlay = True
                self.docs.IMS2DoverlayData[idName] = {'zvals_list': zvals_list,
                                                      'cmap_list': cmap_list,
                                                      'title_list': title_list,
                                                      'plot_parameters': {'n_grid': n_grid,
                                                                          'n_rows': n_rows,
                                                                          'n_cols': n_cols},
                                                      'xvals': xvals_list,
                                                      'xlabels': xlabel,
                                                      'yvals': yvals_list,
                                                      'ylabels': ylabel,
                                                      'title': title,
                                                      'header': header,
                                                      'footnote': footnote}

        elif self.config.overlayMethod in ["Transparent", "Mask", "RMSD", "RMSF"]:

            # Check how many items were selected
            if tempAccumulator > 2:
                msg = "Currently only supporting an overlay of two ions.\n" + \
                      "Comparing: {} and {}.".format(compList[0], compList[1])
                dlgBox(exceptionTitle='Warning', exceptionMsg=msg, type="Warning")
                print(msg)

            if self.config.overlayMethod == "Transparent":
                self.view.panelPlots.mainBook.SetSelection(self.config.panelNames['Overlay'])
                # Overlay plot of two species to see whether there is a difference between

                self.view.panelPlots.on_plot_overlay_2D(zvalsIon1=zvalsIon1plot,
                                                        cmapIon1=cmapIon1,
                                                        alphaIon1=alphaIon1,
                                                        zvalsIon2=zvalsIon2plot,
                                                        cmapIon2=cmapIon2,
                                                        alphaIon2=alphaIon2,
                                                        xvals=xaxisLabels,
                                                        yvals=yaxisLabels,
                                                        xlabel=xlabel,
                                                        ylabel=ylabel,
                                                        flag='Text',
                                                        plotName="Transparent")

            elif self.config.overlayMethod == "Mask":
                # In this case, the values are not transparency but a threshold cutoff! Values between 0-1
                cutoffIon1 = maskIon1
                cutoffIon2 = maskIon2
                # Based on the value in alpha/cutoff, data will be cleared up
                zvalsIon1plotMask = masked_array(zvalsIon1plot, zvalsIon1plot < cutoffIon1)
                zvalsIon1plot = zvalsIon1plotMask
                zvalsIon2plotMask = masked_array(zvalsIon2plot, zvalsIon2plot < cutoffIon2)
                zvalsIon2plot = zvalsIon2plotMask
                self.view.panelPlots.mainBook.SetSelection(self.config.panelNames['Overlay'])
                self.view.panelPlots.on_plot_overlay_2D(zvalsIon1=zvalsIon1plotMask,
                                                        cmapIon1=cmapIon1,
                                                        alphaIon1=1,
                                                        zvalsIon2=zvalsIon2plotMask,
                                                        cmapIon2=cmapIon2,
                                                        alphaIon2=1,
                                                        xvals=xaxisLabels,
                                                        yvals=yaxisLabels,
                                                        xlabel=xlabel,
                                                        ylabel=ylabel,
                                                        flag='Text',
                                                        plotName="Mask")

            elif self.config.overlayMethod == "RMSD":
                """ Compute RMSD of two selected files """
                # Check whether we should be restricting the RMSD range
                if self.config.restrictXYrangeRMSD:
                    zvalsIon1plot, xvals, yvals = self.restrictRMSDrange(zvalsIon1plot, xaxisLabels,
                                                                         yaxisLabels, self.config.xyLimitsRMSD)

                    zvalsIon2plot, xvals, yvals = self.restrictRMSDrange(zvalsIon2plot, xaxisLabels,
                                                                         yaxisLabels, self.config.xyLimitsRMSD)
                    xaxisLabels, yaxisLabels = xvals, yvals

                pRMSD, tempArray = pr_activation.compute_RMSD(inputData1=zvalsIon1plot,
                                                              inputData2=zvalsIon2plot)
                rmsdLabel = "RMSD: %2.2f" % pRMSD
                self.onThreading(None, ("RMSD: %2.2f" % pRMSD, 4), action='updateStatusbar')

                self.setXYlimitsRMSD2D(xaxisLabels, yaxisLabels)

                self.view.panelPlots.on_plot_RMSD(tempArray, xaxisLabels, yaxisLabels, xlabel, ylabel,
                                                  self.config.currentCmap, plotType='RMSD',
                                                  set_page=True)
                # Add RMSD label
                rmsdXpos, rmsdYpos = self.onCalculateRMSDposition(xlist=xaxisLabels, ylist=yaxisLabels)
                if rmsdXpos is not None and rmsdYpos is not None:
                    self.addTextRMSD(rmsdXpos, rmsdYpos, rmsdLabel, 0)
                try:
                    self.view.panelPlots.on_plot_3D(zvals=tempArray, labelsX=xaxisLabels, labelsY=yaxisLabels,
                                                    xlabel=xlabel, ylabel=ylabel, zlabel='Intensity',
                                                    cmap=self.config.currentCmap)
                except Exception:
                    pass

            elif self.config.overlayMethod == "RMSF":
                """ Compute RMSF of two selected files """
                self.rmsdfFlag = True

                if self.config.restrictXYrangeRMSD:
                    zvalsIon1plot, xvals, yvals = self.restrictRMSDrange(zvalsIon1plot, xaxisLabels,
                                                                         yaxisLabels, self.config.xyLimitsRMSD)

                    zvalsIon2plot, xvals, yvals = self.restrictRMSDrange(zvalsIon2plot, xaxisLabels,
                                                                         yaxisLabels, self.config.xyLimitsRMSD)
                    xaxisLabels, yaxisLabels = xvals, yvals

                pRMSFlist = pr_activation.compute_RMSF(inputData1=zvalsIon1plot, inputData2=zvalsIon2plot)
                pRMSD, tempArray = pr_activation.compute_RMSD(inputData1=zvalsIon1plot, inputData2=zvalsIon2plot)

                rmsdLabel = "RMSD: %2.2f" % pRMSD
                self.onThreading(None, ("RMSD: %2.2f" % pRMSD, 4), action='updateStatusbar')
                xLabel = compDict[compList[0]]['xlabels']
                yLabel = compDict[compList[0]]['ylabels']
                pRMSFlist = pr_heatmap.smooth_gaussian_2D(inputData=pRMSFlist, sigma=1)

                self.setXYlimitsRMSD2D(xaxisLabels, yaxisLabels)
                self.view.panelPlots.on_plot_RMSDF(yvalsRMSF=pRMSFlist,
                                                   zvals=tempArray,
                                                   xvals=xaxisLabels, yvals=yaxisLabels,
                                                   xlabelRMSD=xLabel, ylabelRMSD=yLabel,
                                                   ylabelRMSF=ylabelRMSF,
                                                   color=self.config.lineColour_1D,
                                                   cmap=self.config.currentCmap)
#                 self.onPlotRMSDF(yvalsRMSF=pRMSFlist,
#                                  zvals=tempArray,
#                                  xvals=xaxisLabels, yvals=yaxisLabels,
#                                  xlabelRMSD=xLabel, ylabelRMSD=yLabel,
#                                  ylabelRMSF=ylabelRMSF,
#                                  color=self.config.lineColour_1D,
#                                  cmap=self.config.currentCmap)
                self.view.panelPlots.mainBook.SetSelection(self.config.panelNames['RMSF'])
                # Add RMSD label
                rmsdXpos, rmsdYpos = self.onCalculateRMSDposition(xlist=xaxisLabels,
                                                                  ylist=yaxisLabels)
                if rmsdXpos is not None and rmsdYpos is not None:
                    self.addTextRMSD(rmsdXpos, rmsdYpos, rmsdLabel, 0, plot='RMSF')

            # Add data to the dictionary (overlay data)
            if add_data_to_document:
                self.docs.gotOverlay = True
                # add label
                idName = '%s, %s' % (compList[0], compList[1])

                idName = "%s: %s" % (self.config.overlayMethod, idName)
                # Add to the name to includ the method
                # Check if exists. We need to extract labels (header...)
                checkExist = self.docs.IMS2DoverlayData.get(idName, None)
                if checkExist is not None:
                    title = self.docs.IMS2DoverlayData[idName].get('header', "")
                    header = self.docs.IMS2DoverlayData[idName].get('header', "")
                    footnote = self.docs.IMS2DoverlayData[idName].get('footnote', "")
                else:
                    title, header, footnote = "", "", ""
                # Add data to dictionary
                if self.config.overlayMethod in ["Mask", "Transparent"]:
                    self.docs.IMS2DoverlayData[idName] = {'zvals1': zvalsIon1plot,
                                                          'zvals2': zvalsIon2plot,
                                                          'cmap1': cmapIon1,
                                                          'cmap2': cmapIon2,
                                                          'alpha1': alphaIon1,
                                                          'alpha2': alphaIon2,
                                                          'mask1': maskIon1,
                                                          'mask2': maskIon2,
                                                          'xvals': xaxisLabels,
                                                          'xlabels': xlabel,
                                                          'yvals': yaxisLabels,
                                                          'ylabels': ylabel,
                                                          'file1': compList[0],
                                                          'file2': compList[1],
                                                          'label1': compDict[compList[0]]['label'],
                                                          'label2': compDict[compList[1]]['label'],
                                                          'title': title,
                                                          'header': header,
                                                          'footnote': footnote}
                elif self.config.overlayMethod == "RMSF":
                    self.docs.IMS2DoverlayData[idName] = {'yvalsRMSF': pRMSFlist,
                                                          'zvals': tempArray,
                                                          'xvals': xaxisLabels,
                                                          'yvals': yaxisLabels,
                                                          'ylabelRMSF': ylabelRMSF,
                                                          'xlabelRMSD': xLabel,
                                                          'ylabelRMSD': yLabel,
                                                          'rmsdLabel': rmsdLabel,
                                                          'colorRMSF': self.config.lineColour_1D,
                                                          'cmapRMSF': self.config.currentCmap,
                                                          'title': title,
                                                          'header': header,
                                                          'footnote': footnote}
                elif self.config.overlayMethod == "RMSD":
                    self.docs.IMS2DoverlayData[idName] = {'zvals': tempArray,
                                                          'xvals': xaxisLabels,
                                                          'yvals': yaxisLabels,
                                                          'xlabel': xlabel,
                                                          'ylabel': ylabel,
                                                          'rmsdLabel': rmsdLabel,
                                                          'cmap': self.config.currentCmap,
                                                          'title': title,
                                                          'header': header,
                                                          'footnote': footnote}

        elif any(self.config.overlayMethod in method for method in ["Mean", "Standard Deviation", "Variance"]):
            meanData = []
            for row in range(tempAccumulator):
                key = compList[row]
                meanData.append(compDict[key]['zvals'])

            xAxisLabels = compDict[key]['xvals']
            xlabel = compDict[key]['xlabels']
            yAxisLabels = compDict[key]['yvals']
            ylabel = compDict[key]['ylabels']
            msg = ''.join(["Computing ", self.config.textOverlayMethod, " for ", str(len(meanData)), " files."])
            self.onThreading(None, (msg, 4), action='updateStatusbar')
            if self.config.overlayMethod == "Mean":
                """ Computes mean of selected files """
                zvals = pr_activation.compute_mean(inputData=meanData)
            elif self.config.overlayMethod == "Standard Deviation":
                """ Computes standard deviation of selected files """
                zvals = pr_activation.compute_std_dev(inputData=meanData)
            elif self.config.overlayMethod == "Variance":
                """ Computes variance of selected files """
                zvals = pr_activation.compute_variance(inputData=meanData)
            # Plot
            self.view.panelPlots.on_plot_2D_data(
                data=[
        zvals,
        xAxisLabels,
        xlabel,
        yAxisLabels,
        ylabel,
        self.config.currentCmap])
            self.view.panelPlots.mainBook.SetSelection(self.config.panelNames['2D'])
            if add_data_to_document:
                self.docs.gotStatsData = True
                # Check if exists. We need to extract labels (header...)
                checkExist = self.docs.IMS2DstatsData.get(self.config.overlayMethod, None)
                if checkExist is not None:
                    title = self.docs.IMS2DstatsData[self.config.overlayMethod].get('header', "")
                    header = self.docs.IMS2DstatsData[self.config.overlayMethod].get('header', "")
                    footnote = self.docs.IMS2DstatsData[self.config.overlayMethod].get('footnote', "")
                else:
                    title, header, footnote = "", "", ""

                # add label
                idName = '%s, %s' % (compList[0], compList[1])
                idName = "%s: %s" % (self.config.overlayMethod, idName)

                self.docs.IMS2DstatsData[idName] = {'zvals': zvals,
                                                    'xvals': xAxisLabels,
                                                    'xlabels': xlabel,
                                                    'yvals': yAxisLabels,
                                                    'ylabels': ylabel,
                                                    'cmap': self.config.currentCmap,
                                                    'title': title,
                                                    'header': header,
                                                    'footnote': footnote}
        elif self.config.overlayMethod == "RMSD Matrix":
            """ Compute RMSD matrix for selected files """
            zvals = np.zeros([tempAccumulator, tempAccumulator])
            tickLabels = []
            for row in range(tempAccumulator):
                key = compList[row]
                # Extract text labels from table
                tickLabels.append(compDict[key]['label'])
                # Compute pairwise RMSD
                for row2 in range(row + 1, tempAccumulator):
                    zvalsIon1plot = compDict[compList[row]]['zvals']
                    zvalsIon2plot = compDict[compList[row2]]['zvals']
                    pRMSD, tempArray = pr_activation.compute_RMSD(inputData1=zvalsIon1plot,
                                                                  inputData2=zvalsIon2plot)
                    zvals[row, row2] = np.round(pRMSD, 2)
            self.view.panelPlots.on_plot_matrix(zvals=zvals, xylabels=tickLabels, cmap=self.docs.colormap)
            self.view.panelPlots.mainBook.SetSelection(self.config.panelNames['Comparison'])
            if add_data_to_document:
                self.docs.gotStatsData = True
                # Check if exists. We need to extract labels (header...)
                checkExist = self.docs.IMS2DstatsData.get(self.config.overlayMethod, None)
                if checkExist is not None:
                    title = self.docs.IMS2DstatsData[self.config.overlayMethod].get('header', "")
                    header = self.docs.IMS2DstatsData[self.config.overlayMethod].get('header', "")
                    footnote = self.docs.IMS2DstatsData[self.config.overlayMethod].get('footnote', "")
                else:
                    title, header, footnote = "", "", ""
                self.docs.IMS2DstatsData[self.config.overlayMethod] = {'zvals': zvals,
                                                                       'cmap': self.config.currentCmap,
                                                                       'matrixLabels': tickLabels,
                                                                       'title': title,
                                                                       'header': header,
                                                                       'footnote': footnote}

        elif self.config.overlayMethod == "RGB":
            data_list, idName = [], ""
            legend_text = []
            for row in range(tempAccumulator):
                key = compList[row]
                data = compDict[key]['zvals']
                color = convertRGB255to1(compDict[key]['color'])
                min_threshold = compDict[key]['min_threshold']
                max_threshold = compDict[key]['max_threshold']
                label = compDict[key]['label']
                if label == "":
                    label = compDict[key]['ion_name']
                legend_text.append([color, label])

                # Change intensity
                data = pr_heatmap.adjust_min_max_intensity(data.copy(), min_threshold, max_threshold)
                # Convert to RGB
                rgb = make_rgb(data, color)
                data_list.append(rgb)
                # Add new label
                if idName == "":
                    idName = compList[row]
                else:
                    idName = "%s, %s" % (idName, compList[row])
            xAxisLabels = compDict[key]['xvals']
            xlabel = compDict[key]['xlabels']
            yAxisLabels = compDict[key]['yvals']
            ylabel = compDict[key]['ylabels']

            # Sum rgb list
            if len(data_list) >= 1:
                rgb_plot = combine_rgb(data_list)

                self.view.panelPlots.on_plot_rgb(rgb_plot, xAxisLabels, yAxisLabels, xlabel,
                                                 ylabel, legend_text)
                self.view.panelPlots.mainBook.SetSelection(self.config.panelNames['2D'])

            # Add data to the dictionary (overlay data)
            if add_data_to_document:
                self.docs.gotOverlay = True
                # Add to the name to includ the method
                # Check if exists. We need to extract labels (header...)
                checkExist = self.docs.IMS2DoverlayData.get(idName, None)
                if checkExist is not None:
                    title = self.docs.IMS2DoverlayData[idName].get('header', "")
                    header = self.docs.IMS2DoverlayData[idName].get('header', "")
                    footnote = self.docs.IMS2DoverlayData[idName].get('footnote', "")
                else:
                    title, header, footnote = "", "", ""
                idName = "%s: %s" % (self.config.overlayMethod, idName)
                # remove unnecessary file extensions from filename
                if len(idName) > 511:
                    self.onThreading(None, ("Filename is too long. Reducing...", 4), action='updateStatusbar')
                    idName = idName.replace(".csv", "").replace(".txt", "").replace(".raw", "").replace(".d", "")
                    idName = idName[:500]

                self.docs.IMS2DoverlayData[idName] = {'zvals': rgb_plot,
                                                      'xvals': xaxisLabels,
                                                      'xlabels': xlabel,
                                                      'yvals': yaxisLabels,
                                                      'ylabels': ylabel,
                                                      'rgb_list': data_list,
                                                      'legend_text': legend_text,
                                                      'title': title,
                                                      'header': header,
                                                      'footnote': footnote}

        # Add data to document
        if add_data_to_document:
            self.docs.gotComparisonData = True
            self.docs.IMS2DcompData = compDict
            self.currentDoc = self.docs.title

            # Update file list
            self.OnUpdateDocument(self.docs, 'comparison_data')

    def restrictRMSDrange(self, zvals, xvals, yvals, limits):
        """
        This function adjusts the size of the RMSD array to match the selected
        sizes from the GUI
        """
        # Get limits
        xmin, xmax, ymin, ymax = limits

        if xmin > xmax:
            xmin_temp = xmax
            xmax = xmin
            xmin = xmin_temp

        if ymin > ymax:
            ymin_temp = ymax
            ymax = ymin
            ymin = ymin_temp

#         print(xmin, xmax, ymin, ymax)

        if xmin is None:
            xmin = xvals[0]
        if xmax is None:
            xmax = xvals[-1]
        if ymin is None:
            ymin = xvals[0]
        if ymax is None:
            ymax = xvals[-1]

        # Find nearest values
        __, idxXmin = find_nearest(np.array(xvals), xmin)
        __, idxXmax = find_nearest(np.array(xvals), xmax)
        __, idxYmin = find_nearest(np.array(yvals), ymin)
        __, idxYmax = find_nearest(np.array(yvals), ymax)

        # in case index is returned as 0, return original value
        msg = ''.join([""])
        if idxXmax == 0:
            msg = 'Your Xmax value is too small - reseting to maximum'
            idxXmax = len(xvals)
        if idxXmin == idxXmax:
            msg = 'Your X-axis values are too close together - reseting to original view'
            idxXmin = 0
            idxXmax = len(xvals)

        if idxYmax == 0:
            msg = 'Your Ymax value is too small - reseting to maximum'
            idxYmax = len(yvals)
        if idxYmin == idxYmax:
            msg = 'Your Y-axis values are too close together - reseting to original view'
            idxYmin = 0
            idxYmax = len(yvals)

        zvals = zvals[idxYmin:idxYmax, idxXmin:idxXmax]
        xvals = xvals[idxXmin:idxXmax]
        yvals = yvals[idxYmin:idxYmax]
        self.onThreading(None, (msg, 4), action='updateStatusbar')

        return zvals, xvals, yvals

    def restoreComparisonToList(self, evt=None):
        """
        Once comparison document was made and has been pickled, the data is not
        easily accesible (apart from replotting). This function is to help retreive
        the input data and restore it to the file list - in this case text panel
        """
        try:
            self.currentDoc = self.view.panelDocuments.documents.enableCurrentDocument()
        except Exception:
            return
        if self.currentDoc == "Current documents":
            return

        # Make sure the document is of comparison type
        if self.documentsDict[self.currentDoc].dataType == 'Type: Comparison':
            # Enable text panel
            self.view.onPaneOnOff(evt=ID_window_textList, check=True)
#             self.view.textView = False
#             self.view.mainToolbar.ToggleTool(id=ID_OnOff_textView, toggle=True)
#             self.view._mgr.GetPane(self.view.panelMultipleText).Show()
#             self.view._mgr.Update()
            tempList = self.view.panelMultipleText.peaklist
            document = self.documentsDict[self.currentDoc]
            if document.gotComparisonData:
                filename = document.title
                for key in document.IMS2DcompData:
                    xvals = document.IMS2DcompData[key]['xvals']
                    shape = document.IMS2DcompData[key]['shape']
                    label = document.IMS2DcompData[key]['label']
                    cmap = document.IMS2DcompData[key]['cmap']
                    alpha = document.IMS2DcompData[key]['alpha']
                    tempList.Append([filename,
                                     xvals[0], xvals[-1],
                                     cmap, str(alpha),
                                     label, shape,
                                     key])

    def onCalculateRMSDposition(self, xlist, ylist):
        """
        This function calculates the X and Y position of the RMSD label
        """

        # First determine whether we need label at all
        if self.config.rmsd_position == "none":
            return None, None

        # Get values
        xMultiplier, yMultiplier = self.config.rmsd_location
        xMin = np.min(xlist)
        xMax = np.max(xlist)
        yMin = np.min(ylist)
        yMax = np.max(ylist)

        # Calculate RMSD positions
        rmsdXpos = xMin + ((xMax - xMin) * xMultiplier) / 100
        rmsdYpos = yMin + ((yMax - yMin) * yMultiplier) / 100

        args = ("Added RMSD label at xpos: %s ypos %s" % (rmsdXpos, rmsdYpos), 4)
        self.onThreading(None, args, action='updateStatusbar')

        return rmsdXpos, rmsdYpos

#     def onCombineMultipleMLFiles(self, e=None):
#         """
#         This function takes the multiple ML dictionary, sorts it and combines it
#         to form a 2D IM-MS map
#         """
#         try:
#             self.currentDoc = self.view.panelDocuments.documents.enableCurrentDocument()
#         except Exception:
#             return
#         self.docs = self.documentsDict[self.currentDoc]
#         if self.docs.dataType != 'Type: MANUAL':
#             msg = 'Make sure you select the correct dataset - MANUAL'
#             self.onThreading(None, (msg, 4), action='updateStatusbar')
#             return
#
#         # Sort data in the dictionary first - if returns False then it hasn't done it!
#         vals_sorted = self.view.panelMML.OnSortByColumn(column=1)
#         tempList = self.view.panelMML.peaklist
#         if not vals_sorted:
#             return
#         else:
#             counter = 0
#             for item in range(tempList.GetItemCount()):
#                 key = tempList.GetItem(item, 0).GetText()
# #                 trapCV = str2num(tempList.GetItem(item,1).GetText())
#                 if counter == 0:
#                     tempArray = self.docs.multipleMassSpectrum[key]['ims1D']
#                     xLabelLow = self.docs.multipleMassSpectrum[key]['trap']  # first iteration so first value
#                     counter = counter + 1
#                 else:
#                     imsList = self.docs.multipleMassSpectrum[key]['ims1D']
#                     tempArray = np.concatenate((tempArray, imsList), axis=0)
#                     counter = counter + 1
#
#             # Reshape data to form a 2D array of size 200 x number of files
#             imsData2D = tempArray.reshape((200, int(counter)), order='F')
#             # Get the x-axis labels
#             xLabelHigh = self.docs.multipleMassSpectrum[key]['trap']  # after the loop has finished, so last value
#             xlabels = np.linspace(xLabelLow, xLabelHigh, num=counter)
#             ylabels = 1 + np.arange(len(imsData2D[:, 1]))
#             self.view.panelPlots.on_plot_2D_data(data=[imsData2D, xlabels,
#                                                        'Collision Voltage (V)', ylabels,
#                                                        'Drift time (bins)',
#                                                        self.docs.colormap])
#
#             self.docs.got2DIMS = True
#             self.docs.IMS2D = {'zvals': imsData2D,
#                                'xvals': xlabels,
#                                'xlabels': 'Collision Voltage (V)',
#                                'yvals': ylabels,
#                                'ylabels': 'Drift time (bins)',
#                                'cmap': self.docs.colormap}
#
#             # Append to list
#             self.documentsDict[self.docs.title] = self.docs
#
#             # Update documents tree
#             self.view.panelDocuments.documents.add_document(docData=self.docs)

    def checkIfRawFile(self, path):
        """
        Checks whether the selected directory is a MassLynx file i.e. ends with .raw
        """
        if path.rstrip('/')[-4:] == ".raw":
            return path

    def onProcessMultipleIonsIons(self, evt):
        """
        This function processes the 2D array data from multiple ions MULTIFILE or ORIGAMI
        """
        # Shortcut to table
        tempList = self.view.panelMultipleIons.peaklist

        # Make a list of current documents
        for row in range(tempList.GetItemCount()):
            self.currentDoc = tempList.GetItem(itemId=row, col=self.config.peaklistColNames['filename']).GetText()
            # Check that data was extracted first
            if self.currentDoc == '':
                self.onThreading(None, ('Please extract data first', 4), action='updateStatusbar')
                continue
            if evt.GetId() == ID_processAllIons:
                pass
            elif evt.GetId() == ID_processSelectedIons:
                if not tempList.IsChecked(index=row):
                    continue
            # Extract ion name
            mzStart = tempList.GetItem(itemId=row, col=self.config.peaklistColNames['start']).GetText()
            mzEnd = tempList.GetItem(itemId=row, col=self.config.peaklistColNames['end']).GetText()
            selectedItem = ''.join([str(mzStart), '-', str(mzEnd)])
            # strip any processed string from the title
            dataset = selectedItem
            if "(processed)" in selectedItem:
                dataset = selectedItem.split(" (")[0]
            new_dataset = "%s (processed)" % dataset
            # Select document
            self.docs = self.documentsDict[self.currentDoc]
            dataType = self.docs.dataType

            # process data
            if (dataType in ['Type: ORIGAMI', 'Type: Infrared', 'Type: MANUAL'] and
                    self.docs.gotCombinedExtractedIons):
                try:
                    tempData = self.docs.IMS2DCombIons[selectedItem]
                    imsData2D, params = self.data_processing.on_process_2D(zvals=tempData['zvals'].copy(),
                                                                           return_all=True)
                    imsData1D = np.sum(imsData2D, axis=1).T
                    rtDataY = np.sum(imsData2D, axis=0)
                    self.docs.IMS2DCombIons[new_dataset] = {'zvals': imsData2D,
                                                            'xvals': tempData['xvals'],
                                                            'xlabels': tempData['xlabels'],
                                                            'yvals': tempData['yvals'],
                                                            'ylabels': tempData['ylabels'],
                                                            'yvals1D': imsData1D, 'yvalsRT': rtDataY,
                                                            'cmap': tempData.get('cmap', self.config.currentCmap),
                                                            'xylimits': tempData['xylimits'],
                                                            'charge': tempData.get('charge', None),
                                                            'label': tempData.get('label', None),
                                                            'alpha': tempData.get('alpha', None),
                                                            'mask': tempData.get('alpha', None),
                                                            'process_parameters': params}
                except Exception:
                    pass

            if (dataType in ['Type: ORIGAMI', 'Type: Infrared'] and
                    self.docs.gotExtractedIons):
                try:
                    tempData = self.docs.IMS2Dions[selectedItem]
                    imsData2D, params = self.data_processing.on_process_2D(zvals=tempData['zvals'].copy(),
                                                                           return_all=True)
                    imsData1D = np.sum(imsData2D, axis=1).T
                    rtDataY = np.sum(imsData2D, axis=0)
                    self.docs.IMS2Dions[new_dataset] = {'zvals': imsData2D,
                                                        'xvals': tempData['xvals'],
                                                        'xlabels': tempData['xlabels'],
                                                        'yvals': tempData['yvals'],
                                                        'ylabels': tempData['ylabels'],
                                                        'yvals1D': imsData1D, 'yvalsRT': rtDataY,
                                                        'cmap': tempData.get('cmap', self.config.currentCmap),
                                                        'xylimits': tempData['xylimits'],
                                                        'charge': tempData.get('charge', None),
                                                        'label': tempData.get('label', None),
                                                        'alpha': tempData.get('alpha', None),
                                                        'mask': tempData.get('alpha', None),
                                                        'process_parameters': params}
                except Exception:
                    pass

            # Update file list
            self.OnUpdateDocument(self.docs, 'combined_ions')

#     def on_combine_mass_spectra(self, document_name=None):
#
#         if document_name is None:
#             self.docs = self.data_processing._on_get_document()
#         else:
#             self.docs = self.documentsDict[document_name]
#
#         kwargs = {'auto_range': False,
#                   'mz_min': self.config.ms_mzStart,
#                   'mz_max': self.config.ms_mzEnd,
#                   'mz_bin': self.config.ms_mzBinSize,
#                   'linearization_mode': self.config.ms_linearization_mode}
#         msg = "Linearization method: {} | min: {} | max: {} | window: {} | auto-range: {}".format(
#             self.config.ms_linearization_mode,
#             self.config.ms_mzStart,
#             self.config.ms_mzEnd,
#             self.config.ms_mzBinSize,
#             self.config.ms_auto_range)
#         self.onThreading(None, (msg, 4), action='updateStatusbar')
#
#         if len(list(self.docs.multipleMassSpectrum.keys())) > 0:
#             # check the min/max values in the mass spectrum
#             if self.config.ms_auto_range:
#                 mzStart, mzEnd = pr_spectra.check_mass_range(ms_dict=self.docs.multipleMassSpectrum)
#                 self.config.ms_mzStart = mzStart
#                 self.config.ms_mzEnd = mzEnd
#                 kwargs.update(mz_min=mzStart, mz_max=mzEnd)
#                 try:
#                     self.view.panelProcessData.on_update_GUI(update_what="mass_spectra")
#                 except:
#                     pass
#
#             msFilenames = ["m/z"]
#             counter = 0
#             for key in self.docs.multipleMassSpectrum:
#                 msFilenames.append(key)
#                 if counter == 0:
#                     msDataX, tempArray = pr_spectra.linearize_data(self.docs.multipleMassSpectrum[key]['xvals'],
#                                                                    self.docs.multipleMassSpectrum[key]['yvals'],
#                                                                    **kwargs)
#                     msList = tempArray
#                 else:
#                     msDataX, msList = pr_spectra.linearize_data(self.docs.multipleMassSpectrum[key]['xvals'],
#                                                                 self.docs.multipleMassSpectrum[key]['yvals'],
#                                                                 **kwargs)
#                     tempArray = np.concatenate((tempArray, msList), axis=0)
#                 counter += 1
#
#             # Reshape the list
#             combMS = tempArray.reshape((len(msList), int(counter)), order='F')
#
#             # Sum y-axis data
#             msDataY = np.sum(combMS, axis=1)
#             msDataY = pr_spectra.normalize_1D(inputData=msDataY)
#             xlimits = [self.docs.parameters['startMS'],
#                        self.docs.parameters['endMS']]
#
#             # Form pandas dataframe
#             combMSOut = np.concatenate((msDataX, tempArray), axis=0)
#             combMSOut = combMSOut.reshape((len(msList), int(counter + 1)), order='F')
#
#             # Add data
#             self.docs.gotMS = True
#             self.docs.massSpectrum = {'xvals': msDataX, 'yvals': msDataY, 'xlabels':'m/z (Da)', 'xlimits':xlimits}
#             # Plot
#             name_kwargs = {"document": self.docs.title, "dataset": "Mass Spectrum"}
#             self.view.panelPlots.on_plot_MS(msDataX, msDataY, xlimits=xlimits, **name_kwargs)
#
#             # Update status bar with MS range
#             self.view.SetStatusText("{}-{}".format(self.docs.parameters['startMS'],
#                                                    self.docs.parameters['endMS']), 1)
#             self.view.SetStatusText("MSMS: {}".format(self.docs.parameters['setMS']), 2)
#         else:
#             self.docs.gotMS = False
#             self.docs.massSpectrum = {}
#             self.view.SetStatusText("", 1)
#             self.view.SetStatusText("", 2)
#
#         # Add info to document
#         self.OnUpdateDocument(self.docs, 'document')

#     def reBinMSdata(self, evt):
#         self.currentDoc = self.view.panelDocuments.documents.enableCurrentDocument()
#         self.docs = self.documentsDict[self.currentDoc]
#
#         if self.docs.dataType == 'Type: MANUAL' and self.docs.gotMultipleMS:
#             # Sum all mass spectra into one
#             counter = 0
#             # Bin MS data
#             binsize = self.config.binMSbinsize
#             msBinList = np.arange(self.docs.parameters['startMS'],
#                                   self.docs.parameters['endMS'] + binsize,
#                                   binsize)
#
#             msCentre = msBinList[:-1] + (binsize / 2)
#             for key in self.docs.multipleMassSpectrum:
#                 if counter == 0:
#                     tempArray = pr_spectra.bin_1D(x=self.docs.multipleMassSpectrum[key]['xvals'],
#                                                   y=self.docs.multipleMassSpectrum[key]['yvals'],
#                                                   bins=msBinList)
#                     counter = counter + 1
#                 else:
#                     msList = pr_spectra.bin_1D(x=self.docs.multipleMassSpectrum[key]['xvals'],
#                                                y=self.docs.multipleMassSpectrum[key]['yvals'],
#                                                bins=msBinList)
#                     tempArray = np.concatenate((tempArray, msList), axis=0)
#                     counter = counter + 1
#             # Reshape the list
#             combMS = tempArray.reshape((len(msList), int(counter)), order='F')
#             # Sum y-axis data
#             msDataY = np.sum(combMS, axis=1)
#             msDataY = pr_spectra.normalize_1D(inputData=msDataY)
#             xlimits = self.docs.massSpectrum['xlimits']
#             # Add info to document
#             self.docs.massSpectrum = {'xvals': msCentre,
#                                       'yvals': msDataY,
#                                       'xlabels': 'm/z (Da)',
#                                       'xlimits': xlimits}
#             self.OnUpdateDocument(self.docs, 'document')
#             # Plot
#             name_kwargs = {"document": self.docs.title, "dataset": "Mass Spectrum"}
#             self.view.panelPlots.on_plot_MS(msCentre, msDataY, xlimits=xlimits, **name_kwargs)
#         evt.Skip()

    def on_highlight_selected_ions(self, evt):
        """
        This function adds rectanges and markers to the m/z window
        """
        self.docs = self.data_processing._on_get_document()

        if self.docs.dataType == 'Type: ORIGAMI' or self.docs.dataType == 'Type: MANUAL':
            tempList = self.view.panelMultipleIons.peaklist
        elif self.docs.dataType == 'Type: Multifield Linear DT':
            tempList = self.view.panelLinearDT.bottomP.peaklist
        else:
            return

        if not self.docs.gotMS:
            return

        name_kwargs = {"document": self.docs.title, "dataset": "Mass Spectrum"}
        self.view.panelPlots.on_plot_MS(self.docs.massSpectrum['xvals'],
                                        self.docs.massSpectrum['yvals'],
                                        xlimits=self.docs.massSpectrum['xlimits'],
                                        **name_kwargs)
        # Show rectangles
        # Need to check whether there were any ions in the table already
        last = tempList.GetItemCount() - 1
        ymin = 0
        height = 100000000000
        for item in range(tempList.GetItemCount()):
            itemInfo = self.view.panelMultipleIons.OnGetItemInformation(itemID=item)
            filename = itemInfo['document']
            if filename != self.currentDoc:
                continue
            xmin = itemInfo['start']
            width = itemInfo['end'] - xmin
            color = convertRGB255to1(itemInfo['color'])
            if np.sum(color) <= 0:
                color = self.config.markerColor_1D
            if item == last:
                self.view.panelPlots.on_plot_patches(xmin, ymin, width, height, color=color,
                                                     alpha=self.config.markerTransparency_1D,
                                                     repaint=True)
            else:
                self.view.panelPlots.on_plot_patches(xmin, ymin, width, height, color=color,
                                                     alpha=self.config.markerTransparency_1D,
                                                     repaint=False)

    def getImageFilename(self, prefix=False, csv=False, defaultValue='',
                         withPath=False, extension=None):
        """
        Set-up a new filename for saved images
        """

        if withPath:
            if extension is None:
                fileType = "Text file|*%s" % self.config.saveExtension
            else:
                fileType = extension
            dlg = wx.FileDialog(self.view, "Save data to file...", "", "", fileType,
                                wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
            dlg.SetFilename(defaultValue)
            if dlg.ShowModal() == wx.ID_OK:
                filename = dlg.GetPath()
                return filename
            else:
                return None
        elif not prefix:
            saveFileName = dlgAsk(
                'Please enter a new filename for the images. Names will be appended with the item keyword.',
                defaultValue=defaultValue)
        else:
            if not csv:
                saveFileName = dlgAsk(
                    'Please enter a new prefix for the images. Names will be appended with the item keyword.',
                    defaultValue=defaultValue)
            else:
                saveFileName = dlgAsk(
                    'Please enter a new prefix for the output file. Names will be appended with the item keyword.',
                    defaultValue=defaultValue)

        return saveFileName

    # TODO: Move to data_handling
    def onChangeChargeState(self, evt):

        self.currentDoc, selectedItem, selectedText = self.view.panelDocuments.documents.enableCurrentDocument(
            getSelected=True)
        if self.currentDoc is None or self.currentDoc == "Current documents":
            return
        indent = self.view.panelDocuments.documents.getItemIndent(selectedItem)
        selectedItemParentText = ''
        if indent > 2:
            __, selectedItemParentText = self.view.panelDocuments.documents.getParentItem(selectedItem, 2,
                                                                                          getSelected=True)
        else:
            pass

        self.document = self.documentsDict[self.currentDoc]

        # Check that the user hasn't selected the header
        if (selectedText == 'Drift time (2D, EIC)' or
            selectedText == 'Drift time (2D, combined voltages, EIC)' or
            selectedText == 'Drift time (2D, processed, EIC)' or
                selectedText == 'Input data'):
            # Give an error
            dlgBox(exceptionTitle='Error',
                   exceptionMsg="Please select an ion in the Document Panel to assign a charge state",
                   type="Error")
            return

        currentCharge = self.view.panelDocuments.documents.onGetItemData(dataType='charge')

        charge = dlgAsk('Assign charge state to selected item.',
                        defaultValue=str(currentCharge))

        if charge == '' or charge == 'None':
            return

        # Replace data in the dictionary
        if selectedText is None:
            self.document.IMS2D['charge'] = str2int(charge)
        elif selectedText == 'Drift time (2D)':
            self.document.IMS2D['charge'] = str2int(charge)
        elif selectedText == 'Drift time (2D, processed)':
            self.document.IMS2Dprocess['charge'] = str2int(charge)
        elif selectedItemParentText == 'Drift time (2D, EIC)' and selectedText is not None:
            self.document.IMS2Dions[selectedText]['charge'] = str2int(charge)
        elif selectedItemParentText == 'Drift time (2D, combined voltages, EIC)' and selectedText is not None:
            self.document.IMS2DCombIons[selectedText]['charge'] = str2int(charge)
        elif selectedItemParentText == 'Drift time (2D, processed, EIC)' and selectedText is not None:
            self.document.IMS2DionsProcess[selectedText]['charge'] = str2int(charge)
        elif selectedItemParentText == 'Input data' and selectedText is not None:
            self.document.IMS2DcompData[selectedText]['charge'] = str2int(charge)
        elif selectedItemParentText == 'Chromatograms (combined voltages, EIC)' and selectedText is not None:
            self.document.IMSRTCombIons[selectedText]['charge'] = str2int(charge)
        elif selectedItemParentText == 'Drift time (1D, EIC)' and selectedText is not None:
            self.document.IMS1DdriftTimes[selectedText]['charge'] = str2int(charge)
        else:
            self.document.IMS2D

        # Since charge state is inherent to the m/z range, it needs to be
        # changed iteratively for each dataset
        if any(selectedItemParentText in type for type in ['Drift time (2D, EIC)',
                                                           'Drift time (2D, combined voltages, EIC)',
                                                           'Drift time (2D, processed, EIC)',
                                                           'Chromatograms (combined voltages, EIC)',
                                                           'Drift time (1D, EIC)']):
            if selectedText in self.document.IMS2Dions:
                self.document.IMS2Dions[selectedText]['charge'] = str2int(charge)
            if selectedText in self.document.IMS2DCombIons:
                self.document.IMS2DCombIons[selectedText]['charge'] = str2int(charge)
            if selectedText in self.document.IMS2DionsProcess:
                self.document.IMS2DionsProcess[selectedText]['charge'] = str2int(charge)
            if selectedText in self.document.IMSRTCombIons:
                self.document.IMSRTCombIons[selectedText]['charge'] = str2int(charge)
            if selectedText in self.document.IMS1DdriftTimes:
                self.document.IMS1DdriftTimes[selectedText]['charge'] = str2int(charge)
            # Only to MANUAL data type
            for key in self.document.IMS1DdriftTimes:
                splitText = re.split('-| |,|', key)
                if '-'.join([splitText[0], splitText[1]]) == selectedText:
                    self.document.IMS1DdriftTimes[key]['charge'] = str2int(charge)

            # We also have to check if there is data in the table
            if self.document.dataType == 'Type: ORIGAMI' or self.document.dataType == 'Type: MANUAL':
                splitText = re.split('-| |,|', selectedText)
                row = self.view.panelMultipleIons.findItem(splitText[0], splitText[1], self.currentDoc)
                if row is not None:
                    self.view.panelMultipleIons.peaklist.SetStringItem(index=row,
                                                                       col=self.config.peaklistColNames['charge'],
                                                                       label=str(charge))

        # Append to list
        self.documentsDict[self.document.title] = self.document

    def normalize_colormap(self, data, min=0, mid=50, max=100, cbarLimits=None):
        """
        This function alters the colormap intensities
        """
        # Check if cbarLimits have been adjusted
        if cbarLimits is not None and self.config.colorbar:
            maxValue = self.config.colorbarRange[1]
        else:
            maxValue = np.max(data)

        # Determine what are normalization values
        # Convert from % to number
        cmapMin = (maxValue * min) / 100
        cmapMid = (maxValue * mid) / 100
        cmapMax = (maxValue * max) / 100

        cmapNormalization = MidpointNormalize(midpoint=cmapMid,
                                              vmin=cmapMin,
                                              vmax=cmapMax,
                                              clip=False)
        return cmapNormalization

    def onOpenPeakListCSV(self, evt):
        """
        This function opens a formatted CSV file with peaks
        """
        dlg = wx.FileDialog(self.view, "Choose a text file (m/z, window size, charge):",
                            wildcard="*.csv;*.txt",
                            style=wx.FD_DEFAULT_STYLE | wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_CANCEL:
            return
        else:
            # Create shortcut
            tempList = self.view.panelMultipleIons.peaklist
            delimiter, __ = checkExtension(input=dlg.GetPath().encode('ascii', 'replace'))
            peaklist = pd.read_csv(dlg.GetPath(), delimiter=delimiter)
            try:
                peaklist['m/z']
            except KeyError:
                msg = "Please make sure your file contains headers. i.e. m/z | window | z (optional)"
                dlgBox(exceptionTitle='Incorrect input',
                       exceptionMsg=msg,
                       type="Error")
                return
            for peak in range(len(peaklist)):

                # Determine window size
                if self.config.useInternalMZwindow:
                    mzAdd = self.config.mzWindowSize
                else:
                    try:
                        mzAdd = peaklist['window'][peak]
                    except KeyError:
                        msg = "Please make sure your file contains headers. i.e. m/z | window | z (optional)"
                        dlgBox(exceptionTitle='Incorrect input',
                               exceptionMsg=msg,
                               type="Error")
                        return
                # Generate mz start/end
                mzMin = np.round((peaklist['m/z'][peak] - mzAdd), 2)
                mzMax = np.round((peaklist['m/z'][peak] + mzAdd), 2)
                # Get charge of ion
                try:
                    charge = peaklist['z'][peak]
                except KeyError:
                    charge = ''
                # Get label of the ion
                try:
                    label = peaklist['label'][peak]
                except KeyError:
                    label = ''
                tempList.Append([str(mzMin), str(mzMax), str(charge), '', '', '', '', '', str(label)])
        self.view.onPaneOnOff(evt=ID_window_ionList, check=True)
        dlg.Destroy()

        if evt is not None:
            evt.Skip()

#     def onUpdateColormap(self, evt=None):
#         """
#         Updates colormap for current document
#         """
#         self.currentDoc = self.view.panelDocuments.documents.enableCurrentDocument()
#         if not self.currentDoc:
#             document = None
#         elif self.currentDoc == 'Current documents':
#             return
#         else:
#             document = self.documentsDict[self.currentDoc]
#         # Return
#         return document

#     def testXYmaxVals(self, values=None):
#         """
#         This function checks whether the x/y axis labels should be adjusted (divided)
#         to adjust their size
#         """
#         if not hasattr(values, "__len__"):
#             if 10000 < values <= 1000000:
#                 divider = 1000
#             elif values > 1000000:
#                 divider = 1000000
#             else:
#                 divider = 1
#         elif 10000 < max(values) <= 1000000:
#             divider = 1000
#         elif  max(values) > 1000000:
#             divider = 1000000
#         else:
#             divider = 1
#         return divider
#     def onDocumentColour(self, evt):
#         """Get new colour"""
#         try:
#             self.currentDoc = self.view.panelDocuments.documents.enableCurrentDocument()
#         except Exception:
#             return None
#         if self.currentDoc == 'Current documents':
#             return
#
#         document = self.documentsDict[self.currentDoc]
#         # Check document
#         if not self.documentsDict:
#             wx.Bell()
#             return
#
#         # Show dialog and get new colour
#         dlg = wx.ColourDialog(self.view)
#         dlg.GetColourData().SetChooseFull(True)
#         if dlg.ShowModal() == wx.ID_OK:
#             data = dlg.GetColourData()
#             newColour = list(data.GetColour().Get())
#             document.lineColour = list([np.float(newColour[0]) / 255,
#                                         np.float(newColour[1]) / 255,
#                                         np.float(newColour[2]) / 255])
#             dlg.Destroy()
#         else:
#             return
#
# #         self.view.panelControls.colorBtn.SetBackgroundColour(newColour)
#         # Update plot
#         self.view.panelDocuments.documents.onShowPlot()

    # TODOO: move to another panel
#     def onSelectProtein(self, evt):
#         if evt.GetId() == ID_selectCalibrant:
#             mode = 'calibrants'
#         else:
#             mode = 'proteins'
#
#         self.selectProteinDlg = panelCalibrantDB(self.view, self, self.config, mode)
#         self.selectProteinDlg.Show()

    # def onAddCalibrant(self, path=None, mzStart=None, mzEnd=None, mzCentre=None,
    #                    pusherFreq=None, tDout=False, e=None):
    #     """
    #     Extract and plot 1DT information for selected m/z range
    #     """

    #     # Figure out what is the current document
    #     self.currentDoc = self.view.panelDocuments.documents.enableCurrentDocument()
    #     if self.currentDoc == 'Current documents':
    #         return
    #     document = self.documentsDict[self.currentDoc]

    #     # Determine the m/z range to extract
    #     extract_kwargs = {'return_data': True}
    #     __, yvalsDT = io_waters.driftscope_extract_DT(path=path,
    #                                                    driftscope_path=self.config.driftscopePath,
    #                                                    mz_start=mzStart, mz_end=mzEnd
    #                                                    ** extract_kwargs)
    #     mphValue = (max(yvalsDT)) * 0.2  # 20 % cutoff

    #     if pusherFreq != 1:
    #         xlabel = 'Drift time (ms)'
    #     else:
    #         xlabel = 'Drift time (bins)'
    #     # Create x-labels in ms
    #     xvalsDT = (np.arange(1, len(yvalsDT) + 1) * pusherFreq) / 1000

    #     # Detect peak
    #     ind = detectPeaks(x=yvalsDT, mph=mphValue)
    #     if len(ind) > 1:
    #         self.onThreading(None, ('Found more than one peak. Selected the first one', 4), action='updateStatusbar')
    #         tD = np.round(xvalsDT[ind[0]], 2)
    #         yval = np.round(yvalsDT[ind[0]], 2)
    #         yval = pr_spectra.normalize_1D(yval)  # just puts it in the middle of the peak
    #     elif len(ind) == 0:
    #         self.onThreading(None, ('Found no peaks', 4), action='updateStatusbar')
    #         tD = ""
    #     else:
    #         tD = np.round(xvalsDT[ind[0]], 2)
    #         yval = np.round(yvalsDT[ind[0]], 2)
    #         yval = pr_spectra.normalize_1D(yval)  # just puts it in the middle of the peak

    #     # Add data to document
    #     protein, charge, CCS, gas, mw = None, None, None, None, None

    #     # Check whether the document has molecular weight
    #     mw = document.moleculeDetails.get('molWeight', None)
    #     protein = document.moleculeDetails.get('protein', None)

    #     document.gotCalibration = True
    #     rangeName = ''.join([str(mzStart), '-', str(mzEnd)])
    #     document.calibration[rangeName] = {'xrange': [mzStart, mzEnd],
    #                                        'xvals': xvalsDT,
    #                                        'yvals': yvalsDT,
    #                                        'xcentre': ((mzEnd + mzStart) / 2),
    #                                        'protein': protein,
    #                                        'charge': charge,
    #                                        'ccs': CCS,
    #                                        'tD': tD,
    #                                        'gas': gas,
    #                                        'xlabels': xlabel,
    #                                        'peak': [tD, yval],
    #                                        'mw': mw
    #                                        }
    #     # Plot
    #     self.onPlot1DTCalibration(dtX=xvalsDT,
    #                               dtY=yvalsDT,
    #                               xlabel='Drift time (ms)',
    #                               color=document.lineColour)

    #     if tD != "":
    #         self.addMarkerMS(xvals=tD,
    #                          yvals=yval,
    #                          color=self.config.annotColor,
    #                          marker=self.config.markerShape,
    #                          size=self.config.markerSize,
    #                          plot='CalibrationDT')

    #     self.view.panelDocuments.documents.add_document(docData=document)
    #     self.documentsDict[document.title] = document
    #     if tDout:
    #         return tD

#     def OnBuildCCSCalibrationDataset(self, evt):
#
#         # Create temporary dictionary
#         tempDict = {}
#         self.currentCalibrationParams = []
#
#         # Shortcut to the table
#         tempList = self.view.panelCCS.topP.peaklist
#         if tempList.GetItemCount() == 0:
#             self.onThreading(
#                 None,
#                 ('Cannot build calibration curve as the calibration list is empty. Load data first.',
#      4),
#                 action='updateStatusbar')
#         try:
#             self.currentDoc = self.view.panelDocuments.documents.enableCurrentDocument()
#         except Exception:
#             return
#         if self.currentDoc == "Current documents":
#             return
#
#         # Check if the currently selected document is Calibration dataframe file
#         if (self.documentsDict[self.currentDoc].dataType == 'Type: CALIBRANT' and
#                 self.documentsDict[self.currentDoc].fileFormat == 'Format: DataFrame'):
#             self.docs = self.documentsDict[self.currentDoc]
#             self.view.SetStatusText('Using document: ' + self.docs.title.encode('ascii', 'replace'), 3)
#         else:
#             self.onThreading(None, ('Checking if there is a calibration document', 4), action='updateStatusbar')
#             docList = self.checkIfAnyDocumentsAreOfType(type='Type: CALIBRANT',
#                                                         format='Format: DataFrame')
#             if len(docList) == 0:
#                 self.onThreading(
#                     None,
#                     ('Did not find appropriate document. Creating a new one...',
#      4),
#                     action='updateStatusbar')
#                 dlg = wx.FileDialog(self.view, "Please select a name for the calibration document",
#                                     "", "", "", wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
#                 if dlg.ShowModal() == wx.ID_OK:
#                     path, idName = os.path.split(dlg.GetPath())
#                 else:
#                     return
#
#                 # Create document
#                 self.docs = documents()
#                 self.docs.title = idName
#                 self.docs.path = path
#                 self.docs.userParameters = self.config.userParameters
#                 self.docs.userParameters['date'] = getTime()
#                 self.docs.dataType = 'Type: CALIBRANT'
#                 self.docs.fileFormat = 'Format: DataFrame'
#             else:
#                 self.selectDocDlg = panelSelectDocument(self.view, self, docList)
#                 if self.selectDocDlg.ShowModal() == wx.ID_OK:
#                     pass
#
#                 # Check that document exists
#                 if self.currentDoc is None:
#                     self.view.SetStatusText('Please select CCS calibration document', 3)
#                     return
#
#                 self.docs = self.documentsDict[self.currentDoc]
#                 self.view.SetStatusText('Using document: ' + self.docs.title.encode('ascii', 'replace'), 3)
#
#         selectedIon = None
#         calibrationDict = {}
#         # Update CCS dataset
#         for caliID in range(tempList.GetItemCount()):
#             # Only add info if dataset was checked
#             if tempList.IsChecked(index=caliID):
#                 # Get document info
#                 selectedItem = tempList.GetItem(caliID, self.config.ccsTopColNames['filename']).GetText()
#                 mzStart = tempList.GetItem(caliID, self.config.ccsTopColNames['start']).GetText()
#                 mzEnd = tempList.GetItem(caliID, self.config.ccsTopColNames['end']).GetText()
#                 selectedIon = ''.join([str(mzStart), '-', str(mzEnd)])
#                 document = self.documentsDict[selectedItem]
#                 # Add to dictionary
#                 calibrationDict[selectedIon] = document.calibration[selectedIon]
#                 self.docs.gotCalibration = True
#                 self.docs.calibration[selectedIon] = calibrationDict[selectedIon]
#
#         if len(calibrationDict) == 0:
#             self.view.SetStatusText('The calibration dictionary was empty. Select items in the table first', 3)
#             return
#
#         if selectedIon is None:
#             self.view.SetStatusText('Please select items in the table - otherwise CCS calibration cannot be created', 3)
#             return
#
#         # Determine what gas is used - selects it based on the last value in the list
#         gas = self.config.elementalMass[calibrationDict[selectedIon]['gas']]
#         self.docs.gas = gas
#
#         # Determine the c correction factor
#         if isempty(self.docs.corrC):
#             self.view.SetStatusText(
#                 'Missing TOF correction factor - you can modify the value in the Document Information Panel', 3)
#             return
#
#         # Build dataframe
#         df = pd.DataFrame(columns=['m/z', 'z', 'tD', 'MW', 'CCS', 'RedMass', 'tDd', 'CCSd', 'lntDd',
#                                    'lnCCSd', 'tDdd'],
#                           index=np.arange(0, len(calibrationDict)))
#
#         # Populate dataframe
#         for i, key in enumerate(calibrationDict):
#             charge = calibrationDict[key]['charge']
#             ccs = calibrationDict[key]['ccs']
#             tD = calibrationDict[key]['tD']
#             if not isnumber(charge) or not isnumber(ccs) or not isnumber(tD):
#                 continue
#             else:
#                 if isnumber(calibrationDict[key]['mw']):
#                     xcentre = ((self.config.elementalMass['Hydrogen'] * charge) +
#                                calibrationDict[key]['mw'] / charge)
#                 else:
#                     xcentre = calibrationDict[key]['xcentre']
#                 df['m/z'].loc[i] = xcentre
#                 df['z'].loc[i] = charge
#                 df['CCS'].loc[i] = ccs
#                 df['tD'].loc[i] = tD
#
#         # Remove rows with NaNs
#         df = df.dropna(how='all')
#         if len(df) == 0:
#             self.view.SetStatusText('Please make sure you fill in appropriate parameters', 3)
#             return
#
#         # Compute variables
#         df['MW'] = (df['m/z'] - (self.config.elementalMass['Hydrogen'] * df['z'])) * \
#         df['z']  # calculate molecular weight
#         df['RedMass'] = ((df['MW'] * self.docs.gas) / (df['MW'] + self.docs.gas))  # calculate reduced mass
#         df['tDd'] = (df['tD'] - ((self.docs.corrC * df['m/z'].apply(sqrt)) / 1000))  # corrected drift time
#         df['CCSd'] = df['CCS'] / (df['z'] * (1 / df['RedMass']).apply(sqrt))  # corrected ccs
#         df['lntDd'] = df['tDd'].apply(log)  # log drift time
#         df['lnCCSd'] = df['CCSd'].apply(log)  # log ccs
#
#         # Compute linear regression properties
#         outLinear = linregress(df['tDd'].astype(np.float64), df['CCSd'].astype(np.float64))
#         slopeLinear, interceptLinear = outLinear[0], outLinear[1]
#         r2Linear = outLinear[2] * outLinear[2]
#
#         # Compute power regression properties
#         out = linregress(df['lntDd'], df['lnCCSd'])
#         slope, intercept = out[0], out[1]
#         df['tDdd'] = df['tDd'].pow(slope) * df['z'] * df['RedMass'].apply(sqrt)
#
#         outPower = linregress(df['tDdd'].astype(np.float64), df['CCS'].astype(np.float64))
#         slopePower, interceptPower = outPower[0], outPower[1]
#         r2Power = outPower[2] * outPower[2]
#
#         # Add logarithmic method
#
#         df.fillna('')
#         calibrationParams = {'linear': [slopeLinear, interceptLinear, r2Linear],
#                              'power': [slopePower, interceptPower, r2Power],
#                              'powerParms': [slope, intercept],
#                              'gas': gas}
#
#         # Add calibration DataFrame to document
#         self.docs.gotCalibrationParameters = True
#         self.docs.calibrationParameters = {'dataframe': df,
#                                            'parameters': calibrationParams}
#
#         # Calibration fit line
#         xvalsLinear, yvalsLinear = pr_spectra.abline(np.asarray((df.tDd.min(), df.tDd.max())),
#                                                      slopeLinear, interceptLinear)
#         xvalsPower, yvalsPower = pr_spectra.abline(np.asarray((df.tDdd.min(), df.tDdd.max())),
#                                                    slopePower, interceptPower)
#         # Plot data
#         # TODO: need to check this is correct
# #         self.onPlotCalibrationCurve(xvals1=df['tDd'], yvals1=df['CCSd'], label1='Linear',
# #                                     xvalsLinear=xvalsLinear, yvalsLinear=yvalsLinear,
# #                                     xvals2=df['tDdd'], yvals2=df['CCS'], label2='Power',
# #                                     xvalsPower=xvalsPower, yvalsPower=yvalsPower,
# #                                     color='red', marker='o')
#
#         # Append to list
#         self.documentsDict[self.docs.title] = self.docs
#         # Update documents tree
#         self.view.panelDocuments.documents.add_document(docData=self.docs)
#
#         # Set current calibration parameters
#         self.currentCalibrationParams = self.docs.calibrationParameters
#
#         self.view.SetStatusText(''.join(['R² (linear): ', str(np.round(r2Linear, 4)),
#                                          ' | R² (power): ', str(np.round(r2Power, 4)), ]), 3)
#
# #     def OnApplyCCSCalibrationToSelectedIons(self, evt):
# #
# #         # Shortcut to the table
# #         tempList = self.view.panelCCS.bottomP.peaklist
# #         calibrationMode = self.view.panelCCS.bottomP.calibrationMode.GetStringSelection()
# #         for caliID in range(tempList.GetItemCount()):
# #             # Only add info if dataset was checked
# #             if tempList.IsChecked(index=caliID):
# #                 # Get document info
# #                 filename = tempList.GetItem(caliID, self.config.ccsBottomColNames['filename']).GetText()
# #                 mzStart = tempList.GetItem(caliID, self.config.ccsBottomColNames['start']).GetText()
# #                 mzEnd = tempList.GetItem(caliID, self.config.ccsBottomColNames['end']).GetText()
# #                 charge = str2int(tempList.GetItem(caliID, self.config.ccsBottomColNames['charge']).GetText())
# #                 mzCentre = str2num(tempList.GetItem(caliID, self.config.ccsBottomColNames['ion']).GetText())
# #                 selectedType = tempList.GetItem(caliID, self.config.ccsBottomColNames['format']).GetText()
# #                 rangeName = ''.join([str(mzStart), '-', str(mzEnd)])
# #
# #                 # Check these fields were filled in
# #                 if isempty(charge) or isempty(mzCentre):
# #                     msg = 'Please fill in the fields'
# #                     self.view.SetStatusText(msg, 3)
# #                     return
# #                 elif charge == 0:
# #                     msg = "%s (%s) is missing charge value. Please add charge information before trying to apply CCS calibration" % (
# #                         rangeName, filename)
# #                     dlgBox(exceptionTitle='Missing charge information',
# #                            exceptionMsg=msg,
# #                            type="Warning")
# #                     continue
# #                 # Get document object based on the filename
# #                 document = self.documentsDict[filename]
# #
# #                 # Select data based on the format of the object
# #                 if selectedType == '2D, extracted':
# #                     data = document.IMS2Dions[rangeName]
# #                 elif selectedType == '2D, combined':
# #                     data = document.IMS2DCombIons[rangeName]
# #                 elif selectedType == '2D, processed':
# #                     data = document.IMS2DionsProcess[rangeName]
# #
# #                 # Unpack data
# #                 zvals, xvals, xlabel, yvals, ylabel, charge, mw, mzCentre = self.get2DdataFromDictionary(
# #                     dictionary=data, dataType='calibration', compact=False)
# #                 # Check that the object has pusher frequency
# #                 pusherFreq = document.parameters.get('pusherFreq', 1)
# #
# #                 if (pusherFreq == 1 or not isnumber(pusherFreq)) and ylabel != 'Drift time (ms)':
# #                     msg = "%s (%s) ion is missing pusher frequency value. Please modify it in the Notes, Information and Labels panel" % (
# #                         filename, rangeName)
# #                     dlgBox(exceptionTitle='Missing data',
# #                            exceptionMsg=msg,
# #                            type="Error")
# #                     continue
# #                 # Check if ylabel is in ms
# #                 if ylabel != 'Drift time (ms)':
# #                     if ylabel == 'Drift time (bins)':
# #                         yvals = yvals * (pusherFreq / 1000)
# #                     else:
# #                         # Need to restore scans and convert them to ms
# #                         yvals = 1 + np.arange(len(zvals[:, 1]))
# #                         yvals = yvals * (pusherFreq / 1000)
# #
# #                 # Check for TOF correction factor
# #                 if isempty(document.corrC) and document.parameters.get('corrC', None) is None:
# #                     msg = 'Missing TOF correction factor'
# #                     self.view.SetStatusText(msg, 3)
# #                     return
# #
# #                 # Check for charge and m/z information
# #                 if not isnumber(charge) or not isnumber(mzCentre):
# #                     if not isnumber(charge):
# #                         msg = 'Missing charge information'
# #                     elif not isnumber(mzCentre):
# #                         msg = 'Missing m/z information'
# #                     self.view.SetStatusText(msg, 3)
# #                     return
# #
# #                 # Create empty DataFrame to calculate CCS
# #                 df = pd.DataFrame(columns=['m/z', 'z', 'tD', 'MW', 'RedMass', 'tDd', 'tDdd'],
# #                                   index=np.arange(0, len(yvals)))
# #                 df['m/z'] = float(mzCentre)
# #                 df['z'] = int(charge)
# #                 df['tD'] = yvals
# #
# #                 # Unpack calibration parameters
# #                 if len(self.currentCalibrationParams) == 0:
# #                     if document.gotCalibrationParameters:
# #                         self.currentCalibrationParams = document.calibrationParameters
# #
# #                 # Now assign the calibration parameters
# #                 try:
# #                     calibrationParameters = self.currentCalibrationParams.get('parameters', None)
# #                 except (IndexError, KeyError):
# #                     calibrationParameters = None
# #
# #                 if calibrationParameters is None:
# #                     # TODO: add function to search for calibration document
# #                     docList = self.checkIfAnyDocumentsAreOfType(type='Type: CALIBRANT',
# #                                                                 format='Format: DataFrame')
# #                     if len(docList) == 0:
# #                         msg = "Cound not find calibration document or calibration file. Please create or load one in first"
# #                         dlgBox(exceptionTitle='Missing data',
# #                                exceptionMsg=msg,
# #                                type="Error")
# #                         return
# #                     else:
# #                         self.selectDocDlg = panelSelectDocument(self.view, self, docList, allowNewDoc=False)
# #                         if self.selectDocDlg.ShowModal() == wx.ID_OK:
# #                             calibrationParameters = self.currentCalibrationParams.get('parameters', None)
# #                             if calibrationParameters is None:
# #                                 return
# #                         return
# #
# #                 # Get parameters
# #                 slopeLinear, interceptLinear, r2Linear = calibrationParameters['linear']
# #                 slopePower, interceptPower, r2Power = calibrationParameters['power']
# #                 slope, intercept = calibrationParameters['powerParms']
# #                 gas = calibrationParameters['gas']
# #
# #                 # Fill in remaining details
# #                 df['MW'] = (df['m/z'] - (self.config.elementalMass['Hydrogen'] * df['z'])) * df['z']
# #                 df['RedMass'] = ((df['MW'] * gas) / (df['MW'] + gas))
# #                 df['tDd'] = (df['tD'] - ((document.corrC * df['m/z'].apply(sqrt)) / 1000))
# #
# #                 # Linear law
# #                 df['CCSd'] = slopeLinear * df['tDd'] + interceptLinear
# #                 df['CCSlinear'] = df['CCSd'] * (df['z'] * (1 / df['RedMass']).apply(sqrt))
# #                 # Power law
# #                 df['tDdd'] = df['tDd'].pow(slope) * df['z'] * df['RedMass'].apply(sqrt)
# #                 df['CCSpower'] = (df['tDdd'] * slopePower) + interceptPower
# #
# #                 # Update dictionary
# #                 document.gotCalibrationParameters = True
# #                 document.calibrationParameters = self.currentCalibrationParams
# #                 document.calibrationParameters['mode'] = calibrationMode
# #
# #                 document.gas = gas
# #
# #                 if calibrationMode == 'Linear':
# #                     ccsVals = pd.to_numeric(df['CCSlinear']).values
# #                 elif calibrationMode == 'Power':
# #                     ccsVals = pd.to_numeric(df['CCSpower']).values
# #
# #                 # Assign data
# #                 if selectedType == '2D, extracted':
# #                     document.IMS2Dions[rangeName]['yvals'] = ccsVals
# #                     document.IMS2Dions[rangeName]['yvalsCCSBackup'] = ccsVals
# #                     document.IMS2Dions[rangeName]['ylabels'] = 'Collision Cross Section (Å²)'
# #                 elif selectedType == '2D, combined':
# #                     document.IMS2DCombIons[rangeName]['yvals'] = ccsVals
# #                     document.IMS2DCombIons[rangeName]['yvalsCCSBackup'] = ccsVals
# #                     document.IMS2DCombIons[rangeName]['ylabels'] = 'Collision Cross Section (Å²)'
# #                 elif selectedType == '2D, processed':
# #                     document.IMS2DionsProcess[rangeName]['yvals'] = ccsVals
# #                     document.IMS2DionsProcess[rangeName]['yvalsCCSBackup'] = ccsVals
# #                     document.IMS2DionsProcess[rangeName]['ylabels'] = 'Collision Cross Section (Å²)'
# #
# #                 # Assign updated to dictionary
# #                 self.documentsDict[document.title] = document
# #
# #                 # Update documents tree
# #                 self.view.panelDocuments.documents.add_document(docData=document)
# #
# #         # Update status bar
# #         try:
# #             self.view.SetStatusText(''.join(['R² (linear): ', str(np.round(r2Linear, 4)),
# #                                              ' | R² (power): ', str(np.round(r2Power, 4)),
# #                                              ' | Used: ', calibrationMode, ' mode']), 3)
# #         except Exception:            pass
# #
# #     def OnAddDataToCCSTable(self, filename=None, mzStart=None, mzEnd=None,
# #                             mzCentre=None, charge=None, protein=None,
# #                             format=None, evt=None):
# #         """
# #         Add data to table and prepare DataFrame for CCS calibration
# #         """
# #         # Shortcut to the table
# #         tempList = self.view.panelCCS.bottomP.peaklist
# #
# #         # Add data to table
# #         tempList.Append([filename, mzStart, mzEnd,
# #                          mzCentre, protein, charge, format])
# #
# #         # Remove duplicates
# #         self.view.panelCCS.bottomP.onRemoveDuplicates(evt=None)
# #         # Enable and show CCS table
# #         self.view.onPaneOnOff(evt=ID_window_ccsList, check=True)
# #
# #     def saveCCScalibrationToPickle(self, evt):
# #         """
# #         Save CCS calibration parameters to file
# #         """
# #         try:
# #             self.currentDoc = self.view.panelDocuments.documents.enableCurrentDocument()
# #         except Exception:            return
# #         if self.currentDoc == "Current documents":
# #             return
# #
# #         # Check if the currently selected document is Calibration dataframe file
# #         if (self.documentsDict[self.currentDoc].dataType == 'Type: CALIBRANT' and
# #                 self.documentsDict[self.currentDoc].fileFormat == 'Format: DataFrame'):
# #             self.docs = self.documentsDict[self.currentDoc]
# #             self.view.SetStatusText('Using document: ' + self.docs.title.encode('ascii', 'replace'), 3)
# #         else:
# #             docList = self.checkIfAnyDocumentsAreOfType(type='Type: CALIBRANT',
# #                                                         format='Format: DataFrame')
# #             if len(docList) == 0:
# #                 print('Did not find appropriate document.')
# #                 return
# #             else:
# #                 self.DocDlg = panelSelectDocument(self.view, self, docList, allowNewDoc=False)
# #                 if self.selectDocDlg.ShowModal() == wx.ID_OK:
# #                     pass
# #
# #                 # Check that document exists
# #                 if self.currentDoc is None:
# #                     self.view.SetStatusText('Please select CCS calibration document', 3)
# #                     return
# #
# #                 self.docs = self.documentsDict[self.currentDoc]
# #                 self.view.SetStatusText('Using document: ' + self.docs.title.encode('ascii', 'replace'), 3)
# #
# #         # Get calibration parameters
# #         # Unpack calibration parameters
# #         if len(self.currentCalibrationParams) == 0:
# #             if self.docs.gotCalibrationParameters:
# #                 self.currentCalibrationParams = self.docs.calibrationParameters
# #
# #         # Save parameters
# #         fileType = "ORIGAMI Document File|*.pickle"
# #         dlg = wx.FileDialog(self.view, "Save CCS calibration to file...", "", "", fileType,
# #                             wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
# #         defaultFilename = self.docs.title.split(".")
# #         defaultFilename = "".join([defaultFilename[0], '_CCScaliParams'])
# #         dlg.SetFilename(defaultFilename)
# #
# #         if dlg.ShowModal() == wx.ID_OK:
# #             saveFileName = dlg.GetPath()
# #             # Save
# #             saveObject(filename=saveFileName, saveFile=self.currentCalibrationParams)
# #         else:
# #             return

    def onUserDefinedListImport(self, evt):
        """ Load a csv file with CV/SPV values for the List/User-defined method"""
        dlg = wx.FileDialog(self.view, "Choose a text file:", wildcard="*.csv",
                            style=wx.FD_DEFAULT_STYLE | wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            print("You chose %s" % dlg.GetPath())

            origamiList = np.genfromtxt(dlg.GetPath(), delimiter=',', skip_header=True)
            self.config.origamiList = origamiList

        dlg.Destroy()

#     def onImportCCSDatabase(self, evt, onStart=False):
#
#         if not onStart:
#             dlg = wx.FileDialog(self.view, "Choose a CCS database file:", wildcard="*.csv",
#                                 style=wx.FD_DEFAULT_STYLE | wx.FD_CHANGE_DIR)
#             if dlg.ShowModal() == wx.ID_OK:
#                 print("You chose %s" % dlg.GetPath())
#
#                 # Open database
#                 self.config.ccsDB = io_text.text_ccs_database_open(dlg.GetPath())
#         else:
#             self.config.ccsDB = io_text.text_ccs_database_open(
#                 filename=os.path.join(self.config.cwd, "example_files", "calibrantDB.csv"))
#             print('Loaded CCS database')

    def onProcessMultipleTextFiles(self, evt):

        if evt.GetId() == ID_textPanel_process_all:
            self.view.panelMultipleText.OnCheckAllItems(evt=None, override=True)

        tempList = self.view.panelMultipleText.peaklist
        try:
            for row in range(tempList.GetItemCount()):
                itemInfo = self.view.panelMultipleText.OnGetItemInformation(itemID=row)
                if itemInfo['select']:
                    self.docs = self.documentsDict[itemInfo['document']]
                    imsData2D = self.data_processing.on_process_2D(zvals=self.docs.IMS2D['zvals'].copy(),
                                                                   return_data=True)
                    self.docs.got2Dprocess = True
                    self.docs.IMS2Dprocess = {'zvals': imsData2D,
                                              'xvals': self.docs.IMS2D['xvals'],
                                              'xlabels': self.docs.IMS2D['xlabels'],
                                              'yvals': self.docs.IMS2D['yvals'],
                                              'ylabels': self.docs.IMS2D['ylabels'],
                                              'cmap': itemInfo['colormap'],
                                              'label': itemInfo['label'],
                                              'charge': itemInfo['charge'],
                                              'alpha': itemInfo['alpha'],
                                              'mask': itemInfo['mask'],
                                              'color': itemInfo['color'],
                                              'min_threshold': itemInfo['min_threshold'],
                                              'max_threshold': itemInfo['max_threshold']}

                    # Update file list
                    self.OnUpdateDocument(self.docs, 'document')
                else:
                    pass
        except Exception:
            print("Cannot process selected items. These belong to Comparison document")
            return

        if evt.GetId() == ID_textPanel_process_all:
            self.view.panelMultipleText.OnCheckAllItems(evt=None, check=False, override=True)

    def onPopulateXaxisTextLabels(self, startVal=None, endVal=None, shapeVal=None):
        """
        This function will check whether specified file has x-axis labels
        present in the dictionary. If not, it will check if x-axis values are
        present in the table. If true, it will generate x-axis labels based
        on the 'Start X', 'End X' and size of the array (shape)
        """
        labels = np.linspace(startVal, endVal, shapeVal)
        return labels

    def checkIfAnyDocumentsAreOfType(self, type=None, format=None):
        """
        This helper function checkes whether any of the documents in the
        document tree/ dictionary are of specified type
        """
        listOfDocs = []
        for key in self.documentsDict:
            if self.documentsDict[key].dataType == type and format is None:
                listOfDocs.append(key)

            elif (self.documentsDict[key].dataType == type and
                  self.documentsDict[key].fileFormat == format):
                listOfDocs.append(key)

            else:
                continue

        return listOfDocs

    def onExtractDToverMZrangeMultiple(self, e):
        # TODO: move this function to data_handling
        """
        Currently this function is not working well. IT doesn't store data in the correct format
        i.e. it only saves ONE RT per charge state which is useless
        Need to do:
        - add to document object to have a sub-tree with each RT for each MZ
        - should be a dictionary with m/z, rts, charge
        """
        # Combine 1DT to array
        initialDoc = self.view.panelDocuments.documents.enableCurrentDocument()

        rtList = self.view.panelLinearDT.topP.peaklist  # List with MassLynx file information
        mzList = self.view.panelLinearDT.bottomP.peaklist  # List with m/z information

        if rtList.GetItemCount() == 0 or mzList.GetItemCount() == 0:
            self.view.SetStatusText('Please make sure you selected regions to extract', 3)
            return
        for mz in range(mzList.GetItemCount()):
            mzStart = str2num(mzList.GetItem(mz, 0).GetText())
            mzEnd = str2num(mzList.GetItem(mz, 1).GetText())
            charge = str2num(mzList.GetItem(mz, 3).GetText())
            # Get document for the ion
#             self.currentDoc = self.view.panelDocuments.documents.enableCurrentDocument()
            self.currentDoc = mzList.GetItem(mz, 4).GetText()
            document = self.documentsDict[self.currentDoc]
            path = document.path
            scantime = document.parameters['scanTime']
            xvals = document.IMS2D['yvals']
            xlabel = document.IMS2D['ylabels']
            # Get height of the peak
            ms = document.massSpectrum
            ms = np.flipud(np.rot90(np.array([ms['xvals'], ms['yvals']])))
            mzYMax = self.view.getYvalue(msList=ms, mzStart=mzStart, mzEnd=mzEnd)
            mzList.SetStringItem(index=mz, col=2, label=str(mzYMax))
            tempArray = []
            driftList = []
            retTimeList = []
            for rt in range(rtList.GetItemCount()):
                # RT has to be in minutes to extract using Driftscope
                rtStart = str2num(rtList.GetItem(rt, 0).GetText())
                rtEnd = str2num(rtList.GetItem(rt, 1).GetText())
                retTimeList.append([int(rtStart), int(rtEnd)])  # create list of RTs to be saved with the document
                rtStart = round(rtStart * (scantime / 60), 2)
                rtEnd = round(rtEnd * (scantime / 60), 2)
                filename = rtList.GetItem(rt, 4).GetText()
                driftVoltage = str2num(rtList.GetItem(rt, 3).GetText())
                if driftVoltage is None:
                    driftVoltage = 0
                if filename != document.title:
                    continue
                self.view.SetStatusText(
                    ''.join(['RT(s): ', str(rtStart), '-', str(rtEnd), ', MS: ', str(mzStart), '-', str(mzEnd)]), 3)
                # Load output
                extract_kwargs = {'return_data': True}
                __, imsData1D = io_waters.driftscope_extract_DT(path=path,
                                                                 driftscope_path=self.config.driftscopePath,
                                                                 mz_start=mzStart, mz_end=mzEnd,
                                                                 rt_start=rtStart, rt_end=rtEnd
                                                                 ** extract_kwargs)
                # Append to output
                tempArray.append(imsData1D)
                driftList.append(driftVoltage)

            # Add data to document object
            ims1Darray = np.array(tempArray)  # combine
            imsData1D = np.sum(ims1Darray, axis=0)
            document.gotExtractedDriftTimes = True
            rangeName = ''.join([str(mzStart), '-', str(mzEnd)])
            document.IMS1DdriftTimes[rangeName] = {'xvals': xvals,
                                                   'yvals': ims1Darray,
                                                   'yvalsSum': imsData1D,
                                                   'xlabels': xlabel,
                                                   'charge': charge,
                                                   'driftVoltage': driftList,
                                                   'retTimes': retTimeList,
                                                   'xylimits': [mzStart, mzEnd, mzYMax]}
            self.documentsDict[self.currentDoc] = document
            self.view.panelDocuments.documents.add_document(docData=document)
        document = self.documentsDict[initialDoc]
        self.view.panelDocuments.documents.add_document(docData=document)

    def get2DdataFromDictionary(self, dictionary=None, dataType='plot',
                                compact=False, plotType='2D'):
        """
        This is a helper function to extract relevant data from dictionary
        Params:
        dictionary: dictionary with 2D data to be examined
        dataType: what data you want to get back
                - plot: only return the minimum required parameters
                - process: plotting + charge state
        """
        if dictionary is None:
            return
        if plotType == '2D':
            # These are always there
            zvals = dictionary['zvals'].copy()
            xvals = dictionary['xvals']
            xlabels = dictionary['xlabels']
            yvals = dictionary['yvals']
            ylabels = dictionary['ylabels']
            cmap = dictionary.get('cmap', self.config.currentCmap)
            charge = dictionary.get('charge', None)
            mw = dictionary.get('mw', None)
            mzCentre = dictionary.get('xcentre', None)

#             if cmap == '' or cmap is None: cmap = 'viridis'
            if dataType == 'all':
                if compact:
                    data = zvals, xvals, xlabels, yvals, ylabels, cmap, charge
                    return data
                else:
                    return zvals, xvals, xlabels, yvals, ylabels, cmap, charge
            elif dataType == 'plot':
                if compact:
                    data = zvals, xvals, xlabels, yvals, ylabels, cmap
                    return data
                else:
                    return zvals, xvals, xlabels, yvals, ylabels, cmap
            elif dataType == 'calibration':
                return zvals, xvals, xlabels, yvals, ylabels, charge, mw, mzCentre
        if plotType == '1D':
            xvals = dictionary['xvals']
            try:
                xlabels = dictionary['xlabels']
            except:
                xlabels = dictionary['xlabel']
            yvals = dictionary['yvals']
            try:
                cmap = dictionary['cmap']
            except KeyError:
                cmap = [0, 0, 0]

            try:
                xlimits = dictionary['xlimits']
            except KeyError:
                xlimits = None
            if dataType == 'plot':
                if compact:
                    data = xvals, yvals, xlabels, cmap
                    return data
                else:
                    return xvals, yvals, xlabels, cmap
        elif plotType == 'Overlay':
            zvals1 = dictionary['zvals1']
            zvals2 = dictionary['zvals2']
            cmapIon1 = dictionary['cmap1']
            cmapIon2 = dictionary['cmap2']
            alphaIon1 = dictionary['alpha1']
            alphaIon2 = dictionary['alpha2']
            xvals = dictionary['xvals']
            xlabel = dictionary['xlabels']
            yvals = dictionary['yvals']
            ylabel = dictionary['ylabels']
            file1 = dictionary['file1']
            file2 = dictionary['file2']
            label1 = dictionary['label1']
            label2 = dictionary['label2']
            try:
                charge1 = dictionary['charge1']
                charge2 = dictionary['charge2']
            except KeyError:
                charge1 = None
                charge2 = None
            if dataType == 'plot':
                if compact:
                    return
                else:
                    return (zvals1, zvals2, cmapIon1, cmapIon2, alphaIon1, alphaIon2, xvals,
                            xlabel, yvals, ylabel, charge1, charge2)
        elif plotType == 'Matrix':
            zvals = dictionary['zvals']
            xylabels = dictionary['matrixLabels']
            cmap = dictionary['cmap']
            return zvals, xylabels, cmap
        elif plotType == 'RMSF':
            zvals = dictionary['zvals']
            yvalsRMSF = dictionary['yvalsRMSF']
            xvals = dictionary['xvals']
            yvals = dictionary['yvals']
            xlabelRMSD = dictionary['xlabelRMSD']
            ylabelRMSD = dictionary['ylabelRMSD']
            ylabelRMSF = dictionary['ylabelRMSF']
            color = dictionary['colorRMSF']
            cmap = dictionary['cmapRMSF']
            rmsdLabel = dictionary['rmsdLabel']
            return zvals, yvalsRMSF, xvals, yvals, xlabelRMSD, ylabelRMSD, ylabelRMSF, color, cmap, rmsdLabel
        elif plotType == 'RMSD':
            zvals = dictionary['zvals']
            xvals = dictionary['xvals']
            xlabels = dictionary['xlabel']
            yvals = dictionary['yvals']
            ylabels = dictionary['ylabel']
            rmsdLabel = dictionary['rmsdLabel']
            cmap = dictionary['cmap']
            return zvals, xvals, xlabels, yvals, ylabels, rmsdLabel, cmap
        elif plotType == 'Overlay1D':
            xvals = dictionary['xvals']
            yvals = dictionary['yvals']
            xlabels = dictionary['xlabel']
            colors = dictionary['colors']
            labels = dictionary['labels']
            xlimits = dictionary.get('xlimits', None)
            return xvals, yvals, xlabels, colors, labels, xlimits

    def getOverlayDataFromDictionary(self, dictionary=None, dataType='plot', compact=False):
        """
        This is a helper function to extract relevant data from dictionary
        Params:
        dictionary: dictionary with 2D data to be examined
        dataType: what data you want to get back
                - plot: only return the minimum required parameters
                - process: plotting + charge state
                - all: return you got
        """
        if dictionary is None:
            return
        # These are always there
        zvals1 = dictionary['zvals1']
        zvals2 = dictionary['zvals2']
        cmap1 = dictionary['cmap1']
        cmap2 = dictionary['cmap2']
        alpha1 = dictionary['alpha1']
        alpha2 = dictionary['alpha2']
        mask1 = dictionary['mask1']
        mask2 = dictionary['mask2']
        label1 = dictionary['label1']
        label2 = dictionary['label2']
        xvals = dictionary['xvals']
        xlabels = dictionary['xlabels']
        yvals = dictionary['yvals']
        ylabels = dictionary['ylabels']
        if dataType == 'plot':
            if compact:
                data = [zvals1, zvals2, cmap1, cmap2, alpha1, alpha2, mask1, mask2, xvals, yvals,
                        xlabels, ylabels]
                return data
            else:
                return zvals1, zvals2, cmap1, cmap2, alpha1, alpha2, mask1, mask2, xvals, yvals, xlabels, ylabels

#     def process2Ddata(self, zvals=None, replot=False, replot_type='2D',
#                       return_data=False, return_all=False, e=None):
#         """
#         Process data - smooth, threshold and normalize 2D data
#         """
#
#         # new in 1.1.0
#         if replot:
#             data = self._get_replot_data(replot_type)
#             zvals = data[0]
#
#         # make sure any data was retrieved
#         if zvals is None:
#             return
#
#         # Check values
#         self.config.onCheckValues(data_type='process')
#         if self.config.processParamsWindow_on_off:
#             self.view.panelProcessData.onSetupValues(evt=None)
#
#         # Smooth data
#         if self.config.plot2D_smooth_mode is not None:
#             if self.config.plot2D_smooth_mode == 'Gaussian':
#                 zvals = pr_heatmap.smooth_gaussian_2D(inputData=zvals.copy(),
#                                                       sigma=self.config.plot2D_smooth_sigma)
#             elif self.config.plot2D_smooth_mode == 'Savitzky-Golay':
#                 zvals = pr_heatmap.smooth_savgol_2D(inputData=zvals,
#                                                     polyOrder=self.config.plot2D_smooth_polynomial,
#                                                     windowSize=self.config.plot2D_smooth_window)
#         else:
#             pass
#         # Threshold
#         zvals = pr_heatmap.remove_noise_2D(inputData=zvals.copy(),
#                                            threshold=self.config.plot2D_threshold)
#         # Normalize
#         if self.config.plot2D_normalize:
#             zvals = pr_heatmap.normalize_2D(inputData=zvals.copy(),
#                                             mode=self.config.plot2D_normalize_mode)
#
#         if replot:
#             xvals, yvals, xlabel, ylabel = data[1::]
#             if replot_type == '2D':
#                 self.view.panelPlots.on_plot_2D(zvals, xvals, yvals, xlabel, ylabel, override=False)
#                 if self.config.waterfall:
#                     self.view.panelPlots.on_plot_waterfall(yvals=xvals, xvals=yvals, zvals=zvals,
#                                                            xlabel=xlabel, ylabel=ylabel)
#                 self.view.panelPlots.on_plot_3D(zvals=zvals, labelsX=xvals, labelsY=yvals,
#                                                 xlabel=xlabel, ylabel=ylabel, zlabel='Intensity')
#                 if not self.config.waterfall:
#                     self.view.panelPlots.mainBook.SetSelection(self.config.panelNames['2D'])
#             elif replot_type == 'DT/MS':
#                 self.view.panelPlots.on_plot_MSDT(zvals, xvals, yvals, xlabel, ylabel, override=False)
#                 self.view.panelPlots.mainBook.SetSelection(self.config.panelNames['MZDT'])
#
#         if return_data:
#             return zvals
#
#         if return_all:
#             parameters = {'smooth_mode': self.config.plot2D_smooth_mode,
#                           'sigma': self.config.plot2D_smooth_sigma,
#                           'polyOrder': self.config.plot2D_smooth_polynomial,
#                           'windowSize': self.config.plot2D_smooth_window,
#                           'threshold': self.config.plot2D_threshold}
#             return zvals, parameters
#
#     def process2Ddata2(self, zvals=None, labelsX=None, e=None, mode='2D'):
#         """
#         Process 2D data - smooth, threshold and normalize 2D data
#         """
#         # Gather info about the file and document
#         selectedItemParentText = None
#         self.currentDoc, selectedItem, selectedText = self.view.panelDocuments.documents.enableCurrentDocument(
#             getSelected=True)
#         indent = self.view.panelDocuments.documents.getItemIndent(selectedItem)
#         if indent > 2:
#             __, selectedItemParentText = self.view.panelDocuments.documents.getParentItem(selectedItem, 2,
#                                                                                           getSelected=True)
#         else:
#             pass
#         self.docs = self.documentsDict[self.currentDoc]
#
#         # Clear current data
#         zvals = None
#         # Based on the selection and indent, data is selected
#         if selectedText == 'Drift time (2D)' and indent == 2:
#             zvals, xvals, xlabel, yvals, ylabel, cmap = self.get2DdataFromDictionary(dictionary=self.docs.IMS2D,
#                                                                                      dataType='plot', compact=False)
#
#         elif selectedText == 'Drift time (processed)' and indent == 2:
#             zvals, xvals, xlabel, yvals, ylabel, cmap = self.get2DdataFromDictionary(dictionary=self.docs.IMS2Dprocess,
#                                                                                      dataType='plot', compact=False)
#
#         elif selectedItemParentText == 'Drift time (2D, EIC)' and indent == 3:
#             zvals, xvals, xlabel, yvals, ylabel, cmap = self.get2DdataFromDictionary(
#                 dictionary=self.docs.IMS2Dions[selectedText], dataType='plot', compact=False)
#
#         elif selectedItemParentText == 'Drift time (2D, processed, EIC)' and indent == 3:
#             zvals, xvals, xlabel, yvals, ylabel, cmap = self.get2DdataFromDictionary(
#                 dictionary=self.docs.IMS2DionsProcess[selectedText], dataType='plot', compact=False)
#
#         elif selectedItemParentText == 'Drift time (2D, combined voltages, EIC)' and indent == 3:
#             zvals, xvals, xlabel, yvals, ylabel, cmap = self.get2DdataFromDictionary(
#                 dictionary=self.docs.IMS2DCombIons[selectedText], dataType='plot', compact=False)
#
#         elif selectedItemParentText == 'Input data' and indent == 3:
#             zvals, xvals, xlabel, yvals, ylabel, cmap = self.get2DdataFromDictionary(
#                 dictionary=self.docs.IMS2DcompData[selectedText], dataType='plot', compact=False)
#
#         elif selectedItemParentText == 'Statistical' and indent == 3:
#             zvals, xvals, xlabel, yvals, ylabel, cmap = self.get2DdataFromDictionary(
#                 dictionary=self.docs.IMS2DstatsData[selectedText], dataType='plot', compact=False)
#         elif selectedText == 'MS vs DT' and indent == 2:
#             zvals, xvals, xlabel, yvals, ylabel, cmap = self.get2DdataFromDictionary(dictionary=self.docs.DTMZ,
#                                                                                      dataType='plot', compact=False)
#         else:
#             self.view.SetStatusText('Not implemented yet', 3)
#
#         if (isempty(zvals) or isempty(xvals) or isempty(xlabel) or isempty(yvals) or isempty(ylabel)):
#             self.view.SetStatusText('Sorry, missing data - cannot perform action', 3)
#             try:
#                 self.checkWhatIsMissing2D(zvals, xvals, xlabel, yvals, ylabel, cmap)
#             except UnboundLocalError:
#                 return
#             return
#
#         # Smooth data
#         if self.config.smoothMode == "None" or self.config.smoothMode == False:
#             pass
#         elif self.config.smoothMode == "Gaussian":
#             sigma = str2num(self.config.gaussSigma.encode('ascii', 'replace'))
#             zvals = pr_heatmap.smooth_gaussian_2D(inputData=zvals, sigma=sigma)
#         elif self.config.smoothMode == "Savitzky-Golay":
#             savgolPoly = str2int(self.config.savGolPolyOrder.encode('ascii', 'replace'))
#             savgolWindow = str2int(self.config.savGolWindowSize.encode('ascii', 'replace'))
#             zvals = pr_heatmap.smooth_savgol_2D(inputData=zvals,
#                                                 polyOrder=savgolPoly,
#                                                 windowSize=savgolWindow)
#         else:
#             pass
#         # Threshold data
#         threshold = str2num(self.config.threshold.encode('ascii', 'replace'))
#
#         if isempty(threshold) or threshold is None or threshold == '':
#             pass
#         else:
#             zvals = pr_heatmap.remove_noise_2D(inputData=zvals, threshold=threshold)
#             threshold = None
#
#         # Normalize data - following previous actions!
#         if self.config.normalize:
#             zvals = pr_heatmap.normalize_2D(inputData=zvals, mode=self.config.normMode)
#
#         # Check and change colormap if necessary
#         cmapNorm = self.normalize_colormap(zvals,
#                                             min=self.config.minCmap,
#                                             mid=self.config.midCmap,
#                                             max=self.config.maxCmap,
#                                             #                                             cbarLimits=self.config.colorbarRange
#                                             )
#
#         # Plot data
#         if mode == '2D':
#             self.view.panelPlots.on_plot_2D(zvals, xvals, yvals, xlabel, ylabel, cmap, cmapNorm=cmapNorm)
#             if self.config.waterfall:
#                 self.view.panelPlots.on_plot_waterfall(yvals=xvals, xvals=yvals, zvals=zvals,
#                                                        xlabel=xlabel, ylabel=ylabel)
#             self.view.panelPlots.on_plot_3D(zvals=zvals, labelsX=xvals, labelsY=yvals,
#                                             xlabel=xlabel, ylabel=ylabel, zlabel='Intensity', cmap=cmap)
#         elif mode == 'MSDT':
#             self.view.panelPlots.on_plot_MSDT(zvals, xvals, yvals, xlabel, ylabel, cmap, cmapNorm=cmapNorm)
#
#     def process_2D(self, document=None, dataset=None, ionName=None):
#         # new in 1.1.0
#         if document is None or dataset is None:
#             self.currentDoc = self.view.panelDocuments.documents.enableCurrentDocument()
#             if self.currentDoc is None or self.currentDoc == "Current documents":
#                 return
#             self.docs = self.documentsDict[self.currentDoc]
#         else:
#             self.docs = self.documentsDict[document]
#
#         # get data
#         if dataset == "Drift time (2D)":
#             data = self.docs.IMS2D
#         elif dataset == "Drift time (2D, processed)":
#             data = self.docs.IMS2Dprocess
#         elif dataset == "Drift time (2D, EIC)":
#             data = self.docs.IMS2Dions[ionName]
#         elif dataset == "Drift time (2D, processed, EIC)":
#             data = self.docs.IMS2DionsProcess[ionName]
#         elif dataset == "Drift time (2D, combined voltages, EIC)":
#             data = self.docs.IMS2DCombIons[ionName]
#         elif dataset == "Input data":
#             data = self.docs.IMS2DcompData[ionName]
#         elif dataset == "Statistical":
#             data = self.docs.IMS2DstatsData[ionName]
#         elif dataset == "DT/MS":
#             data = self.docs.DTMZ
#
#         # unpact data
#         zvals = data['zvals']
#         xvals = data['xvals']
#         yvals = data['yvals']
#         xlabel = data['xlabels']
#         ylabel = data['ylabels']
#
#         zvals, params = self.data_processing.on_process_2D(zvals=zvals.copy(), return_all=True)
#
#         # strip any processed string from the title
#         if ionName is not None:
#             if "(processed)" in ionName:
#                 dataset = ionName.split(" (")[0]
#             new_dataset = "%s (processed)" % ionName
#
#         if dataset == "Drift time (2D)":
#             self.docs.got2Dprocess = True
#             self.docs.IMS2Dprocess = self.docs.IMS2D.copy()
#             self.docs.IMS2Dprocess['zvals'] = zvals
#             self.docs.IMS2Dprocess['process_parameters'] = params
#             self.docs.IMS2D['process_parameters'] = params
#         if dataset == "Drift time (2D, EIC)":
#             self.docs.IMS2Dions[new_dataset] = self.docs.IMS2Dions[ionName].copy()
#             self.docs.IMS2Dions[new_dataset]['zvals'] = zvals
#             self.docs.IMS2Dions[new_dataset]['process_parameters'] = params
#         elif dataset == "Drift time (2D, processed, EIC)":
#             self.docs.IMS2DionsProcess[new_dataset] = self.docs.IMS2DionsProcess[ionName].copy()
#             self.docs.IMS2DionsProcess[new_dataset]['zvals'] = zvals
#             self.docs.IMS2DionsProcess[new_dataset]['process_parameters'] = params
#         elif dataset == "Drift time (2D, combined voltages, EIC)":
#             self.docs.IMS2DCombIons[new_dataset] = self.docs.IMS2DCombIons[ionName].copy()
#             self.docs.IMS2DCombIons[new_dataset]['zvals'] = zvals
#             self.docs.IMS2DCombIons[new_dataset]['process_parameters'] = params
#         elif dataset == "Input data":
#             self.docs.IMS2DcompData[new_dataset] = self.docs.IMS2DcompData[ionName].copy()
#             self.docs.IMS2DcompData[new_dataset]['zvals'] = zvals
#             self.docs.IMS2DcompData[new_dataset]['process_parameters'] = params
#         elif dataset == "Statistical":
#             self.docs.IMS2DstatsData[new_dataset] = self.docs.IMS2DstatsData[ionName].copy()
#             self.docs.IMS2DstatsData[new_dataset]['zvals'] = zvals
#             self.docs.IMS2DstatsData[new_dataset]['process_parameters'] = params
#         elif dataset == "DT/MS":
#             self.docs.DTMZ['zvals'] = zvals
#             self.docs.DTMZ['process_parameters'] = params
#
#         # replot
#         if dataset in ['Drift time (2D)', 'Drift time (2D, processed)',
#                        'Drift time (2D, EIC)', 'Drift time (2D, combined voltages, EIC)',
#                        'Drift time (2D, processed, EIC)', 'Input data', 'Statistical']:
#             self.view.panelPlots.on_plot_2D(zvals, xvals, yvals, xlabel, ylabel, override=False)
#             if self.config.waterfall:
#                 self.view.panelPlots.on_plot_waterfall(yvals=xvals, xvals=yvals, zvals=zvals,
#                                                        xlabel=xlabel, ylabel=ylabel)
#             self.view.panelPlots.on_plot_3D(zvals=zvals, labelsX=xvals, labelsY=yvals,
#                                             xlabel=xlabel, ylabel=ylabel, zlabel='Intensity')
#             # change to correct plot window
#             if not self.config.waterfall:
#                 self.view.panelPlots.mainBook.SetSelection(self.config.panelNames['2D'])
#         elif dataset == "DT/MS":
#             self.view.panelPlots.on_plot_MSDT(zvals, xvals, yvals, xlabel, ylabel)
#             self.view.panelPlots.mainBook.SetSelection(self.config.panelNames['MZDT'])
#
#         # Update file list
#         self.OnUpdateDocument(self.docs, 'document')
#
#     def processMSdata(self, replot=False, msX=None, msY=None, return_data=False,
#                       return_all=False, evt=None):
#         # new in 1.1.0
#         if replot:
#             msX, msY, xlimits = self._get_replot_data('MS')
#             if msX is None or msY is None:
#                 return
#
#         # Check values
#         self.config.onCheckValues(data_type='process')
#         if self.config.processParamsWindow_on_off:
#             self.view.panelProcessData.onSetupValues(evt=None)
#
#         if self.config.ms_process_crop:
#             kwargs = {'min': self.config.ms_crop_min,
#                       'max': self.config.ms_crop_max}
#             msX, msY = pr_spectra.crop_1D_data(msX, msY, **kwargs)
#
#         if self.config.ms_process_linearize and msX is not None:
#             kwargs = {'auto_range': self.config.ms_auto_range,
#                       'mz_min': self.config.ms_mzStart,
#                       'mz_max': self.config.ms_mzEnd,
#                       'mz_bin': self.config.ms_mzBinSize,
#                       'linearization_mode': self.config.ms_linearization_mode}
#             msX, msY = pr_spectra.linearize_data(msX, msY, **kwargs)
#
#         if self.config.ms_process_smooth:
#             # Smooth data
#             kwargs = {'sigma': self.config.ms_smooth_sigma,
#                       'polyOrder': self.config.ms_smooth_polynomial,
#                       'windowSize': self.config.ms_smooth_window}
#             msY = pr_spectra.smooth_1D(data=msY, smoothMode=self.config.ms_smooth_mode, **kwargs)
#
#         if self.config.ms_process_threshold:
#             # Threshold data
#             msY = pr_spectra.remove_noise_1D(inputData=msY, threshold=self.config.ms_threshold)
#
#         if self.config.ms_process_normalize:
#             # Normalize data
#             if self.config.ms_normalize:
#                 msY = pr_spectra.normalize_1D(inputData=np.asarray(msY),
#                                               mode=self.config.ms_normalize_mode)
#
#         if replot:
#             # Plot data
#             kwargsMS = {}
#             self.view.panelPlots.on_plot_MS(msX=msX, msY=msY,
#                                             override=False, **kwargsMS)
#
#         if return_data:
#             if msX is not None:
#                 return msX, msY
#             else:
#                 return msY
#
#         if return_all:
#             parameters = {'smooth_mode': self.config.ms_smooth_mode,
#                           'sigma': self.config.ms_smooth_sigma,
#                           'polyOrder': self.config.ms_smooth_polynomial,
#                           'windowSize': self.config.ms_smooth_window,
#                           'threshold': self.config.ms_threshold}
#             return msX, msY, parameters
#
#     def process_MS(self, document=None, dataset=None):
#
#         if document is None or dataset is None:
#             self.currentDoc = self.view.panelDocuments.documents.enableCurrentDocument()
#             if self.currentDoc is None or self.currentDoc == "Current documents":
#                 return
#             self.docs = self.documentsDict[self.currentDoc]
#         else:
#             self.docs = self.documentsDict[document]
#
#         # select dataset
#         if dataset == 'Mass Spectrum':
#             if self.docs.gotMS:
#                 data = self.docs.massSpectrum
#         else:
#             if self.docs.gotMultipleMS:
#                 data = self.docs.multipleMassSpectrum[dataset]
#
#         # retrieve plot data
#         msX = data['xvals']
#         msY = data['yvals']
#         annotations = data.get('annotations', {})
#         title = data.get('header', "")
#         header = data.get('header', "")
#         footnote = data.get('footnote', "")
#         msX, msY, params = self.processMSdata(msX=msX, msY=msY, return_all=True)
#         xlimits = [np.min(msX), np.max(msX)]
#         ms_data = {'xvals': msX, 'yvals': msY,
#                    'xlabels': 'm/z (Da)',
#                    'parameters': params,
#                    'annotations': annotations, 'title': title,
#                    'header': header, 'footnote': footnote,
#                    'xlimits': xlimits}
#
#         # add data to dictionary
#         if dataset == 'Mass Spectrum':
#             self.docs.gotSmoothMS = True
#             self.docs.smoothMS = ms_data
#             new_dataset = "Mass Spectrum (processed)"
#         else:
#             # strip any processed string from the title
#             if "(processed)" in dataset:
#                 dataset = dataset.split(" (")[0]
#             new_dataset = "%s (processed)" % dataset
#             self.docs.multipleMassSpectrum[new_dataset] = ms_data
#
#         # Plot processed MS
#         name_kwargs = {"document": self.docs.title, "dataset": new_dataset}
#         self.view.panelPlots.on_plot_MS(msX, msY, xlimits=xlimits, **name_kwargs)
#         self.OnUpdateDocument(self.docs, 'document')

    def _get_replot_data(self, data_format):
        """
        @param data_format (str): type of data to be returned
        """
        # new in 1.1.0
        if data_format == '2D':
            get_data = self.config.replotData.get('2D', None)
            zvals, xvals, yvals, xlabel, ylabel = None, None, None, None, None
            if get_data is not None:
                zvals = get_data['zvals'].copy()
                xvals = get_data['xvals']
                yvals = get_data['yvals']
                xlabel = get_data['xlabels']
                ylabel = get_data['ylabels']
            return zvals, xvals, yvals, xlabel, ylabel
        elif data_format == 'RMSF':
            get_data = self.config.replotData.get('RMSF', None)
            zvals, xvals, yvals, xlabelRMSD, ylabelRMSD, ylabelRMSF = None, None, None, None, None, None
            if get_data is not None:
                zvals = get_data['zvals'].copy()
                xvals = get_data['xvals']
                yvals = get_data['yvals']
                xlabelRMSD = get_data['xlabelRMSD']
                ylabelRMSD = get_data['ylabelRMSD']
                ylabelRMSF = get_data['ylabelRMSF']
            return zvals, xvals, yvals, xlabelRMSD, ylabelRMSD, ylabelRMSF
        elif data_format == 'DT/MS':
            get_data = self.config.replotData.get('DT/MS', None)
            zvals, xvals, yvals, xlabel, ylabel = None, None, None, None, None
            if get_data is not None:
                zvals = get_data['zvals'].copy()
                xvals = get_data['xvals']
                yvals = get_data['yvals']
                xlabel = get_data['xlabels']
                ylabel = get_data['ylabels']
            return zvals, xvals, yvals, xlabel, ylabel
        elif data_format == 'MS':
            get_data = self.config.replotData.get('MS', None)
            xvals, yvals, xlimits = None, None, None
            if get_data is not None:
                xvals = get_data.get('xvals', None)
                yvals = get_data.get('yvals', None)
                xlimits = get_data.get('xlimits', None)
            return xvals, yvals, xlimits
        elif data_format == 'RT':
            get_data = self.config.replotData.get('RT', None)
            xvals, yvals, xlabel = None, None, None
            if get_data is not None:
                xvals = get_data.get('xvals', None)
                yvals = get_data.get('yvals', None)
                xlabel = get_data.get('xlabel', None)
            return xvals, yvals, xlabel
        elif data_format == '1D':
            get_data = self.config.replotData.get('1D', None)
            xvals, yvals, xlabel = None, None, None
            if get_data is not None:
                xvals = get_data.get('xvals', None)
                yvals = get_data.get('yvals', None)
                xlabel = get_data.get('xlabel', None)
            return xvals, yvals, xlabel
        elif data_format == 'Matrix':
            get_data = self.config.replotData.get('Matrix', None)
            zvals, xylabels, cmap = None, None, None
            if get_data is not None:
                zvals = get_data.get('zvals', None)
                xylabels = get_data.get('xylabels', None)
                cmap = get_data.get('cmap', None)
            return zvals, xylabels, cmap

    def checkWhatIsMissing2D(self, zvals, xvals, xlabel, yvals, ylabel, cmap):
        if isempty(zvals):
            self.view.SetStatusText("Missing 2D array", 3)

        if isempty(xvals):
            self.view.SetStatusText("Missing x-axis labels", 3)

        if isempty(xlabel):
            self.view.SetStatusText("Missing x-axis label", 3)

        if isempty(yvals):
            self.view.SetStatusText("Missing y-axis labels", 3)

        if isempty(ylabel):
            self.view.SetStatusText("Missing y-axis label", 3)

        if isempty(cmap):
            self.view.SetStatusText("Missing colormap", 3)

    # TODO: move this function to panelPlots or else
    def plot_compareMS(self, msX=None, msY_1=None, msY_2=None, msY=None, xlimits=None,
                       replot=False, override=True, evt=None):

        if replot:
            data = self._get_replot_data('compare_MS')
            if data['subtract']:
                msX = data['xvals']
                msY = data['yvals']
                xlimits = data['xlimits']
            else:
                msX = data['xvals']
                msY_1 = data['yvals1']
                msY_2 = data['yvals2']
                xlimits = data['xlimits']
                legend = data['legend']
                return
        else:
            legend = self.config.compare_massSpectrum
            subtract = self.config.compare_massSpectrumParams['subtract']

        # Build kwargs
        plt_kwargs = self.view.panelPlots._buildPlotParameters(plotType='1D')

        self.view.panelPlots.plot1.clearPlot()
        if subtract:
            self.view.panelPlots.plot1.plot_1D(xvals=msX, yvals=msY,
                                               xlimits=xlimits,
                                               zoom='box', title="", xlabel="m/z",
                                               ylabel="Intensity", label="",
                                               lineWidth=self.config.lineWidth_1D,
                                               axesSize=self.config._plotSettings['MS']['axes_size'],
                                               plotType='MS',
                                               **plt_kwargs)
            if override:
                self.config.replotData['compare_MS'] = {'xvals': msX,
                                                        'yvals': msY,
                                                        'xlimits': xlimits,
                                                        'subtract': subtract}
        else:
            self.view.panelPlots.plot1.plot_1D_compare(xvals=msX,
                                                       yvals1=msY_1, yvals2=msY_2,
                                                       xlimits=xlimits,
                                                       zoom='box', title="",
                                                       xlabel="m/z", ylabel="Intensity",
                                                       label=legend,
                                                       lineWidth=self.config.lineWidth_1D,
                                                       axesSize=self.config._plotSettings['MS (compare)']['axes_size'],
                                                       plotType='compare',
                                                       **plt_kwargs)
            if override:
                self.config.replotData['compare_MS'] = {'xvals': msX,
                                                        'yvals1': msY_1,
                                                        'yvals2': msY_2,
                                                        'xlimits': xlimits,
                                                        'legend': legend,
                                                        'subtract': subtract}
        # Show the mass spectrum
        self.view.panelPlots.plot1.repaint()

    def plot_1D_update(self, plotName='all', evt=None):

        plt_kwargs = self.view.panelPlots._buildPlotParameters(plotType='1D')

        if plotName in ['all', 'MS']:
            try:
                self.view.panelPlots.plot1.plot_1D_update(**plt_kwargs)
                self.view.panelPlots.plot1.repaint()
            except AttributeError:
                pass

        if plotName in ['all', 'RT']:
            try:
                self.view.panelPlots.plotRT.plot_1D_update(**plt_kwargs)
                self.view.panelPlots.plotRT.repaint()
            except AttributeError:
                pass

        if plotName in ['all', '1D']:
            try:
                self.view.panelPlots.plot1D.plot_1D_update(**plt_kwargs)
                self.view.panelPlots.plot1D.repaint()
            except AttributeError:
                pass

    def plot_2D_update(self, plotName='all', evt=None):
        plt_kwargs = self.view.panelPlots._buildPlotParameters(plotType='2D')

        if plotName in ['all', '2D']:
            try:
                zvals, __, __, __, __ = self._get_replot_data('2D')
                # normalize
                cmapNorm = self.normalize_colormap(zvals,
                                                    min=self.config.minCmap,
                                                    mid=self.config.midCmap,
                                                    max=self.config.maxCmap)
                plt_kwargs['colormap_norm'] = cmapNorm

                self.view.panelPlots.plot2D.plot_2D_update(**plt_kwargs)
                self.view.panelPlots.plot2D.repaint()
            except AttributeError:
                pass

        if plotName in ['all', 'DT/MS']:
            try:
                zvals, __, __, __, __ = self._get_replot_data('DT/MS')
                # normalize
                cmapNorm = self.normalize_colormap(zvals,
                                                    min=self.config.minCmap,
                                                    mid=self.config.midCmap,
                                                    max=self.config.maxCmap)
                plt_kwargs['colormap_norm'] = cmapNorm
                self.view.panelPlots.plotMZDT.plot_2D_update(**plt_kwargs)
                self.view.panelPlots.plotMZDT.repaint()
            except AttributeError:
                pass

    def plot_3D_update(self, plotName='all', evt=None):
        plt_kwargs = self.view.panelPlots._buildPlotParameters(plotType='3D')

        if plotName in ['all', '3D']:
            try:
                self.view.panelPlots.plot3D.plot_3D_update(**plt_kwargs)
                self.view.panelPlots.plot3D.repaint()
            except AttributeError:
                pass

    def plot_update_axes(self, plotName, evt=None):

        # get current sizes
        axes_sizes = self.config._plotSettings[plotName]['axes_size']

        # get link to the plot
        if plotName == 'MS':
            resize_plot = [self.view.panelPlots.plot1,
                           self.view.panelPlots.plotRT_MS,
                           self.view.panelPlots.plot1D_MS]
        elif plotName == 'MS (compare)':
            resize_plot = self.view.panelPlots.plot1
        elif plotName == 'RT':
            resize_plot = self.view.panelPlots.plotRT
        elif plotName == 'DT':
            resize_plot = self.view.panelPlots.plot1D
        elif plotName == '2D':
            resize_plot = self.view.panelPlots.plot2D
        elif plotName == 'Waterfall':
            resize_plot = self.view.panelPlots.plotWaterfallIMS
        elif plotName == 'RMSD':
            resize_plot = self.view.panelPlots.plotRMSF
        elif plotName in ['Comparison', 'Matrix']:
            resize_plot = self.view.panelPlots.plotCompare
        elif plotName == 'DT/MS':
            resize_plot = self.view.panelPlots.plotMZDT
        elif plotName in ['Overlay', 'Overlay (Grid)']:
            resize_plot = self.view.panelPlots.plotOverlay
        elif plotName == 'Calibration (MS)':
            resize_plot = self.view.panelPlots.topPlotMS
        elif plotName == 'Calibration (DT)':
            resize_plot = self.view.panelPlots.bottomPlot1DT
        elif plotName == '3D':
            resize_plot = self.view.panelPlots.plot3D
        elif plotName == 'UniDec (MS)':
            resize_plot = self.view.panelPlots.plotUnidec_MS
        elif plotName == 'UniDec (MW)':
            resize_plot = self.view.panelPlots.plotUnidec_mwDistribution
        elif plotName == 'UniDec (m/z vs Charge)':
            resize_plot = self.view.panelPlots.plotUnidec_mzGrid
        elif plotName == 'UniDec (Isolated MS)':
            resize_plot = self.view.panelPlots.plotUnidec_individualPeaks
        elif plotName == 'UniDec (MW vs Charge)':
            resize_plot = self.view.panelPlots.plotUnidec_mwVsZ
        elif plotName == 'UniDec (Barplot)':
            resize_plot = self.view.panelPlots.plotUnidec_barChart
        elif plotName == 'UniDec (Charge Distribution)':
            resize_plot = self.view.panelPlots.plotUnidec_chargeDistribution
        # apply new size
        try:
            if not isinstance(resize_plot, list):
                resize_plot = [resize_plot]
            for plot in resize_plot:
                if plot.lock_plot_from_updating:
                    msg = "This plot is locked and you cannot use global setting updated. \n" + \
                          "Please right-click in the plot area and select Customise plot..." + \
                          " to adjust plot settings."
                    print(msg)
                    continue
                plot.plot_update_axes(axes_sizes)
                plot.repaint()
                plot._axes = axes_sizes
        except (AttributeError, UnboundLocalError):
            pass

#     def onPlotLinearDT(self, yvals, e=None):
#         # Plot mass spectrum
#         self.view.panelPlots.plot1D.clearPlot()
#         xvals = np.arange(1, 201)  # temporary hack
#         if isempty(yvals):
#             yvals = self.dc.imsData1D
#         else:
#             yvals = yvals
#
#         self.view.panelPlots.plot1D.plotNew1Dplot(xvals=xvals, yvals=yvals,
#                                                   title="", xlabel="Drift time (bins)",
#                                                   ylabel="Intensity", label="",
#                                                   color=self.config.lineColour, zoom='box',
#                                                   plotName='1D')
#         # Show the mass spectrum
#         self.view.panelPlots.plot1D.repaint()
#
#     def onPlotMSDTCalibration(self, msX=None, msY=None, xlimits=None, dtX=None,
#                               dtY=None, color=None, xlabelDT='Drift time (bins)',
#                               e=None, plotType='both'):
#         # MS plot
#         if plotType == 'both' or plotType == 'MS':
#             self.view.panelPlots.topPlotMS.clearPlot()
#             # get kwargs
#             plt_kwargs = self.view.panelPlots._buildPlotParameters(plotType='1D')
#             self.view.panelPlots.topPlotMS.plot_1D(xvals=msX,
#                                                    yvals=msY,
#                                                    xlabel="m/z",
#                                                    ylabel="Intensity",
#                                                    xlimits=xlimits,
#                                                    axesSize=self.config._plotSettings['Calibration (MS)']['axes_size'],
#                                                    plotType='1D',
#                                                    **plt_kwargs)
#             # Show the mass spectrum
#             self.view.panelPlots.topPlotMS.repaint()
#
#         if plotType == 'both' or plotType == '1DT':
#             ylabel = "Intensity"
#             # 1DT plot
#             self.view.panelPlots.bottomPlot1DT.clearPlot()
#             # get kwargs
#             plt_kwargs = self.view.panelPlots._buildPlotParameters(plotType='1D')
#             self.view.panelPlots.bottomPlot1DT.plot_1D(
#                 xvals=dtX,
#                 yvals=dtY,
#                 xlabel=xlabelDT,
#                 ylabel=ylabel,
#                 axesSize=self.config._plotSettings['Calibration (DT)']['axes_size'],
#                 plotType='CalibrationDT',
#                 **plt_kwargs)
#             self.view.panelPlots.bottomPlot1DT.repaint()
#
#     def onPlot1DTCalibration(self, dtX=None, dtY=None, color=None,
#                              xlabel='Drift time (bins)', e=None):
#
#         # Check yaxis labels
#         ylabel = "Intensity"
#         # 1DT plot
#         self.view.panelPlots.bottomPlot1DT.clearPlot()
#         # get kwargs
#         plt_kwargs = self.view.panelPlots._buildPlotParameters(plotType='1D')
#         self.view.panelPlots.bottomPlot1DT.plot_1D(xvals=dtX, yvals=dtY,
#                                                    xlabel=xlabel, ylabel=ylabel,
#                                                    axesSize=self.config._plotSettings['Calibration (DT)']['axes_size'],
#                                                    plotType='1D',
#                                                    **plt_kwargs)
#         self.view.panelPlots.bottomPlot1DT.repaint()
#
#     def onPlotCalibrationCurve(self, xvals1, yvals1, label1, xvalsLinear, yvalsLinear,
#                                xvals2, yvals2, label2, xvalsPower, yvalsPower,
#                                color, marker, markerSize=5, e=None):
#
#         self.view.panelPlots.bottomPlot1DT.clearPlot()
#         self.view.panelPlots.bottomPlot1DT.plotScatter_2plot(
#             xvals1,
#             yvals1,
#             label1,
#             xvalsLinear,
#             yvalsLinear,
#             xvals2,
#             yvals2,
#             label2,
#             xvalsPower,
#             yvalsPower,
#             color,
#             marker,
#             markerSize=5,
#             axesSize=self.config._plotSettings['Calibration (DT)']['axes_size'])
#         self.view.panelPlots.bottomPlot1DT.repaint()

    def addMarkerMS(self, xvals=None, yvals=None, color='b', marker='o', size=5, plot='MS'):
        if plot == 'MS':
            self.view.panelPlots.plot1.onAddMarker(xval=xvals,
                                                   yval=yvals,
                                                   color=color,
                                                   marker=marker,
                                                   size=size)
            self.view.panelPlots.plot1.repaint()
        elif plot == 'RT':
            self.view.panelPlots.plotRT.onAddMarker(xval=xvals,
                                                    yval=yvals,
                                                    color=color,
                                                    marker=marker,
                                                    size=size)
            self.view.panelPlots.plotRT.repaint()
        elif plot == 'CalibrationMS':
            self.view.panelPlots.topPlotMS.onAddMarker(xval=xvals,
                                                       yval=yvals,
                                                       color=color,
                                                       marker=marker,
                                                       size=size)
            self.view.panelPlots.topPlotMS.repaint()
        elif plot == 'CalibrationDT':
            self.view.panelPlots.bottomPlot1DT.onAddMarker(xval=xvals,
                                                           yval=yvals,
                                                           color=color,
                                                           marker=marker,
                                                           size=size,
                                                           testMax='yvals')
            self.view.panelPlots.bottomPlot1DT.repaint()

    def addRectMS(self, x, y, width, height, color='r', alpha=0.5, repaint=False, plot='MS'):

        if plot == 'MS':
            self.view.panelPlots.plot1.addRectangle(x, y, width,
                                                    height, color=color,
                                                    alpha=alpha)
            if not repaint:
                return
            else:
                self.view.panelPlots.plot1.repaint()
        elif plot == 'CalibrationMS':
            self.view.panelPlots.topPlotMS.addRectangle(x, y, width,
                                                        height, color=color,
                                                        alpha=alpha)
            if not repaint:
                return
            else:
                self.view.panelPlots.topPlotMS.repaint()

    def addRectRT(self, x, y, width, height, color='r', alpha=0.5, repaint=False):
        self.view.panelPlots.plotRT.addRectangle(x, y,
                                                 width,
                                                 height,
                                                 color=color,
                                                 alpha=alpha)
        if not repaint:
            return
        else:
            self.view.panelPlots.plotRT.repaint()

    def addTextMS(self, x, y, text, rotation, color="k"):
        self.view.panelPlots.plot1.addText(x, y, text, rotation, color)
        self.view.panelPlots.plot1.repaint()

    def addTextRMSD(self, x, y, text, rotation, color="k", plot='RMSD'):

        if plot == 'RMSD':
            self.view.panelPlots.plotRMSF.addText(x, y, text, rotation,
                                                  color=self.config.rmsd_color,
                                                  fontsize=self.config.rmsd_fontSize,
                                                  weight=self.config.rmsd_fontWeight)
            self.view.panelPlots.plotRMSF.repaint()
        elif plot == 'RMSF':
            self.view.panelPlots.plotRMSF.addText(x, y, text, rotation,
                                                  color=self.config.rmsd_color,
                                                  fontsize=self.config.rmsd_fontSize,
                                                  weight=self.config.rmsd_fontWeight)
            self.view.panelPlots.plotRMSF.repaint()
        elif plot == 'Grid':
            self.view.panelPlots.plotOverlay.addText(x, y, text, rotation,
                                                     color=self.config.rmsd_color,
                                                     fontsize=self.config.rmsd_fontSize,
                                                     weight=self.config.rmsd_fontWeight,
                                                     plot=plot)
            self.view.panelPlots.plotOverlay.repaint()

#     def onAddMarker1D(self, xval=None, yval=None, color='r', marker='o'):
#         """
#         This function adds marker to 1D plot
#         """
#         # Check yaxis labels
#         ydivider = self.testXYmaxVals(values=yval)
#         yval = yval / ydivider
#         # Add single point
#         self.view.panelPlots.bottomPlot1DT.onAddMarker(xval=xval,
#                                                        yval=yval,
#                                                        color=color,
#                                                        marker=marker)
#         self.view.panelPlots.bottomPlot1DT.repaint()

#     def getXYlimits2D(self, xvals, yvals, zvals=None):
#
#         # Get min/max values
#         xmin, xmax = xvals[0], xvals[-1]
#         ymin, ymax = yvals[0], yvals[-1]
#         self.config.xyLimits = [xmin, xmax, ymin, ymax]
#         if zvals is not None:
#             self.config.colorbarRange = [np.min(zvals), np.max(zvals)]

#     def getIntensityLimits2D(self, zvals):
#         minVal, maxVal = np.min(zvals), np.max(zvals)
#         self.config.colorbarRange = [minVal, maxVal]
# #         self.view.panelControls.onUpdateColorbarLimits(evt=None)

    def setXYlimitsRMSD2D(self, xvals, yvals):
        # Get min/max values
        xmin, xmax = xvals[0], xvals[-1]
        ymin, ymax = yvals[0], yvals[-1]
        self.config.xyLimitsRMSD = [xmin, xmax, ymin, ymax]

#     def onZoomMS(self, startX, endX, endY, plot='MS'):
#
#         if plot == 'MS':
#             self.view.panelPlots.plot1.onZoomIn(startX, endX, endY)
#             self.view.panelPlots.plot1.repaint()
#         elif plot == 'CalibrationMS':
#             self.view.panelPlots.topPlotMS.onZoomIn(startX, endX, endY)

    # TODO: move this function to panelplots
    def OnChangedRMSF(self, xmin, xmax):
        """
        Receives a message about change in RMSF plot
        """

        self.view.panelPlots.plotRMSF.onZoomRMSF(xmin, xmax)

#     def onZoom2D(self, evt):
#         if self.config.restrictXYrange:
#             if len(self.config.xyLimits) != 4:
#                 return
#
#             startX, endX, startY, endY = self.config.xyLimits
#
#             msg = ' '.join(['Zoomed in: X:', str(startX), '-', str(endX),
#                             'Y:', str(startY), '-', str(endY)])
#             self.view.SetStatusText(msg, 3)
#             self.view.panelPlots.plot2D.onZoom2D(startX, endX, startY, endY)
#             self.view.panelPlots.plot2D.repaint()
#             if self.config.waterfall:
#                 # Axes are rotated so using yaxis limits
#                 self.view.panelPlots.plotWaterfallIMS.onZoom1D(startY, endY)
#                 self.view.panelPlots.plotWaterfallIMS.repaint()
#
#     def onRebootZoom(self, evt):
#         plotList = [self.view.panelPlots.plot1,
#                     self.view.panelPlots.plotRT,
#                     self.view.panelPlots.plotRMSF, self.view.panelPlots.plotMZDT,
#                     self.view.panelPlots.plotCompare, self.view.panelPlots.plot2D,
#                     self.view.panelPlots.plot3D, self.view.panelPlots.plotOverlay,
#                     self.view.panelPlots.plotWaterfallIMS, self.view.panelPlots.topPlotMS,
#                     self.view.panelPlots.bottomPlot1DT, self.view.panelPlots.plotOther]
#
#         for plot in plotList:
#             plot.onRebootZoomKeys(evt=None)
#
#         # Message
#         args = ("Zoom keys were reset", 4)
#         self.onThreading(evt, args, action='updateStatusbar')

    def onImportConfig(self, evt, onStart=False):
        """
        This function imports configuration file
        """
        if not onStart:
            if evt.GetId() == ID_openConfig:
                config_path = os.path.join(self.config.cwd, 'configOut.xml')
                self.onThreading(None, ("Imported configuration file: {}".format(
                    config_path), 4), action='updateStatusbar')
                self.config.loadConfigXML(path=config_path, evt=None)
                self.view.updateRecentFiles()
                return
            elif evt.GetId() == ID_openAsConfig:
                dlg = wx.FileDialog(self.view, "Open Configuration File", wildcard="*.xml",
                                    style=wx.FD_DEFAULT_STYLE | wx.FD_CHANGE_DIR)
                if dlg.ShowModal() == wx.ID_OK:
                    fileName = dlg.GetPath()
                    self.config.loadConfigXML(path=fileName, evt=None)
                    self.view.updateRecentFiles()
        else:
            self.config.loadConfigXML(path='configOut.xml', evt=None)
#             self.view.updateRecentFiles()
            return

    def onExportConfig(self, evt, verbose=True):
        if isinstance(evt, int):
            evtID = evt
        else:
            evtID = evt.GetId()

        if evtID == ID_saveConfig:
            try:
                save_dir = os.path.join(self.config.cwd, 'configOut.xml')
            except TypeError:
                return
            if self.config.threading:
                args = (save_dir, None, verbose)
                self.onThreading(None, args, action='export_settings')
            else:
                try:
                    self.config.saveConfigXML(path=save_dir, evt=None, verbose=verbose)
                except TypeError:
                    pass
        elif evtID == ID_saveAsConfig:
            dlg = wx.FileDialog(self.view, "Save As Configuration File", wildcard="*.xml",
                                style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
            dlg.SetFilename('configOut.xml')
            if dlg.ShowModal() == wx.ID_OK:
                fileName = dlg.GetPath()
                self.config.saveConfigXML(path=fileName, evt=None, verbose=verbose)

    def on_open_directory(self, path=None, evt=None):

        if path is None:
            path, title = self.getCurrentDocumentPath()
            if path is None or title is None:
                self.view.SetStatusText('Please select a document')
                return

        try:
            os.startfile(path)
        except WindowsError:
            dlgBox(exceptionTitle='This folder does not exist',
                   exceptionMsg="Could not open the directory - this folder does not exist",
                   type="Error")
            return

    def getCurrentDocumentPath(self):
        '''
        Function used to get the path to current document
        '''
        # Gather info about the file and document
        self.currentDoc, selectedItem, selectedText = self.view.panelDocuments.documents.enableCurrentDocument(
            getSelected=True)
        indent = self.view.panelDocuments.documents.getItemIndent(selectedItem)
        if self.currentDoc == 'Current documents':
            return None, None
        elif indent > 2:
            selectedItemParent, selectedItemParentText = self.view.panelDocuments.documents.getParentItem(
                selectedItem, 2, getSelected=True)
        else:
            pass
        document = self.documentsDict[self.currentDoc]
        return document.path, document.title

    # TODO: move to data_handling module
    def OnUpdateDocument(self, document, expand_item='document', expand_item_title=None):

        if expand_item == 'document':
            self.view.panelDocuments.documents.add_document(docData=document,
                                                            expandItem=document)
        elif expand_item == 'ions':
            if expand_item_title is None:
                self.view.panelDocuments.documents.add_document(docData=document,
                                                                expandItem=document.IMS2Dions)
            else:
                self.view.panelDocuments.documents.add_document(docData=document,
                                                                expandItem=document.IMS2Dions[expand_item_title])
        elif expand_item == 'combined_ions':
            if expand_item_title is None:
                self.view.panelDocuments.documents.add_document(docData=document,
                                                                expandItem=document.IMS2DCombIons)
            else:
                self.view.panelDocuments.documents.add_document(docData=document,
                                                                expandItem=document.IMS2DCombIons[expand_item_title])

        elif expand_item == 'processed_ions':
            if expand_item_title is None:
                self.view.panelDocuments.documents.add_document(docData=document,
                                                                expandItem=document.IMS2DionsProcess)
            else:
                self.view.panelDocuments.documents.add_document(docData=document,
                                                                expandItem=document.IMS2DionsProcess[expand_item_title])

        elif expand_item == 'ions_1D':
            if expand_item_title is None:
                self.view.panelDocuments.documents.add_document(docData=document,
                                                                expandItem=document.multipleDT)
            else:
                self.view.panelDocuments.documents.add_document(docData=document,
                                                                expandItem=document.multipleDT[expand_item_title])

        elif expand_item == 'comparison_data':
            if expand_item_title is None:
                self.view.panelDocuments.documents.add_document(docData=document,
                                                                expandItem=document.IMS2DcompData)
            else:
                self.view.panelDocuments.documents.add_document(docData=document,
                                                                expandItem=document.IMS2DcompData[expand_item_title])

        elif expand_item == 'mass_spectra':
            if expand_item_title is None:
                self.view.panelDocuments.documents.add_document(docData=document,
                                                                expandItem=document.multipleMassSpectrum)
            else:
                self.view.panelDocuments.documents.add_document(
    docData=document, expandItem=document.multipleMassSpectrum[expand_item_title])

        elif expand_item == 'overlay':
            if expand_item_title is None:
                self.view.panelDocuments.documents.add_document(docData=document,
                                                                expandItem=document.IMS2DoverlayData)
            else:
                self.view.panelDocuments.documents.add_document(docData=document,
                                                                expandItem=document.IMS2DoverlayData[expand_item_title])
        # just set data
        elif expand_item == 'no_refresh':
            self.view.panelDocuments.documents.set_document(document_old=self.documentsDict[document.title],
                                                            document_new=document)

        # update dictionary
        self.documentsDict[document.title] = document
        self.currentDoc = document.title

    # TODO: move to data_handling module
    def onAddBlankDocument(self, evt, document_type=None):
        """
        Adds blank document of specific type
        """

        dlg = wx.FileDialog(self.view, "Please add name and select path for the document",
                            "", "", "", wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            itemPath, idName = os.path.split(dlg.GetPath())
        else:
            return

        if evt is None:
            evtID = None
        elif isinstance(evt, int):
            evtID = evt
        else:
            evtID = evt.GetId()

        document = documents()
        document.title = idName
        document.path = itemPath
        self.currentDoc = idName
        document.userParameters = self.config.userParameters
        document.userParameters['date'] = getTime()
        # Add method specific parameters
        if evtID == ID_addNewOverlayDoc or document_type == 'overlay':
            document.dataType = 'Type: Comparison'
            document.fileFormat = 'Format: ORIGAMI'

        elif evtID == ID_addNewCalibrationDoc or document_type == 'calibration':
            document.dataType = 'Type: CALIBRANT'
            document.fileFormat = 'Format: DataFrame'

        elif evtID == ID_addNewInteractiveDoc or document_type == 'interactive':
            document.dataType = 'Type: Interactive'
            document.fileFormat = 'Format: ORIGAMI'

        elif evtID == ID_addNewManualDoc or document_type == 'manual':
            document.dataType = 'Type: MANUAL'
            document.fileFormat = 'Format: MassLynx (.raw)'

        self.OnUpdateDocument(document, 'document')

    def on_open_weblink(self, evt):
        """Open selected webpage."""

        if isinstance(evt, int):
            evtID = evt
        else:
            evtID = evt.GetId()

        # set link
        links = {ID_helpHomepage: 'home', ID_helpGitHub: 'github',
                 ID_helpCite: 'cite', ID_helpNewVersion: 'newVersion',
                 ID_helpYoutube: 'youtube', ID_helpGuide: 'guide',
                 ID_helpHTMLEditor: 'htmlEditor', ID_helpNewFeatures: 'newFeatures',
                 ID_helpReportBugs: 'reportBugs'}

        link = self.config.links[links[evtID]]

        # open webpage
        try:
            self.onThreading(None, ("Opening a link in your default internet browser", 4),
                             action='updateStatusbar')
            webbrowser.open(link, autoraise=1)
        except Exception:            pass

    def onCheckVersion(self, evt=None):
        """
        Simple function to check whether this is the newest version available
        """
        # TODO: move his function to separate module (e.g. utils/version.py - can be unit tested)
        pass
#         try:
#             newVersion = get_latest_version(link=self.config.links['newVersion'])
#             update = compare_versions(newVersion, self.config.version)
#             if not update:
#                 try:
#                     if evt.GetId() == ID_CHECK_VERSION:
#                         dlgBox(exceptionTitle='ORIGAMI',
#                                exceptionMsg='You are using the most up to date version %s.' % (self.config.version),
#                                type="Info")
#                 except Exception:                    pass
#             else:
#                 webpage = get_latest_version(get_webpage=True)
#                 wx.Bell()
#                 message = "Version {} is now available for download.\nYou are currently using version {}.".format(
#                     newVersion, self.config.version)
#                 self.onThreading(None, (message, 4),
#                                  action='updateStatusbar')
#                 msgDialog = panelNotifyNewVersion(self.view, self, webpage)
#                 msgDialog.ShowModal()
#         except Exception as e:
#             self.onThreading(None, ('Could not check version number', 4),
#                              action='updateStatusbar')
#             logger.error(e)

#     def onOpenUserGuide(self, evt):
#         """
#         Opens PDF viewer
#         """
#         try:
#             os.startfile('UserGuide_ANALYSE.pdf')
#         except Exception:
#             return

#     def openHTMLViewer(self, evt):
#         from help_documentation import HTMLHelp
#
#         htmlPages = HTMLHelp()
#         evtID = evt.GetId()
#         if evtID == ID_help_UniDecInfo:
#             kwargs = htmlPages.page_UniDec_info
#
#         elif evtID == ID_help_page_dataLoading:
#             kwargs = htmlPages.page_data_loading_info
#
#         elif evtID == ID_help_page_gettingStarted:
#             kwargs = htmlPages.page_data_getting_started
#
#         elif evtID == ID_help_page_UniDec:
#             kwargs = htmlPages.page_deconvolution_info
#
#         elif evtID == ID_help_page_ORIGAMI:
#             kwargs = htmlPages.page_origami_info
#
#         elif evtID == ID_help_page_overlay:
#             kwargs = htmlPages.page_overlay_info
#
#         elif evtID == ID_help_page_multipleFiles:
#             kwargs = htmlPages.page_multiple_files_info
#
#         elif evtID == ID_help_page_linearDT:
#             kwargs = htmlPages.page_linear_dt_info
#
#         elif evtID == ID_help_page_CCScalibration:
#             kwargs = htmlPages.page_ccs_calibration_info
#
#         elif evtID == ID_help_page_dataExtraction:
#             kwargs = htmlPages.page_data_extraction_info
#
#         elif evtID == ID_help_page_Interactive:
#             kwargs = htmlPages.page_interactive_output_info
#
#         elif evtID == ID_help_page_OtherData:
#             kwargs = htmlPages.page_other_data_info
#
#         elif evtID == ID_help_page_annotatingMassSpectra:
#             kwargs = htmlPages.page_annotating_mass_spectra
#
#         htmlViewer = panelHTMLViewer(self.view, self.config, **kwargs)
#         htmlViewer.Show()


if __name__ == '__main__':
    app = ORIGAMI(redirect=False)
    app.start()
