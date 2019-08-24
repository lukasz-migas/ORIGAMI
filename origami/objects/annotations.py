# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
"""Annotations container"""


class Annotation:
    """Class containing all metadata about a single annotation"""

    VERSION = 1

    def __init__(self, patch_position, color, kind="1D", **kwargs):

        # type
        self.kind = kind

        # label
        self.label = kwargs.get("label", "")
        self.label_position = kwargs.get("label_position", [0, 0])
        self.label_show = kwargs.get("label_show", True)
        self.label_color = kwargs.get("label_color", [1.0, 1.0, 1.0])

        # patch
        self.patch_position = patch_position
        self.patch_show = kwargs.get("patch_show", True)
        self.patch_color = kwargs.get("patch_color", color)

        # arrow
        self.arrow_show = kwargs.get("arrow_show", False)
        self.arrow_style = "default"

        # marker
        self.marker = None

        # meta
        self.charge = kwargs.get("charge", 0)

    def __repr__(self):
        return (
            f"Annotation(label={self.label}; color={self.label_color}; charge={self.charge}"
            + f"; patch={self.patch_position}; color={self.patch_color}"
            + f"; arrow={self.arrow_show})"
        )

    @property
    def kind(self):
        return self._kind

    @kind.setter
    def kind(self, kind):
        if kind not in ["1D", "2D"]:
            raise NotImplementedError(f"Annotation of `{kind}` has not been implemented yet.")
        self._kind = kind

    @property
    def label_position(self):
        return self._label_position

    @label_position.setter
    def label_position(self, label_position):
        if not isinstance(label_position, (tuple)):
            label_position = list(label_position)
        self._label_position = label_position

    @property
    def patch_position(self):
        return self._patch_position

    @patch_position.setter
    def patch_position(self, patch_position):
        if not isinstance(patch_position, (tuple)):
            patch_position = list(patch_position)
        self._patch_position = patch_position

    def update_annotation(self, **kwargs):
        """Update annotation"""
        pass


#         # position
#         self.position_x = kwargs.get("position_x", self.position_x)
#         self.position_y = kwargs.get("position_y", self.position_y)
#         self.position_label_x = kwargs.get("position_label_x", self.position_label_x)
#         self.position_label_y = kwargs.get("position_label_y", self.position_label_y)
#
#         # visual information
#         self.color = kwargs.get("color", self.color)
#         self.add_arrow = kwargs.get("add_arrow", self.add_arrow)
#         self.show = kwargs.get("show", self.show)
#
#         # meta information
#         self.span_min = kwargs.get("span_min", self.span_min)
#         self.span_max = kwargs.get("span_max", self.span_max)
#         self.charge = kwargs.get("charge", self.charge)
#         self.label = kwargs.get("label", self.label)

# class Annotation:
#     """Class containing all metadata about a single annotation"""
#
#     VERSION = 1
#
#     def __init__(self, **kwargs):
#
#         # positionA
#         self.position_x = kwargs["position_x"]
#         self.position_y = kwargs["position_y"]
#         self.position_label_x = kwargs["position_label_x"]
#         self.position_label_y = kwargs["position_label_y"]
#
#         # visual information
#         self.color = kwargs.get("color", [1.0, 1.0, 1.0])
#         self.add_arrow = kwargs.get("add_arrow", True)
#         self.show = kwargs.get("show", True)
#
#         # meta information
#         self.span_min = kwargs.get("span_min", 0)
#         self.span_max = kwargs.get("span_max", 0)
#         self.charge = kwargs.get("charge", 0)
#         self.label = kwargs.get("label", "")
#
#     def __repr__(self):
#         return f"Annotation(label={self.label}; charge={self.charge}" \
#             +f"; x={self.position_x}; y={self.position_y}; color={self.color}" \
#             +f"; arrow={self.add_arrow})"
#
#     def update_annotation(self, **kwargs):
#         """Update annotation"""
#         # position
#         self.position_x = kwargs.get("position_x", self.position_x)
#         self.position_y = kwargs.get("position_y", self.position_y)
#         self.position_label_x = kwargs.get("position_label_x", self.position_label_x)
#         self.position_label_y = kwargs.get("position_label_y", self.position_label_y)
#
#         # visual information
#         self.color = kwargs.get("color", self.color)
#         self.add_arrow = kwargs.get("add_arrow", self.add_arrow)
#         self.show = kwargs.get("show", self.show)
#
#         # meta information
#         self.span_min = kwargs.get("span_min", self.span_min)
#         self.span_max = kwargs.get("span_max", self.span_max)
#         self.charge = kwargs.get("charge", self.charge)
#         self.label = kwargs.get("label", self.label)


class Annotations(object):
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
        annotations = list(self.annotations.keys())
        if annotation_name in annotations:
            del self.annotations[annotation_name]

    def find_annotation_by_keywords(self, **kwargs):

        for name, annotation in self.items():
            if annotation.span_min == kwargs.get("min", -1) and annotation.span_max == kwargs.get("max", -1):
                return name

        return None
