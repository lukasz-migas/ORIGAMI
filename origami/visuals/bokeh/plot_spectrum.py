"""Spectrum based plots"""
# Third-party imports
from bokeh.models import ColumnDataSource

# Local imports
from origami.utils.secret import get_short_hash
from origami.visuals.bokeh.parser import get_param
from origami.visuals.bokeh.plot_base import PlotBase


class PlotSpectrum(PlotBase):
    """Base spectrum plot"""

    DATA_KEYS = ["x", "y"]
    DEFAULT_PLOT = "line"

    def __init__(self, *args, **kwargs):
        PlotBase.__init__(self, *args, **kwargs)
        self.PLOT_ID = get_short_hash()

    def get_source(self, data_obj):
        """Get data source that can be used by Bokeh to plot the data"""
        data = {"x": data_obj.x, "y": data_obj.y}
        self.validate_data(data)
        self.x_limit = data_obj.x_limit
        self.y_limit = data_obj.y_limit
        return ColumnDataSource(data)

    def _get_hover_kwargs(self):
        return {
            "show_arrow": True,
            "tooltips": [(f"{self.x_label}", "@x"), (f"{self.y_label}", "@y")],
            "mode": "vline",
            "line_policy": "next",
            # "names": [self.PLOT_ID],
        }

    def plot(self, data_obj=None, forced_kwargs=None, **kwargs):
        """Basic plotting method"""
        kwargs, _kwargs = self._pre_plot(data_obj, forced_kwargs, **kwargs)

        # add plot line
        self._plots[self.DEFAULT_PLOT] = self.figure.line(
            x="x",
            y="y",
            source=self._sources[self.DEFAULT_PLOT],
            name=self.PLOT_ID,
            muted_alpha=get_param("bokeh_legend_mute_alpha", **kwargs),
            line_dash=get_param("bokeh_line_style", **kwargs),
            line_width=get_param("bokeh_line_width", **kwargs),
            line_alpha=get_param("bokeh_line_alpha", **kwargs),
        )
        # add legend
        if kwargs.get("legend", False):
            self.add_legend(**kwargs)
        self._post_plot(**kwargs)

    def add_line(self, data_obj=None, forced_kwargs=None, **kwargs):
        """Add line to the plot"""
        source = self.get_source(data_obj)
        kwargs, _kwargs = self.parse_kwargs(self.BOKEH_KEYS, forced_kwargs=forced_kwargs, **kwargs)
        line = self.figure.line(x="x", y="y", source=source, **kwargs)
        self._sources[line.id] = source
        self._plots[line.id] = line


class PlotMultilineSpectrum(PlotBase):
    """Multi-line base class"""

    DATA_KEYS = ["xs", "ys"]
    DEFAULT_PLOT = "multiline"

    def __init__(self, *args, **kwargs):
        PlotBase.__init__(self, *args, **kwargs)
        self.PLOT_ID = get_short_hash()

    def get_source(self, data_obj):
        """Get data source that can be used by Bokeh to plot the data"""
        data = {"xs": data_obj.x, "ys": data_obj.ys}
        self.validate_data(data)
        self.x_limit = data_obj.x_limit
        self.y_limit = data_obj.y_limit
        return ColumnDataSource(data)

    def _get_hover_kwargs(self):
        return {
            "show_arrow": True,
            "tooltips": [(f"{self.x_label}", "$data_x"), (f"{self.y_label}", "$data_y")],
            "line_policy": "next",
        }

    def plot(self, data_obj=None, forced_kwargs=None, **kwargs):
        """Basic plotting method"""
        kwargs, _kwargs = self._pre_plot(data_obj, forced_kwargs, **kwargs)

        self._plots[self.DEFAULT_PLOT] = self.figure.multi_line(
            xs="xs", ys="ys", source=self._sources[self.DEFAULT_PLOT], name=self.PLOT_ID, **kwargs
        )
        # add legend
        if kwargs.get("legend", False):
            self.add_legend(**kwargs)
        self._post_plot(**kwargs)


class PlotScatter(PlotBase):
    """Scatter plot base"""

    DATA_KEYS = ["x", "y"]
    DEFAULT_PLOT = "scatter"

    def __init__(self, *args, plot_width=600, plot_height=600, **kwargs):
        PlotBase.__init__(self, *args, plot_width=plot_width, plot_height=plot_height, **kwargs)
        self.PLOT_ID = get_short_hash()

    def _get_hover_kwargs(self):
        return {
            "show_arrow": True,
            "tooltips": [(f"{self.x_label}", "@x"), (f"{self.y_label}", "@y")],
            "mode": "vline",
            # "names": [self.PLOT_ID],
        }

    def get_source(self, data_obj):
        """Get data source that can be used by Bokeh to plot the data"""
        data = {"x": data_obj.x, "y": data_obj.y}
        self.validate_data(data)
        self.x_limit = data_obj.x_limit
        self.y_limit = data_obj.y_limit
        return ColumnDataSource(data)

    def plot(self, data_obj=None, forced_kwargs=None, **kwargs):
        """Basic plotting method"""
        kwargs, _kwargs = self._pre_plot(data_obj, forced_kwargs, **kwargs)

        self._plots[self.DEFAULT_PLOT] = self.figure.scatter(
            x="x",
            y="y",
            source=self._sources[self.DEFAULT_PLOT],
            name=self.PLOT_ID,
            muted_alpha=get_param("bokeh_legend_mute_alpha", **kwargs),
            size=get_param("bokeh_scatter_size", **kwargs),
            marker=get_param("bokeh_scatter_marker", **kwargs),
            fill_alpha=get_param("bokeh_scatter_alpha", **kwargs),
            line_color=get_param("bokeh_scatter_edge_color", **kwargs),
            line_width=get_param("bokeh_scatter_edge_width", **kwargs),
        )
        # add legend
        if kwargs.get("legend", False):
            self.add_legend(**kwargs)
        self._post_plot(**kwargs)

    def add_line(self, data_obj=None, forced_kwargs=None, **kwargs):
        """Add line to the plot"""
        source = self.get_source(data_obj)
        kwargs, _kwargs = self.parse_kwargs(self.BOKEH_KEYS, forced_kwargs=forced_kwargs, **kwargs)
        line = self.figure.line(x="x", y="y", source=source, **kwargs)
        self._sources[line.id] = source
        self._plots[line.id] = line
