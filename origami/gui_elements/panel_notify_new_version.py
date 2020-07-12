"""Panel that notifies the user of a new version of ORIGAMI"""
# Standard library imports
import logging

# Third-party imports
import wx

# Local imports
from origami.styles import set_tooltip
from origami.styles import make_checkbox
from origami.config.config import CONFIG
from origami.gui_elements.misc_dialogs import DialogBox
from origami.gui_elements.panel_html_viewer import PanelHTMLViewer

LOGGER = logging.getLogger(__name__)


class PanelNewVersion(PanelHTMLViewer):
    """HTML panel that displays latest version of ORIGAMI"""

    not_ask_again_check = None
    DISABLE_SEARCH_BAR = True

    def __init__(
        self, parent, link="https://github.com/lukasz-migas/ORIGAMI/releases/tag/1.2.1.4"
    ):  # CONFIG.new_version_panel_link):
        super().__init__(parent, link=link)

    def make_gui(self):
        """Make UI"""
        sizer = self.make_panel()
        sizer = self.modify_sizer(sizer)

        sizer.Fit(self)
        self.SetSizerAndFit(sizer)
        self.Layout()

        self.SetBackgroundColour(wx.WHITE)

    def modify_sizer(self, sizer):
        """Add additional controls to the sizer"""

        download_btn = wx.Button(self, -1, "Download Now", size=(-1, 30))
        download_btn.SetBackgroundColour(wx.WHITE)
        download_btn.Bind(wx.EVT_BUTTON, self.on_download)
        set_tooltip(download_btn, "Go to the website and download latest version of ORIGAMI!😀")

        close_btn = wx.Button(self, -1, "Cancel", size=(-1, 30))
        close_btn.SetBackgroundColour(wx.WHITE)
        close_btn.Bind(wx.EVT_BUTTON, self.on_close)
        set_tooltip(close_btn, "Close this window.")

        self.not_ask_again_check = make_checkbox(self, "Don't ask again")
        self.not_ask_again_check.SetValue(CONFIG.new_version_panel_do_not_ask)
        self.not_ask_again_check.Bind(wx.EVT_CHECKBOX, self.on_apply)
        set_tooltip(self.not_ask_again_check, "Do not inform again on a new version")

        btn_grid = wx.BoxSizer(wx.HORIZONTAL)
        btn_grid.Add(download_btn, 0, wx.ALIGN_CENTER_VERTICAL, 5)
        btn_grid.AddSpacer(5)
        btn_grid.Add(close_btn, 0, wx.ALIGN_CENTER_VERTICAL, 5)
        btn_grid.AddSpacer(5)
        btn_grid.Add(self.not_ask_again_check, 0, wx.ALIGN_CENTER_VERTICAL, 5)

        sizer.Add(btn_grid, 0, wx.ALIGN_CENTER_HORIZONTAL)

        return sizer

    def on_apply(self, _evt):
        """Update config"""
        CONFIG.new_version_panel_do_not_ask = self.not_ask_again_check.GetValue()

    def on_download(self, _evt):
        """Navigate to the download page"""
        self.open_in_browser(None, CONFIG.new_version_panel_link)


def check_version(parent=None, silent: bool = True):
    """Check whether there is a new version of ORIGAMI available online"""
    from origami.utils.version import get_latest_version, compare_versions

    latest, url, failed = get_latest_version()
    if compare_versions(latest, CONFIG.version):
        LOGGER.info("New version of ORIGAMI is available online!")
        if not CONFIG.new_version_panel_do_not_ask:
            dlg = PanelNewVersion(parent, url)
            dlg.Show()
    elif failed:
        LOGGER.warning("Could not check for latest version of ORIGAMI.")
    else:
        LOGGER.info("Using latest version of ORIGAMI")
        if not silent:
            DialogBox("Using latest version of ORIGAMI", "You are using the latest version of ORIGAMI!", "Info")


def _main():
    app = wx.App()
    # check_version()
    ex = PanelNewVersion(None)
    ex.Show()
    app.MainLoop()


if __name__ == "__main__":
    _main()
