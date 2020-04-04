"""Processing module that handles loading of data from various file formats"""
# Standard library imports
import time
import logging

# Third-party imports
import numpy as np

# Local imports
from origami.utils.ranges import get_min_max
from origami.readers.io_mgf import MGFreader
from origami.readers.io_mzml import mzMLreader
from origami.utils.utilities import format_time
from origami.config.environment import ENV
from origami.readers.io_text_files import TextHeatmapReader
from origami.readers.io_text_files import TextSpectrumReader
from origami.readers.io_text_files import AnnotatedDataReader
from origami.readers.io_thermo_raw import thermoRAWreader
from origami.readers.io_waters_raw_api import WatersRawReader

LOGGER = logging.getLogger(__name__)

MGF_N_SCANS = 50000
MZML_N_SCANS = 50000


class LoadHandler:
    def __init__(self):
        """Initialized"""

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

        # sum the first and second axes to obtain the dt and rt values
        array = reader.array
        dt_y = np.sum(array, axis=1).T
        rt_y = np.sum(array, axis=0)

        return array, reader.x, reader.y, dt_y, rt_y

    @staticmethod
    def load_mgf_data(path):
        """Read data from MGF file format"""
        t_start = time.time()
        reader = MGFreader(path)
        LOGGER.debug("Created MGF file reader. Started loading data...")

        data = reader.get_n_scans(MGF_N_SCANS)
        LOGGER.debug("Loaded mzML data in " + format_time(t_start))
        return reader, data

    def load_mgf_document(self, path):
        """Load mgf data and set inside ORIGAMI document"""
        # instantiate document
        document = ENV.get_new_document("mgf", path)

        # read data
        reader, data = self.load_mgf_data(path)

        # set data
        document.tandem_spectra = data
        document.set_reader("data_reader", reader)

        return document

    @staticmethod
    def load_mzml_data(path):
        """Read data from mzML file format"""
        t_start = time.time()
        reader = mzMLreader(path)
        LOGGER.debug("Created mzML file reader. Started loading data...")

        data = reader.get_n_scans(MZML_N_SCANS)
        LOGGER.debug("Loaded mzML data in " + format_time(t_start))
        return reader, data

    def load_mzml_document(self, path):
        """Load mzml data and set inside ORIGAMI document"""
        # instantiate document
        document = ENV.get_new_document("mzml", path)

        # read data
        reader, data = self.load_mzml_data(path)

        # set data
        document.tandem_spectra = data
        document.set_reader("data_reader", reader)

        return document

    @staticmethod
    def load_thermo_data(path):
        """Load Thermo data"""
        reader = thermoRAWreader(path)
        LOGGER.debug("Created Thermo file reader. Started loading data...")

        # get chromatographic data
        rt_x, rt_y = reader.get_tic()

        # get mass spectra
        mass_spectra = reader.get_spectrum_for_each_filter()
        chromatograms = reader.get_chromatogram_for_each_filter()

        # get average spectrum
        mz_x, mz_y = reader.get_average_spectrum()
        x_limits = get_min_max(mz_x)

        data = {
            "mz": {"xvals": mz_x, "yvals": mz_y, "xlimits": x_limits, "xlabels": "m/z (Da)"},
            "rt": {"xvals": rt_x, "yvals": rt_y, "xlabels": "Time (min)"},
            "mass_spectra": mass_spectra,
            "chromatograms": chromatograms,
        }
        return reader, data

    def load_thermo_document(self, path):
        """Load Thermo data and set in ORIGAMI document"""
        reader, data = self.load_thermo_data(path)

        document = ENV.get_new_document("thermo", path)

        document.RT = data["rt"]
        document.massSpectrum = data["mz"]
        document.multipleMassSpectrum = data["mass_spectra"]
        document.multipleRT = data["chromatograms"]
        document.set_reader("data_reader", reader)

        return document

    @staticmethod
    def load_waters_ms_data(path):
        """Load Waters mass spectrometry and chromatographic data"""
        t_start = time.time()
        reader = WatersRawReader(path)
        LOGGER.debug("Initialized Waters reader")

        mz_x, mz_y = reader.get_average_spectrum()
        x_limits = get_min_max(mz_x)
        LOGGER.debug("Loaded spectrum in " + format_time(t_start))

        rt_x, rt_y = reader.get_TIC(0)
        LOGGER.debug("Loaded TIC in " + format_time(t_start))

        parameters = reader.get_inf_data()

        data = {
            "mz": {"xvals": mz_x, "yvals": mz_y, "xlimits": x_limits, "xlabels": "m/z (Da)"},
            "rt": {"xvals": rt_x, "yvals": rt_y, "xlabels": "Scans"},
            "parameters": parameters,
        }

        return reader, data

    def load_waters_ms_document(self, path):
        """Load Waters data and set in ORIGAMI document"""
        reader, data = self.load_waters_ms_data(path)

        document = ENV.get_new_document("waters", path)
        document.parameters = data["parameters"]
        document.massSpectrum = data["mz"]
        document.RT = data["rt"]

        return document
