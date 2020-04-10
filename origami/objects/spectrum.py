# Third-party imports
import numpy as np

# Local imports
from origami.utils.ranges import get_min_max


class DataObject:
    def __init__(self, name, x, y, x_label, y_label, x_label_options=None, y_label_options=None):
        self.name = name
        self._x = x
        self._y = y
        self._x_label = x_label
        self._y_label = y_label
        self._x_limit = None
        self._y_limit = None
        self._x_label_options = x_label_options
        self._y_label_options = y_label_options

    @property
    def x_label(self):
        return self._x_label

    @property
    def y_label(self):
        return self._y_label

    @property
    def x_label_options(self):
        if self._x_label_options is None:
            self._x_label_options = [self._x_label]
        return self._x_label_options

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    @property
    def x_limit(self):
        if self._x_limit:
            self._x_limit = get_min_max(self.x)
        return self._x_limit

    @property
    def y_limit(self):
        if self._y_limit:
            self._y_limit = get_min_max(self.x)
        return self._y_limit

    def save_to_hdf5(self):
        pass

    def save_to_csv(self):
        pass

    def save_to_json(self):
        pass

    def to_dict(self):
        raise NotImplementedError("Must implement method")


class SpectrumObject(DataObject):
    def __init__(self, x, y, x_label: str, y_label: str, name: str, **kwargs):
        super().__init__(name, x, y, x_label, y_label, **kwargs)

    def to_dict(self):
        return {
            "xvals": self.x,
            "yvals": self.y,
            "xlimits": self.x_limit,
            "xlabels": self.x_label,
            "ylabels": self.y_label,
        }


class MassSpectrumObject(SpectrumObject):
    def __init__(self, x, y, name: str):
        super().__init__(x, y, x_label="m/z (Da)", y_label="Intensity", name=name)


class ChromatogramObject(SpectrumObject):
    def __init__(self, x, y, name: str):
        super().__init__(
            x, y, x_label="Scans", y_label="Intensity", name=name, x_label_options=["Scans", "Retention time (mins)"]
        )


class HeatmapObject(DataObject):
    def __init__(
        self,
        array: np.ndarray,
        name: str,
        x=None,
        y=None,
        xy=None,
        yy=None,
        x_label: str = "x-axis",
        y_label: str = "y-axis",
    ):
        super().__init__(name, x, y, x_label, y_label)
        self._array = array
        self._xy = xy
        self._yy = yy

    @property
    def x(self):
        if self._x is None:
            self._x = np.arange(1, self.shape[1])
        return self._x

    @property
    def y(self):
        if self._y is None:
            self._y = np.arange(1, self.shape[0])
        return self._y

    @property
    def xy(self):
        if self._xy is None:
            self._xy = self.array.sum(axis=0)
        return self._xy

    @property
    def yy(self):
        if self._yy is None:
            self._yy = self.array.sum(axis=1)
        return self._yy

    @property
    def array(self):
        return self._array

    @property
    def shape(self):
        return self._array.shape

    def to_dict(self):
        return {
            "xvals": self.x,
            "yvals": self.y,
            "zvals": self.array,
            "xvals_sum": self.xy,
            "yvals_sum": self.yy,
            "xlabels": self.x_label,
            "ylabels": self.y_label,
        }
