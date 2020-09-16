"""Test PlotDocument"""
# Standard library imports
import os

# Third-party imports
import numpy as np
import pytest

# Local imports
from origami.objects.containers import IonHeatmapObject
from origami.objects.containers import MassSpectrumObject
from origami.visuals.bokeh.layout import RowLayout
from origami.visuals.bokeh.layout import GridLayout
from origami.visuals.bokeh.layout import ColumnLayout
from origami.visuals.bokeh.document import Tab
from origami.visuals.bokeh.document import PlotDocument


class TestPlotDocument:
    def test_init(self, tmpdir_factory):
        path = str(tmpdir_factory.mktemp("output"))
        store = PlotDocument(path, filename="TEST")
        assert store.output_dir == path
        assert "TEST.html" in store.filepath

        tab = store.add_tab("TAB1")
        assert isinstance(tab, Tab)
        assert "TAB1" in store.tab_names
        assert tab.n_layouts == 0

        tab_2 = store.get_tab("TAB1")
        assert tab == tab_2

        _, col_1 = store.add_col(tab)
        _, col_2 = store.add_col("TAB1")
        assert isinstance(col_1, ColumnLayout)
        assert col_1 != col_2
        assert tab.n_layouts == 2

        _, row_1 = store.add_row(tab)
        _, row_2 = store.add_row("TAB1")
        assert isinstance(row_1, RowLayout)
        assert row_1 != row_2
        assert tab.n_layouts == 4

        _, grid_1 = store.add_grid(tab)
        _, grid_2 = store.add_grid("TAB1")
        assert isinstance(grid_1, GridLayout)
        assert grid_1 != grid_2
        assert tab.n_layouts == 6

        with pytest.raises(ValueError):
            store.add_tab("TAB1")
        store.add_tab("TAB1", True)

        # forcefully removed tab so old tab is gone
        tab_3 = store.get_tab("TAB1")
        assert tab != tab_3
        assert tab_3.n_layouts == 0

        store.add_tabs(["TAB2", "TAB3"])
        assert store.n_tabs == 3 == len(store.tab_names)

        _, store.add_row("TAB4")
        assert "TAB4" in store

        with pytest.raises(KeyError):
            store.get_tab("TAB5", auto_add_tab=False)

    def test_line(self, tmpdir_factory):
        data_obj = MassSpectrumObject(np.arange(100), np.random.randint(0, 100, 100))

        path = str(tmpdir_factory.mktemp("output"))
        store = PlotDocument(path, filename="TEST")

        tab, col = store.add_col("TAB1")
        plot_obj, _ = tab.add_spectrum(data_obj, col)
        assert plot_obj.x_label == data_obj.x_label
        assert plot_obj.y_label == data_obj.y_label

        # test labels
        plot_obj.add_labels({"x": [0, 50, 100], "y": [40, 40, 40], "text": ["A", "B", "C"]})

        # add widgets and events
        plot_obj.add_widgets(
            [
                "annotations_toggle",
                "annotations_font_size",
                "annotations_offset_x",
                "annotations_offset_y",
                "annotations_rotation",
            ],
            150,
        )
        plot_obj.add_widgets(["figure_width", "figure_height", "hover_mode", "figure_sizing_mode"], 150)
        plot_obj.add_events(["double_tab_zoom_out_event"])

        filepath = store.save(display=False)
        assert os.path.exists(filepath)

    def test_scatter(self, tmpdir_factory):
        data_obj = MassSpectrumObject(np.arange(100), np.random.randint(0, 100, 100))

        path = str(tmpdir_factory.mktemp("output"))
        store = PlotDocument(path, filename="TEST")

        tab, col = store.add_col("TAB1")
        plot_obj, _ = tab.add_scatter(data_obj, col)
        assert plot_obj.x_label == data_obj.x_label
        assert plot_obj.y_label == data_obj.y_label

        # test labels
        plot_obj.set_hover_tool()
        plot_obj.add_band(dict(base=np.arange(100), lower=np.arange(100) - 3, upper=np.arange(100) + 3))
        plot_obj.add_labels({"x": [0, 50, 100], "y": [40, 40, 40], "text": ["A", "B", "C"]})
        plot_obj.add_span(data=dict(location=50, dimension="width"))
        plot_obj.add_span(data=dict(location=50, dimension="height"))
        with pytest.raises(ValueError):
            plot_obj.add_span(data=dict(location=50, dimension="WIDTH"))

        # add widgets and events
        plot_obj.add_widgets(
            [
                "annotations_toggle",
                "annotations_font_size",
                "annotations_offset_x",
                "annotations_offset_y",
                "annotations_rotation",
            ],
            150,
        )
        plot_obj.add_widgets(["figure_width", "figure_height", "hover_mode", "figure_sizing_mode"], 150)
        plot_obj.add_widgets(["scatter_size", "scatter_transparency"], 150)
        plot_obj.add_events(["double_tab_zoom_out_event"])

        filepath = store.save(display=False)
        assert os.path.exists(filepath)

    def test_heatmap(self, tmpdir_factory):
        data_obj = IonHeatmapObject(np.random.randint(0, 100, (100, 100)), np.arange(100), np.arange(100))

        path = str(tmpdir_factory.mktemp("output"))
        store = PlotDocument(path, filename="TEST")

        tab, col = store.add_col("TAB1")
        plot_obj, _ = tab.add_heatmap(data_obj, col)
        assert plot_obj.x_label == data_obj.x_label
        assert plot_obj.y_label == data_obj.y_label

        plot_obj.set_hover_tool()
        plot_obj.add_widgets(["figure_width", "figure_height", "hover_mode", "figure_sizing_mode"], 150)
        plot_obj.add_events(["double_tab_zoom_out_event"])

        filepath = store.save(display=False)
        assert os.path.exists(filepath)
