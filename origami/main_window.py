"""Main frame module"""
# Standard library imports
import os
import logging
import webbrowser
from time import sleep
from time import gmtime
from time import strftime
from typing import List
from typing import Optional
from functools import partial

# Third-party imports
import numpy as np
import psutil
import wx.aui
from pubsub import pub

# Local imports
from origami.ids import ID_WHATS_NEW
from origami.ids import ID_SHOW_ABOUT
from origami.ids import ID_CHECK_VERSION
from origami.ids import ID_RESET_ORIGAMI
from origami.ids import ID_quit
from origami.ids import ID_helpCite
from origami.ids import ID_helpGuide
from origami.ids import ID_helpAuthor
from origami.ids import ID_helpGitHub
from origami.ids import ID_openConfig
from origami.ids import ID_renameItem
from origami.ids import ID_saveConfig
from origami.ids import ID_window_all
from origami.ids import ID_helpYoutube
from origami.ids import ID_save1DImage
from origami.ids import ID_save2DImage
from origami.ids import ID_save3DImage
from origami.ids import ID_saveMSImage
from origami.ids import ID_saveRTImage
from origami.ids import ID_fileMenu_MGF
from origami.ids import ID_helpHomepage
from origami.ids import ID_openAsConfig
from origami.ids import ID_openDocument
from origami.ids import ID_saveAsConfig
from origami.ids import ID_saveDocument
from origami.ids import ID_clearAllPlots
from origami.ids import ID_fileMenu_mzML
from origami.ids import ID_saveMZDTImage
from origami.ids import ID_saveRMSDImage
from origami.ids import ID_saveRMSFImage
from origami.ids import ID_helpGuideLocal
from origami.ids import ID_helpHTMLEditor
from origami.ids import ID_helpNewVersion
from origami.ids import ID_helpReportBugs
from origami.ids import ID_window_ionList
from origami.ids import ID_windowMaximize
from origami.ids import ID_windowMinimize
from origami.ids import ID_addNewManualDoc
from origami.ids import ID_documentRecent0
from origami.ids import ID_documentRecent1
from origami.ids import ID_documentRecent2
from origami.ids import ID_documentRecent3
from origami.ids import ID_documentRecent4
from origami.ids import ID_documentRecent5
from origami.ids import ID_documentRecent6
from origami.ids import ID_documentRecent7
from origami.ids import ID_documentRecent8
from origami.ids import ID_documentRecent9
from origami.ids import ID_help_UniDecInfo
from origami.ids import ID_helpNewFeatures
from origami.ids import ID_selectCalibrant
from origami.ids import ID_window_controls
from origami.ids import ID_window_textList
from origami.ids import ID_addNewOverlayDoc
from origami.ids import ID_check_Driftscope
from origami.ids import ID_help_page_UniDec
from origami.ids import ID_saveOverlayImage
from origami.ids import ID_showPlotDocument
from origami.ids import ID_windowFullscreen
from origami.ids import ID_assignChargeState
from origami.ids import ID_docTree_compareMS
from origami.ids import ID_help_page_ORIGAMI
from origami.ids import ID_help_page_overlay
from origami.ids import ID_importAtStart_CCS
from origami.ids import ID_saveAsInteractive
from origami.ids import ID_extraSettings_rmsd
from origami.ids import ID_fileMenu_thermoRAW
from origami.ids import ID_help_page_linearDT
from origami.ids import ID_saveWaterfallImage
from origami.ids import ID_showPlotMSDocument
from origami.ids import ID_docTree_plugin_MSMS
from origami.ids import ID_docTree_plugin_UVPD
from origami.ids import ID_fileMenu_openRecent
from origami.ids import ID_help_page_OtherData
from origami.ids import ID_saveDataCSVDocument
from origami.ids import ID_saveRMSDmatrixImage
from origami.ids import ID_window_documentList
from origami.ids import ID_addNewInteractiveDoc
from origami.ids import ID_extraSettings_legend
from origami.ids import ID_extraSettings_plot1D
from origami.ids import ID_extraSettings_plot2D
from origami.ids import ID_extraSettings_plot3D
from origami.ids import ID_extraSettings_violin
from origami.ids import ID_fileMenu_clearRecent
from origami.ids import ID_plots_showCursorGrid
from origami.ids import ID_extraSettings_general
from origami.ids import ID_help_page_dataLoading
from origami.ids import ID_help_page_Interactive
from origami.ids import ID_load_multiple_text_2D
from origami.ids import ID_window_multipleMLList
from origami.ids import ID_extraSettings_colorbar
from origami.ids import ID_checkAtStart_Driftscope
from origami.ids import ID_extraSettings_waterfall
from origami.ids import ID_help_page_multipleFiles
from origami.ids import ID_annotPanel_otherSettings
from origami.ids import ID_help_page_CCScalibration
from origami.ids import ID_help_page_dataExtraction
from origami.ids import ID_help_page_gettingStarted
from origami.ids import ID_importExportSettings_file
from origami.ids import ID_load_masslynx_raw_ms_only
from origami.ids import ID_load_origami_masslynx_raw
from origami.ids import ID_mainPanel_openSourceFiles
from origami.ids import ID_openCCScalibrationDatabse
from origami.ids import ID_unidecPanel_otherSettings
from origami.ids import ID_extraSettings_general_plot
from origami.ids import ID_importExportSettings_image
from origami.ids import ID_load_multiple_masslynx_raw
from origami.ids import ID_importExportSettings_peaklist
from origami.ids import ID_help_page_annotatingMassSpectra
from origami.ids import ID_load_multiple_origami_masslynx_raw
from origami.styles import make_menu_item
from origami.utils.path import clean_directory
from origami.panel_plots import PanelPlots
from origami.utils.check import compare_versions
from origami.utils.check import get_latest_version
from origami.config.config import CONFIG
from origami.panel_peaklist import PanelPeaklist
from origami.panel_textlist import PanelTextlist
from origami.panel_multi_file import PanelMultiFile
from origami.config.environment import ENV
from origami.panel_document_tree import PanelDocumentTree
from origami.readers.io_text_files import check_file_type
from origami.handlers.data_handling import DataHandling
from origami.handlers.data_processing import DataProcessing
from origami.gui_elements.misc_dialogs import DialogBox
from origami.handlers.data_visualisation import DataVisualization
from origami.gui_elements.panel_export_settings import PanelExportSettings
from origami.gui_elements.panel_plot_parameters import PanelVisualisationSettingsEditor
from origami.gui_elements.dialog_notify_new_version import DialogNewVersion
from origami.gui_elements.dialog_notify_open_documents import DialogNotifyOpenDocuments
from origami.widgets.interactive.panel_interactive_creator import PanelInteractiveCreator

logger = logging.getLogger(__name__)


# TODO: change toolbar to be vertical and size of icons to be 32x32
# TODO: update icons


