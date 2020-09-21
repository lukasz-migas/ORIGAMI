"""Bokeh Document Store"""
# Standard library imports
import os
import webbrowser
from typing import List
from typing import Tuple
from typing import Union

# Third-party imports
from bokeh.io import save
from bokeh.io import show
from bokeh.models import Tabs
from bokeh.models import Panel
from bokeh.layouts import column

# Local imports
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
            out.append(f"Tab={self.name}; Name={layout.name}; Tag={key}")
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

    def render(self):
        """Render tab object"""
        tab_contents = []
        for name, layout in self.items():
            tab_contents.append(layout.render())
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

    def change_layout(self, name: str, new_name: str = None, new_layout: str = None):
        """Change layout configuration, e.g. change from Row -> Column or update the title"""

        # update name
        if new_name is not None:
            layout = self.pop(name)
            self[new_name] = layout
            name = new_name

        # update type
        if new_layout is not None:
            layout = self.get_layout(name)
            if layout.LAYOUT != new_layout:
                layout_kwargs = layout.as_dict()
                if new_layout == "row":
                    layout = RowLayout(**layout_kwargs)
                elif new_layout == "grid":
                    layout = GridLayout(**layout_kwargs)
                else:
                    layout = ColumnLayout(**layout_kwargs)
                self[name] = layout

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


class PlotStore:
    """Bokeh document responsible for rendering of the various plots and widgets"""

    def __init__(self, output_dir: str = None, filename: str = "figure-store.html", title: str = "Document Store"):
        self._output_dir = output_dir
        self._filename = filename
        self._title = title

        self._tabs = {}

    def __repr__(self):
        return f"{self.__class__.__name__} <tabs={len(self._tabs)}>"

    def __contains__(self, item):
        if isinstance(item, str):
            return item in self._tabs
        return item in self._tabs.values()

    @property
    def output_dir(self) -> str:
        """Return output directory"""
        output_dir = self._output_dir
        if output_dir is None:
            output_dir = os.getcwd()
        return output_dir

    @property
    def filepath(self) -> str:
        """Returns full path including the filename"""
        filepath = os.path.join(self.output_dir, self._filename)
        if not filepath.endswith(".html"):
            filepath += ".html"
        return filepath

    @property
    def tab_names(self):
        """Get list of tab names"""
        return list(self._tabs.keys())

    @property
    def layout_list(self) -> List[str]:
        """Returns a list of objects that are contained within this instance of the tab"""
        out = []
        for tab in self._tabs.values():
            out.extend(tab.layout_list)
        return out

    @property
    def n_tabs(self) -> int:
        """Return the number of tabs present in the Store"""
        return len(self._tabs)

    def show(self, tab_names=None, always_as_tabs=True):
        """Return HTML representation of the document"""
        return show(self.get_layout(tab_names, always_as_tabs))

    def save(self, filepath=None, display=True, **kwargs) -> str:
        """Save Bokeh document as HTML file

        Parameters
        ----------
        filepath : str
            path where to save the HTML document
        display : bool
            if 'True', newly generated document will be shown in the browser
        kwargs :
            parameters to be passed on to the 'get_layout' function
        """

        if filepath is None:
            filepath = self.filepath

        save(self.get_layout(**kwargs), filepath, title=self._title)

        # open figure in browser
        if display:
            webbrowser.open_new_tab(filepath)
        return filepath

    def get_layout(self, tab_names=None, always_as_tabs=True):
        """Return fully ordered Bokeh document which can be visualised (using 'show' command) or exported as HTML

        Parameters
        ----------
        tab_names : list
            list of tab names which must be present in the `tabs` container
        always_as_tabs : bool
            if 'True', the resultant HTML document will contain 'Tabs' even if only one tab is present

        Returns
        -------
        tabs : Tabs
            Tabs container

        """
        # user can specify which tabs they would like to export as HTML document. If 'tab_names' was not specified,
        # we will use all tabs in the exported document
        if tab_names is None:
            tab_names = self.tab_names
        else:
            # let's check if the user supplied single tab name using strings...
            if isinstance(tab_names, str):
                tab_names = [tab_names]

        # check that each tab name is actually present in the tab store
        if not all([tab_name in self._tabs for tab_name in tab_names]):
            raise ValueError("Some of the specified tab names are not present in the figure store")

        # initialize panel store
        panels = []
        # iterate over each tab
        for tab_name in tab_names:
            tab = self._tabs[tab_name]
            panel = tab.render()
            if panel is None:
                continue
            panels.append(panel)

        # if the 'always_as_tabs' toggle is disabled and only one tab is present, the returned object will be column
        # element
        if len(panels) == 1 and not always_as_tabs:
            return panels[0].child

        return Tabs(tabs=panels)

    def add_tab(self, tab_name: str, force: bool = False):
        """Add new tab"""
        if tab_name in self._tabs and not force:
            raise ValueError("Tab already exists - please use `force=True` to reset it.")
        self._tabs[tab_name] = Tab(tab_name)
        return self._tabs[tab_name]

    def add_tabs(self, tab_names: List[str], force=False):
        """Add multiple new tabs to the document

        Parameters
        ----------
        tab_names : List[str]
            list of tab names
        force : bool, optional
            if tab with name `tab_name` already exists and `reset` is set to `True` no exception will be thrown

        Raises
        ------
        ValueError
            raised if `tab_name` already present in the `self.tabs` container. It will not be thrown if `force` is set
            to `True
        """
        for tab_name in tab_names:
            self.add_tab(tab_name, force)

    def remove_tab(self, tab_name: str):
        """Remove tab from the PlotStore"""
        del self._tabs[tab_name]

    def get_tab(self, tab: str, auto_add_tab: bool = True):
        """Get tab"""
        if isinstance(tab, Tab):
            return tab
        if tab not in self._tabs:
            if auto_add_tab:
                return self.add_tab(tab)
            raise KeyError(f"Tab `{tab}` is not present in the Document")
        return self._tabs[tab]

    def add_row(self, tab: Union[str, Tab], name: str = None, auto_add_tab: bool = True) -> Tuple[Tab, RowLayout]:
        """Add row to tab"""
        tab = self.get_tab(tab, auto_add_tab)
        return tab, tab.add_row(name)

    def add_col(self, tab: Union[str, Tab], name: str = None, auto_add_tab: bool = True) -> Tuple[Tab, ColumnLayout]:
        """Add row to tab"""
        tab = self.get_tab(tab, auto_add_tab)
        return tab, tab.add_col(name)

    def add_grid(self, tab: Union[str, Tab], name: str = None, auto_add_tab: bool = True) -> Tuple[Tab, GridLayout]:
        """Add row to tab"""
        tab = self.get_tab(tab, auto_add_tab)
        return tab, tab.add_grid(name)
