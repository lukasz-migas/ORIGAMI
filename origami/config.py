# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
#    Copyright (C) 2017-2018 Lukasz G. Migas
#    <lukasz.migas@manchester.ac.uk> OR <lukas.migas@yahoo.com>
#
# 	 GitHub : https://github.com/lukasz-migas/ORIGAMI
# 	 University of Manchester IP : https://www.click2go.umip.com/i/s_w/ORIGAMI.html
# 	 Cite : 10.1016/j.ijms.2017.08.014
#
#    This program is free software. Feel free to redistribute it and/or
#    modify it under the condition you cite and credit the authors whenever
#    appropriate.
#    The program is distributed in the hope that it will be useful but is
#    provided WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE
# -------------------------------------------------------------------------
# __author__ lukasz.g.migas

import glob
import os.path
import platform
import xml.dom.minidom
import xml.parsers.expat
from ast import literal_eval
from collections import OrderedDict

import numpy as np
from matplotlib.pyplot import colormaps

from gui_elements.misc_dialogs import dlgBox
from utils.converters import str2num, str2int, str2bool

import logging
logger = logging.getLogger("origami")


class OrigamiConfig:

    def __init__(self):
        """
        Initilize config
        """

        self._processID = None
        self.loggingFile_path = None
        self.version = "1.3.0.0"
        self.debug = True

        self.document_version = "19-10-2018"
        self.unidec_engine = None
        self.links = {
            'home' : 'https://www.click2go.umip.com/i/s_w/ORIGAMI.html',
            'github' : 'https://github.com/lukasz-migas/ORIGAMI',
            'cite' : 'https://doi.org/10.1016/j.ijms.2017.08.014',
            'newVersion' : 'https://github.com/lukasz-migas/ORIGAMI/releases',
            'guide': 'https://origami.lukasz-migas.com/',
            'youtube':'https://www.youtube.com/playlist?list=PLrPB7zfH4WXMYa5CN9qDtl-G-Ax_L6AK8',
            'htmlEditor':'https://html-online.com/editor/',
            'newFeatures':'https://docs.google.com/forms/d/e/1FAIpQLSduN15jzq06QCaacliBg8GkOajDNjWn4cEu_1J-kBhXSKqMHQ/viewform',
            'reportBugs':'https://docs.google.com/forms/d/e/1FAIpQLSf7Ahgvt-YFRrA61Pv1S4i8nBK6wfhOpD2O9lGt_E3IA0lhfQ/viewform',
            'unidec_cite_1':'https://pubs.acs.org/doi/abs/10.1021/acs.analchem.5b00140',
            'unidec_cite_2':'https://link.springer.com/article/10.1007/s13361-018-1951-9',
            'unidec_github':'https://github.com/michaelmarty/UniDec/releases',
            'about-author':'https://lukasz-migas.com/'}
        self.logging = False
        self.threading = True
        self.autoSaveSettings = True
        self.autoSaveDocuments = True

        self.loadCCSAtStart = True
        self.configFile_name = 'configOut.xml'
        self.checkForDriftscopeAtStart = True
        self.driftscopePath = "C:\DriftScope\lib"
        self.driftscopePath_dist = "readers/driftscope"

        self.import_duplicate_action = "merge"
        self.import_duplicate_ask = False

        self.watermark = '<p><span style="color: #808080;">This document was generated using ORIGAMI (v. {}) which is an Open-Source software for the analysis of MS and IM-MS datasets. If you would like more information, have a look <a href="https://doi.org/10.1016/j.ijms.2017.08.014">here</a> and to download it for free, have a look <a href="https://github.com/lukasz-migas/ORIGAMI/releases">here</a>.</span></p>'.format(self.version)
        # Populate GUI
        self.overlayChoices = sorted(["Mask", "Transparent", "RGB", "Mean",
                                      "Variance", "Standard Deviation",
                                      "RMSD", "RMSF", "RMSD Matrix",
                                      "Grid (2->1)", "Grid (n x n)"])

        self.comboAcqTypeSelectChoices = ["Linear", "Exponential", "Fitted",
                                          "User-defined"]

        self.normModeChoices = ["Maximum", "Logarithmic", "Natural log", "Square root",
                                "Least Abs Deviation", "Least Squares"]

        self.detectModeChoices = ["MS", "RT", "MS/RT"]
        self.comboSmoothSelectChoices = ["None", "Savitzky-Golay", "Gaussian"]
        self.comboInterpSelectChoices = ['None', 'nearest', 'bilinear',
                                         'bicubic', 'spline16', 'spline36', 'hanning',
                                        'hamming', 'hermite', 'kaiser', 'quadric',
                                        'catrom', 'gaussian', 'bessel', 'mitchell',
                                        'sinc', 'lanczos']
        self.narrowCmapList = ['Greys', 'Purples', 'Blues', 'Greens', 'Oranges', 'Reds',
                               'Greys_r', 'Purples_r', 'Blues_r', 'Greens_r', 'Oranges_r', 'Reds_r',
                               'YlOrBr', 'YlOrRd', 'OrRd', 'PuRd', 'RdPu', 'BuPu',
                               'GnBu', 'PuBu', 'YlGnBu', 'PuBuGn', 'BuGn', 'YlGn',
                               'viridis', 'plasma', 'inferno', 'magma',
                               'PiYG', 'PRGn', 'BrBG', 'PuOr', 'RdGy', 'RdBu',
                               'RdYlBu', 'RdYlGn', 'Spectral', 'coolwarm']

        self.imageFormatType = ['png', 'svg', 'svgz', 'ps', 'raw', 'eps', 'jpeg', 'tiff', 'pdf']
        self.styles = ['Default', 'ggplot', 'fivethirtyeight', 'classic',
                       'bmh', 'seaborn', 'seaborn-ticks',
                       'seaborn-bright', 'seaborn-dark', 'seaborn-pastel']
        self.currentPalette = "HLS"
        self.color_palettes = {'HLS':'hls', 'HUSL':'husl', 'Cubehelix':'cubehelix',
                               'Spectral':'Spectral', 'Viridis':'viridis',
                               'Rainbow':'rainbow', 'Inferno':'Inferno'}

        self.imageType2D = ['Image', 'Contour']
        self.imageType3D = ['Surface', 'Wireframe']

        self.availablePlotsList = ["MS", "MS (compare)", "RT", "DT", "2D", "3D", "DT/MS", "Waterfall",
                                   "RMSD", "Comparison", "Overlay", "Calibration (MS)",
                                   "Calibration (DT)"]

        self.markerShapeDict = {'square':'s', 'circle':'o', 'pentagon':'p', 'star':'*',
                                'diamond':'D', 'cross':'x'}

        self.textOutputDict = {'comma':',', 'tab':'\t', 'space':' '}
        self.textExtensionDict = {'comma':'.csv', 'tab':'.txt', 'space':'.txt'}

        self.rmsdLocChoices = {'leftTop': (5, 95), 'rightTop': (75, 95), 'leftBottom': (5, 5),
                               'rightBottom': (75, 5), 'None':()}

        self.interactiveToolsOnOff = {'1D':{'hover':True, 'save':True, 'pan':True,
                                            'boxzoom':True, 'crosshair':False,
                                            'boxzoom_horizontal':True,
                                            'boxzoom_vertical':False,
                                            'reset':True, 'wheel':True,
                                            'wheelType':'Wheel Zoom X',
                                            'activeDrag':'Box Zoom',
                                            'activeWheel':'None',
                                            'activeInspect':'Hover'},
                                      '2D':{'hover':True, 'save':True, 'pan':True,
                                             'boxzoom':True, 'crosshair':True,
                                             'boxzoom_horizontal':False,
                                             'boxzoom_vertical':False,
                                             'reset':True, 'wheel':True,
                                             'wheelType':'Wheel Zoom X',
                                             'activeDrag':'Box Zoom',
                                             'activeWheel':'None',
                                             'activeInspect':'Hover'},
                                      'Overlay':{'hover':True, 'save':True, 'pan':True,
                                                 'boxzoom':True, 'crosshair':True,
                                                 'boxzoom_horizontal':False,
                                                 'boxzoom_vertical':False,
                                                 'reset':True,
                                                 'wheel':False,
                                                 'wheelType':'Wheel Zoom X',
                                                 'activeDrag':'Box Zoom',
                                                 'activeWheel':'None',
                                                 'activeInspect':'Hover'},
                                      'All':{'hover':True, 'save':True, 'pan':True,
                                             'boxzoom':True, 'crosshair':True,
                                             'boxzoom_horizontal':True,
                                             'boxzoom_vertical':True,
                                             'reset':True, 'wheel':True,
                                             'wheelType':'Wheel Zoom XY',
                                             'activeDrag':'Box Zoom',
                                             'activeWheel':'None',
                                             'activeInspect':'Hover'}}

        self._plotSettings = {'MS':{'axes_size':[0.1, 0.5, 0.85, 0.45], 'gui_size':[10, 6], 'resize_size':[10, 4], 'save_size':[0.1, 0.15, 0.85, 0.8], 'default_name':'MS'},
                              'MS (compare)':{'axes_size':[0.1, 0.1, 0.8, 0.85], 'gui_size':[8, 8], 'resize_size':[10, 10], 'save_size':[0.1, 0.1, 0.8, 0.85], 'default_name':'MS_compare'},
                              'RT':{'axes_size':[0.1, 0.2, 0.8, 0.75], 'gui_size':[10, 4], 'resize_size':[10, 4], 'save_size':[0.1, 0.15, 0.85, 0.8], 'default_name':'RT'},
                              'DT':{'axes_size':[0.1, 0.2, 0.8, 0.75], 'gui_size':[10, 4], 'resize_size':[10, 4], 'save_size':[0.1, 0.15, 0.85, 0.8], 'default_name':'IMS1D'},
                              '2D':{'axes_size':[0.1, 0.1, 0.8, 0.85], 'gui_size':[8, 8], 'resize_size':[10, 10], 'save_size':[0.1, 0.1, 0.8, 0.85], 'default_name':'IMS2D'},
                              '3D':{'axes_size':[0.1, 0.1, 0.8, 0.85], 'gui_size':[12, 8], 'resize_size':[10, 10], 'save_size':[0.1, 0.1, 0.8, 0.85], 'default_name':'IMS3D'},
                              'DT/MS':{'axes_size':[0.1, 0.1, 0.8, 0.85], 'gui_size':[8, 8], 'resize_size':[10, 10], 'save_size':[0.1, 0.1, 0.8, 0.85], 'default_name':'DTMS'},
                              'MS (DT/RT)':{'axes_size':[0.1, 0.2, 0.8, 0.75], 'gui_size':[10, 4], 'resize_size':[10, 4], 'save_size':[0.1, 0.15, 0.85, 0.8], 'default_name':'MS'},

                              'Waterfall':{'axes_size':[0.05, 0.1, 0.9, 0.85], 'gui_size':[10, 4], 'resize_size':[10, 10], 'save_size':[0.1, 0.1, 0.8, 0.8], 'default_name':'Waterfall'},
                              'Violin':{'axes_size':[0.15, 0.1, 0.8, 0.85], 'gui_size':[10, 4], 'resize_size':[10, 10], 'save_size':[0.1, 0.1, 0.8, 0.8], 'default_name':'Violin'},
                              'RMSD':{'axes_size':[0.1, 0.1, 0.8, 0.85], 'gui_size':[10, 4], 'resize_size':[10, 10], 'save_size':[0.1, 0.1, 0.8, 0.85], 'default_name':'RMSD'},
                              'RMSF':{'axes_size':[0.1, 0.1, 0.8, 0.85], 'gui_size':[10, 4], 'resize_size':[10, 10], 'save_size':[0.1, 0.1, 0.8, 0.85], 'default_name':'RMSF'},
                              'Matrix':{'axes_size':[0.1, 0.1, 0.8, 0.85], 'gui_size':[8, 8], 'resize_size':[10, 10], 'save_size':[0.1, 0.1, 0.8, 0.85], 'default_name':'matrix'},
                              'Comparison':{'axes_size':[0.2, 0.2, 0.6, 0.6], 'gui_size':[8, 8], 'resize_size':[10, 10], 'save_size':[0.2, 0.2, 0.6, 0.6], 'default_name':'comparison'},
                              'Overlay':{'axes_size':[0.1, 0.1, 0.8, 0.85], 'gui_size':[8, 8], 'resize_size':[10, 10], 'save_size':[0.1, 0.1, 0.8, 0.85], 'default_name':'overlay'},
                              'Overlay (Grid)':{'axes_size':[0.1, 0.1, 0.8, 0.85], 'gui_size':[8, 8], 'resize_size':[10, 10], 'save_size':[0.1, 0.1, 0.8, 0.85], 'default_name':'overlay'},

                              'Calibration (MS)':{'axes_size':[0.10, 0.15, 0.8, 0.7], 'gui_size':[10, 4], 'resize_size':[10, 4], 'save_size':[0.10, 0.20, 0.8, 0.7], 'default_name':'calibration_MS'},
                              'Calibration (DT)':{'axes_size':[0.10, 0.15, 0.8, 0.7], 'gui_size':[6, 6], 'resize_size':[10, 4], 'save_size':[0.10, 0.15, 0.8, 0.7], 'default_name':'calibration_DT'},

                              'UniDec (MS)':{'axes_size':[0.1, 0.2, 0.8, 0.7], 'gui_size':[6, 3], 'resize_size':[10, 6], 'save_size':[0.1, 0.1, 0.8, 0.85], 'default_name':'unidec_MS'},
                              'UniDec (MW)':{'axes_size':[0.1, 0.2, 0.8, 0.7], 'gui_size':[6, 3], 'resize_size':[10, 6], 'save_size':[0.1, 0.1, 0.8, 0.85], 'default_name':'unidec_MW'},
                              'UniDec (m/z vs Charge)':{'axes_size':[0.1, 0.1, 0.8, 0.85], 'gui_size':[6, 6], 'resize_size':[10, 10], 'save_size':[0.1, 0.1, 0.8, 0.85], 'default_name':'unidec_grid_MZvZ'},
                              'UniDec (Isolated MS)':{'axes_size':[0.1, 0.1, 0.8, 0.85], 'gui_size':[6, 6], 'resize_size':[10, 6], 'save_size':[0.1, 0.1, 0.8, 0.85], 'default_name':'unidec_isolated_MS'},
                              'UniDec (MW vs Charge)':{'axes_size':[0.1, 0.1, 0.8, 0.85], 'gui_size':[6, 6], 'resize_size':[10, 10], 'save_size':[0.1, 0.1, 0.8, 0.85], 'default_name':'unidec_grid_MWvZ'},
                              'UniDec (Barplot)':{'axes_size':[0.15, 0.1, 0.8, 0.85], 'gui_size':[6, 6], 'resize_size':[10, 6], 'save_size':[0.1, 0.1, 0.8, 0.85], 'default_name':'unidec_barplot'},
                              'UniDec (Charge Distribution)':{'axes_size':[0.15, 0.1, 0.7, 0.75], 'gui_size':[6, 3], 'resize_size':[10, 6], 'save_size':[0.1, 0.1, 0.8, 0.85], 'default_name':'unidec_chargeDist'},

                              'Other (Line)':{'axes_size':[0.15, 0.45, 0.75, 0.5], 'gui_size':[10, 6], 'resize_size':[10, 4], 'save_size':[0.1, 0.1, 0.8, 0.85], 'default_name':'other_line'},
                              'Other (Multi-line)':{'axes_size':[0.15, 0.2, 0.7, 0.7], 'gui_size':[6, 3], 'resize_size':[10, 6], 'save_size':[0.1, 0.1, 0.8, 0.85], 'default_name':'other_multiline'},
                              'Other (Barplot)':{'axes_size':[0.1, 0.1, 0.8, 0.85], 'gui_size':[6, 6], 'resize_size':[10, 10], 'save_size':[0.1, 0.1, 0.8, 0.85], 'default_name':'other_barplot'},
                              'Other (Grid-1D)':{'axes_size':[0.15, 0.1, 0.75, 0.85], 'gui_size':[6, 6], 'resize_size':[10, 10], 'save_size':[0.15, 0.1, 0.75, 0.85], 'default_name':'other_grid1D'},
                              'Other (Scatter)':{'axes_size':[0.15, 0.15, 0.75, 0.8], 'gui_size':[6, 6], 'resize_size':[10, 10], 'save_size':[0.15, 0.15, 0.75, 0.8], 'default_name':'other_scatter'},
                              'Other (Waterfall)':{'axes_size':[0.1, 0.15, 0.8, 0.8], 'gui_size':[6, 6], 'resize_size':[10, 10], 'save_size':[0.1, 0.15, 0.8, 0.8], 'default_name':'other_waterfall'},
                              }

        self.labelsXChoices = ['Scans', 'Collision Voltage (V)',
                               'Activation Voltage (V)', 'Lab Frame Energy (eV)',
                               'Activation Energy (eV)', 'Mass-to-charge (Da)',
                               'm/z (Da)', 'Wavenumber (cm⁻¹)']

        self.labelsYChoices = ['Drift time (bins)', 'Drift time (ms)',
                               'Arrival time (ms)', 'Collision Cross Section (Å²)']

        self.panelNames = {'MS':0, 'RT':1, '1D':2, '2D':3, 'MZDT':4, 'Waterfall':5,
                           '3D':6, 'RMSF':7, 'Comparison':8, 'Overlay':9,
                           'Calibration':10, 'UniDec':11, "Other":12}

        self.peaklistColNames = {'check':0, 'start':1, 'end':2, 'charge':3, 'intensity':4,
                                 'color':5, 'colormap':6, 'alpha':7, 'mask':8,
                                 'label':9, 'method':10, 'filename':11}

        self._peakListSettings = [{'name':'', 'order':0, 'width':25, 'show':True},
                                  {'name':'min m/z', 'order':1, 'width':65, 'show':True},
                                  {'name':'max m/z', 'order':2, 'width':65, 'show':True},
                                  {'name':'z', 'order':3, 'width':25, 'show':True},
                                  {'name':'% int', 'order':4, 'width':60, 'show':True},
                                  {'name':'color', 'order':5, 'width':60, 'show':True},
                                  {'name':'colormap', 'order':6, 'width':70, 'show':True},
                                  {'name':'\N{GREEK SMALL LETTER ALPHA}', 'order':7, 'width':35, 'show':True},
                                  {'name':'mask', 'order':8, 'width':40, 'show':True},
                                  {'name':'label', 'order':9, 'width':50, 'show':True},
                                  {'name':'method', 'order':10, 'width':80, 'show':True},
                                  {'name':'file', 'order':11, 'width':100, 'show':True}
                                  ]

        self.driftTopColNames = {'start':0, 'end':1, 'scans':2, 'drift_voltage':4,
                                 'filename':5}

        self.driftBottomColNames = {'start':0, 'end':1, 'intensity':2, 'charge':4,
                                    'filename':5}

        self.textlistColNames = {'check':0, 'start':1, 'end':2, 'charge':3, 'color':4,
                                 'colormap':5, 'alpha':6, 'mask':7, 'label':8,
                                 'shape':9, 'filename':10}

        self._textlistSettings = [{'name':'', 'order':0, 'width':25, 'show':True},
                                  {'name':'min CE', 'order':1, 'width':65, 'show':True},
                                  {'name':'max CE', 'order':2, 'width':65, 'show':True},
                                  {'name':'z', 'order':3, 'width':25, 'show':True},
                                  {'name':'color', 'order':4, 'width':60, 'show':True},
                                  {'name':'colormap', 'order':5, 'width':70, 'show':True},
                                  {'name':'\N{GREEK SMALL LETTER ALPHA}', 'order':6, 'width':35, 'show':True},
                                  {'name':'mask', 'order':7, 'width':40, 'show':True},
                                  {'name':'label', 'order':8, 'width':50, 'show':True},
                                  {'name':'shape', 'order':9, 'width':70, 'show':True},
                                  {'name':'file', 'order':10, 'width':100, 'show':True}
                                  ]

        # column name 'energy' was changed to 'variable' as it might be more appropriate
        self.multipleMLColNames = {'check':0, 'filename':1, 'energy':2, 'document':3, 'label':4}
        self._multipleFilesSettings = [{'name':'', 'order':0, 'width':25, 'show':True},
                                       {'name':'filename', 'order':1, 'width':200, 'show':True},
                                       {'name':'variable', 'order':2, 'width':50, 'show':True},
                                       {'name':'document', 'order':3, 'width':80, 'show':True},
                                       {'name':'label', 'order':4, 'width':100, 'show':True}
                                       ]

        self._interactiveSettings = [{'name':'', 'order':0, 'width':25, 'show':True},
                                     {'name':'document', 'order':1, 'width':150, 'show':True},
                                     {'name':'type', 'order':2, 'width':90, 'show':True},
                                     {'name':'file/ion/item', 'order':3, 'width':150, 'show':True},
                                     {'name':'title', 'order':4, 'width':40, 'show':True},
                                     {'name':'header', 'order':5, 'width':40, 'show':True},
                                     {'name':'footnote', 'order':6, 'width':40, 'show':True},
                                     {'name':'color/colormap', 'order':7, 'width':75, 'show':True},
                                     {'name':'page', 'order':8, 'width':50, 'show':True},
#                                      {'name':'tools', 'order':9, 'width':50, 'show':True},
                                     {'name':'#', 'order':9, 'width':30, 'show':True},
                                     ]
        self.interactiveColNames = {'check':0, 'document':1, 'type':2, 'file':3, 'title':4,
                                     'header':5, 'footnote':6, 'color':7, 'colormap':7,
                                     'page':8,
#                                      'tools':9,
                                     'order':9}

        self.ccsTopColNames = {'filename':0, 'start':1, 'end':2,
                               'protein':3, 'charge':4, 'ccs':5, 'tD':6,
                               'gas':7}

        self.ccsBottomColNames = {'filename':0, 'start':1, 'end':2,
                                  'ion':3, 'protein':4, 'charge':5,
                                  'format':6}

        self.ccsDBColNames = {'protein':0, 'mw':1, 'units':2, 'charge':3, 'ion':4,
                              'hePos':5, 'n2Pos':6, 'heNeg':7, 'n2Neg':8, 'state':9,
                              'source':10}

        # Calibration
        self.elementalMass = {'Hydrogen':1.00794, 'Helium':4.002602, 'Nitrogen':28.0134}

        # Add default HTML output methods
        self.pageDict = {'None':{'name':'None', 'layout':'Individual', 'rows':None, 'columns':None},
                         'Rows':{'name':'Rows', 'layout':'Rows', 'rows':None, 'columns':None},
                         'Columns':{'name':'Columns', 'layout':'Columns', 'rows':None, 'columns':None}
                         }
        self.interactive_pageLayout_choices = ['Individual', 'Columns', 'Rows', 'Grid']
        self.interactive_wheelZoom_choices = ['Wheel Zoom XY', 'Wheel Zoom X', 'Wheel Zoom Y']
        self.interactive_toolbarPosition_choices = ['left', 'above', 'right', 'below']
        self.interactive_activeDragTools_choices = ['Box Zoom', 'Box Zoom X', 'Box Zoom Y', 'Pan', 'Pan X', 'Pan Y', 'auto', 'None']
        self.interactive_activeWheelTools_choices = ['Wheel Zoom XY', 'Wheel Zoom X', 'Wheel Zoom Y', 'auto', 'None']
        self.interactive_activeHoverTools_choices = ['Hover', 'Crosshair', 'auto', 'None']
        self.interactive_colorbarPosition_choices = ['left', 'above', 'right', 'below']

        #=========== FILE INFO ===========
        # can be removed
        self.rawName = ''
        self.fileName = ''
        self.textName = ''
        self.dirname = ''
        self.savefilename = ''

        # Replot data
        self.replotData = {}
        self.replotMSdata = {}
        self.replot1Ddata = {}
        self.replot2Ddata = {}

        # temporary data storage
        self._temp_ = {}  # new in v1.2.1

        # mzml/mgf/mzident etc
        self.msms_load_n_scans = 500  # new
        self.msms_show_neutral_loss = False  # new
        self.msms_show_full_label = True  # new
        self.msms_add_arrows = False
        self.msms_line_color_unlabelled = (0, 0, 0)  # new
        self.msms_line_color_labelled = (1, 0, 0)  # new
        self.msms_label_y_offset = 0.02  # new

        self._tandem_show_PTMs_in_table = False  # new
        self._tandem_show_unidentified_in_table = True  # new
        self._tandem_label_format = {'fragment_name':True, 'peptide_seq':False,
                                     'charge':True, 'delta_mz': False}

        self.fragments_tolerance = {"Da":0.05, "ppm":25}  # new
        self.fragments_tolerance_limits = {"Da":[0.00, 5, 0.25], "ppm":[0, 500, 25]}  # new
        self.fragments_units_choices = ["Da", "ppm"]  # new
        self.fragments_units = "Da"  # new
        self.fragments_max_matches = 1  # new
        self.fragments_common = {"a/x":["a-all", "x-all"],
                                 "b/y":["b-all", "y-all"],
                                 "c/z":["c-all", "z-all"],
                                 "ETD/ECD":["c-all", "y-all", "z+1/2/3"],
                                 "CID":["b-all", "y-all"],
                                 "Other":[]}

        self.fragments_search = {
            'M-ALL':False, 'M':False, 'M-nH2O':False, 'M-nNH3':False,
            'a-ALL':False, 'a':False, 'a-nH2O':False, 'a-nNH3':False,
            'b-ALL':False, 'b':False, 'b-nH2O':False, 'b-nNH3':False,
            'c-ALL':False, 'c':False, 'c-nH2O':False, 'c-nNH3':False, 'c-dot':False, 'c+1/2':False,
            'x-ALL':False, 'x':False, 'x-nH2O':False, 'x-nNH3':False,
            'y-ALL':False, 'y':False, 'y-nH2O':False, 'y-nNH3':False,
            'z-ALL':False, 'z':False, 'z-nH2O':False, 'z-nNH3':False, 'z-dot':False, 'z+1/2/3':False}

        # plot parameters
        self._plots_grid_show = False
        self._plots_grid_color = [0, 0, 0]
        self._plots_grid_line_width = 1

        self._plots_extract_color = [1, 0, 0.2]
        self._plots_extract_line_width = 4.0
        self._plots_extract_crossover_1D = 0.1
        self._plots_extract_crossover_2D = 0.02

        self._plots_zoom_vertical_color = [0.5, 0.0, 0]
        self._plots_zoom_horizontal_color = [0.5, 0.0, 0]
        self._plots_zoom_box_color = [0.5, 0.0, 0]
        self._plots_zoom_line_width = 2
        self._plots_zoom_crossover = 0.05

        # window parameters
        self.extraParamsWindow_on_off = False
        self.extraParamsWindow = {'General':0, 'Plot 1D':1, 'Plot 2D':2,
                                  'Plot 3D':3, 'Colorbar':4, 'Legend':5,
                                  'RMSD':6, 'Waterfall':7, 'Violin':8,
                                  'Extra':9}

        self.processParamsWindow_on_off = False
        self.processParamsWindow = {'Extract':0, 'ORIGAMI':1, 'MS':2, '2D':3, 'Peak fitting':4, 'UniDec':5}

        self.interactiveParamsWindow_on_off = False

        self.importExportParamsWindow_on_off = False
        self.importExportParamsWindow = {'Peaklist':0, 'Image':1, 'Files':2}

        # Custom colors dictionary
        self.customColors = OrderedDict([(0, [16, 71, 185]), (1, [50, 140, 0]), (2, [241, 144, 0]),
                                         (3, [76, 199, 197]), (4, [143, 143, 21]), (5, [38, 122, 255]),
                                         (6, [38, 143, 73]), (7, [237, 187, 0]), (8, [120, 109, 255]),
                                         (9, [179, 78, 0]), (10, [128, 191, 189]), (11, [137, 136, 68]),
                                         (12, [200, 136, 18]), (13, [197, 202, 61]), (14, [123, 182, 255]),
                                         (15, [69, 67, 138])])
        self.used_customColors = []
        self.overlay_cmaps = ['Greys', 'Purples', 'Blues', 'Greens', 'Oranges', 'Reds',
                              'Greys_r', 'Purples_r', 'Blues_r', 'Greens_r', 'Oranges_r', 'Reds_r',
                              'YlOrBr', 'YlOrRd', 'OrRd', 'PuRd', 'RdPu', 'BuPu',
            				  'GnBu', 'PuBu', 'YlGnBu', 'PuBuGn', 'BuGn', 'YlGn']
        self.overlay_defaultMask = 0.4
        self.overlay_defaultAlpha = 0.5
        self.overlay_smooth1DRT = 1
        self.smoothOverlay1DRT = 1

        # previous files
        self.previousFiles = []

        # Open windows
        self._windowSettings = {'Plots':{'gripper':False, 'caption':False,
                                         'close_button':False, 'show':True,
                                         'floating':False, 'title':'Plots'},
                                'Documents':{'gripper':False, 'caption':True,
                                             'close_button':True, 'show':True,
                                             'floating':False, 'title':'Documents'},
                                'Peak list':{'gripper':False, 'caption':True,
                                             'close_button':True, 'show':False,
                                             'floating':False, 'title':'Peak list'},
                                'CCS calibration':{'gripper':False, 'caption':True,
                                                   'close_button':True, 'show':False,
                                                   'floating':False, 'title':'CCS calibration'},
                                'Linear Drift Cell':{'gripper':False, 'caption':True,
                                                     'close_button':True, 'show':False,
                                                     'floating':False, 'title':'Linear Drift Cell'},
                                'Text files':{'gripper':False, 'caption':True,
                                              'close_button':True, 'show':False,
                                              'floating':False, 'title':'Text files'},
                                'Multiple files':{'gripper':False, 'caption':True,
                                                  'close_button':True, 'show':False,
                                                  'floating':False, 'title':'Multiple files'},
                                'Log':{'gripper':False, 'caption':True,
                                       'close_button':True, 'show':False,
                                       'title':'Log', 'floating':False},
                                'Plot parameters':{'gripper':False, 'caption':True,
                                                   'close_button':True, 'show':False,
                                                   'floating':True, 'title':'Plot parameters'},
                                'Import/Export parameters':{'gripper':False, 'caption':True,
                                                            'close_button':True, 'show':False,
                                                            'floating':True, 'title':'Import/Export parameters'},
                                'Processing parameters':{'gripper':False, 'caption':True,
                                                         'close_button':True, 'show':False,
                                                         'floating':True, 'title':'Processing parameters'},
                                'Toolbar':{'gripper':True, 'show':True, 'orientation':'top',
                                           'left_position':False, 'top_position':True,
                                           'left_dockable':True, 'right_dockable':True,
                                           'top_dockable':True, 'bottom_dockable':True,
                                           'title':'Toolbar', 'close_button':False}
                                }

        # GUI add-ons
        self.cmap_narrow_choices = ['Greys', 'Purples', 'Blues', 'Greens', 'Oranges', 'Reds',
                                    'Greys_r', 'Purples_r', 'Blues_r', 'Greens_r', 'Oranges_r', 'Reds_r',
                                    'YlOrBr', 'YlOrRd', 'OrRd', 'PuRd', 'RdPu', 'BuPu', 'GnBu',
                                    'YlOrBr_r', 'YlOrRd_r', 'OrRd_r', 'PuRd_r', 'RdPu_r', 'BuPu_r', 'GnBu_r',
                                    'PuBu', 'YlGnBu', 'PuBuGn', 'BuGn', 'YlGn', 'viridis', 'plasma',
                                    'inferno', 'magma', 'PiYG', 'PRGn', 'BrBG', 'PuOr', 'RdGy', 'RdBu',
                                    'RdYlBu', 'RdYlGn', 'Spectral', 'coolwarm']
        self.interpolation_choices = ['None', 'nearest', 'bilinear', 'bicubic',
                                      'spline16', 'spline36', 'hanning', 'hamming',
                                      'hermite', 'kaiser', 'quadric', 'catrom',
                                      'gaussian', 'bessel', 'mitchell', 'sinc',
                                      'lanczos']
        self.normalizationMS_choices = ["Maximum"]
        self.normalization2D_choices = ["Maximum", "Logarithmic", "Natural log", "Square root", "Least Abs Deviation", "Least Squares"]
        self.smoothMS_choices = ["None", "Savitzky-Golay", "Gaussian"]
        self.smooth2D_choices = ["None", "Savitzky-Golay", "Gaussian"]

        self.markerShapeDict = {'square':'s', 'circle':'o', 'pentagon':'p', 'star':'*',
                                'diamond':'D', 'cross':'x', 'plus':'+', 'point':'.',
                                'vline':': ', 'hline':'_'}
        self.lineStylesList = ['solid', 'dashed', 'dashdot', 'dotted']
        self.lineStylesDict = {"-":'solid', "--":'dashed', "-.":'dashdot', ":":'dotted'}
        self.lineHatchDict = OrderedDict([('none', ' '), ('sparse hatch', '/'), ('dense hatch', '//'),
                                          ('vertical line', '|'), ('horizontal line', '-'),
                                          ('square', '+'), ('cross', 'X'), ('small circles', 'o'),
                                          ('large circles', 'O'), ('dots', '.'), ('stars', '*')])
        self.lineHatchList = ['', '/', ' |', '|', '-', '+', 'X', 'o', 'O', '.', '*']
        self.legendPositionChoice = ["best", "upper right", "upper left", "lower left", "lower right", "right", "center left", "center right", "lower center", "upper center", "center"]
        self.legendFontChoice = ["xx-small", "x-small", "small", "medium", "large", "x-large", "xx-large"]
        self.colorbarChoices = ["left", "right", "top", "bottom"]

        self.horizontal_alignment_list = ['center', 'right', 'left']
        self.vertical_alignment_list = ['center', 'top', 'bottom']
        self.label_fontsize_list = ["xx-small", "x-small", "small", "medium", "large", "x-large", "xx-large"]
        self.label_fontweight_list = ["ultralight", "light", "normal", "regular", "medium", "bold", "heavy"]
        self.label_font_orientation_list = ['horizontal', 'vertical']

        # Smart zoom
        self.smart_zoom_enable = True  # new in v1.3.0.0
        self.smart_zoom_soft_max = 15000  # new in v1.3.0.0
        self.smart_zoom_hard_max = 100000  # new in v1.3.0.0
        self.smart_zoom_downsampling_method_choices = ["Auto", "Binned (summed)", "Binned (mean)", "Sub-sampled"]  # new in v1.3.0.0
        self.smart_zoom_downsampling_method = "Auto"  # new in v1.3.0.0
        self.smart_zoom_subsample_default = 5  # new in v1.3.0.0
        self.smart_zoom_view_mode_choices = ["One-view (2D-only)", "Three-view (DT, MS, 2D)"]  # new in v1.3.0.0
        self.smart_zoom_view_mode = "One-view (2D-only)"  # new in v1.3.0.0
        self.smart_zoom_min_search = 1  # new in v1.3.0.0
        self.smart_zoom_max_search = 20  # new in v1.3.0.0

        # Annotation
        self.annotation_charge_std_dev = 0.05

        self.annotation_arrow_line_width = 0.5
        self.annotation_arrow_line_style = "dashed"
        self.annotation_arrow_cap_length = 0.01  # new in v1.2.1
        self.annotation_arrow_cap_width = 0.01  # new in v1.2.1

        self.annotation_label_y_offset = 0.05  # new in v1.2.1
        self.annotation_label_horz = "center"
        self.annotation_label_vert = "center"
        self.annotation_label_font_size = "small"
        self.annotation_label_font_weight = "normal"
        self.annotation_label_font_orientation = "horizontal"

        self.annotation_zoom_y = False  # new in v1.2.1
        self.annotation_zoom_y_multiplier = 1.5  # new in v1.2.1
        self.annotation_show_vline = False  # new in v1.2.1

        self.annotation_patch_transparency = 0.2  # new in v1.2.1
        self.annotation_patch_width = 3  # new in v1.2.1

        # UniDec
        self.unidec_mzStart = 500
        self.unidec_mzEnd = 8000
        self.unidec_mzBinSize = 0.1
        self.unidec_gaussianFilter = 0.0
        self.unidec_linearization_choices = {"Linear m/z":0,
                                             "Linear resolution":1,
                                             "Nonlinear":2,
                                             "Linear interpolation":3,
                                             "Linear resolution interpolation":4}
        self.unidec_linearization = "Linear m/z"
        self.unidec_accelerationV = 0.0

        self.unidec_zStart = 1
        self.unidec_zEnd = 100
        self.unidec_mwStart = 500
        self.unidec_mwEnd = 150000
        self.unidec_mwFrequency = 100
        self.unidec_peakWidth = 2.0
        self.unidec_peakWidth_auto = True
        self.unidec_peakFunction_choices = {"Gaussian":0, "Lorentzian":1, "Split G/L":""}
        self.unidec_peakFunction = "Lorentzian"

        self.unidec_peakDetectionWidth = 500.0
        self.unidec_peakDetectionThreshold = 0.1
        self.unidec_peakNormalization_choices = {"None":0, "Max":1, "Total":2}
        self.unidec_peakNormalization = "Max"
        self.unidec_lineSeparation = 0.05
        self.unidec_maxIterations = 100
        self.unidec_charges_label_charges = 0.05
        self.unidec_charges_offset = 0.01
        self.unidec_show_individualComponents = True
        self.unidec_show_markers = True
        self.unidec_speedy = True
        self.unidec_show_chargeStates = False
        self.unidec_maxShown_individualLines = 100
        self.unidec_optimiseLabelPositions = True

        self.unidec_plot_fit_lineColor = (1., 0., 0.)
        self.unidec_plot_MW_showMarkers = True
        self.unidec_plot_MW_markerSize = 50
        self.unidec_plot_isolatedMS_markerSize = 50
        self.unidec_plot_bar_markerSize = 50
        self.unidec_plot_bar_width = 1
        self.unidec_plot_bar_alpha = 1.0
        self.unidec_plot_bar_edge_color = (0., 0., 0.)
        self.unidec_plot_bar_sameAsFill = False
        self.unidec_plot_bar_lineWidth = 2.
        self.unidec_plot_color_scheme = "Color palette"
        self.unidec_plot_colormap = "viridis"
        self.unidec_plot_palette = "HLS"
        self.unidec_plot_contour_levels = 75
        self.unidec_plot_panel_view = "Tabbed view"

        # ORIGAMI
        self.origami_startScan = 0
        self.origami_spv = 3
        self.origami_startVoltage = 4
        self.origami_endVoltage = 200
        self.origami_stepVoltage = 2
        self.origami_boltzmannOffset = 0
        self.origami_exponentialPercentage = 0
        self.origami_exponentialIncrement = 0
        self.origami_acquisition_choices = ['Linear', 'Exponential', 'Boltzmann', 'User-defined', 'Manual']
        self.origami_acquisition = 'Linear'
        self.origami_userDefined_list = []

        # Extracting
        self.extract_massSpectra = False
        self.extract_chromatograms = False
        self.extract_driftTime1D = False
        self.extract_driftTime2D = False
        self.extract_mzStart = 0
        self.extract_mzEnd = 0
        self.extract_rtStart = 0
        self.extract_rtEnd = 999
        self.extract_dtStart = 1
        self.extract_dtEnd = 200

        # Peak fitting
        self.fit_addPeaks = True
        self.fit_addPeaksToAnnotations = False
        self.fit_xaxis_limit = False
        self.fit_highlight = True
        self.fit_show_labels = True
        self.fit_show_labels_mz = True
        self.fit_show_labels_int = True
        self.fit_labels_optimise_position = True
        self.fit_show_labels_max_count = 100
        self.fit_type_choices = ['MS', 'RT', 'MS + RT']
        self.fit_type = 'MS'
        self.fit_threshold = 0.10
        self.fit_window = 500
        self.fit_width = 1.0
        self.fit_asymmetric_ratio = 0.6
        self.fit_smoothPeaks = True
        self.fit_smooth_sigma = 1.0
        self.fit_highRes = False
        self.fit_highRes_threshold = 0.0
        self.fit_highRes_window = 10
        self.fit_highRes_width = 1
        self.fit_highRes_isotopicFit = False

        # UVPD
        self.uvpd_peak_finding_threshold = 0.1  # new in v1.2.1
        self.uvpd_peak_buffer_width = 1  # new in v1.2.1
        self.uvpd_peak_first_index = 1  # new in v1.2.1
        self.uvpd_peak_laser_on = (1, 0, 0)  # new in v1.2.1
        self.uvpd_peak_laser_off = (0, 0, 1)  # new in v1.2.1
        self.uvpd_peak_show_markers = True  # new in v1.2.1
        self.uvpd_peak_show_patches = False  # new in v1.2.1
        self.uvpd_peak_show_labels = False  # new in v1.2.1

        # RMSD
        self.rmsd_position_choices = ['bottom left', 'bottom right', 'top left', 'top right', 'none', 'other']
        self.rmsd_position = 'bottom left'
        self.rmsd_location = (5, 5)
        self.rmsd_color = (1, 1, 1)
        self.rmsd_fontSize = 10
        self.rmsd_fontWeight = True
        self.rmsd_rotation_X = 45
        self.rmsd_rotation_Y = 0
        self.rmsd_matrix_add_labels = True
        self.rmsd_lineColour = (0, 0, 0)
        self.rmsd_lineTransparency = 0.4
        self.rmsd_underlineColor = (0, 0, 0)
        self.rmsd_underlineTransparency = 0.4
        self.rmsd_lineWidth = 1
        self.rmsd_lineStyle = 'solid'
        self.rmsd_lineHatch = ' '
        self.rmsd_hspace = 0.1

        # Extract DT/MS
        self.extract_dtms_mzStart = 200
        self.extract_dtms_mzEnd = 5000
        self.extract_dtms_mzBinSize = 0.1

        # Process 2D
        self.plot2D_normalize = False
        self.plot2D_normalize_choices = ["Maximum", "Logarithmic", "Natural log", "Square root", "Least Abs Deviation", "Least Squares"]
        self.plot2D_normalize_mode = 'Maximum'
        self.plot2D_smooth_choices = ['None', 'Gaussian', 'Savitzky-Golay']
        self.plot2D_smooth_mode = 'None'
        self.plot2D_smooth_sigma = 1
        self.plot2D_smooth_window = 3
        self.plot2D_smooth_polynomial = 1
        self.plot2D_threshold = 0.0

        # Process MS
        self.ms_normalize = True
        self.ms_normalize_choices = ['Maximum']
        self.ms_normalize_mode = 'Maximum'
        self.ms_smooth_choices = ['None', 'Gaussian', 'Savitzky-Golay']
        self.ms_smooth_mode = 'None'
        self.ms_smooth_sigma = 1
        self.ms_smooth_window = 3
        self.ms_smooth_polynomial = 1
        self.ms_threshold = 0.0

        self.ms_crop_min = 500
        self.ms_crop_max = 8000

        self.ms_process_crop = False
        self.ms_process_linearize = True
        self.ms_process_smooth = True
        self.ms_process_threshold = True
        self.ms_process_normalize = True

        # Importing files
        self.import_binOnImport = True
        self.import_loadMS = True
        self.import_loadRT = True
        self.import_loadDT = True
        self.import_loadDTMS = True

        # Binning
        self.ms_mzStart = 500
        self.ms_mzEnd = 8000
        self.ms_mzBinSize = 1
        self.ms_enable_in_RT = False
        self.ms_enable_in_MML_start = True
        self.ms_dtmsBinSize = 1
        self.ms_linearization_mode_choices = ["Linear m/z", "Linear resolution",
                                              "Nonlinear", "Linear interpolation",
                                              "Linear resolution interpolation",
                                              "Binning"]
        self.ms_linearization_mode = "Linear interpolation"
        self.ms_auto_range = True

        # waterfall
        self.waterfall = False
        self.waterfall_increment = 0.05
        self.waterfall_offset = 0
        self.waterfall_reverse = False
        self.waterfall_lineWidth = 1
        self.waterfall_lineStyle = 'solid'
        self.waterfall_color = [0, 0, 0]
        self.waterfall_useColormap = True
        self.waterfall_normalize = True
        self.waterfall_color_choices = ["Same color", "Colormap", "Color palette", "Random"]  # new
        self.waterfall_colormap = "mako"
        self.waterfall_color_value = "Same color"
        self.waterfall_line_sameAsShade = True
        self.waterfall_add_labels = False
        self.waterfall_labels_frequency = 1
        self.waterfall_labels_x_offset = 0.05
        self.waterfall_labels_y_offset = 0.05
        self.waterfall_label_fontSize = 12
        self.waterfall_label_fontWeight = True
        self.waterfall_shade_under = True
        self.waterfall_shade_under_color = [0, 0, 0]
        self.waterfall_shade_under_nlimit = 50
        self.waterfall_shade_under_transparency = 0.25
        self.waterfall_label_format_choices = ["String", "Float", "Integer"]
        self.waterfall_label_format = "Float"

        # violin
        self.violin_orientation_choices = ["vertical", "horizontal"]
        self.violin_orientation = "vertical"
        self.violin_spacing = 0.5
        self.violin_min_percentage = 0.03
        self.violin_lineWidth = 2
        self.violin_lineStyle = 'solid'
        self.violin_color = [0, 0, 0]
        self.violin_normalize = True
        self.violin_color_choices = ["Same color", "Colormap", "Color palette", "Random"]
        self.violin_colormap = "mako"
        self.violin_color_value = "Colormap"
        self.violin_line_sameAsShade = False
        self.violin_shade_under = True
        self.violin_shade_under_color = [0, 0, 0]
        self.violin_nlimit = 50
        self.violin_shade_under_transparency = 1
        self.violin_label_format_choices = ["String", "Float", "Integer"]
        self.violin_label_format = "Integer"
        self.violin_labels_frequency = 1

        # bar
        self.bar_width = 0.1
        self.bar_alpha = 1.0
        self.bar_edge_color = (0., 0., 0.)
        self.bar_sameAsFill = True
        self.bar_lineWidth = 1.

        # colorbar
        self.colorbar = False
        self.colorbarWidth = 2
        self.colorbarPad = 0.03
        self.colorbarRange = [0, 1]
        self.colorbarMinPoints = 5
        self.colorbarPosition = 'right'
        self.colorbarLabelSize = 12

        # legend
        self.legend = False
        self.legendFrame = True
        self.legendMarkerFirst = True
        self.legendPosition = 'best'
        self.legendFontSize = 'small'
        self.legendAnchorPosition = []
        self.legendColumns = 1
        self.legendMarkerSize = 1
        self.legendNumberMarkers = 1
        self.legendAlpha = 0.5
        self.legendFancyBox = True
        self.legendLineWidth = 4
        self.legendPatchAlpha = 0.25

        # 1D parameters
        self.lineColour_1D = (0, 0, 0)
        self.labelPad_1D = 5
        self.frameWidth_1D = 1
        self.lineWidth_1D = 1
        self.lineStyle_1D = 'solid'
        self.lineShadeUnder_1D = True
        self.lineShadeUnderColour_1D = (0, 0, 0)
        self.lineShadeUnderTransparency_1D = 0.4
        self.markerColor_1D = (0, 0, 1)
        self.markerTransparency_1D = 0.4
        self.markerEdgeUseSame_1D = True
        self.markerEdgeColor_1D = (0, 0, 1)
        self.markerShape_1D = 'o'
        self.markerShapeTXT_1D = 'circle'
        self.markerSize_1D = 5
        self.axisOnOff_1D = True
        self.annotationFontSize_1D = 10
        self.annotationFontWeight_1D = False
        self.tickFontSize_1D = 16
        self.tickFontWeight_1D = False
        self.labelFontSize_1D = 16
        self.labelFontWeight_1D = False
        self.titleFontSize_1D = 18
        self.titleFontWeight_1D = False
        self.spines_left_1D = True
        self.spines_right_1D = True
        self.spines_top_1D = True
        self.spines_bottom_1D = True
        self.ticks_left_1D = True
        self.ticks_right_1D = False
        self.ticks_top_1D = False
        self.ticks_bottom_1D = True
        self.tickLabels_left_1D = True
        self.tickLabels_right_1D = False
        self.tickLabels_top_1D = False
        self.tickLabels_bottom_1D = True

        # 2D parameters
        self.interpolation = "None"
        self.axisOnOff_2D = True
        self.labelPad_2D = 5
        self.annotationFontSize_2D = 8
        self.annotationFontWeight_2D = False
        self.tickFontSize_2D = 12
        self.tickFontWeight_2D = False
        self.labelFontSize_2D = 14
        self.labelFontWeight_2D = False
        self.titleFontSize_2D = 16
        self.titleFontWeight_2D = False
        self.spines_left_2D = True
        self.spines_right_2D = True
        self.spines_top_2D = True
        self.spines_bottom_2D = True
        self.ticks_left_2D = True
        self.ticks_right_2D = False
        self.ticks_top_2D = False
        self.ticks_bottom_2D = True
        self.tickLabels_left_2D = True
        self.tickLabels_right_2D = False
        self.tickLabels_top_2D = False
        self.tickLabels_bottom_2D = True

        # 3D parameters
        self.plotType_3D = 'Surface'
        self.showGrids_3D = False
        self.shade_3D = True
        self.ticks_3D = True
        self.spines_3D = True
        self.labels_3D = True
        self.markerTransparency_3D = 0.7
        self.markerColor_3D = (0, 0, 1)
        self.markerShape_3D = 'o'
        self.markerShapeTXT_3D = 'circle'
        self.markerSize_3D = 50
        self.markerEdgeUseSame_3D = True
        self.markerEdgeColor_3D = (0, 0, 0)
        self.labelPad_3D = 20
        self.annotationFontSize_3D = 8
        self.annotationFontWeight_3D = False
        self.tickFontSize_3D = 12
        self.tickFontWeight_3D = False
        self.labelFontSize_3D = 14
        self.labelFontWeight_3D = False
        self.titleFontSize_3D = 16
        self.titleFontWeight_3D = False

        # comparison MS
        self.lineColour_MS1 = (0, 0, 0)
        self.lineTransparency_MS1 = 1.0
        self.lineStyle_MS1 = 'solid'
        self.lineColour_MS2 = (0, 0, 1)
        self.lineTransparency_MS2 = 1.0
        self.lineStyle_MS2 = 'solid'
        self.compare_massSpectrum = []
        self.compare_massSpectrumParams = {'inverse':True, 'preprocess':False,
                                           'normalize':False, 'subtract':False}

        # Settings Panel
        self.lastDir = None

        # Events
        self.extraParamsWindow_on_off = False

        # Standard input/output/error
        self.stdin = None
        self.stdout = None
        self.stderr = None

        self.cwd = None
        self.unidec_path = None
        self.temporary_data = None

        # Application presets
        self.zoomWindowX = 3  # m/z units
        self.zoomWindowY = 5  # percent

        # Presets
        self.userParameters = {'operator':'Lukasz G. Migas',
                               'contact':'lukasz.migas@manchester.ac.uk',
                               'institution':'University of Manchester',
                               'instrument':'SynaptG2',
                               'date':'date'}

        self.resize = True
        #=========== DOCUMENT TREE PARAMETERS ==========
        self.quickDisplay = False
        self.loadConfigOnStart = True
        self.currentPeakFit = "MS"
        self.overrideCombine = True
        self.useInternalParamsCombine = False
        self.overlay_usedProcessed = True

        self.binMSfromRT = False
        self.showMZDT = True
        self.ccsDB = None
        self.proteinData = None

        #=========== FILE INFO ===========
        self.normalize = False
        self.ciuMode = ''
        self.scantime = ''
        self.startTime = None
        #=========== COMBINE ===========
        self.startScan = ''
        self.startVoltage = ''
        self.endVoltage = ''
        self.stepVoltage = ''
        self.scansPerVoltage = ''
        self.chargeState = ''
        self.expPercentage = ''
        self.expIncrement = ''
        self.fittedScale = ''
        self.acqMode = ''
        self.origamiList = []

        self.binCVdata = True
        self.binMSstart = 500
        self.binMSend = 8000
        self.binMSbinsize = 0.1

        #=========== EXTRACT MZ ===========
        self.mzStart = ''
        self.mzEnd = ''
        self.rtStart = ''
        self.rtEnd = ''

        self.extractMode = ''  # 'singleIon' OR 'multipleIons'

        self.annotColor = (0, 0, 1)
        self.annotTransparency = 40
        self.markerShape = 's'
        self.markerSize = 5
        self.binSize = 0.05
        self.binSizeMZDT = 1
        self.binOnLoad = False
        self.peakWindow = 500
        self.peakThreshold = 0.1
        self.peakWidth = 1
        # High Res
        self.peakFittingHighRes = False
        self.peakThresholdAssign = 0.0
        self.peakWidthAssign = 1
        self.peakWindowAssign = 10
        self.showIsotopes = True

        self.showRectanges = True
        self.autoAddToTable = False
        self.currentRangePeakFitCheck = False
        self.smoothFitting = True
        self.sigmaMS = 1
        self.markerShapeTXT = 'square'

        #=========== PROCESS ===========
        self.datatype = ''
        self.normMode = 'None'
        self.smoothMode = ''
        self.savGolPolyOrder = 1
        self.savGolWindowSize = 3
        self.gaussSigma = 1
        self.threshold = 0

        #=========== PLOT PARAMETERS =============
        self.lineColour = (0, 0, 0)
        self.lineWidth = 10
        self.currentCmap = "inferno"
        self.interpolation = "None"
        self.overlayMethod = "Transparent"
        self.textOverlayMethod = "Mask"

        self.plotType = "Image"  # Contour / Heatmap
        self.currentStyle = 'Default'
        self.prettyContour = False
        self.useCurrentCmap = True
        self.addWaterfall = False

        self.minCmap = 0  # %
        self.midCmap = 50  # %
        self.maxCmap = 100  # %

        self.rmsdLoc = "leftBottom"
        self.rmsdLocPos = (5, 5)  # (xpos, ypos) %
        self.rmsdColor = (1, 1, 1)
        self.rmsdFontSize = 16
        self.rmsdFontWeight = True
        self.rmsdRotX = 45
        self.rmsdRotY = 0

        self.restrictXYrange = False
        self.xyLimits = []  # limits the view of 2D plot

        self.restrictXYrangeRMSD = False
        self.xyLimitsRMSD = []  # limits the range of RMSD/F calculation

        self.dpi = 200
        self.transparent = True

        self.imageWidthInch = 8
        self.imageHeightInch = 8
        self.imageFormat = 'png'

        #=========== TEXT PARAMETERS =============
        self.notationFontSize = 8
        self.tickFontWeight = False
        self.tickFontSize = 12
        self.tickFontWeight = False
        self.labelFontSize = 14
        self.labelFontWeight = False
        self.titleFontSize = 16
        self.titleFontWeight = False

        # Import CSV
        self.mzWindowSize = 3
        self.useInternalMZwindow = False

        # Export CSV
        self.saveDelimiterTXT = 'comma'
        self.saveDelimiter = ','
        self.saveExtension = '.csv'
        self.saveFormat = 'ASCII with Headers'
        self.normalizeMultipleMS = True

        # Initilize colormaps
        self.initilizeColormaps()
