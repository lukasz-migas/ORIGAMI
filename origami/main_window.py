"""Main frame module"""
# Standard library imports
import os
import time
import logging
import webbrowser
from typing import Optional
from functools import partial

# Third-party imports
import numpy as np
import psutil
import wx.aui
from pubsub import pub

# Local imports
from origami.ids import ID_helpCite
from origami.ids import ID_helpGuide
from origami.ids import ID_helpAuthor
from origami.ids import ID_helpGitHub
from origami.ids import ID_openConfig
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
from origami.ids import ID_fileMenu_mzML
from origami.ids import ID_saveMZDTImage
from origami.ids import ID_saveRMSDImage
from origami.ids import ID_saveRMSFImage
from origami.ids import ID_helpHTMLEditor
from origami.ids import ID_helpNewVersion
from origami.ids import ID_helpReportBugs
from origami.ids import ID_window_ionList
from origami.ids import ID_help_UniDecInfo
from origami.ids import ID_helpNewFeatures
from origami.ids import ID_selectCalibrant
from origami.ids import ID_window_controls
from origami.ids import ID_window_textList
from origami.ids import ID_help_page_UniDec
from origami.ids import ID_saveOverlayImage
from origami.ids import ID_help_page_ORIGAMI
from origami.ids import ID_help_page_overlay
from origami.ids import ID_importAtStart_CCS
from origami.ids import ID_extraSettings_rmsd
from origami.ids import ID_help_page_linearDT
from origami.ids import ID_saveWaterfallImage
from origami.ids import ID_docTree_plugin_MSMS
from origami.ids import ID_docTree_plugin_UVPD
from origami.ids import ID_fileMenu_openRecent
from origami.ids import ID_help_page_OtherData
from origami.ids import ID_saveRMSDmatrixImage
from origami.ids import ID_window_documentList
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
from origami.ids import ID_window_multipleMLList
from origami.ids import ID_extraSettings_colorbar
from origami.ids import ID_checkAtStart_Driftscope
from origami.ids import ID_extraSettings_waterfall
from origami.ids import ID_help_page_multipleFiles
from origami.ids import ID_annotPanel_otherSettings
from origami.ids import ID_help_page_CCScalibration
from origami.ids import ID_help_page_dataExtraction
from origami.ids import ID_help_page_gettingStarted
from origami.ids import ID_load_masslynx_raw_ms_only
from origami.ids import ID_openCCScalibrationDatabse
from origami.ids import ID_unidecPanel_otherSettings
from origami.ids import ID_extraSettings_general_plot
from origami.ids import ID_help_page_annotatingMassSpectra
from origami.ids import ID_load_multiple_origami_masslynx_raw
from origami.styles import make_menu_item
from origami.utils.path import clean_directory
from origami.panel_plots import PanelPlots
from origami.icons.assets import Icons
from origami.config.config import CONFIG
from origami.panel_peaklist import PanelPeaklist
from origami.panel_textlist import PanelTextlist
from origami.panel_multi_file import PanelMultiFile
from origami.config.environment import ENV
from origami.panel_document_tree import PanelDocumentTree
from origami.gui_elements.statusbar import Statusbar
from origami.handlers.data_handling import DataHandling
from origami.gui_elements.popup_toast import PopupToastManager
from origami.handlers.data_processing import DataProcessing
from origami.gui_elements.misc_dialogs import DialogBox
from origami.handlers.data_visualisation import DataVisualization
from origami.gui_elements.panel_plot_parameters import PanelVisualisationSettingsEditor
from origami.gui_elements.dialog_notify_open_documents import DialogNotifyOpenDocuments
from origami.widgets.interactive.panel_interactive_creator import PanelInteractiveCreator

logger = logging.getLogger(__name__)


