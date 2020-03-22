"""Various color utility functions"""
# Standard library imports
import re
from ast import literal_eval

# Third-party imports
import numpy as np

# Local imports
from origami.utils.random import random_int_0_to_255


def get_n_colors(n_colors):
    colors = []
    for __ in range(n_colors):
        colors.append(get_random_color())
    return colors


def get_all_color_types(color_1, as_255=False):
    """Convert color(1) to font color and color(255) representation"""
    if as_255:
        color_1 = convert_rgb_255_to_1(color_1)
    else:
        color_255 = convert_rgb_1_to_255(color_1, as_integer=True)
    font_color = get_font_color(color_255, return_rgb=True)

    return color_255, color_1, font_color


def check_color_type(color):
    if isinstance(color, list):
        return color

    if color in [None, ""]:
        return get_random_color(return_as_255=True)

    if re.search(r"^#(?:[0-9a-fA-F]{3}){1,2}$", color):
        return convert_hex_to_rgb_255(color)


def check_color_format(color):

    if np.sum(color) < 4:
        return convert_rgb_1_to_255(color)

    return color


def get_random_color(return_as_255=False):

    color = (random_int_0_to_255(), random_int_0_to_255(), random_int_0_to_255())

    if not return_as_255:
        color = convert_rgb_255_to_1(color)

    return color


def convert_rgb_255_to_1(rgbList, decimals=3, check_color_range=False):

    # Make sure color is an rgb format and not string format
    try:
        rgbList = literal_eval(rgbList)
    except Exception:
        rgbList = rgbList

    if check_color_range:
        rgbList = check_color_format(rgbList)

    rgbList = list(
        [
            round((np.float(rgbList[0]) / 255), decimals),
            round((np.float(rgbList[1]) / 255), decimals),
            round((np.float(rgbList[2]) / 255), decimals),
        ]
    )
    return rgbList


def convert_rgb_1_to_255(rgbList, decimals=3, as_integer=False, as_tuple=False):
    if not as_integer:
        rgbList = list(
            [
                np.round((np.float(rgbList[0]) * 255), decimals),
                np.round((np.float(rgbList[1]) * 255), decimals),
                np.round((np.float(rgbList[2]) * 255), decimals),
            ]
        )
    else:
        try:
            rgbList = list(
                [int(np.float(rgbList[0]) * 255), int(np.float(rgbList[1]) * 255), int(np.float(rgbList[2]) * 255)]
            )
        except ValueError:
            rgbList = literal_eval(rgbList)
            rgbList = list(
                [int(np.float(rgbList[0]) * 255), int(np.float(rgbList[1]) * 255), int(np.float(rgbList[2]) * 255)]
            )

    if not as_tuple:
        return rgbList

    return tuple(rgbList)


def convert_rgb_1_to_hex(rgbList):

    return "#{:02x}{:02x}{:02x}".format(
        int(np.float(rgbList[0]) * 255), int(np.float(rgbList[1]) * 255), int(np.float(rgbList[2]) * 255)
    )


def convert_rgb_255_to_hex(rgbList):

    return "#{:02x}{:02x}{:02x}".format(int(np.float(rgbList[0])), int(np.float(rgbList[1])), int(np.float(rgbList[2])))


def convert_hex_to_rgb_1(hex_str, decimals=3):
    hex_color = hex_str.lstrip("#")
    hlen = len(hex_color)
    rgb = tuple(int(hex_color[i : i + int(hlen / 3)], 16) for i in range(0, int(hlen), int(hlen / 3)))
    return [np.round(rgb[0] / 255.0, decimals), np.round(rgb[1] / 255.0, decimals), np.round(rgb[2] / 255.0, decimals)]


def convert_hex_to_rgb_255(hex_str):
    hex_color = hex_str.lstrip("#")
    hlen = len(hex_color)
    rgb = tuple(int(hex_color[i : i + int(hlen / 3)], 16) for i in range(0, int(hlen), int(hlen / 3)))
    return rgb


