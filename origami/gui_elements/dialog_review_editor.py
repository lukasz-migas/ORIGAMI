"""Review panel enabling selection of which item(s) should be saved/removed"""
# Standard library imports
import logging
from enum import IntEnum
from typing import Dict
from typing import List
from typing import Optional

# Third-party imports
import wx

# Local imports
from origami.styles import Dialog
from origami.styles import set_tooltip
from origami.styles import set_item_font
from origami.styles import make_bitmap_btn
from origami.icons.assets import Icons
from origami.gui_elements.panel_base import TableMixin

logger = logging.getLogger(__name__)


class TableColumnIndex(IntEnum):
    """Table indexer"""

    check = 0
    type = 1
    name = 2


class DialogReviewEditorBase(Dialog, TableMixin):
    """Review dialog"""

    # UI elements
    ok_btn = None
    cancel_btn = None
    peaklist = None

    TABLE_COLUMN_INDEX = TableColumnIndex
    TABLE_TEXT_ALIGN = wx.LIST_FORMAT_LEFT
    USE_COLOR = False
    MSG = "Please review the list of items shown below and select items which you would like to add to the document."

    def __init__(self, parent, item_list: List[List[str]]):
        Dialog.__init__(
            self, parent, title="Review items....", style=wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER & ~wx.MAXIMIZE_BOX
        )
        TableMixin.__init__(self)
        self.view = parent

        self._output_list = []

        self.make_gui()
        self.populate_list(item_list)

        # setup layout
        self.SetSize((-1, 500))
        self.Layout()

        self.CentreOnScreen()
        self.Show(True)
        self.SetFocus()
        self.peaklist.Bind(wx.EVT_LIST_ITEM_CHECKED, self.on_set_items)
        self.peaklist.Bind(wx.EVT_LIST_ITEM_UNCHECKED, self.on_set_items)

        self.on_set_items(None)

    def on_close(self, _evt):
        """Destroy this frame"""
        self._output_list = []
        self.EndModal(wx.ID_NO)

    def on_ok(self, _evt):
        """Gracefully close window"""
        self._output_list = self.get_selected_items()
        self.EndModal(wx.ID_OK)

    def make_gui(self):
        """Make and arrange main panel"""

        # make panel
        panel = self.make_panel()
        btn_grid = self.make_buttons()

        # pack element
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(panel, 1, wx.EXPAND, 5)
        main_sizer.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND, 10)
        main_sizer.Add(btn_grid, 0, wx.ALIGN_CENTER_HORIZONTAL, 5)

        # fit layout
        main_sizer.Fit(self)
        self.SetSizerAndFit(main_sizer)
        self.Layout()

    def make_buttons(self):
        """Make buttons"""

        self.ok_btn = wx.Button(self, wx.ID_OK, "Select", size=(-1, 22))
        self.ok_btn.Bind(wx.EVT_BUTTON, self.on_ok)

        self.cancel_btn = wx.Button(self, wx.ID_OK, "Cancel", size=(-1, 22))
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_close)

        btn_grid = wx.GridBagSizer(2, 2)
        n = 0
        btn_grid.Add(self.ok_btn, (n, 0), flag=wx.ALIGN_CENTER)

        btn_grid.Add(self.cancel_btn, (n, 1), flag=wx.ALIGN_CENTER)

        return btn_grid

    def make_panel(self):
        """Make panel"""
        panel = wx.Panel(self, -1, size=(-1, -1))

        info_label = wx.StaticText(panel, -1, self.MSG)
        set_item_font(info_label)

        self.peaklist = self.make_table(self.TABLE_DICT, panel)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(info_label, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        main_sizer.Add(self.peaklist, 1, wx.EXPAND | wx.ALL, 10)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def populate_list(self, item_list):
        """Populate table"""
        for item_info in item_list:
            self.peaklist.Append(["", item_info[0], item_info[1]])

        self.peaklist.on_check_all(True)

    def get_selected_items(self):
        """Get list of selected items"""
        item_count = self.peaklist.GetItemCount()

        # generate list of document_title and dataset_name
        item_list = []
        for item_id in range(item_count):
            information = self.on_get_item_information(item_id)
            if information["select"]:
                item_list.append(information["name"])
        return item_list

    def on_set_items(self, _evt):
        """Set currently selected items"""
        self._output_list = self.get_selected_items()

    @property
    def output_list(self):
        """Return a list of selected items"""
        return self._output_list

    def on_update_document(self, item_id: Optional[int] = None, item_info: Optional[Dict] = None):
        """Update document"""
        pass

    def on_menu_item_right_click(self, evt):
        """Right-click menu"""
        pass

    def on_double_click_on_item(self, evt):
        """Double-click event"""
        pass


class DialogReviewEditorOverlay(DialogReviewEditorBase):
    """Dialog enabling review of items from the overlay panel"""

    TABLE_DICT = {
        0: dict(name="", tag="check", type="bool", width=20, show=True, order=0, id=wx.NewIdRef(), hidden=True),
        1: dict(name="visualisation", tag="type", type="str", width=150, show=True, order=1, id=wx.NewIdRef()),
        2: dict(name="name", tag="name", type="str", width=600, show=True, order=2, id=wx.NewIdRef()),
    }

    def __init__(self, parent, item_list):
        super().__init__(parent, item_list)


class DialogReviewEditorExtract(DialogReviewEditorBase):
    """Dialog enabling review of items from the overlay panel"""

    TABLE_DICT = {
        0: dict(name="", tag="check", type="bool", width=20, show=True, order=0, id=wx.NewIdRef(), hidden=True),
        1: dict(name="type", tag="type", type="str", width=150, show=True, order=1, id=wx.NewIdRef()),
        2: dict(name="name", tag="name", type="str", width=550, show=True, order=2, id=wx.NewIdRef()),
    }

    def __init__(self, parent, item_list):
        super().__init__(parent, item_list)


class DialogReviewProcessHeatmap(DialogReviewEditorBase):
    """Dialog enabling review of items from the overlay panel"""

    # ui elements
    process_btn = None

    TABLE_DICT = {
        0: dict(name="", tag="check", type="bool", width=20, show=True, order=0, id=wx.NewIdRef(), hidden=True),
        1: dict(name="type", tag="type", type="str", width=100, show=True, order=1, id=wx.NewIdRef()),
        2: dict(name="name", tag="name", type="str", width=550, show=True, order=2, id=wx.NewIdRef()),
    }
    MSG = "Please select item(s) that you would like to process and add to the document"

    def __init__(self, parent, item_list, document_tree=None):
        self._icons = Icons()

        super().__init__(parent, item_list)

        self.document_tree = document_tree

    def make_buttons(self):
        """Make buttons"""

        self.ok_btn = wx.Button(self, wx.ID_OK, "Process", size=(-1, 22))
        self.ok_btn.Bind(wx.EVT_BUTTON, self.on_ok)

        self.cancel_btn = wx.Button(self, wx.ID_OK, "Cancel", size=(-1, 22))
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_close)

        self.process_btn = make_bitmap_btn(
            self, wx.ID_ANY, self._icons.process_heatmap, tooltip="Change heatmap pre-processing parameters"
        )
        self.process_btn.Bind(wx.EVT_BUTTON, self.on_open_process_ms_settings)

        btn_grid = wx.BoxSizer(wx.HORIZONTAL)
        btn_grid.Add(self.ok_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        btn_grid.Add(self.cancel_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        btn_grid.Add(self.process_btn, 0, wx.ALIGN_CENTER_VERTICAL)

        return btn_grid

    def on_open_process_ms_settings(self, _evt):
        """Open MS pre-processing panel"""
        self.document_tree.on_open_process_heatmap_settings(disable_plot=True, disable_process=True)


class DialogReviewProcessSpectrum(DialogReviewEditorBase):
    """Dialog enabling review of items from the overlay panel"""

    # ui elements
    process_btn = None

    TABLE_DICT = {
        0: dict(name="", tag="check", type="bool", width=20, show=True, order=0, id=wx.NewIdRef(), hidden=True),
        1: dict(name="type", tag="type", type="str", width=100, show=True, order=1, id=wx.NewIdRef()),
        2: dict(name="name", tag="name", type="str", width=550, show=True, order=2, id=wx.NewIdRef()),
    }
    MSG = "Please select item(s) that you would like to process and add to the document"

    def __init__(self, parent, item_list, document_tree=None):
        self._icons = Icons()

        super().__init__(parent, item_list)

        self.document_tree = document_tree

    def make_buttons(self):
        """Make buttons"""

        self.ok_btn = wx.Button(self, wx.ID_OK, "Process", size=(-1, 22))
        self.ok_btn.Bind(wx.EVT_BUTTON, self.on_ok)
        set_tooltip(self.ok_btn, "Process selected mass spectra")

        self.cancel_btn = wx.Button(self, wx.ID_OK, "Cancel", size=(-1, 22))
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_close)

        self.process_btn = make_bitmap_btn(
            self, wx.ID_ANY, self._icons.process_ms, tooltip="Change MS pre-processing parameters"
        )
        self.process_btn.Bind(wx.EVT_BUTTON, self.on_open_process_ms_settings)

        btn_grid = wx.BoxSizer(wx.HORIZONTAL)
        btn_grid.Add(self.ok_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        btn_grid.Add(self.cancel_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        btn_grid.Add(self.process_btn, 0, wx.ALIGN_CENTER_VERTICAL)

        return btn_grid

    def on_open_process_ms_settings(self, _evt):
        """Open MS pre-processing panel"""
        self.document_tree.on_open_process_ms_settings(disable_plot=True, disable_process=True)


def _main():
    app = wx.App()
    ex = DialogReviewProcessSpectrum(
        None,
        [
            ["Item 1", "Data 1"],
            ["Item 2", "Data 2"],
            ["Item 1", "Data 1"],
            ["Item 2", "Data 2"],
            ["Item 1", "Data 1"],
            ["Item 2", "Data 2"],
            ["Item 1", "Data 1"],
            ["Item 2", "Data 2"],
            ["Item 1", "Data 1"],
            ["Item 2", "Data 2"],
            ["Item 1", "Data 1"],
            ["Item 2", "Data 2"],
            ["Item 1", "Data 1"],
            ["Item 2", "Data 2"],
            ["Item 1", "Data 1"],
            ["Item 2", "Data 2"],
            ["Item 1", "Data 1"],
            ["Item 2", "Data 2"],
            ["Item 1", "Data 1"],
            ["Item 2", "Data 2"],
        ],
    )

    ex.ShowModal()
    app.MainLoop()


if __name__ == "__main__":
    _main()
