"""Container base"""
# Standard library imports
from typing import Any
from typing import Dict

# Third-party imports
import numpy as np
from zarr import Group

# Local imports
from origami.utils.path import get_duplicate_name
from origami.utils.ranges import get_min_max
from origami.objects.container import ContainerBase
from origami.objects.annotations import Annotations


class DataObject(ContainerBase):
    """Generic data object"""

    # data attributes
    DOCUMENT_KEY = None

    def __init__(
        self,
        name,
        x,
        y,
        x_label="",
        y_label="",
        x_label_options=None,
        y_label_options=None,
        metadata=None,
        extra_data=None,
        **kwargs,
    ):
        """Base object for all other container objects

        Parameters
        ----------
        name : str
            name of the object so its easily searchable
        x : np.ndarray
            x-axis array
        y : np.ndarray
            y-axis array
        x_label : str
            x-axis label
        y_label : str
            y-axis label
        x_label_options : List[str]
            list of alternative x-axis labels
        y_label_options : List[str]
            list of alternative y-axis labels
        extra_data : dict
            dictionary containing additional data that should be exported in zarr container
        metadata : dict
            dictionary containing additional metadata that should be exported in zarr container
        """
        super().__init__(
            extra_data,
            metadata,
            x_label=x_label,
            y_label=y_label,
            x_label_options=x_label_options,
            y_label_options=y_label_options,
        )
        # settable attributes
        self.name = name
        self._x = x
        self._y = y
        self.check()

        self.check_kwargs(kwargs)

    def __repr__(self):
        return f"{self.__class__.__name__}<x-label={self.x_label}; y-label={self.y_label}; shape={self.shape}>"

    @property
    def x(self):
        """Return the `x` axis of the dataset"""
        return self._x

    @property
    def y(self):
        """Return the `y` axis of the dataset"""
        return self._y

    @property
    def x_limit(self):
        """Return the min/max values of the x-axis"""
        return get_min_max(self.x)

    @property
    def y_limit(self):
        """Return the min/max values of the y-axis"""
        return get_min_max(self.y)

    @property
    def shape(self):
        """Return the shape of the object"""
        return self.x.shape

    def check_kwargs(self, kwargs):
        """Checks whether kwargs have been fully processed"""
        if kwargs:
            for key, value in kwargs.items():
                if isinstance(value, np.ndarray):
                    self._extra_data[key] = value
                elif isinstance(value, (int, float, list, tuple, dict)):
                    self._metadata[key] = value

    def to_csv(self, *args, **kwargs):
        """Export data in a csv format"""
        raise NotImplementedError("Must implement method")

    def to_dict(self):
        """Export data in a dictionary object"""
        raise NotImplementedError("Must implement method")

    def to_zarr(self):
        """Outputs data to dictionary of `data` and `attributes`"""
        raise NotImplementedError("Must implement method")

    def check(self):
        """Check input"""
        raise NotImplementedError("Must implement method")

    def copy(self, new_name: str = None, suffix: str = "copy"):
        """Copy object and flush to disk"""
        store = self.get_parent()
        title = self.title
        if store is not None and title is not None:
            if new_name is None:
                new_name = get_duplicate_name(title, suffix=suffix)
            data, attrs = self.to_zarr()
            store.add(new_name, data, attrs)
            return new_name, store[new_name, True]

    def duplicate(self):
        """Duplicate data object without ever setting it in the DocumentStore"""
        from copy import deepcopy

        data_obj_copy = deepcopy(self)
        data_obj_copy.owner = None
        return data_obj_copy

    @property
    def can_flush(self):
        """Check whether data can be flushed to disk"""
        return self.owner is not None

    def flush(self, title: str = None):
        """Flush current object data to the DocumentStore"""
        store = self.get_parent()
        if title is None:
            title = self.title
        if store is not None and title is not None:
            data, attrs = self.to_zarr()
            store.add(title, data, attrs)
            self.unsaved = False

    def change_x_label(self, to_label: str, **kwargs):
        """Changes the label and x-axis values to a new format"""

    def change_y_label(self, to_label: str, **kwargs):
        """Changes the label and y-axis values to a new format"""

    def get_annotations(self):
        """Returns instance of the `Annotations` object"""
        annotations = self._metadata.get("annotations", dict())
        return Annotations(annotations)

    def set_annotations(self, annotations: Annotations):
        """Set instance of the `Annotations` object"""
        self._metadata["annotations"] = annotations.to_dict()
        self.flush()

    def get(self, key: str, default: Any = None):
        """Get arbitrary metadata from the object"""
        return self._metadata.get(key, default)

    def add_group(self, group_name: str, data: Dict, attrs: Dict):
        """Add Zarr group to base object"""
        document = self.get_parent()
        title = "/".join([self.title, group_name])
        document.add(title, data, attrs)

    def get_group(self, group_name: str) -> Group:
        """Get Zarr group from the base object"""
        document = self.get_parent()
        title = "/".join([self.title, group_name])
        return document.get(title)
