# Standard library imports
import time

# Third-party imports
import pytest

# Local imports
from origami.utils.utilities import time_loop
from origami.utils.utilities import format_size
from origami.utils.utilities import format_time
from origami.utils.utilities import time_average


def test_format_size():
    assert "100" == format_size(100)
    assert "1.0K" == format_size(2 ** 10)
    assert "1.0M" == format_size(2 ** 20)
    assert "1.0G" == format_size(2 ** 30)
    assert "1.0T" == format_size(2 ** 40)
    assert "1.0P" == format_size(2 ** 50)


@pytest.mark.parametrize(
    "value, expected", [(0.01, "us"), (0.1, "ms"), (0.5, "s"), (1, "s"), (60, "s"), (75, "min"), (3654, "hr")]
)
def test_format_time(value, expected):
    """Test 'format_time'"""
    result = format_time(value)
    assert expected in result


def test_time_average():
    """Test 'time_average'"""
    t_start = time.time()
    time.sleep(0.01)
    result = time_average(t_start, 1)
    assert "Avg:" in result
    assert "Tot:" in result
    assert result.startswith("[")
    assert result.endswith("]")


def test_time_loop():
    """Test 'time_loop'"""
    t_start = time.time()
    time.sleep(0.01)
    result = time_loop(t_start, 0, 1)
    assert "Avg:" in result
    assert "Rem:" in result
    assert "Tot:" in result
    assert "%" in result

    result = time_loop(t_start, 0, 1, as_percentage=False)
    assert "%" not in result
    assert result.startswith("[")
    assert result.endswith("]")
