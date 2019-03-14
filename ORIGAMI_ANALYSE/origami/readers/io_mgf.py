# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
#    Copyright (C) 2017-2018 Lukasz G. Migas 
#    <lukasz.migas@manchester.ac.uk> OR <lukas.migas@yahoo.com>
# 
#	 GitHub : https://github.com/lukasz-migas/ORIGAMI
#	 University of Manchester IP : https://www.click2go.umip.com/i/s_w/ORIGAMI.html
#	 Cite : 10.1016/j.ijms.2017.08.014
#
#    This program is free software. Feel free to redistribute it and/or 
#    modify it under the condition you cite and credit the authors whenever 
#    appropriate. 
#    The program is distributed in the hope that it will be useful but is 
#    provided WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE
# -------------------------------------------------------------------------
# __author__ lukasz.g.migas

import pyteomics  # @UnresolvedImport
from pyteomics import mgf  # @UnresolvedImport
from collections import OrderedDict 
import numpy as np

class MGFreader():
    def __init__(self, filename, **kwargs):
        self.filename = filename
        self.source = self.create_parser()
        self.last_scan = 1
        
    def create_parser(self):
        return mgf.read(self.filename, convert_arrays=1, use_header=False)
    
    def get_all_titles(self):
        scan_info = dict()
        for scan, spectrum in enumerate(self.source):
            scan_info[scan] = spectrum['params']['title']
            
        return scan_info
    
    def get_title_from_scan(self, scan):
        return scan['params']['title']
            
    def get_all_info(self):
        scan_info = dict()
        for scan, spectrum in enumerate(self.source):
            scan_info[scan] = {'title':spectrum['params']['title'],
                               'precursor_mz':np.round(spectrum['params']['pepmass'][0], 4),
                               'precursor_charge':spectrum['params']['charge'],
                               'peak_count':len(spectrum['m/z array'])}
            
        return scan_info
    
    def get_info_from_scan(self, scan):
        return {'title':scan['params']['title'],
                'precursor_mz':np.round(scan['params']['pepmass'][0], 4),
                'precursor_charge':scan['params']['charge'],
                'peak_count':len(scan['m/z array'])}
    
    def get_all_scans(self):
        self.reset()
        
        data = OrderedDict()
        for scan, spectrum in enumerate(self.source):
            xvals, yvals, charges = self.get_spectrum_from_scan(spectrum, "1D")
            scan_info = self.get_info_from_scan(spectrum)
            data["Scan {}".format(scan)] = {'xvals':xvals, 'yvals':yvals, 'charges':charges,
                                            'scan_info':scan_info}
            
        return data
            
    def get_n_scans(self, n_scans):
        data = OrderedDict()
        for scan in range(n_scans):
            try:
                spectrum = next(self.source)
            except StopIteration:
                self.last_scan = scan + self.last_scan - 1
                return data
            scan_n = scan + self.last_scan
            xvals, yvals, charges = self.get_spectrum_from_scan(spectrum, "1D")
            scan_info = self.get_info_from_scan(spectrum)
            data["Scan {}".format(scan_n)] = {'xvals':xvals, 'yvals':yvals, 'charges':charges,
                                              'scan_info':scan_info}
            
        self.last_scan = scan_n
        return data
    
    def add_n_scans(self, data, n_scans):
        for scan in range(n_scans):
            try:
                spectrum = next(self.source)
            except StopIteration:
                self.last_scan = scan + self.last_scan - 1
                return data
            scan_n = scan + self.last_scan
            xvals, yvals, charges = self.get_spectrum_from_scan(spectrum, "1D")
            scan_info = self.get_info_from_scan(spectrum)
            data["Scan {}".format(scan_n)] = {'xvals':xvals, 'yvals':yvals, 'charges':charges,
                                              'scan_info':scan_info}
            
        self.last_scan = scan_n
        return data
        
    def get_spectrum_from_scan(self, scan, mode="2D"):
        xvals, yvals, charges = scan['m/z array'], scan['intensity array'], scan['charge array']
        
        if mode == "1D":
            return xvals, yvals, charges
        else:
            lines = []
            for i in range(len(xvals)):
                pair=[(xvals[i],0), (xvals[i], yvals[i])]
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
            title = data[key]['scan_info']['title']
            index_dict[title] = key

        return index_dict    