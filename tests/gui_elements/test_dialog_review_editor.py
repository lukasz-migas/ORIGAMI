"""Test SelectDataset dialog"""
# Third-party imports
import wx
import pytest

# Local imports
from origami.gui_elements.dialog_review_editor import DialogReviewExportData
from origami.gui_elements.dialog_review_editor import DialogReviewEditorExtract
from origami.gui_elements.dialog_review_editor import DialogReviewEditorOverlay
from origami.gui_elements.dialog_review_editor import DialogReviewExportFigures
from origami.gui_elements.dialog_review_editor import DialogReviewApplyOrigamiMs
from origami.gui_elements.dialog_review_editor import DialogReviewProcessHeatmap
from origami.gui_elements.dialog_review_editor import DialogReviewProcessSpectrum
from origami.gui_elements.dialog_review_editor import DialogReviewExtractData

from ..wxtc import WidgetTestCase


def get_data():
    """Get test data"""
    return [["Item 1", "Data 1"], ["Item 2", "Data 2"]]


@pytest.mark.guitest
class TestDialogReviewApplyOrigamiMs(WidgetTestCase):
    """Test dialog"""

    @pytest.mark.parametrize("msg", ("Hello", None))
    def test_dialog_ok(self, msg):
        item_list = get_data()

        dlg = DialogReviewApplyOrigamiMs(self.frame, item_list)
        checked = dlg.get_checked_items()
        assert len(dlg.output_list) == len(item_list) == len(checked) == dlg.n_rows

        wx.CallLater(250, dlg.on_ok, None)
        res = dlg.ShowModal()
        assert res == wx.ID_OK
        dlg.Destroy()
        self.yield_()

    def test_dialog_cancel(self):
        item_list = get_data()
        dlg = DialogReviewApplyOrigamiMs(self.frame, item_list)

        wx.CallLater(250, dlg.on_close, None)
        res = dlg.ShowModal()
        assert res == wx.ID_NO
        dlg.Destroy()
        self.yield_()

        assert len(dlg.output_list) == 0


@pytest.mark.guitest
class TestDialogReviewProcessSpectrum(WidgetTestCase):
    """Test dialog"""

    @pytest.mark.parametrize("msg", ("Hello", None))
    def test_dialog_ok(self, msg):
        item_list = get_data()

        dlg = DialogReviewProcessSpectrum(self.frame, item_list)
        checked = dlg.get_checked_items()
        assert len(dlg.output_list) == len(item_list) == len(checked) == dlg.n_rows

        wx.CallLater(250, dlg.on_ok, None)
        res = dlg.ShowModal()
        assert res == wx.ID_OK
        dlg.Destroy()
        self.yield_()

    def test_dialog_cancel(self):
        item_list = get_data()
        dlg = DialogReviewProcessSpectrum(self.frame, item_list)

        wx.CallLater(250, dlg.on_close, None)
        res = dlg.ShowModal()
        assert res == wx.ID_NO
        dlg.Destroy()
        self.yield_()

        assert len(dlg.output_list) == 0


@pytest.mark.guitest
class TestDialogReviewProcessHeatmap(WidgetTestCase):
    """Test dialog"""

    @pytest.mark.parametrize("msg", ("Hello", None))
    def test_dialog_ok(self, msg):
        item_list = get_data()

        dlg = DialogReviewProcessHeatmap(self.frame, item_list)
        checked = dlg.get_checked_items()
        assert len(dlg.output_list) == len(item_list) == len(checked) == dlg.n_rows

        wx.CallLater(250, dlg.on_ok, None)
        res = dlg.ShowModal()
        assert res == wx.ID_OK
        dlg.Destroy()
        self.yield_()

    def test_dialog_cancel(self):
        item_list = get_data()
        dlg = DialogReviewProcessHeatmap(self.frame, item_list)

        wx.CallLater(250, dlg.on_close, None)
        res = dlg.ShowModal()
        assert res == wx.ID_NO
        dlg.Destroy()
        self.yield_()

        assert len(dlg.output_list) == 0


