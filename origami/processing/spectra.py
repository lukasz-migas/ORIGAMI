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

import math
import numpy as np
from bisect import bisect_left
from scipy.signal import savgol_filter
from scipy.ndimage import gaussian_filter
from gui_elements.misc_dialogs import dlgBox
from scipy.interpolate.interpolate import interp1d


def remove_noise_1D(inputData=None, threshold=0):
    # Check whether threshold values meet the criteria.
    # First check if value is not above the maximum or below 0
    if (threshold > np.max(inputData)) or (threshold < 0):
        dlgBox(
            exceptionTitle='Warning',
            exceptionMsg="Threshold value was too high - the maximum value is %s. Value was reset to 0. Consider reducing your threshold value." %
            np.max(inputData),
            type="Warning")
        threshold = 0
    elif threshold == 0.0:
        pass
    # Check if the value is a fraction (i.e. if working on a normalized dataset)
    elif (threshold < (np.max(inputData) / 10000)):  # This is somewhat guesswork! It won't be 100 % fool proof
        if (threshold > 1) or (threshold <= 0):
            threshold = 0
        dlgBox(
            exceptionTitle='Warning',
            exceptionMsg="Threshold value was too low - the maximum value is %s. Value was reset to 0. Consider increasing your threshold value." %
            np.max(inputData),
            type="Warning")
        threshold = 0
    # Or leave it as is if the values are correct
    else:
        threshold = threshold

    inputData[inputData <= threshold] = 0
    return inputData


def normalize_1D(inputData=None, mode="Maximum"):  # normalizeMS
    # Normalize data to maximum intensity of 1
    try:
        inputData = inputData.astype(np.float64)
    except AttributeError:
        inputData = np.array(inputData, dtype=np.float64)

    if mode == "Maximum":
        max_val = np.max(inputData)
        normData = np.divide(inputData, max_val)
    elif mode == 'tic':
        normData = np.divide(inputData.astype(np.float64), np.sum(inputData))
        normData = np.divide(normData.astype(np.float64), np.max(normData))

    return normData


def check_mass_range(ms_list=None, ms_dict=None):
    """
    Check what is the minimum and maximum value in the list/dictionary of mass spectra
    to ensure that the linearisation range is correct
    """
    mz_min, mz_max = [], []
    if ms_dict is not None:
        for key in ms_dict:
            mz_min.append(ms_dict[key]['xvals'][0])
            mz_max.append(ms_dict[key]['xvals'][-1])

    if ms_list is not None:
        for i in range(len(ms_list)):
            mz_min.append(ms_dict[i]['xvals'][0])
            mz_max.append(ms_dict[i]['xvals'][-1])

    # determine min and maximum value from the list
    return np.min(mz_min), np.max(mz_max)


def interpolate(x_short, y_short, x_long):

    fcn = interp1d(x_short, y_short, fill_value=0, bounds_error=False)
    new_y_long = fcn(x_long)
    return x_long, new_y_long


def linearize_data(msX, msY, **kwargs):

    if 'auto_range' in kwargs:
        if kwargs['auto_range']:
            mzStart = msX[0]
            mzEnd = msY[-1]
        else:
            mzStart = kwargs['mz_min']
            mzEnd = kwargs['mz_max']
    else:
        mzStart = kwargs['mz_min']
        mzEnd = kwargs['mz_max']

    binsize = kwargs['mz_bin']
    msCentre = get_linearization_range(mzStart, mzEnd, binsize, kwargs['linearization_mode'])

    msCentre, msYbin = linearize(data=np.transpose([msX, msY]), binsize=binsize,
                                 mode=kwargs['linearization_mode'],
                                 input_list=msCentre)
    msYbin = np.nan_to_num(msYbin)

    return msCentre, msYbin


def crop_1D_data(msX, msY, **kwargs):
    """
    @param msX (list): x-axis list
    @param msY (list): y-axis list
    """

    crop_min, crop_max = kwargs['min'], kwargs['max']

    # get data min, max
    data_min, data_max = np.min(msX), np.max(msX)

    # check if data is in appropriate range
    if crop_min < data_min:
        crop_min = data_min

    if crop_max > data_max:
        crop_max = data_max

    if crop_min == crop_max:
        print("Please widen the mass range")
        return msX, msY

    # get spectrum
    spectrum = np.transpose([msX, msY])
    spectrum = getNarrow1Ddata(spectrum, mzRange=(crop_min, crop_max))

    return spectrum[:, 0], spectrum[:, 1]


def sum_1D(data):  # sumClassMSdata
    """
    @param data (dict): dictionary with mass spectra [keys: xvals, yvals]
    """
    # Retrieve MS data
    ydata = []
    # Iterate over the whole dictionary to retrieve y-axis data
    for idx in range(len(data)):
        ydata.append(data[idx]['yvals'])
    # Sum y-axis data
    msY = np.sum(ydata, axis=0)

    return msY


def sum_1D_dictionary(ydict=None):  # sumMSdata
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

    return ydict[key][0], msSum


def subtract_1D(msY_1, msY_2):  # subtractMS

    # Subtract values
    out_1 = msY_1 - msY_2
    out_2 = msY_1 - msY_2

    # Return all positive/negative values as two lists
    out_1[out_1 < 0] = 0
    out_2[out_2 > 0] = 0

    return out_1, out_2


def smooth_gaussian_1D(data=None, sigma=1):  # smooth1D
    """
    This function uses Gaussian filter to smooth 1D data
    """
    if data is None or len(data) == 0:
        return None
    if sigma < 0:
        dlgBox(exceptionTitle='Warning',
               exceptionMsg="Value of sigma is too low. Value was reset to 1",
               type="Warning")
        sigma = 1
    else:
        sigma = sigma
    dataOut = gaussian_filter(data, sigma=sigma, order=0)
    return dataOut


def smooth_1D(data=None, smoothMode='Gaussian', **kwargs):  # smooth_1D
    """
    This function uses Gaussian filter to smooth 1D data
    """
    if smoothMode == 'Gaussian':
        sigma = kwargs.pop('sigma')
        if data is None or len(data) == 0:
            return None
        if sigma < 0:
            sigma = 1
        # Smooth array
        try:
            dataOut = gaussian_filter(data, sigma=sigma, order=0)
        except (ValueError, TypeError, MemoryError) as error:
            return data
        return dataOut

    elif smoothMode == 'Savitzky-Golay':
        polyOrder = kwargs.pop('polyOrder')
        windowSize = kwargs.pop('windowSize')
        # Check if input data is there
        if data is None or len(data) == 0:
            return None

        try:
            dataOut = savgol_filter(data, polyorder=polyOrder,
                                    window_length=windowSize,
                                    axis=0)
        except (ValueError, TypeError, MemoryError) as error:
            print(error)
            return data
        # Remove values below zero
        dataOut[dataOut < 0] = 0  # Remove any values that are below 0
        return dataOut
    else:
        return data


def bin_1D(x=None, y=None, bins=None, binmode="Bin"):  # binMSdata
    """Bin data"""
    # Bin data using numpy histogram function
    if binmode == "Bin":
        msYbin, __ = np.histogram(x, bins=bins, weights=y)

    return msYbin


def sum_spectrum_to_chromatogram(ydict=None):  # sumMSdata2RT
    """ sum data in direction to obtain retention times plot """
    rtX, rtY = [], []
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
                         range(0, len(data), num_compressed)])
