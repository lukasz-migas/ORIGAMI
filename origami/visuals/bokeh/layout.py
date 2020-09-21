"""Layout to be used by individual pages to render HTML content"""
# Standard library imports
import math
from typing import Dict

# Third-party imports
from bokeh.models import Div
from bokeh.layouts import row
from bokeh.layouts import column
from bokeh.layouts import layout
from bokeh.layouts import gridplot

# Local imports
from origami.utils.secret import get_short_hash


class BaseLayout(dict):
    """Base layout"""

    LAYOUT = None

    def __init__(
        self,
        name: str,
        plot_objects=None,
        div_title: str = None,
        div_header: str = None,
        div_footer: str = None,
        shared_tools: bool = True,
        n_cols: int = None,
        sizing_mode: str = "fixed",
        *args,
    ):
        super(BaseLayout, self).__init__(*args)
        self._name = name
        # self._objects = []
        self._div_title = div_title
        self._div_header = div_header
        self._div_footer = div_footer
        self._shared_tools = shared_tools
        self._n_cols = n_cols
        self._sizing_mode = sizing_mode
        if isinstance(plot_objects, dict):
            self.update(**plot_objects)

    def __repr__(self):
        return f"{self.__class__.__name__}<name={self._name} no. plots={self.n_plots}>"

    @property
    def name(self):
        """Returns name of the layout"""
        return self._name

    @name.setter
    def name(self, value: str):
        """Set title"""
        self._name = value

    @property
    def n_plots(self) -> int:
        """Returns the number of plots in the object"""
        return len(self)

    @property
    def objects(self):
        """Returns properly arranged layout"""
        return [obj.render() for obj in self.values()]

    @property
    def div_title(self):
        """Return title"""
        return Div(text="<b>%s</b>" % self._div_title)

    @property
    def div_title_str(self):
        """Return title as a string"""
        return self._div_title

    @div_title.setter
    def div_title(self, value: str):
        """Set title"""
        self._div_title = value

    @property
    def div_header(self):
        """Return header"""
        return Div(text=self._div_header)

    @property
    def div_header_str(self):
        """Return header as a string"""
        return self._div_header

    @div_header.setter
    def div_header(self, value: str):
        """Set title"""
        self._div_header = value

    @property
    def div_footer(self):
        """Return footer"""
        return Div(text=self._div_footer)

    @property
    def div_footer_str(self):
        """Return footer as a string"""
        return self._div_footer

    @div_footer.setter
    def div_footer(self, value: str):
        """Set title"""
        self._div_footer = value

    @property
    def n_cols(self):
        """Return footer"""
        return self._n_cols

    @n_cols.setter
    def n_cols(self, value: int):
        """Set number of columns"""
        self._n_cols = value

    @property
    def shared_tools(self):
        """Return shared tools"""
        return self._shared_tools

    @shared_tools.setter
    def shared_tools(self, value: bool):
        """Set number of columns"""
        self._shared_tools = value

    def as_dict(self) -> Dict:
        """Return layout in the form of a dictionary"""
        return {
            "name": self._name,
            "plot_objects": self.items(),
            "div_title": self._div_title,
            "div_header": self._div_header,
            "div_footer": self._div_footer,
            "shared_tools": self._shared_tools,
            "n_cols": self._n_cols,
            "sizing_mode": self._sizing_mode,
        }

    def list(self):
        """Creates a list of objects present in the layout"""

    def append(self, plot_obj, key=None):
        """Add plot object to the `objects` container"""
        if key is None:
            key = get_short_hash()
        self[key] = plot_obj

    def extend(self, **plot_obj: Dict):
        """Add plot object to the `objects` container"""
        self.update(**plot_obj)

    def render(self):
        """Render layout so it can be displayed in the Document"""
        return column([self.div_title, self.div_header, self._render(), self.div_footer])

    def _render(self):
        """Render layout so it can be displayed in the Document"""
        raise NotImplementedError("Must implement method")

    def _get_layout_kwargs(self):
        """Get keyword parameters to be used by the `LAYOUT` function"""
        return {"sizing_mode": self._sizing_mode}


class RowLayout(BaseLayout):
    """Row layout"""

    LAYOUT = "row"

    def _render(self):
        """Render layout so it can be displayed in the Document"""
        return row(self.objects, **self._get_layout_kwargs())


class ColumnLayout(BaseLayout):
    """Column layout"""

    LAYOUT = "column"

    def _render(self):
        """Render layout so it can be displayed in the Document"""
        return column(self.objects, **self._get_layout_kwargs())


class LayoutLayout(BaseLayout):
    """Auto-grid layout"""

    @property
    def objects(self):
        """Returns properly arranged layout"""
        return self.values()

    def _render(self):
        """Render layout so it can be displayed in the Document"""
        return layout(self.objects, **self._get_layout_kwargs())


class GridLayout(BaseLayout):
    """Grid layout"""

    LAYOUT = "grid"

    def _get_layout_kwargs(self):
        n_cols = self._n_cols
        if n_cols is None:
            n_cols = math.ceil(math.sqrt(self.n_plots))
        return {"ncols": n_cols, "toolbar_location": "above", "sizing_mode": self._sizing_mode}  # noqa

    def _render(self):
        """Render layout so it can be displayed in the Document"""
        return gridplot(self.objects, **self._get_layout_kwargs())
