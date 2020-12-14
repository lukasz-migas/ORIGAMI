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
from origami.processing.utils import find_nearest_index

logger = logging.getLogger(__name__)


# TODO: add ppm sampling
# TODO: should try to speed this up as the for-loop makes this very computationally expensive
def baseline_curve(data, window: int, **kwargs):
    """Based on massign method: https://pubs.acs.org/doi/abs/10.1021/ac300056a

    We initialise an array which has the same length as the input array, subsequently smooth the spectrum  and then
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
    window = abs(window)
    if window <= 0:
        from origami.utils.exceptions import MessageError

        raise MessageError("Incorrect input", "Value should be above 0")

    return baseline_curve_(data, window)


def baseline_curve_(data, window: int):
    length = data.shape[0]
    mins = np.zeros(length, dtype=np.int32)
    for i in range(length):
        mins[i] = np.amin(data[int(max([0, i - window])) : int(min([i + window, length]))])
    background = gaussian_filter(mins, window * 2)
    return data - background


def baseline_polynomial(y: np.ndarray, deg: int = 4, max_iter: int = 100, tol: float = 1e-3, **kwargs):
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
    max_iter : int (default: 100)
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
    if max_iter is None:
        max_iter = 100
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

    for _ in range(max_iter):
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
    z = np.zeros_like(w)
    while niter > 0:
        W = sparse.spdiags(w, 0, L, L)
        Z = W + lam * D.dot(D.transpose())
        z = spsolve(Z, w * y)
        w = p * (y > z) + (1 - p) * (y < z)
        niter -= 1
    return z


def baseline_linear(data, threshold: float, **kwargs):
    """Subtract baseline using linear method"""
    if not isinstance(threshold, (int, float)):
        raise TypeError("Threshold must be a number")
    if threshold < 0:
        raise ValueError("Value should be above 0")

    data[data <= threshold] = 0

    return data


def baseline_median(data, median_window: int = 5, **kwargs):
    """Median-filter"""
    if median_window % 2 == 0:
        from origami.utils.exceptions import MessageError

        raise MessageError("Incorrect input", "Median window must be an odd number")

    data = median_filter(data, median_window)
    return data


def baseline_tophat(data, tophat_window=100, **kwargs):
    """Top-hat filter"""
    from scipy.ndimage.morphology import white_tophat

    return white_tophat(data, tophat_window)


def baseline_1d(
    y,
    baseline_method: str = "Linear",
    threshold: Optional[float] = None,
    poly_order: Optional[int] = 4,
    max_iter: Optional[int] = 100,
    tol: Optional[float] = 1e-3,
    median_window: Optional[int] = 5,
    curved_window: Optional[int] = None,
    tophat_window: Optional[int] = 100,
    **kwargs,
):
    """Subtract baseline from the y-axis intensity array

    Parameters
    ----------
    y : ndarray
        Data to detect the baseline.
    baseline_method : str
        baseline removal method
    threshold : float
        any value below `threshold` will be set to 0
    poly_order : int
        Degree of the polynomial that will estimate the data baseline. A low degree may fail to detect all the
        baseline present, while a high degree may make the data too oscillatory, especially at the edges; only used
        with method being `Polynomial`
    max_iter : int
        Maximum number of iterations to perform; only used with method being `Polynomial`
    tol : float
        Tolerance to use when comparing the difference between the current fit coefficients and the ones from the
        last iteration. The iteration procedure will stop when the difference between them is lower than *tol*.; only
        used with method being `Polynomial`
    median_window : int
        median filter size - should be an odd number; only used with method being `Median`
    curved_window : int
        curved window size; only used with method being `Curved`
    tophat_window : int
        tophat window size; only used with method being `Top Hat`

    Returns
    -------
    y : np.ndarray
        y-axis intensity array with baseline removed
    """
    # ensure data is in 64-bit format
    y = np.array(y, dtype=np.float64)
    if baseline_method == "Linear":
        y = baseline_linear(y, threshold=threshold)
    elif baseline_method == "Polynomial":
        baseline = baseline_polynomial(y, deg=poly_order, max_iter=max_iter, tol=tol)
        y = y - baseline
    elif baseline_method == "Median":
        y = baseline_median(y, median_window=median_window)
    elif baseline_method == "Curved":
        y = baseline_curve(y, curved_window)
    elif baseline_method == "Top Hat":
        y = baseline_tophat(y, tophat_window)

    y[y <= 0] = 0

    return y


def normalize_1d(y):
    """Normalize 1d array"""
    # ensure data is in 64-bit format
    y = np.array(y, dtype=np.float64)
    norm_data = np.divide(y, np.max(y))

    # replace nans
    norm_data = np.nan_to_num(norm_data)
    return norm_data


def interpolate(x_short, y_short, x_long):
    """Linear interpolate ywo arrays so they have the same length"""
    fcn = interp1d(x_short, y_short, fill_value=0, bounds_error=False)
    new_y_long = fcn(x_long)
    return x_long, new_y_long


def linearize_data(
    x: np.ndarray,
    y: np.ndarray,
    linearize_method: Optional[str] = None,
    bin_size: Optional[float] = None,
    auto_range: bool = True,
    x_min: Optional[float] = None,
    x_max: Optional[float] = None,
    ppm: Optional[float] = None,
    x_bin: Optional[np.ndarray] = None,
    **kwargs,
):
    """Linearize data by either up- or down-sampling

    Parameters
    ----------
    x : np.ndarray
        x-axis values
    y : np.ndarray
        y-axis intensity values
    linearize_method : str
        name of the linearization method
    bin_size : float
        size of the bin between adjacent values in the x-axis
    auto_range : bool
        if `True`, the x-axis range will be decided automatically
    x_min : floats
        starting value of the linearization method
    x_max : float
        ending value of the linearization method
    ppm : float
        parts-per million at which the spectrum should be resampled
    x_bin : np.ndarray
        pre-computed x-axis values

    Returns
    -------
    x_bin : np.ndarray
        sub-sampled x-axis values
    y_bin : np.ndarray
        sub-sampled y-axis intensity values
    """

    # get the x axis minimum/maximum values
    if auto_range or x_min is None or x_max is None:
        x_min = math.ceil(x[0] / bin_size) * bin_size
        x_max = math.floor(x[-1] / bin_size) * bin_size

    x_bin, y_bin = linearize(data=np.transpose([x, y]), bin_size=bin_size, mode=linearize_method, ppm=ppm, x_bin=x_bin)
    y_bin = np.nan_to_num(y_bin)

    return x_bin, y_bin


def crop_1d_data(x, y, crop_min: Optional[float] = None, crop_max: Optional[float] = None):
    """Crop signal to defined x-axis region

    Parameters
    ----------
    x : np.ndarray
        x-axis values
    y : np.ndarray
        y-axis intensity values
    crop_min : float, optional
        minimum value in the x-axis array to be retained
    crop_max : float, optional
        maximum value in the x-axis array to be retained

    Returns
    -------
    x : np.ndarray
        cropped x-axis array
    y : np.ndarray
        cropped y-axis array
    """
    # get data min, max
    data_min, data_max = get_min_max(x)
    if crop_min is None or crop_min < data_min:
        crop_min = data_min

    if crop_max is None or crop_max > data_max:
        crop_max = data_max

    if crop_min == crop_max or (crop_min == data_min and crop_max == data_max):
        return x, y

    min_idx, max_idx = find_nearest_index(x, [crop_min, crop_max])

    return x[min_idx : max_idx + 1], y[min_idx : max_idx + 1]


def smooth_gaussian_1d(y, sigma: float, **kwargs):
    """Smooth using Gaussian filter"""
    if sigma < 0:
        from origami.utils.exceptions import MessageError

        raise MessageError("Incorrest value of `sigma`", "Value of `sigma` is too low. Value must be larger than 0")

    _y = gaussian_filter(y, sigma=sigma)
    return _y


def smooth_moving_average_1d(y, N: int, **kwargs):
    """Smooth using moving average"""
    # get parameters
    if N <= 0:
        from origami.utils.exceptions import MessageError

        raise MessageError(
            "Incorrect value of `window size`", "Value of `window size` is too low. Value must be larger than 0"
        )

    return np.convolve(y, np.ones((N,)) / N, mode="same")


def smooth_sav_gol_1d(y, poly_order: int, window_size: int, **kwargs):
    """Smooth using Savitzky-Golay filter"""
    # get parameters
    try:
        y = savgol_filter(y, polyorder=poly_order, window_length=window_size, axis=0)
    except (ValueError, TypeError, MemoryError) as err:
        logger.error(err)
        return y

    return y


def smooth_1d(
    y,
    smooth_method: Optional[str] = "Gaussian",
    sigma: Optional[float] = None,
    poly_order: Optional[int] = None,
    window_size: Optional[int] = None,
    N: Optional[int] = None,
    **kwargs,
):
    """Smooth spectral data using one of few filters

    Parameters
    ----------
    y : np.ndarray
        y-axis intensity values
    smooth_method : str
        name of the smoothing method
    sigma: float
        gaussian sigma value; only used with method being `Gaussian`
    poly_order : int
        polynomial value; only used with method being `Savitzky-Golay`
    window_size : int
        window size; only used with method being `Savitzky-Golay`
    N : int
        size of the window in moving average; only used with method being `Moving average`

    Returns
    -------
    y : np.ndarray
        smoothed signal

    """

    if smooth_method == "Gaussian":
        y = smooth_gaussian_1d(y, sigma=sigma)
    elif smooth_method == "Savitzky-Golay":
        y = smooth_sav_gol_1d(y, poly_order=poly_order, window_size=window_size)
    elif smooth_method == "Moving average":
        y = smooth_moving_average_1d(y, N=N)

    # remove values below zero
    y[y < 0] = 0

    return y


def abline(y, slope: float, intercept: float):
    """
    Calculate xy coords for a line from slope and intercept
    x_vals: tuple of (xmin, xmax) : float
    slope: slope : float
    intercept: float
    """
    y_ = intercept + slope * y
    return y, y_


def nearest(array, target):
    """
    In an sorted array, quickly find the position of the element closest to the target.

    Parameters
    ----------
    array: np.ndarray
        input array
    target: Any
        searched value

    Returns
    -------
    index : int
        np.argmin(np.abs(array - target))
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


