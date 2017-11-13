from plottingWindow import plottingWindow
from numpy import arange, sin, pi, min, max, arange, linspace
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib import gridspec
import matplotlib as mpl
import matplotlib.pyplot as plt
from toolbox import *
from mpl_toolkits.axes_grid1 import make_axes_locatable
import dialogs as dialogs
from analysisFcns import normalizeIMS




class plot1D(plottingWindow):
    # FIXME add possibility to read font size from config
    def __init__(self,  *args, **kwargs ):
        plottingWindow.__init__(self, *args, **kwargs)
        self.plotflag = False
        
        self.getNewLabelSizes()
        
        
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
        
    def plotSeaborn(self):
        pass

        self.view.panelPlots.plotRT.clearPlot()
        self.view.panelPlots.plotRT.plotSeaborn()
        # Show the mass spectrum
        self.view.panelPlots.plotRT.repaint()
#         gs = gridspec.GridSpec(1, 1)
#         
#         self._axes = [0.1, 0.1, 0.8, 0.8]
# 
#         
#         # Plot 
#         self.plotMS = self.figure.add_axes(self._axes)
#         import seaborn as sns
#         from scipy.stats import kendalltau
#         sns.set(style="darkgrid")
#          
# #         # Load the long-form example gammas dataset
# #         gammas = sns.load_dataset("gammas")
# #          
# #         # Plot the response with standard error
# #         sns.tsplot(data=gammas, time="timepoint", unit="subject",
# #                                 condition="ROI", value="BOLD signal",
# #                                 ax=self.plotMS)
#         
#         
#         self.setup_zoom([self.plotMS], 'box', plotName='1D')  
        
    def plotNewScatterPlot(self, xvals=None, yvals=None, color='red',
                               marker='o', title='',xlabel="", 
                               ylabel="", fontsize=16, xlimits=None,
                               axesSize=None, zoom="box",**kwargs):
        # Setup parameters
        self.plotflag = True # Used only if saving data
        self.zoomtype = zoom
        if axesSize == None: self._axes = [0.1, 0.1, 0.85, 0.85]
        else: self._axes = axesSize
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.figure.set_facecolor('white')
        self.figure.set_edgecolor('white')
        self.canvas.SetBackgroundColour('white')
        self.getNewLabelSizes()
        
        mpl.rc('xtick', labelsize=self.labelFontSize)
        mpl.rc('ytick', labelsize=self.labelFontSize)
        
        # Plot 
        self.plotCalibration = self.figure.add_axes(self._axes)
#         self.plotCalibration.title(str(title))
        self.plotCalibration.scatter(xvals, yvals, edgecolors='black',
                                     color=color)
        self.plotCalibration.plot(xvals, yvals, color=color)
        
        
        # Setup parameters
        if xlimits == None or xlimits[0] == None or xlimits[1] == None:
            xlimits = [min(xvals)-0.5, max(xvals)+0.5]
        
        self.plotCalibration.set_xlim([xlimits[0], xlimits[1]])
        self.plotCalibration.set_ylim([min(yvals)-0.5, max(yvals)+0.5])

        extent= [xlimits[0], min(yvals)-0.5, xlimits[-1],max(yvals)+0.5] 

#         self.figure.set_tight_layout(True) # not found in axes
        self.plotCalibration.set_xlabel(self.xlabel, fontsize=self.labelFontSize, 
                                        weight=self.labelFontWeight)
        self.plotCalibration.set_ylabel(self.ylabel, fontsize=self.labelFontSize, 
                                        weight=self.labelFontWeight)
        # Setup font size info
        self.plotCalibration.tick_params(labelsize=self.tickFontSize)
        

        # FIX ZOOM
        self.setup_zoom([self.plotCalibration], self.zoomtype, 
                        data_lims=extent)     
           
        # Setup X-axis getter
        self.setupGetXAxies([self.plotCalibration])
        
    def plotNewOverlay1D(self, xvals=None, yvals=None, colors='black', 
                         xlabel=None, ylabel=None, xlimits=None, 
                         axesSize=None, testMax = None, lineWidth=1,
                         labels=None, zoom=None, plotName=None, **kwargs):
        """
        Overlay plot for RT, 1D datasets
        """
        
        self.plotflag = True # Used only if saving data
        self.zoomtype = zoom
        if axesSize == None: self._axes = [0.1, 0.1, 0.8, 0.8]
        else: self._axes = axesSize
        
        # Plot 
        self.plotMS = self.figure.add_axes(self._axes)

        for xval, yval, color, label in zip(xvals, yvals, colors, labels):
            self.plotMS.plot(xval, yval, color=color, 
                             label=label, linewidth=lineWidth)
        
        self.plotMS.legend()
        # Setup parameters
        if xlimits == None or xlimits[0] == None or xlimits[1] == None:
            xlimits = [min(xvals), max(xvals)]
            
        # Set limits
        self.plotMS.set_xlim([xlimits[0], xlimits[1]])
        self.plotMS.set_ylim([min(yvals), max(yvals)+0.001])
