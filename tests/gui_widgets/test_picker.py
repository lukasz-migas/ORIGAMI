"""Test Comparison panel"""
# Third-party imports
import wx
import pytest

# Local imports
from origami.icons.assets import Icons
from origami.config.config import CONFIG
from origami.widgets.mz_picker.panel_peak_picker import PanelPeakPicker

from ..wxtc import WidgetTestCase


@pytest.mark.guitest
class TestPanelPeakPicker(WidgetTestCase):
    """Test dialog"""

    @pytest.mark.parametrize("method", ("native_local", "small_molecule", "native_differential"))
    def test_panel_create(self, get_env_with_document, method):
        # get environment
        env = get_env_with_document
        document = env.on_get_document()

        document_title = document.title
        dataset_name = "MassSpectra/Summed Spectrum"
        # instantiate icons
        icons = Icons()

        # setup peak picker
        dlg = PanelPeakPicker(None, None, icons, document_title=document_title, dataset_name=dataset_name, debug=True)

        # simulate pre-processing
        # self.sim_checkbox_click(dlg.preprocess_check, pre_process)
        # assert CONFIG.peak_panel_highlight is dlg.visualize_highlight_check.GetValue()

        wx.CallAfter(dlg.on_set_method, method)
        # dlg.on_set_method(method)
        # dlg.on_find_peaks(None)
        self.sim_button_click(dlg.find_peaks_btn)
        # self.sim_button_click(dlg.plot_peaks_btn)

        # simulate specify m/z range
        for value in [True, False]:
            self.sim_checkbox_click(dlg.mz_limit_check, value)
            assert CONFIG.peak_panel_specify_mz is dlg.mz_limit_check.GetValue() is value
            assert dlg.mz_min_value.IsEnabled() is value
            assert dlg.mz_max_value.IsEnabled() is value

        # change filter(s)
        for value in CONFIG.peak_panel_filter_choices:
            self.sim_combobox_click(dlg.post_filter_choice, value)
            assert CONFIG.peak_panel_filter_choice == dlg.post_filter_choice.GetStringSelection() == value

        # # update plot
        # simulate check highlights
        for value in [True, False]:
            self.sim_checkbox_click(dlg.visualize_highlight_check, value)
            assert CONFIG.peak_panel_highlight is dlg.visualize_highlight_check.GetValue() is value

        # simulate check scatter points
        for value in [True, False]:
            self.sim_checkbox_click(dlg.visualize_scatter_check, value)
            assert CONFIG.peak_panel_scatter is dlg.visualize_scatter_check.GetValue() is value

        # simulate check labels
        for value in [True, False]:
            self.sim_checkbox_click(dlg.visualize_show_labels_check, value)
            assert CONFIG.peak_panel_labels is dlg.visualize_show_labels_check.GetValue() is value
            assert dlg.visualize_show_labels_int_check.IsEnabled() is value
            assert dlg.visualize_show_labels_mz_check.IsEnabled() is value
            assert dlg.visualize_show_labels_width_check.IsEnabled() is value

        self.wait_for(200)
