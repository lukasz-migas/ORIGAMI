"""Test `views`"""
# Third-party imports
import wx
import pytest

# Local imports
from origami.objects.containers import MobilogramObject
from origami.widgets.ccs.view_ccs import ViewCCSFit
from origami.widgets.ccs.view_ccs import ViewCCSMobilogram

from ...wxtc import WidgetTestCase


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
class TestViewCCSFit(TestPlotView):
    """Test dialog"""

    @pytest.mark.parametrize("plot_type", ("scatter",))
    def test_panel_create(self, plot_type):
        view = ViewCCSFit(self.frame, (12, 8))
        self.set_plot(view)

        # test plot using x/y
        view.plot([1, 2, 3], [3, 2, 1])
        view.plot([1, 2, 3, 4], [1, 2, 3, 4])
        assert view.figure.PLOT_TYPE == plot_type

        # test plot using object
        mz_obj = MobilogramObject([1, 2, 3, 4], [2, 3, 1, 4])  # noqa
        view.plot(obj=mz_obj)

        # clear data
        view.clear()
        for key in view.DATA_KEYS:
            assert view._data[key] is None
        assert view.figure.PLOT_TYPE is None

        # check right-click menu
        menu = view.get_right_click_menu(self.frame)
        assert isinstance(menu, wx.Menu)

        # check popup
        popup = view.on_open_about(None)
        assert popup


@pytest.mark.guitest
class TestPanelViewCCSMobilogram(TestPlotView):
    """Test dialog"""

    @pytest.mark.parametrize("plot_type", ("line",))
    def test_panel_create(self, plot_type):
        view = ViewCCSMobilogram(self.frame, (12, 8))
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
            assert view._data[key] is None
        assert view.figure.PLOT_TYPE is None

        # check right-click menu
        menu = view.get_right_click_menu(self.frame)
        assert isinstance(menu, wx.Menu)

        # # check popup
        popup = view.on_open_about(None)
        assert popup

    def test_panel_update_style(self):
        view = ViewCCSMobilogram(self.frame, (12, 8))
        self.set_plot(view)

        # test plot using x/y
        obj = MobilogramObject([1, 2, 3, 4], [2, 3, 1, 4])  # noqa
        view.plot(obj=obj)

        for style in view.UPDATE_STYLES:
            view.update_style(style)
