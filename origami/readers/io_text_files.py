# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import logging
import os
import time

import numpy as np
import pandas as pd
from readers.io_utils import remove_non_digits_from_list
from utils.color import check_color_type
from utils.color import convert_hex_to_rgb_1
from utils.color import get_n_colors
from utils.color import get_random_color
from utils.labels import _replace_labels
from utils.visuals import check_n_grid_dimensions

logger = logging.getLogger(__name__)

dtype_dict = {np.int32: "%d", np.float16: "%.3f", np.float32: "%.6f", np.float64: "%.8f"}


class AnnotatedDataReader:

    # TODO: add seaborn colors rather than randoms
    def __init__(self, filename):
        self.filename = filename
        self.title = self._parse_title()
        self._data = self._load_dataframe()
        self.dataset_title, self.data = self._parse_data(self._data)

    def _load_dataframe(self):
        if self.filename.endswith(".csv"):
            df = pd.read_csv(self.filename, sep=",", engine="python", header=None)
        elif self.filename.endswith(".txt"):
            df = pd.read_csv(self.filename, sep="\t", engine="python", header=None)

        return df

    def _parse_title(self):
        title = os.path.basename(self.filename)
        return title

    def _parse_data(self, df):

        plot_type = "multi-line"
        plot_modifiers = {}
        if "title" in list(df.iloc[:, 0]):
            idx = list(df.iloc[:, 0]).index("title")
            title = list(df.iloc[idx, 1::])[0]

        row_labels = list(df.iloc[:, 0])
        if "plot_type" in row_labels:
            idx = row_labels.index("plot_type")
            plot_type = list(df.iloc[idx, 1::])[0]

        x_label = ""
        if "x_label" in row_labels:
            idx = row_labels.index("x_label")
            x_label = list(df.iloc[idx, 1::])[0]

        y_label = ""
        if "y_label" in row_labels:
            idx = row_labels.index("y_label")
            y_label = list(df.iloc[idx, 1::])[0]

        x_unit = ""
        if "x_unit" in row_labels:
            idx = row_labels.index("x_unit")
            x_unit = list(df.iloc[idx, 1::])[0]

        y_unit = ""
        if "y_unit" in row_labels:
            idx = row_labels.index("y_unit")
            y_unit = list(df.iloc[idx, 1::])[0]

        order = []
        if "order" in row_labels:
            idx = row_labels.index("order")
            order = list(df.iloc[idx, 1::])

        labels = []
        if "label" in row_labels:
            idx = row_labels.index("label")
            labels = list(df.iloc[idx, 1::].dropna())
        elif "labels" in row_labels:
            idx = row_labels.index("labels")
            labels = list(df.iloc[idx, 1::].dropna())

        x_labels = []
        if "x_labels" in row_labels:
            idx = row_labels.index("x_labels")
            x_labels = list(df.iloc[idx, 1::].dropna())

        y_labels = []
        if "y_labels" in row_labels:
            idx = row_labels.index("y_labels")
            y_labels = list(df.iloc[idx, 1::].dropna())

        xlimits = [None, None]
        if "xlimits" in row_labels:
            idx = row_labels.index("xlimits")
            xlimits = list(df.iloc[idx, 1:3].dropna().astype("float32"))

        ylimits = [None, None]
        if "ylimits" in row_labels:
            idx = row_labels.index("ylimits")
            ylimits = list(df.iloc[idx, 1:3].dropna().astype("float32"))

        colors = []
        if "color" in row_labels:
            idx = row_labels.index("color")
            colors = list(df.iloc[idx, 1::].dropna())
        elif "colors" in row_labels:
            idx = row_labels.index("colors")
            colors = list(df.iloc[idx, 1::].dropna())

        column_types = []
        if "column_type" in row_labels:
            idx = row_labels.index("column_type")
            column_types = list(df.iloc[idx, 1::].dropna())

        legend_labels = []
        if "legend_labels" in row_labels:
            idx = row_labels.index("legend_labels")
            legend_labels = list(df.iloc[idx, 1::].dropna())

        legend_colors = []
        if "legend_colors" in row_labels:
            idx = row_labels.index("legend_colors")
            legend_colors = list(df.iloc[idx, 1::].dropna())

        hover_labels = []
        if "hover_labels" in row_labels:
            idx = row_labels.index("hover_labels")
            hover_labels = list(df.iloc[idx, 1::].dropna())

        plot_modifiers.update(
            legend_labels=legend_labels, legend_colors=legend_colors, xlimits=xlimits, ylimits=ylimits
        )
        xvals, yvals, zvals, xvalsErr, yvalsErr, itemColors, itemLabels = [], [], [], [], [], [], []
        xyvals, urls = [], []
        axis_y_min, axis_y_max, axis_note = [], [], []
        xy_labels = []

        # get first index
        first_num_idx = pd.to_numeric(df.iloc[:, 0], errors="coerce").notnull().idxmax()

        # check if axis labels have been provided
        for xy_axis in [
            "axis_x",
            "axis_y",
            "axis_xerr",
            "axis_yerr",
            "axis_color",
            "axis_colors",
            "axis_label",
            "axis_labels",
            "axis_y_min",
            "axis_y_max",
            "axis_xy",
            "axis_url",
        ]:
            if xy_axis in row_labels:
                idx = row_labels.index(xy_axis)
                xy_labels = list(df.iloc[idx, :])

        if len(xy_labels) == df.shape[1]:
            df = df.iloc[first_num_idx:, :]
            for i, xy_label in enumerate(xy_labels):
                if xy_label == "axis_x":
                    xvals.append(np.asarray(df.iloc[:, i].dropna().astype("float32")))
                if xy_label == "axis_y":
                    yvals.append(np.asarray(df.iloc[:, i].dropna().astype("float32")))
                if xy_label == "axis_xerr":
                    xvalsErr.append(np.asarray(df.iloc[:, i].dropna().astype("float32")))
                if xy_label == "axis_yerr":
                    yvalsErr.append(np.asarray(df.iloc[:, i].dropna().astype("float32")))
                if xy_label == "axis_y_min":
                    axis_y_min.append(np.asarray(df.iloc[:, i].dropna().astype("float32")))
                if xy_label == "axis_y_max":
                    axis_y_max.append(np.asarray(df.iloc[:, i].dropna().astype("float32")))
                if xy_label in ["axis_xy", "axis_yx"]:
                    xyvals.append(np.asarray(df.iloc[:, i].dropna().astype("float32")))
                if xy_label in ["axis_color", "axis_colors"]:
                    _colors = list(df.iloc[:, i].dropna().astype("str"))
                    _colorsRGB = []
                    for _color in _colors:
                        _colorsRGB.append(convert_hex_to_rgb_1(str(_color)))
                    itemColors.append(_colorsRGB)
                    plot_modifiers["color_items"] = True
                if xy_label in ["axis_label", "axis_labels"]:
                    itemLabels.append(list(df.iloc[:, i].replace(np.nan, "", regex=True).astype("str")))
                    plot_modifiers["label_items"] = True
                if xy_label == "axis_note":
                    axis_note.append(np.asarray(df.iloc[:, i].replace(np.nan, "", regex=True).astype("str")))
                if xy_label == "axis_url":
                    urls.append(np.asarray(df.iloc[:, i].astype("str")))
        else:
            # drop all other non-numeric rows
            df = df[pd.to_numeric(df.iloc[:, 0], errors="coerce").notnull()]
            df = df.astype("float32")

            # extract x, y and zvals
            if df.shape[1] >= 2:
                xvals = list(df.iloc[:, 0])
            else:
                return None, None

            if df.shape[1] == 2:
                yvals = list(df.iloc[:, 1])

            if df.shape[1] > 2:
                zvals = df.iloc[:, 1::].as_matrix()

            if plot_type in ["multi-line", "waterfall", "scatter", "grid-line", "grid-scatter"]:
                yvals_new = []
                for item in range(zvals.shape[1]):
                    yvals_new.append(zvals[:, item])

                # replace
                xvals = [xvals]
                yvals = yvals_new
                zvals = []
                if len(labels) != len(yvals):
                    labels = [""] * len(yvals)

        # create combination of x y columns
        if len(xyvals) > 0:
            from itertools import product

            xyproduct = list(product(xyvals, xyvals))
            xvals, yvals = [], []
            for iprod in xyproduct:
                xvals.append(iprod[0])
                yvals.append(iprod[1])
            if len(x_labels) == len(xyvals) and len(y_labels) == len(xyvals):
                xyproduct = list(product(x_labels, y_labels))
                x_labels, y_labels = [], []
                for iprod in xyproduct:
                    x_labels.append(iprod[0])
                    y_labels.append(iprod[1])

        if plot_type in ["grid-line", "grid-scatter", "grid-mixed"]:
            n_xvals = len(xvals)
            n_yvals = len(yvals)
            n_grid = max([n_xvals, n_yvals])
            n_rows, n_cols, __, __ = check_n_grid_dimensions(n_grid)
            plot_modifiers.update(n_grid=n_grid, n_rows=n_rows, n_cols=n_cols)

        # check if we need to add any metadata
        if len(colors) == 0 or len(colors) < len(yvals):
            colors = get_n_colors(len(yvals))

        if len(labels) != len(yvals):
            labels = [""] * len(yvals)

        # update title
        _plot_types = {
            "multi-line": "Multi-line",
            "scatter": "Scatter",
            "line": "Line",
            "waterfall": "Waterfall",
            "grid-line": "Grid-line",
            "grid-scatter": "Grid-scatter",
            "vertical-bar": "V-bar",
            "horizontal-bar": "H-bar",
        }

        title = "{}: {}".format(_plot_types[plot_type], title)
        other_data = {
            "plot_type": plot_type,
            "xvals": xvals,
            "yvals": yvals,
            "zvals": zvals,
            "xvalsErr": xvalsErr,
            "yvalsErr": yvalsErr,
            "yvals_min": axis_y_min,
            "yvals_max": axis_y_max,
            "itemColors": itemColors,
            "itemLabels": itemLabels,
            "xlabel": _replace_labels(x_label),
            "ylabel": _replace_labels(y_label),
            "xlimits": xlimits,
            "ylimits": ylimits,
            "xlabels": x_labels,
            "ylabels": y_labels,
            "hover_labels": hover_labels,
            "x_unit": x_unit,
            "y_unit": y_unit,
            "colors": colors,
            "labels": labels,
            "urls": urls,
            "column_types": column_types,
            "column_order": order,
            "path": self.filename,
            "plot_modifiers": plot_modifiers,
        }

        msg = "Item {} has: x-columns ({}), x-errors ({}), y-columns ({}), x-errors ({}), ".format(
            os.path.basename(self.filename), len(xvals), len(xvalsErr), len(yvals), len(yvalsErr)
        ) + "labels ({}), colors ({})".format(len(labels), len(colors))
        logger.info(msg)

        return title, other_data


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


