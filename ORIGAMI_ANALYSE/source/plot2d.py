from __future__ import division
from plottingWindow import plottingWindow
from numpy import arange, sin, pi, min, max, random, amax
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.colors import LogNorm
from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from toolbox import *
import seaborn as sns
from matplotlib import cm


# TODO:
# play with colorbars = http://nbviewer.jupyter.org/github/mgeier/python-audio/blob/master/plotting/matplotlib-colorbar.ipynb
# http://matplotlib.org/mpl_toolkits/axes_grid/users/overview.html#axesdivider

class plot2D(plottingWindow):
    def __init__(self, *args, **kwargs):
        plottingWindow.__init__(self, *args, **kwargs)
        self.plotflag = False # Used only if saving data

        
    def getNewLabelSizes(self):
        self.titleFontSize = self.config.titleFontSize
        self.titleFontWeight = self.config.titleFontWeight
        if self.titleFontWeight: self.titleFontWeight = 'bold'
        else: self.titleFontWeight = 'normal'
        
        self.labelFontSize = self.config.labelFontSize
        self.labelFontWeight = self.config.labelFontWeight
        if self.labelFontWeight: self.labelFontWeight = 'bold'
        else: self.labelFontWeight = 'normal'
        
        self.tickFontSize = self.config.tickFontSize
        
    def extents(self,f):
        delta = f[1] - f[0]
        return [f[0] - delta/2, f[-1] + delta/2]
     
    def plotNew2Dplot2(self, zvals=None, title="", cmap='inferno', interpolation='None',
                      labelsX=None, labelsY=None, xlabel="", ylabel="", zoom="box", 
                      colorbar=False, fontsize=12, cmapNorm=None, axesSize=None,
                      plotName=None, **kwargs):      
        """
        labelX, labelY = list of values used for extent of the figure
        """
        self.plotflag = True # Used only if saving data
        self.zoomtype = zoom
        if axesSize == None: self._axes = [0.1, 0.1, 0.85, 0.85]
        else: self._axes = axesSize
        self.xlabel = xlabel
        self.ylabel = ylabel
        
        self.getNewLabelSizes()
        
        matplotlib.rc('xtick', labelsize=self.labelFontSize)
        matplotlib.rc('ytick', labelsize=self.labelFontSize)
        
        if colorbar:
            self._axes = [0.1, 0.1, 0.8, 0.85]
        # Plot 
        self.plotMS = self.figure.add_axes(self._axes)
        extent = self.extents(labelsX)+self.extents(labelsY)
        self.cax = self.plotMS.imshow(zvals, 
                                      cmap=cmap, 
                                      interpolation=interpolation,
                                      extent=extent,
                                      aspect='auto', 
                                      origin='lower',
                                      norm=cmapNorm)
        
        cbarDivider = make_axes_locatable(self.plotMS)
           
        # Extent for zoom is slight different
