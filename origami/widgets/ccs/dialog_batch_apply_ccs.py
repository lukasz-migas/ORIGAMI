"""Utility panel to perform batch `Apply CCS calibration`"""
# Standard library imports
from typing import Dict

# Third-party imports
import wx

# Local imports
from origami.icons.assets import Icons
from origami.config.environment import ENV
from origami.gui_elements.helpers import TableConfig
from origami.gui_elements.helpers import set_tooltip
from origami.gui_elements.helpers import make_bitmap_btn
from origami.handlers.queue_handler import QUEUE
from origami.gui_elements.dialog_review_editor import DialogReviewEditorBase


def is_empty(value):
    """Checks whether item has any valid value"""
    if isinstance(value, str):
        if len(value) == 0:
            return False
    return True


class TableColumnIndex:
    """Table indexer"""

    check = 0
    type = 1
    name = 2
    mz = 3
    charge = 4
    tag = 5


class DialogBatchApplyCCSCalibration(DialogReviewEditorBase):
    """Dialog enabling review of items from the overlay panel"""

    # ui elements
    process_btn = None

    TABLE_DICT = TableConfig()
    TABLE_DICT.add("", "check", "bool", 25, hidden=True)
    TABLE_DICT.add("type", "type", "str", 100)
    TABLE_DICT.add("name", "name", "str", 300)
    TABLE_DICT.add("m/z", "mz", "float", 100)
    TABLE_DICT.add("z", "charge", "int", 50)
    TABLE_DICT.add("tag", "tag", "str", 0, hidden=True)
    TABLE_COLUMN_INDEX = TableColumnIndex

    REVIEW_MSG = "Please select item(s) that you would like to apply CCS calibration settings to."
    EXTRA_MSG = (
        "Items highlighted in red cannot be processed because they are missing crucial information."
        " Please double-click on an item to rectify it."
    )

    TABLE_GET_KEYS = ("name", "mz", "charge", "tag")
    TABLE_WIDGET_DICT = dict()
    USE_COLOR = True

    _disable_table_update = False
    _current_item = None

    # ui elements
    charge_value, mz_value = None, None

    def __init__(self, parent, item_list, document_tree=None, document_title: str = None, calibration_name: str = None):
        self._icons = Icons()

        super().__init__(parent, item_list)

        self.document_tree = document_tree
        self.document_title = document_title
        self.calibration_name = calibration_name

        self.invalidate_items()
        self.setup()

    def setup(self):
        """Setup widget"""
        self.TABLE_WIDGET_DICT = {self.charge_value: TableColumnIndex.charge, self.mz_value: TableColumnIndex.mz}
        self.peaklist.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_select_item)

    def on_select_item(self, evt):
        """Select calibrant from the table and populate fields"""
        self._disable_table_update = True
        if hasattr(evt, "GetIndex"):
            self.peaklist.item_id = evt.GetIndex()
        item_info = self.on_get_item_information()
        self.mz_value.SetValue(str(item_info["mz"]))
        self.charge_value.SetValue(str(item_info["charge"]))
        self._current_item = item_info["tag"]
        print(self._current_item, item_info)
        self._disable_table_update = False

    @property
    def data_handling(self):
        """Return handle to `data_processing`"""
        return self.document_tree.data_handling

    @staticmethod
    def is_valid(item: Dict) -> bool:
        """Validate input"""
        mz = item["mz"]
        charge = item["charge"]
        if not isinstance(mz, float) or not mz > 0:
            return False
        if not isinstance(charge, int) or charge in [0, None]:
            return False
        return True

    def make_buttons(self):
        """Make buttons"""

        # controls
        charge_value = wx.StaticText(self, -1, "Charge (z):")
        self.charge_value = wx.SpinCtrl(self, -1, "", min=-100, max=100, size=(60, -1))
        self.charge_value.Bind(wx.EVT_TEXT, self.on_edit_item)

        mz_value = wx.StaticText(self, -1, "m/z (Da):")
        self.mz_value = wx.TextCtrl(self, -1, "", size=(60, -1))
        self.mz_value.Bind(wx.EVT_TEXT, self.on_edit_item)

        control_sizer = wx.BoxSizer()
        control_sizer.Add(charge_value, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 5)
        control_sizer.Add(self.charge_value, 0, wx.ALIGN_CENTER_VERTICAL)
        control_sizer.Add(mz_value, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 5)
        control_sizer.Add(self.mz_value, 0, wx.ALIGN_CENTER_VERTICAL)

        # buttons
        self.ok_btn = wx.Button(self, wx.ID_OK, "Process", size=(-1, -1))
        self.ok_btn.Bind(wx.EVT_BUTTON, self.on_ok)
        set_tooltip(self.ok_btn, "Apply ORIGAMI-MS settings on the selected objects")

        self.cancel_btn = wx.Button(self, wx.ID_OK, "Cancel", size=(-1, -1))
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_close)

        self.process_btn = make_bitmap_btn(self, wx.ID_ANY, self._icons.process_ms, tooltip="Change CCS calibration")
        self.process_btn.Bind(wx.EVT_BUTTON, self.on_open_ccs_calibration_editor)

        btn_sizer = wx.BoxSizer()
        btn_sizer.Add(self.ok_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        btn_sizer.Add(self.cancel_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        btn_sizer.Add(self.process_btn, 0, wx.ALIGN_CENTER_VERTICAL)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(control_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)
        sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)

        return sizer

    def on_edit_item(self, evt):
        """Edit calibrant that is already in the table"""
        # in certain circumstances, it is better not to update the table
        if self._disable_table_update:
            return
        # get ui object that created this event
        obj = evt.GetEventObject()

        # get current item in the table that is being edited
        item_id = self.on_find_item("tag", self._current_item)
        if item_id == -1:
            return

        # get current column
        col_id = self.TABLE_WIDGET_DICT.get(obj, -1)
        if col_id == -1:
            return

        # update item in the table
        self.peaklist.SetItem(item_id, col_id, str(obj.GetValue()))
        self.invalidate_item(item_id)

    def on_open_ccs_calibration_editor(self, _evt):
        """Open MS pre-processing panel"""
        self.document_tree.on_open_ccs_editor(
            None, document_title=self.document_title, calibration_name=self.calibration_name
        )

    def on_ok(self, _evt):
        """Override default event"""
        self._output_list = self.get_selected_items()

        print(self._output_list)

        if self.document_title is not None:
            self.on_process()

        self.EndModal(wx.ID_OK)

    def on_process(self):
        """Process object"""
        # get document object
        document = ENV.on_get_document(self.document_title)

        # iterate over each of the selected items
        for object_name in self.output_list:
            obj = document[object_name, True]
            QUEUE.add_call(obj.apply_origami_ms, (), func_result=self._on_add_to_document)

    def _on_add_to_document(self, obj):
        """Add object to the document tree in a thread-safe manner"""
        # add data to the document tree
        if obj is not None:
            self.document_tree.on_update_document(obj.DOCUMENT_KEY, obj.title, self.document_title)


def _main():
    app = wx.App()
    ex = DialogBatchApplyCCSCalibration(
        None,
        [
            ["MassSpectrum", "Data 1", "500", "", "123"],
            ["MassSpectrum", "Data 1", "", "3", "dasd"],
            ["MassSpectrum", "Data 1", "500", "3", "ada1"],
            ["MassSpectrum", "Data 1", "500", "", "das1231cd"],
            ["MassSpectrum", "Data 1", "500", "", "aaqcxg"],
        ],
    )

    ex.ShowModal()
    app.MainLoop()


if __name__ == "__main__":
    _main()
