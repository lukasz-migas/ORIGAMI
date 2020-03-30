"""Base class of the `View` object"""
# Standard library imports
from abc import ABC
from abc import abstractmethod
from typing import Optional

# Local imports
from origami.visuals.mpl.base import PlotBase


class ViewBase(ABC):
    def __init__(self, parent, figsize, title, **kwargs):
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
        self._x_label = None
        self._y_label = None
        self._z_label = None
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
    def x_label(self):
        return self._x_label

    @x_label.setter
    def x_label(self, value):
        if value == self._x_label:
            return
        self._x_label = value
        self._update()

    @property
    def y_label(self):
        return self._y_label

    @y_label.setter
    def y_label(self, value):
        if value == self._y_label:
            return
        self._y_label = value
        self._update()

    @property
    def z_label(self):
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

    def set_document(self, **kwargs):
        """Set document information for particular plot"""
        if "document" in kwargs:
            self.document_name = kwargs.pop("document")
        if "dataset" in kwargs:
            self.document_name = kwargs.pop("dataset")

    def set_labels(self, **kwargs):
        """Update plot labels without triggering replot"""
        if "x_label" in kwargs:
            self._x_label = kwargs.pop("x_label")
        if "y_label" in kwargs:
            self._y_label = kwargs.pop("y_label")
        if "z_label" in kwargs:
            self._z_label = kwargs.pop("z_label")

    def add_labels(self, x, y, text, **kwargs):
        """Add text label to the plot"""

    def add_h_lines(self, value, **kwargs):
        """Add text label to the plot"""

    def add_v_lines(self, value, **kwargs):
        """Add text label to the plot"""

    def add_rects(self, coordinates, **kwargs):
        """Add text label to the plot"""

    def add_line(self, x, y, **kwargs):
        """Add text label to the plot"""
