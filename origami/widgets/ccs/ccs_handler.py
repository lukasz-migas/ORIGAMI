"""CCS handler"""
# Standard library imports
# import pandas as pd
import logging

# Third-party imports
import pandas as pd

# Local imports
from origami.utils.path import get_delimiter_from_filename

LOGGER = logging.getLogger(__name__)


class CCSHandler:
    """CCS handler class

    Workflow:
    - select Waters file DONE
        -> load mass spectrum
    - specify which gas is used DONE
    - user specifies m/z window DONE
        -> extract mobilogram
    - user specifies dt range OR auto-specify DONE
        -> find the appropriate mobility value in miliseconds
    -> user specifies calibrant information DONE
        -> mw, charge, ccs
        -> m/z, dt are automatically populated
    -repeat until happy DONE
    - calculate ccs
    - export all necessary data to json file
        -> name of the file
        -> path to the file
        -> gas
        -> m/z, mw, charge, dt, ccs
        -> calibration parameters
    """

    @staticmethod
    def write_calibration_db(path: str, calibration_db):
        """Write calibration database file"""

        if not isinstance(calibration_db, list) or not calibration_db:
            raise ValueError("Calibration database should be provided as a nested list")

        if len(calibration_db[0]) != 10:
            raise ValueError("Each row in the calibration database should have 10 items")

        columns = ["calibrant", "mw", "charge", "mz", "he_pos", "he_neg", "n2_pos", "n2_neg", "state", "source"]
        df = pd.DataFrame(calibration_db, columns=columns)

        delimiter = get_delimiter_from_filename(path)
        df.to_csv(path, sep=delimiter)

    @staticmethod
    def read_calibration_db(path: str):
        """Read calibration database file

        Parameters
        ----------
        path : str
            path to the file with calibration data

        Returns
        -------
        matches : dict
            dictionary with all necessary fields
        """

        def _check_field(field_name):
            """Check field"""
            if field_name not in matches:
                return False
            if matches[field_name] is None:
                return False
            return True

        columns_dict = {
            "calibrant": ["protein", "molecule", "calibrant"],
            "mw": ["mw", "mol_weight", "molecular_weight"],
            "mz": ["mz", "m/z", "m/z (da)", "m/z(da)"],
            "charge": ["charge", "z"],
            "he_pos": ["hepos", "he_pos", "ccs_he_pos", "ccshe_pos"],
            "he_neg": ["heneg", "he_neg", "ccs_he_neg", "ccshe_neg"],
            "n2_pos": ["n2pos", "n2_pos", "ccs_n2_pos", "ccsn2_pos"],
            "n2_neg": ["n2neg", "n2_neg", "ccs_n2_neg", "ccsn2_neg"],
            "state": ["state", "type"],
            "source": ["source", "ref"],
        }
        df = pd.read_csv(path)
        df.fillna("", inplace=True)
        column_names = df.columns

        matches = dict().fromkeys(columns_dict.keys(), [""] * len(df))
        # iterate over all columns
        for i, column_name in enumerate(column_names):
            # iterate over all items in the column dictionary to find which column belongs to which table name
            for table_col, alternative_names in columns_dict.items():
                if column_name.lower() in alternative_names:
                    matches[table_col] = df[column_name].values
                    break

        # perform few checks
        necessary_fields = ("calibrant", "charge")
        if not all([_check_field(necessary) for necessary in necessary_fields]):
            raise ValueError(f"Calibration data should include these fields: `{necessary_fields}`")

        # fill-in molecular weight
        if not _check_field("mw") and all([_check_field("charge"), _check_field("mz")]):
            matches["mw"] = (matches["mz"] - matches["charge"] * 1) * matches["charge"]  # noqa
            LOGGER.debug("Filled in molecular weight field")

        return matches


CCS_HANDLER = CCSHandler()
