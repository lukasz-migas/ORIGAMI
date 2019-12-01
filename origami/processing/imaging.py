"""Imaging mass spectrometry normalization"""
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


# class ImagingNormalizationProcessor:
#
#     def __init__(self, document):
#         self.document = document
#
#         self.intensities = self.generate_intensity_array()
#         self.compute_normalizations()
#
#     def generate_intensity_array(self):
#         meta = self.document.metadata["imaging_lesa"]
#         dset = self.document.multipleMassSpectrum[list(self.document.multipleMassSpectrum.keys())[0]]
#
#         # compute parameters
#         n_px = int(meta["x_dim"] * meta["y_dim"])
#         mz_bins = len(dset["xvals"])
#
#         # pre-allocate
#         intensities = np.zeros((n_px, mz_bins), dtype=np.float32)
#
#         # collect data
#         for i, dset in enumerate(self.document.multipleMassSpectrum.values()):
#             intensities[i] = dset["yvals"]
#
#         return intensities
#
#     def compute_normalizations(self):
#         self.add_normalization(*self.add_total_normalization())
#         self.add_normalization(*self.add_rms_normalization())
#         self.add_normalization(*self.add_median_normalization())
#         self.add_normalization(*self.add_l2_normalization())
#
#     def add_total_normalization(self):
#         # total intensity normalization
#         divisor = np.sum(self.intensities)
#         norm_intensity = np.divide(self.intensities, divisor)
#         return norm_intensity, "total"
#
#     def add_rms_normalization(self):
#         # root-mean square normalization
#         divisor = np.sqrt(np.mean(np.square(self.intensities)))
#         norm_intensity = np.divide(self.intensities, divisor)
#         return norm_intensity, "sqrt"
#
#     def add_median_normalization(self):
#         # median normalization
#         divisor = np.median(self.intensities[self.intensities > 0])
#         norm_intensity = np.divide(self.intensities, divisor)
#         return norm_intensity, "median"
#
#     def add_l2_normalization(self):
#         # l2 normalization
#         divisor = np.sqrt(np.sum(np.square(self.intensities)))
#         norm_intensity = np.divide(self.intensities, divisor)
#         return norm_intensity, "l2"
#
#     def add_normalization(self, normalization, name):
#         # collect data
#         for i, dset in enumerate(self.document.multipleMassSpectrum.values()):
#
#             # make sure there is somewhere to add normalization to
#             if "norm" not in dset:
#                 dset["norm"] = dict()
#
#             # actually add data
#             dset["norm"][name] = normalization[i]
