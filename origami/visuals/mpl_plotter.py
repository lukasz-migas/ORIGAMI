# Standard library imports
import os

# Third-party imports
import wx
import matplotlib
import matplotlib.patches as patches
from PIL import Image
from PIL import ImageChops
from numpy import amax
from numpy import divide
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D  # NOQA
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg

# Local imports
from origami.visuals.ZoomBox import ZoomBox
from origami.visuals.ZoomBox import GetXValues
from origami.gui_elements.misc_dialogs import DialogBox

matplotlib.use("WXAgg")


class mpl_plotter(wx.Panel):
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
            self.config = kwargs.pop("config")

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
            "grid_show": self.config._plots_grid_show,
            "grid_color": self.config._plots_grid_color,
            "grid_line_width": self.config._plots_grid_line_width,
            "extract_color": self.config._plots_extract_color,
            "extract_line_width": self.config._plots_extract_line_width,
            "extract_crossover_sensitivity_1D": self.config._plots_extract_crossover_1D,
            "extract_crossover_sensitivity_2D": self.config._plots_extract_crossover_2D,
            "zoom_color_vertical": self.config._plots_zoom_vertical_color,
            "zoom_color_horizontal": self.config._plots_zoom_horizontal_color,
            "zoom_color_box": self.config._plots_zoom_box_color,
            "zoom_line_width": self.config._plots_zoom_line_width,
            "zoom_crossover_sensitivity": self.config._plots_zoom_crossover,
        }
        return plot_parameters

    def setupGetXAxies(self, plots):
        self.getxaxis = GetXValues(plots)

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
        self.onRebootZoomKeys(evt=None)

    def update_extents(self, extents):
        ZoomBox.update_extents(self.zoom, extents)

    def update_y_extents(self, y_min, y_max):
        ZoomBox.update_y_extents(self.zoom, y_min, y_max)

    def _on_mark_annotation(self, state):
        try:
            ZoomBox.update_mark_state(self.zoom, state)
        except TypeError:
            pass

    def onRebootZoomKeys(self, evt):
        """
        Reboot 'stuck' keys
        """
        if self.zoom is not None:
            ZoomBox.onRebootKeyState(self.zoom, evt=None)

    def _convert_xaxis(self, xvals):
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
                kdnorm = 1000.0
                xlabel = "Mass (kDa)"
                kda = True
            elif amax(xvals) > 10000:
                kdnorm = 1000.0
                xlabel = "Mass (kDa)"
                kda = True
            else:
                xlabel = "Mass (Da)"
                kda = False
                kdnorm = 1.0
        except (TypeError, ValueError):
            try:
                if xvals > 10000:
                    kdnorm = 1000.0
                    xlabel = "Mass (kDa)"
                    kda = True
            except Exception:
                xlabel = "Mass (Da)"
                kdnorm = 1.0
                kda = False

        # convert x-axis
        xvals = xvals / kdnorm

        return xvals, xlabel, kda

    def testXYmaxVals(self, values=None):
        """
        Function to check whether x/y axis labels do not need formatting
        """
        if max(values) > 1000:
            divider = 1000
        elif max(values) > 1000000:
            divider = 1000000
        else:
            divider = 1
        return divider

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

    def clearPlot(self, *args):
        """
        Clear the plot and rest some of the parameters.
        :param args: Arguments
        :return:
        """
        self.figure.clear()
        # clear labels
        try:
            self.text = []
        except Exception:
            pass
        try:
            self.lines = []
        except Exception:
            pass
        try:
            self.patch = []
        except Exception:
            pass
        try:
            self.markers = []
        except Exception:
            pass
        try:
            self.arrows = []
        except Exception:
            pass
        try:
            self.temporary = []
        except Exception:
            pass

        self.rotate = 0

        # clear plots
        try:
            self.cax = None
        except Exception:
            pass

        try:
            self.plotMS = None
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

    def onselect(self, ymin, ymax):
        pass

    def pil_trim(self, im):
        bg = Image.new(im.mode, im.size, im.getpixel((0, 0)))
        diff = ImageChops.difference(im, bg)
        diff = ImageChops.add(diff, diff, 2.0, -100)
        bbox = diff.getbbox()
        if bbox:
            return im.crop(bbox)

    def saveFigure(self, path, transparent, dpi, **kwargs):
        """
        Saves figures in specified location.
        Transparency and DPI taken from config file
        """
        self.figure.savefig(path, transparent=transparent, dpi=dpi, **kwargs)

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
            resize_size_inch = self.config._plotSettings[resize_name]["resize_size"]

        if not hasattr(self.plotMS, "get_position"):
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
            old_axes_size = self.plotMS.get_position()
            new_axes_size = override_axes_size
            if override_axes_size is None:
                new_axes_size = self.config._plotSettings[resize_name]["save_size"]

            try:
                self.plotMS.set_position(new_axes_size)
            except RuntimeError:
                self.plotMS.set_position(old_axes_size)

            self.repaint()

        # Save figure
        try:
            self.figure.savefig(path, **kwargs)
        except IOError:
            # reset axes size
            if resize_size_inch is not None and not self.lock_plot_from_updating_size:
                self.plotMS.set_position(old_axes_size)
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
                        self.plotMS.set_position(new_axes_size)
                    except RuntimeError:
                        self.plotMS.set_position(old_axes_size)
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
            self.plotMS.set_position(old_axes_size)
            self.on_resize()

    def onAddMarker(self, xval=None, yval=None, marker="s", color="r", size=5, testMax="none", label="", as_line=True):
        """
        This function adds a marker to 1D plot
        """
        if testMax == "yvals":
            ydivider, expo = self.testXYmaxValsUpdated(values=yval)
            if expo > 1:
                yvals = divide(yval, float(ydivider))

        if as_line:
            self.plotMS.plot(
                xval,
                yval,
                color=color,
                marker=marker,
                linestyle="None",
                markersize=size,
                markeredgecolor="k",
                label=label,
            )
        else:
            self.plotMS.scatter(xval, yval, color=color, marker=marker, s=size, edgecolor="k", label=label, alpha=1.0)

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
            self.text = self.plotMS.text(
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

    def addRectangle(self, x, y, width, height, color="green", alpha=0.5, linewidth=0):
        """
        Add rect patch to plot
        """
        # (x,y), width, height, alpha, facecolor, linewidth
        add_patch = patches.Rectangle((x, y), width, height, color=color, alpha=alpha, linewidth=linewidth)
        self.plotMS.add_patch(add_patch)

    def onZoomIn(self, startX, endX, endY):
        self.plotMS.axis([startX, endX, 0, endY])

    def onZoomRMSF(self, startX, endX):
        x1, x2, y1, y2 = self.plotRMSF.axis()
        self.plotRMSF.axis([startX, endX, y1, y2])

    def onGetXYvals(self, axes="both"):
        xvals = self.plotMS.get_xlim()
        yvals = self.plotMS.get_ylim()
        if axes == "both":
            return xvals, yvals
        elif axes == "x":
            return xvals
        elif axes == "y":
            return yvals

    def get_plot_name(self):
        return self.plot_name

    def get_axes_size(self):
        return self._axes
