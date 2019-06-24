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

# This file contains a number of useful functions

from builtins import str
import wx, os, re, time
import urllib.request, urllib.error, urllib.parse
import numpy as np
from numpy import savetxt
from datetime import datetime
from distutils.version import LooseVersion
from collections import OrderedDict
import pandas as pd
import pickle as pickle


def mlen(listitem, get_longest=False):

    for i, item in enumerate(listitem):
        print("Item {} has length {}".format(i, len(item)))


def remove_nan_from_list(data_list):
    data_list = np.asarray(data_list)
    data_list = data_list[~np.isnan(data_list)]
    return data_list


def dir_extra(dirlist, keywords="get"):
    """
    Quickly filter through keywords in dir list
    -----
    Usage:
        print(dir_extra(dir(line), 'set'))
    """
    # convert string to list
    if type(keywords) == str:
        keywords = [keywords]

    dirlist_out = []
    for item in dirlist:
        for keyword in keywords:
            if keyword in item:
                dirlist_out.append(item)

    return dirlist_out


def merge_two_dicts(dict_1, dict_2):
    combined_dict = dict_1.copy()  # start with x's keys and values
    combined_dict.update(dict_2)  # modifies z with y's keys and values & returns None
    return combined_dict


def get_latest_version(link=None, get_webpage=False):

    if not get_webpage:
        # Search website for all versions
        vers = []
        for line in urllib.request.urlopen(link):
            if 'Update to ORIGAMI-ANALYSE (' in line.decode('utf-8'):
                vers.append(line)
                break
        if len(vers) == 0:
            return None
        # Split the latest one to get newest version
        split = re.split(' |<', vers[0])
        webVersion = None
        for row in split:
            if '(' in row:
                webVersion = row.strip("()")
                break
        return webVersion
    else:
        webpage = urllib.request.urlopen(
            "https://raw.githubusercontent.com/lukasz-migas/ORIGAMI/master/ORIGAMI_ANALYSE/update_info.md")
        return webpage.read().decode('utf-8')


def compare_versions(newVersion, oldVersion):
    return LooseVersion(newVersion) > LooseVersion(oldVersion)


def cleanup_document(document):

    if 'temporary_unidec' in document.massSpectrum:
        del document.massSpectrum['temporary_unidec']

    for spectrum in document.multipleMassSpectrum:
        if 'temporary_unidec' in document.multipleMassSpectrum[spectrum]:
            del document.multipleMassSpectrum[spectrum]['temporary_unidec']

    return document


def saveObject(filename=None, saveFile=None):
    """ 
    Simple tool to save objects/dictionaries
    """
    tstart = time.clock()
    print(''.join(['Saving data...']))
    with open(filename, 'wb') as handle:
        saveFile = cleanup_document(saveFile)
        pickle.dump(saveFile, handle, protocol=pickle.HIGHEST_PROTOCOL)
    tend = time.clock()
    print("Saved document in: {}. It took {:.4f} seconds.".format(filename, (tend - tstart)))


def openObject(filename=None):
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


def checkExtension(input):
    # FIXME add this to the text loader
    """
    This function checks what is the extension of the file to be either saved OR loaded
    """
    fileNameExt = (str.split(input, '.'))
    fileNameExt = fileNameExt[-1]
    if fileNameExt.lower() == 'csv' or fileNameExt.lower() == 'CSV':
        outDelimiter = ','
        delimiterName = '.csv'
    elif fileNameExt.lower() == 'txt' or fileNameExt.lower() == 'TXT':
        outDelimiter = '\t'
        delimiterName = '.txt'
    else:
        outDelimiter = ','
        delimiterName = '.csv'
    return outDelimiter, delimiterName


def savaData(fileName, inputData, delimiter):
    """
    This function saves data to an array. In case you want to save it in a 
    zipped format, just append .gz to the end of the file
    """
    savetxt(fileName, inputData, delimiter=delimiter, fmt='%f')
    pass


