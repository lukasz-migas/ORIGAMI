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

# TODO: add another peak method that will try to determine the charge state:
# could be based on the the assumption that adjacent peaks will have same spacing when belonging to the same ion


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
    pks_idx_width_half = np.ceil((pks_props["widths"] / 2)).astype(np.int32)
    pks_idx_width = np.ceil(pks_props["widths"] * peak_width_modifier).astype(np.int32)

    # collect peak widths
    pks_idx_minus_width = pks_idx - pks_idx_width_half
    pks_idx_plus_width = pks_idx + pks_idx_width_half

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
    pks_idx_width_half = np.ceil((pks_width / 2)).astype(np.int32)
    pks_idx_width = np.ceil(pks_width).astype(np.int32)

    # collect peak widths
    pks_idx_minus_width = pks_idx - pks_idx_width_half
    pks_idx_plus_width = pks_idx + pks_idx_width_half

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


def detectPeaks(x, mph=None, mpd=1, threshold=0, edge='rising',
                 kpsh=False, valley=False, show=False, ax=None):

    """Detect peaks in data based on their amplitude and other features.
    __author__ = "Marcos Duarte, https://github.com/demotu/BMC"
    Parameters
    ----------
    x : 1D array_like
        data.
    mph : {None, number}, optional (default = None)
        detect peaks that are greater than minimum peak height.
    mpd : positive integer, optional (default = 1)
        detect peaks that are at least separated by minimum peak distance (in
        number of data).
    threshold : positive number, optional (default = 0)
        detect peaks (valleys) that are greater (smaller) than `threshold`
        in relation to their immediate neighbors.
    edge : {None, 'rising', 'falling', 'both'}, optional (default = 'rising')
        for a flat peak, keep only the rising edge ('rising'), only the
        falling edge ('falling'), both edges ('both'), or don't detect a
        flat peak (None).
    kpsh : bool, optional (default = False)
        keep peaks with same height even if they are closer than `mpd`.
    valley : bool, optional (default = False)
        if True (1), detect valleys (local minima) instead of peaks.
    show : bool, optional (default = False)
        if True (1), plot data in matplotlib figure.
    ax : a matplotlib.axes.Axes instance, optional (default = None).

    Returns
    -------
    ind : 1D array_like
        indeces of the peaks in `x`.

    Notes
    -----
    The detection of valleys instead of peaks is performed internally by simply
    negating the data: `ind_valleys = detect_peaks(-x)`
    
    The function can handle NaN's 

    See this IPython Notebook [1]_.

    References
    ----------
    .. [1] http://nbviewer.ipython.org/github/demotu/BMC/blob/master/notebooks/DetectPeaks.ipynb

    Examples
    --------
    >>> from detect_peaks import detect_peaks
    >>> x = np.random.randn(100)
    >>> x[60:81] = np.nan
    >>> # detect all peaks and plot data
    >>> ind = detect_peaks(x, show=True)
    >>> print(ind)

    >>> x = np.sin(2*np.pi*5*np.linspace(0, 1, 200)) + np.random.randn(200)/5
    >>> # set minimum peak height = 0 and minimum peak distance = 20
    >>> detect_peaks(x, mph=0, mpd=20, show=True)

    >>> x = [0, 1, 0, 2, 0, 3, 0, 2, 0, 1, 0]
    >>> # set minimum peak distance = 2
    >>> detect_peaks(x, mpd=2, show=True)

    >>> x = np.sin(2*np.pi*5*np.linspace(0, 1, 200)) + np.random.randn(200)/5
    >>> # detection of valleys instead of peaks
    >>> detect_peaks(x, mph=0, mpd=20, valley=True, show=True)

    >>> x = [0, 1, 1, 0, 1, 1, 0]
    >>> # detect both edges
    >>> detect_peaks(x, edge='both', show=True)

    >>> x = [-2, 1, -2, 2, 1, 1, 3, 0]
    >>> # set threshold = 2
    >>> detect_peaks(x, threshold = 2, show=True)
    """

    x = np.atleast_1d(x).astype('float64')
    if x.size < 3:
        return np.array([], dtype=int)
    if valley:
        x = -x
    # find indices of all peaks
    dx = x[1:] - x[:-1]
    # handle NaN's
    indnan = np.where(np.isnan(x))[0]
    if indnan.size:
        x[indnan] = np.inf
        dx[np.where(np.isnan(dx))[0]] = np.inf
    ine, ire, ife = np.array([[], [], []], dtype=int)
    if not edge:
        ine = np.where((np.hstack((dx, 0)) < 0) & (np.hstack((0, dx)) > 0))[0]
    else:
        if edge.lower() in ['rising', 'both']:
            ire = np.where((np.hstack((dx, 0)) <= 0) & (np.hstack((0, dx)) > 0))[0]
        if edge.lower() in ['falling', 'both']:
            ife = np.where((np.hstack((dx, 0)) < 0) & (np.hstack((0, dx)) >= 0))[0]
    ind = np.unique(np.hstack((ine, ire, ife)))
    # handle NaN's
    if ind.size and indnan.size:
        # NaN's and values close to NaN's cannot be peaks
        ind = ind[np.in1d(ind, np.unique(np.hstack((indnan, indnan - 1, indnan + 1))), invert=True)]
    # first and last values of x cannot be peaks
    if ind.size and ind[0] == 0:
        ind = ind[1:]
    if ind.size and ind[-1] == x.size - 1:
        ind = ind[:-1]
    # remove peaks < minimum peak height
    if ind.size and mph is not None:
        ind = ind[x[ind] >= mph]
    # remove peaks - neighbors < threshold
    if ind.size and threshold > 0:
        dx = np.min(np.vstack([x[ind] - x[ind - 1], x[ind] - x[ind + 1]]), axis=0)
        ind = np.delete(ind, np.where(dx < threshold)[0])
    # detect small peaks closer than minimum peak distance
    if ind.size and mpd > 1:
        ind = ind[np.argsort(x[ind])][::-1]  # sort ind by peak height
        idel = np.zeros(ind.size, dtype=bool)
        for i in range(ind.size):
            if not idel[i]:
                # keep peaks with the same height if kpsh is True
                idel = idel | (ind >= ind[i] - mpd) & (ind <= ind[i] + mpd) \
                    & (x[ind[i]] > x[ind] if kpsh else True)
                idel[i] = 0  # Keep current peak
        # remove the small peaks and sort back the indices by their occurrence
        ind = np.sort(ind[~idel])

    return ind
