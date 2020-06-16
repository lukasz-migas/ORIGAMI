# This module is heavily inspired by the excellent `ms_peak_picker` library
# https://github.com/mobiusklein/ms_peak_picker/blob/master/ms_peak_picker/peak_set.py

# Standard library imports
import logging
import operator
from copy import deepcopy
from typing import List

# Third-party imports
import numpy as np
from natsort import natsorted

# Local imports
from origami.processing.utils import ppm_error

LOGGER = logging.getLogger(__name__)


class Peak:
    """Represent a single centroided mass spectral peak.

    Attributes
    ----------
    x : float
        The m/z value at which the peak achieves its maximal abundance
    y : float
        The apex height of the peak
    idx : int
        The index at which the peak was found in the m/z array it was picked from
    x_fwhm : double
        The symmetric full width at half of the
        peak's maximum height
    idx_fwhm : int
        The symmetric full width at half of the
        peak's maximum height
    area : float
        The total area of the peak, as determined by trapezoid integration
    signal_to_noise : float
        The signal to noise ratio of the peak
    x_left : float
        The left-sided width at half of max
    x_right : float
        The right-sided width at half of max
    idx_left : int
        The left-sided index at half of max
    idx_right : int
        The right-sided index at half of max
    peak_id : int
        peak index in the :class: PeakSet
    score : any, optional
        peak score of any kind (e.g. str for good/bad classification)
    color : str. optional
        color of the peak (can be used by other applications to indicate peak information)
    """

    __slots__ = [
        "x",
        "y",
        "idx",
        "signal_to_noise",
        "area",
        "x_fwhm",
        "x_left",
        "x_right",
        "idx_fwhm",
        "idx_left",
        "idx_right",
        "peak_id",
        "score",
        "color",
    ]

    def __init__(
        self,
        x,
        y,
        idx,
        x_left,
        x_right,
        idx_left,
        idx_right,
        x_fwhm=None,
        idx_fwhm=None,
        area=None,
        signal_to_noise=0,
        peak_id=0,
        score=100,
        color=None,
    ):
        # compulsory attributes
        self.x = x
        self.y = y
        self.x_left = x_left
        self.x_right = x_right
        self.idx = idx
        self.idx_left = idx_left
        self.idx_right = idx_right
        self.x_fwhm = x_right - x_left if x_fwhm is None else x_fwhm
        self.idx_fwhm = idx_right - idx_left if idx_fwhm is None else idx_fwhm

        # optional attributes
        self.area = y if area is None else area
        self.signal_to_noise = signal_to_noise
        self.score = score
        self.color = color
        self.peak_id = peak_id

    def __hash__(self):
        return hash(self.x)

    def __eq__(self, other):
        """Checks for equality between two peaks. Takes into account the m/z value, s/n and peak width"""
        if other is None:
            return False
        return (
            (abs(self.x - other.x) < 1e-5)
            and (abs(self.signal_to_noise - other.signal_to_noise) < 1e-5)
            and (abs(self.x_fwhm - other.x_fwhm) < 1e-5)
        )

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return (
            f"Peak(x={self.x:.3f}; y={self.y:.2f}; signal-to-noise={self.signal_to_noise}; fwhm={self.x_fwhm:.4f};"
            f" area={self.area}; width={self.idx_fwhm}; index={self.idx})"
        )

    @property
    def fwhm_height(self):
        """Return fwhm height"""
        return self.y / 2

    def clone(self):
        """Creates a deep copy of the peak

        Returns
        -------
        copy: Peak
            copy of the peak
        """
        return deepcopy(self)

    def as_slice(self, window=0):
        """Returns the peak index as slice which can be used to extract data spectrum or an array"""
        return slice(self.idx_left - window, self.idx_right + window + 1)

    def as_dict(self):
        """Returns the peak as dict with all values"""
        return dict(
            x=self.x,
            y=self.y,
            x_left=self.x_left,
            x_right=self.x_right,
            idx=self.idx,
            idx_left=self.idx_left,
            idx_right=self.idx_right,
            x_fwhm=self.x_fwhm,
            idx_fwhm=self.idx_fwhm,
            area=self.area,
            signal_to_noise=self.signal_to_noise,
            score=self.score,
            color=self.color,
            peak_id=self.peak_id,
        )


