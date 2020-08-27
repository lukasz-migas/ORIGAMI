"""Test heatmap containers"""
# Standard library imports
import os

# Third-party imports
import numpy as np
import pytest

# Local imports
from origami.objects.containers import MobilogramObject
from origami.objects.containers import ChromatogramObject
from origami.objects.containers.heatmap import IonHeatmapObject
from origami.objects.containers.heatmap import MassSpectrumHeatmapObject


def _get_2d_data():
    x = np.arange(50)
    y = np.arange(100)
    array = np.zeros((100, 50))
    return x, y, array


class TestIonHeatmapObject:
    @staticmethod
    def _get_obj():
        x, y, array = _get_2d_data()
        return IonHeatmapObject(array, x=x, y=y)

    def test_init(self):
        obj = self._get_obj()
        assert len(obj.shape) == 2
        assert obj.x_label == "Scans"
        assert obj.y_label == "Drift time (bins)"
        assert len(obj.x_limit) == 2
        assert len(obj.y_limit) == 2
        assert len(obj.z_limit) == 2
        assert obj.shape[0] == len(obj.y)
        assert obj.shape[1] == len(obj.x)

        # transpose
        shape = obj.shape
        obj.transpose()
        assert obj.unsaved is True
        assert obj.x_label == "Drift time (bins)"
        assert obj.y_label == "Scans"
        assert obj.shape != shape

        # check data
        assert isinstance(obj.x, np.ndarray)
        assert isinstance(obj.y, np.ndarray)
        assert isinstance(obj.array, np.ndarray)
        assert isinstance(obj.xy, np.ndarray)
        assert isinstance(obj.yy, np.ndarray)

        # reset cache
        obj.reset_xy_cache()
        assert obj._xy is None
        assert obj._yy is None

        # test exports
        data = obj.to_dict()
        assert isinstance(data, dict)
        assert "x" in data
        assert "y" in data
        assert "array" in data

        data, attrs = obj.to_zarr()
        assert isinstance(data, dict)
        assert isinstance(attrs, dict)
        assert "class" in attrs

        attrs = obj.to_attrs()
        assert isinstance(attrs, dict)
        assert "class" in attrs

    @pytest.mark.parametrize("x_min, x_max, y_min, y_max", ([0, 10, 0, 10], [0, 25, 0, 10], [0, 50, 0, 100]))
    def test_roi(self, x_min, x_max, y_min, y_max):
        obj = self._get_obj()
        x, y, array = obj.get_array_for_roi(x_min, x_max, y_min, y_max)
        assert len(y) == array.shape[0]
        assert len(x) == array.shape[1]

        x_only = obj.get_x_for_roi(x_min, x_max, y_min, y_max)
        assert len(x_only) == obj.shape[1]

        y_only = obj.get_y_for_roi(x_min, x_max, y_min, y_max)
        assert len(y_only) == obj.shape[0]

    @pytest.mark.parametrize("delimiter", (",", "\t", " "))
    def test_to_csv(self, tmpdir_factory, delimiter):
        path = str(tmpdir_factory.mktemp("output"))
        obj = self._get_obj()

        # export as heatmap
        _path = obj.to_csv(os.path.join(path, "heatmap"), delimiter=delimiter)
        assert os.path.exists(_path) is True
        data = np.loadtxt(_path, delimiter=delimiter)
        y = data[:, 0]
        array = data[:, 1:]
        assert data.shape[0] == obj.shape[0]
        assert data.shape[1] == obj.shape[1] + 1
        assert len(y) == len(obj.y)
        assert array.shape == obj.shape

        # export as mobilogram
        _path = obj.to_csv(os.path.join(path, "mobilogram"), delimiter=delimiter, dim_dt=True)
        assert os.path.exists(_path) is True
        data = np.loadtxt(_path, delimiter=delimiter)
        assert data.shape[0] == len(obj.y)
        np.testing.assert_array_almost_equal(data[:, 0], obj.y)

        # export as chromatogram
        _path = obj.to_csv(os.path.join(path, "chromatogram"), delimiter=delimiter, dim_rt=True)
        assert os.path.exists(_path) is True
        data = np.loadtxt(_path, delimiter=delimiter)
        assert data.shape[0] == len(obj.x)
        np.testing.assert_array_almost_equal(data[:, 0], obj.x)

    def test_as_object(self):
        obj = self._get_obj()
        dt_obj = obj.as_mobilogram()
        assert isinstance(dt_obj, MobilogramObject)
        np.testing.assert_equal(dt_obj.x, obj.y)
        np.testing.assert_equal(dt_obj.y, obj.yy)

        rt_obj = obj.as_chromatogram()
        assert isinstance(rt_obj, ChromatogramObject)
        np.testing.assert_equal(rt_obj.x, obj.x)
        np.testing.assert_equal(rt_obj.y, obj.xy)

    @pytest.mark.parametrize("scan_time", (0, -5, None))
    def test_change_x_label_fail(self, scan_time):
        obj = self._get_obj()
        with pytest.raises(ValueError):
            obj.change_x_label(to_label="Time (mins)", scan_time=scan_time)

        with pytest.raises(ValueError):
            obj.change_x_label(to_label="TiME (MINS)", scan_time=5)

    @pytest.mark.parametrize("x_label", ("Time (mins)", "Retention time (mins)"))
    @pytest.mark.parametrize("scan_time", (0.5, 1, 5.0))
    def test_change_x_label_to_min(self, x_label, scan_time):
        obj = self._get_obj()
        obj.change_x_label(to_label=x_label, scan_time=scan_time)
        assert obj.x_label == x_label
        assert obj.x[-1] == (49 * scan_time) / 60

        obj.change_x_label(to_label="Scans", scan_time=scan_time)
        assert obj.x_label == "Scans"
        assert obj.x[-1] == 49

    @pytest.mark.parametrize("pusher_freq", (0, -5, None))
    def test_change_y_label_fail(self, pusher_freq):
        obj = self._get_obj()
        with pytest.raises(ValueError):
            obj.change_y_label(to_label="Time (mins)", pusher_freq=pusher_freq)

        with pytest.raises(ValueError):
            obj.change_y_label(to_label="TiME (MINS)", pusher_freq=100)

    @pytest.mark.parametrize("x_label", ("Drift time (ms)", "Arrival time (ms)"))
    @pytest.mark.parametrize("pusher_freq", (50, 100))
    def test_change_y_label_to_ms(self, x_label, pusher_freq):
        obj = self._get_obj()
        obj.change_y_label(to_label=x_label, pusher_freq=pusher_freq)
        assert obj.y_label == x_label
        assert obj.y[-1] == 99 * (pusher_freq / 1000)

        obj.change_y_label(to_label="Drift time (bins)", pusher_freq=pusher_freq)
        assert obj.y_label == "Drift time (bins)"
        assert obj.y[-1] == 99


