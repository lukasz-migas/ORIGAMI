"""Test PanelAbout dialog"""
# Third-party imports
import pytest

# Local imports
from origami.utils.test import WidgetTestCase
from origami.gui_elements.panel_process_heatmap import PanelProcessHeatmap


@pytest.mark.guitest
class TestPanelProcessHeatmap(WidgetTestCase):
    """Test dialog"""

    def test_dialog_ok(self):
        dlg = PanelProcessHeatmap(self.frame, None)

        dlg.Show()

    def test_dialog_no_plot(self):
        dlg = PanelProcessHeatmap(self.frame, None, disable_plot=True)

        assert dlg.plot_btn is None

        dlg.Show()

    def test_dialog_no_process(self):
        dlg = PanelProcessHeatmap(self.frame, None, disable_process=True)

        assert dlg.add_to_document_btn is None

        dlg.Show()

    def test_dialog_activity(self):
        dlg = PanelProcessHeatmap(self.frame, None)

        # ensure all buttons are present and activity indicator is hidden
        assert dlg.plot_btn is not None
        assert dlg.add_to_document_btn is not None
        assert not dlg.activity_indicator.IsShown()

        # trigger activity ON
        dlg.on_progress(True, "")
        assert dlg.activity_indicator.IsShown()
        assert not dlg.plot_btn.IsEnabled()
        assert not dlg.add_to_document_btn.IsEnabled()

        # trigger activity OFF
        dlg.on_progress(False, "")
        assert not dlg.activity_indicator.IsShown()
        assert dlg.plot_btn.IsEnabled()
        assert dlg.add_to_document_btn.IsEnabled()

        dlg.Show()

    def test_dialog_ui(self):
        dlg = PanelProcessHeatmap(self.frame, None)

        toggle = False
        # crop
        dlg.crop_check.SetValue(toggle)
        dlg.on_toggle_controls(None)
        assert dlg.crop_xmin_value.IsEnabled() is toggle
        assert dlg.crop_xmax_value.IsEnabled() is toggle
        assert dlg.crop_ymin_value.IsEnabled() is toggle
        assert dlg.crop_ymax_value.IsEnabled() is toggle

        # linearize
        dlg.interpolate_check.SetValue(toggle)
        dlg.on_toggle_controls(None)
        assert dlg.interpolate_choice.IsEnabled() is toggle
        assert dlg.interpolate_fold.IsEnabled() is toggle
        assert dlg.interpolate_xaxis.IsEnabled() is toggle
        assert dlg.interpolate_yaxis.IsEnabled() is toggle

        # smooth
        dlg.smooth_check.SetValue(toggle)
        dlg.on_toggle_controls(None)
        assert dlg.smooth_sigma_value.IsEnabled() is toggle
        assert dlg.smooth_poly_order_value.IsEnabled() is toggle
        assert dlg.smooth_window_value.IsEnabled() is toggle

        # baseline
        dlg.baseline_check.SetValue(toggle)
        dlg.on_toggle_controls(None)
        assert dlg.baseline_threshold_value.IsEnabled() is toggle

        # normalize
        dlg.normalize_check.SetValue(toggle)
        dlg.on_toggle_controls(None)
        assert dlg.normalize_choice.IsEnabled() is toggle

        dlg.Show()

    def test_dialog_ui_extra(self):
        dlg = PanelProcessHeatmap(self.frame, None)

        # smooth
        dlg.smooth_check.SetValue(True)
        dlg.smooth_choice.SetStringSelection("Gaussian")
        dlg.on_toggle_controls(None)
        assert dlg.smooth_sigma_value.IsEnabled() is True
        assert dlg.smooth_poly_order_value.IsEnabled() is False
        assert dlg.smooth_window_value.IsEnabled() is False
        dlg.smooth_choice.SetStringSelection("Savitzky-Golay")
        dlg.on_toggle_controls(None)
        assert dlg.smooth_sigma_value.IsEnabled() is False
        assert dlg.smooth_poly_order_value.IsEnabled() is True
        assert dlg.smooth_window_value.IsEnabled() is True

        dlg.Show()
