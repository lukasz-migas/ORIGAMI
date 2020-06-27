"""Base class of the `View` object"""
# Standard library imports
import os
import time
import logging
from abc import ABC
from abc import abstractmethod
from typing import Optional

# Third-party imports
import wx

# Local imports
from origami.config.config import CONFIG
from origami.utils.utilities import report_time
from origami.visuals.mpl.base import PlotBase
from origami.objects.containers import DataObject

LOGGER = logging.getLogger(__name__)


class ViewBase(ABC):
    """Viewer base class"""

    DATA_KEYS = []
    MPL_KEYS = []

    def __init__(self, parent, figsize, title="", **kwargs):
        self.parent = parent
        self.figsize = figsize
        self.title = title

        # ui elements
        self.panel = None
        self.sizer = None
        self.figure: Optional[PlotBase] = None

        # process settings
        self._allow_extraction = kwargs.pop("allow_extraction", False)
        self._callbacks = kwargs.pop("callbacks", dict())

        # user settings
        self._x_label = kwargs.pop("x_label", None)
        self._y_label = kwargs.pop("y_label", None)
        self._z_label = kwargs.pop("z_label", None)
        self._data = dict()
        self._plt_kwargs = dict()
        self.document_name = None
        self.dataset_name = None

    def __repr__(self):
        return f"{self.__class__.__name__}<title={self.title}>"

    @abstractmethod
    def plot(self, *args, **kwargs):
        raise NotImplementedError("Must implement method")

    @abstractmethod
    def update(self, *args, **kwargs):
        raise NotImplementedError("Must implement method")

    @abstractmethod
    def replot(self, **kwargs):
        raise NotImplementedError("Must implement method")

    @abstractmethod
    def _update(self):
        raise NotImplementedError("Must implement method")

    @property
    def callbacks(self):
        """Return list of callbacks associated with the figure"""
        return self._callbacks

    @callbacks.setter
    def callbacks(self, value):
        self._callbacks = value

    @property
    def x_label(self):
        """Return x-axis label"""
        return self._x_label

    @x_label.setter
    def x_label(self, value):
        if value == self._x_label:
            return
        self._x_label = value
        self._update()

    @property
    def y_label(self):
        """Return y-axis label"""
        return self._y_label

    @y_label.setter
    def y_label(self, value):
        if value == self._y_label:
            return
        self._y_label = value
        self._update()

    @property
    def z_label(self):
        """Return z-axis label"""
        return self._z_label

    @z_label.setter
    def z_label(self, value):
        if value == self._z_label:
            return
        self._z_label = value
        self._update()

    def set_data(self, **kwargs):
        """Update plot data"""
        changed = False
        if self.DATA_KEYS is not None:
            for key, value in kwargs.items():
                if key in self.DATA_KEYS:
                    self._data[key] = value
                    changed = True

        if changed:
            self._update()

    def get_data(self, keys=None):
        """Get plot data"""
        if keys is None:
            keys = self.DATA_KEYS
        data = []
        for key in keys:
            data.append(self._data[key])

        return data

    def update_data(self, **kwargs):
        """Update data store without invoking plot update"""
        for key, value in kwargs.items():
            self._data[key] = value

    def set_document(self, obj: Optional[DataObject] = None, **kwargs):
        """Set document information for particular plot"""
        document, dataset = None, None
        if obj and obj.owner is not None:
            document, dataset = obj.owner
        else:
            document = kwargs.pop("document", None)
            dataset = kwargs.pop("dataset", None)

        self.document_name = document
        self.document_name = dataset

    def set_labels(self, obj: Optional[DataObject] = None, **kwargs):
        """Update plot labels without triggering replot"""

        def remove_keys(key):
            """Remove key from kwargs"""
            if key in kwargs:
                del kwargs[key]

        x_label, y_label, z_label = self._x_label, self._y_label, self._z_label
        if obj and obj.owner is not None:
            x_label = obj.x_label
            y_label = obj.y_label
            if hasattr(obj, "z_label"):
                z_label = obj.z_label
        else:
            x_label = kwargs.pop("x_label", self._x_label)
            y_label = kwargs.pop("y_label", self._y_label)
            z_label = kwargs.pop("z_label", self._z_label)

        self._x_label = x_label
        self._y_label = y_label
        self._z_label = z_label
        remove_keys("x_label"), remove_keys("y_label"), remove_keys("z_label")

    def repaint(self):
        """Repaint plot"""
        self.figure.repaint()

    def add_scatter(self, x, y, color="r", marker="o", size=5, repaint: bool = True):
        """Add scatter points to the plot"""
        #         if isinstance(color, list):
        #             assert len(color) == len(x), "Number of colors must match the number of markers"

        self.figure.plot_add_markers(xvals=x, yvals=y, color=color, marker=marker, size=size)
        if repaint:
            self.figure.repaint()

    def remove_scatter(self, repaint: bool = True):
        """Remove scatter points from the plot area"""
        self.figure.plot_remove_markers(False)

        if repaint:
            self.figure.repaint()

    def add_labels(
        self, x, y, label, name=None, color=None, optimize_labels: bool = False, repaint: bool = True, **kwargs
    ):
        """Add text label to the plot"""
        plt_kwargs = {
            "horizontalalignment": kwargs.pop("horizontal_alignment", "center"),
            "verticalalignment": kwargs.pop("vertical_alignment", "center"),
            "check_yscale": kwargs.pop("check_yscale", False),
            "butterfly_plot": kwargs.pop("butterfly_plot", False),
            "fontweight": kwargs.pop("font_weight", "normal"),
            "fontsize": kwargs.pop("font_size", "medium"),
        }
        y_offset = kwargs.get("yoffset", 0.0)
        if name is None:
            name = [None] * len(x)
        if color is None:
            color = ["k"] * len(x)

        for _x, _y, _label, _name, _color in zip(x, y, label, name, color):
            self.figure.plot_add_text(_x, _y, _label, text_name=_name, color=_color, yoffset=y_offset, **plt_kwargs)

        if optimize_labels:
            self.figure._fix_label_positions()

        if repaint:
            self.figure.repaint()

    def remove_labels(self, repaint: bool = True):
        """Remove scatter points from the plot area"""
        self.figure.plot_remove_text(False)

        if repaint:
            self.figure.repaint()

    def add_h_line(self, y_val, x_min: float = None, x_max: float = None, **kwargs):
        """Add horizontal line to the plot"""
        _x_min, _x_max = self.figure.get_xlim()
        if x_min is None:
            x_min = _x_min
        if x_max is None:
            x_max = _x_max

        self.figure.plot_add_line(x_min, x_max, y_val, y_val, "horizontal")
        self.figure.repaint()

    def add_v_line(self, x_val, y_min: float = None, y_max: float = None, repaint: bool = True, **kwargs):
        """Add vertical line to the plot"""
        _y_min, _y_max = self.figure.get_ylim()
        if y_min is None:
            y_min = _y_min
        if y_max is None:
            y_max = _y_max

        self.figure.plot_add_line(x_val, x_val, y_min, y_max, "vertical")
        if repaint:
            self.figure.repaint()

    def add_patches(self, x, y, width, height, label=None, color=None, pickable: bool = True, repaint: bool = True):
        """Add rectangular patches to the plot"""
        assert len(x) == len(y) == len(width), "Incorrect shape of the data. `x, y, width` must have the same length"
        if label is None:
            label = [None] * len(x)
        if color is None:
            color = ["r"] * len(x)
        for _x, _y, _width, _height, _label, _color in zip(x, y, width, height, label, color):
            self.figure.plot_add_patch(_x, _y, _width, _height, label=_label, color=_color, pickable=pickable)
            # , color=color, alpha=alpha, label=label, **kwargs)

        if repaint:
            self.figure.repaint()

    def remove_patches(self, repaint: bool = True):
        """Remove rectangular patches from the plot"""
        self.figure.plot_remove_patches(False)

        if repaint:
            self.figure.repaint()

    def add_arrows(self, arrow_values, name=None, repaint: bool = True):
        """Add arrows patches to the plot"""
        if name is None:
            name = [None] * len(arrow_values)
        for _arrow_value, _name in zip(arrow_values, name):
            self.figure.plot_add_arrow(_arrow_value, text_name=_name)

        if repaint:
            self.figure.repaint()

    def remove_arrows(self, repaint: bool = True):
        """Remove arrows patches from the plot"""
        self.figure.plot_remove_arrows(False)

        if repaint:
            self.figure.repaint()

    def add_line(self, x, y, **kwargs):
        """Add text label to the plot"""

    def set_xlim(self, x_min: float, x_max: float):
        """Set x-axis limits in the plot area"""
        self.figure.on_zoom_x_axis(x_min, x_max)
        self.figure.repaint()

    def set_ylim(self, y_min: float, y_max: float):
        """Set y-axis limits in the plot area"""
        self.figure.on_zoom_y_axis(y_min, y_max)
        self.figure.repaint()

    def set_xylim(self, x_min: float, x_max: float, y_min: float, y_max: float):
        """Set xy-axis limits in the plot area"""
        self.figure.on_zoom_xy_axis(x_min, x_max, y_min, y_max)
        self.figure.repaint()

    def copy_to_clipboard(self):
        """Copy plot to clipboard"""
        return self.figure.copy_to_clipboard()

    def save_figure(self, filename, **kwargs):
        """Export figure"""
        # setup file dialog
        wildcard = (
            "SVG Scalable Vector Graphic (*.svg)|*.svg|"
            + "SVGZ Compressed Scalable Vector Graphic (*.svgz)|*.svgz|"
            + "PNG Portable Network Graphic (*.png)|*.png|"
            + "Enhanced Windows Metafile (*.eps)|*.eps|"
            + "JPEG File Interchange Format (*.jpeg)|*.jpeg|"
            + "TIFF Tag Image File Format (*.tiff)|*.tiff|"
            + "RAW Image File Format (*.raw)|*.raw|"
            + "PS PostScript Image File Format (*.ps)|*.ps|"
            + "PDF Portable Document Format (*.pdf)|*.pdf"
        )

        wildcard_dict = {"svg": 0, "svgz": 1, "png": 2, "eps": 3, "jpeg": 4, "tiff": 5, "raw": 6, "ps": 7, "pdf": 8}

        dlg = wx.FileDialog(
            self.parent, "Save as...", "", "", wildcard=wildcard, style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        )
        dlg.CentreOnParent()
        dlg.SetFilename(filename)
        try:
            dlg.SetFilterIndex(wildcard_dict[CONFIG.imageFormat])
        except Exception:
            LOGGER.error("Could not set image format")

        if dlg.ShowModal() == wx.ID_OK:
            t_start = time.time()
            filename = dlg.GetPath()
            __, extension = os.path.splitext(filename)
            CONFIG.imageFormat = extension[1::]

            # build kwargs
            kwargs = {
                "transparent": CONFIG.transparent,
                "dpi": CONFIG.dpi,
                "format": extension[1::],
                "compression": "zlib",
                "resize": None,
                "tight": CONFIG.image_tight,
            }

            # if CONFIG.resize:
            #     kwargs["resize"] = resizeName

            self.figure.save_figure(path=filename, **kwargs)

            LOGGER.info(f"Saved figure in {report_time(t_start)}")
        dlg.Destroy()
