# Standard library imports
import os

# Local imports
from origami.utils.path import clean_filename


class ContainerBase:
    def __init__(self, extra_data, metadata, x_label="", y_label="", x_label_options=None, y_label_options=None):
        self._cls = self.__class__.__name__
        self._owner = None
        self._path = None
        self._output_path = None

        self._x_label = x_label
        self._y_label = y_label
        self._x_label_options = x_label_options
        self._y_label_options = y_label_options

        self._extra_data = dict() if extra_data is None else extra_data
        self._metadata = dict() if metadata is None else metadata
        self.options = dict()

    @property
    def owner(self):
        return self._owner

    @owner.setter
    def owner(self, value):
        """Sets the owner of the container object"""
        self._owner = value

    def set_owner(self, value):
        """Sets the owner of the container object"""
        self.owner = value

    def set_output_path(self, value):
        """Sets the owner of the container object"""
        self._output_path = value

    @property
    def path(self):
        return self._path

    def set_metadata(self, metadata):
        """Updates the metadata store"""
        if not isinstance(metadata, dict):
            raise ValueError("Cannot parse metadata that is not a dictionary")
        self._metadata.update(**metadata)

    @property
    def output_path(self):
        if self._output_path:
            return os.path.join(self._output_path, clean_filename(self.owner[1].split("/")[-1]))

    @property
    def x_label(self):
        return self._x_label

    @x_label.setter
    def x_label(self, value):
        """Sets the x-axis label"""
        self._x_label = value

    @property
    def y_label(self):
        return self._y_label

    @y_label.setter
    def y_label(self, value):
        """Sets the x-axis label"""
        self._y_label = value

    @property
    def x_label_options(self):
        if self._x_label_options is None:
            self._x_label_options = [self._x_label]
        return self._x_label_options
