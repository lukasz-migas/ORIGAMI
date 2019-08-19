# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
"""Utility tools for label replacements"""
import re

from utils.converters import str2num


def get_ion_name_from_label(ion_name, as_num=False):
    """Extract mz values from label

    Parameters
    ----------
    ion_name : str
        ion label with name format MZMIN-MZMAX - can have some supplement afterwards

    Returns
    -------
    mz_min : str
        start m/z value
    mz_max : str
        end m/z value
    """
    if ion_name.startswith("ion="):
        indexes = 1, 2
    else:
        indexes = 0, 1
    ion_label = re.split(r"-|\(|:|,|=| ", ion_name)
    mz_min = ion_label[indexes[0]]
    mz_max = ion_label[indexes[1]]
    if as_num:
        mz_min = str2num(mz_min)
        mz_max = str2num(mz_max)

    return mz_min, mz_max


def get_clean_label_without_tag(label, tag):
    """Remove tag from label

    Parameters
    ----------
    label : str
        label with (or without tag)
    tag : str
        component of label that should be removed

    Returns
    label : str
        cleaned-up label
    """
    if f"({tag})" in label:
        label = re.split(fr"\({tag}\)", label)[0]
        label = label.rstrip()

    if f", {tag})" in label:
        label = re.split(fr", {tag}\)", label)[0]

    return label


def convert_str_to_unicode(s, return_type="superscript"):
    """Convert string label to unicode"""

    if "+" not in s and "-" not in s and return_type not in ["charge-only [n+]", "charge-only [+n]"]:
        s = "+{}".format(s)

    if return_type == "None":
        return ""
    elif return_type == "charge-only [+n]":
        return "+{}".format(s)
    elif return_type == "charge-only [n+]":
        return "{}+".format(s)
    elif return_type == "superscript":
        unicode_string = "".join(dict(list(zip("+-0123456789", "⁺⁻⁰¹²³⁴⁵⁶⁷⁸⁹"))).get(c, c) for c in s)
        return unicode_string
    elif return_type == "M+nH":
        unicode_string = "".join(dict(list(zip("+-0123456789", "⁺⁻⁰¹²³⁴⁵⁶⁷⁸⁹"))).get(c, c) for c in s)
        modified_label = "[M{}H]{}".format(s, unicode_string)
        return modified_label
    elif return_type == "2M+nH":
        unicode_string = "".join(dict(list(zip("+-0123456789", "⁺⁻⁰¹²³⁴⁵⁶⁷⁸⁹"))).get(c, c) for c in s)
        modified_label = "[2M{}H]{}".format(s, unicode_string)
        return modified_label
    elif return_type == "3M+nH":
        unicode_string = "".join(dict(list(zip("+-0123456789", "⁺⁻⁰¹²³⁴⁵⁶⁷⁸⁹"))).get(c, c) for c in s)
        modified_label = "[3M{}H]{}".format(s, unicode_string)
        return modified_label
    elif return_type == "4M+nH":
        unicode_string = "".join(dict(list(zip("+-0123456789", "⁺⁻⁰¹²³⁴⁵⁶⁷⁸⁹"))).get(c, c) for c in s)
        modified_label = "[4M{}H]{}".format(s, unicode_string)
        return modified_label
    else:
        return s


