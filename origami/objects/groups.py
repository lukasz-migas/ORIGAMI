"""Group objects"""
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
from origami.config.environment import ENV
from origami.objects.containers import DataObject
from origami.objects.containers import MobilogramObject
from origami.objects.containers import ChromatogramObject
from origami.objects.containers import MassSpectrumObject
from origami.objects.containers.utilities import XYAxesLabelAlternatives


class DataObjectsContainer:
    """Container class for DataObjects"""

    def __init__(self, data_objects: Union[Dict[str, DataObject], Dict[str, str], List[DataObject], List[List[str]]]):
        self._data_objs = data_objects
        self._names = None
        self._is_dict = isinstance(data_objects, dict)
        self._is_loaded = self.is_loaded()
        self.check()

    def __getitem__(self, item):
        """Retrieve object from the internal store"""
        if isinstance(item, int):
            item = item if not self._is_dict else self.names[item]
        else:
            if not self._is_dict:
                raise ValueError("Cannot retrieve item by name if data was provided as a dictionary")
        value = self._data_objs[item]

        if isinstance(value, list):
            document = ENV.on_get_document(value[0])
            value = document[value[1], True]
        return value

    def is_loaded(self):
        """Checks whether items in the `data_objs` attribute are DataObjects or strings"""
        if self._is_dict:
            for value in self._data_objs.values():
                if isinstance(value, str):
                    return False
        else:
            for value in self._data_objs:
                if isinstance(value, str):
                    return False
        return True

    @property
    def names(self):
        """Returns the list of object names"""
        if self._names is None:
            self._names = range(self.n_objects) if not self._is_dict else list(self._data_objs.keys())
        return self._names

    @property
    def n_objects(self):
        """Return number of objects in the group container"""
        return len(self._data_objs)

    def check(self):
        """Ensure correct data was added to the data group"""
        if not isinstance(self._data_objs, (list, dict)):
            raise ValueError("Group data should be provided in a list or dict object")
        for data_obj in self:
            if not isinstance(data_obj, (DataObject, list)):
                raise ValueError("Objects must be of the instance `DataObject`")


