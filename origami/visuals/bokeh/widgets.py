"""Various Bokeh extensions"""
# Standard library imports
import logging
from typing import List
from typing import Union

# Third-party imports
from bokeh import events
from bokeh.models import Line
from bokeh.models import Image
from bokeh.models import Legend
from bokeh.models import Select
from bokeh.models import Slider
from bokeh.models import Toggle
from bokeh.models import Scatter
from bokeh.models import ColorBar
from bokeh.models import CustomJS
from bokeh.models import Dropdown
from bokeh.models import LabelSet
from bokeh.models import HoverTool
from bokeh.models import ColorPicker
from bokeh.models import RadioButtonGroup
from bokeh.plotting import Figure

# Local imports
from origami.visuals.bokeh.utilities import convert_colormap_to_mapper

LOGGER = logging.getLogger(__name__)

ANNOTATION_WIDGET_LIST = [
    "annotations_toggle",
    "annotations_font_size",
    "annotations_offset_x",
    "annotations_offset_y",
    "annotations_rotation",
]
SCATTER_WIDGET_LIST = ["scatter_size", "scatter_transparency"]
HOVER_WIDGET_LIST = ["hover_mode"]
FIGURE_WIDGET_LIST = ["figure_width", "figure_height", "figure_sizing_mode"]
LEGEND_WIDGET_LIST = []


def add_events(plot_obj, event_list: List[str]):
    """Add events to the plot object"""
    for event_name in event_list:
        if event_name == "double_tab_zoom_out_event":
            double_tab_zoom_out_event(plot_obj.figure)


def add_widgets(plot_obj, widget_list: List[str], widget_width: int = 300):
    """Add widgets to the plot object"""
    widgets = []
    for widget_name in widget_list:
        widget = None
        # annotation (Label/LabelSet) widgets
        if widget_name.startswith("annotations"):
            widget = add_annotation_widgets(plot_obj, widget_name, widget_width)
        elif widget_name.startswith("scatter"):
            widget = add_scatter_widgets(plot_obj, widget_name, widget_width)
        elif widget_name.startswith("hover"):
            widget = add_hover_widgets(plot_obj, widget_name, widget_width)
        elif widget_name.startswith("figure"):
            widget = add_figure_widgets(plot_obj, widget_name, widget_width)

        if widget is not None:
            widgets.append(widget)

    return widgets


def add_annotation_widgets(plot_obj, widget_name: str, widget_width: int = 300):
    """Add annotation widgets"""
    annotations = plot_obj.get_annotation("LabelSet")
    if not annotations:
        return None
    if widget_name == "annotations_toggle":
        return annotations_toggle(plot_obj.figure, annotations, widget_width)
    elif widget_name == "annotations_font_size":
        return annotations_font_size(plot_obj.figure, annotations, widget_width)
    elif widget_name == "annotations_offset_x":
        return annotations_offset_x(plot_obj.figure, annotations, widget_width)
    elif widget_name == "annotations_offset_y":
        return annotations_offset_y(plot_obj.figure, annotations, widget_width)
    elif widget_name == "annotations_rotation":
        return annotations_rotation(plot_obj.figure, annotations, widget_width)
    else:
        LOGGER.warning(f"Could not parse `{widget_name}` - please use any of the following {ANNOTATION_WIDGET_LIST}`")


def add_scatter_widgets(plot_obj, widget_name: str, widget_width: int = 300):
    """Add annotation widgets"""
    scatter = plot_obj.get_glyph(Scatter)
    if not scatter:
        return None
    if widget_name == "scatter_size":
        return scatter_size(plot_obj.figure, scatter, widget_width)
    elif widget_name == "scatter_transparency":
        return scatter_transparency(plot_obj.figure, scatter, widget_width)
    else:
        LOGGER.warning(f"Could not parse `{widget_name}` - please use any of the following {SCATTER_WIDGET_LIST}`")


