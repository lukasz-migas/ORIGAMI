"""Visualisation view"""
# Third-party imports
import wx
from pubsub import pub

# Local imports
from origami.utils.secret import get_short_hash
from origami.visuals.mpl.plot_spectrum import PlotSpectrum
from origami.gui_elements.views.view_base import ViewBase
from origami.gui_elements.views.view_base import ViewMPLMixin
from origami.gui_elements.views.view_mixins import ViewAxesMixin


class ViewOverlayPanelMixin:
    """Spectrum panel base"""

    @staticmethod
    def make_panel(parent, figsize, plot_id, axes_size=None):
        """Initialize plot panel"""
        plot_panel = wx.Panel(parent)
        plot_window = PlotSpectrum(plot_panel, figsize=figsize, axes_size=axes_size, plot_id=plot_id)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(plot_window, 1, wx.EXPAND)
        plot_panel.SetSizer(sizer)
        sizer.Fit(plot_panel)

        return plot_panel, plot_window, sizer


class ViewOverlay(ViewBase, ViewMPLMixin, ViewOverlayPanelMixin, ViewAxesMixin):
    """Viewer specialized in displaying overlay and comparison data"""

    VIEW_TYPE = "1d"
    DATA_KEYS = ("x", "y", "obj")
    MPL_KEYS = ["1d", "axes", "legend"]
    UPDATE_STYLES = ("line", "fill")
    ALLOWED_PLOTS = ("line", "multi-line", "waterfall")
    DEFAULT_PLOT = "line"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.PLOT_ID = get_short_hash()
        self.panel, self.figure, self.sizer = self.make_panel(self.parent, self.figsize, self.PLOT_ID, self.axes_size)

        # register view
        pub.sendMessage("view.register", view_id=self.PLOT_ID, view=self)

    def plot_1d_overlay(self):
        """Overlay multiple line plots"""

    def plot_1d_compare(self):
        """Overlay two line plots"""

    def plot_2d_mask(self):
        """Overlay heatmaps using masking"""

    def plot_2d_transparent(self):
        """Overlay heatmaps using transparency"""

    def plot_2d_rgb(self):
        """Overlay multiple heatmaps using RGB overlay"""

    def plot_2d_heatmap(self):
        """Overlay heatmap plots : mean, stddev, variance"""

    def plot_2d_rmsd(self):
        """Overlay two heatmaps using RMSD plot"""

    def plot_2d_rmsf(self):
        """Overlay two heatmaps using RMSD + RMSF plot"""

    def plot_2d_rmsd_matrix(self):
        """Generate RMSD matrix plot from multiple heatmaps"""

    def plot_2d_rmsd_dot(self):
        """Generate RMSD dot plot from multiple heatmaps"""

    def plot_2d_grid_2_to_1(self):
        """Overlay two heatmaps using individual heatmaps -> RMSD plot"""

    def plot_2d_grid_n_x_n(self):
        """Overlay multiple heatmaps in a grid with linked zooming"""

    def plot(self, *args, **kwargs):
        pass

    def update(self, *args, **kwargs):
        pass

    def replot(self, **kwargs):
        pass

    def _update(self):
        pass

    def update_style(self, name: str):
        pass
