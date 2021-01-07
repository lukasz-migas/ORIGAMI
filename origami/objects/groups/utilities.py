"""Group utilities"""
# Standard library imports
from typing import Dict
from typing import List
from typing import Union

# Local imports
from origami.objects.containers import DataObject


class DataObjectsContainer:
    """Container class for DataObjects"""

    def __init__(self, data_objects: Union[Dict[str, DataObject], Dict[str, str], List[DataObject], List[List[str]]]):
        self._data_objs = data_objects
        self._names = None
        self._is_dict = isinstance(data_objects, dict)
        self._is_loaded = self.is_loaded()
        self.check()

    def __getitem__(self, item):
        """Retrieve object from the internal store"""
        # Local imports
        from origami.config.environment import ENV

        if isinstance(item, int):
            item = item if not self._is_dict else self.names[item]
        else:
            if not self._is_dict:
                raise ValueError("Cannot retrieve item by name if data was provided as a dictionary")
        value = self._data_objs[item]

        if isinstance(value, list):
            document = ENV.on_get_document(value[0])
            value = document[value[1], True]
        return value

    def pprint(self):
        """Return the list of objects in a pretty format"""
        item_list = []
        if self._is_dict:
            for item in self._data_objs.values():
                print("ITEM dict", item)
                document_title, dataset_name = item
                item_list.append(f"    {document_title} | {dataset_name}")
        else:
            for item in self._data_objs:
                print("ITEM list", item)
                document_title, dataset_name = item
                item_list.append(f"    {document_title} | {dataset_name}")
        return "\n".join(item_list)

    def is_loaded(self):
        """Checks whether items in the `data_objs` attribute are DataObjects or strings"""
        if self._is_dict:
            for value in self._data_objs.values():
                if isinstance(value, str):
                    return False
        else:
            for value in self._data_objs:
                if isinstance(value, str):
                    return False
        return True

    @property
    def names(self):
        """Returns the list of object names"""
        if self._names is None:
            self._names = range(self.n_objects) if not self._is_dict else list(self._data_objs.keys())
        return self._names

    @property
    def n_objects(self):
        """Return number of objects in the group container"""
        return len(self._data_objs)

    def check(self):
        """Ensure correct data was added to the data group"""
        if not isinstance(self._data_objs, (list, dict)):
            raise ValueError("Group data should be provided in a list or dict object")
        for data_obj in self:
            if not isinstance(data_obj, (DataObject, list)):
                raise ValueError("Objects must be of the instance `DataObject`")
