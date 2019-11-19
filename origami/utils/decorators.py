def signal_blocker(fcn):
    def wrapped(self, *args, **kwargs):
        if not hasattr(self, "_block"):
            out = fcn(self, *args, **kwargs)
            return out
        self._block = True
        out = fcn(self, *args, **kwargs)
        self._block = False
        return out

    return wrapped
