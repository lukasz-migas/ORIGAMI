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

# This file contains a number of useful functions

from builtins import str
import wx, os, re, random, string, time, shutil
import urllib.request, urllib.error, urllib.parse
import numpy as np
from numpy import savetxt, asarray
from operator import itemgetter
from itertools import groupby
from datetime import datetime
from distutils.version import LooseVersion
from matplotlib.colors import LogNorm, Normalize
from collections import OrderedDict
from ast import literal_eval
from random import randint
import pandas as pd
import pickle as pickle


def mlen(listitem, get_longest=False):

    for i, item in enumerate(listitem):
        print("Item {} has length {}".format(i, len(item)))


def clean_filename(filename):
    filename = filename.replace(".csv", "").replace(".txt", "").replace(".raw", "")
    filename = filename.replace(".tab", "").replace(".RAW", "").replace(".mgf", "")
    filename = filename.replace(".mzML", "").replace(".mzIdentML", "").replace(":", "")
    filename = filename.replace("/", "").replace("~", "").replace("@", "at")
    filename = filename.replace("[", "_").replace("]", "_")

    return filename


def clean_directory(dirpath):
    """Iterate over specified directory and delete all files and directories"""
    for filename in os.listdir(dirpath):
        filepath = os.path.join(dirpath, filename)
        # remove directory
        try: shutil.rmtree(filepath)
        # remove files
        except OSError:
            try: os.remove(filepath)
            except Exception: continue


