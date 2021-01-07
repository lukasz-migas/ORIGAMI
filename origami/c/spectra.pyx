#cython: boundscheck=False
#cython: wraparound=False
#cython: nonecheck=False
#cython: language_level=3

# Third-party imports
import numpy as np

# Third-party imports
cimport numpy as np

# Third-party imports
from scipy.ndimage import gaussian_filter


cpdef baseline_curve_(np.ndarray[ndim=1, dtype=np.float64_t] data, int window):  # noqa
    cdef:
        int i
        int length = data.shape[0]  # noqa
        int start, end
        int[:] mins = np.zeros(length, dtype=np.int32)
    
    window = abs(window)
    for i in range(length):
        start = max([0, i - window])
        end = min([i + window, length])
        mins[i] = np.amin(data[start : end])
    background = gaussian_filter(mins, window * 2)
    return data - background


cpdef nonlinear_axis(start: float, end: float, res: float):
    cdef:
        float _res = float(res)
        float i = start
        list axis = [start]
    i += i / _res
    while i < end:
        axis.append(i)
        i += i / _res
    return np.array(axis)


def linear_interpolation(x1: float, x2: float, x:float):
    return float(x - x1) / float(x2 - x1)