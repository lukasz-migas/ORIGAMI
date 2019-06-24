# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
#    Copyright (C) 2017-2018 Lukasz G. Migas
#    <lukasz.migas@manchester.ac.uk> OR <lukas.migas@yahoo.com>
#
#      GitHub : https://github.com/lukasz-migas/ORIGAMI
#      University of Manchester IP : https://www.click2go.umip.com/i/s_w/ORIGAMI.html
#      Cite : 10.1016/j.ijms.2017.08.014
#
#    This program is free software. Feel free to redistribute it and/or
#    modify it under the condition you cite and credit the authors whenever
#    appropriate.
#    The program is distributed in the hope that it will be useful but is
#    provided WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE
# -------------------------------------------------------------------------
# __author__ lukasz.g.migas

from utils.multiplierz_lite.mzAPI import raw
import numpy as np
from utils.path import clean_filename


class thermoRAWreader():

    def __init__(self, filename, **kwargs):
        self.filename = filename
        self.source = self.create_parser()
        self.filters = self.source.source.GetAllFilterInfo()

        self.last_scan = 1

    def create_parser(self):
        source = raw.mzFile(self.filename)
        return source

    def get_scan_info(self, rt_start=0, rt_end=None):

        scan_info = {}
        for scan in range(*self.source.scan_range()):
            info = self.source.source.GetFilterInfoForScan(scan)
            ms_level = info[0].upper() if info[0].upper() != 'MS' else 'MS1'
            time = self.source.source.time_from_scan(scan)
            ms_format = 'p' if info[2] == 'Profile' else 'c'
            scan_info[scan] = {'time': time,
                               'precursor_mz': info[1],
                               'ms_level': ms_level,
                               'format': ms_format,
                               'filter': self.filters[scan - 1]}

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
                    'xvals': msX,
                    'yvals': msY,
                    'xlabels': 'm/z (Da)',
                    'xlimits': xlimits,
                    'filter': title}
        return data

    def get_chromatogram_for_each_filter(self):

        unique_filters = set(self.filters)
        data = {}
        for title in unique_filters:
            if title not in ["None", None]:
                rtX, rtY = self.get_xic(title=title)
                xlimits = [np.min(rtX), np.max(rtY)]
                data[clean_filename(title)] = {
                    'xvals': rtX,
                    'yvals': rtY,
                    'xlabels': 'Time (min)',
                    'xlimits': xlimits,
                    'filter': title}
        return data

    def get_spectrum(self):
        pass

    def get_tic(self, return_xy=True):
        tic = np.array(self.source.tic())

        if return_xy:
            return tic[:, 0], tic[:, 1]
        else:
            return tic

    def get_xic(self, mz_start=-1, mz_end=-1, rt_start=-1, rt_end=-1, title=None, return_xy=True):
        xic = np.array(self.source.xic(rt_start, rt_end, mz_start, mz_end, title))

        if return_xy:
            return xic[:, 0], xic[:, 1]
        else:
            return xic

    def _stitch_chromatograms(self, data):
        from natsort import natsorted

        chrom_mins = []
        for key in data:
            chrom_mins.append([data[key]['xvals'][0], data[key]['xvals'][-1], key])

        chrom_mins = natsorted(chrom_mins)

        xvals, yvals = [], []
        for item in chrom_mins:
            rt_start, rt_end, key = item
            xvals.extend(data[key]['xvals'])
            yvals.extend(data[key]['yvals'])

        return xvals, yvals
