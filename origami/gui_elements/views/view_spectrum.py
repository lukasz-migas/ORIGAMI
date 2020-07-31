"""Viewer classes for spectral data"""
# Standard library imports
import logging

# Third-party imports
import wx
from pubsub import pub

# Local imports
from origami.utils.secret import get_short_hash
from origami.config.config import CONFIG
from origami.visuals.mpl.plot_spectrum import PlotSpectrum
from origami.gui_elements.views.view_base import ViewBase
from origami.gui_elements.views.view_base import ViewMPLMixin

LOGGER = logging.getLogger(__name__)


class ViewSpectrumPanelMixin:
    """Spectrum panel base"""

    @staticmethod
    def make_panel(parent, figsize, plot_id, axes_size=None):
        """Initialize plot panel"""
        plot_panel = wx.Panel(parent)
        plot_window = PlotSpectrum(plot_panel, figsize=figsize, axes_size=axes_size, plot_id=plot_id)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(plot_window, 1, wx.EXPAND)
        plot_panel.SetSizer(sizer)
        sizer.Fit(plot_panel)

        return plot_panel, plot_window, sizer


class ViewSpectrum(ViewBase, ViewMPLMixin, ViewSpectrumPanelMixin):
    """Viewer class for spectral data"""

    VIEW_TYPE = "1d"
    DATA_KEYS = ("x", "y", "obj")
    MPL_KEYS = ["1D"]
    UPDATE_STYLES = ("line", "fill")
    ALLOWED_PLOTS = ("line", "waterfall")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.PLOT_ID = get_short_hash()
        self.panel, self.figure, self.sizer = self.make_panel(self.parent, self.figsize, self.PLOT_ID, self.axes_size)

        # register view
        pub.sendMessage("view.register", view_id=self.PLOT_ID, view=self)

    def _update(self):
        """Update plot with current data"""
        self.update(self._data["x"], self._data["y"], **self._plt_kwargs)

    @staticmethod
    def check_input(x, y, obj):
        """Ensure that input is correct"""
        if x is None and y is None and obj is None:
            raise ValueError("You must provide the x/y values or container object")
        if x is None and y is None and obj is not None:
            x = obj.x
            y = obj.y
        return x, y

    def check_kwargs(self, **kwargs):
        """Check kwargs"""
        if "allow_extraction" not in kwargs:
            kwargs["allow_extraction"] = self._allow_extraction
        return kwargs

    def plot(self, x=None, y=None, obj=None, repaint: bool = True, **kwargs):
        """Simple line plot"""
        # try to update plot first, as it can be quicker
        self.set_document(obj, **kwargs)
        self.set_labels(obj, **kwargs)

        kwargs.update(**CONFIG.get_mpl_parameters(self.MPL_KEYS))
        kwargs = self.check_kwargs(**kwargs)

        try:
            self.update(x, y, obj, repaint=repaint, **kwargs)
        except AttributeError:
            x, y = self.check_input(x, y, obj)
            self.figure.clear()
            self.figure.plot_1d(x, y, x_label=self.x_label, y_label=self.y_label, callbacks=self._callbacks, **kwargs)
            if repaint:
                self.figure.repaint()

            # set data
            self._data.update(x=x, y=y, obj=obj)
            self._plt_kwargs = kwargs
            LOGGER.debug("Plotted data")

    def update(self, x=None, y=None, obj=None, repaint: bool = True, **kwargs):
        """Update plot without having to clear it"""
        self.set_document(obj, **kwargs)
        self.set_labels(obj, **kwargs)

        # update plot
        x, y = self.check_input(x, y, obj)
        self.figure.plot_1d_update_data(x, y, self.x_label, self.y_label, **kwargs)
        if repaint:
            self.figure.repaint()

        # set data
        self._data.update(x=x, y=y, obj=obj)
        self._plt_kwargs = kwargs
        LOGGER.debug("Updated plot data")

    def replot(self, **kwargs):
        """Replot the current plot"""
        if kwargs is None:
            kwargs = self._plt_kwargs

        self.update(self._data["x"], self._data["y"], **kwargs)

    def update_style(self, name: str):
        """Update plot style"""
        if name.startswith("line"):
            self.figure.plot_1d_update_style_by_label(
                gid=None,
                color=CONFIG.lineColour_1D,
                line_style=CONFIG.lineStyle_1D,
                line_width=CONFIG.lineWidth_1D,
                #                 transparency=CONFIG.XXX,
            )
        elif name.startswith("fill"):
            self.figure.plot_1d_update_patch_style_by_label(
                gid=None,
                show=CONFIG.lineShadeUnder_1D,
                color=CONFIG.lineShadeUnderColour_1D,
                transparency=CONFIG.lineShadeUnderTransparency_1D,
                x=self._data["x"],
                y=self._data["y"],
                fill_kwargs=CONFIG.get_mpl_parameters(self.MPL_KEYS),
            )

        self.figure.repaint()


class ViewMassSpectrum(ViewSpectrum):
    """Specialized viewer for mass spectral data"""

    def __init__(self, parent, figsize, title="MassSpectrum", **kwargs):
        ViewSpectrum.__init__(self, parent, figsize, title, **kwargs)
        self._x_label = kwargs.pop("x_label", "m/z (Da)")
        self._y_label = kwargs.pop("y_label", "Intensity")


class ViewChromatogram(ViewSpectrum):
    """Specialized viewer for chromatographic data"""

    def __init__(self, parent, figsize, title="Chromatogram", **kwargs):
        ViewSpectrum.__init__(self, parent, figsize, title, **kwargs)
        self._x_label = kwargs.pop("x_label", "Scans")
        self._y_label = kwargs.pop("y_label", "Intensity")


