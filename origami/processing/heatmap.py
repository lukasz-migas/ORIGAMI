# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import logging

import numpy as np
from gui_elements.misc_dialogs import dlgBox
from scipy.ndimage import gaussian_filter
from scipy.signal import savgol_filter
from sklearn.preprocessing import normalize
from utils.check import is_prime
logger = logging.getLogger('origami')


def adjust_min_max_intensity(inputData=None, min_threshold=0.0, max_threshold=1.0):  # threshold2D

    # Check min_threshold is larger than max_threshold
    if min_threshold > max_threshold:
        print('Minimum threshold is larger than the maximum. Values were reversed.')
        min_threshold, max_threshold = max_threshold, min_threshold

    # Check if they are the same
    if min_threshold == max_threshold:
        print('Minimum and maximum thresholds are the same.')
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


def remove_noise_2D(inputData, threshold=0):
    data_max = np.max(inputData)
    if threshold > data_max:
        logger.warning(f'Threshold value {threshold} is larger than the maximum value in the data {data_max}')
        return inputData

    inputData[inputData <= threshold] = 0
    return inputData


def smooth_gaussian_2D(inputData=None, sigma=2):  # smoothDataGaussian
    # Check if input data is there
    if inputData is None or len(inputData) == 0:
        return None
    if sigma < 0:
        dlgBox(
            exceptionTitle='Warning',
            exceptionMsg='Value of sigma is too low. Value was reset to 1',
            type='Warning',
        )
        sigma = 1
    else:
        sigma = sigma
    dataOut = gaussian_filter(inputData, sigma=sigma, order=0)
    dataOut[dataOut < 0] = 0
    return dataOut
# ------------ #


def smooth_savgol_2D(inputData=None, polyOrder=2, windowSize=5):  # smoothDataSavGol
    # Check if input data is there
    if inputData is None or len(inputData) == 0:
        return None
    # Check whether polynomial order is of correct size
    if (polyOrder <= 0):
        dlgBox(
            exceptionTitle='Warning',
            exceptionMsg='Polynomial order is too small. Value was reset to 2',
            type='Warning',
        )
        polyOrder = 2
    else:
        polyOrder = polyOrder
    # Check whether window size is of correct size
    if windowSize is None:
        windowSize = polyOrder + 1
    elif (windowSize % 2) and (windowSize > polyOrder):
        windowSize = windowSize
    elif windowSize <= polyOrder:
        dlgBox(
            exceptionTitle='Warning',
            exceptionMsg='Window size was smaller than the polynomial order. Value was reset to %s' %
            (
                polyOrder +
                1
            ),
            type='Warning',
        )
        windowSize = polyOrder + 1
    else:
        print('Window size is even. Adding 1 to make it odd.')
        windowSize = windowSize + 1

    dataOut = savgol_filter(inputData, polyorder=polyOrder, window_length=windowSize, axis=0)
    dataOut[dataOut < 0] = 0  # Remove any values that are below 0
    return dataOut
# ------------ #


def normalize_2D(inputData=None, mode='Maximum'):  # normalizeIMS
    """
    Normalize 2D array to appropriate mode
    """
    inputData = np.nan_to_num(inputData)
#      Normalize 2D array to maximum intensity of 1
    if mode == 'Maximum':
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
    return normData


def interpolate_2D(xvals, yvals, zvals, new_xvals=None, new_yvals=None):
    from scipy.interpolate.interpolate import interp2d
    if new_xvals is None:
        spacing = np.diff(xvals)
        n_bins = len(np.arange(xvals[0], xvals[-1], min(spacing))) + 1
        new_xvals = np.linspace(xvals[0], xvals[-1], n_bins)
    if new_yvals is None:
        spacing = np.diff(yvals)
        n_bins = len(np.arange(yvals[0], yvals[-1], min(spacing))) + 1
        new_yvals = np.linspace(yvals[0], yvals[-1], n_bins)

    fcn = interp2d(xvals, yvals, zvals, kind='linear')
    new_zvals = fcn(new_xvals, new_yvals)

    return new_xvals, yvals, new_zvals


def calculate_division_factors(value, min_division=1, max_division=20, subsampling_default=5):
    """Calculate division factor(s) for DT/MS dataset"""
    division_factors = []
    if is_prime(value):
        print(
            'The x-dimension is a prime number so I cannot bin it. Will downsample with `{}` instead.'.format(
                subsampling_default,
            ),
        )
        return [], subsampling_default
    else:
        for i in range(max_division, min_division, -1):
            if value % i == 0:
                division_factors.append(i)
        if not division_factors:
            print(
                'Failed to find division factor in the range {}-{}. Will downsample with `{}` instead'.format(
                    min_division, max_division, subsampling_default,
                ),
            )
            return [], subsampling_default
        return division_factors, np.max(division_factors)


def subsample_array(data, xvals, division_factor):
    """Downsample array by sampling every n signals"""
    return data[:, ::division_factor], xvals[::division_factor]


def bin_sum_array(data, xvals, division_factor):
    """Downsample array by binning and subsequently summing multiple signals"""
    y_dim, x_dim = data.shape
    new_shape = (y_dim, int(x_dim / division_factor), division_factor)
    if np.prod(new_shape) != data.size:
        raise ValueError(
            "Scale cannot be '{}' as it does will prevent correct reshaping!".format(division_factor) +
            ' Number of items before reshape: {} and after {}'.format(data.size, np.prod(new_shape)),
        )
    return np.reshape(data, new_shape).sum(axis=2), bin_mean_1D_array(xvals, new_shape)


def bin_mean_array(data, xvals, division_factor):
    """Downsample array by binning and subsequently averaging multiple signals"""
    y_dim, x_dim = data.shape
    new_shape = (y_dim, int(x_dim / division_factor), division_factor)
    if np.prod(new_shape) != data.size:
        raise ValueError(
            "Scale cannot be '{}' as it does will prevent correct reshaping!".format(division_factor) +
            ' Number of items before reshape: {} and after {}'.format(data.size, np.prod(new_shape)),
        )
    return np.reshape(data, new_shape).mean(axis=2), bin_mean_1D_array(xvals, new_shape)


def bin_mean_1D_array(xvals, new_shape):
    xvals = np.reshape(xvals, (1, new_shape[1], new_shape[2])).mean(axis=2)
    return np.reshape(xvals, (new_shape[1],))
