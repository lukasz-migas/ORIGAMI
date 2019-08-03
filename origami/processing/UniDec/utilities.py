# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import re
from operator import itemgetter

import numpy as np
import processing.utils as pr_utils
from natsort.natsort import natsorted


def unidec_sort_MW_list(mass_list, column_id):
    """Sort mass list based on MW or %"""

    _mass_list_sort = []
    for item in mass_list:
        item_split = re.split(r"MW: | \(| %\)", item)
        _mass_list_sort.append([item_split[1], item_split[2]])

    _mass_list_sort = natsorted(_mass_list_sort, key=itemgetter(column_id), reverse=True)

    mass_list = []
    for item in _mass_list_sort:
        mass_list.append("MW: {} ({} %)".format(item[0], item[1]))

    return mass_list


def calculate_charge_positions(chargeList, selectedMW, msX, adductIon="H+", remove_below=0.01):

    _adducts = {
        "H+": 1.007276467,
        "H+ Na+": 22.996493,
        "Na+": 22.989218,
        "Na+ x2": 45.978436,
        "Na+ x3": 68.967654,
        "K+": 38.963158,
        "K+ x2": 77.926316,
        "K+ x3": 116.889474,
        "NH4+": 18.033823,
        "H-": -1.007276,
        "Cl-": 34.969402,
    }

    # np.min(self.config.unidec_engine.data.data2[:, 0]), np.max(self.config.unidec_engine.data.data2[:, 0])
    min_mz, max_mz = np.min(msX), np.max(msX)
    charges = np.array(list(map(int, np.arange(chargeList[0, 0], chargeList[-1, 0] + 1))))
    peakpos = (float(selectedMW) + (_adducts[adductIon])) / charges

    ignore = (peakpos > min_mz) & (peakpos < max_mz)
    peakpos, charges, intensity = peakpos[ignore], charges[ignore], chargeList[:, 1][ignore]

    # remove peaks that are of poor intensity
    max_intensity = np.amax(intensity) * remove_below
    ignore = intensity > max_intensity
    peakpos, charges, intensity = peakpos[ignore], charges[ignore], intensity[ignore]

    return peakpos, charges, intensity


def get_peak_maximum(data, xmin=None, xmax=None, xval=None):

    if xmin is None and xmax is None and xval is not None:
        min_difference = np.diff(data[:, 0]).mean()
        xmin = xval - min_difference
        xmax = xval + min_difference

    narrow_data = pr_utils.get_narrow_data_range(data=data, mzRange=(xmin, xmax))
    if len(narrow_data) > 0:
        peak_max = np.round(pr_utils.find_peak_maximum(narrow_data), 4)
    else:
        peak_max = 1

    return peak_max
