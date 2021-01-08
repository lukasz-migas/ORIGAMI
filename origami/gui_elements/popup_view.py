"""Persistent popup window with designated plot area"""
# Standard library imports
from typing import Dict

# Third-party imports
import wx

# Local imports
from origami.gui_elements.popup import PopupBase
from origami.gui_elements._panel import TestPanel  # noqa
from origami.gui_elements.views.view_heatmap import ViewHeatmap
from origami.gui_elements.views.view_spectrum import ViewMobilogram
from origami.gui_elements.views.view_spectrum import ViewChromatogram
from origami.gui_elements.views.view_spectrum import ViewMassSpectrum


class PopupViewBase(PopupBase):
    """Create popup window to modify few uncommon settings"""

    # Popup flags
    ENABLE_RIGHT_CLICK_DISMISS = False
    ENABLE_LEFT_DLICK_DISMISS = False
    ENABLE_INFO_MESSAGE = True

    PLOT_FIGURE_SIZE = (6, 3)
    PLOT_AXES_SIZE = (0.15, 0.3, 0.8, 0.65)
    INFO_MESSAGE = "You can click-and-drag in the plot area."

    title = None
    plot_view = None
    plot_panel = None
    plot_window = None

    def __init__(
        self, parent, style=wx.BORDER_SIMPLE, obj=None, allow_extraction: bool = False, callbacks: Dict = None
    ):
        self._allow_extraction = allow_extraction
        self._callbacks = callbacks
        if callbacks:
            if "CTRL" in callbacks:
                self.INFO_MESSAGE += " Hold CTRL + left-drag to extract data."

        PopupBase.__init__(self, parent, style)

        self.SetMinSize((400, 400))

        if obj is not None:
            self.plot(obj)

        self.Bind(wx.EVT_CONTEXT_MENU, self.on_right_click)

    def make_panel(self):
        """Make plot panel"""
        self.plot_panel = self.make_plot()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.plot_panel, 1, wx.EXPAND | wx.ALL, 2)
        self.set_info(sizer)
        self.set_close_btn(sizer)

        self.SetSizerAndFit(sizer)
        self.Layout()

    # noinspection DuplicatedCode
    def on_right_click(self, evt):
        """On right-click menu event"""
        # ensure that user clicked inside the plot area
        if hasattr(evt.EventObject, "figure"):
            menu = self.plot_view.get_right_click_menu(self)

            self.PopupMenu(menu)
            menu.Destroy()
            self.SetFocus()

    def plot(self, obj):
        """Update plot"""
        self.plot_view.plot(obj=obj)

    def make_plot(self):
        """Make plot panel"""
        raise NotImplementedError("Must implement method")


class PopupMobilogramView(PopupViewBase):
    """Create popup window that enables visualisation of mobilogram(s)"""

    def make_plot(self):
        """Make plot panel"""
        self.plot_view = ViewMobilogram(
            self,
            self.PLOT_FIGURE_SIZE,
            callbacks=self._callbacks,
            allow_extraction=self._allow_extraction,
            axes_size=self.PLOT_AXES_SIZE,
        )
        self.plot_panel = self.plot_view.panel
        self.plot_window = self.plot_view.figure

        return self.plot_panel


class PopupChromatogramView(PopupViewBase):
    """Create popup window that enables visualisation of mobilogram(s)"""

    def make_plot(self):
        """Make plot panel"""
        self.plot_view = ViewChromatogram(
            self,
            self.PLOT_FIGURE_SIZE,
            callbacks=self._callbacks,
            allow_extraction=self._allow_extraction,
            axes_size=self.PLOT_AXES_SIZE,
        )
        self.plot_panel = self.plot_view.panel
        self.plot_window = self.plot_view.figure

        return self.plot_panel


class PopupMassSpectrumView(PopupViewBase):
    """Create popup window that enables visualisation of mass spectrum/a"""

    def make_plot(self):
        """Make plot panel"""
        self.plot_view = ViewMassSpectrum(
            self,
            self.PLOT_FIGURE_SIZE,
            callbacks=self._callbacks,
            allow_extraction=self._allow_extraction,
            axes_size=self.PLOT_AXES_SIZE,
        )
        self.plot_panel = self.plot_view.panel
        self.plot_window = self.plot_view.figure

        return self.plot_panel


class PopupHeatmapView(PopupViewBase):
    """Create popup window that enables visualisation of mass spectrum/a"""

    PLOT_FIGURE_SIZE = (6, 6)
    PLOT_AXES_SIZE = (0.25, 0.25, 0.6, 0.6)

    def make_plot(self):
        """Make plot panel"""
        self.plot_view = ViewHeatmap(
            self,
            self.PLOT_FIGURE_SIZE,
            callbacks=self._callbacks,
            allow_extraction=self._allow_extraction,
            axes_size=self.PLOT_AXES_SIZE,
        )
        self.plot_panel = self.plot_view.panel
        self.plot_window = self.plot_view.figure

        return self.plot_panel


class TestPopup(TestPanel):
    """Test the popup window"""

    def __init__(self, parent):
        super().__init__(parent)

        self.btn_1.Bind(wx.EVT_BUTTON, self.on_popup)

    def on_popup(self, evt):
        """Activate popup"""
        import numpy as np
        from origami.objects.containers import MobilogramObject

        obj = MobilogramObject(np.arange(100), np.arange(100))
        p = PopupMobilogramView(self, obj=obj)
        p.position_on_event(evt)
        p.Show()


if __name__ == "__main__":

    def _main_popup():
        from origami.app import App

        app = App()

        dlg = TestPopup(None)
        wx.PostEvent(dlg.btn_1, wx.PyCommandEvent(wx.EVT_BUTTON.typeId, dlg.btn_1.GetId()))
        dlg.Show()

        app.MainLoop()

    _main_popup()
