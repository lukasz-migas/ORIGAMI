"""Handler class for UniDec mass deconvolution"""
# Standard library imports
import time
import logging

# Local imports
from origami.utils.secret import get_short_hash
from origami.config.config import CONFIG
from origami.utils.utilities import report_time
from origami.handlers.process import PROCESS_HANDLER
from origami.objects.document import DocumentStore
from origami.objects.containers import MassSpectrumObject
from origami.widgets.unidec.processing.engine import UniDecEngine

LOGGER = logging.getLogger(__name__)


class UniDecHandler:
    """UniDec handler"""

    def __init__(self):
        pass

    @staticmethod
    def unidec_init_engine():
        """Initialize UniDec engine"""
        if CONFIG.unidec_engine is None:
            CONFIG.unidec_engine = UniDecEngine()

    def unidec_initialize(self, mz_obj: MassSpectrumObject, document: DocumentStore):
        """Initialize UniDec engine"""
        LOGGER.debug("UniDec: Started loading data...")

        self.unidec_init_engine()

        filename = mz_obj.dataset_name
        if filename in ["", None]:
            filename = get_short_hash()

        CONFIG.unidec_engine.set_mass_spectrum(mz_obj, filename=filename, output_dir=CONFIG.APP_TEMP_DATA_PATH)
        LOGGER.debug("UniDec: Finished loading data...")

        return CONFIG.unidec_engine.data

    @staticmethod
    def unidec_preprocess():
        """Pre-process mass spectrum"""
        t_start = time.time()
        LOGGER.debug("UniDec: Started pre-processing...")
        # create copy of the mass spectrum object so the data is not overwritten in the Document
        mz_obj = CONFIG.unidec_engine.data.mz_obj.duplicate()
        mz_obj = PROCESS_HANDLER.on_process_ms(mz_obj)
        CONFIG.unidec_engine.process_mass_spectrum(mz_obj)
        LOGGER.debug(f"UniDec: Finished pre-processing in {report_time(t_start)}")

        return CONFIG.unidec_engine.data

    def unidec_initialize_and_preprocess(self, mz_obj: MassSpectrumObject, document: DocumentStore):
        """Initialize UniDec engine and pre-process data"""
        self.unidec_initialize(mz_obj, document)
        self.unidec_preprocess()
        return CONFIG.unidec_engine.data

    @staticmethod
    def unidec_run():
        """Pre-process mass spectrum"""
        t_start = time.time()
        LOGGER.debug("UniDec: Started deconvolution...")
        # this is required so the ORIGAMI-defined parameters are used in the deconvolution
        CONFIG.unidec_engine.config.set_from_origami_config()
        CONFIG.unidec_engine.run_unidec()
        LOGGER.debug(f"UniDec: Finished deconvolution in {report_time(t_start)}")

        return CONFIG.unidec_engine.data

    @staticmethod
    def unidec_find_peaks():
        """Pre-process mass spectrum"""
        t_start = time.time()
        LOGGER.debug("UniDec: Started peak picking...")
        # this is required so the ORIGAMI-defined parameters are used in the deconvolution
        CONFIG.unidec_engine.config.set_from_origami_config()
        CONFIG.unidec_engine.pick_peaks()
        LOGGER.debug(f"UniDec: Finished peak picking in {report_time(t_start)}")

        # convolve peaks
        LOGGER.info("UniDec: Started convolving peaks...")
        try:
            CONFIG.unidec_engine.convolve_peaks()
        except OverflowError as err:
            print(err)
            raise ValueError(
                "Too many peaks! Try again with larger 'Peak detection threshold' or 'Peak detection window (Da).'"
            )
        LOGGER.debug(f"UniDec: Finished convolving in {report_time(t_start)}")

        return CONFIG.unidec_engine.data

    @staticmethod
    def unidec_isolate():
        """Isolate single molecular weight"""
        t_start = time.time()
        LOGGER.info("UniDec: Started isolating MW...")

        try:
            CONFIG.unidec_engine.pick_peaks()
        except (ValueError, ZeroDivisionError):
            raise ValueError(
                "Failed to find peaks. Try increasing the value of 'Peak detection window (Da)'"
                " to be same or larger than 'Sample frequency (Da)'."
            )

        except IndexError as err:
            print(err)
            raise ValueError("Please run UniDec first")

        LOGGER.debug(f"UniDec: Finished isolating MW in {report_time(t_start)}")

    def unidec_autorun(self, mz_obj: MassSpectrumObject, document: DocumentStore):
        """Autorun UniDec"""
        t_start = time.time()
        LOGGER.info("UniDec: Started Autorun...")
        self.unidec_initialize_and_preprocess(mz_obj, document)
        self.unidec_run()
        self.unidec_find_peaks()
        LOGGER.debug(f"UniDec: Finished autorun in {report_time(t_start)}")
        return CONFIG.unidec_engine.data

    # def _unidec_isolate(self):
    #     tstart = time.time()
    #     LOGGER.info("UniDec: Isolating MW...")
    #
    #     try:
    #         CONFIG.unidec_engine.pick_peaks()
    #     except (ValueError, ZeroDivisionError):
    #         msg = (
    #             "Failed to find peaks. Try increasing the value of 'Peak detection window (Da)'"
    #             + "to be same or larger than 'Sample frequency (Da)'."
    #         )
    #         raise ValueError(msg)
    #
    #     except IndexError:
    #         raise ValueError("Please run UniDec first")
    #
    #     LOGGER.info(f"UniDec: Finished isolating a single MW in {time.time()-tstart:.2f} seconds")
    #
    # def _unidec_autorun(self):
    #     t_start = time.time()
    #     LOGGER.info("UniDec: Started Autorun...")
    #     CONFIG.unidec_engine.autorun()
    #     CONFIG.unidec_engine.convolve_peaks()
    #     LOGGER.info(f"UniDec: Finished Autorun in {time.time()-t_start:.2f} seconds")
    #
    # def _unidec_setup_parameters(self):
    #
    #     # set common parameters
    #     CONFIG.unidec_engine.config.numit = CONFIG.unidec_maxIterations
    #
    #     # preprocess
    #     CONFIG.unidec_engine.config.minmz = CONFIG.unidec_mzStart
    #     CONFIG.unidec_engine.config.maxmz = CONFIG.unidec_mzEnd
    #     CONFIG.unidec_engine.config.mzbins = CONFIG.unidec_mzBinSize
    #     CONFIG.unidec_engine.config.smooth = CONFIG.unidec_gaussianFilter
    #     CONFIG.unidec_engine.config.accvol = CONFIG.unidec_accelerationV
    #     CONFIG.unidec_engine.config.linflag = CONFIG.unidec_linearization_choices[CONFIG.unidec_linearization]
    #     CONFIG.unidec_engine.config.cmap = CONFIG.heatmap_colormap
    #
    #     # unidec engine
    #     CONFIG.unidec_engine.config.masslb = CONFIG.unidec_mwStart
    #     CONFIG.unidec_engine.config.massub = CONFIG.unidec_mwEnd
    #     CONFIG.unidec_engine.config.massbins = CONFIG.unidec_mwFrequency
    #     CONFIG.unidec_engine.config.startz = CONFIG.unidec_zStart
    #     CONFIG.unidec_engine.config.endz = CONFIG.unidec_zEnd
    #     CONFIG.unidec_engine.config.numz = CONFIG.unidec_zEnd - CONFIG.unidec_zStart
    #     CONFIG.unidec_engine.config.psfun = CONFIG.unidec_peakFunction_choices[CONFIG.unidec_peakFunction]
    #
    #     # peak finding
    #     CONFIG.unidec_engine.config.peaknorm = CONFIG.unidec_peakNormalization_choices[
    #     CONFIG.unidec_peakNormalization]
    #     CONFIG.unidec_engine.config.peakwindow = CONFIG.unidec_peakDetectionWidth
    #     CONFIG.unidec_engine.config.peakthresh = CONFIG.unidec_peakDetectionThreshold
    #     CONFIG.unidec_engine.separation = CONFIG.unidec_lineSeparation
    #
    # def _check_unidec_input(self, **kwargs):
    #     if "mz_min" in kwargs and "mz_max" in kwargs:
    #         if CONFIG.unidec_mzStart > kwargs["mz_max"]:
    #             CONFIG.unidec_mzStart = np.round(kwargs["mz_min"], 0)
    #
    #         if CONFIG.unidec_mzEnd < kwargs["mz_min"]:
    #             CONFIG.unidec_mzEnd = np.round(kwargs["mz_max"], 0)
    #
    #     if "mz_max" in kwargs:
    #         if CONFIG.unidec_mzEnd > kwargs["mz_max"]:
    #             CONFIG.unidec_mzEnd = np.round(kwargs["mz_max"], 0)
    #
    # def _unidec_initilize(self, document_title, dataset, msX, msY):
    #     LOGGER.info("UniDec: Loading data...")
    #
    #     file_name = "".join([document_title, "_", dataset])
    #     file_name = clean_filename(file_name)
    #     folder = CONFIG.APP_TEMP_DATA_PATH
    #     kwargs = {"clean": True}
    #     CONFIG.unidec_engine.open_file(
    #         file_name=file_name, file_directory=folder, data_in=np.transpose([msX, msY]), **kwargs
    #     )
    #     LOGGER.info("UniDec: Finished loading data...")
    #
    # def _unidec_preprocess(self, dataset):
    #     tstart = ttime()
    #     LOGGER.info("UniDec: Pre-processing...")
    #     # preprocess
    #     try:
    #         CONFIG.unidec_engine.process_data()
    #     except IndexError:
    #         self.on_run_unidec(dataset, task="load_data_unidec")
    #         self.presenter.onThreading(
    #             None, ("No data was loaded. Trying to load it automatically", 4), action="updateStatusbar"
    #         )
    #         return
    #     except ValueError:
    #         msg = (
    #             "Interpolation range is above the 'true' data range."
    #             + "Consider reducing interpolation range to cover the span of the mass spectrum"
    #         )
    #         self.presenter.onThreading(None, (msg, 4), action="updateStatusbar")
    #         DialogBox(title="Error", msg=msg, kind="Error")
    #         return
    #     LOGGER.info(f"UniDec: Finished pre-processing in {ttime()-tstart:.2f} seconds")
    #
    # def _unidec_run(self):
    #     tstart = ttime()
    #     LOGGER.info("UniDec: Deconvoluting...")
    #
    #     if CONFIG.unidec_peakWidth_auto:
    #         CONFIG.unidec_engine.get_auto_peak_width()
    #     else:
    #         CONFIG.unidec_engine.config.mzsig = CONFIG.unidec_peakWidth
    #
    #     try:
    #         CONFIG.unidec_engine.run_unidec()
    #         CONFIG.unidec_peakWidth = CONFIG.unidec_engine.config.mzsig
    #     except IndexError:
    #         raise MessageError("Error", "Please load and pre-process data first")
    #     except ValueError:
    #         self.presenter.onThreading(None, ("Could not perform task", 4), action="updateStatusbar")
    #         return
    #     LOGGER.info(f"UniDec: Finished deconvoluting in {ttime()-tstart:.2f} seconds")
    #
    # def _unidec_find_peaks(self):
    #     tstart = ttime()
    #     LOGGER.info("UniDec: Picking peaks...")
    #
    #     # check if there is data in the dataset
    #     if len(CONFIG.unidec_engine.data.massdat) == 0:
    #         raise MessageError("Incorrect input", "Please `Run UniDec` first as there is missing data")
    #
    #     # pick peaks
    #     try:
    #         CONFIG.unidec_engine.pick_peaks()
    #     except (ValueError, ZeroDivisionError) as err:
    #         print(err)
    #         msg = (
    #             "Failed to find peaks. Try increasing the value of 'Peak detection window (Da)'. "
    #             + "This value should be >= 'Sample frequency (Da)'"
    #         )
    #         raise MessageError("Error", msg)
    #     except IndexError as err:
    #         print(err)
    #         raise MessageError("Error", "Index error. Try reducing value of 'Sample frequency (Da)'")
    #
    #     # convolve peaks
    #     LOGGER.info(f"UniDec: Finished picking peaks in {ttime()-tstart:.2f} seconds")
    #     LOGGER.info("UniDec: Convolving peaks...")
    #     try:
    #         CONFIG.unidec_engine.convolve_peaks()
    #     except OverflowError as err:
    #         print(err)
    #         msg = "Too many peaks! Try again with larger 'Peak detection threshold' or 'Peak detection window (Da).'"
    #         raise MessageError("Error", msg)
    #     LOGGER.info(f"UniDec: Finished convolving peaks in {ttime()-tstart:.2f} seconds")
    #
    # def _unidec_isolate(self):
    #     tstart = ttime()
    #     LOGGER.info("UniDec: Isolating MW...")
    #
    #     try:
    #         CONFIG.unidec_engine.pick_peaks()
    #     except (ValueError, ZeroDivisionError):
    #         msg = (
    #             "Failed to find peaks. Try increasing the value of 'Peak detection window (Da)'"
    #             + "to be same or larger than 'Sample frequency (Da)'."
    #         )
    #         DialogBox(title="Error", msg=msg, kind="Error")
    #         return
    #
    #     except IndexError:
    #         DialogBox(title="Error", msg="Please run UniDec first", kind="Error")
    #         return
    #
    #     LOGGER.info(f"UniDec: Finished isolating a single MW in {ttime()-tstart:.2f} seconds")
    #
    # def _unidec_autorun(self):
    #     tstart = ttime()
    #     LOGGER.info("UniDec: Started Autorun...")
    #     CONFIG.unidec_engine.autorun()
    #     CONFIG.unidec_engine.convolve_peaks()
    #     LOGGER.info(f"UniDec: Finished Autorun in {ttime()-tstart:.2f} seconds")
    #
    # def _unidec_setup_parameters(self):
    #
    #     # set common parameters
    #     CONFIG.unidec_engine.config.numit = CONFIG.unidec_maxIterations
    #
    #     # preprocess
    #     CONFIG.unidec_engine.config.minmz = CONFIG.unidec_mzStart
    #     CONFIG.unidec_engine.config.maxmz = CONFIG.unidec_mzEnd
    #     CONFIG.unidec_engine.config.mzbins = CONFIG.unidec_mzBinSize
    #     CONFIG.unidec_engine.config.smooth = CONFIG.unidec_gaussianFilter
    #     CONFIG.unidec_engine.config.accvol = CONFIG.unidec_accelerationV
    #     CONFIG.unidec_engine.config.linflag = CONFIG.unidec_linearization_choices[CONFIG.unidec_linearization]
    #     CONFIG.unidec_engine.config.cmap = CONFIG.heatmap_colormap
    #
    #     # unidec engine
    #     CONFIG.unidec_engine.config.masslb = CONFIG.unidec_mwStart
    #     CONFIG.unidec_engine.config.massub = CONFIG.unidec_mwEnd
    #     CONFIG.unidec_engine.config.massbins = CONFIG.unidec_mwFrequency
    #     CONFIG.unidec_engine.config.startz = CONFIG.unidec_zStart
    #     CONFIG.unidec_engine.config.endz = CONFIG.unidec_zEnd
    #     CONFIG.unidec_engine.config.numz = CONFIG.unidec_zEnd - CONFIG.unidec_zStart
    #     CONFIG.unidec_engine.config.psfun = CONFIG.unidec_peakFunction_choices[CONFIG.unidec_peakFunction]
    #
    #     # peak finding
    #     CONFIG.unidec_engine.config.peaknorm = CONFIG.unidec_peakNormalization_choices[
    #     CONFIG.unidec_peakNormalization]
    #     CONFIG.unidec_engine.config.peakwindow = CONFIG.unidec_peakDetectionWidth
    #     CONFIG.unidec_engine.config.peakthresh = CONFIG.unidec_peakDetectionThreshold
    #     CONFIG.unidec_engine.separation = CONFIG.unidec_lineSeparation
    #
    # def _calculate_peak_widths(self, chargeList, selectedMW, peakWidth, adductIon="H+"):
    #     _adducts = {
    #         "H+": 1.007276467,
    #         "Na+": 22.989218,
    #         "K+": 38.963158,
    #         "NH4+": 18.033823,
    #         "H-": -1.007276,
    #         "Cl-": 34.969402,
    #     }
    #     min_mz, max_mz = (np.min(CONFIG.unidec_engine.data.data2[:, 0]), np.max(
    #     CONFIG.unidec_engine.data.data2[:, 0]))
    #     charges = np.array(list(map(int, np.arange(chargeList[0, 0], chargeList[-1, 0] + 1))))
    #     peakpos = (float(selectedMW) + charges * _adducts[adductIon]) / charges
    #
    #     ignore = (peakpos > min_mz) & (peakpos < max_mz)
    #     peakpos, charges, intensities = peakpos[ignore], charges[ignore], chargeList[:, 1][ignore]
    #
    #     # calculate min and max value based on the peak width
    #     mw_annotations = {}
    #     for peak, charge, intensity in zip(peakpos, charges, intensities):
    #         min_value = peak - peakWidth / 2.0
    #         max_value = peak + peakWidth / 2.0
    #         label_value = "MW: {}".format(selectedMW)
    #         annotation_dict = {
    #             "min": min_value,
    #             "max": max_value,
    #             "charge": charge,
    #             "intensity": intensity,
    #             "label": label_value,
    #             "color": CONFIG.interactive_ms_annotations_color,
    #         }
    #
    #         name = "{} - {}".format(np.round(min_value, 2), np.round(max_value, 2))
    #         mw_annotations[name] = annotation_dict
    #     return mw_annotations
    #
    # def on_run_unidec_fcn(self, dataset, task, **kwargs):
    #     if not CONFIG.APP_ENABLE_THREADING:
    #         self.on_run_unidec(dataset, task, **kwargs)
    #     else:
    #         self.on_threading(action="process.unidec.run", args=(dataset, task), kwargs=kwargs)
    #
    # def on_run_unidec(self, dataset, task, **kwargs):
    #     """Runner function
    #
    #     Parameters
    #     ----------
    #     dataset : str
    #         type of data to be analysed using UniDec
    #     task : str
    #         task that should be carried out. Different tasks spawn different processes
    #     call_after : bool
    #         will call after function `fcn` with arguments `args` after the main part is executed - takes advantage
    #         of the multi-threaded nature of the runner function
    #     """
    #
    #     # retrive dataset and document
    #     self.unidec_dataset = dataset
    #     data, __, document_title = self.get_unidec_data(data_type="document_all")
    #
    #     # retrieve unidec object
    #     if "temporary_unidec" in data and task not in ["auto_unidec"]:
    #         CONFIG.unidec_engine = data["temporary_unidec"]
    #     else:
    #         CONFIG.unidec_engine = unidec.UniDec()
    #         CONFIG.unidec_engine.config.UniDecPath = CONFIG.APP_UNIDEC_PATH
    #
    #     # check which tasks are carried out
    #     if task in ["auto_unidec", "load_data_unidec", "run_all_unidec", "load_data_and_preprocess_unidec"]:
    #         msX = data["xvals"]
    #         msY = data["yvals"]
    #
    #         check_kwargs = {"mz_min": msX[0], "mz_max": msX[-1]}
    #         self._check_unidec_input(**check_kwargs)
    #
    #     # setup parameters
    #     if task not in ["auto_unidec"]:
    #         self._unidec_setup_parameters()
    #
    #     # load data
    #     if task in ["auto_unidec", "load_data_unidec", "run_all_unidec"]:
    #         self._unidec_initilize(document_title, dataset, msX, msY)
    #
    #     # pre-process
    #     if task in ["run_all_unidec", "preprocess_unidec"]:
    #         self._unidec_preprocess(dataset)
    #
    #     # load and pre-process
    #     if task in ["load_data_and_preprocess_unidec"]:
    #         self._unidec_initilize(document_title, dataset, msX, msY)
    #         self._unidec_preprocess(dataset)
    #
    #     # deconvolute
    #     if task in ["run_all_unidec", "run_unidec"]:
    #         self._unidec_run()
    #
    #     # find peaks
    #     if task in ["run_all_unidec", "pick_peaks_unidec"]:
    #         self._unidec_find_peaks()
    #
    #     # isolate peak
    #     if task in ["isolate_mw_unidec"]:
    #         self._unidec_isolate()
    #
    #     # run auto
    #     if task in ["auto_unidec"]:
    #         self._unidec_autorun()
    #
    #     # add data to document
    #     self.on_add_unidec_data(task, dataset, document_title=document_title)
    #
    #     # add call-after
    #     if kwargs.get("call_after", False):
    #         fcn = kwargs.pop("fcn")
    #         args = kwargs.pop("args")
    #         fcn(args)
    #
    # def on_add_unidec_data(self, task, dataset, document_title=None):
    #     """Convenience function to add data to document"""
    #
    #     document = self.data_handling.on_get_document(document_title)
    #
    #     # initilise data in the mass spectrum dictionary
    #     if dataset == "Mass Spectrum":
    #         if "unidec" not in document.massSpectrum:
    #             document.massSpectrum["unidec"] = {}
    #         data = document.massSpectrum
    #     elif dataset == "Mass Spectrum (processed)":
    #         data = document.smoothMS
    #         if "unidec" not in document.smoothMS:
    #             document.smoothMS["unidec"] = {}
    #     else:
    #         if "unidec" not in document.multipleMassSpectrum[dataset]:
    #             document.multipleMassSpectrum[dataset]["unidec"] = {}
    #         data = document.multipleMassSpectrum[dataset]
    #
    #     # clear old data
    #     if task in ["auto_unidec", "run_all_unidec", "preprocess_unidec", "load_data_and_preprocess_unidec"]:
    #         data["unidec"].clear()
    #
    #     # add processed data
    #     if task in ["auto_unidec", "run_all_unidec", "preprocess_unidec", "load_data_and_preprocess_unidec"]:
    #         raw_data = {
    #             "xvals": CONFIG.unidec_engine.data.data2[:, 0],
    #             "yvals": CONFIG.unidec_engine.data.data2[:, 1],
    #             "color": [0, 0, 0],
    #             "label": "Data",
    #             "xlabels": "m/z",
    #             "ylabels": "Intensity",
    #         }
    #         # add data
    #         data["unidec"]["Processed"] = raw_data
    #
    #     # add fitted and deconvolution data
    #     if task in ["auto_unidec", "run_all_unidec", "run_unidec"]:
    #         fit_data = {
    #             "xvals": [CONFIG.unidec_engine.data.data2[:, 0], CONFIG.unidec_engine.data.data2[:, 0]],
    #             "yvals": [CONFIG.unidec_engine.data.data2[:, 1], CONFIG.unidec_engine.data.fitdat],
    #             "colors": [[0, 0, 0], [1, 0, 0]],
    #             "labels": ["Data", "Fit Data"],
    #             "xlabel": "m/z",
    #             "ylabel": "Intensity",
    #             "xlimits": [
    #                 np.min(CONFIG.unidec_engine.data.data2[:, 0]),
    #                 np.max(CONFIG.unidec_engine.data.data2[:, 0]),
    #             ],
    #         }
    #         mw_distribution_data = {
    #             "xvals": CONFIG.unidec_engine.data.massdat[:, 0],
    #             "yvals": CONFIG.unidec_engine.data.massdat[:, 1],
    #             "color": [0, 0, 0],
    #             "label": "Data",
    #             "xlabels": "Mass (Da)",
    #             "ylabels": "Intensity",
    #         }
    #         mz_grid_data = {
    #             "grid": CONFIG.unidec_engine.data.mzgrid,
    #             "xlabels": " m/z (Da)",
    #             "ylabels": "Charge",
    #             "cmap": CONFIG.unidec_engine.config.cmap,
    #         }
    #         mw_v_z_data = {
    #             "xvals": CONFIG.unidec_engine.data.massdat[:, 0],
    #             "yvals": CONFIG.unidec_engine.data.ztab,
    #             "zvals": CONFIG.unidec_engine.data.massgrid,
    #             "xlabels": "Mass (Da)",
    #             "ylabels": "Charge",
    #             "cmap": CONFIG.unidec_engine.config.cmap,
    #         }
    #         # set data in the document store
    #         data["unidec"]["Fitted"] = fit_data
    #         data["unidec"]["MW distribution"] = mw_distribution_data
    #         data["unidec"]["m/z vs Charge"] = mz_grid_data
    #         data["unidec"]["MW vs Charge"] = mw_v_z_data
    #
    #     # add aux data
    #     if task in ["auto_unidec", "run_all_unidec", "pick_peaks_unidec"]:
    #         # individually plotted
    #         individual_dict = self.get_unidec_data(data_type="Individual MS")
    #         barchart_dict = self.get_unidec_data(data_type="Barchart")
    #         massList, massMax = self.get_unidec_data(data_type="MassList")
    #         individual_dict["_massList_"] = [massList, massMax]
    #
    #         # add data
    #         data["unidec"]["m/z with isolated species"] = individual_dict
    #         data["unidec"]["Barchart"] = barchart_dict
    #         data["unidec"]["Charge information"] = CONFIG.unidec_engine.get_charge_peaks()
    #
    #     # store unidec engine - cannot be pickled, so will be deleted when saving document
    #     data["temporary_unidec"] = CONFIG.unidec_engine
    #
    #     self.document_tree.on_update_unidec(data["unidec"], document_title, dataset)
    #
    # def get_unidec_data(self, data_type="Individual MS", **kwargs):
    #
    #     if data_type == "Individual MS":
    #         stickmax = 1.0
    #         num = 0
    #         individual_dict = dict()
    #         legend_text = [[[0, 0, 0], "Raw"]]
    #         colors, labels = [], []
    #         #             charges = CONFIG.unidec_engine.get_charge_peaks()
    #         for i in range(0, CONFIG.unidec_engine.pks.plen):
    #             p = CONFIG.unidec_engine.pks.peaks[i]
    #             if p.ignore == 0:
    #                 list1, list2 = [], []
    #                 if (not isempty(p.mztab)) and (not isempty(p.mztab2)):
    #                     mztab = np.array(p.mztab)
    #                     mztab2 = np.array(p.mztab2)
    #                     maxval = np.amax(mztab[:, 1])
    #                     for k in range(0, len(mztab)):
    #                         if mztab[k, 1] > CONFIG.unidec_engine.config.peakplotthresh * maxval:
    #                             list1.append(mztab2[k, 0])
    #                             list2.append(mztab2[k, 1])
    #
    #                     if CONFIG.unidec_engine.pks.plen <= 15:
    #                         color = convert_rgb_255_to_1(CONFIG.custom_colors[i])
    #                     else:
    #                         color = p.color
    #                     colors.append(color)
    #                     labels.append("MW: {:.2f}".format(p.mass))
    #                     legend_text.append([color, "MW: {:.2f}".format(p.mass)])
    #
    #                     individual_dict["MW: {:.2f}".format(p.mass)] = {
    #                         "scatter_xvals": np.array(list1),
    #                         "scatter_yvals": np.array(list2),
    #                         "marker": p.marker,
    #                         "color": color,
    #                         "label": "MW: {:.2f}".format(p.mass),
    #                         "line_xvals": CONFIG.unidec_engine.data.data2[:, 0],
    #                         "line_yvals": np.array(p.stickdat) / stickmax
    #                         - (num + 1) * CONFIG.unidec_engine.config.separation,
    #                     }
    #                     num += 1
    #
    #         individual_dict["legend_text"] = legend_text
    #         individual_dict["xvals"] = CONFIG.unidec_engine.data.data2[:, 0]
    #         individual_dict["yvals"] = CONFIG.unidec_engine.data.data2[:, 1]
    #         individual_dict["xlabel"] = "m/z (Da)"
    #         individual_dict["ylabel"] = "Intensity"
    #         individual_dict["colors"] = colors
    #         individual_dict["labels"] = labels
    #
    #         return individual_dict
    #
    #     elif data_type == "MassList":
    #         mwList, heightList = [], []
    #         for i in range(0, CONFIG.unidec_engine.pks.plen):
    #             p = CONFIG.unidec_engine.pks.peaks[i]
    #             if p.ignore == 0:
    #                 mwList.append("MW: {:.2f} ({:.2f} %)".format(p.mass, p.height))
    #                 heightList.append(p.height)
    #
    #         return mwList, mwList[heightList.index(np.max(heightList))]
    #
    #     elif data_type == "Barchart":
    #         if CONFIG.unidec_engine.pks.plen > 0:
    #             num = 0
    #             yvals, colors, labels, legend_text, markers, legend = [], [], [], [], [], []
    #             for p in CONFIG.unidec_engine.pks.peaks:
    #                 if p.ignore == 0:
    #                     yvals.append(p.height)
    #                     if CONFIG.unidec_engine.pks.plen <= 15:
    #                         color = convert_rgb_255_to_1(CONFIG.custom_colors[num])
    #                     else:
    #                         color = p.color
    #                     markers.append(p.marker)
    #                     labels.append(p.label)
    #                     colors.append(color)
    #                     legend_text.append([color, "MW: {:.2f}".format(p.mass)])
    #                     legend.append("MW: {:.2f}".format(p.mass))
    #                     num += 1
    #                 xvals = list(range(0, num))
    #                 barchart_dict = {
    #                     "xvals": xvals,
    #                     "yvals": yvals,
    #                     "labels": labels,
    #                     "colors": colors,
    #                     "legend": legend,
    #                     "legend_text": legend_text,
    #                     "markers": markers,
    #                 }
    #             return barchart_dict
    #
    #     elif data_type == "document_all":
    #         if "document_title" in kwargs:
    #             document_title = kwargs["document_title"]
    #         else:
    #             document = self.data_handling.on_get_document()
    #             if document is None:
    #                 return
    #             document_title = document.title
    #
    #         if self.unidec_dataset == "Mass Spectrum":
    #             data = document.massSpectrum
    #         elif self.unidec_dataset == "Mass Spectrum (processed)":
    #             data = document.smoothMS
    #         else:
    #             data = document.multipleMassSpectrum[self.unidec_dataset]
    #
    #         return data, document, document_title
    #
    #     elif data_type == "document_info":
    #
    #         if "document_title" in kwargs:
    #             document_title = kwargs["document_title"]
    #         else:
    #             document = self.data_handling.on_get_document()
    #             document_title = document.title
    #
    #         try:
    #             document = ENV[document_title]
    #         except KeyError:
    #             if kwargs.get("notify_of_error", True):
    #                 DialogBox(title="Error", msg="Please create or load a document first", kind="Error")
    #             return
    #
    #         return document, document_title
    #
    #     elif data_type == "unidec_data":
    #
    #         data, __, __ = self.get_unidec_data(data_type="document_all")
    #         return data["unidec"]
    #
    #     elif data_type == "mass_list":
    #         data, __, __ = self.get_unidec_data(data_type="document_all")
    #         return data["unidec"]["m/z with isolated species"]["_massList_"]


UNIDEC_HANDLER = UniDecHandler()
