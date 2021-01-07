"""Test UniDec viewer"""
# Standard library imports
import os

# Third-party imports
import pytest

# Local imports
from origami.utils.test import WidgetTestCase
from origami.utils.exceptions import MessageError
from origami.widgets.ccs.panel_ccs_database import PanelCCSDatabase


@pytest.mark.guitest
class TestPanelCCSDatabase(WidgetTestCase):
    """Test dialog"""

    def test_panel_create(self, tmp_path):
        dlg = PanelCCSDatabase(None)
        dlg.Hide()

        n_rows = dlg.n_rows
        assert dlg.n_rows != 0

        # make sure error dialog is displayed
        with pytest.raises(MessageError):
            dlg.on_add_calibrant(None)

        with pytest.raises(MessageError):
            self.sim_button_click_evt(dlg.add_btn, [dlg.on_add_calibrant])

        # add calibrant
        dlg.calibrant_value.SetValue("TEST")
        dlg.mw_value.SetValue("123")
        dlg.mz_value.SetValue("123")
        dlg.charge_value.SetValue("1")
        dlg.he_pos_ccs_value.SetValue("13")
        self.sim_button_click_evt(dlg.add_btn, [dlg.on_add_calibrant])
        assert n_rows + 1 == dlg.n_rows

        # write calibration table
        path = str(tmp_path / "calibrants.csv")
        dlg._on_save_calibrants(path)
        assert os.path.exists(path)

        # clear table
        dlg.on_delete_all(None, True)
        assert dlg.n_rows == 0

        dlg._on_load_calibrants(path)
        assert n_rows + 1 == dlg.n_rows

        for gas, polarity in zip(["Helium", "Nitrogen"], ["Positive", "Negative"]):
            quick = dlg.generate_quick_selection(gas, polarity)
            assert isinstance(quick, list)

        self.wait_for(500)
