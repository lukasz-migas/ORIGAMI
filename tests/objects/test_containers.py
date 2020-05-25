# Third-party imports
import numpy as np

# Local imports
from origami.objects.containers import MobilogramObject
from origami.objects.containers import ChromatogramObject
from origami.objects.containers import MassSpectrumObject


def get_data():
    x = np.arange(100)
    y = np.arange(100)
    return x, y


class TestMassSpectrumObject:
    def test_init(self):
        x, y = get_data()
        obj = MassSpectrumObject(x, y)
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


class TestChromatogramObject:
    def test_init(self):
        x, y = get_data()
        obj = ChromatogramObject(x, y)
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
    def test_init(self):
        x, y = get_data()
        obj = MobilogramObject(x, y)
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
