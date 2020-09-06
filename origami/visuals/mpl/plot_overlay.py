"""Overlay plot that is a composite of other plots"""
# Standard library imports
import itertools
from typing import List

# Third-party imports
import numpy as np
import matplotlib.patches as mpatches
from matplotlib import gridspec
from matplotlib.collections import PatchCollection

# Local imports
import origami.utils.visuals as ut_visuals
from origami.utils.color import get_font_color
from origami.utils.color import convert_rgb_1_to_255
from origami.utils.ranges import get_min_max
from origami.utils.utilities import rescale
from origami.visuals.mpl.gids import PlotIds
from origami.visuals.mpl.plot_spectrum import PlotSpectrum
from origami.visuals.mpl.plot_heatmap_2d import PlotHeatmap2D


def prepare_grid_2_to_1(**kwargs):
    """Prepare grid 2->1 layout"""
    n_rows, n_cols = kwargs["grid_tto_n_rows"], kwargs["grid_tto_n_cols"]
    main_prop = kwargs["grid_tto_main_x_proportion"]

    # ensure that the number of rows is such that it can be divided in half
    if n_rows % 2 != 0:
        n_rows += 1
    n_row_half = int(n_rows / 2)

    # ensure that the number of colums is such that side plots have at least 2 and main plot is more than 1
    n_col_main = round(main_prop * n_cols)  # round
    while n_cols - n_col_main < 2:
        n_cols += 1

    gs = gridspec.GridSpec(
        n_rows, n_cols, wspace=kwargs["grid_tto_width_space"], hspace=kwargs["grid_tto_height_space"]
    )

    gs_main = gs[:, 0:n_col_main]
    gs_top = gs[0:n_row_half, n_col_main:]
    gs_bottom = gs[n_row_half:, n_col_main:]

    return gs, gs_main, gs_top, gs_bottom


