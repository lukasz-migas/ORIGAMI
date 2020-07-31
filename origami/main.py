"""Main entry point for ORIGAMI"""
# Standard library imports
import gc
import os
import sys
import logging
# import warnings
import threading
import faulthandler
from sys import platform

# Third-party imports
import wx

# Local imports
import origami.processing.UniDec.unidec as unidec
from origami.icons.icons import IconContainer
from origami.main_window import MainWindow
from origami.config.config import CONFIG
from origami.utils.logging import set_logger
from origami.utils.logging import set_logger_level
from origami.help_documentation import OrigamiHelp
from origami.gui_elements.views.view_register import VIEW_REG  # noqa

# # needed to avoid annoying warnings to be printed on console
# warnings.filterwarnings("ignore", category=DeprecationWarning)
# warnings.filterwarnings("ignore", category=RuntimeWarning)
# warnings.filterwarnings("ignore", category=UserWarning)
# warnings.filterwarnings("ignore", category=FutureWarning)

logger = logging.getLogger(__name__)
faulthandler.enable()

# disable MPL logger
logging.getLogger("matplotlib").setLevel(logging.ERROR)


class App(wx.App):
    def InitLocale(self):
        self.ResetLocale()


class ORIGAMI:
    """ORIGAMI App instance"""

    config = None
    icons = None
    help = None
    logging = None

    def __init__(self, *args, **kwargs):
        self.__wx_app = App(redirect=False, filename="ORIGAMI")
        self.view = None
        self.initilize_app(*args, **kwargs)

    def start(self):
        """Start application"""
        self.view.Show()
        self.__wx_app.MainLoop()

    # def on_reboot_origami(self, _evt):
    #     """Reset window"""
    #     dlg = DialogBox("Restart ORIGAMI", "Are you sure you want to restart the application?", kind="Question")
    #     if dlg == wx.ID_CANCEL:
    #         return
    #     self.__wx_app.GetMainLoop().ProcessIdle()
    #     # self.__wx_app.ExitMainLoop()
    #     self.view.Destroy()
    #     self.view = None
    #     self.view = MainWindow(self, icons=self.icons, title="ORIGAMI - %s " % self.config.version)
    #     self.view.Show()

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
        self.help = OrigamiHelp()

        # Load configuration file
        self.on_import_configuration_on_startup()

        # Setup variables
        #         self.initialize_state()
        self.view = MainWindow(self, icons=self.icons, title="ORIGAMI - %s " % self.config.version)
        self.__wx_app.SetTopWindow(self.view)
        self.view.Show()

        self.__wx_app.SetAppName("ORIGAMI - %s " % self.config.version)
        self.__wx_app.SetVendorName("Lukasz G. Migas")
        self.__wx_app.MainLoop()

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
        #         self.view.panelPlots.on_change_plot_style(evt=None)
        #         self.view.panelPlots.on_change_color_palette(evt=None)
        self.view.on_update_recent_files()

        self.logging = self.config.logging
        self.config._processID = os.getpid()

        gc.enable()
        self.on_start_logging()

        # add binding to UniDec engine
        self.config.unidec_engine = unidec.UniDec()

        # Set unidec directory
        self.config.unidec_path = self.config.unidec_engine.config.UniDecPath

        # only check if on Windows
        if self.config.checkForDriftscopeAtStart and platform == "win32":
            self.config.setup_paths()

        # add data handling and processing modules
        self.view.panelParametersEdit.setup_handling_and_processing()

    #     def initialize_registry(self):
    #         """Update reg keys to allow viewing of JS/HTML inside ORIGAMI windows"""
    #         from origami.utils.windows_reg_edit import set_ie_emulation_level
    #         from origami.utils.windows_reg_edit import set_ie_lockdown_level
    #
    #         set_ie_emulation_level()
    #         set_ie_lockdown_level()
    #         logger.debug("Initialized registry...")

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

    def onThreading(self, evt, args, action="loadOrigami"):  # noqa

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
        elif action == "export_settings":
            thread_obj = threading.Thread(target=self.config.saveConfigXML, args=args)

        # Start thread
        if thread_obj is None:
            return
        try:
            thread_obj.start()
        except Exception:  # noqa
            print("Failed to execute the operation in threaded mode. Consider switching it off?")

    def get2DdataFromDictionary(self, dictionary=None, dataType="plot", compact=False, plotType="2D"):  # noqa
        """Legacy function"""
        logger.info("This function is no longer used")

    # TODO: move to data_handling module
    def OnUpdateDocument(self, document, expand_item="document", expand_item_title=None):  # noqa
        """Legacy function"""
        logger.info("This function is no longer used")

    # TODO: move to data_handling module
    def onAddBlankDocument(self, evt, document_type=None):  # noqa
        """Legacy function"""
        logger.info("This function is no longer used")


if __name__ == "__main__":
    app = ORIGAMI(redirect=False)