class ViewMobilogram(ViewSpectrum):
    """Specialized viewer for mobilogram data"""

    def __init__(self, parent, figsize, title="Mobilogram", **kwargs):
        ViewSpectrum.__init__(self, parent, figsize, title, **kwargs)
        self._x_label = kwargs.pop("x_label", "Drift time (bins)")
        self._y_label = kwargs.pop("y_label", "Intensity")


class ViewCompareSpectra(ViewBase, ViewSpectrumPanelMixin):
    """Viewer class for comparison of spectral data"""

    DATA_KEYS = ("x_top", "x_bottom", "y_top", "y_bottom", "labels")
    MPL_KEYS = ["1D"]
    ALLOWED_PLOTS = ("line-compare",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.PLOT_ID = get_short_hash()
        self.panel, self.figure, self.sizer = self.make_panel(self.parent, self.figsize, self.PLOT_ID)

        # register view
        pub.sendMessage("view.register", view_id=self.PLOT_ID, view=self)

    @staticmethod
    def check_input(x_top, x_bottom, y_top, y_bottom, obj_top, obj_bottom):
        """Ensure that input is correct"""
        if x_top is None and y_top is None and obj_top is None:
            raise ValueError("You must provide the x/y values or container object")
        if x_top is None and y_top is None and obj_top is not None:
            x_top = obj_top.x
            y_top = obj_top.y
        if x_bottom is None and y_bottom is None and obj_bottom is None:
            raise ValueError("You must provide the x/y values or container object")
        if x_bottom is None and y_bottom is None and obj_bottom is not None:
            x_bottom = obj_top.x
            y_bottom = obj_top.y

        return x_top, x_bottom, y_top, y_bottom

    def plot(
        self, x_top=None, x_bottom=None, y_top=None, y_bottom=None, obj_top=None, obj_bottom=None, labels=None, **kwargs
    ):
        """Simple line plot"""
        # try to update plot first, as it can be quicker
        # self.set_document(obj, **kwargs)
        # self.set_labels(obj, **kwargs)

        if labels is None:
            labels = ["", ""]
        kwargs.update(**CONFIG.get_mpl_parameters(self.MPL_KEYS))

        try:
            self.update(x_top, x_bottom, y_top, y_bottom, obj_top, obj_bottom, labels, **kwargs)
        except AttributeError:
            x_top, x_bottom, y_top, y_bottom = self.check_input(x_top, x_bottom, y_top, y_bottom, obj_top, obj_bottom)
            self.figure.clear()
            self.figure.plot_1d_compare(
                x_top,
                x_bottom,
                y_top,
                y_bottom,
                labels=labels,
                x_label=self.x_label,
                y_label=self.y_label,
                callbacks=self._callbacks,
                allow_extraction=self._allow_extraction,
                **kwargs,
            )
            self.figure.repaint()

            # set data
            self._data.update(x_top=x_top, x_bottom=x_bottom, y_top=y_top, y_bottom=y_bottom, labels=labels)
            self._plt_kwargs = kwargs
            LOGGER.debug("Plotted data")

    def update(
        self, x_top=None, x_bottom=None, y_top=None, y_bottom=None, obj_top=None, obj_bottom=None, labels=None, **kwargs
    ):
        """Update plot without having to clear it"""
        # self.set_document(obj, **kwargs)
        # self.set_labels(obj, **kwargs)
        if labels is None:
            labels = ["", ""]
        # update plot
        x_top, x_bottom, y_top, y_bottom = self.check_input(x_top, x_bottom, y_top, y_bottom, obj_top, obj_bottom)
        self.figure.plot_1d_compare_update_data(x_top, x_bottom, y_top, y_bottom, labels, **kwargs)
        self.figure.repaint()

        # set data
        self._data.update(x_top=x_top, x_bottom=x_bottom, y_top=y_top, y_bottom=y_bottom, labels=labels)
        self._plt_kwargs = kwargs
        LOGGER.debug("Updated plot data")

    def replot(self, **kwargs):
        """Replot the current plot"""
        if kwargs is None:
            kwargs = self._plt_kwargs

        self.update(
            self._data["x_top"],
            self._data["x_bottom"],
            self._data["y_top"],
            self._data["y_bottom"],
            self._data["labels"],
            **kwargs,
        )

    def _update(self):
        pass

    def update_style(self, *args, **kwargs):
        """Update plot style"""
        self.figure.plot_1d_update_style_by_label(*args, **kwargs)
        self.figure.repaint()


class ViewCompareMassSpectra(ViewCompareSpectra):
    """Specialized viewer for comparison of mass spectral data"""

    def __init__(self, parent, figsize, title="CompareMassSpectra", **kwargs):
        ViewCompareSpectra.__init__(self, parent, figsize, title=title, **kwargs)
        self._x_label = kwargs.pop("x_label", "m/z (Da)")
        self._y_label = kwargs.pop("y_label", "Intensity")


class _TestFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None)

        mz_obj = MassSpectrumObject()  # noqa
        view_ms = ViewMassSpectrum(self, (12, 8))
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(view_ms.panel, 1, wx.EXPAND)

        view_ms.plot([1, 2, 3], [1, 3, 1])

        self.SetSizerAndFit(sizer)
        self.Layout()


def _main():

    app = wx.App()

    ex = _TestFrame()

    ex.Show()
    app.MainLoop()


if __name__ == "__main__":
    _main()