def add_hover_widgets(plot_obj, widget_name: str, widget_width: int = 300):
    """Add annotation widgets"""
    hovers = plot_obj.get_glyph(HoverTool)
    if not hovers:
        return None
    if widget_name == "hover_mode":
        return hover_mode(plot_obj.figure, hovers, widget_width)
    else:
        LOGGER.warning(f"Could not parse `{widget_name}` - please use any of the following {HOVER_WIDGET_LIST}`")


def add_figure_widgets(plot_obj, widget_name: str, widget_width: int = 300):
    """Add annotation widgets"""
    if widget_name == "figure_width":
        return link_figure_width(plot_obj.figure, widget_width)
    elif widget_name == "figure_height":
        return link_figure_height(plot_obj.figure, widget_width)
    elif widget_name == "figure_sizing_mode":
        return figure_sizing_mode(plot_obj.figure, widget_width)
    else:
        LOGGER.warning(f"Could not parse `{widget_name}` - please use any of the following {FIGURE_WIDGET_LIST}`")


def annotations_toggle(figure: Figure, labels: Union[LabelSet, List[LabelSet]], widget_width: int = 300):
    """Create toggle responsible for showing/hiding labels"""
    js_code = """\
    if (cb_obj.active) {
        var text_alpha = 1;
        var label = "Hide labels";
    } else {
        var text_alpha = 0;
        var label = "Show labels";
    }
    for (var i in labels) {
        var _labels = labels[i];
        _labels.text_alpha = text_alpha;
    }
    cb_obj.label = label;
    console.log("Toggled labels");
    """
    if not isinstance(labels, (list, tuple)):
        labels = [labels]
    callback = CustomJS(code=js_code, args={"labels": labels, "figure": figure})
    toggle = Toggle(label="Hide labels", button_type="success", active=True, width=widget_width)
    toggle.js_on_change("active", callback)
    return toggle


def annotations_font_size(figure: Figure, labels, widget_width: int = 300):
    """Add slider to control annotation size"""
    js_code = """\
    var label_size = cb_obj.value;
    for (var i in labels) {
        var _labels = labels[i];
        _labels.text_font_size = label_size + 'pt';
    }
    console.log('Font size: ' + label_size);
    """
    if not isinstance(labels, (list, tuple)):
        labels = [labels]
    callback = CustomJS(code=js_code, args={"labels": labels, "figure": figure})
    slider = Slider(start=6, end=30, step=1, value=10, title="Label fontsize", width=widget_width)
    slider.js_on_change("value", callback)
    return slider


def annotations_offset_x(figure: Figure, labels, widget_width: int = 300):
    """Add slider to control annotation size"""
    js_code = """\
    var x_offset = cb_obj.value;
    for (var i in labels) {
        var _labels = labels[i];
        _labels.x_offset = x_offset;
    }
    console.log('X offset: ' + x_offset);
    """
    if not isinstance(labels, (list, tuple)):
        labels = [labels]
    callback = CustomJS(code=js_code, args={"labels": labels, "figure": figure})
    slider = Slider(start=-100, end=100, step=5, value=50, title="Label x-axis offset", width=widget_width)
    slider.js_on_change("value", callback)
    return slider


def annotations_offset_y(figure: Figure, labels, widget_width: int = 300):
    """Add slider to control annotation size"""
    js_code = """\
    var y_offset = cb_obj.value;
    for (var i in labels) {
        var _labels = labels[i];
        _labels.y_offset = y_offset;
    }
    console.log('Y offset: ' + y_offset);
    """
    if not isinstance(labels, (list, tuple)):
        labels = [labels]
    callback = CustomJS(code=js_code, args={"labels": labels, "figure": figure})
    slider = Slider(start=-100, end=100, step=5, value=50, title="Label y-axis offset", width=widget_width)
    slider.js_on_change("value", callback)
    return slider


