"""UniDec utilities"""
# Standard library imports
import os
import re
import sys
import platform
import subprocess
from copy import deepcopy
from bisect import bisect_left
from ctypes import cdll
from ctypes import byref
from ctypes import c_int
from ctypes import c_double
from operator import itemgetter

# Third-party imports
import numpy as np
from scipy import signal
from natsort.natsort import natsorted
from scipy.interpolate import interp1d

# Local imports
import origami.processing.utils as pr_utils
from origami.widgets.unidec.processing.fitting import ldis
from origami.widgets.unidec.processing.fitting import ndis
from origami.widgets.unidec.processing.fitting import splitdis

is_64bits = sys.maxsize > 2 ** 32

# determine which OS version is used
DLL_NAME = "libmypfunc"
if platform.system() == "Windows":
    if not is_64bits:
        DLL_NAME += "32"
    DLL_NAME += ".dll"
elif platform.system() == "Darwin":
    DLL_NAME += ".dylib"
else:
    DLL_NAME += ".so"

check_dll_path = DLL_NAME
if os.path.isfile(check_dll_path):
    DLL_PATH = check_dll_path
else:
    DLL_PATH = os.path.join(os.path.dirname(__file__), "unidec_bin", check_dll_path)

try:
    DLL_LIB = cdll.LoadLibrary(DLL_PATH)
except (OSError, NameError) as err:
    print(DLL_PATH, err)
    print("Failed to load libmypfunc, convolutions in nonlinear mode might be slow")


def unidec_call(config, silent=False, kill=None):
    """
    Run the UniDec binary specified by exepath with the configuration file specified by configfile.
    If silent is False (default), the output from exepath will be printed to the standard out.
    If silent is True, the output is suppressed.

    The binary is run as a commandline subprocess with a call of (for example):

    UniDec call follows this pattern
        -> UniDec.exe conf.dat

    """

    call = [config.UNIDEC_DLL_PATH, str(config.config_path)]

    if kill is not None:
        call.append("-kill")
        call.append(str(kill))

    if silent:
        out = subprocess.call(call, stdout=subprocess.PIPE)
    else:
        out = subprocess.call(call)
    return out


def simple_peak_detect(data, config=None, window: int = 10, threshold: float = 0):
    """Simple peak detection algorithm.

    Detects a peak if a given data point is a local maximum within plus or minus config.peak_window.
    Peaks must also be above a threshold of config.peak_threshold * max_data_intensity.

    The mass and intensity of peaks meeting these criteria are output as a P x 2 array.

    Parameters
    ----------
    data : np.ndarray
        mass array (N x 2; mw, intensity)
    config : UniDecConfig object
        instance of config
    window : int
        size of the window
    threshold : float
        intensity threshold

    Returns
    -------
    peaks : np.ndarray
        array of detected peaks (P x 2; mass, intensity)
    """
    if config is not None:
        window = config.peakwindow / config.massbins
        threshold = config.peakthresh

    peaks = []
    length = len(data)
    max_val = np.amax(data[:, 1])
    for i in range(1, length):
        if data[i, 1] > max_val * threshold:
            start = i - window
            end = i + window
            if start < 0:
                start = 0
            if end > length:
                end = length
            check_max = np.amax(data[int(start) : int(end) + 1, 1])
            if data[i, 1] == check_max and data[i, 1] != data[i - 1, 1]:
                peaks.append([data[i, 0], data[i, 1]])
    return np.array(peaks)


def makespecfun(i, k, peaks_masses, adductmass, charges, xvals, ftab, xmax, xmin):
    """
    Small helper function to speed things up. May be more better way to do this, but I found this to be fastest.
    :param i: peak mass index
    :param k: charge index
    :param peaks_masses: peak masses list
    :param adductmass: Adduct mass
    :param charges: charge list
    :param xvals: x-values from data
    :param ftab: List of interpolation functions
    :param xmax: Maximum x value
    :param xmin: Minimum x value
    :return:
    """
    intx = np.true_divide((peaks_masses[i] + adductmass * charges[k]), charges[k])
    if xmin < intx < xmax:
        f = ftab[k]
        inty = f(intx)
    else:
        inty = 0
    pos = nearest(xvals, intx)
    return np.array([intx, inty, pos])


def nearest(array, target):
    """
    In an sorted array, quickly find the position of the element closest to the target.
    :param array: Array
    :param target: Value
    :return: np.argmin(np.abs(array - target))
    """
    i = bisect_left(array, target)
    if i <= 0:
        return 0
    elif i >= len(array) - 1:
        return len(array) - 1
    if np.abs(array[i] - target) > np.abs(array[i - 1] - target):
        i -= 1
    return i


