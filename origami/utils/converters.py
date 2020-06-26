__all__ = [
    "byte2str",
    "str2num",
    "num2str",
    "str2int",
    "float2int",
    "str2bool",
    "rounder",
    "convert_ms_to_bins",
    "convert_bins_to_ms",
    "convert_mins_to_scans",
    "convert_scans_to_mins",
    "convert_cm_to_inch",
    "convert_inch_to_cm",
]

# Standard library imports
from typing import List
from collections import Iterable


def convert_cm_to_inch(values) -> List[float]:
    """Convert centimeters to inches"""
    if not isinstance(values, Iterable):
        values = [values]
    return [_value / 2.54 for _value in values]


def convert_inch_to_cm(values) -> List[float]:
    """Convert centimeters to inches"""
    if not isinstance(values, Iterable):
        values = [values]
    return [_value * 2.54 for _value in values]


def convert_ms_to_bins(values, pusher_freq):
    """Converts milliseconds to drift bins"""

    def _convert(value):
        return round(value / pusher_freq)

    return [_convert(value) for value in values]


def convert_bins_to_ms(values, pusher_freq):
    """Converts drift bins to milliseconds"""

    def _convert(value):
        return float(value * pusher_freq)

    return [_convert(value) for value in values]


def convert_mins_to_scans(values, scan_time):
    """Converts retention time minutes to scans"""

    def convert(value):
        return round(value / scan_time) * 60

    return [convert(value) for value in values]


def convert_scans_to_mins(values, scan_time):
    """Converts scans to retention time in minutes"""

    def _convert(value):
        return round(value * scan_time) / 60

    return [_convert(value) for value in values]


def byte2str(string):
    try:
        return string.decode()
    except Exception as e:
        return string


def str2num(string):
    try:
        val = float(string)
        return val
    except (ValueError, TypeError):
        return None


def num2str(val):
    try:
        string = str(val)
        return string
    except (ValueError, TypeError):
        return None


def str2int(string, default_value=None):
    try:
        val = int(string)
        return val
    except (ValueError, TypeError):
        return default_value


def float2int(num):
    try:
        val = int(num)
        return val
    except (ValueError, TypeError):
        return num


def str2bool(s):
    if s == "True":
        return True
    elif s == "False":
        return False
    else:
        return False  # raise ValueError


def convert_type(value):
    if isinstance(value, str):
        return str(value)
    elif isinstance(value, int):
        return str2int(value)
    elif isinstance(value, float):
        return str2num(value)


def rounder(value, digits=4):
    """Round and return value"""
    value = round(str2num(value), digits)
    return f"{value}"
