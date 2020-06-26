"""Test PanelAbout dialog"""
# Third-party imports
import wx

# Local imports
from origami.gui_elements.panel_process_spectrum import PanelProcessMassSpectrum

from ..wxtc import WidgetTestCase


class TestPanelProcessMassSpectrum(WidgetTestCase):
    """Test dialog"""

    def test_dialog_ok(self):
        dlg = PanelProcessMassSpectrum(self.frame, None)

        wx.CallLater(250, dlg.on_close, None)
        dlg.Show()
        self.yield_()

    def test_dialog_no_plot(self):
        dlg = PanelProcessMassSpectrum(self.frame, None, disable_plot=True)

        assert dlg.plot_btn is None

        wx.CallLater(250, dlg.on_close, None)
        dlg.Show()
        self.yield_()

    def test_dialog_no_process(self):
        dlg = PanelProcessMassSpectrum(self.frame, None, disable_process=True)

        assert dlg.add_to_document_btn is None

        wx.CallLater(250, dlg.on_close, None)
        dlg.Show()
        self.yield_()

    def test_dialog_ui(self):
        dlg = PanelProcessMassSpectrum(self.frame, None)

        toggle = False
        # crop
        dlg.ms_process_crop.SetValue(toggle)
        dlg.on_toggle_controls(None)
        assert dlg.crop_min_value.IsEnabled() is toggle
        assert dlg.crop_max_value.IsEnabled() is toggle

        # linearize
        dlg.ms_process_linearize.SetValue(toggle)
        dlg.on_toggle_controls(None)
        assert dlg.bin_linearization_method_choice.IsEnabled() is toggle
        assert dlg.bin_mzBinSize_value.IsEnabled() is toggle
        assert dlg.bin_mzStart_value.IsEnabled() is toggle
        assert dlg.bin_mzEnd_value.IsEnabled() is toggle
        assert dlg.bin_autoRange_check.IsEnabled() is toggle

        # smooth
        dlg.ms_process_smooth.SetValue(toggle)
        dlg.on_toggle_controls(None)
        assert dlg.ms_sigma_value.IsEnabled() is toggle
        assert dlg.ms_polynomial_value.IsEnabled() is toggle
        assert dlg.ms_window_value.IsEnabled() is toggle
        assert dlg.ms_smooth_moving_window.IsEnabled() is toggle

        # baseline
        dlg.ms_process_threshold.SetValue(toggle)
        dlg.on_toggle_controls(None)
        assert dlg.ms_threshold_value.IsEnabled() is toggle
        assert dlg.ms_baseline_choice.IsEnabled() is toggle
        assert dlg.ms_baseline_polynomial_order.IsEnabled() is toggle
        assert dlg.ms_baseline_curved_window.IsEnabled() is toggle
        assert dlg.ms_baseline_median_window.IsEnabled() is toggle
        assert dlg.ms_baseline_tophat_window.IsEnabled() is toggle

        wx.CallLater(250, dlg.on_close, None)
        dlg.Show()
        self.yield_()
