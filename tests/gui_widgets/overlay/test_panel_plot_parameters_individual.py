"""Test plot settings panels"""
# Third-party imports
import pytest

# Local imports
from origami.widgets.overlay.plot_parameters.panel_rgb import PanelRGBSettings
from origami.widgets.overlay.plot_parameters.panel_rmsd import PanelRMSDSettings
from origami.widgets.overlay.plot_parameters.panel_rmsf import PanelRMSFSettings
from origami.widgets.overlay.plot_parameters.panel_grid_nxn import PanelGridNxNSettings
from origami.widgets.overlay.plot_parameters.panel_grid_tto import PanelGridTTOSettings
from origami.widgets.overlay.plot_parameters.panel_rmsd_matrix import PanelRMSDMatrixSettings

from ...wxtc import WidgetTestCase


@pytest.mark.guitest
class TestPanelRGBSettings(WidgetTestCase):
    """Test dialog"""

    def test_panel_create(self):
        dlg = PanelRGBSettings(self.frame, None)

        dlg.on_apply(None)
        dlg.on_toggle_controls(None)


@pytest.mark.guitest
class TestPanelGridNxNSettings(WidgetTestCase):
    """Test dialog"""

    def test_panel_create(self):
        dlg = PanelGridNxNSettings(self.frame, None)

        dlg.on_apply(None)
        dlg.on_toggle_controls(None)


@pytest.mark.guitest
class TestPanelGridTTOSettings(WidgetTestCase):
    """Test dialog"""

    def test_panel_create(self):
        dlg = PanelGridTTOSettings(self.frame, None)

        dlg.on_apply(None)
        dlg.on_toggle_controls(None)


@pytest.mark.guitest
class TestPanelRMSDSettings(WidgetTestCase):
    """Test dialog"""

    def test_panel_create(self):
        dlg = PanelRMSDSettings(self.frame, None)

        dlg.on_apply(None)
        dlg.on_toggle_controls(None)


@pytest.mark.guitest
class TestPanelRMSFSettings(WidgetTestCase):
    """Test dialog"""

    def test_panel_create(self):
        dlg = PanelRMSFSettings(self.frame, None)

        dlg.on_apply(None)
        dlg.on_toggle_controls(None)


@pytest.mark.guitest
class TestPanelRMSDMatrixSettings(WidgetTestCase):
    """Test dialog"""

    def test_panel_create(self):
        dlg = PanelRMSDMatrixSettings(self.frame, None)

        dlg.on_apply(None)
        dlg.on_toggle_controls(None)
