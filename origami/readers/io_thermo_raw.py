# isort:skip_file
# Standard library imports
import os
import sys
from typing import Optional
import logging

import clr
import numpy as np

# Local imports
from origami.objects.containers import ChromatogramObject, MassSpectrumObject

# from origami.utils.path import clean_filename
# from origami.utils.check import check_value_order

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


DEFAULT_FILTER = "Full MS"
LOGGER = logging.getLogger(__name__)


class ThermoRawReader:
    def __init__(self, path):
        self.path = path
        self.source = self.create_parser()
        self._unique_filters = self.filter_list()
        self._scan_filters = self._collect_filters()
        self.last_scan = 1
        self._rt_min = None
        self.mz_min, self.mz_max = self.mass_range

    def __repr__(self):
        return f"{self.__class__.__name__}<path={self.path}; m/z range={self.mz_min:.2f}-{self.mz_max:.2f}>"

    def __getitem__(self, item):
        """Retrieve mass spectrum for indexed filter"""
        if isinstance(item, int):
            title = self._unique_filters[item]
        elif isinstance(item, str):
            self._check_filter(item)
            title = item
        else:
            raise ValueError("Not sure how to process the request! Try using `scan_id` or `filter` values")
        LOGGER.debug(f"Getting mass spectrum for {title} filter")
        return self.get_spectrum(title=title)

    def __del__(self):
        self.close()

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

    def n_filters(self):
        """Returns the number of filters in the file"""
        return len(self._unique_filters)

    def n_scans(self):
        """Returns the number of scans in the file"""
        return self.scan_range[-1]

    def create_parser(self):
        """Create parser"""
        source = RawFileReaderAdapter.FileFactory(self.path)
        if source.InstrumentCount > 1:
            LOGGER.warning("This file has multiple files present - only one is allowed at the moment")
        source.SelectInstrument(Device.MS, 1)
        return source

    def close(self):
        """Close file"""
        self.source.Dispose()

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

    def get_filter_by_idx(self, index):
        if index >= self.n_filters():
            raise IndexError(f"Index `{index}` is larger than the maximum number of filters ({self.n_filters()}")
        return self._unique_filters[index]

    def get_scan_info(self, rt_start=None, rt_end=None):

        _scan_range = self.scan_range
        if rt_start is None:
            rt_start = _scan_range[0]
        if rt_end is None or rt_end > _scan_range[1]:
            rt_end = _scan_range[1]

        scan_dict = {}
        for scan_id in range(rt_start, rt_end + 1):
            info = self.source.GetFilterForScanNumber(scan_id)
            ms_level = "MS%d" % info.MSOrder
            mz = 0.0
            if ms_level != "MS1":
                mz = info.GetMass(0)  # I guess >0 is for MS3 etc?
            time = self.source.RetentionTimeFromScanNumber(scan_id)
            scan_info = self.source.GetScanStatsForScanNumber(scan_id)
            ms_format = "c" if scan_info.IsCentroidScan else "p"
            scan_dict[scan_id] = {
                "time": time,
                "precursor_mz": mz,
                "ms_level": ms_level,
                "format": ms_format,
                "filter": IScanFilter(info).ToString(),
            }
        return scan_dict

    def get_spectrum_for_each_filter(self):

        unique_filters = set(self._scan_filters)
        data = {}
        for title in unique_filters:
            if title not in ["None", None]:
                data[title] = self.get_spectrum(title=title)
        return data

    def get_chromatogram_for_each_filter(self):
        unique_filters = set(self._scan_filters)
        data = {}
        for title in unique_filters:
            if title not in ["None", None]:
                data[title] = self.get_chromatogram(title=title)
        return data

    def _get_spectrum(self, scan_id, centroid: bool = False):
        """Retrieve scan data"""
        if scan_id > self.n_scans() or scan_id < 1:
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

    def get_spectrum(
        self,
        start_scan: Optional[int] = None,
        end_scan: Optional[int] = None,
        centroid: bool = False,
        title: Optional[str] = None,
    ):
        """Get average mass spectrum for particular scan range

        Parameters
        ----------
        start_scan : int
            retention start time in scans
        end_scan : int
            retention end time in scans
        centroid : bool
            if `True`, centroid mass spectrum will be returned instead of profile
        title : str
            filter title
        """
        if title is None:
            title = DEFAULT_FILTER
        start_scan, end_scan, title = self._get_scan_parameters(start_scan, end_scan, title)
        average_scan = Extensions.AverageScansInScanRange(self.source, start_scan, end_scan, title)

        if average_scan is None or not average_scan.HasCentroidStream:
            raise ValueError("Could not retrieve average scan %d - %d" % (start_scan, end_scan))
        if centroid:
            x = np.asarray(list(average_scan.CentroidScan.Masses))
            y = np.asarray(list(average_scan.CentroidScan.Intensities))
        else:
            x = np.asarray(list(average_scan.SegmentedScan.Positions))
            y = np.asarray(list(average_scan.SegmentedScan.Intensities))
        return MassSpectrumObject(
            x, y, metadata={"filter": title, "start_scan": int(start_scan), "end_scan": int(end_scan)}
        )

    def get_tic(self):
        """Get total ion current"""
        return self.get_chromatogram()

    def get_chromatogram(self, mz_start=0, mz_end=99999, rt_start=-1, rt_end=-1, title=None, rt_as_scan: bool = False):
        """Return extracted chromatogram

        Parameters
        ----------
        mz_start : float
            start m/z value
        mz_end : float
            end m/z value
        rt_start : Union[int, float]
            retention start time in minutes
        rt_end : Union[int, float]
            retention end time in minutes
        title : str
            filter title
        rt_as_scan : bool
            if `True`, the function will accept scans to be provided as scan numbers
        """
        if rt_start != -1:
            if not rt_as_scan:
                rt_start = self.source.ScanNumberFromRetentionTime(rt_start)
        if rt_end != -1:
            if not rt_as_scan:
                rt_end = self.source.ScanNumberFromRetentionTime(rt_end)
        if mz_start == -1:
            mz_start = 0
        if mz_end == -1:
            mz_end = 99999
        if title is None:
            title = DEFAULT_FILTER

        start_scan, end_scan, title = self._get_scan_parameters(rt_start, rt_end, title)
        settings = ChromatogramTraceSettings(title, [Range.Create(mz_start, mz_end)])
        xic_data = self.source.GetChromatogramData([settings], start_scan, end_scan)
        xic_trace = ChromatogramSignal.FromChromatogramData(xic_data)[0]
        return ChromatogramObject(
            np.asarray(list(xic_trace.Times)),
            np.asarray(list(xic_trace.Intensities)),
            x_label="Retention time (min)",
            metadata={"filter": title, "start_scan": int(start_scan), "end_scan": int(end_scan)},
        )

    def _check_filter(self, title):
        """Checks whether requested filter exists"""
        if title != DEFAULT_FILTER and title not in self._unique_filters:
            filter_fmt = "\n".join(self._unique_filters)
            raise ValueError(f"Filter `{title}` was not recorded. Try any of these instead: \n{filter_fmt}")

    def _get_scan_parameters(
        self, start_scan: Optional[int] = None, end_scan: Optional[int] = None, title: Optional[str] = None
    ):
        """Retrieve scan information for defined range"""

        def check_scan(value, min_value, max_value, default_value):
            """Checks against values present in the filter"""
            if value is None or value == -1:
                return default_value
            if value < min_value:
                raise ValueError(
                    f"Scan number {value} does not belong to this filter. Try between {min_value}-{max_value}"
                )
            if value > max_value:
                raise ValueError(
                    f"Scan number {value} does not belong to this filter. Try between {min_value}-{max_value}"
                )
            return value

        # user provided title/filter
        _start_scan, _end_scan = self.scan_range
        if title:
            self._check_filter(title)
            # using default filter so all scans
            if title == DEFAULT_FILTER:
                _start_scan, _end_scan = self.scan_range
            else:
                scans = []
                for scan_id, _title in enumerate(self._scan_filters, start=1):
                    if _title == title:
                        scans.append(scan_id)
                _start_scan = np.min(scans)
                _end_scan = np.max(scans)
            start_scan = check_scan(start_scan, _start_scan, _end_scan, _start_scan)
            end_scan = check_scan(end_scan, _start_scan, _end_scan, _end_scan)
        # # user provided start/end regions in the chromatogram
        # elif start_scan is not None and end_scan is not None:
        #     start_scan, end_scan = check_value_order(start_scan, end_scan)
        #     if start_scan < _start_scan:
        #         start_scan = _start_scan
        #     if end_scan > _end_scan:
        #         end_scan = _end_scan
        return start_scan, end_scan, title
