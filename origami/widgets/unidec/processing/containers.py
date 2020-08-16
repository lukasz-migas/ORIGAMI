"""UniDec containers"""
# Standard library imports
import os

# Third-party imports
import numpy as np
from zarr import Group

# Local imports
from origami.objects.containers.heatmap import HeatmapObject
from origami.objects.containers.spectrum import SpectrumObject
from origami.objects.containers.spectrum import MassSpectrumObject
from origami.widgets.unidec.processing.config import UniDecConfig


class ChargeMassSpectrumHeatmap(HeatmapObject):
    """Ion heatmap data object"""

    DOCUMENT_KEY = ""

    def __init__(
        self,
        array,
        x,
        y,
        xy=None,
        yy=None,
        name: str = "",
        metadata=None,
        extra_data=None,
        x_label="m/z (Th)",
        y_label="Charge",
        **kwargs,
    ):
        super().__init__(
            array,
            name,
            x=x,
            y=y,
            xy=xy,
            yy=yy,
            x_label=x_label,
            y_label=y_label,
            x_label_options=["Charge"],
            y_label_options=["m/z (Th)", "m/z (Da)"],
            metadata=metadata,
            extra_data=extra_data,
            **kwargs,
        )


class ChargeMolecularWeightHeatmap(HeatmapObject):
    """Ion heatmap data object"""

    DOCUMENT_KEY = ""

    def __init__(
        self,
        array,
        x,
        y,
        xy=None,
        yy=None,
        name: str = "",
        metadata=None,
        extra_data=None,
        x_label="Mass (kDa)",
        y_label="Charge",
        **kwargs,
    ):
        super().__init__(
            array,
            name,
            x=x,
            y=y,
            xy=xy,
            yy=yy,
            x_label=x_label,
            y_label=y_label,
            x_label_options=["Charge"],
            y_label_options=["Mass (kDa)", "Molecular weight (kDa)", "MW (kDa)"],
            metadata=metadata,
            extra_data=extra_data,
            **kwargs,
        )


class MolecularWeightObject(SpectrumObject):
    """MW data object"""

    DOCUMENT_KEY = ""

    def __init__(
        self, x, y, name: str = "", metadata=None, extra_data=None, x_label="Mass (kDa)", y_label="Intensity", **kwargs
    ):
        """
        Additional data can be stored in the `extra_data` dictionary. The convention should be:
            data that is most commonly used/displayed should be stored under the x/y attributes
            alternative x-axis should be stored in the `extra_data` dict. If the extra data is
            scans, then store it under `x_bin` and if its in time/minutes, store it under `x_min`.

        Data keys:
            x : x-axis data most commonly used
            y : y-axis data most commonly used
            x_bin : x-axis data in scans/bins
            x_min : x-axis data in minutes/time
            """
        super().__init__(
            x,
            y,
            x_label=x_label,
            y_label=y_label,
            name=name,
            x_label_options=["Mass (kDa)", "Molecular weight (kDa)", "MW (kDa)"],
            metadata=metadata,
            extra_data=extra_data,
            **kwargs,
        )


