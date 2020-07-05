"""Various container objects"""
# Standard library imports
import logging
from abc import ABC
from abc import abstractmethod
from typing import Dict
from typing import List
from typing import Tuple
from typing import Union
from typing import Optional

# Third-party imports
import numpy as np
from zarr import Group

# Local imports
import origami.processing.heatmap as pr_heatmap
import origami.processing.spectra as pr_spectra
from origami.utils.path import get_duplicate_name
from origami.utils.ranges import get_min_max
from origami.processing.utils import find_nearest_index
from origami.objects.container import ContainerBase
from origami.processing.heatmap import equalize_heatmap_spacing
from origami.objects.annotations import Annotations

LOGGER = logging.getLogger(__name__)


class ChromatogramAxesMixin(ABC):
    """Mixin class to provide easy conversion of x-axis"""

    def _change_rt_axis(
        self,
        to_label: str,
        scan_time: Optional[float],
        metadata: Dict,
        extra_data: Dict,
        label_options: List[str],
        current_label: str,
        current_values: np.ndarray,
        default_label_key: str,
        min_key: str,
        bin_key: str,
    ) -> Tuple[str, np.ndarray]:
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
        metadata : Dict
            dictionary containing metadata information
        extra_data : Dict
            dictionary containing all additional data
        label_options : List[str]
            list of available labels for particular object
        current_label : str
            current label of the object
        default_label_key : str
            key by which the default value can be determined (e.g `x_label_default` or `y_label_default`)
        min_key : str
            key by which the time axis values can be accessed (e.g. `x_min`)
        bin_key : str
            key by which the bin axis values can be accessed (e.g. `x_bin`)

        Returns
        -------
        to_label : str
            new axis label of the object
        new_values : np.ndarray
            new axis values of the object
        """

        def _get_scan_time(_scan_time):
            # no need to change anything
            if _scan_time is None:
                _scan_time = self.get_parent().parameters.get("scan_time", None)
            if _scan_time is None:
                raise ValueError("Cannot perform conversion due to a missing `scan_time` information.")
            return _scan_time

        # set default label
        if default_label_key not in metadata:
            metadata[default_label_key] = current_label

        # check whether the new label refers to the default value
        if to_label == "Restore default":
            to_label = metadata[default_label_key]

        if to_label not in label_options:
            raise ValueError(f"Cannot change label to `{to_label}`; \nAllowed labels: {label_options}")

        if current_label == to_label:
            LOGGER.warning("The before and after labels are the same")
            return current_label, current_values

        # create back-up of the bin data
        if current_label == "Scans":
            extra_data[bin_key] = current_values

        if to_label in ["Time (mins)", "Retention time (mins)"] and current_label == "Scans":
            if min_key in extra_data:
                new_values = extra_data[min_key]
            else:
                new_values = extra_data[bin_key]
                new_values = new_values * (_get_scan_time(scan_time) / 60)
        elif to_label == "Scans" and current_label in ["Time (mins)", "Retention time (mins)"]:
            if bin_key in extra_data:
                new_values = extra_data[bin_key]
            else:
                new_values = current_values
                new_values = np.round((new_values * 60) / _get_scan_time(scan_time)).astype(np.int32)
        elif check_alternative_names(current_label, to_label, ["Time (mins)", "Retention time (mins)"]):
            new_values = current_values
        else:
            raise ValueError("Cannot convert x-axis")

        # set data
        return to_label, new_values

    @abstractmethod
    def get_parent(self):  # noqa
        raise NotImplementedError("Must implement method")


class MobilogramAxesMixin(ABC):
    """Mixin class to provide easy conversion of x-axis"""

    def _change_dt_axis(
        self,
        to_label: str,
        pusher_freq: Optional[float],
        metadata: Dict,
        extra_data: Dict,
        label_options: List[str],
        current_label: str,
        current_values: np.ndarray,
        default_label_key: str,
        ms_key: str,
        bin_key: str,
    ) -> Tuple[str, np.ndarray]:
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
        metadata : Dict
            dictionary containing metadata information
        extra_data : Dict
            dictionary containing all additional data
        label_options : List[str]
            list of available labels for particular object
        current_label : str
            current label of the object
        default_label_key : str
            key by which the default value can be determined (e.g `x_label_default` or `y_label_default`)
        ms_key : str
            key by which the time axis values can be accessed (e.g. `x_min`)
        bin_key : str
            key by which the bin axis values can be accessed (e.g. `x_bin`)

        Returns
        -------
        to_label : str
            new axis label of the object
        new_values : np.ndarray
            new axis values of the object
        """

        def _get_pusher_freq(_pusher_freq):
            # no need to change anything
            if _pusher_freq is None:
                _pusher_freq = self.get_parent().parameters.get("pusher_freq", None)
            if _pusher_freq is None:
                raise ValueError("Cannot perform conversion due to a missing `pusher_freq` information.")
            return _pusher_freq

        # set default label
        if default_label_key not in metadata:
            metadata[default_label_key] = current_label

        # check whether the new label refers to the default value
        if to_label == "Restore default":
            to_label = metadata[default_label_key]

        if to_label not in label_options:
            raise ValueError(f"Cannot change label to `{to_label}`; \nAllowed labels: {label_options}")

        if current_label == to_label:
            LOGGER.warning("The before and after labels are the same")
            return current_label, current_values

        # create back-up of the bin data
        if current_label == "Drift time (bins)":
            extra_data["x_bin"] = current_values

        if to_label in ["Drift time (ms)", "Arrival time (ms)"] and current_label == "Drift time (bins)":
            if ms_key in extra_data:
                new_values = extra_data[ms_key]
            else:
                new_values = extra_data[bin_key]
                new_values = new_values * (_get_pusher_freq(pusher_freq) / 1000)
        elif to_label == "Drift time (bins)" and current_label in ["Drift time (ms)", "Arrival time (ms)"]:
            if bin_key in extra_data:
                new_values = extra_data[bin_key]
            else:
                new_values = current_values
                new_values = np.round((new_values * 1000) / _get_pusher_freq(pusher_freq)).astype(np.int32)
        elif check_alternative_names(current_label, to_label, ["Drift time (ms)", "Arrival time (ms)"]):
            new_values = current_values
        else:
            raise ValueError("Cannot convert x-axis")

        # set data
        return to_label, new_values

    @abstractmethod
    def get_parent(self):  # noqa
        raise NotImplementedError("Must implement method")


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
    DOCUMENT_KEY = None

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
        """Return the `x` axis of the dataset"""
        return self._x

    @property
    def y(self):
        """Return the `y` axis of the dataset"""
        return self._y

    @property
    def x_limit(self):
        """Return the min/max values of the x-axis"""
        return get_min_max(self.x)

    @property
    def y_limit(self):
        """Return the min/max values of the y-axis"""
        return get_min_max(self.y)

    @property
    def shape(self):
        """Return the shape of the object"""
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
        """Export data in a csv format"""
        raise NotImplementedError("Must implement method")

    def to_dict(self):
        """Export data in a dictionary object"""
        raise NotImplementedError("Must implement method")

    def to_zarr(self):
        """Outputs data to dictionary of `data` and `attributes`"""
        raise NotImplementedError("Must implement method")

    def check(self):
        """Check input"""
        raise NotImplementedError("Must implement method")

    def copy(self, new_name: str = None, suffix: str = "copy"):
        """Copy object and flush to disk"""
        store = self.get_parent()
        title = self.title
        if store is not None and title is not None:
            if new_name is None:
                new_name = get_duplicate_name(title, suffix=suffix)
            data, attrs = self.to_zarr()
            store.add(new_name, data, attrs)
            return new_name, store[new_name, True]

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

    def get_annotations(self):
        """Returns instance of the `Annotations` object"""

        annotations = self._metadata.get("annotations", dict())
        return Annotations(annotations)

    def set_annotations(self, annotations: Annotations):
        """Set instance of the `Annotations` object"""
        self._metadata["annotations"] = annotations.to_dict()
        self.flush()


