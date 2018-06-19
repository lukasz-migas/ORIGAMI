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

import os.path
from subprocess import call,Popen
import numpy as np
from sklearn.preprocessing import normalize
from scipy.signal import savgol_filter 
from scipy.ndimage import gaussian_filter
from toolbox import *
from operator import itemgetter
from itertools import *
from dialogs import dlgBox
import math
from bisect import bisect_left
from scipy.interpolate import interp1d
from numpy.core.numerictypes import _maxvals
 
def combineIRdata(inputData=None, threshold=2000, noiseLevel=500, sigma=0.5):
    # TODO: This function needs work - Got to acquire more data to test it properly
    # Create empty lists
    dataList, indexList =[], []
    # Iterate and extract values that are below the IR threshold
    for x in range(len(inputData[1,:])):
        if np.sum(inputData[:,x]) > threshold:
            dataList.append(inputData[:,x])
            indexList.append(x)
              
    # Split the indexList so we have a list of lists of indexes to split data into
    splitlist = [map(itemgetter(1), g) for k, g in groupby(enumerate(indexList), lambda (i,x):i-x)]
      
    # Split data
    dataSplit = []
    for i in splitlist:
        dataSlice = inputData[:, i[0]:i[-1]]
        dataSliceSum = np.sum(dataSlice,axis=1)
        dataSplit.append(dataSliceSum)
          
    dataSplitArray = np.array(dataSplit)
    dataSplitArray = dataSplitArray[1:,:] # Remove first row as it has a lot of intensity
    dataSplitArray[dataSplitArray<=noiseLevel] = 0 # Remove noise
  
    dataSplitArray = np.flipud(np.rot90(dataSplitArray)) # rotate 
    # Convert the 2D array to 1D list too
    dataRT = np.sum(dataSplitArray, axis=0)
    data1DT = np.sum(dataSplitArray, axis=1)
      
    # Simulate x-axis values
    yvals = 1+np.arange(len(dataSplitArray)) 
    xvals = 1+np.arange(len(dataSplitArray[1,:]))
      
    # Return array
    return dataSplitArray, xvals, yvals, dataRT, data1DT
 
def combineCEscansLinear(imsDataInput = None, firstVoltage = None, startVoltage = None, endVoltage = None, 
                        stepVoltage = None, scansPerVoltage = None):
    # Build dictionary with parameters
    parameters = {'firstVoltage':firstVoltage, 'startV':startVoltage,
                  'endV':endVoltage, 'stepV':stepVoltage,'spv':scansPerVoltage,
                  'method':'Linear'}
    
    # Calculate information about acquisition lengths
    numberOfVoltages=((endVoltage-startVoltage)/stepVoltage)+1
    lastVoltage=firstVoltage+(scansPerVoltage*numberOfVoltages)
    if lastVoltage > len(imsDataInput[1,:]):
        return [None, lastVoltage, len(imsDataInput[1,:])], None, None
    else:
        print('File has a total of: %s scans. The last scan of CE ramp is %s' %(len(imsDataInput[1,:]), lastVoltage))
   
    # Pre-calculate X-axis information
    ColEnergyX = np.linspace(startVoltage,endVoltage, num=numberOfVoltages)
    # Crop IMS data to appropriate size (remove start and end regions 'reporter')
    cropIMSdata = imsDataInput[:,int(firstVoltage)::]
    x1 = 0
    # Create an empty array to put data into
    imsDataCEcombined, scanList = [], []
    for i, cv in zip(range(int(numberOfVoltages)), ColEnergyX):
        x2 = int(x1+scansPerVoltage)
        scanList.append([x1+firstVoltage, x2+firstVoltage, cv])
        _tempIMSData = cropIMSdata[:,x1:x2] # Crop appropriate range 
        _tempIMSData = np.sum(_tempIMSData, axis=1) # Combine all into one array
        x1 = x2
        imsDataCEcombined=np.append(imsDataCEcombined,_tempIMSData) # Create a new array containing all IMS data         
    # Output raw and normalized data
    imsDataCEcombined = imsDataCEcombined.reshape((200,int(numberOfVoltages)),order='F') # Reshape list to array
    return imsDataCEcombined, scanList, parameters
 
# ------------ #
     
