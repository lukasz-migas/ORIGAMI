# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import os
import time

import numpy as np
import pandas as pd
from utils.color import convertHEXtoRGB1
from utils.labels import _replace_labels


class MetaTextReader:
    def __init__(self, filename, **kwargs):
        tstart = time.time()
        self.filename = filename
        self.title = os.path.basename(filename)

    def load_file(self, fname):

        if fname.endswith(".csv"):
            df = pd.read_csv(fname, sep=",", engine="python", header=None)
        elif fname.endswith(".txt"):
            df = pd.read_csv(fname, sep="\t", engine="python", header=None)

        self.df = df

    def extract_data(self):

        plot_type = "multi-line"
        fname = self.title

        plot_modifiers = {}
        if "title" in list(self.df.iloc[:, 0]):
            idx = list(self.df.iloc[:, 0]).index("title")
            title = list(self.df.iloc[idx, 1::])[0]

        row_labels = list(self.df.iloc[:, 0])
        if "plot_type" in row_labels:
            idx = row_labels.index("plot_type")
            plot_type = list(self.df.iloc[idx, 1::])[0]

        if "x_label" in row_labels:
            idx = row_labels.index("x_label")
            x_label = list(self.df.iloc[idx, 1::])[0]
        else:
            x_label = ""

        if "y_label" in row_labels:
            idx = row_labels.index("y_label")
            y_label = list(self.df.iloc[idx, 1::])[0]
        else:
            y_label = ""

        if "x_unit" in row_labels:
            idx = row_labels.index("x_unit")
            x_unit = list(self.df.iloc[idx, 1::])[0]
        else:
            x_unit = ""

        if "y_unit" in row_labels:
            idx = row_labels.index("y_unit")
            y_unit = list(self.df.iloc[idx, 1::])[0]
        else:
            y_unit = ""

        if "order" in row_labels:
            idx = row_labels.index("order")
            order = list(self.df.iloc[idx, 1::])
        else:
            order = []

        if "label" in row_labels:
            idx = row_labels.index("label")
            labels = list(self.df.iloc[idx, 1::].dropna())
        elif "labels" in row_labels:
            idx = row_labels.index("labels")
            labels = list(self.df.iloc[idx, 1::].dropna())
        else:
            labels = []

        if "x_labels" in row_labels:
            idx = row_labels.index("x_labels")
            x_labels = list(self.df.iloc[idx, 1::].dropna())
        else:
            x_labels = []

        if "y_labels" in row_labels:
            idx = row_labels.index("y_labels")
            y_labels = list(self.df.iloc[idx, 1::].dropna())
        else:
            y_labels = []

        if "xlimits" in row_labels:
            idx = row_labels.index("xlimits")
            xlimits = list(self.df.iloc[idx, 1:3].dropna().astype("float32"))
        else:
            xlimits = [None, None]

        if "ylimits" in row_labels:
            idx = row_labels.index("ylimits")
            ylimits = list(self.df.iloc[idx, 1:3].dropna().astype("float32"))
        else:
            ylimits = [None, None]

        if "color" in row_labels:
            idx = row_labels.index("color")
            colors = list(self.df.iloc[idx, 1::].dropna())
        elif "colors" in row_labels:
            idx = row_labels.index("colors")
            colors = list(self.df.iloc[idx, 1::].dropna())
        else:
            colors = []

        if "column_type" in row_labels:
            idx = row_labels.index("column_type")
            column_types = list(self.df.iloc[idx, 1::].dropna())
        else:
            column_types = []

        if "legend_labels" in row_labels:
            idx = row_labels.index("legend_labels")
            legend_labels = list(self.df.iloc[idx, 1::].dropna())
        else:
            legend_labels = []

        if "legend_colors" in row_labels:
            idx = row_labels.index("legend_colors")
            legend_colors = list(self.df.iloc[idx, 1::].dropna())
        else:
            legend_colors = []

        if "hover_labels" in row_labels:
            idx = row_labels.index("hover_labels")
            hover_labels = list(self.df.iloc[idx, 1::].dropna())
        else:
            hover_labels = []

        plot_modifiers.update(
            legend_labels=legend_labels, legend_colors=legend_colors, xlimits=xlimits, ylimits=ylimits
        )
        xvals, yvals, zvals, xvalsErr, yvalsErr, itemColors, itemLabels = [], [], [], [], [], [], []
        xyvals = []
        axis_y_min, axis_y_max, axis_note = [], [], []
        xy_labels = []

        # get first index
        first_num_idx = pd.to_numeric(self.df.iloc[:, 0], errors="coerce").notnull().idxmax()

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
        ]:
            if xy_axis in row_labels:
                idx = row_labels.index(xy_axis)
                xy_labels = list(self.df.iloc[idx, :])

        if len(xy_labels) == self.df.shape[1]:
            df = self.df.iloc[first_num_idx:, :]  # [pd.to_numeric(self.df.iloc[:,0], errors='coerce').notnull()]
            for i, xy_label in enumerate(xy_labels):
                if xy_label == "axis_x":
                    xvals.append(np.asarray(self.df.iloc[:, i].dropna().astype("float32")))
                if xy_label == "axis_y":
                    yvals.append(np.asarray(self.df.iloc[:, i].dropna().astype("float32")))
                if xy_label == "axis_xerr":
                    xvalsErr.append(np.asarray(self.df.iloc[:, i].dropna().astype("float32")))
                if xy_label == "axis_yerr":
                    yvalsErr.append(np.asarray(self.df.iloc[:, i].dropna().astype("float32")))
                if xy_label == "axis_y_min":
                    axis_y_min.append(np.asarray(self.df.iloc[:, i].dropna().astype("float32")))
                if xy_label == "axis_y_max":
                    axis_y_max.append(np.asarray(self.df.iloc[:, i].dropna().astype("float32")))
                if xy_label in ["axis_xy", "axis_yx"]:
                    xyvals.append(np.asarray(self.df.iloc[:, i].dropna().astype("float32")))
                if xy_label in ["axis_color", "axis_colors"]:
                    _colors = list(self.df.iloc[:, i].dropna().astype("str"))
                    _colorsRGB = []
                    for _color in _colors:
                        _colorsRGB.append(convertHEXtoRGB1(str(_color)))
                    itemColors.append(_colorsRGB)
                    plot_modifiers["color_items"] = True
                if xy_label in ["axis_label", "axis_labels"]:
                    itemLabels.append(list(self.df.iloc[:, i].replace(np.nan, "", regex=True).astype("str")))
                    plot_modifiers["label_items"] = True
                if xy_label == "axis_note":
                    axis_note.append(np.asarray(self.df.iloc[:, i].replace(np.nan, "", regex=True).astype("str")))
        else:
            # drop all other non-numeric rows
            df = df[pd.to_numeric(self.df.iloc[:, 0], errors="coerce").notnull()]
            df = self.df.astype("float32")

            # extract x, y and zvals
            if self.df.shape[1] >= 2:
                xvals = list(self.df.iloc[:, 0])
            else:
                return None, None

            if self.df.shape[1] == 2:
                yvals = list(self.df.iloc[:, 1])

            if self.df.shape[1] > 2:
                zvals = self.df.iloc[:, 1::].as_matrix()

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
            if n_grid in [2]:
                n_rows, n_cols = 1, 2
            elif n_grid in [3, 4]:
                n_rows, n_cols = 2, 2
            elif n_grid in [5, 6]:
                n_rows, n_cols = 2, 3
            elif n_grid in [7, 8, 9]:
                n_rows, n_cols = 3, 3
            elif n_grid in [10, 11, 12]:
                n_rows, n_cols = 3, 4
            elif n_grid in [13, 14, 15, 16]:
                n_rows, n_cols = 4, 4
            elif n_grid in [17, 18, 19, 20, 21, 22, 23, 24, 25]:
                n_rows, n_cols = 5, 5
            plot_modifiers.update(n_grid=n_grid, n_rows=n_rows, n_cols=n_cols)

        # check if we need to add any metadata
        if len(colors) == 0 or len(colors) < len(yvals):
            colors = self.presenter.view.panelPlots.on_change_color_palette(
                None, n_colors=len(yvals), return_colors=True
            )

        if len(labels) != len(yvals):
            labels = [""] * len(yvals)

        msg = "Item {} has: x-columns ({}), x-errors ({}), y-columns ({}), x-errors ({}), ".format(
            os.path.basename(fname), len(xvals), len(xvalsErr), len(yvals), len(yvalsErr)
        ) + "labels ({}), colors ({})".format(len(labels), len(colors))
        print(msg)

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
            "column_types": column_types,
            "column_order": order,
            "path": fname,
            "plot_modifiers": plot_modifiers,
        }

        return title, other_data
