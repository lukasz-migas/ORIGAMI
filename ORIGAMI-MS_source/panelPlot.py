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

import wx
import matplotlib
from matplotlib import interactive
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D
from plottingWindow import plottingWindow
from time import clock, gmtime, strftime

class panelPlot (wx.Panel):
    def __init__( self, parent):
        wx.Panel.__init__ ( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition,
                             size = wx.Size( 350, 600 ), style = wx.TAB_TRAVERSAL )
        
        self.parent = parent
        self.currentPage = None
        self.startTime = (strftime("%H-%M-%S_%d-%m-%Y", gmtime()))
        
        self.makeNotebook()

    def makeNotebook(self):
        mainSizer = wx.BoxSizer( wx.VERTICAL )
        # Setup notebook
        self.plotNotebook = wx.Notebook(self, wx.ID_ANY, wx.DefaultPosition,
                                        wx.DefaultSize, 0)
        
        # Setup PLOT SPV
        self.panelSPV = wx.Panel( self.plotNotebook, wx.ID_ANY, wx.DefaultPosition,
                                    wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.plotNotebook.AddPage( self.panelSPV, u"SPVs", False )
        
        self.plot1 = plot1D(self.panelSPV)
        box1 = wx.BoxSizer(wx.VERTICAL)
        box1.Add(self.plot1, 1, wx.EXPAND)
        self.panelSPV.SetSizer(box1)

        self.panelTime = wx.Panel( self.plotNotebook, wx.ID_ANY, wx.DefaultPosition,
                                    wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.plotNotebook.AddPage( self.panelTime, u"Acquisition", False )
        
        self.plot2 = plot1D(self.panelTime)
        box2 = wx.BoxSizer(wx.VERTICAL)
        box2.Add(self.plot2, 1, wx.EXPAND)
        self.panelTime.SetSizer(box2)
        
        
        # Setup LOG 
        self.panelLog = wx.Panel( self.plotNotebook, wx.ID_ANY, wx.DefaultPosition, 
                                   wx.DefaultSize, wx.TAB_TRAVERSAL )

        self.plotNotebook.AddPage( self.panelLog, u"ORIGAMI Log", False )
        
        style = wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL|wx.TE_WORDWRAP
        self.log = wx.TextCtrl(self.panelLog, wx.ID_ANY, size=(-1,-1),
                          style=style)
        self.log.SetBackgroundColour(wx.BLACK)
        self.log.SetForegroundColour(wx.GREEN)
        
        logSizer = wx.BoxSizer(wx.VERTICAL)     
        logSizer.Add(self.log, 1, wx.EXPAND)
        self.panelLog.SetSizer(logSizer) 
        
        self.log.Bind(wx.EVT_TEXT, self.saveLogData)
        
        
#         self.panelTable = wx.Panel( self.plotNotebook, wx.ID_ANY, wx.DefaultPosition,
#                                     wx.DefaultSize, wx.TAB_TRAVERSAL )
#         self.plotNotebook.AddPage( self.panelTable, u"CV Table", False )        


        mainSizer.Add( self.plotNotebook, 1, wx.EXPAND |wx.ALL, 1)   
        self.SetSizer(mainSizer)
        self.Layout()
        self.Show(True)
        
        
    def saveLogData(self, evt):
        fileName = ''.join(['ORIGAMI_log__',self.startTime,'.log'])
        savefile = open(fileName,'w')
        savefile.write(self.log.GetValue())
        savefile.close()
        
class plot1D(plottingWindow):
    def __init__(self, *args, **kwargs):
        plottingWindow.__init__(self, *args, **kwargs)
        self.plotflag = False
        
    def plot1Ddata(self, xvals, yvals, xlabel, ylabel, title, zoom="box",
                   axesSize=None, fontsize=10):
        
        self.plotflag = True # Used only if saving data
        self.zoomtype = zoom
        if axesSize == None: self._axes = [0.15, 0.2, 0.8, 0.7]
        else: self._axes = axesSize
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.figure.set_facecolor('white')
        self.figure.set_edgecolor('white')
        self.canvas.SetBackgroundColour('white')
        matplotlib.rc('xtick', labelsize=fontsize)
        matplotlib.rc('ytick', labelsize=fontsize)
        
        self.plotSPV = self.figure.add_axes(self._axes)
        self.plotSPV.plot(xvals, yvals, color='black')
        
        self.plotSPV.set_xlim([min(xvals),max(xvals)])
        self.plotSPV.set_ylim([min(yvals)-1,max(yvals)+1])
        
        self.plotSPV.set_xlabel(self.xlabel, fontsize=fontsize, weight='normal')
        self.plotSPV.set_ylabel(self.ylabel, fontsize=fontsize, weight='normal')

        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        