class UniDecResultsObject:
    """Data container for UniDec results"""

    def __init__(self, mz_obj: MassSpectrumObject, config: UniDecConfig):
        self._cls = self.__class__.__name__

        # settable attributes
        self.config = config
        self.peaks = None
        self.charge_peaks = None

        # data
        self.mz_obj = mz_obj
        self.mz_raw = mz_obj.xy

        # after run results
        self.mz_processed = None
        self.mw_raw = None
        self.charges = None
        self.mw_grid = None
        self.fit_raw = None
        self.baseline = None
        self.mz_grid = None
        self.error = None

    def __repr__(self):
        """Pretty formatting of the class repr"""
        return f"{self.__class__.__name__}<processed={self.is_processed}; executed={self.is_executed}>"

    @property
    def is_processed(self):
        """Flag to indicate whether data has been pre-processed"""
        return self.mz_processed is not None

    @property
    def is_executed(self):
        """Flag to indicated whether UniDec has been executed"""
        return self.mz_grid is not None

    @property
    def mw_max(self):
        """Return the maximum value in the MW data"""
        if self.mw_raw:
            return np.amax(self.mw_raw[:, 1])
        return None

    def to_zarr(self):
        """Outputs data to dictionary composed of `data` and `attributes`"""
        # export data
        data = dict()
        for key, _data in (
            ["mz_processed", self.mz_processed],
            ["mw_raw", self.mw_raw],
            ["mw_grid", self.mw_grid],
            ["fit_raw", self.fit_raw],
            ["baseline", self.baseline],
            ["mz_grid", self.mz_grid],
            ["error", self.error],
            ["charges", self.charges],
        ):
            if isinstance(_data, np.ndarray):
                data[key] = _data
        # export attributes
        # TODO: also need to export peaks and charge peaks
        attributes = {"class": self._cls, "config": self.config.to_dict()}

        return data, attributes

    def export(self, path: str, data: np.ndarray):
        """Export data to appropriate location"""
        if data is None:
            data = self.mz_raw
        np.savetxt(path, data, fmt="%f")  # noqa

    def import_data(self, efficiency: bool = False):
        """Import results from binary/text files written by UniDec dll"""

        # check whether run was successful
        if os.path.isfile(self.config.out_mw_filename):
            self.mw_raw = np.loadtxt(self.config.out_mw_filename)
        else:
            raise ValueError("Could not load MW from file")

        self.charges = np.arange(self.config.startz, self.config.endz + 1)

        if not efficiency:
            if os.path.isfile(self.config.out_mw_grid_filename):
                self.mw_grid = np.fromfile(self.config.out_mw_grid_filename, dtype=float)

            if os.path.isfile(self.config.out_fit_filename):
                self.fit_raw = np.fromfile(self.config.out_fit_filename, dtype=float)
            try:
                if self.config.aggressiveflag != 0:
                    if os.path.isfile(self.config.out_baseline_filename):
                        self.baseline = np.fromfile(self.config.out_baseline_filename, dtype=float)
                else:
                    self.baseline = np.array([])
            except Exception as err:
                self.baseline = np.array([])
                print(err)

        errors = None
        if os.path.isfile(self.config.out_error_filename):
            errors = np.genfromtxt(self.config.out_error_filename, dtype="str")
        if self.config.imflag == 0 and errors is not None:
            # Calculate Error
            sse = float(errors[0, 2])
            mean = np.mean(self.mz_processed[:, 1])
            self.config.error = 1 - sse / np.sum((self.mz_processed[:, 1] - mean) ** 2)
            if not efficiency:
                # Import Grid
                if os.path.isfile(self.config.out_mz_grid_filename):
                    mz_grid = np.fromfile(self.config.out_mz_grid_filename, dtype=float)
                    xv, yv = np.meshgrid(self.charges, self.mz_processed[:, 0])
                    xv = np.c_[np.ravel(yv), np.ravel(xv)]
                    self.mz_grid = np.c_[xv, mz_grid]

    @property
    def mz_grid_2d(self):
        """Return the `mz_grid` as two-dimensional array"""
        x = np.unique(self.mz_grid[:, 0])
        y = np.unique(self.mz_grid[:, 1])
        z = self.mz_grid[:, 2]
        return x, y, self._reshape_grid(x, y, z).T

    @property
    def mz_grid_obj(self):
        """Return the `mz_grid` as ORIGAMI object"""
        x, y, array = self.mz_grid_2d
        return ChargeMassSpectrumHeatmap(array, x, y)

    @property
    def mw_grid_2d(self):
        """Return the `mw_grid` as two-dimensional array"""
        x = self.mw_raw[:, 0]
        y = self.charges
        z = self.mw_grid
        return x, y, self._reshape_grid(x, y, z).T

    @property
    def mw_grid_obj(self):
        """Return the `mw_grid` as ORIGAMI object"""
        x, y, array = self.mw_grid_2d
        return ChargeMolecularWeightHeatmap(array, x, y)

    @property
    def mw_obj(self):
        """Return the `mw_raw` as ORIGAMI object"""
        return MolecularWeightObject(self.mw_raw[:, 0], self.mw_raw[:, 1])

    @property
    def mz_raw_obj(self):
        """Return the `mz_raw` as ORIGAMI object"""
        return self.mz_obj

    @property
    def mz_processed_obj(self):
        """Return the `mz_processed` as ORIGAMI object"""
        return MassSpectrumObject(self.mz_processed[:, 0], self.mz_processed[:, 1])

    @staticmethod
    def _reshape_grid(x, y, z):
        """Reshape array"""
        x_len = len(x)
        y_len = len(y)
        array = np.reshape(z, (x_len, y_len))
        return array


def unidec_results_object(mz_obj: MassSpectrumObject, group: Group) -> UniDecResultsObject:
    """Instantiate UniDec results group"""
    metadata = group.attrs.asdict()
    config = UniDecConfig()
    config.from_dict(metadata.get("config", dict()))

    # instantiate object
    obj = UniDecResultsObject(mz_obj, config)

    # set data
    if group.get("mz_processed", None):
        obj.mz_processed = group["mz_processed"][:]
    if group.get("mw_raw", None):
        obj.mw_raw = group["mw_raw"][:]
    if group.get("charges", None):
        obj.charges = group["charges"][:]
    if group.get("mw_grid", None):
        obj.mw_grid = group["mw_grid"][:]
    if group.get("fit_raw", None):
        obj.fit_raw = group["fit_raw"][:]
    if group.get("baseline", None):
        obj.baseline = group["baseline"][:]
    if group.get("mz_grid", None):
        obj.mz_grid = group["mz_grid"][:]
    if group.get("error", None):
        obj.error = group["error"][:]

    return obj
