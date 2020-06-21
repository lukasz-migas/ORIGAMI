# Third-party imports
# Standard library imports
# Standard library imports
# Standard library imports
# Standard library imports
from typing import List
from typing import Tuple
from typing import Union

import numpy as np
import peakutils
from scipy.signal import find_peaks
from scipy.signal import peak_widths


def find_peaks_in_spectrum_peak_properties(
    x,
    y,
    threshold: float = 250,
    width: int = 0,
    rel_height: float = 0.5,
    min_intensity: float = 0.0,
    distance: int = 1,
    mz_range: Union[Tuple, List] = None,
    peak_width_modifier: float = 1.0,
    prominence: int = 1,
    **kwargs,
):
    # find peaks
    pks_idx, pks_props = find_peaks(
        y, threshold=threshold, width=width, rel_height=rel_height, distance=distance, prominence=prominence
    )
    # extract peak values
    pks_x = x[pks_idx]
    pks_y = y[pks_idx]

    # adjust mass range if it was user-specified
    if mz_range is not None:
        mz_min, mz_max = mz_range
        pks_idx_mask = np.logical_and(pks_x >= mz_min, pks_x <= mz_max)
        pks_y = pks_y[pks_idx_mask]
        pks_idx = pks_idx[pks_idx_mask]
        pks_props = mask_peaks_props(pks_props, pks_idx_mask)

    # calculate minimum threshold
    try:
        pks_idx_mask = pks_y > (np.max(pks_y) * min_intensity)
    except ValueError:
        pks_idx_mask = []
    pks_idx = pks_idx[pks_idx_mask]
    pks_props = mask_peaks_props(pks_props, pks_idx_mask)

    # extract peak values
    pks_x = x[pks_idx]
    pks_y = y[pks_idx]

    # round-up peak width index
    pks_idx_width_half = np.ceil((pks_props["widths"] / 2) * peak_width_modifier).astype(np.int32)
    pks_width = np.ceil(pks_props["widths"] * peak_width_modifier).astype(np.int32)

    # collect peak widths
    pks_idx_minus_width = pks_idx - pks_idx_width_half
    pks_idx_plus_width = pks_idx + pks_idx_width_half

    # make sure index falls within the data size
    pks_idx_minus_width[pks_idx_minus_width < 0] = 0
    pks_idx_plus_width[pks_idx_plus_width > len(y) - 1] = len(y) - 1

    # get peaks
    pks_x_minus_width = x[pks_idx_minus_width]
    pks_x_plus_width = x[pks_idx_plus_width]

    found_peaks = {
        "idx": pks_idx,
        "x": pks_x,
        "y": pks_y,
        "idx_fwhm": pks_width,
        "x_left": pks_x_minus_width,
        "x_right": pks_x_plus_width,
        "idx_left": pks_idx_minus_width,
        "idx_right": pks_idx_plus_width,
    }

    return found_peaks


def find_peaks_in_spectrum_local_max(
    x,
    y,
    window: int = 10,
    min_intensity: float = 0,
    mz_range: Union[Tuple, List] = None,
    rel_height: float = 0.5,
    **kwargs,
):
    """Find peaks in a signal (e.g. mass spectrum) based on a local max search

    Parameters:
    ----------
    x : np.array
        m/z array
    y : np.ndarray
        intensity array
    window: float
        extraction window
    min_intensity: float
        minimal intensity
    mz_range: tuple
        user-defined mass range (ms start, ms end)

    Additional parameters:
    ---------------------
    verbose: bool
        will print some basic information about peak finding
    rel_height: float
        determines the relative position of the peak height that is used for peak width definition

    Returns
    -------
    found_peaks: dict
        dictionary with all peak information found for specified m/z range
    """
    pks_idx, pks_x, pks_y = find_peaks_local_max(x, y, window, min_intensity)

    if mz_range is not None:
        mz_min, mz_max = mz_range
        pks_x = np.asarray(pks_x)
        mz_start_idx = np.argmin(np.abs(pks_x - mz_min))
        mz_end_idx = np.argmin(np.abs(pks_x - mz_max))
        pks_x = pks_x[mz_start_idx:mz_end_idx]
        pks_y = np.asarray(pks_y)[mz_start_idx:mz_end_idx]
        pks_idx = np.asarray(pks_idx)[mz_start_idx:mz_end_idx]

    n_peaks = len(pks_idx)
    if n_peaks == 0:
        return dict(peaks_index=[])

    pks_width, widths_height, left_ips, right_ips = peak_widths(y, pks_idx, rel_height=rel_height)

    # round-up peak width index
    pks_idx_width_half = np.ceil(pks_width / 2).astype(np.int32)
    # pks_idx_width = np.ceil(pks_width).astype(np.int32)

    # collect peak widths
    pks_idx_minus_width = pks_idx - pks_idx_width_half
    pks_idx_plus_width = pks_idx + pks_idx_width_half

    # get peaks
    pks_mz_x_minus_width = x[pks_idx_minus_width]
    pks_mz_x_plus_width = x[pks_idx_plus_width]
    # pks_mz_x_width = pks_mz_x_plus_width - pks_mz_x_minus_width

    return {
        "x": pks_x,
        "y": pks_y,
        "x_left": pks_mz_x_minus_width,
        "x_right": pks_mz_x_plus_width,
        "idx": pks_idx,
        "idx_left": pks_idx_minus_width,
        "idx_right": pks_idx_plus_width,
        "idx_fwhm": pks_width,
    }