def _replace_labels(label):
    """ Replace string labels to unicode """

    unicode_label = str(label)
    try:
        if any(_label in unicode_label for _label in ["\u2070", "u2070", "^0"]):
            unicode_label = unicode_label.replace("\u2070", "⁰").replace("u2070", "⁰").replace("^0", "⁰")
        if any(_label in unicode_label for _label in ["\u00B9", "u00B9", "^1"]):
            unicode_label = unicode_label.replace("\u00B9", "¹").replace("u00B9", "¹").replace("^1", "¹")
        if any(_label in unicode_label for _label in ["\u00B2", "u00B2", "^2"]):
            unicode_label = unicode_label.replace("\u00B2", "²").replace("u00B2", "²").replace("^2", "²")
        if any(_label in unicode_label for _label in ["\u00B3", "u00B3", "^3"]):
            unicode_label = unicode_label.replace("\u00B3", "³").replace("u00B1", "³").replace("^3", "³")
        if any(_label in unicode_label for _label in ["\u00B4", "u00B4", "^4"]):
            unicode_label = unicode_label.replace("\u00B4", "⁴").replace("u00B4", "⁴").replace("^4", "⁴")
        if any(_label in unicode_label for _label in ["\u2075", "u2075", "^5"]):
            unicode_label = unicode_label.replace("\u2075", "⁵").replace("u2075", "⁵").replace("^5", "⁵")
        if any(_label in unicode_label for _label in ["\u2076", "u2076", "^6"]):
            unicode_label = unicode_label.replace("\u2076", "⁶").replace("u2076", "⁶").replace("^6", "⁶")
        if any(_label in unicode_label for _label in ["\u2077", "u2077", "^7"]):
            unicode_label = unicode_label.replace("\u2077", "⁷").replace("u2077", "⁷").replace("^7", "⁷")
        if any(_label in unicode_label for _label in ["\u2078", "u2078", "^8"]):
            unicode_label = unicode_label.replace("\u2078", "⁸").replace("u2078", "⁸").replace("^8", "⁸")
        if any(_label in unicode_label for _label in ["\u2079", "u2079", "^9"]):
            unicode_label = unicode_label.replace("\u2079", "⁹").replace("u2079", "⁹").replace("^9", "⁹")
        if any(_label in unicode_label for _label in ["\u2080", "u2080", "*0"]):
            unicode_label = unicode_label.replace("\u2080", "₀").replace("u2080", "₀").replace("*0", "₀")
        if any(_label in unicode_label for _label in ["\u2081", "u2081", "*1"]):
            unicode_label = unicode_label.replace("\u2081", "₁").replace("u2081", "₁").replace("*1", "₁")
        if any(_label in unicode_label for _label in ["\u2082", "u2082", "*2"]):
            unicode_label = unicode_label.replace("\u2082", "₂").replace("u2082", "₂").replace("*2", "₂")
        if any(_label in unicode_label for _label in ["\u2083", "u2083", "*3"]):
            unicode_label = unicode_label.replace("\u2083", "₃").replace("u2083", "₃").replace("*3", "₃")
        if any(_label in unicode_label for _label in ["\u2084", "u2084", "*4"]):
            unicode_label = unicode_label.replace("\u2084", "₄").replace("u2084", "₄").replace("*4", "₄")
        if any(_label in unicode_label for _label in ["\u2085", "u2085", "*5"]):
            unicode_label = unicode_label.replace("\u2085", "₅").replace("u2085", "₅").replace("*5", "₅")
        if any(_label in unicode_label for _label in ["\u2086", "u2086", "*6"]):
            unicode_label = unicode_label.replace("\u2086", "₆").replace("u2086", "₆").replace("*6", "₆")
        if any(_label in unicode_label for _label in ["\u2087", "u2087", "*7"]):
            unicode_label = unicode_label.replace("\u2077", "₇").replace("u2077", "₇").replace("*7", "₇")
        if any(_label in unicode_label for _label in ["\u2088", "u2088", "*8"]):
            unicode_label = unicode_label.replace("\u2088", "₈").replace("u2088", "₈").replace("*8", "₈")
        if any(_label in unicode_label for _label in ["\u2089", "u2089", "*9"]):
            unicode_label = unicode_label.replace("\u2089", "₉").replace("u2089", "₉").replace("*9", "₉")
        if any(_label in unicode_label for _label in ["\R", "\r"]):
            unicode_label = unicode_label.replace("\R", "®").replace("\r", "®")
        if any(_label in unicode_label for _label in ["\u207A", "u207A", "++", "^+"]):
            unicode_label = unicode_label.replace("\u207A", "⁺").replace("u207A", "⁺").replace("++", "⁺").replace("^+", "⁺")
        if any(_label in unicode_label for _label in ["\u207B", "u207B", "--", "^-"]):
            unicode_label = unicode_label.replace("\u207B", "⁻").replace("u207B", "⁻").replace("--", "⁻").replace("^-", "⁻")
        if any(_label in unicode_label for _label in ["\u22C5", "u22C5", ",,", "^,"]):
            unicode_label = unicode_label.replace("\u22C5", "⋅").replace("u22C5", "⋅").replace(",,", "⋅").replace("^,", "⋅")
        if any(_label in unicode_label for _label in ["nan", "NaN"]):
            unicode_label = unicode_label.replace("nan", "").replace("NaN", "")
        if any(_label in unicode_label for _label in ["\u212B", "u212B", "AA", "ang"]):
            unicode_label = unicode_label.replace("\u212B", "Å").replace("u212B", "Å").replace("AA", "Å").replace("ang", "Å")
        if any(_label in unicode_label for _label in ["\u03B1", "u03B1", "alpha", "aaa"]):
            unicode_label = unicode_label.replace("\u03B1", "α").replace("u03B1", "α").replace("alpha", "α").replace("aaa", "α")
        if any(_label in unicode_label for _label in ["\u03B2", "u03B2", "beta", "bbb"]):
            unicode_label = unicode_label.replace("\u03B2", "β").replace("u03B2", "β").replace("beta", "β").replace("bbb", "β")
        if any(_label in unicode_label for _label in ["\u03BA", "u03BA", "kappa", "kkk"]):
            unicode_label = unicode_label.replace("\u03BA", "κ").replace("u03BA", "κ").replace("kappa", "κ").replace("kkk", "κ")
        if any(_label in unicode_label for _label in ["\u0394", "u0394", "delta", "ddd"]):
            unicode_label = unicode_label.replace("\u0394", "Δ").replace("u0394", "Δ").replace("delta", "Δ").replace("ddd", "Δ")
        if any(_label in unicode_label for _label in ["\u03A8", "u03A8", "PSI"]):
            unicode_label = unicode_label.replace("\u03A8", "Ψ").replace("u03A8", "Ψ").replace("PSI", "Ψ")
        if any(_label in unicode_label for _label in ["\u03C8", "u03C8", "psi"]):
            unicode_label = unicode_label.replace("\u03C8", "ψ").replace("u03C8", "ψ").replace("psi", "ψ")
        if any(_label in unicode_label for _label in ["\u03A6", "u03A6", "PHI"]):
            unicode_label = unicode_label.replace("\u03A6", "Φ").replace("u03A6", "Φ").replace("PHI", "Φ")
        if any(_label in unicode_label for _label in ["\u03C6", "u03C6", "phi"]):
            unicode_label = unicode_label.replace("\u03C6", "φ").replace("u03C6", "φ").replace("phi", "φ")
        if any(_label in unicode_label for _label in ["\u03A9", "u03A9", "OMEGA"]):
            unicode_label = unicode_label.replace("\u03A9", "Ω").replace("u03A9", "Ω").replace("OMEGA", "Ω")
        if any(_label in unicode_label for _label in ["\u03C9", "u03C9", "omega"]):
            unicode_label = unicode_label.replace("\u03C9", "ω").replace("u03C9", "ω").replace("omega", "ω")

    except Exception:
        return unicode_label

    return unicode_label


