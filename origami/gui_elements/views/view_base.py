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
from origami.config.environment import ENV
from origami.objects.containers import DataObject

LOGGER = logging.getLogger(__name__)


class ViewMPLMixin:
    """Mixin class for matplotlib based views"""

    figure = None

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
            self.figure._fix_label_positions()  # noqa

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

    def add_patch(
        self,
        x: float,
        y: float,
        width: float,
        height: Optional[float],
        label: str = None,
        pickable: bool = True,
        repaint: bool = True,
    ):
        """Add rectangular patch to the plot"""
        self.figure.plot_add_patch(x, y, width, height, label=label, pickable=pickable)
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

    def reset_zoom(self):
        """Restore original extents of the plot"""
        self.figure.on_reset_zoom()


class ViewBase(ABC):
    """Viewer base class"""

    DATA_KEYS = []
    MPL_KEYS = []
    NAME = None
    UPDATE_STYLES = ()
    SUPPORTED_FILE_FORMATS = ("png", "eps", "jpeg", "tiff", "raw", "ps", "pdf", "svg", "svgz")

    def __init__(self, parent, figsize, title="", **kwargs):
        self.parent = parent
        self.figsize = figsize
        self.axes_size = kwargs.pop("axes_size", None)
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
        """Simple plot"""
        raise NotImplementedError("Must implement method")

    @abstractmethod
    def update(self, *args, **kwargs):
        """Quick update"""
        raise NotImplementedError("Must implement method")

    @abstractmethod
    def replot(self, **kwargs):
        """Full replot"""
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

    def set_object(self, data_obj):
        """Set Data object that is associated with the view"""
        self._data["obj"] = data_obj

    def get_object(self, get_cache: bool = True):
        """Get Data object that is shown in the View"""
        if self.document_name is None or self.dataset_name is None:
            return None

        # check whether object had been cached
        data_obj = None
        if get_cache:
            data_obj = self._data.get("obj", None)
        if data_obj is None:
            document = ENV.on_get_document(self.document_name)
            data_obj = document[self.dataset_name, True]

        return data_obj

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
        if obj and obj.owner is not None:
            document, dataset = obj.owner
        else:
            document = kwargs.pop("document", None)
            dataset = kwargs.pop("dataset", None)

        self.document_name = document
        self.dataset_name = dataset

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

    def clear(self):
        """Clear plot"""
        self.figure.clear()
        if "obj" in self._data:
            self._data["obj"] = None

    def copy_to_clipboard(self):
        """Copy plot to clipboard"""
        return self.figure.copy_to_clipboard()

    def save_figure(self, filename="", path=None, **kwargs):
        """Export figure"""

        def _get_path():
            wildcard, wildcard_dict = build_wildcard(self.SUPPORTED_FILE_FORMATS)
            dlg = wx.FileDialog(
                self.parent, "Save as...", "", "", wildcard=wildcard, style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
            )
            dlg.CentreOnParent()
            dlg.SetFilename(filename)
            try:
                dlg.SetFilterIndex(wildcard_dict[CONFIG.imageFormat])
            except Exception:
                LOGGER.error("Could not set image format")

            _path = None
            if dlg.ShowModal() == wx.ID_OK:
                _path = dlg.GetPath()
                __, extension = os.path.splitext(_path)
                CONFIG.imageFormat = extension[1::]
            dlg.Destroy()

            return _path

        if path is None:
            path = _get_path()

        if path is None:
            return
        t_start = time.time()

        # if CONFIG.resize:
        #     kwargs["resize"] = resizeName

        self.figure.savefig(
            path=path,
            transparent=CONFIG.transparent,
            dpi=CONFIG.dpi,
            image_fmt=CONFIG.imageFormat,
            compression="zlib",
            resize=None,
            tight=CONFIG.image_tight,
        )

        LOGGER.info(f"Saved figure in {report_time(t_start)}")


def build_wildcard(supported_formats):
    """Build export wildcard"""
    _wildcards = dict(
        png="PNG Portable Network Graphic (*.png)|*.png",
        eps="Enhanced Windows Metafile (*.eps)|*.eps",
        jpeg="JPEG File Interchange Format (*.jpeg)|*.jpeg",
        tiff="TIFF Tag Image File Format (*.tiff)|*.tiff",
        raw="RAW Image File Format (*.raw)|*.raw",
        ps="PS PostScript Image File Format (*.ps)|*.ps",
        pdf="PDF Portable Document Format (*.pdf)|*.pdf",
        svg="SVG Scalable Vector Graphic (*.svg)|*.svg",
        svgz="SVGZ Compressed Scalable Vector Graphic (*.svgz)|*.svgz",
    )

    wildcard = ""
    wildcard_dict = {}

    n_formats = len(supported_formats) - 1
    for i, fmt in enumerate(supported_formats):
        value = _wildcards[fmt]
        if i < n_formats:
            value += "|"
        wildcard += value
        wildcard_dict[fmt] = i

    return wildcard, wildcard_dict
