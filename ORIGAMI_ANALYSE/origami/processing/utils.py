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
from __future__ import division
import numpy as np
from operator import itemgetter
from itertools import groupby
from time import time as ttime
from scipy.signal import find_peaks # @UnresolvedImport

def detect_peaks_chromatogram(data, threshold, add_buffer=0): # detectPeaksRT
    """
    This function searches for split in the sequence of numbers (when signal goes to 0)
    and returns the xy coordinates for the rectangle to be plotted
    ---
    output : list of tuples, start and end x coordinates
    """
    inxY = np.where(data[:,1] > threshold)
    valX = data[inxY,0]
    valY = data[inxY,1]
    valXX = valX.astype(int).tolist()[0]
    # Find index values
    outlist = []
    apex_list = []
    for k, g in groupby(enumerate(valXX), lambda (i,x):i-x):
        x = (map(itemgetter(1), g)) # list of vals
        xStart = x[0] # get x start
        xEnd = x[-1] # get x end
        
        if (xStart-xEnd) == 0:
            apex_list.append([xStart, xEnd])
            xStart = xStart - add_buffer
            xEnd = xEnd + add_buffer
            
        
        outlist.append([xStart,xEnd])
        
    # pair list
    outlistRav = np.ravel(outlist)-1
    try:
        valXout = data[outlistRav, 0]
        valYout = data[outlistRav, 1]
        output = np.array(zip(valXout,valYout))
    except IndexError:
        output = []
    # apex list
    try:
        apexListRav = np.ravel(apex_list)-1
        apexListRav = np.unique(apexListRav)
        valXout = data[apexListRav, 0]
        valYout = data[apexListRav, 1]
        apexlist = np.array(zip(valXout,valYout))
    except IndexError:
        apexlist = []
    
    return output, outlist, apexlist

def detect_peaks_spectrum2(xvals, yvals, window=10, threshold=0):
    peaks, __ = find_peaks(yvals, distance=window, threshold=threshold)
    
    mzs, ints = xvals[peaks], yvals[peaks]
    
    return np.transpose([mzs, ints])

def detect_peaks_spectrum(data, window=10, threshold=0, mzRange=None): # detectPeaks1D
    """
    Peak detection tool.
    Modified to include a mz range (i.e to only search in specified region)
    ---
    Parameters:
    ---
    data: array [ms, intensity]
    window: float 
    threshold: float
    mzRange: tuple (ms start, ms end)
    """
#     tstart = ttime()
    
    peaks = []
    if mzRange!=None:
        mzStart = np.argmin(np.abs(data[:,0] - mzRange[0]))
        mzEnd = np.argmin(np.abs(data[:,0] - mzRange[1]))
        data = data[mzStart:mzEnd,:]
        
    length = len(data)
    maxval = np.amax(data[:, 1])
    for i in xrange(1, length):
        if data[i, 1] > maxval * threshold:
            start = i - window
            end = i + window
            if start < 0: start = 0
            if end > length: end = length
            testmax = np.amax(data[int(start):int(end) + 1, 1])
            if data[i, 1] == testmax and data[i, 1] != data[i - 1, 1]:
                peaks.append([data[i, 0], data[i, 1]])
    
#     print("It took {:.4f} seconds to search spectrum".format(ttime()-tstart))            
    
    return np.array(peaks)

def find_peak_maximum(data, fail_value=1): # findPeakMax
    """
    Simple tool to find the intensity (maximum) of a selected peak
    ---
    data: array [ms, intensity]
    return max value
    """
    try:
        ymax = np.amax(data[:,1])
    except ValueError: 
        print('Failed to find value. Ymax set to maximum, {}'.format(fail_value))
        ymax = fail_value
    return ymax

def find_peak_maximum_1D(yvals, fail_value=1):
    try: ymax = np.amax(yvals)
    except: ymax = 1
    return ymax

def get_narrow_data_range(data, mzRange=None): # getNarrow1Ddata
    """ Find and return a narrow data range """
    start = np.argmin(np.abs(data[:,0] - mzRange[0]))
    end = np.argmin(np.abs(data[:,0] - mzRange[1]))
    
    if start > end: end, start = start, end
    
    dataOut = data[start:end,:] 
    return dataOut

def get_narrow_data_range_1D(xvals, yvals, x_range=None):
    start = np.argmin(np.abs(xvals - x_range[0]))
    end = np.argmin(np.abs(xvals - x_range[1]))
    
    if start > end: end, start = start, end
    return xvals[start:end], yvals[start:end]
    
    
    
    
    
    
    
    
    
    
    