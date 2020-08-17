"""Peak container used by UniDec"""
# Standard library imports
import math
import string
from typing import Dict
from typing import List

# Third-party imports
import numpy as np
import matplotlib.cm as cm

# Local imports
from origami.config.config import CONFIG

__author__ = "Michael.Marty; Lukasz Migas"


class Peak:
    """ Class for a single peak. Contains all key parameters for describing and plotting the peak."""

    def __init__(self):
        """Initialize all parameters for the peak to defaults"""
        self.mass = 0
        self.height = 0
        self.area = ""
        self.color = [1, 1, 1]
        self.label = ""
        self.marker = "."
        self.marker_text = "."
        self.ignore = 0
        self.sticks = []
        self.kendrick_num = 0
        self.kendrick_defect = 0
        self.kendrick_mass = 0
        self.score = 0
        self.mass_mean = 0
        self.mass_error = 0
        self.error_fwhm = 0
        self.error_mean = -1
        self.mz_tab = []

    def __repr__(self):
        """Pretty print"""
        return f"{self.__class__.__name__}<mass={self.mass}; height={self.height}>"

    def to_dict(self) -> Dict:
        """Serialize peak"""
        return dict(
            mass=self.mass,
            height=self.height,
            area=self.area,
            color=self.color,
            label=self.label,
            marker=self.marker,
            marker_text=self.marker_text,
            ignore=self.ignore,
            sticks=self.sticks,
            kendrick_num=self.kendrick_num,
            kendrick_defect=self.kendrick_defect,
            kendrick_mass=self.kendrick_mass,
            score=self.score,
            mass_mean=self.mass_mean,
            mass_error=self.mass_error,
            error_fwhm=self.error_fwhm,
            error_mean=self.error_mean,
        )


class Peaks:
    """Class containing all useful data about peaks.

    The peaks themselves are of the Peak class and contained within the self.peaks list.
    """

    _markers = ["o", "v", "^", ">", "s", "d", "*"]
    _text_markers = ["\u25CB", "\u25BD", "\u25B3", "\u25B7", "\u25A2", "\u2662", "\u2606"]
    n_markers = len(_markers)

    def __init__(self):
        """
        Initialize Peaks class and set empty values
        :return: None
        """
        self.peaks = []
        self.changed = 0
        self.convolved = False
        self.composite = None
        self.peak_colors = []
        self.colormap = []
        self.mw_bin_size = 0
        self.norm = 1

    def __repr__(self):
        """Pretty print"""
        return f"{self.__class__.__name__}<n_peaks={self.n_peaks}>"

    def __getitem__(self, item):
        """Return peak"""
        return self.peaks[item]

    @property
    def n_peaks(self):
        """Return the number of peaks"""
        return len(self.peaks)

    @property
    def x(self):
        """Return x-axis"""
        return np.arange(self.n_peaks)

    @property
    def masses(self):
        """Return masses"""
        return np.asarray([p.mass for p in self.peaks])

    @property
    def y(self):
        """Return y-axis"""
        return self.intensities

    @property
    def intensities(self):
        """Return masses"""
        return np.asarray([p.height for p in self.peaks])

    @property
    def markers(self):
        """Return masses"""
        return [p.marker for p in self.peaks]

    @property
    def text_markers(self):
        """Return masses"""
        return [p.marker_text for p in self.peaks]

    @property
    def colors(self):
        """Return masses"""
        return [p.color for p in self.peaks]

    @property
    def labels(self):
        """Return masses"""
        return [p.label for p in self.peaks]

    def to_dict(self) -> Dict:
        """Serialize the list of peaks to a dictionary that can be easily restored"""
        _peaks = []
        for peak in self.peaks:
            _peaks.append([peak.mass, peak.height])

        return dict(peaks=_peaks, convolved=self.convolved, composite=self.composite, changed=self.changed)

    def from_dict(self, peaks: List):
        """Load peaks from dictionary"""

    def add_peaks(self, peaks_array, mw_bin_size: float = 0):
        """
        Create peak objects from an array

        Parameters
        ----------
        peaks_array : np.ndarray
            Nx2 array containing (mass, height) of each peak
        mw_bin_size: float
            describes the precision of the mass inputs by describing the bin size on the mass axis.
        """
        for p in peaks_array:
            peak = Peak()
            peak.mass = p[0]
            peak.height = p[1]
            self.peaks.append(peak)
        self.convolved = False
        self.composite = None
        self.mw_bin_size = mw_bin_size

    def default_params(self, cmap: str = None):
        """Set default parameters for peaks, such as color, label, and marker

        Parameters
        ----------
        cmap: str
            Colormap from matplotlib.cm
        """
        if cmap is None:
            cmap = CONFIG.unidec_plot_colormap

        self.colormap = cm.get_cmap(cmap, self.n_peaks)
        if self.colormap is None:
            self.colormap = cm.get_cmap("rainbow", self.n_peaks)
        self.peak_colors = self.colormap(np.arange(self.n_peaks))
        for i in range(0, len(self.peaks)):
            self.peaks[i].marker = self._markers[i % self.n_markers]
            self.peaks[i].marker_text = self._text_markers[i % self.n_markers]
            self.peaks[i].color = self.peak_colors[i]
            if i >= 26:
                self.peaks[i].label = string.ascii_uppercase[i % 26] + str(int(math.floor(i / 26) + 1))
            else:
                self.peaks[i].label = string.ascii_uppercase[i % 26]

    def get_mass_defects(self, kendrick_mass, mode=0):
        """
        Get the mass defects and mass number for each peak
        Parameters
        ----------
        kendrick_mass: float
            Kendrick reference mass
        mode: int
            Select range of defects 1=(0,1), 0=(-0.5,0.5)
        """
        for p in self.peaks:
            p.kendrick_mass = p.mass / float(kendrick_mass)
            if mode == 1:
                p.kendrick_num = np.floor(p.kendrick_mass)
                p.kendrick_defect = p.kendrick_mass - np.floor(p.kendrick_mass)
            else:
                p.kendrick_num = np.round(p.kendrick_mass)
                p.kendrick_defect = p.kendrick_mass - np.round(p.kendrick_mass)
