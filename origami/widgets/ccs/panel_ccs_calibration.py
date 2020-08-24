"""Panel for preparing CCS calibration data"""
# Standard library imports
import os
import re
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
from origami.icons.assets import Icons
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
from origami.gui_elements.helpers import TableConfig
from origami.gui_elements.helpers import set_tooltip
from origami.gui_elements.helpers import set_item_font
from origami.gui_elements.helpers import make_bitmap_btn
from origami.widgets.ccs.view_ccs import ViewCCSFit
from origami.widgets.ccs.view_ccs import ViewCCSMobilogram
from origami.gui_elements.panel_base import TableMixin
from origami.gui_elements.misc_dialogs import DialogBox
from origami.widgets.ccs.panel_ccs_database import PanelCCSDatabase
from origami.gui_elements.views.view_register import VIEW_REG
from origami.gui_elements.views.view_spectrum import ViewMassSpectrum
from origami.widgets.ccs.processing.containers import CalibrationIndex
from origami.widgets.ccs.processing.calibration import CCSCalibrationProcessor

LOGGER = logging.getLogger(__name__)

# TODO: restore calibration data
# TODO: add option to change the fit plot between linear and log
# TODO: write documentation
# TODO: there is a bug


class TableColumnIndex(IntEnum):
    """Table indexer"""

    check = 0
    calibrant = 1
    mz = 2
    mw = 3
    charge = 4
    dt = 5
    ccs = 6
    name = 7
    path = 8


class PlotNotebookPages:
    """Notebook pages"""

    extraction = 0
    calibration = 1


