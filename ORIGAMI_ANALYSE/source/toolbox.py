# This file contains a number of useful functions
from __future__ import division, print_function
from __builtin__ import str
import os
import zipfile
from numpy import savetxt, asarray
import wx
import numpy as np
from operator import itemgetter
from itertools import *
from datetime import datetime
import re
from distutils.version import LooseVersion

from matplotlib.colors import LogNorm, Normalize
import urllib2 


import origamiStyles
import pickle


def checkVersion(link=None):
    # Search website for all versions
    vers = []
    for line in urllib2.urlopen(link):
        if 'Update to ORIGAMI-ANALYSE (' in line:
            vers.append(line)
            break
    if len(vers) == 0: return None
    # Split the latest one to get newest version
    split = re.split(' |<', vers[0])
    webVersion = None
    for row in split:
        if '(' in row:
            webVersion = row.strip("()")
            break
    
    return webVersion
    
def compareVersions(newVersion, oldVersion):
    return LooseVersion(newVersion) > LooseVersion(oldVersion)

def saveObject(filename=None, saveFile=None):
    """ 
    Simple tool to save objects/dictionaries
    """
#     saveFileName = filename+'/classificationData.pickle' 
    print(''.join(['Saved data in: ', filename]))
    with open(filename, 'wb') as handle:
        pickle.dump(saveFile, handle, protocol=pickle.HIGHEST_PROTOCOL)
        
def openObject(filename=None):
    """
    Simple tool to open pickled objects/dictionaries
    """
    if filename.rstrip('/')[-7:] == ".pickle":
        with open(filename, 'rb') as f:
            try:
                return pickle.load(f)
            except Exception, e:
                return [None, e]
    else:
        with open(filename + '.pickle', 'rb') as f:
            return pickle.load(f)

def str2num(string):
    try:
        val = float(string)
        return val
    except (ValueError, TypeError):
        return None
    
def num2str(val):
    try:
        string = str(val)
        return string
    except (ValueError, TypeError):
        return None

def str2int(string):
    try:
        val = int(string)
        return val
    except (ValueError, TypeError):
        return None

def float2int(num):
    try:
        val = int(num)
        return val
    except (ValueError, TypeError):
        return num
    
def isempty(input):
    try:
        if asarray(input).size == 0 or input is None:
            out = True
        else:
            out = False
    except (TypeError, ValueError, AttributeError):
        print('Could not determine whether object is empty. Output set to FALSE')
        out = False
    return out
    
def str2bool(s):
    if s == 'True':
         return True
    elif s == 'False':
         return False
    else:
         raise ValueError
    
def isnumber(input):
    """ Quick and easy way to check if input is a number """
    return isinstance(input, (int, long, float, complex))
     
def checkExtension(input):
    # FIXME add this to the text loader
    """
    This function checks what is the extension of the file to be either saved OR loaded
    """
    fileNameExt=(str.split(input,'.'))
    fileNameExt=fileNameExt[-1]
    if fileNameExt.lower() == 'csv' or fileNameExt.lower() == 'CSV':
        outDelimiter = ','
        delimiterName = '.csv'
    elif fileNameExt.lower() == 'txt' or fileNameExt.lower() == 'TXT':
        outDelimiter = '\t'
        delimiterName = '.txt'
    else:
        outDelimiter = ','
        delimiterName = '.csv'
    return outDelimiter, delimiterName
        
def savaData(fileName, inputData, delimiter ):
    """
    This function saves data to an array. In case you want to save it in a 
    zipped format, just append .gz to the end of the file
    """
    savetxt(fileName, inputData, delimiter=delimiter, fmt='%f')
    pass

def strictly_increasing(L):
    """
    This function checks if the values in x are always increasing
    If they are not, the  value which flags the problem is returned
    """
    answer  = all(x<y for x, y in zip(L, L[1:]))
    for x,y in zip(L, L[1:]):
        if x>y:
            return y
    return answer

def binData(inputData, binSize):
    print('Bin data ')
    
def getMassRangeFromRawFile(self, path):
    print('End mass')
    
def getScantimeFromRawFile(self, path):
    print('Scan time')
    
