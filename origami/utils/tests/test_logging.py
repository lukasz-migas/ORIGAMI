# Third-party imports
import pytest

# Local imports
from origami.utils.logging import delete_logger
from origami.utils.logging import set_logger_level
from origami.utils.logging import set_logger_format
from origami.utils.logging import set_logger_parameters


@pytest.mark.parametrize("verbose", [None, True, "INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"])
def test_set_logger_level(verbose):
    set_logger_level(verbose)


@pytest.mark.parametrize("verbose", [None, True, "INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"])
def test_set_logger_parameters(verbose):
    set_logger_parameters(verbose)


def test_set_logger_format():
    set_logger_format()


def test_delete_logger():
    delete_logger()
