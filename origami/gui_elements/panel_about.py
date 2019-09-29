# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import wx
from ids import ID_helpAuthor
from ids import ID_helpCite
from ids import ID_helpGitHub
from ids import ID_helpHomepage
from ids import ID_helpNewFeatures
from ids import ID_helpReportBugs


class PanelAbout(wx.MiniFrame):
    """About panel."""

    def __init__(self, parent, presenter, frameTitle, config, icons):
        wx.MiniFrame.__init__(
            self,
            parent,
            -1,
            frameTitle,
            style=wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX),
        )

        self.parent = parent
        self.presenter = presenter

        self.config = config
        self.icons = icons
        # make gui items
        sizer = self.make_gui()
        wx.EVT_CLOSE(self, self.on_close)

        # fit layout
        self.Layout()
        sizer.Fit(self)
        self.SetSizer(sizer)
        self.SetMinSize(self.GetSize())
        self.Centre()

    def make_gui(self):
        """Make panel gui."""
        NORMAL_FONT = wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        # make elements
        panel = wx.Panel(self, -1)

        image = wx.StaticBitmap(panel, -1, self.icons.getLogo)

        versionLabel = "Version %s" % self.config.version
        version = wx.StaticText(panel, -1, versionLabel, style=wx.ALIGN_CENTRE)
        version.SetFont(wx.NORMAL_FONT)

        about_msg = (
            "If you encounter any problems, have questions or would like to send some feedback,\n"
            + "               please me at l.g.migas@tudelft.nl or lukas.migas@yahoo.com"
        )

        message = wx.StaticText(panel, -1, about_msg)
        message.SetFont(wx.NORMAL_FONT)

        university = wx.StaticText(panel, -1, "University of Manchester")
        university.SetFont(wx.SMALL_FONT)

        copyright_text = wx.StaticText(panel, -1, "(c) 2017-present Lukasz G. Migas")
        copyright_text.SetFont(NORMAL_FONT)

        homepageBtn = wx.Button(panel, ID_helpHomepage, "Homepage", size=(150, -1))
        homepageBtn.Bind(wx.EVT_BUTTON, self.parent.on_open_link)

        githubBtn = wx.Button(panel, ID_helpGitHub, "GitHub", size=(150, -1))
        githubBtn.Bind(wx.EVT_BUTTON, self.parent.on_open_link)

        citeBtn = wx.Button(panel, ID_helpCite, "How to Cite", size=(150, -1))
        citeBtn.Bind(wx.EVT_BUTTON, self.parent.on_open_link)

        newFeaturesBtn = wx.Button(panel, ID_helpNewFeatures, "Request New Features", size=(150, -1))
        newFeaturesBtn.Bind(wx.EVT_BUTTON, self.parent.on_open_link)

        reportBugBtn = wx.Button(panel, ID_helpReportBugs, "Report Bugs", size=(150, -1))
        reportBugBtn.Bind(wx.EVT_BUTTON, self.parent.on_open_link)

        authorBtn = wx.Button(panel, ID_helpAuthor, "About author", size=(150, -1))
        authorBtn.Bind(wx.EVT_BUTTON, self.parent.on_open_link)

        btn_grid = wx.GridBagSizer(2, 2)
        y = 0
        btn_grid.Add(homepageBtn, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        btn_grid.Add(githubBtn, (y, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        btn_grid.Add(citeBtn, (y, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)

        btn2_grid = wx.GridBagSizer(2, 2)
        y = 0
        btn2_grid.Add(newFeaturesBtn, (y, 0), flag=wx.ALIGN_CENTER)
        btn2_grid.Add(reportBugBtn, (y, 1), flag=wx.ALIGN_CENTER)

        btn3_grid = wx.GridBagSizer(2, 2)
        y = 0
        btn3_grid.Add(authorBtn, (y, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)

        # pack element
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(image, 0, wx.ALIGN_CENTER_HORIZONTAL, 20)
        sizer.Add(version, 0, wx.ALIGN_CENTER_HORIZONTAL, 20)
        sizer.AddSpacer(10)
        sizer.Add(message, 0, wx.ALIGN_CENTER_HORIZONTAL, 20)
        sizer.AddSpacer(10)
        sizer.Add(university, 0, wx.ALIGN_CENTER_HORIZONTAL, 20)
        sizer.AddSpacer(10)
        sizer.Add(copyright_text, 0, wx.ALIGN_CENTER_HORIZONTAL, 20)
        sizer.AddSpacer(10)
        sizer.Add(btn2_grid, 0, wx.ALIGN_CENTER_HORIZONTAL, 20)
        sizer.AddSpacer(10)
        sizer.Add(btn_grid, 0, wx.ALIGN_CENTER_HORIZONTAL, 20)
        sizer.AddSpacer(10)
        sizer.Add(btn3_grid, 0, wx.ALIGN_CENTER_HORIZONTAL, 20)
        sizer.AddSpacer(10)

        sizer.Fit(panel)
        return sizer

    def on_close(self, evt):
        """Destroy this frame."""
        self.Destroy()
