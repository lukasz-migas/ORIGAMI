"""Plot parameters"""
# Standard library imports
import time
import logging

# Third-party imports
import wx

# Local imports
from origami.icons.assets import Icons
from origami.icons.assets import Colormaps
from origami.utils.system import RUNNING_UNDER_PYTEST
from origami.config.config import CONFIG
from origami.utils.utilities import report_time
from origami.gui_elements.mixins import DocumentationMixin
from origami.widgets.interactive.plot_parameters.panel_1d import Panel1dSettings
from origami.widgets.interactive.plot_parameters.panel_2d import Panel2dSettings
from origami.widgets.interactive.plot_parameters.panel_rmsd import PanelRMSDSettings
from origami.widgets.interactive.plot_parameters.panel_rmsf import PanelRMSFSettings
from origami.widgets.interactive.plot_parameters.panel_tools import PanelToolsSettings
from origami.widgets.interactive.plot_parameters.panel_legend import PanelLegendSettings
from origami.widgets.interactive.plot_parameters.panel_tandem import PanelTandemSettings
from origami.widgets.interactive.plot_parameters.panel_general import PanelGeneralSettings
from origami.widgets.interactive.plot_parameters.panel_widgets import PanelWidgetsSettings
from origami.widgets.interactive.plot_parameters.panel_colorbar import PanelColorbarSettings
from origami.widgets.interactive.plot_parameters.panel_waterfall import PanelWaterfallSettings
from origami.widgets.interactive.plot_parameters.panel_preprocess import PanelPreprocessSettings
from origami.widgets.interactive.plot_parameters.panel_rmsd_matrix import PanelRMSDMatrixSettings

logger = logging.getLogger(__name__)

CTRL_SIZE = 60
ALIGN_CV_R = wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT

__all__ = ("PanelVisualisationSettingsEditor",)


