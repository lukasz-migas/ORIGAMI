# Standard library imports
from typing import List

# Third-party imports
import numpy as np

# Local imports
from origami.processing import spectra
from origami.config.config import CONFIG
from origami.objects.containers import DataObject


class DataGroup:

    _x_min = None
    _x_max = None
    _x = None
    _y_sum = None
    _y_mean = None

    def __init__(self, data_objects: List[DataObject]):
        self._data_objs = data_objects

        self.check()

    def __repr__(self):
        return f"{self.__class__.__name__}<no. objects={self.n_objects}>"

    @property
    def n_objects(self):
        return len(self._data_objs)

    def mean(self):
        raise NotImplementedError("Must implement method")

    def sum(self):
        raise NotImplementedError("Must implement method")

    def resample(self):
        raise NotImplementedError("Must implement method")

    def to_csv(self, *args, **kwargs):
        """Outputs data to .csv file"""
        raise NotImplementedError("Must implement method")

    def to_dict(self):
        """Outputs data ina dictionary format"""
        raise NotImplementedError("Must implement method")

    def to_zarr(self):
        """Outputs data to dictionary of `data` and `attributes`"""
        raise NotImplementedError("Must implement method")

    def check(self):
        """Ensure correct data was added to the data group"""
        assert isinstance(self._data_objs, list), "Group data should be provided in a list object"
        assert len(self._data_objs) >= 1, "Group should have 1 or more elements"
        for do in self._data_objs:
            assert isinstance(do, DataObject), "Objects must be of the instance `DataObject`"


class SpectrumGroup(DataGroup):
    def __init__(self, data_objects: List[DataObject]):
        super().__init__(data_objects)

    @property
    def x(self):
        if self._x is None:
            self._x, self._y_sum = self.sum()
        return self._x

    @property
    def y(self):
        return self.y_sum

    @property
    def y_sum(self):
        if self._y_sum is None:
            self._x, self._y_sum = self.sum()
        return self._y_sum

    @property
    def y_mean(self):
        if self._y_mean is None:
            self._x, self._y_mean = self.mean()
        return self._y_mean

    def get_x_range(self):
        """Calculate data extents"""

        x_min = self._x_min
        x_max = self._x_max

        if not x_min or not x_max:

            x_mins, x_maxs = [], []
            for obj in self._data_objs:
                x_mins.append(obj.x[0])
                x_maxs.append(obj.x[-1])

            self._x_min = np.min(x_mins)
            self._x_max = np.max(x_maxs)

        return self._x_min, self._x_max

    def reset(self):
        self._x = None
        self._y_sum = None
        self._y_mean = None
        self._x_min = None
        self._x_max = None

    def mean(self, x_min=None, x_max=None, bin_size=None, linearization_mode=None, auto_range=False):
        x, ys = self.resample(x_min, x_max, bin_size, linearization_mode, auto_range)
        y_mean = ys.mean(axis=0)
        return x, y_mean

    def sum(self, x_min=None, x_max=None, bin_size=None, linearization_mode=None, auto_range=False):
        x, ys = self.resample(x_min, x_max, bin_size, linearization_mode, auto_range)
        y_sum = ys.sum(axis=0, dtype=np.float64)
        return x, y_sum

    def resample(self, x_min=None, x_max=None, bin_size=None, linearization_mode=None, auto_range=False):
        """Resample dataset so it has consistent size and shape"""
        # specify x-axis limits
        _x_min, _x_max = self.get_x_range()
        x_min = x_min if x_min else _x_min
        x_max = x_max if x_max else _x_max

        # specify processing parameters
        if not linearization_mode:
            linearization_mode = CONFIG.ms_linearization_mode

        if not bin_size:
            bin_size = CONFIG.ms_mzBinSize

        # pre-calculate data for single data object to be able to instantiate numpy array for each spectrum
        obj = self._data_objs[0]
        x, y = spectra.linearize_data(
            obj.x,
            obj.y,
            x_min=x_min,
            x_max=x_max,
            linearization_mode=linearization_mode,
            bin_size=bin_size,
            auto_range=False,
        )

        # preset array
        ys = np.zeros((self.n_objects, len(x)), dtype=np.float32)
        ys[0] = y
        for i, obj in enumerate(self._data_objs[1::], start=1):
            _, y = spectra.linearize_data(
                obj.x,
                obj.y,
                x_min=x_min,
                x_max=x_max,
                linearization_mode=linearization_mode,
                bin_size=bin_size,
                auto_range=False,
                x_bin=x,
            )
            ys[i] = y

        return x, ys

    def to_csv(self, *args, **kwargs):
        pass

    def to_dict(self):
        pass

    def to_zarr(self):
        pass
