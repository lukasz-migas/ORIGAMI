# List of functions used to load data into ORIGAMI

import os.path
from subprocess import call, Popen, CREATE_NEW_CONSOLE
import numpy as np
from sklearn.preprocessing import normalize
import time
from _codecs import encode
from toolbox import *
from analysisFcns import binMSdata
import pandas as pd
from _codecs import encode
from ctypes import *

# Load C library
mlLib = cdll.LoadLibrary("MassLynxRaw.dll")

### EXTRACT FUNCTIONS ####
# ========================================
def rawOpen1DRTdata(path=None, fileName=None, inputFile='output.1dDT', norm=None,
	fileNameLocation=None):
	"""
	Load data for 1D IM-MS data
	"""
	tstart = time.clock()
	if (path==None and fileNameLocation==None):
		outName='/'.join([fileName,inputFile])
	elif (path!=None and fileName!=None ):
		outName='/'.join([path,fileName,inputFile])
	elif (path!=None):
		outName='/'.join([path,inputFile])
	else:
		outName='/'.join([fileNameLocation])
	
	#f = open(outName, "r") 
	imsData = np.fromfile(outName, dtype=np.int32)
	imsDataClean = imsData[3::]
	imsDataReshape = imsDataClean.reshape((200,2), order='C')
	imsData1D = imsDataReshape[:,1]
	tend = time.clock()
# 	print('Loaded 1D IM-MS in: %.2gs' % (tend-tstart))
	if (norm==True):
		imsData1DNorm = imsData1D.astype(np.float64)/max(imsData1D)
		return imsData1DNorm
	else:
		return imsData1D
	
def rawOpenRTdata(path=None, fileName=None, inputFile='output.1dRT', norm=None,
	fileNameLocation=None):
	
	if (path==None and fileNameLocation==None):
		outName='/'.join([fileName,inputFile])
	elif (path!=None and fileName!=None ):
		outName='/'.join([path,fileName,inputFile])
	elif (path!=None):
		outName='/'.join([path,inputFile])
	else:
		outName='/'.join([fileNameLocation])

	rtData = np.fromfile(outName, dtype=np.int32)
	rtDataClean = rtData[3::]
	nScans = rtData[1]
	rtDataReshape = rtDataClean.reshape((nScans,2), order='C')
	rtData1D = rtDataReshape[:,1]

	if (norm==True):
		rtData1DNorm = rtData1D.astype(np.float64)/max(rtData1D)
		return rtData1D,rtData1DNorm
	else:
		return rtData1D	

def rawOpen2DIMSdata(path=None, fileName=None, inputFile='output.2dRTDT', norm=None,
	fileNameLocation=None):
	# TO DO:
	tstart = time.clock()
	if (path==None and fileNameLocation==None):
		outName='/'.join([fileName,inputFile])
	elif (path!=None and fileName!=None ):
		outName='/'.join([path,fileName,inputFile])
	elif (path!=None):
		outName='/'.join([path,inputFile])
	else:
		outName=fileNameLocation
		
	f = open(outName, "r") 
	imsData = np.fromfile(f, dtype=np.int32)
	imsDataClean = imsData[3::]
	numberOfRows = imsData[1]
	imsDataReshape = imsDataClean.reshape((200,numberOfRows),order='F') # Reshapes the list to 2D array
	imsDataSplit = np.hsplit(imsDataReshape,int(numberOfRows/5)) # Splits the array into [scans,200,5] array
	imsDataSplit  = np.sum(imsDataSplit,axis=2).T # Sums each 5 RT scans together
	"""
	There is a bug - sometimes when extracting, the last column values
	go way outside of range and make the plot look terrible. Hacky way
	round this is to check that any values fall outside the range and if so,
	set the last column to 0s...
	"""
	#Test to ensure all values are above 0 or below 1E8
	for value in imsDataSplit[:,-1]:
		if value < 0: 
			print('Values in the last column were below 0 - reset to 0')
			imsDataSplit[:,-1] = 0
		elif value > 10000000:
			print('Values in the last column were above 1000000 - reset to 0')
			imsDataSplit[:,-1] = 0

	tend = time.clock()
