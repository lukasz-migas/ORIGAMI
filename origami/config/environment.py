"""Container object that stores the current state of the application"""
# Standard library imports
import os
import logging

# Local imports
from origami.document import document as Document
from origami.utils.time import get_current_time
from origami.config.config import CONFIG
from origami.config.convert import convert_v1_to_v2
from origami.config.convert import upgrade_document_annotations
from origami.readers.io_document import open_py_object

LOGGER = logging.getLogger(__name__)

DOCUMENT_TYPE_ATTRIBUTES = dict(
    overlay=dict(data_type="Type: Comparison", file_format="Format: ORIGAMI"),
    interactive=dict(data_type="Type: Interactive", file_format="Format: ORIGAMI"),
    manual=dict(data_type="Type: MANUAL", file_format="Format: MassLynx (.raw)"),
    thermo=dict(data_type="Type: MS", file_format="Format: Thermo (.RAW)"),
    mgf=dict(data_type="Type: MS/MS", file_format="Format: .mgf"),
    mzml=dict(data_type="Type: MS/MS", file_format="Format: .mzML"),
    imaging=dict(data_type="Type: Imaging", file_format="Format: MassLynx (.raw)"),
    origami=dict(data_type="Type: ORIGAMI", file_format="Format: MassLynx (.raw)"),
    waters=dict(data_type="Type: MassLynx", file_format="Format: MassLynx (.raw)"),
)
ALTERNATIVE_NAMES = {
    "compare": "overlay",
    "Type: Comparison": "overlay",
    "Type: Interactive": "interactive",
    "Type: MANUAL": "manual",
    "Type: MS/MS": "mgf",
    "mzML": "mzml",
    "Imaging": "imaging",
    "Type: Imaging": "imaging",
}


# TODO: add `callbacks` section to the  document


def get_document_title(path):
    base_title = "New Document"
    if path in ["", None]:
        return base_title
    elif os.path.exists(path):
        return os.path.basename(path)
    return base_title


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
        #         if not isinstance(value, Document):
        #             raise ValueError(f"Item must be of `Document` type not {type(value)}")
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
        if self.n_documents == 1:
            self._current = self.titles[0]
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

    def on_get_document(self, title=None):
        """Returns current document"""
        if title is None:
            title = self.current

        return self.documents[title]

    def save(self, path: str):
        """Save document to pickle file"""
        pass

    def load(self, path: str):
        """Load document from pickle file"""
        document_obj, document_version = open_py_object(path)
        # check version
        if document_version < 2:
            document_obj = convert_v1_to_v2(document_obj)

        # upgrade annotations
        upgrade_document_annotations(document_obj)

        self.add(document_obj)

    @staticmethod
    def blank() -> Document:
        """Creates new document instance without any attributes being pre-set"""
        return Document()

    @staticmethod
    def new(document_type: str, path: str) -> Document:
        """Create new document that contains certain attributes"""
        # ensure the correct name is used
        if document_type not in DOCUMENT_TYPE_ATTRIBUTES:
            document_type = ALTERNATIVE_NAMES[document_type]

        # get document attributes
        attributes = DOCUMENT_TYPE_ATTRIBUTES[document_type]

        # instantiate document
        document = Document()
        document.title = get_document_title(path)
        document.path = path
        document.userParameters = CONFIG.userParameters
        document.userParameters["date"] = get_current_time()
        document.dataType = attributes["data_type"]
        document.fileFormat = attributes["file_format"]

        return document

    def get_new_document(self, document_type: str, path: str) -> Document:
        """Alias for `new`"""
        return self.new(document_type, path)


ENV = Environment()
