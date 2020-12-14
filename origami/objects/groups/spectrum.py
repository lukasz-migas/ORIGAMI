"""Spectrum groups"""
# Standard library imports
from typing import Dict
from typing import List
from typing import Union

# Third-party imports
import numpy as np

# Local imports
from origami.processing import spectra
from origami.config.config import CONFIG
from origami.objects.containers import DataObject
from origami.objects.containers import MobilogramObject
from origami.objects.containers import ChromatogramObject
from origami.objects.containers import MassSpectrumObject
from origami.objects.groups.base import DataGroup


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
    def array(self):
        """Returns array of y-axes"""
        ys = self.ys
        return np.asarray(ys).T

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

    def resample(
        self, x_min=None, x_max=None, bin_size=None, linearization_mode=None, auto_range=False, ppm=None, **kwargs
    ):
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
                    ppm=ppm,
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
