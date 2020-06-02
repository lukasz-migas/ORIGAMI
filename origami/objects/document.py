"""Wrapper around Zarr's file object with functions amenable to ORIGAMI's dataset"""
# Standard library imports
import os
import shutil
import logging
from typing import Dict
from typing import List
from typing import Optional
from pathlib import Path

# Third-party imports
import zarr
import numpy as np
from zarr import Group
from natsort import natsorted
from zarr.util import is_valid_python_name

# Local imports
from origami import __version__
from origami.utils.path import clean_filename
from origami.objects.tandem import TandemSpectra
from origami.readers.io_json import read_json_data
from origami.readers.io_json import write_json_data
from origami.utils.utilities import get_chunk_size
from origami.utils.converters import byte2str
from origami.objects.containers import DataObject
from origami.objects.containers import mobilogram_object
from origami.objects.containers import ion_heatmap_object
from origami.objects.containers import chromatogram_object
from origami.objects.containers import msdt_heatmap_object
from origami.objects.containers import mass_spectrum_object

LOGGER = logging.getLogger(__name__)

# TODO: add annotations attribute to group


class DocumentStore:
    VERSION: int = 1
    EXTENSION: str = ".origami"
    GROUPS = [
        "MassSpectra",
        "Mobilograms",
        "Chromatograms",
        "IonHeatmaps",
        "MSDTHeatmaps",
        "Metadata",
        "Overlays",
        "Configs",  # json/xml
        "Raw",  # any raw file
        "Output",  # any file
        "Tandem",  # pickled dictionary...
    ]

    # attributes that can be set
    _title = None

    def __init__(self, path: str, title: Optional[str] = None):
        self.path = self._has_extension(path, self.EXTENSION)
        self.title = title

        self.fp: Group = zarr.open(str(self.path))
        self.fp.require_groups(*self.GROUPS)

        # temporary stores
        self.file_reader = dict()
        self.app_data = dict()
        self.metadata = dict()
        self._tandem_spectra = TandemSpectra(self.fp)
        self.output_path = os.path.join(self.path, "Output")

        self._check_version()

    def __repr__(self):
        return f"{self.__class__.__name__}<{str(self.path)}>"

    def __getitem__(self, item):
        """Get item from the store"""
        as_object = False
        if isinstance(item, tuple):
            item, as_object = item
        if not isinstance(item, str):
            raise ValueError(f"Expected str and got {type(item)} ({item})")

        if as_object:
            return self.as_object(self.fp[item])
        return self.fp[item]

    def __contains__(self, item):
        """Check whether object is present in the store"""
        return item in self.fp

    def __delitem__(self, key):
        """Delete item from the document"""
        item: Group = self[key]
        # remove all objects from group
        if hasattr(item, "clear"):
            item.clear()
        else:
            # remove dataset
            del self.fp[key]

    def __getattr__(self, item):
        # allow access to group members via dot notation
        try:
            return self.__getitem__(item)
        except KeyError:
            raise AttributeError

    def __dir__(self):
        # noinspection PyUnresolvedReferences
        base = list(super().__dir__())
        keys = sorted(set(base + list(self.fp)))
        keys = [k for k in keys if is_valid_python_name(k)]
        return keys

    def __len__(self):
        return len(self.fp)

    #     def __iter__(self):
    #         for key in self.fp:
    #             yield key

    def __enter__(self):
        """Return the Group for use as a context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """If the underlying Store has a ``close`` method, call it."""
        try:
            self.fp.store.close()
        except AttributeError:
            pass

    def as_object(self, group: Group):
        """Returns the group data as an object"""
        klass_name = group.attrs.get("class", None)
        obj = None

        if klass_name == "MassSpectrumObject":
            obj = mass_spectrum_object(group)
        elif klass_name == "ChromatogramObject":
            obj = chromatogram_object(group)
        elif klass_name == "MobilogramObject":
            obj = mobilogram_object(group)
        elif klass_name == "MassSpectrumHeatmapObject":
            obj = msdt_heatmap_object(group)
        elif klass_name == "IonHeatmapObject":
            obj = ion_heatmap_object(group)
        elif klass_name == "StitchIonHeatmapObject":
            obj = ion_heatmap_object(group)
        # elif klass_name == "MassSpectrumGroup":
        #     obj =

        # return instantiated objected
        if obj:
            # associate object with metadata
            obj.set_owner((self.title, group.path))
            obj.set_output_path(self.output_path)

            return obj

        raise ValueError(f"Not sure how to handle {klass_name}")

    def _check_version(self):
        """Load document version from disk

        1. If the current version of document does not exist, version will be written to the document automatically
        2. If the version on disk is not the latest version, it will be automatically updated
        """
        version = self.fp.attrs.get("format_version", None)
        self.fp.attrs["origami_version"] = __version__
        if version is None:
            self.fp.attrs["format_version"] = version = self.VERSION

        if version != self.VERSION:
            LOGGER.warning(f"The current version of the document is out of date - update will happen automatically.")

    def _ipython_key_completions_(self):
        return sorted(self)

    @staticmethod
    def _has_extension(path, extension):
        """Cleans-up path"""
        path = Path(path)
        return str(path.with_suffix(extension))

    @property
    def groups(self):
        return [group for group in self.fp.group_keys()]

    @property
    def info(self):
        return self.fp.info

    @property
    def title(self):
        if self._title is None:
            self._title = os.path.splitext(os.path.split(self.path)[1])[0]
        return self._title

    @title.setter
    def title(self, value):
        self._title = byte2str(value)

    @property
    def data_type(self):
        """Returns the type of dataset"""
        return self.fp.attrs["data_type"]

    @property
    def file_format(self):
        return self.fp.attrs["file_format"]

    @property
    def parameters(self):
        """Returns parameters object"""
        if "Metadata/Parameters" in self:
            return self["Metadata/Parameters"]
        return {}

    def group(self, key):
        """Retrieve group from the dataset"""
        if key not in self.groups:
            raise ValueError(f"Group '{key}' is not present in the document. Try: {self.groups}")
        return self.fp[key]

    def full_path(self, item: str) -> Path:
        """Return full path to an object"""
        if not isinstance(item, str):
            raise ValueError("Expected str object")
        return self.path / Path(item)

    def _get(self, key):
        """Get group, and if necessary - create a new one"""
        # break the key into pieces
        if key is None:
            return self.fp

        parts = Path(key).parts

        if len(parts) == 1:
            group = self.fp.create_group(parts[0])
        elif len(parts) == 2:
            group = self.get(key)
            if group is None:
                group = self[parts[0]].create_group(parts[1])
        else:
            raise ValueError("Not sure what to do")
        return group

    def add_attrs(self, key=None, attrs=None):
        """Add attributes to group"""
        group = self._get(key)

        # add attributes
        for attr, value in attrs.items():
            group.attrs[attr] = value

        return group

    def get_attrs(self, key=None, attrs: List[str] = None):
        """Return dictionary of attributes"""
        group = self._get(key)
        if len(attrs):
            return group.attrs.get(attrs[0], None)

        _attrs = {}
        for attr in attrs:
            _attrs[attr] = group.attrs.get(attr, None)
        return _attrs

    def add_spectrum(self, title: str, data: Optional[Dict] = None, attrs: Optional[Dict] = None):
        """Adds mass spectrum to the document"""
        if isinstance(data, DataObject):
            data, attrs = data.to_zarr()
        group = self.add(f"MassSpectra/{title}", data, attrs)
        return self.as_object(group)

    def add_chromatogram(self, title: str, data: Optional[Dict] = None, attrs: Optional[Dict] = None):
        """Adds chromatogram to the document"""
        if isinstance(data, DataObject):
            data, attrs = data.to_zarr()
        group = self.add(f"Chromatograms/{title}", data, attrs)
        return self.as_object(group)

    def add_mobilogram(self, title: str, data: Optional[Dict] = None, attrs: Optional[Dict] = None):
        """Adds mobilograms to the document"""
        if isinstance(data, DataObject):
            data, attrs = data.to_zarr()
        group = self.add(f"Mobilograms/{title}", data, attrs)
        return self.as_object(group)

    def add_heatmap(self, title: str, data: Optional[Dict] = None, attrs: Optional[Dict] = None):
        """Adds heatmap to the document"""
        if isinstance(data, DataObject):
            data, attrs = data.to_zarr()
        group = self.add(f"IonHeatmaps/{title}", data, attrs)
        return self.as_object(group)

    def add_metadata(self, title: str, data: Optional[Dict] = None, attrs: Optional[Dict] = None):
        """Adds metadata to the document"""
        if isinstance(data, DataObject):
            data, attrs = data.to_zarr()
        group = self.add(f"Metadata/{title}", data, attrs)
        return group

    def add(self, key, data=None, attrs=None):
        """Add data to group"""
        # TODO: add name check so that names are always valid keys
        if data is None:
            data = dict()
        if attrs is None:
            attrs = dict()

        # get group and add data to it
        group = self._get(key)
        group = self._set_group_data(group, data, attrs)
        return group

    def get(self, item, default=None):
        """Returns the group if one is present"""
        return self.fp.get(item, default)

    def clear(self, item):
        """Clears all data from the store without removing the directory"""
        try:
            self[item].clear()
        except (KeyError, AttributeError):
            LOGGER.warning(f"Could not clear `{item}`")

    def duplicate(self, path):
        """Create copy of the document with new name"""
        raise NotImplementedError("Must implement method")

    def remove(self, item):
        """Deletes all data and the root directory from the store"""
        try:
            del self.fp[item]
        except KeyError:
            LOGGER.warning(f"Could not delete `{item}`")

    def copy(self, item: str, copy: Optional[str] = None):
        """Copy object and set it inside the document"""
        group = self._get(item)
        if copy is None:
            copy = self._get_unique_name(item, 2)

        self.add(copy, {k: v[:] for k, v in group.items()}, attrs=group.attrs.asdict())

    def _get_unique_name(self, title: str, n_fill: int = 1):
        """Returns unique name"""
        n = 0
        while title + " #" + "%d".zfill(n_fill) % n in self:
            n += 1
        return title + " #" + "%d".zfill(n_fill) % n

    @staticmethod
    def _set_group_data(group: Group, data: Dict, attrs: Dict, chunks: bool = True):
        """Add all components of a group or subgroup"""
        # add datasets
        for key, value in data.items():
            assert isinstance(value, np.ndarray)

            # rather than using the default chunk size, we override the rather small values preset by the Zarr
            # developers
            chunk_size = get_chunk_size(chunks, value.shape, value.dtype)

            # first try to create the dataset with all necessary metadata
            if key not in group:
                group.create_dataset(key, data=value, chunks=chunk_size)
            else:
                # overwrite while keeping the chunk size the same
                group.array(key, value, overwrite=True, chunks=chunk_size)

        # add attributes
        for key, value in attrs.items():
            group.attrs[key] = value
        return group

    def _get_config_path(self, name):
        """Returns nicely formatted config file path"""
        path = self.full_path("Configs")
        path = self._has_extension(os.path.join(str(path), clean_filename(name)), ".json")
        return path

    def add_config(self, name: str, data: Dict):
        """Write or update configuration file in the `Config` directory"""
        assert isinstance(data, dict), "Configuration file should be a dict object"
        path = self._get_config_path(name)

        write_json_data(path, data, check_existing=True)
        LOGGER.debug(f"Wrote configuration file to {path}")

    def get_config(self, name: str, default: bool = None):
        """Retrieves configuration file

        Parameters
        ----------
        name : str
            name of the configuration file
        default : bool, optional
            what should be the default value if the configuration file with `name` does not exist

        Returns
        -------
        value : dict
            dictionary with config values
        """
        path = self._get_config_path(name)
        if os.path.exists(path):
            return read_json_data(path)
        return default

    def add_raw(self, filepath):
        """Copies raw file to the ORIGAMI directory

        Parameters
        ----------
        filepath : str
            path of the file to be added to the `Raw` directory
        """
        filepath = Path(filepath)
        if not filepath.exists():
            raise ValueError("Cannot copy data if it does not exist")

        dst_path = os.path.join(str(self.full_path("Raw")), filepath.name)
        if os.path.isdir(filepath):
            shutil.copytree(filepath, dst_path)
        else:
            shutil.copy2(filepath, dst_path)
        LOGGER.debug(f"Copied {filepath} to {str(dst_path)}")

    def tree(self):
        """Returns tree representation of the document"""
        return self.fp.tree()

    def view(self) -> List[str]:
        """Returns tree-like representation of the dataset"""

        def get_children(o):

            return natsorted([i.path for i in o.values()])

        out = []
        for o in self.fp.values():
            if hasattr(o, "values"):
                children = get_children(o)
                out.extend(children)
        return out

    def _extend_group(self, group: Group):
        """Extends the functionality of the `Group` object by adding new attribute"""

    def get_reader(self, title):
        """Retrieve reader"""
        if title in self.file_reader:
            return self.file_reader[title]

    def set_reader(self, title, reader):
        """Set reader"""
        self.file_reader[title] = reader

    @property
    def tandem_spectra(self):
        return self._tandem_spectra

    @tandem_spectra.setter
    def tandem_spectra(self, value):
        self._tandem_spectra.set_from_dict(value)
