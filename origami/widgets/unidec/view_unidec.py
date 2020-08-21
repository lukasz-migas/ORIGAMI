"""Set of views for UniDec panel"""
# Standard library imports
import time
import logging

# Local imports
from origami.config.config import CONFIG
from origami.utils.utilities import report_time
from origami.gui_elements.views.view_mixins import ViewAxesMixin
from origami.gui_elements.views.view_mixins import ViewWaterfallMixin
from origami.gui_elements.views.view_heatmap import ViewHeatmap
from origami.gui_elements.views.view_spectrum import ViewSpectrum
from origami.gui_elements.views.view_spectrum import ViewMassSpectrum

LOGGER = logging.getLogger(__name__)


class ViewFitMassSpectrum(ViewMassSpectrum):
    """Specialized viewer for UniDec MS"""

    # TODO: ensure legend is always shown
    # TODO: ensure y-axis intensity is always updated to reflect the range shown by the original + fit
    FORCED_KWARGS = {"legend": True}

    def __init__(self, parent, figsize, title="MassSpectrumFit", **kwargs):
        ViewMassSpectrum.__init__(self, parent, figsize, title, **kwargs)
        self._x_label = kwargs.pop("x_label", "m/z (Da)")
        self._y_label = kwargs.pop("y_label", "Intensity")


class ViewMolecularWeight(ViewSpectrum):
    """Specialized viewer for mass spectral data"""

    # TODO: ensure legend is always shown
    # TODO: ensure masses always shown in descending order
    # TODO: ensure the x-axis is correctly labeled as kda when divided by 1k or Da when not (modify `x_label` attribute)
    FORCED_KWARGS = {"legend": True}

    def __init__(self, parent, figsize, title="MolecularWeight", **kwargs):
        ViewSpectrum.__init__(self, parent, figsize, title, **kwargs)
        self._x_label = kwargs.pop("x_label", "Mass (kDa)")
        self._y_label = kwargs.pop("y_label", "Intensity")


class ViewChargeDistribution(ViewSpectrum):
    """Specialized viewer for mass spectral data"""

    def __init__(self, parent, figsize, title="ChargeDistribution", **kwargs):
        ViewSpectrum.__init__(self, parent, figsize, title, **kwargs)
        self._x_label = kwargs.pop("x_label", "Charge")
        self._y_label = kwargs.pop("y_label", "Intensity")


class ViewBarChart(ViewSpectrum):
    """Barchart viewer"""

    VIEW_TYPE = "bar"
    DATA_KEYS = ("x", "y", "labels", "colors", "obj")
    MPL_KEYS = ["bar", "axes", "legend"]
    UPDATE_STYLES = ("bar",)
    ALLOWED_PLOTS = ("bar",)
    DEFAULT_PLOT = "bar"

    def __init__(self, parent, figsize, title="Barchart", **kwargs):
        ViewSpectrum.__init__(self, parent, figsize, title, **kwargs)
        self._x_label = kwargs.pop("x_label", "Species")
        self._y_label = kwargs.pop("y_label", "Intensity")

    # noinspection PyMethodOverriding
    @staticmethod
    def check_input(x, y, labels, colors, obj):
        """Ensure that input is correct"""
        if x is None and y is None and obj is None:
            raise ValueError("You must provide the x/y values or container object")
        if x is None and y is None and obj is not None:
            x = obj.x
            y = obj.y
            labels = obj.labels
            colors = obj.colors
        return x, y, labels, colors

    def plot(self, x=None, y=None, labels=None, colors=None, obj=None, repaint: bool = True, **kwargs):
        """Simple line plot"""
        # try to update plot first, as it can be quicker
        t_start = time.time()
        #         self.set_document(obj, **kwargs)
        #         self.set_labels(obj, **kwargs)

        kwargs.update(**CONFIG.get_mpl_parameters(self.MPL_KEYS))
        kwargs = self.check_kwargs(**kwargs)

        x, y, labels, colors = self.check_input(x, y, labels, colors, obj)
        self.figure.clear()
        self.figure.plot_1d_barplot(
            x, y, labels, colors, x_label=self.x_label, y_label=self.y_label, callbacks=self._callbacks, **kwargs
        )
        self.figure.repaint(repaint)

        # set data
        self._data.update(x=x, y=y, obj=obj)
        self.set_plot_parameters(**kwargs)
        LOGGER.debug(f"Plotted data in {report_time(t_start)}")


