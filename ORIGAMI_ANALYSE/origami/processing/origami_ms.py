# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
#    Copyright (C) 2017-2018 Lukasz G. Migas 
#    <lukasz.migas@manchester.ac.uk> OR <lukas.migas@yahoo.com>
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
# __author__ lukasz.g.migas

import numpy as np
from operator import itemgetter
from itertools import groupby

def origami_combine_infrared(inputData=None, threshold=2000, noiseLevel=500, sigma=0.5): # combineIRdata
    # TODO: This function needs work - Got to acquire more data to test it properly
    # Create empty lists
    dataList, indexList =[], []
    # Iterate and extract values that are below the IR threshold
    for x in range(len(inputData[1,:])):
        if np.sum(inputData[:,x]) > threshold:
            dataList.append(inputData[:,x])
            indexList.append(x)
              
    # Split the indexList so we have a list of lists of indexes to split data into
    splitlist = [list(map(itemgetter(1), g)) for k, g in groupby(enumerate(indexList), lambda i_x:i_x[0]-i_x[1])]
      
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
 
def origami_combine_linear(imsDataInput, firstVoltage, startVoltage, endVoltage, # combineCEscansLinear
                           stepVoltage, scansPerVoltage):
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
        print(('File has a total of: %s scans. The last scan of CE ramp is %s' %(len(imsDataInput[1,:]), lastVoltage)))
   
    # Pre-calculate X-axis information
    ColEnergyX = np.linspace(startVoltage,endVoltage, num=numberOfVoltages)
    # Crop IMS data to appropriate size (remove start and end regions 'reporter')
    cropIMSdata = imsDataInput[:,int(firstVoltage)::]
    x1 = 0
    # Create an empty array to put data into
    imsDataCEcombined, scanList = [], []
    for i, cv in zip(list(range(int(numberOfVoltages))), ColEnergyX):
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
     
def origami_combine_exponential(imsDataInput, firstVoltage, # combineCEscansExponential
                                startVoltage, endVoltage, stepVoltage, scansPerVoltage,
                                expIncrement, expPercentage, expAccumulator = 0,
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
        print(('File has a total of: %s scans. The last scan of CE ramp is %s' %(len(imsDataInput[1,:]), lastVoltage)))
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
 
def origami_combine_boltzmann(imsDataInput, firstVoltage, # combineCEscansFitted
                              startVoltage, endVoltage, stepVoltage, scansPerVoltage,
                              expIncrement, verbose, A1 = 2, A2 = 0.07, x0 = 47, dx = None):
    
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
        print(('File has a total of: %s scans. The last scan of CE ramp is %s' %(len(imsDataInput[1,:]), lastVoltage)))
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
 
def origami_combine_userDefined(imsDataInput=None, firstVoltage=None, inputList=None): # combineCEscansUserDefined

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
        print(('File has a total of: %s scans. The last scan of CE ramp is %s' %(len(imsDataInput[1,:]), lastVoltage)))
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
 