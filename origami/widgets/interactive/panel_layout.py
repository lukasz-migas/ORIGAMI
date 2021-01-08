"""Layout panel"""
# Standard library imports
import logging
from typing import Dict

# Third-party imports
import wx
from pubsub import pub

# Local imports
from origami.styles import Validator
from origami.utils.secret import get_short_hash
from origami.utils.utilities import notify_error
from origami.gui_elements.helpers import TableConfig
from origami.gui_elements.helpers import set_tooltip
from origami.gui_elements.helpers import make_bitmap_btn
from origami.gui_elements.helpers import make_spin_ctrl_int
from origami.visuals.bokeh.document import PlotStore
from origami.gui_elements.panel_base import TableMixin
from origami.widgets.interactive.utilities import DIV_STYLE
from origami.widgets.interactive.utilities import PUB_EVENT_LAYOUT_ADD
from origami.widgets.interactive.utilities import PUB_EVENT_PLOT_ORDER
from origami.widgets.interactive.utilities import PUB_EVENT_TAB_REMOVE
from origami.widgets.interactive.utilities import PUB_EVENT_LAYOUT_REMOVE
from origami.widgets.interactive.utilities import PUB_EVENT_LAYOUT_UPDATE

LOGGER = logging.getLogger(__name__)


def check_values(*values):
    """Check values"""
    for value in values:
        if value in ["", None]:
            return False
    return True


class TableColumnIndexEditor:
    """Table indexer"""

    check = 0
    order = 1
    name = 2
    document_title = 3
    dataset_type = 4
    tag = 5


