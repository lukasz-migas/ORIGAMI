"""Configuration instance"""
# Standard library imports
import os
import time
import logging
import platform
from typing import List
from typing import Union
from itertools import cycle
from collections import OrderedDict

# Third-party imports
from pubsub import pub
from matplotlib.pyplot import colormaps

# Local imports
from origami.objects.misc import CompareItem
from origami.utils.random import get_random_int
from origami.utils.version import __version__
from origami.readers.io_json import read_json_data
from origami.readers.io_json import write_json_data

logger = logging.getLogger(__name__)

MODULE_PATH = os.path.dirname(__file__)
CWD = os.path.dirname(MODULE_PATH)


class Config:
    """Configuration file"""

    def __init__(self):
        """Setup config

        The configuration file contains all (or almost all) of changable variables that are used throughout ORIGAMI.
        Over the time, their names has changed, however in the current iteration, names are usually separated by an
        underscore and indicate what sort of action they are used for. For instance, parameters starting with
        `waterfall_...` will be used to update waterfall-like plots. The value in the configuration file will reflect
        the name in the `Config` instance since values are set using the `setattr` method.
        """

        # Various app defaults
        self.APP_STDIN = None
        self.APP_STDOUT = None
        self.APP_STDERR = None
        self.APP_CWD = CWD
        self.APP_TEMP_DATA_PATH = None
        self.APP_PROCESS_ID = None
        self.APP_ENABLE_LOGGING = False
        self.APP_LOG_PATH = None
        self.APP_LOG_DIR = None
        self.APP_ENABLE_THREADING = True
        self.APP_ENABLE_CONFIG_AUTO_SAVE = True
        self.APP_CHECK_UNIDEC_PATH_AT_START = True
        self.APP_UNIDEC_PATH = None
        self.APP_CHECK_DRIFTSCOPE_PATH_AT_START = True
        self.APP_DRIFTSCOPE_PATH = r"C:\DriftScope\lib"
        self.APP_DRIFTSCOPE_ALT_PATH = "readers/driftscope"
        self.APP_LOAD_CCS_DB_AT_START = True
        self.APP_SYSTEM = platform.system()
        self.APP_START_TIME = time.strftime("%Y_%m_%d-%H-%M-%S", time.gmtime())

        self.DEFAULT_CONFIG_NAME = "origami-config.json"

        # Configurable
        self.version = __version__
        self.debug = True
        self.testing = False

        self.unidec_engine = None
        # fmt: off
        self.links = {
            "home": "https://www.click2go.umip.com/i/s_w/ORIGAMI.html",
            "github": "https://github.com/lukasz-migas/ORIGAMI",
            "cite": "https://doi.org/10.1016/j.ijms.2017.08.014",
            "newVersion": "https://github.com/lukasz-migas/ORIGAMI/releases",
            "guide": "https://origami.lukasz-migas.com/",
            "youtube": "https://www.youtube.com/playlist?list=PLrPB7zfH4WXMYa5CN9qDtl-G-Ax_L6AK8",
            "htmlEditor": "https://html-online.com/editor/",
            "newFeatures":
            "https://docs.google.com/forms/d/e/1FAIpQLSduN15jzq06QCaacliBg8GkOajDNjWn4cEu_1J-kBhXSKqMHQ/viewform",
            "reportBugs":
                "https://docs.google.com/forms/d/e/1FAIpQLSf7Ahgvt-YFRrA61Pv1S4i8nBK6wfhOpD2O9lGt_E3IA0lhfQ/viewform",
            "unidec_cite_1": "https://pubs.acs.org/doi/abs/10.1021/acs.analchem.5b00140",
            "unidec_cite_2": "https://link.springer.com/article/10.1007/s13361-018-1951-9",
            "unidec_github": "https://github.com/michaelmarty/UniDec/releases",
            "about-author": "https://lukasz-migas.com/",
        }
        # fmt: on
        self.watermark = f"""
        <p>
          <span style="color: #808080;"
            >This document was generated using ORIGAMI (v. {self.version}) which is an Open-Source
            software for the analysis of MS and IM-MS datasets. If you would like more
            information, have a look
            <a href="https://doi.org/10.1016/j.ijms.2017.08.014">here</a> and to
            download it for free, have a look
            <a href="https://github.com/lukasz-migas/ORIGAMI/releases">here</a>.</span
          >
        </p>
        """
        # Populate GUI
        self.overlayChoices = sorted(
            [
                "Mask",
                "Transparent",
                "RGB",
                "Mean",
                "Variance",
                "Standard Deviation",
                "RMSD",
                "RMSF",
                "RMSD Matrix",
                "Grid (2->1)",
                "Grid (n x n)",
            ]
        )

        self.colormap_narrow_choices = [
            "Greys",
            "Purples",
            "Blues",
            "Greens",
            "Oranges",
            "Reds",
            "Greys_r",
            "Purples_r",
            "Blues_r",
            "Greens_r",
            "Oranges_r",
            "Reds_r",
            "YlOrBr",
            "YlOrRd",
            "OrRd",
            "PuRd",
            "RdPu",
            "BuPu",
            "GnBu",
            "PuBu",
            "YlGnBu",
            "PuBuGn",
            "BuGn",
            "YlGn",
            "viridis",
            "plasma",
            "inferno",
            "magma",
            "PiYG",
            "PRGn",
            "BrBG",
            "PuOr",
            "RdGy",
            "RdBu",
            "RdYlBu",
            "RdYlGn",
            "Spectral",
            "coolwarm",
        ]

        self.image_format_choices = ["png", "ps", "raw", "eps", "jpeg", "tiff", "pdf", "svg", "svgz"]
        self.plot_style_choices = [
            "Default",
            "ggplot",
            "fivethirtyeight",
            "classic",
            "bmh",
            "seaborn",
            "seaborn-ticks",
            "seaborn-bright",
            "seaborn-dark",
            "seaborn-pastel",
        ]
        self.current_style = "Default"

        self.color_palettes = {
            "HLS": "hls",
            "HUSL": "husl",
            "Cubehelix": "cubehelix",
            "Spectral": "Spectral",
            "Viridis": "viridis",
            "Rainbow": "rainbow",
            "Inferno": "Inferno",
        }
        self.current_palette = "HLS"

        self.availablePlotsList = [
            "MS",
            "MS (compare)",
            "RT",
            "DT",
            "2D",
            "3D",
            "DT/MS",
            "Waterfall",
            "RMSD",
            "Comparison",
            "Overlay",
            "Calibration (MS)",
            "Calibration (DT)",
        ]

        self.textOutputDict = {"comma": ",", "tab": "\t", "space": " "}
        self.textExtensionDict = {"comma": ".csv", "tab": ".txt", "space": ".txt"}

        self.rmsdLocChoices = {
            "leftTop": (5, 95),
            "rightTop": (75, 95),
            "leftBottom": (5, 5),
            "rightBottom": (75, 5),
            "None": (),
        }

        self.interactiveToolsOnOff = {
            "1D": {
                "hover": True,
                "save": True,
                "pan": True,
                "boxzoom": True,
                "crosshair": False,
                "boxzoom_horizontal": True,
                "boxzoom_vertical": False,
                "reset": True,
                "wheel": True,
                "wheelType": "Wheel Zoom X",
                "activeDrag": "Box Zoom",
                "activeWheel": "None",
                "activeInspect": "Hover",
            },
            "2D": {
                "hover": True,
                "save": True,
                "pan": True,
                "boxzoom": True,
                "crosshair": True,
                "boxzoom_horizontal": False,
                "boxzoom_vertical": False,
                "reset": True,
                "wheel": True,
                "wheelType": "Wheel Zoom X",
                "activeDrag": "Box Zoom",
                "activeWheel": "None",
                "activeInspect": "Hover",
            },
            "Overlay": {
                "hover": True,
                "save": True,
                "pan": True,
                "boxzoom": True,
                "crosshair": True,
                "boxzoom_horizontal": False,
                "boxzoom_vertical": False,
                "reset": True,
                "wheel": False,
                "wheelType": "Wheel Zoom X",
                "activeDrag": "Box Zoom",
                "activeWheel": "None",
                "activeInspect": "Hover",
            },
            "All": {
                "hover": True,
                "save": True,
                "pan": True,
                "boxzoom": True,
                "crosshair": True,
                "boxzoom_horizontal": True,
                "boxzoom_vertical": True,
                "reset": True,
                "wheel": True,
                "wheelType": "Wheel Zoom XY",
                "activeDrag": "Box Zoom",
                "activeWheel": "None",
                "activeInspect": "Hover",
            },
        }

        self._plotSettings = {
            "MS": {
                "axes_size": [0.1, 0.5, 0.85, 0.45],
                "gui_size": [10, 6],
                "resize_size": [10, 4],
                "save_size": [0.1, 0.15, 0.85, 0.8],
                "default_name": "MS",
            },
            "MS (compare)": {
                "axes_size": [0.1, 0.1, 0.8, 0.85],
                "gui_size": [8, 8],
                "resize_size": [10, 10],
                "save_size": [0.1, 0.1, 0.8, 0.85],
                "default_name": "MS_compare",
            },
            "RT": {
                "axes_size": [0.1, 0.2, 0.8, 0.75],
                "gui_size": [10, 4],
                "resize_size": [10, 4],
                "save_size": [0.1, 0.15, 0.85, 0.8],
                "default_name": "RT",
            },
            "DT": {
                "axes_size": [0.1, 0.2, 0.8, 0.75],
                "gui_size": [10, 4],
                "resize_size": [10, 4],
                "save_size": [0.1, 0.15, 0.85, 0.8],
                "default_name": "IMS1D",
            },
            "2D": {
                "axes_size": [0.1, 0.1, 0.8, 0.85],
                "gui_size": [8, 8],
                "resize_size": [10, 10],
                "save_size": [0.1, 0.1, 0.8, 0.85],
                "default_name": "IMS2D",
            },
            "3D": {
                "axes_size": [0.1, 0.1, 0.8, 0.85],
                "gui_size": [12, 8],
                "resize_size": [10, 10],
                "save_size": [0.1, 0.1, 0.8, 0.85],
                "default_name": "IMS3D",
            },
            "DT/MS": {
                "axes_size": [0.1, 0.1, 0.8, 0.85],
                "gui_size": [8, 8],
                "resize_size": [10, 10],
                "save_size": [0.1, 0.1, 0.8, 0.85],
                "default_name": "DTMS",
            },
            "MS (DT/RT)": {
                "axes_size": [0.1, 0.2, 0.8, 0.75],
                "gui_size": [10, 4],
                "resize_size": [10, 4],
                "save_size": [0.1, 0.15, 0.85, 0.8],
                "default_name": "MS",
            },
            "Waterfall": {
                "axes_size": [0.05, 0.1, 0.9, 0.85],
                "gui_size": [10, 4],
                "resize_size": [10, 10],
                "save_size": [0.1, 0.1, 0.8, 0.8],
                "default_name": "Waterfall",
            },
            "Violin": {
                "axes_size": [0.15, 0.1, 0.8, 0.85],
                "gui_size": [10, 4],
                "resize_size": [10, 10],
                "save_size": [0.1, 0.1, 0.8, 0.8],
                "default_name": "Violin",
            },
            "RMSD": {
                "axes_size": [0.1, 0.1, 0.8, 0.85],
                "gui_size": [10, 4],
                "resize_size": [10, 10],
                "save_size": [0.1, 0.1, 0.8, 0.85],
                "default_name": "RMSD",
            },
            "RMSF": {
                "axes_size": [0.1, 0.1, 0.8, 0.85],
                "gui_size": [10, 4],
                "resize_size": [10, 10],
                "save_size": [0.1, 0.1, 0.8, 0.85],
                "default_name": "RMSF",
            },
            "Matrix": {
                "axes_size": [0.1, 0.1, 0.8, 0.85],
                "gui_size": [8, 8],
                "resize_size": [10, 10],
                "save_size": [0.1, 0.1, 0.8, 0.85],
                "default_name": "matrix",
            },
            "Comparison": {
                "axes_size": [0.2, 0.2, 0.6, 0.6],
                "gui_size": [8, 8],
                "resize_size": [10, 10],
                "save_size": [0.2, 0.2, 0.6, 0.6],
                "default_name": "comparison",
            },
            "Overlay": {
                "axes_size": [0.1, 0.1, 0.8, 0.85],
                "gui_size": [8, 8],
                "resize_size": [10, 10],
                "save_size": [0.1, 0.1, 0.8, 0.85],
                "default_name": "overlay",
            },
            "Overlay (Grid)": {
                "axes_size": [0.1, 0.1, 0.8, 0.85],
                "gui_size": [8, 8],
                "resize_size": [10, 10],
                "save_size": [0.1, 0.1, 0.8, 0.85],
                "default_name": "overlay",
            },
            "Calibration (MS)": {
                "axes_size": [0.10, 0.15, 0.8, 0.7],
                "gui_size": [10, 4],
                "resize_size": [10, 4],
                "save_size": [0.10, 0.20, 0.8, 0.7],
                "default_name": "calibration_MS",
            },
            "Calibration (DT)": {
                "axes_size": [0.10, 0.15, 0.8, 0.7],
                "gui_size": [6, 6],
                "resize_size": [10, 4],
                "save_size": [0.10, 0.15, 0.8, 0.7],
                "default_name": "calibration_DT",
            },
            "UniDec (MS)": {
                "axes_size": [0.1, 0.2, 0.8, 0.7],
                "gui_size": [6, 3],
                "resize_size": [10, 6],
                "save_size": [0.1, 0.1, 0.8, 0.85],
                "default_name": "unidec_MS",
            },
            "UniDec (MW)": {
                "axes_size": [0.1, 0.2, 0.8, 0.7],
                "gui_size": [6, 3],
                "resize_size": [10, 6],
                "save_size": [0.1, 0.1, 0.8, 0.85],
                "default_name": "unidec_MW",
            },
            "UniDec (m/z vs Charge)": {
                "axes_size": [0.1, 0.1, 0.8, 0.85],
                "gui_size": [6, 6],
                "resize_size": [10, 10],
                "save_size": [0.1, 0.1, 0.8, 0.85],
                "default_name": "unidec_grid_MZvZ",
            },
            "UniDec (Isolated MS)": {
                "axes_size": [0.1, 0.1, 0.8, 0.85],
                "gui_size": [6, 6],
                "resize_size": [10, 6],
                "save_size": [0.1, 0.1, 0.8, 0.85],
                "default_name": "unidec_isolated_MS",
            },
            "UniDec (MW vs Charge)": {
                "axes_size": [0.1, 0.1, 0.8, 0.85],
                "gui_size": [6, 6],
                "resize_size": [10, 10],
                "save_size": [0.1, 0.1, 0.8, 0.85],
                "default_name": "unidec_grid_MWvZ",
            },
            "UniDec (Barplot)": {
                "axes_size": [0.15, 0.1, 0.8, 0.85],
                "gui_size": [6, 6],
                "resize_size": [10, 6],
                "save_size": [0.1, 0.1, 0.8, 0.85],
                "default_name": "unidec_barplot",
            },
            "UniDec (Charge Distribution)": {
                "axes_size": [0.15, 0.1, 0.7, 0.75],
                "gui_size": [6, 3],
                "resize_size": [10, 6],
                "save_size": [0.1, 0.1, 0.8, 0.85],
                "default_name": "unidec_chargeDist",
            },
            "Other (Line)": {
                "axes_size": [0.15, 0.45, 0.75, 0.5],
                "gui_size": [10, 6],
                "resize_size": [10, 4],
                "save_size": [0.1, 0.1, 0.8, 0.85],
                "default_name": "other_line",
            },
            "Other (Multi-line)": {
                "axes_size": [0.15, 0.2, 0.7, 0.7],
                "gui_size": [6, 3],
                "resize_size": [10, 6],
                "save_size": [0.1, 0.1, 0.8, 0.85],
                "default_name": "other_multiline",
            },
            "Other (Barplot)": {
                "axes_size": [0.1, 0.1, 0.8, 0.85],
                "gui_size": [6, 6],
                "resize_size": [10, 10],
                "save_size": [0.1, 0.1, 0.8, 0.85],
                "default_name": "other_barplot",
            },
            "Other (Grid-1D)": {
                "axes_size": [0.15, 0.1, 0.75, 0.85],
                "gui_size": [6, 6],
                "resize_size": [10, 10],
                "save_size": [0.15, 0.1, 0.75, 0.85],
                "default_name": "other_grid1D",
            },
            "Other (Scatter)": {
                "axes_size": [0.15, 0.15, 0.75, 0.8],
                "gui_size": [6, 6],
                "resize_size": [10, 10],
                "save_size": [0.15, 0.15, 0.75, 0.8],
                "default_name": "other_scatter",
            },
            "Other (Waterfall)": {
                "axes_size": [0.1, 0.15, 0.8, 0.8],
                "gui_size": [6, 6],
                "resize_size": [10, 10],
                "save_size": [0.1, 0.15, 0.8, 0.8],
                "default_name": "other_waterfall",
            },
        }

        self.labelsXChoices = [
            "Scans",
            "Collision Voltage (V)",
            "Activation Voltage (V)",
            "Lab Frame Energy (eV)",
            "Activation Energy (eV)",
            "Mass-to-charge (Da)",
            "m/z (Da)",
            "Wavenumber (cm⁻¹)",
        ]

        self.labelsYChoices = [
            "Drift time (bins)",
            "Drift time (ms)",
            "Arrival time (ms)",
            "Collision Cross Section (Å²)",
        ]

        self.panelNames = {
            "MS": 0,
            "RT": 1,
            "1D": 2,
            "2D": 3,
            "MZDT": 4,
            "Waterfall": 5,
            "3D": 6,
            "RMSF": 7,
            "Comparison": 7,
            "Overlay": 7,
            "Calibration": 3,
            "UniDec": 0,
            "Other": 7,
        }

        self.peaklistColNames = {
            "check": 0,
            "ion_name": 1,
            "charge": 2,
            "intensity": 3,
            "color": 4,
            "colormap": 5,
            "alpha": 6,
            "mask": 7,
            "label": 8,
            "method": 9,
            "filename": 10,
        }

        self.driftTopColNames = {"start": 0, "end": 1, "scans": 2, "drift_voltage": 4, "filename": 5}

        self.driftBottomColNames = {"start": 0, "end": 1, "intensity": 2, "charge": 4, "filename": 5}

        self.overlay_list_col_names = {
            "check": 0,
            "dataset_name": 1,
            "dataset_type": 2,
            "document": 3,
            "shape": 4,
            "color": 5,
            "colormap": 6,
            "alpha": 7,
            "mask": 8,
            "label": 9,
            "min_threshold": 10,
            "max_threshold": 11,
            "processed": 12,
            "order": 13,
        }

        self._interactiveSettings = [
            {"name": "", "order": 0, "width": 25, "show": True},
            {"name": "document", "order": 1, "width": 150, "show": True},
            {"name": "type", "order": 2, "width": 90, "show": True},
            {"name": "file/ion/item", "order": 3, "width": 150, "show": True},
            {"name": "title", "order": 4, "width": 40, "show": True},
            {"name": "header", "order": 5, "width": 40, "show": True},
            {"name": "footnote", "order": 6, "width": 40, "show": True},
            {"name": "color/colormap", "order": 7, "width": 75, "show": True},
            {"name": "page", "order": 8, "width": 50, "show": True},
            {"name": "#", "order": 9, "width": 30, "show": True},
        ]
        self.interactiveColNames = {
            "check": 0,
            "document": 1,
            "type": 2,
            "file": 3,
            "title": 4,
            "header": 5,
            "footnote": 6,
            "color": 7,
            "colormap": 7,
            "page": 8,
            "order": 9,
        }

        self.ccsTopColNames = {
            "filename": 0,
            "start": 1,
            "end": 2,
            "protein": 3,
            "charge": 4,
            "ccs": 5,
            "tD": 6,
            "gas": 7,
        }

        self.ccsBottomColNames = {"filename": 0, "start": 1, "end": 2, "ion": 3, "protein": 4, "charge": 5, "format": 6}
        self.ccsDBColNames = {
            "protein": 0,
            "mw": 1,
            "units": 2,
            "charge": 3,
            "ion": 4,
            "hePos": 5,
            "n2Pos": 6,
            "heNeg": 7,
            "n2Neg": 8,
            "state": 9,
            "source": 10,
        }

        # Calibration
        self.elementalMass = {"Hydrogen": 1.00794, "Helium": 4.002602, "Nitrogen": 28.0134}

        # Add default HTML output methods
        self.pageDict = {
            "None": {"name": "None", "layout": "Individual", "rows": None, "columns": None},
            "Rows": {"name": "Rows", "layout": "Rows", "rows": None, "columns": None},
            "Columns": {"name": "Columns", "layout": "Columns", "rows": None, "columns": None},
        }
        self.interactive_pageLayout_choices = ["Individual", "Columns", "Rows", "Grid"]
        self.interactive_wheelZoom_choices = ["Wheel Zoom XY", "Wheel Zoom X", "Wheel Zoom Y"]
        self.interactive_toolbarPosition_choices = ["left", "above", "right", "below"]
        self.interactive_activeDragTools_choices = [
            "Box Zoom",
            "Box Zoom X",
            "Box Zoom Y",
            "Pan",
            "Pan X",
            "Pan Y",
            "auto",
            "None",
        ]
        self.interactive_activeWheelTools_choices = ["Wheel Zoom XY", "Wheel Zoom X", "Wheel Zoom Y", "auto", "None"]
        self.interactive_activeHoverTools_choices = ["Hover", "Crosshair", "auto", "None"]
        self.interactive_colorbarPosition_choices = ["left", "above", "right", "below"]

        # can be removed
        self.dirname = ""

        # mzml/mgf/mzident etc
        self.msms_load_n_scans = 500  # new
        self.msms_show_neutral_loss = False  # new
        self.msms_show_full_label = True  # new
        self.msms_add_arrows = False
        self.msms_line_color_unlabelled = (0, 0, 0)  # new
        self.msms_line_color_labelled = (1, 0, 0)  # new
        self.msms_label_y_offset = 0.02  # new

        self._tandem_show_PTMs_in_table = False  # new
        self._tandem_show_unidentified_in_table = True  # new
        self._tandem_label_format = {"fragment_name": True, "peptide_seq": False, "charge": True, "delta_mz": False}

        self.fragments_tolerance = {"Da": 0.05, "ppm": 25}  # new
        self.fragments_tolerance_limits = {"Da": [0.00, 5, 0.25], "ppm": [0, 500, 25]}  # new
        self.fragments_units_choices = ["Da", "ppm"]  # new
        self.fragments_units = "Da"  # new
        self.fragments_max_matches = 1  # new
        self.fragments_common = {
            "a/x": ["a-all", "x-all"],
            "b/y": ["b-all", "y-all"],
            "c/z": ["c-all", "z-all"],
            "ETD/ECD": ["c-all", "y-all", "z+1/2/3"],
            "CID": ["b-all", "y-all"],
            "Other": [],
        }

        self.fragments_search = {
            "M-ALL": False,
            "M": False,
            "M-nH2O": False,
            "M-nNH3": False,
            "a-ALL": False,
            "a": False,
            "a-nH2O": False,
            "a-nNH3": False,
            "b-ALL": False,
            "b": False,
            "b-nH2O": False,
            "b-nNH3": False,
            "c-ALL": False,
            "c": False,
            "c-nH2O": False,
            "c-nNH3": False,
            "c-dot": False,
            "c+1/2": False,
            "x-ALL": False,
            "x": False,
            "x-nH2O": False,
            "x-nNH3": False,
            "y-ALL": False,
            "y": False,
            "y-nH2O": False,
            "y-nNH3": False,
            "z-ALL": False,
            "z": False,
            "z-nH2O": False,
            "z-nNH3": False,
            "z-dot": False,
            "z+1/2/3": False,
        }

        # window parameters
        self.extraParamsWindow_on_off = False
        self.extraParamsWindow = {
            "General": 0,
            "Plot 1D": 1,
            "Plot 2D": 2,
            "Plot 3D": 3,
            "Colorbar": 4,
            "Legend": 5,
            "RMSD": 6,
            "Waterfall": 7,
            "Violin": 8,
            "Extra": 9,
        }

        self.interactiveParamsWindow_on_off = False

        self.importExportParamsWindow_on_off = False
        self.importExportParamsWindow = {"Peaklist": 0, "Image": 1, "Files": 2}

        # Custom colors dictionary
        self.custom_colors = OrderedDict(
            [
                (0, [16, 71, 185]),
                (1, [50, 140, 0]),
                (2, [241, 144, 0]),
                (3, [76, 199, 197]),
                (4, [143, 143, 21]),
                (5, [38, 122, 255]),
                (6, [38, 143, 73]),
                (7, [237, 187, 0]),
                (8, [120, 109, 255]),
                (9, [179, 78, 0]),
                (10, [128, 191, 189]),
                (11, [137, 136, 68]),
                (12, [200, 136, 18]),
                (13, [197, 202, 61]),
                (14, [123, 182, 255]),
                (15, [69, 67, 138]),
            ]
        )
        self.custom_colors_cycle = cycle(list(self.custom_colors.values()))

        self.overlay_cmaps = [
            "Greys",
            "Purples",
            "Blues",
            "Greens",
            "Oranges",
            "Reds",
            "Greys_r",
            "Purples_r",
            "Blues_r",
            "Greens_r",
            "Oranges_r",
            "Reds_r",
            "YlOrBr",
            "YlOrRd",
            "OrRd",
            "PuRd",
            "RdPu",
            "BuPu",
            "GnBu",
            "PuBu",
            "YlGnBu",
            "PuBuGn",
            "BuGn",
            "YlGn",
        ]
        self.overlay_cmap_cycle = cycle(self.overlay_cmaps)
        self.overlay_defaultMask = 0.4
        self.overlay_defaultAlpha = 0.5

        # previous files
        self.recent_files = []

        # Open windows
        self.WINDOW_SETTINGS = {
            "Plots": {
                "gripper": False,
                "caption": False,
                "close_button": False,
                "show": True,
                "floating": False,
                "title": "Plots",
            },
            "Documents": {
                "gripper": False,
                "caption": True,
                "close_button": True,
                "show": True,
                "floating": False,
                "title": "Documents",
            },
            "Peak list": {
                "gripper": False,
                "caption": True,
                "close_button": True,
                "show": False,
                "floating": False,
                "title": "Peak list",
            },
            "Text files": {
                "gripper": False,
                "caption": True,
                "close_button": True,
                "show": False,
                "floating": False,
                "title": "Text files",
            },
            "Multiple files": {
                "gripper": False,
                "caption": True,
                "close_button": True,
                "show": False,
                "floating": False,
                "title": "Multiple files",
            },
            "Plot parameters": {
                "gripper": False,
                "caption": True,
                "close_button": True,
                "show": False,
                "floating": True,
                "title": "Plot parameters",
            },
        }

        # GUI add-ons
        self.cmap_narrow_choices = [
            "Greys",
            "Purples",
            "Blues",
            "Greens",
            "Oranges",
            "Reds",
            "Greys_r",
            "Purples_r",
            "Blues_r",
            "Greens_r",
            "Oranges_r",
            "Reds_r",
            "YlOrBr",
            "YlOrRd",
            "OrRd",
            "PuRd",
            "RdPu",
            "BuPu",
            "GnBu",
            "YlOrBr_r",
            "YlOrRd_r",
            "OrRd_r",
            "PuRd_r",
            "RdPu_r",
            "BuPu_r",
            "GnBu_r",
            "PuBu",
            "YlGnBu",
            "PuBuGn",
            "BuGn",
            "YlGn",
            "viridis",
            "plasma",
            "inferno",
            "magma",
            "PiYG",
            "PRGn",
            "BrBG",
            "PuOr",
            "RdGy",
            "RdBu",
            "RdYlBu",
            "RdYlGn",
            "Spectral",
            "coolwarm",
        ]
        self.interpolation_choices = [
            "None",
            "nearest",
            "bilinear",
            "bicubic",
            "spline16",
            "spline36",
            "hanning",
            "hamming",
            "hermite",
            "kaiser",
            "quadric",
            "catrom",
            "gaussian",
            "bessel",
            "mitchell",
            "sinc",
            "lanczos",
        ]
        self.normalizationMS_choices = ["Maximum"]
        self.normalization2D_choices = [
            "Maximum",
            "Logarithmic",
            "Natural log",
            "Square root",
            "Least Abs Deviation",
            "Least Squares",
        ]
        self.smoothMS_choices = ["None", "Savitzky-Golay", "Gaussian"]
        self.smooth2D_choices = ["None", "Savitzky-Golay", "Gaussian"]

        self.marker_shape_dict = {
            "square": "s",
            "circle": "o",
            "pentagon": "p",
            "star": "*",
            "diamond": "D",
            "cross": "x",
            "plus": "+",
            "point": ".",
            "vline": ": ",
            "hline": "_",
        }
        self.lineStylesList = ["solid", "dashed", "dashdot", "dotted"]
        self.lineStylesDict = {"-": "solid", "--": "dashed", "-.": "dashdot", ":": "dotted"}
        self.lineHatchDict = OrderedDict(
            [
                ("none", " "),
                ("sparse hatch", "/"),
                ("dense hatch", "//"),
                ("vertical line", "|"),
                ("horizontal line", "-"),
                ("square", "+"),
                ("cross", "X"),
                ("small circles", "o"),
                ("large circles", "O"),
                ("dots", "."),
                ("stars", "*"),
            ]
        )
        self.lineHatchList = ["", "/", " |", "|", "-", "+", "X", "o", "O", ".", "*"]

        self.legendFontChoice = ["xx-small", "x-small", "small", "medium", "large", "x-large", "xx-large"]

        self.horizontal_alignment_list = ["center", "right", "left"]
        self.vertical_alignment_list = ["center", "top", "bottom"]
        self.label_fontsize_list = ["xx-small", "x-small", "small", "medium", "large", "x-large", "xx-large"]
        self.label_fontweight_list = ["ultralight", "light", "normal", "regular", "medium", "bold", "heavy"]
        self.label_font_orientation_list = ["horizontal", "vertical"]

        # MPL interaction parameters
        self.zoom_color_normal = (1, 1, 1)
        self.zoom_color_extract = (1, 0, 0)

        # Smart zoom
        self.smart_zoom_enable = True  # new in v1.3.0.0
        self.smart_zoom_soft_max = 15000  # new in v1.3.0.0
        self.smart_zoom_hard_max = 100000  # new in v1.3.0.0
        self.smart_zoom_downsampling_method_choices = [
            "Auto",
            "Binned (summed)",
            "Binned (mean)",
            "Sub-sampled",
        ]  # new in v1.3.0.0
        self.smart_zoom_downsampling_method = "Auto"  # new in v1.3.0.0
        self.smart_zoom_subsample_default = 5  # new in v1.3.0.0
        self.smart_zoom_view_mode_choices = ["One-view (2D-only)", "Three-view (DT, MS, 2D)"]  # new in v1.3.0.0
        self.smart_zoom_view_mode = "One-view (2D-only)"  # new in v1.3.0.0
        self.smart_zoom_min_search = 1  # new in v1.3.0.0
        self.smart_zoom_max_search = 20  # new in v1.3.0.0

        # Annotation
        self.annotation_charge_std_dev = 0.05
        self.annotation_arrow_line_width = 0.5
        self.annotation_arrow_line_style = "dashed"
        self.annotation_arrow_cap_length = 0.01  # new in v1.2.1
        self.annotation_arrow_cap_width = 0.01  # new in v1.2.1
        self.annotation_label_y_offset = 0.05  # new in v1.2.1
        self.annotation_label_horz = "center"
        self.annotation_label_vert = "center"
        self.annotation_label_font_size = "small"
        self.annotation_label_font_weight = "normal"
        self.annotation_label_font_orientation = "horizontal"
        self.annotation_zoom_y = False  # new in v1.2.1
        self.annotation_zoom_y_multiplier = 1.5  # new in v1.2.1
        self.annotation_show_vline = False  # new in v1.2.1
        self.annotation_patch_transparency = 0.2  # new in v1.2.1
        self.annotation_patch_width = 3  # new in v1.2.1

        # UniDec
        self.unidec_mzStart = 500
        self.unidec_mzEnd = 8000
        self.unidec_mzBinSize = 0.1
        self.unidec_gaussianFilter = 0.0
        self.unidec_linearization_choices = {
            "Linear m/z": 0,
            "Linear resolution": 1,
            "Nonlinear": 2,
            "Linear interpolation": 3,
            "Linear resolution interpolation": 4,
        }
        self.unidec_linearization = "Linear m/z"
        self.unidec_accelerationV = 0.0
        self.unidec_zStart = 1
        self.unidec_zEnd = 100
        self.unidec_mwStart = 500
        self.unidec_mwEnd = 150000
        self.unidec_mwFrequency = 100
        self.unidec_peakWidth = 2.0
        self.unidec_peakWidth_auto = True
        self.unidec_peakFunction_choices = {"Gaussian": 0, "Lorentzian": 1, "Split G/L": 2}
        self.unidec_peakFunction = "Lorentzian"

        self.unidec_peakDetectionWidth = 500.0
        self.unidec_peakDetectionThreshold = 0.1
        self.unidec_peakNormalization_choices = {"None": 0, "Max": 1, "Total": 2}
        self.unidec_peakNormalization = "Max"
        self.unidec_lineSeparation = 0.05
        self.unidec_maxIterations = 100
        self.unidec_charges_label_charges = 0.05
        self.unidec_charges_offset = 0.01
        self.unidec_show_individualComponents = True
        self.unidec_show_markers = True
        self.unidec_speedy = True
        self.unidec_show_chargeStates = False
        self.unidec_maxShown_individualLines = 100
        self.unidec_optimiseLabelPositions = True

        self.unidec_plot_fit_lineColor = (1.0, 0.0, 0.0)
        self.unidec_plot_MW_showMarkers = True
        self.unidec_plot_MW_markerSize = 50
        self.unidec_plot_isolatedMS_markerSize = 50
        self.unidec_plot_bar_markerSize = 50
        self.unidec_plot_bar_width = 1
        self.unidec_plot_bar_alpha = 1.0
        self.unidec_plot_bar_edge_color = (0.0, 0.0, 0.0)
        self.unidec_plot_bar_sameAsFill = False
        self.unidec_plot_bar_lineWidth = 2.0
        self.unidec_plot_color_scheme = "Color palette"
        self.unidec_plot_colormap = "viridis"
        self.unidec_plot_palette = "HLS"
        self.unidec_plot_contour_levels = 75
        self.unidec_plot_panel_view = "Tabbed view"

        # ORIGAMI
        self.origami_method_choices = ["Linear", "Exponential", "Boltzmann", "User-defined"]
        self.origami_method = "Linear"
        self.origami_scans_per_voltage = 3
        self.origami_start_voltage = 4
        self.origami_start_scan = 0
        self.origami_end_voltage = 200
        self.origami_step_voltage = 2
        self.origami_boltzmann_offset = 0
        self.origami_exponential_percentage = 0
        self.origami_exponential_increment = 0
        self.origami_user_defined_list = []
        self.origami_preprocess = True  # new in v1.3.0.0

        # Extracting
        self.extract_mz = False
        self.extract_mz_use_mz = True
        self.extract_mz_use_rt = True
        self.extract_mz_use_dt = True
        self.extract_rt = False
        self.extract_rt_use_mz = True
        self.extract_rt_use_dt = True
        self.extract_dt = False
        self.extract_dt_use_mz = True
        self.extract_dt_use_rt = True
        self.extract_heatmap = False
        self.extract_heatmap_use_mz = True
        self.extract_heatmap_use_rt = True
        self.extract_mz_start = 0
        self.extract_mz_end = 0
        self.extract_rt_start = 0
        self.extract_rt_end = 999
        self.extract_dt_start = 1
        self.extract_dt_end = 200
        self.extract_rt_use_scans = False  # new in v1.3.0.0
        self.extract_dt_use_ms = False  # new in v1.3.0.0

        # Annotation parameters
        # Panel settings
        self.annotate_panel_highlight = True
        self.annotate_panel_zoom_in = True
        self.annotate_panel_zoom_in_window = 5
        self.annotate_panel_add_to_table = True
        self.annotate_panel_patch_color = (1, 0, 0)
        self.annotate_panel_patch_alpha = 0.5
        self.annotate_panel_label_color = (0, 0, 0)

        # Comparison parameters
        # Panel settings
        self.compare_color_top = (0, 0, 0)
        self.compare_color_bottom = (0, 0, 1)
        self.compare_style_top = "solid"
        self.compare_style_bottom = "solid"
        self.compare_alpha_top = 1.0
        self.compare_alpha_bottom = 1.0
        self.compare_inverse = True
        self.compare_panel_preprocess = True
        self.compare_panel_normalize = True
        self.compare_panel_subtract = True
        self.compare_panel_top_ = CompareItem()
        self.compare_panel_bottom_ = CompareItem()

        # new version
        self.new_version_panel_link = r"https://github.com/lukasz-migas/ORIGAMI/releases"
        self.new_version_panel_do_not_ask = False

        # Main plot events
        # events in MS panel
        self.plot_panel_ms_extract_auto = True
        self.plot_panel_ms_extract_rt = True
        self.plot_panel_ms_extract_heatmap = True
        self.plot_panel_ms_extract_mobilogram = True

        # events in RT panel
        self.plot_panel_rt_extract_auto = True
        self.plot_panel_rt_extract_ms = True
        self.plot_panel_rt_extract_mobilogram = True

        # events in DT panel
        self.plot_panel_dt_extract_auto = True
        self.plot_panel_dt_extract_ms = True
        self.plot_panel_dt_extract_rt = True

        # Document tree
        self.tree_panel_delete_item_ask = True
        self.tree_panel_delete_group_ask = True
        self.tree_panel_delete_document_ask = True
        self.tree_panel_item_highlight = True
        self.tree_panel_item_auto_plot = False

        # LESA viewer
        self.lesa_panel_extract_full = False
        self.lesa_panel_auto_add = False

        # Duplicate panel
        self.import_duplicate_panel_action = "merge"
        self.import_duplicate_panel_ask = False

        # Peak-picking parameters
        # Panel settings
        self.peak_panel_method_choices = ["small_molecule", "native_local", "native_differential"]
        self.peak_panel_method_choice = "small_molecule"
        self.peak_panel_specify_mz = False
        self.peak_panel_mz_start = None
        self.peak_panel_mz_end = None
        self.peak_panel_preprocess = True
        self.peak_panel_verbose = False
        self.peak_panel_method = None
        self.peak_panel_scatter = True
        self.peak_panel_highlight = True
        self.peak_panel_labels = True
        self.peak_panel_labels_mz = True
        self.peak_panel_labels_int = True
        self.peak_panel_labels_width = False
        self.peak_panel_optimise_position = True
        self.peak_panel_labels_max_count = 100
        self.peak_panel_filter_choices = ["Score", "Width (no. bins)", "Width (Da)"]
        self.peak_panel_filter_choice = "Width (Da)"
        self.peak_panel_score_choices = ["asymmetry", "tailing", "slopes"]
        self.peak_panel_score_choice = "asymmetry"

        # Extract DT/MS
        self.msdt_panel_extract_mz_start = 200
        self.msdt_panel_extract_mz_end = 5000
        self.msdt_panel_extract_mz_bin_size = 0.1

        # Process 2D
        self.heatmap_crop = False  # new in v1.3.0.0
        self.heatmap_crop_xmin = 0  # new in v1.3.0.0
        self.heatmap_crop_xmax = 5000  # new in v1.3.0.0
        self.heatmap_crop_ymin = 0  # new in v1.3.0.0
        self.heatmap_crop_ymax = 200  # new in v1.3.0.0

        self.heatmap_interpolate = True  # new in v1.3.0.0
        self.heatmap_interpolate_choices = ["Linear", "Cubic", "Quintic"]  # new in v1.3.0.0s
        self.heatmap_interpolate_mode = "Linear"  # new in v1.3.0.0
        self.heatmap_interpolate_xaxis = True  # new in v1.3.0.0
        self.heatmap_interpolate_yaxis = False  # new in v1.3.0.0
        self.heatmap_interpolate_fold = 2  # new in v1.3.0.0

        self.heatmap_smooth = True  # new in v1.3.0.0
        self.heatmap_smooth_choices = ["Gaussian", "Savitzky-Golay"]
        self.heatmap_smooth_mode = "Gaussian"
        self.heatmap_smooth_sigma = 1
        self.heatmap_smooth_window = 3
        self.heatmap_smooth_polynomial = 1

        self.heatmap_threshold = True  # new in v1.3.0.0
        self.heatmap_threshold_lower = 0.0

        self.heatmap_normalize = False
        self.heatmap_normalize_choices = [
            "Maximum",
            "Logarithmic",
            "Natural log",
            "Square root",
            "Least Abs Deviation",
            "Least Squares",
        ]
        self.heatmap_normalize_mode = "Maximum"

        # Process MS
        self.ms_crop = False
        self.ms_crop_min = 500
        self.ms_crop_max = 8000

        self.ms_linearize = True
        self.ms_linearize_mz_start = 500
        self.ms_linearize_mz_end = 8000
        self.ms_linearize_mz_auto_range = True
        self.ms_linearize_mz_bin_size = 1
        self.ms_linearize_method_choices = [
            "Linear m/z",
            "Linear resolution",
            "Nonlinear",
            "Linear interpolation",
            "Linear resolution interpolation",
            "Binning",
        ]
        self.ms_linearize_method = "Linear interpolation"

        self.ms_smooth = True
        self.ms_smooth_choices = ["Gaussian", "Savitzky-Golay", "Moving average"]  # new in v1.3.0.0
        self.ms_smooth_mode = "Gaussian"
        self.ms_smooth_sigma = 1
        self.ms_smooth_window = 3
        self.ms_smooth_polynomial = 1
        self.ms_smooth_moving_window = 5  # new in v1.3.0.0

        self.ms_threshold = True
        self.ms_baseline_method_choices = ["Linear", "Polynomial", "Curved", "Median", "Top Hat"]  # new in v1.3.0.0
        self.ms_baseline_method = "Linear"
        self.ms_baseline_linear_threshold = 0.0  # new in v1.3.0.0
        self.ms_baseline_polynomial_order = 3  # new in v1.3.0.0
        self.ms_baseline_curved_window = 500  # new in v1.3.0.0
        self.ms_baseline_median_window = 5  # new
        self.ms_baseline_tophat_window = 100  # new

        self.ms_normalize = True

        # Local-max settings
        self.peak_local_threshold = 0.01
        self.peak_local_window = 10
        self.peak_local_relative_height = 0.75

        # Differential settings
        self.peak_differential_threshold = 0.01
        self.peak_differential_window = 10
        self.peak_differential_relative_height = 0.75

        # Small-molecule settings
        self.peak_property_threshold = 250  # new in v1.3.0.0
        self.peak_property_width = 0  # new in v1.3.0.0
        self.peak_property_relative_height = 0.5  # new in v1.3.0.0
        self.peak_property_min_intensity = 0.0  # new in v1.3.0.0
        self.peak_property_distance = 1  # new in v1.3.0.0
        self.peak_property_peak_width_modifier = 1.0  # new in v1.3.0.0

        # UVPD
        self.uvpd_peak_finding_threshold = 0.1  # new in v1.2.1
        self.uvpd_peak_buffer_width = 1  # new in v1.2.1
        self.uvpd_peak_first_index = 1  # new in v1.2.1
        self.uvpd_peak_laser_on = (1, 0, 0)  # new in v1.2.1
        self.uvpd_peak_laser_off = (0, 0, 1)  # new in v1.2.1
        self.uvpd_peak_show_markers = True  # new in v1.2.1
        self.uvpd_peak_show_patches = False  # new in v1.2.1
        self.uvpd_peak_show_labels = False  # new in v1.2.1

        # RMSD
        self.rmsd_position_choices = ["bottom left", "bottom right", "top left", "top right", "none", "other"]
        self.rmsd_label_position = "bottom left"
        self.rmsd_location = (5, 5)
        self.rmsd_color = (1, 1, 1)
        self.rmsd_label_font_size = 10
        self.rmsd_label_font_weight = True
        self.rmsd_rotation_x = 45
        self.rmsd_rotation_y = 0
        self.rmsd_matrix_add_labels = True
        self.rmsd_matrix_font_size = 12  # new in v2.0.0
        self.rmsd_matrix_font_weight = False  # new in v2.0.0
        self.rmsd_matrix_font_color_choices = ["auto", "user-defined"]  # new in v2.0.0
        self.rmsd_matrix_font_color_fmt = "auto"  # new in v2.0.0
        self.rmsd_matrix_font_color = (0, 0, 0)
        self.rmsf_line_color = (0, 0, 0)
        self.rmsf_line_transparency = 0.4
        self.rmsf_line_width = 1
        self.rmsf_line_style = "solid"
        self.rmsf_fill_color = (0, 0, 0)
        self.rmsf_fill_transparency = 0.4
        self.rmsf_fill_hatch = " "
        self.rmsf_h_space = 0.1

        # Importing files
        self.import_binOnImport = True  # REMOVE

        # waterfall
        self.waterfall = False
        self.waterfall_increment = 0.05
        self.waterfall_offset = 0
        self.waterfall_reverse = False
        self.waterfall_normalize = True
        self.waterfall_line_width = 1
        self.waterfall_line_style = "solid"
        self.waterfall_line_color = [0, 0, 0]
        self.waterfall_line_same_as_fill = True
        self.waterfall_color_choices = ["Same color", "Colormap", "Color palette", "Random"]  # new
        self.waterfall_colormap = "viridis"
        self.waterfall_color_scheme = "Same color"
        self.waterfall_palette = "HLS"
        self.waterfall_fill_under = True
        self.waterfall_fill_under_color = [0, 0, 0]
        self.waterfall_fill_under_nlimit = 1000
        self.waterfall_fill_under_transparency = 0.25
        self.waterfall_labels_show = False
        self.waterfall_labels_frequency = 1
        self.waterfall_labels_x_offset = 0.05
        self.waterfall_labels_y_offset = 0.05
        self.waterfall_labels_font_size = 12
        self.waterfall_labels_font_weight = True
        self.waterfall_labels_format_choices = ["String", "Float", "Integer"]
        self.waterfall_labels_format = "Float"

        # violin
        self.violin_orientation_choices = ["vertical", "horizontal"]
        self.violin_orientation = "vertical"
        self.violin_n_limit = 50
        self.violin_spacing = 0.5
        self.violin_min_percentage = 0.03
        self.violin_normalize = True
        self.violin_smooth = True
        self.violin_smooth_sigma = 2
        self.violin_line_width = 2
        self.violin_line_style = "solid"
        self.violin_line_color = [0, 0, 0]
        self.violin_color_choices = ["Same color", "Colormap", "Color palette", "Random"]
        self.violin_colormap = "viridis"
        self.violin_color_scheme = "Colormap"
        self.violin_line_same_as_fill = False
        self.violin_fill_under = True
        self.violin_fill_under_color = [0, 0, 0]
        self.violin_fill_under_transparency = 1
        self.violin_labels_format_choices = ["String", "Float", "Integer"]
        self.violin_labels_format = "Integer"
        self.violin_labels_frequency = 1
        self.violin_palette = "HLS"

        # colorbar
        self.colorbar = False
        self.colorbar_fmt_choices = ["0 % 100", "true-values (pretty)", "true-values (raw)"]  # new
        self.colorbar_label_fmt = "0 % 100"  # new
        self.colorbar_height = 100  # new (%)
        self.colorbar_width = 2
        self.colorbar_pad = 0.03
        self.colorbar_min_points = 5
        self.colorbar_position_choices = [
            "left",
            "right",
            "top",
            "bottom",
            "inside (top-left)",
            "inside (top-right)",
            "inside (bottom-left)",
            "inside (bottom-right)",
        ]
        self.colorbar_orientation_choices = ["vertical", "horizontal"]
        self.colorbar_position = "right"
        self.colorbar_label_size = 12
        self.colorbar_edge_color = (0, 0, 0)
        self.colorbar_label_color = (0, 0, 0)
        self.colorbar_edge_width = 1
        self.colorbar_inset_width = 25

        # legend
        self.legend = False
        self.legend_frame = True
        self.legend_marker_first = True
        self.legend_position_choices = [
            "best",
            "upper right",
            "upper left",
            "lower left",
            "lower right",
            "right",
            "center left",
            "center right",
            "lower center",
            "upper center",
            "center",
        ]
        self.legend_position = "best"
        self.legend_font_size = "small"
        self.legend_n_columns = 1
        self.legend_marker_size = 1
        self.legend_n_markers = 1
        self.legend_transparency = 0.5
        self.legend_fancy_box = True
        self.legend_line_width = 4
        self.legend_patch_transparency = 0.25

        # axes parameters
        self.axes_frame_show = True
        self.axes_frame_spine_left = True
        self.axes_frame_spine_right = True
        self.axes_frame_spine_top = True
        self.axes_frame_spine_bottom = True
        self.axes_frame_ticks_left = True
        self.axes_frame_ticks_right = False
        self.axes_frame_ticks_top = False
        self.axes_frame_ticks_bottom = True
        self.axes_frame_tick_labels_left = True
        self.axes_frame_tick_labels_right = False
        self.axes_frame_tick_labels_top = False
        self.axes_frame_tick_labels_bottom = True
        self.axes_frame_labels_left = True
        self.axes_frame_labels_right = False
        self.axes_frame_labels_top = False
        self.axes_frame_labels_bottom = True
        self.axes_frame_width = 1
        self.axes_title_font_size = 18
        self.axes_title_font_weight = False
        self.axes_label_pad = 5
        self.axes_label_font_size = 16
        self.axes_label_font_weight = False
        self.axes_tick_font_size = 16
        self.axes_tick_font_weight = False
        self.axes_annotation_font_size = 10
        self.axes_annotation_font_weight = False

        # line parameters
        self.spectrum_line_color = (0, 0, 0)
        self.spectrum_line_width = 1
        self.spectrum_line_style = "solid"
        self.spectrum_line_fill_under = True
        self.spectrum_fill_color = (0, 0, 0)
        self.spectrum_fill_transparency = 0.5

        # marker parameters
        self.marker_fill_color = (0, 0, 1)
        self.marker_transparency = 0.4
        self.marker_edge_same_as_fill = True
        self.marker_edge_color = (0, 0, 1)
        self.marker_shape_dict = {
            "square": "s",
            "circle": "o",
            "pentagon": "p",
            "star": "*",
            "diamond": "D",
            "cross": "x",
        }
        self.marker_shape_choices = list(self.marker_shape_dict.keys())
        self.marker_shape = "o"
        self.marker_shape_txt = "circle"
        self.marker_size = 5

        # bar parameters
        self.bar_width = 0.1
        self.bar_alpha = 1.0
        self.bar_edge_color = (0.0, 0.0, 0.0)
        self.bar_edge_same_as_fill = True
        self.bar_line_width = 1.0

        # heatmap (2d) parameters
        self.heatmap_plot_type_choices = ("Image", "Contour")
        self.heatmap_plot_type = "Image"
        self.heatmap_n_contour = 100
        self.heatmap_colormap = "viridis"
        self.heatmap_normalization_choices = ["MinMax", "Midpoint", "Logarithmic", "Power"]
        self.heatmap_normalization = "Midpoint"
        self.heatmap_normalization_min = 0
        self.heatmap_normalization_mid = 50
        self.heatmap_normalization_max = 100
        self.heatmap_normalization_power_gamma = 0.5
        self.heatmap_interpolation_choices = [
            "None",
            "nearest",
            "bilinear",
            "bicubic",
            "spline16",
            "spline36",
            "hanning",
            "hamming",
            "hermite",
            "kaiser",
            "quadric",
            "catrom",
            "gaussian",
            "bessel",
            "mitchell",
            "sinc",
            "lanczos",
        ]
        self.heatmap_interpolation = "None"

        # heatmap (3d) parameters
        self.heatmap_3d_colormap = "viridis"
        self.heatmap_3d_axis_color = (1, 1, 1)
        self.heatmap_3d_background_color = (0, 0, 0)
        self.heatmap_3d_opacity = 1.0
        self.heatmap_3d_clim_min = 0.0
        self.heatmap_3d_clim_max = 1.0
        self.heatmap_3d_axis_font_size = 16
        self.heatmap_3d_axis_tick_size = 16
        self.heatmap_3d_axis_x_margin = 35
        self.heatmap_3d_axis_y_margin = 75
        self.heatmap_3d_axis_z_margin = 35

        # Settings Panel
        self.lastDir = None
        self.image_folder_path = None  # NEW v1.3.0.0
        self.image_size_inch = [8, 8]
        self.image_size_cm = []
        self.image_size_px = []
        self.image_axes_size = [0.12, 0.12, 0.8, 0.8]

        self.data_folder_path = None  # New v1.3.0.0

        # Events
        self.extraParamsWindow_on_off = False

        # Presets
        self.userParameters = {
            "operator": "Lukasz G. Migas",
            "contact": "lukasz.migas@manchester.ac.uk",
            "institution": "University of Manchester",
            "instrument": "SynaptG2",
            "date": "date",
        }

        self.resize = True
        # =========== DOCUMENT TREE PARAMETERS ==========
        self.ccsDB = None  # REMOVE
        self.proteinData = None  # REMOVE
        self.origamiList = []  # REMOVE

        self.overlayMethod = "Transparent"
        self.textOverlayMethod = "Mask"

        self.dpi = 200
        self.transparent = True
        self.image_tight = True
        self.imageWidthInch = 8
        self.imageHeightInch = 8
        self.imageFormat = "png"

        # Export CSV
        self.saveDelimiterTXT = "comma"
        self.saveDelimiter = ","
        self.saveExtension = ".csv"

        # Initialize colormaps
        self.colormap_choices = sorted(colormaps())

        # ===============================================================================
        # # Interactive parameters
        # ===============================================================================

        self.saveInteractiveOverride = True

        self.figHeight = 600
        self.figWidth = 600
        self.figHeight1D = 300
        self.figWidth1D = 800

        self.layoutModeDoc = "Individual"
        self.plotLayoutOverlay = "Rows"
        self.defNumRows = ""
        self.defNumColumns = ""
        self.linkXYaxes = True
        self.hoverVline = True
        self.interactive_cvd_cmap = "viridis"
        self.interactive_cvd_cmap_choices = ["magma", "viridis", "cividis", "plasma", "magma"]

        self.toolsLocation = "right"
        self.activeDrag = "Box Zoom"
        self.activeWheel = "None"
        self.activeInspect = "Hover"

        self.interactive_custom_scripts = True
        self.interactive_custom_events = True
        self.interactive_custom_position = "right"

        # Other
        self.interactive_override_defaults = True
        self.openInteractiveOnSave = True
        self.interactive_add_offline_support = False
        self.interactive_sort_before_saving = True  # new in v1.2.1

        # Colorbar
        self.interactive_colorbar = False
        self.interactive_colorbar_precision = 1
        self.interactive_colorbar_label_offset = 2
        self.interactive_colorbar_useScientific = False
        self.interactive_colorbar_location = "right"
        self.interactive_colorbar_orientation = "vertical"
        self.interactive_colorbar_offset_x = 5
        self.interactive_colorbar_offset_y = 0
        self.interactive_colorbar_width = 15
        self.interactive_colorbar_padding = 10
        self.interactive_colorbar_edge_color = (0.0, 0.0, 0.0)  # new in v1.2.1
        self.interactive_colorbar_edge_width = 2  # new in v1.2.1
        self.interactive_colorbar_modify_ticks = False  # new in v1.2.1
        self.interactive_colorbar_label_fontSize = 16  # new in v1.2.1
        self.interactive_colorbar_label_weight = False  # new in v1.2.1
        self.interactive_colorbar_title_fontSize = 16  # new in v1.2.1
        self.interactive_colorbar_title_weight = False  # new in v1.2.1

        # Frame
        self.interactive_outline_width = 2
        self.interactive_outline_alpha = 1
        self.interactive_border_min_left = 20
        self.interactive_border_min_right = 20
        self.interactive_border_min_top = 20
        self.interactive_border_min_bottom = 20
        self.interactive_background_color = (1.0, 1.0, 1.0)
        self.interactive_grid_line = False
        self.interactive_grid_line_color = (1.0, 1.0, 1.0)

        # Fonts
        self.interactive_title_fontSize = 16
        self.interactive_title_weight = False
        self.interactive_label_fontSize = 14
        self.interactive_label_weight = False
        self.interactive_tick_fontSize = 12
        self.interactive_annotation_fontSize = 12
        self.interactive_annotation_weight = False
        self.interactive_annotation_color = (0, 0, 0)
        self.interactive_annotation_background_color = (1, 1, 1)
        self.interactive_annotation_alpha = 1

        # Overlay grid
        self.interactive_grid_label = True
        self.interactive_grid_label_size = 12
        self.interactive_grid_label_weight = False
        self.interactive_grid_label_color = (0, 0, 0)
        self.interactive_grid_xpos = 10
        self.interactive_grid_ypos = 10

        # Waterfall
        self.interactive_waterfall_increment = 0.05  # new in v1.2.1
        self.interactive_waterfall_shade_under = False  # new in v1.2.1
        self.interactive_waterfall_shade_alpha = 0.25  # new in v1.2.1

        # Mass spectra
        self.interactive_ms_annotations = True
        self.interactive_ms_annotations_color = (0.18, 0.8, 0.44)
        self.interactive_ms_annotations_line_color = (0, 0, 0)
        self.interactive_ms_annotations_transparency = 0.3
        self.interactive_ms_linearize = True
        self.interactive_ms_binSize = 0.1

        self.interactive_ms_annotations_offsetX = 5
        self.interactive_ms_annotations_offsetY = 5
        self.interactive_ms_annotations_fontSize = 10
        self.interactive_ms_annotations_fontWeight = True
        self.interactive_ms_annotations_highlight = False
        self.interactive_ms_annotations_labels = True
        self.interactive_ms_annotations_rotation = 90
        self.interactive_ms_annotations_label_color = (0.0, 0.0, 0.0)

        # Ticks
        self.interactive_tick_useScientific = True
        self.interactive_tick_precision = 1

        # Legend
        self.interactive_legend = True
        self.interactive_legend_click_policy_choices = ["hide", "mute"]
        self.interactive_legend_click_policy = "hide"
        self.interactive_legend_location_choices = [
            "top_left",
            "top_center",
            "top_right",
            "center_right",
            "bottom_right",
            "bottom_center",
            "bottom_left",
            "center_left",
            "center",
        ]  # , "other"]
        self.interactive_legend_location = "top_left"
        self.interactive_legend_mute_alpha = 0.25
        self.interactive_legend_background_alpha = 0.5
        self.interactive_legend_orientation_choices = ["vertical", "horizontal"]
        self.interactive_legend_orientation = "vertical"
        self.interactive_legend_font_size = 10

        # Line
        self.interactive_line_style_choices = ["solid", "dashed", "dotted", "dotdash", "dashdot"]
        self.interactive_line_style = "solid"
        self.interactive_line_width = 2
        self.interactive_line_alpha = 1
        self.interactive_line_shade_under = False  # new in v1.2.1
        self.interactive_line_shade_alpha = 0.25  # new in v1.2.1
        self.interactive_line_color = (0.0, 0.0, 0.0)  # new in v1.2.1

        # Scatter
        self.interactive_scatter_size = 10
        self.interactive_scatter_alpha = 1.0
        self.interactive_scatter_marker_choices = [
            "circle",
            "square",
            "triangle",
            "circle_cross",
            "square_cross",
            "diamond",
            "circle_x",
            "square_x",
            "inverted_triangle",
            "cross",
            "x",
            "asterisk",
        ]
        self.interactive_scatter_marker = "circle"
        self.interactive_scatter_sameAsFill = True
        self.interactive_scatter_edge_color = (0.0, 0.0, 0.0)
        self.interactive_scatter_lineWidth = 1.0  # new in v1.2.1

        # bar
        self.interactive_bar_width = 0.1
        self.interactive_bar_alpha = 1.0
        self.interactive_bar_edge_color = (0.0, 0.0, 0.0)
        self.interactive_bar_sameAsFill = True
        self.interactive_bar_lineWidth = 1.0

        # setup paths
        self.setup_paths()

    def on_check_parameters(self, data_type="all"):
        """
        Helper function to fix values that might be inappropriate for certain calculations

        Parameters
        ----------
        data_type : str
            determines which variables should be checked

            'all'        :    all variables are checked
            'process'    :    only variables involved in processing are checked
            'plotting'   :    only variables involved in plotting are checked
        """

        if data_type in ["all", "extract"]:
            # Extract
            if self.extract_mz_start == self.extract_mz_end:
                self.extract_mz_end = self.extract_mz_start + 1

            if self.extract_mz_end < self.extract_mz_start:
                self.extract_mz_start, self.extract_mz_end = self.extract_mz_end, self.extract_mz_start

            if self.extract_dt_start == self.extract_dt_end:
                self.extract_dt_end = self.extract_dt_start + 1

            if self.extract_dt_end < self.extract_dt_start:
                self.extract_dt_start, self.extract_dt_end = self.extract_dt_end, self.extract_dt_start

            if self.extract_rt_start == self.extract_rt_end:
                self.extract_rt_end = self.extract_rt_start + 1

            if self.extract_rt_end < self.extract_rt_start:
                self.extract_rt_start, self.extract_rt_end = self.extract_rt_end, self.extract_rt_start

            # Mass spectrum
            if self.ms_linearize_mz_end < self.ms_linearize_mz_start:
                self.ms_linearize_mz_start, self.ms_linearize_mz_end = (
                    self.ms_linearize_mz_end,
                    self.ms_linearize_mz_start,
                )

            if self.ms_linearize_mz_bin_size == 0:
                self.ms_linearize_mz_bin_size = 0.1

        if data_type in ["all", "origami"]:
            # ORIGAMI
            if self.origami_scans_per_voltage == 0:
                self.origami_scans_per_voltage = 1

            if self.origami_end_voltage < self.origami_start_voltage:
                self.origami_start_voltage, self.origami_end_voltage = (
                    self.origami_end_voltage,
                    self.origami_start_voltage,
                )

        if data_type in ["all", "process"]:
            # mass spectra
            if self.ms_smooth_sigma < 0:
                self.ms_smooth_sigma = 0

            if self.ms_smooth_window % 2 == 0:
                self.ms_smooth_window = self.ms_smooth_window + 1

            if self.ms_smooth_polynomial >= self.ms_smooth_window:
                if self.ms_smooth_polynomial % 2 == 0:
                    self.ms_smooth_window = self.ms_smooth_polynomial + 1
                else:
                    self.ms_smooth_window = self.ms_smooth_polynomial + 2

            # plot 2D
            if self.heatmap_smooth_sigma < 0:
                self.heatmap_smooth_sigma = 0

            if self.heatmap_smooth_window % 2 == 0:
                self.heatmap_smooth_window = self.heatmap_smooth_window + 1

            if self.heatmap_smooth_polynomial >= self.heatmap_smooth_window:
                if self.heatmap_smooth_polynomial % 2 == 0:
                    self.heatmap_smooth_window = self.heatmap_smooth_polynomial + 1
                else:
                    self.heatmap_smooth_window = self.heatmap_smooth_polynomial + 2

            if self.heatmap_threshold_lower is None or self.heatmap_threshold_lower < 0:
                self.heatmap_threshold_lower = 0

    def setup_paths(self, return_check: bool = False):
        """Setup paths"""

        def _check_path(dir_path, file_path=None):
            """Check whether directory exists and also a file"""
            if os.path.isdir(dir_path):
                if file_path and os.path.isfile(file_path):
                    return True
                return True
            return False

        # check driftscope main directory
        found_dir = True
        if not _check_path(self.APP_DRIFTSCOPE_PATH, os.path.join(self.APP_DRIFTSCOPE_PATH, "imextract.exe")):
            logger.warning("Could not resolve Driftscope path using the default `C:\DriftScope\lib` location")
            alternative_driftscope_path = os.path.join(self.APP_CWD, self.APP_DRIFTSCOPE_ALT_PATH)
            if not _check_path(alternative_driftscope_path, os.path.join(alternative_driftscope_path, "imextract.exe")):
                logger.warning(
                    "Could not resolve Driftscope path using the alternative `C:\DriftScope\lib` location."
                    " Data extraction will be restricted!"
                )
                found_dir = False
            else:
                self.APP_DRIFTSCOPE_PATH = alternative_driftscope_path

        if found_dir:
            print(f"Driftscope path {self.APP_DRIFTSCOPE_PATH}")

        if return_check:
            return found_dir

    def setup_logging(self, verbose: Union[int, str] = "DEBUG"):
        """Setup ORIGAMI logger"""
        from origami.utils.logging import set_logger
        from origami.utils.logging import set_logger_level

        log_directory = os.path.join(self.APP_CWD, "logs")
        if not os.path.exists(log_directory):
            print("Directory logs did not exist - created a new one in {}".format(log_directory))
            os.makedirs(log_directory)
        self.APP_LOG_DIR = log_directory

        # Generate filename
        if self.APP_LOG_PATH is None:
            file_path = "origami_{}.log".format(self.APP_START_TIME)
            self.APP_LOG_PATH = os.path.join(log_directory, file_path)

        # setup logger
        set_logger(file_path=self.APP_LOG_PATH)
        set_logger_level(verbose=verbose)

        logger.info("Logs can be found in {}".format(self.APP_LOG_PATH))
        print("Logs can be found in {}".format(self.APP_LOG_PATH))

    def setup_temporary_dir(self):
        """Setup temporary directory"""
        if self.APP_CWD is None:
            logger.warning("Could not setup temporary directory")
            return
        temp_data_folder = os.path.join(self.APP_CWD, "temporary_data")
        if not os.path.exists(temp_data_folder):
            os.makedirs(temp_data_folder)
        self.APP_TEMP_DATA_PATH = temp_data_folder

    def get_random_colormap(self, narrow=True):
        """Get random colormap

        Parameters
        ----------
        narrow : bool
            if True, only selected colormaps will be used

        Returns
        -------
        colormap : str
            name of random colormap
        """

        cmaps = self.colormap_choices
        if narrow:
            cmaps = self.colormap_narrow_choices
        return cmaps[get_random_int(0, len(cmaps) - 1)]

    def get_zoom_parameters(self):
        """Get matplotlib interaction parameters"""
        return {"normal": self.zoom_color_normal, "extract": self.zoom_color_extract}

    def get_mpl_parameters(self, plot_type, add_frame_width: bool = True, get_keys: bool = False):
        """Get plot parameters that can be consumed by plotting classes"""
        if get_keys:
            return [
                "compare",
                "axes",
                "scatter",
                "bar",
                "legend",
                "scatter",
                "annotation",
                "unidec",
                "colorbar",
                "normalization",
                "2d",
                "1d",
                "3d",
                "rmsd",
                "joint",
                "waterfall",
                "violin",
                "arrow",
                # "label",
            ]

        config = dict()
        if not isinstance(plot_type, list):
            plot_type = [plot_type]

        for _plot_type in plot_type:
            _plot_type = _plot_type.lower()
            if _plot_type == "compare":
                config.update(
                    {
                        "compare_color_top": self.compare_color_top,
                        "compare_color_bottom": self.compare_color_bottom,
                        "compare_style_top": self.compare_style_top,
                        "compare_style_bottom": self.compare_style_bottom,
                        "compare_alpha_top": self.compare_alpha_top,
                        "compare_alpha_bottom": self.compare_alpha_bottom,
                        "compare_inverse": self.compare_inverse,
                    }
                )
            if _plot_type == "axes":
                config.update(
                    {
                        "axes_frame_width": self.axes_frame_width,
                        "axes_frame_show": self.axes_frame_show,
                        "axes_tick_font_size": self.axes_tick_font_size,
                        "axes_tick_font_weight": self.axes_tick_font_weight,
                        "axes_label_font_size": self.axes_label_font_size,
                        "axes_label_font_weight": self.axes_label_font_weight,
                        "axes_title_font_size": self.axes_title_font_size,
                        "axes_title_font_weight": self.axes_title_font_weight,
                        "axes_label_pad": self.axes_label_pad,
                        "axes_frame_ticks_left": self.axes_frame_ticks_left,
                        "axes_frame_ticks_right": self.axes_frame_ticks_right,
                        "axes_frame_ticks_top": self.axes_frame_ticks_top,
                        "axes_frame_ticks_bottom": self.axes_frame_ticks_bottom,
                        "axes_frame_tick_labels_left": self.axes_frame_tick_labels_left,
                        "axes_frame_tick_labels_right": self.axes_frame_tick_labels_right,
                        "axes_frame_tick_labels_top": self.axes_frame_tick_labels_top,
                        "axes_frame_tick_labels_bottom": self.axes_frame_tick_labels_bottom,
                        "axes_frame_spine_left": self.axes_frame_spine_left,
                        "axes_frame_spine_right": self.axes_frame_spine_right,
                        "axes_frame_spine_top": self.axes_frame_spine_top,
                        "axes_frame_spine_bottom": self.axes_frame_spine_bottom,
                    }
                )
            if _plot_type == "scatter":
                config.update(
                    {
                        "marker_edge_color": self.marker_edge_color,
                        "marker_fill_color": self.marker_fill_color,
                        "marker_size": self.marker_size,
                        "marker_shape": self.marker_shape,
                        "marker_transparency": self.marker_transparency,
                    }
                )
            if _plot_type == "bar":
                config.update(
                    {
                        "bar_width": self.bar_width,
                        "bar_alpha": self.bar_alpha,
                        "bar_edge_color": self.bar_edge_color,
                        "bar_edge_same_as_fill": self.bar_edge_same_as_fill,
                        "bar_line_width": self.bar_line_width,
                    }
                )
            if _plot_type == "legend":
                config.update(
                    {
                        "legend": self.legend,
                        "legend_transparency": self.legend_transparency,
                        "legend_position": self.legend_position,
                        "legend_n_columns": self.legend_n_columns,
                        "legend_font_size": self.legend_font_size,
                        "legend_frame": self.legend_frame,
                        "legend_fancy_box": self.legend_fancy_box,
                        "legend_marker_first": self.legend_marker_first,
                        "legend_marker_size": self.legend_marker_size,
                        "legend_n_markers": self.legend_n_markers,
                        "legend_line_width": self.legend_line_width,
                        "legend_patch_transparency": self.legend_patch_transparency,
                    }
                )
            if _plot_type == "scatter":
                config.update({})
            if _plot_type == "1d":
                config.update(
                    {
                        "spectrum_line_width": self.spectrum_line_width,
                        "spectrum_line_color": self.spectrum_line_color,
                        "spectrum_line_style": self.spectrum_line_style,
                        "spectrum_line_fill_under": self.spectrum_line_fill_under,
                        "spectrum_fill_color": self.spectrum_fill_color,
                        "spectrum_fill_transparency": self.spectrum_fill_transparency,
                    }
                )
            if _plot_type == "annotation":
                config.update(
                    {
                        "annotation_label_horz": self.annotation_label_horz,
                        "annotation_label_vert": self.annotation_label_vert,
                        "annotation_label_font_size": self.annotation_label_font_size,
                        "annotation_label_font_weight": self.annotation_label_font_weight,
                    }
                )
            if _plot_type == "unidec":
                config.update(
                    {
                        "bar_width": self.unidec_plot_bar_width,
                        "bar_alpha": self.unidec_plot_bar_alpha,
                        "bar_edge_color": self.unidec_plot_bar_edge_color,
                        "bar_edge_same_as_fill": self.unidec_plot_bar_sameAsFill,
                        "bar_line_width": self.unidec_plot_bar_lineWidth,
                        "bar_marker_size": self.unidec_plot_bar_markerSize,
                        "fit_line_color": self.unidec_plot_fit_lineColor,
                        "isolated_marker_size": self.unidec_plot_isolatedMS_markerSize,
                        "MW_marker_size": self.unidec_plot_MW_markerSize,
                        "MW_show_markers": self.unidec_plot_MW_showMarkers,
                        "color_scheme": self.unidec_plot_color_scheme,
                        "heatmap_colormap": self.unidec_plot_colormap,
                        "palette": self.unidec_plot_palette,
                        "maximum_shown_items": self.unidec_maxShown_individualLines,
                        "contour_levels": self.unidec_plot_contour_levels,
                    }
                )
            if _plot_type == "colorbar":
                config.update(
                    {
                        "colorbar": self.colorbar,
                        "colorbar_width": self.colorbar_width,
                        "colorbar_pad": self.colorbar_pad,
                        "colorbar_min_points": self.colorbar_min_points,
                        "colorbar_position": self.colorbar_position,
                        "colorbar_label_fmt": self.colorbar_label_fmt,
                        "colorbar_label_size": self.colorbar_label_size,
                        "colorbar_edge_color": self.colorbar_edge_color,
                        "colorbar_edge_width": self.colorbar_edge_width,
                        "colorbar_label_color": self.colorbar_label_color,
                        "colorbar_inset_width": self.colorbar_inset_width,
                    }
                )

            if _plot_type == "normalization":
                config.update(
                    {
                        "heatmap_normalization_min": self.heatmap_normalization_min,
                        "heatmap_normalization_mid": self.heatmap_normalization_mid,
                        "heatmap_normalization_max": self.heatmap_normalization_max,
                        "heatmap_normalization": self.heatmap_normalization,
                        "heatmap_normalization_power_gamma": self.heatmap_normalization_power_gamma,
                    }
                )

            if _plot_type == "2d":
                config.update(
                    {
                        "heatmap_interpolation": self.heatmap_interpolation,
                        "heatmap_colormap": self.heatmap_colormap,
                        "heatmap_n_contour": self.heatmap_n_contour,
                        "heatmap_plot_type": self.heatmap_plot_type,
                    }
                )

            if _plot_type == "3d":
                config.update(
                    {
                        "axes_label_pad": self.axes_label_pad,
                        "axes_tick_font_size": self.axes_tick_font_size,
                        "axes_tick_font_weight": self.axes_tick_font_weight,
                        "axes_label_font_size": self.axes_label_font_size,
                        "axes_label_font_weight": self.axes_label_font_weight,
                        "axes_title_font_size": self.axes_title_font_size,
                        "axes_title_font_weight": self.axes_title_font_weight,
                    }
                )

            if _plot_type in ["rmsd", "rmsf"]:
                config.update(
                    {
                        "rmsd_label_position": self.rmsd_label_position,
                        "rmsd_label_font_size": self.rmsd_label_font_size,
                        "rmsd_label_font_weight": self.rmsd_label_font_weight,
                        "rmsf_h_space": self.rmsf_h_space,
                        "rmsf_line_color": self.rmsf_line_color,
                        "rmsf_line_transparency": self.rmsf_line_transparency,
                        "rmsf_line_style": self.rmsf_line_style,
                        "rmsf_line_width": self.rmsf_line_width,
                        "rmsf_fill_hatch": self.rmsf_fill_hatch,
                        "rmsf_fill_color": self.rmsf_fill_color,
                        "rmsf_fill_transparency": self.rmsf_fill_transparency,
                        "rmsd_rotation_x": self.rmsd_rotation_x,
                        "rmsd_rotation_y": self.rmsd_rotation_y,
                        "rmsd_matrix_add_labels": self.rmsd_matrix_add_labels,
                        "rmsd_matrix_font_size": self.rmsd_matrix_font_size,
                        "rmsd_matrix_font_weight": self.rmsd_matrix_font_weight,
                        "rmsd_matrix_font_color_fmt": self.rmsd_matrix_font_color_fmt,
                        "rmsd_matrix_font_color": self.rmsd_matrix_font_color,
                    }
                )
            if _plot_type in "joint":
                config.update({})
            if _plot_type in "waterfall":  # FIX ME
                config.update(
                    {
                        "waterfall_increment": self.waterfall_increment,
                        "waterfall_offset": self.waterfall_offset,
                        "waterfall_line_width": self.waterfall_line_width,
                        "waterfall_line_style": self.waterfall_line_style,
                        "waterfall_reverse": self.waterfall_reverse,
                        "waterfall_line_color": self.waterfall_line_color,
                        "waterfall_fill_under_color": self.waterfall_fill_under_color,
                        "waterfall_normalize": self.waterfall_normalize,
                        "waterfall_colormap": self.waterfall_colormap,
                        "waterfall_palette": self.waterfall_palette,
                        "waterfall_color_scheme": self.waterfall_color_scheme,
                        "waterfall_line_same_as_fill": self.waterfall_line_same_as_fill,
                        "waterfall_labels_show": self.waterfall_labels_show,
                        "waterfall_labels_frequency": self.waterfall_labels_frequency,
                        "waterfall_labels_x_offset": self.waterfall_labels_x_offset,
                        "waterfall_labels_y_offset": self.waterfall_labels_y_offset,
                        "waterfall_labels_font_size": self.waterfall_labels_font_size,
                        "waterfall_labels_font_weight": self.waterfall_labels_font_weight,
                        "waterfall_labels_format": self.waterfall_labels_format,
                        "waterfall_fill_under": self.waterfall_fill_under,
                        "waterfall_fill_under_nlimit": self.waterfall_fill_under_nlimit,
                        "waterfall_fill_under_transparency": self.waterfall_fill_under_transparency,
                    }
                )
            elif _plot_type in ["violin"]:  # FIX ME
                config.update(
                    {
                        "violin_min_percentage": self.violin_min_percentage,
                        "violin_spacing": self.violin_spacing,
                        "violin_orientation": self.violin_orientation,
                        "violin_line_width": self.violin_line_width,
                        "violin_line_style": self.violin_line_style,
                        "violin_line_color": self.violin_line_color,
                        "violin_fill_under_color": self.violin_fill_under_color,
                        "violin_normalize": self.violin_normalize,
                        "violin_smooth": self.violin_smooth,
                        "violin_smooth_sigma": self.violin_smooth_sigma,
                        "violin_colormap": self.violin_colormap,
                        "violin_palette": self.violin_palette,
                        "violin_color_scheme": self.violin_color_scheme,
                        "violin_line_same_as_fill": self.violin_line_same_as_fill,
                        "violin_labels_format": self.violin_labels_format,
                        "violin_fill_under": self.violin_fill_under,
                        "violin_n_limit": self.violin_n_limit,
                        "violin_fill_under_transparency": self.violin_fill_under_transparency,
                        "violin_labels_frequency": self.violin_labels_frequency,
                    }
                )
            if _plot_type in ["arrow"]:
                config.update(
                    {
                        "annotation_arrow_line_width": self.annotation_arrow_line_width,
                        "annotation_arrow_line_style": self.annotation_arrow_line_style,
                        "annotation_arrow_cap_length": self.annotation_arrow_cap_length,
                        "annotation_arrow_cap_width": self.annotation_arrow_cap_width,
                    }
                )
                add_frame_width = False
            # if _plot_type == "label":  # FIX ME
            #     config.update(
            #         {
            #             "horizontalalignment": self.annotation_label_horz,
            #             "verticalalignment": self.annotation_label_vert,
            #             "fontweight": self.annotation_label_font_weight,
            #             "fontsize": self.annotation_label_font_size,
            #             "rotation": self.annotation_label_font_orientation,
            #         }
            #     )
            #     add_frame_width = False

        if "axes_frame_width" not in config and add_frame_width:
            config["axes_frame_width"] = self.axes_frame_width

        return config

    def get_panel_parameters(self, config_key: Union[List[str], str], get_keys: bool = False):
        """Get parameters that correspond to panels and UI elements

        Parameters
        ----------
        config_key : List[str], str
            configuration key or list of configuration keys that should be retrieved from the config file
        get_keys : bool
            if `True`, return the list of keys of config keys that can be retrieved

        Returns
        -------
        config_keys : List[str]
            if `get_keys` is True
        config : Dict
            dictionary with keys
        """

        if get_keys:
            return [
                "zoom",
                "panel_origami_ms",
                "panel_smart_zoom",
                "panel_annotate",
                "panel_compare_ms",
                "panel_new_version",
                "panel_duplicate_check",
                "panel_pick_ms",
                "panel_extract_msdt",
                "panel_document_tree",
                "panel_process_heatmap",
                "panel_process_ms",
            ]

        config = dict()
        if not isinstance(config_key, list):
            config_key = [config_key]

        for _config_key in config_key:
            if _config_key == "zoom":
                config.update(
                    {"zoom_color_normal": self.zoom_color_normal, "zoom_color_extract": self.zoom_color_extract}
                )
            if _config_key == "panel_smart_zoom":
                config.update(
                    {
                        "smart_zoom_enable": self.smart_zoom_enable,
                        "smart_zoom_soft_max": self.smart_zoom_soft_max,
                        "smart_zoom_hard_max": self.smart_zoom_hard_max,
                        "smart_zoom_downsampling_method": self.smart_zoom_downsampling_method,
                        "smart_zoom_subsample_default": self.smart_zoom_subsample_default,
                        "smart_zoom_view_mode": self.smart_zoom_view_mode,
                        "smart_zoom_min_search": self.smart_zoom_min_search,
                        "smart_zoom_max_search": self.smart_zoom_max_search,
                    }
                )
            if _config_key == "panel_origami_ms":
                config.update(
                    {
                        "origami_method": self.origami_method,
                        "origami_scans_per_voltage": self.origami_scans_per_voltage,
                        "origami_start_voltage": self.origami_start_voltage,
                        "origami_start_scan": self.origami_start_scan,
                        "origami_end_voltage": self.origami_end_voltage,
                        "origami_step_voltage": self.origami_step_voltage,
                        "origami_boltzmann_offset": self.origami_boltzmann_offset,
                        "origami_exponential_percentage": self.origami_exponential_percentage,
                        "origami_preprocess": self.origami_preprocess,
                    }
                )
            if _config_key == "panel_annotate":
                config.update(
                    {
                        "annotate_panel_highlight": self.annotate_panel_highlight,
                        "annotate_panel_zoom_in": self.annotate_panel_zoom_in,
                        "annotate_panel_zoom_in_window": self.annotate_panel_zoom_in_window,
                        "annotate_panel_add_to_table": self.annotate_panel_add_to_table,
                        "annotate_panel_patch_color": self.annotate_panel_patch_color,
                        "annotate_panel_patch_alpha": self.annotate_panel_patch_alpha,
                        "annotate_panel_label_color": self.annotate_panel_label_color,
                    }
                )
            if _config_key == "panel_compare_ms":
                config.update(
                    {
                        "compare_panel_preprocess": self.compare_panel_preprocess,
                        "compare_panel_normalize": self.compare_panel_normalize,
                        "compare_panel_subtract": self.compare_panel_subtract,
                    }
                )
            if _config_key == "panel_new_version":
                config.update(
                    {
                        "new_version_panel_link": self.new_version_panel_link,
                        "new_version_panel_do_not_ask": self.new_version_panel_do_not_ask,
                    }
                )
            if _config_key == "panel_duplicate_check":
                config.update(
                    {
                        "import_duplicate_panel_action": self.import_duplicate_panel_action,
                        "import_duplicate_panel_ask": self.import_duplicate_panel_ask,
                    }
                )
            if _config_key == "panel_pick_ms":
                config.update(
                    {
                        "peak_panel_method_choice": self.peak_panel_method_choice,
                        "peak_panel_specify_mz": self.peak_panel_specify_mz,
                        "peak_panel_mz_start": self.peak_panel_mz_start,
                        "peak_panel_mz_end": self.peak_panel_mz_end,
                        "peak_panel_preprocess": self.peak_panel_preprocess,
                        "peak_panel_verbose": self.peak_panel_verbose,
                        "peak_panel_method": self.peak_panel_method,
                        "peak_panel_scatter": self.peak_panel_scatter,
                        "peak_panel_highlight": self.peak_panel_highlight,
                        "peak_panel_labels": self.peak_panel_labels,
                        "peak_panel_labels_mz": self.peak_panel_labels_mz,
                        "peak_panel_labels_int": self.peak_panel_labels_int,
                        "peak_panel_labels_width": self.peak_panel_labels_width,
                        "peak_panel_optimise_position": self.peak_panel_optimise_position,
                        "peak_panel_labels_max_count": self.peak_panel_labels_max_count,
                        "peak_panel_filter_choice": self.peak_panel_filter_choice,
                        "peak_panel_score_choice": self.peak_panel_score_choice,
                    }
                )
            if _config_key == "panel_extract_msdt":
                config.update(
                    {
                        "msdt_panel_extract_mz_start": self.msdt_panel_extract_mz_start,
                        "msdt_panel_extract_mz_end": self.msdt_panel_extract_mz_end,
                        "msdt_panel_extract_mz_bin_size": self.msdt_panel_extract_mz_bin_size,
                    }
                )
            if _config_key == "panel_document_tree":
                config.update(
                    {
                        "tree_panel_delete_item_ask": self.tree_panel_delete_item_ask,
                        "tree_panel_delete_group_ask": self.tree_panel_delete_group_ask,
                        "tree_panel_delete_document_ask": self.tree_panel_delete_document_ask,
                        "tree_panel_item_highlight": self.tree_panel_item_highlight,
                        "tree_panel_item_auto_plot": self.tree_panel_item_auto_plot,
                    }
                )
            if _config_key == "panel_process_heatmap":
                config.update(
                    {
                        "heatmap_crop": self.heatmap_crop,
                        "heatmap_crop_xmin": self.heatmap_crop_xmin,
                        "heatmap_crop_xmax": self.heatmap_crop_xmax,
                        "heatmap_crop_ymin": self.heatmap_crop_ymin,
                        "heatmap_crop_ymax": self.heatmap_crop_ymax,
                        "heatmap_interpolate": self.heatmap_interpolate,
                        "heatmap_interpolate_mode": self.heatmap_interpolate_mode,
                        "heatmap_interpolate_xaxis": self.heatmap_interpolate_xaxis,
                        "heatmap_interpolate_yaxis": self.heatmap_interpolate_yaxis,
                        "heatmap_interpolate_fold": self.heatmap_interpolate_fold,
                        "heatmap_smooth": self.heatmap_smooth,
                        "heatmap_smooth_mode": self.heatmap_smooth_mode,
                        "heatmap_smooth_sigma": self.heatmap_smooth_sigma,
                        "heatmap_smooth_window": self.heatmap_smooth_window,
                        "heatmap_smooth_polynomial": self.heatmap_smooth_polynomial,
                        "heatmap_threshold": self.heatmap_threshold,
                        "heatmap_threshold_lower": self.heatmap_threshold_lower,
                        "heatmap_normalize": self.heatmap_normalize,
                        "heatmap_normalize_mode": self.heatmap_normalize_mode,
                    }
                )
            if _config_key == "panel_process_ms":
                config.update(
                    {
                        "ms_crop": self.ms_crop,
                        "ms_crop_min": self.ms_crop_min,
                        "ms_crop_max": self.ms_crop_max,
                        "ms_linearize": self.ms_linearize,
                        "ms_linearize_mz_start": self.ms_linearize_mz_start,
                        "ms_linearize_mz_end": self.ms_linearize_mz_end,
                        "ms_linearize_mz_auto_range": self.ms_linearize_mz_auto_range,
                        "ms_linearize_mz_bin_size": self.ms_linearize_mz_bin_size,
                        "ms_linearize_method": self.ms_linearize_method,
                        "ms_smooth": self.ms_smooth,
                        "ms_smooth_mode": self.ms_smooth_mode,
                        "ms_smooth_sigma": self.ms_smooth_sigma,
                        "ms_smooth_window": self.ms_smooth_window,
                        "ms_smooth_polynomial": self.ms_smooth_polynomial,
                        "ms_smooth_moving_window": self.ms_smooth_moving_window,
                        "ms_threshold": self.ms_threshold,
                        "ms_baseline_method": self.ms_baseline_method,
                        "ms_baseline_linear_threshold": self.ms_baseline_linear_threshold,
                        "ms_baseline_polynomial_order": self.ms_baseline_polynomial_order,
                        "ms_baseline_curved_window": self.ms_baseline_curved_window,
                        "ms_baseline_median_window": self.ms_baseline_median_window,
                        "ms_baseline_tophat_window": self.ms_baseline_tophat_window,
                        "ms_normalize": self.ms_normalize,
                    }
                )

        return config

    def save_config(self, path: str):
        """Export configuration file to JSON file"""
        config = {}

        # get matplotlib config data
        mpl_keys = self.get_mpl_parameters("", get_keys=True)
        config["mpl-settings"] = dict()
        for key in mpl_keys:
            config["mpl-settings"][key] = self.get_mpl_parameters([key])

        # get panel config data
        panel_keys = self.get_panel_parameters("", get_keys=True)
        config["ui-settings"] = dict()
        for key in panel_keys:
            config["ui-settings"][key] = self.get_panel_parameters([key])

        # add recent files
        config["recent-files"] = self.recent_files

        # write to json file
        write_json_data(path, config)
        logger.debug(f"Saved config file to `{path}`")

    def load_config(self, path: str, check_type: bool = True):
        """Load configuration from JSON file"""
        config = read_json_data(path)

        if not isinstance(config, dict):
            logger.error("Configuration file should be a dictionary with key:value pairs")
            return

        # iterate over the major groups of settings
        for config_group_title in ["mpl-settings", "ui-settings"]:
            _config_group = config.get(config_group_title, dict())
            for _, group_config in _config_group.items():
                for key, value in group_config.items():
                    if hasattr(self, key):
                        if check_type:
                            current_value = getattr(self, key)
                            if not self._check_type(current_value, value):
                                logger.warning(
                                    f"Could not set `{key}` as the types were not similar enough to ensure compliance."
                                    f"\nCurrent value={current_value}; New value={value}"
                                )
                                continue
                        setattr(self, key, value)
            logger.debug(f"Loaded `{config_group_title}` settings")

        # load recent files
        _recent_files = config.get("recent-files", [])
        if isinstance(_recent_files, list):
            self.recent_files = _recent_files
        logger.debug(f"Loaded config file from `{path}`")

        pub.sendMessage("config.loaded")

    @staticmethod
    def _check_type(current_value, value):
        """Check whether type of the value matches that of the currently set value"""
        current_type = type(current_value)
        new_type = type(value)

        # simplest case where types match perfectly
        if current_type == new_type:
            return True
        if current_type in [int, float] and new_type in [int, float]:
            return True
        if current_type in [list, tuple] and new_type in [list, tuple]:
            return True
        return False


CONFIG = Config()
