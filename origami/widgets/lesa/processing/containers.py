"""LESA container objects"""
# Third-party imports
import numpy as np
from zarr import Group

# Local imports
from origami.objects.containers.base import DataObject
from origami.objects.containers.heatmap import HeatmapObject
from origami.objects.containers.utilities import get_extra_data


class ImagingIonHeatmapObject(HeatmapObject):
    """Heatmap object for imaging purposes"""

    def __init__(
        self, array: np.ndarray, name: str = "", metadata=None, extra_data=None, x_label="x", y_label="y", **kwargs
    ):
        # pre-process data before setting it up in the container
        array, x, y = self._preprocess(array)

        super().__init__(
            array,
            x=x,
            y=y,
            x_label=x_label,
            y_label=y_label,
            metadata=metadata,
            extra_data=extra_data,
            name=name,
            **kwargs,
        )

    @staticmethod
    def _preprocess(array: np.ndarray):
        """"""
        x = np.arange(array.shape[1])
        y = np.arange(array.shape[0])

        return array, x, y

    def apply_norm(self, norm):
        """Normalize array"""
        self._array = self.array / norm

        return self


class Normalizer:
    """Normalization class"""

    def __init__(self, array: np.ndarray, x_dim: int, y_dim: int):
        self._array = array
        self.x_dim = x_dim
        self.y_dim = y_dim

    def __call__(self, array: np.ndarray = None, img_obj: ImagingIonHeatmapObject = None):
        """Normalize existing array"""

        def _reshape():
            _array = np.flipud(np.reshape(self._array, (self.x_dim, self.y_dim)))
            return _array

        if array is not None:
            if len(array.shape) == 1:
                array /= self._array
            else:
                array /= _reshape()
            return array
        elif img_obj is not None:
            return img_obj.apply_norm(_reshape())


def normalization_object(group: Group) -> Normalizer:
    """Instantiate normalization object"""
    return Normalizer(group["array"][:], group.attrs["x_dim"], group.attrs["y_dim"])


def imaging_heatmap_object(group: Group) -> DataObject:
    """Instantiate ion heatmap object from ion heatmap group saved in zarr format"""
    metadata = group.attrs.asdict()
    obj = ImagingIonHeatmapObject(
        group["array"][:],
        group["x"][:],
        group["y"][:],
        group["xy"][:],
        group["yy"][:],
        extra_data=get_extra_data(group, ["array", "x", "y", "xy", "yy"]),
        **group.attrs.asdict(),
    )
    obj.set_metadata(metadata)
    return obj
