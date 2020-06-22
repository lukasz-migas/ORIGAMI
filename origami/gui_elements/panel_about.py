"""About ORIGAMI panel"""
# Third-party imports
import wx
from wx.lib.agw import hyperlink

# Local imports
from origami.config.config import CONFIG


class PanelAbout(wx.MiniFrame):
    """About panel."""

    def __init__(self, parent, icons):
        wx.MiniFrame.__init__(
            self,
            parent,
            -1,
            "ORIGAMI",
            style=wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX),
        )
        self.parent = parent
        self.icons = icons

        # make gui items
        sizer = self.make_gui()

        # fit layout
        self.Layout()
        sizer.Fit(self)
        self.SetSizer(sizer)
        self.SetMinSize(self.GetSize())
        self.Centre()
        self.SetTitle("ORIGAMI %s" % CONFIG.version)

        # bind events
        self.Bind(wx.EVT_CLOSE, self.on_close)

    # noinspection DuplicatedCode
    def make_gui(self):
        """Make panel gui."""
        # make elements
        panel = wx.Panel(self, -1)

        image = wx.StaticBitmap(panel, -1, self.icons.getLogo)

        version_label = "Version %s" % CONFIG.version
        version = wx.StaticText(panel, -1, version_label, style=wx.ALIGN_CENTRE)
        version.SetFont(wx.NORMAL_FONT)

        about_msg = (
            "If you encounter any problems, have questions or would like to send some feedback, \nplease contact me at"
            # l.g.migas@tudelft.nl or lukas.migas@yahoo.com"
        )
        link_email_tu = hyperlink.HyperLinkCtrl(panel, -1, "l.g.migas@tudelft.nl", URL="mailto:l.g.migas@tudelft.nl")
        link_email_yh = hyperlink.HyperLinkCtrl(panel, -1, "lukas.migas@yahoo.com", URL="mailto:lukas.migas@yahoo.com")

        message = wx.StaticText(panel, -1, about_msg, style=wx.ALIGN_CENTRE)
        message.SetFont(wx.NORMAL_FONT)

        university = wx.StaticText(panel, -1, "University of Manchester / TU Delft")
        university.SetFont(wx.SMALL_FONT)

        copyright_text = wx.StaticText(panel, -1, "(c) 2017-present Lukasz G. Migas")
        copyright_text.SetFont(wx.NORMAL_FONT)

        homepage_btn = hyperlink.HyperLinkCtrl(
            panel, -1, "Homepage/Documentation", URL="https://origami.lukasz-migas.com/"
        )
        github_btn = hyperlink.HyperLinkCtrl(panel, -1, "GitHub", URL="https://github.com/lukasz-migas/ORIGAMI")
        cite_btn = hyperlink.HyperLinkCtrl(panel, -1, "Publication", URL="https://doi.org/10.1016/j.ijms.2017.08.014")
        new_features_btn = hyperlink.HyperLinkCtrl(
            panel,
            -1,
            "Request New Features",
            URL="https://docs.google.com/forms/d/e/1FAIpQLSduN15jzq06QCaacliBg8GkOajDNjWn4cEu_1J-kBhXSKqMHQ/viewform",
        )
        report_bug_btn = hyperlink.HyperLinkCtrl(
            panel,
            -1,
            "Report Bugs",
            URL="https://docs.google.com/forms/d/e/1FAIpQLSf7Ahgvt-YFRrA61Pv1S4i8nBK6wfhOpD2O9lGt_E3IA0lhfQ/viewform",
        )
        author_btn = hyperlink.HyperLinkCtrl(panel, -1, "About Author", URL="https://lukasz-migas.com/")

        email_sizer = wx.BoxSizer(wx.HORIZONTAL)
        email_sizer.Add(link_email_tu, 0)
        email_sizer.AddSpacer(20)
        email_sizer.Add(link_email_yh, 0)

        # pack element
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(image, 0, wx.ALIGN_CENTER_HORIZONTAL, 20)
        sizer.Add(version, 0, wx.ALIGN_CENTER_HORIZONTAL, 20)
        sizer.AddSpacer(10)
        sizer.Add(message, 0, wx.ALIGN_CENTER_HORIZONTAL, 20)
        sizer.AddSpacer(5)
        sizer.Add(email_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL, 20)
        sizer.AddSpacer(20)
        sizer.Add(homepage_btn, 0, wx.ALIGN_CENTER_HORIZONTAL)
        sizer.AddSpacer(5)
        sizer.Add(github_btn, 0, wx.ALIGN_CENTER_HORIZONTAL)
        sizer.AddSpacer(5)
        sizer.Add(cite_btn, 0, wx.ALIGN_CENTER_HORIZONTAL)
        sizer.AddSpacer(5)
        sizer.Add(new_features_btn, 0, wx.ALIGN_CENTER_HORIZONTAL)
        sizer.AddSpacer(5)
        sizer.Add(report_bug_btn, 0, wx.ALIGN_CENTER_HORIZONTAL)
        sizer.AddSpacer(5)
        sizer.Add(author_btn, 0, wx.ALIGN_CENTER_HORIZONTAL)
        sizer.AddSpacer(5)
        sizer.AddSpacer(10)
        sizer.Add(university, 0, wx.ALIGN_CENTER_HORIZONTAL, 20)
        sizer.AddSpacer(10)
        sizer.Add(copyright_text, 0, wx.ALIGN_CENTER_HORIZONTAL, 20)

        sizer.Fit(panel)
        return sizer

    def on_close(self, _evt):
        """Destroy this frame."""
        self.Destroy()


def _main():
    from origami.icons.icons import IconContainer

    app = wx.App()
    icons = IconContainer()
    ex = PanelAbout(None, icons)

    ex.Show()
    app.MainLoop()


if __name__ == "__main__":
    _main()
