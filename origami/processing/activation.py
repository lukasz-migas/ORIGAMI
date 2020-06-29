# Third-party imports
import numpy as np

# Local imports
from origami.utils.check import isempty
from origami.processing.heatmap import normalize_2d
from origami.processing.spectra import normalize_1D


def compute_rmsd(array_1, array_2, normalize=True):
    """
    Compute the RMSD for a part of arrays
    """
    if isempty(array_1) or isempty(array_2):
        print("Make sure you pick more than one file")
        return
    elif array_1.shape != array_2.shape:
        print("The two arrays are of different size! Cannot compare.")
        return

    if normalize:
        array_1 = normalize_2d(array_1.copy())
        array_2 = normalize_2d(array_2.copy())

    # Before computing RMSD, we need to normalize to 1
    array_sub = array_1 - array_2
    array_pow = array_sub ** 2
    rmsd = (np.average(array_pow)) ** 0.5
    rmsd_percent = rmsd * 100

    return rmsd_percent, array_sub


def compute_rmsf(array_1, array_2):
    """
    Compute the pairwise RMSF for a pair of arrays. RMSF is computed by comparing
    each individual voltage separately
    """
    if isempty(array_1) or isempty(array_2):
        print("Make sure you pick more than file")
        return
    elif array_1.shape != array_2.shape:
        print("The two arrays are of different size! Cannot compare.")
        return

    rmsf_percent = []
    size = len(array_1[1, :])
    for row in range(0, size, 1):
        # Before computing the value of RMSF, we have to normalize to 1
        # to convert to percentage
        array_1_norm = normalize_1D(array_1[:, row])
        np.nan_to_num(array_1_norm, copy=False)
        array_2_norm = normalize_1D(array_2[:, row])
        np.nan_to_num(array_2_norm, copy=False)
        # Compute difference
        array_sub = array_1_norm - array_2_norm
        array_pow = array_sub ** 2
        # Calculate RMSF/D value
        rmsf = (np.average(array_pow)) ** 0.5
        _percent_rmsf = rmsf * 100
        rmsf_percent.append(_percent_rmsf)
    return rmsf_percent


def compute_variance(array):
    output = np.var(array, axis=0)
    return output


def compute_mean(array):
    output = np.mean(array, axis=0)
    return output


def compute_std_dev(array):
    output = np.std(array, axis=0)
    return output