def combineCEscansExponential(imsDataInput = None, firstVoltage = None, 
                            startVoltage = None, endVoltage = None, 
                            stepVoltage = None, scansPerVoltage = None, 
                            expIncrement = None, expPercentage = None, expAccumulator = 0,
                            verbose = False):
    # Build dictionary with parameters
    parameters = {'firstVoltage':firstVoltage, 'startV':startVoltage,
                  'endV':endVoltage, 'stepV':stepVoltage,'spv':scansPerVoltage,
                  'expIncrement':expIncrement,'expPercent':expIncrement,
                  'method':'Exponential'}
    
    # Calculate how many voltages were used 
    numberOfVoltages=((endVoltage-startVoltage)/stepVoltage)+1
    ColEnergyX = np.linspace(startVoltage,endVoltage, num=numberOfVoltages)
    startScansPerVoltage = scansPerVoltage # Used as backup
    # Generate list of SPVs first
    scanPerVoltageList = [] # Pre-set empty array
    for i in range(int(numberOfVoltages)):
        # Prepare list 
        if (ColEnergyX[i] >= endVoltage*expPercentage/100):
            expAccumulator=expAccumulator+expIncrement
            scanPerVoltageFit = np.round(startScansPerVoltage*np.exp(expAccumulator),0)
        else:
            scanPerVoltageFit = startScansPerVoltage 
        # Create a list with SPV counter
        scanPerVoltageList.append(scanPerVoltageFit)
    lastVoltage=firstVoltage+(sum(scanPerVoltageList))
    if lastVoltage > len(imsDataInput[1,:]):
        return [None, lastVoltage, len(imsDataInput[1,:])], None, None
    else: 
        print('File has a total of: %s scans. The last scan of CE ramp is %s' %(len(imsDataInput[1,:]), lastVoltage))
    # Crop IMS data to appropriate size (remove start and end regions 'reporter')
    cropIMSdata = imsDataInput[:,int(firstVoltage)::] #int(lastVoltage)]
    x1 = 0
    imsDataCEcombined, scanList = [], []
    for i, cv in zip(scanPerVoltageList, ColEnergyX):
        x2 = int(x1+i)
        scanList.append([x1+firstVoltage, x2+firstVoltage, cv])
        _tempIMSData = cropIMSdata[:,x1:x2] # Crop appropriate range 
        _tempIMSData = np.sum(_tempIMSData,axis=1) # Combine all into one array
        # Combine data into a list that will be reshaped afterwards
        imsDataCEcombined=np.append(imsDataCEcombined,_tempIMSData) # Create a new array containing all IMS data  
        x1 = x2 # set new starting index
    # Output raw and normalized data
    imsDataCEcombined = imsDataCEcombined.reshape((200,int(numberOfVoltages)),order='F') # Reshape list to array
    return imsDataCEcombined, scanList, parameters
# ------------ #
 
def combineCEscansFitted(imsDataInput = None, firstVoltage = None, 
                        startVoltage = None, endVoltage = None, 
                        stepVoltage = None, scansPerVoltage = None, 
                        expIncrement = None, verbose = False, A1 = 2, A2 = 0.07, 
                        x0 = 47, dx = None):
    
    # Build dictionary with parameters
    parameters = {'firstVoltage':firstVoltage, 'startV':startVoltage,
                  'endV':endVoltage, 'stepV':stepVoltage,'spv':scansPerVoltage,
                  'A1':A1,'A2':A2,'x0':x0,'dx':dx,'method':'Fitted'}
    
    # Calculate how many voltages were used 
    numberOfVoltages=((endVoltage-startVoltage)/stepVoltage)+1
    ColEnergyX = np.linspace(startVoltage,endVoltage, num=numberOfVoltages)
    startScansPerVoltage = scansPerVoltage # Used as backup
    # Generate list of SPVs first
    scanPerVoltageList = [] # Pre-set empty array
    for i in range(int(numberOfVoltages)):
        scanPerVoltageFit = np.round(1/(A2+(A1-A2)/(1+np.exp((ColEnergyX[i]-x0)/dx))),0)
        # Append to file
        scanPerVoltageList.append(scanPerVoltageFit*startScansPerVoltage)
 
    # Calculate last voltage
    lastVoltage=firstVoltage+(sum(scanPerVoltageList))
    if lastVoltage > len(imsDataInput[1,:]):
        return [None, lastVoltage, len(imsDataInput[1,:])], None, None
    else: 
        print('File has a total of: %s scans. The last scan of CE ramp is %s' %(len(imsDataInput[1,:]), lastVoltage))
    # Crop IMS data to appropriate size (remove start and end regions 'reporter')
    cropIMSdata = imsDataInput[:,int(firstVoltage)::] #int(lastVoltage)]
    x1 = 0
    imsDataCEcombined, scanList = [], []
    for i, cv in zip(scanPerVoltageList, ColEnergyX):
        x2 = int(x1+i)
        scanList.append([x1+firstVoltage, x2+firstVoltage, cv]) 
        _tempIMSData = cropIMSdata[:,x1:x2] # Crop appropriate range 
        _tempIMSData = np.sum(_tempIMSData,axis=1) # Combine all into one array
        # Combine data into a list that will be reshaped afterwards
        imsDataCEcombined=np.append(imsDataCEcombined,_tempIMSData) # Create a new array containing all IMS data
        x1 = x2
    # Output raw and normalized data
    imsDataCEcombined = imsDataCEcombined.reshape((200,int(numberOfVoltages)),order='F') # Reshape list to array
    return imsDataCEcombined, scanList, parameters
