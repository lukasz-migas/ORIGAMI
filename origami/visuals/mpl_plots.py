# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import itertools
import logging
import warnings
from copy import deepcopy

import matplotlib
import matplotlib.cm as cm
import matplotlib.patches as patches
import numpy as np
import utils.visuals as ut_visuals
from gui_elements.misc_dialogs import DialogBox
from matplotlib import gridspec
from matplotlib.collections import LineCollection
from matplotlib.ticker import MaxNLocator
from mpl_toolkits.axes_grid1 import make_axes_locatable
from processing.heatmap import normalize_2D
from processing.spectra import normalize_1D
from seaborn import color_palette
from toolbox import find_limits_all
from toolbox import find_limits_list
from toolbox import merge_two_dicts
from toolbox import remove_nan_from_list
from utils.adjustText import adjust_text
from utils.color import convertRGB1to255
from utils.color import determineFontColor
from utils.color import randomColorGenerator
from utils.exceptions import MessageError
from utils.labels import _replace_labels
from utils.ranges import get_min_max
from visuals.mpl_plotter import mpl_plotter
from visuals.normalize import MidpointNormalize

logger = logging.getLogger("origami")

# needed to avoid annoying warnings to be printed on console
# import matplotlib.colors as mpl_colors
# import matplotlib as mpl
# import matplotlib.pyplot as plt
# from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg

# from mpl_toolkits.mplot3d import Axes3D
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)


