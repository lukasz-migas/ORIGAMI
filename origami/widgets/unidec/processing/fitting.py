# Third-party imports
import numpy as np
from scipy import special
from scipy.optimize import curve_fit


def weighted_std_2(values, weights):
    """
    Calculate weighted standard deviation.
    :param values: Values
    :param weights: Weights
    :return: Weighted standard deviation.
    """
    average = np.average(values, weights=weights)
    variance = np.average((np.array(values) - average) ** 2, weights=weights)  # Fast and numerically precise
    return np.sqrt(variance)


def psfit(x, s, m, a, b, psfun):
    """
    Make peak shape from fit
    :param x: x values
    :param s: fwhm
    :param m: max position
    :param a: amplitude
    :param b: background
    :param psfun: peak shape function integer code
    :return: peak shape fit data
    """
    if psfun == 0:
        return ndis_fit(x, s, m, a, b)
    elif psfun == 1:
        return ldis_fit(x, s, m, a, b)
    elif psfun == 2:
        return splitdis_fit(x, s, m, a, b)


def ldis_fit(x, s, m, a, b):
    """
    Function for fitting Lorentzian distribution to peak.
    Adds a background to ldis.
    Prevents negative background, amplitude, and standard deviation.
    :param x: x value
    :param s: full width half max
    :param m: mean
    :param a: amplitude
    :param b: linear background
    :return: peak shape
    """
    if b < 0 or a < 0 or s < 0:
        return x * 0
    return ldis(x, m, s, a=a, norm_area=True) + b


def splitdis_fit(x, s, m, a, b):
    """
    Function for fitting Split G/L distribution to peak.
    Adds a background to splitdis.
    Prevents negative background, amplitude, and standard deviation.
    :param x: x value
    :param s: full width half max
    :param m: mean
    :param a: amplitude
    :param b: linear background
    :return: peak shape
    """
    if b < 0 or a < 0 or s < 0:
        return x * 0
    return splitdis(x, m, s, a=a, norm_area=True) + b


def isolated_peak_fit(xvals, yvals, psfun):
    """
    Fit an isolated peak to the peak shape model.
    :param xvals: x values of data
    :param yvals: y values of data
    :param psfun: peak shape function integer code
    :return: fit_array, fit_data (4 x 2 array of (fit, error) for [fwhm,mid,amp,background],fit to data)
    """
    midguess = xvals[np.argmax(yvals)]
    bguess = np.amin(yvals)
    sigguess = weighted_std_2(xvals, yvals - bguess) * 1
    # Two rounds to guess at area
    if psfun < 3:
        testdat = psfit(xvals, sigguess, midguess, 1, bguess, psfun)
        aguess = np.amax(yvals) / np.amax(testdat)
        testdat = psfit(xvals, sigguess, midguess, aguess, bguess, psfun)
        aguess = aguess * np.amax(yvals) / np.amax(testdat)
    else:
        testdat = psfit(xvals, sigguess, midguess, 1, bguess, 0)
        aguess = np.amax(yvals) / np.amax(testdat)
        testdat = psfit(xvals, sigguess, midguess, aguess, bguess, 0)
        aguess = aguess * np.amax(yvals) / np.amax(testdat)
    # Fit it
    if psfun < 3:
        fit, err, fitdat = fit_peak(xvals, yvals, psfun, midguess, sigguess, aguess, bguess)
    else:
        fit, err, fitdat = voigt_fit(xvals, yvals, midguess, sigguess, 0, aguess, bguess)

    return np.transpose([fit, err]), fitdat


def voigt(x, mu=0, sigma=1, gamma=1, amp=1, background=0):
    """voigt profile

    V(x,sig,gam) = Re(w(z))/(sig*sqrt(2*pi))
    z = (x+i*gam)/(sig*sqrt(2))
    """
    if sigma == 0:
        return ldis(x, mu, gamma * 2.0, amp) + background
    elif gamma == 0:
        return ndis_std(x, mu, sigma, amp) + background
    else:
        z = (x - mu + 1j * gamma) / (sigma * np.sqrt(2))
        w = special.wofz(z)
        v = w.real / (sigma * np.sqrt(2 * np.pi))
        v *= amp / np.amax(v)
        v += background
    return v


def voigt_fit(xvals, yvals, mguess=0, sguess=0.1, gguess=0, aguess=0, bguess=0):
    """Voigt fit"""
    guess = [mguess, sguess, gguess, aguess, bguess]
    popt, pcov = curve_fit(voigt, xvals, yvals, p0=guess, maxfev=1000000)
    fitdat = voigt(xvals, popt[0], popt[1], popt[2], popt[3], popt[4])
    return popt, np.sqrt(np.diag(pcov)), fitdat


