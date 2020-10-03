"""Bokeh utilities"""
# Third-party imports
import numpy as np
import matplotlib.cm as cm
import matplotlib.colors as colors
from bokeh.models import ColorBar
from bokeh.models import FixedTicker
from bokeh.models import AdaptiveTicker
from bokeh.models import FuncTickFormatter
from bokeh.models import BasicTickFormatter
from bokeh.models.mappers import LinearColorMapper

# Local imports
from origami.utils.color import convert_rgb_1_to_255
from origami.visuals.bokeh.parser import get_param
from origami.visuals.bokeh.parser import parse_font_size
from origami.visuals.bokeh.parser import parse_font_weight


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


def _add_colorbar(figure, array, color_mapper, modify_ticks=False, as_percentage=False, **kwargs):
    """
    Add colorbar to bokeh plot

    Parameters
    ----------
    figure : bokeh object
        bokeh plot object
    array : np.ndarray
        data array
    color_mapper : bokeh colorMapper object
    modify_ticks : bool
        decide whether ticks should be modified
    as_percentage : bool
        decide whether ticks should be 'values' or 'percentages'
    """
    orientation = get_param("bokeh_colorbar_orientation", **kwargs)
    if modify_ticks:
        if as_percentage:
            z_min, z_max = np.round(np.min(array), 10), np.round(np.max(array), 10)
            z_mid = np.round(np.max(array) / 2.0, 10)
            ticker = FixedTicker(ticks=[z_min, z_mid, z_max])
            formatter = FuncTickFormatter(
                code="""
            data = {zmin: '0', zmid: '%', zmax: '100'}
            return data[tick]
            """.replace(
                    "zmin", str(z_min)
                )
                .replace("zmid", str(z_mid))
                .replace("zmax", str(z_max))
            )
        else:
            ticker = FixedTicker(ticks=[-1.0, 0.0, 1.0])
            formatter = BasicTickFormatter(
                precision=get_param("bokeh_colorbar_precision", **kwargs),
                use_scientific=get_param("bokeh_colorbar_use_scientific", **kwargs),
            )
    else:
        ticker = AdaptiveTicker()
        formatter = BasicTickFormatter(
            precision=get_param("bokeh_colorbar_precision", **kwargs),
            use_scientific=get_param("bokeh_colorbar_use_scientific", **kwargs),
        )

    location, label_align = "right", "left"
    if orientation == "horizontal":
        location, label_align = "below", "center"

    colorbar = ColorBar(
        color_mapper=color_mapper,
        ticker=ticker,
        formatter=formatter,
        label_standoff=get_param("bokeh_colorbar_label_offset", **kwargs),
        location=(get_param("bokeh_colorbar_offset_x", **kwargs), get_param("bokeh_colorbar_offset_y", **kwargs)),
        orientation=orientation,
        width=get_param("bokeh_colorbar_width", **kwargs) if orientation == "vertical" else "auto",
        height=get_param("bokeh_colorbar_width", **kwargs) if orientation == "horizontal" else "auto",
        padding=get_param("bokeh_colorbar_padding", **kwargs),
        bar_line_width=get_param("bokeh_colorbar_edge_width", **kwargs),
        bar_line_color=convert_rgb_1_to_255(
            get_param("bokeh_colorbar_edge_color", **kwargs), as_integer=True, as_tuple=True
        ),
        bar_line_cap="square",
        major_tick_line_color=convert_rgb_1_to_255(
            get_param("bokeh_colorbar_edge_color", **kwargs), as_integer=True, as_tuple=True
        ),
        major_tick_line_width=get_param("bokeh_colorbar_edge_width", **kwargs),
        minor_tick_line_color=convert_rgb_1_to_255(
            get_param("bokeh_colorbar_edge_color", **kwargs), as_integer=True, as_tuple=True
        ),
        minor_tick_line_width=get_param("bokeh_colorbar_edge_width", **kwargs),
        major_label_text_align=label_align,  # get_param("bokeh_colorbar_label_offset", **kwargs),  # todo
        major_label_text_font_size=parse_font_size(get_param("bokeh_colorbar_label_font_size", **kwargs)),
        major_label_text_font_style=parse_font_weight(get_param("bokeh_colorbar_label_weight", **kwargs)),
    )
    figure.add_layout(colorbar, location)
