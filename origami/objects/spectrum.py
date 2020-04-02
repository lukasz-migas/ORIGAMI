# Third-party imports
import numpy as np

# Local imports
from origami.utils.ranges import get_min_max


class DataObject:
    def __init__(self):
        pass

    def save_to_hdf5(self):
        pass

    def save_to_csv(self):
        pass

    def save_to_json(self):
        pass


class SpectrumObject:
    def __init__(self, x, y, x_label: str = "m/z (Da)", y_label: str = "Intensity"):
        self._x = x
        self._y = y
        self._x_label = x_label
        self._y_label = y_label

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    @property
    def x_limit(self):
        return get_min_max(self.x)


class HeatmapObject:
    def __init__(self, array, x=None, y=None, x_label: str = "x-axis", y_label: str = "y-axis"):
        self._array = array
        self._x = x
        self._y = y
        self._x_label = x_label
        self._y_label = y_label

    @property
    def x(self):
        if self._x is None:
            self._x = np.arange(1, self.shape[1])
        return self._x

    @property
    def y(self):
        if self._y is None:
            self._y = np.arange(1, self.shape[0])
        return self._y

    @property
    def array(self):
        return self._array

    @property
    def shape(self):
        return self._array.shape
