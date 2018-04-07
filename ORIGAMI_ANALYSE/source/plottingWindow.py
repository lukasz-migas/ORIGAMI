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

# IMPORT LIBS
import wx
import matplotlib
matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.figure import Figure
from ZoomBox import ZoomBox, GetXValues
from wx.lib.pubsub import pub
import matplotlib.patches as patches
from numpy import amax, divide
from mpl_toolkits.mplot3d import Axes3D

from os.path import join, splitext, basename

try:
    from dialogs import dlgBox
except:
    pass

class plottingWindow(wx.Window):
    def __init__(self, *args, **kwargs):
        
        if "figsize" in kwargs:
             self.figure = Figure(figsize=kwargs["figsize"])
             self._axes = [0.1, 0.1, 0.8, 0.8]
             del kwargs["figsize"]
        else:          
            self.figure = Figure(figsize=[8,2.5])
        
        if 'config' in kwargs:
            self.config = kwargs['config']
            del kwargs["config"]
         
        self.figure.set_facecolor('white')
        
        wx.Window.__init__(self, *args, **kwargs)        
        self.canvas = FigureCanvasWxAgg(self, -1, self.figure)
        self.figure.set_facecolor('white')
        self.figure.set_edgecolor('white')
        self.canvas.SetBackgroundColour('white')
        
        # Create a resizer
        self.Bind(wx.EVT_SIZE, self.sizeHandler)
        self.resize = 1
        self.canvas.mpl_connect('motion_notify_event', self.onMotion)
        self.canvas.mpl_connect('pick_event', self.onPick)

        # Prepare for zoom
        self.zoom = None
        self.zoomtype = "box"
        
    def onPick(self, evt):
        pass
        # to be used to improve 3D plot
