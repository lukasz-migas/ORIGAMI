"""Container object testing suite"""
# Standard library imports
import os

# Third-party imports
import numpy as np
import pytest

# Local imports
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

    @pytest.mark.parametrize("delimiter", (",", "\t", " "))
    def test_to_csv_with_zeros(self, tmpdir_factory, delimiter):
        path = str(tmpdir_factory.mktemp("output"))
        obj = self._get_obj()
        path = obj.to_csv(os.path.join(path, "mass_spectrum"), delimiter=delimiter, remove_zeros=False)
        data = np.loadtxt(path, delimiter=delimiter)
        assert data[0, 0] == 0

    @pytest.mark.parametrize("delimiter", (",", "\t", " "))
    def test_to_csv_without_zeros(self, tmpdir_factory, delimiter):
        path = str(tmpdir_factory.mktemp("output"))
        obj = self._get_obj()
        path = obj.to_csv(os.path.join(path, "mass_spectrum"), delimiter=delimiter, remove_zeros=True)
        data = np.loadtxt(path, delimiter=delimiter)
        assert data[0, 0] == 1


class TestChromatogramObject:
    @pytest.fixture()
    def fake_rt(self):
        """Synthetic chromatogram"""
        x, y = _get_1d_data()
        return ChromatogramObject(x, y)

    @pytest.fixture()
    def real_rt(self, get_env_with_document):
        """Chromatogram from document"""
        env, title = get_env_with_document
        document = env.on_get_document(title)
        return document["Chromatograms/Summed Chromatogram", True]

    def test_init(self, fake_rt):
        obj = fake_rt
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

    @pytest.mark.parametrize("x_label", ("Scans", "Time (mins)", "Retention time (mins)"))
    def test_change_x_label(self, fake_rt, x_label):
        obj = fake_rt
        obj.change_x_label(to_label=x_label, scan_time=1)
        assert obj.x_label == x_label

        obj.change_x_label(to_label="Restore default", scan_time=1)
        assert obj.x_label == "Scans"

    @pytest.mark.parametrize("x_label", ("Scans", "Time (mins)", "Retention time (mins)"))
    def test_change_x_label_doc(self, real_rt, x_label):
        obj = real_rt
        obj.change_x_label(to_label=x_label)
        assert obj.x_label == x_label

        obj.change_x_label(to_label="Restore default")
        assert obj.x_label == "Scans"

    @pytest.mark.parametrize("scan_time", (0, -5, None))
    def test_change_x_label_fail(self, fake_rt, scan_time):
        obj = fake_rt
        with pytest.raises(ValueError):
            obj.change_x_label(to_label="Time (mins)", scan_time=scan_time)

        with pytest.raises(ValueError):
            obj.change_x_label(to_label="TiME (MINS)", scan_time=5)

    @pytest.mark.parametrize("x_label", ("Time (mins)", "Retention time (mins)"))
    @pytest.mark.parametrize("scan_time", (0.5, 1, 5.0))
    def test_change_x_label_to_min(self, fake_rt, x_label, scan_time):
        obj = fake_rt
        obj.change_x_label(to_label=x_label, scan_time=scan_time)
        assert obj.x_label == x_label
        assert obj.x[-1] == (99 * scan_time) / 60

        obj.change_x_label(to_label="Scans", scan_time=scan_time)
        assert obj.x_label == "Scans"
        assert obj.x[-1] == 99

    @pytest.mark.parametrize("delimiter", (",", "\t", " "))
    def test_to_csv_with_zeros(self, fake_rt, tmpdir_factory, delimiter):
        path = str(tmpdir_factory.mktemp("output"))
        obj = fake_rt
        path = obj.to_csv(os.path.join(path, "chromatogram"), delimiter=delimiter, remove_zeros=False)
        data = np.loadtxt(path, delimiter=delimiter)
        assert data[0, 0] == 0

    @pytest.mark.parametrize("delimiter", (",", "\t", " "))
    def test_to_csv_without_zeros(self, fake_rt, tmpdir_factory, delimiter):
        path = str(tmpdir_factory.mktemp("output"))
        obj = fake_rt
        path = obj.to_csv(os.path.join(path, "chromatogram"), delimiter=delimiter, remove_zeros=True)
        data = np.loadtxt(path, delimiter=delimiter)
        assert data[0, 0] == 1


