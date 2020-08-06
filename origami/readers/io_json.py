"""All utility functions that deal with JSON files"""
# Standard library imports
import os
import json

# Third-party imports
import numpy as np


def remove_duplicates(data):
    # list of dictionaries
    if isinstance(data, list):
        # check if list of dictionaries
        if all(isinstance(d, dict) for d in data):
            return [dict(t) for t in {tuple(d.items()) for d in data}]

    return data


def default(o):
    """Fixes writing of objects containing numpy dtypes

    Parameters
    ----------
    o : any
        object to be serialized

    Returns
    -------
    int / float
        converted object

    Raises
    ------
    TypeError
    """
    if isinstance(o, (np.int64, np.int32, np.int16)):
        return int(o)
    elif isinstance(o, (np.float64, np.float32, np.float16)):
        return float(o)
    raise TypeError("Could not convert %s of type %s" % o, type(o))


def read_json_data(filepath):
    """Read JSON data and metadata

    Parameters
    ----------
    filepath : str
        path to the JSON file

    Returns
    -------
    loaded json data
    """
    with open(filepath, "r") as f_ptr:
        json_data = json.load(f_ptr)

    return json_data


def write_json_data(filepath, obj, indent=4, check_existing=False):
    """Write data to JSON file

    Parameters
    ----------
    filepath : str
        path to JSON file
    obj : any
        object containing data
    indent : int, optional
        number of spaces to indent by, by default 4
    check_existing : bool, optional
        if True, existing JSON file data will be merged with the new data object
    """

    if not check_existing or not os.path.exists(filepath):
        with open(filepath, "w") as f_ptr:
            json.dump(obj, f_ptr, indent=indent, default=default, sort_keys=True, separators=(",", ": "))
    else:
        with open(filepath, "r+") as f_ptr:
            data = json.load(f_ptr)

            if isinstance(data, list):
                data.extend(obj)
            elif isinstance(data, dict):
                data.update(obj)

            # remove duplicates
            data = remove_duplicates(data)

            f_ptr.seek(0)  # rewind
            json.dump(data, f_ptr, indent=indent, default=default, sort_keys=True, separators=(",", ": "))
            f_ptr.truncate()