def strictly_increasing(L):
    """
    This function checks if the values in x are always increasing
    If they are not, the  value which flags the problem is returned
    """
    answer = all(x < y for x, y in zip(L, L[1:]))
    for x, y in zip(L, L[1:]):
        if x > y:
            return y
    return answer


def binData(inputData, binSize):
    print('Bin data ')


def getMassRangeFromRawFile(self, path):
    print('End mass')


def getScantimeFromRawFile(self, path):
    print('Scan time')


def removeDuplicates(values):
    output = []
    seen = set()
    for value in values:
        # If value has not been encountered yet,
        # ... add it to both list and set.
        if value not in seen:
            output.append(value)
            seen.add(value)
    return output


def removeListDuplicates(input, columnsIn=None, limitedCols=None):
    """ remove duplicates from list based on columns """

    df = pd.DataFrame(input, columns=columnsIn)
    df.drop_duplicates(subset=limitedCols, inplace=True)
    output = df.values.tolist()
    return output


def saveAsText(filename, data, format='%.2f', delimiter=',',
               header=""):
    """
    This function uses np.savetxt to save formatted data to file
    """

    try:
        np.savetxt(filename,
                   np.transpose(data),
                   fmt=format,
                   delimiter=delimiter,
                   header=header)
    except IOError:
        print(''.join(["Cannot save file: '", filename, "' as it is currently open."]))
        return
    print(''.join(["Saved: ", filename]))


def find_nearest(array, value):
    idx = (np.abs(array - value)).argmin()
    return array[idx], idx


def find_limits(xvals, yvals):
    xouts, youts = [], []

    # Iterate over dictionary to find minimum values for each key
    for key in xvals:
        xouts.append(np.min(xvals[key]))
        xouts.append(np.max(xvals[key]))
        youts.append(np.min(yvals[key]))
        youts.append(np.max(yvals[key]))

    return xouts, youts


def find_limits_list(xvals, yvals):
    xouts, youts = [], []

    # Iterate over dictionary to find minimum values for each key
    for i in range(len(xvals)):
        xouts.append(np.min(xvals[i]))
        xouts.append(np.max(xvals[i]))
        youts.append(np.min(yvals[i]))
        youts.append(np.max(yvals[i]))

    return xouts, youts


def find_limits_all(xvals, yvals):
    xouts, youts = [], []

    if isinstance(xvals, dict):
        for key in xvals:
            xouts.append(np.min(xvals[key]))
            xouts.append(np.max(xvals[key]))
    elif any(isinstance(el, list) for el in xvals):
        for i in range(len(xvals)):
            xouts.append(np.min(xvals[i]))
            xouts.append(np.max(xvals[i]))
    elif any(isinstance(el, np.ndarray) for el in xvals):
        for i in range(len(xvals)):
            xouts.append(np.min(xvals[i]))
            xouts.append(np.max(xvals[i]))
    else:
        xouts = xvals

    if isinstance(yvals, dict):
        for key in yvals:
            youts.append(np.min(yvals[key]))
            youts.append(np.max(yvals[key]))
    elif any(isinstance(el, list) for el in yvals):
        for i in range(len(yvals)):
            youts.append(np.min(yvals[i]))
            youts.append(np.max(yvals[i]))
    elif any(isinstance(el, np.ndarray) for el in yvals):
        for i in range(len(yvals)):
            youts.append(np.min(yvals[i]))
            youts.append(np.max(yvals[i]))
    else:
        youts = yvals

    # find limits
    xlimits = [np.min(xouts), np.max(xouts)]
    ylimits = [np.min(youts), np.max(youts)]

    return xlimits, ylimits


def sort_dictionary(dictionary, key='key'):
    """
    Sort OrderedDict based on key value
    """
    if key != 'key':
        return OrderedDict(sorted(iter(dictionary.items()), key=lambda x: x[1][key]))
    else:
        return OrderedDict(sorted(list(dictionary.items()), key=lambda x: x[0]))
