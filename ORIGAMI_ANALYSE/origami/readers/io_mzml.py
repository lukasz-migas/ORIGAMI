# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
#    Copyright (C) 2017-2018 Lukasz G. Migas 
#    <lukasz.migas@manchester.ac.uk> OR <lukas.migas@yahoo.com>
# 
#     GitHub : https://github.com/lukasz-migas/ORIGAMI
#     University of Manchester IP : https://www.click2go.umip.com/i/s_w/ORIGAMI.html
#     Cite : 10.1016/j.ijms.2017.08.014
#
#    This program is free software. Feel free to redistribute it and/or 
#    modify it under the condition you cite and credit the authors whenever 
#    appropriate. 
#    The program is distributed in the hope that it will be useful but is 
#    provided WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE
# -------------------------------------------------------------------------
# __author__ lukasz.g.migas

from pymzml import run as pymzml_run #@UnresolvedImport
from collections import OrderedDict 
import numpy as np

class mzMLreader():
    def __init__(self, filename, **kwargs):
        self.filename = filename
        self.source = self.create_parser()
        self.last_scan = 1
        
    def create_parser(self):
        return pymzml_run.Reader(self.filename)
    
    def reset(self):
        self.source = pymzml_run.Reader(self.filename)
        self.last_scan = 1

    def get_spectrum_from_scan(self, scan, mode="2D"):
        xvals, yvals, charges = scan.mz, scan.i, np.zeros_like(scan.i)
        
        if mode == "1D":
            return xvals, yvals, charges
        else:
            lines = []
            for i in range(len(xvals)):
                pair=[(xvals[i],0), (xvals[i], yvals[i])]
                lines.append(pair)

            return lines
        
    def get_info_from_scan(self, scan):
        precursor_mz = np.round(scan['selected ion m/z'], 4)
        try: charge = int(scan['charge state'])
        except: charge = 0
        title = scan.get('spectrum title', "")
        if title in [None, "None"]:
            title = "Scan={}".format(scan.ID)
        
        return {'title':title, 
                'precursor_mz':precursor_mz,
                'precursor_charge':charge,
                'peak_count':len(scan.i)}    

    def get_n_scans(self, n_scans):
        data = OrderedDict()
        for scan in xrange(n_scans):
            try: 
                spectrum = next(self.source)
            except StopIteration:
                self.last_scan = scan + self.last_scan - 1
                return data
            scan_n = scan + self.last_scan
            # check if its MSn type
            if spectrum['ms level'] != 2:
                continue
            xvals, yvals, charges = self.get_spectrum_from_scan(spectrum, "1D")
            scan_info = self.get_info_from_scan(spectrum)
            data["Scan {}".format(scan_n)] = {'xvals':xvals, 'yvals':yvals, 'charges':charges,
                                              'scan_info':scan_info}

            
        self.last_scan = scan_n
        return data
    