class SpectrumObject(DataObject):
    """Generic spectrum object"""

    def __init__(self, x, y, x_label: str, y_label: str, name: str, metadata: dict, extra_data: dict, **kwargs):
        super().__init__(name, x, y, x_label, y_label, metadata=metadata, extra_data=extra_data, **kwargs)

    @property
    def x_bin(self):
        """Return x-axis in bins"""
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

    def get_intensity_at_loc(self, x_min: float, x_max: float, get_max: bool = True):
        """Get intensity information for specified x-axis region of interest"""
        x_idx_min, x_idx_max = find_nearest_index(self.x, [x_min, x_max])
        y = self.y[x_idx_min : x_idx_max + 1]
        if get_max:
            return float(y.max())
        return y


class MassSpectrumObject(SpectrumObject):
    """Mass spectrum container object"""

    DOCUMENT_KEY = "Mass Spectra"

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

    def crop(self, crop_min: Optional[float] = None, crop_max: Optional[float] = None, **kwargs):  # noqa
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
        **kwargs,  # noqa
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
        N: Optional[int] = None,  # noqa
        **kwargs,  # noqa
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
        **kwargs,  # noqa
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


class ChromatogramObject(SpectrumObject, ChromatogramAxesMixin):
    """Chromatogram data object"""

    DOCUMENT_KEY = "Chromatograms"

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
        to_label, x = self._change_rt_axis(
            to_label,
            scan_time,
            self._metadata,
            self._extra_data,
            self.x_label_options,
            self.x_label,
            self.x,
            "x_label_default",
            "x_min",
            "x_bin",
        )

        # set data
        self.x_label = to_label
        self._x = x
        self.flush()