# ------------ #
 
def combineCEscansUserDefined(imsDataInput=None, firstVoltage=None, inputList=None):

    # Build dictionary with parameters
    parameters = {'firstVoltage':firstVoltage, 
                  'inputList':inputList,
                  'method':'User-defined'}

    # Pre-calculate lists
    scanPerVoltageList = inputList[:,0]
    ColEnergyX = inputList[:,1]
    
    # Make sure that list is of correct shape
    if len(ColEnergyX) != len(scanPerVoltageList):
        return
    # Calculate information about acquisition lengths
    numberOfVoltages=len(scanPerVoltageList)
    lastVoltage=firstVoltage+sum(scanPerVoltageList)
    
    if lastVoltage > len(imsDataInput[1,:]):
        return [None, lastVoltage, len(imsDataInput[1,:])], None, None, None
    else:
        print('File has a total of: %s scans. The last scan of CE ramp is %s' %(len(imsDataInput[1,:]), lastVoltage))
    # Crop IMS data to appropriate size (remove start and end regions 'reporter')
    cropIMSdata = imsDataInput[:,int(firstVoltage)::]
    x1 = int(0)
    # Create an empty array to put data into
    imsDataCEcombined, scanList = [], []
    for i, cv in zip(scanPerVoltageList, ColEnergyX):
        x2 = int(x1+i) # index 2
        scanList.append([x1+firstVoltage, x2+firstVoltage, cv, (x2-x1)])
        _tempIMSData = cropIMSdata[:,x1:x2] # Crop appropriate range 
        _tempIMSData = np.sum(_tempIMSData, axis=1) # Combine all into one array
        imsDataCEcombined=np.append(imsDataCEcombined,_tempIMSData) # Create a new array containing all IMS data
        x1 = x2
    imsDataCEcombined = imsDataCEcombined.reshape((200, len(scanPerVoltageList)),order='F') # Reshape list to array
    return imsDataCEcombined, ColEnergyX, scanList, parameters
 
def smoothDataGaussian(inputData = None, sigma = 2):
    # Check if input data is there
    if inputData is None or len(inputData) == 0:
        return None
    if sigma < 0:
        dlgBox(exceptionTitle='Warning', 
               exceptionMsg= "Value of sigma is too low. Value was reset to 1",
               type="Warning")
        sigma=1
    else:
        sigma=sigma
    dataOut = gaussian_filter(inputData, sigma = sigma, order=0)
    dataOut[dataOut < 0] = 0
    return dataOut    
# ------------ #
 
def smoothDataSavGol(inputData = None, polyOrder = 2, windowSize = 5):
    # Check if input data is there
    if inputData is None or len(inputData) == 0:
        return None
    # Check whether polynomial order is of correct size
    if (polyOrder<=0) :
        dlgBox(exceptionTitle='Warning', 
               exceptionMsg= "Polynomial order is too small. Value was reset to 2",
               type="Warning")
        polyOrder=2   
    else:
        polyOrder=polyOrder
    # Check whether window size is of correct size
    if windowSize is None:
        windowSize = polyOrder+1
    elif (windowSize % 2) and (windowSize>polyOrder) :
        windowSize=windowSize
    elif windowSize<= polyOrder:
        dlgBox(exceptionTitle='Warning', 
               exceptionMsg= "Window size was smaller than the polynomial order. Value was reset to %s" % (polyOrder+1),
               type="Warning")
        windowSize=polyOrder+1
    else:
        print('Window size is even. Adding 1 to make it odd.')
        windowSize=windowSize+1
          
    dataOut = savgol_filter(inputData, polyorder=polyOrder, window_length=windowSize, axis=0)
    dataOut[dataOut < 0] = 0 # Remove any values that are below 0
    return dataOut
