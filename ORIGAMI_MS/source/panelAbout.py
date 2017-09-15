# -*- coding: utf-8 -*-

# load libs
import wx

# load modules
from IDs import *

class panelAbout(wx.MiniFrame):
    """About panel."""
    
    def __init__(self, parent, presenter, frameTitle, config, icons):
        wx.MiniFrame.__init__(self, parent, -1, frameTitle, style=wx.DEFAULT_FRAME_STYLE
                       & ~ (wx.RESIZE_BORDER | wx.RESIZE_BOX | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX))
        
        self.parent = parent
        self.presenter = presenter
        
        self.config = config
        self.icons = icons
        # make gui items
        sizer = self.makeGUI()
        wx.EVT_CLOSE(self, self.onClose)
        
        # fit layout
        self.Layout()
        sizer.Fit(self)
        self.SetSizer(sizer)
        self.SetMinSize(self.GetSize())
        self.Centre()
        
    def makeGUI(self):
        """Make panel gui."""
        
        # make elements
        panel = wx.Panel(self, -1)
        
        image = wx.StaticBitmap(panel, -1, self.icons.getLogo)
        
        title = wx.StaticText(panel, -1, "ORIGAMI")
        title.SetFont(wx.Font(10, wx.FONTFAMILY_SWISS, 
                              wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        
        versionLabel = 'Version %s' % self.config.version
        version = wx.StaticText(panel, -1, versionLabel, style=wx.ALIGN_CENTRE)
        version.SetFont(wx.SMALL_FONT)
        
        copyright = wx.StaticText(panel, -1, "(c) 2017 Lukasz G. Migas")
        copyright.SetFont(wx.SMALL_FONT)
        
        message = wx.StaticText(panel, -1, 'If you encounter any problems, have questions or would like to send some feedback, please contact Lukasz Migas at lukasz.migas@manchester.ac.uk.')
        message.SetFont(wx.SMALL_FONT)
        university = wx.StaticText(panel, -1, "University of Manchester")
        university.SetFont(wx.SMALL_FONT)
        
        homepageBtn = wx.Button(panel, ID_helpHomepage, "Homepage", size=(150, -1))
        homepageBtn.Bind(wx.EVT_BUTTON, self.presenter.onLibraryLink)
        
        githubBtn = wx.Button(panel, ID_helpGitHub, "GitHub", size=(150, -1))
        githubBtn.Bind(wx.EVT_BUTTON, self.presenter.onLibraryLink)
        
        citeBtn = wx.Button(panel, ID_helpCite, "How to Cite", size=(150, -1))
        citeBtn.Bind(wx.EVT_BUTTON, self.presenter.onLibraryLink)
        
        # pack element
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(image, 0, wx.CENTER|wx.ALL, 20)
        sizer.Add(title, 0, wx.CENTER|wx.LEFT|wx.RIGHT, 20)
        sizer.AddSpacer(10)
        sizer.Add(version, 0, wx.CENTER|wx.LEFT|wx.RIGHT, 20)
        sizer.AddSpacer(10)
        sizer.Add(message, 0, wx.CENTER|wx.LEFT|wx.RIGHT, 20)
        sizer.AddSpacer(10)
        sizer.Add(university, 0, wx.CENTER|wx.LEFT|wx.RIGHT, 20)
        sizer.AddSpacer(10)
        sizer.Add(copyright, 0, wx.CENTER|wx.LEFT|wx.RIGHT, 20)
        sizer.AddSpacer(20)
        sizer.Add(homepageBtn, 0, wx.CENTER|wx.LEFT|wx.RIGHT, 20)
        sizer.AddSpacer(10)
        sizer.Add(githubBtn, 0, wx.CENTER|wx.LEFT|wx.RIGHT, 20)
        sizer.AddSpacer(10)
        sizer.Add(citeBtn, 0, wx.CENTER|wx.LEFT|wx.RIGHT|wx.BOTTOM, 20)
        
        sizer.Fit(panel)
        return sizer
    # ----
    
    
    def onClose(self, evt):
        """Destroy this frame."""
        self.Destroy()
    # ----