class DataGroup(ContainerBase):
    """Group object for data operations"""

    _resample = True
    _x_min = None
    _x_max = None
    _x = None
    _y_sum = None
    _y_mean = None
    _processing = None

    def __init__(
        self,
        data_objects: Union[Dict[str, DataObject], Dict[str, str], List[DataObject], List[List[str]]],
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
        self._data_objs = DataObjectsContainer(data_objects)
        self._next: int = -1
        self._is_dict = isinstance(data_objects, dict)

    def __repr__(self):
        return f"{self.__class__.__name__}<no. objects={self.n_objects}; resample={self.need_resample}>"

    def __iter__(self):
        return self

    def __next__(self):
        self._next += 1

        if self._next < self.n_objects:
            return self[self._next]
        self._next = -1  # reset iterator
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
        """Returns the list of object names"""
        return self._data_objs.names

    @property
    def n_objects(self):
        """Return number of objects in the group container"""
        return self._data_objs.n_objects

    @property
    def need_resample(self):
        """Flag to indicate whether data needs to be resampled"""
        raise NotImplementedError("Must implement method")

    @property
    def processing(self):
        """Returns processing steps"""
        return self._processing

    @property
    def xs(self):
        """Return list of x-axes"""
        return [data_obj.x for data_obj in self]

    @property
    def ys(self):
        """Return list of y-axes"""
        return [data_obj.y for data_obj in self]

    @property
    def x_labels(self):
        """Return list of x-labels"""
        return [data_obj.x_label for data_obj in self]

    @property
    def y_labels(self):
        """Return list of y-labels"""
        return [data_obj.y_label for data_obj in self]

    @property
    def shapes(self):
        """Return list of shapes"""
        return [data_obj.shape for data_obj in self]

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
        """Mean array"""
        raise NotImplementedError("Must implement method")

    def sum(self):
        """Sum array"""
        raise NotImplementedError("Must implement method")

    def resample(self):
        """Resample"""
        raise NotImplementedError("Must implement method")

    def reset(self):
        """Reset"""
        raise NotImplementedError("Must implement method")

    def to_csv(self, *args, **kwargs):
        """Save data in CSV format"""
        raise ValueError("Cannot export data in CSV format")

    def to_dict(self):
        """Export data in dictionary format"""
        raise ValueError("Cannot export data in dict format")

    def to_zarr(self):
        """Outputs data to dictionary of `data` and `attributes`"""
        attrs = {"class": self._cls, **self._metadata}
        return dict(), attrs

    def change_x_label(self, to_label: str):
        """Change x-axis label and values"""
        if to_label in self.x_label_options:
            for data_obj in self:
                data_obj.change_x_label(to_label)
        return self

    def change_y_label(self, to_label: str):
        """Change x-axis label and values"""
        if to_label in self.y_label_options:
            for data_obj in self:
                data_obj.change_y_label(to_label)
        return self

    def validate_x_labels(self):
        """Validate that x-axis labels are the same or similar"""
        labels = set(self.x_labels)
        if len(labels) == 1:
            return True
        _labels = []
        for label in labels:
            _labels.append(XYAxesLabelAlternatives.get(label))
        if len(_labels) == 1:
            return True
        return False

    def validate_y_labels(self):
        """Validate that y-axis labels are the same or similar"""
        labels = set(self.y_labels)
        if len(labels) == 1:
            return True
        _labels = []
        for label in labels:
            _labels.append(XYAxesLabelAlternatives.get(label))
        if len(_labels) == 1:
            return True
        return False

    def validate_shape(self):
        """Validate that shape of the object is the same"""
        shapes = set(self.shapes)
        if len(shapes) == 1:
            return True
        return False


class SpectrumGroup(DataGroup):
    """Spectrum group object"""

    def __init__(
        self,
        data_objects: Union[Dict[str, DataObject], Dict[str, str], List[DataObject], List[List[str]]],
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
        """Returns x-axis"""
        if self._x is None:
            self._x, self._y_sum = self.sum()
        return self._x

    @property
    def y(self):
        """Returns summed intensity array"""
        return self.y_sum

    @property
    def y_sum(self):
        """Computes summed intensity array"""
        if self._y_sum is None:
            self._x, self._y_sum = self.sum()
        return self._y_sum

    @property
    def y_mean(self):
        """Computes mean intensity array"""
        if self._y_mean is None:
            self._x, self._y_mean = self.mean()
        return self._y_mean

    @property
    def x_limit(self):
        """Returns x-axis limits"""
        return list(self.get_x_range())

    @property
    def need_resample(self):
        """Checks whether need to resample"""
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
        """Generate mean spectrum"""
        raise NotImplementedError("Must implement method")

    def _mean(self, x_min=None, x_max=None, bin_size=None, linearization_mode=None, auto_range=False, **kwargs):  # noqa
        x, ys = self.resample(x_min, x_max, bin_size, linearization_mode, auto_range)
        y_mean = ys.mean(axis=0)
        return x, y_mean

    def sum(self, x_min=None, x_max=None, bin_size=None, linearization_mode=None, auto_range=False, **kwargs):
        """Generate summed spectrum"""
        raise NotImplementedError("Must implement method")

    def _sum(self, x_min=None, x_max=None, bin_size=None, linearization_mode=None, auto_range=False, **kwargs):  # noqa
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

    def to_zarr(self):
        """Outputs data to dictionary of `data` and `attributes`"""
        attrs = {"class": self._cls, **self._metadata}
        return dict(), attrs


class MassSpectrumGroup(SpectrumGroup):
    """Mass spectrum group"""

    def __init__(self, data_objects, metadata=None, extra_data=None, x_label="m/z (Da)", y_label="Intensity", **kwargs):
        super().__init__(
            data_objects, x_label=x_label, y_label=y_label, metadata=metadata, extra_data=extra_data, **kwargs
        )

    def mean(self, x_min=None, x_max=None, bin_size=None, linearization_mode=None, auto_range=False, **kwargs):
        """Create average spectrum"""
        x, y = self._mean(x_min, x_max, bin_size, linearization_mode, auto_range, **kwargs)
        return MassSpectrumObject(x, y)

    def sum(self, x_min=None, x_max=None, bin_size=None, linearization_mode=None, auto_range=False, **kwargs):
        """Create summed spectrum"""
        x, y = self._sum(x_min, x_max, bin_size, linearization_mode, auto_range, **kwargs)
        return MassSpectrumObject(x, y)


class ChromatogramGroup(SpectrumGroup):
    """Chromatogram group"""

    def __init__(self, data_objects, metadata=None, extra_data=None, x_label="Scans", y_label="Intensity", **kwargs):
        super().__init__(
            data_objects,
            x_label=x_label,
            y_label=y_label,
            x_label_options=[
                "Scans",
                "Time (mins)",
                "Retention time (mins)",
                "Collision Voltage (V)",
                "Activation Voltage (V)",
                "Activation Energy (V)",
                "Lab Frame Energy (eV)",
                "Activation Voltage (eV)",
                "Activation Energy (eV)",
            ],
            metadata=metadata,
            extra_data=extra_data,
            **kwargs,
        )

    def mean(self, x_min=None, x_max=None, bin_size=None, linearization_mode=None, auto_range=False, **kwargs):
        """Create average chromatogram"""
        x, y = self._mean(x_min, x_max, bin_size, linearization_mode, auto_range, **kwargs)
        return ChromatogramObject(x, y)

    def sum(self, x_min=None, x_max=None, bin_size=None, linearization_mode=None, auto_range=False, **kwargs):
        """Create summed chromatogram"""
        x, y = self._sum(x_min, x_max, bin_size, linearization_mode, auto_range, **kwargs)
        return ChromatogramObject(x, y)


class MobilogramGroup(SpectrumGroup):
    """Mobilogram group"""

    def __init__(
        self, data_objects, metadata=None, extra_data=None, x_label="Drift time (bins)", y_label="Intensity", **kwargs
    ):
        super().__init__(
            data_objects,
            x_label=x_label,
            y_label=y_label,
            x_label_options=[
                "Drift time (bins)",
                "Drift time (ms)",
                "Arrival time (ms)",
                "Collision Cross Section (Å²)",
                "CCS (Å²)",
            ],
            metadata=metadata,
            extra_data=extra_data,
            **kwargs,
        )

    def mean(self, x_min=None, x_max=None, bin_size=None, linearization_mode=None, auto_range=False, **kwargs):
        """Create average mobilogram"""
        x, y = self._mean(x_min, x_max, bin_size, linearization_mode, auto_range, **kwargs)
        return MobilogramObject(x, y)

    def sum(self, x_min=None, x_max=None, bin_size=None, linearization_mode=None, auto_range=False, **kwargs):
        """Create summed mobilogram"""
        x, y = self._sum(x_min, x_max, bin_size, linearization_mode, auto_range, **kwargs)
        return MobilogramObject(x, y)


class HeatmapGroup(DataGroup):
    """Heatmap group object"""

    def __init__(
        self,
        data_objects: Union[Dict[str, DataObject], Dict[str, str], List[DataObject], List[List[str]]],
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
    def arrays(self):
        """Return list of arrays"""
        return [data_obj.array for data_obj in self]

    @property
    def need_resample(self):
        return False

    def mean(self):
        pass

    def sum(self):
        pass

    def resample(self):
        pass

    def reset(self):
        pass


class IonHeatmapGroup(HeatmapGroup):
    """Ion heatmap group"""

    def __init__(
        self, data_objects, metadata=None, extra_data=None, x_label="Scans", y_label="Drift time (bins)", **kwargs
    ):
        super().__init__(
            data_objects,
            x_label=x_label,
            y_label=y_label,
            x_label_options=[
                "Scans",
                "Time (mins)",
                "Retention time (mins)",
                "Collision Voltage (V)",
                "Activation Voltage (V)",
                "Activation Energy (V)",
                "Lab Frame Energy (eV)",
                "Activation Voltage (eV)",
                "Activation Energy (eV)",
            ],
            y_label_options=[
                "Drift time (bins)",
                "Drift time (ms)",
                "Arrival time (ms)",
                "Collision Cross Section (Å²)",
                "CCS (Å²)",
            ],
            metadata=metadata,
            extra_data=extra_data,
            **kwargs,
        )
