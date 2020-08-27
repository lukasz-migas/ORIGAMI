"""Post-processing of ORIGAMI-MS data"""
# Standard library imports
import logging
from typing import List

# Third-party imports
import numpy as np

LOGGER = logging.getLogger(__name__)


def _combine_scans(array: np.ndarray, start_scan: int, start_end_cv_list: List, n_voltages: int):
    """Combine scans"""
    if len(array.shape) == 2:
        return _combine_scans_heatmap(array, start_scan, start_end_cv_list, n_voltages)
    elif len(array.shape) == 1:
        return _combine_scans_chromatogram(array, start_scan, start_end_cv_list)
    else:
        raise ValueError("Not sure how to handle data")


def _combine_scans_heatmap(array: np.ndarray, start_scan: int, start_end_cv_list: List, n_voltages: int):
    """Combine scans"""
    data_cropped = array[:, start_scan::]
    array_comb_cv = []
    for _start_idx, _end_idx, _ in start_end_cv_list:
        temp_data = data_cropped[:, _start_idx:_end_idx].sum(axis=1)
        array_comb_cv = np.append(array_comb_cv, temp_data)

    # Output raw and normalized data
    array_comb_cv = array_comb_cv.reshape((200, int(n_voltages)), order="F")

    return array_comb_cv


def _combine_scans_chromatogram(array: np.ndarray, start_scan: int, start_end_cv_list: List):
    """Combine scans"""
    data_cropped = array[start_scan::]
    array_comb_cv = []
    for _start_idx, _end_idx, _ in start_end_cv_list:
        temp_data = data_cropped[_start_idx:_end_idx].sum(axis=0)
        array_comb_cv = np.append(array_comb_cv, temp_data)

    return array_comb_cv


def calculate_scan_list_linear(
    start_scan: int, start_voltage: float, end_voltage: float, step_voltage: float, scans_per_voltage: int
):
    """Calculate start/end combine parameters based on the `linear` method"""
    parameters = {
        "start_scan": start_scan,
        "start_voltage": start_voltage,
        "end_voltage": end_voltage,
        "step_voltage": step_voltage,
        "scans_per_voltage": scans_per_voltage,
        "method": "Linear",
    }
    # Calculate information about acquisition lengths
    n_voltages = int((end_voltage - start_voltage) / step_voltage) + 1

    # Pre-calculate X-axis information
    cv_list = np.linspace(start_voltage, end_voltage, num=n_voltages)

    x1 = 0
    start_end_cv_list = []
    # Create an empty array to put data into
    for _, cv in zip(list(range(n_voltages)), cv_list):
        x2 = int(x1 + scans_per_voltage)
        start_end_cv_list.append([x1 + start_scan, x2 + start_scan, cv])
        x1 = x2

    return start_end_cv_list, n_voltages, parameters


def calculate_scan_list_exponential(
    start_scan: int,
    start_voltage: float,
    end_voltage: float,
    step_voltage: float,
    scans_per_voltage: int,
    exponential_increment: float,
    exponential_percentage: float,
    exp_accumulator: int = 0,
):
    """Calculate start/end combine parameters based on the `exponential` method"""
    parameters = {
        "start_scan": start_scan,
        "start_voltage": start_voltage,
        "end_voltage": end_voltage,
        "step_voltage": step_voltage,
        "scans_per_voltage": scans_per_voltage,
        "exponential_increment": exponential_increment,
        "exponential_percentage": exponential_percentage,
        "method": "Exponential",
    }
    # Calculate how many voltages were used
    n_voltages = int((end_voltage - start_voltage) / step_voltage) + 1
    cv_list = np.linspace(start_voltage, end_voltage, num=n_voltages)
    start_scans_per_voltage = scans_per_voltage  # Used as backup

    # Generate list of SPVs first
    scans_per_voltage_list = []  # Pre-set empty array
    for i in range(int(n_voltages)):
        if cv_list[i] >= end_voltage * exponential_percentage / 100:
            exp_accumulator = exp_accumulator + exponential_increment
            scans_per_voltage_fit = np.round(start_scans_per_voltage * np.exp(exp_accumulator))
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

    return start_end_cv_list, n_voltages, parameters


