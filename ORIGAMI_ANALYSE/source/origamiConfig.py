# -*- coding: utf-8 -*- 
import os
import numpy as np
import matplotlib.cm as cm
from matplotlib.pyplot import colormaps
import platform
from toolbox import *
from wx.lib.embeddedimage import PyEmbeddedImage
from collections import OrderedDict, defaultdict
import wx
import wx.lib.mixins.listctrl  as listmix
import os.path
from ast import literal_eval
import glob
import xml.dom.minidom
import dialogs as dialogs



__author__ = 'Lukasz G Migas'

                                
class document():
    """
    Document object
    """
    
    def __init__(self):
        
        # File info
        self.dovVersion = "v1" # to keep track of new features
        
        self.title = ''
        self.path = ''
        self.notes = ''
        
        self.dataType = ''
        self.fileFormat = ''
        self.parameters = {}
        self.userParameters = {}
        self.fileInformation = {}
        self.moleculeDetails = {}
        self.saveHMTLpath = ''         
        
        # Data storage
        self.gotMS = False
        self.massSpectrum = {}
        
        self.smoothMS = {}
        self.gotMultipleMS = False
        
        self.multipleMassSpectrum = OrderedDict()
        self.gotMSSaveData = False
        self.massSpectraSave = []
        
        self.got1DT = False
        self.DT = []
        
        self.got1RT = False
        self.RT = []
        
        self.got2DIMS = False
        self.IMS2D = {}
        
        self.got2Dprocess = False
        self.IMS2Dprocess = [] # 2D processed data
        
        self.gotExtractedIons = False
        self.IMS2Dions = {}
        
        self.got2DprocessIons = False
        self.IMS2DionsProcess = {} # dictionary for processed data
        
        self.gotExtractedDriftTimes = False
        self.IMS1DdriftTimes = {}
        
        # Dictionary to store dt/rt vs mz data
        # introduced in v 1.0.4
        self.gotDTMZ = False
        self.DTMZ = {}
        
        self.gotDTMZions = False
        self.DTMZions = {}
        
        # Dictionary with 1D and 2D IMMS data - from ORIGAMI
        self.gotCombinedExtractedIonsRT = False
        self.IMSRTCombIons = {}
        
        self.gotCombinedExtractedIons = False
        self.IMS2DCombIons = {}
        
        self.combineIonsList = []
        
        # OVerlay 
        self.gotOverlay = False
        self.overlay2D = {}
        
        # Peaklist
        self.gotPeaklist = False
        self.peakList = []
        
        # Calibration [for calibration file only!]
        self.gas = 28.0134 # N2 = 28.0134, He = 4.002602
        self.corrC = 1.57 # correction factor
        self.gotCalibration = False
        self.calibration = {}
        self.gotCalibrationDataset = False
        self.calibrationDataset = {} # calibrants, files
        self.gotCalibrationParameters = False
        self.calibrationParameters = [] # df + calibration parameters
                
        
        # Overlay/Statistical only
        self.gotComparisonData = False
        self.IMS2DcompData = {}
        self.gotOverlay = False
        self.IMS2DoverlayData = {}
        self.gotStatsData = False
        self.IMS2DstatsData = {}
        self.got2Dmatrix = False
        
 
        # Experimental variables
        self.scanTime = None
        self.currentExtractRange = None
        
        # Styles
        self.lineColour = (0,0,0) # black
        self.style = 'solid'
        self.lineWidth = 1
        self.colormap  = 'inferno'
        self.plot2Dtype = 'contour' # contour/imshow
        self.visible = True
    
    
