"""Various utilities that revolve around screens"""
# Standard library imports
import math

# Third-party imports
import wx


def calculate_window_size(screen_size, percentage_size, max_window_size=None):
    """Calculate size of the window based on the screen size and desired percentage size

    Parameters
    ----------
    screen_size: tuple
        x, y size in pixels
    percentage_size: float, list
        desired size of the window size. Values should be between 0 and 1
    max_window_size : Tuple[int]

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

    if max_window_size is not None and len(max_window_size) == 2:
        _max_x_size, _max_y_size = max_window_size
        if x_size > _max_x_size:
            x_size = _max_x_size
        if y_size > _max_y_size:
            y_size = _max_y_size

    return x_size, y_size


def move_to_different_screen(parent):
    """Move application to another window"""
    try:
        current_w, current_h = parent.GetPosition()
        screen_w, screen_h = current_w, current_h
        for idx in range(wx.Display.GetCount()):
            screen_w, screen_h, _, _ = wx.Display(idx).GetGeometry()
            if screen_w > current_w:
                break

        parent.SetPosition((screen_w, screen_h))
    except AttributeError:
        pass