def _get_dtype_type(arr_or_dtype):
    """Get the type (NOT dtype) instance associated with an array or dtype object.

    Parameters
    ----------
    arr_or_dtype : array-like
        The array-like or dtype object whose type we want to extract.

    Returns
    -------
    obj_type : The extract type instance from the
               passed in array or dtype object.
    """

    if isinstance(arr_or_dtype, np.dtype):
        return arr_or_dtype.type
    elif isinstance(arr_or_dtype, type):
        return np.dtype(arr_or_dtype).type

    try:
        return arr_or_dtype.dtype.type
    except AttributeError:
        return type(None)


def _get_n_columns(data):
    shape = data.shape
    if len(shape) == 1:
        return 1
    else:
        return shape[1]


def get_column_dtypes(data):
    if not isinstance(data, np.ndarray):
        data = np.asarray(data)

    dtype = _get_dtype_type(data)
    n_columns = _get_n_columns(data)

    return [dtype_dict.get(dtype, "%.4f")] * n_columns


def convert_values_to_header(vals):
    header = list(map(str, vals))
    header.insert(0, "")

    return header


def prepare_heatmap_data_for_saving(zvals, xvals, yvals, guess_dtype=False):
    # get dtype
    fmt = []
    fmt.extend(get_column_dtypes(yvals))
    fmt.extend(get_column_dtypes(zvals))

    if yvals.shape[0] == zvals.shape[0]:
        data = np.vstack([yvals, zvals.T]).T
    elif yvals.shape[0] == zvals.shape[1]:
        data = np.vstack([yvals, zvals]).T

    # labels
    header = convert_values_to_header(xvals)

    return data, header, fmt