#         self.initlizePaths()

#===============================================================================
# # Interactive parameters
#===============================================================================

        self.saveInteractiveOverride = True

        self.figHeight = 600
        self.figWidth = 600
        self.figHeight1D = 300
        self.figWidth1D = 800

        self.layoutModeDoc = 'Individual'
        self.plotLayoutOverlay = 'Rows'
        self.defNumRows = ''
        self.defNumColumns = ''
        self.linkXYaxes = True
        self.hoverVline = True
        self.interactive_cvd_cmap = "viridis"
        self.interactive_cvd_cmap_choices = ["magma", "viridis", "cividis", "plasma", "magma"]

        self.toolsLocation = 'right'
        self.activeDrag = 'Box Zoom'
        self.activeWheel = 'None'
        self.activeInspect = 'Hover'

        self.interactive_custom_scripts = True
        self.interactive_custom_events = True
        self.interactive_custom_position = "right"

        # Other
        self.interactive_override_defaults = True
        self.openInteractiveOnSave = True
        self.interactive_add_offline_support = False
        self.interactive_sort_before_saving = True  # new in v1.2.1

        # Colorbar
        self.interactive_colorbar = False
        self.interactive_colorbar_precision = 1
        self.interactive_colorbar_label_offset = 2
        self.interactive_colorbar_useScientific = False
        self.interactive_colorbar_location = 'right'
        self.interactive_colorbar_orientation = 'vertical'
        self.interactive_colorbar_offset_x = 5
        self.interactive_colorbar_offset_y = 0
        self.interactive_colorbar_width = 15
        self.interactive_colorbar_padding = 10
        self.interactive_colorbar_edge_color = (0., 0., 0.)  # new in v1.2.1
        self.interactive_colorbar_edge_width = 2  # new in v1.2.1
        self.interactive_colorbar_modify_ticks = False  # new in v1.2.1
        self.interactive_colorbar_label_fontSize = 16  # new in v1.2.1
        self.interactive_colorbar_label_weight = False  # new in v1.2.1
        self.interactive_colorbar_title_fontSize = 16  # new in v1.2.1
        self.interactive_colorbar_title_weight = False  # new in v1.2.1

        # Frame
        self.interactive_outline_width = 2
        self.interactive_outline_alpha = 1
        self.interactive_border_min_left = 20
        self.interactive_border_min_right = 20
        self.interactive_border_min_top = 20
        self.interactive_border_min_bottom = 20
        self.interactive_background_color = (1., 1., 1.)
        self.interactive_grid_line = False
        self.interactive_grid_line_color = (1., 1., 1.)

        # Fonts
        self.interactive_title_fontSize = 16
        self.interactive_title_weight = False
        self.interactive_label_fontSize = 14
        self.interactive_label_weight = False
        self.interactive_tick_fontSize = 12
        self.interactive_annotation_fontSize = 12
        self.interactive_annotation_weight = False
        self.interactive_annotation_color = (0, 0, 0)
        self.interactive_annotation_background_color = (1, 1, 1)
        self.interactive_annotation_alpha = 1

        # Overlay grid
        self.interactive_grid_label = True
        self.interactive_grid_label_size = 12
        self.interactive_grid_label_weight = False
        self.interactive_grid_label_color = (0, 0, 0)
        self.interactive_grid_xpos = 10
        self.interactive_grid_ypos = 10

        # Waterfall
        self.interactive_waterfall_increment = 0.05  # new in v1.2.1
        self.interactive_waterfall_shade_under = False  # new in v1.2.1
        self.interactive_waterfall_shade_alpha = 0.25  # new in v1.2.1

        # Mass spectra
        self.interactive_ms_annotations = True
        self.interactive_ms_annotations_color = (0.18, 0.8, 0.44)
        self.interactive_ms_annotations_line_color = (0, 0, 0)
        self.interactive_ms_annotations_transparency = 0.3
        self.interactive_ms_linearize = True
        self.interactive_ms_binSize = 0.1

        self.interactive_ms_annotations_offsetX = 5
        self.interactive_ms_annotations_offsetY = 5
        self.interactive_ms_annotations_fontSize = 10
        self.interactive_ms_annotations_fontWeight = True
        self.interactive_ms_annotations_highlight = False
        self.interactive_ms_annotations_labels = True
        self.interactive_ms_annotations_rotation = 90
        self.interactive_ms_annotations_label_color = (0., 0., 0.)

        # Ticks
        self.interactive_tick_useScientific = True
        self.interactive_tick_precision = 1

        # Legend
        self.interactive_legend = True
        self.interactive_legend_click_policy_choices = ['hide', 'mute']
        self.interactive_legend_click_policy = 'hide'
        self.interactive_legend_location_choices = ["top_left", "top_center", "top_right", "center_right",
                                                    "bottom_right", "bottom_center", "bottom_left", "center_left",
                                                    "center"]  # , "other"]
        self.interactive_legend_location = 'top_left'
        self.interactive_legend_mute_alpha = 0.25
        self.interactive_legend_background_alpha = 0.5
        self.interactive_legend_orientation_choices = ['vertical', 'horizontal']
        self.interactive_legend_orientation = 'vertical'
        self.interactive_legend_font_size = 10

        # Line
        self.interactive_line_style_choices = ['solid', 'dashed', 'dotted', 'dotdash', 'dashdot']
        self.interactive_line_style = 'solid'
        self.interactive_line_width = 2
        self.interactive_line_alpha = 1
        self.interactive_line_shade_under = False  # new in v1.2.1
        self.interactive_line_shade_alpha = 0.25  # new in v1.2.1
        self.interactive_line_color = (0., 0., 0.)  # new in v1.2.1

        # Scatter
        self.interactive_scatter_size = 10
        self.interactive_scatter_alpha = 1.
        self.interactive_scatter_marker_choices = ["circle", "square", "triangle",
                                                  "circle_cross", "square_cross",
                                                  "diamond", "circle_x", "square_x",
                                                  "inverted_triangle", "cross", "x",
                                                  "asterisk"]
        self.interactive_scatter_marker = "circle"
        self.interactive_scatter_sameAsFill = True
        self.interactive_scatter_edge_color = (0., 0., 0.)
        self.interactive_scatter_lineWidth = 1.  # new in v1.2.1

        # bar
        self.interactive_bar_width = 0.1
        self.interactive_bar_alpha = 1.0
        self.interactive_bar_edge_color = (0., 0., 0.)
        self.interactive_bar_sameAsFill = True
        self.interactive_bar_lineWidth = 1.

    def onCheckValues(self, data_type='all'):
        """
        Helper function to fix values that might be inappropriate for certain calculations
        ------
        params:
        ------
        @param data_type (str): determines which variables should be checked
            'all'        :    all variables are checked
            'process'    :    only variables involved in processing are checked
            'plotting'   :    only variables involved in plotting are checked
        """

        if data_type in ['all', 'extract']:
            # Extract
            if self.extract_mzStart == self.extract_mzEnd:
                self.extract_mzEnd = self.extract_mzStart + 1
            if self.extract_mzEnd < self.extract_mzStart:
                self.extract_mzStart, self.extract_mzEnd = self.extract_mzEnd, self.extract_mzStart

            if self.extract_dtStart == self.extract_dtEnd:
                self.extract_dtEnd = self.extract_dtStart + 1
            if self.extract_dtEnd < self.extract_dtStart:
                self.extract_dtStart, self.extract_dtEnd = self.extract_dtEnd, self.extract_dtStart

            if self.extract_rtStart == self.extract_rtEnd:
                self.extract_rtEnd = self.extract_rtStart + 1
            if self.extract_rtEnd < self.extract_rtStart:
                self.extract_rtStart, self.extract_rtEnd = self.extract_rtEnd, self.extract_rtStart

            # Mass spectrum
            if self.ms_mzEnd < self.ms_mzStart:
                self.ms_mzStart, self.ms_mzEnd = self.ms_mzEnd, self.ms_mzStart

            if self.ms_mzBinSize == 0:
                self.ms_mzBinSize = 0.1

            if self.ms_dtmsBinSize == 0:
                self.ms_dtmsBinSize = 0.1

        if data_type in ['all', 'origami']:
            # ORIGAMI
            if self.origami_spv == 0:
                self.origami_spv = 1

            if self.origami_endVoltage < self.origami_startVoltage:
                self.origami_startVoltage, self.origami_endVoltage = self.origami_endVoltage, self.origami_startVoltage

        if data_type in ['all', 'process']:

            # SMOOTHINH
            # mass spectra
            if self.ms_smooth_sigma < 0:
                self.ms_smooth_sigma = 0

            if self.ms_smooth_window % 2 == 0:
                self.ms_smooth_window = self.ms_smooth_window + 1

            if self.ms_smooth_polynomial >= self.ms_smooth_window:
                if self.ms_smooth_polynomial % 2 == 0:
                    self.ms_smooth_window = self.ms_smooth_polynomial + 1
                else:
                    self.ms_smooth_window = self.ms_smooth_polynomial + 2

            # plot 2D
            if self.plot2D_smooth_sigma < 0:
                self.plot2D_smooth_sigma = 0

            if self.plot2D_smooth_window % 2 == 0:
                self.plot2D_smooth_window = self.plot2D_smooth_window + 1

            if self.plot2D_smooth_polynomial >= self.plot2D_smooth_window:
                if self.plot2D_smooth_polynomial % 2 == 0:
                    self.plot2D_smooth_window = self.plot2D_smooth_polynomial + 1
                else:
                    self.plot2D_smooth_window = self.plot2D_smooth_polynomial + 2

    def initilizeColormaps(self):
        self.colormapMode = 0

        mapList = colormaps()  # + cmocean.cmapnames
        self.cmaps2 = sorted(mapList)
