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
    def __init__(self, parent, figsize, title="", **kwargs):
        self.parent = parent
        self.figsize = figsize
        self.title = title
        self.DATA_KEYS = None

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

    def add_labels(self, x, y, text, **kwargs):
        """Add text label to the plot"""

    def add_h_line(self, y_val, x_min: float = None, x_max: float = None, **kwargs):
        """Add horizontal line to the plot"""
        _x_min, _x_max = self.figure.get_xlim()
        if x_min is None:
            x_min = _x_min
        if x_max is None:
            x_max = _x_max

        self.figure.plot_add_line(x_min, x_max, y_val, y_val, "horizontal")
        self.figure.repaint()

    def add_v_line(self, x_val, y_min: float = None, y_max: float = None, **kwargs):
        """Add vertical line to the plot"""
        _y_min, _y_max = self.figure.get_ylim()
        if y_min is None:
            y_min = _y_min
        if y_max is None:
            y_max = _y_max

        self.figure.plot_add_line(x_val, x_val, y_min, y_max, "vertical")
        self.figure.repaint()

    def add_rects(self, coordinates, **kwargs):
        """Add text label to the plot"""

    def add_line(self, x, y, **kwargs):
        """Add text label to the plot"""

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
