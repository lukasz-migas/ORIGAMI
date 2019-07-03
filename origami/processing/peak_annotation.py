# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas


class PeakAnnotation():

    def __init__(self, **kwargs):
        self.document = kwargs.get('document', '')
        self.dataset = kwargs.get('dataset', '')

    def get_document_annotations(self):
        pass

    def get_annotation(self):
        pass

    def set_document_annotations(self):
        pass

    def set_annotation(self):
        pass

    def add_annotation(self, annotation_dict, **kwargs):
        pass
