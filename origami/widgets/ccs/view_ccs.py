"""CCS views"""
# Standard library imports
import time
import logging

# Local imports
from origami.config.config import CONFIG
from origami.utils.utilities import report_time
from origami.gui_elements.views.view_spectrum import ViewSpectrum
from origami.gui_elements.views.view_spectrum import ViewMobilogram

LOGGER = logging.getLogger(__name__)


class ViewCCSFit(ViewSpectrum):
    """Specialized viewer for CCS Fit"""

    # TODO: this should be plotted as scatter plot with linear fit to indicate the slope + added R2

    FORCED_KWARGS = {
        "spectrum_line_fill_under": False,
        "y_lower_start": None,
        "y_upper_multiplier": 1,
        "x_pad": 1,
        "y_pad": 1,
        "axes_tick_font_size": 12,
        "axes_label_pad": 2,
        "axes_label_font_size": 14,
    }

    def __init__(self, parent, figsize, title="CCSFit", **kwargs):
        ViewSpectrum.__init__(self, parent, figsize, title, **kwargs)
        self._x_label = kwargs.pop("x_label", "x-axis")
        self._y_label = kwargs.pop("y_label", "y-axis")

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
            self.figure.plot_1d_scatter(
                x, y, x_label=self.x_label, y_label=self.y_label, callbacks=self._callbacks, **kwargs
            )
            self.figure.repaint(repaint)

            # set data
            self._data.update(x=x, y=y, obj=obj)
            self.set_plot_parameters(**kwargs)
            LOGGER.debug(f"Plotted data in {report_time(t_start)}")

    def update(self, x=None, y=None, obj=None, repaint: bool = True, **kwargs):
        """Update plot without having to clear it"""
        raise AttributeError


#         t_start = time.time()
#         self.set_document(obj, **kwargs)
#         self.set_labels(obj, **kwargs)
#
#         # update plot
#         x, y = self.check_input(x, y, obj)
#         self.figure.plot_1d_update_data(x, y, self.x_label, self.y_label, **kwargs)
#         self.figure.on_check_zoom_state(x, y)
#         self.figure.repaint(repaint)
#
#         # set data
#         self._data.update(x=x, y=y, obj=obj)
#         self.set_plot_parameters(**kwargs)
#         LOGGER.debug(f"Plotted data in {report_time(t_start)}")


class ViewCCSMobilogram(ViewMobilogram):
    """Specialized viewer for mobilogram in CCS panel"""

    def __init__(self, parent, figsize, title="CCSMobilogram", **kwargs):
        super(ViewCCSMobilogram, self).__init__(parent, figsize, title, **kwargs)

    def plot(self, x=None, y=None, obj=None, repaint: bool = True, **kwargs):
        """Slightly modified plot to always resize y-axis"""
        super(ViewCCSMobilogram, self).plot(x, y, obj, repaint=False, **kwargs)
        self.reset_zoom()
        self.repaint()
