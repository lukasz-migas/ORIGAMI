from collections import OrderedDict

class document():
    """
    Document object
    """
    
    def __init__(self):
        
        # File info
        self.docVersion = "19-10-2018" # to keep track of new features: add as date: DD-MM-YYYY
        
        self.last_saved = None # added in 19-10-2018 / v1.2.1
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
        
        # mass spectrum
        self.gotMS = False
        self.massSpectrum = {}
        # processed mass spectrum
        self.smoothMS = {}
        # multiple mass spectrum
        self.gotMultipleMS = False
        self.multipleMassSpectrum = OrderedDict()
        # save data (dataframe format)
        self.gotMSSaveData = False
        self.massSpectraSave = []
        # mobiligram (1D) data
        self.got1DT = False
        self.DT = []
        # multiple mobiligrams (1D) data
        self.gotMultipleDT = False 
        self.multipleDT = OrderedDict()
        # chromatogram data
        self.got1RT = False
        self.RT = []
        # multiple chromatograms 
        self.gotMultipleRT = False 
        self.multipleRT = OrderedDict()
        # mobiligram (2D) data = global
        self.got2DIMS = False
        self.IMS2D = {}
        # processed mobiligram (2D) data = global
        self.got2Dprocess = False
        self.IMS2Dprocess = [] # 2D processed data
        # mobiligram (2D) data = extracted ion
        self.gotExtractedIons = False
        self.IMS2Dions = {}
        # processed mobiligram (2D) data = extracted ion
        self.got2DprocessIons = False
        self.IMS2DionsProcess = {} # dictionary for processed data
        # mobiligram (1D) data = extracted ion
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
        
        # Overlay 
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
        
        # Other data
        self.other_data = {}
        self.tandem_spectra = {}
        self.file_reader = {}
        self.app_data = {}
 
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
    