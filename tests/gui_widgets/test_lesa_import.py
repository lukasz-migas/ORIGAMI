"""Test LESA viewer"""
# Standard library imports
import sys

# Third-party imports
import wx
import pytest

# Local imports
from origami.widgets.lesa.panel_imaging_lesa_import import PanelImagingImportDataset

from ..wxtc import WidgetTestCase


@pytest.mark.guitest
@pytest.mark.skipif(sys.platform == "win32", reason="Running this test under Windows can sporadically cause errors")
class TestPanelImagingImportDataset(WidgetTestCase):
    """Test dialog"""

    def test_panel_create(self):
        dlg = PanelImagingImportDataset(None, None)
        dlg.Hide()
        self.wait_for(500)

        # ensure shape values are of correct color
        assert dlg.image_shape_x.GetBackgroundColour() != wx.WHITE
        assert dlg.image_shape_y.GetBackgroundColour() != wx.WHITE
        assert dlg.import_precompute_norm.IsEnabled() is False

        self.sim_spin_ctrl_click_evt(dlg.image_shape_x, 3, [dlg.on_shape])
        self.sim_spin_ctrl_click_evt(dlg.image_shape_y, 3, [dlg.on_shape])

        assert dlg.image_shape_x.GetBackgroundColour() == wx.WHITE
        assert dlg.image_shape_y.GetBackgroundColour() == wx.WHITE

        self.wait_for(500)
