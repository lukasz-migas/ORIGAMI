"""Test enabler"""
from origami.config.enabler import AppEnabler


class TestAppEnabler:
    def test_init(self):
        enabler = AppEnabler()
        assert enabler
