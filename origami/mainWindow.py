# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
# Load libraries
import logging
import os
import webbrowser
from time import gmtime
from time import sleep
from time import strftime

import numpy as np
import psutil
import wx.aui
from gui_elements.dialog_notify_new_version import DialogNewVersion
from gui_elements.dialog_notify_open_documents import DialogNotifyOpenDocuments
from gui_elements.misc_dialogs import DialogBox
from gui_elements.panel_exportSettings import panelExportSettings
from ids import ID_addCCScalibrantFile
from ids import ID_addNewInteractiveDoc
from ids import ID_addNewManualDoc
from ids import ID_addNewOverlayDoc
from ids import ID_annotPanel_otherSettings
from ids import ID_assignChargeState
from ids import ID_check_Driftscope
from ids import ID_CHECK_VERSION
from ids import ID_checkAtStart_Driftscope
from ids import ID_clearAllPlots
from ids import ID_docTree_compareMS
from ids import ID_docTree_plugin_MSMS
from ids import ID_docTree_plugin_UVPD
from ids import ID_documentRecent0
from ids import ID_documentRecent1
from ids import ID_documentRecent2
from ids import ID_documentRecent3
from ids import ID_documentRecent4
from ids import ID_documentRecent5
from ids import ID_documentRecent6
from ids import ID_documentRecent7
from ids import ID_documentRecent8
from ids import ID_documentRecent9
from ids import ID_extraSettings_colorbar
from ids import ID_extraSettings_general
from ids import ID_extraSettings_general_plot
from ids import ID_extraSettings_legend
from ids import ID_extraSettings_plot1D
from ids import ID_extraSettings_plot2D
from ids import ID_extraSettings_plot3D
from ids import ID_extraSettings_rmsd
from ids import ID_extraSettings_violin
from ids import ID_extraSettings_waterfall
from ids import ID_fileMenu_clearRecent
from ids import ID_fileMenu_MGF
from ids import ID_fileMenu_mzML
from ids import ID_fileMenu_openRecent
from ids import ID_fileMenu_thermoRAW
from ids import ID_help_page_annotatingMassSpectra
from ids import ID_help_page_CCScalibration
from ids import ID_help_page_dataExtraction
from ids import ID_help_page_dataLoading
from ids import ID_help_page_gettingStarted
from ids import ID_help_page_Interactive
from ids import ID_help_page_linearDT
from ids import ID_help_page_multipleFiles
from ids import ID_help_page_ORIGAMI
from ids import ID_help_page_OtherData
from ids import ID_help_page_overlay
from ids import ID_help_page_UniDec
from ids import ID_help_UniDecInfo
from ids import ID_helpAuthor
from ids import ID_helpCite
from ids import ID_helpGitHub
from ids import ID_helpGuide
from ids import ID_helpGuideLocal
from ids import ID_helpHomepage
from ids import ID_helpHTMLEditor
from ids import ID_helpNewFeatures
from ids import ID_helpNewVersion
from ids import ID_helpReportBugs
from ids import ID_helpYoutube
from ids import ID_importAtStart_CCS
from ids import ID_importExportSettings_file
from ids import ID_importExportSettings_image
from ids import ID_importExportSettings_peaklist
from ids import ID_load_clipboard_spectrum
from ids import ID_load_masslynx_raw
from ids import ID_load_masslynx_raw_ms_only
from ids import ID_load_multiple_masslynx_raw
from ids import ID_load_multiple_origami_masslynx_raw
from ids import ID_load_multiple_text_2D
from ids import ID_load_origami_masslynx_raw
from ids import ID_load_text_2D
from ids import ID_load_text_MS
from ids import ID_mainPanel_openSourceFiles
from ids import ID_openAsConfig
from ids import ID_openCCScalibrationDatabse
from ids import ID_openConfig
from ids import ID_openDocument
from ids import ID_openIRRawFile
from ids import ID_openLinearDTRawFile
from ids import ID_plots_showCursorGrid
from ids import ID_process2DDocument
from ids import ID_quit
from ids import ID_renameItem
from ids import ID_RESET_ORIGAMI
from ids import ID_save1DImage
from ids import ID_save2DImage
from ids import ID_save3DImage
from ids import ID_saveAllDocuments
from ids import ID_saveAsConfig
from ids import ID_saveAsInteractive
from ids import ID_saveConfig
from ids import ID_saveDataCSVDocument
from ids import ID_saveDocument
from ids import ID_saveMSImage
from ids import ID_saveMZDTImage
from ids import ID_saveOverlayImage
from ids import ID_saveRMSDImage
from ids import ID_saveRMSDmatrixImage
from ids import ID_saveRMSFImage
from ids import ID_saveRTImage
from ids import ID_saveWaterfallImage
from ids import ID_selectCalibrant
from ids import ID_setDriftScopeDir
from ids import ID_SHOW_ABOUT
from ids import ID_showPlotDocument
from ids import ID_showPlotMSDocument
from ids import ID_unidecPanel_otherSettings
from ids import ID_WHATS_NEW
from ids import ID_window_all
from ids import ID_window_controls
from ids import ID_window_documentList
from ids import ID_window_ionList
from ids import ID_window_multipleMLList
from ids import ID_window_textList
from ids import ID_windowFullscreen
from ids import ID_windowMaximize
from ids import ID_windowMinimize
from panel_document_tree import PanelDocumentTree
from panel_multi_file import PanelMultiFile
from panel_peaklist import PanelPeaklist
from panel_plots import PanelPlots
from panel_textlist import PanelTextlist
from panelExtraParameters import panelParametersEdit
from panelInteractiveOutput import panelInteractiveOutput as panelInteractive
from processing.data_handling import data_handling
from processing.data_processing import data_processing
from processing.data_visualisation import data_visualisation
from pubsub import pub
from readers.io_text_files import check_file_type
from styles import makeMenuItem
from toolbox import compare_versions
from toolbox import get_latest_version
from utils.path import clean_directory

logger = logging.getLogger("origami")


