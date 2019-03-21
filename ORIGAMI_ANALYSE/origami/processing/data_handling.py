import wx
import os
from pubsub import pub
import numpy as np

from utils.converters import byte2str
from utils.random import randomIntegerGenerator
from utils.color import convertRGB255to1, convertRGB1to255
from ids import ID_window_ionList, ID_window_multiFieldList


class data_handling():

    def __init__(self, presenter, view, config):
        self.presenter = presenter
        self.view = view
        self.config = config

        # processing links
        self.data_processing = self.presenter.data_processing

        # panel links
        self.documentTree = view.panelDocuments.documents

        self.plotsPanel = self.view.plotsPanel

        self.ionPanel = self.view.panelMultipleIons()
        self.ionList = self.ionPanel.peaklist

        self.textPanel = self.view.panelMultipleText
        self.textList = self.textPanel.peaklist

        self.filesPanel = self.view.panelMML
        self.filesList = self.filesPanel.peaklist

        # Setup listeners
        pub.subscribe(self.extract_from_plot_1D, 'extract_from_plot_1D')
        pub.subscribe(self.extract_from_plot_2D, 'extract_from_plot_2D')

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

    @staticmethod
    def get_path_and_fname(path, simple=False):
        """
        Retrieve file path and filename. Also check whether path exists.
        path: str
            file path
        simple: bool
            only return path (without filename) and filename
        """

        # strip file extension from path name
        if path.endswith((".hdi", ".imzML", ".raw", ".pickle")):
            path, _ = os.path.splitext(path)

        full_path = path
        path, fname = os.path.split(path)
        fname, _ = os.path.splitext(fname)
        is_path = os.path.isdir(path)

        if simple:
            return path, byte2str(fname)

        return full_path, path, fname, is_path

    def extract_from_plot_1D(self, xvalsMin, xvalsMax, yvalsMax, currentView=None, currentDoc=""):
        self.currentPage = self.panelPlots._get_page_text()
        self.SetStatusText("", number=4)

        document = self._on_get_document()
        document_title = document.title

        if self.currentPage in ['RT', 'MS', '1D', '2D'] and document.dataType == 'Type: Interactive':
            args = ("Cannot extract data from Interactive document", 4)
            self.presenter.onThreading(None, args, action='updateStatusbar')
            return

        # Extract mass spectrum from mobiligram window
        elif self.currentPage == '1D':
            dt_label = self.panelPlots.plot1D.plot_labels.get("xlabel", "Drift time (bins)")

            if xvalsMin == None or xvalsMax == None:
                args = ('Your extraction range was outside the window. Please try again', 4)
                self.presenter.onThreading(None, args, action='updateStatusbar')
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
            if xvalsMin == None or xvalsMax == None:
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

                _add_to_table = {"mz_start": mzStart, "mz_end": mzEnd, "charge": charge,
                                 "mz_ymax": mzYMax, "color": convertRGB1to255(color),
                                 "colormap": self.config.overlay_cmaps[randomIntegerGenerator(0, len(self.config.overlay_cmaps) - 1)],
                                 "alpha": self.config.overlay_defaultAlpha,
                                 "mask": self.config.overlay_defaultMask,
                                 "document": currentDoc}
                self.ionPanel.on_add_to_table(_add_to_table, check_color=False)

                if self.config.showRectanges:
                    self.panelPlots.on_plot_patches(mzStart, 0, (mzEnd - mzStart), 100000000000,
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
                    self.panelPlots.on_plot_patches(mzStart, 0, (mzEnd - mzStart), 100000000000,
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
            if outcome == True:
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
            if outcome == True:
                return
            xvalDiff = xvalsMax - xvalsMin.astype(int)
            self.view.panelLinearDT.topP.peaklist.Append([xvalsMin, xvalsMax,
                                                     xvalDiff, "",
                                                     self.presenter.currentDoc])

            self.panelPlots.on_add_patch(xvalsMin, 0, (xvalsMax - xvalsMin), 100000000000,
                                         color=self.config.annotColor,
                                         alpha=(self.config.annotTransparency / 100),
                                         repaint=True, plot="RT")

        # Extract mass spectrum from chromatogram window
        elif self.currentPage == 'RT' and document.dataType != 'Type: Multifield Linear DT':
            rt_label = self.panelPlots.plotRT.plot_labels.get("xlabel", "Scans")

            # Get values
            if xvalsMin == None or xvalsMax == None:
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
        self.currentPage = self.panelPlots.mainBook.GetPageText(self.panelPlots.mainBook.GetSelection())

        if self.currentPage == "DT/MS":
            xlabel = self.panelPlots.plotMZDT.plot_labels.get("xlabel", "m/z")
            ylabel = self.panelPlots.plotMZDT.plot_labels.get("ylabel", "Drift time (bins)")
        elif self.currentPage == "2D":
            xlabel = self.panelPlots.plot2D.plot_labels.get("xlabel", "Scans")
            ylabel = self.panelPlots.plot2D.plot_labels.get("ylabel", "Drift time (bins)")

        xmin, xmax, ymin, ymax = dataOut
        if xmin == None or xmax == None or ymin == None or ymax == None:
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
