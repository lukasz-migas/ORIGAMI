# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import numpy as np
from processing.heatmap import normalize_2D
from processing.spectra import normalize_1D
from utils.check import isempty


def compute_RMSD(inputData1=None, inputData2=None):  # computeRMSD
    """
    Compute the RMSD for a part of arrays
    """
    if isempty(inputData1) or isempty(inputData2):
        print('Make sure you pick more than one file')
        return
    elif inputData1.shape != inputData2.shape:
        print('The two arrays are of different size! Cannot compare.')
        return
    else:
        # Before computing RMSD, we need to normalize to 1
        tempArray = (
            normalize_2D(inputData=inputData1) -
            normalize_2D(inputData=inputData2)
        )
        tempArray2 = tempArray ** 2
        RMSD = ((np.average(tempArray2)) ** 0.5)
        pRMSD = RMSD * 100

    return pRMSD, tempArray


def compute_RMSF(inputData1=None, inputData2=None):  # computeRMSF
    """
    Compute the pairwise RMSF for a pair of arrays. RMSF is computed by comparing
    each individual voltage separately
    """
    if isempty(inputData1) or isempty(inputData2):
        print('Make sure you pick more than file')
        return
    elif inputData1.shape != inputData2.shape:
        print('The two arrays are of different size! Cannot compare.')
        return
    else:
        pRMSFlist = []
        size = len(inputData1[1, :])
        for row in range(0, size, 1):
            # Before computing the value of RMSF, we have to normalize to 1
            # to convert to percentage
            inputData1norm = normalize_1D(inputData=inputData1[:, row])
            np.nan_to_num(inputData1norm, copy=False)
            inputData2norm = normalize_1D(inputData=inputData2[:, row])
            np.nan_to_num(inputData2norm, copy=False)
            # Compute difference
            tempArray = (inputData1norm - inputData2norm)
            tempArray2 = tempArray ** 2
            # Calculate RMSF/D value
            RMSF = ((np.average(tempArray2)) ** 0.5)
            pRMSF = RMSF * 100
            pRMSFlist.append(pRMSF)
    return pRMSFlist


def compute_variance(inputData=None):  # computeVariance
    output = np.var(inputData, axis=0)
    return output


def compute_mean(inputData=None):  # computeMean
    output = np.mean(inputData, axis=0)
    return output


def compute_std_dev(inputData=None):  # computeStdDev
    output = np.std(inputData, axis=0)
    return output
