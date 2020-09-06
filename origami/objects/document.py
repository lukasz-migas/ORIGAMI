"""Wrapper around Zarr's file object with functions amenable to ORIGAMI's dataset"""
# Standard library imports
import os
import re
import shutil
import logging
from typing import Dict
from typing import List
from typing import Tuple
from typing import Union
from typing import Optional
from pathlib import Path

# Third-party imports
import zarr
import numpy as np
from zarr import Array
from zarr import Group
from natsort import natsorted
from zarr.util import is_valid_python_name

# Local imports
from origami import __version__
from origami.utils.path import clean_filename
from origami.objects.groups import mobilogram_group_object
from origami.objects.groups import ion_heatmap_group_object
from origami.objects.groups import chromatogram_group_object
from origami.objects.groups import mass_spectrum_group_object
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
from origami.objects.groups.base import DataGroup
from origami.widgets.ccs.processing.containers import ccs_calibration_object
from origami.widgets.lesa.processing.containers import normalization_object

LOGGER = logging.getLogger(__name__)


# TODO: add option to only flush some of the data to disk (e.g. metadata, extra_data)


def get_children(o):
    """Return list of children of the group object"""
    return natsorted([i.path for i in o.values()])


def get_children_quick(group_name: str, o):
    """Return list of children of the group object without ready data"""
    return natsorted([f"{group_name}/{obj_name}" for obj_name in o])


def check_path(path: Union[str, List]):
    """Check whether path(s) exist on the file system"""
    if isinstance(path, str):
        if not os.path.exists(path):
            return False
    elif isinstance(path, list):
        for _path in path:
            if not os.path.exists(_path):
                return False
    return True


class DocumentGroups:
    """Enumeration object keeping track of the current names of various folders / groups used by the DocumentStore"""

    # group names
    MS = "MassSpectra"
    RT = "Chromatograms"
    DT = "Mobilograms"
    HEATMAP = "IonHeatmaps"
    MSDT = "MSDTHeatmaps"
    METADATA = "Metadata"
    OVERLAY = "Overlays"
    CONFIG = "Configs"
    RAW = "Raw"
    OUTPUT = "Output"
    TANDEM = "Tandem"
    CALIBRATION = "CCSCalibrations"

    # average/summed objects
    MassSpectrum = "MassSpectra/Summed Spectrum"
    Chromatogram = "Chromatograms/Summed Chromatogram"
    Mobilogram = "Mobilograms/Summed Mobilogram"
    Heatmap = "IonHeatmaps/Summed Heatmap"
    MassHeatmap = "MSDTHeatmaps/Summed Heatmap"


