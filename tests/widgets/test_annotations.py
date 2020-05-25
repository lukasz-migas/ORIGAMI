# # Third-party imports
# import wx
# import pytest
#
# # Local imports
# from origami.widgets.annotations.panel_annotation_editor import PanelAnnotationEditorUI
#
#
# class TestPanelAnnotationEditorUI:
#     @staticmethod
#     @pytest.mark.parametrize("plot_type", ("mass_spectrum", "chromatogram", "mobilogram", "heatmap", "annotated"))
#     def test_init(get_app, plot_type):
#         _, frame, config, icons = get_app
#
#         panel = PanelAnnotationEditorUI(frame, config, icons, plot_type)
#         panel.Show()
#         assert panel
#
#         menu = panel.get_menu_column_right_click()
#         assert isinstance(menu, wx.Menu)
#
#         panel.Close(True)
#
#     @staticmethod
#     def test_fail(get_app):
#         _, frame, config, icons = get_app
#
#         plot_type = "other"
#         with pytest.raises(ValueError):
#             PanelAnnotationEditorUI(frame, config, icons, plot_type)
