"""Data handling module"""
# Standard library imports
import os
import copy
import time
import logging
import threading
from typing import List
from typing import Callable
from multiprocessing.pool import ThreadPool

# Third-party imports
import wx
import numpy as np
from pubsub import pub

# Local imports
from origami.readers import io_text_files
from origami.utils.path import clean_filename
from origami.utils.path import check_path_exists
from origami.utils.path import get_path_and_fname
from origami.utils.color import get_random_color
from origami.utils.color import convert_rgb_255_to_1
from origami.utils.random import get_random_int
from origami.config.config import CONFIG
from origami.handlers.call import Call
from origami.handlers.load import LoadHandler
from origami.handlers.export import ExportHandler
from origami.utils.utilities import report_time
from origami.handlers.process import ProcessHandler
from origami.objects.document import DocumentStore
from origami.processing.utils import get_maximum_xy
from origami.utils.converters import byte2str
from origami.utils.converters import convert_ms_to_bins
from origami.utils.converters import convert_mins_to_scans
from origami.utils.converters import convert_scans_to_mins
from origami.utils.exceptions import MessageError
from origami.config.environment import ENV
from origami.objects.containers import DataObject
from origami.handlers.queue_handler import QUEUE
from origami.gui_elements.misc_dialogs import DialogBox

logger = logging.getLogger(__name__)

# TODO: when loading text files, the user should be asked if he/she wants to open them as separate documents or put
# inside the same file
# TODO: add new data structure for tandem MS data - most likely this will be a SQLite database with table for x/y  data
# and annotations in separate columns


