from plottingWindow import plottingWindow
from numpy import arange, sin, pi, meshgrid, sqrt, shape, ravel, zeros_like, divide
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from mpl_toolkits.mplot3d import Axes3D
import matplotlib

#needed to avoid annoying warnings to be printed on console
import warnings
warnings.filterwarnings("ignore",category=DeprecationWarning)
warnings.filterwarnings("ignore",category=RuntimeWarning)

# # Mayavi 
# from traits.api import HasTraits, Instance
# from traitsui.api import View, Item
# from mayavi.core.ui.api import SceneEditor, MlabSceneModel


class plot3D(plottingWindow):
    
    def __init__(self, *args, **kwargs):
        plottingWindow.__init__(self, *args, **kwargs)
        self.plotflag = False # Used only if saving data
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
        
    def plotNew3Dplot(self, xvals=None, yvals=None, zvals=None, cmap='inferno', 
                      title="", xlabel="", ylabel="", zlabel="", label="", **kwargs):
        
        self.plotflag = True # Used only if saving data
        
        self.getNewLabelSizes()
        matplotlib.rc('xtick', labelsize=self.labelFontSize)
        matplotlib.rc('ytick', labelsize=self.labelFontSize)

        # Prepare data
        self.xvals = xvals  
        self.yvals = yvals 
        self.xvals, self.yvals = meshgrid(self.xvals,self.yvals)
        
        ydivider, expo = self.testXYmaxValsUpdated(values=zvals)
        if expo > 1:
            offset_text = r'x$\mathregular{10^{%d}}$' %expo
            zlabel = ''.join([zlabel, " [", offset_text,"]"])
            zvals = divide(zvals, float(ydivider))
        
        self.plotMS = self.figure.add_subplot(111, projection='3d', aspect='auto')
        self.plotMS.plot_surface(self.xvals, self.yvals, zvals, cmap=cmap,
                                 antialiased=False, linewidth=0)
#                                  rcount=200, ccount=200) # determines the resolution of the image
        
        self.plotMS.w_xaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        self.plotMS.w_yaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        self.plotMS.w_zaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        
        self.plotMS.set_xlabel(xlabel, labelpad=20, fontsize=self.labelFontSize, 
                               weight=self.labelFontWeight)
        self.plotMS.set_ylabel(ylabel, labelpad=20, fontsize=self.labelFontSize, 
                               weight=self.labelFontWeight)
        self.plotMS.set_zlabel(zlabel, labelpad=20, fontsize=self.labelFontSize, 
                               weight=self.labelFontWeight)
        
        self.plotMS.set_xlim([xvals[0],xvals[-1]])
        self.plotMS.set_ylim([yvals[0],yvals[-1]])
        
#         self.plotMS.set_xlim([0,imsDataSize[1]])
#         self.plotMS.set_ylim([0,imsDataSize[0]])
        self.plotMS.grid(False)
    
    def plotNew3DBarplot(self, xvals=None, yvals=None, zvals=None, cmap='inferno', 
                         title="", xlabel="", ylabel="", zlabel="", label="", **kwargs):
        # TODO add colormapper 
        imsDataSize = shape(zvals)
        self.xvals = range(imsDataSize[1])
        self.yvals = range(imsDataSize[0])
        self.zvals = zvals
        self.xvals,self.yvals = meshgrid(self.xvals,self.yvals)
        
        x, y = self.xvals.ravel(), self.yvals.ravel()
        top = self.zvals.ravel() #x+y
        bottom = zeros_like(top)
        width = depth = 1
        
        self.plotMS = self.figure.add_subplot(111, projection='3d', aspect='auto')
        self.plotMS.bar3d(x, y, bottom, width, depth, top) #, shade=True)
#         self.plotMS.bar3d(self.xvals, self.yvals, self.zvals, cmap=cmap,
#                                  antialiased=False, linewidth=0)
        self.plotMS.w_xaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        self.plotMS.w_yaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        self.plotMS.w_zaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        self.plotMS.set_xlim([0,imsDataSize[1]])
        self.plotMS.set_ylim([0,imsDataSize[0]])
        self.plotMS.grid(False)
        
  
# class MayaviPanel(HasTraits):
#     scene = Instance(MlabSceneModel, ())
#  
#     view = View(Item('scene', editor=SceneEditor(), 
#                      resizable=True, show_label=False), 
#                 resizable=True)
# 
#     def __init__(self):
#         HasTraits.__init__(self)
#         self.scene.background=(1,1,1) #set white background!
#         self.scene.mlab.test_points3d()
# 
#     def display(self,data,t,color=(0.4,1,0.2)):
#         
#         self.scene.mlab.clf()
#         self.plot=self.scene.mlab.contour3d(data, color=color,contours=[t])
# 
# 
#     def update(self,data,t):
#         self.display(data, t)
#         #print "updating with %s"%t
#         #self.plot.mlab_source.set(scalars=data,contours=[t])
#         
#     def surface(self, xvals, yvals, zvals, cmap):
#         self.scene.mlab.clf()
#         self.plot = self.scene.mlab.surf(zvals, warp_scale="auto")