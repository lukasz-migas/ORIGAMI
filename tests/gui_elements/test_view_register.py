"""Test ViewRegister"""
# Third-party imports
import wx
import pytest
from pubsub import pub

# Local imports
from origami.gui_elements.views.view_register import ViewRegister
from origami.gui_elements.views.view_spectrum import ViewSpectrum

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
class TestViewRegister(TestPlotView):
    """Test dialog"""

    def test_init(self):
        view_reg = ViewRegister()
        assert isinstance(view_reg, ViewRegister)

    def test_add(self):
        view_reg = ViewRegister()

        view = ViewSpectrum(self.frame, (12, 8))
        self.set_plot(view)
        pub.sendMessage("view.activate", view_id=view.PLOT_ID)

        assert view_reg.active == view.PLOT_ID

    def test_register(self):
        view_reg = ViewRegister()

        view = ViewSpectrum(self.frame, (12, 8))
        self.set_plot(view)
        pub.sendMessage("view.activate", view_id=view.PLOT_ID)
        assert view_reg.active == view.PLOT_ID

        # will not do anything as the view is automatically registered
        pub.sendMessage("view.register", view_id=view.PLOT_ID, view=view)

        # try to give incorrect values
        with pytest.raises(ValueError):
            pub.sendMessage("view.register", view_id=123, view=view)

        with pytest.raises(ValueError):
            pub.sendMessage("view.register", view_id="123", view="not a view")

    def test_unregister(self):
        view_reg = ViewRegister()

        view = ViewSpectrum(self.frame, (12, 8))
        self.set_plot(view)
        pub.sendMessage("view.activate", view_id=view.PLOT_ID)
        assert view_reg.active == view.PLOT_ID

        # cannot unregister view that does not exist
        pub.sendMessage("view.unregister", view_id="RANDOMSTRING")

        pub.sendMessage("view.unregister", view_id=view.PLOT_ID)
        assert view_reg.active is None

    def test_activate(self):
        view_reg = ViewRegister()

        # false activation
        pub.sendMessage("view.activate", view_id="RANDOMSTRING")
        assert view_reg.active != "RANDOMSTRING"

        view_1 = ViewSpectrum(self.frame, (12, 8))
        self.set_plot(view_1)

        view_2 = ViewSpectrum(self.frame, (12, 8))
        self.set_plot(view_2)

        pub.sendMessage("view.activate", view_id=view_1.PLOT_ID)
        assert view_reg.active == view_1.PLOT_ID

        pub.sendMessage("view.activate", view_id=view_2.PLOT_ID)
        assert view_reg.active == view_2.PLOT_ID
