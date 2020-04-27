"""Processing module that handles loading of data from various file formats"""
# Standard library imports
import os
import math
import time
import logging
from sys import platform
from typing import Dict
from typing import Optional

# Third-party imports
import numpy as np

# Local imports
from origami.utils.check import check_axes_spacing
from origami.readers.io_mgf import MGFReader
from origami.readers.io_mzml import mzMLReader
from origami.utils.utilities import report_time
from origami.utils.decorators import check_os
from origami.config.environment import ENV
from origami.objects.containers import IonHeatmapObject
from origami.objects.containers import MobilogramObject
from origami.objects.containers import ChromatogramObject
from origami.objects.containers import MassSpectrumObject
from origami.objects.containers import MassSpectrumHeatmapObject
from origami.processing.heatmap import equalize_heatmap_spacing
from origami.readers.io_text_files import TextHeatmapReader
from origami.readers.io_text_files import TextSpectrumReader
from origami.readers.io_text_files import AnnotatedDataReader

# enable on windowsOS only
if platform == "win32":
    from origami.readers.io_waters_raw_api import WatersRawReader
    from origami.readers.io_waters_raw import WatersIMReader
    from origami.readers.io_thermo_raw import ThermoRawReader

LOGGER = logging.getLogger(__name__)

MGF_N_SCANS = 50000
MZML_N_SCANS = 50000


def check_path(path: str, extension: Optional[str] = None):
    """Check whether path is correct"""
    if not os.path.exists(path):
        raise ValueError(f"Path `{path}` does not exist")
    if extension is not None and not path.endswith(extension):
        raise ValueError(f"Path `{path}` does not have the correct extension")


