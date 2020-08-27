"""Test CCS calibration"""
# Standard library imports
import os

# Third-party imports
import numpy as np
import pytest

# Local imports
from origami.config.environment import Environment
from origami.objects.containers.heatmap import IonHeatmapObject
from origami.objects.containers.spectrum import MobilogramObject
from origami.widgets.ccs.processing.containers import CalibrationIndex
from origami.widgets.ccs.processing.containers import CCSCalibrationObject
from origami.widgets.ccs.processing.calibration import CCSCalibrationProcessor


def _get_data():
    """This data was manually generated so any errors in the calibration will be also reflected in my spreadsheet..."""
    mz = [6439, 6173, 5926, 5685, 4256, 3987, 3760]
    mw = [148073.8199, 148127.8121, 148124.8043, 147783.7964, 63824.88255, 63775.87472, 63902.86689]
    charge = [23, 24, 25, 26, 15, 16, 17]
    td = [20.357, 18.797, 17.478, 16.417, 13.606, 12.295, 11.235]
    ccs = [6965, 6980, 6925, 6870, 3605, 3615, 3625]
    tdd = [20.23101789, 18.67364755, 17.35714059, 16.29862367, 13.5035763, 12.19586597, 11.13872942]
    tddd = [706.4138424, 703.3939361, 702.0365802, 703.7400906, 363.6616661, 365.4747045, 368.2639391]
    ccsd = [1602.42947, 1538.968868, 1465.768627, 1398.198871, 1271.585165, 1195.417718, 1128.211828]
    lntdd = [3.007216966, 2.927113308, 2.854003983, 2.791080667, 2.602954561, 2.501097039, 2.410428173]
    lnccsd = [7.379276175, 7.338867905, 7.290135044, 7.242940167, 7.148019563, 7.086250958, 7.028389205]

    x = [0.138, 0.276, 0.415, 0.553, 0.691, 0.83, 0.968]
    x_ccs = [116.4078413, 340.3701828, 482.4517068, 597.5004308, 698.0487218, 789.5398467, 873.2629173]

    array = np.zeros((len(mz), 5), dtype=np.float64)
    array[:, CalibrationIndex.mz] = mz
    array[:, CalibrationIndex.mw] = mw
    array[:, CalibrationIndex.charge] = charge
    array[:, CalibrationIndex.tD] = td
    array[:, CalibrationIndex.CCS] = ccs
    return (
        array,
        np.asarray(tdd),
        np.asarray(tddd),
        np.asarray(ccsd),
        np.asarray(lntdd),
        np.asarray(lnccsd),
        np.asarray(x),
        np.asarray(x_ccs),
    )