def find_peaks_in_spectrum_peakutils(
    x,
    y,
    min_intensity: float = 0,
    min_distance: int = 30,
    mz_range: Union[Tuple, List] = None,
    rel_height: float = 0.5,
    **kwargs,
):
    pks_idx = peakutils.indexes(y, min_intensity, min_distance, thres_abs=False if min_intensity < 1 else True)
    pks_x = x[pks_idx]
    pks_y = y[pks_idx]

    if mz_range is not None:
        mz_min, mz_max = mz_range
        pks_x = np.asarray(pks_x)
        mz_start_idx = np.argmin(np.abs(pks_x - mz_min))
        mz_end_idx = np.argmin(np.abs(pks_x - mz_max))
        pks_x = pks_x[mz_start_idx:mz_end_idx]
        pks_y = np.asarray(pks_y)[mz_start_idx:mz_end_idx]
        pks_idx = np.asarray(pks_idx)[mz_start_idx:mz_end_idx]

    pks_width, widths_height, left_ips, right_ips = peak_widths(y, pks_idx, rel_height=rel_height)

    # round-up peak width index
    pks_idx_width_half = np.ceil(pks_width / 2).astype(np.int32)
    # pks_idx_width = np.ceil(pks_width).astype(np.int32)

    # collect peak widths
    pks_idx_minus_width = pks_idx - pks_idx_width_half
    pks_idx_plus_width = pks_idx + pks_idx_width_half

    # get peaks
    pks_mz_x_minus_width = x[pks_idx_minus_width]
    pks_mz_x_plus_width = x[pks_idx_plus_width]

    return {
        "x": pks_x,
        "y": pks_y,
        "x_left": pks_mz_x_minus_width,
        "x_right": pks_mz_x_plus_width,
        "idx": pks_idx,
        "idx_left": pks_idx_minus_width,
        "idx_right": pks_idx_plus_width,
        "idx_fwhm": pks_width,
    }


def mask_peaks_props(pks_props, mask):
    """Mask peak properties"""
    for prop in pks_props:
        pks_props[prop] = pks_props[prop][mask]

    return pks_props


# noinspection DuplicatedCode
def find_peaks_local_max(x: np.ndarray, y: np.ndarray, window: int, threshold: float):
    """Find peaks using local maximum approach"""
    pks_idx = []
    pks_x = []
    pks_y = []
    length = len(x)
    max_intensity = max(y)
    intensity_threshold = max_intensity * threshold
    # iterate over the entire mass range
    for i in range(1, length):
        mz_x_value = x[i]
        mz_y_value = y[i]
        if mz_y_value > intensity_threshold:
            start = i - window
            end = i + window
            if start < 0:
                start = 0
            if end > length:
                end = length
            test_value = max(y[start : end + 1])
            if mz_y_value == test_value and mz_y_value != y[i - 1]:
                pks_idx.append(i)
                pks_x.append(mz_x_value)
                pks_y.append(mz_y_value)
    return pks_idx, pks_x, pks_y


try:
    has_c = True
    _find_peaks_local_max = find_peaks_local_max
    from origami.c.peaks import find_peaks_local_max
except ImportError as e:
    print(e)
    has_c = False
