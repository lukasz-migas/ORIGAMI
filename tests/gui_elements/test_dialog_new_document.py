"""Test DialogNewDocument dialog"""
# Third-party imports
import wx
import pytest

# Local imports
from origami.utils.test import WidgetTestCase
from origami.config.environment import ENV
from origami.config.environment import DOCUMENT_TYPES
from origami.gui_elements.dialog_new_document import DialogNewDocument


@pytest.mark.guitest
class TestDialogNewDocument(WidgetTestCase):
    """Test dialog"""

    @pytest.mark.parametrize("document_type", DOCUMENT_TYPES)
    def test_dialog_ok_all(self, tmpdir_factory, document_type):
        path = str(tmpdir_factory.mktemp("TEST_PATH"))

        dlg = DialogNewDocument(self.frame, document_type)
        dlg.title_value.SetValue("TEST_TITLE")
        dlg.path_value.SetValue(path)
        assert dlg.document_type_choice.IsEnabled() is False
        assert dlg.title == "TEST_TITLE"
        assert dlg.path == path
        assert dlg.document_type == document_type
        assert "TEST_TITLE" in dlg.full_path and path in dlg.full_path and ".origami" in dlg.full_path

        wx.CallLater(250, dlg.on_ok, None)
        dlg.ShowModal()
        self.yield_()

        assert "TEST_TITLE" in dlg.current_document
        assert "TEST_TITLE" in ENV
        assert ENV["TEST_TITLE"].data_type == document_type
        del ENV["TEST_TITLE"]

    def test_dialog_ok_none(self, tmpdir_factory):
        path = str(tmpdir_factory.mktemp("TEST_PATH"))

        dlg = DialogNewDocument(self.frame)
        dlg.title_value.SetValue("TEST_TITLE")
        dlg.path_value.SetValue(path)
        assert dlg.document_type_choice.IsEnabled() is True

        wx.CallLater(250, dlg.on_ok, None)
        dlg.ShowModal()
        self.yield_()

        assert "TEST_TITLE" in dlg.current_document
        assert "TEST_TITLE" in ENV
        del ENV["TEST_TITLE"]

    def test_dialog_cancel_none(self, tmpdir_factory):
        path = str(tmpdir_factory.mktemp("TEST_PATH"))

        dlg = DialogNewDocument(self.frame)
        dlg.title_value.SetValue("TEST_TITLE")
        dlg.path_value.SetValue(path)
        assert dlg.document_type_choice.IsEnabled() is True

        wx.CallLater(250, dlg.on_close, None)
        dlg.ShowModal()
        self.yield_()

        assert dlg.current_document is None
        assert "TEST_TITLE" not in ENV
