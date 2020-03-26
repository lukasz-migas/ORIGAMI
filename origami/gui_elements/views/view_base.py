class ViewBase:
    def __init__(self, parent, figsize, config, title):
        self.parent = parent
        self.figsize = figsize
        self.config = config
        self.title = title
        self.DATA_KEYS = None

        self._panel = None
        self._plot = None
        self._sizer = None

        # user settings
        self._x_label = None
        self._y_label = None
        self._data = dict()
        self._plt_kwargs = dict()

        self.document_name = None
        self.dataset_name = None

    def __repr__(self):
        return f"{self.__class__.__name__}<title={self.title}>"

    @property
    def x_label(self):
        return self._x_label

    @x_label.setter
    def x_label(self, value):
        if value == self._x_label:
            return

        self._x_label = value
        self._update()

    @property
    def y_label(self):
        return self._x_label

    @y_label.setter
    def y_label(self, value):
        if value == self._x_label:
            return

        self._y_label = value
        self._update()

    def set_data(self, **kwargs):
        """Update plot data"""
        changed = False
        if self.DATA_KEYS is not None:
            for key, value in kwargs.items():
                if key in self.DATA_KEYS:
                    self._data[key] = value
                    changed = True

        if changed:
            self._update()

    def set_document(self, **kwargs):
        """Set document information for particular plot"""
        if "document" in kwargs:
            self.document_name = kwargs.pop("document")
        if "dataset" in kwargs:
            self.document_name = kwargs.pop("dataset")

    def plot(self, *args, **kwargs):
        raise NotImplementedError("Must implement method")

    def update(self, *args, **kwargs):
        raise NotImplementedError("Must implement method")

    def _update(self):
        raise NotImplementedError("Must implement method")
