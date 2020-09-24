"""Test `views`"""
# Third-party imports
import wx
import numpy as np
import pytest

# Local imports
from origami.objects.containers import IonHeatmapObject
from origami.gui_elements.views.view_heatmap_3d import ViewHeatmap3d

from ..wxtc import WidgetTestCase


@pytest.mark.guitest
class TestPlotView(WidgetTestCase):
    """Test panel"""

    def set_plot(self, view):
        """Set view in the panel"""
        sizer = wx.BoxSizer()
        sizer.Add(view.panel, 1, wx.EXPAND)
        self.frame.SetSizerAndFit(sizer)
        self.frame.Layout()
        self.frame.Hide()


@pytest.mark.guitest
class TestPanelViewHeatmap3d(TestPlotView):
    """Test dialog"""

    def test_panel_create(self):
        view = ViewHeatmap3d(self.frame, None)
        self.set_plot(view)

        # test plot using x/y
        obj = IonHeatmapObject(np.random.randint(0, 100, (3, 4)), np.arange(4), np.arange(3))

        # test plot using object
        view.plot(obj=obj)
        view.update(obj=obj)

        # there was a change in object size so have to fully redraw figure
        obj = IonHeatmapObject(np.random.randint(0, 100, (5, 6)), np.arange(6), np.arange(5))
        with pytest.raises(AttributeError):
            view.update(obj=obj)

        view.clear()
        assert view.figure.canvas.base_plot is None

        # # check popup
        popup = view.on_open_about(None)
        popup.Hide()
        assert popup

    def test_panel_update_style(self):
        view = ViewHeatmap3d(self.frame, None)
        self.set_plot(view)

        # cannot update style since plot has not been generated yet
        with pytest.raises(AttributeError):
            view.update_style(view.UPDATE_STYLES[0])

        obj = IonHeatmapObject(np.random.randint(0, 100, (3, 4)), np.arange(4), np.arange(3))
        view.plot(obj=obj)

        for name in view.UPDATE_STYLES:
            view.update_style(name)

        # style is not present in the allowed style(s)
        with pytest.raises(ValueError):
            view.update_style("NOT A STYLE")
