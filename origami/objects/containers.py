# Standard library imports
from typing import List
from typing import Union
from typing import Optional

# Third-party imports
import numpy as np
from zarr import Group

# Local imports
from origami.utils.ranges import get_min_max
from origami.objects.container import ContainerBase
from origami.processing.heatmap import equalize_heatmap_spacing
from origami.processing.spectra import baseline_1D
from origami.processing.spectra import normalize_1D
from origami.processing.spectra import linearize_data

# TODO: add x/y-axis converters to easily switch between labels


def get_fmt(*arrays):
    """Retrieve appropriate numpy format based on the data"""
    fmts = []
    for array in arrays:
        if np.issubdtype(array.dtype, np.integer):
            fmts.append("%d")
        elif np.issubdtype(array.dtype, np.float32):
            fmts.append("%.4f")
        else:
            fmts.append("%.6f")
    return fmts


class DataObject(ContainerBase):
    # data attributes
    _x_limit = None
    _y_limit = None

    def __init__(
        self,
        name,
        x,
        y,
        x_label="",
        y_label="",
        x_label_options=None,
        y_label_options=None,
        metadata=None,
        extra_data=None,
        **kwargs,
    ):
        """Base object for all other container objects

        Parameters
        ----------
        name : str
            name of the object so its easily searchable
        x : np.ndarray
            x-axis array
        y : np.ndarray
            y-axis array
        x_label : str
            x-axis label
        y_label : str
            y-axis label
        x_label_options : List[str]
            list of alternative x-axis labels
        y_label_options : List[str]
            list of alternative y-axis labels
        extra_data : dict
            dictionary containing additional data that should be exported in zarr container
        metadata : dict
            dictionary containing additional metadata that should be exported in zarr container
        """
        super().__init__(
            extra_data,
            metadata,
            x_label=x_label,
            y_label=y_label,
            x_label_options=x_label_options,
            y_label_options=y_label_options,
        )
        # settable attributes
        self.name = name
        self._x = x
        self._y = y
        self.check()

        self.check_kwargs(kwargs)

    def __repr__(self):
        return f"{self.__class__.__name__}<x-label={self.x_label}; y-label={self.y_label}; shape={self.shape}>"

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    @property
    def x_limit(self):
        if not self._x_limit:
            self._x_limit = get_min_max(self.x)
        return self._x_limit

    @property
    def y_limit(self):
        if not self._y_limit:
            self._y_limit = get_min_max(self.x)
        return self._y_limit

    @property
    def shape(self):
        return self.x.shape

    def check_kwargs(self, kwargs):
        """Checks whether kwargs have been fully processed"""
        if kwargs:
            for key, value in kwargs.items():
                if isinstance(value, np.ndarray):
                    self._extra_data[key] = value
                elif isinstance(value, (int, float, list, tuple, dict)):
                    self._metadata[key] = value

    def to_csv(self, *args, **kwargs):
        raise NotImplementedError("Must implement method")

    def to_dict(self):
        raise NotImplementedError("Must implement method")

    def to_zarr(self):
        """Outputs data to dictionary of `data` and `attributes`"""
        raise NotImplementedError("Must implement method")

    def check(self):
        raise NotImplementedError("Must implement method")


class SpectrumObject(DataObject):
    def __init__(self, x, y, x_label: str, y_label: str, name: str, metadata: dict, extra_data: dict, **kwargs):
        super().__init__(name, x, y, x_label, y_label, metadata=metadata, extra_data=extra_data, **kwargs)

    @property
    def x_bin(self):
        return np.arange(len(self.x))

    def to_dict(self):
        """Outputs data to dictionary"""
        data = {
            "x": self.x,
            "y": self.y,
            "x_limit": self.x_limit,
            "x_label": self.x_label,
            "y_label": self.y_label,
            **self._metadata,
            **self._extra_data,
        }
        return data

    def to_zarr(self):
        """Outputs data to dictionary of `data` and `attributes`"""
        data = {"x": self.x, "y": self.y, **self._extra_data}
        attrs = {
            "class": self._cls,
            "x_limit": self.x_limit,
            "x_label": self.x_label,
            "y_label": self.y_label,
            **self._metadata,
        }
        return data, attrs

    def to_csv(self, path, *args, **kwargs):
        """Export data in a csv/txt format"""
        x = self.x
        y = self.y
        if kwargs.get("remove_zeros", self.options.get("remove_zeros", False)):
            index = np.where((self.x == 0) | (self.y == 0))
            x = x[index]
            y = y[index]

        # get metadata
        fmt = get_fmt(x, y)
        delimiter = kwargs.get("delimiter", ",")
        header = f"{delimiter}".join([self.x_label, self.y_label])
        np.savetxt(path, np.c_[x, y], delimiter=delimiter, fmt=fmt, header=header)

    def check(self):
        """Checks whether the provided data has the same size and shape"""
        if len(self._x) != len(self._y):
            raise ValueError("x and y axis data must have the same length")
        if not isinstance(self._metadata, dict):
            self._metadata = dict()

    def normalize(self, copy: bool = False):
        """Normalize spectrum to 1"""
        self._y = normalize_1D(self.y)


