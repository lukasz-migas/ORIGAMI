# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import logging

import numpy as np
from processing.utils import find_nearest_index
from processing.utils import nthroot
from scipy.ndimage import gaussian_filter
from scipy.signal import savgol_filter
from sklearn.preprocessing import normalize
from utils.check import check_value_order
from utils.check import is_prime
from utils.exceptions import MessageError

logger = logging.getLogger(__name__)


def adjust_min_max_intensity(inputData=None, min_threshold=0.0, max_threshold=1.0):

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


def remove_noise_2D(inputData, threshold=0):
    data_max = np.max(inputData)
    if threshold > data_max:
        logger.warning(f"Threshold value {threshold} is larger than the maximum value in the data {data_max}")
        return inputData

    inputData[inputData <= threshold] = 0
    return inputData


def crop_2D(xvals, yvals, data, xmin, xmax, ymin, ymax):
    """Crop array"""
    # ensure order of values is correct
    xmin, xmax = check_value_order(xmin, xmax)
    ymin, ymax = check_value_order(ymin, ymax)

    # check if values are not the same
    crop_x = True
    if xmin == xmax:
        crop_x = False
    crop_y = True
    if ymin == ymax:
        crop_y = False

    # find nearest index
    xmin_idx = find_nearest_index(xvals, xmin)
    xmax_idx = find_nearest_index(xvals, xmax)
    ymin_idx = find_nearest_index(yvals, ymin)
    ymax_idx = find_nearest_index(yvals, ymax)

    if crop_x:
        xvals = xvals[xmin_idx : xmax_idx + 1]
        data = data[:, xmin_idx : xmax_idx + 1]

    if crop_y:
        yvals = yvals[ymin_idx : ymax_idx + 1]
        data = data[ymin_idx : ymax_idx + 1]

    return xvals, yvals, data


def smooth_2D(data, mode="Gaussian", **kwargs):

    if mode == "Gaussian":
        data = smooth_gaussian_2D(data, **kwargs)
    elif mode == "Savitzky-Golay":
        data = smooth_gaussian_2D(data, **kwargs)

    # remove values below 0
    data[data < 0] = 0

    return data


def smooth_gaussian_2D(data, **kwargs):
    sigma = kwargs.pop("sigma")

    if sigma < 0:
        raise MessageError("Incorrect value of `sigma`", "Value of `sigma` must be larger than 0")

    dataOut = gaussian_filter(data, sigma=sigma, order=0)

    return dataOut


def smooth_savgol_2D(data, **kwargs):
    # get parameters
    polyOrder = kwargs.pop("polyOrder")
    windowSize = kwargs.pop("windowSize")

    dataOut = savgol_filter(data, polyorder=polyOrder, window_length=windowSize, axis=0)

    return dataOut


def normalize_2D(data, mode="Maximum", **kwargs):
    """Normalize heatmap

    Parameters
    ----------
    data : np.array
        input array
    mode : {'Maximum', 'Logarithmic', 'Natural log', 'Square root', 'Least Abs Deviation', 'Least Squares'}, optional
        normalization mode

    Returns
    -------
    norm_data : np.array
        normalized array
    """
    # replace NaNs with 0s
    data = np.nan_to_num(data)
    # ensure its in float64 formt
    data = data.astype(np.float64)

    # normalize data
    if mode == "None":
        return data

    if mode == "Maximum":
        norm_data = normalize(data, axis=0, norm="max")
    elif mode == "Logarithmic":
        norm_data = np.log10(data)
    elif mode == "Natural log":
        norm_data = np.log(data)
    elif mode == "Square root":
        norm_data = np.sqrt(data)
    elif mode == "Least Abs Deviation":
        norm_data = normalize(data, axis=0, norm="l1")
    elif mode == "Least Squares":
        norm_data = normalize(data, axis=0, norm="l2")
    elif mode == "Median":
        median = np.median(data[data > 0])
        norm_data = data / median
    elif mode == "p-Norm":
        div = nthroot(np.sum(data ** kwargs["p"]), kwargs["p"])
        norm_data = data / div
    elif mode == "Total Intensity":
        div = np.sum(data)
        norm_data = data / div
    elif mode == "Root Mean Square":
        div = np.square(np.mean(np.power(data, 2)))
        norm_data = data / div
    elif mode == "L2":
        div = np.square(np.sum(np.power(data, 2)))
        norm_data = data / div

    # replace NaNs with 0s
    norm_data = np.nan_to_num(norm_data)

    return norm_data


