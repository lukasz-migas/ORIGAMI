# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import logging
import os.path
from subprocess import CREATE_NEW_CONSOLE
from subprocess import Popen

import numpy as np
from gui_elements.misc_dialogs import DialogBox
from readers.io_utils import clean_up
from toolbox import strictly_increasing
from utils.path import check_waters_path
logger = logging.getLogger('origami')

# Load C library
# mlLib = cdll.LoadLibrary(os.path.join("MassLynxRaw.dll"))

# create data holder
temp_data_folder = os.path.join(os.getcwd(), 'temporary_data')


# ##
# USE DRIFTSCOPE
# ##
def driftscope_extract_MS(
    path, bin_size=10000,
    rt_start=0, rt_end=99999.0,
    dt_start=1, dt_end=200,
    mz_start=0, mz_end=99999,
    driftscope_path=r'C:\DriftScope\lib', **kwargs
):
    """
    Extract MS data from MassLynx (.raw) file that has IMS data
    @param path (str): path to MassLynx (.raw) file
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
    if kwargs.get('use_temp_folder', True) and os.path.exists(temp_data_folder):
        out_path = temp_data_folder
    else:
        out_path = path

    path = check_waters_path(path)

    # Write range file
    range_file = os.path.join(out_path, '__.1dMZ.inp')
    try:
        input_file = open(range_file, 'w')
    except IOError as err:
        DialogBox(exceptionTitle='Error', exceptionMsg=str(err), type='Error')
        return

    input_file.write(
        '{} {} {}\n{} {} 1\n{} {} 1'.format(
            mz_start, mz_end, bin_size,
            rt_start, rt_end,
            dt_start, dt_end,
        ),
    )
    input_file.close()

    # Create command for execution
    cmd = r'{}\imextract.exe -d "{}" -f 1 -o "{}\output.1dMZ" -t mobilicube -p "{}'.format(
        driftscope_path, path, out_path, range_file,
    )

    # Extract command
    process_id = Popen(cmd, shell=kwargs.get('verbose', True), creationflags=CREATE_NEW_CONSOLE)
    process_id.wait()

    # return data
    if kwargs.get('return_data', False):
        msX, msY = rawMassLynx_MS_load(out_path)
        return msX, msY
    else:
        return None


def rawMassLynx_MS_load(path=None, inputFile='output.1dMZ', normalize=True, **kwargs):
    data_path = os.path.join(path, inputFile)
    # Load data into array
    data = np.fromfile(data_path, dtype=np.float32)
    data_clean = data[2:(-1)]
    n_rows = int(len(data_clean) / 2)
    msDataReshape = data_clean.reshape((2, n_rows), order='F')
    # Extract MS data
    data_x = msDataReshape[1]
    data_y = msDataReshape[0]

    # clean-up MS file
    firstBad = strictly_increasing(data_x)
    if firstBad:
        pass
    else:
        firstBadIdx = np.where(data_x == firstBad)
        try:
            data_x = data_x[0:(firstBadIdx[0][0] - 1)]
            data_y = data_y[0:(firstBadIdx[0][0] - 1)]
        except IndexError:
            pass

    # clean-up filepath
    try:
        clean_up(data_path)
    except Exception as e:
        logger.warning('Failed to delete file. Error: {}'.format(e))

    # Normalize MS data
    if normalize:
        data_y = data_y / max(data_y)

    return data_x, data_y


def driftscope_extract_RT(
    path=None, rt_start=0, rt_end=99999.0, dt_start=1, dt_end=200,
    mz_start=0, mz_end=999999, driftscope_path=r'C:\DriftScope\lib',
    **kwargs
):
    """
    Extract the retention time for specified (or not) mass range
    """
    # check if data should be extracted to data folder OR temporary folder
    if kwargs.get('use_temp_folder', True) and os.path.exists(temp_data_folder):
        out_path = temp_data_folder
    else:
        out_path = path

    path = check_waters_path(path)

    # Create input file
    range_file = os.path.join(out_path, '__.1dRT.inp')

    try:
        input_file = open(range_file, 'w')
    except IOError as err:
        DialogBox(exceptionTitle='Error', exceptionMsg=str(err), type='Error')
        return
    input_file.write(
        '{} {} 1\n{} {} 5000\n{} {} 1'.format(
            mz_start, mz_end,
            rt_start, rt_end,
            dt_start, dt_end,
        ),
    )
    input_file.close()

    # Create command for execution
    cmd = r'{}\imextract.exe -d "{}" -f 1 -o "{}\output.1dRT" -t mobilicube -p "{}'.format(
        driftscope_path, path, out_path, range_file,
    )

    process_id = Popen(cmd, shell=kwargs.get('verbose', True), creationflags=CREATE_NEW_CONSOLE)
    process_id.wait()

    # return data
    if kwargs.get('return_data', False):
        if kwargs.get('normalize', False):
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
    data_path = os.path.join(path, inputFile)
    data = np.fromfile(data_path, dtype=np.int32)
    n_scans = data[1]
    data_clean = data[3::]
    data_reshape = data_clean.reshape((n_scans, 2), order='C')
    data_1D = data_reshape[:, 1]

    # clean-up filepath
    try:
        clean_up(data_path)
    except Exception as e:
        logger.warning('Failed to delete file. Error: {}'.format(e))

    if normalize:
        data_1D_norm = data_1D.astype(np.float64) / max(data_1D)
        return data_1D, data_1D_norm
    else:
        return data_1D


def driftscope_extract_DT(
    path=None, rt_start=0, rt_end=99999.0, dt_start=1, dt_end=200,
    mz_start=0, mz_end=999999, driftscope_path=r'C:\DriftScope\lib', **kwargs
):
    # check if data should be extracted to data folder OR temporary folder
    if kwargs.get('use_temp_folder', True) and os.path.exists(temp_data_folder):
        out_path = temp_data_folder
    else:
        out_path = path

    path = check_waters_path(path)

    # Create input file
    range_file = os.path.join(out_path, '__.1dDT.inp')
    try:
        input_file = open(range_file, 'w')
    except IOError as err:
        DialogBox(exceptionTitle='Error', exceptionMsg=str(err), type='Error')
        return
    input_file.write(
        '{} {} 1\n{} {} 1\n{} {} 200'.format(
            mz_start, mz_end,
            rt_start, rt_end,
            dt_start, dt_end,
        ),
    )
    input_file.close()

    # Create command for execution
    cmd = r'{}\imextract.exe -d "{}" -f 1 -o "{}\output.1dDT" -t mobilicube -p "{}'.format(
        driftscope_path, path, out_path, range_file,
    )
    process_id = Popen(cmd, shell=kwargs.get('verbose', True), creationflags=CREATE_NEW_CONSOLE)
    process_id.wait()

    # return data
    if kwargs.get('return_data', False):
        if kwargs.get('normalize', False):
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
    data_path = os.path.join(path, inputFile)
    data = np.fromfile(data_path, dtype=np.int32)
    data_clean = data[3::]
    data_reshape = data_clean.reshape((200, 2), order='C')
    data_1D = data_reshape[:, 1]

    # clean-up filepath
    try:
        clean_up(data_path)
    except Exception as e:
        logger.warning('Failed to delete file. Error: {}'.format(e))

    if normalize:
        data_1D_norm = data_1D.astype(np.float64) / max(data_1D)
        return data_1D_norm
    else:
        return data_1D


def driftscope_extract_2D(
    path=None, mz_start=0, mz_end=999999, rt_start=0, rt_end=99999.0,
    dt_start=1, dt_end=200, driftscope_path=r'C:\DriftScope\lib', **kwargs
):
    # check if data should be extracted to data folder OR temporary folder
    if kwargs.get('use_temp_folder', True) and os.path.exists(temp_data_folder):
        out_path = temp_data_folder
    else:
        out_path = path

    path = check_waters_path(path)

    # Create input file
    range_file = os.path.join(out_path, '__.2dRTDT.inp')
    try:
        input_file = open(range_file, 'w')
    except IOError as err:
        DialogBox(exceptionTitle='Error', exceptionMsg=str(err), type='Error')
        return
    input_file.write(
        '{} {} 1\n{} {} 5000\n{} {} 200'.format(
            mz_start, mz_end,
            rt_start, rt_end,
            dt_start, dt_end,
        ),
    )
    input_file.close()
    # Create command for execution
    cmd = r'{}\imextract.exe -d "{}" -f 1 -o "{}\output.2dRTDT" -t mobilicube -b 1 -scans 0 -p "{}'.format(
        driftscope_path, path, out_path, range_file,
    )

    process_id = Popen(cmd, shell=kwargs.get('verbose', True), creationflags=CREATE_NEW_CONSOLE)
    process_id.wait()

    # return data
    if kwargs.get('return_data', False):
        if kwargs.get('normalize', False):
            dt, dtnorm = rawMassLynx_2DT_load(out_path, normalize=True)
            return dt, dtnorm
        else:
            dt = rawMassLynx_2DT_load(out_path)
            return dt
    else:
        return None


def rawMassLynx_2DT_load(path=None, inputFile='output.2dRTDT', normalize=False, **kwargs):
    data_path = os.path.join(path, inputFile)
    data = np.fromfile(data_path, dtype=np.int32)
    data_clean = data[3::]
    n_rows = data[1]
    data_reshape = data_clean.reshape((200, n_rows), order='F')  # Reshapes the list to 2D array
    data_split = np.hsplit(data_reshape, int(n_rows / 5))  # Splits the array into [scans,200,5] array
    data_split = np.sum(data_split, axis=2).T  # Sums each 5 RT scans together

    """
    There is a bug - sometimes when extracting, the last column values
    go way outside of range and make the plot look terrible. Hacky way
    round this is to check that any values fall outside the range and if so,
    set the last column to 0s...
    """

    # Test to ensure all values are above 0 or below 1E8
    for value in data_split[:, -1]:
        if value < 0:
            data_split[:, -1] = 0
        elif value > 10000000:
            data_split[:, -1] = 0

    # clean-up filepath
    try:
        clean_up(data_path)
    except Exception as e:
        logger.warning('Failed to delete file. Error: {}'.format(e))

    if normalize:
        data_split_norm = normalize(data_split.astype(np.float64), axis=0, norm='max')  # Norm to 1
        return data_split, data_split_norm
    else:
        return data_split


def driftscope_extract_MZDT(
    path=None, mz_start=0, mz_end=999999, mz_nPoints=5000, dt_start=1, dt_end=200,
    silent_extract=True, driftscope_path=r'C:\DriftScope\lib', **kwargs
):
    # check if data should be extracted to data folder OR temporary folder
    if kwargs.get('use_temp_folder', True) and os.path.exists(temp_data_folder):
        out_path = temp_data_folder
    else:
        out_path = path

    path = check_waters_path(path)

    # Create input file
    range_file = os.path.join(out_path, '__.2dDTMZ.inp')
    try:
        input_file = open(range_file, 'w')
    except IOError as err:
        DialogBox(exceptionTitle='Error', exceptionMsg=str(err), type='Error')
        return
    input_file.write(
        '{} {} {}\n0.0 9999.0 1\n{} {} 200'.format(
            mz_start, mz_end, mz_nPoints,
            dt_start, dt_end,
        ),
    )
    input_file.close()

    # Create command for execution
    cmd = r'{}\imextract.exe -d "{}" -f 1 -o "{}\output.2dDTMZ" -t mobilicube -p "{}'.format(
        driftscope_path, path, out_path, range_file,
    )

    process_id = Popen(cmd, shell=kwargs.get('verbose', True), creationflags=CREATE_NEW_CONSOLE)
    process_id.wait()

    # return data
    if kwargs.get('return_data', False):
        if kwargs.get('normalize', False):
            dt, dtnorm = rawMassLynx_MZDT_load(out_path, normalize=True)
            return dt, dtnorm
        else:
            dt = rawMassLynx_MZDT_load(out_path)
            return dt
    else:
        return None


def rawMassLynx_MZDT_load(path=None, inputFile='output.2dDTMZ', normalize=False, **kwargs):
    data_path = os.path.join(path, inputFile)
    data = np.fromfile(data_path, dtype=np.int32)
    data_clean = data[3::]
    n_bins = data[0]
    data_reshaped = data_clean.reshape((200, n_bins), order='C')  # Reshapes the list to 2D array

    # clean-up filepath
    try:
        clean_up(data_path)
    except Exception as e:
        logger.warning('Failed to delete file. Error: {}'.format(e))

    if normalize:
        data_reshaped_norm = normalize(data_reshaped.astype(np.float64), axis=0, norm='max')  # Norm to 1
        return data_reshaped, data_reshaped_norm
    else:
        return data_reshaped

# # ##
# # USE C READER
# # ##
#
#
# def rawMassLynx_MS_bin(filename, startScan=0, endScan=-1, function=1,
#                        mzStart=None, mzEnd=None, binsize=None, binData=False,
#                        **kwargs):
#     """
#     Extract MS data, bin it
#     ---
#     @param binData: boolean, determines if data should be binned or not
#     """
#     tstart = time.clock()
#     # Create pointer to the file
# #     try:
#     filePointer = mlLib.newCMassLynxRawReader(filename)
# #     except WindowsError as err:
# #         DialogBox(exceptionTitle="Error", exceptionMsg=str(err), type="Error")
# #         return
#
#     # Setup scan reader
#     dataPointer = mlLib.newCMassLynxRawScanReader(filePointer)
#     # Extract number of scans available from the file
#     nScans = mlLib.getScansInFunction(dataPointer, function)
#     # Initilise pointers to data
#     xpoint = c_float()
#     ypoint = c_float()
#     # Initilise empty lists
#     msX = []
#     msY = []
#     msDict = {}
#     if endScan == -1 or endScan > nScans:
#         endScan = nScans
#     if 'linearization_mode' in kwargs:
#         if kwargs['linearization_mode'] == 'Raw':
#             binData = False
#
#     if binsize == 0.:
#         binData = False
#
#     if binData:
#         if 'auto_range' in kwargs and kwargs['auto_range']:
#             mzStart = kwargs['mz_min']
#             mzEnd = kwargs['mz_max']
#
#         if mzStart is None or mzEnd is None or binsize is None:
#             logger.warning('Missing parameters')
#             return
#         elif kwargs['linearization_mode'] == "Binning":
#             msList = np.arange(mzStart, mzEnd + binsize, binsize)
#             msCentre = msList[:-1] + (binsize / 2)
#         else:
#             msCentre = get_linearization_range(mzStart, mzEnd, binsize, kwargs['linearization_mode'])
#
#     msRange = np.arange(startScan, endScan) + 1
#     # First extract data
#     for scan in msRange:
#         nPoints = mlLib.getScanSize(dataPointer, function, scan)
#         # Read XY coordinates
#         mlLib.getXYCoordinates(filePointer, function, scan, byref(xpoint), byref(ypoint))
#         # Prepare pointers
#         mzP = (c_float * nPoints)()
#         mzI = (c_float * nPoints)()
#         # Read spectrum
#         mlLib.readSpectrum(dataPointer, function, scan, byref(mzP), byref(mzI))
#         # Extract data from pointer and assign it to list
#         msX = np.ndarray((nPoints,), 'f', mzP, order='C')
#         msY = np.ndarray((nPoints,), 'f', mzI, order='C')
#         if binData:
#             if kwargs['linearization_mode'] == "Binning":
#                 msYbin = bin_1D(x=msX, y=msY, bins=msList)
#             else:
#                 msCentre, msYbin = linearize(data=np.transpose([msX, msY]),
#                                              binsize=binsize, mode=kwargs['linearization_mode'],
#                                              input_list=msCentre)
#             msDict[scan] = [msCentre, msYbin]
#         else:
#             msDict[scan] = [msX, msY]
#     tend = time.clock()
#     logger.info("It took {:.4f} seconds to process {} scans".format((tend - tstart), len(msRange)))
#
#     # Return data
#     return msDict
