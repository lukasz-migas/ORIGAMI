# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
import math


def calculate_window_size(screen_size, percentage_size):
    """Calculate size of the window based on the screen size and desired percentage size

    Parameters
    ----------
    screen_size: tuple
        x, y size in pixels
    percentage_size: float
        desired size of the window size. Values should be between 0 and 1

    Returns
    -------
    (x_size, y_size): tuple
        calculated size of window based on the input parameters
    """
    x_size, y_size = screen_size

    # values should be as proportion between 0 and 1
    if percentage_size > 1.:
        percentage_size = percentage_size / 100
        print(percentage_size)

    x_size = math.ceil(x_size * percentage_size)
    y_size = math.ceil(y_size * percentage_size)

    return (x_size, y_size)
