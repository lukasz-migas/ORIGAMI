"""Base class of the `View` object"""
# Standard library imports
import os
import time
import logging
from abc import ABC
from abc import abstractmethod
from typing import Union
from typing import Optional

# Third-party imports
import wx
import numpy as np
from pubsub import pub

# Local imports
from origami.icons.assets import Icons
from origami.config.config import CONFIG
from origami.utils.utilities import report_time
from origami.utils.exceptions import IncorrectPlotTypeError
from origami.utils.exceptions import PlotTypeNotPlottedWarning
from origami.config.environment import ENV
from origami.objects.containers import DataObject
from origami.gui_elements.helpers import make_menu_item
from origami.visuals.mpl.plot_base import PlotBase
from origami.gui_elements.views.view_about_popup import ViewAboutPopup

LOGGER = logging.getLogger(__name__)


class ViewMPLMixin:
    """Mixin class for matplotlib based views"""

    figure = None

    def show_legend(self, show=True, draggable: bool = True, repaint: bool = True):
        """Show legend"""
        self.figure.set_legend_parameters(None, draggable=draggable, legend=show)
        self.figure.repaint(repaint)

    def add_scatter(self, x, y, color="r", marker="o", size=5, label="", repaint: bool = True):
        """Add scatter points to the plot"""
        self.figure.plot_add_markers(x=x, y=y, color=color, marker=marker, label=label, size=size)
        if repaint:
            self.figure.repaint()

    def remove_scatter(self, repaint: bool = True):
        """Remove scatter points from the plot area"""
        self.figure.plot_remove_markers(False)
        self.figure.repaint(repaint)

    def add_labels(
        self,
        x,
        y,
        label,
        name=None,
        color=None,
        optimize_labels: bool = False,
        pickable: bool = True,
        repaint: bool = True,
        **kwargs,
    ):
        """Add text label to the plot"""
        plt_kwargs = {
            "horizontalalignment": kwargs.pop("annotation_label_horz", "center"),
            "verticalalignment": kwargs.pop("annotation_label_vert", "center"),
            "check_yscale": kwargs.pop("check_yscale", False),
            "butterfly_plot": kwargs.pop("butterfly_plot", False),
            "fontweight": kwargs.pop("annotation_label_font_weight", "normal"),
            "fontsize": kwargs.pop("annotation_label_font_size", "medium"),
        }
        y_offset = kwargs.get("yoffset", 0.0)
        if name is None:
            name = [None] * len(x)
        if color is None:
            color = ["k"] * len(x)

        for _x, _y, _label, _name, _color in zip(x, y, label, name, color):
            self.figure.plot_add_label(
                _x, _y, _label, text_name=_name, color=_color, y_offset=y_offset, pickable=pickable, **plt_kwargs
            )

        if optimize_labels:
            self.figure._fix_label_positions()  # noqa
        self.figure.repaint(repaint)

    def remove_labels(self, start_with: str = None, repaint: bool = True):
        """Remove scatter points from the plot area"""
        self.figure.plot_remove_label(start_with, repaint=False)
        self.figure.repaint(repaint)

    def add_slope(self, x_min: np.ndarray, intercept: float, slope: float, label="Slope", repaint: bool = True):
        """Add slope to the plot"""
        self.figure.plot_add_slope(x_min, intercept, slope, label=label)
        self.figure.repaint(repaint)

    def add_h_line(
        self, y_val, x_min: float = None, x_max: float = None, label=None, repaint: bool = True, **kwargs
    ):  # noqa
        """Add horizontal line to the plot"""
        _x_min, _x_max = self.figure.get_xlim()
        if x_min is None:
            x_min = _x_min
        if x_max is None:
            x_max = _x_max

        self.figure.plot_add_line(x_min, x_max, y_val, y_val, "horizontal", label=label)
        self.figure.repaint(repaint)

    def add_v_line(
        self,
        x_val,
        y_min: float = None,
        y_max: float = None,
        label=None,
        color=(1, 0, 0),
        repaint: bool = True,
        **kwargs,
    ):  # noqa
        """Add vertical line to the plot"""
        _y_min, _y_max = self.figure.get_ylim()
        if y_min is None:
            y_min = _y_min
        if y_max is None:
            y_max = _y_max

        self.figure.plot_add_line(x_val, x_val, y_min, y_max, "vertical", label=label, color=color)
        self.figure.repaint(repaint)

    def remove_lines(self, repaint: bool = True):
        """Remove scatter points from the plot area"""
        self.figure.plot_remove_lines(False)

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
        self.figure.repaint(repaint)

    def add_patches(self, x, y, width, height, label=None, color=None, pickable: bool = True, repaint: bool = True):
        """Add rectangular patches to the plot"""
        assert len(x) == len(y) == len(width), "Incorrect shape of the data. `x, y, width` must have the same length"
        if label is None:
            label = [None] * len(x)
        if color is None:
            color = ["r"] * len(x)
        for _x, _y, _width, _height, _label, _color in zip(x, y, width, height, label, color):
            self.figure.plot_add_patch(_x, _y, _width, _height, label=_label, color=_color, pickable=pickable)
        self.figure.repaint(repaint)

    def remove_patches(self, repaint: bool = True):
        """Remove rectangular patches from the plot"""
        self.figure.plot_remove_patches(False)
        self.figure.repaint(repaint)

    def add_arrows(self, arrow_values, name=None, repaint: bool = True):
        """Add arrows patches to the plot"""
        if name is None:
            name = [None] * len(arrow_values)
        for _arrow_value, _name in zip(arrow_values, name):
            self.figure.plot_add_arrow(_arrow_value, text_name=_name)
        self.figure.repaint(repaint)

    def remove_arrows(self, repaint: bool = True):
        """Remove arrows patches from the plot"""
        self.figure.plot_remove_arrows(False)
        self.figure.repaint(repaint)

    def set_xlim(self, x_min: float, x_max: float):
        """Set x-axis limits in the plot area"""
        self.figure.on_zoom_x_axis(x_min, x_max)
        self.figure.repaint()

    def get_current_xlim(self):
        """Return the x-limit of the plot"""
        return self.figure.get_current_xlim()

    def get_xlim(self):
        """Return the x-limit of the plot"""
        return self.figure.get_xlim()

    def set_ylim(self, y_min: float, y_max: float):
        """Set y-axis limits in the plot area"""
        self.figure.on_zoom_y_axis(y_min, y_max)
        self.figure.repaint()

    def get_ylim(self):
        """Return the x-limit of the plot"""
        return self.figure.get_ylim()

    def set_xylim(self, x_min: float, x_max: float, y_min: float, y_max: float):
        """Set xy-axis limits in the plot area"""
        self.figure.on_zoom_xy_axis(x_min, x_max, y_min, y_max)
        self.figure.repaint()

    def reset_zoom(self):
        """Restore original extents of the plot"""
        self.figure.on_reset_zoom()