def calculate_interpolation_axes(vals, fold):
    start, end = vals[0], vals[-1]
    new_n_bins = (len(vals) - 1) * fold + 1
    new_vals = np.linspace(start, end, new_n_bins)

    return new_vals


def equalize_heatmap_spacing(xvals, yvals, zvals):

    spacing = np.diff(xvals)
    n_bins = len(np.arange(xvals[0], xvals[-1], min(spacing))) + 1
    new_xvals = np.linspace(xvals[0], xvals[-1], n_bins)

    spacing = np.diff(yvals)
    n_bins = len(np.arange(yvals[0], yvals[-1], min(spacing))) + 1
    new_yvals = np.linspace(yvals[0], yvals[-1], n_bins)

    return interpolate_2D(xvals, yvals, zvals, new_xvals=new_xvals, new_yvals=new_yvals)


def interpolate_2D(xvals, yvals, zvals, fold=1, mode="linear", **kwargs):
    """Interpolate along given axis

    Parameters
    ----------
    xvals : np.array
    yvals : np.array
    zvals : np.array
    fold: float
    mode : {'linear', 'cubic', 'quintic'}, optional

    Returns
    -------
    new_xvals : np.array
    yvals : np.array
    new_zvals : np.array
    """
    from scipy.interpolate.interpolate import interp2d

    mode = mode.lower()

    if fold <= 0:
        raise MessageError("Incorrect value of `fold`", "The value of `fold` must be larger than 0")

    new_xvals = kwargs.pop("new_xvals", xvals)
    if kwargs.get("x_axis", False):
        new_xvals = calculate_interpolation_axes(xvals, fold)

    new_yvals = kwargs.pop("new_yvals", yvals)
    if kwargs.get("y_axis", False):
        new_yvals = calculate_interpolation_axes(yvals, fold)

    fcn = interp2d(xvals, yvals, zvals, kind=mode)
    new_zvals = fcn(new_xvals, new_yvals)

    return new_xvals, new_yvals, new_zvals


def calculate_division_factors(value, min_division=1, max_division=20, subsampling_default=5):
    """Calculate division factor(s) for DT/MS dataset"""
    division_factors = []
    if is_prime(value):
        print(
            "The x-dimension is a prime number so I cannot bin it. Will downsample with `{}` instead.".format(
                subsampling_default
            )
        )
        return [], subsampling_default
    else:
        for i in range(max_division, min_division, -1):
            if value % i == 0:
                division_factors.append(i)
        if not division_factors:
            print(
                "Failed to find division factor in the range {}-{}. Will downsample with `{}` instead".format(
                    min_division, max_division, subsampling_default
                )
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
            "Scale cannot be '{}' as it does will prevent correct reshaping!".format(division_factor)
            + " Number of items before reshape: {} and after {}".format(data.size, np.prod(new_shape))
        )
    return np.reshape(data, new_shape).sum(axis=2), bin_mean_1D_array(xvals, new_shape)


def bin_mean_array(data, xvals, division_factor):
    """Downsample array by binning and subsequently averaging multiple signals"""
    y_dim, x_dim = data.shape
    new_shape = (y_dim, int(x_dim / division_factor), division_factor)
    if np.prod(new_shape) != data.size:
        raise ValueError(
            "Scale cannot be '{}' as it does will prevent correct reshaping!".format(division_factor)
            + " Number of items before reshape: {} and after {}".format(data.size, np.prod(new_shape))
        )
    return np.reshape(data, new_shape).mean(axis=2), bin_mean_1D_array(xvals, new_shape)


def bin_mean_1D_array(xvals, new_shape):
    xvals = np.reshape(xvals, (1, new_shape[1], new_shape[2])).mean(axis=2)
    return np.reshape(xvals, (new_shape[1],))
