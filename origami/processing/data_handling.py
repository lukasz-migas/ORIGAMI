import copy
import logging
import math
import os
import re
import threading
from sys import platform

import numpy as np
import processing.heatmap as pr_heatmap
import processing.origami_ms as pr_origami
import processing.spectra as pr_spectra
import readers.io_text_files as io_text
import wx
from document import document as documents
from gui_elements.dialog_multi_directory_picker import DialogMultiDirectoryPicker
from gui_elements.dialog_select_document import DialogSelectDocument
from gui_elements.misc_dialogs import dlgBox
from ids import ID_load_masslynx_raw
from ids import ID_load_origami_masslynx_raw
from ids import ID_openIRRawFile
from ids import ID_window_ccsList
from ids import ID_window_ionList
from ids import ID_window_multiFieldList
from ids import ID_window_multipleMLList
from processing.utils import find_nearest_value
from processing.utils import get_maximum_value_in_range
from pubsub import pub
from readers.io_document import open_py_object
from readers.io_document import save_py_object
from utils.check import check_axes_spacing
from utils.check import check_value_order
from utils.check import isempty
from utils.color import convertRGB1to255
from utils.color import convertRGB255to1
from utils.color import randomColorGenerator
from utils.converters import byte2str
from utils.converters import str2int
from utils.converters import str2num
from utils.path import check_path_exists
from utils.path import check_waters_path
from utils.path import get_base_path
from utils.path import get_path_and_fname
from utils.random import randomIntegerGenerator
from utils.ranges import get_min_max
from utils.time import getTime
from utils.time import ttime
# enable on windowsOS only
if platform == 'win32':
    import readers.io_waters_raw as io_waters
    import readers.io_waters_raw_api as io_waters_raw_api

logger = logging.getLogger('origami')


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

        if action == 'statusbar.update':
            th = threading.Thread(target=self.view.updateStatusbar, args=args)
        elif action == 'load.raw.masslynx':
            th = threading.Thread(target=self.on_open_single_MassLynx_raw, args=args)
        elif action == 'load.text.heatmap':
            th = threading.Thread(target=self.on_open_single_text_2D, args=args)
        elif action == 'load.multiple.text.heatmap':
            th = threading.Thread(target=self.on_open_multiple_text_2D, args=args)
        elif action == 'load.text.spectrum':
            th = threading.Thread(target=self.on_add_text_MS, args=args)
        elif action == 'load.raw.masslynx.ms_only':
            th = threading.Thread(target=self.on_open_MassLynx_raw_MS_only, args=args)
        elif action == 'extract.heatmap':
            th = threading.Thread(target=self.on_extract_2D_from_mass_range, args=args)
        elif action == 'load.multiple.raw.masslynx':
            th = threading.Thread(target=self.on_open_multiple_ML_files, args=args)
        elif action == 'save.document':
            th = threading.Thread(target=self.on_save_document, args=args)
        elif action == 'save.all.document':
            th = threading.Thread(target=self.on_save_all_documents, args=args)

        elif action == 'load.document':
            th = threading.Thread(target=self.on_open_document, args=args)

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

        if document_title is None or document_title == 'Documents':
            return None

#         print(self.presenter.documentsDict.keys())

        document_title = byte2str(document_title)
        document = self.presenter.documentsDict[document_title]

        return document

    def _on_get_path(self):
        dlg = wx.FileDialog(
            self.view,
            'Please select name and path for the document...',
            '', '', '', wx.FD_SAVE,
        )
        if dlg.ShowModal() == wx.ID_OK:
            path, fname = os.path.split(dlg.GetPath())

            return path, fname
        else:
            return None, None

    def _get_waters_api_reader(self, document):
        reader = document.file_reader.get('data_reader', None)
        if reader is None:
            reader = io_waters_raw_api.WatersRawReader(check_waters_path(document.path))

        return reader

    def _get_waters_api_spectrum_data(self, reader, **kwargs):
        fcn = 0
        if not hasattr(reader, 'mz_spacing'):
            __, __ = reader.generate_mz_interpolation_range(fcn)

        mz_x = reader.mz_x

        start_scan = kwargs.get('start_scan', 0)
        end_scan = kwargs.get('end_scan', reader.stats_in_functions[fcn]['n_scans'])
        scan_list = kwargs.get('scan_list', np.arange(start_scan, end_scan))

        mz_y = reader.get_summed_spectrum(fcn, 0, mz_x, scan_list)
        mz_y = mz_y.astype(np.int32)

        return mz_x, mz_y

    def _get_driftscope_spectrum_data(self, path, **kwargs):
        kwargs.update({'return_data': True})
        ms_x, ms_y = io_waters.driftscope_extract_MS(
            path=path, driftscope_path=self.config.driftscopePath, **kwargs
        )

        return ms_x, ms_y

    def _get_driftscope_chromatography_data(self, path, **kwargs):
        kwargs.update({'return_data': True, 'normalize': True})
        xvals_RT, yvals_RT, yvals_RT_norm = io_waters.driftscope_extract_RT(
            path=path, driftscope_path=self.config.driftscopePath, **kwargs
        )

        return xvals_RT, yvals_RT, yvals_RT_norm

    def _get_driftscope_mobiligram_data(self, path, **kwargs):
        kwargs.update({'return_data': True})
        xvals_DT, yvals_DT = io_waters.driftscope_extract_DT(
            path=path, driftscope_path=self.config.driftscopePath, **kwargs
        )

        return xvals_DT, yvals_DT

    def _get_driftscope_mobility_data(self, path, **kwargs):
        kwargs.update({'return_data': True})
        zvals = io_waters.driftscope_extract_2D(
            path=path, driftscope_path=self.config.driftscopePath, **kwargs
        )
        y_size, x_size = zvals.shape
        xvals = 1 + np.arange(x_size)
        yvals = 1 + np.arange(y_size)

        return xvals, yvals, zvals

    def _get_driftscope_mobility_vs_spectrum_data(self, path, mz_min, mz_max, mz_binsize=None, **kwargs):

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
            **kwargs
        )

        # in cases when the bin size is very small, the number of points in the zvals might not match those in the
        # xvals hence this should be resampled
        if n_points != zvals_MSDT.shape[1]:
            n_points = zvals_MSDT.shape[1]

        y_size, __ = zvals_MSDT.shape
        # calculate m/z values
        xvals_MSDT = np.linspace(
            mz_min - mz_binsize,
            mz_max + mz_binsize,
            n_points,
            endpoint=True,
        )
        # calculate DT bins
        yvals_MSDT = 1 + np.arange(y_size)

        return xvals_MSDT, yvals_MSDT, zvals_MSDT

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
            elif (
                self.presenter.documentsDict[document_title].dataType == document_type and
                self.presenter.documentsDict[document_title].fileFormat == document_format
            ):
                document_list.append(document_title)

        return document_list

    def _get_document_of_type(self, document_type):
        document_list = self.__get_document_list_of_type(document_type=document_type)

        if len(document_list) == 0:
            self.__update_statusbar('Did not find appropriate document. Creating a new one...', 4)
            document = self.__create_new_document()
        elif len(document_list) == 1:
            document = self._on_get_document(document_list[0])
        else:
            dlg = DialogSelectDocument(self.view, presenter=self.presenter, document_list=document_list)
            if dlg.ShowModal() == wx.ID_OK:
                return

            document_title = dlg.current_document
            if document_title is None:
                self.__update_statusbar('Please select document', 4)
                return

            document = self._on_get_document(document_title)
            self.__update_statusbar('Will be using {} document'.format(document_title), 4)

        return document

    def __create_new_document(self):
        dlg = wx.FileDialog(
            self.view, 'Please select a name for the document',
            '', '', '', wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        )
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

    def on_add_ion_ORIGAMI(
        self, item_information, document, path, mz_start, mz_end, mz_y_max, ion_name,
        label, charge,
    ):
        kwargs = dict(mz_start=mz_start, mz_end=mz_end)
        # 1D
        try:
            __, yvals_DT = self._get_driftscope_mobiligram_data(path, **kwargs)
        except IOError:
            msg = 'Failed to open the file - most likely because this file no longer exists' + \
                  ' or has been moved. You can change the document path by right-clicking\n' + \
                  ' on the document in the Document Tree and \n' + \
                  ' selecting Notes, Information, Labels...'
            dlgBox(exceptionTitle='Missing folder', exceptionMsg=msg, type='Error')
            return
        # RT
        __, yvals_RT, __ = self._get_driftscope_chromatography_data(path, **kwargs)

        # 2D
        xvals, yvals, zvals = self._get_driftscope_mobility_data(path, **kwargs)

        # Add data to document object
