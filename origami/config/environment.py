"""Container object that stores the current state of the application"""
# Standard library imports
import os
import logging
from typing import Dict
from typing import List
from typing import Union
from typing import Optional

# Local imports
from origami.utils.time import get_current_time
from origami.config.config import CONFIG
from origami.config.convert import convert_pickle_to_zarr
from origami.objects.document import DocumentStore
from origami.objects.callbacks import PropertyCallbackManager
from origami.objects.containers import DataObject

# ID_showPlotMSDocument

LOGGER = logging.getLogger(__name__)

DOCUMENT_TYPE_ATTRIBUTES = dict(
    overlay=dict(data_type="Type: Comparison", file_format="Format: ORIGAMI"),
    interactive=dict(data_type="Type: Interactive", file_format="Format: ORIGAMI"),
    manual=dict(data_type="Type: MANUAL", file_format="Format: MassLynx (.raw)"),
    thermo=dict(data_type="Type: MS", file_format="Format: Thermo (.RAW)"),
    text=dict(data_type="Type: ORIGAMI", file_format="Format: Text (.csv; .txt; .tab)"),
    mgf=dict(data_type="Type: MS/MS", file_format="Format: .mgf"),
    mzml=dict(data_type="Type: MS/MS", file_format="Format: .mzML"),
    imaging=dict(data_type="Type: Imaging", file_format="Format: MassLynx (.raw)"),
    origami=dict(data_type="Type: ORIGAMI", file_format="Format: MassLynx (.raw)"),
    activation=dict(data_type="Type: Activation", file_format="Format: MassLynx (.raw)"),
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
    "Type: Activation": "activation",
    "Type: ORIGAMI": "origami",
}
DOCUMENT_TYPES = [
    "Type: ORIGAMI",
    "Type: Activation",
    "Type: MANUAL",  # remove
    # "Type: Infrared",  # remove
    # "Type: 2D IM-MS",  # remove
    # "Type: Interactive",  # remove
    "Type: Comparison",
    "Type: MS",  # remove
    "Type: Imaging",
    "Type: MS/MS",
]
DOCUMENT_DEFAULT = "origami"
DOCUMENT_KEY_PAIRS = {
    "mz": "MassSpectra/Summed Spectrum",
    "mass_spectrum": "MassSpectra/Summed Spectrum",
    "rt": "Chromatograms/Summed Chromatogram",
    "chromatogram": "Chromatograms/Summed Chromatogram",
    "dt": "Mobilograms/Summed Mobilogram",
    "mobilogram": "Mobilograms/Summed Mobilogram",
    "heatmap": "IonHeatmaps/Summed Heatmap",
    "msdt": "MSDTHeatmaps/Summed Heatmap",
    "mass_spectra": ("MassSpectra", "*"),
    "chromatograms": ("Chromatograms", "*"),
    "mobilograms": ("Mobilograms", "*"),
    "parameters": "Metadata/Parameters",
    # "reader": "file_reader",
    # "tandem_spectra": "tandem_spectra",
}

# TODO: add `callbacks` section to the  document


def get_document_title(path):
    base_title = "New Document"
    if path in ["", None]:
        return base_title
    elif os.path.exists(path):
        return os.path.basename(path)
    return base_title