class ViewBase(ABC):
    """Viewer base class"""

    DEFAULT_PLOT = None
    DATA_KEYS = []
    MPL_KEYS = []
    PLOT_ID = None
    UPDATE_STYLES = ()
    ALLOWED_PLOTS = ()
    FORCED_KWARGS = {}
    SUPPORTED_FILE_FORMATS = ("png", "eps", "jpeg", "tiff", "raw", "ps", "pdf", "svg", "svgz")

    # ui elements
    lock_plot_check = None
    resize_plot_check = None

    def __init__(self, parent, figsize, title="", **kwargs):
        self.parent = parent
        self.figsize = figsize
        self.axes_size = kwargs.pop("axes_size", None)
        self.title = title
        self.filename = kwargs.pop("filename", "")
        self._icons = Icons()

        # ui elements
        self.panel = None
        self.sizer = None
        self.figure: Optional[PlotBase] = None
        self._tooltip_timer = None

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

        pub.subscribe(self.on_activate_document, "view.activate")

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

    def update_style(self, name: str):
        """Update plot style"""
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

    @property
    def plot_type(self):
        """Return currently shown plot type"""
        return self.figure.PLOT_TYPE

    def _set_forced_kwargs(self):
        """Dynamically update force plot keyword arguments"""

    def on_activate_document(self, view_id: str):
        """Whenever the event is emitted, the view should send another event to indicate that the current document has
        been changed"""
        if view_id != self.PLOT_ID or self.document_name is None:
            return
        pub.sendMessage("document.activate", document_title=self.document_name)

    def set_plot_parameters(self, **kwargs):
        """Update plot kwargs"""
        self._plt_kwargs.update(**kwargs)

    def snapshot(self, flush: bool = False):
        """Take snapshot of current parameters so plot can be reproduced exactly"""
        return self._plt_kwargs

    def can_plot(self, plot_type: str):
        """Check whether specified plot can be displayed"""
        if plot_type in self.ALLOWED_PLOTS:
            return
        raise IncorrectPlotTypeError(f"Plot `{plot_type}` cannot be displayed in this view")

    def is_plotted(self, plot_type: str):
        """Check whether specified plot is plotted"""
        if self.figure.PLOT_TYPE == plot_type:
            return
        raise PlotTypeNotPlottedWarning(f"Plot `{plot_type}` has not been plotted yet")

    def is_plotted_or_plot(self, plot_type: str, plot_func, data_keys):
        """Check whether specified plot is plotted and if not, plot it afresh"""
        try:
            self.is_plotted(plot_type)
            return True
        except PlotTypeNotPlottedWarning:
            plot_func(**self.get_data(data_keys, as_dict=True))
            return False

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

    def get_data(self, keys=None, as_dict: bool = False):
        """Get plot data"""
        if keys is None:
            keys = self.DATA_KEYS

        if as_dict:
            data = {}
        else:
            data = []
        for key in keys:
            if as_dict:
                data[key] = self._data[key]
            else:
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

    def get_plot_type(self, plot_type) -> str:
        """Get current or new plot type"""
        if plot_type is None:
            if isinstance(self.figure.PLOT_TYPE, str):
                plot_type = self.figure.PLOT_TYPE
            else:
                plot_type = self.DEFAULT_PLOT
        return plot_type

    def repaint(self, repaint: bool = True):
        """Repaint plot"""
        self.figure.repaint(repaint)

    def clear(self):
        """Clear plot"""
        self.figure.clear()

        # clear old data
        for key in self.DATA_KEYS:
            self._data[key] = None
        if "obj" in self._data:
            self._data["obj"] = None

        self.figure.PLOT_TYPE = None

    def light_clear(self):
        """Surface-only clear of the plot without resetting the data"""
        self.figure.clear()

    def copy_to_clipboard(self):
        """Copy plot to clipboard"""
        return self.figure.copy_to_clipboard()

    def save_figure(self, filename="", path=None, **kwargs):  # noqa
        """Export figure"""

        # get the default filename that was set on the view
        if self.filename not in ["", None] and filename in ["", None]:
            filename = self.filename

        def _get_path():
            wildcard, wildcard_dict = build_wildcard(self.SUPPORTED_FILE_FORMATS)
            dlg = wx.FileDialog(
                self.parent, "Save as...", "", "", wildcard=wildcard, style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
            )
            dlg.CentreOnParent()
            dlg.SetFilename(filename)
            try:
                dlg.SetFilterIndex(wildcard_dict[CONFIG.imageFormat])
            except KeyError:
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
            pub.sendMessage("notify.message.warning", message="Cancelled figure save")
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
        pub.sendMessage("notify.message.info", message=f"Saved figure in {report_time(t_start)}")

    def get_right_click_menu(self, parent: Union[wx.Panel, wx.MiniFrame, wx.Frame]):
        """Get the commonly used right-click menu items

        Once the menu object is instantiated, it can be modified by `Prepend` or `Append` methods to add additional
        handlers.

        Parameters
        ----------
        parent
            parent object where the events can be bound to

        Returns
        -------
        menu : wx.Menu
            menu object with few of the commonly used events
        """
        menu = wx.Menu()

        # create menu items
        menu_save = make_menu_item(parent=menu, evt_id=wx.ID_ANY, text="Save figure as...", bitmap=self._icons.png)
        menu_clipboard = make_menu_item(parent=menu, text="Copy plot to clipboard", bitmap=self._icons.filelist)
        menu_clear = make_menu_item(parent=menu, text="Clear plot", bitmap=self._icons.clear)
        menu_info = make_menu_item(parent=menu, text="About plot...", bitmap=self._icons.info)

        self.lock_plot_check = menu.AppendCheckItem(wx.ID_ANY, "Lock plot", help="")
        self.lock_plot_check.Check(self.figure.lock_plot_from_updating)
        menu.AppendSeparator()
        self.resize_plot_check = menu.AppendCheckItem(wx.ID_ANY, "Resize on saving", help="")
        self.resize_plot_check.Check(self.figure.resize)
        menu.Append(menu_save)
        menu.Append(menu_clipboard)
        menu.AppendSeparator()
        menu.Append(menu_info)
        menu.AppendSeparator()
        menu.Append(menu_clear)

        # bind menu items to event handlers
        parent.Bind(wx.EVT_MENU, self.on_copy_to_clipboard, menu_clipboard)
        parent.Bind(wx.EVT_MENU, self.on_save_figure, menu_save)
        parent.Bind(wx.EVT_MENU, self.on_clear_plot, menu_clear)
        parent.Bind(wx.EVT_MENU, self.on_lock_plot, self.lock_plot_check)
        parent.Bind(wx.EVT_MENU, self.on_resize_check, self.resize_plot_check)
        parent.Bind(wx.EVT_MENU, self.on_open_about, menu_info)

        return menu

    def on_clear_plot(self, _evt):
        """Clear plot area"""
        self.figure.clear()
        pub.sendMessage("notify.message.info", message="Cleared plot area")

    def on_copy_to_clipboard(self, _evt):
        """Clear plot area"""
        self.figure.copy_to_clipboard()
        pub.sendMessage("notify.message.info", message="Copied figure to clipboard")

    def on_save_figure(self, _evt):
        """Clear plot area"""
        self.save_figure()

    def on_lock_plot(self, _evt):
        """Lock/unlock plot"""
        self.figure.lock_plot_from_updating = not self.figure.lock_plot_from_updating
        verb = "Locked" if self.figure.lock_plot_from_updating else "Unlocked"
        pub.sendMessage("notify.message.info", message=f"{verb} figure")

    def on_resize_check(self, _evt):
        """Enable/disable plot resizing"""
        self.figure.resize = not self.figure.resize
        verb = "Enabled" if self.figure.resize else "Disabled"
        pub.sendMessage("notify.message.info", message=f"{verb} figure resize on save")

    def on_open_about(self, _evt):
        """Open settings of the Document Tree"""
        popup = ViewAboutPopup(self.panel, self)
        popup.position_on_mouse()
        popup.Show()
        return popup


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
