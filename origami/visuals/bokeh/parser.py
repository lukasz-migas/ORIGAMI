"""Parameter parser"""
# Standard library imports
from typing import Any

# Local imports
from origami.config.config import CONFIG

MATCHES = {
    # legend
    "bokeh_legend_click_policy": "click_policy",
    "bokeh_legend_location": "location",
    "bokeh_legend_mute_alpha": "muted_alpha",
    "bokeh_legend_background_alpha": "fill_alpha",
    "bokeh_legend_orientation": "orientation",
    "bokeh_legend_font_size": "label_text_font_size",
    # colorbar
    "bokeh_colorbar_precision": "precision",
    "bokeh_colorbar_label_offset": "label_standoff",
    "bokeh_colorbar_use_scientific": "use_scientific",
    "bokeh_colorbar_location": "location",
    "bokeh_colorbar_orientation": "orientation",
    "bokeh_colorbar_offset_x": "bokeh_colorbar_offset_x",
    "bokeh_colorbar_offset_y": "bokeh_colorbar_offset_y",
    "bokeh_colorbar_width": "width",
    "bokeh_colorbar_padding": "padding",
    "bokeh_colorbar_edge_color": "bar_line_color",
    "bokeh_colorbar_edge_width": "bar_line_width",
    "bokeh_colorbar_modify_ticks": "modify_ticks",
    "bokeh_colorbar_label_font_size": "major_label_text_font_size",
    "bokeh_colorbar_label_weight": "major_label_text_font_style",
    "bokeh_colorbar_title_font_size": "title_text_font_size",
    "bokeh_colorbar_title_weight": "title_text_font_style",
    # frame
    "bokeh_frame_outline_width": "outline_line_width",
    "bokeh_frame_outline_alpha": "outline_line_alpha",
    "bokeh_frame_border_min_left": "min_border_left",
    "bokeh_frame_border_min_right": "min_border_right",
    "bokeh_frame_border_min_top": "min_border_top",
    "bokeh_frame_border_min_bottom": "min_border_bottom",
    "bokeh_frame_background_color": "background_fill_color",
    "bokeh_frame_grid_line": "bokeh_frame_grid_line",
    "bokeh_frame_grid_line_color": "bokeh_frame_grid_line_color",
    "bokeh_frame_title_font_size": "text_font_size",
    "bokeh_frame_title_font_weight": "text_font_style",
    "bokeh_frame_label_font_size": "axis_label_text_font_size",
    "bokeh_frame_label_font_weight": "axis_label_text_font_style",
    "bokeh_frame_tick_font_size": "major_label_text_font_size",
    # "bokeh_frame_tick_use_scientific": self.bokeh_frame_tick_use_scientific,
    # "bokeh_frame_tick_precision": self.bokeh_frame_tick_precision,
    # scatter
    "bokeh_scatter_size": "size",
    "bokeh_scatter_marker": "marker",
    "bokeh_scatter_edge_same_as_fill": "bokeh_scatter_edge_same_as_fill",
    "bokeh_scatter_alpha": "fill_alpha",
    "bokeh_scatter_edge_color": "line_color",
    "bokeh_scatter_edge_width": "line_width",
    # bar
    "bokeh_bar_width": "width",
    "bokeh_bar_alpha": "fill_alpha",
    "bokeh_bar_edge_color": "line_color",
    "bokeh_bar_edge_same_as_fill": "bokeh_bar_edge_same_as_fill",
    "bokeh_bar_edge_width": "line_width",
    # line
    "bokeh_line_style": "line_dash",
    "bokeh_line_width": "line_width",
    "bokeh_line_alpha": "line_alpha",
    "bokeh_line_fill_under": "bokeh_line_fill_under",
    "bokeh_line_fill_alpha": "fill_alpha",
    "bokeh_line_color": "fill_color",
}


def get_param(origami_key: str, **kwargs) -> Any:
    """Retrieve bokeh keyword parameter"""
    # get proper bokeh key from the matches dictionary
    key = MATCHES.get(origami_key, None)
    # return proper bokeh key if in the dictionary
    if key in kwargs:
        return kwargs[key]
    # return origami key if in the dictionary
    if origami_key in kwargs:
        return kwargs[origami_key]
    # return origami default
    return getattr(CONFIG, origami_key)


def parse_font_size(value):
    """Parse font size so it matches Bokeh spec"""
    if isinstance(value, (int, float)):
        return "%spt" % value
    elif isinstance(value, str):
        if "pt" not in value:
            return "%spt" % value
    return value


def parse_font_weight(value):
    """Parse font weight so it matches Bokeh spec"""
    if value:
        return "bold"
    return "normal"
