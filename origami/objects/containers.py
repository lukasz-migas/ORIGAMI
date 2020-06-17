# Standard library imports
from typing import List
from typing import Union
from typing import Optional

# Third-party imports
import numpy as np
from zarr import Group

# Local imports
import origami.processing.spectra as pr_spectra
from origami.utils.path import get_duplicate_name
from origami.utils.ranges import get_min_max
from origami.objects.container import ContainerBase
from origami.processing.heatmap import equalize_heatmap_spacing


def get_fmt(*arrays: np.ndarray, get_largest: bool = False):
    """Retrieve appropriate numpy format based on the data"""
    fmts = []
    for array in arrays:
        if np.issubdtype(array.dtype, np.integer):
            fmts.append("%d")
        elif np.issubdtype(array.dtype, np.float32):
            fmts.append("%.4f")
        else:
            fmts.append("%.6f")
    if get_largest:
        if "%.6f" in fmts:
            return "%.6f"
        if "%.4f" in fmts:
            return "%.4f"
        return "%d"
    return fmts


def check_alternative_names(current_label, to_label, alternative_labels):
    """Checks whether the current label and the new label are alternatives of each other"""
    if current_label in alternative_labels and to_label in alternative_labels:
        return True
    return False


class DataObject(ContainerBase):
    """Generic data object"""

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
        return get_min_max(self.x)

    @property
    def y_limit(self):
        return get_min_max(self.y)

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
        """Check input"""
        raise NotImplementedError("Must implement method")

    def copy(self):
        """Copy object and flush to disk"""
        store = self.get_parent()
        title = self.title
        if store is not None and title is not None:
            title = get_duplicate_name(title)
            data, attrs = self.to_zarr()
            store.add(title, data, attrs)
            return store[title, True]

    def flush(self):
        """Flush current object data to the DocumentStore"""
        store = self.get_parent()
        title = self.title
        if store is not None and title is not None:
            data, attrs = self.to_zarr()
            store.add(title, data, attrs)

    def change_x_label(self, to_label: str, **kwargs):
        """Changes the label and x-axis values to a new format"""

    def change_y_label(self, to_label: str, **kwargs):
        """Changes the label and y-axis values to a new format"""


class SpectrumObject(DataObject):
    """Generic spectrum object"""

    def __init__(self, x, y, x_label: str, y_label: str, name: str, metadata: dict, extra_data: dict, **kwargs):
        super().__init__(name, x, y, x_label, y_label, metadata=metadata, extra_data=extra_data, **kwargs)

    @property
    def x_bin(self):
        return np.arange(len(self.x))

    @property
    def x_spacing(self):
        """Return the average spacing value for the x-axis"""
        return np.mean(np.diff(self.x))

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
        data = {**self._extra_data, "x": self.x, "y": self.y}
        attrs = {
            **self._metadata,
            "class": self._cls,
            "x_limit": self.x_limit,
            "x_label": self.x_label,
            "y_label": self.y_label,
        }
        return data, attrs

    def to_csv(self, path, *args, **kwargs):
        """Export data in a csv/txt format"""
        x, y = self.x, self.y
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

    def normalize(self):
        """Normalize spectrum to 1"""
        self._y = pr_spectra.normalize_1D(self.y)
        return self

    def divide(self, divider: Union[int, float]):
        """Divide intensity array by specified divider"""
        assert isinstance(divider, (int, float)), "Division factor must be an integer or a float"
        self._y /= divider
        return self


