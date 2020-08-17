"""UniDec config"""
# Standard library imports
import os
import logging
import platform
from typing import Dict

# Local imports
from origami.config.config import CONFIG

LOGGER = logging.getLogger(__name__)

BASE_PATH = os.path.dirname(__file__)
UNIDEC_PATH = os.path.join(BASE_PATH, "unidec_bin")


class UniDecConfig:
    """UniDec config"""

    def __init__(self):
        self.filename = None
        self.base_filename = None
        self.output_dir = None

        # various data filenames
        self.input_filename = None
        self.config_filename = None
        self.m_filename = None
        self.manual_filename = None
        self.o_filename = None
        self.match_filename = None
        self.peaks_filename = None

        # data attributes
        self.mz_min = None
        self.mz_max = None
        self.numz = 0  # number of charge states
        self.startz = 1  # min charge state
        self.endz = 50  # max charge state
        self.masslb = 1000  # lower mw search space
        self.massub = 500000  # upper mw search space
        self.massbins = 10  # spacing in the mw plot
        self.autopsfun = 0
        self.psfun = 0  # which fit function should be used
        self.peakwindow = 500  # peak window in basic peak detector
        self.peakthresh = 0.1  # peak threshold in basic peak detector
        self.peaknorm = 1  # peak normalization
        self.mzbins = 0  #

        # engine attributes
        self.numit = 100  # number of iterations
        self.isotopemode = 0  # Use isotopic distributions in deconvolution.Output either monoisotopic or average masses
        self.linflag = 2  # flag: linear mode
        self.nativezlb = -100  # native lower charge
        self.nativezub = 100  # native upper charge
        self.msig = 0  # width of mass smooth filter
        self.molig = 0  # mass difference used for mass smooth filter
        self.zzsig = 1  # parameter for defining the width of the charge state smooth
        self.psig = 1  # parameter for defining the width of the data point smooth
        self.adductmass = 1.007276467  # mass of the adduct ion
        self.beta = 0  # used to define the degree of softmax distribution applied to the charge state vectors
        self.automzsig = 0
        self.mzsig = 1  # Expected peak FWHM in m/z (Th)
        self.poolflag = 2  # sets the conversion from m/z to mass => integrate, interpolate, smart
        self.mtabsig = 0  # sets window for mass limitation

        # flags
        self.is_bad = 0
        self.imflag = 0  # flag: ion mobility
        self.procflag = 0  # flag: data was pre-processed
        self.batchflag = 0
        self.aggressiveflag = 0
        self.noiseflag = 0
        self.baselineflag = 1

        # system paths
        self.open_command = None
        self.system = None
        self.UNIDEC_DIR_PATH = None
        self.UNIDEC_DLL_PATH = None
        self.UNIDEC_DEFAULT_NAME = None

        self.setup_dll_paths()

    def get_full_path(self, part_path: str):
        """Return full path to the object"""
        return os.path.join(self.output_dir, self.base_filename + "_unidecfiles", part_path)

    @property
    def config_path(self):
        """Return the full directory"""
        return self.get_full_path(self.config_filename)

    @property
    def out_mw_filename(self):
        """Get default filename"""
        return self.base_filename + "_mass.txt"

    @property
    def out_mw_grid_filename(self):
        """Get default filename"""
        return self.base_filename + "_massgrid.bin"

    @property
    def out_fit_filename(self):
        """Get default filename"""
        return self.base_filename + "_fitdat.bin"

    @property
    def out_baseline_filename(self):
        """Get default filename"""
        return self.base_filename + "_baseline.bin"

    @property
    def out_error_filename(self):
        """Get default filename"""
        return self.base_filename + "_error.txt"

    @property
    def out_mz_grid_filename(self):
        """Get default filename"""
        return self.base_filename + "_grid.bin"

    @property
    def out_peaks_filename(self):
        """Get default filename"""
        return self.base_filename + "_peaks.dat"

    def default_file_names(self):
        """Sets the default file names. For things coming into and out of the program. In theory these can be modified,
         but it might be risky.
        """
        if self.base_filename is None or not isinstance(self.base_filename, str):
            raise ValueError("Incorrect base filename")

        self.input_filename = self.base_filename + "_input.dat"
        self.config_filename = self.base_filename + "_conf.dat"
        self.m_filename = self.base_filename + "_mfile.dat"
        self.manual_filename = self.base_filename + "_manualfile.dat"
        self.o_filename = self.base_filename + "_ofile.dat"
        self.match_filename = self.base_filename + "_match.dat"
        self.peaks_filename = self.base_filename + "_peaks.dat"

    def export_config(self, name):
        """Writes config to file give in name. Typically in format: name value."""

        self.numz = self.endz - self.startz + 1
        f = open(name, "w")
        f.write("imflag " + str(self.imflag) + "\n")  # noqa
        f.write("input " + str(self.input_filename) + "\n")  # noqa
        f.write("output " + str(self.base_filename) + "\n")  # noqa
        f.write("numit " + str(self.numit) + "\n")  # noqa
        f.write("numz " + str(self.numz) + "\n")  # noqa
        f.write("endz " + str(self.endz) + "\n")  # noqa
        f.write("startz " + str(self.startz) + "\n")  # noqa
        f.write("zzsig " + str(self.zzsig) + "\n")  # noqa
        f.write("psig " + str(self.psig) + "\n")  # noqa
        f.write("mzsig " + str(self.mzsig) + "\n")  # noqa
        f.write("psfun " + str(self.psfun) + "\n")  # noqa
        f.write("massub " + str(self.massub) + "\n")  # noqa
        f.write("masslb " + str(self.masslb) + "\n")  # noqa
        f.write("msig " + str(self.msig) + "\n")  # noqa
        f.write("molig " + str(self.molig) + "\n")  # noqa
        f.write("massbins " + str(self.massbins) + "\n")  # noqa
        f.write("peakwindow " + str(self.peakwindow) + "\n")  # noqa
        f.write("peakthresh " + str(self.peakthresh) + "\n")  # noqa
        f.write("adductmass " + str(self.adductmass) + "\n")  # noqa
        f.write("nativezub " + str(self.nativezub) + "\n")  # noqa
        f.write("nativezlb " + str(self.nativezlb) + "\n")  # noqa
        f.write("linflag " + str(self.linflag) + "\n")  # noqa
        f.write("peaknorm " + str(self.peaknorm) + "\n")  # noqa
        f.write("beta " + str(self.beta) + "\n")  # noqa
        f.write("automzsig " + str(self.automzsig) + "\n")  # noqa
        f.write("autopsfun " + str(self.autopsfun) + "\n")  # noqa
        f.close()

    def to_dict(self):
        """Export data to dictionary"""
        output = dict()

        for key, value in self.__dict__.items():
            if not key.isupper():
                output[key] = value
        return output

    def from_dict(self, config: Dict):
        """Import data from dictionary"""
        for key, value in config.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def setup_dll_paths(self):
        """Initialize initial paths for UniDec directories"""
        self.system = platform.system()
        self.UNIDEC_DIR_PATH = UNIDEC_PATH

        if self.system == "Windows":
            self.UNIDEC_DEFAULT_NAME = "UniDec.exe"
            self.open_command = "start "
        elif self.system == "Darwin":
            self.UNIDEC_DEFAULT_NAME = "unidecmac"  # noqa
            self.open_command = "open "
        else:
            self.UNIDEC_DEFAULT_NAME = "unideclinux"
            self.open_command = "gnome-open "  # noqa

        self.UNIDEC_DLL_PATH = os.path.join(self.UNIDEC_DIR_PATH, self.UNIDEC_DEFAULT_NAME)

        LOGGER.debug(f"UniDec DLL path={self.UNIDEC_DLL_PATH}")

    def default_high_res(self):
        """Sets some defaults for high resolution spectra. Leaves other values unchanged."""
        # Interpolate Spectrum at higher resolution
        self.mzbins = 0
        self.linflag = 2
        self.adductmass = 1.007276467
        # Narrow Charge and Mass Range
        self.startz = 1
        self.endz = 50
        self.massub = 500000
        self.masslb = 1000
        # Increase mass resolution and lower peak shape
        self.massbins = 10
        self.mzsig = 1
        self.psfun = 0
        self.isotopemode = 0
        self.molig = 0
        self.msig = 0
        self.numit = 50
        self.zzsig = 1
        self.psig = 1

    def default_low_res(self):
        """Sets some defaults for high resolution spectra. Leaves other values unchanged."""
        # Interpolate Spectrum at higher resolution
        self.mzbins = 1
        self.linflag = 0
        self.adductmass = 1.007276467
        # Narrow Charge and Mass Range
        self.startz = 1
        self.endz = 100
        self.massub = 1000000
        self.masslb = 10000
        # Increase mass resolution and lower peak shape
        self.massbins = 100
        self.mzsig = 10
        self.psfun = 2
        self.isotopemode = 0
        self.molig = 0
        self.msig = 0
        self.numit = 50
        self.zzsig = 1
        self.psig = 1

    def default_nanodisc(self):
        """Sets some defaults for high resolution spectra. Leaves other values unchanged."""
        # Interpolate Spectrum at higher resolution
        self.mzbins = 0
        self.linflag = 2
        self.adductmass = 1.007276467
        # Narrow Charge and Mass Range
        self.startz = 1
        self.endz = 30
        self.massub = 200000
        self.masslb = 20000
        # Increase mass resolution and lower peak shape
        self.massbins = 10
        self.mzsig = 10
        self.psfun = 0
        self.molig = 760
        self.msig = 1
        self.zzsig = 1
        self.psig = 1
        self.isotopemode = 0

    def default_isotopic_res(self):
        """Sets some defaults for isotopic resolution spectra. Leaves other values unchanged."""
        # Interpolate Spectrum at higher resolution
        self.mzbins = 0
        self.linflag = 2
        self.adductmass = 1.007276467
        # Narrow Charge and Mass Range
        self.startz = 1
        self.endz = 30
        self.massub = 30000
        self.masslb = 100
        # Increase mass resolution and lower peak shape
        self.massbins = 0.1
        self.mzsig = 0
        self.psfun = 0
        self.isotopemode = 1
        self.psig = 0

    def default_zero_charge(self):
        """Sets some defaults for when the zero-charge mass spectrum itself is to be deisotoped.
        Leaves other values unchanged.
        """
        self.mzbins = 0
        self.linflag = 2
        self.startz = 1
        self.endz = 1
        self.massbins = 0.1
        self.mzsig = 0.4
        self.psfun = 0
        self.isotopemode = 1
        self.adductmass = 0
        self.mz_min = ""
        self.mz_max = ""

    def set_from_origami_config(self):
        """Set a number of values used by UniDec from ORIGAMI-based settings"""
        self.masslb = CONFIG.unidec_panel_mw_start
        self.massub = CONFIG.unidec_panel_mw_end
        self.massbins = CONFIG.unidec_panel_mw_bin_size
        self.startz = CONFIG.unidec_panel_z_start
        self.endz = CONFIG.unidec_panel_z_end
        self.psfun = CONFIG.unidec_panel_peak_func_dict[CONFIG.unidec_panel_peak_func]
        self.peaknorm = CONFIG.unidec_panel_peak_detect_norm_dict[CONFIG.unidec_panel_peak_detect_norm]
        self.peakwindow = CONFIG.unidec_panel_peak_detect_width
        self.peakthresh = CONFIG.unidec_panel_peak_detect_threshold
        # self.separation = CONFIG.unidec_panel_plot_line_sep
        self.numit = CONFIG.unidec_panel_max_iterations
        # self.isotopemode = CONFIG.
        # self.linflag = CONFIG.
        # self.nativezlb = CONFIG.
        # self.nativezub = CONFIG.
        self.msig = CONFIG.unidec_panel_smooth_mass_width
        self.psig = CONFIG.unidec_panel_smooth_nearby_points
        self.zzsig = CONFIG.unidec_panel_smooth_charge_distribution
        self.beta = CONFIG.unidec_panel_softmax_beta
        self.msig = CONFIG.unidec_panel_smooth_mass_width
        self.adductmass = CONFIG.unidec_panel_adduct_mass
        # # self.automzsig = CONFIG.
        self.mzsig = CONFIG.unidec_panel_peak_width
        self.poolflag = CONFIG.unidec_panel_mz_to_mw_transform_dict[CONFIG.unidec_panel_mz_to_mw_transform]
        # # self.mtabsig = CONFIG.
        # # self.molig = CONFIG.
