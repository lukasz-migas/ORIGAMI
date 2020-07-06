# Standard library imports
import math
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
from origami.utils.exceptions import NoIonMobilityDatasetError
from origami.objects.containers import IonHeatmapObject
from origami.objects.containers import MobilogramObject
from origami.objects.containers import ChromatogramObject
from origami.objects.containers import MassSpectrumObject
from origami.objects.containers import MassSpectrumHeatmapObject
from origami.readers.io_waters_raw_api import WatersRawReader

logger = logging.getLogger(__name__)

# create data holder
TEMP_DATA_FOLDER = os.path.join(os.getcwd(), "temporary_data")

# TODO: move away from returning individual arrays to wrapping them into MS objects


def get_driftscope_path():
    """Searches in the common places for Driftscope path"""
    # if installed on the system, Driftscope will be in C:\DriftScope\lib
    if os.path.exists(r"C:\DriftScope\lib"):
        return r"C:\DriftScope\lib"
    else:
        path = os.path.join(os.path.dirname(__file__), "driftscope")
        if os.path.exists(path):
            return path


class WatersIMReader(WatersRawReader):
    def __init__(self, path, driftscope_path=None, temp_dir=None, silent: bool = False):
        super().__init__(path)
        self.path = check_waters_path(path)
        self._driftscope = driftscope_path if driftscope_path is not None else get_driftscope_path()
        self._temp_dir = temp_dir if temp_dir is not None else self.path
        self.output_dir = self._temp_dir
        self.verbose = True
        self._last = None
        self._rt_min = None
        self._dt_ms = None
        if self.n_functions < 2 and not silent:
            raise NoIonMobilityDatasetError(f"Dataset {path} does not have ion mobility dimension")

    @property
    def driftscope_path(self):
        return os.path.join(self._driftscope, "imextract.exe")

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
        mz_obj : MassSpectrumObject
            mass spectrum object
        """
        # write output filename first
        filename = self.get_temp_filename()
        range_file = self.get_filepath(filename + ".in")
        with open(range_file, "w") as f_ptr:
            f_ptr.write(f"{mz_start} {mz_end} {n_bins}\n{rt_start} {rt_end} 1\n{dt_start} {dt_end} 1")

        # create command
        out_path = self.get_filepath(filename + ".1dMZ")
        cmd = rf'{self.driftscope_path} -d "{self.path}" -f 1 -o "{out_path}" -t mobilicube -p "{range_file}'

        # Extract command
        self.execute(cmd)
        self.clean(range_file)

        if return_data:
            x, y = self.load_ms(out_path)
            return MassSpectrumObject(
                x,
                y,
                metadata={
                    "rt_start": float(rt_start),
                    "rt_end": float(rt_end),
                    "dt_start": float(dt_start),
                    "dt_end": float(dt_end),
                    "mz_start": float(mz_start),
                    "mz_end": float(mz_end),
                },
            )
        return out_path

    def load_ms(self, path):
        """Load binary data extracted using `extract_ms`

        Parameters
        ----------
        path : str
            path to the binary MS data

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

        return x, y

    def extract_rt(
        self,
        rt_start: float = 0,
        rt_end: float = 99999.0,
        dt_start: int = 1,
        dt_end: int = 200,
        mz_start: float = 0,
        mz_end: float = 99999,
        return_data=True,
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
        rt_obj : ChromatogramObject
            chrmatogram object
        """
        mz_start, mz_end = self.check_mz_range(mz_start, mz_end)

        # write output filename first
        filename = self.get_temp_filename()
        range_file = self.get_filepath(filename + ".in")
        with open(range_file, "w") as f_ptr:
            f_ptr.write(f"{mz_start} {mz_end} 1\n{rt_start} {rt_end} 5000\n{dt_start} {dt_end} 1")

        # create command
        out_path = self.get_filepath(filename + ".1dRT")
        cmd = rf'{self.driftscope_path} -d "{self.path}" -f 1 -o "{out_path}" -t mobilicube -p "{range_file}'

        # Extract command
        self.execute(cmd)
        self.clean(range_file)

        if return_data:
            x, x_bin, y = self.load_rt(out_path)
            return ChromatogramObject(
                x_bin,
                y,
                extra_data=dict(x_min=x),
                metadata={
                    "rt_start": float(rt_start),
                    "rt_end": float(rt_end),
                    "dt_start": float(dt_start),
                    "dt_end": float(dt_end),
                    "mz_start": float(mz_start),
                    "mz_end": float(mz_end),
                },
            )
        return out_path

    def load_rt(self, path):
        """Load binary data extracted using `extract_rt`

        Parameters
        ----------
        path : str
            path to the binary MS data

        Returns
        -------
        x : np.ndarray
            retention time, in minutes
        x_bin : np.ndarray
            retention time, in bins
        y : np.ndarray
            intensity values
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

        return x, x_bin, y

    def extract_dt(
        self,
        rt_start: float = 0,
        rt_end: float = 99999.0,
        dt_start: int = 1,
        dt_end: int = 200,
        mz_start: float = 0,
        mz_end: float = 99999,
        return_data=True,
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
        dt_obj : MobilogramObject
            mobilogram object
        """
        mz_start, mz_end = self.check_mz_range(mz_start, mz_end)

        # write output filename first
        filename = self.get_temp_filename()
        range_file = self.get_filepath(filename + ".in")
        with open(range_file, "w") as f_ptr:
            f_ptr.write(f"{mz_start} {mz_end} 1\n{rt_start} {rt_end} 1\n{dt_start} {dt_end} 200")

        # create command
        out_path = self.get_filepath(filename + ".1dDT")
        cmd = rf'{self.driftscope_path} -d "{self.path}" -f 1 -o "{out_path}" -t mobilicube -p "{range_file}'
        # Extract command
        self.execute(cmd)
        self.clean(range_file)

        if return_data:
            x_bin, y = self.load_dt(out_path)
            return MobilogramObject(
                x_bin,
                y,
                extra_data=dict(x_ms=self.dt_ms),
                metadata={
                    "rt_start": float(rt_start),
                    "rt_end": float(rt_end),
                    "dt_start": float(dt_start),
                    "dt_end": float(dt_end),
                    "mz_start": float(mz_start),
                    "mz_end": float(mz_end),
                },
            )
        return out_path

    def load_dt(self, path):
        """Load binary data extracted using `extract_dt`

        Parameters
        ----------
        path : str
            path to the binary MS data

        Returns
        -------
        x_bin : np.ndarray
            drift time, in bins
        y : np.ndarray
            intensity values
        """
        data = np.fromfile(path, dtype=np.int32)
        n_rows = data[2]
        xy = data[3::].reshape(2, n_rows, order="F")
        y = xy[1, :]
        x_bin = np.arange(1, n_rows + 1, dtype=np.int32)
        self.clean(path)

        return x_bin, y

    def extract_heatmap(
        self,
        rt_start: float = 0,
        rt_end: float = 99999.0,
        dt_start: int = 1,
        dt_end: int = 200,
        mz_start: float = 0,
        mz_end: float = 99999,
        reduce: str = "sum",
        return_data=True,
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
        heatmap_obj : IonHeatmapObject
            heatmap object
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
            rf'{self.driftscope_path} -d "{self.path}" -f 1 -o "{out_path}" -t mobilicube -b 1 '
            rf'-scans 0 -p "{range_file}'
        )

        # Extract command
        self.execute(cmd)
        self.clean(range_file)

        if return_data:
            array = self.load_heatmap(out_path, reduce=reduce)
            dt_x = self.dt_bin
            dt_y = array.sum(axis=1)
            rt_x = self.rt_bin
            rt_y = array.sum(axis=0)
            return IonHeatmapObject(
                array,
                x=rt_x,
                y=dt_x,
                xy=rt_y,
                yy=dt_y,
                metadata={
                    "rt_start": float(rt_start),
                    "rt_end": float(rt_end),
                    "dt_start": float(dt_start),
                    "dt_end": float(dt_end),
                    "mz_start": float(mz_start),
                    "mz_end": float(mz_end),
                },
            )
        return out_path

    def load_heatmap(self, path, reduce="sum"):
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
        reduce : str
            data reduction of the interpolated heatmap - see `Notes` above

        Returns
        -------
        heatmap : np.ndarray
            intensity array
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
            raise ValueError("Could not reduce the size of heatmap. Use either `sum, mean, median` methods")

        self.clean(path)
        return heatmap

    def extract_msdt(
        self,
        mz_start: float = 0,
        mz_end: float = 999999,
        n_points: int = 5000,
        dt_start: int = 1,
        dt_end: int = 200,
        rt_start: float = 0,
        rt_end: float = 99999.0,
        mz_bin_size: float = None,
        return_data=True,
    ):
        """Extract heatmap from ion mobility dataset

        Parameters
        ----------
        mz_start : float
            start m/z extraction range, in Da
        mz_end : float
            end m/z extraction range, in Da
        n_points : int
            number of points in the mass dimension
        dt_start : int
            start drift time, in drift bins
        dt_end : int
            end drift time, in drift bins
        rt_start : float
            start retention time, in minutes
        rt_end : float
            end retention time, in minutes
        mz_bin_size : float
            bin size in Da
        return_data : bool
            if `True`, extracted data will be loaded and returned

        Returns
        -------
        msdt_obj : MassSpectrumHeatmapObject
            heatmap object
        """
        mz_start, mz_end = self.check_mz_range(mz_start, mz_end)
        if mz_bin_size is not None and isinstance(mz_bin_size, float):
            n_points = math.floor((mz_end - mz_start) / mz_bin_size)

        # write output filename first
        filename = self.get_temp_filename()
        range_file = self.get_filepath(filename + ".in")
        with open(range_file, "w") as f_ptr:
            f_ptr.write(f"{mz_start} {mz_end} {n_points}\n{rt_start} {rt_end} 1\n{dt_start} {dt_end} 200")

        # create command
        out_path = self.get_filepath(filename + ".2dDTMZ")
        cmd = rf'{self.driftscope_path} -d "{self.path}" -f 1 -o "{out_path}" -t mobilicube -p "{range_file}'

        # Extract command
        self.execute(cmd)
        self.clean(range_file)

        if return_data:
            array = self.load_msdt(out_path)
            n_points = array.shape[1]
            mz_bin_size = (mz_end - mz_start) / n_points
            mz_x = self.mz_from_n_bins(mz_start - mz_bin_size, mz_end + mz_bin_size, n_points)
            mz_y = array.sum(axis=0)
            dt_x = self.dt_bin
            dt_y = array.sum(axis=1)
            return MassSpectrumHeatmapObject(
                array,
                x=mz_x,
                y=dt_x,
                xy=mz_y,
                yy=dt_y,
                metadata={
                    "dt_start": float(dt_start),
                    "dt_end": float(dt_end),
                    "mz_start": float(mz_start),
                    "mz_end": float(mz_end),
                    "n_points": int(n_points),
                },
            )

        return out_path

    def load_msdt(self, path):
        """Load binary data extracted using `extract_msdt`

        Parameters
        ----------
        path : str
            path to the binary MS data

        Returns
        -------
        heatmap : np.ndarray
            intensity array
        """
        heatmap = np.fromfile(path, dtype=np.int32)
        n_bins = heatmap[0]
        heatmap = heatmap[3::].reshape((200, n_bins), order="C")

        self.clean(path)

        return heatmap