class OrigamiConfig:
    
    def __init__(self):
        """
        Initilize config
        """
        
        self.version = "1.0.4"
        self.links = {'home' : 'https://www.click2go.umip.com/i/s_w/ORIGAMI.html',
                      'github' : 'https://github.com/lukasz-migas/ORIGAMI',
                      'cite' : 'https://doi.org/10.1016/j.ijms.2017.08.014',
                      'newVersion' : 'https://github.com/lukasz-migas/ORIGAMI/releases',
                      'guide': 'https://github.com/lukasz-migas/ORIGAMI/blob/master/ORIGAMI_ANALYSE/UserGuide.pdf',
                      'youtube':'https://www.youtube.com/watch?v=XNfM6F_MSb0&list=PLrPB7zfH4WXMYa5CN9qDtl-G-Ax_L6AK8',
                      'htmlEditor':'https://html-online.com/editor/'}
        self.logging = False
        self.threading = True
        
        # Populate GUI
        self.overlayChoices = ["Mask", "Transparent", "Mean", "Variance", "RMSD", 
                               "Standard Deviation", "RMSF","RMSD Matrix"]
        
        self.comboAcqTypeSelectChoices = ["Linear", "Exponential", "Fitted", "User-defined"] # change to Boltzmann
        
        self.normModeChoices = ["Maximum", "Logarithmic","Natural log","Square root",
                                "Least Abs Deviation","Least Squares"]
        
        self.detectModeChoices = ["MS","RT","MS/RT"]#, "DT","MS/DT"]

        self.comboSmoothSelectChoices = ["None","Savitzky-Golay", "Gaussian"] # "Moving Average"
        
        self.comboInterpSelectChoices = ['None', 'nearest', 'bilinear', 
                                        'bicubic', 'spline16','spline36', 'hanning', 
                                        'hamming', 'hermite', 'kaiser', 'quadric', 
                                        'catrom', 'gaussian', 'bessel', 'mitchell', 
                                        'sinc', 'lanczos']
        
        self.narrowCmapList = ['Greys', 'Purples', 'Blues', 'Greens', 'Oranges', 'Reds',
                               'YlOrBr', 'YlOrRd', 'OrRd', 'PuRd', 'RdPu', 'BuPu',
                               'GnBu', 'PuBu', 'YlGnBu', 'PuBuGn', 'BuGn', 'YlGn',
                               'viridis', 'plasma', 'inferno', 'magma',
                               'PiYG', 'PRGn', 'BrBG', 'PuOr', 'RdGy', 'RdBu',
                               'RdYlBu', 'RdYlGn', 'Spectral', 'coolwarm']
        
        self.imageFormatType  = ['png','svg', 'eps', 'jpeg', 'tiff', 'pdf']
        
        self.imageType2D = ['Image','Contour']
        
        self.styles = ['Default', 'ggplot', 'fivethirtyeight', 'classic',
                       'bmh', 'seaborn', 'seaborn-ticks',
                       'seaborn-bright', 'seaborn-dark','seaborn-pastel']
        
        self.availablePlotsList = ["MS", "RT", "DT", "2D", "Waterfall",  
                                   "RMSD", "Comparison", "Overlay"]
        
                
        self.markerShapeDict = {'square':'s', 'circle':'o', 'pentagon':'p','star':'*',
                                'diamond':'D', 'cross':'x'}
        
        self.textOutputDict = {'comma':',', 'tab':'\t', 'space':' '}
        self.textExtensionDict = {'comma':'.csv', 'tab':'.txt', 'space':'.txt'}
        
        self.rmsdLocChoices = {'leftTop': (5, 95),
                               'rightTop': (75, 95), 
                               'leftBottom': (5, 5),
                               'rightBottom': (75, 5),
                               'None':()}
        
        self.interactiveToolsOnOff = {'1D':{'hover':True,'save':True,'pan':True,
                                            'boxzoom':True,'crosshair':False,
                                            'reset':True, 
                                            'wheel':True, 'wheelType':'Wheel Zoom X',
                                            'activeDrag':'Box Zoom',
                                            'activeWheel':'None',
                                            'activeInspect':'Hover'},
                                       '2D':{'hover':True,'save':True,'pan':True,
                                             'boxzoom':True,'crosshair':True, 
                                             'reset':True, 
                                             'wheel':True,'wheelType':'Wheel Zoom X',
                                             'activeDrag':'Box Zoom',
                                             'activeWheel':'None',
                                             'activeInspect':'Hover'},
                                       'Overlay':{'hover':True,'save':True,'pan':True,
                                                  'boxzoom':True,'crosshair':True,
                                                  'reset':True, 
                                                  'wheel':False,'wheelType':'Wheel Zoom X',
                                                  'activeDrag':'Box Zoom',
                                                  'activeWheel':'None',
                                                  'activeInspect':'Hover'}}
        
        
        self.plotSizes = {'MS':[0.1,0.5,0.85,0.45], 
                          'RT':[0.1,0.5,0.85,0.45],
                          'DT':[0.1,0.5,0.85,0.45],
                          '2D':[0.1, 0.1, 0.8, 0.85],
                          'DTMS':[0.1, 0.1, 0.8, 0.85],
                          'Waterfall':[0.05,0.1,0.9,0.85], 
                          'RMSD':[0.1, 0.1, 0.8, 0.85],
                          'Comparison':[0.2, 0.2, 0.6, 0.6],
                          'Overlay':[0.1, 0.1, 0.8, 0.85],
                          'CalibrationMS':[0.10, 0.20, 0.8, 0.7],
                          'CalibrationDT':[0.10, 0.15, 0.8, 0.7]
                            }
        
        self.savePlotSizes = {'MS':[0.1,0.15,0.85,0.8], 
                              'RT':[0.1,0.15,0.85,0.8],
                              'DT':[0.1,0.15,0.85,0.8],
                              '2D':[0.1, 0.1, 0.8, 0.85],
                              'DTMS':[0.1, 0.1, 0.8, 0.85],
                              'Waterfall':[0.1,0.1,0.8,0.8], 
                              'RMSD':[0.1, 0.1, 0.8, 0.85],
                              'Comparison':[0.2, 0.2, 0.6, 0.6],
                              'Overlay':[0.1, 0.1, 0.8, 0.85],
                              'CalibrationMS':[0.10, 0.20, 0.8, 0.7],
                              'CalibrationDT':[0.10, 0.15, 0.8, 0.7]
                                }
        self.plotResize = {'MS':[10, 4], 
                           'RT':[10, 4],
                           'DT':[10, 4],
                           '2D':[10, 10],
                           'DTMS':[10, 10],
                           'Waterfall':[10, 10],
                           'RMSD':[10, 10],
                           'Comparison':[10, 10],
                           'Overlay':[10, 10],
                           'CalibrationMS':[10, 4], 
                           'CalibrationDT':[10, 4], 
                            }
        

        self.labelsXChoices = ['Scans', 
                               'Collision Voltage (V)', 
                               'Lab Frame Energy (eV)',
                               'Mass-to-charge (Da)', 
                               'm/z (Da)',
                               u'Wavenumber (cm⁻¹)']
        
        self.labelsYChoices = ['Drift time (bins)', 
                               'Drift time (ms)', 
                               u'Collision Cross Section (Å²)']
        
        # Dictionary with name:number of panels - better way of accessing various panels
        # rather than rememebring which panel is which!
        n = 0
        self.panelNames = {'MS':0, 'RT':1,'1D':2,'2D':3,
                           'MZDT':4, 'Waterfall':5,'3D':6,
                           'RMSF':7,'Comparison':8,'Overlay':9,
                           'Calibration':10,'Log':11}
        
        self.peaklistColNames = {'start':0, 'end':1,'charge':2,'color':3,
                                 'alpha':4,'filename':5,'method':6,
                                 'intensity':7,'label':8}
        
        self.driftTopColNames = {'start':0,'end':1,'intensity':2,'charge':4,
                                 'filename':5}
        
        self.textlistColNames = {'filename':0, 'startX':1, 'endX':2,'color':3,
                                 'alpha':4,'label':5,'shape':6, 'tag':7}
        
        self.multipleMLColNames = {'filename':0,'energy':1, 'document':2}
        
        self.ccsTopColNames = {'filename':0, 'start':1,'end':2,
                               'protein':3, 'charge':4,'ccs':5,'tD':6,
                               'gas':7}
        
        self.ccsBottomColNames = {'filename':0, 'start':1,'end':2,
                                  'ion':3,'protein':4, 'charge':5, 
                                  'format':6}
        
        self.ccsDBColNames = {'protein':0,'mw':1,'units':2,'charge':3,'ion':4,
                              'hePos':5,'n2Pos':6,'heNeg':7,'n2Neg':8,'state':9,
                              'source':10}
        
        # Calibration
        self.elementalMass = {'Hydrogen':1.00794, 
                              'Helium':4.002602, 
                              'Nitrogen':28.0134}
        
        # Add default HTML output methods 
        self.pageDict = {}
        self.pageDict['None'] = {'name':'None', 'layout':'Individual', 'rows':None, 'columns':None}
        self.pageDict['Rows'] = {'name':'Rows', 'layout':'Rows', 'rows':None, 'columns':None}
        self.pageDict['Columns'] = {'name':'Columns', 'layout':'Columns', 'rows':None, 'columns':None}
        
        #=========== FILE INFO ===========
        # can be removed
        self.rawName = ''
        self.fileName = ''
        self.textName = ''
        self.dirname = ''
        self.savefilename = ''
        
        # Initilize main config
        self.initilizeConfig()
        
    def initilizeConfig(self):
        # Settings Panel
        self.lastDir = None
        
        # Standard input/output/error
        self.stdin = None
        self.stdout = None
        self.stderr = None
        
        # Application presets
        self.zoomWindowX = 3 # m/z units
        self.zoomWindowY = 5 # percent
            
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
        
        self.binCVdata = False
        self.binMSstart = 500
        self.binMSend = 8000
        self.binMSbinsize = 0.1
        
        #=========== EXTRACT MZ ===========
        self.mzStart = ''
        self.mzEnd = ''
        self.rtStart = ''
        self.rtEnd = ''
         
        self.extractMode = '' # 'singleIon' OR 'multipleIons'
        
        self.annotColor = (0,0,1)
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
        self.smoothOverlay1DRT = 1
        
        
        #=========== PLOT PARAMETERS =============
        self.lineColour = (0,0,0)
        self.lineWidth = 10
        self.currentCmap = "inferno"
        self.interpolation = "None"
        self.overlayMethod = "Transparent"
        self.textOverlayMethod = "Mask"
        self.waterfallOffset = 0.05
        self.plotType = "Image" # Contour / Heatmap 
        self.currentStyle = 'Default'
        self.prettyContour = False
        self.useCurrentCmap = True
        self.addWaterfall = False
        self.colorbar = False
        self.colorbarWidth = 2
        self.colorbarPad = 0.03
        
        self.minCmap = 0 # %
        self.midCmap = 50 # %
        self.maxCmap = 100 # %
        
        self.rmsdLoc = "leftBottom"
        self.rmsdLocPos = (5,5) # (xpos, ypos) %
        self.rmsdColor = (1,1,1)
        self.rmsdFontSize = 16
        self.rmsdFontWeight = True
        self.rmsdRotX = 45
        self.rmsdRotY = 0
        
        self.restrictXYrange = False
        self.xyLimits = [] # limits the view of 2D plot
        
        self.restrictXYrangeRMSD = False
        self.xyLimitsRMSD = [] # limits the range of RMSD/F calculation
        
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
        self.initlizePaths()

       
#===============================================================================
# # Interactive parameters 
#===============================================================================

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
        
        self.toolsLocation = 'right'
        self.activeDrag = 'Box Zoom'
        self.activeWheel = 'None'
        self.activeInspect = 'Hover'
        self.colorbarInteractive = False
        
        self.titleFontSizeVal = 16
        self.titleFontWeightInteractive = False
        self.labelFontSizeVal = 14
        self.labelFontWeightInteractive = False
        self.tickFontSizeVal = 12
        self.notationFontSizeVal = 12
        self.notationFontWeightInteractive = True
        
        self.notationColor = (0,0,0)
        self.notationBackgroundColor = (1,1,1)
        self.notationTransparency = 1
        
        self.openInteractiveOnSave = True
        
    def initilizeColormaps(self):
        self.colormapMode = 0 # 0 = select few; 1 = all maps
        
        if self.colormapMode == 1:
            mapList = ['Jet']
        else:
            mapList = [i for i in cm.datad]
            self.cmaps = sorted(mapList)
        
        mapList2 = colormaps()
        self.cmaps2 = sorted(mapList2)
        
    def initlizePaths(self):
        self.system = platform.system()
        self.driftscopePath = "C:\DriftScope\lib"
        
        # Check if driftscope exists
        if not os.path.isdir(self.driftscopePath):
            print('Could not find Driftscope path')
            msg = "Could not localise Driftscope directory. Please setup path to Dritscope lib folder. It usually exists under C:\DriftScope\lib"
            dialogs.dlgBox(exceptionTitle='Could not find Driftscope', 
                           exceptionMsg= msg,
                           type="Warning")
