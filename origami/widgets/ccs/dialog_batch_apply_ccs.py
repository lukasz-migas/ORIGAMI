"""Utility panel to perform batch `Apply CCS calibration`"""
# Standard library imports
from typing import Dict
from typing import Union

# Third-party imports
import wx

# Local imports
from origami.icons.assets import Icons
from origami.utils.secret import get_short_hash
from origami.config.environment import ENV
from origami.gui_elements.helpers import TableConfig
from origami.gui_elements.helpers import set_tooltip
from origami.gui_elements.helpers import make_bitmap_btn
from origami.handlers.queue_handler import QUEUE
from origami.gui_elements.dialog_review_editor import DialogReviewEditorBase
from origami.widgets.ccs.processing.containers import CCSCalibrationObject


def is_empty(value):
    """Checks whether item has any valid value"""
    if isinstance(value, str):
        if len(value) == 0:
            return False
    return True


def _str_fmt(value, default: Union[str, float, int] = ""):
    if value is None:
        return str(default)
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


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

    TABLE_CONFIG = TableConfig()
    TABLE_CONFIG.add("", "check", "bool", 25, hidden=True)
    TABLE_CONFIG.add("type", "type", "str", 100)
    TABLE_CONFIG.add("name", "name", "str", 275)
    TABLE_CONFIG.add("m/z", "mz", "float", 100)
    TABLE_CONFIG.add("z", "charge", "int", 50)
    TABLE_CONFIG.add("tag", "tag", "str", 0, hidden=True)
    TABLE_COLUMN_INDEX = TableColumnIndex

    REVIEW_MSG = "Please select item(s) that you would like to apply CCS calibration settings to."
    EXTRA_MSG = (
        "Items highlighted in red cannot be processed because they are missing crucial information."
        " Please double-click on an item to rectify it."
    )

    TABLE_GET_KEYS = ("name", "mz", "charge", "tag")
    TABLE_WIDGET_DICT = dict()
    TABLE_USE_COLOR = True

    _disable_table_update = False
    _current_item = None

    # ui elements
    charge_value, mz_value = None, None

    def __init__(
        self,
        parent,
        item_list,
        document_tree=None,
        document_title: str = None,
        calibration_obj: CCSCalibrationObject = None,
    ):
        """Dialog used to batch process ion mobility data objects and apply CCS calibration

        Parameters
        ----------
        parent : MainWindow
            main window of the application
        item_list : List
            list of items to be inserted in the table. It should have the format of:
                [(DATASET_TYPE, ITEM_NAME, M/Z, CHARGE, RANDOM-STRING)]
            the last entry, RANDOM-STRING is essential as it will be used to find items in the table
        document_tree : DocumentTree
            instance of the document tree
        document_title : str
            name of the document
        calibration_obj : CCSCalibrationObject
            calibration object that will be used to apply the CCS conversion
        """
        self._icons = Icons()

        super().__init__(parent, item_list)

        self.document_tree = document_tree
        self.document_title = document_title
        self.calibration_obj = calibration_obj

        self.invalidate_items()
        self.setup()

    def setup(self):
        """Setup widget"""
        self.TABLE_WIDGET_DICT = {self.charge_value: TableColumnIndex.charge, self.mz_value: TableColumnIndex.mz}
        self.peaklist.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_select_item)

    @property
    def data_handling(self):
        """Return handle to `data_processing`"""
        return self.document_tree.data_handling

    @staticmethod
    def is_valid(item_info: Dict) -> bool:
        """Validate input"""
        mz = item_info["mz"]
        charge = item_info["charge"]
        if not isinstance(mz, float) or not mz > 0:
            return False
        if not isinstance(charge, int) or charge in [0, None]:
            return False
        return True

    def data_obj(self, item_id: int):
        """Get current data object"""
        item_info = self.on_get_item_information(item_id)
        document = ENV.on_get_document(self.document_title)
        return document[item_info["name"], True, True]

    def make_buttons(self):
        """Make buttons"""

        # controls
        charge_value = wx.StaticText(self, -1, "Charge (z):")
        self.charge_value = wx.SpinCtrl(self, -1, "", min=-100, max=100, size=(100, -1))
        self.charge_value.Bind(wx.EVT_TEXT, self.on_edit_item)

        mz_value = wx.StaticText(self, -1, "m/z (Da):")
        self.mz_value = wx.TextCtrl(self, -1, "", size=(100, -1))
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

    def on_select_item(self, evt):
        """Select calibrant from the table and populate fields"""
        self._disable_table_update = True
        if hasattr(evt, "GetIndex"):
            self.peaklist.item_id = evt.GetIndex()
        item_info = self.on_get_item_information()
        self.mz_value.SetValue(_str_fmt(item_info["mz"]))
        self.charge_value.SetValue(_str_fmt(item_info["charge"], "0"))
        self._current_item = item_info["tag"]
        self._disable_table_update = False

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
            None, document_title=self.document_title, calibration_obj=self.calibration_obj
        )

    def on_ok(self, _evt):
        """Override default event"""
        self._output_list = self.get_selected_items()

        if self.document_title is not None and self.calibration_obj is not None:
            self.on_process()
        self.EndModal(wx.ID_OK)

    def on_update_data_obj(self):
        """Update data objects with new metadata"""
        for item_id in range(self.n_rows - 1):
            item_info = self.on_get_item_information(item_id)
            if self.is_valid(item_info):
                data_obj = self.data_obj(item_id)
                data_obj.add_metadata(["mz", "charge"], [item_info["mz"], item_info["charge"]])

    def on_process(self):
        """Process object"""
        # get document object
        document = ENV.on_get_document(self.document_title)

        # iterate over each of the selected items
        for object_name, mz, charge, _ in self.output_list:
            obj = document[object_name, True, True]
            obj.add_metadata(["mz", "charge"], [mz, charge])
            QUEUE.add_call(
                obj.apply_ccs_calibration, (self.calibration_obj, mz, charge), func_result=self._on_add_to_document
            )

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
            ["MassSpectrum", "Data 1", "500", "", get_short_hash()],
            ["MassSpectrum", "Data 1", "", "3", get_short_hash()],
            ["MassSpectrum", "Data 1", "500", "3", get_short_hash()],
            ["MassSpectrum", "Data 1", "500", "", get_short_hash()],
            ["MassSpectrum", "Data 1", "500", "", get_short_hash()],
        ],
    )

    ex.ShowModal()
    app.MainLoop()


if __name__ == "__main__":
    _main()