#         self.cmocean_cmaps = cmocean.cmapnames

    def initlizePaths(self, return_check=False):
        self.system = platform.system()

        alternative_driftscope_path = os.path.join(self.cwd, self.driftscopePath_dist)
        print(alternative_driftscope_path)
        # Check if driftscope exists
        if not os.path.isdir(self.driftscopePath):
            if not os.path.isdir(alternative_driftscope_path):
                print('Could not find Driftscope path')
                msg = "Could not localise Driftscope directory. Please setup path to Dritscope lib folder. It usually exists under C:\DriftScope\lib"
                dlgBox(exceptionTitle='Could not find Driftscope',
                               exceptionMsg=msg,
                               type="Warning")
                return False
            else:
                self.driftscopePath = alternative_driftscope_path

        if not os.path.isfile(self.driftscopePath + "\imextract.exe"):
            print('Could not find imextract.exe')
            msg = "Could not localise Driftscope imextract.exe program. Please setup path to Dritscope lib folder. It usually exists under C:\DriftScope\lib"
            dlgBox(exceptionTitle='Could not find Driftscope',
                           exceptionMsg=msg,
                           type="Warning")
            return False

        self.origamiPath = ""

        if return_check:
            return True
        else:
            print(("Driftscope Path: {}".format(self.driftscopePath)))

    def getPusherFrequency(self, parameters, mode="V"):
        mode = 'V'
        """           V           W
        600         39.25       75.25
        1200        54.25       106.25
        2000        69.25       137.25
        5000        110.25      216.25
        8000        138.25      273.25
        14000       182.25      363.25
        32000       274.25      547.25
        100000      486.25      547.25
        """
        """
        Check what pusher frequency should be used
        """
        if mode == "V":
            if parameters['endMS'] <= 600:
                parameters['pusherFreq'] = 39.25
            elif 600 < parameters['endMS'] <= 1200:
                parameters['pusherFreq'] = 54.25
            elif 1200 < parameters['endMS'] <= 2000:
                parameters['pusherFreq'] = 69.25
            elif 2000 < parameters['endMS'] <= 5000:
                parameters['pusherFreq'] = 110.25
            elif 5000 < parameters['endMS'] <= 8000:
                parameters['pusherFreq'] = 138.25
            elif 8000 < parameters['endMS'] <= 14000:
                parameters['pusherFreq'] = 182.25
            elif 14000 < parameters['endMS'] <= 32000:
                parameters['pusherFreq'] = 274.25
            elif 32000 < parameters['endMS'] <= 100000:
                parameters['pusherFreq'] = 486.25
        elif mode == "W":
            if parameters['endMS'] <= 600:
                parameters['pusherFreq'] = 75.25
            elif 600 < parameters['endMS'] <= 1200:
                parameters['pusherFreq'] = 106.25
            elif 1200 < parameters['endMS'] <= 2000:
                parameters['pusherFreq'] = 137.25
            elif 2000 < parameters['endMS'] <= 5000:
                parameters['pusherFreq'] = 216.25
            elif 5000 < parameters['endMS'] <= 8000:
                parameters['pusherFreq'] = 273.25
            elif 8000 < parameters['endMS'] <= 14000:
                parameters['pusherFreq'] = 363.25
            elif 14000 < parameters['endMS'] <= 32000:
                parameters['pusherFreq'] = 547.25
            elif 32000 < parameters['endMS'] <= 100000:
                parameters['pusherFreq'] = 547.25

        return parameters

    def importMassLynxInfFile(self, path, manual=False, e=None):
        '''
        Imports information file for selected MassLynx file
        '''
        fileName = "\_extern.inf"
        fileName = ''.join([path, fileName])

        parameters = OrderedDict.fromkeys(["startMS", "endMS", "setMS", "scanTime", "ionPolarity",
                                   "modeSensitivity", "pusherFreq", "corrC", "trapCE"], None)

        if not os.path.isfile(fileName):
            return parameters

        f = open(fileName, 'r')
        i = 0  # hacky way to get the correct collision voltage value
        for line in f:
            if "Start Mass" in line:
                try: parameters['startMS'] = str2num(str(line.split()[2]))
                except Exception: pass
            if "MSMS End Mass" in line:
                try: parameters['endMS'] = str2num(str(line.split()[3]))
                except Exception: pass
            elif "End Mass" in line:
                try: parameters['endMS'] = str2num(str(line.split()[2]))
                except Exception: pass
            if "Set Mass" in line:
                try: parameters['setMS'] = str2num(str(line.split()[2]))
                except Exception: pass
            if "Scan Time (sec)" in line:
                try: parameters['scanTime'] = str2num(str(line.split()[3]))
                except Exception: pass
            if "Polarity" in line:
                try: parameters['ionPolarity'] = str(line.split()[1])
                except Exception: pass
            if "Sensitivity" in line:
                try: parameters['modeSensitivity'] = str(line.split()[1])
                except Exception: pass
            if "Analyser" in line:
                try: parameters['modeAnalyser'] = str(line.split()[1])
                except Exception: pass
            if "EDC Delay Coefficient" in line:
                try:
                    parameters['corrC'] = str2num(str(line.split()[3]))
                except Exception: pass
