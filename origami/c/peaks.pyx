#cython: boundscheck=False
#cython: wraparound=False
#cython: nonecheck=False
#cython: language_level=3
# Third-party imports
cimport numpy as np

# Third-party imports
import numpy as np


cpdef find_peaks_local_max(x, y, int window, float threshold):
    cdef:
        list pks_idx = [] , pks_x = [], pks_y = []
        int length = len(x)
        int i, start, end
        float mz_x_value, mz_y_value
        float max_intensity, test_value, intensity_threshold

    max_intensity = max(y)
    intensity_threshold = max_intensity * threshold
    # iterate over the entire mass range
    for i in range(1, length):
        mz_x_value = x[i]
        mz_y_value = y[i]
        if mz_y_value > intensity_threshold:
            start = i - window
            end = i + window
            if start < 0:
                start = 0
            if end > length:
                end = length
            test_value = max(y[start:end+1])
            if mz_y_value == test_value and mz_y_value != y[i - 1]:
                pks_idx.append(i)
                pks_x.append(mz_x_value)
                pks_y.append(mz_y_value)
    return pks_idx, pks_x, pks_y