# ------------ #
 
def normalizeMS(inputData = None):
    # Normalize data to maximum intensity of 1
    normData = np.divide(inputData.astype(np.float64), np.max(inputData))
    return normData
# ------------ #
 
def normalizeIMS(inputData = None, mode='Maximum'):
    """
    Normalize 2D array to appropriate mode
    """
    inputData = np.nan_to_num(inputData)
#      Normalize 2D array to maximum intensity of 1
    if mode == "Maximum":
        normData = normalize(inputData.astype(np.float64), axis=0, norm='max')
    elif mode == 'Logarithmic':
        normData = np.log10(inputData.astype(np.float64))
    elif mode == 'Natural log':
         normData = np.log(inputData.astype(np.float64))
    elif mode == 'Square root':
         normData = np.sqrt(inputData.astype(np.float64))
    elif mode == 'Least Abs Deviation':
         normData = normalize(inputData.astype(np.float64), axis=0, norm='l1')
    elif mode == 'Least Squares':
         normData = normalize(inputData.astype(np.float64), axis=0, norm='l2')
     #TODO add except ValueError which will return raw data
    return normData
# ------------ #
 
def smooth1D(data=None, sigma=1):
    """
    This function uses Gaussian filter to smooth 1D data
    """
    if data is None or len(data) == 0:
        return None
    if sigma < 0: 
        dlgBox(exceptionTitle='Warning', 
               exceptionMsg= "Value of sigma is too low. Value was reset to 1",
               type="Warning")
        sigma=1
    else:
        sigma=sigma
    dataOut = gaussian_filter(data, sigma = sigma, order=0)
    return dataOut
 
def removeNoise(inputData=None, threshold=0):
    # Check whether threshold values meet the criteria.
    # First check if value is not above the maximum or below 0
    if (threshold > np.max(inputData)) or (threshold < 0):
        dlgBox(exceptionTitle='Warning', 
               exceptionMsg= "Threshold value was too high - the maximum value is %s. Value was reset to 0. Consider reducing your threshold value." % np.max(inputData), 
               type="Warning")
        threshold=0
    elif threshold == 0.0:
        pass
    # Check if the value is a fraction (i.e. if working on a normalized dataset)
    elif (threshold < (np.max(inputData)/10000)): # This is somewhat guesswork! It won't be 100 % fool proof
        if (threshold > 1) or (threshold <= 0):
            threshold=0
        dlgBox(exceptionTitle='Warning', 
               exceptionMsg= "Threshold value was too low - the maximum value is %s. Value was reset to 0. Consider increasing your threshold value." % np.max(inputData), 
               type="Warning")
        threshold=0
    # Or leave it as is if the values are correct
    else:
        threshold=threshold
         
    inputData[inputData<=threshold] = 0
    return inputData    
 
def computeRMSD(inputData1 = None, inputData2 = None):
    """
    Compute the RMSD for a part of arrays
    """
    if isempty(inputData1) or isempty(inputData2):
        print('Make sure you pick more than one file')
        return
    elif inputData1.shape != inputData2.shape:
        print("The two arrays are of different size! Cannot compare.")
        return
    else: 
        # Before computing RMSD, we need to normalize to 1
        tempArray = (normalizeIMS(inputData=inputData1)-
                     normalizeIMS(inputData=inputData2))
        tempArray2 = tempArray**2
        RMSD = ((np.average(tempArray2))**0.5)
        pRMSD = RMSD * 100
         
    return pRMSD, tempArray
         
