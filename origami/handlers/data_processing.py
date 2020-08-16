# Standard library imports
import time
import logging
import threading

# Third-party imports
import numpy as np

# Local imports
import origami.processing.utils as pr_utils
import origami.processing.heatmap as pr_heatmap
import origami.processing.spectra as pr_spectra
import origami.processing.peptide_annotation as pr_frag
from origami.utils.converters import str2num
from origami.utils.exceptions import MessageError

# from misc.code.UniDec import unidec
from origami.config.environment import ENV
from origami.gui_elements.misc_dialogs import DialogSimpleAsk

logger = logging.getLogger(__name__)


class DataProcessing:
    """Data processing"""

    def __init__(self, presenter, view, config, **kwargs):
        self.presenter = presenter
        self.view = view
        self.config = config

        self.frag_generator = pr_frag.PeptideAnnotation()

        # unidec parameters
        # self.unidec_dataset = None
        # self.unidec_document = None

    @property
    def data_handling(self):
        """Return handle to `data_processing`"""
        return self.presenter.data_handling

    @property
    def document_tree(self):
        """Return handle to `document_tree`"""
        return self.view.panelDocuments.documents

    @property
    def panel_plot(self):
        """Return handle to `data_processing`"""
        return self.view.panelPlots

    def on_get_document(self):
        self.presenter.currentDoc = self.document_tree.on_enable_document()
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

        if action == "custom.action":
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
            ys_smooth.append(pr_spectra.smooth_gaussian_1d(y_signal, sigma=sigma))

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

    # # TODO: seperate this function into seperate mini functions - a lot easier to debug...
    # def on_pick_peaks(self, evt):
    #     """
    #     This function finds peaks from 1D array
    #     """
    #     document = self.data_handling.on_get_document()
    #
    #     tstart = time.time()
    #     if document.dataType in ["Type: ORIGAMI", "Type: MANUAL", "Type: Infrared", "Type: MassLynx", "Type: MS"]:
    #         panel = self.ionPanel
    #         tempList = self.ionList
    #         dataPlot = self.plotsPanel.plot1
    #         pageID = self.config.panelNames["MS"]
    #         markerPlot = "MS"
    #     elif document.dataType == "Type: Multifield Linear DT":
    #         panel = self.view.panelLinearDT.bottomP
    #         tempList = self.view.panelLinearDT.bottomP.peaklist
    #         rtTemptList = self.view.panelLinearDT.topP.peaklist
    #         dataPlot = self.view.panelPlots.plot1
    #         pageID = self.config.panelNames["MS"]
    #         markerPlot = "MS"
    #     elif document.dataType == "Type: CALIBRANT":
    #         panel = self.view.panelCCS.topP
    #         tempList = self.view.panelCCS.topP.peaklist
    #         dataPlot = self.view.panelPlots.topPlotMS
    #         pageID = self.config.panelNames["Calibration"]
    #         markerPlot = "CalibrationMS"
    #
    #     # A couple of constants
    #     ymin = 0
    #     height = 1.0
    #     peak_count = 0
    #     method = 1
    #
    #     # clear previous results
    #     try:
    #         dataPlot.plot_remove_markers()
    #         dataPlot.plot_remove_patches()
    #         dataPlot.plot_remove_label()
    #     except Exception:
    #         pass
    #
    #     # Chromatograms
    #     if self.config.fit_type in ["RT", "MS/RT"]:
    #         if document.dataType in ["Type: Multifield Linear DT", "Type: Infrared"]:
    #             # TO ADD: current view only, smooth
    #             # Prepare data first
    #             rtList = np.transpose([document.RT["xvals"], document.RT["yvals"]])
    #
    #             # Detect peaks
    #             peakList, tablelist, _ = pr_utils.detect_peaks_chromatogram(rtList, self.config.fit_threshold)
    #             peak_count = len(peakList)
    #
    #             if len(peakList) > 0:
    #                 self.view.panelPlots.mainBook.SetSelection(self.config.panelNames["RT"])
    #                 self.view.panelPlots.on_plot_rt(document.RT["xvals"], document.RT["yvals"],
    #                 document.RT["xlabels"])
    #                 # Add rectangles (if checked)
    #                 if self.config.fit_highlight:
    #                     self.view.panelPlots.on_add_marker(
    #                         xvals=peakList[:, 0],
    #                         yvals=peakList[:, 1],
    #                         color=self.config.markerColor_1D,
    #                         marker=self.config.markerShape_1D,
    #                         size=self.config.markerSize_1D,
    #                         plot="RT",
    #                     )
    #                     # Iterate over list and add rectangles
    #                     last = len(tablelist) - 1
    #                     for i, rt in enumerate(tablelist):
    #                         xmin = rt[0]
    #                         if xmin == 1:
    #                             pass
    #                         else:
    #                             xmin = xmin - 1
    #                         width = rt[1] - xmin + 1
    #                         if i == last:
    #                             width = width - 1
    #                             self.view.panelPlots.on_add_patch(
    #                                 xmin,
    #                                 ymin,
    #                                 width,
    #                                 height,
    #                                 color=self.config.markerColor_1D,
    #                                 alpha=(self.config.markerTransparency_1D / 100),
    #                                 plot="RT",
    #                                 repaint=True,
    #                             )
    #                         else:
    #                             self.view.panelPlots.on_add_patch(
    #                                 xmin,
    #                                 ymin,
    #                                 width,
    #                                 height,
    #                                 color=self.config.markerColor_1D,
    #                                 alpha=(self.config.markerTransparency_1D / 100),
    #                                 plot="RT",
    #                                 repaint=False,
    #                             )
    #
    #                     # Add items to table (if checked)
    #                     if self.config.fit_addPeaks:
    #                         if document.dataType == "Type: Multifield Linear DT":
    #                             self.view.on_toggle_panel(evt=ID_window_multiFieldList, check=True)
    #                             for rt in tablelist:
    #                                 xmin, xmax = rt[0], rt[1]
    #                                 xdiff = xmax - xmin
    #                                 rtTemptList.Append([xmin, xmax, xdiff, "", self.presenter.currentDoc])
    #                             # Removing duplicates
    #                             self.view.panelLinearDT.topP.onRemoveDuplicates(evt=None)
    #
    #     if self.config.fit_type in ["RT (UVPD)"]:
    #         height = 100000000000
    #         # Prepare data first
    #         rtList = np.transpose([document.RT["xvals"], document.RT["yvals"]])
    #         # Detect peaks
    #         peakList, tablelist, apexlist = pr_utils.detect_peaks_chromatogram(
    #             rtList, self.config.fit_threshold, add_buffer=1
    #         )
    #         peak_count = len(peakList)
    #
    #         self.view.panelPlots.on_clear_patches("RT", True)
    #         self.view.panelPlots.on_add_marker(
    #             xvals=apexlist[:, 0],
    #             yvals=apexlist[:, 1],
    #             color=self.config.markerColor_1D,
    #             marker=self.config.markerShape_1D,
    #             size=self.config.markerSize_1D,
    #             plot="RT",
    #             clear_first=True,
    #         )
    #         last = len(tablelist) - 1
    #         for i, rt in enumerate(tablelist):
    #             if i % 2:
    #                 color = (1, 0, 0)
    #             else:
    #                 color = (0, 0, 1)
    #             xmin = rt[0]
    #             if xmin == 1:
    #                 pass
    #             else:
    #                 xmin = xmin - 1
    #             width = rt[1] - xmin + 1
    #             if i == last:
    #                 width = width - 1
    #                 self.view.panelPlots.on_add_patch(
    #                     xmin,
    #                     ymin,
    #                     width,
    #                     height,
    #                     color=color,
    #                     #
    #                     alpha=(self.config.markerTransparency_1D/100),
    #                     plot="RT",
    #                     repaint=True,
    #                 )
    #             else:
    #                 self.view.panelPlots.on_add_patch(
    #                     xmin,
    #                     ymin,
    #                     width,
    #                     height,
    #                     color=color,
    #                     #
    #                     alpha=(self.config.markerTransparency_1D/100),
    #                     plot="RT",
    #                     repaint=False,
    #                 )
    #
    #     # Mass spectra
    #     if self.config.fit_type in ["MS", "MS/RT"]:
    #         if document.gotMS:
    #             if self.config.fit_smoothPeaks:
    #                 msX = document.massSpectrum["xvals"]
    #                 msY = document.massSpectrum["yvals"]
    #                 # Smooth data
    #                 msY = pr_spectra.smooth_gaussian_1d(data=msY, sigma=self.config.fit_smooth_sigma)
    #                 msY = pr_spectra.normalize_1D(msY)
    #             else:
    #                 msX = document.massSpectrum["xvals"]
    #                 msY = document.massSpectrum["yvals"]
    #
    #             msList = np.transpose([msX, msY])
    #             try:
    #                 mzRange = dataPlot.onGetXYvals(axes="x")  # using shortcut
    #             except AttributeError:
    #                 mzRange = document.massSpectrum["xlimits"]
    #
    #             if self.config.fit_xaxis_limit:
    #                 # Get current m/z range
    #                 msList = pr_utils.get_narrow_data_range(data=msList, mzRange=mzRange)
    # get index of that m/z range
    #
    #             # find peaks
    #             if method == 1:
    #                 peakList = pr_utils.detect_peaks_spectrum(
    #                     data=msList, window=self.config.fit_window, threshold=self.config.fit_threshold
    #                 )
    #             else:
    #                 peakList = pr_utils.detect_peaks_spectrum2(
    #                     msX, msY, window=self.config.fit_window, threshold=self.config.fit_threshold
    #                 )
    #             height = 100000000000
    #             width = self.config.fit_width * 2
    #             peak_count = len(peakList)
    #             last_peak = peak_count - 1
    #             if peak_count > 0:
    #                 # preset peaklist with space for other parameters
    #                 peakList = np.c_[
    #                     peakList, np.zeros(len(peakList)), np.empty(len(peakList)), np.empty(len(peakList))
    #                 ]
    #
    #                 self.view.panelPlots.mainBook.SetSelection(pageID)  # using shortcut
    #                 self.presenter.view.panelPlots.on_clear_patches(plot=markerPlot)
    #                 # Plotting smoothed (or not) MS
    #                 if document.dataType == "Type: CALIBRANT":
    #                     self.view.panelPlots.on_plot_MS_DT_calibration(
    #                         msX=msX,
    #                         msY=msY,
    #                         xlimits=document.massSpectrum["xlimits"],
    #                         color=self.config.lineColour_1D,
    #                         plotType="MS",
    #                         view_range=mzRange,
    #                     )
    #                 else:
    #                     name_kwargs = {"document": document.title, "dataset": "Mass Spectrum"}
    #                     self.view.panelPlots.on_plot_ms(
    #                         msX, msY, xlimits=document.massSpectrum["xlimits"], view_range=mzRange, **name_kwargs
    #                     )
    #                 # clear plots
    #                 self.presenter.view.panelPlots.on_clear_labels()
    #
    #                 for i, peak in enumerate(peakList):
    #                     if i == last_peak:
    #                         repaint = True
    #                     else:
    #                         repaint = False
    #
    #                     # preset all variables
    #                     mzStart = peak[0] - (self.config.fit_width * self.config.fit_asymmetric_ratio)
    #                     mzEnd = mzStart + width
    #
    #                     if method == 1:  # old method
    #                         mzNarrow = pr_utils.get_narrow_data_range(data=msList, mzRange=(mzStart, mzEnd))
    #                         label_height = np.round(pr_utils.find_peak_maximum(mzNarrow), 2)
    #                         narrow_count = len(mzNarrow)
    #                     else:
    #                         msXnarrow, msYnarrow = pr_utils.get_narrow_data_range_1D(msX, msY,
    #                         x_range=(mzStart, mzEnd))
    #                         label_height = np.round(pr_utils.find_peak_maximum_1D(msYnarrow), 2)
    #                         narrow_count = len(msXnarrow)
    #
    #                     charge = 0
    #
    #                     # detect charges
    #                     if self.config.fit_highRes:
    #                         # Iterate over the peaklist
    #                         isotope_peaks_x, isotope_peaks_y = [], []
    #                         if narrow_count > 0:
    #                             if method == 1:  # old method
    #                                 highResPeaks = pr_utils.detect_peaks_spectrum(
    #                                     data=mzNarrow,
    #                                     window=self.config.fit_highRes_window,
    #                                     threshold=self.config.fit_highRes_threshold,
    #                                 )
    #                             else:
    #                                 highResPeaks = pr_utils.detect_peaks_spectrum2(
    #                                     msXnarrow,
    #                                     msYnarrow,
    #                                     window=self.config.fit_highRes_window,
    #                                     threshold=self.config.fit_highRes_threshold,
    #                                 )
    #                             peakDiffs = np.diff(highResPeaks[:, 0])
    #                             if len(peakDiffs) > 0:
    #                                 charge = int(np.round(1 / np.round(np.average(peakDiffs), 4), 0))
    #
    #                             try:
    #                                 max_index = np.where(highResPeaks[:, 1] == np.max(highResPeaks[:, 1]))
    #                                 isotopic_max_val_x, isotopic_max_val_y = (
    #                                     highResPeaks[max_index, :][0][0][0],
    #                                     highResPeaks[max_index, :][0][0][1],
    #                                 )
    #                             except Exception:
    #                                 isotopic_max_val_x, isotopic_max_val_y = None, None
    #
    #                             # Assumes positive mode
    #                             peakList[i, 2] = charge
    #                             if isotopic_max_val_x is not None:
    #                                 peakList[i, 3] = isotopic_max_val_x
    #                                 peakList[i, 4] = isotopic_max_val_y
    #
    #                             if self.config.fit_highRes_isotopicFit:
    #                                 isotope_peaks_x.append(highResPeaks[:, 0].tolist())
    #                                 isotope_peaks_y.append(highResPeaks[:, 1].tolist())
    #
    #                     # generate label
    #                     if self.config.fit_show_labels and peak_count <= self.config.fit_show_labels_max_count:
    #                         if self.config.fit_show_labels_mz and self.config.fit_show_labels_int:
    #                             if charge != 0:
    #                                 label = "{:.2f}, {:.2f}\nz={}".format(peak[0], label_height, charge)
    #                             else:
    #                                 label = "{:.2f}, {:.2f}".format(peak[0], label_height)
    #                         elif self.config.fit_show_labels_mz and not self.config.fit_show_labels_int:
    #                             if charge != 0:
    #                                 label = "{:.2f}\nz={}".format(peak[0], charge)
    #                             else:
    #                                 label = "{:.2f}".format(peak[0])
    #                         elif not self.config.fit_show_labels_mz and self.config.fit_show_labels_int:
    #                             if charge != 0:
    #                                 label = "{:.2f}\nz={}".format(label_height, charge)
    #                             else:
    #                                 label = "{:.2f}".format(label_height)
    #
    #                     # add isotopic markers
    #                     if self.config.fit_highRes_isotopicFit:
    #                         flat_x = [item for sublist in isotope_peaks_x for item in sublist]
    #                         flat_y = [item for sublist in isotope_peaks_y for item in sublist]
    #                         self.presenter.view.panelPlots.on_plot_markers(
    #                             xvals=flat_x,
    #                             yvals=flat_y,
    #                             color=(1, 0, 0),
    #                             marker="o",
    #                             size=15,
    #                             plot=markerPlot,
    #                             repaint=repaint,
    #                         )
    #
    #                     # add labels
    #                     if self.config.fit_show_labels and peak_count <= self.config.fit_show_labels_max_count:
    #                         self.presenter.view.panelPlots.on_plot_labels(
    #                             xpos=peak[0], yval=label_height / dataPlot.y_divider, label=label, repaint=repaint
    #                         )
    #
    #                     # highlight in MS
    #                     if self.config.fit_highlight:
    #                         self.presenter.view.panelPlots.on_plot_patches(
    #                             mzStart,
    #                             ymin,
    #                             width,
    #                             height,
    #                             color=self.config.markerColor_1D,
    #                             alpha=(self.config.markerTransparency_1D),
    #                             repaint=repaint,
    #                             plot=markerPlot,
    #                         )
    #                 # add peaks to annotations dictionary
    #                 if self.config.fit_addPeaksToAnnotations:
    #                     # get document annotations
    #                     annotations = self.get_document_annotations()
    #                     for i, mz in enumerate(peakList):
    #                         peak = mz[0]
    #                         min_value = np.round(peak - (self.config.fit_width * self.config.fit_asymmetric_ratio), 4)
    #                         max_value = np.round(min_value + width, 4)
    #
    #                         mz_narrow = pr_utils.get_narrow_data_range(msList, mzRange=[min_value, max_value])
    #                         intensity = pr_utils.find_peak_maximum(mz_narrow)
    #                         max_index = np.where(mz_narrow[:, 1] == intensity)[0]
    #                         intensity = np.round(intensity, 2)
    #                         try:
    #                             position = mz_narrow[max_index, 0]
    #                         except Exception:
    #                             position = max_value - ((max_value - min_value) / 2)
    #                         try:
    #                             position = position[0]
    #                         except Exception:
    #                             pass
    #
    #                         try:
    #                             charge_value = int(mz[2])
    #                         except Exception:
    #                             charge_value = 0
    #                         if len(mz) > 3 and mz[3] > 1:
    #                             isotopic_max_val_x = mz[3]
    #                             isotopic_max_val_y = mz[4]
    #                             annotation_dict = {
    #                                 "min": min_value,
    #                                 "max": max_value,
    #                                 "charge": charge_value,
    #                                 "intensity": intensity,
    #                                 "label": "",
    #                                 "color": self.config.interactive_ms_annotations_color,
    #                                 "isotopic_x": isotopic_max_val_x,
    #                                 "isotopic_y": isotopic_max_val_y,
    #                             }
    #                         else:
    #                             annotation_dict = {
    #                                 "min": min_value,
    #                                 "max": max_value,
    #                                 "charge": charge_value,
    #                                 "intensity": intensity,
    #                                 "label": "",
    #                                 "isotopic_x": position,
    #                                 "isotopic_y": intensity,
    #                                 "color": self.config.interactive_ms_annotations_color,
    #                             }
    #                         name = "{} - {}".format(min_value, max_value)
    #                         annotations[name] = annotation_dict
    #
    #                     self.set_document_annotations(annotations)
    #                 #                         self.data_handling.on_update_document(document)
    #
    #                 # add found peaks to the table
    #                 if self.config.fit_addPeaks:
    #                     if document.dataType in ["Type: ORIGAMI", "Type: MANUAL"]:
    #                         self.view.on_toggle_panel(evt=ID_window_ionList, check=True)
    #                         for mz in peakList:
    #                             # New in 1.0.4: Added slightly assymetric envelope to the peak
    #                             xmin = np.round(mz[0] - (self.config.fit_width * self.config.fit_asymmetric_ratio), 2)
    #                             xmax = xmin + width
    #                             try:
    #                                 charge = str(int(mz[2]))
    #                             except Exception:
    #                                 charge = ""
    #                             intensity = np.round(mz[1] * 100, 1)
    #                             if not panel.on_check_duplicate(f"{xmin}-{xmax}", self.presenter.currentDoc):
    #                                 add_dict = {
    #                                     "mz_start": xmin,
    #                                     "mz_end": xmax,
    #                                     "charge": charge,
    #                                     "color": self.config.customColors[get_random_int(0, 15)],
    #                                     "mz_ymax": intensity,
    #                                     "colormap": self.config.overlay_cmaps[
    #                                         get_random_int(0, len(self.config.overlay_cmaps) - 1)
    #                                     ],
    #                                     "alpha": self.config.overlay_defaultAlpha,
    #                                     "mask": self.config.overlay_defaultMask,
    #                                     "document": self.presenter.currentDoc,
    #                                 }
    #                                 panel.on_add_to_table(add_dict)
    #
    #                     elif document.dataType == "Type: Multifield Linear DT":
    #                         self.view.on_toggle_panel(evt=ID_window_multiFieldList, check=True)
    #                         for mz in peakList:
    #                             xmin = np.round(mz[0] - (self.config.fit_width * 0.75), 2)
    #                             xmax = xmin + width
    #                             try:
    #                                 charge = str(int(mz[2]))
    #                             except Exception:
    #                                 charge = ""
    #                             intensity = np.round(mz[1] * 100, 1)
    #                             tempList.Append([xmin, xmax, intensity, charge, self.presenter.currentDoc])
    #                         # Removing duplicates
    #                         self.view.panelLinearDT.bottomP.onRemoveDuplicates(evt=None)
    #
    #                     elif document.dataType == "Type: CALIBRANT":
    #                         self.view.on_toggle_panel(evt=ID_window_ccsList, check=True)
    #                         for mz in peakList:
    #                             xmin = np.round(mz[0] - (self.config.peakWidth * 0.75), 2)
    #                             xmax = xmin + width
    #                             try:
    #                                 charge = str(int(mz[2]))
    #                             except Exception:
    #                                 charge = ""
    #                             intensity = np.round(mz[1] * 100, 1)
    #                             tempList.Append([self.presenter.currentDoc, xmin, xmax, "", charge])
    #                         # Removing duplicates
    #                         self.view.panelCCS.topP.onRemoveDuplicates(evt=None)
    #
    #         msg = "Found {} peaks in {:.4f} seconds.".format(peak_count, time.time() - tstart)
    #         self.presenter.onThreading(None, (msg, 4), action="updateStatusbar")

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

    def on_get_peptide_fragments(self, spectrum_dict, label_format={}, get_lists=False, **kwargs):
        tstart = time.time()
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
                len(found_peaks), peptide, time.time() - tstart
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

    def smooth_spectrum(self, mz_y, method="gaussian"):
        if method == "gaussian":
            mz_y = pr_spectra.smooth_gaussian_1d(mz_y, self.config.fit_smooth_sigma)

        return mz_y
