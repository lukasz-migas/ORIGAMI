# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
# Standard library imports
# Standard library imports
# Standard library imports
import logging
from operator import itemgetter
from itertools import groupby

# Third-party imports
import numpy as np

logger = logging.getLogger(__name__)


def origami_combine_infrared(inputData=None, threshold=2000, noiseLevel=500, sigma=0.5):  # combineIRdata
    # TODO: This function needs work - Got to acquire more data to test it properly
    # Create empty lists
    dataList, indexList = [], []
    # Iterate and extract values that are below the IR threshold
    for x in range(len(inputData[1, :])):
        if np.sum(inputData[:, x]) > threshold:
            dataList.append(inputData[:, x])
            indexList.append(x)

    # Split the indexList so we have a list of lists of indexes to split data into
    splitlist = [list(map(itemgetter(1), g)) for _, g in groupby(enumerate(indexList), lambda i_x: i_x[0] - i_x[1])]

    # Split data
    dataSplit = []
    for i in splitlist:
        dataSlice = inputData[:, i[0] : i[-1]]
        dataSliceSum = np.sum(dataSlice, axis=1)
        dataSplit.append(dataSliceSum)

    dataSplitArray = np.array(dataSplit)
    dataSplitArray = dataSplitArray[1:, :]  # Remove first row as it has a lot of intensity
    dataSplitArray[dataSplitArray <= noiseLevel] = 0  # Remove noise

    dataSplitArray = np.flipud(np.rot90(dataSplitArray))  # rotate
    # Convert the 2D array to 1D list too
    dataRT = np.sum(dataSplitArray, axis=0)
    data1DT = np.sum(dataSplitArray, axis=1)

    # Simulate x-axis values
    yvals = 1 + np.arange(len(dataSplitArray))
    xvals = 1 + np.arange(len(dataSplitArray[1, :]))

    # Return array
    return dataSplitArray, xvals, yvals, dataRT, data1DT


def calculate_scan_list_linear(start_scan, start_voltage, end_voltage, step_voltage, scans_per_voltage):
    # Calculate information about acquisition lengths
    n_voltages = int((end_voltage - start_voltage) / step_voltage) + 1

    # Pre-calculate X-axis information
    cv_list = np.linspace(start_voltage, end_voltage, num=n_voltages)

    x1 = 0
    start_end_cv_list = []
    # Create an empty array to put data into
    for _, cv in zip(list(range(int(n_voltages))), cv_list):
        x2 = int(x1 + scans_per_voltage)
        start_end_cv_list.append([x1 + start_scan, x2 + start_scan, cv])
        x1 = x2

    return start_end_cv_list


def calculate_scan_list_exponential(
    start_scan,
    start_voltage,
    end_voltage,
    step_voltage,
    scans_per_voltage,
    exponential_increment,
    exponential_percentage,
    expAccumulator=0,
):
    # Calculate how many voltages were used
    n_voltages = int((end_voltage - start_voltage) / step_voltage) + 1
    cv_list = np.linspace(start_voltage, end_voltage, num=n_voltages)
    start_scans_per_voltage = scans_per_voltage  # Used as backup

    # Generate list of SPVs first
    scans_per_voltage_list = []  # Pre-set empty array
    for i in range(int(n_voltages)):
        if cv_list[i] >= end_voltage * exponential_percentage / 100:
            expAccumulator = expAccumulator + exponential_increment
            scans_per_voltage_fit = np.round(start_scans_per_voltage * np.exp(expAccumulator), 0)
        else:
            scans_per_voltage_fit = start_scans_per_voltage
        # Create a list with SPV counter
        scans_per_voltage_list.append(scans_per_voltage_fit)

    x1 = 0
    start_end_cv_list = []
    for i, cv in zip(scans_per_voltage_list, cv_list):
        x2 = int(x1 + i)
        start_end_cv_list.append([x1 + start_scan, x2 + start_scan, cv])
        x1 = x2  # set new starting index

    return start_end_cv_list


def calculate_scan_list_boltzmann(
    start_scan, start_voltage, end_voltage, step_voltage, scans_per_voltage, dx, A1=2, A2=0.07, x0=47
):

    # Calculate how many voltages were used
    n_voltages = ((end_voltage - start_voltage) / step_voltage) + 1
    cv_list = np.linspace(start_voltage, end_voltage, num=n_voltages)
    start_scans_per_voltage = scans_per_voltage  # Used as backup

    # Generate list of SPVs first
    scans_per_voltage_list = []  # Pre-set empty array
    for i in range(int(n_voltages)):
        scans_per_voltage_fit = np.round(1 / (A2 + (A1 - A2) / (1 + np.exp((cv_list[i] - x0) / dx))), 0)
        if scans_per_voltage_fit == 0:
            scans_per_voltage_fit = 1
        # Append to file
        scans_per_voltage_list.append(scans_per_voltage_fit * start_scans_per_voltage)

    x1 = 0
    start_end_cv_list = []
    for i, cv in zip(scans_per_voltage_list, cv_list):
        x2 = int(x1 + i)
        start_end_cv_list.append([x1 + start_scan, x2 + start_scan, cv])
        x1 = x2

    return start_end_cv_list