def ndis(x, mid, fwhm, **kwargs):
    """
    Gaussian function normalized to a max of 1.

    Note: x and mid are interchangable. At least one should be a single float. The other may be an array.
    :param x: x values
    :param mid: Mean
    :param fwhm: Full Width at Half Max (2.35482 * standard deviation)
    :param kwargs: Allows norm_area flag to be passed
    :return: Gaussian distribution at x values
    """
    sig = fwhm / 2.35482
    return ndis_std(x, mid, sig, **kwargs)


def ndis_std(x, mid, sig, a=1, norm_area=False):
    """
    Normal Gaussian function normalized to the max of 1.
    :param x: x values
    :param mid: Mean of Gaussian
    :param sig: Standard Deviation
    :param a: Maximum amplitude (default is 1)
    :param norm_area: Boolean, Whether to normalize so that the area under the distribution is 1.
    :return: Gaussian distribution at x values
    """
    if norm_area:
        a *= 1 / (sig * np.sqrt(2 * np.pi))
    return a * np.exp(-(x - mid) * (x - mid) / (2.0 * sig * sig))


def ldis(x, mid, fwhm, a=1, norm_area=False):
    """
    Lorentzian function normalized to a max of 1.
    Note: x and mid are interchangable. At least one should be a single float. The other may be an array.
    :param x: x values
    :param mid: Mean
    :param fwhm: Full Width at Half Max
    :param a: Amplitude (default is 1)
    :param norm_area: Boolean, Whether to normalize so that the area under the distribution is 1.
    :return: Lorentzian distribution at x values
    """
    if norm_area:
        a *= (1 / np.pi) * (fwhm / 2.0)
    else:
        a *= (fwhm / 2.0) * (fwhm / 2.0)
    return a / ((x - mid) * (x - mid) + (fwhm / 2.0) * (fwhm / 2.0))


def splitdis(x, mid, fwhm, a=1, norm_area=False):
    """
    Split Gaussain/Lorentzian function normalized to a max of 1.

    Gaussian < mid. Lorentzian > mid.

    :param mid: Mid point (point of peak intensity)
    :param x: x value or values
    :param fwhm: Full Width at Half Max
    :return: Split Gaussian/Lorentzian distribution at x value
    """
    sig2 = fwhm / (2 * np.sqrt(2 * np.log(2)))
    if norm_area:
        a1 = a * ((1 / np.pi) / (fwhm / 2.0)) / 0.83723895067
        a2 = a * 2.0 / (fwhm * np.pi) / 0.83723895067
    else:
        a1 = a
        a2 = a
    try:
        if mid < x:
            return ldis(x, mid, fwhm, a=a1)
        else:
            return ndis_std(x, mid, sig2, a=a2)
    except ValueError:
        output = np.zeros(len(x))
        output[x > mid] = ldis(x[x > mid], mid, fwhm, a=a1)
        output[x <= mid] = ndis_std(x[x <= mid], mid, sig2, a=a2)
        return output


def ndis_fit(x, s, m, a, b):
    """
    Function for fitting normal distribution to peak.
    Adds a background to ndis.
    Prevents negative background, amplitude, and standard deviation.
    :param x: x value
    :param s: full width half max
    :param m: mean
    :param a: amplitude
    :param b: linear background
    :return: peak shape
    """
    if b < 0 or a < 0 or s < 0:
        return x * 0
    return ndis(x, m, s, a=a, norm_area=True) + b


def fit_peak(xvals, yvals, psfun, midguess, fwhmguess, aguess, bguess):
    """
    Fit peak from xvals and yvals data to defined peak shape function.
    :param xvals: x values of data
    :param yvals: y values of data
    :param psfun: peak shape function integer code
    :param midguess: midpoint guess
    :param fwhmguess: fwhm guess
    :param aguess: amplitude guess
    :param bguess: background guess
    :return: popt, perr, fitdat (optimized parameters [fwhm, mid, a, b], std error of parameters, fit to data)
    """
    guess = [fwhmguess, midguess, aguess, bguess]

    if psfun == 0:
        popt, pcov = curve_fit(ndis_fit, xvals, yvals, p0=guess)
    elif psfun == 1:
        popt, pcov = curve_fit(ldis_fit, xvals, yvals, p0=guess)
    elif psfun == 2:
        popt, pcov = curve_fit(splitdis_fit, xvals, yvals, p0=guess)
    else:
        popt = guess
        pcov = np.ones((len(guess), len(guess)))
        print("Failed")

    fitdat = psfit(xvals, popt[0], popt[1], popt[2], popt[3], psfun)
    return popt, np.sqrt(np.diag(pcov)), fitdat
