# Standard library imports
import logging
import warnings

# Third-party imports
import numpy as np
import matplotlib
from seaborn import color_palette
from matplotlib import patches
from matplotlib.ticker import MaxNLocator

# Local imports
import origami.utils.visuals as ut_visuals
from origami.utils.misc import merge_two_dicts
from origami.utils.misc import remove_nan_from_list
from origami.utils.color import get_random_color
from origami.utils.ranges import get_min_max
from origami.config.config import CONFIG
from origami.utils.adjustText import adjust_text
from origami.utils.exceptions import MessageError
from origami.visuals.mpl.panel import MPLPanel

logger = logging.getLogger(__name__)

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)


class PlotBase(MPLPanel):
    def __init__(self, *args, **kwargs):
        self._axes = kwargs.get("axes_size", [0.12, 0.12, 0.8, 0.8])  # keep track of axes size
        MPLPanel.__init__(self, *args, **kwargs)

        self._plot_flag = False
        self.plot_base = None

    def _set_axes(self):
        """Add axis to the figure"""
        self.plot_base = self.figure.add_axes(self._axes)

    def _locked(self):
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

    def _compute_xy_limits(self, x, y, y_lower_start=0, y_upper_multiplier=1.0):
        """Calculate the x/y axis ranges"""
        x = np.asarray(x)
        y = np.asarray(y)
        x_min, x_max = get_min_max(x)
        y_min, y_max = get_min_max(y)

        xlimits = [x_min, x_max]
        if y_lower_start is None:
            y_lower_start = y_min
        ylimits = [y_lower_start, y_max * y_upper_multiplier]

        # extent is x_min, y_min, x_max, y_max
        extent = [xlimits[0], ylimits[0], xlimits[1], ylimits[1]]

        return xlimits, ylimits, extent

    def store_plot_limits(self, extent):
        self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]

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

        #         if CONFIG._plots_check_axes_size:
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
                loc=kwargs.get("legend_position", CONFIG.legendPosition),
                ncol=kwargs.get("legend_num_columns", CONFIG.legendColumns),
                fontsize=kwargs.get("legend_font_size", CONFIG.legendFontSize),
                frameon=kwargs.get("legend_frame_on", CONFIG.legendFrame),
                framealpha=kwargs.get("legend_transparency", CONFIG.legendAlpha),
                markerfirst=kwargs.get("legend_marker_first", CONFIG.legendMarkerFirst),
                markerscale=kwargs.get("legend_marker_size", CONFIG.legendMarkerSize),
                fancybox=kwargs.get("legend_fancy_box", CONFIG.legendFancyBox),
                scatterpoints=kwargs.get("legend_num_markers", CONFIG.legendNumberMarkers),
                handles=handles,
            )
            if "legend_zorder" in kwargs:
                legend.set_zorder(kwargs.pop("legend_zorder"))
            legend.draggable()

    def set_plot_xlabel(self, xlabel, **kwargs):
        kwargs = ut_visuals.check_plot_settings(**kwargs)

        if xlabel is None:
            xlabel = self.plot_base.get_xlabel()
        self.plot_base.set_xlabel(
            xlabel, labelpad=kwargs["label_pad"], fontsize=kwargs["label_size"], weight=kwargs["label_weight"]
        )
        self.plot_labels["xlabel"] = xlabel

    def set_plot_ylabel(self, ylabel, **kwargs):
        kwargs = ut_visuals.check_plot_settings(**kwargs)
        if ylabel is None:
            ylabel = self.plot_base.get_ylabel()
        self.plot_base.set_ylabel(
            ylabel, labelpad=kwargs["label_pad"], fontsize=kwargs["label_size"], weight=kwargs["label_weight"]
        )
        self.plot_labels["ylabel"] = ylabel

    def set_plot_title(self, title, **kwargs):
        kwargs = ut_visuals.check_plot_settings(**kwargs)

        if title is None:
            title = self.plot_base.get_title()

        self.plot_base.set_title(title, fontsize=kwargs["title_size"], weight=kwargs.get("label_weight", "normal"))

    def set_tick_parameters(self, **kwargs):

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

    def _convert_yaxis(self, values, label, set_divider=True, convert_values=True):
        """ Function to check whether x/y axis labels do not need formatting """

        increment = 10
        divider = 1

        try:
            itemShape = values.shape
        except Exception:
            values = np.array(values)
            itemShape = values.shape

        if len(itemShape) > 1:
            maxValue = np.amax(np.absolute(values))
        elif len(itemShape) == 1:
            maxValue = np.max(np.absolute(values))
        else:
            maxValue = values

        while 10 <= (maxValue / divider) >= 1:
            divider = divider * increment

        expo = len(str(divider)) - len(str(divider).rstrip("0"))

        if expo == 1:
            divider = 1

        label = ut_visuals.add_exponent_to_label(label, divider)
        if expo > 1:
            if convert_values:
                values = np.divide(values, float(divider))

        if set_divider:
            self.y_divider = divider

        return values, label, divider

    def _convert_yaxis_with_preset_divider(self, values, label):
        if self.y_divider is None:
            __, __, __ = self._convert_yaxis(values, label)

        divider = self.y_divider
        expo = len(str(divider)) - len(str(divider).rstrip("0"))

        if expo > 1:
            offset_text = r"x$\mathregular{10^{%d}}$" % expo
            label = "".join([label, " [", offset_text, "]"])

        values = np.divide(values, float(divider))

        return values, label, divider

    def _get_colors(self, n_colors):
        if CONFIG.currentPalette not in ["Spectral", "RdPu"]:
            palette = CONFIG.currentPalette.lower()
        else:
            palette = CONFIG.currentPalette
        colorlist = color_palette(palette, n_colors)

        return colorlist

    def _convert_yaxis_list(self, values, label):

        # compute divider(s)
        _dividers = []
        for _, value in enumerate(values):
            __, __ylabel, divider = self._convert_yaxis(value, label, set_divider=False, convert_values=False)
            _dividers.append(divider)

        # update divider
        self.y_divider = np.max(_dividers)

        for i, value in enumerate(values):
            values[i] = np.divide(value, float(divider))

        label = ut_visuals.add_exponent_to_label(label, self.y_divider)

        return values, label

    def _check_colormap(self, cmap=None, **kwargs):
        #         # checking entire dict
        #         if cmap is None:
        #             if kwargs["colormap"] in CONFIG.cmocean_cmaps:
        #                 kwargs["colormap"] = eval("cmocean.cm.%s" % kwargs["colormap"])
        #             return kwargs
        #
        #         # only checking colormap
        #         if cmap in CONFIG.cmocean_cmaps:
        #             cmap = eval("cmocean.cm.%s" % cmap)
        return cmap

    def _fix_label_positions(self, lim=20):
        """
        Try to fix position of labels to prevent overlap
        """
        try:
            adjust_text(self.text, lim=lim)
        except (AttributeError, KeyError, ValueError):
            logger.warning("Failed to fix label position", exc_info=True)

    def get_xylimits(self):
        xmin, xmax = self.plot_base.get_xlim()
        ymin, ymax = self.plot_base.get_ylim()

        return [xmin, xmax, ymin, ymax]

    def set_xy_limits(self, xy_limits):
        # xylimits = [xmin, xmax, ymin, ymax]

        self.plot_base.set_xlim([xy_limits[0], xy_limits[1]])
        self.plot_base.set_ylim([xy_limits[2], xy_limits[3]])

        extent = [xy_limits[0], xy_limits[2], xy_limits[1], xy_limits[3]]
        self.update_extents(extent)

    def on_zoom_x_axis(self, xmin, xmax):
        self.plot_base.set_xlim([xmin, xmax])

    def on_zoom_y_axis(self, startY=None, endY=None, **kwargs):
        xylimits = self.get_xylimits()

        if startY is None:
            startY = xylimits[2]

        if endY is None:
            endY = xylimits[3]

        if kwargs.pop("convert_values", False):
            try:
                startY = np.divide(startY, self.y_divider)
                endY = np.divide(endY, self.y_divider)
            except Exception:
                pass

        self.plot_base.set_ylim([startY, endY])
        self.update_y_extents(startY, endY)

    def on_zoom_xy(self, startX, endX, startY, endY):
        try:
            startY = startY / float(self.y_divider)
            endY = endY / float(self.y_divider)
        except Exception:
            pass
        try:
            self.plot_base.axis([startX, endX, startY, endY])
            self.repaint()
        except Exception:
            pass

    def on_zoom(self, startX, endX, endY):
        try:
            endY = endY / float(self.y_divider)
        except Exception:
            pass
        try:
            self.plot_base.axis([startX, endX, 0, endY])
            self.repaint()
        except Exception:
            pass

    def on_reset_zoom(self):
        self.plot_base.set_xlim((self.plot_limits[0], self.plot_limits[1]))
        self.plot_base.set_ylim((self.plot_limits[2], self.plot_limits[3]))
        self.repaint()

    def plot_remove_patch_with_label(self, label):
        """
        Remove plot
        """

        if len(self.patch) == 0:
            return

        for i, patch in enumerate(self.patch):
            if hasattr(patch, "obj_name") and patch.obj_name == label:
                try:
                    patch.remove()
                    del self.patch[i]
                except Exception:
                    return

    def plot_add_arrow(self, arrow_vals, stick_to_intensity=True, **kwargs):
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
            except Exception:
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

    def plot_remove_arrows(self):
        for arrow in self.arrows:
            try:
                arrow.remove()
            except Exception:
                pass

        self.arrows = []
        self.repaint()

    def plot_add_markers(
        self, xvals, yvals, label="", marker="o", color="r", size=15, test_yvals=False, test_xvals=False, **kwargs
    ):

        if test_yvals:
            yvals, __, __ = self._convert_yaxis(yvals, "")

        if kwargs.get("test_yvals_with_preset_divider", False):
            yvals, __, __ = self._convert_yaxis_with_preset_divider(yvals, label)

        if test_xvals:
            xvals, __, __ = self._convert_xaxis(xvals)

        markers = self.plot_base.scatter(
            xvals,
            yvals,
            color=color,
            marker=marker,
            s=size,
            label=label,
            edgecolor=kwargs.get("edge_color", "k"),
            alpha=kwargs.get("marker_alpha", 1.0),
            zorder=kwargs.get("zorder", 5),
        )
        self.markers.append(markers)

    def plot_remove_markers(self, repaint=True):

        for marker in self.markers:
            try:
                marker.remove()
            except Exception:
                pass

        self.markers = []
        if repaint:
            self.repaint()

    def plot_remove_lines(self, label_starts_with):
        try:
            lines = self.plot_base.get_lines()
        except AttributeError:
            raise MessageError("Error", "Please plot something first")
        for line in lines:
            line_label = line.get_label()
            if line_label.startswith(label_starts_with):
                line.remove()

    def _remove_existing_label(self, name_tag):
        for i, text in enumerate(self.text):
            if text.obj_name == name_tag:
                text.remove()
                del self.text[i]

    def _remove_existing_arrow(self, name_tag):
        for i, arrow in enumerate(self.arrows):
            if arrow.obj_name == name_tag:
                arrow.remove()
                del self.arrows[i]

    def _remove_existing_line(self, name_tag):
        for i, line in enumerate(self.lines):
            if line.obj_name == name_tag:
                line.remove()
                del self.lines[i]

    def _remove_existing_patch(self, name_tag):
        for i, patch in enumerate(self.patch):
            if patch.obj_name == name_tag:
                patch.remove()
                del self.patch[i]

    def add_labels(self, x, y, labels, **kwargs):
        """Add labels to the plot"""
        if not isinstance(x, (list, tuple, np.ndarray)):
            x = [x]
        if not isinstance(y, (list, tuple, np.ndarray)):
            y = [y]
        if not isinstance(labels, (list, tuple, np.ndarray)):
            labels = [labels]

        pass

    def plot_add_text_and_lines(
        self,
        xpos,
        yval,
        label,
        vline=True,
        vline_position=None,
        color="black",
        yoffset=0.05,
        stick_to_intensity=False,
        **kwargs,
    ):
        obj_name = kwargs.pop("text_name", None)
        if obj_name is not None:
            self._remove_existing_label(obj_name)

        try:
            ymin, ymax = self.plot_base.get_ylim()
        except AttributeError:
            raise MessageError("Error", "Please plot something first")

        if stick_to_intensity:
            try:
                y_position = np.divide(yval, self.y_divider)
            except Exception:
                y_position = ymax
        else:
            y_position = ymax

        # get custom name tag

        text = self.plot_base.text(
            np.array(xpos),
            y_position + yoffset,
            label,
            horizontalalignment=kwargs.pop("horizontalalignment", "center"),
            verticalalignment=kwargs.pop("verticalalignment", "top"),
            color=color,
            clip_on=True,
            picker=True,
            **kwargs,
        )
        text.obj_name = obj_name  # custom tag
        text.y_divider = self.y_divider
        self.text.append(text)

        if vline:
            if vline_position is not None:
                xpos = vline_position
            line = self.plot_base.axvline(xpos, ymin, yval * 0.8, color=color, linestyle="dashed", alpha=0.4)
            self.lines.append(line)

    def plot_add_text(self, xpos, yval, label, color="black", yoffset=0.0, zorder=3, **kwargs):

        is_butterfly = kwargs.pop("butterfly_plot", False)

        # check if value should be scaled based on the exponential
        if kwargs.pop("check_yscale", False):
            try:
                yval = np.divide(yval, self.y_divider)
            except Exception:
                pass

        # reverse value
        if is_butterfly:
            try:
                yval = -yval
                yoffset = -yoffset
            except Exception:
                pass

        # get custom name tag
        obj_name = kwargs.pop("text_name", None)

        yval = yval + yoffset

        # this will offset the intensity of the label by small value
        if kwargs.pop("add_arrow_to_low_intensity", False):
            if is_butterfly:
                if (yval - yoffset) > 0.2 * self.plot_limits[2]:
                    rand_offset = -np.random.uniform(high=0.75 * self.plot_limits[2])
                    yval_old = yval - yoffset
                    yval -= rand_offset
                    arrow_vals = [xpos, yval_old, 0, yval - yval_old]
                    self.plot_add_arrow(arrow_vals, stick_to_intensity=False)
            else:
                if (yval - yoffset) < 0.2 * self.plot_limits[3]:
                    rand_offset = np.random.uniform(high=0.5 * self.plot_limits[3])
                    yval_old = yval - yoffset
                    yval += rand_offset
                    arrow_vals = [xpos, yval_old, 0, yval - yval_old]
                    self.plot_add_arrow(arrow_vals, stick_to_intensity=False)

        text = self.plot_base.text(
            np.array(xpos), yval + yoffset, label, color=color, clip_on=True, zorder=zorder, picker=True, **kwargs
        )
        text._yposition = yval - kwargs.get("labels_y_offset", CONFIG.waterfall_labels_y_offset)
        text.obj_name = obj_name  # custom tag
        text.y_divider = self.y_divider
        self.text.append(text)

    def plot_remove_text(self, repaint=True):
        for text in self.text:
            try:
                text.remove()
            except Exception:
                pass

        self.text = []
        if repaint:
            self.repaint()

    def plot_add_patch(
        self, xmin, ymin, width, height, color="r", alpha=0.5, linewidth=0, add_temporary=False, label="", **kwargs
    ):

        if label not in [None, ""]:
            self._remove_existing_patch(label)

        # check if need to rescale height
        try:
            height = np.divide(height, self.y_divider)
        except Exception:
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
                    picker=True,
                    edgecolor="k",
                )
            )
        except AttributeError:
            print("Please plot something first")
            return

        # set label
        patch.obj_name = label
        patch.y_divider = self.y_divider

        if add_temporary:
            self.plot_remove_temporary()
            self.temporary.append(patch)
        else:
            self.patch.append(patch)

    def plot_remove_patches(self, repaint=True):

        for patch in self.patch:
            try:
                patch.remove()
            except Exception:
                pass

        self.patch = []
        if repaint:
            self.repaint()

    def plot_add_line(self, xmin, xmax, ymin, ymax, orientation, label="temporary"):

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
        for patch in self.temporary:
            try:
                patch.remove()
            except Exception:
                pass

        self.temporary = []
        if repaint:
            self.repaint()

    def plot_remove_text_and_lines(self, repaint=True):

        for text in self.text:
            try:
                text.remove()
            except Exception:
                pass

        for line in self.lines:
            try:
                line.remove()
            except Exception:
                pass

        for arrow in self.arrows:
            try:
                arrow.remove()
            except Exception:
                pass

        self.text = []
        self.lines = []
        self.arrows = []

        if repaint:
            self.repaint()

    def plot_1D_update_data_only(self, xvals, yvals):
        kwargs = self.plot_parameters

        lines = self.plot_base.get_lines()
        ylabel = self.plot_base.get_ylabel()
        ylabel = ylabel.split(" [")[0]

        #         yvals, ylabel, __ = self._convert_yaxis(yvals, ylabel)

        lines[0].set_xdata(xvals)
        lines[0].set_ydata(yvals)

        self.set_plot_ylabel(ylabel, **kwargs)

    def plot_1D_get_data(self, use_divider=False):
        xdata, ydata, labels = [], [], []

        lines = self.plot_base.get_lines()
        for line in lines:
            xdata.append(line.get_xdata())
            if use_divider:
                ydata.append(line.get_ydata() * self.y_divider)
            else:
                ydata.append(line.get_ydata())
            labels.append(line.get_label())

        xlabel = self.plot_base.get_xlabel()
        ylabel = self.plot_base.get_ylabel()
        return xdata, ydata, labels, xlabel, ylabel

    def plot_1D_update_data(self, xvals, yvals, xlabel, ylabel, testMax="yvals", **kwargs):
        if self.plot_name in ["compare", "Compare"]:
            raise Exception("Wrong plot name - resetting")

        # override parameters
        if not self.lock_plot_from_updating:
            self.plot_parameters = kwargs
        else:
            kwargs = merge_two_dicts(kwargs, self.plot_parameters)
            self.plot_parameters = kwargs

        try:
            self.plot_remove_text_and_lines()
            self.plot_remove_patches()
        except Exception:
            pass

        # remove old lines
        if hasattr(self, "plot_base"):
            lines = self.plot_base.get_lines()
            for line in lines[1:]:
                line.remove()

        # remove old shades
        while len(self.plot_base.collections) > 0:
            for shade in self.plot_base.collections:
                shade.remove()

        #         if testMax == "yvals":
        #             yvals, ylabel, __ = self._convert_yaxis(yvals, ylabel)
        #
        #         if kwargs.pop("testX", False):
        #             xvals, xlabel, __ = self._convert_xaxis(xvals)

        lines[0].set_xdata(xvals)
        lines[0].set_ydata(yvals)
        lines[0].set_linewidth(kwargs["line_width"])
        lines[0].set_color(kwargs["line_color"])
        lines[0].set_linestyle(kwargs["line_style"])
        lines[0].set_label(kwargs.get("label", ""))

        # update limits and extents
        xlimits = (np.min(xvals), np.max(xvals))
        ylimits = (np.min(yvals), np.max(yvals) * 1.1)
        extent = [xlimits[0], ylimits[0], xlimits[1], ylimits[1]]

        if kwargs["shade_under"]:
            shade_kws = dict(
                facecolor=kwargs["shade_under_color"],
                alpha=kwargs.get("shade_under_transparency", 0.25),
                clip_on=kwargs.get("clip_on", True),
                zorder=kwargs.get("zorder", 1),
            )
            self.plot_base.fill_between(xvals, 0, yvals, **shade_kws)

        # convert weights
        if kwargs["label_weight"]:
            kwargs["label_weight"] = "heavy"
        else:
            kwargs["label_weight"] = "normal"

        self.plot_base.set_xlim(xlimits)
        self.plot_base.set_ylim(ylimits)
        self.set_plot_xlabel(xlabel, **kwargs)
        self.set_plot_ylabel(ylabel, **kwargs)

        if kwargs.get("minor_ticks_off", False) or xlabel == "Scans" or xlabel == "Charge":
            self.plot_base.xaxis.set_tick_params(which="minor", bottom="off")
            self.plot_base.xaxis.set_major_locator(MaxNLocator(integer=True))

        self.update_extents(extent)
        self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]

        self.plot_labels.update({"xlabel": xlabel, "ylabel": ylabel})

        # update legend
        handles, __ = self.plot_base.get_legend_handles_labels()
        self.set_legend_parameters(handles, **self.plot_parameters)

    def plot_1D_update_data_by_label(self, xvals, yvals, gid, label):
        """Update plot data without replotting the entire plot

        Parameters
        ----------
        xvals: np.array
            x-axis values
        yvals: np.array
            y-axis values
        gid: int / str
            value by which we can identify the desired plot
        label: str
            new label to be updated in the legend
        """
        lines = self.plot_base.get_lines()

        # calculate divider
        __, __, divider = self._convert_yaxis(yvals, "", set_divider=False, convert_values=False)
        #         divider = np.max([divider, self.y_divider])

        # convert ylabel based on the divider
        ylabel = ut_visuals.add_exponent_to_label(self.plot_base.get_ylabel(), divider)
        self.set_plot_ylabel(ylabel, **self.plot_parameters)

        # determine the plot limits and if necessary, update the plot data
        ylimits = self.get_ylimits()
        for line in lines:
            plot_gid = line.get_gid()
            if plot_gid is not None and plot_gid != gid:
                old_yvals = line.get_ydata()
                old_yvals = np.multiply(old_yvals, float(self.y_divider))
                old_yvals = np.divide(old_yvals, float(divider))
                line.set_ydata(old_yvals)
                ylimits = get_min_max(old_yvals)

        # update divider
        self.y_divider = divider

        # change data for desired plot
        yvals, __, __ = self._convert_yaxis_with_preset_divider(yvals, "")
        for line in lines:
            plot_gid = line.get_gid()
            if plot_gid == gid:
                line.set_xdata(xvals)
                line.set_ydata(yvals)
                line.set_label(label)
                break

        # update legend
        handles, __ = self.plot_base.get_legend_handles_labels()
        self.set_legend_parameters(handles, **self.plot_parameters)

        # update plot limits
        ylimits = get_min_max(get_min_max(yvals) + ylimits)
        self.on_zoom_y_axis(ylimits[0], ylimits[1], convert_values=False)

    def plot_1D_update_style_by_label(self, gid, **kwargs):

        lines = self.plot_base.get_lines()
        for line in lines:
            plot_gid = line.get_gid()
            if plot_gid == gid:
                if "color" in kwargs:
                    line.set_color(kwargs.get("color"))
                if "line_style" in kwargs:
                    line.set_linestyle(kwargs.get("line_style"))
                if "transparency" in kwargs:
                    line.set_alpha(kwargs.get("transparency"))
                break

        handles, __ = self.plot_base.get_legend_handles_labels()
        self.set_legend_parameters(handles, **self.plot_parameters)

    def _plot_1D_compare_prepare_data(self, yvals_1, yvals_2, ylabel=None):
        if ylabel is None:
            ylabel = self.plot_base.get_ylabel()

        yvals_1, __, divider_1 = self._convert_yaxis(yvals_1, "", convert_values=False)
        yvals_2, __, divider_2 = self._convert_yaxis(yvals_2, "", convert_values=False)
        divider = np.max([divider_1, divider_2])
        self.y_divider = divider
        yvals_1 = np.divide(yvals_1, float(divider))
        yvals_2 = np.divide(yvals_2, float(divider))
        ylabel = ut_visuals.add_exponent_to_label(ylabel, divider)

        return yvals_1, yvals_2, ylabel

    def plot_1D_compare_update_data(self, xvals_1, xvals_2, yvals_1, yvals_2, **kwargs):

        # update settings
        self._check_and_update_plot_settings(**kwargs)

        yvals_1, yvals_2, ylabel = self._plot_1D_compare_prepare_data(yvals_1, yvals_2, None)
        self.set_plot_ylabel(ylabel, **self.plot_parameters)

        ylimits = []
        lines = self.plot_base.get_lines()
        for line in lines:
            plot_gid = line.get_gid()
            if plot_gid == 0:
                line.set_xdata(xvals_1)
                line.set_ydata(yvals_1)
                line.set_label(kwargs.pop("label_1", line.get_label()))
                line.set_color(kwargs.get("line_color_1", line.get_color()))
                ylimits += get_min_max(yvals_1)
            elif plot_gid == 1:
                line.set_xdata(xvals_2)
                line.set_ydata(yvals_2)
                line.set_label(kwargs.pop("label_2", line.get_label()))
                line.set_color(kwargs.get("line_color_2", line.get_color()))
                ylimits += get_min_max(yvals_2)

        # update legend
        handles, __ = self.plot_base.get_legend_handles_labels()
        self.set_legend_parameters(handles, **self.plot_parameters)

        # update plot limits
        ylimits = get_min_max(ylimits)
        self.on_zoom_y_axis(ylimits[0], ylimits[1], convert_values=False)

    def plot_1D_waterfall_update(self, which="other", **kwargs):

        if self.lock_plot_from_updating:
            self._locked()

        kwargs = ut_visuals.check_plot_settings(**kwargs)

        if self.plot_name == "Waterfall_overlay" and which in ["color", "data"]:
            return

        if which in ["other", "style"]:
            self.plot_1d_waterfall_update_style(**kwargs)

        elif which == "color":
            self.plot_1d_waterfall_update_color(**kwargs)

        elif which == "shade":
            self.plot_1d_waterfall_update_shade(**kwargs)

        elif which == "label":
            self.plot_1d_waterfall_update_label(**kwargs)

        elif which == "data":
            self.plot_1d_waterfall_data(**kwargs)

        elif which == "frame":
            self.set_tick_parameters(**kwargs)

        elif which == "fonts":
            self.plot_1d_waterfall_fonts(**kwargs)

        self.plot_parameters = kwargs

    def plot_1d_waterfall_update_style(self, **kwargs):
        if self.plot_name != "Violin":
            for i, line in enumerate(self.plot_base.get_lines()):
                line.set_linestyle(kwargs["line_style"])
                line.set_linewidth(kwargs["line_width"])
        else:
            for shade in range(len(self.plot_base.collections)):
                self.plot_base.collections[shade].set_linestyle(kwargs["line_style"])
                self.plot_base.collections[shade].set_linewidth(kwargs["line_width"])

    def plot_1d_waterfall_update_color(self, **kwargs):
        n_colors = len(self.plot_base.get_lines())
        n_patch_colors = len(self.plot_base.collections)
        if n_colors != n_patch_colors:
            if n_patch_colors > n_colors:
                n_colors = n_patch_colors

        # get colorlist
        colorlist = self._get_colorlist(None, n_colors, which="shade", **kwargs)

        if self.plot_name != "Violin":
            for i, line in enumerate(self.plot_base.get_lines()):
                if kwargs["line_color_as_shade"]:
                    line_color = colorlist[i]
                else:
                    line_color = kwargs["line_color"]
                line.set_color(line_color)
        else:
            for i in range(len(self.plot_base.collections)):
                if kwargs["line_color_as_shade"]:
                    line_color = colorlist[i]
                else:
                    line_color = kwargs["line_color"]
                self.plot_base.collections[i].set_edgecolor(line_color)

        for shade in range(len(self.plot_base.collections)):
            shade_color = colorlist[shade]
            self.plot_base.collections[shade].set_facecolor(shade_color)

    def plot_1d_waterfall_update_shade(self, **kwargs):
        try:
            for shade in range(len(self.plot_base.collections)):
                self.plot_base.collections[shade].set_alpha(kwargs["shade_under_transparency"])
        except AttributeError:
            logger.warning("Could not update waterfall underlines")

    def plot_1d_waterfall_update_label(self, **kwargs):

        # calculate new position
        label_xposition = self.text_offset_position["min"] + (
            self.text_offset_position["max"] * kwargs["labels_x_offset"]
        )

        if not isinstance(self.text, list):
            logger.warning("Could not update waterfall labels - are they plotted?")
            return

        for text_obj in self.text:
            if not kwargs["add_labels"]:
                text_obj.set_visible(False)
            else:
                text_obj.set_fontweight(kwargs["labels_font_weight"])
                text_obj.set_fontsize(kwargs["labels_font_size"])
                yposition = text_obj._yposition + kwargs["labels_y_offset"]
                text_obj.set_position([label_xposition, yposition])
                text = ut_visuals.convert_label(text_obj.get_text(), label_format=kwargs["labels_format"])
                text_obj.set_text(text)

    def plot_1d_waterfall_data(self, **kwargs):
        # TODO: needs to respect labels
        # TODO: needs to respect shade
        # TODO: fix an issue when there is shade under the curve
        # fix might be here: https://stackoverflow.com/questions/16120801/matplotlib-animate-fill-between-shape
        #         count = 0
        increment = kwargs["increment"] - self.plot_parameters["increment"]
        offset = kwargs["offset"]  # - self.plot_parameters['offset']

        # some presets
        label_kws = dict(fontsize=kwargs["labels_font_size"], fontweight=kwargs["labels_font_weight"])
        shade_kws = dict(alpha=kwargs.get("shade_under_transparency", 0.25), clip_on=kwargs.get("clip_on", True))

        # collect information about underlines
        collection_info = dict()
        for i, shade in enumerate(self.plot_base.collections):
            collection_info[i] = [shade.get_zorder(), shade.get_facecolor()]
        self.plot_base.collections.clear()

        label_info = dict()
        for i, text in enumerate(self.text):
            label_info[i] = [text._text, text.get_zorder(), text.get_position()[0]]
        self.plot_remove_text(False)

        if kwargs["reverse"] and label_info:
            logger.warning(
                "When 'reverse' is set to True, labels cannot be changed so they are removed. You have to"
                " fully replot the waterfall plot."
            )
            label_info.clear()

        ydata, y_offset, i_text = [], 0, 0
        n_count = len(self.plot_base.get_lines())
        for i, line in enumerate(self.plot_base.get_lines()):
            xvals = line.get_xdata()
            yvals = line.get_ydata()
            # indication that waterfall plot is actually shown
            if len(yvals) > 5:
                y = yvals + y_offset
                y_min, y_max = get_min_max(y)
                line.set_ydata(y)

                # update labels
                if label_info:
                    if i % kwargs["labels_frequency"] == 0 or i == n_count - 1:
                        self.plot_add_text(
                            xpos=label_info[i_text][2],
                            yval=y_min + kwargs["labels_y_offset"],
                            label=label_info[i_text][0],
                            zorder=label_info[i_text][1],
                            **label_kws,
                        )
                        i_text += 1

                # add underline data if present
                if collection_info:
                    shade_kws.update(zorder=collection_info[i][0], facecolor=collection_info[i][1])
                    self.plot_base.fill_between(xvals, y_min, y, **shade_kws)

                ydata.extend([y_min, y_max])
                y_offset = y_offset - increment

        # update extents
        ydata = remove_nan_from_list(ydata)
        self.plot_limits[2] = np.min(ydata) - offset
        self.plot_limits[3] = np.max(ydata) + 0.05
        extent = [self.plot_limits[0], self.plot_limits[2], self.plot_limits[1], self.plot_limits[3]]
        self.update_extents(extent)
        self.plot_base.set_xlim((self.plot_limits[0], self.plot_limits[1]))
        self.plot_base.set_ylim((self.plot_limits[2], self.plot_limits[3]))

    def plot_1d_waterfall_fonts(self, **kwargs):
        # update ticks
        matplotlib.rc("xtick", labelsize=kwargs["tick_size"])
        matplotlib.rc("ytick", labelsize=kwargs["tick_size"])

        # update labels
        self.set_plot_xlabel(None, **kwargs)
        self.set_plot_ylabel(None, **kwargs)

        # Setup font size info
        self.plot_base.tick_params(labelsize=kwargs["tick_size"])

    def plot_1D_update(self, **kwargs):
        if self.lock_plot_from_updating:
            self._locked()

        # update plot labels
        self.set_plot_xlabel(None, **kwargs)
        self.set_plot_ylabel(None, **kwargs)
        self.set_tick_parameters(**kwargs)

        # update line settings
        for __, line in enumerate(self.plot_base.get_lines()):
            line.set_linewidth(kwargs["line_width"])
            line.set_linestyle(kwargs["line_style"])
            line.set_color(kwargs["line_color"])

        # add shade if it has been previously deleted
        if kwargs["shade_under"] and not self.plot_base.collections:
            xvals, yvals, _, _, _ = self.plot_1D_get_data(use_divider=False)
            self.plot_1d_add_under_curve(xvals[0], yvals[0], **kwargs)

        for __, shade in enumerate(self.plot_base.collections):
            if not kwargs["shade_under"]:
                shade.remove()
            else:
                shade.set_facecolor(kwargs["shade_under_color"])
                shade.set_alpha(kwargs["shade_under_transparency"])

        self._update_plot_settings_(**kwargs)

    def plot_1D_update_rmsf(self, **kwargs):
        if self.lock_plot_from_updating:
            self._locked()

        if any([plot is None for plot in [self.plotRMSF, self.plot_base]]):
            return

        # ensure correct format of kwargs
        kwargs = ut_visuals.check_plot_settings(**kwargs)

        # update ticks
        matplotlib.rc("xtick", labelsize=kwargs["tick_size"])
        matplotlib.rc("ytick", labelsize=kwargs["tick_size"])

        # update labels
        for plot_obj in [self.plotRMSF, self.plot_base]:
            # Setup font size info
            plot_obj.set_ylabel(
                plot_obj.get_ylabel(),
                labelpad=kwargs["label_pad"],
                fontsize=kwargs["label_size"],
                weight=kwargs["label_weight"],
            )
            plot_obj.set_ylabel(
                plot_obj.get_ylabel(),
                labelpad=kwargs["label_pad"],
                fontsize=kwargs["label_size"],
                weight=kwargs["label_weight"],
            )

            plot_obj.tick_params(labelsize=kwargs["tick_size"])

            # update axis frame
            plot_obj.set_axis_on() if kwargs["axis_onoff"] else plot_obj.set_axis_off()

            plot_obj.tick_params(
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

            plot_obj.spines["left"].set_visible(kwargs["spines_left"])
            plot_obj.spines["right"].set_visible(kwargs["spines_right"])
            plot_obj.spines["top"].set_visible(kwargs["spines_top"])
            plot_obj.spines["bottom"].set_visible(kwargs["spines_bottom"])
            [i.set_linewidth(kwargs["frame_width"]) for i in plot_obj.spines.values()]

        # update line style, width, etc
        for _, line in enumerate(self.plotRMSF.get_lines()):
            line.set_linewidth(kwargs["rmsd_line_width"])
            line.set_linestyle(kwargs["rmsd_line_style"])
            line.set_color(kwargs["rmsd_line_color"])

        for __, shade in enumerate(self.plotRMSF.collections):
            shade.set_facecolor(kwargs["rmsd_underline_color"])
            shade.set_alpha(kwargs["rmsd_underline_transparency"])
            shade.set_hatch(kwargs["rmsd_underline_hatch"])

    def plot_update_axes(self, axes_sizes):
        self.plot_base.set_position(axes_sizes)
        self._axes = axes_sizes

    def get_optimal_margins(self, axes_sizes):
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
            except:
                pass
        l, t, r, b = l + dl, t + dt, r + dr, b + db

        return l, b, 1 - r, 1 - t

    def _get_colorlist(self, colorList, n_colors, which="line", **kwargs):

        if colorList is not None and len(colorList) == n_colors:
            colorlist = colorList
        elif kwargs["color_scheme"] == "Colormap":
            colorlist = color_palette(kwargs["colormap"], n_colors)

        elif kwargs["color_scheme"] == "Color palette":
            if kwargs["palette"] not in ["Spectral", "RdPu"]:
                kwargs["palette"] = kwargs["palette"].lower()
            colorlist = color_palette(kwargs["palette"], n_colors)
        elif kwargs["color_scheme"] == "Same color":
            color = [kwargs["line_color"]] if which == "line" else [kwargs["shade_color"]]
            colorlist = color * n_colors
        elif kwargs["color_scheme"] == "Random":
            colorlist = []
            for __ in range(n_colors):
                colorlist.append(get_random_color())
        return colorlist
