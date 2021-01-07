"""Test ORIGAMI-MS settings panel"""
# Third-party imports
import pytest

# Local imports
from origami.utils.test import WidgetTestCase
from origami.widgets.origami_ms.dialog_origami_ms import DialogOrigamiMsSettings


@pytest.mark.guitest
class TestDialogOrigamiMsSettings(WidgetTestCase):
    """Test dialog"""

    def test_dialog_ok(self):
        dlg = DialogOrigamiMsSettings(self.frame, None, debug=True)

        # make sure methods are correctly enabling/disabling widgets
        assert dlg.user_settings_changed is False
        self.sim_combobox_click_evt(dlg.origami_method_choice, "Linear", [dlg.on_toggle_controls, dlg.on_apply])
        assert dlg.origami_boltzmann_offset_value.IsEnabled() is False
        assert dlg.origami_exponential_increment_value.IsEnabled() is False
        assert dlg.origami_exponential_percentage_value.IsEnabled() is False
        assert dlg.user_settings_changed is True

        self.sim_combobox_click_evt(dlg.origami_method_choice, "Exponential", [dlg.on_toggle_controls])
        assert dlg.origami_boltzmann_offset_value.IsEnabled() is False
        assert dlg.origami_exponential_increment_value.IsEnabled() is True
        assert dlg.origami_exponential_percentage_value.IsEnabled() is True

        self.sim_combobox_click_evt(dlg.origami_method_choice, "Boltzmann", [dlg.on_toggle_controls])
        assert dlg.origami_boltzmann_offset_value.IsEnabled() is True
        assert dlg.origami_exponential_increment_value.IsEnabled() is False
        assert dlg.origami_exponential_percentage_value.IsEnabled() is False

        self.sim_combobox_click_evt(dlg.origami_method_choice, "User-defined", [dlg.on_toggle_controls])
        assert dlg.origami_boltzmann_offset_value.IsEnabled() is False
        assert dlg.origami_exponential_increment_value.IsEnabled() is False
        assert dlg.origami_exponential_percentage_value.IsEnabled() is False
        assert dlg.origami_scansPerVoltage_value.IsEnabled() is False
        assert dlg.origami_load_list_btn.IsEnabled() is True

        self.sim_checkbox_click_evt(dlg.preprocess_check, True, [dlg.on_toggle_controls])
        assert dlg.process_btn.IsEnabled() is True
        self.sim_checkbox_click_evt(dlg.preprocess_check, False, [dlg.on_toggle_controls])
        assert dlg.process_btn.IsEnabled() is False
