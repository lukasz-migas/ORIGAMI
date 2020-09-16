"""Layout to be used by individual pages to render HTML content"""
# Standard library imports
import math

# Third-party imports
from bokeh.layouts import row
from bokeh.layouts import column
from bokeh.layouts import layout
from bokeh.layouts import gridplot


class BaseLayout:
    """Base layout"""

    LAYOUT = None

    def __init__(self, name: str, plot_objects=None):
        self._name = name
        self._objects = []
        if isinstance(plot_objects, list):
            self._objects.extend(plot_objects)

    def __repr__(self):
        return f"{self.__class__.__name__}<name={self._name}>"

    @property
    def objects(self):
        """Returns properly arranged layout"""
        return [obj.render() for obj in self._objects]

    def append(self, plot_obj):
        """Add plot object to the `objects` container"""
        self._objects.append(plot_obj)

    def extend(self, *plot_obj):
        """Add plot object to the `objects` container"""
        self._objects.extend(plot_obj)

    def render(self):
        """Render layout so it can be displayed in the Document"""
        raise NotImplementedError("Must implement method")

    @staticmethod
    def _get_layout_kwargs():
        """Get keyword parameters to be used by the `LAYOUT` function"""
        return dict()


class RowLayout(BaseLayout):
    """Row layout"""

    def render(self):
        """Render layout so it can be displayed in the Document"""
        return row(self.objects, **self._get_layout_kwargs())


class ColumnLayout(BaseLayout):
    """Column layout"""

    def render(self):
        """Render layout so it can be displayed in the Document"""
        return column(self.objects, **self._get_layout_kwargs())


class LayoutLayout(BaseLayout):
    """Auto-grid layout"""

    @property
    def objects(self):
        """Returns properly arranged layout"""
        return self._objects

    def render(self):
        """Render layout so it can be displayed in the Document"""
        return layout(self.objects, **self._get_layout_kwargs())


class GridLayout(BaseLayout):
    """Grid layout"""

    def _get_layout_kwargs(self):
        n_cols = math.ceil(math.sqrt(len(self._objects)))
        return {"ncols": n_cols}

    def render(self):
        """Render layout so it can be displayed in the Document"""
        return gridplot(self.objects, **self._get_layout_kwargs())
