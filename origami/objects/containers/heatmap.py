"""Heatmap container objects"""
# Standard library imports
import math
import logging
from typing import List
from typing import Union
from typing import Optional

# Third-party imports
import numpy as np

# Local imports
from origami.processing import heatmap as pr_heatmap
from origami.processing.utils import find_nearest_index
from origami.processing.heatmap import equalize_heatmap_spacing
from origami.objects.containers.base import DataObject
from origami.objects.containers.spectrum import MobilogramObject
from origami.objects.containers.spectrum import ChromatogramObject
from origami.objects.containers.utilities import OrigamiMsMixin
from origami.objects.containers.utilities import MobilogramAxesMixin
from origami.objects.containers.utilities import ChromatogramAxesMixin
from origami.objects.containers.utilities import get_fmt

LOGGER = logging.getLogger(__name__)


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

    def reset_xy_cache(self):
        """Reset cached summed arrays"""
        self._xy = None
        self._yy = None

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

    def _get_roi_slice(self, x_max, x_min, y_max, y_min):
        x_min_idx, x_max_idx = find_nearest_index(self.x, [x_min, x_max])
        y_min_idx, y_max_idx = find_nearest_index(self.y, [y_min, y_max])
        array = self._array[y_min_idx : y_max_idx + 1, x_min_idx : x_max_idx + 1]
        return array, x_min_idx, x_max_idx + 1, y_min_idx, y_max_idx + 1

    def get_x_for_roi(self, x_min: float, x_max: float, y_min: float, y_max: float):
        """Get array of intensities for particular region of interest along the horizontal axis"""
        array, x_min_idx, x_max_idx, _, _ = self._get_roi_slice(x_max, x_min, y_max, y_min)
        y = np.zeros(self.shape[1])
        y[x_min_idx:x_max_idx] = array.sum(axis=0)
        return y

    def get_y_for_roi(self, x_min: float, x_max: float, y_min: float, y_max: float):
        """Get array of intensities for particular region of interest along the horizontal axis"""
        array, _, _, y_min_idx, y_max_idx = self._get_roi_slice(x_max, x_min, y_max, y_min)
        y = np.zeros(self.shape[0])
        y[y_min_idx:y_max_idx] = array.sum(axis=1)
        return y

    def get_array_for_roi(self, x_min: float, x_max: float, y_min: float, y_max: float):
        """Get array of intensities for particular region of interest along both dimensions"""
        array, x_min_idx, x_max_idx, y_min_idx, y_max_idx = self._get_roi_slice(x_max, x_min, y_max, y_min)
        x = self.x[x_min_idx:x_max_idx]
        y = self.x[y_min_idx:y_max_idx]
        return self.downsample(x=x, y=y, array=array)

    def transpose(self):
        """Transpose array

        Returns
        -------
        self
        """
        # reset the x/y-axis
        self._x, self._y = self.y, self.x
        # reset the x/y-labels
        self._x_label, self._y_label = self.y_label, self.x_label
        self._x_label_options, self._y_label_options = self._y_label_options, self._x_label_options
        # rotate the array
        self._array = self._array.T
        self.unsaved = True
        return self

    def downsample(
        self,
        max_x_size: int = 1000,
        mode: str = "Sub-sample",
        x: np.ndarray = None,
        y: np.ndarray = None,
        array: np.ndarray = None,
    ):
        """Return data at a down-sampled rate"""
        if x is None:
            x = self.x
        if y is None:
            y = self.y
        if array is None:
            array = self.array

        if mode == "Sub-sample":
            rate = math.ceil(array.shape[1] / max_x_size)
            x = x[::rate]
            array = array[:, ::rate]
        elif mode == "Summed":
            n_rows, n_cols = array.shape
            n_cols = n_cols if n_cols <= max_x_size else max_x_size
            array, _ = pr_heatmap.view_as_blocks(array, n_rows, n_cols)
            array = array.sum(axis=0)
            x, _ = pr_heatmap.view_as_blocks(x[np.newaxis, :], 1, n_cols)
            x = x.mean(axis=0).ravel()
        return x, y, array

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
        self : origami.objects.containers.spectrum.MassSpectrumObject
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
        self.unsaved = True
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
        self.unsaved = True
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
        self.unsaved = True
        return self

    def baseline(self, threshold: Union[int, float] = 0, **kwargs):  # noqa
        """Remove baseline"""
        self._array = pr_heatmap.remove_noise_2d(self.array, threshold)
        self.unsaved = True
        return self

    def normalize(self, normalize_method: str = "Maximum", **kwargs):  # noqa
        """Normalize heatmap"""
        self._array = pr_heatmap.normalize_2d(self.array, method=normalize_method)
        self.unsaved = True
        return self


class IonHeatmapObject(HeatmapObject, ChromatogramAxesMixin, MobilogramAxesMixin, OrigamiMsMixin):
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

    # noinspection DuplicatedCode
    def change_x_label(self, to_label: str, charge: Optional[int] = None, scan_time: Optional[float] = None):
        """Change x-axis label and values. Any changes are automatically flushed to disk.

        Conversion of the x-axis label in the heatmap object is a little bit more difficult because there is a lot more
        possibilities of conversions.

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
        x_label_option_1 = ["Scans", "Time (mins)", "Retention time (mins)", "Restore default"]
        x_label_option_2 = [
            "Collision Voltage (V)",
            "Activation Voltage (V)",
            "Activation Energy (V)",
            "Lab Frame Energy (eV)",
            "Activation Voltage (eV)",
            "Activation Energy (eV)",
            "Restore default",
        ]
        if to_label in x_label_option_1 and self.x_label in x_label_option_1:
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
        elif to_label in x_label_option_2 and self.x_label in x_label_option_2:
            to_label, x = self._change_rt_cv_axis(
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
        else:
            raise ValueError(
                f"Cannot convert label from `{self.x_label}` to `{to_label}`. If you are trying to convert"
                " `Scans` to `Collision Voltage` and this is a ORIGAMI-MS document consider applying"
                " ORIGAMI-MS settings on this heatmap object."
            )

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

    def apply_origami_ms(self):
        """Apply ORIGAMI-MS settings on the heatmap object"""
        if self.x_label in ["Collision Voltage (V)", "Activation Voltage (V)", "Lab Frame Energy (eV)"]:
            LOGGER.warning("Dataset already has Collision Voltage (V) labels")
            return self
        elif self.x_label != "Scans" and self.x_label in ["Time (mins)", "Retention time (mins)"]:
            self.change_x_label("Scans")
        elif self.x_label != "Scans":
            raise ValueError("Cannot apply ORIGAMI-MS settings on this object")

        # convert data
        self._array, self._x, start_end_cv, parameters = self._apply_origami_ms(self.array)
        self.reset_xy_cache()

        # set extra data
        self.x_label = "Collision Voltage (V)"
        self._extra_data["oms_ss_es_cv"] = start_end_cv
        self._metadata["origami_ms"] = parameters

        # get new title
        self.title = self.title + " [CIU]"
        self.flush()
        return self

    def as_mobilogram(self):
        """Return instance of MobilogramObject"""
        return MobilogramObject(self.x, self.xy)

    def as_chromatogram(self):
        """Return instance of MobilogramObject"""
        return ChromatogramObject(self.y, self.yy)


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
    """Heatmap object for imaging purposes"""

    def __init__(
        self, array: np.ndarray, name: str = "", metadata=None, extra_data=None, x_label="x", y_label="y", **kwargs
    ):
        # pre-process data before setting it up in the container
        array, x, y = self._preprocess(array)

        super().__init__(
            array,
            x=x,
            y=y,
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
