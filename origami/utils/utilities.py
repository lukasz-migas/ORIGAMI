# Standard library imports
import math
import time
import numbers

# Third-party imports
import numpy as np
from zarr.util import normalize_dtype
from zarr.util import normalize_shape

CHUNK_BASE = 2 * 1024 * 1024  # Multiplier by which chunks are adjusted
CHUNK_MIN = 256 * 1024  # Soft lower limit (128k)
CHUNK_MAX = 64 * 1024 * 1024  # Hard upper limit


def get_chunk_size(chunks, shape, dtype):
    dtype, object_codec = normalize_dtype(dtype, None)
    shape = normalize_shape(shape) + dtype.shape
    dtype = dtype.base
    chunks = normalize_chunks(chunks, shape, dtype.itemsize)
    return chunks


def guess_chunks(shape, typesize):
    """
    Guess an appropriate chunk layout for a dataset, given its shape and
    the size of each element in bytes.  Will allocate chunks only as large
    as MAX_SIZE.  Chunks are generally close to some power-of-2 fraction of
    each axis, slightly favoring bigger values for the last index.
    Undocumented and subject to change without warning.
    """

    n_dimensions = len(shape)
    # require chunks to have non-zero length for all dimensions
    chunks = np.maximum(np.array(shape, dtype="=f8"), 1)

    # Determine the optimal chunk size in bytes using a PyTables expression.
    # This is kept as a float.
    dataset_size = np.product(chunks) * typesize
    target_size = CHUNK_BASE * (2 ** np.log10(dataset_size / (1024.0 * 1024)))

    if target_size > CHUNK_MAX:
        target_size = CHUNK_MAX
    elif target_size < CHUNK_MIN:
        target_size = CHUNK_MIN

    idx = 0
    while True:
        # Repeatedly loop over the axes, dividing them by 2.  Stop when:
        # 1a. We're smaller than the target chunk size, OR
        # 1b. We're within 50% of the target chunk size, AND
        # 2. The chunk is smaller than the maximum chunk size

        chunk_bytes = np.product(chunks) * typesize

        if (
            chunk_bytes < target_size or abs(chunk_bytes - target_size) / target_size < 0.5
        ) and chunk_bytes < CHUNK_MAX:
            break

        if np.product(chunks) == 1:
            break  # Element size larger than CHUNK_MAX

        chunks[idx % n_dimensions] = math.ceil(chunks[idx % n_dimensions] / 2.0)
        idx += 1

    return tuple(int(x) for x in chunks)


def normalize_chunks(chunks, shape, typesize):
    """Convenience function to normalize the `chunks` argument for an array
    with the given `shape`."""

    # N.B., expect shape already normalized

    # handle auto-chunking
    if chunks is None or chunks is True:
        return guess_chunks(shape, typesize)

    # handle no chunking
    if chunks is False:
        return shape

    if isinstance(chunks, numbers.Integral):
        chunks = tuple(int(chunks) for _ in shape)
    # handle 1D convenience form

    # handle bad dimensionality
    if len(chunks) > len(shape):
        raise ValueError("too many dimensions in chunks")

    # handle underspecified chunks
    if len(chunks) < len(shape):
        # assume chunks across remaining dimensions
        chunks += shape[len(chunks) :]

    # handle None or -1 in chunks
    if -1 in chunks or None in chunks:
        chunks = tuple(s if c == -1 or c is None else int(c) for s, c in zip(shape, chunks))

    return tuple(chunks)


def format_size(size: int) -> str:
    """Convert bytes to nicer format"""
    if size < 2 ** 10:
        return "%s" % size
    elif size < 2 ** 20:
        return "%.1fK" % (size / float(2 ** 10))
    elif size < 2 ** 30:
        return "%.1fM" % (size / float(2 ** 20))
    elif size < 2 ** 40:
        return "%.1fG" % (size / float(2 ** 30))
    elif size < 2 ** 50:
        return "%.1fT" % (size / float(2 ** 40))
    else:
        return "%.1fP" % (size / float(2 ** 50))


def format_time(value: float) -> str:
    """Convert time to nicer format"""
    if value <= 0.01:
        return f"{value * 1000000:.0f}us"
    elif value <= 0.1:
        return f"{value * 1000:.1f}ms"
    elif value > 86400:
        return f"{value / 86400:.2f}day"
    elif value > 1800:
        return f"{value / 3600:.2f}hr"
    elif value > 60:
        return f"{value / 60:.2f}min"
    return f"{value:.2f}s"


def report_time(t_start: float):
    """Reports the difference in time between the current time and the start time

    Parameters
    ----------
    t_start : float
        start time

    Returns
    -------
    formatted_time : str
        nicely formatted time difference
    """
    return format_time(time.time() - t_start)


def time_loop(t_start: float, n_item: int, n_total: int, as_percentage: bool = True) -> str:
    """Calculate average, remaining and total times

    Parameters
    ----------
    t_start : float
        starting time of the for loop
    n_item : int
        index of the current item - assumes index starts at 0
    n_total : int
        total number of items in the for loop - assumes index starts at 0
    as_percentage : bool, optional
        if 'True', progress will be displayed as percentage rather than the raw value

    Returns
    -------
    timed : str
        loop timing information
    """
    t_tot = time.time() - t_start
    t_avg = t_tot / (n_item + 1)
    t_rem = t_avg * (n_total - n_item + 1)

    # calculate progress
    progress = f"{n_item}/{n_total + 1}"
    if as_percentage:
        progress = f"{(n_item / (n_total + 1)) * 100:.1f}%"

    return f"[Avg: {format_time(t_avg)} | Rem: {format_time(t_rem)} | Tot: {format_time(t_tot)} || {progress}]"


def time_average(t_start: float, n_total: int) -> str:
    """Calculate average and total time of a task

    Parameters
    ----------
    t_start : float
        starting time of the task
    n_total : int
        total number of items

    Returns
    -------

    """
    t_tot = time.time() - t_start
    t_avg = t_tot / (n_total + 1)

    return f"[Avg: {format_time(t_avg)} | Tot: {format_time(t_tot)}]"