#         print(dir(evt.artist.get_xdata))
#         print('pick')
    
    def _generatePlotParameters(self):
        plot_parameters = {'grid_show':self.config._plots_grid_show,
                           'grid_color':self.config._plots_grid_color,
                           'grid_line_width':self.config._plots_grid_line_width,
                           'extract_color':self.config._plots_extract_color,
                           'extract_line_width':self.config._plots_extract_line_width,
                           'extract_crossover_sensitivity_1D':self.config._plots_extract_crossover_1D,
                           'extract_crossover_sensitivity_2D':self.config._plots_extract_crossover_2D,
                           'zoom_color_vertical':self.config._plots_zoom_vertical_color,
                           'zoom_color_horizontal':self.config._plots_zoom_horizontal_color,
                           'zoom_color_box':self.config._plots_zoom_box_color,
                           'zoom_line_width':self.config._plots_zoom_line_width,
                           'zoom_crossover_sensitivity':self.config._plots_zoom_crossover
                           }
        return plot_parameters
       
    def setupGetXAxies(self, plots):
        self.getxaxis =  GetXValues(plots)
       
    def setup_zoom(self, plots, zoom, data_lims=None, plotName=None,
                   plotParameters=None):
        if plotParameters == None:
            plotParameters = self._generatePlotParameters()
        
        if zoom == 'box':
            self.zoom = ZoomBox(plots, None, drawtype='box',
                                useblit=True, button=1,
                                onmove_callback=None, 
                                rectprops=dict(alpha=0.2, facecolor='yellow'),
                                spancoords='data', data_lims=data_lims,
                                plotName = plotName,
                                plotParameters = plotParameters)
        self.onRebootZoomKeys(evt=None)
                        
    def update_extents(self, extents):
        ZoomBox.update_extents(self.zoom, extents)
                         
    def onRebootZoomKeys(self, evt):
        """
        Reboot 'stuck' keys
        DOES NOT ACTUALLY WORK!
        """
        if self.zoom != None:
            ZoomBox.onRebootKeyState(self.zoom, evt=None)
        
    def onMotion(self, evt):
        """
        Triggered by pubsub from plot windows. Reports text in Status Bar.
        :param xpos: x position fed from event
        :param ypos: y position fed from event
        :return: None
        """
        pub.sendMessage('newxy', xpos=evt.xdata, ypos=evt.ydata)
        
    def testXYmaxVals(self,values=None):
        """ 
        Function to check whether x/y axis labels do not need formatting
        """
        if max(values) > 1000:
            divider = 1000
        elif max(values) > 1000000:
            divider = 1000000
        else:
            divider = 1
        return divider
    
    def testXYmaxValsUpdated(self,values=None):
        """ 
        Function to check whether x/y axis labels do not need formatting
        """
        baseDiv = 10
        increment = 10
        divider = baseDiv
        
        itemShape = values.shape
        if len(itemShape)>1: 
            maxValue = amax(values)
        elif len(itemShape) == 1:
            maxValue = max(values)
        else:
            maxValue = values
        while 10 <= (maxValue/divider) >= 1:
            divider = divider *increment
        
        expo = len(str(divider)) - len(str(divider).rstrip('0'))
        
        return divider, expo
   
    def repaint(self):
        """
        Redraw and refresh the plot.
        :return: None
        """
        self.canvas.draw()
        
    def clearPlot(self, *args):
        """
        Clear the plot and rest some of the parameters.
        :param args: Arguments
        :return:
        """
        self.figure.clear()
        try:
            self.cax = None
        except:
            pass
        
        try:
            self.plotMS = None
        except:
            pass
        self.repaint()
            
    def sizeHandler(self, *args, **kwargs):
        if self.resize == 1:
            self.canvas.SetSize(self.GetSize())
            
    def onselect(self, ymin, ymax):
        pass

    def saveFigure(self, path, transparent, dpi, **kwargs):
        """
        Saves figures in specified location. 
        Transparency and DPI taken from config file
        """
        self.figure.savefig(path, transparent=transparent, dpi=dpi, **kwargs)

    def saveFigure2(self, path, **kwargs):
        """
        Saves figures in specified location. 
        Transparency and DPI taken from config file
        """
        # check if plot exists
        if not hasattr(self, 'plotMS'): 
            print('Cannot save a plot that does not exist')
            return 
    
        # Get resize parameter
        resizeName = kwargs.get('resize', None)
        resizeSize = None
        
        if resizeName != None:
            resizeSize = self.config._plotSettings[resizeName]['resize_size']
        
        if resizeSize != None:
            dpi = wx.ScreenDC().GetPPI() 
            # Calculate new size
            figsizeNarrowPix = (int(resizeSize[0]*dpi[0]), int(resizeSize[1]*dpi[1]))
            # Set new canvas size and reset the view
            self.canvas.SetSize(figsizeNarrowPix)
            self.canvas.draw()
            # Get old and new plot sizes
            oldAxesSize = self.plotMS.get_position()
            newAxesSize = self.config._plotSettings[resizeName]['save_size']
            try:
                self.plotMS.set_position(newAxesSize)
            except RuntimeError:
                self.plotMS.set_position(oldAxesSize)
                
            self.repaint()
        
        # Save figure
        try:
            self.figure.savefig(path, **kwargs)
        except IOError:
            # reset axes size
            if resizeSize != None:
                self.plotMS.set_position(oldAxesSize)
                self.sizeHandler()
            # warn user
            from dialogs import dlgBox
            dlgBox(exceptionTitle='Warning', 
                   exceptionMsg= "Cannot save file: %s as it appears to be currently open or the folder doesn't exist" % path,
                   type="Error")
            # get file extension
            fname, delimiter_txt = splitext(path)
            try: bname = basename(fname)
            except: bname = ""
             
            fileType = "Image file (%s)|*%s" % (delimiter_txt, delimiter_txt)
            dlg =  wx.FileDialog(None, "Save as...",
                                 "", "", fileType, wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
            dlg.SetFilename(bname)
             
            if dlg.ShowModal() == wx.ID_OK:
                fname, __ = splitext(dlg.GetPath())
                path = join(fname + delimiter_txt)
                
                # reset axes, again
                if resizeSize != None:
                    self.canvas.SetSize(figsizeNarrowPix)
                    self.canvas.draw()
                    try:
                        self.plotMS.set_position(newAxesSize)
                    except RuntimeError:
                        self.plotMS.set_position(oldAxesSize)
                    self.repaint()
                
                try:
                    self.figure.savefig(path, **kwargs)
                except: pass
        
        # Reset previous view
        if resizeSize != None:
            self.plotMS.set_position(oldAxesSize)
            self.sizeHandler()

    def onAddMarker(self, xval=None, yval=None, marker='s', color='r', size=5,
                    testMax='none'):
        """ 
        This function adds a marker to 1D plot
        """
        if testMax == 'yvals':
            ydivider, expo = self.testXYmaxValsUpdated(values=yval)
            if expo > 1:
                yvals = divide(yval, float(ydivider))
        
        self.plotMS.plot(xval, yval, color=color, marker=marker, 
                         linestyle='None', markersize=size)
        
    def addText(self, xval=None, yval=None, text=None, rotation=90, color="k",
                fontsize=16,weight=True):
        """
        This function annotates the MS peak
        """
        # Change label weight
        if weight:weight='bold'
        else: weight='regular'
        
        self.text = self.plotMS.text(x=xval, y=yval, 
                                     s=text, 
                                     fontsize=fontsize,
                                     rotation=rotation,
                                     weight=weight, 
                                     fontdict=None,
                                     color=color)
        
    def addRectangle(self, x, y, width, height, color='green',
                     alpha=0.5, linewidth=0):
        """
        Add rect patch to plot
        """
        # (x,y), width, height, alpha, facecolor, linewidth
        self.plotMS.add_patch(patches.Rectangle( (x, y), width, height,
                                                 color=color, 
                                                 alpha=alpha,
                                                 linewidth=linewidth))
            
    def onZoomIn(self, startX, endX, endY):
        self.plotMS.axis([startX, endX, 0, endY])
        
    def onZoom2D(self, startX, endX, startY, endY):
        self.plotMS.axis([startX, endX, startY, endY])
        
    def onZoom1D(self, startX, endX):
        # Retrieve current axis values
        try:
            x1, x2, y1, y2 = self.plotMS.axis()
        except AttributeError: 
            print('No waterfall plot - replot data')
        # Set updated values
        self.plotMS.axis([startX, endX, y1, y2])
        
    def onZoomRMSF(self, startX, endX):
        x1, x2, y1, y2 = self.plotRMSF.axis()
        self.plotRMSF.axis([startX, endX, y1, y2])
        
    def onGetXYvals(self, axes='both'):
        xvals = self.plotMS.get_xlim()
        yvals = self.plotMS.get_ylim()
        if axes=='both': 
            return xvals, yvals
        elif axes=='x':
            return xvals
        elif axes=='y':
            return yvals
        
    def getPlotName(self):
        plotName = self.plot_name
        return plotName
    
    def getAxesSize(self):
        axesSize = self._axes
        return axesSize
    
    
    
    