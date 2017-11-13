# IMPORT LIBS
import wx
from matplotlib import interactive
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.figure import Figure
from ZoomBox import ZoomBox, GetXValues
import NoZoomSpan
from wx.lib.pubsub import pub
import matplotlib.patches as patches
from matplotlib.patches import Rectangle
from numpy import amax, divide


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

        # Prepare for zoom
        self.zoom = None
        self.zoomtype = "box"
       
    def setupGetXAxies(self, plots):
        self.getxaxis =  GetXValues(plots)
       
    def setup_zoom(self, plots, zoom, data_lims=None, plotName=None):
        if zoom == 'box':
            self.zoom = ZoomBox(plots, None, drawtype='box',
                                useblit=True, button=1,
                                onmove_callback=None, 
                                rectprops=dict(alpha=0.2, facecolor='yellow'),
                                spancoords='data',
                                data_lims=data_lims,
                                plotName = plotName)
                  
        self.onRebootZoomKeys(evt=None)
                  
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
        # Get resize parameter
        resizeName = kwargs.pop('resize', None)
        
        resizeSize = self.config.plotResize.get(resizeName, None)
        
        if resizeSize != None:
            dpi = wx.ScreenDC().GetPPI() 
            # Calculate new size
            figsizeNarrowPix = (int(resizeSize[0]*dpi[0]), int(resizeSize[1]*dpi[1]))
            # Set new canvas size and reset the view
            self.canvas.SetSize(figsizeNarrowPix)
            self.canvas.draw()
            # Get old and new plot sizes
            oldAxesSize = self.plotMS.get_position()
            newAxesSize = self.config.savePlotSizes[resizeName]
            try:
                self.plotMS.set_position(newAxesSize)
            except RuntimeError:
                self.plotMS.set_position(oldAxesSize)
                
            self.repaint()
        
        # Save figure
        self.figure.savefig(path, **kwargs)
        
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
        
        self.plotMS.text(x=xval, y=yval, 
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
        
# 	def colorbar(mappable):
#         # http://joseph-long.com/writing/colorbars/
#         # TODO : this needs a lot of work! currently not implemented
#         self.plotMS = mappable.axes
#         fig = self.plotMS.figure
#         divider = make_axes_locatable(ax)
#         cax = divider.append_axes("right", size="5%", pad=0.05)
#         return fig.colorbar(mappable, cax=cax)
        
