"""Processing module that handles data extract"""
# Standard library imports
import logging
from sys import platform
from typing import Dict

# Third-party imports
import numpy as np

# Local imports
from origami.utils.check import check_axes_spacing
from origami.utils.decorators import check_os
from origami.config.environment import ENV
from origami.processing.heatmap import equalize_heatmap_spacing

# enable on windowsOS only
io_waters_raw = None
if platform == "win32":
    from origami.readers import io_waters_raw

LOGGER = logging.getLogger(__name__)


class ExtractionHandler:
    def __init__(self):
        """Initialized"""

    @staticmethod
    @check_os("win32")
    def waters_extract_ms_from_mobilogram(x_min: int, x_max: int, title=None):
        """Extract mass spectrum based on drift time selection

        Parameters
        ----------
        x_min : int
            start drift time in bins
        x_max : int
            end drift time in bins
        title: str, optional
            document title

        Returns
        -------
        obj_name : str
            name of the data object
        obj_data : Dict
            dictionary containing extracted data
        document : Document
            instance of the document for which data was extracted
        """
        document = ENV.on_get_document(title)

        # setup file reader
        reader = document.get_reader("ion_mobility")
        if reader is None:
            reader = io_waters_raw.WatersIMReader(document.path)
            document.set_reader("ion_mobility", reader)

        # extract data
        mz_x, mz_y, _ = reader.extract_ms(dt_start=x_min, dt_end=x_max, return_data=True)

        # preset data
        obj_name = f"Drift time: {x_min}-{x_max}"
        obj_data = {
            "xvals": mz_x,
            "yvals": mz_y,
            "range": [x_min, x_max],
            "xlabels": "m/z (Da)",
            "xlimits": document.mz_x_limits,
        }

        return obj_name, obj_data, document

    @staticmethod
    @check_os("win32")
    def waters_extract_ms_from_chromatogram(x_min: float, x_max: float, title=None):
        """Extract mass spectrum based on retention time selection

        Parameters
        ----------
        x_min : float
            start retention time in minutes
        x_max : float
            end retention time in minutes
        title: str, optional
            document title

        Returns
        -------
        obj_name : str
            name of the data object
        obj_data : Dict
            dictionary containing extracted data
        document : Document
            instance of the document for which data was extracted
        """
        document = ENV.on_get_document(title)

        # setup file reader
        reader = document.get_reader("ion_mobility")
        if reader is None:
            reader = io_waters_raw.WatersIMReader(document.path)
            document.set_reader("ion_mobility", reader)

        mz_x, mz_y, _ = reader.extract_ms(rt_start=x_min, rt_end=x_max, return_data=True)

        # Add data to dictionary
        obj_name = f"Scans: {x_min}-{x_max}"
        obj_data = {
            "xvals": mz_x,
            "yvals": mz_y,
            "range": [x_min, x_max],
            "xlabels": "m/z (Da)",
            "xlimits": document.mz_x_limits,
        }

        return obj_name, obj_data, document

    @staticmethod
    @check_os("win32")
    def waters_extract_heatmap_from_mass_spectrum_one(x_min: float, x_max: float, title=None):
        """Extract heatmap based on mass spectrum range

        Parameters
        ----------
        x_min : float
            start m/z value
        x_max : float
            end m/z value
        title: str, optional
            document title

        Returns
        -------
        obj_name : str
            name of the data object
        obj_data : Dict
            dictionary containing extracted data
        document : Document
            instance of the document for which data was extracted
        """
        document = ENV.on_get_document(title)

        # setup file reader
        reader = document.get_reader("ion_mobility")
        if reader is None:
            reader = io_waters_raw.WatersIMReader(document.path)
            document.set_reader("ion_mobility", reader)

        # get heatmap
        array, _ = reader.extract_heatmap(mz_start=x_min, mz_end=x_max, return_data=True)
        dt_x, dt_y, _ = reader.extract_dt(mz_start=x_min, mz_end=x_max, return_data=True)
        _, rt_x, rt_y, _ = reader.extract_rt(mz_start=x_min, mz_end=x_max, return_data=True)

        obj_name = f"{x_min:.2f}-{x_max:.2f}"
        obj_data = {
            "zvals": array,
            "yvals": dt_x,
            "xvals": rt_y,
            "xlabels": "Scans",
            "ylabels": "Drift time (bins)",
            "yvals1D": dt_y,
            "yvalsRT": rt_y,
        }

        return obj_name, obj_data, document

    @staticmethod
    @check_os("win32")
    def waters_extract_heatmap_from_mass_spectrum_many(x_min: float, x_max: float, filelist: Dict, title=None):
        """Extract heatmap based on mass spectrum range

        Parameters
        ----------
        x_min : float
            start m/z value
        x_max : float
            end m/z value
        filelist : Dict
            dictionary with filename : variable mapping
        title: str, optional
            document title

        Returns
        -------
        obj_name : str
            name of the data object
        obj_data : Dict
            dictionary containing extracted data
        document : Document
            instance of the document for which data was extracted
        """
        # document = ENV.on_get_document(title)
        n_files = len(filelist)

        dt_x = np.arange(1, 201)
        array = np.zeros((200, n_files))
        rt_x = []
        for idx, (filepath, value) in enumerate(filelist.items()):
            reader = io_waters_raw.WatersIMReader(filepath)
            dt_x, _dt_y, _ = reader.extract_dt(mz_start=x_min, mz_end=x_max, return_data=True)
            array[:, idx] = _dt_y
            rt_x.append(value)

        rt_x = np.asarray(rt_x)

        if not check_axes_spacing(rt_x):
            rt_x, dt_x, array = equalize_heatmap_spacing(rt_x, dt_x, array)

        # sum retention time and mobilogram
        rt_y = array.sum(axis=0)
        dt_y = array.sum(axis=1)

        obj_name = f"{x_min:.2f}-{x_max:.2f}"
        obj_data = {
            "zvals": array,
            "yvals": dt_x,
            "xvals": rt_x,
            "xlabels": "Scans",
            "ylabels": "Drift time (bins)",
            "yvals1D": dt_y,
            "yvalsRT": rt_y,
        }

        return obj_name, obj_data, None  # document
