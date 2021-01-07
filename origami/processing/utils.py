# Standard library imports
from typing import List
from typing import Union
from operator import itemgetter
from itertools import groupby
from collections import Iterable

# Third-party imports
import numpy as np

# Local imports
from origami.utils.check import check_value_order


def ppm_error(x, y):
    """Calculate ppm error"""
    return (x - y) / y


def nthroot(value, n):
    """Calculate the n-th root of any number"""
    return value ** (1 / float(n))


def detect_peaks_chromatogram(data, threshold, add_buffer=0):  # detectPeaksRT
    """
    This function searches for split in the sequence of numbers (when signal goes to 0)
    and returns the xy coordinates for the rectangle to be plotted
    ---
    output : list of tuples, start and end x coordinates
    """
    inxY = np.where(data[:, 1] > threshold)
    valX = data[inxY, 0]
    valY = data[inxY, 1]
    valXX = valX.astype(int).tolist()[0]
    # Find index values
    outlist = []
    apex_list = []
    for k, g in groupby(enumerate(valXX), lambda i_x: i_x[0] - i_x[1]):
        x = list(map(itemgetter(1), g))  # list of vals
        xStart = x[0]  # get x start
        xEnd = x[-1]  # get x end

        if (xStart - xEnd) == 0:
            apex_list.append([xStart, xEnd])
            xStart = xStart - add_buffer
            xEnd = xEnd + add_buffer

        outlist.append([xStart, xEnd])

    # pair list
    outlistRav = np.ravel(outlist) - 1
    try:
        valXout = data[outlistRav, 0]
        valYout = data[outlistRav, 1]
        output = np.array(list(zip(valXout, valYout)))
    except IndexError:
        output = []
    # apex list
    try:
        apexListRav = np.ravel(apex_list) - 1
        apexListRav = np.unique(apexListRav)
        valXout = data[apexListRav, 0]
        valYout = data[apexListRav, 1]
        apexlist = np.array(list(zip(valXout, valYout)))
    except IndexError:
        apexlist = []

    return output, outlist, apexlist


def find_peak_maximum(data, fail_value=1):
    """
    Simple tool to find the intensity (maximum) of a selected peak
    ---
    data: array [ms, intensity]
    return max value
    """
    try:
        ymax = np.amax(data[:, 1])
    except ValueError:
        print("Failed to find value. Ymax set to maximum, {}".format(fail_value))
        ymax = fail_value
    return ymax


def find_nearest_index(data: np.ndarray, value: Union[int, float, np.ndarray, List]):
    """Find nearest index of asked value

    Parameters
    ----------
    data : np.array
        input array (e.g. m/z values)
    value : Union[int, float, np.ndarray]
        asked value

    Returns
    -------
    index : int
        index value
    """
    data = np.asarray(data)
    if isinstance(value, Iterable):
        return [np.argmin(np.abs(data - _value)) for _value in value]
    return np.argmin(np.abs(data - value))


def get_maximum_xy(x, y, x_min, x_max):
    """Get the maximum value in two arrays based on an intensity array"""
    if len(x) != len(y):
        raise ValueError("Incorrect array lengths!")
    x, y = np.asarray(x), np.asarray(y)
    idx_min, idx_max = find_nearest_index(x, [x_min, x_max])
    y_idx = y[idx_min : idx_max + 1].argmax()
    return x[idx_min : idx_max + 1][y_idx], y[idx_min : idx_max + 1][y_idx]


def get_narrow_data_range(data, mzRange=None):
    """ Find and return a narrow data range """
    start = find_nearest_index(data[:, 0], mzRange[0])  # np.argmin(np.abs(data[:, 0] - mzRange[0]))
    end = find_nearest_index(data[:, 0], mzRange[1])  # np.argmin(np.abs(data[:, 0] - mzRange[1]))

    start, end = check_value_order(start, end)

    dataOut = data[start:end, :]
    return dataOut


try:
    has_c = True
    _ppm_error = ppm_error
    # Local imports
    from origami.c.utilities import ppm_error
except ImportError as e:
    print(e)
    has_c = False
