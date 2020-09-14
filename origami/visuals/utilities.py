"""Utilities"""
# Third-party imports
import seaborn as sns
import matplotlib
from matplotlib import pyplot as plt
from matplotlib.ticker import FuncFormatter

# Local imports
from origami.utils.color import convert_rgb_1_to_255
from origami.utils.color import convert_rgb_1_to_hex
from origami.config.config import CONFIG

__all__ = (
    "compute_divider",
    "y_tick_fmt",
    "get_intensity_formatter",
    "on_change_color_palette",
    "on_get_colors_from_colormap",
    "on_change_plot_style",
)


def compute_divider(value):
    """Compute divider"""
    divider = 1000000000
    value = abs(value)
    while value == value % divider:
        divider = divider / 1000
    return len(str(int(divider))) - len(str(int(divider)).rstrip("0"))


def y_tick_fmt(x, pos):  # noqa
    """Y-tick formatter"""

    def _convert_divider_to_str(value, exp_value):
        value = float(value)
        if exp_value in [0, 1, 2]:
            if value <= 1:
                return f"{value:.2G}"
            elif value <= 1000:
                if value.is_integer():
                    return f"{value:.0F}"
                return f"{value:.1F}"
        elif exp_value in [3, 4, 5]:
            return f"{value / 1000:.1f}k"
        elif exp_value in [6, 7, 8]:
            return f"{value / 1000000:.0f}M"
        elif exp_value in [9, 10, 11, 12]:
            return f"{value / 1000000000:.0f}B"

    return _convert_divider_to_str(x, compute_divider(x))


def get_intensity_formatter():
    """Simple intensity formatter"""
    return FuncFormatter(y_tick_fmt)


def on_change_color_palette(
    cmap: str = None, n_colors: int = 16, return_colors: bool = False, return_hex: bool = False
):
    """Change color palette"""
    if cmap is not None:
        palette_name = cmap
    else:
        if CONFIG.current_palette in ["Spectral", "RdPu"]:
            palette_name = CONFIG.current_palette
        else:
            palette_name = CONFIG.current_palette.lower()

    new_colors = sns.color_palette(palette_name, n_colors)

    if not return_colors:
        for i in range(n_colors):
            CONFIG.custom_colors[i] = convert_rgb_1_to_255(new_colors[i])
    else:
        if return_hex:
            new_colors_hex = []
            for new_color in new_colors:
                new_colors_hex.append(convert_rgb_1_to_hex(new_color))
            return new_colors_hex
        else:
            return new_colors


def on_get_colors_from_colormap(n_colors: int):
    """Return list of colors from colormap"""
    color_list = sns.color_palette(CONFIG.heatmap_colormap, n_colors)
    return color_list


def on_change_plot_style():
    """Change plot style"""
    # https://tonysyu.github.io/raw_content/matplotlib-style-gallery/gallery.html

    if CONFIG.current_style == "Default":
        matplotlib.rcParams.update(matplotlib.rcParamsDefault)
    elif CONFIG.current_style == "ggplot":
        plt.style.use("ggplot")
    elif CONFIG.current_style == "ticks":
        sns.set_style("ticks")
    else:
        plt.style.use(CONFIG.current_style)
