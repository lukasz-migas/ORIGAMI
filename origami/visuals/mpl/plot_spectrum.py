"""Plot spectral data"""
# Standard library imports
import logging

# Third-party imports
import numpy as np

# Local imports
from origami.visuals.mpl.gids import PlotIds
from origami.visuals.utilities import get_intensity_formatter
from origami.visuals.mpl.plot_base import PlotBase

logger = logging.getLogger(__name__)


class PlotSpectrum(PlotBase):
    """Instantiate plot canvas"""

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
            line.set_linewidth(kwargs["spectrum_line_width"])
            line.set_linestyle(kwargs["spectrum_line_style"])

    def plot_1d(
        self, x, y, title="", x_label="", y_label="", label="", y_lower_start=0, y_upper_multiplier=1.1, **kwargs
    ):
        """Standard 1d plot

        Parameters
        ----------
        x :
        y :
        title :
        x_label :
        y_label :
        label :
        kwargs :
        """
        # Simple hack to reduce size is to use different subplot size
        self._set_axes()

        xlimits, ylimits, extent = self._compute_xy_limits(x, y, y_lower_start, y_upper_multiplier)

        # add 1d plot
        self.plot_base.plot(
            x,
            y,
            color=kwargs["spectrum_line_color"],
            label=label,
            linewidth=kwargs["spectrum_line_width"],
            linestyle=kwargs["spectrum_line_style"],
            gid=PlotIds.PLOT_1D_LINE_GID,
        )
        if kwargs["spectrum_line_fill_under"]:
            self.plot_1d_add_under_curve(x, y, **kwargs)

        # setup axis formatters
        self.plot_base.yaxis.set_major_formatter(get_intensity_formatter())
        if kwargs.get("x_axis_formatter", False):
            self.plot_base.xaxis.set_major_formatter(get_intensity_formatter())
        self.plot_base.set_xlim(xlimits)
        self.plot_base.set_ylim(ylimits)
        self.set_plot_xlabel(x_label, **kwargs)
        self.set_plot_ylabel(y_label, **kwargs)
        self.set_plot_title(title, **kwargs)
        self.set_tick_parameters(**kwargs)
        self.set_line_style(**kwargs)

        self.setup_new_zoom(
            [self.plot_base],
            data_limits=[extent],
            allow_extraction=kwargs.get("allow_extraction", False),
            callbacks=kwargs.get("callbacks", dict()),
        )

        # Setup X-axis getter
        self.store_plot_limits([extent], [self.plot_base])
        self.PLOT_TYPE = "line"

    def plot_1d_add_under_curve(self, xvals, yvals, gid=None, ax=None, **kwargs):
        """Fill data under the line"""
        color = kwargs.get("spectrum_fill_color", None)
        if not color:
            color = kwargs["spectrum_line_color"]

        shade_kws = dict(
            facecolor=color,
            alpha=kwargs.get("spectrum_fill_transparency", 0.25),
            clip_on=kwargs.get("clip_on", True),
            zorder=kwargs.get("zorder", 1),
            hatch=kwargs.get("spectrum_fill_hatch", None),
        )
        if ax is None:
            ax = self.plot_base
        if gid is None:
            gid = PlotIds.PLOT_1D_PATCH_GID
        ax.fill_between(xvals, 0, yvals, gid=gid, **shade_kws)

    def plot_1d_update_data(
        self, x, y, x_label="", y_label="", y_lower_start=0, y_upper_multiplier=1.1, ax=None, **kwargs
    ):
        """Update plot data"""
        # override parameters
        _, _, extent = self._compute_xy_limits(x, y, y_lower_start, y_upper_multiplier)

        if ax is None:
            ax = self.plot_base

        line = None
        lines = ax.get_lines()
        for line in lines:
            gid = line.get_gid()
            if gid == PlotIds.PLOT_1D_LINE_GID:
                break

        if line is None:
            raise ValueError("Could not find line to update")

        line.set_xdata(x)
        line.set_ydata(y)
        line.set_linewidth(kwargs["spectrum_line_width"])
        line.set_color(kwargs["spectrum_line_color"])
        line.set_linestyle(kwargs["spectrum_line_style"])
        line.set_label(kwargs.get("label", ""))

        for patch in ax.collections:
            if patch.get_gid() == PlotIds.PLOT_1D_PATCH_GID:
                patch.remove()
                self.plot_1d_add_under_curve(x, y, ax=ax, **kwargs)

        # general plot updates
        self.set_plot_xlabel(x_label, **kwargs)
        self.set_plot_ylabel(y_label, **kwargs)

        # update plot limits
        self.update_extents([extent])
        self.store_plot_limits([extent], [self.plot_base])

    def plot_1d_compare(
        self, x_top, x_bottom, y_top, y_bottom, x_label="", y_label="", labels=None, title="", **kwargs
    ):
        """Standard overlay plot

        Parameters
        ----------
        x_top :
        x_bottom :
        y_top :
        y_bottom :
        x_label :
        y_label :
        labels :
        title :
        kwargs :
        """
        self._set_axes()

        if labels is None or not isinstance(labels, list):
            labels = ["", ""]

        xlimits, ylimits, extent = self._compute_multi_xy_limits([x_top, x_bottom], [y_top, y_bottom], None)

        if x_bottom is None:
            x_bottom = x_top

        self.plot_base = self.figure.add_axes(self._axes)
        self.plot_base.plot(
            x_top,
            y_top,
            color=kwargs["compare_color_top"],
            label=labels[0],
            linewidth=kwargs["spectrum_line_width"],
            linestyle=kwargs["compare_style_top"],
            alpha=kwargs["compare_alpha_top"],
            gid=PlotIds.PLOT_COMPARE_TOP_GID,
        )

        self.plot_base.plot(
            x_bottom,
            y_bottom,
            color=kwargs["compare_color_bottom"],
            label=labels[1],
            linewidth=kwargs["spectrum_line_width"],
            linestyle=kwargs["compare_style_bottom"],
            alpha=kwargs["compare_alpha_bottom"],
            gid=PlotIds.PLOT_COMPARE_BOTTOM_GID,
        )

        self.plot_base.axhline(linewidth=kwargs["spectrum_line_width"], color="k")

        # set plot limits
        self.plot_base.yaxis.set_major_formatter(get_intensity_formatter())
        self.plot_base.set_xlim(xlimits)
        self.plot_base.set_ylim(ylimits)
        self.set_plot_xlabel(x_label, **kwargs)
        self.set_plot_ylabel(y_label, **kwargs)
        self.set_plot_title(title, **kwargs)
        self.set_tick_parameters(**kwargs)
        self.set_legend_parameters(None, **kwargs)
        self.set_line_style(**kwargs)

        self.setup_new_zoom(
            [self.plot_base],
            data_limits=[extent],
            allow_extraction=kwargs.get("allow_extraction", False),
            callbacks=kwargs.get("callbacks", dict()),
        )

        # Setup X-axis getter
        self.store_plot_limits([extent], [self.plot_base])

        # update style
        self.plot_1d_update_style_by_label(
            PlotIds.PLOT_COMPARE_TOP_GID, spectrum_line_style=kwargs["compare_style_top"]
        )
        self.plot_1d_update_style_by_label(
            PlotIds.PLOT_COMPARE_BOTTOM_GID, spectrum_line_style=kwargs["compare_style_bottom"]
        )
        self.PLOT_TYPE = "line-compare"

    def prepare_barplot(self, colors, **kwargs):
        """Prepare barchart"""
        if not kwargs.get("bar_edge_same_as_fill", True):
            edgecolor = kwargs.get("bar_edge_color", (0, 0, 0, 1))
            edgecolor = [edgecolor] * len(colors)
        else:
            edgecolor = colors

        return edgecolor

    def plot_1d_barplot(self, x, y, labels, colors, x_label="", y_label="", title="", **kwargs):
        """Basic barchart plot"""
        # update settings
        xlimits, ylimits, extent = self._compute_xy_limits(x, y, 0, 1.1, x_pad=1)
        edgecolor = self.prepare_barplot(colors, **kwargs)

        # Simple hack to reduce size is to use different subplot size
        xticloc = np.array(x)
        self.plot_base = self.figure.add_axes(self._axes, xticks=xticloc)
        self.cax = self.plot_base.bar(
            x,
            y,
            color=colors,
            label="Intensities",
            alpha=kwargs.get("bar_alpha", 0.5),
            linewidth=kwargs.get("bar_line_width", 1),
            width=kwargs.get("bar_width", 1),
            edgecolor=edgecolor,
        )

        self.plot_base.set_xlim(xlimits)
        self.plot_base.set_ylim(ylimits)
        self.set_plot_xlabel(x_label, **kwargs)
        self.set_plot_ylabel(y_label, **kwargs)
        self.set_plot_title(title, **kwargs)
        self.set_tick_parameters(**kwargs)
        self.set_legend_parameters(None, **kwargs)
        self.set_line_style(**kwargs)

        peaklabels = [str(p) for p in labels]
        self.plot_base.set_xticklabels(peaklabels, rotation=90, fontsize=kwargs["axes_tick_font_size"])  # 90

        self.setup_new_zoom(
            [self.plot_base],
            data_limits=[extent],
            allow_extraction=kwargs.get("allow_extraction", False),
            callbacks=kwargs.get("callbacks", dict()),
        )

    def plot_1d_update_barplot(self, **kwargs):
        """Update barchart"""
        colors = [patch.get_facecolor() for patch in self.cax.patches]
        edgecolor = self.prepare_barplot(colors, **kwargs)

        n_width = kwargs["bar_width"] / 2
        for i, patch in enumerate(self.cax.patches):
            patch.set_alpha(kwargs["bar_alpha"])

            patch.set_edgecolor(edgecolor[i])
            patch.set_linewidth(kwargs["bar_line_width"])
            x, width = patch.get_x(), patch.get_width() / 2
            x_c = x + width
            patch.set_x(x_c - n_width)
            patch.set_width(kwargs["bar_width"])

        print(dir(self.cax.patches[0]))

    def plot_1d_compare_update_data(self, x_top, x_bottom, y_top, y_bottom, labels=None, **kwargs):
        """Update comparison data"""
        if labels is None or not isinstance(labels, list):
            labels = ["", ""]

        _, ylimits, extent = self._compute_multi_xy_limits([x_top, x_bottom], [y_top, y_bottom], None)

        lines = self.plot_base.get_lines()
        for line in lines:
            plot_gid = line.get_gid()
            if plot_gid == PlotIds.PLOT_COMPARE_TOP_GID:
                if labels[0] is None:
                    labels[0] = line.get_label()
                line.set_xdata(x_top)
                line.set_ydata(y_top)
                line.set_label(labels[0])
                line.set_color(kwargs.get("line_colors_1", line.get_color()))
            elif plot_gid == PlotIds.PLOT_COMPARE_BOTTOM_GID:
                if labels[1] is None:
                    labels[1] = line.get_label()
                line.set_xdata(x_bottom)
                line.set_ydata(y_bottom)
                line.set_label(labels[1])
                line.set_color(kwargs.get("compare_color_bottom", line.get_color()))

        # update legend
        handles, __ = self.plot_base.get_legend_handles_labels()
        self.set_legend_parameters(handles, **self.plot_parameters)

        # update plot limits
        self.update_extents([extent])
        self.store_plot_limits([extent], [self.plot_base])
        self.on_zoom_y_axis(*ylimits)

    def plot_1d_update_style_by_label(
        self,
        gid: str = None,
        spectrum_line_color=None,
        spectrum_line_style: str = None,
        spectrum_line_width: float = None,
        spectrum_line_transparency: float = None,
        label: str = None,
        ax=None,
    ):
        """Update line style based on a specific group id"""
        if gid is None:
            gid = PlotIds.PLOT_1D_LINE_GID
        if ax is None:
            ax = self.plot_base
        lines = ax.get_lines()
        for line in lines:
            plot_gid = line.get_gid()
            if plot_gid == gid:
                if spectrum_line_color is not None:
                    line.set_color(spectrum_line_color)
                if spectrum_line_width is not None:
                    line.set_linewidth(spectrum_line_width)
                if spectrum_line_style is not None:
                    line.set_linestyle(spectrum_line_style)
                if spectrum_line_transparency is not None:
                    line.set_alpha(spectrum_line_transparency)
                if label is not None:
                    line.set_label(label)

        handles, __ = ax.get_legend_handles_labels()
        self.set_legend_parameters(handles, **self.plot_parameters)
        return True

    def plot_1d_update_patch_style_by_label(
        self,
        gid: str = None,
        ax=None,
        spectrum_line_fill_under: bool = None,
        spectrum_fill_color=None,
        spectrum_fill_transparency: float = None,
        spectrum_fill_hatch: str = None,
        x: np.ndarray = None,
        y: np.ndarray = None,
        fill_kwargs=None,
    ):
        """Update patch style based on a specific group id"""
        if gid is None:
            gid = PlotIds.PLOT_1D_PATCH_GID
        if ax is None:
            ax = self.plot_base

        found = False
        for patch in ax.collections:
            patch_id = patch.get_gid()
            if patch_id == gid:
                found = True
                if spectrum_fill_color is not None:
                    patch.set_facecolor(spectrum_fill_color)
                if spectrum_fill_transparency is not None:
                    patch.set_alpha(spectrum_fill_transparency)
                patch.set_hatch(spectrum_fill_hatch)
                if not spectrum_line_fill_under:
                    patch.remove()

        # failed to find patch BUT it needs to be created
        if not found and spectrum_line_fill_under and x is not None and y is not None and fill_kwargs is not None:
            self.plot_1d_add_under_curve(x, y, ax=ax, **fill_kwargs)
            found = True
        return found

    def plot_1d_add_line(
        self, x: np.ndarray, y: np.ndarray, label: str, line_color: (1, 0, 0), gid: str = "", **kwargs
    ):
        """Add 1d line"""
        self._set_axes()

        xlimits, ylimits, extent = self._compute_xy_limits(x, y, 0, 1.1)

        if not self.check_line(gid, self.plot_base):
            self.plot_base = self.figure.add_axes(self._axes)
            self.plot_base.plot(
                x,
                y,
                color=line_color,
                label=label,
                linewidth=kwargs["spectrum_line_width"],
                linestyle=kwargs["spectrum_line_style"],
                gid=gid,
            )
        else:
            self.update_line(x, y, gid, self.plot_base)
            self.plot_1d_update_style_by_label(
                gid, line_color, kwargs["spectrum_line_style"], kwargs["spectrum_line_width"]
            )

        # set plot limits
        self.plot_base.yaxis.set_major_formatter(get_intensity_formatter())
        # self.plot_base.set_xlim(xlimits)
        # self.plot_base.set_ylim(ylimits)
        self.set_tick_parameters(**kwargs)
        self.set_legend_parameters(None, **kwargs)
        self.set_line_style(**kwargs)

        # self.setup_new_zoom(
        #     [self.plot_base],
        #     data_limits=[extent],
        #     allow_extraction=kwargs.get("allow_extraction", False),
        #     callbacks=kwargs.get("callbacks", dict()),
        # )

        # Setup X-axis getter
        # self.store_plot_limits([extent], [self.plot_base])
        self.PLOT_TYPE = "line"

    def plot_1d_scatter(
        self,
        x,
        y,
        title="",
        x_label="",
        y_label="",
        label="",
        color="b",
        marker="o",
        size=20,
        y_lower_start=0,
        y_upper_multiplier=1.1,
        y_lower_multiplier=1,
        x_pad=0,
        y_pad=0,
        x_axis_formatter: bool = False,
        y_axis_formatter: bool = True,
        **kwargs,
    ):
        """Standard 1d plot

        Parameters
        ----------
        x :
        y :
        title :
        x_label :
        y_label :
        label :
        kwargs :
        """
        # Simple hack to reduce size is to use different subplot size
        self._set_axes()

        xlimits, ylimits, extent = self._compute_xy_limits(
            x, y, y_lower_start, y_upper_multiplier, x_pad=x_pad, y_pad=y_pad, y_lower_multiplier=y_lower_multiplier
        )

        self.plot_base.scatter(
            x,
            y,
            color=color,
            marker=marker,
            s=size,
            label=label,
            edgecolor=kwargs.get("edge_color", "k"),
            alpha=kwargs.get("marker_alpha", 1.0),
            zorder=kwargs.get("zorder", 5),
        )

        # setup axis formatters
        if x_axis_formatter:
            self.plot_base.xaxis.set_major_formatter(get_intensity_formatter())
        if y_axis_formatter:
            self.plot_base.yaxis.set_major_formatter(get_intensity_formatter())
        self.plot_base.set_xlim(xlimits)
        self.plot_base.set_ylim(ylimits)
        self.set_plot_xlabel(x_label, **kwargs)
        self.set_plot_ylabel(y_label, **kwargs)
        self.set_plot_title(title, **kwargs)
        self.set_tick_parameters(**kwargs)

        self.setup_new_zoom(
            [self.plot_base],
            data_limits=[extent],
            allow_extraction=kwargs.get("allow_extraction", False),
            callbacks=kwargs.get("callbacks", dict()),
        )

        # Setup X-axis getter
        self.store_plot_limits([extent], [self.plot_base])
        self.PLOT_TYPE = "scatter"

    #
    # def plot_1D_centroid(
    #     self,
    #     xvals=None,
    #     yvals=None,
    #     xyvals=None,
    #     xlabel="m/z (Da)",
    #     ylabel="Intensity",
    #     title="",
    #     xlimits=None,
    #     color="black",
    #     update_y_axis=True,
    #     zoom="box",
    #     plot_name="MS",
    #     axesSize=None,
    #     adding_on_top=False,
    #     **kwargs,
    # ):
    #     """
    #     Parameters
    #     ----------
    #     adding_on_top : bool
    #         If ``True`` it will not create new axes and will instead change the size
    #         of the plot to ensure appropriate overlay.
    #     update_y_axis : bool
    #         If ``True`` y-axis values will be rescaled to ensure they do not have
    #         excessive number of zeroes.
    #     """
    #
    #     # update settings
    #     self._check_and_update_plot_settings(plot_name=plot_name, axes_size=axesSize, **kwargs)
    #
    #     if kwargs.get("butterfly_plot", False):
    #         yvals = -np.array(yvals)
    #         self.plot_base.axhline(linewidth=kwargs["spectrum_line_width"], color="k")
    #
    #     if update_y_axis:
    #         yvals, ylabel, __ = self._convert_yaxis(yvals, ylabel)
    #     else:
    #         yvals = np.divide(yvals, float(self.y_divider))
    #
    #     if xyvals is None:
    #         xyvals = ut_visuals.convert_to_vertical_line_input(xvals, yvals)
    #
    #     # Simple hack to reduce size is to use different subplot size
    #     if not adding_on_top:
    #         self.plot_base = self.figure.add_axes(self._axes)
    #     else:
    #         self.plot_base.set_position(self._axes)
    #     line_coll = LineCollection(xyvals, colors=(kwargs["spectrum_line_color"]),
    #     linewidths=(kwargs["spectrum_line_width"]))
    #     self.plot_base.add_collection(line_coll)
    #
    #     # Setup parameters
    #     if xlimits is None or xlimits[0] is None or xlimits[1] is None:
    #         xlimits = (np.min(xvals) - 5, np.max(xvals) + 5)
    #
    #     # update limits and extents
    #     if kwargs.get("butterfly_plot", False):
    #         xylimits = self.get_xy_limits()
    #         ylimits = [-xylimits[3], xylimits[3]]
    #     else:
    #         ylimits = (np.min(yvals), np.max(yvals) * 1.1)
    #
    #     # check if user provided
    #     if "plot_modifiers" in kwargs:
    #         plot_modifiers = kwargs["plot_modifiers"]
    #
    #         if "xlimits" in plot_modifiers and plot_modifiers["xlimits"] != [None, None]:
    #             xlimits = plot_modifiers["xlimits"]
    #         if "ylimits" in plot_modifiers and plot_modifiers["ylimits"] != [None, None]:
    #             ylimits = plot_modifiers["ylimits"]
    #
    #     extent = [xlimits[0], ylimits[0], xlimits[1], ylimits[1]]
    #     self.plot_base.set_xlim(xlimits)
    #     self.plot_base.set_ylim(ylimits)
    #
    #     self.set_plot_xlabel(xlabel, **kwargs)
    #     self.set_plot_ylabel(ylabel, **kwargs)
    #     self.set_tick_parameters(**kwargs)
    #
    #     for __, line in enumerate(self.plot_base.get_lines()):
    #         line.set_linewidth(kwargs["spectrum_line_width"])
    #         line.set_linestyle(kwargs["spectrum_line_style"])
    #
    #     if title != "":
    #         self.set_plot_title(title, **kwargs)
    #
    #     self.setup_zoom([self.plot_base], self.zoomtype, data_lims=extent, plotName=plot_name, allowWheel=True)
    #
    #     # Setup X-axis getter
    #     self.setupGetXAxies([self.plot_base])
    #     if not adding_on_top:
    #         self.plot_base.plot_limits = [extent[0], extent[2], extent[1], extent[3]]
    #
    #
    # def plot_floating_barplot(
    #     self, xvals, yvals_min, yvals_max, xlabel, ylabel, colors=None, axesSize=None, plotName="bar", **kwargs
    # ):
    #     # update settings
    #     if colors is None:
    #         colors = []
    #     self._check_and_update_plot_settings(plot_name=plotName, axes_size=axesSize, **kwargs)
    #
    #     matplotlib.rc("xtick", labelsize=kwargs["axes_tick_font_size"])
    #     matplotlib.rc("ytick", labelsize=kwargs["axes_tick_font_size"])
    #
    #     # disable ticks on one side
    #     if kwargs["violin_orientation"] == "horizontal-bar":
    #         kwargs["axes_frame_ticks_left"] = False
    #         kwargs["axes_frame_tick_labels_left"] = False
    #     else:
    #         kwargs["axes_frame_ticks_bottom"] = False
    #         kwargs["axes_frame_tick_labels_bottom"] = False
    #
    #     # Plot
    #     plot_modifiers = kwargs["plot_modifiers"]
    #     xlabel = _replace_labels(xlabel)
    #     ylabel = _replace_labels(ylabel)
    #
    #     xvals_count = len(xvals)
    #     yvals_min_count = len(yvals_min)
    #     yvals_max_count = len(yvals_max)
    #     if yvals_min_count > 1 or yvals_max_count > 1:
    #         if xvals_count < yvals_min_count or xvals_count < yvals_max_count:
    #             xvals = xvals * yvals_min_count
    #         # if yvals_min_count != yvals_max_count and yvals_max_count > yvals_min_count:
    #
    #     if len(colors) != yvals_min_count:
    #         colors = self._get_colors(yvals_min_count)
    #
    #     if "xlimits" in plot_modifiers and plot_modifiers["xlimits"] != [None, None]:
    #         xlimits = plot_modifiers["xlimits"]
    #     else:
    #         xlimits, __ = find_limits_all(xvals, xvals)
    #         xlimits = [xlimits[0] - 2 * kwargs.get("bar_width", 0.1), xlimits[1] + 2 * kwargs.get("bar_width", 0.1)]
    #
    #     if "ylimits" in plot_modifiers and plot_modifiers["ylimits"] != [None, None]:
    #         ylimits = plot_modifiers["ylimits"]
    #     else:
    #         ymin, ymax = find_limits_all(yvals_min, yvals_max)
    #         ylimits = [ymin[0] - 0.05 * ymin[0], ymax[1] + 0.05 * ymax[1]]
    #
    #     for i in range(yvals_min_count):
    #         xval = xvals[i]
    #         yval_min = yvals_min[i]
    #         yval_max = yvals_max[i]
    #         yvals_height = yval_max - yval_min
    #
    #         if len(kwargs["item_colors"]) > 0 and len(kwargs["item_colors"]) == yvals_min_count:
    #             if len(kwargs["item_colors"][i]) == len(xval):
    #                 colorList = kwargs["item_colors"][i]
    #             else:
    #                 colorList = len(xval) * [colors[i]]
    #         else:
    #             colorList = len(xval) * [colors[i]]
    #
    #         self.plot_base = self.figure.add_axes(self._axes)
    #         if not kwargs.get("bar_edge_same_as_fill", True):
    #             edgecolor = kwargs.get("bar_edge_color", "#000000")
    #         else:
    #             edgecolor = colorList
    #
    #         if kwargs["violin_orientation"] == "vertical-bar":
    #             self.plot_base.bar(
    #                 xval,
    #                 bottom=yval_min,
    #                 height=yvals_height,
    #                 color=colorList,
    #                 width=kwargs.get("bar_width", 0.1),
    #                 edgecolor=edgecolor,
    #                 alpha=kwargs.get("bar_alpha", 0.5),
    #                 linewidth=kwargs.get("bar_line_width", 1),
    #             )
    #         else:
    #             xlimits, ylimits = ylimits, xlimits
    #             self.plot_base.barh(
    #                 xval,
    #                 left=yval_min,
    #                 width=yvals_height,
    #                 color=colorList,
    #                 height=kwargs.get("bar_width", 0.1),
    #                 edgecolor=edgecolor,
    #                 alpha=kwargs.get("bar_alpha", 0.5),
    #                 linewidth=kwargs.get("bar_line_width", 1),
    #             )
    #
    #     self.set_plot_xlabel(xlabel, **kwargs)
    #     self.set_plot_ylabel(ylabel, **kwargs)
    #     self.set_tick_parameters(**kwargs)
    #
    #     extent = [xlimits[0], ylimits[0], xlimits[1], ylimits[1]]
    #     self.setup_zoom([self.plot_base], self.zoomtype, data_lims=extent)
    #     #
    #     # Setup X-axis getter
    #     self.setupGetXAxies([self.plot_base])
    #     self.plot_base.plot_limits = [extent[0], extent[2], extent[1], extent[3]]
    #
    #     # add legend
    #     plot_modifiers = kwargs["plot_modifiers"]
    #     legend_labels = plot_modifiers["legend_labels"]
    #     legend_colors = plot_modifiers["legend_colors"]
    #     if len(legend_labels) > 0 and len(legend_colors) > 0 and len(legend_labels) == len(legend_colors):
    #         legend_text = []
    #         for leg_color, leg_label in zip(legend_colors, legend_labels):
    #             leg_label = _replace_labels(leg_label)
    #             legend_text.append([leg_color, leg_label])
    #         self.plot_1D_add_legend(legend_text, **kwargs)
    #
    # def plot_1D_scatter(
    #     self,
    #     xvals=None,
    #     yvals=None,
    #     zvals=None,
    #     colors="red",
    #     labels=None,
    #     title="",
    #     xlabel="",
    #     ylabel="",
    #     xlimits=None,
    #     axesSize=None,
    #     plotName="whole",
    #     **kwargs,
    # ):
    #     # update settings
    #     if labels is None:
    #         labels = []
    #     self._check_and_update_plot_settings(plot_name=plotName, axes_size=axesSize, **kwargs)
    #
    #     # Plot
    #     self.plot_base = self.figure.add_axes(self._axes)
    #     plot_modifiers = kwargs["plot_modifiers"]
    #     itemColors = kwargs.get("item_colors", [])
    #
    #     if yvals is None:
    #         yvals = []
    #     self.scatter_plots = []
    #     if len(zvals) == 0:
    #         for i in range(len(yvals)):
    #             yval = yvals[i]
    #             if len(xvals) == len(yvals):
    #                 xval = xvals[i]
    #             else:
    #                 xval = xvals
    #             if len(itemColors) > 0:
    #                 if len(itemColors) == len(yvals):
    #                     color = itemColors[i]
    #                 else:
    #                     color = itemColors[0]
    #                 try:
    #                     plot = self.plot_base.scatter(
    #                         xval,
    #                         yval,
    #                         edgecolors="k",
    #                         c=color,
    #                         s=kwargs["marker_size"],
    #                         marker=kwargs["marker_shape"],
    #                         alpha=kwargs["marker_transparency"],
    #                         picker=5,
    #                     )
    #                 except Exception:
    #                     color = colors[i]
    #                     plot = self.plot_base.scatter(
    #                         xval,
    #                         yval,
    #                         edgecolors=color,
    #                         color=color,
    #                         s=kwargs["marker_size"],
    #                         marker=kwargs["marker_shape"],
    #                         alpha=kwargs["marker_transparency"],
    #                         picker=5,
    #                     )
    #             else:
    #                 color = colors[i]
    #                 plot = self.plot_base.scatter(
    #                     xval,
    #                     yval,
    #                     edgecolors=color,
    #                     color=color,
    #                     s=kwargs["marker_size"],
    #                     marker=kwargs["marker_shape"],
    #                     alpha=kwargs["marker_transparency"],
    #                     picker=5,
    #                 )
    #
    #             self.scatter_plots.append(plot)
    #
    #     elif len(xvals) != len(yvals) and zvals.shape[1] == len(colors):
    #         for i, color in enumerate(colors):
    #             plot = self.plot_base.scatter(
    #                 xvals,
    #                 zvals[:, i],
    #                 edgecolors=color,
    #                 color=color,
    #                 s=kwargs["marker_size"],
    #                 marker=kwargs["marker_shape"],
    #                 alpha=kwargs["marker_transparency"],
    #                 label=labels[i],
    #                 picker=5,
    #             )
    #             self.scatter_plots.append(plot)
    #
    #     self.set_legend_parameters(None, **kwargs)
    #
    #     # Setup parameters
    #     xlimits, ylimits = find_limits_all(xvals, yvals)
    #     self.plot_base.set_xlim([xlimits[0], xlimits[1]])
    #     self.plot_base.set_ylim([ylimits[0], ylimits[1]])
    #     extent = [xlimits[0], ylimits[0], xlimits[1], ylimits[1]]
    #
    #     self.set_plot_xlabel(xlabel, **kwargs)
    #     self.set_plot_ylabel(ylabel, **kwargs)
    #     self.set_tick_parameters(**kwargs)
    #
    #     self.setup_zoom([self.plot_base], self.zoomtype, data_lims=extent)
    #
    #     # Setup X-axis getter
    #     self.setupGetXAxies([self.plot_base])
    #     self.plot_base.plot_limits = [extent[0], extent[2], extent[1], extent[3]]
    #
    # def plot_1D_overlay(
    #     self,
    #     xvals,
    #     yvals,
    #     colors,
    #     xlabel,
    #     ylabel,
    #     labels,
    #     xlimits=None,
    #     zoom="box",
    #     plotType=None,
    #     testMax="yvals",
    #     axesSize=None,
    #     title="",
    #     allowWheel=True,
    #     **kwargs,
    # ):
    #     # update settings
    #     self._check_and_update_plot_settings(plot_name=plotType, axes_size=axesSize, **kwargs)
    #
    #     # check in case only one item was passed
    #     # assumes xvals is a list in a list
    #     if len(xvals) != len(yvals) and len(xvals) == 1:
    #         xvals = xvals * len(yvals)
    #
    #     matplotlib.rc("xtick", labelsize=kwargs["axes_tick_font_size"])
    #     matplotlib.rc("ytick", labelsize=kwargs["axes_tick_font_size"])
    #
    #     if xlimits is None:
    #         xvals_limit, __ = find_limits_list(xvals, yvals)
    #         xlimits = (np.min(xvals_limit), np.max(xvals_limit))
    #
    #     yvals, ylabel = self._convert_yaxis_list(yvals, ylabel)
    #
    #     xlabel = _replace_labels(xlabel)
    #     ylabel = _replace_labels(ylabel)
    #
    #     # Plot
    #     self.plot_base = self.figure.add_axes(self._axes)
    #
    #     handles = []
    #     zorder, zorder_offset = 5, 5
    #     for xval, yval, color, label in zip(xvals, yvals, colors, labels):
    #         label = _replace_labels(label)
    #         self.plot_base.plot(
    #             xval,
    #             yval,
    #             color=color,
    #             label=label,
    #             linewidth=kwargs["spectrum_line_width"],
    #             linestyle=kwargs["spectrum_line_style"],
    #             zorder=zorder,
    #         )
    #
    #         if kwargs["spectrum_line_fill_under"]:
    #             handles.append(patches.Patch(color=color, label=label, alpha=0.25))
    #             shade_kws = dict(
    #                 facecolor=color,
    #                 alpha=kwargs.get("spectrum_fill_transparency", 0.25),
    #                 clip_on=kwargs.get("clip_on", True),
    #                 zorder=zorder - 2,
    #             )
    #             self.plot_base.fill_between(xval, 0, yval, **shade_kws)
    #             zorder = zorder + zorder_offset
    #
    #     if not kwargs["spectrum_line_fill_under"]:
    #         handles, labels = self.plot_base.get_legend_handles_labels()
    #
    #     # add legend
    #     self.set_legend_parameters(handles, legend_zorder=zorder + 10, **kwargs)
    #
    #     self.set_plot_xlabel(xlabel, **kwargs)
    #     self.set_plot_ylabel(ylabel, **kwargs)
    #
    #     self.plot_base.set_xlim(xlimits)
    #     self.plot_base.set_ylim([np.min(np.concatenate(yvals)), np.max(np.concatenate(yvals)) + 0.01])
    #
    #     extent = [xlimits[0], np.min(np.concatenate(yvals)), xlimits[-1], np.max(np.concatenate(yvals)) + 0.01]
    #
    #     self.set_tick_parameters(**kwargs)
    #
    #     for __, line in enumerate(self.plot_base.get_lines()):
    #         line.set_linewidth(kwargs["spectrum_line_width"])
    #         line.set_linestyle(kwargs["spectrum_line_style"])
    #
    #     if title != "":
    #         self.set_plot_title(title, **kwargs)
    #
    #     self.setup_zoom([self.plot_base], self.zoomtype, data_lims=extent, plotName=plotType, allowWheel=allowWheel)
    #     # Setup X-axis getter
    #     self.setupGetXAxies([self.plot_base])
    #     self.plot_base.plot_limits = [extent[0], extent[2], extent[1], extent[3]]
    #
    #
    # def plot_1D_add(self, xvals, yvals, color, label="", setup_zoom=True, allowWheel=False, plot_name=None, **kwargs):
    #     # get current limits
    #     xmin, xmax = self.plot_base.get_xlim()
    #
    #     if plot_name is not None:
    #         self.plot_name = plot_name
    #     self.plot_base.plot(np.array(xvals), yvals, color=color, label=label,
    #     linewidth=kwargs.get("spectrum_line_width", 2.0))
    #
    #     lines = self.plot_base.get_lines()
    #     yvals_limits = []
    #     for line in lines:
    #         yvals_limits.extend(line.get_ydata())
    #
    #     xlimits = [np.min(xvals), np.max(xvals)]
    #     ylimits = [np.min(yvals_limits), np.max(yvals_limits)]
    #
    #     self.plot_base.set_xlim([xlimits[0], xlimits[1]])
    #     self.plot_base.set_ylim([ylimits[0], ylimits[1] + 0.025])
    #
    #     extent = [xlimits[0], ylimits[0], xlimits[-1], ylimits[-1] + 0.025]
    #     if kwargs.get("update_extents", False):
    #         self.update_extents([extent])
    #         self.plot_base.plot_limits = [extent[0], extent[2], extent[1], extent[3]]
    #
    #     if setup_zoom:
    #         self.setup_zoom(
    #             [self.plot_base], self.zoomtype, data_lims=extent, plotName=plot_name, allowWheel=allowWheel
    #         )
    #         self.plot_base.plot_limits = [extent[0], extent[2], extent[1], extent[3]]
    #
    #     self.on_zoom_x_axis(xmin, xmax)
    #
    # def plot_1D_add_legend(self, legend_text, **kwargs):
    #
    #     # update settings
    #     self._check_and_update_plot_settings(**kwargs)
    #
    #     handles = []
    #     if legend_text is not None and kwargs.get("legend", CONFIG.legend):
    #         for i in range(len(legend_text)):
    #             handles.append(
    #                 patches.Patch(
    #                     color=legend_text[i][0], label=legend_text[i][1], alpha=kwargs["legend_patch_transparency"]
    #                 )
    #             )
    #
    #     # legend
    #     self.set_legend_parameters(handles, **kwargs)
    #
    #
    # def plot_1D_waterfall_overlay(
    #     self,
    #     xvals=None,
    #     yvals=None,
    #     zvals=None,
    #     label="",
    #     xlabel="",
    #     colorList=None,
    #     ylabel="",
    #     zoom="box",
    #     axesSize=None,
    #     plotName="1D",
    #     xlimits=None,
    #     plotType="Waterfall_overlay",
    #     labels=None,
    #     **kwargs,
    # ):
    #
    #     if colorList is None:
    #         colorList = []
    #     if labels is None:
    #         labels = []
    #     self.zoomtype = zoom
    #     self.plot_name = plotType
    #
    #     # override parameters
    #     if not self.lock_plot_from_updating:
    #         if axesSize is not None:
    #             self._axes = axesSize
    #
    #         kwargs["axes_frame_ticks_left"] = False
    #         kwargs["axes_frame_tick_labels_left"] = False
    #         self.plot_parameters = kwargs
    #     else:
    #         # update ticks
    #         kwargs = merge_two_dicts(kwargs, self.plot_parameters)
    #         self.plot_parameters = kwargs
    #
    #     matplotlib.rc("xtick", labelsize=kwargs["axes_tick_font_size"])
    #     matplotlib.rc("ytick", labelsize=kwargs["axes_tick_font_size"])
    #
    #     self.plot_base = self.figure.add_axes(self._axes)
    #     if kwargs["labels_font_weight"]:
    #         kwargs["labels_font_weight"] = "heavy"
    #     else:
    #         kwargs["labels_font_weight"] = "normal"
    #
    #     count = len(xvals)
    #     zorder, zorder_offset = 5, 5 + count
    #     label_freq = kwargs["labels_frequency"]
    #
    #     if xlabel not in ["m/z", "Mass (Da)", "Charge"]:
    #         xlabel, ylabel = ylabel, xlabel
    #
    #     ydata = []
    #
    #     if len(labels) == 0:
    #         labels = [" "] * count
    #     yOffset_start = yOffset = kwargs["waterfall_offset"] * (count + 1)
    #
    #     # Find new xlimits
    #     xvals_limit, __ = find_limits_list(xvals, yvals)
    #     xlimits = (np.min(xvals_limit), np.max(xvals_limit))
    #
    #     label_xposition = xlimits[0] + (xlimits[1] * kwargs["labels_x_offset"])
    #     self.text_offset_position = dict(min=xlimits[0], max=xlimits[1], offset=kwargs["labels_x_offset"])
    #
    #     for item in range(len(xvals)):
    #         xval = xvals[item]
    #         yval = yvals[item]
    #         zval = np.array(zvals[item])
    #         line_color = colorList[item]
    #         yOffset = yOffset_start
    #         label = labels[item]
    #
    #         shade_color = colorList[item]
    #         if not kwargs["waterfall_reverse"]:
    #             yval = yval[::-1]
    #             zval = np.fliplr(zval)
    #
    #         for irow in range(len(yval)):
    #             if irow > 0:
    #                 label = ""
    #
    #             zval_one = np.asarray(zval[:, irow])
    #             if kwargs["waterfall_increment"] != 0 and kwargs.get("waterfall_normalize", True):
    #                 zval_one = normalize_1D(zval_one)
    #
    #             y = zval_one + yOffset
    #             self.plot_base.plot(
    #                 xval,
    #                 y,
    #                 color=line_color,
    #                 linewidth=kwargs["spectrum_line_width"],
    #                 linestyle=kwargs["spectrum_line_style"],
    #                 label=label,
    #                 zorder=zorder,
    #             )
    #             if kwargs["spectrum_line_fill_under"] and len(yval) < kwargs.get("shade_under_n_limit", 50):
    #                 shade_kws = dict(
    #                     facecolor=shade_color,
    #                     alpha=kwargs.get("spectrum_fill_transparency", 0.25),
    #                     clip_on=kwargs.get("clip_on", True),
    #                     zorder=zorder - 2,
    #                 )
    #                 self.plot_base.fill_between(xval, np.min(y), y, **shade_kws)
    #
    #             if kwargs.get("add_labels", True) and kwargs["labels_frequency"] != 0 and item == 0:
    #                 x_label = ut_visuals.convert_label(yval[irow], label_format=kwargs["labels_format"])
    #                 if irow % kwargs["labels_frequency"] == 0:
    #                     label_kws = dict(fontsize=kwargs["labels_font_size"], fontweight=kwargs["labels_font_weight"])
    #                     self.plot_add_label(
    #                         xpos=label_xposition,
    #                         yval=yOffset + kwargs["labels_y_offset"],
    #                         label=x_label,
    #                         zorder=zorder + 3,
    #                         **label_kws,
    #                     )
    #             ydata.extend(y)
    #             yOffset = yOffset - kwargs["waterfall_increment"]
    #             zorder = zorder + 5
    #         zorder = zorder + (zorder_offset * 5)
    #
    #     handles, __ = self.plot_base.get_legend_handles_labels()
    #     self.set_legend_parameters(handles, **kwargs)
    #
    #     self.set_plot_xlabel(xlabel, **kwargs)
    #
    #     self.set_tick_parameters(**kwargs)
    #
    #     for __, line in enumerate(self.plot_base.get_lines()):
    #         line.set_linewidth(kwargs["spectrum_line_width"])
    #         line.set_linestyle(kwargs["spectrum_line_style"])
    #
    #     self.plot_base.spines["left"].set_visible(kwargs["axes_frame_spine_left"])
    #     self.plot_base.spines["right"].set_visible(kwargs["axes_frame_spine_right"])
    #     self.plot_base.spines["top"].set_visible(kwargs["axes_frame_spine_top"])
    #     self.plot_base.spines["bottom"].set_visible(kwargs["axes_frame_spine_bottom"])
    #     for i in self.plot_base.spines.values():
    #         i.set_linewidth(kwargs["axes_frame_width"])
    #         i.set_zorder(zorder)
    #
    #     ydata = remove_nan_from_list(ydata)
    #     ylimits = [np.min(ydata) - kwargs["waterfall_offset"], np.max(ydata) + 0.05]
    #     extent = [xlimits[0], ylimits[0], xlimits[1], ylimits[1]]
    #     self.setup_zoom([self.plot_base], self.zoomtype, plotName=plotName, data_lims=extent)
    #     self.plot_base.plot_limits = [xlimits[0], xlimits[1], ylimits[0], ylimits[1]]
    #     # Setup X-axis getter
    #     self.setupGetXAxies([self.plot_base])
    #     self.plot_base.set_xlim([xlimits[0], xlimits[1]])
    #
    # def plot_n_grid_1D_overlay(
    #     self, xvals, yvals, xlabel, ylabel, labels, colors, plotName="Grid_1D", axesSize=None,
    #     testMax="yvals", **kwargs
    # ):
    #     # update settings
    #     self._check_and_update_plot_settings(plot_name=plotName, axes_size=axesSize, **kwargs)
    #
    #     # check in case only one item was passed
    #     # assumes xvals is a list in a list
    #     if len(xvals) != len(yvals) and len(xvals) == 1:
    #         xvals = xvals * len(yvals)
    #
    #     n_xvals = len(xvals)
    #     n_yvals = len(yvals)
    #     n_grid = np.max([n_xvals, n_yvals])
    #     n_rows, n_cols, __, __ = ut_visuals.check_n_grid_dimensions(n_grid)
    #
    #     # set tick size
    #     matplotlib.rc("xtick", labelsize=kwargs["axes_tick_font_size"])
    #     matplotlib.rc("ytick", labelsize=kwargs["axes_tick_font_size"])
    #
    #     gs = gridspec.GridSpec(nrows=n_rows, ncols=n_cols)
    #
    #     # check if labels were added
    #     if "xlabels" in kwargs:
    #         xlabels = kwargs["xlabels"]
    #         if len(xlabels) != n_xvals:
    #             xlabels = [xlabel] * n_xvals
    #     else:
    #         xlabels = [xlabel] * n_xvals
    #
    #     if "ylabels" in kwargs:
    #         ylabels = kwargs["ylabels"]
    #         if len(ylabels) != n_yvals:
    #             ylabels = [ylabel] * n_yvals
    #     else:
    #         ylabels = [ylabel] * n_yvals
    #
    #     plt_list, handles, extent = [], [], []
    #     for i in range(n_grid):
    #         row = int(i // n_cols)
    #         col = i % n_cols
    #
    #         xval = xvals[i]
    #         yval = yvals[i]
    #         color = colors[i]
    #         label = labels[i]
    #         xlabel = xlabels[i]
    #         ylabel = ylabels[i]
    #
    #         xlabel = _replace_labels(xlabel)
    #         ylabel = _replace_labels(ylabel)
    #         #             if testMax == 'yvals':
    #         #                 ydivider, expo = self.testXYmaxValsUpdated(values=yval)
    #         #                 if expo > 1:
    #         #                     offset_text = r'x$\mathregular{10^{%d}}$' % expo
    #         #                     ylabel = ''.join([ylabel, " [", offset_text,"]"])
    #         #                     yval = divide(yval, float(ydivider))
    #         #                 else: ydivider = 1
    #         #                 self.y_divider = ydivider
    #
    #         xmin, xmax = np.min(xval), np.max(xval)
    #         ymin, ymax = np.min(yval), np.max(yval)
    #         extent.append([xmin, ymin, xmax, ymax])
    #         ax = self.figure.add_subplot(gs[row, col], aspect="auto")
    #         ax.plot(
    #             xval, yval, color=color, label=label, linewidth=kwargs["spectrum_line_width"],
    #             linestyle=kwargs["spectrum_line_style"]
    #         )
    #
    #         if kwargs["spectrum_line_fill_under"]:
    #             handles.append(patches.Patch(color=color, label=label, alpha=0.25))
    #             shade_kws = dict(
    #                 facecolor=color,
    #                 alpha=kwargs.get("spectrum_fill_transparency", 0.25),
    #                 clip_on=kwargs.get("clip_on", True),
    #             )
    #             ax.fill_between(xval, 0, yval, **shade_kws)
    #         ax.set_xlim(xmin, xmax)
    #         ax.set_ylim(ymin, ymax)
    #         ax.tick_params(
    #             axis="both",
    #             left=kwargs["axes_frame_ticks_left"],
    #             right=kwargs["axes_frame_ticks_right"],
    #             top=kwargs["axes_frame_ticks_top"],
    #             bottom=kwargs["axes_frame_ticks_bottom"],
    #             labelleft=kwargs["axes_frame_tick_labels_left"],
    #             labelright=kwargs["axes_frame_tick_labels_right"],
    #             labeltop=kwargs["axes_frame_tick_labels_top"],
    #             labelbottom=kwargs["axes_frame_tick_labels_bottom"],
    #         )
    #
    #         # spines
    #         ax.spines["left"].set_visible(kwargs["axes_frame_spine_left"])
    #         ax.spines["right"].set_visible(kwargs["axes_frame_spine_right"])
    #         ax.spines["top"].set_visible(kwargs["axes_frame_spine_top"])
    #         ax.spines["bottom"].set_visible(kwargs["axes_frame_spine_bottom"])
    #
    #         # update axis frame
    #         if kwargs["axes_frame_show"]:
    #             ax.set_axis_on()
    #         else:
    #             ax.set_axis_off()
    #
    #         kwargs["axes_label_pad"] = 5
    #         ax.set_xlabel(
    #             xlabel, labelpad=kwargs["axes_label_pad"], fontsize=kwargs["axes_tick_font_size"],
    #             weight=kwargs["axes_label_font_weight"]
    #         )
    #
    #         ax.set_ylabel(
    #             ylabel, labelpad=kwargs["axes_label_pad"], fontsize=kwargs["axes_tick_font_size"],
    #             weight=kwargs["axes_label_font_weight"]
    #         )
    #
    #         if kwargs.get("legend", CONFIG.legend):
    #             handle, label = ax.get_legend_handles_labels()
    #             ax.legend(
    #                 loc=kwargs.get("legend_position", CONFIG.legendPosition),
    #                 ncol=kwargs.get("legend_n_columns", CONFIG.legendColumns),
    #                 fontsize=kwargs.get("legend_font_size", CONFIG.legendFontSize),
    #                 frameon=kwargs.get("legend_frame", CONFIG.legendFrame),
    #                 framealpha=kwargs.get("legend_transparency", CONFIG.legendAlpha),
    #                 markerfirst=kwargs.get("legend_marker_first", CONFIG.legendMarkerFirst),
    #                 markerscale=kwargs.get("legend_marker_size", CONFIG.legendMarkerSize),
    #                 fancybox=kwargs.get("legend_fancy_box", CONFIG.legendFancyBox),
    #                 scatterpoints=kwargs.get("legend_n_markers", CONFIG.legendNumberMarkers),
    #                 handles=handle,
    #                 labels=label,
    #             )
    #
    #             leg = ax.axes.get_legend()
    #             leg.draggable()
    #         # add plot list
    #         plt_list.append(ax)
    #
    #     gs.tight_layout(self.figure)
    #     self.figure.tight_layout()
    #     #
    #     self.setup_zoom(plt_list, self.zoomtype, data_lims=extent)
    #
    # def plot_n_grid_scatter(
    #     self,
    #     xvals,
    #     yvals,
    #     xlabel,
    #     ylabel,
    #     labels,
    #     colors,
    #     plotName="Grid_scatter",
    #     axesSize=None,
    #     testMax="yvals",
    #     **kwargs,
    # ):
    #     # update settings
    #     self._check_and_update_plot_settings(plot_name=plotName, axes_size=axesSize, **kwargs)
    #
    #     # check in case only one item was passed
    #     # assumes xvals is a list in a list
    #     if len(xvals) != len(yvals) and len(xvals) == 1:
    #         xvals = xvals * len(yvals)
    #
    #     n_xvals = len(xvals)
    #     n_yvals = len(yvals)
    #     n_grid = np.max([n_xvals, n_yvals])
    #     n_rows, n_cols, __, __ = ut_visuals.check_n_grid_dimensions(n_grid)
    #
    #     # convert weights
    #     if kwargs["axes_title_font_weight"]:
    #         kwargs["axes_title_font_weight"] = "heavy"
    #     else:
    #         kwargs["axes_title_font_weight"] = "normal"
    #
    #     if kwargs["axes_label_font_weight"]:
    #         kwargs["axes_label_font_weight"] = "heavy"
    #     else:
    #         kwargs["axes_label_font_weight"] = "normal"
    #
    #     # set tick size
    #     matplotlib.rc("xtick", labelsize=kwargs["axes_tick_font_size"])
    #     matplotlib.rc("ytick", labelsize=kwargs["axes_tick_font_size"])
    #
    #     gs = gridspec.GridSpec(nrows=n_rows, ncols=n_cols)
    #
    #     # check if labels were added
    #     if "xlabels" in kwargs:
    #         xlabels = kwargs["xlabels"]
    #         if len(xlabels) != n_xvals:
    #             xlabels = [xlabel] * n_xvals
    #     else:
    #         xlabels = [xlabel] * n_xvals
    #
    #     if "ylabels" in kwargs:
    #         ylabels = kwargs["ylabels"]
    #         if len(ylabels) != n_yvals:
    #             ylabels = [ylabel] * n_yvals
    #     else:
    #         ylabels = [ylabel] * n_yvals
    #
    #     plt_list, handles, extent = [], [], []
    #     for i in range(n_grid):
    #         row = int(i // n_cols)
    #         col = i % n_cols
    #
    #         xval = xvals[i]
    #         yval = yvals[i]
    #         color = colors[i]
    #         label = labels[i]
    #         xlabel = xlabels[i]
    #         ylabel = ylabels[i]
    #
    #         xlabel = _replace_labels(xlabel)
    #         ylabel = _replace_labels(ylabel)
    #
    #         xmin, xmax = np.min(xval), np.max(xval)
    #         ymin, ymax = np.min(yval), np.max(yval)
    #         extent.append([xmin, ymin, xmax, ymax])
    #         ax = self.figure.add_subplot(gs[row, col], aspect="auto")
    #         ax.scatter(
    #             xval,
    #             yval,
    #             color=color,
    #             marker=kwargs["marker_shape"],
    #             alpha=kwargs["marker_transparency"],
    #             s=kwargs["marker_size"],
    #         )
    #
    #         #                 if plot_modifiers.get("color_items", False) and len(kwargs['item_colors']) > 0:
    #         #                     color = kwargs['item_colors'][0]
    #         #                     try:
    #         #                         plot = self.plotMS.scatter(xval, yval,
    #         #                                                    edgecolors="k",
    #         #                                                     c=color,
    #         #                                                    s=kwargs['scatter_size'],
    #         #                                                    marker=kwargs['scatter_shape'],
    #         #                                                    alpha=kwargs['scatter_alpha'],
    #         #     #                                                label=labels[i],
    #         #                                                    picker=5)
    #         #                     except Exception:
    #         #                         color = colors[i]
    #         #                         plot = self.plotMS.scatter(xval, yval,
    #         #                                                    edgecolors=color,
    #         #                                                    color=color,
    #         #                                                    s=kwargs['scatter_size'],
    #         #                                                    marker=kwargs['scatter_shape'],
    #         #                                                    alpha=kwargs['scatter_alpha'],
    #         #     #                                                label=labels[i],
    #         #                                                    picker=5)
    #         #                 else:
    #         #                     color = colors[i]
    #         #                     plot = self.plotMS.scatter(xval, yval,
    #         #                                                edgecolors=color,
    #         #                                                color=color,
    #         #                                                s=kwargs['scatter_size'],
    #         #                                                marker=kwargs['scatter_shape'],
    #         #                                                alpha=kwargs['scatter_alpha'],
    #         # #                                                label=labels[i],
    #         #                                                picker=5)
    #
    #         ax.set_xlim(xmin, xmax)
    #         ax.set_ylim(ymin, ymax)
    #         ax.tick_params(
    #             axis="both",
    #             left=kwargs["axes_frame_ticks_left"],
    #             right=kwargs["axes_frame_ticks_right"],
    #             top=kwargs["axes_frame_ticks_top"],
    #             bottom=kwargs["axes_frame_ticks_bottom"],
    #             labelleft=kwargs["axes_frame_tick_labels_left"],
    #             labelright=kwargs["axes_frame_tick_labels_right"],
    #             labeltop=kwargs["axes_frame_tick_labels_top"],
    #             labelbottom=kwargs["axes_frame_tick_labels_bottom"],
    #         )
    #
    #         # spines
    #         ax.spines["left"].set_visible(kwargs["axes_frame_spine_left"])
    #         ax.spines["right"].set_visible(kwargs["axes_frame_spine_right"])
    #         ax.spines["top"].set_visible(kwargs["axes_frame_spine_top"])
    #         ax.spines["bottom"].set_visible(kwargs["axes_frame_spine_bottom"])
    #
    #         # update axis frame
    #         if kwargs["axes_frame_show"]:
    #             ax.set_axis_on()
    #         else:
    #             ax.set_axis_off()
    #
    #         kwargs["axes_label_pad"] = 5
    #         ax.set_xlabel(
    #             xlabel, labelpad=kwargs["axes_label_pad"], fontsize=kwargs["axes_tick_font_size"],
    #             weight=kwargs["axes_label_font_weight"]
    #         )
    #
    #         ax.set_ylabel(
    #             ylabel, labelpad=kwargs["axes_label_pad"], fontsize=kwargs["axes_tick_font_size"],
    #             weight=kwargs["axes_label_font_weight"]
    #         )
    #
    #         if kwargs.get("legend", CONFIG.legend):
    #             handle, label = ax.get_legend_handles_labels()
    #             ax.legend(
    #                 loc=kwargs.get("legend_position", CONFIG.legendPosition),
    #                 ncol=kwargs.get("legend_n_columns", CONFIG.legendColumns),
    #                 fontsize=kwargs.get("legend_font_size", CONFIG.legendFontSize),
    #                 frameon=kwargs.get("legend_frame", CONFIG.legendFrame),
    #                 framealpha=kwargs.get("legend_transparency", CONFIG.legendAlpha),
    #                 markerfirst=kwargs.get("legend_marker_first", CONFIG.legendMarkerFirst),
    #                 markerscale=kwargs.get("legend_marker_size", CONFIG.legendMarkerSize),
    #                 fancybox=kwargs.get("legend_fancy_box", CONFIG.legendFancyBox),
    #                 scatterpoints=kwargs.get("legend_n_markers", CONFIG.legendNumberMarkers),
    #                 handles=handle,
    #                 labels=label,
    #             )
    #
    #             leg = ax.axes.get_legend()
    #             leg.draggable()
    #         # add plot list
    #         plt_list.append(ax)
    #
    #     gs.tight_layout(self.figure)
    #     self.figure.tight_layout()
    #     #
    #     self.setup_zoom(plt_list, self.zoomtype, data_lims=extent)
    #
    # def plot_1D_2D(
    #     self,
    #     yvalsRMSF=None,
    #     zvals=None,
    #     labelsX=None,
    #     labelsY=None,
    #     ylabelRMSF="",
    #     xlabelRMSD="",
    #     ylabelRMSD="",
    #     testMax="yvals",
    #     label="",
    #     zoom="box",
    #     plotName="RMSF",
    #     axesSize=None,
    #     **kwargs,
    # ):
    #     """
    #     Plots RMSF and RMSD together
    #     """
    #     # Setup parameters
    #     gs = gridspec.GridSpec(2, 1, height_ratios=[1, 3])
    #     gs.update(hspace=kwargs["rmsf_h_space"])
    #
    #     # update settings
    #     self._check_and_update_plot_settings(plot_name=plotName, axes_size=axesSize, **kwargs)
    #
    #     if kwargs["axes_label_font_weight"]:
    #         kwargs["axes_label_font_weight"] = "heavy"
    #     else:
    #         kwargs["axes_label_font_weight"] = "normal"
    #
    #     # set tick size
    #     matplotlib.rc("xtick", labelsize=kwargs["axes_tick_font_size"])
    #     matplotlib.rc("ytick", labelsize=kwargs["axes_tick_font_size"])
    #
    #     # Check if there are any labels attached with the data
    #     if xlabelRMSD == "":
    #         xlabelRMSD = "Scans"
    #     if ylabelRMSD == "":
    #         ylabelRMSD = "Drift time (bins)"
    #     if ylabelRMSF == "":
    #         ylabelRMSF = "RMSD (%)"
    #
    #     if testMax == "yvals":
    #         ydivider, expo = self.testXYmaxValsUpdated(values=yvalsRMSF)
    #         if expo > 1:
    #             offset_text = r"x$\mathregular{10^{%d}}$" % expo
    #             ylabelRMSF = "".join([ylabelRMSF, " [", offset_text, "]"])
    #             yvalsRMSF = np.divide(yvalsRMSF, float(ydivider))
    #     else:
    #         ylabelRMSF = "RMSD (%)"
    #
    #     # Plot RMSF data (top plot)
    #     if len(labelsX) != len(yvalsRMSF):
    #         DialogBox(title="Missing data", msg="Missing x-axis labels! Cannot execute this action!", kind="Error")
    #         return
    #
    #     self.plotRMSF = self.figure.add_subplot(gs[0], aspect="auto")
    #     self.plotRMSF.plot(
    #         labelsX,
    #         yvalsRMSF,
    #         color=kwargs["rmsf_line_color"],
    #         linewidth=kwargs["rmsf_line_width"],
    #         linestyle=kwargs["rmsf_line_style"],
    #     )
    #
    #     self.plotRMSF.fill_between(
    #         labelsX,
    #         yvalsRMSF,
    #         0,
    #         edgecolor=kwargs["rmsf_line_color"],
    #         facecolor=kwargs["rmsf_fill_color"],
    #         alpha=kwargs["rmsf_fill_transparency"],
    #         hatch=kwargs["rmsf_fill_hatch"],
    #         linewidth=kwargs["rmsf_line_width"],
    #         linestyle=kwargs["rmsf_line_style"],
    #     )
    #
    #     self.plotRMSF.set_xlim([np.min(labelsX), np.max(labelsX)])
    #     self.plotRMSF.set_ylim([0, np.max(yvalsRMSF) + 0.2])
    #     self.plotRMSF.get_xaxis().set_visible(False)
    #
    #     self.plotRMSF.set_ylabel(
    #         ylabelRMSF, labelpad=kwargs["axes_label_pad"], fontsize=kwargs["axes_tick_font_size"],
    #         weight=kwargs["axes_label_font_weight"]
    #     )
    #
    #     extent = ut_visuals.extents(labelsX) + ut_visuals.extents(labelsY)
    #     self.plot_base = self.figure.add_subplot(gs[1], aspect="auto")
    #
    #     self.cax = self.plot_base.imshow(
    #         zvals,
    #         extent=extent,
    #         cmap=kwargs["heatmap_colormap"],
    #         interpolation=kwargs["heatmap_interpolation"],
    #         norm=kwargs["colormap_norm"],
    #         aspect="auto",
    #         origin="lower",
    #     )
    #
    #     xmin, xmax = self.plot_base.get_xlim()
    #     ymin, ymax = self.plot_base.get_ylim()
    #     self.plot_base.set_xlim(xmin, xmax - 0.5)
    #     self.plot_base.set_ylim(ymin, ymax - 0.5)
    #
    #     extent = [labelsX[0], labelsY[0], labelsX[-1], labelsY[-1]]
    #     self.setup_zoom([self.plot_base], self.zoomtype, data_lims=extent, plotName=plotName)
    #     self.plot_base.plot_limits = [extent[0], extent[2], extent[1], extent[3]]
    #
    #     self.set_plot_xlabel(xlabelRMSD, **kwargs)
    #     self.set_plot_ylabel(ylabelRMSD, **kwargs)
    #
    #     # ticks
    #     self.plot_base.tick_params(
    #         axis="both",
    #         left=kwargs["axes_frame_ticks_left"],
    #         right=kwargs["axes_frame_ticks_right"],
    #         top=kwargs["axes_frame_ticks_top"],
    #         bottom=kwargs["axes_frame_ticks_bottom"],
    #         labelleft=kwargs["axes_frame_tick_labels_left"],
    #         labelright=kwargs["axes_frame_tick_labels_right"],
    #         labeltop=kwargs["axes_frame_tick_labels_top"],
    #         labelbottom=kwargs["axes_frame_tick_labels_bottom"],
    #     )
    #
    #     self.plotRMSF.tick_params(
    #         axis="both",
    #         left=kwargs["ticks_left_1D"],
    #         right=kwargs["ticks_right_1D"],
    #         top=kwargs["ticks_top_1D"],
    #         bottom=kwargs["ticks_bottom_1D"],
    #         labelleft=kwargs["tickLabels_left_1D"],
    #         labelright=kwargs["tickLabels_right_1D"],
    #         labeltop=kwargs["tickLabels_top_1D"],
    #         labelbottom=kwargs["tickLabels_bottom_1D"],
    #     )
    #
    #     # spines
    #     self.plot_base.spines["left"].set_visible(kwargs["axes_frame_spine_left"])
    #     self.plot_base.spines["right"].set_visible(kwargs["axes_frame_spine_right"])
    #     self.plot_base.spines["top"].set_visible(kwargs["axes_frame_spine_top"])
    #     self.plot_base.spines["bottom"].set_visible(kwargs["axes_frame_spine_bottom"])
    #     [i.set_linewidth(kwargs["axes_frame_width"]) for i in self.plot_base.spines.values()]
    #
    #     self.plotRMSF.spines["left"].set_visible(kwargs["spines_left_1D"])
    #     self.plotRMSF.spines["right"].set_visible(kwargs["spines_right_1D"])
    #     self.plotRMSF.spines["top"].set_visible(kwargs["spines_top_1D"])
    #     self.plotRMSF.spines["bottom"].set_visible(kwargs["spines_bottom_1D"])
    #     [i.set_linewidth(kwargs["axes_frame_width"]) for i in self.plotRMSF.spines.values()]
    #
    #     # update axis frame
    #     if kwargs["axes_frame_show"]:
    #         self.plot_base.set_axis_on()
    #     else:
    #         self.plot_base.set_axis_off()
    #
    #     if kwargs["axis_onoff_1D"]:
    #         self.plotRMSF.set_axis_on()
    #     else:
    #         self.plotRMSF.set_axis_off()
    #
    #     # update gridspace
    #     self.set_colorbar_parameters(zvals, **kwargs)
    #     gs.tight_layout(self.figure)
    #     self.figure.tight_layout()
