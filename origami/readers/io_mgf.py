# Standard library imports

# Third-party imports
import numpy as np
from pyteomics import mgf


class MGFReader:
    def __init__(self, filename):
        self.filename = filename
        self.source = self.create_parser()
        self.last_scan = 1

    def create_parser(self):
        return mgf.read(self.filename, convert_arrays=1, use_header=False)

    def get_all_titles(self):
        scan_info = dict()
        for scan, spectrum in enumerate(self.source):
            scan_info[scan] = spectrum["params"]["title"]

        return scan_info

    @staticmethod
    def get_title_from_scan(scan):
        return scan["params"]["title"]

    def get_all_info(self):
        scan_info = dict()
        for scan, spectrum in enumerate(self.source):
            scan_info[scan] = {
                "title": spectrum["params"]["title"],
                "precursor_mz": np.round(spectrum["params"]["pepmass"][0], 4),
                "precursor_charge": spectrum["params"]["charge"],
                "peak_count": len(spectrum["m/z array"]),
            }

        return scan_info

    @staticmethod
    def get_info_from_scan(scan):
        return {
            "title": scan["params"]["title"],
            "precursor_mz": np.round(scan["params"]["pepmass"][0], 4),
            "precursor_charge": scan["params"].get("charge", 1),
            "peak_count": len(scan["m/z array"]),
        }

    def get_all_scans(self):
        self.reset()

        data = dict()
        for scan, spectrum in enumerate(self.source):
            xvals, yvals, charges = self.get_spectrum_from_scan(spectrum, "1D")
            scan_info = self.get_info_from_scan(spectrum)
            data["Scan {}".format(scan)] = {"xvals": xvals, "yvals": yvals, "charges": charges, "scan_info": scan_info}

        return data

    def get_n_scans(self, n_scans):
        data = dict()
        scan_n = 0
        for scan in range(n_scans):
            try:
                spectrum = next(self.source)
            except StopIteration:
                self.last_scan = scan + self.last_scan - 1
                return data
            scan_n = scan + self.last_scan
            xvals, yvals, charges = self.get_spectrum_from_scan(spectrum, "1D")
            scan_info = self.get_info_from_scan(spectrum)
            data["Scan {}".format(scan_n)] = {
                "xvals": xvals,
                "yvals": yvals,
                "charges": charges,
                "scan_info": scan_info,
            }

        self.last_scan = scan_n
        return data

    def add_n_scans(self, data, n_scans):
        scan_n = 0
        for scan in range(n_scans):
            try:
                spectrum = next(self.source)
            except StopIteration:
                self.last_scan = scan + self.last_scan - 1
                return data
            scan_n = scan + self.last_scan
            xvals, yvals, charges = self.get_spectrum_from_scan(spectrum, "1D")
            scan_info = self.get_info_from_scan(spectrum)
            data["Scan {}".format(scan_n)] = {
                "xvals": xvals,
                "yvals": yvals,
                "charges": charges,
                "scan_info": scan_info,
            }

        self.last_scan = scan_n
        return data

    def get_spectrum_from_scan(self, scan, mode="2D"):
        xvals, yvals, charges = scan["m/z array"], scan["intensity array"], scan["charge array"]

        if mode == "1D":
            return xvals, yvals, charges
        else:
            lines = []
            for i in range(len(xvals)):
                pair = [(xvals[i], 0), (xvals[i], yvals[i])]
                lines.append(pair)

            return lines

    def get_scan_by_title(self, title):
        return self.source.get_spectrum(title)

    def reset(self):
        self.source.reset()
        self.last_scan = 1

    def create_title_map(self, data):

        index_dict = {}
        for key in data:
            title = data[key]["scan_info"]["title"]
            index_dict[title] = key

        return index_dict