class PanelCCSCalibration(MiniFrame, TableMixin, DatasetMixin, ConfigUpdateMixin):
    """CCS panel"""

    TABLE_DICT = TableConfig()
    TABLE_DICT.add("", "check", "bool", 25, hidden=True)
    TABLE_DICT.add("calibrant", "calibrant", "str", 80)
    TABLE_DICT.add("m/z", "mz", "float", 70)
    TABLE_DICT.add("MW", "mw", "float", 70)
    TABLE_DICT.add("z", "charge", "int", 40)
    TABLE_DICT.add("dt", "dt", "float", 70)
    TABLE_DICT.add("ccs", "ccs", "float", 80)
    TABLE_DICT.add("name", "name", "str", 0, hidden=True)
    TABLE_DICT.add("path", "path", "str", 0, hidden=True)
    TABLE_WIDGET_DICT = dict()
    TABLE_COLUMN_INDEX = TableColumnIndex
    USE_COLOR = False
    PANEL_BASE_TITLE = "CCS Calibration Builder"
    HELP_LINK = "https://origami.lukasz-migas.com/"

    PUB_SUBSCRIBE_MZ_GET_EVENT = "ccs.extract.ms"
    PUB_SUBSCRIBE_DT_GET_EVENT = "ccs.extract.dt"
    PUB_SUBSCRIBE_UPDATE = "ccs.update.quick"

    # ui elements
    view_mz, view_dt, view_fit, peaklist, quick_selection_choice, mz_value = None, None, None, None, None, None
    mw_value, charge_value, dt_value, ccs_value, add_calibrant_btn = None, None, None, None, None
    remove_calibrant_btn, gas_choice, reset_btn, save_btn, calculate_ccs_btn = None, None, None, None, None
    file_path_choice, load_file_btn, action_btn, load_document_btn = None, None, None, None
    auto_process_btn, correction_value, mw_auto_btn, polarity_choice = None, None, None, None
    extract_calibrant_btn, window_size_value, clear_calibrant_btn = None, None, None
    plot_notebook, calibrant_value = None, None

    # attributes
    _mz_obj = None
    _dt_obj = None
    _cache = dict()
    _tmp_cache = dict()
    _ccs_obj = None

    def __init__(self, parent, document_title: str = None, debug: bool = False):
        """Initialize panel"""
        MiniFrame.__init__(self, parent, title="CCS Calibration Builder...", style=wx.DEFAULT_FRAME_STYLE)
        t_start = time.time()
        self.parent = parent
        self._icons = Icons()

        # initialize gui
        self.make_gui()

        # setup kwargs
        self.document_title = document_title
        self.unsaved = False  # indicate that the panel has unsaved changes
        self._debug = debug  # flag to indicate the application is in debug mode
        self._db = None  # handle of the CCS database dialog
        self._showing_quick = False  # flag to indicate that quick selection is being shown rather than user-extracted
        self._disable_table_update = False  # flag to prevent editing events
        self._current_item = None  # specifies which is the currently selected item

        # bind events
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_CONTEXT_MENU, self.on_right_click)
        LOGGER.debug(f"Started-up CCS panel in {report_time(t_start)}")

        self.CenterOnParent()
        self.SetFocus()
        self.SetSize((1200, 1000))

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
        # setup maximum size of quick selection
        self.quick_selection_choice.SetMaxSize(self.quick_selection_choice.GetSize())

        self._config_mixin_setup()
        self._dataset_mixin_setup()

        # add listeners
        pub.subscribe(self.evt_extract_dt_from_ms, self.PUB_SUBSCRIBE_MZ_GET_EVENT)
        pub.subscribe(self.evt_select_conformation, self.PUB_SUBSCRIBE_DT_GET_EVENT)
        pub.subscribe(self.on_update_quick_selection, self.PUB_SUBSCRIBE_UPDATE)

        self.on_validate_input(None)

        self.TABLE_WIDGET_DICT = {
            self.calibrant_value: (TableColumnIndex.calibrant, "calibrant"),
            self.mw_value: (TableColumnIndex.mw, "mw"),
            self.charge_value: (TableColumnIndex.charge, "charge"),
            self.mz_value: (TableColumnIndex.mz, "mz"),
            self.dt_value: (TableColumnIndex.dt, "dt"),
            self.ccs_value: (TableColumnIndex.ccs, "ccs"),
        }

        # instantiate CCS database
        self._db = PanelCCSDatabase(self, icons=self._icons, hide_on_close=True)
        self.on_update_quick_selection(None)

        # check existing document
        self.check_existing_calibration()

    def check_existing_calibration(self):
        """Checks whether existing calibration already exists for a particular document"""
        if self.document_title is None:
            return

        # get current document
        document = ENV.on_get_document(self.document_title)
        if document:
            calibration_list = document.get_ccs_calibration_list()
            print("EXISTING LIST", calibration_list)

    def on_close(self, evt, force: bool = False):
        """Close window"""
        if self.unsaved and not force and not self._debug:
            dlg = DialogBox(
                title="Would you like to continue?",
                msg="There are unsaved changes in this window. Continuing might lead to loss of calibration data."
                "\nWould you like to continue?",
                kind="Question",
            )
            if dlg == wx.ID_NO:
                return

        try:
            pub.unsubscribe(self.evt_extract_dt_from_ms, self.PUB_SUBSCRIBE_MZ_GET_EVENT)
            pub.unsubscribe(self.evt_select_conformation, self.PUB_SUBSCRIBE_DT_GET_EVENT)
            pub.unsubscribe(self.on_update_quick_selection, self.PUB_SUBSCRIBE_UPDATE)
            LOGGER.debug("Unsubscribed from events")
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

        # make notebook
        self.plot_notebook = wx.Notebook(panel)
        _plot_panel = wx.Panel(self.plot_notebook, -1)

        # mass spectrum
        self.view_mz = ViewMassSpectrum(
            _plot_panel,
            (6, 3),
            CONFIG,
            allow_extraction=True,
            callbacks=dict(CTRL=self.PUB_SUBSCRIBE_MZ_GET_EVENT),
            filename="mass-spectrum",
        )

        # mobilogram
        self.view_dt = ViewCCSMobilogram(
            _plot_panel,
            (6, 3),
            CONFIG,
            allow_extraction=True,
            callbacks=dict(CTRL=self.PUB_SUBSCRIBE_DT_GET_EVENT),
            filename="molecular-weight",
        )

        plot_sizer = wx.BoxSizer(wx.VERTICAL)
        plot_sizer.Add(self.view_mz.panel, 1, wx.EXPAND)
        plot_sizer.Add(self.view_dt.panel, 1, wx.EXPAND)

        plot_sizer.Fit(_plot_panel)
        _plot_panel.SetSizer(plot_sizer)

        # fit
        self.view_fit = ViewCCSFit(
            self.plot_notebook,
            (4, 2),
            CONFIG,
            allow_extraction=False,
            filename="ccs-fit",
            axes_size=(0.15, 0.25, 0.8, 0.65),
        )

        self.plot_notebook.AddPage(_plot_panel, "Extraction")
        self.plot_notebook.AddPage(self.view_fit.panel, "Calibration")

        # data selection
        self.file_path_choice = wx.Choice(panel, -1)
        self.file_path_choice.Bind(wx.EVT_CHOICE, self.on_select_file)

        self.load_file_btn = wx.Button(panel, -1, "Load")
        self.load_file_btn.Bind(wx.EVT_BUTTON, self.on_load_file)

        self.load_document_btn = make_bitmap_btn(panel, -1, self._icons.folder)
        self.load_document_btn.Bind(wx.EVT_BUTTON, self.on_open_document)
        set_tooltip(
            self.load_document_btn,
            "If in standalone mode, open ORIGAMI document to which you would like to save the calibration.",
        )

        self.auto_process_btn = wx.Button(panel, -1, "Auto-process")
        self.auto_process_btn.Bind(wx.EVT_BUTTON, self.on_auto_process)

        gas_choice = wx.StaticText(panel, -1, "Gas:")
        self.gas_choice = wx.Choice(panel, -1, choices=["Nitrogen", "Helium"])
        self.gas_choice.SetStringSelection("Nitrogen")
        self.gas_choice.Bind(wx.EVT_CHOICE, self.on_update_quick_selection)

        polarity_choice = wx.StaticText(panel, -1, "Polarity:")
        self.polarity_choice = wx.Choice(panel, -1, choices=["Positive", "Negative"])
        self.polarity_choice.SetStringSelection("Positive")
        self.polarity_choice.Bind(wx.EVT_CHOICE, self.on_update_quick_selection)

        correction_factor = wx.StaticText(panel, -1, "Correction factor:")
        self.correction_value = wx.TextCtrl(panel, -1, "", validator=Validator("floatPos"))
        set_tooltip(
            self.correction_value,
            "Instruments Enhanced Duty Cycle (EDC) delay coefficient. Automatically loaded from the raw file",
        )

        # item settings
        quick_selection = wx.StaticText(panel, -1, "Quick selection:")
        self.quick_selection_choice = wx.Choice(panel, -1)
        self.quick_selection_choice.Bind(wx.EVT_CHOICE, self.on_quick_selection)

        self.action_btn = make_bitmap_btn(panel, -1, self._icons.list)
        self.action_btn.Bind(wx.EVT_BUTTON, self.on_open_calibrant_panel)
        set_tooltip(self.action_btn, "Open new panel with currently loaded or available calibrant ions")

        calibrant_value = wx.StaticText(panel, -1, "calibrant")
        self.calibrant_value = wx.TextCtrl(panel, -1, "")
        self.calibrant_value.Bind(wx.EVT_TEXT, self.on_validate_input)
        self.calibrant_value.Bind(wx.EVT_TEXT, self.on_edit_calibrant)

        mz_value = wx.StaticText(panel, -1, "m/z")
        self.mz_value = wx.TextCtrl(panel, -1, "", validator=Validator("floatPos"))
        self.mz_value.Bind(wx.EVT_TEXT, self.on_validate_input)
        self.mz_value.Bind(wx.EVT_TEXT, self.on_edit_calibrant)

        mw_value = wx.StaticText(panel, -1, "MW (Da)")
        self.mw_value = wx.TextCtrl(panel, -1, "", validator=Validator("floatPos"))
        self.mw_value.Bind(wx.EVT_TEXT, self.on_validate_input)
        self.mw_value.Bind(wx.EVT_TEXT, self.on_edit_calibrant)

        self.mw_auto_btn = make_bitmap_btn(panel, -1, self._icons.target)
        self.mw_auto_btn.Bind(wx.EVT_BUTTON, self.on_auto_set_mw)
        set_tooltip(self.mw_auto_btn, "Auto-set molecular weight based on the m/z and charge values.")

        charge_value = wx.StaticText(panel, -1, "Charge (z):")
        self.charge_value = wx.SpinCtrl(panel, -1, "", min=-100, max=100)
        self.charge_value.Bind(wx.EVT_TEXT, self.on_validate_input)
        self.charge_value.Bind(wx.EVT_TEXT, self.on_edit_calibrant)

        dt_value = wx.StaticText(panel, -1, "DT (ms):")
        self.dt_value = wx.TextCtrl(panel, -1, "", validator=Validator("floatPos"))
        self.dt_value.Bind(wx.EVT_TEXT, self.on_validate_input)
        self.dt_value.Bind(wx.EVT_TEXT, self.on_edit_calibrant)

        ccs_value = wx.StaticText(panel, -1, "CCS (Å²):")
        self.ccs_value = wx.TextCtrl(panel, -1, "", validator=Validator("floatPos"))
        self.ccs_value.Bind(wx.EVT_TEXT, self.on_validate_input)
        self.ccs_value.Bind(wx.EVT_TEXT, self.on_edit_calibrant)

        window_size_value = wx.StaticText(panel, -1, "window (Da):")
        self.window_size_value = wx.TextCtrl(panel, -1, "25", validator=Validator("floatPos"))
        set_tooltip(
            self.window_size_value,
            "Size of the extraction window when using the quick-selection control. This pads the m/z value with +/-"
            " window to ensure enough data is extracted to form a mobilogram. This value is ignored when CTRL+drag in"
            " mass spectrum.",
        )
        self.window_size_value.Bind(wx.EVT_TEXT, self.on_update_quick_selection_window)

        self.extract_calibrant_btn = wx.Button(panel, -1, "Extract")
        self.extract_calibrant_btn.Bind(wx.EVT_BUTTON, self.on_extract_calibrant)

        self.add_calibrant_btn = wx.Button(panel, -1, "Add")
        self.add_calibrant_btn.Bind(wx.EVT_BUTTON, self.on_add_calibrant)

        self.clear_calibrant_btn = wx.Button(panel, -1, "Clear")
        self.clear_calibrant_btn.Bind(wx.EVT_BUTTON, self.on_clear_calibrant)

        self.remove_calibrant_btn = wx.Button(panel, -1, "Remove")
        self.remove_calibrant_btn.Bind(wx.EVT_BUTTON, self.on_remove_calibrant)

        btn_sizer_cali = wx.BoxSizer()
        btn_sizer_cali.Add(self.extract_calibrant_btn)
        btn_sizer_cali.AddSpacer(5)
        btn_sizer_cali.Add(self.add_calibrant_btn)
        btn_sizer_cali.AddSpacer(5)
        btn_sizer_cali.Add(self.clear_calibrant_btn)
        btn_sizer_cali.AddSpacer(5)
        btn_sizer_cali.Add(self.remove_calibrant_btn)

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
        grid.Add(polarity_choice, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.polarity_choice, (n, 1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
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
        grid.Add(calibrant_value, (n, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.calibrant_value, (n, 1), (1, 3), flag=wx.EXPAND)
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
        grid.Add(window_size_value, (n, 2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid.Add(self.window_size_value, (n, 3), flag=wx.EXPAND)

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
        side_sizer.AddSpacer(3)
        side_sizer.Add(btn_sizer_cali, 0, wx.ALIGN_CENTER_HORIZONTAL)
        side_sizer.Add(self.peaklist, 1, wx.EXPAND)
        side_sizer.AddSpacer(3)
        side_sizer.Add(wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND)
        side_sizer.Add(calculate_label, 0, wx.ALIGN_CENTER_HORIZONTAL)
        side_sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL)
        side_sizer.Add(info_sizer, 0, wx.EXPAND)

        # main sizer
        main_sizer = wx.BoxSizer()
        main_sizer.Add(self.plot_notebook, 1, wx.EXPAND | wx.ALL, 3)
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

        self._parse_evt(evt)

    def on_load_file(self, _evt):
        """Select Waters .raw directory"""
        # get directory
        path = None
        dlg = wx.DirDialog(wx.GetTopLevelParent(self), "Choose a Waters (.raw) directory")
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
        dlg.Destroy()

        # load data
        if path is not None and path.endswith(".raw"):
            metadata = LOAD_HANDLER.waters_metadata(path)
            mz_obj = LOAD_HANDLER.waters_im_extract_ms(path)
            self._set_calibration_cache(path, {"mz_obj": mz_obj, "metadata": metadata})

    def on_auto_set_mw(self, _evt):
        """Automatically set molecular weight based on the m/z value and charge"""
        mz_value = str2num(self.mz_value.GetValue())
        charge_value = str2int(self.charge_value.GetValue())
        polarity = self.polarity_choice.GetStringSelection()
        if not all([mz_value, charge_value]):
            return

        if polarity == "Positive":
            mw = (mz_value - charge_value * 1.00784) * charge_value
        else:
            mw = (mz_value + charge_value * 1.00784) * charge_value
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

    def on_open_calibrant_panel(self, _evt):
        """Open panel where users can create calibration table"""
        if not self._db:
            self._db = PanelCCSDatabase(self, icons=self._icons, hide_on_close=True)
        self._db.Show()

    def on_auto_process(self, _evt):
        """Auto-process the loaded data"""
        from origami.widgets.ccs.misc_windows import DialogAutoGenerateConformers

        popup = DialogAutoGenerateConformers(self)
        popup.Show()

    def _on_auto_process(self, mw: float, z_start: int, z_end: int, mz_window: float):
        """Auto-process the currently loaded mass spectrum"""
        charges = np.arange(z_start, z_end + 1)[::-1]
        mz_values = mw / charges
        for mz, charge in zip(mz_values, charges):
            self.evt_extract_dt_from_ms([mz - mz_window, mz + mz_window, None, None], None, None)
            self.charge_value.SetValue(str(charge))
            # presets
            self.mw_value.SetValue(str(mw))
            self.ccs_value.SetValue("1")
            self.on_add_calibrant(None)

    def _simulate_auto_process(self, mw: float, z_start: int, z_end: int, mz_window: float):
        """Simulate auto-processing by highlighting the regions of interest"""
        self.view_mz.remove_patches(repaint=False)
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
        self.view_mz.remove_patches(repaint=False)
        self.mz_obj = mz_obj
        self.correction_value.SetValue(str(self.correction_factor))

        LOGGER.debug(f"Changed mass spectrum to `{filename}`")
        if evt is not None:
            evt.Skip()

    def on_update_quick_selection(self, _evt):
        """Make changes to the config"""
        gas = self.gas_choice.GetStringSelection()
        polarity = self.polarity_choice.GetStringSelection()

        if self._db:
            quick_selection = self._db.generate_quick_selection(gas, polarity)
            self.quick_selection_choice.Clear()
            if quick_selection:
                self.quick_selection_choice.SetItems(quick_selection)
                self.quick_selection_choice.SetStringSelection(quick_selection[0])

    def on_select_calibrant_from_table(self, evt):
        """Select calibrant in the table and show the data"""
        if hasattr(evt, "GetIndex"):
            self.peaklist.item_id = evt.GetIndex()
        item_info = self.on_get_item_information()
        self._on_set_calibrant_metadata(item_info)
        name = item_info["name"]
        path = item_info["path"]

        self._tmp_cache[path] = self._cache[path]["calibrants"][name]
        self.dt_obj = self._tmp_cache[path]["dt_obj"]
        self._on_show_dt_marker()

    def on_edit_calibrant(self, evt):
        """Edit calibrant in the table"""
        if self._disable_table_update:
            self._parse_evt(evt)
            return
        # get ui object that created this event
        obj = evt.GetEventObject()

        # get current item in the table that is being edited
        item_id = self.on_find_item("name", self._current_item)
        if item_id == -1:
            self._parse_evt(evt)
            return

        # get current column
        (col_id, key) = self.TABLE_WIDGET_DICT.get(obj, -1)
        if col_id == -1:
            self._parse_evt(evt)
            return

        # update item in the table
        value = obj.GetValue()
        self.peaklist.SetItem(item_id, col_id, str(value))

        # update item in the cache
        value = self._parse_value(key, value)
        self._cache[self.current_path]["calibrants"][self._current_item][key] = value
        self._parse_evt(evt)

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
        calibrant = self.calibrant_value.GetValue()
        if calibrant in ["", None]:
            calibrant = f"calibrant {self.n_rows + 1}"

        if not all([mz_value, mw_value, charge_value, dt_value, ccs_value]):
            raise MessageError("Error", "Cannot add calibrant to the table as some values are missing")
        if not all(
            [
                v in self._tmp_cache[self.current_path]
                for v in ["dt_obj", "dt_int", "name", "mz_min", "mz_max", "mz_int"]
            ]
        ):
            raise MessageError(
                "Error",
                "Cache data is missing some essential data - please click on the `Extract`"
                " button so it can be added and try-again",
            )

        # get index of the present object
        idx = self.on_find_item("mz", mz_value)
        if idx != -1:
            self.remove_from_table(idx)

        # add to table
        name = self._tmp_cache[self.current_path]["name"]
        self.on_add_to_table(
            dict(
                calibrant=calibrant,
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
            {
                "charge": charge_value,
                "mz": mz_value,
                "mw": mw_value,
                "dt": dt_value,
                "ccs": ccs_value,
                "calibrant": calibrant,
            }
        )

        # add to cache
        self._set_calibration_cache(self.current_path, {"calibrant": self._tmp_cache[self.current_path], "name": name})
        self._on_show_mz_patches()

        # reset temporary cache
        self.on_clear_calibrant(None)
        self._tmp_cache[self.current_path] = None

        LOGGER.debug("Added calibrant to cache")

    def on_clear_calibrant(self, _evt):
        """Clear all fields"""
        item_info = dict().fromkeys(["mz", "mw", "charge", "dt", "ccs", "name", "calibrant"], None)
        self._on_set_calibrant_metadata(item_info)

    def on_extract_calibrant(self, _evt):
        """Extract calibrant data"""
        # show the peak in the mass spectrum
        mz_window = str2num(self.window_size_value.GetValue())
        if mz_window is None:
            mz_window = 25

        mz = str2num(self.mz_value.GetValue())
        self.evt_extract_dt_from_ms([mz - mz_window, mz + mz_window, None, None], None, None)

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
        self.view_dt.clear()
        self.on_clear_calibrant(None)
        LOGGER.debug("Removed calibrant from the cache")

    def on_quick_selection(self, _evt):
        """Quick selection to fill-in few common parameters"""
        self._showing_quick = True
        self._disable_table_update = True
        quick_selection = self.quick_selection_choice.GetStringSelection()

        # get values from the selection
        mw, charge, mz, ccs = re.findall(r"=(.*?);", quick_selection)
        calibrant = quick_selection.split(";")[0]

        if str2num(mw):
            self.mw_value.SetValue(mw)
        if str2int(charge):
            self.charge_value.SetValue(charge)
        if str2num(mz):
            self.mz_value.SetValue(mz)
        if str2num(ccs):
            self.ccs_value.SetValue(ccs)
        self.dt_value.SetValue("")
        self.calibrant_value.SetValue(calibrant)

        # show the peak in the mass spectrum
        mz_window = str2num(self.window_size_value.GetValue())
        if mz_window is None:
            mz_window = 25
            LOGGER.warning("The extraction window is not a number!")
        mz = str2num(mz)

        self.view_mz.remove_patches("temporary_mz", False)
        self.view_mz.add_patch(mz - mz_window, 0, mz_window * 2, 99999999, label="temporary_mz")
        self.on_validate_input(None)
        self._disable_table_update = False

    def on_update_quick_selection_window(self, _evt):
        """Update the quick selection window"""
        mz_window = str2num(self.window_size_value.GetValue())
        if self._showing_quick and mz_window is not None:
            self.on_quick_selection(_evt)

    def evt_extract_dt_from_ms(self, rect, x_labels, y_labels):  # noqa
        """Extract mobilogram from mass spectrum"""
        mz_min, mz_max, _, _ = rect
        mz_pos, mz_int = self.mz_obj.get_x_at_loc(mz_min, mz_max)
        path = self.current_path
        dt_obj = LOAD_HANDLER.waters_im_extract_dt(path, mz_start=mz_min, mz_end=mz_max)
        dt_obj.change_x_label("Drift time (ms)", self.pusher_frequency)
        dt_pos, dt_int = dt_obj.get_x_at_max()
        name = get_short_hash()

        # store information about currently plotted mobility object in temporary cache
        self._tmp_cache[path] = {
            "mz_min": mz_min,
            "mz_max": mz_max,
            "mz": mz_pos,
            "mz_int": mz_int,
            "dt_obj": dt_obj,
            "dt": dt_pos,
            "dt_int": dt_int,
            "name": name,
        }

        # update plot
        self.dt_obj = dt_obj
        self._on_set_calibrant_metadata(self._tmp_cache[path])
        self._on_show_dt_marker()
        self._showing_quick = False

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
        self.view_mz.remove_patches(repaint=False)
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
        self._disable_table_update = True
        if "mz" in cache:
            self.mz_value.SetValue(f"{cache['mz']:.2f}" if cache["mz"] else "")
        if "mw" in cache:
            self.mw_value.SetValue(f"{cache['mw']:.2f}" if cache["mw"] else "")
        if "charge" in cache:
            self.charge_value.SetValue(f"{cache['charge']}" if cache["charge"] else "0")
        if "ccs" in cache:
            self.ccs_value.SetValue(f"{cache['ccs']:.2f}" if cache["ccs"] else "")
        if "dt" in cache:
            self.dt_value.SetValue(f"{cache['dt']:.2f}" if cache["dt"] else "")
        if "calibrant" in cache:
            self.calibrant_value.SetValue(cache["calibrant"])
        self._current_item = cache["name"]
        self._disable_table_update = False

    def on_create_calibration(self, _evt):
        """Create calibration curve"""
        selected_indices = self.get_checked_items()
        if not selected_indices:
            raise MessageError(
                "Error", "Cannot create calibration curve with 0 selected items. Please select items in the table."
            )

        self._collect_calibration_data(selected_indices)
        self.unsaved = True

    def _collect_calibration_data(self, selected_indices):
        """Collect calibration data"""
        metadata = []
        extra_data = {}
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
                    "calibrant": calibrant["calibrant"],
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
            extra_data[name] = calibrant["dt_obj"]

        calibration = CCSCalibrationProcessor(metadata, extra_data)
        ccs_obj = calibration.create_calibration(array, self.gas_mw, self.correction_factor)
        self._ccs_obj = calibration

        # update plot data
        self.on_show_fit(ccs_obj)
        self.plot_notebook.SetSelection(PlotNotebookPages.calibration)

    def on_save_calibration(self, _evt):
        """Save calibration curve in the document"""
        from origami.gui_elements.misc_dialogs import DialogSimpleAsk

        # check whether calibration was created
        if not self._ccs_obj:
            raise MessageError("Error", "Please create CCS calibration before trying to save it.")

        # get list of documents to which the calibration should be saved to
        document_list = ENV.get_document_list(document_format=DOCUMENT_WATERS_FILE_FORMATS)
        if not document_list:
            raise MessageError("Error", "List od documents was empty - cannot save calibration data")

        # allow the user to make selection
        dlg = wx.MultiChoiceDialog(
            self, "Please select documents where the calibration data should be saved to", "Documents", document_list
        )
        if dlg.ShowModal() == wx.ID_CANCEL:
            LOGGER.debug("Saving of calibration was cancelled")
            return

        # get name under which the calibration data should be loaded
        calibration_name = DialogSimpleAsk(
            "Please specify name of the calibration", "Calibration name", "Calibration", self
        )
        if calibration_name is None:
            LOGGER.debug("Saving of calibration was cancelled")
            return

        indices = dlg.GetSelections()
        document_titles = [document_list[idx] for idx in indices]
        dlg.Destroy()

        for document_title in document_titles:
            self._on_save_calibration(document_title, calibration_name)
        self.unsaved = False

    def _on_save_calibration(self, document_title, calibration_name):
        """Save calibration data in the document"""
        document = ENV.on_get_document(document_title)
        self._ccs_obj.export_calibration(document, calibration_name)
        LOGGER.debug(f"Saved calibration `{calibration_name}` to `{document_title}` document.")

    def on_reset_calibration(self, _evt):
        """Reset calibration curve"""
        if self._ccs_obj:
            dlg = DialogBox(
                "Are you sure?",
                "Are you sure you want to reset current calibration object?",
                kind="Question",
                parent=self,
            )
            if dlg == wx.ID_NO:
                return
            self._ccs_obj = None
            self.view_fit.clear()
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

    @staticmethod
    def _parse_evt(evt):
        """Parse event"""
        if evt is not None:
            evt.Skip()

    @staticmethod
    def _parse_value(key: str, value: str):
        """Parse value and convert to correct type"""
        if key in ["charge"]:
            return str2int(value)
        else:
            return str2num(value)


def _main():

    app = wx.App()
    ex = PanelCCSCalibration(None, debug=True)

    ex.Show()
    app.MainLoop()


if __name__ == "__main__":
    _main()
