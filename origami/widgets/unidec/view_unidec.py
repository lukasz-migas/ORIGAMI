"""Set of views for UniDec panel"""
# Local imports
from origami.gui_elements.views.view_heatmap import ViewHeatmap
from origami.gui_elements.views.view_spectrum import ViewSpectrum


class ViewMolecularWeight(ViewSpectrum):
    """Specialized viewer for mass spectral data"""

    def __init__(self, parent, figsize, title="MolecularWeight", **kwargs):
        ViewSpectrum.__init__(self, parent, figsize, title, **kwargs)
        self._x_label = kwargs.pop("x_label", "Mass(kDa)")
        self._y_label = kwargs.pop("y_label", "Intensity")


class ViewChargeDistribution(ViewSpectrum):
    """Specialized viewer for mass spectral data"""

    def __init__(self, parent, figsize, title="ChargeDistribution", **kwargs):
        ViewSpectrum.__init__(self, parent, figsize, title, **kwargs)
        self._x_label = kwargs.pop("x_label", "Charge")
        self._y_label = kwargs.pop("y_label", "Intensity")


class ViewBarchart(ViewSpectrum):
    """Specialized viewer for mass spectral data"""

    def __init__(self, parent, figsize, title="Barchart", **kwargs):
        ViewSpectrum.__init__(self, parent, figsize, title, **kwargs)
        self._x_label = kwargs.pop("x_label", "Species")
        self._y_label = kwargs.pop("y_label", "Intensity")


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


class ViewMolecularWeightGrid(ViewHeatmap):
    """Viewer class for extracted ions"""

    def __init__(self, parent, figsize, title="MSGrid", **kwargs):
        ViewHeatmap.__init__(self, parent, figsize, title, **kwargs)
        self._x_label = kwargs.pop("x_label", "Mass (kDa)")
        self._y_label = kwargs.pop("y_label", "Charge)")