def calculate_scan_list_user_defined(start_scan, spv_cv_list):

    scans_per_voltage_list = spv_cv_list[:, 0]
    cv_list = spv_cv_list[:, 1]

    x1 = 0
    start_end_cv_list = []
    for i, cv in zip(scans_per_voltage_list, cv_list):
        x2 = int(x1 + i)
        start_end_cv_list.append([x1 + start_scan, x2 + start_scan, cv])
        x1 = x2

    return start_end_cv_list


def origami_combine_linear(data, start_scan, start_voltage, end_voltage, step_voltage, scans_per_voltage):
    # Build dictionary with parameters
    parameters = {
        "start_scan": start_scan,
        "startV": start_voltage,
        "endV": end_voltage,
        "stepV": step_voltage,
        "spv": scans_per_voltage,
        "method": "Linear",
    }

    # Calculate information about acquisition lengths
    n_voltages = ((end_voltage - start_voltage) / step_voltage) + 1
    end_scan = int(start_scan + (scans_per_voltage * n_voltages))
    if end_scan > data.shape[1]:
        return [None, end_scan, len(data[1, :])], None, None

    logger.info(
        f"File has a total of {data.shape[1]} scans. Scans {start_scan}-{end_scan} will be used for CV accumulation"
    )

    # Pre-calculate X-axis information
    cv_list = np.linspace(start_voltage, end_voltage, num=n_voltages)
    # Crop IMS data to appropriate size (remove start and end regions 'reporter')
    data_cropped = data[:, int(start_scan) : :]

    x1 = 0
    # Create an empty array to put data into
    data_combined_CV, start_end_cv_list = [], []
    for _, cv in zip(list(range(int(n_voltages))), cv_list):
        x2 = int(x1 + scans_per_voltage)
        start_end_cv_list.append([x1 + start_scan, x2 + start_scan, cv])
        temp_data = data_cropped[:, x1:x2]
        temp_data = np.sum(temp_data, axis=1)  # Combine all into one array
        x1 = x2
        data_combined_CV = np.append(data_combined_CV, temp_data)  # Create a new array containing all IMS data

    # Output raw and normalized data
    data_combined_CV = data_combined_CV.reshape((200, int(n_voltages)), order="F")  # Reshape list to array
    return data_combined_CV, start_end_cv_list, parameters


def origami_combine_exponential(
    data,
    start_scan,  # combineCEscansExponential
    start_voltage,
    end_voltage,
    step_voltage,
    scans_per_voltage,
    exponential_increment,
    exponential_percentage,
    expAccumulator=0,
    verbose=False,
):
    # Build dictionary with parameters
    parameters = {
        "start_scan": start_scan,
        "startV": start_voltage,
        "endV": end_voltage,
        "stepV": step_voltage,
        "spv": scans_per_voltage,
        "exponential_increment": exponential_increment,
        "expPercent": exponential_percentage,
        "method": "Exponential",
    }

    # Calculate how many voltages were used
    n_voltages = ((end_voltage - start_voltage) / step_voltage) + 1
    cv_list = np.linspace(start_voltage, end_voltage, num=n_voltages)
    start_scans_per_voltage = scans_per_voltage  # Used as backup

    # Generate list of SPVs first
    scans_per_voltage_list = []  # Pre-set empty array
    for i in range(int(n_voltages)):
        # Prepare list
        if cv_list[i] >= end_voltage * exponential_percentage / 100:
            expAccumulator = expAccumulator + exponential_increment
            scans_per_voltage_fit = np.round(start_scans_per_voltage * np.exp(expAccumulator), 0)
        else:
            scans_per_voltage_fit = start_scans_per_voltage
        # Create a list with SPV counter
        scans_per_voltage_list.append(scans_per_voltage_fit)
    end_scan = start_scan + (sum(scans_per_voltage_list))
    if end_scan > len(data[1, :]):
        return [None, end_scan, len(data[1, :])], None, None

    logger.info(
        f"File has a total of {data.shape[1]} scans. Scans {start_scan}-{end_scan} will be used for CV accumulation"
    )

    # Crop IMS data to appropriate size (remove start and end regions 'reporter')
    data_cropped = data[:, int(start_scan) : :]  # int(end_scan)]
    x1 = 0
    data_combined_CV, start_end_cv_list = [], []
    for i, cv in zip(scans_per_voltage_list, cv_list):
        x2 = int(x1 + i)
        start_end_cv_list.append([x1 + start_scan, x2 + start_scan, cv])
        temp_data = data_cropped[:, x1:x2]  # Crop appropriate range
        temp_data = np.sum(temp_data, axis=1)  # Combine all into one array
        # Combine data into a list that will be reshaped afterwards
        data_combined_CV = np.append(data_combined_CV, temp_data)  # Create a new array containing all IMS data
        x1 = x2  # set new starting index
    # Output raw and normalized data
    data_combined_CV = data_combined_CV.reshape((200, int(n_voltages)), order="F")  # Reshape list to array
    return data_combined_CV, start_end_cv_list, parameters