def calculate_scan_list_boltzmann(
    start_scan: int,
    start_voltage: float,
    end_voltage: float,
    step_voltage: float,
    scans_per_voltage: int,
    dx: float,
    A1: int = 2,  # noqa
    A2: float = 0.07,  # noqa
    x0: int = 47,
):
    """Calculate start/end combine parameters based on the `boltzmann` method"""
    parameters = {
        "start_scan": start_scan,
        "start_voltage": start_voltage,
        "end_voltage": end_voltage,
        "step_voltage": step_voltage,
        "scans_per_voltage": scans_per_voltage,
        "A1": A1,
        "A2": A2,
        "x0": x0,
        "dx": dx,
        "method": "Boltzmann",
    }
    # Calculate how many voltages were used
    n_voltages = int((end_voltage - start_voltage) / step_voltage) + 1
    cv_list = np.linspace(start_voltage, end_voltage, num=n_voltages)
    start_scans_per_voltage = scans_per_voltage  # Used as backup

    # Generate list of SPVs first
    scans_per_voltage_list = []  # Pre-set empty array
    for i in range(int(n_voltages)):
        scans_per_voltage_fit = np.round(1 / (A2 + (A1 - A2) / (1 + np.exp((cv_list[i] - x0) / dx))))
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

    return start_end_cv_list, n_voltages, parameters


def calculate_scan_list_user_defined(start_scan, spv_cv_list):
    """Calculate list start/end scans based on the user-defined parameters"""
    parameters = {"start_scan": start_scan, "input_list": spv_cv_list, "method": "User-defined"}
    scans_per_voltage_list = spv_cv_list[:, 0]
    cv_list = spv_cv_list[:, 1]

    n_voltages = len(cv_list)
    x1 = 0
    start_end_cv_list = []
    for i, cv in zip(scans_per_voltage_list, cv_list):
        x2 = int(x1 + i)
        start_end_cv_list.append([x1 + start_scan, x2 + start_scan, cv])
        x1 = x2

    return start_end_cv_list, n_voltages, parameters


def convert_origami_ms_linear(
    array: np.ndarray,
    start_scan: int,
    start_voltage: float,
    end_voltage: float,
    step_voltage: float,
    scans_per_voltage: int,
):
    """Combine array data using linear method"""
    start_end_cv_list, n_voltages, parameters = calculate_scan_list_linear(
        start_scan, start_voltage, end_voltage, step_voltage, scans_per_voltage
    )
    array_comb_cv = _combine_scans(array, start_scan, start_end_cv_list, n_voltages)
    start_end_cv_list = np.asarray(start_end_cv_list)
    return array_comb_cv, start_end_cv_list[:, 2], start_end_cv_list, parameters


def convert_origami_ms_exponential(
    array: np.ndarray,
    start_scan: int,
    start_voltage: float,
    end_voltage: float,
    step_voltage: float,
    scans_per_voltage: int,
    exponential_increment: float,
    exponential_percentage: float,
    exp_accumulator: int = 0,
):
    """Combine array data using exponential method"""
    start_end_cv_list, n_voltages, parameters = calculate_scan_list_exponential(
        start_scan,
        start_voltage,
        end_voltage,
        step_voltage,
        scans_per_voltage,
        exponential_increment,
        exponential_percentage,
        exp_accumulator,
    )
    array_comb_cv = _combine_scans(array, start_scan, start_end_cv_list, n_voltages)
    start_end_cv_list = np.asarray(start_end_cv_list)
    return array_comb_cv, start_end_cv_list[:, 2], start_end_cv_list, parameters


def convert_origami_ms_boltzmann(
    array: np.ndarray,
    start_scan: int,
    start_voltage: float,
    end_voltage: float,
    step_voltage: float,
    scans_per_voltage: int,
    dx: float,
    A1: int = 2,  # noqa
    A2: float = 0.07,  # noqa
    x0: int = 47,
):
    """Combine array data using boltzmann method"""
    start_end_cv_list, n_voltages, parameters = calculate_scan_list_boltzmann(
        start_scan, start_voltage, end_voltage, step_voltage, scans_per_voltage, dx, A1, A2, x0
    )
    array_comb_cv = _combine_scans(array, start_scan, start_end_cv_list, n_voltages)
    start_end_cv_list = np.asarray(start_end_cv_list)
    return array_comb_cv, start_end_cv_list[:, 2], start_end_cv_list, parameters


