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
from scipy.signal import savgol_filter 
from scipy.ndimage import gaussian_filter
from sklearn.preprocessing import normalize
from gui_elements.misc_dialogs import dlgBox

def adjust_min_max_intensity(inputData=None, min_threshold=0.0, max_threshold=1.0): # threshold2D
    
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
    min_threshold = min_threshold * data_max
    max_threshold = max_threshold * data_max
    
    # Adjust minimum threshold
    inputData[inputData <= min_threshold] = 0
    
    # Adjust maximum threshold
    inputData[inputData >= max_threshold] = data_max
    
    return inputData

def remove_noise_2D(inputData=None, threshold=0): # removeNoise
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

def smooth_gaussian_2D(inputData = None, sigma = 2): # smoothDataGaussian
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
 
def smooth_savgol_2D(inputData = None, polyOrder = 2, windowSize = 5): # smoothDataSavGol
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
 
def normalize_2D(inputData = None, mode='Maximum'): # normalizeIMS
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

