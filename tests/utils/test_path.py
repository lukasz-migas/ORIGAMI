# Third-party imports
import pytest

# Local imports
from origami.utils.path import get_duplicate_name


@pytest.mark.parametrize(
    "name, expected",
    (
        [r"D:\Data\ORIGAMI\CON_A_LINEAR_z20.origami", r"D:\Data\ORIGAMI\CON_A_LINEAR_z20 (copy 0).origami"],
        [r"D:\Data\ORIGAMI\CON_A_LINEAR_z20 (copy 0).origami", r"D:\Data\ORIGAMI\CON_A_LINEAR_z20 (copy 1).origami"],
        [
            r"D:\Data\ORIGAMI\CON_A_LINEAR_z20 (copy 131).origami",
            r"D:\Data\ORIGAMI\CON_A_LINEAR_z20 (copy 132).origami",
        ],
        [r"D:\Data\ORIGAMI\CON_A_LINEAR_z20 (copy 131)", r"D:\Data\ORIGAMI\CON_A_LINEAR_z20 (copy 132).origami"],
    ),
)
def test_get_duplicate_name_split(name, expected):
    result = get_duplicate_name(name, ".origami")
    assert result == expected


@pytest.mark.parametrize(
    "name, expected", (["MassSpectrum", "MassSpectrum (copy 0)"], ["MassSpectrum (copy 0)", "MassSpectrum (copy 1)"])
)
def test_get_duplicate_name(name, expected):
    result = get_duplicate_name(name)
    assert result == expected
