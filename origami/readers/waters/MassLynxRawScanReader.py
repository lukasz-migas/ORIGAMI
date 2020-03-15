""" Waters
    MassLynx Python SDK
"""
# Standard library imports
from ctypes import POINTER
from ctypes import cast
from ctypes import c_int
from ctypes import c_byte
from ctypes import c_float
from ctypes import c_void_p

# Local imports
from origami.readers.waters.MassLynxRawReader import MassLynxBaseType
from origami.readers.waters.MassLynxRawReader import MassLynxRawReader


class MassLynxRawScanReader(MassLynxRawReader):
    """Read masslynx scan data"""

    def __init__(self, source):
        super().__init__(source, MassLynxBaseType.SCAN)

    def ReadScan(self, whichFunction, whichScan):
        #         masses = []
        #         intensities = []

        # create the retrun values
        size = c_int(0)
        pMasses = c_void_p()
        pIntensities = c_void_p()

        # read scan
        readScan = MassLynxRawReader.massLynxDll.readScan
        readScan.argtypes = [c_void_p, c_int, c_int, POINTER(c_void_p), POINTER(c_void_p), POINTER(c_int)]
        super().CheckReturnCode(readScan(self._getReader(), whichFunction, whichScan, pMasses, pIntensities, size))

        # fill the array
        pM = cast(pMasses, POINTER(c_float))
        pI = cast(pIntensities, POINTER(c_float))

        masses = pM[0 : size.value]
        intensities = pI[0 : size.value]

        # dealocate memory
        # MassLynxRawReader.ReleaseMemory( pMasses)
        # MassLynxRawReader.ReleaseMemory( pIntensities)

        return masses, intensities

    def ReadScanFlags(self, whichFunction, whichScan):
        flags = []

        # create the retrun values
        size = c_int(0)
        pMasses = c_void_p()
        pIntensities = c_void_p()
        pFlags = c_void_p()

        # read scan
        readScanFlags = MassLynxRawReader.massLynxDll.readScanFlags
        readScanFlags.argtypes = [
            c_void_p,
            c_int,
            c_int,
            POINTER(c_void_p),
            POINTER(c_void_p),
            POINTER(c_void_p),
            POINTER(c_int),
        ]
        super().CheckReturnCode(
            readScanFlags(self._getReader(), whichFunction, whichScan, pMasses, pIntensities, pFlags, size)
        )

        # fill the array
        pM = cast(pMasses, POINTER(c_float))
        pI = cast(pIntensities, POINTER(c_float))

        masses = pM[0 : size.value]
        intensities = pI[0 : size.value]

        # check for flags
        if pFlags.value is not None:
            pF = cast(pFlags, POINTER(c_byte))
            flags = pF[0 : size.value]

        return masses, intensities, flags

    def ReadDriftScan(self, whichFunction, whichScan, whichDrift):

        # create the return values
        size = c_int(0)
        pMasses = c_void_p()
        pIntensities = c_void_p()

        # read scan
        readDriftScan = MassLynxRawReader.massLynxDll.readDriftScan
        readDriftScan.argtypes = [c_void_p, c_int, c_int, c_int, POINTER(c_void_p), POINTER(c_void_p), POINTER(c_int)]
        super().CheckReturnCode(
            readDriftScan(self._getReader(), whichFunction, whichScan, whichDrift, pMasses, pIntensities, size)
        )

        # fill the array
        pM = cast(pMasses, POINTER(c_float))
        pI = cast(pIntensities, POINTER(c_float))

        masses = pM[0 : size.value]
        intensities = pI[0 : size.value]

        # dealocate memory
        # MassLynxRawReader.ReleaseMemory( pMasses)
        # MassLynxRawReader.ReleaseMemory( pIntensities)

        return masses, intensities