#             if manual == True:
            if "Trap Collision Energy" in line:
                if i == 1:
                    try: parameters['trapCE'] = str2num(str(line.split()[3]))
                    except Exception: pass
                i += 1
        f.close()
        parameters = self.getPusherFrequency(parameters=parameters, mode="V")

        return parameters

    def importMassLynxHeaderFile(self, path, e=None):
        '''
        Imports information file for selected MassLynx file
        '''
        fileName = "\_HEADER.TXT"
        fileName = ''.join([path, fileName])

        fileInfo = OrderedDict.fromkeys(["SampleDescription"], None)

        if not os.path.isfile(fileName):
            return ""

        try:
            with open(fileName, "r") as f:
                for line in f:
                    if "$$ Sample Description:" in line:
                        splitline = line.split(" ")
                        line = " ".join(splitline[1::])
                        fileInfo['SampleDescription'] = line
                        break
        except UnicodeDecodeError:
            return ""

#         f = open(fileName, 'r')
#         i = 0  # hacky way to get the correct collision voltage value
#         for line in f:
#             if "$$ Sample Description:" in line:
#                 splitline = line.split(" ")
#                 line = " ".join(splitline[1::])
#                 fileInfo['SampleDescription'] = line
#         f.close()

        return fileInfo

    def importOrigamiConfFile(self, path, e=None):
        """
        Tries to import conf file from MassLynx directory
        """
        fileName = "\origami.conf"
        fileName = ''.join([path, fileName])
        parameters = OrderedDict.fromkeys(["method", "spv", "startVoltage",
                                           "endVoltage", "stepVoltage",
                                           "expIncrement", "expPercentage",
                                           "dx", "spvList", "cvList"], "")

        # Check if there is another file with different name
        searchname = ''.join([path, "\*.conf"])
        filelist = []
        for file in glob.glob(searchname):
            filelist.append(file)

        if len(filelist) > 0:
            if filelist[0] == fileName: pass
            else: fileName = filelist[0]

        if os.path.isfile(fileName):
            print('Found ORIGAMI-MS configuration file')
            f = open(fileName, 'r')
            pass
        else:
            print('Did not find any ORIGAMI-MS configuration files')
            return parameters

        for line in f:
            if "method" in line:
                try: parameters['method'] = str(line.split()[1])
                except Exception: pass
            if "start" in line:
                try: parameters['startVoltage'] = str2num(str(line.split()[1]))
                except Exception: pass
            if "spv" in line:
                try: parameters['spv'] = str2int(str(line.split()[1]))
                except Exception: pass
            if "end" in line:
                try: parameters['endVoltage'] = str2num(str(line.split()[1]))
                except Exception: pass
            if "step" in line:
                try: parameters['stepVoltage'] = str2num(str(line.split()[1]))
                except Exception: pass
            if "expIncrement" in line:
                try: parameters['expIncrement'] = str2num(str(line.split()[1]))
                except Exception: pass
            if "expPercentage" in line:
                try: parameters['expPercentage'] = str2num(str(line.split()[1]))
                except Exception: pass
            if "dx" in line:
                try: parameters['dx'] = str2num(str(line.split()[1]))
                except Exception: pass
            if "SPVsList" in line:
                try: parameters['spvList'] = str(line.split()[1::])
                except Exception: pass
            if "CVsList" in line:
                try: parameters['cvList'] = str(line.split()[1::])
                except Exception: pass
        f.close()

        # Also check if there is a list file
        spvCVlist = None
        try:
            spvPath = ''.join([path, "\spvCVlistOut.csv"])
        except Exception:
            pass
        try:
            spvPath = ''.join([path, '\cv.csv'])
        except Exception:
            return parameters

        try:
            print('Found collision voltage list.')
            self.origamiList = np.genfromtxt(spvPath, skip_header=1,
                                             delimiter=',',
                                             filling_values=0)
        except Exception:
            pass

        return parameters

    def saveConfigXML(self, path, evt=None, verbose=True):
        """ Make and save config file in XML format """

        buff = '<?xml version="1.0" encoding="utf-8" ?>\n'
        buff += '<!-- Please refrain from changing the parameter names - this will break things! -->\n'
        buff += '<origamiConfig version="1.0">\n\n'

        # presets
        buff += '  <presets>\n'
        buff += '    <!-- User-specific parameters -->\n'
        buff += '    <param name="operator" value="%s" type="unicode" />\n' % (self.userParameters['operator'])
        buff += '    <param name="contact" value="%s" type="unicode" />\n' % (self.userParameters['contact'])
        buff += '    <param name="institution" value="%s" type="unicode" />\n' % (self.userParameters['institution'])
        buff += '    <param name="instrument" value="%s" type="unicode" />\n' % (self.userParameters['instrument'])
        buff += '  </presets>\n\n'

        # recent files
        buff += '  <recent>\n'
        for item in self.previousFiles:
            buff += '    <path value="%s" format="%s" />\n' % (self._escape(item['file_path']), item['file_type'])
        buff += '  </recent>\n\n'

        # GUI presets
        buff += '  <presets_gui>\n'
        buff += '    <param name="logging" value="%s" type="bool" />\n' % (bool(self.logging))
        buff += '    <param name="threading" value="%s" type="bool" />\n' % (bool(self.threading))
        buff += '    <param name="autoSaveSettings" value="%s" type="bool" />\n' % (bool(self.autoSaveSettings))
        buff += '    <param name="debug" value="%s" type="bool" />\n' % (bool(self.debug))
        buff += '    <param name="quickDisplay" value="%s" type="bool" />\n' % (bool(self.quickDisplay))
        buff += '    <param name="loadCCSAtStart" value="%s" type="bool" />\n' % (bool(self.loadCCSAtStart))
        buff += '    <param name="checkForDriftscopeAtStart" value="%s" type="bool" />\n' % (bool(self.checkForDriftscopeAtStart))
        buff += '    <param name="overrideCombine" value="%s" type="bool" />\n' % (bool(self.overrideCombine))
        buff += '    <param name="useInternalParamsCombine" value="%s" type="bool" />\n' % (bool(self.useInternalParamsCombine))
        buff += '    <param name="overlay_usedProcessed" value="%s" type="bool" />\n' % (bool(self.overlay_usedProcessed))
        buff += '    <param name="import_duplicate_action" value="%s" type="unicode" choices="%s" />\n' % (self.import_duplicate_action, ["override", "merge", "duplicate"])
        buff += '    <param name="import_duplicate_ask" value="%s" type="bool" />\n' % (bool(self.import_duplicate_ask))
        buff += '  </presets_gui>\n\n'

        # Plot sizes in GUI
        buff += '  <presets_gui_plotSizes>\n'
        for key, __ in sorted(self._plotSettings.items()):
            ps = self._plotSettings[key]
            buff += '    <param name="%s" left_axes="%.2f" bottom_axes="%.2f" width_axes="%.2f" height_axes="%.2f" left_save="%.2f" bottom_save="%.2f" width_save="%.2f" height_save="%.2f" width_resize="%.2f" height_resize="%.2f" width_gui="%.2f" height_gui="%.2f" default_name="%s" type="float" />\n' % (key,
                                                                                                                                                                                                                                                                                                                ps['axes_size'][0],
                                                                                                                                                                                                                                                                                                                ps['axes_size'][1],
                                                                                                                                                                                                                                                                                                                ps['axes_size'][2],
                                                                                                                                                                                                                                                                                                                ps['axes_size'][3],
                                                                                                                                                                                                                                                                                                                ps['save_size'][0],
                                                                                                                                                                                                                                                                                                                ps['save_size'][1],
                                                                                                                                                                                                                                                                                                                ps['save_size'][2],
                                                                                                                                                                                                                                                                                                                ps['save_size'][3],
                                                                                                                                                                                                                                                                                                                ps['resize_size'][0],
                                                                                                                                                                                                                                                                                                                ps['resize_size'][1],
                                                                                                                                                                                                                                                                                                                ps['gui_size'][0],
                                                                                                                                                                                                                                                                                                                ps['gui_size'][1],
                                                                                                                                                                                                                                                                                                                ps['default_name'])
        buff += '  </presets_gui_plotSizes>\n\n'

