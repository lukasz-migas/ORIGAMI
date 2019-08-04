# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import logging
import os
import time

import numpy as np
import pandas as pd
from readers.io_utils import remove_non_digits_from_list
from utils.color import check_color_type
from utils.color import randomColorGenerator

logger = logging.getLogger("origami")


def check_column_names(col_names):
    col_names_out = list()
    for column in col_names:
        if column.startswith("# "):
            column = column.split("# ")[1]
        elif column.startswith("# "):
            column = column.split("#")[1]
        col_names_out.append(column)

    return col_names_out


def find_column_name_in_list(allowed_names, col_names):
    for col_name in allowed_names:
        if col_name in col_names:
            break

    if col_name not in col_names:
        col_name = None

    return col_name


def get_column_data_from_row(row, column, default_value=""):
    if column is None:
        return default_value

    return row[column]


def check_file_type(path=None, fileName=None):
    """
    Simple check if the text file is likely to be MS or 2D type. Checks based
    on the length of the list. If value above 1000 rows, its unlikely to be
    a 2D datafile. Obviously this might be wrong assumption! It is checked when
    files are dropped into the main window.
    """
    # get extension
    __, extension = os.path.splitext(path)

    # read data
    if extension == ".csv":
        ms = pd.read_csv(path, header=None)
    elif extension in [".txt", ".tab"]:
        ms = pd.read_csv(path, delim_whitespace=True, header=None)

    if ms.shape[0] > 5000:
        return "MS"

    return "2D"


def prepare_heatmap_data_for_saving(zvals, xvals, yvals, guess_dtype=False):
    if yvals.shape[0] == zvals.shape[0]:
        data = np.vstack([yvals, zvals.T]).T
    elif yvals.shape[0] == zvals.shape[1]:
        data = np.vstack([yvals, zvals]).T

    # labels
    header = convert_values_to_header(xvals)

    return data, header


def convert_values_to_header(vals):
    header = list(map(str, vals))
    header.insert(0, "")

    return header


def prepare_signal_data_for_saving(xvals, yvals, xlabel, ylabel, guess_dtype=False):
    # check whether shape of the input data matches
    if xvals.shape != yvals.shape:
        raise ValueError("Incorrect shape of input data")

    data = np.vstack([xvals, yvals])

    # ensure that data is structured to have more rows than columns
    if data.shape[0] < data.shape[1]:
        data = data.T

    # generate header
    header = [xlabel, ylabel]

    return data, header


def text_infrared_open(path=None, normalize=None):
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


def text_heatmap_open(path=None, normalize=None):

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


def text_spectrum_open(path=None):

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

    if kwargs.pop("as_object", False):
        data = np.array(data, dtype=object)

    try:
        np.savetxt(filename, data, fmt=fmt, delimiter=delimiter, header=header, comments="")
    except IOError:
        logger.error(f"Failed to save file {filename} as it is currently in use.")


def text_peaklist_open(path, default_mask=0.5, default_alpha=0.5):
    """Open peaklist file

    Parameters
    ----------
    path : str

    Returns
    -------
    peaklist_list : list
        list of dictionaries that will be used to append to the peaklist panel
    """
    # read data
    peaklist = pd.read_csv(path, sep="\t|,", engine="python")
    peaklist = peaklist.fillna("")

    # get columns - check if there is # in the first item in column
    columns = check_column_names(peaklist.columns.values.tolist())
    peaklist.columns = columns

    # retrieve column idx
    ion_name_col = find_column_name_in_list(["ion_name", "ion", "name"], columns)
    mz_start_col = find_column_name_in_list(["min", "min m/z", "mz_start"], columns)
    mz_end_col = find_column_name_in_list(["max", "max m/z", "mz_end"], columns)
    intensity_col = find_column_name_in_list(["intensity"], columns)
    charge_col = find_column_name_in_list(["z", "charge"], columns)
    label_col = find_column_name_in_list(["label", "information"], columns)
    color_col = find_column_name_in_list(["color", "colour"], columns)
    colormap_col = find_column_name_in_list(["colormap"], columns)
    alpha_col = find_column_name_in_list(["alpha", "transparency"], columns)
    mask_col = find_column_name_in_list(["mask"], columns)

    # ensure minimal number of columns is present
    peaklist_list = []
    if mz_start_col is None or mz_end_col is None:
        logger.error("Missing essential column(s): 'mz_start' and/or 'mz_end'")
        return peaklist_list

    # iterate over each to generate dictionary
    for __, row in peaklist.iterrows():
        ion_name = get_column_data_from_row(row, ion_name_col)
        mz_start = get_column_data_from_row(row, mz_start_col)
        mz_end = get_column_data_from_row(row, mz_end_col)
        charge = get_column_data_from_row(row, charge_col, 1)
        intensity = get_column_data_from_row(row, intensity_col, 1.0)
        label = get_column_data_from_row(row, label_col)
        color = get_column_data_from_row(row, color_col, randomColorGenerator())
        colormap = get_column_data_from_row(row, colormap_col)
        alpha = get_column_data_from_row(row, alpha_col, default_alpha)
        mask = get_column_data_from_row(row, mask_col, default_mask)

        document_title = ""

        # check ion name
        if ion_name in ["", None]:
            ion_name = f"{mz_start}-{mz_end}"

        # check color
        color = check_color_type(color)
        add_dict = {
            "ion_name": ion_name,
            "mz_start": mz_start,
            "mz_end": mz_end,
            "charge": charge,
            "mz_ymax": intensity,
            "color": color,
            "colormap": colormap,
            "alpha": alpha,
            "mask": mask,
            "label": label,
            "document": document_title,
        }
        peaklist_list.append(add_dict)

    return peaklist_list
