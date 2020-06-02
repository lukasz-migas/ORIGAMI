# Standard library imports
import math
import logging
from bisect import bisect_left
from typing import Optional

# Third-party imports
import numpy as np
import scipy.linalg as LA
from scipy.signal import savgol_filter
from scipy.ndimage import median_filter
from scipy.ndimage import gaussian_filter
from scipy.interpolate.interpolate import interp1d

# Local imports
from origami.utils.ranges import get_min_max
from origami.processing.utils import get_narrow_data_range
from origami.utils.exceptions import MessageError

logger = logging.getLogger(__name__)


# TODO: add ppm sampling
# TODO: should try to speed this up as the for-loop makes this very computationally expensive
def baseline_curve(data, window, **kwargs):
    """Based on massign method: https://pubs.acs.org/doi/abs/10.1021/ac300056a

    We initlise an array which has the same length as the input array, subsequently smooth the spectrum  and then
    subtract the background from the spectrum

    Parameters
    ----------
    data: np.array
        intensity array
    window: int
        window integer

    Returns
    -------
    data: np.array
        data without background

    """
    if window <= 0:
        raise MessageError("Incorrect input", "Value should be above 0")

    window = abs(window)

    length = data.shape[0]
    mins = np.zeros((length), dtype=np.int32)

    for i in range(length):
        mins[i] = np.amin(data[int(max([0, i - window])) : int(min([i + window, length]))])
    background = gaussian_filter(mins, window * 2)
    return data - background


def baseline_polynomial(y, deg=None, max_it=None, tol=None, **kwargs):
    """
    Taken from: https://peakutils.readthedocs.io/en/latest/index.html
    -----------------------------------------------------------------
    Computes the baseline of a given data.

    Iteratively performs a polynomial fitting in the data to detect its
    baseline. At every iteration, the fitting weights on the regions with
    peaks are reduced to identify the baseline only.

    Parameters
    ----------
    y : ndarray
        Data to detect the baseline.
    deg : int (default: 3)
        Degree of the polynomial that will estimate the data baseline. A low
        degree may fail to detect all the baseline present, while a high
        degree may make the data too oscillatory, especially at the edges.
    max_it : int (default: 100)
        Maximum number of iterations to perform.
    tol : float (default: 1e-3)
        Tolerance to use when comparing the difference between the current
        fit coefficients and the ones from the last iteration. The iteration
        procedure will stop when the difference between them is lower than
        *tol*.

    Returns
    -------
    ndarray
        Array with the baseline amplitude for every original point in *y*
    """
    # for not repeating ourselves in `envelope`
    if deg is None:
        deg = 4
    if max_it is None:
        max_it = 100
    if tol is None:
        tol = 1e-3

    order = deg + 1
    coeffs = np.ones(order)

    # try to avoid numerical issues
    cond = math.pow(abs(y).max(), 1.0 / order)
    x = np.linspace(0.0, cond, y.size)
    base = y.copy()

    vander = np.vander(x, order)
    vander_pinv = LA.pinv2(vander)

    for _ in range(max_it):
        coeffs_new = np.dot(vander_pinv, y)

        if LA.norm(coeffs_new - coeffs) / LA.norm(coeffs) < tol:
            break

        coeffs = coeffs_new
        base = np.dot(vander, coeffs)
        y = np.minimum(y, base)

    return base


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


def baseline_linear(data, threshold=0, **kwargs):
    value_max = np.max(data)
    if threshold < 0:
        raise MessageError("Incorrect input", "Value should be above 0")

    if threshold > value_max:
        raise MessageError("Incorrect input", f"Value {threshold} is above the maximum {value_max}")

    data[data <= threshold] = 0

    return data


def baseline_median(data, median_window=5, **kwargs):
    """Median-filter"""
    if median_window % 2 == 0:
        raise MessageError("Median window must be an odd number")

    data = median_filter(data, median_window)
    return data


def baseline_tophat(data, tophat_window=100, **kwargs):
    from scipy.ndimage.morphology import white_tophat

    return white_tophat(data, tophat_window)


def baseline_1D(data, mode="Linear", **kwargs):
    # ensure data is in 64-bit format
    data = np.array(data, dtype=np.float64)
    if mode == "Linear":
        data = baseline_linear(data, **kwargs)
    elif mode == "Polynomial":
        baseline = baseline_polynomial(data, **kwargs)
        data = data - baseline
    elif mode == "Median":
        data = baseline_median(data, **kwargs)
    elif mode == "Curved":
        data = baseline_curve(data, **kwargs)
    elif mode == "Top Hat":
        data = baseline_tophat(data, **kwargs)

    data[data <= 0] = 0

    return data