#         buff += '  <presets_gui_peaklistPanel>\n'
#         for item in self._peakListSettings:
#             buff += '    <param name="%s" order="%d" width="%d" show="%s" type="mixed" />\n' % (item['name'], int(item['order']), int(item['width']), bool(item['show']))
#         buff += '  </presets_gui_peaklistPanel>\n\n'
#
#         buff += '  <presets_gui_textPanel>\n'
#         for item in self._textlistSettings:
#             buff += '    <param name="%s" order="%d" width="%d" show="%s" type="mixed" />\n' % (item['name'], int(item['order']), int(item['width']), bool(item['show']))
#         buff += '  </presets_gui_textPanel>\n\n'
#
#         buff += '  <presets_gui_multipleFilesPanel>\n'
#         for item in self._multipleFilesSettings:
#             buff += '    <param name="%s" order="%d" width="%d" show="%s" type="mixed" />\n' % (str(item['name']), int(item['order']), int(item['width']), bool(item['show']))
#         buff += '  </presets_gui_multipleFilesPanel>\n\n'
#
#         buff += '  <presets_gui_interactivePanel>\n'
#         for item in self._interactiveSettings:
#             buff += '    <param name="%s" order="%d" width="%d" show="%s" type="mixed" />\n' % (item['name'], int(item['order']), int(item['width']), bool(item['show']))
#         buff += '  </presets_gui_interactivePanel>\n\n'

        # GUI settings
        buff += '  <presets_gui_aui_settings>\n'
        for key in sorted(self._windowSettings.keys()):
            item = self._windowSettings[key]
            if key != "Toolbar":
                buff += '    <param title="%s" gripper="%s" caption="%s" close_button="%s" floating="%s" show="%s" type="mixed" />\n' % (
                    item['title'], bool(item['gripper']), str(item['caption']), bool(item['close_button']), bool(item['floating']), bool(item['show']))
            else:
                buff += '    <param title="%s" gripper="%s" orientation="%s" close_button="%s" left_position="%s" top_position="%s" left_dockable="%s" right_dockable="%s" top_dockable="%s" bottom_dockable="%s" show="%s" type="mixed" />\n' % (
                    item['title'], bool(item['gripper']), item['orientation'], bool(item['close_button']), bool(item['left_position']), bool(item['top_position']), bool(item['left_dockable']),
                    bool(item['right_dockable']), bool(item['top_dockable']), bool(item['bottom_dockable']), bool(item['show']))
        buff += '  </presets_gui_aui_settings>\n\n'

        # Plot presets - zoom
        buff += '  <plot_presets_zoom>\n'
        buff += '    <param name="_plots_grid_show" value="%s" type="bool" />\n' % (bool(self._plots_grid_show))
        buff += '    <param name="_plots_grid_color" value="%s" type="color" />\n' % (str(self._plots_grid_color))
        buff += '    <param name="_plots_grid_line_width" value="%.2f" type="float" />\n' % (float(self._plots_grid_line_width))
        buff += '    <param name="_plots_extract_color" value="%s" type="color" />\n' % (str(self._plots_extract_color))
        buff += '    <param name="_plots_extract_line_width" value="%.2f" type="float" />\n' % (float(self._plots_extract_line_width))
        buff += '    <param name="_plots_extract_crossover_1D" value="%.2f" type="float" />\n' % (float(self._plots_extract_crossover_1D))
        buff += '    <param name="_plots_extract_crossover_2D" value="%.2f" type="float" />\n' % (float(self._plots_extract_crossover_2D))
        buff += '    <param name="_plots_zoom_vertical_color" value="%s" type="color" />\n' % (str(self._plots_zoom_vertical_color))
        buff += '    <param name="_plots_zoom_horizontal_color" value="%s" type="color" />\n' % (str(self._plots_zoom_horizontal_color))
        buff += '    <param name="_plots_zoom_box_color" value="%s" type="color" />\n' % (str(self._plots_zoom_box_color))
        buff += '    <param name="_plots_zoom_line_width" value="%.2f" type="float" />\n' % (float(self._plots_zoom_line_width))
        buff += '    <param name="_plots_zoom_crossover" value="%.2f" type="float" />\n' % (float(self._plots_zoom_crossover))
        buff += '  </plot_presets_zoom>\n\n'

        # Plot presets - annotations
        buff += '  <plot_presets_annotations>\n'
        buff += '    <param name="annotation_charge_std_dev" value="%.2f" type="float" />\n' % (float(self.annotation_charge_std_dev))
        buff += '    <param name="annotation_arrow_cap_length" value="%.2f" type="float" />\n' % (float(self.annotation_arrow_cap_length))
        buff += '    <param name="annotation_arrow_cap_width" value="%.2f" type="float" />\n' % (float(self.annotation_arrow_cap_width))
        buff += '    <param name="annotation_arrow_line_width" value="%.2f" type="float" />\n' % (float(self.annotation_arrow_line_width))
        buff += '    <param name="annotation_arrow_line_style" value="%s" type="unicode" choices="%s" />\n' % (self.annotation_arrow_line_style, self.origami_acquisition_choices)
        buff += '    <param name="annotation_label_y_offset" value="%.2f" type="float" />\n' % (float(self.annotation_label_y_offset))
        buff += '    <param name="annotation_zoom_y_multiplier" value="%.2f" type="float" />\n' % (float(self.annotation_zoom_y_multiplier))
        buff += '    <param name="annotation_zoom_y" value="%s" type="bool" />\n' % (bool(self.annotation_zoom_y))
        buff += '    <param name="annotation_show_vline" value="%s" type="bool" />\n' % (bool(self.annotation_show_vline))
        buff += '    <param name="annotation_label_horz" value="%s" type="unicode" choices="%s" />\n' % (self.annotation_label_horz, self.horizontal_alignment_list)
        buff += '    <param name="annotation_label_vert" value="%s" type="unicode" choices="%s" />\n' % (self.annotation_label_vert, self.vertical_alignment_list)
        buff += '    <param name="annotation_label_font_size" value="%s" type="unicode" choices="%s" />\n' % (self.annotation_label_font_size, self.label_fontsize_list)
        buff += '    <param name="annotation_label_font_weight" value="%s" type="unicode" choices="%s" />\n' % (self.annotation_label_font_weight, self.label_fontweight_list)
        buff += '    <param name="annotation_patch_transparency" value="%.2f" type="float" />\n' % (float(self.annotation_patch_transparency))
        buff += '    <param name="annotation_patch_width" value="%.2f" type="float" />\n' % (float(self.annotation_patch_width))
        buff += '  </plot_presets_annotations>\n\n'

        # Custom colors
        buff += '  <custom_colors>\n'
        for i in self.customColors:
            try: color_text = "[{:d}, {:d}, {:d}]".format(int(self.customColors[i][0]), int(self.customColors[i][1]), int(self.customColors[i][2]))
            except Exception: color_text = str(self.customColors[i])
            buff += '    <param name="{}" value="{}" type="color" />\n'.format('_'.join(["color", str(i)]), color_text)
        buff += '  </custom_colors>\n\n'

        # Process presets - overlay
        buff += '  <process_presets_overlay>\n'
        buff += '    <param name="overlay_defaultMask" value="%.2f" type="float" />\n' % (float(self.overlay_defaultMask))
        buff += '    <param name="overlay_defaultAlpha" value="%.2f" type="float" />\n' % (float(self.overlay_defaultAlpha))
        buff += '    <param name="overlay_smooth1DRT" value="%.2f" type="float" />\n' % (float(self.overlay_smooth1DRT))
        buff += '  </process_presets_overlay>\n\n'

        # Process - extract
        buff += '  <process_presets_extract>\n'
        buff += '    <param name="extract_massSpectra" value="%s" type="bool" />\n' % (bool(self.extract_massSpectra))
        buff += '    <param name="extract_chromatograms" value="%s" type="bool" />\n' % (bool(self.extract_chromatograms))
        buff += '    <param name="extract_driftTime1D" value="%s" type="bool" />\n' % (bool(self.extract_driftTime1D))
        buff += '    <param name="extract_driftTime2D" value="%s" type="bool" />\n' % (bool(self.extract_driftTime2D))
        buff += '    <param name="extract_mzStart" value="%.2f" type="float" />\n' % (float(self.extract_mzStart))
        buff += '    <param name="extract_mzEnd" value="%.2f" type="float" />\n' % (float(self.extract_mzEnd))
        buff += '    <param name="extract_rtStart" value="%.2f" type="float" />\n' % (float(self.extract_rtStart))
        buff += '    <param name="extract_rtEnd" value="%.2f" type="float" />\n' % (float(self.extract_rtEnd))
        buff += '    <param name="extract_dtStart" value="%.2f" type="float" />\n' % (float(self.extract_dtStart))
        buff += '    <param name="extract_dtEnd" value="%.2f" type="float" />\n' % (float(self.extract_dtEnd))
        buff += '  </process_presets_extract>\n\n'

        # Process - origami
        buff += '  <process_presets_origami>\n'
        buff += '    <param name="origami_acquisition" value="%s" type="unicode" choices="%s" />\n' % (self.origami_acquisition, self.origami_acquisition_choices)
        buff += '    <param name="origami_startScan" value="%d" type="int" />\n' % (int(self.origami_startScan))
        buff += '    <param name="origami_spv" value="%d" type="int" />\n' % (int(self.origami_spv))
        buff += '    <param name="origami_startVoltage" value="%.2f" type="float" />\n' % (float(self.origami_startVoltage))
        buff += '    <param name="origami_endVoltage" value="%.2f" type="float" />\n' % (float(self.origami_endVoltage))
        buff += '    <param name="origami_stepVoltage" value="%.2f" type="float" />\n' % (float(self.origami_stepVoltage))
        buff += '    <param name="origami_boltzmannOffset" value="%.2f" type="float" />\n' % (float(self.origami_boltzmannOffset))
        buff += '    <param name="origami_exponentialPercentage" value="%.2f" type="float" />\n' % (float(self.origami_exponentialPercentage))
        buff += '    <param name="origami_exponentialIncrement" value="%.2f" type="float" />\n' % (float(self.origami_exponentialIncrement))
        buff += '  </process_presets_origami>\n\n'

        # Process - mass spectrum
        buff += '  <process_presets_unidec>\n'
        buff += '    <!-- Pre-processing parameters -->\n'
        buff += '    <param name="unidec_mzStart" value="%d" type="float" />\n' % (float(self.unidec_mzStart))
        buff += '    <param name="unidec_mzEnd" value="%.2f" type="float" />\n' % (float(self.unidec_mzEnd))
        buff += '    <param name="unidec_mzBinSize" value="%.2f" type="float" />\n' % (float(self.unidec_mzBinSize))
        buff += '    <param name="unidec_gaussianFilter" value="%.2f" type="float" />\n' % (float(self.unidec_gaussianFilter))
        buff += '    <param name="unidec_accelerationV" value="%.2f" type="float" />\n' % (float(self.unidec_accelerationV))
        buff += '    <param name="unidec_linearization" value="%s" type="unicode" choices="%s" />\n' % (self.unidec_linearization, list(self.unidec_linearization_choices.keys()))
        buff += '    <!-- UniDec engine parameters -->\n'
        buff += '    <param name="unidec_zStart" value="%d" type="int" />\n' % (int(self.unidec_zStart))
        buff += '    <param name="unidec_zEnd" value="%d" type="int" />\n' % (int(self.unidec_zEnd))
        buff += '    <param name="unidec_mwStart" value="%.2f" type="float" />\n' % (float(self.unidec_mwStart))
        buff += '    <param name="unidec_mwEnd" value="%.2f" type="float" />\n' % (float(self.unidec_mwEnd))
        buff += '    <param name="unidec_mwFrequency" value="%.2f" type="float" />\n' % (float(self.unidec_mwFrequency))
        buff += '    <param name="unidec_peakWidth" value="%.2f" type="float" />\n' % (float(self.unidec_peakWidth))
        buff += '    <param name="unidec_peakFunction" value="%s" type="unicode" choices="%s" />\n' % (self.unidec_peakFunction, list(self.unidec_peakFunction_choices.keys()))
        buff += '    <!-- Peak picking parameters -->\n'
        buff += '    <param name="unidec_peakDetectionWidth" value="%.2f" type="float" />\n' % (float(self.unidec_peakDetectionWidth))
        buff += '    <param name="unidec_peakDetectionThreshold" value="%.2f" type="float" />\n' % (float(self.unidec_peakDetectionThreshold))
        buff += '    <param name="unidec_peakNormalization" value="%s" type="unicode" choices="%s" />\n' % (self.unidec_peakNormalization, list(self.unidec_peakNormalization_choices.keys()))
        buff += '    <param name="unidec_lineSeparation" value="%.2f" type="float" />\n' % (float(self.unidec_lineSeparation))
        buff += '    <!-- Plotting parameters -->\n'
        buff += '    <param name="unidec_plot_panel_view" value="%s" type="unicode" />\n' % (str(self.unidec_plot_panel_view))
        buff += '    <param name="unidec_maxShown_individualLines" value="%d" type="int" />\n' % (int(self.unidec_maxShown_individualLines))
        buff += '    <param name="unidec_plot_fit_lineColor" value="%s" type="color" />\n' % (str(self.unidec_plot_fit_lineColor))
        buff += '    <param name="unidec_plot_MW_showMarkers" value="%s" type="bool" />\n' % (bool(self.unidec_plot_MW_showMarkers))
        buff += '    <param name="unidec_plot_MW_markerSize" value="%d" type="int" />\n' % (int(self.unidec_plot_MW_markerSize))
        buff += '    <param name="unidec_plot_isolatedMS_markerSize" value="%d" type="int" />\n' % (int(self.unidec_plot_isolatedMS_markerSize))
        buff += '    <param name="unidec_plot_bar_markerSize" value="%d" type="int" />\n' % (int(self.unidec_plot_bar_markerSize))
        buff += '    <param name="unidec_plot_bar_width" value="%.2f" type="float" />\n' % (float(self.unidec_plot_bar_width))
        buff += '    <param name="unidec_plot_bar_alpha" value="%.2f" type="float" />\n' % (float(self.unidec_plot_bar_alpha))
        buff += '    <param name="unidec_plot_bar_edge_color" value="%s" type="color" />\n' % (str(self.unidec_plot_bar_edge_color))
        buff += '    <param name="unidec_plot_bar_sameAsFill" value="%s" type="bool" />\n' % (bool(self.unidec_plot_bar_sameAsFill))
        buff += '    <param name="unidec_plot_bar_lineWidth" value="%d" type="int" />\n' % (int(self.unidec_plot_bar_lineWidth))
        buff += '    <param name="unidec_plot_contour_levels" value="%d" type="int" />\n' % (int(self.unidec_plot_contour_levels))
        buff += '    <param name="unidec_plot_color_scheme" value="%s" type="unicode" choices="%s" />\n' % (self.unidec_plot_color_scheme, ["Color scheme", "Colormap"])
        buff += '    <param name="unidec_plot_colormap" value="%s" type="unicode" />\n' % (str(self.unidec_plot_colormap))
        buff += '    <param name="unidec_plot_palette" value="%s" type="unicode" />\n' % (str(self.unidec_plot_palette))
        buff += '  </process_presets_unidec>\n\n'

        # Process - peak fitting
        buff += '  <process_presets_fitting>\n'
        buff += '    <param name="fit_type" value="%s" type="unicode" choices="%s" />\n' % (self.fit_type, self.fit_type_choices)
        buff += '    <param name="fit_highlight" value="%s" type="bool" />\n' % (bool(self.fit_highlight))
        buff += '    <param name="fit_addPeaks" value="%s" type="bool" />\n' % (bool(self.fit_addPeaks))
        buff += '    <param name="fit_xaxis_limit" value="%s" type="bool" />\n' % (bool(self.fit_xaxis_limit))
        buff += '    <param name="fit_highRes_isotopicFit" value="%s" type="bool" />\n' % (bool(self.fit_highRes_isotopicFit))
        buff += '    <param name="fit_smoothPeaks" value="%s" type="bool" />\n' % (bool(self.fit_smoothPeaks))
        buff += '    <param name="fit_highRes" value="%s" type="bool" />\n' % (bool(self.fit_highRes))
        buff += '    <param name="fit_window" value="%d" type="int" />\n' % (int(self.fit_window))
        buff += '    <param name="fit_threshold" value="%.2f" type="float" />\n' % (float(self.fit_threshold))
        buff += '    <param name="fit_width" value="%.2f" type="float" />\n' % (float(self.fit_width))
        buff += '    <param name="fit_asymmetric_ratio" value="%.2f" type="float" />\n' % (float(self.fit_asymmetric_ratio))
        buff += '    <param name="fit_highRes_window" value="%d" type="int" />\n' % (int(self.fit_highRes_window))
        buff += '    <param name="fit_smooth_sigma" value="%.2f" type="float" />\n' % (float(self.fit_smooth_sigma))
        buff += '    <param name="fit_highRes_threshold" value="%.2f" type="float" />\n' % (float(self.fit_highRes_threshold))
        buff += '    <param name="fit_highRes_width" value="%.2f" type="float" />\n' % (float(self.fit_highRes_width))
        buff += '  </process_presets_fitting>\n\n'

        buff += '  <process_presets_binning>\n'
        buff += '    <param name="ms_enable_in_RT" value="%s" type="bool" />\n' % (bool(self.ms_enable_in_RT))
        buff += '    <param name="ms_enable_in_MML_start" value="%s" type="bool" />\n' % (bool(self.ms_enable_in_MML_start))
        buff += '    <param name="ms_mzStart" value="%.2f" type="float" />\n' % (float(self.ms_mzStart))
        buff += '    <param name="ms_mzEnd" value="%.2f" type="float" />\n' % (float(self.ms_mzEnd))
        buff += '    <param name="ms_mzBinSize" value="%.2f" type="float" />\n' % (float(self.ms_mzBinSize))
        buff += '    <param name="ms_dtmsBinSize" value="%.2f" type="float" />\n' % (float(self.ms_dtmsBinSize))
        buff += '    <param name="ms_linearization_mode" value="%s" type="unicode" choices="%s" />\n' % (self.ms_linearization_mode, self.ms_linearization_mode_choices)
        buff += '    <param name="ms_auto_range" value="%s" type="bool" />\n' % (bool(self.ms_auto_range))
        buff += '    <param name="ms_process_crop" value="%s" type="bool" />\n' % (bool(self.ms_process_crop))
        buff += '    <param name="ms_process_linearize" value="%s" type="bool" />\n' % (bool(self.ms_process_linearize))
        buff += '    <param name="ms_process_smooth" value="%s" type="bool" />\n' % (bool(self.ms_process_smooth))
        buff += '    <param name="ms_process_threshold" value="%s" type="bool" />\n' % (bool(self.ms_process_threshold))
        buff += '    <param name="ms_process_normalize" value="%s" type="bool" />\n' % (bool(self.ms_process_normalize))
        buff += '  </process_presets_binning>\n\n'

        # Process - mass spectrum
        buff += '  <process_presets_ms>\n'
        buff += '    <param name="ms_normalize" value="%s" type="bool" />\n' % (bool(self.ms_normalize))
        buff += '    <param name="ms_normalize_mode" value="%s" type="unicode" choices="%s" />\n' % (self.ms_normalize_mode, self.ms_normalize_choices)
        buff += '    <param name="ms_smooth_mode" value="%s" type="unicode" choices="%s" />\n' % (self.ms_smooth_mode, self.ms_smooth_choices)
        buff += '    <param name="ms_smooth_polynomial" value="%d" type="int" />\n' % (int(self.ms_smooth_polynomial))
        buff += '    <param name="ms_smooth_window" value="%d" type="int" />\n' % (int(self.ms_smooth_window))
        buff += '    <param name="ms_smooth_sigma" value="%.2f" type="float" />\n' % (float(self.ms_smooth_sigma))
        buff += '    <param name="ms_threshold" value="%.2f" type="float" />\n' % (float(self.ms_threshold))
        buff += '  </process_presets_ms>\n\n'

        # Plot presets - compare mass spectra
        buff += '  <process_compare_mass_spectra>\n'
        buff += '    <param name="lineColour_MS1" value="%s" type="color" />\n' % (str(self.lineColour_MS1))
        buff += '    <param name="lineStyle_MS1" value="%s" type="unicode" choices="%s" />\n' % (self.lineStyle_MS1, self.lineStylesList)
        buff += '    <param name="lineTransparency_MS1" value="%.2f" type="float" />\n' % (float(self.lineTransparency_MS1))
        buff += '    <param name="lineColour_MS2" value="%s" type="color" />\n' % (str(self.lineColour_MS2))
        buff += '    <param name="lineStyle_MS2" value="%s" type="unicode" choices="%s" />\n' % (self.lineStyle_MS2, self.lineStylesList)
        buff += '    <param name="lineTransparency_MS2" value="%.2f" type="float" />\n' % (float(self.lineTransparency_MS2))
        buff += '  </process_compare_mass_spectra>\n\n'

        # Process - plot 2D
        buff += '  <process_presets_uvpd>\n'
        buff += '    <param name="uvpd_peak_show_markers" value="%s" type="bool" />\n' % (bool(self.uvpd_peak_show_markers))
        buff += '    <param name="uvpd_peak_show_patches" value="%s" type="bool" />\n' % (bool(self.uvpd_peak_show_patches))
        buff += '    <param name="uvpd_peak_show_labels" value="%s" type="bool" />\n' % (bool(self.uvpd_peak_show_labels))
        buff += '    <param name="uvpd_peak_laser_on" value="%s" type="color" />\n' % (str(self.uvpd_peak_laser_on))
        buff += '    <param name="uvpd_peak_laser_off" value="%s" type="color" />\n' % (str(self.uvpd_peak_laser_off))
        buff += '    <param name="uvpd_peak_first_index" value="%d" type="int" />\n' % (int(self.uvpd_peak_first_index))
        buff += '    <param name="uvpd_peak_buffer_width" value="%.2f" type="float" />\n' % (float(self.uvpd_peak_buffer_width))
        buff += '    <param name="uvpd_peak_finding_threshold" value="%.2f" type="float" />\n' % (float(self.uvpd_peak_finding_threshold))
        buff += '  </process_presets_uvpd>\n\n'

        # Process - UVPD
        buff += '  <process_presets_plot2D>\n'
        buff += '    <param name="plot2D_normalize" value="%s" type="bool" />\n' % (bool(self.plot2D_normalize))
        buff += '    <param name="plot2D_normalize_mode" value="%s" type="unicode" choices="%s" />\n' % (self.plot2D_normalize_mode, self.plot2D_normalize_choices)
        buff += '    <param name="plot2D_smooth_mode" value="%s" type="unicode" choices="%s" />\n' % (self.plot2D_smooth_mode, self.plot2D_smooth_choices)
        buff += '    <param name="plot2D_smooth_polynomial" value="%d" type="int" />\n' % (int(self.plot2D_smooth_polynomial))
        buff += '    <param name="plot2D_smooth_window" value="%d" type="int" />\n' % (int(self.plot2D_smooth_window))
        buff += '    <param name="plot2D_smooth_sigma" value="%.2f" type="float" />\n' % (float(self.plot2D_smooth_sigma))
        buff += '    <param name="plot2D_threshold" value="%.2f" type="float" />\n' % (float(self.plot2D_threshold))
        buff += '  </process_presets_plot2D>\n\n'

        # Plot presets - rmsd
        buff += '  <plot_presets_rmsd>\n'
        buff += '    <param name="rmsd_position" value="%s" type="unicode" choices="%s" />\n' % (self.rmsd_position, self.rmsd_position_choices)
        buff += '    <param name="rmsd_fontSize" value="%.2f" type="float" />\n' % (float(self.rmsd_fontSize))
        buff += '    <param name="rmsd_fontWeight" value="%s" type="bool" />\n' % (bool(self.rmsd_fontWeight))
        buff += '    <param name="rmsd_color" value="%s" type="color" />\n' % (str(self.rmsd_color))
        buff += '    <param name="rmsd_rotation_X" value="%.2f" type="float" />\n' % (float(self.rmsd_rotation_X))
        buff += '    <param name="rmsd_rotation_Y" value="%.2f" type="float" />\n' % (float(self.rmsd_rotation_Y))
        buff += '    <param name="rmsd_lineColour" value="%s" type="color" />\n' % (str(self.rmsd_lineColour))
        buff += '    <param name="rmsd_lineTransparency" value="%.2f" type="float" />\n' % (float(self.rmsd_lineTransparency))
        buff += '    <param name="rmsd_underlineColor" value="%s" type="color" />\n' % (str(self.rmsd_underlineColor))
        buff += '    <param name="rmsd_underlineTransparency" value="%.2f" type="float" />\n' % (float(self.rmsd_underlineTransparency))
        buff += '    <param name="rmsd_lineWidth" value="%.2f" type="float" />\n' % (float(self.rmsd_lineWidth))
        buff += '    <param name="rmsd_lineStyle" value="%s" type="unicode" choices="%s" />\n' % (self.rmsd_lineStyle, self.lineStylesList)
        buff += '    <param name="rmsd_lineHatch" value="%s" type="unicode" choices="%s" />\n' % (self.rmsd_lineHatch, self.lineHatchList)
        buff += '    <param name="rmsd_hspace" value="%.2f" type="float" />\n' % (float(self.rmsd_hspace))
        buff += '  </plot_presets_rmsd>\n\n'

        # Plot presets - waterfall
        buff += '  <plot_presets_waterfall>\n'
        buff += '    <param name="waterfall" value="%s" type="bool" />\n' % (bool(self.waterfall))
        buff += '    <param name="waterfallOffset" value="%.2f" type="float" />\n' % (float(self.waterfall_offset))
        buff += '    <param name="waterfall_increment" value="%.2f" type="float" />\n' % (float(self.waterfall_increment))
        buff += '    <param name="waterfall_reverse" value="%s" type="bool" />\n' % (bool(self.waterfall_reverse))
        buff += '    <param name="waterfall_lineWidth" value="%.2f" type="float" />\n' % (float(self.waterfall_lineWidth))
        buff += '    <param name="waterfall_lineStyle" value="%s" type="unicode" choices="%s" />\n' % (self.waterfall_lineStyle, self.lineStylesList)
        buff += '    <param name="waterfall_color" value="%s" type="color" />\n' % (str(self.waterfall_color))
        buff += '    <param name="waterfall_useColormap" value="%s" type="bool" />\n' % (bool(self.waterfall_useColormap))
        buff += '    <param name="waterfall_normalize" value="%s" type="bool" />\n' % (bool(self.waterfall_normalize))
        buff += '    <param name="waterfall_label_format" value="%s" type="unicode" choices="%s" />\n' % (self.waterfall_label_format, self.waterfall_label_format_choices)
        buff += '    <param name="waterfall_color_value" value="%s" type="unicode" choices="%s" />\n' % (self.waterfall_color_value, self.waterfall_color_choices)
        buff += '    <param name="waterfall_add_labels" value="%s" type="bool" />\n' % (bool(self.waterfall_add_labels))
        buff += '    <param name="waterfall_shade_under" value="%s" type="bool" />\n' % (bool(self.waterfall_shade_under))
        buff += '    <param name="waterfall_shade_under_transparency" value="%.2f" type="float" />\n' % (float(self.waterfall_shade_under_transparency))
        buff += '    <param name="waterfall_shade_under_nlimit" value="%d" type="int" />\n' % (int(self.waterfall_shade_under_nlimit))
        buff += '    <param name="waterfall_labels_frequency" value="%.2f" type="float" />\n' % (float(self.waterfall_labels_frequency))
        buff += '    <param name="waterfall_labels_x_offset" value="%.2f" type="float" />\n' % (float(self.waterfall_labels_x_offset))
        buff += '    <param name="waterfall_labels_y_offset" value="%.2f" type="float" />\n' % (float(self.waterfall_labels_y_offset))
        buff += '    <param name="waterfall_label_fontSize" value="%.2f" type="float" />\n' % (float(self.waterfall_label_fontSize))
        buff += '    <param name="waterfall_label_fontWeight" value="%s" type="bool" />\n' % (bool(self.waterfall_label_fontWeight))
        buff += '  </plot_presets_waterfall>\n\n'

        # Plot presets - violin
        buff += '  <plot_presets_violin>\n'
        buff += '    <param name="violin_normalize" value="%s" type="bool" />\n' % (bool(self.violin_normalize))
        buff += '    <param name="violin_orientation" value="%s" type="unicode" choices="%s" />\n' % (self.violin_orientation, self.violin_orientation_choices)
        buff += '    <param name="violin_label_format" value="%s" type="unicode" choices="%s" />\n' % (self.violin_label_format, self.violin_label_format_choices)
        buff += '    <param name="violin_color_value" value="%s" type="unicode" choices="%s" />\n' % (self.violin_color_value, self.violin_color_choices)
        buff += '    <param name="violin_line_sameAsShade" value="%s" type="bool" />\n' % (bool(self.violin_line_sameAsShade))
        buff += '    <param name="violin_shade_under_transparency" value="%.2f" type="float" />\n' % (float(self.violin_shade_under_transparency))
        buff += '    <param name="violin_nlimit" value="%d" type="int" />\n' % (int(self.violin_nlimit))
        buff += '    <param name="violin_labels_frequency" value="%.2f" type="float" />\n' % (float(self.violin_labels_frequency))
        buff += '    <param name="violin_min_percentage" value="%.2f" type="float" />\n' % (float(self.violin_min_percentage))
        buff += '    <param name="violin_spacing" value="%.2f" type="float" />\n' % (float(self.violin_spacing))
        buff += '    <param name="violin_lineWidth" value="%.2f" type="float" />\n' % (float(self.violin_lineWidth))
        buff += '    <param name="violin_lineStyle" value="%s" type="unicode" choices="%s" />\n' % (self.violin_lineStyle, self.lineStylesList)
        buff += '  </plot_presets_violin>\n\n'

        # Plot presets - bar
        buff += '  <plot_presets_bar>\n'
        buff += '    <param name="bar_sameAsFill" value="%s" type="bool" />\n' % (bool(self.bar_sameAsFill))
        buff += '    <param name="bar_width" value="%.2f" type="float" />\n' % (float(self.bar_width))
        buff += '    <param name="bar_alpha" value="%.2f" type="float" />\n' % (float(self.bar_alpha))
        buff += '    <param name="bar_lineWidth" value="%.2f" type="float" />\n' % (float(self.bar_lineWidth))
        buff += '    <param name="bar_edge_color" value="%s" type="color" />\n' % (str(self.bar_edge_color))
        buff += '  </plot_presets_bar>\n\n'

        # Plot presets - legend
        buff += '  <plot_presets_legend>\n'
        buff += '    <param name="legend" value="%s" type="bool" />\n' % (bool(self.legend))
        buff += '    <param name="legendFancyBox" value="%s" type="bool" />\n' % (bool(self.legendFancyBox))
        buff += '    <param name="legendMarkerFirst" value="%s" type="bool" />\n' % (bool(self.legendMarkerFirst))
        buff += '    <param name="legendFrame" value="%s" type="bool" />\n' % (bool(self.legendFrame))
        buff += '    <param name="legendPosition" value="%s" type="unicode" choices="%s" />\n' % (self.legendPosition, self.legendPositionChoice)
        buff += '    <param name="legendFontSize" value="%s" type="unicode" choices="%s" />\n' % (self.legendFontSize, self.legendFontChoice)
        buff += '    <param name="legendColumns" value="%d" type="int" />\n' % (int(self.legendColumns))
        buff += '    <param name="legendNumberMarkers" value="%d" type="int" />\n' % (int(self.legendNumberMarkers))
        buff += '    <param name="legendMarkerSize" value="%.2f" type="float" />\n' % (float(self.legendMarkerSize))
        buff += '    <param name="legendAlpha" value="%.2f" type="float" />\n' % (float(self.legendAlpha))
        buff += '    <param name="legendLineWidth" value="%.2f" type="float" />\n' % (float(self.legendLineWidth))
        buff += '  </plot_presets_legend>\n\n'

        # Plot presets - colorbar
        buff += '  <plot_presets_colorbar>\n'
        buff += '    <param name="colorbar" value="%s" type="bool" />\n' % (bool(self.colorbar))
        buff += '    <param name="colorbarPosition" value="%s" type="unicode" choices="%s" />\n' % (self.colorbarPosition, self.colorbarChoices)
        buff += '    <param name="colorbarMinPoints" value="%d" type="int" />\n' % (int(self.colorbarMinPoints))
        buff += '    <param name="colorbarWidth" value="%.2f" type="float" />\n' % (float(self.colorbarWidth))
        buff += '    <param name="colorbarPad" value="%.2f" type="float" />\n' % (float(self.colorbarPad))
        buff += '    <param name="colorbarLabelSize" value="%.2f" type="float" />\n' % (float(self.colorbarLabelSize))
        buff += '  </plot_presets_colorbar>\n\n'

        # Plot presets - 1D plots
        buff += '  <plot_presets_plot_1D>\n'
        buff += '    <param name="lineColour_1D" value="%s" type="color" />\n' % (str(self.lineColour_1D))
        buff += '    <param name="lineWidth_1D" value="%.2f" type="float" />\n' % (float(self.lineWidth_1D))
        buff += '    <param name="frameWidth_1D" value="%d" type="float" />\n' % (float(self.frameWidth_1D))
        buff += '    <param name="labelPad_1D" value="%d" type="float" />\n' % (float(self.labelPad_1D))
        buff += '    <param name="lineStyle_1D" value="%s" type="unicode" choices="%s" />\n' % (self.lineStyle_1D, self.lineStylesList)
        buff += '    <param name="markerColor_1D" value="%s" type="color" />\n' % (str(self.markerColor_1D))
        buff += '    <param name="markerTransparency_1D" value="%.2f" type="float" />\n' % (float(self.markerTransparency_1D))
        buff += '    <param name="markerSize_1D" value="%.2f" type="float" />\n' % (float(self.markerSize_1D))
        buff += '    <param name="markerShape_1D" value="%s" type="unicode" choices="%s" />\n' % (self.markerShape_1D, list(self.markerShapeDict.keys()))
        buff += '    <param name="markerShapeTXT_1D" value="%s" type="unicode" choices="%s" />\n' % (self.markerShapeTXT_1D, list(self.markerShapeDict.keys()))
        buff += '    <param name="axisOnOff_1D" value="%s" type="bool" />\n' % (bool(self.axisOnOff_1D))
        buff += '    <param name="annotationFontWeight_1D" value="%s" type="bool" />\n' % (bool(self.annotationFontWeight_1D))
        buff += '    <param name="annotationFontSize_1D" value="%.2f" type="float" />\n' % (float(self.annotationFontSize_1D))
        buff += '    <param name="tickFontWeight_1D" value="%s" type="bool" />\n' % (bool(self.tickFontWeight_1D))
        buff += '    <param name="tickFontSize_1D" value="%.2f" type="float" />\n' % (float(self.tickFontSize_1D))
        buff += '    <param name="labelFontWeight_1D" value="%s" type="bool" />\n' % (bool(self.labelFontWeight_1D))
        buff += '    <param name="labelFontSize_1D" value="%.2f" type="float" />\n' % (float(self.labelFontSize_1D))
        buff += '    <param name="titleFontWeight_1D" value="%s" type="bool" />\n' % (bool(self.titleFontWeight_1D))
        buff += '    <param name="titleFontSize_1D" value="%.2f" type="float" />\n' % (float(self.titleFontSize_1D))
        buff += '    <param name="spines_left_1D" value="%s" type="bool" />\n' % (bool(self.spines_left_1D))
        buff += '    <param name="spines_right_1D" value="%s" type="bool" />\n' % (bool(self.spines_right_1D))
        buff += '    <param name="spines_top_1D" value="%s" type="bool" />\n' % (bool(self.spines_top_1D))
        buff += '    <param name="spines_bottom_1D" value="%s" type="bool" />\n' % (bool(self.spines_bottom_1D))
        buff += '    <param name="ticks_left_1D" value="%s" type="bool" />\n' % (bool(self.ticks_left_1D))
        buff += '    <param name="ticks_right_1D" value="%s" type="bool" />\n' % (bool(self.ticks_right_1D))
        buff += '    <param name="ticks_top_1D" value="%s" type="bool" />\n' % (bool(self.ticks_top_1D))
        buff += '    <param name="ticks_bottom_1D" value="%s" type="bool" />\n' % (bool(self.ticks_bottom_1D))
        buff += '    <param name="tickLabels_left_1D" value="%s" type="bool" />\n' % (bool(self.tickLabels_left_1D))
        buff += '    <param name="tickLabels_right_1D" value="%s" type="bool" />\n' % (bool(self.tickLabels_right_1D))
        buff += '    <param name="tickLabels_top_1D" value="%s" type="bool" />\n' % (bool(self.tickLabels_top_1D))
        buff += '    <param name="tickLabels_bottom_1D" value="%s" type="bool" />\n' % (bool(self.tickLabels_bottom_1D))
        buff += '  </plot_presets_plot_1D>\n\n'

        # Plot presets - 2D plots
        buff += '  <plot_presets_plot_2D>\n'
        buff += '    <param name="interpolation" value="%s" type="unicode" choices="%s" />\n' % (self.interpolation, self.comboInterpSelectChoices)
        buff += '    <param name="plotType" value="%s" type="unicode" choices="%s" />\n' % (self.plotType, self.imageType2D)
        buff += '    <param name="currentCmap" value="%s" type="unicode" choices="%s" />\n' % (self.currentCmap, self.cmaps2)
        buff += '    <param name="useCurrentCmap" value="%s" type="bool" />\n' % (bool(self.useCurrentCmap))
        buff += '    <param name="minCmap" value="%.2f" type="float" />\n' % (float(self.minCmap))
        buff += '    <param name="midCmap" value="%.2f" type="float" />\n' % (float(self.midCmap))
        buff += '    <param name="maxCmap" value="%.2f" type="float" />\n' % (float(self.maxCmap))
        buff += '    <param name="labelPad_2D" value="%.2f" type="float" />\n' % (float(self.labelPad_2D))
        buff += '    <param name="axisOnOff_2D" value="%s" type="bool" />\n' % (bool(self.axisOnOff_2D))
        buff += '    <param name="annotationFontWeight_2D" value="%s" type="bool" />\n' % (bool(self.annotationFontWeight_2D))
        buff += '    <param name="annotationFontSize_2D" value="%.2f" type="float" />\n' % (float(self.annotationFontSize_2D))
        buff += '    <param name="tickFontWeight_2D" value="%s" type="bool" />\n' % (bool(self.tickFontWeight_2D))
        buff += '    <param name="tickFontSize_2D" value="%.2f" type="float" />\n' % (float(self.tickFontSize_2D))
        buff += '    <param name="labelFontWeight_2D" value="%s" type="bool" />\n' % (bool(self.labelFontWeight_2D))
        buff += '    <param name="labelFontSize_2D" value="%.2f" type="float" />\n' % (float(self.labelFontSize_2D))
        buff += '    <param name="titleFontWeight_2D" value="%s" type="bool" />\n' % (bool(self.titleFontWeight_2D))
        buff += '    <param name="titleFontSize_2D" value="%.2f" type="float" />\n' % (float(self.titleFontSize_2D))
        buff += '    <param name="spines_left_2D" value="%s" type="bool" />\n' % (bool(self.spines_left_2D))
        buff += '    <param name="spines_right_2D" value="%s" type="bool" />\n' % (bool(self.spines_right_2D))
        buff += '    <param name="spines_top_2D" value="%s" type="bool" />\n' % (bool(self.spines_top_2D))
        buff += '    <param name="spines_bottom_2D" value="%s" type="bool" />\n' % (bool(self.spines_bottom_2D))
        buff += '    <param name="ticks_left_2D" value="%s" type="bool" />\n' % (bool(self.ticks_left_2D))
        buff += '    <param name="ticks_right_2D" value="%s" type="bool" />\n' % (bool(self.ticks_right_2D))
        buff += '    <param name="ticks_top_2D" value="%s" type="bool" />\n' % (bool(self.ticks_top_2D))
        buff += '    <param name="ticks_bottom_2D" value="%s" type="bool" />\n' % (bool(self.ticks_bottom_2D))
        buff += '    <param name="tickLabels_left_2D" value="%s" type="bool" />\n' % (bool(self.tickLabels_left_2D))
        buff += '    <param name="tickLabels_right_2D" value="%s" type="bool" />\n' % (bool(self.tickLabels_right_2D))
        buff += '    <param name="tickLabels_top_2D" value="%s" type="bool" />\n' % (bool(self.tickLabels_top_2D))
        buff += '    <param name="tickLabels_bottom_2D" value="%s" type="bool" />\n' % (bool(self.tickLabels_bottom_2D))
        buff += '  </plot_presets_plot_2D>\n\n'

        # Plot presets - 3D plots
        buff += '  <plot_presets_plot_3D>\n'
        buff += '    <param name="showGrids_3D" value="%s" type="bool" />\n' % (bool(self.showGrids_3D))
        buff += '    <param name="shade_3D" value="%s" type="bool" />\n' % (bool(self.shade_3D))
        buff += '    <param name="ticks_3D" value="%s" type="bool" />\n' % (bool(self.ticks_3D))
        buff += '    <param name="spines_3D" value="%s" type="bool" />\n' % (bool(self.spines_3D))
        buff += '    <param name="labels_3D" value="%s" type="bool" />\n' % (bool(self.labels_3D))
        buff += '    <param name="labelPad_3D" value="%.2f" type="float" />\n' % (float(self.labelPad_3D))
        buff += '    <param name="markerEdgeUseSame_3D" value="%s" type="bool" />\n' % (bool(self.markerEdgeUseSame_3D))
        buff += '    <param name="markerColor_3D" value="%s" type="color" />\n' % (str(self.markerColor_3D))
        buff += '    <param name="markerTransparency_3D" value="%.2f" type="float" />\n' % (float(self.markerTransparency_3D))
        buff += '    <param name="markerSize_3D" value="%.2f" type="float" />\n' % (float(self.markerSize_3D))
        buff += '    <param name="markerShape_3D" value="%s" type="unicode" choices="%s" />\n' % (self.markerShape_3D, list(self.markerShapeDict.keys()))
        buff += '    <param name="markerShapeTXT_3D" value="%s" type="unicode" choices="%s" />\n' % (self.markerShapeTXT_3D, list(self.markerShapeDict.keys()))
        buff += '    <param name="markerEdgeColor_3D" value="%s" type="color" />\n' % (str(self.markerEdgeColor_3D))
        buff += '    <param name="annotationFontWeight_3D" value="%s" type="bool" />\n' % (bool(self.annotationFontWeight_3D))
        buff += '    <param name="annotationFontSize_3D" value="%.2f" type="float" />\n' % (float(self.annotationFontSize_3D))
        buff += '    <param name="tickFontWeight_3D" value="%s" type="bool" />\n' % (bool(self.tickFontWeight_3D))
        buff += '    <param name="tickFontSize_3D" value="%.2f" type="float" />\n' % (float(self.tickFontSize_3D))
        buff += '    <param name="labelFontWeight_3D" value="%s" type="bool" />\n' % (bool(self.labelFontWeight_3D))
        buff += '    <param name="labelFontSize_3D" value="%.2f" type="float" />\n' % (float(self.labelFontSize_3D))
        buff += '    <param name="titleFontWeight_3D" value="%s" type="bool" />\n' % (bool(self.titleFontWeight_3D))
        buff += '    <param name="titleFontSize_3D" value="%.2f" type="float" />\n' % (float(self.titleFontSize_3D))
        buff += '  </plot_presets_plot_3D>\n\n'

        buff += '  <exportParams>\n'
        buff += '    <param name="dpi" value="%d" type="int" />\n' % (int(self.dpi))
        buff += '    <param name="imageWidthInch" value="%d" type="int" />\n' % (int(self.imageWidthInch))
        buff += '    <param name="imageHeightInch" value="%d" type="int" />\n' % (int(self.imageHeightInch))
        buff += '    <param name="transparent" value="%s" type="bool" />\n' % (bool(self.transparent))
        buff += '    <param name="colorbar" value="%s" type="bool" />\n' % (bool(self.colorbar))
        buff += '    <param name="imageFormat" value="%s" type="unicode" choices="%s" />\n' % (str(self.imageFormat), self.imageFormatType)
        buff += '    <param name="saveDelimiterTXT" value="%s" type="unicode" choices="%s" />\n' % (self.saveDelimiterTXT, list(self.textOutputDict.keys()))
        buff += '    <param name="normalizeMultipleMS" value="%s" type="bool" />\n' % (bool(self.normalizeMultipleMS))
        buff += '  </exportParams>\n\n'

        buff += '  <presets_interactive_toolsets>\n'
        buff += '    <!-- wheelType_choices="%s" -->\n' % self.interactive_wheelZoom_choices
        buff += '    <!-- activeDrag_choices="%s" -->\n' % self.interactive_activeDragTools_choices
        buff += '    <!-- activeWheel_choices="%s" -->\n' % self.interactive_activeWheelTools_choices
        buff += '    <!-- activeInspect_choices="%s" -->\n' % self.interactive_activeHoverTools_choices
        for key, __ in sorted(self.interactiveToolsOnOff.items()):
            ts = self.interactiveToolsOnOff[key]
            buff += '    <param name="%s" hover="%s" save="%s" pan="%s" boxzoom="%s" boxzoom_horizontal="%s" boxzoom_vertical="%s" crosshair="%s" reset="%s" wheel="%s" wheelType="%s" activeDrag="%s" activeWheel="%s" activeInspect="%s" type="mixed" />\n' % (key, bool(ts['hover']), bool(ts['save']), bool(ts['pan']), bool(ts['boxzoom']), bool(ts.get('boxzoom_horizontal', True)), bool(ts.get('boxzoom_vertical', False)), bool(ts['crosshair']), bool(ts['reset']), bool(ts['wheel']), ts['wheelType'], ts['activeDrag'], ts['activeWheel'], ts['activeInspect'])
        buff += '  </presets_interactive_toolsets>\n\n'

        buff += '  <presets_interactive_pageLayouts>\n'
        buff += '    <!-- layout_choices="%s" -->\n' % self.interactive_pageLayout_choices
        for key, __ in sorted(self.pageDict.items()):
            pl = self.pageDict[key]
            buff += '    <param page_name="%s" name="%s" layout="%s" rows="%s" columns="%s" grid_share_tools="%s" type="mixed" />\n' % (key,
                                                                                                                                                                  pl['name'],
                                                                                                                                                                  pl['layout'],
                                                                                                                                                                  pl.get('rows', None),
                                                                                                                                                                  pl['columns'],
                                                                                                                                                                  pl.get('grid_share_tools', True))
        buff += '  </presets_interactive_pageLayouts>\n\n'

        buff += '  <presets_interactive_gui>\n'
        buff += '    <!-- GENERAL PARAMETERS -->\n'
        buff += '    <param name="interactive_override_defaults" value="%s" type="bool" />\n' % (bool(self.interactive_override_defaults))
        buff += '    <param name="openInteractiveOnSave" value="%s" type="bool" />\n' % (bool(self.openInteractiveOnSave))
        buff += '    <param name="interactive_cvd_cmap" value="%s"  choices="%s" type="unicode" />\n' % (str(self.interactive_cvd_cmap), self.interactive_cvd_cmap_choices)

        buff += '    <!-- JAVA SCRIPT PARAMETERS -->\n'
        buff += '    <param name="interactive_custom_scripts" value="%s" type="bool" />\n' % (bool(self.interactive_custom_scripts))
        buff += '    <param name="interactive_custom_events" value="%s" type="bool" />\n' % (bool(self.interactive_custom_events))
        buff += '    <param name="interactive_custom_position" value="%s"  choices="%s" type="unicode" />\n' % (str(self.interactive_custom_position), ["left", "right", "below", "above"])

        buff += '    <!-- FRAME PARAMETERS -->\n'
        buff += '    <param name="figHeight" value="%d" type="int" />\n' % (int(self.figHeight))
        buff += '    <param name="figWidth" value="%d" type="int" />\n' % (int(self.figWidth))
        buff += '    <param name="figHeight1D" value="%d" type="int" />\n' % (int(self.figHeight1D))
        buff += '    <param name="figWidth1D" value="%d" type="int" />\n' % (int(self.figWidth1D))
        buff += '    <param name="interactive_outline_alpha" value="%.1f" type="float" />\n' % (float(self.interactive_outline_alpha))
        buff += '    <param name="interactive_outline_width" value="%.1f" type="float" />\n' % (float(self.interactive_outline_width))
        buff += '    <param name="interactive_border_min_right" value="%d" type="int" />\n' % (int(self.interactive_border_min_right))
        buff += '    <param name="interactive_border_min_left" value="%d" type="int" />\n' % (int(self.interactive_border_min_left))
        buff += '    <param name="interactive_border_min_top" value="%d" type="int" />\n' % (int(self.interactive_border_min_top))
        buff += '    <param name="interactive_border_min_bottom" value="%d" type="int" />\n' % (int(self.interactive_border_min_bottom))
        buff += '    <param name="layoutModeDoc" value="%s" type="unicode" />\n' % (str(self.layoutModeDoc))
        buff += '    <param name="interactive_grid_line" value="%s" type="bool" />\n' % (bool(self.interactive_grid_line))
        buff += '    <param name="interactive_background_color" value="%s" type="color" />\n' % (str(self.interactive_background_color))
        buff += '    <param name="interactive_grid_line_color" value="%s" type="color" />\n' % (str(self.interactive_grid_line_color))

        buff += '    <!-- TOOLS PARAMETERS -->\n'
        buff += '    <param name="toolsLocation" value="%s" type="unicode" />\n' % (str(self.toolsLocation))
        buff += '    <param name="activeDrag" value="%s" type="unicode" />\n' % (str(self.activeDrag))
        buff += '    <param name="activeWheel" value="%s" type="unicode" />\n' % (str(self.activeWheel))
        buff += '    <param name="activeInspect" value="%s" type="unicode" />\n' % (str(self.activeInspect))

        buff += '    <!-- OVERLAY PARAMETERS -->\n'
        buff += '    <param name="plotLayoutOverlay" value="%s" type="unicode" />\n' % (str(self.plotLayoutOverlay))
        buff += '    <param name="linkXYaxes" value="%s" type="bool" />\n' % (bool(self.linkXYaxes))
        buff += '    <param name="interactive_grid_label" value="%s" type="bool" />\n' % (bool(self.interactive_grid_label))
        buff += '    <param name="interactive_grid_label_weight" value="%s" type="bool" />\n' % (bool(self.interactive_grid_label_weight))
        buff += '    <param name="interactive_grid_label_size" value="%.2f" type="float" />\n' % (float(self.interactive_grid_label_size))
        buff += '    <param name="interactive_grid_xpos" value="%.2f" type="float" />\n' % (float(self.interactive_grid_xpos))
        buff += '    <param name="interactive_grid_ypos" value="%.2f" type="float" />\n' % (float(self.interactive_grid_ypos))
        buff += '    <param name="interactive_grid_label_color" value="%s" type="color" />\n' % (str(self.interactive_grid_label_color))

        buff += '    <!-- FONT PARAMETERS -->\n'
        buff += '    <param name="interactive_title_fontSize" value="%d" type="int" />\n' % (int(self.interactive_title_fontSize))
        buff += '    <param name="interactive_title_weight" value="%s" type="bool" />\n' % (bool(self.interactive_title_weight))
        buff += '    <param name="interactive_label_fontSize" value="%d" type="int" />\n' % (int(self.interactive_label_fontSize))
        buff += '    <param name="interactive_label_weight" value="%s" type="bool" />\n' % (bool(self.interactive_label_weight))
        buff += '    <param name="interactive_tick_fontSize" value="%d" type="int" />\n' % (int(self.interactive_tick_fontSize))
        buff += '    <param name="interactive_annotation_fontSize" value="%d" type="int" />\n' % (int(self.interactive_annotation_fontSize))
        buff += '    <param name="interactive_annotation_weight" value="%s" type="bool" />\n' % (bool(self.interactive_annotation_weight))
        buff += '    <param name="interactive_annotation_color" value="%s" type="color" />\n' % (str(self.interactive_annotation_color))
        buff += '    <param name="interactive_annotation_background_color" value="%s" type="color" />\n' % (str(self.interactive_annotation_background_color))
        buff += '    <param name="interactive_annotation_alpha" value="%.2f" type="float" />\n' % (float(self.interactive_annotation_alpha))

        buff += '    <!-- COLORBAR PARAMETERS -->\n'
        buff += '    <param name="interactive_colorbar" value="%s" type="bool" />\n' % (bool(self.interactive_colorbar))
        buff += '    <param name="interactive_colorbar_useScientific" value="%s" type="bool" />\n' % (bool(self.interactive_colorbar_useScientific))
        buff += '    <param name="interactive_colorbar_label_offset" value="%d" type="int" />\n' % (int(self.interactive_colorbar_label_offset))
        buff += '    <param name="interactive_colorbar_precision" value="%d" type="int" />\n' % (int(self.interactive_colorbar_precision))
        buff += '    <param name="interactive_colorbar_offset_x" value="%d" type="int" />\n' % (int(self.interactive_colorbar_offset_x))
        buff += '    <param name="interactive_colorbar_offset_y" value="%d" type="int" />\n' % (int(self.interactive_colorbar_offset_y))
        buff += '    <param name="interactive_colorbar_width" value="%d" type="int" />\n' % (int(self.interactive_colorbar_width))
        buff += '    <param name="interactive_colorbar_padding" value="%d" type="int" />\n' % (int(self.interactive_colorbar_padding))
        buff += '    <param name="interactive_colorbar_location" value="%s"  choices="%s" type="unicode" />\n' % (str(self.interactive_colorbar_location), self.interactive_colorbarPosition_choices)
        buff += '    <param name="interactive_colorbar_orientation" value="%s" type="unicode" />\n' % (str(self.interactive_colorbar_orientation))
        buff += '    <param name="interactive_colorbar_edge_color" value="%s" type="color" />\n' % (str(self.interactive_colorbar_edge_color))
        buff += '    <param name="interactive_colorbar_edge_width" value="%.2f" type="float" />\n' % (float(self.interactive_colorbar_edge_width))
        buff += '    <param name="interactive_colorbar_label_fontSize" value="%.2f" type="float" />\n' % (float(self.interactive_colorbar_label_fontSize))
        buff += '    <param name="interactive_colorbar_title_fontSize" value="%.2f" type="float" />\n' % (float(self.interactive_colorbar_title_fontSize))
        buff += '    <param name="interactive_colorbar_title_weight" value="%s" type="bool" />\n' % (bool(self.interactive_colorbar_title_weight))
        buff += '    <param name="interactive_colorbar_label_weight" value="%s" type="bool" />\n' % (bool(self.interactive_colorbar_label_weight))
        buff += '    <param name="interactive_colorbar_modify_ticks" value="%s" type="bool" />\n' % (bool(self.interactive_colorbar_modify_ticks))

        buff += '    <!-- TICK PARAMETERS -->\n'
        buff += '    <param name="interactive_tick_precision" value="%d" type="int" />\n' % (int(self.interactive_tick_precision))
        buff += '    <param name="interactive_tick_useScientific" value="%s" type="bool" />\n' % (bool(self.interactive_tick_useScientific))

        buff += '    <!-- LEGEND PARAMETERS -->\n'
        buff += '    <param name="interactive_legend" value="%s" type="bool" />\n' % (bool(self.interactive_legend))
        buff += '    <param name="interactive_legend_click_policy" value="%s"  choices="%s" type="unicode" />\n' % (str(self.interactive_legend_click_policy), self.interactive_legend_click_policy_choices)
        buff += '    <param name="interactive_legend_location" value="%s"  choices="%s" type="unicode" />\n' % (str(self.interactive_legend_location), self.interactive_legend_location_choices)
        buff += '    <param name="interactive_legend_orientation" value="%s"  choices="%s" type="unicode" />\n' % (str(self.interactive_legend_orientation), self.interactive_legend_orientation_choices)
        buff += '    <param name="interactive_legend_mute_alpha" value="%.2f" type="float" />\n' % (float(self.interactive_legend_mute_alpha))
        buff += '    <param name="interactive_legend_background_alpha" value="%.2f" type="float" />\n' % (float(self.interactive_legend_background_alpha))
        buff += '    <param name="interactive_legend_font_size" value="%.2f" type="float" />\n' % (float(self.interactive_legend_font_size))

        buff += '    <!-- LINE PARAMETERS -->\n'
        buff += '    <param name="hoverVline" value="%s" type="bool" />\n' % (bool(self.hoverVline))
        buff += '    <param name="interactive_line_style" value="%s"  choices="%s" type="unicode" />\n' % (str(self.interactive_line_style), self.interactive_line_style_choices)
        buff += '    <param name="interactive_line_width" value="%.2f" type="float" />\n' % (float(self.interactive_line_width))
        buff += '    <param name="interactive_line_alpha" value="%.2f" type="float" />\n' % (float(self.interactive_line_alpha))
        buff += '    <param name="interactive_line_color" value="%s" type="color" />\n' % (str(self.interactive_line_color))
        buff += '    <param name="interactive_line_shade_alpha" value="%.2f" type="float" />\n' % (float(self.interactive_line_shade_alpha))
        buff += '    <param name="interactive_line_shade_under" value="%s" type="bool" />\n' % (bool(self.interactive_line_shade_under))

        buff += '    <!-- LINEARIZE PARAMETERS -->\n'
        buff += '    <param name="interactive_ms_linearize" value="%s" type="bool" />\n' % (bool(self.hoverVline))
        buff += '    <param name="interactive_ms_binSize" value="%.2f" type="float" />\n' % (float(self.interactive_ms_binSize))

        buff += '    <!-- BAR PARAMETERS -->\n'
        buff += '    <param name="interactive_bar_sameAsFill" value="%s" type="bool" />\n' % (bool(self.interactive_bar_sameAsFill))
        buff += '    <param name="interactive_bar_width" value="%.2f" type="float" />\n' % (float(self.interactive_bar_width))
        buff += '    <param name="interactive_bar_alpha" value="%.2f" type="float" />\n' % (float(self.interactive_bar_alpha))
        buff += '    <param name="interactive_bar_lineWidth" value="%.2f" type="float" />\n' % (float(self.interactive_bar_lineWidth))
        buff += '    <param name="interactive_bar_edge_color" value="%s" type="color" />\n' % (str(self.interactive_bar_edge_color))

        buff += '    <!-- SCATTER PARAMETERS -->\n'
        buff += '    <param name="interactive_scatter_sameAsFill" value="%s" type="bool" />\n' % (bool(self.interactive_scatter_sameAsFill))
        buff += '    <param name="interactive_scatter_size" value="%d" type="int" />\n' % (int(self.interactive_scatter_size))
        buff += '    <param name="interactive_scatter_alpha" value="%.2f" type="float" />\n' % (float(self.interactive_scatter_alpha))
        buff += '    <param name="interactive_scatter_edge_color" value="%s" type="color" />\n' % (str(self.interactive_scatter_edge_color))
        buff += '    <param name="interactive_scatter_marker" value="%s"  choices="%s" type="unicode" />\n' % (str(self.interactive_scatter_marker), self.interactive_scatter_marker_choices)
        buff += '    <param name="interactive_scatter_lineWidth" value="%.2f" type="float" />\n' % (float(self.interactive_scatter_lineWidth))

        buff += '    <!-- ANNOTATIONS PARAMETERS -->\n'
        buff += '    <param name="interactive_ms_annotations" value="%s" type="bool" />\n' % (bool(self.interactive_ms_annotations))
        buff += '    <param name="interactive_ms_annotations_color" value="%s" type="color" />\n' % (str(self.interactive_ms_annotations_color))
        buff += '    <param name="interactive_ms_annotations_line_color" value="%s" type="color" />\n' % (str(self.interactive_ms_annotations_line_color))
        buff += '    <param name="interactive_ms_annotations_transparency" value="%.2f" type="float" />\n' % (float(self.interactive_ms_annotations_transparency))
        buff += '    <param name="interactive_ms_annotations_fontWeight" value="%s" type="bool" />\n' % (bool(self.interactive_ms_annotations_fontWeight))
        buff += '    <param name="interactive_ms_annotations_highlight" value="%s" type="bool" />\n' % (bool(self.interactive_ms_annotations_highlight))
        buff += '    <param name="interactive_ms_annotations_labels" value="%s" type="bool" />\n' % (bool(self.interactive_ms_annotations_labels))
        buff += '    <param name="interactive_ms_annotations_offsetX" value="%.2f" type="float" />\n' % (float(self.interactive_ms_annotations_offsetX))
        buff += '    <param name="interactive_ms_annotations_offsetY" value="%.2f" type="float" />\n' % (float(self.interactive_ms_annotations_offsetY))
        buff += '    <param name="interactive_ms_annotations_fontSize" value="%.2f" type="float" />\n' % (float(self.interactive_ms_annotations_fontSize))
        buff += '    <param name="interactive_ms_annotations_rotation" value="%.2f" type="float" />\n' % (float(self.interactive_ms_annotations_rotation))
        buff += '    <param name="interactive_ms_annotations_label_color" value="%s" type="color" />\n' % (str(self.interactive_ms_annotations_label_color))

        buff += '    <!-- WATERFALL PARAMETERS -->\n'
        buff += '    <param name="interactive_waterfall_shade_under" value="%s" type="bool" />\n' % (bool(self.interactive_waterfall_shade_under))
        buff += '    <param name="interactive_waterfall_shade_alpha" value="%.2f" type="float" />\n' % (float(self.interactive_waterfall_shade_alpha))
        buff += '    <param name="interactive_waterfall_increment" value="%.2f" type="float" />\n' % (float(self.interactive_waterfall_increment))

        buff += '  </presets_interactive_gui>\n\n'

        buff += '</origamiConfig>'

        # save config file
        try:
            save = open(path, 'w+')
            save.write(buff)
            save.close()
            logger.info('Saved configuration parameters to {}'.format(path))
            return True
        except Exception as e:
            logger.error("Failed to save configuration parameters")
            logger.error(e)
            return False

    def loadConfigXML(self, path, evt=None):

        try:
            document = xml.dom.minidom.parse(path)
        except IOError:
            print('Missing configuration file')
            self.saveConfigXML(path='configOut.xml', evt=None)
            return
        except xml.parsers.expat.ExpatError as e:
            print(e)
            print('Syntax error - please load XML config file')
            return

        presetsTags = document.getElementsByTagName('presets')
        if presetsTags:
            xmlTags = presetsTags[0].getElementsByTagName('param')
            for item in xmlTags:
                # Get values
                name = item.getAttribute('name')
                value = item.getAttribute('value')
                type = item.getAttribute('type')
                # Get value of proper type
                value = self.setProperType(value=value, type=type)
                # Set attribute
                setattr(self, name, value)
        # Update user parameters
        self.userParameters['operator'] = self.operator
        self.userParameters['contact'] = self.contact
        self.userParameters['institution'] = self.institution
        self.userParameters['instrument'] = self.instrument

        tagList = ['process_presets_overlay', 'process_presets_binning',
                   'process_compare_mass_spectra', 'process_presets_uvpd',
                   'process_presets_origami', 'process_presets_fitting',
                   'process_presets_unidec', 'process_presets_ms', 'process_presets_plot2D',
                   'process_presets_extract', 'plot_presets_legend',
                   'plot_presets_colorbar', 'plot_presets_plot_1D',
                   'plot_presets_plot_2D', 'plot_presets_plot_3D',
                   'plot_presets_rmsd', 'plot_presets_violin',
                   'plot_presets_bar',
                   'plot_presets_waterfall', 'plot_presets_zoom',
                   'plot_presets_annotations',
                   'presets_gui', 'exportParams', 'presets_interactive_gui'
                   ]

        for tag in tagList:
            mainTags = document.getElementsByTagName(tag)
            if mainTags:
                xmlTags = mainTags[0].getElementsByTagName('param')
                for item in xmlTags:
                    # Get values
                    name = item.getAttribute('name')
                    value = item.getAttribute('value')
                    type = item.getAttribute('type')
                    # Get value of proper type
                    value = self.setProperType(value=value, type=type)
                    # Set attribute
                    setattr(self, name, value)

        mainTags = document.getElementsByTagName('custom_colors')
        if mainTags:
            xmlTags = mainTags[0].getElementsByTagName('param')
            custom_colors = {}
            for item in xmlTags:
                # Get values
                name = item.getAttribute('name')
                tmp_name = name.split('_')
                name = str2int(tmp_name[1])
                value = item.getAttribute('value')
                type = item.getAttribute('type')
                # Get value of proper type
                value = self.setProperType(value=value, type=type)
                # Set attribute
                custom_colors[name] = value
            self.customColors = custom_colors

        recentTags = document.getElementsByTagName('recent')
        if recentTags:
            pathTags = recentTags[0].getElementsByTagName('path')
            if pathTags:
                self.previousFiles = []
                for pathTag in pathTags:
                    self.previousFiles.append({'file_path':pathTag.getAttribute('value'),
                                               'file_type':pathTag.getAttribute('format')
                                               })

        plotSizesTags = document.getElementsByTagName('presets_gui_plotSizes')
        if plotSizesTags:
            xmlTags = plotSizesTags[0].getElementsByTagName('param')
            for item in xmlTags:
                # Get values
                name = item.getAttribute('name')
                axes_size, save_size, resize_size, gui_size = [], [], [], []
                for sizer in ['left_axes', 'bottom_axes', 'width_axes', 'height_axes']:
                    value = item.getAttribute(sizer)
                    type = item.getAttribute('type')
                    # Get value of proper type
                    value = self.setProperType(value=value, type=type)
                    axes_size.append(value)
                for sizer in ['left_save', 'bottom_save', 'width_save', 'height_save']:
                    value = item.getAttribute(sizer)
                    type = item.getAttribute('type')
                    # Get value of proper type
                    value = self.setProperType(value=value, type=type)
                    save_size.append(value)
                for sizer in ['width_resize', 'height_resize']:
                    value = item.getAttribute(sizer)
                    type = item.getAttribute('type')
                    # Get value of proper type
                    value = self.setProperType(value=value, type=type)
                    resize_size.append(value)
                for sizer in ['width_gui', 'height_gui']:
                    value = item.getAttribute(sizer)
                    type = item.getAttribute('type')
                    # Get value of proper type
                    try:
                        value = self.setProperType(value=value, type=type)
                        gui_size.append(value)
                    except ValueError:
                        gui_size = self._plotSettings[name]['gui_size']
                for sizer in ['default_name']:
                    value = item.getAttribute(sizer)
                    type = "unicode"
                    # Get value of proper type
                    value = self.setProperType(value=value, type=type)
                    default_name = value
                # Set attribute
                self._plotSettings[name]['axes_size'] = axes_size
                self._plotSettings[name]['save_size'] = save_size
                self._plotSettings[name]['resize_size'] = resize_size
                self._plotSettings[name]['gui_size'] = gui_size
                self._plotSettings[name]['default_name'] = default_name