def remove_nan_from_list(data_list):
    data_list = np.asarray(data_list)
    data_list = data_list[~np.isnan(data_list)]
    return data_list


def determineFontColor(rgb, rgb_mode=2, return_rgb=False, return_hex=False):
    """
    This function determines the luminance of background and determines the 
    'best' font color based on that value
    --- LINKS ---
    https://stackoverflow.com/questions/596216/formula-to-determine-brightness-of-rgb-color
    https://stackoverflow.com/questions/1855884/determine-font-color-based-on-background-color
    """

    if rgb_mode == 1:
        a = 1 - (rgb[0] * 0.2126 +
                 rgb[1] * 0.7152 +
                 rgb[2] * 0.0722) / 255
    elif rgb_mode == 2:
        a = 1 - (rgb[0] * 0.299 +
                 rgb[1] * 0.587 +
                 rgb[2] * 0.114) / 255

    elif rgb_mode == 3:
        a = 1 - (np.sqrt(rgb[0]) * 0.299 +
                 np.sqrt(rgb[1]) * 0.587 +
                 np.sqrt(rgb[2]) * 0.114) / 255
    if a < 0.5:
        if return_rgb: return (0, 0, 0)
        elif return_hex: return "#000000"
        else: return "black"
    else:
        if return_rgb: return (255, 255, 255)
        elif return_hex: return "#ffffff"
        else: return "white"


def dir_extra(dirlist, keywords="get"):
    """
    Quickly filter through keywords in dir list
    -----
    Usage:
        print(dir_extra(dir(line), 'set'))
    """
    # convert string to list
    if type(keywords) == str:
        keywords = [keywords]

    dirlist_out = []
    for item in dirlist:
        for keyword in keywords:
            if keyword in item:
                dirlist_out.append(item)

    return dirlist_out

# def timeit(method):
#
#     def timed(*args, **kw):
#         ts = time.time()
#         result = method(*args, **kw)
#         te = time.time()
#
#         print("It took %2.4f seconds" % (te-ts))
#         return result
#
#     return timed


def randomColorGenerator(return_as_255=False):
    r = lambda: random.randint(0, 255)
    color = (r(), r(), r())
    if return_as_255:
        return color
    else:
        color = convertRGB255to1(color)
    return color


def randomIntegerGenerator(min_int, max_int):
    return randint(min_int, max_int)


def randomStringGenerator(size=5, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))


def merge_two_dicts(dict_1, dict_2):
    combined_dict = dict_1.copy()  # start with x's keys and values
    combined_dict.update(dict_2)  # modifies z with y's keys and values & returns None
    return combined_dict


def get_latest_version(link=None, get_webpage=False):

    if not get_webpage:
        # Search website for all versions
        vers = []
        for line in urllib.request.urlopen(link):
            if 'Update to ORIGAMI-ANALYSE (' in line.decode('utf-8'):
                vers.append(line)
                break
        if len(vers) == 0:
            return None
        # Split the latest one to get newest version
        split = re.split(' |<', vers[0])
        webVersion = None
        for row in split:
            if '(' in row:
                webVersion = row.strip("()")
                break
        return webVersion
    else:
        webpage = urllib.request.urlopen(
            "https://raw.githubusercontent.com/lukasz-migas/ORIGAMI/master/ORIGAMI_ANALYSE/update_info.md")
        return webpage.read().decode('utf-8')


