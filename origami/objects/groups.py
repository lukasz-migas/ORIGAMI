# Standard library imports
from typing import Any
from typing import Dict
from typing import List
from typing import Union

# Third-party imports
import numpy as np

# Local imports
from origami.processing import spectra
from origami.config.config import CONFIG
from origami.objects.container import ContainerBase
from origami.objects.containers import DataObject
from origami.objects.containers import MassSpectrumObject


class DataGroup(ContainerBase):

    _resample = True
    _x_min = None
    _x_max = None
    _x = None
    _y_sum = None
    _y_mean = None
    _processing = None
    _names = None

    def __init__(
        self,
        data_objects: Union[Dict, List[DataObject]],
        x_label="",
        y_label="",
        x_label_options=None,
        y_label_options=None,
        metadata=None,
        extra_data=None,
        **kwargs,
    ):
        super().__init__(
            extra_data,
            metadata,
            x_label=x_label,
            y_label=y_label,
            x_label_options=x_label_options,
            y_label_options=y_label_options,
        )
        self._data_objs = data_objects
        self._next: int = -1
        self._is_dict = isinstance(data_objects, dict)

        self.check()

    def __repr__(self):
        return f"{self.__class__.__name__}<no. objects={self.n_objects}; resample={self.need_resample}>"

    def __iter__(self):
        return self

    def __next__(self):
        self._next += 1

        if self._next < self.n_objects:
            return self[self._next]
            # name = self._next if not self._is_dict else self.names[self._next]
            # return self._data_objs[name]

        # reset iterator
        self._next = -1
        raise StopIteration

    def __getitem__(self, item):
        """Get item"""
        if isinstance(item, int):
            item = item if not self._is_dict else self.names[item]
        else:
            if not self._is_dict:
                raise ValueError("Cannot retrieve item by name if data was provided as a dictionary")

        return self._data_objs[item]

    @property
    def names(self):
        if self._names is None:
            self._names = range(self.n_objects) if not self._is_dict else list(self._data_objs.keys())
        return self._names

    @property
    def n_objects(self):
        """Return number of objects in the group container"""
        return len(self._data_objs)

    @property
    def need_resample(self):
        raise NotImplementedError("Must implement method")

    @property
    def processing(self):
        return self._processing

    # def get(self, idx: int=None, name: str=None):
    #     """Retrieve one item by its name / index"""

    def add_processing_step(self, method: str, processing: Any):
        """Sets all processing processing associated with this fitter than can later be exported as a json file"""
        if self._processing is None:
            self._processing = dict()
        old_processing = self._processing.pop(method, None)
        self._processing[method] = processing

        # checks whether previous processing parameters are the same as what is being updated - if they are the same
        # no action needs to be taken, however, if they are different, all currently preset parameter MUST BE reset
        # otherwise you might get different results!
        if old_processing != processing:
            self.reset()

    def get_processing_step(self, method):
        """Retrieves processing steps previously carried out on the dataset"""
        if self._processing is None:
            self._processing = dict()
        return self._processing.get(method, dict())

    def mean(self):
        raise NotImplementedError("Must implement method")

    def sum(self):
        raise NotImplementedError("Must implement method")

    def resample(self):
        raise NotImplementedError("Must implement method")

    def reset(self):
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
        assert isinstance(self._data_objs, (list, dict)), "Group data should be provided in a list or dict object"
        assert len(self._data_objs) >= 1, "Group should have 1 or more elements"
        for data_obj in self:
            assert isinstance(data_obj, DataObject), "Objects must be of the instance `DataObject`"


# class HeatmapGroup(DataGroup):
#     def __init__(
#         self,
#         data_objects: Union[Dict, List[DataObject]],
#         x_label="",
#         y_label="",
#         x_label_options=None,
#         y_label_options=None,
#         metadata=None,
#         extra_data=None,
#         **kwargs,
#     ):
#         super().__init__(
#             data_objects,
#             x_label=x_label,
#             y_label=y_label,
#             metadata=metadata,
#             extra_data=extra_data,
#             x_label_options=x_label_options,
#             y_label_options=y_label_options,
#             **kwargs,
#         )
#
#     @property
#     def need_resample(self):
#         return
#
#     def mean(self):
#         pass
#
#     def sum(self):
#         pass
#
#     def resample(self):
#         pass
#
#     def reset(self):
#         pass
#
#     def to_csv(self, *args, **kwargs):
#         pass
#
#     def to_dict(self):
#         pass
#
#     def to_zarr(self):
#         pass