def _get_nearest_peak(peaklist, mz: float):
    lo = 0
    hi = len(peaklist)

    tol = 1

    def sweep(_lo, _hi):
        best_error = float("inf")
        best_index = None
        for i in range(_hi - _lo):
            i += _lo
            v = peaklist[i].x
            err = abs(v - mz)
            if err < best_error:
                best_error = err
                best_index = i
        return peaklist[best_index], best_error

    def bin_search(_lo, _hi):
        if (_hi - _lo) < 5:
            return sweep(_lo, _hi)
        else:
            mid = (_hi + _lo) // 2
            v = peaklist[mid].x
            if abs(v - mz) < tol:
                return sweep(_lo, _hi)
            elif v > mz:
                return bin_search(_lo, mid)
            else:
                return bin_search(mid, _hi)

    return bin_search(lo, hi)


class PeakSet:
    """A sequence of :class:`Peak` instances, ordered by m/z,
    providing efficient search and retrieval of individual peaks or
    whole intervals of the m/z domain.

    This collection is not meant to be updated once created, as it
    it is indexed for ease of connecting individual peak objects to
    their position in the underlying sequence.

    One :class:`PeakSet` is considered equal to another if all of their
    contained :class:`Peak` members are equal to each other

    Attributes
    ----------
    peaks : list
        The :class:`FittedPeak` instances, stored
    """

    def __init__(self, peaks):
        self.peaks = list(peaks)

        self._indexed = False
        self._index_key = "x"
        self._index_reverse = False
        self.reindex()

    def __repr__(self):
        return "<PeakSet %d Peaks>" % (len(self))

    def __getitem__(self, item):
        if isinstance(item, slice):
            return PeakSet(self.peaks[item])
        elif isinstance(item, (list, np.ndarray)):
            return PeakSet([self.peaks[_item] for _item in item])
        return self.peaks[item]

    def __eq__(self, other):
        if other is None:
            return False
        return tuple(self) == tuple(other)

    def __ne__(self, other):
        return not (self == other)

    def __len__(self):
        return len(self.peaks)

    def __add__(self, other):
        if not hasattr(other, "peaks"):
            raise ValueError("Could not find `peaks` attribute in the object")

        self.peaks.extend(other.peaks)
        self.peaks = list(set(self.peaks))
        self.reindex()
        return self

    def __delitem__(self, key):
        """Delete item"""
        self.peaks.pop(key)

    def __contains__(self, item):
        for peak in self.peaks:
            if peak == item:
                return True
        return False

    def add(self, peaks: List[Peak], reindex: bool = False):
        """Add peaks to the `peaks` storage"""
        if not isinstance(peaks, list):
            raise ValueError("Must provide list of peaks")

        for peak in peaks:
            if not isinstance(peak, Peak):
                raise ValueError("Cannot add this object to the PeakSet")
            self.peaks.append(peak)

        self._indexed = False
        if reindex:
            self.reindex()

    def remove(self, indices: List = None, reindex: bool = False):
        """Remove peaks from the `peaks` storage."""
        if not isinstance(indices, list):
            raise ValueError("Must provide list of indices")

        # always iterate backwards!
        for idx in sorted(indices, reverse=True):
            _ = self.peaks.pop(idx)

        self._indexed = False
        if reindex:
            self.reindex()

    def reindex(self, key=None, reverse=None, set_keys=True):
        """Re-indexes the sequence of peaks, updating their :attr:`peak_id`"""
        if key is None:
            key = self._index_key
        if reverse is None:
            reverse = self._index_reverse

        if isinstance(reverse, str):
            reverse = dict(ascending=False, descending=True)[reverse]
        self._index(key, reverse)

        # sets the currently specified keys
        if set_keys:
            self._index_key = key
            self._index_reverse = reverse

    def _index(self, key: str, reverse: bool):
        """Sets the index of peaks in the list"""
        self.peaks = natsorted(self.peaks, key=operator.attrgetter(key), reverse=reverse)
        i = 0
        for i, peak in enumerate(self.peaks):
            peak.peak_id = i
        self._indexed = True

    def has_peak(self, mz, tolerance=1e-5):
        """Search the for the peak nearest to `mz` within `tolerance` error (in PPM)

        Parameters
        ----------
        mz : float
            The m/z to search for
        tolerance : float, optional
            The error tolerance to accept. Defaults to 1e-5 (10 ppm)

        Returns
        -------
        FittedPeak
            The peak, if found. `None` otherwise.
        """
        return binary_search(self.peaks, mz, tolerance)

    get_nearest_peak = _get_nearest_peak

    def between(self, m1, m2):
        """Retrieve a :class:`PeakSet` containing all the peaks in `self` whose m/z is between `m1` and `m2`.

        These peaks are not copied.

        Parameters
        ----------
        m1 : float
            The lower m/z limit
        m2 : float
            The upper m/z limit

        Returns
        -------
        PeakSet
        """
        if not self._indexed:
            self.reindex()
        start, end = self._get_peak_indices(m1, m2)
        return self[start : end + 1]

    def all_peaks_for(self, mz, error_tolerance=2e-5):
        """Find all peaks within `error_tolerance` ppm of `mz` m/z.

        Parameters
        ----------
        mz : float
            The query m/z
        error_tolerance : float, optional
            The parts-per-million error tolerance (the default is 2e-5)

        Returns
        -------
        tuple
        """
        if not self._indexed:
            self.reindex()
        m1 = mz - (mz * error_tolerance)
        m2 = mz + (mz * error_tolerance)
        start, end = self._get_peak_indices(m1, m2)

        return self.peaks[start : end + 1]

    # noinspection PyArgumentList
    def _get_peak_indices(self, m1: float, m2: float):
        """Returns indices between two masses"""
        p1, _ = self.get_nearest_peak(m1)
        p2, _ = self.get_nearest_peak(m2)

        start = p1.peak_id
        end = p2.peak_id
        n = len(self)
        if p1.x < m1 and start + 1 < n:
            start += 1
        if p2.x > m2 and end > 0:
            end -= 1

        return start, end


