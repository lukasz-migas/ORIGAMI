"""Test `views`"""
# Third-party imports
import wx
import pytest

# Local imports
from origami.objects.containers import MobilogramObject
from origami.objects.containers import ChromatogramObject
from origami.objects.containers import MassSpectrumObject
from origami.gui_elements.views.view_spectrum import ViewMobilogram
from origami.gui_elements.views.view_spectrum import ViewChromatogram
from origami.gui_elements.views.view_spectrum import ViewMassSpectrum
from origami.gui_elements.views.view_spectrum import ViewCompareMassSpectra

from ..wxtc import WidgetTestCase


@pytest.mark.guitest
class TestPlotView(WidgetTestCase):
    """Test panel"""

    def set_plot(self, view):
        """Set view in the panel"""
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(view.panel, 1, wx.EXPAND)
        self.frame.SetSizerAndFit(sizer)
        self.frame.Layout()


@pytest.mark.guitest
class TestPanelViewMassSpectrum(TestPlotView):
    """Test dialog"""

    def test_panel_create(self):
        view = ViewMassSpectrum(self.frame, (12, 8))
        self.set_plot(view)

        # test plot using x/y
        view.plot([1, 2, 3], [3, 2, 1])
        view.plot([1, 2, 3, 4], [1, 2, 3, 4])

        # test plot using object
        mz_obj = MassSpectrumObject([1, 2, 3, 4], [2, 3, 1, 4])  # noqa
        view.plot(obj=mz_obj)

    def test_panel_update_style(self):
        view = ViewMassSpectrum(self.frame, (12, 8))
        self.set_plot(view)

        # test plot using x/y
        obj = MassSpectrumObject([1, 2, 3, 4], [2, 3, 1, 4])  # noqa
        view.plot(obj=obj)

        for style in view.UPDATE_STYLES:
            view.update_style(style)


@pytest.mark.guitest
class TestPanelViewChromatogram(TestPlotView):
    """Test dialog"""

    def test_panel_create(self):
        view = ViewChromatogram(self.frame, (12, 8))
        self.set_plot(view)

        # test plot using x/y
        view.plot([1, 2, 3], [3, 2, 1])
        view.plot([1, 2, 3, 4], [1, 2, 3, 4])

        # test plot using object
        mz_obj = ChromatogramObject([1, 2, 3, 4], [2, 3, 1, 4])  # noqa
        view.plot(obj=mz_obj)

    def test_panel_update_style(self):
        view = ViewChromatogram(self.frame, (12, 8))
        self.set_plot(view)

        # test plot using x/y
        obj = ChromatogramObject([1, 2, 3, 4], [2, 3, 1, 4])  # noqa
        view.plot(obj=obj)

        for style in view.UPDATE_STYLES:
            view.update_style(style)


@pytest.mark.guitest
class TestPanelViewMobilogram(TestPlotView):
    """Test dialog"""

    def test_panel_create(self):
        view = ViewMobilogram(self.frame, (12, 8))
        self.set_plot(view)

        # test plot using x/y
        view.plot([1, 2, 3], [3, 2, 1])
        view.plot([1, 2, 3, 4], [1, 2, 3, 4])

        # test plot using object
        mz_obj = MobilogramObject([1, 2, 3, 4], [2, 3, 1, 4])  # noqa
        view.plot(obj=mz_obj)

    def test_panel_update_style(self):
        view = ViewMobilogram(self.frame, (12, 8))
        self.set_plot(view)

        # test plot using x/y
        obj = MobilogramObject([1, 2, 3, 4], [2, 3, 1, 4])  # noqa
        view.plot(obj=obj)

        for style in view.UPDATE_STYLES:
            view.update_style(style)


@pytest.mark.guitest
class TestPanelViewCompareMassSpectra(TestPlotView):
    """Test dialog"""

    def test_panel_create(self):
        view = ViewCompareMassSpectra(self.frame, (12, 8))
        self.set_plot(view)

        # test plot using x/y
        view.plot([1, 2, 3], [1, 2, 3, 1], [3, 2, 1], [3, 2, 1, 3])
        view.plot([1, 2, 3, 4], [23, 1, 3], [1, 2, 3, 4], [3, 2, 1])
