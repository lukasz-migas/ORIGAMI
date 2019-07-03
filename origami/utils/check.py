# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import re
import urllib
from distutils.version import LooseVersion

import numpy as np


def is_prime(a):
    """Check whether value is a prime number"""
    return all(a % i for i in range(2, a))


def check_axes_spacing(values):
    spacing = np.diff(values)
    if len(np.unique(spacing)) > 1:
        return False
    else:
        return True


def check_value(value):
    if value is None:
        return ''
    else:
        return str(value)


def check_type(value, value_type):
    if isinstance(value, value_type):
        return True
    else:
        return False


def check_value_order(value_min, value_max):
    if value_max < value_min:
        value_max, value_min = value_min, value_max

    return value_min, value_max


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


def isbool(value):
    return isinstance(value, bool)


def isnumber(input):
    """ Quick and easy way to check if input is a number """
    return isinstance(input, (int, float, complex))


def get_latest_version(link=None, get_webpage=False):

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
                webVersion = row.strip('()')
                break
        return webVersion
    else:
        webpage = urllib.request.urlopen(
            'https://raw.githubusercontent.com/lukasz-migas/ORIGAMI/master/ORIGAMI_ANALYSE/update_info.md',
        )
        return webpage.read().decode('utf-8')


def compare_versions(newVersion, oldVersion):
    return LooseVersion(newVersion) > LooseVersion(oldVersion)
