"""About ORIGAMI panel"""
# Third-party imports
import wx
from wx.lib.agw import hyperlink

# Local imports
from origami.icons.assets import Images
from origami.config.config import CONFIG


class PanelAbout(wx.MiniFrame):
    """About panel."""

    EMAIL_ONE = "l.g.migas@tudelft.nl"
    EMAIL_TWO = "lukas.migas@yahoo.com"
    INSTITUTION = "University of Manchester / TU Delft"
    COPYRIGHT = "(c) 2017-present Lukasz G. Migas"
    DOCS = "https://origami.lukasz-migas.com/"
    GITHUB = "https://github.com/lukasz-migas/ORIGAMI"
    CITE = "https://doi.org/10.1016/j.ijms.2017.08.014"
    AUTHOR = "https://lukasz-migas.com/"
    NEW_FEATURES = "https://docs.google.com/forms/d/e/1FAIpQLSduN15jzq06QCaacliBg8GkOajDNjWn4cEu_1J-kBhXSKqMHQ/viewform"
    BUGS = "https://docs.google.com/forms/d/e/1FAIpQLSf7Ahgvt-YFRrA61Pv1S4i8nBK6wfhOpD2O9lGt_E3IA0lhfQ/viewform"

    def __init__(self, parent):
        wx.MiniFrame.__init__(
            self,
            parent,
            wx.ID_ANY,
            "ORIGAMI",
            style=wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX),
        )
        self.parent = parent
        self.images = Images()

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
        panel = wx.Panel(self, wx.ID_ANY)

        image = wx.StaticBitmap(panel, wx.ID_ANY, self.images.logo)
        print(dir(image))

        version_label = "Version %s" % CONFIG.version
        version = wx.StaticText(panel, wx.ID_ANY, version_label, style=wx.ALIGN_CENTRE)
        version.SetFont(wx.NORMAL_FONT)

        about_msg = (
            "If you encounter any problems, have questions or would like to send some feedback, \nplease contact me at"
        )
        link_email_tu = hyperlink.HyperLinkCtrl(panel, wx.ID_ANY, self.EMAIL_ONE, URL=f"mailto:{self.EMAIL_ONE}")
        link_email_yh = hyperlink.HyperLinkCtrl(panel, wx.ID_ANY, self.EMAIL_TWO, URL=f"mailto:{self.EMAIL_TWO}")

        message = wx.StaticText(panel, wx.ID_ANY, about_msg, style=wx.ALIGN_CENTRE)
        message.SetFont(wx.NORMAL_FONT)

        university = wx.StaticText(panel, wx.ID_ANY, self.INSTITUTION)
        university.SetFont(wx.SMALL_FONT)

        copyright_text = wx.StaticText(panel, wx.ID_ANY, self.COPYRIGHT)
        copyright_text.SetFont(wx.NORMAL_FONT)

        homepage_btn = hyperlink.HyperLinkCtrl(panel, wx.ID_ANY, "Homepage/Documentation", URL=self.DOCS)
        github_btn = hyperlink.HyperLinkCtrl(panel, wx.ID_ANY, "GitHub", URL=self.GITHUB)
        cite_btn = hyperlink.HyperLinkCtrl(panel, wx.ID_ANY, "Publication", URL=self.CITE)
        new_features_btn = hyperlink.HyperLinkCtrl(panel, wx.ID_ANY, "Request New Features", URL=self.NEW_FEATURES)
        report_bug_btn = hyperlink.HyperLinkCtrl(panel, wx.ID_ANY, "Report Bugs", URL=self.BUGS)
        author_btn = hyperlink.HyperLinkCtrl(panel, wx.ID_ANY, "About Author", URL=self.AUTHOR)

        email_sizer = wx.BoxSizer()
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


if __name__ == "__main__":  # pragma: no cover

    def _main():

        from origami.app import App

        app = App()
        ex = PanelAbout(None)

        ex.Show()
        app.MainLoop()

    _main()
