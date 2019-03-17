import numpy as np


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
