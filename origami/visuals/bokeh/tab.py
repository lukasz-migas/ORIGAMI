"""Tab"""
# Standard library imports
from typing import List
from typing import Tuple
from typing import Union

# Third-party imports
from bokeh.models import Div
from bokeh.models import Panel
from bokeh.layouts import column

# Local imports
from origami.config.config import CONFIG
from origami.visuals.bokeh.layout import RowLayout
from origami.visuals.bokeh.layout import BaseLayout
from origami.visuals.bokeh.layout import GridLayout
from origami.visuals.bokeh.layout import ColumnLayout
from origami.visuals.bokeh.plot_base import PlotBase
from origami.visuals.bokeh.plot_base import PlotHeatmap
from origami.visuals.bokeh.plot_base import PlotScatter
from origami.visuals.bokeh.plot_base import PlotSpectrum
from origami.visuals.bokeh.plot_base import PlotHeatmapRGBA


class Tab(dict):
    """Tab container"""

    def __init__(self, name: str, default_layout: str = "col", auto_create: bool = True, *args):
        super(Tab, self).__init__(*args)
        self._name = name
        self._last_layout = None
        self._default_layout = default_layout
        self._auto_create = auto_create

    def __repr__(self):
        return f"{self.__class__.__name__}<layouts={len(self)}>"

    @property
    def name(self) -> str:
        """Return the name of the tab"""
        return self._name

    @property
    def n_layouts(self) -> int:
        """Return the number of layouts present in the Tab"""
        return len(self)

    @property
    def auto_create(self):
        """Flag to indicate whether layouts should be auto-created"""
        return self._auto_create

    @auto_create.setter
    def auto_create(self, value):
        self._auto_create = value

    @property
    def layout_list(self) -> List[str]:
        """Returns a list of objects that are contained within this instance of the tab"""
        out = []
        for key, layout in self.items():
            out.append(layout.layout_repr(self.name, key))
        return out

    def _get_unique_name(self, basename: str = "item"):
        """Get unique name for an item in specific tab. Names are made unique by adding #NUMBER+1 itself

        Parameters
        ----------
        basename : str
            base name of the unique name, default = 'item'

        Returns
        -------
        name : str
            new, unique name
        """
        i = 0
        while f"{basename} #{i}" in self:
            i += 1
        return f"{basename} #{i}"

    def _add(self, name: str, klass, basename: str) -> BaseLayout:
        """Add layout instance

        Parameters
        ----------
        name : str
            name of the layout - if one is not provided, a new, unique name will be created
        klass : Callable
            instance of BaseLayout that can be instantiated
        basename : str
            name on which to base the `name` on in case one was not provided
        """
        if name is None:
            name = self._get_unique_name(basename)
        self[name] = klass(name)
        self._last_layout = name
        return self[name]

    def render(self, remove_watermark: bool = False):
        """Render tab object"""
        tab_contents = []
        for _, layout in self.items():
            tab_contents.append(layout.render())

        if not remove_watermark:
            tab_contents.append(Div(text=str(CONFIG.watermark)))

        return Panel(child=column(children=tab_contents), title=self._name)

    def get_layout(self, name: Union[str, BaseLayout]) -> BaseLayout:
        """Get layout already present in the tab"""
        # if no layout is provided, assume the user wanted the last one
        if name is None and self._last_layout is not None:
            return self[self._last_layout]

        # the user can give an instance of the layout
        if isinstance(name, BaseLayout):
            return name

        # the user can give the string object
        if name not in self:
            if self._auto_create:
                return self.auto_add()
            raise KeyError(f"Layout `{name}` not in the Tab")
        return self[name]

    def get_plot_obj(self, plot_name: str, layout_name: str = None) -> PlotBase:
        """Get plot object stored in one of the layouts"""
        if layout_name is not None:
            return self.get_layout(layout_name).get(plot_name)
        for layout in self:
            if plot_name in layout:
                return layout[plot_name]
        raise KeyError("Could not retrieve plot object")

    def auto_add(self) -> BaseLayout:
        """Automatically add layout to the Tab"""
        return self.add_layout(None, self._default_layout)  # noqa

    def add_layout(self, name: str, layout: str):
        """Add layout based on the name"""
        if layout == "row":
            return self.add_row(name)
        elif layout in ["col", "column"]:
            return self.add_col(name)
        elif layout == "grid":
            return self.add_grid(name)

    def add_row(self, name: str = None) -> BaseLayout:
        """Add row the tab

        Parameters
        ----------
        name : str
            name of the row object

        Returns
        -------
        layout : RowLayout
            row layout
        """
        return self._add(name, RowLayout, "row")

    def add_col(self, name: str = None) -> BaseLayout:
        """Add row the tab

        Parameters
        ----------
        name : str
            name of the row object

        Returns
        -------
        layout : ColumnLayout
            column layout
        """
        return self._add(name, ColumnLayout, "col")

    def add_grid(self, name: str = None) -> BaseLayout:
        """Add row the tab

        Parameters
        ----------
        name : str
            name of the row object

        Returns
        -------
        layout : GridLayout
            grid layout
        """
        return self._add(name, GridLayout, "grid")

    def update_layout(self, tag: str, new_name: str = None, new_layout: str = None):
        """Change layout configuration, e.g. change from Row -> Column or update the title

        Parameters
        ----------
        tag : str
            tag by which it is possible to retrieve the layout
        new_name : str, optional
            new name of the layout
        new_layout : str, optional
            specify the new layout format. Value must be either: `row, column, grid`
        """
        # update name
        if new_name is not None:
            self[tag].name = new_name

        # update type
        if new_layout is not None:
            layout = self.get_layout(tag)
            if layout.LAYOUT != new_layout:
                # new class of the layout
                klass = {"row": RowLayout, "grid": GridLayout, "column": ColumnLayout, "col": ColumnLayout}[new_layout]
                layout_kwargs = layout.as_dict()
                self[tag] = klass(**layout_kwargs)

    def add_spectrum(
        self, data_obj, layout: Union[str, BaseLayout] = None, plot_name: str = None, forced_kwargs=None, **kwargs
    ) -> Tuple[PlotBase, BaseLayout]:
        """Add spectrum to the Tab"""
        layout = self.get_layout(layout)
        plot_obj = PlotSpectrum(**kwargs)
        plot_obj.plot(data_obj, forced_kwargs=forced_kwargs, **kwargs)
        layout.append(plot_obj, plot_name)
        return plot_obj, layout

    def add_scatter(
        self, data_obj, layout: Union[str, BaseLayout] = None, plot_name: str = None, forced_kwargs=None, **kwargs
    ) -> Tuple[PlotBase, BaseLayout]:
        """Add scatter to the Tab"""
        layout = self.get_layout(layout)
        plot_obj = PlotScatter(**kwargs)
        plot_obj.plot(data_obj, forced_kwargs=forced_kwargs, **kwargs)
        layout.append(plot_obj, plot_name)
        return plot_obj, layout

    def add_heatmap(
        self, data_obj, layout: Union[str, BaseLayout] = None, plot_name: str = None, forced_kwargs=None, **kwargs
    ) -> Tuple[PlotBase, BaseLayout]:
        """Add heatmap to the Tab"""
        layout = self.get_layout(layout)
        plot_obj = PlotHeatmap(**kwargs)
        plot_obj.plot(data_obj, forced_kwargs=forced_kwargs, **kwargs)
        layout.append(plot_obj, plot_name)
        return plot_obj, layout

    def add_heatmap_rgba(
        self, data_obj, layout: Union[str, BaseLayout] = None, plot_name: str = None, forced_kwargs=None, **kwargs
    ) -> Tuple[PlotBase, BaseLayout]:
        """Add RGBA heatmap to the Tab"""
        layout = self.get_layout(layout)
        plot_obj = PlotHeatmapRGBA(**kwargs)
        plot_obj.plot(data_obj, forced_kwargs=forced_kwargs, **kwargs)
        layout.append(plot_obj, plot_name)
        return plot_obj, layout