class TestMobilogramObject:
    @staticmethod
    def _get_obj():
        x, y = _get_1d_data()
        return MobilogramObject(x, y)

    @pytest.fixture()
    def real_dt(self, get_env_with_document):
        """Mobilogram from document"""
        env, title = get_env_with_document
        document = env.on_get_document(title)
        return document["Mobilograms/Summed Mobilogram", True]

    def test_init(self):
        obj = self._get_obj()
        assert obj.x_label == "Drift time (bins)"
        assert obj.y_label == "Intensity"
        assert len(obj.x_limit) == 2
        assert len(obj.y_limit) == 2

        x_bin = obj.x_bin
        assert len(x_bin) == len(obj.x)

        data = obj.to_dict()
        assert isinstance(data, dict)
        assert "x" in data
        assert "y" in data

        data, attrs = obj.to_zarr()
        assert isinstance(data, dict)
        assert isinstance(attrs, dict)
        assert "class" in attrs

    @pytest.mark.parametrize("x_label", ("Drift time (bins)", "Drift time (ms)", "Arrival time (ms)"))
    def test_change_x_label(self, x_label):
        obj = self._get_obj()
        obj.change_x_label(to_label=x_label, pusher_freq=100)
        assert obj.x_label == x_label

        obj.change_x_label(to_label="Restore default", pusher_freq=100)
        assert obj.x_label == "Drift time (bins)"

    @pytest.mark.parametrize("x_label", ("Drift time (bins)", "Drift time (ms)", "Arrival time (ms)"))
    def test_change_x_label_doc(self, real_dt, x_label):
        obj = real_dt
        obj.change_x_label(to_label=x_label)
        assert obj.x_label == x_label

        obj.change_x_label(to_label="Restore default")
        assert obj.x_label == "Drift time (bins)"

    @pytest.mark.parametrize("pusher_freq", (0, -5, None))
    def test_change_x_label_fail(self, pusher_freq):
        obj = self._get_obj()
        with pytest.raises(ValueError):
            obj.change_x_label(to_label="Time (mins)", pusher_freq=pusher_freq)

        with pytest.raises(ValueError):
            obj.change_x_label(to_label="TiME (MINS)", pusher_freq=100)

    @pytest.mark.parametrize("x_label", ("Drift time (ms)", "Arrival time (ms)"))
    @pytest.mark.parametrize("pusher_freq", (50, 100))
    def test_change_x_label_to_min(self, x_label, pusher_freq):
        obj = self._get_obj()
        obj.change_x_label(to_label=x_label, pusher_freq=pusher_freq)
        assert obj.x_label == x_label
        assert obj.x[-1] == 99 * (pusher_freq / 1000)

        obj.change_x_label(to_label="Drift time (bins)", pusher_freq=pusher_freq)
        assert obj.x_label == "Drift time (bins)"
        assert obj.x[-1] == 99

    @pytest.mark.parametrize("delimiter", (",", "\t", " "))
    def test_to_csv_with_zeros(self, tmpdir_factory, delimiter):
        path = str(tmpdir_factory.mktemp("output"))
        obj = self._get_obj()
        path = obj.to_csv(os.path.join(path, "mobilogram"), delimiter=delimiter, remove_zeros=False)
        data = np.loadtxt(path, delimiter=delimiter)
        assert data[0, 0] == 0

    @pytest.mark.parametrize("delimiter", (",", "\t", " "))
    def test_to_csv_without_zeros(self, tmpdir_factory, delimiter):
        path = str(tmpdir_factory.mktemp("output"))
        obj = self._get_obj()
        path = obj.to_csv(os.path.join(path, "mobilogram"), delimiter=delimiter, remove_zeros=True)
        data = np.loadtxt(path, delimiter=delimiter)
        assert data[0, 0] == 1