def compare_versions(newVersion, oldVersion):
    return LooseVersion(newVersion) > LooseVersion(oldVersion)


def cleanup_document(document):

    if 'temporary_unidec' in document.massSpectrum:
        del document.massSpectrum['temporary_unidec']

    for spectrum in document.multipleMassSpectrum:
        if 'temporary_unidec' in document.multipleMassSpectrum[spectrum]:
            del document.multipleMassSpectrum[spectrum]['temporary_unidec']

    return document


def saveObject(filename=None, saveFile=None):
    """ 
    Simple tool to save objects/dictionaries
    """
    tstart = time.clock()
    print(''.join(['Saving data...']))
    with open(filename, 'wb') as handle:
        saveFile = cleanup_document(saveFile)
        pickle.dump(saveFile, handle, protocol=pickle.HIGHEST_PROTOCOL)
    tend = time.clock()
    print("Saved document in: {}. It took {:.4f} seconds.".format(filename, (tend - tstart)))


def openObject(filename=None):
    """
    Simple tool to open pickled objects/dictionaries
    """
    if filename.rstrip('/')[-7:] == ".pickle":
        with open(filename, 'rb') as f:
            try:
                return pickle.load(f)
            except Exception as e:
                print(e)
                return None
    else:
        with open(filename + '.pickle', 'rb') as f:
            return pickle.load(f)


def str2num(string):
    try:
        val = float(string)
        return val
    except (ValueError, TypeError):
        return None


def num2str(val, error_value=None):
    try:
        string = str(val)
        return string
    except (ValueError, TypeError):
        return error_value


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


def int2float(num):
    try:
        val = float(num)
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
    return isinstance(input, (int, float, complex))


def checkExtension(input):
    # FIXME add this to the text loader
    """
    This function checks what is the extension of the file to be either saved OR loaded
    """
    fileNameExt = (str.split(input, '.'))
    fileNameExt = fileNameExt[-1]
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


def savaData(fileName, inputData, delimiter):
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
    answer = all(x < y for x, y in zip(L, L[1:]))
    for x, y in zip(L, L[1:]):
        if x > y:
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
        ind = ind[np.in1d(ind, np.unique(np.hstack((indnan, indnan - 1, indnan + 1))), invert=True)]
    # first and last values of x cannot be peaks
    if ind.size and ind[0] == 0:
        ind = ind[1:]
    if ind.size and ind[-1] == x.size - 1:
        ind = ind[:-1]
    # remove peaks < minimum peak height
    if ind.size and mph is not None:
        ind = ind[x[ind] >= mph]
    # remove peaks - neighbors < threshold
    if ind.size and threshold > 0:
        dx = np.min(np.vstack([x[ind] - x[ind - 1], x[ind] - x[ind + 1]]), axis=0)
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


def removeListDuplicates(input, columnsIn=None, limitedCols=None):
    """ remove duplicates from list based on columns """

    df = pd.DataFrame(input, columns=columnsIn)
    df.drop_duplicates(subset=limitedCols, inplace=True)
    output = df.values.tolist()
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
    if mzRange is not None:
        mzStart = np.argmin(np.abs(data[:, 0] - mzRange[0]))
        mzEnd = np.argmin(np.abs(data[:, 0] - mzRange[1]))
        data = data[mzStart:mzEnd, :]
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

# def detectPeaksRT(data, threshold):
#     """
#     This function searches for split in the sequence of numbers (when signal goes to 0)
#     and returns the xy coordinates for the rectangle to be plotted
#     ---
#     output : list of tuples, start and end x coordinates
#     """
#     inxY = np.where(data[:,1] > threshold)
#     valX = data[inxY,0]
#     valY = data[inxY,1]
#     valXX = valX.astype(int).tolist()[0]
#     # Find index values
#     outlist = []
#     for k, g in groupby(enumerate(valXX), lambda (i,x):i-x):
#         x = (map(itemgetter(1), g)) # list of vals
# #         print(x)
#         xStart = x[0] # get x start
#         xEnd = x[-1] # get x end
#         outlist.append([xStart,xEnd])
#     outlistRav = np.ravel(outlist)-1
#     valXout = data[outlistRav,0]
#     valYout = data[outlistRav,1]
#     output = np.array(zip(valXout,valYout))
#     return output, outlist


