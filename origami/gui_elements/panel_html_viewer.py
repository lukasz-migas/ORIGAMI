"""Very basic html viewer"""
# Standard library imports
import os
import webbrowser

# Third-party imports
import wx.html2

# Local imports
from origami.styles import set_tooltip
from origami.styles import make_bitmap_btn
from origami.icons.assets import Icons
from origami.utils.screen import calculate_window_size
from origami.config.config import CONFIG


class PanelHTMLViewer(wx.MiniFrame):
    """HTML viewer"""

    # ui elements
    html_view = None
    next_btn = None
    prev_btn = None
    home_btn = None
    browser_btn = None
    search_bar = None

    # extra
    DISABLE_SEARCH_BAR = False

    def __init__(self, parent, msg: str = None, html_msg: str = None, md_msg: str = None, link: str = None):
        wx.MiniFrame.__init__(
            self,
            parent,
            -1,
            "Help & Information Panel",
            size=(600, 400),
            style=(wx.DEFAULT_FRAME_STYLE | wx.MAXIMIZE_BOX | wx.CLOSE_BOX),
        )

        self.parent = parent
        self._icons = Icons()
        wx.InitAllImageHandlers()

        # get current working directory and temporarily change path
        cwd = os.getcwd()
        if CONFIG.cwd:
            os.chdir(CONFIG.cwd)

        msg, self._home_link = self.get_text(msg, html_msg, md_msg, link)

        self.make_gui()
        self.setup(msg, self._home_link)

        self.CentreOnParent()
        self.Show(True)
        self.SetFocus()

        # reset working directory
        self.Bind(wx.EVT_CLOSE, self.on_close)
        os.chdir(cwd)

    def setup(self, msg, link):
        """Setup"""
        if msg:
            self.html_view.FirstPage = msg
            self.html_view.SetPage(self.html_view.FirstPage, "")
            self.html_view.Bind(wx.html2.EVT_WEBVIEW_NAVIGATING, self.on_url)
            self.html_view.Bind(wx.html2.EVT_WEBVIEW_NEWWINDOW, self.on_url)
        else:
            self.html_view.LoadURL(link)

        screen_size = wx.GetDisplaySize()
        if self.parent is not None:
            screen_size = self.parent.GetSize()
        window_size = calculate_window_size(screen_size, [0.4, 0.6])
        self.SetSize(window_size)

        if self.DISABLE_SEARCH_BAR:
            self.search_bar.Enable(False)

    def make_gui(self):
        """Make UI"""
        sizer = self.make_panel()

        sizer.Fit(self)
        self.SetSizerAndFit(sizer)
        self.Layout()

    # noinspection DuplicatedCode

    def make_panel(self):
        """Make UI"""
        # search bar
        self.prev_btn = make_bitmap_btn(self, wx.ID_ANY, self._icons.previous, style=wx.BORDER_NONE)
        self.prev_btn.Bind(wx.EVT_BUTTON, self.go_back)
        set_tooltip(self.prev_btn, "Go back.")

        self.next_btn = make_bitmap_btn(self, wx.ID_ANY, self._icons.next, style=wx.BORDER_NONE)
        self.next_btn.Bind(wx.EVT_BUTTON, self.go_forward)
        set_tooltip(self.next_btn, "Go forward.")

        self.home_btn = make_bitmap_btn(self, wx.ID_ANY, self._icons.home, style=wx.BORDER_NONE)
        self.home_btn.Bind(wx.EVT_BUTTON, self.go_home)
        set_tooltip(self.home_btn, "Go home.")

        self.browser_btn = make_bitmap_btn(self, wx.ID_ANY, self._icons.firefox, style=wx.BORDER_NONE)
        self.browser_btn.Bind(wx.EVT_BUTTON, self.open_in_browser)
        set_tooltip(self.browser_btn, "Open current page in full browser.")

        self.search_bar = wx.TextCtrl(self, -1, style=wx.TE_PROCESS_ENTER)
        self.search_bar.Bind(wx.EVT_TEXT_ENTER, self.go_to)
        set_tooltip(self.search_bar, "Type-in URL address and press Enter.")

        # html view
        self.html_view = wx.html2.WebView.New(self)

        self.html_view.Bind(wx.html2.EVT_WEBVIEW_NAVIGATING, self.on_toggle_controls)
        self.html_view.Bind(wx.html2.EVT_WEBVIEW_LOADED, self.on_toggle_controls)
        self.html_view.Bind(wx.html2.EVT_WEBVIEW_NAVIGATED, self.set_title)

        top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        top_sizer.Add(self.prev_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        top_sizer.Add(self.next_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        top_sizer.Add(self.home_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        top_sizer.Add(self.browser_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        top_sizer.Add(self.search_bar, 1, wx.EXPAND)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(top_sizer, 0, wx.EXPAND)
        sizer.Add(self.html_view, 1, wx.EXPAND)

        return sizer

    def on_toggle_controls(self, evt):
        """Enable/disable controls while web-page is loading"""
        loading = not self.html_view.IsBusy()

        self.next_btn.Enable(loading)
        self.prev_btn.Enable(loading)
        self.home_btn.Enable(loading)

        if self.DISABLE_SEARCH_BAR:
            self.search_bar.Enable(False)
        else:
            self.search_bar.Enable(loading)

    def set_title(self, _evt):
        """Set title to mirror the current url"""
        url = self.html_view.GetCurrentURL()
        self.SetTitle(url)
        self.search_bar.SetValue(url)

    def go_back(self, _evt):
        """Go back to previous location"""
        if not self.html_view.IsBusy():
            self.html_view.GoBack()

    def go_forward(self, _evt):
        """Go forward to location"""
        if not self.html_view.IsBusy():
            self.html_view.GoForward()

    def go_home(self, _evt):
        """Go back to home location"""
        if not self.html_view.IsBusy():
            self.html_view.LoadURL(self._home_link)

    def go_to(self, _evt):
        """Go to new location"""
        if not self.html_view.IsBusy():
            self.html_view.LoadURL(self.search_bar.GetValue())

    def open_in_browser(self, _evt, url: str = None):
        """Open current webpage in browser"""
        if url is None:
            url = self.html_view.GetCurrentURL()
        webbrowser.open(url, autoraise=True)

    @staticmethod
    def on_url(evt):
        """Open URL"""
        link = evt.GetURL()
        webbrowser.open(link)
        if evt is not None:
            evt.Veto()

    def on_close(self, evt):
        """Destroy this frame."""
        self.Destroy()

    @staticmethod
    def get_text(msg, html_msg=None, md_msg=None, link=None):
        """Parses text provided to the window"""
        if msg is not None:
            return msg, None
        if html_msg is not None:
            msg = html_msg
        elif md_msg is not None:
            from markdown2 import markdown

            msg = markdown(md_msg, extras=["smarty-pants", "tables"])
        elif link is not None:
            return None, link
        return msg, link


MARKDOWN_EXAMPLE = """
---
__Advertisement :)__

- __[pica](https://nodeca.github.io/pica/demo/)__ - high quality and fast image
  resize in browser.
- __[babelfish](https://github.com/nodeca/babelfish/)__ - developer friendly
  i18n with plurals support and easy syntax.

You will like those projects!

---

# h1 Heading 8-)
## h2 Heading
### h3 Heading
#### h4 Heading
##### h5 Heading
###### h6 Heading
"""


def _main():
    app = wx.App()
    ex = PanelHTMLViewer(None, link=r"https://origami.lukasz-migas.com/")  # md_msg=MARKDOWN_EXAMPLE)

    ex.Show()
    app.MainLoop()


if __name__ == "__main__":
    _main()