#         else:
#             print('Found Driftscope')
        if not os.path.isfile(self.driftscopePath+"\imextract.exe"):
            print('Could not find imextract.exe')
            msg = "Could not localise Driftscope imextract.exe program. Please setup path to Dritscope lib folder. It usually exists under C:\DriftScope\lib"
            dialogs.dlgBox(exceptionTitle='Could not find Driftscope', 
                           exceptionMsg= msg,
                           type="Warning")
#         else:
#             print('Found imextract.exe')
            
        self.origamiPath = "" 
        
    def getPusherFrequency(self, parameters):
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
        return parameters

    def importMassLynxInfFile(self, path, manual=False, e=None):
        '''
        Imports information file for selected MassLynx file
        '''
        fileName = "\_extern.inf"
        fileName = ''.join([path,fileName])
        
        parameters = OrderedDict.fromkeys(["startMS","endMS","setMS","scanTime","ionPolarity",
                                   "modeSensitivity", "pusherFreq", "corrC", "trapCE"], None)
        
        if not os.path.isfile(fileName): 
            return parameters
        
        f = open(fileName, 'r')
        i = 0 # hacky way to get the correct collision voltage value
        for line in f:
            if "Start Mass" in line:
                try: parameters['startMS'] = str2num(str(line.split()[2]))
                except: pass
            if "MSMS End Mass" in line:
                try: parameters['endMS'] = str2num(str(line.split()[3]))
                except: pass
            elif "End Mass" in line:
                try: parameters['endMS'] = str2num(str(line.split()[2]))
                except: pass
            if "Set Mass" in line:
                try: parameters['setMS'] = str2num(str(line.split()[2]))
                except: pass
            if "Scan Time (sec)" in line:
                try: parameters['scanTime'] = str2num(str(line.split()[3]))
                except: pass
            if "Polarity" in line:
                try: parameters['ionPolarity'] = str(line.split()[1])
                except: pass
            if "Sensitivity" in line:
                try: parameters['modeSensitivity'] = str(line.split()[1])
                except: pass
            if "EDC Delay Coefficient" in line:
                try: 
                    parameters['corrC'] = str2num(str(line.split()[3]))
                except: pass