class PanelLayoutEditor(wx.Panel, TableMixin):
    """Layout editor"""

    # peaklist parameters
    TABLE_CONFIG = TableConfig()
    TABLE_CONFIG.add("", "check", "bool", 25, hidden=True)
    TABLE_CONFIG.add("order", "order", "int", 75)
    TABLE_CONFIG.add("name", "name", "str", 200)
    TABLE_CONFIG.add("document", "document_title", "str", 200)
    TABLE_CONFIG.add("type", "dataset_type", "str", 200)
    TABLE_CONFIG.add("tag", "tag", "str", 0, hidden=True)  # tag of the plot
    TABLE_COLUMN_INDEX = TableColumnIndexEditor
    TABLE_USE_COLOR = False
    TABLE_DISABLE_SORT = True

    # ui elements
    tab_layout_value, note, up_btn, down_btn = None, None, None, None

    def __init__(self, notebook, parent, icons, plot_store: PlotStore = None):
        wx.Panel.__init__(self, notebook)
        self.parent = parent
        self._icons = icons
        self.plot_store = plot_store

        self._disable_table_update = None
        self._current_item = None

        self.make_gui()
        self.setup()

        # bind events
        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnDestroy)

    def OnDestroy(self, event):  # noqa
        """Called just before the panel is destroyed so we can cleanup"""
        try:
            pub.unsubscribe(self.evt_layout_choice_add, PUB_EVENT_LAYOUT_ADD)
            pub.unsubscribe(self.evt_layout_choice_remove, PUB_EVENT_LAYOUT_REMOVE)
            pub.unsubscribe(self.evt_layout_choice_update, PUB_EVENT_LAYOUT_UPDATE)
            pub.unsubscribe(self.evt_tab_choice_remove, PUB_EVENT_TAB_REMOVE)
            LOGGER.debug("Unsubscribed from events")
        except Exception as err:
            LOGGER.error("Failed to unsubscribe events: %s" % err)
        event.Skip()

    def setup(self):
        """Setup"""
        pub.subscribe(self.evt_layout_choice_add, PUB_EVENT_LAYOUT_ADD)
        pub.subscribe(self.evt_layout_choice_remove, PUB_EVENT_LAYOUT_REMOVE)
        pub.subscribe(self.evt_layout_choice_update, PUB_EVENT_LAYOUT_UPDATE)
        pub.subscribe(self.evt_tab_choice_remove, PUB_EVENT_TAB_REMOVE)

    @property
    def current_item(self) -> str:
        """Returns the tag of the currently selected item"""
        return self._current_item

    @property
    def current_item_id(self) -> int:
        """Returns the index of currently selected item in the table"""
        idx = self.on_find_item("tag", self._current_item)
        return idx

    def make_gui(self):
        """Make UI"""

        tab_layout_value = wx.StaticText(self, -1, "Layout:")
        self.tab_layout_value = wx.ComboBox(self, choices=[], style=wx.CB_READONLY, name="tab_choice")
        self.tab_layout_value.Bind(wx.EVT_COMBOBOX, self.on_populate_table)

        self.peaklist = self.make_table(self.TABLE_CONFIG)
        self.peaklist.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_select_plot)

        self.note = wx.StaticText(
            self,
            -1,
            ""
            "Please select a layout and then a plot item in the table. You can use the up and down arrows to move plot"
            "\nobjects around in order to specify their order in the final HTML document",
        )

        self.up_btn = make_bitmap_btn(self, wx.ID_ANY, self._icons.up)
        self.up_btn.Bind(wx.EVT_BUTTON, self.on_move_up)
        set_tooltip(self.up_btn, "Move currently select plot up in the layout")

        self.down_btn = make_bitmap_btn(self, wx.ID_ANY, self._icons.down)
        self.down_btn.Bind(wx.EVT_BUTTON, self.on_move_down)
        set_tooltip(self.down_btn, "Move currently selected plot down in the layout")

        # pack heatmap items
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(tab_layout_value, (n, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.tab_layout_value, (n, 1), (1, 1), flag=wx.EXPAND)
        grid.AddGrowableCol(1, 1)

        btn_sizer = wx.BoxSizer(wx.VERTICAL)
        btn_sizer.Add(self.up_btn, 0, wx.ALIGN_CENTER_HORIZONTAL)
        btn_sizer.Add(self.down_btn, 0, wx.ALIGN_CENTER_HORIZONTAL)

        table_sizer = wx.BoxSizer()
        table_sizer.Add(self.peaklist, 1, wx.EXPAND | wx.ALL, 5)
        table_sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.note, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(table_sizer, 1, wx.EXPAND | wx.ALL, 5)

        # pack elements
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(grid, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(sizer, 1, wx.EXPAND | wx.ALL, 5)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizerAndFit(main_sizer)
        self.Layout()

    def on_select_plot(self, evt):
        """Select plot object in the table"""
        self._disable_table_update = True
        if hasattr(evt, "GetIndex"):
            self.peaklist.item_id = evt.GetIndex()

        # get metadata contained within the table
        item_info = self.on_get_item_information()

        self._current_item = item_info["tag"]
        LOGGER.debug(f"Selected `{self._current_item}`")
        self._disable_table_update = False

    def on_move_up(self, _evt):
        """Move object up in the table"""
        current_id = self.current_item_id
        # no need to move
        if current_id == 0 or current_id == -1:
            return
        # update id
        new_id = current_id - 1
        self._on_change_item_position(current_id, new_id)

    def on_move_down(self, _evt):
        """Move object down in the table"""
        current_id = self.current_item_id
        # no need to move
        if current_id == self.n_rows - 1 or current_id == -1:
            return

        # update id
        new_id = current_id + 1
        self._on_change_item_position(current_id, new_id)

    def reorder_plot_ids(self):
        """Iterate through all rows in the table and fix the ids"""
        plot_data = {}
        for item_id in range(self.n_rows):
            self.peaklist.set_text(item_id, TableColumnIndexEditor.order, item_id)
            plot_data[self.peaklist.get_text(item_id, TableColumnIndexEditor.tag)] = item_id
        pub.sendMessage(PUB_EVENT_PLOT_ORDER, plot_data=plot_data)

    def _on_change_item_position(self, current_id: int, new_id: int):
        """Update position of an item in the table"""
        item_data = []
        for col_id in range(self.n_columns):
            item = self.peaklist.GetItem(current_id, col_id)
            item.SetId(new_id)
            item.SetState(0)
            item_data.append(item)

        self.peaklist.DeleteItem(current_id)
        self.peaklist.InsertItem(new_id, "")
        for item in item_data:
            self.peaklist.SetItem(item)
        self.peaklist.Select(new_id, 1)
        self.reorder_plot_ids()

    def on_populate_table(self, _evt):
        """Populate table based on objects found in the parent with specific layout"""

        def _get_order(order, _plot_id):
            if order in [None, ""]:
                return _plot_id
            return order

        layout_name = self.tab_layout_value.GetStringSelection()
        if not hasattr(self.parent, "get_plots_for_layout"):
            notify_error("Cannot retrieve list of plot items")
            return
        item_list = self.parent.get_plots_for_layout(layout_name)
        self.peaklist.DeleteAllItems()
        plot_id = 0
        for item in item_list:
            # add to table
            self.on_add_to_table(
                {
                    "order": _get_order(item["order"], plot_id),
                    "name": item["name"],
                    "dataset_name": item["dataset_name"],
                    "document_title": item["document_title"],
                    "dataset_type": item["dataset_type"],
                    "tag": item["tag"],
                },
                check_color=False,
            )

    def evt_layout_choice_add(self, layout_data: Dict):
        """Add new layout to the combobox

        This function expects `name` in the `layout_data`
        """
        idx = self.tab_layout_value.FindString(layout_data["name"])
        if idx != -1:
            LOGGER.warning(f"Layout with the name `{layout_data['name']}` is already in the control")
            return
        self.tab_layout_value.AppendItems([layout_data["name"]])

    def evt_layout_choice_remove(self, layout_data: Dict):
        """Remove layout from the combobox and ensure its also removed from the table

        This function expects `name` in the `layout_data`
        """
        idx = self.tab_layout_value.FindString(layout_data["name"])
        is_current = self.tab_layout_value.GetStringSelection() == layout_data["name"]
        self.tab_layout_value.Delete(idx)
        if is_current:
            self.peaklist.DeleteAllItems()

    def evt_layout_choice_update(self, layout_data: Dict):
        """Update layout name in the combobox and in the table

        This function expects `old_name` and `new_name` in the `layout_data`
        """
        idx = self.tab_layout_value.FindString(layout_data["old_name"])
        self.tab_layout_value.SetString(idx, layout_data["new_name"])

    def evt_tab_choice_remove(self, tab_data: Dict):
        """Remove tab and all of its layouts from the combobox and the table

        This function expects `name` in the `tab_data`
        """
        items = self.tab_layout_value.GetItems()
        _items = []
        for item in items:
            if tab_data["name"] not in item:
                _items.append(item)
        self.tab_layout_value.Clear()
        self.tab_layout_value.SetItems(_items)
        self.peaklist.DeleteAllItems()


class TableColumnIndexBuilder:
    """Table indexer"""

    check = 0
    tab = 1
    layout = 2
    name = 3
    tag = 4


class PanelLayoutBuilder(wx.Panel, TableMixin):
    """Layout builder"""

    # peaklist parameters
    TABLE_CONFIG = TableConfig()
    TABLE_CONFIG.add("", "check", "bool", 25, hidden=True)
    TABLE_CONFIG.add("tab name", "tab", "str", 150)
    TABLE_CONFIG.add("layout type", "layout", "str", 125)
    TABLE_CONFIG.add("layout name", "name", "str", 300)
    TABLE_CONFIG.add("tag", "tag", "str", 0, hidden=True)
    TABLE_COLUMN_INDEX = TableColumnIndexBuilder
    TABLE_USE_COLOR = False
    TABLE_WIDGET_DICT = None

    # ui elements
    div_title, div_header, div_footer, n_columns, shared_tools, add_btn = None, None, None, None, None, None
    remove_btn, tab_title, update_btn, layout_choice, layout_name = None, None, None, None, None
    add_tab_btn, remove_tab_btn, clear_btn = None, None, None

    def __init__(self, notebook, parent, icons, plot_store: PlotStore = None):
        wx.Panel.__init__(self, notebook)
        self.parent = parent
        self._icons = icons
        self.plot_store = plot_store

        self._disable_table_update = None
        self._current_item = None
        self._tab_list = plot_store.tab_names if plot_store else []

        self.make_gui()
        self.setup()

    @property
    def current_item(self) -> str:
        """Returns the tag of the currently selected item"""
        return self._current_item

    @property
    def current_item_id(self) -> int:
        """Returns the index of currently selected item in the table"""
        idx = self.on_find_item("tag", self._current_item)
        return idx

    def setup(self):
        """Setup"""
        self.TABLE_WIDGET_DICT = {
            self.layout_name: TableColumnIndexBuilder.name,
            self.layout_choice: TableColumnIndexBuilder.layout,
            self.div_title: "div_title",
            self.div_header: "div_header",
            self.div_footer: "div_footer",
            self.n_columns: "n_cols",
            self.shared_tools: "shared_tools",
        }
        self.on_select_tab(None)

    def make_gui(self):
        """Make UI"""
        panel = self.make_panel()

        self.peaklist = self.make_table(self.TABLE_CONFIG)
        self.peaklist.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_select_layout)

        # pack elements
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(panel, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(self.peaklist, 1, wx.EXPAND | wx.ALL, 5)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizerAndFit(main_sizer)
        self.Layout()

    def make_panel(self):
        """Make panel"""
        panel = wx.Panel(self, -1, size=(-1, -1))

        tab_title = wx.StaticText(panel, -1, "Tab title:")
        self.tab_title = wx.ComboBox(panel, choices=self._tab_list, style=wx.CB_READONLY, name="tab_choice")
        self.tab_title.Bind(wx.EVT_COMBOBOX, self.on_select_tab)

        self.add_tab_btn = make_bitmap_btn(panel, wx.ID_ANY, self._icons.add)
        self.add_tab_btn.Bind(wx.EVT_BUTTON, self.on_add_tab)
        set_tooltip(self.add_tab_btn, "Add tab to the PlotStore")

        self.remove_tab_btn = make_bitmap_btn(panel, wx.ID_ANY, self._icons.remove)
        self.remove_tab_btn.Bind(wx.EVT_BUTTON, self.on_remove_tab)
        set_tooltip(self.remove_tab_btn, "Remove tab from the PlotStore alongside all of its layouts")

        layout_name = wx.StaticText(panel, -1, "Name:")
        self.layout_name = wx.TextCtrl(panel, -1, "", size=(-1, -1), name="layout_name", validator=Validator("path"))
        self.layout_name.Bind(wx.EVT_TEXT, self.on_edit_layout)

        layout_choice = wx.StaticText(panel, -1, "Layout:")
        self.layout_choice = wx.ComboBox(
            panel, choices=["Row", "Column", "Grid"], style=wx.CB_READONLY, name="layout_choice"
        )
        self.layout_choice.SetStringSelection("Row")
        self.layout_choice.Bind(wx.EVT_COMBOBOX, self.on_edit_layout)
        self.layout_choice.Bind(wx.EVT_COMBOBOX, self.on_toggle_controls)

        div_title = wx.StaticText(panel, -1, "Title:")
        self.div_title = wx.TextCtrl(panel, -1, "", size=(-1, -1), style=DIV_STYLE, name="div_title")
        self.div_title.Bind(wx.EVT_TEXT, self.on_edit_layout)

        div_header = wx.StaticText(panel, -1, "Header:")
        self.div_header = wx.TextCtrl(panel, -1, "", size=(400, 100), style=DIV_STYLE, name="div_header")
        self.div_header.Bind(wx.EVT_TEXT, self.on_edit_layout)

        div_footer = wx.StaticText(panel, -1, "Footer:")
        self.div_footer = wx.TextCtrl(panel, -1, "", size=(400, 100), style=DIV_STYLE, name="div_footer")
        self.div_footer.Bind(wx.EVT_TEXT, self.on_edit_layout)

        n_columns = wx.StaticText(panel, -1, "No. columns:")
        self.n_columns = make_spin_ctrl_int(panel, 1, 1, 5, name="n_columns", size=(100, -1))
        self.n_columns.Bind(wx.EVT_SPINCTRL, self.on_edit_layout)

        shared_tools = wx.StaticText(panel, -1, "Shared tools:")
        self.shared_tools = wx.CheckBox(panel, -1, "", name="shared_tools")
        self.shared_tools.Bind(wx.EVT_CHECKBOX, self.on_edit_layout)

        self.add_btn = wx.Button(panel, wx.ID_ANY, "Add", size=(-1, -1))
        self.add_btn.Bind(wx.EVT_BUTTON, self.on_add_layout)

        self.clear_btn = wx.Button(panel, wx.ID_ANY, "Clear", size=(-1, -1))
        self.clear_btn.Bind(wx.EVT_BUTTON, self.on_clear_ui)

        self.remove_btn = wx.Button(panel, wx.ID_ANY, "Remove", size=(-1, -1))
        self.remove_btn.Bind(wx.EVT_BUTTON, self.on_remove_layout)

        btn_sizer = wx.BoxSizer()
        btn_sizer.Add(self.add_btn)
        btn_sizer.AddSpacer(5)
        btn_sizer.Add(self.clear_btn)
        btn_sizer.AddSpacer(5)
        btn_sizer.Add(self.remove_btn)

        _row_sizer = wx.BoxSizer()
        _row_sizer.Add(self.tab_title, 1, wx.EXPAND, 0)
        _row_sizer.AddSpacer(5)
        _row_sizer.Add(self.add_tab_btn)
        _row_sizer.Add(self.remove_tab_btn)

        # pack heatmap items
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(tab_title, (n, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(_row_sizer, (n, 1), (1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(layout_name, (n, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.layout_name, (n, 1), (1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(layout_choice, (n, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.layout_choice, (n, 1), (1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(div_title, (n, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.div_title, (n, 1), (1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(div_header, (n, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_TOP)
        grid.Add(self.div_header, (n, 1), (2, 1), flag=wx.EXPAND)
        n += 2
        grid.Add(div_footer, (n, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_TOP)
        grid.Add(self.div_footer, (n, 1), (2, 1), flag=wx.EXPAND)
        n += 2
        grid.Add(n_columns, (n, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.n_columns, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        n += 1
        grid.Add(shared_tools, (n, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.shared_tools, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        grid.AddGrowableCol(1, 1)

        settings_sizer = wx.BoxSizer(wx.VERTICAL)
        settings_sizer.Add(grid, 1, wx.EXPAND | wx.ALL, 0)
        settings_sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 0)
        settings_sizer.Fit(panel)
        panel.SetSizerAndFit(settings_sizer)

        return panel

    def on_add_tab(self, _evt):
        """Add tab to the PlotStore"""

        from origami.widgets.interactive.dialog_new_tab import DialogNewTab

        tabs = self.plot_store.tab_names
        dlg = DialogNewTab(self, "Tab", tabs)
        dlg.ShowModal()

        # get new name
        tab_name = dlg.new_name
        if tab_name is None:
            return
        # add new tab
        tab = self.plot_store.add_tab(tab_name)
        tab.auto_create = False
        self._populate_tab_list(tab_name)

        LOGGER.debug(f"Added new tab - `{tab_name}`")

    def on_remove_tab(self, _evt):
        """Remove tab from the PlotStore"""

        from origami.gui_elements.misc_dialogs import DialogBox

        tab_name = self.tab_title.GetStringSelection()
        if not check_values(tab_name):
            return

        dlg = DialogBox(
            title="Are you sure?",
            msg=f"Are you sure you want to remove `{tab_name}` from the PlotStore?\nThis action is irreversible.",
            kind="Question",
        )
        if dlg == wx.ID_NO:
            LOGGER.info("Action was cancelled")
            return
        self.plot_store.remove_tab(tab_name)
        self._populate_tab_list()

        # remove item(s) from the table that have the same tab
        item_ids = []
        for item_id in range(self.n_rows):
            item_info = self.on_get_item_information(item_id)
            if item_info["tab"] == tab_name:
                item_ids.append(item_id)
        if item_ids:
            self.remove_from_table(item_ids)
        pub.sendMessage(PUB_EVENT_TAB_REMOVE, tab_data={"name": tab_name})
        LOGGER.debug(f"Removed tab - `{tab_name}`")

    def _populate_tab_list(self, tab_name: str = None):
        """Populate selection box"""
        # add new tab to selection
        self.tab_title.Clear()
        self.tab_title.SetItems(self.plot_store.tab_names)
        if tab_name:
            self.tab_title.SetStringSelection(tab_name)
        self.on_select_tab(None)

    def on_select_tab(self, _evt):
        """Select tab"""
        tab_name = self.tab_title.GetStringSelection()
        is_tab = check_values(tab_name)

        self.layout_choice.Enable(is_tab)
        self.layout_name.Enable(is_tab)
        self.div_title.Enable(is_tab)
        self.div_header.Enable(is_tab)
        self.div_footer.Enable(is_tab)
        self.n_columns.Enable(is_tab)
        self.shared_tools.Enable(is_tab)

    def on_select_layout(self, evt):
        """Select calibrant from the table and populate fields"""
        self._disable_table_update = True
        if hasattr(evt, "GetIndex"):
            self.peaklist.item_id = evt.GetIndex()

        # get metadata contained within the table
        item_info = self.on_get_item_information()

        # get metadata contained within the config file
        metadata = self.get_layout_metadata(item_info)

        self.tab_title.SetStringSelection(item_info["tab"])
        self.layout_name.SetValue(item_info["name"])
        self.layout_choice.SetStringSelection(item_info["layout"])
        self.div_title.SetValue(metadata["div_title"])
        self.div_header.SetValue(metadata["div_header"])
        self.div_footer.SetValue(metadata["div_footer"])
        self.n_columns.SetValue(metadata["n_columns"])
        self.shared_tools.SetValue(metadata["shared_tools"])

        self._current_item = item_info["tag"]
        LOGGER.debug(f"Selected `{self._current_item}`")
        self._disable_table_update = False

    def get_layout_metadata(self, item_info: Dict) -> Dict:
        """Get metadata from the DocumentStore"""
        tab_name = item_info["tab"]
        # get tab from the plot store
        tab = self.plot_store.get_tab(tab_name)
        layout = tab.get_layout(item_info["tag"])
        return {
            "div_title": layout.div_title_str,
            "div_header": layout.div_header_str,
            "div_footer": layout.div_footer_str,
            "n_columns": layout.n_cols,
            "shared_tools": layout.shared_tools,
        }

    def on_add_layout(self, _evt):
        """Add layout to the table"""
        self._disable_table_update = True
        tab_name = self.tab_title.GetStringSelection()
        name = self.layout_name.GetValue()
        layout_type = self.layout_choice.GetStringSelection()
        if not check_values(tab_name, layout_type, name):
            notify_error("You must provide `tab title`, `layout type` and  `name`")
            return
        # add layout
        self._on_add_layout(tab_name=tab_name, layout_type=layout_type, name=name)
        self.on_clear_ui(None)
        self._disable_table_update = False

    def get_current_layout(self):
        """Get current layout"""
        # get tab from the plot store
        item_info = self.on_get_item_information()

        # get layout
        try:
            tab = self.plot_store.get_tab(item_info["tab"])
            layout = tab.get_layout(item_info["tag"])
        except KeyError:
            tab, layout = None, None
        return tab, layout

    def on_edit_layout(self, evt):
        """Edit layout"""
        if self._disable_table_update:
            return
        tab, layout = self.get_current_layout()
        if layout is None:
            return

        # get ui object that created this event
        obj = evt.GetEventObject()
        tag = self.current_item

        # get current item in the table that is being edited
        item_id = self.current_item_id
        col_id = self.TABLE_WIDGET_DICT.get(obj, -1)
        if item_id == -1 or col_id == -1:
            return

        if isinstance(col_id, str):
            setattr(layout, col_id, obj.GetValue())
            return

        # update item in the table
        if col_id == TableColumnIndexBuilder.name:
            old_name = layout.layout_repr(tab.name, self.current_item)
            layout.name = obj.GetValue()
            new_name = layout.layout_repr(tab.name, self.current_item)
            #             self.peaklist.SetItem(item_id, col_id, str(obj.GetValue()))
            pub.sendMessage(
                PUB_EVENT_LAYOUT_UPDATE,
                layout_data={"tag": self.current_item, "old_name": old_name, "new_name": new_name},
            )
        elif col_id == TableColumnIndexBuilder.layout:
            tab.update_layout(tag, new_layout=obj.GetValue().lower())
        self.peaklist.SetItem(item_id, col_id, str(obj.GetValue()))

    def on_toggle_controls(self, evt):
        """Toggle various items in the UI based on event triggers"""
        is_grid = self.layout_choice.GetStringSelection() == "Grid"
        self.n_columns.Enable(is_grid)
        self.shared_tools.Enable(is_grid)

        if evt is not None:
            evt.Skip()

    def _on_add_layout(self, tab_name: str, layout_type: str, name: str):
        """Add layout to the PlotStore"""
        div_title = self.div_title.GetValue()
        div_header = self.div_header.GetValue()
        div_footer = self.div_footer.GetValue()
        n_columns = self.n_columns.GetValue()
        shared_tools = self.shared_tools.GetValue()
        if self.current_item is None:
            tag = get_short_hash()
        else:
            tag = self.current_item

        # get tab from the plot store
        tab = self.plot_store.get_tab(tab_name)

        # get layout
        try:
            layout = tab.get_layout(tag)
        except KeyError:
            layout = tab.add_layout(tag, layout_type.lower())

        # update values
        layout.name = name
        layout.div_title = div_title
        layout.div_header = div_header
        layout.div_footer = div_footer
        layout.n_cols = n_columns
        layout.shared_tools = shared_tools

        item_id = self.current_item_id
        if item_id == -1:
            pub.sendMessage(PUB_EVENT_LAYOUT_ADD, layout_data={"tag": tag, "name": layout.layout_repr(tab.name, tag)})
            self.on_add_to_table({"tab": tab_name, "layout": layout_type, "name": name, "tag": tag})

    def on_clear_ui(self, _evt):
        """Clear ui elements"""
        self._disable_table_update = True
        self.layout_name.SetValue("")
        self.div_title.SetValue("")
        self.div_header.SetValue("")
        self.div_footer.SetValue("")
        self.shared_tools.SetValue(False)
        self.n_columns.SetValue(1)
        self._current_item = None
        self._disable_table_update = False

    def on_remove_layout(self, _evt):
        """Remove layout to the table"""
        if self.current_item is not None:
            tab, layout = self.get_current_layout()
            pub.sendMessage(
                PUB_EVENT_LAYOUT_REMOVE,
                layout_data={"tag": self.current_item, "name": layout.layout_repr(tab.name, self.current_item)},
            )
            self.remove_from_table([self.current_item_id])
        self._current_item = None


if __name__ == "__main__":

    from origami.icons.assets import Icons
    from origami.utils.screen import move_to_different_screen

    def _main_builder():

        from origami.app import App

        class _TestFrame(wx.Frame):
            def __init__(self):
                wx.Frame.__init__(self, None, -1, "Frame", size=(300, 300))
                icons = Icons()
                panel = PanelLayoutBuilder(self, self, icons)

        app = App()
        ex = _TestFrame()

        ex.Show()
        move_to_different_screen(ex)
        app.MainLoop()

    def _main_editor():

        from origami.app import App

        class _TestFrame(wx.Frame):
            def __init__(self):
                wx.Frame.__init__(self, None, -1, "Frame", size=(300, 300))
                icons = Icons()
                panel = PanelLayoutEditor(self, self, icons)

        app = App()
        ex = _TestFrame()

        ex.Show()
        move_to_different_screen(ex)
        app.MainLoop()

    _main_builder()