def detectPeaks(x, mph=None, mpd=1, threshold=0, edge='rising',
                 kpsh=False, valley=False, show=False, ax=None):

    """Detect peaks in data based on their amplitude and other features.
    __author__ = "Marcos Duarte, https://github.com/demotu/BMC"
    Parameters
    ----------
    x : 1D array_like
        data.
    mph : {None, number}, optional (default = None)
        detect peaks that are greater than minimum peak height.
    mpd : positive integer, optional (default = 1)
        detect peaks that are at least separated by minimum peak distance (in
        number of data).
    threshold : positive number, optional (default = 0)
        detect peaks (valleys) that are greater (smaller) than `threshold`
        in relation to their immediate neighbors.
    edge : {None, 'rising', 'falling', 'both'}, optional (default = 'rising')
        for a flat peak, keep only the rising edge ('rising'), only the
        falling edge ('falling'), both edges ('both'), or don't detect a
        flat peak (None).
    kpsh : bool, optional (default = False)
        keep peaks with same height even if they are closer than `mpd`.
    valley : bool, optional (default = False)
        if True (1), detect valleys (local minima) instead of peaks.
    show : bool, optional (default = False)
        if True (1), plot data in matplotlib figure.
    ax : a matplotlib.axes.Axes instance, optional (default = None).

    Returns
    -------
    ind : 1D array_like
        indeces of the peaks in `x`.

    Notes
    -----
    The detection of valleys instead of peaks is performed internally by simply
    negating the data: `ind_valleys = detect_peaks(-x)`
    
    The function can handle NaN's 

    See this IPython Notebook [1]_.

    References
    ----------
    .. [1] http://nbviewer.ipython.org/github/demotu/BMC/blob/master/notebooks/DetectPeaks.ipynb

    Examples
    --------
    >>> from detect_peaks import detect_peaks
    >>> x = np.random.randn(100)
    >>> x[60:81] = np.nan
    >>> # detect all peaks and plot data
    >>> ind = detect_peaks(x, show=True)
    >>> print(ind)

    >>> x = np.sin(2*np.pi*5*np.linspace(0, 1, 200)) + np.random.randn(200)/5
    >>> # set minimum peak height = 0 and minimum peak distance = 20
    >>> detect_peaks(x, mph=0, mpd=20, show=True)

    >>> x = [0, 1, 0, 2, 0, 3, 0, 2, 0, 1, 0]
    >>> # set minimum peak distance = 2
    >>> detect_peaks(x, mpd=2, show=True)

    >>> x = np.sin(2*np.pi*5*np.linspace(0, 1, 200)) + np.random.randn(200)/5
    >>> # detection of valleys instead of peaks
    >>> detect_peaks(x, mph=0, mpd=20, valley=True, show=True)

    >>> x = [0, 1, 1, 0, 1, 1, 0]
    >>> # detect both edges
    >>> detect_peaks(x, edge='both', show=True)

    >>> x = [-2, 1, -2, 2, 1, 1, 3, 0]
    >>> # set threshold = 2
    >>> detect_peaks(x, threshold = 2, show=True)
    """

    x = np.atleast_1d(x).astype('float64')
    if x.size < 3:
        return np.array([], dtype=int)
    if valley:
        x = -x
    # find indices of all peaks
    dx = x[1:] - x[:-1]
    # handle NaN's
    indnan = np.where(np.isnan(x))[0]
    if indnan.size:
        x[indnan] = np.inf
        dx[np.where(np.isnan(dx))[0]] = np.inf
    ine, ire, ife = np.array([[], [], []], dtype=int)
    if not edge:
        ine = np.where((np.hstack((dx, 0)) < 0) & (np.hstack((0, dx)) > 0))[0]
    else:
        if edge.lower() in ['rising', 'both']:
            ire = np.where((np.hstack((dx, 0)) <= 0) & (np.hstack((0, dx)) > 0))[0]
        if edge.lower() in ['falling', 'both']:
            ife = np.where((np.hstack((dx, 0)) < 0) & (np.hstack((0, dx)) >= 0))[0]
    ind = np.unique(np.hstack((ine, ire, ife)))
    # handle NaN's
    if ind.size and indnan.size:
        # NaN's and values close to NaN's cannot be peaks
        ind = ind[np.in1d(ind, np.unique(np.hstack((indnan, indnan-1, indnan+1))), invert=True)]
    # first and last values of x cannot be peaks
    if ind.size and ind[0] == 0:
        ind = ind[1:]
    if ind.size and ind[-1] == x.size-1:
        ind = ind[:-1]
    # remove peaks < minimum peak height
    if ind.size and mph is not None:
        ind = ind[x[ind] >= mph]
    # remove peaks - neighbors < threshold
    if ind.size and threshold > 0:
        dx = np.min(np.vstack([x[ind]-x[ind-1], x[ind]-x[ind+1]]), axis=0)
        ind = np.delete(ind, np.where(dx < threshold)[0])
    # detect small peaks closer than minimum peak distance
    if ind.size and mpd > 1:
        ind = ind[np.argsort(x[ind])][::-1]  # sort ind by peak height
        idel = np.zeros(ind.size, dtype=bool)
        for i in range(ind.size):
            if not idel[i]:
                # keep peaks with the same height if kpsh is True
                idel = idel | (ind >= ind[i] - mpd) & (ind <= ind[i] + mpd) \
                    & (x[ind[i]] > x[ind] if kpsh else True)
                idel[i] = 0  # Keep current peak
        # remove the small peaks and sort back the indices by their occurrence
        ind = np.sort(ind[~idel])

    if show:
        if indnan.size:
            x[indnan] = np.nan
        if valley:
            x = -x
        _plot(x, mph, mpd, threshold, edge, valley, ax, ind)

    return ind

