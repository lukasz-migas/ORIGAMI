# isort:skip_file
# Standard library imports
import os
import sys
from typing import Optional

import clr
import numpy as np

# Local imports
from origami.utils.path import clean_filename

DLL_PATH = os.path.join(os.path.dirname(__file__), "thermo")
DLL_LIST = [
    "ThermoFisher.CommonCore.Data",
    "ThermoFisher.CommonCore.RawFileReader",
    "ThermoFisher.CommonCore.BackgroundSubtraction",
    "ThermoFisher.CommonCore.MassPrecisionEstimator",
    "System.Collections",
]

sys.path += [DLL_PATH]
for dll in DLL_LIST:
    clr.AddReference(dll)

# noinspection PyUnresolvedReferences
from ThermoFisher.CommonCore.Data import Extensions  # noqa

# noinspection PyUnresolvedReferences
from ThermoFisher.CommonCore.Data.Business import Range  # noqa

# noinspection PyUnresolvedReferences
from ThermoFisher.CommonCore.Data.Business import Device  # noqa

# noinspection PyUnresolvedReferences
from ThermoFisher.CommonCore.Data.Business import ChromatogramSignal  # noqa

# noinspection PyUnresolvedReferences
from ThermoFisher.CommonCore.Data.Business import ChromatogramTraceSettings  # noqa

# noinspection PyUnresolvedReferences
from ThermoFisher.CommonCore.RawFileReader import RawFileReaderAdapter  # noqa

# noinspection PyUnresolvedReferences
from ThermoFisher.CommonCore.Data.Interfaces import IScanFilter  # noqa


