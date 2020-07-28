"""View heatmap objects in 3d"""
# Standard library imports
import logging

# Third-party imports
import wx

# Local imports
from origami.utils.secret import get_short_hash
from origami.config.config import CONFIG
from origami.visuals.mpl.plot_heatmap_3d import PlotHeatmap3d
from origami.gui_elements.views.view_base import ViewBase

LOGGER = logging.getLogger(__name__)


class ViewHeatmap3d(ViewBase):
    """Viewer class for heatmap-based objects"""

    DATA_KEYS = ("array", "x", "y")
    MPL_KEYS = ["2D"]
    UPDATE_STYLES = (
        "opacity",
        "clim",
        "colormap",
        "font",
        "tick",
        "color.axis",
        "color.background",
        "margin",
        "margin.x",
        "margin.y",
        "margin.z",
    )
    NAME = get_short_hash()
    SUPPORTED_FILE_FORMATS = ("png", "jpeg", "tiff", "pdf")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.panel, self.figure, self.sizer = self.make_panel()

        # set args
        self.z_label = "Intensity"

    def _update(self):
        """Update plot with current data"""
        try:
            self.update(self._data["x"], self._data["y"], **self._plt_kwargs)
        except KeyError:
            pass

    def make_panel(self):
        """Initialize plot panel"""
        plot_panel = wx.Panel(self.parent)
        plot_window = PlotHeatmap3d(plot_panel)  # , plot_id=self.NAME)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(plot_window, 1, wx.EXPAND)
        plot_panel.SetSizer(sizer)
        sizer.Fit(plot_panel)

        return plot_panel, plot_window, sizer

    def clear(self):
        """Clear canvas"""
        try:
            self.figure.canvas.clear()
        except RuntimeError:
            pass

    @staticmethod
    def check_input(x, y, array, obj):
        """Check user-input"""
        if x is None and y is None and array is None and obj is None:
            raise ValueError("You must provide the x/y/array values or container object")
        if x is None and y is None and array is None and obj is not None:
            x = obj.x
            y = obj.y
            array = obj.array
        return x, y, array

    def check_kwargs(self, **kwargs):
        """Check kwargs"""
        if "allow_extraction" not in kwargs:
            kwargs["allow_extraction"] = self._allow_extraction
        return kwargs

    def plot(self, x=None, y=None, array=None, obj=None, **kwargs):
        """Simple line plot"""
        # try to update plot first, as it can be quicker
        self.set_document(obj, **kwargs)
        self.set_labels(obj, **kwargs)

        kwargs.update(**CONFIG.get_mpl_parameters(self.MPL_KEYS))
        kwargs = self.check_kwargs(**kwargs)

        try:
            self.update(x, y, array, obj, **kwargs)
        except AttributeError:
            x, y, array = self.check_input(x, y, array, obj)
            self.figure.clear()
            self.figure.canvas.plot_3d_surface(
                x, y, array, x_label=self.x_label, y_label=self.y_label, z_label=self.z_label, **kwargs
            )

        # set data
        self._data.update(x=x, y=y, array=array, obj=obj)
        self._plt_kwargs = kwargs
        LOGGER.debug("Plotted data")

    def update(self, x=None, y=None, array=None, obj=None, **kwargs):
        """Update plot without having to clear it"""
        self.set_document(obj, **kwargs)
        self.set_labels(obj, **kwargs)

        # update plot
        x, y, array = self.check_input(x, y, array, obj)
        self.figure.canvas.plot_3d_update(x, y, array, self.x_label, self.y_label, self.z_label, **kwargs)
        # self.figure.repaint()

        # set data
        self._data.update(x=x, y=y, array=array, obj=obj)
        self._plt_kwargs = kwargs
        LOGGER.debug("Updated plot data")

    def replot(self, **kwargs):
        """Replot the current plot"""

    def update_style(self, name: str):
        """Update style of the plot"""
        if name not in self.UPDATE_STYLES:
            raise ValueError(f"Not sure how to handle `{name}`")

        if not self.figure.can_update():
            raise AttributeError("Plot has not been generated yet")

        if name == "opacity":
            self.figure.canvas.set_opacity(CONFIG.heatmap_3d_opacity)
        elif name == "clim":
            self.figure.canvas.set_clim((CONFIG.heatmap_3d_clim_min, CONFIG.heatmap_3d_clim_max))
        elif name == "colormap":
            self.figure.canvas.set_colormap(CONFIG.heatmap_3d_colormap)
        elif name == "font":
            self.figure.canvas.set_axis_font_size(CONFIG.heatmap_3d_axis_font_size)
        elif name == "tick":
            self.figure.canvas.set_axis_tick_size(CONFIG.heatmap_3d_axis_tick_size)
        elif name == "color.axis":
            self.figure.canvas.set_axis_color(CONFIG.heatmap_3d_axis_color)
        elif name == "color.background":
            self.figure.canvas.set_background(CONFIG.heatmap_3d_background_color)
        elif name == "margin":
            self.figure.canvas.set_axis_label_margin(dimensions=("x", "y", "z"))
        elif name == "margin.x":
            self.figure.canvas.set_axis_label_margin(dimensions=("x",))
        elif name == "margin.y":
            self.figure.canvas.set_axis_label_margin(dimensions=("y",))
        elif name == "margin.z":
            self.figure.canvas.set_axis_label_margin(dimensions=("z",))
