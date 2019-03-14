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

from pyteomics import mass # @UnresolvedImport
from time import time as ttime
import numpy as np
import re


class PeptideAnnotation():
    def __init__(self, **kwargs):
        
        # list all available peptide fragments
        self._all_ = ["M-all", "a-all", "b-all", "c-all", "x-all", "y-all", "z-all"]
        self._M_all_ = ["M", 
                        "M-H2Ox1", 'M-H2Ox2', 'M-H2Ox3', 'M-H2Ox4', 
                        "M-NH3x1", "M-NH3x2", "M-NH3x3", "M-NH3x4"]
        self._a_all_ = ["a", 
                        "a-H2Ox1", 'a-H2Ox2', 'a-H2Ox3', 'a-H2Ox4', 
                        "a-NH3x1", "a-NH3x2", "a-NH3x3", "a-NH3x4"]
        self._b_all_ =  ["b", 
                         "b-H2Ox1", 'b-H2Ox2', 'b-H2Ox3', 'b-H2Ox4', 
                         "b-NH3x1", "b-NH3x2", "b-NH3x3", "b-NH3x4"]
        self._c_all_ = ["c", 
                        "c-H2Ox1", 'c-H2Ox2', 'c-H2Ox3', 'c-H2Ox4', 
                        "c-NH3x1", "c-NH3x2", "c-NH3x3", "c-NH3x4", 
                        "c-1", "c-dot", "c+1", "c+2"]
        self._x_all_ = ["x", 
                        "x-H2Ox1", "x-H2Ox2", "x-H2Ox3", "x-H2Ox4", 
                        "x-NH3x1", "x-NH3x2", "x-NH3x3", "x-NH3x4"]
        self._y_all_ = ["y", 
                        "y-H2Ox1", "y-H2Ox2", "y-H2Ox3", "y-H2Ox4", 
                        "y-NH3x1", "y-NH3x2", "y-NH3x3", "y-NH3x4"]
        self._z_all_ = ["z", 
                        "z-H2Ox1", "z-H2Ox2", "z-H2Ox3", "z-H2Ox4", 
                        "z-NH3x1", "z-NH3x2", "z-NH3x3", "z-NH3x4", 
                        "z-dot", "z+1", "z+2", "z+3"]
    
        self._all_h2o_loss_ = ["M-H2Ox1", 'M-H2Ox2', 'M-H2Ox3', 'M-H2Ox4', 
                               "a-H2Ox1", 'a-H2Ox2', 'a-H2Ox3', 'a-H2Ox4',
                               "b-H2Ox1", 'b-H2Ox2', 'b-H2Ox3', 'b-H2Ox4', 
                               "c-H2Ox1", 'c-H2Ox2', 'c-H2Ox3', 'c-H2Ox4',
                               "x-H2Ox1", 'x-H2Ox2', 'x-H2Ox3', 'x-H2Ox4', 
                               "y-H2Ox1", 'y-H2Ox2', 'y-H2Ox3', 'y-H2Ox4',
                               "z-H2Ox1", 'z-H2Ox2', 'z-H2Ox3', 'z-H2Ox4']
        self._all_nh3_loss_ = ["M-NH3x1", "M-NH3x2", "M-NH3x3", "M-NH3x4", 
                               "a-NH3x1", "a-NH3x2", "a-NH3x3", "a-NH3x4",
                               "b-NH3x1", "b-NH3x2", "b-NH3x3", "b-NH3x4", 
                               "c-NH3x1", "c-NH3x2", "c-NH3x3", "c-NH3x4",
                               "x-NH3x1", "x-NH3x2", "x-NH3x3", "x-NH3x4", 
                               "y-NH3x1", "y-NH3x2", "y-NH3x3", "y-NH3x4",
                               "z-NH3x1", "z-NH3x2", "z-NH3x3", "z-NH3x4"]
        
        self._all_abc_all_ = self._a_all_ + self._b_all_ + self._c_all_
        self._all_xyz_all_ = self._x_all_ + self._y_all_ + self._z_all_
        
        
        # generate composition map
        self.ion_composition = self.generate_ion_composition_map()
        
        # set label
        self._label_format = kwargs.get("label_format", None)
        
    def get_unimod_db(self):
        self.unimod_db = mass.Unimod()
        
    def set_label_format(self, label_format):
        self._label_format = label_format
    
    def replace_ion_composition_shortcut(self, ion_types):
        
        if "ALL" in ion_types:
            ion_types.extend(self._all_)
            ion_types.remove("ALL")
        
        if "M-all" in ion_types:
            ion_types.extend(self._M_all_)
            ion_types.remove("M-all")
    
        if "a-all" in ion_types:
            ion_types.extend(self._a_all_)
            ion_types.remove("a-all")
    
        if "b-all" in ion_types:
            ion_types.extend(self._b_all_)
            ion_types.remove("b-all")
    
        if "c-all" in ion_types:
            ion_types.extend(self._c_all_)
            ion_types.remove("c-all")
    
        if "x-all" in ion_types:
            ion_types.extend(self._x_all_)
            ion_types.remove("x-all")
    
        if "y-all" in ion_types:
            ion_types.extend(self._y_all_)
            ion_types.remove("y-all")
    
        if "z-all" in ion_types:
            ion_types.extend(self._z_all_)
            ion_types.remove("z-all")
            
        # remove duplicates and return
        return list(set(ion_types))
    
    def generate_ion_composition_map(self):
        ion_comp = mass.std_ion_comp
        # extra M-ions
        ion_comp['M-H2Ox1'] = mass.Composition(formula='H-2O-1')
        ion_comp['M-H2Ox2'] = mass.Composition(formula='H-4O-2')
        ion_comp['M-H2Ox3'] = mass.Composition(formula='H-6O-3')
        ion_comp['M-H2Ox4'] = mass.Composition(formula='H-8O-4')
        
        ion_comp['M-NH3x1'] = mass.Composition(formula='N-1H-3')
        ion_comp['M-NH3x2'] = mass.Composition(formula='N-2H-6')
        ion_comp['M-NH3x3'] = mass.Composition(formula='N-3H-9')
        ion_comp['M-NH3x4'] = mass.Composition(formula='N-4H-12')
        
        # extra a-ions
        ion_comp['a-H2Ox1'] = mass.Composition(formula='H-2O-1' + 'C-1O-1' + 'H-2O-1')
        ion_comp['a-H2Ox2'] = mass.Composition(formula='H-2O-1' + 'C-1O-1' + 'H-4O-2')
        ion_comp['a-H2Ox3'] = mass.Composition(formula='H-2O-1' + 'C-1O-1' + 'H-6O-3')
        ion_comp['a-H2Ox4'] = mass.Composition(formula='H-2O-1' + 'C-1O-1' + 'H-8O-4')
        
        ion_comp['a-NH3x1'] = mass.Composition(formula='H-2O-1' + 'C-1O-1' + 'N-1H-3')
        ion_comp['a-NH3x2'] = mass.Composition(formula='H-2O-1' + 'C-1O-1' + 'N-2H-6')
        ion_comp['a-NH3x3'] = mass.Composition(formula='H-2O-1' + 'C-1O-1' + 'N-3H-9')
        ion_comp['a-NH3x4'] = mass.Composition(formula='H-2O-1' + 'C-1O-1' + 'N-4H-12')
        
        # extra b-ions
        ion_comp['b-H2Ox1'] = mass.Composition(formula='H-2O-1' + 'H-2O-1')
        ion_comp['b-H2Ox2'] = mass.Composition(formula='H-2O-1' + 'H-4O-2')
        ion_comp['b-H2Ox3'] = mass.Composition(formula='H-2O-1' + 'H-6O-3')
        ion_comp['b-H2Ox4'] = mass.Composition(formula='H-2O-1' + 'H-8O-4')
        
        ion_comp['b-NH3x1'] = mass.Composition(formula='H-2O-1' + 'N-1H-3')
        ion_comp['b-NH3x2'] = mass.Composition(formula='H-2O-1' + 'N-2H-6')
        ion_comp['b-NH3x3'] = mass.Composition(formula='H-2O-1' + 'N-3H-9')
        ion_comp['b-NH3x4'] = mass.Composition(formula='H-2O-1' + 'N-4H-12')
        
        # extra c-ions
        ion_comp['c-H2Ox1'] = mass.Composition(formula='H-2O-1' + 'NH3' + 'H-2O-1')
        ion_comp['c-H2Ox2'] = mass.Composition(formula='H-2O-1' + 'NH3' + 'H-4O-2')
        ion_comp['c-H2Ox3'] = mass.Composition(formula='H-2O-1' + 'NH3' + 'H-6O-3')
        ion_comp['c-H2Ox4'] = mass.Composition(formula='H-2O-1' + 'NH3' + 'H-8O-4')
        
        ion_comp['c-NH3x1'] = mass.Composition(formula='H-2O-1' + 'NH3' + 'N-1H-3')
        ion_comp['c-NH3x2'] = mass.Composition(formula='H-2O-1' + 'NH3' + 'N-2H-6')
        ion_comp['c-NH3x3'] = mass.Composition(formula='H-2O-1' + 'NH3' + 'N-3H-9')
        ion_comp['c-NH3x4'] = mass.Composition(formula='H-2O-1' + 'NH3' + 'N-4H-12')
        
        # extra x-ions
        ion_comp['x-H2Ox1'] = mass.Composition(formula='H-2O-1' + 'CO2' + 'H-2O-1')
        ion_comp['x-H2Ox2'] = mass.Composition(formula='H-2O-1' + 'CO2'+ 'H-4O-2')
        ion_comp['x-H2Ox3'] = mass.Composition(formula='H-2O-1' + 'CO2'+ 'H-6O-3')
        ion_comp['x-H2Ox4'] = mass.Composition(formula='H-2O-1' + 'CO2'+ 'H-8O-4')
        
        ion_comp['x-NH3x1'] = mass.Composition(formula='H-2O-1' + 'CO2'+ 'N-1H-3')
        ion_comp['x-NH3x2'] = mass.Composition(formula='H-2O-1' + 'CO2'+ 'N-2H-6')
        ion_comp['x-NH3x3'] = mass.Composition(formula='H-2O-1' + 'CO2'+ 'N-3H-9')
        ion_comp['x-NH3x4'] = mass.Composition(formula='H-2O-1' + 'CO2'+ 'N-4H-12')
        
        # extra b-ions
        ion_comp['y-H2Ox1'] = mass.Composition(formula='H-2O-1')
        ion_comp['y-H2Ox2'] = mass.Composition(formula='H-4O-2')
        ion_comp['y-H2Ox3'] = mass.Composition(formula='H-6O-3')
        ion_comp['y-H2Ox4'] = mass.Composition(formula='H-8O-4')
        
        ion_comp['y-NH3x1'] = mass.Composition(formula='N-1H-3')
        ion_comp['y-NH3x2'] = mass.Composition(formula='N-2H-6')
        ion_comp['y-NH3x3'] = mass.Composition(formula='N-3H-9')
        ion_comp['y-NH3x4'] = mass.Composition(formula='N-4H-12')
        
        # extra z-ions
        ion_comp['z-H2Ox1'] = mass.Composition(formula='H-2O-1' + 'ON-1H-1' + 'H-2O-1')
        ion_comp['z-H2Ox2'] = mass.Composition(formula='H-2O-1' + 'ON-1H-1' + 'H-4O-2')
        ion_comp['z-H2Ox3'] = mass.Composition(formula='H-2O-1' + 'ON-1H-1' + 'H-6O-3')
        ion_comp['z-H2Ox4'] = mass.Composition(formula='H-2O-1' + 'ON-1H-1' + 'H-8O-4')
        
        ion_comp['z-NH3x1'] = mass.Composition(formula='H-2O-1' + 'ON-1H-1' + 'N-1H-3')
        ion_comp['z-NH3x2'] = mass.Composition(formula='H-2O-1' + 'ON-1H-1' + 'N-2H-6')
        ion_comp['z-NH3x3'] = mass.Composition(formula='H-2O-1' + 'ON-1H-1' + 'N-3H-9')
        ion_comp['z-NH3x4'] = mass.Composition(formula='H-2O-1' + 'ON-1H-1' + 'N-4H-12')
        
        return ion_comp
    
    def count_sequence_letters(self, peptide, amino_acids):
        
        count = 0
        for aa in peptide:
            if aa in amino_acids:
                count += 1
                
        return count
        
    def check_peptide_rules(self, ion_type, peptide):
        """
        Check against common rulebook to ensure 'silly' fragments are not produced
        """
        # only consider peptides with S, T, E, D amino acids
        if ion_type in self._all_h2o_loss_:
            if re.search('[STED]', peptide):
                aa_count = self.count_sequence_letters(peptide, "STED")
                if "x1" in ion_type and aa_count >= 1: return True
                elif "x2" in ion_type and aa_count >= 2: return True
                elif "x3" in ion_type and aa_count >= 3: return True
                elif "x4" in ion_type and aa_count >= 4: return True
                else: return False
                
        # only consider peptides with R, K, Q, N amino acids
        elif ion_type in self._all_nh3_loss_:
            if re.search('[RKQN]', peptide):
                aa_count = self.count_sequence_letters(peptide, "RKQN")
                if "x1" in ion_type and aa_count >= 1: return True
                elif "x2" in ion_type and aa_count >= 2: return True
                elif "x3" in ion_type and aa_count >= 3: return True
                elif "x4" in ion_type and aa_count >= 4: return True
                else: return False
        else:
            return True
            
    def add_modification_composition(self, modification_dict):
        
        for i in modification_dict:
            modification = modification_dict[i]["name"]
            
            # check if modification already present
            if modification in list(self.ion_composition.keys()):
                continue
            
            # try retrieving modification information
            try:
                unimod = self.unimod_db.by_title(modification, True)
            except AttributeError:
                self.get_unimod_db()
                unimod = self.unimod_db.by_title(modification, True)
            
            # update ion composition dictionary
            self.ion_composition[modification] = unimod['composition']
    
    def check_modification(self, seq_id, peptide_seq, modification_dict):
        
        mod_peptide_seq = peptide_seq
        modification_mass = 0
        for mod_id in modification_dict:
            mod_location = modification_dict[mod_id]['location']
            mod_name = modification_dict[mod_id]['name']
            if seq_id >= mod_location:
                for res_id in modification_dict[mod_id]['residues']:
                    if res_id in peptide_seq:
                        mod_peptide_seq = peptide_seq[:mod_location] + mod_name + peptide_seq[mod_location:]
                        modification_mass = modification_dict[mod_id]['mass_delta']
        
        return mod_peptide_seq, modification_mass
                        
    def generate_fragments_from_peptide(self, peptide, ion_types, label_format={},
        min_charge=1, max_charge=1, aa_mass_dict=None, polarity="+", ion_composition=None, 
        modification_dict={}, verbose=False):
        
        tstart = ttime()
        
        # specify charges
        if min_charge < 1:
            min_charge = 1
        
        if max_charge < min_charge:
            max_charge, min_charge = min_charge, max_charge
            
