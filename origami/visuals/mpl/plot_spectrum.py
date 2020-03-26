# Standard library imports
import logging

# Third-party imports
import numpy as np
import matplotlib
from seaborn import color_palette
from matplotlib import patches
from matplotlib import gridspec
from matplotlib.ticker import MaxNLocator
from matplotlib.collections import LineCollection

# Local imports
import origami.utils.visuals as ut_visuals
from origami.utils.misc import merge_two_dicts
from origami.utils.misc import remove_nan_from_list
from origami.utils.color import get_random_color
from origami.utils.labels import _replace_labels
from origami.utils.ranges import get_min_max
from origami.utils.ranges import find_limits_all
from origami.utils.ranges import find_limits_list
from origami.visuals.mpl.base import PlotBase
from origami.processing.heatmap import normalize_2D
from origami.processing.spectra import normalize_1D
from origami.gui_elements.misc_dialogs import DialogBox

logger = logging.getLogger(__name__)


class PlotSpectrum(PlotBase):
    def __init__(self, *args, **kwargs):
        PlotBase.__init__(self, *args, **kwargs)

    def transform(self, x, y, x_label, y_label, transform_x, transform_y):
        """Performs basic transformation on the x/y axis data to ensure it is nicely displayed to the user"""
        if transform_x:
            x, y_label, __ = self._convert_xaxis(x, x_label)

        if transform_y:
            y, y_label, __ = self._convert_yaxis(x, y_label)

        return x, y, x_label, y_label

    def set_line_style(self, **kwargs):
        """Updates line style"""
        for __, line in enumerate(self.plot_base.get_lines()):
            line.set_linewidth(kwargs["line_width"])
            line.set_linestyle(kwargs["line_style"])

    def store_plot_limits(self, extent):
        self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]

    def plot_1d(self, x, y, title="", x_label="", y_label="", label="", **kwargs):
        """Standard 1d plot"""
        # Simple hack to reduce size is to use different subplot size
        self._set_axes()

        # transform data and determine plot limits
        x, y, x_label, y_label = self.transform(
            x,
            y,
            x_label,
            y_label,
            transform_x=kwargs.get("transform_x", False),
            transform_y=kwargs.get("transform_y", False),
        )
        xlimits, ylimits, extent = self._compute_xy_limits(x, y, 1.1)

        # add 1d plot
        self.plot_base.plot(
            x,
            y,
            color=kwargs["line_color"],
            label=label,
            linewidth=kwargs["line_width"],
            linestyle=kwargs["line_style"],
        )
        if kwargs["shade_under"]:
            self.plot_1d_add_under_curve(x, y, **kwargs)

        # set plot limits
        self.plot_base.set_xlim(xlimits)
        self.plot_base.set_ylim(ylimits)

        self.set_plot_xlabel(x_label, **kwargs)
        self.set_plot_ylabel(x_label, **kwargs)
        self.set_plot_title(title, **kwargs)
        self.set_tick_parameters(**kwargs)
        self.set_line_style(**kwargs)

        self.setup_new_zoom(
            [self.plot_base],
            data_limits=extent,
            allow_extraction=kwargs.get("allow_extraction", False),
            callbacks=kwargs.get("callbacks", dict()),
        )

        # Setup X-axis getter
        self.store_plot_limits(extent)

    def plot_1D(
        self,
        xvals=None,
        yvals=None,
        xlabel="",
        ylabel="",
        label="",
        title="",
        xlimits=None,
        plotType=None,
        testMax="yvals",
        testX=False,
        allowWheel=True,
        axesSize=None,
        **kwargs,
    ):
        """
        Plots MS and 1DT data
        """
        # update settings
        self._check_and_update_plot_settings(plot_name=plotType, axes_size=axesSize, **kwargs)

        if testMax == "yvals":
            yvals, ylabel, __ = self._convert_yaxis(yvals, ylabel)

        if testX:
            xvals, xlabel, __ = self._convert_xaxis(xvals)

        # Simple hack to reduce size is to use different subplot size
        self.plot_base = self.figure.add_axes(self._axes)
        self.plot_base.plot(
            xvals,
            yvals,
            color=kwargs["line_color"],
            label=label,
            linewidth=kwargs["line_width"],
            linestyle=kwargs["line_style"],
        )
        if kwargs["shade_under"]:
            self.plot_1d_add_under_curve(xvals, yvals, **kwargs)

        # Setup parameters
        if xlimits is None or xlimits[0] is None or xlimits[1] is None:
            xlimits = (np.min(xvals), np.max(xvals))

        # update limits and extents
        ylimits = (np.min(yvals), np.max(yvals) * 1.1)

        # check if user provided
        if "plot_modifiers" in kwargs:
            plot_modifiers = kwargs["plot_modifiers"]

            if "xlimits" in plot_modifiers and plot_modifiers["xlimits"] != [None, None]:
                xlimits = plot_modifiers["xlimits"]
            if "ylimits" in plot_modifiers and plot_modifiers["ylimits"] != [None, None]:
                ylimits = plot_modifiers["ylimits"]

        extent = [xlimits[0], ylimits[0], xlimits[1], ylimits[1]]
        self.plot_base.set_xlim(xlimits)
        self.plot_base.set_ylim(ylimits)

        if kwargs.get("minor_ticks_off", False) or xlabel == "Scans" or xlabel == "Charge":
            self.plot_base.xaxis.set_tick_params(which="minor", bottom="off")
            self.plot_base.xaxis.set_major_locator(MaxNLocator(integer=True))

        self.set_plot_xlabel(xlabel, **kwargs)
        self.set_plot_ylabel(ylabel, **kwargs)
        self.set_tick_parameters(**kwargs)

        for __, line in enumerate(self.plot_base.get_lines()):
            line.set_linewidth(kwargs["line_width"])
            line.set_linestyle(kwargs["line_style"])

        if title != "":
            self.set_plot_title(title, **kwargs)

        self.setup_zoom(
            [self.plot_base],
            self.zoomtype,
            data_lims=extent,
            plotName=plotType,
            allowWheel=allowWheel,
            allow_extraction=kwargs.get("allow_extraction", False),
            callbacks=kwargs.get("callbacks", dict()),
        )

        # Setup X-axis getter
        self.setupGetXAxies([self.plot_base])
        self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]
        self.plot_labels.update({"xlabel": xlabel, "ylabel": ylabel})

    def plot_1D_centroid(
        self,
        xvals=None,
        yvals=None,
        xyvals=None,
        xlabel="m/z (Da)",
        ylabel="Intensity",
        title="",
        xlimits=None,
        color="black",
        update_y_axis=True,
        zoom="box",
        plot_name="MS",
        axesSize=None,
        adding_on_top=False,
        **kwargs,
    ):
        """
        Parameters
        ----------
        adding_on_top : bool
            If ``True`` it will not create new axes and will instead change the size
            of the plot to ensure appropriate overlay.
        update_y_axis : bool
            If ``True`` y-axis values will be rescaled to ensure they do not have
            excessive number of zeroes.
        """

        # update settings
        self._check_and_update_plot_settings(plot_name=plot_name, axes_size=axesSize, **kwargs)

        if kwargs.get("butterfly_plot", False):
            yvals = -np.array(yvals)
            self.plot_base.axhline(linewidth=kwargs["line_width"], color="k")

        if update_y_axis:
            yvals, ylabel, __ = self._convert_yaxis(yvals, ylabel)
        else:
            yvals = np.divide(yvals, float(self.y_divider))

        if xyvals is None:
            xyvals = ut_visuals.convert_to_vertical_line_input(xvals, yvals)

        # Simple hack to reduce size is to use different subplot size
        if not adding_on_top:
            self.plot_base = self.figure.add_axes(self._axes)
        else:
            self.plot_base.set_position(self._axes)
        line_coll = LineCollection(xyvals, colors=(kwargs["line_color"]), linewidths=(kwargs["line_width"]))
        self.plot_base.add_collection(line_coll)

        # Setup parameters
        if xlimits is None or xlimits[0] is None or xlimits[1] is None:
            xlimits = (np.min(xvals) - 5, np.max(xvals) + 5)

        # update limits and extents
        if kwargs.get("butterfly_plot", False):
            xylimits = self.get_xylimits()
            ylimits = [-xylimits[3], xylimits[3]]
        else:
            ylimits = (np.min(yvals), np.max(yvals) * 1.1)

        # check if user provided
        if "plot_modifiers" in kwargs:
            plot_modifiers = kwargs["plot_modifiers"]

            if "xlimits" in plot_modifiers and plot_modifiers["xlimits"] != [None, None]:
                xlimits = plot_modifiers["xlimits"]
            if "ylimits" in plot_modifiers and plot_modifiers["ylimits"] != [None, None]:
                ylimits = plot_modifiers["ylimits"]

        extent = [xlimits[0], ylimits[0], xlimits[1], ylimits[1]]
        self.plot_base.set_xlim(xlimits)
        self.plot_base.set_ylim(ylimits)

        self.set_plot_xlabel(xlabel, **kwargs)
        self.set_plot_ylabel(ylabel, **kwargs)
        self.set_tick_parameters(**kwargs)

        for __, line in enumerate(self.plot_base.get_lines()):
            line.set_linewidth(kwargs["line_width"])
            line.set_linestyle(kwargs["line_style"])

        if title != "":
            self.set_plot_title(title, **kwargs)

        self.setup_zoom([self.plot_base], self.zoomtype, data_lims=extent, plotName=plot_name, allowWheel=True)

        # Setup X-axis getter
        self.setupGetXAxies([self.plot_base])
        if not adding_on_top:
            self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]

    def plot_1D_barplot(
        self,
        xvals,
        yvals,
        labels,
        colors,
        xlabel="",
        ylabel="",
        title="",
        zoom="box",
        axesSize=None,
        plotType=None,
        **kwargs,
    ):
        # update settings
        self._check_and_update_plot_settings(plot_name=plotType, axes_size=axesSize, **kwargs)

        if not kwargs.get("bar_edgecolor_sameAsFill", True):
            edgecolor = kwargs.get("bar_edgecolor", "#000000")
        else:
            edgecolor = colors

        # Simple hack to reduce size is to use different subplot size
        xticloc = np.array(xvals)
        self.plot_base = self.figure.add_axes(self._axes, xticks=xticloc)
        self.plot_base.bar(
            xvals,
            yvals,
            color=colors,
            label="Intensities",
            alpha=kwargs.get("bar_alpha", 0.5),
            linewidth=kwargs.get("bar_linewidth", 1),
            width=kwargs.get("bar_width", 1),
            edgecolor=edgecolor,
        )

        peaklabels = [str(p) for p in labels]
        self.plot_base.set_xticklabels(peaklabels, rotation=90, fontsize=kwargs["label_size"])  # 90
        self.set_plot_xlabel(xlabel, **kwargs)
        self.set_plot_ylabel(ylabel, **kwargs)
        self.set_tick_parameters(**kwargs)

        for __, line in enumerate(self.plot_base.get_lines()):
            line.set_linewidth(kwargs["line_width"])
            line.set_linestyle(kwargs["line_style"])

        if title != "":
            self.set_plot_title(title, **kwargs)

        xlimits = self.plot_base.get_xlim()
        ylimits = self.plot_base.get_ylim()
        extent = [xlimits[0], ylimits[0], xlimits[1], ylimits[1]]
        self.setup_zoom([self.plot_base], self.zoomtype, plotName=plotType, data_lims=extent)

    def plot_floating_barplot(
        self, xvals, yvals_min, yvals_max, xlabel, ylabel, colors=None, axesSize=None, plotName="bar", **kwargs
    ):
        # update settings
        if colors is None:
            colors = []
        self._check_and_update_plot_settings(plot_name=plotName, axes_size=axesSize, **kwargs)

        matplotlib.rc("xtick", labelsize=kwargs["tick_size"])
        matplotlib.rc("ytick", labelsize=kwargs["tick_size"])

        # disable ticks on one side
        if kwargs["orientation"] == "horizontal-bar":
            kwargs["ticks_left"] = False
            kwargs["tickLabels_left"] = False
        else:
            kwargs["ticks_bottom"] = False
            kwargs["tickLabels_bottom"] = False

        # Plot
        plot_modifiers = kwargs["plot_modifiers"]
        xlabel = _replace_labels(xlabel)
        ylabel = _replace_labels(ylabel)

        xvals_count = len(xvals)
        yvals_min_count = len(yvals_min)
        yvals_max_count = len(yvals_max)
        if yvals_min_count > 1 or yvals_max_count > 1:
            if xvals_count < yvals_min_count or xvals_count < yvals_max_count:
                xvals = xvals * yvals_min_count
            # if yvals_min_count != yvals_max_count and yvals_max_count > yvals_min_count:

        if len(colors) != yvals_min_count:
            colors = self._get_colors(yvals_min_count)

        if "xlimits" in plot_modifiers and plot_modifiers["xlimits"] != [None, None]:
            xlimits = plot_modifiers["xlimits"]
        else:
            xlimits, __ = find_limits_all(xvals, xvals)
            xlimits = [xlimits[0] - 2 * kwargs.get("bar_width", 0.1), xlimits[1] + 2 * kwargs.get("bar_width", 0.1)]

        if "ylimits" in plot_modifiers and plot_modifiers["ylimits"] != [None, None]:
            ylimits = plot_modifiers["ylimits"]
        else:
            ymin, ymax = find_limits_all(yvals_min, yvals_max)
            ylimits = [ymin[0] - 0.05 * ymin[0], ymax[1] + 0.05 * ymax[1]]

        for i in range(yvals_min_count):
            xval = xvals[i]
            yval_min = yvals_min[i]
            yval_max = yvals_max[i]
            yvals_height = yval_max - yval_min

            if len(kwargs["item_colors"]) > 0 and len(kwargs["item_colors"]) == yvals_min_count:
                if len(kwargs["item_colors"][i]) == len(xval):
                    colorList = kwargs["item_colors"][i]
                else:
                    colorList = len(xval) * [colors[i]]
            else:
                colorList = len(xval) * [colors[i]]

            self.plot_base = self.figure.add_axes(self._axes)
            if not kwargs.get("bar_edgecolor_sameAsFill", True):
                edgecolor = kwargs.get("bar_edgecolor", "#000000")
            else:
                edgecolor = colorList

            if kwargs["orientation"] == "vertical-bar":
                self.plot_base.bar(
                    xval,
                    bottom=yval_min,
                    height=yvals_height,
                    color=colorList,
                    width=kwargs.get("bar_width", 0.1),
                    edgecolor=edgecolor,
                    alpha=kwargs.get("bar_alpha", 0.5),
                    linewidth=kwargs.get("bar_linewidth", 1),
                )
            else:
                xlimits, ylimits = ylimits, xlimits
                self.plot_base.barh(
                    xval,
                    left=yval_min,
                    width=yvals_height,
                    color=colorList,
                    height=kwargs.get("bar_width", 0.1),
                    edgecolor=edgecolor,
                    alpha=kwargs.get("bar_alpha", 0.5),
                    linewidth=kwargs.get("bar_linewidth", 1),
                )

        self.set_plot_xlabel(xlabel, **kwargs)
        self.set_plot_ylabel(ylabel, **kwargs)
        self.set_tick_parameters(**kwargs)

        extent = [xlimits[0], ylimits[0], xlimits[1], ylimits[1]]
        self.setup_zoom([self.plot_base], self.zoomtype, data_lims=extent)
        #
        # Setup X-axis getter
        self.setupGetXAxies([self.plot_base])
        self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]

        # add legend
        plot_modifiers = kwargs["plot_modifiers"]
        legend_labels = plot_modifiers["legend_labels"]
        legend_colors = plot_modifiers["legend_colors"]
        if len(legend_labels) > 0 and len(legend_colors) > 0 and len(legend_labels) == len(legend_colors):
            legend_text = []
            for leg_color, leg_label in zip(legend_colors, legend_labels):
                leg_label = _replace_labels(leg_label)
                legend_text.append([leg_color, leg_label])
            self.plot_1D_add_legend(legend_text, **kwargs)

    def plot_1D_scatter(
        self,
        xvals=None,
        yvals=None,
        zvals=None,
        colors="red",
        labels=None,
        title="",
        xlabel="",
        ylabel="",
        xlimits=None,
        axesSize=None,
        plotName="whole",
        **kwargs,
    ):
        # update settings
        if labels is None:
            labels = []
        self._check_and_update_plot_settings(plot_name=plotName, axes_size=axesSize, **kwargs)

        # Plot
        self.plot_base = self.figure.add_axes(self._axes)
        plot_modifiers = kwargs["plot_modifiers"]
        itemColors = kwargs.get("item_colors", [])

        if yvals is None:
            yvals = []
        self.scatter_plots = []
        if len(zvals) == 0:
            for i in range(len(yvals)):
                yval = yvals[i]
                if len(xvals) == len(yvals):
                    xval = xvals[i]
                else:
                    xval = xvals
                if len(itemColors) > 0:
                    if len(itemColors) == len(yvals):
                        color = itemColors[i]
                    else:
                        color = itemColors[0]
                    try:
                        plot = self.plot_base.scatter(
                            xval,
                            yval,
                            edgecolors="k",
                            c=color,
                            s=kwargs["scatter_size"],
                            marker=kwargs["scatter_shape"],
                            alpha=kwargs["scatter_alpha"],
                            picker=5,
                        )
                    except Exception:
                        color = colors[i]
                        plot = self.plot_base.scatter(
                            xval,
                            yval,
                            edgecolors=color,
                            color=color,
                            s=kwargs["scatter_size"],
                            marker=kwargs["scatter_shape"],
                            alpha=kwargs["scatter_alpha"],
                            picker=5,
                        )
                else:
                    color = colors[i]
                    plot = self.plot_base.scatter(
                        xval,
                        yval,
                        edgecolors=color,
                        color=color,
                        s=kwargs["scatter_size"],
                        marker=kwargs["scatter_shape"],
                        alpha=kwargs["scatter_alpha"],
                        picker=5,
                    )

                self.scatter_plots.append(plot)

        elif len(xvals) != len(yvals) and zvals.shape[1] == len(colors):
            for i, color in enumerate(colors):
                plot = self.plot_base.scatter(
                    xvals,
                    zvals[:, i],
                    edgecolors=color,
                    color=color,
                    s=kwargs["scatter_size"],
                    marker=kwargs["scatter_shape"],
                    alpha=kwargs["scatter_alpha"],
                    label=labels[i],
                    picker=5,
                )
                self.scatter_plots.append(plot)

        self.set_legend_parameters(None, **kwargs)

        # Setup parameters
        xlimits, ylimits = find_limits_all(xvals, yvals)
        self.plot_base.set_xlim([xlimits[0], xlimits[1]])
        self.plot_base.set_ylim([ylimits[0], ylimits[1]])
        extent = [xlimits[0], ylimits[0], xlimits[1], ylimits[1]]

        self.set_plot_xlabel(xlabel, **kwargs)
        self.set_plot_ylabel(ylabel, **kwargs)
        self.set_tick_parameters(**kwargs)

        self.setup_zoom([self.plot_base], self.zoomtype, data_lims=extent)

        # Setup X-axis getter
        self.setupGetXAxies([self.plot_base])
        self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]

    def plot_1D_compare(
        self,
        xvals1,
        xvals2,
        yvals1,
        yvals2,
        xlabel="",
        ylabel="",
        label="",
        plotType="compare_MS",
        testMax="yvals",
        axesSize=None,
        **kwargs,
    ):
        # update settings
        self._check_and_update_plot_settings(plot_name=plotType, axes_size=axesSize, **kwargs)

        matplotlib.rc("xtick", labelsize=kwargs["tick_size"])
        matplotlib.rc("ytick", labelsize=kwargs["tick_size"])

        if testMax == "yvals":
            yvals1, yvals2, ylabel = self._plot_1D_compare_prepare_data(yvals1, yvals2, ylabel)

        if xvals2 is None:
            xvals2 = xvals1

        self.plot_base = self.figure.add_axes(self._axes)
        self.plot_base.plot(
            xvals1,
            yvals1,
            color=kwargs["line_color_1"],
            label=label[0],
            linewidth=kwargs["line_width"],
            linestyle=kwargs["line_style_1"],
            alpha=kwargs["line_transparency_1"],
            gid=0,
        )

        self.plot_base.plot(
            xvals2,
            yvals2,
            color=kwargs["line_color_2"],
            label=label[1],
            linewidth=kwargs["line_width"],
            linestyle=kwargs["line_style_2"],
            alpha=kwargs["line_transparency_2"],
            gid=1,
        )

        self.plot_base.axhline(linewidth=kwargs["line_width"], color="k")

        xlimits = np.min([np.min(xvals1), np.min(xvals2)]), np.max([np.max(xvals1), np.max(xvals2)])
        ylimits = np.min([np.min(yvals1), np.min(yvals2)]), np.max([np.max(yvals1), np.max(yvals2)])
        extent = [xlimits[0], ylimits[0] - 0.01, xlimits[-1], ylimits[1] + 0.01]

        self.set_plot_xlabel(xlabel, **kwargs)
        self.set_plot_ylabel(ylabel, **kwargs)
        self.set_legend_parameters(None, **kwargs)
        self.set_tick_parameters(**kwargs)
        self.setup_zoom([self.plot_base], self.zoomtype, data_lims=extent, plotName=plotType)

        # Setup X-axis getter
        self.setupGetXAxies([self.plot_base])
        self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]

    def plot_1D_overlay(
        self,
        xvals,
        yvals,
        colors,
        xlabel,
        ylabel,
        labels,
        xlimits=None,
        zoom="box",
        plotType=None,
        testMax="yvals",
        axesSize=None,
        title="",
        allowWheel=True,
        **kwargs,
    ):
        # update settings
        self._check_and_update_plot_settings(plot_name=plotType, axes_size=axesSize, **kwargs)

        # check in case only one item was passed
        # assumes xvals is a list in a list
        if len(xvals) != len(yvals) and len(xvals) == 1:
            xvals = xvals * len(yvals)

        matplotlib.rc("xtick", labelsize=kwargs["tick_size"])
        matplotlib.rc("ytick", labelsize=kwargs["tick_size"])

        if xlimits is None:
            xvals_limit, __ = find_limits_list(xvals, yvals)
            xlimits = (np.min(xvals_limit), np.max(xvals_limit))

        yvals, ylabel = self._convert_yaxis_list(yvals, ylabel)

        xlabel = _replace_labels(xlabel)
        ylabel = _replace_labels(ylabel)

        # Plot
        self.plot_base = self.figure.add_axes(self._axes)

        handles = []
        zorder, zorder_offset = 5, 5
        for xval, yval, color, label in zip(xvals, yvals, colors, labels):
            label = _replace_labels(label)
            self.plot_base.plot(
                xval,
                yval,
                color=color,
                label=label,
                linewidth=kwargs["line_width"],
                linestyle=kwargs["line_style"],
                zorder=zorder,
            )

            if kwargs["shade_under"]:
                handles.append(patches.Patch(color=color, label=label, alpha=0.25))
                shade_kws = dict(
                    facecolor=color,
                    alpha=kwargs.get("shade_under_transparency", 0.25),
                    clip_on=kwargs.get("clip_on", True),
                    zorder=zorder - 2,
                )
                self.plot_base.fill_between(xval, 0, yval, **shade_kws)
                zorder = zorder + zorder_offset

        if not kwargs["shade_under"]:
            handles, labels = self.plot_base.get_legend_handles_labels()

        # add legend
        self.set_legend_parameters(handles, legend_zorder=zorder + 10, **kwargs)

        self.set_plot_xlabel(xlabel, **kwargs)
        self.set_plot_ylabel(ylabel, **kwargs)

        self.plot_base.set_xlim(xlimits)
        self.plot_base.set_ylim([np.min(np.concatenate(yvals)), np.max(np.concatenate(yvals)) + 0.01])

        extent = [xlimits[0], np.min(np.concatenate(yvals)), xlimits[-1], np.max(np.concatenate(yvals)) + 0.01]

        self.set_tick_parameters(**kwargs)

        for __, line in enumerate(self.plot_base.get_lines()):
            line.set_linewidth(kwargs["line_width"])
            line.set_linestyle(kwargs["line_style"])

        if title != "":
            self.set_plot_title(title, **kwargs)

        self.setup_zoom([self.plot_base], self.zoomtype, data_lims=extent, plotName=plotType, allowWheel=allowWheel)
        # Setup X-axis getter
        self.setupGetXAxies([self.plot_base])
        self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]

    def plot_1D_waterfall(
        self,
        xvals=None,
        yvals=None,
        zvals=None,
        label="",
        xlabel="",
        colorList=None,
        ylabel="",
        zoom="box",
        axesSize=None,
        plotName="1D",
        xlimits=None,
        plotType="Waterfall",
        labels=None,
        **kwargs,
    ):
        # TODO: Convert axes.plot to LineCollection = will be a lot faster!
        # TODO: Add x-axis checker for mass spectra

        if colorList is None:
            colorList = []
        if labels is None:
            labels = []
        self.zoomtype = zoom
        self.plot_name = plotType
        kwargs = ut_visuals.check_plot_settings(**kwargs)

        # override parameters
        if not self.lock_plot_from_updating:
            if axesSize is not None:
                self._axes = axesSize

            kwargs["ticks_left"] = False
            kwargs["tickLabels_left"] = False
            self.plot_parameters = kwargs
        else:
            # update ticks
            kwargs = merge_two_dicts(kwargs, self.plot_parameters)
            self.plot_parameters = kwargs

        matplotlib.rc("xtick", labelsize=kwargs["tick_size"])
        matplotlib.rc("ytick", labelsize=kwargs["tick_size"])

        self.plot_base = self.figure.add_axes(self._axes)

        zorder, zorder_offset = 5, 5
        count = kwargs["labels_frequency"]

        # swap labels in some circumstances
        if xlabel not in ["m/z", "Mass (Da)", "Charge"]:
            xlabel, ylabel = ylabel, xlabel

        xlabel = _replace_labels(xlabel)
        ylabel = _replace_labels(ylabel)

        # uniform x-axis
        ydata = []
        if zvals is not None:
            n_items = len(zvals[1, :])
            item_list = np.linspace(0, n_items - 1, n_items).astype(np.int32)
            self.text_offset_position = dict(min=np.min(xvals), max=np.max(xvals), offset=kwargs["labels_x_offset"])
            label_xposition = np.min(xvals) + (np.max(xvals) * kwargs["labels_x_offset"])
            yOffset = kwargs["offset"] * (n_items + 1)
            label_kws = dict(fontsize=kwargs["labels_font_size"], fontweight=kwargs["labels_font_weight"])
            shade_kws = dict(alpha=kwargs.get("shade_under_transparency", 0.25), clip_on=kwargs.get("clip_on", True))
            add_underline = kwargs["shade_under"] and len(item_list) < kwargs.get("shade_under_n_limit", 50)
            add_labels = kwargs.get("add_labels", True) and kwargs["labels_frequency"] != 0

            if len(labels) != n_items:
                labels = [""] * n_items

            # reverse data
            if kwargs["reverse"]:
                zvals = np.fliplr(zvals)
                yvals = yvals[::-1]
                labels = labels[::-1]

            if xlimits is None or any([val is None for val in xlimits]):
                xlimits = [np.min(xvals), np.max(xvals)]

            # normalize data if increment is not 0
            if kwargs["increment"] != 0 and kwargs.get("normalize", True):
                zvals = normalize_2D(zvals)
            else:
                __, ylabel, __ = self._convert_yaxis(zvals, "Intensity", set_divider=False)

            colorlist = self._get_colorlist(colorList, n_items, **kwargs)
            # Iterate over the colormap to get the color shading we desire
            for i in item_list[::-1]:
                y = zvals[:, i] + yOffset
                y_min, y_max = get_min_max(y)

                if kwargs["line_color_as_shade"]:
                    line_color = colorlist[i]
                else:
                    line_color = kwargs["line_color"]
                shade_color = colorlist[i]

                self.plot_base.plot(
                    xvals,
                    y,
                    color=line_color,
                    linewidth=kwargs["line_width"],
                    linestyle=kwargs["line_style"],
                    label=labels[i],
                    zorder=zorder,
                )

                if add_underline:
                    shade_kws.update(zorder=zorder - 2, facecolor=shade_color)
                    self.plot_base.fill_between(xvals, y_min, y, **shade_kws)

                if add_labels:
                    label = ut_visuals.convert_label(yvals[i], label_format=kwargs["labels_format"])
                    if i % kwargs["labels_frequency"] == 0 or i == n_items - 1:
                        self.plot_add_text(
                            xpos=label_xposition,
                            yval=yOffset + kwargs["labels_y_offset"],
                            label=label,
                            zorder=zorder + 3,
                            **label_kws,
                        )
                ydata.extend([y_min, y_max])
                yOffset = yOffset - kwargs["increment"]
                zorder = zorder + zorder_offset
                count += 1
        else:
            raise ValueError("This method has been removed temporarily!")

        #         # non-uniform x-axis
        #         else:
        #             # check in case only one item was passed
        #             # assumes xvals is a list in a list
        #             if len(xvals) != len(yvals) and len(xvals) == 1:
        #                 xvals = xvals * len(yvals)
        #
        #             n_items = len(yvals)
        #             if len(labels) == 0:
        #                 labels = [""] * n_items
        #             yOffset = kwargs["offset"] * (n_items + 1)
        #
        #             # Find new xlimits
        #             xvals_limit, __ = find_limits_list(xvals, yvals)
        #             xlimits = (np.min(xvals_limit), np.max(xvals_limit))
        #
        #             label_xposition = xlimits[0] + (xlimits[1] * kwargs["labels_x_offset"])
        #             self.text_offset_position = dict(min=xlimits[0], max=xlimits[1], offset=kwargs["labels_x_offset"])
        #
        #             colorlist = self._get_colorlist(colorList, n_items, **kwargs)
        #
        #             if kwargs["reverse"]:
        #                 xvals = xvals[::-1]
        #                 yvals = yvals[::-1]
        #                 colorlist = colorlist[::-1]
        #                 labels = labels[::-1]
        #
        #             for irow in range(len(xvals)):
        #                 # Always normalizes data - otherwise it looks pretty bad
        #
        #                 if kwargs["increment"] != 0 and kwargs.get("normalize", True):
        #                     yvals[irow] = normalize_1D(yvals[irow])
        #                 else:
        #                     ylabel = "Intensity"
        #                     try:
        #                         ydivider, expo = self.testXYmaxValsUpdated(values=yvals[irow])
        #                         if expo > 1:
        #                             yvals[irow] = np.divide(yvals[irow], float(ydivider))
        #                             offset_text = r"x$\mathregular{10^{%d}}$" % expo
        #                             ylabel = "".join([ylabel, " [", offset_text, "]"])
        #                     except AttributeError:
        #                         kwargs["increment"] = 0.00001
        #                         yvals[irow] = normalize_1D(yvals[irow])
        #
        #                 item_list = np.linspace(0, n_items - 1, n_items)
        #                 if kwargs["line_color_as_shade"]:
        #                     line_color = colorlist[irow]
        #                 else:
        #                     line_color = kwargs["line_color"]
        #                 shade_color = colorlist[int(irow)]
        #                 y = yvals[irow]
        #                 self.plotMS.plot(
        #                     xvals[irow],
        #                     (y + yOffset),
        #                     color=line_color,
        #                     linewidth=kwargs["line_width"],
        #                     linestyle=kwargs["line_style"],
        #                     label=labels[irow],
        #                     zorder=zorder,
        #                 )
        #
        #                 if kwargs["shade_under"] and len(item_list) < kwargs.get("shade_under_n_limit", 50):
        #                     shade_kws = dict(
        #                         facecolor=shade_color,
        #                         alpha=kwargs.get("shade_under_transparency", 0.25),
        #                         clip_on=kwargs.get("clip_on", True),
        #                         zorder=zorder - 2,
        #                     )
        #                     self.plotMS.fill_between(xvals[irow], np.min(y + yOffset), (y + yOffset), **shade_kws)
        #
        #                 if kwargs.get("add_labels", True) and kwargs["labels_frequency"] != 0:
        #                     label = _replace_labels(labels[irow])
        #                     if irow % kwargs["labels_frequency"] == 0:
        #                         label_kws = dict(fontsize=kwargs["labels_font_size"],
        # fontweight=kwargs["labels_font_weight"])
        #                         self.plot_add_text(
        #                             xpos=label_xposition,
        #                             yval=yOffset + kwargs["labels_y_offset"],
        #                             label=label,
        #                             zorder=zorder + 3,
        #                             **label_kws,
        #                         )
        #                 ydata.extend(y + yOffset)
        #                 yOffset = yOffset - kwargs["increment"]
        #                 zorder = zorder + zorder_offset

        self.set_plot_xlabel(xlabel, **kwargs)
        self.set_tick_parameters(**kwargs)

        self.plot_base.spines["left"].set_visible(kwargs["spines_left"])
        self.plot_base.spines["right"].set_visible(kwargs["spines_right"])
        self.plot_base.spines["top"].set_visible(kwargs["spines_top"])
        self.plot_base.spines["bottom"].set_visible(kwargs["spines_bottom"])
        for i in self.plot_base.spines.values():
            i.set_linewidth(kwargs["frame_width"])
            i.set_zorder(zorder)

        # convert to array to remove nan's and figure out limits
        ydata = remove_nan_from_list(ydata)
        ylimits = np.min(ydata) - kwargs["offset"], np.max(ydata) + 0.05
        extent = [xlimits[0], ylimits[0], xlimits[1], ylimits[1]]

        self.setup_zoom([self.plot_base], self.zoomtype, plotName=plotName, data_lims=extent)
        self.plot_limits = [xlimits[0], xlimits[1], ylimits[0], ylimits[1]]

        # Setup X-axis getter
        self.plot_base.set_xlim([xlimits[0], xlimits[1]])

        # a couple of set values
        self.n_colors = n_items

    def plot_1D_add(self, xvals, yvals, color, label="", setup_zoom=True, allowWheel=False, plot_name=None, **kwargs):
        # get current limits
        xmin, xmax = self.plot_base.get_xlim()

        if plot_name is not None:
            self.plot_name = plot_name
        self.plot_base.plot(np.array(xvals), yvals, color=color, label=label, linewidth=kwargs.get("line_width", 2.0))

        lines = self.plot_base.get_lines()
        yvals_limits = []
        for line in lines:
            yvals_limits.extend(line.get_ydata())

        xlimits = [np.min(xvals), np.max(xvals)]
        ylimits = [np.min(yvals_limits), np.max(yvals_limits)]

        self.plot_base.set_xlim([xlimits[0], xlimits[1]])
        self.plot_base.set_ylim([ylimits[0], ylimits[1] + 0.025])

        extent = [xlimits[0], ylimits[0], xlimits[-1], ylimits[-1] + 0.025]
        if kwargs.get("update_extents", False):
            self.update_extents(extent)
            self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]

        if setup_zoom:
            self.setup_zoom(
                [self.plot_base], self.zoomtype, data_lims=extent, plotName=plot_name, allowWheel=allowWheel
            )
            self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]

        self.on_zoom_x_axis(xmin, xmax)

    def plot_1D_add_legend(self, legend_text, **kwargs):

        # update settings
        self._check_and_update_plot_settings(**kwargs)

        handles = []
        if legend_text is not None and kwargs.get("legend", self.config.legend):
            for i in range(len(legend_text)):
                handles.append(
                    patches.Patch(
                        color=legend_text[i][0], label=legend_text[i][1], alpha=kwargs["legend_patch_transparency"]
                    )
                )

        # legend
        self.set_legend_parameters(handles, **kwargs)

    def plot_remove_legend(self):
        try:
            leg = self.plot_base.axes.get_legend()
            leg.remove()
        except (AttributeError, KeyError):
            pass

    def plot_1d_add_under_curve(self, xvals, yvals, **kwargs):

        color = kwargs.get("shade_under_color", None)
        if not color:
            color = kwargs["line_color"]

        shade_kws = dict(
            facecolor=color,
            alpha=kwargs.get("shade_under_transparency", 0.25),
            clip_on=kwargs.get("clip_on", True),
            zorder=kwargs.get("zorder", 1),
        )
        self.plot_base.fill_between(xvals, 0, yvals, **shade_kws)

    def plot_1D_waterfall_overlay(
        self,
        xvals=None,
        yvals=None,
        zvals=None,
        label="",
        xlabel="",
        colorList=None,
        ylabel="",
        zoom="box",
        axesSize=None,
        plotName="1D",
        xlimits=None,
        plotType="Waterfall_overlay",
        labels=None,
        **kwargs,
    ):

        if colorList is None:
            colorList = []
        if labels is None:
            labels = []
        self.zoomtype = zoom
        self.plot_name = plotType

        # override parameters
        if not self.lock_plot_from_updating:
            if axesSize is not None:
                self._axes = axesSize

            kwargs["ticks_left"] = False
            kwargs["tickLabels_left"] = False
            self.plot_parameters = kwargs
        else:
            # update ticks
            kwargs = merge_two_dicts(kwargs, self.plot_parameters)
            self.plot_parameters = kwargs

        matplotlib.rc("xtick", labelsize=kwargs["tick_size"])
        matplotlib.rc("ytick", labelsize=kwargs["tick_size"])

        self.plot_base = self.figure.add_axes(self._axes)
        if kwargs["labels_font_weight"]:
            kwargs["labels_font_weight"] = "heavy"
        else:
            kwargs["labels_font_weight"] = "normal"

        count = len(xvals)
        zorder, zorder_offset = 5, 5 + count
        label_freq = kwargs["labels_frequency"]

        if xlabel not in ["m/z", "Mass (Da)", "Charge"]:
            xlabel, ylabel = ylabel, xlabel

        ydata = []

        if len(labels) == 0:
            labels = [" "] * count
        yOffset_start = yOffset = kwargs["offset"] * (count + 1)

        # Find new xlimits
        xvals_limit, __ = find_limits_list(xvals, yvals)
        xlimits = (np.min(xvals_limit), np.max(xvals_limit))

        label_xposition = xlimits[0] + (xlimits[1] * kwargs["labels_x_offset"])
        self.text_offset_position = dict(min=xlimits[0], max=xlimits[1], offset=kwargs["labels_x_offset"])

        for item in range(len(xvals)):
            xval = xvals[item]
            yval = yvals[item]
            zval = np.array(zvals[item])
            line_color = colorList[item]
            yOffset = yOffset_start
            label = labels[item]

            shade_color = colorList[item]
            if not kwargs["reverse"]:
                yval = yval[::-1]
                zval = np.fliplr(zval)

            for irow in range(len(yval)):
                if irow > 0:
                    label = ""

                zval_one = np.asarray(zval[:, irow])
                if kwargs["increment"] != 0 and kwargs.get("normalize", True):
                    zval_one = normalize_1D(zval_one)

                y = zval_one + yOffset
                self.plot_base.plot(
                    xval,
                    y,
                    color=line_color,
                    linewidth=kwargs["line_width"],
                    linestyle=kwargs["line_style"],
                    label=label,
                    zorder=zorder,
                )
                if kwargs["shade_under"] and len(yval) < kwargs.get("shade_under_n_limit", 50):
                    shade_kws = dict(
                        facecolor=shade_color,
                        alpha=kwargs.get("shade_under_transparency", 0.25),
                        clip_on=kwargs.get("clip_on", True),
                        zorder=zorder - 2,
                    )
                    self.plot_base.fill_between(xval, np.min(y), y, **shade_kws)

                if kwargs.get("add_labels", True) and kwargs["labels_frequency"] != 0 and item == 0:
                    x_label = ut_visuals.convert_label(yval[irow], label_format=kwargs["labels_format"])
                    if irow % kwargs["labels_frequency"] == 0:
                        label_kws = dict(fontsize=kwargs["labels_font_size"], fontweight=kwargs["labels_font_weight"])
                        self.plot_add_text(
                            xpos=label_xposition,
                            yval=yOffset + kwargs["labels_y_offset"],
                            label=x_label,
                            zorder=zorder + 3,
                            **label_kws,
                        )
                ydata.extend(y)
                yOffset = yOffset - kwargs["increment"]
                zorder = zorder + 5
            zorder = zorder + (zorder_offset * 5)

        handles, __ = self.plot_base.get_legend_handles_labels()
        self.set_legend_parameters(handles, **kwargs)

        self.set_plot_xlabel(xlabel, **kwargs)

        self.set_tick_parameters(**kwargs)

        for __, line in enumerate(self.plot_base.get_lines()):
            line.set_linewidth(kwargs["line_width"])
            line.set_linestyle(kwargs["line_style"])

        self.plot_base.spines["left"].set_visible(kwargs["spines_left"])
        self.plot_base.spines["right"].set_visible(kwargs["spines_right"])
        self.plot_base.spines["top"].set_visible(kwargs["spines_top"])
        self.plot_base.spines["bottom"].set_visible(kwargs["spines_bottom"])
        for i in self.plot_base.spines.values():
            i.set_linewidth(kwargs["frame_width"])
            i.set_zorder(zorder)

        ydata = remove_nan_from_list(ydata)
        ylimits = [np.min(ydata) - kwargs["offset"], np.max(ydata) + 0.05]
        extent = [xlimits[0], ylimits[0], xlimits[1], ylimits[1]]
        self.setup_zoom([self.plot_base], self.zoomtype, plotName=plotName, data_lims=extent)
        self.plot_limits = [xlimits[0], xlimits[1], ylimits[0], ylimits[1]]
        # Setup X-axis getter
        self.setupGetXAxies([self.plot_base])
        self.plot_base.set_xlim([xlimits[0], xlimits[1]])

    def plot_1D_violin(
        self,
        xvals=None,
        yvals=None,
        zvals=None,
        xlabel="",
        ylabel="",
        orientation="vertical",
        axesSize=None,
        plotName="Violin",
        plotType="Violin",
        **kwargs,
    ):

        # update settings
        self._check_and_update_plot_settings(plot_name=plotType, axes_size=axesSize, **kwargs)

        self.plot_base = self.figure.add_axes(self._axes)
        if kwargs["label_weight"]:
            kwargs["label_weight"] = "heavy"
        else:
            kwargs["label_weight"] = "normal"

        n_count = zvals.shape[1]
        if kwargs["color_scheme"] == "Colormap":
            colorlist = color_palette(kwargs["colormap"], n_count)
        elif kwargs["color_scheme"] == "Color palette":
            if kwargs["palette"] not in ["Spectral", "RdPu"]:
                kwargs["palette"] = kwargs["palette"].lower()
            colorlist = color_palette(kwargs["palette"], n_count)
        elif kwargs["color_scheme"] == "Same color":
            colorlist = [kwargs["shade_color"]] * n_count
        elif kwargs["color_scheme"] == "Random":
            colorlist = []
            for __ in range(n_count):
                colorlist.append(get_random_color())

        tick_labels, tick_position = [], []
        min_percentage = kwargs.get("min_percentage", 0.03)
        normalize = kwargs.get("normalize", True)
        spacing = kwargs.get("spacing", 0.5)

        offset = spacing
        offset_list = []
        # precalculate positions
        for i in range(n_count):
            yvals_in = zvals[:, i]
            max_value = np.max(yvals_in)
            offset_list.append(max_value)

        # select appropriate fcn
        if orientation == "horizontal":
            plot_fcn = self.plot_base.fill_between
        else:
            plot_fcn = self.plot_base.fill_betweenx

        for i in range(n_count):
            # get yvals
            yvals_in = zvals[:, i]
            if normalize:
                yvals_in = normalize_1D(yvals_in)

            # calculate offset
            max_value = np.max(yvals_in)

            if normalize:
                offset = offset + max_value * 2 + spacing
            else:
                if i == 0:
                    offset = offset + max_value
                else:
                    offset = offset + max_value + (offset_list[(i - 1)]) + spacing

            filter_index = yvals_in > (max_value * min_percentage)
            # minimise number of points
            xvals_plot = xvals[filter_index]
            yvals_plot = yvals_in[filter_index]

            if kwargs["line_color_as_shade"]:
                line_color = colorlist[i]
            else:
                line_color = kwargs["line_color"]

            shade_kws = dict(
                facecolor=colorlist[i],
                alpha=kwargs.get("shade_under_transparency", 0.25),
                clip_on=kwargs.get("clip_on", True),
            )

            plot_fcn(
                xvals_plot,
                -yvals_plot + offset,
                yvals_plot + offset,
                edgecolor=line_color,
                linewidth=kwargs["line_width"],
                **shade_kws,
            )

            if kwargs["labels_frequency"] != 0:
                if i % kwargs["labels_frequency"] == 0 or i == n_count - 1:
                    tick_position.append(offset)
                    tick_labels.append(ut_visuals.convert_label(yvals[int(i)], label_format=kwargs["labels_format"]))

        xlimits = self.plot_base.get_xlim()
        ylimits = self.plot_base.get_ylim()
        extent = [xlimits[0], ylimits[0], xlimits[1], ylimits[1]]
        if orientation == "horizontal":
            self.plot_base.set_yticks(tick_position)
            self.plot_base.set_yticklabels(tick_labels)
            xlabel, ylabel = ylabel, xlabel
        else:
            self.plot_base.set_xticks(tick_position)
            self.plot_base.set_xticklabels(tick_labels)

        handles, __ = self.plot_base.get_legend_handles_labels()
        self.set_legend_parameters(handles, **kwargs)

        self.set_plot_xlabel(xlabel, **kwargs)
        self.set_plot_ylabel(ylabel, **kwargs)

        self.set_tick_parameters(**kwargs)

        for __, line in enumerate(self.plot_base.get_lines()):
            line.set_linewidth(kwargs["line_width"])
            line.set_linestyle(kwargs["line_style"])

        self.plot_base.spines["left"].set_visible(kwargs["spines_left"])
        self.plot_base.spines["right"].set_visible(kwargs["spines_right"])
        self.plot_base.spines["top"].set_visible(kwargs["spines_top"])
        self.plot_base.spines["bottom"].set_visible(kwargs["spines_bottom"])
        for i in self.plot_base.spines.values():
            i.set_linewidth(kwargs["frame_width"])

        # a couple of set values
        self.n_colors = n_count

        # setup zoom and plot limits
        self.setup_zoom([self.plot_base], self.zoomtype, plotName=plotName, data_lims=extent)
        self.plot_limits = [xlimits[0], xlimits[1], ylimits[0], ylimits[1]]

    def plot_n_grid_1D_overlay(
        self, xvals, yvals, xlabel, ylabel, labels, colors, plotName="Grid_1D", axesSize=None, testMax="yvals", **kwargs
    ):
        # update settings
        self._check_and_update_plot_settings(plot_name=plotName, axes_size=axesSize, **kwargs)

        # check in case only one item was passed
        # assumes xvals is a list in a list
        if len(xvals) != len(yvals) and len(xvals) == 1:
            xvals = xvals * len(yvals)

        n_xvals = len(xvals)
        n_yvals = len(yvals)
        n_grid = np.max([n_xvals, n_yvals])
        n_rows, n_cols, __, __ = ut_visuals.check_n_grid_dimensions(n_grid)

        # set tick size
        matplotlib.rc("xtick", labelsize=kwargs["tick_size"])
        matplotlib.rc("ytick", labelsize=kwargs["tick_size"])

        gs = gridspec.GridSpec(nrows=n_rows, ncols=n_cols)

        # check if labels were added
        if "xlabels" in kwargs:
            xlabels = kwargs["xlabels"]
            if len(xlabels) != n_xvals:
                xlabels = [xlabel] * n_xvals
        else:
            xlabels = [xlabel] * n_xvals

        if "ylabels" in kwargs:
            ylabels = kwargs["ylabels"]
            if len(ylabels) != n_yvals:
                ylabels = [ylabel] * n_yvals
        else:
            ylabels = [ylabel] * n_yvals

        plt_list, handles, extent = [], [], []
        for i in range(n_grid):
            row = int(i // n_cols)
            col = i % n_cols

            xval = xvals[i]
            yval = yvals[i]
            color = colors[i]
            label = labels[i]
            xlabel = xlabels[i]
            ylabel = ylabels[i]

            xlabel = _replace_labels(xlabel)
            ylabel = _replace_labels(ylabel)
            #             if testMax == 'yvals':
            #                 ydivider, expo = self.testXYmaxValsUpdated(values=yval)
            #                 if expo > 1:
            #                     offset_text = r'x$\mathregular{10^{%d}}$' % expo
            #                     ylabel = ''.join([ylabel, " [", offset_text,"]"])
            #                     yval = divide(yval, float(ydivider))
            #                 else: ydivider = 1
            #                 self.y_divider = ydivider

            xmin, xmax = np.min(xval), np.max(xval)
            ymin, ymax = np.min(yval), np.max(yval)
            extent.append([xmin, ymin, xmax, ymax])
            ax = self.figure.add_subplot(gs[row, col], aspect="auto")
            ax.plot(
                xval, yval, color=color, label=label, linewidth=kwargs["line_width"], linestyle=kwargs["line_style"]
            )

            if kwargs["shade_under"]:
                handles.append(patches.Patch(color=color, label=label, alpha=0.25))
                shade_kws = dict(
                    facecolor=color,
                    alpha=kwargs.get("shade_under_transparency", 0.25),
                    clip_on=kwargs.get("clip_on", True),
                )
                ax.fill_between(xval, 0, yval, **shade_kws)
            ax.set_xlim(xmin, xmax)
            ax.set_ylim(ymin, ymax)
            ax.tick_params(
                axis="both",
                left=kwargs["ticks_left"],
                right=kwargs["ticks_right"],
                top=kwargs["ticks_top"],
                bottom=kwargs["ticks_bottom"],
                labelleft=kwargs["tickLabels_left"],
                labelright=kwargs["tickLabels_right"],
                labeltop=kwargs["tickLabels_top"],
                labelbottom=kwargs["tickLabels_bottom"],
            )

            # spines
            ax.spines["left"].set_visible(kwargs["spines_left"])
            ax.spines["right"].set_visible(kwargs["spines_right"])
            ax.spines["top"].set_visible(kwargs["spines_top"])
            ax.spines["bottom"].set_visible(kwargs["spines_bottom"])

            # update axis frame
            if kwargs["axis_onoff"]:
                ax.set_axis_on()
            else:
                ax.set_axis_off()

            kwargs["label_pad"] = 5
            ax.set_xlabel(
                xlabel, labelpad=kwargs["label_pad"], fontsize=kwargs["label_size"], weight=kwargs["label_weight"]
            )

            ax.set_ylabel(
                ylabel, labelpad=kwargs["label_pad"], fontsize=kwargs["label_size"], weight=kwargs["label_weight"]
            )

            if kwargs.get("legend", self.config.legend):
                handle, label = ax.get_legend_handles_labels()
                ax.legend(
                    loc=kwargs.get("legend_position", self.config.legendPosition),
                    ncol=kwargs.get("legend_num_columns", self.config.legendColumns),
                    fontsize=kwargs.get("legend_font_size", self.config.legendFontSize),
                    frameon=kwargs.get("legend_frame_on", self.config.legendFrame),
                    framealpha=kwargs.get("legend_transparency", self.config.legendAlpha),
                    markerfirst=kwargs.get("legend_marker_first", self.config.legendMarkerFirst),
                    markerscale=kwargs.get("legend_marker_size", self.config.legendMarkerSize),
                    fancybox=kwargs.get("legend_fancy_box", self.config.legendFancyBox),
                    scatterpoints=kwargs.get("legend_num_markers", self.config.legendNumberMarkers),
                    handles=handle,
                    labels=label,
                )

                leg = ax.axes.get_legend()
                leg.draggable()
            # add plot list
            plt_list.append(ax)

        gs.tight_layout(self.figure)
        self.figure.tight_layout()
        #
        self.setup_zoom(plt_list, self.zoomtype, data_lims=extent)

    def plot_n_grid_scatter(
        self,
        xvals,
        yvals,
        xlabel,
        ylabel,
        labels,
        colors,
        plotName="Grid_scatter",
        axesSize=None,
        testMax="yvals",
        **kwargs,
    ):
        # update settings
        self._check_and_update_plot_settings(plot_name=plotName, axes_size=axesSize, **kwargs)

        # check in case only one item was passed
        # assumes xvals is a list in a list
        if len(xvals) != len(yvals) and len(xvals) == 1:
            xvals = xvals * len(yvals)

        n_xvals = len(xvals)
        n_yvals = len(yvals)
        n_grid = np.max([n_xvals, n_yvals])
        n_rows, n_cols, __, __ = ut_visuals.check_n_grid_dimensions(n_grid)

        # convert weights
        if kwargs["title_weight"]:
            kwargs["title_weight"] = "heavy"
        else:
            kwargs["title_weight"] = "normal"

        if kwargs["label_weight"]:
            kwargs["label_weight"] = "heavy"
        else:
            kwargs["label_weight"] = "normal"

        # set tick size
        matplotlib.rc("xtick", labelsize=kwargs["tick_size"])
        matplotlib.rc("ytick", labelsize=kwargs["tick_size"])

        gs = gridspec.GridSpec(nrows=n_rows, ncols=n_cols)

        # check if labels were added
        if "xlabels" in kwargs:
            xlabels = kwargs["xlabels"]
            if len(xlabels) != n_xvals:
                xlabels = [xlabel] * n_xvals
        else:
            xlabels = [xlabel] * n_xvals

        if "ylabels" in kwargs:
            ylabels = kwargs["ylabels"]
            if len(ylabels) != n_yvals:
                ylabels = [ylabel] * n_yvals
        else:
            ylabels = [ylabel] * n_yvals

        plt_list, handles, extent = [], [], []
        for i in range(n_grid):
            row = int(i // n_cols)
            col = i % n_cols

            xval = xvals[i]
            yval = yvals[i]
            color = colors[i]
            label = labels[i]
            xlabel = xlabels[i]
            ylabel = ylabels[i]

            xlabel = _replace_labels(xlabel)
            ylabel = _replace_labels(ylabel)

            xmin, xmax = np.min(xval), np.max(xval)
            ymin, ymax = np.min(yval), np.max(yval)
            extent.append([xmin, ymin, xmax, ymax])
            ax = self.figure.add_subplot(gs[row, col], aspect="auto")
            ax.scatter(
                xval,
                yval,
                color=color,
                marker=kwargs["scatter_shape"],
                alpha=kwargs["scatter_alpha"],
                s=kwargs["scatter_size"],
            )

            #                 if plot_modifiers.get("color_items", False) and len(kwargs['item_colors']) > 0:
            #                     color = kwargs['item_colors'][0]
            #                     try:
            #                         plot = self.plotMS.scatter(xval, yval,
            #                                                    edgecolors="k",
            #                                                     c=color,
            #                                                    s=kwargs['scatter_size'],
            #                                                    marker=kwargs['scatter_shape'],
            #                                                    alpha=kwargs['scatter_alpha'],
            #     #                                                label=labels[i],
            #                                                    picker=5)
            #                     except Exception:
            #                         color = colors[i]
            #                         plot = self.plotMS.scatter(xval, yval,
            #                                                    edgecolors=color,
            #                                                    color=color,
            #                                                    s=kwargs['scatter_size'],
            #                                                    marker=kwargs['scatter_shape'],
            #                                                    alpha=kwargs['scatter_alpha'],
            #     #                                                label=labels[i],
            #                                                    picker=5)
            #                 else:
            #                     color = colors[i]
            #                     plot = self.plotMS.scatter(xval, yval,
            #                                                edgecolors=color,
            #                                                color=color,
            #                                                s=kwargs['scatter_size'],
            #                                                marker=kwargs['scatter_shape'],
            #                                                alpha=kwargs['scatter_alpha'],
            # #                                                label=labels[i],
            #                                                picker=5)

            ax.set_xlim(xmin, xmax)
            ax.set_ylim(ymin, ymax)
            ax.tick_params(
                axis="both",
                left=kwargs["ticks_left"],
                right=kwargs["ticks_right"],
                top=kwargs["ticks_top"],
                bottom=kwargs["ticks_bottom"],
                labelleft=kwargs["tickLabels_left"],
                labelright=kwargs["tickLabels_right"],
                labeltop=kwargs["tickLabels_top"],
                labelbottom=kwargs["tickLabels_bottom"],
            )

            # spines
            ax.spines["left"].set_visible(kwargs["spines_left"])
            ax.spines["right"].set_visible(kwargs["spines_right"])
            ax.spines["top"].set_visible(kwargs["spines_top"])
            ax.spines["bottom"].set_visible(kwargs["spines_bottom"])

            # update axis frame
            if kwargs["axis_onoff"]:
                ax.set_axis_on()
            else:
                ax.set_axis_off()

            kwargs["label_pad"] = 5
            ax.set_xlabel(
                xlabel, labelpad=kwargs["label_pad"], fontsize=kwargs["label_size"], weight=kwargs["label_weight"]
            )

            ax.set_ylabel(
                ylabel, labelpad=kwargs["label_pad"], fontsize=kwargs["label_size"], weight=kwargs["label_weight"]
            )

            if kwargs.get("legend", self.config.legend):
                handle, label = ax.get_legend_handles_labels()
                ax.legend(
                    loc=kwargs.get("legend_position", self.config.legendPosition),
                    ncol=kwargs.get("legend_num_columns", self.config.legendColumns),
                    fontsize=kwargs.get("legend_font_size", self.config.legendFontSize),
                    frameon=kwargs.get("legend_frame_on", self.config.legendFrame),
                    framealpha=kwargs.get("legend_transparency", self.config.legendAlpha),
                    markerfirst=kwargs.get("legend_marker_first", self.config.legendMarkerFirst),
                    markerscale=kwargs.get("legend_marker_size", self.config.legendMarkerSize),
                    fancybox=kwargs.get("legend_fancy_box", self.config.legendFancyBox),
                    scatterpoints=kwargs.get("legend_num_markers", self.config.legendNumberMarkers),
                    handles=handle,
                    labels=label,
                )

                leg = ax.axes.get_legend()
                leg.draggable()
            # add plot list
            plt_list.append(ax)

        gs.tight_layout(self.figure)
        self.figure.tight_layout()
        #
        self.setup_zoom(plt_list, self.zoomtype, data_lims=extent)

    def plot_1D_2D(
        self,
        yvalsRMSF=None,
        zvals=None,
        labelsX=None,
        labelsY=None,
        ylabelRMSF="",
        xlabelRMSD="",
        ylabelRMSD="",
        testMax="yvals",
        label="",
        zoom="box",
        plotName="RMSF",
        axesSize=None,
        **kwargs,
    ):
        """
        Plots RMSF and RMSD together
        """
        # Setup parameters
        gs = gridspec.GridSpec(2, 1, height_ratios=[1, 3])
        gs.update(hspace=kwargs["rmsd_hspace"])

        # update settings
        self._check_and_update_plot_settings(plot_name=plotName, axes_size=axesSize, **kwargs)

        if kwargs["label_weight"]:
            kwargs["label_weight"] = "heavy"
        else:
            kwargs["label_weight"] = "normal"

        # set tick size
        matplotlib.rc("xtick", labelsize=kwargs["tick_size"])
        matplotlib.rc("ytick", labelsize=kwargs["tick_size"])

        # Check if there are any labels attached with the data
        if xlabelRMSD == "":
            xlabelRMSD = "Scans"
        if ylabelRMSD == "":
            ylabelRMSD = "Drift time (bins)"
        if ylabelRMSF == "":
            ylabelRMSF = "RMSD (%)"

        if testMax == "yvals":
            ydivider, expo = self.testXYmaxValsUpdated(values=yvalsRMSF)
            if expo > 1:
                offset_text = r"x$\mathregular{10^{%d}}$" % expo
                ylabelRMSF = "".join([ylabelRMSF, " [", offset_text, "]"])
                yvalsRMSF = np.divide(yvalsRMSF, float(ydivider))
        else:
            ylabelRMSF = "RMSD (%)"

        # Plot RMSF data (top plot)
        if len(labelsX) != len(yvalsRMSF):
            DialogBox(
                exceptionTitle="Missing data",
                exceptionMsg="Missing x-axis labels! Cannot execute this action!",
                type="Error",
            )
            return

        self.plotRMSF = self.figure.add_subplot(gs[0], aspect="auto")
        self.plotRMSF.plot(
            labelsX,
            yvalsRMSF,
            color=kwargs["rmsd_line_color"],
            linewidth=kwargs["rmsd_line_width"],
            linestyle=kwargs["rmsd_line_style"],
        )

        self.plotRMSF.fill_between(
            labelsX,
            yvalsRMSF,
            0,
            edgecolor=kwargs["rmsd_line_color"],
            facecolor=kwargs["rmsd_underline_color"],
            alpha=kwargs["rmsd_underline_transparency"],
            hatch=kwargs["rmsd_underline_hatch"],
            linewidth=kwargs["rmsd_line_width"],
            linestyle=kwargs["rmsd_line_style"],
        )

        self.plotRMSF.set_xlim([np.min(labelsX), np.max(labelsX)])
        self.plotRMSF.set_ylim([0, np.max(yvalsRMSF) + 0.2])
        self.plotRMSF.get_xaxis().set_visible(False)

        self.plotRMSF.set_ylabel(
            ylabelRMSF, labelpad=kwargs["label_pad"], fontsize=kwargs["label_size"], weight=kwargs["label_weight"]
        )

        extent = ut_visuals.extents(labelsX) + ut_visuals.extents(labelsY)
        self.plot_base = self.figure.add_subplot(gs[1], aspect="auto")

        self.cax = self.plot_base.imshow(
            zvals,
            extent=extent,
            cmap=kwargs["colormap"],
            interpolation=kwargs["interpolation"],
            norm=kwargs["colormap_norm"],
            aspect="auto",
            origin="lower",
        )

        xmin, xmax = self.plot_base.get_xlim()
        ymin, ymax = self.plot_base.get_ylim()
        self.plot_base.set_xlim(xmin, xmax - 0.5)
        self.plot_base.set_ylim(ymin, ymax - 0.5)

        extent = [labelsX[0], labelsY[0], labelsX[-1], labelsY[-1]]
        self.setup_zoom([self.plot_base], self.zoomtype, data_lims=extent, plotName=plotName)
        self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]

        self.set_plot_xlabel(xlabelRMSD, **kwargs)
        self.set_plot_ylabel(ylabelRMSD, **kwargs)

        # ticks
        self.plot_base.tick_params(
            axis="both",
            left=kwargs["ticks_left"],
            right=kwargs["ticks_right"],
            top=kwargs["ticks_top"],
            bottom=kwargs["ticks_bottom"],
            labelleft=kwargs["tickLabels_left"],
            labelright=kwargs["tickLabels_right"],
            labeltop=kwargs["tickLabels_top"],
            labelbottom=kwargs["tickLabels_bottom"],
        )

        self.plotRMSF.tick_params(
            axis="both",
            left=kwargs["ticks_left_1D"],
            right=kwargs["ticks_right_1D"],
            top=kwargs["ticks_top_1D"],
            bottom=kwargs["ticks_bottom_1D"],
            labelleft=kwargs["tickLabels_left_1D"],
            labelright=kwargs["tickLabels_right_1D"],
            labeltop=kwargs["tickLabels_top_1D"],
            labelbottom=kwargs["tickLabels_bottom_1D"],
        )

        # spines
        self.plot_base.spines["left"].set_visible(kwargs["spines_left"])
        self.plot_base.spines["right"].set_visible(kwargs["spines_right"])
        self.plot_base.spines["top"].set_visible(kwargs["spines_top"])
        self.plot_base.spines["bottom"].set_visible(kwargs["spines_bottom"])
        [i.set_linewidth(kwargs["frame_width"]) for i in self.plot_base.spines.values()]

        self.plotRMSF.spines["left"].set_visible(kwargs["spines_left_1D"])
        self.plotRMSF.spines["right"].set_visible(kwargs["spines_right_1D"])
        self.plotRMSF.spines["top"].set_visible(kwargs["spines_top_1D"])
        self.plotRMSF.spines["bottom"].set_visible(kwargs["spines_bottom_1D"])
        [i.set_linewidth(kwargs["frame_width"]) for i in self.plotRMSF.spines.values()]

        # update axis frame
        if kwargs["axis_onoff"]:
            self.plot_base.set_axis_on()
        else:
            self.plot_base.set_axis_off()

        if kwargs["axis_onoff_1D"]:
            self.plotRMSF.set_axis_on()
        else:
            self.plotRMSF.set_axis_off()

        # update gridspace
        self.set_colorbar_parameters(zvals, **kwargs)
        gs.tight_layout(self.figure)
        self.figure.tight_layout()