def normalize_1D(data, mode="Maximum"):
    # ensure data is in 64-bit format
    data = np.array(data, dtype=np.float64)

    #     if mode == 'Maximum':
    norm_data = np.divide(data, data.max())

    #     elif mode == 'Total Ion Current (TIC)':
    #         norm_data = np.divide(data, np.sum(data))
    # #         norm_data = np.divide(norm_data, norm_data.max())
    #     elif mode == 'Highest peak':
    #         norm_data = np.divide(data, data[data.argmax()])
    # #         norm_data = np.divide(norm_data, norm_data.max())
    #     elif mode == 'Root Mean Square (RMS)':
    #         norm_data = np.divide(data, np.sqrt(np.mean(data ** 2)))
    # #         norm_data = np.divide(norm_data, norm_data.max())
    #     elif mode == 'Log':
    #         norm_data = np.divide(data, np.sum(np.log(data[np.nonzero(data)])))
    # #         norm_data = np.divide(norm_data, norm_data.max())
    #     elif mode == 'Square root':
    #         norm_data = np.divide(data, np.sum(np.sqrt(data)))
    # #         norm_data = np.divide(norm_data, norm_data.max())

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
            mz_min.append(ms_dict[key]["xvals"][0])
            mz_max.append(ms_dict[key]["xvals"][-1])

    if ms_list is not None:
        for i in range(len(ms_list)):
            mz_min.append(ms_dict[i]["xvals"][0])
            mz_max.append(ms_dict[i]["xvals"][-1])

    # determine min and maximum value from the list
    return np.min(mz_min), np.max(mz_max)


def interpolate(x_short, y_short, x_long):

    fcn = interp1d(x_short, y_short, fill_value=0, bounds_error=False)
    new_y_long = fcn(x_long)
    return x_long, new_y_long


def linearize_data(
    x: np.ndarray,
    y: np.ndarray,
    bin_size: Optional[float] = None,
    linearization_mode: Optional[str] = None,
    auto_range: bool = True,
    x_min: Optional[float] = None,
    x_max: Optional[float] = None,
    x_bin: Optional[np.ndarray] = None,
    **kwargs,
):
    """Linearize data by either up- or down-sampling"""

    # get the x axis minimum/maximum values
    if auto_range or x_min is None or x_max is None:
        x_min = math.ceil(x[0] / bin_size) * bin_size
        x_max = math.floor(x[-1] / bin_size) * bin_size
    if x_bin is None:
        x_bin = get_linearization_range(x_min, x_max, bin_size, linearization_mode)

    x_bin, y_bin = linearize(data=np.transpose([x, y]), bin_size=bin_size, mode=linearization_mode, x_bin=x_bin)
    y_bin = np.nan_to_num(y_bin)

    return x_bin, y_bin


def crop_1D_data(msX, msY, **kwargs):
    """
    msX : list
        x-axis list
    msY : list
        y-axis list
    """

    crop_min, crop_max = kwargs["min"], kwargs["max"]

    # get data min, max
    data_min, data_max = get_min_max(msX)

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
    spectrum = get_narrow_data_range(spectrum, mzRange=(crop_min, crop_max))

    return spectrum[:, 0], spectrum[:, 1]


def sum_1D(data):
    """
    @param data (dict): dictionary with mass spectra [keys: xvals, yvals]
    """
    # Retrieve MS data
    ydata = []
    # Iterate over the whole dictionary to retrieve y-axis data
    for idx in range(len(data)):
        ydata.append(data[idx]["yvals"])
    # Sum y-axis data
    msY = np.sum(ydata, axis=0)

    return msY


def sum_1D_dictionary(ydict=None):
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


def smooth_gaussian_1D(data=None, sigma=1, **kwargs):
    """Smooth using Gaussian filter"""
    if sigma < 0:
        raise MessageError("Incorrest value of `sigma`", "Value of `sigma` is too low. Value must be larger than 0")

    dataOut = gaussian_filter(data, sigma=sigma, order=0)
    return dataOut


def smooth_moving_average_1D(x, **kwargs):
    """Smooth using moving average"""
    # get parameters
    N = kwargs.pop("N")
    if N <= 0:
        raise MessageError(
            "Incorrest value of `window size`", "Value of `window size` is too low. Value must be larger than 0"
        )

    return np.convolve(x, np.ones((N,)) / N, mode="same")


