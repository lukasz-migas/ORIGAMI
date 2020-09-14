"""Layout to be used by individual pages to render HTML content"""
# Third-party imports
from bokeh.layouts import row
from bokeh.layouts import column
from bokeh.layouts import layout
from bokeh.layouts import gridplot


class BaseLayout:
    """Base layout"""

    LAYOUT = None

    def __init__(self, plot_objects):
        self._objects = []
        if isinstance(plot_objects, list):
            self._objects.extend(plot_objects)

    @property
    def objects(self):
        """Returns properly arranged layout"""
        return self._objects

    def add(self, plot_obj):
        """Add plot object to the `objects` container"""
        self._objects.append(plot_obj)

    def render(self):
        """Render layout so it can be displayed in the Document"""
        self.LAYOUT(children=self._objects, **self._get_layout_kwargs())

    @staticmethod
    def _get_layout_kwargs():
        """Get keyword parameters to be used by the `LAYOUT` function"""
        return dict()


class RowLayout(BaseLayout):
    """Row layout"""

    LAYOUT = row


class ColumnLayout(BaseLayout):
    """Column layout"""

    LAYOUT = column


class LayoutLayout(BaseLayout):
    """Auto-grid layout"""

    LAYOUT = layout

    @property
    def objects(self):
        """Returns properly arranged layout"""
        return self._objects


class GridLayout(BaseLayout):
    """Grid layout"""

    LAYOUT = gridplot

    @property
    def objects(self):
        """Returns properly arranged layout"""
        return self._objects
