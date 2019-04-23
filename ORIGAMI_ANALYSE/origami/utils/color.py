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


def convertRGB1to255(rgbList, decimals=3, as_integer=False, as_tuple=False):
    if not as_integer:
        rgbList = list([np.round((np.float(rgbList[0]) * 255), decimals),
                        np.round((np.float(rgbList[1]) * 255), decimals),
                        np.round((np.float(rgbList[2]) * 255), decimals)])
    else:
        try:
            rgbList = list([int((np.float(rgbList[0]) * 255)),
                            int((np.float(rgbList[1]) * 255)),
                            int((np.float(rgbList[2]) * 255))])
        except ValueError:
            rgbList = eval(rgbList)
            rgbList = list([int((np.float(rgbList[0]) * 255)),
                            int((np.float(rgbList[1]) * 255)),
                            int((np.float(rgbList[2]) * 255))])

    if not as_tuple:
        return rgbList
    else:
        return tuple(rgbList)


def convertRGB1toHEX(rgbList):

        return '#{:02x}{:02x}{:02x}'.format(int((np.float(rgbList[0]) * 255)),
                                            int((np.float(rgbList[1]) * 255)),
                                            int((np.float(rgbList[2]) * 255)))


def convertRGB255toHEX(rgbList):

        return '#{:02x}{:02x}{:02x}'.format(int((np.float(rgbList[0]))),
                                            int((np.float(rgbList[1]))),
                                            int((np.float(rgbList[2]))))


def convertHEXtoRGB1(hex, decimals=3):
    hex = hex.lstrip('#')
    hlen = len(hex)
    rgb = tuple(int(hex[i:i + int(hlen / 3)], 16) for i in range(0, int(hlen), int(hlen / 3)))
    return [np.round(rgb[0] / 255., decimals), np.round(rgb[1] / 255., decimals), np.round(rgb[2] / 255., decimals)]


def convertHEXtoRGB255(hex, decimals=3):
    hex = hex.lstrip('#')
    hlen = len(hex)
    return tuple(int(hex[i:i + int(hlen / 3)], 16) for i in range(0, hlen, int(hlen / 3)))


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


def make_rgb(x, color):
    """
    Convert array to specific color
    """
    # Get size of the input array
    y_size, x_size = x.shape

    # Create an empty 3D array
    rgb = np.zeros([y_size, x_size, 3], dtype='d')

    # Make sure color is an rgb format and not string format
    try:
        color = literal_eval(color)
    except:
        color = color

    # Check color range is 0-1
    if np.max(color) > 1.0:
        color = remap_values(color, 0, 1, type_format='float')

    # Represent as color range
    r_color, g_color, b_color = color

    # Red channel
    if r_color > 0:
        r_rgb = remap_values(x, 0, r_color, type_format='float')
    else:
        r_rgb = np.zeros_like(x)

    # Green channel
    if g_color > 0:
        g_rgb = remap_values(x, 0, g_color, type_format='float')
    else:
        g_rgb = np.zeros_like(x)

    # Blue channel
    if b_color > 0:
        b_rgb = remap_values(x, 0, b_color, type_format='float')
    else:
        b_rgb = np.zeros_like(x)

    # Add to 3D array
    rgb[:, :, 0] = r_rgb
    rgb[:, :, 1] = g_rgb
    rgb[:, :, 2] = b_rgb

    return rgb


def remap_values(x, nMin, nMax, oMin=None, oMax=None, type_format='int'):

    if oMin == None:
        oMin = np.min(x)
    if oMax == None:
        oMax = np.max(x)

    # range check
    if oMin == oMax:
        print("Warning: Zero input range")
        return None

    if nMin == nMax:
        print("Warning: Zero input range")
        return None

    # Check that values are of correct type
    if type_format == 'float':
        nMin = float(nMin)
        nMax = float(nMax)

    # check reversed input range
    reverseInput = False
    oldMin = min(oMin, oMax)
    oldMax = max(oMin, oMax)
    if not oldMin == oMin:
        reverseInput = True

    # check reversed output range
    reverseOutput = False
    newMin = min(nMin, nMax)
    newMax = max(nMin, nMax)
    if not newMin == nMin :
        reverseOutput = True

    portion = (x - oldMin) * (newMax - newMin) / (oldMax - oldMin)
    if reverseInput:
        portion = (oldMax - x) * (newMax - newMin) / (oldMax - oldMin)

    result = portion + newMin
    if reverseOutput:
        result = newMax - portion

    if type_format == 'int':
        return result.astype(int)
    elif type_format == 'float':
        return result.astype(float)
    else:
        return result


def combine_rgb(data_list):
    return np.sum(data_list, axis=0)
