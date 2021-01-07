"""Test toast"""
# Third-party imports
import numpy as np
import pytest

# Local imports
from origami.utils.test import WidgetTestCase
from origami.objects.containers import IonHeatmapObject
from origami.objects.containers import MobilogramObject
from origami.objects.containers import ChromatogramObject
from origami.objects.containers import MassSpectrumObject
from origami.gui_elements.popup_view import PopupHeatmapView
from origami.gui_elements.popup_view import PopupMobilogramView
from origami.gui_elements.popup_view import PopupChromatogramView
from origami.gui_elements.popup_view import PopupMassSpectrumView

# This test suite should be run last to avoid crashing other UI tests


@pytest.mark.guitest
class TestPopupMobilogramView(WidgetTestCase):
    """Test dialog"""

    def test_mobilogram_popup_view(self):
        obj = MobilogramObject(np.arange(10), np.arange(10))

        p = PopupMobilogramView(self.frame, obj=obj)
        p.position_on_window(self.frame)
        p.Show()

    def test_chromatogram_popup_view(self):
        obj = ChromatogramObject(np.arange(10), np.arange(10))

        p = PopupChromatogramView(self.frame, obj=obj)
        p.position_on_window(self.frame)
        p.Show()

    def test_mass_spectrum_popup_view(self):
        obj = MassSpectrumObject(np.arange(10), np.arange(10))

        p = PopupMassSpectrumView(self.frame, obj=obj)
        p.position_on_window(self.frame)
        p.Show()

    def test_heatmap_popup_view(self):
        obj = IonHeatmapObject(np.zeros((10, 10)), np.arange(10), np.arange(10))

        p = PopupHeatmapView(self.frame, obj=obj)
        p.position_on_window(self.frame)
        p.Show()