#                 {'axes_size':axes_size,
#                                             'save_size':save_size,
#                                             'resize_size':resize_size,
#                                             'gui_size':gui_size,
#                                             'default_name':default_name}

        interactiveTags = document.getElementsByTagName('presets_interactive_toolsets')
        if interactiveTags:
            xmlTags = interactiveTags[0].getElementsByTagName('param')
            for item in xmlTags:
                # Get values
                name = item.getAttribute('name')
                tools_dict = {}
                for key_item in ['hover', 'save', 'pan',
                                 'boxzoom', 'crosshair',
                                 'reset', 'wheel', 'boxzoom_vertical',
                                 'boxzoom_horizontal']:
                    try:
                        value = item.getAttribute(key_item)
                        # Get value of proper type
                        value = self.setProperType(value=value, type='bool')
                        tools_dict[key_item] = value
                    except ValueError:
                        pass
                for key_item in ['wheelType', 'activeDrag', 'activeWheel', 'activeInspect']:
                    value = item.getAttribute(key_item)
                    # Get value of proper type
                    value = self.setProperType(value=value, type='str')
                    tools_dict[key_item] = value

                if "boxzoom_vertical" not in tools_dict:
                    tools_dict['boxzoom_vertical'] = False

                if "boxzoom_horizontal" not in tools_dict:
                    tools_dict['boxzoom_horizontal'] = True
                self.interactiveToolsOnOff[name] = tools_dict

        interactiveTags = document.getElementsByTagName('presets_interactive_pageLayouts')
        if interactiveTags:
            xmlTags = interactiveTags[0].getElementsByTagName('param')
            for item in xmlTags:
                # Get values
                page_name = item.getAttribute('page_name')
                page_dict = {}
                for key_item in ['name', 'layout', 'rows', 'columns', 'grid_share_tools',
#                                  'header', 'footnote'
                                 ]:
                    value = item.getAttribute(key_item)
                    # Get value of proper type
                    value = self.setProperType(value=value, type='str')
                    if value in ['None', 'none'] and key_item in ['rows', 'columns']:
                        value = None
                    elif key_item in ['rows', 'columns']:
                        value = int(value)
                    elif key_item in ["grid_share_tools"]:
                        value = str2bool(value)
