# -*- coding: utf-8 -*- 
"""
@author: Lukasz G. Migas
"""

import wx
import os
from styles import makeMenuItem
from ids import ID_log_save_log, ID_log_go_to_directory, ID_log_clear_window, ID_extraSettings_logging

# TODO: LOG should wrap text to ensure it fits on the screen

class panelLog(wx.Panel):

    def __init__( self, parent, config, icons):
        wx.Panel.__init__(self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition,
                          size = wx.Size(600,200), style = wx.TAB_TRAVERSAL)

        
        self.config = config
        self.icons = icons
        self.parent = parent
        
        style = wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL|wx.TE_WORDWRAP
        self.log = wx.TextCtrl(self, wx.ID_ANY, size=(-1,-1),
                               style=style)
        self.log.Bind(wx.EVT_TEXT, self.saveLogData)
        
        self.log.SetBackgroundColour(wx.BLACK)
        self.log.SetForegroundColour(wx.GREEN)
        
        logSizer = wx.BoxSizer(wx.VERTICAL)     
        logSizer.Add(self.log, 1, wx.EXPAND)
        self.SetSizer(logSizer) 
        
        wx.EVT_CLOSE(self, self.onClose)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnRightClickMenu)

    def saveLogData(self, evt):
        
#         if self.config.loggingFile_path is None:
#             self.config.loggingFile_path = "logs\\MSIML_%s.log" % self.config.startTime
#             print('\nGenerated log filename: %s' % self.config.loggingFile_path)

        try:
            savefile = open(self.config.loggingFile_path,'w')
            savefile.write(self.log.GetValue())
            savefile.close()
        except:
            pass
  
    def clearLogData(self, evt):
        self.log.SetValue("")
        
    def onGoToDirectory(self, evt=None):
        '''
        Go to selected directory
        '''
        path = os.path.join(self.config.cwd, "logs")
        self.parent.presenter.openDirectory(path=path)
        
    def saveLogDataAs(self, evt):
        dlg = wx.FileDialog(self, "Save log file...", wildcard = "*.log" ,
                           style=wx.FD_DEFAULT_STYLE | wx.FD_CHANGE_DIR)
        path = os.path.join(self.config.cwd, "logs", "ORIGAMI_logfile.log")
        dlg.SetPath(path)
        if dlg.ShowModal() == wx.ID_OK:
            fileName=dlg.GetPath()
            savefile = open(fileName,'w')
            savefile.write(self.log.GetValue())
            savefile.close()
        
    def onClose(self, evt):
        """Destroy this frame."""
        self.config._windowSettings['Log']['show'] = False
        self.parent._mgr.GetPane(self).Hide()
        self.parent._mgr.Update()
    # ----
    
    def OnRightClickMenu(self, evt):
        
        self.Bind(wx.EVT_MENU, self.saveLogDataAs, id=ID_log_save_log)
        self.Bind(wx.EVT_MENU, self.onGoToDirectory, id=ID_log_go_to_directory)
        self.Bind(wx.EVT_MENU, self.clearLogData, id=ID_log_clear_window)
        self.Bind(wx.EVT_MENU, self.onLogging, id=ID_extraSettings_logging)
        
        menu = wx.Menu()
        self.logToFile = menu.AppendItem(makeMenuItem(parent=menu, id=ID_extraSettings_logging, 
                                                      text="Enable/disable logging ", 
                                                      bitmap=None,
                                                      kind=wx.ITEM_CHECK))
        self.logToFile.Check(self.config.logging)
        menu.AppendSeparator()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_log_go_to_directory, 
                                     text="Go to folder with log files... ", 
                                     bitmap=self.icons.iconsLib['folder_path_16']))
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_log_save_log, 
                                     text="Save log to new file", 
                                     bitmap=self.icons.iconsLib['save16']))
        menu.AppendSeparator()
        menu.AppendItem(makeMenuItem(parent=menu, id=ID_log_clear_window, 
                                     text="Clear current log file",
                                     bitmap=self.icons.iconsLib['clear_16']))
        
        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()
        
    def onLogging(self, evt):
         
        self.config.logging = not self.config.logging
 
        if self.config.logging: msg = "Logging events/warnings/errors to file in: %s" % self.config.cwd
        else: msg = "Logging to file was disabled"
        # fire events
        self.parent.onEnableDisableLogging(evt=None)
             
        print(msg)
        self.parent.presenter.onThreading(None, (msg, 4) , action='updateStatusbar')