#         Extent for zoom
        extent= [xlimits[0], min(yval), xlimits[-1],max(yval)+0.001] 

        self.plotMS.set_xlabel(xlabel, fontsize=self.labelFontSize, 
                               weight=self.labelFontWeight)
        self.plotMS.set_ylabel(ylabel, fontsize=self.labelFontSize, 
                               weight=self.labelFontWeight)
                
        # Setup font size info
        self.plotMS.tick_params(labelsize=self.tickFontSize)
        
        self.setup_zoom([self.plotMS], self.zoomtype, data_lims=extent,
                        plotName=plotName)        
        # Setup X-axis getter
        self.setupGetXAxies([self.plotMS])
                
    def plotData1D(self, xvals=None, yvals=None, title="", xlabel="",
                      ylabel="", label="", xlimits=None, color="black",
                      axesSize=None, zoom="box", testMax = None, lineWidth=1,
                      plotName=None, **kwargs):
        
        """
        Plot 1D data
        """
        self.plotflag = True # Used only if saving data
        self.zoomtype = zoom
        if axesSize == None: self._axes = [0.1, 0.1, 0.8, 0.8]
        else: self._axes = axesSize
        
        self.getNewLabelSizes()

        mpl.rc('xtick', labelsize=self.labelFontSize)
        mpl.rc('ytick', labelsize=self.labelFontSize)
        
        # Plot 
        self.plotMS = self.figure.add_axes(self._axes)
        
        if testMax == 'yvals':
            ydivider, expo = self.testXYmaxValsUpdated(values=yvals)
            if expo > 1:
                offset_text = r'x$\mathregular{10^{%d}}$' %expo
                ylabel = ''.join([ylabel, " [", offset_text,"]"])
                yvals = np.divide(yvals, float(ydivider))

        self.plotMS.plot(xvals, yvals, color=color, label=label, 
                         linewidth=lineWidth)

        # Setup parameters
        if xlimits == None or xlimits[0] == None or xlimits[1] == None:
            xlimits = [min(xvals), max(xvals)]
            
        # Set limits
        self.plotMS.set_xlim([xlimits[0], xlimits[1]])
        self.plotMS.set_ylim([min(yvals), max(yvals)+0.001])
