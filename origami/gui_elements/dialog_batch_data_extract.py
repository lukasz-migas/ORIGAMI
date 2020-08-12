"""Extract data in batch"""
# Standard library imports
import os
import logging
from ast import literal_eval
from enum import IntEnum

# Third-party imports
import wx

# Local imports
from origami.icons.assets import Icons
from origami.handlers.load import LOAD_HANDLER
from origami.objects.document import DocumentGroups
from origami.config.environment import ENV
from origami.gui_elements.helpers import set_tooltip
from origami.handlers.queue_handler import QUEUE
from origami.gui_elements.dialog_review_editor import DialogReviewEditorBase

LOGGER = logging.getLogger(__name__)


class TableColumnIndex(IntEnum):
    """Table indexer"""

    check = 0
    type = 1
    name = 2
    parameters = 3


class DialogBatchDataExtract(DialogReviewEditorBase):
    """Dialog enabling review of items from the overlay panel"""

    # ui elements
    process_btn = None

    TABLE_DICT = {
        0: dict(name="", tag="check", type="bool", width=25, show=True, order=0, id=wx.NewIdRef(), hidden=True),
        1: dict(name="type", tag="type", type="str", width=100, show=True, order=1, id=wx.NewIdRef()),
        2: dict(name="name", tag="name", type="str", width=150, show=True, order=2, id=wx.NewIdRef()),
        3: dict(name="parameters", tag="parameters", type="str", width=380, show=True, order=2, id=wx.NewIdRef()),
    }
    TABLE_COLUMN_INDEX = TableColumnIndex
    REVIEW_MSG = "Please select item(s) that you would like extract."
    TABLE_GET_KEYS = ("type", "name", "parameters")

    def __init__(self, parent, item_list, document_tree=None, document_title: str = None):
        self._icons = Icons()

        super().__init__(parent, item_list)

        self.document_tree = document_tree
        self.document_title = document_title

    def make_buttons(self):
        """Make buttons"""

        self.ok_btn = wx.Button(self, wx.ID_OK, "Extract", size=(-1, -1))
        self.ok_btn.Bind(wx.EVT_BUTTON, self.on_ok)
        set_tooltip(self.ok_btn, "Extract data for selected items")

        self.cancel_btn = wx.Button(self, wx.ID_OK, "Cancel", size=(-1, -1))
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_close)

        btn_grid = wx.BoxSizer()
        btn_grid.Add(self.ok_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        btn_grid.Add(self.cancel_btn, 0, wx.ALIGN_CENTER_VERTICAL)

        return btn_grid

    def on_ok(self, _evt):
        """Override default event"""
        self._output_list = self.get_selected_items()

        if self.document_title is not None:
            self.on_process()
        else:
            LOGGER.warning("Not extracting data")

        self.EndModal(wx.ID_OK)

    def on_process(self):
        """Process object"""
        # # get document object
        document = ENV.on_get_document(self.document_title)
        path = document.get_file_path("main")
        if path is None or not os.path.exists(path):
            raise ValueError("Cannot extract data because path does not exist")

        # iterate over each of the selected items
        for extraction_type, obj_name, parameters in self.output_list:
            parameters = literal_eval(parameters)
            func = None
            if extraction_type == DocumentGroups.MS:
                func = LOAD_HANDLER.waters_im_extract_ms
            elif extraction_type == DocumentGroups.RT:
                func = LOAD_HANDLER.waters_im_extract_rt
            elif extraction_type == DocumentGroups.DT:
                func = LOAD_HANDLER.waters_im_extract_dt
            elif extraction_type == DocumentGroups.HEATMAP:
                func = LOAD_HANDLER.waters_im_extract_heatmap
            elif extraction_type == DocumentGroups.MSDT:
                func = LOAD_HANDLER.waters_im_extract_msdt

            if func is None:
                continue
            # submit job to the queue
            QUEUE.add_call(
                func, (path,), **parameters, func_result=self._on_add_to_document, func_result_args=(obj_name,)
            )

    def _on_add_to_document(self, obj, obj_name):
        """Add object to the document tree in a thread-safe manner"""
        # add data to the document tree
        if obj is not None:
            # set object title
            obj.set_owner((self.document_title, f"{obj.DOCUMENT_KEY}/{obj_name}"))
            # add to document
            obj.flush()
            # add to document tree
            self.document_tree.on_update_document(obj.DOCUMENT_KEY, obj.title, self.document_title)


def _main():
    app = wx.App()
    ex = DialogBatchDataExtract(
        None,
        [
            [DocumentGroups.MS, "CV: 4V; ", str(dict(rt_start=3, rt_end=7))],
            [DocumentGroups.RT, "CV: 4V; ", str(dict(rt_start=3, rt_end=7))],
            [DocumentGroups.DT, "CV: 4V; ", str(dict(rt_start=3, rt_end=7))],
            [DocumentGroups.HEATMAP, "CV: 4V; ", str(dict(rt_start=3, rt_end=7))],
            [DocumentGroups.MSDT, "CV: 4V; ", str(dict(rt_start=3, rt_end=7))],
        ],
    )

    ex.ShowModal()
    app.MainLoop()


if __name__ == "__main__":
    _main()
