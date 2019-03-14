import gzip


def gzOptOpen(filename, mode='r'):
    '''
    Utility function for opening files that may be compressed
    via gzip ('fasta.gz' files.)
    '''

    if filename.lower().endswith('.gz'):
        return gzip.open(filename, mode=mode)
    else:
        return open(filename, mode=mode)
