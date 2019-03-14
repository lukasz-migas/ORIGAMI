import time

import numpy as np
import pandas as pd

import readers.waters.MassLynxRawChromatogramReader as MassLynxRawChromatogramReader
import readers.waters.MassLynxRawInfoReader as MassLynxRawInfoReader
import readers.waters.MassLynxRawReader as MassLynxScanItem
import readers.waters.MassLynxRawScanReader as MassLynxRawScanReader
from processing.spectra import bin_1D, normalize_1D
from toolbox import str2num


class WatersRawReader():

    def __init__(self, filename, **kwargs):
        tstart = time.time()
        self.filename = filename

        # set parameters
        self.bin_params = kwargs
        self.bin_list = self.create_bin_range()
        self.bin_centres = self.create_bin_centres()

        # create parsers
        self.reader = self.create_file_parser()
        self.info_reader = self.create_info_parser()
        self.data_reader = self.create_data_parser()

        # get parameters
        self.stats_in_functions = self.get_functions_and_stats()

        # setup file mode
        self.instrument_type = self.stats_in_functions[0]['ion_mode']

    def create_file_parser(self):
        return MassLynxRawReader.MassLynxRawReader(self.filename, 1)

    def create_info_parser(self):
        return MassLynxRawInfoReader.MassLynxRawInfoReader(self.reader)

    def create_data_parser(self):
        return MassLynxRawScanReader.MassLynxRawScanReader(self.reader)

    def create_bin_range(self):
        return np.arange(self.bin_params['min_mz'],
                         self.bin_params['max_mz']+self.bin_params['mz_bin'],
                         self.bin_params['mz_bin'])

    def create_bin_centres(self):
        ms_centres = np.arange(self.bin_params['min_mz'],
                               self.bin_params['max_mz']+self.bin_params['mz_bin'],
                               self.bin_params['mz_bin'])[1::]

        return ms_centres - self.bin_params['mz_bin']

    def get_functions_and_stats(self):
        self.n_functions = self.info_reader.GetNumberofFunctions()

        stats_in_functions = {}
        for fcn in range(self.n_functions):
            scans = self.info_reader.GetScansInFunction(fcn)
            mass_range = self.info_reader.GetAcquisitionMassRange(fcn)
            ion_mode = self.info_reader.GetIonModeString(self.info_reader.GetIonMode(fcn))
            fcn_type = self.info_reader.GetFunctionTypeString(self.info_reader.GetFunctionType(fcn))

            stats_in_functions[fcn] = {"n_scans": scans,
                                       "mass_range": mass_range,
                                       "ion_mode": ion_mode,
                                       "fcn_type": fcn_type}

        return stats_in_functions

    def get_scan_headers(self, function, scan):
        # retrieve x and y coordinate
        xpos, ypos = self.info_reader.GetScanItems(function, scan, [9, 10])

        return xpos, ypos

    def get_scan_data(self, function, scan):
        xvals, yvals = self.data_reader.ReadScan(function, scan)

        # linearize and normalize data
        yvals, __ = np.histogram(xvals, bins=self.bin_list, weights=yvals)
        yvals = yvals/np.max(yvals)

        return yvals

    def get_all_scans(self, instrument_type=None):
        if instrument_type is None:
            instrument_type = self.instrument_type

        yvals_summed = np.zeros_like(self.bin_centres)
        zvals_summed = []

        # MALDI
        if instrument_type in ["LDI+", "LDI-"]:
            for fcn in range(self.n_functions):
                for i in range(self.stats_in_functions[fcn]['n_scans']):
                    yvals = self.get_scan_data(fcn, i)
                    xpos, ypos = self.get_scan_headers(fcn, i)
        # DESI
        elif instrument_type in ["ES+", "ES-"]:
            fcn = 0
            n_scans = self.stats_in_functions[fcn]['n_scans']
            ms_DF = np.zeros((n_scans, len(self.bin_centres)))
            msBinDict = dict.fromkeys(list(range(n_scans)))

            for scan in range(self.stats_in_functions[fcn]['n_scans']):
                yvals = self.get_scan_data(fcn, scan)
                xpos, ypos = self.get_scan_headers(fcn, scan)

                ms_DF[int(scan), :] = yvals
                msBinDict[int(scan)] = {'xval': str2num(xpos),
                                        'yval': str2num(ypos)}

                yvals_summed = np.add(yvals, yvals_summed)
                zvals_summed.append(np.sum(yvals))

        print((ms_DF.shape))
        return ms_DF, msBinDict, yvals_summed, zvals_summed