#                     elif key_item in ["header", "footnote"]:
#                         value = str(value)
                    page_dict[key_item] = value
                self.pageDict[page_name] = page_dict

#         tagList = {'presets_gui_textPanel':'_textlistSettings',
#                    'presets_gui_peaklistPanel':'_peakListSettings',
#                    'presets_gui_multipleFilesPanel':'_multipleFilesSettings',
#                    'presets_gui_interactivePanel':'_interactiveSettings'}
#
#         for tag, tag_name in tagList.items():
#             mainTags = document.getElementsByTagName(tag)
#             if mainTags:
#                 xmlTags = mainTags[0].getElementsByTagName('param')
#                 gui_params = getattr(self, tag_name)
#                 for item in xmlTags:
#                     # Get values
#                     name = item.getAttribute('name')
#                     order = int(item.getAttribute('order'))
#                     width = int(item.getAttribute('width'))
#                     show = str2bool(item.getAttribute('show'))
#                     for i in range(len(gui_params)):
#                         if gui_params[i]['name'] == name:
#                             gui_params[i] = {'name':name, 'order':order, 'width':width, 'show':show}
#                 # Set attribute
#                 setattr(self, tag_name, gui_params)

            gui_settings = document.getElementsByTagName('presets_gui_aui_settings')
            if gui_settings:
                xmlTags = gui_settings[0].getElementsByTagName('param')
                gui_params = {}
                for item in xmlTags:
                    title = item.getAttribute('title')
                    if title != "Toolbar":
                        gripper = str2bool(item.getAttribute('gripper'))
                        caption = str2bool(item.getAttribute('caption'))
                        close_button = str2bool(item.getAttribute('close_button'))
                        floating = str2bool(item.getAttribute('floating'))
                        show = str2bool(item.getAttribute('show'))
                        self._windowSettings[title] = {'title':title, 'gripper':gripper, 'caption':caption,
                                                       'close_button':close_button, 'floating':floating,
                                                       'show':show}
                    else:
                        orientation = item.getAttribute('orientation')
                        gripper = str2bool(item.getAttribute('gripper'))
                        close_button = str2bool(item.getAttribute('close_button'))
                        left_position = str2bool(item.getAttribute('left_position'))
                        top_position = str2bool(item.getAttribute('top_position'))
                        left_dockable = str2bool(item.getAttribute('left_dockable'))
                        right_dockable = str2bool(item.getAttribute('right_dockable'))
                        top_dockable = str2bool(item.getAttribute('top_dockable'))
                        bottom_dockable = str2bool(item.getAttribute('bottom_dockable'))
                        show = str2bool(item.getAttribute('show'))
                        self._windowSettings[title] = {'title':title, 'orientation':orientation, 'gripper':gripper,
                                                       'close_button':close_button, 'left_position':left_position,
                                                       'top_position':top_position, 'left_dockable':left_dockable,
                                                       'right_dockable':right_dockable, 'bottom_dockable':bottom_dockable,
                                                       'top_dockable':top_dockable, 'show':show}

                    # Set attribute
