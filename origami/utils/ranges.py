# Third-party imports
import numpy as np


def get_min_max(data):
    return [np.min(data), np.max(data)]


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