#         Extent for zoom
        extent= [xlimits[0], min(yvals), xlimits[-1],max(yvals)+0.001] 

        self.plotMS.set_xlabel(xlabel, fontsize=self.labelFontSize, 
                               weight=self.labelFontWeight)
        self.plotMS.set_ylabel(ylabel, fontsize=self.labelFontSize, 
                               weight=self.labelFontWeight)
                
        # Setup font size info
        self.plotMS.tick_params(labelsize=self.tickFontSize)
        
        self.setup_zoom([self.plotMS], self.zoomtype, data_lims=extent,
                        plotName=plotName)        
        # Setup X-axis getter
        self.setupGetXAxies([self.plotMS])
          
    def plotScatter_2plot(self, xvals1, yvals1, label1,xvalsLinear, yvalsLinear,
                          xvals2, yvals2, label2, xvalsPower, yvalsPower, 
                          color, marker, markerSize=5, axesSize=None, zoom="box",):
        
        gs = gridspec.GridSpec(1, 2, width_ratios=[1,1])
        gs.update(wspace=0.2)
        self.zoomtype = zoom
        self.getNewLabelSizes()
        
        mpl.rc('xtick', labelsize=self.labelFontSize)
        mpl.rc('ytick', labelsize=self.labelFontSize)
        
        self.plotLinear = self.figure.add_subplot(gs[0], aspect='auto')
        self.plotLinear.scatter(xvals1, yvals1, c=color, label=label1)
        self.plotLinear.plot(xvalsLinear, yvalsLinear, '--', c='blue')
        # Setup font size info
        self.plotLinear.tick_params(labelsize=self.tickFontSize)
        
        self.plotPower = self.figure.add_subplot(gs[1], aspect='auto') 
        self.plotPower.scatter(xvals2, yvals2, c=color, label=label2)
        self.plotPower.plot(xvalsPower, yvalsPower, '--', c='blue')
        
        self.plotPower.tick_params(labelsize=self.tickFontSize)
        self.plotPower.yaxis.tick_right()

        
        gs.tight_layout(self.figure)
        
    def plotNew1D_2plot(self, yvalsRMSF=None, zvals=None, labelsX=None, labelsY=None, 
                        color='black', cmap='inferno', interpolation="None", ylabelRMSF="",
                         xlabelRMSD="",ylabelRMSD="", testMax = 'yvals', label="", 
                         zoom="box", colorbar=False,plotName=False):
        """
        Plots RMSF and RMSD together
        """
        # Setup parameters
        gs = gridspec.GridSpec(2, 1, height_ratios=[1,3])
        gs.update(hspace=0.1)
        self.zoomtype = zoom
        
        self.getNewLabelSizes()
        
        mpl.rc('xtick', labelsize=self.labelFontSize)
        mpl.rc('ytick', labelsize=self.labelFontSize)
        
        # Check if there are any labels attached with the data 
        if xlabelRMSD=="": xlabelRMSD = "Scans"
        if ylabelRMSD=="": ylabelRMSD = "Drift time (bins)"
        if ylabelRMSF=="": ylabelRMSF = "RMSD (%)"
            
        if testMax == 'yvals':
            ydivider, expo = self.testXYmaxValsUpdated(values=yvalsRMSF)
            if expo > 1:
                offset_text = r'x$\mathregular{10^{%d}}$' %expo
                ylabelRMSF = ''.join([ylabelRMSF, " [", offset_text,"]"])
                yvalsRMSF = np.divide(yvalsRMSF, float(ydivider))
        else:
            ylabelRMSF = "RMSD (%)"
                
        
        # Plot RMSF data (top plot)        
        if len(labelsX) != len(yvalsRMSF):
                dialogs.dlgBox(exceptionTitle='Missing data', 
                               exceptionMsg= 'Missing x-axis labels! Cannot execute this action!',
                               type="Error")
                return
            
        self.plotRMSF = self.figure.add_subplot(gs[0], aspect='auto')         
        self.plotRMSF.fill_between(labelsX, yvalsRMSF,0, color=color, alpha=0.4) 
        
        self.plotRMSF.set_xlim([min(labelsX), max(labelsX)])
        self.plotRMSF.set_ylim([min(yvalsRMSF), max(yvalsRMSF)+0.2])
        self.plotRMSF.get_xaxis().set_visible(False)
        self.plotRMSF.set_ylabel(ylabelRMSF, fontsize=self.labelFontSize, 
                                 weight=self.labelFontWeight)
        self.plotRMSF.tick_params(labelsize=self.tickFontSize)
        
        extent = self.extents(labelsX)+self.extents(labelsY)
        self.plotMS = self.figure.add_subplot(gs[1], aspect='auto')
        plotMS = self.plotMS.imshow(zvals, cmap=cmap,
                                   interpolation=interpolation, extent= extent, 
                                   aspect='auto', origin='lower')
        extent= [labelsX[0], labelsY[0], labelsX[-1],labelsY[-1]] 
        self.setup_zoom([self.plotMS], self.zoomtype, data_lims=extent,
                        plotName=plotName)
         
        
        self.plotMS.set_xlabel(xlabelRMSD, fontsize=self.labelFontSize, 
                                 weight=self.labelFontWeight)
        self.plotMS.set_ylabel(ylabelRMSD, fontsize=self.labelFontSize, 
                                 weight=self.labelFontWeight)
        self.plotMS.tick_params(labelsize=self.tickFontSize)
        
        cbarDivider = make_axes_locatable(self.plotMS)
        
        if colorbar:
            # pad controls how close colorbar is to the axes
            gs.update(hspace=0.1)
            cax = cbarDivider.append_axes("right", size="3%", pad=0.03)
            self.figure.colorbar(plotMS, cax=cax)
        else: pass
        
        gs.tight_layout(self.figure)
       
    def plotNewWaterfallPlot(self, xvals=None, yvals=None, yOffset=0, yIncrement=0.05,
                              color='black', cmap='inferno', label="", xlabel="", 
                              zoom="box", axesSize=None, **kwargs):

        self.zoomtype = zoom
        if axesSize == None: self._axes = [0.1, 0.1, 0.85, 0.85]
        else: self._axes = axesSize
        
        self.getNewLabelSizes()

        mpl.rc('xtick', labelsize=self.labelFontSize)
        mpl.rc('ytick', labelsize=0)

        self.plotMS = self.figure.add_axes(self._axes)
        
        # Always normalizes data - otherwise it looks pretty bad
        yvals = normalizeIMS(inputData=yvals)

        color_idx= linspace(0,1,len(yvals[1,:]))
        voltage_idx = linspace(0, len(yvals[1,:])-1,len(yvals[1,:])-1)
        waterfallCmap = plt.cm.get_cmap(name=cmap)
        
        # Iterate over the colormap to get the color shading we desire 
        for i, idx in zip(voltage_idx, color_idx):
            y = yvals[:,int(i)] 
            self.plotMS.plot(xvals, (y+yOffset), color=waterfallCmap(idx), label=label)
            yOffset=yOffset+yIncrement
            
        self.plotMS.set_xlabel(xlabel, fontsize=self.labelFontSize, 
                               weight=self.labelFontWeight)
        self.plotMS.get_yaxis().set_visible(False)
        self.plotMS.tick_params(labelsize=self.tickFontSize)
        
        self.setup_zoom([self.plotMS], self.zoomtype)
        # Setup X-axis getter
        self.setupGetXAxies([self.plotMS])
        

          
    def addPlot(self, xvals=None, yvals=None, color='blue', label=""):
        """
        Add plot to already existing plot (i.e. RT or DT)
        """
        self.plotMS.plot(xvals, yvals, color=color, label=label)
        self.setup_zoom([self.plotMS], self.zoomtype)
        
    def extents(self,f):
        delta = f[1] - f[0]
        return [f[0] - delta/2, f[-1] + delta/2]
        
        
        
        
        
        
        
        
        
        
        