from processing.utils import nthroot


def test_nthroot():
    expected = 3.0
    result = nthroot(9, 2)
    assert expected == result
