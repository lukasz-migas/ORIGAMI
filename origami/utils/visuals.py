# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import numpy as np
from utils.check import isbool
from utils.converters import str2int
from utils.converters import str2num


def prettify_tick_format(tick_labels):
    increment = 1000

    def compute_divider(value):
        divider = 1000000000
        while value == value % divider:
            divider = divider / increment
        return len(str(int(divider))) - len(str(int(divider)).rstrip("0"))

    def convert_divider_to_str(value, exp_value):
        if exp_value in [0, 1, 2]:
            return value
        elif exp_value in [3, 4, 5]:
            return f"{value / 1000:.1f}k"
        elif exp_value == [6, 7, 8]:
            return f"{value / 1000000:.0f}k"

    _tick_labels = []
    for value in tick_labels:
        _tick_labels.append(convert_divider_to_str(value, compute_divider(value)))

    return _tick_labels


def calculate_label_position(xlist, ylist, xy_loc_multiplier=None):
    """Compute xy location of label based on the xy values"""

    if xy_loc_multiplier is None:
        return None, None

    x_loc_multiplier, y_loc_multiplier = xy_loc_multiplier

    # Get values
    x_min = np.min(xlist)
    x_max = np.max(xlist)
    y_min = np.min(ylist)
    y_max = np.max(ylist)

    # Calculate RMSD positions
    label_x_pos = x_min + ((x_max - x_min) * x_loc_multiplier) / 100
    label_y_pos = y_min + ((y_max - y_min) * y_loc_multiplier) / 100

    return label_x_pos, label_y_pos


def add_exponent_to_label(label, divider):
    expo = len(str(divider)) - len(str(divider).rstrip("0"))

    # remove previous exponent label
    label = label.split(" [")[0]

    if expo > 1:
        offset_text = r"x$\mathregular{10^{%d}}$" % expo
        label = "".join([label, " [", offset_text, "]"])

    return label


def convert_label(label, label_format):
    if label_format == "String":
        try:
            new_label = str(label)
        except UnicodeEncodeError:
            new_label = str(label)
    elif label_format == "Float":
        new_label = str2num(label)
        if new_label in [None, "None"]:
            try:
                new_label = str(label)
            except UnicodeEncodeError:
                new_label = str(label)
    elif label_format == "Integer":
        new_label = str2int(label)
        if new_label in [None, "None"]:
            new_label = str2num(label)
            new_label = str2int(new_label)
            if new_label in [None, "None"]:
                try:
                    new_label = str(label)
                except UnicodeEncodeError:
                    new_label = str(label)

    return new_label


def extents(f):
    delta = f[1] - f[0]
    return [f[0] - delta / 2, f[-1] + delta / 2]


def check_n_grid_dimensions(n_grid):

    if n_grid in [2]:
        n_rows, n_cols, y_label_pos, x_label_pos = 1, 2, 1, 1
    elif n_grid in [3, 4]:
        n_rows, n_cols, y_label_pos, x_label_pos = 2, 2, 1, 1
    elif n_grid in [5, 6]:
        n_rows, n_cols, y_label_pos, x_label_pos = 2, 3, 1, 2
    elif n_grid in [7, 8, 9]:
        n_rows, n_cols, y_label_pos, x_label_pos = 3, 3, 2, 2
    elif n_grid in [10, 11, 12]:
        n_rows, n_cols, y_label_pos, x_label_pos = 3, 4, 2, 1
    elif n_grid in [13, 14, 15, 16]:
        n_rows, n_cols, y_label_pos, x_label_pos = 4, 4, 1, 1
    elif n_grid in list(range(17, 26)):
        n_rows, n_cols, y_label_pos, x_label_pos = 5, 5, 3, 3
    elif n_grid in list(range(26, 37)):
        n_rows, n_cols, y_label_pos, x_label_pos = 6, 6, 1, 1

    return n_rows, n_cols, y_label_pos, x_label_pos


def check_plot_settings(**kwargs):
    # convert weights
    if "title" in kwargs:
        if kwargs["title_weight"] and isbool(kwargs["title_weight"]):
            kwargs["title_weight"] = "heavy"
        else:
            kwargs["title_weight"] = "normal"

    if "label_weight" in kwargs:
        if kwargs["label_weight"] and isbool(kwargs["label_weight"]):
            kwargs["label_weight"] = "heavy"
        else:
            kwargs["label_weight"] = "normal"

    return kwargs


def convert_to_vertical_line_input(xvals, yvals):
    lines = []
    for i in range(len(xvals)):
        pair = [(xvals[i], 0), (xvals[i], yvals[i])]
        lines.append(pair)

    return lines