def findPeakMax(data, fail_value=1):
    """
    Simple tool to find the intensity (maximum) of a selected peak
    ---
    data: array [ms, intensity]
    return max value
    """
    try:
        ymax = np.amax(data[:, 1])
    except ValueError:
        print('Failed to find value. Ymax set to maximum, {}'.format(fail_value))
        ymax = fail_value
    return ymax


def getNarrow1Ddata(data, mzRange=None):
    """
    Find and return a narrow data range
    """
    start = np.argmin(np.abs(data[:, 0] - mzRange[0]))
    end = np.argmin(np.abs(data[:, 0] - mzRange[1]))

    if start > end: end, start = start, end

    dataOut = data[start:end, :]
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
        print(''.join(["Cannot save file: '", filename, "' as it is currently open."]))
        return
    print(''.join(["Saved: ", filename]))


def getTime():
    return datetime.now().strftime('%d-%m-%Y %H:%M:%S')


def find_nearest(array, value):
    idx = (np.abs(array - value)).argmin()
    return array[idx], idx


def roundRGB(rgbList, decimals=3):
    rgbList = list([round(rgbList[0], decimals),
                    round(rgbList[1], decimals),
                    round(rgbList[2], decimals)])
    return rgbList


def convertHEXtoRGB255(hex, decimals=3):
    hex = hex.lstrip('#')
    hlen = len(hex)
    return tuple(int(hex[i:i + int(hlen / 3)], 16) for i in range(0, hlen, int(hlen / 3)))


def convertHEXtoRGB1(hex, decimals=3):
    hex = hex.lstrip('#')
    hlen = len(hex)
    rgb = tuple(int(hex[i:i + int(hlen / 3)], 16) for i in range(0, int(hlen), int(hlen / 3)))
    return [np.round(rgb[0] / 255., decimals), np.round(rgb[1] / 255., decimals), np.round(rgb[2] / 255., decimals)]


def convertRGB255to1(rgbList, decimals=3):
    rgbList = list([round((np.float(rgbList[0]) / 255), decimals),
                    round((np.float(rgbList[1]) / 255), decimals),
                    round((np.float(rgbList[2]) / 255), decimals)])
    return rgbList


def convertRGB1to255(rgbList, decimals=3, as_integer=False, as_tuple=False):
    if not as_integer:
        rgbList = list([np.round((np.float(rgbList[0]) * 255), decimals),
                        np.round((np.float(rgbList[1]) * 255), decimals),
                        np.round((np.float(rgbList[2]) * 255), decimals)])
    else:
        try:
            rgbList = list([int((np.float(rgbList[0]) * 255)),
                            int((np.float(rgbList[1]) * 255)),
                            int((np.float(rgbList[2]) * 255))])
        except ValueError:
            rgbList = eval(rgbList)
            rgbList = list([int((np.float(rgbList[0]) * 255)),
                            int((np.float(rgbList[1]) * 255)),
                            int((np.float(rgbList[2]) * 255))])

    if not as_tuple:
        return rgbList
    else:
        return tuple(rgbList)


def convertRGB1toHEX(rgbList):

        return '#{:02x}{:02x}{:02x}'.format(int((np.float(rgbList[0]) * 255)),
                                            int((np.float(rgbList[1]) * 255)),
                                            int((np.float(rgbList[2]) * 255)))


def convertRGB255toHEX(rgbList):

        return '#{:02x}{:02x}{:02x}'.format(int((np.float(rgbList[0]))),
                                            int((np.float(rgbList[1]))),
                                            int((np.float(rgbList[2]))))


def find_limits(xvals, yvals):
    xouts, youts = [], []

    # Iterate over dictionary to find minimum values for each key
    for key in xvals:
        xouts.append(np.min(xvals[key]))
        xouts.append(np.max(xvals[key]))
        youts.append(np.min(yvals[key]))
        youts.append(np.max(yvals[key]))

    return xouts, youts


def find_limits_list(xvals, yvals):
    xouts, youts = [], []

    # Iterate over dictionary to find minimum values for each key
    for i in range(len(xvals)):
        xouts.append(np.min(xvals[i]))
        xouts.append(np.max(xvals[i]))
        youts.append(np.min(yvals[i]))
        youts.append(np.max(yvals[i]))

    return xouts, youts


