# Standard library imports
import os

# Third-party imports
import wx
import matplotlib
from numpy import amax
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg

# Local imports
from origami.config.config import CONFIG
from origami.visuals.mpl.zoom import ZoomBox
from origami.visuals.mpl.zoom import GetXValues
from origami.visuals.mpl.new_zoom import MPLInteraction
from origami.gui_elements.misc_dialogs import DialogBox

matplotlib.use("WXAgg")


class MPLPanel(wx.Panel):
    def __init__(self, *args, **kwargs):

        if "figsize" in kwargs:
            self.figsize = kwargs.pop("figsize")
        else:
            self.figsize = [8, 2.5]

        if "axes_size" in kwargs:
            axes_size = kwargs.pop("axes_size")
            self._axes = axes_size
        else:
            self._axes = [0.15, 0.12, 0.8, 0.8]

        self.figure = Figure(figsize=self.figsize)

        if "config" in kwargs:
            kwargs.pop("config")

        self.window_name = kwargs.pop("window_name", None)

        wx.Panel.__init__(self, *args, **kwargs)
        self.canvas = FigureCanvasWxAgg(self, -1, self.figure)

        # RESIZE
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW, 0)
        self.SetSizer(sizer)
        self.Fit()
        self.Show()

        # Create a resizer
        self.Bind(wx.EVT_SIZE, self.on_resize)

        # Prepare for zoom
        self.zoom = None
        self.zoomtype = "box"
        self.plotName = None
        self.resize = 1
        self.screen_dpi = wx.ScreenDC().GetPPI()

        # obj containers
        self.text = []
        self.lines = []
        self.patch = []
        self.markers = []
        self.arrows = []
        self.temporary = []  # temporary holder

        self.lock_plot_from_updating = False
        self.lock_plot_from_updating_size = False
        self.plot_parameters = {}
        self.plot_limits = []

        # occasionally used to tag to mark what plot was used previously
        self._plot_tag = ""
        self.plot_name = ""
        self.plot_data = {}
        self.plot_labels = {}

        self.x_divider = 1
        self.y_divider = 1
        self.rotate = 0
        self.document_name = None
        self.dataset_name = None

        # plot data
        self.data_limits = []

    def __repr__(self):
        return f"Plot: {self.plotName} | Window name: {self.window_name} | Axes size: {self._axes}"

    def get_xlimits(self):
        return [self.data_limits[0], self.data_limits[2]]

    def get_ylimits(self):
        return [self.data_limits[1], self.data_limits[3]]

    def _generatePlotParameters(self):
        plot_parameters = {
            "grid_show": CONFIG._plots_grid_show,
            "grid_color": CONFIG._plots_grid_color,
            "grid_line_width": CONFIG._plots_grid_line_width,
            "extract_color": CONFIG._plots_extract_color,
            "extract_line_width": CONFIG._plots_extract_line_width,
            "extract_crossover_sensitivity_1D": CONFIG._plots_extract_crossover_1D,
            "extract_crossover_sensitivity_2D": CONFIG._plots_extract_crossover_2D,
            "zoom_color_vertical": CONFIG._plots_zoom_vertical_color,
            "zoom_color_horizontal": CONFIG._plots_zoom_horizontal_color,
            "zoom_color_box": CONFIG._plots_zoom_box_color,
            "zoom_line_width": CONFIG._plots_zoom_line_width,
            "zoom_crossover_sensitivity": CONFIG._plots_zoom_crossover,
        }
        return plot_parameters

    def setupGetXAxies(self, plots):
        self.getxaxis = GetXValues(plots)

    def setup_new_zoom(
        self, figure, data_limits=None, plot_parameters=None, allow_wheel=True, allow_extraction=True, callbacks=None
    ):
        if callbacks is None:
            callbacks = dict()

        if plot_parameters is None:
            plot_parameters = self._generatePlotParameters()

        self.zoom = MPLInteraction(
            figure,
            data_limits=data_limits,
            plot_parameters=plot_parameters,
            allow_extraction=allow_extraction,
            allow_wheel=allow_wheel,
            callbacks=callbacks,
        )

    def setup_zoom(
        self,
        plots,
        zoom,
        data_lims=None,
        plotName=None,
        plotParameters=None,
        allowWheel=True,
        allow_extraction=True,
        callbacks=dict(),
    ):
        if plotParameters is None:
            plotParameters = self._generatePlotParameters()

        self.data_limits = data_lims

        self.zoom = ZoomBox(
            plots,
            None,
            useblit=True,
            button=1,
            onmove_callback=None,
            rectprops=dict(alpha=0.2, facecolor="yellow"),
            spancoords="data",
            data_lims=data_lims,
            plotName=plotName,
            allow_mouse_wheel=allowWheel,
            allow_extraction=allow_extraction,
            plotParameters=plotParameters,
            callbacks=callbacks,
        )
        # self.onRebootZoomKeys(evt=None)

    def update_extents(self, extents):
        ZoomBox.update_extents(self.zoom, extents)

    def update_y_extents(self, y_min, y_max):
        ZoomBox.update_y_extents(self.zoom, y_min, y_max)

    def on_mark_annotation(self, state):
        try:
            ZoomBox.update_mark_state(self.zoom, state)
        except TypeError:
            pass
        except AttributeError:
            MPLInteraction.update_mark_state(self.zoom, state)

    def onRebootZoomKeys(self, evt):
        """
        Reboot 'stuck' keys
        """
        if self.zoom is not None:
            ZoomBox.onRebootKeyState(self.zoom, evt=None)

    def _convert_xaxis(self, xvals, x_label=""):
        """
        Adapted from Unidec/PlottingWindow.py

        Test whether the axis should be normalized to convert mass units from Da to kDa.
        Will use kDa if: xvals[int(len(xvals) / 2)] > 100000 or xvals[len(xvals) - 1] > 1000000

        If kDa is used, self.kda=True and self.kdnorm=1000. Otherwise, self.kda=False and self.kdnorm=1.
        :param xvals: mass axis
        :return: None
        """
        try:
            if xvals[int(len(xvals) / 2)] > 100000 or xvals[len(xvals) - 1] > 1000000:
                kda_norm_factor = 1000.0
                x_label = "Mass (kDa)"
                kda = True
            elif amax(xvals) > 10000:
                kda_norm_factor = 1000.0
                x_label = "Mass (kDa)"
                kda = True
            else:
                x_label = "Mass (Da)"
                kda = False
                kda_norm_factor = 1.0
        except (TypeError, ValueError):
            try:
                if xvals > 10000:
                    kda_norm_factor = 1000.0
                    x_label = "Mass (kDa)"
                    kda = True
            except Exception:
                x_label = "Mass (Da)"
                kda_norm_factor = 1.0
                kda = False

        # convert x-axis
        xvals = xvals / kda_norm_factor

        return xvals, x_label, kda

    def testXYmaxValsUpdated(self, values=None):
        """
        Function to check whether x/y axis labels do not need formatting
        """
        baseDiv = 10
        increment = 10
        divider = baseDiv

        try:
            itemShape = values.shape
        except Exception:
            from numpy import array

            values = array(values)
            itemShape = values.shape

        if len(itemShape) > 1:
            maxValue = amax(values)
        elif len(itemShape) == 1:
            maxValue = max(values)
        else:
            maxValue = values

        while 10 <= (maxValue / divider) >= 1:
            divider = divider * increment

        expo = len(str(divider)) - len(str(divider).rstrip("0"))

        return divider, expo

    def repaint(self):
        """
        Redraw and refresh the plot.
        :return: None
        """
        self.canvas.draw()

    def clear(self, *args):
        """
        Clear the plot and rest some of the parameters.
        :param args: Arguments
        :return:
        """
        self.figure.clear()

        # clear stores
        self.text = []
        self.lines = []
        self.patch = []
        self.markers = []
        self.arrows = []
        self.temporary = []

        # reset attributes
        self.rotate = 0

        # clear plots
        try:
            self.cax = None
        except Exception:
            pass

        try:
            self.plot_base = None
        except Exception:
            pass

        try:
            self.plot2D_upper = None
        except Exception:
            pass

        try:
            self.plot2D_lower = None
        except Exception:
            pass

        try:
            self.plot2D_side = None
        except Exception:
            pass

        try:
            self.plotRMSF = None
        except Exception:
            pass

        self.repaint()

    def on_resize(self, *args, **kwargs):

        if self.lock_plot_from_updating_size:
            self.SetBackgroundColour(wx.WHITE)
            return

        if self.resize == 1:
            self.canvas.SetSize(self.GetSize())

    def save_figure(self, path, **kwargs):
        """
        Saves figures in specified location.
        Transparency and DPI taken from config file
        """
        # check if plot exists
        if not hasattr(self, "plotMS"):
            print("Cannot save a plot that does not exist")
            return

        if kwargs.pop("tight", True):
            kwargs["bbox_inches"] = "tight"

        # Get resize parameter
        resize_name = kwargs.get("resize", None)
        resize_size_inch = None
        override_image_size_px = kwargs.pop("image_size_px", None)
        override_axes_size = kwargs.pop("image_axes_size", None)

        if resize_name is not None:
            resize_size_inch = CONFIG._plotSettings[resize_name]["resize_size"]

        if not hasattr(self.plot_base, "get_position"):
            resize_size_inch = None

        if resize_size_inch is not None and not self.lock_plot_from_updating_size:

            # Calculate new size
            resize_size_px = override_image_size_px
            if override_image_size_px is None:
                resize_size_px = (
                    int(resize_size_inch[0] * self.screen_dpi[0]),
                    int(resize_size_inch[1] * self.screen_dpi[1]),
                )

            # Set new canvas size and reset the view
            self.canvas.SetSize(resize_size_px)
            self.canvas.draw()
            # Get old and new plot sizes
            old_axes_size = self.plot_base.get_position()
            new_axes_size = override_axes_size
            if override_axes_size is None:
                new_axes_size = CONFIG._plotSettings[resize_name]["save_size"]

            try:
                self.plot_base.set_position(new_axes_size)
            except RuntimeError:
                self.plot_base.set_position(old_axes_size)

            self.repaint()

        # Save figure
        try:
            self.figure.savefig(path, **kwargs)
        except IOError:
            # reset axes size
            if resize_size_inch is not None and not self.lock_plot_from_updating_size:
                self.plot_base.set_position(old_axes_size)
                self.on_resize()
            # warn user
            DialogBox(
                exceptionTitle="Warning",
                exceptionMsg="Cannot save file: %s as it appears to be currently open or the folder doesn't exist"
                % path,
                type="Error",
            )
            # get file extension
            fname, delimiter_txt = os.path.splitext(path)
            try:
                bname = os.path.basename(fname)
            except Exception:
                bname = ""

            fileType = "Image file ({})|*{}".format(delimiter_txt, delimiter_txt)
            dlg = wx.FileDialog(None, "Save as...", "", "", fileType, wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
            dlg.SetFilename(bname)

            if dlg.ShowModal() == wx.ID_OK:
                fname, __ = os.path.splitext(dlg.GetPath())
                path = os.path.join(fname + delimiter_txt)

                # reset axes, again
                if resize_size_inch is not None and not self.lock_plot_from_updating_size:
                    self.canvas.SetSize(resize_size_px)
                    self.canvas.draw()
                    try:
                        self.plot_base.set_position(new_axes_size)
                    except RuntimeError:
                        self.plot_base.set_position(old_axes_size)
                    self.repaint()

                try:
                    kwargs["bbox_inches"] = "tight"
                    self.figure.savefig(path, **kwargs)
                except Exception:
                    try:
                        del kwargs["bbox_inches"]
                        self.figure.savefig(path, **kwargs)
                    except Exception:
                        pass

        # Reset previous view
        if resize_size_inch is not None and not self.lock_plot_from_updating_size:
            self.plot_base.set_position(old_axes_size)
            self.on_resize()

    def addText(self, xval=None, yval=None, text=None, rotation=90, color="k", fontsize=16, weight=True, plot=None):
        """
        This function annotates the MS peak
        """
        # Change label weight
        if weight:
            weight = "bold"
        else:
            weight = "regular"

        if plot in [None, "RMSD", "RMSF"]:
            self.text = self.plot_base.text(
                x=xval,
                y=yval,
                s=text,
                fontsize=fontsize,
                rotation=rotation,
                weight=weight,
                fontdict=None,
                color=color,
                clip_on=True,
            )

        elif plot == "Grid":
            self.text = self.plot2D_side.text(
                x=xval,
                y=yval,
                s=text,
                fontsize=fontsize,
                rotation=rotation,
                weight=weight,
                fontdict=None,
                color=color,
                clip_on=True,
            )

    def onZoomRMSF(self, startX, endX):
        x1, x2, y1, y2 = self.plotRMSF.axis()
        self.plotRMSF.axis([startX, endX, y1, y2])

    def onGetXYvals(self, axes="both"):
        xvals = self.plot_base.get_xlim()
        yvals = self.plot_base.get_ylim()
        if axes == "both":
            return xvals, yvals
        elif axes == "x":
            return xvals
        elif axes == "y":
            return yvals

    def get_plot_name(self):
        return self.plot_name