class MassSpectrumObject(SpectrumObject):
    def __init__(
        self, x, y, name: str = "", metadata=None, extra_data=None, x_label="m/z (Da)", y_label="Intensity", **kwargs
    ):
        super().__init__(
            x, y, x_label=x_label, y_label=y_label, name=name, metadata=metadata, extra_data=extra_data, **kwargs
        )

        # set default options
        self.options["remove_zeros"] = True

    def linearize(self, copy: bool = False, **kwargs):
        """Linearize spectrum to common m/z axis"""
        x, y = linearize_data(self.x, self.y, **kwargs)
        self._x, self._y = x, y
        # self.set_metadata(dict(linearize=kwargs))

    def baseline(self, copy: bool = False, **kwargs):
        """Remove baseline from the mass spectrum"""
        y = baseline_1D(self.y, mode=kwargs.get("baseline_method"), **kwargs)
        self._y = y
        # self.set_metadata(dict(baseline=kwargs))


class ChromatogramObject(SpectrumObject):
    def __init__(
        self, x, y, name: str = "", metadata=None, extra_data=None, x_label="Scans", y_label="Intensity", **kwargs
    ):
        """
        Additional data can be stored in the `extra_data` dictionary. The convention should be:
            data that is most commonly used/displayed should be stored under the x/y attributes
            alternative x-axis should be stored in the `extra_data` dict. If the extra data is
            scans, then store it under `x_bin` and if its in time/minutes, store it under `x_min`.

        Data keys:
            x : x-axis data most commonly used
            y : y-axis data most commonly used
            x_bin : x-axis data in scans/bins
            x_min : x-axis data in minutes/time
            """
        super().__init__(
            x,
            y,
            x_label=x_label,
            y_label=y_label,
            name=name,
            x_label_options=["Scans", "Time (mins)", "Retention time (mins)"],
            metadata=metadata,
            extra_data=extra_data,
            **kwargs,
        )

    def to_scans(self, scan_time: Optional[Union[int, float]] = None):
        """Return x-axis in scans"""
        if scan_time is None:
            if "x_bin" in self._extra_data:
                return self._extra_data["x_bin"]
            return self.x_bin
        if self.x_label == "Scans":
            return self.x
        return np.round(self.x / scan_time).astype(np.int32)

    def to_min(self, scan_time: Optional[Union[int, float]] = None):
        """Return x-axis in minutes"""
        if scan_time is None:
            if "x_min" in self._extra_data:
                return self._extra_data["x_min"]
            raise ValueError("Could not process the request")
        if self.x_label == "Scans":
            return self.x * scan_time
        return self.x


class MobilogramObject(SpectrumObject):
    def __init__(
        self,
        x,
        y,
        name: str = "",
        metadata=None,
        extra_data=None,
        x_label="Drift time (bins)",
        y_label="Intensity",
        **kwargs,
    ):
        super().__init__(
            x,
            y,
            x_label=x_label,
            y_label=y_label,
            name=name,
            x_label_options=["Drift time (bins)", "Arrival time (ms)", "Drift time (ms)"],
            metadata=metadata,
            extra_data=extra_data,
            **kwargs,
        )

    def to_bins(self, pusher_freq: Optional[float] = None):
        """Converts x-axis to bins"""

    def to_ms(self, pusher_freq: Optional[float] = None):
        """Converts x-axis to milliseconds"""