def convert_origami_ms_user_defined(array, start_scan, input_cv_list):
    """Combine array data using user-defined method"""
    start_end_cv_list, n_voltages, parameters = calculate_scan_list_user_defined(start_scan, input_cv_list)
    array_comb_cv = _combine_scans(array, start_scan, start_end_cv_list, n_voltages)
    start_end_cv_list = np.asarray(start_end_cv_list)
    return array_comb_cv, start_end_cv_list[:, 2], start_end_cv_list, parameters


def convert_origami_ms(array, **kwargs):
    """Combine array data using any of the appropriate methods"""
    if kwargs["method"] == "Linear":
        array_comb_cv, x, start_end_cv_list, parameters = convert_origami_ms_linear(
            array,
            kwargs["start_scan"],
            kwargs["start_voltage"],
            kwargs["end_voltage"],
            kwargs["step_voltage"],
            kwargs["scans_per_voltage"],
        )
    elif kwargs["method"] == "Exponential":
        array_comb_cv, x, start_end_cv_list, parameters = convert_origami_ms_exponential(
            array,
            kwargs["start_scan"],
            kwargs["start_voltage"],
            kwargs["end_voltage"],
            kwargs["step_voltage"],
            kwargs["scans_per_voltage"],
            kwargs["exponential_increment"],
            kwargs["exponential_percentage"],
        )
    elif kwargs["method"] == "Boltzmann":
        array_comb_cv, x, start_end_cv_list, parameters = convert_origami_ms_boltzmann(
            array,
            kwargs["start_scan"],
            kwargs["start_voltage"],
            kwargs["end_voltage"],
            kwargs["step_voltage"],
            kwargs["scans_per_voltage"],
            kwargs["boltzmann_offset"],
        )
    elif kwargs["method"] == "User-defined":
        array_comb_cv, x, start_end_cv_list, parameters = convert_origami_ms_user_defined(
            array, kwargs["start_scan"], kwargs["start_scan_end_scan_cv_list"]
        )
    else:
        raise ValueError("Method not yet supported or is incorrect")

    return array_comb_cv, x, start_end_cv_list, parameters


def calculate_origami_ms(**kwargs):
    """Combine array data using any of the appropriate methods"""
    if kwargs["method"] == "Linear":
        start_end_cv_list, n_voltages, parameters = calculate_scan_list_linear(
            kwargs["start_scan"],
            kwargs["start_voltage"],
            kwargs["end_voltage"],
            kwargs["step_voltage"],
            kwargs["scans_per_voltage"],
        )
    elif kwargs["method"] == "Exponential":
        start_end_cv_list, n_voltages, parameters = calculate_scan_list_exponential(
            kwargs["start_scan"],
            kwargs["start_voltage"],
            kwargs["end_voltage"],
            kwargs["step_voltage"],
            kwargs["scans_per_voltage"],
            kwargs["exponential_increment"],
            kwargs["exponential_percentage"],
        )
    elif kwargs["method"] == "Boltzmann":
        start_end_cv_list, n_voltages, parameters = calculate_scan_list_boltzmann(
            kwargs["start_scan"],
            kwargs["start_voltage"],
            kwargs["end_voltage"],
            kwargs["step_voltage"],
            kwargs["scans_per_voltage"],
            kwargs["boltzmann_offset"],
        )
    elif kwargs["method"] == "User-defined":
        start_end_cv_list, n_voltages, parameters = calculate_scan_list_user_defined(
            kwargs["start_scan"], kwargs["start_scan_end_scan_cv_list"]
        )
    else:
        raise ValueError("Method not yet supported or is incorrect")

    return start_end_cv_list, n_voltages, parameters


def generate_extraction_windows(start_end_cv_list):
    """Generate list of extraction windows"""
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

    return scans, voltages