def annotations_rotation(figure: Figure, labels, widget_width: int = 300):
    """Add slider to control annotation size"""
    js_code = """\
    var angle = cb_obj.value * 0.0174533;
    for (var i in labels) {
        var _labels = labels[i];
        _labels.angle_units = 'deg';
        _labels.angle = angle;
    }
    console.log('Angle changed to: ' + angle);
    """
    if not isinstance(labels, (list, tuple)):
        labels = [labels]
    callback = CustomJS(code=js_code, args={"labels": labels, "figure": figure})
    slider = Slider(start=0, end=180, step=10, value=0, title="Label rotation angle", width=widget_width)
    slider.js_on_change("value", callback)
    return slider


def legend_toggle(figure: Figure, legend: Legend, widget_width: int = 300):
    """Add toggle to show/hide legend object"""
    js_code = """\
    if (cb_obj.active) {
        legend.border_line_alpha = 0;
        legend.visible = true;
        cb_obj.label = "Hide legend";
        console.log('Showing legend');
    } else {
        legend.border_line_alpha = 0;
        legend.visible = false;
        cb_obj.label = "Show legend";
        console.log('Hiding legend');
    }
    figure.change.emit();
    """
    callback = CustomJS(code=js_code, args={"legend": legend, "figure": figure})
    toggle = Toggle(label="Hide legend", button_type="success", active=True, width=widget_width)
    toggle.js_on_change("active", callback)
    return toggle


def legend_position(figure: Figure, legend: Legend, widget_width: int = 300):
    """Add Dropdown to move the legend object"""
    js_code = """\
    position = cb_obj.value;
    legend.location = position;
    legend.visible = true;
    figure.change.emit();
    console.log('Legend position: ' + position);
    """
    menu = [
        ("Top left", "top_left"),
        ("Top right", "top_right"),
        ("Bottom left", "bottom_left"),
        ("Bottom right", "bottom_right"),
    ]
    callback = CustomJS(code=js_code, args={"legend": legend, "figure": figure})
    dropdown = Dropdown(menu=menu, label="Legend position", width=widget_width)
    dropdown.js_on_change("value", callback)
    return dropdown


def legend_orientation(figure: Figure, legend: Legend, widget_width: int = 300):
    """Add toggle to control orientation of the legend"""
    js_code = """\
    if (cb_obj.active == 0) {
        legend.orientation = 'vertical';
        console.log('Legend orientation: vertical');
        }
    else if (cb_obj.active == 1) {
        legend.orientation = 'horizontal';
        console.log('Legend orientation: horizontal');
    }
    figure.change.emit();
    """
    active_mode = 0  # TODO: get from config or legend object
    callback = CustomJS(code=js_code, args={"legend": legend, "figure": figure})
    radio = RadioButtonGroup(labels=["Vertical", "Horizontal"], active=active_mode, width=widget_width)
    radio.js_on_change("active", callback)
    return radio


def legend_transparency(figure: Figure, legend: Legend, widget_width: int = 300):
    """Add toggle to control orientation of the legend"""
    js_code = """
    var transparency = cb_obj.value;
    legend.background_fill_alpha = transparency;
    figure.change.emit();
    console.log('Legend transparency: ' + transparency);
    """
    callback = CustomJS(code=js_code, args={"legend": legend, "figure": figure})
    slider = Slider(start=0, end=1, step=0.1, value=1, title="Legend transparency", width=widget_width)
    slider.js_on_change("value", callback)
    return slider


def scatter_size(figure: Figure, scatter: Scatter, widget_width: int = 300):
    """Set size of the scatter points"""
    js_code = """\
    var scatter_size = cb_obj.value;
    for (var i in scatter) {
        var _scatter = scatter[i];
        _scatter.glyph.size = scatter_size;
    }
    figure.change.emit();
    console.log('Scatter size: ' + scatter_size);
    """
    if not isinstance(scatter, (list, tuple)):
        scatter = [scatter]
    callback = CustomJS(code=js_code, args={"scatter": scatter, "figure": figure})
    slider = Slider(start=1, end=100, step=1, value=1, title="Scatter size", width=widget_width)
    slider.js_on_change("value", callback)
    return slider


