import pytest
from matplotlib.ticker import FuncFormatter
from origami.visuals.utilities import get_intensity_formatter
from origami.visuals.utilities import y_tick_fmt


@pytest.mark.parametrize(
    "value, expected",
    (
        [100, "100"],
        [100.3, "100.3"],
        [1000, "1.0k"],
        [11000, "11.0k"],
        [101000, "101.0k"],
        [9000000, "9.0M"],
        [1e8, "100.0M"],
        [1e9, "1.0B"],
    ),
)
def test_get_intensity_formatter(value, expected):
    fmt = get_intensity_formatter()
    assert fmt(value) == expected
    assert isinstance(fmt, FuncFormatter)


@pytest.mark.parametrize(
    "value, expected",
    (
        [100, "100"],
        [100.3, "100.3"],
        [1000, "1.0k"],
        [11000, "11.0k"],
        [101000, "101.0k"],
        [9000000, "9.0M"],
        [1e8, "100.0M"],
        [1e9, "1.0B"],
    ),
)
def test_y_tick_fmt(value, expected):
    result = y_tick_fmt(value, 0)
    assert result == expected