class PanelVisualisationSettingsEditor(wx.Panel, DocumentationMixin):
    """Extra settings panel."""

    # documentation attributes
    HELP_LINK = "www.origami.lukasz-migas.com"

    # ui elements
    main_book = None
    _panel_general, _panel_1d, _panel_2d, _panel_colorbar, _panel_legend = None, None, None, None, None
    _panel_waterfall, _panel_rmsd, _panel_rmsd_matrix, _panel_rmsf, _panel_tandem = None, None, None, None, None
    _panel_widgets, _panel_tools, _panel_preprocess = None, None, None

    # UI attributes
    ALL_PANEL_NAMES = [
        "General",
        "Plot 1D",
        "Plot 2D",
        "Colorbar",
        "Legend",
        "Waterfall",
        "RMSD",
        "RMSD Matrix",
        "RMSF",
        "Tandem",
        "Widgets",
        "Tools",
        "Pre-processing",
    ]
    CURRENT_PANEL_NAMES = ALL_PANEL_NAMES
    PAGES = []
    PAGES_INDEX = {
        "General": 0,
        "Plot 1D": 1,
        "Plot 2D": 2,
        "Colorbar": 3,
        "Legend": 4,
        "Waterfall": 5,
        "RMSD": 6,
        "RMSD Matrix": 7,
        "RMSF": 8,
        "Tandem": 9,
        "Widgets": 10,
        "Tools": 11,
        "Pre-processing": 12,
    }

    def __init__(self, parent, presenter, window: str = None):
        wx.Panel.__init__(self, parent)  # , title="Plot parameters")
        t_start = time.time()
        self._colormaps = Colormaps()
        self._icons = Icons()
        self.view = parent
        self.presenter = presenter

        self.import_evt = True
        self.current_page = None
        self._switch = -1

        # make gui items
        self.make_gui()

        if window:
            self.on_set_page(window)

        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_event)
        self.Bind(wx.EVT_CLOSE, self.on_close)

        self.import_evt = False
        self.CenterOnParent()
        logger.info(f"Start-up took {report_time(t_start)}")

    def OnDestroy(self, evt):  # noqa
        """Called just before the panel is destroyed so we can cleanup"""
        for panel in self.PAGES:
            panel.config_mixin_teardown()
        if evt:
            evt.Skip()

    @property
    def data_handling(self):
        """Return handle to `data_processing`"""
        return self.presenter.data_handling

    @property
    def data_processing(self):
        """Return handle to `data_processing`"""
        return self.presenter.data_processing

    @property
    def panel_plot(self):
        """Return handle to `panel_plot`"""
        return self.view.panelPlots

    @property
    def document_tree(self):
        """Return handle to `document_tree`"""
        return self.presenter.view.panelDocuments.documents

    def on_key_event(self, evt):
        """Keyboard event handler"""
        key_code = evt.GetKeyCode()
        if key_code == wx.WXK_ESCAPE:  # key = esc
            self.on_close(evt=None)

        if evt is not None:
            evt.Skip()

    def on_set_page(self, window: str):
        """Change page"""
        if isinstance(window, int):
            page_id = window
        else:
            page_id = CONFIG.extraParamsWindow[window]

        self.main_book.SetSelection(page_id)

    #         self.on_page_changed(None)

    def on_page_changed(self, _evt):
        """Change window"""
        t_start = time.time()
        self.current_page = self.main_book.GetPageText(self.main_book.GetSelection())

        # when the window is changed, the layout can be incorrect, hence we have to "reset it" on each occasion
        # basically a hack that kind of works...
        _size = self.GetSize()
        self._switch = 1 if self._switch == -1 else -1
        self.SetSize((_size[0] + self._switch, _size[1] + self._switch))
        self.SetSize(_size)
        self.SetMinSize(_size)

        self.SetFocus()
        logger.debug(f"Changed window to `{self.current_page}` in {report_time(t_start)}")

    def on_close(self, evt, force: bool = False):  # noqa
        """Destroy this frame."""
        CONFIG.WINDOW_SETTINGS["Plot parameters"]["show"] = False  # noqa
        CONFIG.extraParamsWindow_on_off = False
        if hasattr(self.view, "window_mgr"):
            self.view.window_mgr.GetPane(self).Hide()  # noqa
            self.view.window_mgr.Update()  # noqa

    def make_gui(self):
        """Make UI"""
        # Setup notebook
        self.main_book = wx.Choicebook(self, wx.ID_ANY, style=wx.CHB_DEFAULT)

        # general
        self._panel_general = PanelGeneralSettings(self.main_book, self.view)
        self.main_book.AddPage(self._panel_general, "General")

        # plot 1D
        self._panel_1d = Panel1dSettings(self.main_book, self.view)
        self.main_book.AddPage(self._panel_1d, "Plot 1D")

        # plot 2D
        self._panel_2d = Panel2dSettings(self.main_book, self.view)
        self.main_book.AddPage(self._panel_2d, "Plot 2D")

        # colorbar
        self._panel_colorbar = PanelColorbarSettings(self.main_book, self.view)
        self.main_book.AddPage(self._panel_colorbar, "Colorbar")

        # legend
        self._panel_legend = PanelLegendSettings(self.main_book, self.view)
        self.main_book.AddPage(self._panel_legend, "Legend")

        # waterfall
        self._panel_waterfall = PanelWaterfallSettings(self.main_book, self.view)
        self.main_book.AddPage(self._panel_waterfall, "Waterfall")

        # rmsd
        self._panel_rmsd = PanelRMSDSettings(self.main_book, self.view)
        self.main_book.AddPage(self._panel_rmsd, "RMSD")

        # rmsd matrix
        self._panel_rmsd_matrix = PanelRMSDMatrixSettings(self.main_book, self.view)
        self.main_book.AddPage(self._panel_rmsd_matrix, "RMSD Matrix")

        # rmsf
        self._panel_rmsf = PanelRMSFSettings(self.main_book, self.view)
        self.main_book.AddPage(self._panel_rmsf, "RMSF")

        # tandem
        self._panel_tandem = PanelTandemSettings(self.main_book, self.view)
        self.main_book.AddPage(self._panel_tandem, "Tandem")

        # widgets
        self._panel_widgets = PanelWidgetsSettings(self.main_book, self.view)
        self.main_book.AddPage(self._panel_widgets, "Widgets")

        # tools
        self._panel_tools = PanelToolsSettings(self.main_book, self.view)
        self.main_book.AddPage(self._panel_tools, "Tools")

        # tools
        self._panel_preprocess = PanelPreprocessSettings(self.main_book, self.view)
        self.main_book.AddPage(self._panel_preprocess, "Pre-processing")

        if not RUNNING_UNDER_PYTEST:
            self._panel_general.SetupScrolling()
            self._panel_1d.SetupScrolling()
            self._panel_2d.SetupScrolling()
            self._panel_colorbar.SetupScrolling()
            self._panel_legend.SetupScrolling()
            self._panel_waterfall.SetupScrolling()
            self._panel_rmsd.SetupScrolling()
            self._panel_rmsd_matrix.SetupScrolling()
            self._panel_rmsf.SetupScrolling()
            self._panel_tandem.SetupScrolling()
            self._panel_widgets.SetupScrolling()
            self._panel_tools.SetupScrolling()
            self._panel_preprocess.SetupScrolling()

        # keep track of pages
        self.PAGES.extend(
            [
                self._panel_general,
                self._panel_1d,
                self._panel_2d,
                self._panel_colorbar,
                self._panel_legend,
                self._panel_waterfall,
                self._panel_rmsd,
                self._panel_rmsd_matrix,
                self._panel_rmsf,
                self._panel_tandem,
                self._panel_widgets,
                self._panel_tools,
                self._panel_preprocess,
            ]
        )

        # fit sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.main_book, 1, wx.EXPAND | wx.ALL, 0)

        self.main_book.Bind(wx.EVT_CHOICEBOOK_PAGE_CHANGED, self.on_page_changed)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizer(main_sizer)
        self.SetMinSize((350, 600))
        self.Layout()
        self.SetFocus()
        self.Show()

    def get_config(self):
        """Get configuration data"""
        config = dict()
        for panel in self.PAGES:
            config.update(panel.get_config())
        return config


if __name__ == "__main__":  # pragma: no cover

    def _main():

        from origami.app import App

        class _TestFrame(wx.Frame):
            def __init__(self):
                wx.Frame.__init__(self, None)

                panel = PanelVisualisationSettingsEditor(self, None)
                sizer = wx.BoxSizer()
                sizer.Add(panel, 1, wx.EXPAND)

                self.SetSizerAndFit(sizer)
                self.Layout()

        app = App()
        ex = _TestFrame()

        ex.Show()
        app.MainLoop()

    _main()
