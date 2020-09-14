"""Base plot for Bokeh plotting functionality"""
# Standard library imports
import os
import webbrowser
from abc import abstractmethod
from copy import copy
from typing import Dict
from typing import List
from typing import Tuple
from typing import Union

# Third-party imports
from bokeh.models import Div
from bokeh.models import ColumnDataSource
from bokeh.layouts import column
from bokeh.plotting import figure
from bokeh.io.export import get_layout_html

# Local imports
from origami.utils.secret import get_short_hash
from origami.config.config import CONFIG


class PlotBase:
    """Base class for all other Bokeh plots"""

    DEFAULT_PLOT = None
    BOKEH_KEYS = []
    FORCED_KWARGS = {}
    DATA_KEYS = []
    PLOT_ID = None
    TOOLS = "pan, xpan, xbox_zoom, box_zoom, crosshair, reset"
    ACTIVE_DRAG = "xbox_zoom"

    def __init__(
        self,
        x_label: str = "",
        y_label: str = "",
        title=None,
        header=None,
        footer=None,
        output_dir: str = None,
        **kwargs,
    ):

        # data attributes
        self._plots = dict()
        self._sources = dict()
        self._output_dir = output_dir

        # layout attributes
        self._div_title = title
        self._div_header = header
        self._div_footer = footer

        # plot attributes
        self._x_label = x_label
        self._y_label = y_label

        self.FORCED_KWARGS.update(**kwargs.get("FORCED_KWARGS", dict()))
        self._data = dict()
        self._plt_kwargs = dict()

        self.figure = figure(tools=self.TOOLS, active_drag=self.ACTIVE_DRAG)

    @property
    def output_dir(self):
        """Return output directory"""
        output_dir = self._output_dir
        if output_dir is None:
            output_dir = os.getcwd()
        return output_dir

    @property
    def x_label(self):
        """Return x-axis label"""
        return self._x_label

    @x_label.setter
    def x_label(self, value):
        """Set x-axis label"""
        self._x_label = value
        self.figure.xaxis.axis_label = value

    @property
    def y_label(self):
        """Return y-axis label"""
        return self._y_label

    @y_label.setter
    def y_label(self, value):
        """Set y-axis label"""
        self._y_label = value
        self.figure.yaxis.axis_label = value

    @property
    def div_title(self):
        """Return title"""
        return Div(text="<b>%s</b>" % self._div_title)

    @div_title.setter
    def div_title(self, value):
        """Set title"""
        self._div_title = value

    @property
    def div_header(self):
        """Return header"""
        return Div(text=self._div_header)

    @div_header.setter
    def div_header(self, value):
        """Set title"""
        self._div_header = value

    @property
    def div_footer(self):
        """Return footer"""
        return Div(text=self._div_footer)

    @div_footer.setter
    def div_footer(self, value):
        """Set title"""
        self._div_footer = value

    @property
    def layout(self):
        """Setup plot layout

        Each plot consists of three elements:
        TITLE DIV - title of the plot
        FIGURE - Bokeh Plot instance
        ANNOTATION DIV - any comments/annotations provided for particular plot

        --- to be added in the future ---
        TOOLS - interactive tools added for improved visualisation and control purposes
        """
        return column(self.div_title, self.div_header, self.figure, self.div_footer)

    @property
    def plot_width(self):
        """Plot width of the figure"""
        return self.figure.plot_width

    @plot_width.setter
    def plot_width(self, value):
        """Set plot width of the figure"""
        self.figure.plot_width = value

    @property
    def plot_height(self):
        """Plot height of the figure"""
        return self.figure.plot_height

    @plot_height.setter
    def plot_height(self, value):
        """Set plot height of the figure"""
        self.figure.plot_height = value

    @abstractmethod
    def plot(self, data_obj=None, forced_kwargs=None, **kwargs):
        """Method responsible for plotting"""
        raise NotImplementedError("Must implement method")

    def link_axes(self, x_range=None, y_range=None):
        """Link x- and/or y-axis ranges to another plot"""
        if x_range:
            if isinstance(x_range, PlotBase):
                x_range = x_range.figure.x_range
            self.figure.x_range = x_range
        if y_range:
            if isinstance(y_range, PlotBase):
                y_range = x_range.figure.y_range
            self.figure.y_range = y_range

    def parse_kwargs(
        self, extra_bokeh_keys: Union[str, List[str]], mpl_kwargs=None, forced_kwargs=None, **kwargs
    ) -> Tuple[Dict, Dict]:
        """Parse keyword parameters to be consumed by the plotting function

        Keyword parameters are collected in the order:
        1. User provided parameters in `kwargs`
        2. kwargs is updated by parameters from CONFIG
        3. kwargs is updated by `mpl_kwargs`
        4. kwargs is updated by `self.FORCED_KWARGS`
        5. kwargs is updated by `forced_kwargs`
        """
        # get config kwargs
        mpl_keys = copy(self.BOKEH_KEYS)
        if extra_bokeh_keys:
            if isinstance(extra_bokeh_keys, str):
                mpl_keys.append(extra_bokeh_keys)
            elif isinstance(extra_bokeh_keys, list):
                mpl_keys.extend(extra_bokeh_keys)
        kwargs.update(**CONFIG.get_bokeh_parameters(mpl_keys))  # noqa

        # update by `mpl_kwargs`
        if isinstance(mpl_kwargs, dict):
            kwargs.update(**mpl_kwargs)

        # update by default `FORCED_KWARGS`
        kwargs.update(**self.FORCED_KWARGS)

        # update by default `forced_kwargs`
        if isinstance(forced_kwargs, dict):
            kwargs.update(**forced_kwargs)
        return kwargs, copy(kwargs)

    def validate_data(self, data: Dict):
        """Validate data source to ensure necessary keys have been added"""
        sizes = []
        for key in self.DATA_KEYS:
            if key not in data:
                raise ValueError(f"Missing key `{key}` in the data source")
            sizes.append(data[key].shape)
        if len(set(sizes)) > 1:
            raise ValueError("Input sizes are inconsistent")

    def get_source(self, data_obj):
        """Get data source that can be used by Bokeh to plot the data"""

    def save(self, filepath=None, show: bool = True):
        """Save Bokeh plot as HTML file

        Parameters
        ----------
        filepath : str
            path where to save the HTML document
        show : bool
            if 'True', newly generated document will be shown in the browser
        """

        if filepath is None:
            filepath = os.path.join(self.output_dir, self.PLOT_ID + ".html")

        html_str = get_layout_html(self.layout)
        with open(filepath, "wb") as f_ptr:
            f_ptr.write(html_str.encode("utf-8"))

        # open figure in browser
        if show:
            webbrowser.open_new_tab(filepath)


class PlotSpectrum(PlotBase):
    """Base spectrum plot"""

    DATA_KEYS = ["x", "y"]
    DEFAULT_PLOT = "line"

    def __init__(self, *args, **kwargs):
        super(PlotSpectrum, self).__init__(*args, **kwargs)
        self.PLOT_ID = get_short_hash()

    def get_source(self, data_obj):
        """Get data source that can be used by Bokeh to plot the data"""
        data = {"x": data_obj.x, "y": data_obj.y}
        self.x_label = data_obj.x_label
        self.y_label = data_obj.y_label
        self.validate_data(data)
        return ColumnDataSource(data)

    def plot(self, data_obj=None, forced_kwargs=None, **kwargs):
        """Basic plotting method"""
        self._sources[self.DEFAULT_PLOT] = self.get_source(data_obj)
        kwargs, _kwargs = self.parse_kwargs(self.BOKEH_KEYS, forced_kwargs=forced_kwargs, **kwargs)

        self._plots[self.DEFAULT_PLOT] = self.figure.line(
            x="x", y="y", source=self._sources[self.DEFAULT_PLOT], name=self.PLOT_ID, **kwargs
        )
