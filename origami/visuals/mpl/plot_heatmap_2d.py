# Standard library imports
import logging
import itertools
from copy import deepcopy

# Third-party imports
import numpy as np
import matplotlib
from matplotlib import cm
from matplotlib import patches
from matplotlib import gridspec
from matplotlib.colors import LogNorm
from matplotlib.colors import PowerNorm
from matplotlib.ticker import MaxNLocator
from mpl_toolkits.axes_grid1 import make_axes_locatable
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

# Local imports
import origami.utils.visuals as ut_visuals
from origami.utils.color import get_font_color
from origami.utils.color import convert_rgb_1_to_255
from origami.config.config import CONFIG
from origami.utils.visuals import prettify_tick_format
from origami.visuals.mpl.base import PlotBase
from origami.visuals.mpl.normalize import MidpointNormalize

logger = logging.getLogger(__name__)


class PlotHeatmap2D(PlotBase):
    def __init__(self, *args, **kwargs):
        PlotBase.__init__(self, *args, **kwargs)

    def plot_2d(self, x, y, array, title="", x_label="", y_label="", axesSize=None, plotName=None, **kwargs):
        self._set_axes()

        xlimits, ylimits, extent = self._compute_xy_limits(x, y, None)

        # add 2d plot
        self.cax = self.plot_base.imshow(
            array,
            cmap=kwargs["colormap"],
            interpolation=kwargs["interpolation"],
            #             norm=kwargs["colormap_norm"],
            aspect="auto",
            origin="lower",
            extent=[*xlimits, *ylimits],
        )
        #         print(extent)
        # set plot limits
        self.plot_base.set_xlim(xlimits)
        self.plot_base.set_ylim(ylimits)
        self.set_plot_xlabel(x_label, **kwargs)
        self.set_plot_ylabel(y_label, **kwargs)
        self.set_plot_title(title, **kwargs)
        self.set_tick_parameters(**kwargs)

        self.setup_new_zoom(
            [self.plot_base],
            data_limits=extent,
            allow_extraction=kwargs.get("allow_extraction", False),
            callbacks=kwargs.get("callbacks", dict()),
        )
        self.store_plot_limits(extent)

        # add colorbar
        self.set_colorbar_parameters(array, **kwargs)

        # update normalization
        self.plot_2D_update_normalization(**kwargs)

    def get_heatmap_normalization(self, zvals, **kwargs):

        # normalize
        zvals_max = np.max(zvals)
        cmap_min = (zvals_max * kwargs["colormap_min"]) / 100.0
        cmap_mid = (zvals_max * kwargs["colormap_mid"]) / 100.0
        cmap_max = (zvals_max * kwargs["colormap_max"]) / 100.0

        # compute normalization
        if kwargs["colormap_norm_method"] == "Midpoint":
            cmap_norm = MidpointNormalize(midpoint=cmap_mid, v_min=cmap_min, v_max=cmap_max)
        elif kwargs["colormap_norm_method"] == "Logarithmic":
            cmap_norm = LogNorm(vmin=cmap_min, vmax=cmap_max)
        elif kwargs["colormap_norm_method"] == "Power":
            cmap_norm = PowerNorm(gamma=kwargs["colormap_norm_power_gamma"], vmin=cmap_min, vmax=cmap_max)

        return cmap_norm

    def set_colorbar_parameters(self, zvals, **kwargs):
        """Add colorbar to the plot

        Parameters
        ----------
        zvals : np.array
            intensity array
        **kwargs : dict
            dictionary with all plot parameters defined by the user
        """

        tick_labels = None
        if kwargs["colorbar_label_fmt"] == "0 % 100":
            tick_labels = ["0", "%", "100"]

        # always override when dealing with RMSD/RMSF PlotBase
        if self.plot_name in ["RMSD", "RMSF"]:
            tick_labels = ["-100", "%", "100"]

        # retrieve ticks
        ticks = [np.min(zvals), (np.max(zvals) - np.abs(np.min(zvals))) / 2, np.max(zvals)]

        # override middle tick if value is repeated in the edges
        if ticks[1] in [ticks[0], ticks[2]]:
            ticks[1] = 0

        self.ticks = ticks
        self.tick_labels = tick_labels

        # add colorbar
        self.plot_2D_colorbar_update(**kwargs)

    def plot_2D_colorbar_update(self, **kwargs):
        """Set colorbar parameters"""

        if self.lock_plot_from_updating:
            self._locked()

        # add colorbar
        if kwargs["colorbar"]:
            if hasattr(self, "ticks"):
                ticks = self.ticks
            elif hasattr(self.cbar, "ticks"):
                ticks = self.cbar.ticks
            else:
                raise ValueError("Could not find ticks")

            if hasattr(self, "tick_labels"):
                tick_labels = self.tick_labels
            elif hasattr(self.cbar, "tick_labels"):
                tick_labels = self.cbar.tick_labels
            else:
                raise ValueError("Could not find tick labels")

            if self.plot_name == "RMSF":
                if kwargs["colorbar_position"] not in CONFIG.colorbar_position_choices[4::]:
                    kwargs["colorbar_position"] = "inside (top-left)"
                    logger.warning(
                        f"RMSF plot can only have in-plot colorbar."
                        f" Set value to the default: {kwargs['colorbar_position']}"
                        f" Please use one of the `{CONFIG.colorbar_position_choices[4::]}`"
                    )

            # remove colorbar
            try:
                self.cbar.remove()
            except (AttributeError, ValueError, KeyError):
                logger.debug("Failed to delete colorbar - probably didn't exist")

            # add colorbar to axes
            if kwargs["colorbar_position"].startswith("inside"):
                loc_dict = {
                    "inside (top-left)": [2, [0.01, 0, 1, 1]],
                    "inside (top-right)": [1, [-0.02, 0, 1, 1]],
                    "inside (bottom-left)": [3, [0.005, 0.02, 1, 1]],
                    "inside (bottom-right)": [4, [-0.02, 0.02, 1, 1]],
                }
                loc, bbox = loc_dict[kwargs["colorbar_position"]]
                # add extra padding when the label size increases
                bbox[1] = bbox[1] * (kwargs["colorbar_label_size"] / 10)
                self.cbar = inset_axes(
                    self.plot_base,
                    width="50%",
                    height=f"{kwargs['colorbar_width']}%",
                    loc=loc,
                    bbox_to_anchor=bbox,
                    bbox_transform=self.plot_base.transAxes,
                )
            else:
                colorbar_axes = make_axes_locatable(self.plot_base)
                self.cbar = colorbar_axes.append_axes(
                    kwargs["colorbar_position"], size=f"{kwargs['colorbar_width']}%", pad=kwargs["colorbar_pad"]
                )

            # modify / fix labels
            if kwargs["colorbar_label_fmt"] == "0 % 100":
                tick_labels = ["0", "%", "100"]
                if self.plot_name in ["RMSD", "RMSF"]:
                    tick_labels = ["-100", "%", "100"]
            else:
                tick_labels = ticks
                if kwargs["colorbar_label_fmt"] == "true-values (pretty)":
                    tick_labels = prettify_tick_format(ticks)

            # actually add colorbar
            if kwargs["colorbar_position"] in ["left", "right"]:
                cbar = self.figure.colorbar(self.cax, cax=self.cbar, ticks=ticks, orientation="vertical")
                self.cbar.yaxis.set_ticks_position(kwargs["colorbar_position"])
                self.cbar.set_yticklabels(tick_labels)
            elif kwargs["colorbar_position"] in ["top", "bottom"]:
                cbar = self.figure.colorbar(self.cax, cax=self.cbar, ticks=ticks, orientation="horizontal")
                self.cbar.xaxis.set_ticks_position(kwargs["colorbar_position"])
                self.cbar.set_xticklabels(tick_labels)
            else:
                cbar = self.figure.colorbar(self.cax, cax=self.cbar, ticks=ticks, orientation="horizontal")
                self.cbar.xaxis.set_ticks_position("bottom")
                self.cbar.set_xticklabels(tick_labels)

            # set parameters
            cbar.outline.set_edgecolor(kwargs["colorbar_outline_color"])
            cbar.outline.set_linewidth(kwargs["colorbar_outline_width"])
            self.cbar.ticks = ticks
            self.cbar.tick_labels = tick_labels
            self.cbar.tick_params(
                labelsize=kwargs["colorbar_label_size"],
                labelcolor=kwargs["colorbar_label_color"],
                color=kwargs["colorbar_outline_color"],
            )
        # remove colorbar
        else:
            if hasattr(self, "cbar"):
                if hasattr(self.cbar, "ticks"):
                    self.ticks = self.cbar.ticks
                if hasattr(self.cbar, "tick_labels"):
                    self.tick_labels = self.cbar.tick_labels
                try:
                    self.cbar.remove()
                except KeyError:
                    pass

    def on_rotate_heatmap_data(self, yvals, zvals):

        # rotate zvals
        zvals = np.rot90(zvals)
        yvals = yvals[::-1]

        return yvals, zvals

    def on_rotate_90(self):
        # only works for 2D PlotBase!

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

    def plot_2D_get_data(self):

        #         xvals, yvals, zvals = [], [], []
        #         zvals = self.cax.get_array()
        #         xlabel = self.plotMS.get_xlabel()
        #         ylabel = self.plotMS.get_ylabel()

        return self.plot_data

    def plot_2D_update_label(self, **kwargs):
        kwargs = ut_visuals.check_plot_settings(**kwargs)

        if kwargs["rmsd_label_coordinates"] != [None, None]:
            self.text.set_position(kwargs["rmsd_label_coordinates"])
            self.text.set_visible(True)
        else:
            self.text.set_visible(False)

        self.text.set_fontweight(kwargs["rmsd_label_font_weight"])
        self.text.set_fontsize(kwargs["rmsd_label_font_size"])
        self.text.set_color(kwargs["rmsd_label_color"])

    def plot_2D_update(self, **kwargs):
        if self.lock_plot_from_updating:
            self._locked()

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
        self.plot_2D_colorbar_update(**kwargs)

        self.plot_parameters = kwargs

    def plot_2D_matrix_update_label(self, **kwargs):
        kwargs = ut_visuals.check_plot_settings(**kwargs)

        self.plot_base.set_xticklabels(self.plot_base.get_xticklabels(), rotation=kwargs["rmsd_matrix_rotX"])
        self.plot_base.set_yticklabels(self.plot_base.get_xticklabels(), rotation=kwargs["rmsd_matrix_rotY"])

        if not isinstance(self.text, list):
            return

        for text in self.text:
            text.set_visible(kwargs["rmsd_matrix_labels"])
            if not kwargs["rmsd_matrix_color_choice"] == "auto":
                text.set_color(kwargs["rmsd_matrix_color"])
            text.set_fontsize(kwargs["rmsd_matrix_label_size"])
            text.set_fontweight(kwargs["rmsd_matrix_label_weight"])

    def plot_2D_update_normalization(self, **kwargs):
        if self.lock_plot_from_updating:
            self._locked()

        if hasattr(self, "plot_data"):
            if "zvals" in self.plot_data:
                cmap_norm = self.get_heatmap_normalization(self.plot_data["zvals"], **kwargs)

                self.plot_parameters["colormap_norm"] = cmap_norm

                if "colormap_norm" in self.plot_parameters:
                    self.cax.set_norm(self.plot_parameters["colormap_norm"])
                    self.plot_2D_colorbar_update(**kwargs)

    def plot_2D_update_data(self, xvals, yvals, xlabel, ylabel, zvals, **kwargs):

        # clear plot in some circumstances
        if self._plot_tag in ["rmsd_matrix"]:
            self.clear()

        # rotate data
        if self.rotate != 0 and not kwargs.pop("already_rotated", False):
            yvals, zvals = self.on_rotate_heatmap_data(yvals, zvals)

        # update settings
        self._check_and_update_plot_settings(**kwargs)

        # update limits and extents
        extent = ut_visuals.extents(xvals) + ut_visuals.extents(yvals)
        self.cax.set_data(zvals)
        self.cax.set_norm(kwargs.get("colormap_norm", None))
        self.cax.set_extent(extent)
        self.cax.set_cmap(kwargs["colormap"])
        self.cax.set_interpolation(kwargs["interpolation"])

        xmin, xmax, ymin, ymax = extent
        self.plot_base.set_xlim(xmin, xmax)
        self.plot_base.set_ylim(ymin, ymax)

        extent = [xmin, ymin, xmax, ymax]
        if kwargs.get("update_extents", True):
            self.update_extents(extent)
            self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]

        self.set_plot_xlabel(xlabel, **kwargs)
        self.set_plot_ylabel(ylabel, **kwargs)

        try:
            leg = self.plot_base.axes.get_legend()
            leg.remove()
        except Exception:
            pass

        # add data
        self.plot_data = {"xvals": xvals, "yvals": yvals, "zvals": zvals, "xlabel": xlabel, "ylabel": ylabel}
        self.plot_labels.update({"xlabel": xlabel, "ylabel": ylabel})

        # add colorbar
        self.set_colorbar_parameters(zvals, **kwargs)

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

    def plot_2D_surface(
        self, zvals, xvals, yvals, xlabel, ylabel, legend=False, axesSize=None, plotName=None, **kwargs
    ):
        # update settings
        self._check_and_update_plot_settings(plot_name=plotName, axes_size=axesSize, **kwargs)

        # set tick size
        matplotlib.rc("xtick", labelsize=kwargs["tick_size"])
        matplotlib.rc("ytick", labelsize=kwargs["tick_size"])

        # Plot
        self.plot_base = self.figure.add_axes(self._axes)
        extent = ut_visuals.extents(xvals) + ut_visuals.extents(yvals)

        # Add imshow
        self.cax = self.plot_base.imshow(
            zvals,
            extent=extent,
            cmap=kwargs["colormap"],
            interpolation=kwargs["interpolation"],
            norm=kwargs["colormap_norm"],
            aspect="auto",
            origin="lower",
        )
        xmin, xmax, ymin, ymax = extent
        self.plot_base.set_xlim(xmin, xmax - 0.5)
        self.plot_base.set_ylim(ymin, ymax - 0.5)

        # legend
        if legend:
            self.set_legend_parameters(None, **kwargs)

        # setup zoom
        extent = [xmin, ymin, xmax, ymax]
        self.setup_zoom([self.plot_base], self.zoomtype, data_lims=extent, plotName=plotName)
        self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]

        # labels
        if xlabel in ["None", None, ""]:
            xlabel = ""
        if ylabel in ["None", None, ""]:
            ylabel = ""

        self.set_plot_xlabel(xlabel, **kwargs)
        self.set_plot_ylabel(ylabel, **kwargs)

        # add colorbar
        self.set_colorbar_parameters(zvals, **kwargs)

        self.set_tick_parameters(**kwargs)

        # add data
        self.plot_data = {"xvals": xvals, "yvals": yvals, "zvals": zvals, "xlabel": xlabel, "ylabel": ylabel}
        self.plot_labels.update({"xlabel": xlabel, "ylabel": ylabel})

    def plot_2D_contour(
        self, zvals, xvals, yvals, xlabel, ylabel, legend=False, axesSize=None, plotName=None, **kwargs
    ):
        # update settings
        self._check_and_update_plot_settings(plot_name=plotName, axes_size=axesSize, **kwargs)

        # set tick size
        matplotlib.rc("xtick", labelsize=kwargs["tick_size"])
        matplotlib.rc("ytick", labelsize=kwargs["tick_size"])

        # Plot
        self.plot_base = self.figure.add_axes(self._axes)

        extent = ut_visuals.extents(xvals) + ut_visuals.extents(yvals)

        # Add imshow
        self.cax = self.plot_base.contourf(
            zvals, 300, extent=extent, cmap=kwargs["colormap"], norm=kwargs["colormap_norm"], antialiasing=True
        )

        xmin, xmax, ymin, ymax = extent
        self.plot_base.set_xlim(xmin, xmax - 0.5)
        self.plot_base.set_ylim(ymin, ymax - 0.5)

        # legend
        if legend:
            self.set_legend_parameters(None, **kwargs)

        # setup zoom
        extent = [xmin, ymin, xmax, ymax]
        self.setup_zoom([self.plot_base], self.zoomtype, data_lims=extent)
        self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]

        # labels
        if xlabel in ["None", None, ""]:
            xlabel = ""
        if ylabel in ["None", None, ""]:
            ylabel = ""

        self.set_plot_xlabel(xlabel, **kwargs)
        self.set_plot_ylabel(ylabel, **kwargs)

        # add colorbar
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
        speedy=True,
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
        self.plot_base = self.figure.add_axes(self._axes)

        if testX:
            xvals, xlabel, __ = self._convert_xaxis(xvals)

        extent = ut_visuals.extents(xvals) + ut_visuals.extents(yvals)

        if not speedy:
            self.cax = self.plot_base.contourf(
                xvals, yvals, np.transpose(zvals), kwargs.get("contour_levels", 100), cmap=kwargs["colormap"], norm=norm
            )
        else:
            self.cax = self.plot_base.imshow(
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

        xmin, xmax = self.plot_base.get_xlim()
        ymin, ymax = self.plot_base.get_ylim()
        self.plot_base.set_xlim(xmin, xmax - 0.5)
        self.plot_base.set_ylim(ymin, ymax - 0.5)

        if kwargs.get("minor_ticks_off", True):
            self.plot_base.yaxis.set_tick_params(which="minor", bottom="off")
            self.plot_base.yaxis.set_major_locator(MaxNLocator(integer=True))

        # labels
        if xlabel in ["None", None, ""]:
            xlabel = ""
        if ylabel in ["None", None, ""]:
            ylabel = ""

        self.set_plot_xlabel(xlabel, **kwargs)
        self.set_plot_ylabel(ylabel, **kwargs)

        # add colorbar
        self.set_colorbar_parameters(zvals, **kwargs)
        self.set_tick_parameters(**kwargs)

        if title != "":
            self.set_plot_title(title, **kwargs)

        # setup zoom
        extent = [xmin, ymin, xmax, ymax]
        self.setup_zoom([self.plot_base], self.zoomtype, data_lims=extent, plotName=plotName, allowWheel=False)
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
        self.plot_base = self.figure.add_axes(self._axes)

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
        self.cax = self.plot_base.imshow(
            zvals, extent=extent, interpolation=kwargs["interpolation"], origin="lower", aspect="auto"
        )

        xmin, xmax = self.plot_base.get_xlim()
        ymin, ymax = self.plot_base.get_ylim()
        self.plot_base.set_xlim(xmin, xmax - 0.5)
        self.plot_base.set_ylim(ymin, ymax - 0.5)
        extent = [xmin, ymin, xmax, ymax]

        # legend
        self.set_legend_parameters(handles, **kwargs)

        self.set_plot_xlabel(xlabel, **kwargs)
        self.set_plot_ylabel(ylabel, **kwargs)

        self.set_tick_parameters(**kwargs)

        self.setup_zoom([self.plot_base], self.zoomtype, data_lims=extent)
        self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]

    def plot_2D_matrix(self, zvals=None, xylabels=None, axesSize=None, plotName=None, **kwargs):
        self._plot_tag = "rmsd_matrix"
        # update settings
        self._check_and_update_plot_settings(plot_name=plotName, axes_size=axesSize, **kwargs)

        matplotlib.rc("xtick", labelsize=kwargs["tick_size"])
        matplotlib.rc("ytick", labelsize=kwargs["tick_size"])

        # Plot
        self.plot_base = self.figure.add_axes(self._axes)

        # Setup labels
        xsize = len(zvals)
        if xylabels:
            self.plot_base.set_xticks(np.arange(1, xsize + 1, 1))
            self.plot_base.set_xticklabels(xylabels, rotation=kwargs["rmsd_matrix_rotX"])
            self.plot_base.set_yticks(np.arange(1, xsize + 1, 1))
            self.plot_base.set_yticklabels(xylabels, rotation=kwargs["rmsd_matrix_rotY"])

        extent = [0.5, xsize + 0.5, 0.5, xsize + 0.5]

        # Add imshow
        self.cax = self.plot_base.imshow(
            zvals,
            cmap=kwargs["colormap"],
            interpolation=kwargs["interpolation"],
            aspect="auto",
            extent=extent,
            origin="lower",
        )

        xmin, xmax = self.plot_base.get_xlim()
        ymin, ymax = self.plot_base.get_ylim()
        self.plot_base.set_xlim(xmin, xmax - 0.5)
        self.plot_base.set_ylim(ymin, ymax - 0.5)
        extent = [xmin, ymin, xmax, ymax]

        # add labels
        self.text = []
        if kwargs["rmsd_matrix_labels"]:
            cmap = self.cax.get_cmap()
            color = kwargs["rmsd_matrix_color"]
            for i, j in itertools.product(list(range(zvals.shape[0])), list(range(zvals.shape[1]))):
                if kwargs["rmsd_matrix_color_choice"] == "auto":
                    color = get_font_color(convert_rgb_1_to_255(cmap(zvals[i, j] / 2)))

                label = format(zvals[i, j], ".2f")
                obj_name = kwargs.pop("text_name", None)
                text = self.plot_base.text(
                    j + 1, i + 1, label, horizontalalignment="center", color=color, picker=True, clip_on=True
                )
                text.obj_name = obj_name  # custom tag
                text.y_divider = self.y_divider
                self.text.append(text)

        # add colorbar
        self.set_colorbar_parameters(zvals, **kwargs)

        self.set_tick_parameters(**kwargs)

        # setup zoom
        self.setup_zoom([self.plot_base], self.zoomtype, data_lims=extent, plotName=plotName)
        self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]

    def plot_2D_image_update_data(self, xvals, yvals, zvals, xlabel="", ylabel="", **kwargs):
        # update settings
        self._check_and_update_plot_settings(**kwargs)

        # update limits and extents
        self.cax.set_data(zvals)
        self.cax.set_norm(kwargs.get("colormap_norm", None))
        self.cax.set_cmap(kwargs["colormap"])
        self.cax.set_interpolation(kwargs["interpolation"])

        xlimit = self.plot_base.get_xlim()
        xmin, xmax = xlimit
        ylimit = self.plot_base.get_ylim()
        ymin, ymax = ylimit

        # setup zoom
        extent = [xmin, ymin, xmax, ymax]

        if kwargs.get("update_extents", True):
            self.update_extents(extent)
            self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]

        # add data
        self.plot_data = {"xvals": xvals, "yvals": yvals, "zvals": zvals, "xlabel": xlabel, "ylabel": ylabel}
        self.plot_labels.update({"xlabel": xlabel, "ylabel": ylabel})

        # add colorbar
        self.plot_2D_update_normalization(**kwargs)
        self.set_colorbar_parameters(zvals, **kwargs)

    def plot_2D_image(self, zvals, xvals, yvals, xlabel="", ylabel="", axesSize=None, plotName=None, **kwargs):
        # update settings
        self._check_and_update_plot_settings(plot_name=plotName, axes_size=axesSize, **kwargs)

        # set tick size
        matplotlib.rc("xtick", labelsize=kwargs["tick_size"])
        matplotlib.rc("ytick", labelsize=kwargs["tick_size"])

        # Plot
        self.plot_base = self.figure.add_axes(self._axes)

        # Add imshow
        self.cax = self.plot_base.imshow(
            zvals,
            #             extent=extent,
            cmap=kwargs["colormap"],
            interpolation=kwargs["interpolation"],
            norm=kwargs["colormap_norm"],
            aspect="equal",
            origin="lower",
        )

        xlimit = self.plot_base.get_xlim()
        xmin, xmax = xlimit
        ylimit = self.plot_base.get_ylim()
        ymin, ymax = ylimit

        # setup zoom
        extent = [xmin, ymin, xmax, ymax]
        self.setup_zoom(
            [self.plot_base],
            self.zoomtype,
            data_lims=extent,
            plotName=plotName,
            callbacks=kwargs.get("callbacks", dict()),
        )
        self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]

        # add colorbar
        self.set_colorbar_parameters(zvals, **kwargs)

        # remove tick labels
        for key in [
            "ticks_left",
            "ticks_right",
            "ticks_top",
            "ticks_bottom",
            "tickLabels_left",
            "tickLabels_right",
            "tickLabels_top",
            "tickLabels_bottom",
        ]:
            kwargs[key] = False

        self.set_tick_parameters(**kwargs)

        # add data
        self.plot_data = {"xvals": xvals, "yvals": yvals, "zvals": zvals, "xlabel": xlabel, "ylabel": ylabel}
        self.plot_labels.update({"xlabel": xlabel, "ylabel": ylabel})

        # update normalization
        self.plot_2D_update_normalization(**kwargs)

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
        self.plot_base = self.figure.add_axes(self._axes)

        extent = ut_visuals.extents(labelsX) + ut_visuals.extents(labelsY)

        # Add imshow
        self.cax = self.plot_base.imshow(
            zvalsIon1,
            extent=extent,
            cmap=cmapIon1,
            interpolation=kwargs["interpolation"],
            aspect="auto",
            origin="lower",
            alpha=alphaIon1,
        )
        plotMS2 = self.plot_base.imshow(
            zvalsIon2,
            extent=extent,
            cmap=cmapIon2,
            interpolation=kwargs["interpolation"],
            aspect="auto",
            origin="lower",
            alpha=alphaIon2,
        )

        xmin, xmax = self.plot_base.get_xlim()
        ymin, ymax = self.plot_base.get_ylim()
        self.plot_base.set_xlim(xmin, xmax - 0.5)
        self.plot_base.set_ylim(ymin, ymax - 0.5)

        # legend
        self.set_legend_parameters(None, **kwargs)
        # setup zoom
        extent = [xmin, ymin, xmax, ymax]
        self.setup_zoom([self.plot_base], self.zoomtype, data_lims=extent, plotName=plotName)
        self.plot_limits = [extent[0], extent[2], extent[1], extent[3]]

        # labels
        if xlabel in ["None", None, ""]:
            xlabel = ""
        if ylabel in ["None", None, ""]:
            ylabel = ""

        self.set_plot_xlabel(xlabel, **kwargs)
        self.set_plot_ylabel(ylabel, **kwargs)
        self.set_tick_parameters(**kwargs)