def prepare_signal_data_for_saving(xvals, yvals, xlabel, ylabel, guess_dtype=False):
    # get dtype
    fmt = []
    fmt.extend(get_column_dtypes(xvals))
    fmt.extend(get_column_dtypes(yvals))

    # check whether shape of the input data matches
    xvals = np.asarray(xvals)
    yvals = np.asarray(yvals)

    if xvals.shape != yvals.shape:
        raise ValueError("Incorrect shape of input data")

    data = np.vstack([xvals, yvals])

    # ensure that data is structured to have more rows than columns
    if data.shape[0] < data.shape[1]:
        data = data.T

    # generate header
    header = [xlabel, ylabel]

    return data, header, fmt


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

    logger.info(
        "Labels size: {} x {} Array size: {} x {}".format(len(xvals), len(yvals), len(zvals[0, :]), len(zvals[:, 0]))
    )

    if normalize:
        zvals_norm = normalize(zvals, axis=0, norm="max")  # Norm to 1
        return zvals, zvals_norm, xvals, yvals

    return zvals, xvals, yvals


def text_spectrum_open(path=None):

    # get extension
    __, extension = os.path.splitext(path)
    dirname = os.path.dirname(path)

    # read data
    if extension == ".csv":
        ms = pd.read_csv(path, header=None)
    elif extension in [".txt", ".tab"]:
        ms = pd.read_csv(path, delim_whitespace=True, header=None)

    # check if first row is numerical
    if ms.loc[0, :].dtype != "float64":
        logger.info(
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
        logger.info(
            "MS file has more than two columns. In future each row will be combined into one MS and"
            + " additional container will be created for multiple MS"
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

    Parameters
    ----------
    filename : str
        path to where file should be saved
    data : list, np.array
        data to be saved
    header : str

    """
    # transpose data
    if kwargs.pop("transpose", False):
        data = np.transpose(data)

    # force object dtype
    if kwargs.pop("as_object", False):
        data = np.array(data, dtype=object)

    # check whether data is array
    if not isinstance(data, np.ndarray):
        data = np.asarray(data)

    # check whether fmt and data are of same size
    if isinstance(fmt, list):
        if data.shape[1] != len(fmt):
            logger.warning(
                "Number of columns does not match number of items in the `fmt` keyword." + " Using default instead"
            )
            fmt = "%.4f"

    try:
        np.savetxt(filename, data, fmt=fmt, delimiter=delimiter, header=header)
    except IOError:
        logger.error(f"Failed to save file {filename} as it is currently in use.")


# TODO: replace this function with save_text
def saveAsText(filename, data, format="%.2f", delimiter=",", header=""):
    """
    This function uses np.savetxt to save formatted data to file
    """

    try:
        np.savetxt(filename, np.transpose(data), fmt=format, delimiter=delimiter, header=header)
    except IOError:
        print("".join(["Cannot save file: '", filename, "' as it is currently open."]))
        return
    print("".join(["Saved: ", filename]))


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
        color = get_column_data_from_row(row, color_col, get_random_color())
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


def text_annotations_open():
    pass
    # def on_load_peaklist(self, evt):
    #     """
    #     This function opens a formatted CSV file with peaks
    #     """
    #     # TODO: Move to data handling
    #     raise MessageError("Function was removed", "Need to re-implement this...")

    #         dlg = wx.FileDialog(
    #             self,
    #             "Choose a text file (m/z, window size, charge):",
    #             wildcard="*.csv;*.txt",
    #             style=wx.FD_DEFAULT_STYLE | wx.FD_CHANGE_DIR,
    #         )
    #         if dlg.ShowModal() == wx.ID_CANCEL:
    #             return
    #         else:
    #
    #             # Create shortcut
    #             delimiter, __ = checkExtension(input=dlg.GetPath().encode("ascii", "replace"))
    #             peaklist = read_csv(dlg.GetPath(), delimiter=delimiter)
    #             peaklist = peaklist.fillna("")
    #
    #             columns = peaklist.columns.values.tolist()
    #             for min_name in ["min", "min m/z"]:
    #                 if min_name in columns:
    #                     break
    #                 else:
    #                     continue
    #             if min_name not in columns:
    #                 min_name = None
    #
    #             for max_name in ["max", "max m/z"]:
    #                 if max_name in columns:
    #                     break
    #                 else:
    #                     continue
    #             if max_name not in columns:
    #                 max_name = None
    #
    #             for position_name in ["position"]:
    #                 if position_name in columns:
    #                     break
    #                 else:
    #                     continue
    #             if position_name not in columns:
    #                 position_name = None
    #
    #             for charge_name in ["z", "charge"]:
    #                 if charge_name in columns:
    #                     break
    #                 else:
    #                     continue
    #             if charge_name not in columns:
    #                 charge_name = None
    #
    #             for label_name in ["label", "information"]:
    #                 if label_name in columns:
    #                     break
    #                 else:
    #                     continue
    #             if label_name not in columns:
    #                 label_name = None
    #
    #             for color_name in ["color", "colour"]:
    #                 if color_name in columns:
    #                     break
    #                 else:
    #                     continue
    #             if color_name not in columns:
    #                 color_name = None
    #
    #             for intensity_name in ["intensity"]:
    #                 if intensity_name in columns:
    #                     break
    #                 else:
    #                     continue
    #             if intensity_name not in columns:
    #                 intensity_name = None
    #
    #             if min_name is None or max_name is None:
    #                 return
    #
    #             # iterate
    #             color_value = str(convert_rgb_255_to_1(self.patch_color_btn.GetBackgroundColour()))
    #             arrow = False
    #             for peak in range(len(peaklist)):
    #                 min_value = peaklist[min_name][peak]
    #                 max_value = peaklist[max_name][peak]
    #                 if position_name is not None:
    #                     position = peaklist[position_name][peak]
    #                 else:
    #                     position = max_value - ((max_value - min_value) / 2)
    #
    #                 in_table, __ = self.checkDuplicate(min_value, max_value)
    #
    #                 if in_table:
    #                     continue
    #
    #                 if intensity_name is not None:
    #                     intensity = peaklist[intensity_name][peak]
    #                 else:
    #                     intensity = np.round(
    #                         pr_utils.find_peak_maximum(
    #                             pr_utils.get_narrow_data_range(data=self.data, mzRange=[min_value, max_value]),
    #                             fail_value=0.0,
    #                         ),
    #                         2,
    #                     )
    #                 if charge_name is not None:
    #                     charge_value = peaklist[charge_name][peak]
    #                 else:
    #                     charge_value = ""
    #
    #                 if label_name is not None:
    #                     label_value = peaklist[label_name][peak]
    #                 else:
    #                     label_value = ""
    #
    #                 self.peaklist.Append(
    #                     [
    #                         "",
    #                         str(min_value),
    #                         str(max_value),
    #                         str(position),
    #                         str(intensity),
    #                         str(charge_value),
    #                         str(label_value),
    #                         str(color_value),
    #                         str(arrow),
    #                     ]
    #                 )
    #
    #                 annotation_dict = {
    #                     "min": min_value,
    #                     "max": max_value,
    #                     "charge": charge_value,
    #                     "intensity": intensity,
    #                     "label": label_value,
    #                     "color": literal_eval(color_value),
    #                     "isotopic_x": position,
    #                     "isotopic_y": intensity,
    #                 }
    #
    #                 name = "{} - {}".format(min_value, max_value)
    #                 self.kwargs["annotations"][name] = annotation_dict
    #
    #             self.documentTree.on_update_annotation(
    #                 self.kwargs["annotations"], self.kwargs["document"], self.kwargs["dataset"]
    #             )
    #
    #             dlg.Destroy()
