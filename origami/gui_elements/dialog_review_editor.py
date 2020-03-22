# Standard library imports
import logging

# Third-party imports
import wx

# Local imports
from origami.styles import Dialog
from origami.styles import ListCtrl
from origami.styles import set_item_font

logger = logging.getLogger(__name__)


class DialogReviewEditor(Dialog):
    """Review dialog"""

    # peaklist list
    _overlay_peaklist = {
        0: {"name": "", "tag": "check", "type": "bool", "width": 20, "show": True},
        1: {"name": "visualisation", "tag": "visualisation", "type": "str", "width": 150, "show": True},
        2: {"name": "name", "tag": "name", "type": "str", "width": 600, "show": True},
    }

    _extraction_peaklist = {
        0: {"name": "", "tag": "check", "type": "bool", "width": 20, "show": True},
        1: {"name": "type", "tag": "type", "type": "str", "width": 150, "show": True},
        2: {"name": "name", "tag": "name", "type": "str", "width": 600, "show": True},
    }

    def __init__(self, parent, presenter, config, item_list, **kwargs):
        Dialog.__init__(self, parent, title="Review items....")
        self.view = parent
        self.presenter = presenter
        self.config = config

        self.output_list = []

        self.review_type = kwargs["review_type"]
        if self.review_type == "overlay":
            self._peaklist_peaklist = self._overlay_peaklist
        elif self.review_type == "extraction":
            self._peaklist_peaklist = self._extraction_peaklist

        self.make_gui()
        self.populate_list(item_list)

        # setup layout
        self.SetSize((800, 500))
        self.Layout()

        self.CentreOnScreen()
        self.Show(True)
        self.SetFocus()

    def on_close(self, evt):
        """Destroy this frame"""
        self.EndModal(wx.ID_NO)

    def on_ok(self, evt):
        self.output_list = self.get_selected_items()
        self.EndModal(wx.ID_OK)

    def make_panel(self):
        panel = wx.Panel(self, -1, size=(-1, -1))

        msg = (
            "Please review the list of items shown below and select items"
            + " which you would \nlike to add to the document.\n"
        )

        info_label = wx.StaticText(panel, -1, msg)
        set_item_font(info_label)

        self.make_listctrl_panel(panel)

        horizontal_line_1 = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)

        self.ok_btn = wx.Button(panel, wx.ID_OK, "Select", size=(-1, 22))
        self.ok_btn.Bind(wx.EVT_BUTTON, self.on_ok)

        self.cancel_btn = wx.Button(panel, wx.ID_OK, "Cancel", size=(-1, 22))
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_close)

        btn_grid = wx.GridBagSizer(2, 2)
        n = 0
        btn_grid.Add(self.ok_btn, (n, 0), flag=wx.ALIGN_CENTER)
        btn_grid.Add(self.cancel_btn, (n, 1), flag=wx.ALIGN_CENTER)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(info_label, 0, wx.ALIGN_CENTER_HORIZONTAL, 10)
        main_sizer.Add(self.peaklist, 1, wx.ALIGN_CENTER_HORIZONTAL, 10)
        main_sizer.Add(horizontal_line_1, 0, wx.ALIGN_CENTER_HORIZONTAL, 10)
        main_sizer.Add(btn_grid, 0, wx.ALIGN_CENTER_HORIZONTAL, 10)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)

        return panel

    def populate_list(self, item_list):

        for item_info in item_list:
            self.peaklist.Append(["", item_info[0], item_info[1]])

        self.peaklist.on_check_all(True)

    def make_listctrl_panel(self, panel):

        self.peaklist = ListCtrl(panel, style=wx.LC_REPORT | wx.LC_VRULES, column_info=self._peaklist_peaklist)
        for col in range(len(self._peaklist_peaklist)):
            item = self._peaklist_peaklist[col]
            order = col
            name = item["name"]
            width = 0
            if item["show"]:
                width = item["width"]
            self.peaklist.InsertColumn(order, name, width=width, format=wx.LIST_FORMAT_CENTER)
            self.peaklist.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))

    def get_selected_items(self):
        item_count = self.peaklist.GetItemCount()

        # generate list of document_title and dataset_name
        item_list = []
        for item_id in range(item_count):
            information = self.on_get_item_information(item_id)
            if information["select"]:
                item_list.append(information["name"])

        return item_list

    def on_get_item_information(self, itemID):
        information = self.peaklist.on_get_item_information(itemID)

        return information
