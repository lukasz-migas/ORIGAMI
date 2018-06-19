# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
#    Copyright (C) 2017 Lukasz G. Migas <lukasz.migas@manchester.ac.uk>
# 
#     GitHub : https://github.com/lukasz-migas/ORIGAMI
#     University of Manchester IP : https://www.click2go.umip.com/i/s_w/ORIGAMI.html
#     Cite : 10.1016/j.ijms.2017.08.014
#
#    This program is free software. Feel free to redistribute it and/or 
#    modify it under the condition you cite and credit the authors whenever 
#    appropriate. 
#    The program is distributed in the hope that it will be useful but is 
#    provided WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE
# -------------------------------------------------------------------------

from __future__ import division
import matplotlib
import matplotlib as mpl
import matplotlib.cm as cm
import matplotlib.colors as colors
import matplotlib.patches as patches
import matplotlib.pyplot as plt
from matplotlib import gridspec
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.colors import LogNorm
from matplotlib.patches import Rectangle
from mpl_toolkits.axes_grid1 import make_axes_locatable
from mpl_toolkits.mplot3d import Axes3D
from numpy import (arange, sin, pi, meshgrid, sqrt, shape, ravel, zeros_like, 
                   divide, min, max, arange, linspace, amax)
from plottingWindow import plottingWindow
from toolbox import find_limits, dir_extra, determineFontColor, convertRGB1to255, find_limits_list, MidpointNormalize, merge_two_dicts
import dialogs as dialogs
from analysisFcns import normalizeIMS, normalizeMS
import numpy as np
import itertools
import copy
from matplotlib.ticker import MaxNLocator

#needed to avoid annoying warnings to be printed on console
import warnings
warnings.filterwarnings("ignore",category=DeprecationWarning)
warnings.filterwarnings("ignore",category=RuntimeWarning)

