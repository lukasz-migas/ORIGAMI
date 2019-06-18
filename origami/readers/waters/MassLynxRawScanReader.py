''' Waters 
    MassLynx Python SDK
'''
from readers.waters.MassLynxRawReader import MassLynxRawReader, MassLynxBaseType
from ctypes import c_float, POINTER, c_int, c_void_p, cast, c_byte


class MassLynxRawScanReader(MassLynxRawReader):
    """Read masslynx scan data"""

    def __init__(self, source):
        super().__init__(source, MassLynxBaseType.SCAN)

    # @classmethod
    # def CreateFromPath( cls, path ):                      # alternative constructor - pass class to constructor
    #    return cls(MassLynxRawReader.fromPath( path, 1 ))                     # initalise with reader

    # @classmethod
    # def CreateFromReader( cls, sourceReader ):                  # alternative constructor - pass class to constructor
    #     return cls(MassLynxRawReader.fromReader( sourceReader, 1 ))                     # initalise with reader

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

        masses = pM[0:size.value]
        intensities = pI[0:size.value]

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
        readScanFlags.argtypes = [c_void_p, c_int, c_int, POINTER(
            c_void_p), POINTER(c_void_p), POINTER(c_void_p), POINTER(c_int)]
        super().CheckReturnCode(readScanFlags(self._getReader(), whichFunction, whichScan, pMasses, pIntensities, pFlags, size))

        # fill the array
        pM = cast(pMasses, POINTER(c_float))
        pI = cast(pIntensities, POINTER(c_float))

        masses = pM[0:size.value]
        intensities = pI[0:size.value]

        # check for flags
        if None != pFlags.value:
            pF = cast(pFlags, POINTER(c_byte))
            flags = pF[0:size.value]

        return masses, intensities, flags

    def ReadDriftScan(self, whichFunction, whichScan, whichDrift):

        # create the return values
        size = c_int(0)
        pMasses = c_void_p()
        pIntensities = c_void_p()

        # read scan
        readDriftScan = MassLynxRawReader.massLynxDll.readDriftScan
        readDriftScan.argtypes = [c_void_p, c_int, c_int, c_int, POINTER(c_void_p), POINTER(c_void_p), POINTER(c_int)]
        super().CheckReturnCode(readDriftScan(self._getReader(), whichFunction, whichScan, whichDrift, pMasses, pIntensities, size))

        # fill the array
        pM = cast(pMasses, POINTER(c_float))
        pI = cast(pIntensities, POINTER(c_float))

        masses = pM[0:size.value]
        intensities = pI[0:size.value]

        # dealocate memory
        # MassLynxRawReader.ReleaseMemory( pMasses)
        # MassLynxRawReader.ReleaseMemory( pIntensities)

        return masses, intensities

    # def readDaughterScan( self, whichFunction, whichScan ):
    #    try:
    #        size = self.getScanSize( whichFunction,whichScan )

    #    	# get the daughter scan size
    #        daughtersize = c_int(0)

    #        # get daughter size
    #        getDaughterScanSize =  RawReader.massLynxDll.getDaughterScanSize
    #        getDaughterScanSize.argtypes = [c_void_p, c_int, c_int, POINTER(c_int)]
    #        RawReader.CheckReturnCode( getDaughterScanSize(RawReader.getReader(self),whichFunction,whichScan, daughtersize) )

    #      # create the float arrays
    #        masses = (c_float*size)()
    #        intensities = (c_float*size)()
    #        daughters = (c_float*daughtersize.value)()

    #        # read daughter size
    #        readSpectrumDaughters = RawReader.massLynxDll.readSpectrumDaughters
    #        readSpectrumDaughters.argtypes = [c_void_p, c_int, c_int,  POINTER(c_float), POINTER(c_float), POINTER(c_float)]
    #        RawReader.CheckReturnCode( readSpectrumDaughters(RawReader.getReader(self), whichFunction, whichScan, masses, intensities, daughters) )

    #    except RawReaderException as e:
    #        e.Handler()
    #        return [], [], []

    #    return list(masses), list(intensities), list(daughters)