class HeatmapObject(DataObject):
    def __init__(
        self,
        array: np.ndarray,
        name: str,
        x=None,
        y=None,
        xy=None,
        yy=None,
        x_label: str = "x-axis",
        y_label: str = "y-axis",
        metadata=None,
        extra_data=None,
        **kwargs,
    ):
        super().__init__(name, x, y, x_label, y_label, metadata=metadata, extra_data=extra_data, **kwargs)
        self._array = array
        self._xy = xy
        self._yy = yy

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
    def xy(self):
        if self._xy is None:
            self._xy = self.array.sum(axis=0)
        return self._xy

    @property
    def yy(self):
        if self._yy is None:
            self._yy = self.array.sum(axis=1)
        return self._yy

    @property
    def array(self):
        return self._array

    @property
    def shape(self):
        return self._array.shape

    def to_dict(self):
        return {
            "x": self.x,
            "y": self.y,
            "array": self.array,
            "xy": self.xy,
            "yy": self.yy,
            "x_label": self.x_label,
            "y_label": self.y_label,
            **self._metadata,
            **self._extra_data,
        }

    def to_zarr(self):
        """Outputs data to dictionary of `data` and `attributes`"""
        data = {"x": self.x, "y": self.y, "array": self.array, "xy": self.xy, "yy": self.yy, **self._extra_data}
        attrs = {"class": self._cls, "x_label": self.x_label, "y_label": self.y_label, **self._metadata}
        return data, attrs

    def to_csv(self, *args, **kwargs):
        """Export data in a csv/txt format"""
        pass

    def check(self):
        pass

    def downsample(self, rate: int = 5, mode: str = "Sub-sample"):
        """Return data at a downsampled rate"""


class IonHeatmapObject(HeatmapObject):
    def __init__(
        self,
        array,
        x,
        y,
        xy=None,
        yy=None,
        name: str = "",
        metadata=None,
        extra_data=None,
        x_label="Scans",
        y_label="Drift time (bins)",
        **kwargs,
    ):
        super().__init__(
            array,
            name,
            x=x,
            y=y,
            xy=xy,
            yy=yy,
            x_label=x_label,
            y_label=y_label,
            x_label_options=["Scans", "Retention time (mins)"],
            metadata=metadata,
            extra_data=extra_data,
            **kwargs,
        )


class StitchIonHeatmapObject(IonHeatmapObject):
    def __init__(
        self,
        data_objects: List[MobilogramObject],
        variables: List,
        name: str = "",
        metadata=None,
        extra_data=None,
        x_label="Scans",
        y_label="Drift time (bins)",
        **kwargs,
    ):
        # pre-process data before setting it up in the container
        array, x, y = self._preprocess(data_objects, variables)

        super().__init__(
            array,
            x=x,
            y=y,
            xy=None,
            yy=None,
            x_label=x_label,
            y_label=y_label,
            metadata=metadata,
            extra_data=extra_data,
            name=name,
            **kwargs,
        )

    @staticmethod
    def _preprocess(data_objects: List[MobilogramObject], variables: List):
        """"""
        assert len(data_objects) == len(variables)
        obj = data_objects[0]
        y = obj.x
        x = np.asarray(variables)
        array = np.zeros((len(y), len(x)), dtype=np.float32)
        for i, mob in enumerate(data_objects):
            array[:, i] = mob.y

        x, y, array = equalize_heatmap_spacing(x, y, array)

        return array, x, y


class MassSpectrumHeatmapObject(HeatmapObject):
    def __init__(
        self,
        array,
        x,
        y,
        xy=None,
        yy=None,
        name: str = "",
        metadata=None,
        extra_data=None,
        x_label="m/z (Da)",
        y_label="Drift time (bins)",
        **kwargs,
    ):
        super().__init__(
            array,
            name,
            x=x,
            y=y,
            xy=xy,
            yy=yy,
            x_label=x_label,
            y_label=y_label,
            x_label_options=["Drift time (bins)", "Drift time (ms)"],
            metadata=metadata,
            extra_data=extra_data,
            **kwargs,
        )


def mass_spectrum_object(group: Group):
    """Instantiate mass spectrum object from mass spectrum group saved in zarr format"""
    return MassSpectrumObject(group["x"][:], group["y"][:], **group.attrs.asdict())


def chromatogram_object(group: Group):
    """Instantiate mass spectrum object from chromatogram group saved in zarr format"""
    return ChromatogramObject(group["x"][:], group["y"][:], **group.attrs.asdict())


def mobilogram_object(group: Group):
    """Instantiate mass spectrum object from mobilogram group saved in zarr format"""
    return MobilogramObject(group["x"][:], group["y"][:], **group.attrs.asdict())


def ion_heatmap_object(group: Group):
    """Instantiate ion heatmap object from ion heatmap group saved in zarr format"""
    return IonHeatmapObject(
        group["array"][:], group["x"][:], group["y"][:], group["xy"][:], group["yy"][:], **group.attrs.asdict()
    )


def msdt_heatmap_object(group: Group):
    """Instantiate ion heatmap object from ion heatmap group saved in zarr format"""
    return MassSpectrumHeatmapObject(
        group["array"][:], group["x"][:], group["y"][:], group["xy"][:], group["yy"][:], **group.attrs.asdict()
    )
