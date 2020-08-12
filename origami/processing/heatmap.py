# Standard library imports
import logging
from typing import Union

# Third-party imports
import numpy as np
from scipy.signal import savgol_filter
from scipy.ndimage import gaussian_filter
from sklearn.preprocessing import normalize

# Local imports
from origami.utils.check import is_prime
from origami.utils.check import check_value_order
from origami.utils.utilities import find_nearest_divisible
from origami.processing.utils import nthroot
from origami.processing.utils import find_nearest_index
from origami.utils.exceptions import MessageError

logger = logging.getLogger(__name__)


def adjust_min_max_intensity(array, min_threshold=0.0, max_threshold=1.0):

    # Check min_threshold is larger than max_threshold
    if min_threshold > max_threshold:
        print("Minimum threshold is larger than the maximum. Values were reversed.")
        min_threshold, max_threshold = max_threshold, min_threshold

    # Check if they are the same
    if min_threshold == max_threshold:
        print("Minimum and maximum thresholds are the same.")
        return array

    # Find maximum value in the array
    data_max = np.max(array)
    min_threshold = min_threshold * data_max
    max_threshold = max_threshold * data_max

    # Adjust minimum threshold
    array[array <= min_threshold] = 0

    # Adjust maximum threshold
    array[array >= max_threshold] = data_max

    return array


def remove_noise_2d(array, threshold: Union[int, float] = 0):
    """Remove noise from the array"""
    data_max = np.max(array)
    if threshold > data_max:
        logger.warning(f"Threshold value {threshold} is larger than the maximum value in the data {data_max}")

    array[array <= threshold] = 0
    return array


def crop_2d(
    x: np.ndarray,
    y: np.ndarray,
    array: np.ndarray,
    x_min: Union[int, float],
    x_max: Union[int, float],
    y_min: Union[int, float],
    y_max: Union[int, float],
):
    """Crop array"""
    # ensure order of values is correct
    x_min, x_max = check_value_order(x_min, x_max)
    y_min, y_max = check_value_order(y_min, y_max)

    # check if values are not the same
    crop_x = True
    if x_min == x_max:
        crop_x = False
    crop_y = True
    if y_min == y_max:
        crop_y = False

    # find nearest index
    xmin_idx = find_nearest_index(x, x_min)
    xmax_idx = find_nearest_index(x, x_max)
    ymin_idx = find_nearest_index(y, y_min)
    ymax_idx = find_nearest_index(y, y_max)

    if crop_x:
        x = x[xmin_idx : xmax_idx + 1]
        array = array[:, xmin_idx : xmax_idx + 1]

    if crop_y:
        y = y[ymin_idx : ymax_idx + 1]
        array = array[ymin_idx : ymax_idx + 1]

    return x, y, array


def smooth_2d(array: np.ndarray, method: str = "Gaussian", sigma: int = 1, poly_order: int = 1, window_size: int = 3):
    """Smooth array"""

    if method == "Savitzky-Golay":
        array = smooth_savgol_2d(array, poly_order=poly_order, window_size=window_size)
    elif method == "Gaussian":
        array = smooth_gaussian_2d(array, sigma=sigma)

    # remove values below 0
    array[array < 0] = 0

    return array


def smooth_gaussian_2d(data, sigma: int):
    """Smooth array using the gaussian filter"""
    if sigma < 0:
        raise MessageError("Incorrect value of `sigma`", "Value of `sigma` must be larger than 0")

    array_out = gaussian_filter(data, sigma=sigma, order=0)

    return array_out


def smooth_savgol_2d(array, poly_order: int, window_size: int):
    """Smooth the array using savitzky-golay filter"""
    array_out = savgol_filter(array, polyorder=poly_order, window_length=window_size, axis=0)

    return array_out


def normalize_2d(data, method="Maximum", p_norm: int = 1):
    """Normalize heatmap

    Parameters
    ----------
    data : np.array
        input array
    method : {'Maximum', 'Logarithmic', 'Natural log', 'Square root', 'Least Abs Deviation', 'Least Squares'}, optional
        normalization mode
    p_norm : int, optional

    Returns
    -------
    norm_data : np.array
        normalized array
    """
    # replace NaNs with 0s
    data = np.nan_to_num(data)
    data = data.astype(np.float64)

    # normalize data
    if method == "None":
        return data

    if method == "Maximum":
        norm_data = normalize(data, axis=0, norm="max")
    elif method == "Logarithmic":
        norm_data = np.log10(data)
    elif method == "Natural log":
        norm_data = np.log(data)
    elif method == "Square root":
        norm_data = np.sqrt(data)
    elif method == "Least Abs Deviation":
        norm_data = normalize(data, axis=0, norm="l1")
    elif method == "Least Squares":
        norm_data = normalize(data, axis=0, norm="l2")
    elif method == "Median":
        median = np.median(data[data > 0])
        norm_data = data / median
    elif method == "p-Norm":
        div = nthroot(np.sum(data ** p_norm), p_norm)
        norm_data = data / div
    elif method == "Total Intensity":
        div = np.sum(data)
        norm_data = data / div
    elif method == "Root Mean Square":
        div = np.square(np.mean(np.power(data, 2)))
        norm_data = data / div
    elif method == "L2":
        div = np.square(np.sum(np.power(data, 2)))
        norm_data = data / div
    else:
        raise ValueError(f"Could not normalized with the mode=`{method}`")
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

    return interpolate_2d(xvals, yvals, zvals, new_x=new_xvals, new_y=new_yvals)


