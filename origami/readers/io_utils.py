# Standard library imports
import os
from typing import Optional

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


def get_waters_pusher_frequency(parameters, mode: Optional[str] = "V"):
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
        parameters["pusher_freq"] = -1
        return parameters

    if mode in ["V", "Sensitivity", "Resolution", "Sensitivity Mode", "Resolution Mode"]:
        if parameters["end_ms"] <= 600:
            parameters["pusher_freq"] = 39.25
        elif 600 < parameters["end_ms"] <= 1200:
            parameters["pusher_freq"] = 54.25
        elif 1200 < parameters["end_ms"] <= 2000:
            parameters["pusher_freq"] = 69.25
        elif 2000 < parameters["end_ms"] <= 5000:
            parameters["pusher_freq"] = 110.25
        elif 5000 < parameters["end_ms"] <= 8000:
            parameters["pusher_freq"] = 138.25
        elif 8000 < parameters["end_ms"] <= 14000:
            parameters["pusher_freq"] = 182.25
        elif 14000 < parameters["end_ms"] <= 32000:
            parameters["pusher_freq"] = 274.25
        elif 32000 < parameters["end_ms"] <= 100000:
            parameters["pusher_freq"] = 486.25
    elif mode in ["W", "High Resolution"]:
        if parameters["end_ms"] <= 600:
            parameters["pusher_freq"] = 75.25
        elif 600 < parameters["end_ms"] <= 1200:
            parameters["pusher_freq"] = 106.25
        elif 1200 < parameters["end_ms"] <= 2000:
            parameters["pusher_freq"] = 137.25
        elif 2000 < parameters["end_ms"] <= 5000:
            parameters["pusher_freq"] = 216.25
        elif 5000 < parameters["end_ms"] <= 8000:
            parameters["pusher_freq"] = 273.25
        elif 8000 < parameters["end_ms"] <= 14000:
            parameters["pusher_freq"] = 363.25
        elif 14000 < parameters["end_ms"] <= 32000:
            parameters["pusher_freq"] = 547.25
        elif 32000 < parameters["end_ms"] <= 100000:
            parameters["pusher_freq"] = 547.25

    return parameters


def get_waters_inf_data(path):
    """Imports information file for selected MassLynx file"""
    filename = os.path.join(path, "_extern.inf")
    # TODO: replace current method with regex since it will be more specific...
    parameters = dict.fromkeys(
        [
            "start_ms",
            "end_ms",
            "end_msms",
            "set_msms",
            "scan_time",
            "polarity",
            "mode_sensitivity",
            "mode_analyser",
            "pusher_freq",
            "correction_c",
            "trap_ce",
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
                    parameters["start_ms"] = str2num(str(line.split()[-1]))
                except Exception:
                    pass
            if "MSMS End Mass" in line:
                try:
                    parameters["end_ms"] = str2num(str(line.split()[-1]))
                except Exception:
                    pass
            if "End Mass" in line:
                try:
                    parameters["end_ms"] = str2num(str(line.split()[-1]))
                except Exception:
                    pass
            if "Set Mass" in line:
                try:
                    parameters["set_msms"] = str2num(str(line.split()[-1]))
                except Exception:
                    pass
            if "Scan Time (sec)" in line or "Scan Time" in line:
                try:
                    parameters["scan_time"] = str2num(str(line.split()[-1]))
                except Exception:
                    pass
            if "Polarity" in line:
                try:
                    parameters["polarity"] = str(line.split()[-1])
                except Exception:
                    pass
            if "Sensitivity" in line:
                try:
                    parameters["mode_sensitivity"] = str(line.split()[-1])
                except Exception:
                    pass
            if "Analyser" in line or "OpticMode" in line:
                try:
                    parameters["mode_analyser"] = str(line.split("\t")[-1]).strip()
                except Exception:
                    pass
            if "EDC Delay Coefficient" in line:
                try:
                    parameters["correction_c"] = str2num(str(line.split()[-1]))
                except Exception:
                    pass
            if "ADC Pusher Period (us)" in line:
                parameters["pusher_freq"] = str2num(line.split()[-1])
            if "Trap Collision Energy" in line:
                if i == 1:
                    try:
                        parameters["trap_ce"] = str2num(str(line.split()[-1]))
                    except Exception:
                        pass
                i += 1

    if parameters["pusher_freq"] is None:
        parameters = get_waters_pusher_frequency(parameters, mode=parameters["mode_analyser"])

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
