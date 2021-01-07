"""Data import panel for LESA documents"""
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
from origami.utils.exceptions import MessageError
from origami.gui_elements.helpers import make_checkbox
from origami.gui_elements.helpers import set_item_font
from origami.gui_elements.helpers import make_spin_ctrl_int
from origami.gui_elements.panel_import_files import PanelImportManagerBase

logger = logging.getLogger(__name__)


class PanelImagingImportDataset(PanelImportManagerBase):
    """LESA import manager"""

    DOCUMENT_TYPE = "Type: Imaging"
    PUB_SUBSCRIBE_EVENT = "widget.imaging.import.update.spectrum"
    PUB_IN_PROGRESS_EVENT = "widget.imaging.import.progress"
    SUPPORTED_FILE_FORMATS = [".raw"]
    CONFIG_NAME = "imaging"

    # ui elements
    image_shape_x = None
    image_shape_y = None
    import_precompute_norm = None

    def __init__(self, parent, presenter):
        self._init()
        PanelImportManagerBase.__init__(self, parent, presenter, title="Imaging: Import LESA")

    def _init(self):
        """Modify certain elements before initialization takes place"""
        self.TABLE_CONFIG[self.TABLE_COLUMN_INDEX.variable]["type"] = "int"

    @property
    def data_handling(self):
        """Return handle to the `data_handling` object"""
        return self.presenter.data_handling

    @property
    def document_tree(self):
        """Return handle to the `document_tree` object"""
        return self.presenter.view.panelDocuments.documents

    def make_implementation_panel(self, panel):
        """Make settings panel"""

        # import
        image_dimension_label = set_item_font(wx.StaticText(panel, wx.ID_ANY, "Imaging details:"))
        image_shape_x = wx.StaticText(panel, -1, "Shape (x-dim):")
        self.image_shape_x = make_spin_ctrl_int(panel, 0, 0, 100, (90, -1), name="shape_x")
        self.image_shape_x.Bind(wx.EVT_TEXT, self.on_shape)
        self.image_shape_x.SetBackgroundColour((255, 230, 239))

        image_shape_y = wx.StaticText(panel, -1, "Shape (y-dim):")
        self.image_shape_y = make_spin_ctrl_int(panel, 0, 0, 100, (90, -1), name="shape_y")
        self.image_shape_y.Bind(wx.EVT_TEXT, self.on_shape)
        self.image_shape_y.SetBackgroundColour((255, 230, 239))

        # import info
        self.import_precompute_norm = make_checkbox(
            panel,
            "Pre-compute dataset normalizations",
            tooltip="This will slow-down the processing speed but will allow for immediate access to normalizations.",
        )
        self.import_precompute_norm.Disable()
        self.import_precompute_norm.SetValue(True)

        dim_sizer = wx.BoxSizer()
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

    def on_shape(self, _evt):
        """Update text box color"""
        bad_color = (255, 230, 239)
        good_color = wx.WHITE
        self.image_shape_x.SetBackgroundColour(good_color if self.image_shape_x.GetValue() else bad_color)
        self.image_shape_x.Refresh()
        self.image_shape_y.SetBackgroundColour(good_color if self.image_shape_y.GetValue() else bad_color)
        self.image_shape_y.Refresh()

    def _parse_path(self, path):
        """Parse raw file"""

        def get_file_idx():
            """Get information about the raw file"""
            _, file = os.path.split(path)
            _idx = file.split("_")[-1]
            _idx = _idx.split(".raw")[0]
            return _idx

        # get data
        variable = get_file_idx()
        try:
            variable = int(variable)
        except TypeError:
            logger.warning(f"Could not identify the index of {path}")

        # get waters metadata without explicitly loading it
        info = self.data_handling.get_waters_info(path)
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
        self.data_handling.on_open_lesa_file_fcn(self.document_title, filelist, **parameters)

    _import.__doc__ = PanelImportManagerBase._import.__doc__


if __name__ == "__main__":

    def _main():
        # Local imports
        from origami.app import App

        app = App()
        ex = PanelImagingImportDataset(None, None)
        ex.Show()
        app.MainLoop()

    _main()