# 	print('Loaded 2D IM-MS in: %.2gs' % (tend-tstart)) 
	if (norm==True):
		imsDataSplitNorm = normalize(imsDataSplit.astype(np.float64),axis=0,norm='max') # Norm to 1 
		return imsDataSplit, imsDataSplitNorm
	else:
		return imsDataSplit
	
def rawOpenMSdata(path=None, fileName=None, inputFile='output.1dMZ', norm=True,
	fileNameLocation=None):
	if (path==None and fileNameLocation==None):
		outName='/'.join([fileName,inputFile])
	elif (path!=None and fileName!=None ):
			outName='/'.join([path,fileName,inputFile])
	elif (path!=None):
			outName='/'.join([path,inputFile])
	else:
		outName=fileNameLocation
	
	f = open(outName, "r") 
	# Load data into array
	msData = np.fromfile(f, dtype=np.float32)
	msDataClean = msData[2:(-1)]
	numberOfRows = int(len(msDataClean)/2)
	msDataReshape = msDataClean.reshape((2,numberOfRows), order='F')
	# Extract MS data
	msX = msDataReshape[1]
	msY = msDataReshape[0]
	firstBad = strictly_increasing(msX)
	if firstBad == True: pass
	else:
		firstBadIdx = np.where(msX==firstBad)
		try:
			msX = msX[0:(firstBadIdx[0][0]-1)]
			msY = msY[0:(firstBadIdx[0][0]-1)]
			print('Removed issue in the MS file')
		except IndexError: pass
	# Normalize MS data
	if norm:
		msY = msY/max(msY)
	else:
		msY = msY

	return msX, msY
	# ------------ #

def rawOpenMZDTdata(path=None, fileName=None, inputFile='output.2dDTMZ', norm=None,
                    fileNameLocation=None):
    tstart = time.clock()
    if (path==None and fileNameLocation==None):
        outName='/'.join([fileName,inputFile])
    elif (path!=None and fileName!=None ):
        outName='/'.join([path,fileName,inputFile])
    elif (path!=None):
        outName='/'.join([path,inputFile])
    else:
        outName=fileNameLocation

    f = open(outName, "r") 
    imsData = np.fromfile(f, dtype=np.int32)
    imsDataClean = imsData[3::]
    numberOfBins = imsData[0]
    imsDataSplit = imsDataClean.reshape((200, numberOfBins),order='C') # Reshapes the list to 2D array
    tend = time.clock()
    if (norm==True):
        imsDataSplitNorm = normalize(imsDataSplit.astype(np.float64),axis=0,norm='max') # Norm to 1 
        return imsDataSplit, imsDataSplitNorm
    else:
        return imsDataSplit

def textOpenIRData(path=None, fileName=None, norm=None, fileNameLocation=None):
	tstart = time.clock()

	outName = fileNameLocation.encode('ascii', 'replace')
	# Determine what file type it is
	fileNameExt=(str.split(outName,'.'))
	fileNameExt=fileNameExt[-1]
	if fileNameExt.lower() == 'csv':
		_imsDataText = np.genfromtxt(outName, delimiter=',', missing_values=[""], filling_values=[0])
	elif fileNameExt.lower() == 'txt':
		_imsDataText = np.genfromtxt(outName, delimiter='\t', missing_values=[""], filling_values=[0])

	# Remove values that are not numbers
	_imsDataText = np.nan_to_num(_imsDataText)
	yvals = _imsDataText[:,0] 
	xvals = _imsDataText[0,:]
	zvals = _imsDataText[1:,1:]
	
	return zvals, xvals, yvals

def textOpen2DIMSdata(path=None, fileName=None, norm=None, fileNameLocation=None):

	outName = fileNameLocation.encode('ascii', 'replace')
	# Determine what file type it is
	fileNameExt=(str.split(outName,'.'))
	fileNameExt=fileNameExt[-1]
	
	# Get data using pandas df
	df = pd.read_csv(outName, sep='\t|,| ', engine='python')
	# First value at 0,0 is equal to zero
	df.rename(columns={'0.00':'','0.00.1':'0.00'}, inplace=True)
	# Remove NaNs
	df.fillna(value=0, inplace=True)
	# Convert df to matrix
	zvals = df.as_matrix()
	imsDataText = zvals[:,1::]
	# Get yvalues
	YaxisLabels = zvals[:,0]
	# Get xvalues
	xvals = df.columns.tolist()

	XaxisLabels = map(float, xvals[1::])
	
	print('Labels size: %s x %s. Array size: %s x %s') % (len(XaxisLabels), len(YaxisLabels),
														len(imsDataText[0,:]), len(imsDataText[:,0]))

	if (norm==True):
		imsDataTextNorm = normalize(imsDataText,axis=0, norm='max') # Norm to 1 
		return imsDataText, imsDataTextNorm, XaxisLabels, YaxisLabels
	else:
		return imsDataText, XaxisLabels, YaxisLabels	

