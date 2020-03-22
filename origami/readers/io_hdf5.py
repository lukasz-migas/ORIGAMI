"""Tools to operate on hdf5 file"""
# Third-party imports
import h5py


def create_hdf5_file(filename, mode="w"):
    return h5py.File(filename, mode=mode)


def get_group(hdf_obj, group_name):
    try:
        group_obj = hdf_obj[group_name]
    except KeyError:
        group_obj = hdf_obj.create_group(group_name)

    return group_obj


def add_data_to_group(group_obj, dataset_name, data, dtype, compression=None, chunks=None):
    """Add data to group

    Parameters
    ----------
    group_obj: h5py group object
        group that data will be added to
    dataset_name: str
        dataset name
    data: np.array, list
        data to be added to the file
    dtype: str
        dtype of the data
    compression: None, gzip
        compression strategy
    chunks: None, bool, shape
        None - no chunking (unless compression), bool - auto-chunking, shape
    """
    replaced_dset = False

    if compression is not None and chunks is not None:
        chunks = True

    if dataset_name in list(group_obj.keys()):
        if group_obj[dataset_name].dtype == dtype:
            try:
                group_obj[dataset_name][:] = data
                replaced_dset = True
            except TypeError:
                del group_obj[dataset_name]
        else:
            del group_obj[dataset_name]

    if not replaced_dset:
        group_obj.create_dataset(dataset_name, data=data, dtype=dtype, compression=compression, chunks=chunks)


def add_attribute(dset_obj, attribute_name, attribute_value):
    """
    Parameters
    ----------
    dset_obj: hdf5 dataset object
        dataset the attribute will be added to
    attribute_name: str
        attribute name
    attribute_value: str, float, int
        attribute value
    """
    dset_obj.attrs[attribute_name] = attribute_value


def replace_dataset(group_obj, name, data, dtype=None, compression=None, chunks=None):
    """
    group_obj
    name
    data
    """
    if dtype is None:
        dtype = data.dtype

    if name in list(group_obj.keys()):
        del group_obj[name]
    group_obj.create_dataset(name, data=data, dtype=dtype, compression=compression, chunks=chunks)
