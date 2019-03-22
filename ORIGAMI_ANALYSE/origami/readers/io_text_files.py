# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
#    Copyright (C) 2017-2018 Lukasz G. Migas
#    <lukasz.migas@manchester.ac.uk> OR <lukas.migas@yahoo.com>
#
# 	 GitHub : https://github.com/lukasz-migas/ORIGAMI
# 	 University of Manchester IP : https://www.click2go.umip.com/i/s_w/ORIGAMI.html
# 	 Cite : 10.1016/j.ijms.2017.08.014
#
#    This program is free software. Feel free to redistribute it and/or
#    modify it under the condition you cite and credit the authors whenever
#    appropriate.
#    The program is distributed in the hope that it will be useful but is
#    provided WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE
# -------------------------------------------------------------------------
# __author__ lukasz.g.migas

import os
import time

import numpy as np
import pandas as pd
from sklearn.preprocessing import normalize

from readers.io_utils import remove_non_digits_from_list


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
    if extension == '.csv':
        ms = pd.read_csv(path, header=None)
    elif extension in ['.txt', '.tab']:
        ms = pd.read_csv(path, delim_whitespace=True, header=None)

    if ms.shape[0] > 1000: return "MS"
    else: return "2D"


def text_infrared_open(path=None, normalize=None):  # textOpenIRData
    tstart = time.clock()

    outName = path.encode('ascii', 'replace')
    # Determine what file type it is
    fileNameExt = (str.split(outName, '.'))
    fileNameExt = fileNameExt[-1]
    if fileNameExt.lower() == 'csv':
        _imsDataText = np.genfromtxt(outName, delimiter=',', missing_values=[""], filling_values=[0])
    elif fileNameExt.lower() == 'txt':
        _imsDataText = np.genfromtxt(outName, delimiter='\t', missing_values=[""], filling_values=[0])

    # Remove values that are not numbers
    _imsDataText = np.nan_to_num(_imsDataText)
    yvals = _imsDataText[:, 0]
    xvals = _imsDataText[0, :]
    zvals = _imsDataText[1:, 1:]

    return zvals, xvals, yvals


def text_heatmap_open(path=None, normalize=None):  # textOpen2DIMSdata

#     outName = path.encode('ascii', 'replace')
    # Determine what file type it is
    fileNameExt = str.split(path, '.')
    fileNameExt = fileNameExt[-1]

    # Get data using pandas df
    df = pd.read_csv(path, sep='\t|,| ', engine='python', index_col=False)
    # First value at 0,0 is equal to zero
    df.rename(columns={'0.00':'', '0.00.1':'0.00'}, inplace=True)

    # Get xvalues
    xvals = df.columns.tolist()
    XaxisLabels = list(map(float, remove_non_digits_from_list(xvals)))

    # Remove NaNs
    df.dropna(axis=1, how="all", inplace=True)  # remove entire column that has NaNs
    df.fillna(value=0, inplace=True)

    # Convert df to matrix
    zvals = df.as_matrix()
    imsDataText = zvals[:, 1::]
    # Get yvalues
    YaxisLabels = zvals[:, 0]

    if (len(XaxisLabels) == (imsDataText.shape[1] + 1) and
        XaxisLabels[0] == 0):
        XaxisLabels = XaxisLabels[1::]

    print(('Labels size: {} x {} Array size: {} x {}'.format(len(XaxisLabels),
                                                            len(YaxisLabels),
                                                            len(imsDataText[0, :]),
                                                            len(imsDataText[:, 0]))))

    if normalize:
        imsDataTextNorm = normalize(imsDataText, axis=0, norm='max')  # Norm to 1
        return imsDataText, imsDataTextNorm, XaxisLabels, YaxisLabels
    else:
        return imsDataText, XaxisLabels, YaxisLabels


def text_spectrum_open(path=None):  # textOpenMSData

    # get extension
    fname, extension = os.path.splitext(path)
    dirname = os.path.dirname(path)

    # read data
    if extension == '.csv':
        ms = pd.read_csv(path, header=None)
    elif extension in ['.txt', '.tab']:
        ms = pd.read_csv(path, delim_whitespace=True, header=None)

    # check if first row is numerical
    if ms.loc[0, :].dtype != 'float64':
        print("Detected non-numerical values in the first row. Attempting to reopen the file and skipping the first row.")
        if extension == '.csv':
            ms = pd.read_csv(path, header=None, skiprows=1)
        elif extension in ['.txt', '.tab']:
            ms = pd.read_csv(path, delim_whitespace=True, header=None, skiprows=1)

    # check how many rows are present
    n_rows = ms.shape[1] - 1
    # convert to numpy array
    ms = np.array(ms)
    if n_rows > 1:
        print("MS file has more than two columns. In future each row will be combined into one MS and additional container will be created for multiple MS")
        xvals, yvals = ms[:, 0], ms[:, 1]
    else:
        xvals, yvals = ms[:, 0], ms[:, 1]
    return xvals, yvals, dirname, extension  # , n_rows


def text_ccsDatabase_open(filename=None):
    """ imports formated CCS database """

    try:
        df = pd.read_csv(filepath_or_buffer=filename, sep=',')
        df.fillna(0, inplace=True)
    except IOError: return None

    return df