def rawExtractMSdata(path=None, driftscopeLocation='C:\DriftScope\lib', bin=10000,
					fileName=None, rtStart=0, rtEnd=999.0, dtStart=1, dtEnd=200,
					mzStart=0, mzEnd=99999, fileNameLocation = None):
	# TO DO: 
	# - enable selection of RT region for extracting MS for each collision voltage
	# Create input file
	msRangeFile='CIUrange.1dMZ.inp'
	if (path==None and fileNameLocation==None):
		msRangeFileLocation='/'.join([fileName,msRangeFile])
	elif (path!=None and fileName!=None ):
		msRangeFileLocation='/'.join([path,fileName,msRangeFile])
		fileNameLocation = '/'.join([path,fileName])
	else:
		fileNameLocation=fileNameLocation
		msRangeFileLocation='/'.join([fileNameLocation,msRangeFile])
		
	fileID = open(msRangeFileLocation,'w')
	fileID.write("%s %s %s\n%s %s 1\n%s %s 1" % (mzStart, mzEnd, bin, rtStart, rtEnd, dtStart, dtEnd))
		
	fileID.close()
	# Create command for execution
	cmd = ''.join([driftscopeLocation,'\imextract.exe -d "', fileNameLocation, '" -f 1 -o "', fileNameLocation, '\output.1dMZ" -t mobilicube -p "', msRangeFileLocation, '"'])
	# Extract command
	extractIMS = Popen(cmd, shell=True, creationflags=CREATE_NEW_CONSOLE)
	while extractIMS.poll() is None:
		pass
	return None
	# ------------ #
	
def rawExtract2DIMSdata(path=None, driftscopeLocation='C:\DriftScope\lib', fileName=None,
					 	mzStart=None, mzEnd=None, rtStart=0.0, rtEnd=999.0, 
					 	fileNameLocation = None):
	# Create input file
	msRangeFile='CIUrange.2dRTDT.inp'
	if (path==None and fileNameLocation==None):
		msRangeFileLocation='/'.join([fileName,msRangeFile])
	elif (path!=None and fileName!=None ):
		print('here')
		msRangeFileLocation='/'.join([path,fileName,msRangeFile])
		fileNameLocation = '/'.join([path,fileName])
	else:
		fileNameLocation=fileNameLocation
		msRangeFileLocation='/'.join([fileNameLocation,msRangeFile])
		
	fileID = open(msRangeFileLocation,'w')
	if (not(mzStart) or not(mzEnd)):
		fileID.write('0 99999 1\n0.0 999.0 5000\n1.0 200 200') 
	else:
		fileID.write("%s %s 1\n%s %s 5000\n1 200 200" % (mzStart, mzEnd, rtStart, rtEnd))
	
	fileID.close()
	# Create command for execution
	cmd = ''.join([driftscopeLocation,'\imextract.exe -d "', fileNameLocation, '" -f 1 -o "', 
				fileNameLocation, '\output.2dRTDT" -t mobilicube -b 1 -scans 0 -p "', 
				msRangeFileLocation, '"'])
	extractIMS = Popen(cmd, shell=True, creationflags=CREATE_NEW_CONSOLE)
	while extractIMS.poll() is None:
		pass
	
	return None
	# ------------ #
	