def linearize(data: np.ndarray, bin_size: float, mode: str, ppm: float, x_bin=None):
    """Linearize the array"""
    if x_bin is None:
        x_bin = []

    if mode == "Parts-per-million":
        x = seq_ppm(data[0, 0], data[-1, 0], ppm)
        y = linearize_ppm(data[:, 0], data[:, 1], x)
        return x, y

    if len(x_bin) == 0:
        x_bin = get_linearization_range(data[0, 0], data[-1, 0], bin_size, mode)

    # perform linearization
    if mode in ["Linear m/z", "Linear resolution"]:
        xy = lin_integrate2(data[:, 0], data[:, 1], x_bin)
    #         xy = lin_integrate(data, x_bin)
    else:
        xy = lin_interpolate(data, x_bin)

    # unpack to x and y list
    x = xy[:, 0]
    y = xy[:, 1]

    return x, y


def nonlinear_axis(start: float, end: float, res: float):
    """
    Creates a nonlinear axis with the m/z values spaced with a defined and constant resolution.

    Parameters
    ----------
    start : float
        minimum m/z value
    end : float
        maximum m/z value
    res : float
        resolution of the axis (m / delta m)

    Returns
    -------
    x : np.ndarray
        1d array of non-linear axis
    """
    res = float(res)
    i = start
    i += i / res
    axis = [start]
    while i < end:
        axis.append(i)
        i += i / res
    return np.array(axis)