class ViewIndividualPeaks(ViewSpectrum, ViewWaterfallMixin, ViewAxesMixin):
    """Specialized viewer for mass spectral data"""

    # TODO: add legend for markers

    ALLOWED_PLOTS = ("waterfall", "line")
    DATA_KEYS = ("array", "x", "y", "obj")

    def __init__(self, parent, figsize, title="IndividualPlots", **kwargs):
        ViewSpectrum.__init__(self, parent, figsize, title, **kwargs)
        self._x_label = kwargs.pop("x_label", "m/z")
        self._y_label = kwargs.pop("y_label", "Offset intensity")

    # noinspection PyMethodOverriding
    @staticmethod
    def check_input(x, y, array, obj):
        """Check user-input"""
        if x is None and y is None and array is None and obj is None:
            raise ValueError("You must provide the x/y/array values or container object")
        if x is None and y is None and array is None and obj is not None:
            x = obj.x
            y = obj.y
            array = obj.array
        return x, y, array

    def _set_forced_kwargs(self):
        """Dynamically update force plot keyword arguments"""
        # update forced kwargs
        self.FORCED_KWARGS.update(
            {
                "waterfall_increment": CONFIG.unidec_panel_plot_individual_line_sep,
                "waterfall_reverse": False,
                "waterfall_normalize": True,
            }
        )

    def plot_waterfall(self, x=None, y=None, array=None, obj=None, repaint: bool = True, **kwargs):
        """Simple plot"""
        self._set_forced_kwargs()
        super(ViewIndividualPeaks, self).plot_waterfall(x, y, array, obj, False, **kwargs)
        self.figure.plot_waterfall_fix_y_axis()
        self.repaint(repaint)

    def replot(self, plot_type: str = None, repaint: bool = True, light_clear: bool = False):
        """Replot the current plot"""
        # get plot_type
        plot_type = self.get_plot_type(plot_type)

        if light_clear:
            self.light_clear()

        # get replot data
        array, x, y, obj = self.get_data(self.DATA_KEYS)
        if plot_type == "waterfall":
            self.plot_waterfall(x, y, array, obj, repaint=repaint)

    def update_style(self, name: str):
        """Update plot style"""
        t_start = time.time()

        kwargs = dict()
        if name.startswith("waterfall"):
            kwargs = self._update_style_waterfall(name)
        elif name.startswith("axes"):
            kwargs = self._update_style_axes(name)
        self.figure.repaint()
        self.set_plot_parameters(**kwargs)
        LOGGER.debug(f"Updated plot styles - {name} in {report_time(t_start)}")


class ViewMassSpectrumGrid(ViewHeatmap):
    """Viewer class for extracted ions"""

    # TODO: fix the issue where the bottom and top have white stripe - need to change the x-axis zoom

    def __init__(self, parent, figsize, title="MSGrid", **kwargs):
        ViewHeatmap.__init__(self, parent, figsize, title, **kwargs)
        self._x_label = kwargs.pop("x_label", "m/z (Da)")
        self._y_label = kwargs.pop("y_label", "Charge)")

    def plot(self, x=None, y=None, array=None, obj=None, repaint: bool = True, **kwargs):
        """Simple plot"""
        speedy = CONFIG.unidec_panel_plot_speed_heatmap
        super(ViewMassSpectrumGrid, self).plot(x, y, array, obj, repaint, speedy=speedy, **kwargs)


class ViewMolecularWeightGrid(ViewHeatmap):
    """Viewer class for extracted ions"""

    # TODO: fix the issue where the bottom and top have white stripe - need to change the x-axis zoom

    def __init__(self, parent, figsize, title="MSGrid", **kwargs):
        ViewHeatmap.__init__(self, parent, figsize, title, **kwargs)
        self._x_label = kwargs.pop("x_label", "Mass (kDa)")
        self._y_label = kwargs.pop("y_label", "Charge)")

    def plot(self, x=None, y=None, array=None, obj=None, repaint: bool = True, **kwargs):
        """Simple plot"""
        super(ViewMolecularWeightGrid, self).plot(x, y, array, obj, repaint, speedy=True, **kwargs)
