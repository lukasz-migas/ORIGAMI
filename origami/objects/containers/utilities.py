# Standard library imports
import os
import logging
from abc import ABC
from abc import abstractmethod
from typing import Dict
from typing import List
from typing import Tuple
from typing import Optional

# Third-party imports
import numpy as np
from zarr import Array
from zarr import Group

# Local imports
from origami.processing import origami_ms

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

        Parameters
        ----------
        to_label : str
            new axis label of the object
        scan_time : float, optional
            scan time to be used throughout the conversion
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
                parent = self.get_parent()
                if parent:
                    _scan_time = parent.parameters.get("scan_time", None)
            if _scan_time is None or _scan_time <= 0:
                raise ValueError("Cannot perform conversion due to a missing `scan_time` information.")
            return _scan_time

        min_labels = ["Time (mins)", "Retention time (mins)"]
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

        if to_label in min_labels and current_label == "Scans":
            if min_key in extra_data:
                new_values = extra_data[min_key]
            else:
                new_values = extra_data[bin_key]
                new_values = new_values * (_get_scan_time(scan_time) / 60)
        elif to_label == "Scans" and current_label in min_labels:
            if bin_key in extra_data:
                new_values = extra_data[bin_key]
            else:
                new_values = current_values
                new_values = np.round((new_values * 60) / _get_scan_time(scan_time)).astype(np.int32)
        elif check_alternative_names(current_label, to_label, min_labels):
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

        Parameters
        ----------
        to_label : str
            new axis label of the object
        pusher_freq : float, optional
            pusher frequency time to be used throughout the conversion
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
                parent = self.get_parent()
                if parent:
                    _pusher_freq = parent.parameters.get("pusher_freq", None)
            if _pusher_freq is None or _pusher_freq <= 0:
                raise ValueError("Cannot perform conversion due to a missing `pusher_freq` information.")
            return _pusher_freq

        ms_labels = ["Drift time (ms)", "Arrival time (ms)"]
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

        if to_label in ms_labels and current_label == "Drift time (bins)":
            if ms_key in extra_data:
                new_values = extra_data[ms_key]
            else:
                new_values = extra_data[bin_key]
                new_values = new_values * (_get_pusher_freq(pusher_freq) / 1000)
        elif to_label == "Drift time (bins)" and current_label in ms_labels:
            if bin_key in extra_data:
                new_values = extra_data[bin_key]
            else:
                new_values = current_values
                new_values = np.round((new_values * 1000) / _get_pusher_freq(pusher_freq)).astype(np.int32)
        elif check_alternative_names(current_label, to_label, ms_labels):
            new_values = current_values
        else:
            raise ValueError("Cannot convert x-axis")

        # set data
        return to_label, new_values

    @abstractmethod
    def get_parent(self):  # noqa
        raise NotImplementedError("Must implement method")


class OrigamiMsMixin(ABC):
    """Mixin used to convert heatmap array to ORIGAMI-MS format"""

    array = None

    @abstractmethod
    def get_parent(self):  # noqa
        raise NotImplementedError("Must implement method")

    def _change_rt_cv_axis(
        self,
        to_label: str,
        charge: Optional[int],
        metadata: Dict,
        extra_data: Dict,
        label_options: List[str],
        current_label: str,
        current_values: np.ndarray,
        default_label_key: str,
        cv_key: str,
        ev_key: str,
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

        Parameters
        ----------
        to_label : str
            new axis label of the object
        charge : float, optional
            charge of the ion/object to be used throughout the conversion
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
        cv_key : str
            key by which the time axis values can be accessed (e.g. `x_min`)
        ev_key : str
            key by which the bin axis values can be accessed (e.g. `x_bin`)

        Returns
        -------
        to_label : str
            new axis label of the object
        new_values : np.ndarray
            new axis values of the object
        """

        def _get_charge(_charge):
            # no need to change anything
            if _charge is None:
                _charge = metadata.get("charge", 1)
            if _charge is None:
                raise ValueError("Cannot perform conversion due to a missing `charge` information.")
            return _charge

        cv_labels = ["Collision Voltage (V)", "Activation Voltage (V)", "Activation Energy (V)"]
        ev_labels = ["Lab Frame Energy (eV)", "Activation Voltage (eV)", "Activation Energy (eV)"]
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
        if current_label in ["Collision Voltage (V)", "Activation Voltage (V)"]:
            extra_data[cv_key] = current_values
        elif current_label in ["Lab Frame Energy (eV)", "Activation Voltage (eV)"]:
            extra_data[ev_key] = current_values

        if to_label in ev_labels and current_label in cv_labels:
            if ev_key in extra_data:
                new_values = extra_data[ev_key]
            else:
                new_values = extra_data[cv_key]
                new_values = new_values * _get_charge(charge)
        elif to_label in cv_labels and current_label in ev_labels:
            if cv_key in extra_data:
                new_values = extra_data[cv_key]
            else:
                new_values = extra_data[ev_key]
                new_values = new_values / _get_charge(charge)
        elif check_alternative_names(current_label, to_label, cv_labels) or check_alternative_names(
            current_label, to_label, ev_labels
        ):
            new_values = current_values
        else:
            raise ValueError("Cannot convert x-axis")

        # set data
        return to_label, new_values

    def _apply_origami_ms(self, array: np.ndarray):
        """Apply ORIGAMI-MS settings on the heatmap object"""

        def _get_parameters(_origami_ms_config):
            # no need to change anything
            if _origami_ms_config is None:
                parent = self.get_parent()
                if parent:
                    _origami_ms_config = parent.get_config("origami_ms")
            if _origami_ms_config is None:
                raise ValueError("Cannot perform conversion due to a missing `origami-ms` information.")
            if not isinstance(_origami_ms_config, dict):
                raise ValueError("ORIGAMI-MS parameters are in incompatible format")
            return _origami_ms_config

        # get ORIGAMI-MS parameters
        oms_config = _get_parameters(None)

        # # data must be converted in such a way as to give a summed array and reduced number of x-axis values
        array, x, start_end_cv_list, parameters = origami_ms.convert_origami_ms(array, **oms_config)

        return array, x, start_end_cv_list, parameters


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


def get_output_fmt(delimiter: str) -> str:
    """Get appropriate file ending for a delimiter"""
    return {",": ".csv", "\t": ".txt", " ": ".txt"}.get(delimiter, ".csv")


def check_output_path(path: str, delimiter: str) -> str:
    """Check whether output file has appropriate extension"""
    _, ext = os.path.splitext(path)
    if not ext or ext not in [".csv", ".txt", ".tab"]:
        ext = get_output_fmt(delimiter)
        path = path + ext
    return path


def check_alternative_names(current_label, to_label, alternative_labels):
    """Checks whether the current label and the new label are alternatives of each other"""
    if current_label in alternative_labels and to_label in alternative_labels:
        return True
    return False


def get_extra_data(group: Group, known_keys: List):
    """Get all additional metadata that has been saved in the group store"""
    extra_keys = list(set(group.keys()) - set(known_keys))
    extra_data = dict()
    for key in extra_keys:
        _data = group[key]
        if isinstance(_data, Array):
            extra_data[key] = _data[:]
    return extra_data
