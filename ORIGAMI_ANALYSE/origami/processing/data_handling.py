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
    ID_openIRRawFile, ID_window_multipleMLList
from gui_elements.misc_dialogs import dlgBox
from utils.check import isempty, check_value_order
from utils.time import getTime, ttime, tsleep
from utils.path import get_path_and_fname, check_waters_path, check_path_exists, clean_up_MDD_path
from utils.converters import byte2str
from utils.random import randomIntegerGenerator
from utils.color import convertRGB255to1, convertRGB1to255, randomColorGenerator
from utils.ranges import get_min_max
from processing.utils import get_maximum_value_in_range
import processing.origami_ms as pr_origami
import logging
from gui_elements.dialog_selectDocument import panelSelectDocument
logger = logging.getLogger("origami")

# TODO: on_open_MassLynx_raw_MS_only: This function is currently broken: OSError: [WinError -529697949] Windows Error 0xe06d7363


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

        # add application defaults
        self.plot_page = None

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
        elif action == "extract.heatmap":
            th = threading.Thread(target=self.on_extract_2D_from_mass_range, args=args)
        elif action == "load.multiple.raw.masslynx":
            th = threading.Thread(target=self.on_open_multiple_ML_files, args=args)

        # Start thread
        try:
            th.start()
        except Exception as e:
            logger.warning('Failed to execute the operation in threaded mode. Consider switching it off?')
            logger.error(e)

    def __update_statusbar(self, msg, field):
        self.on_threading(args=(msg, field), action='statusbar.update')

    def _on_get_document(self, document_title=None):

        if document_title is None:
            document_title = self.documentTree.on_enable_document()
        else:
            document_title = byte2str(document_title)

        if document_title is None or document_title == "Current documents":
            return None

        document_title = byte2str(document_title)
        document = self.presenter.documentsDict[document_title]

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

    def _get_driftscope_spectrum_data(self, path, **kwargs):
        kwargs.update({'return_data': True})
        ms_x, ms_y = io_waters.driftscope_extract_MS(
            path=path, driftscope_path=self.config.driftscopePath, **kwargs)

        return ms_x, ms_y

    def _get_driftscope_chromatography_data(self, path, **kwargs):
        kwargs.update({'return_data': True, 'normalize': True})
        xvals_RT, yvals_RT, yvals_RT_norm = io_waters.driftscope_extract_RT(
            path=path, driftscope_path=self.config.driftscopePath, **kwargs)

        return xvals_RT, yvals_RT, yvals_RT_norm

    def _get_driftscope_mobiligram_data(self, path, **kwargs):
        kwargs.update({'return_data': True})
        xvals_DT, yvals_DT = io_waters.driftscope_extract_DT(
            path=path, driftscope_path=self.config.driftscopePath, **kwargs)

        return xvals_DT, yvals_DT

    def _get_driftscope_mobility_data(self, path, **kwargs):
        kwargs.update({'return_data': True})
        zvals = io_waters.driftscope_extract_2D(
            path=path, driftscope_path=self.config.driftscopePath, **kwargs)
        y_size, x_size = zvals.shape
        xvals = 1 + np.arange(x_size)
        yvals = 1 + np.arange(y_size)

        return xvals, yvals, zvals

    def _get_driftscope_mobility_vs_spectrum_data(self, path, mz_min, mz_max, mz_binsize=None, **kwargs):
        import math

        if mz_binsize is None:
            mz_binsize = self.config.ms_dtmsBinSize

        # m/z spacing, default is 1 Da
        n_points = int(math.floor((mz_max - mz_min) / mz_binsize))

        # Extract and load data
        kwargs.update({'return_data': True})
        zvals_MSDT = io_waters.driftscope_extract_MZDT(
            path=path,
            driftscope_path=self.config.driftscopePath,
            mz_start=mz_min,
            mz_end=mz_max,
            mz_nPoints=n_points,
            **kwargs)

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

    def _get_text_spectrum_data(self, path):
        # Extract MS file
        xvals, yvals, dirname, extension = io_text.text_spectrum_open(path=path)
        xlimits = get_min_max(xvals)

        return xvals, yvals, dirname, xlimits, extension

    def __get_document_list_of_type(self, document_type, document_format=None):
        """
        This helper function checkes whether any of the documents in the
        document tree/ dictionary are of specified type
        """
        document_list = []
        for document_title in self.presenter.documentsDict:
            if self.presenter.documentsDict[document_title].dataType == document_type and document_format is None:
                document_list.append(document_title)
            elif (self.presenter.documentsDict[document_title].dataType == document_type and
                  self.presenter.documentsDict[document_title].fileFormat == document_format):
                document_list.append(document_title)

        return document_list

    def _get_document_of_type(self, document_type):
        document_list = self.__get_document_list_of_type(document_type=document_type)

        if len(document_list) == 0:
            self.__update_statusbar("Did not find appropriate document. Creating a new one...", 4)
            document = self.__create_new_document()
        else:
            dlg = panelSelectDocument(self.view, self, document_list)
            if dlg.ShowModal() == wx.ID_OK:
                return

            document_title = dlg.current_document
            if document_title is None:
                self.__update_statusbar("Please select document", 4)
                return

            document = self._on_get_document(document_title)
            self.__update_statusbar("Will be using {} document".format(document_title), 4)

        return document

    def __create_new_document(self):
        dlg = wx.FileDialog(self.view, "Please select a name for the document",
                            "", "", "", wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            path, document_title = os.path.split(dlg.GetPath())
            document_title = byte2str(document_title)
        else:
            return

        # Create document
        document = documents()
        document.title = document_title
        document.path = path
        document.userParameters = self.config.userParameters
        document.userParameters['date'] = getTime()

        return document

    def __on_add_ion_ORIGAMI(self, item_information, document, path, mz_start, mz_end, mz_y_max, ion_name, label, charge):
        kwargs = dict(mz_start=mz_start, mz_end=mz_end)
        # 1D
        try:
            __, yvals_DT = self._get_driftscope_mobiligram_data(path, **kwargs)
        except IOError:
            msg = "Failed to open the file - most likely because this file no longer exists" + \
                  " or has been moved. You can change the document path by right-clicking\n" + \
                  " on the document in the Document Tree and \n" + \
                  " selecting Notes, Information, Labels..."
            dlgBox(exceptionTitle='Missing folder', exceptionMsg=msg, type="Error")
            return
        # RT
        __, yvals_RT, __ = self._get_driftscope_chromatography_data(path, **kwargs)

        # 2D
        xvals, yvals, zvals = self._get_driftscope_mobility_data(path, **kwargs)

        # Add data to document object
#         document.gotExtractedIons = True
#         document.IMS2Dions[ion_name]
        ion_data = {'zvals': zvals,
                    'xvals': xvals,
                    'xlabels': 'Scans',
                    'yvals': yvals,
                    'ylabels': 'Drift time (bins)',
                    'cmap': item_information.get('colormap', self.config.currentCmap),
                    'yvals1D': yvals_DT,
                    'yvalsRT': yvals_RT,
                    'title': label,
                    'label': label,
                    'charge': charge,
                    'alpha': item_information['alpha'],
                    'mask': item_information['mask'],
                    'color': item_information['color'],
                    'min_threshold': item_information['min_threshold'],
                    'max_threshold': item_information['max_threshold'],
                    'xylimits': [mz_start, mz_end, mz_y_max]}

        self.documentTree.on_update_data(ion_data, ion_name, document, data_type="ion.heatmap.raw")

    def __on_add_ion_MANUAL(self, item_information, document, mz_start, mz_end, mz_y_max, ion_name, ion_id, charge, label):

        self.filesList.on_sort(2, True)
        tempDict = {}
        for item in range(self.filesList.GetItemCount()):
            # Determine whether the title of the document matches the title of the item in the table
            # if it does not, skip the row
            docValue = self.filesList.GetItem(item, self.config.multipleMLColNames['document']).GetText()
            if docValue != document.title:
                continue

            nameValue = self.filesList.GetItem(item, self.config.multipleMLColNames['filename']).GetText()
            try:
                path = document.multipleMassSpectrum[nameValue]['path']
                dt_x, dt_y = self._get_driftscope_mobiligram_data(path, mz_start=mz_start, mz_end=mz_end)
            # if the files were moved, we can at least try to with the document path
            except IOError:
                try:
                    path = os.path.join(document.path, nameValue)
                    dt_x, dt_y = self._get_driftscope_mobiligram_data(path, mz_start=mz_start, mz_end=mz_end)
                    document.multipleMassSpectrum[nameValue]['path'] = path
                except Exception:
                    msg = "It would appear ORIGAMI cannot find the file on your disk. You can try to fix this issue\n" + \
                          "by updating the document path by right-clicking on the document and selecting\n" + \
                          "'Notes, Information, Labels...' and updating the path to where the dataset is found.\n" + \
                          "After that, try again and ORIGAMI will try to stitch the new document path with the file name.\n"
                    dlgBox(exceptionTitle='Error',
                           exceptionMsg=msg,
                           type="Error")
                    return

            # Get height of the peak
            self.ionPanel.on_update_value_in_peaklist(ion_id, "method", "Manual")

            # Create temporary dictionary for all IMS data
            tempDict[nameValue] = [dt_y]
            # Add 1D data to 1D data container
            newName = "{}, File: {}".format(ion_name, nameValue)

            ion_data = {'xvals': dt_x,
                        'yvals': dt_y,
                        'xlabels': 'Drift time (bins)',
                        'ylabels': 'Intensity',
                        'charge': charge,
                        'xylimits': [mz_start, mz_end, mz_y_max],
                        'filename': nameValue}
            self.documentTree.on_update_data(ion_data, newName, document, data_type="ion.mobiligram")

        # Combine the contents in the dictionary - assumes they are ordered!
        counter = 0  # needed to start off
        xlabelsActual = []
        for counter, item in enumerate(range(self.filesList.GetItemCount()), 1):
            # Determine whether the title of the document matches the title of the item in the table
            # if it does not, skip the row
            docValue = self.filesList.GetItem(item, self.config.multipleMLColNames['document']).GetText()
            if docValue != document.title:
                continue
            key = self.filesList.GetItem(item, self.config.multipleMLColNames['filename']).GetText()
            if counter == 1:
                tempArray = tempDict[key][0]
                xLabelLow = document.multipleMassSpectrum[key]['trap']  # first iteration so first value
                xlabelsActual.append(document.multipleMassSpectrum[key]['trap'])
            else:
                imsList = tempDict[key][0]
                tempArray = np.concatenate((tempArray, imsList), axis=0)
                xlabelsActual.append(document.multipleMassSpectrum[key]['trap'])

        # Reshape data to form a 2D array of size 200 x number of files
        imsData2D = tempArray.reshape((200, counter), order='F')

        # Combine 2D array into 1D
        rtDataY = np.sum(imsData2D, axis=0)
        imsData1D = np.sum(imsData2D, axis=1).T

        # Get the x-axis labels
        xLabelHigh = document.multipleMassSpectrum[key]['trap']  # after the loop has finished, so last value
        if xLabelLow in [None, "None"] or xLabelHigh in [None, "None"]:
            msg = "The user-specified labels appear to be 'None'. Rather than failing to generate x-axis labels" + \
                  " a list of 1-n values is created."
            logger.warning(msg)
            xlabels = np.arange(1, counter)
        else:
            xlabels = np.linspace(xLabelLow, xLabelHigh, num=counter)
        ylabels = 1 + np.arange(imsData1D.shape[0])

        # Add data to the document
        ion_data = {'zvals': imsData2D,
                    'xvals': xlabels,
                    'xlabels': 'Collision Voltage (V)',
                    'yvals': ylabels,
                    'ylabels': 'Drift time (bins)',
                    'yvals1D': imsData1D,
                    'yvalsRT': rtDataY,
                    'cmap': document.colormap,
                    'title': label,
                    'label': label,
                    'charge': charge,
                    'alpha': item_information['alpha'],
                    'mask': item_information['mask'],
                    'color': item_information['color'],
                    'min_threshold': item_information['min_threshold'],
                    'max_threshold': item_information['max_threshold'],
                    'xylimits': [mz_start, mz_end, mz_y_max]}

        self.documentTree.on_update_data(ion_data, ion_name, document, data_type="ion.heatmap.combined")

    def __on_add_ion_IR(self, item_information, document, path, mz_start, mz_end, ion_name, ion_id, charge, label):
        # 2D
        __, __, zvals = self._get_driftscope_mobility_data(path)

        dataSplit, xvals, yvals, yvals_RT, yvals_DT = pr_origami.origami_combine_infrared(
            inputData=zvals, threshold=2000, noiseLevel=500)

        mz_y_max = item_information['intensity']
        # Add data to document object
        ion_data = {'zvals': dataSplit,
                    'xvals': xvals,
                    'xlabels': 'Wavenumber (cm⁻¹)',
                    'yvals': yvals,
                    'ylabels': 'Drift time (bins)',
                    'cmap': self.config.currentCmap,
                    'yvals1D': yvals_DT,
                    'yvalsRT': yvals_RT,
                    'title': label,
                    'label': label,
                    'charge': charge,
                    'alpha': item_information['alpha'],
                    'mask': item_information['mask'],
                    'color': item_information['color'],
                    'min_threshold': item_information['min_threshold'],
                    'max_threshold': item_information['max_threshold'],
                    'xylimits': [mz_start, mz_end, mz_y_max]}
        # Update document
        self.documentTree.on_update_data(ion_data, ion_name, document, data_type="ion.heatmap.raw")
        self.on_update_document(document, 'ions')

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

    def on_update_document(self, document, expand_item='document', expand_item_title=None):

        if expand_item == 'document':
            self.documentTree.add_document(docData=document, expandItem=document)
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
            self.documentTree.set_document(document_old=self.presenter.documentsDict[document.title],
                                           document_new=document)

        # update dictionary
        self.presenter.documentsDict[document.title] = document
        self.presenter.currentDoc = document.title

    def extract_from_plot_1D(self, xvalsMin, xvalsMax, yvalsMax, currentView=None, currentDoc=""):
        self.plot_page = self.plotsPanel._get_page_text()

        document = self._on_get_document()
        document_title = document.title

        # Extraction of data when the Interactive document is enabled is not possible
        if self.plot_page in ['RT', 'MS', '1D', '2D'] and document.dataType == 'Type: Interactive':
            args = ("Cannot extract data from Interactive document", 4)
            self.on_threading(args=args, action='statusbar.update')
            return

        # Extract mass spectrum from mobiligram window
        elif self.plot_page == '1D':
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
        elif self.plot_page == "MS" or currentView == "MS":
            if xvalsMin is None or xvalsMax is None:
                self.__update_statusbar('Your extraction range was outside the window. Please try again', 4)
                return

            if document.fileFormat == "Format: Thermo (.RAW)":
                return

            mz_start = np.round(xvalsMin, 2)
            mz_end = np.round(xvalsMax, 2)
            mz_start, mz_end = check_value_order(mz_start, mz_end)

            # Make sure the document has MS in first place (i.e. Text)
            if not document.gotMS:
                return

            # Get MS data for specified region and extract Y-axis maximum
            ms = document.massSpectrum
            ms = np.transpose([ms['xvals'], ms['yvals']])
            mz_y_max = np.round(get_maximum_value_in_range(ms, mz_range=(mz_start, mz_end)) * 100, 2)

            # predict charge state
            charge = self.data_processing.predict_charge_state(
                ms[:, 0], ms[:, 1], (mz_start, mz_end))
            color = self.ionPanel.on_check_duplicate_colors(
                self.config.customColors[randomIntegerGenerator(0, 15)])
            color = convertRGB255to1(color)
            colormap = self.config.overlay_cmaps[randomIntegerGenerator(0, len(self.config.overlay_cmaps) - 1)]

            if document.dataType in ['Type: ORIGAMI', 'Type: MANUAL', 'Type: Infrared']:
                self.view.onPaneOnOff(evt=ID_window_ionList, check=True)
                # Check if value already present
                outcome = self.ionPanel.onCheckForDuplicates(
                    mzStart=str(mz_start), mzEnd=str(mz_end))
                if outcome:
                    self.SetStatusText('Selected range already in the table', 3)
                    if currentView == "MS":
                        return outcome
                    return

                _add_to_table = {"mz_start": mz_start,
                                 "mz_end": mz_end,
                                 "charge": charge,
                                 "mz_ymax": mz_y_max,
                                 "color": convertRGB1to255(color),
                                 "colormap": colormap,
                                 "alpha": self.config.overlay_defaultAlpha,
                                 "mask": self.config.overlay_defaultMask,
                                 "document": document_title}
                self.ionPanel.on_add_to_table(_add_to_table, check_color=False)

                if self.config.showRectanges:
                    self.plotsPanel.on_plot_patches(
                        mz_start, 0, (mz_end - mz_start), 100000000000,
                        color=color, alpha=self.config.markerTransparency_1D,
                        repaint=True)

                if self.ionPanel.extractAutomatically:
                    self.presenter.on_extract_2D_from_mass_range_threaded(None, extract_type="new")

            elif document.dataType == 'Type: Multifield Linear DT':
                self.view.onPaneOnOff(evt=ID_window_multiFieldList, check=True)
                # Check if value already present
                outcome = self.view.panelLinearDT.bottomP.onCheckForDuplicates(mz_start=str(mz_start),
                                                                               mzEnd=str(mz_end))
                if outcome:
                    return
                self.view.panelLinearDT.bottomP.peaklist.Append([mz_start,
                                                                 mz_end,
                                                                 mz_y_max,
                                                                 "",
                                                                 self.presenter.currentDoc])

                if self.config.showRectanges:
                    self.plotsPanel.on_plot_patches(mz_start, 0, (mz_end - mz_start), 100000000000,
                                                    color=self.config.annotColor,
                                                    alpha=self.config.markerTransparency_1D,
                                                    repaint=True)

        # Extract data from calibration window
        if self.plot_page == "Calibration":
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
        elif self.plot_page == "RT" and document.dataType == 'Type: Multifield Linear DT':
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
                                                          document_title])

            self.plotsPanel.on_add_patch(xvalsMin, 0, (xvalsMax - xvalsMin), 100000000000,
                                         color=self.config.annotColor,
                                         alpha=(self.config.annotTransparency / 100),
                                         repaint=True, plot="RT")

        # Extract mass spectrum from chromatogram window
        elif self.plot_page == 'RT' and document.dataType != 'Type: Multifield Linear DT':
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
                self.view.SetStatusText('The scan range you selected was too small. Please choose wider range', 3)
                return
            # Extract data
            if document.fileFormat == "Format: Thermo (.RAW)":
                return
            else:
                self.presenter.on_extract_MS_from_chromatogram(startScan=xvalsMin, endScan=xvalsMax, units=rt_label)

        else:
            return

    def extract_from_plot_2D(self, dataOut):
        self.plot_page = self.plotsPanel._get_page_text()

        if self.plot_page == "DT/MS":
            xlabel = self.plotsPanel.plotMZDT.plot_labels.get("xlabel", "m/z")
            ylabel = self.plotsPanel.plotMZDT.plot_labels.get("ylabel", "Drift time (bins)")
        elif self.plot_page == "2D":
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
        if self.plot_page == "DT/MS":
            self.presenter.on_extract_RT_from_mzdt(xmin, xmax, ymin, ymax,
                                                   units_x=xlabel, units_y=ylabel)
        elif self.plot_page == "2D":
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
            xvals_RT, __, yvals_RT_norm = self._get_driftscope_chromatography_data(path)
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

    def on_extract_2D_from_mass_range_fcn(self, evt, extract_type="all"):
        """
        Extract 2D array for each m/z range specified in the table
        """
        if evt is None:
            evt = extract_type
        else:
            evt = "all"

        if not self.config.threading:
            self.on_extract_2D_from_mass_range(evt)
        else:
            args = (evt,)
            self.on_threading(action='extract.heatmap', args=args)

    def on_extract_2D_from_mass_range(self, extract_type="all"):
        """ extract multiple ions = threaded """

        for ion_id in range(self.ionList.GetItemCount()):
            # Extract ion name
            item_information = self.ionPanel.OnGetItemInformation(itemID=ion_id)
            document_title = item_information['document']
            print("doc", document_title)

            # Check if the ion has been assigned a filename
            if document_title == '':
                self.__update_statusbar('File name column was empty. Using the current document name instead', 4)
                document = self._on_get_document()
                document_title = document.title
                self.ionPanel.on_update_value_in_peaklist(ion_id, "document", document_title)

            document = self._on_get_document(document_title)
            path = document.path
            if not check_path_exists(path):
                msg = "File with {} path no longer exists".format(path)
                dlgBox("File no longer exists", msg, type="Error")
                return

            # Extract information from the table
            mz_start = item_information['start']
            mz_end = item_information['end']
            mz_y_max = item_information['intensity']
            label = item_information['label']
            charge = item_information['charge']

            if charge is None:
                charge = "1"

            # Create range name
            ion_name = item_information['ionName']

            # Check that the mzStart/mzEnd are above the acquire MZ value
            if mz_start < min(document.massSpectrum['xvals']):
                self.ionList.ToggleItem(index=ion_id)
                msg = "Ion: {} was below the minimum value in the mass spectrum.".format(ion_name) + \
                    " Consider removing it from the list"
                self.__update_statusbar(msg, 4)
                continue

            # Check whether this ion was already extracted
            if extract_type == 'new' and document.gotExtractedIons:
                try:
                    if document.IMS2Dions[ion_name]:
                        self.__update_statusbar("Data was already extracted for the : {} ion".format(ion_name), 4)
                        continue
                except KeyError:
                    pass

            elif extract_type == 'new' and document.gotCombinedExtractedIons:
                try:
                    if document.IMS2DCombIons[ion_name]:
                        self.__update_statusbar("Data was already extracted for the : {} ion".format(ion_name), 4)
                        continue
                except KeyError:
                    pass

            # Extract selected ions
            if extract_type == 'selected' and not self.ionList.IsChecked(index=ion_id):
                continue

            if document.dataType == 'Type: ORIGAMI':
                self.__on_add_ion_ORIGAMI(
                    item_information, document, path, mz_start, mz_end, mz_y_max, ion_name, label, charge)

            # Check if manual dataset
            elif document.dataType == 'Type: MANUAL':
                self.__on_add_ion_MANUAL(
                    item_information, document, mz_start, mz_end, mz_y_max, ion_name, ion_id, charge, label)

            elif document.dataType == 'Type: Infrared':
                self.__on_add_ion_IR(
                    item_information, document, path, mz_start, mz_end, mz_y_max, ion_name, ion_id, charge, label)
            else:
                return
            msg = "Extracted: {}/{}".format((ion_id + 1), self.ionList.GetItemCount())
            self.__update_statusbar(msg, 4)

    def on_open_multiple_ML_files_fcn(self, open_type, pathlist=[]):

        if self.config.lastDir is None or not os.path.isdir(self.config.lastDir):
            self.config.lastDir = os.getcwd()

        dlg = MDD.MultiDirDialog(self.view, title="Choose Waters (.raw) files to open...",
                                 defaultPath=self.config.lastDir,
                                 agwStyle=MDD.DD_MULTIPLE | MDD.DD_DIR_MUST_EXIST)

        if dlg.ShowModal() == wx.ID_OK:
            pathlist = dlg.GetPaths()

        if len(pathlist) == 0:
            self.__update_statusbar("Please select at least one file in order to continue.", 4)
            return

        if open_type == "multiple_files_add":
            document = self._get_document_of_type('Type: MANUAL')
        elif open_type == "multiple_files_new_document":
            document = self.__create_new_document()

        if not self.config.threading:
            self.on_open_multiple_ML_files(document, open_type, pathlist)
        else:
            self.on_threading("load.multiple.raw.masslynx", (document, open_type, pathlist,))

    def on_open_multiple_ML_files(self, document, open_type, pathlist=[]):
        # http://stackoverflow.com/questions/1252481/sort-dictionary-by-another-dictionary
        # http://stackoverflow.com/questions/22520739/python-sort-a-dict-by-values-producing-a-list-how-to-sort-this-from-largest-to

        tstart = ttime()

        if document is None:
            logger.warning("Document was not selected.")
            return

        for i, file_path in enumerate(pathlist):
            path = check_waters_path(file_path)
            path = clean_up_MDD_path(path)
            if not check_path_exists(path):
                logger.warning("File with path: {} does not exist".format(path))
                continue

            # add data to document
            __, file_name = os.path.split(path)
            parameters = self.config.importMassLynxInfFile(path=path, manual=True)
            xlimits = [parameters['startMS'], parameters['endMS']]
            ms_x, ms_y = self._get_driftscope_spectrum_data(path)
            dt_x, dt_y = self._get_driftscope_mobiligram_data(path)

            try:
                color = self.config.customColors[i]
            except KeyError:
                color = randomColorGenerator(return_as_255=True)
            print("pre", color)
            color = convertRGB255to1(
                self.filesPanel.on_check_duplicate_colors(color, document_name=document.title))
            print("post", color)
            label = os.path.splitext(file_name)[0]

            add_dict = {"filename": file_name,
                        "variable": parameters["trapCE"],
                        "document": document.title,
                        "label": label,
                        "color": color}
            self.filesPanel.on_add_to_table(add_dict)

            document.gotMultipleMS = True
            document.multipleMassSpectrum[file_name] = {'trap': parameters['trapCE'],
                                                        'xvals': ms_x,
                                                        'yvals': ms_y,
                                                        'ims1D': dt_y,
                                                        'ims1DX': dt_x,
                                                        'xlabel': 'Drift time (bins)',
                                                        'xlabels': 'm/z (Da)',
                                                        'path': path,
                                                        'color': color,
                                                        'parameters': parameters,
                                                        'xlimits': xlimits}

        kwargs = {'auto_range': False,
                  'mz_min': self.config.ms_mzStart,
                  'mz_max': self.config.ms_mzEnd,
                  'mz_bin': self.config.ms_mzBinSize,
                  'linearization_mode': self.config.ms_linearization_mode}
        msg = "Linearization method: {} | min: {} | max: {} | window: {} | auto-range: {}".format(
            self.config.ms_linearization_mode,
            self.config.ms_mzStart,
            self.config.ms_mzEnd,
            self.config.ms_mzBinSize,
            self.config.ms_auto_range)
        self.__update_statusbar(msg, 4)

        # check the min/max values in the mass spectrum
        if self.config.ms_auto_range:
            mzStart, mzEnd = pr_spectra.check_mass_range(ms_dict=document.multipleMassSpectrum)
            self.config.ms_mzStart = mzStart
            self.config.ms_mzEnd = mzEnd
            kwargs.update(mz_min=mzStart, mz_max=mzEnd)

        msFilenames = ["m/z"]
        for counter, key in enumerate(document.multipleMassSpectrum):
            msFilenames.append(key)

            if counter == 0:
                ms_x, ms_y = pr_spectra.linearize_data(
                    document.multipleMassSpectrum[key]['xvals'],
                    document.multipleMassSpectrum[key]['yvals'],
                    **kwargs)
                ms_y_sum = ms_y
            else:
                ms_x, ms_y = pr_spectra.linearize_data(
                    document.multipleMassSpectrum[key]['xvals'],
                    document.multipleMassSpectrum[key]['yvals'],
                    **kwargs)
                ms_y_sum += ms_y

        xlimits = [parameters['startMS'], parameters['endMS']]
        document.gotMS = True
        document.massSpectrum = {'xvals': ms_x,
                                 'yvals': ms_y_sum,
                                 'xlabels':'m/z (Da)',
                                 'xlimits':xlimits}
        # Plot
        name_kwargs = {"document": document.title, "dataset": "Mass Spectrum"}
        self.view.panelPlots.on_plot_MS(ms_x, ms_y_sum, xlimits=xlimits, **name_kwargs)

        # Add info to document
        document.parameters = parameters
        document.dataType = 'Type: MANUAL'
        document.fileFormat = 'Format: MassLynx (.raw)'
        self.on_update_document(document, 'document')

        # Show panel
        self.view.onPaneOnOff(evt=ID_window_multipleMLList, check=True)
        self.filesList.on_remove_duplicates()

        # Update status bar with MS range
        self.__update_statusbar("Data extraction took {:.4f} seconds for {} files.".format(
            ttime() - tstart, i + 1), 4)
        self.view.SetStatusText("{}-{}".format(parameters['startMS'], parameters['endMS']), 1)
        self.view.SetStatusText("MSMS: {}".format(parameters['setMS']), 2)

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
#         self.on_update_document(document, 'document')
#
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
#         self.on_update_document(self.docs, 'mass_spectra')
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
#             msDict = io_waters.rawMassLynx_MS_bin(filename=str(document.path),
#                                                   function=1,
#                                                   startScan=startScan, endScan=endScan,
#                                                   binData=self.config.import_binOnImport,
#                                                   mzStart=self.config.ms_mzStart,
#                                                   mzEnd=self.config.ms_mzEnd,
#                                                   binsize=self.config.ms_mzBinSize,
#                                                   **kwargs)
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
#         self.on_update_document(document, 'mass_spectra', expand_item_title=itemName)
#         # Plot MS
#         name_kwargs = {"document": document.title, "dataset": itemName}
#         self.view.panelPlots.on_plot_MS(msX, msY, xlimits=xlimits, show_in_window="RT", **name_kwargs)
#         # Set status
#         msg = "Extracted MS data for rt: %s-%s" % (startScan, endScan)
#         self.onThreading(None, (msg, 3), action='updateStatusbar')
#
#     def on_extract_MS_from_heatmap(self, startScan=None, endScan=None, dtStart=None,
#                                    dtEnd=None, units_x="Scans", units_y="Drift time (bins)"):
#         """ Function to extract MS data for specified DT/MS region """
#
#         document_title = self.view.panelDocuments.documents.enableCurrentDocument()
#         if document_title == 'Current documents':
#             return
#         document = self.documentsDict[document_title]
#
#         try:
#             scanTime = document.parameters['scanTime']
#         except:
#             scanTime = None
#
#         try:
#             pusherFreq = document.parameters['pusherFreq']
#         except:
#             pusherFreq = None
#
#         try:
#             xlimits = [document.parameters['startMS'], document.parameters['endMS']]
#         except Exception:
#             try:
#                 xlimits = [np.min(document.massSpectrum['xvals']), np.max(document.massSpectrum['xvals'])]
#             except:
#                 return
#
#         if units_x == "Scans":
#             if scanTime is None:
#                 return
#             rtStart = round(startScan * (scanTime / 60), 2)
#             rtEnd = round(endScan * (scanTime / 60), 2)
#         elif units_x in ['Time (min)', 'Retention time (min)']:
#             rtStart, rtEnd = startScan, endScan
#             if scanTime is None:
#                 return
#             startScan = np.ceil(((startScan / scanTime) * 60)).astype(int)
#             endScan = np.ceil(((endScan / scanTime) * 60)).astype(int)
#
#         if units_y in ["Drift time (ms)", "Arrival time (ms)"]:
#             if pusherFreq is None:
#                 return
#             dtStart = np.ceil(((dtStart / pusherFreq) * 1000)).astype(int)
#             dtEnd = np.ceil(((dtEnd / pusherFreq) * 1000)).astype(int)
#
#         # Mass spectra
#         try:
#             extract_kwargs = {'return_data': True}
#             msX, msY = io_waters.driftscope_extract_MS(path=document.path,
#                                                         driftscope_path=self.config.driftscopePath,
#                                                         rt_start=rtStart, rt_end=rtEnd,
#                                                         dt_start=dtStart, dt_end=dtEnd,
#                                                         **extract_kwargs)
#             if xlimits is None:
#                 xlimits = [np.min(msX), np.max(msX)]
#         except (IOError, ValueError):
#             return
#
#         # Add data to dictionary
#         itemName = "Scans: {}-{} | Drift time: {}-{}".format(startScan, endScan,
#                                                              dtStart, dtEnd)
#
#         document.gotMultipleMS = True
#         document.multipleMassSpectrum[itemName] = {'xvals': msX,
#                                                    'yvals': msY,
#                                                    'range': [startScan, endScan],
#                                                    'xlabels': 'm/z (Da)',
#                                                    'xlimits': xlimits}
#
#         self.on_update_document(document, 'mass_spectra', expand_item_title=itemName)
#         # Plot MS
#         name_kwargs = {"document": document.title, "dataset": itemName}
#         self.view.panelPlots.on_plot_MS(msX, msY, xlimits=xlimits, **name_kwargs)
#         # Set status
#         msg = "Extracted MS data for rt: %s-%s" % (startScan, endScan)
#         self.onThreading(None, (msg, 3), action='updateStatusbar')
#
#     def onCombineCEvoltagesMultiple(self, evt):
#         # self.config.extractMode = 'multipleIons'
#
#         # Shortcut to ion table
#         tempList = self.view.panelMultipleIons.peaklist
#
#         # Make a list of current documents
#         for row in range(tempList.GetItemCount()):
#
#             # Check which mode was selected
#             if evt.GetId() == ID_combineCEscans:
#                 pass
#             elif evt.GetId() == ID_combineCEscansSelectedIons:
#                 if not tempList.IsChecked(index=row):
#                     continue
#
#             self.currentDoc = tempList.GetItem(itemId=row,
#                                                col=self.config.peaklistColNames['filename']).GetText()
#             # Check that data was extracted first
#             if self.currentDoc == '':
#                 msg = "Please extract data first"
#                 dlgBox(exceptionTitle='Extract data first',
#                        exceptionMsg=msg,
#                        type="Warning")
#                 continue
#             # Get document
#             self.docs = self.documentsDict[self.currentDoc]
#
#             # Check that this data was opened in ORIGAMI mode and has extracted data
#             if self.docs.dataType == 'Type: ORIGAMI' and self.docs.gotExtractedIons:
#                 zvals = self.docs.IMS2Dions
#             else:
#                 msg = "Data was not extracted yet. Please extract before continuing."
#                 dlgBox(exceptionTitle='Missing data',
#                        exceptionMsg=msg,
#                        type="Error")
#                 continue
#
#             # Extract ion name
#     item_informationitemInfo = self.view.panelMultipleIons.OnGetItemInformation(itemID=row)
#             selectedItem = itemInfo['ionName']
#
#         # Combine data
#         # LINEAR METHOD
#             if self.config.origami_acquisition == 'Linear':
#                 # Check that the user filled in appropriate parameters
#                 if ((evt.GetId() == ID_recalculateORIGAMI or self.config.useInternalParamsCombine)
#                         and self.docs.gotCombinedExtractedIons):
#                     try:
#                         self.config.origami_startScan = self.docs.IMS2DCombIons[selectedItem]['parameters']['firstVoltage']
#                         self.config.origami_startVoltage = self.docs.IMS2DCombIons[selectedItem]['parameters']['startV']
#                         self.config.origami_endVoltage = self.docs.IMS2DCombIons[selectedItem]['parameters']['endV']
#                         self.config.origami_stepVoltage = self.docs.IMS2DCombIons[selectedItem]['parameters']['stepV']
#                         self.config.origami_spv = self.docs.IMS2DCombIons[selectedItem]['parameters']['spv']
#                     except Exception:
#                         pass
#                 # Ensure that config is not missing variabels
#                 elif not any([self.config.origami_startScan, self.config.origami_startVoltage, self.config.origami_endVoltage,
#                               self.config.origami_stepVoltage, self.config.origami_spv]):
#                     msg = 'Cannot perform action. Missing fields in the ORIGAMI parameters panel'
#                     self.onThreading(None, (msg, 3), action='updateStatusbar')
#                     return
#
#                 # Check if ion/file has specified ORIGAMI method
#                 if itemInfo['method'] == '':
#                     tempList.SetStringItem(index=row, col=self.config.peaklistColNames['method'],
#                                            label=self.config.origami_acquisition)
#                 elif (itemInfo['method'] == self.config.origami_acquisition and self.config.overrideCombine):
#                     pass
#                 # Check if using internal parameters and item is checked
#                 elif self.config.useInternalParamsCombine and tempList.IsChecked(index=row):
#                     pass
#                 else:
#                     continue
#                 # Combine data
#                 imsData2D, scanList, parameters = pr_origami.origami_combine_linear(imsDataInput=zvals[selectedItem]['zvals'],
#                                                                                     firstVoltage=self.config.origami_startScan,
#                                                                                     startVoltage=self.config.origami_startVoltage,
#                                                                                     endVoltage=self.config.origami_endVoltage,
#                                                                                     stepVoltage=self.config.origami_stepVoltage,
#                                                                                     scansPerVoltage=self.config.origami_spv)
#             # EXPONENTIAL METHOD
#             elif self.config.origami_acquisition == 'Exponential':
#                 # Check that the user filled in appropriate parameters
#                 if ((evt.GetId() == ID_recalculateORIGAMI or self.config.useInternalParamsCombine)
#                         and self.docs.gotCombinedExtractedIons):
#                     try:
#                         self.config.origami_startScan = self.docs.IMS2DCombIons[selectedItem]['parameters']['firstVoltage']
#                         self.config.origami_startVoltage = self.docs.IMS2DCombIons[selectedItem]['parameters']['startV']
#                         self.config.origami_endVoltage = self.docs.IMS2DCombIons[selectedItem]['parameters']['endV']
#                         self.config.origami_stepVoltage = self.docs.IMS2DCombIons[selectedItem]['parameters']['stepV']
#                         self.config.origami_spv = self.docs.IMS2DCombIons[selectedItem]['parameters']['spv']
#                         self.config.origami_exponentialIncrement = self.docs.IMS2DCombIons[
#                             selectedItem]['parameters']['expIncrement']
#                         self.config.origami_exponentialPercentage = self.docs.IMS2DCombIons[
#                             selectedItem]['parameters']['expPercent']
#                     except Exception:
#                         pass
#                 # Ensure that config is not missing variabels
#                 elif not any([self.config.origami_startScan, self.config.origami_startVoltage, self.config.origami_endVoltage,
#                               self.config.origami_stepVoltage, self.config.origami_spv, self.config.origami_exponentialIncrement,
#                               self.config.origami_exponentialPercentage]):
#                     msg = 'Cannot perform action. Missing fields in the ORIGAMI parameters panel'
#                     self.onThreading(None, (msg, 3), action='updateStatusbar')
#                     return
#
#                 # Check if ion/file has specified ORIGAMI method
#                 if itemInfo['method'] == '':
#                     tempList.SetStringItem(index=row, col=self.config.peaklistColNames['method'],
#                                            label=self.config.origami_acquisition)
#                 elif (itemInfo['method'] == self.config.origami_acquisition and
#                       self.config.overrideCombine):
#                     pass
#                 # Check if using internal parameters and item is checked
#                 elif self.config.useInternalParamsCombine and tempList.IsChecked(index=row):
#                     pass
#                 else:
#                     continue  # skip
#                 imsData2D, scanList, parameters = pr_origami.origami_combine_exponential(imsDataInput=zvals[selectedItem]['zvals'],
#                                                                                          firstVoltage=self.config.origami_startScan,
#                                                                                          startVoltage=self.config.origami_startVoltage,
#                                                                                          endVoltage=self.config.origami_endVoltage,
#                                                                                          stepVoltage=self.config.origami_stepVoltage,
#                                                                                          scansPerVoltage=self.config.origami_spv,
#                                                                                          expIncrement=self.config.origami_exponentialIncrement,
#                                                                                          expPercentage=self.config.origami_exponentialPercentage)
#             # FITTED/BOLTZMANN METHOD
#             elif self.config.origami_acquisition == 'Fitted':
#                 # Check that the user filled in appropriate parameters
#                 if ((evt.GetId() == ID_recalculateORIGAMI or self.config.useInternalParamsCombine)
#                         and self.docs.gotCombinedExtractedIons):
#                     try:
#                         self.config.origami_startScan = self.docs.IMS2DCombIons[selectedItem]['parameters']['firstVoltage']
#                         self.config.origami_startVoltage = self.docs.IMS2DCombIons[selectedItem]['parameters']['startV']
#                         self.config.origami_endVoltage = self.docs.IMS2DCombIons[selectedItem]['parameters']['endV']
#                         self.config.origami_stepVoltage = self.docs.IMS2DCombIons[selectedItem]['parameters']['stepV']
#                         self.config.origami_spv = self.docs.IMS2DCombIons[selectedItem]['parameters']['spv']
#                         self.config.origami_boltzmannOffset = self.docs.IMS2DCombIons[selectedItem]['parameters']['dx']
#                     except Exception:
#                         pass
#                 # Ensure that config is not missing variabels
#                 elif not any([self.config.origami_startScan, self.config.origami_startVoltage, self.config.origami_endVoltage,
#                               self.config.origami_stepVoltage, self.config .scansPerVoltage, self.config.origami_boltzmannOffset]):
#                     msg = 'Cannot perform action. Missing fields in the ORIGAMI parameters panel'
#                     self.onThreading(None, (msg, 3), action='updateStatusbar')
#                     return
#
#                 # Check if ion/file has specified ORIGAMI method
#                 if itemInfo['method'] == '':
#                     tempList.SetStringItem(index=row, col=self.config.peaklistColNames['method'],
#                                            label=self.config.origami_acquisition)
#                 elif (itemInfo['method'] == self.config.origami_acquisition and
#                       self.config.overrideCombine):
#                     pass
#                 # Check if using internal parameters and item is checked
#                 elif self.config.useInternalParamsCombine and tempList.IsChecked(index=row):
#                     pass
#                 else:
#                     continue  # skip
#                 imsData2D, scanList, parameters = pr_origami.origami_combine_boltzmann(imsDataInput=zvals[selectedItem]['zvals'],
#                                                                                        firstVoltage=self.config.origami_startScan,
#                                                                                        startVoltage=self.config.origami_startVoltage,
#                                                                                        endVoltage=self.config.origami_endVoltage,
#                                                                                        stepVoltage=self.config.origami_stepVoltage,
#                                                                                        scansPerVoltage=self.config.origami_spv,
#                                                                                        dx=self.config.origami_boltzmannOffset)
#             # USER-DEFINED/LIST METHOD
#             elif self.config.origami_acquisition == 'User-defined':
#                 print((self.config.origamiList, self.config.origami_startScan))
#                 errorMsg = None
#                 # Check that the user filled in appropriate parameters
#                 if evt.GetId() == ID_recalculateORIGAMI or self.config.useInternalParamsCombine:
#                     try:
#                         self.config.origami_startScan = self.docs.IMS2DCombIons[selectedItem]['parameters']['firstVoltage']
#                         self.config.origamiList = self.docs.IMS2DCombIons[selectedItem]['parameters']['inputList']
#                     except Exception:
#                         pass
#                 # Ensure that config is not missing variabels
#                 elif len(self.config.origamiList) == 0:
#                     errorMsg = "Please load a text file with ORIGAMI parameters"
#                 elif not self.config.origami_startScan:
#                     errorMsg = "The first scan is incorect (currently: %s)" % self.config.origami_startScan
#                 elif self.config.origamiList[:, 0].shape != self.config.origamiList[:, 1].shape:
#                     errorMsg = "The collision voltage list is of incorrect shape."
#
#                 if errorMsg is not None:
#                     self.onThreading(None, (errorMsg, 3), action='updateStatusbar')
#                     return
#
#                 # Check if ion/file has specified ORIGAMI method
#                 if itemInfo['method'] == '':
#                     tempList.SetStringItem(index=row, col=self.config.peaklistColNames['method'],
#                                            label=self.config.origami_acquisition)
#                 elif (itemInfo['method'] == self.config.origami_acquisition and
#                       self.config.overrideCombine):
#                     pass
#                 # Check if using internal parameters and item is checked
#                 elif self.config.useInternalParamsCombine and tempList.IsChecked(index=row):
#                     pass
#                 else:
#                     continue  # skip
#                 imsData2D, xlabels, scanList, parameters = pr_origami.origami_combine_userDefined(
#     imsDataInput=zvals[selectedItem]['zvals'], firstVoltage=self.config.origami_startScan, inputList=self.config.origamiList)
#
#             if imsData2D[0] is None:
#                 msg = "With your current input, there would be too many scans in your file! " + \
#                       "There are %s scans in your file and your settings suggest there should be %s" \
#                       % (imsData2D[2], imsData2D[1])
#                 dlgBox(exceptionTitle='Are your settings correct?',
#                        exceptionMsg=msg, type="Warning")
#                 continue
#
#             # Add x-axis and y-axis labels
#             if self.config.origami_acquisition != 'User-defined':
#                 xlabels = np.arange(self.config.origami_startVoltage,
#                                     (self.config.origami_endVoltage + self.config.origami_stepVoltage),
#                                     self.config.origami_stepVoltage)
#
#             # Y-axis is bins by default
#             ylabels = np.arange(1, 201, 1)
#             # Combine 2D array into 1D
#             imsData1D = np.sum(imsData2D, axis=1).T
#             yvalsRT = np.sum(imsData2D, axis=0)
#             # Check if item has labels, alpha, charge
#             charge = zvals[selectedItem].get('charge', None)
#             cmap = zvals[selectedItem].get('cmap', self.config.overlay_cmaps[randomIntegerGenerator(0, 5)])
#             color = zvals[selectedItem].get('color', self.config.customColors[randomIntegerGenerator(0, 15)])
#             label = zvals[selectedItem].get('label', None)
#             alpha = zvals[selectedItem].get('alpha', self.config.overlay_defaultAlpha)
#             mask = zvals[selectedItem].get('mask', self.config.overlay_defaultMask)
#             min_threshold = zvals[selectedItem].get('min_threshold', 0)
#             max_threshold = zvals[selectedItem].get('max_threshold', 1)
#
#             # Add 2D data to document object
#             self.docs.gotCombinedExtractedIons = True
#             self.docs.IMS2DCombIons[selectedItem] = {'zvals': imsData2D,
#                                                      'xvals': xlabels,
#                                                      'xlabels': 'Collision Voltage (V)',
#                                                      'yvals': ylabels,
#                                                      'ylabels': 'Drift time (bins)',
#                                                      'yvals1D': imsData1D,
#                                                      'yvalsRT': yvalsRT,
#                                                      'cmap': cmap,
#                                                      'xylimits': zvals[selectedItem]['xylimits'],
#                                                      'charge': charge,
#                                                      'label': label,
#                                                      'alpha': alpha,
#                                                      'mask': mask,
#                                                      'color': color,
#                                                      'min_threshold': min_threshold,
#                                                      'max_threshold': max_threshold,
#                                                      'scanList': scanList,
#                                                      'parameters': parameters}
#             self.docs.combineIonsList = scanList
#             # Add 1D data to document object
#             self.docs.gotCombinedExtractedIonsRT = True
#             self.docs.IMSRTCombIons[selectedItem] = {'xvals': xlabels,
#                                                      'yvals': np.sum(imsData2D, axis=0),
#                                                      'xlabels': 'Collision Voltage (V)'}
#
#             # Update document
#             self.on_update_document(self.docs, 'combined_ions')

