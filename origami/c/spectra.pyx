#cython: boundscheck=False
#cython: wraparound=False
#cython: nonecheck=False
#cython: language_level=3

import numpy as np
cimport numpy as np
from scipy.ndimage import gaussian_filter


cpdef baseline_curve_(np.ndarray[ndim=1, dtype=np.float64_t] data, int window):
    cdef:
        int i
        int length = data.shape[0]
        int start, end
        int[:] mins = np.zeros(length, dtype=np.int32)
    
    window = abs(window)
    for i in range(length):
        start = max([0, i - window])
        end = min([i + window, length])
        mins[i] = np.amin(data[start : end])
    background = gaussian_filter(mins, window * 2)
    return data - background