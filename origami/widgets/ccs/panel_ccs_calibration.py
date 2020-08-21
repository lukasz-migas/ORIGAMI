"""Panel for preparing CCS calibration data"""
# Standard library imports
import os
import time
import logging
from enum import IntEnum
from typing import Dict

# Third-party imports
import wx
import numpy as np
from pubsub import pub

# Local imports
from origami.styles import MiniFrame
from origami.styles import Validator
from origami.utils.secret import get_short_hash
from origami.config.config import CONFIG
from origami.handlers.load import LOAD_HANDLER
from origami.utils.utilities import report_time
from origami.utils.converters import str2int
from origami.utils.converters import str2num
from origami.utils.exceptions import MessageError
from origami.config.environment import ENV
from origami.config.environment import DOCUMENT_WATERS_FILE_FORMATS
from origami.objects.containers import MobilogramObject
from origami.objects.containers import MassSpectrumObject
from origami.gui_elements.mixins import DatasetMixin
from origami.gui_elements.mixins import ConfigUpdateMixin
from origami.gui_elements.helpers import set_tooltip
from origami.gui_elements.helpers import set_item_font
from origami.gui_elements.helpers import make_bitmap_btn
from origami.widgets.ccs.view_ccs import ViewCCSFit
from origami.widgets.ccs.view_ccs import ViewCCSMobilogram
from origami.gui_elements.panel_base import TableMixin
from origami.gui_elements.views.view_register import VIEW_REG
from origami.gui_elements.views.view_spectrum import ViewMassSpectrum
from origami.widgets.ccs.processing.containers import CalibrationIndex
from origami.widgets.ccs.processing.calibration import CCSCalibrationProcessor

LOGGER = logging.getLogger(__name__)

# TODO: add table with list of proteins + their molecular weights
# TODO: add table where users specify preset calibrants
# TODO: add table which shows all calibration data (editable)
# TODO: restore calibration data
# TODO: save dt data alongside calibration data
# TODO: add __call__ func to calibration


class TableColumnIndex(IntEnum):
    """Table indexer"""

    check = 0
    mz = 1
    mw = 2
    charge = 3
    dt = 4
    ccs = 5
    name = 6
    path = 7


