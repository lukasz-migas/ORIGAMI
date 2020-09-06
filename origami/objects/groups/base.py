"""Group base"""
# Standard library imports
from typing import Any
from typing import Dict
from typing import List
from typing import Union

# Local imports
from origami.objects.container import ContainerBase
from origami.objects.containers import DataObject
from origami.objects.groups.utilities import DataObjectsContainer
from origami.objects.containers.utilities import XYAxesLabelAlternatives


class DataGroup(ContainerBase):
    """Group object for data operations"""

    _resample = True
    _x_min = None
    _x_max = None
    _x = None
    _y_sum = None
    _y_mean = None
    _processing = None

    def __init__(
        self,
        data_objects: Union[Dict[str, DataObject], Dict[str, str], List[DataObject], List[List[str]]],
        x_label="",
        y_label="",
        x_label_options=None,
        y_label_options=None,
        metadata=None,
        extra_data=None,
        **kwargs,
    ):
        super().__init__(
            extra_data,
            metadata,
            x_label=x_label,
            y_label=y_label,
            x_label_options=x_label_options,
            y_label_options=y_label_options,
        )
        self._data_objs = DataObjectsContainer(data_objects)
        self._next: int = -1
        self._is_dict = isinstance(data_objects, dict)

    def __repr__(self):
        return f"{self.__class__.__name__}<no. objects={self.n_objects}>"

    def __iter__(self):
        return self

    def __next__(self):
        self._next += 1

        if self._next < self.n_objects:
            return self[self._next]
        self._next = -1  # reset iterator
        raise StopIteration

    def __getitem__(self, item):
        """Get item"""
        if isinstance(item, int):
            item = item if not self._is_dict else self.names[item]
        else:
            if not self._is_dict:
                raise ValueError("Cannot retrieve item by name if data was provided as a dictionary")
        return self._data_objs[item]

    @property
    def names(self):
        """Returns the list of object names"""
        return self._data_objs.names

    @property
    def n_objects(self):
        """Return number of objects in the group container"""
        return self._data_objs.n_objects

    @property
    def need_resample(self):
        """Flag to indicate whether data needs to be resampled"""
        raise NotImplementedError("Must implement method")

    @property
    def processing(self):
        """Returns processing steps"""
        return self._processing

    @property
    def xs(self):
        """Return list of x-axes"""
        return [data_obj.x for data_obj in self]

    @property
    def ys(self):
        """Return list of y-axes"""
        return [data_obj.y for data_obj in self]

    @property
    def x_labels(self):
        """Return list of x-labels"""
        return [data_obj.x_label for data_obj in self]

    @property
    def y_labels(self):
        """Return list of y-labels"""
        return [data_obj.y_label for data_obj in self]

    @property
    def shapes(self):
        """Return list of shapes"""
        return [data_obj.shape for data_obj in self]

    def pprint(self, title: str) -> str:
        """Returns string representation of the data object"""
        data_obj_repr = self._data_objs.pprint()
        return f"{title}\n{data_obj_repr}"

    def add_processing_step(self, method: str, processing: Any):
        """Sets all processing processing associated with this fitter than can later be exported as a json file"""
        if self._processing is None:
            self._processing = dict()
        old_processing = self._processing.pop(method, None)
        self._processing[method] = processing

        # checks whether previous processing parameters are the same as what is being updated - if they are the same
        # no action needs to be taken, however, if they are different, all currently preset parameter MUST BE reset
        # otherwise you might get different results!
        if old_processing != processing:
            self.reset()

    def get_processing_step(self, method):
        """Retrieves processing steps previously carried out on the dataset"""
        if self._processing is None:
            self._processing = dict()
        return self._processing.get(method, dict())

    def get_group_metadata(self, keys: List[str], defaults=None, group_key=None) -> Dict:
        """Get group metadata"""
        if isinstance(keys, str):
            keys = [keys]
            defaults = [defaults]

        # pre-allocate output dictionary
        values = dict()
        for data_obj in self:
            if group_key:
                metadata = data_obj.get_metadata(group_key, dict())
                for i, key in enumerate(keys):
                    if key not in values:
                        values[key] = []
                    values[key].append(metadata.get(key, defaults[i]))
            else:
                for i, key in enumerate(keys):
                    if key not in values:
                        values[key] = []
                    values[key].append(data_obj.get_metadata(key, defaults[i]))
        return values

    def mean(self):
        """Mean array"""
        raise NotImplementedError("Must implement method")

    def sum(self):
        """Sum array"""
        raise NotImplementedError("Must implement method")

    def resample(self):
        """Resample"""
        raise NotImplementedError("Must implement method")

    def reset(self):
        """Reset"""
        raise NotImplementedError("Must implement method")

    def to_csv(self, *args, **kwargs):
        """Save data in CSV format"""
        raise ValueError("Cannot export data in CSV format")

    def to_dict(self):
        """Export data in dictionary format"""
        raise ValueError("Cannot export data in dict format")

    def to_zarr(self):
        """Outputs data to dictionary of `data` and `attributes`"""
        attrs = {"class": self._cls, **self._metadata}
        return dict(), attrs

    def export(self, name: str):
        """Export data in a Zarr format"""

    def change_x_label(self, to_label: str):
        """Change x-axis label and values"""
        if to_label in self.x_label_options:
            for data_obj in self:
                data_obj.change_x_label(to_label)
        return self

    def change_y_label(self, to_label: str):
        """Change x-axis label and values"""
        if to_label in self.y_label_options:
            for data_obj in self:
                data_obj.change_y_label(to_label)
        return self

    def validate_x_labels(self):
        """Validate that x-axis labels are the same or similar"""
        labels = set(self.x_labels)
        if len(labels) == 1:
            return True
        _labels = []
        for label in labels:
            _labels.append(XYAxesLabelAlternatives.get(label))
        if len(_labels) == 1:
            return True
        return False

    def validate_y_labels(self):
        """Validate that y-axis labels are the same or similar"""
        labels = set(self.y_labels)
        if len(labels) == 1:
            return True
        _labels = []
        for label in labels:
            _labels.append(XYAxesLabelAlternatives.get(label))
        if len(_labels) == 1:
            return True
        return False

    def validate_shape(self):
        """Validate that shape of the object is the same"""
        shapes = set(self.shapes)
        if len(shapes) == 1:
            return True
        return False

    def validate_size(self, n_min: int = 1, n_max: int = 1):
        """Validate that the number of items is correct"""
        return n_min <= self.n_objects <= n_max
