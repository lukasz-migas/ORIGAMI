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
from origami.gui_elements.helpers import TableConfig
from origami.gui_elements.helpers import set_tooltip
from origami.gui_elements.helpers import make_bitmap_btn
from origami.gui_elements.helpers import make_spin_ctrl_int
from origami.visuals.bokeh.document import PlotStore
from origami.gui_elements.panel_base import TableMixin

LOGGER = logging.getLogger(__name__)

PUB_EVENT_LAYOUT_UPDATE = "interactive.layout.update"


def check_values(*values):
    """Check values"""
    for value in values:
        if value in ["", None]:
            return False
    return True


class TableColumnIndexLayout:
    """Table indexer"""

    check = 0
    tab = 1
    layout = 2
    name = 3
    tag = 4


class PanelLayout(wx.Panel, TableMixin):
    """Layout manager"""

    # peaklist parameters
    TABLE_CONFIG = TableConfig()
    TABLE_CONFIG.add("", "check", "bool", 25, hidden=True)
    TABLE_CONFIG.add("tab", "tab", "str", 125)
    TABLE_CONFIG.add("layout", "layout", "str", 125)
    TABLE_CONFIG.add("name", "name", "str", 250)
    TABLE_CONFIG.add("tag", "tag", "str", 0, hidden=True)
    TABLE_COLUMN_INDEX = TableColumnIndexLayout
    TABLE_USE_COLOR = False
    TABLE_WIDGET_DICT = None

    # ui elements
    div_title, div_header, div_footer, n_columns, shared_tools, add_btn = None, None, None, None, None, None
    remove_btn, tab_title, update_btn, layout_choice, layout_name = None, None, None, None, None
    add_tab_btn, remove_tab_btn, clear_btn = None, None, None

    def __init__(self, parent, icons, plot_store: PlotStore = None):
        wx.Panel.__init__(self, parent)
        self.parent = parent
        self._icons = icons
        self.plot_store = plot_store

        self._disable_table_update = None
        self._current_item = None
        self._tab_list = plot_store.tab_names

        self.make_gui()
        self.setup()

    @property
    def current_item_id(self):
        """Returns the index of currently selected item in the table"""
        idx = self.on_find_item("tag", self._current_item)
        return idx

    def setup(self):
        """Setup"""
        self.TABLE_WIDGET_DICT = {
            self.layout_name: TableColumnIndexLayout.name,
            self.layout_choice: TableColumnIndexLayout.layout,
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
        main_sizer.Add(panel, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)
        main_sizer.Add(self.peaklist, 1, wx.EXPAND, 0)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizerAndFit(main_sizer)
        self.Layout()

    def make_panel(self):
        """Make panel"""
        panel = wx.Panel(self)

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

        div_title = wx.StaticText(panel, -1, "Title:")
        self.div_title = wx.TextCtrl(
            panel, -1, "", size=(-1, -1), style=wx.TE_MULTILINE | wx.TE_WORDWRAP | wx.TE_RICH2, name="div_title"
        )
        self.div_title.Bind(wx.EVT_TEXT, self.on_edit_layout)

        div_header = wx.StaticText(panel, -1, "Header:")
        self.div_header = wx.TextCtrl(
            panel, -1, "", size=(400, 100), style=wx.TE_MULTILINE | wx.TE_WORDWRAP | wx.TE_RICH2, name="div_header"
        )
        self.div_header.Bind(wx.EVT_TEXT, self.on_edit_layout)

        div_footer = wx.StaticText(panel, -1, "Footer:")
        self.div_footer = wx.TextCtrl(
            panel, -1, "", size=(400, 100), style=wx.TE_MULTILINE | wx.TE_WORDWRAP | wx.TE_RICH2, name="div_footer"
        )
        self.div_footer.Bind(wx.EVT_TEXT, self.on_edit_layout)

        n_columns = wx.StaticText(panel, -1, "No. columns:")
        self.n_columns = make_spin_ctrl_int(panel, 1, 1, 5, name="n_columns", size=(100, -1))
        self.n_columns.Bind(wx.EVT_SPINCTRL, self.on_edit_layout)

        shared_tools = wx.StaticText(panel, -1, "Shared tools:")
        self.shared_tools = wx.CheckBox(panel, -1, "", name="shared_tools")

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
            raise ValueError("You must provide `tab title`, `layout type` and  `name`")
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

        # get current item in the table that is being edited
        item_id = self.current_item_id
        col_id = self.TABLE_WIDGET_DICT.get(obj, -1)
        if item_id == -1 or col_id == -1:
            return

        if isinstance(col_id, str):
            setattr(layout, col_id, obj.GetValue())
            return

        # update item in the table
        if col_id == TableColumnIndexLayout.name:
            layout.name = obj.GetValue()
        elif col_id == TableColumnIndexLayout.layout:
            tab.change_layout(layout.name, new_layout=obj.GetValue().lower())
        self.peaklist.SetItem(item_id, col_id, str(obj.GetValue()))
        pub.sendMessage(PUB_EVENT_LAYOUT_UPDATE, layout_list=("change", self.plot_store.layout_list))

    def _on_add_layout(self, tab_name: str, layout_type: str, name: str):
        """Add layout to the PlotStore"""
        div_title = self.div_title.GetValue()
        div_header = self.div_header.GetValue()
        div_footer = self.div_footer.GetValue()
        n_columns = self.n_columns.GetValue()
        shared_tools = self.shared_tools.GetValue()
        if self._current_item is None:
            tag = get_short_hash()
        else:
            tag = self._current_item

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
            pub.sendMessage(PUB_EVENT_LAYOUT_UPDATE, layout_list=("add", self.plot_store.layout_list))
            self.on_add_to_table({"tab": tab_name, "layout": layout_type, "name": name, "tag": tag})

    def on_clear_ui(self, _evt):
        """Clear ui elements"""
        self._disable_table_update = True
        self.layout_name.SetValue("")
        self.div_title.SetValue("")
        self.div_header.SetValue("")
        self.div_footer.SetValue("")
        self._current_item = None
        self._disable_table_update = False

    def on_remove_layout(self, _evt):
        """Remove layout to the table"""
        if self._current_item is not None:
            pub.sendMessage(PUB_EVENT_LAYOUT_UPDATE, layout_list=("remove", self.plot_store.layout_list))
            self.remove_from_table([self.current_item_id])
        self._current_item = None