@pytest.mark.guitest
class TestDialogReviewExtractData(WidgetTestCase):
    """Test dialog"""

    @pytest.mark.parametrize("msg", ("Hello", None))
    def test_dialog_ok(self, msg):
        item_list = get_data()

        dlg = DialogReviewExtractData(self.frame, item_list)
        checked = dlg.get_checked_items()
        assert len(dlg.output_list) == len(item_list) == len(checked) == dlg.n_rows

        wx.CallLater(250, dlg.on_ok, None)
        res = dlg.ShowModal()
        assert res == wx.ID_OK
        dlg.Destroy()
        self.yield_()

    def test_dialog_cancel(self):
        item_list = get_data()
        dlg = DialogReviewExtractData(self.frame, item_list)

        wx.CallLater(250, dlg.on_close, None)
        res = dlg.ShowModal()
        assert res == wx.ID_NO
        dlg.Destroy()
        self.yield_()

        assert len(dlg.output_list) == 0


@pytest.mark.guitest
class TestDialogReviewEditorOverlay(WidgetTestCase):
    """Test dialog"""

    @pytest.mark.parametrize("msg", ("Hello", None))
    def test_dialog_ok(self, msg):
        item_list = get_data()

        dlg = DialogReviewEditorOverlay(self.frame, item_list)
        checked = dlg.get_checked_items()
        assert len(dlg.output_list) == len(item_list) == len(checked) == dlg.n_rows

        wx.CallLater(250, dlg.on_ok, None)
        res = dlg.ShowModal()
        assert res == wx.ID_OK
        dlg.Destroy()
        self.yield_()

    def test_dialog_cancel(self):
        item_list = get_data()
        dlg = DialogReviewEditorOverlay(self.frame, item_list)

        wx.CallLater(250, dlg.on_close, None)
        res = dlg.ShowModal()
        assert res == wx.ID_NO
        dlg.Destroy()
        self.yield_()

        assert len(dlg.output_list) == 0


@pytest.mark.guitest
class TestDialogReviewEditorExtract(WidgetTestCase):
    """Test dialog"""

    @pytest.mark.parametrize("msg", ("Hello", None))
    def test_dialog_ok(self, msg):
        item_list = get_data()

        dlg = DialogReviewEditorExtract(self.frame, item_list)
        checked = dlg.get_checked_items()
        assert len(dlg.output_list) == len(item_list) == len(checked) == dlg.n_rows

        wx.CallLater(250, dlg.on_ok, None)
        res = dlg.ShowModal()
        assert res == wx.ID_OK
        dlg.Destroy()
        self.yield_()

    def test_dialog_cancel(self):
        item_list = get_data()
        dlg = DialogReviewEditorExtract(self.frame, item_list)

        wx.CallLater(250, dlg.on_close, None)
        res = dlg.ShowModal()
        assert res == wx.ID_NO
        dlg.Destroy()
        self.yield_()

        assert len(dlg.output_list) == 0


@pytest.mark.guitest
class TestDialogReviewExportFigures(WidgetTestCase):
    """Test dialog"""

    @pytest.mark.parametrize("msg", ("Hello", None))
    def test_dialog_ok(self, msg):
        item_list = get_data()

        dlg = DialogReviewExportFigures(self.frame, item_list)
        checked = dlg.get_checked_items()
        assert len(dlg.output_list) == len(item_list) == len(checked) == dlg.n_rows

        wx.CallLater(250, dlg.on_ok, None)
        res = dlg.ShowModal()
        assert res == wx.ID_OK
        dlg.Destroy()
        self.yield_()

    def test_dialog_cancel(self):
        item_list = get_data()
        dlg = DialogReviewExportFigures(self.frame, item_list)

        wx.CallLater(250, dlg.on_close, None)
        res = dlg.ShowModal()
        assert res == wx.ID_NO
        dlg.Destroy()
        self.yield_()

        assert len(dlg.output_list) == 0


@pytest.mark.guitest
class TestDialogReviewExportData(WidgetTestCase):
    """Test dialog"""

    @pytest.mark.parametrize("msg", ("Hello", None))
    def test_dialog_ok(self, msg):
        item_list = get_data()

        dlg = DialogReviewExportData(self.frame, item_list)
        checked = dlg.get_checked_items()
        assert len(dlg.output_list) == len(item_list) == len(checked) == dlg.n_rows

        wx.CallLater(250, dlg.on_ok, None)
        res = dlg.ShowModal()
        assert res == wx.ID_OK
        dlg.Destroy()
        self.yield_()

    def test_dialog_cancel(self):
        item_list = get_data()
        dlg = DialogReviewExportData(self.frame, item_list)

        wx.CallLater(250, dlg.on_close, None)
        res = dlg.ShowModal()
        assert res == wx.ID_NO
        dlg.Destroy()
        self.yield_()

        assert len(dlg.output_list) == 0
