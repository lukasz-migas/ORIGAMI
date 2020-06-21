"""Plot IDs"""
# Standard library imports
from enum import IntEnum


class PlotIds(IntEnum):
    """This class should be used to keep track of the various ids each part of the plot has. It should speed-up
    plotting of individual elements in the plot area.
    """

    PLOT_1D_LINE_GID = 14
    PLOT_1D_PATCH_GID = 15
    PLOT_COMPARE_TOP_GID = 16
    PLOT_COMPARE_BOTTOM_GID = 17