class plots(mpl_plotter):
    def __init__(self, *args, **kwargs):
        self._axes = kwargs.get("axes_size", [0.12, 0.12, 0.8, 0.8])  # keep track of axes size
        mpl_plotter.__init__(self, *args, **kwargs)

        self.plotflag = False

        # obj containers
        self.text = []
        self.lines = []
        self.patch = []
        self.markers = []
        self.arrows = []
        self.temporary = []  # temporary holder

        self.lock_plot_from_updating = False
        self.lock_plot_from_updating_size = False
        self.plot_parameters = {}
        self.plot_limits = []

        self.plot_name = ""
        self.plot_data = {}
        self.plot_labels = {}

        self.x_divider = 1
        self.y_divider = 1
        self.rotate = 0
        self.document_name = None
        self.dataset_name = None

    def _check_axes_size(self, axes_size, min_left=0.12, min_bottom=0.12, max_width=0.8, max_height=0.8):
        try:
            l, b, w, h = axes_size
        except TypeError:
            return axes_size

        axes_size = [max([l, min_left]), max([b, min_bottom]), min([w, max_width]), min([h, max_height])]

        return axes_size

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

        #         if self.config._plots_check_axes_size:
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
        self.canvas.Copy_to_Clipboard()
        logger.info("Figure was copied to the clipboard")

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
        if kwargs.get("legend", self.config.legend):
            legend = self.plotMS.legend(
                loc=kwargs.get("legend_position", self.config.legendPosition),
                ncol=kwargs.get("legend_num_columns", self.config.legendColumns),
                fontsize=kwargs.get("legend_font_size", self.config.legendFontSize),
                frameon=kwargs.get("legend_frame_on", self.config.legendFrame),
                framealpha=kwargs.get("legend_transparency", self.config.legendAlpha),
                markerfirst=kwargs.get("legend_marker_first", self.config.legendMarkerFirst),
                markerscale=kwargs.get("legend_marker_size", self.config.legendMarkerSize),
                fancybox=kwargs.get("legend_fancy_box", self.config.legendFancyBox),
                scatterpoints=kwargs.get("legend_num_markers", self.config.legendNumberMarkers),
                handles=handles,
            )
            if "legend_zorder" in kwargs:
                legend.set_zorder(kwargs.pop("legend_zorder"))
            legend.draggable()

    def set_colorbar_parameters(self, zvals, **kwargs):
        """Add colorbar to the plot

        Parameters
        ----------
        zvals : np.array
            intensity array
        **kwargs: dict
            dictionary with all plot parameters defined by the user
        """

        try:
            self.cbar.remove()
        except (AttributeError, KeyError):
            pass

        tick_labels = ["0", "%", "100"]
        if self.plot_name in ["RMSD", "RMSF"]:
            tick_labels = ["-100", "%", "100"]

        if kwargs["colorbar"]:
            cbarDivider = make_axes_locatable(self.plotMS)
            # pad controls how close colorbar is to the axes
            self.cbar = cbarDivider.append_axes(
                kwargs["colorbar_position"],
                size="".join([str(kwargs["colorbar_width"]), "%"]),
                pad=kwargs["colorbar_pad"],
            )
            ticks = [np.min(zvals), (np.max(zvals) - np.abs(np.min(zvals))) / 2, np.max(zvals)]

            if ticks[1] in [ticks[0], ticks[2]]:
                ticks[1] = 0

            self.cbar.ticks = ticks
            #             self.cbar.tick_labels = tick_labels

            if kwargs["colorbar_position"] in ["left", "right"]:
                self.figure.colorbar(self.cax, cax=self.cbar, ticks=ticks, orientation="vertical")
                self.cbar.yaxis.set_ticks_position(kwargs["colorbar_position"])
                self.cbar.set_yticklabels(tick_labels)
            else:
                self.figure.colorbar(self.cax, cax=self.cbar, ticks=ticks, orientation="horizontal")
                self.cbar.xaxis.set_ticks_position(kwargs["colorbar_position"])
                self.cbar.set_xticklabels(tick_labels)

            # setup other parameters
            self.cbar.tick_params(labelsize=kwargs["colorbar_label_size"])

    def set_plot_xlabel(self, xlabel, **kwargs):
        kwargs = ut_visuals.check_plot_settings(**kwargs)

        if xlabel is None:
            xlabel = self.plotMS.get_xlabel()
        self.plotMS.set_xlabel(
            xlabel, labelpad=kwargs["label_pad"], fontsize=kwargs["label_size"], weight=kwargs["label_weight"]
        )

    def set_plot_ylabel(self, ylabel, **kwargs):
        kwargs = ut_visuals.check_plot_settings(**kwargs)
        if ylabel is None:
            ylabel = self.plotMS.get_ylabel()
        self.plotMS.set_ylabel(
            ylabel, labelpad=kwargs["label_pad"], fontsize=kwargs["label_size"], weight=kwargs["label_weight"]
        )

    def set_plot_zlabel(self, zlabel, **kwargs):
        kwargs = ut_visuals.check_plot_settings(**kwargs)

        if zlabel is None:
            zlabel = self.plotMS.get_ylabel()
        self.plotMS.set_zlabel(
            zlabel, labelpad=kwargs["label_pad"], fontsize=kwargs["label_size"], weight=kwargs["label_weight"]
        )

    def set_plot_title(self, title, **kwargs):
        kwargs = ut_visuals.check_plot_settings(**kwargs)

        if title is None:
            title = self.plotMS.get_title()

        self.plotMS.set_title(title, fontsize=kwargs["title_size"], weight=kwargs.get("label_weight", "normal"))

    def set_tick_parameters(self, **kwargs):

        matplotlib.rc("xtick", labelsize=kwargs["tick_size"])
        matplotlib.rc("ytick", labelsize=kwargs["tick_size"])

        # update axis frame
        if kwargs["axis_onoff"]:
            self.plotMS.set_axis_on()
        else:
            self.plotMS.set_axis_off()

        self.plotMS.tick_params(
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

        self.plotMS.spines["left"].set_visible(kwargs["spines_left"])
        self.plotMS.spines["right"].set_visible(kwargs["spines_right"])
        self.plotMS.spines["top"].set_visible(kwargs["spines_top"])
        self.plotMS.spines["bottom"].set_visible(kwargs["spines_bottom"])
        [i.set_linewidth(kwargs["frame_width"]) for i in self.plotMS.spines.values()]

    def _convert_intensities(self, values, label, set_divider=True, convert_values=True):
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

    def _convert_intensities_with_preset_divider(self, values, label):
        if self.y_divider is None:
            __, __, __ = self._convert_intensities(values, label)

        divider = self.y_divider
        expo = len(str(divider)) - len(str(divider).rstrip("0"))

        if expo > 1:
            offset_text = r"x$\mathregular{10^{%d}}$" % expo
            label = "".join([label, " [", offset_text, "]"])

        values = np.divide(values, float(divider))

        return values, label, divider

    def _get_colors(self, n_colors):
        if self.config.currentPalette not in ["Spectral", "RdPu"]:
            palette = self.config.currentPalette.lower()
        else:
            palette = self.config.currentPalette
        colorlist = color_palette(palette, n_colors)

        return colorlist

    def _convert_intensities_list(self, values, label):

        _dividers = []
        for i in range(len(values)):
            __, __ylabel, divider = self._convert_intensities(values[i], label, set_divider=False, convert_values=False)
            _dividers.append(divider)

        self.y_divider = np.max(_dividers)

        for i in range(len(values)):
            values[i] = np.divide(values[i], float(divider))

        label = ut_visuals.add_exponent_to_label(label, self.y_divider)

        return values, label

    def _check_colormap(self, cmap=None, **kwargs):
        if cmap is None:
            if kwargs["colormap"] in self.config.cmocean_cmaps:
                kwargs["colormap"] = eval("cmocean.cm.%s" % kwargs["colormap"])

            return kwargs
        else:
            if cmap in self.config.cmocean_cmaps:
                cmap = eval("cmocean.cm.%s" % cmap)

            return cmap

    def _fix_label_positions(self, lim=20):
        """
        Try to fix position of labels to prevent overlap
        """
        try:
            adjust_text(self.text, lim=lim)
        except Exception:
            pass

    def get_xylimits(self):
        xmin, xmax = self.plotMS.get_xlim()
        ymin, ymax = self.plotMS.get_ylim()

        return [xmin, xmax, ymin, ymax]

    def set_xylimits(self, xylimits):
        # xylimits = [xmin, xmax, ymin, ymax]

        self.plotMS.set_xlim([xylimits[0], xylimits[1]])
        self.plotMS.set_ylim([xylimits[2], xylimits[3]])

        extent = [xylimits[0], xylimits[2], xylimits[1], xylimits[3]]
        self.update_extents(extent)

    def on_zoom_x_axis(self, xmin, xmax):
        self.plotMS.set_xlim([xmin, xmax])

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

        self.plotMS.set_ylim([startY, endY])
        self.update_y_extents(startY, endY)

    def on_zoom_xy(self, startX, endX, startY, endY):
        try:
            startY = startY / float(self.y_divider)
            endY = endY / float(self.y_divider)
        except Exception:
            pass
        try:
            self.plotMS.axis([startX, endX, startY, endY])
            self.repaint()
        except Exception:
            pass

    def on_zoom(self, startX, endX, endY):
        try:
            endY = endY / float(self.y_divider)
        except Exception:
            pass
        try:
            self.plotMS.axis([startX, endX, 0, endY])
            self.repaint()
        except Exception:
            pass

    def on_rotate_heatmap_data(self, yvals, zvals):

        # rotate zvals
        zvals = np.rot90(zvals)
        yvals = yvals[::-1]

        return yvals, zvals

    def on_rotate_90(self):
        # only works for 2D plots!

        if hasattr(self, "plot_data"):
            if len(self.plot_data) == 0:
                return

            self.rotate = self.rotate + 90

            yvals = deepcopy(self.plot_data["xvals"])
            xvals = deepcopy(self.plot_data["yvals"])
            ylabel = deepcopy(self.plot_data["xlabel"])
            xlabel = deepcopy(self.plot_data["ylabel"])
            zvals = deepcopy(self.plot_data["zvals"])

            yvals, zvals = self.on_rotate_heatmap_data(yvals, zvals)
            self.plot_2D_update_data(xvals, yvals, xlabel, ylabel, zvals, already_rotated=True, **self.plot_parameters)

            if self.rotate == 360:
                self.rotate = 0

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

        if stick_to_intensity:
            try:
                ymin = np.divide(ymin, self.y_divider)
                dy = np.divide(dy, self.y_divider)
            except Exception:
                pass

        if dx == 0 and dy == 0:
            return

        # get custom name tag
        obj_name = kwargs.pop("text_name", None)
        obj_props = kwargs.pop("props", [None, None])
        arrow = self.plotMS.arrow(
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
            yvals, __, __ = self._convert_intensities(yvals, "")

        if kwargs.get("test_yvals_with_preset_divider", False):
            yvals, __, __ = self._convert_intensities_with_preset_divider(yvals, label)

        if test_xvals:
            xvals, __, __ = self.kda_test(xvals)

        markers = self.plotMS.scatter(
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

    def plot_remove_markers(self):

        for marker in self.markers:
            try:
                marker.remove()
            except Exception:
                pass

        self.markers = []
        self.repaint()

    def plot_remove_lines(self, label_starts_with):
        try:
            lines = self.plotMS.get_lines()
        except AttributeError:
            raise MessageError("Error", "Please plot something first")
        for line in lines:
            line_label = line.get_label()
            if line_label.startswith(label_starts_with):
                line.remove()

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

        try:
            ymin, ymax = self.plotMS.get_ylim()
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
        obj_name = kwargs.pop("text_name", None)
        text = self.plotMS.text(
            np.array(xpos),
            y_position + yoffset,
            label,
            horizontalalignment=kwargs.pop("horizontalalignment", "center"),
            verticalalignment=kwargs.pop("verticalalignment", "top"),
            color=color,
            picker=True,
            **kwargs,
        )
        text.obj_name = obj_name  # custom tag
        self.text.append(text)

        if vline:
            if vline_position is not None:
                xpos = vline_position
            line = self.plotMS.axvline(xpos, ymin, yval * 0.8, color=color, linestyle="dashed", alpha=0.4)
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

        text = self.plotMS.text(
            np.array(xpos), yval + yoffset, label, color=color, clip_on=True, zorder=zorder, picker=True, **kwargs
        )
        text._yposition = yval - kwargs.get("labels_y_offset", self.config.waterfall_labels_y_offset)
        text.obj_name = obj_name  # custom tag
        self.text.append(text)

    def plot_remove_text(self):
        for text in self.text:
            try:
                text.remove()
            except Exception:
                pass

        self.text = []
        self.repaint()

    def plot_add_patch(
        self, xmin, ymin, width, height, color="r", alpha=0.5, linewidth=0, add_temporary=False, label="", **kwargs
    ):

        # check if need to rescale height
        try:
            height = np.divide(height, self.y_divider)
        except Exception:
            pass
        try:
            patch = self.plotMS.add_patch(
                patches.Rectangle((xmin, ymin), width, height, color=color, alpha=alpha, linewidth=linewidth)
            )
        except AttributeError:
            print("Please plot something first")
            return

        # set label
        patch.obj_name = label

        if add_temporary:
            self.plot_remove_temporary()
            self.temporary.append(patch)
        else:
            self.patch.append(patch)

    def plot_remove_patches(self):

        for patch in self.patch:
            try:
                patch.remove()
            except Exception:
                pass

        self.patch = []
        self.repaint()

    def plot_remove_temporary(self, repaint=False):
        for patch in self.temporary:
            try:
                patch.remove()
            except Exception:
                pass

        self.temporary = []
        if repaint:
            self.repaint()

    def plot_remove_text_and_lines(self):

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

        self.repaint()

    def plot_1D_update_data_only(self, xvals, yvals):
        kwargs = self.plot_parameters

        lines = self.plotMS.get_lines()
        ylabel = self.plotMS.get_ylabel()
        ylabel = ylabel.split(" [")[0]

        yvals, ylabel, __ = self._convert_intensities(yvals, ylabel)

        lines[0].set_xdata(xvals)
        lines[0].set_ydata(yvals)

        self.set_plot_ylabel(ylabel, **kwargs)

    def plot_1D_get_data(self):
        xdata, ydata, labels = [], [], []

        lines = self.plotMS.get_lines()
        for line in lines:
            xdata.append(line.get_xdata())
            ydata.append(line.get_ydata() * self.y_divider)
            labels.append(line.get_label())

        xlabel = self.plotMS.get_xlabel()
        ylabel = self.plotMS.get_ylabel()
        return xdata, ydata, labels, xlabel, ylabel

    def plot_2D_get_data(self):

        #         xvals, yvals, zvals = [], [], []
        #         zvals = self.cax.get_array()
        #         xlabel = self.plotMS.get_xlabel()
        #         ylabel = self.plotMS.get_ylabel()

        return self.plot_data

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
        lines = self.plotMS.get_lines()
        for line in lines[1:]:
            line.remove()

        # remove old shades
        while len(self.plotMS.collections) > 0:
            for shade in self.plotMS.collections:
                shade.remove()

        if testMax == "yvals":
            yvals, ylabel, __ = self._convert_intensities(yvals, ylabel)

        if kwargs.pop("testX", False):
            xvals, xlabel, __ = self.kda_test(xvals)

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
            self.plotMS.fill_between(xvals, 0, yvals, **shade_kws)

        # convert weights
        if kwargs["label_weight"]:
            kwargs["label_weight"] = "heavy"
        else:
            kwargs["label_weight"] = "normal"

        self.plotMS.set_xlim(xlimits)
        self.plotMS.set_ylim(ylimits)
        self.set_plot_xlabel(xlabel, **kwargs)
        self.set_plot_ylabel(ylabel, **kwargs)

        if kwargs.get("minor_ticks_off", False) or xlabel == "Scans" or xlabel == "Charge":
            self.plotMS.xaxis.set_tick_params(which="minor", bottom="off")
            self.plotMS.xaxis.set_major_locator(MaxNLocator(integer=True))

        self.update_extents(extent)
        self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]

        self.plot_labels.update({"xlabel": xlabel, "ylabel": ylabel})

        # update legend
        handles, __ = self.plotMS.get_legend_handles_labels()
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
        lines = self.plotMS.get_lines()

        # calculate divider
        __, __, divider = self._convert_intensities(yvals, "", set_divider=False, convert_values=False)
        #         divider = np.max([divider, self.y_divider])

        # convert ylabel based on the divider
        ylabel = ut_visuals.add_exponent_to_label(self.plotMS.get_ylabel(), divider)
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
        yvals, __, __ = self._convert_intensities_with_preset_divider(yvals, "")
        for line in lines:
            plot_gid = line.get_gid()
            if plot_gid == gid:
                line.set_xdata(xvals)
                line.set_ydata(yvals)
                line.set_label(label)
                break

        # update legend
        handles, __ = self.plotMS.get_legend_handles_labels()
        self.set_legend_parameters(handles, **self.plot_parameters)

        # update plot limits
        ylimits = get_min_max(get_min_max(yvals) + ylimits)
        self.on_zoom_y_axis(ylimits[0], ylimits[1], convert_values=False)

    def plot_1D_update_style_by_label(self, gid, **kwargs):

        lines = self.plotMS.get_lines()
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

        handles, __ = self.plotMS.get_legend_handles_labels()
        self.set_legend_parameters(handles, **self.plot_parameters)

    def _plot_1D_compare_prepare_data(self, yvals_1, yvals_2, ylabel=None):
        if ylabel is None:
            ylabel = self.plotMS.get_ylabel()

        yvals_1, __, divider_1 = self._convert_intensities(yvals_1, "", convert_values=False)
        yvals_2, __, divider_2 = self._convert_intensities(yvals_2, "", convert_values=False)
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
        lines = self.plotMS.get_lines()
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
        handles, __ = self.plotMS.get_legend_handles_labels()
        self.set_legend_parameters(handles, **self.plot_parameters)

        # update plot limits
        ylimits = get_min_max(ylimits)
        self.on_zoom_y_axis(ylimits[0], ylimits[1], convert_values=False)

    def plot_1D_waterfall_update(self, which="other", **kwargs):
        if self.lock_plot_from_updating:
            msg = (
                "This plot is locked and you cannot use global setting updated. \n"
                + "Please right-click in the plot area and select Customise plot..."
                + " to adjust plot settings."
            )
            print(msg)
            return

        if self.plot_name == "Waterfall_overlay" and which in ["color", "data"]:
            return

        if which in ["other", "style"]:
            if self.plot_name != "Violin":
                for i, line in enumerate(self.plotMS.get_lines()):
                    line.set_linestyle(kwargs["line_style"])
                    line.set_linewidth(kwargs["line_width"])
            else:
                for shade in range(len(self.plotMS.collections)):
                    self.plotMS.collections[shade].set_linestyle(kwargs["line_style"])
                    self.plotMS.collections[shade].set_linewidth(kwargs["line_width"])

        elif which == "color":
            n_colors = len(self.plotMS.get_lines())
            n_patch_colors = len(self.plotMS.collections)
            if n_colors != n_patch_colors:
                if n_patch_colors > n_colors:
                    n_colors = n_patch_colors

            if kwargs["color_scheme"] == "Colormap":
                colorlist = color_palette(kwargs["colormap"], n_colors)

            elif kwargs["color_scheme"] == "Color palette":
                if kwargs["palette"] not in ["Spectral", "RdPu"]:
                    kwargs["palette"] = kwargs["palette"].lower()
                colorlist = color_palette(kwargs["palette"], n_colors)

            elif kwargs["color_scheme"] == "Same color":
                colorlist = [kwargs["shade_color"]] * n_colors

            elif kwargs["color_scheme"] == "Random":
                colorlist = []
                for __ in range(n_colors):
                    colorlist.append(randomColorGenerator())

            if self.plot_name != "Violin":
                for i, line in enumerate(self.plotMS.get_lines()):
                    if kwargs["line_color_as_shade"]:
                        line_color = colorlist[i]
                    else:
                        line_color = kwargs["line_color"]
                    line.set_color(line_color)
            else:
                for i in range(len(self.plotMS.collections)):
                    if kwargs["line_color_as_shade"]:
                        line_color = colorlist[i]
                    else:
                        line_color = kwargs["line_color"]
                    self.plotMS.collections[i].set_edgecolor(line_color)

            for shade in range(len(self.plotMS.collections)):
                shade_color = colorlist[shade]
                self.plotMS.collections[shade].set_facecolor(shade_color)

        elif which == "shade":
            try:
                for shade in range(len(self.plotMS.collections)):
                    self.plotMS.collections[shade].set_alpha(kwargs["shade_under_transparency"])
            except AttributeError:
                pass

        elif which == "label":
            # convert weights
            if kwargs["labels_font_weight"]:
                kwargs["labels_font_weight"] = "heavy"
            else:
                kwargs["labels_font_weight"] = "normal"

            # calculate new position
            label_xposition = self.text_offset_position["min"] + (
                self.text_offset_position["max"] * kwargs["labels_x_offset"]
            )

            for i in range(len(self.text)):
                self.text[i].set_fontweight(kwargs["labels_font_weight"])
                self.text[i].set_fontsize(kwargs["labels_font_size"])
                yposition = self.text[i]._yposition + kwargs["labels_y_offset"]
                position = [label_xposition, yposition]
                self.text[i].set_position(position)
                text = ut_visuals.convert_label(self.text[i].get_text(), label_format=kwargs["labels_format"])
                self.text[i].set_text(text)

        elif which == "data":
            # TODO: fix an issue when there is shade under the curve
            # fix might be here: https://stackoverflow.com/questions/16120801/matplotlib-animate-fill-between-shape
            count = 0
            increment = kwargs["increment"] - self.plot_parameters["increment"]
            offset = kwargs["offset"]  # - self.plot_parameters['offset']
            ydata = []
            #             print(dir(self.plotMS.collections[0]),
            #                   self.plotMS.collections[2]._offset_position)
            #             for shade in range(len(self.plotMS.collections)):
            #                 self.plotMS.collections[shade].set_offsets(100.)
            #                 print(self.plotMS.collections[shade].get_paths())
            #                 print(dir_extra(dir(self.plotMS.collections[shade]), "set"))
            for i, line in enumerate(self.plotMS.get_lines()):
                yvals = line.get_ydata()
                if len(yvals) > 5:
                    count = +1
            yOffset = 0  # offset*(count+1)
            for i, line in enumerate(self.plotMS.get_lines()):
                yvals = line.get_ydata()
                if len(yvals) > 5:
                    new_yvals = yvals + yOffset
                    line.set_ydata(new_yvals)
                    ydata.extend(new_yvals)
                    yOffset = yOffset - increment

            # remove nans
            ydata = np.array(ydata)
            ydata = ydata[~np.isnan(ydata)]
            self.plot_limits[2] = np.min(ydata) - offset
            self.plot_limits[3] = np.max(ydata) + 0.05
            extent = [self.plot_limits[0], self.plot_limits[2], self.plot_limits[1], self.plot_limits[3]]
            self.update_extents(extent)
            self.plotMS.set_xlim((self.plot_limits[0], self.plot_limits[1]))
            self.plotMS.set_ylim((self.plot_limits[2], self.plot_limits[3]))

        elif which == "frame":
            self.set_tick_parameters(**kwargs)

        elif which == "fonts":
            # update ticks
            matplotlib.rc("xtick", labelsize=kwargs["tick_size"])
            matplotlib.rc("ytick", labelsize=kwargs["tick_size"])

            kwargs = ut_visuals.check_plot_settings(**kwargs)

            # update labels
            self.set_plot_xlabel(None, **kwargs)
            self.set_plot_ylabel(None, **kwargs)

            # Setup font size info
            self.plotMS.tick_params(labelsize=kwargs["tick_size"])

        self.plot_parameters = kwargs

    def plot_1D_update(self, **kwargs):
        if self.lock_plot_from_updating:
            msg = (
                "This plot is locked and you cannot use global setting updated. \n"
                + "Please right-click in the plot area and select Customise plot..."
                + " to adjust plot settings."
            )
            print(msg)
            return

        # convert weights
        if kwargs["label_weight"]:
            kwargs["label_weight"] = "heavy"
        else:
            kwargs["label_weight"] = "normal"

        self.set_plot_xlabel(None, **kwargs)
        self.set_plot_ylabel(None, **kwargs)
        self.set_tick_parameters(**kwargs)

        for __, line in enumerate(self.plotMS.get_lines()):
            line.set_linewidth(kwargs["line_width"])
            line.set_linestyle(kwargs["line_style"])

        self._update_plot_settings_(**kwargs)

    def plot_1D_update_rmsf(self, **kwargs):
        if self.lock_plot_from_updating:
            msg = (
                "This plot is locked and you cannot use global setting updated. \n"
                + "Please right-click in the plot area and select Customise plot..."
                + " to adjust plot settings."
            )
            print(msg)
            return

        # update ticks
        matplotlib.rc("xtick", labelsize=kwargs["tick_size"])
        matplotlib.rc("ytick", labelsize=kwargs["tick_size"])

        # convert weights
        if kwargs["label_weight"]:
            kwargs["label_weight"] = "heavy"
        else:
            kwargs["label_weight"] = "normal"

        # update labels
        self.plotRMSF.set_xlabel(
            self.plotMS.get_xlabel(),
            labelpad=kwargs["label_pad"],
            fontsize=kwargs["label_size"],
            weight=kwargs["label_weight"],
        )
        self.plotRMSF.set_ylabel(
            self.plotMS.get_ylabel(),
            labelpad=kwargs["label_pad"],
            fontsize=kwargs["label_size"],
            weight=kwargs["label_weight"],
        )
        # Setup font size info
        self.plotRMSF.tick_params(labelsize=kwargs["tick_size"])

        # update axis frame
        if kwargs["axis_onoff"]:
            self.plotRMSF.set_axis_on()
        else:
            self.plotRMSF.set_axis_off()

        self.plotRMSF.tick_params(
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

        for i, line in enumerate(self.plotRMSF.get_lines()):
            line.set_linewidth(kwargs["rmsd_line_width"])
            line.set_linestyle(kwargs["rmsd_line_style"])
            line.set_color(kwargs["rmsd_line_color"])

        self.plotRMSF.spines["left"].set_visible(kwargs["spines_left"])
        self.plotRMSF.spines["right"].set_visible(kwargs["spines_right"])
        self.plotRMSF.spines["top"].set_visible(kwargs["spines_top"])
        self.plotRMSF.spines["bottom"].set_visible(kwargs["spines_bottom"])
        [i.set_linewidth(kwargs["frame_width"]) for i in self.plotMS.spines.values()]

    def plot_2D_update_label(self, **kwargs):

        if kwargs["rmsd_label_coordinates"] != [None, None]:
            self.text.set_position(kwargs["rmsd_label_coordinates"])
            self.text.set_visible(True)
        else:
            self.text.set_visible(False)

        # convert weights
        if kwargs["rmsd_label_font_weight"]:
            kwargs["rmsd_label_font_weight"] = "heavy"
        else:
            kwargs["rmsd_label_font_weight"] = "normal"

        self.text.set_fontweight(kwargs["rmsd_label_font_weight"])
        self.text.set_fontsize(kwargs["rmsd_label_font_size"])
        self.text.set_color(kwargs["rmsd_label_color"])

    def plot_2D_update(self, **kwargs):

        if self.lock_plot_from_updating:
            msg = (
                "This plot is locked and you cannot use global setting updated. \n"
                + "Please right-click in the plot area and select Customise plot..."
                + " to adjust plot settings."
            )
            print(msg)
            return

        try:
            cbar_yticks = self.cbar.get_yticklabels()
            cbar_xticks = self.cbar.get_xticklabels()
        except Exception:
            pass

        if "colormap_norm" in kwargs:
            self.cax.set_norm(kwargs["colormap_norm"])

        #         kwargs = self._check_colormap(**kwargs)
        self.cax.set_cmap(kwargs["colormap"])

        try:
            self.cax.set_interpolation(kwargs["interpolation"])
        except AttributeError:
            pass

        # update labels
        self.set_plot_xlabel(None, **kwargs)
        self.set_plot_ylabel(None, **kwargs)
        self.set_tick_parameters(**kwargs)

        # update axis frame
        try:
            self.cbar.set_visible(kwargs["colorbar"])
            if len(cbar_yticks) > len(cbar_xticks):
                self.cbar.set_yticklabels(["0", "%", "100"])
            else:
                self.cbar.set_xticklabels(["0", "%", "100"])
        except Exception:
            pass

        self.plot_parameters = kwargs

    def plot_update_axes(self, axes_sizes):
        self.plotMS.set_position(axes_sizes)
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

    def plot_2D_matrix_update_label(self, **kwargs):

        self.plotMS.set_xticklabels(self.plotMS.get_xticklabels(), rotation=kwargs["rmsd_matrix_rotX"])
        self.plotMS.set_yticklabels(self.plotMS.get_xticklabels(), rotation=kwargs["rmsd_matrix_rotY"])

        for text in self.text:
            text.set_visible(kwargs["rmsd_matrix_labels"])

    def plot_3D_update(self, which="all", **kwargs):

        # Setup font size info
        self.plotMS.tick_params(labelsize=kwargs["tick_size"])

        self.plotMS.w_xaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        self.plotMS.w_yaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        self.plotMS.w_zaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))

        # Get rid of spines
        if not kwargs["show_spines"]:
            self.plotMS.w_xaxis.line.set_color((1.0, 1.0, 1.0, 0.0))
            self.plotMS.w_yaxis.line.set_color((1.0, 1.0, 1.0, 0.0))
            self.plotMS.w_zaxis.line.set_color((1.0, 1.0, 1.0, 0.0))
        else:
            self.plotMS.w_xaxis.line.set_color((0.0, 0.0, 0.0, 0.0))
            self.plotMS.w_yaxis.line.set_color((0.0, 0.0, 0.0, 0.0))
            self.plotMS.w_zaxis.line.set_color((0.0, 0.0, 0.0, 0.0))

        # Get rid of the ticks
        if not kwargs["show_ticks"]:
            self.plotMS.set_xticks([])
            self.plotMS.set_yticks([])
            self.plotMS.set_zticks([])

        # convert weights
        if kwargs["label_weight"]:
            kwargs["label_weight"] = "heavy"
        else:
            kwargs["label_weight"] = "normal"

        # update labels
        self.plotMS.set_xlabel(
            self.plotMS.get_xlabel(),
            labelpad=kwargs["label_pad"],
            fontsize=kwargs["label_size"],
            weight=kwargs["label_weight"],
            visible=kwargs["show_labels"],
        )
        self.plotMS.set_ylabel(
            self.plotMS.get_ylabel(),
            labelpad=kwargs["label_pad"],
            fontsize=kwargs["label_size"],
            weight=kwargs["label_weight"],
            visible=kwargs["show_labels"],
        )
        self.plotMS.set_zlabel(
            self.plotMS.get_zlabel(),
            labelpad=kwargs["label_pad"],
            fontsize=kwargs["label_size"],
            weight=kwargs["label_weight"],
            visible=kwargs["show_labels"],
        )

        matplotlib.rc("xtick", labelsize=kwargs["tick_size"])
        matplotlib.rc("ytick", labelsize=kwargs["tick_size"])

        self.plotMS.grid(kwargs["grid"])

    def plot_2D_colorbar_update(self, **kwargs):

        if self.lock_plot_from_updating:
            msg = (
                "This plot is locked and you cannot use global setting updated. \n"
                + "Please right-click in the plot area and select Customise plot..."
                + " to adjust plot settings."
            )
            print(msg)
            return

        try:
            if kwargs["colorbar"]:
                cbarDivider = make_axes_locatable(self.plotMS)

                if hasattr(self.cbar, "ticks"):
                    ticks = self.cbar.ticks
                elif hasattr(self, "ticks"):
                    ticks = self.ticks

                if hasattr(self.cbar, "tick_labels"):
                    tick_labels = self.cbar.tick_labels
                elif hasattr(self, "tick_labels"):
                    tick_labels = self.tick_labels

                try:
                    self.cbar.remove()
                except Exception:
                    pass
                self.cbar = cbarDivider.append_axes(
                    kwargs["colorbar_position"],
                    size="".join([str(kwargs["colorbar_width"]), "%"]),
                    pad=kwargs["colorbar_pad"],
                )

                self.cbar.ticks = ticks
                self.cbar.tick_labels = tick_labels

                if kwargs["colorbar_position"] in ["left", "right"]:
                    self.figure.colorbar(self.cax, cax=self.cbar, ticks=ticks, orientation="vertical")
                    self.cbar.yaxis.set_ticks_position(kwargs["colorbar_position"])
                    self.cbar.set_yticklabels(tick_labels)
                else:
                    self.figure.colorbar(self.cax, cax=self.cbar, ticks=ticks, orientation="horizontal")
                    self.cbar.xaxis.set_ticks_position(kwargs["colorbar_position"])
                    self.cbar.set_xticklabels(tick_labels)

                self.cbar.tick_params(labelsize=kwargs["colorbar_label_size"])
            else:
                if hasattr(self.cbar, "ticks"):
                    self.ticks = self.cbar.ticks
                if hasattr(self.cbar, "tick_labels"):
                    self.tick_labels = self.cbar.tick_labels

                self.cbar.remove()
        except Exception:
            pass

    def plot_2D_update_normalization(self, **kwargs):

        if self.lock_plot_from_updating:
            msg = (
                "This plot is locked and you cannot use global setting updated. \n"
                + "Please right-click in the plot area and select Customise plot..."
                + " to adjust plot settings."
            )
            print(msg)
            return

        if hasattr(self, "plot_data"):
            if "zvals" in self.plot_data:
                # normalize
                zvals_max = np.max(self.plot_data["zvals"])

                cmap_min = (zvals_max * kwargs["colormap_min"]) / 100.0
                cmap_mid = (zvals_max * kwargs["colormap_mid"]) / 100.0
                cmap_max = (zvals_max * kwargs["colormap_max"]) / 100.0

                cmap_norm = MidpointNormalize(midpoint=cmap_mid, vmin=cmap_min, vmax=cmap_max)

                self.plot_parameters["colormap_norm"] = cmap_norm

                if "colormap_norm" in self.plot_parameters:
                    self.cax.set_norm(self.plot_parameters["colormap_norm"])
                    self.plot_2D_colorbar_update(**kwargs)

    def plot_1D_add(self, xvals, yvals, color, label="", setup_zoom=True, allowWheel=False, plot_name=None, **kwargs):
        # get current limits
        xmin, xmax = self.plotMS.get_xlim()

        if plot_name is not None:
            self.plot_name = plot_name
        self.plotMS.plot(np.array(xvals), yvals, color=color, label=label, linewidth=kwargs.get("line_width", 2.0))

        lines = self.plotMS.get_lines()
        yvals_limits = []
        for line in lines:
            yvals_limits.extend(line.get_ydata())

        xlimits = [np.min(xvals), np.max(xvals)]
        ylimits = [np.min(yvals_limits), np.max(yvals_limits)]

        self.plotMS.set_xlim([xlimits[0], xlimits[1]])
        self.plotMS.set_ylim([ylimits[0], ylimits[1] + 0.025])

        extent = [xlimits[0], ylimits[0], xlimits[-1], ylimits[-1] + 0.025]
        if kwargs.get("update_extents", False):
            self.update_extents(extent)
            self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]

        if setup_zoom:
            self.setup_zoom([self.plotMS], self.zoomtype, data_lims=extent, plotName=plot_name, allowWheel=allowWheel)
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
            leg = self.plotMS.axes.get_legend()
            leg.remove()
        except (AttributeError, KeyError):
            pass

    def plot_2D_update_data(self, xvals, yvals, xlabel, ylabel, zvals, **kwargs):

        # rotate data
        if self.rotate != 0 and not kwargs.pop("already_rotated", False):
            yvals, zvals = self.on_rotate_heatmap_data(yvals, zvals)

        # update settings
        self._check_and_update_plot_settings(**kwargs)

        # update limits and extents
        extent = ut_visuals.extents(xvals) + ut_visuals.extents(yvals)
        self.cax.set_data(zvals)
        #         vmax = np.quantile(zvals, 0.95)
        #         self.cax.set_clim(vmax=vmax)
        self.cax.set_norm(kwargs.get("colormap_norm", None))
        self.cax.set_extent(extent)
        self.cax.set_cmap(kwargs["colormap"])
        self.cax.set_interpolation(kwargs["interpolation"])

        xmin, xmax, ymin, ymax = extent
        self.plotMS.set_xlim(xmin, xmax)
        self.plotMS.set_ylim(ymin, ymax)

        extent = [xmin, ymin, xmax, ymax]
        if kwargs.get("update_extents", True):
            self.update_extents(extent)
            self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]

        self.set_plot_xlabel(xlabel, **kwargs)
        self.set_plot_ylabel(ylabel, **kwargs)

        try:
            leg = self.plotMS.axes.get_legend()
            leg.remove()
        except Exception:
            pass

        # add data
        self.plot_data = {"xvals": xvals, "yvals": yvals, "zvals": zvals, "xlabel": xlabel, "ylabel": ylabel}
        self.plot_labels.update({"xlabel": xlabel, "ylabel": ylabel})

        # add colorbar
        if kwargs["colorbar"]:
            self.set_colorbar_parameters(zvals, **kwargs)

    def plot_1D(
        self,
        xvals=None,
        yvals=None,
        title="",
        xlabel="",
        ylabel="",
        label="",
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
            yvals, ylabel, __ = self._convert_intensities(yvals, ylabel)

        if testX:
            xvals, xlabel, __ = self.kda_test(xvals)

        # Simple hack to reduce size is to use different subplot size
        self.plotMS = self.figure.add_axes(self._axes)
        self.plotMS.plot(
            xvals,
            yvals,
            color=kwargs["line_color"],
            label=label,
            linewidth=kwargs["line_width"],
            linestyle=kwargs["line_style"],
        )
        if kwargs["shade_under"]:
            shade_kws = dict(
                facecolor=kwargs["shade_under_color"],
                alpha=kwargs.get("shade_under_transparency", 0.25),
                clip_on=kwargs.get("clip_on", True),
                zorder=kwargs.get("zorder", 1),
            )
            self.plotMS.fill_between(xvals, 0, yvals, **shade_kws)

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
        self.plotMS.set_xlim(xlimits)
        self.plotMS.set_ylim(ylimits)

        if kwargs.get("minor_ticks_off", False) or xlabel == "Scans" or xlabel == "Charge":
            self.plotMS.xaxis.set_tick_params(which="minor", bottom="off")
            self.plotMS.xaxis.set_major_locator(MaxNLocator(integer=True))

        self.set_plot_xlabel(xlabel, **kwargs)
        self.set_plot_ylabel(ylabel, **kwargs)
        self.set_tick_parameters(**kwargs)

        for __, line in enumerate(self.plotMS.get_lines()):
            line.set_linewidth(kwargs["line_width"])
            line.set_linestyle(kwargs["line_style"])

        if title != "":
            self.set_plot_title(title, **kwargs)

        self.setup_zoom(
            [self.plotMS],
            self.zoomtype,
            data_lims=extent,
            plotName=plotType,
            allowWheel=allowWheel,
            preventExtraction=kwargs.get("prevent_extraction", False),
        )

        # Setup X-axis getter
        self.setupGetXAxies([self.plotMS])
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
            self.plotMS.axhline(linewidth=kwargs["line_width"], color="k")

        if update_y_axis:
            yvals, ylabel, __ = self._convert_intensities(yvals, ylabel)
        else:
            yvals = np.divide(yvals, float(self.y_divider))

        if xyvals is None:
            xyvals = ut_visuals.convert_to_vertical_line_input(xvals, yvals)

        # Simple hack to reduce size is to use different subplot size
        if not adding_on_top:
            self.plotMS = self.figure.add_axes(self._axes)
        else:
            self.plotMS.set_position(self._axes)
        line_coll = LineCollection(xyvals, colors=(kwargs["line_color"]), linewidths=(kwargs["line_width"]))
        self.plotMS.add_collection(line_coll)

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
        self.plotMS.set_xlim(xlimits)
        self.plotMS.set_ylim(ylimits)

        self.set_plot_xlabel(xlabel, **kwargs)
        self.set_plot_ylabel(ylabel, **kwargs)
        self.set_tick_parameters(**kwargs)

        for __, line in enumerate(self.plotMS.get_lines()):
            line.set_linewidth(kwargs["line_width"])
            line.set_linestyle(kwargs["line_style"])

        if title != "":
            self.set_plot_title(title, **kwargs)

        self.setup_zoom([self.plotMS], self.zoomtype, data_lims=extent, plotName=plot_name, allowWheel=True)

        # Setup X-axis getter
        self.setupGetXAxies([self.plotMS])
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
        self.plotMS = self.figure.add_axes(self._axes, xticks=xticloc)
        self.plotMS.bar(
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
        self.plotMS.set_xticklabels(peaklabels, rotation=90, fontsize=kwargs["label_size"])  # 90
        self.set_plot_xlabel(xlabel, **kwargs)
        self.set_plot_ylabel(ylabel, **kwargs)
        self.set_tick_parameters(**kwargs)

        for __, line in enumerate(self.plotMS.get_lines()):
            line.set_linewidth(kwargs["line_width"])
            line.set_linestyle(kwargs["line_style"])

        if title != "":
            self.set_plot_title(title, **kwargs)

        xlimits = self.plotMS.get_xlim()
        ylimits = self.plotMS.get_ylim()
        extent = [xlimits[0], ylimits[0], xlimits[1], ylimits[1]]
        self.setup_zoom([self.plotMS], self.zoomtype, plotName=plotType, data_lims=extent)

    def plot_floating_barplot(
        self, xvals, yvals_min, yvals_max, xlabel, ylabel, colors=[], axesSize=None, plotName="bar", **kwargs
    ):
        # update settings
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

            self.plotMS = self.figure.add_axes(self._axes)
            if not kwargs.get("bar_edgecolor_sameAsFill", True):
                edgecolor = kwargs.get("bar_edgecolor", "#000000")
            else:
                edgecolor = colorList

            if kwargs["orientation"] == "vertical-bar":
                self.plotMS.bar(
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
                self.plotMS.barh(
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
        self.setup_zoom([self.plotMS], self.zoomtype, data_lims=extent)
        #
        # Setup X-axis getter
        self.setupGetXAxies([self.plotMS])
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
        labels=[],
        title="",
        xlabel="",
        ylabel="",
        xlimits=None,
        axesSize=None,
        plotName="whole",
        **kwargs,
    ):
        # update settings
        self._check_and_update_plot_settings(plot_name=plotName, axes_size=axesSize, **kwargs)

        # Plot
        self.plotMS = self.figure.add_axes(self._axes)
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
                        plot = self.plotMS.scatter(
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
                        plot = self.plotMS.scatter(
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
                    plot = self.plotMS.scatter(
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
                plot = self.plotMS.scatter(
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
        self.plotMS.set_xlim([xlimits[0], xlimits[1]])
        self.plotMS.set_ylim([ylimits[0], ylimits[1]])
        extent = [xlimits[0], ylimits[0], xlimits[1], ylimits[1]]

        self.set_plot_xlabel(xlabel, **kwargs)
        self.set_plot_ylabel(ylabel, **kwargs)
        self.set_tick_parameters(**kwargs)

        self.setup_zoom([self.plotMS], self.zoomtype, data_lims=extent)

        # Setup X-axis getter
        self.setupGetXAxies([self.plotMS])
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

        self.plotMS = self.figure.add_axes(self._axes)
        self.plotMS.plot(
            xvals1,
            yvals1,
            color=kwargs["line_color_1"],
            label=label[0],
            linewidth=kwargs["line_width"],
            linestyle=kwargs["line_style_1"],
            alpha=kwargs["line_transparency_1"],
            gid=0,
        )

        self.plotMS.plot(
            xvals2,
            yvals2,
            color=kwargs["line_color_2"],
            label=label[1],
            linewidth=kwargs["line_width"],
            linestyle=kwargs["line_style_2"],
            alpha=kwargs["line_transparency_2"],
            gid=1,
        )

        self.plotMS.axhline(linewidth=kwargs["line_width"], color="k")

        xlimits = np.min([np.min(xvals1), np.min(xvals2)]), np.max([np.max(xvals1), np.max(xvals2)])
        ylimits = np.min([np.min(yvals1), np.min(yvals2)]), np.max([np.max(yvals1), np.max(yvals2)])
        extent = [xlimits[0], ylimits[0] - 0.01, xlimits[-1], ylimits[1] + 0.01]

        self.set_plot_xlabel(xlabel, **kwargs)
        self.set_plot_ylabel(ylabel, **kwargs)
        self.set_legend_parameters(None, **kwargs)
        self.set_tick_parameters(**kwargs)
        self.setup_zoom([self.plotMS], self.zoomtype, data_lims=extent, plotName=plotType)

        # Setup X-axis getter
        self.setupGetXAxies([self.plotMS])
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

        yvals, ylabel = self._convert_intensities_list(yvals, ylabel)

        xlabel = _replace_labels(xlabel)
        ylabel = _replace_labels(ylabel)

        # Plot
        self.plotMS = self.figure.add_axes(self._axes)

        handles = []
        zorder, zorder_offset = 5, 5
        for xval, yval, color, label in zip(xvals, yvals, colors, labels):
            label = _replace_labels(label)
            self.plotMS.plot(
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
                self.plotMS.fill_between(xval, 0, yval, **shade_kws)
                zorder = zorder + zorder_offset

        if not kwargs["shade_under"]:
            handles, labels = self.plotMS.get_legend_handles_labels()

        # add legend
        self.set_legend_parameters(handles, legend_zorder=zorder + 10, **kwargs)

        self.set_plot_xlabel(xlabel, **kwargs)
        self.set_plot_ylabel(ylabel, **kwargs)

        self.plotMS.set_xlim(xlimits)
        self.plotMS.set_ylim([np.min(np.concatenate(yvals)), np.max(np.concatenate(yvals)) + 0.01])

        extent = [xlimits[0], np.min(np.concatenate(yvals)), xlimits[-1], np.max(np.concatenate(yvals)) + 0.01]

        self.set_tick_parameters(**kwargs)

        for __, line in enumerate(self.plotMS.get_lines()):
            line.set_linewidth(kwargs["line_width"])
            line.set_linestyle(kwargs["line_style"])

        if title != "":
            self.set_plot_title(title, **kwargs)

        self.setup_zoom([self.plotMS], self.zoomtype, data_lims=extent, plotName=plotType, allowWheel=allowWheel)
        # Setup X-axis getter
        self.setupGetXAxies([self.plotMS])
        self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]

    def plot_1D_waterfall(
        self,
        xvals=None,
        yvals=None,
        zvals=None,
        label="",
        xlabel="",
        colorList=[],
        ylabel="",
        zoom="box",
        axesSize=None,
        plotName="1D",
        xlimits=None,
        plotType="Waterfall",
        labels=[],
        **kwargs,
    ):
        # TODO: Convert axes.plot to LineCollection = will be a lot faster!
        # TODO: Add x-axis checker for mass spectra

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

        self.plotMS = self.figure.add_axes(self._axes)
        if kwargs["labels_font_weight"]:
            kwargs["labels_font_weight"] = "heavy"
        else:
            kwargs["labels_font_weight"] = "normal"

        zorder, zorder_offset = 5, 5
        count = kwargs["labels_frequency"]

        if xlabel not in ["m/z", "Mass (Da)", "Charge"]:
            xlabel, ylabel = ylabel, xlabel

        xlabel = _replace_labels(xlabel)
        ylabel = _replace_labels(ylabel)

        # uniform x-axis
        ydata = []
        if zvals is not None:
            n_colors = len(zvals[1, :])

            if len(labels) == 0:
                labels = [""] * n_colors

            if kwargs["reverse"]:
                zvals = np.fliplr(zvals)
                yvals = yvals[::-1]
                labels = labels[::-1]

            # Setup parameters
            if xlimits is None or xlimits[0] is None or xlimits[1] is None:
                xlimits = [np.min(xvals), np.max(xvals)]

            # Always normalizes data - otherwise it looks pretty bad
            if kwargs["increment"] != 0 and kwargs.get("normalize", True):
                zvals = normalize_2D(zvals)
            else:
                ylabel = "Intensity"
                ydivider, expo = self.testXYmaxValsUpdated(values=zvals)
                if expo > 1:
                    zvals = np.divide(zvals, float(ydivider))
                    offset_text = r"x$\mathregular{10^{%d}}$" % expo
                    ylabel = "".join([ylabel, " [", offset_text, "]"])

            voltage_idx = np.linspace(0, len(zvals[1, :]) - 1, len(zvals[1, :]))
            label_xposition = np.min(xvals) + (np.max(xvals) * kwargs["labels_x_offset"])
            yOffset = kwargs["offset"] * (len(zvals[1, :]) + 1)

            self.text_offset_position = dict(min=np.min(xvals), max=np.max(xvals), offset=kwargs["labels_x_offset"])

            if kwargs["color_scheme"] == "Colormap":
                colorlist = color_palette(kwargs["colormap"], n_colors)
            elif kwargs["color_scheme"] == "Color palette":
                if kwargs["palette"] not in ["Spectral", "RdPu"]:
                    kwargs["palette"] = kwargs["palette"].lower()
                colorlist = color_palette(kwargs["palette"], n_colors)
            elif kwargs["color_scheme"] == "Same color":
                colorlist = [kwargs["shade_color"]] * n_colors
            elif kwargs["color_scheme"] == "Random":
                colorlist = []
                for __ in range(n_colors):
                    colorlist.append(randomColorGenerator())

            # Iterate over the colormap to get the color shading we desire
            for i in voltage_idx[::-1]:
                y = zvals[:, int(i)]

                if kwargs.get("normalize", True):
                    y = normalize_1D(y)

                if kwargs["line_color_as_shade"]:
                    line_color = colorlist[int(i)]
                else:
                    line_color = kwargs["line_color"]
                shade_color = colorlist[int(i)]

                self.plotMS.plot(
                    xvals,
                    (y + yOffset),
                    color=line_color,
                    linewidth=kwargs["line_width"],
                    linestyle=kwargs["line_style"],
                    label=labels[int(i)],
                    zorder=zorder,
                )

                if kwargs["shade_under"] and len(voltage_idx) < kwargs.get("shade_under_n_limit", 50):
                    shade_kws = dict(
                        facecolor=shade_color,
                        alpha=kwargs.get("shade_under_transparency", 0.25),
                        clip_on=kwargs.get("clip_on", True),
                        zorder=zorder - 2,
                    )
                    self.plotMS.fill_between(xvals, np.min(y + yOffset), (y + yOffset), **shade_kws)

                if kwargs.get("add_labels", True) and kwargs["labels_frequency"] != 0:
                    label = ut_visuals.convert_label(yvals[int(i)], label_format=kwargs["labels_format"])
                    if int(i) % kwargs["labels_frequency"] == 0:
                        label_kws = dict(fontsize=kwargs["labels_font_size"], fontweight=kwargs["labels_font_weight"])
                        self.plot_add_text(
                            xpos=label_xposition,
                            yval=yOffset + kwargs["labels_y_offset"],
                            label=label,
                            zorder=zorder + 3,
                            **label_kws,
                        )
                ydata.extend(y + yOffset)
                yOffset = yOffset - kwargs["increment"]
                zorder = zorder + zorder_offset
                count = count + 1

        # non-uniform x-axis
        else:
            # check in case only one item was passed
            # assumes xvals is a list in a list
            if len(xvals) != len(yvals) and len(xvals) == 1:
                xvals = xvals * len(yvals)

            n_colors = len(yvals)
            if len(labels) == 0:
                labels = [""] * n_colors
            yOffset = kwargs["offset"] * (n_colors + 1)

            # Find new xlimits
            xvals_limit, __ = find_limits_list(xvals, yvals)
            xlimits = (np.min(xvals_limit), np.max(xvals_limit))

            label_xposition = xlimits[0] + (xlimits[1] * kwargs["labels_x_offset"])
            self.text_offset_position = dict(min=xlimits[0], max=xlimits[1], offset=kwargs["labels_x_offset"])

            if colorList is not None and len(colorList) == n_colors:
                colorlist = colorList
            elif kwargs["color_scheme"] == "Colormap":
                colorlist = color_palette(kwargs["colormap"], n_colors)
            elif kwargs["color_scheme"] == "Color palette":
                if kwargs["palette"] not in ["Spectral", "RdPu"]:
                    kwargs["palette"] = kwargs["palette"].lower()
                colorlist = color_palette(kwargs["palette"], n_colors)
            elif kwargs["color_scheme"] == "Same color":
                colorlist = [kwargs["line_color"]] * n_colors
            elif kwargs["color_scheme"] == "Random":
                colorlist = []
                for __ in range(n_colors):
                    colorlist.append(randomColorGenerator())

            if kwargs["reverse"]:
                xvals = xvals[::-1]
                yvals = yvals[::-1]
                colorlist = colorlist[::-1]
                labels = labels[::-1]

            for irow in range(len(xvals)):
                # Always normalizes data - otherwise it looks pretty bad

                if kwargs["increment"] != 0 and kwargs.get("normalize", True):
                    yvals[irow] = normalize_1D(yvals[irow])
                else:
                    ylabel = "Intensity"
                    try:
                        ydivider, expo = self.testXYmaxValsUpdated(values=yvals[irow])
                        if expo > 1:
                            yvals[irow] = np.divide(yvals[irow], float(ydivider))
                            offset_text = r"x$\mathregular{10^{%d}}$" % expo
                            ylabel = "".join([ylabel, " [", offset_text, "]"])
                    except AttributeError:
                        kwargs["increment"] = 0.00001
                        yvals[irow] = normalize_1D(yvals[irow])

                voltage_idx = np.linspace(0, n_colors - 1, n_colors)
                if kwargs["line_color_as_shade"]:
                    line_color = colorlist[irow]
                else:
                    line_color = kwargs["line_color"]
                shade_color = colorlist[int(irow)]
                y = yvals[irow]
                self.plotMS.plot(
                    xvals[irow],
                    (y + yOffset),
                    color=line_color,
                    linewidth=kwargs["line_width"],
                    linestyle=kwargs["line_style"],
                    label=labels[irow],
                    zorder=zorder,
                )

                if kwargs["shade_under"] and len(voltage_idx) < kwargs.get("shade_under_n_limit", 50):
                    shade_kws = dict(
                        facecolor=shade_color,
                        alpha=kwargs.get("shade_under_transparency", 0.25),
                        clip_on=kwargs.get("clip_on", True),
                        zorder=zorder - 2,
                    )
                    self.plotMS.fill_between(xvals[irow], np.min(y + yOffset), (y + yOffset), **shade_kws)

                if kwargs.get("add_labels", True) and kwargs["labels_frequency"] != 0:
                    label = _replace_labels(labels[irow])
                    if irow % kwargs["labels_frequency"] == 0:
                        label_kws = dict(fontsize=kwargs["labels_font_size"], fontweight=kwargs["labels_font_weight"])
                        self.plot_add_text(
                            xpos=label_xposition,
                            yval=yOffset + kwargs["labels_y_offset"],
                            label=label,
                            zorder=zorder + 3,
                            **label_kws,
                        )
                ydata.extend(y + yOffset)
                yOffset = yOffset - kwargs["increment"]
                zorder = zorder + zorder_offset

        self.set_plot_xlabel(xlabel, **kwargs)

        self.set_tick_parameters(**kwargs)

        for __, line in enumerate(self.plotMS.get_lines()):
            line.set_linewidth(kwargs["line_width"])
            line.set_linestyle(kwargs["line_style"])

        self.plotMS.spines["left"].set_visible(kwargs["spines_left"])
        self.plotMS.spines["right"].set_visible(kwargs["spines_right"])
        self.plotMS.spines["top"].set_visible(kwargs["spines_top"])
        self.plotMS.spines["bottom"].set_visible(kwargs["spines_bottom"])
        for i in self.plotMS.spines.values():
            i.set_linewidth(kwargs["frame_width"])
            i.set_zorder(zorder)

        # convert to array to remove nan's and figure out limits
        ydata = remove_nan_from_list(ydata)
        ylimits = np.min(ydata) - kwargs["offset"], np.max(ydata) + 0.05
        extent = [xlimits[0], ylimits[0], xlimits[1], ylimits[1]]

        self.setup_zoom([self.plotMS], self.zoomtype, plotName=plotName, data_lims=extent)
        self.plot_limits = [xlimits[0], xlimits[1], ylimits[0], ylimits[1]]
        # Setup X-axis getter
        self.setupGetXAxies([self.plotMS])
        self.plotMS.set_xlim([xlimits[0], xlimits[1]])

        # a couple of set values
        self.n_colors = n_colors

    def plot_1D_waterfall_overlay(
        self,
        xvals=None,
        yvals=None,
        zvals=None,
        label="",
        xlabel="",
        colorList=[],
        ylabel="",
        zoom="box",
        axesSize=None,
        plotName="1D",
        xlimits=None,
        plotType="Waterfall_overlay",
        labels=[],
        **kwargs,
    ):

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

        self.plotMS = self.figure.add_axes(self._axes)
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
                self.plotMS.plot(
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
                    self.plotMS.fill_between(xval, np.min(y), y, **shade_kws)

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

        handles, __ = self.plotMS.get_legend_handles_labels()
        self.set_legend_parameters(handles, **kwargs)

        self.set_plot_xlabel(xlabel, **kwargs)

        self.set_tick_parameters(**kwargs)

        for __, line in enumerate(self.plotMS.get_lines()):
            line.set_linewidth(kwargs["line_width"])
            line.set_linestyle(kwargs["line_style"])

        self.plotMS.spines["left"].set_visible(kwargs["spines_left"])
        self.plotMS.spines["right"].set_visible(kwargs["spines_right"])
        self.plotMS.spines["top"].set_visible(kwargs["spines_top"])
        self.plotMS.spines["bottom"].set_visible(kwargs["spines_bottom"])
        for i in self.plotMS.spines.values():
            i.set_linewidth(kwargs["frame_width"])
            i.set_zorder(zorder)

        ydata = remove_nan_from_list(ydata)
        ylimits = [np.min(ydata) - kwargs["offset"], np.max(ydata) + 0.05]
        extent = [xlimits[0], ylimits[0], xlimits[1], ylimits[1]]
        self.setup_zoom([self.plotMS], self.zoomtype, plotName=plotName, data_lims=extent)
        self.plot_limits = [xlimits[0], xlimits[1], ylimits[0], ylimits[1]]
        # Setup X-axis getter
        self.setupGetXAxies([self.plotMS])
        self.plotMS.set_xlim([xlimits[0], xlimits[1]])

    #         # a couple of set values
    #         self.n_colors = n_colors

    def plot_1D_violin(
        self,
        xvals=None,
        yvals=None,
        zvals=None,
        xlabel="",
        ylabel="",
        colorList=[],
        orientation="vertical",
        axesSize=None,
        plotName="Violin",
        xlimits=None,
        plotType="Violin",
        labels=[],
        **kwargs,
    ):

        # update settings
        self._check_and_update_plot_settings(plot_name=plotType, axes_size=axesSize, **kwargs)

        self.plotMS = self.figure.add_axes(self._axes)
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
                colorlist.append(randomColorGenerator())

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

            if orientation == "horizontal":
                self.plotMS.fill_between(
                    xvals_plot,
                    -yvals_plot + offset,
                    yvals_plot + offset,
                    #                                          facecolor=colorlist[i],
                    edgecolor=line_color,
                    linewidth=kwargs["line_width"],
                    **shade_kws,
                )
            else:
                self.plotMS.fill_betweenx(
                    xvals_plot,
                    -yvals_plot + offset,
                    yvals_plot + offset,
                    #                                           facecolor=colorlist[i],
                    edgecolor=line_color,
                    linewidth=kwargs["line_width"],
                    **shade_kws,
                )

            if kwargs["labels_frequency"] != 0:
                if i % kwargs["labels_frequency"] == 0:
                    tick_position.append(offset)
                    tick_labels.append(ut_visuals.convert_label(yvals[int(i)], label_format=kwargs["labels_format"]))

        xlimits = [np.amin(xvals), np.amax(xvals)]

        if orientation == "horizontal":
            xlimits = self.plotMS.get_xlim()
            ylimits = self.plotMS.get_ylim()
            extent = [xlimits[0], ylimits[0], xlimits[1], ylimits[1]]
            self.plotMS.set_yticks(tick_position)
            self.plotMS.set_yticklabels(tick_labels)
            xlabel, ylabel = ylabel, xlabel
        else:
            xlimits = self.plotMS.get_xlim()
            ylimits = self.plotMS.get_ylim()
            extent = [xlimits[0], ylimits[0], xlimits[1], ylimits[1]]
            self.plotMS.set_xticks(tick_position)
            self.plotMS.set_xticklabels(tick_labels)

        handles, __ = self.plotMS.get_legend_handles_labels()
        self.set_legend_parameters(handles, **kwargs)

        self.set_plot_xlabel(xlabel, **kwargs)
        self.set_plot_ylabel(ylabel, **kwargs)

        self.set_tick_parameters(**kwargs)

        for __, line in enumerate(self.plotMS.get_lines()):
            line.set_linewidth(kwargs["line_width"])
            line.set_linestyle(kwargs["line_style"])

        self.plotMS.spines["left"].set_visible(kwargs["spines_left"])
        self.plotMS.spines["right"].set_visible(kwargs["spines_right"])
        self.plotMS.spines["top"].set_visible(kwargs["spines_top"])
        self.plotMS.spines["bottom"].set_visible(kwargs["spines_bottom"])
        for i in self.plotMS.spines.values():
            i.set_linewidth(kwargs["frame_width"])

        # a couple of set values
        self.n_colors = n_count

        # setup zoom and plot limits
        self.setup_zoom([self.plotMS], self.zoomtype, plotName=plotName, data_lims=extent)
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

    #         self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]

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

    #         self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]

    def plot_n_grid_2D_overlay(
        self,
        n_zvals,
        cmap_list,
        title_list,
        xvals,
        yvals,
        xlabel,
        ylabel,
        plotName="Overlay_Grid",
        axesSize=None,
        **kwargs,
    ):
        # update settings
        self._check_and_update_plot_settings(plot_name=plotName, axes_size=axesSize, **kwargs)

        n_grid = len(n_zvals)
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
        gs.update(hspace=kwargs.get("grid_hspace", 1), wspace=kwargs.get("grid_hspace", 1))

        #         extent = ut_visuals.extents(xvals)+ut_visuals.extents(yvals)
        plt_list, extent_list = [], []
        for i in range(n_grid):
            row = int(i // n_cols)
            col = i % n_cols
            ax = self.figure.add_subplot(gs[row, col], aspect="auto")

            if len(xvals) == n_grid:
                extent = ut_visuals.extents(xvals[i]) + ut_visuals.extents(yvals[i])
                xmin, xmax = np.min(xvals[i]), np.max(xvals[i])
                ymin, ymax = np.min(yvals[i]), np.max(yvals[i])
            else:
                extent = ut_visuals.extents(xvals) + ut_visuals.extents(yvals)
                xmin, xmax = np.min(xvals), np.max(xvals)
                ymin, ymax = np.min(yvals), np.max(yvals)
            extent_list.append([xmin, ymin, xmax, ymax])

            if kwargs.get("override_colormap", False):
                cmap = kwargs["colormap"]
            else:
                cmap = cmap_list[i]

            ax.imshow(
                n_zvals[i],
                extent=extent,
                cmap=cmap,
                interpolation=kwargs["interpolation"],
                aspect="auto",
                origin="lower",
            )

            ax.set_xlim(xmin, xmax - 0.5)
            ax.set_ylim(ymin, ymax - 0.5)
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

            if kwargs.get("grid_show_title", True):
                ax.set_title(
                    label=title_list[i],
                    fontdict={"fontsize": kwargs["title_size"], "fontweight": kwargs["title_weight"]},
                )

            # remove ticks for anything thats not on the outskirts
            if kwargs.get("grid_show_tickLabels", True):
                if col != 0:
                    ax.set_yticks([])
                if row != (n_rows - 1):
                    ax.set_xticks([])
            else:
                ax.set_yticks([])
                ax.set_xticks([])

            # update axis frame
            if kwargs["axis_onoff"]:
                ax.set_axis_on()
            else:
                ax.set_axis_off()
            plt_list.append(ax)

            if kwargs.get("grid_show_label", False):
                kwargs["label_pad"] = 5
                if col == 0:
                    ax.set_ylabel(
                        ylabel,
                        labelpad=kwargs["label_pad"],
                        fontsize=kwargs["label_size"],
                        weight=kwargs["label_weight"],
                    )
                if row == n_rows - 1:
                    ax.set_xlabel(
                        xlabel,
                        labelpad=kwargs["label_pad"],
                        fontsize=kwargs["label_size"],
                        weight=kwargs["label_weight"],
                    )

        try:
            gs.tight_layout(self.figure, pad=kwargs.get("grid_pad", 1.08))
        except ValueError as e:
            print(e)
        self.figure.tight_layout()

        #         extent = [xmin, ymin, xmax, ymax]
        self.setup_zoom(plt_list, self.zoomtype, data_lims=extent_list)

    #         self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]

    def plot_grid_2D_overlay(
        self,
        zvals_1,
        zvals_2,
        zvals_cum,
        xvals,
        yvals,
        xlabel,
        ylabel,
        plotName="Overlay_Grid",
        axesSize=None,
        **kwargs,
    ):

        # update settings
        self._check_and_update_plot_settings(plot_name=plotName, axes_size=axesSize, **kwargs)

        gs = gridspec.GridSpec(nrows=2, ncols=2, height_ratios=[1, 1], width_ratios=[1, 2])
        gs.update(hspace=kwargs["rmsd_hspace"], wspace=kwargs["rmsd_hspace"])

        self.plot2D_upper = self.figure.add_subplot(gs[0, 0], aspect="auto")
        self.plot2D_lower = self.figure.add_subplot(gs[1, 0], aspect="auto")
        self.plot2D_side = self.figure.add_subplot(gs[:, 1], aspect="auto")

        # Calculate extents
        extent = ut_visuals.extents(xvals) + ut_visuals.extents(yvals)
        self.plot2D_upper.imshow(
            zvals_1,
            extent=extent,
            cmap=kwargs.get("colormap_1", "Reds"),
            interpolation=kwargs["interpolation"],
            norm=kwargs["cmap_norm_1"],
            aspect="auto",
            origin="lower",
        )

        self.plot2D_lower.imshow(
            zvals_2,
            extent=extent,
            cmap=kwargs.get("colormap_2", "Blues"),
            interpolation=kwargs["interpolation"],
            norm=kwargs["cmap_norm_2"],
            aspect="auto",
            origin="lower",
        )

        self.plot2D_side.imshow(
            zvals_cum,
            extent=extent,
            cmap=kwargs["colormap"],
            interpolation=kwargs["interpolation"],
            norm=kwargs["cmap_norm_cum"],
            aspect="auto",
            origin="lower",
        )

        xmin, xmax = np.min(xvals), np.max(xvals)
        ymin, ymax = np.min(yvals), np.max(yvals)

        # ticks
        for plot in [self.plot2D_upper, self.plot2D_lower, self.plot2D_side]:
            plot.set_xlim(xmin, xmax - 0.5)
            plot.set_ylim(ymin, ymax - 0.5)

            plot.tick_params(
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
            plot.spines["left"].set_visible(kwargs["spines_left"])
            plot.spines["right"].set_visible(kwargs["spines_right"])
            plot.spines["top"].set_visible(kwargs["spines_top"])
            plot.spines["bottom"].set_visible(kwargs["spines_bottom"])
            [i.set_linewidth(kwargs["frame_width"]) for i in plot.spines.values()]

            # update axis frame
            if kwargs["axis_onoff"]:
                plot.set_axis_on()
            else:
                plot.set_axis_off()

            kwargs["label_pad"] = 5
            plot.set_xlabel(
                xlabel, labelpad=kwargs["label_pad"], fontsize=kwargs["label_size"], weight=kwargs["label_weight"]
            )
            plot.set_ylabel(
                ylabel, labelpad=kwargs["label_pad"], fontsize=kwargs["label_size"], weight=kwargs["label_weight"]
            )

        gs.tight_layout(self.figure)
        self.figure.tight_layout()
        extent = [xmin, ymin, xmax, ymax]
        self.setup_zoom([self.plot2D_upper, self.plot2D_lower, self.plot2D_side], self.zoomtype, data_lims=extent)
        self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]

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
        self.plotMS = self.figure.add_subplot(gs[1], aspect="auto")

        self.cax = self.plotMS.imshow(
            zvals,
            extent=extent,
            cmap=kwargs["colormap"],
            interpolation=kwargs["interpolation"],
            norm=kwargs["colormap_norm"],
            aspect="auto",
            origin="lower",
        )

        xmin, xmax = self.plotMS.get_xlim()
        ymin, ymax = self.plotMS.get_ylim()
        self.plotMS.set_xlim(xmin, xmax - 0.5)
        self.plotMS.set_ylim(ymin, ymax - 0.5)

        extent = [labelsX[0], labelsY[0], labelsX[-1], labelsY[-1]]
        self.setup_zoom([self.plotMS], self.zoomtype, data_lims=extent, plotName=plotName)
        self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]

        self.set_plot_xlabel(xlabelRMSD, **kwargs)
        self.set_plot_ylabel(ylabelRMSD, **kwargs)

        # setup colorbar

        #         if kwargs["colorbar"]:
        #             cbarDivider = make_axes_locatable(self.plotMS)
        #             # pad controls how close colorbar is to the axes
        #             self.cbar = cbarDivider.append_axes(
        #                 kwargs["colorbar_position"],
        #                 size="".join([str(kwargs["colorbar_width"]), "%"]),
        #                 pad=kwargs["colorbar_pad"],
        #             )
        #             tick_min = np.min(zvals)
        #             tick_max = np.max(zvals)
        #             tick_mid = np.median([tick_min, tick_max])
        #             ticks = [tick_min, tick_mid, tick_max]
        #
        #             if plotName in ["RMSD", "RMSF"]:
        #                 tick_labels = ["-100", "%", "100"]
        #             else:
        #                 tick_labels = ["0", "%", "100"]
        #
        #             self.cbar.ticks = ticks
        #             self.cbar.tick_labels = tick_labels
        #
        #             if kwargs["colorbar_position"] in ["left", "right"]:
        #                 self.figure.colorbar(self.cax, cax=self.cbar, ticks=ticks, orientation="vertical")
        #                 self.cbar.yaxis.set_ticks_position(kwargs["colorbar_position"])
        #                 self.cbar.set_yticklabels(tick_labels)
        #             else:
        #                 self.figure.colorbar(self.cax, cax=self.cbar, ticks=ticks, orientation="horizontal")
        #                 self.cbar.xaxis.set_ticks_position(kwargs["colorbar_position"])
        #                 self.cbar.set_xticklabels(tick_labels)
        #
        #             # setup other parameters
        #             self.cbar.tick_params(labelsize=kwargs["colorbar_label_size"])

        # ticks
        self.plotMS.tick_params(
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
        self.plotMS.spines["left"].set_visible(kwargs["spines_left"])
        self.plotMS.spines["right"].set_visible(kwargs["spines_right"])
        self.plotMS.spines["top"].set_visible(kwargs["spines_top"])
        self.plotMS.spines["bottom"].set_visible(kwargs["spines_bottom"])
        [i.set_linewidth(kwargs["frame_width"]) for i in self.plotMS.spines.values()]

        self.plotRMSF.spines["left"].set_visible(kwargs["spines_left_1D"])
        self.plotRMSF.spines["right"].set_visible(kwargs["spines_right_1D"])
        self.plotRMSF.spines["top"].set_visible(kwargs["spines_top_1D"])
        self.plotRMSF.spines["bottom"].set_visible(kwargs["spines_bottom_1D"])
        [i.set_linewidth(kwargs["frame_width"]) for i in self.plotRMSF.spines.values()]

        # update axis frame
        if kwargs["axis_onoff"]:
            self.plotMS.set_axis_on()
        else:
            self.plotMS.set_axis_off()

        if kwargs["axis_onoff_1D"]:
            self.plotRMSF.set_axis_on()
        else:
            self.plotRMSF.set_axis_off()

        # update gridspace
        gs.tight_layout(self.figure)
        self.figure.tight_layout()

    def plot_2D(self, zvals=None, xlabel="", ylabel="", axesSize=None, legend=None, plotName="2D", **kwargs):
        # update settings
        self._check_and_update_plot_settings(plot_name=plotName, axes_size=axesSize, **kwargs)

        matplotlib.rc("xtick", labelsize=kwargs["tick_size"])
        matplotlib.rc("ytick", labelsize=kwargs["tick_size"])

        # Plot
        self.plotMS = self.figure.add_axes(self._axes)

        if legend is not None:
            for i in range(len(legend)):
                self.plotMS.plot(
                    -1, -1, "-", c=legend[i][1], label=legend[i][0], marker="s", markersize=15, linewidth=0
                )

        # Calculate extents
        xvals, yvals = zvals.shape
        xvals = np.arange(xvals)
        yvals = np.arange(yvals)

        # Add imshow
        self.cax = self.plotMS.imshow(
            zvals,
            cmap=kwargs["colormap"],
            interpolation=kwargs["interpolation"],
            norm=kwargs["colormap_norm"],
            origin="lower",
            aspect="auto",
        )

        xmin, xmax = self.plotMS.get_xlim()
        ymin, ymax = self.plotMS.get_ylim()
        self.plotMS.set_xlim(xmin, xmax - 0.5)
        self.plotMS.set_ylim(ymin, ymax - 0.5)
        extent = [xmin, ymin, xmax, ymax]

        cbarDivider = make_axes_locatable(self.plotMS)

        # legend
        self.set_legend_parameters(None, **kwargs)

        # labels
        if xlabel in ["None", None]:
            xlabel = ""
        if ylabel in ["None", None]:
            ylabel = ""

        self.set_plot_xlabel(xlabel, **kwargs)
        self.set_plot_ylabel(ylabel, **kwargs)

        # setup colorbar
        if kwargs["colorbar"]:
            # pad controls how close colorbar is to the axes
            self.cbar = cbarDivider.append_axes(
                kwargs["colorbar_position"],
                size="".join([str(kwargs["colorbar_width"]), "%"]),
                pad=kwargs["colorbar_pad"],
            )

            ticks = [np.min(zvals), (np.max(zvals) - np.min(zvals)) / 2, np.max(zvals)]

            self.cbar.ticks = ticks
            #             self.cbar.tick_labels = tick_labels

            if kwargs["colorbar_position"] in ["left", "right"]:
                self.figure.colorbar(self.cax, cax=self.cbar, ticks=ticks, orientation="vertical")
                self.cbar.yaxis.set_ticks_position(kwargs["colorbar_position"])
                self.cbar.set_yticklabels(["0", "%", "100"])
            else:
                self.figure.colorbar(self.cax, cax=self.cbar, ticks=ticks, orientation="horizontal")
                self.cbar.xaxis.set_ticks_position(kwargs["colorbar_position"])
                self.cbar.set_xticklabels(["0", "%", "100"])

            # setup other parameters
            self.cbar.tick_params(labelsize=kwargs["colorbar_label_size"])

        self.set_tick_parameters(**kwargs)

        self.setup_zoom([self.plotMS], self.zoomtype, data_lims=extent)
        self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]

        # add data
        self.plot_data = {"xvals": xvals, "yvals": yvals, "zvals": zvals, "xlabel": xlabel, "ylabel": ylabel}

    def plot_2D_surface(
        self, zvals, xvals, yvals, xlabel, ylabel, legend=False, axesSize=None, plotName=None, **kwargs
    ):
        # update settings
        self._check_and_update_plot_settings(plot_name=plotName, axes_size=axesSize, **kwargs)

        # set tick size
        matplotlib.rc("xtick", labelsize=kwargs["tick_size"])
        matplotlib.rc("ytick", labelsize=kwargs["tick_size"])

        # Plot
        self.plotMS = self.figure.add_axes(self._axes)
        extent = ut_visuals.extents(xvals) + ut_visuals.extents(yvals)

        # Add imshow
        self.cax = self.plotMS.imshow(
            zvals,
            extent=extent,
            cmap=kwargs["colormap"],
            interpolation=kwargs["interpolation"],
            norm=kwargs["colormap_norm"],
            aspect="auto",
            origin="lower",
        )
        xmin, xmax, ymin, ymax = extent
        self.plotMS.set_xlim(xmin, xmax - 0.5)
        self.plotMS.set_ylim(ymin, ymax - 0.5)

        # legend
        if legend:
            self.set_legend_parameters(None, **kwargs)

        # setup zoom
        extent = [xmin, ymin, xmax, ymax]
        self.setup_zoom([self.plotMS], self.zoomtype, data_lims=extent, plotName=plotName)
        self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]

        # labels
        if xlabel in ["None", None, ""]:
            xlabel = ""
        if ylabel in ["None", None, ""]:
            ylabel = ""

        self.set_plot_xlabel(xlabel, **kwargs)
        self.set_plot_ylabel(ylabel, **kwargs)

        # add colorbar
        if kwargs["colorbar"]:
            self.set_colorbar_parameters(zvals, **kwargs)

        self.set_tick_parameters(**kwargs)

        # add data
        self.plot_data = {"xvals": xvals, "yvals": yvals, "zvals": zvals, "xlabel": xlabel, "ylabel": ylabel}
        self.plot_labels.update({"xlabel": xlabel, "ylabel": ylabel})

        print(axesSize, self.get_optimal_margins(axesSize))

    def plot_2D_contour(
        self, zvals, xvals, yvals, xlabel, ylabel, legend=False, axesSize=None, plotName=None, **kwargs
    ):
        # update settings
        self._check_and_update_plot_settings(plot_name=plotName, axes_size=axesSize, **kwargs)

        # set tick size
        matplotlib.rc("xtick", labelsize=kwargs["tick_size"])
        matplotlib.rc("ytick", labelsize=kwargs["tick_size"])

        # Plot
        self.plotMS = self.figure.add_axes(self._axes)

        extent = ut_visuals.extents(xvals) + ut_visuals.extents(yvals)

        # Add imshow
        self.cax = self.plotMS.contourf(
            zvals, 300, extent=extent, cmap=kwargs["colormap"], norm=kwargs["colormap_norm"], antialiasing=True
        )

        xmin, xmax, ymin, ymax = extent
        self.plotMS.set_xlim(xmin, xmax - 0.5)
        self.plotMS.set_ylim(ymin, ymax - 0.5)

        # legend
        if legend:
            self.set_legend_parameters(None, **kwargs)

        # setup zoom
        extent = [xmin, ymin, xmax, ymax]
        self.setup_zoom([self.plotMS], self.zoomtype, data_lims=extent)
        self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]

        # labels
        if xlabel in ["None", None, ""]:
            xlabel = ""
        if ylabel in ["None", None, ""]:
            ylabel = ""

        self.set_plot_xlabel(xlabel, **kwargs)
        self.set_plot_ylabel(ylabel, **kwargs)

        # add colorbar
        if kwargs["colorbar"]:
            self.set_colorbar_parameters(zvals, **kwargs)

        self.set_tick_parameters(**kwargs)

        # add data
        self.plot_data = {"xvals": xvals, "yvals": yvals, "zvals": zvals, "xlabel": xlabel, "ylabel": ylabel}
        self.plot_labels.update({"xlabel": xlabel, "ylabel": ylabel})

    def plot_2D_contour_unidec(
        self,
        data=None,
        zvals=None,
        xvals=None,
        yvals=None,
        xlabel="m/z (Da)",
        ylabel="Charge",
        legend=False,
        speedy=True,
        zoom="box",
        axesSize=None,
        plotName=None,
        testX=False,
        title="",
        **kwargs,
    ):
        # update settings
        self._check_and_update_plot_settings(plot_name=plotName, axes_size=axesSize, **kwargs)

        # set tick size
        matplotlib.rc("xtick", labelsize=kwargs["tick_size"])
        matplotlib.rc("ytick", labelsize=kwargs["tick_size"])

        # prep data
        if xvals is None or yvals is None or zvals is None:
            zvals = data[:, 2]
            xvals = np.unique(data[:, 0])
            yvals = np.unique(data[:, 1])
        xlen = len(xvals)
        ylen = len(yvals)
        zvals = np.reshape(zvals, (xlen, ylen))

        # normalize grid
        norm = cm.colors.Normalize(vmax=np.amax(zvals), vmin=np.amin(zvals))

        # Plot
        self.plotMS = self.figure.add_axes(self._axes)

        if testX:
            xvals, xlabel, __ = self.kda_test(xvals)

        extent = ut_visuals.extents(xvals) + ut_visuals.extents(yvals)

        if not speedy:
            self.cax = self.plotMS.contourf(
                xvals, yvals, np.transpose(zvals), kwargs.get("contour_levels", 100), cmap=kwargs["colormap"], norm=norm
            )
        else:
            self.cax = self.plotMS.imshow(
                np.transpose(zvals),
                extent=extent,
                cmap=kwargs["colormap"],
                interpolation=kwargs["interpolation"],
                norm=norm,
                aspect="auto",
                origin="lower",
            )

        #             if 'colormap_norm' in kwargs:
        #                 self.cax.set_norm(kwargs['colormap_norm'])

        xmin, xmax = self.plotMS.get_xlim()
        ymin, ymax = self.plotMS.get_ylim()
        self.plotMS.set_xlim(xmin, xmax - 0.5)
        self.plotMS.set_ylim(ymin, ymax - 0.5)

        if kwargs.get("minor_ticks_off", True):
            self.plotMS.yaxis.set_tick_params(which="minor", bottom="off")
            self.plotMS.yaxis.set_major_locator(MaxNLocator(integer=True))

        # labels
        if xlabel in ["None", None, ""]:
            xlabel = ""
        if ylabel in ["None", None, ""]:
            ylabel = ""

        self.set_plot_xlabel(xlabel, **kwargs)
        self.set_plot_ylabel(ylabel, **kwargs)

        # add colorbar
        if kwargs["colorbar"]:
            self.set_colorbar_parameters(zvals, **kwargs)

        #         cbarDivider = make_axes_locatable(self.plotMS)
        #         # setup colorbar
        #         if kwargs["colorbar"]:
        #             # pad controls how close colorbar is to the axes
        #             self.cbar = cbarDivider.append_axes(
        #                 kwargs["colorbar_position"],
        #                 size="".join([str(kwargs["colorbar_width"]), "%"]),
        #                 pad=kwargs["colorbar_pad"],
        #             )
        #
        #             ticks = [np.min(zvals), (np.max(zvals) - np.min(zvals)) / 2, np.max(zvals)]
        #             if ticks[1] in [ticks[0], ticks[2]]:
        #                 ticks[1] = 0
        #
        #             tick_labels = ["0", "%", "100"]
        #
        #             self.cbar.ticks = ticks
        #             self.cbar.tick_labels = tick_labels
        #
        #             if kwargs["colorbar_position"] in ["left", "right"]:
        #                 self.figure.colorbar(self.cax, cax=self.cbar, ticks=ticks, orientation="vertical")
        #                 self.cbar.yaxis.set_ticks_position(kwargs["colorbar_position"])
        #                 self.cbar.set_yticklabels(tick_labels)
        #             else:
        #                 self.figure.colorbar(self.cax, cax=self.cbar, ticks=ticks, orientation="horizontal")
        #                 self.cbar.xaxis.set_ticks_position(kwargs["colorbar_position"])
        #                 self.cbar.set_xticklabels(tick_labels)
        #
        #             # setup other parameters
        #             self.cbar.tick_params(labelsize=kwargs["colorbar_label_size"])

        self.set_tick_parameters(**kwargs)

        if title != "":
            self.set_plot_title(title, **kwargs)

        # setup zoom
        extent = [xmin, ymin, xmax, ymax]
        self.setup_zoom([self.plotMS], self.zoomtype, data_lims=extent, plotName=plotName, allowWheel=False)
        self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]
        self.plot_data = {"xvals": xvals, "yvals": yvals, "zvals": zvals, "xlabel": xlabel, "ylabel": ylabel}

    def plot_2D_rgb(
        self, zvals, xvals, yvals, xlabel, ylabel, zoom="box", axesSize=None, legend_text=None, plotName="RGB", **kwargs
    ):
        # update settings
        self._check_and_update_plot_settings(plot_name=plotName, axes_size=axesSize, **kwargs)

        matplotlib.rc("xtick", labelsize=kwargs["tick_size"])
        matplotlib.rc("ytick", labelsize=kwargs["tick_size"])

        # Plot
        self.plotMS = self.figure.add_axes(self._axes)

        handles = []
        if legend_text is not None:
            for i in range(len(legend_text)):
                handles.append(
                    patches.Patch(
                        color=legend_text[i][0], label=legend_text[i][1], alpha=kwargs["legend_patch_transparency"]
                    )
                )

        extent = ut_visuals.extents(xvals) + ut_visuals.extents(yvals)

        # Add imshow
        self.cax = self.plotMS.imshow(
            zvals, extent=extent, interpolation=kwargs["interpolation"], origin="lower", aspect="auto"
        )

        xmin, xmax = self.plotMS.get_xlim()
        ymin, ymax = self.plotMS.get_ylim()
        self.plotMS.set_xlim(xmin, xmax - 0.5)
        self.plotMS.set_ylim(ymin, ymax - 0.5)
        extent = [xmin, ymin, xmax, ymax]

        # legend
        self.set_legend_parameters(handles, **kwargs)

        self.set_plot_xlabel(xlabel, **kwargs)
        self.set_plot_ylabel(ylabel, **kwargs)

        self.set_tick_parameters(**kwargs)

        self.setup_zoom([self.plotMS], self.zoomtype, data_lims=extent)
        self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]

    def plot_2D_matrix(
        self, zvals=None, xylabels=None, xNames=None, zoom="box", axesSize=None, plotName=None, **kwargs
    ):

        # update settings
        self._check_and_update_plot_settings(plot_name=plotName, axes_size=axesSize, **kwargs)

        matplotlib.rc("xtick", labelsize=kwargs["tick_size"])
        matplotlib.rc("ytick", labelsize=kwargs["tick_size"])

        # Plot
        self.plotMS = self.figure.add_axes(self._axes)

        # Setup labels
        xsize = len(zvals)
        if xylabels:
            self.plotMS.set_xticks(np.arange(1, xsize + 1, 1))
            self.plotMS.set_xticklabels(xylabels, rotation=kwargs["rmsd_matrix_rotX"])
            self.plotMS.set_yticks(np.arange(1, xsize + 1, 1))
            self.plotMS.set_yticklabels(xylabels, rotation=kwargs["rmsd_matrix_rotY"])

        extent = [0.5, xsize + 0.5, 0.5, xsize + 0.5]

        # Add imshow
        self.cax = self.plotMS.imshow(
            zvals,
            cmap=kwargs["colormap"],
            interpolation=kwargs["interpolation"],
            aspect="auto",
            extent=extent,
            origin="lower",
        )

        xmin, xmax = self.plotMS.get_xlim()
        ymin, ymax = self.plotMS.get_ylim()
        self.plotMS.set_xlim(xmin, xmax - 0.5)
        self.plotMS.set_ylim(ymin, ymax - 0.5)
        extent = [xmin, ymin, xmax, ymax]

        # add labels
        self.text = []
        if kwargs["rmsd_matrix_labels"]:
            thresh = zvals.max() / 2.0
            cmap = self.cax.get_cmap()
            color = determineFontColor(convertRGB1to255(cmap(thresh)))
            for i, j in itertools.product(list(range(zvals.shape[0])), list(range(zvals.shape[1]))):
                color = determineFontColor(convertRGB1to255(cmap(zvals[i, j] / 2)))
                label = format(zvals[i, j], ".2f")
                obj_name = kwargs.pop("text_name", None)
                text = self.plotMS.text(
                    j + 1, i + 1, label, horizontalalignment="center", color=color, picker=True, clip_on=True
                )
                text.obj_name = obj_name  # custom tag
                self.text.append(text)

        cbarDivider = make_axes_locatable(self.plotMS)

        try:
            handles, __ = self.plotMS.get_legend_handles_labels()
            if len(handles) > 0:
                self.set_legend_parameters(handles, **kwargs)
        except Exception:
            pass

        # add colorbar
        if kwargs["colorbar"]:
            self.set_colorbar_parameters(zvals, **kwargs)

        #         # setup colorbar
        #         if kwargs["colorbar"]:
        #             # pad controls how close colorbar is to the axes
        #             self.cbar = cbarDivider.append_axes(
        #                 kwargs["colorbar_position"],
        #                 size="".join([str(kwargs["colorbar_width"]), "%"]),
        #                 pad=kwargs["colorbar_pad"],
        #             )
        #
        #             ticks = [np.min(zvals), (np.max(zvals) - np.min(zvals)) / 2, np.max(zvals)]
        #             tick_labels = ["0", "%", "100"]
        #
        #             self.cbar.ticks = ticks
        #             self.cbar.tick_labels = tick_labels
        #
        #             if kwargs["colorbar_position"] in ["left", "right"]:
        #                 self.figure.colorbar(self.cax, cax=self.cbar, ticks=ticks, orientation="vertical")
        #                 self.cbar.yaxis.set_ticks_position(kwargs["colorbar_position"])
        #                 self.cbar.set_yticklabels(tick_labels)
        #             else:
        #                 self.figure.colorbar(self.cax, cax=self.cbar, ticks=ticks, orientation="horizontal")
        #                 self.cbar.xaxis.set_ticks_position(kwargs["colorbar_position"])
        #                 self.cbar.set_xticklabels(tick_labels)
        #
        #             # setup other parameters
        #             self.cbar.tick_params(labelsize=kwargs["colorbar_label_size"])

        self.set_tick_parameters(**kwargs)

        # setup zoom
        self.setup_zoom([self.plotMS], self.zoomtype, data_lims=extent, plotName=plotName)
        self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]

    def plot_2D_overlay(
        self,
        zvalsIon1=None,
        zvalsIon2=None,
        cmapIon1="Reds",
        cmapIon2="Greens",
        alphaIon1=1,
        alphaIon2=1,
        labelsX=None,
        labelsY=None,
        xlabel="",
        ylabel="",
        zoom="box",
        axesSize=None,
        plotName=None,
        **kwargs,
    ):

        # update settings
        self._check_and_update_plot_settings(plot_name=plotName, axes_size=axesSize, **kwargs)

        # set tick size
        matplotlib.rc("xtick", labelsize=kwargs["tick_size"])
        matplotlib.rc("ytick", labelsize=kwargs["tick_size"])

        # Plot
        self.plotMS = self.figure.add_axes(self._axes)

        extent = ut_visuals.extents(labelsX) + ut_visuals.extents(labelsY)

        # Add imshow
        self.cax = self.plotMS.imshow(
            zvalsIon1,
            extent=extent,
            cmap=cmapIon1,
            interpolation=kwargs["interpolation"],
            aspect="auto",
            origin="lower",
            alpha=alphaIon1,
        )
        plotMS2 = self.plotMS.imshow(
            zvalsIon2,
            extent=extent,
            cmap=cmapIon2,
            interpolation=kwargs["interpolation"],
            aspect="auto",
            origin="lower",
            alpha=alphaIon2,
        )

        xmin, xmax = self.plotMS.get_xlim()
        ymin, ymax = self.plotMS.get_ylim()
        self.plotMS.set_xlim(xmin, xmax - 0.5)
        self.plotMS.set_ylim(ymin, ymax - 0.5)

        # legend
        self.set_legend_parameters(None, **kwargs)
        # setup zoom
        extent = [xmin, ymin, xmax, ymax]
        self.setup_zoom([self.plotMS], self.zoomtype, data_lims=extent, plotName=plotName)
        self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]

        # labels
        if xlabel in ["None", None, ""]:
            xlabel = ""
        if ylabel in ["None", None, ""]:
            ylabel = ""

        self.set_plot_xlabel(xlabel, **kwargs)
        self.set_plot_ylabel(ylabel, **kwargs)

        self.set_tick_parameters(**kwargs)

    def plot_3D_bar(
        self,
        xvals=None,
        yvals=None,
        zvals=None,
        xylabels=None,
        cmap="inferno",
        title="",
        xlabel="",
        ylabel="",
        zlabel="",
        label="",
        axesSize=None,
        plotType="Bar",
        **kwargs,
    ):
        # update settings
        self._check_and_update_plot_settings(plot_name=plotType, axes_size=axesSize, **kwargs)

        xvals = list(range(zvals.shape[1]))
        yvals = list(range(zvals.shape[0]))
        xvals, yvals = np.meshgrid(xvals, yvals)

        x, y = xvals.ravel(), yvals.ravel()
        top = zvals.ravel()
        bottom = np.zeros_like(top)
        width = depth = 1

        cmap = cm.get_cmap(kwargs["colormap"])  # Get desired colormap
        max_height = np.max(top)  # get range of colorbars
        min_height = np.min(top)

        # scale each z to [0,1], and get their rgb values
        rgba = [cmap((k - min_height) / max_height) for k in top]

        self.plotMS = self.figure.add_subplot(111, projection="3d", aspect="auto")
        self.plotMS.mouse_init(rotate_btn=1, zoom_btn=2)
        self.plotMS.bar3d(x, y, bottom, width, depth, top, color=rgba, zsort="average", picker=1)

        # update labels
        self.set_plot_xlabel(None, **kwargs)
        self.set_plot_ylabel(None, **kwargs)

        # Setup font size info
        self.plotMS.tick_params(labelsize=kwargs["tick_size"])

        self.plotMS.w_xaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        self.plotMS.w_yaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        self.plotMS.w_zaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))

        # Get rid of spines
        if not kwargs["show_spines"]:
            self.plotMS.w_xaxis.line.set_color((1.0, 1.0, 1.0, 0.0))
            self.plotMS.w_yaxis.line.set_color((1.0, 1.0, 1.0, 0.0))
            self.plotMS.w_zaxis.line.set_color((1.0, 1.0, 1.0, 0.0))

        # Setup labels
        xsize = len(zvals)
        if xylabels:
            self.plotMS.set_xticks(np.arange(1, xsize + 1, 1) - 0.5)
            self.plotMS.set_xticklabels(xylabels, rotation=kwargs["rmsd_matrix_rotX"])
            self.plotMS.set_yticks(np.arange(1, xsize + 1, 1) - 0.5)
            self.plotMS.set_yticklabels(xylabels, rotation=kwargs["rmsd_matrix_rotY"])

        # Get rid of the ticks
        if not kwargs["show_ticks"]:
            self.plotMS.set_xticks([])
            self.plotMS.set_yticks([])
            self.plotMS.set_zticks([])

        # update labels
        self.plotMS.set_xlabel(
            xlabel,
            labelpad=kwargs["label_pad"],
            fontsize=kwargs["label_size"],
            weight=kwargs["label_weight"],
            visible=kwargs["show_labels"],
        )
        self.plotMS.set_ylabel(
            ylabel,
            labelpad=kwargs["label_pad"],
            fontsize=kwargs["label_size"],
            weight=kwargs["label_weight"],
            visible=kwargs["show_labels"],
        )
        self.plotMS.set_zlabel(
            zlabel,
            labelpad=kwargs["label_pad"],
            fontsize=kwargs["label_size"],
            weight=kwargs["label_weight"],
            visible=kwargs["show_labels"],
        )
        self.plotMS.grid(kwargs["grid"])

        self.plotMS.set_xlim([0, len(xvals)])
        self.plotMS.set_ylim([0, len(yvals)])
        self.plotMS.set_zlim([np.min(zvals), np.max(zvals)])

        self.plotMS.set_position(axesSize)

    def plot_3D_surface(
        self,
        xvals=None,
        yvals=None,
        zvals=None,
        colors=None,
        xlabel=None,
        ylabel=None,
        zlabel=None,
        plotName="whole",
        axesSize=None,
        plotType="Surface3D",
        **kwargs,
    ):
        # update settings
        self._check_and_update_plot_settings(plot_name=plotType, axes_size=axesSize, **kwargs)

        #         kwargs = self._check_colormap(**kwargs)
        xvals, yvals = np.meshgrid(xvals, yvals)

        ydivider, expo = self.testXYmaxValsUpdated(values=zvals)
        if expo > 1:
            offset_text = r"x$\mathregular{10^{%d}}$" % expo
            zlabel = "".join([zlabel, " [", offset_text, "]"])
            zvals = np.divide(zvals, float(ydivider))

        matplotlib.rc("xtick", labelsize=kwargs["tick_size"])
        matplotlib.rc("ytick", labelsize=kwargs["tick_size"])

        self.plotMS = self.figure.add_subplot(111, projection="3d", aspect="auto")
        self.plotMS.mouse_init(rotate_btn=1, zoom_btn=2)

        self.cax = self.plotMS.plot_surface(
            xvals, yvals, zvals, cmap=kwargs["colormap"], antialiased=True, shade=kwargs["shade"], picker=1
        )

        # update labels
        self.set_plot_xlabel(None, **kwargs)
        self.set_plot_ylabel(None, **kwargs)

        # Setup font size info
        self.plotMS.tick_params(labelsize=kwargs["tick_size"])

        self.plotMS.w_xaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        self.plotMS.w_yaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        self.plotMS.w_zaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))

        # Get rid of spines
        if not kwargs["show_spines"]:
            self.plotMS.w_xaxis.line.set_color((1.0, 1.0, 1.0, 0.0))
            self.plotMS.w_yaxis.line.set_color((1.0, 1.0, 1.0, 0.0))
            self.plotMS.w_zaxis.line.set_color((1.0, 1.0, 1.0, 0.0))

        # Get rid of the ticks
        if not kwargs["show_ticks"]:
            self.plotMS.set_xticks([])
            self.plotMS.set_yticks([])
            self.plotMS.set_zticks([])

        # update labels
        self.plotMS.set_xlabel(
            xlabel,
            labelpad=kwargs["label_pad"],
            fontsize=kwargs["label_size"],
            weight=kwargs["label_weight"],
            visible=kwargs["show_labels"],
        )
        self.plotMS.set_ylabel(
            ylabel,
            labelpad=kwargs["label_pad"],
            fontsize=kwargs["label_size"],
            weight=kwargs["label_weight"],
            visible=kwargs["show_labels"],
        )
        self.plotMS.set_zlabel(
            zlabel,
            labelpad=kwargs["label_pad"],
            fontsize=kwargs["label_size"],
            weight=kwargs["label_weight"],
            visible=kwargs["show_labels"],
        )

        self.plotMS.grid(kwargs["grid"])

        self.plotMS.set_xlim([np.min(xvals), np.max(xvals)])
        self.plotMS.set_ylim([np.min(yvals), np.max(yvals)])
        self.plotMS.set_zlim([np.min(zvals), np.max(zvals)])

        self.plotMS.set_position(axesSize)

    def plot_3D_wireframe(
        self,
        xvals=None,
        yvals=None,
        zvals=None,
        colors=None,
        xlabel=None,
        ylabel=None,
        zlabel=None,
        plotName="whole",
        axesSize=None,
        plotType="Wireframe3D",
        **kwargs,
    ):
        # update settings
        self._check_and_update_plot_settings(plot_name=plotType, axes_size=axesSize, **kwargs)

        xvals, yvals = np.meshgrid(xvals, yvals)

        ydivider, expo = self.testXYmaxValsUpdated(values=zvals)
        if expo > 1:
            offset_text = r"x$\mathregular{10^{%d}}$" % expo
            zlabel = "".join([zlabel, " [", offset_text, "]"])
            zvals = np.divide(zvals, float(ydivider))

        matplotlib.rc("xtick", labelsize=kwargs["tick_size"])
        matplotlib.rc("ytick", labelsize=kwargs["tick_size"])

        #         kwargs = self._check_colormap(**kwargs)
        self.plotMS = self.figure.add_subplot(111, projection="3d", aspect="auto")
        self.plotMS.mouse_init(rotate_btn=1, zoom_btn=2)
        self.plotMS.plot_wireframe(
            xvals,
            yvals,
            zvals,
            color=kwargs["line_color"],
            linewidth=kwargs["line_width"],
            linestyle=kwargs["line_style"],
            antialiased=False,
        )

        # update labels
        self.set_plot_xlabel(None, **kwargs)
        self.set_plot_ylabel(None, **kwargs)

        # Setup font size info
        self.plotMS.tick_params(labelsize=kwargs["tick_size"])

        self.plotMS.w_xaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        self.plotMS.w_yaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        self.plotMS.w_zaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))

        # Get rid of spines
        if not kwargs["show_spines"]:
            self.plotMS.w_xaxis.line.set_color((1.0, 1.0, 1.0, 0.0))
            self.plotMS.w_yaxis.line.set_color((1.0, 1.0, 1.0, 0.0))
            self.plotMS.w_zaxis.line.set_color((1.0, 1.0, 1.0, 0.0))
        else:
            self.plotMS.w_xaxis.line.set_color((0.0, 0.0, 0.0, 0.0))
            self.plotMS.w_yaxis.line.set_color((0.0, 0.0, 0.0, 0.0))
            self.plotMS.w_zaxis.line.set_color((0.0, 0.0, 0.0, 0.0))

        # Get rid of the ticks
        if not kwargs["show_ticks"]:
            self.plotMS.set_xticks([])
            self.plotMS.set_yticks([])
            self.plotMS.set_zticks([])

        # update labels
        self.plotMS.set_xlabel(
            xlabel,
            labelpad=kwargs["label_pad"],
            fontsize=kwargs["label_size"],
            weight=kwargs["label_weight"],
            visible=kwargs["show_labels"],
        )
        self.plotMS.set_ylabel(
            ylabel,
            labelpad=kwargs["label_pad"],
            fontsize=kwargs["label_size"],
            weight=kwargs["label_weight"],
            visible=kwargs["show_labels"],
        )
        self.plotMS.set_zlabel(
            zlabel,
            labelpad=kwargs["label_pad"],
            fontsize=kwargs["label_size"],
            weight=kwargs["label_weight"],
            visible=kwargs["show_labels"],
        )

        self.plotMS.grid(kwargs["grid"])

        self.plotMS.set_xlim([np.min(xvals), np.max(xvals)])
        self.plotMS.set_ylim([np.min(yvals), np.max(yvals)])
        self.plotMS.set_zlim([np.min(zvals), np.max(zvals)])

        self.plotMS.set_position(axesSize)

    def plot_3D_scatter(
        self,
        xvals=None,
        yvals=None,
        zvals=None,
        colors=None,
        xlabel=None,
        ylabel=None,
        zlabel=None,
        plotName="whole",
        axesSize=None,
        plotType="Scatter3D",
        **kwargs,
    ):
        # update settings
        self._check_and_update_plot_settings(plot_name=plotType, axes_size=axesSize, **kwargs)

        matplotlib.rc("xtick", labelsize=kwargs["tick_size"])
        matplotlib.rc("ytick", labelsize=kwargs["tick_size"])

        self.plotMS = self.figure.add_subplot(111, projection="3d", aspect="auto")
        if colors is not None:
            self.plotMS.scatter(
                xvals,
                yvals,
                zvals,
                c=colors,
                edgecolor=colors,
                marker=kwargs["scatter_shape"],
                alpha=kwargs["scatter_alpha"],
                s=kwargs["scatter_size"],
                depthshade=kwargs["shade"],
            )
        else:
            self.plotMS.scatter(
                xvals,
                yvals,
                zvals,
                c=kwargs["scatter_color"],
                edgecolor=kwargs["scatter_edge_color"],
                marker=kwargs["scatter_shape"],
                alpha=kwargs["scatter_alpha"],
                s=kwargs["scatter_size"],
                depthshade=kwargs["shade"],
            )

        # update labels
        self.set_plot_xlabel(None, **kwargs)
        self.set_plot_ylabel(None, **kwargs)

        # Setup font size info
        self.plotMS.tick_params(labelsize=kwargs["tick_size"])

        self.plotMS.w_xaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        self.plotMS.w_yaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))
        self.plotMS.w_zaxis.set_pane_color((1.0, 1.0, 1.0, 1.0))

        # Get rid of spines
        if not kwargs["show_spines"]:
            self.plotMS.w_xaxis.line.set_color((1.0, 1.0, 1.0, 0.0))
            self.plotMS.w_yaxis.line.set_color((1.0, 1.0, 1.0, 0.0))
            self.plotMS.w_zaxis.line.set_color((1.0, 1.0, 1.0, 0.0))

        # Get rid of the ticks
        if not kwargs["show_ticks"]:
            self.plotMS.set_xticks([])
            self.plotMS.set_yticks([])
            self.plotMS.set_zticks([])

        # update labels
        self.plotMS.set_xlabel(
            xlabel,
            labelpad=kwargs["label_pad"],
            fontsize=kwargs["label_size"],
            weight=kwargs["label_weight"],
            visible=kwargs["show_labels"],
        )
        self.plotMS.set_ylabel(
            ylabel,
            labelpad=kwargs["label_pad"],
            fontsize=kwargs["label_size"],
            weight=kwargs["label_weight"],
            visible=kwargs["show_labels"],
        )
        self.plotMS.set_zlabel(
            zlabel,
            labelpad=kwargs["label_pad"],
            fontsize=kwargs["label_size"],
            weight=kwargs["label_weight"],
            visible=kwargs["show_labels"],
        )

        self.plotMS.grid(kwargs["grid"])

        self.plotMS.set_xlim([np.min(xvals), np.max(xvals)])
        self.plotMS.set_ylim([np.min(yvals), np.max(yvals)])
        self.plotMS.set_zlim([np.min(zvals), np.max(zvals)])


