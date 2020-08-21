"""Calibration database"""
from origami.gui_elements.helpers import make_bitmap_btn, set_tooltip
from origami.styles import MiniFrame, Validator
from origami.gui_elements.panel_base import TableMixin
from enum import IntEnum
import time
import logging
import wx

from origami.utils.utilities import report_time
from pubsub import pub

LOGGER = logging.getLogger(__name__)


class TableColumnIndex(IntEnum):
    """Table indexer"""

    check = 0
    protein = 1
    mw = 2
    charge = 3
    he_pos = 4
    he_neg = 5
    n2_pos = 6
    n2_neg = 7
    state = 8
    source = 9


class PanelCCSDatabase(MiniFrame, TableMixin):
    """CCS database panel"""

    TABLE_DICT = {
        0: {
            "name": "",
            "tag": "check",
            "type": "bool",
            "show": True,
            "width": 25,
            "order": 0,
            "id": wx.NewIdRef(),
            "hidden": True,
        },
        1: {
            "name": "protein",
            "tag": "protein",
            "type": "str",
            "show": True,
            "width": 150,
            "order": 1,
            "id": wx.NewIdRef(),
        },
        2: {"name": "MW", "tag": "mw", "type": "float", "show": True, "width": 80, "order": 2, "id": wx.NewIdRef()},
        3: {"name": "z", "tag": "charge", "type": "int", "show": True, "width": 50, "order": 3, "id": wx.NewIdRef()},
        4: {
            "name": "He+",
            "tag": "he_pos",
            "type": "float",
            "show": True,
            "width": 60,
            "order": 4,
            "id": wx.NewIdRef(),
        },
        5: {
            "name": "He-",
            "tag": "he_neg",
            "type": "float",
            "show": True,
            "width": 60,
            "order": 5,
            "id": wx.NewIdRef(),
        },
        6: {
            "name": "N2+",
            "tag": "n2_pos",
            "type": "float",
            "show": True,
            "width": 60,
            "order": 6,
            "id": wx.NewIdRef(),
        },
        7: {
            "name": "N2-",
            "tag": "n2_neg",
            "type": "float",
            "show": True,
            "width": 60,
            "order": 7,
            "id": wx.NewIdRef(),
        },
        8: {"name": "state", "tag": "state", "type": "str", "show": True, "width": 60, "order": 8, "id": wx.NewIdRef()},
        9: {
            "name": "source",
            "tag": "source",
            "type": "str",
            "show": True,
            "width": 60,
            "order": 9,
            "id": wx.NewIdRef(),
        },
    }
    TABLE_COLUMN_INDEX = TableColumnIndex
    USE_COLOR = False
    HELP_LINK = "https://origami.lukasz-migas.com/"

    PUB_SUBSCRIBE_UPDATE = "ccs.update.quick"

    def __init__(self, parent, debug: bool = False):
        """Initialize panel"""
        MiniFrame.__init__(self, parent, title="CCS Calibration Builder...", style=wx.DEFAULT_FRAME_STYLE)
        t_start = time.time()
        self.parent = parent

        # initialize gui
        self.make_gui()

        # setup kwargs
        self.unsaved = False
        self._debug = debug

        # bind events
        self.Bind(wx.EVT_CLOSE, self.on_close)
        LOGGER.debug(f"Started-up CCS panel in {report_time(t_start)}")

        self.CenterOnParent()
        self.SetFocus()
        self.SetSize((800, 400))

    def make_panel(self):
        """Make panel"""
        panel = wx.Panel(self, -1, size=(-1, -1), name="settings")

        # make table
        self.peaklist = self.make_table(self.TABLE_DICT, panel)
        self.peaklist.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_select_calibrant_from_table)

        # statusbar
        info_sizer = self.make_statusbar(panel, "right")

        protein_value = wx.StaticText(panel, -1, "Protein")
        self.protein_value = wx.TextCtrl(panel, -1, "")
        # self.mz_value.Bind(wx.EVT_TEXT, self.on_validate_input)

        mw_value = wx.StaticText(panel, -1, "MW (Da)")
        self.mw_value = wx.TextCtrl(panel, -1, "", validator=Validator("floatPos"))
        # self.mw_value.Bind(wx.EVT_TEXT, self.on_validate_input)

        charge_value = wx.StaticText(panel, -1, "Charge (z):")
        self.charge_value = wx.SpinCtrl(panel, -1, "", min=-100, max=100)
        # self.charge_value.Bind(wx.EVT_TEXT, self.on_validate_input)

        he_pos_ccs_value = wx.StaticText(panel, -1, "He+ CCS (Å²):")
        self.he_pos_ccs_value = wx.TextCtrl(panel, -1, "", validator=Validator("floatPos"))
        # self.he_ccs_value.Bind(wx.EVT_TEXT, self.on_validate_input)

        he_neg_ccs_value = wx.StaticText(panel, -1, "He- CCS (Å²):")
        self.he_neg_ccs_value = wx.TextCtrl(panel, -1, "", validator=Validator("floatPos"))
        # self.he_ccs_value.Bind(wx.EVT_TEXT, self.on_validate_input)

        n2_pos_ccs_value = wx.StaticText(panel, -1, "N2+ CCS (Å²):")
        self.n2_pos_ccs_value = wx.TextCtrl(panel, -1, "", validator=Validator("floatPos"))
        # self.he_ccs_value.Bind(wx.EVT_TEXT, self.on_validate_input)

        n2_neg_ccs_value = wx.StaticText(panel, -1, "N2- CCS (Å²):")
        self.n2_neg_ccs_value = wx.TextCtrl(panel, -1, "", validator=Validator("floatPos"))
        # self.he_ccs_value.Bind(wx.EVT_TEXT, self.on_validate_input)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(protein_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.protein_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(mw_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.mw_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(charge_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.charge_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(he_pos_ccs_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.he_pos_ccs_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(he_neg_ccs_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.he_neg_ccs_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(n2_pos_ccs_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.n2_pos_ccs_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(n2_neg_ccs_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.n2_neg_ccs_value, (n, 1), flag=wx.EXPAND)

        # buttons
        self.add_btn = wx.Button(panel, -1, "Add new")
        self.add_btn.Bind(wx.EVT_BUTTON, self.on_add_calibrant)
        set_tooltip(self.add_btn, "Add calibrant to the table")

        self.load_btn = make_bitmap_btn(
            panel, -1, wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_BUTTON, wx.Size(16, 16))
        )
        self.load_btn.Bind(wx.EVT_BUTTON, self.on_load_calibrants)
        set_tooltip(self.load_btn, "Load calibration data from configuration file")

        self.save_btn = make_bitmap_btn(
            panel, -1, wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE, wx.ART_BUTTON, wx.Size(16, 16))
        )
        self.save_btn.Bind(wx.EVT_BUTTON, self.on_save_calibrants)
        set_tooltip(self.save_btn, "Export calibration data to configuration file")

        btn_sizer = wx.BoxSizer()
        btn_sizer.Add(self.add_btn)
        btn_sizer.AddSpacer(5)
        btn_sizer.Add(self.load_btn)
        btn_sizer.AddSpacer(5)
        btn_sizer.Add(self.save_btn)

        # main sizer
        side_sizer = wx.BoxSizer(wx.VERTICAL)
        side_sizer.Add(grid, 1, wx.EXPAND | wx.ALL, 3)
        side_sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 3)
        side_sizer.Add(info_sizer, 0, wx.EXPAND)

        # main sizer
        main_sizer = wx.BoxSizer()
        main_sizer.Add(self.peaklist, 1, wx.EXPAND | wx.ALL, 3)
        main_sizer.Add(side_sizer, 0, wx.EXPAND | wx.ALL, 3)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)
        panel.Layout()

        return panel

    def on_add_calibrant(self, _evt):
        """Add new calibrant to the table and config file"""
        print(self, _evt)
        pub.sendMessage(self.PUB_SUBSCRIBE_UPDATE, calibrant="NAME")

    def on_load_calibrants(self, _evt):
        """Load calibrants from configuration file"""
        print(self, _evt)
        pub.sendMessage(self.PUB_SUBSCRIBE_UPDATE, calibrant="ALL")

    def on_save_calibrants(self, _evt):
        """Save calibrants to configuration file"""
        print(self, _evt)

    def on_select_calibrant_from_table(self, _evt):
        """Select calibrant from the table and populate fields"""
        print(self, _evt)


def _main():

    app = wx.App()
    ex = PanelCCSDatabase(None, debug=True)

    ex.Show()
    app.MainLoop()


if __name__ == "__main__":
    _main()
