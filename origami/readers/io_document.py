# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
#    Copyright (C) 2017-2018 Lukasz G. Migas
#    <lukasz.migas@manchester.ac.uk> OR <lukas.migas@yahoo.com>
#
# 	 GitHub : https://github.com/lukasz-migas/ORIGAMI
# 	 University of Manchester IP : https://www.click2go.umip.com/i/s_w/ORIGAMI.html
# 	 Cite : 10.1016/j.ijms.2017.08.014
#
#    This program is free software. Feel free to redistribute it and/or
#    modify it under the condition you cite and credit the authors whenever
#    appropriate.
#    The program is distributed in the hope that it will be useful but is
#    provided WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE
# -------------------------------------------------------------------------
# __author__ lukasz.g.migas

import time
import pickle


def save_py_object(filename=None, saveFile=None):
    """ 
    Simple tool to save objects/dictionaries
    """
    tstart = time.clock()
    print((''.join(['Saving data...'])))
    with open(filename, 'wb') as handle:
        saveFile = cleanup_document(saveFile)
        pickle.dump(saveFile, handle, protocol=pickle.HIGHEST_PROTOCOL)
    tend = time.clock()
    print(("Saved document in: {}. It took {:.4f} seconds.".format(filename, (tend - tstart))))


def open_py_object(filename=None):
    """
    Simple tool to open pickled objects/dictionaries
    """
    if filename.rstrip('/')[-7:] == ".pickle":
        with open(filename, 'rb') as f:
            try:
                return pickle.load(f)
            except Exception as e:
                print(e)
                return None
    else:
        with open(filename + '.pickle', 'rb') as f:
            return pickle.load(f)


def cleanup_document(document):

    if 'temporary_unidec' in document.massSpectrum:
        del document.massSpectrum['temporary_unidec']

    for spectrum in document.multipleMassSpectrum:
        if 'temporary_unidec' in document.multipleMassSpectrum[spectrum]:
            del document.multipleMassSpectrum[spectrum]['temporary_unidec']

    try:
        document.file_reader = {}
    except:
        pass

    return document