def origami_combine_boltzmann(
    data,
    start_scan,  # combineCEscansFitted
    start_voltage,
    end_voltage,
    step_voltage,
    scans_per_voltage,
    expIncrement,
    verbose=False,
    A1=2,
    A2=0.07,
    x0=47,
    dx=None,
):

    # Build dictionary with parameters
    parameters = {
        "start_scan": start_scan,
        "startV": start_voltage,
        "endV": end_voltage,
        "stepV": step_voltage,
        "spv": scans_per_voltage,
        "A1": A1,
        "A2": A2,
        "x0": x0,
        "dx": dx,
        "method": "Fitted",
    }

    # Calculate how many voltages were used
    n_voltages = ((end_voltage - start_voltage) / step_voltage) + 1
    cv_list = np.linspace(start_voltage, end_voltage, num=n_voltages)
    start_scans_per_voltage = scans_per_voltage  # Used as backup
    # Generate list of SPVs first
    scans_per_voltage_list = []  # Pre-set empty array
    for i in range(int(n_voltages)):
        scans_per_voltage_fit = np.round(1 / (A2 + (A1 - A2) / (1 + np.exp((cv_list[i] - x0) / dx))), 0)
        #         if scans_per_voltage_fit == 0:
        #             scans_per_voltage_fit = 1
        # Append to file
        scans_per_voltage_list.append(scans_per_voltage_fit * start_scans_per_voltage)

    # Calculate last voltage
    end_scan = start_scan + (sum(scans_per_voltage_list))
    if end_scan > len(data[1, :]):
        return [None, end_scan, len(data[1, :])], None, None

    logger.info(
        f"File has a total of {data.shape[1]} scans. Scans {start_scan}-{end_scan} will be used for CV accumulation"
    )
    # Crop IMS data to appropriate size (remove start and end regions 'reporter')
    data_cropped = data[:, int(start_scan) : :]  # int(end_scan)]
    x1 = 0
    data_combined_CV, start_end_cv_list = [], []
    for i, cv in zip(scans_per_voltage_list, cv_list):
        x2 = int(x1 + i)
        start_end_cv_list.append([x1 + start_scan, x2 + start_scan, cv])
        temp_data = data_cropped[:, x1:x2]  # Crop appropriate range
        temp_data = np.sum(temp_data, axis=1)  # Combine all into one array
        # Combine data into a list that will be reshaped afterwards
        data_combined_CV = np.append(data_combined_CV, temp_data)  # Create a new array containing all IMS data
        x1 = x2
    # Output raw and normalized data
    data_combined_CV = data_combined_CV.reshape((200, int(n_voltages)), order="F")  # Reshape list to array
    return data_combined_CV, start_end_cv_list, parameters


def origami_combine_userDefined(data=None, start_scan=None, inputList=None):  # combineCEscansUserDefined

    # Build dictionary with parameters
    parameters = {"start_scan": start_scan, "inputList": inputList, "method": "User-defined"}

    # Pre-calculate lists
    scans_per_voltage_list = inputList[:, 0]
    cv_list = inputList[:, 1]

    # Make sure that list is of correct shape
    if len(cv_list) != len(scans_per_voltage_list):
        return

    # Calculate information about acquisition lengths
    end_scan = start_scan + sum(scans_per_voltage_list)

    if end_scan > len(data[1, :]):
        return [None, end_scan, len(data[1, :])], None, None, None

    logger.info(
        f"File has a total of {data.shape[1]} scans. Scans {start_scan}-{end_scan} will be used for CV accumulation"
    )
    # Crop IMS data to appropriate size (remove start and end regions 'reporter')
    data_cropped = data[:, int(start_scan) : :]
    x1 = int(0)
    # Create an empty array to put data into
    data_combined_CV, start_end_cv_list = [], []
    for i, cv in zip(scans_per_voltage_list, cv_list):
        x2 = int(x1 + i)  # index 2
        start_end_cv_list.append([x1 + start_scan, x2 + start_scan, cv, (x2 - x1)])
        temp_data = data_cropped[:, x1:x2]  # Crop appropriate range
        temp_data = np.sum(temp_data, axis=1)  # Combine all into one array
        data_combined_CV = np.append(data_combined_CV, temp_data)  # Create a new array containing all IMS data
        x1 = x2
    data_combined_CV = data_combined_CV.reshape((200, len(scans_per_voltage_list)), order="F")  # Reshape list to array
    return data_combined_CV, cv_list, start_end_cv_list, parameters


def generate_extraction_windows(start_end_cv_list):
    start_end_cv_list = np.asarray(start_end_cv_list)

    start_scan = start_end_cv_list[:, 0]
    end_scan = start_end_cv_list[:, 1]
    cv_list = start_end_cv_list[:, 2]

    scans, voltages = [], []
    for i, cv in enumerate(cv_list):
        scans.append(start_scan[i])
        scans.append(end_scan[i])

        voltages.append(cv)
        voltages.append(cv)

    #     print(scans, voltages)

    return scans, voltages
