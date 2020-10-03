"""Heatmap based plots"""
# Third-party imports
import numpy as np
from bokeh.models import ColumnDataSource

# Local imports
from origami.utils.secret import get_short_hash
from origami.visuals.bokeh.parser import get_param
from origami.visuals.bokeh.plot_base import PlotBase
from origami.visuals.bokeh.utilities import convert_colormap_to_mapper


class PlotHeatmap(PlotBase):
    """Base heatmap plot"""

    DATA_KEYS = ["x", "y", "image", "dw", "dh"]
    DEFAULT_PLOT = "heatmap"
    TOOLS = "pan, box_zoom, crosshair, reset"
    ACTIVE_DRAG = "box_zoom"

    def __init__(self, *args, plot_width=600, plot_height=600, **kwargs):
        PlotBase.__init__(self, *args, plot_width=plot_width, plot_height=plot_height, **kwargs)
        self.PLOT_ID = get_short_hash()

    def get_source(self, data_obj):
        """Get data source that can be used by Bokeh to plot the data"""
        data = {
            "x": [data_obj.x[0]],
            "dw": [data_obj.x[-1]],
            "y": [data_obj.y[0]],
            "dh": [data_obj.y[-1]],
            "image": [data_obj.array],
        }
        self.validate_data(data)
        self.x_limit = data_obj.x_limit
        self.y_limit = data_obj.y_limit
        return ColumnDataSource(data)

    def _get_hover_kwargs(self):
        return {"show_arrow": True, "tooltips": [("x, y", "$x{0.00}, $y{0.00}"), ("intensity", "@image")]}

    def plot(self, data_obj=None, forced_kwargs=None, **kwargs):
        """Basic plotting method"""
        kwargs, _kwargs = self._pre_plot(data_obj, forced_kwargs, **kwargs)

        # set colorbar
        self._data["palette"], self._data["colormapper"] = self.get_colormapper(data_obj.array, **kwargs)

        # make plot
        self._plots[self.DEFAULT_PLOT] = self.figure.image(
            x="x",
            y="y",
            dw="dw",
            dh="dh",
            image="image",
            source=self._sources[self.DEFAULT_PLOT],
            name=self.PLOT_ID,
            palette=self._data["palette"],
        )
        self._plots[self.DEFAULT_PLOT].glyph.color_mapper = self._data["colormapper"]
        if kwargs.get("colorbar", False):
            self.add_colorbar(**kwargs)
        self._post_plot(**kwargs)

    @staticmethod
    def get_colormapper(array: np.ndarray, **kwargs):
        """Get color palette and color mapper"""
        colormap: str = get_param("bokeh_heatmap_colormap", **kwargs)
        return convert_colormap_to_mapper(array, colormap, vmin=kwargs.pop("vmin", None), vmax=kwargs.pop("vmax", None))

    def add_colorbar(self, array=None, **kwargs):
        """Add colorbar to the plot area"""
        from origami.visuals.bokeh.utilities import _add_colorbar

        if array is None:
            array = self._sources["heatmap"].data["image"][0]
        self._plots["colorbar"] = _add_colorbar(self.figure, array, self._data["colormapper"], **kwargs)


class PlotHeatmapRGBA(PlotHeatmap):
    """Base RGBA heatmap plot"""

    DEFAULT_PLOT = "rgba"

    def __init__(self, *args, plot_width=600, plot_height=600, **kwargs):
        PlotBase.__init__(self, *args, plot_width=plot_width, plot_height=plot_height, **kwargs)
        self.PLOT_ID = get_short_hash()

    def plot(self, data_obj=None, forced_kwargs=None, **kwargs):
        """Basic plotting method"""
        kwargs, _kwargs = self._pre_plot(data_obj, forced_kwargs, **kwargs)
        self._sources[self.DEFAULT_PLOT] = self.get_source(data_obj)
        kwargs, _kwargs = self.parse_kwargs(self.BOKEH_KEYS, forced_kwargs=forced_kwargs, **kwargs)

        self._plots[self.DEFAULT_PLOT] = self.figure.image_rgba(
            x="x",
            y="y",
            dw="dw",
            dh="dh",
            image="image",
            source=self._sources[self.DEFAULT_PLOT],
            name=self.PLOT_ID,
            **kwargs,
        )
        self._post_plot(**kwargs)