def linear_interpolation(x1, x2, x):
    """Linear interpolation

    Parameters
    ----------
    x1 : float
    x2 : float
    x: : float

    Returns
    -------
    float(x - x1) / float(x2 - x1)
    """
    return float(x - x1) / float(x2 - x1)


def lin_integrate(data: np.ndarray, new_x: np.ndarray):
    """
    Linearize x-axis by integration.

    Each intensity value in the old data gets proportionally added into the new x-axis.
    The total sum of the intensity values should be constant.

    Parameters
    ----------
    data: np.ndarray
        input array of shape [N, 2]
    new_x : np.ndarray
        new x-axis

    Returns
    -------
    new_xy : np.ndarray
        output array of new shape [n, 2]
    """
    length = len(data)
    inty = np.zeros_like(new_x)
    length_x = len(new_x)
    for i in range(0, length):
        if new_x[0] < data[i, 0] < new_x[length_x - 1]:
            index = find_nearest_index(new_x, data[i, 0])
            if new_x[index] == data[i, 0]:
                inty[index] += data[i, 1]
            if new_x[index] < data[i, 0]:  # and index < length - 1:
                index2 = index + 1
                interpos = linear_interpolation(new_x[index], new_x[index2], data[i, 0])
                inty[index] += (1 - interpos) * data[i, 1]
                inty[index2] += interpos * data[i, 1]
            if new_x[index] > data[i, 0]:  # and index > 0:
                index2 = index - 1
                interpos = linear_interpolation(new_x[index], new_x[index2], data[i, 0])
                inty[index] += (1 - interpos) * data[i, 1]
                inty[index2] += interpos * data[i, 1]
    return np.column_stack((new_x, inty))


