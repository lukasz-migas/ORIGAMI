"""Calibration container objects"""
# Third-party imports
import numpy as np
from scipy.stats import linregress
from zarr.hierarchy import Group

# Local imports
from origami.objects.containers import DataObject
from origami.objects.containers.utilities import get_fmt


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

    @property
    def array(self):
        """Return calibration array"""
        return self._array

    @property
    def r2_linear(self):
        """Return r2 of the linear fit"""
        fit = self.fit_linear
        if fit:
            return fit[2] ** 2

    @property
    def r2_log(self):
        """Return r2 of the log fit"""
        fit = self.fit_log
        if fit:
            return fit[2] ** 2

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
    def fit_log(self):
        """Log fit"""
        return linregress(self.array[:, CalibrationIndex.lntDd], self.array[:, CalibrationIndex.lnCCSd])

    @property
    def fit_log_slope(self):
        """Return the slope and intercept of the log fit"""
        fit = self.fit_log
        return fit[0], fit[1], fit[2] ** 2

    @property
    def column_names(self):
        """Returns list of column names"""
        if "column_names" in self._metadata:
            return self._metadata["column_names"]
        return CCS_TABLE_COLUMNS

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

    def to_csv(self, path, *args, **kwargs):
        """Save data to csv file format"""
        array = self.array
        # get metadata
        delimiter = kwargs.get("delimiter", ",")

        fmt = get_fmt(array, get_largest=True)
        labels = self.column_names
        header = f"{delimiter}".join(labels)
        np.savetxt(path, array, delimiter=delimiter, fmt=fmt, header=header)  # noqa

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

    def check(self):
        """Checks whether the provided data has the same size and shape"""
        if len(self._array.shape) != 2:
            raise ValueError("`array` must have two dimensions")
        if not isinstance(self._metadata, dict):
            self._metadata = dict()


def ccs_calibration_object(group: Group) -> DataObject:
    """Instantiate CCS calibration group saved in zarr format"""
    metadata = group.attrs.asdict()
    obj = CCSCalibrationObject(group["array"][:], **group.attrs.asdict())
    obj.set_metadata(metadata)
    return obj