class plots(plottingWindow):
    def __init__(self, *args, **kwargs):
        plottingWindow.__init__(self, *args, **kwargs)
        self.plotflag = False
        self.text = []
        self.lines = []
        
        self.lock_plot_from_updating = False
        self.plot_parameters = []
        self.plot_limits = []
        self._axes = [0.1, 0.1, 0.8, 0.8]
        self.plot_name = ""
        self.plot_data = {}
        
    #-----
    
    def _plot_settings_(self, **kwargs):
        """
        Setup all plot parameters for easy retrieval
        """
        self.plot_kwargs = kwargs
            
    def extents(self, f):
        delta = f[1] - f[0]
        return [f[0] - delta/2, f[-1] + delta/2]
    #-----
    
    ### PURE UPDATING FUNCTIONS ###
    
    def plot_add_text_and_lines(self, xpos, yval, label, vline=True, color="black", **kwargs):
        ymin, ymax = self.plotMS.get_ylim()
        text = self.plotMS.text(np.array(xpos), ymax+.05, label, 
                                horizontalalignment="center",
                                verticalalignment="top", color=color)
        self.text.append(text)
        if vline:
            line = self.plotMS.vlines(xpos, ymin, yval*0.8, color=color, linestyles="dashed", 
                                      alpha=0.4)
            self.lines.append(line)
        
    def plot_remove_text_and_lines(self):
        if len(self.text) > 0:
            for i, __ in enumerate(self.text):
                try: self.text[i].remove()
                except: pass
                
        if len(self.lines) > 0:
            for i, __ in enumerate(self.lines):
                try: self.lines[i].remove()
                except: pass
        self.text = []
        self.lines = []
        
        self.repaint()
            
    def plot_1D_update_data(self, xvals, yvals, xlabel, ylabel, testMax='yvals', 
                            **kwargs):
        if self.plot_name in ['compare', 'Compare']:
            raise Exception("Wrong plot name - resetting")
        
        # override parameters
        if not self.lock_plot_from_updating:
            self.plot_parameters = kwargs
        else:
            kwargs = merge_two_dicts(kwargs, self.plot_parameters)
            self.plot_parameters = kwargs
        
        lines = self.plotMS.get_lines()
        for line in lines:
            if testMax == 'yvals':
                ydivider, expo = self.testXYmaxValsUpdated(values=yvals)
                if expo > 1:
                    offset_text = r'x$\mathregular{10^{%d}}$' % expo
                    ylabel = ''.join([ylabel, " [", offset_text,"]"])
                    yvals = divide(yvals, float(ydivider)) 

            line.set_xdata(xvals)
            line.set_ydata(yvals)
            line.set_linewidth(kwargs['line_width'])
            line.set_color(kwargs['line_color'])
            line.set_linestyle(kwargs['line_style'])
             
            # update limits and extents
            xlimits = (np.min(xvals), np.max(xvals))
            ylimits = (np.min(yvals), np.max(yvals))
 
            extent= [xlimits[0], ylimits[0], xlimits[1], ylimits[1]]

        if kwargs['shade_under']:
            for shade in range(len(self.plotMS.collections)):
                self.plotMS.collections[shade].remove()
            shade_kws = dict(
                facecolor=kwargs['shade_under_color'],
                alpha=kwargs.get("shade_under_transparency", 0.25),
                clip_on=kwargs.get("clip_on", True),
                zorder=kwargs.get("zorder", 1),
                )
            self.plotMS.fill_between(xvals, 0, yvals, **shade_kws)
        elif len(self.plotMS.collections) > 0:
            for shade in range(len(self.plotMS.collections)):
                self.plotMS.collections[shade].remove()
            
        # convert weights
        if kwargs['label_weight']: kwargs['label_weight'] = "heavy"
        else: kwargs['label_weight'] = "normal"
            
        self.plotMS.set_xlim(xlimits)
        self.plotMS.set_ylim(ylimits)
        self.plotMS.set_xlabel(xlabel, 
                               labelpad=kwargs['label_pad'], 
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'])
        self.plotMS.set_ylabel(ylabel, 
                               labelpad=kwargs['label_pad'], 
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'])
        self.update_extents(extent)
        
    def plot_1D_waterfall_update(self, which="other", **kwargs):
        
        if self.lock_plot_from_updating: 
            msg = "This plot is locked and you cannot use global setting updated. \n" + \
                  "Please right-click in the plot area and select Customise plot..." + \
                  " to adjust plot settings."
            print(msg)
            return
        
        if which == "other":
            for i, line in enumerate(self.plotMS.get_lines()):
                line.set_linestyle(kwargs['line_style'])
                line.set_linewidth(kwargs['line_width'])
            print(dir_extra(dir(line)),
                  line.get_ydata())
        elif which == 'color':
            if not kwargs['use_colormap']:
                for i, line in enumerate(self.plotMS.get_lines()):
                    line.set_color(kwargs['line_color'])
            else:
                waterfallCmap = plt.cm.get_cmap(name=kwargs['colormap'], lut=len(self.plotMS.get_lines())-2)
                for i, line in enumerate(self.plotMS.get_lines()):
                    line.set_color(waterfallCmap(i))
        elif which == 'data':
            # TODO: fix an issue when there is shade under the curve
            count = 0
            increment = kwargs['increment'] - self.plot_parameters['increment']
            offset = kwargs['offset'] - self.plot_parameters['offset']
            ydata = []
            for i, line in enumerate(self.plotMS.get_lines()):
                yvals = line.get_ydata()
                if len(yvals) > 5: count =+ 1
            yOffset = offset*(count+1)
            for i, line in enumerate(self.plotMS.get_lines()):
                yvals = line.get_ydata()
                if len(yvals) > 5:
                    new_yvals = yvals + yOffset
                    line.set_ydata(new_yvals)
                    yOffset=yOffset-increment
                    ydata.extend(new_yvals)
                
            self.plot_limits[2] = np.min(ydata)
            self.plot_limits[3] = np.max(ydata)+0.05
            extent = [self.plot_limits[0], self.plot_limits[2], 
                      self.plot_limits[1], self.plot_limits[3]]
            self.update_extents(extent)
            self.plotMS.set_xlim((self.plot_limits[0], self.plot_limits[1]))
            self.plotMS.set_ylim((self.plot_limits[2], self.plot_limits[3]))
            
        self.plot_parameters = kwargs
        
    def plot_1D_update(self, **kwargs):
        if self.lock_plot_from_updating: 
            msg = "This plot is locked and you cannot use global setting updated. \n" + \
                  "Please right-click in the plot area and select Customise plot..." + \
                  " to adjust plot settings."
            print(msg)
            return
        
        # update ticks
        matplotlib.rc('xtick', labelsize=kwargs['tick_size'])
        matplotlib.rc('ytick', labelsize=kwargs['tick_size'])  
               
        # convert weights
        if kwargs['label_weight']: kwargs['label_weight'] = "heavy"
        else: kwargs['label_weight'] = "normal"
               
        # update labels
        self.plotMS.set_xlabel(self.plotMS.get_xlabel(), 
                               labelpad=kwargs['label_pad'], 
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'])
        self.plotMS.set_ylabel(self.plotMS.get_ylabel(),
                               labelpad=kwargs['label_pad'], 
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'])
        
        # Setup font size info
        self.plotMS.tick_params(labelsize=kwargs['tick_size'])
        
        # update axis frame
        if kwargs['axis_onoff']: 
            self.plotMS.set_axis_on()
        else: 
            self.plotMS.set_axis_off()
                
        
        self.plotMS.tick_params(axis='both',  
                                left=kwargs['ticks_left'], 
                                right=kwargs['ticks_right'], 
                                top=kwargs['ticks_top'],
                                bottom=kwargs['ticks_bottom'],
                                labelleft=kwargs['tickLabels_left'],
                                labelright=kwargs['tickLabels_right'],
                                labeltop=kwargs['tickLabels_top'],
                                labelbottom=kwargs['tickLabels_bottom'])
                
        for i, line in enumerate(self.plotMS.get_lines()):
            line.set_linewidth(kwargs['line_width'])
        
        self.plotMS.spines['left'].set_visible(kwargs['spines_left'])
        self.plotMS.spines['right'].set_visible(kwargs['spines_right'])
        self.plotMS.spines['top'].set_visible(kwargs['spines_top'])
        self.plotMS.spines['bottom'].set_visible(kwargs['spines_bottom'])
        [i.set_linewidth(kwargs['frame_width']) for i in self.plotMS.spines.itervalues()]
        
    #-----
        
    def plot_1D_update_rmsf(self, **kwargs):
        if self.lock_plot_from_updating: 
            msg = "This plot is locked and you cannot use global setting updated. \n" + \
                  "Please right-click in the plot area and select Customise plot..." + \
                  " to adjust plot settings."
            print(msg)
            return
        
        # update ticks
        matplotlib.rc('xtick', labelsize=kwargs['tick_size'])
        matplotlib.rc('ytick', labelsize=kwargs['tick_size'])  
               
        # convert weights
        if kwargs['label_weight']: kwargs['label_weight'] = "heavy"
        else: kwargs['label_weight'] = "normal"
        
        # update labels
        self.plotRMSF.set_xlabel(self.plotMS.get_xlabel(), 
                               labelpad=kwargs['label_pad'], 
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'])
        self.plotRMSF.set_ylabel(self.plotMS.get_ylabel(),
                               labelpad=kwargs['label_pad'], 
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'])
        # Setup font size info
        self.plotRMSF.tick_params(labelsize=kwargs['tick_size'])
        
        # update axis frame
        if kwargs['axis_onoff']: 
            self.plotRMSF.set_axis_on()
        else: 
            self.plotRMSF.set_axis_off()
        
        self.plotRMSF.tick_params(axis='both',  
                                left=kwargs['ticks_left'], 
                                right=kwargs['ticks_right'], 
                                top=kwargs['ticks_top'],
                                bottom=kwargs['ticks_bottom'],
                                labelleft=kwargs['tickLabels_left'],
                                labelright=kwargs['tickLabels_right'],
                                labeltop=kwargs['tickLabels_top'],
                                labelbottom=kwargs['tickLabels_bottom'])

        for i, line in enumerate(self.plotRMSF.get_lines()):
            line.set_linewidth(kwargs['rmsd_line_width'])
            line.set_linestyle(kwargs['rmsd_line_style'])
            line.set_color(kwargs['rmsd_line_color'])
        
        self.plotRMSF.spines['left'].set_visible(kwargs['spines_left'])
        self.plotRMSF.spines['right'].set_visible(kwargs['spines_right'])
        self.plotRMSF.spines['top'].set_visible(kwargs['spines_top'])
        self.plotRMSF.spines['bottom'].set_visible(kwargs['spines_bottom'])
        [i.set_linewidth(kwargs['frame_width']) for i in self.plotMS.spines.itervalues()]
        
    #-----
        
    def plot_2D_update_label(self, **kwargs):
        
        if kwargs['rmsd_label_coordinates'] != [None, None]:
            self.text.set_position(kwargs['rmsd_label_coordinates'])
            self.text.set_visible(True)
        else:
            self.text.set_visible(False)

        # convert weights
        if kwargs['rmsd_label_font_weight']:
            kwargs['rmsd_label_font_weight'] = "heavy"
        else:
            kwargs['rmsd_label_font_weight'] = "normal"
        
        self.text.set_fontweight(kwargs['rmsd_label_font_weight'])
        self.text.set_fontsize(kwargs['rmsd_label_font_size'])
        self.text.set_color(kwargs['rmsd_label_color'])
        
    def plot_2D_update(self, **kwargs):
        
        if self.lock_plot_from_updating: 
            msg = "This plot is locked and you cannot use global setting updated. \n" + \
                  "Please right-click in the plot area and select Customise plot..." + \
                  " to adjust plot settings."
            print(msg)
            return    
    
        # update ticks
        matplotlib.rc('xtick', labelsize=kwargs['tick_size'])
        matplotlib.rc('ytick', labelsize=kwargs['tick_size'])  
        
        try:
            cbar_yticks = self.cbar.get_yticklabels()
            cbar_xticks = self.cbar.get_xticklabels()
        except: pass
        
        if 'colormap_norm' in kwargs:
            self.cax.set_norm(kwargs['colormap_norm'])
            
        self.cax.set_cmap(kwargs['colormap'])
        
        try: self.cax.set_interpolation(kwargs['interpolation'])
        except AttributeError: pass
        
        
        # convert weights
        if kwargs['label_weight']:
            kwargs['label_weight'] = "heavy"
        else:
            kwargs['label_weight'] = "normal"
               
        # update labels
        self.plotMS.set_xlabel(self.plotMS.get_xlabel(), 
                               labelpad=kwargs['label_pad'], 
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'])
        self.plotMS.set_ylabel(self.plotMS.get_ylabel(),
                               labelpad=kwargs['label_pad'], 
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'])

        # Setup font size info
        self.plotMS.tick_params(labelsize=kwargs['tick_size'])
        
        # update axis frame
        if kwargs['axis_onoff']: 
            self.plotMS.set_axis_on()
        else: 
            self.plotMS.set_axis_off()
        
        try:
            self.cbar.set_visible(kwargs['colorbar'])
            if len(cbar_yticks) > len(cbar_xticks):
                self.cbar.set_yticklabels(["0", "%", "100"])
            else:
                self.cbar.set_xticklabels(["0", "%", "100"])
        except:
            pass


        self.plotMS.tick_params(axis='both',  
                                left=kwargs['ticks_left'], 
                                right=kwargs['ticks_right'], 
                                top=kwargs['ticks_top'],
                                bottom=kwargs['ticks_bottom'],
                                labelleft=kwargs['tickLabels_left'],
                                labelright=kwargs['tickLabels_right'],
                                labeltop=kwargs['tickLabels_top'],
                                labelbottom=kwargs['tickLabels_bottom'])
        
        self.plotMS.spines['left'].set_visible(kwargs['spines_left'])
        self.plotMS.spines['right'].set_visible(kwargs['spines_right'])
        self.plotMS.spines['top'].set_visible(kwargs['spines_top'])
        self.plotMS.spines['bottom'].set_visible(kwargs['spines_bottom'])
        [i.set_linewidth(kwargs['frame_width']) for i in self.plotMS.spines.itervalues()]
        
        self.plot_parameters = kwargs
    #-----
    
    def plot_update_axes(self, axes_sizes):
        self.plotMS.set_position(axes_sizes)
        
    def plot_2D_matrix_update_label(self, **kwargs):
        
        
        self.plotMS.set_xticklabels(self.plotMS.get_xticklabels(), 
                                    rotation=kwargs['rmsd_matrix_rotX'])
        self.plotMS.set_yticklabels(self.plotMS.get_xticklabels(), 
                                    rotation=kwargs['rmsd_matrix_rotY'])
        
        for text in self.text:
            text.set_visible(kwargs['rmsd_matrix_labels'])
            
    def plot_3D_update(self, **kwargs):
        
        matplotlib.rc('xtick', labelsize=kwargs['tick_size'])
        matplotlib.rc('ytick', labelsize=kwargs['tick_size'])  
                                
        # update labels
        self.plotMS.set_xlabel(self.plotMS.get_xlabel(), 
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'])
        self.plotMS.set_ylabel(self.plotMS.get_ylabel(),
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'])
        
        # Setup font size info
        self.plotMS.tick_params(labelsize=kwargs['tick_size'])

        self.plotMS.w_xaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        self.plotMS.w_yaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        self.plotMS.w_zaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        
        # Get rid of spines
        if not kwargs['show_spines']:
            self.plotMS.w_xaxis.line.set_color((1.0, 1.0, 1.0, 0.0))
            self.plotMS.w_yaxis.line.set_color((1.0, 1.0, 1.0, 0.0))
            self.plotMS.w_zaxis.line.set_color((1.0, 1.0, 1.0, 0.0))
        else:
            self.plotMS.w_xaxis.line.set_color((0.0, 0.0, 0.0, 0.0))
            self.plotMS.w_yaxis.line.set_color((0.0, 0.0, 0.0, 0.0))
            self.plotMS.w_zaxis.line.set_color((0.0, 0.0, 0.0, 0.0))
        
        # Get rid of the ticks
        if not kwargs['show_ticks']:
            self.plotMS.set_xticks([]) 
            self.plotMS.set_yticks([]) 
            self.plotMS.set_zticks([])

            
        # convert weights
        if kwargs['label_weight']:
            kwargs['label_weight'] = "heavy"
        else:
            kwargs['label_weight'] = "normal"
        
        # update labels
        self.plotMS.set_xlabel(self.plotMS.get_xlabel(),
                               labelpad=kwargs['label_pad'], 
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'],
                               visible=kwargs['show_labels'])
        self.plotMS.set_ylabel(self.plotMS.get_ylabel(),  
                               labelpad=kwargs['label_pad'], 
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'],
                               visible=kwargs['show_labels'])
        self.plotMS.set_zlabel(self.plotMS.get_zlabel(),
                               labelpad=kwargs['label_pad'], 
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'],
                               visible=kwargs['show_labels'])
        
        self.plotMS.grid(kwargs['grid'])
    # ----
    
### PURE PLOTTING FUNCTIONS ###
    
    def plot_2D_colorbar_update(self, **kwargs):

        if self.lock_plot_from_updating: 
            msg = "This plot is locked and you cannot use global setting updated. \n" + \
                  "Please right-click in the plot area and select Customise plot..." + \
                  " to adjust plot settings."
            print(msg)
            return
        
        try:
            if kwargs['colorbar']:
                cbarDivider = make_axes_locatable(self.plotMS)
                
                if hasattr(self.cbar, "ticks"):
                    ticks = self.cbar.ticks
                elif hasattr(self, "ticks"):
                    ticks = self.ticks
                    
#                 if ticks_input is not None:
#                     ticks = ticks_input
#                 
                
                if hasattr(self.cbar, "tick_labels"):
                    tick_labels = self.cbar.tick_labels
                elif hasattr(self, "tick_labels"):
                    tick_labels = self.tick_labels
                
#                 print(self.cbar.ticks)
#                 cbar_xticks = self.cbar.get_xticks()
#                 cbar_yticks = self.cbar.get_yticks()
#                 
#                 if len(cbar_xticks) > len(cbar_yticks): ticks = cbar_xticks
#                 else: ticks = cbar_yticks
#                 
#                 cbar_xtickLabels = self.cbar.get_xticklabels()
#                 cbar_ytickLabels= self.cbar.get_yticklabels()
#                 
#                 if len(cbar_xtickLabels) > len(cbar_ytickLabels): tick_labels = cbar_xtickLabels
#                 else: tick_labels = cbar_ytickLabels
#                 
#                 labels = []
#                 for tick in tick_labels:
#                     labels.append(tick.get_text())
    
                try: self.cbar.remove()
                except: pass
                self.cbar = cbarDivider.append_axes(kwargs['colorbar_position'], 
                                                    size="".join([str(kwargs['colorbar_width']), "%"]), 
                                                    pad=kwargs['colorbar_pad'])
                
                self.cbar.ticks = ticks
                self.cbar.tick_labels = tick_labels
 
                if kwargs['colorbar_position'] in ['left', 'right']:
                    self.figure.colorbar(self.cax, cax=self.cbar, ticks=ticks, orientation='vertical')
                    self.cbar.yaxis.set_ticks_position(kwargs['colorbar_position'])
                    self.cbar.set_yticklabels(tick_labels)
                else:
                    self.figure.colorbar(self.cax, cax=self.cbar, ticks=ticks, orientation='horizontal')
                    self.cbar.xaxis.set_ticks_position(kwargs['colorbar_position'])
                    self.cbar.set_xticklabels(tick_labels)
                
                self.cbar.tick_params(labelsize=kwargs['colorbar_label_size'])
            else:
                if hasattr(self.cbar, "ticks"):
                    self.ticks = self.cbar.ticks
                if hasattr(self.cbar, "tick_labels"):
                    self.tick_labels = self.cbar.tick_labels
                
                self.cbar.remove()
        except: 
            pass
    
    def plot_2D_update_normalization(self, **kwargs):
    
        if self.lock_plot_from_updating: 
            msg = "This plot is locked and you cannot use global setting updated. \n" + \
                  "Please right-click in the plot area and select Customise plot..." + \
                  " to adjust plot settings."
            print(msg)
            return
        
        if hasattr(self, "plot_data"):
            if 'zvals' in self.plot_data:
                # normalize
                zvals_max = max(self.plot_data['zvals'])
                
                cmap_min = (zvals_max*kwargs['colormap_min'])/100.
                cmap_mid = (zvals_max*kwargs['colormap_mid'])/100.
                cmap_max = (zvals_max*kwargs['colormap_max'])/100.
                
                cmap_norm = MidpointNormalize(midpoint=cmap_mid,
                                              vmin=cmap_min,
                                              vmax=cmap_max)
                
                self.plot_parameters['colormap_norm'] = cmap_norm
                
                if 'colormap_norm' in self.plot_parameters:
                    self.cax.set_norm(self.plot_parameters['colormap_norm'])
                    self.plot_2D_colorbar_update(**kwargs)
    
    def plot_1D_add(self, xvals, yvals, color, label="", setup_zoom=True, allowWheel=False, **kwargs):
        self.plotMS.plot(np.array(xvals), yvals, color=color, 
                         label=label, **kwargs)

        lines = self.plotMS.get_lines()
        yvals_limits = []
        for line in lines:
            yvals_limits.extend(line.get_ydata())
            
        xlimits = [min(xvals), max(xvals)]
        ylimits = [min(yvals_limits), max(yvals_limits)]
        
        self.plotMS.set_xlim([xlimits[0], xlimits[1]])
        self.plotMS.set_ylim([ylimits[0], ylimits[1]+0.025])
        
        extent= [xlimits[0], ylimits[0], xlimits[-1], ylimits[-1]+0.025]
        if setup_zoom:
            self.setup_zoom([self.plotMS], self.zoomtype, data_lims=extent,
                            allowWheel=allowWheel)
            self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]

    def plot_1D_add_legend(self, legend_text, **kwargs):
        handles = []
        if legend_text != None:
            for i in range(len(legend_text)):
                handles.append(patches.Patch(color=legend_text[i][0], 
                                             label=legend_text[i][1], 
                                             alpha=kwargs['legend_patch_transparency']))

        # legend
        if kwargs.get('legend', self.config.legend):
            self.plotMS.legend(loc=kwargs.get('legend_position', self.config.legendPosition), 
                               ncol=kwargs.get('legend_num_columns', self.config.legendColumns),
                               fontsize=kwargs.get('legend_font_size', self.config.legendFontSize),
                               frameon=kwargs.get('legend_frame_on', self.config.legendFrame),
                               framealpha=kwargs.get('legend_transparency' ,self.config.legendAlpha),
                               markerfirst=kwargs.get('legend_marker_first', self.config.legendMarkerFirst),
                               markerscale=kwargs.get('legend_marker_size', self.config.legendMarkerSize),
                               fancybox=kwargs.get('legend_fancy_box', self.config.legendFancyBox),
                               scatterpoints=kwargs.get('legend_num_markers', self.config.legendNumberMarkers),
                               handles=handles)
            
            leg = self.plotMS.axes.get_legend()
            leg.draggable()

    def plot_2D_update_data(self, xvals, yvals, xlabel, ylabel, zvals, **kwargs):
        
        # override parameters
        if not self.lock_plot_from_updating:
            self.plot_parameters = kwargs
        else:
            kwargs = merge_two_dicts(kwargs, self.plot_parameters)
            self.plot_parameters = kwargs
        
        # update limits and extents
        extent = self.extents(xvals)+self.extents(yvals)
        
        self.cax.set_data(zvals)
        self.cax.set_norm(kwargs['colormap_norm'])
        self.cax.set_extent(extent)
        self.cax.set_cmap(kwargs['colormap'])
        self.cax.set_interpolation(kwargs['interpolation'])
        
        xmin, xmax, ymin, ymax = extent
        self.plotMS.set_xlim(xmin, xmax)#-0.5)
        self.plotMS.set_ylim(ymin, ymax)#-0.5)
        
        extent = [xmin, ymin, xmax, ymax]
        self.update_extents(extent)
        self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]
        
        
        self.plotMS.set_xlabel(xlabel, fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'])
        self.plotMS.set_ylabel(ylabel, fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'])
        
        try:
            leg = self.plotMS.axes.get_legend()
            leg.remove()
        except: pass
    
        try:
            self.cbar.remove()   
            if kwargs['colorbar']:
                cbarDivider = make_axes_locatable(self.plotMS)
                # pad controls how close colorbar is to the axes
                self.cbar = cbarDivider.append_axes(kwargs['colorbar_position'], 
                                              size="".join([str(kwargs['colorbar_width']), "%"]), 
                                              pad=kwargs['colorbar_pad'])
    
                ticks = [np.min(zvals), (np.max(zvals)-np.min(zvals))/2, np.max(zvals)]
                if ticks[1] in [ticks[0], ticks[2]]: ticks[1] = 0
                
                if self.plot_name in ['RMSD', 'RMSF']:
                    tick_labels = ["-100", "%", "100"]
                else:
                    tick_labels = ["0", "%", "100"]
                
                self.cbar.ticks = ticks
                self.cbar.tick_labels = tick_labels
                
                if kwargs['colorbar_position'] in ['left', 'right']:
                    self.figure.colorbar(self.cax, cax=self.cbar, ticks=ticks, orientation='vertical')
                    self.cbar.yaxis.set_ticks_position(kwargs['colorbar_position'])
                    self.cbar.set_yticklabels(tick_labels)
                else:
                    self.figure.colorbar(self.cax, cax=self.cbar, ticks=ticks, orientation='horizontal')
                    self.cbar.xaxis.set_ticks_position(kwargs['colorbar_position'])
                    self.cbar.set_xticklabels(tick_labels)
                    
                # setup other parameters
                self.cbar.tick_params(labelsize=kwargs['colorbar_label_size'])
        except: pass
    
    
    def plot_1D(self, xvals=None, yvals=None, title="", xlabel="",
                ylabel="", label="", xlimits=None, color="black", 
                zoom="box", plotType=None, testMax='yvals', testX=False, 
                allowWheel=True, axesSize=None, **kwargs):
        """
        Plots MS and 1DT data
        """
        # Setup parameters
        self.plotflag = True # Used only if saving data
        self.zoomtype = zoom
        self.plot_name = plotType

        # override parameters
        if not self.lock_plot_from_updating:
            if axesSize is not None:
                self._axes = axesSize
            self.plot_parameters = kwargs
        else:
            kwargs = merge_two_dicts(kwargs, self.plot_parameters)
            self.plot_parameters = kwargs

        matplotlib.rc('xtick', labelsize=kwargs['tick_size'])
        matplotlib.rc('ytick', labelsize=kwargs['tick_size'])      
        
        if testMax == 'yvals':
            ydivider, expo = self.testXYmaxValsUpdated(values=yvals)
            if expo > 1:
                offset_text = r'x$\mathregular{10^{%d}}$' % expo
                ylabel = ''.join([ylabel, " [", offset_text,"]"])
                yvals = divide(yvals, float(ydivider))
        
        if testX:
            xvals, xlabel, __ = self.kda_test(xvals)
            
        
        # Simple hack to reduce size is to use different subplot size
        self.plotMS = self.figure.add_axes(self._axes)
        self.plotMS.plot(xvals, yvals, 
                         color=kwargs['line_color'], 
                         label=label,
                         linewidth=kwargs['line_width'],
                         linestyle=kwargs['line_style'])
        
        if kwargs['shade_under']:
            shade_kws = dict(
                facecolor=kwargs['shade_under_color'],
                alpha=kwargs.get("shade_under_transparency", 0.25),
                clip_on=kwargs.get("clip_on", True),
                zorder=kwargs.get("zorder", 1),
                )
            self.plotMS.fill_between(xvals, 0, yvals, **shade_kws)
        
        
        # Setup parameters
        if xlimits == None or xlimits[0] == None or xlimits[1] == None:
            xlimits = [min(xvals), max(xvals)]
        
        self.plotMS.set_xlim([xlimits[0], xlimits[1]])
        self.plotMS.set_ylim([min(yvals), max(yvals)+0.01])
        
        extent= [xlimits[0], 0, xlimits[-1],max(yvals)+0.01] 

        if kwargs.get('minor_ticks_off', False) or ylabel == 'Scans' or xlabel == 'Charge':
            self.plotMS.xaxis.set_tick_params(which='minor', bottom='off')
            self.plotMS.xaxis.set_major_locator(MaxNLocator(integer=True))

        # convert weights
        if kwargs['label_weight']: kwargs['label_weight'] = "heavy"
        else: kwargs['label_weight'] = "normal"

        self.plotMS.set_xlabel(xlabel, 
                               labelpad=kwargs['label_pad'], 
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'])
        self.plotMS.set_ylabel(ylabel, 
                               labelpad=kwargs['label_pad'], 
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'])
        
        # update axis frame
        if kwargs['axis_onoff']: self.plotMS.set_axis_on()
        else: self.plotMS.set_axis_off()
                
        self.plotMS.tick_params(axis='both',  
                                left=kwargs['ticks_left'], 
                                right=kwargs['ticks_right'], 
                                top=kwargs['ticks_top'],
                                bottom=kwargs['ticks_bottom'],
                                labelleft=kwargs['tickLabels_left'],
                                labelright=kwargs['tickLabels_right'],
                                labeltop=kwargs['tickLabels_top'],
                                labelbottom=kwargs['tickLabels_bottom'])
                
        for __, line in enumerate(self.plotMS.get_lines()):
            line.set_linewidth(kwargs['line_width'])
            line.set_linestyle(kwargs['line_style'])
        
        if title != "": 
            if kwargs['title_weight']: title_weight = "heavy"
            else: title_weight = "normal"
            self.plotMS.set_title(title,
                                  fontsize=kwargs['title_size'], 
                                  weight=title_weight)
        
        self.plotMS.spines['left'].set_visible(kwargs['spines_left'])
        self.plotMS.spines['right'].set_visible(kwargs['spines_right'])
        self.plotMS.spines['top'].set_visible(kwargs['spines_top'])
        self.plotMS.spines['bottom'].set_visible(kwargs['spines_bottom'])
        [i.set_linewidth(kwargs['frame_width']) for i in self.plotMS.spines.itervalues()]

        self.setup_zoom([self.plotMS], self.zoomtype, data_lims=extent, 
                        plotName=plotType, allowWheel=allowWheel)
         
        # Setup X-axis getter
        self.setupGetXAxies([self.plotMS])
        self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]
    #-----

    def plot_1D_barplot(self, xvals, yvals, labels, colors, xlabel="", ylabel="",
                        title="", zoom="box", axesSize=None, 
                        plotType=None, **kwargs):
        self.plotflag = True # Used only if saving data
        self.zoomtype = zoom
        self.plot_name = plotType

        # override parameters
        if not self.lock_plot_from_updating:
            if axesSize is not None:
                self._axes = axesSize
            self.plot_parameters = kwargs
        else:
            kwargs = merge_two_dicts(kwargs, self.plot_parameters)
            self.plot_parameters = kwargs

        matplotlib.rc('xtick', labelsize=kwargs['tick_size'])
        matplotlib.rc('ytick', labelsize=kwargs['tick_size'])      
        
        # Simple hack to reduce size is to use different subplot size
        xticloc = np.array(xvals)
        self.plotMS = self.figure.add_axes(self._axes, xticks=xticloc)
        self.plotMS.bar(xvals, yvals, color=colors, label="Intensities", width=1)
        peaklabels = [str(p) for p in labels]
        self.plotMS.set_xticklabels(peaklabels, 
                                    rotation=90, #90 
                                    fontsize=kwargs['label_size'])
        # convert weights
        if kwargs['label_weight']:
            kwargs['label_weight'] = "heavy"
        else:
            kwargs['label_weight'] = "normal"

        self.plotMS.set_xlabel(xlabel, 
                               labelpad=kwargs['label_pad'], 
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'])
        self.plotMS.set_ylabel(ylabel, 
                               labelpad=kwargs['label_pad'], 
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'])
        
        # update axis frame
        if kwargs['axis_onoff']: 
            self.plotMS.set_axis_on()
        else: 
            self.plotMS.set_axis_off()
                
        self.plotMS.tick_params(axis='both',  
                                left=kwargs['ticks_left'], 
                                right=kwargs['ticks_right'], 
                                top=kwargs['ticks_top'],
                                bottom=kwargs['ticks_bottom'],
                                labelleft=kwargs['tickLabels_left'],
                                labelright=kwargs['tickLabels_right'],
                                labeltop=kwargs['tickLabels_top'],
                                labelbottom=kwargs['tickLabels_bottom'])
                
        for __, line in enumerate(self.plotMS.get_lines()):
            line.set_linewidth(kwargs['line_width'])
            line.set_linestyle(kwargs['line_style'])
        
        if title != "": 
            if kwargs['title_weight']: title_weight = "heavy"
            else: title_weight = "normal"
            self.plotMS.set_title(title,
                                  fontsize=kwargs['title_size'], 
                                  weight=title_weight)
        
        self.plotMS.spines['left'].set_visible(kwargs['spines_left'])
        self.plotMS.spines['right'].set_visible(kwargs['spines_right'])
        self.plotMS.spines['top'].set_visible(kwargs['spines_top'])
        self.plotMS.spines['bottom'].set_visible(kwargs['spines_bottom'])
        [i.set_linewidth(kwargs['frame_width']) for i in self.plotMS.spines.itervalues()]

    def plot_1D_scatter(self, xvals=None, yvals=None, classList=None,
                           color='red', title='',xlabel="", 
                           ylabel="", xlimits=None, axesSize=None,
                           plotName='whole', **kwargs):
        # Setup parameters
        self.plotflag = True # Used only if saving data
        self.zoomtype = "box"
        self.plot_name = plotName

        # override parameters
        if not self.lock_plot_from_updating:
            if axesSize is not None:
                self._axes = axesSize
            self.plot_parameters = kwargs
        else:
            kwargs = merge_two_dicts(kwargs, self.plot_parameters)
            self.plot_parameters = kwargs
        
        matplotlib.rc('xtick', labelsize=kwargs['tick_size'])
        matplotlib.rc('ytick', labelsize=kwargs['tick_size'])      

        # Plot 
        self.plotMS = self.figure.add_axes(self._axes)
        if plotName == 'whole':
            self.plotMS.scatter(xvals, yvals, 
                                edgecolors=kwargs['scatter_edge_color'],
                                color=kwargs['scatter_color'], 
                                s=kwargs['scatter_size'],
                                marker=kwargs['scatter_shape'],
                                alpha=kwargs['scatter_alpha'])
            
        else:
            for key in set(list(classList)):
                self.plotMS.scatter(xvals[key], yvals[key], 
                                    edgecolors=color[key],
                                    color=color[key], 
                                    s=kwargs['scatter_size'],
                                    marker=kwargs['scatter_shape'],
                                    alpha=kwargs['scatter_alpha'],
                                    label=key)
            # Find new xlimits
            xvals, yvals = find_limits(xvals, yvals)
            
            if kwargs.get('legend', self.config.legend):
                self.plotMS.legend(loc=kwargs.get('legend_position', self.config.legendPosition), 
                                   ncol=kwargs.get('legend_num_columns', self.config.legendColumns),
                                   fontsize=kwargs.get('legend_font_size', self.config.legendFontSize),
                                   frameon=kwargs.get('legend_frame_on', self.config.legendFrame),
                                   framealpha=kwargs.get('legend_transparency' ,self.config.legendAlpha),
                                   markerfirst=kwargs.get('legend_marker_first', self.config.legendMarkerFirst),
                                   markerscale=kwargs.get('legend_marker_size', self.config.legendMarkerSize),
                                   fancybox=kwargs.get('legend_fancy_box', self.config.legendFancyBox),
                                   scatterpoints=kwargs.get('legend_num_markers', self.config.legendNumberMarkers))
            
        # Setup parameters
        if xlimits == None or xlimits[0] == None or xlimits[1] == None:
            xlimits = [min(xvals)-0.5, max(xvals)+0.5]
            

        self.plotMS.set_xlim([xlimits[0], xlimits[1]])
        self.plotMS.set_ylim([min(yvals)-0.5, max(yvals)+0.5])
 
        extent= [xlimits[0], min(yvals)-0.5, xlimits[-1],max(yvals)+0.5] 

        self.plotMS.set_xlabel(xlabel, fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'])
        self.plotMS.set_ylabel(ylabel, fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'])
        
        # Setup font size info
        self.plotMS.tick_params(labelsize=kwargs['tick_size'])
                
        self.setup_zoom([self.plotMS], self.zoomtype, 
                        data_lims=extent)
            
        # Setup X-axis getter
        self.setupGetXAxies([self.plotMS])
        self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]
    #-----
    
    def plot_1D_compare(self, xvals=None, xvals1=None, xvals2=None, 
                        yvals1=None, yvals2=None, title="", xlabel="",
                       ylabel="", label="", xlimits=None, color="black", 
                       zoom="box", plotType="compare_MS", testMax='yvals', 
                       lineWidth=1, axesSize=None, **kwargs):
        """
        Plots MS and 1DT data
        """
        # Setup parameters
        self.plotflag = True # Used only if saving data
        self.zoomtype = zoom
        self.plot_name = plotType

        # override parameters
        if not self.lock_plot_from_updating:
            if axesSize is not None:
                self._axes = axesSize
            self.plot_parameters = kwargs
        else:
            kwargs = merge_two_dicts(kwargs, self.plot_parameters)
            self.plot_parameters = kwargs

        matplotlib.rc('xtick', labelsize=kwargs['tick_size'])
        matplotlib.rc('ytick', labelsize=kwargs['tick_size'])      
        
        if testMax == 'yvals':
            ydivider, expo = self.testXYmaxValsUpdated(values=yvals1)
            if expo > 1:
                yvals1 = divide(yvals1, float(ydivider))
                 
            ydivider, expo = self.testXYmaxValsUpdated(values=yvals2)
            if expo > 1:
                yvals2 = divide(yvals2, float(ydivider))
        
        if kwargs['inverse']:
            yvals2 = -yvals2
        
        if xvals is None:
            if xvals2 is None:
                xvals2 = xvals1
        elif xvals1 is None and xvals2 is None:
            xvals1 = xvals2 = xvals
        
        self.plotMS = self.figure.add_axes(self._axes)
        self.plotMS.plot(xvals1, yvals1, 
                         color=kwargs['line_color_1'], 
                         label=label[0],
                         linewidth=kwargs['line_width'],
                         linestyle=kwargs['line_style_1'],
                         alpha=kwargs['line_transparency_1'])
        
        self.plotMS.plot(xvals2, yvals2, 
                         color=kwargs['line_color_2'], 
                         label=label[1],
                         linewidth=kwargs['line_width'],
                         linestyle=kwargs['line_style_2'],
                         alpha=kwargs['line_transparency_2'])
    
        self.plotMS.axhline(linewidth=kwargs['line_width'],
                            color='k')
        
        xlimits = np.min([np.min(xvals1), np.min(xvals2)]), np.max([np.max(xvals1), np.max(xvals2)])
        ylimits = np.min([np.min(yvals1), np.min(yvals2)]), np.max([np.max(yvals1), np.max(yvals2)])
        # Setup parameters
# 
        extent= [xlimits[0], ylimits[0]-0.01, xlimits[-1], ylimits[1]+0.01] 
        
        self.plotMS.set_xlabel(xlabel, fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'])
        self.plotMS.set_ylabel(ylabel, fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'])
        
        # update axis frame
        if kwargs['axis_onoff']: 
            self.plotMS.set_axis_on()
        else: 
            self.plotMS.set_axis_off()
                
        self.plotMS.tick_params(axis='both',  
                                left=kwargs['ticks_left'], 
                                right=kwargs['ticks_right'], 
                                top=kwargs['ticks_top'],
                                bottom=kwargs['ticks_bottom'],
                                labelleft=kwargs['tickLabels_left'],
                                labelright=kwargs['tickLabels_right'],
                                labeltop=kwargs['tickLabels_top'],
                                labelbottom=kwargs['tickLabels_bottom'])
                
        self.plotMS.spines['left'].set_visible(kwargs['spines_left'])
        self.plotMS.spines['right'].set_visible(kwargs['spines_right'])
        self.plotMS.spines['top'].set_visible(kwargs['spines_top'])
        self.plotMS.spines['bottom'].set_visible(kwargs['spines_bottom'])
        [i.set_linewidth(kwargs['frame_width']) for i in self.plotMS.spines.itervalues()]
        
        # Setup font size info
        self.plotMS.tick_params(labelsize=kwargs['tick_size'])
 
         # legend
        if kwargs.get('legend', self.config.legend):
            self.plotMS.legend(loc=kwargs.get('legend_position', self.config.legendPosition), 
                               ncol=kwargs.get('legend_num_columns', self.config.legendColumns),
                               fontsize=kwargs.get('legend_font_size', self.config.legendFontSize),
                               frameon=kwargs.get('legend_frame_on', self.config.legendFrame),
                               framealpha=kwargs.get('legend_transparency' ,self.config.legendAlpha),
                               markerfirst=kwargs.get('legend_marker_first', self.config.legendMarkerFirst),
                               markerscale=kwargs.get('legend_marker_size', self.config.legendMarkerSize),
                               fancybox=kwargs.get('legend_fancy_box', self.config.legendFancyBox),
                               scatterpoints=kwargs.get('legend_num_markers', self.config.legendNumberMarkers))
            leg = self.plotMS.axes.get_legend()
            leg.draggable()
            
        self.setup_zoom([self.plotMS], self.zoomtype, data_lims=extent)

        # Setup X-axis getter
        self.setupGetXAxies([self.plotMS])
        self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]
    #-----

    def plot_1D_overlay(self, xvals, yvals, colors, xlabel, ylabel, labels, 
                        xlimits, zoom="box", plotType=None, testMax='yvals', 
                        axesSize=None, title="", allowWheel=True, **kwargs):
        # Setup parameters
        self.plotflag = True # Used only if saving data
        self.zoomtype = zoom
        self.plot_name = plotType

        # override parameters
        if not self.lock_plot_from_updating:
            if axesSize is not None:
                self._axes = axesSize
            self.plot_parameters = kwargs
        else:
            kwargs = merge_two_dicts(kwargs, self.plot_parameters)
            self.plot_parameters = kwargs
        
        matplotlib.rc('xtick', labelsize=kwargs['tick_size'])
        matplotlib.rc('ytick', labelsize=kwargs['tick_size'])      
        
        # Plot 
        self.plotMS = self.figure.add_axes(self._axes)
        
        handles = []
        for xval, yval, color, label in zip(xvals, yvals, colors, labels):
            self.plotMS.plot(xval, yval, 
                             color=color, 
                             label=label, 
                             linewidth=kwargs['line_width'],
                             linestyle=kwargs['line_style'])
            
            
            if kwargs['shade_under']:
                handles.append(patches.Patch(color=color, label=label, alpha=0.25))
                shade_kws = dict(
                    facecolor=color,
                    alpha=kwargs.get("shade_under_transparency", 0.25),
                    clip_on=kwargs.get("clip_on", True),
                    zorder=kwargs.get("zorder", 1),
                    )
                self.plotMS.fill_between(xval, 0, yval, **shade_kws)
            
        if not kwargs['shade_under']:
            handles, labels = self.plotMS.get_legend_handles_labels()
            
            
        if kwargs.get('legend', self.config.legend):
            self.plotMS.legend(loc=kwargs.get('legend_position', self.config.legendPosition), 
                               ncol=kwargs.get('legend_num_columns', self.config.legendColumns),
                               fontsize=kwargs.get('legend_font_size', self.config.legendFontSize),
                               frameon=kwargs.get('legend_frame_on', self.config.legendFrame),
                               framealpha=kwargs.get('legend_transparency' ,self.config.legendAlpha),
                               markerfirst=kwargs.get('legend_marker_first', self.config.legendMarkerFirst),
                               markerscale=kwargs.get('legend_marker_size', self.config.legendMarkerSize),
                               fancybox=kwargs.get('legend_fancy_box', self.config.legendFancyBox),
                               scatterpoints=kwargs.get('legend_num_markers', self.config.legendNumberMarkers),
                               handles=handles)
            
            leg = self.plotMS.axes.get_legend()
            leg.draggable()
        
        self.plotMS.set_xlabel(xlabel, fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'])
        self.plotMS.set_ylabel(ylabel, fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'])
        
        # Setup parameters
        if xlimits == None or xlimits[0] == None or xlimits[1] == None:
            xlimits = [min(xvals), max(xvals)]
        
        self.plotMS.set_xlim([xlimits[0], xlimits[1]])
        self.plotMS.set_ylim([min(np.concatenate(yvals)), max(np.concatenate(yvals))+0.01])

        extent= [xlimits[0], min(np.concatenate(yvals)), xlimits[-1],max(np.concatenate(yvals))+0.01] 

        # update axis frame
        if kwargs['axis_onoff']: self.plotMS.set_axis_on()
        else: self.plotMS.set_axis_off()
        
        self.plotMS.tick_params(axis='both',  
                                left=kwargs['ticks_left'], 
                                right=kwargs['ticks_right'], 
                                top=kwargs['ticks_top'],
                                bottom=kwargs['ticks_bottom'],
                                labelleft=kwargs['tickLabels_left'],
                                labelright=kwargs['tickLabels_right'],
                                labeltop=kwargs['tickLabels_top'],
                                labelbottom=kwargs['tickLabels_bottom'])
                
        for __, line in enumerate(self.plotMS.get_lines()):
            line.set_linewidth(kwargs['line_width'])
            line.set_linestyle(kwargs['line_style'])
        
        self.plotMS.spines['left'].set_visible(kwargs['spines_left'])
        self.plotMS.spines['right'].set_visible(kwargs['spines_right'])
        self.plotMS.spines['top'].set_visible(kwargs['spines_top'])
        self.plotMS.spines['bottom'].set_visible(kwargs['spines_bottom'])
        [i.set_linewidth(kwargs['frame_width']) for i in self.plotMS.spines.itervalues()]
        
        if title != "": 
            if kwargs['title_weight']: title_weight = "heavy"
            else: title_weight = "normal"
            self.plotMS.set_title(title,
                                  fontsize=kwargs['title_size'], 
                                  weight=title_weight)
        
        self.setup_zoom([self.plotMS], self.zoomtype, data_lims=extent, 
                        plotName=plotType, allowWheel=allowWheel)        
        # Setup X-axis getter
        self.setupGetXAxies([self.plotMS])
        self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]

    def plot_1D_waterfall(self, xvals=None, yvals=None, zvals=None, label="", xlabel="", 
                          colorList=[], ylabel="", zoom="box", axesSize=None, plotName='1D',
                          xlimits=None, plotType="Waterfall", **kwargs):
        
        self.zoomtype = zoom
        self.plot_name = plotType
        
        # override parameters
        if not self.lock_plot_from_updating:
            if axesSize is not None:
                self._axes = axesSize
            self.plot_parameters = kwargs
        else:
            kwargs = merge_two_dicts(kwargs, self.plot_parameters)
            self.plot_parameters = kwargs


        matplotlib.rc('xtick', labelsize=kwargs['tick_size'])
        matplotlib.rc('ytick', labelsize=kwargs['tick_size'])   
        
        self.plot_parameters = kwargs
        self.plotMS = self.figure.add_axes(self._axes)
        
        if zvals is not None:
            if kwargs['reverse']:
                zvals = np.fliplr(zvals)
    
            # Setup parameters
            if xlimits == None or xlimits[0] == None or xlimits[1] == None:
                xlimits = [min(xvals), max(xvals)]
            
            # Always normalizes data - otherwise it looks pretty bad
            if kwargs['increment'] != 0:
                zvals = normalizeIMS(inputData=zvals)
            else:
                ylabel = 'Intensity'
                ydivider, expo = self.testXYmaxValsUpdated(values=zvals)
                if expo > 1:
                    zvals = divide(zvals, float(ydivider)) 
                    offset_text = r'x$\mathregular{10^{%d}}$' % expo
                    ylabel = ''.join([ylabel, " [", offset_text,"]"])
            
            color_idx= linspace(1, 0,len(zvals[1,:]))
            voltage_idx = linspace(0, len(zvals[1,:])-1,len(zvals[1,:]))#-1)
            
            yOffset = kwargs['offset'] * (len(zvals[1,:])+1)
            if kwargs['use_colormap']:            
                waterfallCmap = plt.cm.get_cmap(name=kwargs['colormap'], 
                                                lut=len(zvals[1,:]))
    
                # Iterate over the colormap to get the color shading we desire 
                for i, idx in zip(voltage_idx[::-1], color_idx[::-1]):
                    y = zvals[:,int(i)] 
                    self.plotMS.plot(xvals, (y+yOffset), 
                                     color=waterfallCmap(idx), 
                                     linewidth=kwargs['line_width'],
                                     linestyle=kwargs['line_style'],
                                     label=label)
                    yOffset=yOffset-kwargs['increment']
            else:
                for i in voltage_idx[::-1]:
                    y = zvals[:,int(i)] 
                    self.plotMS.plot(xvals, (y+yOffset), 
                                     color=kwargs['line_color'], 
                                     linewidth=kwargs['line_width'],
                                     linestyle=kwargs['line_style'],
                                     label=label)
                    yOffset=yOffset-kwargs['increment']
        else:
            icount = len(xvals)
            yOffset = kwargs['offset'] * (icount+1)
            waterfallCmap = plt.cm.get_cmap(name=kwargs['colormap'], lut=icount)
            for irow in xrange(len(xvals)):
                if kwargs['reverse']:
                    xvals[irow] = xvals[irow][::-1]
                    yvals[irow] = yvals[irow][::-1]
                    if len(colorList) == icount:
                        colorList[irow] = colorList[irow][::-1]

                # Always normalizes data - otherwise it looks pretty bad
                if kwargs['increment'] != 0:
                    yvals[irow] = normalizeMS(inputData=yvals[irow])
                else:
                    ylabel = 'Intensity'
                    try:
                        ydivider, expo = self.testXYmaxValsUpdated(values=zvals)
                        if expo > 1:
                            yvals[irow] = divide(yvals[irow], float(ydivider)) 
                            offset_text = r'x$\mathregular{10^{%d}}$' % expo
                            ylabel = ''.join([ylabel, " [", offset_text,"]"])
                    except AttributeError:
                        kwargs['increment'] = 0.00001
                        yvals[irow] = normalizeMS(inputData=yvals[irow])
                
                color_idx = linspace(1, 0, icount)
                voltage_idx = linspace(0, icount-1, icount)
                
                if len(colorList) == icount:
                    y = yvals[irow]
                    self.plotMS.plot(xvals[irow], (y+yOffset), 
                                     color=colorList[irow], 
                                     linewidth=kwargs['line_width'],
                                     linestyle=kwargs['line_style'],
                                     label=label)
                    kwargs['shade_under'] = True
                    if kwargs['shade_under'] and len(colorList) < 25:
                        shade_kws = dict(
                            facecolor=colorList[irow],
                            alpha=kwargs.get("shade_under_transparency", 0.25),
                            clip_on=kwargs.get("clip_on", True),
                            )
                        self.plotMS.fill_between(xvals[irow], np.min((y+yOffset)), (y+yOffset), **shade_kws)
                    yOffset=yOffset-kwargs['increment']
                elif kwargs['use_colormap']:
                    y = yvals[irow]
                    self.plotMS.plot(xvals[irow], (y+yOffset), 
                                     color=waterfallCmap(irow), 
                                     linewidth=kwargs['line_width'],
                                     linestyle=kwargs['line_style'],
                                     label=label)
                    yOffset=yOffset-kwargs['increment']
                else:
                    y = yvals[irow]
                    self.plotMS.plot(xvals[irow], (y+yOffset), 
                                     color=kwargs['line_color'], 
                                     linewidth=kwargs['line_width'],
                                     linestyle=kwargs['line_style'],
                                     label=label)
                    yOffset=yOffset-kwargs['increment']
                    
            # Find new xlimits
            xvals, yvals = find_limits_list(xvals, yvals)
            xlimits = (np.min(xvals), np.max(xvals))


        self.plotMS.set_xlabel(xlabel, 
                               labelpad=kwargs['label_pad'], 
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'])
        
        # update axis frame
        if kwargs['axis_onoff']: self.plotMS.set_axis_on()
        else: self.plotMS.set_axis_off()
                
        self.plotMS.tick_params(axis='both',  
                                left=False,#kwargs['ticks_left'], 
                                right=kwargs['ticks_right'], 
                                top=kwargs['ticks_top'],
                                bottom=kwargs['ticks_bottom'],
                                labelleft=False,#kwargs['tickLabels_left'],
                                labelright=kwargs['tickLabels_right'],
                                labeltop=kwargs['tickLabels_top'],
                                labelbottom=kwargs['tickLabels_bottom'])
                
        for __, line in enumerate(self.plotMS.get_lines()):
            line.set_linewidth(kwargs['line_width'])
            line.set_linestyle(kwargs['line_style'])
        
        self.plotMS.spines['left'].set_visible(kwargs['spines_left'])
        self.plotMS.spines['right'].set_visible(kwargs['spines_right'])
        self.plotMS.spines['top'].set_visible(kwargs['spines_top'])
        self.plotMS.spines['bottom'].set_visible(kwargs['spines_bottom'])
        [i.set_linewidth(kwargs['frame_width']) for i in self.plotMS.spines.itervalues()]

        ylimits = self.plotMS.get_ylim()
        extent = [xlimits[0], ylimits[0], xlimits[1], ylimits[1]]
        self.setup_zoom([self.plotMS], self.zoomtype, plotName=plotName,
                        data_lims=extent)
        self.plot_limits = [xlimits[0], xlimits[1], ylimits[0], ylimits[1]]
        # Setup X-axis getter
        self.setupGetXAxies([self.plotMS])
        
        self.plotMS.set_xlim([xlimits[0], xlimits[1]])
        
    def plot_n_grid_2D_overlay(self, n_zvals, cmap_list, title_list, 
                               xvals, yvals, xlabel, ylabel, plotName='Overlay_Grid', 
                               axesSize=None, **kwargs):
        self.plot_name = plotName
        self.zoomtype = "box"        
        if axesSize is not None:
            self._axes = axesSize
        self.plot_parameters = kwargs
        
        n_grid = len(n_zvals)
        if n_grid in [2]: n_rows, n_cols = 1, 2 
        elif n_grid in [3, 4]: n_rows, n_cols = 2, 2 
        elif n_grid in [5, 6]: n_rows, n_cols = 2, 3
        elif n_grid in [7, 8, 9]: n_rows, n_cols = 3, 3
        elif n_grid in [10, 11, 12]: n_rows, n_cols = 3, 4
        elif n_grid in [13, 14, 15, 16]: n_rows, n_cols = 4, 4
        else: return
        
        # convert weights
        if kwargs['title_weight']: kwargs['title_weight'] = "heavy"
        else: kwargs['title_weight'] = "normal"
        
        if kwargs['label_weight']: kwargs['label_weight'] = "heavy"
        else: kwargs['label_weight'] = "normal"
        
        # set tick size
        matplotlib.rc('xtick', labelsize=kwargs['tick_size'])
        matplotlib.rc('ytick', labelsize=kwargs['tick_size'])      
                
        gs = gridspec.GridSpec(nrows=n_rows, ncols=n_cols)
        
        extent = self.extents(xvals)+self.extents(yvals)
        xmin, xmax = np.min(xvals), np.max(xvals) 
        ymin, ymax = np.min(yvals), np.max(yvals) 
        plt_list = []
        for i in range(n_grid):
            row = int(i // n_cols)
            col = i % n_cols
            ax = self.figure.add_subplot(gs[row, col], aspect='auto')
            ax.imshow(n_zvals[i], extent=extent,
                      cmap=cmap_list[i], 
                      interpolation=kwargs['interpolation'],
                      aspect='auto', origin='lower')
            
            ax.set_xlim(xmin, xmax-0.5)
            ax.set_ylim(ymin, ymax-0.5)
            ax.tick_params(axis='both',  
                           left=kwargs['ticks_left'], 
                            right=kwargs['ticks_right'], 
                            top=kwargs['ticks_top'],
                            bottom=kwargs['ticks_bottom'],
                            labelleft=kwargs['tickLabels_left'],
                            labelright=kwargs['tickLabels_right'],
                            labeltop=kwargs['tickLabels_top'],
                            labelbottom=kwargs['tickLabels_bottom'])
            
            # spines
            ax.spines['left'].set_visible(kwargs['spines_left'])
            ax.spines['right'].set_visible(kwargs['spines_right'])
            ax.spines['top'].set_visible(kwargs['spines_top'])
            ax.spines['bottom'].set_visible(kwargs['spines_bottom'])
            
            ax.set_title(label=title_list[i],
                         fontdict={'fontsize':kwargs['title_size'],
                                   'fontweight':kwargs['title_weight']})
            
            # remove ticks for anything thats not on the outskirts
            if col == (n_cols-1): ax.set_yticks([])
            if n_cols == 3 and col == (n_cols-2): ax.set_yticks([])
            if n_cols == 4 and col == (n_cols-3): ax.set_yticks([])
            if row != (n_rows-1): ax.set_xticks([])

            # update axis frame
            if kwargs['axis_onoff']: ax.set_axis_on()
            else: ax.set_axis_off()
            plt_list.append(ax)
                
            kwargs['label_pad'] = 5
            if col == 0:
                ax.set_ylabel(ylabel, 
                              labelpad=kwargs['label_pad'], 
                              fontsize=kwargs['label_size'], 
                              weight=kwargs['label_weight'])
            if row == n_rows-1:
                ax.set_xlabel(xlabel, 
                              labelpad=kwargs['label_pad'], 
                              fontsize=kwargs['label_size'], 
                              weight=kwargs['label_weight'])

        gs.tight_layout(self.figure)
        self.figure.tight_layout()
        
        extent = [xmin, ymin, xmax, ymax]
        self.setup_zoom(plt_list, self.zoomtype, data_lims=extent)
        self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]
    
    def plot_grid_2D_overlay(self, zvals_1, zvals_2, zvals_cum, xvals, yvals, 
                             xlabel, ylabel, plotName='Overlay_Grid', 
                             axesSize=None, **kwargs):

        self.plot_name = plotName
        self.zoomtype = "box"        

        # override parameters
        if not self.lock_plot_from_updating:
            if axesSize is not None:
                self._axes = axesSize
            self.plot_parameters = kwargs
        else:
            kwargs = merge_two_dicts(kwargs, self.plot_parameters)
            self.plot_parameters = kwargs
        
        gs = gridspec.GridSpec(nrows=2, ncols=2, height_ratios=[1,1], width_ratios=[1,2])
        gs.update(hspace=kwargs['rmsd_hspace'], wspace=kwargs['rmsd_hspace'])
        
        self.plot2D_upper = self.figure.add_subplot(gs[0,0], aspect='auto')
        self.plot2D_lower = self.figure.add_subplot(gs[1,0], aspect='auto')
        self.plot2D_side = self.figure.add_subplot(gs[:,1], aspect='auto')
        
        # Calculate extents
        extent = self.extents(xvals)+self.extents(yvals)
        self.plot2D_upper.imshow(zvals_1, 
                                 extent=extent,
                                 cmap=kwargs.get('colormap_1', 'Reds'), 
                                 interpolation=kwargs['interpolation'],
                                 norm=kwargs['cmap_norm_1'], 
                                 aspect='auto', 
                                 origin='lower')
        
        self.plot2D_lower.imshow(zvals_2, 
                                 extent=extent,
                                 cmap=kwargs.get('colormap_2', 'Blues'), 
                                 interpolation=kwargs['interpolation'],
                                 norm=kwargs['cmap_norm_2'], 
                                 aspect='auto', 
                                 origin='lower')
        
        self.plot2D_side.imshow(zvals_cum, 
                                extent=extent,
                                cmap=kwargs['colormap'], 
                                interpolation=kwargs['interpolation'],
                                norm=kwargs['cmap_norm_cum'], 
                                aspect='auto', 
                                origin='lower')
        
        xmin, xmax = np.min(xvals), np.max(xvals) 
        ymin, ymax = np.min(yvals), np.max(yvals) 
        
        # ticks
        for plot in [self.plot2D_upper, self.plot2D_lower, self.plot2D_side]:
            plot.set_xlim(xmin, xmax-0.5)
            plot.set_ylim(ymin, ymax-0.5)
        
            plot.tick_params(axis='both',  
                                    left=kwargs['ticks_left'], 
                                    right=kwargs['ticks_right'], 
                                    top=kwargs['ticks_top'],
                                    bottom=kwargs['ticks_bottom'],
                                    labelleft=kwargs['tickLabels_left'],
                                    labelright=kwargs['tickLabels_right'],
                                    labeltop=kwargs['tickLabels_top'],
                                    labelbottom=kwargs['tickLabels_bottom'])
            
            # spines
            plot.spines['left'].set_visible(kwargs['spines_left'])
            plot.spines['right'].set_visible(kwargs['spines_right'])
            plot.spines['top'].set_visible(kwargs['spines_top'])
            plot.spines['bottom'].set_visible(kwargs['spines_bottom'])
            [i.set_linewidth(kwargs['frame_width']) for i in plot.spines.itervalues()]
            
            # update axis frame
            if kwargs['axis_onoff']: 
                plot.set_axis_on()
            else: 
                plot.set_axis_off()
                
            kwargs['label_pad'] = 5
            plot.set_xlabel(xlabel, 
                                   labelpad=kwargs['label_pad'], 
                                   fontsize=kwargs['label_size'], 
                                   weight=kwargs['label_weight'])
            plot.set_ylabel(ylabel, 
                                   labelpad=kwargs['label_pad'], 
                                   fontsize=kwargs['label_size'], 
                                   weight=kwargs['label_weight'])
        
        
        gs.tight_layout(self.figure)
        self.figure.tight_layout()
        extent = [xmin, ymin, xmax, ymax]
        self.setup_zoom([self.plot2D_upper, self.plot2D_lower, self.plot2D_side], 
                        self.zoomtype, data_lims=extent)
        self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]
        
    def plot_1D_2D(self, yvalsRMSF=None, zvals=None, labelsX=None, labelsY=None,
                   ylabelRMSF="", xlabelRMSD="",ylabelRMSD="", testMax = 'yvals', 
                   label="", zoom="box", plotName="RMSF", axesSize=None,  
                   **kwargs):
        """
        Plots RMSF and RMSD together
        """
        # Setup parameters
        gs = gridspec.GridSpec(2, 1, height_ratios=[1,3])
        gs.update(hspace=kwargs['rmsd_hspace'])
        self.plot_name = plotName
        self.zoomtype = zoom

        # override parameters
        if not self.lock_plot_from_updating:
            if axesSize is not None:
                self._axes = axesSize
            self.plot_parameters = kwargs
        else:
            kwargs = merge_two_dicts(kwargs, self.plot_parameters)
            self.plot_parameters = kwargs
                 
        if kwargs['label_weight']: kwargs['label_weight'] = "heavy"
        else: kwargs['label_weight'] = "normal"
        
        # set tick size
        matplotlib.rc('xtick', labelsize=kwargs['tick_size'])
        matplotlib.rc('ytick', labelsize=kwargs['tick_size'])  
                 
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
        else: ylabelRMSF = "RMSD (%)"
                         
        # Plot RMSF data (top plot)        
        if len(labelsX) != len(yvalsRMSF):
                dialogs.dlgBox(exceptionTitle='Missing data', 
                               exceptionMsg= 'Missing x-axis labels! Cannot execute this action!',
                               type="Error")
                return
             
        self.plotRMSF = self.figure.add_subplot(gs[0], aspect='auto')
        self.plotRMSF.plot(labelsX, yvalsRMSF, 
                           color=kwargs['rmsd_line_color'], 
                           linewidth=kwargs['rmsd_line_width'],
                           linestyle=kwargs['rmsd_line_style'])
        
        self.plotRMSF.fill_between(labelsX, yvalsRMSF,0, 
                                   edgecolor=kwargs['rmsd_line_color'],
                                   facecolor=kwargs['rmsd_underline_color'],
                                   alpha=kwargs['rmsd_underline_transparency'],
                                   hatch=kwargs['rmsd_underline_hatch'],
                                   linewidth=kwargs['rmsd_line_width'],
                                   linestyle=kwargs['rmsd_line_style']) 
         
        self.plotRMSF.set_xlim([min(labelsX), max(labelsX)])
        self.plotRMSF.set_ylim([0, max(yvalsRMSF)+0.2])
        self.plotRMSF.get_xaxis().set_visible(False)
 
        self.plotRMSF.set_ylabel(ylabelRMSF, 
                                 labelpad=kwargs['label_pad'], 
                                 fontsize=kwargs['label_size'], 
                                 weight=kwargs['label_weight'])
         
        extent = self.extents(labelsX) + self.extents(labelsY)
        self.plotMS = self.figure.add_subplot(gs[1], aspect='auto')
         
        self.cax = self.plotMS.imshow(zvals, extent=extent,
                                      cmap=kwargs['colormap'], 
                                      interpolation=kwargs['interpolation'],
                                      norm=kwargs['colormap_norm'], 
                                      aspect='auto', 
                                      origin='lower')
                 
        xmin, xmax = self.plotMS.get_xlim()
        ymin, ymax = self.plotMS.get_ylim()
        self.plotMS.set_xlim(xmin, xmax-0.5)
        self.plotMS.set_ylim(ymin, ymax-0.5)
         
        extent= [labelsX[0], labelsY[0], labelsX[-1],labelsY[-1]] 
        self.setup_zoom([self.plotMS], self.zoomtype, data_lims=extent,
                        plotName=plotName)
        self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]
          
        self.plotMS.set_xlabel(xlabelRMSD, 
                               labelpad=kwargs['label_pad'], 
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'])
        self.plotMS.set_ylabel(ylabelRMSD, 
                               labelpad=kwargs['label_pad'], 
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'])
 
        # setup colorbar
        if kwargs['colorbar']:
            cbarDivider = make_axes_locatable(self.plotMS)
            # pad controls how close colorbar is to the axes
            self.cbar = cbarDivider.append_axes(kwargs['colorbar_position'], 
                                          size="".join([str(kwargs['colorbar_width']), "%"]), 
                                          pad=kwargs['colorbar_pad'])
            tick_min = np.min(zvals)
            tick_max = np.max(zvals)
            tick_mid = np.median([tick_min + tick_max])
            ticks = [tick_min, tick_mid, tick_max]

            if plotName in ['RMSD', 'RMSF']:
                tick_labels = ["-100", "%", "100"]
            else: 
                tick_labels = ["0", "%", "100"]

            self.cbar.ticks = ticks
            self.cbar.tick_labels = tick_labels
            
            if kwargs['colorbar_position'] in ['left', 'right']:
                self.figure.colorbar(self.cax, cax=self.cbar, 
                                    ticks=ticks, 
                                     orientation='vertical')
                self.cbar.yaxis.set_ticks_position(kwargs['colorbar_position'])
                self.cbar.set_yticklabels(tick_labels)
            else:
                self.figure.colorbar(self.cax, cax=self.cbar, ticks=ticks, orientation='horizontal')
                self.cbar.xaxis.set_ticks_position(kwargs['colorbar_position'])
                self.cbar.set_xticklabels(tick_labels)
            
            print(self.cbar.get_yticks())
            # setup other parameters
            self.cbar.tick_params(labelsize=kwargs['colorbar_label_size'])
         
        # ticks
        self.plotMS.tick_params(axis='both',
                                left=kwargs['ticks_left'],
                                right=kwargs['ticks_right'],
                                top=kwargs['ticks_top'],
                                bottom=kwargs['ticks_bottom'],
                                labelleft=kwargs['tickLabels_left'],
                                labelright=kwargs['tickLabels_right'],
                                labeltop=kwargs['tickLabels_top'],
                                labelbottom=kwargs['tickLabels_bottom'])
         
        self.plotRMSF.tick_params(axis='both',
                                  left=kwargs['ticks_left_1D'],
                                  right=kwargs['ticks_right_1D'],
                                  top=kwargs['ticks_top_1D'],
                                  bottom=kwargs['ticks_bottom_1D'],
                                  labelleft=kwargs['tickLabels_left_1D'],
                                  labelright=kwargs['tickLabels_right_1D'],
                                  labeltop=kwargs['tickLabels_top_1D'],
                                  labelbottom=kwargs['tickLabels_bottom_1D'])
         
        # spines
        self.plotMS.spines['left'].set_visible(kwargs['spines_left'])
        self.plotMS.spines['right'].set_visible(kwargs['spines_right'])
        self.plotMS.spines['top'].set_visible(kwargs['spines_top'])
        self.plotMS.spines['bottom'].set_visible(kwargs['spines_bottom'])
        [i.set_linewidth(kwargs['frame_width']) for i in self.plotMS.spines.itervalues()]
         
        self.plotRMSF.spines['left'].set_visible(kwargs['spines_left_1D'])
        self.plotRMSF.spines['right'].set_visible(kwargs['spines_right_1D'])
        self.plotRMSF.spines['top'].set_visible(kwargs['spines_top_1D'])
        self.plotRMSF.spines['bottom'].set_visible(kwargs['spines_bottom_1D'])
        [i.set_linewidth(kwargs['frame_width']) for i in self.plotRMSF.spines.itervalues()]
 
        # update axis frame
        if kwargs['axis_onoff']: self.plotMS.set_axis_on()
        else: self.plotMS.set_axis_off()        
         
        if kwargs['axis_onoff_1D']: self.plotRMSF.set_axis_on()
        else: self.plotRMSF.set_axis_off()       

            
        # update gridspace
        gs.tight_layout(self.figure)
        self.figure.tight_layout()
        
    def plot_2D(self, zvals=None, title="", extent=None, xlabel="", ylabel="", zoom="box", 
                      axesSize=None, colorbar=False, legend=None, plotName="2D", **kwargs):      
        self.plotflag = True # Used only if saving data
        self.zoomtype = zoom
        self.plot_name = plotName
        
        # override parameters
        if not self.lock_plot_from_updating:
            if axesSize is not None:
                self._axes = axesSize
            self.plot_parameters = kwargs
        else:
            kwargs = merge_two_dicts(kwargs, self.plot_parameters)
            self.plot_parameters = kwargs
        
        matplotlib.rc('xtick', labelsize=kwargs['tick_size'])
        matplotlib.rc('ytick', labelsize=kwargs['tick_size'])      
                        
        # Plot
        self.plotMS = self.figure.add_axes(self._axes)

        if legend != None:
            for i in range(len(legend)):
                self.plotMS.plot(-1, -1, "-", 
                                 c=legend[i][1], 
                                 label=legend[i][0], 
                                 marker='s', 
                                 markersize=15, 
                                 linewidth=0)

        # Calculate extents
        xvals, yvals = zvals.shape
        xvals = np.arange(xvals)
        yvals = np.arange(yvals)
                
        # Add imshow
        self.cax = self.plotMS.imshow(zvals, 
                                      cmap=kwargs['colormap'], 
                                      interpolation=kwargs['interpolation'],
                                      norm=kwargs['colormap_norm'], 
                                      origin='lower',
                                      aspect='auto')
                
        xmin, xmax = self.plotMS.get_xlim()
        ymin, ymax = self.plotMS.get_ylim()
        self.plotMS.set_xlim(xmin, xmax-0.5)
        self.plotMS.set_ylim(ymin, ymax-0.5)
        extent = [xmin, ymin, xmax, ymax]

        cbarDivider = make_axes_locatable(self.plotMS)
        
        # legend
        if kwargs.get('legend', self.config.legend):
            self.plotMS.legend(loc=kwargs.get('legend_position', self.config.legendPosition), 
                               ncol=kwargs.get('legend_num_columns', self.config.legendColumns),
                               fontsize=kwargs.get('legend_font_size', self.config.legendFontSize),
                               frameon=kwargs.get('legend_frame_on', self.config.legendFrame),
                               framealpha=kwargs.get('legend_transparency' ,self.config.legendAlpha),
                               markerfirst=kwargs.get('legend_marker_first', self.config.legendMarkerFirst),
                               markerscale=kwargs.get('legend_marker_size', self.config.legendMarkerSize),
                               fancybox=kwargs.get('legend_fancy_box', self.config.legendFancyBox),
                               scatterpoints=kwargs.get('legend_num_markers', self.config.legendNumberMarkers))
            leg = self.plotMS.axes.get_legend()
            leg.draggable()
            
        # labels
        if xlabel in ['None', None]: xlabel=''
        if ylabel in ['None', None]: ylabel=''
        
        self.plotMS.set_xlabel(xlabel, 
                               labelpad=kwargs['label_pad'], 
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'])
        self.plotMS.set_ylabel(ylabel, 
                               labelpad=kwargs['label_pad'], 
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'])
        
        # setup colorbar
        if kwargs['colorbar']:
            # pad controls how close colorbar is to the axes
            self.cbar = cbarDivider.append_axes(kwargs['colorbar_position'], 
                                          size="".join([str(kwargs['colorbar_width']), "%"]), 
                                          pad=kwargs['colorbar_pad'])

            ticks = [np.min(zvals), (np.max(zvals)-np.min(zvals))/2, np.max(zvals)]
            
            self.cbar.ticks = ticks
#             self.cbar.tick_labels = tick_labels
            
            if kwargs['colorbar_position'] in ['left', 'right']:
                self.figure.colorbar(self.cax, cax=self.cbar, ticks=ticks, orientation='vertical')
                self.cbar.yaxis.set_ticks_position(kwargs['colorbar_position'])
                self.cbar.set_yticklabels(["0", "%", "100"])
            else:
                self.figure.colorbar(self.cax, cax=self.cbar, ticks=ticks, orientation='horizontal')
                self.cbar.xaxis.set_ticks_position(kwargs['colorbar_position'])
                self.cbar.set_xticklabels(["0", "%", "100"])
            
            # setup other parameters
            self.cbar.tick_params(labelsize=kwargs['colorbar_label_size'])
                
        # ticks
        self.plotMS.tick_params(axis='both',  
                                left=kwargs['ticks_left'], 
                                right=kwargs['ticks_right'], 
                                top=kwargs['ticks_top'],
                                bottom=kwargs['ticks_bottom'],
                                labelleft=kwargs['tickLabels_left'],
                                labelright=kwargs['tickLabels_right'],
                                labeltop=kwargs['tickLabels_top'],
                                labelbottom=kwargs['tickLabels_bottom'])
        
        # spines
        self.plotMS.spines['left'].set_visible(kwargs['spines_left'])
        self.plotMS.spines['right'].set_visible(kwargs['spines_right'])
        self.plotMS.spines['top'].set_visible(kwargs['spines_top'])
        self.plotMS.spines['bottom'].set_visible(kwargs['spines_bottom'])
        [i.set_linewidth(kwargs['frame_width']) for i in self.plotMS.spines.itervalues()]
        
        # update axis frame
        if kwargs['axis_onoff']: 
            self.plotMS.set_axis_on()
        else: 
            self.plotMS.set_axis_off()
            
        self.setup_zoom([self.plotMS], self.zoomtype, data_lims=extent)
        self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]
    
    def plot_2D_surface(self, zvals, xvals, yvals, xlabel, ylabel, 
                        legend=False, zoom='box',
                        axesSize=None, plotName=None, **kwargs):
        self.plotflag = True # Used only if saving data
        self.zoomtype = zoom
        self.plot_name = plotName
        
        # override parameters
        if not self.lock_plot_from_updating:
            if axesSize is not None:
                self._axes = axesSize
            self.plot_parameters = kwargs
            print(self._axes)
        else:
            kwargs = merge_two_dicts(kwargs, self.plot_parameters)
            self.plot_parameters = kwargs
        
        # set tick size
        matplotlib.rc('xtick', labelsize=kwargs['tick_size'])
        matplotlib.rc('ytick', labelsize=kwargs['tick_size'])      
        
        # Plot
        self.plotMS = self.figure.add_axes(self._axes)
        extent = self.extents(xvals)+self.extents(yvals)
        
        # Add imshow
        self.cax = self.plotMS.imshow(zvals, extent=extent,
                                      cmap=kwargs['colormap'],
                                      interpolation=kwargs['interpolation'],
                                      norm=kwargs['colormap_norm'], 
                                      aspect='auto', 
                                      origin='lower')
        xmin, xmax, ymin, ymax = extent
        self.plotMS.set_xlim(xmin, xmax-0.5)
        self.plotMS.set_ylim(ymin, ymax-0.5)
        
        # legend
        if legend:
            self.plotMS.legend(loc=kwargs.get('legend_position', self.config.legendPosition), 
                               ncol=kwargs.get('legend_num_columns', self.config.legendColumns),
                               fontsize=kwargs.get('legend_font_size', self.config.legendFontSize),
                               frameon=kwargs.get('legend_frame_on', self.config.legendFrame),
                               framealpha=kwargs.get('legend_transparency' ,self.config.legendAlpha),
                               markerfirst=kwargs.get('legend_marker_first', self.config.legendMarkerFirst),
                               markerscale=kwargs.get('legend_marker_size', self.config.legendMarkerSize),
                               fancybox=kwargs.get('legend_fancy_box', self.config.legendFancyBox),
                               scatterpoints=kwargs.get('legend_num_markers', self.config.legendNumberMarkers))
            leg = self.plotMS.axes.get_legend()
            leg.remove()
        # setup zoom
        extent = [xmin, ymin, xmax, ymax]
        self.setup_zoom([self.plotMS], self.zoomtype, data_lims=extent,
                        plotName=plotName)
        self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]
        
        
        # labels
        if xlabel in ['None', None, ""]: xlabel=''
        if ylabel in ['None', None, ""]: ylabel=''
        
        self.plotMS.set_xlabel(xlabel, 
                               labelpad=kwargs['label_pad'], 
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'])
        self.plotMS.set_ylabel(ylabel, 
                               labelpad=kwargs['label_pad'], 
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'])
        
        # setup colorbar
        if kwargs['colorbar']:
            cbarDivider = make_axes_locatable(self.plotMS)
            # pad controls how close colorbar is to the axes
            self.cbar = cbarDivider.append_axes(kwargs['colorbar_position'], 
                                          size="".join([str(kwargs['colorbar_width']), "%"]), 
                                          pad=kwargs['colorbar_pad'])

            tick_min = np.min(zvals)
            tick_max = np.max(zvals)
            tick_mid = np.median([tick_min + tick_max])
            ticks = [tick_min, tick_mid, tick_max]
            
            if plotName in ['RMSD', 'RMSF']:
                tick_labels = ["-100", "%", "100"]
                ticks = [-tick_max, 0, tick_max]
            else:
                tick_labels = ["0", "%", "100"]
            
            self.cbar.ticks = ticks
            self.cbar.tick_labels = tick_labels
            
            if kwargs['colorbar_position'] in ['left', 'right']:
                self.figure.colorbar(self.cax, cax=self.cbar, ticks=ticks, 
                                     orientation='vertical')
                self.cbar.yaxis.set_ticks_position(kwargs['colorbar_position'])
                self.cbar.set_yticklabels(tick_labels)
            else:
                self.figure.colorbar(self.cax, cax=self.cbar, ticks=ticks, orientation='horizontal')
                self.cbar.xaxis.set_ticks_position(kwargs['colorbar_position'])
                self.cbar.set_xticklabels(tick_labels)
                
            # setup other parameters
            self.cbar.tick_params(labelsize=kwargs['colorbar_label_size'])
            
        # ticks
        self.plotMS.tick_params(axis='both',  
                                left=kwargs['ticks_left'], 
                                right=kwargs['ticks_right'], 
                                top=kwargs['ticks_top'],
                                bottom=kwargs['ticks_bottom'],
                                labelleft=kwargs['tickLabels_left'],
                                labelright=kwargs['tickLabels_right'],
                                labeltop=kwargs['tickLabels_top'],
                                labelbottom=kwargs['tickLabels_bottom'])
        
        # spines
        self.plotMS.spines['left'].set_visible(kwargs['spines_left'])
        self.plotMS.spines['right'].set_visible(kwargs['spines_right'])
        self.plotMS.spines['top'].set_visible(kwargs['spines_top'])
        self.plotMS.spines['bottom'].set_visible(kwargs['spines_bottom'])
        [i.set_linewidth(kwargs['frame_width']) for i in self.plotMS.spines.itervalues()]
        
        # update axis frame
        if kwargs['axis_onoff']: 
            self.plotMS.set_axis_on()
        else: 
            self.plotMS.set_axis_off()
    
    def plot_2D_contour(self, zvals, xvals, yvals, xlabel, ylabel, 
                        legend=False, zoom='box',
                        axesSize=None, plotName=None, **kwargs):
        self.plotflag = True # Used only if saving data
        self.zoomtype = zoom
        self.plot_name = plotName
        
        # override parameters
        if not self.lock_plot_from_updating:
            if axesSize is not None:
                self._axes = axesSize
            self.plot_parameters = kwargs
        else:
            kwargs = merge_two_dicts(kwargs, self.plot_parameters)
            self.plot_parameters = kwargs
        
        # set tick size
        matplotlib.rc('xtick', labelsize=kwargs['tick_size'])
        matplotlib.rc('ytick', labelsize=kwargs['tick_size'])      
        
        # Plot
        self.plotMS = self.figure.add_axes(self._axes)

        extent = self.extents(xvals)+self.extents(yvals)
        
        # Add imshow
        self.cax = self.plotMS.contourf(zvals, 300, extent=extent, 
                                        cmap=kwargs['colormap'], 
                                        norm=kwargs['colormap_norm'], 
                                        antialiasing=True)
                
        xmin, xmax, ymin, ymax = extent
        self.plotMS.set_xlim(xmin, xmax-0.5)
        self.plotMS.set_ylim(ymin, ymax-0.5)

        # legend
        if legend:
            self.plotMS.legend(loc=kwargs.get('legend_position', self.config.legendPosition), 
                               ncol=kwargs.get('legend_num_columns', self.config.legendColumns),
                               fontsize=kwargs.get('legend_font_size', self.config.legendFontSize),
                               frameon=kwargs.get('legend_frame_on', self.config.legendFrame),
                               framealpha=kwargs.get('legend_transparency' ,self.config.legendAlpha),
                               markerfirst=kwargs.get('legend_marker_first', self.config.legendMarkerFirst),
                               markerscale=kwargs.get('legend_marker_size', self.config.legendMarkerSize),
                               fancybox=kwargs.get('legend_fancy_box', self.config.legendFancyBox),
                               scatterpoints=kwargs.get('legend_num_markers', self.config.legendNumberMarkers))
        # setup zoom
        extent = [xmin, ymin, xmax, ymax]
        self.setup_zoom([self.plotMS], self.zoomtype, data_lims=extent)
        self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]
        
        # labels
        if xlabel in ['None', None, ""]: xlabel=''
        if ylabel in ['None', None, ""]: ylabel=''
        
        self.plotMS.set_xlabel(xlabel, 
                               labelpad=kwargs['label_pad'], 
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'])
        self.plotMS.set_ylabel(ylabel, 
                               labelpad=kwargs['label_pad'], 
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'])
        
        # setup colorbar
        if kwargs['colorbar']:
            cbarDivider = make_axes_locatable(self.plotMS)
            # pad controls how close colorbar is to the axes
            self.cbar = cbarDivider.append_axes(kwargs['colorbar_position'], 
                                          size="".join([str(kwargs['colorbar_width']), "%"]), 
                                          pad=kwargs['colorbar_pad'])

            ticks = [np.min(zvals), (np.max(zvals)-np.min(zvals))/2, np.max(zvals)]
            if ticks[1] in [ticks[0], ticks[2]]: ticks[1] = 0
            
            self.cbar.ticks = ticks
#             self.cbar.tick_labels = tick_labels
            
            if kwargs['colorbar_position'] in ['left', 'right']:
                self.figure.colorbar(self.cax, cax=self.cbar, ticks=ticks, orientation='vertical')
                self.cbar.yaxis.set_ticks_position(kwargs['colorbar_position'])
                self.cbar.set_yticklabels(["0", "%", "100"])
            else:
                self.figure.colorbar(self.cax, cax=self.cbar, ticks=ticks, orientation='horizontal')
                self.cbar.xaxis.set_ticks_position(kwargs['colorbar_position'])
                self.cbar.set_xticklabels(["0", "%", "100"])
            
            # setup other parameters
            self.cbar.tick_params(labelsize=kwargs['colorbar_label_size'])
            
        # ticks
        self.plotMS.tick_params(axis='both',  
                                left=kwargs['ticks_left'], 
                                right=kwargs['ticks_right'], 
                                top=kwargs['ticks_top'],
                                bottom=kwargs['ticks_bottom'],
                                labelleft=kwargs['tickLabels_left'],
                                labelright=kwargs['tickLabels_right'],
                                labeltop=kwargs['tickLabels_top'],
                                labelbottom=kwargs['tickLabels_bottom'])
        
        # spines
        self.plotMS.spines['left'].set_visible(kwargs['spines_left'])
        self.plotMS.spines['right'].set_visible(kwargs['spines_right'])
        self.plotMS.spines['top'].set_visible(kwargs['spines_top'])
        self.plotMS.spines['bottom'].set_visible(kwargs['spines_bottom'])
        [i.set_linewidth(kwargs['frame_width']) for i in self.plotMS.spines.itervalues()]
        
        # update axis frame
        if kwargs['axis_onoff']: 
            self.plotMS.set_axis_on()
        else: 
            self.plotMS.set_axis_off()
    
    def plot_2D_contour_unidec(self, data=None, zvals=None, xvals=None, yvals=None, 
                               xlabel="m/z (Da)", ylabel="Charge", legend=False, 
                               speedy=True, zoom='box', axesSize=None, plotName=None, 
                               testX=False, title="", **kwargs):
        self.plotflag = True # Used only if saving data
        self.zoomtype = zoom
        self.plot_name = plotName
        
        # override parameters
        if not self.lock_plot_from_updating:
            if axesSize is not None:
                self._axes = axesSize
            self.plot_parameters = kwargs
        else:
            kwargs = merge_two_dicts(kwargs, self.plot_parameters)
            self.plot_parameters = kwargs
        
        # set tick size
        matplotlib.rc('xtick', labelsize=kwargs['tick_size'])
        matplotlib.rc('ytick', labelsize=kwargs['tick_size'])      
        
        # prep data
        if xvals is None or yvals is None or zvals is None:
            zvals = data[:, 2]
            xvals = np.unique(data[:, 0])
            yvals = np.unique(data[:, 1])
        xlen = len(xvals)
        ylen = len(yvals)
        zvals = np.reshape(zvals, (xlen, ylen))

        # normalize grid
        norm = cm.colors.Normalize(vmax=np.amax(zvals), vmin=np.amin(zvals))
        
        # Plot
        self.plotMS = self.figure.add_axes(self._axes)

        if testX:
            xvals, xlabel, __ = self.kda_test(xvals)
    
        extent = self.extents(xvals)+self.extents(yvals)
        
        if not speedy:
            self.cax = self.plotMS.contourf(xvals, yvals, np.transpose(zvals), 
                                            100, cmap=kwargs['colormap'], 
                                            norm=norm)
        else:
            self.cax = self.plotMS.imshow(np.transpose(zvals), extent=extent,
                                          cmap=kwargs['colormap'],
                                          interpolation=kwargs['interpolation'],
                                          norm=norm, 
                                          aspect='auto', 
                                          origin='lower')
            
#             if 'colormap_norm' in kwargs:
#                 self.cax.set_norm(kwargs['colormap_norm'])
                    
        xmin, xmax = self.plotMS.get_xlim()
        ymin, ymax = self.plotMS.get_ylim()
        self.plotMS.set_xlim(xmin, xmax-0.5)
        self.plotMS.set_ylim(ymin, ymax-0.5)
                
        if kwargs.get('minor_ticks_off', True):
            self.plotMS.yaxis.set_tick_params(which='minor', bottom='off')
            self.plotMS.yaxis.set_major_locator(MaxNLocator(integer=True))
        
        # labels
        if xlabel in ['None', None, ""]: xlabel=''
        if ylabel in ['None', None, ""]: ylabel=''
        
        self.plotMS.set_xlabel(xlabel, 
                               labelpad=kwargs['label_pad'], 
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'])
        self.plotMS.set_ylabel(ylabel, 
                               labelpad=kwargs['label_pad'], 
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'])
        
        cbarDivider = make_axes_locatable(self.plotMS)
        # setup colorbar
        if kwargs['colorbar']:
            # pad controls how close colorbar is to the axes
            self.cbar = cbarDivider.append_axes(kwargs['colorbar_position'], 
                                          size="".join([str(kwargs['colorbar_width']), "%"]), 
                                          pad=kwargs['colorbar_pad'])
 
            ticks = [np.min(zvals), (np.max(zvals)-np.min(zvals))/2, np.max(zvals)]
            if ticks[1] in [ticks[0], ticks[2]]: ticks[1] = 0
             
            tick_labels = ["0", "%", "100"]
             
            self.cbar.ticks = ticks
            self.cbar.tick_labels = tick_labels
             
            if kwargs['colorbar_position'] in ['left', 'right']:
                self.figure.colorbar(self.cax, cax=self.cbar, ticks=ticks, orientation='vertical')
                self.cbar.yaxis.set_ticks_position(kwargs['colorbar_position'])
                self.cbar.set_yticklabels(tick_labels)
            else:
                self.figure.colorbar(self.cax, cax=self.cbar, ticks=ticks, orientation='horizontal')
                self.cbar.xaxis.set_ticks_position(kwargs['colorbar_position'])
                self.cbar.set_xticklabels(tick_labels)
                 
            # setup other parameters
            self.cbar.tick_params(labelsize=kwargs['colorbar_label_size'])
            
        # ticks
        self.plotMS.tick_params(axis='both',  
                                left=kwargs['ticks_left'], 
                                right=kwargs['ticks_right'], 
                                top=kwargs['ticks_top'],
                                bottom=kwargs['ticks_bottom'],
                                labelleft=kwargs['tickLabels_left'],
                                labelright=kwargs['tickLabels_right'],
                                labeltop=kwargs['tickLabels_top'],
                                labelbottom=kwargs['tickLabels_bottom'])
        
        # spines
        self.plotMS.spines['left'].set_visible(kwargs['spines_left'])
        self.plotMS.spines['right'].set_visible(kwargs['spines_right'])
        self.plotMS.spines['top'].set_visible(kwargs['spines_top'])
        self.plotMS.spines['bottom'].set_visible(kwargs['spines_bottom'])
        [i.set_linewidth(kwargs['frame_width']) for i in self.plotMS.spines.itervalues()]
        
        # update axis frame
        if kwargs['axis_onoff']: 
            self.plotMS.set_axis_on()
        else: 
            self.plotMS.set_axis_off()
        
        if title != "": 
            if kwargs['title_weight']: title_weight = "heavy"
            else: title_weight = "normal"
            self.plotMS.set_title(title,
                                  fontsize=kwargs['title_size'], 
                                  weight=title_weight)
            
        # setup zoom
        extent = [xmin, ymin, xmax, ymax]
        self.setup_zoom([self.plotMS], self.zoomtype, data_lims=extent,
                        plotName=plotName, allowWheel=False)
        self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]
        self.plot_data = {'xvals':xvals, 'yvals':yvals, 'zvals':zvals,
                          'xlabel':xlabel, 'ylabel':ylabel}
        
    def plot_2D_rgb(self, zvals, xvals, yvals, xlabel, ylabel, 
                    zoom="box", axesSize=None, legend_text=None,
                    plotName='RGB', **kwargs):
        self.plotflag = True # Used only if saving data
        self.zoomtype = zoom
        self.plot_name = plotName
        
        # override parameters
        if not self.lock_plot_from_updating:
            if axesSize is not None:
                self._axes = axesSize
            self.plot_parameters = kwargs
        else:
            kwargs = merge_two_dicts(kwargs, self.plot_parameters)
            self.plot_parameters = kwargs
        
        matplotlib.rc('xtick', labelsize=kwargs['tick_size'])
        matplotlib.rc('ytick', labelsize=kwargs['tick_size'])
                        
        # Plot
        self.plotMS = self.figure.add_axes(self._axes)
        
        handles = []
        if legend_text != None:
            for i in range(len(legend_text)):
                handles.append(patches.Patch(color=legend_text[i][0], 
                                             label=legend_text[i][1], 
                                             alpha=kwargs['legend_patch_transparency']))

        extent = self.extents(xvals)+self.extents(yvals)

        # Add imshow
        self.cax = self.plotMS.imshow(zvals, extent=extent,
                                      interpolation=kwargs['interpolation'],
                                      origin='lower',
                                      aspect='auto')
        
        xmin, xmax = self.plotMS.get_xlim()
        ymin, ymax = self.plotMS.get_ylim()
        self.plotMS.set_xlim(xmin, xmax-0.5)
        self.plotMS.set_ylim(ymin, ymax-0.5)
        extent = [xmin, ymin, xmax, ymax]

        # legend
        if kwargs.get('legend', self.config.legend):
            self.plotMS.legend(loc=kwargs.get('legend_position', self.config.legendPosition), 
                               ncol=kwargs.get('legend_num_columns', self.config.legendColumns),
                               fontsize=kwargs.get('legend_font_size', self.config.legendFontSize),
                               frameon=kwargs.get('legend_frame_on', self.config.legendFrame),
                               framealpha=kwargs.get('legend_transparency' ,self.config.legendAlpha),
                               markerfirst=kwargs.get('legend_marker_first', self.config.legendMarkerFirst),
                               markerscale=kwargs.get('legend_marker_size', self.config.legendMarkerSize),
                               fancybox=kwargs.get('legend_fancy_box', self.config.legendFancyBox),
                               scatterpoints=kwargs.get('legend_num_markers', self.config.legendNumberMarkers),
                               handles=handles)
            
            leg = self.plotMS.axes.get_legend()
            leg.draggable()

        
        self.plotMS.set_xlabel(xlabel, 
                               labelpad=kwargs['label_pad'], 
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'])
        self.plotMS.set_ylabel(ylabel, 
                               labelpad=kwargs['label_pad'], 
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'])
        
        # ticks
        self.plotMS.tick_params(axis='both',  
                                left=kwargs['ticks_left'], 
                                right=kwargs['ticks_right'], 
                                top=kwargs['ticks_top'],
                                bottom=kwargs['ticks_bottom'],
                                labelleft=kwargs['tickLabels_left'],
                                labelright=kwargs['tickLabels_right'],
                                labeltop=kwargs['tickLabels_top'],
                                labelbottom=kwargs['tickLabels_bottom'])
        
        # spines
        self.plotMS.spines['left'].set_visible(kwargs['spines_left'])
        self.plotMS.spines['right'].set_visible(kwargs['spines_right'])
        self.plotMS.spines['top'].set_visible(kwargs['spines_top'])
        self.plotMS.spines['bottom'].set_visible(kwargs['spines_bottom'])
        [i.set_linewidth(kwargs['frame_width']) for i in self.plotMS.spines.itervalues()]
        
        # update axis frame
        if kwargs['axis_onoff']: 
            self.plotMS.set_axis_on()
        else: 
            self.plotMS.set_axis_off()
            
        self.setup_zoom([self.plotMS], self.zoomtype, data_lims=extent) 
        self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]

    def plot_2D_matrix(self, zvals=None, xylabels=None, xNames=None, zoom="box", 
                       axesSize=None, plotName=None, **kwargs):
        
        self.plotflag = True # Used only if saving data
        self.zoomtype = zoom
        self.plot_name = plotName
        
        # override parameters
        if not self.lock_plot_from_updating:
            if axesSize is not None:
                self._axes = axesSize
            self.plot_parameters = kwargs
        else:
            kwargs = merge_two_dicts(kwargs, self.plot_parameters)
            self.plot_parameters = kwargs
        
        matplotlib.rc('xtick', labelsize=kwargs['tick_size'])
        matplotlib.rc('ytick', labelsize=kwargs['tick_size'])
                        
        # Plot
        self.plotMS = self.figure.add_axes(self._axes)
                
        # Setup labels 
        xsize = len(zvals)
        if xylabels:
            self.plotMS.set_xticks(np.arange(1,xsize+1,1))
            self.plotMS.set_xticklabels(xylabels, 
                                        rotation=kwargs['rmsd_matrix_rotX'])
            self.plotMS.set_yticks(np.arange(1,xsize+1,1))
            self.plotMS.set_yticklabels(xylabels, 
                                        rotation=kwargs['rmsd_matrix_rotY'])
            
        extent=[0.5, xsize+0.5 , 0.5, xsize+0.5]

        # Add imshow
        self.cax = self.plotMS.imshow(zvals, 
                                      cmap=kwargs['colormap'], 
                                      interpolation=kwargs['interpolation'],
                                      aspect='auto', 
                                      extent=extent,
                                      origin='lower')
                
        xmin, xmax = self.plotMS.get_xlim()
        ymin, ymax = self.plotMS.get_ylim()
        self.plotMS.set_xlim(xmin, xmax-0.5)
        self.plotMS.set_ylim(ymin, ymax-0.5)
        extent = [xmin, ymin, xmax, ymax]
        
        # add labels
        self.text = []
        if kwargs['rmsd_matrix_labels']:
            thresh = zvals.max() / 2.
            cmap = self.cax.get_cmap()
            color = determineFontColor(convertRGB1to255(cmap(thresh)))
            for i, j in itertools.product(range(zvals.shape[0]), range(zvals.shape[1])):
                color = determineFontColor(convertRGB1to255(cmap(zvals[i, j]/2)))
                label = format(zvals[i, j], '.2f')
                text = self.plotMS.text(j+1, i+1, label,
                                        horizontalalignment="center",
                                        color=color)
                self.text.append(text)

        cbarDivider = make_axes_locatable(self.plotMS)
        
        try:
            handles, __ = self.plotMS.get_legend_handles_labels()
            if len(handles) > 0:
                # legend
                if kwargs.get('legend', self.config.legend):
                    self.plotMS.legend(loc=kwargs.get('legend_position', self.config.legendPosition), 
                                       ncol=kwargs.get('legend_num_columns', self.config.legendColumns),
                                       fontsize=kwargs.get('legend_font_size', self.config.legendFontSize),
                                       frameon=kwargs.get('legend_frame_on', self.config.legendFrame),
                                       framealpha=kwargs.get('legend_transparency' ,self.config.legendAlpha),
                                       markerfirst=kwargs.get('legend_marker_first', self.config.legendMarkerFirst),
                                       markerscale=kwargs.get('legend_marker_size', self.config.legendMarkerSize),
                                       fancybox=kwargs.get('legend_fancy_box', self.config.legendFancyBox),
                                       scatterpoints=kwargs.get('legend_num_markers', self.config.legendNumberMarkers))
        except: 
            pass
     
        # setup colorbar
        if kwargs['colorbar']:
            # pad controls how close colorbar is to the axes
            self.cbar = cbarDivider.append_axes(kwargs['colorbar_position'], 
                                          size="".join([str(kwargs['colorbar_width']), "%"]), 
                                          pad=kwargs['colorbar_pad'])

            ticks = [np.min(zvals), (np.max(zvals)-np.min(zvals))/2, np.max(zvals)]
            tick_labels = ["0", "%", "100"]
            
            self.cbar.ticks = ticks
            self.cbar.tick_labels = tick_labels
            
            if kwargs['colorbar_position'] in ['left', 'right']:
                self.figure.colorbar(self.cax, cax=self.cbar, ticks=ticks, orientation='vertical')
                self.cbar.yaxis.set_ticks_position(kwargs['colorbar_position'])
                self.cbar.set_yticklabels(tick_labels)
            else:
                self.figure.colorbar(self.cax, cax=self.cbar, ticks=ticks, orientation='horizontal')
                self.cbar.xaxis.set_ticks_position(kwargs['colorbar_position'])
                self.cbar.set_xticklabels(tick_labels)
            
            # setup other parameters
            self.cbar.tick_params(labelsize=kwargs['colorbar_label_size'])
            
            
        # ticks
        self.plotMS.tick_params(axis='both',  
                                left=kwargs['ticks_left'], right=kwargs['ticks_right'], 
                                top=kwargs['ticks_top'], bottom=kwargs['ticks_bottom'],
                                labelleft=kwargs['tickLabels_left'], labelright=kwargs['tickLabels_right'],
                                labeltop=kwargs['tickLabels_top'], labelbottom=kwargs['tickLabels_bottom'])
         
        # spines
        self.plotMS.spines['left'].set_visible(kwargs['spines_left'])
        self.plotMS.spines['right'].set_visible(kwargs['spines_right'])
        self.plotMS.spines['top'].set_visible(kwargs['spines_top'])
        self.plotMS.spines['bottom'].set_visible(kwargs['spines_bottom'])
        [i.set_linewidth(kwargs['frame_width']) for i in self.plotMS.spines.itervalues()]
         
        # update axis frame
        if kwargs['axis_onoff']: 
            self.plotMS.set_axis_on()
        else: 
            self.plotMS.set_axis_off()
            
        # setup zoom
        self.setup_zoom([self.plotMS], self.zoomtype, data_lims=extent, 
                        plotName=plotName)
        self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]
                        
    #-----

    def plot_2D_overlay(self, zvalsIon1=None, zvalsIon2=None, cmapIon1='Reds',
                        cmapIon2='Greens', alphaIon1=1, alphaIon2=1, 
                        labelsX=None, labelsY=None, xlabel="", ylabel="", 
                        zoom="box",  axesSize=None, plotName=None, **kwargs):
        
        self.plotflag = True # Used only if saving data
        self.zoomtype = zoom
        self.plot_name = plotName
        
        # override parameters
        if not self.lock_plot_from_updating:
            if axesSize is not None:
                self._axes = axesSize
            self.plot_parameters = kwargs
        else:
            kwargs = merge_two_dicts(kwargs, self.plot_parameters)
            self.plot_parameters = kwargs

        # set tick size
        matplotlib.rc('xtick', labelsize=kwargs['tick_size'])
        matplotlib.rc('ytick', labelsize=kwargs['tick_size'])      
        
        # Plot
        self.plotMS = self.figure.add_axes(self._axes)

        extent = self.extents(labelsX)+self.extents(labelsY)
        
        # Add imshow
        self.cax = self.plotMS.imshow(zvalsIon1, extent=extent,
                                      cmap=cmapIon1, 
                                      interpolation=kwargs['interpolation'],
                                      aspect='auto', origin='lower',
                                      alpha=alphaIon1)
        plotMS2 = self.plotMS.imshow(zvalsIon2, extent=extent,
                                     cmap=cmapIon2, 
                                     interpolation=kwargs['interpolation'],
                                     aspect='auto', origin='lower',
                                     alpha=alphaIon2)
                
        xmin, xmax = self.plotMS.get_xlim()
        ymin, ymax = self.plotMS.get_ylim()
        self.plotMS.set_xlim(xmin, xmax-0.5)
        self.plotMS.set_ylim(ymin, ymax-0.5)
                
        # legend
        if kwargs.get('legend', self.config.legend):
            self.plotMS.legend(loc=kwargs.get('legend_position', self.config.legendPosition), 
                               ncol=kwargs.get('legend_num_columns', self.config.legendColumns),
                               fontsize=kwargs.get('legend_font_size', self.config.legendFontSize),
                               frameon=kwargs.get('legend_frame_on', self.config.legendFrame),
                               framealpha=kwargs.get('legend_transparency' ,self.config.legendAlpha),
                               markerfirst=kwargs.get('legend_marker_first', self.config.legendMarkerFirst),
                               markerscale=kwargs.get('legend_marker_size', self.config.legendMarkerSize),
                               fancybox=kwargs.get('legend_fancy_box', self.config.legendFancyBox),
                               scatterpoints=kwargs.get('legend_num_markers', self.config.legendNumberMarkers))
        # setup zoom
        extent = [xmin, ymin, xmax, ymax]
        self.setup_zoom([self.plotMS], self.zoomtype, data_lims=extent,
                        plotName=plotName)
        self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]
        
        # labels
        if xlabel in ['None', None, ""]: xlabel=''
        if ylabel in ['None', None, ""]: ylabel=''
        
        self.plotMS.set_xlabel(xlabel, 
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'])
        self.plotMS.set_ylabel(ylabel, 
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'])
            
        # ticks
        self.plotMS.tick_params(axis='both',  
                                left=kwargs['ticks_left'], 
                                right=kwargs['ticks_right'], 
                                top=kwargs['ticks_top'],
                                bottom=kwargs['ticks_bottom'],
                                labelleft=kwargs['tickLabels_left'],
                                labelright=kwargs['tickLabels_right'],
                                labeltop=kwargs['tickLabels_top'],
                                labelbottom=kwargs['tickLabels_bottom'])
        
        # spines
        self.plotMS.spines['left'].set_visible(kwargs['spines_left'])
        self.plotMS.spines['right'].set_visible(kwargs['spines_right'])
        self.plotMS.spines['top'].set_visible(kwargs['spines_top'])
        self.plotMS.spines['bottom'].set_visible(kwargs['spines_bottom'])
        [i.set_linewidth(kwargs['frame_width']) for i in self.plotMS.spines.itervalues()]

        # update axis frame
        if kwargs['axis_onoff']: 
            self.plotMS.set_axis_on()
        else: 
            self.plotMS.set_axis_off()

    def plot_3D_bar(self, xvals=None, yvals=None, zvals=None, xylabels=None,
                    cmap='inferno', title="", xlabel="", ylabel="", zlabel="", 
                    label="", axesSize=None, plotType="Bar", **kwargs):
        if axesSize is not None:
            self._axes = axesSize
        self.plot_parameters = kwargs
        self.plot_name = plotType
        
        xvals = range(zvals.shape[1])
        yvals = range(zvals.shape[0])
        xvals, yvals = meshgrid(xvals, yvals)
        
        x, y = xvals.ravel(), yvals.ravel()
        top = zvals.ravel()
        bottom = zeros_like(top)
        width = depth = 1
        
#         # colormap check
#         if kwargs['colormap'] in self.config.cmocean_cmaps:
#             kwargs['colormap'] = eval("cmocean.cm.%s" % kwargs['colormap'])
        
        cmap = cm.get_cmap(kwargs['colormap']) # Get desired colormap
        max_height = np.max(top)   # get range of colorbars
        min_height = np.min(top)
        
        # scale each z to [0,1], and get their rgb values
        rgba = [cmap((k-min_height)/max_height) for k in top] 
        
        self.plotMS = self.figure.add_subplot(111, projection='3d', aspect='auto')
        self.plotMS.mouse_init(rotate_btn=1, zoom_btn=2)
        self.plotMS.bar3d(x, y, bottom, width, depth, top, color=rgba,
                          zsort='average', picker=1)
        
        # update labels
        self.plotMS.set_xlabel(self.plotMS.get_xlabel(), 
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'])
        self.plotMS.set_ylabel(self.plotMS.get_ylabel(),
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'])
        
        # Setup font size info
        self.plotMS.tick_params(labelsize=kwargs['tick_size'])

        self.plotMS.w_xaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        self.plotMS.w_yaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        self.plotMS.w_zaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        
        # Get rid of spines
        if not kwargs['show_spines']:
            self.plotMS.w_xaxis.line.set_color((1.0, 1.0, 1.0, 0.0))
            self.plotMS.w_yaxis.line.set_color((1.0, 1.0, 1.0, 0.0))
            self.plotMS.w_zaxis.line.set_color((1.0, 1.0, 1.0, 0.0))
        
        # Setup labels 
        xsize = len(zvals)
        if xylabels:
            self.plotMS.set_xticks(np.arange(1,xsize+1,1)-0.5)
            self.plotMS.set_xticklabels(xylabels, 
                                        rotation=kwargs['rmsd_matrix_rotX']
                                        )
            self.plotMS.set_yticks(np.arange(1,xsize+1,1)-0.5)
            self.plotMS.set_yticklabels(xylabels, 
                                        rotation=kwargs['rmsd_matrix_rotY']
                                        )
        
        # Get rid of the ticks
        if not kwargs['show_ticks']:
            self.plotMS.set_xticks([]) 
            self.plotMS.set_yticks([]) 
            self.plotMS.set_zticks([])

        # update labels
        self.plotMS.set_xlabel(xlabel, 
                               labelpad=kwargs['label_pad'], 
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'],
                               visible=kwargs['show_labels'])
        self.plotMS.set_ylabel(ylabel, 
                               labelpad=kwargs['label_pad'], 
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'],
                               visible=kwargs['show_labels'])
        self.plotMS.set_zlabel(zlabel, 
                               labelpad=kwargs['label_pad'], 
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'],
                               visible=kwargs['show_labels'])
        self.plotMS.grid(kwargs['grid'])
               
        self.plotMS.set_xlim([0,len(xvals)])
        self.plotMS.set_ylim([0,len(yvals)])
        self.plotMS.set_zlim([min(zvals), max(zvals)])
        
        self.plotMS.set_position(axesSize)
        
    def plot_3D_surface(self, xvals=None, yvals=None, zvals=None, colors=None, 
                        xlabel=None, ylabel=None, zlabel=None, plotName='whole',
                        axesSize=None, plotType="Surface3D", **kwargs):
        if axesSize is not None:
            self._axes = axesSize
        self.plotflag = True # Used only if saving data
        self.plot_parameters = kwargs
        self.plot_name = plotType

        xvals, yvals = meshgrid(xvals, yvals)
        
        ydivider, expo = self.testXYmaxValsUpdated(values=zvals)
        if expo > 1:
            offset_text = r'x$\mathregular{10^{%d}}$' %expo
            zlabel = ''.join([zlabel, " [", offset_text,"]"])
            zvals = divide(zvals, float(ydivider))
        
        
        matplotlib.rc('xtick', labelsize=kwargs['tick_size'])
        matplotlib.rc('ytick', labelsize=kwargs['tick_size'])  
                                                      
        self.plotMS = self.figure.add_subplot(111, projection='3d', aspect='auto')
        self.plotMS.mouse_init(rotate_btn=1, zoom_btn=2)
        self.cax = self.plotMS.plot_surface(xvals, yvals, zvals, 
                                            cmap=kwargs['colormap'], 
                                            antialiased=True,
                                            shade=kwargs['shade'],
                                            picker=1)
        
        # update labels
        self.plotMS.set_xlabel(self.plotMS.get_xlabel(), 
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'])
        self.plotMS.set_ylabel(self.plotMS.get_ylabel(),
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'])
        
        # Setup font size info
        self.plotMS.tick_params(labelsize=kwargs['tick_size'])

        self.plotMS.w_xaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        self.plotMS.w_yaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        self.plotMS.w_zaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        
        # Get rid of spines
        if not kwargs['show_spines']:
            self.plotMS.w_xaxis.line.set_color((1.0, 1.0, 1.0, 0.0))
            self.plotMS.w_yaxis.line.set_color((1.0, 1.0, 1.0, 0.0))
            self.plotMS.w_zaxis.line.set_color((1.0, 1.0, 1.0, 0.0))
        
        # Get rid of the ticks
        if not kwargs['show_ticks']:
            self.plotMS.set_xticks([]) 
            self.plotMS.set_yticks([]) 
            self.plotMS.set_zticks([])

        # update labels
        self.plotMS.set_xlabel(xlabel, 
                               labelpad=kwargs['label_pad'], 
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'],
                               visible=kwargs['show_labels'])
        self.plotMS.set_ylabel(ylabel, 
                               labelpad=kwargs['label_pad'], 
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'],
                               visible=kwargs['show_labels'])
        self.plotMS.set_zlabel(zlabel, 
                               labelpad=kwargs['label_pad'], 
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'],
                               visible=kwargs['show_labels'])
        
        self.plotMS.grid(kwargs['grid'])
               
        
        self.plotMS.set_xlim([min(xvals),max(xvals)])
        self.plotMS.set_ylim([min(yvals),max(yvals)])
        self.plotMS.set_zlim([min(zvals),max(zvals)])
        
        self.plotMS.set_position(axesSize)
        
    def plot_3D_wireframe(self, xvals=None, yvals=None, zvals=None, colors=None, 
                        xlabel=None, ylabel=None, zlabel=None, plotName='whole',
                        axesSize=None, plotType="Wireframe3D", **kwargs):
        if axesSize is not None:
            self._axes = axesSize
        self.plotflag = True # Used only if saving data
        self.plot_parameters = kwargs
        self.plot_name = plotType

        xvals, yvals = meshgrid(xvals, yvals)
        
        ydivider, expo = self.testXYmaxValsUpdated(values=zvals)
        if expo > 1:
            offset_text = r'x$\mathregular{10^{%d}}$' %expo
            zlabel = ''.join([zlabel, " [", offset_text,"]"])
            zvals = divide(zvals, float(ydivider))
        
        
        matplotlib.rc('xtick', labelsize=kwargs['tick_size'])
        matplotlib.rc('ytick', labelsize=kwargs['tick_size'])  
                           
#         # colormap check
#         if kwargs['colormap'] in self.config.cmocean_cmaps:
#             kwargs['colormap'] = eval("cmocean.cm.%s" % kwargs['colormap'])
                           
        self.plotMS = self.figure.add_subplot(111, projection='3d', aspect='auto')
        self.plotMS.mouse_init(rotate_btn=1, zoom_btn=2)
        self.plotMS.plot_wireframe(xvals, yvals, zvals, 
                                   color=kwargs['line_color'],
                                   linewidth=kwargs['line_width'],
                                   linestyle=kwargs['line_style'],
                                    antialiased=False,
                                 )
        
        # update labels
        self.plotMS.set_xlabel(self.plotMS.get_xlabel(), 
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'])
        self.plotMS.set_ylabel(self.plotMS.get_ylabel(),
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'])
        
        # Setup font size info
        self.plotMS.tick_params(labelsize=kwargs['tick_size'])

        self.plotMS.w_xaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        self.plotMS.w_yaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        self.plotMS.w_zaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        
        # Get rid of spines
        if not kwargs['show_spines']:
            self.plotMS.w_xaxis.line.set_color((1.0, 1.0, 1.0, 0.0))
            self.plotMS.w_yaxis.line.set_color((1.0, 1.0, 1.0, 0.0))
            self.plotMS.w_zaxis.line.set_color((1.0, 1.0, 1.0, 0.0))
        else:
            self.plotMS.w_xaxis.line.set_color((0.0, 0.0, 0.0, 0.0))
            self.plotMS.w_yaxis.line.set_color((0.0, 0.0, 0.0, 0.0))
            self.plotMS.w_zaxis.line.set_color((0.0, 0.0, 0.0, 0.0))
        
        # Get rid of the ticks
        if not kwargs['show_ticks']:
            self.plotMS.set_xticks([]) 
            self.plotMS.set_yticks([]) 
            self.plotMS.set_zticks([])

        # update labels
        self.plotMS.set_xlabel(xlabel, 
                               labelpad=kwargs['label_pad'], 
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'],
                               visible=kwargs['show_labels'])
        self.plotMS.set_ylabel(ylabel, 
                               labelpad=kwargs['label_pad'], 
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'],
                               visible=kwargs['show_labels'])
        self.plotMS.set_zlabel(zlabel, 
                               labelpad=kwargs['label_pad'], 
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'],
                               visible=kwargs['show_labels'])
        
        self.plotMS.grid(kwargs['grid'])
               
        
        self.plotMS.set_xlim([min(xvals),max(xvals)])
        self.plotMS.set_ylim([min(yvals),max(yvals)])
        self.plotMS.set_zlim([min(zvals),max(zvals)])
        
        self.plotMS.set_position(axesSize)
        
    def plot_3D_scatter(self, xvals=None, yvals=None, zvals=None, colors=None, 
                        xlabel=None, ylabel=None, zlabel=None, plotName='whole',
                        axesSize=None, plotType="Scatter3D", **kwargs):
        if axesSize is not None:
            self._axes = axesSize
        self.plotflag = True # Used only if saving data
        self.plot_parameters = kwargs
        self.plot_name = plotType
        
        matplotlib.rc('xtick', labelsize=kwargs['tick_size'])
        matplotlib.rc('ytick', labelsize=kwargs['tick_size'])  
                           
        self.plotMS = self.figure.add_subplot(111, projection='3d', aspect='auto')
        if colors != None:
            self.plotMS.scatter(xvals, yvals, zvals, 
                                c=colors, 
                                edgecolor=colors, 
                                marker=kwargs['scatter_shape'],
                                alpha=kwargs['scatter_alpha'],
                                s=kwargs['scatter_size'],
                                depthshade=kwargs['shade'])
        else:
            self.plotMS.scatter(xvals, yvals, zvals, 
                                c=kwargs['scatter_color'], 
                                edgecolor=kwargs['scatter_edge_color'], 
                                marker=kwargs['scatter_shape'],
                                alpha=kwargs['scatter_alpha'],
                                s=kwargs['scatter_size'],
                                depthshade=kwargs['shade'])
               
        # update labels
        self.plotMS.set_xlabel(self.plotMS.get_xlabel(), 
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'])
        self.plotMS.set_ylabel(self.plotMS.get_ylabel(),
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'])
        
        # Setup font size info
        self.plotMS.tick_params(labelsize=kwargs['tick_size'])

        self.plotMS.w_xaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        self.plotMS.w_yaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        self.plotMS.w_zaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        
        # Get rid of spines
        if not kwargs['show_spines']:
            self.plotMS.w_xaxis.line.set_color((1.0, 1.0, 1.0, 0.0))
            self.plotMS.w_yaxis.line.set_color((1.0, 1.0, 1.0, 0.0))
            self.plotMS.w_zaxis.line.set_color((1.0, 1.0, 1.0, 0.0))
        
        # Get rid of the ticks
        if not kwargs['show_ticks']:
            self.plotMS.set_xticks([]) 
            self.plotMS.set_yticks([]) 
            self.plotMS.set_zticks([])

        # update labels
        self.plotMS.set_xlabel(xlabel, 
                               labelpad=kwargs['label_pad'], 
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'],
                               visible=kwargs['show_labels'])
        self.plotMS.set_ylabel(ylabel, 
                               labelpad=kwargs['label_pad'], 
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'],
                               visible=kwargs['show_labels'])
        self.plotMS.set_zlabel(zlabel, 
                               labelpad=kwargs['label_pad'], 
                               fontsize=kwargs['label_size'], 
                               weight=kwargs['label_weight'],
                               visible=kwargs['show_labels'])
        
        self.plotMS.grid(kwargs['grid'])
               
        
        self.plotMS.set_xlim([min(xvals),max(xvals)])
        self.plotMS.set_ylim([min(yvals),max(yvals)])
        self.plotMS.set_zlim([min(zvals),max(zvals)])

    #----

 
       
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

 
# from traits.api import HasTraits, Instance
# from traitsui.api import View, Item
# from mayavi.core.ui.api import SceneEditor, MlabSceneModel
#  
# from traits.etsconfig.api import ETSConfig
# ETSConfig.toolkit = 'wx'
#  
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
#           
#     def surface(self, xvals, yvals, zvals, cmap):
#         self.scene.mlab.clf()
#         self.plot = self.scene.mlab.surf(zvals, warp_scale="auto")