# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas

__all__ = ["byte2str", "str2num", "num2str", "str2int", "float2int", "str2bool"]


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


def str2int(string):
    try:
        val = int(string)
        return val
    except (ValueError, TypeError):
        return None


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
