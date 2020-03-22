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

        self.mz_min, self.mz_max, self.n_scans = self.get_mass_range()

    def get_mass_range(self):
        """Create handle to the API reader and extract the experimental mass range"""
        reader = WatersRawReader(self.path)
        stats = reader.stats_in_functions
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
        filename = get_short_hash()
        self._last = filename
        return filename

    def execute(self, cmd):
        process_id = Popen(cmd, shell=self.verbose, creationflags=CREATE_NEW_CONSOLE)
        process_id.wait()

    def get_filepath(self, filename):
        return os.path.join(self.output_dir, filename)

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


# def driftscope_extract_MS(
#     path,
#     bin_size=10000,
#     rt_start=0,
#     rt_end=99999.0,
#     dt_start=1,
#     dt_end=200,
#     mz_start=0,
#     mz_end=99999,
#     driftscope_path=r"C:\DriftScope\lib",
#     **kwargs,
# ):
#     """
#     Extract MS data from MassLynx (.raw) file that has IMS data
#     @param path (str): path to MassLynx (.raw) file
#     @param bin_size (int): number of points in the m/z dimension
#     @param rt_start (float): start retention time (minutes)
#     @param rt_end (float): end retention time (minutes)
#     @param dt_start (float): start drift time (bins)
#     @param dt_end (float): end drift time (bins)
#     @param mz_start (float): start m/z  (Da)
#     @param mz_end (float): end m/z (Da)
#     @param driftscope_path (str): path to DriftScope directory
#     """
#     # check if data should be extracted to data folder OR temporary folder
#     if kwargs.get("use_temp_folder", True) and os.path.exists(temp_data_folder):
#         out_path = temp_data_folder
#     else:
#         out_path = path
#
#     path = check_waters_path(path)
#
#     # Write range file
#     range_file = os.path.join(out_path, "__.1dMS.inp")
#     try:
#         input_file = open(range_file, "w")
#     except IOError as err:
#         #         DialogBox(exceptionTitle="Error", exceptionMsg=str(err), type="Error")
#         return
#
#     input_file.write(
#         "{} {} {}\n{} {} 1\n{} {} 1".format(mz_start, mz_end, bin_size, rt_start, rt_end, dt_start, dt_end)
#     )
#     input_file.close()
#
#     # Create command for execution
#     cmd = r'{}\imextract.exe -d "{}" -f 1 -o "{}\{}.1dMZ" -t mobilicube -p "{}'.format(
#         driftscope_path, path, out_path, path, range_file
#     )
#
#     # Extract command
#     process_id = Popen(cmd, shell=kwargs.get("verbose", True), creationflags=CREATE_NEW_CONSOLE)
#     process_id.wait()
#
#     # return data
#     if kwargs.get("return_data", False):
#         msX, msY = rawMassLynx_MS_load(out_path, path + ".1dMZ")
#         return msX, msY
#     else:
#         return None
#
#
# def rawMassLynx_MS_load(path, inputFile="output.1dMZ", normalize=True, **kwargs):
#     data_path = os.path.join(path, inputFile)
#     # Load data into array
#     data = np.fromfile(data_path, dtype=np.float32)
#     data_clean = data[2:(-1)]
#     n_rows = int(len(data_clean) / 2)
#     msDataReshape = data_clean.reshape((2, n_rows), order="F")
#     # Extract MS data
#     data_x = msDataReshape[1]
#     data_y = msDataReshape[0]
#
#     # clean-up MS file
#     firstBad = strictly_increasing(data_x)
#     if firstBad:
#         pass
#     else:
#         firstBadIdx = np.where(data_x == firstBad)
#         try:
#             data_x = data_x[0 : (firstBadIdx[0][0] - 1)]
#             data_y = data_y[0 : (firstBadIdx[0][0] - 1)]
#         except IndexError:
#             pass
#
#     # clean-up filepath
#     try:
#         clean_up(data_path)
#     except Exception as e:
#         logger.warning("Failed to delete file. Error: {}".format(e))
#
#     # Normalize MS data
#     if normalize:
#         data_y = data_y / max(data_y)
#
#     return data_x, data_y
#

