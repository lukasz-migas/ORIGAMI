"""Processing module that handles data extract"""
# Standard library imports
import logging

# Third-party imports
import numpy as np

# Local imports

LOGGER = logging.getLogger(__name__)


class ExtractionHandler:
    def __init__(self):
        """Initialized"""

    def extract_ms_from_mobilogram(self, rect, x_labels, y_labels):
        """Extracts mass spectrum based on selection window in a mobilogram plot"""
        if len(x_labels) > 1:
            raise ValueError("Cannot handle multiple labels")

        # unpack values
        x_label = x_labels[0]
        x_min, x_max, _, _ = rect

        if x_label == "Drift time (bins)":
            dt_start = np.ceil(x_min).astype(int)
            dt_end = np.floor(x_max).astype(int)
        else:
            dt_start = x_min
            dt_end = x_max