#             if manual == True:
            if "Trap Collision Energy" in line:
                if i==1:
                    try: parameters['trapCE'] = str2num(str(line.split()[3]))
                    except: pass
                i+=1
        f.close()
        parameters = self.getPusherFrequency(parameters=parameters)
        print(parameters)
        return parameters
    
    def importMassLynxHeaderFile(self, path, e=None):
        '''
        Imports information file for selected MassLynx file
        '''
        fileName = "\_HEADER.TXT"
        fileName = ''.join([path,fileName])
        
        fileInfo = OrderedDict.fromkeys(["SampleDescription"], None)
        
        if not os.path.isfile(fileName): return parameters
        
        f = open(fileName, 'r')
        i = 0 # hacky way to get the correct collision voltage value
        for line in f:
            if "$$ Sample Description:" in line:
                splitline = line.split(" ")
                line = " ".join(splitline[1::])
                fileInfo['SampleDescription'] = line
        f.close()

        return fileInfo
        
    def importOrigamiConfFile(self, path, e=None):
        """
        Tries to import origami.conf file from MassLynx directory
        """
        fileName = "\origami.conf"
        fileName = ''.join([path,fileName])
        parameters = OrderedDict.fromkeys(["method","spv","startVoltage",
                                           "endVoltage","stepVoltage",
                                           "expIncrement", "expPercentage", 
                                           "dx", "spvList", "cvList"], "")
        
        
        # Check if there is another file with different name
        searchname = ''.join([path,"\*.conf"])
        filelist = []
        for file in glob.glob(searchname):
            filelist.append(file)
        
        if len(filelist) > 0:
            if filelist[0] == fileName: pass
            else: fileName = filelist[0]
            
        
        if os.path.isfile(fileName):
            f = open(fileName, 'r')
            pass
        else:
            print('Did not find any ORIGAMI-MS configuration files. Moving on')
            return parameters   

        for line in f:        
            if "method" in line:
                try: parameters['method'] = str(line.split()[1])
                except: pass
            if "start" in line:
                try: parameters['startVoltage'] = str2num(str(line.split()[1]))
                except: pass
            if "spv" in line:
                try: parameters['spv'] = str2int(str(line.split()[1]))
                except: pass
            if "end" in line:
                try: parameters['endVoltage'] = str2num(str(line.split()[1]))
                except: pass
            if "step" in line:
                try: parameters['stepVoltage'] = str2num(str(line.split()[1]))
                except: pass
            if "expIncrement" in line:
                try: parameters['expIncrement'] = str2num(str(line.split()[1]))
                except: pass
            if "expPercentage" in line:
                try: parameters['expPercentage'] = str2num(str(line.split()[1]))
                except: pass
            if "dx" in line: 
                try: parameters['dx'] = str2num(str(line.split()[1]))
                except: pass
            if "SPVsList" in line:
                try: parameters['spvList'] = str(line.split()[1::])
                except: pass
            if "CVsList" in line: 
                try: parameters['cvList'] = str(line.split()[1::])
                except: pass
        f.close()
        
        # Also check if there is a list file
        spvCVlist = None
        try:
            spvPath = ''.join([path,"\spvCVlistOut.csv"])
            self.origamiList = np.genfromtxt(spvPath, skip_header=1, 
                                             delimiter=',', filling_values=0)
        except: pass
        
        
        return parameters
    
    def saveConfigXML(self, path, evt=None):
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
        
        buff += '  <main>\n'
        buff += '    <param name="logging" value="%s" type="bool" />\n' % (bool(self.logging))
        buff += '    <param name="threading" value="%s" type="bool" />\n' % (bool(self.threading))
        buff += '    <param name="resize" value="%s" type="bool" />\n' % (bool(self.resize))
        buff += '    <param name="lastDir" value="%s" type="path" />\n' % (self.lastDir)
        buff += '    <param name="driftscopePath" value="%s" type="path" note="Driftscope path should be set to the folder which contains the program imextract.exe" />\n' % (self.driftscopePath)
        buff += '    <param name="quickDisplay" value="%s" type="bool" />\n' % (bool(self.quickDisplay))
        buff += '    <param name="loadConfigOnStart" value="%s" type="bool" />\n' % (bool(self.loadConfigOnStart))
        buff += '    <param name="overrideCombine" value="%s" type="bool" />\n' % (bool(self.overrideCombine))
        buff += '    <param name="useInternalParamsCombine" value="%s" type="bool" />\n' % (bool(self.useInternalParamsCombine))
        buff += '    <param name="binOnLoad" value="%s" type="bool" />\n' % (bool(self.binOnLoad))
        buff += '    <param name="binSize" value="%.1f" type="float" />\n' % (float(self.binSize))
        buff += '    <param name="binSizeMZDT" value="%.1f" type="float" />\n' % (float(self.binSizeMZDT))
        buff += '    <param name="binMSfromRT" value="%.1f" type="float" />\n' % (float(self.binSizeMZDT))
        buff += '    <param name="zoomWindowX" value="%.1f" type="float" />\n' % (float(self.zoomWindowX))
        buff += '    <param name="zoomWindowY" value="%.1f" type="float" />\n' % (float(self.zoomWindowY))
        buff += '  </main>\n\n'
        
        buff += '  <origamiParams>\n'
        buff += '    <param name="binMSstart" value="%.1f" type="float" />\n' % (float(self.binMSstart))
        buff += '    <param name="binMSend" value="%.1f" type="float" />\n' % (float(self.binMSend))
        buff += '    <param name="binMSbinsize" value="%.4f" type="float" />\n' % (float(self.binMSbinsize))
        buff += '  </origamiParams>\n\n'

        buff += '  <process>\n'
        buff += '    <param name="normalize" value="%s" type="bool" />\n' % (bool(self.normalize))
        buff += '    <param name="normMode" value="%s" type="unicode" choices="%s" />\n' % (self.normMode, self.normModeChoices)
        buff += '    <param name="smoothMode" value="%s" type="unicode" choices="%s" />\n' % (self.smoothMode, self.comboSmoothSelectChoices)
        buff += '    <param name="savGolPolyOrder" value="%d" type="int" />\n' % (int(round(float(self.savGolPolyOrder),0)))
        buff += '    <param name="savGolWindowSize" value="%d" type="int" />\n' % (int(self.savGolWindowSize))
        buff += '    <param name="gaussSigma" value="%.1f" type="float" />\n' % (float(self.gaussSigma))
        buff += '    <param name="threshold" value="%.1f" type="float" />\n' % (float(self.threshold))
        buff += '    <param name="smoothOverlay1DRT" value="%.1f" type="float" />\n' % (float(self.smoothOverlay1DRT))
        buff += '  </process>\n\n'
        
        buff += '  <peakFinding>\n'
        buff += '    <param name="currentPeakFit" value="%s" type="unicode" choices="%s" />\n' % (self.currentPeakFit, self.detectModeChoices)
        buff += '    <param name="peakWindow" value="%.1f" type="float" />\n' % (float(self.peakWindow))
        buff += '    <param name="peakThreshold" value="%.1f" type="float" />\n' % (float(self.peakThreshold))
        buff += '    <param name="peakWidth" value="%.1f" type="float" />\n' % (float(self.peakWidth))
        buff += '    <param name="sigmaMS" value="%.1f" type="float" />\n' % (float(self.sigmaMS))
        buff += '    <param name="showRectanges" value="%s" type="bool" />\n' % (bool(self.showRectanges))
        buff += '    <param name="autoAddToTable" value="%s" type="bool" />\n' % (bool(self.autoAddToTable))
        buff += '    <param name="currentRangePeakFitCheck" value="%s" type="bool" />\n' % (bool(self.currentRangePeakFitCheck))
        buff += '    <param name="smoothFitting" value="%s" type="bool" />\n' % (bool(self.smoothFitting))
        buff += '    <param name="peakFittingHighRes" value="%s" type="bool" />\n' % (bool(self.peakFittingHighRes))
        buff += '    <param name="peakWidthAssign" value="%.1f" type="float" />\n' % (float(self.peakWidthAssign))
        buff += '    <param name="peakWindowAssign" value="%.d" type="int" />\n' % (float(self.peakWindowAssign))
        buff += '    <param name="peakThresholdAssign" value="%.1f" type="float" />\n' % (float(self.peakThresholdAssign))
        buff += '    <param name="showIsotopes" value="%s" type="bool" />\n' % (bool(self.showIsotopes))
        
        
        buff += '  </peakFinding>\n\n'
        
        buff += '  <plotParameters>\n'
        buff += '    <param name="markerShapeTXT" value="%s" type="unicode" />\n' % (self.markerShapeTXT)
        buff += '    <param name="markerSize" value="%d" type="int" />\n' % (int(self.markerSize))
        buff += '    <param name="annotTransparency" value="%d" type="int" />\n' % (int(self.annotTransparency))
        buff += '    <param name="annotColor" value="%s" type="color" />\n' % (str(self.annotColor))
        buff += '    <param name="lineWidth" value="%d" type="int" />\n' % (int(self.lineWidth))
        buff += '    <param name="lineColour" value="%s" type="color" />\n' % (str(self.lineColour))
        buff += '    <param name="interpolation" value="%s" type="unicode" />\n' % (self.interpolation)
        buff += '    <param name="currentCmap" value="%s" type="unicode" />\n' % (self.currentCmap)
        buff += '    <param name="overlayMethod" value="%s" type="unicode" choices="%s" />\n' % (self.overlayMethod, self.overlayChoices)
        buff += '    <param name="waterfallOffset" value="%.2f" type="float" />\n' % (float(self.waterfallOffset))
        buff += '    <param name="colorbarWidth" value="%.2f" type="float" />\n' % (float(self.colorbarWidth))
        buff += '    <param name="colorbarPad" value="%.2f" type="float" />\n' % (float(self.colorbarPad))
        buff += '    <param name="prettyContour" value="%s" type="bool" />\n' % (bool(self.prettyContour))
        buff += '    <param name="useCurrentCmap" value="%s" type="bool" />\n' % (bool(self.useCurrentCmap))
        buff += '    <param name="addWaterfall" value="%s" type="bool" />\n' % (bool(self.addWaterfall))
        buff += '    <param name="plotType" value="%s" type="unicode" choices="%s" />\n' % (self.plotType, self.imageType2D)
        buff += '    <param name="currentStyle" value="%s" type="unicode" />\n' % (self.currentStyle)
        buff += '    <param name="minCmap" value="%.1f" type="float" />\n' % (float(self.minCmap))
        buff += '    <param name="midCmap" value="%.1f" type="float" />\n' % (float(self.midCmap))
        buff += '    <param name="maxCmap" value="%.1f" type="float" />\n' % (float(self.maxCmap))
        buff += '    <param name="rmsdLoc" value="%s" type="unicode" choices="%s" />\n' % (self.rmsdLoc, self.rmsdLocChoices.keys())
        buff += '    <param name="rmsdLocPos" value="%s" type="tuple" />\n' % (str(self.rmsdLocPos))
        buff += '    <param name="rmsdColor" value="%s" type="color" />\n' % (str(self.rmsdColor))
        buff += '    <param name="rmsdFontSize" value="%d" type="int" />\n' % (int(self.rmsdFontSize))
        buff += '    <param name="rmsdFontWeight" value="%s" type="bool" />\n' % (bool(self.rmsdFontWeight))
        buff += '    <param name="rmsdRotX" value="%d" type="int" />\n' % (int(self.rmsdRotX))
        buff += '    <param name="rmsdRotY" value="%d" type="int" />\n' % (int(self.rmsdRotY))
        buff += '  </plotParameters>\n\n'
    
        buff += '  <exportParams>\n'
        buff += '    <param name="dpi" value="%d" type="int" />\n' % (int(self.dpi))
        buff += '    <param name="imageWidthInch" value="%d" type="int" />\n' % (int(self.imageWidthInch))
        buff += '    <param name="imageHeightInch" value="%d" type="int" />\n' % (int(self.imageHeightInch))
        buff += '    <param name="transparent" value="%s" type="bool" />\n' % (bool(self.transparent))
        buff += '    <param name="colorbar" value="%s" type="bool" />\n' % (bool(self.colorbar))
        buff += '    <param name="imageFormat" value="%s" type="unicode" choices="%s" />\n' % (str(self.imageFormat), self.imageFormatType)
        buff += '    <param name="saveDelimiterTXT" value="%s" type="unicode" choices="%s" />\n' % (self.saveDelimiterTXT, self.textOutputDict.keys())
        buff += '    <param name="normalizeMultipleMS" value="%s" type="bool" />\n' % (bool(self.normalizeMultipleMS))
        buff += '  </exportParams>\n\n'
        
        buff += '  <interactiveGUIparams>\n'
        buff += '    <param name="figHeight" value="%d" type="int" />\n' % (int(self.figHeight))
        buff += '    <param name="figWidth" value="%d" type="int" />\n' % (int(self.figWidth))
        buff += '    <param name="figHeight1D" value="%d" type="int" />\n' % (int(self.figHeight1D))
        buff += '    <param name="figWidth1D" value="%d" type="int" />\n' % (int(self.figWidth1D))
        buff += '    <param name="layoutModeDoc" value="%s" type="unicode" />\n' % (str(self.layoutModeDoc))
        buff += '    <param name="plotLayoutOverlay" value="%s" type="unicode" />\n' % (str(self.plotLayoutOverlay))
        buff += '    <param name="linkXYaxes" value="%s" type="bool" />\n' % (bool(self.linkXYaxes))
        buff += '    <param name="hoverVline" value="%s" type="bool" />\n' % (bool(self.hoverVline)) 
        buff += '    <param name="toolsLocation" value="%s" type="unicode" />\n' % (str(self.toolsLocation))
        buff += '    <param name="activeDrag" value="%s" type="unicode" />\n' % (str(self.activeDrag))
        buff += '    <param name="activeWheel" value="%s" type="unicode" />\n' % (str(self.activeWheel))
        buff += '    <param name="activeInspect" value="%s" type="unicode" />\n' % (str(self.activeInspect))
        buff += '    <param name="colorbarInteractive" value="%s" type="bool" />\n' % (bool(self.colorbarInteractive))
        buff += '    <param name="titleFontSizeVal" value="%d" type="int" />\n' % (int(self.titleFontSizeVal))
        buff += '    <param name="titleFontWeightInteractive" value="%s" type="bool" />\n' % (bool(self.titleFontWeightInteractive))
        buff += '    <param name="labelFontSizeVal" value="%d" type="int" />\n' % (int(self.labelFontSizeVal))
        buff += '    <param name="labelFontWeightInteractive" value="%s" type="bool" />\n' % (bool(self.labelFontWeightInteractive))
        buff += '    <param name="tickFontSizeVal" value="%d" type="int" />\n' % (int(self.tickFontSizeVal))
        buff += '    <param name="notationFontSizeVal" value="%d" type="int" />\n' % (int(self.notationFontSizeVal))
        buff += '    <param name="notationFontWeightInteractive" value="%s" type="bool" />\n' % (bool(self.notationFontWeightInteractive))
        buff += '    <param name="notationColor" value="%s" type="color" />\n' % (str(self.notationColor))
        buff += '    <param name="notationBackgroundColor" value="%s" type="color" />\n' % (str(self.notationBackgroundColor))
        buff += '    <param name="openInteractiveOnSave" value="%s" type="bool" />\n' % (bool(self.openInteractiveOnSave))
        buff += '  </interactiveGUIparams>\n\n'

            
        # Plot sizes in GUI
        buff += '  <plotSizes>\n'
        buff += '    <!-- Plot sizes in GUI. Values should range between 0-1. Remember that plot size is determined by left+width and bottom+height -->\n'
        plotSizes = self.plotSizes['MS']
        buff += '    <param name="MS" left="%.2f" bottom="%.2f" width="%.2f" height="%.2f" type="float" />\n' % (plotSizes[0], plotSizes[1], plotSizes[2], plotSizes[3])
        plotSizes = self.plotSizes['RT']
        buff += '    <param name="RT" left="%.2f" bottom="%.2f" width="%.2f" height="%.2f" type="float" />\n' % (plotSizes[0], plotSizes[1], plotSizes[2], plotSizes[3])
        plotSizes = self.plotSizes['DT']
        buff += '    <param name="DT" left="%.2f" bottom="%.2f" width="%.2f" height="%.2f" type="float" />\n' % (plotSizes[0], plotSizes[1], plotSizes[2], plotSizes[3])
        plotSizes = self.plotSizes['Waterfall']
        buff += '    <param name="Waterfall" left="%.2f" bottom="%.2f" width="%.2f" height="%.2f" type="float" />\n' % (plotSizes[0], plotSizes[1], plotSizes[2], plotSizes[3])
        plotSizes = self.plotSizes['RMSD']
        buff += '    <param name="RMSD" left="%.2f" bottom="%.2f" width="%.2f" height="%.2f" type="float" />\n' % (plotSizes[0], plotSizes[1], plotSizes[2], plotSizes[3])
        plotSizes = self.plotSizes['Comparison']
        buff += '    <param name="Comparison" left="%.2f" bottom="%.2f" width="%.2f" height="%.2f" type="float" />\n' % (plotSizes[0], plotSizes[1], plotSizes[2], plotSizes[3])
        plotSizes = self.plotSizes['Overlay']
        buff += '    <param name="Overlay" left="%.2f" bottom="%.2f" width="%.2f" height="%.2f" type="float" />\n' % (plotSizes[0], plotSizes[1], plotSizes[2], plotSizes[3])
        plotSizes = self.plotSizes['CalibrationMS']
        buff += '    <param name="CalibrationMS" left="%.2f" bottom="%.2f" width="%.2f" height="%.2f" type="float" />\n' % (plotSizes[0], plotSizes[1], plotSizes[2], plotSizes[3])
        plotSizes = self.plotSizes['CalibrationDT']
        buff += '    <param name="CalibrationDT" left="%.2f" bottom="%.2f" width="%.2f" height="%.2f" type="float" />\n' % (plotSizes[0], plotSizes[1], plotSizes[2], plotSizes[3])
        buff += '  </plotSizes>\n\n'
                
        # Plot sizes during saving
        buff += '  <plotSaveSizes>\n'
        buff += '    <!-- Plot sizes during saving. Values should range between 0-1. Remember that plot size is determined by left+width and bottom+height -->\n'
        plotSizes = self.savePlotSizes['MS']
        buff += '    <param name="MS" left="%.2f" bottom="%.2f" width="%.2f" height="%.2f" type="float" />\n' % (plotSizes[0], plotSizes[1], plotSizes[2], plotSizes[3])
        plotSizes = self.savePlotSizes['RT']
        buff += '    <param name="RT" left="%.2f" bottom="%.2f" width="%.2f" height="%.2f" type="float" />\n' % (plotSizes[0], plotSizes[1], plotSizes[2], plotSizes[3])
        plotSizes = self.savePlotSizes['DT']
        buff += '    <param name="DT" left="%.2f" bottom="%.2f" width="%.2f" height="%.2f" type="float" />\n' % (plotSizes[0], plotSizes[1], plotSizes[2], plotSizes[3])
        plotSizes = self.savePlotSizes['Waterfall']
        buff += '    <param name="Waterfall" left="%.2f" bottom="%.2f" width="%.2f" height="%.2f" type="float" />\n' % (plotSizes[0], plotSizes[1], plotSizes[2], plotSizes[3])
        plotSizes = self.savePlotSizes['RMSD']
        buff += '    <param name="RMSD" left="%.2f" bottom="%.2f" width="%.2f" height="%.2f" type="float" />\n' % (plotSizes[0], plotSizes[1], plotSizes[2], plotSizes[3])
        plotSizes = self.savePlotSizes['Comparison']
        buff += '    <param name="Comparison" left="%.2f" bottom="%.2f" width="%.2f" height="%.2f" type="float" />\n' % (plotSizes[0], plotSizes[1], plotSizes[2], plotSizes[3])
        plotSizes = self.savePlotSizes['Overlay']
        buff += '    <param name="Overlay" left="%.2f" bottom="%.2f" width="%.2f" height="%.2f" type="float" />\n' % (plotSizes[0], plotSizes[1], plotSizes[2], plotSizes[3])
        plotSizes = self.savePlotSizes['CalibrationMS']
        buff += '    <param name="CalibrationMS" left="%.2f" bottom="%.2f" width="%.2f" height="%.2f" type="float" />\n' % (plotSizes[0], plotSizes[1], plotSizes[2], plotSizes[3])
        plotSizes = self.savePlotSizes['CalibrationDT']
        buff += '    <param name="CalibrationDT" left="%.2f" bottom="%.2f" width="%.2f" height="%.2f" type="float" />\n' % (plotSizes[0], plotSizes[1], plotSizes[2], plotSizes[3])
        buff += '  </plotSaveSizes>\n\n'
                
        # Plot sizes during saving in inches
        buff += '  <plotSaveSizesInches>\n'
        buff += '    <!-- Plot sizes during saving - values are in inches. -->\n'
        plotSizes = self.plotResize['MS']
        buff += '    <param name="MS" width="%.2f" height="%.2f" type="float" />\n' % (plotSizes[0], plotSizes[1])
        plotSizes = self.plotResize['RT']
        buff += '    <param name="RT" width="%.2f" height="%.2f" type="float" />\n' % (plotSizes[0], plotSizes[1])
        plotSizes = self.plotResize['DT']
        buff += '    <param name="DT" width="%.2f" height="%.2f" type="float" />\n' % (plotSizes[0], plotSizes[1])
        plotSizes = self.plotResize['Waterfall']
        buff += '    <param name="Waterfall" width="%.2f" height="%.2f" type="float" />\n' % (plotSizes[0], plotSizes[1])
        plotSizes = self.plotResize['RMSD']
        buff += '    <param name="RMSD" width="%.2f" height="%.2f" type="float" />\n' % (plotSizes[0], plotSizes[1])
        plotSizes = self.plotResize['Comparison']
        buff += '    <param name="Comparison" width="%.2f" height="%.2f" type="float" />\n' % (plotSizes[0], plotSizes[1])
        plotSizes = self.plotResize['Overlay']
        buff += '    <param name="Overlay" width="%.2f" height="%.2f" type="float" />\n' % (plotSizes[0], plotSizes[1])
        plotSizes = self.plotResize['CalibrationMS']
        buff += '    <param name="CalibrationMS" width="%.2f" height="%.2f" type="float" />\n' % (plotSizes[0], plotSizes[1])
        plotSizes = self.plotResize['CalibrationDT']
        buff += '    <param name="CalibrationDT" width="%.2f" height="%.2f" type="float" />\n' % (plotSizes[0], plotSizes[1])
        buff += '  </plotSaveSizesInches>\n\n'
                
        buff += '</origamiConfig>'    
        
        # save config file
        try:
            save = file(path, 'w')
            save.write(buff.encode("utf-8"))
            save.close()
            print('Saved configuration file')
            return True
        except: 
            return False

    def loadConfigXML(self, path, evt=None):

        try:
            document = xml.dom.minidom.parse(path)
        except IOError:
            print('Missing configuration file')
            self.saveConfigXML(path='configOut.xml', evt=None)
            return
        except xml.parsers.expat.ExpatError:
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
#                 print(name, value, type)
                # Get value of proper type
                value  = self.setProperType(value=value, type=type)
                # Set attribute
                setattr(self, name, value)
        # Update user parameters
        self.userParameters['operator'] = self.operator
        self.userParameters['contact'] = self.contact
        self.userParameters['institution'] = self.institution
        self.userParameters['instrument'] = self.instrument

        mainTags = document.getElementsByTagName('main')
        if mainTags:
            xmlTags = mainTags[0].getElementsByTagName('param')
            for item in xmlTags:
                # Get values
                name = item.getAttribute('name')
                value = item.getAttribute('value')
                type = item.getAttribute('type')
