# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
#    Copyright (C) 2017-2018 Lukasz G. Migas
#    <lukasz.migas@manchester.ac.uk> OR <lukas.migas@yahoo.com>
#
#      GitHub : https://github.com/lukasz-migas/ORIGAMI
#      University of Manchester IP : https://www.click2go.umip.com/i/s_w/ORIGAMI.html
#      Cite : 10.1016/j.ijms.2017.08.014
#
#    This program is free software. Feel free to redistribute it and/or
#    modify it under the condition you cite and credit the authors whenever
#    appropriate.
#    The program is distributed in the hope that it will be useful but is
#    provided WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE
# -------------------------------------------------------------------------
# __author__ lukasz.g.migas

from utils.time import ttime
import numpy as np
from scipy.signal import find_peaks, peak_widths

import logging
logger = logging.getLogger("origami")


def mask_peaks_props(pks_props, mask):
    for prop in pks_props:
        pks_props[prop] = pks_props[prop][mask]

    return pks_props


def find_peaks_in_spectrum_peak_properties(x_signal, y_signal, threshold=250, width=0, rel_height=0.5, min_intensity=0., distance=1,
                           mz_min=None, mz_max=None, peak_width_modifier=1.0, verbose=True):
    tstart = ttime()

    # find peaks
    pks_idx, pks_props = find_peaks(y_signal, threshold=threshold, width=width, rel_height=rel_height,
                                    distance=distance)

    # extract peak values
    pks_x = x_signal[pks_idx]
    pks_y = y_signal[pks_idx]

    # adjust mass range if it was user-specified
    if mz_min:
        pks_idx_mask = pks_x >= mz_min
        pks_x = pks_x[pks_idx_mask]
        pks_y = pks_y[pks_idx_mask]
        pks_idx = pks_idx[pks_idx_mask]
        pks_props = mask_peaks_props(pks_props, pks_idx_mask)

    if mz_max:
        pks_idx_mask = pks_x <= mz_max
        pks_x = pks_x[pks_idx_mask]
        pks_y = pks_y[pks_idx_mask]
        pks_idx = pks_idx[pks_idx_mask]
        pks_props = mask_peaks_props(pks_props, pks_idx_mask)

    # calculate minimum threshold
    try:
        pks_idx_mask = pks_y > np.max(pks_y) * min_intensity
    except ValueError:
        pks_idx_mask = []
    pks_idx = pks_idx[pks_idx_mask]
    pks_props = mask_peaks_props(pks_props, pks_idx_mask)

    # extract peak values
    pks_x = x_signal[pks_idx]
    pks_y = y_signal[pks_idx]

    # round-up peak width index
    pks_idx_width = np.ceil(pks_props["widths"] * peak_width_modifier).astype(np.int32)

    # collect peak widths
    pks_idx_minus_width = pks_idx - pks_idx_width
    pks_idx_plus_width = pks_idx + pks_idx_width

    # make sure index falls within the data size
    pks_idx_minus_width[pks_idx_minus_width < 0] = 0
    pks_idx_plus_width[pks_idx_plus_width > len(y_signal) - 1] = len(y_signal) - 1

    # get peaks
    pks_mz_x_minus_width = x_signal[pks_idx_minus_width]
    pks_mz_x_plus_width = x_signal[pks_idx_plus_width]
    pks_mz_x_width = pks_mz_x_plus_width - pks_mz_x_minus_width

    if verbose:
        logger.info(f"Found {len(pks_idx)} peaks in {ttime() - tstart:.4f} seconds")

    peaks_dict = \
        {"peaks_x_values": pks_x,
         "peaks_y_values": pks_y,
         "peaks_x_minus_width": pks_mz_x_minus_width,
         "peaks_x_plus_width": pks_mz_x_plus_width,
         "peaks_x_width": pks_mz_x_width,
         "peaks_index": pks_idx,
         "peaks_index_width": pks_idx_width,
         "peaks_index_x_minus_width": pks_idx_minus_width,
         "peaks_index_x_plus_width": pks_idx_plus_width,
         "peaks_properties": pks_props}

    return peaks_dict


def find_peaks_in_spectrum_local_search(data, window=10, threshold=0, mz_range=None, **kwargs):
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
    mz_range: tuple
        user-defined mass range (ms start, ms end)
    """
    tstart = ttime()
    # modify search space
    if mz_range is not None:
        mz_min, mz_max = mz_range
        mz_start_idx = np.argmin(np.abs(data[:, 0] - mz_min))
        mz_end_idx = np.argmin(np.abs(data[:, 0] - mz_max))
        data = data[mz_start_idx:mz_end_idx, :]

    # pre-allocate space
    pks_idx, pks_x, pks_y = [], [], []
    length = len(data)
    maxval = np.amax(data[:, 1])
    # iterate over the entire mass range
    for i in range(1, length):
        mz_x_value = data[i, 0]
        mz_y_value = data[i, 1]
        if mz_y_value > maxval * threshold:
            start = i - window
            end = i + window
            if start < 0:
                start = 0
            if end > length:
                end = length
            testmax = np.amax(data[int(start):int(end) + 1, 1])
            if mz_y_value == testmax and mz_y_value != data[i - 1, 1]:
                pks_idx.append(i)
                pks_x.append(mz_x_value)
                pks_y.append(mz_y_value)

    # calculate peak widths at FWHM
    mz_x = data[:, 0]
    mz_y = data[:, 1]

    pks_width, widths_height, left_ips, right_ips = peak_widths(
        mz_y, pks_idx, rel_height=kwargs.get("rel_height", .5))
    pks_props = \
        {"left_ips": left_ips,
         "right_ips": right_ips,
         "width_heights": widths_height,
         "widths": pks_width}

    # round-up peak width index
    pks_idx_width = np.ceil(pks_width).astype(np.int32)

    # collect peak widths
    pks_idx_minus_width = pks_idx - pks_idx_width
    pks_idx_plus_width = pks_idx + pks_idx_width

    # get peaks
    pks_mz_x_minus_width = mz_x[pks_idx_minus_width]
    pks_mz_x_plus_width = mz_x[pks_idx_plus_width]
    pks_mz_x_width = pks_mz_x_plus_width - pks_mz_x_minus_width

    if kwargs.get("verbose", False):
        logger.info(f"Found {len(pks_idx)} peaks in {ttime() - tstart:.4f} seconds")

    # generate output dictionary
    peaks_dict = \
        {"peaks_x_values": pks_x,
         "peaks_y_values": pks_y,
         "peaks_x_minus_width": pks_mz_x_minus_width,
         "peaks_x_plus_width": pks_mz_x_plus_width,
         "peaks_x_width": pks_mz_x_width,
         "peaks_index": pks_idx,
         "peaks_index_width": pks_idx_width,
         "peaks_index_x_minus_width": pks_idx_minus_width,
         "peaks_index_x_plus_width": pks_idx_plus_width,
         "peaks_properties": pks_props}

    return peaks_dict
