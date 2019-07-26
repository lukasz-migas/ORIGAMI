""" Waters
    MassLynx Python Chromatogram reader SDK
"""
from ctypes import c_bool
from ctypes import c_float
from ctypes import c_int
from ctypes import c_void_p
from ctypes import cast
from ctypes import POINTER

from readers.waters.MassLynxRawReader import MassLynxBaseType
from readers.waters.MassLynxRawReader import MassLynxRawReader


class MassLynxRawChromatogramReader(MassLynxRawReader):
    """Read masslynx chromatogram data"""

    def __init__(self, source):
        super().__init__(source, MassLynxBaseType.CHROM)

    def ReadTIC(self, whichFunction):
        #         times = []
        #         intensities = []

        # create the retrun values
        size = c_int(0)
        pTimes = c_void_p()
        pIntensities = c_void_p()

        # read tic
        readTIC = MassLynxRawReader.massLynxDll.readTICChromatogram
        readTIC.argtypes = [c_void_p, c_int, POINTER(c_void_p), POINTER(c_void_p), POINTER(c_int)]
        super().CheckReturnCode(readTIC(self._getReader(), whichFunction, pTimes, pIntensities, size))

        # fill the array
        pT = cast(pTimes, POINTER(c_float))
        pI = cast(pIntensities, POINTER(c_float))

        times = pT[0 : size.value]
        intensities = pI[0 : size.value]

        # dealocate memory
        MassLynxRawReader.ReleaseMemory(pTimes)
        MassLynxRawReader.ReleaseMemory(pIntensities)

        return times, intensities

    def ReadBPI(self, whichFunction):
        # times = []
        # intensities = []
        # try:
        # create the retrun values
        size = c_int(0)
        pTimes = c_void_p()
        pIntensities = c_void_p()

        # read tic
        readBPI = MassLynxRawReader.massLynxDll.readTICChromatogram
        readBPI.argtypes = [c_void_p, c_int, POINTER(c_void_p), POINTER(c_void_p), POINTER(c_int)]
        super().CheckReturnCode(readBPI(self._getReader(), whichFunction, pTimes, pIntensities, size))

        # fill the array
        pT = cast(pTimes, POINTER(c_float))
        pI = cast(pIntensities, POINTER(c_float))

        times = pT[0 : size.value]
        intensities = pI[0 : size.value]

        # dealocate memory
        MassLynxRawReader.ReleaseMemory(pTimes)
        MassLynxRawReader.ReleaseMemory(pIntensities)

        # except MassLynxException as e:
        #    e.Handler()
        #    return [], []

        return times, intensities

    def ReadMassChromatogram(self, whichFunction, whichMass, massTollerance, daughters):
        # just call multiple mass with list of 1
        whichMasses = [whichMass]
        times, intensities = self.ReadMassChromatograms(whichFunction, whichMasses, massTollerance, daughters)

        return times, intensities[0]

    def ReadMassChromatograms(self, whichFunction, whichMasses, massTollerance, daughters):
        #         times = []
        intensities = []

        # get the array of masses
        numMasses = len(whichMasses)
        masses = (c_float * numMasses)(*whichMasses)

        # create the retrun values
        size = c_int(0)
        pTimes = c_void_p()

        # create array of pointers to hold return intensities
        pIntensities = c_void_p()

        readMassChroms = MassLynxRawReader.massLynxDll.readMassChromatograms
        readMassChroms.argtypes = [
            c_void_p,
            c_int,
            POINTER(c_float),
            c_int,
            POINTER(c_void_p),
            POINTER(c_void_p),
            c_float,
            c_bool,
            POINTER(c_int),
        ]
        super().CheckReturnCode(
            readMassChroms(
                self._getReader(),
                whichFunction,
                masses,
                numMasses,
                pTimes,
                pIntensities,
                massTollerance,
                daughters,
                size,
            )
        )

        # fill the array and free memory
        pT = cast(pTimes, POINTER(c_float))
        times = pT[0 : size.value]
        MassLynxRawReader.ReleaseMemory(pTimes)

        # fill in the mass chroms and free memory
        pI = cast(pIntensities, POINTER(c_float))
        for index in range(0, numMasses):
            intensities.append(pI[index * size.value : (index + 1) * size.value])
        #            MassLynxRawReader.ReleaseMemory( ppIntensities[ index] )
        MassLynxRawReader.ReleaseMemory(pIntensities)

        return times, intensities
