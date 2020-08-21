"""Viewer classes for spectral data"""
# Standard library imports
import time
import logging

# Third-party imports
import wx
from pubsub import pub

# Local imports
from origami.utils.secret import get_short_hash
from origami.config.config import CONFIG
from origami.utils.utilities import report_time
from origami.visuals.mpl.plot_spectrum import PlotSpectrum
from origami.gui_elements.views.view_base import ViewBase
from origami.gui_elements.views.view_base import ViewMPLMixin
from origami.gui_elements.views.view_mixins import ViewAxesMixin

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


class ViewSpectrum(ViewBase, ViewMPLMixin, ViewSpectrumPanelMixin, ViewAxesMixin):
    """Viewer class for spectral data"""

    VIEW_TYPE = "1d"
    DATA_KEYS = ("x", "y", "obj")
    MPL_KEYS = ["1d", "axes", "legend"]
    UPDATE_STYLES = ("line", "fill")
    ALLOWED_PLOTS = ("line", "waterfall")
    DEFAULT_PLOT = "line"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.PLOT_ID = get_short_hash()
        self.panel, self.figure, self.sizer = self.make_panel(self.parent, self.figsize, self.PLOT_ID, self.axes_size)

        # register view
        pub.sendMessage("view.register", view_id=self.PLOT_ID, view=self)

    def _update(self):
        """Update plot with current data"""
        self.update(self._data["x"], self._data["y"], **self._plt_kwargs)

    def check_input(self, x, y, obj):
        """Ensure that input is correct"""
        if x is None and y is None and obj is None:
            raise ValueError("You must provide the x/y values or container object")
        if x is None and y is None and obj is not None:
            x = obj.x
            y = obj.y
            self._x_label = obj.x_label
            self._y_label = obj.y_label
        return x, y

    def check_kwargs(self, **kwargs):
        """Check kwargs"""
        if "allow_extraction" not in kwargs:
            kwargs["allow_extraction"] = self._allow_extraction
        return kwargs

    def plot(self, x=None, y=None, obj=None, repaint: bool = True, **kwargs):
        """Simple line plot"""
        # try to update plot first, as it can be quicker
        t_start = time.time()
        self.set_document(obj, **kwargs)
        self.set_labels(obj, **kwargs)

        kwargs.update(**CONFIG.get_mpl_parameters(self.MPL_KEYS))
        kwargs.update(**self.FORCED_KWARGS)
        kwargs = self.check_kwargs(**kwargs)

        try:
            self.update(x, y, obj, repaint=repaint, **kwargs)
        except (AttributeError, OverflowError):
            x, y = self.check_input(x, y, obj)
            self.figure.clear()
            self.figure.plot_1d(x, y, x_label=self.x_label, y_label=self.y_label, callbacks=self._callbacks, **kwargs)
            self.figure.repaint(repaint)

            # set data
            self._data.update(x=x, y=y, obj=obj)
            self.set_plot_parameters(**kwargs)
            LOGGER.debug(f"Plotted data in {report_time(t_start)}")

    def update(self, x=None, y=None, obj=None, repaint: bool = True, **kwargs):
        """Update plot without having to clear it"""
        t_start = time.time()
        self.set_document(obj, **kwargs)
        self.set_labels(obj, **kwargs)

        # update plot
        x, y = self.check_input(x, y, obj)
        self.figure.plot_1d_update_data(x, y, self.x_label, self.y_label, **kwargs)
        self.figure.on_check_zoom_state(x, y)
        self.figure.repaint(repaint)

        # set data
        self._data.update(x=x, y=y, obj=obj)
        self.set_plot_parameters(**kwargs)
        LOGGER.debug(f"Plotted data in {report_time(t_start)}")

    def add_line(self, x=None, y=None, obj=None, label: str = "", gid: str = "", line_color=(1, 0, 0), **kwargs):
        """Add line to the plot"""
        kwargs.update(**CONFIG.get_mpl_parameters(self.MPL_KEYS))
        kwargs.update(**self.FORCED_KWARGS)
        kwargs = self.check_kwargs(**kwargs)

        x, y = self.check_input(x, y, obj)
        self.figure.plot_1d_add_line(x, y, label=label, gid=gid, line_color=line_color, **kwargs)
        self.figure.repaint()

    def remove_line(self, gid: str):
        """Remove line from the plot"""
        # self.figure.remove_lin

    def replot(self, plot_type: str = None, repaint: bool = True, light_clear: bool = False):
        """Replot the current plot"""
        # get plot_type
        plot_type = self.get_plot_type(plot_type)

        if light_clear:
            self.light_clear()

        # get replot data
        x, y, obj = self.get_data(self.DATA_KEYS)
        if plot_type == "line":
            self.plot(x, y, obj, repaint=repaint)

    def update_style(self, name: str):
        """Update plot style"""
        t_start = time.time()
        kwargs = dict()
        if name.startswith("line"):
            self.figure.plot_1d_update_style_by_label(
                spectrum_line_color=CONFIG.spectrum_line_color,
                spectrum_line_style=CONFIG.spectrum_line_style,
                spectrum_line_width=CONFIG.spectrum_line_width,
            )
        elif name.startswith("fill"):
            self.figure.plot_1d_update_patch_style_by_label(
                spectrum_line_fill_under=CONFIG.spectrum_line_fill_under,
                spectrum_fill_color=CONFIG.spectrum_fill_color,
                spectrum_fill_transparency=CONFIG.spectrum_fill_transparency,
                x=self._data["x"],
                y=self._data["y"],
                fill_kwargs=CONFIG.get_mpl_parameters(self.MPL_KEYS),
            )
        elif name.startswith("axes"):
            kwargs = self._update_style_axes(name)
        elif name.startswith("legend"):
            kwargs = CONFIG.get_mpl_parameters(["legend"])
            self.figure.plot_update_legend(**kwargs)
        self.figure.repaint()
        self.set_plot_parameters(**kwargs)
        LOGGER.debug(f"Updated plot styles - {name} in {report_time(t_start)}")


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

    DATA_KEYS = ("x_top", "x_bottom", "y_top", "y_bottom", "obj_top", "obj_bottom", "labels")
    MPL_KEYS = ["1d", "axes", "compare"]
    ALLOWED_PLOTS = ("line-compare",)
    DEFAULT_PLOT = "line-compare"
    VIEW_TYPE = "1d"

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
        kwargs.update(**self.FORCED_KWARGS)

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
            self._data.update(
                x_top=x_top,
                x_bottom=x_bottom,
                y_top=y_top,
                y_bottom=y_bottom,
                obj_top=obj_top,
                obj_bottom=obj_bottom,
                labels=labels,
            )
            self.set_plot_parameters(**kwargs)
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
        self.set_plot_parameters(**kwargs)
        LOGGER.debug("Updated plot data")

    def replot(self, plot_type: str = None, repaint: bool = True):
        """Replot the current plot"""
        # get plot_type
        plot_type = self.get_plot_type(plot_type)

        # get replot data
        x_top, x_bottom, y_top, y_bottom, obj_top, obj_bottom, labels = self.get_data(self.DATA_KEYS)
        if plot_type == "line-compare":
            self.plot(x_top, x_bottom, y_top, y_bottom, obj_top, obj_bottom, labels, repaint=repaint)

    def _update(self):
        pass

    def update_style(self, name: str, gid: int = None, **kwargs):
        """Update plot style"""
        t_start = time.time()
        if name.startswith("legend"):
            kwargs = CONFIG.get_mpl_parameters(["legend"])
            self.figure.plot_update_legend(**kwargs)
        elif name.startswith("axes"):
            kwargs = CONFIG.get_mpl_parameters(["axes"])
            if name.endswith(".frame"):
                self.figure.plot_update_frame(**kwargs)
            elif name.endswith(".labels"):
                self.figure.plot_update_labels(**kwargs)
        else:
            self.figure.plot_1d_update_style_by_label(gid, **kwargs)
        self.figure.repaint()
        LOGGER.debug(f"Updated plot styles - {name} in {report_time(t_start)}")


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
        sizer = wx.BoxSizer()
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
