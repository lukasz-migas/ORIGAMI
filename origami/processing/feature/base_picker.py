# Standard library imports
import os
import time
import logging
from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple
from typing import Union
from typing import Callable

# Third-party imports
import numpy as np

# Local imports
from origami.readers.io_json import read_json_data
from origami.readers.io_json import write_json_data
from origami.utils.utilities import format_time
from origami.processing.feature.metrics import compute_slopes
from origami.processing.feature.metrics import compute_asymmetricity_and_tailing
from origami.processing.feature.peak_set import Peak
from origami.processing.feature.peak_set import PeakSet
from origami.processing.feature.utilities import group_by

COLOR_METRICS = ["width"]
SCORE_METRICS = ["asymmetry", "tailing", "slopes"]
GOOD_COLOR = "#98FB98"
BAD_COLOR = "#FFCCCB"

LOGGER = logging.getLogger(__name__)


# TODO: add iter and next dunders


class BasePicker(ABC):
    """Base class for all peak pickers"""

    def __init__(self, x, y) -> None:
        if len(x) != len(y):
            raise ValueError("The lengths of 'x' and 'y' vector must be the same.")
        self._x_array = np.asarray(x)
        self._y_array = np.asarray(y)

        self._peaks = None
        self._locked = False
        self._verbose = False

        # data attributes
        self._kwargs: Dict = dict()
        self._processing: List = list()

    def __repr__(self):
        return f"{self.__class__.__name__}<{len(self._x_array)} points; {self.n_peaks} peaks; locked={self.locked}>"

    def __getitem__(self, item):
        return self._peaks[item]
        # if isinstance(item, slice):
        #     return PeakSet(self._peaks[item])
        # return self._peaks[item]

    @abstractmethod
    def find_peaks(self, *args, **kwargs):
        """Find features in spectrum"""
        raise NotImplementedError("Must implement method")

    @property
    def locked(self):
        """Get lock state of the picker"""
        return self._locked

    @locked.setter
    def locked(self, value):
        """Set picker as locked"""
        self._locked = value

    @property
    def x_array(self):
        """Return the x-axis of the spectrum"""
        return self._x_array

    @x_array.setter
    def x_array(self, value):
        """Set x-axis of the spectrum"""
        self._x_array = value

    @property
    def y_array(self):
        """Return the y-axis of the spectrum"""
        return self._y_array

    @y_array.setter
    def y_array(self, value):
        """Set the y-axis of the spectrum"""
        self._y_array = value

    @property
    def n_peaks(self):
        """Get number of peaks in the :class: PeakSet"""
        return 0 if self._peaks is None else len(self._peaks)

    @property
    def x_window(self):
        """Retrieve extraction windows"""
        return np.asarray([peak.x_left for peak in self._peaks]), np.asarray([peak.x_right for peak in self._peaks])

    @property
    def xy(self):
        """Get m/z values and intensities"""
        return np.asarray([peak.x for peak in self._peaks]), np.asarray([peak.y for peak in self._peaks])

    @property
    def x(self):
        """Get m/z values for all peaks"""
        return np.asarray([peak.x for peak in self._peaks])

    @property
    def y(self):
        """Get intensity values for all peaks"""
        return np.asarray([peak.y for peak in self._peaks])

    @property
    def x_min_edge(self):
        """Get left-hand side edge m/z values for all peaks"""
        return np.asarray([peak.x_left for peak in self._peaks])

    @property
    def x_max_edge(self):
        """Get right-hand side edge m/z values for all peaks"""
        return np.asarray([peak.x_right for peak in self._peaks])

    @property
    def x_width(self):
        """Get full-width half max for all peaks"""
        return np.asarray([peak.x_width for peak in self._peaks])

    @property
    def idx_window(self):
        """Get left- and right-hand side indices for all peaks"""
        return np.asarray([peak.idx_left for peak in self._peaks]), np.asarray([peak.idx_right for peak in self._peaks])

    @property
    def idx_min(self):
        """Get left-hand side indices for all peaks"""
        return np.asarray([peak.idx_left for peak in self._peaks])

    @property
    def idx_max(self):
        """Get right-hand side indices for all peaks"""
        return np.asarray([peak.idx_right for peak in self._peaks])

    @property
    def idx_width(self):
        """Get full-width half max for all peaks (in index units)"""
        return np.asarray([peak.idx_fwhm for peak in self._peaks])

    @property
    def idx_value(self):
        """Get full-width half max for all peaks (in index units)"""
        return np.asarray([peak.idx for peak in self._peaks])

    @property
    def height(self):
        """Alias for `y`"""
        return self.y

    @property
    def width(self):
        """Alias for `x_width`"""
        return self.x_width

    @property
    def colors(self):
        """Get color for all peaks"""
        return [peak.color for peak in self._peaks]

    @property
    def scores(self):
        """Get score/class for all peaks"""
        return np.asarray([peak.score for peak in self._peaks], dtype=np.float32)

    def copy(self):
        """Return copy of self"""
        from copy import deepcopy

        return deepcopy(self)

    def _get_filter_indices(self, key: str, criteria: Union[List, Tuple, str]):
        """Determines the indices which fall within the criteria range for particular attribute specified by the `key`
        parameter


        Parameters
        ----------
        key : str
            attribute by which the peaks should be filtered
        criteria : Union[List, Tuple, str]
            two-element list/tuple that specifies the min/max range by which to select the peaks. The criteria are
            inclusive, meaning that if the criteria is [5, 15] then any peak that matches the value 5 or 15 will be
            included

        Returns
        -------
        indices : List
            list of indices where the criteria were True

        """
        assert isinstance(key, str)

        array = np.asarray([getattr(peak, key) for peak in self._peaks])
        if isinstance(criteria, (list, tuple)):
            indices = np.argwhere(np.logical_and(array >= criteria[0], array <= criteria[1]))
        elif isinstance(criteria, str):
            indices = np.argwhere(array == criteria)
        else:
            raise ValueError("Could not understand the specified criteria")

        return indices.flatten().tolist()

    def _get_func_indices(self, func: Callable, *args: Any):
        """
        Parameters
        ----------
        func: Callable
            function to call which should take as the first argument instance of `Peak` and any arguments and return
            a iterable object where the first element is a `bool`. If the first element is `True`, the peak is kept
            and if `False` it is removed from the peaklist
        args : Any
            any arguments to be passed to the `func`

        Returns
        -------
        indices : List
            list of indices where the criteria were True

        """
        indices = []
        for i, peak in enumerate(self):
            results = func(peak, *args)
            if results[0]:
                indices.append(i)

        return indices

    def clean_by(self, key: str, criteria: Union[List, Tuple, str]):
        """Selects a subset of peaks that fall within the criteria range for particular attribute

        Parameters
        ----------
        key : str
            attribute by which the peaks should be filtered
        criteria : Union[List, Tuple, str]
            two-element list/tuple that specifies the min/max range by which to select the peaks. The criteria are
            inclusive, meaning that if the criteria is [5, 15] then any peak that matches the value 5 or 15 will be
            included in the resulting PeakSet
        """
        indices = self._get_filter_indices(key, criteria)
        LOGGER.debug(f"Removed {self.n_peaks-len(indices)} peaks [key={key}; criteria={criteria}]")
        self.set_from_peak_set(self[indices])
        self.add_processing_step("clean_by", {"key": key, "criteria": criteria})

    def clean_by_func(self, func: Callable, *args):
        """Filter data by iterating over the peaklist and calling a callable function which indicates whether peak
        should be kept or removed

        Parameters
        ----------
        func: Callable
            function to call which should take as the first argument instance of `Peak` and any arguments and return
            a iterable object where the first element is a `bool`. If the first element is `True`, the peak is kept
            and if `False` it is removed from the peaklist
        args : Any
            any arguments to be passed to the `func`
        """
        indices = self._get_func_indices(func, *args)
        LOGGER.debug(f"Removed {self.n_peaks - len(indices)} peaks")
        self.set_from_peak_set(self[indices])
        self.add_processing_step("clean_by_func", {"func": func.__name__, "args": "Could not parse data"})

    def filter_by(self, key: str, criteria: Union[List, Tuple, str]):
        """Returns a new instance of the peak picker with peaks filtered by `key` and within the criteria ranges

        The method determines which peaks fall within the criteria range and then iteratively selects those peaks
        and returns them in a new instance of the peak picker

        Parameters
        ----------
        key : str
            attribute by which the peaks should be filtered
        criteria : Union[List, Tuple, str]
            two-element list/tuple that specifies the min/max range by which to select the peaks. The criteria are
            inclusive, meaning that if the criteria is [5, 15] then any peak that matches the value 5 or 15 will be
            included in the resulting PeakSet

        Returns
        -------
        copy of self
            copy of the current peak picker with new peak set
        """
        indices = self._get_filter_indices(key, criteria)
        LOGGER.debug(f"Filtered out {self.n_peaks - len(indices)} peaks [key={key}; criteria={criteria}]")
        return self.copy().set_from_peak_set(self[indices])

    def filter_by_func(self, func: Callable, *args):
        """Filter data by iterating over the peaklist and calling a callable function which indicates whether peak
        should be kept or removed

        Parameters
        ----------
        func: Callable
            function to call which should take as the first argument instance of `Peak` and any arguments and return
            a iterable object where the first element is a `bool`. If the first element is `True`, the peak is kept
            and if `False` it is removed from the peaklist
        args : Any
            any arguments to be passed to the `func`

        Returns
        -------
        copy of self
            copy of the current peak picker with new peak set
        """
        indices = self._get_func_indices(func, *args)
        LOGGER.debug(f"Filtered out {self.n_peaks - len(indices)} peaks")
        return self.copy().set_from_peak_set(self[indices])

    def fix_y(self):
        """Helper method to fix the intensity of peak(s) after some operation"""
        if not isinstance(self._y_array, np.ndarray):
            raise ValueError("Cannot perform action")

        for peak in self:
            peak.y = self._y_array[peak.idx]

    def remove(self, indices):
        """Delete peaks from dataset"""
        self._peaks.remove(indices)

    def sort_by(self, key: str, order: str):
        """Sort peaks based on a key and order specification"""
        self._peaks.reindex(key, order)

    def sort_by_x(self):
        """Sort peaks by the m/z value in an ascending order"""
        self.sort_by("x", "ascending")

    def sort_by_y(self):
        """Sort peaks by the intensity in an descending order"""
        self.sort_by("y", "descending")

    def add_processing_step(self, method: str, parameters: Any):
        """Sets all processing parameters associated with this fitter than can later be exported as a json file"""
        self._processing.append({method: parameters})

    def reset_processing_steps(self):
        """Resets all processing steps"""
        self._processing = list()

    def save_processing_steps(self, path: str):
        """Export processing steps as JSON file"""
        if not path.endswith(".json"):
            path = os.path.join(path, "picker-config.json")

        if self._processing:
            write_json_data(path, self._processing, check_existing=False)

    def save(self, path, overwrite: bool = False, **kwargs):
        """Export peaks to JSON file

        Parameters
        ----------
        path : str
            path to where the peaklist should be saved to
        overwrite : bool
            if `True`, existing data will be overwritten, otherwise it will be merged
        kwargs : Any
            any key;value pair that can be exported as a JSON file
        """

        export_list = []
        for peak in self:
            peak_dict = peak.as_dict()
            peak_dict.update(**kwargs)
            export_list.append(peak_dict)
        write_json_data(path, export_list, check_existing=not overwrite)

    def restore(self, path):
        """Restores peaks from JSON file"""
        import_list = read_json_data(path)
        self.set_from_list(import_list)

    def save_peaks(self, dataset_dir, export_dir, mz_x_offset, path=None, overwrite: bool = False):
        """Export peaks to JSON file with several attributes used during the extraction process

        Parameters
        ----------
        dataset_dir : str
            path to the dataset containing raw data
        export_dir : str
            path to the directory where data should be saved to
        mz_x_offset : int
            m/z offset value used to calculate the index position during extraction
        path : Optional[str[
            output path - if value is not provided, the `export_dir` and filename `export-list.json` will be used
            instead
        overwrite : bool
            if `True`, existing data will be overwritten, otherwise it will be merged
        """
        if path is None:
            path = os.path.join(export_dir, "export-list.json")

        self.save(
            path,
            dataset_dir=dataset_dir,
            export_dir=export_dir,
            applied_offset=False,
            x_offset=mz_x_offset,
            overwrite=overwrite,
        )
        LOGGER.info(f"Exported extraction list to {path}")

    def score(self, metric: str = "asymmetry", reorder: bool = True):
        """Computes score for each peak and sets its value"""
        if not isinstance(self._x_array, np.ndarray):
            raise ValueError("Please provide x-axis array")
        if not isinstance(self._y_array, np.ndarray):
            raise ValueError("Please provide y-axis array")

        if metric not in SCORE_METRICS:
            raise ValueError(
                f"metric=`{metric}` cannot be computed - please use one of these instead `{SCORE_METRICS}`"
            )

        if metric in ["asymmetry", "tailing"]:
            afs, tfs = compute_asymmetricity_and_tailing(self._y_array, self.idx_value)
            if metric == "asymmetry":
                self.set_attribute("score", afs)
            elif metric == "tailing":
                self.set_attribute("score", tfs)
        elif metric in ["slope"]:
            slopes = compute_slopes(self._x_array, self._y_array, self)
            self.set_attribute("score", slopes)
        elif metric in ["width"]:
            pass

        if reorder:
            self._peaks.reindex("score", True)

        # set processing parameters
        self.add_processing_step("score", {"metric": metric, "reorder": reorder})

    # def color_peaks(self, metric: str = "width") -> Tuple[List[str], List[str]]:
    #     """Color peaks based on some sort of metric"""
    #     if metric not in COLOR_METRICS:
    #         raise ValueError("Cannot color peaks")
    #
    #     if metric == "width":
    #         colors, scores = self._color_peaks(self._color_peaks_by_width, self.idx_width)
    #     else:
    #         raise ValueError(f"`{metric}` not supported yet")
    #
    #     # self.set_parameters(scoring_metric=metric)  # type: ignore
    #     return colors, scores
    #
    # def _color_peaks(self, fcn, values: Iterable) -> Tuple[List[str], List[str]]:
    #     """Annotate each peak based on some metric
    #
    #     If the metric says the peak is 'poor' it will be colored in a light-red shade and if the peak is 'good' it
    #     will
    #     be shown in light-green
    #     """
    #     colors, scores = fcn(values)
    #
    #     self.set_attribute("color", colors)
    #     self.set_attribute("score", scores)
    #     return colors, scores
    #
    # @staticmethod
    # def _color_peaks_by_width(values: Iterable):
    #     def get_color_scale(
    #         _scale_range: Union[np.ndarray, List], min_good: int = 4, max_good: int = 12
    #     ) -> Tuple[Dict[int, str], Dict[int, str]]:
    #
    #         # setup colors
    #         color_range = dict.fromkeys(_scale_range, BAD_COLOR)
    #         _estimate_range = dict.fromkeys(_scale_range, "bad")
    #
    #         for idx in np.where((_scale_range >= min_good) & (_scale_range <= max_good))[0]:  # type: ignore
    #             scale_idx = _scale_range[idx]
    #             color_range[scale_idx] = GOOD_COLOR
    #             _estimate_range[scale_idx] = "good"
    #
    #         return color_range, _estimate_range
    #
    #     # assign colors
    #     colors: List = []
    #     scores: List = []
    #
    #     # generate scale range
    #     try:
    #         scale_range = np.arange(np.min(values) - 1, np.max(values) + 1)
    #     except ValueError:
    #         return colors, scores
    #
    #     # get scale -> range match-up
    #     color_scales, estimate_range = get_color_scale(scale_range, 2, 16)
    #
    #     for width in values:
    #         colors.append(color_scales[width])
    #         scores.append(estimate_range[width])
    #
    #     return colors, scores
    #
    # def fix_peak(self, peak_id: int, data: Dict[str, Any]) -> bool:
    #     """Fix peak by re-adjusting values in the peak store
    #
    #     Parameters
    #     ----------
    #     peak_id : int
    #         peak index
    #     data : Dict[str, Union[int, float]]
    #         dictionary containing data to be updated in the picker
    #
    #     Returns
    #     -------
    #     success : bool
    #         if data was successfully updated, True will be returned
    #
    #     Raises
    #     ------
    #     IndexError
    #         If the 'row_idx' value larger than the number of peaks, an error will be thrown
    #     ValueError
    #         If the 'data' does not containing necessary fields
    #     """
    #     # TODO: remove the min mz/max mz values
    #     # def find_value(array, value):
    #     #     return np.where(array == value)[0].tolist()
    #
    #     if peak_id > self.n_peaks:
    #         raise IndexError("Index value of the value is too large")
    #
    #     changed = data.get("changed")
    #
    #     if not changed:
    #         LOGGER.warning("Could not update peak data")
    #         return False
    #
    #     # peak = self[peak_id]
    #     peak_data = dict()
    #
    #     # index was changed so we have to adjust width, and x values
    #     if "idx" in changed and all([val in data for val in ["min_idx", "max_idx"]]):
    #         min_idx, max_idx = data["min_idx"], data["max_idx"]
    #         min_mz, max_mz = self._x_array[[min_idx, max_idx]].tolist()
    #         idx_width = max_idx - min_idx
    #
    #     # x value(s) were changed so we have to adjust index and widths
    #     elif "mz" in changed and all([val in data for val in ["min_mz", "max_mz"]]):
    #         min_mz, max_mz = data["min_mz"], data["max_mz"]
    #         min_idx, max_idx = find_nearest_index(self._x_array, min_mz), find_nearest_index(self._x_array, max_mz)
    #         min_mz = self._x_array[min_idx]
    #         max_mz = self._x_array[max_idx]
    #         idx_width = max_idx - min_idx
    #     else:
    #         return False
    #
    #     if any([val is None for val in [idx_width, min_mz, max_mz, min_idx, max_idx]]):
    #         LOGGER.warning("Could not update peak data")
    #         return False
    #
    #     # update data for particular row
    #     peak_data.update(dict(idx_fwhm=idx_width, x_left=min_mz, x_right=max_mz, idx_left=min_idx, idx_right=max_idx))
    #
    #     # update score and color
    #     if self._kwargs.get("scoring_metric"):
    #         color, score = self._color_peaks_by_width([idx_width])
    #         peak_data.update(color=color[0], score=score[0])
    #     self.update_peak(peak_id, peak_data)
    #
    #     return True

    def merge_nearby(self, tolerance: float, n_passes: int = 3):
        """Merge peaks that are within certain tolerance together. This is mostly convenient when trying to compute
        peaks from several spectra and trying to remove peaks that are within small distance from each other

        How the algorithm works:
            1. Group peaks together that fall within the `tolerance` window.
            2. Merge the peaks in each group and generate a new instance of `Peak` object that represents the peaks
                that were merged. If a group consists of three peaks, then the algorithm will determine the peak
                width based on all peaks (determines the minimum/maximum from the provided range), computes the y-axis
                apex (between the minimum/maximum widths) and assigns the x-axis values.
            3. Peaks from each group are deleted from the `PeakSet`
            4. New peak is added
            5. If the `n_passes` is larger than 1, the algorithm will be repeated `n_passes`. If the number of groups
                is 0, the algorithm will exit early.

        Parameters
        ----------
        tolerance : float
            x tolerance in base units
        n_passes : int, optional
            number of iterations the algorithm should be run - after single pass, it is possible that there might
            be several peaks that were merged and then fitted inside the same tolerance. If the `tolerance` value is
            small (e.g. < 0.01) then it might be necessary to repeat the merge more than 3 times.
        """
        for _ in range(n_passes):
            t_start = time.time()
            count, n_groups = self._merge_nearby(tolerance)
            LOGGER.debug(
                f"Merged {count} -> {n_groups} with tolerance {tolerance} in {format_time(time.time()-t_start)}"
            )
            if not n_groups:
                break

        # set processing parameters
        self.add_processing_step("merge_nearby", {"tolerance": tolerance, "n_passes": n_passes})

    def _merge_nearby(self, tolerance: float):
        """Merge peaks that are within certain tolerance together. This is mostly convenient when trying to compute
        peaks from several spectra and trying to remove peaks that are within small distance from each other

        Parameters
        ----------
        tolerance : float
            x tolerance in base units
        """
        # ensure the x-axis is correctly ordered first!
        self._peaks.reindex(key="x", reverse=True, set_keys=False)
        # get the x-axis of the picker
        array = np.asarray(self.x)

        # group peaks together
        # group must be ordered in a DESCENDING order, otherwise the underlying list container will have a fit
        groups = group_by(array, tolerance)
        # iterate over each group and merge peaks for particular peak together
        count = 0
        for group in groups:
            # merge multiple peaks together
            peak = self._merge_peaks(self._x_array, self._y_array, [self[_peak] for _peak in group])
            count += len(group)

            # remove group of peaks
            self._peaks.remove(group)

            # add merged peak
            self._peaks.add([peak])
        # reindex peaks
        self._peaks.reindex()
        return count, len(groups)

    @staticmethod
    def _merge_peaks(x: np.ndarray, y: np.ndarray, peaks: List[Peak]):
        """Merge several peaks together

        Multiple peaks are merged together by computing the x-axis and index ranges based on all peaks. This is done
        by extracting the index left/right from each peak and computing the minimum/maximum values. Subsequently, the
        minimum/maximum values of the peak (in x space) are calculated. Then, we calculate the peak intensity and
        actual peak position.

        Parameters
        ----------
        x : np.ndarray
            x values
        y : np.ndarray
            intensity values
        peaks : List[Peak]
            list of peaks to join together

        Returns
        -------
        peak : Peak
            newly created peak based on the list of peaks
        """
        # find left/right index for width of the peak
        idx_left = np.min([peak.idx_left for peak in peaks])
        idx_right = np.max([peak.idx_right for peak in peaks])
        idx_fwhm = abs(idx_right - idx_left)

        # find x values corresponding to the index
        x_left = np.min([peak.x_left for peak in peaks])
        x_right = np.max([peak.x_right for peak in peaks])
        x_fwhm = abs(x_right - x_left)

        # find max x/y intensity in the range
        _idx = y[idx_left:idx_right].argmax()
        _x = x[idx_left:idx_right][_idx]
        _y = y[idx_left:idx_right][_idx]
        idx = range(idx_left, idx_right)[_idx]
        score = 100
        if idx == idx_left or idx == idx_right:
            score = 0

        return Peak(
            x=_x,
            y=_y,
            x_left=x_left,
            x_right=x_right,
            idx=idx,
            idx_left=idx_left,
            idx_right=idx_right,
            x_fwhm=x_fwhm,
            idx_fwhm=idx_fwhm,
            area=_y,
            signal_to_noise=1,
            score=score,
        )

    @staticmethod
    @abstractmethod
    def get_from_dict(found_peaks: Dict) -> PeakSet:
        """Generate `PeakSet` from dictionary of peaks"""
        raise NotImplementedError("Must implement method")

    def set_from_dict(self, found_peaks: Dict):
        """Set peaks and perform various checks. The input is typically dictionary with various peak properties
        that are ordered"""
        peak_data = self.get_from_dict(found_peaks)

        self._peaks = peak_data

    @staticmethod
    def get_from_list(peak_list: List) -> PeakSet:
        """Generate `PeakSet` from list of dicts of peaks.

        Parameters
        ----------
        peak_list : List[Dict]
            list of dictionaries containing peak information. Each dict inside the list must have several parameters,
            including: `x, y, x_left, x_right, idx_left, idx_right, idx`. The remaining parameters can be ignored as
            they can be calculated by the `Peak` init method.

        Returns
        -------
        peak_set : PeakSet
            initialized PeakSet based on the list of dictionaries
        """

        peak_data = []
        for peak_id, peak_dict in enumerate(peak_list):
            peak_data.append(
                Peak(
                    x=peak_dict.pop("x"),
                    y=peak_dict.pop("y"),
                    x_left=peak_dict.pop("x_left"),
                    x_right=peak_dict.pop("x_right"),
                    idx_left=peak_dict.pop("idx_left"),
                    idx_right=peak_dict.pop("idx_right"),
                    idx=peak_dict.pop("idx"),
                    x_fwhm=peak_dict.pop("x_width"),
                    idx_fwhm=peak_dict.pop("idx_fwhm"),
                    area=peak_dict.pop("area"),
                    signal_to_noise=peak_dict.pop("signal_to_noise"),
                    peak_id=peak_dict.pop("peak_id"),
                    score=peak_dict.pop("score"),
                    color=peak_dict.pop("color"),
                )
            )
        return PeakSet(peak_data)

    def set_from_list(self, peak_list: List):
        """Set peaks and perform various checks. The input is typically a list if dicts with appropriate peak properties
        """
        peak_data = self.get_from_list(peak_list)

        self._peaks = peak_data

    def set_from_peak_set(self, peak_set: PeakSet):
        """Sets peaks from PeakSet and returns self"""
        self._peaks = peak_set
        return self

    def set_attribute(self, key, values):
        """Iterate over values and set attribute"""
        if len(values) != self.n_peaks:
            raise ValueError("Cannot set attribute for all peaks since the dimensions do not match!")

        for peak_id in range(self.n_peaks):
            setattr(self._peaks[peak_id], key, values[peak_id])

    def update_peak(self, peak_id, values):
        """Iterate over values for certain peak and update the value"""
        for key, value in values.items():
            setattr(self._peaks[peak_id], key, value)

        # update order after changing of values
        self._peaks.reindex()

    def get(self, x: float, tolerance: float = 1e-4):
        """Get nearest peak within specified tolerance window"""
        return self._peaks.has_peak(x, tolerance)
