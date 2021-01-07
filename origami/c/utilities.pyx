# cython: embedsignature = True
# cython: cdivision = True
# cython: boundscheck = False
# cython: wraparound=False
#cython: language_level=3
# Third-party imports
import cython

# Third-party imports
cimport numpy as np

# Third-party imports
import numpy as np


cpdef double ppm_error(double x, double y):
    return (x - y) / y

cpdef group_by(np.float64_t [:] array, float window):
    window = window + 0.001
    cdef:
        list groups = [], prev_group = [], group
        int max_len = len(array)
        int i, j, ij
        np.float64_t value, _value

    for i in range(max_len):
        if i in prev_group:
            continue

        value = array[i]
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