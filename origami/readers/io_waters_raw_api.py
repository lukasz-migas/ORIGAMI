# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import numpy as np
import readers.waters.MassLynxRawChromatogramReader as MassLynxRawChromatogramReader
import readers.waters.MassLynxRawInfoReader as MassLynxRawInfoReader
import readers.waters.MassLynxRawReader as MassLynxRawReader
import readers.waters.MassLynxRawScanReader as MassLynxRawScanReader
from scipy.interpolate import interpolate


class WatersRawReader():

    def __init__(self, filename, **kwargs):
        self.filename = filename

        # create parsers
        self.reader = self.create_file_parser()
        self.info_reader = self.create_info_parser()
        self.data_reader = self.create_data_parser()
        self.chrom_reader = self.create_chrom_parser()

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

    def create_chrom_parser(self):
        return MassLynxRawChromatogramReader.MassLynxRawChromatogramReader(self.reader)

    def get_functions_and_stats(self):
        self.n_functions = self.info_reader.GetNumberofFunctions()

        stats_in_functions = {}
        for fcn in range(self.n_functions):
            scans = self.info_reader.GetScansInFunction(fcn)
            mass_range = self.info_reader.GetAcquisitionMassRange(fcn)
            ion_mode = self.info_reader.GetIonModeString(self.info_reader.GetIonMode(fcn))
            fcn_type = self.info_reader.GetFunctionTypeString(self.info_reader.GetFunctionType(fcn))

            stats_in_functions[fcn] = {
                'n_scans': scans,
                'mass_range': mass_range,
                'ion_mode': ion_mode,
                'fcn_type': fcn_type,
            }

        return stats_in_functions

    def check_fcn(self, fcn):
        found_fcn = True
        if fcn not in self.stats_in_functions:
            found_fcn = False

        return found_fcn

    def find_minimum_mz_spacing(self, fcn, n_scans, n_max_scans=500):
        if not self.check_fcn(fcn):
            raise ValueError(f'Function {fcn} could not be found in the file.')

        mz_spacing_diff = np.zeros((0,))
        if n_scans > n_max_scans:
            n_scans = n_max_scans

        for i in range(n_scans):
            xvals, __ = self.data_reader.ReadScan(fcn, i)
            mz_spacing_diff = np.append(mz_spacing_diff, np.diff(xvals))
        return np.min(mz_spacing_diff)

    def generate_mz_interpolation_range(self, fcn):
        if not self.check_fcn(fcn):
            raise ValueError(f'Function {fcn} could not be found in the file.')

        mass_range = self.stats_in_functions[fcn]['mass_range']
        n_scans = self.stats_in_functions[fcn]['n_scans']
        mz_spacing = self.find_minimum_mz_spacing(fcn, n_scans)
        mz_x = np.arange(mass_range[0], mass_range[1], mz_spacing)

        self.mz_spacing = mz_spacing
        self.mz_x = mz_x

        return mz_spacing, mz_x

    def get_summed_spectrum(self, fcn, n_scans, mz_x, scan_list=None):
        if not self.check_fcn(fcn):
            raise ValueError(f'Function {fcn} could not be found in the file.')

        if scan_list is None:
            scan_list = range(n_scans)

        if len(scan_list) == 0:
            raise ValueError('Scan list is empty')

        mz_y = np.zeros_like(mz_x, dtype=np.float64)
        for scan_id in scan_list:
            xvals, yvals = self.data_reader.ReadScan(fcn, scan_id)
            xvals = np.array(xvals)
            yvals = np.array(yvals)
            if len(xvals) > 0:
                f = interpolate.interp1d(xvals, yvals, 'linear', bounds_error=False, fill_value=0)
                mz_y += f(mz_x)

        return mz_y

    def get_TIC(self, fcn):
        tic_x, tic_y = self.chrom_reader.ReadTIC(fcn)
        return tic_x, tic_y

    def get_BPI(self, fcn):
        bpi_x, bpi_y = self.chrom_reader.ReadBPI(fcn)
        return bpi_x, bpi_y

    def get_chromatogram(self, mz_values, tolerance=0.05):
        if not isinstance(mz_values):
            mz_values = [mz_values]

        rt_x, rt_ys = self.chrom_reader.ReadMassChromatograms(
            0, mz_values, tolerance, 0,
        )

        return rt_x, rt_ys

    def get_mobilogram(self, mz_values, tolerance=0.05):
        """Same as `get_chromatogram` but using function 1"""
        if not isinstance(mz_values):
            mz_values = [mz_values]

        dt_x, dt_ys = self.chrom_reader.ReadMassChromatograms(
            1, mz_values, tolerance, 0,
        )

        return dt_x, dt_ys