def rawExtract1DIMSdataOverRT(path=None, driftscopeLocation='C:\DriftScope\lib', 
							fileName='None', mzStart=0, mzEnd=999999, 
							rtStart=0, rtEnd=999.0, fileNameLocation = None):
	# Create input file
	msRangeFile='CIUrange.1dDT.inp'
	if (path==None and fileNameLocation==None):
		msRangeFileLocation='/'.join([fileName,msRangeFile])
	elif (path!=None and fileName!=None ):
		msRangeFileLocation='/'.join([path,fileName,msRangeFile])
		fileNameLocation = '/'.join([path,fileName])
	else:
		fileNameLocation=fileNameLocation
		msRangeFileLocation='/'.join([fileNameLocation,msRangeFile])
	
	fileID = open(msRangeFileLocation,'w')
	fileID.write("%s %s 1\n%s %s 1\n1 200 200" % (str(mzStart), str(mzEnd), str(rtStart), str(rtEnd)))
	
	fileID.close()
	# Create command for execution
	cmd = ''.join([driftscopeLocation,'\imextract.exe -d "', fileNameLocation, '" -f 1 -o "', fileNameLocation, '\output.1dDT" -t mobilicube -p "', msRangeFileLocation, '"'])
	extractIMS = Popen(cmd, shell=True, creationflags=CREATE_NEW_CONSOLE)
	while extractIMS.poll() is None:
		pass
	
	return None
	# ------------ #
	
def rawExtract1DIMSdata(path=None, driftscopeLocation='C:\DriftScope\lib', fileName='None', mzStart=0,
						mzEnd=99999, rtStart=0, rtEnd=999.0, fileNameLocation = None):
	# Create input file
	msRangeFile='CIUrange.1dDT.inp'
	if (path==None and fileNameLocation==None):
		msRangeFileLocation='/'.join([fileName,msRangeFile])
	elif (path!=None and fileName!=None ):
		print('here')
		msRangeFileLocation='/'.join([path,fileName,msRangeFile])
		fileNameLocation = '/'.join([path,fileName])
	else:
		fileNameLocation=fileNameLocation
		msRangeFileLocation='/'.join([fileNameLocation,msRangeFile])
	
	fileID = open(msRangeFileLocation,'w')
	fileID.write("%s %s 1\n%s %s 1\n1 200 200" % (str(mzStart), str(mzEnd), str(rtStart), str(rtEnd)))
	
	fileID.close()
	# Create command for execution
	cmd = ''.join([driftscopeLocation,'\imextract.exe -d "', fileNameLocation, '" -f 1 -o "', fileNameLocation, '\output.1dDT" -t mobilicube -p "', msRangeFileLocation, '"'])
	extractIMS = Popen(cmd, shell=True, creationflags=CREATE_NEW_CONSOLE)
	while extractIMS.poll() is None:
		pass

	return None
	# ------------ #
	
def rawExtractRTdata(path=None, driftscopeLocation='C:\DriftScope\lib', fileName='None', 
					 mzStart=1, mzEnd=99999, dtStart=1, dtEnd=200, fileNameLocation = None):
	"""
	Extract the retention time for specified (or not) mass range
	"""
	# Create input file
	msRangeFile='CIUrange.1dRT.inp'
	if (path==None and fileNameLocation==None):
		msRangeFileLocation='/'.join([fileName,msRangeFile])
	elif (path!=None and fileName!=None ):
		msRangeFileLocation='/'.join([path,fileName,msRangeFile])
		fileNameLocation = '/'.join([path,fileName])
	else:
		fileNameLocation=fileNameLocation
		msRangeFileLocation='/'.join([fileNameLocation,msRangeFile])
	
	fileID = open(msRangeFileLocation,'w')
	fileID.write("%s %s 1\n0.0 999.0 5000\n%s %s 1" % (str(mzStart), str(mzEnd), str(dtStart), str(dtEnd)))

	fileID.close()
	# Create command for execution
	cmd = ''.join([driftscopeLocation,'\imextract.exe -d "', fileNameLocation, '" -f 1 -o "',
				 fileNameLocation, '\output.1dRT" -t mobilicube -p "', msRangeFileLocation, '"'])
	
	extractIMS = Popen(cmd, shell=True, creationflags=CREATE_NEW_CONSOLE)
	while extractIMS.poll() is None:
		pass
	
	return None
	# ------------ #

