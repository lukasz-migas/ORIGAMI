# Standard library imports
import os
import webbrowser

# Third-party imports
import wx.html2

# Local imports
from origami.config.config import CONFIG

# TODO: add browser controls (prev, next, home)
# TODO: add link searchbar


class PanelHTMLViewer(wx.MiniFrame):
    def __init__(self, parent, msg=None, title=None, **kwargs):
        wx.MiniFrame.__init__(
            self,
            parent,
            -1,
            "Help & Information Panel",
            size=(600, 400),
            style=(wx.DEFAULT_FRAME_STYLE | wx.MAXIMIZE_BOX | wx.CLOSE_BOX),
        )

        self.parent = parent
        wx.InitAllImageHandlers()

        # get current working directory and temporarily change path
        cwd = os.getcwd()
        if CONFIG.cwd:
            os.chdir(CONFIG.cwd)

        if title is None:
            title = kwargs.get("title", "Window title")
        msg, link = self.get_text(msg, **kwargs)

        self.label_header = wx.html2.WebView.New(self)

        if msg:
            self.label_header.FirstPage = msg
            self.label_header.SetPage(self.label_header.FirstPage, "")
            self.label_header.Bind(wx.html2.EVT_WEBVIEW_NAVIGATING, self.on_url)
            self.label_header.Bind(wx.html2.EVT_WEBVIEW_NEWWINDOW, self.on_url)
        else:
            self.label_header.LoadURL(link)

        try:
            _main_position = self.parent.GetPosition()
            position_diff = []
            for idx in range(wx.Display.GetCount()):
                d = wx.Display(idx)
                position_diff.append(_main_position[0] - d.GetGeometry()[0])

            current_display_size = wx.Display(position_diff.index(min(position_diff))).GetGeometry()
        except Exception:
            current_display_size = None

        if "window_size" in kwargs:
            if current_display_size is not None:
                screen_width, screen_height = current_display_size[2], current_display_size[3]
                kwargs["window_size"] = list(kwargs["window_size"])

                if kwargs["window_size"][0] > screen_width:
                    kwargs["window_size"][0] = screen_width

                if kwargs["window_size"][1] > screen_height:
                    kwargs["window_size"][1] = screen_height - 75
            self.SetSize(kwargs["window_size"])

        self.SetTitle(title)
        self.Show(True)
        self.CentreOnParent()
        self.SetFocus()
        self.Bind(wx.EVT_CLOSE, self.on_close)

        # reset working directory
        os.chdir(cwd)

    @staticmethod
    def on_url(evt):
        link = evt.GetURL()
        webbrowser.open(link)
        if evt is not None:
            evt.Veto()
        # link = evt.GetLinkInfo()
        # webbrowser.open(link.GetHref())

    def on_close(self, evt):
        """Destroy this frame."""
        self.Destroy()

    @staticmethod
    def get_text(msg, **kwargs):
        """Parses text provided to the window"""
        link = None
        if msg is not None:
            return msg, link

        msg = "TEST MESSAGE"
        if "html_msg" in kwargs:
            msg = kwargs.pop("html_msg")
        elif "md_msg" in kwargs:
            from markdown2 import markdown

            msg = markdown(kwargs.pop("md_msg"), extras=["smarty-pants", "tables"])
        elif "link" in kwargs:
            link = kwargs.pop("link")
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


def main():
    app = wx.App()
    ex = PanelHTMLViewer(None, link=r"https://origami.lukasz-migas.com/")  # md_msg=MARKDOWN_EXAMPLE)

    ex.Show()
    app.MainLoop()


if __name__ == "__main__":
    main()