class TestMassSpectrumHeatmapObject:
    @staticmethod
    def _get_obj():
        x, y, array = _get_2d_data()
        return MassSpectrumHeatmapObject(array, x=x, y=y)

    def test_init(self):
        obj = self._get_obj()
        assert len(obj.shape) == 2
        assert obj.x_label == "m/z (Da)"
        assert obj.y_label == "Drift time (bins)"
        assert len(obj.x_limit) == 2
        assert len(obj.y_limit) == 2
        assert len(obj.z_limit) == 2
        assert obj.shape[0] == len(obj.y)
        assert obj.shape[1] == len(obj.x)

        # transpose
        shape = obj.shape
        obj.transpose()
        assert obj.unsaved is True
        assert obj.x_label == "Drift time (bins)"
        assert obj.y_label == "m/z (Da)"
        assert obj.shape != shape

        # check data
        assert isinstance(obj.x, np.ndarray)
        assert isinstance(obj.y, np.ndarray)
        assert isinstance(obj.array, np.ndarray)
        assert isinstance(obj.xy, np.ndarray)
        assert isinstance(obj.yy, np.ndarray)

        # reset cache
        obj.reset_xy_cache()
        assert obj._xy is None
        assert obj._yy is None

        # test exports
        data = obj.to_dict()
        assert isinstance(data, dict)
        assert "x" in data
        assert "y" in data
        assert "array" in data

        data, attrs = obj.to_zarr()
        assert isinstance(data, dict)
        assert isinstance(attrs, dict)
        assert "class" in attrs

        attrs = obj.to_attrs()
        assert isinstance(attrs, dict)
        assert "class" in attrs

    @pytest.mark.parametrize("x_min, x_max, y_min, y_max", ([0, 10, 0, 10], [0, 25, 0, 10], [0, 50, 0, 100]))
    def test_roi(self, x_min, x_max, y_min, y_max):
        obj = self._get_obj()
        x, y, array = obj.get_array_for_roi(x_min, x_max, y_min, y_max)
        assert len(y) == array.shape[0]
        assert len(x) == array.shape[1]

        x_only = obj.get_x_for_roi(x_min, x_max, y_min, y_max)
        assert len(x_only) == obj.shape[1]

        y_only = obj.get_y_for_roi(x_min, x_max, y_min, y_max)
        assert len(y_only) == obj.shape[0]

    @pytest.mark.parametrize("delimiter", (",", "\t", " "))
    def test_to_csv(self, tmpdir_factory, delimiter):
        path = str(tmpdir_factory.mktemp("output"))
        obj = self._get_obj()

        # export as heatmap
        _path = obj.to_csv(os.path.join(path, "heatmap"), delimiter=delimiter)
        assert os.path.exists(_path) is True
        data = np.loadtxt(_path, delimiter=delimiter)
        y = data[:, 0]
        array = data[:, 1:]
        assert data.shape[0] == obj.shape[0]
        assert data.shape[1] == obj.shape[1] + 1
        assert len(y) == len(obj.y)
        assert array.shape == obj.shape

        # export as mobilogram
        _path = obj.to_csv(os.path.join(path, "mobilogram"), delimiter=delimiter, dim_dt=True)
        assert os.path.exists(_path) is True
        data = np.loadtxt(_path, delimiter=delimiter)
        assert data.shape[0] == len(obj.y)
        np.testing.assert_array_almost_equal(data[:, 0], obj.y)

        # export as chromatogram
        _path = obj.to_csv(os.path.join(path, "chromatogram"), delimiter=delimiter, dim_rt=True)
        assert os.path.exists(_path) is True
        data = np.loadtxt(_path, delimiter=delimiter)
        assert data.shape[0] == len(obj.x)
        np.testing.assert_array_almost_equal(data[:, 0], obj.x)

    @pytest.mark.parametrize("pusher_freq", (0, -5, None))
    def test_change_y_label_fail(self, pusher_freq):
        obj = self._get_obj()
        with pytest.raises(ValueError):
            obj.change_y_label(to_label="Time (mins)", pusher_freq=pusher_freq)

        with pytest.raises(ValueError):
            obj.change_y_label(to_label="TiME (MINS)", pusher_freq=100)

    @pytest.mark.parametrize("x_label", ("Drift time (ms)", "Arrival time (ms)"))
    @pytest.mark.parametrize("pusher_freq", (50, 100))
    def test_change_y_label_to_ms(self, x_label, pusher_freq):
        obj = self._get_obj()
        obj.change_y_label(to_label=x_label, pusher_freq=pusher_freq)
        assert obj.y_label == x_label
        assert obj.y[-1] == 99 * (pusher_freq / 1000)

        obj.change_y_label(to_label="Drift time (bins)", pusher_freq=pusher_freq)
        assert obj.y_label == "Drift time (bins)"
        assert obj.y[-1] == 99
