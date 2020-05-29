# Standard library imports
import logging
import threading
from time import time as ttime

# Third-party imports
import numpy as np

# Local imports
import origami.utils.labels as ut_labels
import origami.processing.peaks as pr_peaks
import origami.processing.utils as pr_utils
import origami.processing.heatmap as pr_heatmap
import origami.processing.spectra as pr_spectra
import origami.processing.origami_ms as pr_origami
import origami.processing.peptide_annotation as pr_frag
from origami.ids import ID_window_ccsList
from origami.ids import ID_window_ionList
from origami.ids import ID_window_multiFieldList
from origami.utils.path import clean_filename
from origami.utils.check import isempty
from origami.utils.check import check_value_order
from origami.utils.color import convert_rgb_255_to_1
from origami.utils.random import get_random_int
from origami.utils.converters import str2num
from origami.utils.exceptions import MessageError
from origami.processing.UniDec import unidec
from origami.config.environment import ENV
from origami.gui_elements.misc_dialogs import DialogBox
from origami.gui_elements.misc_dialogs import DialogSimpleAsk

logger = logging.getLogger(__name__)


class DataProcessing:
    def __init__(self, presenter, view, config, **kwargs):
        self.presenter = presenter
        self.view = view
        self.config = config

        # panel links
        self.documentTree = self.view.panelDocuments.documents

        self.plotsPanel = self.view.panelPlots

        # self.ionPanel = self.view.panelMultipleIons
        # self.ionList = self.ionPanel.peaklist
        #
        # self.textPanel = self.view.panelMultipleText
        # self.textList = self.textPanel.peaklist
        #
        # self.filesPanel = self.view.panelMML
        # self.filesList = self.filesPanel.peaklist

        self.frag_generator = pr_frag.PeptideAnnotation()

        # unidec parameters
        self.unidec_dataset = None
        self.unidec_document = None

    def setup_handling_and_processing(self):
        self.data_handling = self.view.data_handling

    def on_get_document(self):
        self.presenter.currentDoc = self.documentTree.on_enable_document()
        if self.presenter.currentDoc is None or self.presenter.currentDoc == "Documents":
            return None
        document = ENV[self.presenter.currentDoc]

        return document

    def on_threading(self, action, args, **kwargs):
        """
        Execute action using new thread
        args: list/dict
            function arguments
        action: str
            decides which action should be taken
        """

        if action == "process.unidec.run":
            th = threading.Thread(target=self.on_run_unidec, args=args, **kwargs)
        elif action == "custom.action":
            fcn = kwargs.pop("fcn")
            th = threading.Thread(target=fcn, args=args, **kwargs)

        # Start thread
        try:
            th.start()
        except Exception as e:
            logger.warning("Failed to execute the operation in threaded mode. Consider switching it off?")
            logger.error(e)

    def _get_replot_data(self, data_format):
        """Quick function to retrieve plotting data without having to go into the document

        Parameters
        ----------
        data_format: str
            type of data to be returned

        Returns
        -------
        data: various
            returns a set of data that is required to replot the data
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

    def get_mz_spacing(self, x):
        """Return average spacing in the spectrum

        Parameters
        ----------
        x : np.array

        Returns
        -------
        np.float
            average spacing in the array
        """
        return np.abs(np.diff(x)).mean()

    @staticmethod
    def on_smooth_1D_signal(ys):
        sigma = DialogSimpleAsk(
            "Smoothing spectrum using Gaussian Filter. Sigma value:", value="", value_type="floatPos"
        )
        sigma = str2num(sigma)

        if sigma in [None, ""]:
            raise MessageError("Incorrect value", f"Incorrect value of {sigma} was provided")

        ys_smooth = []
        for y_signal in ys:
            ys_smooth.append(pr_spectra.smooth_gaussian_1D(y_signal, sigma=sigma))

        return ys_smooth

    def predict_charge_state(self, msX, msY, mz_range, std_dev=0.05):

        msXnarrow, msYnarrow = pr_utils.get_narrow_data_range_1D(msX, msY, x_range=mz_range)
        isotope_peaks = pr_utils.detect_peaks_spectrum2(
            msXnarrow, msYnarrow, window=self.config.fit_highRes_window, threshold=self.config.fit_highRes_threshold
        )
        peak_diff = np.diff(isotope_peaks[:, 0])
        peak_std = np.std(peak_diff)
        charge = 1
        msg = f"Failed to predict charge state - set charge state to {charge:d}. Standard deviation: {peak_std:.4f}"
        if len(peak_diff) > 0 and peak_std <= std_dev:
            charge = int(np.round(1 / np.round(np.average(peak_diff), 4), 0))
            msg = f"Predicted charge state: {charge:d} | Standard deviation: {peak_std:.4f}"

        logger.info(msg)

        return charge

    # TODO: seperate this function into seperate mini functions - a lot easier to debug...
    def on_pick_peaks(self, evt):
        """
        This function finds peaks from 1D array
        """
        document = self.data_handling.on_get_document()

        tstart = ttime()
        if document.dataType in ["Type: ORIGAMI", "Type: MANUAL", "Type: Infrared", "Type: MassLynx", "Type: MS"]:
            panel = self.ionPanel
            tempList = self.ionList
            dataPlot = self.plotsPanel.plot1
            pageID = self.config.panelNames["MS"]
            markerPlot = "MS"
        elif document.dataType == "Type: Multifield Linear DT":
            panel = self.view.panelLinearDT.bottomP
            tempList = self.view.panelLinearDT.bottomP.peaklist
            rtTemptList = self.view.panelLinearDT.topP.peaklist
            dataPlot = self.view.panelPlots.plot1
            pageID = self.config.panelNames["MS"]
            markerPlot = "MS"
        elif document.dataType == "Type: CALIBRANT":
            panel = self.view.panelCCS.topP
            tempList = self.view.panelCCS.topP.peaklist
            dataPlot = self.view.panelPlots.topPlotMS
            pageID = self.config.panelNames["Calibration"]
            markerPlot = "CalibrationMS"

        # A couple of constants
        ymin = 0
        height = 1.0
        peak_count = 0
        method = 1

        # clear previous results
        try:
            dataPlot.plot_remove_markers()
            dataPlot.plot_remove_patches()
            dataPlot.plot_remove_text()
        except Exception:
            pass

        # Chromatograms
        if self.config.fit_type in ["RT", "MS/RT"]:
            if document.dataType in ["Type: Multifield Linear DT", "Type: Infrared"]:
                # TO ADD: current view only, smooth
                # Prepare data first
                rtList = np.transpose([document.RT["xvals"], document.RT["yvals"]])

                # Detect peaks
                peakList, tablelist, _ = pr_utils.detect_peaks_chromatogram(rtList, self.config.fit_threshold)
                peak_count = len(peakList)

                if len(peakList) > 0:
                    self.view.panelPlots.mainBook.SetSelection(self.config.panelNames["RT"])
                    self.view.panelPlots.on_plot_RT(document.RT["xvals"], document.RT["yvals"], document.RT["xlabels"])
                    # Add rectangles (if checked)
                    if self.config.fit_highlight:
                        self.view.panelPlots.on_add_marker(
                            xvals=peakList[:, 0],
                            yvals=peakList[:, 1],
                            color=self.config.markerColor_1D,
                            marker=self.config.markerShape_1D,
                            size=self.config.markerSize_1D,
                            plot="RT",
                        )
                        # Iterate over list and add rectangles
                        last = len(tablelist) - 1
                        for i, rt in enumerate(tablelist):
                            xmin = rt[0]
                            if xmin == 1:
                                pass
                            else:
                                xmin = xmin - 1
                            width = rt[1] - xmin + 1
                            if i == last:
                                width = width - 1
                                self.view.panelPlots.on_add_patch(
                                    xmin,
                                    ymin,
                                    width,
                                    height,
                                    color=self.config.markerColor_1D,
                                    alpha=(self.config.markerTransparency_1D / 100),
                                    plot="RT",
                                    repaint=True,
                                )
                            else:
                                self.view.panelPlots.on_add_patch(
                                    xmin,
                                    ymin,
                                    width,
                                    height,
                                    color=self.config.markerColor_1D,
                                    alpha=(self.config.markerTransparency_1D / 100),
                                    plot="RT",
                                    repaint=False,
                                )

                        # Add items to table (if checked)
                        if self.config.fit_addPeaks:
                            if document.dataType == "Type: Multifield Linear DT":
                                self.view.on_toggle_panel(evt=ID_window_multiFieldList, check=True)
                                for rt in tablelist:
                                    xmin, xmax = rt[0], rt[1]
                                    xdiff = xmax - xmin
                                    rtTemptList.Append([xmin, xmax, xdiff, "", self.presenter.currentDoc])
                                # Removing duplicates
                                self.view.panelLinearDT.topP.onRemoveDuplicates(evt=None)

        if self.config.fit_type in ["RT (UVPD)"]:
            height = 100000000000
            # Prepare data first
            rtList = np.transpose([document.RT["xvals"], document.RT["yvals"]])
            # Detect peaks
            peakList, tablelist, apexlist = pr_utils.detect_peaks_chromatogram(
                rtList, self.config.fit_threshold, add_buffer=1
            )
            peak_count = len(peakList)

            self.view.panelPlots.on_clear_patches("RT", True)
            self.view.panelPlots.on_add_marker(
                xvals=apexlist[:, 0],
                yvals=apexlist[:, 1],
                color=self.config.markerColor_1D,
                marker=self.config.markerShape_1D,
                size=self.config.markerSize_1D,
                plot="RT",
                clear_first=True,
            )
            last = len(tablelist) - 1
            for i, rt in enumerate(tablelist):
                if i % 2:
                    color = (1, 0, 0)
                else:
                    color = (0, 0, 1)
                xmin = rt[0]
                if xmin == 1:
                    pass
                else:
                    xmin = xmin - 1
                width = rt[1] - xmin + 1
                if i == last:
                    width = width - 1
                    self.view.panelPlots.on_add_patch(
                        xmin,
                        ymin,
                        width,
                        height,
                        color=color,
                        #                                                       alpha=(self.config.markerTransparency_1D/100),
                        plot="RT",
                        repaint=True,
                    )
                else:
                    self.view.panelPlots.on_add_patch(
                        xmin,
                        ymin,
                        width,
                        height,
                        color=color,
                        #                                                       alpha=(self.config.markerTransparency_1D/100),
                        plot="RT",
                        repaint=False,
                    )

        # Mass spectra
        if self.config.fit_type in ["MS", "MS/RT"]:
            if document.gotMS:
                if self.config.fit_smoothPeaks:
                    msX = document.massSpectrum["xvals"]
                    msY = document.massSpectrum["yvals"]
                    # Smooth data
                    msY = pr_spectra.smooth_gaussian_1D(data=msY, sigma=self.config.fit_smooth_sigma)
                    msY = pr_spectra.normalize_1D(msY)
                else:
                    msX = document.massSpectrum["xvals"]
                    msY = document.massSpectrum["yvals"]

                msList = np.transpose([msX, msY])
                try:
                    mzRange = dataPlot.onGetXYvals(axes="x")  # using shortcut
                except AttributeError:
                    mzRange = document.massSpectrum["xlimits"]

                if self.config.fit_xaxis_limit:
                    # Get current m/z range
                    msList = pr_utils.get_narrow_data_range(data=msList, mzRange=mzRange)  # get index of that m/z range

                # find peaks
                if method == 1:
                    peakList = pr_utils.detect_peaks_spectrum(
                        data=msList, window=self.config.fit_window, threshold=self.config.fit_threshold
                    )
                else:
                    peakList = pr_utils.detect_peaks_spectrum2(
                        msX, msY, window=self.config.fit_window, threshold=self.config.fit_threshold
                    )
                height = 100000000000
                width = self.config.fit_width * 2
                peak_count = len(peakList)
                last_peak = peak_count - 1
                if peak_count > 0:
                    # preset peaklist with space for other parameters
                    peakList = np.c_[
                        peakList, np.zeros(len(peakList)), np.empty(len(peakList)), np.empty(len(peakList))
                    ]

                    self.view.panelPlots.mainBook.SetSelection(pageID)  # using shortcut
                    self.presenter.view.panelPlots.on_clear_patches(plot=markerPlot)
                    # Plotting smoothed (or not) MS
                    if document.dataType == "Type: CALIBRANT":
                        self.view.panelPlots.on_plot_MS_DT_calibration(
                            msX=msX,
                            msY=msY,
                            xlimits=document.massSpectrum["xlimits"],
                            color=self.config.lineColour_1D,
                            plotType="MS",
                            view_range=mzRange,
                        )
                    else:
                        name_kwargs = {"document": document.title, "dataset": "Mass Spectrum"}
                        self.view.panelPlots.on_plot_MS(
                            msX, msY, xlimits=document.massSpectrum["xlimits"], view_range=mzRange, **name_kwargs
                        )
                    # clear plots
                    self.presenter.view.panelPlots.on_clear_labels()

                    for i, peak in enumerate(peakList):
                        if i == last_peak:
                            repaint = True
                        else:
                            repaint = False

                        # preset all variables
                        mzStart = peak[0] - (self.config.fit_width * self.config.fit_asymmetric_ratio)
                        mzEnd = mzStart + width

                        if method == 1:  # old method
                            mzNarrow = pr_utils.get_narrow_data_range(data=msList, mzRange=(mzStart, mzEnd))
                            label_height = np.round(pr_utils.find_peak_maximum(mzNarrow), 2)
                            narrow_count = len(mzNarrow)
                        else:
                            msXnarrow, msYnarrow = pr_utils.get_narrow_data_range_1D(msX, msY, x_range=(mzStart, mzEnd))
                            label_height = np.round(pr_utils.find_peak_maximum_1D(msYnarrow), 2)
                            narrow_count = len(msXnarrow)

                        charge = 0

                        # detect charges
                        if self.config.fit_highRes:
                            # Iterate over the peaklist
                            isotope_peaks_x, isotope_peaks_y = [], []
                            if narrow_count > 0:
                                if method == 1:  # old method
                                    highResPeaks = pr_utils.detect_peaks_spectrum(
                                        data=mzNarrow,
                                        window=self.config.fit_highRes_window,
                                        threshold=self.config.fit_highRes_threshold,
                                    )
                                else:
                                    highResPeaks = pr_utils.detect_peaks_spectrum2(
                                        msXnarrow,
                                        msYnarrow,
                                        window=self.config.fit_highRes_window,
                                        threshold=self.config.fit_highRes_threshold,
                                    )
                                peakDiffs = np.diff(highResPeaks[:, 0])
                                if len(peakDiffs) > 0:
                                    charge = int(np.round(1 / np.round(np.average(peakDiffs), 4), 0))

                                try:
                                    max_index = np.where(highResPeaks[:, 1] == np.max(highResPeaks[:, 1]))
                                    isotopic_max_val_x, isotopic_max_val_y = (
                                        highResPeaks[max_index, :][0][0][0],
                                        highResPeaks[max_index, :][0][0][1],
                                    )
                                except Exception:
                                    isotopic_max_val_x, isotopic_max_val_y = None, None

                                # Assumes positive mode
                                peakList[i, 2] = charge
                                if isotopic_max_val_x is not None:
                                    peakList[i, 3] = isotopic_max_val_x
                                    peakList[i, 4] = isotopic_max_val_y

                                if self.config.fit_highRes_isotopicFit:
                                    isotope_peaks_x.append(highResPeaks[:, 0].tolist())
                                    isotope_peaks_y.append(highResPeaks[:, 1].tolist())

                        # generate label
                        if self.config.fit_show_labels and peak_count <= self.config.fit_show_labels_max_count:
                            if self.config.fit_show_labels_mz and self.config.fit_show_labels_int:
                                if charge != 0:
                                    label = "{:.2f}, {:.2f}\nz={}".format(peak[0], label_height, charge)
                                else:
                                    label = "{:.2f}, {:.2f}".format(peak[0], label_height)
                            elif self.config.fit_show_labels_mz and not self.config.fit_show_labels_int:
                                if charge != 0:
                                    label = "{:.2f}\nz={}".format(peak[0], charge)
                                else:
                                    label = "{:.2f}".format(peak[0])
                            elif not self.config.fit_show_labels_mz and self.config.fit_show_labels_int:
                                if charge != 0:
                                    label = "{:.2f}\nz={}".format(label_height, charge)
                                else:
                                    label = "{:.2f}".format(label_height)

                        # add isotopic markers
                        if self.config.fit_highRes_isotopicFit:
                            flat_x = [item for sublist in isotope_peaks_x for item in sublist]
                            flat_y = [item for sublist in isotope_peaks_y for item in sublist]
                            self.presenter.view.panelPlots.on_plot_markers(
                                xvals=flat_x,
                                yvals=flat_y,
                                color=(1, 0, 0),
                                marker="o",
                                size=15,
                                plot=markerPlot,
                                repaint=repaint,
                            )

                        # add labels
                        if self.config.fit_show_labels and peak_count <= self.config.fit_show_labels_max_count:
                            self.presenter.view.panelPlots.on_plot_labels(
                                xpos=peak[0], yval=label_height / dataPlot.y_divider, label=label, repaint=repaint
                            )

                        # highlight in MS
                        if self.config.fit_highlight:
                            self.presenter.view.panelPlots.on_plot_patches(
                                mzStart,
                                ymin,
                                width,
                                height,
                                color=self.config.markerColor_1D,
                                alpha=(self.config.markerTransparency_1D),
                                repaint=repaint,
                                plot=markerPlot,
                            )
                    # add peaks to annotations dictionary
                    if self.config.fit_addPeaksToAnnotations:
                        # get document annotations
                        annotations = self.get_document_annotations()
                        for i, mz in enumerate(peakList):
                            peak = mz[0]
                            min_value = np.round(peak - (self.config.fit_width * self.config.fit_asymmetric_ratio), 4)
                            max_value = np.round(min_value + width, 4)

                            mz_narrow = pr_utils.get_narrow_data_range(msList, mzRange=[min_value, max_value])
                            intensity = pr_utils.find_peak_maximum(mz_narrow)
                            max_index = np.where(mz_narrow[:, 1] == intensity)[0]
                            intensity = np.round(intensity, 2)
                            try:
                                position = mz_narrow[max_index, 0]
                            except Exception:
                                position = max_value - ((max_value - min_value) / 2)
                            try:
                                position = position[0]
                            except Exception:
                                pass

                            try:
                                charge_value = int(mz[2])
                            except Exception:
                                charge_value = 0
                            if len(mz) > 3 and mz[3] > 1:
                                isotopic_max_val_x = mz[3]
                                isotopic_max_val_y = mz[4]
                                annotation_dict = {
                                    "min": min_value,
                                    "max": max_value,
                                    "charge": charge_value,
                                    "intensity": intensity,
                                    "label": "",
                                    "color": self.config.interactive_ms_annotations_color,
                                    "isotopic_x": isotopic_max_val_x,
                                    "isotopic_y": isotopic_max_val_y,
                                }
                            else:
                                annotation_dict = {
                                    "min": min_value,
                                    "max": max_value,
                                    "charge": charge_value,
                                    "intensity": intensity,
                                    "label": "",
                                    "isotopic_x": position,
                                    "isotopic_y": intensity,
                                    "color": self.config.interactive_ms_annotations_color,
                                }
                            name = "{} - {}".format(min_value, max_value)
                            annotations[name] = annotation_dict

                        self.set_document_annotations(annotations)
                    #                         self.data_handling.on_update_document(document)

                    # add found peaks to the table
                    if self.config.fit_addPeaks:
                        if document.dataType in ["Type: ORIGAMI", "Type: MANUAL"]:
                            self.view.on_toggle_panel(evt=ID_window_ionList, check=True)
                            for mz in peakList:
                                # New in 1.0.4: Added slightly assymetric envelope to the peak
                                xmin = np.round(mz[0] - (self.config.fit_width * self.config.fit_asymmetric_ratio), 2)
                                xmax = xmin + width
                                try:
                                    charge = str(int(mz[2]))
                                except Exception:
                                    charge = ""
                                intensity = np.round(mz[1] * 100, 1)
                                if not panel.on_check_duplicate(f"{xmin}-{xmax}", self.presenter.currentDoc):
                                    add_dict = {
                                        "mz_start": xmin,
                                        "mz_end": xmax,
                                        "charge": charge,
                                        "color": self.config.customColors[get_random_int(0, 15)],
                                        "mz_ymax": intensity,
                                        "colormap": self.config.overlay_cmaps[
                                            get_random_int(0, len(self.config.overlay_cmaps) - 1)
                                        ],
                                        "alpha": self.config.overlay_defaultAlpha,
                                        "mask": self.config.overlay_defaultMask,
                                        "document": self.presenter.currentDoc,
                                    }
                                    panel.on_add_to_table(add_dict)

                        elif document.dataType == "Type: Multifield Linear DT":
                            self.view.on_toggle_panel(evt=ID_window_multiFieldList, check=True)
                            for mz in peakList:
                                xmin = np.round(mz[0] - (self.config.fit_width * 0.75), 2)
                                xmax = xmin + width
                                try:
                                    charge = str(int(mz[2]))
                                except Exception:
                                    charge = ""
                                intensity = np.round(mz[1] * 100, 1)
                                tempList.Append([xmin, xmax, intensity, charge, self.presenter.currentDoc])
                            # Removing duplicates
                            self.view.panelLinearDT.bottomP.onRemoveDuplicates(evt=None)

                        elif document.dataType == "Type: CALIBRANT":
                            self.view.on_toggle_panel(evt=ID_window_ccsList, check=True)
                            for mz in peakList:
                                xmin = np.round(mz[0] - (self.config.peakWidth * 0.75), 2)
                                xmax = xmin + width
                                try:
                                    charge = str(int(mz[2]))
                                except Exception:
                                    charge = ""
                                intensity = np.round(mz[1] * 100, 1)
                                tempList.Append([self.presenter.currentDoc, xmin, xmax, "", charge])
                            # Removing duplicates
                            self.view.panelCCS.topP.onRemoveDuplicates(evt=None)

            msg = "Found {} peaks in {:.4f} seconds.".format(peak_count, ttime() - tstart)
            self.presenter.onThreading(None, (msg, 4), action="updateStatusbar")

    def get_document_annotations(self):
        if (
            self.presenter.view.panelPlots.plot1.document_name is not None
            and self.presenter.view.panelPlots.plot1.dataset_name is not None
        ):
            document_title = self.presenter.view.panelPlots.plot1.document_name
            dataset_title = self.presenter.view.panelPlots.plot1.dataset_name

            try:
                document = ENV[document_title]
            except Exception:
                return None

            if dataset_title == "Mass Spectrum":
                annotations = document.massSpectrum.get("annotations", {})
            elif dataset_title == "Mass Spectrum (processed)":
                annotations = document.smoothMS.get("annotations", {})
            else:
                annotations = document.multipleMassSpectrum[dataset_title].get("annotations", {})

            return annotations
        else:
            return None

    def set_document_annotations(self, annotations, document_title=None, dataset_title=None):

        if document_title is None:
            document_title = self.presenter.view.panelPlots.plot1.document_name

        if dataset_title is None:
            dataset_title = self.presenter.view.panelPlots.plot1.dataset_name

        if document_title is not None and dataset_title is not None:

            document = ENV[document_title]
            if dataset_title == "Mass Spectrum":
                document.massSpectrum["annotations"] = annotations
            elif dataset_title == "Mass Spectrum (processed)":
                document.smoothMS["annotations"] = annotations
            else:
                document.multipleMassSpectrum[dataset_title]["annotations"] = annotations

            self.data_handling.on_update_document(document, "document")

    def downsample_array(self, xvals, zvals):
        """Downsample MS/DT array

        Parameters
        ----------
        xvals: np.array
            x-axis array (eg m/z)
        zvals: np.array
            2D array (e.g. m/z vs DT)
        """
        __, x_dim = zvals.shape
        # determine whether soft/hard maximum was breached
        if x_dim > self.config.smart_zoom_soft_max or x_dim > self.config.smart_zoom_hard_max:
            original_shape = zvals.shape
            # calculate division factor(s)
            division_factors, division_factor = pr_heatmap.calculate_division_factors(
                x_dim,
                min_division=self.config.smart_zoom_min_search,
                max_division=self.config.smart_zoom_max_search,
                subsampling_default=self.config.smart_zoom_subsample_default,
            )
            # subsample array
            if not division_factors or self.config.smart_zoom_downsampling_method == "Sub-sampled":
                zvals, xvals = pr_heatmap.subsample_array(zvals, xvals, division_factor)
            else:
                if self.config.smart_zoom_downsampling_method in ["Auto", "Binned (summed)"]:
                    zvals, xvals = pr_heatmap.bin_sum_array(zvals, xvals, division_factor)
                else:
                    zvals, xvals = pr_heatmap.bin_mean_array(zvals, xvals, division_factor)

            logger.info("Downsampled from {} to {}".format(original_shape, zvals.shape))

            # check whether hard maximum was breached
            if zvals.shape[1] > self.config.smart_zoom_hard_max:
                logger.warning("Sub-sampled data is larger than the hard-maximum. Sub-sampling again")
                while zvals.shape[1] > self.config.smart_zoom_hard_max:
                    xvals, zvals = self.downsample_array(xvals, zvals)

        return xvals, zvals

    def on_process_MS(self, msX=None, msY=None, **kwargs):

        # check if data should be replotted (e.g. taken from the plot pre-set data)
        if kwargs.get("replot", False):
            msX, msY, __ = self._get_replot_data("MS")
            if msX is None or msY is None:
                return

        # ensure input values are correct
        self.config.on_check_parameters(data_type="process")
        if self.config.processParamsWindow_on_off:
            self.view.panelProcessData.onSetupValues(evt=None)

        process_msg = ""

        # crop spectrum
        if self.config.ms_process_crop:
            tstart = ttime()
            pr_kwargs = {"min": self.config.ms_crop_min, "max": self.config.ms_crop_max}
            msX, msY = pr_spectra.crop_1D_data(msX, msY, **pr_kwargs)
            process_msg += f"Crop:{ttime()-tstart:.4f}s | "

        # linear spectrum
        if self.config.ms_process_linearize and msX is not None:
            tstart = ttime()
            pr_kwargs = {
                "auto_range": self.config.ms_auto_range,
                "mz_min": self.config.ms_mzStart,
                "mz_max": self.config.ms_mzEnd,
                "mz_bin": self.config.ms_mzBinSize,
                "linearization_mode": self.config.ms_linearization_mode,
            }
            msX, msY = pr_spectra.linearize_data(msX, msY, **pr_kwargs)
            process_msg += f"Linearize:{ttime()-tstart:.4f}s | "

        # smooth spectrum
        if self.config.ms_process_smooth:
            tstart = ttime()
            pr_kwargs = {
                "sigma": self.config.ms_smooth_sigma,
                "polyOrder": self.config.ms_smooth_polynomial,
                "windowSize": self.config.ms_smooth_window,
                "N": self.config.ms_smooth_moving_window,
            }
            msY = pr_spectra.smooth_1D(msY, mode=self.config.ms_smooth_mode, **pr_kwargs)
            process_msg += f"Smooth:{ttime()-tstart:.4f}s | "

        # subtract baseline
        if self.config.ms_process_threshold:
            tstart = ttime()
            msY = pr_spectra.baseline_1D(
                msY,
                self.config.ms_baseline,
                threshold=self.config.ms_threshold,
                window=self.config.ms_baseline_curved_window,
                median_window=self.config.ms_baseline_median_window,
                tophat_window=self.config.ms_baseline_tophat_window,
            )
            process_msg += f"Baseline:{ttime()-tstart:.4f}s | "

        # normalize data
        if self.config.ms_process_normalize:
            tstart = ttime()
            if self.config.ms_normalize:
                msY = pr_spectra.normalize_1D(msY, mode=self.config.ms_normalize_mode)
                process_msg += f"Normalize:{ttime()-tstart:.4f}s"

        if process_msg != "":
            if process_msg.endswith(" | "):
                process_msg = process_msg[:-2]
            logger.info(process_msg)

        # replot data
        if kwargs.get("replot", False):
            # Plot data
            plot_kwargs = {}
            self.view.panelPlots.on_plot_MS(msX=msX, msY=msY, override=False, **plot_kwargs)

        # return data
        if kwargs.get("return_data", False):
            if msX is not None:
                return msX, msY
            else:
                return msY

        # return results and processing parameters
        if kwargs.get("return_all", False):
            parameters = {
                "crop": self.config.ms_process_crop,
                "crop_min": self.config.ms_crop_min,
                "crop_max": self.config.ms_crop_max,
                "auto_range": self.config.ms_auto_range,
                "mz_min": self.config.ms_mzStart,
                "mz_max": self.config.ms_mzEnd,
                "mz_bin": self.config.ms_mzBinSize,
                "linearization_mode": self.config.ms_linearization_mode,
                "smooth_mode": self.config.ms_smooth_mode,
                "sigma": self.config.ms_smooth_sigma,
                "polyOrder": self.config.ms_smooth_polynomial,
                "windowSize": self.config.ms_smooth_window,
                "baseline_mode": self.config.ms_baseline,
                "threshold": self.config.ms_threshold,
                "N": self.config.ms_smooth_moving_window,
            }
            return msX, msY, parameters

    def on_process_MS_and_add_data(self, document_title, dataset):
        __, data = self.data_handling.get_spectrum_data([document_title, dataset])

        # retrieve plot data
        msX = data.pop("xvals")
        msY = data.pop("yvals")

        # process data
        msX, msY, params = self.on_process_MS(msX=msX, msY=msY, return_all=True)
        xlimits = [np.min(msX), np.max(msX)]

        data.update(xvals=msX, yvals=msY, xlimits=xlimits, parameters=params)

        # setup new name
        if dataset == "Mass Spectrum":
            new_dataset = "Mass Spectrum (processed)"
        else:
            # strip any processed string from the title
            dataset = ut_labels.get_clean_label_without_tag(dataset, "processed")
            new_dataset = f"{dataset} (processed)"

        # update dataset and document
        __ = self.data_handling.set_spectrum_data([document_title, new_dataset], data)

        # plot data
        self.view.panelPlots.on_plot_MS(msX, msY, xlimits=xlimits, document=document_title, dataset=new_dataset)

    def on_process_2D(self, xvals=None, yvals=None, zvals=None, **kwargs):
        """Process heatmap data"""

        # check if data should be replotted (e.g. taken from the plot pre-set data)
        if kwargs.get("replot", False):
            data = self._get_replot_data(kwargs["replot_type"])
            zvals, xvals, yvals = data[0:2]

        # make sure any data was retrieved
        if zvals is None:
            return

        process_msg = ""

        # create a copy
        zvals = zvals.copy()

        # check values
        self.config.on_check_parameters(data_type="process")
        if self.config.processParamsWindow_on_off:
            self.view.panelProcessData.onSetupValues(evt=None)

        # interpolate
        if self.config.plot2D_process_interpolate:
            tstart = ttime()
            xvals, yvals, zvals = pr_heatmap.interpolate_2D(
                xvals,
                yvals,
                zvals,
                fold=self.config.plot2D_interpolate_fold,
                mode=self.config.plot2D_interpolate_mode,
                x_axis=self.config.plot2D_interpolate_xaxis,
                y_axis=self.config.plot2D_interpolate_yaxis,
            )
            process_msg += f"Interpolation:{ttime()-tstart:.4f}s | "

        # crop
        if self.config.plot2D_process_crop:
            tstart = ttime()
            xvals, yvals, zvals = pr_heatmap.crop_2D(
                xvals,
                yvals,
                zvals,
                self.config.plot2D_crop_xmin,
                self.config.plot2D_crop_xmax,
                self.config.plot2D_crop_ymin,
                self.config.plot2D_crop_ymax,
            )
            process_msg += f"Crop:{ttime()-tstart:.4f}s | "

        # smooth data
        if self.config.plot2D_process_smooth:
            tstart = ttime()
            pr_kwargs = {
                "sigma": self.config.plot2D_smooth_sigma,
                "polyOrder": self.config.plot2D_smooth_polynomial,
                "windowSize": self.config.plot2D_smooth_window,
            }
            zvals = pr_heatmap.smooth_2D(zvals, **pr_kwargs)
            process_msg += f"Smooth:{ttime()-tstart:.4f}s | "

        # threshold
        if self.config.plot2D_process_threshold:
            tstart = ttime()
            zvals = pr_heatmap.remove_noise_2D(zvals, self.config.plot2D_threshold)

        # normalize
        if self.config.plot2D_normalize:
            tstart = ttime()
            zvals = pr_heatmap.normalize_2D(zvals, mode=self.config.plot2D_normalize_mode)
            process_msg += f"Normalize:{ttime()-tstart:.4f}s | "

        # As a precaution, remove inf
        zvals[zvals == -np.inf] = 0

        if process_msg != "":
            if process_msg.endswith(" | "):
                process_msg = process_msg[:-2]
            logger.info(process_msg)

        # return data
        if kwargs.get("return_data", False):
            return xvals, yvals, zvals

        # return data and parameters
        if kwargs.get("return_all", False):
            parameters = {
                "smooth_mode": self.config.plot2D_smooth_mode,
                "sigma": self.config.plot2D_smooth_sigma,
                "polyOrder": self.config.plot2D_smooth_polynomial,
                "windowSize": self.config.plot2D_smooth_window,
                "threshold": self.config.plot2D_threshold,
            }
            return xvals, yvals, zvals, parameters

        # replot data
        if kwargs.get("replot", False):
            xvals, yvals, xlabel, ylabel = data[1::]
            if kwargs["replot_type"] == "2D":
                self.view.panelPlots.on_plot_2D(zvals, xvals, yvals, xlabel, ylabel, override=False)
                if self.config.waterfall:
                    self.view.panelPlots.on_plot_waterfall(
                        yvals=xvals, xvals=yvals, zvals=zvals, xlabel=xlabel, ylabel=ylabel
                    )
                try:
                    self.view.panelPlots.on_plot_3D(
                        zvals=zvals, labelsX=xvals, labelsY=yvals, xlabel=xlabel, ylabel=ylabel, zlabel="Intensity"
                    )
                except Exception:
                    pass
                if not self.config.waterfall:
                    self.view.panelPlots.mainBook.SetSelection(self.config.panelNames["2D"])
            elif kwargs["replot_type"] == "DT/MS":
                self.view.panelPlots.on_plot_MSDT(zvals, xvals, yvals, xlabel, ylabel, override=False)
                self.view.panelPlots.mainBook.SetSelection(self.config.panelNames["MZDT"])

    def on_process_2D_and_add_data(self, document_title, dataset_type, dataset_name):
        try:
            __, data = self.data_handling.get_mobility_chromatographic_data(
                [document_title, dataset_type, dataset_name]
            )
        except KeyError:
            logger.error(f"Dataset {dataset_name} not present in {dataset_type}")
            return

        # unpact data
        xvals = data["xvals"]
        yvals = data["yvals"]
        zvals = data["zvals"]

        xvals, yvals, zvals, parameters = self.on_process_2D(xvals, yvals, zvals, return_all=True)

        # update data
        data.update(xvals=xvals, yvals=yvals, zvals=zvals, process_parameters=parameters)

        # setup new name
        if (
            dataset_type == "Drift time (2D)"
            and dataset_name is None
            or all([item == "Drift time (2D)" for item in [dataset_type, dataset_name]])
        ):
            dataset_type = "Drift time (2D, processed)"
            new_dataset = None
        if (
            dataset_type == "Drift time (2D, processed)"
            and dataset_name is None
            or all([item == "Drift time (2D, processed)" for item in [dataset_type, dataset_name]])
        ):
            new_dataset = None
            logger.warning(f"Reprocessing {dataset_type}...")
        elif dataset_type == "DT/MS" and dataset_name is None:
            raise MessageError(
                "Not implemented yet",
                "You can process and visualise DT/MS data, however, the"
                + " processed data will not be stored in document, yet",
            )
        else:
            # strip any processed string from the title
            dataset_name = ut_labels.get_clean_label_without_tag(dataset_name, "processed")
            new_dataset = f"{dataset_name} (processed)"

        # update dataset and document
        __ = self.data_handling.set_mobility_chromatographic_data([document_title, dataset_type, new_dataset], data)

        # plot data
        self.view.panelPlots.on_plot_2D(zvals, xvals, yvals, data["xlabels"], data["ylabels"], override=False)

    def on_get_peptide_fragments(self, spectrum_dict, label_format={}, get_lists=False, **kwargs):
        tstart = ttime()
        id_num = kwargs.get("id_num", 0)
        if len(label_format) == 0:
            label_format = {"fragment_name": True, "peptide_seq": False, "charge": True, "delta_mz": False}

        self.frag_generator.set_label_format(label_format)
        # self.frag_generator = pr_frag.PeptideAnnotation(**{"label_format":label_format}) # refresh, temprorary!

        # get parameters
        peptide = None
        if "identification" in spectrum_dict:
            peptide = spectrum_dict["identification"][id_num].get("peptide_seq", None)

        if peptide is None:
            return {}, {}, {}, {}, {}
        z = spectrum_dict["identification"][id_num]["charge"]

        modifications = {}
        try:
            modifications = spectrum_dict["identification"][id_num]["modification_info"]
        except (KeyError, IndexError):
            logger.warning("There were no `modifications` in the dataset")

        # generate fragments
        fragments = self.frag_generator.generate_fragments_from_peptide(
            peptide=peptide,
            ion_types=kwargs.get("ion_types", ["b-all", "y-all"]),
            label_format=label_format,
            max_charge=z,
            modification_dict=modifications,
        )

        # generate fragment lists
        (
            fragment_mass_list,
            fragment_name_list,
            fragment_charge_list,
            fragment_peptide_list,
            frag_full_name_list,
        ) = self.frag_generator.get_fragment_mass_list(fragments)
        xvals, yvals = spectrum_dict["xvals"], spectrum_dict["yvals"]

        # match fragments to peaks in the spectrum
        found_peaks = self.frag_generator.match_peaks(
            xvals,
            yvals,
            fragment_mass_list,
            fragment_name_list,
            fragment_charge_list,
            fragment_peptide_list,
            frag_full_name_list,
            tolerance=kwargs.get("tolerance", 0.25),
            tolerance_units=kwargs.get("tolerance_units", "Da"),
            max_found=kwargs.get("max_annotations", 1),
        )

        # print info
        if kwargs.get("verbose", False):
            msg = "Matched {} peaks in the spectrum for peptide {}. It took {:.4f}.".format(
                len(found_peaks), peptide, ttime() - tstart
            )
            print(msg)

        # return data
        if get_lists:
            # fmt: off
            frag_mass_list, frag_int_list, frag_label_list, frag_full_label_list = \
                self.frag_generator.get_fragment_lists(
                    found_peaks, get_calculated_mz=kwargs.get("get_calculated_mz", False)
                )
            # fmt: on

            return found_peaks, frag_mass_list, frag_int_list, frag_label_list, frag_full_label_list

        # return peaks only
        return found_peaks

    def _check_unidec_input(self, **kwargs):
        if "mz_min" in kwargs and "mz_max" in kwargs:
            if self.config.unidec_mzStart > kwargs["mz_max"]:
                self.config.unidec_mzStart = np.round(kwargs["mz_min"], 0)

            if self.config.unidec_mzEnd < kwargs["mz_min"]:
                self.config.unidec_mzEnd = np.round(kwargs["mz_max"], 0)

        if "mz_max" in kwargs:
            if self.config.unidec_mzEnd > kwargs["mz_max"]:
                self.config.unidec_mzEnd = np.round(kwargs["mz_max"], 0)

    def _unidec_initilize(self, document_title, dataset, msX, msY):
        logger.info("UniDec: Loading data...")

        file_name = "".join([document_title, "_", dataset])
        file_name = clean_filename(file_name)
        folder = self.config.temporary_data
        kwargs = {"clean": True}
        self.config.unidec_engine.open_file(
            file_name=file_name, file_directory=folder, data_in=np.transpose([msX, msY]), **kwargs
        )
        logger.info("UniDec: Finished loading data...")

    def _unidec_preprocess(self, dataset):
        tstart = ttime()
        logger.info("UniDec: Pre-processing...")
        # preprocess
        try:
            self.config.unidec_engine.process_data()
        except IndexError:
            self.on_run_unidec(dataset, task="load_data_unidec")
            self.presenter.onThreading(
                None, ("No data was loaded. Trying to load it automatically", 4), action="updateStatusbar"
            )
            return
        except ValueError:
            msg = (
                "Interpolation range is above the 'true' data range."
                + "Consider reducing interpolation range to cover the span of the mass spectrum"
            )
            self.presenter.onThreading(None, (msg, 4), action="updateStatusbar")
            DialogBox(title="Error", msg=msg, kind="Error")
            return
        logger.info(f"UniDec: Finished pre-processing in {ttime()-tstart:.2f} seconds")

    def _unidec_run(self):
        tstart = ttime()
        logger.info("UniDec: Deconvoluting...")

        if self.config.unidec_peakWidth_auto:
            self.config.unidec_engine.get_auto_peak_width()
        else:
            self.config.unidec_engine.config.mzsig = self.config.unidec_peakWidth

        try:
            self.config.unidec_engine.run_unidec()
            self.config.unidec_peakWidth = self.config.unidec_engine.config.mzsig
        except IndexError:
            raise MessageError("Error", "Please load and pre-process data first")
        except ValueError:
            self.presenter.onThreading(None, ("Could not perform task", 4), action="updateStatusbar")
            return
        logger.info(f"UniDec: Finished deconvoluting in {ttime()-tstart:.2f} seconds")

    def _unidec_find_peaks(self):
        tstart = ttime()
        logger.info("UniDec: Picking peaks...")

        # check if there is data in the dataset
        if len(self.config.unidec_engine.data.massdat) == 0:
            raise MessageError("Incorrect input", "Please `Run UniDec` first as there is missing data")

        # pick peaks
        try:
            self.config.unidec_engine.pick_peaks()
        except (ValueError, ZeroDivisionError) as err:
            print(err)
            msg = (
                "Failed to find peaks. Try increasing the value of 'Peak detection window (Da)'. "
                + "This value should be >= 'Sample frequency (Da)'"
            )
            raise MessageError("Error", msg)
        except IndexError as err:
            print(err)
            raise MessageError("Error", "Index error. Try reducing value of 'Sample frequency (Da)'")

        # convolve peaks
        logger.info(f"UniDec: Finished picking peaks in {ttime()-tstart:.2f} seconds")
        logger.info("UniDec: Convolving peaks...")
        try:
            self.config.unidec_engine.convolve_peaks()
        except OverflowError as err:
            print(err)
            msg = "Too many peaks! Try again with larger 'Peak detection threshold' or 'Peak detection window (Da).'"
            raise MessageError("Error", msg)
        logger.info(f"UniDec: Finished convolving peaks in {ttime()-tstart:.2f} seconds")

    def _unidec_isolate(self):
        tstart = ttime()
        logger.info("UniDec: Isolating MW...")

        try:
            self.config.unidec_engine.pick_peaks()
        except (ValueError, ZeroDivisionError):
            msg = (
                "Failed to find peaks. Try increasing the value of 'Peak detection window (Da)'"
                + "to be same or larger than 'Sample frequency (Da)'."
            )
            DialogBox(title="Error", msg=msg, kind="Error")
            return

        except IndexError:
            DialogBox(title="Error", msg="Please run UniDec first", kind="Error")
            return

        logger.info(f"UniDec: Finished isolating a single MW in {ttime()-tstart:.2f} seconds")

    def _unidec_autorun(self):
        tstart = ttime()
        logger.info("UniDec: Started Autorun...")
        self.config.unidec_engine.autorun()
        self.config.unidec_engine.convolve_peaks()
        logger.info(f"UniDec: Finished Autorun in {ttime()-tstart:.2f} seconds")

    def _unidec_setup_parameters(self):

        # set common parameters
        self.config.unidec_engine.config.numit = self.config.unidec_maxIterations

        # preprocess
        self.config.unidec_engine.config.minmz = self.config.unidec_mzStart
        self.config.unidec_engine.config.maxmz = self.config.unidec_mzEnd
        self.config.unidec_engine.config.mzbins = self.config.unidec_mzBinSize
        self.config.unidec_engine.config.smooth = self.config.unidec_gaussianFilter
        self.config.unidec_engine.config.accvol = self.config.unidec_accelerationV
        self.config.unidec_engine.config.linflag = self.config.unidec_linearization_choices[
            self.config.unidec_linearization
        ]
        self.config.unidec_engine.config.cmap = self.config.currentCmap

        # unidec engine
        self.config.unidec_engine.config.masslb = self.config.unidec_mwStart
        self.config.unidec_engine.config.massub = self.config.unidec_mwEnd
        self.config.unidec_engine.config.massbins = self.config.unidec_mwFrequency
        self.config.unidec_engine.config.startz = self.config.unidec_zStart
        self.config.unidec_engine.config.endz = self.config.unidec_zEnd
        self.config.unidec_engine.config.numz = self.config.unidec_zEnd - self.config.unidec_zStart
        self.config.unidec_engine.config.psfun = self.config.unidec_peakFunction_choices[
            self.config.unidec_peakFunction
        ]

        # peak finding
        self.config.unidec_engine.config.peaknorm = self.config.unidec_peakNormalization_choices[
            self.config.unidec_peakNormalization
        ]
        self.config.unidec_engine.config.peakwindow = self.config.unidec_peakDetectionWidth
        self.config.unidec_engine.config.peakthresh = self.config.unidec_peakDetectionThreshold
        self.config.unidec_engine.separation = self.config.unidec_lineSeparation

    def _calculate_peak_widths(self, chargeList, selectedMW, peakWidth, adductIon="H+"):
        _adducts = {
            "H+": 1.007276467,
            "Na+": 22.989218,
            "K+": 38.963158,
            "NH4+": 18.033823,
            "H-": -1.007276,
            "Cl-": 34.969402,
        }
        min_mz, max_mz = (
            np.min(self.config.unidec_engine.data.data2[:, 0]),
            np.max(self.config.unidec_engine.data.data2[:, 0]),
        )
        charges = np.array(list(map(int, np.arange(chargeList[0, 0], chargeList[-1, 0] + 1))))
        peakpos = (float(selectedMW) + charges * _adducts[adductIon]) / charges

        ignore = (peakpos > min_mz) & (peakpos < max_mz)
        peakpos, charges, intensities = peakpos[ignore], charges[ignore], chargeList[:, 1][ignore]

        # calculate min and max value based on the peak width
        mw_annotations = {}
        for peak, charge, intensity in zip(peakpos, charges, intensities):
            min_value = peak - peakWidth / 2.0
            max_value = peak + peakWidth / 2.0
            label_value = "MW: {}".format(selectedMW)
            annotation_dict = {
                "min": min_value,
                "max": max_value,
                "charge": charge,
                "intensity": intensity,
                "label": label_value,
                "color": self.config.interactive_ms_annotations_color,
            }

            name = "{} - {}".format(np.round(min_value, 2), np.round(max_value, 2))
            mw_annotations[name] = annotation_dict
        return mw_annotations

    def on_run_unidec_fcn(self, dataset, task, **kwargs):
        if not self.config.threading:
            self.on_run_unidec(dataset, task, **kwargs)
        else:
            self.on_threading(action="process.unidec.run", args=(dataset, task), kwargs=kwargs)

    def on_run_unidec(self, dataset, task, **kwargs):
        """Runner function

        Parameters
        ----------
        dataset : str
            type of data to be analysed using UniDec
        task : str
            task that should be carried out. Different tasks spawn different processes
        call_after : bool
            will call after function `fcn` with arguments `args` after the main part is executed - takes advantage
            of the multi-threaded nature of the runner function
        """

        # retrive dataset and document
        self.unidec_dataset = dataset
        data, __, document_title = self.get_unidec_data(data_type="document_all")

        # retrieve unidec object
        if "temporary_unidec" in data and task not in ["auto_unidec"]:
            self.config.unidec_engine = data["temporary_unidec"]
        else:
            self.config.unidec_engine = unidec.UniDec()
            self.config.unidec_engine.config.UniDecPath = self.config.unidec_path

        # check which tasks are carried out
        if task in ["auto_unidec", "load_data_unidec", "run_all_unidec", "load_data_and_preprocess_unidec"]:
            msX = data["xvals"]
            msY = data["yvals"]

            check_kwargs = {"mz_min": msX[0], "mz_max": msX[-1]}
            self._check_unidec_input(**check_kwargs)

        # setup parameters
        if task not in ["auto_unidec"]:
            self._unidec_setup_parameters()

        # load data
        if task in ["auto_unidec", "load_data_unidec", "run_all_unidec"]:
            self._unidec_initilize(document_title, dataset, msX, msY)

        # pre-process
        if task in ["run_all_unidec", "preprocess_unidec"]:
            self._unidec_preprocess(dataset)

        # load and pre-process
        if task in ["load_data_and_preprocess_unidec"]:
            self._unidec_initilize(document_title, dataset, msX, msY)
            self._unidec_preprocess(dataset)

        # deconvolute
        if task in ["run_all_unidec", "run_unidec"]:
            self._unidec_run()

        # find peaks
        if task in ["run_all_unidec", "pick_peaks_unidec"]:
            self._unidec_find_peaks()

        # isolate peak
        if task in ["isolate_mw_unidec"]:
            self._unidec_isolate()

        # run auto
        if task in ["auto_unidec"]:
            self._unidec_autorun()

        # add data to document
        self.on_add_unidec_data(task, dataset, document_title=document_title)

        # add call-after
        if kwargs.get("call_after", False):
            fcn = kwargs.pop("fcn")
            args = kwargs.pop("args")
            fcn(args)

    def on_add_unidec_data(self, task, dataset, document_title=None):
        """Convenience function to add data to document"""

        document = self.data_handling.on_get_document(document_title)

        # initilise data in the mass spectrum dictionary
        if dataset == "Mass Spectrum":
            if "unidec" not in document.massSpectrum:
                document.massSpectrum["unidec"] = {}
            data = document.massSpectrum
        elif dataset == "Mass Spectrum (processed)":
            data = document.smoothMS
            if "unidec" not in document.smoothMS:
                document.smoothMS["unidec"] = {}
        else:
            if "unidec" not in document.multipleMassSpectrum[dataset]:
                document.multipleMassSpectrum[dataset]["unidec"] = {}
            data = document.multipleMassSpectrum[dataset]

        # clear old data
        if task in ["auto_unidec", "run_all_unidec", "preprocess_unidec", "load_data_and_preprocess_unidec"]:
            data["unidec"].clear()

        # add processed data
        if task in ["auto_unidec", "run_all_unidec", "preprocess_unidec", "load_data_and_preprocess_unidec"]:
            raw_data = {
                "xvals": self.config.unidec_engine.data.data2[:, 0],
                "yvals": self.config.unidec_engine.data.data2[:, 1],
                "color": [0, 0, 0],
                "label": "Data",
                "xlabels": "m/z",
                "ylabels": "Intensity",
            }
            # add data
            data["unidec"]["Processed"] = raw_data

        # add fitted and deconvolution data
        if task in ["auto_unidec", "run_all_unidec", "run_unidec"]:
            fit_data = {
                "xvals": [self.config.unidec_engine.data.data2[:, 0], self.config.unidec_engine.data.data2[:, 0]],
                "yvals": [self.config.unidec_engine.data.data2[:, 1], self.config.unidec_engine.data.fitdat],
                "colors": [[0, 0, 0], [1, 0, 0]],
                "labels": ["Data", "Fit Data"],
                "xlabel": "m/z",
                "ylabel": "Intensity",
                "xlimits": [
                    np.min(self.config.unidec_engine.data.data2[:, 0]),
                    np.max(self.config.unidec_engine.data.data2[:, 0]),
                ],
            }
            mw_distribution_data = {
                "xvals": self.config.unidec_engine.data.massdat[:, 0],
                "yvals": self.config.unidec_engine.data.massdat[:, 1],
                "color": [0, 0, 0],
                "label": "Data",
                "xlabels": "Mass (Da)",
                "ylabels": "Intensity",
            }
            mz_grid_data = {
                "grid": self.config.unidec_engine.data.mzgrid,
                "xlabels": " m/z (Da)",
                "ylabels": "Charge",
                "cmap": self.config.unidec_engine.config.cmap,
            }
            mw_v_z_data = {
                "xvals": self.config.unidec_engine.data.massdat[:, 0],
                "yvals": self.config.unidec_engine.data.ztab,
                "zvals": self.config.unidec_engine.data.massgrid,
                "xlabels": "Mass (Da)",
                "ylabels": "Charge",
                "cmap": self.config.unidec_engine.config.cmap,
            }
            # set data in the document store
            data["unidec"]["Fitted"] = fit_data
            data["unidec"]["MW distribution"] = mw_distribution_data
            data["unidec"]["m/z vs Charge"] = mz_grid_data
            data["unidec"]["MW vs Charge"] = mw_v_z_data

        # add aux data
        if task in ["auto_unidec", "run_all_unidec", "pick_peaks_unidec"]:
            # individually plotted
            individual_dict = self.get_unidec_data(data_type="Individual MS")
            barchart_dict = self.get_unidec_data(data_type="Barchart")
            massList, massMax = self.get_unidec_data(data_type="MassList")
            individual_dict["_massList_"] = [massList, massMax]

            # add data
            data["unidec"]["m/z with isolated species"] = individual_dict
            data["unidec"]["Barchart"] = barchart_dict
            data["unidec"]["Charge information"] = self.config.unidec_engine.get_charge_peaks()

        # store unidec engine - cannot be pickled, so will be deleted when saving document
        data["temporary_unidec"] = self.config.unidec_engine

        self.documentTree.on_update_unidec(data["unidec"], document_title, dataset)

    def get_unidec_data(self, data_type="Individual MS", **kwargs):

        if data_type == "Individual MS":
            stickmax = 1.0
            num = 0
            individual_dict = dict()
            legend_text = [[[0, 0, 0], "Raw"]]
            colors, labels = [], []
            #             charges = self.config.unidec_engine.get_charge_peaks()
            for i in range(0, self.config.unidec_engine.pks.plen):
                p = self.config.unidec_engine.pks.peaks[i]
                if p.ignore == 0:
                    list1, list2 = [], []
                    if (not isempty(p.mztab)) and (not isempty(p.mztab2)):
                        mztab = np.array(p.mztab)
                        mztab2 = np.array(p.mztab2)
                        maxval = np.amax(mztab[:, 1])
                        for k in range(0, len(mztab)):
                            if mztab[k, 1] > self.config.unidec_engine.config.peakplotthresh * maxval:
                                list1.append(mztab2[k, 0])
                                list2.append(mztab2[k, 1])

                        if self.config.unidec_engine.pks.plen <= 15:
                            color = convert_rgb_255_to_1(self.config.customColors[i])
                        else:
                            color = p.color
                        colors.append(color)
                        labels.append("MW: {:.2f}".format(p.mass))
                        legend_text.append([color, "MW: {:.2f}".format(p.mass)])

                        individual_dict["MW: {:.2f}".format(p.mass)] = {
                            "scatter_xvals": np.array(list1),
                            "scatter_yvals": np.array(list2),
                            "marker": p.marker,
                            "color": color,
                            "label": "MW: {:.2f}".format(p.mass),
                            "line_xvals": self.config.unidec_engine.data.data2[:, 0],
                            "line_yvals": np.array(p.stickdat) / stickmax
                            - (num + 1) * self.config.unidec_engine.config.separation,
                        }
                        num += 1

            individual_dict["legend_text"] = legend_text
            individual_dict["xvals"] = self.config.unidec_engine.data.data2[:, 0]
            individual_dict["yvals"] = self.config.unidec_engine.data.data2[:, 1]
            individual_dict["xlabel"] = "m/z (Da)"
            individual_dict["ylabel"] = "Intensity"
            individual_dict["colors"] = colors
            individual_dict["labels"] = labels

            return individual_dict

        elif data_type == "MassList":
            mwList, heightList = [], []
            for i in range(0, self.config.unidec_engine.pks.plen):
                p = self.config.unidec_engine.pks.peaks[i]
                if p.ignore == 0:
                    mwList.append("MW: {:.2f} ({:.2f} %)".format(p.mass, p.height))
                    heightList.append(p.height)

            return mwList, mwList[heightList.index(np.max(heightList))]

        elif data_type == "Barchart":
            if self.config.unidec_engine.pks.plen > 0:
                num = 0
                yvals, colors, labels, legend_text, markers, legend = [], [], [], [], [], []
                for p in self.config.unidec_engine.pks.peaks:
                    if p.ignore == 0:
                        yvals.append(p.height)
                        if self.config.unidec_engine.pks.plen <= 15:
                            color = convert_rgb_255_to_1(self.config.customColors[num])
                        else:
                            color = p.color
                        markers.append(p.marker)
                        labels.append(p.label)
                        colors.append(color)
                        legend_text.append([color, "MW: {:.2f}".format(p.mass)])
                        legend.append("MW: {:.2f}".format(p.mass))
                        num += 1
                    xvals = list(range(0, num))
                    barchart_dict = {
                        "xvals": xvals,
                        "yvals": yvals,
                        "labels": labels,
                        "colors": colors,
                        "legend": legend,
                        "legend_text": legend_text,
                        "markers": markers,
                    }
                return barchart_dict

        elif data_type == "document_all":
            if "document_title" in kwargs:
                document_title = kwargs["document_title"]
            else:
                document = self.data_handling.on_get_document()
                if document is None:
                    return
                document_title = document.title

            if self.unidec_dataset == "Mass Spectrum":
                data = document.massSpectrum
            elif self.unidec_dataset == "Mass Spectrum (processed)":
                data = document.smoothMS
            else:
                data = document.multipleMassSpectrum[self.unidec_dataset]

            return data, document, document_title

        elif data_type == "document_info":

            if "document_title" in kwargs:
                document_title = kwargs["document_title"]
            else:
                document = self.data_handling.on_get_document()
                document_title = document.title

            try:
                document = ENV[document_title]
            except KeyError:
                if kwargs.get("notify_of_error", True):
                    DialogBox(title="Error", msg="Please create or load a document first", kind="Error")
                return

            return document, document_title

        elif data_type == "unidec_data":

            data, __, __ = self.get_unidec_data(data_type="document_all")
            return data["unidec"]

        elif data_type == "mass_list":
            data, __, __ = self.get_unidec_data(data_type="document_all")
            return data["unidec"]["m/z with isolated species"]["_massList_"]

    def on_combine_origami_collision_voltages(self, evt):

        # Make a list of Documents
        for ion_id in range(self.ionList.GetItemCount()):
            itemInfo = self.ionPanel.on_get_item_information(item_id=ion_id)
            if not itemInfo["select"]:
                continue

            document_title = itemInfo["document"]
            document = self.data_handling.on_get_document(document_title)

            # Check that this data was opened in ORIGAMI mode and has extracted data
            if document.dataType == "Type: ORIGAMI" and document.gotExtractedIons:
                data = document.IMS2Dions
            else:
                msg = "Data was not extracted yet. Please extract before continuing."
                DialogBox(title="Missing data", msg=msg, kind="Error")
                continue

            # Extract ion name
            ion_name = itemInfo["ionName"]
            method = itemInfo["method"]
            if ion_name not in data:
                logger.warning(f"Could not find {ion_name} in the document")
                continue

            zvals = data[ion_name]["zvals"]

            if method == "":
                self.ionList.SetStringItem(
                    ion_id, self.config.peaklistColNames["method"], self.config.origami_acquisition
                )

            # get origami-ms settings from the metadata
            origami_settings = document.metadata.get("origami_ms", None)
            if origami_settings is None:
                raise MessageError(
                    "Missing ORIGAMI-MS configuration",
                    "Please setup ORIGAMI-MS settings by right-clicking on the document in the"
                    + "Document Tree and selecting `Action -> Setup ORIGAMI-MS parameters"
                    + " or clicking in the toolbar of the peaklist and selecting"
                    + " ORIGAMI-MS: Setup parameters",
                )

            # unpack settings
            method = origami_settings["origami_acquisition"]
            startScan = origami_settings["origami_startScan"]
            startVoltage = origami_settings["origami_startVoltage"]
            endVoltage = origami_settings["origami_endVoltage"]
            stepVoltage = origami_settings["origami_stepVoltage"]
            scansPerVoltage = origami_settings["origami_spv"]
            expIncrement = origami_settings["origami_exponentialIncrement"]
            expPercentage = origami_settings["origami_exponentialPercentage"]
            boltzmannOffset = origami_settings["origami_boltzmannOffset"]
            origami_cv_spv_list = origami_settings["origami_cv_spv_list"]

            # LINEAR METHOD
            if method == "Linear":
                zvals, scan_list, parameters = self.__combine_origami_linear(
                    zvals, startScan, startVoltage, endVoltage, stepVoltage, scansPerVoltage
                )

            # EXPONENTIAL METHOD
            elif method == "Exponential":
                zvals, scan_list, parameters = self.__combine_origami_exponential(
                    zvals,
                    startScan,
                    startVoltage,
                    endVoltage,
                    stepVoltage,
                    scansPerVoltage,
                    expIncrement,
                    expPercentage,
                )

            # FITTED/BOLTZMANN METHOD
            elif method == "Fitted":
                zvals, scan_list, parameters = self.__combine_origami_fitted(
                    zvals, startScan, startVoltage, endVoltage, stepVoltage, scansPerVoltage, boltzmannOffset
                )

            # USER-DEFINED/LIST METHOD
            elif method == "User-defined":
                zvals, xlabels, scan_list, parameters = self.__combine_origami_user_defined(
                    zvals, startScan, origami_cv_spv_list
                )

            if zvals[0] is None:
                msg = (
                    "With your current input, there would be too many scans in your file! "
                    + "There are %s scans in your file and your settings suggest there should be %s"
                    % (zvals[2], zvals[1])
                )
                DialogBox(title="Are your settings correct?", msg=msg, kind="Warning")
                continue

            # Add x-axis and y-axis labels
            if method != "User-defined":
                xlabels = np.arange(
                    self.config.origami_startVoltage,
                    (self.config.origami_endVoltage + self.config.origami_stepVoltage),
                    self.config.origami_stepVoltage,
                )

            # Y-axis is bins by default
            ylabels = np.arange(1, 201, 1)
            # Combine 2D array into 1D
            imsData1D = np.sum(zvals, axis=1).T
            yvalsRT = np.sum(zvals, axis=0)
            # Check if item has labels, alpha, charge
            charge = data[ion_name].get("charge", None)
            cmap = data[ion_name].get("cmap", self.config.overlay_cmaps[get_random_int(0, 5)])
            color = data[ion_name].get("color", self.config.customColors[get_random_int(0, 15)])
            label = data[ion_name].get("label", None)
            alpha = data[ion_name].get("alpha", self.config.overlay_defaultAlpha)
            mask = data[ion_name].get("mask", self.config.overlay_defaultMask)
            min_threshold = data[ion_name].get("min_threshold", 0)
            max_threshold = data[ion_name].get("max_threshold", 1)

            # Add 2D data to document object
            document.gotCombinedExtractedIons = True
            document.IMS2DCombIons[ion_name] = {
                "zvals": zvals,
                "xvals": xlabels,
                "xlabels": "Collision Voltage (V)",
                "yvals": ylabels,
                "ylabels": "Drift time (bins)",
                "yvals1D": imsData1D,
                "yvalsRT": yvalsRT,
                "cmap": cmap,
                "xylimits": data[ion_name]["xylimits"],
                "charge": charge,
                "label": label,
                "alpha": alpha,
                "mask": mask,
                "color": color,
                "min_threshold": min_threshold,
                "max_threshold": max_threshold,
                "scanList": scan_list,
                "parameters": parameters,
            }
            document.combineIonsList = scan_list
            # Add 1D data to document object
            document.gotCombinedExtractedIonsRT = True
            document.IMSRTCombIons[ion_name] = {"xvals": xlabels, "yvals": yvalsRT, "xlabels": "Collision Voltage (V)"}

            # Update document
            self.data_handling.on_update_document(document, "combined_ions")

    def __combine_origami_linear(self, zvals, startScan, startVoltage, endVoltage, stepVoltage, scansPerVoltage):
        if not any([startScan, startVoltage, endVoltage, stepVoltage, scansPerVoltage]):
            logger.error("Cannot perform action. Missing fields in the ORIGAMI parameters panel")
            return

        zvals, scan_list, parameters = pr_origami.origami_combine_linear(
            zvals, startScan, startVoltage, endVoltage, stepVoltage, scansPerVoltage
        )
        return zvals, scan_list, parameters

    def __combine_origami_exponential(
        self, zvals, startScan, startVoltage, endVoltage, stepVoltage, scansPerVoltage, expIncrement, expPercentage
    ):
        if not any([startScan, startVoltage, endVoltage, stepVoltage, scansPerVoltage, expIncrement, expPercentage]):
            logger.error("Cannot perform action. Missing fields in the ORIGAMI parameters panel")
            return

        zvals, scan_list, parameters = pr_origami.origami_combine_exponential(
            zvals, startScan, startVoltage, endVoltage, stepVoltage, scansPerVoltage, expIncrement, expPercentage
        )
        return zvals, scan_list, parameters

    def __combine_origami_fitted(self, zvals, startScan, startVoltage, endVoltage, stepVoltage, scansPerVoltage, dx):
        if not any([startScan, startVoltage, endVoltage, stepVoltage, scansPerVoltage, dx]):
            logger.error("Cannot perform action. Missing fields in the ORIGAMI parameters panel")
            return

        zvals, scan_list, parameters = pr_origami.origami_combine_boltzmann(
            zvals, startScan, startVoltage, endVoltage, stepVoltage, scansPerVoltage, dx
        )
        return zvals, scan_list, parameters

    def __combine_origami_user_defined(self, zvals, startScan, scanList):
        # Ensure that config is not missing variabels
        if len(self.config.origamiList) == 0:
            msg = "Please load a text file with ORIGAMI parameters"
        elif not self.config.origami_startScan:
            msg = "The first scan is incorect (currently: %s)" % self.config.origami_startScan
        elif self.config.origamiList[:, 0].shape != self.config.origamiList[:, 1].shape:
            msg = "The collision voltage list is of incorrect shape."

        if msg is not None:
            logger.error(msg)
            return

        zvals, xlabels, scan_list, parameters = pr_origami.origami_combine_user_defined(zvals, startScan, scanList)

        return zvals, xlabels, scan_list, parameters

    def find_peaks_in_mass_spectrum_peak_properties(self, **kwargs):
        mz_x = kwargs.get("mz_x")
        mz_y = kwargs.get("mz_y")

        mz_min, mz_max = None, None
        if self.config.peak_find_mz_limit:
            mz_min = self.config.peak_find_mz_min
            mz_max = self.config.peak_find_mz_max
            mz_min, mz_max = check_value_order(mz_min, mz_max)

        found_peaks = pr_peaks.find_peaks_in_spectrum_peak_properties(
            mz_x,
            mz_y,
            threshold=self.config.peak_find_threshold,
            distance=self.config.peak_find_distance,
            width=self.config.peak_find_width,
            rel_height=self.config.peak_find_relative_height,
            min_intensity=self.config.peak_find_min_intensity,
            mz_min=mz_min,
            mz_max=mz_max,
            peak_width_modifier=self.config.peak_find_peak_width_modifier,
            verbose=self.config.peak_find_verbose,
        )

        if kwargs.get("return_data", False):
            return found_peaks

    def find_peaks_in_mass_spectrum_local_max(self, **kwargs):
        mz_x = kwargs.get("mz_x")
        mz_y = kwargs.get("mz_y")

        mz_xy = np.transpose([mz_x, mz_y])

        mz_range = None
        if self.config.peak_find_mz_limit:
            mz_min = self.config.peak_find_mz_min
            mz_max = self.config.peak_find_mz_max
            mz_min, mz_max = check_value_order(mz_min, mz_max)
            mz_range = (mz_min, mz_max)

        # check  threshold
        threshold = self.config.fit_threshold
        if threshold > 1:
            threshold = threshold / np.max(mz_y)

        found_peaks = pr_peaks.find_peaks_in_spectrum_local_search(
            mz_xy,
            self.config.fit_window,
            threshold,
            mz_range,
            rel_height=self.config.fit_relative_height,
            verbose=self.config.peak_find_verbose,
        )

        if kwargs.get("return_data", False):
            return found_peaks

    def find_peaks_in_mass_spectrum_peakutils(self, **kwargs):
        mz_x = kwargs.get("mz_x")
        mz_y = kwargs.get("mz_y")

        mz_range = None
        if self.config.peak_find_mz_limit:
            mz_min = self.config.peak_find_mz_min
            mz_max = self.config.peak_find_mz_max
            mz_min, mz_max = check_value_order(mz_min, mz_max)
            mz_range = (mz_min, mz_max)

        # check  threshold
        threshold = self.config.fit_threshold
        if threshold > 1:
            threshold = threshold / np.max(mz_y)

        found_peaks = pr_peaks.find_peaks_in_spectrum_peakutils(
            mz_x,
            mz_y,
            threshold,
            self.config.fit_window,
            mz_range,
            rel_height=self.config.fit_relative_height,
            verbose=self.config.peak_find_verbose,
        )

        if kwargs.get("return_data", False):
            return found_peaks

    def smooth_spectrum(self, mz_y, method="gaussian"):
        if method == "gaussian":
            mz_y = pr_spectra.smooth_gaussian_1D(mz_y, self.config.fit_smooth_sigma)

        return mz_y

    @staticmethod
    def subtract_spectra(xvals_1, yvals_1, xvals_2, yvals_2, **kwargs):
        """Subtract two spectra from one another"""
        xvals_1, yvals_1, xvals_2, yvals_2 = pr_spectra.subtract_spectra(xvals_1, yvals_1, xvals_2, yvals_2)

        return xvals_1, yvals_1, xvals_2, yvals_2
