"""Plot IDs"""


class PlotIds:
    """This class should be used to keep track of the various ids each part of the plot has. It should speed-up
    plotting of individual elements in the plot area.
    """

    # standard 2d plot
    PLOT_2D = "13"

    # standard 1d plots
    PLOT_1D_LINE_GID = "14"
    PLOT_1D_PATCH_GID = "15"

    # comparison plots
    PLOT_COMPARE_TOP_GID = "16"
    PLOT_COMPARE_BOTTOM_GID = "17"

    # joint plots
    PLOT_JOINT_XY = "18"
    PLOT_JOINT_X = "19"
    PLOT_JOINT_Y = "20"
