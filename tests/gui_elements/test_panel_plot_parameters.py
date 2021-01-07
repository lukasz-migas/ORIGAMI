"""Test PanelAbout dialog"""
# Third-party imports
import pytest

# Local imports
from origami.utils.test import WidgetTestCase
from origami.gui_elements.panel_plot_parameters import PanelVisualisationSettingsEditor


@pytest.mark.guitest
class TestPanelVisualisationSettingsEditor(WidgetTestCase):
    """Test dialog"""

    def test_panel_create(self):
        dlg = PanelVisualisationSettingsEditor(self.frame, None)

        # change page(s)
        # -> Plot 1D
        dlg.on_set_page("Plot 1D")
        assert dlg.current_page == "Plot 1D"

        # -> Colorbar
        dlg.on_set_page("Colorbar")
        assert dlg.current_page == "Colorbar"

        # -> Plot 1D
        dlg.on_set_page(1)
        assert dlg.current_page == "Plot 1D"