def make_peaks_mz_tab(mz_grid, peaks, adduct_mass, index=None):
    """For each peak in peaks, get the charge state distribution.

    The intensity at each charge state is determined from mz_grid and stored in a list as peak.mztab.
    An array of the results is also output for help speeding up make_peaks_mz_tab_spectrum

    Parameters
    ----------
    mz_grid: np.ndarray
        m/z grid (N x Z)
    peaks : Peaks object
        picked peaks
    adduct_mass : float
        mass of an electrospray adduct
    index : np.ndarray
        list of indices

    Returns
    -------
    mz_tab : np.ndarray
        P x Z array
    """
    xvals = np.unique(mz_grid[:, 0])
    xmin = np.amin(xvals)
    xmax = np.amax(xvals)
    yvals = np.unique(mz_grid[:, 1])
    x_len = len(xvals)
    y_len = len(yvals)
    new_grid = np.reshape(mz_grid[:, 2], (x_len, y_len))
    n_peaks = peaks.n_peaks
    f_tab = [interp1d(xvals, new_grid[:, k]) for k in range(0, y_len)]
    mz_tab = [
        [makespecfun(i, k, peaks.masses, adduct_mass, yvals, xvals, f_tab, xmax, xmin) for k in range(0, y_len)]
        for i in range(0, n_peaks)
    ]
    if index is None:
        for i in range(0, n_peaks):
            peaks.peaks[i].mz_tab = np.array(mz_tab[i])
    else:
        for i in range(0, n_peaks):
            peaks.peaks[i].mz_tab.append(np.array(mz_tab[i]))
    return np.array(mz_tab)


def make_peaks_mz_tab_spectrum(mz_grid, peaks, mz_processed, mz_tab, index=None):
    """Used for plotting the dots in plot 4.

    Perform the same things as make_peaks_mz_tab, but instead of using the deconvolved intensities,
    it takes the intensity directly from the spectrum.
    Parameters
    ----------
    mz_grid: np.ndarray
        m/z grid (N x Z)
    peaks : Peaks object
        picked peaks
    mz_processed : np.ndarray
        processed mass spectrum of shape (N x 2)
    mz_tab : np.ndarray
        array obtained from `mz_peaks_mz_tab`
    index : np.ndarray
        list of indices

    Returns
    -------
    mz_tab_copy : np.ndarray
        mz_tab_copy but with intensities replaced by value at the spectrum with shape (P x Z)
    """
    zvals = np.unique(mz_grid[:, 1])
    z_len = len(zvals)
    n_peaks = peaks.n_peaks
    mz_tab_copy = deepcopy(mz_tab)

    if index is None:
        mz_tab_copy[:, :, 1] = [
            [mz_processed[int(peaks.peaks[i].mz_tab[k, 2]), 1] for k in range(0, z_len)] for i in range(0, n_peaks)
        ]
        for i in range(0, n_peaks):
            peaks.peaks[i].mz_tab_alt = np.array(mz_tab_copy[i])
    else:
        mz_tab_copy[:, :, 1] = [
            [mz_processed[int(peaks.peaks[i].mz_tab[index][k, 2]), 1] for k in range(0, z_len)]
            for i in range(0, n_peaks)
        ]
        for i in range(0, n_peaks):
            peaks.peaks[i].mz_tab_alt.append(np.array(mz_tab_copy[i]))

    return mz_tab_copy


def peaks_error_fwhm(pks, mw):
    """
    Calculates the error of each peak in pks using FWHM.
    Looks for the left and right point of the peak that is 1/2 the peaks max intensity, rightmass - leftmass = error
    :param pks:
    :param mw: self.data.massdat
    :return:
    """
    pmax = np.amax([p.height for p in pks.peaks])
    datamax = np.amax(np.asarray(mw)[:, 1])
    div = datamax / pmax
    for peak in pks.peaks:
        intensity = peak.height
        index = nearest(mw[:, 0], peak.mass)
        left_width = 0
        right_width = 0
        counter = 1
        left_found = False
        right_found = False
        while right_found is False and left_found is False:
            if left_found is False:
                if mw[index - counter, 1] <= (intensity * div) / 2:
                    left_found = True
                else:
                    left_width += 1
            if right_found is False:
                if mw[index + counter, 1] <= (intensity * div) / 2:
                    right_found = True
                else:
                    right_width += 1
            counter += 1
        peak.error_fwhm = mw[index + right_width, 0] - mw[index - left_width, 0]


