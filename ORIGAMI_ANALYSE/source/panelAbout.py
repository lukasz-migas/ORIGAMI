# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
#    Copyright (C) 2017 Lukasz G. Migas <lukasz.migas@manchester.ac.uk>
# 
#	 GitHub : https://github.com/lukasz-migas/ORIGAMI
#	 University of Manchester IP : https://www.click2go.umip.com/i/s_w/ORIGAMI.html
#	 Cite : 10.1016/j.ijms.2017.08.014
#
#    This program is free software. Feel free to redistribute it and/or 
#    modify it under the condition you cite and credit the authors whenever 
#    appropriate. 
#    The program is distributed in the hope that it will be useful but is 
#    provided WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE
# -------------------------------------------------------------------------

# load libs
import wx

# load modules
from ids import (ID_helpCite, ID_helpGitHub, ID_helpReportBugs, ID_helpNewFeatures,
                 ID_helpHomepage)

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
        BOLD_FONT = wx.Font(11, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        NORMAL_FONT = wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        # make elements
        panel = wx.Panel(self, -1)
        
        image = wx.StaticBitmap(panel, -1, self.icons.getLogo)
        
        title = wx.StaticText(panel, -1, "ORIGAMI")
        title.SetFont(BOLD_FONT)
        
        versionLabel = 'Version %s' % self.config.version
        version = wx.StaticText(panel, -1, versionLabel, style=wx.ALIGN_CENTRE)
        version.SetFont(wx.NORMAL_FONT)
        
        about_msg = 'If you encounter any problems, have questions or would like to send some feedback,\n' + \
                    '            please contact Lukasz Migas at lukasz.migas@manchester.ac.uk.'
        
        message = wx.StaticText(panel, -1, about_msg)
        message.SetFont(wx.SMALL_FONT)
        
        university = wx.StaticText(panel, -1, "University of Manchester")
        university.SetFont(wx.SMALL_FONT)
        
        copyright = wx.StaticText(panel, -1, "(c) 2017 Lukasz G. Migas")
        copyright.SetFont(NORMAL_FONT)
        
        homepageBtn = wx.Button(panel, ID_helpHomepage, "Homepage", size=(150, -1))
        homepageBtn.Bind(wx.EVT_BUTTON, self.presenter.onLibraryLink)
        
        githubBtn = wx.Button(panel, ID_helpGitHub, "GitHub", size=(150, -1))
        githubBtn.Bind(wx.EVT_BUTTON, self.presenter.onLibraryLink)
        
        citeBtn = wx.Button(panel, ID_helpCite, "How to Cite", size=(150, -1))
        citeBtn.Bind(wx.EVT_BUTTON, self.presenter.onLibraryLink)
        
        newFeaturesBtn = wx.Button(panel, ID_helpNewFeatures, "Request New Features", size=(150, -1))
        newFeaturesBtn.Bind(wx.EVT_BUTTON, self.presenter.onLibraryLink)
        
        reportBugBtn = wx.Button(panel, ID_helpReportBugs, "Report Bugs", size=(150, -1))
        reportBugBtn.Bind(wx.EVT_BUTTON, self.presenter.onLibraryLink)
        
        btn_grid = wx.GridBagSizer(2, 2)
        y = 0
        btn_grid.Add(homepageBtn, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        btn_grid.Add(githubBtn, (y,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        btn_grid.Add(citeBtn, (y,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        
        btn2_grid = wx.GridBagSizer(2, 2)
        y = 0
        btn2_grid.Add(newFeaturesBtn, (y,0), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
        btn2_grid.Add(reportBugBtn, (y,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
        
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
        sizer.AddSpacer(10)
        sizer.Add(btn2_grid, 0, wx.CENTER|wx.LEFT|wx.RIGHT, 20)
        sizer.AddSpacer(10)
        sizer.Add(btn_grid, 0, wx.CENTER|wx.LEFT|wx.RIGHT, 20)
        sizer.AddSpacer(10)
        
        sizer.Fit(panel)
        return sizer
    # ----
    
    
    def onClose(self, evt):
        """Destroy this frame."""
        self.Destroy()
    # ----