def computeRMSF(inputData1 = None, inputData2 = None):
    """
    Compute the pairwise RMSF for a pair of arrays. RMSF is computed by comparing 
    each individual voltage separately
    """
    if isempty(inputData1) or isempty(inputData2):
        print('Make sure you pick more than file')
        return
    elif inputData1.shape != inputData2.shape:
        print("The two arrays are of different size! Cannot compare.")
        return
    else:
        pRMSFlist = []
        size = len(inputData1[1,:])
        for row in range(0,size,1):
            # Before computing the value of RMSF, we have to normalize to 1 
            # to convert to percentage
            inputData1norm = normalizeMS(inputData=inputData1[:,row])
            np.nan_to_num(inputData1norm, copy=False)
            inputData2norm = normalizeMS(inputData=inputData2[:,row])
            np.nan_to_num(inputData2norm, copy=False)
            # Compute difference
            tempArray = (inputData1norm - inputData2norm) 
            tempArray2 = tempArray**2
            # Calculate RMSF/D value
            RMSF = ((np.average(tempArray2))**0.5)
            pRMSF = RMSF * 100
            pRMSFlist.append(pRMSF)
    return pRMSFlist
 
def computeVariance(inputData = None):
    output = np.var(inputData, axis=0)
    return output
 
def computeMean(inputData = None):
    output = np.mean(inputData, axis=0)
    return output
     
def computeStdDev(inputData = None):
    output = np.std(inputData, axis=0)
    return output
 
def binMSdata(x=None, y=None, bins=None, binmode="Bin"):
    """Bin data"""
    # Bin data using numpy histogram function
    if binmode == "Bin":
        msYbin, edges = np.histogram(x, bins=bins, weights=y)
    return msYbin
     
def sumMSdata(ydict=None):
    """
    Sum binned data
    Input
    -----
    ydict : dictionary with binned X/Y values
    Output
    ------
    """
    msOut = []
    # Extract y-data from dictionary
    for key in ydict:
        msOut.append(ydict[key][1])
    # Sum into one Y-axis list
    msSum = np.sum(msOut, axis=0)
    
#     msYsum = []
#     for key in ydict:
#         msYsum.append(ydict[key][1])
#     # Sum data
#     msYsummed = [sum(i) for i in zip(*msYsum)]
#     return ydict[key][0], msYsummed

    return ydict[key][0], msSum
     
def sumMSdata2RT(ydict=None):
    """ sum data in direction to obtain retention times plot """
    rtX, rtY = [],[]
    for key in ydict:
        rtX.append(key)
        rtY.append(np.sum(ydict[key][1]))
    # Return data
    return np.asarray(rtX), np.asarray(rtY)
    
def abline(x_vals, slope, intercept):
    """
    Calculate xy coords for a line from slope and intercept
    x_vals: tuple of (xmin, xmax) : float
    slope: slope : float
    intercept: float
    """
    y_vals = intercept + slope * x_vals
    return x_vals, y_vals
     
def smooth_1D(data=None, smoothMode='Gaussian', **kwargs):
    """
    This function uses Gaussian filter to smooth 1D data
    """
    if smoothMode == 'Gaussian':
        sigma = kwargs.pop('sigma')
        if data is None or len(data) == 0:
            return None
        if sigma < 0: 
            sigma=1
        # Smooth array
        try:
            dataOut = gaussian_filter(data, sigma=sigma, order=0)
        except (ValueError, TypeError, MemoryError), error:
            return data
        return dataOut
    
    elif smoothMode == 'Savitzky-Golay':
        polyOrder = kwargs.pop('polyOrder')
        windowSize = kwargs.pop('windowSize')
        # Check if input data is there
        if data is None or len(data) == 0:
            return None
#         # Check whether polynomial order is of correct size
#         if (polyOrder<=0):
#             polyOrder=2   
#         # Check whether window size is of correct size
#         if windowSize is None:
#             windowSize = polyOrder+1
#         elif windowSize<= polyOrder:
#             windowSize=polyOrder+1
#         else:
#             windowSize=windowSize+1

        try:
            dataOut = savgol_filter(data, polyorder=polyOrder, 
                                    window_length=windowSize, 
                                    axis=0)
        except (ValueError, TypeError, MemoryError), error:
            print(error)
#             pub.sendMessage('errorUpdate', dataOut=["%s" % error, 4])
            return data
        # Remove values below zero
        dataOut[dataOut < 0] = 0 # Remove any values that are below 0
        return dataOut
    else:
        return data
 
def nearest(array, target):
    """
    In an sorted array, quickly find the position of the element closest to the target.
    :param array: Array
    :param target: Value
    :return: np.argmin(np.abs(array - target))
    """
    i = bisect_left(array, target)
    if i <= 0:
        return 0
    elif i >= len(array) - 1:
        return len(array) - 1
    if np.abs(array[i] - target) > np.abs(array[i - 1] - target):
        i -= 1
    return i
 