class MainWindow(wx.Frame):
    """Main frame"""

    def __init__(self, parent, config, helpInfo, icons, title="ORIGAMI"):
        wx.Frame.__init__(self, None, title=title)

        # Extract size of screen
        self.displaysize = wx.GetDisplaySize()
        self.SetDimensions(0, 0, self.displaysize[0], self.displaysize[1] - 50)
        # Setup config container
        self.icons = icons
        self.help = helpInfo
        self.presenter = parent

        self.plot_data = {}
        self.plot_scale = {}
        self.plot_name = None

        self._fullscreen = False

        file_drop_target = DragAndDrop(self)
        self.SetDropTarget(file_drop_target)

        icon = wx.EmptyIcon()
        icon.CopyFromBitmap(self.icons.iconsLib["origamiLogoDark16"])
        self.SetIcon(icon)

        # View parameters
        self.mode = None
        self.xpos = None
        self.ypos = None
        self.xy_start = None
        self.resized = False

        self.menubar = None
        self.toolbar = None

        # keep track of which windows are managed
        self._managed_windows = dict()
        self._n_managed_windows = 0

        CONFIG.startTime = strftime("%Y_%m_%d-%H-%M-%S", gmtime())

        # Bind commands to events
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_IDLE, self.on_idle)

        # Setup Notebook manager
        self.window_mgr = wx.aui.AuiManager(self)
        self.window_mgr.SetDockSizeConstraint(1, 1)

        # Load panels
        self.panelDocuments = PanelDocumentTree(self, CONFIG, self.icons, self.presenter)

        self.panelPlots = PanelPlots(self, CONFIG, self.presenter)
        # self.panelMultipleIons = PanelPeaklist(self, self.icons, self.presenter)
        self.panelMultipleText = PanelTextlist(self, self.icons, self.presenter)
        # self.panelMML = PanelMultiFile(self, self.icons, self.presenter)

        self.panelParametersEdit = PanelVisualisationSettingsEditor(
            self, self.presenter, CONFIG, self.icons, window=None
        )

        # add handling, processing and visualisation pipelines
        self.data_processing = DataProcessing(self.presenter, self, CONFIG)
        self.data_handling = DataHandling(self.presenter, self, CONFIG)
        self.data_visualisation = DataVisualization(self.presenter, self, CONFIG)

        # make toolbar
        self.make_toolbar()

        # Panel to store document information
        self.window_mgr.AddPane(
            self.panelDocuments,
            wx.aui.AuiPaneInfo()
            .Left()
            .Caption("Documents")
            .MinSize((250, 100))
            .GripperTop()
            .BottomDockable(False)
            .TopDockable(False)
            .Show(CONFIG._windowSettings["Documents"]["show"])
            .CloseButton(CONFIG._windowSettings["Documents"]["close_button"])
            .CaptionVisible(CONFIG._windowSettings["Documents"]["caption"])
            .Gripper(CONFIG._windowSettings["Documents"]["gripper"]),
        )

        self.window_mgr.AddPane(
            self.panelPlots,
            wx.aui.AuiPaneInfo()
            .CenterPane()
            .Caption("Plot")
            .Show(CONFIG._windowSettings["Plots"]["show"])
            .CloseButton(CONFIG._windowSettings["Plots"]["close_button"])
            .CaptionVisible(CONFIG._windowSettings["Plots"]["caption"])
            .Gripper(CONFIG._windowSettings["Plots"]["gripper"]),
        )

        # # Panel to extract multiple ions from ML files
        # self.window_mgr.AddPane(
        #     self.panelMultipleIons,
        #     wx.aui.AuiPaneInfo()
        #     .Right()
        #     .Caption("Peak list")
        #     .MinSize((300, -1))
        #     .GripperTop()
        #     .BottomDockable(True)
        #     .TopDockable(False)
        #     .Show(CONFIG._windowSettings["Peak list"]["show"])
        #     .CloseButton(CONFIG._windowSettings["Peak list"]["close_button"])
        #     .CaptionVisible(CONFIG._windowSettings["Peak list"]["caption"])
        #     .Gripper(CONFIG._windowSettings["Peak list"]["gripper"]),
        # )

        # Panel to operate on multiple text files
        self.window_mgr.AddPane(
            self.panelMultipleText,
            wx.aui.AuiPaneInfo()
            .Right()
            .Caption("Heatmap List")
            .MinSize((300, -1))
            .GripperTop()
            .BottomDockable(True)
            .TopDockable(False)
            .Show(CONFIG._windowSettings["Text files"]["show"])
            .CloseButton(CONFIG._windowSettings["Text files"]["close_button"])
            .CaptionVisible(CONFIG._windowSettings["Text files"]["caption"])
            .Gripper(CONFIG._windowSettings["Text files"]["gripper"]),
        )
        #
        # # Panel to operate on multiple ML files
        # self.window_mgr.AddPane(
        #     self.panelMML,
        #     wx.aui.AuiPaneInfo()
        #     .Right()
        #     .Caption("Multiple files")
        #     .MinSize((300, -1))
        #     .GripperTop()
        #     .BottomDockable(True)
        #     .TopDockable(False)
        #     .Show(CONFIG._windowSettings["Multiple files"]["show"])
        #     .CloseButton(CONFIG._windowSettings["Multiple files"]["close_button"])
        #     .CaptionVisible(CONFIG._windowSettings["Multiple files"]["caption"])
        #     .Gripper(CONFIG._windowSettings["Multiple files"]["gripper"]),
        # )

        self.window_mgr.AddPane(
            self.panelParametersEdit,
            wx.aui.AuiPaneInfo()
            .Right()
            .Caption(CONFIG._windowSettings["Plot parameters"]["title"])
            .MinSize((320, -1))
            .GripperTop()
            .BottomDockable(True)
            .TopDockable(False)
            .Show(CONFIG._windowSettings["Plot parameters"]["show"])
            .CloseButton(CONFIG._windowSettings["Plot parameters"]["close_button"])
            .CaptionVisible(CONFIG._windowSettings["Plot parameters"]["caption"])
            .Gripper(CONFIG._windowSettings["Plot parameters"]["gripper"]),
        )

        # Setup listeners
        pub.subscribe(self.on_motion, "motion_xy")
        pub.subscribe(self.motion_range, "motion_range")
        pub.subscribe(self.on_distance, "change_x_axis_start")
        pub.subscribe(self.panelPlots.on_change_rmsf_zoom, "change_zoom_rmsd")
        pub.subscribe(self.on_event_mode, "motion_mode")
        #         pub.subscribe(self.data_handling.on_update_DTMS_zoom, "change_zoom_dtms")
        pub.subscribe(self.on_queue_change, "statusbar.update.queue")

        # Load other parts
        self.window_mgr.Update()
        self.make_statusbar()
        self.make_menubar()
        self.make_shortcuts()
        self.SetSize(1980, 1080)
        #         self.Maximize(True)

        # bind events
        self.Bind(wx.aui.EVT_AUI_PANE_CLOSE, self.on_closed_page)
        self.Bind(wx.aui.EVT_AUI_PANE_RESTORE, self.on_restored_page)

        # Fire up a couple of events
        self.on_update_panel_config()
        self.on_toggle_panel(evt=None)
        self.on_toggle_panel_at_start()

    def create_panel(self, which: str, document_title: str):
        """Creates new instance of panel for particular document"""

        def show_panel(_name, klass):
            panel = self.get_panel(_name)
            if panel.window:
                self.show_panel(panel=panel)
            else:
                panel = klass(self, self.icons, self.presenter)
                self.add_panel(panel, title, _name)

        if which not in ["ion", "files"]:
            raise ValueError("Currently can only instantiate [`ion`, `files`] panels")

        name = None
        if which == "ion":
            title = f"Ion table: {document_title}"
            name = f"ion; {document_title}"
            show_panel(name, PanelPeaklist)
        elif which == "files":
            title = f"Filelist: {document_title}"
            name = f"filelist; {document_title}"
            show_panel(name, PanelMultiFile)

        return name

    def get_panel(self, name: str) -> wx.aui.AuiPaneInfo:
        """Get pane based on the name"""
        pane = self.window_mgr.GetPane(name=name)
        return pane

    def show_panel(self, name: Optional[str] = None, panel: Optional[wx.aui.AuiPaneInfo] = None):
        """Show panel"""
        if name is None and panel is None:
            raise ValueError("Please provide either `name` or `panel` keyword parameter")
        if panel is None:
            panel = self.window_mgr.GetPane(name=name)
        panel.Show()
        self.window_mgr.Update()

    def hide_panel(self, name: Optional[str] = None, panel: Optional[wx.aui.AuiPaneInfo] = None):
        """Hide panel"""
        if name is None and panel is None:
            raise ValueError("Please provide either `name` or `panel` keyword parameter")
        if panel is None:
            panel = self.window_mgr.GetPane(name=name)
        panel.Hide()
        self.window_mgr.Update()

    def add_panel(
        self,
        panel: wx.Panel,
        title: str,
        name: str,
        close_btn: bool = True,
        caption_visible: bool = True,
        gripper: bool = True,
        show: bool = True,
    ):
        """Add panel to the manager"""
        self.window_mgr.AddPane(
            panel,
            wx.aui.AuiPaneInfo()
            .Caption(title)
            .CloseButton(close_btn)
            .CaptionVisible(caption_visible)
            .Gripper(gripper)
            .Show(show)
            .Window(panel)
            .Name(name)
            .DestroyOnClose(),
        )
        self.window_mgr.Update()

    def remove_pane(self, name: str):
        """Remove panel"""
        panel = self.window_mgr.GetPane(name=name)
        self.window_mgr.ClosePane(panel)
        self.window_mgr.Update()

    def on_update_panel_config(self):
        CONFIG._windowSettings["Documents"]["id"] = ID_window_documentList
        # CONFIG._windowSettings["Peak list"]["id"] = ID_window_ionList
        # CONFIG._windowSettings["Text files"]["id"] = ID_window_textList
        # CONFIG._windowSettings["Multiple files"]["id"] = ID_window_multipleMLList

    def on_toggle_panel_at_start(self):
        panelDict = {
            "Documents": ID_window_documentList,
            "Heatmap List": ID_window_textList,
            # "Multiple files": ID_window_multipleMLList,
            # "Peak list": ID_window_ionList,
            # "Text files": ID_window_textList,
        }

        for panel in [self.panelDocuments, self.panelMultipleText]:  # , self.panelMML, self.panelMultipleIons, ]:
            if self.window_mgr.GetPane(panel).IsShown():
                self.on_find_toggle_by_id(find_id=panelDict[self.window_mgr.GetPane(panel).caption], check=True)

    # def _onUpdatePlotData(self, plot_type=None):
    #     if plot_type == "2D":
    #         _data = self.presenter._get_replot_data(data_format="2D")
    #         try:
    #             yshape, xshape = _data[0].shape
    #             _yscale = yshape / np.max(_data[2])
    #             _xscale = xshape / np.max(_data[1])
    #             self.plot_data["2D"] = _data[0]
    #             self.plot_scale["2D"] = [_yscale, _xscale]
    #         except Exception:
    #             pass
    #     elif plot_type == "DT/MS":
    #         _data = self.presenter._get_replot_data(data_format="DT/MS")
    #         yshape, xshape = _data[0].shape
    #         _yscale = yshape / np.max(_data[2])
    #         _xscale = xshape / np.max(_data[1])
    #         self.plot_data["DT/MS"] = _data[0]
    #         self.plot_scale["DT/MS"] = [_yscale, _xscale]
    #     elif plot_type == "RMSF":
    #         _data = self.presenter._get_replot_data(data_format="RMSF")
    #         yshape, xshape = _data[0].shape
    #         _yscale = yshape / np.max(_data[2])
    #         _xscale = xshape / np.max(_data[1])
    #         self.plot_data["DT/MS"] = _data[0]
    #         self.plot_scale["DT/MS"] = [_yscale, _xscale]

    def on_closed_page(self, evt):
        """Keep track of which page was closed"""
        # Keep track of which window is closed
        panel_name = evt.GetPane().caption
        if panel_name in CONFIG._windowSettings:
            CONFIG._windowSettings[panel_name]["show"] = False

            # fire-up events
            try:
                evtID = self.onCheckToggleID(panel=evt.GetPane().caption)
                self.on_toggle_panel(evt=evtID)
            except Exception:
                pass

    def on_restored_page(self, evt):
        """Keep track of which page was restored"""
        # Keep track of which window is restored
        CONFIG._windowSettings[evt.GetPane().caption]["show"] = True
        evtID = self.onCheckToggleID(panel=evt.GetPane().caption)
        self.on_toggle_panel(evt=evtID)
        # fire-up events

        if evt is not None:
            evt.Skip()

    def make_statusbar(self):

        self.mainStatusbar = self.CreateStatusBar(7, wx.STB_SIZEGRIP, wx.ID_ANY)
        # 0 = current x y pos
        # 1 = m/z range
        # 2 = MSMS mass
        # 3 = status information
        # 4 = present working file
        # 5 = tool
        # 6 = process
        # 7 = queue size
        self.mainStatusbar.SetStatusWidths([250, 80, 80, 200, -1, 50, 50])
        self.mainStatusbar.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))

    def make_menubar(self):
        # TODO: revamp the menu completely
        #     separate Waters, Thermo, Text files into their own sub folders

        self.menubar = wx.MenuBar()

        # setup recent sub-menu
        self.menuRecent = wx.Menu()
        self.on_update_recent_files()

        menu_tandem = wx.Menu()
        menu_tandem.Append(ID_fileMenu_MGF, "Open Mascot Generic Format file (.mgf) [MS/MS]")
        menu_tandem.Append(ID_fileMenu_mzML, "Open mzML (.mzML) [MS/MS]")

        menu_file = wx.Menu()
        menu_file.AppendMenu(ID_fileMenu_openRecent, "Open Recent", self.menuRecent)
        menu_file.AppendSeparator()
        menu_file.AppendItem(
            make_menu_item(
                parent=menu_file,
                evt_id=ID_openDocument,
                text="Open ORIGAMI Document file (.pickle)\tCtrl+Shift+P",
                bitmap=self.icons.iconsLib["open_project_16"],
            )
        )
        menu_file.AppendSeparator()
        menu_file.AppendItem(
            make_menu_item(
                parent=menu_file,
                evt_id=ID_load_masslynx_raw_ms_only,
                text="Open Waters file (.raw) [MS only]\tCtrl+Shift+M",
                #                 bitmap=self.icons.iconsLib["open_origami_16"],
            )
        )
        menu_file_waters_imms = menu_file.AppendItem(
            make_menu_item(
                parent=menu_file,
                text="Open Waters file (.raw) [IM-MS only]",
                #                 bitmap=self.icons.iconsLib["open_origami_16"],
            )
        )
        menu_file.AppendItem(
            make_menu_item(
                parent=menu_file,
                evt_id=ID_load_origami_masslynx_raw,
                text="Open Waters file (.raw) [ORIGAMI-MS; CIU]\tCtrl+R",
                bitmap=self.icons.iconsLib["open_origami_16"],
            )
        )

        #         menu_file.AppendSeparator()

        #         menu_file.AppendItem(
        #             make_menu_item(
        #                 parent=menu_file,
        #                 id=ID_load_multiple_origami_masslynx_raw,
        #                 text="Open multiple ORIGAMI MassLynx (.raw) files [CIU]\tCtrl+Shift+Q",
        #                 bitmap=self.icons.iconsLib["open_origamiMany_16"],
        #             )
        #         )
        menu_file.AppendSeparator()
        menu_file.AppendItem(
            make_menu_item(
                parent=menu_file,
                evt_id=ID_addNewManualDoc,
                text="Create blank document [CIU; SID;...]",
                help_text="Creating this document will give you an option to load any number of .raw files afterwards",
                bitmap=self.icons.iconsLib["guide_16"],
            )
        )
        menu_file.AppendItem(
            make_menu_item(
                parent=menu_file,
                evt_id=ID_load_multiple_masslynx_raw,
                text="Create `Activation` document and open Waters file(s) (.raw) [CIU; SID; ...]",
                bitmap=self.icons.iconsLib["open_masslynxMany_16"],
            )
        )
        menu_file.AppendSeparator()
        #         menu_file.Append(ID_addCCScalibrantFile, "Open MassLynx (.raw) file [Calibration]\tCtrl+C")
        #         menu_file.Append(ID_openLinearDTRawFile, "Open MassLynx (.raw) file [Linear DT]\tCtrl+F")

        menu_file.AppendSeparator()
        menu_file.AppendItem(
            make_menu_item(
                parent=menu_file,
                evt_id=ID_fileMenu_thermoRAW,
                text="Open Thermo file (.RAW)\tCtrl+Shift+Y",
                bitmap=None,
            )
        )
        menu_file.AppendSeparator()
        menu_file_text_ms = make_menu_item(parent=menu_file, text="Open mass spectrum file(s) (.csv; .txt; .tab)")
        menu_file.AppendItem(menu_file_text_ms)
        menu_file_text_heatmap = make_menu_item(
            parent=menu_file,
            evt_id=ID_load_multiple_text_2D,
            text="Open heatmap file(s) (.csv; .txt; .tab)\tCtrl+Shift+T",
            bitmap=self.icons.iconsLib["open_textMany_16"],
        )
        menu_file.AppendItem(menu_file_text_heatmap)
        menu_file.AppendSeparator()
        menu_file.AppendMenu(wx.ID_ANY, "Open MS/MS files...", menu_tandem)
        #         menu_file.AppendSeparator()
        #         menu_file.AppendItem(
        #             make_menu_item(
        #                 parent=menu_file,
        #                 id=ID_addNewOverlayDoc,
        #                 text="Create blank COMPARISON document [CIU]",
        #                 bitmap=self.icons.iconsLib["new_document_16"],
        #             )
        #         )
        #         menu_file.AppendItem(
        #             make_menu_item(
        #                 parent=menu_file,
        #                 id=ID_addNewInteractiveDoc,
        #                 text="Create blank INTERACTIVE document",
        #                 bitmap=self.icons.iconsLib["bokehLogo_16"],
        #             )
        #         )

        menu_file.AppendSeparator()
        menu_file_clipboard_ms = make_menu_item(
            parent=menu_file,
            #                 id=ID_load_clipboard_spectrum,
            text="Grab MS spectrum from clipboard\tCtrl+V",
            bitmap=self.icons.iconsLib["filelist_16"],
        )
        menu_file.AppendItem(menu_file_clipboard_ms)

        menu_file.AppendSeparator()
        menu_file.AppendItem(
            make_menu_item(
                parent=menu_file,
                evt_id=ID_saveDocument,
                text="Save document as...",
                bitmap=self.icons.iconsLib["save16"],
            )
        )
        #         menu_file.AppendItem(
        #             make_menu_item(
        #                 parent=menu_file,
        #                 id=ID_saveAllDocuments,
        #                 text="Save all documents (.pickle)",
        #                 bitmap=self.icons.iconsLib["pickle_16"],
        #             )
        #         )
        menu_file.AppendSeparator()
        menu_file.AppendItem(
            make_menu_item(parent=menu_file, evt_id=ID_quit, text="Quit\tCtrl+Q", bitmap=self.icons.iconsLib["exit_16"])
        )
        self.menubar.Append(menu_file, "&File")

        # PLOT
        menu_plot = wx.Menu()
        menu_plot.AppendItem(
            make_menu_item(
                parent=menu_plot,
                evt_id=ID_extraSettings_general_plot,
                text="Settings: Plot &General",
                bitmap=self.icons.iconsLib["panel_plot_general_16"],
            )
        )

        menu_plot.AppendItem(
            make_menu_item(
                parent=menu_plot,
                evt_id=ID_extraSettings_plot1D,
                text="Settings: Plot &1D",
                bitmap=self.icons.iconsLib["panel_plot1D_16"],
            )
        )

        menu_plot.AppendItem(
            make_menu_item(
                parent=menu_plot,
                evt_id=ID_extraSettings_plot2D,
                text="Settings: Plot &2D",
                bitmap=self.icons.iconsLib["panel_plot2D_16"],
            )
        )

        menu_plot.AppendItem(
            make_menu_item(
                parent=menu_plot,
                evt_id=ID_extraSettings_plot3D,
                text="Settings: Plot &3D",
                bitmap=self.icons.iconsLib["panel_plot3D_16"],
            )
        )

        menu_plot.AppendItem(
            make_menu_item(
                parent=menu_plot,
                evt_id=ID_extraSettings_colorbar,
                text="Settings: &Colorbar",
                bitmap=self.icons.iconsLib["panel_colorbar_16"],
            )
        )

        menu_plot.AppendItem(
            make_menu_item(
                parent=menu_plot,
                evt_id=ID_extraSettings_legend,
                text="Settings: &Legend",
                bitmap=self.icons.iconsLib["panel_legend_16"],
            )
        )

        menu_plot.AppendItem(
            make_menu_item(
                parent=menu_plot,
                evt_id=ID_extraSettings_rmsd,
                text="Settings: &RMSD",
                bitmap=self.icons.iconsLib["panel_rmsd_16"],
            )
        )

        menu_plot.AppendItem(
            make_menu_item(
                parent=menu_plot,
                evt_id=ID_extraSettings_waterfall,
                text="Settings: &Waterfall",
                bitmap=self.icons.iconsLib["panel_waterfall_16"],
            )
        )

        menu_plot.AppendItem(
            make_menu_item(
                parent=menu_plot,
                evt_id=ID_extraSettings_violin,
                text="Settings: &Violin",
                bitmap=self.icons.iconsLib["panel_violin_16"],
            )
        )

        menu_plot.AppendItem(
            make_menu_item(
                parent=menu_plot,
                evt_id=ID_extraSettings_general,
                text="Settings: &Extra",
                bitmap=self.icons.iconsLib["panel_general2_16"],
            )
        )

        menu_plot.AppendSeparator()
        menu_plot.AppendItem(
            make_menu_item(
                parent=menu_plot,
                evt_id=ID_annotPanel_otherSettings,
                text="Settings: Annotation parameters",
                bitmap=None,
            )
        )
        menu_plot.AppendItem(
            make_menu_item(
                parent=menu_plot, evt_id=ID_unidecPanel_otherSettings, text="Settings: UniDec parameters", bitmap=None
            )
        )

        menu_plot.AppendSeparator()
        menu_plot.Append(ID_plots_showCursorGrid, "Update plot parameters")
        # menuPlot.Append(ID_plots_resetZoom, 'Reset zoom tool\tF12')
        self.menubar.Append(menu_plot, "&Plot settings")

        # VIEW
        menu_view = wx.Menu()
        menu_view.AppendItem(
            make_menu_item(
                parent=menu_view,
                evt_id=ID_clearAllPlots,
                text="&Clear all plots",
                bitmap=self.icons.iconsLib["clear_16"],
            )
        )
        menu_view.AppendSeparator()
        self.documentsPage = menu_view.Append(ID_window_documentList, "Panel: Documents\tCtrl+1", kind=wx.ITEM_CHECK)
        self.mzTable = menu_view.Append(ID_window_ionList, "Panel: Peak list\tCtrl+2", kind=wx.ITEM_CHECK)
        self.textTable = menu_view.Append(ID_window_textList, "Panel: Text list\tCtrl+3", kind=wx.ITEM_CHECK)
        self.multipleMLTable = menu_view.Append(
            ID_window_multipleMLList, "Panel: Multiple files\tCtrl+4", kind=wx.ITEM_CHECK
        )
        menu_view.AppendSeparator()
        menu_view.Append(ID_window_all, "Panel: Restore &all")
        menu_view.AppendSeparator()
        menu_view.AppendItem(
            make_menu_item(
                parent=menu_view,
                evt_id=ID_windowMaximize,
                text="Maximize window",
                bitmap=self.icons.iconsLib["maximize_16"],
            )
        )
        menu_view.AppendItem(
            make_menu_item(
                parent=menu_view,
                evt_id=ID_windowMinimize,
                text="Minimize window",
                bitmap=self.icons.iconsLib["minimize_16"],
            )
        )
        menu_view.AppendItem(
            make_menu_item(
                parent=menu_view,
                evt_id=ID_windowFullscreen,
                text="Toggle fullscreen\tAlt+F11",
                bitmap=self.icons.iconsLib["fullscreen_16"],
            )
        )
        self.menubar.Append(menu_view, "&View")

        # WIDGETS
        menu_widgets = wx.Menu()
        menu_widgets.AppendItem(
            make_menu_item(
                parent=menu_view,
                evt_id=ID_saveAsInteractive,
                text="Open &interactive output panel...\tShift+Z",
                bitmap=self.icons.iconsLib["bokehLogo_16"],
            )
        )
        menu_widgets.AppendItem(
            make_menu_item(
                parent=menu_widgets,
                evt_id=ID_docTree_compareMS,
                text="Open spectrum comparison window...",
                bitmap=self.icons.iconsLib["compare_mass_spectra_16"],
            )
        )
        menu_widgets.AppendItem(
            make_menu_item(
                parent=menu_widgets, evt_id=ID_docTree_plugin_UVPD, text="Open UVPD processing window...", bitmap=None
            )
        )
        menu_widgets.AppendItem(
            make_menu_item(parent=menu_widgets, evt_id=ID_docTree_plugin_MSMS, text="Open MS/MS window...", bitmap=None)
        )
        menu_widget_overlay_viewer = make_menu_item(
            parent=menu_widgets, text="Open overlay window...\tShift+O", bitmap=None
        )
        menu_widgets.AppendItem(menu_widget_overlay_viewer)

        #         menu_widget_interactive_viewer = make_menu_item(
        #             parent=menuWidgets, text="Open interactive window...", bitmap=None
        #         )
        #         menuWidgets.AppendItem(menu_widget_interactive_viewer)

        # add manual activation sub-menu
        menu_widgets.AppendSeparator()
        menu_widget_ciu_import = make_menu_item(
            parent=menu_widgets, text="Open Manual CIU import manager...", bitmap=None
        )
        menu_widgets.AppendItem(menu_widget_ciu_import)
        menu_widget_sid_import = make_menu_item(
            parent=menu_widgets, text="Open Manual SID import manager...", bitmap=None
        )
        menu_widgets.AppendItem(menu_widget_sid_import)

        # add lesa activation sub-menu
        menu_widgets.AppendSeparator()
        menu_widget_lesa_import = make_menu_item(
            parent=menu_widgets, text="Open LESA import manager...\tCtrl+L", bitmap=None
        )
        menu_widgets.AppendItem(menu_widget_lesa_import)

        menu_widget_lesa_viewer = make_menu_item(
            parent=menu_widgets, text="Open LESA imaging window...\tShift+L", bitmap=None
        )
        menu_widgets.AppendItem(menu_widget_lesa_viewer)
        self.menubar.Append(menu_widgets, "&Widgets")

        # CONFIG
        menu_config = wx.Menu()
        menu_config.AppendItem(
            make_menu_item(
                parent=menu_config,
                evt_id=ID_saveConfig,
                text="Export configuration XML file (default location)\tCtrl+S",
                bitmap=self.icons.iconsLib["export_config_16"],
            )
        )
        menu_config.AppendItem(
            make_menu_item(
                parent=menu_config,
                evt_id=ID_saveAsConfig,
                text="Export configuration XML file as...\tCtrl+Shift+S",
                bitmap=None,
            )
        )
        menu_config.AppendSeparator()
        menu_config.AppendItem(
            make_menu_item(
                parent=menu_config,
                evt_id=ID_openConfig,
                text="Import configuration XML file (default location)\tCtrl+Shift+O",
                bitmap=self.icons.iconsLib["import_config_16"],
            )
        )
        menu_config.AppendItem(
            make_menu_item(
                parent=menu_config, evt_id=ID_openAsConfig, text="Import configuration XML file from...", bitmap=None
            )
        )
        menu_config.AppendSeparator()
        self.menu_config_check_load_ccs_db_btn = menu_config.Append(
            ID_importAtStart_CCS, "Load at start", kind=wx.ITEM_CHECK
        )
        self.menu_config_check_load_ccs_db_btn.Check(CONFIG.loadCCSAtStart)
        menu_config.AppendItem(
            make_menu_item(
                parent=menu_config,
                evt_id=ID_openCCScalibrationDatabse,
                text="Import CCS calibration database\tCtrl+Alt+C",
                bitmap=self.icons.iconsLib["filelist_16"],
            )
        )
        menu_config.AppendItem(
            make_menu_item(
                parent=menu_config,
                evt_id=ID_selectCalibrant,
                text="Show CCS calibrants\tCtrl+Shift+C",
                bitmap=self.icons.iconsLib["ccs_table_16"],
            )
        )
        menu_config.AppendSeparator()
        menu_config.AppendItem(
            make_menu_item(
                parent=menu_config,
                evt_id=ID_importExportSettings_peaklist,
                text="Import parameters: Peaklist",
                bitmap=None,
            )
        )
        menu_config.AppendItem(
            make_menu_item(
                parent=menu_config, evt_id=ID_importExportSettings_image, text="Export parameters: Image", bitmap=None
            )
        )
        menu_config.AppendItem(
            make_menu_item(
                parent=menu_config, evt_id=ID_importExportSettings_file, text="Export parameters: File", bitmap=None
            )
        )
        menu_config.AppendSeparator()
        self.menu_config_check_driftscope_btn = menu_config.Append(
            ID_checkAtStart_Driftscope, "Look for DriftScope at start", kind=wx.ITEM_CHECK
        )
        self.menu_config_check_driftscope_btn.Check(CONFIG.checkForDriftscopeAtStart)
        menu_config.AppendItem(
            make_menu_item(
                parent=menu_config,
                evt_id=ID_check_Driftscope,
                text="Check DriftScope path",
                bitmap=self.icons.iconsLib["check_online_16"],
            )
        )
        # menu_config.AppendItem(
        #     make_menu_item(
        #         parent=menu_config,
        #         id=ID_setDriftScopeDir,
        #         text="Set DriftScope path...",
        #         bitmap=self.icons.iconsLib["driftscope_16"],
        #     )
        # )
        self.menubar.Append(menu_config, "&Configuration")

        menu_software = wx.Menu()
        menu_software.AppendItem(
            make_menu_item(
                parent=menu_software,
                evt_id=ID_help_UniDecInfo,
                text="About UniDec engine...",
                bitmap=self.icons.iconsLib["process_unidec_16"],
            )
        )
        #         otherSoftwareMenu.Append(ID_open1DIMSFile, 'About CIDER...')

        menu_help_pages = wx.Menu()
        # helpPagesMenu.AppendItem(make_menu_item(parent=helpPagesMenu, id=ID_help_page_gettingStarted,
        #                                      text='Learn more: Getting started\tF1+0',
        #                                      bitmap=self.icons.iconsLib['blank_16']))
        # helpPagesMenu.AppendSeparator()
        menu_help_pages.AppendItem(
            make_menu_item(
                parent=menu_help_pages,
                evt_id=ID_help_page_dataLoading,
                text="Learn more: Loading data",
                bitmap=self.icons.iconsLib["open16"],
            )
        )

        menu_help_pages.AppendItem(
            make_menu_item(
                parent=menu_help_pages,
                evt_id=ID_help_page_dataExtraction,
                text="Learn more: Data extraction",
                bitmap=self.icons.iconsLib["extract16"],
            )
        )

        menu_help_pages.AppendItem(
            make_menu_item(
                parent=menu_help_pages,
                evt_id=ID_help_page_UniDec,
                text="Learn more: MS deconvolution using UniDec",
                bitmap=self.icons.iconsLib["process_unidec_16"],
            )
        )

        menu_help_pages.AppendItem(
            make_menu_item(
                parent=menu_help_pages,
                evt_id=ID_help_page_ORIGAMI,
                text="Learn more: ORIGAMI-MS (Automated CIU)",
                bitmap=self.icons.iconsLib["origamiLogoDark16"],
            )
        )

        menu_help_pages.AppendItem(
            make_menu_item(
                parent=menu_help_pages,
                evt_id=ID_help_page_multipleFiles,
                text="Learn more: Multiple files (Manual CIU)",
                bitmap=self.icons.iconsLib["panel_mll__16"],
            )
        )

        menu_help_pages.AppendItem(
            make_menu_item(
                parent=menu_help_pages,
                evt_id=ID_help_page_overlay,
                text="Learn more: Overlay documents",
                bitmap=self.icons.iconsLib["overlay16"],
            )
        )

        #         helpPagesMenu.AppendItem(make_menu_item(parent=helpPagesMenu, id=ID_help_page_linearDT,
        #                                               text='Learn more: Linear Drift-time analysis',
        #                                               bitmap=self.icons.iconsLib['panel_dt_16']))
        #
        #         helpPagesMenu.AppendItem(make_menu_item(parent=helpPagesMenu, id=ID_help_page_CCScalibration,
        #                                               text='Learn more: CCS calibration',
        #                                               bitmap=self.icons.iconsLib['panel_ccs_16']))

        menu_help_pages.AppendItem(
            make_menu_item(
                parent=menu_help_pages,
                evt_id=ID_help_page_Interactive,
                text="Learn more: Interactive output",
                bitmap=self.icons.iconsLib["bokehLogo_16"],
            )
        )

        menu_help_pages.AppendItem(
            make_menu_item(
                parent=menu_help_pages,
                evt_id=ID_help_page_annotatingMassSpectra,
                text="Learn more: Annotating mass spectra",
                bitmap=self.icons.iconsLib["annotate16"],
            )
        )

        menu_help_pages.AppendItem(
            make_menu_item(
                parent=menu_help_pages,
                evt_id=ID_help_page_OtherData,
                text="Learn more: Annotated data",
                bitmap=self.icons.iconsLib["blank_16"],
            )
        )

        # HELP MENU
        menu_help = wx.Menu()
        menu_help.AppendMenu(wx.ID_ANY, "Help pages...", menu_help_pages)
        menu_help.AppendSeparator()
        menu_help.AppendItem(
            make_menu_item(
                parent=menu_help,
                evt_id=ID_helpGuide,
                text="Open User Guide...",
                bitmap=self.icons.iconsLib["web_access_16"],
            )
        )
        menu_help.AppendItem(
            make_menu_item(
                parent=menu_help,
                evt_id=ID_helpYoutube,
                text="Check out video guides... (online)",
                bitmap=self.icons.iconsLib["youtube16"],
                help_text=self.help.link_youtube,
            )
        )
        menu_help.AppendItem(
            make_menu_item(
                parent=menu_help,
                evt_id=ID_helpNewVersion,
                text="Check for updates... (online)",
                bitmap=self.icons.iconsLib["github16"],
            )
        )
        menu_help.AppendItem(
            make_menu_item(
                parent=menu_help,
                evt_id=ID_helpCite,
                text="Paper to cite... (online)",
                bitmap=self.icons.iconsLib["cite_16"],
            )
        )
        menu_help.AppendSeparator()
        menu_help.AppendMenu(wx.ID_ANY, "About other software...", menu_software)
        menu_help.AppendSeparator()
        menu_help.AppendItem(
            make_menu_item(
                parent=menu_help,
                evt_id=ID_helpNewFeatures,
                text="Request new features... (web)",
                bitmap=self.icons.iconsLib["request_16"],
            )
        )
        menu_help.AppendItem(
            make_menu_item(
                parent=menu_help,
                evt_id=ID_helpReportBugs,
                text="Report bugs... (web)",
                bitmap=self.icons.iconsLib["bug_16"],
            )
        )
        menu_help.AppendSeparator()
        menu_help.AppendItem(
            make_menu_item(
                parent=menu_help,
                evt_id=ID_CHECK_VERSION,
                text="Check for newest version...",
                bitmap=self.icons.iconsLib["check_online_16"],
            )
        )
        menu_help.AppendItem(
            make_menu_item(
                parent=menu_help,
                evt_id=ID_WHATS_NEW,
                text="Whats new in v{}".format(CONFIG.version),
                bitmap=self.icons.iconsLib["blank_16"],
            )
        )
        menu_help.AppendSeparator()
        menu_help.AppendItem(
            make_menu_item(
                parent=menu_help,
                evt_id=ID_SHOW_ABOUT,
                text="About ORIGAMI\tCtrl+Shift+A",
                bitmap=self.icons.iconsLib["origamiLogoDark16"],
            )
        )
        self.menubar.Append(menu_help, "&Help")
        self.SetMenuBar(self.menubar)

        # DEBUG MODE
        if CONFIG.debug:
            menu_dev = wx.Menu()
            # append inspector
            menu_dev_wxpython = make_menu_item(parent=menu_dev, text="Open wxPython inspector")
            menu_dev.AppendItem(menu_dev_wxpython)
            self.Bind(wx.EVT_MENU, self._dev_open_wxpython_inspector, menu_dev_wxpython)

            # append closable widget
            menu_dev_widget = make_menu_item(parent=menu_dev, text="Add closable widget")
            menu_dev.AppendItem(menu_dev_widget)
            self.Bind(wx.EVT_MENU, self._dev_add_widget, menu_dev_widget)

            self.menubar.Append(menu_dev, "&Development")

        self.SetMenuBar(self.menubar)

        # Bind functions to menu
        # HELP MENU
        self.Bind(wx.EVT_MENU, self.on_open_about_panel, id=ID_SHOW_ABOUT)
        self.Bind(wx.EVT_MENU, self.on_check_ORIGAMI_version, id=ID_CHECK_VERSION)
        self.Bind(wx.EVT_MENU, self.on_whats_new, id=ID_WHATS_NEW)
        self.Bind(wx.EVT_MENU, self.on_open_link, id=ID_helpGuide)
        self.Bind(wx.EVT_MENU, self.onOpenUserGuide, id=ID_helpGuideLocal)
        self.Bind(wx.EVT_MENU, self.on_open_link, id=ID_helpCite)
        self.Bind(wx.EVT_MENU, self.on_open_link, id=ID_helpYoutube)
        self.Bind(wx.EVT_MENU, self.on_open_link, id=ID_helpNewVersion)
        self.Bind(wx.EVT_MENU, self.on_open_link, id=ID_helpReportBugs)
        self.Bind(wx.EVT_MENU, self.on_open_link, id=ID_helpNewFeatures)
        self.Bind(wx.EVT_MENU, self.on_open_link, id=ID_helpAuthor)
        self.Bind(wx.EVT_MENU, self.presenter.on_reboot_origami, id=ID_RESET_ORIGAMI)

        self.Bind(wx.EVT_MENU, self.on_open_HTML_guide, id=ID_help_UniDecInfo)
        self.Bind(wx.EVT_MENU, self.on_open_HTML_guide, id=ID_help_page_gettingStarted)
        self.Bind(wx.EVT_MENU, self.on_open_HTML_guide, id=ID_help_page_dataLoading)
        self.Bind(wx.EVT_MENU, self.on_open_HTML_guide, id=ID_help_page_UniDec)
        self.Bind(wx.EVT_MENU, self.on_open_HTML_guide, id=ID_help_page_ORIGAMI)
        self.Bind(wx.EVT_MENU, self.on_open_HTML_guide, id=ID_help_page_overlay)
        self.Bind(wx.EVT_MENU, self.on_open_HTML_guide, id=ID_help_page_multipleFiles)
        self.Bind(wx.EVT_MENU, self.on_open_HTML_guide, id=ID_help_page_linearDT)
        self.Bind(wx.EVT_MENU, self.on_open_HTML_guide, id=ID_help_page_CCScalibration)
        self.Bind(wx.EVT_MENU, self.on_open_HTML_guide, id=ID_help_page_dataExtraction)
        self.Bind(wx.EVT_MENU, self.on_open_HTML_guide, id=ID_help_page_Interactive)
        self.Bind(wx.EVT_MENU, self.on_open_HTML_guide, id=ID_help_page_OtherData)
        self.Bind(wx.EVT_MENU, self.on_open_HTML_guide, id=ID_help_page_annotatingMassSpectra)

        # FILE MENU
        self.Bind(wx.EVT_MENU, self.data_handling.on_open_multiple_text_2d_fcn, menu_file_text_heatmap)

        #         self.Bind(wx.EVT_MENU, self.data_handling.on_open_MassLynx_raw_fcn, id=ID_openIRRawFile)
        self.Bind(
            wx.EVT_MENU, self.data_handling.on_open_multiple_MassLynx_raw_fcn, id=ID_load_multiple_origami_masslynx_raw
        )

        #         self.Bind(wx.EVT_MENU, self.data_handling.on_open_document_fcn, id=ID_openDocument)
        self.Bind(wx.EVT_MENU, self.panelDocuments.documents.on_save_document, id=ID_saveDocument)
        #         self.Bind(wx.EVT_MENU, self.data_handling.on_save_all_documents_fcn, id=ID_saveAllDocuments)
        self.Bind(wx.EVT_MENU, self.data_handling.on_open_multiple_text_ms_fcn, menu_file_text_ms)
        self.Bind(wx.EVT_MENU, self.data_handling.on_open_single_clipboard_ms, menu_file_clipboard_ms)
        # , id=ID_load_clipboard_spectrum)
        self.Bind(wx.EVT_MENU, self.on_close, id=ID_quit)
        self.Bind(wx.EVT_MENU, self.on_add_blank_document_interactive, id=ID_addNewInteractiveDoc)
        self.Bind(wx.EVT_MENU, self.on_add_blank_document_manual, id=ID_addNewManualDoc)
        self.Bind(wx.EVT_MENU, self.on_add_blank_document_overlay, id=ID_addNewOverlayDoc)
        self.Bind(wx.EVT_TOOL, self.on_open_multiple_files, id=ID_load_multiple_masslynx_raw)

        self.Bind(wx.EVT_TOOL, self.data_handling.on_open_mgf_file_fcn, id=ID_fileMenu_MGF)
        self.Bind(wx.EVT_TOOL, self.data_handling.on_open_mzml_file_fcn, id=ID_fileMenu_mzML)
        self.Bind(wx.EVT_TOOL, self.data_handling.on_open_thermo_file_fcn, id=ID_fileMenu_thermoRAW)

        self.Bind(wx.EVT_MENU, self.data_handling.on_open_waters_raw_ms_fcn, id=ID_load_masslynx_raw_ms_only)
        self.Bind(wx.EVT_MENU, self.data_handling.on_open_waters_raw_imms_fcn, menu_file_waters_imms)
        self.Bind(wx.EVT_MENU, self.data_handling.on_open_waters_raw_imms_fcn, id=ID_load_origami_masslynx_raw)
        #         self.Bind(wx.EVT_MENU, self.data_handling.on_open_MassLynx_raw_fcn, id=ID_load_origami_masslynx_raw)

        # PLOT
        self.Bind(wx.EVT_MENU, self.on_open_plot_settings_panel, id=ID_extraSettings_general_plot)
        self.Bind(wx.EVT_MENU, self.on_open_plot_settings_panel, id=ID_extraSettings_plot1D)
        self.Bind(wx.EVT_MENU, self.on_open_plot_settings_panel, id=ID_extraSettings_plot2D)
        self.Bind(wx.EVT_MENU, self.on_open_plot_settings_panel, id=ID_extraSettings_plot3D)
        self.Bind(wx.EVT_MENU, self.on_open_plot_settings_panel, id=ID_extraSettings_legend)
        self.Bind(wx.EVT_MENU, self.on_open_plot_settings_panel, id=ID_extraSettings_colorbar)
        self.Bind(wx.EVT_MENU, self.on_open_plot_settings_panel, id=ID_extraSettings_rmsd)
        self.Bind(wx.EVT_MENU, self.on_open_plot_settings_panel, id=ID_extraSettings_waterfall)
        self.Bind(wx.EVT_MENU, self.on_open_plot_settings_panel, id=ID_extraSettings_violin)
        self.Bind(wx.EVT_MENU, self.on_open_plot_settings_panel, id=ID_extraSettings_general)
        self.Bind(wx.EVT_MENU, self.on_update_interaction_settings, id=ID_plots_showCursorGrid)

        self.Bind(wx.EVT_MENU, self.on_customise_annotation_plot_parameters, id=ID_annotPanel_otherSettings)
        self.Bind(wx.EVT_MENU, self.on_customise_unidec_plot_parameters, id=ID_unidecPanel_otherSettings)

        # OUTPUT
        self.Bind(wx.EVT_MENU, self.panelPlots.save_images, id=ID_saveOverlayImage)
        self.Bind(wx.EVT_MENU, self.panelPlots.save_images, id=ID_saveMSImage)
        self.Bind(wx.EVT_MENU, self.panelPlots.save_images, id=ID_saveMZDTImage)
        self.Bind(wx.EVT_MENU, self.panelPlots.save_images, id=ID_saveRTImage)
        self.Bind(wx.EVT_MENU, self.panelPlots.save_images, id=ID_save1DImage)
        self.Bind(wx.EVT_MENU, self.panelPlots.save_images, id=ID_save2DImage)
        self.Bind(wx.EVT_MENU, self.panelPlots.save_images, id=ID_save3DImage)
        self.Bind(wx.EVT_MENU, self.panelPlots.save_images, id=ID_saveWaterfallImage)
        self.Bind(wx.EVT_MENU, self.panelPlots.save_images, id=ID_saveRMSDImage)
        self.Bind(wx.EVT_MENU, self.panelPlots.save_images, id=ID_saveRMSFImage)
        self.Bind(wx.EVT_MENU, self.panelPlots.save_images, id=ID_saveRMSDmatrixImage)
        self.Bind(wx.EVT_MENU, self.on_open_interactive_output_panel, id=ID_saveAsInteractive)

        # UTILITIES
        #         self.Bind(wx.EVT_MENU, self.panelDocuments.documents.on_process_UVPD, id=ID_docTree_plugin_UVPD)
        #         self.Bind(wx.EVT_MENU, self.panelDocuments.documents.on_open_MSMS_viewer, id=ID_docTree_plugin_MSMS)
        #         self.Bind(wx.EVT_MENU, self.panelDocuments.documents.on_open_overlay_viewer,
        #         menu_widget_overlay_viewer)
        #         self.Bind(wx.EVT_MENU, self.panelDocuments.documents.on_open_lesa_viewer, menu_widget_lesa_viewer)
        self.Bind(wx.EVT_MENU, self.panelDocuments.documents.on_import_lesa_dataset, menu_widget_lesa_import)
        #         self.Bind(wx.EVT_MENU, self.panelDocuments.documents.on_open_interactive_viewer,
        # menu_widget_interactive_viewer)

        self.Bind(
            wx.EVT_MENU, partial(self.panelDocuments.documents.on_import_manual_dataset, "SID"), menu_widget_sid_import
        )
        self.Bind(
            wx.EVT_MENU, partial(self.panelDocuments.documents.on_import_manual_dataset, "CIU"), menu_widget_ciu_import
        )

        # CONFIG MENU
        self.Bind(wx.EVT_MENU, self.data_handling.on_export_config_fcn, id=ID_saveConfig)
        self.Bind(wx.EVT_MENU, self.data_handling.on_export_config_as_fcn, id=ID_saveAsConfig)
        self.Bind(wx.EVT_MENU, self.data_handling.on_import_config_fcn, id=ID_openConfig)
        self.Bind(wx.EVT_MENU, self.data_handling.on_import_config_as_fcn, id=ID_openAsConfig)
        # self.Bind(wx.EVT_MENU, self.on_setup_driftscope, id=ID_setDriftScopeDir)
        self.Bind(wx.EVT_MENU, self.on_check_driftscope_path, id=ID_check_Driftscope)
        self.Bind(wx.EVT_MENU, self.on_open_export_settings_panel, id=ID_importExportSettings_peaklist)
        self.Bind(wx.EVT_MENU, self.on_open_export_settings_panel, id=ID_importExportSettings_image)
        self.Bind(wx.EVT_MENU, self.on_open_export_settings_panel, id=ID_importExportSettings_file)
        self.Bind(wx.EVT_MENU, self.on_check_in_menu, id=ID_checkAtStart_Driftscope)
        self.Bind(wx.EVT_MENU, self.on_check_in_menu, id=ID_importAtStart_CCS)

        # VIEW MENU
        self.Bind(wx.EVT_MENU, self.on_toggle_panel, id=ID_window_all)
        self.Bind(wx.EVT_MENU, self.on_toggle_panel, self.documentsPage)
        self.Bind(wx.EVT_MENU, self.on_toggle_panel, self.mzTable)
        self.Bind(wx.EVT_MENU, self.on_toggle_panel, self.textTable)
        self.Bind(wx.EVT_MENU, self.on_toggle_panel, self.multipleMLTable)
        self.Bind(wx.EVT_MENU, self.on_set_window_maximize, id=ID_windowMaximize)
        self.Bind(wx.EVT_MENU, self.on_set_window_iconize, id=ID_windowMinimize)
        self.Bind(wx.EVT_MENU, self.on_set_window_fullscreen, id=ID_windowFullscreen)
        self.Bind(wx.EVT_MENU, self.panelPlots.on_clear_all_plots, id=ID_clearAllPlots)
        self.Bind(
            wx.EVT_MENU, self.panelDocuments.documents.on_open_spectrum_comparison_viewer, id=ID_docTree_compareMS
        )
        self.SetMenuBar(self.menubar)

    def _dev_open_wxpython_inspector(self, evt):
        """Opens wxpython inspector"""
        import wx.lib.inspection

        wx.lib.inspection.InspectionTool().Show()
        logger.debug("Opened inspection tool")

    def _dev_add_widget(self, evt):
        """Opens closable widget - use to ensure that widgets can be dynamically added/removed from the UI"""
        item = np.random.choice(["ion", "files"], 1, False)[0]
        panel_name = self.create_panel(item, f"TEST_DOC_#{np.random.randint(0, 100, 1)[0]}")
        logger.debug(f"Created random panel - {panel_name}")

    def on_customise_annotation_plot_parameters(self, evt):
        from origami.gui_elements.dialog_customise_user_annotations import DialogCustomiseUserAnnotations

        dlg = DialogCustomiseUserAnnotations(self, config=CONFIG)
        dlg.ShowModal()

    def on_customise_unidec_plot_parameters(self, evt):
        from origami.widgets.UniDec.dialog_customise_unidec_visuals import DialogCustomiseUniDecVisuals

        dlg = DialogCustomiseUniDecVisuals(self, CONFIG, self.icons)
        dlg.ShowModal()

    def on_add_blank_document_manual(self, evt):
        self.presenter.onAddBlankDocument(evt=None, document_type="manual")

    def on_add_blank_document_interactive(self, evt):
        self.presenter.onAddBlankDocument(evt=None, document_type="interactive")

    def on_add_blank_document_overlay(self, evt):
        self.presenter.onAddBlankDocument(evt=None, document_type="overlay")

    def on_open_multiple_files(self, evt):
        self.data_handling.on_open_multiple_ML_files_fcn(open_type="multiple_files_new_document")

    def on_open_thermo_file(self, evt):
        self.panelDocuments.documents.on_open_thermo_file_fcn(None)

    def on_open_link(self, evt):
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
            ID_helpAuthor: "about-author",
        }

        link = CONFIG.links[links[evtID]]

        # open webpage
        try:
            self.presenter.onThreading(
                None, ("Opening a link in your default internet browser", 4), action="updateStatusbar"
            )
            webbrowser.open(link, autoraise=1)
        except Exception:
            pass

    def on_check_ORIGAMI_version(self, evt=None):
        """
        Simple function to check whether this is the newest version available
        """
        try:
            newVersion = get_latest_version(link=CONFIG.links["newVersion"])
            update = compare_versions(newVersion, CONFIG.version)
            if not update:
                try:
                    if evt.GetId() == ID_CHECK_VERSION:
                        DialogBox(
                            title="ORIGAMI",
                            msg="You are using the most up to date version {}.".format(CONFIG.version),
                            kind="Info",
                        )
                except Exception:
                    pass
            else:
                webpage = get_latest_version(get_webpage=True)
                wx.Bell()
                message = "Version {} is now available for download.\nYou are currently using version {}.".format(
                    newVersion, CONFIG.version
                )
                self.presenter.onThreading(None, (message, 4), action="updateStatusbar")
                msgDialog = DialogNewVersion(self, presenter=self.presenter, webpage=webpage)
                msgDialog.ShowModal()
        except Exception as e:
            self.presenter.onThreading(None, ("Could not check version number", 4), action="updateStatusbar")
            logger.error(e)

    def on_whats_new(self, evt):
        try:
            webpage = get_latest_version(get_webpage=True)
            msgDialog = DialogNewVersion(self, presenter=self.presenter, webpage=webpage)
            msgDialog.ShowModal()
        except Exception:
            pass

    def onOpenUserGuide(self, evt):
        """Opens link in browser"""
        try:
            logger.info("Opening documentation in your browser")
            webbrowser.open(CONFIG.links["guide"], autoraise=True)
        except Exception:
            pass

    def on_open_HTML_guide(self, evt):
        from origami.gui_elements.panel_html_viewer import PanelHTMLViewer
        from origami.help_documentation import HTMLHelp as htmlPages

        htmlPages = htmlPages()
        evtID = evt.GetId()
        link, kwargs = None, {}
        if evtID == ID_help_UniDecInfo:
            kwargs = htmlPages.page_UniDec_info

        elif evtID == ID_help_page_dataLoading:
            link = r"https://origami.lukasz-migas.com/user-guide/loading-data"

        elif evtID == ID_help_page_gettingStarted:
            link = r"https://origami.lukasz-migas.com/user-guide/example-files"

        elif evtID == ID_help_page_UniDec:
            link = r"https://origami.lukasz-migas.com/user-guide/deconvolution/unidec-deconvolution"

        elif evtID == ID_help_page_ORIGAMI:
            link = r"https://origami.lukasz-migas.com/user-guide/data-handling/automated-ciu"

        elif evtID == ID_help_page_overlay:
            kwargs = htmlPages.page_overlay_info

        elif evtID == ID_help_page_multipleFiles:
            link = r"https://origami.lukasz-migas.com/user-guide/data-handling/manual-ciu"

        elif evtID == ID_help_page_linearDT:
            kwargs = htmlPages.page_linear_dt_info

        elif evtID == ID_help_page_CCScalibration:
            kwargs = htmlPages.page_ccs_calibration_info

        elif evtID == ID_help_page_dataExtraction:
            link = r"https://origami.lukasz-migas.com/user-guide/data-handling/ms-and-imms-files"

        elif evtID == ID_help_page_Interactive:
            link = r"https://origami.lukasz-migas.com/user-guide/interactive-output/simple-output"

        elif evtID == ID_help_page_OtherData:
            kwargs = htmlPages.page_other_data_info

        elif evtID == ID_help_page_annotatingMassSpectra:
            link = r"https://origami.lukasz-migas.com/user-guide/processing/mass-spectra-annotation"

        if link is None:
            htmlViewer = PanelHTMLViewer(self, CONFIG, **kwargs)
            htmlViewer.Show()
        else:
            try:
                self.presenter.onThreading(
                    None, ("Opening local documentation in your browser...", 4), action="updateStatusbar"
                )
                webbrowser.open(link, autoraise=True)
            except Exception:
                pass

    def on_check_in_menu(self, evt):
        """Update the check buttons in the menu upon registration of an event"""

        # get event id
        evt_id = evt.GetId()

        if evt_id == ID_checkAtStart_Driftscope:
            check_value = not CONFIG.checkForDriftscopeAtStart
            CONFIG.checkForDriftscopeAtStart = check_value
            self.menu_config_check_driftscope_btn.Check(check_value)
        elif evt_id == ID_importAtStart_CCS:
            check_value = not CONFIG.loadCCSAtStart
            CONFIG.loadCCSAtStart = check_value
            self.menu_config_check_load_ccs_db_btn.Check(check_value)

    def on_set_window_maximize(self, evt):
        """Maximize app."""
        self.Maximize()

    def on_set_window_iconize(self, evt):
        """Iconize app."""
        self.Iconize()

    def on_set_window_fullscreen(self, evt):
        """Fullscreen app."""
        self._fullscreen = not self._fullscreen
        self.ShowFullScreen(
            self._fullscreen, style=wx.FULLSCREEN_ALL & ~(wx.FULLSCREEN_NOMENUBAR | wx.FULLSCREEN_NOSTATUSBAR)
        )

    def make_shortcuts(self):
        """
        Setup shortcuts for the GUI application
        """
        # Setup shortcuts. Format: 'KEY', 'FUNCTION', 'MODIFIER'
        accelerator_events = [
            #             ["I", self.panelDocuments.documents.onOpenDocInfo, wx.ACCEL_CTRL],
            ["W", self.data_handling.on_open_multiple_text_2d_fcn, wx.ACCEL_CTRL],
            ["Z", self.on_open_interactive_output_panel, wx.ACCEL_SHIFT],
            ["G", self.data_handling.on_open_directory, wx.ACCEL_CTRL],
        ]
        key_ids_list = [wx.NewId() for _ in accelerator_events]
        control_list = []
        for idx, key_binding in enumerate(accelerator_events):
            self.Bind(wx.EVT_MENU, key_binding[1], id=key_ids_list[idx])
            control_list.append((key_binding[2], ord(key_binding[0]), key_ids_list[idx]))

        # Add more shortcuts with known IDs
        extra_key_events = [
            # ["Q", self.presenter.on_overlay_2D, wx.ACCEL_ALT, ID_overlayMZfromList],
            # ["W", self.presenter.on_overlay_2D, wx.ACCEL_ALT, ID_overlayTextFromList],
            ["S", self.panelDocuments.documents.on_show_plot, wx.ACCEL_ALT, ID_showPlotDocument],
            ["R", self.panelDocuments.documents.onRenameItem, wx.ACCEL_ALT, ID_renameItem],
            ["X", self.panelDocuments.documents.on_show_plot, wx.ACCEL_ALT, ID_showPlotMSDocument],
            ["Z", self.panelDocuments.documents.on_change_charge_state, wx.ACCEL_ALT, ID_assignChargeState],
            ["V", self.panelDocuments.documents.on_save_csv, wx.ACCEL_ALT, ID_saveDataCSVDocument],
        ]

        for item in extra_key_events:
            self.Bind(wx.EVT_MENU, item[1], id=item[3])
            control_list.append((item[2], ord(item[0]), item[3]))

        self.SetAcceleratorTable(wx.AcceleratorTable(control_list))

    def on_open_source_menu(self, evt):
        menu = wx.Menu()
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                evt_id=ID_fileMenu_MGF,
                text="Open Mascot Generic Format file (.mgf) [MS/MS]",
                bitmap=self.icons.iconsLib["blank_16"],
            )
        )
        menu.AppendItem(
            make_menu_item(
                parent=menu,
                evt_id=ID_fileMenu_mzML,
                text="Open mzML (.mzML) [MS/MS]",
                bitmap=self.icons.iconsLib["blank_16"],
            )
        )
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def make_toolbar(self):

        # Bind events
        self.Bind(wx.EVT_TOOL, self.on_open_source_menu, id=ID_mainPanel_openSourceFiles)

        # Create toolbar
        self.toolbar = self.CreateToolBar(wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT)
        self.toolbar.SetToolBitmapSize((12, 12))

        self.toolbar.AddLabelTool(
            ID_openDocument, "", self.icons.iconsLib["open_project_16"], shortHelp="Open project document..."
        )
        self.toolbar.AddLabelTool(
            ID_saveDocument, "", self.icons.iconsLib["save16"], shortHelp="Save project document..."
        )
        self.toolbar.AddSeparator()
        self.toolbar.AddLabelTool(
            ID_saveConfig, "", self.icons.iconsLib["export_config_16"], shortHelp="Export configuration file"
        )
        self.toolbar.AddSeparator()
        self.toolbar.AddLabelTool(
            ID_load_origami_masslynx_raw,
            "",
            self.icons.iconsLib["open_origami_16"],
            shortHelp="Open MassLynx file (.raw)",
        )
        #         self.toolbar.AddLabelTool(
        #             ID_load_origami_masslynx_raw,
        #             "",
        #             self.icons.iconsLib["open_masslynx_16"],
        #             shortHelp="Open MassLynx file (IM-MS)",
        #         )
        self.toolbar.AddLabelTool(
            ID_load_multiple_masslynx_raw,
            "",
            self.icons.iconsLib["open_masslynxMany_16"],
            shortHelp="Open multiple MassLynx files (e.g. CIU/SID)",
        )
        self.toolbar.AddSeparator()
        self.toolbar.AddLabelTool(
            ID_load_multiple_text_2D,
            "",
            self.icons.iconsLib["open_textMany_16"],
            shortHelp="Open one (or more) heatmap text file",
        )
        self.toolbar.AddSeparator()
        self.toolbar.AddLabelTool(
            ID_mainPanel_openSourceFiles, "", self.icons.iconsLib["ms16"], shortHelp="Open MS/MS files..."
        )
        self.toolbar.AddSeparator()
        self.toolbar.AddCheckTool(
            ID_window_documentList, "", self.icons.iconsLib["panel_doc_16"], shortHelp="Enable/Disable documents panel"
        )
        self.toolbar.AddCheckTool(
            ID_window_ionList, "", self.icons.iconsLib["panel_ion_16"], shortHelp="Enable/Disable peak list panel"
        )
        self.toolbar.AddCheckTool(
            ID_window_textList, "", self.icons.iconsLib["panel_text_16"], shortHelp="Enable/Disable text list panel"
        )
        self.toolbar.AddCheckTool(
            ID_window_multipleMLList, "", self.icons.iconsLib["panel_mll__16"], shortHelp="Enable/Disable files panel"
        )
        self.toolbar.AddSeparator()
        self.toolbar.AddLabelTool(
            ID_extraSettings_general_plot,
            "",
            self.icons.iconsLib["panel_plot_general_16"],
            shortHelp="Settings: General plot",
        )
        self.toolbar.AddLabelTool(
            ID_extraSettings_plot1D, "", self.icons.iconsLib["panel_plot1D_16"], shortHelp="Settings: Plot 1D panel"
        )
        self.toolbar.AddLabelTool(
            ID_extraSettings_plot2D, "", self.icons.iconsLib["panel_plot2D_16"], shortHelp="Settings: Plot 2D panel"
        )
        self.toolbar.AddLabelTool(
            ID_extraSettings_plot3D, "", self.icons.iconsLib["panel_plot3D_16"], shortHelp="Settings: Plot 3D panel"
        )
        self.toolbar.AddLabelTool(
            ID_extraSettings_colorbar,
            "",
            self.icons.iconsLib["panel_colorbar_16"],
            shortHelp="Settings: Colorbar panel",
        )
        self.toolbar.AddLabelTool(
            ID_extraSettings_legend, "", self.icons.iconsLib["panel_legend_16"], shortHelp="Settings: Legend panel"
        )
        self.toolbar.AddLabelTool(
            ID_extraSettings_rmsd, "", self.icons.iconsLib["panel_rmsd_16"], shortHelp="Settings: RMSD panel"
        )
        self.toolbar.AddLabelTool(
            ID_extraSettings_waterfall,
            "",
            self.icons.iconsLib["panel_waterfall_16"],
            shortHelp="Settings: Waterfall panel",
        )
        self.toolbar.AddLabelTool(
            ID_extraSettings_violin, "", self.icons.iconsLib["panel_violin_16"], shortHelp="Settings: Violin panel"
        )
        self.toolbar.AddLabelTool(
            ID_extraSettings_general, "", self.icons.iconsLib["panel_general2_16"], shortHelp="Settings: Extra panel"
        )
        self.toolbar.AddSeparator()
        self.toolbar.AddLabelTool(
            ID_saveAsInteractive, "", self.icons.iconsLib["bokehLogo_16"], shortHelp="Open interactive output panel"
        )

        # Actually realise the toolbar
        self.toolbar.Realize()

    def on_toggle_panel(self, evt, check=None):

        evtID = None
        if isinstance(evt, int):
            evtID = evt
        elif isinstance(evt, str):
            if evt == "document":
                evtID = ID_window_documentList
            # elif evt == "ion":
            #     evtID = ID_window_ionList
            # elif evt == "text":
            #     evtID = ID_window_textList
            # elif evt == "mass_spectra":
            #     evtID = ID_window_multipleMLList
        elif evt is not None:
            evtID = evt.GetId()

        if evtID is not None:
            if evtID == ID_window_documentList:
                if not self.panelDocuments.IsShown() or not self.documentsPage.IsChecked():
                    self.window_mgr.GetPane(self.panelDocuments).Show()
                    CONFIG._windowSettings["Documents"]["show"] = True
                else:
                    self.window_mgr.GetPane(self.panelDocuments).Hide()
                    CONFIG._windowSettings["Documents"]["show"] = False
                self.documentsPage.Check(CONFIG._windowSettings["Documents"]["show"])
                self.on_find_toggle_by_id(find_id=evtID, check=CONFIG._windowSettings["Documents"]["show"])
            # elif evtID == ID_window_ionList:
            #     if not self.panelMultipleIons.IsShown() or check or not self.mzTable.IsChecked():
            #         self.window_mgr.GetPane(self.panelMultipleIons).Show()
            #         CONFIG._windowSettings["Peak list"]["show"] = True
            #     else:
            #         self.window_mgr.GetPane(self.panelMultipleIons).Hide()
            #         CONFIG._windowSettings["Peak list"]["show"] = False
            #     self.mzTable.Check(CONFIG._windowSettings["Peak list"]["show"])
            #     self.on_find_toggle_by_id(find_id=evtID, check=CONFIG._windowSettings["Peak list"]["show"])
            # elif evtID == ID_window_multipleMLList:
            #     if not self.panelMML.IsShown() or check or not self.multipleMLTable.IsChecked():
            #         self.window_mgr.GetPane(self.panelMML).Show()
            #         CONFIG._windowSettings["Multiple files"]["show"] = True
            #     else:
            #         self.window_mgr.GetPane(self.panelMML).Hide()
            #         CONFIG._windowSettings["Multiple files"]["show"] = False
            #     self.multipleMLTable.Check(CONFIG._windowSettings["Multiple files"]["show"])
            #     self.on_find_toggle_by_id(find_id=evtID, check=CONFIG._windowSettings["Multiple files"]["show"])
            # elif evtID == ID_window_textList:
            #     if not self.panelMultipleText.IsShown() or check or not self.textTable.IsChecked():
            #         self.window_mgr.GetPane(self.panelMultipleText).Show()
            #         CONFIG._windowSettings["Text files"]["show"] = True
            #     else:
            #         self.window_mgr.GetPane(self.panelMultipleText).Hide()
            #         CONFIG._windowSettings["Text files"]["show"] = False
            #     self.textTable.Check(CONFIG._windowSettings["Text files"]["show"])
            #     self.on_find_toggle_by_id(find_id=evtID, check=CONFIG._windowSettings["Text files"]["show"])
            elif evtID == ID_window_all:
                for key in CONFIG._windowSettings:
                    CONFIG._windowSettings[key]["show"] = True

                self.on_find_toggle_by_id(check_all=True)

                for panel in [self.panelDocuments]:  # , self.panelMML, self.panelMultipleIons, self.panelMultipleText]:
                    self.window_mgr.GetPane(panel).Show()

                self.documentsPage.Check(CONFIG._windowSettings["Documents"]["show"])
                # self.mzTable.Check(CONFIG._windowSettings["Peak list"]["show"])
                # self.textTable.Check(CONFIG._windowSettings["Text files"]["show"])
                # self.multipleMLTable.Check(CONFIG._windowSettings["Multiple files"]["show"])

        # Checking at start of program
        else:
            if not self.panelDocuments.IsShown():
                CONFIG._windowSettings["Documents"]["show"] = False
            # if not self.panelMML.IsShown():
            #     CONFIG._windowSettings["Multiple files"]["show"] = False
            # if not self.panelMultipleIons.IsShown():
            #     CONFIG._windowSettings["Peak list"]["show"] = False
            # if not self.panelMultipleText.IsShown():
            #     CONFIG._windowSettings["Text files"]["show"] = False

            self.documentsPage.Check(CONFIG._windowSettings["Documents"]["show"])
            # self.mzTable.Check(CONFIG._windowSettings["Peak list"]["show"])
            # self.textTable.Check(CONFIG._windowSettings["Text files"]["show"])
            # self.multipleMLTable.Check(CONFIG._windowSettings["Multiple files"]["show"])

        self.window_mgr.Update()

    def on_find_toggle_by_id(self, find_id=None, check=None, check_all=False):
        """Find toggle item by id in either horizontal/vertical toolbar"""
        id_list = [
            ID_window_documentList,
            ID_window_controls,
            ID_window_ionList,
            ID_window_multipleMLList,
            ID_window_textList,
        ]
        for itemID in id_list:
            if check_all:
                self.toolbar.ToggleTool(toolId=itemID, toggle=True)
            elif itemID == find_id:
                self.toolbar.ToggleTool(toolId=find_id, toggle=check)
        if find_id == ID_window_all:
            self.toolbar.ToggleTool(toolId=id, toggle=True)

    def onCheckToggleID(self, panel):
        panel_dict = {
            "Documents": ID_window_documentList,
            "Controls": ID_window_controls,
            "Multiple files": ID_window_multipleMLList,
            "Peak list": ID_window_ionList,
            "Text files": ID_window_textList,
        }
        return panel_dict[panel]

    def on_close(self, evt, **kwargs):

        n_documents = len(ENV)
        if n_documents > 0 and not kwargs.get("ignore_warning", False):
            verb_form = {"1": "is"}.get(str(n_documents), "are")
            message = (
                "There {} {} document(s) open.\n".format(verb_form, len(ENV)) + "Are you sure you want to continue?"
            )
            msgDialog = DialogNotifyOpenDocuments(self, presenter=self.presenter, message=message)
            dlg = msgDialog.ShowModal()

            if dlg == wx.ID_NO:
                print("Cancelled operation")
                return

        # Try saving configuration file
        try:
            path = os.path.join(CONFIG.cwd, "configOut.xml")
            CONFIG.saveConfigXML(path=path, evt=None)
        except Exception:
            print("Could not save configuration file")

        # Clear-up dictionary
        try:
            ENV.clear()
        except Exception as err:
            print(err)

        # try to unsubscribe from events
        try:
            self.disable_publisher()
        except Exception as err:
            print(f"Could not disable publisher: {err}")

        # Try killing window manager
        try:
            self.window_mgr.UnInit()
        except Exception as err:
            print(f"Could not uninitilize window manager: {err}")

        # Clear-up temporary data directory
        try:
            if CONFIG.temporary_data is not None:
                clean_directory(CONFIG.temporary_data)
                print("Cleared {} from temporary files.".format(CONFIG.temporary_data))
        except Exception as err:
            print(err)

        # Aggressive way to kill the ORIGAMI process (grrr)
        if not kwargs.get("clean_exit", False):
            try:
                p = psutil.Process(CONFIG._processID)
                p.terminate()
            except Exception as err:
                print(err)

        self.Destroy()

    @staticmethod
    def disable_publisher():
        """ Unsubscribe from all events """
        pub.unsubAll()

    def on_distance(self, xy_start: List[float]):
        """Update the start position of when event has started

        Parameters
        ----------
        xy_start : List[float]
            starting position in the x- and y-dimension
        """
        self.xy_start = xy_start

    def on_queue_change(self, msg: str):
        """Update size of the queue

        Parameters
        ----------
        msg : str
            message to be displayed in the queue marker
        """
        self.SetStatusText(msg, number=6)

    def on_event_mode(self, dataOut):
        """Changed cursor based on which key is pressed"""
        shift, ctrl, alt, add2table, wheel, zoom, dragged = dataOut
        self.mode = ""
        cursor = wx.StockCursor(wx.CURSOR_ARROW)
        if alt:
            self.mode = "Measure"
            cursor = wx.StockCursor(wx.CURSOR_MAGNIFIER)
        elif ctrl:
            self.mode = "Add data"
            cursor = wx.StockCursor(wx.CURSOR_CROSS)
        elif add2table:
            self.mode = "Add data"
            cursor = wx.StockCursor(wx.CURSOR_CROSS)
        elif shift:
            self.mode = "Wheel zoom Y"
            cursor = wx.StockCursor(wx.CURSOR_SIZENS)
        elif wheel:
            self.mode = "Wheel zoom X"
            cursor = wx.StockCursor(wx.CURSOR_SIZEWE)
        elif alt and ctrl:
            self.mode = ""
        elif dragged is not None:
            self.mode = "Dragging"
            cursor = wx.StockCursor(wx.CURSOR_HAND)
        elif zoom:
            self.mode = "Zooming"
            cursor = wx.StockCursor(wx.CURSOR_MAGNIFIER)

        self.SetCursor(cursor)
        self.SetStatusText("{}".format(self.mode), number=5)

    def on_motion(self, xpos, ypos, plotname):
        """Updates the x/y values shown in the window based on where in the plot area the mouse is found

        Parameters
        ----------
        xpos : float
            x-axis position of the mouse in the plot area
        ypos : float
            y-axis position of the mouse in the plot area
        plotname : str
            name of the plot from where the action is taking place
        """

        self.plot_name = plotname

        if xpos is None or ypos is None:
            msg = ""
        else:
            msg = "x={:.4f} y={:.4f}".format(xpos, ypos)
        self.SetStatusText(msg, number=0)

    #
    #         if xpos is not None and ypos is not None:
    #             # If measuring distance, additional fields are used to help user
    #             # make observations
    #             if self.startX is not None:
    #                 delta = np.absolute(self.startX - xpos)
    #                 charge = np.round(1.0 / delta, 1)
    #                 mass = (xpos + charge) * charge
    #                 # If inside a plot area with MS, give out charge state
    #                 if self.mode == "Measure" and self.panelPlots.currentPage in ["MS", "DT/MS"]:
    #                     self.SetStatusText(
    #                         f"m/z={xpos:.2f} int={ypos:.2f} Δm/z={delta:.2f} z={charge:.1f} mw={mass:.1f}", number=0
    #                     )
    #                 else:
    #                     if self.panelPlots.currentPage in ["MS"]:
    #                         self.SetStatusText("m/z={:.4f} int={:.4f} Δm/z={:.2f}".format(xpos, ypos, delta),
    #                         number=0)
    #                     elif self.panelPlots.currentPage in ["DT/MS"]:
    #                         self.SetStatusText("m/z={:.4f} dt={:.4f} Δm/z={:.2f}".format(xpos, ypos, delta), number=0)
    #                     elif self.panelPlots.currentPage in ["RT"]:
    #                         self.SetStatusText("scan={:.0f} int={:.4f} Δscans={:.2f}".format(xpos, ypos, delta),
    #                         number=0)
    #                     elif self.panelPlots.currentPage in ["1D"]:
    #                         self.SetStatusText("dt={:.2f} int={:.4f} Δdt={:.2f}".format(xpos, ypos, delta), number=0)
    #                     elif self.panelPlots.currentPage in ["2D"]:
    #                         self.SetStatusText("x={:.4f} dt={:.4f} Δx={:.2f}".format(xpos, ypos, delta), number=0)
    #                     else:
    #                         self.SetStatusText("x={:.4f} y={:.4f} Δx={:.2f}".format(xpos, ypos, delta), number=0)
    #             else:
    #                 if self.panelPlots.currentPage in ["MS"]:
    #                     self.SetStatusText("m/z={:.4f} int={:.4f}".format(xpos, ypos), number=0)
    #                 elif self.panelPlots.currentPage in ["DT/MS"]:
    #                      if self.plot_data["DT/MS"] is not None and len(self.plot_scale["DT/MS"]) == 2:
    #                                              try:
    #                                                  yIdx = int(ypos * self.plot_scale["DT/MS"][0]) - 1
    #                                                  xIdx = int(xpos * self.plot_scale["DT/MS"][1]) - 1
    #                                                  int_value = self.plot_data["DT/MS"][yIdx, xIdx]
    #                                              except Exception:
    #                                              int_value = 0.0
    #                     self.SetStatusText("m/z={:.4f} dt={:.4f} int={:.2f}".format(xpos, ypos, int_value), number=0)
    #                     else:
    #                     self.SetStatusText("m/z={:.4f} dt={:.4f}".format(xpos, ypos), number=0)
    #                 elif self.panelPlots.currentPage in ["RT"]:
    #                     self.SetStatusText("scan={:.0f} int={:.2f}".format(xpos, ypos), number=0)
    #                 elif self.panelPlots.currentPage in ["1D"]:
    #                     self.SetStatusText("dt={:.2f} int={:.2f}".format(xpos, ypos), number=0)
    #                 elif self.panelPlots.currentPage in ["2D"]:
    #                     try:
    #                         if self.plot_data["2D"] is not None and len(self.plot_scale["2D"]) == 2:
    #                             try:
    #                                 yIdx = int(ypos * self.plot_scale["2D"][0]) - 1
    #                                 xIdx = int(xpos * self.plot_scale["2D"][1]) - 1
    #                                 int_value = self.plot_data["2D"][yIdx, xIdx]
    #                             except Exception:
    #                                 int_value = ""
    #                             self.SetStatusText("x={:.2f} dt={:.2f} int={:.2f}".format(xpos, ypos, int_value),
    #                             number=0)
    #                         else:
    #                             self.SetStatusText("x={:.2f} dt={:.2f}".format(xpos, ypos), number=0)
    #                     except Exception:
    #                         self.SetStatusText("x={:.2f} dt={:.2f}".format(xpos, ypos), number=0)
    #                 elif plotname == "zGrid":
    #                     self.SetStatusText("x={:.2f} charge={:.0f}".format(xpos, ypos), number=0)
    #                 elif plotname == "mwDistribution":
    #                     self.SetStatusText("MW={:.2f} intensity={:.2f}".format(xpos, ypos), number=0)
    #                 else:
    #                     self.SetStatusText("x={:.2f} y={:.2f}".format(xpos, ypos), number=0)

    def motion_range(self, xmin, xmax, ymin, ymax):
        if self.mode == "Add data":
            self.SetStatusText(f"X={xmin:.3f}:{xmax:.3f} | Y={ymin:.3f}:{ymax:.3f}", number=4)
        else:
            self.SetStatusText("", number=4)

    def on_size(self, evt):
        """Toggles the resized attribute when user is changing the size of the window"""
        self.resized = True

    def on_idle(self, evt):
        """Toggles the resized attribute when user has finished changing the size of the window"""
        if self.resized:
            self.resized = False

    def on_open_about_panel(self, evt):
        """Show About ORIGAMI panel."""
        from origami.gui_elements.panel_about import PanelAbout

        about = PanelAbout(self, self.presenter, "About ORIGAMI", CONFIG, self.icons)
        about.Centre()
        about.Show()
        about.SetFocus()

    def on_open_plot_settings_panel(self, evt):
        if evt.GetId() == ID_extraSettings_colorbar:
            kwargs = {"window": "Colorbar"}
        elif evt.GetId() == ID_extraSettings_legend:
            kwargs = {"window": "Legend"}
        elif evt.GetId() == ID_extraSettings_plot1D:
            kwargs = {"window": "Plot 1D"}
        elif evt.GetId() == ID_extraSettings_plot2D:
            kwargs = {"window": "Plot 2D"}
        elif evt.GetId() == ID_extraSettings_plot3D:
            kwargs = {"window": "Plot 3D"}
        elif evt.GetId() == ID_extraSettings_rmsd:
            kwargs = {"window": "RMSD"}
        elif evt.GetId() == ID_extraSettings_waterfall:
            kwargs = {"window": "Waterfall"}
        elif evt.GetId() == ID_extraSettings_violin:
            kwargs = {"window": "Violin"}
        elif evt.GetId() == ID_extraSettings_general:
            kwargs = {"window": "Extra"}
        elif evt.GetId() == ID_extraSettings_general_plot:
            kwargs = {"window": "General"}

        if not self.panelParametersEdit.IsShown() or not CONFIG._windowSettings["Plot parameters"]["show"]:
            if CONFIG._windowSettings["Plot parameters"]["floating"]:
                self.window_mgr.GetPane(self.panelParametersEdit).Float()

            self.window_mgr.GetPane(self.panelParametersEdit).Show()
            CONFIG._windowSettings["Plot parameters"]["show"] = True
            self.panelParametersEdit.on_set_page(**kwargs)
            self.window_mgr.Update()
        else:
            args = ("An instance of this panel is already open - changing page to: %s" % kwargs["window"], 4)
            self.presenter.onThreading(evt, args, action="updateStatusbar")
            self.panelParametersEdit.on_set_page(**kwargs)
            return

    def on_open_export_settings_panel(self, evt):
        if evt.GetId() == ID_importExportSettings_image:
            kwargs = {"window": "Image"}
        elif evt.GetId() == ID_importExportSettings_file:
            kwargs = {"window": "Files"}
        elif evt.GetId() == ID_importExportSettings_peaklist:
            kwargs = {"window": "Peaklist"}

        if CONFIG.importExportParamsWindow_on_off:
            args = ("An instance of this panel is already open - changing page to: %s" % kwargs["window"], 4)
            self.presenter.onThreading(evt, args, action="updateStatusbar")
            self.panelImportExportParameters.onSetPage(**kwargs)
            return

        self.SetStatusText("", 4)

        try:
            CONFIG.importExportParamsWindow_on_off = True
            self.panelImportExportParameters = PanelExportSettings(self, self.presenter, CONFIG, self.icons, **kwargs)
            self.panelImportExportParameters.Show()
        except (ValueError, AttributeError, TypeError, KeyError) as e:
            CONFIG.importExportParamsWindow_on_off = False
            DialogBox(title="Failed to open panel", msg=str(e), kind="Error")
            return

    def on_open_interactive_output_panel(self, evt):
        def startup_module():
            """Initialize the panel"""
            CONFIG.interactiveParamsWindow_on_off = True
            self.panel_interactive_output = PanelInteractiveCreator(self, self.icons, self.presenter, CONFIG)
            self.panel_interactive_output.Show()

        if not hasattr(self, "panel_interactive_output"):
            startup_module()
        else:
            try:
                if CONFIG.interactiveParamsWindow_on_off:
                    self.panel_interactive_output.onUpdateList()
                    args = ("An instance of this panel is already open", 4)
                    self.presenter.onThreading(evt, args, action="updateStatusbar")
                    return
            except (IndexError, ValueError, TypeError, KeyError):
                logging.error("Failed to startup `Interactive Output` panel", exc_info=True)
                startup_module()

    def on_update_recent_files(self, path=None):
        """
        path = dictionary {'file_path': path, 'file_type': file type}
        """

        if path:
            if path in CONFIG.previousFiles:
                del CONFIG.previousFiles[CONFIG.previousFiles.index(path)]
            CONFIG.previousFiles.insert(0, path)
            # make sure only 10 items are present in the list
            while len(CONFIG.previousFiles) > 10:
                del CONFIG.previousFiles[-1]

        # clear menu
        for item in self.menuRecent.GetMenuItems():
            self.menuRecent.Delete(item.GetId())

        # populate menu
        for i, __ in enumerate(CONFIG.previousFiles):
            ID = eval("ID_documentRecent" + str(i))
            path = CONFIG.previousFiles[i]["file_path"]
            self.menuRecent.Insert(i, ID, path, "Open Document")
            self.Bind(wx.EVT_MENU, self.on_open_recent_file, id=ID)
            if not os.path.exists(path):
                self.menuRecent.Enable(ID, False)

        # append clear
        if len(CONFIG.previousFiles) > 0:
            self.menuRecent.AppendSeparator()

        self.menuRecent.Append(ID_fileMenu_clearRecent, "Clear Menu", "Clear recent items")
        self.Bind(wx.EVT_MENU, self.on_clear_recent_files, id=ID_fileMenu_clearRecent)

        if CONFIG.autoSaveSettings:
            self.data_handling.on_export_config_fcn(None, False)

    def on_clear_recent_files(self, evt):
        """Clear recent items."""

        CONFIG.previousFiles = []
        self.on_update_recent_files()

    def on_open_recent_file(self, evt):
        """Open recent document."""
        # TODO: FIXME
        # get index
        indexes = {
            ID_documentRecent0: 0,
            ID_documentRecent1: 1,
            ID_documentRecent2: 2,
            ID_documentRecent3: 3,
            ID_documentRecent4: 4,
            ID_documentRecent5: 5,
            ID_documentRecent6: 6,
            ID_documentRecent7: 7,
            ID_documentRecent8: 8,
            ID_documentRecent9: 9,
        }

        # get file information
        documentID = indexes[evt.GetId()]
        file_path = CONFIG.previousFiles[documentID]["file_path"]
        file_type = CONFIG.previousFiles[documentID]["file_type"]

        # open file
        if file_type == "pickle":
            self.data_handling.on_open_document_fcn(None, file_path=file_path)
        elif file_type == "MassLynx":
            self.data_handling.on_open_single_MassLynx_raw(file_path, "Type: MassLynx")
        elif file_type == "ORIGAMI":
            self.data_handling.on_open_single_MassLynx_raw(file_path, "Type: ORIGAMI")
        elif file_type == "Infrared":
            self.data_handling.on_open_single_MassLynx_raw(file_path, "Type: Infrared")
        elif file_type == "Text":
            self.data_handling.on_add_text_2d(None, file_path)
        elif file_type == "Text_MS":
            self.data_handling.on_add_text_ms(path=file_path)

    def on_open_file_from_dnd(self, file_path, file_extension):
        # open file
        if file_extension in [".pickle", ".pkl"]:
            self.data_handling.on_open_document_fcn(None, file_path)
        elif file_extension == ".raw":
            self.data_handling.on_open_single_MassLynx_raw(file_path, "Type: ORIGAMI")
        elif file_extension in [".txt", ".csv", ".tab"]:
            file_format = check_file_type(path=file_path)
            if file_format == "2D":
                self.data_handling.on_add_text_2d(None, file_path)
            else:
                self.data_handling.on_add_text_ms(path=file_path)

    def updateStatusbar(self, msg, position, delay=3, modify_msg=True, print_msg=True):
        """
        Out of thread statusbar display

        Parameters
        ----------
        msg: str
            message to be displayed for specified amount of time
        position: int
            which statusbar box the msg should be displayed in
        delay: int
            number of seconds for which the msg should be displayed for
        modify_msg: bool
            determines whether text should be wrapped between >> TEXT <<
        print_msg: bool
            determines whether message should be printed to console
        """
        # modify message
        if modify_msg:
            msg = f">> {msg} <<"

        if print_msg:
            logger.info(msg)

        # disable delay during testing
        if CONFIG.testing:
            return

        try:
            self.SetStatusText(msg, number=position)
            sleep(delay)
            self.SetStatusText("", number=position)
        except Exception:
            print(f"Statusbar update: {msg}")

    @staticmethod
    def on_update_interaction_settings(evt):
        """
        build and update parameters in the zoom function
        """
        plot_parameters = {
            "grid_show": CONFIG._plots_grid_show,
            "grid_color": CONFIG._plots_grid_color,
            "grid_line_width": CONFIG._plots_grid_line_width,
            "extract_color": CONFIG._plots_extract_color,
            "extract_line_width": CONFIG._plots_extract_line_width,
            "extract_crossover_sensitivity_1D": CONFIG._plots_extract_crossover_1D,
            "extract_crossover_sensitivity_2D": CONFIG._plots_extract_crossover_2D,
            "zoom_color_vertical": CONFIG._plots_zoom_vertical_color,
            "zoom_color_horizontal": CONFIG._plots_zoom_horizontal_color,
            "zoom_color_box": CONFIG._plots_zoom_box_color,
            "zoom_line_width": CONFIG._plots_zoom_line_width,
            "zoom_crossover_sensitivity": CONFIG._plots_zoom_crossover,
        }
        pub.sendMessage("plot_parameters", plot_parameters=plot_parameters)

        if evt is not None:
            evt.Skip()

    @staticmethod
    def on_toggle_threading(evt):
        """Enable/disable multi-threading in the application"""

        if CONFIG.threading:
            msg = (
                "Multi-threading is only an experimental feature for now! It might occasionally crash ORIGAMI,"
                + " in which case you will lose your processed data!"
            )
            DialogBox(title="Warning", msg=msg, kind="Warning")
        if evt is not None:
            evt.Skip()

    @staticmethod
    def on_check_driftscope_path(evt=None):
        check = CONFIG.setup_paths(return_check=True)
        if check:
            wx.Bell()
            DialogBox(
                title="DriftScope path looks good", msg="Found DriftScope on your PC. You are good to go.", kind="Info"
            )
            return


class DragAndDrop(wx.FileDropTarget):
    def __init__(self, window):
        """Constructor"""
        wx.FileDropTarget.__init__(self)
        self.window = window

    def OnDropFiles(self, x, y, filenames):
        """When files are dropped, write where they were dropped and then the file paths themselves"""
        logger.info(f"Dropped {len(filenames)} in the window")
        for filename in filenames:
            logger.info("Opening {filename} file...")
            __, file_extension = os.path.splitext(filename)
            if file_extension in [".raw", ".pickle", ".pkl", ".txt", ".csv", ".tab"]:
                try:
                    self.window.on_open_file_from_dnd(filename, file_extension)
                except Exception:
                    logger.error("Failed to open {}".format(filename))
                    continue
            else:
                logger.warning("Dropped file is not supported")
                continue
