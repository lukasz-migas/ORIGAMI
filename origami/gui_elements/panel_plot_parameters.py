"""Plot parameters"""
# Standard library imports
import time
import logging

# Third-party imports
import wx

# Local imports
from origami.icons.assets import Icons
from origami.icons.assets import Colormaps
from origami.utils.system import running_under_pytest
from origami.config.config import CONFIG
from origami.utils.utilities import report_time
from origami.gui_elements.mixins import DocumentationMixin
from origami.gui_elements.plot_parameters.panel_1d import Panel1dSettings
from origami.gui_elements.plot_parameters.panel_2d import Panel2dSettings
from origami.gui_elements.plot_parameters.panel_3d import Panel3dSettings
from origami.gui_elements.plot_parameters.panel_ui import PanelUISettings
from origami.gui_elements.plot_parameters.panel_sizes import PanelSizesSettings
from origami.gui_elements.plot_parameters.panel_legend import PanelLegendSettings
from origami.gui_elements.plot_parameters.panel_violin import PanelViolinSettings
from origami.gui_elements.plot_parameters.panel_general import PanelGeneralSettings
from origami.gui_elements.plot_parameters.panel_colorbar import PanelColorbarSettings
from origami.gui_elements.plot_parameters.panel_waterfall import PanelWaterfallSettings

logger = logging.getLogger(__name__)

CTRL_SIZE = 60
ALIGN_CV_R = wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT


class PanelVisualisationSettingsEditor(wx.Panel, DocumentationMixin):
    """Extra settings panel."""

    # documentation attributes
    HELP_LINK = "www.origami.lukasz-migas.com"

    # ui elements
    main_book = None
    _panel_general, _panel_1d, _panel_2d, _panel_3d, _panel_colorbar = None, None, None, None, None
    _panel_legend, _panel_waterfall, _panel_violin = None, None, None
    _panel_sizes, _panel_ui = None, None

    # UI attributes
    ALL_PANEL_NAMES = [
        "General",
        "Plot 1D",
        "Plot 2D",
        "Plot 3D",
        "Colorbar",
        "Legend",
        "Waterfall",
        "Violin",
        "Plot sizes",
        "UI behaviour",
    ]
    CURRENT_PANEL_NAMES = ALL_PANEL_NAMES
    PAGES = []
    PAGES_INDEX = {
        "General": 0,
        "Plot 1D": 1,
        "Plot 2D": 2,
        "Plot 3D": 3,
        "Colorbar": 4,
        "Legend": 5,
        "Waterfall": 6,
        "Violin": 7,
        "Plot sizes": 8,
        "UI behaviour": 9,
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

        # plot 3D
        self._panel_3d = Panel3dSettings(self.main_book, self.view)
        self.main_book.AddPage(self._panel_3d, "Plot 3D")

        # colorbar
        self._panel_colorbar = PanelColorbarSettings(self.main_book, self.view)
        self.main_book.AddPage(self._panel_colorbar, "Colorbar")

        # legend
        self._panel_legend = PanelLegendSettings(self.main_book, self.view)
        self.main_book.AddPage(self._panel_legend, "Legend")

        # waterfall
        self._panel_waterfall = PanelWaterfallSettings(self.main_book, self.view)
        self.main_book.AddPage(self._panel_waterfall, "Waterfall")

        # violin
        self._panel_violin = PanelViolinSettings(self.main_book, self.view)
        self.main_book.AddPage(self._panel_violin, "Violin")

        # plot sizes
        self._panel_sizes = PanelSizesSettings(self.main_book, self.view)
        self.main_book.AddPage(self._panel_sizes, "Plot sizes")

        # ui behaviour
        self._panel_ui = PanelUISettings(self.main_book, self.view)
        self.main_book.AddPage(self._panel_ui, "UI behaviour")

        if not running_under_pytest():
            self._panel_general.SetupScrolling()
            self._panel_1d.SetupScrolling()
            self._panel_2d.SetupScrolling()
            self._panel_3d.SetupScrolling()
            self._panel_colorbar.SetupScrolling()
            self._panel_legend.SetupScrolling()
            self._panel_waterfall.SetupScrolling()
            self._panel_violin.SetupScrolling()
            self._panel_sizes.SetupScrolling()
            self._panel_ui.SetupScrolling()

        # keep track of pages
        self.PAGES.extend(
            [
                self._panel_general,
                self._panel_1d,
                self._panel_2d,
                self._panel_3d,
                self._panel_colorbar,
                self._panel_legend,
                self._panel_waterfall,
                self._panel_violin,
                self._panel_sizes,
                self._panel_ui,
            ]
        )

        # add statusbar
        panel = wx.Panel(self, wx.ID_ANY)
        info_sizer = self.make_statusbar(panel, "right")
        info_sizer.Fit(panel)
        panel.SetSizerAndFit(info_sizer)

        # fit sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.main_book, 1, wx.EXPAND | wx.ALL, 0)
        main_sizer.Add(panel, 0, wx.EXPAND, 2)

        self.main_book.Bind(wx.EVT_CHOICEBOOK_PAGE_CHANGED, self.on_page_changed)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizer(main_sizer)
        self.SetMinSize((350, 600))
        self.Layout()
        self.SetFocus()
        self.Show()


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


if __name__ == "__main__":
    _main()
