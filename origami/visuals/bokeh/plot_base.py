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
from typing import Iterable

# Third-party imports
import numpy as np
from bokeh.models import Div
from bokeh.models import Band
from bokeh.models import Span
from bokeh.models import Range1d
from bokeh.models import ColorBar
from bokeh.models import LabelSet
from bokeh.models import HoverTool
from bokeh.models import BasicTicker
from bokeh.models import BoxAnnotation
from bokeh.models import ColumnDataSource
from bokeh.layouts import row
from bokeh.layouts import column
from bokeh.plotting import figure
from bokeh.io.export import get_layout_html

# Local imports
from origami.utils.secret import get_short_hash
from origami.config.config import CONFIG
from origami.visuals.bokeh.utilities import check_source
from origami.visuals.bokeh.utilities import convert_colormap_to_mapper

FORBIDDEN_KWARGS = [
    "div_title",
    "div_header",
    "div_footer",
    "output_dir",
    "x_limit",
    "y_limit",
    "plot_width",
    "plot_height",
    "FORCED_KWARGS",
]


def sanitize_kwargs(forbidden_kwargs: List[str], **kwargs):
    """Remove obviously incorrect values from the keyword arguments so they can be safely passed on to the plot"""
    keys = list(kwargs.keys())
    for key in keys:
        if key in forbidden_kwargs:
            del kwargs[key]
    return kwargs


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
        div_title=None,
        div_header=None,
        div_footer=None,
        output_dir: str = None,
        x_limit: str = None,
        y_limit: str = None,
        plot_width: int = 800,
        plot_height: int = 400,
        **kwargs,
    ):

        # data attributes
        self._plots = dict()
        self._sources = dict()
        self._annotations = dict()
        self._widgets = []
        self._output_dir = output_dir

        # layout attributes
        self._div_title = div_title
        self._div_header = div_header
        self._div_footer = div_footer

        # plot attributes
        self._x_label = x_label
        self._y_label = y_label
        self._x_limit = x_limit
        self._y_limit = y_limit
        self._plot_width = plot_width
        self._plot_height = plot_height

        self.FORCED_KWARGS.update(**kwargs.get("FORCED_KWARGS", dict()))
        self._data = dict()

        self.figure = figure(
            tools=self.TOOLS, active_drag=self.ACTIVE_DRAG, plot_width=self.plot_width, plot_height=self.plot_height
        )

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
        content = []
        if self._div_title:
            content.append(self.div_title)
        if self._div_header:
            content.append(self.div_header)
        content.append(self.figure)
        if self._div_footer:
            content.append(self.div_footer)
        layout = column(content)

        # if a list of widgets is present in the plot object, they should be rendered alongside the plot + annotations
        if len(self._widgets):
            layout = row(layout, column(self._widgets))

        return layout

    @property
    def plot_width(self):
        """Plot width of the figure"""
        return self._plot_width

    @plot_width.setter
    def plot_width(self, value):
        """Set plot width of the figure"""
        self._plot_width = value
        self.figure.plot_width = value

    @property
    def plot_height(self):
        """Plot height of the figure"""
        return self._plot_height

    @plot_height.setter
    def plot_height(self, value):
        """Set plot height of the figure"""
        self._plot_height = value
        self.figure.plot_height = value

    @property
    def x_limit(self):
        """Set x-limit"""
        return self._x_limit

    @x_limit.setter
    def x_limit(self, value):
        self._x_limit = value
        self.figure.x_range = Range1d(*value)

    @property
    def y_limit(self):
        """Get y-limit"""
        return self._x_limit

    @y_limit.setter
    def y_limit(self, value):
        self._y_limit = value
        self.figure.y_range = Range1d(*value)

    @abstractmethod
    def plot(self, data_obj=None, forced_kwargs=None, **kwargs):
        """Method responsible for plotting"""
        raise NotImplementedError("Must implement method")

    def render(self):
        """HTML render"""
        # TODO: add support for widgets
        return self.layout

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
        kwargs = sanitize_kwargs(FORBIDDEN_KWARGS, **kwargs)
        return kwargs, copy(kwargs)

    def validate_data(self, data: Dict):
        """Validate data source to ensure necessary keys have been added"""
        sizes = []
        for key in self.DATA_KEYS:
            if key not in data:
                raise ValueError(f"Missing key `{key}` in the data source")
            sizes.append(len(data[key]))
        if len(set(sizes)) > 1:
            raise ValueError("Input sizes are inconsistent")

    def get_source(self, data_obj):
        """Get data source that can be used by Bokeh to plot the data"""
        raise NotImplementedError("Must implement method")

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

    def _get_hover_kwargs(self) -> Dict:
        return {}

    def set_hover_tool(self):
        """Return hover tool that is specialized for the current plot"""
        hover_kwargs = self._get_hover_kwargs()
        if hover_kwargs:
            self._plots["hover"] = HoverTool(**hover_kwargs)
            self.figure.add_tools(self._plots["hover"])
            return self._plots["hover"]

    def set_plot_labels(self, data_obj):
        """Set labels"""
        self.x_label = data_obj.x_label
        self.y_label = data_obj.y_label

    def add_widgets(self, widget_list: List[str], widget_width: int = 250):
        """Add widgets to the plot object"""
        from origami.visuals.bokeh.widgets import add_widgets

        widgets = add_widgets(self, widget_list, widget_width)
        self._widgets.extend(widgets)

    def add_events(self, event_list: List[str]):
        """Add events to the plot object"""
        from origami.visuals.bokeh.widgets import add_events

        add_events(self, event_list)

    def add_tools(self, tool_list: str):
        """Add tools to the plot object"""

    def get_annotation(self, annotation_type: str):
        """Retrieve annotation of specified type"""
        annotations = []
        for value in self._annotations.values():
            if value[-1] == annotation_type:
                annotations.append(value[0])
        return annotations

    def get_glyph(self, glyph_type):
        """Retrieve glyphs of specified type"""
        glyphs = []
        for value in self._plots.values():
            if hasattr(value, "glyph"):
                if isinstance(value.glyph, glyph_type):
                    glyphs.append(value)
            else:
                if isinstance(value, glyph_type):
                    glyphs.append(value)
        return glyphs

    def add_box(self, data, **kwargs):
        """Add box annotation to the plot"""
        box = BoxAnnotation(**data, **kwargs)
        self.figure.add_layout(box)
        self._annotations[box.id] = (box, data, "BoxAnnotation")

    def add_labels(self, data: Dict, **kwargs):
        """Add multiple labels to the plot"""
        source = check_source(ColumnDataSource(data), ["x", "y", "text"])
        self._add_labels(source, **kwargs)

    def _add_labels(self, source, **kwargs):
        """Add multiple labels to the plot"""
        labels = LabelSet(x="x", y="y", text="text", source=source, **kwargs)
        self.figure.add_layout(labels)
        self._annotations[labels.id] = (labels, source, "LabelSet")

    def add_band(self, data: Dict, **kwargs):
        """Add band to the plot area"""
        source = check_source(ColumnDataSource(data), ["base", "lower", "upper"])
        self._add_band(source, **kwargs)

    def _add_band(self, source, **kwargs):
        """Add band to the plot"""
        band = Band(
            base="base", lower="lower", upper="upper", source=source, level=kwargs.get("level", "underlay"), **kwargs
        )
        self.figure.add_layout(band)
        self._annotations[band.id] = (band, source, "Band")

    def add_span(self, data, **kwargs):
        """Add span to the plot"""
        check_source(data, ["location", "dimension"])
        location = data["location"]
        if not isinstance(location, Iterable):
            location = [location]
        if data["dimension"] not in ["width", "height"]:
            raise ValueError("Dimension should be specified as `width` or `height`")

        for loc in location:
            span = Span(location=loc, dimension=data["dimension"], **kwargs)
            self.figure.add_layout(span)
            self._annotations[span.id] = (span, dict(location=loc, dimension=data["dimension"]), "Span")


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
        self.set_plot_labels(data_obj)
        self._sources[self.DEFAULT_PLOT] = self.get_source(data_obj)
        kwargs, _kwargs = self.parse_kwargs(self.BOKEH_KEYS, forced_kwargs=forced_kwargs, **kwargs)

        self._plots[self.DEFAULT_PLOT] = self.figure.line(
            x="x", y="y", source=self._sources[self.DEFAULT_PLOT], name=self.PLOT_ID, **kwargs
        )

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
        self.set_plot_labels(data_obj)
        self._sources[self.DEFAULT_PLOT] = self.get_source(data_obj)
        kwargs, _kwargs = self.parse_kwargs(self.BOKEH_KEYS, forced_kwargs=forced_kwargs, **kwargs)

        self._plots[self.DEFAULT_PLOT] = self.figure.multi_line(
            xs="xs", ys="ys", source=self._sources[self.DEFAULT_PLOT], name=self.PLOT_ID, **kwargs
        )


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
        self.set_plot_labels(data_obj)
        self._sources[self.DEFAULT_PLOT] = self.get_source(data_obj)
        kwargs, _kwargs = self.parse_kwargs(self.BOKEH_KEYS, forced_kwargs=forced_kwargs, **kwargs)

        self._plots[self.DEFAULT_PLOT] = self.figure.scatter(
            x="x", y="y", source=self._sources[self.DEFAULT_PLOT], name=self.PLOT_ID, **kwargs
        )

    def add_line(self, data_obj=None, forced_kwargs=None, **kwargs):
        """Add line to the plot"""
        source = self.get_source(data_obj)
        kwargs, _kwargs = self.parse_kwargs(self.BOKEH_KEYS, forced_kwargs=forced_kwargs, **kwargs)
        line = self.figure.line(x="x", y="y", source=source, **kwargs)
        self._sources[line.id] = source
        self._plots[line.id] = line


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
        self.set_plot_labels(data_obj)
        self._sources[self.DEFAULT_PLOT] = self.get_source(data_obj)
        kwargs, _kwargs = self.parse_kwargs(self.BOKEH_KEYS, forced_kwargs=forced_kwargs, **kwargs)

        self._data["palette"], self._data["colormapper"] = self.get_colormapper(data_obj.array, **kwargs)
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

    @staticmethod
    def get_colormapper(array: np.ndarray, colormap: str = "viridis", **kwargs):
        """Get color palette and color mapper"""
        return convert_colormap_to_mapper(array, colormap, vmin=kwargs.pop("vmin", None), vmax=kwargs.pop("vmax", None))

    def set_colorbar(self):
        """Add colorbar to the plot area"""
        self._plots["colorbar"] = ColorBar(
            color_mapper=self._data["colormapper"],
            ticker=BasicTicker(),
            location=(0, 0),
            major_label_text_font_size="10pt",
            label_standoff=8,
        )
        self.figure.add_layout(self._plots["colorbar"], "right")


class PlotHeatmapRGBA(PlotHeatmap):
    """Base RGBA heatmap plot"""

    DEFAULT_PLOT = "rgba"

    def __init__(self, *args, plot_width=600, plot_height=600, **kwargs):
        PlotBase.__init__(self, *args, plot_width=plot_width, plot_height=plot_height, **kwargs)
        self.PLOT_ID = get_short_hash()

    def plot(self, data_obj=None, forced_kwargs=None, **kwargs):
        """Basic plotting method"""
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
