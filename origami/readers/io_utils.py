# Standard library imports
import os

# Local imports
from origami.utils.converters import str2num


def remove_non_digits_from_list(check_list):
    list_update = []
    for s in check_list:
        try:
            float(s)
            list_update.append(s)
        except Exception:
            pass

    return list_update


def clean_up(filepath):
    try:
        os.remove(filepath)
    except Exception:
        pass


def get_waters_pusher_frequency(parameters, mode="V"):
    """
    mode           V           W
    600         39.25       75.25
    1200        54.25       106.25
    2000        69.25       137.25
    5000        110.25      216.25
    8000        138.25      273.25
    14000       182.25      363.25
    32000       274.25      547.25
    100000      486.25      547.25
    Check what pusher frequency should be used
    """
    if mode is None:
        parameters["pusherFreq"] = -1
        return parameters

    if mode in ["V", "Sensitivity", "Resolution", "Sensitivity Mode", "Resolution Mode"]:
        if parameters["endMS"] <= 600:
            parameters["pusherFreq"] = 39.25
        elif 600 < parameters["endMS"] <= 1200:
            parameters["pusherFreq"] = 54.25
        elif 1200 < parameters["endMS"] <= 2000:
            parameters["pusherFreq"] = 69.25
        elif 2000 < parameters["endMS"] <= 5000:
            parameters["pusherFreq"] = 110.25
        elif 5000 < parameters["endMS"] <= 8000:
            parameters["pusherFreq"] = 138.25
        elif 8000 < parameters["endMS"] <= 14000:
            parameters["pusherFreq"] = 182.25
        elif 14000 < parameters["endMS"] <= 32000:
            parameters["pusherFreq"] = 274.25
        elif 32000 < parameters["endMS"] <= 100000:
            parameters["pusherFreq"] = 486.25
    elif mode in ["W", "High Resolution"]:
        if parameters["endMS"] <= 600:
            parameters["pusherFreq"] = 75.25
        elif 600 < parameters["endMS"] <= 1200:
            parameters["pusherFreq"] = 106.25
        elif 1200 < parameters["endMS"] <= 2000:
            parameters["pusherFreq"] = 137.25
        elif 2000 < parameters["endMS"] <= 5000:
            parameters["pusherFreq"] = 216.25
        elif 5000 < parameters["endMS"] <= 8000:
            parameters["pusherFreq"] = 273.25
        elif 8000 < parameters["endMS"] <= 14000:
            parameters["pusherFreq"] = 363.25
        elif 14000 < parameters["endMS"] <= 32000:
            parameters["pusherFreq"] = 547.25
        elif 32000 < parameters["endMS"] <= 100000:
            parameters["pusherFreq"] = 547.25

    return parameters


def get_waters_inf_data(path):
    """Imports information file for selected MassLynx file"""
    filename = os.path.join(path, "_extern.inf")
    parameters = dict.fromkeys(
        [
            "startMS",
            "endMS",
            "setMS",
            "scanTime",
            "ionPolarity",
            "modeSensitivity",
            "modeAnalyser",
            "pusherFreq",
            "corrC",
            "trapCE",
        ],
        None,
    )

    if not os.path.isfile(filename):
        return parameters

    with open(filename, "r") as f:
        i = 0  # hacky way to get the correct collision voltage value
        for line in f:
            if "Start Mass" in line:
                try:
                    parameters["startMS"] = str2num(str(line.split()[-1]))
                except Exception:
                    pass
            if "MSMS End Mass" in line:
                try:
                    parameters["endMS"] = str2num(str(line.split()[-1]))
                except Exception:
                    pass
            elif "End Mass" in line:
                try:
                    parameters["endMS"] = str2num(str(line.split()[-1]))
                except Exception:
                    pass
            if "Set Mass" in line:
                try:
                    parameters["setMS"] = str2num(str(line.split()[-1]))
                except Exception:
                    pass
            if "Scan Time (sec)" in line or "Scan Time" in line:
                try:
                    parameters["scanTime"] = str2num(str(line.split()[-1]))
                except Exception:
                    pass
            if "Polarity" in line:
                try:
                    parameters["ionPolarity"] = str(line.split()[-1])
                except Exception:
                    pass
            if "Sensitivity" in line:
                try:
                    parameters["modeSensitivity"] = str(line.split()[-1])
                except Exception:
                    pass
            if "Analyser" in line or "OpticMode" in line:
                try:
                    parameters["modeAnalyser"] = str(line.split("\t")[-1]).strip()
                except Exception:
                    pass
            if "EDC Delay Coefficient" in line:
                try:
                    parameters["corrC"] = str2num(str(line.split()[-1]))
                except Exception:
                    pass
            if "ADC Pusher Period (us)" in line:
                parameters["pusherFreq"] = str2num(line.split()[-1])
            if "Trap Collision Energy" in line:
                if i == 1:
                    try:
                        parameters["trapCE"] = str2num(str(line.split()[-1]))
                    except Exception:
                        pass
                i += 1

    if parameters["pusherFreq"] is None:
        parameters = get_waters_pusher_frequency(parameters, mode=parameters["modeAnalyser"])

    return parameters


def get_waters_header_data(path):
    """
    Imports information file for selected MassLynx file
    """
    filename = os.path.join(path, "_HEADER.TXT")

    fileInfo = dict.fromkeys(["SampleDescription"], None)

    if not os.path.isfile(filename):
        return ""

    try:
        with open(filename, "r") as f:
            for line in f:
                if "$$ Sample Description:" in line:
                    splitline = line.split(" ")
                    line = " ".join(splitline[1::])
                    fileInfo["SampleDescription"] = line
                    break
    except UnicodeDecodeError:
        return ""

    return fileInfo
