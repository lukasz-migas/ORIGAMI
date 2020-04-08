# Standard library imports
from typing import List
from typing import Optional

# Third-party imports
import numpy as np
from scipy.interpolate import interpolate

# Local imports
import origami.readers.waters.MassLynxRawReader as MassLynxRawReader
import origami.readers.waters.MassLynxRawInfoReader as MassLynxRawInfoReader
import origami.readers.waters.MassLynxRawScanReader as MassLynxRawScanReader
import origami.readers.waters.MassLynxRawChromatogramReader as MassLynxRawChromatogramReader
from origami.utils.ranges import get_min_max


class WatersRawReader:
    def __init__(self, path, mz_spacing: float = 0.01):
        self.path = path

        # create parsers
        self.reader, self.info_reader, self.data_reader, self.chrom_reader = self.create_readers()

        # get parameters
        self.stats_in_functions, self._n_functions, self.mz_min, self.mz_max, self.mz_range = (
            self.get_functions_and_stats()
        )
        self._mz_spacing = mz_spacing
        self._mz_x = self.get_linear_mz(self._mz_spacing)
        self._rt_min = None
        self._dt_ms = None

        # setup file mode
        self.instrument_type = self.stats_in_functions[0]["ion_mode"]

    def __repr__(self):
        return f"{self.__class__.__name__}<path={self.path}; m/z range={self.mz_min:.2f}-{self.mz_max:.2f}>"

    @property
    def n_functions(self):
        return self._n_functions

    @property
    def mz_x(self):
        if self._mz_x is None:
            self._mz_x = self.get_linear_mz(self._mz_spacing)
        return self._mz_x

    @mz_x.setter
    def mz_x(self, value):
        """Sets the m/z axis"""
        self._mz_x = np.asarray(value)

    @property
    def dt_bin(self):
        """Return mobility axis in bins"""
        return np.arange(self.n_scans(1), dtype=np.int32) + 1

    @property
    def dt_ms(self):
        """Return mobility axis in milliseconds"""
        if self._dt_ms is None:
            self._dt_ms, _ = self.get_tic(1)
        return self._dt_ms

    @property
    def rt_bin(self):
        """Return chromatogram axis in bins"""
        return np.arange(self.n_scans(0), dtype=np.int32) + 1

    @property
    def rt_min(self):
        if self._rt_min is None:
            self._rt_min, _ = self.get_tic(0)
        return self._rt_min

    def n_scans(self, fcn: int):
        """Get number of scans in particular function"""
        return self.stats_in_functions[fcn]["n_scans"]

    def create_readers(self):
        """Creates various readers used for data extraction"""
        reader = MassLynxRawReader.MassLynxRawReader(self.path, 1)
        info_reader = MassLynxRawInfoReader.MassLynxRawInfoReader(reader)
        data_reader = MassLynxRawScanReader.MassLynxRawScanReader(reader)
        chrom_reader = MassLynxRawChromatogramReader.MassLynxRawChromatogramReader(reader)

        return reader, info_reader, data_reader, chrom_reader

    def get_functions_and_stats(self):
        """Collects basic information about the file"""
        n_functions = self.info_reader.GetNumberofFunctions()

        stats_in_functions = {}
        mass_range = []
        for fcn in range(n_functions):
            scans = self.info_reader.GetScansInFunction(fcn)
            _mass_range = self.info_reader.GetAcquisitionMassRange(fcn)
            ion_mode = self.info_reader.GetIonModeString(self.info_reader.GetIonMode(fcn))
            fcn_type = self.info_reader.GetFunctionTypeString(self.info_reader.GetFunctionType(fcn))

            stats_in_functions[fcn] = {
                "n_scans": scans,
                "mass_range": _mass_range,
                "ion_mode": ion_mode,
                "fcn_type": fcn_type,
            }
            mass_range.extend(_mass_range)

        return stats_in_functions, n_functions, min(mass_range), max(mass_range), mass_range

    def get_inf_data(self):
        """Read metadata data"""
        from origami.readers.io_utils import get_waters_inf_data

        return get_waters_inf_data(self.path)

    def check_fcn(self, fcn):
        """Checks whether the requested function exists"""
        if fcn not in self.stats_in_functions:
            raise ValueError(f"Function {fcn} not found in the file. Try: {list(self.stats_in_functions.keys())}")

    def get_linear_mz(self, mz_spacing: float):
        """Generates linearly spaced interpolation range"""
        x = np.arange(self.mz_min, self.mz_max, mz_spacing)
        return x

    def get_average_spectrum(self, fcn: int = 0):
        """Load average spectrum"""
        x, y = self.get_spectrum(fcn=fcn)
        y = y / self.n_scans(fcn)
        return x, y

    def _get_spectrum(self, fcn, scan_id):
        """Retrieve scan"""
        return self.data_reader.ReadScan(fcn, scan_id)

    def _process_spectrum(self, x, y):
        # TODO: add qualitative check to see if the distance between two adjacent (sorted) x-axis elements is not larger
        #       than some value (e.g. 0.1) and if so, insert two values right next to it with intensity of 0 so the
        #       interpolation does not try to do crazy things
        """Processes accumulated mass spectrum

        Notes
        -----
        1. The final mass spectrum is generated by reordering the accumulated mass and intensity values (according to
        the mass axis) and subsequently summed together for the unique values of the mass axis. Once the summation is
        done, interpolated mass spectrum is generated.
        2. If the amount of data in x/y is low, the spectrum can have visual issues, especially if the values are far
        apart.

        Parameters
        ----------
        x : List
            unsorted list of x-axis values
        y : List
            unsorted list of y-axis values

        Returns
        -------
        y : np.ndarray
            interpolated y-axis values
        """
        # convert lists to array
        x = np.asarray(x)
        y = np.asarray(y)

        if len(x) == 0:
            return np.zeros_like(self.mz_x, dtype=np.float32)

        # retrieve index
        idx = x.argsort()
        x = x[idx]
        y = y[idx]

        # combine data
        x_unique, x_idx = np.unique(x, return_index=True)

        # reindex y-axis and combine same values
        start_idx = 0
        y_summed = np.zeros_like(x_unique)
        for i, end_idx in enumerate(x_idx[1::]):
            y_summed[i] = y[start_idx:end_idx].sum()
            start_idx = end_idx

        # generate interpolation function
        f = interpolate.interp1d(x_unique, y_summed, "linear", bounds_error=False, fill_value=0)
        return f(self.mz_x).astype(np.float32)

    def _get_scan_list(self, start_scan, end_scan, scan_list, fcn):
        """Process user-defined parameters and return iterable object of scans or drift scans"""
        if scan_list is None:
            if not start_scan:
                start_scan = 0
            if not end_scan:
                end_scan = self.n_scans(fcn)
            scan_list = range(start_scan, end_scan)
        return scan_list

    def get_spectrum(
        self,
        start_scan: Optional[int] = None,
        end_scan: Optional[int] = None,
        scan_list: Optional[List[int]] = None,
        fcn: int = 0,
    ):
        """Retrieve mass spectrum

        Parameters
        ----------
        start_scan : int
            start scan of the data extraction
        end_scan : int
            end scan of the data extraction
        scan_list : list
            list of scans to extract. If `scan_list` is provided, the `start_scan` and `end_scan` variables are ignored
        fcn : int
            function to extract data from

        Returns
        -------
        x : np.ndarray
            x-axis of the mass spectrum
        y : np.ndarray
            y-axis of the mass spectrum
        """
        self.check_fcn(fcn)
        scan_list = self._get_scan_list(start_scan, end_scan, scan_list, fcn)

        x, y = [], []
        for scan_id in scan_list:
            _x, _y = self.data_reader.ReadScan(fcn, scan_id)
            x.extend(_x)
            y.extend(_y)

        return self.mz_x, self._process_spectrum(x, y)

    def get_drift_spectrum(
        self,
        start_scan: Optional[int] = None,
        end_scan: Optional[int] = None,
        scan_list: Optional[List[int]] = None,
        start_drift: Optional[int] = None,
        end_drift: Optional[int] = None,
        drift_list: Optional[List[int]] = None,
        fcn: int = 0,
    ):
        """Retrieve mass spectrum

        Parameters
        ----------
        start_scan : int
            start scan of the data extraction
        end_scan : int
            end scan of the data extraction
        scan_list : list
            list of scans to extract. If `scan_list` is provided, the `start_scan` and `end_scan` variables are ignored
        start_drift : int
            start drift scan of the data extraction
        end_drift : int
            end drift scan of the data extraction
        drift_list : list
            list of drift scans to extract. If `drift_list` is provided, the `drift_start` and `drift_end` variables are
            ignored
        fcn : int
            function to extract data from

        Returns
        -------
        x : np.ndarray
            x-axis of the mass spectrum
        y : np.ndarray
            y-axis of the mass spectrum
        """
        self.check_fcn(fcn)
        scan_list = self._get_scan_list(start_scan, end_scan, scan_list, fcn)
        drift_list = self._get_scan_list(start_drift, end_drift, drift_list, 1)
        # use the `ReadScan` method instead since ion mobility criteria are not used
        if len(drift_list) == 200:
            return self.get_spectrum(scan_list=scan_list, fcn=fcn)

        x, y = [], []
        for scan_id in scan_list:
            for drift_id in drift_list:
                _x, _y = self.data_reader.ReadDriftScan(fcn, scan_id, drift_id)
                x.extend(_x)
                y.extend(_y)
        return self.mz_x, self._process_spectrum(x, y)

    def get_tic(self, fcn: int = 0):
        """Retrieve TIC data for particular function

        Parameters
        ----------
        fcn : int
            function id

        Returns
        -------
        x : np.ndarray
            x-axis of the TIC data
        y : np.ndarray
            y-axis of the TIC data
        """
        self.check_fcn(fcn)
        x, y = self.chrom_reader.ReadTIC(fcn)
        return np.asarray(x), np.asarray(y)

    def get_bpi(self, fcn: int = 0):
        """Retrieve BPI data for particular function

        Parameters
        ----------
        fcn : int
            function id

        Returns
        -------
        x : np.ndarray
            x-axis of the TIC data
        y : np.ndarray
            y-axis of the TIC data
        """
        self.check_fcn(fcn)
        x, y = self.chrom_reader.ReadBPI(fcn)
        return np.asarray(x), np.asarray(y)

    def get_chromatogram(self, mz_values, tolerance=0.05):
        """Get chromatograms for particular masses within m/z tolerance window

        Parameters
        ----------
        mz_values : Union[float, List[float]]
            single m/z value or list of m/z vales
        tolerance : float
            tolerance window

        Returns
        -------
        x : np.ndarray
            x-axis of the chromatogram
        ys : List[np.ndarray]
            list of y-axes values
        """
        return self._get_mass_chromatogram(0, mz_values, tolerance)

    def get_mobilogram(self, mz_values, tolerance=0.05):
        """Get mobilogram for particular masses within m/z tolerance window

        Parameters
        ----------
        mz_values : Union[float, List[float]]
            single m/z value or list of m/z vales
        tolerance : float
            tolerance window

        Returns
        -------
        x : np.ndarray
            x-axis of the chromatogram
        ys : List[np.ndarray]
            list of y-axes values
        """
        return self._get_mass_chromatogram(1, mz_values, tolerance)

    def _get_mass_chromatogram(self, fcn, mz_values, tolerance=0.05):
        """Get chromatogram/mobilogram for particular masses within m/z tolerance window

        Parameters
        ----------
        fcn : int
            function id
        mz_values : Union[float, List[float]]
            single m/z value or list of m/z vales
        tolerance : float
            tolerance window

        Returns
        -------
        x : np.ndarray
            x-axis of the chromatogram
        ys : List[np.ndarray]
            list of y-axes values
        """
        self.check_fcn(fcn)
        if isinstance(mz_values, (float, int)):
            mz_values = [mz_values]
        if isinstance(mz_values, tuple):
            mz_values = list(mz_values)
        if not isinstance(tolerance, float) or tolerance <= 0:
            raise ValueError("m/z tolerance must be larger than 0")

        x, ys = self.chrom_reader.ReadMassChromatograms(fcn, mz_values, tolerance, 0)
        assert isinstance(ys, list)

        return np.asarray(x), [np.asarray(y) for y in ys]

    @staticmethod
    def _check_waters_input(reader, mz_start, mz_end, rt_start, rt_end, dt_start, dt_end):
        """Check input for waters files"""
        # check mass range
        mass_range = reader.stats_in_functions.get(0, 1)["mass_range"]
        if mz_start < mass_range[0]:
            mz_start = mass_range[0]
        if mz_end > mass_range[1]:
            mz_end = mass_range[1]

        # check chromatographic range
        xvals, __ = reader.get_tic(0)
        rt_range = get_min_max(xvals)
        if rt_start < rt_range[0]:
            rt_start = rt_range[0]
        if rt_start > rt_range[1]:
            rt_start = rt_range[1]
        if rt_end > rt_range[1]:
            rt_end = rt_range[1]

        # check mobility range
        dt_range = [0, 199]
        if dt_start < dt_range[0]:
            dt_start = dt_range[0]
        if dt_start > dt_range[1]:
            dt_start = dt_range[1]
        if dt_end > dt_range[1]:
            dt_end = dt_range[1]

        return mz_start, mz_end, rt_start, rt_end, dt_start, dt_end
