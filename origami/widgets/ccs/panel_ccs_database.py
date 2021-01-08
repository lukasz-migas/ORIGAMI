"""Calibration database"""
# Standard library imports
import os
import time
import logging
from typing import List

# Third-party imports
import wx
from pubsub import pub

# Local imports
from origami.styles import MiniFrame
from origami.styles import Validator
from origami.utils.secret import get_short_hash
from origami.config.config import CONFIG
from origami.utils.utilities import report_time
from origami.utils.converters import str2int
from origami.utils.converters import str2num
from origami.utils.exceptions import MessageError
from origami.gui_elements.helpers import TableConfig
from origami.gui_elements.helpers import set_tooltip
from origami.gui_elements.helpers import make_checkbox
from origami.gui_elements.helpers import make_menu_item
from origami.gui_elements.helpers import make_bitmap_btn
from origami.gui_elements.panel_base import TableMixin
from origami.widgets.ccs.ccs_handler import CCS_HANDLER

LOGGER = logging.getLogger(__name__)


def _str_fmt(value):
    if value is None:
        return ""
    return str(value)


class TableColumnIndex:
    """Table indexer"""

    check = 0
    calibrant = 1
    mw = 2
    charge = 3
    mz = 4
    he_pos = 5
    he_neg = 6
    n2_pos = 7
    n2_neg = 8
    state = 9
    source = 10
    name = 11
    COLUMN_COUNT = 11