class LoadHandler:
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
            reader = WatersIMReader(document.path)
            document.set_reader("ion_mobility", reader)

        # extract data
        mz_x, mz_y = reader.extract_ms(dt_start=x_min, dt_end=x_max, return_data=True)

        # preset data
        obj_name = f"Drift time: {x_min}-{x_max}"
        obj_data = MassSpectrumObject(mz_x, mz_y, metadata={"range": [x_min, x_max]})

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
            reader = WatersIMReader(document.path)
            document.set_reader("ion_mobility", reader)

        mz_x, mz_y = reader.extract_ms(rt_start=x_min, rt_end=x_max, return_data=True)

        # Add data to dictionary
        obj_name = f"Scans: {x_min}-{x_max}"
        obj_data = MassSpectrumObject(mz_x, mz_y, metadata={"range": [x_min, x_max]})

        return obj_name, obj_data, document

    @staticmethod
    @check_os("win32")
    def waters_extract_ms_from_heatmap(x_min: float, x_max: float, y_min: int, y_max: int, title=None):
        """Extract mass spectrum based on retention time selection

        Parameters
        ----------
        x_min : float
            start retention time in minutes
        x_max : float
            end retention time in minutes
        y_min : int
            start drift time in bins
        y_max : int
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
            reader = WatersIMReader(document.path)
            document.set_reader("ion_mobility", reader)

        mz_x, mz_y = reader.extract_ms(rt_start=x_min, rt_end=x_max, dt_start=y_min, dt_end=y_max, return_data=True)

        # Add data to dictionary
        obj_name = f"Scans: {x_min}-{x_max}"
        obj_data = MassSpectrumObject(mz_x, mz_y, metadata={"range": [x_min, x_max]})

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
            reader = WatersIMReader(document.path)
            document.set_reader("ion_mobility", reader)

        # get heatmap
        _, _, _, _, array = reader.extract_heatmap(mz_start=x_min, mz_end=x_max, return_data=True)
        dt_x, dt_y = reader.extract_dt(mz_start=x_min, mz_end=x_max, return_data=True)
        _, rt_x, rt_y = reader.extract_rt(mz_start=x_min, mz_end=x_max, return_data=True)

        obj_name = f"{x_min:.2f}-{x_max:.2f}"
        obj_data = IonHeatmapObject(array, x=dt_x, y=rt_x, xy=dt_y, yy=rt_y)

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
            reader = WatersIMReader(filepath)
            dt_x, _dt_y = reader.extract_dt(mz_start=x_min, mz_end=x_max, return_data=True)
            array[:, idx] = _dt_y
            rt_x.append(value)

        rt_x = np.asarray(rt_x)

        if not check_axes_spacing(rt_x):
            rt_x, dt_x, array = equalize_heatmap_spacing(rt_x, dt_x, array)

        # sum retention time and mobilogram
        rt_y = array.sum(axis=0)
        dt_y = array.sum(axis=1)

        obj_name = f"{x_min:.2f}-{x_max:.2f}"
        obj_data = IonHeatmapObject(array, x=dt_x, y=rt_x, xy=dt_y, yy=rt_y)

        return obj_name, obj_data, None  # document

    @staticmethod
    @check_os("win32")
    def waters_im_extract_ms(path, **kwargs):
        """Extract chromatographic data"""
        check_path(path)
        reader = WatersIMReader(path)
        x, y = reader.extract_ms(**kwargs)

        return x, y

    @staticmethod
    @check_os("win32")
    def waters_im_extract_rt(path, **kwargs):
        """Extract chromatographic data"""
        check_path(path)
        reader = WatersIMReader(path)
        x, x_bin, y = reader.extract_rt(**kwargs)

        return x_bin, y

    @staticmethod
    @check_os("win32")
    def waters_im_extract_dt(path, **kwargs):
        """Extract mobility data"""
        check_path(path)
        reader = WatersIMReader(path)
        x_bin, y = reader.extract_dt(**kwargs)

        return x_bin, y

    @staticmethod
    @check_os("win32")
    def waters_im_extract_heatmap(path, **kwargs):
        """Extract mobility data"""
        check_path(path)
        reader = WatersIMReader(path)
        dt_x, _, rt_x, _, array = reader.extract_heatmap(**kwargs)

        return dt_x, rt_x, array

    @staticmethod
    @check_os("win32")
    def waters_im_extract_msdt(path, mz_min: float, mz_max: float, mz_bin_size: float = 1.0, **kwargs):
        """Extract mobility data"""
        check_path(path)

        # calculate number of m/z bins
        n_mz_bins = math.floor((mz_max - mz_min) / mz_bin_size)
        reader = WatersIMReader(path)
        mz_x, _, dt_x, _, array = reader.extract_msdt(mz_start=mz_min, mz_end=mz_max, n_points=n_mz_bins, **kwargs)

        return mz_x, dt_x, array

    @staticmethod
    def load_text_mass_spectrum_data(path):
        """Read mass spectrum data from text file"""
        reader = TextSpectrumReader(path)

        return reader.x, reader.y, reader.directory, reader.x_limits, reader.extension

    @staticmethod
    def load_text_annotated_data(filename):
        """Read annotated data from text file"""
        reader = AnnotatedDataReader(filename)

        return reader.dataset_title, reader.data

    @staticmethod
    def load_text_heatmap_data(path):
        """Read heatmap data from text file"""
        reader = TextHeatmapReader(path)

        return IonHeatmapObject(reader.array, x=reader.x, y=reader.y, xy=reader.xy, yy=reader.yy)

    def load_text_heatmap_document(self, path):
        heatmap_obj = self.load_text_heatmap_data(path)
        document = ENV.get_new_document("origami", path, data=dict(heatmap=heatmap_obj))
        return document

    @staticmethod
    def load_mgf_data(path):
        """Read data from MGF file format"""
        t_start = time.time()
        reader = MGFReader(path)
        LOGGER.debug("Created MGF file reader. Started loading data...")

        data = reader.get_n_scans(MGF_N_SCANS)
        LOGGER.debug("Loaded MGF data in " + report_time(t_start))
        return reader, data

    def load_mgf_document(self, path):
        """Load mgf data and set inside ORIGAMI document"""
        # read data
        reader, data = self.load_mgf_data(path)

        # instantiate document
        document = ENV.get_new_document("mgf", path)
        # set data
        document.tandem_spectra = data
        document.set_reader("data_reader", reader)

        return document

    @staticmethod
    def load_mzml_data(path):
        """Read data from mzML file format"""
        t_start = time.time()
        reader = mzMLReader(path)
        LOGGER.debug("Created mzML file reader. Started loading data...")

        data = reader.get_n_scans(MZML_N_SCANS)
        LOGGER.debug("Loaded mzML data in " + report_time(t_start))
        return reader, data

    def load_mzml_document(self, path):
        """Load mzml data and set inside ORIGAMI document"""
        # read data
        reader, data = self.load_mzml_data(path)

        # instantiate document
        document = ENV.get_new_document("mzml", path)
        # set data
        document.tandem_spectra = data
        document.set_reader("data_reader", reader)

        return document

    @staticmethod
    @check_os("win32")
    def load_thermo_ms_data(path):
        """Load Thermo data"""
        t_start = time.time()
        reader = ThermoRawReader(path)
        LOGGER.debug("Created Thermo file reader. Started loading data...")

        # get average data
        chromatogram: ChromatogramObject = reader.get_tic()
        LOGGER.debug("Loaded TIC in " + report_time(t_start))

        mass_spectrum: MassSpectrumObject = reader.get_spectrum()
        LOGGER.debug("Loaded spectrum in " + report_time(t_start))

        # get mass spectra
        mass_spectra: Dict[MassSpectrumObject] = reader.get_spectrum_for_each_filter()
        chromatograms: Dict[ChromatogramObject] = reader.get_chromatogram_for_each_filter()

        data = {"mz": mass_spectrum, "rt": chromatogram, "mass_spectra": mass_spectra, "chromatograms": chromatograms}
        return reader, data

    @check_os("win32")
    def load_thermo_ms_document(self, path):
        """Load Thermo data and set in ORIGAMI document"""
        reader, data = self.load_thermo_ms_data(path)

        document = ENV.get_new_document("thermo", path, data=data)
        document.set_reader("data_reader", reader)

        return document

    @staticmethod
    @check_os("win32")
    def load_waters_ms_data(path):
        """Load Waters mass spectrometry and chromatographic data"""
        t_start = time.time()
        reader = WatersRawReader(path)
        LOGGER.debug("Initialized Waters reader")

        mz_x, mz_y = reader.get_average_spectrum()
        LOGGER.debug("Loaded spectrum in " + report_time(t_start))

        rt_x, rt_y = reader.get_tic(0)
        LOGGER.debug("Loaded TIC in " + report_time(t_start))

        parameters = reader.get_inf_data()

        data = {"mz": MassSpectrumObject(mz_x, mz_y), "rt": ChromatogramObject(rt_x, rt_y), "parameters": parameters}
        LOGGER.debug("Loaded data in " + report_time(t_start))
        return reader, data

    @check_os("win32")
    def load_waters_ms_document(self, path):
        """Load Waters data and set in ORIGAMI document"""
        reader, data = self.load_waters_ms_data(path)
        document = ENV.get_new_document("waters", path, data=data)
        document.set_reader("data_reader", reader)

        return document

    @check_os("win32")
    def load_waters_im_data(self, path):
        """Load Waters IM-MS data"""
        t_start = time.time()
        reader = WatersIMReader(path)
        LOGGER.debug("Initialized Waters reader")

        mz_x, mz_y = reader.extract_ms()
        LOGGER.debug("Loaded spectrum in " + report_time(t_start))

        rt_x_min, rt_x, rt_y = reader.extract_rt()
        LOGGER.debug("Loaded RT in " + report_time(t_start))

        dt_x, dt_y = reader.extract_dt()
        LOGGER.debug("Loaded DT in " + report_time(t_start))

        _, _, _, _, array = reader.extract_heatmap()
        LOGGER.debug("Loaded DT in " + report_time(t_start))

        msdt_mz_x, msdt_dt_x, msdt_array = self.waters_im_extract_msdt(path, reader.mz_min, reader.mz_max)
        LOGGER.debug("Loaded MSDT in " + report_time(t_start))
        parameters = reader.get_inf_data()

        data = {
            "mz": MassSpectrumObject(mz_x, mz_y),
            "rt": ChromatogramObject(rt_x, rt_y, extra_data={"yvals_min": rt_x_min}),
            "dt": MobilogramObject(dt_x, dt_y),
            "heatmap": IonHeatmapObject(array, x=dt_x, y=rt_x, xy=dt_y, yy=rt_y),
            "msdt": MassSpectrumHeatmapObject(msdt_array, x=msdt_mz_x, y=msdt_dt_x),
            "parameters": parameters,
        }
        LOGGER.debug("Loaded data in " + report_time(t_start))
        return reader, data

    @check_os("win32")
    def load_waters_im_document(self, path):
        """Load Waters data and set in ORIGAMI document"""
        reader, data = self.load_waters_im_data(path)
        document = ENV.get_new_document("origami", path, data=data)
        document.set_reader("data_reader", reader)

        return document
