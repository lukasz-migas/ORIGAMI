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

# Local imports
from origami.visuals.bokeh.tab import Tab
from origami.visuals.bokeh.layout import RowLayout
from origami.visuals.bokeh.layout import GridLayout
from origami.visuals.bokeh.layout import ColumnLayout


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
    def title(self) -> str:
        """Return title of the PlotStore"""
        return self._title

    @title.setter
    def title(self, value: str):
        """Return title of the PlotStore"""
        self._title = value

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

    def save(self, filepath=None, display=True, tab_names=None, always_as_tabs=True) -> str:
        """Save Bokeh document as HTML file

        Parameters
        ----------
        filepath : str
            path where to save the HTML document
        display : bool
            if 'True', newly generated document will be shown in the browser
        tab_names : list
            list of tab names which must be present in the `tabs` container
        always_as_tabs : bool
            if 'True', the resultant HTML document will contain 'Tabs' even if only one tab is present

        Returns
        -------
        filepath : str
            output path
        """

        if filepath is None:
            filepath = self.filepath

        save(self.get_layout(tab_names=tab_names, always_as_tabs=always_as_tabs), filepath, title=self._title)

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

    def reset_layouts(self):
        """Reset all layouts contained within the PlotStore"""
        for tab in self._tabs.values():
            for layout in tab.values():
                layout.clear()

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
