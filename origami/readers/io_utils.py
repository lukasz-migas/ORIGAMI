# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
# Standard library imports
# Standard library imports
# Standard library imports
import os


def remove_non_digits_from_list(check_list):
    list_update = []
    for s in check_list:
        try:
            float(s)
            list_update.append(s)
        except Exception:
            pass

    return list_update


def clean_up(filepath):
    try:
        os.remove(filepath)
    except Exception:
        pass
