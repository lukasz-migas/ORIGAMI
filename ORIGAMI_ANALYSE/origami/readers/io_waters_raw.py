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

import time
import os.path
from subprocess import Popen, CREATE_NEW_CONSOLE
import numpy as np
from ctypes import cdll, c_float, byref

from toolbox import strictly_increasing
from processing.spectra import get_linearization_range, bin_1D, linearize
from gui_elements.misc_dialogs import dlgBox
from io_utils import clean_up

# Load C library
# mlLib = cdll.LoadLibrary(os.path.join(os.getcwd(), "readers\MassLynxRaw.dll"))
mass_lynx_raw_path = os.path.join(os.getcwd(), "MassLynxRaw.dll")
print("MassLynx path: {}".format(mass_lynx_raw_path))
mlLib = cdll.LoadLibrary(mass_lynx_raw_path)

# create data holder
temp_data_folder = os.path.join(os.getcwd(), "temporary_data")

#  USE DRIFTSCOPE


def rawMassLynx_MS_extract(path, bin_size=10000, rt_start=0, rt_end=99999.0, dt_start=1, dt_end=200,
                           mz_start=0, mz_end=50000, driftscope_path='C:\DriftScope\lib', **kwargs):
    """
    @param bin_size (int): number of points in the m/z dimension
    @param rt_start (float): start retention time (minutes)
    @param rt_end (float): end retention time (minutes)
    @param dt_start (float): start drift time (bins)
    @param dt_end (float): end drift time (bins)
    @param mz_start (float): start m/z  (Da)
    @param mz_end (float): end m/z (Da)
    @param driftscope_path (str): path to DriftScope directory
    """
    # check if data should be extracted to data folder OR temporary folder
    if kwargs.get("use_temp_folder", True) and os.path.exists(temp_data_folder):
        out_path = temp_data_folder
    else:
        out_path = path

    # Write range file
    range_file = os.path.join(out_path, '__.1dMZ.inp')
    try:
        fileID = open(range_file, 'w')
    except IOError as err:
        dlgBox(exceptionTitle="Error", exceptionMsg=str(err), type="Error")
        return

    fileID.write("%s %s %s\n%s %s 1\n%s %s 1" % (mz_start, mz_end, bin_size, rt_start, rt_end, dt_start, dt_end))
    fileID.close()

    # Create command for execution
    cmd = ''.join([driftscope_path, '\imextract.exe -d "', path, '" -f 1 -o "', out_path,
                   '\output.1dMZ" -t mobilicube -p "', range_file, '"'])
    # Extract command
    extractIMS = Popen(cmd, shell=kwargs.get("verbose", True),
                       creationflags=CREATE_NEW_CONSOLE)

    extractIMS.wait()

    # return data
    if kwargs.get("return_data", False):
        msX, msY = rawMassLynx_MS_load(out_path)
        return msX, msY
    else:
        return None


def rawMassLynx_MS_load(path=None, inputFile='output.1dMZ', normalize=True, **kwargs):
    datapath = os.path.join(path, inputFile)
    # Load data into array
    msData = np.fromfile(datapath, dtype=np.float32)
    msDataClean = msData[2:(-1)]
    numberOfRows = int(len(msDataClean) / 2)
    msDataReshape = msDataClean.reshape((2, numberOfRows), order='F')
    # Extract MS data
    msX = msDataReshape[1]
    msY = msDataReshape[0]

    # clean-up MS file
    firstBad = strictly_increasing(msX)
    if firstBad == True: pass
    else:
        firstBadIdx = np.where(msX == firstBad)
        try:
            msX = msX[0:(firstBadIdx[0][0] - 1)]
            msY = msY[0:(firstBadIdx[0][0] - 1)]
        except IndexError: pass

    # clean-up filepath
    try: clean_up(datapath)
    except: pass

    # Normalize MS data
    if normalize:
        msY = msY / max(msY)

    return msX, msY
    # ------------ #


