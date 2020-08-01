"""Test PanelAbout dialog"""
# Third-party imports
import pytest

# Local imports
from origami.gui_elements.plot_parameters.panel_1d import Panel1dSettings
from origami.gui_elements.plot_parameters.panel_2d import Panel2dSettings
from origami.gui_elements.plot_parameters.panel_3d import Panel3dSettings
from origami.gui_elements.plot_parameters.panel_ui import PanelUISettings
from origami.gui_elements.plot_parameters.panel_rmsd import PanelRMSDSettings
from origami.gui_elements.plot_parameters.panel_sizes import PanelSizesSettings
from origami.gui_elements.plot_parameters.panel_legend import PanelLegendSettings
from origami.gui_elements.plot_parameters.panel_violin import PanelViolinSettings
from origami.gui_elements.plot_parameters.panel_general import PanelGeneralSettings
from origami.gui_elements.plot_parameters.panel_colorbar import PanelColorbarSettings
from origami.gui_elements.plot_parameters.panel_waterfall import PanelWaterfallSettings

from ..wxtc import WidgetTestCase


@pytest.mark.guitest
class TestPanelGeneralSettings(WidgetTestCase):
    """Test dialog"""

    def test_panel_create(self):
        dlg = PanelGeneralSettings(self.frame, None)

        # update settings
        dlg.plot_axis_on_off_check.SetValue(True)
        dlg.on_toggle_controls(None)
        dlg.on_apply(None)
        assert dlg.plot_right_spines_check.IsEnabled() is True
        assert dlg.plot_frame_width_value.IsEnabled() is True

        dlg.plot_axis_on_off_check.SetValue(False)
        dlg.on_toggle_controls(None)
        dlg.on_apply(None)
        assert dlg.plot_right_spines_check.IsEnabled() is False
        assert dlg.plot_frame_width_value.IsEnabled() is False


@pytest.mark.guitest
class TestPanel1dSettings(WidgetTestCase):
    """Test dialog"""

    def test_panel_create(self):
        dlg = Panel1dSettings(self.frame, None)

        # update settings
        dlg.plot1d_marker_edge_color_check.SetValue(True)  # enable marker
        dlg.plot1d_underline_check.SetValue(True)  # enable shade
        dlg.bar_color_edge_check.SetValue(True)  # enable bar
        dlg.on_toggle_controls(None)
        dlg.on_apply(None)
        assert dlg.plot1d_underline_alpha_value.IsEnabled() is True
        assert dlg.plot1d_underline_color_btn.IsEnabled() is True
        assert dlg.plot1d_marker_edge_color_btn.IsEnabled() is True
        assert dlg.bar_edge_color_btn.IsEnabled() is True

        dlg.plot1d_marker_edge_color_check.SetValue(False)  # enable marker
        dlg.plot1d_underline_check.SetValue(False)  # enable shade
        dlg.bar_color_edge_check.SetValue(False)  # enable bar
        dlg.on_toggle_controls(None)
        dlg.on_apply(None)
        assert dlg.plot1d_underline_alpha_value.IsEnabled() is False
        assert dlg.plot1d_underline_color_btn.IsEnabled() is False
        assert dlg.plot1d_marker_edge_color_btn.IsEnabled() is False
        assert dlg.bar_edge_color_btn.IsEnabled() is False


@pytest.mark.guitest
class TestPanel2dSettings(WidgetTestCase):
    """Test dialog"""

    def test_panel_create(self):
        dlg = Panel2dSettings(self.frame, None)

        dlg.on_apply(None)
        dlg.on_toggle_controls(None)


@pytest.mark.guitest
class TestPanel3dSettings(WidgetTestCase):
    """Test dialog"""

    def test_panel_create(self):
        dlg = Panel3dSettings(self.frame, None)

        dlg.on_apply(None)
        dlg.on_toggle_controls(None)


@pytest.mark.guitest
class TestPanelColorbarSettings(WidgetTestCase):
    """Test dialog"""

    def test_panel_create(self):
        dlg = PanelColorbarSettings(self.frame, None)

        dlg.on_apply(None)
        dlg.on_toggle_controls(None)

        # update controls
        dlg.colorbar_tgl.SetValue(True)
        dlg.on_toggle_controls(None)
        assert dlg.colorbar_fontsize_value.IsEnabled() is True

        # change position
        dlg.colorbar_position_value.SetStringSelection("left")
        dlg.on_toggle_controls(None)
        assert dlg.colorbar_width_inset_value.IsEnabled() is False
        assert dlg.colorbar_pad_value.IsEnabled() is True

        dlg.colorbar_position_value.SetStringSelection("inside (top-left)")
        dlg.on_toggle_controls(None)
        assert dlg.colorbar_width_inset_value.IsEnabled() is True
        assert dlg.colorbar_pad_value.IsEnabled() is False

        dlg.colorbar_tgl.SetValue(False)
        dlg.on_toggle_controls(None)
        assert dlg.colorbar_fontsize_value.IsEnabled() is False


@pytest.mark.guitest
class TestPanelWaterfallSettings(WidgetTestCase):
    """Test dialog"""

    def test_panel_create(self):
        dlg = PanelWaterfallSettings(self.frame, None)

        dlg.on_apply(None)
        dlg.on_toggle_controls(None)


@pytest.mark.guitest
class TestPanelViolinSettings(WidgetTestCase):
    """Test dialog"""

    def test_panel_create(self):
        dlg = PanelViolinSettings(self.frame, None)

        dlg.on_apply(None)
        dlg.on_toggle_controls(None)


@pytest.mark.guitest
class TestPanelLegendSettings(WidgetTestCase):
    """Test dialog"""

    def test_panel_create(self):
        dlg = PanelLegendSettings(self.frame, None)

        dlg.on_apply(None)
        dlg.on_toggle_controls(None)

        # update controls
        dlg.legend_toggle.SetValue(True)
        dlg.on_toggle_controls(None)
        assert dlg.legend_position_value.IsEnabled() is True

        dlg.legend_toggle.SetValue(False)
        dlg.on_toggle_controls(None)
        assert dlg.legend_position_value.IsEnabled() is False


@pytest.mark.guitest
class TestPanelSizesSettings(WidgetTestCase):
    """Test dialog"""

    def test_panel_create(self):
        dlg = PanelSizesSettings(self.frame, None)

        dlg.on_apply(None)
        dlg.on_toggle_controls(None)


@pytest.mark.guitest
class TestPanelUISettings(WidgetTestCase):
    """Test dialog"""

    def test_panel_create(self):
        dlg = PanelUISettings(self.frame, None)

        dlg.on_apply(None)
        dlg.on_toggle_controls(None)


@pytest.mark.guitest
class TestPanelRMSDSettings(WidgetTestCase):
    """Test dialog"""

    def test_panel_create(self):
        dlg = PanelRMSDSettings(self.frame, None)

        dlg.on_apply(None)
        dlg.on_toggle_controls(None)
