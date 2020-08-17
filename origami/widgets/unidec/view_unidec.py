"""Set of views for UniDec panel"""
# Standard library imports
import time
import logging
from copy import copy

# Local imports
from origami.config.config import CONFIG
from origami.utils.utilities import report_time
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
        ViewSpectrum.__init__(self, parent, figsize, title, **kwargs)
        self._x_label = kwargs.pop("x_label", "m/z (Da)")
        self._y_label = kwargs.pop("y_label", "Intensity")


class ViewMolecularWeight(ViewSpectrum):
    """Specialized viewer for mass spectral data"""

    # TODO: ensure legend is always shown
    # TODO: ensure masses always shown in descending order
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


class ViewIndividualPeaks(ViewSpectrum):
    """Specialized viewer for mass spectral data"""

    # TODO add legend

    ALLOWED_PLOTS = ("waterfall", "line")
    DATA_KEYS = ("array", "x", "y", "obj")

    def __init__(self, parent, figsize, title="Barchart", **kwargs):
        ViewSpectrum.__init__(self, parent, figsize, title, **kwargs)
        self._x_label = kwargs.pop("x_label", "m/z")
        self._y_label = kwargs.pop("y_label", "Offset intensity")

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

    def plot_waterfall(self, x=None, y=None, array=None, obj=None, repaint: bool = True, **kwargs):
        """Plot object as a waterfall"""
        self.can_plot("waterfall")
        t_start = time.time()
        # try to update plot first, as it can be quicker
        mpl_keys = copy(self.MPL_KEYS)
        mpl_keys.append("waterfall")

        self.set_document(obj, **kwargs)
        self.set_labels(obj, **kwargs)

        kwargs.update(**CONFIG.get_mpl_parameters(mpl_keys))
        kwargs.update(**self.FORCED_KWARGS)
        kwargs = self.check_kwargs(**kwargs)
        x, y, array = self.check_input(x, y, array, obj)
        self.figure.clear()
        self.figure.plot_waterfall(
            x, y, array, x_label=self.x_label, y_label=self.y_label, callbacks=self._callbacks, obj=obj, **kwargs
        )
        if repaint:
            self.figure.repaint()

        # set data
        self._data.update(x=x, y=y, array=array, obj=obj)
        self.set_plot_parameters(**kwargs)
        LOGGER.debug(f"Plotted data in {report_time(t_start)}")

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

        # heatmap-specific updates
        kwargs = dict()
        if name.startswith("waterfall"):
            if not self.is_plotted_or_plot("waterfall", self.plot_waterfall, self.DATA_KEYS):
                return

            # update data - requires full redraw
            if name.endswith(".data"):
                self.replot("waterfall", False)
            else:
                kwargs = CONFIG.get_mpl_parameters(["waterfall"])
                x, y, array = self.get_data(["x", "y", "array"])
                self.figure.plot_waterfall_update(x, y, array, name, **kwargs)
        elif name.startswith("axes"):
            kwargs = CONFIG.get_mpl_parameters(["axes"])
            if name.endswith(".frame"):
                self.figure.plot_update_frame(**kwargs)
            elif name.endswith(".labels"):
                self.figure.plot_update_labels(**kwargs)
        self.figure.repaint()
        self.set_plot_parameters(**kwargs)
        LOGGER.debug(f"Updated plot styles - {name} in {report_time(t_start)}")


class ViewMassSpectrumGrid(ViewHeatmap):
    """Viewer class for extracted ions"""

    def __init__(self, parent, figsize, title="MSGrid", **kwargs):
        ViewHeatmap.__init__(self, parent, figsize, title, **kwargs)
        self._x_label = kwargs.pop("x_label", "m/z (Da)")
        self._y_label = kwargs.pop("y_label", "Charge)")

    def plot(self, x=None, y=None, array=None, obj=None, repaint: bool = True, **kwargs):
        """Simple plot"""
        super(ViewMassSpectrumGrid, self).plot(x, y, array, obj, repaint, speedy=True, **kwargs)


class ViewMolecularWeightGrid(ViewHeatmap):
    """Viewer class for extracted ions"""

    def __init__(self, parent, figsize, title="MSGrid", **kwargs):
        ViewHeatmap.__init__(self, parent, figsize, title, **kwargs)
        self._x_label = kwargs.pop("x_label", "Mass (kDa)")
        self._y_label = kwargs.pop("y_label", "Charge)")

    def plot(self, x=None, y=None, array=None, obj=None, repaint: bool = True, **kwargs):
        """Simple plot"""
        super(ViewMolecularWeightGrid, self).plot(x, y, array, obj, repaint, speedy=True, **kwargs)
