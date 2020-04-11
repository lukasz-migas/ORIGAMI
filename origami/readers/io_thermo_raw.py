# Third-party imports
import numpy as np

# Local imports
from _ctypes import COMError
from comtypes.client import CreateObject
from origami.utils.path import clean_filename


class ThermoRawReader:
    OBJ_GUID = "{10729396-43ee-49e5-aa07-85f02292ac70}"

    def __init__(self, path):
        self.path = path
        self.source = self.create_parser()
        self.filters = self.source.GetAllFilterInfo()

        self.last_scan = 1

    def create_parser(self):
        """Create parser"""
        try:
            source = CreateObject(self.OBJ_GUID)
        except WindowsError as err:
            print("RawReader.dll not found in registry.")
            raise err
        except COMError:
            # As far as I know, this should only happen if you're trying to
            # run this in Python 3.
            source = CreateObject(self.OBJ_GUID, dynamic=True)
        return source

    def get_scan_info(self, rt_start=None, rt_end=None):

        _scan_range = self.source.scan_range()
        if rt_start is None:
            rt_start = _scan_range[0]
        if rt_end is None or rt_end > _scan_range[1]:
            rt_end = _scan_range[1]

        scan_info = {}
        for scan in range(rt_start, rt_end):
            info = self.source.GetFilterInfoForScan(scan)
            ms_level = info[0].upper() if info[0].upper() != "MS" else "MS1"
            time = self.source.time_from_scan(scan)
            ms_format = "p" if info[2] == "Profile" else "c"
            scan_info[scan] = {
                "time": time,
                "precursor_mz": info[1],
                "ms_level": ms_level,
                "format": ms_format,
                "filter": self.filters[scan - 1],
            }

        return scan_info

    def get_average_spectrum(self, title="Full ms ", return_xy=True):
        spectrum = np.array(self.source.average_scan(0, 99999, title))

        if return_xy:
            return spectrum[:, 0], spectrum[:, 1]
        else:
            return spectrum

    def get_spectrum_for_each_filter(self):

        unique_filters = set(self.filters)
        data = {}
        for title in unique_filters:
            if title not in ["None", None]:
                msX, msY = self.get_average_spectrum(title)
                xlimits = [np.min(msX), np.max(msX)]
                data[clean_filename(title)] = {
                    "xvals": msX,
                    "yvals": msY,
                    "xlabels": "m/z (Da)",
                    "xlimits": xlimits,
                    "filter": title,
                }
        return data

    def get_chromatogram_for_each_filter(self):
        unique_filters = set(self.filters)
        data = {}
        for title in unique_filters:
            if title not in ["None", None]:
                rtX, rtY = self.get_xic(title=title)
                xlimits = [np.min(rtX), np.max(rtY)]
                data[clean_filename(title)] = {
                    "xvals": rtX,
                    "yvals": rtY,
                    "xlabels": "Time (min)",
                    "xlimits": xlimits,
                    "filter": title,
                }
        return data

    def get_spectrum(self):
        pass

    def get_tic(self, return_xy=True):
        tic = np.array(self.source.get_tic())
        if return_xy:
            return tic[:, 0], tic[:, 1]
        return tic

    def get_xic(self, mz_start=-1, mz_end=-1, rt_start=-1, rt_end=-1, title=None, return_xy=True):
        """Return extracted chromatogram"""
        if rt_start != -1:
            rt_start = self.source.scan_from_time(rt_start)
        if rt_end != -1:
            rt_end = self.source.scan_from_time(rt_end)
        if title is None:
            title = "Full MS"
        xic = np.array(self.source.get_xic(rt_start, rt_end, mz_start, mz_end, title))

        if return_xy:
            return xic[:, 0], xic[:, 1]
        else:
            return xic

    def _stitch_chromatograms(self, data):
        from natsort import natsorted

        chrom_mins = []
        for key in data:
            chrom_mins.append([data[key]["xvals"][0], data[key]["xvals"][-1], key])

        chrom_mins = natsorted(chrom_mins)

        xvals, yvals = [], []
        for item in chrom_mins:
            rt_start, rt_end, key = item
            xvals.extend(data[key]["xvals"])
            yvals.extend(data[key]["yvals"])

        return xvals, yvals