def scatter_transparency(figure: Figure, scatter: Scatter, widget_width: int = 300):
    """Set size of the scatter points"""
    js_code = """
    var scatter_alpha = cb_obj.value;
    for (var i in scatter) {
        var _scatter = scatter[i];
        _scatter.glyph.line_alpha = scatter_alpha;
        _scatter.glyph.fill_alpha = scatter_alpha;
    }
    figure.change.emit();
    console.log('Scatter transparency: ' + scatter_alpha);
    """
    if not isinstance(scatter, (list, tuple)):
        scatter = [scatter]
    callback = CustomJS(code=js_code, args={"scatter": scatter, "figure": figure})
    slider = Slider(start=0, end=1, step=0.05, value=1, title="Scatter transparency", width=widget_width)
    slider.js_on_change("value", callback)
    return slider


def heatmap_colormap(
    figure: Figure, image: Image, colorbar: ColorBar, array, colormap_names: List[str], widget_width: int = 300
):
    """Change colormap of the image"""
    js_code = """\
    var cmap = cb_obj.value;
    for (var i in image) {
        var _image = image[i];
        _image.glyph.color_mapper.palette = cmap;
    }
    figure.change.emit();
    console.log("Changed colormap to " + cmap);
    """
    menu, colormaps = [], []
    for i, cmap in enumerate(colormap_names):
        menu.append(("{}".format(colormap_names[i]), str(i)))
        colormaps.append(cmap)
    if not isinstance(image, (list, tuple)):
        image = [image]
    if not isinstance(colorbar, (list, tuple)):
        colorbar = [colorbar]

    callback = CustomJS(
        code=js_code, args={"image": image, "colorbar": colorbar, "colormaps": colormaps, "figure": figure}
    )
    dropdown = Select(options=["Viridis", "Cividis"], title="Colormap selection", width=widget_width)
    dropdown.js_on_change("value", callback)
    return dropdown


def heatmap_colormap2(
    figure: Figure, image: Image, colorbar: ColorBar, array, colormap_names: List[str], widget_width: int = 300
):
    """Change colormap of the image"""
    # _image.glyph.color_mapper = cmap;
    js_code = """\
    var idx = parseInt(cb_obj.value, 10);
    var cmap = colormaps[idx]
    for (var i in image) {
        var image2 = image[i];
        console.log(image2);

    }
    figure.change.emit();
    console.log("Changed colormap to " + cmap);
    """
    menu, colormaps = [], []
    for i, cmap in enumerate(colormap_names):
        menu.append(("{}".format(colormap_names[i]), str(i)))
        _, colormapper = convert_colormap_to_mapper(array, cmap)
        colormaps.append(colormapper)

    if not isinstance(image, (list, tuple)):
        image = [image]
    if not isinstance(colorbar, (list, tuple)):
        colorbar = [colorbar]

    callback = CustomJS(
        code=js_code, args={"image": image, "colorbar": colorbar, "colormaps": colormaps, "figure": figure}
    )
    dropdown = Dropdown(menu=menu, label="Colormap selection", width=widget_width)
    dropdown.js_on_event("menu_item_click", callback)
    return dropdown


def hover_mode(figure: Figure, hover: HoverTool, widget_width: int = 300):
    """Add RadioButtonGroup to change how HoverTool behaves"""
    js_code = """\
    var hover_mode = cb_obj.value;
    for (var i in hover) {
        var _hover = hover[i];
        _hover.mode = hover_mode;
    }
    console.debug("Changed hover mode to " + hover_mode);
    """
    if not isinstance(hover, (list, tuple)):
        hover = [hover]
    callback = CustomJS(code=js_code, args={"hover": hover, "figure": figure})
    active_mode = "mouse"
    for _hover in hover:
        active_mode = _hover.mode
    dropdown = Select(options=["mouse", "vline", "hline"], value=active_mode, title="Hover mode", width=widget_width)
    dropdown.js_on_change("value", callback)
    return dropdown


