import wx
import os
import threading
from pubsub import pub
import numpy as np
import wx.lib.agw.multidirdialog as MDD

import readers.io_text_files as io_text
import readers.io_waters_raw as io_waters
import processing.spectra as pr_spectra
from document import document as documents
from ids import ID_window_ionList, ID_window_multiFieldList, ID_load_origami_masslynx_raw, ID_load_masslynx_raw, \
    ID_openIRRawFile
from gui_elements.misc_dialogs import dlgBox
from utils.check import isempty
from utils.time import getTime, ttime
from utils.path import get_path_and_fname, check_waters_path
from utils.converters import byte2str
from utils.random import randomIntegerGenerator
from utils.color import convertRGB255to1, convertRGB1to255

import logging
from utils.ranges import get_min_max
logger = logging.getLogger("origami")


class data_handling():

    def __init__(self, presenter, view, config):
        self.presenter = presenter
        self.view = view
        self.config = config

        # processing links
        self.data_processing = self.view.data_processing

        # panel links
        self.documentTree = self.view.panelDocuments.documents

        self.plotsPanel = self.view.panelPlots

        self.ionPanel = self.view.panelMultipleIons
        self.ionList = self.ionPanel.peaklist

        self.textPanel = self.view.panelMultipleText
        self.textList = self.textPanel.peaklist

        self.filesPanel = self.view.panelMML
        self.filesList = self.filesPanel.peaklist

        # Setup listeners
        pub.subscribe(self.extract_from_plot_1D, 'extract_from_plot_1D')
        pub.subscribe(self.extract_from_plot_2D, 'extract_from_plot_2D')

    def on_threading(self, action, args):
        """
        Execute action using new thread
        args: list/dict
            function arguments
        action: str
            decides which action should be taken
        """

        if action == "statusbar.update":
            th = threading.Thread(target=self.view.updateStatusbar, args=args)
        elif action == "load.raw.masslynx":
            th = threading.Thread(target=self.on_open_single_MassLynx_raw, args=args)
        elif action == "load.text.heatmap":
            th = threading.Thread(target=self.on_open_single_text_2D, args=args)
        elif action == "load.multiple.text.heatmap":
            th = threading.Thread(target=self.on_open_multiple_text_2D, args=args)
        elif action == "load.text.spectrum":
            th = threading.Thread(target=self.__on_add_text_MS, args=args)
        elif action == "load.raw.masslynx.ms_only":
            th = threading.Thread(target=self.on_open_MassLynx_raw_MS_only, args=args)

        # Start thread
        try:
            th.start()
        except Exception as e:
            logger.warning('Failed to execute the operation in threaded mode. Consider switching it off?')
            logger.error(e)

    def _on_get_document(self, document_title=None):

        if document_title is None:
            self.presenter.currentDoc = self.documentTree.on_enable_document()
        else:
            self.presenter.currentDoc = byte2str(document_title)

        if self.presenter.currentDoc is None or \
                self.presenter.currentDoc == "Current documents":
            return None

        self.presenter.currentDoc = byte2str(self.presenter.currentDoc)
        document = self.presenter.documentsDict[self.presenter.currentDoc]

        return document

    def _on_get_path(self):
        dlg = wx.FileDialog(self.view,
                            "Please select name and path for the document...",
                            "", "", "", wx.FD_SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            path, fname = os.path.split(dlg.GetPath())

            return path, fname
        else:
            return None, None

    def __on_add_text_2D(self, filename, filepath):

        if filename is None:
            _, filename = get_path_and_fname(filepath, simple=True)

        # Split filename to get path
        path, filename = get_path_and_fname(filepath, simple=True)

        filepath = byte2str(filepath)
        if self.textPanel.onCheckDuplicates(filename):
            return

        # load heatmap information and split into individual components
        array_2D, xAxisLabels, yAxisLabels = io_text.text_heatmap_open(path=filepath)
        array_1D_mob = np.sum(array_2D, axis=1).T
        array_1D_RT = np.sum(array_2D, axis=0)

        # Try to extract labels from the text file
        if isempty(xAxisLabels) or isempty(yAxisLabels):
            xAxisLabels, yAxisLabels = "", ""
            xlabel_start, xlabel_end = "", ""

            msg = "Missing x/y-axis labels for {}!".format(filename) + \
                " Consider adding x/y-axis to your file to obtain full functionality."
            dlgBox(exceptionTitle='Missing data', exceptionMsg=msg, type="Warning")
        else:
            xlabel_start, xlabel_end = xAxisLabels[0], xAxisLabels[-1]

        add_dict = {
            'energy_start': xlabel_start,
            'energy_end': xlabel_end,
            'charge': "",
            "color": self.config.customColors[randomIntegerGenerator(0, 15)],
            "colormap": self.config.overlay_cmaps[randomIntegerGenerator(0, len(self.config.overlay_cmaps) - 1)],
            'alpha': self.config.overlay_defaultMask,
            'mask': self.config.overlay_defaultAlpha,
            'label': "",
            'shape': array_2D.shape,
            'document': filename}

        color = self.textPanel.on_add_to_table(add_dict, return_color=True)
        color = convertRGB255to1(color)

        # Add data to document
        document = documents()
        document.title = filename
        document.path = path
        document.userParameters = self.config.userParameters
        document.userParameters['date'] = getTime()
        document.dataType = 'Type: 2D IM-MS'
        document.fileFormat = 'Format: Text (.csv/.txt)'
        document.got2DIMS = True
        document.IMS2D = {'zvals': array_2D,
                          'xvals': xAxisLabels,
                          'xlabels': 'Collision Voltage (V)',
                          'yvals': yAxisLabels,
                          'yvals1D': array_1D_mob,
                          'yvalsRT': array_1D_RT,
                          'ylabels': 'Drift time (bins)',
                          'cmap': self.config.currentCmap,
                          'mask': self.config.overlay_defaultMask,
                          'alpha': self.config.overlay_defaultAlpha,
                          'min_threshold': 0,
                          'max_threshold': 1,
                          'color': color}

        # Update document
        self.view.updateRecentFiles(path={'file_type': 'Text', 'file_path': path})
        self.on_update_document(document, 'document')

    def __on_add_text_MS(self, path):
        # Update statusbar
        self.on_threading(args=("Loading {}...".format(path), 4), action='statusbar.update')
        __, document_title = get_path_and_fname(path, simple=True)

        ms_x, ms_y, dirname, xlimits, extension = self._get_text_spectrum_data(path)
        # Add data to document
        document = documents()
        document.title = document_title
        document.path = dirname
        document.userParameters = self.config.userParameters
        document.userParameters['date'] = getTime()
        document.dataType = 'Type: MS'
        document.fileFormat = 'Format: Text ({})'.format(extension)
        document.gotMS = True
        document.massSpectrum = {'xvals': ms_x,
                                 'yvals': ms_y,
                                 'xlabels': 'm/z (Da)',
                                 'xlimits': xlimits}

        # Plot
        name_kwargs = {"document": document.title, "dataset": "Mass Spectrum"}
        self.view.panelPlots.on_plot_MS(ms_x, ms_y, xlimits=xlimits, **name_kwargs)

        # Update document
        self.view.updateRecentFiles(path={'file_type': 'Text_MS', 'file_path': path})
        self.on_update_document(document, 'document')

    def _get_driftscope_spectrum_data(self, path):
        extract_kwargs = {'return_data': True}
        ms_x, ms_y = io_waters.rawMassLynx_MS_extract(
            path=path, driftscope_path=self.config.driftscopePath, **extract_kwargs)

        return ms_x, ms_y

    def _get_driftscope_chromatography_data(self, path):
        # RT
        extract_kwargs = {'return_data': True, 'normalize': True}
        xvals_RT, yvals_RT, yvals_RT_norm = io_waters.rawMassLynx_RT_extract(
            path=path, driftscope_path=self.config.driftscopePath, **extract_kwargs)

        return xvals_RT, yvals_RT, yvals_RT_norm

    def _get_driftscope_mobiligram_data(self, path):
        extract_kwargs = {'return_data': True}
        xvals_DT, yvals_DT = io_waters.rawMassLynx_DT_extract(
            path=path, driftscope_path=self.config.driftscopePath, **extract_kwargs)

        return xvals_DT, yvals_DT

    def _get_driftscope_mobility_data(self, path):
        extract_kwargs = {'return_data': True}
        zvals = io_waters.rawMassLynx_2DT_extract(
            path=path, driftscope_path=self.config.driftscopePath, **extract_kwargs)
        y_size, x_size = zvals.shape
        xvals = 1 + np.arange(x_size)
        yvals = 1 + np.arange(y_size)

        return xvals, yvals, zvals

    def _get_driftscope_mobility_vs_spectrum_data(self, path, mz_min, mz_max, mz_binsize=None):
        import math

        if mz_binsize is None:
            mz_binsize = self.config.ms_dtmsBinSize

        # m/z spacing, default is 1 Da
        n_points = int(math.floor((mz_max - mz_min) / mz_binsize))

        # Extract and load data
        extract_kwargs = {'return_data': True}
        zvals_MSDT = io_waters.rawMassLynx_MZDT_extract(
            path=path,
            driftscope_path=self.config.driftscopePath,
            mz_start=mz_min,
            mz_end=mz_max,
            mz_nPoints=n_points,
            **extract_kwargs)

        y_size, __ = zvals_MSDT.shape
        # Get x/y axis
        xvals_MSDT = np.linspace(
            mz_min - mz_binsize,
            mz_max + mz_binsize,
            n_points, endpoint=True)
        yvals_MSDT = 1 + np.arange(y_size)

        return xvals_MSDT, yvals_MSDT, zvals_MSDT

    def _get_masslynx_spectrum_data(self, path, mz_min, mz_max):
        kwargs = {'auto_range': self.config.ms_auto_range,
                  'mz_min': mz_min, 'mz_max': mz_max,
                  'linearization_mode': self.config.ms_linearization_mode}
        ms_dict = io_waters.rawMassLynx_MS_bin(
            filename=path,
            function=1,
            binData=self.config.import_binOnImport,
            mzStart=self.config.ms_mzStart,
            mzEnd=self.config.ms_mzEnd,
            binsize=self.config.ms_mzBinSize,
            **kwargs)

        # Sum MS data
        ms_x, ms_y = pr_spectra.sum_1D_dictionary(ydict=ms_dict)

        return ms_x, ms_y, ms_dict

    def on_update_document(self, document, expand_item='document', expand_item_title=None):

        if expand_item == 'document':
            self.documentTree.add_document(docData=document,

                                           expandItem=document)
        elif expand_item == 'ions':
            if expand_item_title is None:
                self.documentTree.add_document(docData=document,
                                               expandItem=document.IMS2Dions)
            else:
                self.documentTree.add_document(docData=document,
                                               expandItem=document.IMS2Dions[expand_item_title])
        elif expand_item == 'combined_ions':
            if expand_item_title is None:
                self.documentTree.add_document(docData=document,
                                               expandItem=document.IMS2DCombIons)
            else:
                self.documentTree.add_document(docData=document,
                                               expandItem=document.IMS2DCombIons[expand_item_title])

        elif expand_item == 'processed_ions':
            if expand_item_title is None:
                self.documentTree.add_document(docData=document,
                                               expandItem=document.IMS2DionsProcess)
            else:
                self.documentTree.add_document(docData=document,
                                               expandItem=document.IMS2DionsProcess[expand_item_title])

        elif expand_item == 'ions_1D':
            if expand_item_title is None:
                self.documentTree.add_document(docData=document,
                                               expandItem=document.multipleDT)
            else:
                self.documentTree.add_document(docData=document,
                                               expandItem=document.multipleDT[expand_item_title])

        elif expand_item == 'comparison_data':
            if expand_item_title is None:
                self.documentTree.add_document(docData=document,
                                               expandItem=document.IMS2DcompData)
            else:
                self.documentTree.add_document(docData=document,
                                               expandItem=document.IMS2DcompData[expand_item_title])

        elif expand_item == 'mass_spectra':
            if expand_item_title is None:
                self.documentTree.add_document(docData=document,
                                               expandItem=document.multipleMassSpectrum)
            else:
                self.documentTree.add_document(docData=document,
                                               expandItem=document.multipleMassSpectrum[expand_item_title])

        elif expand_item == 'overlay':
            if expand_item_title is None:
                self.documentTree.add_document(docData=document,
                                               expandItem=document.IMS2DoverlayData)
            else:
                self.documentTree.add_document(docData=document,
                                               expandItem=document.IMS2DoverlayData[expand_item_title])
        # just set data
        elif expand_item == 'no_refresh':
            self.documentTree.set_document(document_old=self.documentsDict[document.title],
                                           document_new=document)

        # update dictionary
        self.presenter.documentsDict[document.title] = document
        self.presenter.currentDoc = document.title

    def extract_from_plot_1D(self, xvalsMin, xvalsMax, yvalsMax, currentView=None, currentDoc=""):
        self.currentPage = self.plotsPanel._get_page_text()
        self.SetStatusText("", number=4)

        document = self._on_get_document()
        document_title = document.title

        if self.currentPage in ['RT', 'MS', '1D', '2D'] and document.dataType == 'Type: Interactive':
            args = ("Cannot extract data from Interactive document", 4)
            self.on_threading(args=args, action='statusbar.update')
            return

        # Extract mass spectrum from mobiligram window
        elif self.currentPage == '1D':
            dt_label = self.plotsPanel.plot1D.plot_labels.get("xlabel", "Drift time (bins)")

            if xvalsMin is None or xvalsMax is None:
                args = ('Your extraction range was outside the window. Please try again', 4)
                self.on_threading(args=args, action='statusbar.update')
                return

            if dt_label == "Drift time (bins)":
                dtStart = np.ceil(xvalsMin).astype(int)
                dtEnd = np.floor(xvalsMax).astype(int)
            else:
                dtStart = xvalsMin
                dtEnd = xvalsMax

            # Check that values are in correct order
            if dtEnd < dtStart:
                dtEnd, dtStart = dtStart, dtEnd

            self.presenter.on_extract_MS_from_mobiligram(dtStart=dtStart, dtEnd=dtEnd, units=dt_label)

        # Extract heatmap from mass spectrum window
        elif self.currentPage == "MS" or currentView == "MS":
            if xvalsMin is None or xvalsMax is None:
                self.SetStatusText('Your extraction range was outside the window. Please try again', 3)
                return

            if document.fileFormat == "Format: Thermo (.RAW)":
                return

            mzStart = np.round(xvalsMin, 2)
            mzEnd = np.round(xvalsMax, 2)

            mzYMax = np.round(yvalsMax * 100, 1)
            # Check that values are in correct order
            if mzEnd < mzStart:
                mzEnd, mzStart = mzStart, mzEnd

            # Make sure the document has MS in first place (i.e. Text)
            if not self.presenter.documentsDict[currentDoc].gotMS:
                return

            # Get MS data for specified region and extract Y-axis maximum
            ms = self.presenter.documentsDict[currentDoc].massSpectrum
            ms = np.transpose([ms['xvals'], ms['yvals']])
            mzYMax = self.getYvalue(msList=ms, mzStart=mzStart, mzEnd=mzEnd)

            # predict charge state
            charge = self.data_processing.predict_charge_state(ms[:, 0], ms[:, 1], (mzStart, mzEnd))
            color = self.ionPanel.on_check_duplicate_colors(
                self.config.customColors[randomIntegerGenerator(0, 15)])
            color = convertRGB255to1(color)

            if (document.dataType == 'Type: ORIGAMI' or
                document.dataType == 'Type: MANUAL' or
                    document.dataType == 'Type: Infrared'):
                self.view.onPaneOnOff(evt=ID_window_ionList, check=True)
                # Check if value already present
                outcome = self.ionPanel.onCheckForDuplicates(mzStart=str(mzStart),
                                                             mzEnd=str(mzEnd))
                if outcome:
                    self.SetStatusText('Selected range already in the table', 3)
                    if currentView == "MS":
                        return outcome
                    return

                _add_to_table = {"mz_start": mzStart,
                                 "mz_end": mzEnd,
                                 "charge": charge,
                                 "mz_ymax": mzYMax,
                                 "color": convertRGB1to255(color),
                                 "colormap": self.config.overlay_cmaps[randomIntegerGenerator(0,
                                                                                              len(self.config.overlay_cmaps) - 1)],
                                 "alpha": self.config.overlay_defaultAlpha,
                                 "mask": self.config.overlay_defaultMask,
                                 "document": currentDoc}
                self.ionPanel.on_add_to_table(_add_to_table, check_color=False)

                if self.config.showRectanges:
                    self.plotsPanel.on_plot_patches(mzStart, 0, (mzEnd - mzStart), 100000000000,
                                                    color=color, alpha=self.config.markerTransparency_1D,
                                                    repaint=True)

                if self.ionPanel.extractAutomatically:
                    self.presenter.on_extract_2D_from_mass_range_threaded(None, extract_type="new")

            elif document.dataType == 'Type: Multifield Linear DT':
                self.view.onPaneOnOff(evt=ID_window_multiFieldList, check=True)
                # Check if value already present
                outcome = self.view.panelLinearDT.bottomP.onCheckForDuplicates(mzStart=str(mzStart),
                                                                               mzEnd=str(mzEnd))
                if outcome:
                    return
                self.view.panelLinearDT.bottomP.peaklist.Append([mzStart, mzEnd,
                                                                 mzYMax, "",
                                                                 self.presenter.currentDoc])

                if self.config.showRectanges:
                    self.plotsPanel.on_plot_patches(mzStart, 0, (mzEnd - mzStart), 100000000000,
                                                    color=self.config.annotColor,
                                                    alpha=self.config.markerTransparency_1D,
                                                    repaint=True)

        # Extract data from calibration window
        if self.currentPage == "Calibration":
            # Check whether the current document is of correct type!
            if (document.fileFormat != 'Format: MassLynx (.raw)' or document.dataType != 'Type: CALIBRANT'):
                print('Please select the correct document file in document window!')
                return
            mzVal = np.round((xvalsMax + xvalsMin) / 2, 2)
            # prevents extraction if value is below 50. This assumes (wrongly!)
            # that the m/z range will never be below 50.
            if xvalsMax < 50:
                self.SetStatusText('Make sure you are extracting in the MS window.', 3)
                return
            # Check if value already present
            outcome = self.panelCCS.topP.onCheckForDuplicates(mzCentre=str(mzVal))
            if outcome:
                return
            self.view._mgr.GetPane(self.panelCCS).Show()
            self.ccsTable.Check(True)
            self.view._mgr.Update()
            if yvalsMax <= 1:
                tD = self.presenter.onAddCalibrant(path=document.path,
                                                   mzCentre=mzVal,
                                                   mzStart=np.round(xvalsMin, 2),
                                                   mzEnd=np.round(xvalsMax, 2),
                                                   pusherFreq=document.parameters['pusherFreq'],
                                                   tDout=True)

                self.panelCCS.topP.peaklist.Append([document_title,
                                                    np.round(xvalsMin, 2),
                                                    np.round(xvalsMax, 2),
                                                    "", "", "", str(tD)])
                if self.config.showRectanges:
                    self.presenter.addRectMS(xvalsMin, 0, (xvalsMax - xvalsMin), 1.0,
                                             color=self.config.annotColor,
                                             alpha=(self.config.annotTransparency / 100),
                                             repaint=True, plot='CalibrationMS')

        # Extract mass spectrum from chromatogram window - Linear DT files
        elif self.currentPage == "RT" and document.dataType == 'Type: Multifield Linear DT':
            self.view._mgr.GetPane(self.view.panelLinearDT).Show()
#             self.multifieldTable.Check(True)
            self.view._mgr.Update()
            xvalsMin = np.ceil(xvalsMin).astype(int)
            xvalsMax = np.floor(xvalsMax).astype(int)
            # Check that values are in correct order
            if xvalsMax < xvalsMin:
                xvalsMax, xvalsMin = xvalsMin, xvalsMax

            # Check if value already present
            outcome = self.view.panelLinearDT.topP.onCheckForDuplicates(rtStart=str(xvalsMin),
                                                                        rtEnd=str(xvalsMax))
            if outcome:
                return
            xvalDiff = xvalsMax - xvalsMin.astype(int)
            self.view.panelLinearDT.topP.peaklist.Append([xvalsMin, xvalsMax,
                                                          xvalDiff, "",
                                                          self.presenter.currentDoc])

            self.plotsPanel.on_add_patch(xvalsMin, 0, (xvalsMax - xvalsMin), 100000000000,
                                         color=self.config.annotColor,
                                         alpha=(self.config.annotTransparency / 100),
                                         repaint=True, plot="RT")

        # Extract mass spectrum from chromatogram window
        elif self.currentPage == 'RT' and document.dataType != 'Type: Multifield Linear DT':
            rt_label = self.plotsPanel.plotRT.plot_labels.get("xlabel", "Scans")

            # Get values
            if xvalsMin is None or xvalsMax is None:
                self.SetStatusText("Extraction range was from outside of the plot area. Try again",
                                   number=4)
                return
            if rt_label == "Scans":
                xvalsMin = np.ceil(xvalsMin).astype(int)
                xvalsMax = np.floor(xvalsMax).astype(int)

            # Check that values are in correct order
            if xvalsMax < xvalsMin:
                xvalsMax, xvalsMin = xvalsMin, xvalsMax

            # Check if difference between the two values is large enough
            if (xvalsMax - xvalsMin) < 1 and rt_label == "Scans":
                self.SetStatusText('The scan range you selected was too small. Please choose wider range', 3)
                return
            # Extract data
            if document.fileFormat == "Format: Thermo (.RAW)":
                return
            else:
                self.presenter.on_extract_MS_from_chromatogram(startScan=xvalsMin, endScan=xvalsMax, units=rt_label)

        else:
            return

    def extract_from_plot_2D(self, dataOut):
        self.currentPage = self.plotsPanel._get_page_text()

        if self.currentPage == "DT/MS":
            xlabel = self.plotsPanel.plotMZDT.plot_labels.get("xlabel", "m/z")
            ylabel = self.plotsPanel.plotMZDT.plot_labels.get("ylabel", "Drift time (bins)")
        elif self.currentPage == "2D":
            xlabel = self.plotsPanel.plot2D.plot_labels.get("xlabel", "Scans")
            ylabel = self.plotsPanel.plot2D.plot_labels.get("ylabel", "Drift time (bins)")

        xmin, xmax, ymin, ymax = dataOut
        if xmin is None or xmax is None or ymin is None or ymax is None:
            self.SetStatusText("Extraction range was from outside of the plot area. Try again", number=4)
            return

        xmin = np.round(xmin, 2)
        xmax = np.round(xmax, 2)

        if ylabel == "Drift time (bins)":
            ymin = int(np.round(ymin, 0))
            ymax = int(np.round(ymax, 0))
        elif ylabel in ["Drift time (ms)", "Arrival time (ms)"]:
            ymin, ymax = ymin, ymax
        else:
            return

        if xlabel == "Scans":
            xmin = np.ceil(xmin).astype(int)
            xmax = np.floor(xmax).astype(int)
        elif xlabel in ['Retention time (min)', 'Time (min)', 'm/z']:
            xmin, xmax = xmin, xmax
        else:
            return

        # Reverse values if they are in the wrong order
        if xmax < xmin:
            xmax, xmin = xmin, xmax
        if ymax < ymin:
            ymax, ymin = ymin, ymax

        # Extract data
        if self.currentPage == "DT/MS":
            self.presenter.on_extract_RT_from_mzdt(xmin, xmax, ymin, ymax,
                                                   units_x=xlabel, units_y=ylabel)
        elif self.currentPage == "2D":
            self.presenter.on_extract_MS_from_heatmap(xmin, xmax, ymin, ymax,
                                                      units_x=xlabel, units_y=ylabel)
        self.SetStatusText("", number=4)

    def on_open_text_2D_fcn(self, evt):
        if not self.config.threading:
            self.on_open_single_text_2D()
        else:
            self.on_threading(action="load.text.heatmap", args=())

    def on_open_single_text_2D(self):
        dlg = wx.FileDialog(self.view, "Choose a text file:", wildcard="*.txt; *.csv",
                            style=wx.FD_DEFAULT_STYLE | wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            filepath = dlg.GetPath()
            __, filename = get_path_and_fname(filepath, simple=True)
            self.__on_add_text_2D(filename, filepath)
        dlg.Destroy()

    def on_open_multiple_text_2D_fcn(self, evt):
        self.view.onPaneOnOff(evt="text", check=True)

        wildcard = "Text files with axis labels (*.txt, *.csv)| *.txt;*.csv"
        dlg = wx.FileDialog(self.view, "Choose a text file. Make sure files contain x- and y-axis labels!",
                            wildcard=wildcard, style=wx.FD_MULTIPLE | wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            pathlist = dlg.GetPaths()
            filenames = dlg.GetFilenames()

            if not self.config.threading:
                self.on_open_multiple_text_2D(pathlist, filenames)
            else:
                self.on_threading(action='load.multiple.text.heatmap', args=(pathlist, filenames),)
        dlg.Destroy()

    def on_open_multiple_text_2D(self, pathlist, filenames):
        for filepath, filename in zip(pathlist, filenames):
            self.__on_add_text_2D(filename, filepath)

    def on_open_multiple_MassLynx_raw_fcn(self, evt):

        dlg = MDD.MultiDirDialog(self.view,
                                 title="Choose Waters (.raw) files to open...",
                                 agwStyle=MDD.DD_MULTIPLE | MDD.DD_DIR_MUST_EXIST)

        if dlg.ShowModal() == wx.ID_OK:
            pathlist = dlg.GetPaths()
            data_type = 'Type: ORIGAMI'
            for path in pathlist:
                if not check_waters_path(path):
                    msg = "The path ({}) you've selected does not end with .raw"
                    dlgBox(exceptionTitle='Please load MassLynx (.raw) file',
                           exceptionMsg=msg,
                           type="Error")
                    return

                if not self.config.threading:
                    self.on_open_single_MassLynx_raw(path, data_type)
                else:
                    self.on_threading(action='load.raw.masslynx', args=(path, data_type),)

    def on_open_MassLynx_raw_fcn(self, evt):

        # Reset arrays
        dlg = wx.DirDialog(self.view, "Choose a MassLynx (.raw) file",
                           style=wx.DD_DEFAULT_STYLE)

        if evt == ID_load_origami_masslynx_raw:
            data_type = 'Type: ORIGAMI'
        elif evt == ID_load_masslynx_raw:
            data_type = 'Type: MassLynx'
        elif evt == ID_openIRRawFile:
            data_type = 'Type: Infrared'
        else:
            data_type = 'Type: ORIGAMI'

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            if not check_waters_path(path):
                msg = "The path ({}) you've selected does not end with .raw"
                dlgBox(exceptionTitle='Please load MassLynx (.raw) file',
                       exceptionMsg=msg,
                       type="Error")
                return

            if not self.config.threading:
                self.on_open_single_MassLynx_raw(path, data_type)
            else:
                self.on_threading(action='load.raw.masslynx', args=(path, data_type),)

        dlg.Destroy()

    def on_open_single_MassLynx_raw(self, path, data_type):
        """ Load data = threaded """
        tstart = ttime()
        self.on_threading(args=("Loading {}...".format(path), 4), action='statusbar.update')
        __, document_title = get_path_and_fname(path, simple=True)

        # Get experimental parameters
        parameters = self.config.importMassLynxInfFile(path=path)
        fileInfo = self.config.importMassLynxHeaderFile(path=path)
        xlimits = [parameters['startMS'], parameters['endMS']]

        try:
            ms_x, ms_y = self._get_driftscope_spectrum_data(path)
            self.on_threading(args=("Extracted mass spectrum", 4), action='statusbar.update')
        except IOError:
            # Failed to open document because it does not have IM-MS data
            data_type = 'Type: MS'
            # Extract MS data
            ms_x, ms_y, ms_dict = self._get_masslynx_spectrum_data(path, xlimits[0], xlimits[1])
            # Sum MS to get RT data
            yvals_RT, yvals_RT_norm = pr_spectra.sum_spectrum_to_chromatogram(ydict=ms_dict)
            xvals_RT = np.arange(1, len(yvals_RT) + 1)

        if data_type != 'Type: MS':
            # RT
            xvals_RT, __, yvals_RT_norm = self._geget_driftscopehromatography_data(path)
            self.on_threading(args=("Extracted chromatogram", 4), action='statusbar.update')

            # DT
            xvals_DT, yvals_DT = self._get_driftscope_mobiligram_data(path)
            self.on_threading(args=("Extracted mobiligram", 4), action='statusbar.update')

            # 2D
            xvals, yvals, zvals = self._get_driftscope_mobility_data(path)
            self.on_threading(args=("Extracted heatmap", 4), action='statusbar.update')

            # Plot MZ vs DT
            if self.config.showMZDT:
                xvals_MSDT, yvals_MSDT, zvals_MSDT = self._get_driftscope_mobility_vs_spectrum_data(
                    path, parameters["startMS"], parameters["endMS"])
                # Plot
                self.plotsPanel.on_plot_MSDT(
                    zvals_MSDT, xvals_MSDT, yvals_MSDT, 'm/z', 'Drift time (bins)')

        # Update status bar with MS range
            self.view.SetStatusText("{}-{}".format(parameters['startMS'], parameters['endMS']), 1)
            self.view.SetStatusText("MSMS: {}".format(parameters['setMS']), 2)

        # Add info to document and data to file
        document = documents()
        document.title = document_title
        document.path = path
        document.dataType = data_type
        document.fileFormat = 'Format: Waters (.raw)'
        document.fileInformation = fileInfo
        document.parameters = parameters
        document.userParameters = self.config.userParameters
        document.userParameters['date'] = getTime()

        # add mass spectrum data
        document.gotMS = True
        document.massSpectrum = {'xvals': ms_x,
                                 'yvals': ms_y,
                                 'xlabels': 'm/z (Da)',
                                 'xlimits': xlimits}
        name_kwargs = {"document": document_title, "dataset": "Mass Spectrum"}
        self.plotsPanel.on_plot_MS(ms_x, ms_y, xlimits=xlimits, **name_kwargs)

        # add chromatogram data
        document.got1RT = True
        document.RT = {'xvals': xvals_RT,
                       'yvals': yvals_RT_norm,
                       'xlabels': 'Scans'}
        self.plotsPanel.on_plot_RT(xvals_RT, yvals_RT_norm, 'Scans')

        if data_type != 'Type: MS':
            # add mobiligram data
            document.got1DT = True
            document.DT = {'xvals': xvals_DT,
                           'yvals': yvals_DT,
                           'xlabels': 'Drift time (bins)',
                           'ylabels': 'Intensity'}
            self.plotsPanel.on_plot_1D(xvals_DT, yvals_DT, 'Drift time (bins)')

            # add 2D mobiligram data
            document.got2DIMS = True
            document.IMS2D = {'zvals': zvals,
                              'xvals': xvals,
                              'xlabels': 'Scans',
                              'yvals': yvals,
                              'yvals1D': yvals_DT,
                              'ylabels': 'Drift time (bins)',
                              'cmap': self.config.currentCmap,
                              'charge': 1}
            self.plotsPanel.on_plot_2D_data(data=[zvals, xvals, 'Scans', yvals, 'Drift time (bins)'])

            # add DT/MS data
            if self.config.showMZDT:
                document.gotDTMZ = True
                document.DTMZ = {'zvals': zvals_MSDT,
                                 'xvals': xvals_MSDT,
                                 'yvals': yvals_MSDT,
                                 'xlabels': 'm/z',
                                 'ylabels': 'Drift time (bins)',
                                 'cmap': self.config.currentCmap}

        if data_type == 'Type: ORIGAMI':
            self.view.updateRecentFiles(path={'file_type': 'ORIGAMI', 'file_path': path})
        elif data_type == 'Type: MassLynx':
            self.view.updateRecentFiles(path={'file_type': 'MassLynx', 'file_path': path})
        elif data_type == 'Type: Infrared':
            self.view.updateRecentFiles(path={'file_type': 'Infrared', 'file_path': path})
        else:
            self.view.updateRecentFiles(path={'file_type': 'MassLynx', 'file_path': path})

        # Update document
        self.on_update_document(document, 'document')
        self.on_threading(args=("Opened file in {:.4f} seconds".format(ttime() - tstart), 4),
                          action='statusbar.update')

    def _get_text_spectrum_data(self, path):
        # Extract MS file
        xvals, yvals, dirname, extension = io_text.text_spectrum_open(path=path)
        xlimits = get_min_max(xvals)

        return xvals, yvals, dirname, xlimits, extension

    def on_open_single_text_MS_fcn(self, evt):
        wildcard = "Text file (*.txt, *.csv, *.tab)| *.txt;*.csv;*.tab"
        dlg = wx.FileDialog(self.view, "Choose MS text file...",
                            wildcard=wildcard,
                            style=wx.FD_DEFAULT_STYLE | wx.FD_CHANGE_DIR | wx.FD_MULTIPLE)
        if dlg.ShowModal() == wx.ID_OK:
            pathlist = dlg.GetPaths()
            for path in pathlist:
                if not self.config.threading:
                    self.__on_add_text_MS(path)
                else:
                    self.on_threading(action="load.text.spectrum", args=(path,))

        dlg.Destroy()

    def on_open_single_clipboard_MS(self, evt):
        """
        Get spectrum (n x 2) from clipboard
        """
        try:
            wx.TheClipboard.Open()
            textObj = wx.TextDataObject()
            wx.TheClipboard.GetData(textObj)
            wx.TheClipboard.Close()
            text = textObj.GetText()
            text = text.splitlines()
            data = []
            for t in text:
                line = t.split()
                if len(line) == 2:
                    try:
                        mz = float(line[0])
                        intensity = float(line[1])
                        data.append([mz, intensity])
                    except (ValueError, TypeError):
                        logger.warning("Failed to convert mass range to dtype: float")
            data = np.array(data)
            ms_x = data[:, 0]
            ms_y = data[:, 1]
            xlimits = get_min_max(ms_x)

            # Add data to document
            dlg = wx.FileDialog(self.view, "Please select name and directory for the MS document...",
                                "", "", "", wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
            dlg.CentreOnParent()
            if dlg.ShowModal() == wx.ID_OK:
                path = dlg.GetPath()
                dirname, fname = get_path_and_fname(path, simple=True)

                document = documents()
                document.title = fname
                document.path = dirname
                document.userParameters = self.config.userParameters
                document.userParameters['date'] = getTime()
                document.dataType = 'Type: MS'
                document.fileFormat = 'Format: Text ({})'.format("Clipboard")
                document.gotMS = True
                document.massSpectrum = {'xvals': ms_x,
                                         'yvals': ms_y,
                                         'xlabels': 'm/z (Da)',
                                         'xlimits': xlimits}

                # Plot
                name_kwargs = {"document": document.title, "dataset": "Mass Spectrum"}
                self.view.panelPlots.on_plot_MS(ms_x, ms_y, xlimits=xlimits, **name_kwargs)

                # Update document
                self.on_update_document(document, 'document')
        except Exception:
            logger.warning("Failed to get spectrum from the clipboard")
            return

    def on_open_MassLynx_raw_MS_only_fcn(self, evt):

        dlg = wx.DirDialog(self.view, "Choose a MassLynx file:",
                           style=wx.DD_DEFAULT_STYLE)

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()

            if not check_waters_path(path):
                msg = "The path ({}) you've selected does not end with .raw"
                dlgBox(exceptionTitle='Please load MassLynx (.raw) file',
                       exceptionMsg=msg,
                       type="Error")
                return

            if not self.config.threading:
                self.on_open_MassLynx_raw_MS_only(path)
            else:
                self.on_threading(action="load.raw.masslynx.ms_only", args=(path,))

        dlg.Destroy()

    # TODO: This function is currently broken: OSError: [WinError -529697949] Windows Error 0xe06d7363
    def on_open_MassLynx_raw_MS_only(self, path):
        """ open MS file (without IMS) """

        # Update statusbar
        self.on_threading(args=("Loading {}...".format(path), 4), action='statusbar.update')
        __, document_title = get_path_and_fname(path, simple=True)

        # Get experimental parameters
        parameters = self.config.importMassLynxInfFile(path=path)
        xlimits = [parameters['startMS'], parameters['endMS']]
        ms_x, ms_y, ms_dict = self._get_masslynx_spectrum_data(path, xlimits[0], xlimits[1])

        # Sum MS to get RT data
        rtX, rtY = pr_spectra.sum_spectrum_to_chromatogram(ydict=ms_dict)

        # Add data to document

        document = documents()
        document.title = document_title
        document.path = path
        document.parameters = parameters
        document.userParameters = self.config.userParameters
        document.userParameters['date'] = getTime()
        document.dataType = 'Type: MS'
        document.fileFormat = 'Format: Waters (.raw)'
        document.gotMS = True
        document.massSpectrum = {'xvals': ms_x,
                                 'yvals': ms_y,
                                 'xlabels': 'm/z (Da)',
                                 'xlimits': xlimits}
        document.got1RT = True
        document.RT = {'xvals': rtX,
                       'yvals': rtY,
                       'xlabels': 'Scans'}

        # Plot
        name_kwargs = {"document": document.title, "dataset": "Mass Spectrum"}
        self.view.panelPlots.on_plot_MS(ms_x, ms_y, xlimits=xlimits, **name_kwargs)
        self.view.panelPlots.on_plot_RT(rtX, rtY, 'Scans')

        # Update document
        self.view.updateRecentFiles(path={'file_type': 'MassLynx', 'file_path': path})
        self.on_update_document(document, 'document')
