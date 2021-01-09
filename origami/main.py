"""Main entry point for ORIGAMI"""
# Standard library imports
import gc
import os
import sys
import logging
import threading
import faulthandler
from sys import platform

# Third-party imports
import wx

# Local imports
from origami.app import App
from origami.icons.icons import IconContainer
from origami.main_window import MainWindow
from origami.config.config import CONFIG
from origami.gui_elements.views.view_register import VIEW_REG  # noqa
from origami.utils.appdirs import USER_CONFIG_DIR
from origami.gui_elements.splash_screen import SplashScreenView


logger = logging.getLogger(__name__)
faulthandler.enable()
gc.enable()

# disable MPL logger
logging.getLogger("matplotlib").setLevel(logging.ERROR)


class ORIGAMI:
    """ORIGAMI App instance"""

    config = None
    icons = None
    help = None

    def __init__(self, redirect: bool = False, *args, **kwargs):
        self.__wx_app = App(redirect=redirect, filename="ORIGAMI")
        self.view = None
        self.initilize_app(*args, **kwargs)

    def start(self):
        """Start application"""
        self.view.Show()
        self.__wx_app.MainLoop()

    def quit(self):
        """Quit application"""
        self.__wx_app.GetMainLoop().ProcessIdle()
        self.__wx_app.ExitMainLoop()
        self.view.Destroy()
        return True

    def end_app_session(self):
        """Close application"""
        wx.CallAfter(self.quit, force=True)

    def initilize_app(self, *args, **kwargs):  # noqa
        """Initialize app"""
        self.config = CONFIG
        self.icons = IconContainer()

        # show splash screen
        splash = SplashScreenView()
        splash.Show()

        # Load configuration file
        self.on_import_configuration_on_startup()
        self.setup_app()

        # Setup variables
        self.view = MainWindow(self, icons=self.icons, title="ORIGAMI - %s " % self.config.version)
        self.__wx_app.SetTopWindow(self.view)
        self.view.Show()

        self.__wx_app.SetAppName("ORIGAMI - %s " % self.config.version)
        self.__wx_app.SetVendorName("Lukasz G. Migas")
        self.__wx_app.MainLoop()

        # Setup plot style
        #         self.view.panelPlots.on_change_plot_style(evt=None)
        #         self.view.panelPlots.on_change_color_palette(evt=None)
        self.view.on_update_recent_files()

        # Assign standard input/output to variable
        CONFIG.APP_STDIN = sys.stdin
        CONFIG.APP_STDOUT = sys.stdout
        CONFIG.APP_STDERR = sys.stderr

        # get handle of the current process id
        CONFIG.APP_PROCESS_ID = os.getpid()

        # setup temporary directory
        CONFIG.setup_temporary_dir()
        CONFIG.setup_logging()

        # setup Driftscope paths
        if CONFIG.APP_CHECK_DRIFTSCOPE_PATH_AT_START and platform == "win32":
            CONFIG.setup_paths()

        # setup recent files
        self.view.on_update_recent_files()

    #     def initialize_registry(self):
    #         """Update reg keys to allow viewing of JS/HTML inside ORIGAMI windows"""
    #         from origami.utils.windows_reg_edit import set_ie_emulation_level
    #         from origami.utils.windows_reg_edit import set_ie_lockdown_level
    #
    #         set_ie_emulation_level()
    #         set_ie_lockdown_level()
    #         logger.debug("Initialized registry...")
    @staticmethod
    def setup_app():
        """Setup application"""
        # Assign standard input/output to variable
        CONFIG.APP_STDIN = sys.stdin
        CONFIG.APP_STDOUT = sys.stdout
        CONFIG.APP_STDERR = sys.stderr

        # get handle of the current process id
        CONFIG.APP_PROCESS_ID = os.getpid()

        # setup temporary directory
        CONFIG.setup_temporary_dir()
        CONFIG.setup_logging()

        # setup Driftscope paths
        if CONFIG.APP_CHECK_DRIFTSCOPE_PATH_AT_START and platform == "win32":
            CONFIG.setup_paths()

    @property
    def data_handling(self):
        """Return handle to the `data_handling` object"""
        return self.view.data_handling

    @property
    def data_processing(self):
        """Return handle to the `data_processing` object"""
        return self.view.data_processing

    @property
    def data_visualisation(self):
        """Return handle to the `data_visualisation` object"""
        return self.view.data_visualisation

    def on_import_configuration_on_startup(self):
        """This function imports configuration file"""
        try:
            self.config.load_config(os.path.join(USER_CONFIG_DIR, CONFIG.DEFAULT_CONFIG_NAME))
        except Exception:
            pass

    def onThreading(self, evt, args, action="loadOrigami"):  # noqa
        """Start separate thread"""

        thread_obj = None
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

        # Start thread
        if thread_obj is None:
            return
        try:
            thread_obj.start()
        except Exception:  # noqa
            print("Failed to execute the operation in threaded mode. Consider switching it off?")


if __name__ == "__main__":
    app = ORIGAMI()