class TestCCSCalibrationProcessor:
    def test_init(self):
        correction_factor = 1.57
        gas_mw = 28.00615
        array, tdd, tddd, ccsd, lntdd, lnccsd, x, x_ccs = _get_data()  # noqa

        ccs_proc = CCSCalibrationProcessor(dict(), dict())
        assert ccs_proc._fitted is False
        _ = ccs_proc.create_calibration(array, gas_mw=gas_mw, correction_factor=correction_factor)
        assert ccs_proc._fitted is True

        # check object
        ccs_obj = ccs_proc.ccs_obj
        assert isinstance(ccs_obj, CCSCalibrationObject)

        # check values
        cali_array = ccs_proc.calibration
        assert isinstance(cali_array, np.ndarray)
        np.testing.assert_array_almost_equal(cali_array[:, CalibrationIndex.tDd], tdd)
        np.testing.assert_array_almost_equal(cali_array[:, CalibrationIndex.tDdd], tddd)
        np.testing.assert_array_almost_equal(cali_array[:, CalibrationIndex.CCSd], ccsd)
        np.testing.assert_array_almost_equal(cali_array[:, CalibrationIndex.lntDd], lntdd)
        np.testing.assert_array_almost_equal(cali_array[:, CalibrationIndex.lnCCSd], lnccsd)

        # check parameters
        r2_lin = ccs_proc.r2_linear
        assert isinstance(r2_lin, float)
        r2_log = ccs_proc.r2_log
        assert isinstance(r2_log, float)

    def test_prepare(self):
        correction_factor = 1.57
        gas_mw = 28.00615
        mz = [6439, 6173, 5926, 5685, 4256, 3987, 3760]
        mw = [148073.8199, 148127.8121, 148124.8043, 147783.7964, 63824.88255, 63775.87472, 63902.86689]
        charge = [23, 24, 25, 26, 15, 16, 17]
        td = [20.357, 18.797, 17.478, 16.417, 13.606, 12.295, 11.235]
        ccs = [6965, 6980, 6925, 6870, 3605, 3615, 3625]
        _, tdd, tddd, ccsd, lntdd, lnccsd, x, x_ccs = _get_data()  # noqa

        ccs_proc = CCSCalibrationProcessor(dict(), dict())
        array = ccs_proc.prepare_array(mz, mw, charge, td, ccs)
        assert ccs_proc._fitted is False
        _ = ccs_proc.create_calibration(array, gas_mw=gas_mw, correction_factor=correction_factor)
        assert ccs_proc._fitted is True

        # check values
        cali_array = ccs_proc.calibration
        assert isinstance(cali_array, np.ndarray)
        np.testing.assert_array_almost_equal(cali_array[:, CalibrationIndex.tDd], tdd)
        np.testing.assert_array_almost_equal(cali_array[:, CalibrationIndex.tDdd], tddd)
        np.testing.assert_array_almost_equal(cali_array[:, CalibrationIndex.CCSd], ccsd)
        np.testing.assert_array_almost_equal(cali_array[:, CalibrationIndex.lntDd], lntdd)
        np.testing.assert_array_almost_equal(cali_array[:, CalibrationIndex.lnCCSd], lnccsd)

    def test_ccs_export(self, get_origami_document):

        correction_factor = 1.57
        gas_mw = 28.00615
        array, tdd, tddd, ccsd, lntdd, lnccsd, x, x_ccs = _get_data()  # noqa

        ccs_proc = CCSCalibrationProcessor(dict(), dict())
        ccs_obj = ccs_proc.create_calibration(array, gas_mw=gas_mw, correction_factor=correction_factor)

        path = get_origami_document
        document = Environment().load(path)
        ccs_proc.export_calibration(document, "TEST_CALIBRATION")
        calibrations = document.get_ccs_calibration_list()
        assert len(calibrations) == 1
        with pytest.raises(ValueError):
            document.get_ccs_calibration("TEST_CALIBRATION")

        ccs_obj_doc = document.get_ccs_calibration(calibrations[0])
        assert isinstance(ccs_obj_doc, CCSCalibrationObject)

        np.testing.assert_array_almost_equal(ccs_obj.array, ccs_obj_doc.array)

    def test_ccs_obj(self):
        correction_factor = 1.57
        gas_mw = 28.00615
        array, tdd, tddd, ccsd, lntdd, lnccsd, x, x_ccs = _get_data()  # noqa

        ccs_proc = CCSCalibrationProcessor(dict(), dict())
        ccs_obj = ccs_proc.create_calibration(array, gas_mw=gas_mw, correction_factor=correction_factor)
        assert ccs_obj.x_label == "dt'"
        assert ccs_obj.y_label == "Ω'"
        ccs_obj.change_calibration("linear")
        assert ccs_obj.x_label == "dt'"
        assert ccs_obj.y_label == "Ω'"
        ccs_obj.change_calibration("log")
        assert ccs_obj.x_label == "ln(dt')"
        assert ccs_obj.y_label == "ln(Ω')"

        # apply calibration
        assert isinstance(ccs_obj, CCSCalibrationObject)
        cali_array = ccs_obj.array
        np.testing.assert_array_almost_equal(cali_array[:, CalibrationIndex.tDd], tdd)
        np.testing.assert_array_almost_equal(cali_array[:, CalibrationIndex.tDdd], tddd)
        np.testing.assert_array_almost_equal(cali_array[:, CalibrationIndex.CCSd], ccsd)
        np.testing.assert_array_almost_equal(cali_array[:, CalibrationIndex.lntDd], lntdd)
        np.testing.assert_array_almost_equal(cali_array[:, CalibrationIndex.lnCCSd], lnccsd)

        # test parameters
        assert ccs_obj.correction_factor == correction_factor
        assert ccs_obj.gas_mw == gas_mw

        # test exports
        data = ccs_obj.to_dict()
        assert isinstance(data, dict)
        assert "x" in data
        assert "y" in data
        assert "array" in data

        data, attrs = ccs_obj.to_zarr()
        assert isinstance(data, dict)
        assert isinstance(attrs, dict)
        assert "class" in attrs

        attrs = ccs_obj.to_attrs()
        assert isinstance(attrs, dict)
        assert "class" in attrs

        # convert array
        mz, charge = 5707, 18
        x_ccs_conv = ccs_obj(mz, charge, x)
        np.testing.assert_array_almost_equal(x_ccs, x_ccs_conv)

        # convert mobilogram
        dt_obj = MobilogramObject(x, np.zeros_like(x), x_label="Drift time (ms)")
        x_ccs_conv = ccs_obj(mz, charge, dt_obj)
        np.testing.assert_array_almost_equal(x_ccs, x_ccs_conv)

        # convert heatmap
        heatmap_obj = IonHeatmapObject(np.zeros((len(x), len(x))), np.zeros_like(x), x, y_label="Drift time (ms)")
        x_ccs_conv = ccs_obj(mz, charge, heatmap_obj)
        np.testing.assert_array_almost_equal(x_ccs, x_ccs_conv)

        # check parameters
        r2_lin = ccs_obj.r2_linear
        assert isinstance(r2_lin, float)
        r2_log = ccs_obj.r2_log
        assert isinstance(r2_log, float)

        slope, intercept, r2 = ccs_obj.fit_linear_slope
        assert isinstance(slope, float) and isinstance(intercept, float) and isinstance(r2, float)
        assert r2 == r2_lin
        label = ccs_obj.fit_linear_label
        assert isinstance(label, str)
        assert "y=" in label and "R" in label

        slope, intercept, r2 = ccs_obj.fit_log_slope
        assert isinstance(slope, float) and isinstance(intercept, float) and isinstance(r2, float)
        assert r2 == r2_log
        label = ccs_obj.fit_log_label
        assert isinstance(label, str)
        assert "y=" in label and "R" in label

    @pytest.mark.parametrize("delimiter", (",", "\t", " "))
    def test_ccs_obj_to_csv(self, tmpdir_factory, delimiter):
        correction_factor = 1.57
        gas_mw = 28.00615
        array, tdd, tddd, ccsd, lntdd, lnccsd, x, x_ccs = _get_data()  # noqa

        ccs_proc = CCSCalibrationProcessor(dict(), dict())
        ccs_obj = ccs_proc.create_calibration(array, gas_mw=gas_mw, correction_factor=correction_factor)

        path = str(tmpdir_factory.mktemp("output"))
        _path = ccs_obj.to_csv(os.path.join(path, "mass_spectrum"), delimiter=delimiter)
        data = np.loadtxt(_path, delimiter=delimiter)
        assert isinstance(data, np.ndarray)
        assert data.shape == ccs_obj.array.shape
