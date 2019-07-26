# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import logging
import os
import time

import numpy as np
import pandas as pd
from readers.io_utils import remove_non_digits_from_list

logger = logging.getLogger("origami")


def check_file_type(path=None, fileName=None):
    """
    Simple check if the text file is likely to be MS or 2D type. Checks based
    on the length of the list. If value above 1000 rows, its unlikely to be
    a 2D datafile. Obviously this might be wrong assumption! It is checked when
    files are dropped into the main window.
    """
    # get extension
    fname, extension = os.path.splitext(path)
    dirname = os.path.dirname(path)

    # read data
    if extension == ".csv":
        ms = pd.read_csv(path, header=None)
    elif extension in [".txt", ".tab"]:
        ms = pd.read_csv(path, delim_whitespace=True, header=None)

    if ms.shape[0] > 1000:
        return "MS"

    return "2D"


def text_infrared_open(path=None, normalize=None):  # textOpenIRData
    tstart = time.clock()

    outName = path.encode("ascii", "replace")
    # Determine what file type it is
    fileNameExt = str.split(outName, ".")
    fileNameExt = fileNameExt[-1]
    if fileNameExt.lower() == "csv":
        _imsDataText = np.genfromtxt(outName, delimiter=",", missing_values=[""], filling_values=[0])
    elif fileNameExt.lower() == "txt":
        _imsDataText = np.genfromtxt(outName, delimiter="\t", missing_values=[""], filling_values=[0])

    # Remove values that are not numbers
    _imsDataText = np.nan_to_num(_imsDataText)
    yvals = _imsDataText[:, 0]
    xvals = _imsDataText[0, :]
    zvals = _imsDataText[1:, 1:]

    return zvals, xvals, yvals


# TODO: remove pandas dependency


def text_heatmap_open(path=None, normalize=None):  # textOpen2DIMSdata

    #     outName = path.encode('ascii', 'replace')
    # Determine what file type it is
    fileNameExt = str.split(path, ".")
    fileNameExt = fileNameExt[-1]

    # Get data using pandas df
    df = pd.read_csv(path, sep="\t|,| ", engine="python", index_col=False)

    # First value at 0,0 is equal to zero
    df.rename(columns={"0.00": "", "0.00.1": "0.00"}, inplace=True)

    # Get xvalues
    xvals_list = df.columns.tolist()
    xvals = list(map(float, remove_non_digits_from_list(xvals_list)))

    # Remove NaNs
    df.dropna(axis=1, how="all", inplace=True)  # remove entire column that has NaNs
    df.fillna(value=0, inplace=True)

    # Convert df to matrix
    df_array = df.as_matrix()
    zvals = df_array[:, 1::]
    # Get yvalues
    yvals = df_array[:, 0]

    if len(xvals) == (zvals.shape[1] + 1) and xvals[0] == 0:
        xvals = xvals[1::]

    print("Labels size: {} x {} Array size: {} x {}".format(len(xvals), len(yvals), len(zvals[0, :]), len(zvals[:, 0])))

    if normalize:
        zvals_norm = normalize(zvals, axis=0, norm="max")  # Norm to 1
        return zvals, zvals_norm, xvals, yvals

    return zvals, xvals, yvals


def text_spectrum_open(path=None):  # textOpenMSData

    # get extension
    fname, extension = os.path.splitext(path)
    dirname = os.path.dirname(path)

    # read data
    if extension == ".csv":
        ms = pd.read_csv(path, header=None)
    elif extension in [".txt", ".tab"]:
        ms = pd.read_csv(path, delim_whitespace=True, header=None)

    # check if first row is numerical
    if ms.loc[0, :].dtype != "float64":
        print(
            "Detected non-numerical values in the first row. Attempting to reopen the file and skipping the first row."
        )
        if extension == ".csv":
            ms = pd.read_csv(path, header=None, skiprows=1)
        elif extension in [".txt", ".tab"]:
            ms = pd.read_csv(path, delim_whitespace=True, header=None, skiprows=1)

    # check how many rows are present
    n_rows = ms.shape[1] - 1
    # convert to numpy array
    ms = np.array(ms)
    if n_rows > 1:
        print(
            "MS file has more than two columns. In future each row will be combined into one MS and additional container will be created for multiple MS"
        )
        xvals, yvals = ms[:, 0], ms[:, 1]
    else:
        xvals, yvals = ms[:, 0], ms[:, 1]
    return xvals, yvals, dirname, extension  # , n_rows


def text_ccs_database_open(filename):
    """ imports formated CCS database """

    try:
        df = pd.read_csv(filepath_or_buffer=filename, sep=",")
        df.fillna(0, inplace=True)
    except IOError:
        return None

    return df


def save_data(filename, data, header=None, fmt="%.4f", delimiter=",", **kwargs):
    """Save data using numpy's savetxt
    """
    if kwargs.pop("transpose", False):
        data = np.transpose(data)

    try:
        np.savetxt(filename, data, fmt=format, delimiter=delimiter, header=header, **kwargs)
    except IOError:
        logger.error(f"Failed to save file {filename} as it is currently in use.")
