"""Annotations container"""


class Annotations:

    def __init__(self):
        self.annotations = dict()
        self.names = []

    def add_annotation(self, annotation_dict):
        pass

    def update_annotation(self, annotation_name, annotation_dict):
        pass

    def remove_annotation(self, annotation_name):
        if annotation_name in self.names:
            del self.annotations[annotation_name]
            del self.names[self.names.index(annotation_name)]
