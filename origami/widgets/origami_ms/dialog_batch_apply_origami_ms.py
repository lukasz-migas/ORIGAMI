"""Batch application of ORIGAMI-MS parameters"""
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


class DialogReviewApplyOrigamiMs(DialogReviewEditorBase):
    """Dialog enabling review of items from the overlay panel"""

    # ui elements
    process_btn = None

    TABLE_CONFIG = TableConfig()
    TABLE_CONFIG.add("", "check", "bool", 25, hidden=True)
    TABLE_CONFIG.add("type", "type", "str", 100)
    TABLE_CONFIG.add("name", "name", "str", 550)

    REVIEW_MSG = "Please select item(s) that you would like to apply ORIGAMI-MS settings to."

    def __init__(self, parent, item_list, document_tree=None, document_title: str = None):
        self._icons = Icons()

        super().__init__(parent, item_list)

        self.document_tree = document_tree
        self.document_title = document_title

    @property
    def data_handling(self):
        """Return handle to `data_processing`"""
        return self.document_tree.data_handling

    def make_buttons(self):
        """Make buttons"""

        self.ok_btn = wx.Button(self, wx.ID_OK, "Process", size=(-1, -1))
        self.ok_btn.Bind(wx.EVT_BUTTON, self.on_ok)
        set_tooltip(self.ok_btn, "Apply ORIGAMI-MS settings on the selected objects")

        self.cancel_btn = wx.Button(self, wx.ID_OK, "Cancel", size=(-1, -1))
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_close)

        self.process_btn = make_bitmap_btn(
            self, wx.ID_ANY, self._icons.process_ms, tooltip="Change ORIGAMI-MS settings"
        )
        self.process_btn.Bind(wx.EVT_BUTTON, self.on_open_origami_ms_settings)

        btn_grid = wx.BoxSizer()
        btn_grid.Add(self.ok_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        btn_grid.Add(self.cancel_btn, 0, wx.ALIGN_CENTER_VERTICAL)
        btn_grid.Add(self.process_btn, 0, wx.ALIGN_CENTER_VERTICAL)

        return btn_grid

    def on_open_origami_ms_settings(self, _evt):
        """Open MS pre-processing panel"""
        self.document_tree.on_action_origami_ms(None, document_title=self.document_title)

    def on_ok(self, _evt):
        """Override default event"""
        self._output_list = self.get_selected_items()

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

    from origami.app import App

    app = App()
    ex = DialogReviewApplyOrigamiMs(
        None, [["MassSpectrum", "Data 1"], ["MassSpectrum", "Data 1"], ["MassSpectrum", "Data 1"]]
    )

    ex.ShowModal()
    app.MainLoop()


if __name__ == "__main__":
    _main()
