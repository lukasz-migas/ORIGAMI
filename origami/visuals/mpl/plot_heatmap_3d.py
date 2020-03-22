# Third-party imports
import numpy as np
import matplotlib

# Local imports
import origami.utils.visuals as ut_visuals
from origami.visuals.mpl.base import PlotBase


class PlotHeatmap3D(PlotBase):
    def __init__(self, *args, **kwargs):
        PlotBase.__init__(self, *args, **kwargs)

    def set_plot_zlabel(self, zlabel, **kwargs):
        kwargs = ut_visuals.check_plot_settings(**kwargs)

        if zlabel is None:
            zlabel = self.plot_base.get_ylabel()
        self.plot_base.set_zlabel(
            zlabel, labelpad=kwargs["label_pad"], fontsize=kwargs["label_size"], weight=kwargs["label_weight"]
        )

    def plot_3D_update(self, **kwargs):

        # Setup font size info
        self.plot_base.tick_params(labelsize=kwargs["tick_size"])

        # Get rid of spines
        if not kwargs["show_spines"]:
            self.update_xyz_pane_colors((1.0, 1.0, 1.0, 0.0))
        else:
            self.update_xyz_pane_colors((0.0, 0.0, 0.0, 0.0))

        # Get rid of the ticks
        if not kwargs["show_ticks"]:
            self.plot_base.set_xticks([])
            self.plot_base.set_yticks([])
            self.plot_base.set_zticks([])

        # convert weights
        if kwargs["label_weight"]:
            kwargs["label_weight"] = "heavy"
        else:
            kwargs["label_weight"] = "normal"

        # update labels
        self.update_xyz_labels(
            self.plot_base.get_xlabel(), self.plot_base.get_ylabel(), self.plot_base.get_zlabel(), **kwargs
        )

        matplotlib.rc("xtick", labelsize=kwargs["tick_size"])
        matplotlib.rc("ytick", labelsize=kwargs["tick_size"])

        self.plot_base.grid(kwargs["grid"])

    def plot_3D_surface(
        self, xvals, yvals, zvals, xlabel=None, ylabel=None, zlabel=None, axesSize=None, plotType="Surface3D", **kwargs
    ):
        # update settings
        self._check_and_update_plot_settings(plot_name=plotType, axes_size=axesSize, **kwargs)

        #         kwargs = self._check_colormap(**kwargs)
        xvals, yvals = np.meshgrid(xvals, yvals)

        ydivider, expo = self.testXYmaxValsUpdated(values=zvals)
        if expo > 1:
            offset_text = r"x$\mathregular{10^{%d}}$" % expo
            zlabel = "".join([zlabel, " [", offset_text, "]"])
            zvals = np.divide(zvals, float(ydivider))

        matplotlib.rc("xtick", labelsize=kwargs["tick_size"])
        matplotlib.rc("ytick", labelsize=kwargs["tick_size"])

        self.plot_base = self.figure.add_subplot(111, projection="3d", aspect="auto")
        self.plot_base.mouse_init(rotate_btn=1, zoom_btn=2)

        self.cax = self.plot_base.plot_surface(
            xvals, yvals, zvals, cmap=kwargs["colormap"], antialiased=True, shade=kwargs["shade"], picker=1
        )

        # update labels
        self.set_plot_xlabel(None, **kwargs)
        self.set_plot_ylabel(None, **kwargs)

        # Setup font size info
        self.plot_base.tick_params(labelsize=kwargs["tick_size"])

        # Get rid of spines
        if not kwargs["show_spines"]:
            self.update_xyz_pane_colors((1.0, 1.0, 1.0, 0.0))
        else:
            self.update_xyz_pane_colors((0.0, 0.0, 0.0, 0.0))

        # Get rid of the ticks
        if not kwargs["show_ticks"]:
            self.plot_base.set_xticks([])
            self.plot_base.set_yticks([])
            self.plot_base.set_zticks([])

        # update labels
        self.update_xyz_labels(xlabel, ylabel, zlabel, **kwargs)

        self.plot_base.grid(kwargs["grid"])

        self.update_xyz_limits(xvals, yvals, zvals)

        self.plot_base.set_position(axesSize)

    def update_xyz_pane_colors(self, color):
        """Update pane colors"""
        self.plot_base.w_xaxis.line.set_color(color)
        self.plot_base.w_yaxis.line.set_color(color)
        self.plot_base.w_zaxis.line.set_color(color)

    def update_xyz_limits(self, xvals, yvals, zvals):
        """Update plot limits"""
        self.plot_base.set_xlim([np.min(xvals), np.max(xvals)])
        self.plot_base.set_ylim([np.min(yvals), np.max(yvals)])
        self.plot_base.set_zlim([np.min(zvals), np.max(zvals)])

    def update_xyz_labels(self, xlabel, ylabel, zlabel, **kwargs):
        """Update x/y/z labels"""
        # update labels
        self.plot_base.set_xlabel(
            xlabel,
            labelpad=kwargs["label_pad"],
            fontsize=kwargs["label_size"],
            weight=kwargs["label_weight"],
            visible=kwargs["show_labels"],
        )
        self.plot_base.set_ylabel(
            ylabel,
            labelpad=kwargs["label_pad"],
            fontsize=kwargs["label_size"],
            weight=kwargs["label_weight"],
            visible=kwargs["show_labels"],
        )
        self.plot_base.set_zlabel(
            zlabel,
            labelpad=kwargs["label_pad"],
            fontsize=kwargs["label_size"],
            weight=kwargs["label_weight"],
            visible=kwargs["show_labels"],
        )

    def plot_3D_wireframe(
        self,
        xvals,
        yvals,
        zvals,
        xlabel=None,
        ylabel=None,
        zlabel=None,
        axesSize=None,
        plotType="Wireframe3D",
        **kwargs,
    ):
        # update settings
        self._check_and_update_plot_settings(plot_name=plotType, axes_size=axesSize, **kwargs)

        xvals, yvals = np.meshgrid(xvals, yvals)

        ydivider, expo = self.testXYmaxValsUpdated(values=zvals)
        if expo > 1:
            offset_text = r"x$\mathregular{10^{%d}}$" % expo
            zlabel = "".join([zlabel, " [", offset_text, "]"])
            zvals = np.divide(zvals, float(ydivider))

        matplotlib.rc("xtick", labelsize=kwargs["tick_size"])
        matplotlib.rc("ytick", labelsize=kwargs["tick_size"])

        #         kwargs = self._check_colormap(**kwargs)
        self.plot_base = self.figure.add_subplot(111, projection="3d", aspect="auto")
        self.plot_base.mouse_init(rotate_btn=1, zoom_btn=2)
        self.plot_base.plot_wireframe(
            xvals,
            yvals,
            zvals,
            color=kwargs["line_color"],
            linewidth=kwargs["line_width"],
            linestyle=kwargs["line_style"],
            antialiased=False,
        )

        # update labels
        self.set_plot_xlabel(None, **kwargs)
        self.set_plot_ylabel(None, **kwargs)

        # Setup font size info
        self.plot_base.tick_params(labelsize=kwargs["tick_size"])

        # Get rid of spines
        if not kwargs["show_spines"]:
            self.update_xyz_pane_colors((1.0, 1.0, 1.0, 0.0))
        else:
            self.update_xyz_pane_colors((0.0, 0.0, 0.0, 0.0))

        # Get rid of the ticks
        if not kwargs["show_ticks"]:
            self.plot_base.set_xticks([])
            self.plot_base.set_yticks([])
            self.plot_base.set_zticks([])

        # update labels
        self.update_xyz_labels(xlabel, ylabel, zlabel, **kwargs)

        self.plot_base.grid(kwargs["grid"])
        self.update_xyz_limits(xvals, yvals, zvals)

        self.plot_base.set_position(axesSize)
