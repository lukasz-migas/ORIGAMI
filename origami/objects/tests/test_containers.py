from origami.objects.containers import MassSpectrumObject
import numpy as np


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
        assert "xvals" in data
        assert "yvals" in data
