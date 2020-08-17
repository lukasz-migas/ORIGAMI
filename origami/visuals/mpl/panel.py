# Standard library imports
import os
import logging
from typing import List

# Third-party imports
import wx
import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg

# Local imports
from origami.config.config import CONFIG
from origami.visuals.mpl.new_zoom import MPLInteraction
from origami.gui_elements.misc_dialogs import DialogBox

matplotlib.use("WXAgg")
matplotlib.rcParams["agg.path.chunksize"] = 10000

LOGGER = logging.getLogger(__name__)


class MPLPanel(wx.Panel):
    def __init__(self, *args, **kwargs):
        self.figsize = kwargs.pop("figsize", None)
        if self.figsize is None:
            self.figsize = [8, 4]

        # ensure minimal figure size
        if self.figsize[0] <= 0:
            self.figsize[0] = 1.0
        if self.figsize[1] <= 0:
            self.figsize[1] = 1.0

        axes_size = None
        if "axes_size" in kwargs:
            axes_size = kwargs.pop("axes_size")

        if axes_size is None:
            axes_size = [0.13, 0.18, 0.8, 0.75]
        self._axes = axes_size
        self.plot_id = kwargs.pop("plot_id", "")

        self.figure = Figure(figsize=self.figsize)

        if "config" in kwargs:
            kwargs.pop("config")

        self.window_name = kwargs.pop("window_name", None)

        wx.Panel.__init__(self, *args, **kwargs)
        self.canvas = FigureCanvasWxAgg(self, -1, self.figure)

        # RESIZE
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.EXPAND, 0)
        self.SetSizerAndFit(sizer)
        self.Show()

        self.SetBackgroundColour(wx.WHITE)
        # Create a resizer
        self.Bind(wx.EVT_SIZE, self.on_resize)
        self.Bind(wx.EVT_MOUSEWHEEL, self.on_wheel)

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
        self.PLOT_TYPE = None
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

    def on_wheel(self, evt):
        print(evt)

    def setup_new_zoom(
        self,
        figure,
        data_limits=None,
        plot_parameters=None,
        allow_wheel=True,
        allow_extraction=True,
        callbacks=None,
        is_heatmap: bool = False,
        is_joint: bool = False,
        obj=None,
    ):
        """Setup the new-style matplotlib zoom"""
        if callbacks is None:
            callbacks = dict()

        if plot_parameters is None:
            plot_parameters = CONFIG.get_zoom_parameters()

        self.zoom = MPLInteraction(
            figure,
            data_limits=data_limits,
            plot_parameters=plot_parameters,
            allow_extraction=allow_extraction,
            allow_wheel=allow_wheel,
            callbacks=callbacks,
            parent=self.GetParent(),
            is_heatmap=is_heatmap,
            is_joint=is_joint,
            obj=obj,
            plot_id=self.plot_id,
        )

    def update_extents(self, extents: List, obj=None):
        """Update plot extents"""
        self.zoom.update_handler(data_limits=extents, obj=obj)

    def repaint(self, repaint: bool = True):
        """Redraw and refresh the plot"""
        if repaint:
            self.canvas.draw()

    def clear(self):
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
        self.PLOT_TYPE = None

        # clear plots
        self.cax = None
        self.plot_base = None
        self.repaint()

    def on_resize(self, evt):
        """Update plot area as it is being resized"""
        if self.lock_plot_from_updating_size:
            self.SetBackgroundColour(wx.WHITE)
            return

        if self.resize == 1:
            self.canvas.SetSize(self.GetSize())
        evt.Skip()

    def savefig(
        self,
        path,
        tight: bool = True,
        dpi: int = 150,
        transparent: bool = True,
        compression: str = "zlib",
        image_fmt: "str" = "png",
        resize=None,
    ):
        """Export figure"""
        # TODO: add option to resize the plot area
        if not hasattr(self, "plot_base"):
            LOGGER.warning("Cannot save a plot that has not been plotted yet")
            return

        #         # get current plot information
        #         if resize:
        #             old_px_size, old_axes_size = self.GetSize(), None
        #             if hasattr(self.plot_base, "get_position"):
        #                 old_axes_size = self.plot_base.get_position()
        #
        #             new_px_size = (1000, 300)
        #             new_axes_size = (0.2, 0.2, 0.5, 0.5)
        #
        #             self.SetSize(new_px_size)
        #             self.plot_base.set_position(new_axes_size)
        #             self.canvas.draw()

        self.figure.savefig(
            path,
            transparent=transparent,
            dpi=dpi,
            compression=compression,
            format=image_fmt,
            optimize=True,
            quality=95,
            bbox_inces="tight" if tight else None,
        )

    #         if resize:
    #             self.SetSize(old_px_size)
    #             if old_axes_size is not None and hasattr(self.plot_base, "set_position"):
    #                 self.plot_base.set_position(old_axes_size)
    #             self.canvas.draw()

    def save_figure(self, path, **kwargs):
        """
        Saves figures in specified location.
        Transparency and DPI taken from config file
        """
        # check if plot exists
        if not hasattr(self, "plot_base"):
            LOGGER.warning("Cannot save a plot that does not exist")
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
                title="Warning",
                msg="Cannot save file: %s as it appears to be currently open or the folder doesn't exist" % path,
                kind="Error",
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

    def get_plot_name(self):
        """Get plot name"""
        return self.plot_name
