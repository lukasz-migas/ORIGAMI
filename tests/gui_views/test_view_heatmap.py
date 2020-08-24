"""Test `views`"""
# Third-party imports
import wx
import numpy as np
import pytest

# Local imports
from origami.objects.containers import IonHeatmapObject
from origami.objects.containers import MassSpectrumHeatmapObject
from origami.gui_elements.views.view_heatmap import ViewIonHeatmap
from origami.gui_elements.views.view_heatmap import ViewMassSpectrumHeatmap

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


@pytest.mark.guitest
class TestPanelViewIonHeatmap(TestPlotView):
    """Test dialog"""

    @pytest.mark.parametrize("plot_type", ("heatmap", "contour", "joint", "waterfall", "violin"))
    def test_panel_create(self, plot_type):
        view = ViewIonHeatmap(self.frame, (12, 12))
        self.set_plot(view)

        # test plot using x/y
        obj = IonHeatmapObject(np.random.randint(0, 100, (3, 4)), np.arange(4), np.arange(3))

        # test plot using object
        view.plot(obj=obj)
        assert view.figure.PLOT_TYPE == "heatmap"
        view.plot_contour(obj=obj)
        assert view.figure.PLOT_TYPE == "contour"
        view.plot_joint(obj=obj)
        assert view.figure.PLOT_TYPE == "joint"
        view.plot_violin(obj=obj)
        assert view.figure.PLOT_TYPE == "violin"
        view.plot_waterfall(obj=obj)
        assert view.figure.PLOT_TYPE == "waterfall"

        # replot data
        view.replot(plot_type)
        assert view.figure.PLOT_TYPE == plot_type

        # check popup
        popup = view.on_open_about(None)
        # # wx.CallLater(100, popup.on_dismiss, None)
        assert popup
        # # self.wait_for(150)

    def test_panel_update_heatmap_style(self):
        view = ViewIonHeatmap(self.frame, None)
        self.set_plot(view)

        # test plot using x/y
        obj = IonHeatmapObject(np.random.randint(0, 100, (3, 4)), np.arange(4), np.arange(3))

        # heatmap object
        view.plot(obj=obj)
        assert view.figure.PLOT_TYPE == "heatmap"
        view.update_style("heatmap")
        view.update_style("colorbar")
        view.update_style("normalization")

    def test_panel_update_violin_style(self):
        view = ViewIonHeatmap(self.frame, None)
        self.set_plot(view)

        # test plot using x/y
        obj = IonHeatmapObject(np.random.randint(0, 100, (3, 4)), np.arange(4), np.arange(3))
        # violin object
        view.plot_violin(obj=obj)
        assert view.figure.PLOT_TYPE == "violin"

        for style in view.UPDATE_STYLES:
            if not style.startswith("violin"):
                continue
            view.update_style(style)

    def test_panel_update_waterfall_style(self):
        view = ViewIonHeatmap(self.frame, None)
        self.set_plot(view)

        # test plot using x/y
        obj = IonHeatmapObject(np.random.randint(0, 100, (3, 4)), np.arange(4), np.arange(3))
        view.plot_waterfall(obj=obj)
        assert view.figure.PLOT_TYPE == "waterfall"

        for style in view.UPDATE_STYLES:
            if not style.startswith("waterfall"):
                continue
            view.update_style(style)


@pytest.mark.guitest
class TestPanelViewMassSpectrumHeatmap(TestPlotView):
    """Test dialog"""

    def test_panel_create(self):
        view = ViewMassSpectrumHeatmap(self.frame, (12, 12))
        self.set_plot(view)

        # test plot using x/y
        obj = MassSpectrumHeatmapObject(np.random.randint(0, 100, (3, 4)), np.arange(4), np.arange(3))

        # test plot using object
        view.plot(obj=obj)
        view.plot_joint(obj=obj)

        # check popup
        popup = view.on_open_about(None)
        # wx.CallLater(100, popup.on_dismiss, None)
        assert popup
        # self.wait_for(150)
