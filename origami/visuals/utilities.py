# Third-party imports
from matplotlib.ticker import FuncFormatter


def compute_divider(value):
    divider = 1000000000
    value = abs(value)
    while value == value % divider:
        divider = divider / 1000
    return len(str(int(divider))) - len(str(int(divider)).rstrip("0"))


def y_tick_fmt(x, pos):
    def convert_divider_to_str(value, exp_value):
        value = float(value)
        if exp_value in [0, 1, 2]:
            if value <= 1:
                return f"{value:.2G}"
            elif value <= 1000:
                if value.is_integer():
                    return f"{value:.0F}"
                return f"{value:.1F}"
        elif exp_value in [3, 4, 5]:
            return f"{value / 1000:.1f}k"
        elif exp_value in [6, 7, 8]:
            return f"{value / 1000000:.0f}M"
        elif exp_value in [9, 10, 11, 12]:
            return f"{value / 1000000000:.0f}B"

    return convert_divider_to_str(x, compute_divider(x))


def get_intensity_formatter():
    return FuncFormatter(y_tick_fmt)
