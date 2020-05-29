# Standard library imports
import os
import logging

# Third-party imports
from numbers import Number
from typing import Dict, List, Tuple

import wx

# Local imports
from origami.styles import make_checkbox
from origami.styles import set_item_font
from origami.styles import make_spin_ctrl_int
from origami.utils.exceptions import MessageError
from origami.gui_elements.panel_import_files import PanelImportManagerBase

logger = logging.getLogger(__name__)


class PanelImagingImportDataset(PanelImportManagerBase):
    """LESA import manager"""

    DOCUMENT_TYPE = "Type: Imaging"
    PUB_SUBSCRIBE_EVENT = "widget.imaging.import.update.spectrum"
    SUPPORTED_FILE_FORMATS = [".raw"]

    # ui elements
    image_shape_x = None
    image_shape_y = None
    import_precompute_norm = None

    def __init__(self, parent, presenter, icons, **kwargs):
        PanelImportManagerBase.__init__(self, parent, presenter, icons, title="Imaging: Import LESA")

        self.parent = parent
        self.presenter = presenter
        self.icons = icons

    @property
    def data_handling(self):
        return self.presenter.data_handling

    @property
    def document_tree(self):
        return self.presenter.view.panelDocuments.documents

    def make_implementation_panel(self, panel):
        """Make settings panel"""

        # import
        image_dimension_label = set_item_font(wx.StaticText(panel, wx.ID_ANY, "Image dimensions:"))
        image_shape_x = wx.StaticText(panel, -1, "Shape (x-dim):")
        self.image_shape_x = make_spin_ctrl_int(panel, 0, 0, 100, 1, (90, -1), name="shape_x")
        self.image_shape_x.SetBackgroundColour((255, 230, 239))

        image_shape_y = wx.StaticText(panel, -1, "Shape (y-dim):")
        self.image_shape_y = make_spin_ctrl_int(panel, 0, 0, 100, 1, (90, -1), name="shape_y")
        self.image_shape_y.SetBackgroundColour((255, 230, 239))

        # import info
        self.import_precompute_norm = make_checkbox(
            panel,
            "Pre-compute dataset normalizations",
            tooltip="This will slow-down the processing speed but will allow for immediate access to normalizations.",
        )
        self.import_precompute_norm.Disable()
        self.import_precompute_norm.SetValue(True)

        dim_sizer = wx.BoxSizer(wx.HORIZONTAL)
        dim_sizer.Add(image_shape_x, 0, wx.ALIGN_CENTER_VERTICAL)
        dim_sizer.Add(self.image_shape_x, 0, wx.ALIGN_CENTER_VERTICAL)
        dim_sizer.AddSpacer(10)
        dim_sizer.Add(image_shape_y, 0, wx.ALIGN_CENTER_VERTICAL)
        dim_sizer.Add(self.image_shape_y, 0, wx.ALIGN_CENTER_VERTICAL)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(image_dimension_label)
        sizer.Add(dim_sizer)
        sizer.Add(self.import_precompute_norm)

        return sizer

    def _on_update_import_info(self):
        """Returns string to be inserted into the import label"""
        n_checked, mz_range, im_on, __ = self.get_list_parameters()

        if not mz_range or not im_on:
            return "Please load files first", wx.RED

        color = wx.BLACK
        if isinstance(mz_range, list) or isinstance(im_on, list):
            color = wx.RED

        info = f"Number of files: {n_checked}\n"
        info += f"Mass range: {mz_range}\n"
        info += f"Ion mobility: {im_on}"

        return info, color

    def on_update_implementation(self, metadata):
        """Update UI elements of the implementation"""
        # update image dimensions
        self.image_shape_x.SetValue(str(metadata.get("x_dim", 0)))
        self.image_shape_y.SetValue(str(metadata.get("y_dim", 0)))

    def get_parameters_implementation(self):
        """Retrieve processing parameters that are specific for the implementation"""
        x_dim = self.image_shape_x.GetValue()
        y_dim = self.image_shape_y.GetValue()

        n_files = self.peaklist.GetItemCount()

        if x_dim * y_dim == 0:
            raise MessageError("Error", "Please fill-in image dimensions information!")
        if x_dim * y_dim != n_files:
            raise MessageError("Error", "The number of files does not match image dimensions!")

        return dict(x_dim=int(x_dim), y_dim=int(y_dim))

    def _parse_path(self, path):
        def get_file_idx():
            _, file = os.path.split(path)
            _idx = file.split("_")[-1]
            _idx = _idx.split(".raw")[0]
            return _idx

        # get data
        idx = get_file_idx()
        try:
            idx = int(idx)
        except TypeError:
            logger.warning(f"Could not identify the index of {path}")

        reader = self.data_handling.get_waters_api_reader(path)
        ms_fcn = reader.stats_in_functions[0]
        dt_fcn = reader.stats_in_functions.get(1, False)
        mz_range = ms_fcn["mass_range"]
        n_scans = ms_fcn["n_scans"]
        scan_range = f"0-{n_scans - 1}"
        is_im = True if dt_fcn else False

        return dict(mz_range=mz_range, ion_mobility=is_im, scan_range=scan_range)

    def _import(self, filelist: List[Tuple[Number, str, int, int, Dict]], parameters: Dict):
        self.data_handling.on_open_multiple_LESA_files_fcn(filelist, **parameters)

    _import.__doc__ = PanelImportManagerBase._import.__doc__
