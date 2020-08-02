"""Base class for all mpl-based plotting functionality"""
# Standard library imports
import logging
from copy import copy
from typing import List
from typing import Union
from typing import Optional

# Third-party imports
import numpy as np
import matplotlib
from seaborn import color_palette
from matplotlib import patches
from matplotlib.collections import LineCollection

# Local imports
import origami.utils.visuals as ut_visuals
from origami.utils.misc import merge_two_dicts
from origami.utils.color import get_random_color
from origami.utils.ranges import get_min_max
from origami.config.config import CONFIG
from origami.utils.adjustText import adjust_text
from origami.utils.exceptions import MessageError
from origami.visuals.mpl.panel import MPLPanel
from origami.visuals.utilities import get_intensity_formatter

logger = logging.getLogger(__name__)


class PlotBase(MPLPanel):
    """Generic plot base"""

    PLOT_TYPE = None

    def __init__(self, *args, **kwargs):
        self._axes = kwargs.get("axes_size", [0.12, 0.12, 0.8, 0.8])  # keep track of axes size
        MPLPanel.__init__(self, *args, **kwargs)

        self._plot_flag = False
        self.plot_type = None
        self.plot_base = None

        # only used by the heatmap plots
        self.cax = None

        # only used by the joint plot
        self.plot_joint_x = None
        self.plot_joint_y = None

    def _set_axes(self):
        """Add axis to the figure"""
        self.plot_base = self.figure.add_axes(self._axes)

    def _is_locked(self):
        """Check whether plot is locked"""
        if self.lock_plot_from_updating:
            self._locked()

    def _locked(self):
        """Let user know that the plot is locked"""
        raise MessageError(
            "Plot modification is locked",
            "This plot is locked and you cannot use global setting updated. \n"
            + "Please right-click in the plot area and select Customise plot..."
            + " to adjust plot settings.",
        )

    @staticmethod
    def _check_axes_size(axes_size, min_left=0.12, min_bottom=0.12, max_width=0.8, max_height=0.8):
        try:
            l, b, w, h = axes_size
        except TypeError:
            return axes_size

        axes_size = [max([l, min_left]), max([b, min_bottom]), min([w, max_width]), min([h, max_height])]

        return axes_size

    @staticmethod
    def _compute_multi_xy_limits(xs, ys, y_lower_start=0, y_upper_multiplier=1.0):
        """Calculate x/y axis ranges from multiple arrays"""
        assert isinstance(xs, list)
        assert isinstance(ys, list)

        _xlimits, _ylimits = [], []
        for x, y in zip(xs, ys):
            x_min, x_max = get_min_max(x)
            y_min, y_max = get_min_max(y)
            _xlimits.append([x_min, x_max])
            _ylimits.append([y_min, y_max])

        x_min, x_max = get_min_max(_xlimits)
        y_min, y_max = get_min_max(_ylimits)

        xlimits = [x_min, x_max]
        if y_lower_start is None:
            y_lower_start = y_min
        ylimits = [y_lower_start, y_max * y_upper_multiplier]

        # extent is x_min, y_min, x_max, y_max
        extent = [xlimits[0], ylimits[0], xlimits[1], ylimits[1]]

        return xlimits, ylimits, extent

    @staticmethod
    def _compute_xy_limits(
        x: Union[List, np.ndarray],
        y: Union[List, np.ndarray],
        y_lower_start: Optional[float] = 0,
        y_upper_multiplier: float = 1.0,
        is_heatmap: bool = False,
    ):
        """Calculate the x/y axis ranges"""
        x = np.nan_to_num(x)
        y = np.nan_to_num(y)
        x_min, x_max = get_min_max(x)
        y_min, y_max = get_min_max(y)

        if is_heatmap:
            x_min, x_max = x_min - 0.5, x_max + 0.5
            y_min, y_max = y_min - 0.5, y_max + 0.5

        xlimits = [x_min, x_max]
        if y_lower_start is None:
            y_lower_start = y_min
        ylimits = [y_lower_start, y_max * y_upper_multiplier]

        # extent is x_min, y_min, x_max, y_max
        extent = [xlimits[0], ylimits[0], xlimits[1], ylimits[1]]

        return xlimits, ylimits, extent

    def store_plot_limits(self, extent: List, ax: List = None):
        """Setup plot limits"""
        if ax is None:
            ax = [self.plot_base]

        if not isinstance(ax, list):
            ax = list(ax)

        if len(ax) != len(extent):
            raise ValueError("Could not store plot limits")

        for _ax, _extent in zip(ax, extent):
            _ax.plot_limits = [_extent[0], _extent[2], _extent[1], _extent[3]]

    def get_plot_limits(self, ax=None):
        """Get plot limits"""
        if ax is None:
            ax = self.plot_base
        return ax.plot_limits

    #         self._check_plot_limits(extent)

    #     def _check_plot_limits(self, extent):
    #         """Check whether current plot limits are way-outside of what the new plot expects"""
    #         # get current plot limits
    #         x_min, y_min, x_max, y_max = extent
    #
    #         # get new plot limits
    #         _x_min, _x_max = self.get_xlim()
    #         _y_min, _y_max = self.get_ylim()
    # #         _x_min, _x_max, _y_min, _y_max = self.plot_limits
    #
    #         # check x-axis
    # #         if _x_min < x_min:
    # #             _x_min = x_min
    #         if _x_max > x_max:
    #             _x_max = x_max
    #
    #         # check y-axis
    # #         if _y_min < y_min:
    # #             _y_min = y_min
    #         if _y_max > y_max:
    #             _y_max = y_max
    #
    #         self.set_xy_limits((_x_min, _x_max, _y_min, _y_max))

    def get_xlim(self):
        """Get x-axis limits"""
        plot_limits = self.get_plot_limits()
        return plot_limits[0], plot_limits[1]

    def get_ylim(self):
        """Get y-axis limits"""
        plot_limits = self.get_plot_limits()
        return plot_limits[2], plot_limits[3]

    def _update_plot_settings_(self, **kwargs):
        for parameter in kwargs:
            self.plot_parameters[parameter] = kwargs[parameter]

    def _check_and_update_plot_settings(self, **kwargs):

        # check kwargs
        kwargs = ut_visuals.check_plot_settings(**kwargs)

        # extract plot name
        if "plot_name" in kwargs:
            self.plot_name = kwargs["plot_name"]

        if "axes_size" in kwargs:
            axes_size = kwargs["axes_size"]
        else:
            axes_size = self._axes

        axes_size = self._check_axes_size(axes_size)

        # override parameters
        if not self.lock_plot_from_updating:
            if axes_size is not None:
                self._axes = axes_size
            self.plot_parameters = kwargs
        else:
            kwargs = merge_two_dicts(kwargs, self.plot_parameters)
            self.plot_parameters = kwargs

    def _plot_settings_(self, **kwargs):
        """
        Setup all plot parameters for easy retrieval
        """
        self.plot_kwargs = kwargs

    def copy_to_clipboard(self):
        """Copy canvas to clipboard"""
        self.canvas.Copy_to_Clipboard()
        logger.debug("Figure was copied to the clipboard")

    def set_legend_parameters(self, handles=None, **kwargs):
        """Add legend to the plot

        Parameters
        ----------
        handles: legend handles
            list of legend handles or None
        **kwargs: dict
            dictionary with all plot parameters defined by the user
        """
        # legend
        self.plot_remove_legend()
        if kwargs.get("legend", CONFIG.legend):
            legend = self.plot_base.legend(
                loc=kwargs.get("legend_position", CONFIG.legend_position),
                ncol=kwargs.get("legend_num_columns", CONFIG.legend_columns),
                fontsize=kwargs.get("legend_font_size", CONFIG.legend_font_size),
                frameon=kwargs.get("legend_frame_on", CONFIG.legend_frame),
                framealpha=kwargs.get("legend_transparency", CONFIG.legend_transparency),
                markerfirst=kwargs.get("legend_marker_first", CONFIG.legend_marker_first),
                markerscale=kwargs.get("legend_marker_size", CONFIG.legend_marker_size),
                fancybox=kwargs.get("legend_fancy_box", CONFIG.legend_fancy_box),
                scatterpoints=kwargs.get("legend_num_markers", CONFIG.legend_n_markers),
                handles=handles,
            )
            if "legend_zorder" in kwargs:
                legend.set_zorder(kwargs.pop("legend_zorder"))
            legend.set_draggable(True)

    def plot_remove_legend(self):
        """Remove legend from the plot area"""
        try:
            leg = self.plot_base.axes.get_legend()
            leg.remove()
        except (AttributeError, KeyError):
            logger.warning("Could not remove legend from the plot area - did it exist?")

    def set_plot_xlabel(self, xlabel: str, **kwargs):
        """Set plot x-axis label"""
        kwargs = ut_visuals.check_plot_settings(**kwargs)

        if xlabel is None:
            xlabel = self.plot_base.get_xlabel()
        self.plot_base.set_xlabel(
            xlabel, labelpad=kwargs["label_pad"], fontsize=kwargs["label_size"], weight=kwargs["label_weight"]
        )
        self.plot_labels["xlabel"] = xlabel

    def set_plot_ylabel(self, ylabel: str, **kwargs):
        """Set plot y-axis label"""
        kwargs = ut_visuals.check_plot_settings(**kwargs)
        if ylabel is None:
            ylabel = self.plot_base.get_ylabel()
        self.plot_base.set_ylabel(
            ylabel, labelpad=kwargs["label_pad"], fontsize=kwargs["label_size"], weight=kwargs["label_weight"]
        )
        self.plot_labels["ylabel"] = ylabel

    def set_plot_title(self, title: str, **kwargs):
        """Set plot title"""
        kwargs = ut_visuals.check_plot_settings(**kwargs)

        if title is None:
            title = self.plot_base.get_title()

        self.plot_base.set_title(title, fontsize=kwargs["title_size"], weight=kwargs.get("label_weight", "normal"))

    def set_tick_parameters(self, **kwargs):
        """Set tick parameters"""

        matplotlib.rc("xtick", labelsize=kwargs["tick_size"])
        matplotlib.rc("ytick", labelsize=kwargs["tick_size"])

        # update axis frame
        if kwargs["axis_onoff"]:
            self.plot_base.set_axis_on()
        else:
            self.plot_base.set_axis_off()

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
            labelsize=kwargs["tick_size"],
        )

        # prevent scientific notation
        try:
            self.plot_base.get_xaxis().get_major_formatter().set_useOffset(False)
        except AttributeError:
            logger.warning("Could not fully set label offsets", exc_info=False)

        # setup borders
        self.plot_base.spines["left"].set_visible(kwargs["spines_left"])
        self.plot_base.spines["right"].set_visible(kwargs["spines_right"])
        self.plot_base.spines["top"].set_visible(kwargs["spines_top"])
        self.plot_base.spines["bottom"].set_visible(kwargs["spines_bottom"])
        [i.set_linewidth(kwargs["frame_width"]) for i in self.plot_base.spines.values()]

    # def _convert_yaxis(self, values, label, set_divider=True, convert_values=True):
    #     """ Function to check whether x/y axis labels do not need formatting """
    #
    #     increment = 10
    #     divider = 1
    #
    #     try:
    #         itemShape = values.shape
    #     except Exception:
    #         values = np.array(values)
    #         itemShape = values.shape
    #
    #     if len(itemShape) > 1:
    #         maxValue = np.amax(np.absolute(values))
    #     elif len(itemShape) == 1:
    #         maxValue = np.max(np.absolute(values))
    #     else:
    #         maxValue = values
    #
    #     while 10 <= (maxValue / divider) >= 1:
    #         divider = divider * increment
    #
    #     expo = len(str(divider)) - len(str(divider).rstrip("0"))
    #
    #     if expo == 1:
    #         divider = 1
    #
    #     label = ut_visuals.add_exponent_to_label(label, divider)
    #     if expo > 1:
    #         if convert_values:
    #             values = np.divide(values, float(divider))
    #
    #     if set_divider:
    #         self.y_divider = divider
    #
    #     return values, label, divider
    #
    # def _convert_yaxis_with_preset_divider(self, values, label):
    #     if self.y_divider is None:
    #         __, __, __ = self._convert_yaxis(values, label)
    #
    #     divider = self.y_divider
    #     expo = len(str(divider)) - len(str(divider).rstrip("0"))
    #
    #     if expo > 1:
    #         offset_text = r"x$\mathregular{10^{%d}}$" % expo
    #         label = "".join([label, " [", offset_text, "]"])
    #
    #     values = np.divide(values, float(divider))
    #
    #     return values, label, divider
    #
    # def _get_colors(self, n_colors):
    #     if CONFIG.currentPalette not in ["Spectral", "RdPu"]:
    #         palette = CONFIG.currentPalette.lower()
    #     else:
    #         palette = CONFIG.currentPalette
    #     colorlist = color_palette(palette, n_colors)
    #
    #     return colorlist
    #
    # def _convert_yaxis_list(self, values, label):
    #
    #     # compute divider(s)
    #     _dividers = []
    #     for _, value in enumerate(values):
    #         __, __ylabel, divider = self._convert_yaxis(value, label, set_divider=False, convert_values=False)
    #         _dividers.append(divider)
    #
    #     # update divider
    #     self.y_divider = np.max(_dividers)
    #
    #     for i, value in enumerate(values):
    #         values[i] = np.divide(value, float(divider))
    #
    #     label = ut_visuals.add_exponent_to_label(label, self.y_divider)
    #
    #     return values, label
    #
    # def _check_colormap(self, cmap=None, **kwargs):
    #     #         # checking entire dict
    #     #         if cmap is None:
    #     #             if kwargs["colormap"] in CONFIG.cmocean_cmaps:
    #     #                 kwargs["colormap"] = eval("cmocean.cm.%s" % kwargs["colormap"])
    #     #             return kwargs
    #     #
    #     #         # only checking colormap
    #     #         if cmap in CONFIG.cmocean_cmaps:
    #     #             cmap = eval("cmocean.cm.%s" % cmap)
    #     return cmap

    def _fix_label_positions(self, lim=20):
        """
        Try to fix position of labels to prevent overlap
        """
        try:
            adjust_text(self.text, lim=lim)
        except (AttributeError, KeyError, ValueError):
            logger.warning("Failed to fix label position", exc_info=True)

    def get_xy_limits(self) -> List[float]:
        """Get x- and y-axis limits that are currently shown in the plot"""
        xmin, xmax = self.plot_base.get_xlim()
        ymin, ymax = self.plot_base.get_ylim()

        return [xmin, xmax, ymin, ymax]

    def set_xy_limits(self, xy_limits: List[float]):
        """Set x- and y-axis limits"""
        xmin, xmax, ymin, ymax = xy_limits

        self.plot_base.set_xlim([xmin, xmax])
        self.plot_base.set_ylim([ymin, ymax])

        self.update_extents([[xmin, ymin, xmax, ymax]])

    def on_zoom_x_axis(self, start_x=None, end_x=None):
        """Horizontal zoom"""
        _start_x, _end_x, _, _ = self.get_xy_limits()
        if start_x is None:
            start_x = _start_x
        if end_x is None:
            end_x = _end_x

        self.plot_base.set_xlim([start_x, end_x])

    def on_zoom_y_axis(self, start_y=None, end_y=None):
        """Vertical zoom"""
        _, _, _start_y, _end_y = self.get_xy_limits()
        if start_y is None:
            start_y = _start_y
        if end_y is None:
            end_y = _end_y

        self.plot_base.set_ylim([start_y, end_y])

    def on_zoom_xy_axis(self, start_x: float, end_x: float, start_y: float, end_y: float):
        """Horizontal and vertical zoom"""
        _start_x, _end_x, _start_y, _end_y = self.get_xy_limits()
        if start_x is None:
            start_x = _start_x
        if end_x is None:
            end_x = _end_x
        if start_y is None:
            start_y = _start_y
        if end_y is None:
            end_y = _end_y

        self.plot_base.axis([start_x, end_x, start_y, end_y])

    def on_set_zoom_state(self, start_x: float, end_x: float, start_y: float, end_y: float):
        """Set horizontal and vertical zoom only if the desired range is accessible by the plot area"""
        _start_x, _end_x, _start_y, _end_y = self.get_xy_limits()

        if end_x > _end_x:
            end_x = _end_x
        if start_x > _end_x or start_x > end_x:
            start_x = _start_x
        if end_y > _end_y:
            end_y = _end_y
        if start_y > _end_y or start_y > end_y:
            start_y = _start_y
        self.plot_base.axis([start_x, end_x, start_y, end_y])

    def on_reset_zoom(self):
        """Reset plot zoom"""
        start_x, end_x, start_y, end_y = self.get_plot_limits()
        self.plot_base.set_xlim(start_x, end_x)
        self.plot_base.set_ylim(start_y, end_y)
        self.repaint()

    def plot_add_arrow(self, arrow_vals: List[float], stick_to_intensity: bool = True, **kwargs):
        """Add arrow to the plot"""
        # unpack parameters
        xmin, ymin, dx, dy = arrow_vals

        obj_name = kwargs.pop("text_name", None)
        obj_props = kwargs.pop("props", [None, None])

        if obj_name is not None:
            self._remove_existing_arrow(obj_name)

        if stick_to_intensity:
            try:
                ymin = np.divide(ymin, self.y_divider)
                dy = np.divide(dy, self.y_divider)
            except Exception:  # noqa
                pass

        if dx == 0 and dy == 0:
            return

        # get custom name tag
        arrow = self.plot_base.arrow(
            xmin,
            ymin,
            dx,
            dy,
            head_length=kwargs.get("arrow_head_length", 0),
            head_width=kwargs.get("arrow_head_width", 0),
            fc=kwargs.get("arrow_face_color", (0.5, 0.5, 0.5)),
            ec=kwargs.get("arrow_edge_color", (0.5, 0.5, 0.5)),
            lw=kwargs.get("arrow_line_width", 0.5),
            ls=kwargs.get("arrow_line_style", ":"),
        )
        arrow.obj_name = obj_name  # custom tag
        arrow.obj_props = obj_props
        arrow.y_divider = self.y_divider

        self.arrows.append(arrow)

    def plot_remove_arrows(self, repaint: bool = True):
        """Remove arrows from the plot"""
        for arrow in self.arrows:
            try:
                arrow.remove()
            except Exception:  # noqa
                pass

        self.arrows = []
        self.repaint(repaint)

    def plot_add_markers(
        self, x: np.ndarray, y: np.ndarray, label: str = "", marker: str = "o", color="r", size: float = 15, **kwargs
    ):
        """Add markers (scatter points) to the plot area"""

        markers = self.plot_base.scatter(
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
        self.markers.append(markers)

    def plot_remove_markers(self, repaint: bool = True):
        """Remove markers (scatter points) from the plot area"""
        for marker in self.markers:
            try:
                marker.remove()
            except Exception:  # noqa
                pass

        self.markers = []
        self.repaint(repaint)

    # def plot_remove_lines(self, label_starts_with: str):
    #     """Remove plot lines from the plot area"""
    #     try:
    #         lines = self.plot_base.get_lines()
    #     except AttributeError:
    #         raise MessageError("Error", "Please plot something first")
    #     for line in lines:
    #         line_label = line.get_label()
    #         if line_label.startswith(label_starts_with):
    #             line.remove()

    def plot_remove_patch_with_label(self, label: str):
        """Remove patch with specific label

        Parameters
        ----------
        label : str
            label that was set on the patch object
        """

        if len(self.patch) == 0:
            return

        for i, patch in enumerate(self.patch):
            if hasattr(patch, "obj_name") and patch.obj_name == label:
                try:
                    patch.remove()
                    del self.patch[i]
                except Exception:  # noqa
                    return

    def _remove_existing_label(self, name_tag: str):
        """Remove label with specific name tag"""
        for i, text in enumerate(self.text):
            if text.obj_name == name_tag:
                text.remove()
                del self.text[i]
                break

    def _remove_existing_arrow(self, name_tag: str):
        """Remove arrow with specific name tag"""
        for i, arrow in enumerate(self.arrows):
            if arrow.obj_name == name_tag:
                arrow.remove()
                del self.arrows[i]
                break

    def _remove_existing_line(self, name_tag: str):
        """Remove line with specific name tag"""
        for i, line in enumerate(self.lines):
            if line.obj_name == name_tag:
                line.remove()
                del self.lines[i]
                break

    def _remove_existing_patch(self, name_tag: str):
        """Remove patch with specific name tag"""
        for i, patch in enumerate(self.patch):
            if patch.obj_name == name_tag:
                patch.remove()
                del self.patch[i]
                break

    # def add_labels(self, x, y, labels, **kwargs):
    #     """Add labels to the plot"""
    #     if not isinstance(x, (list, tuple, np.ndarray)):
    #         x = [x]
    #     if not isinstance(y, (list, tuple, np.ndarray)):
    #         y = [y]
    #     if not isinstance(labels, (list, tuple, np.ndarray)):
    #         labels = [labels]
    #
    #     pass
    #
    # def plot_add_text_and_lines(
    #     self,
    #     xpos,
    #     yval,
    #     label,
    #     vline=True,
    #     vline_position=None,
    #     color="black",
    #     yoffset=0.05,
    #     stick_to_intensity=False,
    #     **kwargs,
    # ):
    #     obj_name = kwargs.pop("text_name", None)
    #     if obj_name is not None:
    #         self._remove_existing_label(obj_name)
    #
    #     try:
    #         ymin, ymax = self.plot_base.get_ylim()
    #     except AttributeError:
    #         raise MessageError("Error", "Please plot something first")
    #
    #     if stick_to_intensity:
    #         try:
    #             y_position = np.divide(yval, self.y_divider)
    #         except Exception:
    #             y_position = ymax
    #     else:
    #         y_position = ymax
    #
    #     # get custom name tag
    #
    #     text = self.plot_base.text(
    #         np.array(xpos),
    #         y_position + yoffset,
    #         label,
    #         horizontalalignment=kwargs.pop("horizontalalignment", "center"),
    #         verticalalignment=kwargs.pop("verticalalignment", "top"),
    #         color=color,
    #         clip_on=True,
    #         picker=True,
    #         **kwargs,
    #     )
    #     text.obj_name = obj_name  # custom tag
    #     text.y_divider = self.y_divider
    #     self.text.append(text)
    #
    #     if vline:
    #         if vline_position is not None:
    #             xpos = vline_position
    #         line = self.plot_base.axvline(xpos, ymin, yval * 0.8, color=color, linestyle="dashed", alpha=0.4)
    #         self.lines.append(line)

    def plot_add_label(
        self,
        x: float,
        y: float,
        label: str,
        color="black",
        y_offset: float = 0.0,
        zorder: int = 3,
        pickable: bool = True,
        **kwargs,
    ):
        """Add label to the plot at a specified x and y position"""
        is_butterfly = kwargs.pop("butterfly_plot", False)

        # check if value should be scaled based on the exponential
        if kwargs.pop("check_yscale", False):
            try:
                y = np.divide(y, self.y_divider)
            except Exception:  # noqa
                pass

        # reverse value
        if is_butterfly:
            try:
                y = -y
                y_offset = -y_offset
            except Exception:  # noqa
                pass

        y = y + y_offset
        text_name = kwargs.pop("text_name", None)
        # this will offset the intensity of the label by small value
        if kwargs.pop("add_arrow_to_low_intensity", False):
            plot_limits = self.get_plot_limits()
            if is_butterfly:
                if (y - y_offset) > 0.2 * plot_limits[2]:
                    rand_offset = -np.random.uniform(high=0.75 * plot_limits[2])
                    yval_old = y - y_offset
                    y -= rand_offset
                    arrow_vals = [x, yval_old, 0, y - yval_old]
                    self.plot_add_arrow(arrow_vals, stick_to_intensity=False)
            else:
                if (y - y_offset) < 0.2 * plot_limits[3]:
                    rand_offset = np.random.uniform(high=0.5 * plot_limits[3])
                    yval_old = y - y_offset
                    y += rand_offset
                    arrow_vals = [x, yval_old, 0, y - yval_old]
                    self.plot_add_arrow(arrow_vals, stick_to_intensity=False)

        text = self.plot_base.text(
            np.array(x), y + y_offset, label, color=color, clip_on=True, zorder=zorder, picker=pickable, **kwargs
        )
        text._yposition = y - kwargs.get("labels_y_offset", CONFIG.waterfall_labels_y_offset)
        text.obj_name = text_name  # custom tag
        text.y_divider = self.y_divider
        self.text.append(text)

    def plot_remove_label(self, repaint: bool = True):
        """Remove label from the plot area"""
        for text in self.text:
            try:
                text.remove()
            except Exception:  # noqa
                pass

        self.text = []
        self.repaint(repaint)

    def plot_add_labels(self, xs, ys, labels, color="black", pickable: bool = True, repaint: bool = False, **kwargs):
        """Add multiple labels to the plot"""
        self.plot_remove_label(repaint)
        for x, y, label in zip(xs, ys, labels):
            self.plot_add_label(x, y, label, color=color, pickable=pickable, **kwargs)
        self.repaint(repaint)

    def plot_add_patch(
        self,
        xmin: float,
        ymin: float,
        width: float,
        height: float,
        color="r",
        alpha: float = 0.5,
        linewidth: float = 0,
        add_temporary: bool = False,
        label: str = "",
        pickable: bool = True,
        **kwargs,  # noqa
    ):
        """Add patch to the plot area"""
        if label not in [None, ""]:
            self._remove_existing_patch(label)

        # height can be defined as None to force retrieval of the highest value in the plot
        if height is None:
            height = self.get_ylim()[-1]

        # check if need to rescale height
        try:
            height = np.divide(height, self.y_divider)
        except Exception:  # noqa
            pass

        try:
            patch = self.plot_base.add_patch(
                patches.Rectangle(
                    (xmin, ymin),
                    width,
                    height,
                    color=color,
                    alpha=alpha,
                    linewidth=linewidth,
                    picker=pickable,
                    edgecolor="k",
                )
            )
        except AttributeError:
            logger.warning("Please plot something first")
            return

        # set label
        patch.obj_name = label
        patch.y_divider = self.y_divider

        if add_temporary:
            self.plot_remove_temporary()
            self.temporary.append(patch)
        else:
            self.patch.append(patch)

    def plot_remove_patches(self, repaint: bool = True):
        """Remove patch fr-om the plot area"""
        for patch in self.patch:
            try:
                patch.remove()
            except Exception:  # noqa
                pass

        self.patch = []
        self.repaint(repaint)

    def plot_add_line(self, xmin: float, xmax: float, ymin: float, ymax: float, orientation: str, label="temporary"):
        """Add vertical or horizontal line to the plot area"""

        if label is not None:
            self._remove_existing_line(label)

        if orientation == "vertical":
            line = self.plot_base.axvline(xmin, 0, 1, color="r", linestyle="dashed", alpha=0.7)
        else:
            line = self.plot_base.axhline(ymin / self.y_divider, 0, 1, color="r", linestyle="dashed", alpha=0.7)

        # add name to the line for future removal
        line.obj_name = label
        self.lines.append(line)

    def plot_remove_temporary(self, repaint=False):
        """Remove temporary patch from the plot area"""
        for patch in self.temporary:
            try:
                patch.remove()
            except Exception:  # noqa
                pass

        self.temporary = []
        self.repaint(repaint)

    def plot_remove_lines(self, repaint: bool = True):
        """Remove label from the plot area"""
        for line in self.lines:
            try:
                line.remove()
            except Exception:  # noqa
                pass

        self.lines = []
        self.repaint(repaint)

    def plot_remove_text_and_lines(self, repaint: bool = True):
        """Remove labels and lines from the plot area"""
        self.plot_remove_label(False)
        self.plot_remove_lines(False)
        self.plot_remove_arrows(False)
        self.repaint(repaint)

    def plot_waterfall_update(self, x: np.ndarray, y: np.ndarray, array: np.ndarray, name: str, **kwargs):
        """Generic waterfall update function"""
        self._is_locked()

        if name.startswith("waterfall."):
            name = name.split("waterfall.")[-1]

        if name.startswith("line") or name.startswith("fill"):
            self.plot_waterfall_update_line_style(array, **kwargs)
        elif name.startswith("label"):
            if name.endswith(".reset"):
                self.plot_waterfall_reset_label(x, y, array, **kwargs)
            else:
                self.plot_waterfall_update_label(**kwargs)

    def plot_waterfall_update_line_style(self, array, **kwargs):
        """Update waterfall lines"""
        n_signals = array.shape[1]
        lc, fc = self.get_waterfall_colors(n_signals, **kwargs)
        for collection in self.plot_base.collections:
            if isinstance(collection, LineCollection):
                collection.set_linestyle(kwargs["line_style"])
                collection.set_linewidth(kwargs["line_width"])
                collection.set_edgecolors(lc)
                if kwargs["shade_under"]:
                    collection.set_facecolors(fc)
                else:
                    collection.set_facecolors([])

    def plot_waterfall_reset_label(self, x, y, array, **kwargs):
        """Update waterfall labels"""
        _, _, label_x, label_y, label_text = self._prepare_waterfall(x, y, array, **kwargs)
        if kwargs["add_labels"]:
            self.plot_add_labels(
                label_x,
                label_y,
                label_text,
                pickable=False,
                repaint=False,
                **self._get_waterfall_label_kwargs(**kwargs),
            )
        else:
            self.plot_remove_label(False)

    def plot_waterfall_update_label(self, **kwargs):
        """Update waterfall labels"""
        _kwargs = self._get_waterfall_label_kwargs(**kwargs)
        for label in self.text:
            label.set_fontweight(_kwargs["fontweight"])
            label.set_fontsize(_kwargs["fontsize"])
            label.set_horizontalalignment(_kwargs["horizontalalignment"])
            label.set_verticalalignment(_kwargs["verticalalignment"])

    # def    plot_1D_waterfall_update(self, which="other", **kwargs):
    #
    #     if self.lock_plot_from_updating:
    #         self._locked()
    #
    #     kwargs = ut_visuals.check_plot_settings(**kwargs)
    #
    #     if self.plot_name == "Waterfall_overlay" and which in ["color", "data"]:
    #         return
    #
    #     if which in ["other", "style"]:
    #         self.plot_1d_waterfall_update_style(**kwargs)
    #
    #     elif which == "color":
    #         self.plot_1d_waterfall_update_color(**kwargs)
    #
    #     elif which == "shade":
    #         self.plot_1d_waterfall_update_shade(**kwargs)
    #
    #     elif which == "label":
    #         self.plot_1d_waterfall_update_label(**kwargs)
    #
    #     elif which == "data":
    #         self.plot_1d_waterfall_data(**kwargs)
    #
    #     elif which == "frame":
    #         self.set_tick_parameters(**kwargs)
    #
    #     elif which == "fonts":
    #         self.plot_1d_waterfall_fonts(**kwargs)
    #
    #     self.plot_parameters = kwargs
    #
    # def plot_1d_waterfall_update_style(self, **kwargs):
    #     if self.plot_name != "Violin":
    #         for i, line in enumerate(self.plot_base.get_lines()):
    #             line.set_linestyle(kwargs["line_style"])
    #             line.set_linewidth(kwargs["line_width"])
    #     else:
    #         for shade in range(len(self.plot_base.collections)):
    #             self.plot_base.collections[shade].set_linestyle(kwargs["line_style"])
    #             self.plot_base.collections[shade].set_linewidth(kwargs["line_width"])
    #
    # def plot_1d_waterfall_update_color(self, **kwargs):
    #     n_colors = len(self.plot_base.get_lines())
    #     n_patch_colors = len(self.plot_base.collections)
    #     if n_colors != n_patch_colors:
    #         if n_patch_colors > n_colors:
    #             n_colors = n_patch_colors
    #
    #     # get colorlist
    #     colorlist = self._get_colorlist(None, n_colors, which="shade", **kwargs)
    #
    #     if self.plot_name != "Violin":
    #         for i, line in enumerate(self.plot_base.get_lines()):
    #             if kwargs["line_color_as_shade"]:
    #                 line_color = colorlist[i]
    #             else:
    #                 line_color = kwargs["line_color"]
    #             line.set_color(line_color)
    #     else:
    #         for i in range(len(self.plot_base.collections)):
    #             if kwargs["line_color_as_shade"]:
    #                 line_color = colorlist[i]
    #             else:
    #                 line_color = kwargs["line_color"]
    #             self.plot_base.collections[i].set_edgecolor(line_color)
    #
    #     for shade in range(len(self.plot_base.collections)):
    #         shade_color = colorlist[shade]
    #         self.plot_base.collections[shade].set_facecolor(shade_color)
    #
    # def plot_1d_waterfall_update_shade(self, **kwargs):
    #     try:
    #         for shade in range(len(self.plot_base.collections)):
    #             self.plot_base.collections[shade].set_alpha(kwargs["shade_under_transparency"])
    #     except AttributeError:
    #         logger.warning("Could not update waterfall underlines")
    #
    # def plot_1d_waterfall_update_label(self, **kwargs):
    #
    #     # calculate new position
    #     label_xposition = self.text_offset_position["min"] + (
    #         self.text_offset_position["max"] * kwargs["labels_x_offset"]
    #     )
    #
    #     if not isinstance(self.text, list):
    #         logger.warning("Could not update waterfall labels - are they plotted?")
    #         return
    #
    #     for text_obj in self.text:
    #         if not kwargs["add_labels"]:
    #             text_obj.set_visible(False)
    #         else:
    #             text_obj.set_fontweight(kwargs["labels_font_weight"])
    #             text_obj.set_fontsize(kwargs["labels_font_size"])
    #             yposition = text_obj._yposition + kwargs["labels_y_offset"]
    #             text_obj.set_position([label_xposition, yposition])
    #             text = ut_visuals.convert_label(text_obj.get_text(), label_format=kwargs["labels_format"])
    #             text_obj.set_text(text)
    #
    # def plot_1d_waterfall_data(self, **kwargs):
    #     # TODO: needs to respect labels
    #     # TODO: needs to respect shade
    #     # TODO: fix an issue when there is shade under the curve
    #     # fix might be here: https://stackoverflow.com/questions/16120801/matplotlib-animate-fill-between-shape
    #     #         count = 0
    #     increment = kwargs["increment"] - self.plot_parameters["increment"]
    #     offset = kwargs["offset"]  # - self.plot_parameters['offset']
    #
    #     # some presets
    #     label_kws = dict(fontsize=kwargs["labels_font_size"], fontweight=kwargs["labels_font_weight"])
    #     shade_kws = dict(alpha=kwargs.get("shade_under_transparency", 0.25), clip_on=kwargs.get("clip_on", True))
    #
    #     # collect information about underlines
    #     collection_info = dict()
    #     for i, shade in enumerate(self.plot_base.collections):
    #         collection_info[i] = [shade.get_zorder(), shade.get_facecolor()]
    #     self.plot_base.collections.clear()
    #
    #     label_info = dict()
    #     for i, text in enumerate(self.text):
    #         label_info[i] = [text._text, text.get_zorder(), text.get_position()[0]]
    #     self.plot_remove_label(False)
    #
    #     if kwargs["reverse"] and label_info:
    #         logger.warning(
    #             "When 'reverse' is set to True, labels cannot be changed so they are removed. You have to"
    #             " fully replot the waterfall plot."
    #         )
    #         label_info.clear()
    #
    #     ydata, y_offset, i_text = [], 0, 0
    #     n_count = len(self.plot_base.get_lines())
    #     for i, line in enumerate(self.plot_base.get_lines()):
    #         xvals = line.get_xdata()
    #         yvals = line.get_ydata()
    #         # indication that waterfall plot is actually shown
    #         if len(yvals) > 5:
    #             y = yvals + y_offset
    #             y_min, y_max = get_min_max(y)
    #             line.set_ydata(y)
    #
    #             # update labels
    #             if label_info:
    #                 if i % kwargs["labels_frequency"] == 0 or i == n_count - 1:
    #                     self.plot_add_label(
    #                         x=label_info[i_text][2],
    #                         y=y_min + kwargs["labels_y_offset"],
    #                         label=label_info[i_text][0],
    #                         zorder=label_info[i_text][1],
    #                         **label_kws,
    #                     )
    #                     i_text += 1
    #
    #             # add underline data if present
    #             if collection_info:
    #                 shade_kws.update(zorder=collection_info[i][0], facecolor=collection_info[i][1])
    #                 self.plot_base.fill_between(xvals, y_min, y, **shade_kws)
    #
    #             ydata.extend([y_min, y_max])
    #             y_offset = y_offset - increment
    #
    #     # # update extents
    #     # ydata = remove_nan_from_list(ydata)
    #     # self.plot_limits[2] = np.min(ydata) - offset
    #     # self.plot_limits[3] = np.max(ydata) + 0.05
    #     # extent = [self.plot_limits[0], self.plot_limits[2], self.plot_limits[1], self.plot_limits[3]]
    #     # self.update_extents(extent)
    #     # self.plot_base.set_xlim((self.plot_limits[0], self.plot_limits[1]))
    #     # self.plot_base.set_ylim((self.plot_limits[2], self.plot_limits[3]))
    #
    # def plot_1d_waterfall_fonts(self, **kwargs):
    #     # update ticks
    #     matplotlib.rc("xtick", labelsize=kwargs["tick_size"])
    #     matplotlib.rc("ytick", labelsize=kwargs["tick_size"])
    #
    #     # update labels
    #     self.set_plot_xlabel(None, **kwargs)
    #     self.set_plot_ylabel(None, **kwargs)
    #
    #     # Setup font size info
    #     self.plot_base.tick_params(labelsize=kwargs["tick_size"])
    #
    # def plot_1D_update(self, **kwargs):
    #     if self.lock_plot_from_updating:
    #         self._locked()
    #
    #     # update plot labels
    #     self.set_plot_xlabel(None, **kwargs)
    #     self.set_plot_ylabel(None, **kwargs)
    #     self.set_tick_parameters(**kwargs)
    #
    #     # update line settings
    #     for __, line in enumerate(self.plot_base.get_lines()):
    #         line.set_linewidth(kwargs["line_width"])
    #         line.set_linestyle(kwargs["line_style"])
    #         line.set_color(kwargs["line_color"])
    #
    #     # add shade if it has been previously deleted
    #     if kwargs["shade_under"] and not self.plot_base.collections:
    #         xvals, yvals, _, _, _ = self.plot_1D_get_data(use_divider=False)
    #         self.plot_1d_add_under_curve(xvals[0], yvals[0], **kwargs)
    #
    #     for __, shade in enumerate(self.plot_base.collections):
    #         if not kwargs["shade_under"]:
    #             shade.remove()
    #         else:
    #             shade.set_facecolor(kwargs["shade_under_color"])
    #             shade.set_alpha(kwargs["shade_under_transparency"])
    #
    #     self._update_plot_settings_(**kwargs)

    # def plot_1D_update_rmsf(self, **kwargs):
    #     if self.lock_plot_from_updating:
    #         self._locked()
    #
    #     if any([plot is None for plot in [self.plotRMSF, self.plot_base]]):
    #         return
    #
    #     # ensure correct format of kwargs
    #     kwargs = ut_visuals.check_plot_settings(**kwargs)
    #
    #     # update ticks
    #     matplotlib.rc("xtick", labelsize=kwargs["tick_size"])
    #     matplotlib.rc("ytick", labelsize=kwargs["tick_size"])
    #
    #     # update labels
    #     for plot_obj in [self.plotRMSF, self.plot_base]:
    #         # Setup font size info
    #         plot_obj.set_ylabel(
    #             plot_obj.get_ylabel(),
    #             labelpad=kwargs["label_pad"],
    #             fontsize=kwargs["label_size"],
    #             weight=kwargs["label_weight"],
    #         )
    #         plot_obj.set_ylabel(
    #             plot_obj.get_ylabel(),
    #             labelpad=kwargs["label_pad"],
    #             fontsize=kwargs["label_size"],
    #             weight=kwargs["label_weight"],
    #         )
    #
    #         plot_obj.tick_params(labelsize=kwargs["tick_size"])
    #
    #         # update axis frame
    #         plot_obj.set_axis_on() if kwargs["axis_onoff"] else plot_obj.set_axis_off()
    #
    #         plot_obj.tick_params(
    #             axis="both",
    #             left=kwargs["ticks_left"],
    #             right=kwargs["ticks_right"],
    #             top=kwargs["ticks_top"],
    #             bottom=kwargs["ticks_bottom"],
    #             labelleft=kwargs["tickLabels_left"],
    #             labelright=kwargs["tickLabels_right"],
    #             labeltop=kwargs["tickLabels_top"],
    #             labelbottom=kwargs["tickLabels_bottom"],
    #         )
    #
    #         plot_obj.spines["left"].set_visible(kwargs["spines_left"])
    #         plot_obj.spines["right"].set_visible(kwargs["spines_right"])
    #         plot_obj.spines["top"].set_visible(kwargs["spines_top"])
    #         plot_obj.spines["bottom"].set_visible(kwargs["spines_bottom"])
    #         [i.set_linewidth(kwargs["frame_width"]) for i in plot_obj.spines.values()]
    #
    #     # update line style, width, etc
    #     for _, line in enumerate(self.plotRMSF.get_lines()):
    #         line.set_linewidth(kwargs["rmsd_line_width"])
    #         line.set_linestyle(kwargs["rmsd_line_style"])
    #         line.set_color(kwargs["rmsd_line_color"])
    #
    #     for __, shade in enumerate(self.plotRMSF.collections):
    #         shade.set_facecolor(kwargs["rmsd_underline_color"])
    #         shade.set_alpha(kwargs["rmsd_underline_transparency"])
    #         shade.set_hatch(kwargs["rmsd_underline_hatch"])

    def plot_update_axes(self, axes_sizes: List[float]):
        """Update axes position"""
        self.plot_base.set_position(axes_sizes)
        self._axes = axes_sizes

    def get_optimal_margins(self, axes_sizes):
        """Get optimal margins for the plot"""
        trans = self.figure.transFigure.inverted().transform
        l, t, r, b = axes_sizes
        (l, b), (r, t) = trans(((l, b), (r, t)))

        # Extent
        dl, dt, dr, db = 0, 0, 0, 0
        for _, ax in enumerate(self.figure.get_axes()):
            (x0, y0), (x1, y1) = ax.get_position().get_points()
            try:
                (ox0, oy0), (ox1, oy1) = ax.get_tightbbox(self.canvas.get_renderer()).get_points()
                (ox0, oy0), (ox1, oy1) = trans(((ox0, oy0), (ox1, oy1)))
                dl = min(0.2, max(dl, (x0 - ox0)))
                dt = min(0.2, max(dt, (oy1 - y1)))
                dr = min(0.2, max(dr, (ox1 - x1)))
                db = min(0.2, max(db, (y0 - oy0)))
            except Exception:  # noqa
                pass
        l, t, r, b = l + dl, t + dt, r + dr, b + db

        return l, b, 1 - r, 1 - t

    @staticmethod
    def get_waterfall_colors(n_colors: int, **kwargs):
        """Get list of colors to be used by the waterfall plot"""
        lc, fc = [], []

        # check if colors should be a colormap
        if kwargs["color_scheme"] == "Colormap":
            fc = color_palette(kwargs["colormap"], n_colors)
        # or color palette
        elif kwargs["color_scheme"] == "Color palette":
            if kwargs["palette"] not in ["Spectral", "RdPu"]:
                kwargs["palette"] = kwargs["palette"].lower()
            fc = color_palette(kwargs["palette"], n_colors)
        # or same color
        elif kwargs["color_scheme"] == "Same color":
            fc = [kwargs["shade_color"]] * n_colors
        # or random color
        elif kwargs["color_scheme"] == "Random":
            fc = [get_random_color() for _ in range(n_colors)]

        if kwargs["line_color_as_shade"]:
            lc = copy(fc)
        else:
            lc = [kwargs["line_color"]] * n_colors

        # change alpha channel
        _fc = []
        alpha = kwargs.get("shade_under_transparency", 0.25)
        for color in copy(fc):
            color = list(color)
            color.append(alpha)
            _fc.append(color)

        return lc, _fc

    def get_violin_colors(self, n_colors: int, **kwargs):
        """Get list of colors to be used by the violin plot"""
        from itertools import repeat

        lc, fc = self.get_waterfall_colors(n_colors, **kwargs)
        lc = [x for item in lc for x in repeat(item, 2)]
        fc = [x for item in fc for x in repeat(item, 2)]
        return lc, fc

    @staticmethod
    def _prepare_waterfall(x, y, array, **kwargs):
        """Prepare data for waterfall plotting"""

        def _add_label():
            if label_frequency:
                label_x.append(_label_x)
                label_y.append(_y.min() + label_y_offset)
                label_text.append(ut_visuals.convert_label(x[i], label_format=kwargs["labels_format"]))

        # TODO: add `fix_end` option to prevent incorrect shading
        normalize = kwargs.get("normalize", True)
        y_increment = kwargs["increment"]
        label_y_offset = kwargs["labels_y_offset"]
        label_frequency = int(kwargs["labels_frequency"])
        #         fix_end = kwargs.get("fix_end", True)

        if kwargs["reverse"]:
            array = np.fliplr(array)
            x = x[::-1]

        array = array.astype(np.float32)

        yy, xy = [], []
        label_x, label_y, label_text = [], [], []
        if array is not None:
            _label_x = y.max() * kwargs["labels_x_offset"]
            for i, _y in enumerate(array.T):
                # normalize (to 1) the intensity of signal
                if normalize:
                    _y = _y / _y.max()

                # increase the baseline to set the signal apart from the one before it
                _y += i * y_increment
                xy.append(np.column_stack([y, _y]))
                yy.extend([_y.min(), _y.max()])

                _add_label()

        else:
            for i, (_x, _y) in enumerate(zip(x, y)):
                # normalize (to 1) the intensity of signal
                if normalize:
                    _y = _y / _y.max()

                # increase the baseline to set the signal apart from the one before it
                _y += i * y_increment
                xy.append(np.column_stack([_x, _y]))
                yy.extend([_y.min(), _y.max()])

        # trim number of labels
        if label_frequency:
            label_x = label_x[0::label_frequency]
            label_y = label_y[0::label_frequency]
            label_text = label_text[0::label_frequency]

        return yy, xy, label_x, label_y, label_text

    @staticmethod
    def _get_waterfall_label_kwargs(**kwargs):
        """Get kwargs to be consumed by the labels function"""
        return {
            "horizontalalignment": kwargs.pop("horizontal_alignment", "center"),
            "verticalalignment": kwargs.pop("vertical_alignment", "center"),
            "check_yscale": kwargs.pop("check_yscale", False),
            "butterfly_plot": kwargs.pop("butterfly_plot", False),
            "fontweight": "bold" if kwargs["labels_font_weight"] else "normal",
            "fontsize": kwargs.pop("labels_font_size", "medium"),
        }

    def plot_waterfall(self, x, y, array, x_label=None, y_label=None, **kwargs):
        """Plot as waterfall"""
        # TODO: add labels
        self._set_axes()

        yy, xy, label_x, label_y, label_text = self._prepare_waterfall(x, y, array, **kwargs)
        n_signals = len(xy)

        # get list of parameters for the plot
        lc, fc = self.get_waterfall_colors(n_signals, **kwargs)

        # the list of values is reversed to ensure that the zorder of each plot/line is correct
        coll = LineCollection(xy[::-1])
        self.plot_base.add_collection(coll)

        # set line style
        coll.set_edgecolors(lc)
        coll.set_linestyle(kwargs["line_style"])
        coll.set_linewidths(kwargs["line_width"])

        # set face style
        if kwargs["shade_under"]:
            coll.set_facecolors(fc)

        # set labels
        self.plot_add_labels(label_x, label_y, label_text, pickable=False, **self._get_waterfall_label_kwargs(**kwargs))

        # in waterfall plot, the horizontal axis is the mobility axis
        xlimits, ylimits, extent = self._compute_xy_limits(y, yy, None, is_heatmap=False)
        # set plot limits
        self.plot_base.yaxis.set_major_formatter(get_intensity_formatter())
        self.plot_base.set_xlim(xlimits)
        self.plot_base.set_ylim(ylimits)
        self.set_plot_xlabel(x_label, **kwargs)
        self.set_plot_ylabel(y_label, **kwargs)
        self.set_tick_parameters(**kwargs)

        self.setup_new_zoom(
            [self.plot_base],
            data_limits=extent,
            allow_extraction=kwargs.get("allow_extraction", False),
            callbacks=kwargs.get("callbacks", dict()),
            is_heatmap=True,
        )
        self.store_plot_limits([extent], [self.plot_base])
        self.PLOT_TYPE = "waterfall"

    @staticmethod
    def update_line(x, y, gid, ax):
        """Update line plot"""
        lines = ax.get_lines()
        for line in lines:
            plot_gid = line.get_gid()
            if plot_gid == gid:
                line.set_xdata(x)
                line.set_ydata(y)
                break