# class MayaviPanel(HasTraits):
#     scene = Instance(MlabSceneModel, ())
#
#     view = View(Item('scene', editor=SceneEditor(),
#                      resizable=True, show_label=False),
#                 resizable=True)
#
#     def __init__(self):
#         HasTraits.__init__(self)
#         self.scene.background=(1,1,1) #set white background!
#         self.scene.mlab.test_points3d()
#
#     def display(self,data,t,color=(0.4,1,0.2)):
#
#         self.scene.mlab.clf()
#         self.plot=self.scene.mlab.contour3d(data, color=color,contours=[t])
#
#
#     def update(self,data,t):
#         self.display(data, t)
#         #print "updating with %s"%t
#         #self.plot.mlab_source.set(scalars=data,contours=[t])
#
#     def surface(self, xvals, yvals, zvals, cmap):
#         self.scene.mlab.clf()
#         self.plot = self.scene.mlab.surf(zvals, warp_scale="auto")

# from traits.api import HasTraits, Instance
# from traitsui.api import View, Item
# from mayavi.core.ui.api import SceneEditor, MlabSceneModel
#
# from traits.etsconfig.api import ETSConfig
# ETSConfig.toolkit = 'wx'
#
# class MayaviPanel(HasTraits):
#     scene = Instance(MlabSceneModel, ())
#
#     view = View(Item('scene', editor=SceneEditor(),
#                      resizable=True, show_label=False),
#                 resizable=True)
#
#     def __init__(self):
#         HasTraits.__init__(self)
#         self.scene.background=(1,1,1) #set white background!
#         self.scene.mlab.test_points3d()
#
#     def display(self,data,t,color=(0.4,1,0.2)):
#
#         self.scene.mlab.clf()
#         self.plot=self.scene.mlab.contour3d(data, color=color,contours=[t])
#
#
#     def update(self,data,t):
#         self.display(data, t)
#
#     def surface(self, xvals, yvals, zvals, cmap):
#         self.scene.mlab.clf()
#         self.plot = self.scene.mlab.surf(zvals, warp_scale="auto")