#         extent= [labelsX[0], labelsY[0], labelsX[-1],labelsY[-1]] 
        extent= [extent[0], extent[2], extent[1], extent[3]] 
        self.setup_zoom([self.plotMS], self.zoomtype, data_lims=extent,
                        plotName=plotName)
        
        if colorbar:
            # https://stackoverflow.com/questions/18195758/set-matplotlib-colorbar-size-to-match-graph
            # pad controls how close colorbar is to the axes
            cbarWidth = "".join([str(self.config.colorbarWidth), "%"])
            cax = cbarDivider.append_axes("right", size=cbarWidth, pad=self.config.colorbarPad)
            self.figure.colorbar(self.cax, cax=cax)
        else: pass
        
        self.plotMS.set_xlabel(self.xlabel, fontsize=self.labelFontSize, 
                               weight=self.labelFontWeight)
        self.plotMS.set_ylabel(self.ylabel, fontsize=self.labelFontSize, 
                               weight=self.labelFontWeight)
        
        self.plotMS.tick_params(labelsize=self.tickFontSize)

    def plotNew2DContourPlot2(self, zvals=None, labelsX=None, xlabel="", labelsY=None, ylabel="", 
                              title="", cmap='inferno', zoom="box", colorbar=False, fontsize=12,
                              pretty=True, cmapNorm=None, axesSize=None,
                              plotName=None, **kwargs):      
        
        self.plotflag = True # Used only if saving data
        self.zoomtype = zoom
        if axesSize == None: self._axes = [0.1, 0.1, 0.85, 0.85]
        else: self._axes = axesSize
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.getNewLabelSizes()
        
        matplotlib.rc('xtick', labelsize=self.labelFontSize)
        matplotlib.rc('ytick', labelsize=self.labelFontSize)   
        
        if colorbar:
            self._axes = [0.1, 0.1, 0.8, 0.85]

        # Plot 
        self.plotMS = self.figure.add_axes(self._axes)
        extent = self.extents(labelsX)+self.extents(labelsY)
        if pretty == True:
            maxV = amax(zvals)
            if maxV == 1: step = 0.02
            else: step = 500
            levels = np.arange(0.0, maxV, step) + step
            print(len(levels))
            self.cax = self.plotMS.contourf(labelsX, 
                                            labelsY, 
                                            zvals, 
                                            levels, 
                                            cmap=cmap, 
                                            antialiasing=True,
                                            norm=cmapNorm)
        else:
            self.cax = self.plotMS.contourf(labelsX, 
                                            labelsY, 
                                            zvals, 
                                            cmap=cmap, 
                                            antialiasing=True,
                                            norm=cmapNorm)
        
        cbarDivider = make_axes_locatable(self.plotMS)
        
        extent= [labelsX[0], labelsY[0], labelsX[-1],labelsY[-1]] # [xmin, ymin, xmax, ymax] 
        self.setup_zoom([self.plotMS], self.zoomtype, data_lims=extent,
                        plotName=plotName) 
            
        if colorbar:
            # https://stackoverflow.com/questions/18195758/set-matplotlib-colorbar-size-to-match-graph
            # pad controls how close colorbar is to the axes
            cbarWidth = "".join([str(self.config.colorbarWidth), "%"])
            cax = cbarDivider.append_axes("right", size=cbarWidth, 
                                          pad=self.config.colorbarPad)
            self.figure.colorbar(self.cax, cax=cax)
        else: pass
                    
        self.plotMS.set_xlabel(self.xlabel, fontsize=self.labelFontSize, 
                               weight=self.labelFontWeight)
        self.plotMS.set_ylabel(self.ylabel, fontsize=self.labelFontSize, 
                               weight=self.labelFontWeight)
        
        self.plotMS.tick_params(labelsize=self.tickFontSize)
              
    def plotNew2DoverlayPlot(self, zvalsIon1=None, zvalsIon2=None, cmapIon1='Reds',
                             cmapIon2='Greens', alphaIon1=1, alphaIon2=1,
                             interpolation='None', labelsX=None,
                             labelsY=None, xlabel="", ylabel="", zoom="box", 
                             colorbar=False,axesSize=None, plotName=None,
                              **kwargs):
        
        self.plotflag = True # Used only if saving data
        self.zoomtype = zoom
        if axesSize == None: self._axes = [0.1, 0.1, 0.85, 0.85]
        else: self._axes = axesSize
        self.xlabel = xlabel
        self.ylabel = ylabel

        
        # Set axis label size
        self.getNewLabelSizes()
        if colorbar:
            self._axes = [0.1, 0.1, 0.8, 0.85]
        
        matplotlib.rc('xtick', labelsize=self.labelFontSize)
        matplotlib.rc('ytick', labelsize=self.labelFontSize)      
        # Add plot to canvas 
        self.plotMS = self.figure.add_axes(self._axes)
        
        extent = self.extents(labelsX)+self.extents(labelsY)
        self.plotMS.imshow(zvalsIon1, cmap=cmapIon1, interpolation=interpolation,
                            extent=extent, aspect='auto', origin='lower', alpha=alphaIon2)
        plotMS2 = self.plotMS.imshow(zvalsIon2, cmap=cmapIon2, interpolation=interpolation,
                            extent=extent, aspect='auto', origin='lower', alpha=alphaIon2) 
        
#         extent= [labelsX[0], labelsY[0], labelsX[-1],labelsY[-1]] # [xmin, ymin, xmax, ymax]
        extent= [extent[0], extent[2], extent[1], extent[3]] 
        self.setup_zoom([self.plotMS], self.zoomtype, data_lims=extent,
                        plotName=plotName)  
        
        cbarDivider = make_axes_locatable(self.plotMS)
            
        if colorbar:
            # https://stackoverflow.com/questions/18195758/set-matplotlib-colorbar-size-to-match-graph
            # pad controls how close colorbar is to the axes
            cbarWidth = "".join([str(self.config.colorbarWidth), "%"])
            cax = cbarDivider.append_axes("right", size=cbarWidth, pad=self.config.colorbarPad)
            self.figure.colorbar(plotMS2, cax=cax)
        else: pass

        
        self.plotMS.set_xlabel(self.xlabel, fontsize=self.labelFontSize, 
                               weight=self.labelFontWeight)
        self.plotMS.set_ylabel(self.ylabel, fontsize=self.labelFontSize, 
                               weight=self.labelFontWeight)
        
        self.plotMS.tick_params(labelsize=self.tickFontSize)
        
    def plotNew2DmatrixPlot(self, zvals=None, xylabels=None, cmap='inferno', interpolation='None', 
                            xNames=None, zoom="box", axesSize=None,colorbar=False, 
                            plotName=None, **kwargs):
        """
        Plot the pairwise RMSD matrix
        """
        
        self.plotflag = True # Used only if saving data
        self.zoomtype=zoom
        if axesSize == None: self._axes = [0.2, 0.2, 0.6, 0.6]
        else: self._axes = axesSize
