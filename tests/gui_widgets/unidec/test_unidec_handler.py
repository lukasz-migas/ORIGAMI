"""Test unidec handler"""
from origami.objects.containers import MassSpectrumObject
from origami.widgets.unidec.unidec_handler import UniDecHandler
from origami.handlers.load import LoadHandler
from origami.config.config import CONFIG
from origami.widgets.unidec.processing.containers import (
    UniDecResultsObject,
    ChargeMassSpectrumHeatmap,
    MolecularWeightObject,
    ChargeMolecularWeightHeatmap,
)
import numpy as np


class TestUniDecHandler:
    def test_init(self, get_text_ms_path):
        # load data
        loader = LoadHandler()
        document = loader.load_text_mass_spectrum_document(get_text_ms_path)
        mz_obj = document["MassSpectra/Summed Spectrum", True]

        # init handler
        handler = UniDecHandler()
        assert handler

        # initialize
        data = handler.unidec_initialize(mz_obj)
        assert CONFIG.unidec_engine is not None
        assert isinstance(data, UniDecResultsObject)

        assert data.is_processed is False
        assert data.document_title == mz_obj.document_title
        assert data.dataset_name == mz_obj.dataset_name

        # preprocess
        data = handler.unidec_preprocess()
        assert data.is_processed

        x_limit = data.x_limit
        assert isinstance(x_limit, tuple)

        mz_obj_uni = data.mz_raw_obj
        assert mz_obj_uni == mz_obj

        mz_obj_proc = data.mz_processed_obj
        assert isinstance(mz_obj_proc, MassSpectrumObject)

        # run
        data = handler.unidec_run()
        assert data.is_executed

        # check grid obj
        x, y, grid = data.mz_grid_2d
        assert isinstance(x, np.ndarray)
        assert isinstance(y, np.ndarray)
        assert isinstance(grid, np.ndarray)
        assert y.shape[0] == grid.shape[0]
        assert x.shape[0] == grid.shape[1]

        grid_obj = data.mz_grid_obj
        assert isinstance(grid_obj, ChargeMassSpectrumHeatmap)

        # check grid obj
        x, y, grid = data.mw_grid_2d
        assert isinstance(x, np.ndarray)
        assert isinstance(y, np.ndarray)
        assert isinstance(grid, np.ndarray)
        assert y.shape[0] == grid.shape[0]
        assert x.shape[0] == grid.shape[1]

        grid_obj = data.mw_grid_obj
        assert isinstance(grid_obj, ChargeMolecularWeightHeatmap)

        # check mw obj
        mw_obj = data.mw_obj
        assert isinstance(mw_obj, MolecularWeightObject)
