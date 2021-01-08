"""Various utilities for peak-picking module"""
# Third-party imports
import numpy as np


def group_by(array: np.ndarray, window: float):
    """Group array elements together if they fall within the window/tolerance range"""
    # add a little wiggle room to account for marginal cases
    window = window + 0.0001
    groups = []
    max_len = len(array)
    prev_group = []
    for i, value in enumerate(array):
        if i in prev_group:
            continue

        group = []
        j = 0
        while True:
            ij = i + j
            if ij == max_len:
                break
            if ij in prev_group:
                break

            _value = array[ij]
            if value - _value <= window:
                group.append(ij)
            else:
                break
            j += 1
        if len(group) > 1:
            groups.append(group)
            prev_group = group
    return groups[::-1]


try:
    has_c = True
    _group_by = group_by

    from origami.c.utilities import group_by
except ImportError as e:
    print(e)
    has_c = False