#         self.figure.set_facecolor('white')
#         self.figure.set_edgecolor('white')
#         self.canvas.SetBackgroundColour('white')
          
        self.getNewLabelSizes()
        
        matplotlib.rc('xtick', labelsize=self.labelFontSize)
        matplotlib.rc('ytick', labelsize=self.labelFontSize)      
        xsize = len(zvals)
        extent=[0.5,xsize+0.5,0.5,xsize+0.5]
        self.plotMS = self.figure.add_axes(self._axes)
        cax = self.plotMS.imshow(zvals, cmap=cmap, interpolation=interpolation,
                            aspect='equal', 
#                             aspect='auto', 
                            extent=extent, 
                            origin='lower')
        
        # Setup labels 
        if xylabels:
            self.plotMS.set_xticks(np.arange(1,xsize+1,1))
            self.plotMS.set_xticklabels(xylabels, rotation=self.config.rmsdRotX)
            self.plotMS.set_yticks(np.arange(1,xsize+1,1))
            self.plotMS.set_yticklabels(xylabels, rotation=self.config.rmsdRotY)
        extent=[0.5,0.5,xsize+0.5,xsize+0.5]
        
        if colorbar:
            # pad controls how close colorbar is to the axes       
            self.figure.colorbar(cax, ax=None, use_gridspec=True, pad=0.01) 
        else: pass
        
        self.setup_zoom([self.plotMS], self.zoomtype, data_lims=extent,
                        plotName=plotName)
    
    def plotMZDT(self, zvals=None, title="", cmap='inferno', interpolation='None',
                      labelsX=None, labelsY=None, xlabel="", ylabel="", zoom="box", 
                      colorbar=False, fontsize=12, cmapNorm=None, axesSize=None, 
                      plotName=None, **kwargs):      
        """
        labelX, labelY = list of values used for extent of the figure
        """

        self.plotflag = True # Used only if saving data
        self.zoomtype = zoom
        if axesSize == None: self._axes = [0.1, 0.1, 0.85, 0.85]
        else: self._axes = axesSize
        self.xlabel = xlabel
        self.ylabel = ylabel
        
        self.getNewLabelSizes()
        
        matplotlib.rc('xtick', labelsize=self.labelFontSize)
        matplotlib.rc('ytick', labelsize=self.labelFontSize)
        
        if colorbar:
            self._axes = [0.1, 0.1, 0.8, 0.85]
        # Plot 
        self.plotMS = self.figure.add_axes(self._axes)
        extent = self.extents(labelsX)+self.extents(labelsY)
        
        self.cax = self.plotMS.imshow(zvals, 
                                      cmap=cmap, 
                                      interpolation=interpolation,
                                      extent=extent,
                                      aspect='auto', 
                                      origin='lower',
                                      norm=cmapNorm)
        
        cbarDivider = make_axes_locatable(self.plotMS)
           
#         extent= [labelsX[0], labelsY[0], labelsX[-1],labelsY[-1]] 
        extent= [extent[0], extent[2], extent[1], extent[3]] 
        self.setup_zoom([self.plotMS], self.zoomtype, data_lims=extent,
                        plotName=plotName)
        
        if colorbar:
            # https://stackoverflow.com/questions/18195758/set-matplotlib-colorbar-size-to-match-graph
            # pad controls how close colorbar is to the axes
            cbarWidth = "".join([str(self.config.colorbarWidth), "%"])
            cax = cbarDivider.append_axes("right", size=cbarWidth, pad=self.config.colorbarPad)
            self.figure.colorbar(self.cax, cax=cax)
        else: pass
        
        self.plotMS.set_xlabel(self.xlabel, fontsize=self.labelFontSize, 
                               weight=self.labelFontWeight)
        self.plotMS.set_ylabel(self.ylabel, fontsize=self.labelFontSize, 
                               weight=self.labelFontWeight)
        
        self.plotMS.tick_params(labelsize=self.tickFontSize)