#         document.gotExtractedIons = True
#         document.IMS2Dions[ion_name]
        ion_data = {
            'zvals': zvals,
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
            'xylimits': [mz_start, mz_end, mz_y_max],
        }

        self.documentTree.on_update_data(ion_data, ion_name, document, data_type='ion.heatmap.raw')

    def on_add_ion_MANUAL(
        self, item_information, document, mz_start, mz_end, mz_y_max, ion_name, ion_id,
        charge, label,
    ):

        self.filesList.on_sort(2, False)
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
                    msg = \
                        'It would appear ORIGAMI cannot find the file on your disk. You can try to fix this issue\n' + \
                        'by updating the document path by right-clicking on the document and selecting\n' + \
                        "'Notes, Information, Labels...' and updating the path to where the dataset is found.\n" + \
                        'After that, try again and ORIGAMI will try to stitch the new document path with the file name.\n'
                    dlgBox(exceptionTitle='Error', exceptionMsg=msg, type='Error')
                    return

            # Get height of the peak
            self.ionPanel.on_update_value_in_peaklist(ion_id, 'method', 'Manual')

            # Create temporary dictionary for all IMS data
            tempDict[nameValue] = [dt_y]
            # Add 1D data to 1D data container
            newName = '{}, File: {}'.format(ion_name, nameValue)

            ion_data = {
                'xvals': dt_x,
                'yvals': dt_y,
                'xlabels': 'Drift time (bins)',
                'ylabels': 'Intensity',
                'charge': charge,
                'xylimits': [mz_start, mz_end, mz_y_max],
                'filename': nameValue,
            }
            self.documentTree.on_update_data(ion_data, newName, document, data_type='ion.mobiligram')

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
            energy = str2num(document.multipleMassSpectrum[key]['trap'])
            if counter == 1:
                tempArray = tempDict[key][0]
            else:
                imsList = tempDict[key][0]
                tempArray = np.concatenate((tempArray, imsList), axis=0)
            xlabelsActual.append(energy)

        # Reshape data to form a 2D array of size 200 x number of files
        zvals = tempArray.reshape((200, counter), order='F')

        try:
            xLabelHigh = np.max(xlabelsActual)
            xLabelLow = np.min(xlabelsActual)
        except Exception:
            xLabelLow, xLabelHigh = None, None

        # Get the x-axis labels
        if xLabelLow in [None, 'None'] or xLabelHigh in [None, 'None']:
            msg = "The user-specified labels appear to be 'None'. Rather than failing to generate x-axis labels" + \
                  ' a list of 1-n values is created.'
            logger.warning(msg)
            xvals = np.arange(1, counter)
        else:
            xvals = xlabelsActual  # np.linspace(xLabelLow, xLabelHigh, num=counter)

        yvals = 1 + np.arange(200)
        if not check_axes_spacing(xvals):
            msg = \
                'The spacing between the energy variables is not even. Linear interpolation will be performed to' + \
                ' ensure even spacing between values.'
            self.__update_statusbar(msg, field=4)
            logger.warning(msg)

            xvals, yvals, zvals = pr_heatmap.interpolate_2D(xvals, yvals, zvals)

        # Combine 2D array into 1D
        rt_y = np.sum(zvals, axis=0)
        dt_y = np.sum(zvals, axis=1).T

        # Add data to the document
        ion_data = {
            'zvals': zvals,
            'xvals': xvals,
            'xlabels': 'Collision Voltage (V)',
            'yvals': yvals,
            'ylabels': 'Drift time (bins)',
            'yvals1D': dt_y,
            'yvalsRT': rt_y,
            'cmap': document.colormap,
            'title': label,
            'label': label,
            'charge': charge,
            'alpha': item_information['alpha'],
            'mask': item_information['mask'],
            'color': item_information['color'],
            'min_threshold': item_information['min_threshold'],
            'max_threshold': item_information['max_threshold'],
            'xylimits': [mz_start, mz_end, mz_y_max],
        }

        self.documentTree.on_update_data(ion_data, ion_name, document, data_type='ion.heatmap.combined')

    def on_add_ion_IR(self, item_information, document, path, mz_start, mz_end, ion_name, ion_id, charge, label):
        # 2D
        __, __, zvals = self._get_driftscope_mobility_data(path)

        dataSplit, xvals, yvals, yvals_RT, yvals_DT = pr_origami.origami_combine_infrared(
            inputData=zvals, threshold=2000, noiseLevel=500,
        )

        mz_y_max = item_information['intensity']
        # Add data to document object
        ion_data = {
            'zvals': dataSplit,
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
            'xylimits': [mz_start, mz_end, mz_y_max],
        }
        # Update document
        self.documentTree.on_update_data(ion_data, ion_name, document, data_type='ion.heatmap.raw')
        self.on_update_document(document, 'ions')

    def on_add_text_2D(self, filename, filepath):

        if filename is None:
            _, filename = get_path_and_fname(filepath, simple=True)

        # Split filename to get path
        path, filename = get_path_and_fname(filepath, simple=True)

        filepath = byte2str(filepath)
        if self.textPanel.onCheckDuplicates(filename):
            return

        # load heatmap information and split into individual components
        array_2D, xvals, yvals = io_text.text_heatmap_open(path=filepath)
        array_1D_mob = np.sum(array_2D, axis=1).T
        array_1D_RT = np.sum(array_2D, axis=0)

        # Try to extract labels from the text file
        if isempty(xvals) or isempty(yvals):
            xvals, yvals = '', ''
            xlabel_start, xlabel_end = '', ''

            msg = 'Missing x/y-axis labels for {}!'.format(filename) + \
                ' Consider adding x/y-axis to your file to obtain full functionality.'
            dlgBox(exceptionTitle='Missing data', exceptionMsg=msg, type='Warning')
        else:
            xlabel_start, xlabel_end = xvals[0], xvals[-1]

        add_dict = {
            'energy_start': xlabel_start,
            'energy_end': xlabel_end,
            'charge': '',
            'color': self.config.customColors[randomIntegerGenerator(0, 15)],
            'colormap': self.config.overlay_cmaps[randomIntegerGenerator(0, len(self.config.overlay_cmaps) - 1)],
            'alpha': self.config.overlay_defaultAlpha,
            'mask': self.config.overlay_defaultMask,
            'label': '',
            'shape': array_2D.shape,
            'document': filename,
        }

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
        self.on_update_document(document, 'document')

        data = {
            'zvals': array_2D,
            'xvals': xvals,
            'xlabels': 'Collision Voltage (V)',
            'yvals': yvals,
            'yvals1D': array_1D_mob,
            'yvalsRT': array_1D_RT,
            'ylabels': 'Drift time (bins)',
            'cmap': self.config.currentCmap,
            'mask': self.config.overlay_defaultMask,
            'alpha': self.config.overlay_defaultAlpha,
            'min_threshold': 0,
            'max_threshold': 1,
            'color': color,
        }
        self.documentTree.on_update_data(data, '', document, data_type='main.heatmap')

        # Update document
        self.view.updateRecentFiles(path={'file_type': 'Text', 'file_path': path})

    def on_add_text_MS(self, path):
        # Update statusbar
        self.on_threading(args=('Loading {}...'.format(path), 4), action='statusbar.update')
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
        # add document
        self.on_update_document(document, 'document')

        data = {'xvals': ms_x, 'yvals': ms_y, 'xlabels': 'm/z (Da)', 'xlimits': xlimits}

        self.documentTree.on_update_data(data, '', document, data_type='main.spectrum')

        # Plot
        name_kwargs = {'document': document.title, 'dataset': 'Mass Spectrum'}
        self.plotsPanel.on_plot_MS(ms_x, ms_y, xlimits=xlimits, **name_kwargs)

        # Update document
        self.view.updateRecentFiles(path={'file_type': 'Text_MS', 'file_path': path})

    def on_update_document(self, document, expand_item='document', expand_item_title=None):

        if expand_item == 'document':
            self.documentTree.add_document(docData=document, expandItem=document)
        elif expand_item == 'ions':
            if expand_item_title is None:
                self.documentTree.add_document(
                    docData=document,
                    expandItem=document.IMS2Dions,
                )
            else:
                self.documentTree.add_document(
                    docData=document,
                    expandItem=document.IMS2Dions[expand_item_title],
                )
        elif expand_item == 'combined_ions':
            if expand_item_title is None:
                self.documentTree.add_document(
                    docData=document,
                    expandItem=document.IMS2DCombIons,
                )
            else:
                self.documentTree.add_document(
                    docData=document,
                    expandItem=document.IMS2DCombIons[expand_item_title],
                )

        elif expand_item == 'processed_ions':
            if expand_item_title is None:
                self.documentTree.add_document(
                    docData=document,
                    expandItem=document.IMS2DionsProcess,
                )
            else:
                self.documentTree.add_document(
                    docData=document,
                    expandItem=document.IMS2DionsProcess[expand_item_title],
                )

        elif expand_item == 'ions_1D':
            if expand_item_title is None:
                self.documentTree.add_document(
                    docData=document,
                    expandItem=document.multipleDT,
                )
            else:
                self.documentTree.add_document(
                    docData=document,
                    expandItem=document.multipleDT[expand_item_title],
                )

        elif expand_item == 'comparison_data':
            if expand_item_title is None:
                self.documentTree.add_document(
                    docData=document,
                    expandItem=document.IMS2DcompData,
                )
            else:
                self.documentTree.add_document(
                    docData=document,
                    expandItem=document.IMS2DcompData[expand_item_title],
                )

        elif expand_item == 'mass_spectra':
            if expand_item_title is None:
                self.documentTree.add_document(
                    docData=document,
                    expandItem=document.multipleMassSpectrum,
                )
            else:
                self.documentTree.add_document(
                    docData=document,
                    expandItem=document.multipleMassSpectrum[expand_item_title],
                )

        elif expand_item == 'overlay':
            if expand_item_title is None:
                self.documentTree.add_document(
                    docData=document,
                    expandItem=document.IMS2DoverlayData,
                )
            else:
                self.documentTree.add_document(
                    docData=document,
                    expandItem=document.IMS2DoverlayData[expand_item_title],
                )
        # just set data
        elif expand_item == 'no_refresh':
            self.documentTree.set_document(
                document_old=self.presenter.documentsDict[document.title],
                document_new=document,
            )

        # update dictionary
        self.presenter.documentsDict[document.title] = document
        self.presenter.currentDoc = document.title

    def extract_from_plot_1D(self, xvalsMin, xvalsMax, yvalsMax, currentView=None, currentDoc=''):
        self.plot_page = self.plotsPanel._get_page_text()

        document = self._on_get_document()
        document_title = document.title

        # Extraction of data when the Interactive document is enabled is not possible
        if self.plot_page in ['RT', 'MS', '1D', '2D'] and document.dataType == 'Type: Interactive':
            args = ('Cannot extract data from Interactive document', 4)
            self.on_threading(args=args, action='statusbar.update')
            return

        # Extract mass spectrum from mobiligram window
        elif self.plot_page == '1D':
            dt_label = self.plotsPanel.plot1D.plot_labels.get('xlabel', 'Drift time (bins)')

            if xvalsMin is None or xvalsMax is None:
                args = ('Your extraction range was outside the window. Please try again', 4)
                self.on_threading(args=args, action='statusbar.update')
                return

            if dt_label == 'Drift time (bins)':
                dtStart = np.ceil(xvalsMin).astype(int)
                dtEnd = np.floor(xvalsMax).astype(int)
            else:
                dtStart = xvalsMin
                dtEnd = xvalsMax

            # Check that values are in correct order
            if dtEnd < dtStart:
                dtEnd, dtStart = dtStart, dtEnd

            self.on_extract_MS_from_mobiligram(dtStart=dtStart, dtEnd=dtEnd, units=dt_label)

        # Extract heatmap from mass spectrum window
        elif self.plot_page == 'MS' or currentView == 'MS':
            if xvalsMin is None or xvalsMax is None:
                self.__update_statusbar('Your extraction range was outside the window. Please try again', 4)
                return

            if document.fileFormat == 'Format: Thermo (.RAW)':
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
                ms[:, 0], ms[:, 1], (mz_start, mz_end),
            )
            color = self.ionPanel.on_check_duplicate_colors(
                self.config.customColors[randomIntegerGenerator(0, 15)],
            )
            color = convertRGB255to1(color)
            colormap = self.config.overlay_cmaps[randomIntegerGenerator(0, len(self.config.overlay_cmaps) - 1)]

            if document.dataType in ['Type: ORIGAMI', 'Type: MANUAL', 'Type: Infrared']:
                self.view.on_toggle_panel(evt=ID_window_ionList, check=True)
                # Check if value already present
                outcome = self.ionPanel.onCheckForDuplicates(
                    mzStart=str(mz_start), mzEnd=str(mz_end),
                )
                if outcome:
                    self.__update_statusbar('Selected range already in the table', 4)
                    if currentView == 'MS':
                        return outcome
                    return

                _add_to_table = {
                    'mz_start': mz_start,
                    'mz_end': mz_end,
                    'charge': charge,
                    'mz_ymax': mz_y_max,
                    'color': convertRGB1to255(color),
                    'colormap': colormap,
                    'alpha': self.config.overlay_defaultAlpha,
                    'mask': self.config.overlay_defaultMask,
                    'document': document_title,
                }
                self.ionPanel.on_add_to_table(_add_to_table, check_color=False)

                if self.config.showRectanges:
                    label = '{};{:.2f}-{:.2f}'.format(document_title, mz_start, mz_end)
                    self.plotsPanel.on_plot_patches(
                        mz_start, 0, (mz_end - mz_start), 100000000000,
                        color=color, alpha=self.config.markerTransparency_1D,
                        label=label,
                        repaint=True,
                    )

                if self.ionPanel.extractAutomatically:
                    self.on_extract_2D_from_mass_range_fcn(None, extract_type='new')

            elif document.dataType == 'Type: Multifield Linear DT':
                self.view.on_toggle_panel(evt=ID_window_multiFieldList, check=True)
                # Check if value already present
                outcome = self.view.panelLinearDT.bottomP.onCheckForDuplicates(
                    mz_start=str(mz_start),
                    mzEnd=str(mz_end),
                )
                if outcome:
                    return
                self.view.panelLinearDT.bottomP.peaklist.Append([
                    mz_start,
                    mz_end,
                    mz_y_max,
                    '',
                    self.presenter.currentDoc,
                ])

                if self.config.showRectanges:
                    self.plotsPanel.on_plot_patches(
                        mz_start, 0, (mz_end - mz_start), 100000000000,
                        color=self.config.annotColor,
                        alpha=self.config.markerTransparency_1D,
                        repaint=True,
                    )

        # # Extract data from calibration window
        # if self.plot_page == "Calibration":
        #     # Check whether the current document is of correct type!
        #     if (document.fileFormat != 'Format: MassLynx (.raw)' or document.dataType != 'Type: CALIBRANT'):
        #         print('Please select the correct document file in document window!')
        #         return
        #     mzVal = np.round((xvalsMax + xvalsMin) / 2, 2)
        #     # prevents extraction if value is below 50. This assumes (wrongly!)
        #     # that the m/z range will never be below 50.
        #     if xvalsMax < 50:
        #         self.SetStatusText('Make sure you are extracting in the MS window.', 3)
        #         return
        #     # Check if value already present
        #     outcome = self.panelCCS.topP.onCheckForDuplicates(mzCentre=str(mzVal))
        #     if outcome:
        #         return
        #     self.view._mgr.GetPane(self.panelCCS).Show()
        #     self.ccsTable.Check(True)
        #     self.view._mgr.Update()
        #     if yvalsMax <= 1:
        #         tD = self.presenter.onAddCalibrant(path=document.path,
        #                                            mzCentre=mzVal,
        #                                            mzStart=np.round(xvalsMin, 2),
        #                                            mzEnd=np.round(xvalsMax, 2),
        #                                            pusherFreq=document.parameters['pusherFreq'],
        #                                            tDout=True)

        #         self.panelCCS.topP.peaklist.Append([document_title,
        #                                             np.round(xvalsMin, 2),
        #                                             np.round(xvalsMax, 2),
        #                                             "", "", "", str(tD)])
        #         if self.config.showRectanges:
        #             self.presenter.addRectMS(xvalsMin, 0, (xvalsMax - xvalsMin), 1.0,
        #                                      color=self.config.annotColor,
        #                                      alpha=(self.config.annotTransparency / 100),
        #                                      repaint=True, plot='CalibrationMS')

        # Extract mass spectrum from chromatogram window - Linear DT files
        elif self.plot_page == 'RT' and document.dataType == 'Type: Multifield Linear DT':
            self.view._mgr.GetPane(self.view.panelLinearDT).Show()
            self.view._mgr.Update()
            xvalsMin = np.ceil(xvalsMin).astype(int)
            xvalsMax = np.floor(xvalsMax).astype(int)
            # Check that values are in correct order
            if xvalsMax < xvalsMin:
                xvalsMax, xvalsMin = xvalsMin, xvalsMax

            # Check if value already present
            outcome = self.view.panelLinearDT.topP.onCheckForDuplicates(
                rtStart=str(xvalsMin),
                rtEnd=str(xvalsMax),
            )
            if outcome:
                return
            xvalDiff = xvalsMax - xvalsMin.astype(int)
            self.view.panelLinearDT.topP.peaklist.Append([
                xvalsMin, xvalsMax,
                xvalDiff, '',
                document_title,
            ])

            self.plotsPanel.on_add_patch(
                xvalsMin, 0, (xvalsMax - xvalsMin), 100000000000,
                color=self.config.annotColor,
                alpha=(self.config.annotTransparency / 100),
                repaint=True, plot='RT',
            )

        # Extract mass spectrum from chromatogram window
        elif self.plot_page == 'RT' and document.dataType != 'Type: Multifield Linear DT':
            rt_label = self.plotsPanel.plotRT.plot_labels.get('xlabel', 'Scans')

            # Get values
            if xvalsMin is None or xvalsMax is None:
                self.__update_statusbar('Extraction range was from outside of the plot area. Please try again', 4)
                return

            if rt_label in ['Collision Voltage (V)']:
                self.__update_statusbar(f'Cannot extract MS data when the x-axis is in {rt_label} format', 4)
                return

            if rt_label == 'Scans':
                xvalsMin = np.ceil(xvalsMin).astype(int)
                xvalsMax = np.floor(xvalsMax).astype(int)

            # Check that values are in correct order
            if xvalsMax < xvalsMin:
                xvalsMax, xvalsMin = xvalsMin, xvalsMax

            # Extract data
            if document.fileFormat == 'Format: Thermo (.RAW)':
                return
            else:
                self.on_extract_MS_from_chromatogram(startScan=xvalsMin, endScan=xvalsMax, units=rt_label)

        else:
            return

    def extract_from_plot_2D(self, dataOut):
        self.plot_page = self.plotsPanel._get_page_text()

        if self.plot_page == 'DT/MS':
            xlabel = self.plotsPanel.plot_DT_vs_MS.plot_labels.get('xlabel', 'm/z')
            ylabel = self.plotsPanel.plot_DT_vs_MS.plot_labels.get('ylabel', 'Drift time (bins)')
        elif self.plot_page == '2D':
            xlabel = self.plotsPanel.plot2D.plot_labels.get('xlabel', 'Scans')
            ylabel = self.plotsPanel.plot2D.plot_labels.get('ylabel', 'Drift time (bins)')

        xmin, xmax, ymin, ymax = dataOut
        if xmin is None or xmax is None or ymin is None or ymax is None:
            self.__update_statusbar('Extraction range was from outside of the plot area. Please try again', 4)
            return

        xmin = np.round(xmin, 2)
        xmax = np.round(xmax, 2)

        if ylabel == 'Drift time (bins)':
            ymin = int(np.round(ymin, 0))
            ymax = int(np.round(ymax, 0))
        elif ylabel in ['Drift time (ms)', 'Arrival time (ms)']:
            ymin, ymax = ymin, ymax
        else:
            return

        if xlabel == 'Scans':
            xmin = np.ceil(xmin).astype(int)
            xmax = np.floor(xmax).astype(int)
        elif xlabel in ['Retention time (min)', 'Time (min)', 'm/z']:
            xmin, xmax = xmin, xmax
        else:
            return

        # Reverse values if they are in the wrong order
        xmin, xmax = check_value_order(xmin, xmax)
        ymin, ymax = check_value_order(ymin, ymax)

        # Extract data
        if self.plot_page == 'DT/MS':
            self.on_extract_RT_from_mzdt(xmin, xmax, ymin, ymax, units_x=xlabel, units_y=ylabel)
        elif self.plot_page == '2D':
            self.on_extract_MS_from_heatmap(xmin, xmax, ymin, ymax, units_x=xlabel, units_y=ylabel)

    def on_open_text_2D_fcn(self, evt):
        if not self.config.threading:
            self.on_open_single_text_2D()
        else:
            self.on_threading(action='load.text.heatmap', args=())

    def on_open_single_text_2D(self):
        dlg = wx.FileDialog(
            self.view, 'Choose a text file:', wildcard='*.txt; *.csv',
            style=wx.FD_DEFAULT_STYLE | wx.FD_CHANGE_DIR,
        )
        if dlg.ShowModal() == wx.ID_OK:
            filepath = dlg.GetPath()
            __, filename = get_path_and_fname(filepath, simple=True)
            self.on_add_text_2D(filename, filepath)
        dlg.Destroy()

    def on_open_multiple_text_2D_fcn(self, evt):
        self.view.on_toggle_panel(evt='text', check=True)

        wildcard = 'Text files with axis labels (*.txt, *.csv)| *.txt;*.csv'
        dlg = wx.FileDialog(
            self.view, 'Choose a text file. Make sure files contain x- and y-axis labels!',
            wildcard=wildcard, style=wx.FD_MULTIPLE | wx.FD_CHANGE_DIR,
        )
        if dlg.ShowModal() == wx.ID_OK:
            pathlist = dlg.GetPaths()
            filenames = dlg.GetFilenames()

            if not self.config.threading:
                self.on_open_multiple_text_2D(pathlist, filenames)
            else:
                self.on_threading(action='load.multiple.text.heatmap', args=(pathlist, filenames))
        dlg.Destroy()

    def on_open_multiple_text_2D(self, pathlist, filenames):
        for filepath, filename in zip(pathlist, filenames):
            self.on_add_text_2D(filename, filepath)

    def on_open_multiple_MassLynx_raw_fcn(self, evt):

        if not check_path_exists(self.config.lastDir):
            self.config.lastDir = os.getcwd()

        dlg = DialogMultiDirectoryPicker(
            self.view,
            title='Choose Waters (.raw) files to open...',
            default_path=self.config.lastDir,
        )

        if dlg.ShowModal() == 'ok':  # wx.ID_OK:
            pathlist = dlg.GetPaths()
            data_type = 'Type: ORIGAMI'
            for path in pathlist:
                if not check_waters_path(path):
                    msg = "The path ({}) you've selected does not end with .raw"
                    dlgBox(
                        exceptionTitle='Please load MassLynx (.raw) file',
                        exceptionMsg=msg,
                        type='Error',
                    )
                    return

                if not self.config.threading:
                    self.on_open_single_MassLynx_raw(path, data_type)
                else:
                    self.on_threading(action='load.raw.masslynx', args=(path, data_type))

    def on_open_MassLynx_raw_fcn(self, evt):

        # Reset arrays
        dlg = wx.DirDialog(
            self.view, 'Choose a MassLynx (.raw) file',
            style=wx.DD_DEFAULT_STYLE,
        )

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
                dlgBox(
                    exceptionTitle='Please load MassLynx (.raw) file',
                    exceptionMsg=msg,
                    type='Error',
                )
                return

            if not self.config.threading:
                self.on_open_single_MassLynx_raw(path, data_type)
            else:
                self.on_threading(action='load.raw.masslynx', args=(path, data_type))

        dlg.Destroy()

    def on_open_single_MassLynx_raw(self, path, data_type):
        """ Load data = threaded """
        tstart = ttime()
        self.on_threading(args=('Loading {}...'.format(path), 4), action='statusbar.update')
        __, document_title = get_path_and_fname(path, simple=True)

        # Get experimental parameters
        parameters = self.config.get_waters_inf_data(path)
        fileInfo = self.config.get_waters_header_data(path)
        xlimits = [parameters['startMS'], parameters['endMS']]
        reader = io_waters_raw_api.WatersRawReader(path)

        tstart_extraction = ttime()
        ms_x, ms_y = self._get_waters_api_spectrum_data(reader)
        self.__update_statusbar(f'Extracted mass spectrum in {ttime()-tstart_extraction:.4f}', 4)

        tstart_extraction = ttime()
        xvals_RT, yvals_RT = reader.get_TIC(0)
        xvals_RT = np.arange(1, len(xvals_RT) + 1)
        self.__update_statusbar(f'Extracted chromatogram in {ttime()-tstart_extraction:.4f}', 4)

        if reader.n_functions == 1:
            data_type = 'Type: MS'

        if data_type != 'Type: MS' and reader.n_functions > 1:

            # DT
            tstart_extraction = ttime()
            xvals_DT, yvals_DT = reader.get_TIC(1)
            xvals_DT = np.arange(1, len(xvals_DT) + 1)
            self.__update_statusbar(f'Extracted mobiligram in {ttime()-tstart_extraction:.4f}', 4)

            # 2D
            tstart_extraction = ttime()
            xvals, yvals, zvals = self._get_driftscope_mobility_data(path)
            self.__update_statusbar(f'Extracted heatmap in {ttime()-tstart_extraction:.4f}', 4)

            # Plot MZ vs DT
            if self.config.showMZDT:
                tstart_extraction = ttime()
                xvals_MSDT, yvals_MSDT, zvals_MSDT = self._get_driftscope_mobility_vs_spectrum_data(
                    path, parameters['startMS'], parameters['endMS'],
                )
                self.__update_statusbar(f'Extracted DT/MS heatmap in {ttime()-tstart_extraction:.4f}', 4)
                # Plot
                xvals_MSDT, zvals_MSDT = self.data_processing.downsample_array(xvals_MSDT, zvals_MSDT)
                self.plotsPanel.on_plot_MSDT(zvals_MSDT, xvals_MSDT, yvals_MSDT, 'm/z', 'Drift time (bins)')

            # Update status bar with MS range
            self.view.SetStatusText('{}-{}'.format(parameters['startMS'], parameters['endMS']), 1)
            self.view.SetStatusText('MSMS: {}'.format(parameters['setMS']), 2)

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
        document.file_reader = {'data_reader': reader}

        # add mass spectrum data
        document.gotMS = True
        document.massSpectrum = {
            'xvals': ms_x,
            'yvals': ms_y,
            'xlabels': 'm/z (Da)',
            'xlimits': xlimits,
        }
        name_kwargs = {'document': document_title, 'dataset': 'Mass Spectrum'}
        self.plotsPanel.on_plot_MS(ms_x, ms_y, xlimits=xlimits, **name_kwargs)

        # add chromatogram data
        document.got1RT = True
        document.RT = {
            'xvals': xvals_RT,
            'yvals': yvals_RT,
            'xlabels': 'Scans',
        }
        self.plotsPanel.on_plot_RT(xvals_RT, yvals_RT, 'Scans')

        if data_type != 'Type: MS':
            # add mobiligram data
            document.got1DT = True
            document.DT = {
                'xvals': xvals_DT,
                'yvals': yvals_DT,
                'xlabels': 'Drift time (bins)',
                'ylabels': 'Intensity',
            }
            self.plotsPanel.on_plot_1D(xvals_DT, yvals_DT, 'Drift time (bins)')

            # add 2D mobiligram data
            document.got2DIMS = True
            document.IMS2D = {
                'zvals': zvals,
                'xvals': xvals,
                'xlabels': 'Scans',
                'yvals': yvals,
                'yvals1D': yvals_DT,
                'ylabels': 'Drift time (bins)',
                'cmap': self.config.currentCmap,
                'charge': 1,
            }
            self.plotsPanel.on_plot_2D_data(data=[zvals, xvals, 'Scans', yvals, 'Drift time (bins)'])

            # add DT/MS data
            if self.config.showMZDT:
                document.gotDTMZ = True
                document.DTMZ = {
                    'zvals': zvals_MSDT,
                    'xvals': xvals_MSDT,
                    'yvals': yvals_MSDT,
                    'xlabels': 'm/z',
                    'ylabels': 'Drift time (bins)',
                    'cmap': self.config.currentCmap,
                }

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
        self.on_threading(
            args=('Opened file in {:.4f} seconds'.format(ttime() - tstart), 4),
            action='statusbar.update',
        )

    def on_open_single_text_MS_fcn(self, evt):
        wildcard = 'Text file (*.txt, *.csv, *.tab)| *.txt;*.csv;*.tab'
        dlg = wx.FileDialog(
            self.view, 'Choose MS text file...',
            wildcard=wildcard,
            style=wx.FD_DEFAULT_STYLE | wx.FD_CHANGE_DIR | wx.FD_MULTIPLE,
        )
        if dlg.ShowModal() == wx.ID_OK:
            pathlist = dlg.GetPaths()
            for path in pathlist:
                if not self.config.threading:
                    self.on_add_text_MS(path)
                else:
                    self.on_threading(action='load.text.spectrum', args=(path,))

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
                        logger.warning('Failed to convert mass range to dtype: float')
            data = np.array(data)
            ms_x = data[:, 0]
            ms_y = data[:, 1]
            xlimits = get_min_max(ms_x)

            # Add data to document
            dlg = wx.FileDialog(
                self.view, 'Please select name and directory for the MS document...',
                '', '', '', wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
            )
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
                document.fileFormat = 'Format: Text ({})'.format('Clipboard')
                document.gotMS = True
                document.massSpectrum = {
                    'xvals': ms_x,
                    'yvals': ms_y,
                    'xlabels': 'm/z (Da)',
                    'xlimits': xlimits,
                }

                # Plot
                name_kwargs = {'document': document.title, 'dataset': 'Mass Spectrum'}
                self.plotsPanel.on_plot_MS(ms_x, ms_y, xlimits=xlimits, **name_kwargs)

                # Update document
                self.on_update_document(document, 'document')
        except Exception:
            logger.warning('Failed to get spectrum from the clipboard')
            return

    def on_open_MassLynx_raw_MS_only_fcn(self, evt):

        dlg = wx.DirDialog(
            self.view, 'Choose a MassLynx file:',
            style=wx.DD_DEFAULT_STYLE,
        )

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()

            if not check_waters_path(path):
                msg = "The path ({}) you've selected does not end with .raw"
                dlgBox(
                    exceptionTitle='Please load MassLynx (.raw) file',
                    exceptionMsg=msg,
                    type='Error',
                )
                return

            if not self.config.threading:
                self.on_open_MassLynx_raw_MS_only(path)
            else:
                self.on_threading(action='load.raw.masslynx.ms_only', args=(path,))

        dlg.Destroy()

    def on_open_MassLynx_raw_MS_only(self, path):
        """ open MS file (without IMS) """

        # Update statusbar
        self.on_threading(args=('Loading {}...'.format(path), 4), action='statusbar.update')
        __, document_title = get_path_and_fname(path, simple=True)

        # Get experimental parameters
        parameters = self.config.get_waters_inf_data(path)
        xlimits = [parameters['startMS'], parameters['endMS']]

        reader = io_waters_raw_api.WatersRawReader(path)

        # get mass spectrum
        ms_x, ms_y = self._get_waters_api_spectrum_data(reader)

        # get chromatogram
        rt_x, rt_y = reader.get_TIC(0)
        rt_x = np.arange(1, len(rt_x) + 1)

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
        document.massSpectrum = {
            'xvals': ms_x,
            'yvals': ms_y,
            'xlabels': 'm/z (Da)',
            'xlimits': xlimits,
        }
        document.got1RT = True
        document.RT = {
            'xvals': rt_x,
            'yvals': rt_y,
            'xlabels': 'Scans',
        }

        # Plot
        name_kwargs = {'document': document.title, 'dataset': 'Mass Spectrum'}
        self.plotsPanel.on_plot_MS(ms_x, ms_y, xlimits=xlimits, **name_kwargs)
        self.plotsPanel.on_plot_RT(rt_x, rt_y, 'Scans')

        # Update document
        self.view.updateRecentFiles(path={'file_type': 'MassLynx', 'file_path': path})
        self.on_update_document(document, 'document')

    def on_extract_2D_from_mass_range_fcn(self, evt, extract_type='all'):
        """
        Extract 2D array for each m/z range specified in the table
        """
        if evt is None:
            evt = extract_type
        else:
            evt = 'all'

        if not self.config.threading:
            self.on_extract_2D_from_mass_range(evt)
        else:
            args = (evt,)
            self.on_threading(action='extract.heatmap', args=args)

    def on_extract_2D_from_mass_range(self, extract_type='all'):
        """ extract multiple ions = threaded """

        # first check how many items need extracting
        n_items = self.ionList.GetItemCount()

        n_extracted = 0
        for ion_id in range(self.ionList.GetItemCount()):
            # Extract ion name
            item_information = self.ionPanel.OnGetItemInformation(itemID=ion_id)
            document_title = item_information['document']

            # Check if the ion has been assigned a filename
            if document_title == '':
                self.__update_statusbar('File name column was empty. Using the current document name instead', 4)
                document = self._on_get_document()
                document_title = document.title
                self.ionPanel.on_update_value_in_peaklist(ion_id, 'document', document_title)

            document = self._on_get_document(document_title)
            path = document.path
            path = check_waters_path(path)
            if not check_path_exists(path):
                msg = 'File with {} path no longer exists'.format(path)
                dlgBox('File no longer exists', msg, type='Error')
                return

            # Extract information from the table
            mz_start = item_information['start']
            mz_end = item_information['end']
            mz_y_max = item_information['intensity']
            label = item_information['label']
            charge = item_information['charge']

            if charge is None:
                charge = '1'

            # Create range name
            ion_name = item_information['ionName']

            # Check that the mzStart/mzEnd are above the acquire MZ value
            if mz_start < min(document.massSpectrum['xvals']):
                self.ionList.ToggleItem(index=ion_id)
                msg = 'Ion: {} was below the minimum value in the mass spectrum.'.format(ion_name) + \
                    ' Consider removing it from the list'
                self.__update_statusbar(msg, 4)
                continue

            # Check whether this ion was already extracted
            if extract_type == 'new' and document.gotExtractedIons:
                if ion_name in document.IMS2Dions:
                    self.__update_statusbar('Data was already extracted for the : {} ion'.format(ion_name), 4)
                    n_items -= 1
                    continue

            elif extract_type == 'new' and document.gotCombinedExtractedIons:
                if ion_name in document.IMS2DCombIons:
                    self.__update_statusbar('Data was already extracted for the : {} ion'.format(ion_name), 4)
                    n_items -= 1
                    continue

            # Extract selected ions
            if extract_type == 'selected' and not self.ionList.IsChecked(index=ion_id):
                n_items -= 1
                continue

            n_extracted += 1
            if document.dataType == 'Type: ORIGAMI':
                self.on_add_ion_ORIGAMI(
                    item_information, document, path, mz_start, mz_end, mz_y_max, ion_name, label, charge,
                )

            # Check if manual dataset
            elif document.dataType == 'Type: MANUAL':
                self.on_add_ion_MANUAL(
                    item_information, document, mz_start, mz_end, mz_y_max, ion_name, ion_id, charge, label,
                )

            elif document.dataType == 'Type: Infrared':
                self.on_add_ion_IR(
                    item_information, document, path, mz_start, mz_end, mz_y_max, ion_name, ion_id, charge, label,
                )
            else:
                return
            msg = 'Extracted: {}/{}'.format((n_extracted), n_items)
            self.__update_statusbar(msg, 4)

    def on_open_multiple_ML_files_fcn(self, open_type, pathlist=[]):

        if not check_path_exists(self.config.lastDir):
            self.config.lastDir = os.getcwd()

        dlg = DialogMultiDirectoryPicker(
            self.view,
            title='Choose Waters (.raw) files to open...',
            default_path=self.config.lastDir,
        )
