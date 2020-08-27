"""Init"""
# Third-party imports
from zarr import Group

# Local imports
from origami.objects.containers.base import DataObject
from origami.objects.containers.heatmap import IonHeatmapObject
from origami.objects.containers.heatmap import StitchIonHeatmapObject
from origami.objects.containers.heatmap import MassSpectrumHeatmapObject
from origami.objects.containers.spectrum import MobilogramObject
from origami.objects.containers.spectrum import ChromatogramObject
from origami.objects.containers.spectrum import MassSpectrumObject
from origami.objects.containers.utilities import get_data
from origami.objects.containers.utilities import get_extra_data


def mass_spectrum_object(group: Group, quick: bool = False) -> DataObject:
    """Instantiate mass spectrum object from mass spectrum group saved in zarr format"""
    metadata = group.attrs.asdict()
    obj = MassSpectrumObject(
        *get_data(group, ["x", "y"], quick), extra_data=get_extra_data(group, ["x", "y"], quick), **metadata
    )
    obj.set_metadata(metadata)
    return obj


def chromatogram_object(group: Group, quick: bool = False) -> DataObject:
    """Instantiate chromatogram object from chromatogram group saved in zarr format"""
    metadata = group.attrs.asdict()
    obj = ChromatogramObject(
        *get_data(group, ["x", "y"], quick), extra_data=get_extra_data(group, ["x", "y"], quick), **metadata
    )
    obj.set_metadata(metadata)
    return obj


def mobilogram_object(group: Group, quick: bool = False) -> DataObject:
    """Instantiate mobilogram object from mobilogram group saved in zarr format"""
    metadata = group.attrs.asdict()
    obj = MobilogramObject(
        *get_data(group, ["x", "y"], quick), extra_data=get_extra_data(group, ["x", "y"], quick), **metadata
    )
    obj.set_metadata(metadata)
    return obj


def ion_heatmap_object(group: Group, quick: bool = False) -> DataObject:
    """Instantiate ion heatmap object from ion heatmap group saved in zarr format"""
    metadata = group.attrs.asdict()
    obj = IonHeatmapObject(
        *get_data(group, ["array", "x", "y", "xy", "yy"], quick),
        extra_data=get_extra_data(group, ["array", "x", "y", "xy", "yy"], quick),
        **metadata,
    )
    obj.set_metadata(metadata)
    return obj


def stitch_ion_heatmap_object(group: Group, quick: bool = False) -> DataObject:
    """Instantiate stitch ion heatmap object from ion heatmap group saved in zarr format"""
    metadata = group.attrs.asdict()
    obj = StitchIonHeatmapObject(
        *get_data(group, ["array", "x", "y", "xy", "yy"], quick),
        extra_data=get_extra_data(group, ["array", "x", "y", "xy", "yy"], quick),
        **metadata,
    )
    obj.set_metadata(metadata)
    return obj


def msdt_heatmap_object(group: Group, quick: bool = False) -> DataObject:
    """Instantiate mass heatmap object from ion heatmap group saved in zarr format"""
    metadata = group.attrs.asdict()
    obj = MassSpectrumHeatmapObject(
        *get_data(group, ["array", "x", "y", "xy", "yy"], quick),
        extra_data=get_extra_data(group, ["array", "x", "y", "xy", "yy"], quick),
        **metadata,
    )
    obj.set_metadata(metadata)
    return obj