#                 print(name, value, type)
                # Get value of proper type
                value  = self.setProperType(value=value, type=type)
                # Set attribute
                setattr(self, name, value)
                
        origamiTags = document.getElementsByTagName('origamiParams')
        if origamiTags:
            xmlTags = origamiTags[0].getElementsByTagName('param')
            for item in xmlTags:
                # Get values
                name = item.getAttribute('name')
                value = item.getAttribute('value')
                type = item.getAttribute('type')
#                 print(name, value, type)
                # Get value of proper type
                value  = self.setProperType(value=value, type=type)
                # Set attribute
                setattr(self, name, value)
                
        processTags = document.getElementsByTagName('process')
        if processTags:
            xmlTags = processTags[0].getElementsByTagName('param')
            for item in xmlTags:
                # Get values
                name = item.getAttribute('name')
                value = item.getAttribute('value')
                type = item.getAttribute('type')
#                 print(name, value, type)
                # Get value of proper type
                value  = self.setProperType(value=value, type=type)
                # Set attribute
                setattr(self, name, value)

        peakFindingTags = document.getElementsByTagName('peakFinding')
        if peakFindingTags:
            xmlTags = peakFindingTags[0].getElementsByTagName('param')
            for item in xmlTags:
                # Get values
                name = item.getAttribute('name')
                value = item.getAttribute('value')
                type = item.getAttribute('type')
