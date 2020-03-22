# Local imports
from origami.visuals.mpl.plot_spectrum import PlotSpectrum
from origami.visuals.mpl.plot_heatmap_2d import PlotHeatmap2D


class PlotMixed(PlotSpectrum, PlotHeatmap2D):
    """Misc plot base that allows both 1D and 2D plots"""
