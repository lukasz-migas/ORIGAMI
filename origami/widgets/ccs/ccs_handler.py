"""CCS handler"""


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


CCS_HANDLER = CCSHandler()