#                 print(name, value, type)
                # Get value of proper type
                value  = self.setProperType(value=value, type=type)
                # Set attribute
                setattr(self, name, value)
                
        plotParamsTags= document.getElementsByTagName('plotParameters')
        if plotParamsTags:
            xmlTags = plotParamsTags[0].getElementsByTagName('param')
            for item in xmlTags:
                # Get values
                name = item.getAttribute('name')
                value = item.getAttribute('value')
                type = item.getAttribute('type')
#                 print(name, value, type)
                # Get value of proper type
                value  = self.setProperType(value=value, type=type)
                # Set attribute
                setattr(self, name, value)
                
        exportParamsTags= document.getElementsByTagName('exportParams')
        if exportParamsTags:
            xmlTags = exportParamsTags[0].getElementsByTagName('param')
            for item in xmlTags:
                # Get values
                name = item.getAttribute('name')
                value = item.getAttribute('value')
                type = item.getAttribute('type')
#                 print(name, value, type)
                # Get value of proper type
                value  = self.setProperType(value=value, type=type)
                # Set attribute
                setattr(self, name, value)
                
        interactiveParamsTags= document.getElementsByTagName('interactiveGUIparams')
        if interactiveParamsTags:
            xmlTags = interactiveParamsTags[0].getElementsByTagName('param')
            for item in xmlTags:
                # Get values
                name = item.getAttribute('name')
                value = item.getAttribute('value')
                type = item.getAttribute('type')
