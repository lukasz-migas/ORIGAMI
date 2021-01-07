"""Test CCS calibration"""
# Third-party imports
import wx
import numpy as np
import pytest

# Local imports
from origami.utils.test import WidgetTestCase
from origami.utils.exceptions import MessageError
from origami.objects.containers.spectrum import MobilogramObject
from origami.objects.containers.spectrum import MassSpectrumObject
from origami.widgets.ccs.panel_ccs_calibration import PanelCCSCalibration


@pytest.mark.guitest
class TestPanelCCSCalibration(WidgetTestCase):
    """Test dialog"""

    def test_panel_create(self):
        dlg = PanelCCSCalibration(None, debug=True)
        dlg.Hide()

        # ensure errors are shown
        with pytest.raises(MessageError):
            dlg.on_add_calibrant(None)

        with pytest.raises(MessageError):
            dlg.on_remove_calibrant(None)

        with pytest.raises(MessageError):
            dlg.on_create_calibration(None)

        with pytest.raises(MessageError):
            dlg.on_save_calibration(None)

        # some functionality
        dlg.on_auto_set_mw(None)
        assert dlg.mw_value.GetValue() == ""

        self.sim_textctrl_click_evt(dlg.charge_value, 1, [dlg.on_validate_input])
        assert dlg.charge_value.GetBackgroundColour() == wx.WHITE
        assert dlg.mz_value.GetBackgroundColour() != wx.WHITE
        assert dlg.mw_value.GetBackgroundColour() != wx.WHITE

        self.sim_textctrl_click_evt(dlg.mz_value, 10, [dlg.on_validate_input])
        assert dlg.mz_value.GetBackgroundColour() == wx.WHITE

        dlg.on_auto_set_mw(None)
        assert dlg.mw_value.GetValue() != ""

        self.sim_button_click_evt(dlg.clear_calibrant_btn, [dlg.on_clear_calibrant])
        assert dlg.mz_value.GetValue() == ""
        assert dlg.charge_value.GetValue() == 0
        assert dlg.mw_value.GetValue() == ""

        # plotting
        mz_obj = MassSpectrumObject(np.arange(100), np.arange(100))
        dlg.mz_obj = mz_obj

        dt_obj = MobilogramObject(np.arange(100), np.arange(100))
        dlg.dt_obj = dt_obj

        self.wait_for(500)
