"""Handler class for UniDec mass deconvolution"""
# Standard library imports
import time
import logging

# Local imports
from origami.utils.secret import get_short_hash
from origami.config.config import CONFIG
from origami.utils.utilities import report_time
from origami.handlers.process import PROCESS_HANDLER
from origami.objects.containers import MassSpectrumObject
from origami.widgets.unidec.processing.engine import UniDecEngine

LOGGER = logging.getLogger(__name__)


class UniDecHandler:
    """UniDec handler"""

    def __init__(self):
        pass

    @staticmethod
    def unidec_init_engine(document_title: str = None, dataset_name: str = None):
        """Initialize UniDec engine"""
        if CONFIG.unidec_engine is None:
            CONFIG.unidec_engine = UniDecEngine(document_title=document_title, dataset_name=dataset_name)

    def unidec_initialize(self, mz_obj: MassSpectrumObject):
        """Initialize UniDec engine"""
        LOGGER.debug("UniDec: Started loading data...")

        self.unidec_init_engine()

        # get unique filename
        document_title = mz_obj.document_title
        filename = mz_obj.dataset_name
        if filename in ["", None] or document_title in ["", None]:
            filename = get_short_hash()
            document_title = get_short_hash()
        filename = "_".join([document_title, filename])

        CONFIG.unidec_engine.set_mass_spectrum(mz_obj, filename=filename, output_dir=CONFIG.APP_TEMP_DATA_PATH)
        LOGGER.debug("UniDec: Finished loading data...")

        return CONFIG.unidec_engine.data

    @staticmethod
    def unidec_preprocess():
        """Pre-process mass spectrum"""
        t_start = time.time()
        LOGGER.debug("UniDec: Started pre-processing...")
        CONFIG.unidec_engine.config.set_from_origami_config()

        # create copy of the mass spectrum object so the data is not overwritten in the Document
        mz_obj = CONFIG.unidec_engine.data.mz_obj.duplicate()
        mz_obj = PROCESS_HANDLER.on_process_ms(mz_obj)
        CONFIG.unidec_engine.process_mass_spectrum(mz_obj)
        LOGGER.debug(f"UniDec: Finished pre-processing in {report_time(t_start)}")

        return CONFIG.unidec_engine.data

    def unidec_initialize_and_preprocess(self, mz_obj: MassSpectrumObject):
        """Initialize UniDec engine and pre-process data"""
        self.unidec_initialize(mz_obj)
        self.unidec_preprocess()
        return CONFIG.unidec_engine.data

    @staticmethod
    def unidec_run():
        """Pre-process mass spectrum"""
        t_start = time.time()
        LOGGER.debug("UniDec: Started deconvolution...")
        # this is required so the ORIGAMI-defined parameters are used in the deconvolution
        CONFIG.unidec_engine.config.set_from_origami_config()

        # run unidec
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
        CONFIG.unidec_engine.config.set_from_origami_config()

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

    def unidec_autorun(self, mz_obj: MassSpectrumObject):
        """Autorun UniDec"""
        t_start = time.time()
        LOGGER.info("UniDec: Started Autorun...")
        self.unidec_initialize_and_preprocess(mz_obj)
        self.unidec_run()
        self.unidec_find_peaks()
        LOGGER.debug(f"UniDec: Finished autorun in {report_time(t_start)}")
        return CONFIG.unidec_engine.data

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
