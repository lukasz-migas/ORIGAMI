"""Container object that stores the current state of the application"""
# Standard library imports
import logging

# Local imports
from origami.document import document as Document

LOGGER = logging.getLogger(__name__)


class Environment:
    def __init__(self):
        self._current = None
        self.documents = dict()

    def __repr__(self):
        return f"DocumentStore<{self.n_documents} documents>"

    def __len__(self):
        return len(self.documents)

    def __getitem__(self, item):
        """Get document object"""
        if item not in self.documents:
            raise ValueError(f"Document `{item}` does not exist")
        self.current = item
        LOGGER.debug(f"Retrieved `{item}`")
        return self.documents[item]

    def __setitem__(self, key, value):
        """Set document object"""
        if not isinstance(value, Document):
            raise ValueError("Item must be of `Document` type")
        self.documents[key] = value
        self.current = value.title

    def __delitem__(self, key):
        """Delete document object"""
        self.documents.pop(key)
        self.current = None
        LOGGER.debug(f"Deleted `{key}`")

    def __contains__(self, item):
        """Check if document is already present"""
        if item in self.documents:
            return True
        return False

    @property
    def n_documents(self):
        """Return the number of documents"""
        return len(self.documents)

    @property
    def current(self):
        return self._current

    @current.setter
    def current(self, value):
        if value not in self.documents and value is not None:
            raise ValueError(
                f"Cannot set `{value}` as current document as its not present in the document store. Use"
                f" {self.titles}"
            )
        self._current = value
        LOGGER.debug(f"Updated current document -> `{value}`")

    @property
    def titles(self):
        return list(self.keys())

    def add(self, document: Document):
        """Add document to the store"""
        self.documents[document.title] = document

    def remove(self, key):
        """Remove document from the store"""
        self.documents.pop(key)

    def rename(self, old_name, new_name):
        """Rename document"""
        document = self.documents.pop(old_name)
        document.title = new_name
        self.add(document)

    def get(self, key, alt=None):
        """Get document"""
        return self.documents.get(key, alt)

    def pop(self, key, alt=None):
        """Pop document"""
        return self.documents.pop(key, alt)

    def clear(self):
        """Clear document store"""
        self.documents.clear()

    def keys(self):
        return self.documents.keys()

    def values(self):
        return self.documents.values()

    def items(self):
        return self.documents.items()

    def on_get_document(self):
        """Returns current document"""
        return self.documents[self.current]

    def save(self, path: str):
        """Save document to pickle file"""
        pass

    def load(self, path: str):
        """Load document from pickle file"""
        pass


ENV = Environment()
