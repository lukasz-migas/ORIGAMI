# Standard library imports
import gc
import os
import sys
import logging
import warnings
import threading
import webbrowser
import faulthandler
from sys import platform

# Third-party imports
import wx

# Local imports
import origami.processing.UniDec.unidec as unidec
from origami.ids import ID_helpCite
from origami.ids import ID_helpGuide
from origami.ids import ID_helpGitHub
from origami.ids import ID_helpYoutube
from origami.ids import ID_helpHomepage
from origami.ids import ID_helpHTMLEditor
from origami.ids import ID_helpNewVersion
from origami.ids import ID_helpReportBugs
from origami.ids import ID_addNewManualDoc
from origami.ids import ID_helpNewFeatures
from origami.ids import ID_addNewOverlayDoc
from origami.ids import ID_addNewCalibrationDoc
from origami.ids import ID_addNewInteractiveDoc
from origami.document import document as documents
from origami.utils.time import getTime
from origami.icons.icons import ICONS
from origami.main_window import MainWindow
from origami.config.config import CONFIG
from origami.utils.logging import set_logger
from origami.utils.logging import set_logger_level
from origami.config.environment import ENV
from origami.help_documentation import OrigamiHelp
from origami.gui_elements.misc_dialogs import DialogSimpleAsk

# needed to avoid annoying warnings to be printed on console
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

logger = logging.getLogger(__name__)
faulthandler.enable()

# disable MPL logger
logging.getLogger("matplotlib").setLevel(logging.ERROR)


class ORIGAMI:
    def __init__(self, *args, **kwargs):
        self.__wx_app = wx.App(redirect=False, filename="ORIGAMI")
        self.view = None
        self.initilize_app(*args, **kwargs)

    def start(self):
        self.view.Show()
        self.__wx_app.MainLoop()

    def on_reboot_origami(self, evt):
        """
        Reset window
        """
        self.view.Destroy()
        self.view = None
        self.view = MainWindow(self, config=self.config, icons=self.icons, title="ORIGAMI", helpInfo="")
        self.view.Show()

    def quit(self):
        self.__wx_app.ProcessIdle()
        self.__wx_app.ExitMainLoop()
        self.view.Destroy()
        return True

    def end_app_session(self):
        wx.CallAfter(self.quit, force=True)

    def initilize_app(self, *args, **kwargs):
        self.config = CONFIG
        self.icons = ICONS
        self.help = OrigamiHelp()

        # Load configuration file
        self.on_import_configuration_on_startup()

        # Setup variables
        self.initilize_state()
        self.view = MainWindow(
            self, config=self.config, icons=self.icons, helpInfo=self.help, title="ORIGAMI - %s " % self.config.version
        )
        self.__wx_app.SetTopWindow(self.view)
        self.__wx_app.SetAppName("ORIGAMI - %s " % self.config.version)
        self.__wx_app.SetVendorName("Lukasz G. Migas")

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
        self.view.on_update_recent_files()

        self.logging = self.config.logging
        self.config._processID = os.getpid()

        # add data processing module
        self.data_processing = self.view.data_processing
        self.data_handling = self.view.data_handling
        self.data_visualisation = self.view.data_visualisation

        gc.enable()
        self.on_start_logging()

        # add binding to UniDec engine
        self.config.unidec_engine = unidec.UniDec()

        # Set unidec directory
        self.config.unidec_path = self.config.unidec_engine.config.UniDecPath

        # check version
        self.on_check_version()

        # only check if on Windows
        if self.config.checkForDriftscopeAtStart and platform == "win32":
            self.config.initilize_paths()
            self.initilize_registry()

        # add data handling and processing modules
        self.view.panelDocuments.documents.setup_handling_and_processing()
        self.view.panelMultipleIons.setup_handling_and_processing()
        self.view.panelMultipleText.setup_handling_and_processing()
        self.view.panelMML.setup_handling_and_processing()
        self.view.panelPlots.setup_handling_and_processing()
        self.view.panelParametersEdit.setup_handling_and_processing()
        self.data_processing.setup_handling_and_processing()
        self.data_visualisation.setup_handling_and_processing()

        #         if self.config.debug and not self.config.testing:
        #             self._debug_()

        if self.config.testing:
            self._test_()

    def initilize_state(self):
        """Pre-set variables"""
        self.currentDoc = None

    def initilize_registry(self):
        """Update reg keys to allow viewing of JS/HTML inside ORIGAMI windows"""
        from origami.utils.windows_reg_edit import set_ie_emulation_level
        from origami.utils.windows_reg_edit import set_ie_lockdown_level

        set_ie_emulation_level()
        set_ie_lockdown_level()
        logger.debug("Initilized registry...")

    def _test_(self):
        """Exit application after performing some tests

        GUI testing is tricky, so we simply invoke a couple of functions and ensure they run without raising any
        errors. If everything is configured correctly, all tasks will complete and the application will close without
        errors.
        """
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
            self.data_handling.on_extract_MS_from_mobilogram(65, 75)
            self.data_handling.on_extract_MS_from_mobilogram(11, 15, "Arrival time (ms)")

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
        set_logger(file_path=self.config.loggingFile_path)
        set_logger_level(verbose="DEBUG")

        logger.info("Logs can be found in {}".format(self.config.loggingFile_path))

    def on_create_document(self, name, path, **kwargs):
        """Create document"""
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
            thread_obj = threading.Thread(target=target.save_figure, args=(path,), kwargs=kwargs)

        elif action == "updateStatusbar":
            if len(args) == 2:
                msg, position = args
                thread_obj = threading.Thread(target=self.view.updateStatusbar, args=(msg, position))
            elif len(args) == 3:
                msg, position, delay = args
                thread_obj = threading.Thread(target=self.view.updateStatusbar, args=(msg, position, delay))
        elif action == "export_settings":
            thread_obj = threading.Thread(target=self.config.saveConfigXML, args=args)

        # Start thread
        try:
            thread_obj.start()
        except Exception:
            print("Failed to execute the operation in threaded mode. Consider switching it off?")

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

    def _get_replot_data(self, data_format):
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
            self.view.panelDocuments.documents.set_document(document_old=ENV[document.title], document_new=document)

        # update dictionary
        ENV[document.title] = document
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

    def on_check_version(self, evt=None):
        """
        Simple function to check whether this is the newest version available
        """
        # TODO: move his function to separate module (e.g. utils/version.py - can be unit tested)
        logger.info("Not implemented yet")


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


if __name__ == "__main__":
    app = ORIGAMI(redirect=False)
    app.start()