def rawExtractDTdata(path=None, driftscopeLocation='C:\DriftScope\lib', fileName='None', 
					 mzStart=1, mzEnd=99999, rtStart=0.0, rtEnd=999, dtStart=1, dtEnd=200, 
					 fileNameLocation=None):
	"""
	Extract the retention time for specified (or not) mass range
	"""
	# Create input file
	msRangeFile='CIUrange.1dRT.inp'
	if (path==None and fileNameLocation==None):
		msRangeFileLocation='/'.join([fileName,msRangeFile])
	elif (path!=None and fileName!=None ):
		msRangeFileLocation='/'.join([path,fileName,msRangeFile])
		fileNameLocation = '/'.join([path,fileName])
	else:
		fileNameLocation=fileNameLocation
		msRangeFileLocation='/'.join([fileNameLocation,msRangeFile])
	
	fileID = open(msRangeFileLocation,'w')
	fileID.write("%s %s 1\n%s %s 5000\n%s %s 1" % (mzStart, mzEnd, rtStart, rtEnd, dtStart, dtEnd))

	fileID.close()
	# Create command for execution
	cmd = ''.join([driftscopeLocation,'\imextract.exe -d "', fileNameLocation, '" -f 1 -o "',
				 fileNameLocation, '\output.1dMZ" -t mobilicube -p "', msRangeFileLocation, '"'])
	print(cmd)
	extractIMS = Popen(cmd, shell=True, creationflags=CREATE_NEW_CONSOLE)
	while extractIMS.poll() is None:
		pass
	
	return None
 	
def rawExtractMZDTdata(path=None, driftscopeLocation='C:\DriftScope\lib', fileName=None,
                       mzStart=0, mzEnd=99999, nPoints=5000, dtStart=1, dtEnd=200,
                       fileNameLocation = None):
    # Create input file
    msRangeFile='CIUrange.2dDTMZ.inp'
    if (path==None and fileNameLocation==None):
        msRangeFileLocation='/'.join([fileName,msRangeFile])
    elif (path!=None and fileName!=None ):
        msRangeFileLocation='/'.join([path,fileName,msRangeFile])
        fileNameLocation = '/'.join([path,fileName])
    else:
        fileNameLocation=fileNameLocation
        msRangeFileLocation='/'.join([fileNameLocation,msRangeFile])

    fileID = open(msRangeFileLocation,'w')
    fileID.write("%s %s %s\n0.0 999.0 1\n%s %s 200" % (str(mzStart), str(mzEnd), str(nPoints), str(dtStart), str(dtEnd)))

    fileID.close()
    # Create command for execution
    cmd = ''.join([driftscopeLocation,'\imextract.exe -d "', fileNameLocation, '" -f 1 -o "', fileNameLocation, '\output.2dDTMZ" -t mobilicube -p "', msRangeFileLocation, '"'])
    
    extractIMS = Popen(cmd, shell=True, creationflags=CREATE_NEW_CONSOLE)
    while extractIMS.poll() is None:
		pass
 
    # ------------ #
    
# def rawExtractMZRTdata(path=None, driftscopeLocation='C:\DriftScope\lib', fileName=None,
#                        mzStart=0, mzEnd=99999, nPoints=5000, dtStart=1, dtEnd=200,
#                        fileNameLocation = None):
#     # Create input file
#     msRangeFile='CIUrange.2dDTMZ.inp'
#     if (path==None and fileNameLocation==None):
#         msRangeFileLocation='/'.join([fileName,msRangeFile])
#     elif (path!=None and fileName!=None ):
#         msRangeFileLocation='/'.join([path,fileName,msRangeFile])
#         fileNameLocation = '/'.join([path,fileName])
#     else:
#         fileNameLocation=fileNameLocation
#         msRangeFileLocation='/'.join([fileNameLocation,msRangeFile])
# 
#     fileID = open(msRangeFileLocation,'w')
#     fileID.write("%s %s %s\n0.0 999.0 1\n%s %s 200" % (str(mzStart), str(mzEnd), str(nPoints), str(dtStart), str(dtEnd)))
# 
#     fileID.close()
#     # Create command for execution
#     cmd = ''.join([driftscopeLocation,'\imextract.exe -d "', fileNameLocation, '" -f 1 -o "', 
# 				fileNameLocation, '\output.2dDTMZ" -t mobilicube -p "', 
# 				msRangeFileLocation, '"'])
#     extractIMS = call(cmd)
# 
#     return None
#     # ------------ #
	
