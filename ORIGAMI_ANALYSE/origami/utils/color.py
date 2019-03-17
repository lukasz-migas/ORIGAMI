from ast import literal_eval
from utils.random import random_int_0_to_255
import numpy as np

__all__ = ["randomColorGenerator", "convertRGB255to1", "convertRGB1to255", "determineFontColor"]


def randomColorGenerator(return_as_255=False):

    color = (random_int_0_to_255(),
             random_int_0_to_255(),
             random_int_0_to_255())

    if return_as_255:
        return color
    else:
        color = convertRGB255to1(color)
    return color


def convertRGB255to1(rgbList, decimals=3):

    # Make sure color is an rgb format and not string format
    try:
        rgbList = literal_eval(rgbList)
    except Exception:
        rgbList = rgbList

    rgbList = list([round((np.float(rgbList[0]) / 255), decimals),
                    round((np.float(rgbList[1]) / 255), decimals),
                    round((np.float(rgbList[2]) / 255), decimals)])
    return rgbList


def convertRGB1to255(rgbList, decimals=3, as_int=False):
    rgbList = list([np.round((np.float(rgbList[0]) * 255), decimals),
                    np.round((np.float(rgbList[1]) * 255), decimals),
                    np.round((np.float(rgbList[2]) * 255), decimals)])

    if as_int:
        return [int(rgbList[0]), int(rgbList[1]), int(rgbList[2])]
    else:
        return rgbList


def determineFontColor(rgb, rgb_mode=2, return_rgb=False, convert1to255=False):
    """
    This function determines the luminance of background and determines the
    'best' font color based on that value

    --- LINKS ---
    https://stackoverflow.com/questions/596216/formula-to-determine-brightness-of-rgb-color
    https://stackoverflow.com/questions/1855884/determine-font-color-based-on-background-color
    """

    if convert1to255:
        rgb = convertRGB1to255(rgb)

    if rgb_mode == 1:
        a = 1 - (rgb[0] * 0.2126 +
                 rgb[1] * 0.7152 +
                 rgb[2] * 0.0722) / 255
    elif rgb_mode == 2:
        a = 1 - (rgb[0] * 0.299 +
                 rgb[1] * 0.587 +
                 rgb[2] * 0.114) / 255

    elif rgb_mode == 3:
        a = 1 - (np.sqrt(rgb[0]) * 0.299 +
                 np.sqrt(rgb[1]) * 0.587 +
                 np.sqrt(rgb[2]) * 0.114) / 255
    if a < 0.5:
        if return_rgb:
            return (0, 0, 0)
        else:
            return "black"
    else:
        if return_rgb:
            return (255, 255, 255)
        else:
            return "white"
