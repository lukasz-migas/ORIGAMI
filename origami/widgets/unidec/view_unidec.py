"""Set of views for UniDec panel"""
# Standard library imports
import time
import logging

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

    def __init__(self, parent, figsize, title="Barchart", **kwargs):
        ViewSpectrum.__init__(self, parent, figsize, title, **kwargs)
        self._x_label = kwargs.pop("x_label", "Charge")
        self._y_label = kwargs.pop("y_label", "Intensity")


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
