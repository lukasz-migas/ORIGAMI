"""Calibration container objects"""
# Standard library imports
import logging
from typing import Union

# Third-party imports
import numpy as np
from scipy.stats import linregress
from zarr.hierarchy import Array
from zarr.hierarchy import Group

# Local imports
from origami.objects.containers.base import DataObject
from origami.objects.containers.heatmap import IonHeatmapObject
from origami.objects.containers.spectrum import MobilogramObject
from origami.objects.containers.utilities import get_fmt
from origami.objects.containers.utilities import get_data

LOGGER = logging.getLogger(__name__)


class CalibrationIndex:
    """Index of which column corresponds to which attribute"""

    mz = 0
    mw = 1
    charge = 2
    tD = 3
    CCS = 4
    red_mass = 5
    tDd = 6
    CCSd = 7
    lntDd = 8
    lnCCSd = 9
    tDdd = 10
    N_COLUMNS = 11


CCS_TABLE_COLUMNS = ["m/z", "MW", "charge", "tD", "CCS", "red_mass", "tDd", "CCSd", "lntDd", "lnCCSd", "tDdd"]


class CCSCalibrationObject(DataObject):
    """CCS calibration object"""

    def __init__(
        self,
        array: np.ndarray,
        name: str = "CCSCalibration",
        x_label: str = "dt'",
        y_label: str = "Ω'",
        metadata=None,
        extra_data=None,
        **kwargs,
    ):
        self._array = array
        x = array[:, CalibrationIndex.tDd]
        y = array[:, CalibrationIndex.CCSd]

        super().__init__(
            name,
            x,
            y,
            x_label=x_label,
            y_label=y_label,
            x_label_options=["dt'", "ln(dt')"],
            y_label_options=["Ω'", "ln(Ω')"],
            metadata=metadata,
            extra_data=extra_data,
            **kwargs,
        )

    def change_calibration(self, fit: str):
        """Change fit to alternative view"""
        if fit.lower() == "linear":
            self._x = self.array[:, CalibrationIndex.tDd]
            self._y = self.array[:, CalibrationIndex.CCSd]
            self._x_label, self._y_label = "dt'", "Ω'"
        else:
            self._x = self.array[:, CalibrationIndex.lntDd]
            self._y = self.array[:, CalibrationIndex.lnCCSd]
            self._x_label, self._y_label = "ln(dt')", "ln(Ω')"

    @property
    def array(self):
        """Return calibration array"""
        if isinstance(self._array, Array):
            self._array = self._array[:]
        return self._array

    @property
    def fit_linear(self):
        """Linear fit"""
        return linregress(self.array[:, CalibrationIndex.tDd], self.array[:, CalibrationIndex.CCSd])

    @property
    def fit_linear_slope(self):
        """Return the slope and intercept of the linear fit"""
        fit = self.fit_linear
        return fit[0], fit[1], fit[2] ** 2

    @property
    def r2_linear(self):
        """Return r2 of the linear fit"""
        fit = self.fit_linear
        if fit:
            return fit[2] ** 2

    @property
    def fit_linear_label(self):
        """Return fit label"""
        slope, intercept, r2 = self.fit_linear_slope
        return f"y={slope:.4f}x + {intercept:.4f}\nR²={r2:.4f}"

    @property
    def fit_log(self):
        """Log fit"""
        return linregress(self.array[:, CalibrationIndex.lntDd], self.array[:, CalibrationIndex.lnCCSd])

    @property
    def fit_log_slope(self):
        """Return the slope and intercept of the log fit"""
        fit = self.fit_log
        return fit[0], fit[1], fit[2] ** 2

    @property
    def r2_log(self):
        """Return r2 of the log fit"""
        fit = self.fit_log
        if fit:
            return fit[2] ** 2

    @property
    def fit_log_label(self):
        """Return fit label"""
        slope, intercept, r2 = self.fit_log_slope
        return f"y={slope:.4f}x + {intercept:.4f}\nR²={r2:.4f}"

    @property
    def column_names(self):
        """Returns list of column names"""
        if "column_names" in self._metadata:
            return self._metadata["column_names"]
        return CCS_TABLE_COLUMNS

    @property
    def gas_mw(self):
        """Return the gas molecular weight"""
        return self._metadata["gas_mw"]

    @property
    def calibrants(self):
        """Returns all metadata and data about each of the calibrants used to create the calibration curve"""
        calibrants = self._metadata.get("calibrants")
        parent = self.get_parent()

        # load data
        if isinstance(calibrants, list) and parent:
            for calibrant in calibrants:
                name = calibrant["name"]
                calibrant["dt_obj"] = parent[f"{self.title}/{name}", True]

        return calibrants

    @property
    def correction_factor(self):
        """Return the correction factor"""
        return self._metadata["correction_factor"]

    def to_csv(self, path, *args, **kwargs):
        """Save data to csv file format"""
        array = self.array
        # get metadata
        delimiter = kwargs.get("delimiter", ",")

        fmt = get_fmt(array, get_largest=True)
        labels = self.column_names
        header = f"{delimiter}".join(labels)
        np.savetxt(path, array, delimiter=delimiter, fmt=fmt, header=header)  # noqa
        return path

    def __call__(
        self,
        mz: float,
        charge: int,
        dt: Union[MobilogramObject, IonHeatmapObject, np.ndarray],
        adduct_mw: float = 1.00783,
    ):
        """Convert ion mobility axis to collision cross sections using the existing calibration

        The conversion is carried out as follows:
        1. We calculate the corrected drift time using equation: tDd = X - (C * gasMW) * np.sqrt(m/z) / 1000
        2. We calculate the reduced mass using equation: red_mass = sqrt((mw * gasMW) / (mw + gasMW))
        3. We calculate the slope and intercept using linear fit (x=lntDd, y=lnCCSd) from the calibration fit
        4. We calculated new corrected  drift time using equation: tDdd = tDd^slope * charge * red_mass
        5. We calculate new slope and intercept using linear fit (x=tDdd, y=CCS)
        6. We finally calculate the CCS using equation: ccs = (tDdd * slope) + intercept

        Parameters
        ----------
        mz : float
            m/z value the ion was recorded at
        charge : float
            charge of the ion of interest
        dt : Union[MobilogramObject, IonHeatmapObject, np.ndarray]
            array of drift times that should be converted to CCS
        adduct_mw : float
            mass of the adduct that will be used to deduce the molecular weight

        Returns
        -------
        ccs : np.ndarray
            array of collision cross sections that was obtained from the drift times

        Notes
        -----
        See https://www.nature.com/articles/nprot.2008.78 for more details
        """
        # ensure time-axis is correct
        if isinstance(dt, MobilogramObject):
            dt.change_x_label("Drift time (ms)")
            x = dt.x
        elif isinstance(dt, IonHeatmapObject):
            dt.change_y_label("Drift time (ms)")
            x = dt.y
        else:
            x = dt

        # get fit parameters
        slope, _, _ = self.fit_log_slope

        # calculate molecular weight
        mw = (np.full_like(x, fill_value=mz) * charge) - (adduct_mw * charge)

        # calculate corrected drift time
        xd = x - (self.correction_factor * np.sqrt(mz) / 1000)

        # calculate reduced mass
        red_mass = np.sqrt((mw * self.gas_mw) / (mw + self.gas_mw))

        # calculate new corrected drift time
        xdd = np.power(xd, slope) * charge * red_mass

        # calculate the slope and intercept using the new corrected drift time and ccs
        fit = linregress(self.array[:, CalibrationIndex.tDdd], self.array[:, CalibrationIndex.CCS])
        slope, intercept = fit[0], fit[1]

        # calculate CCS
        ccs = (xdd * slope) + intercept

        return ccs

    def to_dict(self):
        """Export data in a dictionary format"""
        return {
            "x": self.x,
            "y": self.y,
            "array": self.array,
            "x_label": self.x_label,
            "y_label": self.y_label,
            **self._metadata,
            **self._extra_data,
        }

    def to_zarr(self):
        """Outputs data to dictionary of `data` and `attributes`"""
        data = {**self._extra_data, "x": self.x, "y": self.y, "array": self.array}
        attrs = {**self._metadata, "class": self._cls, "x_label": self.x_label, "y_label": self.y_label}
        return data, attrs

    def to_attrs(self):
        """Outputs attributes in a dictionary format"""
        return {**self._metadata, "class": self._cls, "x_label": self.x_label, "y_label": self.y_label}

    def check(self):
        """Checks whether the provided data has the same size and shape"""
        if len(self._array.shape) != 2:
            raise ValueError("`array` must have two dimensions")
        if not isinstance(self._metadata, dict):
            self._metadata = dict()


def ccs_calibration_object(group: Group, quick: bool) -> DataObject:
    """Instantiate CCS calibration group saved in zarr format"""
    metadata = group.attrs.asdict()
    obj = CCSCalibrationObject(*get_data(group, ["array"], quick), **group.attrs.asdict())
    obj.set_metadata(metadata)
    return obj