# def driftscope_extract_RT(
#     path=None,
#     rt_start=0,
#     rt_end=99999.0,
#     dt_start=1,
#     dt_end=200,
#     mz_start=0,
#     mz_end=999999,
#     driftscope_path=r"C:\DriftScope\lib",
#     **kwargs,
# ):
#     """
#     Extract the retention time for specified (or not) mass range
#     """
#     # check if data should be extracted to data folder OR temporary folder
#     if kwargs.get("use_temp_folder", True) and os.path.exists(temp_data_folder):
#         out_path = temp_data_folder
#     else:
#         out_path = path
#
#     path = check_waters_path(path)
#
#     # Create input file
#     range_file = os.path.join(out_path, "__.1dRT.inp")
#
#     try:
#         input_file = open(range_file, "w")
#     except IOError as err:
#         #         DialogBox(exceptionTitle="Error", exceptionMsg=str(err), type="Error")
#         return
#     input_file.write("{} {} 1\n{} {} 5000\n{} {} 1".format(mz_start, mz_end, rt_start, rt_end, dt_start, dt_end))
#     input_file.close()
#
#     # Create command for execution
#     cmd = r'{}\imextract.exe -d "{}" -f 1 -o "{}\output.1dRT" -t mobilicube -p "{}'.format(
#         driftscope_path, path, out_path, range_file
#     )
#
#     process_id = Popen(cmd, shell=kwargs.get("verbose", True), creationflags=CREATE_NEW_CONSOLE)
#     process_id.wait()
#
#     # return data
#     if kwargs.get("return_data", False):
#         if kwargs.get("normalize", False):
#             rtY, rtYnorm = rawMassLynx_RT_load(out_path, normalize=True)
#             rtX = np.arange(1, len(rtY) + 1)
#             return rtX, rtY, rtYnorm
#         else:
#             rtY = rawMassLynx_RT_load(out_path)
#             rtX = np.arange(1, len(rtY) + 1)
#             return rtX, rtY
#     else:
#         return None
#
#
# def rawMassLynx_RT_load(path=None, inputFile="output.1dRT", normalize=False, **kwargs):
#     data_path = os.path.join(path, inputFile)
#     data = np.fromfile(data_path, dtype=np.int32)
#     n_scans = data[1]
#     data_clean = data[3::]
#     data_reshape = data_clean.reshape((n_scans, 2), order="C")
#     data_1D = data_reshape[:, 1]
#
#     # clean-up filepath
#     try:
#         clean_up(data_path)
#     except Exception as e:
#         logger.warning("Failed to delete file. Error: {}".format(e))
#
#     if normalize:
#         data_1D_norm = data_1D.astype(np.float64) / max(data_1D)
#         return data_1D, data_1D_norm
#     else:
#         return data_1D
#
#
# def driftscope_extract_DT(
#     path=None,
#     rt_start=0,
#     rt_end=99999.0,
#     dt_start=1,
#     dt_end=200,
#     mz_start=0,
#     mz_end=999999,
#     driftscope_path=r"C:\DriftScope\lib",
#     **kwargs,
# ):
#     # check if data should be extracted to data folder OR temporary folder
#     if kwargs.get("use_temp_folder", True) and os.path.exists(temp_data_folder):
#         out_path = temp_data_folder
#     else:
#         out_path = path
#
#     path = check_waters_path(path)
#
#     # Create input file
#     range_file = os.path.join(out_path, "__.1dDT.inp")
#     try:
#         input_file = open(range_file, "w")
#     except IOError as err:
#         #         DialogBox(exceptionTitle="Error", exceptionMsg=str(err), type="Error")
#         return
#     input_file.write("{} {} 1\n{} {} 1\n{} {} 200".format(mz_start, mz_end, rt_start, rt_end, dt_start, dt_end))
#     input_file.close()
#
#     # Create command for execution
#     cmd = r'{}\imextract.exe -d "{}" -f 1 -o "{}\output.1dDT" -t mobilicube -p "{}'.format(
#         driftscope_path, path, out_path, range_file
#     )
#     process_id = Popen(cmd, shell=kwargs.get("verbose", True), creationflags=CREATE_NEW_CONSOLE)
#     process_id.wait()
#
#     # return data
#     if kwargs.get("return_data", False):
#         if kwargs.get("normalize", False):
#             dtY, dtYnorm = rawMassLynx_DT_load(out_path, normalize=True)
#             dtX = np.arange(1, len(dtY) + 1)
#             return dtX, dtY, dtYnorm
#         else:
#             dtY = rawMassLynx_DT_load(out_path)
#             dtX = np.arange(1, len(dtY) + 1)
#             return dtX, dtY
#     else:
#         return None
#
#
# def rawMassLynx_DT_load(path=None, inputFile="output.1dDT", normalize=False, **kwargs):
#     """
#     Load data for 1D IM-MS data
#     """
#     data_path = os.path.join(path, inputFile)
#     data = np.fromfile(data_path, dtype=np.int32)
#     data_clean = data[3::]
#     data_reshape = data_clean.reshape((200, 2), order="C")
#     data_1D = data_reshape[:, 1]
#
#     # clean-up filepath
#     try:
#         clean_up(data_path)
#     except Exception as e:
#         logger.warning("Failed to delete file. Error: {}".format(e))
#
#     if normalize:
#         data_1D_norm = data_1D.astype(np.float64) / max(data_1D)
#         return data_1D_norm
#     else:
#         return data_1D
#
#
# def driftscope_extract_2D(
#     path=None,
#     mz_start=0,
#     mz_end=999999,
#     rt_start=0,
#     rt_end=99999.0,
#     dt_start=1,
#     dt_end=200,
#     driftscope_path=r"C:\DriftScope\lib",
#     **kwargs,
# ):
#     # check if data should be extracted to data folder OR temporary folder
#     if kwargs.get("use_temp_folder", True) and os.path.exists(temp_data_folder):
#         out_path = temp_data_folder
#     else:
#         out_path = path
#
#     path = check_waters_path(path)
#
#     # Create input file
#     range_file = os.path.join(out_path, "__.2dRTDT.inp")
#     try:
#         input_file = open(range_file, "w")
#     except IOError as err:
#         #         DialogBox(exceptionTitle="Error", exceptionMsg=str(err), type="Error")
#         return
#     input_file.write("{} {} 1\n{} {} 5000\n{} {} 200".format(mz_start, mz_end, rt_start, rt_end, dt_start, dt_end))
#     input_file.close()
#     # Create command for execution
#     cmd = r'{}\imextract.exe -d "{}" -f 1 -o "{}\output.2dRTDT" -t mobilicube -b 1 -scans 0 -p "{}'.format(
#         driftscope_path, path, out_path, range_file
#     )
#
#     process_id = Popen(cmd, shell=kwargs.get("verbose", True), creationflags=CREATE_NEW_CONSOLE)
#     process_id.wait()
#
#     # return data
#     if kwargs.get("return_data", False):
#         if kwargs.get("normalize", False):
#             dt, dtnorm = rawMassLynx_2DT_load(out_path, normalize=True)
#             return dt, dtnorm
#         else:
#             dt = rawMassLynx_2DT_load(out_path)
#             return dt
#     else:
#         return None
#
#
# def rawMassLynx_2DT_load(path=None, inputFile="output.2dRTDT", normalize=False, **kwargs):
#     data_path = os.path.join(path, inputFile)
#     data = np.fromfile(data_path, dtype=np.int32)
#     data_clean = data[3::]
#     n_rows = data[1]
#     data_reshape = data_clean.reshape((200, n_rows), order="F")  # Reshapes the list to 2D array
#     data_split = np.hsplit(data_reshape, int(n_rows / 5))  # Splits the array into [scans,200,5] array
#     data_split = np.sum(data_split, axis=2).T  # Sums each 5 RT scans together
#
#     """
#     There is a bug - sometimes when extracting, the last column values
#     go way outside of range and make the plot look terrible. Hacky way
#     round this is to check that any values fall outside the range and if so,
#     set the last column to 0s...
#     """
#
#     # Test to ensure all values are above 0 or below 1E8
#     for value in data_split[:, -1]:
#         if value < 0:
#             data_split[:, -1] = 0
#         elif value > 10000000:
#             data_split[:, -1] = 0
#
#     # clean-up filepath
#     try:
#         clean_up(data_path)
#     except Exception as e:
#         logger.warning("Failed to delete file. Error: {}".format(e))
#
#     if normalize:
#         data_split_norm = normalize(data_split.astype(np.float64), axis=0, norm="max")  # Norm to 1
#         return data_split, data_split_norm
#     else:
#         return data_split
#
#
# def driftscope_extract_MZDT(
#     path=None,
#     mz_start=0,
#     mz_end=999999,
#     mz_nPoints=5000,
#     dt_start=1,
#     dt_end=200,
#     silent_extract=True,
#     driftscope_path=r"C:\DriftScope\lib",
#     **kwargs,
# ):
#     # check if data should be extracted to data folder OR temporary folder
#     if kwargs.get("use_temp_folder", True) and os.path.exists(temp_data_folder):
#         out_path = temp_data_folder
#     else:
#         out_path = path
#
#     path = check_waters_path(path)
#
#     # Create input file
#     range_file = os.path.join(out_path, "__.2dDTMZ.inp")
#     try:
#         input_file = open(range_file, "w")
#     except IOError as err:
#         #         DialogBox(exceptionTitle="Error", exceptionMsg=str(err), type="Error")
#         return
#     input_file.write("{} {} {}\n0.0 9999.0 1\n{} {} 200".format(mz_start, mz_end, mz_nPoints, dt_start, dt_end))
#     input_file.close()
#
#     # Create command for execution
#     cmd = r'{}\imextract.exe -d "{}" -f 1 -o "{}\output.2dDTMZ" -t mobilicube -p "{}'.format(
#         driftscope_path, path, out_path, range_file
#     )
#
#     process_id = Popen(cmd, shell=kwargs.get("verbose", True), creationflags=CREATE_NEW_CONSOLE)
#     process_id.wait()
#
#     # return data
#     if kwargs.get("return_data", False):
#         if kwargs.get("normalize", False):
#             dt, dtnorm = rawMassLynx_MZDT_load(out_path, normalize=True)
#             return dt, dtnorm
#         else:
#             dt = rawMassLynx_MZDT_load(out_path)
#             return dt
#     else:
#         return None
#
#
# def rawMassLynx_MZDT_load(path=None, inputFile="output.2dDTMZ", normalize=False, **kwargs):
#     data_path = os.path.join(path, inputFile)
#     data = np.fromfile(data_path, dtype=np.int32)
#     data_clean = data[3::]
#     n_bins = data[0]
#     print(n_bins)
#     data_reshaped = data_clean.reshape((200, n_bins), order="C")  # Reshapes the list to 2D array
#     print(data_reshaped.shape)
#
#     # clean-up filepath
#     #     try:
#     #         clean_up(data_path)
#     #     except Exception as e:
#     #         logger.warning("Failed to delete file. Error: {}".format(e))
#
#     if normalize:
#         data_reshaped_norm = normalize(data_reshaped.astype(np.float64), axis=0, norm="max")  # Norm to 1
#         return data_reshaped, data_reshaped_norm
#     else:
#         return data_reshaped