def extractMSdata(filename=None,startScan=0, endScan=-1, function=1,
                  mzStart=None, mzEnd=None, binsize=None, binData=False):
    """
    Extract MS data, bin it
    ---
    @param binData: boolean, determines if data should be binned or not
    """
    tstart = time.clock()
    # Create pointer to the file
    filePointer = mlLib.newCMassLynxRawReader(filename)
    # Setup scan reader
    dataPointer = mlLib.newCMassLynxRawScanReader(filePointer)
    # Extract number of scans available from the file
    nScans = mlLib.getScansInFunction(dataPointer, function)
    # Initilise pointers to data
    xpoint = c_float() 
    ypoint = c_float()
    # Initilise empty lists
    msX = []
    msY = []
    msDict = {}
    if endScan == -1 or endScan > nScans:
        endScan = nScans
    if binData:
        if mzStart == None or mzEnd == None or binsize == None: 
            print('Missing parameters')
            return
        msList = np.arange(mzStart, mzEnd+binsize, binsize)
        msCentre = msList[:-1]+(binsize/2)
    msRange = np.arange(startScan, endScan)+1
    # First extract data
    for scan in msRange:
        nPoints = mlLib.getScanSize(dataPointer, function, scan)
        # Read XY coordinates
        mlLib.getXYCoordinates(filePointer,function, scan, byref(xpoint), byref(ypoint))
        # Prepare pointers
        mzP = (c_float * nPoints)()
        mzI = (c_float * nPoints)()
        # Read spectrum
        mlLib.readSpectrum(dataPointer, function, scan, byref(mzP), byref(mzI))
        # Extract data from pointer and assign it to list
        msX = np.ndarray((nPoints, ), 'f', mzP, order='C')    
        msY = np.ndarray((nPoints, ), 'f', mzI, order='C') 
        if binData:
            msYbin = binMSdata(x=msX, y=msY, bins=msList)
            msDict[scan] = [msCentre, msYbin]
        else:
            msDict[scan] = [msX, msY]

    tend = time.clock()
    print(''.join(["It took: ", str(np.round((tend-tstart),2)), " seconds to process ",str((len(msRange))), " scans"]))
    
    # Return data
    return msDict
	
def importCCSDatabase(filename=None):
	""" imports formated CCS database """
	
	try:
		df = pd.read_csv(filepath_or_buffer=filename, sep=',')
		df.fillna(0, inplace=True)
	except IOError: return None
	

	return df
		
def sumClassMSdata(data):
    # Retrieve MS data
    ydata = []
    # Iterate over the whole dictionary to retrieve y-axis data
    for idx in range(len(data)):
        ydata.append(data[idx]['yvals'])
    # Sum y-axis data
    msY = np.sum(ydata, axis=0)
    
    return msY

def subtractMS(msY_1, msY_2):

    # Subtract values
    out_1 = msY_1 - msY_2
    out_2 = msY_1 - msY_2
    
    # Return all positive/negative values as two lists
    out_1[out_1 < 0] = 0
    out_2[out_2 > 0] = 0

    return out_1, out_2
 	
def normalize1D(inputData = None, mode='Maximum'):
    # Normalize data to maximum intensity of 1
    
    if mode == 'Maximum':
        normData = np.divide(inputData.astype(np.float64), np.max(inputData))
    elif mode == 'tic':
        normData = np.divide(inputData.astype(np.float64), np.sum(inputData))
        normData = np.divide(normData.astype(np.float64), np.max(normData))

    return normData
# ------------ #
			
def threshold2D(inputData=None, min_threshold=0.0, max_threshold=1.0):  
    
    # Check min_threshold is larger than max_threshold
    if min_threshold > max_threshold:
        print("Minimum threshold is larger than the maximum. Values were reversed.")
        min_threshold, max_threshold = max_threshold, min_threshold
    
    # Check if they are the same
    if min_threshold == max_threshold:
        print("Minimum and maximum thresholds are the same.")
        return inputData
    
    # Find maximum value in the array
    data_max = np.max(inputData)
    min_threshold = min_threshold  * data_max
    max_threshold = max_threshold  * data_max
    
    # Adjust minimum threshold
    inputData[inputData <= min_threshold] = 0
    
    # Adjust maximum threshold
    inputData[inputData >= max_threshold] = data_max
    
    return inputData
			
			
			
			
			
			
			
			
			
			
			
			
			
			
			
			
			
			
			
			
			
			
			
			
			
			
			
			
			