class ThermoRawReader:
    def __init__(self, path):
        self.path = path
        self.source = self.create_parser()
        self._filters = self.filter_list()
        self.filters = self._collect_filters()
        self.last_scan = 1
        self._rt_min = None

    @property
    def scan_range(self):
        """Returns the scan range"""
        return self.source.RunHeaderEx.FirstSpectrum, self.source.RunHeaderEx.LastSpectrum

    @property
    def time_range(self):
        """Returns the time range"""
        return self.source.RunHeaderEx.StartTime, self.source.RunHeaderEx.EndTime

    @property
    def mass_range(self):
        """Return the acquisition mass range"""
        return self.source.RunHeaderEx.LowMass, self.source.RunHeaderEx.HighMass

    @property
    def rt_bin(self):
        start_scan, end_scan = self.scan_range
        return np.arange(start_scan, end_scan + 1)

    @property
    def rt_min(self):
        if self._rt_min is None:
            self._rt_min, _ = self.get_chromatogram(0, 1)
        return self._rt_min

    def n_scans(self):
        """Returns the number of scans"""
        return self.scan_range[-1]

    def create_parser(self):
        """Create parser"""
        source = RawFileReaderAdapter.FileFactory(self.path)
        if source.InstrumentCount > 1:
            print("This file has multiple files present - only one is allowed at the moment")
        source.SelectInstrument(Device.MS, 1)
        return source

    def _collect_filters(self):
        """Returns filter for each scan"""
        filters = []
        for scan_id in range(*self.scan_range):
            filters.append(IScanFilter(self.source.GetFilterForScanNumber(scan_id)).ToString())
        return filters

    def filter_list(self):
        """Returns filter list"""
        filters = [IScanFilter(x).ToString() for x in self.source.GetFilters()]
        return filters

    def get_scan_info(self, rt_start=None, rt_end=None):

        _scan_range = self.source.scan_range()
        if rt_start is None:
            rt_start = _scan_range[0]
        if rt_end is None or rt_end > _scan_range[1]:
            rt_end = _scan_range[1]

        scan_info = {}
        for scan_id in range(rt_start, rt_end):
            info = self.source.GetFilterForScanNumber(scan_id)
            level = "MS%d" % info.MSOrder
            mz = 0.0
            if level != "MS1":
                mz = info.GetMass(0)  # I guess >0 is for MS3 etc?

            ms_level = info[0].upper() if info[0].upper() != "MS" else "MS1"
            time = self.source.RetentionTimeFromScanNumber(scan_id)
            scan_info = self.source.GetScanStatsForScanNumber(scan_id)
            ms_format = "c" if scan_info.IsCentroidScan else "p"
            scan_info[scan_id] = {
                "time": time,
                "precursor_mz": mz,
                "ms_level": ms_level,
                "format": ms_format,
                "filter": self.filters[scan_id - 1],
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
                x, y = self.get_average_spectrum(title)
                xlimits = [np.min(x), np.max(x)]
                data[clean_filename(title)] = {
                    "xvals": x,
                    "yvals": y,
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
                x, y = self.get_chromatogram(title=title)
                xlimits = [np.min(x), np.max(y)]
                data[clean_filename(title)] = {
                    "xvals": x,
                    "yvals": y,
                    "xlabels": "Time (min)",
                    "xlimits": xlimits,
                    "filter": title,
                }
        return data

    def _get_spectrum(self, scan_id, centroid: bool = False):
        """Retrieve scan data"""
        if scan_id > self.n_scans():
            raise ValueError("Tried to extract scan that is not present in the data")

        scan_stats = self.source.GetScanStatsForScanNumber(scan_id)
        # Does IsCentroidScan indicate that profile data is not available?
        if centroid or scan_stats.IsCentroidScan:
            if not centroid:
                raise ValueError("No profile data for scan %s" % scan_id)

            stream = self.source.GetCentroidStream(scan_id, False)
            if stream.Masses is not None and stream.Intensities is not None:
                x = np.asarray(list(stream.Masses))
                y = np.asarray(list(stream.Intensities))
            else:
                # try getting profile data instead
                scan = self.source.GetSegmentedScanFromScanNumber(scan_id, scan_stats)
                x = np.asarray(list(scan.Positions))
                y = np.asarray(list(scan.Intensities))

        else:  # Profile-only scan.
            scan = self.source.GetSegmentedScanFromScanNumber(scan_id, scan_stats)
            x = np.asarray(list(scan.Positions))
            y = np.asarray(list(scan.Intensities))
        return x, y

    def _get_scan_parameters(
        self, start_scan: Optional[int] = None, end_scan: Optional[int] = None, title: Optional[str] = None
    ):
        """Retrieve scan information for defined range"""
        if title:
            if title not in self._filters:
                raise ValueError(f"Filter `{title}` was not recorded")
            scans = []
            for scan_id, _title in enumerate(self.filters, start=1):
                if _title == title:
                    scans.append(scan_id)
            start_scan = min(scans)
            end_scan = max(scans)
        return start_scan, end_scan, title

    def get_spectrum(
        self,
        start_scan: Optional[int] = None,
        end_scan: Optional[int] = None,
        centroid: bool = False,
        title: Optional[str] = None,
    ):
        """Retrieve average mass spectrum"""
        if title is None:
            title = "Full MS"
        start_scan, end_scan, title = self._get_scan_parameters(start_scan, end_scan, title)
        average_scan = Extensions.AverageScansInScanRange(self.source, start_scan, end_scan, title)

        if not average_scan.HasCentroidStream:
            raise ValueError("Could not retrieve average scan %d - %d" % (start_scan, end_scan))
        if centroid:
            x = np.asarray(list(average_scan.CentroidScan.Masses))
            y = np.asarray(list(average_scan.CentroidScan.Intensities))
        else:
            x = np.asarray(list(average_scan.SegmentedScan.Positions))
            y = np.asarray(list(average_scan.SegmentedScan.Intensities))
        return x, y

    def get_tic(self):
        """Get total ion current"""
        x, y = self.get_chromatogram()
        return x, y

    def get_chromatogram(self, mz_start=0, mz_end=99999, rt_start=-1, rt_end=-1, title=None):
        """Return extracted chromatogram

        Parameters
        ----------
        mz_start : float
            start m/z value
        mz_end : float
            end m/z value
        rt_start : float
            retention start time in minutes
        rt_end : float
            retention end time in minutes
        title : str
            filter title
        """
        if rt_start != -1:
            rt_start = self.source.ScanNumberFromRetentionTime(rt_start)
        if rt_end != -1:
            rt_end = self.source.ScanNumberFromRetentionTime(rt_end)
        if title is None:
            title = "Full MS"

        # start_scan, stop_scan = list(map(self.scan_from_time, [rt_start, rt_end]))
        settings = ChromatogramTraceSettings(title, [Range.Create(mz_start, mz_end)])
        xic_data = self.source.GetChromatogramData([settings], rt_start, rt_end)
        xic_trace = ChromatogramSignal.FromChromatogramData(xic_data)[0]
        return np.asarray(list(xic_trace.Times)), np.asarray(list(xic_trace.Intensities))
