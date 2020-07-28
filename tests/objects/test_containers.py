# Third-party imports
import numpy as np

# Local imports
import pytest

from origami.objects.containers import MobilogramObject
from origami.objects.containers import ChromatogramObject
from origami.objects.containers import MassSpectrumObject


def _get_1d_data():
    x = np.arange(100)
    y = np.arange(100)
    return x, y


class TestMassSpectrumObject:
    @staticmethod
    def _get_obj():
        x, y = _get_1d_data()
        return MassSpectrumObject(x, y)

    def test_init(self):
        obj = self._get_obj()
        assert obj.x_label == "m/z (Da)"
        assert obj.y_label == "Intensity"
        assert len(obj.x_limit) == 2
        assert len(obj.y_limit) == 2

        data = obj.to_dict()
        assert isinstance(data, dict)
        assert "x" in data
        assert "y" in data

        data, attrs = obj.to_zarr()
        assert isinstance(data, dict)
        assert isinstance(attrs, dict)
        assert "class" in attrs

    def test_process(self):
        # normalize
        obj = self._get_obj()
        assert obj.unsaved is False
        obj.process()
        assert obj.unsaved is False

    def test_normalize(self):
        # normalize
        obj = self._get_obj()
        assert obj.unsaved is False
        obj.normalize()
        assert obj.unsaved is True
        assert obj.y_limit[1] == 1.0

    def test_baseline(self):
        # normalize
        obj = self._get_obj()
        assert obj.unsaved is False

        with pytest.raises(TypeError):
            obj.baseline()
        with pytest.raises(ValueError):
            obj.baseline(threshold=-1)

        obj.baseline(threshold=1)
        assert obj.unsaved is True

    def test_smooth(self):
        # normalize
        obj = self._get_obj()
        assert obj.unsaved is False
        obj.smooth()
        assert obj.unsaved is True

    def test_linearize(self):
        # normalize
        obj = self._get_obj()
        assert obj.unsaved is False
        with pytest.raises(TypeError):
            obj.linearize()

    @pytest.mark.parametrize("crop_min, crop_max", ([0, 50], [25, 75]))
    def test_crop(self, crop_min, crop_max):
        obj = self._get_obj()
        assert obj.unsaved is False
        obj.crop(crop_min, crop_max)
        assert obj.unsaved is True
        x_min, x_max = obj.x_limit
        assert crop_min == x_min
        assert crop_max == x_max


class TestChromatogramObject:
    @staticmethod
    def _get_obj():
        x, y = _get_1d_data()
        return ChromatogramObject(x, y)

    def test_init(self):
        obj = self._get_obj()
        assert obj.x_label == "Scans"
        assert obj.y_label == "Intensity"
        assert len(obj.x_limit) == 2
        assert len(obj.y_limit) == 2

        data = obj.to_dict()
        assert isinstance(data, dict)
        assert "x" in data
        assert "y" in data

        data, attrs = obj.to_zarr()
        assert isinstance(data, dict)
        assert isinstance(attrs, dict)
        assert "class" in attrs


class TestMobilogramObject:
    @staticmethod
    def _get_obj():
        x, y = _get_1d_data()
        return MobilogramObject(x, y)

    def test_init(self):
        obj = self._get_obj()
        assert obj.x_label == "Drift time (bins)"
        assert obj.y_label == "Intensity"
        assert len(obj.x_limit) == 2
        assert len(obj.y_limit) == 2

        data = obj.to_dict()
        assert isinstance(data, dict)
        assert "x" in data
        assert "y" in data

        data, attrs = obj.to_zarr()
        assert isinstance(data, dict)
        assert isinstance(attrs, dict)
        assert "class" in attrs
