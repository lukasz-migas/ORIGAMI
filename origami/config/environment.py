"""Container object that stores the current state of the application"""
# Standard library imports
import logging

# Local imports
from origami.document import document as Document

LOGGER = logging.getLogger(__name__)


class Environment:
    def __init__(self):
        self.title = None
        self.documents = dict()

    def __repr__(self):
        return f"DocumentStore<{self.n_documents} documents>"

    def __len__(self):
        return len(self.documents)

    def __getitem__(self, item):
        """Get document object"""
        if item not in self.documents:
            raise ValueError(f"Document `{item}` does not exist")
        self.title = item
        LOGGER.debug(f"Retrieved `{item}`")
        return self.documents[item]

    def __setitem__(self, key, value):
        """Set document object"""
        self.documents[key] = value

    def __delitem__(self, key):
        """Delete document object"""
        self.documents.pop(key)
        LOGGER.debug(f"Deleted `{key}`")

    def __contains__(self, item):
        """Check if document is already present"""
        if item in self.documents:
            return True
        return False

    @property
    def n_documents(self):
        return len(self.documents)

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


ENV = Environment()
