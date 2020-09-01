"""Handler for overlaying plots"""
# Standard library imports
from typing import List

# Third-party imports
import numpy as np

# Local imports
import origami.processing.activation as pr_activation
from origami.utils.color import convert_rgb_1_to_hex
from origami.visuals.rgb import ImageRGBA
from origami.config.config import CONFIG
from origami.utils.visuals import check_n_grid_dimensions
# from origami.config.environment import ENV
# from origami.config.config import CONFIG
from origami.objects.groups import IonHeatmapGroup
from origami.objects.groups import MobilogramGroup
from origami.objects.groups import ChromatogramGroup
from origami.objects.groups import MassSpectrumGroup
from origami.handlers.process import PROCESS_HANDLER


class OverlayHandler:
    """Handler class for pre-processing of overlay data"""

    def collect_overlay_1d_spectra(self, item_list: List[List[str]], spectral_type: str, auto_resample: bool):  # noqa
        """Prepare overlay line data"""
        if spectral_type == "Mass Spectra":
            group_obj = MassSpectrumGroup(item_list)
        elif spectral_type == "Chromatograms":
            group_obj = ChromatogramGroup(item_list)
        elif spectral_type == "Mobilograms":
            group_obj = MobilogramGroup(item_list)
        else:
            raise ValueError("Cannot collect data")

        if not group_obj.validate_shape() and not auto_resample:
            raise ValueError("Cannot collect data since the shape and size of the data does not match")
        valid_x = group_obj.validate_x_labels()
        valid_y = group_obj.validate_y_labels()

        return group_obj, valid_x, valid_y

    def collect_overlay_2d_heatmap(self, item_list, auto_resample: bool):  # noqa
        """Prepare overlay heatmap data"""
        group_obj = IonHeatmapGroup(item_list)
        if not group_obj.validate_shape() and not auto_resample:
            raise ValueError("Cannot collect data since the shape and size of the data does not match")
        valid_x = group_obj.validate_x_labels()
        valid_y = group_obj.validate_y_labels()

        return group_obj, valid_x, valid_y

    def get_group_metadata(self, group_obj, keys: List[str], defaults: List, n_items: int):
        """Retrieve metadata from the data objects"""
        metadata = group_obj.get_group_metadata(keys, defaults, "overlay")
        for key, values in metadata.items():
            if len(values) != n_items:
                raise ValueError(f"Expected {n_items} for the {key} data")

        return metadata

    def prepare_overlay_1d_butterfly(self, group_obj):
        """Prepare line data for butterfly plot"""
        if not group_obj.validate_size(n_min=2, n_max=2):
            raise ValueError("This visualisation can only have 2 items selected")
        x_top, x_bottom = group_obj.xs
        y_top, y_bottom = group_obj.ys

        # format kwargs
        metadata = self.get_group_metadata(group_obj, ["line_style", "color", "transparency"], ["solid", "k", 1], 2)
        forced_kwargs = dict(
            compare_color_top=metadata["color"][0],
            compare_style_top=metadata["line_style"][0],
            compare_alpha_top=metadata["transparency"][0],
            compare_color_bottom=metadata["color"][1],
            compare_style_bottom=metadata["line_style"][1],
            compare_alpha_bottom=metadata["transparency"][1],
        )

        return x_top, x_bottom, y_top, -y_bottom, forced_kwargs

    def prepare_overlay_1d_subtract(self, group_obj):
        """Prepare line data for butterfly plot"""
        if not group_obj.validate_size(n_min=2, n_max=2):
            raise ValueError("This visualisation can only have 2 items selected")
        x_top, x_bottom = group_obj.xs
        y_top, y_bottom = group_obj.ys
        x_top, y_top, x_bottom, y_bottom = PROCESS_HANDLER.subtract_spectra(x_top, y_top, x_bottom, y_bottom)

        # format kwargs
        metadata = self.get_group_metadata(group_obj, ["line_style", "color", "transparency"], ["solid", "k", 1], 2)
        forced_kwargs = dict(
            compare_color_top=metadata["color"][0],
            compare_style_top=metadata["line_style"][0],
            compare_alpha_top=metadata["transparency"][0],
            compare_color_bottom=metadata["color"][1],
            compare_style_bottom=metadata["line_style"][1],
            compare_alpha_bottom=metadata["transparency"][1],
        )

        return x_top, x_bottom, y_top, y_bottom, forced_kwargs

    def prepare_overlay_1d_multiline(self, group_obj):
        """Prepare line data for butterfly plot"""
        if not group_obj.validate_size(n_min=2, n_max=100):
            raise ValueError("This visualisation must have more than two items selected")
        xs, array = group_obj.xs, group_obj.array
        y = xs[0]
        x = np.arange(len(xs))
        return x, y, array

    def prepare_overlay_2d_mean(self, group_obj):
        """Prepare heatmap data"""
        arrays = group_obj.arrays

        # compute mean array
        array = pr_activation.compute_mean(arrays)

        return array, group_obj.x, group_obj.y, group_obj.x_label, group_obj.y_label

    def prepare_overlay_2d_stddev(self, group_obj):
        """Prepare heatmap data"""
        arrays = group_obj.arrays

        # compute mean array
        array = pr_activation.compute_std_dev(arrays)

        return array, group_obj.x, group_obj.y, group_obj.x_label, group_obj.y_label

    def prepare_overlay_2d_variance(self, group_obj):
        """Prepare heatmap data"""
        arrays = group_obj.arrays

        # compute mean array
        array = pr_activation.compute_variance(arrays)

        return array, group_obj.x, group_obj.y, group_obj.x_label, group_obj.y_label

    def prepare_overlay_2d_mask(self, group_obj):
        """Prepare heatmap data"""
        if not group_obj.validate_size(n_min=2, n_max=2):
            raise ValueError("This visualisation can only have 2 items selected")

        # get data
        array_1, array_2 = group_obj.arrays

        # get metadata
        metadata = self.get_group_metadata(group_obj, ["mask", "colormap"], [0.5, "Reds"], 2)
        mask_1, mask_2 = metadata["mask"]
        colormap_1, colormap_2 = metadata["colormap"]
        forced_kwargs = dict(heatmap_colormap_1=colormap_1, heatmap_colormap_2=colormap_2)

        # compute mean array
        array_ma_1, array_ma_2 = pr_activation.mask_arrays(array_1, array_2, mask_1, mask_2)
        return array_ma_1, array_ma_2, group_obj.x, group_obj.y, group_obj.x_label, group_obj.y_label, forced_kwargs

    def prepare_overlay_2d_transparent(self, group_obj):
        """Prepare heatmap data"""
        if not group_obj.validate_size(n_min=2, n_max=2):
            raise ValueError("This visualisation can only have 2 items selected")

        # get data
        array_1, array_2 = group_obj.arrays

        # get metadata
        metadata = self.get_group_metadata(group_obj, ["transparency", "colormap"], [0.5, "Reds"], 2)
        alpha_1, alpha_2 = metadata["transparency"]
        colormap_1, colormap_2 = metadata["colormap"]

        # build forced kwargs
        forced_kwargs = dict(
            heatmap_transparency_1=alpha_1,
            heatmap_transparency_2=alpha_2,
            heatmap_colormap_1=colormap_1,
            heatmap_colormap_2=colormap_2,
        )

        # compute mean array
        return array_1, array_2, group_obj.x, group_obj.y, group_obj.x_label, group_obj.y_label, forced_kwargs

    def prepare_overlay_2d_grid_compare_rmsd(self, group_obj):
        """Prepare heatmap data"""
        if not group_obj.validate_size(n_min=2, n_max=2):
            raise ValueError("This visualisation can only have 2 items selected")

        # get data
        array_1, array_2 = group_obj.arrays

        # compute mean array
        rmsd, array = pr_activation.compute_rmsd(array_1, array_2)
        rmsd_label = f"{rmsd:.2f} %"

        return array_1, array_2, array, group_obj.x, group_obj.y, group_obj.x_label, group_obj.y_label, rmsd_label

    def prepare_overlay_2d_rmsd(self, group_obj):
        """Prepare heatmap data"""
        if not group_obj.validate_size(n_min=2, n_max=2):
            raise ValueError("This visualisation can only have 2 items selected")
        array_1, array_2 = group_obj.arrays

        # compute mean array
        rmsd, array = pr_activation.compute_rmsd(array_1, array_2)
        rmsd_label = f"{rmsd:.2f} %"

        return array, group_obj.x, group_obj.y, group_obj.x_label, group_obj.y_label, rmsd_label

    def prepare_overlay_2d_rmsf(self, group_obj):
        """Prepare heatmap data"""
        if not group_obj.validate_size(n_min=2, n_max=2):
            raise ValueError("This visualisation can only have 2 items selected")
        array_1, array_2 = group_obj.arrays

        # compute mean array
        rmsd, array = pr_activation.compute_rmsd(array_1, array_2)
        rmsf = pr_activation.compute_rmsf(array_1, array_2)
        rmsd_label = f"{rmsd:.2f} %"

        return array, group_obj.x, group_obj.y, rmsf, group_obj.x_label, group_obj.y_label, rmsd_label

    def prepare_overlay_2d_rmsd_matrix(self, group_obj):
        """Prepare heatmap data"""
        if not group_obj.validate_size(n_min=2, n_max=100):
            raise ValueError("This visualisation must have at least 2 items selected")
        arrays = group_obj.arrays

        # compute mean array
        x, y, array = pr_activation.compute_rmsd_matrix(arrays)

        return array, x, y, group_obj.x_label, group_obj.y_label

    def prepare_overlay_2d_grid_n_x_n(self, group_obj):
        """Prepare heatmap data"""
        if not group_obj.validate_size(n_min=2, n_max=25):
            raise ValueError("This visualisation must have at least 2 items selected")

        # get data
        arrays = group_obj.arrays
        n_rows, n_cols, _, _ = check_n_grid_dimensions(len(arrays))

        return arrays, group_obj.x, group_obj.y, group_obj.x_label, group_obj.y_label, n_rows, n_cols

    def prepare_overlay_2d_rgb(self, group_obj):
        """Prepare heatmap data"""
        if not group_obj.validate_size(n_min=1, n_max=4):
            raise ValueError("This visualisation must have at least 1 items selected")
        arrays = group_obj.arrays

        # get metadata
        metadata = self.get_group_metadata(group_obj, ["color"], [(1, 0, 1)], len(arrays))
        colors = metadata["color"]
        colors = [convert_rgb_1_to_hex(color) for color in colors]

        rgba = ImageRGBA(arrays, colors)
        array = rgba.rgba
        if CONFIG.rgb_adaptive_hist:
            array = rgba.adaptive_histogram(
                clip_limit=CONFIG.rgb_adaptive_hist_clip_limit, n_bins=CONFIG.rgb_adaptive_hist_n_bins, image=array
            )

        # build forced_kwargs
        forced_kwargs = dict(colorbar=False)

        return array, group_obj.x, group_obj.y, group_obj.x_label, group_obj.y_label, forced_kwargs


OVERLAY_HANDLER = OverlayHandler()
