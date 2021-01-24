"""Handler class for UniDec mass deconvolution"""
# Standard library imports
import time
import logging

# Local imports
from origami.utils.secret import get_short_hash
from origami.config.config import CONFIG
from origami.utils.utilities import report_time
from origami.handlers.process import PROCESS_HANDLER
from origami.objects.containers import MassSpectrumObject
from origami.widgets.unidec.processing.engine import UniDecEngine
from origami.widgets.unidec.processing.containers import UniDecResultsObject

LOGGER = logging.getLogger(__name__)


class UniDecHandler:
    """UniDec handler"""

    @staticmethod
    def unidec_init_engine(document_title: str = None, dataset_name: str = None):
        """Initialize UniDec engine"""
        if CONFIG.unidec_engine is None:
            CONFIG.unidec_engine = UniDecEngine(document_title=document_title, dataset_name=dataset_name)

    def unidec_initialize(self, mz_obj: MassSpectrumObject) -> UniDecResultsObject:
        """Initialize UniDec engine"""
        LOGGER.debug("UniDec: Started loading data...")

        self.unidec_init_engine(mz_obj.document_title, mz_obj.dataset_name)

        # get unique filename
        document_title = mz_obj.document_title
        filename = mz_obj.dataset_name
        if filename in ["", None] or document_title in ["", None]:
            filename = get_short_hash()
            document_title = get_short_hash()
        filename = "_".join([document_title, filename])

        CONFIG.unidec_engine.set_mass_spectrum(mz_obj, filename=filename, output_dir=CONFIG.APP_TEMP_DATA_PATH)
        LOGGER.debug("UniDec: Finished loading data...")

        return CONFIG.unidec_engine.data

    @staticmethod
    def unidec_preprocess() -> UniDecResultsObject:
        """Pre-process mass spectrum"""
        t_start = time.time()
        LOGGER.debug("UniDec: Started pre-processing...")
        CONFIG.unidec_engine.config.set_from_origami_config()

        # create copy of the mass spectrum object so the data is not overwritten in the Document
        mz_obj = CONFIG.unidec_engine.data.mz_obj.duplicate()
        mz_obj = PROCESS_HANDLER.on_process_ms(mz_obj)
        CONFIG.unidec_engine.process_mass_spectrum(mz_obj)
        LOGGER.debug(f"UniDec: Finished pre-processing in {report_time(t_start)}")

        return CONFIG.unidec_engine.data

    def unidec_initialize_and_preprocess(self, mz_obj: MassSpectrumObject) -> UniDecResultsObject:
        """Initialize UniDec engine and pre-process data"""
        self.unidec_initialize(mz_obj)
        self.unidec_preprocess()
        return CONFIG.unidec_engine.data

    @staticmethod
    def unidec_run() -> UniDecResultsObject:
        """Pre-process mass spectrum"""
        t_start = time.time()
        LOGGER.debug("UniDec: Started deconvolution...")
        # this is required so the ORIGAMI-defined parameters are used in the deconvolution
        CONFIG.unidec_engine.config.set_from_origami_config()

        # run unidec
        CONFIG.unidec_engine.run_unidec()
        LOGGER.debug(f"UniDec: Finished deconvolution in {report_time(t_start)}")

        return CONFIG.unidec_engine.data

    @staticmethod
    def unidec_find_peaks() -> UniDecResultsObject:
        """Pre-process mass spectrum"""
        t_start = time.time()
        LOGGER.debug("UniDec: Started peak picking...")
        # this is required so the ORIGAMI-defined parameters are used in the deconvolution
        CONFIG.unidec_engine.config.set_from_origami_config()
        CONFIG.unidec_engine.pick_peaks()
        LOGGER.debug(f"UniDec: Finished peak picking in {report_time(t_start)}")

        # convolve peaks
        LOGGER.info("UniDec: Started convolving peaks...")
        try:
            CONFIG.unidec_engine.convolve_peaks()
        except OverflowError as err:
            print(err)
            raise ValueError(
                "Too many peaks! Try again with larger 'Peak detection threshold' or 'Peak detection window (Da).'"
            )
        LOGGER.debug(f"UniDec: Finished convolving in {report_time(t_start)}")

        return CONFIG.unidec_engine.data

    @staticmethod
    def unidec_isolate():
        """Isolate single molecular weight"""
        t_start = time.time()
        LOGGER.info("UniDec: Started isolating MW...")
        CONFIG.unidec_engine.config.set_from_origami_config()

        try:
            CONFIG.unidec_engine.pick_peaks()
        except (ValueError, ZeroDivisionError):
            raise ValueError(
                "Failed to find peaks. Try increasing the value of 'Peak detection window (Da)'"
                " to be same or larger than 'Sample frequency (Da)'."
            )

        except IndexError as err:
            print(err)
            raise ValueError("Please run UniDec first")

        LOGGER.debug(f"UniDec: Finished isolating MW in {report_time(t_start)}")

    def unidec_autorun(self, mz_obj: MassSpectrumObject) -> UniDecResultsObject:
        """Autorun UniDec"""
        t_start = time.time()
        LOGGER.info("UniDec: Started Autorun...")
        self.unidec_initialize_and_preprocess(mz_obj)
        self.unidec_run()
        self.unidec_find_peaks()
        LOGGER.debug(f"UniDec: Finished autorun in {report_time(t_start)}")
        return CONFIG.unidec_engine.data


UNIDEC_HANDLER = UniDecHandler()