class Environment(PropertyCallbackManager):
    ALLOWED_EVENTS = ["add", "change", "rename", "delete"]

    def __init__(self):
        super(Environment, self).__init__()
        self._current = None
        self.documents = dict()
        LOGGER.debug("Instantiated Document Store Environment")

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
        #         if key.endswith(".origami"):
        #             key, _ = key[::-8]
        self.documents[key] = value
        self.current = value.title
        self._trigger("add", value.title)

    def __delitem__(self, key):
        """Delete document object"""
        self.documents.pop(key)
        self.current = None
        self._trigger("delete", key)
        LOGGER.debug(f"Deleted `{key}`")

    def __contains__(self, item):
        """Check if document is already present"""
        if item in self.documents:
            return True
        return False

    def _trigger(self, event: str, metadata):
        """Trigger callback on the object"""
        super(Environment, self).trigger(event, metadata)

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
        """Return all document titles"""
        return list(self.keys())

    def exists(self, title: Optional[str] = None, path: Optional[str] = None):
        """Checks whether document with the name already exists"""
        if path is not None:
            title = get_document_title(path)
        if title is None and path is None:
            raise ValueError("Expected either `title` or `path` keyword parameter")
        return title in self

    def add(self, document: DocumentStore):
        """Add document to the store"""
        self.documents[document.title] = document
        self._trigger("add", document.title)

    def remove(self, key):
        """Remove document from the store"""
        document = self.documents.pop(key)
        self._trigger("delete", document.title)
        return document

    def rename(self, old_name, new_name):
        """Rename document"""
        document = self.documents.pop(old_name)
        document.title = new_name
        self.documents[new_name] = document
        self._trigger("rename", [old_name, new_name])

    def get(self, key, alt=None):
        """Get document"""
        return self.documents.get(key, alt)

    def pop(self, key, alt=None):
        """Pop document"""
        document = self.documents.pop(key, alt)
        if document is not None:
            self._trigger("delete", document.title)
        return document

    def clear(self):
        """Clear document store"""
        titles = self.titles
        self.documents.clear()
        for title in titles:
            self._trigger("delete", title)

    def keys(self):
        """Returns document list"""
        return list(self.documents.keys())

    def values(self):
        """Return documents"""
        return self.documents.values()

    def items(self):
        """Returns list of tuples of (key, document)"""
        return self.documents.items()

    def on_get_document(self, title=None):
        """Returns current document"""
        if title is None:
            title = self.current
        return self.documents[title]

    def save(self, path: str):
        """Save document - this function should not exist since zarr data is saved as it is added to the document"""
        pass

    def load(self, path: str):
        """Load document from pickle file"""
        # check whether path ends with pickle (e.g. old format) and if so, handle the transition to the new format
        if path.endswith(".pickle"):
            path = convert_pickle_to_zarr(path)
        elif not path.endswith(".origami"):
            raise ValueError(f"Not sure how to handle document store `{path}`")

        document_obj = DocumentStore(path)

        self.add(document_obj)
        return document_obj

    def open(self, path: str):
        """Alias for load"""
        return self.load(path)

    def duplicate(self, title: str, path: str):
        """Duplicate document in-place"""
        document = self[title]
        document_copy = document.duplicate(path)

        # load duplicated document
        if document_copy is not None and isinstance(document_copy, DocumentStore):
            self.add(document_copy)

    def set_document(
        self,
        document: Optional[DocumentStore] = None,
        path: Optional[str] = None,
        document_type: Optional[str] = None,
        data: Optional[Dict] = None,
    ):
        """Set document in the environment"""
        # create new document if one was not provided
        if document is None:
            if path is None:
                path = os.path.join(CONFIG.cwd, self._get_new_name())
            if document_type is None:
                document_type = DOCUMENT_DEFAULT
            document = self.new(document_type, path)

        # add data to the document
        changed = []
        title = document.title
        if isinstance(data, dict):
            for obj_name, obj_data in data.items():
                attr_name = DOCUMENT_KEY_PAIRS.get(obj_name)
                # could not figure out what to do with the data
                if attr_name is None:
                    LOGGER.error(f"Could not processes {obj_name} - not registered yet")
                    continue

                # data is simply object that can be directly mapped to container
                if isinstance(obj_data, DataObject) and hasattr(obj_data, "to_zarr"):
                    _data, _attrs = obj_data.to_zarr()
                    document.add(attr_name, _data, _attrs)
                    changed.append((title, attr_name))
                # data is dictionary object that needs to be iterated over
                elif isinstance(attr_name, tuple) and isinstance(obj_data, dict):
                    attr_name, _ = attr_name
                    for _obj_name, _obj_data in obj_data.items():
                        _data, _attrs = _obj_data.to_zarr()
                        dataset_name = f"{attr_name}/{_obj_name}"
                        document.add(dataset_name, _data, _attrs)
                        changed.append((title, dataset_name))
                # data is dictionary that should be treated as attributes
                elif isinstance(obj_data, dict):
                    _attrs = obj_data
                    document.add(attr_name, attrs=_attrs)
                else:
                    LOGGER.error(f"Could not process {obj_name} - lacks converter ({type(obj_data)}")

        if changed:
            self._trigger("change", changed)

        # set document in-place
        self[document.title] = document
        return document

    def _get_new_name(self, title: str = "New Document", n_fill: int = 1):
        """Returns unique, document name"""
        n = 0
        while title + " #" + "%d".zfill(n_fill) % n in self:
            n += 1
        return title + " #" + "%d".zfill(n_fill) % n

    def new(
        self,
        document_type: str,
        path: str,
        data: Optional[Dict] = None,
        check_unique: bool = False,
        title: Optional[str] = None,
    ) -> DocumentStore:
        """Create new document that contains certain pre-set attributes. The document is not automatically added to the
        store. Use `add_new` if you would like to instantiate and add the document to the document store"""
        # ensure the correct name is used
        if document_type not in DOCUMENT_TYPE_ATTRIBUTES:
            document_type = ALTERNATIVE_NAMES[document_type]

        # get document attributes
        attributes = DOCUMENT_TYPE_ATTRIBUTES[document_type]

        if not title:
            title = get_document_title(path)

        if check_unique:
            title = self._get_new_name(title)

        # instantiate document
        document = DocumentStore(path, title)
        document.add_attrs(
            attrs={
                "path": path,
                "data_type": attributes["data_type"],
                "file_format": attributes["file_format"],
                "date": get_current_time(),
            }
        )
        document.add_config("user-parameters", CONFIG.userParameters)

        # add data to document
        if data is not None:
            document = self.set_document(document, data=data)

        return document

    def get_new_document(
        self, document_type: str, path: str, data: Optional[Dict] = None, title: Optional[str] = None
    ) -> DocumentStore:
        """Alias for `new`"""
        return self.new(document_type, path, data, title=title)

    def add_new(
        self, document_type: str, path: str, data: Optional[Dict] = None, title: Optional[str] = None
    ) -> DocumentStore:
        """Creates new document and adds it to the store"""
        document = self.new(document_type, path, data, title=title)
        self.add(document)
        LOGGER.debug(f"Created new document: {document.path}")
        return document

    def get_document_list(
        self,
        document_types: Union[str, List[str]] = "all",
        document_format: Optional[str] = None,
        check_path: bool = False,
    ):
        """Get list of currently opened documents based on some requirements

        Parameters
        ----------
        document_types : Union[str, List[str]]
            types of document to be searched for in the store
        document_format : Optional[str]
            types of format to be searched for in the store
        check_path : bool
            if `True`, a simple OS check will be performed to ensure only existing document is selected

        Returns
        -------
        document_list : List
            list of document titles
        """
        if document_types == "all" or document_types is None:
            document_types = DOCUMENT_TYPES
        if isinstance(document_types, str):
            document_types = [document_types]

        document_list = []
        for document_title, document in self.items():
            if check_path and not os.path.exists(document.path):
                continue
            if document.data_type in document_types:
                if document_format is None or document_format == document.file_format:
                    document_list.append(document_title)
        return document_list


ENV = Environment()