def peaks_error_mean(pks, data, charge_tab, mw, config):
    """
    Calculates error using the masses at different charge states.
    For each peak, finds the local max of the peak at each charge state, and does a weighted mean and weighted std. dev.
    :param pks:
    :param data: self.data.massgrid
    :param charge_tab: self.data.ztab
    :param mw: self.data.massdat
    :param config: self.config
    :return:
    """
    length = len(data) / len(charge_tab)
    for peak in pks.peaks:
        index = nearest(mw[:, 0], peak.mass)
        masses = []
        ints = []
        idx_start = nearest(mw[:, 0], mw[index, 0] - config.peakwindow)
        idx_end = nearest(mw[:, 0], mw[index, 0] + config.peakwindow)
        for z in range(0, len(charge_tab)):
            startind = round(idx_start + (z * length))
            endind = round(idx_end + (z * length))
            tmparr = data[startind:endind]
            ind = np.argmax(tmparr)
            ints.append(tmparr[ind])
            masses.append(mw[idx_start + ind, 0])
        mean = np.average(masses, weights=ints)

        # Calculate weighted standard deviation
        peak_sum = 0
        denom = 0
        for w, m in enumerate(masses):
            peak_sum += ints[w] * pow(m - mean, 2)
            denom += ints[w]
        denom *= len(charge_tab) - 1
        std = peak_sum / denom
        std = std / len(charge_tab)
        std = std ** 0.5
        peak.error_mean = std


def makeconvspecies(processed_data, peaks, config):
    """
    For data and peaks, create a simulated spectrum of each peak.
    Assumes p.mz_tab has been set for each p in pks.peaks by make_peaks_mz_tab
    Also makes pks.composite, which is a sum of all the simulated spectra.
    :param processed_data: Processed 2D MS data (data2, N x 2)
    :param peaks: Peaks object (P Peak objects in pks.peaks)
    :param config: UniDecConfig object
    :return: Array of simulated spectra (P x N)
    """
    x = processed_data[:, 0]
    x_len = len(x)

    if config.linflag != 2:
        peak_width = config.mzsig / config.mzbins
        kernel = conv_peak_shape_kernel(x, config.psfun, peak_width)
        sticks = [stickconv(p.mz_tab, kernel) for p in peaks.peaks]
    else:
        try:
            sticks = [cconvolve(x, p.mz_tab, config.mzsig, config.psfun) for p in peaks.peaks]
        except (OSError, TypeError, NameError, AttributeError):
            sticks = [nonlinstickconv(x, p.mz_tab, config.mzsig, config.psfun) for p in peaks.peaks]

    peaks.composite = np.zeros(x_len)
    for i in range(0, peaks.n_peaks):
        peaks.peaks[i].sticks = sticks[i]
        peaks.composite += np.array(sticks[i])
    peaks.convolved = True
    return np.array(sticks)


def nonlinstickconv(xvals, mz_tab, fwhm, peak_func):
    """
    Python-based Nonlinear convolution. First makes a stick spectrum. Then, convolved with peak shape kernel.
    :param xvals: x-axis
    :param mz_tab: mz_tab from make_peaks_mz_tab
    :param fwhm: Full width half max
    :param peak_func: Peak shape function integer
    :return: Convolved output
    """
    if peak_func == 0:
        window = 5 * fwhm
    else:
        window = 15 * fwhm
    x_len = len(xvals)
    stick = np.zeros(x_len)
    stick[np.array(mz_tab[:, 2]).astype(np.int)] = mz_tab[:, 1]
    bool1 = [np.abs(xvals - xvals[i]) < window for i in range(0, x_len)]
    kernels = np.array([make_peak_shape(-xvals[bool1[i]], peak_func, fwhm, -xvals[i]) for i in range(0, x_len)])
    output = np.array([np.sum(kernels[i] * stick[bool1[i]]) for i in range(0, x_len)])
    return output


def cconv(a, b):
    """
    Circular convolution of two lists
    :param a: N-length array
    :param b: N-length array
    :return: Convolution
    """
    # return np.fft.ifft(np.fft.fft(a) * np.fft.fft(b)).real
    # return np.convolve(a, np.roll(b, (len(b)) / 2 - 1 + len(b) % 2), mode="same")
    roll_value = round((len(b)) / 2 - 1 + len(b) % 2)
    return signal.fftconvolve(a, np.roll(b, roll_value), mode="same")