def rawMassLynx_RT_extract(path=None, rt_start=0, rt_end=99999.0, dt_start=1, dt_end=200,
                           mz_start=0, mz_end=50000, driftscope_path='C:\DriftScope\lib',
                           **kwargs):
    """
    Extract the retention time for specified (or not) mass range
    """
    # check if data should be extracted to data folder OR temporary folder
    if kwargs.get("use_temp_folder", True) and os.path.exists(temp_data_folder):
        out_path = temp_data_folder
    else:
        out_path = path

    # Create input file
    range_file = os.path.join(out_path, '__.1dRT.inp')

    try:
        fileID = open(range_file, 'w')
    except IOError as err:
        dlgBox(exceptionTitle="Error", exceptionMsg=str(err), type="Error")
        return
    fileID.write("{} {} 1\n0.0 9999.0 5000\n{} {} 1".format(mz_start, mz_end, dt_start, dt_end))
    fileID.close()
    # Create command for execution
    cmd = ''.join([driftscope_path, '\imextract.exe -d "', path, '" -f 1 -o "',
                   out_path, '\output.1dRT" -t mobilicube -p "', range_file, '"'])

    extractIMS = Popen(cmd, shell=kwargs.get("verbose", True),
                       creationflags=CREATE_NEW_CONSOLE)
    extractIMS.wait()

    # return data
    if kwargs.get("return_data", False):
        if kwargs.get("normalize", False):
            rtY, rtYnorm = rawMassLynx_RT_load(out_path, normalize=True)
            rtX = np.arange(1, len(rtY) + 1)
            return rtX, rtY, rtYnorm
        else:
            rtY = rawMassLynx_RT_load(out_path)
            rtX = np.arange(1, len(rtY) + 1)
            return rtX, rtY
    else:
        return None


def rawMassLynx_RT_load(path=None, inputFile='output.1dRT', normalize=False, **kwargs):
    datapath = os.path.join(path, inputFile)
    rtData = np.fromfile(datapath, dtype=np.int32)
    rtDataClean = rtData[3::]
    nScans = rtData[1]
    rtDataReshape = rtDataClean.reshape((nScans, 2), order='C')
    rtData1D = rtDataReshape[:, 1]

    # clean-up filepath
    try: clean_up(datapath)
    except: pass

    if normalize:
        rtData1DNorm = rtData1D.astype(np.float64) / max(rtData1D)
        return rtData1D, rtData1DNorm
    else:
        return rtData1D


def rawMassLynx_DT_extract(path=None, rt_start=0, rt_end=99999.0, dt_start=1, dt_end=200,
                           mz_start=0, mz_end=50000, driftscope_path='C:\DriftScope\lib', **kwargs):
    """
    """
    # check if data should be extracted to data folder OR temporary folder
    if kwargs.get("use_temp_folder", True) and os.path.exists(temp_data_folder):
        out_path = temp_data_folder
    else:
        out_path = path

    # Create input file
    range_file = os.path.join(out_path, '__.1dDT.inp')
    try:
        fileID = open(range_file, 'w')
    except IOError as err:
        dlgBox(exceptionTitle="Error", exceptionMsg=str(err), type="Error")
        return
    fileID.write("{} {} 1\n{} {} 1\n1 200 200".format(mz_start, mz_end, rt_start, rt_end,))
    fileID.close()

    # Create command for execution
    cmd = ''.join([driftscope_path, '\imextract.exe -d "', path, '" -f 1 -o "',
                   out_path, '\output.1dDT" -t mobilicube -p "', range_file, '"'])
    extractIMS = Popen(cmd, shell=kwargs.get("verbose", True),
                       creationflags=CREATE_NEW_CONSOLE)
    extractIMS.wait()

    # return data
    if kwargs.get("return_data", False):
        if kwargs.get("normalize", False):
            dtY, dtYnorm = rawMassLynx_DT_load(out_path, normalize=True)
            dtX = np.arange(1, len(dtY) + 1)
            return dtX, dtY, dtYnorm
        else:
            dtY = rawMassLynx_DT_load(out_path)
            dtX = np.arange(1, len(dtY) + 1)
            return dtX, dtY
    else:
        return None


def rawMassLynx_DT_load(path=None, inputFile='output.1dDT', normalize=False, **kwargs):
    """
    Load data for 1D IM-MS data
    """
    datapath = os.path.join(path, inputFile)
    imsData = np.fromfile(datapath, dtype=np.int32)
    imsDataClean = imsData[3::]
    imsDataReshape = imsDataClean.reshape((200, 2), order='C')
    imsData1D = imsDataReshape[:, 1]

    # clean-up filepath
    try: clean_up(datapath)
    except: pass

    if normalize:
        imsData1DNorm = imsData1D.astype(np.float64) / max(imsData1D)
        return imsData1DNorm
    else:
        return imsData1D