def find_limits_all(xvals, yvals):
    xouts, youts = [], []

    if isinstance(xvals, dict):
        for key in xvals:
            xouts.append(np.min(xvals[key]))
            xouts.append(np.max(xvals[key]))
    elif any(isinstance(el, list) for el in xvals):
        for i in range(len(xvals)):
            xouts.append(np.min(xvals[i]))
            xouts.append(np.max(xvals[i]))
    elif any(isinstance(el, np.ndarray) for el in xvals):
        for i in range(len(xvals)):
            xouts.append(np.min(xvals[i]))
            xouts.append(np.max(xvals[i]))
    else:
        xouts = xvals

    if isinstance(yvals, dict):
        for key in yvals:
            youts.append(np.min(yvals[key]))
            youts.append(np.max(yvals[key]))
    elif any(isinstance(el, list) for el in yvals):
        for i in range(len(yvals)):
            youts.append(np.min(yvals[i]))
            youts.append(np.max(yvals[i]))
    elif any(isinstance(el, np.ndarray) for el in yvals):
        for i in range(len(yvals)):
            youts.append(np.min(yvals[i]))
            youts.append(np.max(yvals[i]))
    else:
        youts = yvals

    # find limits
    xlimits = [np.min(xouts), np.max(xouts)]
    ylimits = [np.min(youts), np.max(youts)]

    return xlimits, ylimits


def sort_dictionary(dictionary, key='key'):
    """
    Sort OrderedDict based on key value
    """
    if key != 'key':
        return OrderedDict(sorted(iter(dictionary.items()), key=lambda x: x[1][key]))
    else:
        return OrderedDict(sorted(list(dictionary.items()), key=lambda x: x[0]))


def make_rgb(x, color):
    """
    Convert array to specific color
    """
    # Get size of the input array
    y_size, x_size = x.shape

    # Create an empty 3D array
    rgb = np.zeros([y_size, x_size, 3], dtype='d')

    # Make sure color is an rgb format and not string format
    try:
        color = literal_eval(color)
    except Exception:
        color = color

    # Check color range is 0-1
    if np.max(color) > 1.0:
        color = remap_values(color, 0, 1, type_format='float')

    # Represent as color range
    r_color, g_color, b_color = color

    # Red channel
    if r_color > 0:
        r_rgb = remap_values(x, 0, r_color, type_format='float')
    else:
        r_rgb = np.zeros_like(x)

    # Green channel
    if g_color > 0:
        g_rgb = remap_values(x, 0, g_color, type_format='float')
    else:
        g_rgb = np.zeros_like(x)

    # Blue channel
    if b_color > 0:
        b_rgb = remap_values(x, 0, b_color, type_format='float')
    else:
        b_rgb = np.zeros_like(x)

    # Add to 3D array
    rgb[:, :, 0] = r_rgb
    rgb[:, :, 1] = g_rgb
    rgb[:, :, 2] = b_rgb

    return rgb


def remap_values(x, nMin, nMax, oMin=None, oMax=None, type_format='int'):

    if oMin is None:
        oMin = np.min(x)
    if oMax is None:
        oMax = np.max(x)

    # range check
    if oMin == oMax:
        print("Warning: Zero input range")
        return None

    if nMin == nMax:
        print("Warning: Zero input range")
        return None

    # Check that values are of correct type
    if type_format == 'float':
        nMin = float(nMin)
        nMax = float(nMax)

    # check reversed input range
    reverseInput = False
    oldMin = min(oMin, oMax)
    oldMax = max(oMin, oMax)
    if not oldMin == oMin:
        reverseInput = True

    # check reversed output range
    reverseOutput = False
    newMin = min(nMin, nMax)
    newMax = max(nMin, nMax)
    if not newMin == nMin :
        reverseOutput = True

    portion = (x - oldMin) * (newMax - newMin) / (oldMax - oldMin)
    if reverseInput:
        portion = (oldMax - x) * (newMax - newMin) / (oldMax - oldMin)

    result = portion + newMin
    if reverseOutput:
        result = newMax - portion

    if type_format == 'int':
        return result.astype(int)
    elif type_format == 'float':
        return result.astype(float)
    else:
        return result


def combine_rgb(data_list):
    return np.sum(data_list, axis=0)


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