class DocumentStore:
    """DocumentStore object"""

    VERSION: int = 1
    EXTENSION: str = ".origami"
    # defines the groups that can be present in a document
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
        "Views",  # json with information about a specific view
        "CCSCalibrations",  # any CCS calibration
    ]
    # defines the types of document that can extract data
    CAN_EXTRACT = [
        "Format: Waters (.raw)",
        "Format: MassLynx (.raw)",
        "Format: Thermo (.RAW)",
        "Format: Multiple Waters (.raw)",
        "Format: Multiple MassLynx (.raw)",
        "Format: Multiple Thermo (.RAW)",
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

        self.add_config("paths", dict())
        self._check_version()

    def __repr__(self):
        return f"{self.__class__.__name__}<{str(self.path)}>"

    def __getitem__(self, item):
        """Get item from the store"""
        as_object, quick = False, False
        if isinstance(item, tuple):
            if len(item) == 2:
                item, as_object = item
            if len(item) == 3:
                item, as_object, quick = item
        if not isinstance(item, str):
            raise ValueError(f"Expected str and got {type(item)} ({item})")

        if as_object:
            return self.as_object(self.fp[item], quick)
        return self.fp[item]

    def __contains__(self, item):
        """Check whether object is present in the store"""
        return item in self.fp

    def __delitem__(self, key):
        """Delete item from the document"""
        item: Group = self[key]

        # remove all objects from group
        if hasattr(item, "clear"):
            if item.path not in self.GROUPS:
                del self.fp[key]
            else:
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

    def __enter__(self):
        """Return the Group for use as a context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """If the underlying Store has a ``close`` method, call it."""
        try:
            self.fp.store.close()
        except AttributeError:
            pass

    def as_object(self, group: Group, quick: bool = False):
        """Returns the group data as an object"""
        klass_name = group.attrs.get("class", None)
        obj = None

        if klass_name == "MassSpectrumObject":
            obj = mass_spectrum_object(group, quick)
        elif klass_name == "ChromatogramObject":
            obj = chromatogram_object(group, quick)
        elif klass_name == "MobilogramObject":
            obj = mobilogram_object(group, quick)
        elif klass_name == "MassSpectrumHeatmapObject":
            obj = msdt_heatmap_object(group, quick)
        elif klass_name == "IonHeatmapObject":
            obj = ion_heatmap_object(group, quick)
        elif klass_name == "StitchIonHeatmapObject":
            obj = ion_heatmap_object(group, quick)
        elif klass_name == "ImagingIonHeatmapObject":
            obj = ion_heatmap_object(group, quick)
        elif klass_name == "CCSCalibrationObject":
            obj = ccs_calibration_object(group, quick)
        elif klass_name == "MassSpectrumGroup":
            obj = mass_spectrum_group_object(self.title, group)
        elif klass_name == "ChromatogramGroup":
            obj = chromatogram_group_object(self.title, group)
        elif klass_name == "MobilogramGroup":
            obj = mobilogram_group_object(self.title, group)
        elif klass_name == "IonHeatmapGroup":
            obj = ion_heatmap_group_object(self.title, group)

        # return instantiated objected
        if obj:
            # associate object with metadata
            obj.set_owner((self.title, group.path))
            obj.set_output_path(self.output_path)
            obj.set_full_path(os.path.join(self.path, group.path))

            return obj

        raise ValueError(f"Not sure how to handle {klass_name} ({group})")

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
            LOGGER.warning("The current version of the document is out of date - update will happen automatically.")

    def _ipython_key_completions_(self):
        return sorted(self)

    @staticmethod
    def _has_extension(path, extension):
        """Cleans-up path"""
        path = Path(path)
        return str(path.with_suffix(extension))

    @property
    def groups(self):
        """Returns list of groups"""
        return [group for group in self.fp.group_keys()]

    @property
    def info(self):
        """Return document information"""
        return self.fp.info

    @property
    def title(self):
        """Returns the title of the document"""
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
        """Returns the file type of the dataset"""
        return self.fp.attrs["file_format"]

    @property
    def parameters(self):
        """Returns parameters object"""
        if "Metadata/Parameters" in self:
            return self["Metadata/Parameters"].attrs.asdict()
        return {}

    def has_ccs_calibration(self):
        """Checks whether there are any CCS calibrations in the document"""
        return (len(self.get_ccs_calibration_list())) > 0

    def is_imaging(self):
        """Checks whether the document is a LESA-imaging document"""
        if "Imaging" not in self.data_type:
            return False
        return True

    def is_origami_ms(self, check_parameters: bool = False):
        """Checks whether the document is a ORIGAMI-MS document"""
        if self.data_type != "Type: ORIGAMI":
            return False
        if check_parameters:
            cfg = self.get_config("origami_ms")
            if cfg is None:
                return False
        return True

    def is_multifile(self):
        """Checks whether the document is a Multifile document"""
        if "Multi" in self.file_format:
            return True

    def can_extract(self) -> Tuple[bool, bool, str]:
        """Checks whether this document can be used for data extraction. Returns tuple of bool values to indicate
        whether data can be extracted and/or the dataset uses multiple raw file

        Returns
        -------
        can_extract : bool
            specifies whether data can be extracted for the file
        is_multifile : bool
            specifies whether the document is based on multiple raw files (e.g. LESA or manual CIU/SID)
        file_fmt : str
            specifies whether raw data is in Waters, Thermo or other file format
        """
        if self.file_format not in self.CAN_EXTRACT:
            return False, False, ""

        file_fmt = "waters"
        if "Thermo" in self.file_format:
            file_fmt = "thermo"

        if self.is_multifile():
            return True, True, file_fmt
        return True, False, file_fmt

    def get_multifile_filelist(self, keys: List[str] = None):
        """Return filelist that corresponds to a multi-file object"""
        if not self.is_multifile():
            return dict()

        paths = self.get_file_path("multifile")
        if paths in ["", None]:
            return dict()

        if keys is None:
            return paths

        _paths = {}
        for path, value in paths.items():
            _paths[path] = []
            for key in keys:
                _paths[path].append(value.get(key, ""))
        return _paths

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
        elif len(parts) == 3:
            group = self.get(key)
            if group is None:
                # _group = self[parts[0]].create_group(parts[1])
                group = self[parts[0]][parts[1]].create_group(parts[2])
        else:
            raise ValueError(f"Not sure what to do (key={key})")
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

    def add_spectrum(self, title: str, data: Union[Dict, DataObject] = None, attrs: Optional[Dict] = None):
        """Adds mass spectrum to the document"""
        if isinstance(data, DataObject):
            data, attrs = data.to_zarr()
        if not title.startswith(DocumentGroups.MS):
            title = f"{DocumentGroups.MS}/{title}"
        group = self.add(title, data, attrs)
        return self.as_object(group)

    def add_chromatogram(self, title: str, data: Union[Dict, DataObject] = None, attrs: Optional[Dict] = None):
        """Adds chromatogram to the document"""
        if isinstance(data, DataObject):
            data, attrs = data.to_zarr()
        if not title.startswith(DocumentGroups.RT):
            title = f"{DocumentGroups.RT}/{title}"
        group = self.add(title, data, attrs)
        return self.as_object(group)

    def add_mobilogram(self, title: str, data: Union[Dict, DataObject] = None, attrs: Optional[Dict] = None):
        """Adds mobilograms to the document"""
        if isinstance(data, DataObject):
            data, attrs = data.to_zarr()
        if not title.startswith(DocumentGroups.DT):
            title = f"{DocumentGroups.DT}/{title}"
        group = self.add(title, data, attrs)
        return self.as_object(group)

    def add_heatmap(self, title: str, data: Union[Dict, DataObject] = None, attrs: Optional[Dict] = None):
        """Adds heatmap to the document"""
        if isinstance(data, DataObject):
            data, attrs = data.to_zarr()
        if not title.startswith(DocumentGroups.HEATMAP):
            title = f"{DocumentGroups.HEATMAP}/{title}"
        group = self.add(title, data, attrs)
        return self.as_object(group)

    def add_msdt(self, title: str, data: Union[Dict, DataObject] = None, attrs: Optional[Dict] = None):
        """Adds heatmap to the document"""
        if isinstance(data, DataObject):
            data, attrs = data.to_zarr()
        if not title.startswith(DocumentGroups.MSDT):
            title = f"{DocumentGroups.MSDT}/{title}"
        group = self.add(title, data, attrs)
        return self.as_object(group)

    def add_ccs_calibration(self, title: str, data: Union[Dict, DataObject] = None, attrs: Optional[Dict] = None):
        """Adds ccs calibration to the document"""
        if isinstance(data, DataObject):
            data, attrs = data.to_zarr()
        if not title.startswith(DocumentGroups.CALIBRATION):
            title = f"{DocumentGroups.CALIBRATION}/{title}"
        group = self.add(title, data, attrs)
        return self.as_object(group)

    def add_metadata(self, title: str, data: Union[Dict, DataObject] = None, attrs: Optional[Dict] = None):
        """Adds metadata to the document"""
        if isinstance(data, DataObject):
            data, attrs = data.to_zarr()
        group = self.add(f"{DocumentGroups.METADATA}/{title}", data, attrs)
        return group

    def add_raw(self, filepath: Union[str, Path]):
        """Copies raw file to the ORIGAMI directory

        Parameters
        ----------
        filepath : str
            path of the file to be added to the `Raw` directory
        """
        filepath = Path(filepath)
        if not filepath.exists():
            raise ValueError("Cannot copy data if it does not exist")

        dst_path = os.path.join(str(self.full_path(DocumentGroups.RAW)), filepath.name)
        if os.path.isdir(filepath):
            shutil.copytree(filepath, dst_path)
        else:
            shutil.copy2(filepath, dst_path)
        LOGGER.debug(f"Copied {filepath} to {str(dst_path)}")

    def add_overlay(self, title: str, group_obj: DataGroup):
        """Adds ccs calibration to the document"""
        if not isinstance(group_obj, DataGroup):
            raise ValueError("Cannot export object of this type")

        data, attrs = group_obj.to_zarr()
        if not title.startswith(DocumentGroups.OVERLAY):
            title = f"{DocumentGroups.OVERLAY}/{title}"
        group = self.add(title, data, attrs)

        # iterate over all data objects retained within the group object
        for i, data_obj in enumerate(group_obj):
            dataset_name = data_obj.dataset_name
            self.add_group_to_group(group, f"{i}_{dataset_name}", data_obj)
        return group_obj

    def add_group_to_group(
        self, group: Group, title: str, data: Union[Dict, DataObject] = None, attrs: Optional[Dict] = None
    ):
        """Add sub-group to a non-main group.

        This method should be used whenever adding multi-array data to a
        child object (e.g. UniDec results data to a MassSpectrum)
        """
        if isinstance(data, DataObject):
            data, attrs = data.to_zarr()
        sub_group = self.add(f"{group.path}/{title}", data, attrs)
        return sub_group

    def add(self, key, data=None, attrs=None, as_object: bool = False):
        """Add data to group"""
        # TODO: add name check so that names are always valid keys
        if isinstance(data, DataObject):
            data, attrs = data.to_zarr()
        if data is None:
            data = dict()
        if attrs is None:
            attrs = dict()

        # get group and add data to it
        group = self._get(key)
        group = self._set_group_data(group, data, attrs)
        if as_object:
            return self.as_object(group)
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

    def duplicate(self, path: str, overwrite: bool = False):
        """Create copy of the document with new name"""
        from origami.utils.path import copy_directory

        if path == self.path:
            raise ValueError("Destination path cannot be the same as the DocumentStore path")

        # ensure path ends with ORIGAMI
        if not path.endswith(".origami"):
            path += ".origami"
            LOGGER.warning(f"Path `{path}` should end with `.origami` extension")

        try:
            copy_directory(self.path, path, overwrite)
            return DocumentStore(path)
        except OSError:
            LOGGER.error("Could not duplicate directory")

    def remove(self, item):
        """Deletes all data and the root directory from the store"""
        try:
            del self.fp[item]
        except KeyError:
            LOGGER.warning(f"Could not delete `{item}`")

    def delete(self):
        """Delete DocumentStore from the disk"""
        from send2trash import send2trash, TrashPermissionError

        try:
            send2trash(self.path)
            LOGGER.info(f"Send directory `{self.path}` to the Recycle Bin")
        except TrashPermissionError:
            LOGGER.error("Could not delete self")

    def copy(self, item: str, copy: Optional[str] = None):
        """Copy object and set it inside the document"""
        group = self._get(item)
        if copy is None:
            copy = self._get_unique_name(item, 2)

        self.add(copy, {k: v[:] for k, v in group.items()}, attrs=group.attrs.asdict())

    def get_new_name(self, name: str, suffix: str):
        """Return new name for an object

        Parameters
        ----------
        name : str
            base name of the item
        suffix : str
            suffix to be added to the base name (e.g. `copy` will result in (copy 0...)

        Returns
        -------
        name : str
            new name that does not exist on the hard drive
        """

        def _new_name(name, n):
            if n == 0 or f"({suffix})" not in name:
                name = name + f" ({suffix} %d)" % n
            else:
                name = name.replace(f" ({suffix} {n-1})", f" ({suffix} {n})")

            return name

        prev = re.findall(rf"\({suffix} (\d+)", name)  # noqa
        n = 0

        if prev:
            n = int(prev[-1])

        while True:
            _name = _new_name(name, n)
            if not os.path.exists(os.path.join(self.path, _name)):
                break
            n += 1

        name = _new_name(name, n)
        return name

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
            if isinstance(value, Array):
                value = value[:]
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
        if not isinstance(data, dict):
            raise ValueError("Configuration file should be a dictionary object")
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

    def tree(self):
        """Returns tree representation of the document"""
        return self.fp.tree()

    def view(self) -> List[str]:
        """Returns tree-like representation of the dataset"""

        out = []
        for o in self.fp.values():
            if hasattr(o, "values"):
                children = get_children(o)
                out.extend(children)
        return out

    def view_group(self, group_name: str):
        """View group elements"""
        try:
            group = self.fp[group_name]
        except KeyError:
            LOGGER.warning(f"Group `{group_name}` does not exist")
            return []
        return get_children_quick(group_name, group)

    def _extend_group(self, group: Group):
        """Extends the functionality of the `Group` object by adding new attribute"""

    def add_reader(self, title, reader):
        """Set reader"""
        self.file_reader[title] = reader
        self.add_file_path(title, reader.path)

    def get_reader(self, title):
        """Retrieve reader"""
        if title in self.file_reader:
            return self.file_reader[title]

    def add_file_path(self, title: str, path: str):
        """Add file path associated with the document"""
        config = self.get_config("paths")
        config[title] = path
        self.add_config("paths", config)

    def get_file_path(self, title: str):
        """Return path to a raw file"""
        config = self.get_config("paths")
        return config.get(title, "")

    def get_file_paths(self):
        """Return the whole configuration object"""
        config = self.get_config("paths")
        return config

    @property
    def tandem_spectra(self):
        """Return the tandem spectra object"""
        return self._tandem_spectra

    @tandem_spectra.setter
    def tandem_spectra(self, value):
        """Set the tandem spectra object"""
        self._tandem_spectra.set_from_dict(value)

    def get_normalization_list(self):
        """Returns list of normalization(s) available in an imaging document"""
        normalizations = ["None"]
        for key in self.Metadata.keys():
            if key.startswith("Normalization"):
                normalizations.append(key)
        return normalizations

    def get_normalization(self, name: str):
        """Return normalization object"""
        if name not in self.get_normalization_list():
            raise ValueError(f"Cannot get `{name}` normalization as its not present in the Document")

        return normalization_object(self.Metadata[name])

    def get_ccs_calibration_list(self):
        """Returns list of CCS calibrations available in the document"""
        calibrations = self.view_group(DocumentGroups.CALIBRATION)
        return calibrations

    def get_ccs_calibration(self, name: str):
        """Return CCS calibration object"""
        if name not in self.get_ccs_calibration_list():
            raise ValueError(f"Cannot get `{name}` calibration as its not present in the Document.")

        if "/" in name or name.startswith(DocumentGroups.CALIBRATION):
            name = name.split("/")[-1]

        return self.as_object(self.CCSCalibrations[name])

    def get_overlay_list(self):
        """Returns list of Overlays available in the document"""
        overlays = self.view_group(DocumentGroups.OVERLAY)
        return overlays

    def get_overlay(self, name: str):
        """Return Overlay object"""
        if name not in self.get_overlay_list():
            raise ValueError(f"Cannot get `{name}` overlay as its not present in the Document.")

        if "/" in name or name.startswith(DocumentGroups.OVERLAY):
            name = name.split("/")[-1]

        return self.as_object(self.Overlays[name])
