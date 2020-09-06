"""Overlay viewer"""
# Standard library imports
import time
import logging

# Third-party imports
import wx

# Local imports
from origami.styles import MiniFrame
from origami.utils.utilities import report_time
from origami.widgets.overlay.mixins import PanelOverlayViewerMixin
from origami.widgets.overlay.panel_plot_parameters import PanelOverlayViewerSettings

LOGGER = logging.getLogger(__name__)


class PanelOverlayViewer(MiniFrame, PanelOverlayViewerMixin):
    """Overlay viewer and editor"""

    plot_settings = None

    def __init__(self, parent, presenter, icons=None, group_obj=None, debug: bool = False):
        MiniFrame.__init__(
            self,
            parent,
            title="Overlay viewer...",
            style=wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX,
            bind_key_events=False,
        )
        t_start = time.time()
        self.view = parent
        self.presenter = presenter
        self._icons = self._get_icons(icons)

        self._window_size = self._get_window_size(self.view, [0.6, 0.6])

        # presets
        self._debug = debug
        self._group_obj = group_obj

        # make gui items
        self.make_gui()

        if self._group_obj:
            self.on_plot_overlay()
        LOGGER.debug(f"Instantiated overlay editor in {report_time(t_start)}")

    @property
    def group_obj(self):
        """Get group object"""
        method, forced_kwargs = self._group_obj.get_metadata(["method", "overlay"], [None, {}])
        return method, self._group_obj, forced_kwargs

    def make_gui(self):
        """Make UI"""

        # make plot
        plot_panel = self.make_plot_panel(self)

        # make extra
        self.plot_settings = PanelOverlayViewerSettings(self, self.view)

        # pack elements
        main_sizer = wx.BoxSizer()
        main_sizer.Add(plot_panel, 1, wx.EXPAND, 0)
        main_sizer.Add(self.plot_settings, 0, wx.EXPAND, 0)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizer(main_sizer)
        self.SetSize(self._window_size)
        self.Layout()

        self.CenterOnParent()
        self.SetFocus()
        self.Show()

    def on_plot_overlay(self):
        """Overlay heatmap objects"""
        method, group_obj, forced_kwargs = self.group_obj

        plt_funcs = {
            "Butterfly (n=2)": self.on_plot_1d_butterfly,
            "Subtract (n=2)": self.on_plot_1d_subtract,
            "Overlay": self.on_plot_1d_overlay,
            "Waterfall": self.on_plot_1d_waterfall,
            "Mean": self.on_plot_2d_mean,
            "Standard Deviation": self.on_plot_2d_stddev,
            "Variance": self.on_plot_2d_variance,
            "RMSD": self.on_plot_2d_rmsd,
            "RMSF": self.on_plot_2d_rmsf,
            "RMSD Matrix": self.on_plot_2d_rmsd_matrix,
            "RMSD Dot": self.on_plot_2d_rmsd_dot,
            "Mask": self.on_plot_2d_mask,
            "Transparent": self.on_plot_2d_transparent,
            "Grid (2->1)": self.on_plot_2d_tto,
            "Grid (NxN)": self.on_plot_2d_nxn,
            "Side-by-side": self.on_plot_2d_side_by_side,
            "RGB": self.on_plot_2d_rgb,
        }

        plt_func = plt_funcs.get(method, None)
        if plt_func is None:
            LOGGER.error("Method not implemented yet")
            return

        # plot function
        kwargs = plt_func(group_obj, forced_kwargs)  # noqa

        # set metadata
        group_obj.set_metadata({"overlay": kwargs})


def _main():
    from origami.utils.screen import move_to_different_screen

    app = wx.App()
    ex = PanelOverlayViewer(None, None, debug=True)

    ex.Show()
    move_to_different_screen(ex)
    app.MainLoop()


if __name__ == "__main__":
    _main()
