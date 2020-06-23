# Third-party imports
import numpy as np


def is_prime(a):
    """Check whether value is a prime number"""
    return all(a % i for i in range(2, a))


def check_axes_spacing(values):
    spacing = np.diff(values)

    if len(np.unique(spacing)) > 1:
        return False
    return True


def check_value(value):
    if value is None:
        return ""
    return str(value)


def check_type(value, value_type):
    if isinstance(value, value_type):
        return True
    return False


def check_value_order(value_min, value_max):
    if not isnumber(value_min) or not isnumber(value_max):
        return value_min, value_max

    if value_max < value_min:
        value_max, value_min = value_min, value_max

    return value_min, value_max


def check_range(value, range_min, range_max):
    # check if range values are supplied in correct order
    if range_min > range_max:
        range_max, range_min = range_min, range_max

    if range_min <= value <= range_max:
        return True
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


def isnumber(value):
    """ Quick and easy way to check if input is a number """
    return isinstance(value, (int, float, complex))
