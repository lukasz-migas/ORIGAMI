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
    MPL_KEYS = ["axes", "legend", "unidec"]
    UPDATE_STYLES = ("bar",)
    ALLOWED_PLOTS = ("bar",)
    DEFAULT_PLOT = "bar"

    def __init__(self, parent, figsize, title="Barchart", **kwargs):
        ViewSpectrum.__init__(self, parent, figsize, title, **kwargs)
        self._x_label = kwargs.pop("x_label", "Species")
        self._y_label = kwargs.pop("y_label", "Intensity")

    # noinspection PyMethodOverriding
    @staticmethod
    def check_input(obj):
        """Ensure that input is correct"""
        return obj.x, obj.y, obj.labels, obj.colors, obj.markers

    # noinspection PyMethodOverriding
    def plot(self, obj, repaint: bool = True, forced_kwargs=None, **kwargs):
        """Simple line plot"""
        t_start = time.time()
        #         self.set_document(obj, **kwargs)
        #         self.set_labels(obj, **kwargs)

        kwargs, _kwargs = self.parse_kwargs(self.MPL_KEYS, forced_kwargs=forced_kwargs, **kwargs)
        kwargs = self.check_kwargs(**kwargs)

        x, y, labels, colors, markers = self.check_input(obj)
        self.figure.clear()
        self.figure.plot_1d_barplot(
            x, y, labels, colors, x_label=self.x_label, y_label=self.y_label, callbacks=self._callbacks, **kwargs
        )

        # add markers to the barchart
        for x, y, color, marker, label in zip(x, y, colors, markers, labels):
            self.add_scatter(
                x, y, color, marker, size=CONFIG.unidec_panel_plot_bar_markers_size, label=label, repaint=False
            )
        self.figure.repaint(repaint)

        # set data
        self._data.update(x=x, y=y, obj=obj)
        self.set_plot_parameters(**kwargs)
        LOGGER.debug(f"Plotted data in {report_time(t_start)}")

    def update_style(self, name: str):
        """Update plot style"""
        t_start = time.time()
        kwargs = dict()
        if name.startswith("barchart"):
            kwargs = CONFIG.get_mpl_parameters(["unidec"])
            self.figure.plot_1d_update_barplot(**kwargs)
        elif name.startswith("axes"):
            kwargs = self._update_style_axes(name)
        self.figure.repaint()
        self.set_plot_parameters(**kwargs)
        LOGGER.debug(f"Updated plot styles - {name} in {report_time(t_start)}")


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

    def plot_waterfall(self, x=None, y=None, array=None, obj=None, repaint: bool = True, **kwargs):
        """Simple plot"""
        forced_kwargs = {
            "waterfall_increment": CONFIG.unidec_panel_plot_individual_line_sep,
            "waterfall_reverse": False,
            "waterfall_normalize": True,
        }
        super(ViewIndividualPeaks, self).plot_waterfall(x, y, array, obj, False, forced_kwargs=forced_kwargs, **kwargs)
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


class ViewUnidecHeatmap(ViewHeatmap):
    """Viewer class for UniDec heatmaps"""

    MPL_KEYS = ["2d", "colorbar", "normalization", "axes", "unidec"]

    def plot(self, x=None, y=None, array=None, obj=None, repaint: bool = True, **kwargs):
        """Simple plot"""
        forced_kwargs = {
            "speedy": CONFIG.unidec_panel_plot_speed_heatmap,
            "heatmap_colormap": CONFIG.unidec_panel_plot_heatmap_colormap,
            "heatmap_n_contour": CONFIG.unidec_panel_plot_contour_levels,
        }
        super(ViewUnidecHeatmap, self).plot(x, y, array, obj, repaint, forced_kwargs=forced_kwargs, **kwargs)

    def update_style(self, name: str):
        """Update plot style"""
        t_start = time.time()
        # heatmap-specific updates
        kwargs = dict()
        if name.startswith("heatmap"):
            if not self.is_plotted_or_plot("heatmap", self.plot, self.DATA_KEYS):
                return
            if name.endswith("normalization"):
                kwargs = CONFIG.get_mpl_parameters(["normalization"])
                self.figure.plot_2d_update_normalization(array=self._data["array"], **kwargs)
            elif name.endswith("colorbar"):
                kwargs = CONFIG.get_mpl_parameters(["colorbar"])
                self.figure.plot_2d_update_colorbar(**kwargs)
            else:
                self.figure.plot_2d_update_heatmap_style(
                    colormap=CONFIG.unidec_panel_plot_heatmap_colormap,
                    interpolation=CONFIG.heatmap_interpolation,
                    array=self._data["array"],
                    cbar_kwargs=CONFIG.get_mpl_parameters("colorbar"),
                )
        elif name.startswith("axes"):
            kwargs = self._update_style_axes(name)
        self.figure.repaint()
        self.set_plot_parameters(**kwargs)
        LOGGER.debug(f"Updated plot styles - {name} in {report_time(t_start)}")


class ViewMassSpectrumGrid(ViewUnidecHeatmap):
    """Viewer class for extracted ions"""

    # TODO: fix the issue where the bottom and top have white stripe - need to change the x-axis zoom

    def __init__(self, parent, figsize, title="MSGrid", **kwargs):
        ViewUnidecHeatmap.__init__(self, parent, figsize, title, **kwargs)
        self._x_label = kwargs.pop("x_label", "m/z (Da)")
        self._y_label = kwargs.pop("y_label", "Charge)")


class ViewMolecularWeightGrid(ViewUnidecHeatmap):
    """Viewer class for extracted ions"""

    # TODO: fix the issue where the bottom and top have white stripe - need to change the x-axis zoom

    def __init__(self, parent, figsize, title="MSGrid", **kwargs):
        ViewUnidecHeatmap.__init__(self, parent, figsize, title, **kwargs)
        self._x_label = kwargs.pop("x_label", "Mass (kDa)")
        self._y_label = kwargs.pop("y_label", "Charge)")
