# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import logging
import math
from bisect import bisect_left

import numpy as np
from gui_elements.misc_dialogs import DialogBox
from processing.utils import get_narrow_data_range
from scipy import sparse
from scipy.interpolate.interpolate import interp1d
from scipy.ndimage import gaussian_filter
from scipy.signal import savgol_filter
from scipy.sparse.linalg import spsolve
from utils.exceptions import MessageError
from utils.ranges import get_min_max
logger = logging.getLogger('origami')


def baseline_als(y, lam, p, niter=10):
    """Asymmetric Least Squares smoothing. There are two parameters p for asymmetry and lambda for smoothness.
    Values of p should range between 0.001 and 0.1 and lambda between 10^2 to 10^9

    """
    from scipy import sparse
    from scipy.sparse.linalg import spsolve
    # taken from: https://stackoverflow.com/questions/29156532/python-baseline-correction-library/29185844
    L = len(y)
    D = sparse.diags([1, -2, 1], [0, -1, -2], shape=(L, L - 2))
    w = np.ones(L)
    while niter > 0:
        W = sparse.spdiags(w, 0, L, L)
        Z = W + lam * D.dot(D.transpose())
        z = spsolve(Z, w * y)
        w = p * (y > z) + (1 - p) * (y < z)
        niter -= 1
        print(niter)
    return z


def remove_noise_1D(data, threshold=0):
    value_max = np.max(data)
    if threshold < 0:
        raise MessageError('Incorrect input', 'Value should be above 0')

    if threshold > value_max:
        raise MessageError('Incorrect input', f'Value {threshold} is above the maximum {value_max}')

    data[data <= threshold] = 0
    return data


def normalize_1D(data, mode='Maximum'):
    # ensure data is in 64-bit format
    data = np.array(data, dtype=np.float64)

    if mode == 'Maximum':
        norm_data = np.divide(data, data.max())
    elif mode == 'Total Ion Current (TIC)':
        norm_data = np.divide(data, np.sum(data))
        norm_data = np.divide(norm_data, norm_data.max())
    elif mode == 'Highest peak':
        norm_data = np.divide(data, data[data.argmax()])
#         norm_data = np.divide(norm_data, norm_data.max())
    elif mode == 'Root Mean Square (RMS)':
        norm_data = np.divide(data, np.sqrt(np.mean(data ** 2)))
#         norm_data = np.divide(norm_data, norm_data.max())
    elif mode == 'Log':
        norm_data = np.divide(data, np.sum(np.log(data[np.nonzero(data)])))
#         norm_data = np.divide(norm_data, norm_data.max())
    elif mode == 'Square root':
        norm_data = np.divide(data, np.sum(np.sqrt(data)))
#         norm_data = np.divide(norm_data, norm_data.max())

    # replace nans
    norm_data = np.nan_to_num(norm_data)

    return norm_data


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

    msCentre, msYbin = linearize(
        data=np.transpose([msX, msY]), binsize=binsize,
        mode=kwargs['linearization_mode'],
        input_list=msCentre,
    )
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
        print('Please widen the mass range')
        return msX, msY

    # get spectrum
    spectrum = np.transpose([msX, msY])
    spectrum = get_narrow_data_range(spectrum, mzRange=(crop_min, crop_max))

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
        DialogBox(
            exceptionTitle='Warning',
            exceptionMsg='Value of sigma is too low. Value was reset to 1',
            type='Warning',
        )
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
            dataOut = savgol_filter(
                data, polyorder=polyOrder,
                window_length=windowSize,
                axis=0,
            )
        except (ValueError, TypeError, MemoryError) as error:
            print(error)
            return data
        # Remove values below zero
        dataOut[dataOut < 0] = 0  # Remove any values that are below 0
        return dataOut
    else:
        return data


def bin_1D(x=None, y=None, bins=None, binmode='Bin'):  # binMSdata
    """Bin data"""
    # Bin data using numpy histogram function
    if binmode == 'Bin':
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
    if mode in ['Linear m/z', 'Linear interpolation']:
        msList = np.arange(mzStart, mzEnd, binsize)
    else:
        msList = nonlinear_axis(mzStart, mzEnd, mzStart / binsize)

    return msList


def linearize(data, binsize, mode, input_list=[]):
    if len(input_list) == 0:
        length = len(data)
        firstpoint = math.ceil(data[0, 0] / binsize) * binsize
        lastpoint = math.floor(data[length - 1, 0] / binsize) * binsize

        if mode in ['Linear m/z', 'Linear interpolation']:
            intx = np.arange(firstpoint, lastpoint, binsize)
        else:
            intx = nonlinear_axis(firstpoint, lastpoint, firstpoint / binsize)
    else:
        intx = input_list

    if mode in ['Linear m/z', 'Linear resolution']:
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
        return np.array([
            np.mean(data[index:index + num_compressed], axis=0) for index in
            range(0, len(data), num_compressed)
        ])


def subtract_spectra(xvals_1, yvals_1, xvals_2, yvals_2, **kwargs):
    n_size_1 = len(xvals_1)
    n_size_2 = len(xvals_2)

    if n_size_1 != n_size_2:
        logger.warning(f'The two spectra are of different size. They will be interpolated to the same scale.')
        # calculate plot size
        ylimits_1 = get_min_max(xvals_1)
        ylimits_2 = get_min_max(xvals_2)
        ylimits = get_min_max(ylimits_1 + ylimits_2)
        # calculate spacing
        if n_size_1 > n_size_2:
            mz_bin = np.diff(xvals_1).mean()
        else:
            mz_bin = np.diff(xvals_1).mean()

        pr_kwargs = {
            'auto_range': False, 'mz_min': ylimits[0], 'mz_max': ylimits[1],
            'mz_bin': mz_bin, 'linearization_mode': 'Linear interpolation',
        }
        xvals_1, yvals_1 = linearize_data(xvals_1, yvals_1, **pr_kwargs)
        xvals_2, yvals_2 = linearize_data(xvals_2, yvals_2, **pr_kwargs)

    # calculate difference
    yvals_1 = yvals_1 - yvals_2

    # create copy of difference
    yvals_2 = np.copy(yvals_1)

    # recreate two arrays
    yvals_1[yvals_1 <= 0] = 0
    yvals_2[yvals_2 >= 0] = 0

    return xvals_1, yvals_1, xvals_2, yvals_2