def stickconv(mz_tab, kernel):
    """
    Make stick spectrum and then convolves with kernel.
    :param mz_tab: mz_tab from make_peaks_mz_tab
    :param kernel: peak shape kernel
    :return: Convolved output
    """
    xlen = len(kernel)
    temp = np.zeros(xlen)
    temp[np.array(mz_tab[:, 2]).astype(np.int)] = mz_tab[:, 1]
    return cconv(temp, kernel)


def cconvolve(xvals, mz_tab, fwhm, peak_func):
    """
    Fast nonlinear convolution algorithm using C dll.
    :param xvals: x-axis
    :param mz_tab: mz_tab from make_peaks_mz_tab()
    :param fwhm: Full width half max of peak
    :param peak_func: Peak shape function code (0=Gauss, 1=Lorentzian, 2=Split G/L)
    :return: Convolved output
    """
    stick = np.zeros(len(xvals))
    stick[np.array(mz_tab[:, 2]).astype(np.int)] = mz_tab[:, 1]
    c_x = (c_double * len(xvals))(*xvals)
    c_input = (c_double * len(stick))(*stick)
    c_output = (c_double * len(stick))()
    DLL_LIB.convolve(byref(c_x), byref(c_input), byref(c_output), c_int(peak_func), c_double(fwhm), len(c_input))
    return np.frombuffer(c_output)


def conv_peak_shape_kernel(xaxis, peak_func, fwhm):
    """
    Creation of an efficient peak shape kernel for circular convolutions.

    Note: peak width must be in units of index not value of x-axis. To get this take fwhm/binsize.
    :param xaxis: Array of x axis values
    :param peak_func: Integer

    0=Gaussian
    1=Lorentzian
    2=Split Gaussian/Lorentzian

    :param fwhm: Full width half max of peak (in units matching data indexes not values)
    :return: Peak shape kernel centered at 0.
    """
    limit = int(10 * fwhm)
    length = len(xaxis)
    kernel = np.zeros(length)
    for i in range(-limit, limit):
        if peak_func == 0:
            kernel[i % length] = ndis(i, 0, fwhm)
        if peak_func == 1:
            kernel[i % length] = ldis(i, 0, fwhm)
        if peak_func == 2:
            kernel[i % length] = splitdis(i, 0, fwhm)
    return kernel


def make_peak_shape(x, peak_func, fwhm, mid, norm_area: bool = False):
    """
    Make a peak of width fwhm centered at mid for given x axis.

    Note: peak width must be in units of index not value of x-axis. To get this take fwhm/binsize.

    Parameters
    ----------
    x: np.ndarray
        Array of x axis values
    peak_func: int
        peak function
        0=Gaussian
        1=Lorentzian
        2=Split Gaussian/Lorentzian
    fwhm: float
        Full width half max of peak (in units matching data indexes not values)
    mid: float
        Midpoint of peak
    norm_area : bool
        normalize area

    Returns
    -------
    kernel :
        Peak shape centered at midpoint
    """

    if peak_func == 0:
        kernel = ndis(x, mid, fwhm, norm_area=norm_area)
    elif peak_func == 1:
        kernel = ldis(x, mid, fwhm, norm_area=norm_area)
    elif peak_func == 2:
        kernel = splitdis(x, mid, fwhm, norm_area=norm_area)
    elif peak_func == 3:
        kernel = ndis(x, mid, fwhm, norm_area=norm_area)
    else:
        kernel = x * 0
    return kernel


def unidec_sort_mw_list(mass_list, column_id):
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


def calculate_charge_positions(
    charge_list, mw: float, x: np.ndarray, adduct_ion: str = "H+", remove_below: float = 0.01
):
    """Calculate positions of charges"""
    adducts = {
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
    min_mz, max_mz = np.min(x), np.max(x)
    charges = np.array(list(map(int, np.arange(charge_list[0, 0], charge_list[-1, 0] + 1))))
    peak_pos = (float(mw) + (adducts[adduct_ion])) / charges

    ignore = (peak_pos > min_mz) & (peak_pos < max_mz)
    peak_pos, charges, intensity = peak_pos[ignore], charges[ignore], charge_list[:, 1][ignore]

    # remove peaks that are of poor intensity
    max_intensity = np.amax(intensity) * remove_below
    ignore = intensity > max_intensity
    peak_pos, charges, intensity = peak_pos[ignore], charges[ignore], intensity[ignore]

    return peak_pos, charges, intensity


def get_peak_maximum(data, xmin=None, xmax=None, xval=None):
    """Get maximum value of the peak"""
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
