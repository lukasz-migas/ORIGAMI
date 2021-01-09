"""Test splash screen"""
import pytest
from origami.gui_elements.splash_screen import SplashScreenView
from origami.utils.test import WidgetTestCase


@pytest.mark.guitest
class TestSplashScreenView(WidgetTestCase):
    """Test"""

    def test_init(self):
        splash = SplashScreenView(200)
        splash.Show()
        assert splash
        self.wait_for(200)