class MassSpectrumObject(SpectrumObject):
    """Mass spectrum container object"""

    def __init__(
        self, x, y, name: str = "", metadata=None, extra_data=None, x_label="m/z (Da)", y_label="Intensity", **kwargs
    ):
        super().__init__(
            x, y, x_label=x_label, y_label=y_label, name=name, metadata=metadata, extra_data=extra_data, **kwargs
        )

        # set default options
        self.options["remove_zeros"] = True

    def process(
        self, crop: bool = False, linearize: bool = False, smooth: bool = False, baseline: bool = False, **kwargs
    ):
        """Perform all processing steps in one go. For correct parameter names, refer to the individual methods

        Parameters
        ----------
        crop : bool
            if `True`, spectral cropping will occur
        linearize : bool
            if `True`, spectrum will be linearized
        smooth : bool
            if `True`, spectrum will be smoothed
        baseline : bool
            if `True`, baseline will be removed from the mass spectrum
        kwargs : Dict[Any, Any]
            dictionary containing processing parameters

        Returns
        -------
        self : MassSpectrumObject
            processed mass spectrum object
        """
        if crop:
            self.crop(**kwargs)
        if linearize:
            self.linearize(**kwargs)
        if smooth:
            self.smooth(**kwargs)
        if baseline:
            self.baseline(**kwargs)
        return self

    def crop(self, crop_min: Optional[float] = None, crop_max: Optional[float] = None, **kwargs):
        """Crop signal to defined x-axis region

        Parameters
        ----------
        crop_min : float, optional
            minimum value in the x-axis array to be retained
        crop_max : float, optional
            maximum value in the x-axis array to be retained
        """
        x, y = pr_spectra.crop_1D_data(self.x, self.y, crop_min, crop_max)
        self._x, self._y = x, y
        return self

    def linearize(
        self,
        bin_size: Optional[float] = None,
        linearize_method: Optional[str] = None,
        auto_range: bool = True,
        x_min: Optional[float] = None,
        x_max: Optional[float] = None,
        x_bin: Optional[np.ndarray] = None,
        **kwargs,
    ):
        """Linearize data by either up- or down-sampling

        Parameters
        ----------
        bin_size : float
            size of the bin between adjacent values in the x-axis
        linearize_method : str
            name of the linearization method
        auto_range : bool
            if `True`, the x-axis range will be decided automatically
        x_min : floats
            starting value of the linearization method
        x_max : float
            ending value of the linearization method
        x_bin : np.ndarray
            pre-computed x-axis values
        """
        x, y = pr_spectra.linearize_data(
            self.x,
            self.y,
            bin_size=bin_size,
            linearize_method=linearize_method,
            auto_range=auto_range,
            x_min=x_min,
            x_max=x_max,
            x_bin=x_bin,
        )
        self._x, self._y = x, y
        return self

    def smooth(
        self,
        smooth_method: Optional[str] = None,
        sigma: Optional[float] = None,
        poly_order: Optional[int] = None,
        window_size: Optional[int] = None,
        N: Optional[int] = None,
        **kwargs,
    ):
        """Smooth spectral data using one of few filters

        Parameters
        ----------
        smooth_method : str
            name of the smoothing method
        sigma: float
            gaussian sigma value; only used with method being `Gaussian`
        poly_order : int
            polynomial value; only used with method being `Savitzky-Golay`
        window_size : int
            window size; only used with method being `Savitzky-Golay`
        N : int
            size of the window in moving average; only used with method being `Moving average`
        """
        y = pr_spectra.smooth_1d(
            self.y, smooth_method=smooth_method, sigma=sigma, window_size=window_size, poly_order=poly_order, N=N
        )
        self._y = y
        return self

    def baseline(
        self,
        baseline_method: str = "Linear",
        threshold: Optional[float] = None,
        poly_order: Optional[int] = 4,
        max_iter: Optional[int] = 100,
        tol: Optional[float] = 1e-3,
        median_window: Optional[int] = 5,
        curved_window: Optional[int] = None,
        tophat_window: Optional[int] = 100,
        **kwargs,
    ):
        """Subtract baseline from the y-axis intensity array

        Parameters
        ----------
        baseline_method : str
            baseline removal method
        threshold : float
            any value below `threshold` will be set to 0
        poly_order : int
            Degree of the polynomial that will estimate the data baseline. A low degree may fail to detect all the
            baseline present, while a high degree may make the data too oscillatory, especially at the edges; only used
            with method being `Polynomial`
        max_iter : int
            Maximum number of iterations to perform; only used with method being `Polynomial`
        tol : float
            Tolerance to use when comparing the difference between the current fit coefficients and the ones from the
            last iteration. The iteration procedure will stop when the difference between them is lower than *tol*.;
            only used with method being `Polynomial`
        median_window : int
            median filter size - should be an odd number; only used with method being `Median`
        curved_window : int
            curved window size; only used with method being `Curved`
        tophat_window : int
            tophat window size; only used with method being `Top Hat`
        """
        y = pr_spectra.baseline_1D(
            self.y,
            baseline_method=baseline_method,
            threshold=threshold,
            poly_order=poly_order,
            max_iter=max_iter,
            tol=tol,
            median_window=median_window,
            curved_window=curved_window,
            tophat_window=tophat_window,
        )
        self._y = y
        return self


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

    def change_x_label(self, to_label: str, scan_time: Optional[float] = None):
        """Change x-axis label and values. Any changes are automatically flushed to disk.

        Notes
        -----
        Scans -> Retention time (mins), Time (mins)
            - requires x-axis bins
            - requires scan time in seconds
            multiply x-axis bins * scan time and then divide by 60
        Retention time (mins), Time (mins) -> Scans
            - requires x-axis bins OR x-axis time in minutes
            - requires scan time in seconds
            multiply x-axis time * 60 to convert to seconds and then divide by the scan time. Values are rounded
        """
        # set default label
        if "x_label_default" not in self._metadata:
            self._metadata["x_label_default"] = self.x_label

        # check whether the new label refers to the default value
        if to_label == "Restore default":
            to_label = self._metadata["x_label_default"]

        print(to_label, self._metadata)

        if to_label not in self.x_label_options:
            raise ValueError(f"Cannot change label to `{to_label}`; \nAllowed labels: {self.x_label_options}")

        # no need to change anything
        if scan_time is None:
            scan_time = self.get_parent().parameters.get("scan_time", None)
        if self.x_label == to_label or scan_time is None:
            return

        # create back-up of the bin data
        if self.x_label == "Scans":
            self._extra_data["x_bin"] = self.x

        if to_label in ["Time (mins)", "Retention time (mins)"] and self.x_label == "Scans":
            if "x_min" in self._extra_data:
                x = self._extra_data["x_min"]
            else:
                x = self._extra_data["x_bin"]
                x = x * (scan_time / 60)
        elif to_label == "Scans" and self.x_label in ["Time (mins)", "Retention time (mins)"]:
            if "x_bin" in self._extra_data:
                x = self._extra_data["x_bin"]
            else:
                x = self.x
                x = np.round((x * 60) / scan_time).astype(np.int32)
        elif check_alternative_names(self.x_label, to_label, ["Time (mins)", "Retention time (mins)"]):
            x = self.x
        else:
            raise ValueError("Cannot convert x-axis")

        # set data
        self.x_label = to_label
        self._x = x
        self.flush()


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

    def change_x_label(self, to_label: str, pusher_freq: Optional[float] = None):
        """Change x-axis label and values. Any changes are automatically flushed to disk.

        Notes
        -----
        Drift time (bins) -> Drift time (ms) / Arrival time (ms)
            - requires x-axis bins
            - requires pusher frequency in microseconds
            multiply x-axis bins * pusher frequency and divide by 1000
        Drift time (ms) / Arrival time (ms) -> Drift time (bins)
            - requires x-axis bins OR x-axis time
            - requires pusher frequency in microseconds
            multiply x-axis time * 1000 and divide by pusher frequency
        """
        # set default label
        if "x_label_default" not in self._metadata:
            self._metadata["x_label_default"] = self.x_label

        # check whether the new label refers to the default value
        if to_label == "Restore default":
            to_label = self._metadata["x_label_default"]

        print(to_label, self._metadata)

        if to_label not in self.x_label_options:
            raise ValueError(f"Cannot change label to `{to_label}`; \nAllowed labels: {self.x_label_options}")

        # no need to change anything
        pusher_freq = self.get_parent().parameters.get("pusher_freq", None)
        if self.x_label == to_label or pusher_freq is None:
            return

        # create back-up of the bin data
        if self.x_label == "Drift time (bins)":
            self._extra_data["x_bin"] = self.x

        if to_label in ["Drift time (ms)", "Arrival time (ms)"] and self.x_label == "Drift time (bins)":
            if "x_ms" in self._extra_data:
                x = self._extra_data["x_ms"]
            else:
                x = self._extra_data["x_bin"]
                x = x * (pusher_freq / 1000)
        elif to_label == "Drift time (bins)" and self.x_label in ["Drift time (ms)", "Arrival time (ms)"]:
            if "x_bin" in self._extra_data:
                x = self._extra_data["x_bin"]
            else:
                x = self.x
                x = np.round((x * 1000) / pusher_freq).astype(np.int32)
        elif check_alternative_names(self.x_label, to_label, ["Drift time (ms)", "Arrival time (ms)"]):
            x = self.x
        else:
            raise ValueError("Cannot convert x-axis")

        # set data
        self.x_label = to_label
        self._x = x
        self.flush()


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
        self._array = array
        self._xy = xy
        self._yy = yy
        super().__init__(name, x, y, x_label, y_label, metadata=metadata, extra_data=extra_data, **kwargs)

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
        data = {**self._extra_data, "x": self.x, "y": self.y, "array": self.array, "xy": self.xy, "yy": self.yy}
        attrs = {**self._metadata, "class": self._cls, "x_label": self.x_label, "y_label": self.y_label}
        return data, attrs

    def to_csv(self, path, *args, **kwargs):
        """Export data in a csv/txt format"""
        array, x, y = self.array, self.x, self.y
        # get metadata
        delimiter = kwargs.get("delimiter", ",")

        # sum the mobility dimension
        if kwargs.get("dim_dt"):
            fmt = get_fmt(self.x, self.xy)
            header = f"{delimiter}".join([self.y_label, "Intensity"])
            np.savetxt(path, np.c_[self.y, self.yy], delimiter=delimiter, fmt=fmt, header=header)
        # sum the chromatography dimension
        elif kwargs.get("dim_rt"):
            fmt = get_fmt(self.x, self.xy)
            header = f"{delimiter}".join([self.x_label, "Intensity"])
            np.savetxt(path, np.c_[self.x, self.xy], delimiter=delimiter, fmt=fmt, header=header)
        # return array
        else:
            fmt = get_fmt(array, x, y, get_largest=True)
            labels = list(map(str, x.tolist()))
            labels.insert(0, "")
            header = f"{delimiter}".join(labels)
            np.savetxt(path, np.c_[y, array], delimiter=delimiter, fmt=fmt, header=header)

    def check(self):
        """Checks whether the provided data has the same size and shape"""
        if len(self._array.shape) != 2:
            raise ValueError("`array` must have two dimensions")
        if not isinstance(self._metadata, dict):
            self._metadata = dict()

    def downsample(self, rate: int = 5, mode: str = "Sub-sample"):
        """Return data at a down-sampled rate"""


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
            x_label_options=[
                "Scans",
                "Time (mins)",
                "Retention time (mins)",
                "Collision Voltage (V)",
                "Activation Voltage (V)",
                "Lab Frame Energy (eV)",
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

    # noinspection DuplicatedCode
    def change_x_label(self, to_label: str, charge: Optional[int] = None, scan_time: Optional[float] = None):
        """Change x-axis label and values. Any changes are automatically flushed to disk.

        Notes
        -----
        Scans -> Retention time (mins), Time (mins)
            - requires x-axis bins
            - requires scan time in seconds
            multiply x-axis bins * scan time and then divide by 60
        Retention time (mins), Time (mins) -> Scans
            - requires x-axis bins OR x-axis time in minutes
            - requires scan time in seconds
            multiply x-axis time * 60 to convert to seconds and then divide by the scan time. Values are rounded
        """
        # set default label
        if "x_label_default" not in self._metadata:
            self._metadata["x_label_default"] = self.x_label

        # check whether the new label refers to the default value
        if to_label == "Restore default":
            to_label = self._metadata["x_label_default"]

        if to_label not in self.x_label_options:
            raise ValueError(f"Cannot change label to `{to_label}`; \nAllowed labels: {self.x_label_options}")

        # no need to change anything
        if scan_time is None:
            scan_time = self.get_parent().parameters.get("scan_time", None)
        if charge is None:
            charge = self._metadata.get("charge", 1)
        if self.x_label == to_label or scan_time is None:
            return

        # create back-up of the bin data
        if self.x_label == "Scans":
            self._extra_data["x_bin"] = self.x

        # convert scans to time
        if to_label in ["Time (mins)", "Retention time (mins)"] and self.x_label == "Scans":
            if "x_min" in self._extra_data:
                x = self._extra_data["x_min"]
            else:
                x = self._extra_data["x_bin"]
                x = x * (scan_time / 60)
        # convert time to scans
        elif to_label == "Scans" and self.x_label in ["Time (mins)", "Retention time (mins)"]:
            if "x_bin" in self._extra_data:
                x = self._extra_data["x_bin"]
            else:
                x = self.x
                x = np.round((x * 60) / scan_time).astype(np.int32)
        # convert lab frame energy to activation energy
        elif (
            to_label in ["Collision Voltage (V)", "Activation Voltage (V)"] and self.x_label == "Lab Frame Energy (eV)"
        ):
            if "x_cv" in self._extra_data:
                x = self._extra_data["x_cv"]
            else:
                x = self.x / charge
        # convert lab frame energy to activation energy
        elif to_label == "Lab Frame Energy (eV)" and self.x_label in [
            "Collision Voltage (V)",
            "Activation Voltage (V)",
        ]:
            if "x_ev" in self._extra_data:
                x = self._extra_data["x_ev"]
            else:
                x = self.x * charge
        elif check_alternative_names(
            self.x_label, to_label, ["Time (mins)", "Retention time (mins)"]
        ) or check_alternative_names(self.x_label, to_label, ["Collision Voltage (V)", "Activation Voltage (V)"]):
            x = self.x
        else:
            raise ValueError("Cannot convert x-axis")

        # set data
        self.x_label = to_label
        self._x = x
        self.flush()

    # noinspection DuplicatedCode
    def change_y_label(self, to_label: str, pusher_freq: Optional[float] = None):
        """Change x-axis label and values. Any changes are automatically flushed to disk.

        Notes
        -----
        Drift time (bins) -> Drift time (ms) / Arrival time (ms)
            - requires x-axis bins
            - requires pusher frequency in microseconds
            multiply x-axis bins * pusher frequency and divide by 1000
        Drift time (ms) / Arrival time (ms) -> Drift time (bins)
            - requires x-axis bins OR x-axis time
            - requires pusher frequency in microseconds
            multiply x-axis time * 1000 and divide by pusher frequency
        """
        # set default label
        if "y_label_default" not in self._metadata:
            self._metadata["y_label_default"] = self.x_label

        # check whether the new label refers to the default value
        if to_label == "Restore default":
            to_label = self._metadata["y_label_default"]

        if to_label not in self.y_label_options:
            raise ValueError(f"Cannot change label to `{to_label}`; \nAllowed labels: {self.y_label_options}")

        # no need to change anything
        if pusher_freq is None:
            pusher_freq = self.get_parent().parameters.get("pusher_freq", None)
        if self.y_label == to_label or pusher_freq is None:
            return

        # create back-up of the bin data
        if self.y_label == "Drift time (bins)":
            self._extra_data["y_bin"] = self.y

        if to_label in ["Drift time (ms)", "Arrival time (ms)"] and self.y_label == "Drift time (bins)":
            if "y_ms" in self._extra_data:
                y = self._extra_data["y_ms"]
            else:
                y = self._extra_data["y_bin"]
                y = y * (pusher_freq / 1000)
        elif to_label == "Drift time (bins)" and self.y_label in ["Drift time (ms)", "Arrival time (ms)"]:
            if "y_bin" in self._extra_data:
                y = self._extra_data["y_bin"]
            else:
                y = self.y
                y = np.round((y * 1000) / pusher_freq).astype(np.int32)
        elif check_alternative_names(self.y_label, to_label, ["Drift time (ms)", "Arrival time (ms)"]):
            y = self.y
        else:
            raise ValueError("Cannot convert x-axis")

        # set data
        self.y_label = to_label
        self._y = y
        self.flush()


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
            x_label_options=["m/z (Da)"],
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

    def change_x_label(self, to_label: str, **kwargs):
        """Changes the label and x-axis values to a new format"""


def mass_spectrum_object(group: Group):
    """Instantiate mass spectrum object from mass spectrum group saved in zarr format"""
    metadata = group.attrs.asdict()
    obj = MassSpectrumObject(group["x"][:], group["y"][:], **metadata)
    obj.set_metadata(metadata)
    return obj


def chromatogram_object(group: Group):
    """Instantiate chromatogram object from chromatogram group saved in zarr format"""
    metadata = group.attrs.asdict()
    obj = ChromatogramObject(group["x"][:], group["y"][:], **group.attrs.asdict())
    obj.set_metadata(metadata)
    return obj


def mobilogram_object(group: Group):
    """Instantiate mobilogram object from mobilogram group saved in zarr format"""
    metadata = group.attrs.asdict()
    obj = MobilogramObject(group["x"][:], group["y"][:], **group.attrs.asdict())
    obj.set_metadata(metadata)
    return obj


def ion_heatmap_object(group: Group):
    """Instantiate ion heatmap object from ion heatmap group saved in zarr format"""
    metadata = group.attrs.asdict()
    obj = IonHeatmapObject(
        group["array"][:], group["x"][:], group["y"][:], group["xy"][:], group["yy"][:], **group.attrs.asdict()
    )
    obj.set_metadata(metadata)
    return obj


def stitch_ion_heatmap_object(group: Group):
    """Instantiate stitch ion heatmap object from ion heatmap group saved in zarr format"""
    metadata = group.attrs.asdict()
    obj = StitchIonHeatmapObject(
        group["array"][:], group["x"][:], group["y"][:], group["xy"][:], group["yy"][:], **group.attrs.asdict()
    )
    obj.set_metadata(metadata)
    return obj


def msdt_heatmap_object(group: Group):
    """Instantiate mass heatmap object from ion heatmap group saved in zarr format"""
    metadata = group.attrs.asdict()
    obj = MassSpectrumHeatmapObject(
        group["array"][:], group["x"][:], group["y"][:], group["xy"][:], group["yy"][:], **group.attrs.asdict()
    )
    obj.set_metadata(metadata)
    return obj
