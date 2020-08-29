"""Handler for overlaying plots"""
# Standard library imports
from typing import List

# Local imports
# from origami.config.environment import ENV
# from origami.config.config import CONFIG
from origami.objects.groups import IonHeatmapGroup
from origami.objects.groups import MobilogramGroup
from origami.objects.groups import ChromatogramGroup
from origami.objects.groups import MassSpectrumGroup


class OverlayHandler:
    """Handler class for pre-processing of overlay data"""

    def collect_overlay_1d_spectra(self, item_list: List[List[str]], spectral_type: str, auto_resample: bool):  # noqa
        """Prepare overlay line data"""
        if spectral_type == "Mass Spectra":
            group = MassSpectrumGroup(item_list)
        elif spectral_type == "Chromatograms":
            group = ChromatogramGroup(item_list)
        elif spectral_type == "Mobilograms":
            group = MobilogramGroup(item_list)
        else:
            raise ValueError("Cannot collect data")

        if not group.validate_shape() and not auto_resample:
            raise ValueError("Cannot collect data since the shape and size of the data does not match")
        valid_x = group.validate_x_labels()
        valid_y = group.validate_y_labels()

        return group, valid_x, valid_y

    def collect_overlay_2d_heatmap(self, item_list, auto_resample: bool):  # noqa
        """Prepare overlay heatmap data"""
        group = IonHeatmapGroup(item_list)
        if not group.validate_shape() and not auto_resample:
            raise ValueError("Cannot collect data since the shape and size of the data does not match")
        valid_x = group.validate_x_labels()
        valid_y = group.validate_y_labels()

        return group, valid_x, valid_y


OVERLAY_HANDLER = OverlayHandler()
