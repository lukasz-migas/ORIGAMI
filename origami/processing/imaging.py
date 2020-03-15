"""Imaging mass spectrometry normalization"""
# Third-party imports
import numpy as np


class ImagingNormalizationProcessor:
    def __init__(self, document):
        self.document = document

        self.n_px = self.generate_metadata()
        self.compute_normalizations()

    def generate_metadata(self):
        meta = self.document.metadata["imaging_lesa"]

        # compute parameters
        n_px = int(meta["x_dim"] * meta["y_dim"])
        return n_px

    def compute_normalizations(self):
        self.add_normalization(*self.add_total_normalization())
        self.add_normalization(*self.add_rms_normalization())
        self.add_normalization(*self.add_median_normalization())
        self.add_normalization(*self.add_l2_normalization())

    def add_total_normalization(self):
        # total intensity normalization
        norm_intensity = np.zeros((self.n_px,), dtype=np.float32)
        for i, dset in enumerate(self.document.multipleMassSpectrum.values()):
            norm_intensity[i] = np.sum(dset["yvals"])
        return norm_intensity, "total"

    def add_rms_normalization(self):
        # root-mean square normalization
        norm_intensity = np.zeros((self.n_px,), dtype=np.float32)
        for i, dset in enumerate(self.document.multipleMassSpectrum.values()):
            norm_intensity[i] = np.sqrt(np.mean(np.square(dset["yvals"])))
        return norm_intensity, "sqrt"

    def add_median_normalization(self):
        # median normalization
        norm_intensity = np.zeros((self.n_px,), dtype=np.float32)
        for i, dset in enumerate(self.document.multipleMassSpectrum.values()):
            norm_intensity[i] = np.median(dset["yvals"][dset["yvals"] > 0])
        return norm_intensity, "median"

    def add_l2_normalization(self):
        # l2 normalization
        norm_intensity = np.zeros((self.n_px,), dtype=np.float32)
        for i, dset in enumerate(self.document.multipleMassSpectrum.values()):
            norm_intensity[i] = np.sqrt(np.sum(np.square(dset["yvals"])))
        return norm_intensity, "l2"

    def add_normalization(self, normalization, name):

        # make sure there is somewhere to add normalization to
        if "norm" not in self.document.metadata["imaging_lesa"]:
            self.document.metadata["imaging_lesa"]["norm"] = dict()

        # actually add data
        self.document.metadata["imaging_lesa"]["norm"][name] = normalization