def figure_sizing_mode(figure: Figure, widget_width: int = 300):
    """Change colormap of the image"""
    js_code = """\
    var sizing_mode = cb_obj.value;
    figure.sizing_mode = sizing_mode
    figure.change.emit();
    console.log("Changed sizing mode to " + sizing_mode);
    """

    callback = CustomJS(code=js_code, args={"figure": figure})
    dropdown = Select(
        options=[
            "fixed",
            "stretch_width",
            "stretch_height",
            "scale_width",
            "scale_width",
            "scale_height",
            "scale_both",
        ],
        title="Sizing mode",
        width=widget_width,
    )
    dropdown.js_on_change("value", callback)
    return dropdown


def link_edge_color(plot_obj: Union[Line, Scatter], widget_width: int = 300):
    """Link color of a edge color of the glyph"""
    color = plot_obj.glyph.line_color
    label = "Line" if isinstance(plot_obj, Line) else "Scatter"
    picker = ColorPicker(title=f"{label} color", width=widget_width, color=color)
    picker.js_link("color", plot_obj.glyph, "line_color")
    return picker


def link_edge_width(plot_obj: Union[Line, Scatter], widget_width: int = 300):
    """Link color of a fill color of the glyph"""
    line_width = plot_obj.glyph.line_width
    label = "Line" if isinstance(plot_obj, Line) else "Edge"
    slider = Slider(start=0.1, end=10, step=0.5, value=line_width, title=f"{label} width", width=widget_width)
    slider.js_link("value", plot_obj.glyph, "line_width")
    return slider


def link_edge_transparency(plot_obj: Union[Line, Scatter], widget_width: int = 300):
    """Link color of a fill color of the glyph"""
    line_width = plot_obj.glyph.line_width
    label = "Line" if isinstance(plot_obj, Line) else "Edge"
    slider = Slider(start=0.0, end=1, step=0.05, value=line_width, title=f"{label} transparency", width=widget_width)
    slider.js_link("value", plot_obj.glyph, "line_alpha")
    return slider


def link_fill_color(plot_obj: Union[Scatter], widget_width: int = 300):
    """Link color of a fill color of the glyph"""
    color = plot_obj.glyph.fill_color
    picker = ColorPicker(title="Fill color", width=widget_width, color=color)
    picker.js_link("color", plot_obj.glyph, "fill_color")
    return picker


def link_fill_transparency(plot_obj: Union[Scatter], widget_width: int = 300):
    """Link color of a fill color of the glyph"""
    line_width = plot_obj.glyph.line_width
    slider = Slider(start=0.0, end=1, step=0.05, value=line_width, title="Fill transparency", width=widget_width)
    slider.js_link("value", plot_obj.glyph, "fill_alpha")
    return slider


def link_figure_width(figure: Figure, widget_width: int = 300):
    """Link color of a fill color of the glyph"""
    plot_width = figure.plot_width
    slider = Slider(start=50, end=1000, step=50, value=plot_width, title="Plot width", width=widget_width)
    slider.js_link("value", figure, "plot_width")
    return slider


def link_figure_height(figure: Figure, widget_width: int = 300):
    """Link color of a fill color of the glyph"""
    plot_height = figure.plot_height
    slider = Slider(start=50, end=1000, step=50, value=plot_height, title="Plot height", width=widget_width)
    slider.js_link("value", figure, "plot_height")
    return slider


def double_tab_zoom_out_event(figure):
    """Zoom-out in the plot area during double-tap event"""
    js_code = """\
    console.log('Resetting zoom');
    figure.reset.emit();
    """
    figure.js_on_event(events.DoubleTap, CustomJS(code=js_code, args={"figure": figure}))
