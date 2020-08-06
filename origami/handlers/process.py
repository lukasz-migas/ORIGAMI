"""Processing module"""
# Third-party imports
import numpy as np

# Local imports
from origami.utils.check import check_value_order
from origami.config.config import CONFIG
from origami.processing.spectra import subtract_spectra
from origami.objects.containers.heatmap import HeatmapObject
from origami.objects.containers.spectrum import MassSpectrumObject


class ProcessHandler:
    """Data processing handler"""

    @staticmethod
    def subtract_spectra(x_top: np.ndarray, y_top: np.ndarray, x_bottom: np.ndarray, y_bottom: np.ndarray):
        """Subtract two spectra from one another

        Parameters
        ----------
        x_top : np.ndarray
            x-axis of the top spectrum
        y_top : np.ndarray
            y-axis of the top spectrum
        x_bottom : np.ndarray
            x-axis of the bottom spectrum
        y_bottom : np.ndarray
            y-axis of the bottom spectrum
        """
        x_top, y_top, x_bottom, y_bottom = subtract_spectra(x_top, y_top, x_bottom, y_bottom)

        return x_top, y_top, x_bottom, y_bottom

    @staticmethod
    def on_process_ms(mz_obj: MassSpectrumObject):
        """Process and modify mass spectrum object

        Parameters
        ----------
        mz_obj : MassSpectrumObject
            mass spectrum object

        Returns
        -------
        mz_obj : MassSpectrumObject
            processed mass spectrum object
        """
        if not isinstance(mz_obj, MassSpectrumObject):
            raise ValueError("This function takes `MassSpectrumObject` as an argument")

        if CONFIG.ms_crop:
            mz_obj.crop(crop_min=CONFIG.ms_crop_min, crop_max=CONFIG.ms_crop_max)

        if CONFIG.ms_linearize:
            mz_obj.linearize(
                bin_size=CONFIG.ms_linearize_mz_bin_size,
                x_min=CONFIG.ms_linearize_mz_start,
                x_max=CONFIG.ms_linearize_mz_end,
                linearize_method=CONFIG.ms_linearize_method,
            )

        if CONFIG.ms_smooth:
            mz_obj.smooth(
                smooth_method=CONFIG.ms_smooth_mode,
                sigma=CONFIG.ms_smooth_sigma,
                poly_order=CONFIG.ms_smooth_polynomial,
                window_size=CONFIG.ms_smooth_window,
                N=CONFIG.ms_smooth_moving_window,
            )

        if CONFIG.ms_threshold:
            mz_obj.baseline(
                baseline_method=CONFIG.ms_baseline_method,
                threshold=CONFIG.ms_baseline_linear_threshold,
                curved_window=CONFIG.ms_baseline_curved_window,
                median_window=CONFIG.ms_baseline_median_window,
                tophat_window=CONFIG.ms_baseline_tophat_window,
            )

        if CONFIG.ms_normalize:
            mz_obj.normalize()

        return mz_obj

    @staticmethod
    def on_process_heatmap(heatmap_obj: HeatmapObject):
        """Process and modify mass spectrum object

        Parameters
        ----------
        heatmap_obj : HeatmapObject
            heatmap object

        Returns
        -------
        heatmap_obj : HeatmapObject
            processed heatmap
        """
        if not isinstance(heatmap_obj, HeatmapObject):
            raise ValueError("This function takes `HeatmapObject` as an argument")

        if CONFIG.heatmap_interpolate:
            heatmap_obj.linearize(
                fold=CONFIG.heatmap_interpolate_fold,
                linearize_method=CONFIG.heatmap_interpolate_mode,
                x_axis=CONFIG.heatmap_interpolate_xaxis,
                y_axis=CONFIG.heatmap_interpolate_yaxis,
            )

        if CONFIG.heatmap_crop:
            heatmap_obj.crop(
                x_min=CONFIG.heatmap_crop_xmin,
                x_max=CONFIG.heatmap_crop_xmax,
                y_min=CONFIG.heatmap_crop_ymin,
                y_max=CONFIG.heatmap_crop_ymax,
            )

        if CONFIG.heatmap_smooth:
            heatmap_obj.smooth(
                smooth_method=CONFIG.ms_smooth_mode,
                sigma=CONFIG.heatmap_smooth_sigma,
                poly_order=CONFIG.heatmap_smooth_polynomial,
                window_size=CONFIG.heatmap_smooth_window,
            )

        if CONFIG.heatmap_threshold:
            heatmap_obj.baseline(threshold=CONFIG.heatmap_threshold_lower)

        if CONFIG.heatmap_normalize:
            heatmap_obj.normalize(normalize_method=CONFIG.heatmap_normalize_mode)

        return heatmap_obj

    # noinspection DuplicatedCode
    @staticmethod
    def find_peaks_in_mass_spectrum_peak_properties(
        mz_obj: MassSpectrumObject,
        threshold=CONFIG.peak_property_threshold,
        distance=CONFIG.peak_property_distance,
        width=CONFIG.peak_property_width,
        rel_height=CONFIG.peak_property_relative_height,
        min_intensity=CONFIG.peak_property_min_intensity,
        peak_width_modifier=CONFIG.peak_property_peak_width_modifier,
        pick_mz_min=None,
        pick_mz_max=None,
    ):
        """Find peaks in mass spectrum using peak properties"""
        from origami.processing.feature.mz_picker import PropertyPeakPicker

        mz_min, mz_max = mz_obj.x_limit
        if pick_mz_min is None:
            pick_mz_min = mz_min
        if pick_mz_max is None:
            pick_mz_max = mz_max
        pick_mz_min, pick_mz_max = check_value_order(pick_mz_min, pick_mz_max)

        picker = PropertyPeakPicker(mz_obj.x, mz_obj.y)
        picker.find_peaks(
            mz_range=[pick_mz_min, pick_mz_max],
            threshold=threshold,
            distance=distance,
            width=width,
            rel_height=rel_height,
            min_intensity=min_intensity,
            peak_width_modifier=peak_width_modifier,
        )
        return picker

    # noinspection DuplicatedCode
    @staticmethod
    def find_peaks_in_mass_spectrum_local_max(
        mz_obj: MassSpectrumObject,
        window=CONFIG.peak_local_window,
        threshold=CONFIG.peak_local_threshold,
        rel_height=CONFIG.peak_local_relative_height,
        pick_mz_min=None,
        pick_mz_max=None,
    ):
        """Find peaks in mass spectrum using local-maximum algorithm"""
        from origami.processing.feature.mz_picker import LocalMaxPeakPicker

        mz_min, mz_max = mz_obj.x_limit
        if pick_mz_min is None:
            pick_mz_min = mz_min
        if pick_mz_max is None:
            pick_mz_max = mz_max
        pick_mz_min, pick_mz_max = check_value_order(pick_mz_min, pick_mz_max)

        # check  threshold
        if threshold > 1:
            threshold = threshold / mz_obj.y_limit[1]

        picker = LocalMaxPeakPicker(mz_obj.x, mz_obj.y)
        picker.find_peaks(
            mz_range=[pick_mz_min, pick_mz_max], window=window, min_intensity=threshold, rel_height=rel_height
        )
        return picker

    # noinspection DuplicatedCode
    @staticmethod
    def find_peaks_in_mass_spectrum_peakutils(
        mz_obj: MassSpectrumObject,
        window=CONFIG.peak_differential_window,
        threshold=CONFIG.peak_differential_threshold,
        rel_height=CONFIG.peak_differential_relative_height,
        pick_mz_min=None,
        pick_mz_max=None,
    ):
        """Find peaks in the mass spectrum using differential algorithm"""
        from origami.processing.feature.mz_picker import DifferentialPeakPicker

        mz_min, mz_max = mz_obj.x_limit
        if pick_mz_min is None:
            pick_mz_min = mz_min
        if pick_mz_max is None:
            pick_mz_max = mz_max
        pick_mz_min, pick_mz_max = check_value_order(pick_mz_min, pick_mz_max)

        # check  threshold
        if threshold > 1:
            threshold = threshold / mz_obj.y_limit[1]

        picker = DifferentialPeakPicker(mz_obj.x, mz_obj.y)
        picker.find_peaks(
            mz_range=[pick_mz_min, pick_mz_max], min_distance=window, min_intensity=threshold, rel_height=rel_height
        )
        return picker


PROCESS_HANDLER = ProcessHandler()
