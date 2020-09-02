"""Heatmap plot"""
# Standard library imports
import logging

# Third-party imports
import wx
import numpy as np
from matplotlib import gridspec
from matplotlib.colors import LogNorm
from matplotlib.colors import Normalize
from matplotlib.colors import PowerNorm
from matplotlib.collections import LineCollection
from mpl_toolkits.axes_grid1 import make_axes_locatable
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

# Local imports
import origami.utils.visuals as ut_visuals
from origami.config.config import CONFIG
from origami.utils.visuals import prettify_tick_format
from origami.visuals.mpl.gids import PlotIds
from origami.processing.spectra import smooth_gaussian_1d
from origami.visuals.mpl.normalize import MidpointNormalize
from origami.visuals.mpl.plot_base import PlotBase

logger = logging.getLogger(__name__)


class PlotHeatmap2D(PlotBase):
    """Heatmap plotting"""

    def __init__(self, *args, **kwargs):
        PlotBase.__init__(self, *args, **kwargs)

        self.ticks = None
        self.tick_labels = None
        self.text = None

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

    def plot_2d(self, x, y, array, title="", x_label="", y_label="", obj=None, **kwargs):
        """Simple heatmap plot"""
        self._set_axes()

        # add 2d plot
        if kwargs["heatmap_plot_type"] == "Image" and not kwargs.get("speedy", False):
            xlimits, ylimits, extent = self._compute_xy_limits(x, y, None, is_heatmap=True)

            self.cax = self.plot_base.imshow(
                array,
                cmap=kwargs["heatmap_colormap"],
                interpolation=kwargs["heatmap_interpolation"],
                aspect="auto",
                origin="lower",
                extent=[*xlimits, *ylimits],
            )
            _plot_type = "heatmap"
        else:
            xlimits, ylimits, extent = self._compute_xy_limits(x, y, None, is_heatmap=True)
            self.cax = self.plot_base.contourf(
                array,
                kwargs["heatmap_n_contour"],
                cmap=kwargs["heatmap_colormap"],
                antialiasing=True,
                origin="lower",
                extent=[*xlimits, *ylimits],
            )
            _plot_type = "contour"
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
        self.set_colorbar_parameters(array, **kwargs)

        # update normalization
        self.plot_2D_update_normalization(**kwargs)
        self.PLOT_TYPE = _plot_type

    def plot_2d_contour(self, x, y, array, title="", x_label="", y_label="", obj=None, **kwargs):
        """Simple heatmap plot"""
        self._set_axes()

        xlimits, ylimits, extent = self._compute_xy_limits(x, y, None, is_heatmap=True)

        # add 2d plot
        self.cax = self.plot_base.contourf(
            array,
            kwargs["heatmap_n_contour"],
            cmap=kwargs["heatmap_colormap"],
            #               norm=kwargs["colormap_norm"],
            antialiasing=True,
            origin="lower",
            extent=[*xlimits, *ylimits],
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
        self.set_colorbar_parameters(array, **kwargs)

        # update normalization
        self.plot_2D_update_normalization(**kwargs)
        self.PLOT_TYPE = "contour"

    def plot_2d_update_data(self, x, y, array, x_label=None, y_label=None, obj=None, **kwargs):
        """Update heatmap data without the need for full replot"""
        if kwargs["heatmap_plot_type"] == "contour":
            raise AttributeError("Contour plot does not have `set_data`")

        # update limits and extents
        xlimits, ylimits, extent = self._compute_xy_limits(x, y, None, is_heatmap=True)

        self.cax.set_data(array)
        self.cax.set_extent([*xlimits, *ylimits])
        self.cax.set_cmap(kwargs["heatmap_colormap"])
        self.cax.set_interpolation(kwargs["heatmap_interpolation"])
        self.cax.set_clim(vmin=array.min(), vmax=array.max())

        # set plot limits
        self.set_plot_xlabel(x_label, **kwargs)
        self.set_plot_ylabel(y_label, **kwargs)

        # update normalization
        self.plot_2D_update_normalization(**kwargs)

        # add colorbar
        if self.PLOT_TYPE in ["heatmap"]:
            self.set_colorbar_parameters(array, **kwargs)
            axes = [self.plot_base]
            extent = [extent]
        elif self.PLOT_TYPE in ["joint"]:
            yy = array.sum(axis=1)
            xy = array.sum(axis=0)
            self.update_line(x, xy, PlotIds.PLOT_JOINT_X, self.plot_joint_x)
            self.update_line(yy, y, PlotIds.PLOT_JOINT_Y, self.plot_joint_y)
            # add limits of the other plots
            _, _, extent_x = self._compute_xy_limits(x, xy, None)
            _, _, extent_y = self._compute_xy_limits(yy, y, None)
            axes = [self.plot_base, self.plot_joint_x, self.plot_joint_y]
            extent = [extent, extent_x, extent_y]
        else:
            raise ValueError("Should not have plotted this")

        # update plot limits
        self.update_extents(extent, obj=obj)
        self.store_plot_limits(extent, axes)

    def plot_2d_update_heatmap_style(
        self, array: np.ndarray = None, colormap: str = None, interpolation: str = None, cbar_kwargs=None
    ):
        """Update style of heatmap plot"""
        self._is_locked()

        if colormap is not None:
            self.cax.set_cmap(colormap)
        if interpolation is not None and hasattr(self, "set_interpolation"):
            self.cax.set_interpolation(interpolation)

        # update colorbar
        if array is not None and cbar_kwargs is not None:
            if self.PLOT_TYPE not in ["joint"]:
                self.set_colorbar_parameters(array, **cbar_kwargs)

    def plot_2d_update_normalization(self, array: np.ndarray, **kwargs):
        """Update plot normalization"""
        self._is_locked()
        cmap_norm, _ = self.get_heatmap_normalization(array, **kwargs)
        self.cax.set_norm(cmap_norm)

    def plot_2d_update_colorbar(self, **kwargs):
        """Update colorbar parameters"""
        self._is_locked()
        self.plot_2d_colorbar_update(**kwargs)

    @staticmethod
    def _prepare_violin(x, y, array, **kwargs):
        """Prepare violin data"""
        normalize = kwargs.get("violin_normalize", True)
        smooth = kwargs.get("violin_smooth", True)
        sigma = kwargs.get("violin_smooth_sigma", 2)
        spacing = kwargs.get("violin_spacing", 0.5)
        orientation = kwargs.get("violin_orientation", "vertical")
        min_percentage = kwargs.get("violin_min_percentage", 0.03)
        offset = spacing
        n_signals = len(x)

        yy, xy = [], []
        tick_positions, tick_labels = [], []
        for i, _y in enumerate(array.T):
            # normalize (to 1) the intensity of signal
            if normalize:
                _y = (_y / _y.max()).astype(np.float32)
            if smooth:
                _y = smooth_gaussian_1d(_y, sigma)

            # increase the baseline to set the signal apart from the one before it
            max_value = _y.max()
            filter_index = _y > (_y.max() * min_percentage)  # noqa
            _y = _y[filter_index]
            if len(_y) == 0:
                continue
            # 1) ensure the violin line is created in both directions by appending it going forward and backwards
            # 2) at the very end, make sure to close it off by inserting the very first value
            if orientation == "vertical":
                _intensity = np.append(_y + offset, (-_y + offset)[::-1])
                _intensity = np.append(_intensity, _intensity[0])
                _variable = np.append(y[filter_index], y[filter_index][::-1])
                _variable = np.append(_variable, _variable[0])
                xy.append(np.column_stack([_intensity, _variable]))
                yy.append(_y.max() + offset)
            else:
                _variable = np.append(_y + offset, (-_y + offset)[::-1])
                _intensity = np.append(y[filter_index], y[filter_index][::-1])
                xy.append(np.column_stack([_intensity, _variable]))
                yy.append(_y.max() + offset)
            offset = offset + (max_value * 2) + spacing

            if kwargs["violin_labels_frequency"] != 0:
                if i % kwargs["violin_labels_frequency"] == 0 or i == n_signals - 1:
                    tick_positions.append(offset)
                    tick_labels.append(ut_visuals.convert_label(x[i], label_format=kwargs["violin_labels_format"]))

        return xy, yy, tick_positions, tick_labels

    def plot_violin_update(self, x: np.ndarray, y: np.ndarray, array: np.ndarray, name: str, **kwargs):
        """Generic violin update function"""
        self._is_locked()

        if name.startswith("violin."):
            name = name.split("violin.")[-1]

        if name.startswith("line") or name.startswith("fill"):
            self.plot_violin_update_line_style(array, **kwargs)
        elif name.startswith("label"):
            if name.endswith(".reset"):
                self.plot_violin_reset_label(x, y, array, **kwargs)

    def plot_violin_update_line_style(self, array, **kwargs):
        """Update violin lines"""
        n_signals = array.shape[1]
        lc, fc = self.get_violin_colors(n_signals, **kwargs)
        for collection in self.plot_base.collections:
            if isinstance(collection, LineCollection):
                collection.set_linestyle(kwargs["violin_line_style"])
                collection.set_linewidth(kwargs["violin_line_width"])
                collection.set_edgecolors(lc)
                if kwargs["violin_fill_under"]:
                    collection.set_facecolors(fc)
                else:
                    collection.set_facecolors([])

    def plot_violin_reset_label(self, x, y, array, **kwargs):
        """Update violin lines"""
        orientation = kwargs.get("violin_orientation", "vertical")
        _, _, tick_positions, tick_labels = self._prepare_violin(x, y, array, **kwargs)

        if orientation != "vertical":
            self.plot_base.set_yticks(tick_positions)
            self.plot_base.set_yticklabels(tick_labels)
        else:
            self.plot_base.set_xticks(tick_positions)
            self.plot_base.set_xticklabels(tick_labels)

    def plot_violin_quick(self, x, y, array, x_label=None, y_label=None, **kwargs):
        """Plot as violin"""
        # TODO: add labels
        self._set_axes()

        orientation = kwargs.get("violin_orientation", "vertical")
        xy, yy, tick_positions, tick_labels = self._prepare_violin(x, y, array, **kwargs)

        # get list of parameters for the plot
        n_signals = len(x)
        lc, fc = self.get_violin_colors(n_signals, **kwargs)

        # the list of values is reversed to ensure that the zorder of each plot/line is correct
        coll = LineCollection(xy[::-1], antialiased=np.ones(len(xy)))
        self.plot_base.add_collection(coll)

        # set line style
        coll.set_edgecolors(lc)
        coll.set_linestyle(kwargs["violin_line_style"])
        coll.set_linewidths(kwargs["violin_line_width"])

        # set face style
        if kwargs["violin_fill_under"]:
            coll.set_facecolors(fc)
            coll.set_clip_on(True)

        # in violin plot, the horizontal axis is the mobility axis
        if orientation != "vertical":
            xlimits, ylimits, extent = self._compute_xy_limits(y, yy)
            self.plot_base.set_yticks(tick_positions)
            self.plot_base.set_yticklabels(tick_labels)
            x_label, y_label = y_label, x_label
        else:
            xlimits, ylimits, extent = self._compute_xy_limits(yy, y)
            self.plot_base.set_xticks(tick_positions)
            self.plot_base.set_xticklabels(tick_labels)

        # set plot limits
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
        self.PLOT_TYPE = "violin"

    def plot_violin(self, x, y, array, x_label=None, y_label=None, obj=None, **kwargs):
        """Plot as violin"""
        self._set_axes()

        normalize = kwargs.get("violin_normalize", True)
        spacing = kwargs.get("violin_spacing", 0.5)
        orientation = kwargs.get("violin_orientation", "vertical")
        min_percentage = kwargs.get("violin_min_percentage", 0.03)

        offset = spacing

        # get list of colors
        n_signals = len(x)
        lc, fc = self.get_waterfall_colors(n_signals, **kwargs)

        yy, tick_labels, tick_positions = [], [], []
        # iterate over each signal, line and face color
        for i, (_y, _lc, _fc) in enumerate(zip(array.T, lc, fc)):
            # normalize (to 1) the intensity of signal
            if normalize:
                _y = (_y / _y.max()).astype(np.float32)
            _y = np.nan_to_num(_y, nan=0)

            # in order to remove the baseline of the plot, we apply slight filter on the data, reducing the overall
            # number of points
            filter_index = _y > (_y.max() * min_percentage)  # noqa
            _y = _y[filter_index]
            if len(_y) == 0:
                continue
            if orientation == "vertical":
                self.plot_base.fill_betweenx(
                    y[filter_index],
                    -_y + offset,
                    _y + offset,
                    edgecolor=_lc,
                    linewidth=kwargs["violin_line_width"],
                    facecolor=_fc,
                    clip_on=True,
                )
            else:
                self.plot_base.fill_between(
                    y[filter_index],
                    -_y + offset,
                    _y + offset,
                    edgecolor=_lc,
                    linewidth=kwargs["violin_line_width"],
                    facecolor=_fc,
                    clip_on=True,
                )
            # keep track of the maximum values
            yy.append(_y.max() + offset)

            if kwargs["violin_labels_frequency"] != 0:
                if i % kwargs["violin_labels_frequency"] == 0 or i == n_signals - 1:
                    tick_positions.append(offset)
                    tick_labels.append(ut_visuals.convert_label(x[int(i)], label_format=kwargs["violin_labels_format"]))

            # increase the baseline to set the signal aparxt from the one before it
            offset = offset + (_y.max() * 2) + spacing

        # in violin plot, the horizontal axis is the mobility axis
        if orientation != "vertical":
            xlimits, ylimits, extent = self._compute_xy_limits(y, yy)
            self.plot_base.set_yticks(tick_positions)
            self.plot_base.set_yticklabels(tick_labels)
            x_label, y_label = y_label, x_label
        else:
            xlimits, ylimits, extent = self._compute_xy_limits(yy, y)
            self.plot_base.set_xticks(tick_positions)
            self.plot_base.set_xticklabels(tick_labels)

        # set plot limits
        self.plot_base.set_xlim(xlimits)
        self.plot_base.set_ylim(ylimits)
        self.set_plot_xlabel(x_label, **kwargs)
        self.set_plot_ylabel(y_label, **kwargs)
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
        self.PLOT_TYPE = "violin"

    def plot_joint(self, x, y, array, x_label=None, y_label=None, ratio: int = 5, obj=None, **kwargs):
        """Plot as joint"""
        gs = gridspec.GridSpec(ratio + 1, ratio + 1, wspace=0.1, hspace=0.1)
        self.plot_base = self.figure.add_subplot(gs[1:, :-1])
        self.plot_base.set_gid(PlotIds.PLOT_JOINT_XY)

        self.plot_joint_x = self.figure.add_subplot(gs[0, :-1], sharex=self.plot_base)
        self.plot_joint_x.set_gid(PlotIds.PLOT_JOINT_X)

        self.plot_joint_y = self.figure.add_subplot(gs[1:, -1], sharey=self.plot_base)
        self.plot_joint_y.set_gid(PlotIds.PLOT_JOINT_Y)

        xlimits, ylimits, extent = self._compute_xy_limits(x, y, None)

        yy = array.sum(axis=1)
        xy = array.sum(axis=0)

        # add 2d plot
        self.cax = self.plot_base.imshow(
            array,
            cmap=kwargs["heatmap_colormap"],
            interpolation=kwargs["heatmap_interpolation"],
            #             norm=kwargs["colormap_norm"],
            aspect="auto",
            origin="lower",
            extent=[*xlimits, *ylimits],
            gid=PlotIds.PLOT_JOINT_XY,
        )

        # set margin plots
        self.plot_joint_x.plot(x, xy, gid=PlotIds.PLOT_JOINT_X)
        self.plot_joint_y.plot(yy, y, gid=PlotIds.PLOT_JOINT_Y)

        # turn off the ticks on the density axis for the marginal plots
        self._joint_despine(self.plot_joint_x, "horizontal")
        self._joint_despine(self.plot_joint_y, "vertical")

        # set plot limits
        self.plot_base.set_xlim(xlimits)
        self.plot_base.set_ylim(ylimits)
        self.set_plot_xlabel(x_label, **kwargs)
        self.set_plot_ylabel(y_label, **kwargs)
        self.set_tick_parameters(**kwargs)

        # add limits of the other plots
        _, _, extent_x = self._compute_xy_limits(x, xy, 1)
        _, _, extent_y = self._compute_xy_limits(yy, y, 1)

        # setup zoom
        self.setup_new_zoom(
            [self.plot_base, self.plot_joint_x, self.plot_joint_y],
            data_limits=[extent, extent_x, extent_y],
            allow_extraction=kwargs.get("allow_extraction", False),
            callbacks=kwargs.get("callbacks", dict()),
            is_heatmap=True,
            is_joint=True,
            obj=obj,
        )
        self.store_plot_limits([extent, extent_x, extent_y], [self.plot_base, self.plot_joint_x, self.plot_joint_y])

        # update normalization
        self.plot_2D_update_normalization(**kwargs)
        self.PLOT_TYPE = "joint"

    @staticmethod
    def _joint_despine(ax, orientation: str):
        """Despine joint plot"""
        # prevent scientific notation
        try:
            ax.get_xaxis().get_major_formatter().set_useOffset(False)
        except AttributeError:
            logger.warning("Could not fully set label offsets", exc_info=False)
        ax.ticklabel_format(useOffset=False, style="plain", axis="both")
        ax.tick_params(
            axis="both",
            left=True if orientation == "vertical" else False,
            top=False,
            bottom=True if orientation == "horizontal" else False,
            right=False,
            labelleft=False,
            labelright=False,
            labeltop=False,
            labelbottom=False,
        )

    def plot_2d_rgb(self, x, y, array, title="", x_label="", y_label="", obj=None, **kwargs):
        """Simple heatmap plot"""
        self._set_axes()

        # add 2d plot
        xlimits, ylimits, extent = self._compute_xy_limits(x, y, None, is_heatmap=True)

        self.cax = self.plot_base.imshow(
            array,
            cmap=kwargs["heatmap_colormap"],
            interpolation=kwargs["heatmap_interpolation"],
            aspect="auto",
            origin="lower",
            extent=[*xlimits, *ylimits],
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
        self.set_colorbar_parameters(array, **kwargs)

        # update normalization
        self.plot_2D_update_normalization(**kwargs)
        self.PLOT_TYPE = "heatmap-rgb"

    # def plot_2D_rgb(
    #     self, zvals, xvals, yvals, xlabel, ylabel, zoom="box", axesSize=None, legend_text=None, plotName="RGB",
    #     **kwargs
    # ):
    #     # update settings
    #     self._check_and_update_plot_settings(plot_name=plotName, axes_size=axesSize, **kwargs)
    #
    #     matplotlib.rc("xtick", labelsize=kwargs["axes_tick_font_size"])
    #     matplotlib.rc("ytick", labelsize=kwargs["axes_tick_font_size"])
    #
    #     # Plot
    #     self.plot_base = self.figure.add_axes(self._axes)
    #
    #     handles = []
    #     if legend_text is not None:
    #         for i in range(len(legend_text)):
    #             handles.append(
    #                 patches.Patch(
    #                     color=legend_text[i][0], label=legend_text[i][1], alpha=kwargs["legend_patch_transparency"]
    #                 )
    #             )
    #
    #     extent = ut_visuals.extents(xvals) + ut_visuals.extents(yvals)
    #
    #     # Add imshow
    #     self.cax = self.plot_base.imshow(
    #         zvals, extent=extent, interpolation=kwargs["heatmap_interpolation"], origin="lower", aspect="auto"
    #     )
    #
    #     xmin, xmax = self.plot_base.get_xlim()
    #     ymin, ymax = self.plot_base.get_ylim()
    #     self.plot_base.set_xlim(xmin, xmax - 0.5)
    #     self.plot_base.set_ylim(ymin, ymax - 0.5)
    #     extent = [xmin, ymin, xmax, ymax]
    #
    #     # legend
    #     self.set_legend_parameters(handles, **kwargs)
    #
    #     self.set_plot_xlabel(xlabel, **kwargs)
    #     self.set_plot_ylabel(ylabel, **kwargs)
    #
    #     self.set_tick_parameters(**kwargs)
    #
    #     self.setup_zoom([self.plot_base], self.zoomtype, data_lims=extent)
    #     self.plot_base.plot_limits = [extent[0], extent[2], extent[1], extent[3]]

    @staticmethod
    def get_heatmap_normalization(
        array: np.ndarray,
        heatmap_normalization: str,
        heatmap_normalization_min: float,
        heatmap_normalization_mid: float,
        heatmap_normalization_max: float,
        heatmap_normalization_power_gamma: float,
        **kwargs,
    ):
        """Get heatmap normalization"""
        # check normalization
        if heatmap_normalization not in ["Midpoint", "Logarithmic", "Power", "MinMax"]:
            raise ValueError("Incorrect normalization method")

        # normalize
        zvals_max = np.max(array)
        cmap_min = (zvals_max * heatmap_normalization_min) / 100.0
        cmap_mid = (zvals_max * heatmap_normalization_mid) / 100.0
        cmap_max = (zvals_max * heatmap_normalization_max) / 100.0

        # compute normalization
        reset_colorbar = False
        if heatmap_normalization == "Midpoint":
            cmap_norm = MidpointNormalize(midpoint=cmap_mid, v_min=cmap_min, v_max=cmap_max)
        elif heatmap_normalization == "Logarithmic":
            cmap_norm = LogNorm(vmin=cmap_min + 0.01, vmax=cmap_max)
        elif heatmap_normalization == "Power":
            cmap_norm = PowerNorm(gamma=heatmap_normalization_power_gamma, vmin=cmap_min, vmax=cmap_max)
        elif heatmap_normalization == "MinMax":
            cmap_norm = Normalize(vmin=cmap_min, vmax=cmap_max)
            reset_colorbar = True
        else:
            raise ValueError("Incorrect normalization method")

        return cmap_norm, reset_colorbar

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
        self.plot_2d_colorbar_update(**kwargs)

    def plot_2d_colorbar_update(self, **kwargs):
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
                    width=f"{kwargs['colorbar_inset_width']}%",
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
                cbar = self.figure.colorbar(self.cax, cax=self.cbar, orientation="vertical", ticks=ticks)
                self.cbar.yaxis.set_ticks_position(kwargs["colorbar_position"])
                self.cbar.set_yticklabels(tick_labels)
            elif kwargs["colorbar_position"] in ["top", "bottom"]:
                cbar = self.figure.colorbar(self.cax, cax=self.cbar, orientation="horizontal", ticks=ticks)
                self.cbar.xaxis.set_ticks_position(kwargs["colorbar_position"])
                self.cbar.set_xticklabels(tick_labels)
            else:
                cbar = self.figure.colorbar(self.cax, cax=self.cbar, orientation="horizontal", ticks=ticks)
                self.cbar.xaxis.set_ticks_position("bottom")
                self.cbar.set_xticklabels(tick_labels)

            # set parameters
            cbar.outline.set_edgecolor(kwargs["colorbar_edge_color"])
            cbar.outline.set_linewidth(kwargs["colorbar_edge_width"])
            self.cbar.ticks = ticks
            self.cbar.tick_labels = tick_labels
            self.cbar.tick_params(
                labelsize=kwargs["colorbar_label_size"],
                labelcolor=kwargs["colorbar_label_color"],
                color=kwargs["colorbar_edge_color"],
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

    # def plot_2D_update(self, **kwargs):
    #     """Update plot data"""
    #     if self.lock_plot_from_updating:
    #         self._locked()
    #
    #     if "colormap_norm" in kwargs:
    #         self.cax.set_norm(kwargs["colormap_norm"])
    #
    #     #         kwargs = self._check_colormap(**kwargs)
    #     self.cax.set_cmap(kwargs["heatmap_colormap"])
    #
    #     try:
    #         self.cax.set_interpolation(kwargs["heatmap_interpolation"])
    #     except AttributeError:
    #         pass
    #
    #     # update labels
    #     self.set_plot_xlabel(**kwargs)
    #     self.set_plot_ylabel(**kwargs)
    #     self.set_tick_parameters(**kwargs)
    #     self.plot_2d_colorbar_update(**kwargs)
    #
    #     self.plot_parameters = kwargs

    def plot_2D_update_normalization(self, **kwargs):
        if self.lock_plot_from_updating:
            self._locked()

        if hasattr(self, "plot_data"):
            if "zvals" in self.plot_data:
                cmap_norm, _ = self.get_heatmap_normalization(self.plot_data["zvals"], **kwargs)

                self.plot_parameters["colormap_norm"] = cmap_norm

                if "colormap_norm" in self.plot_parameters:
                    self.cax.set_norm(self.plot_parameters["colormap_norm"])
                    self.plot_2d_colorbar_update(**kwargs)

    # def plot_2D_update_data(self, xvals, yvals, xlabel, ylabel, zvals, **kwargs):
    #
    #     # clear plot in some circumstances
    #     if self._plot_tag in ["rmsd_matrix"]:
    #         self.clear()
    #
    #     # update settings
    #     self._check_and_update_plot_settings(**kwargs)
    #
    #     # update limits and extents
    #     extent = ut_visuals.extents(xvals) + ut_visuals.extents(yvals)
    #     self.cax.set_data(zvals)
    #     self.cax.set_norm(kwargs.get("colormap_norm", None))
    #     self.cax.set_extent(extent)
    #     self.cax.set_cmap(kwargs["heatmap_colormap"])
    #     self.cax.set_interpolation(kwargs["heatmap_interpolation"])
    #
    #     xmin, xmax, ymin, ymax = extent
    #     self.plot_base.set_xlim(xmin, xmax)
    #     self.plot_base.set_ylim(ymin, ymax)
    #
    #     extent = [xmin, ymin, xmax, ymax]
    #     if kwargs.get("update_extents", True):
    #         self.update_extents([extent])
    #         self.plot_base.plot_limits = [extent[0], extent[2], extent[1], extent[3]]
    #
    #     self.set_plot_xlabel(xlabel, **kwargs)
    #     self.set_plot_ylabel(ylabel, **kwargs)
    #
    #     try:
    #         leg = self.plot_base.axes.get_legend()
    #         leg.remove()
    #     except Exception:
    #         pass
    #
    #     # add data
    #     self.plot_data = {"xvals": xvals, "yvals": yvals, "zvals": zvals, "xlabel": xlabel, "ylabel": ylabel}
    #     self.plot_labels.update({"xlabel": xlabel, "ylabel": ylabel})
    #
    #     # add colorbar
    #     self.set_colorbar_parameters(zvals, **kwargs)

    #


class TestPanel(wx.Dialog):
    """Test panel"""

    btn_1 = None
    btn_2 = None

    def __init__(self, parent):

        wx.Dialog.__init__(self, parent, wx.ID_ANY, title="TEST DIALOG")

        plot_panel = wx.Panel(self)
        plot_window = PlotHeatmap2D(plot_panel)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(plot_window, 1, wx.EXPAND)
        plot_panel.SetSizer(main_sizer)
        main_sizer.Fit(plot_panel)

        main_sizer.Fit(self)
        self.SetSizerAndFit(main_sizer)
        self.CenterOnScreen()
        self.Show()

        array = np.random.randint(0, 1, (20, 200))
        array = array.astype(np.float32)
        kwargs = CONFIG.get_mpl_parameters(["colorbar", "2d", "normalization", "axes"])

        x = np.arange(array.shape[0])
        y = np.arange(array.shape[1])
        plot_window.plot_2d(x, y, array, **kwargs)


def _main():
    app = wx.App()
    frame = wx.Frame(None, -1)
    panel = TestPanel(frame)
    panel.ShowModal()
    app.MainLoop()


if __name__ == "__main__":
    _main()
