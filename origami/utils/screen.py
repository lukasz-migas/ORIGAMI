# Standard library imports
import math


def calculate_window_size(screen_size, percentage_size):
    """Calculate size of the window based on the screen size and desired percentage size

    Parameters
    ----------
    screen_size: tuple
        x, y size in pixels
    percentage_size: float, list
        desired size of the window size. Values should be between 0 and 1

    Returns
    -------
    (x_size, y_size): tuple
        calculated size of window based on the input parameters
    """
    x_size, y_size = screen_size

    if isinstance(percentage_size, list):
        percentage_size_x, percentage_size_y = percentage_size
    else:
        percentage_size_x, percentage_size_y = percentage_size, percentage_size

    # values should be as proportion between 0 and 1
    if percentage_size_x > 1.0:
        percentage_size_x = percentage_size_x / 100
    if percentage_size_y > 1.0:
        percentage_size_y = percentage_size_y / 100

    x_size = math.ceil(x_size * percentage_size_x)
    y_size = math.ceil(y_size * percentage_size_y)

    return (x_size, y_size)
