# Third-party imports
import numpy as np

# Local imports
from origami.objects.groups.spectrum import SpectrumGroup
from origami.objects.containers import MassSpectrumObject


def _get_mass_spectrum_data():
    objs = []
    for i in range(5):
        x = np.arange(100 + i)
        y = np.random.randint(0, 1000, 100 + i)
        objs.append(MassSpectrumObject(x, y))
    return objs, y.shape[0]


class TestSpectrumGroup:
    def test_init(self):
        objs, y_shape = _get_mass_spectrum_data()

        group = SpectrumGroup(objs)
        assert group.n_objects == len(objs)
