# Standard library imports
import os
import logging
from typing import Dict
from typing import List
from typing import Tuple
from numbers import Number

# Third-party imports
import wx

# Local imports
from origami.styles import make_checkbox, set_item_font
from origami.utils.exceptions import MessageError
from origami.gui_elements.panel_import_files import PanelImportManagerBase

logger = logging.getLogger(__name__)


class PanelManualImportDataset(PanelImportManagerBase):
    """Manual activation data import manager"""

    DOCUMENT_TYPE = "Type: Activation"
    PUB_SUBSCRIBE_EVENT = "widget.manual.import.update.spectrum"
    SUPPORTED_FILE_FORMATS = [".raw"]
    CONFIG_NAME = "activation"
    ACTIVATION_TYPES = ["CIU", "SID"]
    ACTIVATION_TYPE = ""

    # ui elements
    activation_type_choice = None
    auto_interpolate_check = None

    def __init__(self, parent, presenter, **kwargs):
        self._init(**kwargs)
        PanelImportManagerBase.__init__(self, parent, presenter, title="Activation: Import CIU/SID")

    def _init(self, **kwargs):
        """Modify certain elements before initialization takes place"""
        self.TABLE_DICT[self.TABLE_COLUMN_INDEX.variable]["type"] = "float"
        self.ACTIVATION_TYPE = kwargs.pop("activation_type", "CIU")

    @property
    def data_handling(self):
        return self.presenter.data_handling

    @property
    def document_tree(self):
        return self.presenter.view.panelDocuments.documents

    def make_implementation_panel(self, panel):
        """Make settings panel"""

        # import
        image_dimension_label = set_item_font(wx.StaticText(panel, wx.ID_ANY, "Activation details:"))
        activation_type = wx.StaticText(panel, -1, "Activation type:")
        self.activation_type_choice = wx.Choice(panel, -1, choices=self.ACTIVATION_TYPES)
        self.activation_type_choice.SetStringSelection(self.ACTIVATION_TYPE)

        self.auto_interpolate_check = make_checkbox(
            panel,
            "Auto-interpolate",
            tooltip="Ion mobility profiles will be automatically interpolated to ensure spacing between adjacent"
            " mobilograms is consistent. This will only take place if the data was acquired with a non-linear"
            " manner.",
        )
        self.auto_interpolate_check.SetValue(True)

        detail_sizer = wx.BoxSizer(wx.HORIZONTAL)
        detail_sizer.Add(activation_type, 0, wx.ALIGN_CENTER_VERTICAL)
        detail_sizer.Add(self.activation_type_choice, 0, wx.ALIGN_CENTER_VERTICAL)
        detail_sizer.AddSpacer(10)
        detail_sizer.Add(self.auto_interpolate_check, 0, wx.ALIGN_CENTER_VERTICAL)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(image_dimension_label)
        sizer.Add(detail_sizer)

        return sizer

    def on_update_implementation(self, metadata):
        """Update UI elements of the implementation"""
        self.activation_type_choice.SetStringSelection(str(metadata.get("activation_type", "CIU")))
        self.auto_interpolate_check.SetValidator(metadata.get("auto_interpolate", True))

    def get_parameters_implementation(self):
        """Retrieve processing parameters that are specific for the implementation"""
        activation_type = self.activation_type_choice.GetStringSelection()
        auto_interpolate = self.auto_interpolate_check.GetValue()

        return dict(activation_type=activation_type, auto_interpolate=auto_interpolate)

    def _parse_path(self, path):
        def get_file_idx():
            activation_type = self.activation_type_choice.GetStringSelection()

            _idx = None
            if activation_type == "CIU":
                _idx = info["cid"]

            if _idx is None or activation_type == "SID":
                _, file = os.path.split(path)
                _idx = file.split("_")[-1]
                _idx = _idx.split(".raw")[0]
            return _idx

        # get waters metadata without explicitly loading data
        info = self.data_handling.get_waters_info(path)
        variable = get_file_idx()
        is_im = info["is_im"]
        mz_range = info["mz_range"]
        n_scans = info["n_scans"]
        scan_range = f"0-{n_scans - 1}"
        mz_range = f"{mz_range[0]}-{mz_range[1]}"

        return dict(mz_range=mz_range, ion_mobility=is_im, scan_range=scan_range, variable=variable, n_scans=n_scans)

    def _import(self, filelist: List[Tuple[Number, str, int, int, Dict]], **parameters: Dict):
        if self.document_title is None:
            raise MessageError(
                "Incorrect document", "Please specify document by clicking on the `Select document...` " "button"
            )

        self.data_handling.on_open_manual_file_fcn(self.document_title, filelist, **parameters)

    _import.__doc__ = PanelImportManagerBase._import.__doc__