def _sweep_solution(array, value, lo, hi, tolerance):
    best_index = -1
    best_error = float("inf")
    best_intensity = 0
    for i in range(hi - lo):
        target = array[lo + i]
        error = ppm_error(value, target.x)
        abs_error = abs(error)
        if abs_error < tolerance and (abs_error < best_error * 1.1) and (target.y > best_intensity):
            best_index = lo + i
            best_error = abs_error
            best_intensity = target.y
    if best_index == -1:
        return None
    else:
        return array[best_index]


def _binary_search(array, value, lo, hi, tolerance):
    if (hi - lo) < 5:
        return _sweep_solution(array, value, lo, hi, tolerance)
    else:
        mid = (hi + lo) // 2
        target = array[mid]
        target_value = target.x
        error = ppm_error(value, target_value)

        if abs(error) <= tolerance:
            return _sweep_solution(array, value, max(mid - (mid if mid < 5 else 5), lo), min(mid + 5, hi), tolerance)
        elif target_value > value:
            return _binary_search(array, value, lo, mid, tolerance)
        elif target_value < value:
            return _binary_search(array, value, mid, hi, tolerance)
    raise Exception("No recursion found!")


def binary_search(array, value, tolerance=2e-5):
    size = len(array)
    if size == 0:
        return None
    return _binary_search(array, value, 0, size, tolerance)
