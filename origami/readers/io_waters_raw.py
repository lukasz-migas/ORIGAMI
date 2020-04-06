# Standard library imports
import logging
import os.path
from subprocess import CREATE_NEW_CONSOLE
from subprocess import Popen

# Third-party imports
import numpy as np

# Local imports
from origami.utils.path import check_waters_path
from origami.utils.secret import get_short_hash
from origami.readers.io_utils import clean_up
from origami.processing.heatmap import normalize_2D
from origami.readers.io_waters_raw_api import WatersRawReader

logger = logging.getLogger(__name__)

# create data holder
temp_data_folder = os.path.join(os.getcwd(), "temporary_data")


class WatersIMReader:
    def __init__(self, path, driftscope_path=r"C:\DriftScope\lib", temp_dir=None):
        self.path = check_waters_path(path)
        self._driftscope = driftscope_path
        self._temp_dir = temp_dir if temp_dir is not None else self.path
        self.output_dir = self._temp_dir
        self.verbose = True
        self._last = None
        self._rt_min = None
        self._dt_ms = None

        self.mz_min, self.mz_max, self.n_scans = self.get_mass_range()

    def __repr__(self):
        return f"{self.__class__.__name__}<path={self.path}; m/z range={self.mz_min:.2f}-{self.mz_max:.2f}>"

    @property
    def dt_bin(self):
        """Return mobility axis in bins"""
        return np.arange(200, dtype=np.int32) + 1

    @property
    def dt_ms(self):
        """Return mobility axis in milliseconds"""
        if self._dt_ms is None:
            reader = WatersRawReader(self.path)
            self._dt_ms, _ = reader.get_tic(1)
        return self._dt_ms

    @property
    def rt_bin(self):
        """Return chromatogram axis in bins"""
        return np.arange(self.n_scans, dtype=np.int32) + 1

    @property
    def rt_min(self):
        if self._rt_min is None:
            reader = WatersRawReader(self.path)
            self._rt_min, _ = reader.get_tic(0)
            # self._rt_min, _, _, _ = self.extract_rt(dt_start=0, dt_end=1)
        return self._rt_min

    def get_mass_range(self):
        """Create handle to the API reader and extract the experimental mass range"""
        reader = WatersRawReader(self.path)
        stats = reader.stats_in_functions
        # if len(stats) < 2:
        #     raise ValueError("This Waters (.raw) file only has 1 function! Cannot extract ion mobility data")
        mz_min, mz_max = stats[0]["mass_range"]
        return mz_min, mz_max, stats[0]["n_scans"]

    def check_mz_range(self, mz_start, mz_end):
        """Ensure the user-defined mass-range makes sense"""
        if mz_start < self.mz_min:
            mz_start = self.mz_min
        if mz_end > self.mz_max:
            mz_end = self.mz_max

        return mz_start, mz_end

    def get_temp_filename(self):
        """Creates temporary filename"""
        filename = get_short_hash()
        self._last = filename
        return filename

    def execute(self, cmd):
        """Executes the extraction command"""
        process_id = Popen(cmd, shell=self.verbose, creationflags=CREATE_NEW_CONSOLE)
        process_id.wait()

    def get_filepath(self, filename):
        """Combines output directory with new filename"""
        return os.path.join(self.output_dir, filename)

    @staticmethod
    def mz_from_n_bins(mz_start: float, mz_end: float, n_mz_bins: int):
        """Return approximate m/z axis based on number of bins and specified mass range. The mass axis is calculated
        using simple linear spacing

        Parameters
        ----------
        mz_start : float
            start m/z value - ensure the m/z bin size was subtracted from this value
        mz_end : float
            end m/z value - ensure the m/z bin size was added to this value
        n_mz_bins : int
            number of m/z points

        Returns
        -------
        x : np.ndarray
            linearly spaced m/z axis with constant bin size
        """
        return np.linspace(mz_start, mz_end, n_mz_bins, endpoint=True)

    @staticmethod
    def clean(path):
        # clean-up filepath
        try:
            clean_up(path)
        except Exception as e:
            logger.warning("Failed to delete file. Error: {}".format(e))

    def extract_ms(
        self,
        n_bins: int = 10000,
        rt_start: float = 0,
        rt_end: float = 99999.0,
        dt_start: int = 1,
        dt_end: int = 200,
        mz_start: float = 0,
        mz_end: float = 99999,
        return_data=True,
        **kwargs,
    ):
        """Extract mass spectrum from ion mobility dataset

        Parameters
        ----------
        n_bins : int
            number of mass bins
        rt_start : float
            start retention time, in minutes
        rt_end : float
            end retention time, in minutes
        dt_start : int
            start drift time, in drift bins
        dt_end : int
            end drift time, in drift bins
        mz_start : float
            start m/z extraction range, in Da
        mz_end : float
            end m/z extraction range, in Da
        return_data : bool
            if `True`, extracted data will be loaded and returned

        Returns
        -------
        x : np.ndarray
            m/z values
        y : np.ndarray
            intensity values
        y_norm : np.ndarray
            normalized (to 1) intensity values
        """
        # write output filename first
        filename = self.get_temp_filename()
        range_file = self.get_filepath(filename + ".in")
        with open(range_file, "w") as f_ptr:
            f_ptr.write(f"{mz_start} {mz_end} {n_bins}\n{rt_start} {rt_end} 1\n{dt_start} {dt_end} 1")

        # create command
        out_path = self.get_filepath(filename + ".1dMZ")
        cmd = rf'{self._driftscope}\imextract.exe -d "{self.path}" -f 1 -o "{out_path}" -t mobilicube -p "{range_file}'

        # Extract command
        self.execute(cmd)
        self.clean(range_file)

        if return_data:
            x, y, y_norm = self.load_ms(out_path, normalize=kwargs.get("normalize", False))
            return x, y, y_norm
        return out_path

    def load_ms(self, path, normalize=False):
        """Load binary data extracted using `extract_ms`

        Parameters
        ----------
        path : str
            path to the binary MS data
        normalize : bool
            if `True`, a normalized spectrum will be also generated

        Returns
        -------
        x : np.ndarray
            m/z values
        y : np.ndarray
            intensity values
        y_norm : np.ndarray
            normalized (to 1) intensity values
        """
        # load data
        data = np.fromfile(path, dtype=np.float32)
        n_rows = int(data[3::].shape[0] / 2)
        xy = data[3::].reshape(2, n_rows, order="F")
        x = xy[0, :]
        y = xy[1, :] / data[2]

        self.clean(path)
        # normalize mass spectrum to 1
        y_norm = y
        if normalize:
            y_norm = y / y.max()

        return x, y, y_norm

    def extract_rt(
        self,
        rt_start: float = 0,
        rt_end: float = 99999.0,
        dt_start: int = 1,
        dt_end: int = 200,
        mz_start: float = 0,
        mz_end: float = 99999,
        return_data=True,
        **kwargs,
    ):
        """Extract chromatogram from ion mobility dataset

        Parameters
        ----------
        rt_start : float
            start retention time, in minutes
        rt_end : float
            end retention time, in minutes
        dt_start : int
            start drift time, in drift bins
        dt_end : int
            end drift time, in drift bins
        mz_start : float
            start m/z extraction range, in Da
        mz_end : float
            end m/z extraction range, in Da
        return_data : bool
            if `True`, extracted data will be loaded and returned

        Returns
        -------
        x : np.ndarray
            m/z values
        y : np.ndarray
            intensity values
        y_norm : np.ndarray
            normalized (to 1) intensity values
        """
        mz_start, mz_end = self.check_mz_range(mz_start, mz_end)

        # write output filename first
        filename = self.get_temp_filename()
        range_file = self.get_filepath(filename + ".in")
        with open(range_file, "w") as f_ptr:
            f_ptr.write(f"{mz_start} {mz_end} 1\n{rt_start} {rt_end} 5000\n{dt_start} {dt_end} 1")

        # create command
        out_path = self.get_filepath(filename + ".1dRT")
        cmd = rf'{self._driftscope}\imextract.exe -d "{self.path}" -f 1 -o "{out_path}" -t mobilicube -p "{range_file}'

        # Extract command
        self.execute(cmd)
        self.clean(range_file)

        if return_data:
            x, x_bin, y, y_norm = self.load_rt(out_path, normalize=kwargs.get("normalize", False))
            return x, x_bin, y, y_norm
        return out_path

    def load_rt(self, path, normalize=False, **kwargs):
        """Load binary data extracted using `extract_rt`

        Parameters
        ----------
        path : str
            path to the binary MS data
        normalize : bool
            if `True`, a normalized spectrum will be also generated

        Returns
        -------
        x : np.ndarray
            retention time, in minutes
        x_bin : np.ndarray
            retention time, in bins
        y : np.ndarray
            intensity values
        y_norm : np.ndarray
            normalized (to 1) intensity values
        """
        # load retention time data
        data = np.fromfile(path, dtype=np.float32)
        n_rows = int(data[3::].shape[0] / 2)
        xy = data[3::].reshape(2, n_rows, order="F")
        x = xy[0, :]
        x_bin = np.arange(1, n_rows + 1, dtype=np.int32)

        # load chromatographic data
        data = np.fromfile(path, dtype=np.int32)
        xy = data[3::].reshape(2, n_rows, order="F")
        y = xy[1, :]

        self.clean(path)
        y_norm = y
        if normalize:
            y_norm = y.astype(np.float64) / max(y)

        return x, x_bin, y, y_norm

    def extract_dt(
        self,
        rt_start: float = 0,
        rt_end: float = 99999.0,
        dt_start: int = 1,
        dt_end: int = 200,
        mz_start: float = 0,
        mz_end: float = 99999,
        return_data=True,
        **kwargs,
    ):
        """Extract mobilogram from ion mobility dataset

        Parameters
        ----------
        rt_start : float
            start retention time, in minutes
        rt_end : float
            end retention time, in minutes
        dt_start : int
            start drift time, in drift bins
        dt_end : int
            end drift time, in drift bins
        mz_start : float
            start m/z extraction range, in Da
        mz_end : float
            end m/z extraction range, in Da
        return_data : bool
            if `True`, extracted data will be loaded and returned

        Returns
        -------
        x_bin : np.ndarray
            drift time in bins
        y : np.ndarray
            intensity values
        y_norm : np.ndarray
            normalized (to 1) intensity values
        """
        mz_start, mz_end = self.check_mz_range(mz_start, mz_end)

        # write output filename first
        filename = self.get_temp_filename()
        range_file = self.get_filepath(filename + ".in")
        with open(range_file, "w") as f_ptr:
            f_ptr.write(f"{mz_start} {mz_end} 1\n{rt_start} {rt_end} 1\n{dt_start} {dt_end} 200")

        # create command
        out_path = self.get_filepath(filename + ".1dDT")
        cmd = rf'{self._driftscope}\imextract.exe -d "{self.path}" -f 1 -o "{out_path}" -t mobilicube -p "{range_file}'
        # Extract command
        self.execute(cmd)
        self.clean(range_file)

        if return_data:
            x_bin, y, y_norm = self.load_dt(out_path, normalize=kwargs.get("normalize", False))
            return x_bin, y, y_norm
        return out_path

    def load_dt(self, path, normalize=False, **kwargs):
        """Load binary data extracted using `extract_dt`

        Parameters
        ----------
        path : str
            path to the binary MS data
        normalize : bool
            if `True`, a normalized spectrum will be also generated

        Returns
        -------
        x_bin : np.ndarray
            drift time, in bins
        y : np.ndarray
            intensity values
        y_norm : np.ndarray
            normalized (to 1) intensity values
        """
        data = np.fromfile(path, dtype=np.int32)
        n_rows = data[2]
        xy = data[3::].reshape(2, n_rows, order="F")
        y = xy[1, :]
        x_bin = np.arange(1, n_rows + 1, dtype=np.int32)

        self.clean(path)
        y_norm = y
        if normalize:
            y_norm = y.astype(np.float64) / y.max()

        return x_bin, y, y_norm

    def extract_heatmap(
        self,
        rt_start: float = 0,
        rt_end: float = 99999.0,
        dt_start: int = 1,
        dt_end: int = 200,
        mz_start: float = 0,
        mz_end: float = 99999,
        return_data=True,
        reduce: str = "sum",
        **kwargs,
    ):
        """Extract heatmap from ion mobility dataset

        Parameters
        ----------
        rt_start : float
            start retention time, in minutes
        rt_end : float
            end retention time, in minutes
        dt_start : int
            start drift time, in drift bins
        dt_end : int
            end drift time, in drift bins
        mz_start : float
            start m/z extraction range, in Da
        mz_end : float
            end m/z extraction range, in Da
        reduce : str, optional
            type of data reduction to be performed when summing interpolated scans
        return_data : bool
            if `True`, extracted data will be loaded and returned

        Returns
        -------
        array : np.ndarray
            heatmap array
        array_norm : np.ndarray
            normalized (to 1) heatmap array
        """
        mz_start, mz_end = self.check_mz_range(mz_start, mz_end)

        # write output filename first
        filename = self.get_temp_filename()
        range_file = self.get_filepath(filename + ".in")
        with open(range_file, "w") as f_ptr:
            f_ptr.write(f"{mz_start} {mz_end} 1\n{rt_start} {rt_end} 2\n{dt_start} {dt_end} 200")

        # create command
        out_path = self.get_filepath(filename + ".2dRTDT")
        cmd = (
            rf'{self._driftscope}\imextract.exe -d "{self.path}" -f 1 -o "{out_path}" -t mobilicube -b 1 '
            rf'-scans 0 -p "{range_file}'
        )

        # Extract command
        self.execute(cmd)
        self.clean(range_file)

        if return_data:
            array, array_norm = self.load_heatmap(out_path, normalize=kwargs.get("normalize", False), reduce=reduce)
            return array, array_norm
        return out_path

    def load_heatmap(self, path, normalize=False, reduce="sum", **kwargs):
        """Load binary data extracted using `extract_heatmap`

        Notes
        -----
        The data exported in the binary file contains 5 times as many `scans` as the raw data - it would appear that
        the raw data is interpolated using some kind of cubic interpolation. There are a number of ways to deal with
        it. For historical reasons, this was always summed, however, it is also possible to compute a `mean` or a
        `median`

        Parameters
        ----------
        path : str
            path to the binary MS data
        normalize : bool
            if `True`, a normalized spectrum will be also generated
        reduce : str
            data reduction of the interpolated heatmap - see `Notes` above

        Returns
        -------
        heatmap : np.ndarray
            intensity array
        heatmap_norm : np.ndarray
            normalized (to 1) intensity array
        """
        heatmap = np.fromfile(path, dtype=np.int32)
        n_rows = int(heatmap[3::].shape[0] / 200)
        heatmap = heatmap[3::].reshape((200, n_rows), order="F")
        if reduce == "sum":
            heatmap = np.sum(np.hsplit(heatmap, heatmap.shape[1] / 5), axis=2).T
        elif reduce == "mean":
            heatmap = np.mean(np.hsplit(heatmap, heatmap.shape[1] / 5), axis=2).T
        elif reduce == "median":
            heatmap = np.median(np.hsplit(heatmap, heatmap.shape[1] / 5), axis=2).T
        else:
            raise ValueError("Could not reduce the size of heatmap")

        self.clean(path)
        heatmap_norm = heatmap
        if normalize:
            heatmap_norm = normalize_2D(heatmap.astype(np.float64), axis=0, norm="max")
        return heatmap, heatmap_norm

    def extract_msdt(
        self,
        mz_start: float = 0,
        mz_end: float = 999999,
        n_points: int = 5000,
        dt_start: int = 1,
        dt_end: int = 200,
        return_data=True,
        **kwargs,
    ):
        mz_start, mz_end = self.check_mz_range(mz_start, mz_end)

        # write output filename first
        filename = self.get_temp_filename()
        range_file = self.get_filepath(filename + ".in")
        with open(range_file, "w") as f_ptr:
            f_ptr.write(f"{mz_start} {mz_end} {n_points}\n0.0 9999.0 1\n{dt_start} {dt_end} 200")

        # create command
        out_path = self.get_filepath(filename + ".2dDTMZ")
        cmd = rf'{self._driftscope}\imextract.exe -d "{self.path}" -f 1 -o "{out_path}" -t mobilicube -p "{range_file}'

        # Extract command
        self.execute(cmd)
        # self.clean(range_file)

        if return_data:
            array, array_norm = self.load_msdt(out_path, normalize=kwargs.get("normalize", False))
            return array, array_norm
        return out_path

    def load_msdt(self, path, normalize=False, **kwargs):
        """Load binary data extracted using `extract_msdt`

        Parameters
        ----------
        path : str
            path to the binary MS data
        normalize : bool
            if `True`, a normalized spectrum will be also generated

        Returns
        -------
        heatmap : np.ndarray
            intensity array
        heatmap_norm : np.ndarray
            normalized (to 1) intensity array
        """
        heatmap = np.fromfile(path, dtype=np.int32)
        n_bins = heatmap[0]
        heatmap = heatmap[3::].reshape((200, n_bins), order="C")

        self.clean(path)
        heatmap_norm = heatmap
        if normalize:
            heatmap_norm = normalize_2D(heatmap.astype(np.float64), axis=0, norm="max")
        return heatmap, heatmap_norm