#                     self._windowSettings = gui_params

    def saveProteinXML(self, path, evt=None):
        pass

    def saveCCSCalibrantsXML(self, path, evt=None):
        """ Make and save config file in XML format """

        buff = '<?xml version="1.0" encoding="utf-8" ?>\n'
        buff += '<!-- Please refrain from changing the parameter names - this will break things! -->\n'
        buff += '<origamiConfig version="1.0">\n\n'

        # calibrants
        buff += '  <calibrants>\n'
        buff += '    <param protein="operator" mw="%.3f" subunits="%d" charge="%d" m/z="%.3f" ccsHePos="%.3f" ccsN2Pos="%.3f" ccsHeNeg="%.3f" ccsN2Neg="%.3f" state="%s" source="%s" type="calibrant" />\n'
        buff += '  </calibrants>\n\n'

        buff += '</origamiConfig>'

    def setProperType(self, value, type):
        """ change type for config objects """

        if type == 'str' or type == 'unicode':
            value = str(value)
        elif type == 'int':
            value = int(value)
        elif type == 'float':
            value = float(value)
        elif type == 'bool':
            value = str2bool(value)
        elif type == 'color':
            value = literal_eval(value)
        elif type == 'path':
            value = os.path.normpath(value)
        elif type == 'tuple':
            value = literal_eval(value)

        # Return value
        return value

    def _escape(self, text):
        """Clear special characters such as <> etc."""

        text = text.strip()
        search = ('&', '"', "'", '<', '>')
        replace = ('&amp;', '&quot;', '&apos;', '&lt;', '&gt;')
        for x, item in enumerate(search):
            text = text.replace(item, replace[x])

        return text
    # ----
