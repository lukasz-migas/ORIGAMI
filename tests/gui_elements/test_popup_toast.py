"""Test toast"""
# Third-party imports
import pytest

# Local imports
from origami.gui_elements.popup_toast import PopupToast
from origami.gui_elements.popup_toast import PopupToastManager

from ..wxtc import WidgetTestCase


@pytest.mark.guitest
class TestPopupToast(WidgetTestCase):
    """Test dialog"""

    @pytest.mark.parametrize("kind", ("info", "success", "warning", "error", "ERROr"))
    def test_dialog_ok(self, kind):
        _ = PopupToast(self.frame, "HELLO", kind, timeout=100)
        self.wait_for(300)


@pytest.mark.guitest
class TestPopupToastManager(WidgetTestCase):
    """Test dialog"""

    @pytest.mark.parametrize("kind", ("info", "success", "warning", "error", "ERROr"))
    def test_dialog_ok(self, kind):
        mgr = PopupToastManager(self.frame)
        for i in range(3):
            mgr.show_popup("HELLO", kind, timeout=100)
        self.wait_for(300)
