"""Test unidec"""
from origami.utils.test import WidgetTestCase
from origami.widgets.unidec.utilities import get_uri, about_unidec
import pytest


def test_get_uri():
    uri = get_uri()
    assert isinstance(uri, str)
    assert uri.startswith("file:/")


@pytest.mark.guitest
class TestAboutUnidec(WidgetTestCase):
    def test_init(self):
        dlg = about_unidec(None)
        assert dlg
        self.wait_for(200)