class DataHandling(LoadHandler, ExportHandler, ProcessHandler):
    """General data handling module"""

    def __init__(self, presenter, view, config):
        LoadHandler.__init__(self)
        self.presenter = presenter
        self.view = view
        self.config = CONFIG

        self.text_panel = self.view.panelMultipleText
        self.text_list = self.text_panel.peaklist

        # add application defaults
        self.plot_page = None

        self.thread_pool = ThreadPool(processes=1)
        self.pool_data = None

        # Setup listeners
        # events from chromatogram
        pub.subscribe(self.evt_extract_ms_from_chromatogram, "extract.spectrum.from.chromatogram")

        # events from mobilogram
        pub.subscribe(self.evt_extract_ms_from_mobilogram, "extract.spectrum.from.mobilogram")

        # events from mass spectrum
        pub.subscribe(self.evt_extract_heatmap_from_ms, "extract.heatmap.from.spectrum")
        pub.subscribe(self.evt_extract_rt_from_ms, "extract.chromatogram.from.spectrum")

        # events from heatmap
        pub.subscribe(self.evt_extract_ms_from_heatmap, "extract.spectrum.from.heatmap")

        # events from ms-heatmap
        pub.subscribe(self.evt_extract_rt_from_heatmap, "extract.rt.from.heatmap")

    @property
    def data_processing(self):
        """Return handle to `data_processing`"""
        return self.presenter.data_processing

    @property
    def document_tree(self):
        """Return handle to `document_tree`"""
        return self.presenter.view.panelDocuments.documents

    @property
    def panel_plot(self):
        """Return handle to `panel_plot`"""
        return self.presenter.view.panelPlots

    def add_task(self, func, args, func_pre=None, func_result=None, func_error=None, func_post=None, **kwargs):
        """Adds task to the queue handler

        The `Call` handler works by executing consecutive actions.
        1. First, it executes the `func_pre` with No parameters,
        2. Second, it executes the `func` with args and kwargs
            - if action was successful, it will run the `func_result` function with the returned values of the `func`
            - if action was unsuccessful, it will run the `func_error` with error information
        3. Third, it executes the `func_post` with `func_post_args` and `func_post_kwargs` arguments

        The `func_result`, `func_error` and `func_post` are called using the `wx.CallAfter` mechanism to ensure thread
        safety.
        """
        if func_error is None:
            func_error = self.on_error
        call_obj = Call(
            func,
            *args,
            func_pre=func_pre,
            func_post=func_post,
            func_error=func_error,
            func_result=func_result,
            **kwargs,
        )
        QUEUE.add(call_obj)

    def on_error(self, *args, **kwargs):
        """Inform user and log an error"""

    #         DialogBox(
    #             exceptionTitle="Error",
    #             exceptionMsg="Failed to execute the action",
    #             type="Error",
    #             exceptionPrint=True,
    #             )

    def on_threading(self, action, args, func=None, **kwargs):
        """
        Execute action using new thread
        args: list/dict
            function arguments
        action: str
            decides which action should be taken
        """

        _thread = None
        if action == "fcn":
            if args and kwargs:
                _thread = threading.Thread(target=func, args=args, **kwargs)
            elif args and not kwargs:
                _thread = threading.Thread(target=func, args=args)
        elif action == "statusbar.update":
            _thread = threading.Thread(target=self.view.updateStatusbar, args=args)
        elif action == "load.text.spectrum":
            _thread = threading.Thread(target=self.on_add_text_ms, args=args)
        elif action == "extract.data.user":
            _thread = threading.Thread(target=self.on_extract_data_from_user_input, args=args, **kwargs)
        elif action == "load.text.peaklist":
            _thread = threading.Thread(target=self.on_load_user_list, args=args, **kwargs)
        elif action == "load.raw.mgf":
            _thread = threading.Thread(target=self.on_open_mgf_file, args=args)
        elif action == "load.raw.mzml":
            _thread = threading.Thread(target=self.on_open_mzml_file, args=args)
        elif action == "load.add.mzidentml":
            _thread = threading.Thread(target=self.on_add_mzident_file, args=args)

        if _thread is None:
            logger.warning("Failed to execute the operation in threaded mode. Consider switching it off?")
            return

        # Start thread
        try:
            _thread.start()
        except Exception as e:
            logger.warning("Failed to execute the operation in threaded mode. Consider switching it off?")
            logger.error(e)

    def on_get_csv_filename(self, default_filename: str = "", default_path: str = None, ask_permission: bool = False):
        """Get filename where to save text file"""
        wildcard = (
            "CSV (Comma delimited) (*.csv)|*.csv|"
            + "Text (Tab delimited) (*.txt)|*.txt|"
            + "Text (Space delimited (*.txt)|*.txt"
        )

        wildcard_dict = {",": 0, "\t": 1, " ": 2}

        if ask_permission:
            style = wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        else:
            style = wx.FD_SAVE

        dlg = wx.FileDialog(
            self.presenter.view, "Please select a name for the file", "", "", wildcard=wildcard, style=style
        )
        dlg.CentreOnParent()

        # cleanup the name
        default_filename = (
            default_filename.replace(" ", "")
            .replace(":", "")
            .replace(" ", "")
            .replace(".csv", "")
            .replace(".txt", "")
            .replace(".raw", "")
            .replace(".d", "")
            .replace(".", "_")
        )
        dlg.SetFilename(default_filename)
        try:
            dlg.SetFilterIndex(wildcard_dict[CONFIG.saveDelimiter])
        except KeyError:
            pass
        if default_path is not None:
            dlg.SetPath(default_path)

        filename = ""
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()

        return filename

    def update_statusbar(self, msg, field):
        self.on_threading(args=(msg, field), action="statusbar.update")

    def on_get_directory_path(self, title: str):
        """Get path to directory"""
        path = None
        dlg = wx.DirDialog(wx.GetTopLevelParent(self.view), title, style=wx.DD_DEFAULT_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
        dlg.Destroy()

        return path

    @staticmethod
    def on_open_directory(path):
        """Open document path"""

        # if path is not provided, get one from current document
        if path is None:
            document = ENV.on_get_document()
            path = document.path

        # check whether the path exist
        if not check_path_exists(path):
            raise MessageError("Path does not exist", f"Path {path} does not exist")

        # open path
        try:
            os.startfile(path)
        except WindowsError:
            raise MessageError("Path does not exist", f"Failed to open {path}")

        pub.sendMessage("notify.message.success", message="Opening directory...")

    def on_open_origami_document(self, _evt):
        """Open ORIGAMI document"""
        path = None
        dlg = wx.DirDialog(self.view, "Choose a ORIGAMI (.origami) directory store")
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
        dlg.Destroy()

        if path is None:
            logger.warning("Operation was cancelled")
            pub.sendMessage("notify.message.warning", message="Operation was cancelled.")
            return
        elif not path.endswith(".origami"):
            logger.error("Operation was cancelled - it was not an ORIGAMI document.")
            pub.sendMessage("notify.message.error", message="Operation was cancelled - it was not an ORIGAMI document.")
            return
        self.on_setup_basic_document(ENV.load(path))
        pub.sendMessage("file.recent.add", action="origami.document", path=path)

    def on_show_tandem_scan(self, scan_data):
        """Displays scan data in the viewer"""
        if scan_data is None:
            logger.warning("Could not display scan data")
            return
        title = (
            f"Precursor: {scan_data['scan_info']['precursor_mz']:.4f} [{scan_data['scan_info']['precursor_charge']}]"
        )
        self.panel_plot.on_plot_centroid_MS(scan_data["Scan 1"]["xvals"], scan_data["Scan 1"]["yvals"], title=title)

    def on_setup_basic_document(self, document: DocumentStore):
        """This function consumes initialized document with its data already present, displays its results and add the
        document to the document tree in a thread-safe manner"""
        t_start = time.time()

        # show mass spectrum
        if "MassSpectra/Summed Spectrum" in document:
            mz = document["MassSpectra/Summed Spectrum", True]
            self.panel_plot.view_ms.plot(obj=mz)

        # show chromatogram
        if "Chromatograms/Summed Chromatogram" in document:
            rt = document["Chromatograms/Summed Chromatogram", True]
            self.panel_plot.view_rt_rt.plot(obj=rt)

        # show mobilogram
        if "Mobilograms/Summed Mobilogram" in document:
            dt = document["Mobilograms/Summed Mobilogram", True]
            self.panel_plot.view_dt_dt.plot(obj=dt)

        # show heatmap
        if "IonHeatmaps/Summed Heatmap" in document:
            heatmap = document["IonHeatmaps/Summed Heatmap", True]
            self.panel_plot.view_heatmap.plot(obj=heatmap)

        # show mass heatmap
        if "MSDTHeatmaps/Summed Heatmap" in document:
            heatmap = document["MSDTHeatmaps/Summed Heatmap", True]
            self.panel_plot.view_msdt.plot(obj=heatmap)

        self.on_update_document(document, "document")
        logger.info(f"It took {time.time()-t_start:.4f} seconds to load {document.title}")

    @staticmethod
    def _parse_mass_spectrum_range_waters(document, x_label, x_min, x_max, y_label, y_min, y_max):
        """Parse values obtained from mass spectrum plot"""
        # check whether data had been rotated
        if y_label in ["m/z (Da)"]:
            x_label, x_min, x_max = y_label, y_min, y_max

        return x_min, x_max

    @staticmethod
    def _parse_mobilogram_range_waters(document, x_label, x_min, x_max, y_label, y_min, y_max):
        """Parse values obtained from mobilogram plot"""
        parameters = document.parameters
        if not parameters:
            raise MessageError("Error", "Could not retrieve required data parameters")

        # check whether data had been rotated
        if y_label in ["Drift time (bins)", "bins", "Drift time (ms)", "Arrival time (ms)", "ms"]:
            x_label, x_min, x_max = y_label, y_min, y_max

        # extracting mass spectrum from mobilogram
        if x_label in ["Drift time (bins)", "bins"]:
            x_min = np.ceil(x_min).astype(int)
            x_max = np.floor(x_max).astype(int)
        # convert ms to bins
        elif x_label in ["Drift time (ms)", "Arrival time (ms)", "ms"]:
            x_min, x_max = convert_ms_to_bins([x_min, x_max], parameters["pusher_freq"])
        else:
            raise MessageError("Error", "Could not process x-axis label")

        return x_min, x_max

    @staticmethod
    def _parse_chromatogram_range_waters(document, x_label, x_min, x_max, y_label, y_min, y_max, output="bins"):
        """Parse values obtained from chromatogram plot"""
        parameters = document.parameters
        if not parameters:
            raise MessageError("Error", "Could not retrieve required data parameters")

        # check whether data had been rotated
        if y_label in ["Scans", "Time (min)", "Retention time (min)", "min"]:
            x_label, x_min, x_max = y_label, y_min, y_max

        if output == "bins":
            if x_label in ["Scans"]:
                x_min = np.ceil(x_min).astype(int)
                x_max = np.floor(x_max).astype(int)
            # convert ms to bins
            elif x_label in ["Time (min)", "Retention time (min)", "min"]:
                x_min, x_max = convert_mins_to_scans([x_min, x_max], parameters["scan_time"])
            else:
                raise ValueError("Could not process x-axis label")
        elif output == "time":
            if x_label in ["Scans"]:
                x_min, x_max = convert_scans_to_mins([x_min, x_max], parameters["scan_time"])

        return x_min, x_max

    def _parse_chromatogram_range_thermo(self, document, x_label, x_min, x_max, output="bins"):
        """Parse values obtained from chromatogram plot"""

    @staticmethod
    def _plot_extraction_disabled():
        """Inform the user that extraction was disabled and how to enable it again"""
        pub.sendMessage(
            "notify.message.warning",
            "Extraction in this panel was disabled. Hold CTRL + right-click in the plot area to enable it again.",
        )

    def evt_extract_ms_from_heatmap(self, rect, x_labels, y_labels):
        """Extracts mass spectrum from heatmap"""
        t_start = time.time()

        if len(x_labels) > 1:
            raise ValueError("Cannot handle multiple labels")

        # unpack values
        x_label = x_labels[0]
        y_label = y_labels[0]
        x_min, x_max, y_min, y_max = rect
        document = ENV.on_get_document()

        can_extract, is_multifile, file_fmt = document.can_extract()

        if not can_extract:
            raise MessageError("Error", "This document type does not allow data extraction")
        if is_multifile:
            raise MessageError("Error", "Multifile data extraction is not supported yet")
        if file_fmt == "thermo":
            raise MessageError("Error", "Cannot extract mass spectrum data from heatmap")

        # mark on the plot where data is being extracted from
        self.panel_plot.view_heatmap.add_patches([x_min], [y_min], [x_max - x_min], [y_max - y_min], pickable=False)

        # convert limits to the correct format
        x_min_rt, x_max_rt = self._parse_chromatogram_range_waters(
            document, x_label, x_min, x_max, y_label, y_min, y_max, "time"
        )
        y_min_dt, y_max_dt = self._parse_mobilogram_range_waters(document, y_label, y_min, y_max, x_label, x_min, x_max)

        # ensure extraction range is broad enough
        if x_min_rt >= x_max_rt:
            raise MessageError("Error", "The extraction range in the chromatogram dimension was too narrow!")
        if y_min_dt >= y_max_dt:
            raise MessageError("Error", "The extraction range in the mobilogram dimension was too narrow!")

        # get data
        if CONFIG.plot_panel_heatmap_extract_ms:
            obj_name, mz_obj, document = self.waters_extract_ms_from_heatmap(
                x_min_rt, x_max_rt, y_min_dt, y_max_dt, document.title
            )

            # set data
            self.panel_plot.view_ms.plot(obj=mz_obj)
            if CONFIG.plot_panel_heatmap_extract_ms_popup:
                self.panel_plot.popup_ms.plot(obj=mz_obj)

            # # Update document
            self.document_tree.on_update_document(mz_obj.DOCUMENT_KEY, obj_name, document.title)
            logger.info(f"Extracted mass spectrum in {report_time(t_start)} - See: {obj_name}")
        else:
            self._plot_extraction_disabled()

    def evt_extract_rt_from_heatmap(self, rect, x_labels, y_labels):
        """Extracts chromatogram from heatmap"""
        t_start = time.time()
        if len(x_labels) > 1:
            raise ValueError("Cannot handle multiple labels")

        # unpack values
        x_label = x_labels[0]
        y_label = y_labels[0]
        x_min, x_max, y_min, y_max = rect
        document = ENV.on_get_document()

        can_extract, is_multifile, file_fmt = document.can_extract()
        if not can_extract:
            raise MessageError("Error", "This document type does not allow data extraction")
        if is_multifile:
            raise MessageError("Error", "Multifile data extraction is not supported yet")
        if file_fmt == "thermo":
            raise MessageError("Error", "Cannot extract retention time data from heatmap")

        # mark on the plot where data is being extracted from
        self.panel_plot.view_msdt.add_patches([x_min], [y_min], [x_max - x_min], [y_max - y_min], pickable=False)

        # convert limits to the correct format
        x_min_mz, x_max_mz = self._parse_mass_spectrum_range_waters(
            document, x_label, x_min, x_max, y_label, y_min, y_max
        )
        y_min_dt, y_max_dt = self._parse_mobilogram_range_waters(document, y_label, y_min, y_max, x_label, x_min, x_max)

        # ensure extraction range is broad enough
        if x_min_mz >= x_max_mz:
            raise MessageError("Error", "The extraction range in the mass spectrum dimension was too narrow!")
        if y_min_dt >= y_max_dt:
            raise MessageError("Error", "The extraction range in the mobilogram dimension was too narrow!")

        if CONFIG.plot_panel_heatmap_extract_rt:
            # get data
            obj_name, rt_obj, document = self.waters_extract_rt_from_msdt(
                x_min_mz, x_max_mz, y_min_dt, y_max_dt, document.title
            )

            # set data
            self.panel_plot.view_rt_rt.plot(obj=rt_obj)
            if CONFIG.plot_panel_heatmap_extract_rt_popup:
                self.panel_plot.popup_rt.plot(obj=rt_obj)

            # # Update document
            self.document_tree.on_update_document(rt_obj.DOCUMENT_KEY, obj_name, document.title)
            logger.info(f"Extracted chromatogram in {report_time(t_start)} - See: {obj_name}")
        else:
            self._plot_extraction_disabled()

    def evt_extract_ms_from_mobilogram(self, rect, x_labels, y_labels):
        """Extracts mass spectrum based on selection window in a mobilogram plot"""
        # TODO: add handler for other vendors
        t_start = time.time()
        if len(x_labels) > 1:
            raise ValueError("Cannot handle multiple labels")

        # unpack values
        x_label = x_labels[0]
        y_label = y_labels[0]
        x_min, x_max, y_min, y_max = rect
        document = ENV.on_get_document()

        can_extract, is_multifile, file_fmt = document.can_extract()
        if not can_extract:
            raise MessageError("Error", "This document type does not allow data extraction")
        if is_multifile:
            raise MessageError("Error", "Multifile data extraction is not supported yet")
        if file_fmt == "thermo":
            raise MessageError("Error", "Cannot extract heatmap from Thermo file")

        x_min, x_max = self._parse_mobilogram_range_waters(document, x_label, x_min, x_max, y_label, y_min, y_max)

        # get plot data and calculate maximum values in the arrays
        x, y = self.panel_plot.view_dt_dt.get_data(["x", "y"])
        _, y_val = get_maximum_xy(x, y, x_min, x_max)

        if CONFIG.plot_panel_dt_extract_ms:
            # mark on the plot where data is being extracted from
            self.panel_plot.view_dt_dt.add_patches([x_min], [0], [x_max - x_min], [y_val], pickable=False)

            # get data
            obj_name, mz_obj, document = self.waters_extract_ms_from_mobilogram(x_min, x_max, document.title)

            # set data
            self.panel_plot.view_ms.plot(obj=mz_obj)
            if CONFIG.plot_panel_dt_extract_ms_popup:
                self.panel_plot.popup_ms.plot(obj=mz_obj)

            # # Update document
            self.document_tree.on_update_document(mz_obj.DOCUMENT_KEY, obj_name, document.title)
            logger.info(f"Extracted mass spectrum in {report_time(t_start)} - See: {obj_name}")
        else:
            self._plot_extraction_disabled()

    def evt_extract_ms_from_chromatogram(self, rect, x_labels, y_labels):
        """Extracts mass spectrum based on selection window in a mobilogram plot"""
        # TODO: this should actual do work in mins rather than scans!
        # TODO: add handler for other vendors
        t_start = time.time()
        if len(x_labels) > 1:
            raise ValueError("Cannot handle multiple labels")

        # unpack values
        x_label = x_labels[0]
        y_label = y_labels[0]
        x_min, x_max, y_min, y_max = rect
        document = ENV.on_get_document()

        can_extract, is_multifile, file_fmt = document.can_extract()
        if not can_extract:
            raise MessageError("Error", "This document type does not allow data extraction")
        if is_multifile:
            raise MessageError("Error", "Multifile data extraction is not supported yet")

        # get plot data and calculate maximum values in the arrays
        x, y = self.panel_plot.view_rt_rt.get_data(["x", "y"])
        _, y_val = get_maximum_xy(x, y, x_min, x_max)

        if CONFIG.plot_panel_rt_extract_ms:
            # mark on the plot where data is being extracted from
            self.panel_plot.view_rt_rt.add_patches([x_min], [0], [x_max - x_min], [y_val], pickable=False)

            if file_fmt == "waters":
                x_min, x_max = self._parse_chromatogram_range_waters(
                    document, x_label, x_min, x_max, y_label, y_min, y_max, "time"
                )
                obj_name, mz_obj, document = self.waters_extract_ms_from_chromatogram(x_min, x_max, document.title)
            elif file_fmt == "thermo":
                as_scans = False if "mins" in x_label else True
                obj_name, mz_obj, document = self.thermo_extract_ms_from_chromatogram(
                    x_min, x_max, as_scans, document.title
                )
            else:
                return

            # set data
            self.panel_plot.popup_ms.plot(obj=mz_obj)
            if CONFIG.plot_panel_rt_extract_ms_popup:
                self.panel_plot.view_ms.plot(obj=mz_obj)

            # # Update document
            self.document_tree.on_update_document(mz_obj.DOCUMENT_KEY, obj_name, document.title)
            logger.info(f"Extracted mass spectrum in {report_time(t_start)} - See: {obj_name}")
        else:
            self._plot_extraction_disabled()

    def evt_extract_heatmap_from_ms(self, rect, x_labels, y_labels):
        """Extract ion heatmap from mass spectrum"""
        t_start = time.time()
        # unpack values
        x_min, x_max, _, _ = rect
        document = ENV.on_get_document()

        can_extract, is_multifile, file_fmt = document.can_extract()
        if not can_extract:
            raise MessageError("Error", "This document type 8does not allow data extraction")
        #         if is_multifile:
        #             raise MessageError("Error", "Multifile data extraction is not supported yet")
        if file_fmt == "thermo":
            raise MessageError("Error", "Cannot extract heatmap from Thermo file")

        # get plot data and calculate maximum values in the arrays
        x, y = self.panel_plot.view_ms.get_data(["x", "y"])
        _, y_val = get_maximum_xy(x, y, x_min, x_max)

        if CONFIG.plot_panel_ms_extract_heatmap:
            # mark on the plot where data is being extracted from
            self.panel_plot.view_ms.add_patches([x_min], [0], [x_max - x_min], [y_val], pickable=False)

            # get data
            if is_multifile:
                filelist = document.get_multifile_filelist(["variable"])
                obj_name, heatmap_obj, document = self.waters_extract_heatmap_from_mass_spectrum_multifile(
                    x_min, x_max, filelist, document.title
                )
            else:

                obj_name, heatmap_obj, document = self.waters_extract_heatmap_from_mass_spectrum_one(
                    x_min, x_max, document.title
                )

            # set data
            self.panel_plot.view_heatmap.plot(obj=heatmap_obj)
            if CONFIG.plot_panel_ms_extract_heatmap_popup:
                self.panel_plot.popup_2d.plot(obj=heatmap_obj)

            # # Update document
            self.document_tree.on_update_document(heatmap_obj.DOCUMENT_KEY, obj_name, document.title)
            logger.info(f"Extracted ion heatmap in {report_time(t_start)} - See: {obj_name}")
        else:
            self._plot_extraction_disabled()

    def evt_extract_rt_from_ms(self, rect, x_labels, y_labels):
        """Extract chromatogram from mass spectrum"""
        t_start = time.time()
        # unpack values
        x_min, x_max, _, _ = rect
        document = ENV.on_get_document()

        can_extract, is_multifile, file_fmt = document.can_extract()
        if not can_extract:
            raise MessageError("Error", "This document type 8does not allow data extraction")
        if is_multifile:
            raise MessageError("Error", "Multifile data extraction is not supported yet")
        if file_fmt == "thermo":
            raise MessageError("Error", "Cannot extract heatmap from Thermo file")

        # get plot data and calculate maximum values in the arrays
        x, y = self.panel_plot.view_ms.get_data(["x", "y"])
        _, y_val = get_maximum_xy(x, y, x_min, x_max)

        if CONFIG.plot_panel_ms_extract_rt:
            # mark on the plot where data is being extracted from
            # self.panel_plot.view_ms.add_patches([x_min], [0], [x_max - x_min], [y_val], pickable=False)

            # get data
            #         if is_multifile:
            #             filelist = document.get_multifile_filelist(["variable"])
            #             obj_name, heatmap_obj, document = self.waters_extract_rt_from_mass_spectrum_multifile(
            #                 x_min, x_max, filelist, document.title
            #             )
            #         else:
            obj_name, rt_obj, document = self.waters_extract_rt_from_mass_spectrum(x_min, x_max, document.title)

            # set data
            self.panel_plot.view_rt_rt.plot(obj=rt_obj)
            if CONFIG.plot_panel_ms_extract_rt_popup:
                self.panel_plot.popup_rt.plot(obj=rt_obj)

            # # Update document
            self.document_tree.on_update_document(rt_obj.DOCUMENT_KEY, obj_name, document.title)
            logger.info(f"Extracted ion heatmap in {report_time(t_start)} - See: {obj_name}")
        else:
            self._plot_extraction_disabled()

    def on_save_unsaved_changes(self, data_obj, document_title: str = None, dataset_name: str = None):
        """Save unchanged changes on an object"""
        from origami.gui_elements.dialog_save_unsaved import DialogSaveUnsaved

        if document_title is None or dataset_name is None:
            document_title, dataset_name = data_obj.owner

        dlg = DialogSaveUnsaved(self.view, document_title, dataset_name)
        dlg.ShowModal()
        obj_name = dlg.new_name
        if obj_name is None:
            return False, None

        # # Update document
        document = ENV.on_get_document(document_title)
        data_obj = document.add(obj_name, data_obj, as_object=True)

        self.document_tree.on_update_document(data_obj.DOCUMENT_KEY, obj_name, document_title)
        return True, data_obj

    def on_open_multiple_text_2d_fcn(self, evt):
        """Select list of heatmap text files and load them as documents

        If multi-threading is enabled, the action will be executed in a non-blocking manner

        Parameters
        ----------
        evt : wx.Event
            event that triggered the function
        """
        # TODO: add option to put all files into the same document

        # get list of files to open
        wildcard = "Text files with axis labels (*.txt, *.csv)| *.txt;*.csv"
        path_list, file_list = None, None
        dlg = wx.FileDialog(
            self.view,
            "Choose heatmap text file(s) to load...",
            wildcard=wildcard,
            style=wx.FD_MULTIPLE | wx.FD_CHANGE_DIR,
        )
        if dlg.ShowModal() == wx.ID_OK:
            path_list = dlg.GetPaths()
            file_list = dlg.GetFilenames()
        dlg.Destroy()

        if not path_list:
            logger.warning("Action was stopped by the user")
            return

        # get labels for selected items
        x_label, y_label = self.view.get_user_text_x_y_label()

        self.view.on_toggle_panel(evt="text", check=True)
        for filename, filepath in zip(file_list, path_list):
            self.add_task(self.on_load_text_2d, (filename, filepath, x_label, y_label), func_result=self.on_add_text_2d)
            pub.sendMessage("file.recent.add", action="text.heatmap", path=filepath)

    def on_load_text_2d(
        self, filename: str, filepath: str, x_label: str = "Collision Voltage (V)", y_label: str = "Drift time (bins)"
    ):
        """Load heatmap text data without updating GUI"""
        if filename is None:
            _, filename = get_path_and_fname(filepath, simple=True)

        # Split filename to get path
        _, filename = get_path_and_fname(filepath, simple=True)
        filepath = byte2str(filepath)

        if self.text_panel.on_check_existing(filename) or ENV.exists(path=filepath):
            logger.warning(f"Dataset {filename} already exists")
            return None, None, None

        # load heatmap information and split into individual components
        heatmap_obj = self.load_text_heatmap_data(filepath)

        xlabel_start, xlabel_end = heatmap_obj.x[0], heatmap_obj.x[-1]
        color = self.text_panel.on_get_unique_color(next(CONFIG.custom_colors_cycle))

        # update heatmap object and its metadata
        heatmap_obj.x_label = x_label
        heatmap_obj.y_label = y_label
        heatmap_obj.set_metadata(
            {
                "cmap": CONFIG.heatmap_colormap,
                "mask": CONFIG.overlay_defaultMask,
                "alpha": CONFIG.overlay_defaultAlpha,
                "min_threshold": 0,
                "max_threshold": 1,
                "color": convert_rgb_255_to_1(color),
            }
        )

        # add data to document
        document = ENV.get_new_document("text", filepath, data=dict(heatmap=heatmap_obj))

        # setup data that needs to be added to the table
        add_dict = {
            "start": xlabel_start,
            "end": xlabel_end,
            "charge": "",
            "color": color,
            "heatmap_colormap": next(CONFIG.overlay_cmap_cycle),
            "alpha": CONFIG.overlay_defaultAlpha,
            "mask": CONFIG.overlay_defaultMask,
            "label": "",
            "shape": heatmap_obj.shape,
            "document": document.title,
        }

        return document, add_dict, filepath

    def on_add_text_2d(self, document, add_dict, filepath):
        """Safely add data to the GUI application"""
        if any([_ is None for _ in [document, add_dict, filepath]]):
            logger.warning("Could not update GUI")
            return
        self.text_panel.on_add_to_table(add_dict, return_color=False)
        self.on_setup_basic_document(document)

    def on_open_multiple_text_ms_fcn(self, _evt):
        """Open multiple text-based mass spectra"""
        # get list of files to open
        wildcard = "Text files with axis labels (*.txt, *.csv)| *.txt;*.csv"
        path_list = None
        dlg = wx.FileDialog(
            self.view,
            "Choose heatmap text file(s) to load...",
            wildcard=wildcard,
            style=wx.FD_MULTIPLE | wx.FD_CHANGE_DIR,
        )
        if dlg.ShowModal() == wx.ID_OK:
            path_list = dlg.GetPaths()
        dlg.Destroy()

        for filepath in path_list:
            self.add_task(self.on_add_text_ms, (filepath,), func_result=self.on_setup_basic_document)
            pub.sendMessage("file.recent.add", action="text.ms", path=filepath)

    def on_add_text_ms(self, path):
        """Load text mass spectrum"""
        # Update statusbar
        self.update_statusbar(f"Loading {path}...", 4)
        document = self.load_text_mass_spectrum_document(path)

        return document

    def on_open_thermo_file_fcn(self, _evt):
        """Open Thermo .RAW file"""

        paths = []
        dlg = wx.FileDialog(
            self.presenter.view,
            "Open Thermo file",
            wildcard="*.raw; *.RAW",
            style=wx.FD_MULTIPLE | wx.FD_DEFAULT_STYLE | wx.FD_CHANGE_DIR,
        )
        if dlg.ShowModal() == wx.ID_OK:
            paths = dlg.GetPaths()
        dlg.Destroy()

        for path in paths:
            self.add_task(self.load_thermo_ms_document, (path,), func_result=self.on_setup_basic_document)
            pub.sendMessage("file.recent.add", action="thermo.ms", path=path)

    def on_open_mgf_file_fcn(self, _evt):
        """Load tandem data in MZML format"""
        paths = []
        dlg = wx.FileDialog(
            self.presenter.view,
            "Open mzML file",
            wildcard="*.mzML; *.MZML",
            style=wx.FD_MULTIPLE | wx.FD_DEFAULT_STYLE | wx.FD_CHANGE_DIR,
        )
        if dlg.ShowModal() == wx.ID_OK:
            paths = dlg.GetPaths()

        for path in paths:
            self.add_task(self.on_open_mgf_file, (path,), func_result=self.on_show_tandem_scan)
            pub.sendMessage("file.recent.add", action="msms.mgf", path=path)

    def on_open_mgf_file(self, path):
        """Load tandem data in MGF format"""
        if path is None:
            return None
        t_start = time.time()
        document = self.load_mgf_document(path)
        data = document.tandem_spectra["Scan 1"]
        self.on_update_document(document, "document")
        logger.info(f"It took {time.time()-t_start:.4f} seconds to load {document.title}")
        return data

    def on_open_mzml_file_fcn(self, evt):
        """Load tandem data in MZML format"""
        paths = []
        dlg = wx.FileDialog(
            self.presenter.view,
            "Open mzML file",
            wildcard="*.mzML; *.MZML",
            style=wx.FD_MULTIPLE | wx.FD_DEFAULT_STYLE | wx.FD_CHANGE_DIR,
        )
        if dlg.ShowModal() == wx.ID_OK:
            paths = dlg.GetPaths()
        dlg.Destroy()

        for path in paths:
            self.add_task(self.on_open_mzml_file, (path,), func_result=self.on_show_tandem_scan)
            pub.sendMessage("file.recent.add", action="msms.mzml", path=path)

    def on_open_mzml_file(self, path):
        """Load mzml data and return it"""
        if path is None:
            return None
        t_start = time.time()
        document = self.load_mzml_document(path)
        data = document.tandem_spectra["Scan 1"]
        self.on_update_document(document, "document")
        logger.info(f"It took {time.time()-t_start:.4f} seconds to load {document.title}")
        return data

    def on_open_waters_raw_ms_fcn(self, evt):
        """Open Waters (.raw) file"""
        path = self.on_get_directory_path("Choose a Waters (.raw) directory")
        if path is None:
            logger.warning("Could not load file")
            return

        self.add_task(self.load_waters_ms_document, (path,), func_result=self.on_setup_basic_document)
        pub.sendMessage("file.recent.add", action="waters.ms", path=path)

    def on_open_waters_raw_imms_fcn(self, evt):
        """Open Waters (.raw) file"""
        path = self.on_get_directory_path("Choose a Waters (.raw) directory")
        if path is None:
            logger.warning("Could not load file")
            return

        if not self.check_waters_im(path):
            dlg = DialogBox(
                kind="Question",
                msg="This dataset does not have ion mobility dimension -" " would you like to load it in MS-mode only?",
            )
            if dlg == wx.ID_NO:
                logger.info("Delete operation was cancelled")
                return
            self.add_task(self.load_waters_ms_document, (path,), func_result=self.on_setup_basic_document)
        else:
            self.add_task(self.load_waters_im_document, (path,), func_result=self.on_setup_basic_document)
        pub.sendMessage("file.recent.add", action="waters.imms", path=path)

    def on_open_single_clipboard_ms(self, _):
        """Get spectrum (n x 2) from clipboard

        Typically spectrum would be from MassLynx of Thermo software in a two-column format where the first column
        is m/z values followed by intensity. Data is assumed to be floats even if its likely that intensity values
        will be in integer format.
        """
        try:
            wx.TheClipboard.Open()
            text_obj = wx.TextDataObject()
            wx.TheClipboard.GetData(text_obj)
            wx.TheClipboard.Close()
            clip_stream = text_obj.GetText()
            clip_stream = clip_stream.splitlines()

            # get document path
            dlg = wx.FileDialog(
                self.view,
                "Please select name and directory for the MS document...",
                style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
            )
            dlg.SetFilename("spectrum-from-clipboard")
            if dlg.ShowModal() == wx.ID_OK:
                path = dlg.GetPath()
            dlg.Destroy()

            document = self.load_clipboard_ms_document(path, clip_stream)
            self.on_setup_basic_document(document)
        except Exception:
            logger.warning("Failed to get spectrum from the clipboard", exc_info=True)
            return

    # NEED UPDATING \\\\\/////

    def on_get_document(self, document_title=None):
        """Get document"""
        if document_title is None:
            document_title = self.document_tree.on_enable_document()
        else:
            document_title = byte2str(document_title)

        if document_title in [None, "Documents", ""]:
            logger.error(f"No such document {document_title} exist")
            return None

        document_title = byte2str(document_title)
        try:
            document = ENV[document_title]
        except KeyError:
            logger.error(f"Document {document_title} does not exist")
            return None

        return document

    def _on_check_last_path(self):
        if not check_path_exists(CONFIG.lastDir):
            CONFIG.lastDir = os.getcwd()

    def _on_get_path(self):
        dlg = wx.FileDialog(self.view, "Please select name and path for the document...", "", "", "", wx.FD_SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            path, fname = os.path.split(dlg.GetPath())

            return path, fname
        else:
            return None, None

    def on_save_data_as_text(self, data, labels, data_format, **kwargs):

        wildcard = (
            "CSV (Comma delimited) (*.csv)|*.csv|"
            + "Text (Tab delimited) (*.txt)|*.txt|"
            + "Text (Space delimited (*.txt)|*.txt"
        )
        wildcard_dict = {",": 0, "\t": 1, " ": 2}

        style = wx.FD_SAVE
        if kwargs.get("ask_permission", False):
            style = wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        dlg = wx.FileDialog(self.view, "Save text file...", "", "", wildcard=wildcard, style=style)

        default_name = ""
        if "default_name" in kwargs:
            default_name = kwargs.pop("default_name")
            default_name = clean_filename(default_name)
        dlg.SetFilename(default_name)

        try:
            dlg.SetFilterIndex(wildcard_dict[CONFIG.saveDelimiter])
        except KeyError:
            logger.warning("Could not process wildcard delimiter")
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
            __, extension = os.path.splitext(filename)
            CONFIG.saveExtension = extension
            CONFIG.saveDelimiter = list(wildcard_dict.keys())[list(wildcard_dict.values()).index(dlg.GetFilterIndex())]
            if isinstance(data, DataObject):
                data.to_csv(filename, delimiter=CONFIG.saveDelimiter)
            else:
                io_text_files.save_data(
                    filename=filename,
                    data=data,
                    fmt=data_format,
                    delimiter=CONFIG.saveDelimiter,
                    header=CONFIG.saveDelimiter.join(labels),
                    **kwargs,
                )
            logger.info(f"Saved {filename}")
        dlg.Destroy()

    def on_extract_data_from_user_input_fcn(self, document_title=None, **kwargs):

        if not CONFIG.APP_ENABLE_THREADING:
            self.on_extract_data_from_user_input(document_title, **kwargs)
        else:
            self.on_threading(action="extract.data.user", args=(document_title,), kwargs=kwargs)

    def on_extract_data_from_user_input(self, document_title=None, **kwargs):
        """Extract MS/RT/DT/2DT data based on user input"""
        # TODO: This function should check against xvals_mins / xvals_ms to get accurate times
        raise NotImplementedError("Must implement method")

        # document = self.on_get_document(document_title)
        # try:
        #     reader = self._get_waters_api_reader(document)
        # except (AttributeError, ValueError, TypeError):
        #     reader = None
        #
        # # check if data should be added to document
        # add_to_document = kwargs.pop("add_to_document", False)
        # return_data = kwargs.pop("return_data", True)
        # data_storage = {}
        #
        # # get m/z limits
        # mz_start = CONFIG.extract_mzStart
        # mz_end = CONFIG.extract_mzEnd
        # mz_start, mz_end = check_value_order(mz_start, mz_end)
        #
        # # get RT limits
        # rt_start = CONFIG.extract_rtStart
        # rt_end = CONFIG.extract_rtEnd
        # rt_start, rt_end = check_value_order(rt_start, rt_end)
        #
        # # get DT limits
        # dt_start = CONFIG.extract_dtStart
        # dt_end = CONFIG.extract_dtEnd
        # dt_start, dt_end = check_value_order(dt_start, dt_end)
        #
        # # convert scans to minutes
        # if CONFIG.extract_rt_use_scans:
        #     if reader is not None:
        #         rt_start, rt_end = self._get_waters_api_nearest_RT_in_minutes(reader, rt_start, rt_end)
        #     else:
        #         scan_time = kwargs.pop("scan_time", document.parameters["scanTime"])
        #         rt_start = ((rt_start + 1) * scan_time) / 60
        #         rt_end = ((rt_end + 1) * scan_time) / 60
        #
        # # convert ms to drift bins
        # if CONFIG.extract_dt_use_ms:
        #     if reader is not None:
        #         dt_start, dt_end = self._get_waters_api_nearest_DT_in_bins(reader, dt_start, dt_end)
        #     else:
        #         pusher_frequency = kwargs.pop("pusher_frequency", document.parameters["pusherFreq"])
        #         dt_start = int(dt_start / (pusher_frequency * 0.001))
        #         dt_end = int(dt_end / (pusher_frequency * 0.001))
        #
        # # check input
        # if reader is not None:
        #     mz_start, mz_end, rt_start, rt_end, dt_start, dt_end = self._check_waters_input(
        #         reader, mz_start, mz_end, rt_start, rt_end, dt_start, dt_end
        #     )
        #
        # # extract mass spectrum
        # if CONFIG.extract_massSpectra:
        #     mz_kwargs = dict()
        #     spectrum_name = ""
        #     if CONFIG.extract_massSpectra_use_mz:
        #         mz_kwargs.update(mz_start=mz_start, mz_end=mz_end)
        #         spectrum_name += f"ion={mz_start:.2f}-{mz_end:.2f}"
        #     if CONFIG.extract_massSpectra_use_rt:
        #         mz_kwargs.update(rt_start=rt_start, rt_end=rt_end)
        #         spectrum_name += f" rt={rt_start:.2f}-{rt_end:.2f}"
        #     if CONFIG.extract_massSpectra_use_dt:
        #         mz_kwargs.update(dt_start=dt_start, dt_end=dt_end)
        #         spectrum_name += f" dt={int(dt_start)}-{int(dt_end)}"
        #     spectrum_name = spectrum_name.lstrip()
        #     if mz_kwargs:
        #         logger.info(f"Extracting mass spectrum: {mz_kwargs}")
        #         mz_x, mz_y = self.waters_im_extract_ms(document.path, **mz_kwargs)
        #         self.panel_plot.on_plot_ms(mz_x, mz_y)
        #         data = {"xvals": mz_x, "yvals": mz_y, "xlabels": "m/z (Da)", "xlimits": get_min_max(mz_x)}
        #         if add_to_document:
        #             self.document_tree.on_update_data(data, spectrum_name, document, data_type="extracted.spectrum")
        #         if return_data:
        #             data_storage[spectrum_name] = {
        #                 "name": spectrum_name,
        #                 "data_type": "extracted.spectrum",
        #                 "data": data,
        #                 "type": "mass spectrum",
        #             }
        #
        # # extract chromatogram
        # if CONFIG.extract_chromatograms:
        #     rt_kwargs = dict()
        #     chrom_name = ""
        #     if CONFIG.extract_chromatograms_use_mz:
        #         rt_kwargs.update(mz_start=mz_start, mz_end=mz_end)
        #         chrom_name += f"ion={mz_start:.2f}-{mz_end:.2f}"
        #     if CONFIG.extract_chromatograms_use_dt:
        #         rt_kwargs.update(dt_start=dt_start, dt_end=dt_end)
        #         chrom_name += f" rt={rt_start:.2f}-{rt_end:.2f}"
        #     chrom_name = chrom_name.lstrip()
        #     if rt_kwargs:
        #         logger.info(f"Extracting chromatogram: {rt_kwargs}")
        #         xvals_RT, yvals_RT, __ = self.waters_im_extract_rt(document.path, **rt_kwargs)
        #         self.panel_plot.on_plot_rt(xvals_RT, yvals_RT, "Scans")
        #         data = {
        #             "xvals": xvals_RT,
        #             "yvals": yvals_RT,
        #             "xlabels": "Scans",
        #             "ylabels": "Intensity",
        #             "xlimits": get_min_max(xvals_RT),
        #         }
        #         if add_to_document:
        #             self.document_tree.on_update_data(data, chrom_name, document, data_type="extracted.chromatogram")
        #         if return_data:
        #             data_storage[chrom_name] = {
        #                 "name": chrom_name,
        #                 "data_type": "extracted.chromatogram",
        #                 "data": data,
        #                 "type": "chromatogram",
        #             }
        #
        # # extract mobilogram
        # if CONFIG.extract_driftTime1D:
        #     dt_kwargs = dict()
        #     dt_name = ""
        #     if CONFIG.extract_driftTime1D_use_mz:
        #         dt_kwargs.update(mz_start=mz_start, mz_end=mz_end)
        #         dt_name += f"ion={mz_start:.2f}-{mz_end:.2f}"
        #     if CONFIG.extract_driftTime1D_use_rt:
        #         dt_kwargs.update(rt_start=rt_start, rt_end=rt_end)
        #         dt_name += f" rt={rt_start:.2f}-{rt_end:.2f}"
        #
        #     dt_name = dt_name.lstrip()
        #     if dt_kwargs:
        #         logger.info(f"Extracting mobilogram: {dt_kwargs}")
        #         xvals_DT, yvals_DT = self.waters_im_extract_dt(document.path, **dt_kwargs)
        #         self.panel_plot.on_plot_1d(xvals_DT, yvals_DT, "Drift time (bins)")
        #         data = {
        #             "xvals": xvals_DT,
        #             "yvals": yvals_DT,
        #             "xlabels": "Drift time (bins)",
        #             "ylabels": "Intensity",
        #             "xlimits": get_min_max(xvals_DT),
        #         }
        #         if add_to_document:
        #             self.document_tree.on_update_data(data, dt_name, document, data_type="ion.mobilogram.raw")
        #         if return_data:
        #             data_storage[dt_name + " [1D]"] = {
        #                 "name": dt_name,
        #                 "data_type": "ion.mobilogram.raw",
        #                 "data": data,
        #                 "type": "mobilogram",
        #             }
        #
        # # extract heatmap
        # if CONFIG.extract_driftTime2D:
        #     heatmap_kwargs = dict()
        #     dt_name = ""
        #     if CONFIG.extract_driftTime2D_use_mz:
        #         heatmap_kwargs.update(mz_start=mz_start, mz_end=mz_end)
        #         dt_name += f"ion={mz_start:.2f}-{mz_end:.2f}"
        #     if CONFIG.extract_driftTime2D_use_rt:
        #         heatmap_kwargs.update(rt_start=rt_start, rt_end=rt_end)
        #         dt_name += f" rt={rt_start:.2f}-{rt_end:.2f}"
        #
        #     dt_name = dt_name.lstrip()
        #     if heatmap_kwargs:
        #         logger.info(f"Extracting heatmap: {heatmap_kwargs}")
        #         xvals, yvals, zvals = self.waters_im_extract_heatmap(document.path, **heatmap_kwargs)
        #         self.panel_plot.on_plot_2D_data(data=[zvals, xvals, "Scans", yvals, "Drift time (bins)"])
        #         __, yvals_RT, __ = self.waters_im_extract_rt(document.path, **kwargs)
        #         __, yvals_DT = self.waters_im_extract_dt(document.path, **kwargs)
        #         data = {
        #             "zvals": zvals,
        #             "xvals": xvals,
        #             "xlabels": "Scans",
        #             "yvals": yvals,
        #             "ylabels": "Drift time (bins)",
        #             "cmap": CONFIG.currentCmap,
        #             "yvals1D": yvals_DT,
        #             "yvalsRT": yvals_RT,
        #             "title": "",
        #             "label": "",
        #             "charge": 1,
        #             "alpha": CONFIG.overlay_defaultAlpha,
        #             "mask": CONFIG.overlay_defaultMask,
        #             "color": get_random_color(),
        #             "min_threshold": 0,
        #             "max_threshold": 1,
        #             "xylimits": [mz_start, mz_end, 1],
        #         }
        #         if add_to_document:
        #             self.document_tree.on_update_data(data, dt_name, document, data_type="ion.heatmap.raw")
        #         if return_data:
        #             data_storage[dt_name + " [2D]"] = {
        #                 "name": dt_name,
        #                 "data_type": "ion.heatmap.raw",
        #                 "data": data,
        #                 "type": "heatmap",
        #             }
        #
        # # return data
        # if return_data and len(data_storage) > 0:
        #     pub.sendMessage("extract.data.user", data=data_storage)
        #     return data_storage

    def on_add_ion_ORIGAMI(self, item_information, document, path, mz_start, mz_end, mz_y_max, ion_name, label, charge):
        kwargs = dict(mz_start=mz_start, mz_end=mz_end)
        # 1D
        try:
            __, yvals_DT = self.waters_im_extract_dt(path, **kwargs)
        except IOError:
            msg = (
                "Failed to open the file - most likely because this file no longer exists"
                + " or has been moved. You can change the document path by right-clicking\n"
                + " on the document in the Document Tree and \n"
                + " selecting Notes, Information, Labels..."
            )
            raise MessageError("Missing folder", msg)

        # RT
        __, yvals_RT, __ = self.waters_im_extract_rt(path, **kwargs)

        # 2D
        xvals, yvals, zvals = self.waters_im_extract_heatmap(path, **kwargs)

        # Add data to document object
        ion_data = {
            "zvals": zvals,
            "xvals": xvals,
            "xlabels": "Scans",
            "yvals": yvals,
            "ylabels": "Drift time (bins)",
            "cmap": item_information.get("colormap", next(CONFIG.overlay_cmap_cycle)),
            "yvals1D": yvals_DT,
            "yvalsRT": yvals_RT,
            "title": label,
            "label": label,
            "charge": charge,
            "alpha": item_information["alpha"],
            "mask": item_information["mask"],
            "color": item_information["color"],
            "min_threshold": item_information["min_threshold"],
            "max_threshold": item_information["max_threshold"],
            "xylimits": [mz_start, mz_end, mz_y_max],
        }

        self.document_tree.on_update_data(ion_data, ion_name, document, data_type="ion.heatmap.raw")

    def on_add_ion_MANUAL(
        self, item_information, document, mz_start, mz_end, mz_y_max, ion_name, ion_id, charge, label
    ):
        # TODO: FIXME
        # TODO: add checks for paths
        # TODO: cleanup this function to reduce complexity
        pass
        # self.filesList.on_sort(2, False)
        # tempDict = {}
        # for item in range(self.filesList.GetItemCount()):
        #     # Determine whether the title of the document matches the title of the item in the table
        #     # if it does not, skip the row
        #     docValue = self.filesList.GetItem(item, CONFIG.multipleMLColNames["document"]).GetText()
        #     if docValue != document.title:
        #         continue
        #
        #     nameValue = self.filesList.GetItem(item, CONFIG.multipleMLColNames["filename"]).GetText()
        #     try:
        #         path = document.multipleMassSpectrum[nameValue]["path"]
        #         dt_x, dt_y = self.waters_im_extract_dt(path, mz_start=mz_start, mz_end=mz_end)
        #     # if the files were moved, we can at least try to with the document path
        #     except IOError:
        #         try:
        #             path = os.path.join(document.path, nameValue)
        #             dt_x, dt_y = self.waters_im_extract_dt(path, mz_start=mz_start, mz_end=mz_end)
        #             document.multipleMassSpectrum[nameValue]["path"] = path
        #         except Exception:
        #             msg = (
        #                 "It would appear ORIGAMI cannot find the file on your disk. You can try to fix this issue\n"
        #                 + "by updating the document path by right-clicking on the document and selecting\n"
        #                 + "'Notes, Information, Labels...' and updating the path to where the dataset is found.\n"
        #                 + "After that, try again and ORIGAMI will try to stitch the new"
        #                 + " document path with the file name.\n"
        #             )
        #             raise MessageError("Error", msg)
        #
        #     # Get height of the peak
        #     self.ionPanel.on_update_value_in_peaklist(ion_id, "method", "Manual")
        #
        #     # Create temporary dictionary for all IMS data
        #     tempDict[nameValue] = [dt_y]
        #     # Add 1D data to 1D data container
        #     newName = "{}, File: {}".format(ion_name, nameValue)
        #
        #     ion_data = {
        #         "xvals": dt_x,
        #         "yvals": dt_y,
        #         "xlabels": "Drift time (bins)",
        #         "ylabels": "Intensity",
        #         "charge": charge,
        #         "xylimits": [mz_start, mz_end, mz_y_max],
        #         "filename": nameValue,
        #     }
        #     self.document_tree.on_update_data(ion_data, newName, document, data_type="ion.mobilogram")
        #
        # # Combine the contents in the dictionary - assumes they are ordered!
        # counter = 0  # needed to start off
        # x_labels_actual = []
        # _temp_array = None
        # for counter, item in enumerate(range(self.filesList.GetItemCount()), 1):
        #     # Determine whether the title of the document matches the title of the item in the table
        #     # if it does not, skip the row
        #     docValue = self.filesList.GetItem(item, CONFIG.multipleMLColNames["document"]).GetText()
        #     if docValue != document.title:
        #         continue
        #     key = self.filesList.GetItem(item, CONFIG.multipleMLColNames["filename"]).GetText()
        #     energy = str2num(document.multipleMassSpectrum[key]["trap"])
        #     if _temp_array is None:
        #         _temp_array = tempDict[key][0]
        #     imsList = tempDict[key][0]
        #     _temp_array = np.concatenate((_temp_array, imsList), axis=0)
        #     x_labels_actual.append(energy)
        #
        # # Reshape data to form a 2D array of size 200 x number of files
        # zvals = _temp_array.reshape((200, counter), order="F")
        #
        # try:
        #     x_label_high = np.max(x_labels_actual)
        #     x_label_low = np.min(x_labels_actual)
        # except Exception:
        #     x_label_low, x_label_high = None, None
        #
        # # Get the x-axis labels
        # if x_label_low in [None, "None"] or x_label_high in [None, "None"]:
        #     msg = (
        #         "The user-specified labels appear to be 'None'. Rather than failing to generate x-axis labels"
        #         + " a list of 1-n values is created."
        #     )
        #     logger.warning(msg)
        #     xvals = np.arange(1, counter)
        # else:
        #     xvals = x_labels_actual  # np.linspace(xLabelLow, xLabelHigh, num=counter)
        #
        # yvals = 1 + np.arange(200)
        # if not check_axes_spacing(xvals):
        #     msg = (
        #         "The spacing between the energy variables is not even. Linear interpolation will be performed to"
        #         + " ensure even spacing between values."
        #     )
        #     self.update_statusbar(msg, field=4)
        #     logger.warning(msg)
        #
        #     xvals, yvals, zvals = pr_heatmap.equalize_heatmap_spacing(xvals, yvals, zvals)
        #
        # # Combine 2D array into 1D
        # rt_y = np.sum(zvals, axis=0)
        # dt_y = np.sum(zvals, axis=1).T
        #
        # # Add data to the document
        # ion_data = {
        #     "zvals": zvals,
        #     "xvals": xvals,
        #     "xlabels": "Collision Voltage (V)",
        #     "yvals": yvals,
        #     "ylabels": "Drift time (bins)",
        #     "yvals1D": dt_y,
        #     "yvalsRT": rt_y,
        #     "cmap": document.colormap,
        #     "title": label,
        #     "label": label,
        #     "charge": charge,
        #     "alpha": item_information["alpha"],
        #     "mask": item_information["mask"],
        #     "color": item_information["color"],
        #     "min_threshold": item_information["min_threshold"],
        #     "max_threshold": item_information["max_threshold"],
        #     "xylimits": [mz_start, mz_end, mz_y_max],
        # }
        #
        # self.document_tree.on_update_data(ion_data, ion_name, document, data_type="ion.heatmap.combined")

    def on_add_mzident_file_fcn(self, evt):
        """Load tandem annotation data in mzIdent format"""
        if not CONFIG.APP_ENABLE_THREADING:
            self.on_add_mzident_file(evt)
        else:
            self.on_threading(action="load.add.mzidentml", args=(evt,))

    def on_add_mzident_file(self, evt):
        from origami.readers import io_mzid

        document = self.on_get_document()

        dlg = wx.FileDialog(
            self.presenter.view,
            "Open mzIdentML file",
            wildcard="*.mzid; *.mzid.gz; *mzid.zip",
            style=wx.FD_DEFAULT_STYLE | wx.FD_CHANGE_DIR,
        )
        if dlg.ShowModal() == wx.ID_OK:
            logger.info("Adding identification information to {}".format(document.title))
            t_start = time.time()
            path = dlg.GetPath()
            reader = io_mzid.MZIdentReader(filename=path)

            # check if data reader is present
            try:
                index_dict = document.file_reader["data_reader"].create_title_map(document.tandem_spectra)
            except KeyError:
                logger.warning("Missing file reader. Creating a new instance of the reader...")
                if document.fileFormat == "Format: .mgf":
                    from origami.readers import io_mgf

                    document.file_reader["data_reader"] = io_mgf.MGFReader(filename=document.path)
                elif document.fileFormat == "Format: .mzML":
                    from origami.readers import io_mzml

                    document.file_reader["data_reader"] = io_mzml.mzMLReader(filename=document.path)
                else:
                    DialogBox(
                        title="Error",
                        msg="{} not supported yet!".format(document.fileFormat),
                        kind="Error",
                        show_exception=True,
                    )
                    return
                try:
                    index_dict = document.file_reader["data_reader"].create_title_map(document.tandem_spectra)
                except AttributeError:
                    DialogBox(
                        title="Error",
                        msg="Cannot add identification information to {} yet!".format(document.fileFormat),
                        kind="Error",
                        show_exception=True,
                    )
                    return

            tandem_spectra = reader.match_identification_with_peaklist(
                peaklist=copy.deepcopy(document.tandem_spectra), index_dict=index_dict
            )

            document.tandem_spectra = tandem_spectra

            self.on_update_document(document, "document")
            logger.info(f"It took {time.time()-t_start:.4f} seconds to annotate {document.title}")

    def on_extract_2D_from_mass_range_fcn(self, evt, extract_type="all"):
        """
        Extract 2D array for each m/z range specified in the table
        """
        evt = extract_type if evt is None else "all"

        if not CONFIG.APP_ENABLE_THREADING:
            self.on_extract_2D_from_mass_range(evt)
        else:
            args = (evt,)
            self.on_threading(action="extract.heatmap", args=args)

    # def on_extract_2D_from_mass_range(self, extract_type="all"):
    #     """ extract multiple ions = threaded """
    #
    #     # first check how many items need extracting
    #     n_items = self.ionList.GetItemCount()
    #
    #     n_extracted = 0
    #     for ion_id in range(self.ionList.GetItemCount()):
    #         # Extract ion name
    #         item_information = self.ionPanel.on_get_item_information(item_id=ion_id)
    #         document_title = item_information["document"]
    #
    #         # Check if the ion has been assigned a filename
    #         if document_title == "":
    #             self.update_statusbar("File name column was empty. Using the current document name instead", 4)
    #             document = self.on_get_document()
    #             document_title = document.title
    #             self.ionPanel.on_update_value_in_peaklist(ion_id, "document", document_title)
    #
    #         document = self.on_get_document(document_title)
    #         path = document.path
    #         path = check_waters_path(path)
    #
    #         if not check_path_exists(path) and document.dataType != "Type: MANUAL":
    #             raise MessageError(
    #                 "Missing file",
    #                 f"File with {path} path no longer exists. If you think this is a mistake"
    #                 + ", please update the path by right-clicking on the document in the Document Tree"
    #                 + " and selecting `Notes, information, labels...` and update file path",
    #             )
    #
    #         # Extract information from the table
    #         mz_y_max = item_information["intensity"]
    #         label = item_information["label"]
    #         charge = item_information["charge"]
    #         ion_name = item_information["ion_name"]
    #         mz_start, mz_end = ut_labels.get_ion_name_from_label(ion_name, as_num=True)
    #
    #         if charge is None:
    #             charge = 1
    #
    #         # Create range name
    #         ion_name = item_information["ionName"]
    #
    #         # get spectral parameters
    #         __, __, xlimits = self._get_spectrum_parameters(document)
    #
    #         # Check that the mzStart/mzEnd are above the acquire MZ value
    #         if mz_start < xlimits[0]:
    #             self.ionList.ToggleItem(index=ion_id)
    #             raise MessageError(
    #                 "Error",
    #                 f"Ion: {ion_name} was below the minimum value in the mass spectrum."
    #                 + " Consider removing it from the list",
    #             )
    #
    #         # Check whether this ion was already extracted
    #         if extract_type == "new" and document.gotExtractedIons:
    #             if ion_name in document.IMS2Dions:
    #                 logger.info(f"Data was already extracted for the : {ion_name} ion")
    #                 n_items -= 1
    #                 continue
    #         elif extract_type == "new" and document.gotCombinedExtractedIons:
    #             if ion_name in document.IMS2DCombIons:
    #                 logger.info(f"Data was already extracted for the : {ion_name} ion")
    #                 n_items -= 1
    #                 continue
    #
    #         # Extract selected ions
    #         if extract_type == "selected" and not self.ionList.IsChecked(index=ion_id):
    #             n_items -= 1
    #             continue
    #
    #         if document.dataType == "Type: ORIGAMI":
    #             self.on_add_ion_ORIGAMI(
    #                 item_information, document, path, mz_start, mz_end, mz_y_max, ion_name, label, charge
    #             )
    #         # Check if manual dataset
    #         elif document.dataType == "Type: MANUAL":
    #             self.on_add_ion_MANUAL(
    #                 item_information, document, mz_start, mz_end, mz_y_max, ion_name, ion_id, charge, label
    #             )
    #         # check if infrared type document
    #         elif document.dataType == "Type: Infrared":
    #             self.on_add_ion_IR(item_information, document, path, mz_start, mz_end, ion_name, ion_id,
    #             charge, label)
    #
    #         n_extracted += 1
    #         self.update_statusbar(f"Extracted: {n_extracted}/{n_items}", 4)

    def on_open_manual_file_fcn(self, document_title, filelist, raw_format="waters", **kwargs):
        """Import multi-file ciu/sid document"""
        pub.sendMessage("widget.manual.import.progress", is_running=True, message="")
        # get document
        document = ENV[document_title]
        if not document:
            raise ValueError("Please create new document or select one from the list")

        if not CONFIG.APP_ENABLE_THREADING:
            self.on_setup_basic_document(self.load_manual_document(document.path, filelist, **kwargs))
        else:
            self.add_task(
                self.load_manual_document,
                (document.path, filelist),
                func_result=self.on_setup_basic_document,
                func_post=pub.sendMessage,
                func_post_args=("widget.manual.import.progress",),
                func_post_kwargs=dict(is_running=False, message=""),
                **kwargs,
            )

    def on_open_lesa_file_fcn(self, document_title, filelist, raw_format="waters", **kwargs):
        """Import multi-file LESA document"""
        pub.sendMessage("widget.imaging.import.progress", is_running=True, message="")
        # get document
        document = ENV[document_title]
        if not document:
            raise ValueError("Please create new document or select one from the list")

        if not CONFIG.APP_ENABLE_THREADING:
            self.on_setup_basic_document(self.load_lesa_document(document.path, filelist, **kwargs))
        else:
            self.add_task(
                self.load_lesa_document,
                (document.path, filelist),
                func_result=self.on_setup_basic_document,
                func_post=pub.sendMessage,
                func_post_args=("widget.imaging.import.progress",),
                func_post_kwargs=dict(is_running=False, message=""),
                **kwargs,
            )

    def on_update_document(self, document, expand_item="document", expand_item_title=None):

        # update dictionary
        ENV[document.title] = document
        if expand_item == "document":
            self.document_tree.add_document(document, expand_item=document)
        # just set data
        elif expand_item == "no_refresh":
            self.document_tree.set_document(document_old=ENV[document.title], document_new=document)
        else:
            self.document_tree.add_document(document, expand_item=expand_item)

    # def on_update_DTMS_zoom(self, xmin, xmax, ymin, ymax):
    #     """Event driven data sub-sampling
    #
    #     Parameters
    #     ----------
    #     xmin: float
    #         mouse-event minimum in x-axis
    #     xmax: float
    #         mouse-event maximum in x-axis
    #     ymin: float
    #         mouse-event minimum in y-axis
    #     ymax: float
    #         mouse-event maximum in y-axis
    #     """
    #     tstart = time.time()
    #     # get data
    #     xvals = copy.deepcopy(CONFIG.replotData["DT/MS"].get("xvals", None))
    #     yvals = copy.deepcopy(CONFIG.replotData["DT/MS"].get("yvals", None))
    #     zvals = copy.deepcopy(CONFIG.replotData["DT/MS"].get("zvals", None))
    #     xlabel = copy.deepcopy(CONFIG.replotData["DT/MS"].get("xlabels", None))
    #     ylabel = copy.deepcopy(CONFIG.replotData["DT/MS"].get("ylabels", None))
    #     # check if data type is correct
    #     if zvals is None:
    #         logger.error("Cannot complete action as plotting data is empty")
    #         return
    #
    #     # reduce size of the array to match data extraction window
    #     xmin_idx, xmax_idx = find_nearest_index(xvals, xmin), find_nearest_index(xvals, xmax)
    #     ymin_idx, ymax_idx = find_nearest_index(yvals, ymin), find_nearest_index(yvals, ymax)
    #     zvals = zvals[ymin_idx:ymax_idx, xmin_idx:xmax_idx]
    #     xvals = xvals[xmin_idx:xmax_idx]
    #     yvals = yvals[ymin_idx : ymax_idx + 1]
    #
    #     # check if user enabled smart zoom (ON by default)
    #     if CONFIG.smart_zoom_enable:
    #         xvals, zvals = self.data_processing.downsample_array(xvals, zvals)
    #
    #     # check if selection window is large enough
    #     if np.prod(zvals.shape) == 0:
    #         logger.error("You must select wider dt/mz range to continue")
    #         return
    #     # replot
    #     self.panel_plot.on_plot_dtms(zvals, xvals, yvals, xlabel, ylabel, override=False, update_extents=False)
    #     logger.info("Sub-sampling took {:.4f}".format(time.time() - tstart))
    #
    # def on_combine_mass_spectra(self, document_name=None):
    #
    #     document = self.on_get_document(document_name)
    #     if document is None:
    #         raise ValueError("Did not get document")
    #
    #     kwargs = {
    #         "auto_range": False,
    #         "mz_min": CONFIG.ms_mzStart,
    #         "mz_max": CONFIG.ms_mzEnd,
    #         "mz_bin": CONFIG.ms_mzBinSize,
    #         "linearization_mode": CONFIG.ms_linearization_mode,
    #     }
    #     msg = "Linearization method: {} | min: {} | max: {} | window: {} | auto-range: {}".format(
    #         CONFIG.ms_linearization_mode,
    #         CONFIG.ms_mzStart,
    #         CONFIG.ms_mzEnd,
    #         CONFIG.ms_mzBinSize,
    #         CONFIG.ms_auto_range,
    #     )
    #     logger.info(msg)
    #
    #     if document.multipleMassSpectrum:
    #         # check the min/max values in the mass spectrum
    #         if CONFIG.ms_auto_range:
    #             mzStart, mzEnd = pr_spectra.check_mass_range(ms_dict=document.multipleMassSpectrum)
    #             CONFIG.ms_mzStart = mzStart
    #             CONFIG.ms_mzEnd = mzEnd
    #             kwargs.update(mz_min=mzStart, mz_max=mzEnd)
    #             try:
    #                 self.view.panelProcessData.on_update_GUI(update_what="mass_spectra")
    #             except Exception:
    #                 pass
    #
    #         msFilenames = ["m/z"]
    #         counter = 0
    #         for key in document.multipleMassSpectrum:
    #             msFilenames.append(key)
    #             if counter == 0:
    #                 msDataX, tempArray = pr_spectra.linearize_data(
    #                     document.multipleMassSpectrum[key]["xvals"],
    #                     document.multipleMassSpectrum[key]["yvals"],
    #                     **kwargs,
    #                 )
    #                 msList = tempArray
    #             else:
    #                 msDataX, msList = pr_spectra.linearize_data(
    #                     document.multipleMassSpectrum[key]["xvals"],
    #                     document.multipleMassSpectrum[key]["yvals"],
    #                     **kwargs,
    #                 )
    #                 tempArray = np.concatenate((tempArray, msList), axis=0)
    #             counter += 1
    #
    #         # Reshape the list
    #         combMS = tempArray.reshape((len(msList), int(counter)), order="F")
    #
    #         # Sum y-axis data
    #         msDataY = np.sum(combMS, axis=1)
    #         msDataY = pr_spectra.normalize_1D(msDataY)
    #         xlimits = [document.parameters["start_ms"], document.parameters["end_ms"]]
    #
    #         # Form pandas dataframe
    #         combMSOut = np.concatenate((msDataX, tempArray), axis=0)
    #         combMSOut = combMSOut.reshape((len(msList), int(counter + 1)), order="F")
    #
    #         # Add data
    #         document.gotMS = True
    #         document.massSpectrum = {"xvals": msDataX, "yvals": msDataY, "xlabels": "m/z (Da)", "xlimits": xlimits}
    #         # Plot
    #         name_kwargs = {"document": document.title, "dataset": "Mass Spectrum"}
    #         self.panel_plot.on_plot_ms(msDataX, msDataY, xlimits=xlimits, **name_kwargs)
    #
    #         # Update status bar with MS range
    #         self.view.SetStatusText("{}-{}".format(document.parameters["start_ms"], document.parameters["end_ms"]), 1)
    #         self.view.SetStatusText("MSMS: {}".format(document.parameters["set_msms"]), 2)
    #     else:
    #         document.gotMS = False
    #         document.massSpectrum = {}
    #         self.view.SetStatusText("", 1)
    #         self.view.SetStatusText("", 2)
    #
    #     # Add info to document
    #     self.on_update_document(document, "document")

    def get_spectrum_data(self, query_info, **kwargs):
        """Retrieve data for specified query items.

        Parameters
        ----------
        query_info: list
             query should be formed as a list containing two elements [document title, dataset title]

        Returns
        -------
        document: document object
        data: dictionary
            dictionary with all data associated with the [document, dataset] combo
        """

        if len(query_info) == 3:
            document_title, dataset_type, dataset_name = query_info
        else:
            document_title, dataset_name = query_info
            if dataset_name in ["Mass Spectrum", "Mass Spectrum (processed)", "Mass Spectra"]:
                dataset_type = dataset_name
            else:
                dataset_type = "Mass Spectra"

        document, data = self.get_mobility_chromatographic_data([document_title, dataset_type, dataset_name])
        return document, data

    def get_mobility_chromatographic_data(self, query_info, as_copy=True, **kwargs):
        """Retrieve data for specified query items.

        Parameters
        ----------
        query_info : list
             query should be formed as a list containing two elements [document title, dataset type, dataset title]
        as_copy : bool
            if True, data will be returned as deepcopy, otherwise not (default: True)

        Returns
        -------
        document: document object
        data: dictionary
            dictionary with all data associated with the [document title, dataset type, dataset title] combo
        """

        def get_subset_or_all(dataset_type, dataset_name, dataset):
            """Check whether entire dataset of all subdatasets should be returned or simply one subset"""
            if dataset_type == dataset_name:
                return dataset
            else:
                return dataset[dataset_name]

        document_title, dataset_type, dataset_name = query_info
        document = ENV.on_get_document(document_title)

        if "/" not in dataset_name:
            raise ValueError("Incorrect query arguments")
        data = document[dataset_name, True]

        if as_copy:
            data = copy.deepcopy(data)

        return document, data

    def set_mobility_chromatographic_keyword_data(self, query_info, **kwargs):
        """Set keyword(s) data for specified query items.

        Parameters
        ----------
        query_info: list
             query should be formed as a list containing two elements [document title, dataset title]
        kwargs : dict
            dictionary with keyword : value to be set for each item in the query

        Returns
        -------
        document: document object
        """
        raise NotImplementedError("Must reimplement method")

    #         document_title, dataset_type, dataset_name = query_info
    #         document = self.on_get_document(document_title)
    #
    #         for keyword in kwargs:
    #             # MS data
    #             if dataset_type == "Mass Spectrum":
    #                 document.massSpectrum[keyword] = kwargs[keyword]
    #             elif dataset_type == "Mass Spectrum (processed)":
    #                 document.smoothMS[keyword] = kwargs[keyword]
    #             elif dataset_type == "Mass Spectra" and dataset_name not in [None, "Mass Spectra"]:
    #                 document.multipleMassSpectrum[dataset_name][keyword] = kwargs[keyword]
    #             # Drift time (2D) data
    #             elif dataset_type == "Drift time (2D)":
    #                 document.IMS2D[keyword] = kwargs[keyword]
    #             elif dataset_type == "Drift time (2D, processed)":
    #                 document.IMS2Dprocess[keyword] = kwargs[keyword]
    #             elif dataset_type == "Drift time (2D, EIC)" and dataset_name is not None:
    #                 document.IMS2Dions[dataset_name][keyword] = kwargs[keyword]
    #             elif dataset_type == "Drift time (2D, combined voltages, EIC)" and dataset_name is not None:
    #                 document.IMS2DCombIons[dataset_name][keyword] = kwargs[keyword]
    #             elif dataset_type == "Drift time (2D, processed, EIC)" and dataset_name is not None:
    #                 document.IMS2DionsProcess[dataset_name][keyword] = kwargs[keyword]
    #             # overlay input data
    #             elif dataset_type == "Input data" and dataset_name is not None:
    #                 document.IMS2DcompData[dataset_name][keyword] = kwargs[keyword]
    #             # chromatogram data
    #             elif dataset_type == "Chromatogram":
    #                 document.RT[keyword] = kwargs[keyword]
    #             elif dataset_type == "Chromatograms (combined voltages, EIC)" and dataset_name is not None:
    #                 document.IMSRTCombIons[dataset_name][keyword] = kwargs[keyword]
    #             elif dataset_type == "Chromatograms (EIC)" and dataset_name is not None:
    #                 document.multipleRT[dataset_name][keyword] = kwargs[keyword]
    #             # mobilogram data
    #             elif dataset_type == "Drift time (1D)":
    #                 document.DT[keyword] = kwargs[keyword]
    #             elif dataset_type == "Drift time (1D, EIC)" and dataset_name is not None:
    #                 document.multipleDT[dataset_name][keyword] = kwargs[keyword]
    #             elif dataset_type == "Drift time (1D, EIC, DT-IMS)" and dataset_name is not None:
    #                 document.IMS1DdriftTimes[dataset_name][keyword] = kwargs[keyword]
    #             elif dataset_type == "Annotated data" and dataset_name is not None:
    #                 document.other_data[dataset_name][keyword] = kwargs[keyword]
    #             else:
    #                 raise MessageError(
    #                     "Not implemented yet",
    #                     f"Method to handle {dataset_type}, {dataset_name} has not been implemented yet",
    #                 )
    #
    #         return document

    def set_overlay_data(self, query_info, data, **kwargs):
        raise NotImplementedError("Must reimplement method")

    #         document_title, dataset_type, dataset_name = query_info
    #         document = self.on_get_document(document_title)
    #
    #         if data is not None:
    #             if dataset_type == "Statistical" and dataset_name is not None:
    #                 self.document_tree.on_update_data(data, dataset_name, document, data_type="overlay.statistical")
    #             elif dataset_type == "Overlay" and dataset_name is not None:
    #                 self.document_tree.on_update_data(data, dataset_name, document, data_type="overlay.overlay")
    #
    #         return document

    def generate_annotation_list(self, data_type):
        if data_type in ["mass_spectra", "mass_spectrum"]:
            item_list = self.generate_item_list_mass_spectra(output_type="annotations")
        elif data_type == "heatmap":
            item_list = self.generate_item_list_heatmap(output_type="annotations")
        elif data_type == "chromatogram":
            item_list = self.generate_item_list_chromatogram(output_type="annotations")
        elif data_type == "mobilogram":
            item_list = self.generate_item_list_mobilogram(output_type="annotations")

        return item_list

    def generate_item_list(self, data_type="heatmap"):
        """Generate list of items with the current data type(s)"""

        if data_type in ["heatmap", "chromatogram", "mobilogram"]:
            item_list = self.generate_item_list_heatmap()
            if data_type == "chromatogram":
                item_list.extend(self.generate_item_list_chromatogram())
            elif data_type == "mobilogram":
                item_list.extend(self.generate_item_list_mobilogram())
        elif data_type == "mass_spectra":
            item_list = self.generate_item_list_mass_spectra()

        return item_list

    @staticmethod
    def _generate_item_list(output_type: str, all_datasets: List[str], get_overlay_data: Callable, cleanup: Callable):

        all_documents = ENV.get_document_list("all")

        item_list = []
        if output_type in ["annotations", "comparison", "simple_list", "item_list"]:
            item_list = {document_title: list() for document_title in all_documents}

        # iterate over all datasets
        for document_title in all_documents:
            document: DocumentStore = ENV.on_get_document(document_title)

            # iterate over all groups
            for dataset_type in all_datasets:
                dataset_items = document.view_group(dataset_type)

                # iterate over all objects
                for dataset_name in dataset_items:
                    if output_type == "overlay":
                        obj = document[dataset_name, True]
                        item_list.append(get_overlay_data(obj, dataset_type, dataset_type, document_title))
                    elif output_type in ["annotations", "comparison"]:
                        item_list[document_title].append(dataset_name)
                    elif output_type == "simple_list":
                        item_list[document_title].append((dataset_type, dataset_name))
                    elif output_type == "item_list":
                        item_list[document_title].append(dataset_name)

        if output_type == "comparison":
            item_list = cleanup(item_list)

        return item_list

    def generate_item_list_mass_spectra(self, output_type="overlay"):
        """Generate list of items with the correct data type"""

        def get_overlay_data(data: DataObject, dataset_name: str, dataset_type: str, document_title: str):
            """Generate overlay data dictionary"""
            item_out = {
                "dataset_name": dataset_name,
                "dataset_type": dataset_type,
                "document_title": document_title,
                "shape": data.shape,
                "label": data.get("label", ""),
                "color": data.get("color", get_random_color(True)),
                "overlay_order": data.get("overlay_order", ""),
                "processed": True if "processed" in dataset_type else False,
            }
            return item_out

        def cleanup(item_list):
            """Clean-up generated list"""
            document_titles = list(item_list.keys())
            for document_title in document_titles:
                if not item_list[document_title]:
                    item_list.pop(document_title)
            return item_list

        all_datasets = ["MassSpectra"]
        return self._generate_item_list(output_type, all_datasets, get_overlay_data, cleanup)

    def generate_item_list_heatmap(self, output_type="overlay"):
        """Generate list of items with the correct data type"""

        def get_overlay_data(data: DataObject, dataset_name: str, dataset_type: str, document_title: str):
            """Generate overlay data dictionary"""
            item_dict = {
                "dataset_name": dataset_name,
                "dataset_type": dataset_type,
                "document_title": document_title,
                "shape": data["zvals"].shape,
                "cmap": data.get("cmap", CONFIG.heatmap_colormap),
                "label": data.get("label", ""),
                "mask": data.get("mask", CONFIG.overlay_defaultMask),
                "alpha": data.get("alpha", CONFIG.overlay_defaultAlpha),
                "min_threshold": data.get("min_threshold", 0.0),
                "max_threshold": data.get("max_threshold", 1.0),
                "color": data.get("color", get_random_color(True)),
                "overlay_order": data.get("overlay_order", ""),
                "processed": True if "processed" in dataset_type else False,
                "title": data.get("title", ""),
                "header": data.get("header", ""),
                "footnote": data.get("footnote", ""),
            }
            return item_dict

        def cleanup(item_list):
            """Clean-up generated list"""
            return item_list

        all_datasets = ["IonHeatmaps"]
        return self._generate_item_list(output_type, all_datasets, get_overlay_data, cleanup)

    def generate_item_list_msdt(self, output_type="overlay"):
        """Generate list of items with the correct data type"""

        def get_overlay_data(data: DataObject, dataset_name: str, dataset_type: str, document_title: str):
            """Generate overlay data dictionary"""
            item_dict = {
                "dataset_name": dataset_name,
                "dataset_type": dataset_type,
                "document_title": document_title,
                "shape": data["zvals"].shape,
                "cmap": data.get("cmap", CONFIG.heatmap_colormap),
                "label": data.get("label", ""),
                "mask": data.get("mask", CONFIG.overlay_defaultMask),
                "alpha": data.get("alpha", CONFIG.overlay_defaultAlpha),
                "min_threshold": data.get("min_threshold", 0.0),
                "max_threshold": data.get("max_threshold", 1.0),
                "color": data.get("color", get_random_color(True)),
                "overlay_order": data.get("overlay_order", ""),
                "processed": True if "processed" in dataset_type else False,
                "title": data.get("title", ""),
                "header": data.get("header", ""),
                "footnote": data.get("footnote", ""),
            }
            return item_dict

        def cleanup(item_list):
            """Clean-up generated list"""
            return item_list

        all_datasets = ["MSDTHeatmaps"]
        return self._generate_item_list(output_type, all_datasets, get_overlay_data, cleanup)

    def generate_item_list_chromatogram(self, output_type="overlay"):
        """Generate list of items with the correct data type"""

        def get_overlay_data(data: DataObject, dataset_name: str, dataset_type: str, document_title: str):
            """Generate overlay data dictionary"""
            item_dict = {
                "dataset_name": dataset_name,
                "dataset_type": dataset_type,
                "document_title": document_title,
                "shape": data["xvals"].shape,
                "label": data.get("label", ""),
                "color": data.get("color", get_random_color(True)),
                "overlay_order": data.get("overlay_order", ""),
                "processed": True if "processed" in dataset_type else False,
                "title": data.get("title", ""),
                "header": data.get("header", ""),
                "footnote": data.get("footnote", ""),
            }
            return item_dict

        def cleanup(item_list):
            """Clean-up generated list"""
            return item_list

        all_datasets = ["Chromatograms"]
        return self._generate_item_list(output_type, all_datasets, get_overlay_data, cleanup)

    def generate_item_list_mobilogram(self, output_type="overlay"):
        """Generate list of items with the correct data type"""

        def get_overlay_data(data: DataObject, dataset_name: str, dataset_type: str, document_title: str):
            """Generate overlay data dictionary"""
            item_dict = {
                "dataset_name": dataset_name,
                "dataset_type": dataset_type,
                "document_title": document_title,
                "shape": data["xvals"].shape,
                "label": data.get("label", ""),
                "color": data.get("color", get_random_color(True)),
                "overlay_order": data.get("overlay_order", ""),
                "processed": True if "processed" in dataset_type else False,
                "title": data.get("title", ""),
                "header": data.get("header", ""),
                "footnote": data.get("footnote", ""),
            }
            return item_dict

        def cleanup(item_list):
            """Clean-up generated list"""
            return item_list

        all_datasets = ["Mobilograms"]
        return self._generate_item_list(output_type, all_datasets, get_overlay_data, cleanup)

    def on_load_user_list_fcn(self, **kwargs):
        wildcard = (
            "CSV (Comma delimited) (*.csv)|*.csv|"
            + "Text (Tab delimited) (*.txt)|*.txt|"
            + "Text (Space delimited (*.txt)|*.txt"
        )
        dlg = wx.FileDialog(
            self.view, "Load text file...", wildcard=wildcard, style=wx.FD_DEFAULT_STYLE | wx.FD_CHANGE_DIR
        )
        if dlg.ShowModal() == wx.ID_OK:
            file_path = dlg.GetPath()

            peaklist = self.on_load_user_list(file_path, **kwargs)

            return peaklist

    def on_load_user_list(self, file_path, data_type="peaklist"):
        if data_type == "peaklist":
            peaklist = io_text_files.text_peaklist_open(file_path)
        elif data_type == "annotations":
            raise MessageError("Not implemented yet", "Method is not implemented yet")

        return peaklist

    def on_load_custom_data(self, dataset_type, evt):
        """Load data into interactive document

        Parameters
        ----------
        dataset_type : str
            specifies which routine should be taken to load data
        evt : wx.Event
            unused
        """
        from origami.gui_elements.dialog_ask_override import DialogAskOverride
        from origami.utils.misc import merge_two_dicts

        def check_previous_data(dataset, _filename, _data):
            if _filename in dataset:
                if not CONFIG.import_duplicate_panel_ask:
                    dlg_ask = DialogAskOverride(
                        self.view,
                        self.config,
                        f"{_filename} already exists in the document. What would you like to do about it?",
                    )
                    dlg_ask.ShowModal()
                if CONFIG.import_duplicate_panel_action == "merge":
                    logger.info("Existing data will be merged with the new dataset...")
                    # retrieve and merge
                    old_data = dataset[_filename]
                    _data = merge_two_dicts(old_data, _data)
                elif CONFIG.import_duplicate_panel_action == "duplicate":
                    logger.info("A new dataset with new name will be created...")
                    _filename = f"{_filename} (2)"
            return _filename, _data

        # get document
        dlg = wx.FileDialog(
            self.view,
            "Choose data [MS, RT, DT, Heatmap, other]...",
            wildcard="Text file (*.txt, *.csv, *.tab)| *.txt;*.csv;*.tab",
            style=wx.FD_MULTIPLE | wx.FD_CHANGE_DIR,
        )
        if dlg.ShowModal() == wx.ID_OK:
            path_list = dlg.GetPaths()
            file_list = dlg.GetFilenames()

            # get document
            document = self.on_get_document()

            if not path_list:
                logger.warning("The filelist was empty")
                return

            logger.info(f"{len(path_list)} item(s) in the list")
            for path, filename in zip(path_list, file_list):
                data_type = None
                if dataset_type == "mass_spectra":
                    mz_x, mz_y, __, xlimits, extension = self.load_text_spectrum_data(path=path)
                    document.gotMultipleMS = True
                    data = {
                        "xvals": mz_x,
                        "yvals": mz_y,
                        "xlabels": "m/z (Da)",
                        "xlimits": xlimits,
                        "file_path": path,
                        "file_extension": extension,
                    }
                    filename, data = check_previous_data(document.multipleMassSpectrum, filename, data)
                    document.multipleMassSpectrum[filename] = data
                    data_type = "extracted.spectrum"

                elif dataset_type == "chromatograms":
                    rt_x, rt_y, __, xlimits, extension = self.load_text_spectrum_data(path=path)
                    document.gotMultipleRT = True
                    data = {
                        "xvals": rt_x,
                        "yvals": rt_y,
                        "xlabels": "Scans",
                        "ylabels": "Intensity",
                        "xlimits": xlimits,
                        "file_path": path,
                        "file_extension": extension,
                    }

                    filename, data = check_previous_data(document.multipleRT, filename, data)
                    document.multipleRT[filename] = data
                    data_type = "extracted.chromatogram"

                elif dataset_type == "mobilogram":
                    dt_x, dt_y, __, xlimits, extension = self.load_text_spectrum_data(path=path)
                    data = {
                        "xvals": dt_x,
                        "yvals": dt_y,
                        "xlabels": "Drift time (bins)",
                        "ylabels": "Intensity",
                        "xlimits": xlimits,
                        "file_path": path,
                        "file_extension": extension,
                    }

                    filename, data = check_previous_data(document.multipleDT, filename, data)
                    document.multipleDT[filename] = data
                    data_type = "ion.mobilogram.raw"

                elif dataset_type == "heatmaps":
                    zvals, xvals, yvals, dt_y, rt_y = self.load_text_heatmap_data(path)
                    color = convert_rgb_255_to_1(CONFIG.custom_colors[get_random_int(0, 15)])
                    document.gotExtractedIons = True
                    data = {
                        "zvals": zvals,
                        "xvals": xvals,
                        "xlabels": "Scans",
                        "yvals": yvals,
                        "ylabels": "Drift time (bins)",
                        "yvals1D": dt_y,
                        "yvalsRT": rt_y,
                        "cmap": CONFIG.heatmap_colormap,
                        "mask": CONFIG.overlay_defaultMask,
                        "alpha": CONFIG.overlay_defaultAlpha,
                        "min_threshold": 0,
                        "max_threshold": 1,
                        "color": color,
                    }
                    filename, data = check_previous_data(document.multipleDT, filename, data)
                    document.IMS2Dions[filename] = data
                    data_type = "ion.heatmap.raw"

                elif dataset_type == "annotated":
                    try:
                        filename, data = self.load_text_annotated_data(path)
                        if filename is None or data is None:
                            continue

                        filename, data = check_previous_data(document.other_data, filename, data)
                        document.other_data[filename] = data
                        data_type = "custom.annotated"
                    except Exception:
                        logger.error(f"Failed to load `{path}` data", exc_info=True)

                elif dataset_type == "matrix":
                    from pandas import read_csv

                    df = read_csv(filename, sep="\t|,", engine="python", header=None)
                    labels = list(df.iloc[:, 0].dropna())
                    zvals = df.iloc[1::, 1::].astype("float32").as_matrix()

                    filename = "Matrix: {}".format(os.path.basename(filename))
                    data = {
                        "heatmap_plot_type": "matrix",
                        "zvals": zvals,
                        "cmap": CONFIG.heatmap_colormap,
                        "matrixLabels": labels,
                        "path": filename,
                        "plot_modifiers": {},
                    }
                    filename, data = check_previous_data(document.other_data, filename, data)
                    document.other_data[filename] = data
                    data_type = "custom.annotated"

                self.document_tree.on_update_data(data, filename, document, data_type=data_type)
                # log
                logger.info(f"{dataset_type}: Loaded {path}")
            dlg.Destroy()
