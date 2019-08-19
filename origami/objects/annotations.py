# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
"""Annotations container"""
import re


class Annotation:
    """Class containing all metadata about a single annotation"""

    VERSION = 1

    def __init__(self, **kwargs):

        # position
        self.position_x = kwargs["position_x"]
        self.position_y = kwargs["position_y"]
        self.position_label_x = kwargs["position_label_x"]
        self.position_label_y = kwargs["position_label_y"]

        # visual information
        self.color = kwargs.get("color", [1.0, 1.0, 1.0])
        self.add_arrow = kwargs.get("add_arrow", True)
        self.show = kwargs.get("show", True)

        # meta information
        self.span_min = kwargs.get("span_min", 0)
        self.span_max = kwargs.get("span_max", 0)
        self.charge = kwargs.get("charge", 0)
        self.label = kwargs.get("label", "")

    def __repr__(self):
        return f"Annotation - Label: {self.label} | Charge: {self.charge} | x: {self.position_x} | y: {self.position_y}"

    #         # peak information
    #         self.peak_x = kwargs.get("peak_x", 0)
    #         self.peak_y = kwargs.get("peak_y", 0)
    #         self.peak_width = kwargs.get("peak_width", 0)
    #         self.peak_width_height = kwargs.get("peak_width_height", 0)
    #         self.left_ips = kwargs.get("left_ips", 0)
    #         self.right_ips = kwargs.get("right_ips", 0)

    def update_annotation(self, **kwargs):
        """Update annotation"""
        # position
        self.position_x = kwargs.get("position_x", self.position_x)
        self.position_y = kwargs.get("position_y", self.position_y)
        self.position_label_x = kwargs.get("position_label_x", self.position_label_x)
        self.position_label_y = kwargs.get("position_label_y", self.position_label_y)

        # visual information
        self.color = kwargs.get("color", self.color)
        self.add_arrow = kwargs.get("add_arrow", self.add_arrow)
        self.show = kwargs.get("show", self.show)

        # meta information
        self.span_min = kwargs.get("span_min", self.span_min)
        self.span_max = kwargs.get("span_max", self.span_max)
        self.charge = kwargs.get("charge", self.charge)
        self.label = kwargs.get("label", self.label)


class Annotations:
    """Class containing single annotation metadata"""

    VERSION = 1

    def __init__(self):
        self.annotations = dict()

    def __len__(self):
        return len(self.annotations)

    def __repr__(self):
        return f"Annotations: {len(self)}"

    def __iter__(self):
        return iter(self.annotations)

    def __setitem__(self, key, item):
        self.annotations[key] = item

    def __getitem__(self, key):
        return self.annotations[key]

    def keys(self):
        return self.annotations.keys()

    def values(self):
        return self.annotations.values()

    def items(self):
        return self.annotations.items()

    def pop(self, *args):
        return self.annotations.pop(*args)

    def __contains__(self, item):
        return item in self.annotations

    def add_annotation(self, name, annotation_dict):
        """Add annotation"""

        name = self.check_name(name)

        self.annotations[name] = Annotation(**annotation_dict)

    def add_annotation_from_old_format(self, name, annotation_dict, annotation_version=0):
        if annotation_version == self.VERSION:
            self.add_annotation(name, annotation_dict)
            return

        if annotation_version == 0:
            annotation_alias_dict_v0 = {
                "min": "span_min",
                "max": "span_max",
                "charge": "charge",
                "intensity": "position_y",
                "isotopic_x": "position_x",
                "isotopic_y": "position_y",
                "label": "label",
                "color": "color",
                "add_arrow": "add_arrow",
                "position_label_x": "position_label_x",
                "position_label_y": "position_label_y",
            }
            annotation_dict_updated = dict()
            for old_key, new_key in annotation_alias_dict_v0.items():
                annotation_dict_updated[new_key] = annotation_dict.pop(old_key)

            self.add_annotation(name, annotation_dict_updated)

    def check_name(self, name):
        """Check name against all annotations and if duplicate, create alternative"""
        return name

    def check_color(self, color):
        return color

    def update_annotation(self, name, annotation_dict):
        if name in self.annotations:
            self.annotations[name].update_annotation(**annotation_dict)

    def remove_annotation(self, annotation_name):
        if annotation_name in self.names:
            del self.annotations[annotation_name]
            del self.names[self.names.index(annotation_name)]
