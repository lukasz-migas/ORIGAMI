"""Utilities that don't belong anywhere else"""
# Standard library imports
from collections import OrderedDict

# Third-party imports
import numpy as np


def mlen(listitem):
    """Extension of len to compute the length of various items"""

    for i, item in enumerate(listitem):
        print("Item {} has length {}".format(i, len(item)))


def dir_extra(dirlist, keywords="get"):
    """
    Quickly filter through keywords in dir list
    -----
    Usage:
        print(dir_extra(dir(line), 'set'))
    """
    # convert string to list
    if isinstance(keywords, str):
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


def sort_dictionary(dictionary, key="key"):
    """
    Sort OrderedDict based on key value
    """
    if key != "key":
        return OrderedDict(sorted(iter(dictionary.items()), key=lambda x: x[1][key]))
    else:
        return OrderedDict(sorted(list(dictionary.items()), key=lambda x: x[0]))


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


def remove_nan_from_list(data_list):
    data_list = np.asarray(data_list)
    data_list = data_list[~np.isnan(data_list)]
    return data_list


def removeListDuplicates(input, columnsIn=None, limitedCols=None):
    """ remove duplicates from list based on columns """
    # Third-party imports
    import pandas as pd

    df = pd.DataFrame(input, columns=columnsIn)
    df.drop_duplicates(subset=limitedCols, inplace=True)
    output = df.values.tolist()
    return output
