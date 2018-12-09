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

from pyteomics import mzid # @UnresolvedImport
import zipfile, os, gzip


class MZIdentReader():
    def __init__(self, filename, **kwargs):
        
        if filename.endswith('.gz') or filename.endswith('.zip'):
            self.filename = self.extract_file(filename)
        else:
            self.filename = filename
        self.source = self.create_parser()
        self.index_dict = {}
        self.index_dict_num = 0
    
    def extract_file(self, archive):
        if archive.endswith('gz'):
            in_f = gzip.open(archive, 'rb')
            archive = archive.replace(".gz", "")
            out_f = open(archive, 'wb')
            out_f.write(in_f.read())
            in_f.close()
            out_f.close()
            return archive
        
        elif archive.endswith('zip'):
            unzip_path = os.path.dirname(archive)
            zip_ref = zipfile.ZipFile(archive, 'r')
            zip_ref.extractall(unzip_path)
            zip_ref.close()
            
            return os.path.splitext(archive)
            
        
    def create_parser(self):
        return mzid.read(self.filename)
    
    def get_next(self):
        return next(self.source)
    
    def reset(self):
        self.source.reset()
    
    def set_index_dict(self, index_dict):
        self.index_dict = index_dict
        self.index_dict_num = len(index_dict)

    def match_identification_with_peaklist(self, peaklist, index_dict=None):
        if index_dict is not None:
            self.index_dict = index_dict
            
        if len(self.index_dict) == 0:
            print("Index dictionary is empty")
            return
        
        self.reset()

        found, notfound = 0, 0
        for identity in self.source:
            check, title, scanID = self.find_spectral_match(identity)
            if check:
                identification = self.get_spectrum_information(identity)
                peaklist[scanID]['identification'] = identification
                found += 1
            else:
                notfound += 1
                
        msg = "Found {}/{} | Not found {}/{}. There are {} unassigned spectra".format(found, found+notfound,
                                                                                      notfound, found+notfound,
                                                                                      len(peaklist)-found)
        print(msg)
        return peaklist
    
    def find_spectral_match(self, identification):
        """
        Check whether PSM match the peak list
        -----
        identification (dict): mzIdent dataset
        spectral_dict (dict): key - value dictionary of ORIGAMI scan names and peaklist file titles
        """
        
        
        if identification.get("spectrum title", "") in self.index_dict:
            return True, identification['spectrum title'], self.index_dict[identification['spectrum title']]
        elif identification.get("name", "") in self.index_dict:
            return True, identification['name'], self.index_dict[identification['name']]
        else:
            return False, None, None

    def get_spectrum_information(self, spectrum_in):
        spectrum_out = {}
        for spec in xrange(len(spectrum_in.get('SpectrumIdentificationItem', []))):
            peptide_sequence = spectrum_in['SpectrumIdentificationItem'][spec]['PeptideSequence']
            experimental_mz = spectrum_in['SpectrumIdentificationItem'][spec]['experimentalMassToCharge']
            calculated_mz = spectrum_in['SpectrumIdentificationItem'][spec]['calculatedMassToCharge']
            charge = spectrum_in['SpectrumIdentificationItem'][spec].get('chargeState', 0)
            
            # get dictionaries
            scores = self.get_scores(spectrum_in['SpectrumIdentificationItem'][spec])
            peptide_info = self.get_peptide_information(spectrum_in['SpectrumIdentificationItem'][spec].get('PeptideEvidenceRef', []))
            modification_info = self.get_modifications(spectrum_in['SpectrumIdentificationItem'][spec].get('Modification', []))        
            spectrum_out[spec] = {'peptide_seq':peptide_sequence, 
                                  'experimental_mz':experimental_mz,
                                  'calculated_mz':calculated_mz, 
                                  'charge':charge, 
                                  'scores':scores,
                                  'peptide_info':peptide_info, 
                                  'modification_info':modification_info}

        return spectrum_out
        
    def get_peptide_information(self, peptide_in):
        """
        Retrieve peptide information from mzIdent file
        """
        peptide_out = {}
        for pep in xrange(len(peptide_in)):
            peptide_sequence = peptide_in[pep].get('Seq', "")
            protein_description = peptide_in[pep].get('protein description', "")
            accession = peptide_in[pep].get('accession', "")
            start = peptide_in[pep].get('start', "")
            end = peptide_in[pep].get('end', "")
            pre = peptide_in[pep].get('pre', "")
            post = peptide_in[pep].get('post', "")

            peptide_out[pep] = {'peptide_seq':peptide_sequence,
                                'protein_description':protein_description, 
                                'accession':accession, 
                                'start':start, 
                                'end':end,
                                'pre':pre, 
                                'post':post}

        return peptide_out

    def get_modifications(self, modifications_in):
        """
        Retrieve modification information from mzIdent file
        """
        modifications_out = {}
        for mod in xrange(len(modifications_in)):
            modification_location = modifications_in[mod].get('location', "")
            modification_mass_delta = modifications_in[mod].get('monoisotopicMassDelta', "")
            modification_name = modifications_in[mod].get('name', "")
            modification_residues = modifications_in[mod].get('residues', "")

            modifications_out[mod] = {'location':modification_location, 
                                      'mass_delta':modification_mass_delta,
                                      'name':modification_name, 
                                      'residues':modification_residues}

        return modifications_out
    
    def get_scores(self, spectrum_in):
        """
        Retrieve a dictionary with scores
        """
        scaffold_pep_prob = spectrum_in.get('Scaffold:Peptide Probability', "")
        identity_e_score = spectrum_in.get('IdentityE Score', "")
        mascot_score = spectrum_in.get('Mascot:score', "")
        mascot_threshold = spectrum_in.get('Mascot:identity threshold', "")

        scores = {'scaffold_peptide_probability':scaffold_pep_prob,
                  'identity_e_score':identity_e_score,
                  'mascot_score':mascot_score,
                  'mascot_threshold':mascot_threshold}

        return scores