def get_font_color(rgb, rgb_mode=2, return_rgb=False, convert1to255=False):
    """
    This function determines the luminance of background and determines the
    'best' font color based on that value

    --- LINKS ---
    https://stackoverflow.com/questions/596216/formula-to-determine-brightness-of-rgb-color
    https://stackoverflow.com/questions/1855884/determine-font-color-based-on-background-color
    """

    if convert1to255:
        rgb = convert_rgb_1_to_255(rgb)

    if rgb_mode == 1:
        value = 1 - (rgb[0] * 0.2126 + rgb[1] * 0.7152 + rgb[2] * 0.0722) / 255
    elif rgb_mode == 2:
        value = 1 - (rgb[0] * 0.299 + rgb[1] * 0.587 + rgb[2] * 0.114) / 255

    elif rgb_mode == 3:
        value = 1 - (np.sqrt(rgb[0]) * 0.299 + np.sqrt(rgb[1]) * 0.587 + np.sqrt(rgb[2]) * 0.114) / 255
    if value < 0.5:
        if return_rgb:
            return (0, 0, 0)
        return "black"
    else:
        if return_rgb:
            return (255, 255, 255)

        return "white"


def make_rgb_cube(x, color, add_alpha=False):
    """
    Convert array to specific color
    """
    # Get size of the input array
    y_size, x_size = x.shape

    # Make sure color is an rgb format and not string format
    try:
        color = literal_eval(color)
    except Exception:
        color = color

    # remove alpha channel
    if len(color) == 4:
        color = color[0:3]

    # Check color range is 0-1
    if np.max(color) > 1.0:
        color = remap_values(color, 0, 1, type_format="float")

    # Represent as color range
    r_color, g_color, b_color = color

    # Red channel
    if r_color > 0:
        r_rgb = remap_values(x, 0, r_color, type_format="float")
    else:
        r_rgb = np.zeros_like(x)

    # Green channel
    if g_color > 0:
        g_rgb = remap_values(x, 0, g_color, type_format="float")
    else:
        g_rgb = np.zeros_like(x)

    # Blue channel
    if b_color > 0:
        b_rgb = remap_values(x, 0, b_color, type_format="float")
    else:
        b_rgb = np.zeros_like(x)

    # Add to 3D array
    rgb_channels = 3
    if add_alpha:
        rgb_channels = 4
    rgb = np.zeros([y_size, x_size, rgb_channels], dtype="d")
    rgb[:, :, 0] = r_rgb
    rgb[:, :, 1] = g_rgb
    rgb[:, :, 2] = b_rgb

    if add_alpha:
        alpha_mask = np.copy(x)
        alpha_mask[~np.isnan(alpha_mask)] = 1
        alpha_mask[np.isnan(alpha_mask)] = 0
        rgb[:, :, 3] = alpha_mask

    return rgb


def remap_values(x, n_min, n_max, o_min=None, o_max=None, type_format="int"):

    if o_min is None:
        o_min = np.min(x)
    if o_max is None:
        o_max = np.max(x)

    # range check
    if o_min == o_max:
        print("Warning: Zero input range")
        return None

    if n_min == n_max:
        print("Warning: Zero input range")
        return None

    # Check that values are of correct type
    if type_format == "float":
        n_min = float(n_min)
        n_max = float(n_max)

    # check reversed input range
    reverse_input = False
    old_min = min(o_min, o_max)
    old_max = max(o_min, o_max)
    if not old_min == o_min:
        reverse_input = True

    # check reversed output range
    reverse_output = False
    new_min = min(n_min, n_max)
    new_max = max(n_min, n_max)
    if not new_min == n_min:
        reverse_output = True

    portion = (x - old_min) * (new_max - new_min) / (old_max - old_min)
    if reverse_input:
        portion = (old_max - x) * (new_max - new_min) / (old_max - old_min)

    result = portion + new_min
    if reverse_output:
        result = new_max - portion

    if type_format == "int":
        return result.astype(int)
    elif type_format == "float":
        return result.astype(float)

    return result


def rgb_normalize_channel(image, channel, vmin, vmax):
    image_channel = (image[:, :, channel] - vmin) / (vmax - vmin)
    image_channel = np.clip(image_channel, 0.0, 1.0)
    image[:, :, channel] = image_channel
    return image


def combine_rgb(data_list):
    combined_rgb = np.sum(data_list, axis=0)

    return np.clip(combined_rgb, 0.0, 1.0)


def round_rgb(rgbList, decimals=3):
    rgbList = list([round(rgbList[0], decimals), round(rgbList[1], decimals), round(rgbList[2], decimals)])
    return rgbList