def _replace_labels(label):
    """ Replace string labels to unicode """

    unicode_label = str(label)
    try:
        if any(_label in unicode_label for _label in ["\u2070", "u2070", "^0"]):
            unicode_label = unicode_label.replace("\u2070", "⁰").replace("u2070", "⁰").replace("^0", "⁰")
        if any(_label in unicode_label for _label in ["\u00B9", "u00B9", "^1"]):
            unicode_label = unicode_label.replace("\u00B9", "¹").replace("u00B9", "¹").replace("^1", "¹")
        if any(_label in unicode_label for _label in ["\u00B2", "u00B2", "^2"]):
            unicode_label = unicode_label.replace("\u00B2", "²").replace("u00B2", "²").replace("^2", "²")
        if any(_label in unicode_label for _label in ["\u00B3", "u00B3", "^3"]):
            unicode_label = unicode_label.replace("\u00B3", "³").replace("u00B1", "³").replace("^3", "³")
        if any(_label in unicode_label for _label in ["\u00B4", "u00B4", "^4"]):
            unicode_label = unicode_label.replace("\u00B4", "⁴").replace("u00B4", "⁴").replace("^4", "⁴")
        if any(_label in unicode_label for _label in ["\u2075", "u2075", "^5"]):
            unicode_label = unicode_label.replace("\u2075", "⁵").replace("u2075", "⁵").replace("^5", "⁵")
        if any(_label in unicode_label for _label in ["\u2076", "u2076", "^6"]):
            unicode_label = unicode_label.replace("\u2076", "⁶").replace("u2076", "⁶").replace("^6", "⁶")
        if any(_label in unicode_label for _label in ["\u2077", "u2077", "^7"]):
            unicode_label = unicode_label.replace("\u2077", "⁷").replace("u2077", "⁷").replace("^7", "⁷")
        if any(_label in unicode_label for _label in ["\u2078", "u2078", "^8"]):
            unicode_label = unicode_label.replace("\u2078", "⁸").replace("u2078", "⁸").replace("^8", "⁸")
        if any(_label in unicode_label for _label in ["\u2079", "u2079", "^9"]):
            unicode_label = unicode_label.replace("\u2079", "⁹").replace("u2079", "⁹").replace("^9", "⁹")
        if any(_label in unicode_label for _label in ["\u2080", "u2080", "*0"]):
            unicode_label = unicode_label.replace("\u2080", "₀").replace("u2080", "₀").replace("*0", "₀")
        if any(_label in unicode_label for _label in ["\u2081", "u2081", "*1"]):
            unicode_label = unicode_label.replace("\u2081", "₁").replace("u2081", "₁").replace("*1", "₁")
        if any(_label in unicode_label for _label in ["\u2082", "u2082", "*2"]):
            unicode_label = unicode_label.replace("\u2082", "₂").replace("u2082", "₂").replace("*2", "₂")
        if any(_label in unicode_label for _label in ["\u2083", "u2083", "*3"]):
            unicode_label = unicode_label.replace("\u2083", "₃").replace("u2083", "₃").replace("*3", "₃")
        if any(_label in unicode_label for _label in ["\u2084", "u2084", "*4"]):
            unicode_label = unicode_label.replace("\u2084", "₄").replace("u2084", "₄").replace("*4", "₄")
        if any(_label in unicode_label for _label in ["\u2085", "u2085", "*5"]):
            unicode_label = unicode_label.replace("\u2085", "₅").replace("u2085", "₅").replace("*5", "₅")
        if any(_label in unicode_label for _label in ["\u2086", "u2086", "*6"]):
            unicode_label = unicode_label.replace("\u2086", "₆").replace("u2086", "₆").replace("*6", "₆")
        if any(_label in unicode_label for _label in ["\u2087", "u2087", "*7"]):
            unicode_label = unicode_label.replace("\u2077", "₇").replace("u2077", "₇").replace("*7", "₇")
        if any(_label in unicode_label for _label in ["\u2088", "u2088", "*8"]):
            unicode_label = unicode_label.replace("\u2088", "₈").replace("u2088", "₈").replace("*8", "₈")
        if any(_label in unicode_label for _label in ["\u2089", "u2089", "*9"]):
            unicode_label = unicode_label.replace("\u2089", "₉").replace("u2089", "₉").replace("*9", "₉")
        if any(_label in unicode_label for _label in [r"\R", "\r"]):
            unicode_label = unicode_label.replace(r"\R", "®").replace("\r", "®")
        if any(_label in unicode_label for _label in ["\u207A", "u207A", "++", "^+"]):
            unicode_label = (
                unicode_label.replace("\u207A", "⁺").replace("u207A", "⁺").replace("++", "⁺").replace("^+", "⁺")
            )
        if any(_label in unicode_label for _label in ["\u207B", "u207B", "--", "^-"]):
            unicode_label = (
                unicode_label.replace("\u207B", "⁻").replace("u207B", "⁻").replace("--", "⁻").replace("^-", "⁻")
            )
        if any(_label in unicode_label for _label in ["\u22C5", "u22C5", ",,", "^,"]):
            unicode_label = (
                unicode_label.replace("\u22C5", "⋅").replace("u22C5", "⋅").replace(",,", "⋅").replace("^,", "⋅")
            )
        if any(_label in unicode_label for _label in ["nan", "NaN"]):
            unicode_label = unicode_label.replace("nan", "").replace("NaN", "")
        if any(_label in unicode_label for _label in ["\u212B", "u212B", "AA", "ang"]):
            unicode_label = (
                unicode_label.replace("\u212B", "Å").replace("u212B", "Å").replace("AA", "Å").replace("ang", "Å")
            )
        if any(_label in unicode_label for _label in ["\u03B1", "u03B1", "alpha", "aaa"]):
            unicode_label = (
                unicode_label.replace("\u03B1", "α").replace("u03B1", "α").replace("alpha", "α").replace("aaa", "α")
            )
        if any(_label in unicode_label for _label in ["\u03B2", "u03B2", "beta", "bbb"]):
            unicode_label = (
                unicode_label.replace("\u03B2", "β").replace("u03B2", "β").replace("beta", "β").replace("bbb", "β")
            )
        if any(_label in unicode_label for _label in ["\u03BA", "u03BA", "kappa", "kkk"]):
            unicode_label = (
                unicode_label.replace("\u03BA", "κ").replace("u03BA", "κ").replace("kappa", "κ").replace("kkk", "κ")
            )
        if any(_label in unicode_label for _label in ["\u0394", "u0394", "delta", "ddd"]):
            unicode_label = (
                unicode_label.replace("\u0394", "Δ").replace("u0394", "Δ").replace("delta", "Δ").replace("ddd", "Δ")
            )
        if any(_label in unicode_label for _label in ["\u03A8", "u03A8", "PSI"]):
            unicode_label = unicode_label.replace("\u03A8", "Ψ").replace("u03A8", "Ψ").replace("PSI", "Ψ")
        if any(_label in unicode_label for _label in ["\u03C8", "u03C8", "psi"]):
            unicode_label = unicode_label.replace("\u03C8", "ψ").replace("u03C8", "ψ").replace("psi", "ψ")
        if any(_label in unicode_label for _label in ["\u03A6", "u03A6", "PHI"]):
            unicode_label = unicode_label.replace("\u03A6", "Φ").replace("u03A6", "Φ").replace("PHI", "Φ")
        if any(_label in unicode_label for _label in ["\u03C6", "u03C6", "phi"]):
            unicode_label = unicode_label.replace("\u03C6", "φ").replace("u03C6", "φ").replace("phi", "φ")
        if any(_label in unicode_label for _label in ["\u03A9", "u03A9", "OMEGA"]):
            unicode_label = unicode_label.replace("\u03A9", "Ω").replace("u03A9", "Ω").replace("OMEGA", "Ω")
        if any(_label in unicode_label for _label in ["\u03C9", "u03C9", "omega"]):
            unicode_label = unicode_label.replace("\u03C9", "ω").replace("u03C9", "ω").replace("omega", "ω")

    except Exception:
        return unicode_label

    return unicode_label