#         # update ion composition obj
        include_modifications = False
        if len(modification_dict) > 0:
            include_modifications = True
#             self.add_modification_composition(modification_dict)
            
        # determine ion composition
        if ion_composition is None:
            ion_composition = self.ion_composition
            
        # make backup of peptide sequence
        _peptide = peptide
            
        # check if shortcuts were used
        ion_types = self.replace_ion_composition_shortcut(ion_types)

        fragment_dict = {}
        for ion_type in ion_types:
            if ion_type in [self._M_all_]:
                peptide = _peptide
                for charge in range(min_charge, max_charge+1):
                    ion_mz = mass.fast_mass(
                        peptide, ion_type=ion_type, charge=charge, ion_comp=ion_composition)
                    
                    ion_label = "{}{}{}".format(ion_type, polarity, charge)
                    fragment_dict[ion_label] = {'mz':ion_mz, 'z':charge, 'seq':peptide}
                    
            if ion_type in self._all_abc_all_:
                peptide = _peptide
                if not self.check_peptide_rules(ion_type, peptide): 
                    continue
                for i in range(1, len(peptide)):
                    peptide_seq = peptide[:i]
                    if not self.check_peptide_rules(ion_type, peptide_seq):
                        continue
                    mod_peptide_seq, modification_mass = peptide_seq, 0 
                    if include_modifications:
                        mod_peptide_seq, modification_mass = self.check_modification(i, peptide_seq, modification_dict)
                    
                    for charge in range(min_charge, max_charge+1):
                        ion_mz = mass.fast_mass(
                            peptide_seq, ion_type=ion_type, charge=charge, ion_comp=ion_composition)
                        
                        ion_mz = ion_mz + (modification_mass / charge)
                        
                        ion_label, ion_label_full = self.generate_label(
                            ion_type[0], i, polarity, charge, mod_peptide_seq)
                        fragment_dict[ion_label_full] = {
                            'mz':ion_mz, 'z':charge, 'seq':peptide_seq, 'full_label':ion_label_full, 'label':ion_label}
                        
            if ion_type in self._all_xyz_all_:
                peptide = _peptide#[::-1] 
                if not self.check_peptide_rules(ion_type, peptide):
                    continue
                # generate list of inverse fragment numbers
                _frag_label_length = np.arange(len(peptide), 0, -1)
                # iterate over peptide length
                for i in range(1, len(peptide)): 
                    peptide_seq = peptide[i:]
                    if not self.check_peptide_rules(ion_type, peptide_seq):
                        continue
                    mod_peptide_seq, modification_mass = peptide_seq, 0 
                    if include_modifications:
                        mod_peptide_seq, modification_mass = self.check_modification(i+1, peptide_seq, modification_dict)
                    
                    for charge in range(min_charge, max_charge+1):
                        ion_mz = mass.fast_mass(
                            peptide_seq, ion_type=ion_type, charge=charge, ion_comp=ion_composition)
                        
                        # modify ion mass with modification mass
                        ion_mz = ion_mz + (modification_mass / charge)
                        
                        # generate label
                        ion_label, ion_label_full = self.generate_label(
                            ion_type[0], _frag_label_length[i], polarity, charge, mod_peptide_seq, full_ion_type=ion_type)
                        
                        fragment_dict[ion_label_full] = {
                            'mz':ion_mz, 'z':charge, 'seq':mod_peptide_seq, 'full_label':ion_label_full, 'label':ion_label}
                        
        # print verbose information            
        if verbose:
            msg = "Peptide length: {} | # Fragments: {} | Time to generate: {:.4f}".format(
                len(peptide), len(fragment_dict), ttime()-tstart)
            print(msg)
            
        return fragment_dict
    
    def generate_label(self, frag_name, idx, polarity, charge, sequence, 
                       full_ion_type=None, **kwargs):
        """
        Generate consistent fragment labels
        """
        label = ""
        
        if full_ion_type is None or full_ion_type in "abcxyz<":
            full_ion_type = ""
        else:
            full_ion_type = "_{}".format(full_ion_type[2::])
        
        # return default if nothing is specified
        if self._label_format is None:
            label = "{}{}{}{}".format(frag_name, idx, polarity, charge)
            label_full = "{}{}{}{}{}".format(frag_name, idx, full_ion_type, polarity, charge)
            return label, label_full
            
        # add fragment name
        if self._label_format['fragment_name']:
            label = "{}{}".format(frag_name, idx)
            label_full = "{}{}{}".format(frag_name, idx, full_ion_type)
        # add charge
        if self._label_format['charge']:
            label = "{}{}{}".format(label, polarity, charge)
            label_full = "{}{}{}".format(label_full, polarity, charge)
        # add peptide sequence
        if self._label_format['peptide_seq']:
            if label == "": 
                label = "{}".format(sequence)
                label_full = "{}".format(sequence)
            else: 
                label = "{}, {}".format(label, sequence)
                label_full = "{}, {}".format(label_full, sequence)
            
        return label, label_full
            
    def find_n_nearest(self, value, array, n_nearest=1):
        idx = np.argpartition(np.abs(array-value), n_nearest)
        idx = idx[0:n_nearest]
        return array[idx], idx
    
    def get_fragment_mass_list(self, fragment_dict):
        
        frag_mass_list, frag_name_list, frag_charge_list, frag_peptide_list, frag_full_name_list = [], [], [], [], []
        for frag in fragment_dict:
            frag_mass_list.append(fragment_dict[frag]['mz'])
            frag_name_list.append(fragment_dict[frag].get('label', frag))
            frag_charge_list.append(fragment_dict[frag]['z'])
            frag_peptide_list.append(fragment_dict[frag]['seq'])
            frag_full_name_list.append(fragment_dict[frag]['full_label'])
            
        # convert to arrays
        frag_mass_list = np.array(frag_mass_list)
        frag_name_list = np.array(frag_name_list)
        frag_charge_list = np.array(frag_charge_list)
        frag_peptide_list = np.array(frag_peptide_list)
        frag_full_name_list = np.array(frag_full_name_list)
        
        return frag_mass_list, frag_name_list, frag_charge_list, frag_peptide_list, frag_full_name_list
    
    def match_peaks(self, peaklist, peakints, fragment_mass_list, fragment_name_list, 
                    fragment_charge_list, fragment_peptide_list, frag_full_name_list,
                    tolerance=0.01, tolerance_units="Da", max_found=1, verbose=False, **kwargs):
        tstart = ttime()
        found_peaks = {}
        _more_than_one_peak_ = 0
        for measured_mz, measured_int in zip(peaklist, peakints):
            found_peaks_list = []
            calculated_mzs, idxs  = self.find_n_nearest(measured_mz, fragment_mass_list, max_found)
            for calculated_mz, idx in zip(calculated_mzs, idxs):
                delta_mz = np.round(np.abs(np.subtract(measured_mz, calculated_mz)), 4)
                
                # convert error to ppm
                if tolerance_units == "ppm":
                    delta_mz = self.convert_Da_to_ppm(measured_mz, delta_mz)
                
                # check and add to annotation list
                if delta_mz <= tolerance:
                    found_peaks_list.append({'measured_mz':measured_mz, 
                                             'measured_int':measured_int,
                                             'calculated_mz':calculated_mz, 
                                             'delta_mz':delta_mz, 
                                             'label':fragment_name_list[idx],
                                             'full_label':frag_full_name_list[idx],
                                             'peptide':fragment_peptide_list[idx],
                                             'charge':fragment_charge_list[idx]})
            if len(found_peaks_list) > 0:
                if len(found_peaks_list) > 1:
                    print(found_peaks_list)
                    _more_than_one_peak_ += 1
                found_peaks[measured_mz] = found_peaks_list
                
#         if verbose:
        msg = "Found {} ({} > 1 labels) matches with {} {} tolerance | Time to search: {:.4f}".format(
            len(found_peaks), _more_than_one_peak_, tolerance, tolerance_units, ttime()-tstart)
        print(msg)
            
        return found_peaks
    
    def get_fragment_lists(self, fragment_dict, get_calculated_mz=False):

        frag_mass_list, frag_int_list, frag_label_list, frag_full_label_list = [], [], [], []
        for frag in fragment_dict:
            for annot in range(len(fragment_dict[frag])):
                if get_calculated_mz:
                    frag_mass_list.append(fragment_dict[frag][annot]['calculated_mz'])
                else:
                    frag_mass_list.append(fragment_dict[frag][annot]['measured_mz'])
                frag_int_list.append(fragment_dict[frag][annot]['measured_int'])
                frag_label_list.append(fragment_dict[frag][annot]['label'])
                frag_full_label_list.append(fragment_dict[frag][annot]['full_label'])
        
        return frag_mass_list, frag_int_list, frag_label_list, frag_full_label_list
        
    def convert_Da_to_ppm(self, value, delta_value):
        value_out = 1000000 * delta_value/value
        return value_out
    
    
    
    
    
    
    
    
    
    
    
    
    