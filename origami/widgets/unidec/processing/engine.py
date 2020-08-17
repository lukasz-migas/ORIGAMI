"""UniDec Engine code"""
# Standard library imports
import os
import time
import shutil
import logging

# Third-party imports
import numpy as np

# Local imports
from origami.utils.check import isempty
from origami.utils.ranges import get_min_max
from origami.utils.secret import get_short_hash
from origami.utils.utilities import report_time
from origami.objects.containers import MassSpectrumObject
from origami.widgets.unidec.processing import peakstructure
from origami.widgets.unidec.processing.config import UniDecConfig
from origami.widgets.unidec.processing.utilities import unidec_call
from origami.widgets.unidec.processing.utilities import makeconvspecies
from origami.widgets.unidec.processing.utilities import peaks_error_fwhm
from origami.widgets.unidec.processing.utilities import peaks_error_mean
from origami.widgets.unidec.processing.utilities import make_peaks_mz_tab
from origami.widgets.unidec.processing.utilities import simple_peak_detect
from origami.widgets.unidec.processing.utilities import make_peaks_mz_tab_spectrum
from origami.widgets.unidec.processing.containers import UniDecResultsObject

LOGGER = logging.getLogger(__name__)


class UniDecEngine:
    """UniDec engine"""

    def __init__(self):
        self.data = None
        self.config = None
        self.peaks = None
        self.charge_peaks = None

    @property
    def is_processed(self):
        """Flag to indicate whether data has been pre-processed"""
        if self.data:
            return self.data.is_processed
        return False

    @property
    def is_executed(self):
        """Flag to indicated whether UniDec has been executed"""
        if self.data:
            return self.data.is_executed
        return False

    def set_mass_spectrum(
        self, mz_obj: MassSpectrumObject, filename: str = None, output_dir: str = None, clean: bool = False
    ):
        """Set mass spectral data"""

        # instantiate config
        self.config: UniDecConfig = UniDecConfig()
        if filename is None or not isinstance(filename, str):
            filename = get_short_hash()
        if output_dir is None or not isinstance(output_dir, str):
            output_dir = os.getcwd()
        self.config.filename = filename
        self.config.base_filename = os.path.splitext(filename)[0]
        self.config.output_dir = output_dir
        self.config.default_file_names()

        # # set paths
        self.set_paths(clean)

        # instantiate data object
        self.data: UniDecResultsObject = UniDecResultsObject(mz_obj, self.config)

    def set_paths(self, clean: bool = False):
        """Set paths and if necessary, remove old files"""
        # Change paths to unidecfiles folder
        output_dir = os.path.join(self.config.output_dir, self.config.base_filename + "_unidecfiles")

        # remove old directory
        if clean and os.path.isdir(output_dir):
            shutil.rmtree(output_dir)
            LOGGER.info(f"Removed {output_dir}")

        if not os.path.isdir(output_dir):
            try:
                os.mkdir(output_dir)
                LOGGER.info(f"Created {output_dir}")
            except WindowsError:
                time.sleep(0.1)
                try:
                    os.mkdir(output_dir)
                except WindowsError:
                    print("Access was denied. Please try again.")
                    return

        # set current working directory
        os.chdir(output_dir)
        LOGGER.info(f"Change current working directory to `{output_dir}`")

    def process_mass_spectrum(self, mz_obj: MassSpectrumObject = None):
        """Process mass spectrum"""
        # set data parameters in the config
        self.export_config()
        if mz_obj is None:
            mz_obj = self.data.mz_obj

        min_mz, max_mz = get_min_max(mz_obj.x)
        if not isinstance(self.config.mz_min, float):
            self.config.mz_min = min_mz
        if not isinstance(self.config.mz_max, float):
            self.config.mz_max = max_mz

        # set data in the object
        self.data.mz_processed = mz_obj.xy
        self.config.procflag = 1  # noqa

        # export
        self.data.export(self.config.input_filename, self.data.mz_processed)

    def run_unidec(self, silent: bool = False, efficiency: bool = False):
        """Run UniDec"""
        if self.config.procflag == 0:
            raise ValueError("Need to process data first")
        if self.config.is_bad == 1:
            raise ValueError("Mass spectrum does not pass check")

        t_start = time.time()
        self.export_config()
        result = unidec_call(self.config, silent=silent)
        LOGGER.debug(f"UniDec ran for {report_time(t_start)}")

        # successful
        if result == 0:
            self.unidec_imports(efficiency)
            LOGGER.debug(f"File Name=`{self.config.filename}`;  R2={self.config.error}")
        else:
            LOGGER.error(f"UniDec failed with error code: {result}")

    def export_config(self, filename: str = None):
        """Export UniDec configuration file"""
        if filename is None:
            filename = self.config.config_filename
        self.config.export_config(filename)

    def unidec_imports(self, efficiency: bool = False):
        """Import UniDec results from the binary/text files written by the UniDec dll"""
        self.peaks = peakstructure.Peaks()
        self.data.import_data(efficiency)

    def pick_peaks(self):
        """Detect, Normalize, and Output peaks"""
        self.export_config()

        # Detect Peaks and Normalize
        peaks = simple_peak_detect(self.data.mw_raw, self.config)

        if self.config.peaknorm == 0:  # none
            pass
        elif self.config.peaknorm == 1:
            norm = np.divide(np.amax(peaks[:, 1]), 100.0)
            peaks[:, 1] = np.divide(peaks[:, 1], norm)
            self.data.mw_raw[:, 1] = np.divide(self.data.mw_raw[:, 1], norm)
        elif self.config.peaknorm == 2:
            norm = np.sum(peaks[:, 1]) / 100.0
            peaks[:, 1] = peaks[:, 1] / norm
            self.data.mw_raw[:, 1] = self.data.mw_raw[:, 1] / norm
        else:
            norm = np.amax(peaks[:, 1]) / self.data.mw_max
            peaks[:, 1] = peaks[:, 1] / norm
            self.data.mw_raw[:, 1] = self.data.mw_raw[:, 1] / norm

        self.peaks = peakstructure.Peaks()
        self.peaks.add_peaks(peaks, self.config.massbins)
        self.peaks.default_params()  # cmap=self.config.peakcmap)
        self.data.export(self.config.peaks_filename, peaks)
        self.data.peaks = self.peaks

        # generate Intensities of Each Charge State for Each Peak
        mz_tab = make_peaks_mz_tab(self.data.mz_grid, self.peaks, self.config.adductmass)

        # Calculate errors for peaks with FWHM
        peaks_error_fwhm(self.peaks, self.data.mw_raw)
        peaks_error_mean(self.peaks, self.data.mw_grid, self.data.charges, self.data.mw_raw, self.config)

        if self.config.batchflag == 0:
            make_peaks_mz_tab_spectrum(self.data.mz_grid, self.peaks, self.data.mz_processed, mz_tab)
            self.export_config()

        # calculate charge states
        self.get_charge_peaks()

    def convolve_peaks(self):
        """Convolve Peaks with Peak Shape"""
        makeconvspecies(self.data.mz_processed, self.peaks, self.config)

    def get_charge_peaks(self):
        """
        Determines total charge distribution. Imports each charge state as a peak in self.pks.

        Returns
        -------
        charge_peaks : np.ndarray
            array of charges and intensities (Z x 2 array)
        """
        if not isempty(self.data.mz_grid):
            dat = self.data.mz_grid
            c = dat[:, 2]
            x_len = len(np.unique(dat[:, 0]))
            y_len = len(np.unique(dat[:, 1]))
            grid = np.reshape(c, (x_len, y_len))

            charge_intensity = np.sum(grid, axis=0)
            if self.config.peaknorm == 1:
                charge_intensity = charge_intensity / np.amax(charge_intensity) * 100.0
            elif self.config.peaknorm == 2:
                charge_intensity = charge_intensity / np.sum(charge_intensity) * 100.0

            charge_peaks = np.transpose([self.data.charges, charge_intensity])
            np.savetxt(self.config.base_filename + "_chargepeaks.txt", charge_peaks)  # noqa

            peaks = peakstructure.Peaks()
            peaks.add_peaks(charge_peaks, 1)
            peaks.default_params()
            for i, p in enumerate(peaks.peaks):
                p.sticks = grid[:, i]
                p.label = str(int(self.data.charges[i]))
            self.charge_peaks = peaks
            self.data.charge_peaks = self.charge_peaks
            return charge_peaks
        else:
            print("Error: no m/z grid.")
            return None