def interpolate_2d(
    x,
    y,
    array,
    fold=1,
    method="linear",
    x_axis: bool = False,
    new_x: np.ndarray = None,
    y_axis: bool = False,
    new_y: np.ndarray = None,
):
    """Interpolate along given axis

    Parameters
    ----------
    x : np.ndarray
        current x-axis of the array
    y : np.ndarray
        current y-axis of the array
    array : np.ndarray
        current array
    fold: float
        by how much data should be interpolated. Must be larger than 0
    method : {'linear', 'cubic', 'quintic'}, optional
        method used during the interpolation
    x_axis : bool
        flag to interpolate in the x-axis
    new_x : np.ndarray
        new x-axis array
    y_axis : bool
        flag to interpolate in the y-axis
    new_y : np.ndarray
        new y-axis array

    Returns
    -------
    new_x : np.array
    new_y : np.array
    new_array : np.array
    """
    from scipy.interpolate.interpolate import interp2d

    method = method.lower()

    if fold <= 0:
        raise MessageError("Incorrect value of `fold`", "The value of `fold` must be larger than 0")

    new_x = x
    if x_axis:
        new_x = calculate_interpolation_axes(x, fold)

    new_y = y
    if y_axis:
        new_y = calculate_interpolation_axes(y, fold)

    if not isinstance(new_x, np.ndarray) or not isinstance(new_y, np.ndarray):
        raise ValueError("Could not determine new x/y-axis")

    fcn = interp2d(x, y, array, kind=method)
    new_array = fcn(new_x, new_y)

    return new_x, new_y, new_array


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


def bin_sum_array(array, x, scale):
    """Downsample array by binning and subsequently summing multiple signals"""
    y_dim, x_dim = array.shape
    new_shape = (y_dim, int(x_dim / scale), scale)
    if np.prod(new_shape) != array.size:
        raise ValueError(
            "Scale cannot be '{}' as it does will prevent correct reshaping!".format(scale)
            + " Number of items before reshape: {} and after {}".format(array.size, np.prod(new_shape))
        )
    return np.reshape(array, new_shape).sum(axis=2), bin_mean_1d_array(x, new_shape)


def bin_mean_array(array, x, scale):
    """Downsample array by binning and subsequently averaging multiple signals"""
    y_dim, x_dim = array.shape
    new_shape = (y_dim, int(x_dim / scale), scale)
    if np.prod(new_shape) != array.size:
        raise ValueError(
            "Scale cannot be '{}' as it does will prevent correct reshaping!".format(scale)
            + " Number of items before reshape: {} and after {}".format(array.size, np.prod(new_shape))
        )
    return np.reshape(array, new_shape).mean(axis=2), bin_mean_1d_array(x, new_shape)


def bin_mean_1d_array(x, new_shape):
    """Bin 1d array in such a manner as to generate alternative spacing that matches another dimension"""
    x = np.reshape(x, (1, new_shape[1], new_shape[2])).mean(axis=2)
    return np.reshape(x, (new_shape[1],))


def pyramid_sum(array: np.ndarray, x: np.ndarray, n_scales: int):
    """Generate pyramid-like scheme for a large array along one dimension"""
    if not isinstance(n_scales, int) or n_scales <= 1:
        raise ValueError("Number of scales must be an integer larger than 1")
    scales = [2 ** n for n in range(n_scales)]
    for scale in scales:
        _array, _x = bin_sum_array(array, x, scale)
        yield _array, _x, scale


def pyramid_mean(array: np.ndarray, x: np.ndarray, n_scales: int):
    """Generate pyramid-like scheme for a large array along one dimension"""
    if not isinstance(n_scales, int) or n_scales <= 1:
        raise ValueError("Number of scales must be an integer larger than 1")
    scales = [2 ** n for n in range(n_scales)]
    for scale in scales:
        _array, _x = bin_mean_array(array, x, scale)
        yield _array, _x, scale


def view_as_blocks(array, n_rows: int = 200, n_cols: int = 1000):
    """Return an array of shape (n, n_rows, n_cols) where n * n_rows * n_cols = array.size

    If array is a 2D array, the returned array should look like n sub-blocks with
    each sub-block preserving the "physical" layout of array.

    Parameters
    ----------
    array : np.ndarray
        input array
    n_rows : int
        number of rows in each sub-block
    n_cols : int
        number of columns in each sub-block

    References
    ----------
    Inspired by a StackOverflow post [1]
    [1] https://stackoverflow.com/questions/16856788/slice-2d-array-into-smaller-2d-arrays
    """
    h, w = array.shape
    # if the shape is incorrect, pad the array with NaNs at the outer edges
    if h % n_rows != 0 or w % n_cols != 0:
        new_height = find_nearest_divisible(h, n_rows)
        new_width = find_nearest_divisible(w, n_cols)
        _array = array
        array = np.full((new_height, new_width), fill_value=np.nan)
        array[:h, :w] = _array
        h, w = array.shape

    new_shape = (int(h / n_rows), int(w / n_cols))
    return array.reshape((h // n_rows, n_rows, -1, n_cols)).swapaxes(1, 2).reshape(-1, n_rows, n_cols), new_shape
