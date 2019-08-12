# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
# Import libraries
import gc
import logging
import os
import sys
import threading
import warnings
import webbrowser
from sys import platform

import mainWindow as mainWindow
import numpy as np
import processing.UniDec.unidec as unidec
import wx
from config import OrigamiConfig as config
from document import document as documents
from gui_elements.dialog_select_document import DialogSelectDocument
from gui_elements.misc_dialogs import DialogBox
from gui_elements.misc_dialogs import DialogSimpleAsk
from help_documentation import OrigamiHelp
from icons.icons import IconContainer
from ids import ID_addNewCalibrationDoc
from ids import ID_addNewInteractiveDoc
from ids import ID_addNewManualDoc
from ids import ID_addNewOverlayDoc
from ids import ID_helpCite
from ids import ID_helpGitHub
from ids import ID_helpGuide
from ids import ID_helpHomepage
from ids import ID_helpHTMLEditor
from ids import ID_helpNewFeatures
from ids import ID_helpNewVersion
from ids import ID_helpReportBugs
from ids import ID_helpYoutube
from ids import ID_processAllIons
from ids import ID_processSelectedIons
from ids import ID_textPanel_process_all
from ids import ID_window_textList
from toolbox import find_nearest
from utils.logging import set_logger
from utils.logging import set_logger_level
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
        self.__wx_app = wx.App(redirect=False, filename="ORIGAMI")
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
        self.view = mainWindow.MyFrame(self, config=self.config, icons=self.icons, title="ORIGAMI", helpInfo="")
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
        self.icons = IconContainer()
        self.docs = documents()
        self.help = OrigamiHelp()

        # Load configuration file
        self.on_import_configuration_on_startup()

        # Setup variables
        self.initilize_state()
        self.view = mainWindow.MyFrame(
            self, config=self.config, icons=self.icons, helpInfo=self.help, title="ORIGAMI - %s " % self.config.version
        )
        self.__wx_app.SetTopWindow(self.view)
        self.__wx_app.SetAppName("ORIGAMI - %s " % self.config.version)
        self.__wx_app.SetVendorName("Lukasz G. Migas, University of Manchester")

        # Assign standard input/output to variable
        self.config.stdin = sys.stdin
        self.config.stdout = sys.stdout
        self.config.stderr = sys.stderr

        # Set current working directory
        self.config.cwd = os.getcwd()

        # Set temporary data path
        temp_data_folder = os.path.join(os.getcwd(), "temporary_data")
        if not os.path.exists(temp_data_folder):
            os.makedirs(temp_data_folder)
        self.config.temporary_data = temp_data_folder

        # Setup plot style
        self.view.panelPlots.on_change_plot_style(evt=None)
        self.view.panelPlots.on_change_color_palette(evt=None)
        self.view.updateRecentFiles()

        self.logging = self.config.logging
        self.config._processID = os.getpid()

        # add data processing module
        self.data_processing = self.view.data_processing
        self.data_handling = self.view.data_handling
        self.data_visualisation = self.view.data_visualisation

        #         # Load protein/CCS database
        #         if self.config.loadCCSAtStart:
        #             self.onImportCCSDatabase(evt=None, onStart=True)

        gc.enable()
        self.on_start_logging()

        # add binding to UniDec engine
        self.config.unidec_engine = unidec.UniDec()

        # Set unidec directory
        self.config.unidec_path = self.config.unidec_engine.config.UniDecPath

        # check version
        self.onCheckVersion()

        # only check if on Windows
        if self.config.checkForDriftscopeAtStart and platform == "win32":
            self.config.initilize_paths()

        # add data handling and processing modules
        self.view.panelDocuments.documents._setup_handling_and_processing()
        self.view.panelMultipleIons._setup_handling_and_processing()
        self.view.panelMultipleText._setup_handling_and_processing()
        self.view.panelMML._setup_handling_and_processing()
        self.view.panelPlots._setup_handling_and_processing()
        self.view.panelParametersEdit._setup_handling_and_processing()
        self.data_processing._setup_handling_and_processing()
        self.data_visualisation._setup_handling_and_processing()

        if self.config.debug and not self.config.testing:
            self._debug_()

        if self.config.testing:
            self._test_()

    def initilize_state(self):
        """Pre-set variables"""
        self.docsText = {}
        self.documents = []
        self.documentsDict = {}
        self.currentDoc = None
        self.currentCalibrationParams = []
        self.currentPath = None

    def _test_(self):
        # load text MS file
        path = os.path.join(self.config.cwd, "example_files", "text_files", "MS_p27-FL-K31.csv")
        self.data_handling.on_add_text_MS(path)

        # load text 2D file
        for fname in [
            "1_Linear_IMS2D_5140.73-5169.41.csv",
            "2_Exponential_IMS2D_5140.48-5164.36.csv",
            "3_Boltzmann_IMS2D_5139.58-5170.58.csv",
        ]:
            path = os.path.join(self.config.cwd, "example_files", "text_files", fname)
            self.data_handling.on_add_text_2D(None, path)

        if platform == "win32":
            # load Waters (.raw) file - MS only
            path = os.path.join(self.config.cwd, "example_files", "dt-ims", "LM_20151006_7_B_DV60.raw")
            self.data_handling.on_open_single_MassLynx_raw(path, "Type: MS")

            # load Waters (.raw) file - IM-MS
            path = os.path.join(self.config.cwd, "example_files", "origami_ms", "ORIGAMI_ConA_z20.raw")
            self.data_handling.on_open_single_MassLynx_raw(path, "Type: ORIGAMI")

            # extract MS data - RT
            self.data_handling.on_extract_MS_from_chromatogram(5, 10)
            self.data_handling.on_extract_MS_from_chromatogram(1.5, 1.7, "Time (min)")
            self.data_handling.on_extract_MS_from_chromatogram(1.7, 1.9, "Retention time (min)")

            # extract MS data - DT
            self.data_handling.on_extract_MS_from_mobiligram(65, 75)
            self.data_handling.on_extract_MS_from_mobiligram(11, 15, "Arrival time (ms)")

        # exit
        self.view.on_close(None, clean_exit=True, ignore_warning=True)

    def on_import_configuration_on_startup(self):
        """This function imports configuration file"""

        self.config.loadConfigXML(path="configOut.xml")

    def on_start_logging(self):
        """Setup logger"""

        log_directory = os.path.join(self.config.cwd, "logs")
        if not os.path.exists(log_directory):
            print("Directory logs did not exist - created a new one in {}".format(log_directory))
            os.makedirs(log_directory)

        # Generate filename
        if self.config.loggingFile_path is None:

            file_path = "origami_{}.log".format(self.config.startTime)
            self.config.loggingFile_path = os.path.join(log_directory, file_path)

        # setup logger
        set_logger(file_path=self.config.loggingFile_path, debug_mode=self.config.debug)
        set_logger_level(verbose="DEBUG")

        logger.info("Logs can be found in {}".format(self.config.loggingFile_path))

    def on_create_document(self, name, path, **kwargs):
        """
        Create document
        """
        document = documents()
        document.title = name
        document.path = path
        document.userParameters = self.config.userParameters
        document.userParameters["date"] = getTime()
        document.dataType = kwargs.get("data_type", "Type: Other")
        document.fileFormat = kwargs.get("file_format", "Format: Other")

        return document

    def _debug_(self):
        import wx.lib.inspection

        wx.lib.inspection.InspectionTool().Show()

    def onThreading(self, evt, args, action="loadOrigami"):

        if action == "saveFigs":
            target, path, kwargs = args
            th = threading.Thread(target=target.save_figure, args=(path,), kwargs=kwargs)

        elif action == "updateStatusbar":
            if len(args) == 2:
                msg, position = args
                th = threading.Thread(target=self.view.updateStatusbar, args=(msg, position))
            elif len(args) == 3:
                msg, position, delay = args
                th = threading.Thread(target=self.view.updateStatusbar, args=(msg, position, delay))
        elif action == "export_settings":
            th = threading.Thread(target=self.config.saveConfigXML, args=args)

        # Start thread
        try:
            th.start()
        except Exception:
            print("Failed to execute the operation in threaded mode. Consider switching it off?")

    # def onLinearDTirectory(self, e=None):
    # # self.config.ciuMode = 'LinearDT'
    # # self.config.extractMode = 'singleIon'
    #
    # # Reset arrays
    # imsData2D = np.array([])
    # dlg = wx.DirDialog(self.view, "Choose a MassLynx file:",
    #                    style=wx.DD_DEFAULT_STYLE)
    # if self.config.dirname == '':
    #     pass
    # else:
    #     dlg.SetPath(self.config.dirname)
    # if dlg.ShowModal() == wx.ID_OK:
    #     tstart = time.clock()
    #     print("You chose %s" % dlg.GetPath())
    #     # Update statusbar
    #     self.onThreading(None, ("Opened: {}".format(dlg.GetPath()), 4), action='updateStatusbar')
    #     # Get experimental parameters
    #     parameters = self.config.get_waters_inf_data(path=dlg.GetPath())
    #     xlimits = [parameters['startMS'], parameters['endMS']]
    #     # Mass spectra
    #     extract_kwargs = {'return_data': True}
    #     msDataX, msDataY = io_waters.driftscope_extract_MS(path=dlg.GetPath(),
    #                                                         driftscope_path=self.config.driftscopePath,
    #                                                         **extract_kwargs)
    #
    #     # RT
    #     extract_kwargs = {'return_data': True, 'normalize': True}
    #     xvalsRT, rtDataY, rtDataYnorm = io_waters.driftscope_extract_RT(path=dlg.GetPath(),
    #                                                                      driftscope_path=self.config.driftscopePath,
    #                                                                      **extract_kwargs)
    #
    #     # 2D
    #     extract_kwargs = {'return_data': True}
    #     imsData2D = io_waters.driftscope_extract_2D(path=dlg.GetPath(),
    #                                                   driftscope_path=self.config.driftscopePath,
    #                                                   **extract_kwargs)
    #     xlabels = 1 + np.arange(len(imsData2D[1, :]))
    #     ylabels = 1 + np.arange(len(imsData2D[:, 1]))
    #
    #     # Update status bar with MS range
    #     self.view.SetStatusText("{}-{}".format(parameters.get('startMS', ""), parameters.get('endMS', "")), 1)
    #     self.view.SetStatusText("MSMS: {}".format(parameters.get('setMS', "")), 2)
    #
    #     tend = time.clock()
    #     self.onThreading(None, ('Total time to open file: %.2gs' % (tend - tstart), 4), action='updateStatusbar')
    #
    #     # Add info to document
    #     __, idName = os.path.split(dlg.GetPath())
    #     idName = (''.join([idName])).encode('ascii', 'replace')
    #     self.docs = documents()
    #     self.docs.title = idName
    #     self.currentDoc = idName  # Currently plotted document
    #     self.docs.userParameters = self.config.userParameters
    #     self.docs.userParameters['date'] = getTime()
    #     self.docs.path = dlg.GetPath()
    #     self.docs.parameters = parameters
    #     self.docs.dataType = 'Type: Multifield Linear DT'
    #     self.docs.fileFormat = 'Format: MassLynx (.raw)'
    #     # Add data
    #     self.docs.gotMS = True
    #     self.docs.massSpectrum = {'xvals': msDataX,
    #                               'yvals': msDataY,
    #                               'xlabels': 'm/z (Da)',
    #                               'xlimits': xlimits}
    #     self.docs.got1RT = True
    #     self.docs.RT = {'xvals': xvalsRT,
    #                     'yvals': rtDataYnorm,
    #                     'xlabels': 'Scans'}
    #     self.docs.got2DIMS = True
    #     # Format: zvals, xvals, xlabel, yvals, ylabel
    #     self.docs.IMS2D = {'zvals': imsData2D,
    #                        'xvals': xlabels,
    #                         'xlabels': 'Scans',
    #                         'yvals': ylabels,
    #                         'ylabels': 'Drift time (bins)',
    #                         'cmap': self.docs.colormap}
    #
    #     # Plots
    #     self.view.panelPlots.on_plot_RT(xvalsRT, rtDataYnorm, 'Scans')
    #     name_kwargs = {"document": self.docs.title, "dataset": "Mass Spectrum"}
    #     self.view.panelPlots.on_plot_MS(msDataX, msDataY, xlimits=xlimits, **name_kwargs)
    #
    #     # Update document
    #     self.OnUpdateDocument(self.docs, 'document')
    #
    # dlg.Destroy()
    # return None
    #
    # def onCalibrantRawDirectory(self, e=None):
    # """
    # This function opens calibrant file
    # """
    #
    # # Reset arrays
    # dlg = wx.DirDialog(self.view, "Choose a MassLynx file:",
    #                    style=wx.DD_DEFAULT_STYLE)
    #
    # if dlg.ShowModal() == wx.ID_OK:
    #     tstart = time.clock()
    #     # Check whether appropriate calibration file was selected
    #     path = self.checkIfRawFile(dlg.GetPath())
    #     if path is None:
    #         msg = "Are you sure this was a MassLynx (.raw) file? Please load file in correct file format."
    #         DialogBox(exceptionTitle='Please load MassLynx (.raw) file',
    #                exceptionMsg=msg,
    #                type="Error")
    #         return
    #     print("You chose %s" % dlg.GetPath())
    #     # Update statusbar
    #     self.onThreading(None, ("Opened: {}".format(dlg.GetPath()), 4), action='updateStatusbar')
    #     # Get experimental parameters
    #     parameters = self.config.get_waters_inf_data(path=dlg.GetPath())
    #     xlimits = [parameters['startMS'], parameters['endMS']]
    #     # Mass spectra
    #     extract_kwargs = {'return_data': True}
    #     msDataX, msDataY = io_waters.driftscope_extract_MS(path=dlg.GetPath(),
    #                                                         driftscope_path=self.config.driftscopePath,
    #                                                         **extract_kwargs)
    #     # RT
    #     extract_kwargs = {'return_data': True, 'normalize': True}
    #     xvalsRT, rtDataY, rtDataYnorm = io_waters.driftscope_extract_RT(path=dlg.GetPath(),
    #                                                                      driftscope_path=self.config.driftscopePath,
    #                                                                      **extract_kwargs)
    #
    #     # DT
    #     extract_kwargs = {'return_data': True}
    #     xvalsDT, imsData1D = io_waters.driftscope_extract_DT(path=dlg.GetPath(),
    #                                                           driftscope_path=self.config.driftscopePath,
    #                                                           **extract_kwargs)
    #
    #     # Update status bar with MS range
    #     self.view.SetStatusText("{}-{}".format(parameters['startMS'], parameters['endMS']), 1)
    #     self.view.SetStatusText("MSMS: {}".format(parameters['setMS']), 2)
    #     tend = time.clock()
    #     self.onThreading(None, ('Total time to open file: %.2gs' % (tend - tstart), 4),
    #                      action='updateStatusbar')
    #
    #     # Add info to document
    #     __, idName = os.path.split(dlg.GetPath())
    #     idName = (''.join([idName])).encode('ascii', 'replace')
    #     self.docs = documents()
    #     self.docs.title = idName
    #     self.currentDoc = idName  # Currently plotted document
    #     self.docs.path = dlg.GetPath()
    #     self.docs.userParameters = self.config.userParameters
    #     self.docs.userParameters['date'] = getTime()
    #     self.docs.parameters = parameters
    #     self.docs.dataType = 'Type: CALIBRANT'
    #     self.docs.fileFormat = 'Format: MassLynx (.raw)'
    #     self.docs.corrC = parameters['corrC']
    #     # Add data
    #     self.docs.gotMS = True
    #     self.docs.massSpectrum = {'xvals': msDataX,
    #                               'yvals': msDataY,
    #                               'xlabels': 'm/z (Da)',
    #                               'xlimits': xlimits}
    #     self.docs.got1RT = True
    #     self.docs.RT = {'xvals': xvalsRT,
    #                     'yvals': rtDataYnorm,
    #                     'xlabels': 'Scans'}
    #     self.docs.got1DT = True
    #     self.docs.DT = {'xvals': xvalsDT,
    #                     'yvals': imsData1D,
    #                     'xlabels': 'Drift time (bins)',
    #                     'ylabels': 'Intensity'}
    #
    #     # Add plots
    #     self.view.panelPlots.on_plot_RT(xvalsRT, rtDataYnorm, 'Scans')
    #     self.onPlotMSDTCalibration(msX=msDataX,
    #                                msY=msDataY,
    #                                xlimits=xlimits,
    #                                dtX=xvalsDT,
    #                                dtY=imsData1D,
    #                                xlabelDT='Drift time (bins)',
    #                                color=self.docs.lineColour)
    #
    #     self.view.panelPlots.mainBook.SetSelection(self.config.panelNames['Calibration'])
    #
    #     # Update document
    #     self.OnUpdateDocument(self.docs, 'document')
    #
    # dlg.Destroy()
    # return None
    #
    # def onAddCalibrantMultiple(self, evt):
    #
    # tempList = self.view.panelCCS.topP.peaklist
    # for row in range(tempList.GetItemCount()):
    #     if evt.GetId() == ID_extractCCScalibrantAll:
    #         pass
    #     elif evt.GetId() == ID_extractCCScalibrantSelected:
    #         if not tempList.IsChecked(index=row):
    #             continue
    #
    #     # Get values
    #     filename = tempList.GetItem(itemId=row, col=self.config.ccsTopColNames['filename']).GetText()
    #     mzStart = str2num(tempList.GetItem(itemId=row, col=self.config.ccsTopColNames['start']).GetText())
    #     mzEnd = str2num(tempList.GetItem(itemId=row, col=self.config.ccsTopColNames['end']).GetText())
    #     rangeName = ''.join([str(mzStart), '-', str(mzEnd)])
    #
    #     # Get the document
    #     document = self.documentsDict[filename]
    #     if document.fileFormat == 'Format: DataFrame':
    #         print(('Skipping %s as this is a DataFrame document.' % rangeName))
    #         continue
    #
    #     extract_kwargs = {'return_data': True}
    #     __, yvalsDT = io_waters.driftscope_extract_DT(path=document.path,
    #                                                    driftscope_path=self.config.driftscopePath,
    #                                                    **extract_kwargs)
    #     mphValue = (max(yvalsDT)) * 0.2  # 20 % cutoff
    #     # Get pusher
    #     pusherFreq = document.parameters.get('pusherFreq', 1)
    #
    #     if pusherFreq != 1:
    #         xlabel = 'Drift time (ms)'
    #     else:
    #         xlabel = 'Drift time (bins)'
    #     # Create x-labels in ms
    #     xvalsDT = (np.arange(1, len(yvalsDT) + 1) * pusherFreq) / 1000
    #
    #     # Detect peak
    #     ind = detectPeaks(x=yvalsDT, mph=mphValue)
    #     if len(ind) > 1:
    #         self.view.SetStatusText('Found more than one peak. Selected the first one', 3)
    #         tD = np.round(xvalsDT[ind[0]], 2)
    #         print((ind[0], tD))
    #         yval = np.round(yvalsDT[ind[0]], 2)
    #         yval = pr_spectra.normalize_1D(yval)
    #     elif len(ind) == 0:
    #         self.view.SetStatusText('Found no peaks', 3)
    #         tD = ""
    #     else:
    #         self.view.SetStatusText('Found one peak', 3)
    #         tD = np.round(xvalsDT[ind[0]], 2)
    # #                 print(ind[0], tD)
    #         yval = np.round(yvalsDT[ind[0]], 2)
    #         yval = pr_spectra.normalize_1D(yval)
    #
    #     # Add data to document
    #     protein, charge, CCS, gas, mw = None, None, None, None, None
    #
    #     # Check whether the document has molecular weight
    #     mw = document.moleculeDetails.get('molWeight', None)
    #     protein = document.moleculeDetails.get('protein', None)
    #
    #     document.gotCalibration = True
    #     document.calibration[rangeName] = {'xrange': [mzStart, mzEnd],
    #                                        'xvals': xvalsDT,
    #                                        'yvals': yvalsDT,
    #                                        'xcentre': ((mzEnd + mzStart) / 2),
    #                                        'protein': protein,
    #                                        'charge': charge,
    #                                        'ccs': CCS, 'tD': tD,
    #                                        'gas': gas,
    #                                        'xlabels': xlabel,
    #                                        'peak': [tD, yval],
    #                                        'mw': mw
    #                                        }
    #     # Plot
    #     self.onPlot1DTCalibration(dtX=xvalsDT,
    #                               dtY=yvalsDT,
    #                               xlabel=xlabel,
    #                               color=document.lineColour)
    #
    #     if tD != "":
    #         self.addMarkerMS(xvals=tD,
    #                          yvals=yval,
    #                          color=self.config.annotColor,
    #                          marker=self.config.markerShape,
    #                          size=self.config.markerSize,
    #                          plot='CalibrationDT')
    #
    #     # Update document
    #     self.OnUpdateDocument(document, 'document')

    def get_overlay_document(self):
        try:
            self.currentDoc = self.view.panelDocuments.documents.enableCurrentDocument()
        except Exception:
            return
        if self.currentDoc == "Documents":
            return

        # Check if current document is a comparison document
        # If so, it will be used
        if self.documentsDict[self.currentDoc].dataType == "Type: Comparison":
            document = self.documentsDict[self.currentDoc]
            self.onThreading(
                None, ("Using document: " + document.title.encode("ascii", "replace"), 4), action="updateStatusbar"
            )
        else:
            docList = self.checkIfAnyDocumentsAreOfType(type="Type: Comparison")
            if len(docList) == 0:
                print("Did not find appropriate document.")
                dlg = wx.FileDialog(
                    self.view,
                    "Please select a name for the comparison document",
                    "",
                    "",
                    "",
                    wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
                )
                if dlg.ShowModal() == wx.ID_OK:
                    path, idName = os.path.split(dlg.GetPath())
                else:
                    return
                # Create document
                document = documents()
                document.title = idName
                document.path = path
                document.userParameters = self.config.userParameters
                document.userParameters["date"] = getTime()
                document.dataType = "Type: Comparison"
                document.fileFormat = "Format: ORIGAMI"
            else:
                self.selectDocDlg = DialogSelectDocument(self.view, presenter=self, document_list=docList)
                if self.selectDocDlg.ShowModal() == wx.ID_OK:
                    pass

                # Check that document exists
                if self.currentDoc is None:
                    self.onThreading(None, ("Please select comparison document", 4), action="updateStatusbar")
                    return
                document = self.documentsDict[self.currentDoc]
                self.onThreading(
                    None, ("Using document: " + document.title.encode("ascii", "replace"), 4), action="updateStatusbar"
                )

        return document

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
        msg = "".join([""])
        if idxXmax == 0:
            msg = "Your Xmax value is too small - reseting to maximum"
            idxXmax = len(xvals)
        if idxXmin == idxXmax:
            msg = "Your X-axis values are too close together - reseting to original view"
            idxXmin = 0
            idxXmax = len(xvals)

        if idxYmax == 0:
            msg = "Your Ymax value is too small - reseting to maximum"
            idxYmax = len(yvals)
        if idxYmin == idxYmax:
            msg = "Your Y-axis values are too close together - reseting to original view"
            idxYmin = 0
            idxYmax = len(yvals)

        zvals = zvals[idxYmin:idxYmax, idxXmin:idxXmax]
        xvals = xvals[idxXmin:idxXmax]
        yvals = yvals[idxYmin:idxYmax]
        self.onThreading(None, (msg, 4), action="updateStatusbar")

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
        if self.currentDoc == "Documents":
            return

        # Make sure the document is of comparison type
        if self.documentsDict[self.currentDoc].dataType == "Type: Comparison":
            # Enable text panel
            self.view.on_toggle_panel(evt=ID_window_textList, check=True)
            #             self.view.textView = False
            #             self.view.mainToolbar.ToggleTool(id=ID_OnOff_textView, toggle=True)
            #             self.view._mgr.GetPane(self.view.panelMultipleText).Show()
            #             self.view._mgr.Update()
            tempList = self.view.panelMultipleText.peaklist
            document = self.documentsDict[self.currentDoc]
            if document.gotComparisonData:
                filename = document.title
                for key in document.IMS2DcompData:
                    xvals = document.IMS2DcompData[key]["xvals"]
                    shape = document.IMS2DcompData[key]["shape"]
                    label = document.IMS2DcompData[key]["label"]
                    cmap = document.IMS2DcompData[key]["cmap"]
                    alpha = document.IMS2DcompData[key]["alpha"]
                    tempList.Append([filename, xvals[0], xvals[-1], cmap, str(alpha), label, shape, key])

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

        args = ("Added RMSD label at xpos: {} ypos {}".format(rmsdXpos, rmsdYpos), 4)
        self.onThreading(None, args, action="updateStatusbar")

        return rmsdXpos, rmsdYpos

    def onProcessMultipleIonsIons(self, evt):
        """
        This function processes the 2D array data from multiple ions MULTIFILE or ORIGAMI
        """
        # Shortcut to table
        tempList = self.view.panelMultipleIons.peaklist

        # Make a list of Documents
        for row in range(tempList.GetItemCount()):
            self.currentDoc = tempList.GetItem(itemId=row, col=self.config.peaklistColNames["filename"]).GetText()
            # Check that data was extracted first
            if self.currentDoc == "":
                self.onThreading(None, ("Please extract data first", 4), action="updateStatusbar")
                continue
            if evt.GetId() == ID_processAllIons:
                pass
            elif evt.GetId() == ID_processSelectedIons:
                if not tempList.IsChecked(index=row):
                    continue
            # Extract ion name
            mzStart = tempList.GetItem(itemId=row, col=self.config.peaklistColNames["start"]).GetText()
            mzEnd = tempList.GetItem(itemId=row, col=self.config.peaklistColNames["end"]).GetText()
            selectedItem = "".join([str(mzStart), "-", str(mzEnd)])
            # strip any processed string from the title
            dataset = selectedItem
            if "(processed)" in selectedItem:
                dataset = selectedItem.split(" (")[0]
            new_dataset = "%s (processed)" % dataset
            # Select document
            self.docs = self.documentsDict[self.currentDoc]
            dataType = self.docs.dataType

            # process data
            if dataType in ["Type: ORIGAMI", "Type: Infrared", "Type: MANUAL"] and self.docs.gotCombinedExtractedIons:
                try:
                    tempData = self.docs.IMS2DCombIons[selectedItem]
                    imsData2D, params = self.data_processing.on_process_2D(
                        zvals=tempData["zvals"].copy(), return_all=True
                    )
                    imsData1D = np.sum(imsData2D, axis=1).T
                    rtDataY = np.sum(imsData2D, axis=0)
                    self.docs.IMS2DCombIons[new_dataset] = {
                        "zvals": imsData2D,
                        "xvals": tempData["xvals"],
                        "xlabels": tempData["xlabels"],
                        "yvals": tempData["yvals"],
                        "ylabels": tempData["ylabels"],
                        "yvals1D": imsData1D,
                        "yvalsRT": rtDataY,
                        "cmap": tempData.get("cmap", self.config.currentCmap),
                        "xylimits": tempData["xylimits"],
                        "charge": tempData.get("charge", None),
                        "label": tempData.get("label", None),
                        "alpha": tempData.get("alpha", None),
                        "mask": tempData.get("alpha", None),
                        "process_parameters": params,
                    }
                except Exception:
                    pass

            if dataType in ["Type: ORIGAMI", "Type: Infrared"] and self.docs.gotExtractedIons:
                try:
                    tempData = self.docs.IMS2Dions[selectedItem]
                    imsData2D, params = self.data_processing.on_process_2D(
                        zvals=tempData["zvals"].copy(), return_all=True
                    )
                    imsData1D = np.sum(imsData2D, axis=1).T
                    rtDataY = np.sum(imsData2D, axis=0)
                    self.docs.IMS2Dions[new_dataset] = {
                        "zvals": imsData2D,
                        "xvals": tempData["xvals"],
                        "xlabels": tempData["xlabels"],
                        "yvals": tempData["yvals"],
                        "ylabels": tempData["ylabels"],
                        "yvals1D": imsData1D,
                        "yvalsRT": rtDataY,
                        "cmap": tempData.get("cmap", self.config.currentCmap),
                        "xylimits": tempData["xylimits"],
                        "charge": tempData.get("charge", None),
                        "label": tempData.get("label", None),
                        "alpha": tempData.get("alpha", None),
                        "mask": tempData.get("alpha", None),
                        "process_parameters": params,
                    }
                except Exception:
                    pass

            # Update file list
            self.OnUpdateDocument(self.docs, "combined_ions")

    def getImageFilename(self, prefix=False, csv=False, defaultValue="", withPath=False, extension=None):
        """
        Set-up a new filename for saved images
        """

        if withPath:
            if extension is None:
                fileType = "Text file|*%s" % self.config.saveExtension
            else:
                fileType = extension
            dlg = wx.FileDialog(
                self.view, "Save data to file...", "", "", fileType, wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
            )
            dlg.SetFilename(defaultValue)
            if dlg.ShowModal() == wx.ID_OK:
                filename = dlg.GetPath()
                return filename
            else:
                return None
        elif not prefix:
            saveFileName = DialogSimpleAsk(
                "Please enter a new filename for the images. Names will be appended with the item keyword.",
                defaultValue=defaultValue,
            )
        else:
            if not csv:
                saveFileName = DialogSimpleAsk(
                    "Please enter a new prefix for the images. Names will be appended with the item keyword.",
                    defaultValue=defaultValue,
                )
            else:
                saveFileName = DialogSimpleAsk(
                    "Please enter a new prefix for the output file. Names will be appended with the item keyword.",
                    defaultValue=defaultValue,
                )

        return saveFileName

    # fmt: off
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
    #     if self.currentDoc == 'Documents':
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
    #         if self.currentDoc == "Documents":
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
    #                 self.selectDocDlg = DialogSelectDocument(self.view, self, docList)
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
    #             self.view.SetStatusText('Please select items in the table -
    # otherwise CCS calibration cannot be created', 3)
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
    #     def on_applyCCSCalibrationToSelectedIons(self, evt):
    #
    #         # Shortcut to the table
    #         tempList = self.view.panelCCS.bottomP.peaklist
    #         calibrationMode = self.view.panelCCS.bottomP.calibrationMode.GetStringSelection()
    #         for caliID in range(tempList.GetItemCount()):
    #             # Only add info if dataset was checked
    #             if tempList.IsChecked(index=caliID):
    #                 # Get document info
    #                 filename = tempList.GetItem(caliID, self.config.ccsBottomColNames['filename']).GetText()
    #                 mzStart = tempList.GetItem(caliID, self.config.ccsBottomColNames['start']).GetText()
    #                 mzEnd = tempList.GetItem(caliID, self.config.ccsBottomColNames['end']).GetText()
    #                 charge = str2int(tempList.GetItem(caliID, self.config.ccsBottomColNames['charge']).GetText())
    #                 mzCentre = str2num(tempList.GetItem(caliID, self.config.ccsBottomColNames['ion']).GetText())
    #                 selectedType = tempList.GetItem(caliID, self.config.ccsBottomColNames['format']).GetText()
    #                 rangeName = ''.join([str(mzStart), '-', str(mzEnd)])
    #
    #                 # Check these fields were filled in
    #                 if isempty(charge) or isempty(mzCentre):
    #                     msg = 'Please fill in the fields'
    #                     self.view.SetStatusText(msg, 3)
    #                     return
    #                 elif charge == 0:
    #                     msg = "
    # %s (%s) is missing charge value.
    # Please add charge information before trying to apply CCS calibration" % (
    #                         rangeName, filename)
    #                     DialogBox(exceptionTitle='Missing charge information',
    #                            exceptionMsg=msg,
    #                            type="Warning")
    #                     continue
    #                 # Get document object based on the filename
    #                 document = self.documentsDict[filename]
    #
    #                 # Select data based on the format of the object
    #                 if selectedType == '2D, extracted':
    #                     data = document.IMS2Dions[rangeName]
    #                 elif selectedType == '2D, combined':
    #                     data = document.IMS2DCombIons[rangeName]
    #                 elif selectedType == '2D, processed':
    #                     data = document.IMS2DionsProcess[rangeName]
    #
    #                 # Unpack data
    #                 zvals, xvals, xlabel, yvals, ylabel, charge, mw, mzCentre = self.get2DdataFromDictionary(
    #                     dictionary=data, dataType='calibration', compact=False)
    #                 # Check that the object has pusher frequency
    #                 pusherFreq = document.parameters.get('pusherFreq', 1)
    #
    #                 if (pusherFreq == 1 or not isnumber(pusherFreq)) and ylabel != 'Drift time (ms)':
    #                     msg = \
    #     "%s (%s) ion is missing pusher frequency value. Please modify it in the Notes,
    # Information and Labels panel" % (
    #                         filename, rangeName)
    #                     DialogBox(exceptionTitle='Missing data',
    #                            exceptionMsg=msg,
    #                            type="Error")
    #                     continue
    #                 # Check if ylabel is in ms
    #                 if ylabel != 'Drift time (ms)':
    #                     if ylabel == 'Drift time (bins)':
    #                         yvals = yvals * (pusherFreq / 1000)
    #                     else:
    #                         # Need to restore scans and convert them to ms
    #                         yvals = 1 + np.arange(len(zvals[:, 1]))
    #                         yvals = yvals * (pusherFreq / 1000)
    #
    #                 # Check for TOF correction factor
    #                 if isempty(document.corrC) and document.parameters.get('corrC', None) is None:
    #                     msg = 'Missing TOF correction factor'
    #                     self.view.SetStatusText(msg, 3)
    #                     return
    #
    #                 # Check for charge and m/z information
    #                 if not isnumber(charge) or not isnumber(mzCentre):
    #                     if not isnumber(charge):
    #                         msg = 'Missing charge information'
    #                     elif not isnumber(mzCentre):
    #                         msg = 'Missing m/z information'
    #                     self.view.SetStatusText(msg, 3)
    #                     return
    #
    #                 # Create empty DataFrame to calculate CCS
    #                 df = pd.DataFrame(columns=['m/z', 'z', 'tD', 'MW', 'RedMass', 'tDd', 'tDdd'],
    #                                   index=np.arange(0, len(yvals)))
    #                 df['m/z'] = float(mzCentre)
    #                 df['z'] = int(charge)
    #                 df['tD'] = yvals
    #
    #                 # Unpack calibration parameters
    #                 if len(self.currentCalibrationParams) == 0:
    #                     if document.gotCalibrationParameters:
    #                         self.currentCalibrationParams = document.calibrationParameters
    #
    #                 # Now assign the calibration parameters
    #                 try:
    #                     calibrationParameters = self.currentCalibrationParams.get('parameters', None)
    #                 except (IndexError, KeyError):
    #                     calibrationParameters = None
    #
    #                 if calibrationParameters is None:
    #                     # TODO: add function to search for calibration document
    #                     docList = self.checkIfAnyDocumentsAreOfType(type='Type: CALIBRANT',
    #                                                                 format='Format: DataFrame')
    #                     if len(docList) == 0:
    #                         msg = \
    #     "Cound not find calibration document or calibration file. Please create or load one in first"
    #                         DialogBox(exceptionTitle='Missing data',
    #                                exceptionMsg=msg,
    #                                type="Error")
    #                         return
    #                     else:
    #                         self.selectDocDlg = DialogSelectDocument(self.view, self, docList, allowNewDoc=False)
    #                         if self.selectDocDlg.ShowModal() == wx.ID_OK:
    #                             calibrationParameters = self.currentCalibrationParams.get('parameters', None)
    #                             if calibrationParameters is None:
    #                                 return
    #                         return
    #
    #                 # Get parameters
    #                 slopeLinear, interceptLinear, r2Linear = calibrationParameters['linear']
    #                 slopePower, interceptPower, r2Power = calibrationParameters['power']
    #                 slope, intercept = calibrationParameters['powerParms']
    #                 gas = calibrationParameters['gas']
    #
    #                 # Fill in remaining details
    #                 df['MW'] = (df['m/z'] - (self.config.elementalMass['Hydrogen'] * df['z'])) * df['z']
    #                 df['RedMass'] = ((df['MW'] * gas) / (df['MW'] + gas))
    #                 df['tDd'] = (df['tD'] - ((document.corrC * df['m/z'].apply(sqrt)) / 1000))
    #
    #                 # Linear law
    #                 df['CCSd'] = slopeLinear * df['tDd'] + interceptLinear
    #                 df['CCSlinear'] = df['CCSd'] * (df['z'] * (1 / df['RedMass']).apply(sqrt))
    #                 # Power law
    #                 df['tDdd'] = df['tDd'].pow(slope) * df['z'] * df['RedMass'].apply(sqrt)
    #                 df['CCSpower'] = (df['tDdd'] * slopePower) + interceptPower
    #
    #                 # Update dictionary
    #                 document.gotCalibrationParameters = True
    #                 document.calibrationParameters = self.currentCalibrationParams
    #                 document.calibrationParameters['mode'] = calibrationMode
    #
    #                 document.gas = gas
    #
    #                 if calibrationMode == 'Linear':
    #                     ccsVals = pd.to_numeric(df['CCSlinear']).values
    #                 elif calibrationMode == 'Power':
    #                     ccsVals = pd.to_numeric(df['CCSpower']).values
    #
    #                 # Assign data
    #                 if selectedType == '2D, extracted':
    #                     document.IMS2Dions[rangeName]['yvals'] = ccsVals
    #                     document.IMS2Dions[rangeName]['yvalsCCSBackup'] = ccsVals
    #                     document.IMS2Dions[rangeName]['ylabels'] = 'Collision Cross Section (Å²)'
    #                 elif selectedType == '2D, combined':
    #                     document.IMS2DCombIons[rangeName]['yvals'] = ccsVals
    #                     document.IMS2DCombIons[rangeName]['yvalsCCSBackup'] = ccsVals
    #                     document.IMS2DCombIons[rangeName]['ylabels'] = 'Collision Cross Section (Å²)'
    #                 elif selectedType == '2D, processed':
    #                     document.IMS2DionsProcess[rangeName]['yvals'] = ccsVals
    #                     document.IMS2DionsProcess[rangeName]['yvalsCCSBackup'] = ccsVals
    #                     document.IMS2DionsProcess[rangeName]['ylabels'] = 'Collision Cross Section (Å²)'
    #
    #                 # Assign updated to dictionary
    #                 self.documentsDict[document.title] = document
    #
    #                 # Update documents tree
    #                 self.view.panelDocuments.documents.add_document(docData=document)
    #
    #         # Update status bar
    #         try:
    #             self.view.SetStatusText(''.join(['R² (linear): ', str(np.round(r2Linear, 4)),
    #                                              ' | R² (power): ', str(np.round(r2Power, 4)),
    #                                              ' | Used: ', calibrationMode, ' mode']), 3)
    #         except Exception:            pass
    #
    #     def OnAddDataToCCSTable(self, filename=None, mzStart=None, mzEnd=None,
    #                             mzCentre=None, charge=None, protein=None,
    #                             format=None, evt=None):
    #         """
    #         Add data to table and prepare DataFrame for CCS calibration
    #         """
    #         # Shortcut to the table
    #         tempList = self.view.panelCCS.bottomP.peaklist
    #
    #         # Add data to table
    #         tempList.Append([filename, mzStart, mzEnd,
    #                          mzCentre, protein, charge, format])
    #
    #         # Remove duplicates
    #         self.view.panelCCS.bottomP.onRemoveDuplicates(evt=None)
    #         # Enable and show CCS table
    #         self.view.on_toggle_panel(evt=ID_window_ccsList, check=True)
    #
    #     def saveCCScalibrationToPickle(self, evt):
    #         """
    #         Save CCS calibration parameters to file
    #         """
    #         try:
    #             self.currentDoc = self.view.panelDocuments.documents.enableCurrentDocument()
    #         except Exception:            return
    #         if self.currentDoc == "Documents":
    #             return
    #
    #         # Check if the currently selected document is Calibration dataframe file
    #         if (self.documentsDict[self.currentDoc].dataType == 'Type: CALIBRANT' and
    #                 self.documentsDict[self.currentDoc].fileFormat == 'Format: DataFrame'):
    #             self.docs = self.documentsDict[self.currentDoc]
    #             self.view.SetStatusText('Using document: ' + self.docs.title.encode('ascii', 'replace'), 3)
    #         else:
    #             docList = self.checkIfAnyDocumentsAreOfType(type='Type: CALIBRANT',
    #                                                         format='Format: DataFrame')
    #             if len(docList) == 0:
    #                 print('Did not find appropriate document.')
    #                 return
    #             else:
    #                 self.DocDlg = DialogSelectDocument(self.view, self, docList, allowNewDoc=False)
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
    #         # Get calibration parameters
    #         # Unpack calibration parameters
    #         if len(self.currentCalibrationParams) == 0:
    #             if self.docs.gotCalibrationParameters:
    #                 self.currentCalibrationParams = self.docs.calibrationParameters
    #
    #         # Save parameters
    #         fileType = "ORIGAMI Document File|*.pickle"
    #         dlg = wx.FileDialog(self.view, "Save CCS calibration to file...", "", "", fileType,
    #                             wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
    #         defaultFilename = self.docs.title.split(".")
    #         defaultFilename = "".join([defaultFilename[0], '_CCScaliParams'])
    #         dlg.SetFilename(defaultFilename)
    #
    #         if dlg.ShowModal() == wx.ID_OK:
    #             saveFileName = dlg.GetPath()
    #             # Save
    #             saveObject(filename=saveFileName, saveFile=self.currentCalibrationParams)
    #         else:
    #             return

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
    # fmt: on

    def onProcessMultipleTextFiles(self, evt):

        if evt.GetId() == ID_textPanel_process_all:
            self.view.panelMultipleText.OnCheckAllItems(evt=None, override=True)

        tempList = self.view.panelMultipleText.peaklist
        try:
            for row in range(tempList.GetItemCount()):
                itemInfo = self.view.panelMultipleText.on_get_item_information(itemID=row)
                if itemInfo["select"]:
                    self.docs = self.documentsDict[itemInfo["document"]]
                    imsData2D = self.data_processing.on_process_2D(
                        zvals=self.docs.IMS2D["zvals"].copy(), return_data=True
                    )
                    self.docs.got2Dprocess = True
                    self.docs.IMS2Dprocess = {
                        "zvals": imsData2D,
                        "xvals": self.docs.IMS2D["xvals"],
                        "xlabels": self.docs.IMS2D["xlabels"],
                        "yvals": self.docs.IMS2D["yvals"],
                        "ylabels": self.docs.IMS2D["ylabels"],
                        "cmap": itemInfo["colormap"],
                        "label": itemInfo["label"],
                        "charge": itemInfo["charge"],
                        "alpha": itemInfo["alpha"],
                        "mask": itemInfo["mask"],
                        "color": itemInfo["color"],
                        "min_threshold": itemInfo["min_threshold"],
                        "max_threshold": itemInfo["max_threshold"],
                    }

                    # Update file list
                    self.OnUpdateDocument(self.docs, "document")
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

            elif self.documentsDict[key].dataType == type and self.documentsDict[key].fileFormat == format:
                listOfDocs.append(key)

            else:
                continue

        return listOfDocs

    def get2DdataFromDictionary(self, dictionary=None, dataType="plot", compact=False, plotType="2D"):
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
        if plotType == "2D":
            # These are always there
            zvals = dictionary["zvals"].copy()
            xvals = dictionary["xvals"]
            xlabels = dictionary["xlabels"]
            yvals = dictionary["yvals"]
            ylabels = dictionary["ylabels"]
            cmap = dictionary.get("cmap", self.config.currentCmap)
            charge = dictionary.get("charge", None)
            mw = dictionary.get("mw", None)
            mzCentre = dictionary.get("xcentre", None)

            #             if cmap == '' or cmap is None: cmap = 'viridis'
            if dataType == "all":
                if compact:
                    data = zvals, xvals, xlabels, yvals, ylabels, cmap, charge
                    return data
                else:
                    return zvals, xvals, xlabels, yvals, ylabels, cmap, charge
            elif dataType == "plot":
                if compact:
                    data = zvals, xvals, xlabels, yvals, ylabels, cmap
                    return data
                else:
                    return zvals, xvals, xlabels, yvals, ylabels, cmap
            elif dataType == "calibration":
                return zvals, xvals, xlabels, yvals, ylabels, charge, mw, mzCentre
        if plotType == "1D":
            xvals = dictionary["xvals"]
            try:
                xlabels = dictionary["xlabels"]
            except Exception:
                xlabels = dictionary["xlabel"]
            yvals = dictionary["yvals"]
            try:
                cmap = dictionary["cmap"]
            except KeyError:
                cmap = [0, 0, 0]

            try:
                xlimits = dictionary["xlimits"]
            except KeyError:
                xlimits = None
            if dataType == "plot":
                if compact:
                    data = xvals, yvals, xlabels, cmap
                    return data
                else:
                    return xvals, yvals, xlabels, cmap
        elif plotType == "Overlay":
            zvals1 = dictionary["zvals1"]
            zvals2 = dictionary["zvals2"]
            cmapIon1 = dictionary["cmap1"]
            cmapIon2 = dictionary["cmap2"]
            alphaIon1 = dictionary["alpha1"]
            alphaIon2 = dictionary["alpha2"]
            xvals = dictionary["xvals"]
            xlabel = dictionary["xlabels"]
            yvals = dictionary["yvals"]
            ylabel = dictionary["ylabels"]
            try:
                charge1 = dictionary["charge1"]
                charge2 = dictionary["charge2"]
            except KeyError:
                charge1 = None
                charge2 = None
            if dataType == "plot":
                if compact:
                    return
                else:
                    return (
                        zvals1,
                        zvals2,
                        cmapIon1,
                        cmapIon2,
                        alphaIon1,
                        alphaIon2,
                        xvals,
                        xlabel,
                        yvals,
                        ylabel,
                        charge1,
                        charge2,
                    )
        elif plotType == "Matrix":
            zvals = dictionary["zvals"]
            xylabels = dictionary["matrixLabels"]
            cmap = dictionary["cmap"]
            return zvals, xylabels, cmap
        elif plotType == "RMSF":
            zvals = dictionary["zvals"]
            yvalsRMSF = dictionary["yvalsRMSF"]
            xvals = dictionary["xvals"]
            yvals = dictionary["yvals"]
            xlabelRMSD = dictionary["xlabelRMSD"]
            ylabelRMSD = dictionary["ylabelRMSD"]
            ylabelRMSF = dictionary["ylabelRMSF"]
            color = dictionary["colorRMSF"]
            cmap = dictionary["cmapRMSF"]
            rmsdLabel = dictionary["rmsdLabel"]
            return zvals, yvalsRMSF, xvals, yvals, xlabelRMSD, ylabelRMSD, ylabelRMSF, color, cmap, rmsdLabel
        elif plotType == "RMSD":
            zvals = dictionary["zvals"]
            xvals = dictionary["xvals"]
            xlabels = dictionary["xlabel"]
            yvals = dictionary["yvals"]
            ylabels = dictionary["ylabel"]
            rmsdLabel = dictionary["rmsdLabel"]
            cmap = dictionary["cmap"]
            return zvals, xvals, xlabels, yvals, ylabels, rmsdLabel, cmap
        elif plotType == "Overlay1D":
            xvals = dictionary["xvals"]
            yvals = dictionary["yvals"]
            xlabels = dictionary["xlabel"]
            colors = dictionary["colors"]
            labels = dictionary["labels"]
            xlimits = dictionary.get("xlimits", None)
            return xvals, yvals, xlabels, colors, labels, xlimits

    @staticmethod
    def getOverlayDataFromDictionary(dictionary=None, dataType="plot", compact=False):
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
        zvals1 = dictionary["zvals1"]
        zvals2 = dictionary["zvals2"]
        cmap1 = dictionary["cmap1"]
        cmap2 = dictionary["cmap2"]
        alpha1 = dictionary["alpha1"]
        alpha2 = dictionary["alpha2"]
        mask1 = dictionary["mask1"]
        mask2 = dictionary["mask2"]
        xvals = dictionary["xvals"]
        xlabels = dictionary["xlabels"]
        yvals = dictionary["yvals"]
        ylabels = dictionary["ylabels"]
        if dataType == "plot":
            if compact:
                data = [zvals1, zvals2, cmap1, cmap2, alpha1, alpha2, mask1, mask2, xvals, yvals, xlabels, ylabels]
                return data
            else:
                return zvals1, zvals2, cmap1, cmap2, alpha1, alpha2, mask1, mask2, xvals, yvals, xlabels, ylabels

    def _get_replot_data(self, data_format):
        """
        @param data_format (str): type of data to be returned
        """
        # new in 1.1.0
        if data_format == "2D":
            get_data = self.config.replotData.get("2D", None)
            zvals, xvals, yvals, xlabel, ylabel = None, None, None, None, None
            if get_data is not None:
                zvals = get_data["zvals"].copy()
                xvals = get_data["xvals"]
                yvals = get_data["yvals"]
                xlabel = get_data["xlabels"]
                ylabel = get_data["ylabels"]
            return zvals, xvals, yvals, xlabel, ylabel
        elif data_format == "RMSF":
            get_data = self.config.replotData.get("RMSF", None)
            zvals, xvals, yvals, xlabelRMSD, ylabelRMSD, ylabelRMSF = None, None, None, None, None, None
            if get_data is not None:
                zvals = get_data["zvals"].copy()
                xvals = get_data["xvals"]
                yvals = get_data["yvals"]
                xlabelRMSD = get_data["xlabelRMSD"]
                ylabelRMSD = get_data["ylabelRMSD"]
                ylabelRMSF = get_data["ylabelRMSF"]
            return zvals, xvals, yvals, xlabelRMSD, ylabelRMSD, ylabelRMSF
        elif data_format == "DT/MS":
            get_data = self.config.replotData.get("DT/MS", None)
            zvals, xvals, yvals, xlabel, ylabel = None, None, None, None, None
            if get_data is not None:
                zvals = get_data["zvals"].copy()
                xvals = get_data["xvals"]
                yvals = get_data["yvals"]
                xlabel = get_data["xlabels"]
                ylabel = get_data["ylabels"]
            return zvals, xvals, yvals, xlabel, ylabel
        elif data_format == "MS":
            get_data = self.config.replotData.get("MS", None)
            xvals, yvals, xlimits = None, None, None
            if get_data is not None:
                xvals = get_data.get("xvals", None)
                yvals = get_data.get("yvals", None)
                xlimits = get_data.get("xlimits", None)
            return xvals, yvals, xlimits
        elif data_format == "RT":
            get_data = self.config.replotData.get("RT", None)
            xvals, yvals, xlabel = None, None, None
            if get_data is not None:
                xvals = get_data.get("xvals", None)
                yvals = get_data.get("yvals", None)
                xlabel = get_data.get("xlabel", None)
            return xvals, yvals, xlabel
        elif data_format == "1D":
            get_data = self.config.replotData.get("1D", None)
            xvals, yvals, xlabel = None, None, None
            if get_data is not None:
                xvals = get_data.get("xvals", None)
                yvals = get_data.get("yvals", None)
                xlabel = get_data.get("xlabel", None)
            return xvals, yvals, xlabel
        elif data_format == "Matrix":
            get_data = self.config.replotData.get("Matrix", None)
            zvals, xylabels, cmap = None, None, None
            if get_data is not None:
                zvals = get_data.get("zvals", None)
                xylabels = get_data.get("xylabels", None)
                cmap = get_data.get("cmap", None)
            return zvals, xylabels, cmap

    #     def plot_1D_update(self, plotName='all', evt=None):
    #
    #         plt_kwargs = self.view.panelPlots._buildPlotParameters(plotType='1D')
    #
    #         if plotName in ['all', 'MS']:
    #             try:
    #                 self.view.panelPlots.plot1.plot_1D_update(**plt_kwargs)
    #                 self.view.panelPlots.plot1.repaint()
    #             except AttributeError:
    #                 pass
    #
    #         if plotName in ['all', 'RT']:
    #             try:
    #                 self.view.panelPlots.plotRT.plot_1D_update(**plt_kwargs)
    #                 self.view.panelPlots.plotRT.repaint()
    #             except AttributeError:
    #                 pass
    #
    #         if plotName in ['all', '1D']:
    #             try:
    #                 self.view.panelPlots.plot1D.plot_1D_update(**plt_kwargs)
    #                 self.view.panelPlots.plot1D.repaint()
    #             except AttributeError:
    #                 pass
    #
    #     def plot_2D_update(self, plotName='all', evt=None):
    #         plt_kwargs = self.view.panelPlots._buildPlotParameters(plotType='2D')
    #
    #         if plotName in ['all', '2D']:
    #             try:
    #                 zvals, __, __, __, __ = self._get_replot_data('2D')
    #                 # normalize
    #                 cmapNorm = self.normalize_colormap(
    #                     zvals,
    #                     min=self.config.minCmap,
    #                     mid=self.config.midCmap,
    #                     max=self.config.maxCmap,
    #                 )
    #                 plt_kwargs['colormap_norm'] = cmapNorm
    #
    #                 self.view.panelPlots.plot2D.plot_2D_update(**plt_kwargs)
    #                 self.view.panelPlots.plot2D.repaint()
    #             except AttributeError:
    #                 pass
    #
    #         if plotName in ['all', 'DT/MS']:
    #             try:
    #                 zvals, __, __, __, __ = self._get_replot_data('DT/MS')
    #                 # normalize
    #                 cmapNorm = self.normalize_colormap(
    #                     zvals,
    #                     min=self.config.minCmap,
    #                     mid=self.config.midCmap,
    #                     max=self.config.maxCmap,
    #                 )
    #                 plt_kwargs['colormap_norm'] = cmapNorm
    #                 self.view.panelPlots.plot_DT_vs_MS.plot_2D_update(**plt_kwargs)
    #                 self.view.panelPlots.plot_DT_vs_MS.repaint()
    #             except AttributeError:
    #                 pass
    #
    #     def plot_3D_update(self, plotName='all', evt=None):
    #         plt_kwargs = self.view.panelPlots._buildPlotParameters(plotType='3D')
    #
    #         if plotName in ['all', '3D']:
    #             try:
    #                 self.view.panelPlots.plot3D.plot_3D_update(**plt_kwargs)
    #                 self.view.panelPlots.plot3D.repaint()
    #             except AttributeError:
    #                 pass

    def on_add_label(self, x, y, text, rotation, color="k", plot="RMSD"):

        if plot == "RMSD":
            self.view.panelPlots.plot_RMSF.addText(
                x,
                y,
                text,
                rotation,
                color=self.config.rmsd_color,
                fontsize=self.config.rmsd_fontSize,
                weight=self.config.rmsd_fontWeight,
            )
            self.view.panelPlots.plot_RMSF.repaint()
        elif plot == "RMSF":
            self.view.panelPlots.plot_RMSF.addText(
                x,
                y,
                text,
                rotation,
                color=self.config.rmsd_color,
                fontsize=self.config.rmsd_fontSize,
                weight=self.config.rmsd_fontWeight,
            )
            self.view.panelPlots.plot_RMSF.repaint()
        elif plot == "Grid":
            self.view.panelPlots.plot_overlay.addText(
                x,
                y,
                text,
                rotation,
                color=self.config.rmsd_color,
                fontsize=self.config.rmsd_fontSize,
                weight=self.config.rmsd_fontWeight,
                plot=plot,
            )
            self.view.panelPlots.plot_overlay.repaint()

    def setXYlimitsRMSD2D(self, xvals, yvals):
        # Get min/max values
        xmin, xmax = xvals[0], xvals[-1]
        ymin, ymax = yvals[0], yvals[-1]
        self.config.xyLimitsRMSD = [xmin, xmax, ymin, ymax]

    def on_open_directory(self, path=None, evt=None):

        if path is None:
            path, title = self.getCurrentDocumentPath()
            if path is None or title is None:
                self.view.SetStatusText("Please select a document")
                return

        try:
            os.startfile(path)
        except WindowsError:
            DialogBox(
                exceptionTitle="This folder does not exist",
                exceptionMsg="Could not open the directory - this folder does not exist",
                type="Error",
            )
            return

    def getCurrentDocumentPath(self):
        """
        Function used to get the path to current document
        """
        # Gather info about the file and document
        self.currentDoc, __, __ = self.view.panelDocuments.documents.enableCurrentDocument(getSelected=True)
        if self.currentDoc == "Documents":
            return None, None
        document = self.documentsDict[self.currentDoc]
        return document.path, document.title

    # TODO: move to data_handling module
    def OnUpdateDocument(self, document, expand_item="document", expand_item_title=None):

        if expand_item == "document":
            self.view.panelDocuments.documents.add_document(docData=document, expandItem=document)
        elif expand_item == "ions":
            if expand_item_title is None:
                self.view.panelDocuments.documents.add_document(docData=document, expandItem=document.IMS2Dions)
            else:
                self.view.panelDocuments.documents.add_document(
                    docData=document, expandItem=document.IMS2Dions[expand_item_title]
                )
        elif expand_item == "combined_ions":
            if expand_item_title is None:
                self.view.panelDocuments.documents.add_document(docData=document, expandItem=document.IMS2DCombIons)
            else:
                self.view.panelDocuments.documents.add_document(
                    docData=document, expandItem=document.IMS2DCombIons[expand_item_title]
                )

        elif expand_item == "processed_ions":
            if expand_item_title is None:
                self.view.panelDocuments.documents.add_document(docData=document, expandItem=document.IMS2DionsProcess)
            else:
                self.view.panelDocuments.documents.add_document(
                    docData=document, expandItem=document.IMS2DionsProcess[expand_item_title]
                )

        elif expand_item == "ions_1D":
            if expand_item_title is None:
                self.view.panelDocuments.documents.add_document(docData=document, expandItem=document.multipleDT)
            else:
                self.view.panelDocuments.documents.add_document(
                    docData=document, expandItem=document.multipleDT[expand_item_title]
                )

        elif expand_item == "comparison_data":
            if expand_item_title is None:
                self.view.panelDocuments.documents.add_document(docData=document, expandItem=document.IMS2DcompData)
            else:
                self.view.panelDocuments.documents.add_document(
                    docData=document, expandItem=document.IMS2DcompData[expand_item_title]
                )

        elif expand_item == "mass_spectra":
            if expand_item_title is None:
                self.view.panelDocuments.documents.add_document(
                    docData=document, expandItem=document.multipleMassSpectrum
                )
            else:
                self.view.panelDocuments.documents.add_document(
                    docData=document, expandItem=document.multipleMassSpectrum[expand_item_title]
                )

        elif expand_item == "overlay":
            if expand_item_title is None:
                self.view.panelDocuments.documents.add_document(docData=document, expandItem=document.IMS2DoverlayData)
            else:
                self.view.panelDocuments.documents.add_document(
                    docData=document, expandItem=document.IMS2DoverlayData[expand_item_title]
                )
        # just set data
        elif expand_item == "no_refresh":
            self.view.panelDocuments.documents.set_document(
                document_old=self.documentsDict[document.title], document_new=document
            )

        # update dictionary
        self.documentsDict[document.title] = document
        self.currentDoc = document.title

    # TODO: move to data_handling module
    def onAddBlankDocument(self, evt, document_type=None):
        """
        Adds blank document of specific type
        """

        dlg = wx.FileDialog(
            self.view,
            "Please add name and select path for the document",
            "",
            "",
            "",
            wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        )
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
        document.userParameters["date"] = getTime()
        # Add method specific parameters
        if evtID == ID_addNewOverlayDoc or document_type == "overlay":
            document.dataType = "Type: Comparison"
            document.fileFormat = "Format: ORIGAMI"

        elif evtID == ID_addNewCalibrationDoc or document_type == "calibration":
            document.dataType = "Type: CALIBRANT"
            document.fileFormat = "Format: DataFrame"

        elif evtID == ID_addNewInteractiveDoc or document_type == "interactive":
            document.dataType = "Type: Interactive"
            document.fileFormat = "Format: ORIGAMI"

        elif evtID == ID_addNewManualDoc or document_type == "manual":
            document.dataType = "Type: MANUAL"
            document.fileFormat = "Format: MassLynx (.raw)"

        self.OnUpdateDocument(document, "document")

    def on_open_weblink(self, evt):
        """Open selected webpage."""

        if isinstance(evt, int):
            evtID = evt
        else:
            evtID = evt.GetId()

        # set link
        links = {
            ID_helpHomepage: "home",
            ID_helpGitHub: "github",
            ID_helpCite: "cite",
            ID_helpNewVersion: "newVersion",
            ID_helpYoutube: "youtube",
            ID_helpGuide: "guide",
            ID_helpHTMLEditor: "htmlEditor",
            ID_helpNewFeatures: "newFeatures",
            ID_helpReportBugs: "reportBugs",
        }

        link = self.config.links[links[evtID]]

        # open webpage
        try:
            self.onThreading(None, ("Opening a link in your default internet browser", 4), action="updateStatusbar")
            webbrowser.open(link, autoraise=1)
        except Exception:
            pass

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
#                         DialogBox(exceptionTitle='ORIGAMI',
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
#                 msgDialog = DialogNewVersion(self.view, self, webpage)
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


if __name__ == "__main__":
    app = ORIGAMI(redirect=False)
    app.start()