def rawMassLynx_2DT_extract(path=None, mz_start=0, mz_end=50000, rt_start=0, rt_end=99999.0,
                            dt_start=1, dt_end=200, driftscope_path='C:\DriftScope\lib', **kwargs):
    # check if data should be extracted to data folder OR temporary folder
    if kwargs.get("use_temp_folder", True) and os.path.exists(temp_data_folder):
        out_path = temp_data_folder
    else:
        out_path = path

    # Create input file
    range_file = os.path.join(out_path, '__.2dRTDT.inp')
    try:
        fileID = open(range_file, 'w')
    except IOError as err:
        dlgBox(exceptionTitle="Error", exceptionMsg=str(err), type="Error")
        return
    fileID.write("{} {} 1\n{} {} 5000\n1 200 200".format(mz_start, mz_end, rt_start, rt_end))
    fileID.close()
    # Create command for execution
    cmd = ''.join([driftscope_path, '\imextract.exe -d "', path, '" -f 1 -o "', out_path,
                   '\output.2dRTDT" -t mobilicube -b 1 -scans 0 -p "', range_file, '"'])

    extractIMS = Popen(cmd, shell=kwargs.get("verbose", True),
                       creationflags=CREATE_NEW_CONSOLE)
    extractIMS.wait()

    # return data
    if kwargs.get("return_data", False):
        if kwargs.get("normalize", False):
            dt, dtnorm = rawMassLynx_2DT_load(out_path, normalize=True)
            return dt, dtnorm
        else:
            dt = rawMassLynx_2DT_load(out_path)
            return dt
    else:
        return None


def rawMassLynx_2DT_load(path=None, inputFile='output.2dRTDT', normalize=False, **kwargs):
    datapath = os.path.join(path, inputFile)
    imsData = np.fromfile(datapath, dtype=np.int32)
    imsDataClean = imsData[3::]
    numberOfRows = imsData[1]
    imsDataReshape = imsDataClean.reshape((200, numberOfRows), order='F')  # Reshapes the list to 2D array
    imsDataSplit = np.hsplit(imsDataReshape, int(numberOfRows / 5))  # Splits the array into [scans,200,5] array
    imsDataSplit = np.sum(imsDataSplit, axis=2).T  # Sums each 5 RT scans together

    """
    There is a bug - sometimes when extracting, the last column values
    go way outside of range and make the plot look terrible. Hacky way
    round this is to check that any values fall outside the range and if so,
    set the last column to 0s...
    """

    # Test to ensure all values are above 0 or below 1E8
    for value in imsDataSplit[:, -1]:
        if value < 0:
            imsDataSplit[:, -1] = 0
        elif value > 10000000:
            imsDataSplit[:, -1] = 0

    # clean-up filepath
    try: clean_up(datapath)
    except: pass

    if normalize:
        imsDataSplitNorm = normalize(imsDataSplit.astype(np.float64), axis=0, norm='max')  # Norm to 1
        return imsDataSplit, imsDataSplitNorm
    else:
        return imsDataSplit


def rawMassLynx_MZDT_extract(path=None, mz_start=0, mz_end=50000, mz_nPoints=5000, dt_start=1, dt_end=200,
                             silent_extract=True, driftscope_path='C:\DriftScope\lib', **kwargs):
    # check if data should be extracted to data folder OR temporary folder
    if kwargs.get("use_temp_folder", True) and os.path.exists(temp_data_folder):
        out_path = temp_data_folder
    else:
        out_path = path

    # Create input file
    range_file = os.path.join(out_path, '__.2dDTMZ.inp')
    try:
        fileID = open(range_file, 'w')
    except IOError as err:
        dlgBox(exceptionTitle="Error", exceptionMsg=str(err), type="Error")
        return
    fileID.write("{} {} {}\n0.0 9999.0 1\n{} {} 200".format(mz_start, mz_end, mz_nPoints, dt_start, dt_end))
    fileID.close()

    # Create command for execution
    cmd = ''.join([driftscope_path, '\imextract.exe -d "', path, '" -f 1 -o "',
                   out_path, '\output.2dDTMZ" -t mobilicube -p "', range_file, '"'])
    extractIMS = Popen(cmd, shell=kwargs.get("verbose", True),
                       creationflags=CREATE_NEW_CONSOLE)
    extractIMS.wait()

    # return data
    if kwargs.get("return_data", False):
        if kwargs.get("normalize", False):
            dt, dtnorm = rawMassLynx_MZDT_load(out_path, normalize=True)
            return dt, dtnorm
        else:
            dt = rawMassLynx_MZDT_load(out_path)
            return dt
    else:
        return None


