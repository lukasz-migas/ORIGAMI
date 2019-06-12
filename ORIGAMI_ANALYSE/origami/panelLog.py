# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
#    Copyright (C) 2017-2018 Lukasz G. Migas 
#    <lukasz.migas@manchester.ac.uk> OR <lukas.migas@yahoo.com>
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
# __author__ lukasz.g.migas

import wx, os
from styles import makeMenuItem
from ids import (ID_log_save_log, ID_log_go_to_directory, 
                 ID_log_clear_window, ID_extraSettings_logging)

# import threading

# TODO: LOG should wrap text to ensure it fits on the screen

class panelLog(wx.Panel):

    def __init__( self, parent, config, icons):
        wx.Panel.__init__(self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition,
                          size = wx.Size(600,200), style = wx.TAB_TRAVERSAL)

        
        self.config = config
        self.icons = icons
        self.parent = parent
        self.logFile = None
        
        style = wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL|wx.TE_WORDWRAP
        self.log = wx.TextCtrl(self, wx.ID_ANY, size=(-1,-1), style=style)
        self.log.Bind(wx.EVT_TEXT, self.saveLogData)
        
        self.log.SetBackgroundColour(wx.BLACK)
        self.log.SetForegroundColour(wx.GREEN)
        
        logSizer = wx.BoxSizer(wx.VERTICAL)     
        logSizer.Add(self.log, 1, wx.EXPAND)
        self.SetSizer(logSizer) 
        
        wx.EVT_CLOSE(self, self.on_close)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnRightClickMenu)

#     def saveLogDataThreaded(self, evt):
#         
#         if self.logFile is None:
#             return
#         
#         if not self.config.threading:
#             self.saveLogData(evt)
#         else:
#             print("threading")
#             th = threading.Thread(target=self.saveLogData, args=(evt,))
#             # Start thread
#             try: th.start()
#             except: print('exception')

    def saveLogData(self, evt):
        
        if self.logFile is None:
            return
            
#         try:
# #             savefile = open(self.config.loggingFile_path,'w')
#             try: 
#                 self.logFile.write(self.log.GetValue())
#             except: 
#                 pass
# #             savefile.close()
#         except:
#             pass
  
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
        
    def on_close(self, evt):
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
 
        # fire events
        self.parent.onEnableDisableLogging(evt=None)
 
        if self.config.logging: 
            msg = "Logging events/warnings/errors to file in: {}".format(self.config.loggingFile_path)
            self.logFile = open(self.config.loggingFile_path,'w')
        else: 
            msg = "Logging to file was disabled"
            try:
                self.logFile.close()
            except: pass
            self.logFile = None
        
        self.parent.presenter.onThreading(None, (msg, 4) , action='updateStatusbar')








