"""Parameter parser"""
# Standard library imports
from typing import Any
from typing import Dict
from typing import List
from typing import Union

# Third-party imports
from bokeh.models import Plot
from bokeh.models import BoxZoomTool

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
    # heatmap
    "bokeh_heatmap_colormap": "colormap",
    # grid
    "bokeh_grid_label_add": "bokeh_grid_label_add",
    "bokeh_grid_label_font_size": "bokeh_grid_label_font_size",
    "bokeh_grid_label_font_weight": "bokeh_grid_label_font_weight",
    "bokeh_grid_label_font_color": "bokeh_grid_label_font_color",
    "bokeh_grid_label_x_pos": "bokeh_grid_label_x_pos",
    "bokeh_grid_label_y_pos": "bokeh_grid_label_y_pos",
    # waterfall
    "bokeh_waterfall_increment": "bokeh_waterfall_increment",
    "bokeh_waterfall_fill_under": "bokeh_waterfall_fill_under",
    "bokeh_waterfall_fill_alpha": "bokeh_waterfall_fill_alpha",
    # waterfall
    "bokeh_annotation_font_size": "bokeh_annotation_font_size",
    "bokeh_annotation_font_weight": "bokeh_annotation_font_weight",
    "bokeh_annotation_font_color": "bokeh_annotation_font_color",
    "bokeh_annotation_font_background_color": "bokeh_annotation_font_background_color",
    "bokeh_annotation_font_transparency": "bokeh_annotation_font_transparency",
}
DEFAULT_BOKEH_TOOLS = [
    "save",
    "reset",
    "hover",
    "crosshair",
    "pan",
    "xpan",
    "ypan",
    "box_zoom",
    "wheel_zoom",
    "xwheel_zoom",
    "ywheel_zoom",
]
EXTRA_BOKEH_TOOLS = ["xbox_zoom", "ybox_zoom"]
TOOLS = {
    "bokeh_tools_save": "save",
    "bokeh_tools_reset": "reset",
    "bokeh_tools_hover": "hover",
    "bokeh_tools_crosshair": "crosshair",
    "bokeh_tools_pan_xy": "pan",
    "bokeh_tools_pan_x": "xpan",
    "bokeh_tools_pan_y": "ypan",
    "bokeh_tools_boxzoom_xy": "box_zoom",
    # "bokeh_tools_active_drag": "active_drag",
    # "bokeh_tools_active_wheel": "active_wheel",
    # "bokeh_tools_active_inspect": "active_inspect",
}
TOOLS_STANDARD = [
    "bokeh_tools_save",
    "bokeh_tools_reset",
    "bokeh_tools_crosshair",
    "bokeh_tools_pan_xy",
    "bokeh_tools_pan_x",
    "bokeh_tools_pan_y",
    "bokeh_tools_boxzoom_xy",
]
TOOLS_BOXZOOM = ["bokeh_tools_boxzoom_x", "bokeh_tools_boxzoom_y"]
WHEEL_TOOLS = {"Wheel zoom (xy)": "wheel_zoom", "Wheel zoom (x)": "xwheel_zoom", "Wheel zoom (y)": "ywheel_zoom"}
HOVER_TOOLS = {
    "bokeh_tools_boxzoom_x": "xbox_zoom",
    "bokeh_tools_boxzoom_y": "ybox_zoom",
    "xbox_zoom": "xbox_zoom",
    "ybox_zoom": "ybox_zoom",
}
ACTIVE_DRAG_TOOLS = {
    "Box zoom (xy)": "box_zoom",
    "Box zoom (x)": "xbox_zoom",
    "Box zoom (y)": "ybox_zoom",
    "Pan (xy)": "pan",
    "Pan (x)": "xpan",
    "Pan (y)": "ypan",
    "auto": "auto",
    "None": None,
}
ACTIVE_WHEEL_TOOLS = {
    "Wheel zoom (xy)": "wheel_zoom",
    "Wheel zoom (x)": "xwheel_zoom",
    "Wheel zoom (y)": "ywheel_zoom",
    "auto": "auto",
    "None": None,
}
ACTIVE_INSPECT_TOOLS = {"Hover": "hover", "Crosshair": "crosshair", "auto": "auto", "None": None}


def parse_active_drag(key: str, tools: List[Union[str, BoxZoomTool]]):
    """Add active drag"""
    if key in ACTIVE_DRAG_TOOLS:
        tool = ACTIVE_DRAG_TOOLS[key]
        if tool in DEFAULT_BOKEH_TOOLS:
            if tool not in tools:
                tools.append(tool)
            return tool
        elif tool in EXTRA_BOKEH_TOOLS:
            if tool == "xbox_zoom":
                tool = BoxZoomTool(dimensions="width")
            else:
                tool = BoxZoomTool(dimensions="height")
            tools.append(tool)
            return tool
    elif key in HOVER_TOOLS:
        tool = parse_boxzoom(key)
        if tool not in tools:
            tools.append(tool)
        return tool


def parse_active_wheel(key: str, tools: List[Union[str, BoxZoomTool]]):
    """Add active wheel"""
    if key in ACTIVE_WHEEL_TOOLS:
        tool = ACTIVE_WHEEL_TOOLS[key]
        if tool not in tools:
            tools.append(tool)
        return tool


def parse_active_inspect(key: str, tools: List[Union[str, BoxZoomTool]]):
    """Add active inspect"""
    if key in ACTIVE_INSPECT_TOOLS:
        tool = ACTIVE_INSPECT_TOOLS[key]
        if tool not in tools:
            tools.append(tool)
        return tool


def parse_boxzoom(key: str):
    """Parse boxzoom tools"""
    tool = HOVER_TOOLS.get(key, None)
    if tool == "xbox_zoom":
        return BoxZoomTool(dimensions="width")
    elif tool == "ybox_zoom":
        return BoxZoomTool(dimensions="height")


def add_boxzoom(key: str, tools: List[Union[str, BoxZoomTool]]):
    """Add tools"""
    tool = parse_boxzoom(key)
    if tool:
        tools.append(tool)


def clean_tools(tools):
    """Remove all disallowed tools"""
    _tools = []
    for tool in tools:
        if tool not in [None, "None", "", "auto"]:
            _tools.append(tool)
    return _tools


def parse_tools(plot_base, plot: Plot, **kwargs: Dict):
    """Parse tools"""

    def _add_tool(key):
        """Add basic tool"""
        if key in kwargs and kwargs[key]:
            tools.append(TOOLS[key])

    tools: List[Union[str, BoxZoomTool]] = []
    for tool in TOOLS_STANDARD:
        _add_tool(tool)

    # append boxzoom tools
    for tool in TOOLS_BOXZOOM:
        add_boxzoom(tool, tools)

    # append wheel tools
    if kwargs.get("bokeh_tools_wheel", False):
        tool = kwargs.get("bokeh_tools_wheel_choice", "Wheel zoom (xy)")
        tools.append(WHEEL_TOOLS.get(tool, "wheel_zoom"))

    # append hover tool
    if kwargs.get("bokeh_tools_hover", False) and hasattr(plot_base, "set_hover_tool"):
        plot_base.set_hover_tool()

    # add active tools
    plot.toolbar.active_drag = parse_active_drag(kwargs.get("bokeh_tools_active_drag", "auto"), tools)
    plot.toolbar.active_scroll = parse_active_wheel(kwargs.get("bokeh_tools_active_wheel", "auto"), tools)
    plot.toolbar.active_inspect = parse_active_inspect(kwargs.get("bokeh_tools_active_inspect", "auto"), tools)
    plot.toolbar.tools = clean_tools(tools)


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
