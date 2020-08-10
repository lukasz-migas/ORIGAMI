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
        sizer = wx.BoxSizer()
        sizer.Add(view.panel, 1, wx.EXPAND)
        self.frame.SetSizerAndFit(sizer)
        self.frame.Layout()


@pytest.mark.guitest
class TestPanelViewMassSpectrum(TestPlotView):
    """Test dialog"""

    @pytest.mark.parametrize("plot_type", ("line",))
    def test_panel_create(self, plot_type):
        view = ViewMassSpectrum(self.frame, (12, 8))
        self.set_plot(view)

        # test plot using x/y
        view.plot([1, 2, 3], [3, 2, 1])
        view.plot([1, 2, 3, 4], [1, 2, 3, 4])

        # test plot using object
        mz_obj = MassSpectrumObject([1, 2, 3, 4], [2, 3, 1, 4])  # noqa
        view.plot(obj=mz_obj)
        assert view.figure.PLOT_TYPE == plot_type

        # replot data
        view.replot(plot_type)
        assert view.figure.PLOT_TYPE == plot_type

        # clear data
        view.clear()
        for key in view.DATA_KEYS:
            view._data[key] is None  # noqa
        assert view.figure.PLOT_TYPE is None

        # check right-click menu
        menu = view.get_right_click_menu(self.frame)
        assert isinstance(menu, wx.Menu)

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

    @pytest.mark.parametrize("plot_type", ("line",))
    def test_panel_create(self, plot_type):
        view = ViewChromatogram(self.frame, (12, 8))
        self.set_plot(view)

        # test plot using x/y
        view.plot([1, 2, 3], [3, 2, 1])
        view.plot([1, 2, 3, 4], [1, 2, 3, 4])

        # test plot using object
        mz_obj = ChromatogramObject([1, 2, 3, 4], [2, 3, 1, 4])  # noqa
        view.plot(obj=mz_obj)

        # replot data
        view.replot(plot_type)
        assert view.figure.PLOT_TYPE == plot_type

        # clear data
        view.clear()
        for key in view.DATA_KEYS:
            view._data[key] is None  # noqa
        assert view.figure.PLOT_TYPE is None

        # check right-click menu
        menu = view.get_right_click_menu(self.frame)
        assert isinstance(menu, wx.Menu)

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

    @pytest.mark.parametrize("plot_type", ("line",))
    def test_panel_create(self, plot_type):
        view = ViewMobilogram(self.frame, (12, 8))
        self.set_plot(view)

        # test plot using x/y
        view.plot([1, 2, 3], [3, 2, 1])
        view.plot([1, 2, 3, 4], [1, 2, 3, 4])

        # test plot using object
        mz_obj = MobilogramObject([1, 2, 3, 4], [2, 3, 1, 4])  # noqa
        view.plot(obj=mz_obj)

        # replot data
        view.replot(plot_type)
        assert view.figure.PLOT_TYPE == plot_type

        # clear data
        view.clear()
        for key in view.DATA_KEYS:
            view._data[key] is None  # noqa
        assert view.figure.PLOT_TYPE is None

        # check right-click menu
        menu = view.get_right_click_menu(self.frame)
        assert isinstance(menu, wx.Menu)

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

    @pytest.mark.parametrize("plot_type", ("line-compare",))
    def test_panel_create(self, plot_type):
        view = ViewCompareMassSpectra(self.frame, (12, 8))
        self.set_plot(view)

        # test plot using x/y
        view.plot([1, 2, 3], [1, 2, 3, 1], [3, 2, 1], [3, 2, 1, 3])
        view.plot([1, 2, 3, 4], [23, 1, 3], [1, 2, 3, 4], [3, 2, 1])

        # replot data
        view.replot(plot_type)
        assert view.figure.PLOT_TYPE == plot_type

        # clear data
        view.clear()
        for key in view.DATA_KEYS:
            view._data[key] is None  # noqa
        assert view.figure.PLOT_TYPE is None

        # check right-click menu
        menu = view.get_right_click_menu(self.frame)
        assert isinstance(menu, wx.Menu)