#                 print(name, value, type)
                # Get value of proper type
                value  = self.setProperType(value=value, type=type)
                # Set attribute
                setattr(self, name, value)
                
        plotSizesTags= document.getElementsByTagName('plotSizes')
        if plotSizesTags:
            xmlTags = plotSizesTags[0].getElementsByTagName('param')
            for item in xmlTags:
                # Get values
                name = item.getAttribute('name')
                plotSize = []
                for sizer in ['left', 'bottom', 'width', 'height']:
                    value = item.getAttribute(sizer)
                    type = item.getAttribute('type')
                    # Get value of proper type
                    value  = self.setProperType(value=value, type=type)
                    plotSize.append(value)
                # Set attribute
                self.plotSizes[name] = plotSize 
                
        plotSaveSizesTags= document.getElementsByTagName('plotSaveSizes')
        if plotSaveSizesTags:
            xmlTags = plotSaveSizesTags[0].getElementsByTagName('param')
            for item in xmlTags:
                # Get values
                name = item.getAttribute('name')
                plotSize = []
                for sizer in ['left', 'bottom', 'width', 'height']:
                    value = item.getAttribute(sizer)
                    type = item.getAttribute('type')
                    # Get value of proper type
                    value  = self.setProperType(value=value, type=type)
                    plotSize.append(value)
                # Set attribute
                self.savePlotSizes[name] = plotSize 
                
        plotSaveSizesInchesTags= document.getElementsByTagName('plotSaveSizesInches')
        if plotSaveSizesInchesTags:
            xmlTags = plotSaveSizesInchesTags[0].getElementsByTagName('param')
            for item in xmlTags:
                # Get values
                name = item.getAttribute('name')
                plotSize = []
                for sizer in ['width', 'height']:
                    value = item.getAttribute(sizer)
                    type = item.getAttribute('type')
                    # Get value of proper type
                    value  = self.setProperType(value=value, type=type)
                    plotSize.append(value)
                # Set attribute
                self.plotResize[name] = plotSize 
    
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
        
    
class IconContainer:
    def __init__(self):
        
        self.icons()
        self.loadBullets()
        self.loadIcons()
         
    def icons(self):
    
        origamiLogo = PyEmbeddedImage(
        "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"
        "JSGEEDImIv8fYJkezyZa7LkAAAAASUVORK5CYII=")
        self.getLogo = origamiLogo.GetBitmap()


        
        
        #----------------------------------------------------------------------
        bullets = PyEmbeddedImage(
        "iVBORw0KGgoAAAANSUhEUgAAAI8AAAAYCAYAAADDAK5oAAAAAXNSR0IArs4c6QAAAARnQU1B"
        "AACxjwv8YQUAAAAJcEhZcwAADsIAAA7CARUoSoAAAAL5SURBVGhD7Zk7khMxEIZtAh8AUjaD"
        "jAxyCJd0T8kNIIQcTgAZpHAAJ8v8g37T09ut52i8LuurkkfS9EutHnlc3t9P7AaDChbFs9/v"
        "Q2/JqK//udG58HKmkXpb6fTmQfFYzr35VpiQLRdcg944GW9ObrRMSsfKS42f3jzBB5wyYPY5"
        "7gXsY6FoMV9bxePBOEuQMZfGXeKvxc8azMUDuJGylQTUM3jEAkoSdTgcTk3izVvAj84DY0nB"
        "HObKA/orocbPWpyKB3BjZLJqidnQSUI/5VMnKSaPwjgej2H0b8yrNW/BGKUf+vaAbGodHvSX"
        "Q4ufNVkUDzcndxHngvExiVYidWHIAkoBe/Ah7ebmpCZ/9FeC9OPloDdNJ48lt9UimDyZxBjy"
        "xMlBriNlvyRnGujlxA+0HznOtbEmF3nypNCFwrE3HyMnF7V5KykcjSyaWhutzD/VvUUwQODd"
        "5zz7+qrx5oF1Lya/NvAFSvzlxKdlcvxYOqV+enMqHg8vmJiOROpvpbMl15yH8ffEoJrFO89g"
        "UMLi5Plz8zL0ljz9+T30rhd+beiDenxtBVA8VqF4862wWB97ceqN05ua2jAtk9J59/7b7sun"
        "N81+ejMXT+rE6VE80mbMPhLy+/mLuX+OIuOG4ErkBlkbpvP57NePpA5hLrRMjZ/uTM7up83B"
        "5QGc9+5LcmQkUj6mG0KcZWRL4cl68xb0jSubxprTtrWMpQPe3n4NvTydlJ/eLF6YUclsrcgn"
        "VcOni6Cf8gkZNhCT1/Yp681b8EmX68A4BuzFbMaA3uePr8MoToufNVkUj96gxwrjYxKtROo5"
        "ji1ZTU3hkJr84R2nVEf6gT7a1jSdPFbAsRNnTZg8mcQYOTKSSzhxZNHk2liTizx5Uuj4Ofbm"
        "Y+ScOLDDVgI2vkTn7tWHU5NFc47CmZmS47488sXSuy9f8CgTTJ6uGs8WsO55dnoQW6tHTnxa"
        "BuOUH0snRY7MmkR/qgPvycj9eprMh952OltyzXkY/20NKtnt/gKxElRx0ovSxgAAAABJRU5E"
        "rkJggg==")
        self.getBulletsOnData = bullets.GetData
        self.getBulletsOnImage = bullets.GetImage
        self.getBulletsOnBitmap = bullets.GetBitmap
        
        icons_16 = PyEmbeddedImage(
        "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"
        "AACcQvgBAABOIfwAAACnEH4AAIBTCD8AAMAphB8AAOAUwg8AAHAK4QcAADiF8AMAAJxC+AEA"
        "AE4h/AAAAKcQfgAAgFMIPwAAwCmEHwAA4BTCDwAAcArhBwAAOIXwAwAAnEL4AQAATiH8AAAA"
        "pxB+AACAUwg/AADAKYQfAADgFMIPAABwCuEHAAA4hfADAACcQvgBAABOIfwAAACnEH4AAIBT"
        "CD8AAMAphB8AAOAUwg8AAHAK4QcAADiF8AMAAJxC+AEAAE4h/AAAAKcQfgAAgFMIPwAAwCmE"
        "HwAA4BTCDwAAcArhBwAAOIXwAwAAnEL4AQAATiH8AAAApxB+AACAUwg/AADAKYQfAADgFMIP"
        "AABwCuEHAAA4hfADAACcQvgBAABOIfwAAACnEH4AAIBTCD8AAMAphB8AAOAUwg8AAHAK4QcA"
        "ADiF8AMAAJxC+AEAAE4h/AAAAKcQfgAAgFMIPwAAwCmEHwAA4BTCDwAAcArhBwAAOIXwAwAA"
        "nEL4AQAATiH8AAAApxB+AACAUwg/AADAKYQfAADgFMIPAABwCuEHAAA4hfADAACcQvgBAABO"
        "IfwAAACnEH4AAIBTCD8AAMAphB8AAOAUwg8AAHAK4QcAADiF8AMAAJxC+AEAAE4h/AAAAKcQ"
        "fgAAgFMIPwAAwCmEHwAA4BTCDwAAcArhBwAAOIXwAwAAnEL4AQAATiH8AAAApxB+AACAUwg/"
        "AADAKYQfAADgFMIPAABwCuEHAAA4hfADAACcQvgBAABOIfwAAACnEH4AAIBTCD8AAMAphB8A"
        "AOAUwg8AAHAK4QcAADiF8AMAAJxC+AEAAE4h/AAAAKcQfgAAgFMIPwAAwCmEHwAA4BTCDwAA"
        "cArhBwAAOIXwAwAAnEL4AQAATiH8AAAApxB+AACAUwg/AADAKYQfAADgFMIPAABwCuEHAAA4"
        "hfADAACcQvgBAABOIfwAAACnEH4AAIBTCD8AAMAphB8AAOAUwg8AAHAK4QcAADiF8AMAAJxC"
        "+AEAAE4h/AAAAKcQfgAAgFMIPwAAwCmEHwAA4BTCDwAAcArhBwAAOIXwAwAAnEL4AQAATiH8"
        "AAAApxB+AACAUwg/AADAKYQfAADgFMIPAABwCuEHAAA4hfADAACcQvgBAABOIfwAAACnEH4A"
        "AIBTCD8AAMAphB8AAOAUwg8AAHAK4QcAADiF8AMAAJxC+AEAAE4h/AAAAKcQfgAAgFMIPwAA"
        "wCmEHwAA4BTCDwAAcArhBwAAOIXwAwAAnEL4AQAATiH8AAAApxB+AACAUwg/AADAKYQfAADg"
        "FMIPAABwCuEHAAA4hfADAACcQvgBAABOIfwAAACnEH4AAIBTCD8AAMAphB8AAOAUwg8AAHAK"
        "4QcAADiF8AMAAJxC+AEAAE4h/AAAAKcQfgAAgFMIPwAAwCmEHwAA4BTCDwAAcArhBwAAOIXw"
        "AwAAnEL4AQAATiH8AAAApxB+AACAUwg/AADAKYQfAADgFMIPAABwCuEHAAA4hfADAACcQvgB"
        "AABOIfwAAACnEH4AAIBTCD8AAMAphB8AAOAUwg8AAHAK4QcAADiF8AMAAJxC+AEAAE4h/AAA"
        "AKcQfgAAgFMIPwAAwCmEHwAA4BTCDwAAcArhBwAAOIXwAwAAnEL4AQAATiH8AAAApxB+AACA"
        "Uwg/AADAKYQfAADgFMIPAABwCuEHAAA4hfADAACcQvgBAABOIfwAAACnEH4AAIBTCD8AAMAp"
        "hB8AAOAUwg8AAHAK4QcAADiF8AMAAJxC+AEAAE4h/AAAAKcQfgAAgFMIPwAAwCmEHwAA4BTC"
        "DwAAcArhBwAAOIXwAwAAnEL4AQAATiH8AAAApxB+AACAUwg/AADAKYQfAADgFMIPAABwCuEH"
        "AAA4hfADAACcQvgBAABOIfwAAACnEH4AAIBTCD8AAMAphB8AAOAUwg8AAHAK4QcAADiF8AMA"
        "AJxC+AEAAE4h/AAAAKcQfgAAgFMIPwAAwCmEHwAA4BTCDwAAcArhBwAAOIXwAwAAnEL4AQAA"
        "TiH8AAAApxB+AACAUwg/AADAKYQfAADgFMIPAABwCuEHAAA4hfADAACcQvgBAABOIfwAAACn"
        "EH4AAIBTCD8AAMAphB8AAOAQkf8HypGojtjsqhEAAAAASUVORK5CYII=")

        self.getIcons16Data = icons_16.GetData
        self.getIcons16Image = icons_16.GetImage
        self.getIcons16Bitmap = icons_16.GetBitmap


        
    #----------------------------------------------------------------------
        BgrToolbar = PyEmbeddedImage(
        "iVBORw0KGgoAAAANSUhEUgAAACMAAAAkCAYAAAAD3IPhAAAAGXRFWHRTb2Z0d2FyZQBBZG9i"
        "ZSBJbWFnZVJlYWR5ccllPAAAAD1JREFUeNrs0LEJACAUQ0E/OLibRytnSHGB1x+ZJKtlAwMD"
        "AwMDAwMDAwMDAwMDAwMD8zGv04LZTc9cAQYAXRFpP7LCOH4AAAAASUVORK5CYII=")
        self.getBgrToolbarData = BgrToolbar.GetData
        self.getBgrToolbarImage = BgrToolbar.GetImage
        self.getBgrToolbarBitmap = BgrToolbar.GetBitmap
        
    def loadBullets(self):
        self.bulletsLib = {}
        bulletsOn = self.getBulletsOnBitmap()
        self.bulletsLib['bulletsDoc'] = bulletsOn.GetSubBitmap(wx.Rect(0,0,13,12)) # 0
        self.bulletsLib['bulletsMS'] = bulletsOn.GetSubBitmap(wx.Rect(13,0,13,12)) # 1
        self.bulletsLib['bulletsDT'] = bulletsOn.GetSubBitmap(wx.Rect(26,0,13,12)) # 2
        self.bulletsLib['bulletsRT'] = bulletsOn.GetSubBitmap(wx.Rect(39,0,13,12)) # 3
        self.bulletsLib['bulletsDot'] = bulletsOn.GetSubBitmap(wx.Rect(52,0,13,12)) # 4
        self.bulletsLib['bulletsAnnot'] = bulletsOn.GetSubBitmap(wx.Rect(66,0,13,12)) # 5
        self.bulletsLib['bullets2DT'] = bulletsOn.GetSubBitmap(wx.Rect(79,0,13,12)) # 6
        self.bulletsLib['bulletsCalibration'] = bulletsOn.GetSubBitmap(wx.Rect(92,0,13,12)) # 7
        self.bulletsLib['bulletsOverlay'] = bulletsOn.GetSubBitmap(wx.Rect(105,0,13,12)) # 8
        
        self.bulletsLib['bulletsDocOn'] = bulletsOn.GetSubBitmap(wx.Rect(0,11,13,12)) # 9
        self.bulletsLib['bulletsMSIon'] = bulletsOn.GetSubBitmap(wx.Rect(13,11,13,12)) # 10
        self.bulletsLib['bulletsDTIon'] = bulletsOn.GetSubBitmap(wx.Rect(26,11,13,12)) # 11
        self.bulletsLib['bulletsRTIon'] = bulletsOn.GetSubBitmap(wx.Rect(39,11,13,12)) # 12
        self.bulletsLib['bulletsDotOn'] = bulletsOn.GetSubBitmap(wx.Rect(52,11,13,12)) # 13
        self.bulletsLib['bulletsAnnotIon'] = bulletsOn.GetSubBitmap(wx.Rect(66,11,13,12)) # 14
        self.bulletsLib['bullets2DTIon'] = bulletsOn.GetSubBitmap(wx.Rect(79,11,13,12)) # 15
        self.bulletsLib['bulletsCalibrationIon'] = bulletsOn.GetSubBitmap(wx.Rect(92,11,13,12)) # 16
        self.bulletsLib['bulletsOverlayIon'] = bulletsOn.GetSubBitmap(wx.Rect(105,11,13,12)) # 17
        
    def loadIcons(self):
        self.iconsLib = {}
        icons16 = self.getIcons16Bitmap()
        
        # LINE 1
        self.iconsLib['open16'] = icons16.GetSubBitmap(wx.Rect(0,0,16,16))
        self.iconsLib['extract16'] = icons16.GetSubBitmap(wx.Rect(17,0,16,16))
        self.iconsLib['add16'] = icons16.GetSubBitmap(wx.Rect(34,0,16,16))
        self.iconsLib['remove16'] = icons16.GetSubBitmap(wx.Rect(51,0,16,16))
        self.iconsLib['bin16'] = icons16.GetSubBitmap(wx.Rect(68,0,16,16))
        self.iconsLib['overlay16'] = icons16.GetSubBitmap(wx.Rect(85,0,16,16))
        self.iconsLib['save16'] = icons16.GetSubBitmap(wx.Rect(102,0,16,16))
        self.iconsLib['scatter16'] = icons16.GetSubBitmap(wx.Rect(119,0,16,16))
        self.iconsLib['process16'] = icons16.GetSubBitmap(wx.Rect(136,0,16,16))
        self.iconsLib['filter16'] = icons16.GetSubBitmap(wx.Rect(153,0,16,16))
        self.iconsLib['print16'] = icons16.GetSubBitmap(wx.Rect(170,0,16,16))
        self.iconsLib['combine16'] = icons16.GetSubBitmap(wx.Rect(187,0,16,16))
        self.iconsLib['examine16'] = icons16.GetSubBitmap(wx.Rect(204,0,16,16))
        self.iconsLib['undo16'] = icons16.GetSubBitmap(wx.Rect(221,0,16,16))
        # LINE 2
        self.iconsLib['calibration16'] = icons16.GetSubBitmap(wx.Rect(0,17,16,16))
        self.iconsLib['ms16'] = icons16.GetSubBitmap(wx.Rect(17,17,16,16))
        self.iconsLib['rt16'] = icons16.GetSubBitmap(wx.Rect(34,17,16,16))
        self.iconsLib['annotate16'] = icons16.GetSubBitmap(wx.Rect(51,17,16,16))
        self.iconsLib['document16'] = icons16.GetSubBitmap(wx.Rect(68,17,16,16))
        self.iconsLib['info16'] = icons16.GetSubBitmap(wx.Rect(85,17,16,16))
        self.iconsLib['tick16'] = icons16.GetSubBitmap(wx.Rect(102,17,16,16))
        self.iconsLib['cross16'] = icons16.GetSubBitmap(wx.Rect(119,17,16,16))
        self.iconsLib['folder16'] = icons16.GetSubBitmap(wx.Rect(136,17,16,16))
        self.iconsLib['idea16'] = icons16.GetSubBitmap(wx.Rect(153,17,16,16))
        self.iconsLib['setting16'] = icons16.GetSubBitmap(wx.Rect(170,17,16,16))
        self.iconsLib['bars16'] = icons16.GetSubBitmap(wx.Rect(187,17,16,16))
        self.iconsLib['chromeBW16'] = icons16.GetSubBitmap(wx.Rect(204,17,16,16))
        self.iconsLib['ieBW16'] = icons16.GetSubBitmap(wx.Rect(221,17,16,16))
        # LINE 3
        self.iconsLib['check16'] = icons16.GetSubBitmap(wx.Rect(0,34,16,16))
        self.iconsLib['origamiLogo16'] = icons16.GetSubBitmap(wx.Rect(17,34,16,16))
        self.iconsLib['plotIMS16'] = icons16.GetSubBitmap(wx.Rect(34,34,16,16))
        self.iconsLib['plotIMSoverlay16'] = icons16.GetSubBitmap(wx.Rect(51,34,16,16))
        self.iconsLib['plotCalibration16'] = icons16.GetSubBitmap(wx.Rect(68,34,16,16))

        self.iconsLib['documentTwo16'] = icons16.GetSubBitmap(wx.Rect(102,34,16,16))       
        self.iconsLib['github16'] = icons16.GetSubBitmap(wx.Rect(170,34,16,16))
        self.iconsLib['youtube16'] = icons16.GetSubBitmap(wx.Rect(187,34,16,16))
        self.iconsLib['chromeC16'] = icons16.GetSubBitmap(wx.Rect(204,34,16,16))
        self.iconsLib['ieC16'] = icons16.GetSubBitmap(wx.Rect(221,34,16,16))
        
        # LINE 4
        self.iconsLib['rmsdBottomLeft'] = icons16.GetSubBitmap(wx.Rect(0,51,16,16))
        self.iconsLib['rmsdTopLeft'] = icons16.GetSubBitmap(wx.Rect(17,51,16,16))
        self.iconsLib['rmsdTopRight'] = icons16.GetSubBitmap(wx.Rect(34,51,16,16))
        self.iconsLib['rmsdBottomRight'] = icons16.GetSubBitmap(wx.Rect(51,51,16,16))
        self.iconsLib['rmsdNone'] = icons16.GetSubBitmap(wx.Rect(68,51,16,16))
        self.iconsLib['origamiLogoDark16'] = icons16.GetSubBitmap(wx.Rect(85,51,16,16))
        
        # LINE 1 (24x24)
        self.iconsLib['folderOrigami'] = icons16.GetSubBitmap(wx.Rect(0,102,24,24))
        self.iconsLib['folderMassLynx'] = icons16.GetSubBitmap(wx.Rect(25,102,24,24))
        self.iconsLib['folderText'] = icons16.GetSubBitmap(wx.Rect(50,102,24,24))
        self.iconsLib['folderProject'] = icons16.GetSubBitmap(wx.Rect(75,102,24,24))
        self.iconsLib['folderTextMany'] = icons16.GetSubBitmap(wx.Rect(100,102,24,24))
        self.iconsLib['folderMassLynxMany'] = icons16.GetSubBitmap(wx.Rect(125,102,24,24))
        
        # LINE 2 (24x24)
        self.iconsLib['saveDoc'] = icons16.GetSubBitmap(wx.Rect(100,127,24,24))
        self.iconsLib['bokehLogo'] = icons16.GetSubBitmap(wx.Rect(175,127,24,24))
        
        # LINE 3 (24x24)
        self.iconsLib['panelCCS'] = icons16.GetSubBitmap(wx.Rect(25,152,24,24))
        self.iconsLib['panelDT'] = icons16.GetSubBitmap(wx.Rect(50,152,24,24))
        self.iconsLib['panelIon'] = icons16.GetSubBitmap(wx.Rect(75,152,24,24))
        self.iconsLib['panelML'] = icons16.GetSubBitmap(wx.Rect(100,152,24,24))
        self.iconsLib['panelParameters'] = icons16.GetSubBitmap(wx.Rect(125,152,24,24))
        self.iconsLib['panelText'] = icons16.GetSubBitmap(wx.Rect(150,152,24,24))
        self.iconsLib['panelDoc'] = icons16.GetSubBitmap(wx.Rect(175,152,24,24))
        
        # TOOLBAR
        self.iconsLib['bgrToolbar'] = self.getBgrToolbarBitmap()
        
        
        
        