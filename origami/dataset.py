class Document:
    """New document object"""

    VERSION = "1.0"

    def __init__(self):
        # attributes
        self.title = "Document"
        self.path = ""
        self.data_type = ""
        self.format = ""

        # temporary metadata
        self.app_data = dict()
        self.file_reader = dict()
        self.callbacks = dict()

        # metadata
        self.parameters = dict()
        self.user_parameters = dict()
        self.file_parameters = dict()
        self.metadata = dict()

        # mass spectra
        self.mass_spectrum_raw = dict()
        self.mass_spectrum_process = dict()
        self.mass_spectra = dict()
        self.tandem_spectra = dict()

        # chromatograms
        self.chromatogram_raw = dict()
        self.chromatogram_process = dict()
        self.chromatograms = dict()

        # mobilograms
        self.mobilogram_raw = dict()
        self.mobilogram_process = dict()
        self.mobilograms = dict()

        # average heatmap
        self.heatmap_raw = dict()
        self.heatmap_process = dict()

        # ion heatmaps
        self.ion_heatmaps = dict()

        # other heatmaps
        self.other_heatmaps = dict()

        # overlay
        self.overlay = dict()

        # calibration
        self.calibration = dict()

        # other
        self.other = dict()

    def get_spectrum(self, title, processed=False):
        """Retrieve spectrum object"""
        if title is None:
            if not processed:
                return self.mass_spectrum_raw
            return self.mass_spectrum_process
        else:
            return self.mass_spectra.get(title, None)