def removeDuplicates(values):
    output = []
    seen = set()
    for value in values:
        # If value has not been encountered yet,
        # ... add it to both list and set.
        if value not in seen:
            output.append(value)
            seen.add(value)
    return output

def detectPeaks1D(data, window=10, threshold=0, mzRange=None):
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
    ---
    Original author: Michael Marty, UniDec
    """
    peaks = []
    if mzRange!=None:
        mzStart = np.argmin(np.abs(mz[:,0] - mzRange[0]))
        mzEnd = np.argmin(np.abs(mz[:,0] - mzRange[1]))
        data = mz[mzStart:mzEnd,:]
    length = len(data)
    maxval = np.amax(data[:, 1])
    for i in range(1, length):
        if data[i, 1] > maxval * threshold:
            start = i - window
            end = i + window
            if start < 0:
                start = 0
            if end > length:
                end = length
            testmax = np.amax(data[int(start):int(end) + 1, 1])
            if data[i, 1] == testmax and data[i, 1] != data[i - 1, 1]:
                peaks.append([data[i, 0], data[i, 1]])
    return np.array(peaks)

def detectPeaksRT(data, threshold):
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
    for k, g in groupby(enumerate(valXX), lambda (i,x):i-x):
        x = (map(itemgetter(1), g)) # list of vals
#         print(x)
        xStart = x[0] # get x start
        xEnd = x[-1] # get x end
        outlist.append([xStart,xEnd])
    outlistRav = np.ravel(outlist)-1
    valXout = data[outlistRav,0]
    valYout = data[outlistRav,1]
    output = np.array(zip(valXout,valYout))
    return output, outlist

def findPeakMax(data):
    """
    Simple tool to find the intensity (maximum) of a selected peak
    ---
    data: array [ms, intensity]
    return max value
    """
    try:
        ymax = np.amax(data[:,1])
    except ValueError: 
        print('Failed to find value. Ymax set to maximum, 1.')
        ymax = 1
    return ymax

def getNarrow1Ddata(data, mzRange=None):
    """
    Find and return a narrow data range
    """
    start = np.argmin(np.abs(data[:,0] - mzRange[0]))
    end = np.argmin(np.abs(data[:,0] - mzRange[1]))
    
    if start > end: end, start = start, end
    
    dataOut = data[start:end,:] 
    return dataOut

def saveAsText(filename, data, format='%.2f', delimiter=',',
               header=""):
    """
    This function uses np.savetxt to save formatted data to file
    """
    try:
        np.savetxt(filename,
                   np.transpose(data),
                   fmt=format,
                   delimiter=delimiter,
                   header=header)
    except IOError: 
        print(''.join(["Cannot save file: '", filename,"' as it is currently open."]))
        return
    print(''.join(["Saved: ", filename]))

def getTime():
    return datetime.now().strftime('%d-%m-%Y %H:%M:%S')

def find_nearest(array,value):
    idx = (np.abs(array-value)).argmin()
    return array[idx], idx

class MidpointNormalize(Normalize):
    """
    Normalise the colorbar so that diverging bars work there way either side from a prescribed midpoint value)
    e.g. im=ax1.imshow(array, norm=MidpointNormalize(midpoint=0.,vmin=-100, vmax=100))
    """
    def __init__(self, vmin=None, vmax=None, midpoint=None, clip=False):
        self.midpoint = midpoint
        Normalize.__init__(self, vmin, vmax, clip)

    def __call__(self, value, clip=None):
        # I'm ignoring masked values and all kinds of edge cases to make a
        # simple example...
        x, y = [self.vmin, self.midpoint, self.vmax], [0, 0.5, 1]
        return np.ma.masked_array(np.interp(value, x, y))
    
    
    
    
    
    