#
        if dlg.ShowModal() == 'ok':
            pathlist = dlg.GetPaths()

        if len(pathlist) == 0:
            self.__update_statusbar('Please select at least one file in order to continue.', 4)
            return

        # update lastdir
        self.config.lastDir = get_base_path(pathlist[0])

        if open_type == 'multiple_files_add':
            document = self._get_document_of_type('Type: MANUAL')
        elif open_type == 'multiple_files_new_document':
            document = self.__create_new_document()

        if document is None:
            logger.warning('Document was not selected.')
            return

        # setup parameters
        document.dataType = 'Type: MANUAL'
        document.fileFormat = 'Format: MassLynx (.raw)'

        if not self.config.threading:
            self.on_open_multiple_ML_files(document, open_type, pathlist)
        else:
            self.on_threading(action='load.multiple.raw.masslynx', args=(document, open_type, pathlist))

    def on_open_multiple_ML_files(self, document, open_type, pathlist=[]):
        # http://stackoverflow.com/questions/1252481/sort-dictionary-by-another-dictionary
        # http://stackoverflow.com/questions/22520739/python-sort-a-dict-by-values-producing-a-list-how-to-sort-this-from-largest-to

        tstart = ttime()

        enumerate_start = 0
        if open_type == 'multiple_files_add':
            enumerate_start = len(document.multipleMassSpectrum)

        data_was_added = False
        for i, file_path in enumerate(pathlist, start=enumerate_start):
            path = check_waters_path(file_path)
            if not check_path_exists(path):
                logger.warning('File with path: {} does not exist'.format(path))
                continue

            __, file_name = os.path.split(path)

            add_dict = {'filename': file_name, 'document': document.title}
            # check if item already exists
            if self.filesPanel._check_item_in_table(add_dict):
                logger.info(
                    'Item {}:{} is already present in the document'.format(
                        add_dict['document'], add_dict['filename'],
                    ),
                )
                continue

            # add data to document
            parameters = self.config.get_waters_inf_data(path)
            xlimits = [parameters['startMS'], parameters['endMS']]
            ms_x, ms_y = self._get_driftscope_spectrum_data(path)
            dt_x, dt_y = self._get_driftscope_mobiligram_data(path)
            try:
                color = self.config.customColors[i]
            except KeyError:
                color = randomColorGenerator(return_as_255=True)

            color = convertRGB255to1(
                self.filesPanel.on_check_duplicate_colors(color, document_name=document.title),
            )
            label = os.path.splitext(file_name)[0]

            add_dict.update({
                'variable': parameters['trapCE'],
                'label': label,
                'color': color,
            })

            self.filesPanel.on_add_to_table(add_dict, check_color=False)

            data = {
                'trap': parameters['trapCE'],
                'xvals': ms_x,
                'yvals': ms_y,
                'ims1D': dt_y,
                'ims1DX': dt_x,
                'xlabel': 'Drift time (bins)',
                'xlabels': 'm/z (Da)',
                'path': path,
                'color': color,
                'parameters': parameters,
                'xlimits': xlimits,
            }

            self.documentTree.on_update_data(data, file_name, document, data_type='extracted.spectrum')
            data_was_added = True

        # check if any data was added to the document
        if not data_was_added:
            return

        kwargs = {
            'auto_range': False,
            'mz_min': self.config.ms_mzStart,
            'mz_max': self.config.ms_mzEnd,
            'mz_bin': self.config.ms_mzBinSize,
            'linearization_mode': self.config.ms_linearization_mode,
        }
        msg = 'Linearization method: {} | min: {} | max: {} | window: {} | auto-range: {}'.format(
            self.config.ms_linearization_mode,
            self.config.ms_mzStart,
            self.config.ms_mzEnd,
            self.config.ms_mzBinSize,
            self.config.ms_auto_range,
        )
        self.__update_statusbar(msg, 4)

        # check the min/max values in the mass spectrum
        if self.config.ms_auto_range:
            mzStart, mzEnd = pr_spectra.check_mass_range(ms_dict=document.multipleMassSpectrum)
            self.config.ms_mzStart = mzStart
            self.config.ms_mzEnd = mzEnd
            kwargs.update(mz_min=mzStart, mz_max=mzEnd)

        msFilenames = ['m/z']
        for counter, key in enumerate(document.multipleMassSpectrum):
            msFilenames.append(key)

            if counter == 0:
                ms_x, ms_y = pr_spectra.linearize_data(
                    document.multipleMassSpectrum[key]['xvals'],
                    document.multipleMassSpectrum[key]['yvals'],
                    **kwargs
                )
                ms_y_sum = ms_y
            else:
                ms_x, ms_y = pr_spectra.linearize_data(
                    document.multipleMassSpectrum[key]['xvals'],
                    document.multipleMassSpectrum[key]['yvals'],
                    **kwargs
                )
                ms_y_sum += ms_y

        xlimits = [parameters['startMS'], parameters['endMS']]
        data = {
            'xvals': ms_x,
            'yvals': ms_y_sum,
            'xlabels': 'm/z (Da)',
            'xlimits': xlimits,
        }
        self.documentTree.on_update_data(data, '', document, data_type='main.spectrum')
        # Plot
        name_kwargs = {'document': document.title, 'dataset': 'Mass Spectrum'}
        self.plotsPanel.on_plot_MS(ms_x, ms_y_sum, xlimits=xlimits, **name_kwargs)

        # Add info to document
        document.parameters = parameters
        self.on_update_document(document, 'no_refresh')

        # Show panel
        self.view.on_toggle_panel(evt=ID_window_multipleMLList, check=True)
        self.filesList.on_remove_duplicates()

        # Update status bar with MS range
        self.__update_statusbar(
            'Data extraction took {:.4f} seconds for {} files.'.format(
                ttime() - tstart, i + 1,
            ), 4,
        )
        self.view.SetStatusText('{}-{}'.format(parameters['startMS'], parameters['endMS']), 1)
        self.view.SetStatusText('MSMS: {}'.format(parameters['setMS']), 2)

    def on_extract_RT_from_mzdt(
        self, mzStart, mzEnd, dtStart, dtEnd, units_x='m/z',
        units_y='Drift time (bins)',
    ):
        """Function to extract RT data for specified MZ/DT region """

        document = self._on_get_document()
        # convert from miliseconds to bins
        if units_y in ['Drift time (ms)', 'Arrival time (ms)']:
            pusherFreq = document.parameters.get('pusherFreq', 1000)
            dtStart = np.ceil((dtStart / pusherFreq) * 1000).astype(int)
            dtEnd = np.ceil((dtEnd / pusherFreq) * 1000).astype(int)

        # Load data
        extract_kwargs = {'return_data': True, 'normalize': False}
        rtDataX, rtDataY = io_waters.driftscope_extract_RT(
            path=document.path,
            driftscope_path=self.config.driftscopePath,
            mz_start=mzStart, mz_end=mzEnd,
            dt_start=dtStart, dt_end=dtEnd,
            **extract_kwargs
        )
        self.plotsPanel.on_plot_RT(rtDataX, rtDataY, 'Scans')

        ion_name = f'Ion: {mzStart:.2f}-{mzEnd:.2f} | Drift time: {dtStart:.2f}-{dtEnd:.2f}'
        ion_data = {'xvals': rtDataX, 'yvals': rtDataY, 'xlabels': 'Scans'}

        msg = f'Extracted RT data for m/z: {mzStart}-{mzEnd} | dt: {dtStart}-{dtEnd}'
        self.__update_statusbar(msg, 3)

        # Update document
        self.documentTree.on_update_data(ion_data, ion_name, document, data_type='extracted.chromatogram')

    def on_extract_MS_from_mobiligram(self, dtStart=None, dtEnd=None, evt=None, units='Drift time (bins)'):
        document = self._on_get_document()

        # convert from miliseconds to bins
        if units in ['Drift time (ms)', 'Arrival time (ms)']:
            pusherFreq = document.parameters.get('pusherFreq', 1000)
            dtStart = np.ceil((dtStart / pusherFreq) * 1000).astype(int)
            dtEnd = np.ceil((dtEnd / pusherFreq) * 1000).astype(int)

        # Extract data
        extract_kwargs = {'return_data': True}
        msX, msY = io_waters.driftscope_extract_MS(
            path=document.path,
            driftscope_path=self.config.driftscopePath,
            dt_start=dtStart, dt_end=dtEnd,
            **extract_kwargs
        )
        xlimits = [document.parameters['startMS'], document.parameters['endMS']]

        # Add data to dictionary
        ion_name = 'Drift time: {}-{}'.format(dtStart, dtEnd)

        ion_data = {
            'xvals': msX, 'yvals': msY,
            'range': [dtStart, dtEnd],
            'xlabels': 'm/z (Da)',
            'xlimits': xlimits,
        }

        # Plot MS
        name_kwargs = {'document': document.title, 'dataset': ion_name}
        self.plotsPanel.on_plot_MS(msX, msY, xlimits=xlimits, show_in_window='1D', **name_kwargs)
        # Update document
        self.documentTree.on_update_data(ion_data, ion_name, document, data_type='extracted.spectrum')

    def on_extract_MS_from_chromatogram(self, startScan=None, endScan=None, units='Scans'):
        """ Function to extract MS data for specified RT region """

        document = self._on_get_document()

        try:
            scantime = document.parameters['scanTime']
        except Exception:
            scantime = None

        try:
            xlimits = [document.parameters['startMS'], document.parameters['endMS']]
        except Exception:
            try:
                xlimits = [np.min(document.massSpectrum['xvals']), np.max(document.massSpectrum['xvals'])]
            except Exception:
                pass
            xlimits = None

        if scantime is not None:
            if units in ['Time (min)', 'Retention time (min)']:
                startScan = np.ceil((startScan / scantime) * 60).astype(int)
                endScan = np.ceil((endScan / scantime) * 60).astype(int)

        if startScan != endScan:
            scan_list = np.arange(startScan, endScan)
        else:
            scan_list = [startScan]

        reader = self._get_waters_api_reader(document)
        kwargs = {'scan_list': scan_list}
        mz_x, mz_y = self._get_waters_api_spectrum_data(reader, **kwargs)

        # Add data to dictionary
        spectrum_name = 'Scans: {}-{}'.format(startScan, endScan)

        spectrum_data = {
            'xvals': mz_x, 'yvals': mz_y, 'range': [startScan, endScan], 'xlabels': 'm/z (Da)',
            'xlimits': xlimits,
        }
        document.file_reader = {'data_reader': reader}

        self.documentTree.on_update_data(spectrum_data, spectrum_name, document, data_type='extracted.spectrum')
        # Plot MS
        name_kwargs = {'document': document.title, 'dataset': spectrum_name}
        self.plotsPanel.on_plot_MS(mz_x, mz_y, xlimits=xlimits, show_in_window='RT', **name_kwargs)
        # Set status
        msg = f'Extracted MS data for rt: {startScan}-{endScan}'
        self.__update_statusbar(msg, 3)

    def on_extract_MS_from_heatmap(
        self, startScan=None, endScan=None, dtStart=None,
        dtEnd=None, units_x='Scans', units_y='Drift time (bins)',
    ):
        """ Function to extract MS data for specified DT/MS region """

        document = self._on_get_document()

        try:
            scanTime = document.parameters['scanTime']
        except Exception:
            scanTime = None

        try:
            pusherFreq = document.parameters['pusherFreq']
        except Exception:
            pusherFreq = None

        try:
            xlimits = [document.parameters['startMS'], document.parameters['endMS']]
        except Exception:
            try:
                xlimits = [np.min(document.massSpectrum['xvals']), np.max(document.massSpectrum['xvals'])]
            except Exception:
                return

        if units_x == 'Scans':
            if scanTime is None:
                return
            rtStart = round(startScan * (scanTime / 60), 2)
            rtEnd = round(endScan * (scanTime / 60), 2)
        elif units_x in ['Time (min)', 'Retention time (min)']:
            rtStart, rtEnd = startScan, endScan
            if scanTime is None:
                return
            startScan = np.ceil((startScan / scanTime) * 60).astype(int)
            endScan = np.ceil((endScan / scanTime) * 60).astype(int)

        if units_y in ['Drift time (ms)', 'Arrival time (ms)']:
            if pusherFreq is None:
                return
            dtStart = np.ceil((dtStart / pusherFreq) * 1000).astype(int)
            dtEnd = np.ceil((dtEnd / pusherFreq) * 1000).astype(int)

        # Mass spectra
        try:
            extract_kwargs = {'return_data': True}
            msX, msY = io_waters.driftscope_extract_MS(
                path=document.path,
                driftscope_path=self.config.driftscopePath,
                rt_start=rtStart, rt_end=rtEnd,
                dt_start=dtStart, dt_end=dtEnd,
                **extract_kwargs
            )
            if xlimits is None:
                xlimits = [np.min(msX), np.max(msX)]
        except (IOError, ValueError):
            return

        # Add data to dictionary
        ion_name = 'Scans: {}-{} | Drift time: {}-{}'.format(
            startScan, endScan,
            dtStart, dtEnd,
        )

        ion_data = {
            'xvals': msX,
            'yvals': msY,
            'range': [startScan, endScan],
            'xlabels': 'm/z (Da)',
            'xlimits': xlimits,
        }

        self.documentTree.on_update_data(ion_data, ion_name, document, data_type='extracted.spectrum')
        # Plot MS
        name_kwargs = {'document': document.title, 'dataset': ion_name}
        self.plotsPanel.on_plot_MS(msX, msY, xlimits=xlimits, **name_kwargs)
        # Set status
        msg = f'Extracted MS data for rt: {startScan}-{endScan}'
        self.__update_statusbar(msg, 3)

    def on_save_all_documents_fcn(self, evt):
        if self.config.threading:
            self.on_threading(action='save.all.document', args=())
        else:
            self.on_save_all_documents()

    def on_save_all_documents(self):

        for document_title in self.presenter.documentsDict:
            self.on_save_document(document_title, False)

    def on_save_document_fcn(self, document_title, save_as=True):

        if self.config.threading:
            self.on_threading(action='save.document', args=(document_title, save_as))
        else:
            self.on_save_document(document_title, save_as)

    def on_save_document(self, document_title, save_as, **kwargs):
        """
        Save document to file.
        ---
        document_title: str
            name of the document to be retrieved from the document dictionary
        save_as: bool
            check whether document should be saved as (select new path/name) or
            as is
        """
        document = self._on_get_document(document_title)
        document_path = document.path
        document_title = document.title

        if document_title not in document_path:
            document_path = document_path + '\\' + document_title

        try:
            full_path, __, fname, is_path = self.get_path_and_fname(
                document_path,
            )
        except Exception:
            full_path = None
            fname = byte2str(document.title.split('.'))
            is_path = False

        if is_path:
            document_path = full_path + '\\' + document_title

        if not save_as and is_path:
            save_path = full_path
            if not save_path.endswith('.pickle'):
                save_path = save_path + '.pickle'
        else:
            dlg = wx.FileDialog(
                self.view, 'Please select a name for the file',
                '', '',
                wildcard='ORIGAMI Document File (*.pickle)|*.pickle',
                style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
            )
            dlg.CentreOnParent()

            try:
                if full_path is not None and is_path:
                    dlg.SetPath(full_path)
                else:
                    if isinstance(fname, list) and len(fname) == 1:
                        fname = fname[0]
                    dlg.SetFilename(fname)
            except Exception as e:
                logger.warning(e)

            if dlg.ShowModal() == wx.ID_OK:
                save_path = dlg.GetPath()
            else:
                return

        self.view.SetStatusText('Saving data, please wait...', number=4)

        # update filepath
        path, _ = os.path.splitext(save_path)
        document.path = path

        # save document
        save_py_object(save_path, document)
        # update recent files
        self.view.updateRecentFiles(
            path={'file_type': 'pickle', 'file_path': save_path},
        )

    def on_open_document_fcn(self, evt, file_path=None):

        dlg = None
        if file_path is None:
            wildcard = \
                'All accepted formats |*.pkl;*.pickle|' + \
                'ORIGAMI document file (*.pkl; *.pickle)|*.pkl;*.pickle'

            dlg = wx.FileDialog(
                self.view, 'Open Document File',
                wildcard=wildcard,
                style=wx.FD_MULTIPLE | wx.FD_CHANGE_DIR,
            )

        if hasattr(dlg, 'ShowModal'):
            if dlg.ShowModal() == wx.ID_OK:
                file_path = dlg.GetPaths()

        if self.config.threading:
            self.on_threading(action='load.document', args=(file_path,))
        else:
            self.on_open_document(file_path)

    def on_open_document(self, file_paths):

        if file_paths is None:
            return

        if isinstance(file_paths, str):
            file_path = [file_paths]

        for file_path in file_paths:
            try:
                self._load_document_data(document=open_py_object(filename=file_path))
            except (ValueError, AttributeError, TypeError, IOError) as e:
                dlgBox(exceptionTitle='Failed to load document on load.', exceptionMsg=str(e), type='Error')
                return

        self.view.updateRecentFiles(path={'file_type': 'pickle', 'file_path': file_path})

    def _load_document_data(self, document=None):
        """
        Function to iterate over the whole document to ensure complete loading of the data
        Once document is re-loaded, data and GUI are restored to appropriate format
        """
        if document is not None:
            document_title = document.title
            self.presenter.documentsDict[document_title] = document

            if document.fileFormat == 'Format: Waters (.raw)':
                try:
                    reader = self._get_waters_api_reader(document)
                    document.file_reader = {'data_reader': reader}
                except Exception as err:
                    logger.warning(f'When trying to create file error an error occurer. Error msg: {err}')

            if document.gotMS:
                self.__update_statusbar('Loaded mass spectra', 4)
                msX = document.massSpectrum['xvals']
                msY = document.massSpectrum['yvals']
                color = document.lineColour
                try:
                    xlimits = document.massSpectrum['xlimits']
                except KeyError:
                    xlimits = [document.parameters['startMS'], document.parameters['endMS']]
                if document.dataType != 'Type: CALIBRANT':
                    name_kwargs = {'document': document.title, 'dataset': 'Mass Spectrum'}
                    self.plotsPanel.on_plot_MS(msX, msY, xlimits=xlimits, **name_kwargs)
                else:
                    self.onPlotMSDTCalibration(
                        msX=msX, msY=msY, color=color, xlimits=xlimits,
                        plotType='MS',
                    )
            if document.got1DT:
                self.__update_statusbar('Loaded mobiligrams (1D)', 4)
                dtX = document.DT['xvals']
                dtY = document.DT['yvals']
                xlabel = document.DT['xlabels']
                color = document.lineColour
                if document.dataType != 'Type: CALIBRANT':
                    self.plotsPanel.on_plot_1D(dtX, dtY, xlabel)
                else:
                    self.onPlotMSDTCalibration(
                        dtX=dtX, dtY=dtY, color=color,
                        xlabelDT=xlabel, plotType='1DT',
                    )
            if document.got1RT:
                self.__update_statusbar('Loaded chromatograms', 4)
                rtX = document.RT['xvals']
                rtY = document.RT['yvals']
                xlabel = document.RT['xlabels']
                color = document.lineColour
                self.plotsPanel.on_plot_RT(rtX, rtY, xlabel)

            if document.got2DIMS:
                data = document.IMS2D
                zvals = data['zvals']
                xvals = data['xvals']

                if document.dataType == 'Type: 2D IM-MS':
                    if self.textPanel.onCheckDuplicates(document_title):
                        return

                    add_dict = {
                        'energy_start': xvals[0],
                        'energy_end': xvals[-1],
                        'charge': '',
                        'color': data.get(
                            'color',
                            self.config.customColors[randomIntegerGenerator(0, 15)],
                        ),
                        'colormap': data.get(
                            'cmap', self.config.overlay_cmaps[
                                randomIntegerGenerator(
                                    0, len(self.config.overlay_cmaps) - 1,
                                )
                            ],
                        ),
                        'alpha': data.get('alpha', self.config.overlay_defaultAlpha),
                        'mask': data.get('mask', self.config.overlay_defaultMask),
                        'label': data.get('label', ''),
                        'shape': zvals.shape,
                        'document': document_title,
                    }

                    self.textPanel.on_add_to_table(add_dict, return_color=False)

                self.__update_statusbar('Loaded mobiligrams (2D)', 4)

                self.plotsPanel.on_plot_2D_data(
                    data=[
                        zvals,
                        xvals,
                        data['xlabels'],
                        data['yvals'],
                        data['ylabels'],
                    ],
                )

            # Restore ion list
            if (
                any([
                    document.gotExtractedIons, document.got2DprocessIons,
                    document.gotCombinedExtractedIonsRT, document.gotCombinedExtractedIons,
                ])
                and document.dataType != 'Type: Interactive'
            ):
                if len(document.IMS2DCombIons) > 0:
                    dataset = document.IMS2DCombIons
                elif len(document.IMS2DCombIons) == 0:
                    dataset = document.IMS2Dions
                elif len(document.IMS2Dions) == 0:
                    dataset = {}

                for _, key in enumerate(dataset):
                    mz_split = re.split('-| |,|', key)
                    mz_start = mz_split[0]
                    mz_end = mz_split[1]
                    charge = dataset[key].get('charge', '')
                    label = dataset[key].get('label', '')
                    alpha = dataset[key].get('alpha', 0.5)
                    mask = dataset[key].get('mask', 0.25)
                    colormap = dataset[key].get('cmap', self.config.currentCmap)
                    color = dataset[key].get('color', randomColorGenerator())
                    if isinstance(color, wx.Colour):
                        color = convertRGB255to1(color)
                    elif np.sum(color) > 4:
                        color = convertRGB255to1(color)
                    mz_y_max = dataset[key].get('xylimits', '')
                    if mz_y_max is not None:
                        mz_y_max = mz_y_max[2]

                    method = dataset[key].get('parameters', None)
                    if method is not None:
                        method = method.get('method', '')
                    elif method is None and document.dataType == 'Type: MANUAL':
                        method = 'Manual'
                    else:
                        method = ''

                    _add_to_table = {
                        'mz_start': mz_start,
                        'mz_end': mz_end,
                        'charge': charge,
                        'mz_ymax': mz_y_max,
                        'color': convertRGB1to255(color),
                        'colormap': colormap,
                        'alpha': alpha,
                        'mask': mask,
                        'document': document_title,
                    }
                    self.ionPanel.on_add_to_table(_add_to_table, check_color=False)

                    # Update aui manager
                    self.view.on_toggle_panel(evt=ID_window_ionList, check=True)
                self.ionList.on_remove_duplicates()  # (evt=None, limitCols=False)

            # Restore file list
            if document.dataType == 'Type: MANUAL':
                count = self.filesList.GetItemCount() + len(document.multipleMassSpectrum)
                colors = self.plotsPanel.onChangePalette(None, n_colors=count + 1, return_colors=True)
                for __, key in enumerate(document.multipleMassSpectrum):
                    energy = document.multipleMassSpectrum[key]['trap']
                    if 'color' in document.multipleMassSpectrum[key]:
                        color = document.multipleMassSpectrum[key]['color']
                    else:
                        try:
                            color = colors[count + 1]
                        except Exception:
                            color = randomColorGenerator()
                        document.multipleMassSpectrum[key]['color'] = color

                    if 'label' in document.multipleMassSpectrum[key]:
                        label = document.multipleMassSpectrum[key]['label']
                    else:
                        label = os.path.splitext(key)[0]
                        document.multipleMassSpectrum[key]['label'] = label

                    add_dict = {
                        'filename': key,
                        'document': document.title,
                        'variable': energy,
                        'label': label,
                        'color': color,
                    }

                    self.filesPanel.on_add_to_table(add_dict, check_color=False)

                self.view.panelMML.onRemoveDuplicates(evt=None, limitCols=False)
                # Update aui manager
                self.view.on_toggle_panel(evt=ID_window_multipleMLList, check=True)

            # Restore calibration list
            if document.dataType == 'Type: CALIBRANT':
                tempList = self.view.panelCCS.topP.peaklist
                if document.fileFormat == 'Format: MassLynx (.raw)':
                    for key in document.calibration:
                        tempList.Append([
                            document.title,
                            str(document.calibration[key]['xrange'][0]),
                            str(document.calibration[key]['xrange'][1]),
                            document.calibration[key]['protein'],
                            str(document.calibration[key]['charge']),
                            str(document.calibration[key]['ccs']),
                            str(document.calibration[key]['tD']),
                        ])
                elif document.fileFormat == 'Format: DataFrame':
                    try:
                        self.currentCalibrationParams = document.calibrationParameters
                    except KeyError:
                        pass
                    for key in document.calibration:
                        tempList.Append([
                            document.title,
                            str(document.calibration[key]['xrange'][0]),
                            str(document.calibration[key]['xrange'][1]),
                            document.calibration[key]['protein'],
                            str(document.calibration[key]['charge']),
                            str(document.calibration[key]['ccs']),
                            str(document.calibration[key]['tD']),
                        ])
                # Check for duplicates
                self.view.panelCCS.topP.onRemoveDuplicates(evt=None)
                # Update aui manager
                self.view.on_toggle_panel(evt=ID_window_ccsList, check=True)

            # Restore ion list
            if document.dataType == 'Type: Multifield Linear DT':
                # if self.config.ciuMode == 'LinearDT':
                rtList = self.view.panelLinearDT.topP.peaklist  # List with MassLynx file information
                mzList = self.view.panelLinearDT.bottomP.peaklist  # List with m/z information
                for key in document.IMS1DdriftTimes:
                    retTimes = document.IMS1DdriftTimes[key]['retTimes']
                    driftVoltages = document.IMS1DdriftTimes[key]['driftVoltage']
                    mzVals = document.IMS1DdriftTimes[key]['xylimits']
                    mzStart = mzVals[0]
                    mzEnd = mzVals[1]
                    mzYmax = mzVals[2]
                    charge = str2int(document.IMS1DdriftTimes[key]['charge'])
                    for row in range(len(retTimes)):
                        rtStart = str2int(retTimes[row][0])
                        rtEnd = str2int(retTimes[row][1])
                        rtDiff = str2int(rtEnd - rtStart)
                        driftVoltage = driftVoltages[row]
                        rtList.Append([
                            str2int(rtStart),
                            str2int(rtEnd),
                            str2int(rtDiff),
                            str(driftVoltage),
                            document.title,
                        ])
                    self.view.panelLinearDT.topP.onRemoveDuplicates(evt=None)
                    mzList.Append([
                        str(mzStart),
                        str(mzEnd),
                        str(mzYmax),
                        str(charge),
                        document.title,
                    ])
                self.view.panelLinearDT.bottomP.onRemoveDuplicates(evt=None)

                self.view.on_toggle_panel(evt=ID_window_multiFieldList, check=True)
                self.view._mgr.Update()

        # Update documents tree
        self.documentTree.add_document(docData=document, expandAll=False)
        self.presenter.currentDoc = self.view.panelDocuments.documents.enableCurrentDocument()

    def on_overlay_1D(self, source, plot_type):
        """
        This function enables overlaying of multiple ions together - 1D and RT
        """
        # Check what is the ID
        if source == 'ion':
            tempList = self.ionList
            add_data_to_document = self.view.panelMultipleIons.addToDocument
            normalize_dataset = self.view.panelMultipleIons.normalize1D
        elif source == 'text':
            tempList = self.textList
            add_data_to_document = self.view.panelMultipleText.addToDocument
            normalize_dataset = self.view.panelMultipleText.normalize1D

        if add_data_to_document:
            document = self._get_document_of_type('Type: Comparison')
            document_title = document.title

        # Empty lists
        xlist, ylist, colorlist, legend = [], [], [], []
        idName = ''
        # Get data for the dataset
        for row in range(tempList.GetItemCount()):
            if tempList.IsChecked(index=row):
                if source == 'ion':
                    # Get current document
                    itemInfo = self.ionPanel.OnGetItemInformation(itemID=row)
                    print(itemInfo)
                    document_title = itemInfo['document']
                    # Check that data was extracted first
                    if document_title == '':
                        continue

                    document = self._on_get_document(document_title)
                    dataType = document.dataType
                    selectedItem = itemInfo['ionName']
                    label = itemInfo['label']
                    color = convertRGB255to1(itemInfo['color'])
                    itemName = 'ion={} ({})'.format(selectedItem, document_title)

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
                    if idName == '':
                        idName = itemName
                    else:
                        idName = '{}, {}'.format(idName, itemName)

                    # Add depending which event was triggered
                    if plot_type == 'mobiligram':
                        xvals = data['yvals']  # normally this would be the y-axis
                        yvals = data['yvals1D']
                        if normalize_dataset:
                            yvals = pr_spectra.smooth_gaussian_1D(data=yvals, sigma=self.config.overlay_smooth1DRT)
                            yvals = pr_spectra.normalize_1D(inputData=yvals)
                        xlabels = data['ylabels']  # data was rotated so using ylabel for xlabel

                    elif plot_type == 'chromatogram':
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
                    if label == '':
                        label = selectedItem
                    legend.append(label)
                elif source == 'text':
                    itemInfo = self.textPanel.OnGetItemInformation(itemID=row)
                    document_title = itemInfo['document']
                    label = itemInfo['label']
                    color = itemInfo['color']
                    color = convertRGB255to1(itemInfo['color'])
                    # get document
                    try:
                        document = self._on_get_document(document_title)
                        comparison_flag = False
                        selectedItem = document_title
                        itemName = 'file={}'.format(document_title)
                    except Exception as __:
                        comparison_flag = True
                        document_title, ion_name = re.split(': ', document_title)
                        document = self._on_get_document(document_title)
                        selectedItem = ion_name
                        itemName = 'file={}'.format(ion_name)

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
                    if idName == '':
                        idName = itemName
                    else:
                        idName = '{}, {}'.format(idName, itemName)

                    # Add depending which event was triggered
                    if plot_type == 'mobiligram':
                        xvals = data['yvals']  # normally this would be the y-axis
                        try:
                            yvals = data['yvals1D']
                        except KeyError:
                            yvals = np.sum(data['zvals'], axis=1).T
                        if normalize_dataset:
                            yvals = pr_spectra.smooth_gaussian_1D(data=yvals, sigma=self.config.overlay_smooth1DRT)
                            yvals = pr_spectra.normalize_1D(inputData=yvals)
                        xlabels = data['ylabels']  # data was rotated so using ylabel for xlabel

                    elif plot_type == 'chromatogram':
                        xvals = data['xvals'][:-1]  # TEMPORARY FIX
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
                    if label == '':
                        label = selectedItem
                    legend.append(label)

        # Modify the name to include ion tags
        if plot_type == 'mobiligram':
            idName = '1D: %s' % idName
        elif plot_type == 'chromatogram':
            idName = 'RT: %s' % idName

        # remove unnecessary file extensions from filename
        if len(idName) > 511:
            self.onThreading(None, ('Filename is too long. Reducing...', 4), action='updateStatusbar')
            idName = idName.replace('.csv', '').replace('.txt', '').replace('.raw', '').replace('.d', '')
            idName = idName[:500]

        # Determine x-axis limits for the zoom function
        try:
            xlimits = [min(xvals), max(xvals)]
        except UnboundLocalError:
            self.onThreading(None, ('Please select at least one item in the table.', 4), action='updateStatusbar')
            return
        # Add data to dictionary
        if add_data_to_document:
            document = self._get_document_of_type('Type: Comparison')
            document.gotOverlay = True
            document.IMS2DoverlayData[idName] = {
                'xvals': xlist,
                'yvals': ylist,
                'xlabel': xlabels,
                'colors': colorlist,
                'xlimits': xlimits,
                'labels': legend,
            }
            document_title = document.title
            self.on_update_document(document, 'comparison_data')

        # Plot
        if plot_type == 'mobiligram':
            self.plotsPanel.on_plot_overlay_DT(
                xvals=xlist, yvals=ylist, xlabel=xlabels, colors=colorlist,
                xlimits=xlimits, labels=legend, set_page=True,
            )
        elif plot_type == 'chromatogram':
            self.plotsPanel.on_plot_overlay_RT(
                xvals=xlist, yvals=ylist, xlabel=xlabels, colors=colorlist,
                xlimits=xlimits, labels=legend, set_page=True,
            )

    def on_update_DTMS_zoom(self, xmin, xmax, ymin, ymax):
        """Event driven data sub-sampling

        Parameters
        ----------
        xmin: float
            mouse-event minimum in x-axis
        xmax: float
            mouse-event maximum in x-axis
        ymin: float
            mouse-event minimum in y-axis
        ymax: float
            mouse-event maximum in y-axis
        """
        tstart = ttime()
        # get data
        xvals = copy.deepcopy(self.config.replotData['DT/MS'].get('xvals', None))
        yvals = copy.deepcopy(self.config.replotData['DT/MS'].get('yvals', None))
        zvals = copy.deepcopy(self.config.replotData['DT/MS'].get('zvals', None))
        xlabel = copy.deepcopy(self.config.replotData['DT/MS'].get('xlabels', None))
        ylabel = copy.deepcopy(self.config.replotData['DT/MS'].get('ylabels', None))
        # check if data type is correct
        if zvals is None:
            logger.error('Cannot complete action as plotting data is empty')
            return

        # reduce size of the array to match data extraction window
        xmin_idx, xmax_idx = find_nearest_value(xvals, xmin), find_nearest_value(xvals, xmax)
        ymin_idx, ymax_idx = find_nearest_value(yvals, ymin), find_nearest_value(yvals, ymax)
        zvals = zvals[ymin_idx:ymax_idx, xmin_idx:xmax_idx]
        xvals = xvals[xmin_idx:xmax_idx]
        yvals = yvals[ymin_idx:ymax_idx + 1]

        # check if user enabled smart zoom (ON by default)
        if self.config.smart_zoom_enable:
            xvals, zvals = self.data_processing.downsample_array(xvals, zvals)

        # check if selection window is large enough
        if np.prod(zvals.shape) == 0:
            logger.error('You must select wider dt/mz range to continue')
            return
        # replot
        self.plotsPanel.on_plot_MSDT(
            zvals, xvals, yvals, xlabel, ylabel,
            override=False, update_extents=False,
        )
        logger.info('Sub-sampling took {:.4f}'.format(ttime() - tstart))

    def on_combine_mass_spectra(self, document_name=None):

        document = self._on_get_document(document_name)

        kwargs = {
            'auto_range': False,
            'mz_min': self.config.ms_mzStart,
            'mz_max': self.config.ms_mzEnd,
            'mz_bin': self.config.ms_mzBinSize,
            'linearization_mode': self.config.ms_linearization_mode,
        }
        msg = 'Linearization method: {} | min: {} | max: {} | window: {} | auto-range: {}'.format(
            self.config.ms_linearization_mode,
            self.config.ms_mzStart,
            self.config.ms_mzEnd,
            self.config.ms_mzBinSize,
            self.config.ms_auto_range,
        )
        self.onThreading(None, (msg, 4), action='updateStatusbar')

        if len(list(document.multipleMassSpectrum.keys())) > 0:
            # check the min/max values in the mass spectrum
            if self.config.ms_auto_range:
                mzStart, mzEnd = pr_spectra.check_mass_range(ms_dict=document.multipleMassSpectrum)
                self.config.ms_mzStart = mzStart
                self.config.ms_mzEnd = mzEnd
                kwargs.update(mz_min=mzStart, mz_max=mzEnd)
                try:
                    self.view.panelProcessData.on_update_GUI(update_what='mass_spectra')
                except Exception:
                    pass

            msFilenames = ['m/z']
            counter = 0
            for key in document.multipleMassSpectrum:
                msFilenames.append(key)
                if counter == 0:
                    msDataX, tempArray = pr_spectra.linearize_data(
                        document.multipleMassSpectrum[key]['xvals'],
                        document.multipleMassSpectrum[key]['yvals'],
                        **kwargs
                    )
                    msList = tempArray
                else:
                    msDataX, msList = pr_spectra.linearize_data(
                        document.multipleMassSpectrum[key]['xvals'],
                        document.multipleMassSpectrum[key]['yvals'],
                        **kwargs
                    )
                    tempArray = np.concatenate((tempArray, msList), axis=0)
                counter += 1

            # Reshape the list
            combMS = tempArray.reshape((len(msList), int(counter)), order='F')

            # Sum y-axis data
            msDataY = np.sum(combMS, axis=1)
            msDataY = pr_spectra.normalize_1D(inputData=msDataY)
            xlimits = [
                document.parameters['startMS'],
                document.parameters['endMS'],
            ]

            # Form pandas dataframe
            combMSOut = np.concatenate((msDataX, tempArray), axis=0)
            combMSOut = combMSOut.reshape((len(msList), int(counter + 1)), order='F')

            # Add data
            document.gotMS = True
            document.massSpectrum = {'xvals': msDataX, 'yvals': msDataY, 'xlabels': 'm/z (Da)', 'xlimits': xlimits}
            # Plot
            name_kwargs = {'document': document.title, 'dataset': 'Mass Spectrum'}
            self.plotsPanel.on_plot_MS(msDataX, msDataY, xlimits=xlimits, **name_kwargs)

            # Update status bar with MS range
            self.view.SetStatusText(
                '{}-{}'.format(
                    document.parameters['startMS'],
                    document.parameters['endMS'],
                ), 1,
            )
            self.view.SetStatusText('MSMS: {}'.format(document.parameters['setMS']), 2)
        else:
            document.gotMS = False
            document.massSpectrum = {}
            self.view.SetStatusText('', 1)
            self.view.SetStatusText('', 2)

        # Add info to document
        self.on_update_document(document, 'document')

    def on_highlight_selected_ions(self, evt):
        """
        This function adds rectanges and markers to the m/z window
        """
        document = self._on_get_document()
        document_title = self.documentTree.on_enable_document()

        if document.dataType == 'Type: ORIGAMI' or document.dataType == 'Type: MANUAL':
            peaklist = self.ionList
        elif document.dataType == 'Type: Multifield Linear DT':
            peaklist = self.view.panelLinearDT.bottomP.peaklist
        else:
            return

        if not document.gotMS:
            return

        name_kwargs = {'document': document.title, 'dataset': 'Mass Spectrum'}
        self.plotsPanel.on_plot_MS(
            document.massSpectrum['xvals'],
            document.massSpectrum['yvals'],
            xlimits=document.massSpectrum['xlimits'],
            **name_kwargs
        )
        # Show rectangles
        # Need to check whether there were any ions in the table already
        last = peaklist.GetItemCount() - 1
        ymin = 0
        height = 100000000000
        repaint = False
        for item in range(peaklist.GetItemCount()):
            itemInfo = self.view.panelMultipleIons.OnGetItemInformation(itemID=item)
            filename = itemInfo['document']
            if filename != document_title:
                continue
            label = '{};{}-{}'.format(filename, itemInfo['start'], itemInfo['end'])
            xmin = itemInfo['start']
            width = itemInfo['end'] - xmin
            color = convertRGB255to1(itemInfo['color'])
            if np.sum(color) <= 0:
                color = self.config.markerColor_1D
            if item == last:
                repaint = True
            self.plotsPanel.on_plot_patches(
                xmin, ymin, width, height, color=color,
                alpha=self.config.markerTransparency_1D,
                label=label, repaint=repaint,
            )

    def on_extract_mass_spectrum_for_each_collision_voltage(self, evt):
        """
        """
        document = self._on_get_document()

        # Make sure the document is of correct type.
        if not document.dataType == 'Type: ORIGAMI':
            self.__update_statusbar('Please select correct document type - ORIGAMI', 4)
            return

        # Check that the user combined scans already
        if not document.gotCombinedExtractedIons:
            self.__update_statusbar('Please combine collision voltages first', 4)
            return

        reader = self._get_waters_api_reader(document)

        # Do actual work
        scan_list = document.combineIonsList
        document.gotMultipleMS = True

        xlimits = [document.parameters['startMS'], document.parameters['endMS']]
        for start_end_cv in scan_list:
            start_scan, end_scan, cv = start_end_cv
            spectrum_name = f'Scans: {start_scan}-{end_scan} | CV: {cv} V'
            kwargs = {'start_scan': start_scan, 'end_scan': end_scan}
            mz_x, mz_y = self._get_waters_api_spectrum_data(reader, **kwargs)

            spectrum_data = {
                'xvals': mz_x, 'yvals': mz_y, 'range': [start_scan, end_scan], 'xlabels': 'm/z (Da)',
                'xlimits': xlimits, 'trap': cv,
            }

            self.documentTree.on_update_data(spectrum_data, spectrum_name, document, data_type='extracted.spectrum')

    def get_spectrum(self, query_info, **kwargs):

        document_title, spectrum_title = query_info
        document = self._on_get_document(document_title)

        if spectrum_title == 'Mass Spectrum':
            dataset = document.massSpectrum
        elif spectrum_title == 'Mass Spectrum (processed)':
            dataset = document.smoothMS
        else:
            dataset = document.multipleMassSpectrum.get(spectrum_title, dict())

        return dataset
