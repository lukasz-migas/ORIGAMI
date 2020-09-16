"""Bokeh utilities"""
# Third-party imports
import numpy as np
import matplotlib.cm as cm
import matplotlib.colors as colors
from bokeh.models.mappers import LinearColorMapper


def convert_colormap_to_mapper(zvals, colormap="viridis", palette=None, vmin=None, vmax=None):
    """Convert matplotlib colormap to Bokeh colormapper

    Parameters
    ----------
    zvals : np.ndarray
        array
    colormap : str
        name of the colormap
    palette :
    vmin : float
        starting intensity for the colormap
    vmax : float
        final intensity for the colormap

    Returns
    -------
    _palette : Palette
        Bokeh palette
    _color_mapper : LinearColorMapper
        Bokeh colormapper
    """
    zvals = np.nan_to_num(zvals)
    if vmin is None:
        vmin = np.round(np.min(zvals), 2)
    if vmax is None:
        vmax = np.round(np.max(zvals), 2)

    if palette is None:
        _colormap = cm.get_cmap(colormap)
        _palette = [colors.rgb2hex(m) for m in _colormap(np.arange(_colormap.N))]
    else:
        _palette = palette

    _color_mapper = LinearColorMapper(palette=_palette, low=vmin, high=vmax)

    return _palette, _color_mapper


def check_source(source, keys):
    """Helper function to check source has all of the required fields"""
    missing = []
    if isinstance(source, dict):
        for key in keys:
            if key not in source:
                missing.append(key)
    else:
        for key in keys:
            if key not in source.data:
                missing.append(key)

    if missing:
        missing = ", ".join(missing)
        raise ValueError(f"Missing '{missing}' from the ColumnDataSource")
    return source