class PanelCCSDatabase(MiniFrame, TableMixin):
    """CCS database panel"""

    TABLE_CONFIG = TableConfig()
    TABLE_CONFIG.add("", "check", "bool", 25, hidden=True)
    TABLE_CONFIG.add("calibrant", "calibrant", "str", 150)
    TABLE_CONFIG.add("MW", "mw", "float", 60)
    TABLE_CONFIG.add("z", "charge", "int", 50)
    TABLE_CONFIG.add("m/z", "mz", "float", 80)
    TABLE_CONFIG.add("He+", "he_pos", "float", 60)
    TABLE_CONFIG.add("He-", "he_neg", "float", 60)
    TABLE_CONFIG.add("N2+", "n2_pos", "float", 60)
    TABLE_CONFIG.add("N2-", "n2_neg", "float", 60)
    TABLE_CONFIG.add("state", "state", "str", 60)
    TABLE_CONFIG.add("source", "source", "str", 60)
    TABLE_CONFIG.add("name", "name", "str", 0, hidden=True)

    TABLE_COLUMN_INDEX = TableColumnIndex
    TABLE_WIDGET_DICT = dict()
    TABLE_USE_COLOR = False
    HELP_LINK = "https://origami.lukasz-migas.com/"

    PUB_SUBSCRIBE_UPDATE = "ccs.update.quick"
    TIMER_DELAY = 3000  # 3 seconds

    # ui elements
    calibrant_value, mw_value, charge_value, he_pos_ccs_value, he_neg_ccs_value = None, None, None, None, None
    n2_pos_ccs_value, n2_neg_ccs_value, state_value, add_btn, load_btn = None, None, None, None, None
    save_btn, source_value, mz_value, clear_btn, auto_load_check = None, None, None, None, None
    clear_table_btn = None

    def __init__(self, parent, icons=None, hide_on_close: bool = False, debug: bool = False):
        """Initialize panel"""
        MiniFrame.__init__(self, parent, title="CCS Database...", style=wx.DEFAULT_FRAME_STYLE)
        t_start = time.time()
        self.parent = parent
        self._icons = icons

        # initialize gui
        self.make_gui()

        # setup kwargs
        self.hide_on_close = hide_on_close  # controls whether window should be closed or hidden
        self._debug = debug  # flag to skip some checks
        self._cache_db = None  # just a handle to the current data (not updated alongside the table)
        self._disable_table_update = False  # flag to prevent editing events
        self._current_item = None  # specifies which is the currently selected item

        # setup timer so the quick-selection dropdown menu is updated sporadically
        self._timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_update_quick_selection)

        # bind events
        self.Bind(wx.EVT_CLOSE, self.on_close)

        self.CenterOnParent()
        self.SetFocus()
        self.SetSize((1050, 500))

        self.setup()
        LOGGER.debug(f"Started-up CCS Database panel in {report_time(t_start)}")

    def setup(self):
        """Setup widget"""
        self.TABLE_WIDGET_DICT = {
            self.calibrant_value: TableColumnIndex.calibrant,
            self.mw_value: TableColumnIndex.mw,
            self.charge_value: TableColumnIndex.charge,
            self.mz_value: TableColumnIndex.mz,
            self.he_pos_ccs_value: TableColumnIndex.he_pos,
            self.he_neg_ccs_value: TableColumnIndex.he_neg,
            self.n2_pos_ccs_value: TableColumnIndex.n2_pos,
            self.n2_neg_ccs_value: TableColumnIndex.n2_neg,
            self.state_value: TableColumnIndex.state,
            self.source_value: TableColumnIndex.source,
        }

        if CONFIG.ccs_database_panel_load_at_start:
            self._on_load_calibrants(CONFIG.ccs_database_panel_default_db_path)

    def on_close(self, evt, force: bool = False):
        """Close window"""
        if self.hide_on_close and not self._debug and not force:
            self.Hide()
        else:
            self._timer.Stop()
            super(PanelCCSDatabase, self).on_close(evt, force)

    def on_menu_item_right_click(self, evt):
        """Right-click menu in the table"""
        self.peaklist.item_id = evt.GetIndex()
        menu = wx.Menu()
        menu_remove_calibrant = menu.AppendItem(make_menu_item(parent=menu, evt_id=wx.ID_ANY, text="Remove item"))
        menu.AppendSeparator()
        menu_remove_selected = menu.AppendItem(make_menu_item(parent=menu, evt_id=wx.ID_ANY, text="Remove selected"))

        # bind events
        self.Bind(wx.EVT_MENU, self.on_delete_item, menu_remove_calibrant)
        self.Bind(wx.EVT_MENU, self.on_delete_selected, menu_remove_selected)

        self.PopupMenu(menu)
        menu.Destroy()
        self.SetFocus()

    def make_panel(self):
        """Make panel"""
        panel = wx.Panel(self, -1, size=(-1, -1), name="settings")

        # make table
        self.peaklist = self.make_table(self.TABLE_CONFIG, panel)
        self.peaklist.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_select_calibrant_from_table)

        # statusbar
        info_sizer = self.make_statusbar(panel, "right")

        calibrant_value = wx.StaticText(panel, -1, "Calibrant:")
        self.calibrant_value = wx.TextCtrl(panel, -1, "")
        self.calibrant_value.Bind(wx.EVT_TEXT, self.on_edit_calibrant)

        mw_value = wx.StaticText(panel, -1, "MW (Da):")
        self.mw_value = wx.TextCtrl(panel, -1, "", validator=Validator("floatPos"))
        self.mw_value.Bind(wx.EVT_TEXT, self.on_edit_calibrant)

        charge_value = wx.StaticText(panel, -1, "Charge (z):")
        self.charge_value = wx.SpinCtrl(panel, -1, "", min=-100, max=100)
        self.charge_value.Bind(wx.EVT_TEXT, self.on_edit_calibrant)

        mz_value = wx.StaticText(panel, -1, "m/z (Da):")
        self.mz_value = wx.TextCtrl(panel, -1, "")
        self.mz_value.Bind(wx.EVT_TEXT, self.on_edit_calibrant)

        he_pos_ccs_value = wx.StaticText(panel, -1, "He+ CCS (Å²):")
        self.he_pos_ccs_value = wx.TextCtrl(panel, -1, "", validator=Validator("floatPos"))
        self.he_pos_ccs_value.Bind(wx.EVT_TEXT, self.on_edit_calibrant)

        he_neg_ccs_value = wx.StaticText(panel, -1, "He- CCS (Å²):")
        self.he_neg_ccs_value = wx.TextCtrl(panel, -1, "", validator=Validator("floatPos"))
        self.he_neg_ccs_value.Bind(wx.EVT_TEXT, self.on_edit_calibrant)

        n2_pos_ccs_value = wx.StaticText(panel, -1, "N2+ CCS (Å²):")
        self.n2_pos_ccs_value = wx.TextCtrl(panel, -1, "", validator=Validator("floatPos"))
        self.n2_pos_ccs_value.Bind(wx.EVT_TEXT, self.on_edit_calibrant)

        n2_neg_ccs_value = wx.StaticText(panel, -1, "N2- CCS (Å²):")
        self.n2_neg_ccs_value = wx.TextCtrl(panel, -1, "", validator=Validator("floatPos"))
        self.n2_neg_ccs_value.Bind(wx.EVT_TEXT, self.on_edit_calibrant)

        state_value = wx.StaticText(panel, -1, "State:")
        self.state_value = wx.TextCtrl(panel, -1, "")
        self.state_value.Bind(wx.EVT_TEXT, self.on_edit_calibrant)

        source_value = wx.StaticText(panel, -1, "Source:")
        self.source_value = wx.TextCtrl(panel, -1, "")
        self.source_value.Bind(wx.EVT_TEXT, self.on_edit_calibrant)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(calibrant_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.calibrant_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(mw_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.mw_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(charge_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.charge_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(mz_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.mz_value, (n, 1), flag=wx.EXPAND)
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
        n += 1
        grid.Add(state_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.state_value, (n, 1), flag=wx.EXPAND)
        n += 1
        grid.Add(source_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.source_value, (n, 1), flag=wx.EXPAND)

        # buttons
        self.add_btn = wx.Button(panel, -1, "Add new")
        self.add_btn.Bind(wx.EVT_BUTTON, self.on_add_calibrant)
        set_tooltip(self.add_btn, "Add calibrant to the table")

        # buttons
        self.clear_btn = wx.Button(panel, -1, "Clear")
        self.clear_btn.Bind(wx.EVT_BUTTON, self.on_clear_calibrant)
        set_tooltip(self.clear_btn, "Clear calibrant information from the fields above")

        #         icon = wx.ArtProvider.GetBitmap(wx.ART_PLUS, wx.ART_BUTTON, wx.Size(16, 16))
        #         if self._icons:
        #             icon = self._icons.add
        #         self.add_btn = make_bitmap_btn(panel, -1, icon)
        #         self.add_btn.Bind(wx.EVT_BUTTON, self.on_add_calibrant)
        #         set_tooltip(self.add_btn, "Add calibrant to the table")
        #
        #         # buttons
        #         icon = wx.ArtProvider.GetBitmap(wx.ART_DELETE, wx.ART_BUTTON, wx.Size(16, 16))
        #         if self._icons:
        #             icon = self._icons.clear
        #         self.clear_btn = make_bitmap_btn(panel, -1, icon)
        #         self.clear_btn.Bind(wx.EVT_BUTTON, self.on_clear_calibrant)
        #         set_tooltip(self.clear_btn, "Clear calibrant information from the fields above")

        icon = wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_BUTTON, wx.Size(16, 16))
        if self._icons:
            icon = self._icons.folder
        self.load_btn = make_bitmap_btn(panel, -1, icon)
        self.load_btn.Bind(wx.EVT_BUTTON, self.on_load_calibrants)
        set_tooltip(self.load_btn, "Load calibration data from configuration file")

        icon = wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE, wx.ART_BUTTON, wx.Size(16, 16))
        if self._icons:
            icon = self._icons.save
        self.save_btn = make_bitmap_btn(panel, -1, icon)
        self.save_btn.Bind(wx.EVT_BUTTON, self.on_save_calibrants)
        set_tooltip(self.save_btn, "Export calibration data to configuration file")

        icon = wx.ArtProvider.GetBitmap(wx.ART_DELETE, wx.ART_BUTTON, wx.Size(16, 16))
        if self._icons:
            icon = self._icons.bin
        self.clear_table_btn = make_bitmap_btn(panel, -1, icon)
        self.clear_table_btn.Bind(wx.EVT_BUTTON, self.on_delete_all)
        set_tooltip(self.clear_table_btn, "Clear calibration table")

        self.auto_load_check = make_checkbox(panel, "Load default database at start-up")
        self.auto_load_check.SetValue(CONFIG.ccs_database_panel_load_at_start)
        self.auto_load_check.Bind(wx.EVT_CHECKBOX, self.on_apply)

        btn_sizer = wx.BoxSizer()
        btn_sizer.Add(self.add_btn)
        btn_sizer.AddSpacer(5)
        btn_sizer.Add(self.clear_btn)
        btn_sizer.AddSpacer(5)
        btn_sizer.Add(self.load_btn)
        btn_sizer.AddSpacer(5)
        btn_sizer.Add(self.save_btn)
        btn_sizer.AddSpacer(5)
        btn_sizer.Add(self.clear_table_btn)

        # main sizer
        side_sizer = wx.BoxSizer(wx.VERTICAL)
        side_sizer.Add(grid, 1, wx.EXPAND | wx.ALL, 3)
        side_sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 3)
        side_sizer.Add(self.auto_load_check, 0, wx.ALIGN_LEFT)
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

    def on_apply(self, evt):
        """Update config"""
        CONFIG.ccs_database_panel_load_at_start = self.auto_load_check.GetValue()

        if evt is not None:
            evt.Skip()

    def on_add_calibrant(self, _evt):
        """Add new calibrant to the table and config file"""
        calibrant = self.calibrant_value.GetValue()
        mw = str2num(self.mw_value.GetValue())
        charge = str2int(self.charge_value.GetValue())
        mz = str2num(self.mz_value.GetValue())
        he_pos = str2num(self.he_pos_ccs_value.GetValue())
        he_neg = str2num(self.he_neg_ccs_value.GetValue())
        n2_pos = str2num(self.n2_pos_ccs_value.GetValue())
        n2_neg = str2num(self.n2_neg_ccs_value.GetValue())
        state = self.state_value.GetValue()
        source = self.source_value.GetValue()
        name = get_short_hash()

        # check whether user provided the appropriate data
        if not all([calibrant, mw, charge, mz]):
            raise MessageError(
                "Error", "Cannot add calibrant if the `calibrant, mw, charge and m/z` values are not provided"
            )
        if not any([he_pos, he_neg, n2_pos, n2_neg]):
            raise MessageError("Error", "Cannot add calibrant if none of the CCS values have been filled-in")

        # check whether the item already is present in the table

        # add to table
        item_info = {
            "calibrant": calibrant,
            "mw": mw,
            "charge": charge,
            "mz": mz,
            "he_pos": _str_fmt(he_pos),
            "he_neg": _str_fmt(he_neg),
            "n2_pos": _str_fmt(n2_pos),
            "n2_neg": _str_fmt(n2_neg),
            "state": state,
            "source": source,
            "name": name,
        }
        if not self.compare_calibrants(item_info):
            self.on_add_to_table(item_info)
            self._current_item = name
            pub.sendMessage(self.PUB_SUBSCRIBE_UPDATE, _evt=None)

    def compare_calibrants(self, item_info):
        """Compare new item to the last selected item"""
        if self._current_item in ["", None]:
            return False
        item_id = self.on_find_item("name", self._current_item)
        if item_id == -1:
            return False
        _item_info = self.on_get_item_information(item_id)

        # compare several items
        matches = []
        for key in ["calibrant", "mw", "charge", "mz"]:
            matches.append(item_info[key] == _item_info[key])
        return all(matches)

    def on_edit_calibrant(self, evt):
        """Edit calibrant that is already in the table"""
        # in certain circumstances, it is better not to update the table
        if self._disable_table_update:
            return
        # get ui object that created this event
        obj = evt.GetEventObject()

        # get current item in the table that is being edited
        item_id = self.on_find_item("name", self._current_item)
        if item_id == -1:
            return

        # get current column
        col_id = self.TABLE_WIDGET_DICT.get(obj, -1)
        if col_id == -1:
            return

        # update item in the table
        self.peaklist.SetItem(item_id, col_id, str(obj.GetValue()))

        self._timer.Stop()
        self._timer.StartOnce(self.TIMER_DELAY)

    def on_clear_calibrant(self, _evt):
        """Clear calibration info from the text fields"""
        item_info = dict().fromkeys(
            ["calibrant", "mw", "mz", "charge", "he_pos", "he_neg", "n2_pos", "n2_neg", "state", "source", "name"], None
        )
        self._on_set_calibrant_metadata(item_info)

    def on_load_calibrants(self, _evt):
        """Load calibrants from configuration file"""
        dlg = wx.FileDialog(
            self,
            "Open CCS calibration files",
            wildcard="*.csv; *.txt; *.tab",
            style=wx.FD_DEFAULT_STYLE | wx.FD_CHANGE_DIR,
        )
        path = None
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
        dlg.Destroy()

        self._on_load_calibrants(path)

    def _on_load_calibrants(self, path: str):
        """Load calibrants from configuration file"""
        if path is None or not os.path.exists(path):
            LOGGER.warning("Could not load calibration data - does the file exist?")
            return

        calibration_dict = CCS_HANDLER.read_calibration_db(path)
        self.populate_table(calibration_dict)

        pub.sendMessage(self.PUB_SUBSCRIBE_UPDATE, _evt=None)

    def on_save_calibrants(self, _evt):
        """Save calibrants to configuration file"""
        dlg = wx.FileDialog(
            self, "Save CCS calibration files", wildcard="*.csv; *.txt; *.tab", style=wx.FD_SAVE | wx.FD_CHANGE_DIR
        )
        path = None
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
        dlg.Destroy()

        self._on_save_calibrants(path)
        LOGGER.info(f"Saved calibration data to {path}")

    def _on_save_calibrants(self, path: str):
        """Save calibrants to configuration file"""
        n_items = self.n_rows
        calibration_db = []
        for item_id in range(n_items):
            item_info = self.on_get_item_information(item_id)
            calibration_db.append(
                [
                    item_info["calibrant"],
                    item_info["mw"],
                    item_info["charge"],
                    item_info["mz"],
                    item_info["he_pos"],
                    item_info["he_neg"],
                    item_info["n2_pos"],
                    item_info["n2_neg"],
                    item_info["state"],
                    item_info["source"],
                ]
            )

        CCS_HANDLER.write_calibration_db(path, calibration_db)

    def on_select_calibrant_from_table(self, evt):
        """Select calibrant from the table and populate fields"""
        if hasattr(evt, "GetIndex"):
            self.peaklist.item_id = evt.GetIndex()
        item_info = self.on_get_item_information()
        self._on_set_calibrant_metadata(item_info)

    def _on_set_calibrant_metadata(self, item_info):
        """Set calibration data in the table"""
        self._disable_table_update = True
        self.calibrant_value.SetValue(_str_fmt(item_info["calibrant"]))
        self.mw_value.SetValue(_str_fmt(item_info["mw"]))
        self.charge_value.SetValue(_str_fmt(item_info["charge"]))
        self.mz_value.SetValue(_str_fmt(item_info["mz"]))
        self.he_pos_ccs_value.SetValue(_str_fmt(item_info["he_pos"]))
        self.he_neg_ccs_value.SetValue(_str_fmt(item_info["he_neg"]))
        self.n2_pos_ccs_value.SetValue(_str_fmt(item_info["n2_pos"]))
        self.n2_neg_ccs_value.SetValue(_str_fmt(item_info["n2_neg"]))
        self.state_value.SetValue(_str_fmt(item_info["state"]))
        self.source_value.SetValue(_str_fmt(item_info["source"]))
        self._current_item = item_info["name"]
        self._disable_table_update = False

    def populate_table(self, calibration_dict):
        """Populate table with calibrants"""
        n_items = len(calibration_dict["calibrant"])

        # generate new unique hashes for each item so they can be quickly retrieved from the table when editing
        calibration_dict["name"] = [get_short_hash() for _ in range(n_items)]

        for i in range(n_items):
            self.on_add_to_table(
                {
                    "calibrant": calibration_dict["calibrant"][i],
                    "mw": calibration_dict["mw"][i],
                    "charge": calibration_dict["charge"][i],
                    "mz": calibration_dict["mz"][i],
                    "he_pos": calibration_dict["he_pos"][i],
                    "he_neg": calibration_dict["he_neg"][i],
                    "n2_pos": calibration_dict["n2_pos"][i],
                    "n2_neg": calibration_dict["n2_neg"][i],
                    "state": calibration_dict["state"][i],
                    "source": calibration_dict["source"][i],
                    "name": calibration_dict["name"][i],
                }
            )
        self._cache_db = calibration_dict

    def generate_quick_selection(self, gas: str, polarity: str) -> List[str]:
        """Generate quick selection objects

        Parameters
        ----------
        gas : str
            name of the gas that is used in the calibration - should be Helium or Nitrogen
        polarity : str
            name of the polarity used in the calibration - should be Positive or Negative

        Returns
        -------
        quick_selection : List[str]
            list of quick selections with the format ;MW=; z=; m/z=; ccs=;
        """
        if gas == "Helium":
            c_idx, c_key = (
                (TableColumnIndex.he_pos, "he_pos") if polarity == "Positive" else (TableColumnIndex.he_neg, "he_neg")
            )
        else:
            c_idx, c_key = (
                (TableColumnIndex.n2_pos, "n2_pos") if polarity == "Positive" else (TableColumnIndex.n2_neg, "n2_neg")
            )

        # find which indices need processing
        indices = []
        for idx in range(self.n_rows):
            if self.peaklist.GetItemText(idx, c_idx) != "":
                indices.append(idx)

        # actually generate quick selection
        quick_selection = []
        for item_id in indices:
            item_info = self.on_get_item_information(item_id)
            quick_item = (
                f"{item_info['calibrant']}; MW={item_info['mw']}; "
                f"z={item_info['charge']}; m/z={item_info['mz']}; ccs={item_info[c_key]};"
            )
            quick_selection.append(quick_item)

        return quick_selection

    def on_update_quick_selection(self, _evt):
        """Send trigger to update quick selection"""
        if not self._timer.IsRunning():
            pub.sendMessage(self.PUB_SUBSCRIBE_UPDATE, _evt=None)


def _main():

    from origami.app import App

    app = App()
    ex = PanelCCSDatabase(None, debug=True)

    ex.Show()
    app.MainLoop()


if __name__ == "__main__":
    _main()