class MyFrame(wx.Frame):
    def __init__(self, parent, config, helpInfo, icons, title="ORIGAMI"):
        wx.Frame.__init__(self, None, title=title)

        # Extract size of screen
        self.displaysize = wx.GetDisplaySize()
        self.SetDimensions(0, 0, self.displaysize[0], self.displaysize[1] - 50)
        # Setup config container
        self.config = config
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
        self.startX = None

        self.resized = False

        self.config.startTime = strftime("%Y_%m_%d-%H-%M-%S", gmtime())

        # Bind commands to events
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_IDLE, self.OnIdle)

        # Setup Notebook manager
        self._mgr = wx.aui.AuiManager(self)
        self._mgr.SetDockSizeConstraint(1, 1)

        # Load panels
        self.panelDocuments = PanelDocumentTree(self, self.config, self.icons, self.presenter)

        self.panelPlots = PanelPlots(self, self.config, self.presenter)
        self.panelMultipleIons = PanelPeaklist(self, self.config, self.icons, self.help, self.presenter)
        self.panelMultipleText = PanelTextlist(self, self.config, self.icons, self.presenter)
        self.panelMML = PanelMultiFile(self, self.config, self.icons, self.presenter)

        kwargs = {"window": None}
        self.panelParametersEdit = panelParametersEdit(self, self.presenter, self.config, self.icons, **kwargs)

        # add handling, processing and visualisation pipelines
        self.data_processing = data_processing(self.presenter, self, self.config)
        self.data_handling = data_handling(self.presenter, self, self.config)
        self.data_visualisation = data_visualisation(self.presenter, self, self.config)

        # make toolbar
        self.make_toolbar()

        # Panel to store document information
        self._mgr.AddPane(
            self.panelDocuments,
            wx.aui.AuiPaneInfo()
            .Left()
            .Caption("Documents")
            .MinSize((250, 100))
            .GripperTop()
            .BottomDockable(False)
            .TopDockable(False)
            .Show(self.config._windowSettings["Documents"]["show"])
            .CloseButton(self.config._windowSettings["Documents"]["close_button"])
            .CaptionVisible(self.config._windowSettings["Documents"]["caption"])
            .Gripper(self.config._windowSettings["Documents"]["gripper"]),
        )

        self._mgr.AddPane(
            self.panelPlots,
            wx.aui.AuiPaneInfo()
            .CenterPane()
            .Caption("Plot")
            .Show(self.config._windowSettings["Plots"]["show"])
            .CloseButton(self.config._windowSettings["Plots"]["close_button"])
            .CaptionVisible(self.config._windowSettings["Plots"]["caption"])
            .Gripper(self.config._windowSettings["Plots"]["gripper"]),
        )

        # Panel to extract multiple ions from ML files
        self._mgr.AddPane(
            self.panelMultipleIons,
            wx.aui.AuiPaneInfo()
            .Right()
            .Caption("Peak list")
            .MinSize((300, -1))
            .GripperTop()
            .BottomDockable(True)
            .TopDockable(False)
            .Show(self.config._windowSettings["Peak list"]["show"])
            .CloseButton(self.config._windowSettings["Peak list"]["close_button"])
            .CaptionVisible(self.config._windowSettings["Peak list"]["caption"])
            .Gripper(self.config._windowSettings["Peak list"]["gripper"]),
        )

        # Panel to operate on multiple text files
        self._mgr.AddPane(
            self.panelMultipleText,
            wx.aui.AuiPaneInfo()
            .Right()
            .Caption("Text files")
            .MinSize((300, -1))
            .GripperTop()
            .BottomDockable(True)
            .TopDockable(False)
            .Show(self.config._windowSettings["Text files"]["show"])
            .CloseButton(self.config._windowSettings["Text files"]["close_button"])
            .CaptionVisible(self.config._windowSettings["Text files"]["caption"])
            .Gripper(self.config._windowSettings["Text files"]["gripper"]),
        )

        # Panel to operate on multiple ML files
        self._mgr.AddPane(
            self.panelMML,
            wx.aui.AuiPaneInfo()
            .Right()
            .Caption("Multiple files")
            .MinSize((300, -1))
            .GripperTop()
            .BottomDockable(True)
            .TopDockable(False)
            .Show(self.config._windowSettings["Multiple files"]["show"])
            .CloseButton(self.config._windowSettings["Multiple files"]["close_button"])
            .CaptionVisible(self.config._windowSettings["Multiple files"]["caption"])
            .Gripper(self.config._windowSettings["Multiple files"]["gripper"]),
        )

        self._mgr.AddPane(
            self.panelParametersEdit,
            wx.aui.AuiPaneInfo()
            .Right()
            .Caption(self.config._windowSettings["Plot parameters"]["title"])
            .MinSize((320, -1))
            .GripperTop()
            .BottomDockable(True)
            .TopDockable(False)
            .Show(self.config._windowSettings["Plot parameters"]["show"])
            .CloseButton(self.config._windowSettings["Plot parameters"]["close_button"])
            .CaptionVisible(self.config._windowSettings["Plot parameters"]["caption"])
            .Gripper(self.config._windowSettings["Plot parameters"]["gripper"]),
        )

        # Setup listeners
        pub.subscribe(self.on_motion, "motion_xy")
        pub.subscribe(self.motion_range, "motion_range")
        pub.subscribe(self.on_distance, "change_x_axis_start")
        pub.subscribe(self.panelPlots.on_change_rmsf_zoom, "change_zoom_rmsd")
        pub.subscribe(self.on_event_mode, "motion_mode")
        pub.subscribe(self.data_handling.on_update_DTMS_zoom, "change_zoom_dtms")

        # Load other parts
        self._mgr.Update()
        # self.makeBindings()
        self.make_statusbar()
        self.make_menubar()
        self.make_shortcuts()
        self.Maximize(True)

        # bind events
        self.Bind(wx.aui.EVT_AUI_PANE_CLOSE, self.on_closed_page)
        self.Bind(wx.aui.EVT_AUI_PANE_RESTORE, self.on_restored_page)

        # Fire up a couple of events
        self.on_update_panel_config()
        self.on_toggle_panel(evt=None)
        self.on_toggle_panel_at_start()

    def on_update_panel_config(self):
        self.config._windowSettings["Documents"]["id"] = ID_window_documentList
        self.config._windowSettings["Peak list"]["id"] = ID_window_ionList
        self.config._windowSettings["Text files"]["id"] = ID_window_textList
        self.config._windowSettings["Multiple files"]["id"] = ID_window_multipleMLList

    def on_toggle_panel_at_start(self):
        panelDict = {
            "Documents": ID_window_documentList,
            "Multiple files": ID_window_multipleMLList,
            "Peak list": ID_window_ionList,
            "Text files": ID_window_textList,
        }

        for panel in [self.panelDocuments, self.panelMML, self.panelMultipleIons, self.panelMultipleText]:
            if self._mgr.GetPane(panel).IsShown():
                self.on_find_toggle_by_id(find_id=panelDict[self._mgr.GetPane(panel).caption], check=True)

    def _onUpdatePlotData(self, plot_type=None):
        if plot_type == "2D":
            _data = self.presenter._get_replot_data(data_format="2D")
            try:
                yshape, xshape = _data[0].shape
                _yscale = yshape / np.max(_data[2])
                _xscale = xshape / np.max(_data[1])
                self.plot_data["2D"] = _data[0]
                self.plot_scale["2D"] = [_yscale, _xscale]
            except Exception:
                pass
        elif plot_type == "DT/MS":
            _data = self.presenter._get_replot_data(data_format="DT/MS")
            yshape, xshape = _data[0].shape
            _yscale = yshape / np.max(_data[2])
            _xscale = xshape / np.max(_data[1])
            self.plot_data["DT/MS"] = _data[0]
            self.plot_scale["DT/MS"] = [_yscale, _xscale]
        elif plot_type == "RMSF":
            _data = self.presenter._get_replot_data(data_format="RMSF")
            yshape, xshape = _data[0].shape
            _yscale = yshape / np.max(_data[2])
            _xscale = xshape / np.max(_data[1])
            self.plot_data["DT/MS"] = _data[0]
            self.plot_scale["DT/MS"] = [_yscale, _xscale]

    def on_closed_page(self, evt):
        # Keep track of which window is closed
        self.config._windowSettings[evt.GetPane().caption]["show"] = False
        # fire-up events
        try:
            evtID = self.onCheckToggleID(panel=evt.GetPane().caption)
            self.on_toggle_panel(evt=evtID)
        except Exception:
            pass

    def on_restored_page(self, evt):
        # Keep track of which window is restored
        self.config._windowSettings[evt.GetPane().caption]["show"] = True
        evtID = self.onCheckToggleID(panel=evt.GetPane().caption)
        self.on_toggle_panel(evt=evtID)
        # fire-up events

        if evt is not None:
            evt.Skip()

    def make_statusbar(self):

        self.mainStatusbar = self.CreateStatusBar(6, wx.STB_SIZEGRIP, wx.ID_ANY)
        # 0 = current x y pos
        # 1 = m/z range
        # 2 = MSMS mass
        # 3 = status information
        # 4 = present working file
        # 5 = tool
        # 6 = process
        self.mainStatusbar.SetStatusWidths([250, 80, 80, 200, -1, 50])
        self.mainStatusbar.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))

    def on_event_mode(self, dataOut):
        shift, ctrl, alt, add2table, wheel, zoom, dragged = dataOut
        self.mode = ""
        myCursor = wx.StockCursor(wx.CURSOR_ARROW)
        if alt:
            self.mode = "Measure"
            myCursor = wx.StockCursor(wx.CURSOR_MAGNIFIER)
        elif ctrl:
            self.mode = "Add data"
            myCursor = wx.StockCursor(wx.CURSOR_CROSS)
        elif add2table:
            self.mode = "Add data"
            myCursor = wx.StockCursor(wx.CURSOR_CROSS)
        elif shift:
            self.mode = "Wheel zoom Y"
            myCursor = wx.StockCursor(wx.CURSOR_SIZENS)
        elif wheel:
            self.mode = "Wheel zoom X"
            myCursor = wx.StockCursor(wx.CURSOR_SIZEWE)
        elif alt and ctrl:
            self.mode = ""
        elif dragged is not None:
            self.mode = "Dragging"
            myCursor = wx.StockCursor(wx.CURSOR_HAND)
        elif zoom:
            self.mode = "Zooming"
            myCursor = wx.StockCursor(wx.CURSOR_MAGNIFIER)

        self.SetCursor(myCursor)
        self.SetStatusText("{}".format(self.mode), number=5)

    def make_menubar(self):
        self.mainMenubar = wx.MenuBar()

        # setup recent sub-menu
        self.menuRecent = wx.Menu()
        self.updateRecentFiles()

        openCommunityMenu = wx.Menu()
        openCommunityMenu.Append(ID_fileMenu_MGF, "Open Mascot Generic Format file (.mgf) [MS/MS]")
        openCommunityMenu.Append(ID_fileMenu_mzML, "Open mzML (.mzML) [MS/MS]")

        menuFile = wx.Menu()
        menuFile.AppendMenu(ID_fileMenu_openRecent, "Open Recent", self.menuRecent)
        menuFile.AppendSeparator()
        menuFile.AppendItem(
            makeMenuItem(
                parent=menuFile,
                id=ID_openDocument,
                text="Open ORIGAMI Document file (.pickle)\tCtrl+Shift+P",
                bitmap=self.icons.iconsLib["open_project_16"],
            )
        )
        menuFile.AppendSeparator()
        menuFile.AppendItem(
            makeMenuItem(
                parent=menuFile,
                id=ID_load_origami_masslynx_raw,
                text="Open ORIGAMI MassLynx (.raw) file [CIU]\tCtrl+R",
                bitmap=self.icons.iconsLib["open_origami_16"],
            )
        )

        menuFile.AppendItem(
            makeMenuItem(
                parent=menuFile,
                id=ID_load_multiple_origami_masslynx_raw,
                text="Open multiple ORIGAMI MassLynx (.raw) files [CIU]\tCtrl+Shift+Q",
                bitmap=self.icons.iconsLib["open_origamiMany_16"],
            )
        )
        menuFile.AppendSeparator()
        menuFile.AppendItem(
            makeMenuItem(
                parent=menuFile,
                id=ID_addNewManualDoc,
                text="Create blank MANUAL document [CIU]",
                bitmap=self.icons.iconsLib["guide_16"],
            )
        )
        menuFile.AppendItem(
            makeMenuItem(
                parent=menuFile,
                id=ID_load_multiple_masslynx_raw,
                text="Open multiple MassLynx (.raw) files [CIU]\tCtrl+Shift+R",
                bitmap=self.icons.iconsLib["open_masslynxMany_16"],
            )
        )
        menuFile.AppendSeparator()
        menuFile.Append(ID_addCCScalibrantFile, "Open MassLynx (.raw) file [Calibration]\tCtrl+C")
        menuFile.Append(ID_openLinearDTRawFile, "Open MassLynx (.raw) file [Linear DT]\tCtrl+F")
        menuFile.Append(ID_load_masslynx_raw_ms_only, "Open MassLynx (no IM-MS, .raw) file\tCtrl+Shift+M")
        menuFile.AppendSeparator()
        menuFile.AppendItem(
            makeMenuItem(
                parent=menuFile, id=ID_fileMenu_thermoRAW, text="Open Thermo (.RAW) file\tCtrl+Shift+Y", bitmap=None
            )
        )
        menuFile.AppendSeparator()
        menuFile.AppendMenu(wx.ID_ANY, "Open MS/MS files...", openCommunityMenu)
        menuFile.AppendSeparator()
        menuFile.AppendItem(
            makeMenuItem(
                parent=menuFile,
                id=ID_addNewOverlayDoc,
                text="Create blank COMPARISON document [CIU]",
                bitmap=self.icons.iconsLib["new_document_16"],
            )
        )
        menuFile.AppendItem(
            makeMenuItem(
                parent=menuFile,
                id=ID_addNewInteractiveDoc,
                text="Create blank INTERACTIVE document",
                bitmap=self.icons.iconsLib["bokehLogo_16"],
            )
        )
        menuFile.AppendSeparator()
        menuFile.AppendItem(makeMenuItem(parent=menuFile, id=ID_load_text_MS, text="Open MS Text file", bitmap=None))
        menuFile.AppendItem(
            makeMenuItem(
                parent=menuFile,
                id=ID_load_text_2D,
                text="Open IM-MS Text file [CIU]\tCtrl+T",
                bitmap=self.icons.iconsLib["open_text_16"],
            )
        )
        menuFile.AppendItem(
            makeMenuItem(
                parent=menuFile,
                id=ID_load_multiple_text_2D,
                text="Open multiple IM-MS text files [CIU]\tCtrl+Shift+T",
                bitmap=self.icons.iconsLib["open_textMany_16"],
            )
        )
        menuFile.AppendSeparator()
        menuFile.AppendItem(
            makeMenuItem(
                parent=menuFile,
                id=ID_load_clipboard_spectrum,
                text="Grab MS spectrum from clipboard\tCtrl+V",
                bitmap=self.icons.iconsLib["filelist_16"],
            )
        )

        menuFile.AppendSeparator()
        menuFile.AppendItem(
            makeMenuItem(
                parent=menuFile,
                id=ID_saveDocument,
                text="Save document (.pickle)\tCtrl+S",
                bitmap=self.icons.iconsLib["save16"],
            )
        )
        menuFile.AppendItem(
            makeMenuItem(
                parent=menuFile,
                id=ID_saveAllDocuments,
                text="Save all documents (.pickle)",
                bitmap=self.icons.iconsLib["pickle_16"],
            )
        )
        menuFile.AppendSeparator()
        menuFile.AppendItem(
            makeMenuItem(parent=menuFile, id=ID_quit, text="Quit\tCtrl+Q", bitmap=self.icons.iconsLib["exit_16"])
        )
        self.mainMenubar.Append(menuFile, "&File")

        # PLOT
        menuPlot = wx.Menu()
        menuPlot.AppendItem(
            makeMenuItem(
                parent=menuPlot,
                id=ID_extraSettings_general_plot,
                text="Settings: Plot &General",
                bitmap=self.icons.iconsLib["panel_plot_general_16"],
            )
        )

        menuPlot.AppendItem(
            makeMenuItem(
                parent=menuPlot,
                id=ID_extraSettings_plot1D,
                text="Settings: Plot &1D",
                bitmap=self.icons.iconsLib["panel_plot1D_16"],
            )
        )

        menuPlot.AppendItem(
            makeMenuItem(
                parent=menuPlot,
                id=ID_extraSettings_plot2D,
                text="Settings: Plot &2D",
                bitmap=self.icons.iconsLib["panel_plot2D_16"],
            )
        )

        menuPlot.AppendItem(
            makeMenuItem(
                parent=menuPlot,
                id=ID_extraSettings_plot3D,
                text="Settings: Plot &3D",
                bitmap=self.icons.iconsLib["panel_plot3D_16"],
            )
        )

        menuPlot.AppendItem(
            makeMenuItem(
                parent=menuPlot,
                id=ID_extraSettings_colorbar,
                text="Settings: &Colorbar",
                bitmap=self.icons.iconsLib["panel_colorbar_16"],
            )
        )

        menuPlot.AppendItem(
            makeMenuItem(
                parent=menuPlot,
                id=ID_extraSettings_legend,
                text="Settings: &Legend",
                bitmap=self.icons.iconsLib["panel_legend_16"],
            )
        )

        menuPlot.AppendItem(
            makeMenuItem(
                parent=menuPlot,
                id=ID_extraSettings_rmsd,
                text="Settings: &RMSD",
                bitmap=self.icons.iconsLib["panel_rmsd_16"],
            )
        )

        menuPlot.AppendItem(
            makeMenuItem(
                parent=menuPlot,
                id=ID_extraSettings_waterfall,
                text="Settings: &Waterfall",
                bitmap=self.icons.iconsLib["panel_waterfall_16"],
            )
        )

        menuPlot.AppendItem(
            makeMenuItem(
                parent=menuPlot,
                id=ID_extraSettings_violin,
                text="Settings: &Violin",
                bitmap=self.icons.iconsLib["panel_violin_16"],
            )
        )

        menuPlot.AppendItem(
            makeMenuItem(
                parent=menuPlot,
                id=ID_extraSettings_general,
                text="Settings: &Extra",
                bitmap=self.icons.iconsLib["panel_general2_16"],
            )
        )

        menuPlot.AppendSeparator()
        menuPlot.AppendItem(
            makeMenuItem(
                parent=menuPlot, id=ID_annotPanel_otherSettings, text="Settings: Annotation parameters", bitmap=None
            )
        )
        menuPlot.AppendItem(
            makeMenuItem(
                parent=menuPlot, id=ID_unidecPanel_otherSettings, text="Settings: UniDec parameters", bitmap=None
            )
        )

        menuPlot.AppendSeparator()
        menuPlot.Append(ID_plots_showCursorGrid, "Update plot parameters")
        # menuPlot.Append(ID_plots_resetZoom, 'Reset zoom tool\tF12')
        self.mainMenubar.Append(menuPlot, "&Plot settings")

        # VIEW
        menuView = wx.Menu()
        menuView.AppendItem(
            makeMenuItem(
                parent=menuView, id=ID_clearAllPlots, text="&Clear all plots", bitmap=self.icons.iconsLib["clear_16"]
            )
        )
        menuView.AppendSeparator()
        self.documentsPage = menuView.Append(ID_window_documentList, "Panel: Documents\tCtrl+1", kind=wx.ITEM_CHECK)
        self.mzTable = menuView.Append(ID_window_ionList, "Panel: Peak list\tCtrl+2", kind=wx.ITEM_CHECK)
        self.textTable = menuView.Append(ID_window_textList, "Panel: Text list\tCtrl+3", kind=wx.ITEM_CHECK)
        self.multipleMLTable = menuView.Append(
            ID_window_multipleMLList, "Panel: Multiple files\tCtrl+4", kind=wx.ITEM_CHECK
        )
        menuView.AppendSeparator()
        menuView.Append(ID_window_all, "Panel: Restore &all")
        menuView.AppendSeparator()
        menuView.AppendItem(
            makeMenuItem(
                parent=menuView, id=ID_windowMaximize, text="Maximize window", bitmap=self.icons.iconsLib["maximize_16"]
            )
        )
        menuView.AppendItem(
            makeMenuItem(
                parent=menuView, id=ID_windowMinimize, text="Minimize window", bitmap=self.icons.iconsLib["minimize_16"]
            )
        )
        menuView.AppendItem(
            makeMenuItem(
                parent=menuView,
                id=ID_windowFullscreen,
                text="Toggle fullscreen\tAlt+F11",
                bitmap=self.icons.iconsLib["fullscreen_16"],
            )
        )
        self.mainMenubar.Append(menuView, "&View")

        # WIDGETS
        menuWidgets = wx.Menu()
        menuWidgets.AppendItem(
            makeMenuItem(
                parent=menuView,
                id=ID_saveAsInteractive,
                text="Open &interactive output panel...\tShift+Z",
                bitmap=self.icons.iconsLib["bokehLogo_16"],
            )
        )
        menuWidgets.AppendItem(
            makeMenuItem(
                parent=menuWidgets,
                id=ID_docTree_compareMS,
                text="Open spectrum comparison window...",
                bitmap=self.icons.iconsLib["compare_mass_spectra_16"],
            )
        )
        menuWidgets.AppendItem(
            makeMenuItem(
                parent=menuWidgets, id=ID_docTree_plugin_UVPD, text="Open UVPD processing window...", bitmap=None
            )
        )
        menuWidgets.AppendItem(
            makeMenuItem(parent=menuWidgets, id=ID_docTree_plugin_MSMS, text="Open MS/MS window...", bitmap=None)
        )
        menu_widget_overlay_viewer = makeMenuItem(
            parent=menuWidgets, text="Open overlay window...\tShift+O", bitmap=None
        )
        menuWidgets.AppendItem(menu_widget_overlay_viewer)

        self.mainMenubar.Append(menuWidgets, "&Widgets")

        # CONFIG
        menuConfig = wx.Menu()
        menuConfig.AppendItem(
            makeMenuItem(
                parent=menuConfig,
                id=ID_saveConfig,
                text="Export configuration XML file (default location)\tCtrl+S",
                bitmap=self.icons.iconsLib["export_config_16"],
            )
        )
        menuConfig.AppendItem(
            makeMenuItem(
                parent=menuConfig,
                id=ID_saveAsConfig,
                text="Export configuration XML file as...\tCtrl+Shift+S",
                bitmap=None,
            )
        )
        menuConfig.AppendSeparator()
        menuConfig.AppendItem(
            makeMenuItem(
                parent=menuConfig,
                id=ID_openConfig,
                text="Import configuration XML file (default location)\tCtrl+Shift+O",
                bitmap=self.icons.iconsLib["import_config_16"],
            )
        )
        menuConfig.AppendItem(
            makeMenuItem(
                parent=menuConfig, id=ID_openAsConfig, text="Import configuration XML file from...", bitmap=None
            )
        )
        menuConfig.AppendSeparator()
        self.loadCCSAtStart = menuConfig.Append(ID_importAtStart_CCS, "Load at start", kind=wx.ITEM_CHECK)
        self.loadCCSAtStart.Check(self.config.loadCCSAtStart)
        menuConfig.AppendItem(
            makeMenuItem(
                parent=menuConfig,
                id=ID_openCCScalibrationDatabse,
                text="Import CCS calibration database\tCtrl+Alt+C",
                bitmap=self.icons.iconsLib["filelist_16"],
            )
        )
        menuConfig.AppendItem(
            makeMenuItem(
                parent=menuConfig,
                id=ID_selectCalibrant,
                text="Show CCS calibrants\tCtrl+Shift+C",
                bitmap=self.icons.iconsLib["ccs_table_16"],
            )
        )
        menuConfig.AppendSeparator()
        menuConfig.AppendItem(
            makeMenuItem(
                parent=menuConfig, id=ID_importExportSettings_peaklist, text="Import parameters: Peaklist", bitmap=None
            )
        )
        menuConfig.AppendItem(
            makeMenuItem(
                parent=menuConfig, id=ID_importExportSettings_image, text="Export parameters: Image", bitmap=None
            )
        )
        menuConfig.AppendItem(
            makeMenuItem(
                parent=menuConfig, id=ID_importExportSettings_file, text="Export parameters: File", bitmap=None
            )
        )
        menuConfig.AppendSeparator()
        self.checkDriftscopeAtStart = menuConfig.Append(
            ID_checkAtStart_Driftscope, "Look for DriftScope at start", kind=wx.ITEM_CHECK
        )
        self.checkDriftscopeAtStart.Check(self.config.checkForDriftscopeAtStart)
        menuConfig.AppendItem(
            makeMenuItem(
                parent=menuConfig,
                id=ID_check_Driftscope,
                text="Check DriftScope path",
                bitmap=self.icons.iconsLib["check_online_16"],
            )
        )
        menuConfig.AppendItem(
            makeMenuItem(
                parent=menuConfig,
                id=ID_setDriftScopeDir,
                text="Set DriftScope path...",
                bitmap=self.icons.iconsLib["driftscope_16"],
            )
        )
        self.mainMenubar.Append(menuConfig, "&Configuration")

        otherSoftwareMenu = wx.Menu()
        otherSoftwareMenu.AppendItem(
            makeMenuItem(
                parent=otherSoftwareMenu,
                id=ID_help_UniDecInfo,
                text="About UniDec engine...",
                bitmap=self.icons.iconsLib["process_unidec_16"],
            )
        )
        #         otherSoftwareMenu.Append(ID_open1DIMSFile, 'About CIDER...')

        helpPagesMenu = wx.Menu()
        # helpPagesMenu.AppendItem(makeMenuItem(parent=helpPagesMenu, id=ID_help_page_gettingStarted,
        #                                      text='Learn more: Getting started\tF1+0',
        #                                      bitmap=self.icons.iconsLib['blank_16']))
        # helpPagesMenu.AppendSeparator()
        helpPagesMenu.AppendItem(
            makeMenuItem(
                parent=helpPagesMenu,
                id=ID_help_page_dataLoading,
                text="Learn more: Loading data",
                bitmap=self.icons.iconsLib["open16"],
            )
        )

        helpPagesMenu.AppendItem(
            makeMenuItem(
                parent=helpPagesMenu,
                id=ID_help_page_dataExtraction,
                text="Learn more: Data extraction",
                bitmap=self.icons.iconsLib["extract16"],
            )
        )

        helpPagesMenu.AppendItem(
            makeMenuItem(
                parent=helpPagesMenu,
                id=ID_help_page_UniDec,
                text="Learn more: MS deconvolution using UniDec",
                bitmap=self.icons.iconsLib["process_unidec_16"],
            )
        )

        helpPagesMenu.AppendItem(
            makeMenuItem(
                parent=helpPagesMenu,
                id=ID_help_page_ORIGAMI,
                text="Learn more: ORIGAMI-MS (Automated CIU)",
                bitmap=self.icons.iconsLib["origamiLogoDark16"],
            )
        )

        helpPagesMenu.AppendItem(
            makeMenuItem(
                parent=helpPagesMenu,
                id=ID_help_page_multipleFiles,
                text="Learn more: Multiple files (Manual CIU)",
                bitmap=self.icons.iconsLib["panel_mll__16"],
            )
        )

        helpPagesMenu.AppendItem(
            makeMenuItem(
                parent=helpPagesMenu,
                id=ID_help_page_overlay,
                text="Learn more: Overlay documents",
                bitmap=self.icons.iconsLib["overlay16"],
            )
        )

        #         helpPagesMenu.AppendItem(makeMenuItem(parent=helpPagesMenu, id=ID_help_page_linearDT,
        #                                               text='Learn more: Linear Drift-time analysis',
        #                                               bitmap=self.icons.iconsLib['panel_dt_16']))
        #
        #         helpPagesMenu.AppendItem(makeMenuItem(parent=helpPagesMenu, id=ID_help_page_CCScalibration,
        #                                               text='Learn more: CCS calibration',
        #                                               bitmap=self.icons.iconsLib['panel_ccs_16']))

        helpPagesMenu.AppendItem(
            makeMenuItem(
                parent=helpPagesMenu,
                id=ID_help_page_Interactive,
                text="Learn more: Interactive output",
                bitmap=self.icons.iconsLib["bokehLogo_16"],
            )
        )

        helpPagesMenu.AppendItem(
            makeMenuItem(
                parent=helpPagesMenu,
                id=ID_help_page_annotatingMassSpectra,
                text="Learn more: Annotating mass spectra",
                bitmap=self.icons.iconsLib["annotate16"],
            )
        )

        helpPagesMenu.AppendItem(
            makeMenuItem(
                parent=helpPagesMenu,
                id=ID_help_page_OtherData,
                text="Learn more: Annotated data",
                bitmap=self.icons.iconsLib["blank_16"],
            )
        )

        # HELP MENU
        menuHelp = wx.Menu()
        menuHelp.AppendMenu(wx.ID_ANY, "Help pages...", helpPagesMenu)
        menuHelp.AppendSeparator()
        menuHelp.AppendItem(
            makeMenuItem(
                parent=menuHelp, id=ID_helpGuide, text="Open User Guide...", bitmap=self.icons.iconsLib["web_access_16"]
            )
        )
        menuHelp.AppendItem(
            makeMenuItem(
                parent=menuHelp,
                id=ID_helpYoutube,
                text="Check out video guides... (online)",
                bitmap=self.icons.iconsLib["youtube16"],
                help_text=self.help.link_youtube,
            )
        )
        menuHelp.AppendItem(
            makeMenuItem(
                parent=menuHelp,
                id=ID_helpNewVersion,
                text="Check for updates... (online)",
                bitmap=self.icons.iconsLib["github16"],
            )
        )
        menuHelp.AppendItem(
            makeMenuItem(
                parent=menuHelp, id=ID_helpCite, text="Paper to cite... (online)", bitmap=self.icons.iconsLib["cite_16"]
            )
        )
        menuHelp.AppendSeparator()
        menuHelp.AppendMenu(wx.ID_ANY, "About other software...", otherSoftwareMenu)
        menuHelp.AppendSeparator()
        menuHelp.AppendItem(
            makeMenuItem(
                parent=menuHelp,
                id=ID_helpNewFeatures,
                text="Request new features... (web)",
                bitmap=self.icons.iconsLib["request_16"],
            )
        )
        menuHelp.AppendItem(
            makeMenuItem(
                parent=menuHelp, id=ID_helpReportBugs, text="Report bugs... (web)", bitmap=self.icons.iconsLib["bug_16"]
            )
        )
        menuHelp.AppendSeparator()
        menuHelp.AppendItem(
            makeMenuItem(
                parent=menuHelp,
                id=ID_CHECK_VERSION,
                text="Check for newest version...",
                bitmap=self.icons.iconsLib["check_online_16"],
            )
        )
        menuHelp.AppendItem(
            makeMenuItem(
                parent=menuHelp,
                id=ID_WHATS_NEW,
                text="Whats new in v{}".format(self.config.version),
                bitmap=self.icons.iconsLib["blank_16"],
            )
        )
        menuHelp.AppendSeparator()
        menuHelp.AppendItem(
            makeMenuItem(
                parent=menuHelp,
                id=ID_SHOW_ABOUT,
                text="About ORIGAMI\tCtrl+Shift+A",
                bitmap=self.icons.iconsLib["origamiLogoDark16"],
            )
        )
        self.mainMenubar.Append(menuHelp, "&Help")
        self.SetMenuBar(self.mainMenubar)

        # Menu events
        self.Bind(wx.EVT_MENU_HIGHLIGHT_ALL, self.OnMenuHighlight)

        # Bind functions to menu
        # HELP MENU
        self.Bind(wx.EVT_MENU, self.onHelpAbout, id=ID_SHOW_ABOUT)
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
        self.Bind(wx.EVT_MENU, self.presenter.onRebootWindow, id=ID_RESET_ORIGAMI)

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
        self.Bind(wx.EVT_MENU, self.data_handling.on_open_text_2D_fcn, id=ID_load_text_2D)
        self.Bind(wx.EVT_MENU, self.data_handling.on_open_multiple_text_2D_fcn, id=ID_load_multiple_text_2D)

        self.Bind(wx.EVT_MENU, self.data_handling.on_open_MassLynx_raw_fcn, id=ID_load_origami_masslynx_raw)
        self.Bind(wx.EVT_MENU, self.data_handling.on_open_MassLynx_raw_fcn, id=ID_openIRRawFile)
        self.Bind(
            wx.EVT_MENU, self.data_handling.on_open_multiple_MassLynx_raw_fcn, id=ID_load_multiple_origami_masslynx_raw
        )

        self.Bind(wx.EVT_MENU, self.data_handling.on_open_document_fcn, id=ID_openDocument)
        self.Bind(wx.EVT_MENU, self.panelDocuments.documents.on_save_document, id=ID_saveDocument)
        self.Bind(wx.EVT_MENU, self.data_handling.on_save_all_documents_fcn, id=ID_saveAllDocuments)
        self.Bind(wx.EVT_MENU, self.data_handling.on_open_MassLynx_raw_MS_only_fcn, id=ID_load_masslynx_raw_ms_only)
        self.Bind(wx.EVT_MENU, self.data_handling.on_open_single_text_MS_fcn, id=ID_load_text_MS)
        self.Bind(wx.EVT_MENU, self.data_handling.on_open_single_clipboard_MS, id=ID_load_clipboard_spectrum)
        self.Bind(wx.EVT_MENU, self.on_close, id=ID_quit)
        self.Bind(wx.EVT_MENU, self.on_add_blank_document_interactive, id=ID_addNewInteractiveDoc)
        self.Bind(wx.EVT_MENU, self.on_add_blank_document_manual, id=ID_addNewManualDoc)
        self.Bind(wx.EVT_MENU, self.on_add_blank_document_overlay, id=ID_addNewOverlayDoc)
        self.Bind(wx.EVT_TOOL, self.on_open_multiple_files, id=ID_load_multiple_masslynx_raw)
        self.Bind(wx.EVT_TOOL, self.data_handling.on_open_MGF_file_fcn, id=ID_fileMenu_MGF)
        self.Bind(wx.EVT_TOOL, self.data_handling.on_open_mzML_file_fcn, id=ID_fileMenu_mzML)
        self.Bind(wx.EVT_TOOL, self.data_handling.on_open_thermo_file_fcn, id=ID_fileMenu_thermoRAW)

        # PLOT
        self.Bind(wx.EVT_MENU, self.onPlotParameters, id=ID_extraSettings_general_plot)
        self.Bind(wx.EVT_MENU, self.onPlotParameters, id=ID_extraSettings_plot1D)
        self.Bind(wx.EVT_MENU, self.onPlotParameters, id=ID_extraSettings_plot2D)
        self.Bind(wx.EVT_MENU, self.onPlotParameters, id=ID_extraSettings_plot3D)
        self.Bind(wx.EVT_MENU, self.onPlotParameters, id=ID_extraSettings_legend)
        self.Bind(wx.EVT_MENU, self.onPlotParameters, id=ID_extraSettings_colorbar)
        self.Bind(wx.EVT_MENU, self.onPlotParameters, id=ID_extraSettings_rmsd)
        self.Bind(wx.EVT_MENU, self.onPlotParameters, id=ID_extraSettings_waterfall)
        self.Bind(wx.EVT_MENU, self.onPlotParameters, id=ID_extraSettings_violin)
        self.Bind(wx.EVT_MENU, self.onPlotParameters, id=ID_extraSettings_general)
        self.Bind(wx.EVT_MENU, self.updatePlots, id=ID_plots_showCursorGrid)

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
        self.Bind(wx.EVT_MENU, self.openSaveAsDlg, id=ID_saveAsInteractive)

        # UTILITIES
        self.Bind(wx.EVT_MENU, self.panelDocuments.documents.on_process_UVPD, id=ID_docTree_plugin_UVPD)
        self.Bind(wx.EVT_MENU, self.panelDocuments.documents.on_open_MSMS_viewer, id=ID_docTree_plugin_MSMS)
        self.Bind(wx.EVT_MENU, self.panelDocuments.documents.on_open_overlay_viewer, menu_widget_overlay_viewer)

        # CONFIG MENU
        self.Bind(wx.EVT_MENU, self.data_handling.on_export_config_fcn, id=ID_saveConfig)
        self.Bind(wx.EVT_MENU, self.data_handling.on_export_config_as_fcn, id=ID_saveAsConfig)
        self.Bind(wx.EVT_MENU, self.data_handling.on_import_config_fcn, id=ID_openConfig)
        self.Bind(wx.EVT_MENU, self.data_handling.on_import_config_as_fcn, id=ID_openAsConfig)
        self.Bind(wx.EVT_MENU, self.on_setup_driftscope, id=ID_setDriftScopeDir)
        self.Bind(wx.EVT_MENU, self.on_check_driftscope_path, id=ID_check_Driftscope)
        self.Bind(wx.EVT_MENU, self.onExportParameters, id=ID_importExportSettings_peaklist)
        self.Bind(wx.EVT_MENU, self.onExportParameters, id=ID_importExportSettings_image)
        self.Bind(wx.EVT_MENU, self.onExportParameters, id=ID_importExportSettings_file)
        self.Bind(wx.EVT_MENU, self.onCheckToggle, id=ID_checkAtStart_Driftscope)
        self.Bind(wx.EVT_MENU, self.onCheckToggle, id=ID_importAtStart_CCS)

        # VIEW MENU
        self.Bind(wx.EVT_MENU, self.on_toggle_panel, id=ID_window_all)
        self.Bind(wx.EVT_MENU, self.on_toggle_panel, self.documentsPage)
        self.Bind(wx.EVT_MENU, self.on_toggle_panel, self.mzTable)
        self.Bind(wx.EVT_MENU, self.on_toggle_panel, self.textTable)
        self.Bind(wx.EVT_MENU, self.on_toggle_panel, self.multipleMLTable)
        self.Bind(wx.EVT_MENU, self.onWindowMaximize, id=ID_windowMaximize)
        self.Bind(wx.EVT_MENU, self.onWindowIconize, id=ID_windowMinimize)
        self.Bind(wx.EVT_MENU, self.onWindowFullscreen, id=ID_windowFullscreen)
        self.Bind(wx.EVT_MENU, self.panelPlots.on_clear_all_plots, id=ID_clearAllPlots)
        self.Bind(wx.EVT_MENU, self.on_open_compare_MS_window, id=ID_docTree_compareMS)
        self.SetMenuBar(self.mainMenubar)

    def on_customise_annotation_plot_parameters(self, evt):
        from gui_elements.dialog_customise_user_annotations import DialogCustomiseUserAnnotations

        dlg = DialogCustomiseUserAnnotations(self, config=self.config)
        dlg.ShowModal()

    def on_customise_unidec_plot_parameters(self, evt):
        from widgets.UniDec.dialog_customise_unidec_visuals import DialogCustomiseUniDecVisuals

        dlg = DialogCustomiseUniDecVisuals(self, self.config, self.icons)
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

    def on_open_compare_MS_window(self, evt):
        self.panelDocuments.documents.onCompareMS(None)

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

        link = self.config.links[links[evtID]]

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
            newVersion = get_latest_version(link=self.config.links["newVersion"])
            update = compare_versions(newVersion, self.config.version)
            if not update:
                try:
                    if evt.GetId() == ID_CHECK_VERSION:
                        DialogBox(
                            exceptionTitle="ORIGAMI",
                            exceptionMsg="You are using the most up to date version {}.".format(self.config.version),
                            type="Info",
                        )
                except Exception:
                    pass
            else:
                webpage = get_latest_version(get_webpage=True)
                wx.Bell()
                message = "Version {} is now available for download.\nYou are currently using version {}.".format(
                    newVersion, self.config.version
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
            webbrowser.open(self.config.links["guide"], autoraise=1)
        except Exception:
            pass

    def on_open_HTML_guide(self, evt):
        from gui_elements.panel_htmlViewer import panelHTMLViewer
        from help_documentation import HTMLHelp as htmlPages

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
            htmlViewer = panelHTMLViewer(self, self.config, **kwargs)
            htmlViewer.Show()
        else:
            try:
                self.presenter.onThreading(
                    None, ("Opening local documentation in your browser...", 4), action="updateStatusbar"
                )
                webbrowser.open(link, autoraise=1)
            except Exception:
                pass

    def onCheckToggle(self, evt):
        evtID = evt.GetId()

        if evtID == ID_checkAtStart_Driftscope:
            check_value = not self.config.checkForDriftscopeAtStart
            self.config.checkForDriftscopeAtStart = check_value
            self.checkDriftscopeAtStart.Check(check_value)

        if evtID == ID_importAtStart_CCS:
            check_value = not self.config.loadCCSAtStart
            self.config.loadCCSAtStart = check_value
            self.loadCCSAtStart.Check(check_value)

    def OnMenuHighlight(self, evt):
        # Show how to get menu item info from this event handler
        itemID = evt.GetId()
        try:
            msg = self.GetMenuBar().FindItemById(itemID).GetHelp()
            self.SetStatusText(msg, number=4)
        except Exception:
            self.SetStatusText("", number=4)

    def onWindowMaximize(self, evt):
        """Maximize app."""
        self.Maximize()

    def onWindowIconize(self, evt):
        """Iconize app."""
        self.Iconize()

    def onWindowFullscreen(self, evt):
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
        ctrlkeys = [
            ["I", self.panelDocuments.documents.onOpenDocInfo, wx.ACCEL_CTRL],
            ["W", self.data_handling.on_open_multiple_text_2D_fcn, wx.ACCEL_CTRL],
            ["Z", self.openSaveAsDlg, wx.ACCEL_SHIFT],
            ["G", self.presenter.on_open_directory, wx.ACCEL_CTRL],
        ]
        keyIDs = [wx.NewId() for item in ctrlkeys]
        ctrllist = []
        for i, k in enumerate(ctrlkeys):
            self.Bind(wx.EVT_MENU, k[1], id=keyIDs[i])
            ctrllist.append((k[2], ord(k[0]), keyIDs[i]))

        # Add more shortcuts with known IDs
        extraKeys = [
            # ["Q", self.presenter.on_overlay_2D, wx.ACCEL_ALT, ID_overlayMZfromList],
            # ["W", self.presenter.on_overlay_2D, wx.ACCEL_ALT, ID_overlayTextFromList],
            ["S", self.panelDocuments.documents.on_show_plot, wx.ACCEL_ALT, ID_showPlotDocument],
            ["P", self.panelDocuments.documents.onProcess, wx.ACCEL_ALT, ID_process2DDocument],
            ["R", self.panelDocuments.documents.onRenameItem, wx.ACCEL_ALT, ID_renameItem],
            ["X", self.panelDocuments.documents.on_show_plot, wx.ACCEL_ALT, ID_showPlotMSDocument],
            ["Z", self.panelDocuments.documents.on_change_charge_state, wx.ACCEL_ALT, ID_assignChargeState],
            ["V", self.panelDocuments.documents.onSaveCSV, wx.ACCEL_ALT, ID_saveDataCSVDocument],
        ]

        for item in extraKeys:
            self.Bind(wx.EVT_MENU, item[1], id=item[3])
            ctrllist.append((item[2], ord(item[0]), item[3]))

        self.SetAcceleratorTable(wx.AcceleratorTable(ctrllist))
        pass

    def on_open_source_menu(self, evt):
        menu = wx.Menu()
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_fileMenu_MGF,
                text="Open Mascot Generic Format file (.mgf) [MS/MS]",
                bitmap=self.icons.iconsLib["blank_16"],
            )
        )
        menu.AppendItem(
            makeMenuItem(
                parent=menu,
                id=ID_fileMenu_mzML,
                text="Open mzML (.mzML) [MS/MS]",
                bitmap=self.icons.iconsLib["blank_16"],
            )
        )
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def make_toolbar(self):

        # Bind events
        #         self.Bind(wx.EVT_TOOL, self.presenter.onOrigamiRawDirectory, id=ID_load_origami_masslynx_raw)
        #         self.Bind(wx.EVT_TOOL, self.data_handling.on_open_text_2D_fcn, id=ID_load_text_2D)
        #         self.Bind(wx.EVT_TOOL, self.presenter.onOrigamiRawDirectory, id=ID_load_masslynx_raw)
        self.Bind(wx.EVT_TOOL, self.on_open_source_menu, id=ID_mainPanel_openSourceFiles)

        # Create toolbar
        self.mainToolbar_horizontal = self.CreateToolBar(wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT)
        self.mainToolbar_horizontal.SetToolBitmapSize((12, 12))

        self.mainToolbar_horizontal.AddLabelTool(
            ID_openDocument, "", self.icons.iconsLib["open_project_16"], shortHelp="Open project document..."
        )
        self.mainToolbar_horizontal.AddLabelTool(
            ID_saveDocument, "", self.icons.iconsLib["save16"], shortHelp="Save project document..."
        )
        self.mainToolbar_horizontal.AddSeparator()
        self.mainToolbar_horizontal.AddLabelTool(
            ID_saveConfig, "", self.icons.iconsLib["export_config_16"], shortHelp="Export configuration file"
        )
        self.mainToolbar_horizontal.AddSeparator()
        self.mainToolbar_horizontal.AddLabelTool(
            ID_load_origami_masslynx_raw,
            "",
            self.icons.iconsLib["open_origami_16"],
            shortHelp="Open MassLynx file (.raw)",
        )
        self.mainToolbar_horizontal.AddLabelTool(
            ID_load_origami_masslynx_raw,
            "",
            self.icons.iconsLib["open_masslynx_16"],
            shortHelp="Open MassLynx file (IM-MS)",
        )
        self.mainToolbar_horizontal.AddLabelTool(
            ID_load_multiple_masslynx_raw,
            "",
            self.icons.iconsLib["open_masslynxMany_16"],
            shortHelp="Open multiple MassLynx files (e.g. CIU/SID)",
        )
        self.mainToolbar_horizontal.AddSeparator()
        self.mainToolbar_horizontal.AddLabelTool(
            ID_load_text_2D, "", self.icons.iconsLib["open_text_16"], shortHelp="Open text files (2D)"
        )
        self.mainToolbar_horizontal.AddLabelTool(
            ID_load_multiple_text_2D,
            "",
            self.icons.iconsLib["open_textMany_16"],
            shortHelp="Open multiple text files (2D)",
        )
        self.mainToolbar_horizontal.AddSeparator()
        self.mainToolbar_horizontal.AddLabelTool(
            ID_mainPanel_openSourceFiles, "", self.icons.iconsLib["ms16"], shortHelp="Open MS/MS files..."
        )
        self.mainToolbar_horizontal.AddSeparator()
        self.mainToolbar_horizontal.AddCheckTool(
            ID_window_documentList, "", self.icons.iconsLib["panel_doc_16"], shortHelp="Enable/Disable documents panel"
        )
        self.mainToolbar_horizontal.AddCheckTool(
            ID_window_ionList, "", self.icons.iconsLib["panel_ion_16"], shortHelp="Enable/Disable peak list panel"
        )
        self.mainToolbar_horizontal.AddCheckTool(
            ID_window_textList, "", self.icons.iconsLib["panel_text_16"], shortHelp="Enable/Disable text list panel"
        )
        self.mainToolbar_horizontal.AddCheckTool(
            ID_window_multipleMLList, "", self.icons.iconsLib["panel_mll__16"], shortHelp="Enable/Disable files panel"
        )
        self.mainToolbar_horizontal.AddSeparator()
        self.mainToolbar_horizontal.AddLabelTool(
            ID_extraSettings_general_plot,
            "",
            self.icons.iconsLib["panel_plot_general_16"],
            shortHelp="Settings: General plot",
        )
        self.mainToolbar_horizontal.AddLabelTool(
            ID_extraSettings_plot1D, "", self.icons.iconsLib["panel_plot1D_16"], shortHelp="Settings: Plot 1D panel"
        )
        self.mainToolbar_horizontal.AddLabelTool(
            ID_extraSettings_plot2D, "", self.icons.iconsLib["panel_plot2D_16"], shortHelp="Settings: Plot 2D panel"
        )
        self.mainToolbar_horizontal.AddLabelTool(
            ID_extraSettings_plot3D, "", self.icons.iconsLib["panel_plot3D_16"], shortHelp="Settings: Plot 3D panel"
        )
        self.mainToolbar_horizontal.AddLabelTool(
            ID_extraSettings_colorbar,
            "",
            self.icons.iconsLib["panel_colorbar_16"],
            shortHelp="Settings: Colorbar panel",
        )
        self.mainToolbar_horizontal.AddLabelTool(
            ID_extraSettings_legend, "", self.icons.iconsLib["panel_legend_16"], shortHelp="Settings: Legend panel"
        )
        self.mainToolbar_horizontal.AddLabelTool(
            ID_extraSettings_rmsd, "", self.icons.iconsLib["panel_rmsd_16"], shortHelp="Settings: RMSD panel"
        )
        self.mainToolbar_horizontal.AddLabelTool(
            ID_extraSettings_waterfall,
            "",
            self.icons.iconsLib["panel_waterfall_16"],
            shortHelp="Settings: Waterfall panel",
        )
        self.mainToolbar_horizontal.AddLabelTool(
            ID_extraSettings_violin, "", self.icons.iconsLib["panel_violin_16"], shortHelp="Settings: Violin panel"
        )
        self.mainToolbar_horizontal.AddLabelTool(
            ID_extraSettings_general, "", self.icons.iconsLib["panel_general2_16"], shortHelp="Settings: Extra panel"
        )
        self.mainToolbar_horizontal.AddSeparator()
        self.mainToolbar_horizontal.AddLabelTool(
            ID_saveAsInteractive, "", self.icons.iconsLib["bokehLogo_16"], shortHelp="Open interactive output panel"
        )

        # Actually realise the toolbar
        self.mainToolbar_horizontal.Realize()

    def on_toggle_panel(self, evt, check=None):

        if isinstance(evt, int):
            evtID = evt
        elif isinstance(evt, str):
            if evt == "document":
                evtID = ID_window_documentList
            elif evt == "ion":
                evtID = ID_window_ionList
            elif evt == "text":
                evtID = ID_window_textList
            elif evt == "mass_spectra":
                evtID = ID_window_multipleMLList

        elif evt is not None:
            evtID = evt.GetId()
        else:
            evtID = None

        if evtID is not None:
            if evtID == ID_window_documentList:
                if not self.panelDocuments.IsShown() or not self.documentsPage.IsChecked():
                    self._mgr.GetPane(self.panelDocuments).Show()
                    self.config._windowSettings["Documents"]["show"] = True
                else:
                    self._mgr.GetPane(self.panelDocuments).Hide()
                    self.config._windowSettings["Documents"]["show"] = False
                self.documentsPage.Check(self.config._windowSettings["Documents"]["show"])
                self.on_find_toggle_by_id(find_id=evtID, check=self.config._windowSettings["Documents"]["show"])
            elif evtID == ID_window_ionList:
                if not self.panelMultipleIons.IsShown() or check or not self.mzTable.IsChecked():
                    self._mgr.GetPane(self.panelMultipleIons).Show()
                    self.config._windowSettings["Peak list"]["show"] = True
                else:
                    self._mgr.GetPane(self.panelMultipleIons).Hide()
                    self.config._windowSettings["Peak list"]["show"] = False
                self.mzTable.Check(self.config._windowSettings["Peak list"]["show"])
                self.on_find_toggle_by_id(find_id=evtID, check=self.config._windowSettings["Peak list"]["show"])
            elif evtID == ID_window_multipleMLList:
                if not self.panelMML.IsShown() or check or not self.multipleMLTable.IsChecked():
                    self._mgr.GetPane(self.panelMML).Show()
                    self.config._windowSettings["Multiple files"]["show"] = True
                else:
                    self._mgr.GetPane(self.panelMML).Hide()
                    self.config._windowSettings["Multiple files"]["show"] = False
                self.multipleMLTable.Check(self.config._windowSettings["Multiple files"]["show"])
                self.on_find_toggle_by_id(find_id=evtID, check=self.config._windowSettings["Multiple files"]["show"])
            elif evtID == ID_window_textList:
                if not self.panelMultipleText.IsShown() or check or not self.textTable.IsChecked():
                    self._mgr.GetPane(self.panelMultipleText).Show()
                    self.config._windowSettings["Text files"]["show"] = True
                else:
                    self._mgr.GetPane(self.panelMultipleText).Hide()
                    self.config._windowSettings["Text files"]["show"] = False
                self.textTable.Check(self.config._windowSettings["Text files"]["show"])
                self.on_find_toggle_by_id(find_id=evtID, check=self.config._windowSettings["Text files"]["show"])
            elif evtID == ID_window_all:
                for key in self.config._windowSettings:
                    self.config._windowSettings[key]["show"] = True

                self.on_find_toggle_by_id(check_all=True)

                for panel in [self.panelDocuments, self.panelMML, self.panelMultipleIons, self.panelMultipleText]:
                    self._mgr.GetPane(panel).Show()

                self.documentsPage.Check(self.config._windowSettings["Documents"]["show"])
                self.mzTable.Check(self.config._windowSettings["Peak list"]["show"])
                self.textTable.Check(self.config._windowSettings["Text files"]["show"])
                self.multipleMLTable.Check(self.config._windowSettings["Multiple files"]["show"])

        # Checking at start of program
        else:
            if not self.panelDocuments.IsShown():
                self.config._windowSettings["Documents"]["show"] = False
            if not self.panelMML.IsShown():
                self.config._windowSettings["Multiple files"]["show"] = False
            if not self.panelMultipleIons.IsShown():
                self.config._windowSettings["Peak list"]["show"] = False
            if not self.panelMultipleText.IsShown():
                self.config._windowSettings["Text files"]["show"] = False

            self.documentsPage.Check(self.config._windowSettings["Documents"]["show"])
            self.mzTable.Check(self.config._windowSettings["Peak list"]["show"])
            self.textTable.Check(self.config._windowSettings["Text files"]["show"])
            self.multipleMLTable.Check(self.config._windowSettings["Multiple files"]["show"])

        self._mgr.Update()

    def on_find_toggle_by_id(self, find_id=None, check=None, check_all=False):
        """
        Find toggle item by id in either horizontal/vertiacal toolbar
        """
        idList = [
            ID_window_documentList,
            ID_window_controls,
            ID_window_ionList,
            ID_window_multipleMLList,
            ID_window_textList,
        ]
        for itemID in idList:
            if check_all:
                self.mainToolbar_horizontal.ToggleTool(toolId=itemID, toggle=True)
            elif itemID == find_id:
                self.mainToolbar_horizontal.ToggleTool(toolId=find_id, toggle=check)
        if find_id == ID_window_all:
            self.mainToolbar_horizontal.ToggleTool(toolId=id, toggle=True)

    def onCheckToggleID(self, panel):
        panelDict = {
            "Documents": ID_window_documentList,
            "Controls": ID_window_controls,
            "Multiple files": ID_window_multipleMLList,
            "Peak list": ID_window_ionList,
            "Text files": ID_window_textList,
        }
        return panelDict[panel]

    def on_close(self, evt, **kwargs):

        n_documents = len(self.presenter.documentsDict)
        if n_documents > 0 and not kwargs.get("ignore_warning", False):
            verb_form = {"1": "is"}.get(str(n_documents), "are")
            message = (
                "There {} {} document(s) open.\n".format(verb_form, len(self.presenter.documentsDict))
                + "Are you sure you want to continue?"
            )
            msgDialog = DialogNotifyOpenDocuments(self, presenter=self.presenter, message=message)
            dlg = msgDialog.ShowModal()

            if dlg == wx.ID_NO:
                print("Cancelled operation")
                return

        # Try saving configuration file
        try:
            path = os.path.join(self.config.cwd, "configOut.xml")
            self.config.saveConfigXML(path=path, evt=None)
        except Exception:
            print("Could not save configuration file")

        # Clear-up dictionary
        try:
            self.presenter.documentsDict.clear()
        except Exception as err:
            print(err)

        # Try unsubscribing events
        try:
            self.disable_publisher()
        except Exception as err:
            print(f"Could not disable publisher: {err}")

        # Try killing window manager
        try:
            self._mgr.UnInit()
        except Exception as err:
            print(f"Could not uninitilize window manager: {err}")

        # Clear-up temporary data directory
        try:
            if self.config.temporary_data is not None:
                clean_directory(self.config.temporary_data)
                print("Cleared {} from temporary files.".format(self.config.temporary_data))
        except Exception as err:
            print(err)

        # Aggressive way to kill the ORIGAMI process (grrr)
        if not kwargs.get("clean_exit", False):
            try:
                p = psutil.Process(self.config._processID)
                p.terminate()
            except Exception as err:
                print(err)

        self.Destroy()

    def disable_publisher(self):
        """ Unsubscribe from all events """
        pub.unsubAll()

    def on_distance(self, startX):
        # Simple way of setting the start point
        self.startX = startX

    def on_motion(self, xpos, ypos, plotname):
        """
        Triggered by pubsub from plot windows. Reports text in Status Bar.
        :param xpos: x position fed from event
        :param ypos: y position fed from event
        :return: None
        """

        self.plot_name = plotname

        if xpos is not None and ypos is not None:
            # If measuring distance, additional fields are used to help user
            # make observations
            if self.startX is not None:
                delta = np.absolute(self.startX - xpos)
                charge = np.round(1.0 / delta, 1)
                mass = (xpos + charge) * charge
                # If inside a plot area with MS, give out charge state
                if self.mode == "Measure" and self.panelPlots.currentPage in ["MS", "DT/MS"]:
                    self.SetStatusText(
                        f"m/z={xpos:.2f} int={ypos:.2f} Δm/z={delta:.2f} z={charge:.1f} mw={mass:.1f}", number=0
                    )
                else:
                    if self.panelPlots.currentPage in ["MS"]:
                        self.SetStatusText("m/z={:.4f} int={:.4f} Δm/z={:.2f}".format(xpos, ypos, delta), number=0)
                    elif self.panelPlots.currentPage in ["DT/MS"]:
                        self.SetStatusText("m/z={:.4f} dt={:.4f} Δm/z={:.2f}".format(xpos, ypos, delta), number=0)
                    elif self.panelPlots.currentPage in ["RT"]:
                        self.SetStatusText("scan={:.0f} int={:.4f} Δscans={:.2f}".format(xpos, ypos, delta), number=0)
                    elif self.panelPlots.currentPage in ["1D"]:
                        self.SetStatusText("dt={:.2f} int={:.4f} Δdt={:.2f}".format(xpos, ypos, delta), number=0)
                    elif self.panelPlots.currentPage in ["2D"]:
                        self.SetStatusText("x={:.4f} dt={:.4f} Δx={:.2f}".format(xpos, ypos, delta), number=0)
                    else:
                        self.SetStatusText("x={:.4f} y={:.4f} Δx={:.2f}".format(xpos, ypos, delta), number=0)
            else:
                if self.panelPlots.currentPage in ["MS"]:
                    self.SetStatusText("m/z={:.4f} int={:.4f}".format(xpos, ypos), number=0)
                elif self.panelPlots.currentPage in ["DT/MS"]:
                    if self.plot_data["DT/MS"] is not None and len(self.plot_scale["DT/MS"]) == 2:
                        try:
                            yIdx = int(ypos * self.plot_scale["DT/MS"][0]) - 1
                            xIdx = int(xpos * self.plot_scale["DT/MS"][1]) - 1
                            int_value = self.plot_data["DT/MS"][yIdx, xIdx]
                        except Exception:
                            int_value = 0.0
                        self.SetStatusText("m/z={:.4f} dt={:.4f} int={:.2f}".format(xpos, ypos, int_value), number=0)
                    else:
                        self.SetStatusText("m/z={:.4f} dt={:.4f}".format(xpos, ypos), number=0)
                elif self.panelPlots.currentPage in ["RT"]:
                    self.SetStatusText("scan={:.0f} int={:.2f}".format(xpos, ypos), number=0)
                elif self.panelPlots.currentPage in ["1D"]:
                    self.SetStatusText("dt={:.2f} int={:.2f}".format(xpos, ypos), number=0)
                elif self.panelPlots.currentPage in ["2D"]:
                    try:
                        if self.plot_data["2D"] is not None and len(self.plot_scale["2D"]) == 2:
                            try:
                                yIdx = int(ypos * self.plot_scale["2D"][0]) - 1
                                xIdx = int(xpos * self.plot_scale["2D"][1]) - 1
                                int_value = self.plot_data["2D"][yIdx, xIdx]
                            except Exception:
                                int_value = ""
                            self.SetStatusText("x={:.2f} dt={:.2f} int={:.2f}".format(xpos, ypos, int_value), number=0)
                        else:
                            self.SetStatusText("x={:.2f} dt={:.2f}".format(xpos, ypos), number=0)
                    except Exception:
                        self.SetStatusText("x={:.2f} dt={:.2f}".format(xpos, ypos), number=0)
                elif plotname == "zGrid":
                    self.SetStatusText("x={:.2f} charge={:.0f}".format(xpos, ypos), number=0)
                elif plotname == "mwDistribution":
                    self.SetStatusText("MW={:.2f} intensity={:.2f}".format(xpos, ypos), number=0)
                else:
                    self.SetStatusText("x={:.2f} y={:.2f}".format(xpos, ypos), number=0)

        pass

    def motion_range(self, dataOut):
        minx, maxx, miny, maxy = dataOut
        if self.mode == "Add data":
            self.SetStatusText(f"X={minx:.3f}:{maxx:.3f} | Y={miny:.3f}:{maxy:.3f}", number=4)
        else:
            self.SetStatusText("", number=4)

    def OnSize(self, evt):
        self.resized = True  # set dirty

    def OnIdle(self, evt):
        if self.resized:
            self.resized = False

    def onHelpAbout(self, evt):
        """Show About mMass panel."""
        from gui_elements.panelAbout import panelAbout

        about = panelAbout(self, self.presenter, "About ORIGAMI", self.config, self.icons)
        about.Centre()
        about.Show()
        about.SetFocus()

    def onAnnotatePanel(self, evt):
        pass

    def onPlotParameters(self, evt):
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

        if not self.panelParametersEdit.IsShown() or not self.config._windowSettings["Plot parameters"]["show"]:
            if self.config._windowSettings["Plot parameters"]["floating"]:
                self._mgr.GetPane(self.panelParametersEdit).Float()

            self._mgr.GetPane(self.panelParametersEdit).Show()
            self.config._windowSettings["Plot parameters"]["show"] = True
            self.panelParametersEdit.onSetPage(**kwargs)
            self._mgr.Update()
        else:
            args = ("An instance of this panel is already open - changing page to: %s" % kwargs["window"], 4)
            self.presenter.onThreading(evt, args, action="updateStatusbar")
            self.panelParametersEdit.onSetPage(**kwargs)
            return

    def onExportParameters(self, evt):
        if evt.GetId() == ID_importExportSettings_image:
            kwargs = {"window": "Image"}
        elif evt.GetId() == ID_importExportSettings_file:
            kwargs = {"window": "Files"}
        elif evt.GetId() == ID_importExportSettings_peaklist:
            kwargs = {"window": "Peaklist"}

        if self.config.importExportParamsWindow_on_off:
            args = ("An instance of this panel is already open - changing page to: %s" % kwargs["window"], 4)
            self.presenter.onThreading(evt, args, action="updateStatusbar")
            self.panelImportExportParameters.onSetPage(**kwargs)
            return

        self.SetStatusText("", 4)

        try:
            self.config.importExportParamsWindow_on_off = True
            self.panelImportExportParameters = panelExportSettings(
                self, self.presenter, self.config, self.icons, **kwargs
            )
            self.panelImportExportParameters.Show()
        except (ValueError, AttributeError, TypeError, KeyError) as e:
            self.config.importExportParamsWindow_on_off = False
            DialogBox(exceptionTitle="Failed to open panel", exceptionMsg=str(e), type="Error")
            return

    def onSequenceEditor(self, evt):
        from gui_elements.panel_sequenceAnalysis import panelSequenceAnalysis

        self.panelSequenceAnalysis = panelSequenceAnalysis(self, self.presenter, self.config, self.icons)
        self.panelSequenceAnalysis.Show()

    def openSaveAsDlg(self, evt):
        try:
            if self.config.interactiveParamsWindow_on_off:
                self.interactivePanel.onUpdateList()
                args = ("An instance of this panel is already open", 4)
                self.presenter.onThreading(evt, args, action="updateStatusbar")
                return
        except Exception:
            pass

        #         try:
        self.config.interactiveParamsWindow_on_off = True
        self.interactivePanel = panelInteractive(self, self.icons, self.presenter, self.config)
        self.interactivePanel.Show()

    #         except (ValueError, AttributeError, TypeError, KeyError, NameError) as e:
    #             self.config.interactiveParamsWindow_on_off = False
    #             DialogBox(exceptionTitle='Failed to open panel',
    #                    exceptionMsg=str(e),
    #                    type="Error")
    #             return

    def updateRecentFiles(self, path=None):
        """
        path = dictionary {'file_path': path, 'file_type': file type}
        """

        if path:
            if path in self.config.previousFiles:
                del self.config.previousFiles[self.config.previousFiles.index(path)]
            self.config.previousFiles.insert(0, path)
            # make sure only 10 items are present in the list
            while len(self.config.previousFiles) > 10:
                del self.config.previousFiles[-1]

        # clear menu
        for item in self.menuRecent.GetMenuItems():
            self.menuRecent.Delete(item.GetId())

        # populate menu
        for i, __ in enumerate(self.config.previousFiles):
            ID = eval("ID_documentRecent" + str(i))
            path = self.config.previousFiles[i]["file_path"]
            self.menuRecent.Insert(i, ID, path, "Open Document")
            self.Bind(wx.EVT_MENU, self.onDocumentRecent, id=ID)
            if not os.path.exists(path):
                self.menuRecent.Enable(ID, False)

        # append clear
        if len(self.config.previousFiles) > 0:
            self.menuRecent.AppendSeparator()

        self.menuRecent.Append(ID_fileMenu_clearRecent, "Clear Menu", "Clear recent items")
        self.Bind(wx.EVT_MENU, self.onDocumentClearRecent, id=ID_fileMenu_clearRecent)

        if self.config.autoSaveSettings:
            self.data_handling.on_export_config_fcn(None, False)

    def onDocumentClearRecent(self, evt):
        """Clear recent items."""

        self.config.previousFiles = []
        self.updateRecentFiles()

    def onDocumentRecent(self, evt):
        """Open recent document."""

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
        file_path = self.config.previousFiles[documentID]["file_path"]
        file_type = self.config.previousFiles[documentID]["file_type"]

        # open file
        if file_type == "pickle":
            self.data_handling.on_open_document_fcn(file_path=file_path, evt=None)
        elif file_type == "MassLynx":
            self.data_handling.on_open_MassLynx_raw_fcn(path=file_path, evt=ID_load_masslynx_raw)
        elif file_type == "ORIGAMI":
            self.data_handling.on_open_MassLynx_raw_fcn(path=file_path, evt=ID_load_origami_masslynx_raw)
        elif file_type == "Infrared":
            self.data_handling.on_open_MassLynx_raw_fcn(path=file_path, evt=ID_openIRRawFile)
        elif file_type == "Text":
            self.data_handling.on_add_text_2D(None, file_path)
        elif file_type == "Text_MS":
            self.data_handling.on_open_single_text_MS(path=file_path)

    def onOpenFile_DnD(self, file_path, file_extension):
        # open file
        if file_extension in [".pickle", ".pkl"]:
            self.data_handling.on_open_document_fcn(file_path=file_path, evt=None)
        elif file_extension == ".raw":
            self.data_handling.on_open_MassLynx_raw_fcn(path=file_path, evt=ID_load_origami_masslynx_raw)
        elif file_extension in [".txt", ".csv", ".tab"]:
            file_format = check_file_type(path=file_path)
            if file_format == "2D":
                self.data_handling.on_add_text_2D(None, file_path)
            else:
                self.data_handling.on_add_text_MS(path=file_path)

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
        if self.config.testing:
            return

        try:
            self.SetStatusText(msg, number=position)
            sleep(delay)
            self.SetStatusText("", number=position)
        except Exception:
            print(f"Statusbar update: {msg}")

    def updatePlots(self, evt):
        """
        build and update parameters in the zoom function
        """
        plot_parameters = {
            "grid_show": self.config._plots_grid_show,
            "grid_color": self.config._plots_grid_color,
            "grid_line_width": self.config._plots_grid_line_width,
            "extract_color": self.config._plots_extract_color,
            "extract_line_width": self.config._plots_extract_line_width,
            "extract_crossover_sensitivity_1D": self.config._plots_extract_crossover_1D,
            "extract_crossover_sensitivity_2D": self.config._plots_extract_crossover_2D,
            "zoom_color_vertical": self.config._plots_zoom_vertical_color,
            "zoom_color_horizontal": self.config._plots_zoom_horizontal_color,
            "zoom_color_box": self.config._plots_zoom_box_color,
            "zoom_line_width": self.config._plots_zoom_line_width,
            "zoom_crossover_sensitivity": self.config._plots_zoom_crossover,
        }
        pub.sendMessage("plot_parameters", plot_parameters=plot_parameters)

        if evt is not None:
            evt.Skip()

    def onEnableDisableThreading(self, evt):

        if self.config.threading:
            msg = (
                "Multi-threading is only an experimental feature for now! It might occasionally crash ORIGAMI,"
                + " in which case you will lose your processed data!"
            )
            DialogBox(exceptionTitle="Warning", exceptionMsg=msg, type="Warning")
        if evt is not None:
            evt.Skip()

    def on_setup_driftscope(self, evt):
        """
        This function sets the Driftscope directory
        """
        dlg = wx.DirDialog(
            self.view, r"Choose Driftscope path. Usually at C:\DriftScope\lib", style=wx.DD_DEFAULT_STYLE
        )
        try:
            if os.path.isdir(self.config.driftscopePath):
                dlg.SetPath(self.config.driftscopePath)
        except Exception:
            pass

        if dlg.ShowModal() == wx.ID_OK:
            if os.path.basename(dlg.GetPath()) == "lib":
                path = dlg.GetPath()
            elif os.path.basename(dlg.GetPath()) == "DriftScope":
                path = os.path.join(dlg.GetPath(), "lib")
            else:
                path = dlg.GetPath()

            self.config.driftscopePath = path

            self.onThreading(
                None, ("Driftscope path was set to {}".format(self.config.driftscopePath), 4), action="updateStatusbar"
            )

            # Check if driftscope exists
            if not os.path.isdir(self.config.driftscopePath):
                print("Could not find Driftscope path")
                msg = (
                    r"Could not localise Driftscope directory. Please setup path to Dritscope lib folder."
                    + r" It usually exists under C:\DriftScope\lib"
                )
                DialogBox(exceptionTitle="Could not find Driftscope", exceptionMsg=msg, type="Warning")

            if not os.path.isfile(self.config.driftscopePath + r"\imextract.exe"):
                print("Could not find imextract.exe")
                msg = (
                    r"Could not localise Driftscope imextract.exe program. Please setup path to Dritscope"
                    + r" lib folder. It usually exists under C:\DriftScope\lib"
                )
                DialogBox(exceptionTitle="Could not find Driftscope", exceptionMsg=msg, type="Warning")
        evt.Skip()

    def on_check_driftscope_path(self, evt=None):
        check = self.config.initilize_paths(return_check=True)
        if check:
            wx.Bell()
            DialogBox(
                exceptionTitle="DriftScope path looks good",
                exceptionMsg="Found DriftScope on your PC. You are good to go.",
                type="Info",
            )
            return


class DragAndDrop(wx.FileDropTarget):
    def __init__(self, window):
        """Constructor"""
        wx.FileDropTarget.__init__(self)
        self.window = window

    # ----------------------------------------------------------------------

    def OnDropFiles(self, x, y, filenames):
        """
        When files are dropped, write where they were dropped and then
        the file paths themselves
        """
        for filename in filenames:
            print("Opening {} file...".format(filename))
            __, file_extension = os.path.splitext(filename)
            if file_extension in [".raw", ".pickle", ".pkl", ".txt", ".csv", ".tab"]:
                try:
                    self.window.onOpenFile_DnD(filename, file_extension)
                except Exception:
                    print("Failed to open {}".format(filename))
                    continue
            else:
                print("Dropped file is not supported")
                continue