class MainWindow(wx.Frame):
    """Main frame"""

    # attributes
    mode = None
    x_pos = None
    y_pos = None
    xy_start = None
    resized = False

    # ui elements
    menu_recent_files = None
    menubar = None
    toolbar = None
    statusbar = None
    toggle_document_page = None
    toggle_peaks_page = None
    toggle_text_page = None
    toggle_manual_page = None
    menu_config_check_driftscope = None
    menu_config_check_load_ccs_db = None
    panel_interactive_output = None

    def __init__(self, parent, icons, title: str):
        wx.Frame.__init__(self, None, title=title)

        # Extract size of screen
        self.display_size = wx.GetDisplaySize()
        self.SetDimensions(0, 0, self.display_size[0], self.display_size[1] - 50)
        self.icons = icons
        self._icons = Icons()
        self.presenter = parent

        self._timer = wx.Timer(self, wx.ID_ANY)

        self.plot_data = {}  # remove
        self.plot_scale = {}  # remove
        self.plot_name = None
        self.plot_id = None

        self._fullscreen = False

        file_drop_target = DragAndDrop(self)
        self.SetDropTarget(file_drop_target)

        icon = wx.EmptyIcon()
        icon.CopyFromBitmap(self.icons.iconsLib["origamiLogoDark16"])
        self.SetIcon(icon)

        # keep track of which windows are managed
        self._managed_windows = dict()
        self._n_managed_windows = 0

        CONFIG.startTime = time.strftime("%Y_%m_%d-%H-%M-%S", time.gmtime())

        # Bind commands to events
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_IDLE, self.on_idle)

        # Setup Notebook manager
        self.window_mgr = wx.aui.AuiManager(self)
        self.window_mgr.SetDockSizeConstraint(1, 1)

        # Load panels
        self.panelDocuments = PanelDocumentTree(self, CONFIG, self.icons, self.presenter)

        self.panelPlots = PanelPlots(self, self.presenter)
        self.panelMultipleText = PanelTextlist(self, self.icons, self.presenter)

        self.panelParametersEdit = PanelVisualisationSettingsEditor(self, self.presenter, window=None)

        # add handling, processing and visualisation pipelines
        self.data_processing = DataProcessing(self.presenter, self, CONFIG)
        self.data_handling = DataHandling(self.presenter, self, CONFIG)
        self.data_visualisation = DataVisualization(self.presenter, self, CONFIG)

        self.popup_mgr = PopupToastManager(self)

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

        # Load other parts
        self.window_mgr.Update()
        self.make_statusbar()
        self.make_menubar()
        self.make_shortcuts()
        self.SetSize(1920, 1080)

        # bind events
        self.Bind(wx.aui.EVT_AUI_PANE_CLOSE, self.on_closed_page)
        self.Bind(wx.aui.EVT_AUI_PANE_RESTORE, self.on_restored_page)

        # bind pub subscribers
        pub.subscribe(self.on_notify_info, "notify.message.info")
        pub.subscribe(self.on_notify_success, "notify.message.success")
        pub.subscribe(self.on_notify_warning, "notify.message.warning")
        pub.subscribe(self.on_notify_error, "notify.message.error")

        # Fire up a couple of events
        self.on_update_panel_config()
        self.on_toggle_panel(evt=None)
        self.on_toggle_panel_at_start()

        # when in development, move the app to another display
        if CONFIG.debug:
            self._move_app()

        # run action(s) delayed
        self.run_delayed(self._on_check_latest_version)

    @staticmethod
    def run_delayed(func, *args, delay: int = 3000, **kwargs):
        """Run function using a CallLater"""
        wx.CallLater(delay, func, *args, **kwargs)

    def on_notify(self, message: str, kind: str = "info", delay: int = 3000):
        """Notify user of some event"""

        wx.CallAfter(self.popup_mgr.show_popup, message, kind, delay)

    def on_notify_info(self, message: str):
        """Notify user of event using INFO style"""
        self.on_notify(message, "info")

    def on_notify_success(self, message: str):
        """Notify user of event using INFO style"""
        self.on_notify(message, "success")

    def on_notify_warning(self, message: str):
        """Notify user of event using INFO style"""
        self.on_notify(message, "warning")

    def on_notify_error(self, message: str):
        """Notify user of event using INFO style"""
        self.on_notify(message, "error")

    def _move_app(self):
        """Move application to another window"""
        try:
            current_w, current_h = self.GetPosition()
            screen_w, screen_h = current_w, current_h
            for idx in range(wx.Display.GetCount()):
                screen_w, screen_h, _, _ = wx.Display(idx).GetGeometry()
                if screen_w > current_w:
                    break

            self.SetPosition((screen_w, screen_h))
        except Exception:
            pass

    def create_panel(self, which: str, document_title: str):
        """Creates new instance of panel for particular document"""

        def _show_panel(_name, klass):
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
            _show_panel(name, PanelPeaklist)
        elif which == "files":
            title = f"Filelist: {document_title}"
            name = f"filelist; {document_title}"
            _show_panel(name, PanelMultiFile)

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

    @staticmethod
    def on_update_panel_config():
        """Update configuration for panel(s)"""
        CONFIG._windowSettings["Documents"]["id"] = ID_window_documentList

    def on_toggle_panel_at_start(self):
        """Toggle panels at the startup of the application"""
        panel_dict = {"Documents": ID_window_documentList, "Heatmap List": ID_window_textList}

        for panel in [self.panelDocuments, self.panelMultipleText]:  # , self.panelMML, self.panelMultipleIons, ]:
            if self.window_mgr.GetPane(panel).IsShown():
                self.on_find_toggle_by_id(find_id=panel_dict[self.window_mgr.GetPane(panel).caption], check=True)

    def on_closed_page(self, evt):
        """Keep track of which page was closed"""
        # Keep track of which window is closed
        panel_name = evt.GetPane().caption
        if panel_name in CONFIG._windowSettings:
            CONFIG._windowSettings[panel_name]["show"] = False

            # fire-up events
            try:
                evtID = self.on_get_toggle_id(panel=evt.GetPane().caption)
                self.on_toggle_panel(evt=evtID)
            except Exception:
                pass

    def on_restored_page(self, evt):
        """Keep track of which page was restored"""
        # Keep track of which window is restored
        CONFIG._windowSettings[evt.GetPane().caption]["show"] = True
        evt_id = self.on_get_toggle_id(panel=evt.GetPane().caption)
        self.on_toggle_panel(evt=evt_id)
        if evt is not None:
            evt.Skip()

    def make_statusbar(self):
        """Make statusbar"""
        self.statusbar = Statusbar(self, self._icons)
        self.SetStatusBar(self.statusbar)

    def make_menubar(self):
        """Create menubar in the main window"""
        self.menubar = wx.MenuBar()

        # setup recent sub-menu
        self.menu_recent_files = wx.Menu()
        self.on_update_recent_files()

        menu_tandem = wx.Menu()
        menu_tandem.Append(ID_fileMenu_MGF, "Open Mascot Generic Format file (.mgf) [MS/MS]")
        menu_tandem.Append(ID_fileMenu_mzML, "Open mzML (.mzML) [MS/MS]")

        menu_file = wx.Menu()
        menu_file.AppendMenu(ID_fileMenu_openRecent, "Open Recent", self.menu_recent_files)
        menu_file.AppendSeparator()

        menu_file_load_origami = make_menu_item(
            parent=menu_file, text="Open ORIGAMI Document (.origami)", bitmap=self._icons.open
        )
        menu_file.Append(menu_file_load_origami)

        menu_file_load_pickle = make_menu_item(
            parent=menu_file,
            evt_id=ID_openDocument,
            text="Open ORIGAMI Document file (.pickle) [LEGACY]",
            bitmap=self.icons.iconsLib["open_project_16"],
        )
        menu_file.Append(menu_file_load_pickle)
        menu_file.AppendSeparator()
        menu_file.Append(
            make_menu_item(
                parent=menu_file,
                evt_id=ID_load_masslynx_raw_ms_only,
                text="Open Waters file (.raw) [MS only]\tCtrl+Shift+M",
                bitmap=self._icons.micromass,
            )
        )
        menu_file_waters_imms = menu_file.Append(
            make_menu_item(parent=menu_file, text="Open Waters file (.raw) [IM-MS only]", bitmap=self._icons.micromass)
        )
        menu_open_origami = make_menu_item(
            parent=menu_file, text="Open Waters file (.raw) [ORIGAMI-MS; CIU]\tCtrl+R", bitmap=self._icons.micromass
        )
        menu_file.Append(menu_open_origami)

        menu_file.AppendSeparator()
        menu_open_thermo = make_menu_item(
            parent=menu_file, text="Open Thermo file (.RAW)\tCtrl+Shift+Y", bitmap=self._icons.thermo
        )
        menu_file.Append(menu_open_thermo)
        menu_file.AppendSeparator()
        menu_file_text_ms = make_menu_item(parent=menu_file, text="Open mass spectrum file(s) (.csv; .txt; .tab)")
        menu_file.Append(menu_file_text_ms)
        menu_file_text_heatmap = make_menu_item(
            parent=menu_file,
            text="Open heatmap file(s) (.csv; .txt; .tab)\tCtrl+Shift+T",
            bitmap=self.icons.iconsLib["open_textMany_16"],
        )
        menu_file.Append(menu_file_text_heatmap)
        menu_file.AppendSeparator()
        menu_file.AppendMenu(wx.ID_ANY, "Open MS/MS files...", menu_tandem)
        menu_file.AppendSeparator()
        menu_file_clipboard_ms = make_menu_item(
            parent=menu_file,
            #                 id=ID_load_clipboard_spectrum,
            text="Grab MS spectrum from clipboard\tCtrl+V",
            bitmap=self._icons.filelist,
        )
        menu_file.Append(menu_file_clipboard_ms)

        menu_file.AppendSeparator()
        menu_file.Append(
            make_menu_item(
                parent=menu_file, evt_id=ID_saveDocument, text="Save document as...", bitmap=self._icons.save
            )
        )
        menu_file.AppendSeparator()

        menu_file_exit = make_menu_item(parent=menu_file, text="Quit\tCtrl+Q", bitmap=self.icons.iconsLib["exit_16"])
        menu_file.Append(menu_file_exit)
        self.menubar.Append(menu_file, "&File")

        # PLOT
        menu_plot = wx.Menu()
        menu_plot.Append(
            make_menu_item(
                parent=menu_plot,
                evt_id=ID_extraSettings_general_plot,
                text="Settings: Plot &General",
                bitmap=self._icons.switch_on,
            )
        )

        menu_plot.Append(
            make_menu_item(
                parent=menu_plot, evt_id=ID_extraSettings_plot1D, text="Settings: Plot &1D", bitmap=self._icons.plot_1d
            )
        )

        menu_plot.Append(
            make_menu_item(
                parent=menu_plot,
                evt_id=ID_extraSettings_plot2D,
                text="Settings: Plot &2D",
                bitmap=self.icons.iconsLib["panel_plot2D_16"],
            )
        )

        menu_plot.Append(
            make_menu_item(
                parent=menu_plot,
                evt_id=ID_extraSettings_plot3D,
                text="Settings: Plot &3D",
                bitmap=self.icons.iconsLib["panel_plot3D_16"],
            )
        )

        menu_plot.Append(
            make_menu_item(
                parent=menu_plot,
                evt_id=ID_extraSettings_colorbar,
                text="Settings: &Colorbar",
                bitmap=self._icons.plot_colorbar,
            )
        )

        menu_plot.Append(
            make_menu_item(
                parent=menu_plot,
                evt_id=ID_extraSettings_legend,
                text="Settings: &Legend",
                bitmap=self._icons.plot_legend,
            )
        )

        menu_plot.Append(
            make_menu_item(
                parent=menu_plot,
                evt_id=ID_extraSettings_rmsd,
                text="Settings: &RMSD",
                bitmap=self.icons.iconsLib["panel_rmsd_16"],
            )
        )

        menu_plot.Append(
            make_menu_item(
                parent=menu_plot,
                evt_id=ID_extraSettings_waterfall,
                text="Settings: &Waterfall",
                bitmap=self._icons.waterfall,
            )
        )

        menu_plot.Append(
            make_menu_item(
                parent=menu_plot, evt_id=ID_extraSettings_violin, text="Settings: &Violin", bitmap=self._icons.violin
            )
        )

        menu_plot.Append(
            make_menu_item(
                parent=menu_plot, evt_id=ID_extraSettings_general, text="Settings: &Extra", bitmap=self._icons.gear
            )
        )

        menu_plot.AppendSeparator()
        menu_plot.Append(
            make_menu_item(
                parent=menu_plot,
                evt_id=ID_annotPanel_otherSettings,
                text="Settings: Annotation parameters",
                bitmap=None,
            )
        )
        menu_plot.Append(
            make_menu_item(
                parent=menu_plot, evt_id=ID_unidecPanel_otherSettings, text="Settings: UniDec parameters", bitmap=None
            )
        )

        menu_plot.AppendSeparator()
        menu_plot.Append(ID_plots_showCursorGrid, "Update plot parameters")
        # menuPlot.Append(ID_plots_resetZoom, 'Reset zoom tool\tF12')
        self.menubar.Append(menu_plot, "&Plot settings")

        # WIDGETS MENU
        menu_widgets = wx.Menu()
        menu_widget_bokeh = make_menu_item(
            parent=menu_widgets, text="Open &interactive output panel...\tShift+Z", bitmap=self._icons.bokeh
        )
        menu_widgets.Append(menu_widget_bokeh)
        menu_widget_compare_ms = make_menu_item(
            parent=menu_widgets, text="Open spectrum comparison window...", bitmap=self._icons.compare_ms
        )
        menu_widgets.Append(menu_widget_compare_ms)
        menu_widgets.Append(
            make_menu_item(
                parent=menu_widgets, evt_id=ID_docTree_plugin_UVPD, text="Open UVPD processing window...", bitmap=None
            )
        )
        menu_widgets.Append(
            make_menu_item(parent=menu_widgets, evt_id=ID_docTree_plugin_MSMS, text="Open MS/MS window...", bitmap=None)
        )
        menu_widget_overlay_viewer = make_menu_item(
            parent=menu_widgets, text="Open overlay window...\tShift+O", bitmap=None
        )
        menu_widgets.Append(menu_widget_overlay_viewer)

        #         menu_widget_interactive_viewer = make_menu_item(
        #             parent=menuWidgets, text="Open interactive window...", bitmap=None
        #         )
        #         menuWidgets.Append(menu_widget_interactive_viewer)

        # add manual activation sub-menu
        menu_widgets.AppendSeparator()
        menu_widget_ciu_import = make_menu_item(
            parent=menu_widgets, text="Open Manual CIU import manager...", bitmap=None
        )
        menu_widgets.Append(menu_widget_ciu_import)
        menu_widget_sid_import = make_menu_item(
            parent=menu_widgets, text="Open Manual SID import manager...", bitmap=None
        )
        menu_widgets.Append(menu_widget_sid_import)

        # add lesa activation sub-menu
        menu_widgets.AppendSeparator()
        menu_widget_lesa_import = make_menu_item(
            parent=menu_widgets, text="Open LESA import manager...\tCtrl+L", bitmap=None
        )
        menu_widgets.Append(menu_widget_lesa_import)

        menu_widget_lesa_viewer = make_menu_item(
            parent=menu_widgets, text="Open LESA imaging window...\tShift+L", bitmap=None
        )
        menu_widgets.Append(menu_widget_lesa_viewer)
        self.menubar.Append(menu_widgets, "&Widgets")

        # CONFIG MENU
        menu_config = wx.Menu()
        menu_config.Append(
            make_menu_item(
                parent=menu_config,
                evt_id=ID_saveConfig,
                text="Export configuration XML file (default location)\tCtrl+S",
                bitmap=self._icons.export_db,
            )
        )
        menu_config.Append(
            make_menu_item(
                parent=menu_config,
                evt_id=ID_saveAsConfig,
                text="Export configuration XML file as...\tCtrl+Shift+S",
                bitmap=None,
            )
        )
        menu_config.AppendSeparator()
        menu_config.Append(
            make_menu_item(
                parent=menu_config,
                evt_id=ID_openConfig,
                text="Import configuration XML file (default location)\tCtrl+Shift+O",
                bitmap=self._icons.import_db,
            )
        )
        menu_config.Append(
            make_menu_item(
                parent=menu_config, evt_id=ID_openAsConfig, text="Import configuration XML file from...", bitmap=None
            )
        )
        menu_config.AppendSeparator()
        self.menu_config_check_load_ccs_db = menu_config.Append(
            ID_importAtStart_CCS, "Load at start", kind=wx.ITEM_CHECK
        )
        self.menu_config_check_load_ccs_db.Check(CONFIG.loadCCSAtStart)
        menu_config.Append(
            make_menu_item(
                parent=menu_config,
                evt_id=ID_openCCScalibrationDatabse,
                text="Import CCS calibration database\tCtrl+Alt+C",
                bitmap=self._icons.filelist,
            )
        )
        menu_config.Append(
            make_menu_item(
                parent=menu_config,
                evt_id=ID_selectCalibrant,
                text="Show CCS calibrants\tCtrl+Shift+C",
                bitmap=self._icons.target,
            )
        )
        menu_config.AppendSeparator()
        self.menu_config_check_driftscope = menu_config.Append(
            ID_checkAtStart_Driftscope, "Look for DriftScope at start", kind=wx.ITEM_CHECK
        )
        self.menu_config_check_driftscope.Check(CONFIG.checkForDriftscopeAtStart)
        menu_config_driftscope = make_menu_item(
            parent=menu_config, text="Check DriftScope path", bitmap=self._icons.driftscope
        )
        menu_config.Append(menu_config_driftscope)
        # menu_config.Append(
        #     make_menu_item(
        #         parent=menu_config,
        #         id=ID_setDriftScopeDir,
        #         text="Set DriftScope path...",
        #         bitmap=self.icons.iconsLib["driftscope_16"],
        #     )
        # )
        self.menubar.Append(menu_config, "&Configuration")

        menu_software = wx.Menu()
        menu_software.Append(
            make_menu_item(
                parent=menu_software,
                evt_id=ID_help_UniDecInfo,
                text="About UniDec engine...",
                bitmap=self._icons.unidec,
            )
        )
        #         otherSoftwareMenu.Append(ID_open1DIMSFile, 'About CIDER...')

        # VIEW MENU
        menu_view = wx.Menu()
        menu_clear_all_plots = make_menu_item(parent=menu_view, text="&Clear all plots", bitmap=self._icons.erase)
        menu_view.Append(menu_clear_all_plots)
        menu_view.AppendSeparator()
        self.toggle_document_page = menu_view.Append(
            ID_window_documentList, "Panel: Documents\tCtrl+1", kind=wx.ITEM_CHECK
        )
        self.toggle_peaks_page = menu_view.Append(ID_window_ionList, "Panel: Peak list\tCtrl+2", kind=wx.ITEM_CHECK)
        self.toggle_text_page = menu_view.Append(ID_window_textList, "Panel: Text list\tCtrl+3", kind=wx.ITEM_CHECK)
        self.toggle_manual_page = menu_view.Append(
            ID_window_multipleMLList, "Panel: Multiple files\tCtrl+4", kind=wx.ITEM_CHECK
        )
        menu_view.Append(ID_window_all, "Panel: Restore &all")
        menu_view.AppendSeparator()
        menu_view_toolbar_horizontal = make_menu_item(parent=menu_view, text="Toolbar: Horizontal", bitmap=None)
        menu_view.Append(menu_view_toolbar_horizontal)
        menu_view_toolbar_vertical = make_menu_item(parent=menu_view, text="Toolbar: Vertical", bitmap=None)
        menu_view.Append(menu_view_toolbar_vertical)
        menu_view.AppendSeparator()
        menu_view_maximize = make_menu_item(parent=menu_view, text="Maximize window", bitmap=self._icons.maximize)
        menu_view.Append(menu_view_maximize)
        menu_view_minimize = make_menu_item(parent=menu_view, text="Minimize window", bitmap=self._icons.minimize)
        menu_view.Append(menu_view_minimize)
        menu_view_fullscreen = make_menu_item(
            parent=menu_view, text="Toggle fullscreen\tAlt+F11", bitmap=self._icons.fullscreen
        )
        menu_view.Append(menu_view_fullscreen)
        # menu_view.AppendSeparator()
        # menu_view_restart = make_menu_item(parent=menu_view, text="Restart ORIGAMI", bitmap=self._icons.restart)
        # menu_view.Append(menu_view_restart)

        self.menubar.Append(menu_view, "&View")

        # HELP MENU
        menu_help_pages = wx.Menu()
        menu_help_pages.Append(
            make_menu_item(
                parent=menu_help_pages,
                evt_id=ID_help_page_dataLoading,
                text="Learn more: Loading data",
                bitmap=self._icons.folder,
            )
        )

        menu_help_pages.Append(
            make_menu_item(
                parent=menu_help_pages,
                evt_id=ID_help_page_dataExtraction,
                text="Learn more: Data extraction",
                bitmap=self._icons.extract,
            )
        )

        menu_help_pages.Append(
            make_menu_item(
                parent=menu_help_pages,
                evt_id=ID_help_page_UniDec,
                text="Learn more: MS deconvolution using UniDec",
                bitmap=self._icons.unidec,
            )
        )

        menu_help_pages.Append(
            make_menu_item(
                parent=menu_help_pages,
                evt_id=ID_help_page_ORIGAMI,
                text="Learn more: ORIGAMI-MS (Automated CIU)",
                bitmap=self.icons.iconsLib["origamiLogoDark16"],
            )
        )

        menu_help_pages.Append(
            make_menu_item(
                parent=menu_help_pages,
                evt_id=ID_help_page_multipleFiles,
                text="Learn more: Multiple files (Manual CIU)",
                bitmap=self.icons.iconsLib["panel_mll__16"],
            )
        )

        menu_help_pages.Append(
            make_menu_item(
                parent=menu_help_pages,
                evt_id=ID_help_page_overlay,
                text="Learn more: Overlay documents",
                bitmap=self._icons.overlay,
            )
        )

        #         helpPagesMenu.Append(make_menu_item(parent=helpPagesMenu, id=ID_help_page_linearDT,
        #                                               text='Learn more: Linear Drift-time analysis',
        #                                               bitmap=self.icons.iconsLib['panel_dt_16']))
        #
        #         helpPagesMenu.Append(make_menu_item(parent=helpPagesMenu, id=ID_help_page_CCScalibration,
        #                                               text='Learn more: CCS calibration',
        #                                               bitmap=self.icons.iconsLib['panel_ccs_16']))

        menu_help_pages.Append(
            make_menu_item(
                parent=menu_help_pages,
                evt_id=ID_help_page_Interactive,
                text="Learn more: Interactive output",
                bitmap=self._icons.bokeh,
            )
        )

        menu_help_pages.Append(
            make_menu_item(
                parent=menu_help_pages,
                evt_id=ID_help_page_annotatingMassSpectra,
                text="Learn more: Annotating mass spectra",
                bitmap=self._icons.tag,
            )
        )

        menu_help_pages.Append(
            make_menu_item(
                parent=menu_help_pages,
                evt_id=ID_help_page_OtherData,
                text="Learn more: Annotated data",
                bitmap=self._icons.blank,
            )
        )

        # HELP MENU
        menu_help = wx.Menu()
        menu_help.AppendMenu(wx.ID_ANY, "Help pages...", menu_help_pages)
        menu_help.AppendSeparator()
        menu_help.Append(
            make_menu_item(parent=menu_help, evt_id=ID_helpGuide, text="Open User Guide...", bitmap=self._icons.html)
        )
        menu_help.Append(
            make_menu_item(
                parent=menu_help,
                evt_id=ID_helpYoutube,
                text="Check out video guides... (online)",
                bitmap=self._icons.youtube,
            )
        )
        menu_help.Append(
            make_menu_item(
                parent=menu_help,
                evt_id=ID_helpNewVersion,
                text="Check for updates... (online)",
                bitmap=self._icons.github,
            )
        )
        menu_help.Append(
            make_menu_item(
                parent=menu_help, evt_id=ID_helpCite, text="Paper to cite... (online)", bitmap=self._icons.cite
            )
        )
        menu_help.AppendSeparator()
        menu_help.AppendMenu(wx.ID_ANY, "About other software...", menu_software)
        menu_help.AppendSeparator()
        menu_help.Append(
            make_menu_item(
                parent=menu_help,
                evt_id=ID_helpNewFeatures,
                text="Request new features... (web)",
                bitmap=self._icons.request,
            )
        )
        menu_help.Append(
            make_menu_item(
                parent=menu_help, evt_id=ID_helpReportBugs, text="Report bugs... (web)", bitmap=self._icons.bug
            )
        )
        menu_help.AppendSeparator()
        menu_help_version = make_menu_item(
            parent=menu_help, text="Check for newest version...", bitmap=self._icons.bell
        )
        menu_help.Append(menu_help_version)
        menu_help_new = make_menu_item(
            parent=menu_help, text="Whats new in v{}".format(CONFIG.version), bitmap=self._icons.new
        )
        menu_help.Append(menu_help_new)
        menu_help.AppendSeparator()
        menu_help_about = make_menu_item(
            parent=menu_help, text="About ORIGAMI\tCtrl+Shift+A", bitmap=self.icons.iconsLib["origamiLogoDark16"]
        )
        menu_help.Append(menu_help_about)
        self.menubar.Append(menu_help, "&Help")
        self.SetMenuBar(self.menubar)

        # DEBUG MODE
        if CONFIG.debug:
            menu_dev = wx.Menu()
            # append inspector
            menu_dev_wxpython = make_menu_item(parent=menu_dev, text="Open wxPython inspector")
            menu_dev.Append(menu_dev_wxpython)
            self.Bind(wx.EVT_MENU, self._dev_open_wxpython_inspector, menu_dev_wxpython)

            # append closable widget
            menu_dev_widget = make_menu_item(parent=menu_dev, text="Add closable widget")
            menu_dev.Append(menu_dev_widget)
            self.Bind(wx.EVT_MENU, self._dev_add_widget, menu_dev_widget)

            menu_logging = wx.Menu()
            menu_log_debug = menu_logging.AppendRadioItem(wx.ID_ANY, "Logging: DEBUG")
            menu_log_info = menu_logging.AppendRadioItem(wx.ID_ANY, "Logging: INFO")
            menu_log_warning = menu_logging.AppendRadioItem(wx.ID_ANY, "Logging: WARNING")
            menu_log_error = menu_logging.AppendRadioItem(wx.ID_ANY, "Logging: ERROR")
            menu_log_critical = menu_logging.AppendRadioItem(wx.ID_ANY, "Logging: CRITICAL")

            self.Bind(wx.EVT_MENU, self._dev_logging, menu_log_debug)
            self.Bind(wx.EVT_MENU, self._dev_logging, menu_log_info)
            self.Bind(wx.EVT_MENU, self._dev_logging, menu_log_warning)
            self.Bind(wx.EVT_MENU, self._dev_logging, menu_log_error)
            self.Bind(wx.EVT_MENU, self._dev_logging, menu_log_critical)

            menu_dev.AppendMenu(wx.ID_ANY, "Logging", menu_logging)

            self.menubar.Append(menu_dev, "&Development")

        self.SetMenuBar(self.menubar)

        # Bind functions to menu
        # HELP MENU
        self.Bind(wx.EVT_MENU, self.on_open_about_panel, menu_help_about)
        self.Bind(wx.EVT_MENU, self.on_check_latest_version, menu_help_version)
        self.Bind(wx.EVT_MENU, self.on_whats_new, menu_help_new)
        self.Bind(wx.EVT_MENU, self.on_open_link, id=ID_helpGuide)
        self.Bind(wx.EVT_MENU, self.on_open_link, id=ID_helpCite)
        self.Bind(wx.EVT_MENU, self.on_open_link, id=ID_helpYoutube)
        self.Bind(wx.EVT_MENU, self.on_open_link, id=ID_helpNewVersion)
        self.Bind(wx.EVT_MENU, self.on_open_link, id=ID_helpReportBugs)
        self.Bind(wx.EVT_MENU, self.on_open_link, id=ID_helpNewFeatures)
        self.Bind(wx.EVT_MENU, self.on_open_link, id=ID_helpAuthor)
        # self.Bind(wx.EVT_MENU, self.presenter.on_reboot_origami, menu_view_restart)

        self.Bind(wx.EVT_MENU, self.on_open_html_guide, id=ID_help_UniDecInfo)
        self.Bind(wx.EVT_MENU, self.on_open_html_guide, id=ID_help_page_gettingStarted)
        self.Bind(wx.EVT_MENU, self.on_open_html_guide, id=ID_help_page_dataLoading)
        self.Bind(wx.EVT_MENU, self.on_open_html_guide, id=ID_help_page_UniDec)
        self.Bind(wx.EVT_MENU, self.on_open_html_guide, id=ID_help_page_ORIGAMI)
        self.Bind(wx.EVT_MENU, self.on_open_html_guide, id=ID_help_page_overlay)
        self.Bind(wx.EVT_MENU, self.on_open_html_guide, id=ID_help_page_multipleFiles)
        self.Bind(wx.EVT_MENU, self.on_open_html_guide, id=ID_help_page_linearDT)
        self.Bind(wx.EVT_MENU, self.on_open_html_guide, id=ID_help_page_CCScalibration)
        self.Bind(wx.EVT_MENU, self.on_open_html_guide, id=ID_help_page_dataExtraction)
        self.Bind(wx.EVT_MENU, self.on_open_html_guide, id=ID_help_page_Interactive)
        self.Bind(wx.EVT_MENU, self.on_open_html_guide, id=ID_help_page_OtherData)
        self.Bind(wx.EVT_MENU, self.on_open_html_guide, id=ID_help_page_annotatingMassSpectra)

        # FILE MENU
        self.Bind(wx.EVT_MENU, self.data_handling.on_open_origami_document, menu_file_load_origami)
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
        self.Bind(wx.EVT_MENU, self.on_close, menu_file_exit)
        # self.Bind(wx.EVT_MENU, self.on_add_blank_document_interactive, id=ID_addNewInteractiveDoc)
        # self.Bind(wx.EVT_MENU, self.on_add_blank_document_manual, id=ID_addNewManualDoc)
        # self.Bind(wx.EVT_MENU, self.on_add_blank_document_overlay, id=ID_addNewOverlayDoc)
        # self.Bind(wx.EVT_TOOL, self.on_open_multiple_files, menu_open_multiple)

        self.Bind(wx.EVT_TOOL, self.data_handling.on_open_mgf_file_fcn, id=ID_fileMenu_MGF)
        self.Bind(wx.EVT_TOOL, self.data_handling.on_open_mzml_file_fcn, id=ID_fileMenu_mzML)
        self.Bind(wx.EVT_TOOL, self.data_handling.on_open_thermo_file_fcn, menu_open_thermo)

        self.Bind(wx.EVT_MENU, self.data_handling.on_open_waters_raw_ms_fcn, id=ID_load_masslynx_raw_ms_only)
        self.Bind(wx.EVT_MENU, self.data_handling.on_open_waters_raw_imms_fcn, menu_file_waters_imms)
        self.Bind(wx.EVT_MENU, self.data_handling.on_open_waters_raw_imms_fcn, menu_open_origami)

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
        self.Bind(wx.EVT_MENU, self.on_open_interactive_output_panel, menu_widget_bokeh)

        # UTILITIES
        #         self.Bind(wx.EVT_MENU, self.panelDocuments.documents.on_process_UVPD, id=ID_docTree_plugin_UVPD)
        #         self.Bind(wx.EVT_MENU, self.panelDocuments.documents.on_open_MSMS_viewer, id=ID_docTree_plugin_MSMS)
        #         self.Bind(wx.EVT_MENU, self.panelDocuments.documents.on_open_overlay_viewer,
        #         menu_widget_overlay_viewer)
        self.Bind(wx.EVT_MENU, self.panelDocuments.documents.on_open_lesa_viewer, menu_widget_lesa_viewer)
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
        self.Bind(wx.EVT_MENU, self.on_check_driftscope_path, menu_config_driftscope)
        self.Bind(wx.EVT_MENU, self.on_check_in_menu, id=ID_checkAtStart_Driftscope)
        self.Bind(wx.EVT_MENU, self.on_check_in_menu, id=ID_importAtStart_CCS)

        # VIEW MENU
        self.Bind(wx.EVT_MENU, self.on_toggle_panel, id=ID_window_all)
        self.Bind(wx.EVT_MENU, self.on_toggle_panel, self.toggle_document_page)
        self.Bind(wx.EVT_MENU, self.on_toggle_panel, self.toggle_peaks_page)
        self.Bind(wx.EVT_MENU, self.on_toggle_panel, self.toggle_text_page)
        self.Bind(wx.EVT_MENU, self.on_toggle_panel, self.toggle_manual_page)
        self.Bind(wx.EVT_MENU, self.on_set_window_maximize, menu_view_maximize)
        self.Bind(wx.EVT_MENU, self.on_set_window_iconize, menu_view_minimize)
        self.Bind(wx.EVT_MENU, self.on_set_toolbar_horizontal, menu_view_toolbar_horizontal)
        self.Bind(wx.EVT_MENU, self.on_set_toolbar_vertical, menu_view_toolbar_vertical)
        self.Bind(wx.EVT_MENU, self.on_set_window_fullscreen, menu_view_fullscreen)
        self.Bind(wx.EVT_MENU, self.panelPlots.on_clear_all_plots, menu_clear_all_plots)
        self.Bind(wx.EVT_MENU, self.panelDocuments.documents.on_open_spectrum_comparison_viewer, menu_widget_compare_ms)
        self.SetMenuBar(self.menubar)

    @staticmethod
    def _dev_open_wxpython_inspector(_evt):
        """Opens wxpython inspector"""
        import wx.lib.inspection

        wx.lib.inspection.InspectionTool().Show()
        logger.debug("Opened inspection tool")

    def _dev_add_widget(self, _evt):
        """Opens closable widget - use to ensure that widgets can be dynamically added/removed from the UI"""
        item = np.random.choice(["ion", "files"], 1, False)[0]
        panel_name = self.create_panel(item, f"TEST_DOC_#{np.random.randint(0, 100, 1)[0]}")
        logger.debug(f"Created random panel - {panel_name}")

    @staticmethod
    def _dev_logging(evt):
        """Change logger level"""
        name = evt.GetEventObject().FindItemById(evt.GetId()).GetItemLabel()
        level = {
            "Logging: DEBUG": logging.DEBUG,
            "Logging: INFO": logging.INFO,
            "Logging: WARNING": logging.WARNING,
            "Logging: ERROR": logging.ERROR,
            "Logging: CRITICAL": logging.CRITICAL,
        }.get(name, logging.DEBUG)

        logging.getLogger("origami").setLevel(level)
        print(f"Changed logging level to -> {level}")

    def on_customise_annotation_plot_parameters(self, _evt):
        """Open dialog to customise user annotations parameters"""
        from origami.gui_elements.dialog_customise_user_annotations import DialogCustomiseUserAnnotations

        dlg = DialogCustomiseUserAnnotations(self)
        dlg.ShowModal()

    def on_customise_unidec_plot_parameters(self, _evt):
        """Open dialog to customise unidec parameters"""
        from origami.widgets.UniDec.dialog_customise_unidec_visuals import DialogCustomiseUniDecVisuals

        dlg = DialogCustomiseUniDecVisuals(self, CONFIG, self.icons)
        dlg.ShowModal()

    def on_open_link(self, evt):
        """Open selected webpage."""

        evt_id = evt
        if not isinstance(evt_id, int):
            evt_id = evt.GetId()

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

        link = CONFIG.links[links[evt_id]]

        # open webpage
        try:
            self.presenter.onThreading(
                None, ("Opening a link in your default internet browser", 4), action="updateStatusbar"
            )
            webbrowser.open(link, autoraise=True)
        except KeyError:
            logger.warning("Could not open requested link")

    def on_check_latest_version(self, _evt):
        """Manually check for latest version of ORIGAMI"""
        self._on_check_latest_version(False)

    def _on_check_latest_version(self, silent: bool = True):
        """Simple function to check whether this is the newest version available"""
        from origami.gui_elements.panel_notify_new_version import check_version

        check_version(self, silent)

    def on_whats_new(self, _evt):
        """Check latest version"""
        from origami.gui_elements.panel_notify_new_version import PanelNewVersion

        dlg = PanelNewVersion(self)
        dlg.Show()

    def on_open_html_guide(self, evt):
        """Open HTML page"""
        from origami.gui_elements.panel_html_viewer import PanelHTMLViewer
        from origami.help_documentation import HTMLHelp

        html_pages = HTMLHelp()
        evt_id = evt.GetId()
        link, kwargs = None, {}
        if evt_id == ID_help_UniDecInfo:
            kwargs = html_pages.page_UniDec_info

        elif evt_id == ID_help_page_dataLoading:
            link = r"https://origami.lukasz-migas.com/user-guide/loading-data"

        elif evt_id == ID_help_page_gettingStarted:
            link = r"https://origami.lukasz-migas.com/user-guide/example-files"

        elif evt_id == ID_help_page_UniDec:
            link = r"https://origami.lukasz-migas.com/user-guide/deconvolution/unidec-deconvolution"

        elif evt_id == ID_help_page_ORIGAMI:
            link = r"https://origami.lukasz-migas.com/user-guide/data-handling/automated-ciu"

        elif evt_id == ID_help_page_overlay:
            kwargs = html_pages.page_overlay_info

        elif evt_id == ID_help_page_multipleFiles:
            link = r"https://origami.lukasz-migas.com/user-guide/data-handling/manual-ciu"

        elif evt_id == ID_help_page_linearDT:
            kwargs = html_pages.page_linear_dt_info

        elif evt_id == ID_help_page_CCScalibration:
            kwargs = html_pages.page_ccs_calibration_info

        elif evt_id == ID_help_page_dataExtraction:
            link = r"https://origami.lukasz-migas.com/user-guide/data-handling/ms-and-imms-files"

        elif evt_id == ID_help_page_Interactive:
            link = r"https://origami.lukasz-migas.com/user-guide/interactive-output/simple-output"

        elif evt_id == ID_help_page_OtherData:
            kwargs = html_pages.page_other_data_info

        elif evt_id == ID_help_page_annotatingMassSpectra:
            link = r"https://origami.lukasz-migas.com/user-guide/processing/mass-spectra-annotation"

        if link is None:
            html_viewer = PanelHTMLViewer(self, **kwargs)
            html_viewer.Show()
        else:
            html_viewer = PanelHTMLViewer(self, link=link)
            html_viewer.Show()

    def on_check_in_menu(self, evt):
        """Update the check buttons in the menu upon registration of an event"""

        # get event id
        evt_id = evt.GetId()

        if evt_id == ID_checkAtStart_Driftscope:
            check_value = not CONFIG.checkForDriftscopeAtStart
            CONFIG.checkForDriftscopeAtStart = check_value
            self.menu_config_check_driftscope.Check(check_value)
        elif evt_id == ID_importAtStart_CCS:
            check_value = not CONFIG.loadCCSAtStart
            CONFIG.loadCCSAtStart = check_value
            self.menu_config_check_load_ccs_db.Check(check_value)

    def on_set_window_maximize(self, _evt):
        """Maximize app."""
        self.Maximize()

    def on_set_window_iconize(self, _evt):
        """Iconize app."""
        self.Iconize()

    def on_set_window_fullscreen(self, _evt):
        """Fullscreen app."""
        self._fullscreen = not self._fullscreen
        self.ShowFullScreen(
            self._fullscreen, style=wx.FULLSCREEN_ALL & ~(wx.FULLSCREEN_NOMENUBAR | wx.FULLSCREEN_NOSTATUSBAR)
        )

    def on_set_toolbar_vertical(self, _evt):
        """Destroy the old-toolbar and create a new instance in a vertical position"""
        self.toolbar.Destroy()
        self.make_toolbar(wx.TB_VERTICAL)

    def on_set_toolbar_horizontal(self, _evt):
        """Destroy the old-toolbar and create a new instance in a horizontal position"""
        self.toolbar.Destroy()
        self.make_toolbar(wx.TB_HORIZONTAL)

    def make_shortcuts(self):
        """
        Setup shortcuts for the GUI application
        """
        # # Setup shortcuts. Format: 'KEY', 'FUNCTION', 'MODIFIER'
        # accelerator_events = [
        #     #             ["I", self.panelDocuments.documents.onOpenDocInfo, wx.ACCEL_CTRL],
        #     ["W", self.data_handling.on_open_multiple_text_2d_fcn, wx.ACCEL_CTRL],
        #     ["Z", self.on_open_interactive_output_panel, wx.ACCEL_SHIFT],
        #     ["G", self.data_handling.on_open_directory, wx.ACCEL_CTRL],
        # ]
        # key_ids_list = [wx.NewId() for _ in accelerator_events]
        # control_list = []
        # for idx, key_binding in enumerate(accelerator_events):
        #     self.Bind(wx.EVT_MENU, key_binding[1], id=key_ids_list[idx])
        #     control_list.append((key_binding[2], ord(key_binding[0]), key_ids_list[idx]))
        #
        # # Add more shortcuts with known IDs
        # extra_key_events = [
        #     # ["Q", self.presenter.on_overlay_2D, wx.ACCEL_ALT, ID_overlayMZfromList],
        #     # ["W", self.presenter.on_overlay_2D, wx.ACCEL_ALT, ID_overlayTextFromList],
        #     ["S", self.panelDocuments.documents.on_show_plot, wx.ACCEL_ALT, ID_showPlotDocument],
        #     ["R", self.panelDocuments.documents.onRenameItem, wx.ACCEL_ALT, ID_renameItem],
        #     ["X", self.panelDocuments.documents.on_show_plot, wx.ACCEL_ALT, ID_showPlotMSDocument],
        #     ["Z", self.panelDocuments.documents.on_change_charge_state, wx.ACCEL_ALT, ID_assignChargeState],
        #     ["V", self.panelDocuments.documents.on_save_csv, wx.ACCEL_ALT, ID_saveDataCSVDocument],
        # ]
        #
        # for item in extra_key_events:
        #     self.Bind(wx.EVT_MENU, item[1], id=item[3])
        #     control_list.append((item[2], ord(item[0]), item[3]))
        #
        # self.SetAcceleratorTable(wx.AcceleratorTable(control_list))

    def on_open_source_menu(self, _evt):
        """Open menu to load MGF/mzML file(s)"""
        menu = wx.Menu()
        menu.Append(
            make_menu_item(
                parent=menu,
                evt_id=ID_fileMenu_MGF,
                text="Open Mascot Generic Format file (.mgf) [MS/MS]",
                bitmap=self.icons.iconsLib["blank_16"],
            )
        )
        menu.Append(
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

    def make_toolbar(self, style=wx.TB_HORIZONTAL):
        """Make toolbar"""

        # Create toolbar
        self.toolbar = self.CreateToolBar(style | wx.NO_BORDER | wx.TB_FLAT)
        self.toolbar.SetToolBitmapSize((16, 16))

        tool_open_document = self.toolbar.AddTool(wx.ID_ANY, "", self._icons.open, shortHelp="Open ORIGAMI document...")
        self.Bind(wx.EVT_TOOL, self.data_handling.on_open_origami_document, tool_open_document)
        self.toolbar.AddSeparator()

        tool_config_export = self.toolbar.AddTool(
            wx.ID_ANY, "", self._icons.export_db, shortHelp="Export configuration file..."
        )
        self.Bind(wx.EVT_TOOL, self.data_handling.on_export_config_fcn, tool_config_export)

        tool_config_import = self.toolbar.AddTool(
            wx.ID_ANY, "", self._icons.export_db, shortHelp="Import configuration file..."
        )
        self.Bind(wx.EVT_TOOL, self.data_handling.on_import_config_fcn, tool_config_import)

        self.toolbar.AddSeparator()
        tool_open_masslynx = self.toolbar.AddTool(
            wx.ID_ANY, "", self._icons.micromass, shortHelp="Open MassLynx file (.raw)"
        )
        self.Bind(wx.EVT_TOOL, self.data_handling.on_open_waters_raw_imms_fcn, tool_open_masslynx)

        tool_open_thermo = self.toolbar.AddTool(wx.ID_ANY, "", self._icons.thermo, shortHelp="Open Thermo file (.RAW)")
        self.Bind(wx.EVT_TOOL, self.data_handling.on_open_thermo_file_fcn, tool_open_thermo)

        tool_open_multiple = self.toolbar.AddTool(
            wx.ID_ANY, "", self.icons.iconsLib["open_masslynxMany_16"], shortHelp="Open multiple MassLynx files (.raw)"
        )
        # self.Bind(wx.EVT_TOOL, self.data_handling.on_open_thermo_file_fcn, tool_open_multiple)

        self.toolbar.AddSeparator()
        tool_open_text_heatmap = self.toolbar.AddTool(
            wx.ID_ANY, "", self.icons.iconsLib["open_textMany_16"], shortHelp="Open one (or more) heatmap text file"
        )
        self.Bind(wx.EVT_TOOL, self.data_handling.on_open_multiple_text_2d_fcn, tool_open_text_heatmap)

        self.toolbar.AddSeparator()

        tool_open_msms = self.toolbar.AddTool(
            wx.ID_ANY, "", self.icons.iconsLib["ms16"], shortHelp="Open MS/MS files..."
        )
        self.Bind(wx.EVT_TOOL, self.on_open_source_menu, tool_open_msms)
        # self.Bind(wx.EVT_MENU, self.data_handling.on_open_thermo_file_fcn, tool_open_multiple)
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
        tool_action_global = self.toolbar.AddLabelTool(
            ID_extraSettings_general_plot, "", self._icons.switch_on, shortHelp="Settings: General plot"
        )
        tool_action_1d = self.toolbar.AddLabelTool(
            ID_extraSettings_plot1D, "", self._icons.plot_1d, shortHelp="Settings: Plot 1D panel"
        )
        tool_action_2d = self.toolbar.AddLabelTool(
            ID_extraSettings_plot2D, "", self.icons.iconsLib["panel_plot2D_16"], shortHelp="Settings: Plot 2D panel"
        )
        tool_action_3d = self.toolbar.AddLabelTool(
            ID_extraSettings_plot3D, "", self.icons.iconsLib["panel_plot3D_16"], shortHelp="Settings: Plot 3D panel"
        )
        tool_action_colorbar = self.toolbar.AddLabelTool(
            ID_extraSettings_colorbar, "", self._icons.plot_colorbar, shortHelp="Settings: Colorbar panel"
        )
        tool_action_legend = self.toolbar.AddLabelTool(
            ID_extraSettings_legend, "", self._icons.plot_legend, shortHelp="Settings: Legend panel"
        )
        tool_action_rmsd = self.toolbar.AddLabelTool(
            ID_extraSettings_rmsd, "", self.icons.iconsLib["panel_rmsd_16"], shortHelp="Settings: RMSD panel"
        )
        tool_action_waterfall = self.toolbar.AddLabelTool(
            ID_extraSettings_waterfall, "", self._icons.waterfall, shortHelp="Settings: Waterfall panel"
        )
        tool_action_violin = self.toolbar.AddLabelTool(
            ID_extraSettings_violin, "", self._icons.violin, shortHelp="Settings: Violin panel"
        )
        tool_action_general = self.toolbar.AddLabelTool(
            ID_extraSettings_general, "", self._icons.gear, shortHelp="Settings: Extra panel"
        )
        self.toolbar.AddSeparator()

        tool_action_bokeh = self.toolbar.AddLabelTool(
            wx.ID_ANY, "", self._icons.bokeh, shortHelp="Open interactive output panel"
        )
        self.Bind(wx.EVT_MENU, self.on_open_interactive_output_panel, tool_action_bokeh)

        # Actually realise the toolbar
        self.toolbar.Realize()

    def on_toggle_panel(self, evt, check=None):

        evt_id = None
        if isinstance(evt, int):
            evt_id = evt
        elif isinstance(evt, str):
            if evt == "document":
                evt_id = ID_window_documentList
        elif evt is not None:
            evt_id = evt.GetId()

        if evt_id is not None:
            if evt_id == ID_window_documentList:
                if not self.panelDocuments.IsShown() or not self.toggle_document_page.IsChecked():
                    self.window_mgr.GetPane(self.panelDocuments).Show()
                    CONFIG._windowSettings["Documents"]["show"] = True
                else:
                    self.window_mgr.GetPane(self.panelDocuments).Hide()
                    CONFIG._windowSettings["Documents"]["show"] = False
                self.toggle_document_page.Check(CONFIG._windowSettings["Documents"]["show"])
                self.on_find_toggle_by_id(find_id=evt_id, check=CONFIG._windowSettings["Documents"]["show"])
            elif evt_id == ID_window_all:
                for key in CONFIG._windowSettings:
                    CONFIG._windowSettings[key]["show"] = True

                self.on_find_toggle_by_id(check_all=True)

                for panel in [self.panelDocuments]:  # , self.panelMML, self.panelMultipleIons, self.panelMultipleText]:
                    self.window_mgr.GetPane(panel).Show()

                self.toggle_document_page.Check(CONFIG._windowSettings["Documents"]["show"])

        # Checking at start of program
        else:
            if not self.panelDocuments.IsShown():
                CONFIG._windowSettings["Documents"]["show"] = False

            self.toggle_document_page.Check(CONFIG._windowSettings["Documents"]["show"])

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

    @staticmethod
    def on_get_toggle_id(panel):
        """Get toggle ID"""
        panel_dict = {
            "Documents": ID_window_documentList,
            "Controls": ID_window_controls,
            "Multiple files": ID_window_multipleMLList,
            "Peak list": ID_window_ionList,
            "Text files": ID_window_textList,
        }
        return panel_dict[panel]

    def on_close(self, evt, **kwargs):
        """Close window"""

        n_documents = len(ENV)
        if n_documents > 0 and not kwargs.get("ignore_warning", False):
            msg = (
                f"{len(ENV)} document(s) are still open and you might lose some work if they are not saved. "
                "\nAre you sure you would want to continue?"
            )
            dlg = DialogNotifyOpenDocuments(self, message=msg)
            response = dlg.ShowModal()

            if response == wx.ID_NO:
                print("Cancelled operation")
                return
            elif response == wx.ID_SAVE:
                self.presenter.on_save_all_documents()

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

    def on_size(self, _evt):
        """Toggles the resized attribute when user is changing the size of the window"""
        self.resized = True

    def on_idle(self, _evt):
        """Toggles the resized attribute when user has finished changing the size of the window"""
        if self.resized:
            self.resized = False

    def on_open_about_panel(self, _evt):
        """Show About ORIGAMI panel."""
        from origami.gui_elements.panel_about import PanelAbout

        about = PanelAbout(self, self.icons)
        about.Centre()
        about.Show()
        about.SetFocus()

    def on_open_plot_settings_panel(self, evt):
        """Open plot settings"""
        window = None
        evt_id = evt.GetId()
        if evt_id == ID_extraSettings_colorbar:
            window = "Colorbar"
        elif evt_id == ID_extraSettings_legend:
            window = "Legend"
        elif evt_id == ID_extraSettings_plot1D:
            window = "Plot 1D"
        elif evt_id == ID_extraSettings_plot2D:
            window = "Plot 2D"
        elif evt_id == ID_extraSettings_plot3D:
            window = "Plot 3D"
        elif evt_id == ID_extraSettings_rmsd:
            window = "RMSD"
        elif evt_id == ID_extraSettings_waterfall:
            window = "Waterfall"
        elif evt_id == ID_extraSettings_violin:
            window = "Violin"
        elif evt_id == ID_extraSettings_general:
            window = "Extra"
        elif evt_id == ID_extraSettings_general_plot:
            window = "General"

        if window is None:
            return

        if not self.panelParametersEdit.IsShown() or not CONFIG._windowSettings["Plot parameters"]["show"]:
            if CONFIG._windowSettings["Plot parameters"]["floating"]:
                self.window_mgr.GetPane(self.panelParametersEdit).Float()

            self.window_mgr.GetPane(self.panelParametersEdit).Show()
            CONFIG._windowSettings["Plot parameters"]["show"] = True
            self.panelParametersEdit.on_set_page(window)
            self.window_mgr.Update()
        else:
            args = ("An instance of this panel is already open - changing page to: %s" % window, 4)
            self.presenter.onThreading(evt, args, action="updateStatusbar")
            self.panelParametersEdit.on_set_page(window)
            return

    def on_open_interactive_output_panel(self, evt):
        """Open interactive panel"""

        def _startup_module():
            """Initialize the panel"""
            CONFIG.interactiveParamsWindow_on_off = True
            self.panel_interactive_output = PanelInteractiveCreator(self, self.icons, self.presenter, CONFIG)
            self.panel_interactive_output.Show()

        if not hasattr(self, "panel_interactive_output"):
            _startup_module()
        else:
            try:
                if CONFIG.interactiveParamsWindow_on_off:
                    self.panel_interactive_output.onUpdateList()
                    args = ("An instance of this panel is already open", 4)
                    self.presenter.onThreading(evt, args, action="updateStatusbar")
                    return
            except (IndexError, ValueError, TypeError, KeyError):
                logging.error("Failed to startup `Interactive Output` panel", exc_info=True)
                _startup_module()

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
        for item in self.menu_recent_files.GetMenuItems():
            self.menu_recent_files.Delete(item.GetId())

        # populate menu
        for i, __ in enumerate(CONFIG.previousFiles[0:9], start=1):
            document_id = eval("wx.ID_FILE" + str(i))
            path = CONFIG.previousFiles[i]["file_path"]
            self.menu_recent_files.Insert(i - 1, document_id, path, "Open Document")
            self.Bind(wx.EVT_MENU, self.on_open_recent_file, id=document_id)
            if not os.path.exists(path):
                self.menu_recent_files.Enable(document_id, False)

        # append clear
        if len(CONFIG.previousFiles) > 0:
            self.menu_recent_files.AppendSeparator()

        self.menu_recent_files.Append(ID_fileMenu_clearRecent, "Clear Menu", "Clear recent items")
        self.Bind(wx.EVT_MENU, self.on_clear_recent_files, id=ID_fileMenu_clearRecent)

        if CONFIG.autoSaveSettings:
            self.data_handling.on_export_config_fcn(None, False)

    def on_clear_recent_files(self, evt):
        """Clear recent items."""

        CONFIG.previousFiles = []
        self.on_update_recent_files()

    def on_open_recent_file(self, evt):
        """Open recent document."""
        # get index
        # indexes = {
        #     ID_documentRecent0: 0,
        #     ID_documentRecent1: 1,
        #     ID_documentRecent2: 2,
        #     ID_documentRecent3: 3,
        #     ID_documentRecent4: 4,
        #     ID_documentRecent5: 5,
        #     ID_documentRecent6: 6,
        #     ID_documentRecent7: 7,
        #     ID_documentRecent8: 8,
        #     ID_documentRecent9: 9,
        # }
        raise NotImplementedError("Must implement method")
        # # get file information
        # documentID = indexes[evt.GetId()]
        # file_path = CONFIG.previousFiles[documentID]["file_path"]
        # file_type = CONFIG.previousFiles[documentID]["file_type"]
        #
        # # open file
        # if file_type == "pickle":
        #     self.data_handling.on_open_document_fcn(None, file_path=file_path)
        # elif file_type == "MassLynx":
        #     self.data_handling.on_open_single_MassLynx_raw(file_path, "Type: MassLynx")
        # elif file_type == "ORIGAMI":
        #     self.data_handling.on_open_single_MassLynx_raw(file_path, "Type: ORIGAMI")
        # elif file_type == "Infrared":
        #     self.data_handling.on_open_single_MassLynx_raw(file_path, "Type: Infrared")
        # elif file_type == "Text":
        #     self.data_handling.on_add_text_2d(None, file_path)
        # elif file_type == "Text_MS":
        #     self.data_handling.on_add_text_ms(path=file_path)

    def on_open_file_from_dnd(self, file_path, file_extension):
        """Open file as it was dropped in the window"""
        raise NotImplementedError("Must implement method")
        # if file_extension in [".pickle", ".pkl"]:
        #     self.data_handling.on_open_document_fcn(None, file_path)
        # elif file_extension == ".raw":
        #     self.data_handling.on_open_single_MassLynx_raw(file_path, "Type: ORIGAMI")
        # elif file_extension in [".txt", ".csv", ".tab"]:
        #     file_format = check_file_type(path=file_path)
        #     if file_format == "2D":
        #         self.data_handling.on_add_text_2d(None, file_path)
        #     else:
        #         self.data_handling.on_add_text_ms(path=file_path)

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

        wx.CallAfter(self.statusbar.set_message, msg, position, delay * 1000)

    @staticmethod
    def on_update_interaction_settings(evt):
        """build and update parameters in the zoom function"""
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
        """Check Driftscope path"""
        check = CONFIG.setup_paths(return_check=True)
        if check:
            wx.Bell()
            DialogBox(
                title="DriftScope path looks good", msg="Found DriftScope on your PC. You are good to go.", kind="Info"
            )
            return


class DragAndDrop(wx.FileDropTarget):
    """Implement Drag-and-Drop support"""

    SUPPORTED_FORMATS = [".raw", ".RAW", ".txt", ".csv", ".tab", ".origami"]
    LEGACY_FORMATS = [".pickle", ".pkl"]

    def __init__(self, parent):
        """Constructor"""
        wx.FileDropTarget.__init__(self)
        self.parent = parent

    def OnDropFiles(self, x, y, filenames):
        """When files are dropped, write where they were dropped and then the file paths themselves"""
        logger.info(f"Dropped {len(filenames)} in the window")
        for filename in filenames:
            logger.info("Opening {filename} file...")
            __, file_extension = os.path.splitext(filename)
            if file_extension in self.SUPPORTED_FORMATS:
                try:
                    self.parent.on_open_file_from_dnd(filename, file_extension)
                except Exception:
                    logger.error("Failed to open {}".format(filename))
                    continue
            elif file_extension in self.LEGACY_FORMATS:
                logger.warning("Dropped file is no longer supported")
            else:
                logger.warning("Dropped file is not supported")
