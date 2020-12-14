"""Main frame module"""
# Standard library imports
import os
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
from origami.ids import ID_window_all
from origami.ids import ID_helpYoutube
from origami.ids import ID_fileMenu_MGF
from origami.ids import ID_helpHomepage
from origami.ids import ID_saveDocument
from origami.ids import ID_fileMenu_mzML
from origami.ids import ID_helpHTMLEditor
from origami.ids import ID_helpNewVersion
from origami.ids import ID_helpReportBugs
from origami.ids import ID_window_ionList
from origami.ids import ID_help_UniDecInfo
from origami.ids import ID_helpNewFeatures
from origami.ids import ID_window_controls
from origami.ids import ID_window_textList
from origami.ids import ID_help_page_UniDec
from origami.ids import ID_help_page_ORIGAMI
from origami.ids import ID_help_page_overlay
from origami.ids import ID_help_page_linearDT
from origami.ids import ID_fileMenu_openRecent
from origami.ids import ID_help_page_OtherData
from origami.ids import ID_window_documentList
from origami.ids import ID_fileMenu_clearRecent
from origami.ids import ID_help_page_dataLoading
from origami.ids import ID_help_page_Interactive
from origami.ids import ID_window_multipleMLList
from origami.ids import ID_checkAtStart_Driftscope
from origami.ids import ID_help_page_multipleFiles
from origami.ids import ID_annotPanel_otherSettings
from origami.ids import ID_help_page_CCScalibration
from origami.ids import ID_help_page_dataExtraction
from origami.ids import ID_help_page_gettingStarted
from origami.ids import ID_help_page_annotatingMassSpectra
from origami.utils.path import clean_directory
from origami.panel_plots import PanelPlots
from origami.icons.assets import Icons
from origami.config.config import CONFIG
from origami.config.enabler import APP_ENABLER
from origami.panel_peaklist import PanelPeaklist
from origami.panel_textlist import PanelTextlist
from origami.utils.utilities import format_time
from origami.panel_multi_file import PanelMultiFile
from origami.config.environment import ENV
from origami.panel_document_tree import PanelDocumentTree
from origami.gui_elements.helpers import make_menu_item
from origami.gui_elements.statusbar import Statusbar
from origami.handlers.data_handling import DataHandling
from origami.handlers.queue_handler import QUEUE
from origami.gui_elements.popup_toast import PopupToastManager
from origami.handlers.data_processing import DataProcessing
from origami.gui_elements.misc_dialogs import DialogBox
from origami.handlers.data_visualisation import DataVisualization
from origami.gui_elements.panel_plot_parameters import PanelVisualisationSettingsEditor
from origami.gui_elements.dialog_notify_open_documents import DialogNotifyOpenDocuments
from origami import events

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
    tool_recent_files = None
    menubar = None
    toolbar = None
    statusbar = None
    toggle_document_page = None
    toggle_peaks_page = None
    toggle_text_page = None
    toggle_manual_page = None
    menu_config_check_driftscope = None
    panel_interactive_output = None
    _toolbar_horizontal = True

    def __init__(self, parent, icons, title: str):
        wx.Frame.__init__(self, None, title=title)

        # Extract size of screen
        self.display_size = wx.GetDisplaySize()
        self.SetSize(0, 0, self.display_size[0], self.display_size[1] - 50)
        self.icons = icons
        self._icons = Icons()
        self.presenter = parent

        self._timer = wx.Timer(self, wx.ID_ANY)
        self._timers = {}

        self.plot_data = {}  # remove
        self.plot_scale = {}  # remove
        self.plot_name = None
        self.plot_id = None
        self._fullscreen = False

        self.SetDropTarget(DragAndDrop(self))

        icon = wx.Icon()
        icon.CopyFromBitmap(self.icons.iconsLib["origamiLogoDark16"])
        self.SetIcon(icon)

        # keep track of which windows are managed
        self._managed_windows = dict()
        self._n_managed_windows = 0
        self._notification_level = "success"

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

        self.panelParametersEdit = PanelVisualisationSettingsEditor(self, self.presenter)

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
            .Show(CONFIG.WINDOW_SETTINGS["Documents"]["show"])
            .CloseButton(CONFIG.WINDOW_SETTINGS["Documents"]["close_button"])
            .CaptionVisible(CONFIG.WINDOW_SETTINGS["Documents"]["caption"])
            .Gripper(CONFIG.WINDOW_SETTINGS["Documents"]["gripper"]),
        )

        self.window_mgr.AddPane(
            self.panelPlots,
            wx.aui.AuiPaneInfo()
            .CenterPane()
            .Caption("Plot")
            .Show(CONFIG.WINDOW_SETTINGS["Plots"]["show"])
            .CloseButton(CONFIG.WINDOW_SETTINGS["Plots"]["close_button"])
            .CaptionVisible(CONFIG.WINDOW_SETTINGS["Plots"]["caption"])
            .Gripper(CONFIG.WINDOW_SETTINGS["Plots"]["gripper"]),
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
            .Show(CONFIG.WINDOW_SETTINGS["Text files"]["show"])
            .CloseButton(CONFIG.WINDOW_SETTINGS["Text files"]["close_button"])
            .CaptionVisible(CONFIG.WINDOW_SETTINGS["Text files"]["caption"])
            .Gripper(CONFIG.WINDOW_SETTINGS["Text files"]["gripper"]),
        )

        self.window_mgr.AddPane(
            self.panelParametersEdit,
            wx.aui.AuiPaneInfo()
            .Right()
            .Caption(CONFIG.WINDOW_SETTINGS["Plot parameters"]["title"])
            .MinSize((350, -1))
            .GripperTop()
            .BottomDockable(True)
            .TopDockable(False)
            .Show(CONFIG.WINDOW_SETTINGS["Plot parameters"]["show"])
            .CloseButton(CONFIG.WINDOW_SETTINGS["Plot parameters"]["close_button"])
            .CaptionVisible(CONFIG.WINDOW_SETTINGS["Plot parameters"]["caption"])
            .Gripper(CONFIG.WINDOW_SETTINGS["Plot parameters"]["gripper"]),
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
        pub.subscribe(self.on_notify_info, events.EVENT_NOTIFY_INFO)
        pub.subscribe(self.on_notify_success, events.EVENT_NOTIFY_SUCCESS)
        pub.subscribe(self.on_notify_warning, events.EVENT_NOTIFY_WARNING)
        pub.subscribe(self.on_notify_error, events.EVENT_NOTIFY_ERROR)
        pub.subscribe(self.on_add_recent_file, events.EVENT_RECENT_FILE)
        pub.subscribe(self.on_update_recent_files, events.EVENT_CONFIG_LOAD)

        # Fire up a couple of events
        self.on_update_panel_config()
        self.on_toggle_panel(evt=None)
        self.on_toggle_panel_at_start()

        # when in development, move the app to another display
        if CONFIG.debug:
            from origami.utils.screen import move_to_different_screen

            move_to_different_screen(self)

        # run action(s) delayed
        self.run_delayed(self._on_check_latest_version)
        self.add_timer_event(self.on_export_config_fcn, "save.config", 120)

    @staticmethod
    def run_delayed(func, *args, delay: int = 3000, **kwargs):
        """Run function using a CallLater"""
        wx.CallLater(delay, func, *args, **kwargs)
        logger.info("Running delayed action...")

    def add_timer_event(self, func, name: str, delay: int = 60):
        """Add an event to the application that will run every `delay` seconds

        Parameters
        ----------
        func : Callable
            function that needs to be updated every `delay` seconds
        name: str
            name of the event so it can be changed at later stage (if necessary)
        delay : int
            amount of time between each update in seconds
        """
        delay = delay * 1000
        timer = wx.Timer(self, wx.ID_ANY)
        timer.Start(delay)
        self.Bind(wx.EVT_TIMER, func, timer)
        self._timers[name] = timer
        logger.info(f"Added `{name}` timed event that will run every {format_time(delay/1000)}.")

    def remove_timer_event(self, name: str):
        """Remove timer event from the application"""
        if name in self._timers:
            timer = self._timers.pop(name)
            timer.Stop()
            logger.info(f"Removed `{name}` timed event from the application.")

    def update_timer_event(self, name: str, delay: int = 60):
        """Update frequency of a timer event"""
        if name in self._timers:
            delay = delay * 1000
            if delay == self._timers[name].GetInterval():
                self._timers[name].Stop()
                self._timers[name].Start(delay)

    def on_notify(self, message: str, kind: str = "info", delay: int = 3000):
        """Notify user of some event"""
        # restricts notifications based on user settings
        notification_levels = {"success": 10, "info": 20, "warning": 30, "error": 40}
        app_level = notification_levels[self._notification_level]
        kind_level = notification_levels[kind.lower()]
        if kind_level >= app_level:
            wx.CallAfter(self.popup_mgr.show_popup, message, kind, delay)

    def on_notify_info(self, message: str):
        """Notify user of event using INFO style"""
        self.on_notify(message)

    def on_notify_success(self, message: str):
        """Notify user of event using INFO style"""
        self.on_notify(message, "success")

    def on_notify_warning(self, message: str):
        """Notify user of event using INFO style"""
        self.on_notify(message, "warning")

    def on_notify_error(self, message: str):
        """Notify user of event using INFO style"""
        self.on_notify(message, "error")

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
        CONFIG.WINDOW_SETTINGS["Documents"]["id"] = ID_window_documentList

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
        if panel_name in CONFIG.WINDOW_SETTINGS:
            CONFIG.WINDOW_SETTINGS[panel_name]["show"] = False

            # fire-up events
            try:
                evt_id = self.on_get_toggle_id(panel=evt.GetPane().caption)
                self.on_toggle_panel(evt=evt_id)
            except Exception:
                pass

    def on_restored_page(self, evt):
        """Keep track of which page was restored"""
        # Keep track of which window is restored
        CONFIG.WINDOW_SETTINGS[evt.GetPane().caption]["show"] = True
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
        menu_file.Append(ID_fileMenu_openRecent, "Open Recent", self.menu_recent_files)
        menu_file.AppendSeparator()

        menu_file_load_origami = make_menu_item(
            parent=menu_file, text="Open ORIGAMI Document (.origami)", bitmap=self._icons.open
        )
        menu_file.Append(menu_file_load_origami)

        # menu_file_load_pickle = make_menu_item(
        #     parent=menu_file,
        #     evt_id=ID_openDocument,
        #     text="Open ORIGAMI Document file (.pickle) [LEGACY]",
        #     bitmap=self.icons.iconsLib["open_project_16"],
        # )
        # menu_file_load_pickle.Enable(False)
        # menu_file.Append(menu_file_load_pickle)
        menu_file.AppendSeparator()
        menu_file_import_data = menu_file.Append(
            make_menu_item(parent=menu_file, text="Open any allowed file", bitmap=self._icons.wand)
        )

        menu_file_waters_ms = menu_file.Append(
            make_menu_item(
                parent=menu_file, text="Open Waters file (.raw) [MS only]\tCtrl+Shift+M", bitmap=self._icons.micromass
            )
        )
        menu_file_waters_ms.Enable(APP_ENABLER.ALLOW_WATERS_EXTRACTION)

        menu_file_waters_imms = menu_file.Append(
            make_menu_item(parent=menu_file, text="Open Waters file (.raw) [IM-MS]", bitmap=self._icons.micromass)
        )
        menu_file_waters_imms.Enable(APP_ENABLER.ALLOW_WATERS_EXTRACTION)

        menu_open_origami = menu_file.Append(
            make_menu_item(
                parent=menu_file, text="Open Waters file (.raw) [ORIGAMI-MS; CIU]\tCtrl+R", bitmap=self._icons.micromass
            )
        )
        menu_open_origami.Enable(APP_ENABLER.ALLOW_WATERS_EXTRACTION)

        menu_file.AppendSeparator()
        menu_open_thermo = menu_file.Append(
            make_menu_item(parent=menu_file, text="Open Thermo file (.RAW)\tCtrl+Shift+Y", bitmap=self._icons.thermo)
        )
        menu_open_thermo.Enable(APP_ENABLER.ALLOW_THERMO_EXTRACTION)

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
        menu_file.Append(wx.ID_ANY, "Open MS/MS files...", menu_tandem)
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
        menu_plot_general = make_menu_item(
            parent=menu_plot, text="Settings: Plot &General", bitmap=self._icons.switch_on
        )
        menu_plot.Append(menu_plot_general)

        menu_plot_1d = make_menu_item(parent=menu_plot, text="Settings: Plot &1D", bitmap=self._icons.plot_1d)
        menu_plot.Append(menu_plot_1d)

        menu_plot_2d = make_menu_item(
            parent=menu_plot, text="Settings: Plot &2D", bitmap=self.icons.iconsLib["panel_plot2D_16"]
        )
        menu_plot.Append(menu_plot_2d)

        menu_plot_3d = make_menu_item(
            parent=menu_plot, text="Settings: Plot &3D", bitmap=self.icons.iconsLib["panel_plot3D_16"]
        )
        menu_plot.Append(menu_plot_3d)

        menu_plot_colorbar = make_menu_item(
            parent=menu_plot, text="Settings: &Colorbar", bitmap=self._icons.plot_colorbar
        )
        menu_plot.Append(menu_plot_colorbar)

        menu_plot_legend = make_menu_item(parent=menu_plot, text="Settings: &Legend", bitmap=self._icons.plot_legend)
        menu_plot.Append(menu_plot_legend)

        menu_plot_waterfall = menu_plot.Append(
            make_menu_item(parent=menu_plot, text="Settings: &Waterfall", bitmap=self._icons.waterfall)
        )

        menu_plot_violin = menu_plot.Append(
            make_menu_item(parent=menu_plot, text="Settings: &Violin", bitmap=self._icons.violin)
        )

        menu_plot_ui = menu_plot.Append(make_menu_item(parent=menu_plot, text="Settings: &UI", bitmap=self._icons.gear))

        menu_plot.AppendSeparator()
        menu_plot.Append(
            make_menu_item(parent=menu_plot, evt_id=ID_annotPanel_otherSettings, text="Settings: Annotation parameters")
        )
        self.menubar.Append(menu_plot, "&Plot settings")

        # WIDGETS MENU
        menu_widgets = wx.Menu()
        menu_widget_bokeh = make_menu_item(
            parent=menu_widgets, text="Open &interactive output panel...\tShift+Z", bitmap=self._icons.bokeh
        )
        menu_widgets.Append(menu_widget_bokeh)
        menu_widget_bokeh_new = make_menu_item(
            parent=menu_widgets, text="Open &Interactive Output Builder...", bitmap=self._icons.bokeh
        )
        menu_widgets.Append(menu_widget_bokeh_new)

        #         menu_widgets.Append(
        #             make_menu_item(parent=menu_widgets, evt_id=ID_docTree_plugin_UVPD, text="Open UVPD
        # processing window...")
        #         )
        #         menu_widgets.Append(
        #             make_menu_item(parent=menu_widgets, evt_id=ID_docTree_plugin_MSMS, text="Open MS/MS window...")
        #         )

        menu_widgets.AppendSeparator()
        # add spectrum comparison
        menu_widget_compare_ms = menu_widgets.Append(
            make_menu_item(
                parent=menu_widgets, text="Open spectrum comparison window...", bitmap=self._icons.compare_ms
            )
        )
        # add overlay sub-menu
        menu_widget_overlay_viewer = make_menu_item(parent=menu_widgets, text="Open Overlay Builder...\tShift+O")
        menu_widgets.Append(menu_widget_overlay_viewer)

        # add ccs builder menu
        menu_widgets.AppendSeparator()
        menu_widget_ccs_builder = menu_widgets.Append(
            make_menu_item(parent=menu_widgets, text="Open CCS Calibration Builder...", bitmap=self._icons.target)
        )
        menu_widget_ccs_builder.Enable(APP_ENABLER.ALLOW_WATERS_EXTRACTION)
        menu_config_show_ccs_db = menu_widgets.Append(
            make_menu_item(parent=menu_widgets, text="Show CCS calibrants", bitmap=self._icons.list)
        )

        # add manual activation sub-menu
        menu_widgets.AppendSeparator()
        menu_widget_ciu_import = menu_widgets.Append(
            make_menu_item(parent=menu_widgets, text="Open Manual CIU import manager...")
        )
        menu_widget_ciu_import.Enable(APP_ENABLER.ALLOW_WATERS_EXTRACTION)

        menu_widget_sid_import = menu_widgets.Append(
            make_menu_item(parent=menu_widgets, text="Open Manual SID import manager...")
        )
        menu_widget_sid_import.Enable(APP_ENABLER.ALLOW_WATERS_EXTRACTION)

        # add lesa activation sub-menu
        menu_widgets.AppendSeparator()
        menu_widget_lesa_import = menu_widgets.Append(
            make_menu_item(parent=menu_widgets, text="Open LESA import manager...\tCtrl+L")
        )
        menu_widget_lesa_import.Enable(APP_ENABLER.ALLOW_WATERS_EXTRACTION)

        menu_widget_lesa_viewer = menu_widgets.Append(
            make_menu_item(parent=menu_widgets, text="Open LESA imaging window...\tShift+L")
        )
        menu_widget_lesa_viewer.Enable(APP_ENABLER.ALLOW_WATERS_EXTRACTION)

        self.menubar.Append(menu_widgets, "&Widgets")

        # CONFIG MENU
        menu_config = wx.Menu()
        menu_config_export = make_menu_item(
            parent=menu_config, text="Save configuration file (default location)", bitmap=self._icons.export_db
        )
        menu_config.Append(menu_config_export)

        menu_config_export_as = make_menu_item(parent=menu_config, text="Save configuration file as...")
        menu_config.Append(menu_config_export_as)

        menu_config_import = make_menu_item(
            parent=menu_config, text="Load configuration file (default location)", bitmap=self._icons.import_db
        )
        menu_config.Append(menu_config_import)

        menu_config_import_as = make_menu_item(parent=menu_config, text="Load configuration file from...")
        menu_config.Append(menu_config_import_as)

        menu_config_open_dir = make_menu_item(parent=menu_config, text="Show Configs in Explorer")
        menu_config.Append(menu_config_open_dir)
        menu_config.AppendSeparator()
        self.menu_config_check_driftscope = menu_config.Append(
            ID_checkAtStart_Driftscope, "Look for DriftScope at start", kind=wx.ITEM_CHECK
        )
        self.menu_config_check_driftscope.Check(CONFIG.APP_CHECK_DRIFTSCOPE_PATH_AT_START)
        menu_config_driftscope = make_menu_item(
            parent=menu_config, text="Check DriftScope path", bitmap=self._icons.driftscope
        )
        menu_config.Append(menu_config_driftscope)

        menu_logging = wx.Menu()
        menu_log_open_dir = make_menu_item(parent=menu_config, text="Show Log in Explorer")
        menu_log_debug = menu_logging.AppendRadioItem(wx.ID_ANY, "Logging: DEBUG")
        menu_log_info = menu_logging.AppendRadioItem(wx.ID_ANY, "Logging: INFO")
        menu_log_warning = menu_logging.AppendRadioItem(wx.ID_ANY, "Logging: WARNING")
        menu_log_error = menu_logging.AppendRadioItem(wx.ID_ANY, "Logging: ERROR")
        menu_log_critical = menu_logging.AppendRadioItem(wx.ID_ANY, "Logging: CRITICAL")
        menu_logging.AppendSeparator()
        menu_logging.Append(menu_log_open_dir)

        self.Bind(wx.EVT_MENU, self.on_log_change_level, menu_log_debug)
        self.Bind(wx.EVT_MENU, self.on_log_change_level, menu_log_info)
        self.Bind(wx.EVT_MENU, self.on_log_change_level, menu_log_warning)
        self.Bind(wx.EVT_MENU, self.on_log_change_level, menu_log_error)
        self.Bind(wx.EVT_MENU, self.on_log_change_level, menu_log_critical)
        self.Bind(wx.EVT_MENU, self.on_log_open_dir, menu_log_open_dir)

        menu_notifications = wx.Menu()
        menu_notify_success = menu_notifications.AppendRadioItem(wx.ID_ANY, "Notification: SUCCESS")
        menu_notify_info = menu_notifications.AppendRadioItem(wx.ID_ANY, "Notification: INFO")
        menu_notify_warning = menu_notifications.AppendRadioItem(wx.ID_ANY, "Notification: WARNING")
        menu_notify_error = menu_notifications.AppendRadioItem(wx.ID_ANY, "Notification: ERROR")

        self.Bind(wx.EVT_MENU, self.on_notify_change_level, menu_notify_success)
        self.Bind(wx.EVT_MENU, self.on_notify_change_level, menu_notify_info)
        self.Bind(wx.EVT_MENU, self.on_notify_change_level, menu_notify_warning)
        self.Bind(wx.EVT_MENU, self.on_notify_change_level, menu_notify_error)

        menu_config.AppendSeparator()
        menu_config.Append(wx.ID_ANY, "Logging", menu_logging)
        menu_config.Append(wx.ID_ANY, "Notifications", menu_notifications)

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
        menu_view_toolbar_horizontal = make_menu_item(parent=menu_view, text="Toolbar: Horizontal")
        menu_view.Append(menu_view_toolbar_horizontal)
        menu_view_toolbar_vertical = make_menu_item(parent=menu_view, text="Toolbar: Vertical")
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
        menu_help.Append(wx.ID_ANY, "Help pages...", menu_help_pages)
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
        menu_help.Append(wx.ID_ANY, "About other software...", menu_software)
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
        self.Bind(wx.EVT_MENU, self.on_close, menu_file_exit)

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
        self.Bind(wx.EVT_MENU, self.panelDocuments.documents.on_save_document, id=ID_saveDocument)
        self.Bind(wx.EVT_MENU, self.data_handling.on_open_multiple_text_ms_fcn, menu_file_text_ms)
        self.Bind(wx.EVT_MENU, self.data_handling.on_open_single_clipboard_ms, menu_file_clipboard_ms)
        self.Bind(wx.EVT_MENU, self.data_handling.on_open_mgf_file_fcn, id=ID_fileMenu_MGF)
        self.Bind(wx.EVT_MENU, self.data_handling.on_open_mzml_file_fcn, id=ID_fileMenu_mzML)
        self.Bind(wx.EVT_MENU, self.data_handling.on_open_thermo_file_fcn, menu_open_thermo)
        self.Bind(wx.EVT_MENU, self.data_handling.on_open_waters_raw_ms_fcn, menu_file_waters_ms)
        self.Bind(wx.EVT_MENU, self.data_handling.on_open_waters_raw_imms_fcn, menu_file_waters_imms)
        self.Bind(wx.EVT_MENU, self.data_handling.on_open_waters_raw_imms_fcn, menu_open_origami)
        self.Bind(wx.EVT_MENU, self.on_open_new_file, menu_file_import_data)

        # PLOT
        self.Bind(wx.EVT_MENU, partial(self.on_open_plot_settings_panel, "General"), menu_plot_general)
        self.Bind(wx.EVT_MENU, partial(self.on_open_plot_settings_panel, "Colorbar"), menu_plot_colorbar)
        self.Bind(wx.EVT_MENU, partial(self.on_open_plot_settings_panel, "Legend"), menu_plot_legend)
        self.Bind(wx.EVT_MENU, partial(self.on_open_plot_settings_panel, "Plot 1D"), menu_plot_1d)
        self.Bind(wx.EVT_MENU, partial(self.on_open_plot_settings_panel, "Plot 2D"), menu_plot_2d)
        self.Bind(wx.EVT_MENU, partial(self.on_open_plot_settings_panel, "Plot 3D"), menu_plot_3d)
        self.Bind(wx.EVT_MENU, partial(self.on_open_plot_settings_panel, "Waterfall"), menu_plot_waterfall)
        self.Bind(wx.EVT_MENU, partial(self.on_open_plot_settings_panel, "Violin"), menu_plot_violin)
        self.Bind(wx.EVT_MENU, partial(self.on_open_plot_settings_panel, "UI behaviour"), menu_plot_ui)

        self.Bind(wx.EVT_MENU, self.on_customise_annotation_plot_parameters, id=ID_annotPanel_otherSettings)

        # OUTPUT
        self.Bind(wx.EVT_MENU, self.on_open_interactive_output_panel, menu_widget_bokeh)
        #         self.Bind(wx.EVT_MENU, self.on_open_interactive_output_panel_new, menu_widget_bokeh_new)

        # UTILITIES
        self.Bind(wx.EVT_MENU, self.panelDocuments.documents.on_open_lesa_viewer, menu_widget_lesa_viewer)
        self.Bind(wx.EVT_MENU, self.panelDocuments.documents.on_import_lesa_dataset, menu_widget_lesa_import)
        self.Bind(wx.EVT_MENU, self.panelDocuments.documents.on_open_ccs_builder, menu_widget_ccs_builder)
        self.Bind(
            wx.EVT_MENU, partial(self.panelDocuments.documents.on_import_manual_dataset, "SID"), menu_widget_sid_import
        )
        self.Bind(
            wx.EVT_MENU, partial(self.panelDocuments.documents.on_import_manual_dataset, "CIU"), menu_widget_ciu_import
        )
        self.Bind(wx.EVT_MENU, self.panelDocuments.documents.on_open_overlay_editor, menu_widget_overlay_viewer)
        self.Bind(wx.EVT_MENU, self.panelDocuments.documents.on_open_interactive_editor, menu_widget_bokeh_new)

        # CONFIG MENU
        self.Bind(wx.EVT_MENU, self.on_export_config_fcn, menu_config_export)
        self.Bind(wx.EVT_MENU, self.on_export_config_as_fcn, menu_config_export_as)
        self.Bind(wx.EVT_MENU, self.on_import_config_fcn, menu_config_import)
        self.Bind(wx.EVT_MENU, self.on_import_config_as_fcn, menu_config_import_as)
        self.Bind(wx.EVT_MENU, self.on_config_open_dir, menu_config_open_dir)
        self.Bind(wx.EVT_MENU, self.on_check_driftscope_path, menu_config_driftscope)
        self.Bind(wx.EVT_MENU, self.on_show_ccs_database, menu_config_show_ccs_db)
        self.Bind(wx.EVT_MENU, self.on_check_in_menu, id=ID_checkAtStart_Driftscope)

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
    def on_log_change_level(evt):
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
        pub.sendMessage("notify.message.success", message=f"Changed logging level to `{level}`")

    def on_notify_change_level(self, evt):
        """Change notification level"""
        name = evt.GetEventObject().FindItemById(evt.GetId()).GetItemLabel()
        level = {
            "Notification: SUCCESS": "success",
            "Notification: INFO": "info",
            "Notification: WARNING": "warning",
            "Notification: ERROR": "error",
        }.get(name, "success")
        self._notification_level = level
        self.on_notify(f"Changed notification level so only messages with priority >= `{level}` will be shown", level)

    def on_log_open_dir(self, _evt):
        """Open log directory"""
        if CONFIG.APP_LOG_DIR is not None:
            self.data_handling.on_open_directory(CONFIG.APP_LOG_DIR)

    def on_config_open_dir(self, _evt):
        """Open config directory"""
        if CONFIG.APP_CONFIG_DIR is not None:
            self.data_handling.on_open_directory(CONFIG.APP_CONFIG_DIR)

    def on_open_new_file(self, _evt):
        """Import dataset"""
        from origami.gui_elements.panel_data_import import PanelDatasetImport

        dlg = PanelDatasetImport(self, self._icons, self.presenter)
        dlg.Show()

    def on_customise_annotation_plot_parameters(self, _evt):
        """Open dialog to customise user annotations parameters"""
        from origami.gui_elements.dialog_customise_user_annotations import DialogCustomiseUserAnnotations

        dlg = DialogCustomiseUserAnnotations(self)
        dlg.ShowModal()

    @staticmethod
    def on_import_config_fcn(_evt):
        """Load configuration file from the default path"""
        config_path = os.path.join(CONFIG.APP_CWD, CONFIG.DEFAULT_CONFIG_NAME)
        QUEUE.add_call(CONFIG.load_config, (config_path,))

    def on_import_config_as_fcn(self, _evt):
        """Load configuration file from the user-defined path"""
        dlg = wx.FileDialog(
            self,
            "Load configuration file as...",
            wildcard="JavaScript Object Notation format (.json) | *.json",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        )

        dlg.SetFilename(CONFIG.DEFAULT_CONFIG_NAME)

        config_path = None
        if dlg.ShowModal() == wx.ID_OK:
            config_path = dlg.GetPath()

        if config_path is None:
            return
        QUEUE.add_call(CONFIG.load_config, (config_path,))

    @staticmethod
    def on_export_config_fcn(_evt):
        """Import configuration file"""
        config_path = os.path.join(CONFIG.APP_CONFIG_DIR, CONFIG.DEFAULT_CONFIG_NAME)
        QUEUE.add_call(CONFIG.save_config, (config_path,))

    def on_export_config_as_fcn(self, _evt):
        """Save configuration file to a user-defined path"""
        dlg = wx.FileDialog(
            self,
            "Import configuration file...",
            wildcard="JavaScript Object Notation format (.json) | *.json",
            style=wx.FD_DEFAULT_STYLE | wx.FD_CHANGE_DIR,
        )
        config_path = None
        if dlg.ShowModal() == wx.ID_OK:
            config_path = dlg.GetPath()

        if config_path is None:
            return
        QUEUE.add_call(CONFIG.save_config, (config_path,))

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
            webbrowser.open(link)
        except KeyError:
            logger.warning("Could not open requested link")

    def on_check_latest_version(self, _evt):
        """Manually check for latest version of ORIGAMI"""
        self._on_check_latest_version(silent=False)

    def _on_check_latest_version(self, silent: bool = True):
        """Simple function to check whether this is the newest version available"""
        from origami.gui_elements.panel_notify_new_version import get_version_information, inform_version

        QUEUE.add_call(get_version_information, args=(), func_result=inform_version, silent=silent, parent=self)

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
            check_value = not CONFIG.APP_CHECK_DRIFTSCOPE_PATH_AT_START
            CONFIG.APP_CHECK_DRIFTSCOPE_PATH_AT_START = check_value
            self.menu_config_check_driftscope.Check(check_value)

    def on_set_window_maximize(self, _evt):
        """Maximize app."""
        self.Maximize()

    def on_set_window_iconize(self, _evt):
        """Iconize app."""
        self.Iconize()

    def on_set_window_fullscreen(self, _evt):
        """Fullscreen app."""
        self._fullscreen = not self._fullscreen
        self.ShowFullScreen(self._fullscreen, style=wx.FULLSCREEN_NOBORDER | wx.FULLSCREEN_NOCAPTION)

    def on_rotate_toolbar(self, _evt):
        """Flip toolbar to be horizontal or vertical"""
        self._toolbar_horizontal = not self._toolbar_horizontal
        self.on_set_toolbar()

    def on_set_toolbar(self):
        """Set toolbar"""
        if self._toolbar_horizontal:
            self.on_set_toolbar_horizontal(None)
        else:
            self.on_set_toolbar_vertical(None)

    def on_set_toolbar_vertical(self, _evt):
        """Destroy the old-toolbar and create a new instance in a vertical position"""
        self.toolbar.Destroy()
        self.make_toolbar(wx.TB_VERTICAL)

    def on_set_toolbar_horizontal(self, _evt):
        """Destroy the old-toolbar and create a new instance in a horizontal position"""
        self.toolbar.Destroy()
        self.make_toolbar()

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

    def on_open_recent_files_menu(self, _evt):
        """Open menu to load MGF/mzML file(s)"""

        menu = wx.Menu()
        self.set_recent_files_menu(menu)
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

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

        self.tool_recent_files = self.toolbar.AddTool(
            wx.ID_ANY, "", self._icons.hourglass, shortHelp="Open recent files...", kind=wx.ITEM_DROPDOWN
        )
        self.toolbar.SetDropdownMenu(self.tool_recent_files.GetId(), wx.Menu())
        self.toolbar.AddSeparator()

        tool_open_document = self.toolbar.AddTool(wx.ID_ANY, "", self._icons.open, shortHelp="Open ORIGAMI document...")
        self.toolbar.AddSeparator()

        tool_config_export = self.toolbar.AddTool(
            wx.ID_ANY, "", self._icons.export_db, shortHelp="Export configuration file..."
        )

        tool_config_import = self.toolbar.AddTool(
            wx.ID_ANY, "", self._icons.export_db, shortHelp="Import configuration file..."
        )

        self.toolbar.AddSeparator()

        tool_import_data = self.toolbar.AddTool(wx.ID_ANY, "", self._icons.wand, shortHelp="Open any allowed file")
        self.Bind(wx.EVT_TOOL, self.on_open_new_file, tool_import_data)

        tool_open_masslynx = self.toolbar.AddTool(
            wx.ID_ANY, "", self._icons.micromass, shortHelp="Open MassLynx file (.raw)"
        )
        tool_open_masslynx.Enable(APP_ENABLER.ALLOW_WATERS_EXTRACTION)

        tool_open_thermo = self.toolbar.AddTool(wx.ID_ANY, "", self._icons.thermo, shortHelp="Open Thermo file (.RAW)")
        tool_open_thermo.Enable(APP_ENABLER.ALLOW_THERMO_EXTRACTION)

        tool_open_multiple = self.toolbar.AddTool(
            wx.ID_ANY, "", self.icons.iconsLib["open_masslynxMany_16"], shortHelp="Open multiple MassLynx files (.raw)"
        )
        tool_open_multiple.Enable(APP_ENABLER.ALLOW_WATERS_EXTRACTION)

        self.toolbar.AddSeparator()
        tool_open_text_heatmap = self.toolbar.AddTool(
            wx.ID_ANY, "", self.icons.iconsLib["open_textMany_16"], shortHelp="Open one (or more) heatmap text file"
        )
        self.Bind(wx.EVT_TOOL, self.data_handling.on_open_multiple_text_2d_fcn, tool_open_text_heatmap)

        self.toolbar.AddSeparator()

        tool_open_msms = self.toolbar.AddTool(
            wx.ID_ANY, "", self.icons.iconsLib["ms16"], shortHelp="Open MS/MS files...", kind=wx.ITEM_DROPDOWN
        )
        self.toolbar.SetDropdownMenu(tool_open_msms.GetId(), wx.Menu())
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
        tool_action_global = self.toolbar.AddTool(
            wx.ID_ANY, "", self._icons.switch_on, shortHelp="Settings: General plot"
        )
        tool_action_1d = self.toolbar.AddTool(wx.ID_ANY, "", self._icons.plot_1d, shortHelp="Settings: Plot 1D panel")
        tool_action_2d = self.toolbar.AddTool(
            wx.ID_ANY, "", self.icons.iconsLib["panel_plot2D_16"], shortHelp="Settings: Plot 2D panel"
        )
        tool_action_3d = self.toolbar.AddTool(
            wx.ID_ANY, "", self.icons.iconsLib["panel_plot3D_16"], shortHelp="Settings: Plot 3D panel"
        )
        tool_action_colorbar = self.toolbar.AddTool(
            wx.ID_ANY, "", self._icons.plot_colorbar, shortHelp="Settings: Colorbar panel"
        )
        tool_action_legend = self.toolbar.AddTool(
            wx.ID_ANY, "", self._icons.plot_legend, shortHelp="Settings: Legend panel"
        )
        tool_action_waterfall = self.toolbar.AddTool(
            wx.ID_ANY, "", self._icons.waterfall, shortHelp="Settings: Waterfall panel"
        )
        tool_action_violin = self.toolbar.AddTool(wx.ID_ANY, "", self._icons.violin, shortHelp="Settings: Violin panel")
        tool_action_ui = self.toolbar.AddTool(wx.ID_ANY, "", self._icons.gear, shortHelp="Settings: Extra panel")
        self.toolbar.AddSeparator()

        tool_action_bokeh = self.toolbar.AddTool(
            wx.ID_ANY, "", self._icons.bokeh, shortHelp="Open interactive output panel"
        )

        self.toolbar.AddStretchableSpace()
        tool_action_fullscreen = self.toolbar.AddTool(
            wx.ID_ANY, "", self._icons.fullscreen, shortHelp="Toggle fullscreen\tAlt+F11"
        )

        tool_action_rotate = self.toolbar.AddTool(
            wx.ID_ANY, "", self._icons.rotate, shortHelp="Rotate the toolbar to be horizontal or vertical"
        )

        # bind actions
        self.Bind(wx.EVT_MENU, self.on_set_window_fullscreen, tool_action_fullscreen)
        self.Bind(wx.EVT_TOOL, self.on_open_recent_files_menu, self.tool_recent_files)
        self.Bind(wx.EVT_TOOL_DROPDOWN, self.on_open_recent_files_menu, self.tool_recent_files)
        self.Bind(wx.EVT_TOOL, self.data_handling.on_open_origami_document, tool_open_document)
        self.Bind(wx.EVT_TOOL, self.on_export_config_fcn, tool_config_export)
        self.Bind(wx.EVT_TOOL, self.on_import_config_fcn, tool_config_import)
        self.Bind(wx.EVT_TOOL, self.data_handling.on_open_waters_raw_imms_fcn, tool_open_masslynx)
        self.Bind(wx.EVT_TOOL, self.on_open_new_file, tool_import_data)
        self.Bind(wx.EVT_TOOL, self.data_handling.on_open_thermo_file_fcn, tool_open_thermo)
        self.Bind(wx.EVT_TOOL, self.on_open_source_menu, tool_open_msms)
        self.Bind(wx.EVT_TOOL_DROPDOWN, self.on_open_source_menu, tool_open_msms)
        self.Bind(wx.EVT_MENU, self.panelDocuments.documents.on_open_interactive_editor, tool_action_bokeh)
        self.Bind(wx.EVT_MENU, self.on_rotate_toolbar, tool_action_rotate)
        self.Bind(wx.EVT_MENU, partial(self.on_open_plot_settings_panel, "General"), tool_action_global)
        self.Bind(wx.EVT_MENU, partial(self.on_open_plot_settings_panel, "Plot 1D"), tool_action_1d)
        self.Bind(wx.EVT_MENU, partial(self.on_open_plot_settings_panel, "Plot 2D"), tool_action_2d)
        self.Bind(wx.EVT_MENU, partial(self.on_open_plot_settings_panel, "Plot 3D"), tool_action_3d)
        self.Bind(wx.EVT_MENU, partial(self.on_open_plot_settings_panel, "Colorbar"), tool_action_colorbar)
        self.Bind(wx.EVT_MENU, partial(self.on_open_plot_settings_panel, "Legend"), tool_action_legend)
        self.Bind(wx.EVT_MENU, partial(self.on_open_plot_settings_panel, "Waterfall"), tool_action_waterfall)
        self.Bind(wx.EVT_MENU, partial(self.on_open_plot_settings_panel, "Violin"), tool_action_violin)
        self.Bind(wx.EVT_MENU, partial(self.on_open_plot_settings_panel, "UI behaviour"), tool_action_ui)

        # Actually realise the toolbar
        self.toolbar.Realize()

    def on_toggle_panel(self, evt, check=None):
        """Toggle panel"""
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
                    CONFIG.WINDOW_SETTINGS["Documents"]["show"] = True
                else:
                    self.window_mgr.GetPane(self.panelDocuments).Hide()
                    CONFIG.WINDOW_SETTINGS["Documents"]["show"] = False
                self.toggle_document_page.Check(CONFIG.WINDOW_SETTINGS["Documents"]["show"])
                self.on_find_toggle_by_id(find_id=evt_id, check=CONFIG.WINDOW_SETTINGS["Documents"]["show"])
            elif evt_id == ID_window_all:
                for key in CONFIG.WINDOW_SETTINGS:
                    CONFIG.WINDOW_SETTINGS[key]["show"] = True

                self.on_find_toggle_by_id(check_all=True)

                for panel in [self.panelDocuments]:  # , self.panelMML, self.panelMultipleIons, self.panelMultipleText]:
                    self.window_mgr.GetPane(panel).Show()

                self.toggle_document_page.Check(CONFIG.WINDOW_SETTINGS["Documents"]["show"])

        # Checking at start of program
        else:
            if not self.panelDocuments.IsShown():
                CONFIG.WINDOW_SETTINGS["Documents"]["show"] = False

            self.toggle_document_page.Check(CONFIG.WINDOW_SETTINGS["Documents"]["show"])

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

    def on_close(self, _evt, **kwargs):
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
            path = os.path.join(CONFIG.APP_CONFIG_DIR, CONFIG.DEFAULT_CONFIG_NAME)
            CONFIG.save_config(path=path)
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
            if CONFIG.APP_TEMP_DATA_PATH is not None:
                clean_directory(CONFIG.APP_TEMP_DATA_PATH)
                print("Cleared {} from temporary files.".format(CONFIG.APP_TEMP_DATA_PATH))
        except Exception as err:
            print(err)

        # Aggressive way to kill the ORIGAMI process (grrr)
        if not kwargs.get("clean_exit", False):
            try:
                p = psutil.Process(CONFIG.APP_PROCESS_ID)
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

    def on_open_plot_settings_panel(self, window: str = None, _evt=None):
        """Open plot settings

        Parameters
        ----------
        window : str
            name of the panel that should be displayed. Acceptable values include:
            General, Plot 1D, Plot 2D, Plot 3D, Colorbar, Legend, Waterfall, Violin, UI
        _evt : wx.Event
            unused
        """

        if isinstance(window, str):
            window = window

        if window is None:
            return

        if not self.panelParametersEdit.IsShown() or not CONFIG.WINDOW_SETTINGS["Plot parameters"]["show"]:
            if CONFIG.WINDOW_SETTINGS["Plot parameters"]["floating"]:
                self.window_mgr.GetPane(self.panelParametersEdit).Float()

            self.window_mgr.GetPane(self.panelParametersEdit).Show()
            CONFIG.WINDOW_SETTINGS["Plot parameters"]["show"] = True
            self.panelParametersEdit.on_set_page(window)
            self.window_mgr.Update()
        else:
            logger.debug(f"An instance of this panel is already open - changing page to {window}")
            self.panelParametersEdit.on_set_page(window)
            return

    def on_open_interactive_output_panel(self, evt):
        """Open interactive panel"""
        from origami.widgets.interactive._panel_interactive_creator import PanelInteractiveCreator

        def _startup_module():
            """Initialize the panel"""
            CONFIG.interactiveParamsWindow_on_off = True
            self.panel_interactive_output = PanelInteractiveCreator(self, self.icons, self.presenter, CONFIG)
            self.panel_interactive_output.Show()

        _startup_module()

    #         if not hasattr(self, "panel_interactive_output"):
    #             _startup_module()
    #         else:
    #             try:
    #                 if CONFIG.interactiveParamsWindow_on_off:
    #                     self.panel_interactive_output.onUpdateList()
    #                     args = ("An instance of this panel is already open", 4)
    #                     self.presenter.onThreading(evt, args, action="updateStatusbar")
    #                     return
    #             except (IndexError, ValueError, TypeError, KeyError):
    #                 logging.error("Failed to startup `Interactive Output` panel", exc_info=True)
    #                 _startup_module()

    def on_open_interactive_output_panel_new(self, evt):
        """Open interactive panel"""
        from origami.widgets.interactive.panel_interactive_editor import PanelInteractiveEditor

        def _startup_module():
            """Initialize the panel"""
            CONFIG.interactiveParamsWindow_on_off = True
            if self.panel_interactive_output:
                self.panel_interactive_output.Show()
            else:
                self.panel_interactive_output = PanelInteractiveEditor(self, self.presenter)
                self.panel_interactive_output.Show()

        _startup_module()

    def on_show_ccs_database(self, _evt):
        """Show CCS database"""
        from origami.widgets.ccs.panel_ccs_database import PanelCCSDatabase

        dlg = PanelCCSDatabase(self)
        dlg.Show()

    def on_add_recent_file(self, action: str, path: str):
        """Add a file to list of recent files

        Parameters
        ----------
        action : str
            name of the action that will be executed when user request recent file
        path : str
            path to the file/directory that was recently opened
        """
        if len(CONFIG.recent_files) > 9:
            CONFIG.recent_files = CONFIG.recent_files[-9::]

        # check whether the path and action is already present in the file list
        present = False
        for recent_file in CONFIG.recent_files:
            if path == recent_file["path"] and recent_file["action"] == action:
                present = True

        if not present:
            CONFIG.recent_files.append({"path": path, "action": action})
        self.on_update_recent_files()

    def set_recent_files_menu(self, menu):
        """Set recent files items in a menu or toolbar"""
        # clear menu
        for item in menu.GetMenuItems():
            menu.Delete(item.GetId())

        # populate menu
        for i, __ in enumerate(CONFIG.recent_files, start=1):
            if i > 9:
                continue
            document_id = eval("wx.ID_FILE" + str(i))
            path = CONFIG.recent_files[i - 1]["path"]
            menu.Insert(i - 1, document_id, path, "Open Document")
            self.Bind(wx.EVT_MENU, self.on_open_recent_file, id=document_id)
            if not os.path.exists(path):
                menu.Enable(document_id, False)

        # append clear
        if len(CONFIG.recent_files) > 0:
            menu.AppendSeparator()

        # add an option to clear the menu
        menu.Append(ID_fileMenu_clearRecent, "Clear Menu", "Clear recent items")
        self.Bind(wx.EVT_MENU, self.on_clear_recent_files, id=ID_fileMenu_clearRecent)

    def on_update_recent_files(self):
        """Update the list of recent files that is shown in the `File` menu"""
        self.set_recent_files_menu(self.menu_recent_files)
        #         # clear menu
        #         for item in self.menu_recent_files.GetMenuItems():
        #             self.menu_recent_files.Delete(item.GetId())
        #
        #         # populate menu
        #         for i, __ in enumerate(CONFIG.recent_files, start=1):
        #             document_id = eval("wx.ID_FILE" + str(i))
        #             path = CONFIG.recent_files[i - 1]["path"]
        #             self.menu_recent_files.Insert(i - 1, document_id, path, "Open Document")
        #             self.Bind(wx.EVT_MENU, self.on_open_recent_file, id=document_id)
        #             if not os.path.exists(path):
        #                 self.menu_recent_files.Enable(document_id, False)
        #
        #         # append clear
        #         if len(CONFIG.recent_files) > 0:
        #             self.menu_recent_files.AppendSeparator()
        #
        #         # add an option to clear the menu
        #         self.menu_recent_files.Append(ID_fileMenu_clearRecent, "Clear Menu", "Clear recent items")
        #         self.Bind(wx.EVT_MENU, self.on_clear_recent_files, id=ID_fileMenu_clearRecent)
        logger.debug("Updated list of recent files")

    def on_clear_recent_files(self, _evt):
        """Clear recent items."""
        CONFIG.recent_files = []
        self.on_update_recent_files()

    def on_open_recent_file(self, evt):
        """Open recent document."""
        # msms.mgf, msms.mzml
        # get index
        indices = {
            wx.ID_FILE1: 0,
            wx.ID_FILE2: 1,
            wx.ID_FILE3: 2,
            wx.ID_FILE4: 3,
            wx.ID_FILE5: 4,
            wx.ID_FILE6: 5,
            wx.ID_FILE7: 6,
            wx.ID_FILE8: 7,
            wx.ID_FILE9: 8,
        }
        idx = indices.get(evt.GetId(), -1)
        if idx > len(CONFIG.recent_files) - 1:
            return

        # get information about recent file
        recent_file = CONFIG.recent_files[idx]
        action, path = recent_file["action"], recent_file["path"]

        document = None
        if action == "waters.ms":
            document = self.data_handling.load_waters_ms_document(path)
        elif action == "waters.imms":
            document = self.data_handling.load_waters_im_document(path)
        elif action == "text.ms":
            document = self.data_handling.on_add_text_ms(path)
        elif action == "text.heatmap":
            x_label, y_label = self.get_user_text_x_y_label()
            if x_label is None or y_label is None:
                return
            document = self.data_handling.on_load_text_2d(None, path, x_label, y_label)  # noqa
        elif action == "thermo.ms":
            document = self.data_handling.load_thermo_ms_document(path)
        elif action == "origami.document":
            document = ENV.load(path)

        if document is not None:
            self.data_handling.on_setup_basic_document(document)

    def on_open_file_from_dnd(self, path, extension):
        """Open file as it was dropped in the window"""
        document = None
        if extension == ".origami":
            document = ENV.load(path)
            pub.sendMessage("file.recent.add", action="origami.document", path=path)
        if extension == ".raw":
            try:
                document = self.data_handling.load_waters_im_document(path)
                pub.sendMessage("file.recent.add", action="waters.imms", path=path)
            except Exception:
                document = self.data_handling.load_waters_ms_document(path)
                pub.sendMessage("file.recent.add", action="waters.ms", path=path)
        elif extension == ".RAW":
            document = self.data_handling.load_thermo_ms_document(path)
            pub.sendMessage("file.recent.add", action="thermo.ms", path=path)
        elif extension in [".csv", ".txt", ".tab"]:
            from origami.gui_elements.dialog_quick_select import DialogQuickSelection

            dlg = DialogQuickSelection(self, ["Mass Spectrum", "Heatmap"])
            dlg.ShowModal()
            text_type = dlg.value
            dlg.Destroy()
            if text_type == "Mass Spectrum":
                document = self.data_handling.on_add_text_ms(path)
            elif text_type == "Heatmap":
                x_label, y_label = self.get_user_text_x_y_label()
                if x_label is None or y_label is None:
                    return
                _document, add_dict, filepath = self.data_handling.on_load_text_2d(None, path, x_label, y_label)  # noqa
                self.data_handling.on_add_text_2d(_document, add_dict, filepath)

        value = False
        if document is not None:
            self.data_handling.on_setup_basic_document(document)
            value = True

        return value

    def get_user_text_x_y_label(self):
        """Get x- and y-axis labels"""
        from origami.gui_elements.dialog_ask_labels import DialogSelectLabels

        # get labels for selected items
        dlg = DialogSelectLabels(self)
        if dlg.ShowModal() == wx.ID_OK:
            pass
        x_label, y_label = dlg.xy_labels
        dlg.Destroy()

        return x_label, y_label

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
    def on_toggle_threading(evt):
        """Enable/disable multi-threading in the application"""

        if CONFIG.APP_ENABLE_THREADING:
            msg = (
                "Multi-threading is only an experimental feature for now! It might occasionally crash ORIGAMI,"
                + " in which case you will lose your processed data!"
            )
            DialogBox(title="Warning", msg=msg, kind="Warning")
        if evt is not None:
            evt.Skip()

    @staticmethod
    def on_check_driftscope_path(_evt):
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
        logger.info(f"Dropped {len(filenames)} file/directory in the window")
        value = False
        for filename in filenames:
            logger.info(f"Opening {filename} file...")
            __, file_extension = os.path.splitext(filename)
            value = False
            if file_extension in self.SUPPORTED_FORMATS:
                try:
                    value = self.parent.on_open_file_from_dnd(filename, file_extension)
                except Exception:
                    logger.error(f"Failed to open {filename}", exc_info=True)
                    continue
            elif file_extension in self.LEGACY_FORMATS:
                logger.warning("Dropped file is no longer supported")
            else:
                logger.warning("Dropped file is not supported")
        return value