def smooth_sav_gol_1D(data, **kwargs):
    """Smooth using Savitzky-Golay filter"""
    # get parameters
    polyOrder = kwargs.pop("polyOrder")
    windowSize = kwargs.pop("windowSize")
    try:
        dataOut = savgol_filter(data, polyorder=polyOrder, window_length=windowSize, axis=0)
    except (ValueError, TypeError, MemoryError) as err:
        logger.error(err)
        return data

    return dataOut


def smooth_1D(data=None, mode="Gaussian", **kwargs):
    """Smooth data"""

    if mode == "Gaussian":
        data = smooth_gaussian_1D(data, **kwargs)
    elif mode == "Savitzky-Golay":
        data = smooth_sav_gol_1D(data, **kwargs)
    elif mode == "Moving average":
        data = smooth_moving_average_1D(data, **kwargs)

    # remove values below zero
    data[data < 0] = 0

    return data


def sum_spectrum_to_chromatogram(ydict=None):
    """ sum data in direction to obtain retention times plot """
    rtX, rtY = [], []
    for key in ydict:
        rtX.append(key)
        rtY.append(np.sum(ydict[key][1]))

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


def get_linearization_range(x_min: float, x_max: float, bin_size: float, mode: str):
    """Calculate the x-axis range based on the provided min/max values

    Parameters
    ----------
    x_min : float
        minimum value of x-axis
    x_max : float
        maximum value of the x-axis
    bin_size : float
        spacing between points in the x-axis
    mode : str
        type of linearization to be performed on the data
    """
    if mode in ["Linear m/z", "Linear interpolation"]:
        x = np.arange(x_min, x_max, bin_size)
    else:
        x = nonlinear_axis(x_min, x_max, x_min / bin_size)

    return x


def linearize(data, bin_size, mode, x_bin=None):
    if x_bin is None:
        x_bin = []

    if len(x_bin) == 0:
        # length = len(data)
        # firstpoint = math.ceil(data[0, 0] / bin_size) * bin_size
        # lastpoint = math.floor(data[length - 1, 0] / bin_size) * bin_size

        x_bin = get_linearization_range(data[0, 0], data[-1, 0], bin_size, mode)

    # perform linearization
    if mode in ["Linear m/z", "Linear resolution"]:
        xy = lintegrate(data, x_bin)
    else:
        xy = linterpolate(data, x_bin)

    # unpact to x and y list
    x = xy[:, 0]
    y = xy[:, 1]

    return x, y


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

    Parameters
    ----------
    x1 : np.array
    x2 : np.array
    x: : np.array

    Returns
    -------
    float(x - x1) / float(x2 - x1)
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
    length_x = len(intx)
    for i in range(0, length):
        if intx[0] < data[i, 0] < intx[length_x - 1]:
            index = nearest(intx, data[i, 0])
            if intx[index] == data[i, 0]:
                inty[index] += data[i, 1]
            if intx[index] < data[i, 0]:  # and index < length - 1:
                index2 = index + 1
                interpos = linear_interpolation(intx[index], intx[index2], data[i, 0])
                inty[index] += (1 - interpos) * data[i, 1]
                inty[index2] += interpos * data[i, 1]
            if intx[index] > data[i, 0]:  # and index > 0:
                index2 = index - 1
                interpos = linear_interpolation(intx[index], intx[index2], data[i, 0])
                inty[index] += (1 - interpos) * data[i, 1]
                inty[index2] += interpos * data[i, 1]
    return np.column_stack((intx, inty))


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
        return np.array(
            [np.mean(data[index : index + num_compressed], axis=0) for index in range(0, len(data), num_compressed)]
        )


def subtract_spectra(xvals_1, yvals_1, xvals_2, yvals_2, **kwargs):
    n_size_1 = len(xvals_1)
    n_size_2 = len(xvals_2)

    if n_size_1 != n_size_2:
        logger.warning(f"The two spectra are of different size. They will be interpolated to the same scale.")
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
            "auto_range": False,
            "x_min": ylimits[0],
            "x_max": ylimits[1],
            "bin_size": mz_bin,
            "linearization_mode": "Linear interpolation",
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


def seq_ppm(mz_start: float, mz_end: float, ppm: float):
    """Compute sequence of m/z values at a particular ppm"""
    length = (np.log(mz_end) - np.log(mz_start)) / np.log((1 + 1e-6 * ppm) / (1 - 1e-6 * ppm))
    length = math.floor(length) + 1
    mz = mz_start * np.power(((1 + 1e-6 * ppm) / (1 - 1e-6 * ppm)), (np.arange(length) - 1))
    return mz
