"""Panel responsible for creating interactive layouts"""
# Standard library imports
import logging
from typing import Dict
from typing import List

# Third-party imports
import wx
from pubsub import pub

# Local imports
from origami.styles import MiniFrame
from origami.config.config import CONFIG
from origami.config.environment import ENV
from origami.gui_elements.mixins import DatasetMixin
from origami.gui_elements.mixins import ColorGetterMixin
from origami.gui_elements.helpers import TableConfig
from origami.gui_elements.helpers import set_tooltip
from origami.gui_elements.helpers import make_checkbox
from origami.gui_elements.helpers import make_bitmap_btn
from origami.visuals.bokeh.layout import BaseLayout
from origami.visuals.bokeh.document import Tab
from origami.visuals.bokeh.document import PlotStore
from origami.gui_elements.panel_base import TableMixin
from origami.visuals.bokeh.plot_base import PlotBase
from origami.widgets.interactive.panel_layout import PUB_EVENT_LAYOUT_UPDATE
from origami.widgets.interactive.panel_layout import PanelLayout

LOGGER = logging.getLogger(__name__)


class TableColumnIndex:
    """Table indexer"""

    check = 0
    name = 1
    document_title = 2
    dataset_type = 3
    layout = 4
    dataset_name = 5
    tag = 6