def lin_integrate2(x: np.ndarray, y: np.ndarray, new_x: np.ndarray):
    length = len(x)
    length_x = len(new_x)
    new_y = np.zeros_like(new_x)
    for i in range(0, length):
        if new_x[0] < x[i] < new_x[length_x - 1]:
            index = nearest(new_x, x[i])
            if new_x[index] == x[i]:
                new_y[index] += y[i]
            if new_x[index] < x[i]:
                index2 = index + 1
                interpos = linear_interpolation(new_x[index], new_x[index2], x[i])
                new_y[index] += (1 - interpos) * y[i]
                new_y[index2] += interpos * y[i]
            if new_x[index] > x[i]:
                index2 = index - 1
                interpos = linear_interpolation(new_x[index], new_x[index2], x[i])
                new_y[index] += (1 - interpos) * y[i]
                new_y[index2] += interpos * y[i]
    return np.column_stack((new_x, new_y))


def lin_interpolate(data: np.ndarray, new_x: np.ndarray):
    """Linearize x-axis by interpolation.

    The new x-axis is interpolated on the old data and the corresponding intensities and picked out.

    Parameters
    ----------
    data: np.ndarray
        input array of shape [N, 2]
    new_x : np.ndarray
        new x-axis

    Returns
    -------
    new_xy : np.ndarray
        output array of new shape [n, 2]
    """
    f = interp1d(data[:, 0], data[:, 1], fill_value=0, bounds_error=False)
    new_y = f(new_x)
    return np.column_stack((new_x, new_y))


def non_linearize(data, num_compressed):
    """Compress the data in a simple and nonlinear way.

    Parameters
    ----------
    data: np.ndarray
        Data array (N x 2)
    num_compressed: int
    """
    if num_compressed == 0:
        return data
    else:
        num_compressed = int(num_compressed)
        return np.array(
            [np.mean(data[index : index + num_compressed], axis=0) for index in range(0, len(data), num_compressed)]
        )


def subtract_spectra(xvals_1, yvals_1, xvals_2, yvals_2, **kwargs):  # noqa
    """Subtract spectrum from another spectrum.

    If the two spectra have different shapes, both will be linearized to ensure identical size

    Returns
    -------
    x_1 : np.ndarray
        x-axis of the first spectrum
    y_1 : np.ndarray
        y-axis of the first spectrum
    x_2 : np.ndarray
        x-axis of the second spectrum
    y_2 : np.ndarray
        y-axis of the second spectrum
    """
    n_size_1 = len(xvals_1)
    n_size_2 = len(xvals_2)

    if n_size_1 != n_size_2:
        logger.warning("The two spectra are of different size. They will be interpolated to the same scale.")
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


def trim_ppm(x: np.ndarray, y: np.ndarray, x_ppm: np.ndarray):
    """Trim arrays based on user settings"""
    x_idx = np.where((x > x_ppm[0]) & (x < x_ppm[-1]))
    return x[x_idx], y[x_idx]


def linearize_ppm(x: np.ndarray, y: np.ndarray, x_ppm: np.ndarray):
    """Linearize spectrum based on ppm"""
    x, y = trim_ppm(x, y, x_ppm)
    y_ppm = np.zeros_like(x_ppm)
    idx = np.digitize(x, x_ppm, True)
    for i, _idx in enumerate(idx):
        try:
            y_ppm[_idx] += y[i]
        except IndexError:
            pass
    return y_ppm


try:
    has_c = True
    _baseline_curve_ = baseline_curve_
    _nonlinear_axis = nonlinear_axis
    _linear_interpolation = linear_interpolation
    from origami.c.spectra import baseline_curve_
    from origami.c.spectra import nonlinear_axis
    from origami.c.spectra import linear_interpolation
except ImportError as e:
    print(e)
    has_c = False