class PanelCCSCalibration(MiniFrame, TableMixin, DatasetMixin, ConfigUpdateMixin):
    """CCS panel"""

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
        1: {"name": "m/z", "tag": "mz", "type": "float", "show": True, "width": 80, "order": 1, "id": wx.NewIdRef()},
        2: {"name": "MW", "tag": "mw", "type": "float", "show": True, "width": 80, "order": 2, "id": wx.NewIdRef()},
        3: {"name": "z", "tag": "charge", "type": "int", "show": True, "width": 50, "order": 3, "id": wx.NewIdRef()},
        4: {"name": "dt", "tag": "dt", "type": "float", "show": True, "width": 70, "order": 4, "id": wx.NewIdRef()},
        5: {"name": "ccs", "tag": "ccs", "type": "float", "show": True, "width": 80, "order": 5, "id": wx.NewIdRef()},
        6: {
            "name": "name",
            "tag": "name",
            "type": "str",
            "width": 0,
            "show": False,
            "order": 6,
            "id": wx.NewIdRef(),
            "hidden": True,
        },
        7: {
            "name": "path",
            "tag": "path",
            "type": "str",
            "width": 0,
            "show": False,
            "order": 7,
            "id": wx.NewIdRef(),
            "hidden": True,
        },
    }
    TABLE_COLUMN_INDEX = TableColumnIndex
    USE_COLOR = False
    PANEL_BASE_TITLE = "CCS Calibration Builder"
    HELP_LINK = "https://origami.lukasz-migas.com/"

    PUB_SUBSCRIBE_MZ_GET_EVENT = "ccs.extract.ms"
    PUB_SUBSCRIBE_DT_GET_EVENT = "ccs.extract.dt"

    # ui elements
    view_mz, view_dt, view_fit, peaklist, quick_selection_choice, mz_value = None, None, None, None, None, None
    mw_value, charge_value, dt_value, ccs_value, add_calibrant_btn = None, None, None, None, None
    remove_calibrant_btn, gas_choice, reset_btn, save_btn, calculate_ccs_btn = None, None, None, None, None
    file_path_choice, load_file_btn, action_btn, load_document_btn = None, None, None, None
    auto_process_btn, correction_value, mw_auto_btn = None, None, None

    # attributes
    _mz_obj = None
    _dt_obj = None
    _cache = dict()
    _tmp_cache = dict()
    _ccs_obj = None

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
        self.Bind(wx.EVT_CONTEXT_MENU, self.on_right_click)
        LOGGER.debug(f"Started-up CCS panel in {report_time(t_start)}")

        self.CenterOnParent()
        self.SetFocus()
        self.SetSize((1200, 800))

        # setup window
        self.setup()

    @property
    def mz_obj(self) -> MassSpectrumObject:
        """Mass spectrum object"""
        return self._mz_obj

    @mz_obj.setter
    def mz_obj(self, value):
        if isinstance(value, MassSpectrumObject):
            self._mz_obj = value
            self.on_plot_ms()

    @property
    def dt_obj(self) -> MobilogramObject:
        """Mass spectrum object"""
        return self._dt_obj

    @dt_obj.setter
    def dt_obj(self, value):
        if isinstance(value, MobilogramObject):
            self._dt_obj = value
            self.on_plot_dt()

    @property
    def current_path(self):
        """Return path to current raw file"""
        filename = self.file_path_choice.GetStringSelection()
        if filename:
            path = self._cache[filename]
            return path

    @property
    def pusher_frequency(self):
        """Retrieves pusher frequency for the currently selected raw file"""
        pusher_freq = self._cache[self.current_path]["metadata"]["pusher_freq"]
        return pusher_freq

    @property
    def correction_factor(self):
        """Retrieve correction factor for the currently selected raw file"""
        correction_factor = self._cache[self.current_path]["metadata"]["correction_c"]
        return correction_factor

    @property
    def gas_mw(self):
        """Retrieve the gas molecular weight"""
        gas = self.gas_choice.GetStringSelection()
        return {"Helium": 4.002602, "Nitrogen": 28.0134}[gas]

    def setup(self):
        """Setup window"""
        self._config_mixin_setup()
        self._dataset_mixin_setup()

        # add listeners
        pub.subscribe(self.evt_extract_dt_from_ms, self.PUB_SUBSCRIBE_MZ_GET_EVENT)
        pub.subscribe(self.evt_select_conformation, self.PUB_SUBSCRIBE_DT_GET_EVENT)

        self.on_validate_input(None)

    def on_close(self, evt, force: bool = False):
        """Close window"""
        try:
            pub.unsubscribe(self.evt_extract_dt_from_ms, self.PUB_SUBSCRIBE_MZ_GET_EVENT)
            pub.unsubscribe(self.evt_select_conformation, self.PUB_SUBSCRIBE_DT_GET_EVENT)
        except Exception as err:
            LOGGER.error("Failed to unsubscribe events: %s" % err)

        self._config_mixin_teardown()
        self._dataset_mixin_teardown()
        super(PanelCCSCalibration, self).on_close(evt, force)

    def on_plot_ms(self):
        """Plot mass spectrum"""
        mz_obj = self.mz_obj
        if mz_obj:
            self.view_mz.plot(obj=mz_obj)

    def on_plot_dt(self):
        """Plot mobilogram"""
        dt_obj = self.dt_obj
        if dt_obj:
            self.view_dt.plot(obj=dt_obj)

    def on_right_click(self, evt):
        """Right-click menu"""
        if hasattr(evt.EventObject, "figure"):
            view = VIEW_REG.view
            menu = view.get_right_click_menu(self)

            self.PopupMenu(menu)
            menu.Destroy()
            self.SetFocus()

    def make_panel(self):
        """Make panel"""
        panel = wx.Panel(self, -1, size=(-1, -1), name="settings")

        # mass spectrum
        self.view_mz = ViewMassSpectrum(
            panel,
            (6, 3),
            CONFIG,
            allow_extraction=True,
            callbacks=dict(CTRL=self.PUB_SUBSCRIBE_MZ_GET_EVENT),
            filename="mass-spectrum",
        )

        # mobilogram
        self.view_dt = ViewCCSMobilogram(
            panel,
            (6, 3),
            CONFIG,
            allow_extraction=True,
            callbacks=dict(CTRL=self.PUB_SUBSCRIBE_DT_GET_EVENT),
            filename="molecular-weight",
        )

        # fit
        self.view_fit = ViewCCSFit(
            panel, (4, 2), CONFIG, allow_extraction=False, filename="ccs-fit", axes_size=(0.15, 0.25, 0.8, 0.65)
        )

        # data selection
        self.file_path_choice = wx.Choice(panel, -1)
        self.file_path_choice.Bind(wx.EVT_CHOICE, self.on_select_file)

        self.load_file_btn = wx.Button(panel, -1, "Load")
        self.load_file_btn.Bind(wx.EVT_BUTTON, self.on_load_file)

        self.load_document_btn = make_bitmap_btn(
            panel, -1, wx.ArtProvider.GetBitmap(wx.ART_FOLDER_OPEN, wx.ART_BUTTON, wx.Size(16, 16))
        )
        self.load_document_btn.Bind(wx.EVT_BUTTON, self.on_open_document)

        self.auto_process_btn = wx.Button(panel, -1, "Auto-process")
        self.auto_process_btn.Bind(wx.EVT_BUTTON, self.on_auto_process)

        gas_choice = wx.StaticText(panel, -1, "Gas:")
        self.gas_choice = wx.Choice(panel, -1, choices=["Nitrogen", "Helium"])
        self.gas_choice.SetStringSelection("Nitrogen")
        self.gas_choice.Bind(wx.EVT_CHOICE, self.on_apply)

        correction_factor = wx.StaticText(panel, -1, "Correction factor:")
        self.correction_value = wx.TextCtrl(panel, -1, "", validator=Validator("floatPos"))
        self.correction_value.Bind(wx.EVT_TEXT, self.on_apply)
        set_tooltip(
            self.correction_value,
            "Instruments Enhanced Duty Cycle (EDC) delay coefficient. Automatically loaded from the raw file",
        )

        # item settings
        quick_selection = wx.StaticText(panel, -1, "Quick selection:")
        self.quick_selection_choice = wx.Choice(panel, -1)
        self.quick_selection_choice.Bind(wx.EVT_CHOICE, self.on_quick_selection)

        self.action_btn = make_bitmap_btn(
            panel, -1, wx.ArtProvider.GetBitmap(wx.ART_LIST_VIEW, wx.ART_BUTTON, wx.Size(16, 16))
        )
        self.action_btn.Bind(wx.EVT_BUTTON, self.on_open_calibrant_panel)

        mz_value = wx.StaticText(panel, -1, "m/z")
        self.mz_value = wx.TextCtrl(panel, -1, "", validator=Validator("floatPos"))
        self.mz_value.Bind(wx.EVT_TEXT, self.on_validate_input)

        mw_value = wx.StaticText(panel, -1, "MW (Da)")
        self.mw_value = wx.TextCtrl(panel, -1, "", validator=Validator("floatPos"))
        self.mw_value.Bind(wx.EVT_TEXT, self.on_validate_input)

        self.mw_auto_btn = make_bitmap_btn(
            panel, -1, wx.ArtProvider.GetBitmap(wx.ART_PASTE, wx.ART_BUTTON, wx.Size(16, 16))
        )
        self.mw_auto_btn.Bind(wx.EVT_BUTTON, self.on_auto_set_mw)

        charge_value = wx.StaticText(panel, -1, "Charge (z):")
        self.charge_value = wx.SpinCtrl(panel, -1, "", min=-100, max=100)
        self.charge_value.Bind(wx.EVT_TEXT, self.on_validate_input)

        dt_value = wx.StaticText(panel, -1, "DT (ms):")
        self.dt_value = wx.TextCtrl(panel, -1, "", validator=Validator("floatPos"))
        self.dt_value.Bind(wx.EVT_TEXT, self.on_validate_input)

        ccs_value = wx.StaticText(panel, -1, "CCS (Å²):")
        self.ccs_value = wx.TextCtrl(panel, -1, "", validator=Validator("floatPos"))
        self.ccs_value.Bind(wx.EVT_TEXT, self.on_validate_input)

        self.add_calibrant_btn = wx.Button(panel, -1, "Add")
        self.add_calibrant_btn.Bind(wx.EVT_BUTTON, self.on_add_calibrant)

        self.remove_calibrant_btn = wx.Button(panel, -1, "Remove")
        self.remove_calibrant_btn.Bind(wx.EVT_BUTTON, self.on_remove_calibrant)

        add_calibrant_label = wx.StaticText(panel, -1, "Add calibrant")
        set_item_font(add_calibrant_label)

        grid = wx.GridBagSizer(2, 2)
        n = 0
        grid.Add(self.file_path_choice, (n, 0), (1, 3), flag=wx.EXPAND)
        grid.Add(self.load_file_btn, (n, 3), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.load_document_btn, (n, 4), flag=wx.ALIGN_CENTER_VERTICAL)
        n += 1
        grid.Add(correction_factor, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.correction_value, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(gas_choice, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.gas_choice, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        grid.Add(self.auto_process_btn, (n, 3), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        n += 1
        grid.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), (n, 0), (1, 5), flag=wx.EXPAND)
        n += 1
        grid.Add(add_calibrant_label, (n, 0), (1, 5), flag=wx.ALIGN_CENTER_HORIZONTAL)
        n += 1
        grid.Add(quick_selection, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.quick_selection_choice, (n, 1), (1, 3), flag=wx.EXPAND)
        grid.Add(self.action_btn, (n, 4), flag=wx.ALIGN_CENTER_VERTICAL)
        n += 1
        grid.Add(mz_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.mz_value, (n, 1), flag=wx.EXPAND)
        grid.Add(mw_value, (n, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.mw_value, (n, 3), flag=wx.EXPAND)
        grid.Add(self.mw_auto_btn, (n, 4), flag=wx.ALIGN_CENTER_VERTICAL)
        n += 1
        grid.Add(charge_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.charge_value, (n, 1), flag=wx.EXPAND)
        grid.Add(dt_value, (n, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.dt_value, (n, 3), flag=wx.EXPAND)
        n += 1
        grid.Add(ccs_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.ccs_value, (n, 1), flag=wx.EXPAND)
        grid.Add(self.add_calibrant_btn, (n, 2), flag=wx.EXPAND)
        grid.Add(self.remove_calibrant_btn, (n, 3), flag=wx.EXPAND)

        # calculate settings
        self.calculate_ccs_btn = wx.Button(panel, -1, "Calculate")
        self.calculate_ccs_btn.Bind(wx.EVT_BUTTON, self.on_create_calibration)

        self.save_btn = wx.Button(panel, -1, "Save")
        self.save_btn.Bind(wx.EVT_BUTTON, self.on_save_calibration)

        self.reset_btn = wx.Button(panel, -1, "Reset")
        self.reset_btn.Bind(wx.EVT_BUTTON, self.on_reset_calibration)

        btn_sizer = wx.BoxSizer()
        btn_sizer.Add(self.calculate_ccs_btn)
        btn_sizer.AddSpacer(5)
        btn_sizer.Add(self.save_btn)
        btn_sizer.AddSpacer(5)
        btn_sizer.Add(self.reset_btn)

        calculate_label = wx.StaticText(panel, -1, "Calculate CCS")
        set_item_font(calculate_label)

        # make table
        self.peaklist = self.make_table(self.TABLE_DICT, panel)
        self.peaklist.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_select_calibrant_from_table)

        # statusbar
        info_sizer = self.make_statusbar(panel, "right")

        # settings sizer
        side_sizer = wx.BoxSizer(wx.VERTICAL)
        side_sizer.Add(grid, 0, wx.EXPAND)
        side_sizer.Add(self.peaklist, 1, wx.EXPAND)
        side_sizer.AddSpacer(3)
        side_sizer.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND)
        side_sizer.Add(calculate_label, 0, wx.ALIGN_CENTER_HORIZONTAL)
        side_sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL)
        side_sizer.AddSpacer(3)
        side_sizer.Add(self.view_fit.panel, 1, wx.EXPAND)
        side_sizer.Add(info_sizer, 0, wx.EXPAND)
        # plot sizer
        plot_sizer = wx.BoxSizer(wx.VERTICAL)
        plot_sizer.Add(self.view_mz.panel, 1, wx.EXPAND)
        plot_sizer.Add(self.view_dt.panel, 1, wx.EXPAND)

        # main sizer
        main_sizer = wx.BoxSizer()
        main_sizer.Add(plot_sizer, 1, wx.EXPAND | wx.ALL, 3)
        main_sizer.Add(side_sizer, 0, wx.EXPAND | wx.ALL, 3)

        # fit layout
        main_sizer.Fit(panel)
        panel.SetSizerAndFit(main_sizer)
        panel.Layout()

        return panel

    def on_validate_input(self, evt):
        """Update text box color"""
        bad_color, good_color = (255, 230, 239), wx.WHITE

        self.mz_value.SetBackgroundColour(good_color if self.mz_value.GetValue() else bad_color)
        self.mz_value.Refresh()

        self.mw_value.SetBackgroundColour(good_color if self.mw_value.GetValue() else bad_color)
        self.mw_value.Refresh()

        value = self.charge_value.GetValue()
        color = bad_color if value in [None, "", 0] else good_color
        self.charge_value.SetBackgroundColour(color)
        self.charge_value.Refresh()

        self.dt_value.SetBackgroundColour(good_color if self.dt_value.GetValue() else bad_color)
        self.dt_value.Refresh()

        self.ccs_value.SetBackgroundColour(good_color if self.ccs_value.GetValue() else bad_color)
        self.ccs_value.Refresh()

        if evt is not None:
            evt.Skip()

    def on_load_file(self, _evt):
        """Select Waters .raw directory"""
        # get directory
        path = None
        dlg = wx.DirDialog(wx.GetTopLevelParent(self), "Choose a Waters (.raw) directory")
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
        dlg.Destroy()

        # load data
        if path is not None:
            metadata = LOAD_HANDLER.waters_metadata(path)
            mz_obj = LOAD_HANDLER.waters_im_extract_ms(path)
            self._set_calibration_cache(path, {"mz_obj": mz_obj, "metadata": metadata})

    def on_auto_set_mw(self, _evt):
        """Automatically set molecular weight based on the m/z value and charge"""
        mz_value = str2num(self.mz_value.GetValue())
        charge_value = str2int(self.charge_value.GetValue())
        if not all([mz_value, charge_value]):
            return
        mw = (mz_value - charge_value * 1.00784) * charge_value
        self.mw_value.SetValue(str(mw))

    def on_open_document(self, _evt):
        """Open document or waters file where calibration can be saved to"""
        path = None
        dlg = wx.DirDialog(wx.GetTopLevelParent(self), "Choose a ORIGAMI (.origami) directory store")
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
        dlg.Destroy()

        if path is not None and path.endswith(".origami"):
            ENV.load(path)
            LOGGER.info(f"Loaded ORIGAMI document - {path}")

    def on_quick_selection(self, _evt):
        """Quick selection to fill-in few common parameters"""

    def on_open_calibrant_panel(self, _evt):
        """Open panel where users can create calibration table"""

    def on_auto_process(self, _evt):
        """Auto-process the loaded data"""
        from origami.widgets.ccs.misc_windows import DialogAutoGenerateConformers

        popup = DialogAutoGenerateConformers(self)
        popup.Show()

    def _on_auto_process(self, mw: float, z_start: int, z_end: int, mz_window: float):
        """Auto-process the currently loaded mass spectrum"""
        self.mw_value.SetValue(str(mw))
        self.ccs_value.SetValue("1")
        charges = np.arange(z_start, z_end + 1)[::-1]
        mz_values = mw / charges
        for mz, charge in zip(mz_values, charges):
            self.evt_extract_dt_from_ms([mz - mz_window, mz + mz_window, None, None], None, None)
            self.charge_value.SetValue(str(charge))
            self.on_add_calibrant(None)

    def _simulate_auto_process(self, mw: float, z_start: int, z_end: int, mz_window: float):
        """Simulate auto-processing by highlighting the regions of interest"""
        self.view_mz.remove_patches(False)
        charges = np.arange(z_start, z_end + 1)[::-1]
        mz_values = mw / charges
        for mz, _ in zip(mz_values, charges):
            self.view_mz.add_patch(mz - mz_window, 0, mz_window * 2, 99999999, repaint=False)
        self.view_mz.repaint()

    def _set_calibration_cache(self, path: str, data: Dict):
        """Set calibration data in the cache so it can be easily retrieved later on"""
        # adding new file
        if "mz_obj" in data:
            _, filename = os.path.split(path)

            # set data in cache dict
            self._cache[filename] = path
            self.mz_obj = data["mz_obj"]

            # update list of files
            file_list = self.file_path_choice.GetItems()
            if filename not in file_list:
                self._cache[path] = data
                self._cache[path]["calibrants"] = {}
                file_list.append(filename)
                self.file_path_choice.SetItems(file_list)
                self.file_path_choice.SetStringSelection(filename)
            self.correction_value.SetValue(str(self.correction_factor))
            LOGGER.debug(f"Instantiated `{filename}` mass spectrum")

        # add calibrant to cache
        if "calibrant" in data and "name" in data:
            self._cache[self.current_path]["calibrants"][data["name"]] = data["calibrant"]

    def on_select_file(self, evt):
        """Select file from existing list of files"""
        filename = self.file_path_choice.GetStringSelection()
        mz_obj = self._cache[self.current_path]["mz_obj"]
        self.view_mz.remove_patches(False)
        self.mz_obj = mz_obj
        self.correction_value.SetValue(str(self.correction_factor))

        LOGGER.debug(f"Changed mass spectrum to `{filename}`")
        if evt is not None:
            evt.Skip()

    def on_apply(self, _evt):
        """Make changes to the config"""

    def on_select_calibrant_from_table(self, evt):
        """Select calibrant in the table and show the data"""
        if hasattr(evt, "GetIndex"):
            self.peaklist.item_id = evt.GetIndex()
        item_info = self.on_get_item_information()
        self._on_set_calibrant_metadata(item_info)
        name = item_info["name"]
        path = item_info["path"]

        self._tmp_cache[path] = self._cache[path]["calibrants"][name]
        self._on_show_dt_marker()
        self.dt_obj = self._tmp_cache[path]["dt_obj"]

    def on_add_calibrant(self, _evt):
        """Add calibrant to the table and cache"""
        if self._tmp_cache[self.current_path] is None:
            raise MessageError(
                "Error", "Current cache for this file is empty. Please select new m/z region and ion mobility region."
            )

        mz_value = str2num(self.mz_value.GetValue())
        mw_value = str2num(self.mw_value.GetValue())
        charge_value = str2int(self.charge_value.GetValue())
        dt_value = str2num(self.dt_value.GetValue())
        ccs_value = str2num(self.ccs_value.GetValue())
        if not all([mz_value, mw_value, charge_value, dt_value, ccs_value]):
            raise MessageError("Error", "Cannot add calibrant to the table as some values are missing")

        idx = self.on_find_item("mz", mz_value)
        if idx != -1:
            self.remove_from_table(idx)

        # add to table
        name = get_short_hash()
        self.on_add_to_table(
            dict(
                mz=mz_value,
                mw=mw_value,
                charge=charge_value,
                dt=dt_value,
                ccs=ccs_value,
                name=name,
                path=self.current_path,
            )
        )
        self._tmp_cache[self.current_path].update(
            {"charge": charge_value, "mz": mz_value, "mw": mw_value, "dt": dt_value, "ccs": ccs_value}
        )

        # add to cache
        self._set_calibration_cache(self.current_path, {"calibrant": self._tmp_cache[self.current_path], "name": name})
        self._on_show_mz_patches()
        LOGGER.debug("Added calibrant to the cache")

    def on_remove_calibrant(self, _evt):
        """Remove calibrant from the table and the cache"""
        mz_value = str2num(self.mz_value.GetValue())
        idx = self.on_find_item("mz", mz_value)
        if idx == -1:
            raise MessageError("Error", f"Calibrant ion with the m/z value {mz_value} is not in the table")
        item_info = self.on_get_item_information(idx)
        self.remove_from_table(idx)
        del self._cache[item_info["path"]]["calibrants"][item_info["name"]]
        self._on_show_mz_patches()
        LOGGER.debug("Removed calibrant from the cache")

    def evt_extract_dt_from_ms(self, rect, x_labels, y_labels):  # noqa
        """Extract mobilogram from mass spectrum"""
        mz_min, mz_max, _, _ = rect
        mz_pos, mz_int = self.mz_obj.get_x_at_loc(mz_min, mz_max)
        path = self.current_path
        dt_obj = LOAD_HANDLER.waters_im_extract_dt(path, mz_start=mz_min, mz_end=mz_max)
        dt_obj.change_x_label("Drift time (ms)", self.pusher_frequency)
        dt_pos, dt_int = dt_obj.get_x_at_max()

        # store information about currently plotted mobility object in temporary cache
        self._tmp_cache[path] = {
            "mz_min": mz_min,
            "mz_max": mz_max,
            "mz": mz_pos,
            "mz_int": mz_int,
            "dt_obj": dt_obj,
            "dt": dt_pos,
            "dt_int": dt_int,
        }

        # update plot
        self.dt_obj = dt_obj
        self._on_set_calibrant_metadata(self._tmp_cache[path])
        self._on_show_dt_marker()

    def evt_select_conformation(self, rect, x_labels, y_labels):  # noqa
        """Set calibrant data"""
        dt_min, dt_max, _, _ = rect
        dt_pos, dt_int = self.dt_obj.get_x_at_loc(dt_min, dt_max)
        path = self.current_path
        self._tmp_cache[path]["dt"] = dt_pos
        self._tmp_cache[path]["dt_int"] = dt_int
        self._on_set_calibrant_metadata(self._tmp_cache[path])
        self._on_show_dt_marker()

    def _on_show_dt_marker(self):
        """Update position of marker in the mobilogram"""
        self.view_dt.remove_scatter(repaint=False)
        path = self.current_path
        dt_pos = self._tmp_cache[path]["dt"]
        dt_int = self._tmp_cache[path]["dt_int"]
        self.view_dt.add_scatter(dt_pos, dt_int, size=25)

    def _on_show_mz_patches(self):
        """Show/remove patches from the mass spectrum depending what is in the cache"""
        self.view_mz.remove_patches(False)
        for calibrant in self._cache[self.current_path]["calibrants"].values():
            self.view_mz.add_patch(
                calibrant["mz_min"],
                0,
                calibrant["mz_max"] - calibrant["mz_min"],
                calibrant["mz_int"],
                pickable=False,
                repaint=False,
            )
        self.view_mz.repaint()

    def _on_set_calibrant_metadata(self, cache):
        """Set calibration metadata"""
        if "mz" in cache:
            self.mz_value.SetValue(f"{cache['mz']:.2f}")
        if "mw" in cache:
            self.mw_value.SetValue(f"{cache['mw']:.2f}")
        if "charge" in cache:
            self.charge_value.SetValue(f"{cache['charge']}")
        if "ccs" in cache:
            self.ccs_value.SetValue(f"{cache['ccs']:.2f}")
        if "dt" in cache:
            self.dt_value.SetValue(f"{cache['dt']:.2f}")

    def on_create_calibration(self, _evt):
        """Create calibration curve"""
        selected_indices = self.get_checked_items()
        if not selected_indices:
            raise MessageError(
                "Error", "Cannot create calibration curve with 0 selected items. Please select items in the table."
            )

        self._collect_calibration_data(selected_indices)

    def _collect_calibration_data(self, selected_indices):
        """Collect calibration data"""
        metadata = []
        array = np.zeros((len(selected_indices), 5), dtype=np.float32)
        for i, item_id in enumerate(selected_indices):
            item_info = self.on_get_item_information(item_id)
            path = item_info["path"]
            name = item_info["name"]

            # set calibration data in the output array
            calibrant = self._cache[path]["calibrants"][name]
            array[i, CalibrationIndex.mz] = calibrant["mz"]
            array[i, CalibrationIndex.mw] = calibrant["mw"]
            array[i, CalibrationIndex.charge] = calibrant["charge"]
            array[i, CalibrationIndex.tD] = calibrant["dt"]
            array[i, CalibrationIndex.CCS] = calibrant["ccs"]

            # collect metadata
            metadata.append(
                {
                    "name": name,
                    "path": path,
                    "mz_min": float(calibrant["mz_min"]),
                    "mz_max": float(calibrant["mz_max"]),
                    "mz_int": float(calibrant["mz_int"]),
                    "mz": float(calibrant["mz"]),
                    "dt_int": float(calibrant["dt_int"]),
                    "dt": float(calibrant["dt"]),
                    "charge": int(calibrant["charge"]),
                    "mw": float(calibrant["mw"]),
                    "ccs": float(calibrant["ccs"]),
                }
            )

        calibration = CCSCalibrationProcessor(metadata)
        ccs_obj = calibration.create_calibration(array, self.gas_mw, self.correction_factor)
        self._ccs_obj = calibration
        self.on_show_fit(ccs_obj)

    def on_save_calibration(self, _evt):
        """Save calibration curve in the document"""
        from origami.gui_elements.misc_dialogs import DialogSimpleAsk

        # get name under which the calibration data should be loaded
        calibration_name = DialogSimpleAsk(
            "Please specify name of the calibration", "Calibration name", "CCSCalibration", self
        )
        if calibration_name is None:
            LOGGER.debug("Saving of calibration was cancelled")
            return

        document_list = ENV.get_document_list(document_format=DOCUMENT_WATERS_FILE_FORMATS)
        if not document_list:
            LOGGER.debug("List od documents was empty - cannot save calibration data")
            return

        dlg = wx.MultiChoiceDialog(
            self, "Please select documents where the calibration data should be saved to", "Documents", document_list
        )
        if dlg.ShowModal() == wx.ID_CANCEL:
            LOGGER.debug("Saving of calibration was cancelled")
            return

        indices = dlg.GetSelections()
        document_titles = [document_list[idx] for idx in indices]
        dlg.Destroy()

        # get list of documents to which the calibration should be saved to
        for document_title in document_titles:
            document = ENV.on_get_document(document_title)
            self._ccs_obj.export_calibration(document, calibration_name)
            LOGGER.debug(f"Saved calibration `{calibration_name}` to `{document_title}` document.")

    def on_reset_calibration(self, _evt):
        """Reset calibration curve"""
        self.on_show_fit(None)
        LOGGER.debug("Reset calibration data")

    def on_show_fit(self, ccs_obj):
        """Show fit results"""
        if ccs_obj is None:
            self.view_fit.plot(x=np.arange(10), y=np.arange(10), repaint=False)
            self.view_fit.add_slope(np.arange(10), 0, 1, label=f"R2={0.999}", repaint=False)
            self.view_fit.show_legend(draggable=False)
        else:
            self.view_fit.plot(obj=ccs_obj, repaint=False)
            slope, intercept, r2 = ccs_obj.fit_linear_slope
            self.view_fit.add_slope(ccs_obj.x, intercept, slope, label=f"R2={r2:.4f}", repaint=False)
            self.view_fit.show_legend(draggable=False)


def _main():

    app = wx.App()
    ex = PanelCCSCalibration(None, debug=True)

    ex.Show()
    app.MainLoop()


if __name__ == "__main__":
    _main()
