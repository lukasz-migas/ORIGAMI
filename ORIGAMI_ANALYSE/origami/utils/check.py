import numpy as np
import urllib
from distutils.version import LooseVersion
import re


def check_type(value, value_type):
    if isinstance(value, value_type):
        return True
    else:
        return False


def check_range(value, range_min, range_max):
    # check if range values are supplied in correct order
    if range_min > range_max:
        range_max, range_min = range_min, range_max

    if range_min <= value <= range_max:
        return True
    else:
        return False


def isempty(val):
    try:
        if np.asarray(val).size == 0 or val is None:
            out = True
        else:
            out = False
    except (TypeError, ValueError, AttributeError):
        out = False

    return out


def isnumber(input):
    """ Quick and easy way to check if input is a number """
    return isinstance(input, (int, float, complex))


def checkVersion(link=None, get_webpage=False):

    if not get_webpage:
        # Search website for all versions
        vers = []
        for line in urllib.request.urlopen(link):
            if 'Update to ORIGAMI-ANALYSE (' in line.decode('utf-8'):
                vers.append(line)
                break
        if len(vers) == 0:
            return None
        # Split the latest one to get newest version
        split = re.split(' |<', vers[0])
        webVersion = None
        for row in split:
            if '(' in row:
                webVersion = row.strip("()")
                break
        return webVersion
    else:
        webpage = urllib.request.urlopen(
            "https://raw.githubusercontent.com/lukasz-migas/ORIGAMI/master/ORIGAMI_ANALYSE/update_info.md")
        return webpage.read().decode('utf-8')


def compareVersions(newVersion, oldVersion):
    return LooseVersion(newVersion) > LooseVersion(oldVersion)
