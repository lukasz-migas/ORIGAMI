"""Init groups"""
# Third-party imports
from zarr import Group
from natsort import natsorted

# Local imports
from origami.objects.groups.base import DataGroup
from origami.objects.groups.heatmap import IonHeatmapGroup
from origami.objects.groups.spectrum import MobilogramGroup
from origami.objects.groups.spectrum import ChromatogramGroup
from origami.objects.groups.spectrum import MassSpectrumGroup


def get_item_list(document_title: str, group: Group):
    """Get list of items within a group object"""
    item_list = natsorted(list(group.keys()))
    _item_list = []
    for item in item_list:
        _item_list.append([document_title, f"{group.path}/{item}"])
    return _item_list


def mass_spectrum_group_object(document_title: str, group: Group) -> DataGroup:
    """Instantiate mass spectrum group object"""
    metadata = group.attrs.asdict()
    obj = MassSpectrumGroup(get_item_list(document_title, group))
    obj.set_metadata(metadata)
    return obj


def chromatogram_group_object(document_title: str, group: Group) -> DataGroup:
    """Instantiate mass spectrum group object"""
    metadata = group.attrs.asdict()
    obj = ChromatogramGroup(get_item_list(document_title, group))
    obj.set_metadata(metadata)
    return obj


def mobilogram_group_object(document_title: str, group: Group) -> DataGroup:
    """Instantiate mass spectrum group object"""
    metadata = group.attrs.asdict()
    obj = MobilogramGroup(get_item_list(document_title, group))
    obj.set_metadata(metadata)
    return obj


def ion_heatmap_group_object(document_title: str, group: Group) -> DataGroup:
    """Instantiate mass spectrum group object"""
    metadata = group.attrs.asdict()
    obj = IonHeatmapGroup(get_item_list(document_title, group))
    obj.set_metadata(metadata)
    return obj
