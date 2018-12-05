


class data_handling():
    def __init__(self, presenter, view, config, **kwargs):
        self.presenter = presenter
        self.view = view
        self.documentTree = view.panelDocuments.topP.documents
        self.config = config