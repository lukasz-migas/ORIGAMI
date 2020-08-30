"""Overlay plot that is a composite of other plots"""
# Local imports
from origami.visuals.mpl.plot_spectrum import PlotSpectrum
from origami.visuals.mpl.plot_heatmap_2d import PlotHeatmap2D


class PlotOverlay(PlotSpectrum, PlotHeatmap2D):
    """Plot overlay"""

    def __init__(self, *args, **kwargs):
        PlotSpectrum.__init__(self, *args, **kwargs)
        PlotHeatmap2D.__init__(self, *args, **kwargs)
