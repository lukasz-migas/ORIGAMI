# Standard library imports
import time
import logging

# Third-party imports
import numpy as np

# Local imports
import origami.processing.heatmap as pr_heatmap
import origami.processing.peptide_annotation as pr_frag
# from misc.code.UniDec import unidec
from origami.config.environment import ENV

logger = logging.getLogger(__name__)


class DataProcessing:
    """Data processing"""

    def __init__(self, presenter, view, config, **kwargs):
        self.presenter = presenter
        self.view = view
        self.config = config

        self.frag_generator = pr_frag.PeptideAnnotation()

        # unidec parameters
        # self.unidec_dataset = None
        # self.unidec_document = None

    @property
    def data_handling(self):
        """Return handle to `data_processing`"""
        return self.presenter.data_handling

    @property
    def document_tree(self):
        """Return handle to `document_tree`"""
        return self.view.panelDocuments.documents

    @property
    def panel_plot(self):
        """Return handle to `data_processing`"""
        return self.view.panelPlots

    def on_get_document(self):
        self.presenter.currentDoc = self.document_tree.on_enable_document()
        if self.presenter.currentDoc is None or self.presenter.currentDoc == "Documents":
            return None
        document = ENV[self.presenter.currentDoc]

        return document

    def get_mz_spacing(self, x):
        """Return average spacing in the spectrum

        Parameters
        ----------
        x : np.array

        Returns
        -------
        np.float
            average spacing in the array
        """
        return np.abs(np.diff(x)).mean()

    def downsample_array(self, xvals, zvals):
        """Downsample MS/DT array

        Parameters
        ----------
        xvals: np.array
            x-axis array (eg m/z)
        zvals: np.array
            2D array (e.g. m/z vs DT)
        """
        __, x_dim = zvals.shape
        # determine whether soft/hard maximum was breached
        if x_dim > self.config.smart_zoom_soft_max or x_dim > self.config.smart_zoom_hard_max:
            original_shape = zvals.shape
            # calculate division factor(s)
            division_factors, division_factor = pr_heatmap.calculate_division_factors(
                x_dim,
                min_division=self.config.smart_zoom_min_search,
                max_division=self.config.smart_zoom_max_search,
                subsampling_default=self.config.smart_zoom_subsample_default,
            )
            # subsample array
            if not division_factors or self.config.smart_zoom_downsampling_method == "Sub-sampled":
                zvals, xvals = pr_heatmap.subsample_array(zvals, xvals, division_factor)
            else:
                if self.config.smart_zoom_downsampling_method in ["Auto", "Binned (summed)"]:
                    zvals, xvals = pr_heatmap.bin_sum_array(zvals, xvals, division_factor)
                else:
                    zvals, xvals = pr_heatmap.bin_mean_array(zvals, xvals, division_factor)

            logger.info("Downsampled from {} to {}".format(original_shape, zvals.shape))

            # check whether hard maximum was breached
            if zvals.shape[1] > self.config.smart_zoom_hard_max:
                logger.warning("Sub-sampled data is larger than the hard-maximum. Sub-sampling again")
                while zvals.shape[1] > self.config.smart_zoom_hard_max:
                    xvals, zvals = self.downsample_array(xvals, zvals)

        return xvals, zvals

    def on_get_peptide_fragments(self, spectrum_dict, label_format={}, get_lists=False, **kwargs):
        tstart = time.time()
        id_num = kwargs.get("id_num", 0)
        if len(label_format) == 0:
            label_format = {"fragment_name": True, "peptide_seq": False, "charge": True, "delta_mz": False}

        self.frag_generator.set_label_format(label_format)
        # self.frag_generator = pr_frag.PeptideAnnotation(**{"label_format":label_format}) # refresh, temprorary!

        # get parameters
        peptide = None
        if "identification" in spectrum_dict:
            peptide = spectrum_dict["identification"][id_num].get("peptide_seq", None)

        if peptide is None:
            return {}, {}, {}, {}, {}
        z = spectrum_dict["identification"][id_num]["charge"]

        modifications = {}
        try:
            modifications = spectrum_dict["identification"][id_num]["modification_info"]
        except (KeyError, IndexError):
            logger.warning("There were no `modifications` in the dataset")

        # generate fragments
        fragments = self.frag_generator.generate_fragments_from_peptide(
            peptide=peptide,
            ion_types=kwargs.get("ion_types", ["b-all", "y-all"]),
            label_format=label_format,
            max_charge=z,
            modification_dict=modifications,
        )

        # generate fragment lists
        (
            fragment_mass_list,
            fragment_name_list,
            fragment_charge_list,
            fragment_peptide_list,
            frag_full_name_list,
        ) = self.frag_generator.get_fragment_mass_list(fragments)
        xvals, yvals = spectrum_dict["xvals"], spectrum_dict["yvals"]

        # match fragments to peaks in the spectrum
        found_peaks = self.frag_generator.match_peaks(
            xvals,
            yvals,
            fragment_mass_list,
            fragment_name_list,
            fragment_charge_list,
            fragment_peptide_list,
            frag_full_name_list,
            tolerance=kwargs.get("tolerance", 0.25),
            tolerance_units=kwargs.get("tolerance_units", "Da"),
            max_found=kwargs.get("max_annotations", 1),
        )

        # print info
        if kwargs.get("verbose", False):
            msg = "Matched {} peaks in the spectrum for peptide {}. It took {:.4f}.".format(
                len(found_peaks), peptide, time.time() - tstart
            )
            print(msg)

        # return data
        if get_lists:
            # fmt: off
            frag_mass_list, frag_int_list, frag_label_list, frag_full_label_list = \
                self.frag_generator.get_fragment_lists(
                    found_peaks, get_calculated_mz=kwargs.get("get_calculated_mz", False)
                )
            # fmt: on

            return found_peaks, frag_mass_list, frag_int_list, frag_label_list, frag_full_label_list

        # return peaks only
        return found_peaks