def rawMassLynx_MZDT_load(path=None, inputFile='output.2dDTMZ', normalize=False, **kwargs):
    datapath = os.path.join(path, inputFile)
    imsData = np.fromfile(datapath, dtype=np.int32)
    imsDataClean = imsData[3::]
    numberOfBins = imsData[0]
    imsDataSplit = imsDataClean.reshape((200, numberOfBins), order='C')  # Reshapes the list to 2D array

    # clean-up filepath
    try: clean_up(datapath)
    except: pass

    if normalize:
        imsDataSplitNorm = normalize(imsDataSplit.astype(np.float64), axis=0, norm='max')  # Norm to 1
        return imsDataSplit, imsDataSplitNorm
    else:
        return imsDataSplit

# ##
# # USE C READER
# ##


def rawMassLynx_MS_bin(filename=None, startScan=0, endScan=-1, function=1,
                       mzStart=None, mzEnd=None, binsize=None, binData=False,
                       **kwargs):
    """
    Extract MS data, bin it
    ---
    @param binData: boolean, determines if data should be binned or not
    """
    tstart = time.clock()
    # Create pointer to the file
    try:
        filePointer = mlLib.newCMassLynxRawReader(filename)
    except WindowsError as err:
        dlgBox(exceptionTitle="Error", exceptionMsg=str(err), type="Error")
        return

    # Setup scan reader
    dataPointer = mlLib.newCMassLynxRawScanReader(filePointer)
    # Extract number of scans available from the file
    nScans = mlLib.getScansInFunction(dataPointer, function)
    # Initilise pointers to data
    xpoint = c_float()
    ypoint = c_float()
    # Initilise empty lists
    msX = []
    msY = []
    msDict = {}
    if endScan == -1 or endScan > nScans:
        endScan = nScans
    if 'linearization_mode' in kwargs:
        if kwargs['linearization_mode'] == 'Raw':
            binData = False

    if binsize == 0.: binData = False

    if binData:
        if 'auto_range' in kwargs and kwargs['auto_range'] :
            mzStart = kwargs['mz_min']
            mzEnd = kwargs['mz_max']

        if mzStart == None or mzEnd == None or binsize == None:
            print('Missing parameters')
            return
        elif kwargs['linearization_mode'] == "Binning":
            msList = np.arange(mzStart, mzEnd + binsize, binsize)
            msCentre = msList[:-1] + (binsize / 2)
        else:
            msCentre = get_linearization_range(mzStart, mzEnd, binsize, kwargs['linearization_mode'])

    msRange = np.arange(startScan, endScan) + 1
    # First extract data
    for scan in msRange:
        nPoints = mlLib.getScanSize(dataPointer, function, scan)
        # Read XY coordinates
        mlLib.getXYCoordinates(filePointer, function, scan, byref(xpoint), byref(ypoint))
        # Prepare pointers
        mzP = (c_float * nPoints)()
        mzI = (c_float * nPoints)()
        # Read spectrum
        mlLib.readSpectrum(dataPointer, function, scan, byref(mzP), byref(mzI))
        # Extract data from pointer and assign it to list
        msX = np.ndarray((nPoints,), 'f', mzP, order='C')
        msY = np.ndarray((nPoints,), 'f', mzI, order='C')
        if binData:
            if kwargs['linearization_mode'] == "Binning":
                msYbin = bin_1D(x=msX, y=msY, bins=msList)
            else:
                msCentre, msYbin = linearize(data=np.transpose([msX, msY]),
                                            binsize=binsize, mode=kwargs['linearization_mode'],
                                            input_list=msCentre)
            msDict[scan] = [msCentre, msYbin]
        else:
            msDict[scan] = [msX, msY]
    tend = time.clock()
    print("It took {:.4f} seconds to process {} scans".format((tend - tstart), len(msRange)))

    # Return data
    return msDict
