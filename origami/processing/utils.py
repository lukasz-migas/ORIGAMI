# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
from itertools import groupby
from operator import itemgetter

import numpy as np
from scipy.signal import find_peaks
from utils.check import check_value_order


def detect_peaks_chromatogram(data, threshold, add_buffer=0):  # detectPeaksRT
    """
    This function searches for split in the sequence of numbers (when signal goes to 0)
    and returns the xy coordinates for the rectangle to be plotted
    ---
    output : list of tuples, start and end x coordinates
    """
    inxY = np.where(data[:, 1] > threshold)
    valX = data[inxY, 0]
    valY = data[inxY, 1]
    valXX = valX.astype(int).tolist()[0]
    # Find index values
    outlist = []
    apex_list = []
    for k, g in groupby(enumerate(valXX), lambda i_x: i_x[0] - i_x[1]):
        x = (list(map(itemgetter(1), g)))  # list of vals
        xStart = x[0]  # get x start
        xEnd = x[-1]  # get x end

        if (xStart - xEnd) == 0:
            apex_list.append([xStart, xEnd])
            xStart = xStart - add_buffer
            xEnd = xEnd + add_buffer

        outlist.append([xStart, xEnd])

    # pair list
    outlistRav = np.ravel(outlist) - 1
    try:
        valXout = data[outlistRav, 0]
        valYout = data[outlistRav, 1]
        output = np.array(list(zip(valXout, valYout)))
    except IndexError:
        output = []
    # apex list
    try:
        apexListRav = np.ravel(apex_list) - 1
        apexListRav = np.unique(apexListRav)
        valXout = data[apexListRav, 0]
        valYout = data[apexListRav, 1]
        apexlist = np.array(list(zip(valXout, valYout)))
    except IndexError:
        apexlist = []

    return output, outlist, apexlist


def detect_peaks_spectrum2(xvals, yvals, window=10, threshold=0):
    peaks, __ = find_peaks(yvals, distance=window, threshold=threshold)

    mzs, ints = xvals[peaks], yvals[peaks]

    return np.transpose([mzs, ints])


def detect_peaks_spectrum(data, window=10, threshold=0, mzRange=None):
    """
    Peak detection tool
    Modified to include a mz range (i.e to only search in specified region)

    Parameters:
    ----------
    data: np.array
        array with m/z and intensity values [ms, intensity]
    window: float
        extraction window
    threshold: float
        minimal intensity
    mzRange: tuple
        user-defined mass range (ms start, ms end)
    """
    if mzRange is not None:
        mzStart = np.argmin(np.abs(data[:, 0] - mzRange[0]))
        mzEnd = np.argmin(np.abs(data[:, 0] - mzRange[1]))
        data = data[mzStart:mzEnd, :]

    peaks = []
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


def find_peak_maximum(data, fail_value=1):
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


def find_peak_maximum_1D(yvals, fail_value=1):
    try:
        ymax = np.amax(yvals)
    except Exception:
        ymax = 1
    return ymax


def find_nearest_index(data, value):
    data = np.asarray(data)
    return np.argmin(np.abs(data - value))


def get_narrow_data_range(data, mzRange=None):  # getNarrow1Ddata
    """ Find and return a narrow data range """
    start = find_nearest_index(data[:, 0], mzRange[0])  # np.argmin(np.abs(data[:, 0] - mzRange[0]))
    end = find_nearest_index(data[:, 0], mzRange[1])  # np.argmin(np.abs(data[:, 0] - mzRange[1]))

    start, end = check_value_order(start, end)

    dataOut = data[start:end, :]
    return dataOut


def get_narrow_data_range_1D(xvals, yvals, x_range=None):
    start = np.argmin(np.abs(xvals - x_range[0]))
    end = np.argmin(np.abs(xvals - x_range[1]))

    if start > end:
        end, start = start, end
    return xvals[start:end], yvals[start:end]


def get_maximum_value_in_range(data, mz_range):
    data = get_narrow_data_range(data, mz_range)
    return find_peak_maximum(data)
