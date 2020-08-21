"""Imaging mass spectrometry normalization"""
# Standard library imports
import logging

# Third-party imports
import numpy as np
import regex
from natsort import natsorted

# Local imports
from origami.objects.document import DocumentStore
from origami.objects.containers import MassSpectrumObject

LOGGER = logging.getLogger(__name__)


class ImagingNormalizationProcessor:
    """Normalization processor"""

    def __init__(self, document: DocumentStore):
        self.document = document

        self.n_px, self.x_dim, self.y_dim = self.generate_metadata()
        self.compute_normalizations()

    @staticmethod
    def _reduce_total(mz_obj: MassSpectrumObject):
        """Compute TIC normalization"""
        return np.sum(mz_obj.y)

    @staticmethod
    def _reduce_rms(mz_obj: MassSpectrumObject):
        """Compute TIC normalization"""
        return np.sqrt(np.mean(np.square(mz_obj.y)))

    @staticmethod
    def _reduce_median(mz_obj: MassSpectrumObject):
        """Compute TIC normalization"""
        return np.median(mz_obj.y[mz_obj.y > 0])

    @staticmethod
    def _reduce_l2(mz_obj: MassSpectrumObject):
        """Compute TIC normalization"""
        return np.sqrt(np.sum(np.square(mz_obj.y)))

    def generate_metadata(self):
        """Get metadata from the document"""
        meta = self.document.get_config("imaging")

        # compute parameters
        x_dim = int(meta["x_dim"])
        y_dim = int(meta["y_dim"])
        n_px = x_dim * y_dim
        LOGGER.debug(f"Document has {n_px} pixels")
        return n_px, x_dim, y_dim

    def get_spectrum(self):
        """Yields mass spectrum"""

        spectra = self.document["MassSpectra"]
        names = natsorted(list(spectra.keys()))
        for name in names:
            obj = spectra[name]
            if not regex.findall(r"\d+=", name) or "file_info" not in obj.attrs:
                LOGGER.debug(f"Skipped {name} - it is missing index information")
                continue
            # variable = obj.attrs["file_info"]["variable"]
            yield MassSpectrumObject(obj.x[:], obj.y[:])

    def compute_normalizations(self):
        """Computes each normalization for the dataset"""
        norm_reduce = [
            (0, "total", self._reduce_total),
            (1, "sqrt", self._reduce_rms),
            (2, "median", self._reduce_median),
            (3, "l2", self._reduce_l2),
        ]

        # pre-allocate arrays
        norm_intensity = np.zeros((self.n_px, len(norm_reduce)), dtype=np.float32)
        for i, mz_obj in enumerate(self.get_spectrum()):
            for j, _, reduce in norm_reduce:
                norm_intensity[i, j] = reduce(mz_obj)

        # write to disk
        norm_median = self.rescale(norm_intensity, np.median)  # noqa
        norm_mean = self.rescale(norm_intensity, np.mean)
        for j, name, _ in norm_reduce:
            self.add_normalization(name, norm_intensity[:, j])
            self.add_normalization(name + " (scale=median)", norm_median[:, j])
            self.add_normalization(name + " (scale=mean)", norm_mean[:, j])

    @staticmethod
    def rescale(array: np.ndarray, scale_fcn=np.median):
        """Rescale normalization array"""
        norm_rescaled = np.zeros_like(array)
        for i, norm in enumerate(array.T):
            scale = float(scale_fcn(norm))
            norm_scale = np.zeros_like(norm)
            norm_scale.fill(scale)
            norm_scale = norm / norm_scale
            norm_rescaled[:, i] = norm_scale
        return norm_rescaled

    def add_normalization(self, name, normalization):
        """Appends normalization to the metadata store"""
        self.document.add_metadata(
            f"Normalization={name}",
            data=dict(array=normalization),
            attrs=dict(normalization=name, n_px=self.n_px, x_dim=self.x_dim, y_dim=self.y_dim),
        )
        LOGGER.debug(f"Added normalization={name}")
