"""Container object base class"""
# Standard library imports
import os

# Local imports
from origami.utils.path import clean_filename


class ContainerBase:
    """Container object base class"""

    def __init__(self, extra_data, metadata, x_label="", y_label="", x_label_options=None, y_label_options=None):
        self._cls = self.__class__.__name__
        self._owner = None
        self._path = None
        self._output_path = None
        self._unsaved = False

        self._x_label = x_label
        self._y_label = y_label
        self._x_label_options = x_label_options
        self._y_label_options = y_label_options

        self._extra_data = dict() if extra_data is None else extra_data
        self._metadata = dict() if metadata is None else metadata
        self.options = dict()

    @property
    def owner(self):
        """Returns the owner of the container object"""
        return self._owner

    @owner.setter
    def owner(self, value):
        """Sets the owner of the container object"""
        self._owner = value

    def set_owner(self, value):
        """Sets the owner of the container object"""
        if not isinstance(value, (list, tuple)):
            raise ValueError("`set_owner` expects a tuple or list of (DOCUMENT_TITLE, DATASET_NAME)")
        self.owner = value

    def set_output_path(self, value):
        """Sets the owner of the container object"""
        self._output_path = value

    @property
    def title(self):
        """Return the title of the object"""
        if self.owner is not None:
            _, item_name = self.owner
            return item_name

    @title.setter
    def title(self, value: str):
        """Set title of the object"""
        if self.owner is not None:
            document_title, _ = self.owner
            self.owner = (document_title, value)

    @property
    def dataset_name(self):
        """Return the base title of the object"""
        title = self.title
        if title is None or "/" not in title:
            return ""
        _, dataset_name = title.split("/")
        return dataset_name

    @property
    def unsaved(self):
        """Returns the flag to indicate that this object has some unsaved changes"""
        return self._unsaved

    @unsaved.setter
    def unsaved(self, value: bool):
        """Sets unsaved instance"""
        if not isinstance(value, bool):
            raise ValueError("Trying to set `unsaved` attribute with incorrect value type")
        self._unsaved = value

    @property
    def path(self):
        """Returns the path to the container object data and metadata"""
        return self._path

    def set_metadata(self, metadata):
        """Updates the metadata store"""
        if not isinstance(metadata, dict):
            raise ValueError("Cannot parse metadata that is not a dictionary")
        self._metadata.update(**metadata)

    def get_metadata(self, key, default):
        """Return metadata"""
        return self._metadata.get(key, default)

    def add_metadata(self, key, value):
        """Add metadata key:value pair"""
        if not isinstance(key, str):
            raise ValueError("Metadata `key` must be a string")
        if not isinstance(value, (bool, str, int, float, list, tuple)):
            raise ValueError("Metadata `value` must be JSON serializable")
        self._metadata[key] = value

    @property
    def output_path(self):
        """Returns the output path in relation to the DocumentStore"""
        if self._output_path:
            return os.path.join(self._output_path, clean_filename(self.owner[1].split("/")[-1]))

    @property
    def x_label(self):
        """Returns the x-axis label"""
        return self._x_label

    @x_label.setter
    def x_label(self, value):
        """Sets the x-axis label"""
        self._x_label = value

    @property
    def x_label_options(self):
        """Returns the x-axis label options"""
        if self._x_label_options is None:
            self._x_label_options = [self._x_label]
        return self._x_label_options

    @property
    def y_label(self):
        """Returns the y-axis label"""
        return self._y_label

    @y_label.setter
    def y_label(self, value):
        """Sets the x-axis label"""
        self._y_label = value

    @property
    def y_label_options(self):
        """Returns the y-axis label options"""
        if self._y_label_options is None:
            self._y_label_options = [self._y_label]
        return self._y_label_options

    def get_parent(self):
        """Returns the DocumentStore object that is associated with the container"""
        # environment must be imported here since it might cause circular reference if imported at the top
        from origami.config.environment import ENV

        if self.owner is not None:
            parent, _ = self.owner
            return ENV.on_get_document(parent)