class MobilogramObject(SpectrumObject, MobilogramAxesMixin):
    """Mobilogram data object"""

    DOCUMENT_KEY = "Mobilograms"

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
        to_label, x = self._change_dt_axis(
            to_label,
            pusher_freq,
            self._metadata,
            self._extra_data,
            self.x_label_options,
            self.x_label,
            self.x,
            "x_label_default",
            "x_ms",
            "x_bin",
        )

        # set data
        self.x_label = to_label
        self._x = x
        self.flush()


class HeatmapObject(DataObject):
    """Base heatmap object"""

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
        """Return x-axis of the object"""
        if self._x is None:
            self._x = np.arange(1, self.shape[1])
        return self._x

    @property
    def y(self):
        """Return y-axis of the object"""
        if self._y is None:
            self._y = np.arange(1, self.shape[0])
        return self._y

    @property
    def xy(self):
        """Return intensity values of the x-axis (second dimension)"""
        if self._xy is None:
            self._xy = self.array.sum(axis=0)
        return self._xy

    @property
    def yy(self):
        """Return intensity values of the y-axis (first dimension)"""
        if self._yy is None:
            self._yy = self.array.sum(axis=1)
        return self._yy

    @property
    def array(self):
        """Return the array object"""
        return self._array

    @property
    def shape(self):
        """Return the shape of the object"""
        return self._array.shape

    def to_dict(self):
        """Export data in a dictionary format"""
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
            labels = list(map(str, x.tolist()))  # noqa
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

    def process(
        self,
        crop: bool = False,
        linearize: bool = False,
        smooth: bool = False,
        baseline: bool = False,
        normalize: bool = False,
        **kwargs,
    ):
        """Perform all processing steps in one go. For correct parameter names, refer to the individual methods

        Parameters
        ----------
        crop : bool
            if `True`, heatmap cropping will occur
        linearize : bool
            if `True`, heatmap will be linearized
        smooth : bool
            if `True`, heatmap will be smoothed
        baseline : bool
            if `True`, baseline will be removed from the heatmap
        normalize : bool
            if `True`, heatmap will be normalized
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
        if normalize:
            self.normalize(**kwargs)
        return self

    def linearize(
        self,
        fold: float = 1,
        linearize_method: str = "linear",
        x_axis: bool = False,
        new_x: np.ndarray = None,
        y_axis: bool = False,
        new_y: np.ndarray = None,
        **kwargs,  # noqa
    ):
        """Interpolate the x/y-axis of the array"""
        self._x, self._y, self._array = pr_heatmap.interpolate_2d(
            self.x,
            self.y,
            self.array,
            fold=fold,
            method=linearize_method,
            x_axis=x_axis,
            new_x=new_x,
            y_axis=y_axis,
            new_y=new_y,
        )
        return self

    def crop(
        self,
        x_min: Union[int, float],
        x_max: Union[int, float],
        y_min: Union[int, float],
        y_max: Union[int, float],
        **kwargs,  # noqa
    ):
        """Crop array to desired size and shape"""
        self._x, self._y, self._array = pr_heatmap.crop_2d(self.x, self.y, self.array, x_min, x_max, y_min, y_max)
        return self

    def smooth(
        self,
        smooth_method: str = "Gaussian",
        sigma: int = 1,
        poly_order: int = 1,
        window_size: int = 3,
        **kwargs,  # noqa
    ):
        """Smooth array"""
        self._array = pr_heatmap.smooth_2d(
            self.array, method=smooth_method, sigma=sigma, poly_order=poly_order, window_size=window_size
        )
        return self

    def baseline(self, threshold: Union[int, float] = 0, **kwargs):  # noqa
        """Remove baseline"""
        self._array = pr_heatmap.remove_noise_2d(self.array, threshold)
        return self

    def normalize(self, normalize_method: str = "Maximum", **kwargs):  # noqa
        """Normalize heatmap"""
        self._array = pr_heatmap.normalize_2d(self.array, method=normalize_method)
        return self


class IonHeatmapObject(HeatmapObject, MobilogramAxesMixin):
    """Ion heatmap data object"""

    DOCUMENT_KEY = "Heatmaps"

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
        to_label, y = self._change_dt_axis(
            to_label,
            pusher_freq,
            self._metadata,
            self._extra_data,
            self.y_label_options,
            self.y_label,
            self.y,
            "y_label_default",
            "y_ms",
            "y_bin",
        )

        # set data
        self.y_label = to_label
        self._y = y
        self.flush()


class StitchIonHeatmapObject(IonHeatmapObject):
    """Ion heatmap data object that requires joining multiple mobilograms into one heatmap"""

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


class ImagingIonHeatmapObject(HeatmapObject):
    def __init__(
        self, array: np.ndarray, name: str = "", metadata=None, extra_data=None, x_label="x", y_label="y", **kwargs
    ):
        # pre-process data before setting it up in the container
        array, x, y = self._preprocess(array)

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
    def _preprocess(array: np.ndarray):
        """"""
        x = np.arange(array.shape[1])
        y = np.arange(array.shape[0])

        return array, x, y

    def apply_norm(self, norm):
        """Normalize array"""
        self._array = self.array / norm

        return self


class MassSpectrumHeatmapObject(HeatmapObject, MobilogramAxesMixin):
    """MS/DT heatmap data object"""

    DOCUMENT_KEY = "Heatmaps (MS/DT)"

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
        to_label, y = self._change_dt_axis(
            to_label,
            pusher_freq,
            self._metadata,
            self._extra_data,
            self.y_label_options,
            self.y_label,
            self.y,
            "y_label_default",
            "y_ms",
            "y_bin",
        )

        # set data
        self.y_label = to_label
        self._y = y
        self.flush()


class Normalizer:
    """Normalization class"""

    def __init__(self, array: np.ndarray, x_dim: int, y_dim: int):
        self._array = array
        self.x_dim = x_dim
        self.y_dim = y_dim

    def __call__(self, array: np.ndarray = None, img_obj: ImagingIonHeatmapObject = None):
        """Normalize existing array"""

        def _reshape():
            _array = np.flipud(np.reshape(self._array, (self.x_dim, self.y_dim)))
            return _array

        if array is not None:
            if len(array.shape) == 1:
                array /= self._array
            else:
                array /= _reshape()
            return array
        elif img_obj is not None:
            return img_obj.apply_norm(_reshape())


def get_extra_data(group: Group, known_keys: List):
    """Get all additional metadata that has been saved in the group store"""
    extra_keys = list(set(group.keys()) - set(known_keys))
    extra_data = dict()
    for key in extra_keys:
        extra_data[key] = group[key][:]
    return extra_data


def normalization_object(group: Group):
    """Instantiate normalization object"""
    return Normalizer(group["array"][:], group.attrs["x_dim"], group.attrs["y_dim"])


def mass_spectrum_object(group: Group):
    """Instantiate mass spectrum object from mass spectrum group saved in zarr format"""
    metadata = group.attrs.asdict()
    obj = MassSpectrumObject(
        group["x"][:], group["y"][:], extra_data=get_extra_data(group, ["x", "y"]), **group.attrs.asdict()
    )
    obj.set_metadata(metadata)
    return obj


def chromatogram_object(group: Group):
    """Instantiate chromatogram object from chromatogram group saved in zarr format"""
    metadata = group.attrs.asdict()
    get_extra_data(group, ["x", "y"])
    obj = ChromatogramObject(
        group["x"][:], group["y"][:], extra_data=get_extra_data(group, ["x", "y"]), **group.attrs.asdict()
    )
    obj.set_metadata(metadata)
    return obj


def mobilogram_object(group: Group):
    """Instantiate mobilogram object from mobilogram group saved in zarr format"""
    metadata = group.attrs.asdict()
    obj = MobilogramObject(
        group["x"][:], group["y"][:], extra_data=get_extra_data(group, ["x", "y"]), **group.attrs.asdict()
    )
    obj.set_metadata(metadata)
    return obj


def ion_heatmap_object(group: Group):
    """Instantiate ion heatmap object from ion heatmap group saved in zarr format"""
    metadata = group.attrs.asdict()
    obj = IonHeatmapObject(
        group["array"][:],
        group["x"][:],
        group["y"][:],
        group["xy"][:],
        group["yy"][:],
        extra_data=get_extra_data(group, ["array", "x", "y", "xy", "yy"]),
        **group.attrs.asdict(),
    )
    obj.set_metadata(metadata)
    return obj


def stitch_ion_heatmap_object(group: Group):
    """Instantiate stitch ion heatmap object from ion heatmap group saved in zarr format"""
    metadata = group.attrs.asdict()
    obj = StitchIonHeatmapObject(
        group["array"][:],
        group["x"][:],
        group["y"][:],
        group["xy"][:],
        group["yy"][:],
        extra_data=get_extra_data(group, ["array", "x", "y", "xy", "yy"]),
        **group.attrs.asdict(),
    )
    obj.set_metadata(metadata)
    return obj


def msdt_heatmap_object(group: Group):
    """Instantiate mass heatmap object from ion heatmap group saved in zarr format"""
    metadata = group.attrs.asdict()
    obj = MassSpectrumHeatmapObject(
        group["array"][:],
        group["x"][:],
        group["y"][:],
        group["xy"][:],
        group["yy"][:],
        extra_data=get_extra_data(group, ["array", "x", "y", "xy", "yy"]),
        **group.attrs.asdict(),
    )
    obj.set_metadata(metadata)
    return obj
