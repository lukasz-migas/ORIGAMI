"""Mass-spectral peak pickers"""
# Standard library imports
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple
from typing import Union
from typing import Optional

# Third-party imports
import numpy as np

# Local imports
from origami.utils.ranges import get_min_max
from origami.processing.feature.detect import find_peaks_in_spectrum_local_max
from origami.processing.feature.detect import find_peaks_in_spectrum_peakutils
from origami.processing.feature.detect import find_peaks_in_spectrum_peak_properties
from origami.processing.feature.peak_set import Peak
from origami.processing.feature.peak_set import PeakSet
from origami.processing.feature.base_picker import BasePicker


class MassSpectrumBasePicker(BasePicker):
    """Base mass spectrum picker"""

    def __init__(self, x, y):
        super().__init__(x, y)

    def find_peaks(self, *args, **kwargs):
        """Find peaks in mass spectrum"""
        raise NotImplementedError("Must implement method")

    @staticmethod
    def get_from_dict(found_peaks: Dict) -> PeakSet:
        """Generate `PeakSet` from dictionary of peaks"""
        n_peaks = len(found_peaks["x"])

        # add missing columns
        if "x_width" not in found_peaks:
            found_peaks["x_width"] = found_peaks["x_right"] - found_peaks["x_left"]
        if "area" not in found_peaks:
            found_peaks["area"] = np.asarray(found_peaks["y"])
        if "signal_to_noise" not in found_peaks:
            found_peaks["signal_to_noise"] = np.ones_like(found_peaks["y"])
        if "score" not in found_peaks:
            found_peaks["score"] = np.full_like(found_peaks["y"], fill_value=100)

        peak_data = []
        for peak_id in range(n_peaks):
            peak_data.append(
                Peak(
                    x=found_peaks["x"][peak_id],
                    y=found_peaks["y"][peak_id],
                    x_left=found_peaks["x_left"][peak_id],
                    x_right=found_peaks["x_right"][peak_id],
                    idx=found_peaks["idx"][peak_id],
                    idx_left=found_peaks["idx_left"][peak_id],
                    idx_right=found_peaks["idx_right"][peak_id],
                    x_fwhm=found_peaks["x_width"][peak_id],
                    idx_fwhm=found_peaks["idx_fwhm"][peak_id],
                    area=found_peaks["area"][peak_id],
                    signal_to_noise=found_peaks["signal_to_noise"][peak_id],
                    peak_id=peak_id,
                    score=found_peaks["score"][peak_id],
                    color=None,
                )
            )

        return PeakSet(peak_data)


# noinspection DuplicatedCode
class PropertyPeakPicker(MassSpectrumBasePicker):
    """Peak picker that uses base properties to determine appropriate peaks"""

    def __init__(self, x, y) -> None:
        MassSpectrumBasePicker.__init__(self, x, y)

    def find_peaks(
        self,
        mz_range: Optional[Union[List, Tuple]] = None,
        min_intensity: float = 0.01,
        threshold: float = 250,
        width: int = 0,
        rel_height: float = 0.5,
        distance: int = 1,
        peak_width_modifier: float = 1.0,
        prominence: int = 1,
        get: bool = False,
        **kwargs,
    ):
        """Pick peaks in a mass spectrum"""
        self.reset_processing_steps()
        if mz_range is None:
            mz_range = get_min_max(self._x_array)

        if not isinstance(mz_range, (list, tuple)) or len(mz_range) != 2:
            raise ValueError(f"'mz_range' expected a list or tuple and not '{type(mz_range)}'")

        if not 0 <= min_intensity <= 1:
            raise ValueError(f"Intensity should be between 0 and 1")

        found_peaks = find_peaks_in_spectrum_peak_properties(
            self._x_array,
            self._y_array,
            min_intensity=min_intensity,
            mz_range=mz_range,
            threshold=threshold,
            width=width,
            rel_height=rel_height,
            distance=distance,
            peak_width_modifier=peak_width_modifier,
            prominence=prominence,
        )
        self.add_processing_step(
            "find_peaks",
            dict(
                min_intensity=min_intensity,
                mz_range=mz_range,
                threshold=threshold,
                width=width,
                rel_height=rel_height,
                distance=distance,
                peak_width_modifier=peak_width_modifier,
                prominence=prominence,
                **kwargs,
            ),
        )
        # set data
        if get:
            return found_peaks

        self.set_from_dict(found_peaks)


# noinspection DuplicatedCode
class LocalMaxPeakPicker(MassSpectrumBasePicker):
    """Peak picker that uses base properties to determine appropriate peaks"""

    def __init__(self, x, y) -> None:
        MassSpectrumBasePicker.__init__(self, x, y)

    def find_peaks(
        self,
        window: int = 10,
        mz_range: Optional[Union[List, Tuple]] = None,
        min_intensity: float = 0.01,
        get: bool = False,
        **kwargs: Dict[str, Any],
    ):
        """Pick peaks in a mass spectrum"""
        self.reset_processing_steps()
        if mz_range is None:
            mz_range = get_min_max(self._x_array)

        if not isinstance(mz_range, (list, tuple)) or len(mz_range) != 2:
            raise ValueError(f"'mz_range' expected a list or tuple and not '{type(mz_range)}'")

        if not 0 <= min_intensity <= 1:
            raise ValueError(f"Intensity should be between 0 and 1")

        found_peaks = find_peaks_in_spectrum_local_max(
            self._x_array, self._y_array, window=window, min_intensity=min_intensity, mz_range=mz_range, **kwargs
        )

        # update parameters
        self.add_processing_step("find_peaks", {"mz_range": mz_range, "min_intensity": min_intensity, **kwargs})

        # set data
        if get:
            return found_peaks

        # set data
        self.set_from_dict(found_peaks)


# noinspection DuplicatedCode
class DifferentialPeakPicker(MassSpectrumBasePicker):
    """Peak picker that uses base properties to determine appropriate peaks"""

    def __init__(self, x, y) -> None:
        MassSpectrumBasePicker.__init__(self, x, y)

    def find_peaks(
        self,
        min_intensity: float = 0,
        min_distance: int = 30,
        mz_range: Union[Tuple, List] = None,
        get: bool = False,
        **kwargs: Dict[str, Any],
    ):
        """Pick peaks in a mass spectrum"""
        self.reset_processing_steps()
        if mz_range is None:
            mz_range = get_min_max(self._x_array)

        if not isinstance(mz_range, (list, tuple)) or len(mz_range) != 2:
            raise ValueError(f"'mz_range' expected a list or tuple and not '{type(mz_range)}'")

        if not 0 <= min_intensity <= 1:
            raise ValueError(f"Intensity should be between 0 and 1")

        found_peaks = find_peaks_in_spectrum_peakutils(
            self._x_array,
            self._y_array,
            min_distance=min_distance,
            min_intensity=min_intensity,
            mz_range=mz_range,
            **kwargs,
        )

        # update parameters
        self.add_processing_step("find_peaks", {"mz_range": mz_range, "min_intensity": min_intensity, **kwargs})

        # set data
        if get:
            return found_peaks

        # set data
        self.set_from_dict(found_peaks)
