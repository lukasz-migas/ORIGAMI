"""Overlay mixins"""
# Local imports
from origami.widgets.overlay.view_overlay import ViewOverlay
from origami.widgets.overlay.overlay_handler import OVERLAY_HANDLER


class PanelOverlayViewerMixin:
    """Base components of overlay viewer"""

    view_overlay = None

    # noinspection DuplicatedCode
    def make_plot_panel(self, split_panel):
        """Make plot panel"""
        self.view_overlay = ViewOverlay(
            split_panel, (0.01, 0.01), x_label="x-axis", y_label="y-axis", filename="overlay"
        )
        return self.view_overlay.panel

    @staticmethod
    def _parse_kwargs(forced_kwargs=None, **kwargs):
        """Parse keyword parameters to be shown by the plot"""
        if isinstance(forced_kwargs, dict):
            kwargs.update(**forced_kwargs)
        return kwargs

    def on_plot_1d_butterfly(self, group_obj, forced_kwargs=None):
        """Heatmap plot"""
        x_top, x_bottom, y_top, y_bottom, kwargs = OVERLAY_HANDLER.prepare_overlay_1d_butterfly(group_obj)
        kwargs = self.view_overlay.plot_1d_compare(
            x_top, x_bottom, y_top, y_bottom, forced_kwargs=self._parse_kwargs(forced_kwargs, **kwargs)
        )
        return kwargs

    def on_plot_1d_subtract(self, group_obj, forced_kwargs=None):
        """Heatmap plot"""
        x_top, x_bottom, y_top, y_bottom, kwargs = OVERLAY_HANDLER.prepare_overlay_1d_subtract(group_obj)
        kwargs = self.view_overlay.plot_1d_compare(
            x_top, x_bottom, y_top, y_bottom, forced_kwargs=self._parse_kwargs(forced_kwargs, **kwargs)
        )
        return kwargs

    def on_plot_1d_overlay(self, group_obj, forced_kwargs=None):
        """Heatmap plot"""
        x, y, array = OVERLAY_HANDLER.prepare_overlay_1d_multiline(group_obj)
        kwargs = dict(waterfall_increment=0)
        kwargs = self.view_overlay.plot_1d_overlay(
            x, y, array, forced_kwargs=self._parse_kwargs(forced_kwargs, **kwargs)
        )
        return kwargs

    def on_plot_1d_waterfall(self, group_obj, forced_kwargs=None):
        """Heatmap plot"""
        x, y, array = OVERLAY_HANDLER.prepare_overlay_1d_multiline(group_obj)
        kwargs = self.view_overlay.plot_1d_overlay(
            x, y, array, forced_kwargs=self._parse_kwargs(forced_kwargs, **dict())
        )
        return kwargs

    def on_plot_2d_mean(self, group_obj, forced_kwargs=None):
        """Heatmap plot"""
        array, x, y, x_label, y_label = OVERLAY_HANDLER.prepare_overlay_2d_mean(group_obj)
        kwargs = self.view_overlay.plot_2d_heatmap(
            x, y, array, x_label=x_label, y_label=y_label, forced_kwargs=self._parse_kwargs(forced_kwargs, **dict())
        )
        return kwargs

    def on_plot_2d_stddev(self, group_obj, forced_kwargs=None):
        """Heatmap plot"""
        array, x, y, x_label, y_label = OVERLAY_HANDLER.prepare_overlay_2d_stddev(group_obj)
        kwargs = self.view_overlay.plot_2d_heatmap(
            x, y, array, x_label=x_label, y_label=y_label, forced_kwargs=self._parse_kwargs(forced_kwargs, **dict())
        )
        return kwargs

    def on_plot_2d_variance(self, group_obj, forced_kwargs=None):
        """Heatmap plot"""
        array, x, y, x_label, y_label = OVERLAY_HANDLER.prepare_overlay_2d_variance(group_obj)
        kwargs = self.view_overlay.plot_2d_heatmap(
            x, y, array, x_label=x_label, y_label=y_label, forced_kwargs=self._parse_kwargs(forced_kwargs, **dict())
        )
        return kwargs

    def on_plot_2d_rmsd(self, group_obj, forced_kwargs=None):
        """Heatmap plot"""
        array, x, y, x_label, y_label, rmsd_label = OVERLAY_HANDLER.prepare_overlay_2d_rmsd(group_obj)
        kwargs = self.view_overlay.plot_2d_rmsd(
            x,
            y,
            array,
            rmsd_label,
            x_label=x_label,
            y_label=y_label,
            forced_kwargs=self._parse_kwargs(forced_kwargs, **dict()),
        )
        return kwargs

    def on_plot_2d_rmsf(self, group_obj, forced_kwargs=None):
        """Heatmap plot"""
        array, x, y, rmsf_y, x_label, y_label, rmsd_label = OVERLAY_HANDLER.prepare_overlay_2d_rmsf(group_obj)
        kwargs = self.view_overlay.plot_2d_rmsf(
            x,
            y,
            array,
            rmsf_y,
            rmsd_label,
            x_label=x_label,
            y_label=y_label,
            forced_kwargs=self._parse_kwargs(forced_kwargs, **dict()),
        )
        return kwargs

    def on_plot_2d_rmsd_matrix(self, group_obj, forced_kwargs=None):
        """Heatmap plot"""
        array, x, y, tick_labels = OVERLAY_HANDLER.prepare_overlay_2d_rmsd_matrix(group_obj)
        kwargs = self.view_overlay.plot_2d_rmsd_matrix(
            x, y, array, tick_labels, forced_kwargs=self._parse_kwargs(forced_kwargs, **dict())
        )
        return kwargs

    def on_plot_2d_rmsd_dot(self, group_obj, forced_kwargs=None):
        """Heatmap plot"""
        array, x, y, tick_labels = OVERLAY_HANDLER.prepare_overlay_2d_rmsd_matrix(group_obj)
        kwargs = self.view_overlay.plot_2d_rmsd_dot(
            x, y, array, tick_labels, forced_kwargs=self._parse_kwargs(forced_kwargs, **dict())
        )
        return kwargs

    def on_plot_2d_mask(self, group_obj, forced_kwargs=None):
        """Heatmap plot"""
        array_1, array_2, x, y, x_label, y_label, kwargs = OVERLAY_HANDLER.prepare_overlay_2d_mask(group_obj)
        kwargs = self.view_overlay.plot_2d_overlay(
            x,
            y,
            array_1,
            array_2,
            x_label=x_label,
            y_label=y_label,
            forced_kwargs=self._parse_kwargs(forced_kwargs, **kwargs),
        )
        return kwargs

    def on_plot_2d_transparent(self, group_obj, forced_kwargs=None):
        """Heatmap plot"""
        array_1, array_2, x, y, x_label, y_label, kwargs = OVERLAY_HANDLER.prepare_overlay_2d_transparent(group_obj)
        kwargs = self.view_overlay.plot_2d_overlay(
            x,
            y,
            array_1,
            array_2,
            x_label=x_label,
            y_label=y_label,
            forced_kwargs=self._parse_kwargs(forced_kwargs, **kwargs),
        )
        return kwargs

    def on_plot_2d_tto(self, group_obj, forced_kwargs=None):
        """Heatmap plot"""
        a_1, a_2, array, x, y, x_label, y_label, rmsd_label = OVERLAY_HANDLER.prepare_overlay_2d_grid_compare_rmsd(
            group_obj
        )
        kwargs = self.view_overlay.plot_2d_grid_compare_rmsd(
            x,
            y,
            a_1,
            a_2,
            array,
            rmsd_label,
            x_label=x_label,
            y_label=y_label,
            forced_kwargs=self._parse_kwargs(forced_kwargs, **dict()),
        )
        return kwargs

    def on_plot_2d_nxn(self, group_obj, forced_kwargs=None):
        """Heatmap plot"""
        arrays, x, y, x_label, y_label, n_rows, n_cols = OVERLAY_HANDLER.prepare_overlay_2d_grid_n_x_n(group_obj)
        kwargs = self.view_overlay.plot_2d_grid_n_x_n(
            x,
            y,
            arrays,
            n_rows,
            n_cols,
            x_label=x_label,
            y_label=y_label,
            forced_kwargs=self._parse_kwargs(forced_kwargs, **dict()),
        )
        return kwargs

    def on_plot_2d_side_by_side(self, group_obj, forced_kwargs=None):
        """Heatmap plot"""
        arrays, x, y, x_label, y_label, n_rows, n_cols = OVERLAY_HANDLER.prepare_overlay_2d_grid_n_x_n(
            group_obj, n_max=2
        )
        kwargs = self.view_overlay.plot_2d_grid_n_x_n(
            x,
            y,
            arrays,
            n_rows,
            n_cols,
            x_label=x_label,
            y_label=y_label,
            forced_kwargs=self._parse_kwargs(forced_kwargs, **dict()),
        )
        return kwargs

    def on_plot_2d_rgb(self, group_obj, forced_kwargs=None):
        """Heatmap plot"""
        array, x, y, x_label, y_label, kwargs = OVERLAY_HANDLER.prepare_overlay_2d_rgb(group_obj)
        kwargs = self.view_overlay.plot_2d_rgb(
            x, y, array, x_label=x_label, y_label=y_label, forced_kwargs=self._parse_kwargs(forced_kwargs, **kwargs)
        )
        return kwargs