def get_linearization_range(mzStart, mzEnd, binsize, mode):
    if mode in ["Linear m/z", "Linear interpolation"]:
        msList = np.arange(mzStart, mzEnd, binsize)
    else:
        msList = nonlinear_axis(mzStart, mzEnd, mzStart / binsize)
        
    return msList
 
def linearize(data, binsize, mode, input_list=[]):
    if len(input_list) == 0:
        length = len(data)
        firstpoint = math.ceil(data[0, 0] / binsize) * binsize
        lastpoint = math.floor(data[length - 1, 0] / binsize) * binsize
        
        if mode in ["Linear m/z", "Linear interpolation"]:
    #     if mode in [0, 3]:
            intx = np.arange(firstpoint, lastpoint, binsize)
        else:
            intx = nonlinear_axis(firstpoint, lastpoint, firstpoint / binsize)
    else:
        intx = input_list
    
    if mode in ["Linear m/z", "Linear resolution"]:
#     if mode < 2:
        newdat = lintegrate(data, intx)
    else:
        newdat = linterpolate(data, intx)
        
    # unpact to x and y list
    xvals = newdat[:, 0]
    yvals = newdat[:, 1]
    
    return xvals, yvals

def nonlinear_axis(start, end, res):
    """
    Creates a nonlinear axis with the m/z values spaced with a defined and constant resolution.
    :param start: Minimum m/z value
    :param end: Maximum m/z value
    :param res: Resolution of the axis ( m / delta m)
    :return: One dimensional array of the nonlinear axis.
    """
    axis = []
    i = start
    axis.append(i)
    i += i / float(res)
    while i < end:
        axis.append(i)
        i += i / float(res)
    return np.array(axis)
     
def linear_interpolation(x1, x2, x):
    """
    :param x1:
    :param x2:
    :param x:
    :return: float(x - x1) / float(x2 - x1)
    """
    return float(x - x1) / float(x2 - x1)

def lintegrate(data, intx):
    """
    Linearize x-axis by integration.

    Each intensity value in the old data gets proportionally added into the new x-axis.

    The total sum of the intensity values should be constant.
    :param data: Data array
    :param intx: New x-axis for data
    :return: Integration of intensity from original data onto the new x-axis.
        Same shape as the old data but new length.
    """
    length = len(data)
    inty = np.zeros_like(intx)
    for i in range(0, length):
        if intx[0] < data[i, 0] < intx[len(intx) - 1]:
            index = nearest(intx, data[i, 0])
            if intx[index] == data[i, 0]:
                inty[index] += data[i, 1]
            if intx[index] < data[i, 0] and index < length - 1:
                index2 = index + 1
                interpos = linear_interpolation(intx[index], intx[index2], data[i, 0])
                inty[index] += (1 - interpos) * data[i, 1]
                inty[index2] += interpos * data[i, 1]
            if intx[index] > data[i, 0] and index > 0:
                index2 = index - 1
                interpos = linear_interpolation(intx[index], intx[index2], data[i, 0])
                inty[index] += (1 - interpos) * data[i, 1]
                inty[index2] += interpos * data[i, 1]
    newdat = np.column_stack((intx, inty))
    return newdat

def interpolate(x_short, y_short, x_long):
     
    fcn = interp1d(x_short, y_short, fill_value=0, bounds_error=False)
    new_y_long = fcn(x_long)
    return  x_long, new_y_long

def linterpolate(data, intx):
    """
    Linearize x-axis by interpolation.
 
    The new x-axis is interpolated on the old data and the corresponding intensities and picked out.
 
    :param data: Data array
    :param intx: New x-axis
    :return: Interpolation of intensity from original data onto the new x-axis.
        Same shape as the old data but new length.
    """
    f = interp1d(data[:, 0], data[:, 1], fill_value=0, bounds_error=False)
    inty = f(intx)
    return np.column_stack((intx, inty))
     
def nonlinearize(data, num_compressed):
    """
    Compress the data in a simple and nonlinear way.
    :param data: Data array (N x 2)
    :param num_compressed:
    :return:
    """
    if num_compressed == 0:
        return data
    else:
        num_compressed = int(num_compressed)
        return np.array([np.mean(data[index:index + num_compressed], axis=0) for index in
                         xrange(0, len(data), num_compressed)])
     
     
     
     
     
     
     
     
     
     
     
     
     
     
     
     
     
     
     
     
     
     
     
     
     
     
     