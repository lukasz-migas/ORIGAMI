"""Spectrum containers"""
# Standard library imports
import logging
from typing import Union
from typing import Optional

# Third-party imports
import numpy as np

# Local imports
from origami.processing import spectra as pr_spectra
from origami.processing.utils import find_nearest_index
from origami.objects.containers.base import DataObject
from origami.objects.containers.utilities import OrigamiMsMixin
from origami.objects.containers.utilities import MobilogramAxesMixin
from origami.objects.containers.utilities import ChromatogramAxesMixin
from origami.objects.containers.utilities import get_fmt
from origami.objects.containers.utilities import check_output_path

LOGGER = logging.getLogger(__name__)


class SpectrumObject(DataObject):
    """Generic spectrum object"""

    def __init__(self, x, y, x_label: str, y_label: str, name: str, metadata: dict, extra_data: dict, **kwargs):
        super().__init__(name, x, y, x_label, y_label, metadata=metadata, extra_data=extra_data, **kwargs)

    @property
    def x_bin(self):
        """Return x-axis in bins"""
        return np.arange(len(self.x), dtype=np.int32)

    @property
    def x_spacing(self):
        """Return the average spacing value for the x-axis"""
        return np.mean(np.diff(self.x))

    @property
    def xy(self):
        """Return the x- and y-intensity as two columns"""
        return np.transpose([self.x, self.y])

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
            index = np.where((self.x != 0) | (self.y != 0))
            x = x[index]
            y = y[index]

        # get metadata
        fmt = get_fmt(x, y)
        delimiter = kwargs.get("delimiter", ",")
        path = check_output_path(path, delimiter)
        header = f"{delimiter}".join([self.x_label, self.y_label])
        np.savetxt(path, np.c_[x, y], delimiter=delimiter, fmt=fmt, header=header)
        return path

    def check(self):
        """Checks whether the provided data has the same size and shape"""
        if len(self._x) != len(self._y):
            raise ValueError("x and y axis data must have the same length")
        if not isinstance(self._metadata, dict):
            self._metadata = dict()

    def divide(self, divider: Union[int, float]):
        """Divide intensity array by specified divider"""
        if not isinstance(divider, (int, float)):
            raise ValueError("Division factor must be an integer or a float")
        self._y /= divider
        return self

    def get_x_at_loc(self, x_min: float, x_max: float, get_max: bool = True):
        """Get x-axis value information for specified x-axis region of interest"""
        x_idx_min, x_idx_max = find_nearest_index(self.x, [x_min, x_max])
        y = self.y[x_idx_min : x_idx_max + 1]
        y_idx = y.argmax()
        x = self.x[x_idx_min : x_idx_max + 1][y_idx]
        return x, y[y_idx]

    def get_y_at_loc(self, x_min: float, x_max: float, get_max: bool = True):
        """Get intensity information for specified x-axis region of interest"""
        x_idx_min, x_idx_max = find_nearest_index(self.x, [x_min, x_max])
        y = self.y[x_idx_min : x_idx_max + 1]
        if get_max:
            return float(y.max())
        return y

    def get_x_at_max(self):
        """Get position at maximum intensity value"""
        return self.get_x_at_loc(*self.x_limit)

    def get_x_window(self, x_min: float, x_max: float):
        """Crop signal to defined x-axis region without setting it in the object"""
        x, y = pr_spectra.crop_1D_data(self.x, self.y, x_min, x_max)
        return x, y

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
            if `True`, spectral cropping will occur
        linearize : bool
            if `True`, spectrum will be linearized
        smooth : bool
            if `True`, spectrum will be smoothed
        baseline : bool
            if `True`, baseline will be removed from the mass spectrum
        normalize: bool
            if `True`, spectrum will be normalized to 1
        kwargs : Dict[Any, Any]
            dictionary containing processing parameters

        Returns
        -------
        self : SpectrumObject
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
            self.normalize()
        return self

    def normalize(self):
        """Normalize spectrum to 1"""
        self._y = pr_spectra.normalize_1D(self.y)
        self.unsaved = True
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
        self.unsaved = True
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
        self._x, self._y = pr_spectra.linearize_data(
            self.x,
            self.y,
            bin_size=bin_size,
            linearize_method=linearize_method,
            auto_range=auto_range,
            x_min=x_min,
            x_max=x_max,
            x_bin=x_bin,
        )
        self.unsaved = True
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
        self._y = pr_spectra.smooth_1d(
            self.y, smooth_method=smooth_method, sigma=sigma, window_size=window_size, poly_order=poly_order, N=N
        )
        self.unsaved = True
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
        self._y = pr_spectra.baseline_1d(
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
        self.unsaved = True
        return self


class MassSpectrumObject(SpectrumObject):
    """Mass spectrum container object"""

    DOCUMENT_KEY = "MassSpectra"

    def __init__(
        self, x, y, name: str = "", metadata=None, extra_data=None, x_label="m/z (Da)", y_label="Intensity", **kwargs
    ):
        super().__init__(
            x, y, x_label=x_label, y_label=y_label, name=name, metadata=metadata, extra_data=extra_data, **kwargs
        )

        # set default options
        self.options["remove_zeros"] = True

    @property
    def has_unidec_result(self):
        """Check whether object has UniDec results"""
        return self.get_metadata("has_unidec", False)

    def set_unidec_result(self, unidec_results_obj, flush: bool = True):
        """Set UniDec results in the document"""
        if not hasattr(unidec_results_obj, "to_zarr"):
            raise ValueError("Could not set UniDec results in the data object")
        self.add_group("UniDec", *unidec_results_obj.to_zarr())
        self.add_metadata("has_unidec", True)
        if flush:
            self.flush()

    def del_unidec_result(self):
        """Remove UniDec results from the document"""
        # TODO: implemente a method to delete existing data
        if not self.has_unidec_result:
            return
        self.add_metadata("has_unidec", False)

    def get_unidec_result(self):
        """Get UniDec results"""
        from origami.widgets.unidec.processing.containers import unidec_results_object

        if not self.has_unidec_result:
            return None
        group = self.get_group("UniDec")
        if group is None:
            raise ValueError("Could not UniDec data")
        return unidec_results_object(self, group)


class ChromatogramObject(SpectrumObject, ChromatogramAxesMixin, OrigamiMsMixin):
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
        self._y, self._x, start_end_cv, parameters = self._apply_origami_ms(self.y)

        # set extra data
        self.x_label = "Collision Voltage (V)"
        self._extra_data["oms_ss_es_cv"] = start_end_cv
        self._metadata["origami_ms"] = parameters

        # get new title
        self.title = self.title + " [CIU]"
        self.flush()
        return self


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
