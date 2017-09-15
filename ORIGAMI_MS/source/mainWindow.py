# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
#    Copyright (C) 2017 Lukasz G. Migas <lukasz.migas@manchester.ac.uk>

#    This program is free software. Feel free to redistribute it and/or 
#    modify it under the condition you cite and credit the authors whenever 
#    appropriate. 
#    The program is distributed in the hope that it will be useful but is 
#    provided WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE
# -------------------------------------------------------------------------

# Load libraries
import wx
import wx.aui
import sys
from time import clock, gmtime, strftime
from wx.lib.pubsub import pub 
from wx import ID_ANY
from origamiStyles import makeMenuItem

# Print OS version
print(sys.version)

# Import ORIGAMI libraries
from panelControls import panelControls
from panelPlot import panelPlot
from panelAbout import panelAbout
from IDs import *

class MyFrame(wx.Frame):

    def __init__(self, parent, config, icons, id=-1, title='ORIGAMI-MS',  
                 pos=wx.DefaultPosition, size=(750, 600),
                 style=wx.NO_FULL_REPAINT_ON_RESIZE): 
        wx.Frame.__init__(self, None, title=title)
        
        
        self.SetDimensions(0,0,600,700)
        self.Centre()
        
        self.presenter = parent
        self.config = config
        self.icons = icons
        
        try:
            icon = wx.Icon('icon.ico', wx.BITMAP_TYPE_ICO, 16, 16)
            self.SetIcon(icon)
        except: pass
        
        # Setup Notebook manager
        self._mgr = wx.aui.AuiManager(self)
        self._mgr.SetDockSizeConstraint(1, 1)
        
        self.panelControls = panelControls(self, self.presenter, self.config) # Settings
        self.panelPlots = panelPlot(self) # Settings
        
        
        self._mgr.AddPane(self.panelControls, wx.aui.AuiPaneInfo().Top().CloseButton(False)
                          .GripperTop().MinSize((400,200)).Gripper(False).BottomDockable(False)
                          .TopDockable(False).CaptionVisible(False).Resizable(False))

        self._mgr.AddPane(self.panelPlots, wx.aui.AuiPaneInfo().Bottom().CloseButton(False)
                          .GripperTop(False).MinSize((500,400)).Gripper(False).BottomDockable(False)
                          .TopDockable(False).CaptionVisible(False).Resizable(False))
        
        # Load other parts
        self._mgr.Update() 
        self.statusBar()
        self.makeMenubar()
        
    def makeMenubar(self):
        
        # FILE MENU
        self.mainMenu = wx.MenuBar()
        menuFile = wx.Menu()
        menuFile.Append(ID_setMassLynxPath,'Set MassLynx file path\tCtrl+O')
        menuFile.AppendSeparator()
        menuFile.Append(ID_importConfigFile,'Import configuration file\tCtrl+C')
        menuFile.Append(ID_exportConfigFile,'Export configuration file\tCtrl+Shift+C')
        
        self.mainMenu.Append(menuFile, "&File")
        
        # HELP MENU
        menuHelp = wx.Menu()
        menuHelp.Append(ID_helpNewVersion, 'Check for updates...')
        menuHelp.Append(ID_helpCite, 'Paper to cite...')
        menuHelp.AppendSeparator()
        menuHelp.AppendItem(makeMenuItem(parent=menuHelp, 
                                         id=ID_SHOW_ABOUT,
                                         text='About ORIGAMI\tCtrl+Shift+A'))
        self.mainMenu.Append(menuHelp, '&Help')
        
        self.SetMenuBar(self.mainMenu)              
        
        self.Bind(wx.EVT_MENU, self.presenter.onGetMassLynxPath, id=ID_setMassLynxPath)
        self.Bind(wx.EVT_MENU, self.presenter.importConfigFile, id=ID_importConfigFile)
        self.Bind(wx.EVT_MENU, self.presenter.onExportConfig, id=ID_exportConfigFile)
        
        self.Bind(wx.EVT_MENU, self.onHelpAbout, id=ID_SHOW_ABOUT)
        self.Bind(wx.EVT_MENU, self.presenter.onLibraryLink, id=ID_helpCite)
        self.Bind(wx.EVT_MENU, self.presenter.onLibraryLink, id=ID_helpNewVersion) 
        
    def onHelpAbout(self, evt):
        """Show About mMass panel."""
        about = panelAbout(self, self.presenter, 
                           'About ORIGAMI', 
                           self.config,
                           self.icons)
        about.Centre()
        about.Show()
        about.SetFocus()

    def statusBar(self):
        self.mainStatusbar = self.CreateStatusBar(3, wx.ST_SIZEGRIP, wx.ID_ANY)
        self.mainStatusbar.SetStatusWidths([120,50,-1])
        
        
    def OnMotion(self, xpos, ypos):
        """
        Triggered by pubsub from plot windows. Reports text in Status Bar.
        :param xpos: x position fed from event
        :param ypos: y position fed from event
        :return: None
        """
        if xpos is not None and ypos is not None:
            self.SetStatusText("X=%.2f Y=%.2f" % (xpos, ypos), number=0)
        pass
    
    
    
    
    
    
    
    
        