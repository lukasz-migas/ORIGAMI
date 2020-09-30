"""Panel responsible for creating interactive layouts"""
# Standard library imports
import logging
from typing import Any
from typing import Dict
from typing import List
from functools import partial
from collections import namedtuple

# Third-party imports
import wx
from pubsub import pub
from natsort import natsorted
from natsort import order_by_index
from natsort import index_natsorted

# Local imports
from origami.styles import MiniFrame
from origami.config.config import CONFIG
from origami.visuals.bokeh.tab import Tab
from origami.config.environment import ENV
from origami.gui_elements.mixins import DatasetMixin
from origami.gui_elements.mixins import ColorGetterMixin
from origami.gui_elements.helpers import TableConfig
from origami.gui_elements.helpers import set_tooltip
from origami.gui_elements.helpers import make_checkbox
from origami.gui_elements.helpers import make_menu_item
from origami.gui_elements.helpers import make_bitmap_btn
from origami.visuals.bokeh.layout import BaseLayout
from origami.visuals.bokeh.document import PlotStore
from origami.gui_elements.panel_base import TableMixin
from origami.visuals.bokeh.plot_base import PlotBase
from origami.objects.containers.heatmap import IonHeatmapObject
from origami.objects.containers.spectrum import MobilogramObject
from origami.objects.containers.spectrum import ChromatogramObject
from origami.objects.containers.spectrum import MassSpectrumObject
from origami.widgets.interactive.utilities import DIV_STYLE
from origami.widgets.interactive.utilities import PUB_EVENT_LAYOUT_ADD
from origami.widgets.interactive.utilities import PUB_EVENT_PLOT_ORDER
from origami.widgets.interactive.utilities import PUB_EVENT_TAB_REMOVE
from origami.widgets.interactive.utilities import PUB_EVENT_LAYOUT_REMOVE
from origami.widgets.interactive.utilities import PUB_EVENT_LAYOUT_UPDATE
from origami.widgets.interactive.panel_layout import PanelLayoutEditor
from origami.widgets.interactive.panel_layout import PanelLayoutBuilder
from origami.widgets.interactive.panel_plot_parameters import PanelVisualisationSettingsEditor

LOGGER = logging.getLogger(__name__)

PlotItem = namedtuple(
    "PlotItem", ["tag", "document_title", "dataset_name", "layout", "order", "div_title", "div_header", "div_footer"]
)


class TableColumnIndex:
    """Table indexer"""

    check = 0
    name = 1
    document_title = 2
    dataset_type = 3
    layout = 4
    order = 5
    title = 6
    header = 7
    footer = 8
    dataset_name = 9
    tag = 10


