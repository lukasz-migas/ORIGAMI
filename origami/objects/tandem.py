# Standard library imports
import os
from collections import MutableMapping

# TODO: decide on how best to store this data...
#       SQLite - probably best option but would require some work to get going
#           - write a wrapper around TandemMassSpectra that will act as dict so retrieval of mass spectra is easy
#       Pickle - unsafe and I wanted to move away from pickling objects


class TandemSpectra(MutableMapping):
    """Class providing access to tandem spectra"""

    def __init__(self, document, cache=True):
        self.document = document
        self.cache = cache
        self._cached_dict = None
        self._path = os.path.join(self.document.path, "tandem_spectra.pkl")

    def __setitem__(self, item, value) -> None:
        pass

    def __delitem__(self, item) -> None:
        pass

    def __contains__(self, x):
        return x in self.as_dict()

    def __getitem__(self, item):
        return self.as_dict()[item]

    def __iter__(self):
        return iter(self.as_dict())

    def __len__(self):
        return len(self.as_dict())

    def as_dict(self):
        if self.cache and self._cached_dict is not None:
            return self._cached_dict
        d = self._get()
        if self.cache:
            self._cached_dict = d
        return d

    def keys(self):
        return self.as_dict().keys()

    def set_from_dict(self, values):
        """Set the tandem data"""

    def _get(self):
        if os.path.exists(self._path):
            data = self.load()
        else:
            data = dict()
        return data

    @staticmethod
    def load():
        return dict()

    def write(self):
        pass