class PlotOverlay(PlotSpectrum, PlotHeatmap2D):
    """Plot overlay"""

    def __init__(self, *args, **kwargs):
        PlotSpectrum.__init__(self, *args, **kwargs)
        PlotHeatmap2D.__init__(self, *args, **kwargs)

    def plot_2d_overlay(self, x, y, array_1, array_2, title="", x_label="", y_label="", obj=None, **kwargs):
        """Simple heatmap plot"""
        self._set_axes()

        # add 2d plot
        xlimits, ylimits, extent = self._compute_xy_limits(x, y, None, is_heatmap=True)

        self.cax = self.plot_base.imshow(
            array_1,
            cmap=kwargs.get("heatmap_colormap_1", "Reds"),
            interpolation=kwargs["heatmap_interpolation"],
            aspect="auto",
            origin="lower",
            extent=[*xlimits, *ylimits],
            alpha=kwargs.get("heatmap_transparency_1", 1.0),
        )
        self.cax = self.plot_base.imshow(
            array_2,
            cmap=kwargs.get("heatmap_colormap_2", "Blues"),
            interpolation=kwargs["heatmap_interpolation"],
            aspect="auto",
            origin="lower",
            extent=[*xlimits, *ylimits],
            alpha=kwargs.get("heatmap_transparency_2", 1.0),
        )
        # set plot limits
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
            is_heatmap=True,
            obj=obj,
        )
        self.store_plot_limits([extent], [self.plot_base])

        # add colorbar
        # self.set_colorbar_parameters(array, **kwargs)

        # update normalization
        # self.plot_2D_update_normalization(**kwargs)
        self.PLOT_TYPE = "heatmap-overlay"

    def plot_heatmap_line(self, x, y, array, y_top, x_label=None, y_label=None, ratio: int = 5, obj=None, **kwargs):
        """Plot heatmap and line plot"""
        self.plot_line_gs = gridspec.GridSpec(ratio, ratio, wspace=0.1, hspace=kwargs["rmsf_h_space"])

        self.plot_base = self.figure.add_subplot(self.plot_line_gs[1:, :])
        self.plot_base.set_gid(PlotIds.PLOT_LH_2D)

        self.plot_line_top = self.figure.add_subplot(self.plot_line_gs[0:1, :], sharex=self.plot_base)
        self.plot_line_top.set_gid(PlotIds.PLOT_LH_LINE)

        xlimits, ylimits, extent = self._compute_xy_limits(x, y, None)

        # add 2d plot
        self.cax = self.plot_base.imshow(
            array,
            cmap=kwargs["heatmap_colormap"],
            interpolation=kwargs["heatmap_interpolation"],
            aspect="auto",
            origin="lower",
            extent=[*xlimits, *ylimits],
            gid=PlotIds.PLOT_LH_2D,
        )

        # set margin plots
        self.plot_line_top.plot(
            x,
            y_top,
            gid=PlotIds.PLOT_LH_LINE,
            color=kwargs["rmsf_line_color"],
            linestyle=kwargs["rmsf_line_style"],
            lw=kwargs["rmsf_line_width"],
        )

        self.plot_1d_add_under_curve(
            x,
            y_top,
            ax=self.plot_line_top,
            gid=PlotIds.PLOT_LH_PATCH,
            spectrum_fill_color=kwargs["rmsf_fill_color"],
            spectrum_fill_transparency=kwargs["rmsf_fill_transparency"],
            spectrum_fill_hatch=kwargs["rmsf_fill_hatch"],
        )

        # turn off the ticks on the density axis for the marginal plots
        self._joint_despine(self.plot_line_top, "horizontal")

        # set plot limits
        self.plot_base.set_xlim(xlimits)
        self.plot_base.set_ylim(ylimits)
        self.set_plot_xlabel(x_label, **kwargs)
        self.set_plot_ylabel(y_label, **kwargs)
        self.set_tick_parameters(**kwargs)

        # add limits of the other plots
        _, _, extent_x = self._compute_xy_limits(x, y_top, 1)

        # setup zoom
        self.setup_new_zoom(
            [self.plot_base, self.plot_line_top],
            data_limits=[extent, extent_x],
            allow_extraction=kwargs.get("allow_extraction", False),
            callbacks=kwargs.get("callbacks", dict()),
            is_heatmap=True,
            obj=obj,
        )
        self.store_plot_limits([extent, extent_x], [self.plot_base, self.plot_line_top])

        # update normalization
        self.plot_2D_update_normalization(**kwargs)
        self.PLOT_TYPE = "heatmap-line"

    def plot_update_grid(self, grid, wspace=None, hspace=None):
        """Update grid values"""
        grid.update(wspace=wspace, hspace=hspace)
        return False

    def plot_2d_grid_2_to_1(self, x, y, array_top, array_bottom, array, x_label=None, y_label=None, obj=None, **kwargs):
        """Plot heatmap + heatmap => heatmap"""
        self.plot_grid_nxn_grid, gs_main, gs_top, gs_bottom = prepare_grid_2_to_1(**kwargs)

        self.plot_base = self.figure.add_subplot(gs_main)
        self.plot_base.set_gid(PlotIds.PLOT_GRID_2_TO_1_RIGHT)

        self.plot_grid_tto_top = self.figure.add_subplot(gs_top, sharex=self.plot_base, sharey=self.plot_base)
        self.plot_grid_tto_top.set_gid(PlotIds.PLOT_GRID_2_TO_1_LEFT_TOP)

        self.plot_grid_tto_bottom = self.figure.add_subplot(gs_bottom, sharex=self.plot_base, sharey=self.plot_base)
        self.plot_grid_tto_bottom.set_gid(PlotIds.PLOT_GRID_2_TO_1_LEFT_BOTTOM)

        xlimits, ylimits, extent = self._compute_xy_limits(x, y, None)

        # main plot
        self.cax = self.plot_base.imshow(
            array,
            cmap=kwargs["heatmap_colormap"],
            interpolation=kwargs["heatmap_interpolation"],
            aspect="auto",
            origin="lower",
            extent=[*xlimits, *ylimits],
            gid=PlotIds.PLOT_GRID_2_TO_1_RIGHT,
        )

        # two-side plots
        self.cax = self.plot_grid_tto_top.imshow(
            array_top,
            cmap=kwargs["heatmap_colormap"],
            interpolation=kwargs["heatmap_interpolation"],
            aspect="auto",
            origin="lower",
            extent=[*xlimits, *ylimits],
            gid=PlotIds.PLOT_GRID_2_TO_1_LEFT_TOP,
        )

        self.cax = self.plot_grid_tto_bottom.imshow(
            array_bottom,
            cmap=kwargs["heatmap_colormap"],
            interpolation=kwargs["heatmap_interpolation"],
            aspect="auto",
            origin="lower",
            extent=[*xlimits, *ylimits],
            gid=PlotIds.PLOT_GRID_2_TO_1_LEFT_BOTTOM,
        )

        # turn off the ticks on the density axis for the marginal plots
        #         self._joint_despine(self.plot_line_top, "horizontal")
        #
        # set plot limits
        self.plot_base.set_xlim(xlimits)
        self.plot_base.set_ylim(ylimits)
        self.set_plot_xlabel(x_label, **kwargs)
        self.set_plot_ylabel(y_label, **kwargs)
        self.set_tick_parameters(**kwargs)

        # setup zoom
        self.setup_new_zoom(
            [self.plot_base, self.plot_grid_tto_top, self.plot_grid_tto_bottom],
            data_limits=[extent, extent, extent],
            allow_extraction=kwargs.get("allow_extraction", False),
            callbacks=kwargs.get("callbacks", dict()),
            is_heatmap=True,
            obj=obj,
        )
        self.store_plot_limits(
            [extent, extent, extent], [self.plot_base, self.plot_grid_tto_top, self.plot_grid_tto_bottom]
        )

        # update normalization
        self.plot_2D_update_normalization(**kwargs)
        self.PLOT_TYPE = "heatmap-tto"

    def plot_2d_grid_n_x_n(
        self, x, y, arrays, n_rows: int, n_cols: int, x_label=None, y_label=None, colormaps=None, obj=None, **kwargs
    ):
        """Plot image grid"""
        gs = gridspec.GridSpec(
            nrows=n_rows, ncols=n_cols, wspace=kwargs["grid_nxn_width_space"], hspace=kwargs["grid_nxn_height_space"]
        )

        xlimits, ylimits, extent = self._compute_xy_limits(x, y, None)

        if colormaps is None:
            colormaps = [kwargs["heatmap_colormap"]] * len(arrays)

        self.plot_base = self.figure.add_subplot(gs[0, 0], aspect="auto")

        # add 2d plot
        axes, extents = [], []  # self.plot_base], [extent]
        for i in range(0, len(arrays)):
            row = int(i // n_cols)
            col = i % n_cols
            if i == 0:
                ax = self.plot_base
            else:
                ax = self.figure.add_subplot(gs[row, col], aspect="auto", sharex=self.plot_base, sharey=self.plot_base)

            array = arrays[i]
            colormap = colormaps[i]
            ax.imshow(
                array,
                cmap=colormap,
                interpolation=kwargs["heatmap_interpolation"],
                aspect="auto",
                origin="lower",
                extent=[*xlimits, *ylimits],
                gid=PlotIds.PLOT_GRID_2_TO_1_RIGHT,
            )
            axes.append(ax)
            extents.append(extent)

            # only show y-axis label in the first column
            if kwargs["grid_nxn_labels_y_first_col"]:
                if col == 0:
                    self.set_plot_ylabel(y_label, ax=ax, **kwargs)
            else:
                self.set_plot_ylabel(y_label, ax=ax, **kwargs)

            # only show x-axis label in the bottom row
            if kwargs["grid_nxn_labels_x_first_row"]:
                if row == n_rows - 1:
                    self.set_plot_xlabel(x_label, ax=ax, **kwargs)
            else:
                self.set_plot_xlabel(x_label, ax=ax, **kwargs)

            # only show y-ticks in the first row
            is_first_col, is_bottom_row = True, True
            if not kwargs["grid_nxn_ticks_y_each"]:
                is_first_col = col == 0
            if not kwargs["grid_nxn_ticks_x_each"]:
                is_bottom_row = row == n_rows - 1
            ax.tick_params(left=is_first_col, bottom=is_bottom_row, labelleft=is_first_col, labelbottom=is_bottom_row)

        # set plot limits
        self.plot_base.set_xlim(xlimits)
        self.plot_base.set_ylim(ylimits)

        # setup zoom
        self.setup_new_zoom(
            axes,
            data_limits=extents,
            allow_extraction=kwargs.get("allow_extraction", False),
            callbacks=kwargs.get("callbacks", dict()),
            is_heatmap=True,
            obj=obj,
        )
        self.store_plot_limits(extents, axes)

        # update normalization
        self.plot_2D_update_normalization(**kwargs)
        self.PLOT_TYPE = "heatmap-grid"

    def plot_2d_matrix(
        self,
        x: np.ndarray,
        y: np.ndarray,
        array: np.ndarray,
        tick_labels: List[str],
        title: str = "",
        x_label: str = "",
        y_label: str = "",
        obj=None,
        **kwargs,
    ):
        """Simple heatmap plot"""
        self._set_axes()

        # add 2d plot
        xlimits, ylimits, extent = self._compute_xy_limits(x, y, None, is_heatmap=True)

        self.cax = self.plot_base.imshow(
            array,
            cmap=kwargs["heatmap_colormap"],
            interpolation=kwargs["heatmap_interpolation"],
            aspect="equal",
            origin="lower",
            extent=[*xlimits, *ylimits],
        )
        # set ticks
        x_size = len(array)
        if tick_labels and len(tick_labels) == x_size:
            self.plot_base.set_xticks(np.arange(0, x_size, 1))
            self.plot_base.set_xticklabels(tick_labels, rotation=kwargs["rmsd_rotation_x"])
            self.plot_base.set_yticks(np.arange(0, x_size, 1))
            self.plot_base.set_yticklabels(tick_labels, rotation=kwargs["rmsd_rotation_y"])

        # set labels
        self.plot_add_rmsd_matrix_labels(array, **kwargs)

        # set plot limits
        self.plot_base.set_xlim(xlimits)
        self.plot_base.set_ylim(ylimits)
        self.set_plot_xlabel(x_label, **kwargs)
        self.set_plot_ylabel(y_label, **kwargs)
        self.set_plot_title(title, **kwargs)
        self.set_tick_parameters(**kwargs)

        # set zoom
        self.setup_new_zoom(
            [self.plot_base],
            data_limits=[extent],
            allow_extraction=kwargs.get("allow_extraction", False),
            callbacks=kwargs.get("callbacks", dict()),
            is_heatmap=True,
            obj=obj,
        )
        self.store_plot_limits([extent], [self.plot_base])

        # add colorbar
        self.set_colorbar_parameters(array, **kwargs)

        # update normalization
        self.plot_2D_update_normalization(**kwargs)
        self.PLOT_TYPE = "heatmap-matrix"

    def plot_2d_dot(
        self,
        x: np.ndarray,
        y: np.ndarray,
        array: np.ndarray,
        tick_labels: List[str],
        title: str = "",
        x_label: str = "",
        y_label: str = "",
        obj=None,
        **kwargs,
    ):
        """Simple heatmap plot"""
        self._set_axes()

        # add 2d plot
        xlimits, ylimits, extent = self._compute_xy_limits(x, y, None, is_heatmap=True)

        self.cax = self._prepare_dots(array.T, **kwargs)
        self.plot_base.add_collection(self.cax)

        # set ticks
        x_size = len(array)
        if tick_labels and len(tick_labels) == x_size:
            self.plot_base.set_xticks(np.arange(0, x_size, 1))
            self.plot_base.set_xticklabels(tick_labels, rotation=kwargs["rmsd_rotation_x"])
            self.plot_base.set_yticks(np.arange(0, x_size, 1))
            self.plot_base.set_yticklabels(tick_labels, rotation=kwargs["rmsd_rotation_y"])

        # set labels
        self.plot_add_rmsd_matrix_labels(array, **kwargs)

        # set plot limits
        self.plot_base.set_xlim(xlimits)
        self.plot_base.set_ylim(ylimits)
        self.set_plot_xlabel(x_label, **kwargs)
        self.set_plot_ylabel(y_label, **kwargs)
        self.set_plot_title(title, **kwargs)
        self.set_tick_parameters(**kwargs)

        # set zoom
        self.setup_new_zoom(
            [self.plot_base],
            data_limits=[extent],
            allow_extraction=kwargs.get("allow_extraction", False),
            callbacks=kwargs.get("callbacks", dict()),
            is_heatmap=True,
            obj=obj,
        )
        self.store_plot_limits([extent], [self.plot_base])

        # add colorbar
        self.set_colorbar_parameters(array, **kwargs)

        # update normalization
        self.plot_2D_update_normalization(**kwargs)
        self.PLOT_TYPE = "heatmap-dot"

    def _prepare_dots(self, array, min_scale=0.1, max_scale=1.0, **kwargs):
        """Prepare RMSD dot data"""
        patches = []

        array_scale = rescale(array, min_scale, max_scale, old_min=0) / 2
        v, ec, fc = [], [], []
        for i, j in itertools.product(list(range(array.shape[0])), list(range(array.shape[1]))):
            label = format(array[i, j], ".2f")
            if label == "nan":
                continue
            circle = mpatches.Circle((i, j), array_scale[i, j])
            patches.append(circle)
            ec.append("k")
            fc.append("r")
            v.append(array[i, j])

        collection = PatchCollection(patches)  # , edgecolors=ec, facecolors=fc)
        collection.set_array(np.asarray(v))
        collection.set_cmap(kwargs["heatmap_colormap"])

        return collection

    def plot_add_rmsd_matrix_labels(self, array, **kwargs):
        """Add matrix/dot labels to the plot"""
        visible = kwargs["rmsd_matrix_add_labels"]
        font_weight = "bold" if kwargs["rmsd_matrix_font_weight"] else "normal"

        cmap = self.cax.get_cmap()
        color = kwargs["rmsd_matrix_font_color"]
        for i, j in itertools.product(list(range(array.shape[0])), list(range(array.shape[1]))):
            label = format(array[i, j], ".2f")
            if label == "nan":
                continue
            if kwargs["rmsd_matrix_font_color_fmt"] == "auto":
                color = get_font_color(convert_rgb_1_to_255(cmap(array[i, j]), 1))
            self.plot_add_label(
                j,
                i,
                label,
                color,
                pickable=False,
                horizontalalignment="center",
                verticalalignment="center",
                fontsize=kwargs["rmsd_matrix_font_size"],
                fontweight=font_weight,
                text_name="rmsd_matrix",
                visible=visible,
            )

    def plot_update_rmsd_matrix_labels(self, **kwargs):
        """Update matrix labels"""
        font_weight = "bold" if kwargs["rmsd_matrix_font_weight"] else "normal"

        for text_obj in self.text:
            if self._check_start_with(text_obj, "rmsd_matrix"):
                text_obj.set_visible(kwargs["rmsd_matrix_add_labels"])
                if not kwargs["rmsd_matrix_font_color_fmt"] == "auto":
                    text_obj.set_color(kwargs["rmsd_matrix_font_color"])
                text_obj.set_fontsize(kwargs["rmsd_matrix_font_size"])
                text_obj.set_fontweight(font_weight)
        return True

    def plot_update_rmsd_matrix_ticks(self, **kwargs):
        """Update matrix x/y-axis labels"""
        self.plot_base.set_xticklabels(self.plot_base.get_xticklabels(), rotation=kwargs["rmsd_rotation_x"])
        self.plot_base.set_yticklabels(self.plot_base.get_xticklabels(), rotation=kwargs["rmsd_rotation_y"])
        return True

    def prepare_rmsd_label(self, x: np.ndarray = None, y: np.ndarray = None, x_max=None, y_max=None, **kwargs):
        """Prepare RMSD label by computing the relative position of the label"""
        x_rel, y_rel = kwargs["rmsd_location"]

        if not x_max and x is not None:
            _, x_max = get_min_max(x)
        if not y_max and y is not None:
            _, y_max = get_min_max(y)

        if x_max is None or y_max is None:
            return None, None

        self._METADATA.update(**{"rmsd_x_max": x_max, "rmsd_y_max": y_max})

        if x_rel is None or y_rel is None:
            return None, None

        return x_max * (x_rel / 100), y_max * (y_rel / 100)

    def plot_add_rmsd_label(self, x: np.ndarray, y: np.ndarray, label: str, text_name: str = "rmsd_label", **kwargs):
        """Add RMSD label to the plot"""
        x_pos, y_pos = self.prepare_rmsd_label(x, y, **kwargs)

        self.plot_add_label(
            x_pos,
            y_pos,
            label,
            kwargs["rmsd_color"],
            0,
            text_name=text_name,
            horizontalalignment="left",
            verticalalignment="bottom",
            fontweight="bold" if kwargs["rmsd_label_font_weight"] else "normal",
            fontsize=kwargs["rmsd_label_font_size"],
        )

    def plot_update_rmsd_label(self, **kwargs):
        """Update label"""
        kwargs = ut_visuals.check_plot_settings(**kwargs)

        text_obj = self.find_object_by_obj_name(self.text, "rmsd_label")
        if text_obj is None:
            return

        if "rmsd_x_max" not in self._METADATA or "rmsd_y_max" not in self._METADATA:
            return

        x_pos, y_pos = self.prepare_rmsd_label(
            None, None, x_max=self._METADATA["rmsd_x_max"], y_max=self._METADATA["rmsd_y_max"], **kwargs  # noqa
        )

        if x_pos is not None and y_pos is not None:
            text_obj.set_position((x_pos, y_pos))
            text_obj.set_visible(True)
        else:
            text_obj.set_visible(False)

        text_obj.set_fontweight(kwargs["rmsd_label_font_weight"])
        text_obj.set_fontsize(kwargs["rmsd_label_font_size"])
        text_obj.set_color(kwargs["rmsd_color"])
        return True