class SpectrumGroup(DataGroup):
    def __init__(
        self,
        data_objects: Union[Dict, List[DataObject]],
        x_label="",
        y_label="",
        x_label_options=None,
        y_label_options=None,
        metadata=None,
        extra_data=None,
        **kwargs,
    ):
        super().__init__(
            data_objects,
            x_label=x_label,
            y_label=y_label,
            metadata=metadata,
            extra_data=extra_data,
            x_label_options=x_label_options,
            y_label_options=y_label_options,
            **kwargs,
        )

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

    @property
    def x_limit(self):
        return list(self.get_x_range())

    @property
    def need_resample(self):
        self.get_x_range()
        return self._resample

    def get_x_range(self):
        """Calculate data extents"""

        x_min = self._x_min
        x_max = self._x_max

        if not x_min or not x_max:

            x_min_list, x_max_list = [], []
            for obj in self:
                x_min_list.append(obj.x[0])
                x_max_list.append(obj.x[-1])

            if len(np.unique(x_min_list)) == 1 and len(np.unique(x_max_list)) == 1:
                self._resample = False

            self._x_min = np.min(x_min_list)
            self._x_max = np.max(x_max_list)

        return self._x_min, self._x_max

    def reset(self):
        """Resets class data"""
        self._x = None
        self._y_sum = None
        self._y_mean = None
        self._x_min = None
        self._x_max = None

    def mean(self, x_min=None, x_max=None, bin_size=None, linearization_mode=None, auto_range=False, **kwargs):
        raise NotImplementedError("Must implement method")

    def _mean(self, x_min=None, x_max=None, bin_size=None, linearization_mode=None, auto_range=False, **kwargs):
        x, ys = self.resample(x_min, x_max, bin_size, linearization_mode, auto_range)
        y_mean = ys.mean(axis=0)
        return x, y_mean

    def sum(self, x_min=None, x_max=None, bin_size=None, linearization_mode=None, auto_range=False, **kwargs):
        raise NotImplementedError("Must implement method")

    def _sum(self, x_min=None, x_max=None, bin_size=None, linearization_mode=None, auto_range=False, **kwargs):
        x, ys = self.resample(x_min, x_max, bin_size, linearization_mode, auto_range)
        y_sum = ys.sum(axis=0, dtype=np.float64)
        return x, y_sum

    def resample(self, x_min=None, x_max=None, bin_size=None, linearization_mode=None, auto_range=False, **kwargs):
        """Resample dataset so it has consistent size and shape"""

        def _resample_obj():
            """If array needs resampling, it will be resampled, otherwise it will be returned as is"""
            if self.need_resample:
                _x, _y = spectra.linearize_data(
                    obj.x,
                    obj.y,
                    x_min=x_min,
                    x_max=x_max,
                    linearize_method=linearization_mode,
                    bin_size=bin_size,
                    auto_range=False,
                )
            else:
                _x, _y = obj.x, obj.y
            return _x, _y

        # retrieve previous processing parameters
        prev_processing = self.get_processing_step("resample")

        # specify x-axis limits
        _x_min, _x_max = self.get_x_range()

        # specify processing processing
        if x_min is None:
            x_min = prev_processing.get("x_min", _x_min)

        if x_max is None:
            x_max = prev_processing.get("x_max", _x_max)

        if not linearization_mode:
            linearization_mode = prev_processing.get("linearize_method", CONFIG.ms_linearize_method)

        if not bin_size:
            bin_size = prev_processing.get("bin_size", CONFIG.ms_linearize_mz_bin_size)

        # pre-calculate data for single data object to be able to instantiate numpy array for each spectrum
        obj = self[0]
        x, y = _resample_obj()

        # preset array
        ys = np.zeros((self.n_objects, len(x)), dtype=np.float32)
        ys[0] = y
        for i in range(1, self.n_objects):
            obj = self[i]
            # for i, obj in enumerate(self._data_objs[1::], start=1):
            _, y = _resample_obj()
            ys[i] = y

        if self._resample:
            self.add_processing_step(
                "resample",
                dict(
                    x_min=x_min,
                    x_max=x_max,
                    bin_size=bin_size,
                    linearization_mode=linearization_mode,
                    auto_range=auto_range,
                ),
            )

        return x, ys

    def to_csv(self, *args, **kwargs):
        pass

    def to_dict(self):
        data = {
            "x": self.x,
            "y": self.y,
            "y_sum": self.y_sum,
            "y_mean": self.y_mean,
            "x_limit": self.x_limit,
            "x_label": self.x_label,
            "y_label": self.y_label,
            "processing_steps": self.processing,
            **self._metadata,
            **self._extra_data,
        }
        return data

    def to_zarr(self):
        """Outputs data to dictionary of `data` and `attributes`"""
        attrs = {"class": self._cls}
        return dict(), attrs


class MassSpectrumGroup(SpectrumGroup):
    def __init__(self, data_objects, metadata=None, extra_data=None, x_label="m/z (Da)", y_label="Intensity", **kwargs):
        super().__init__(
            data_objects, x_label=x_label, y_label=y_label, metadata=metadata, extra_data=extra_data, **kwargs
        )

    def mean(self, x_min=None, x_max=None, bin_size=None, linearization_mode=None, auto_range=False, **kwargs):
        x, y = self._mean(x_min, x_max, bin_size, linearization_mode, auto_range, **kwargs)
        return MassSpectrumObject(x, y)

    def sum(self, x_min=None, x_max=None, bin_size=None, linearization_mode=None, auto_range=False, **kwargs):
        x, y = self._sum(x_min, x_max, bin_size, linearization_mode, auto_range, **kwargs)
        return MassSpectrumObject(x, y)
