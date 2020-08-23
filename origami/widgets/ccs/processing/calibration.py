"""Class for performing CCS calibration"""
# Standard library imports
import logging

# Third-party imports
import numpy as np
from scipy.stats import linregress

# Local imports
from origami.objects.document import DocumentStore
from origami.widgets.ccs.processing.containers import CCS_TABLE_COLUMNS
from origami.widgets.ccs.processing.containers import CalibrationIndex
from origami.widgets.ccs.processing.containers import CCSCalibrationObject

LOGGER = logging.getLogger(__name__)


class CCSCalibrationProcessor:
    """CCS calibration processor"""

    def __init__(self, metadata, extra_data):
        self.metadata = metadata
        self.extra_data = extra_data

        self._calibration = None
        self._fit_linear = None
        self._fit_log = None
        self._ccs_obj = None
        self._fitted = False

    @property
    def calibration(self):
        """Return calibration array"""
        return self._calibration

    @property
    def r2_linear(self):
        """Return r2 of the linear fit"""
        if self._fit_linear:
            return self._fit_linear[2] ** 2

    @property
    def r2_log(self):
        """Return r2 of the log fit"""
        if self._fit_log:
            return self._fit_log[2] ** 2

    @property
    def fit_linear(self):
        """Linear fit"""
        if self._fit_linear is None and self._calibration is not None:
            return linregress(self._calibration[:, CalibrationIndex.tDd], self._calibration[:, CalibrationIndex.CCSd])
        return self._fit_linear

    @property
    def fit_log(self):
        """Log fit"""
        if self._fit_log is None and self._calibration is not None:
            return linregress(
                self._calibration[:, CalibrationIndex.lntDd], self._calibration[:, CalibrationIndex.lnCCSd]
            )
        return self._fit_log

    @property
    def ccs_obj(self):
        """Return r2 of the log fit"""
        if self._ccs_obj is None and self.calibration is not None:
            self._ccs_obj = CCSCalibrationObject(
                self.calibration, metadata={"calibrants": self.metadata, "column_names": CCS_TABLE_COLUMNS}
            )
        return self._ccs_obj

    @staticmethod
    def prepare_array(mz: np.ndarray, mw: np.ndarray, charge: np.ndarray, dt: np.ndarray, ccs: np.ndarray):
        """Prepare input arrays for CCS calibration"""
        if len(mz) != len(mw) != len(charge) != len(dt) != len(ccs):
            raise ValueError("Input arrays must be of the same length")

        array = np.zeros((len(mz), 5), dtype=np.float64)
        array[:, CalibrationIndex.mz] = mz
        array[:, CalibrationIndex.mw] = mw
        array[:, CalibrationIndex.charge] = charge
        array[:, CalibrationIndex.tD] = dt
        array[:, CalibrationIndex.CCS] = ccs
        return array

    def create_calibration(self, array: np.ndarray, gas_mw: float, correction_factor: float):
        """Create CCS calibration curve"""
        if not array.shape[1] == 5:
            raise ValueError("The input array should contain 5 columns corresponding to `m/z, mw, charge, tD, ccs`")

        calc_array = np.zeros((array.shape[0], 11), dtype=np.float64)
        calc_array[:, 0:5] = array

        # calculate reduced mass
        calc_array[:, CalibrationIndex.red_mass] = (calc_array[:, CalibrationIndex.mw] * gas_mw) / (
            calc_array[:, CalibrationIndex.mw] + gas_mw
        )

        # calculate corrected drift time
        calc_array[:, CalibrationIndex.tDd] = calc_array[:, CalibrationIndex.tD] - (
            0.001 * correction_factor * np.sqrt(calc_array[:, CalibrationIndex.mz])
        )

        # calculate corrected ccs
        calc_array[:, CalibrationIndex.CCSd] = calc_array[:, CalibrationIndex.CCS] / (
            (calc_array[:, CalibrationIndex.charge] * np.sqrt(1 / calc_array[:, CalibrationIndex.red_mass]))
        )

        # apply log transform on corrected tD
        calc_array[:, CalibrationIndex.lntDd] = np.log(calc_array[:, CalibrationIndex.tDd])

        # apply log on corrected CCS
        calc_array[:, CalibrationIndex.lnCCSd] = np.log(calc_array[:, CalibrationIndex.CCSd])

        # compute linear regression
        fit_linear = linregress(calc_array[:, CalibrationIndex.tDd], calc_array[:, CalibrationIndex.CCSd])

        # compute power regression
        fit_log = linregress(calc_array[:, CalibrationIndex.lntDd], calc_array[:, CalibrationIndex.lnCCSd])

        # calculate the tDdd
        calc_array[:, CalibrationIndex.tDdd] = (
            np.power(calc_array[:, CalibrationIndex.tDd], fit_log[0])
            * calc_array[:, CalibrationIndex.charge]
            * np.sqrt(calc_array[:, CalibrationIndex.red_mass])
        )

        self._calibration = calc_array
        self._fit_linear = fit_linear
        self._fit_log = fit_log
        self._fitted = True
        return self.ccs_obj

    def export_calibration(self, document: DocumentStore, name: str):
        """Export CCS calibration to the metadata store"""
        # get calibration data
        if not self._fitted:
            raise ValueError("Cannot export data since CCS calibration has not been fitted yet")

        ccs_obj = self.ccs_obj
        extra_data = self.extra_data

        if not isinstance(ccs_obj, CCSCalibrationObject):
            raise ValueError("Calibration array should be a `CCSCalibrationObject`")
        if not isinstance(document, DocumentStore):
            raise ValueError("Cannot export calibration data because the document is not present.")

        ccs_obj = document.add_ccs_calibration(name, ccs_obj)

        # export extra data
        if isinstance(extra_data, dict):
            for title, data_obj in extra_data.items():
                ccs_obj.add_group(title, *data_obj.to_zarr())

        LOGGER.debug(f"Added calibration={name} to {document.title}")
