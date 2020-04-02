# Standard library imports
import time


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