class PanelInteractiveEditor(MiniFrame, TableMixin, ColorGetterMixin, DatasetMixin):
    """Editor panel"""

    # peaklist parameters
    TABLE_CONFIG = TableConfig()
    TABLE_CONFIG.add("", "check", "bool", 25, hidden=True)
    TABLE_CONFIG.add("name", "name", "str", 200)
    TABLE_CONFIG.add("document", "document_title", "str", 200)
    TABLE_CONFIG.add("type", "dataset_type", "str", 135)
    TABLE_CONFIG.add("tab/layout", "layout", "str", 150)
    TABLE_CONFIG.add("order", "order", "int", 75)
    TABLE_CONFIG.add("title", "div_title", "str", 0, hidden=True)
    TABLE_CONFIG.add("header", "div_header", "str", 0, hidden=True)
    TABLE_CONFIG.add("footer", "div_footer", "str", 0, hidden=True)
    TABLE_CONFIG.add("dataset name", "dataset_name", "str", 0, hidden=True)
    TABLE_CONFIG.add("tag", "tag", "str", 0, hidden=True)
    TABLE_COLUMN_INDEX = TableColumnIndex()
    TABLE_USE_COLOR = False
    TABLE_WIDGET_DICT = None

    HELP_LINK = "https://origami.lukasz-migas.com/"

    # ui elements
    document_title_value, dataset_name_value, div_title, div_header = None, None, None, None
    div_footer, tab_layout_value, output_title_value, output_path_value = None, None, None, None
    output_path_btn, html_editor_btn, export_btn, close_btn = None, None, None, None
    open_in_browser_check, remove_watermark_check, add_offline_support_check = None, None, None
    batch_check_document_items_btn, batch_check_dataset_type_btn, batch_set_layout_btn = None, None, None
    customise_plot_btn, plot_settings = None, None

    def __init__(self, parent, presenter, icons=None, item_list=None, debug: bool = False):
        MiniFrame.__init__(
            self,
            parent,
            title="Interactive output...",
            style=wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX,
            bind_key_events=False,
        )
        self.view = parent
        self.presenter = presenter
        self._icons = self._get_icons(icons)

        self._window_size = self._get_window_size(self.view, [0.9, 0.8])

        # presets
        self._disable_table_update = None
        self._debug = debug
        self._current_item = None
        self._output_title = ""
        self._output_path = ""
        self.item_list = item_list
        self.plot_store: PlotStore = PlotStore()

        self.make_gui()
        self.on_populate_item_list(None)
        self.setup()

    @property
    def current_item_id(self) -> int:
        """Returns the index of currently selected item in the table"""
        idx = self.on_find_item("tag", self._current_item)
        return idx

    @property
    def output_title(self) -> str:
        """Returns the output title to be used in the document"""
        return self.output_title_value.GetValue()

    @property
    def output_path(self) -> str:
        """Returns the output path to be used in the document"""
        return self.output_path_value.GetValue()

    def setup(self):
        """Setup"""
        self.TABLE_WIDGET_DICT = {
            self.tab_layout_value: TableColumnIndex.layout,
            self.div_title: TableColumnIndex.title,
            self.div_header: TableColumnIndex.header,
            self.div_footer: TableColumnIndex.footer,
        }
        self._dataset_mixin_setup()
        pub.subscribe(self.evt_layout_choice_add, PUB_EVENT_LAYOUT_ADD)
        pub.subscribe(self.evt_layout_choice_remove, PUB_EVENT_LAYOUT_REMOVE)
        pub.subscribe(self.evt_layout_choice_update, PUB_EVENT_LAYOUT_UPDATE)
        pub.subscribe(self.evt_tab_choice_remove, PUB_EVENT_TAB_REMOVE)
        pub.subscribe(self.evt_plot_order_update, PUB_EVENT_PLOT_ORDER)

    def on_close(self, evt, force: bool = False):
        """Close window"""
        try:
            pub.unsubscribe(self.evt_layout_choice_add, PUB_EVENT_LAYOUT_ADD)
            pub.unsubscribe(self.evt_layout_choice_remove, PUB_EVENT_LAYOUT_REMOVE)
            pub.unsubscribe(self.evt_layout_choice_update, PUB_EVENT_LAYOUT_UPDATE)
            pub.unsubscribe(self.evt_tab_choice_remove, PUB_EVENT_TAB_REMOVE)
            pub.unsubscribe(self.evt_plot_order_update, PUB_EVENT_PLOT_ORDER)
            LOGGER.debug("Unsubscribed from events")
        except Exception as err:
            LOGGER.error("Failed to unsubscribe events: %s" % err)

        self._dataset_mixin_teardown()
        super(PanelInteractiveEditor, self).on_close(evt, force)

    def make_gui(self):
        """Make UI"""

        notebook = self.make_builder_panel()
        editor = self.make_editor_panel()
        self.plot_settings = PanelVisualisationSettingsEditor(self, self.view)

        # pack elements
        main_sizer = wx.BoxSizer()
        main_sizer.Add(notebook, 1, wx.EXPAND, 5)
        main_sizer.Add(editor, 1, wx.EXPAND, 5)
        main_sizer.Add(wx.StaticLine(self, -1, style=wx.LI_VERTICAL), 0, wx.EXPAND | wx.ALL, 1)
        main_sizer.Add(self.plot_settings, 0, wx.EXPAND, 0)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizer(main_sizer)
        self.SetSize(self._window_size)
        self.Layout()
        self.CenterOnParent()
        self.SetFocus()

    def make_builder_panel(self):
        """Make side panel responsible for generating layouts"""
        # panel = wx.Panel(self, -1, size=(-1, -1), name="settings")

        notebook = wx.Notebook(self)

        panel_document = self.make_document_panel(notebook)
        notebook.AddPage(panel_document, "Document Builder")

        panel_layout = PanelLayoutBuilder(notebook, self, self._icons, self.plot_store)
        notebook.AddPage(panel_layout, "Layout Creator")

        panel_editor = PanelLayoutEditor(notebook, self, self._icons, self.plot_store)
        notebook.AddPage(panel_editor, "Layout Editor")

        return notebook

    def make_document_panel(self, parent):
        """Make side panel responsible for generating document layouts"""
        panel = wx.Panel(parent, -1, size=(-1, -1))

        btn_sizer = self.make_shortcuts_panel(panel)

        self.peaklist = self.make_table(self.TABLE_CONFIG, panel)
        self.peaklist.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_select_item)
        self.peaklist.Bind(wx.EVT_LIST_ITEM_CHECKED, self.on_validate_item)
        self.peaklist.Bind(wx.EVT_LIST_ITEM_UNCHECKED, self.on_validate_item)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(btn_sizer, 0, wx.EXPAND, 3)
        main_sizer.Add(self.peaklist, 1, wx.EXPAND, 3)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)
        panel.Layout()

        return panel

    def make_shortcuts_panel(self, panel):
        """Make toolbar-like to quickly apply batch settings"""
        # panel = wx.Panel(parent, -1, size=(-1, -1))
        self.batch_check_document_items_btn = make_bitmap_btn(
            panel, wx.ID_ANY, self._icons.title, name="batch.document"
        )
        self.batch_check_document_items_btn.Bind(wx.EVT_BUTTON, self.on_batch_apply)
        set_tooltip(self.batch_check_document_items_btn, "Select items in the table with the `???` document title...")

        self.batch_check_dataset_type_btn = make_bitmap_btn(panel, wx.ID_ANY, self._icons.tick, name="batch.dataset")
        self.batch_check_dataset_type_btn.Bind(wx.EVT_BUTTON, self.on_batch_apply)
        set_tooltip(self.batch_check_dataset_type_btn, "Select items in the table with the `???` data type...")

        self.batch_set_layout_btn = make_bitmap_btn(panel, wx.ID_ANY, self._icons.layout, name="batch.layout")
        self.batch_set_layout_btn.Bind(wx.EVT_BUTTON, self.on_batch_apply)
        set_tooltip(self.batch_set_layout_btn, "Apply layout on all selected items")

        sizer = wx.BoxSizer()
        sizer.Add(self.batch_check_document_items_btn, 0, wx.EXPAND, 3)
        sizer.Add(self.batch_check_dataset_type_btn, 0, wx.EXPAND, 3)
        sizer.Add(self.batch_set_layout_btn, 0, wx.EXPAND, 3)

        return sizer

    def make_editor_panel(self):
        """Make side panel responsible for editing object metadata"""
        panel = wx.Panel(self, -1, size=(-1, -1))

        document_title_value = wx.StaticText(panel, -1, "Document:")
        self.document_title_value = wx.StaticText(panel, -1, "")

        dataset_name_value = wx.StaticText(panel, -1, "Dataset name:")
        self.dataset_name_value = wx.StaticText(panel, -1, "")

        div_title = wx.StaticText(panel, -1, "Title:")
        self.div_title = wx.TextCtrl(panel, -1, "", size=(-1, -1), style=DIV_STYLE, name="div_title")
        self.div_title.Bind(wx.EVT_TEXT, self.on_edit_item)

        div_header = wx.StaticText(panel, -1, "Header:")
        self.div_header = wx.TextCtrl(panel, -1, "", size=(-1, 200), style=DIV_STYLE, name="div_header")
        self.div_header.Bind(wx.EVT_TEXT, self.on_edit_item)

        div_footer = wx.StaticText(panel, -1, "Footer:")
        self.div_footer = wx.TextCtrl(panel, -1, "", size=(-1, 200), style=DIV_STYLE, name="div_footer")
        self.div_footer.Bind(wx.EVT_TEXT, self.on_edit_item)

        tab_layout_value = wx.StaticText(panel, -1, "Layout:")
        self.tab_layout_value = wx.ComboBox(panel, choices=[], style=wx.CB_READONLY, name="tab_choice")
        self.tab_layout_value.Bind(wx.EVT_COMBOBOX, self.on_edit_item)

        self.customise_plot_btn = wx.Button(panel, wx.ID_ANY, "Customise...", size=(-1, -1))
        self.customise_plot_btn.Bind(wx.EVT_BUTTON, self.on_customise_plot)
        set_tooltip(self.customise_plot_btn, "Customise plot parameters")

        # output
        output_title_value = wx.StaticText(panel, -1, "Document title:")
        self.output_title_value = wx.TextCtrl(panel, -1, CONFIG.interactive_panel_title, style=wx.TE_CHARWRAP)
        self.output_title_value.Bind(wx.EVT_TEXT, self.on_apply)

        output_path = wx.StaticText(panel, -1, "Path:")
        self.output_path_value = wx.TextCtrl(panel, -1, "", style=wx.TE_CHARWRAP)
        set_tooltip(self.output_path_value, "Specify output path of the HTML document.")

        self.output_path_btn = make_bitmap_btn(panel, wx.ID_ANY, self._icons.folder)
        self.output_path_btn.Bind(wx.EVT_BUTTON, self.on_get_path)
        set_tooltip(self.output_path_btn, "Select output path of the HTML document.")

        self.export_btn = wx.Button(panel, wx.ID_ANY, "Export", size=(-1, -1))
        self.export_btn.Bind(wx.EVT_BUTTON, self.on_export_html)
        set_tooltip(self.export_btn, "Save HTML document")

        self.html_editor_btn = wx.Button(panel, wx.ID_ANY, "HTML Editor", size=(-1, -1))
        self.html_editor_btn.Bind(wx.EVT_BUTTON, self.on_open_html_editor_menu)
        set_tooltip(self.html_editor_btn, "Opens a web-based HTML editor")

        self.close_btn = wx.Button(panel, wx.ID_ANY, "Close", size=(-1, -1))
        self.close_btn.Bind(wx.EVT_BUTTON, self.on_close)
        set_tooltip(self.close_btn, "Close window")

        btn_sizer = wx.BoxSizer()
        btn_sizer.Add(self.export_btn)
        btn_sizer.Add(self.html_editor_btn)
        btn_sizer.Add(self.close_btn)

        self.open_in_browser_check = make_checkbox(panel, "Open in browser after saving")
        self.open_in_browser_check.SetValue(CONFIG.interactive_panel_open_in_browser)

        self.add_offline_support_check = make_checkbox(panel, "Add offline support")
        self.add_offline_support_check.SetValue(CONFIG.interactive_panel_add_offline_support)
        set_tooltip(
            self.add_offline_support_check,
            "Will enable viewing HTML files offline. File size and time to generate the document will increase.",
        )

        self.remove_watermark_check = make_checkbox(panel, "Remove watermark")
        self.remove_watermark_check.SetValue(CONFIG.interactive_panel_remove_watermark)
        set_tooltip(
            self.remove_watermark_check,
            "When unchecked, the ORIGAMI watermark from the bottom of the page will be removed."
            "\nOnly a little bit of advertising",
        )

        check_sizer = wx.BoxSizer()
        check_sizer.Add(self.open_in_browser_check)
        check_sizer.Add(self.add_offline_support_check)
        check_sizer.Add(self.remove_watermark_check)

        # add statusbar
        info_sizer = self.make_statusbar(panel, "right")

        # pack heatmap items
        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(document_title_value, (n, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.document_title_value, (n, 1), (1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(dataset_name_value, (n, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.dataset_name_value, (n, 1), (1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(div_title, (n, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.div_title, (n, 1), (1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(div_header, (n, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_TOP)
        grid.Add(self.div_header, (n, 1), (1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(div_footer, (n, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_TOP)
        grid.Add(self.div_footer, (n, 1), (1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(tab_layout_value, (n, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.tab_layout_value, (n, 1), (1, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(self.customise_plot_btn, (n, 1), (1, 1), flag=wx.ALIGN_LEFT)
        grid.AddGrowableCol(1, 1)

        grid_2 = wx.GridBagSizer(2, 2)
        n = 0
        grid_2.Add(output_title_value, (n, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid_2.Add(self.output_title_value, (n, 1), (1, 1), flag=wx.EXPAND)
        n += 1
        grid_2.Add(output_path, (n, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid_2.Add(self.output_path_value, (n, 1), (1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid_2.Add(self.output_path_btn, (n, 2), (1, 1), flag=wx.ALIGN_CENTER_VERTICAL)
        grid_2.AddGrowableCol(1, 1)

        settings_sizer = wx.BoxSizer(wx.VERTICAL)
        settings_sizer.Add(grid, 1, wx.EXPAND | wx.ALL, 5)
        settings_sizer.AddStretchSpacer()
        settings_sizer.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND | wx.ALL, 5)
        settings_sizer.Add(grid_2, 0, wx.EXPAND | wx.ALL, 5)
        settings_sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)
        settings_sizer.Add(check_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)
        settings_sizer.Add(info_sizer, 0, wx.EXPAND | wx.ALL, 5)
        # fit layout
        settings_sizer.Fit(panel)
        panel.SetSizerAndFit(settings_sizer)

        return panel

    def on_apply(self, evt):
        """Change config"""
        CONFIG.interactive_panel_title = self.output_title_value.GetValue()
        CONFIG.interactive_panel_open_in_browser = self.open_in_browser_check.GetValue()
        CONFIG.interactive_panel_add_offline_support = self.add_offline_support_check.GetValue()
        CONFIG.interactive_panel_remove_watermark = self.remove_watermark_check.GetValue()
        self._parse_evt(evt)

    def on_customise_plot(self, _evt):
        """Customise plot parameters"""
        show = self.plot_settings.IsShown()
        self.plot_settings.Show(not show)
        self.Layout()

    def on_batch_apply(self, evt):
        """Batch-apply some user-selected restrictions"""
        source = evt.GetEventObject().GetName()
        modifiers, item_list = [], []
        if source.endswith("layout"):
            modifiers = ["Set layout >"]
            item_list = self.plot_store.layout_list
            item_list.extend(["separate", "Clear layout"])

        if source.endswith("document"):
            modifiers = ["Select document >", "Add document >"]
            item_list = natsorted(ENV.get_document_list())
        if source.endswith("dataset"):
            modifiers = ["Select dataset type >", "Add dataset type >"]
            item_list = natsorted(list(set(self.peaklist.get_all_in_column(TableColumnIndex.dataset_type))))

        menu = wx.Menu()
        for i, modifier in enumerate(modifiers):
            if i > 0:
                menu.AppendSeparator()
            for item in item_list:
                # add separator to the menu
                if item == "separate":
                    menu.AppendSeparator()
                else:
                    menu_item = make_menu_item(parent=menu, text=f"{modifier} {item}")
                    menu.Append(menu_item)
                    self.Bind(wx.EVT_MENU, self.on_batch_apply_process, menu_item)

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def on_batch_apply_process(self, evt):
        """Actually process user request"""
        # get label from the menu event
        label = evt.GetEventObject().FindItemById(evt.GetId()).GetItemLabel()
        modifier, selection = label.split(" > ")

        # set layout for selected elements
        if "layout" in modifier:
            if selection == "Clear layout":
                selection = ""
            for item_id in self.get_checked_items():
                # TODO: This should also set default order for items
                self.peaklist.set_text(item_id, TableColumnIndex.layout, selection)
                self._validate_item(item_id)
        else:
            if "document" in modifier:
                column_id = TableColumnIndex.document_title
            elif "dataset" in modifier:
                column_id = TableColumnIndex.dataset_type
            else:
                return
            for item_id in range(self.n_rows):
                value = self.peaklist.get_text(item_id, column_id)
                if modifier.startswith("Select"):
                    self.peaklist.CheckItem(item_id, value == selection)
                else:
                    if value == selection:
                        self.peaklist.CheckItem(item_id, True)

    def on_get_path(self, _evt):
        """Get directory where to save the data"""
        dlg = wx.FileDialog(self, "Choose an output filename", wildcard="HTML document (*.html)|*.html")
        dlg.SetFilename("ORIGAMI.html")
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.output_path_value.SetLabel(path)
            self._output_path = path

    def get_selected_items(self) -> List[PlotItem]:
        """Get list of selected items"""
        indices = self.get_checked_items()
        item_list = []
        ordering = []
        for item_id in indices:
            item_info = self.on_get_item_information(item_id)
            # validate item and ensure it has a valid layout
            if item_info["layout"] in ["", None, "None"]:
                LOGGER.warning(
                    f'Item {item_info["document_title"]}/{item_info["dataset_name"]} is missing layout information'
                )
                continue
            order = item_info["order"]
            order = order if order not in ["", "None", None] else 0
            item_list.append(
                PlotItem(
                    item_info["tag"],
                    item_info["document_title"],
                    item_info["dataset_name"],
                    item_info["layout"],
                    order,
                    item_info["div_title"],
                    item_info["div_header"],
                    item_info["div_footer"],
                )
            )
            ordering.append((item_info["layout"], order))

        # sort plot elements based on the tab name and then order defined by the user
        idx = index_natsorted(ordering, key=lambda element: (element[0], element[1]))
        item_list = order_by_index(item_list, idx)

        return item_list

    def on_export_html(self, _evt):
        """Export data in HTML format"""
        item_list = self.get_selected_items()
        if not item_list:
            raise ValueError("You must select at least one item in the table")

        output_path = self.output_path
        output_title = self.output_title
        if output_path in ["", None]:
            raise ValueError("Cannot export data with this path")
        if output_title in ["", None]:
            raise ValueError("Cannot export data with this path")

        # this ensures that layouts do not contain any old plot objects
        self.plot_store.reset_layouts()

        tab_names = []
        for item in item_list:
            _, tab_name = self.set_plot_obj(item)
            tab_names.append(tab_name)
        tab_names = natsorted(set(tab_names))

        self.plot_store.title = output_title
        self.plot_store.save(
            output_path,
            CONFIG.interactive_panel_open_in_browser,
            tab_names=tab_names,
            always_as_tabs=False,
            remove_watermark=CONFIG.interactive_panel_remove_watermark,
        )

    def set_plot_obj(self, item: PlotItem):
        """Set plot data in the document"""
        data_obj = self.get_data_obj(item.document_title, item.dataset_name)
        tab_name, layout_name = self.parse_tab(item.layout)
        tab = self.plot_store.get_tab(tab_name, False)

        if isinstance(data_obj, (MassSpectrumObject, ChromatogramObject, MobilogramObject)):
            plot_obj, _ = tab.add_spectrum(data_obj, layout_name, item.tag)
        elif isinstance(data_obj, (IonHeatmapObject,)):
            plot_obj, _ = tab.add_heatmap(data_obj, layout_name, item.tag)
        else:
            raise ValueError("Could not parse data object")

        # set metadata
        plot_obj.div_title = item.div_title
        plot_obj.div_header = item.div_header
        plot_obj.div_footer = item.div_footer
        return plot_obj, tab_name

    def on_open_html_editor_menu(self, _evt):
        """Create menu enabling selecting which method should be used to open the default html link"""
        menu = wx.Menu()
        menu_html_builtin = make_menu_item(
            parent=menu, text="Open editor in built-in HTML window", bitmap=self._icons.origami, help_text=""
        )
        menu.Append(menu_html_builtin)
        menu_html_browser = make_menu_item(
            parent=menu, text="Open editor in your browser", bitmap=self._icons.browser, help_text=""
        )
        menu.Append(menu_html_browser)

        # bind events
        self.Bind(wx.EVT_MENU, partial(self.on_open_html_editor, "builtin"), menu_html_builtin)
        self.Bind(wx.EVT_MENU, partial(self.on_open_html_editor, "browser"), menu_html_browser)

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def on_open_html_editor(self, browser, _evt):
        """Export data in HTML format"""
        if browser == "builtin":
            from origami.gui_elements.panel_html_viewer import PanelHTMLViewer

            html = PanelHTMLViewer(self, link=CONFIG.interactive_panel_html_editor_link, window_size=(1200, -1))
            html.Show()
        else:
            import webbrowser

            webbrowser.open(CONFIG.interactive_panel_html_editor_link)

    def on_serialize(self, _evt):
        """Serialize the layout for convenient restoration"""
        # TODO: add a method and logic to export current layouts/document structure in a json format

    def on_edit_item(self, evt):
        """Set layout for currently selected object"""
        if self._disable_table_update:
            return

        # get ui object that created this event
        obj = evt.GetEventObject()

        # get current item in the table that is being edited
        item_id = self.current_item_id
        col_id = self.TABLE_WIDGET_DICT.get(obj, -1)
        if item_id == -1 or col_id == -1:
            return
        self.peaklist.SetItem(item_id, col_id, str(obj.GetValue()))
        self._validate_item(item_id)

    def on_select_item(self, evt):
        """Select item in the table and populate its contents"""
        self._disable_table_update = True
        if hasattr(evt, "GetIndex"):
            self.peaklist.item_id = evt.GetIndex()

        # get metadata contained within the table
        item_info = self.on_get_item_information()

        # get metadata contained within the layout file
        # metadata = self.get_plot_object_metadata(item_info)

        # update elements
        self.document_title_value.SetLabel(item_info["document_title"])
        self.dataset_name_value.SetLabel(item_info["dataset_name"])
        self.div_title.SetValue(item_info["div_title"])
        self.div_header.SetValue(item_info["div_header"])
        self.div_footer.SetValue(item_info["div_footer"])
        self.tab_layout_value.SetStringSelection(item_info["layout"])
        self._current_item = item_info["tag"]
        self._disable_table_update = False

    def get_plots_for_layout(self, layout_name: str) -> List[Dict[str, Any]]:
        """Return a list of plot objects based on a specific layout

        Parameters
        ----------
        layout_name : str
            name of the layout as defined using the `layout_repr` method

        Returns
        -------
        item_list : List[Dict[str, Any]]
            list of plot items
        """
        item_list, plot_id = [], 0
        for item_id in range(self.n_rows):
            _layout_name = self.peaklist.get_text(item_id, TableColumnIndex.layout)
            if layout_name == _layout_name:
                item_info = self.on_get_item_information(item_id)
                if item_info["order"] in ["", None]:
                    item_info["order"] = plot_id
                item_list.append(item_info)
                plot_id += 1
        return item_list

    def _validate_item(self, item_id: int):
        layout_name = self.peaklist.get_text(item_id, TableColumnIndex.layout)
        color = wx.WHITE if layout_name != "" else (255, 230, 239)
        self.peaklist.set_background_color(item_id, color)

    def validate_items(self):
        """Validate items"""
        for item_id in range(self.n_rows):
            self._validate_item(item_id)

    def on_validate_item(self, evt):
        """Validate item"""
        item_id = evt.GetIndex()
        self._validate_item(item_id)
        self._parse_evt(evt)

    def on_populate_item_list(self, _evt):
        """Populate item list"""
        item_list = self.item_list
        if not isinstance(item_list, (list, tuple)):
            return
        self.peaklist.DeleteAllItems()
        self._on_populate_item_list(item_list)
        self.validate_items()

    @staticmethod
    def parse_tab(value):
        """Parse value in the format `Tab=; Name=; Tag=;"""

        def _get_value(key):
            return key.split("=")[-1]

        tab_name, tag_name = None, None
        if value.startswith("Tab="):
            tab_name, _, tag_name = value.split("; ")
            tab_name, tag_name = _get_value(tab_name), _get_value(tag_name)
        return tab_name, tag_name

    @staticmethod
    def get_data_obj(document_title: str, dataset_name: str):
        """Get data object"""
        document = ENV.on_get_document(document_title)
        return document[dataset_name, True]

    def get_tab_object(self, item_info: Dict) -> Tab:
        """Get tab object based on what is in the table"""
        tab = None
        tab_name, _ = self.parse_tab(item_info["tab"])
        if tab_name:
            try:
                tab = self.plot_store.get_tab(tab_name)
            except KeyError:
                tab = None
        return tab

    def get_layout_object(self, item_info: Dict) -> BaseLayout:
        """Get layout object"""
        tab = self.get_tab_object(item_info)
        layout = None
        if tab:
            _, tag_name = self.parse_tab(item_info["tab"])
            layout = tab.get_layout(tag_name)
        return layout

    def get_plot_object(self, item_info: Dict) -> PlotBase:
        """Get layout object"""
        tab = self.get_tab_object(item_info)
        plot_obj = None
        if tab:
            _, tag_name = self.parse_tab(item_info["tab"])
            try:
                plot_obj = tab.get_plot_obj(item_info["tag"], tag_name)
            except KeyError:
                pass
        return plot_obj

    def get_plot_object_metadata(self, item_info: Dict) -> Dict:
        """Get plot object based on layout information"""
        plot_obj = self.get_plot_object(item_info)
        if plot_obj:
            return {
                "div_title": plot_obj.div_title,
                "div_header": plot_obj.div_header,
                "div_footer": plot_obj.div_footer,
            }
        return dict.fromkeys(["div_title", "div_header", "div_footer"], "")

    @staticmethod
    def get_item_metadata(item_info: Dict) -> Dict:
        """Get metadata from the DocumentStore"""
        document = ENV.on_get_document(item_info["document_title"])
        if document is None:
            return dict()

        # set data in the document
        obj = document[item_info["dataset_name"], True, True]
        return obj.get_metadata("interactive", dict())

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
        self.tab_layout_value.Delete(idx)
        for item_id in range(self.n_rows):
            layout_name = self.peaklist.get_text(item_id, TableColumnIndex.layout)
            if layout_name == layout_data["name"]:
                self.peaklist.set_text(item_id, TableColumnIndex.layout, "")
                self._validate_item(item_id)

    def evt_layout_choice_update(self, layout_data: Dict):
        """Update layout name in the combobox and in the table

        This function expects `old_name` and `new_name` in the `layout_data`
        """
        idx = self.tab_layout_value.FindString(layout_data["old_name"])
        self.tab_layout_value.SetString(idx, layout_data["new_name"])
        for item_id in range(self.n_rows):
            layout_name = self.peaklist.get_text(item_id, TableColumnIndex.layout)
            if layout_name == layout_data["old_name"]:
                self.peaklist.set_text(item_id, TableColumnIndex.layout, layout_data["new_name"])
                self._validate_item(item_id)

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
        for item_id in range(self.n_rows):
            layout_name = self.peaklist.get_text(item_id, TableColumnIndex.layout)
            if tab_data["name"] in layout_name:
                self.peaklist.set_text(item_id, TableColumnIndex.layout, "")
                self._validate_item(item_id)

    def evt_plot_order_update(self, plot_data: Dict):
        """Update the order of plot elements in the table"""
        for tag, order in plot_data.items():
            idx = self.on_find_item("tag", tag)
            if idx != -1:
                self.peaklist.set_text(idx, TableColumnIndex.order, str(order))

    def _on_populate_item_list(self, item_list: List[str]):
        """Populate table with items"""

        for item in item_list:
            # get document and dataset information
            dataset_name, document_title, tag = item
            dataset_type, name = dataset_name.split("/")

            # add to table
            self.on_add_to_table(
                {
                    "name": name,
                    "dataset_name": dataset_name,
                    "document_title": document_title,
                    "dataset_type": dataset_type,
                    "tag": tag,
                },
                check_color=False,
            )


def _main():
    from origami.utils.secret import get_short_hash

    item_list = [
        ["MassSpectra/Summed Spectrum", "Title", get_short_hash()],
        ["MassSpectra/rt=0-15", "Title", get_short_hash()],
        ["MassSpectra/rt=41-42", "Title", get_short_hash()],
        ["Chromatograms/Summed Chromatogram", "Title", get_short_hash()],
        ["Mobilogram/Summed Chromatogram", "Title", get_short_hash()],
        ["IonHeatmaps/Summed Heatmap", "Title", get_short_hash()],
        ["IonHeatmaps/Summed Heatmap", "Title2", get_short_hash()],
    ]

    app = wx.App()
    ex = PanelInteractiveEditor(None, None, item_list=item_list)
    ex.Show()
    # move_to_different_screen(ex)
    app.MainLoop()


if __name__ == "__main__":
    _main()