class PanelInteractiveEditor(MiniFrame, TableMixin, ColorGetterMixin, DatasetMixin):
    """Editor panel"""

    # peaklist parameters
    TABLE_CONFIG = TableConfig()
    TABLE_CONFIG.add("", "check", "bool", 25, hidden=True)
    TABLE_CONFIG.add("name", "name", "str", 150)
    TABLE_CONFIG.add("document", "document_title", "str", 100)
    TABLE_CONFIG.add("type", "dataset_type", "str", 150)
    TABLE_CONFIG.add("tab/layout", "layout", "str", 150)
    TABLE_CONFIG.add("full name", "dataset_name", "str", 0, hidden=True)
    # TABLE_CONFIG.add("color", "color", "color", 0, hidden=True)
    TABLE_CONFIG.add("tag", "tag", "str", 0, hidden=True)
    TABLE_COLUMN_INDEX = TableColumnIndex()
    # TABLE_KWARGS = dict(
    #     add_item_color=True,
    #     color_in_column=True,
    #     color_column_id=TABLE_CONFIG.find_col_id("color"),
    #     color_in_column_255=True,
    # )
    TABLE_USE_COLOR = False
    TABLE_WIDGET_DICT = None

    HELP_LINK = "https://origami.lukasz-migas.com/"

    # ui elements
    document_title_value, dataset_name_value, div_title, div_header = None, None, None, None
    div_footer, tab_layout_value, output_title_value, output_path = None, None, None, None
    output_path_btn, html_editor_btn, export_btn, close_btn = None, None, None, None
    open_in_browser_check, remove_watermark_check, add_offline_support_check = None, None, None

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

        # presets
        self._disable_table_update = None
        self._debug = debug
        self.item_list = item_list
        self.plot_store = PlotStore()

        self.make_gui()
        self.on_populate_item_list(None)
        self.setup()

    def setup(self):
        """Setup"""
        self._dataset_mixin_setup()
        pub.subscribe(self.evt_layout_choice_update, PUB_EVENT_LAYOUT_UPDATE)

    def on_close(self, evt, force: bool = False):
        """Close window"""
        try:
            pub.unsubscribe(self.evt_layout_choice_update, PUB_EVENT_LAYOUT_UPDATE)
            LOGGER.debug("Unsubscribed from events")
        except Exception as err:
            LOGGER.error("Failed to unsubscribe events: %s" % err)

        self._dataset_mixin_teardown()
        super(PanelInteractiveEditor, self).on_close(evt, force)

    def make_gui(self):
        """Make UI"""

        notebook = self.make_builder_panel()
        editor = self.make_editor_panel()

        # pack elements
        main_sizer = wx.BoxSizer()
        main_sizer.Add(notebook, 1, wx.EXPAND, 5)
        main_sizer.Add(editor, 1, wx.EXPAND, 5)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizer(main_sizer)
        # self.SetSize(self._window_size)
        self.Layout()

        #         self.CenterOnParent()
        self.SetFocus()
        self.Show()

    def make_builder_panel(self):
        """Make side panel responsible for generating layouts"""
        # panel = wx.Panel(self, -1, size=(-1, -1), name="settings")

        notebook = wx.Notebook(self)

        panel_document = self.make_document_panel(notebook)
        notebook.AddPage(panel_document, "Document Builder")

        panel_layout = PanelLayout(notebook, self._icons, self.plot_store)
        notebook.AddPage(panel_layout, "Layout Creator")

        panel_editor = PanelLayout(notebook, self._icons, self.plot_store)
        notebook.AddPage(panel_editor, "Layout Editor")

        return notebook

    def make_document_panel(self, parent):
        """Make side panel responsible for generating document layouts"""
        panel = wx.Panel(parent, -1, size=(-1, -1))

        self.peaklist = self.make_table(self.TABLE_CONFIG, panel)
        self.peaklist.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_select_item)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.peaklist, 1, wx.EXPAND, 3)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)
        panel.Layout()

        return panel

    def make_editor_panel(self):
        """Make side panel responsible for editing object metadata"""
        panel = wx.Panel(self, -1, size=(-1, -1))

        document_title_value = wx.StaticText(panel, -1, "Document:")
        self.document_title_value = wx.StaticText(panel, -1, "")

        dataset_name_value = wx.StaticText(panel, -1, "Dataset name:")
        self.dataset_name_value = wx.StaticText(panel, -1, "")

        div_title = wx.StaticText(panel, -1, "Title:")
        self.div_title = wx.TextCtrl(
            panel, -1, "", size=(-1, -1), style=wx.TE_MULTILINE | wx.TE_WORDWRAP | wx.TE_RICH2, name="div_title"
        )

        div_header = wx.StaticText(panel, -1, "Header:")
        self.div_header = wx.TextCtrl(
            panel, -1, "", size=(-1, 200), style=wx.TE_MULTILINE | wx.TE_WORDWRAP | wx.TE_RICH2, name="div_header"
        )

        div_footer = wx.StaticText(panel, -1, "Footer:")
        self.div_footer = wx.TextCtrl(
            panel, -1, "", size=(-1, 200), style=wx.TE_MULTILINE | wx.TE_WORDWRAP | wx.TE_RICH2, name="div_footer"
        )

        tab_layout_value = wx.StaticText(panel, -1, "Layout:")
        self.tab_layout_value = wx.ComboBox(panel, choices=[], style=wx.CB_READONLY, name="tab_choice")
        self.tab_layout_value.Bind(wx.EVT_COMBOBOX, self.on_set_layout)

        # output
        output_title_value = wx.StaticText(panel, -1, "Document title:")
        self.output_title_value = wx.TextCtrl(panel, -1, CONFIG.interactive_panel_title, style=wx.TE_CHARWRAP)
        self.output_title_value.Bind(wx.EVT_TEXT, self.on_apply)

        output_path = wx.StaticText(panel, -1, "Path:")
        self.output_path = wx.TextCtrl(panel, -1, "", style=wx.TE_CHARWRAP)
        set_tooltip(self.output_path, "Specify output path of the HTML document.")

        self.output_path_btn = make_bitmap_btn(panel, wx.ID_ANY, self._icons.folder)
        self.output_path_btn.Bind(wx.EVT_BUTTON, self.on_get_path)
        set_tooltip(self.output_path_btn, "Select output path of the HTML document.")

        self.html_editor_btn = wx.Button(panel, wx.ID_ANY, "HTML Editor", size=(-1, -1))
        self.html_editor_btn.Bind(wx.EVT_BUTTON, self.on_open_html_editor)
        set_tooltip(self.html_editor_btn, "Opens a web-based HTML editor")

        self.export_btn = wx.Button(panel, wx.ID_ANY, "Export", size=(-1, -1))
        self.export_btn.Bind(wx.EVT_BUTTON, self.on_export_html)
        set_tooltip(self.export_btn, "Save HTML document")

        self.close_btn = wx.Button(panel, wx.ID_ANY, "Close", size=(-1, -1))
        self.close_btn.Bind(wx.EVT_BUTTON, self.on_close)
        set_tooltip(self.close_btn, "Close window")

        btn_sizer = wx.BoxSizer()
        btn_sizer.Add(self.html_editor_btn)
        btn_sizer.Add(self.export_btn)
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
        grid.AddGrowableCol(1, 1)

        grid_2 = wx.GridBagSizer(2, 2)
        n = 0
        grid_2.Add(output_title_value, (n, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid_2.Add(self.output_title_value, (n, 1), (1, 1), flag=wx.EXPAND)
        n += 1
        grid_2.Add(output_path, (n, 0), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid_2.Add(self.output_path, (n, 1), (1, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
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

    def on_get_path(self, _evt):
        """Get directory where to save the data"""
        dlg = wx.FileDialog(self, "Choose an output filename")
        dlg.SetFilename("ORIGAMI.html")
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.output_title_value.SetLabel(path)
            CONFIG.data_folder_path = path

    def on_export_html(self, _evt):
        """Export data in HTML format"""

    def on_open_html_editor(self, _evt):
        """Export data in HTML format"""

    def on_set_layout(self, _evt):
        """Set layout for currently selected object"""
        item_info = self.on_get_item_information()
        plot_obj = self.get_plot_object(item_info)
        if plot_obj is None:
            tab = self.get_tab_object(item_info)

    def on_apply(self, evt):
        """Change config"""
        CONFIG.interactive_panel_title = self.output_title_value.GetValue()
        CONFIG.interactive_panel_open_in_browser = self.open_in_browser_check.GetValue()
        CONFIG.interactive_panel_add_offline_support = self.add_offline_support_check.GetValue()
        CONFIG.interactive_panel_remove_watermark = self.remove_watermark_check.GetValue()
        self._parse_evt(evt)

    def evt_layout_choice_update(self, layout_list):
        """Update list of layout choices"""
        _, layout_list = layout_list
        self.tab_layout_value.Clear()
        self.tab_layout_value.SetItems(layout_list)

    def on_select_item(self, evt):
        """Select item in the table and populate its contents"""
        self._disable_table_update = True
        if hasattr(evt, "GetIndex"):
            self.peaklist.item_id = evt.GetIndex()

        # get metadata contained within the table
        item_info = self.on_get_item_information()

        # get metadata contained within the layout file
        metadata = self.get_plot_object_metadata(item_info)

        # update elements
        self.document_title_value.SetLabel(item_info["document_title"])
        self.dataset_name_value.SetLabel(item_info["dataset_name"])
        self.div_title.SetValue(metadata["div_title"])
        self.div_header.SetValue(metadata["div_header"])
        self.div_footer.SetValue(metadata["div_footer"])
        self._disable_table_update = False

    def on_populate_item_list(self, _evt):
        """Populate item list"""
        item_list = self.item_list
        if not isinstance(item_list, (list, tuple)):
            return
        self.peaklist.DeleteAllItems()
        self._on_populate_item_list(item_list)

    @staticmethod
    def parse_tab(value):
        """Parse value in the format `Tab=; Name=; Tag=;"""

        def _get_value(key):
            return key.split("=")[-1]

        tab_name, tag_name = None, None
        if value.startswith("Tab="):
            tab_name, _, tag_name = value.split("; ")
            tab_name, tag_name = _get_value(tab_name), _get_value(tab_name)
        return tab_name, tag_name

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

    def _on_populate_item_list(self, item_list: List[str]):
        """Populate table with items"""

        for item in item_list:
            # get document and dataset information
            dataset_name, document_title, tag = item
            dataset_type, name = dataset_name.split("/")

            # retrieve any saved metadata
            # metadata = self.get_item_metadata({"document_title": document_title, "dataset_name": dataset_name})

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

    app = wx.App()

    item_list = [
        ["MassSpectra/Summed Spectrum", "Title", get_short_hash()],
        ["MassSpectra/rt=0-15", "Title", get_short_hash()],
        ["MassSpectra/rt=41-42", "Title", get_short_hash()],
        ["Chromatograms/Summed Chromatogram", "Title", get_short_hash()],
        ["Mobilogram/Summed Chromatogram", "Title", get_short_hash()],
        ["IonHeatmaps/Summed Heatmap", "Title", get_short_hash()],
        ["IonHeatmaps/Summed Heatmap", "Title2", get_short_hash()],
    ]

    ex = PanelInteractiveEditor(None, None, item_list=item_list)

    ex.Show()
    # move_to_different_screen(ex)
    app.MainLoop()


if __name__ == "__main__":
    _main()
