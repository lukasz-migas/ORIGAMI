# Third-party imports
import numpy as np
from scipy.stats import linregress
from scipy.signal import peak_widths

# Local imports
from origami.utils.utilities import rescale


def compute_asymmetricity_and_tailing(y, peak_idx):
    """Calculates the peak asymmetricity and tailing factor

    This algorithm is often used in LC and GC-MS where peaks often adopt Gaussian-like shapes. The algorithm simply
    calculates the distance between the center of the peak (apex) and the left/right sides calculated at 5 and 10 %
    heights.

    Parameters
    ----------
    y : np.ndarray
        intensity array
    peak_idx : np.ndarray
        center (apex) of each peak

    Returns
    -------
    afs : np.ndarray
        asymmetricity of each peak, scored between 0-100 where 100 means the peak is perfectly symmetrical, whereas
        anything below indicates some level of asymmetricity. Typically values will be scored between < 1, 1 and > 1
        indicating whether peaks are tailing or fronting, but that is not useful in our case
    tfs: np.ndarray
        tailing/fronting of each peak, scored between 0-100 where 100 means the peak is perfectly Gaussian-like and
        anything below indicates some level of fronting or tailing.
    """
    _, _, a_5, b_5 = peak_widths(y, peak_idx, rel_height=0.05)
    _, _, a_10, b_10 = peak_widths(y, peak_idx, rel_height=0.1)

    # calculate asymmetricity factor
    a = np.abs(peak_idx - a_10)
    b = np.abs(peak_idx - b_10)
    afs = b / a
    afs = np.nan_to_num(afs, nan=float(np.nanmin(afs)))

    # calculate tailing factor
    a = np.abs(peak_idx - a_5)
    b = np.abs(peak_idx - b_5)
    tfs = (a + b) / (2 * a)
    tfs = np.nan_to_num(tfs, nan=float(np.nanmin(tfs)))

    # subtract from 1 to ensure that largest value represents the most `ideal` peak
    afs = 1 - np.abs(afs)
    tfs = 1 - np.abs(tfs)

    return rescale(afs, 0, 100, dtype=np.float64), rescale(tfs, 0, 100, dtype=np.float64)


def compute_slopes(x: np.ndarray, y: np.ndarray, picker) -> np.ndarray:
    """Computes the ratio between the left and right slope of each peak

    Parameters
    ----------
    x : np.ndarray
        indices or m/z array
    y : np.ndarray
        intensity array
    picker :
        object containing `Peak`s

    Returns
    -------
    slope_ratio : np.ndarray
        ratio between the left and right slope, scored between 0-100 where 100 means the left and right slopes are the
        same of extremely similar. Low scores can indicate that peak is attached to another peak and there is some
        overlap between peaks.
    """
    left_slope, right_slope = [], []
    for peak in picker:
        left_slice = slice(peak.idx_left, peak.idx + 1)
        right_slice = slice(peak.idx, peak.idx_right + 1)
        left_slope.append(linregress(x[left_slice], y[left_slice]).slope)
        right_slope.append(linregress(x[right_slice], y[right_slice]).slope)

    slope_ratio = np.asarray(left_slope) / np.asarray(right_slope)
    slope_ratio = 1 - np.abs(slope_ratio)
    return rescale(slope_ratio, 0, 100, dtype=np.float64)
