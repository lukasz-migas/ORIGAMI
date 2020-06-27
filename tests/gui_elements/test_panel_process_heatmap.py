"""Test PanelAbout dialog"""
# Local imports
from origami.gui_elements.panel_process_heatmap import PanelProcessHeatmap

from ..wxtc import WidgetTestCase


class TestPanelProcessHeatmap(WidgetTestCase):
    """Test dialog"""

    def test_dialog_ok(self):
        dlg = PanelProcessHeatmap(self.frame, None)

        # wx.CallLater(250, dlg.on_close, None)
        dlg.Show()
        self.yield_()

    def test_dialog_no_plot(self):
        dlg = PanelProcessHeatmap(self.frame, None, disable_plot=True)

        assert dlg.plot_btn is None

        # wx.CallLater(250, dlg.on_close, None)
        dlg.Show()
        self.yield_()

    def test_dialog_no_process(self):
        dlg = PanelProcessHeatmap(self.frame, None, disable_process=True)

        assert dlg.add_to_document_btn is None

        # wx.CallLater(250, dlg.on_close, None)
        dlg.Show()
        self.yield_()

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
        self.yield_()

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
        self.yield_()
