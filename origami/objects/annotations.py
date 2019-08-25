# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
"""Annotations container"""


def check_annotation_input(annotation_dict):
    """Check annotation input

    Parameters
    ----------
    annotation_dict : dict
        dictionary will required fields

    Returns
    -------
    annotation_dict : dict
        corrected dictionary

    Raises
    ------
    ValueError : if something is missing, ValueError is raised
    """
    # check for keys first
    bad_value_list = [None, "None", ""]
    required_keys = ["label", "label_position", "patch_position"]

    for key in required_keys:
        if key not in annotation_dict:
            raise ValueError(
                f"`{key}` not in the annotation dictionary. Annotation dictionary should at least include"
                + f"{required_keys}. "
            )

    # check label
    if annotation_dict["label"] in bad_value_list:
        raise ValueError("`label` must be a valid string. Please fill-in the `annotation` field")

    if len(annotation_dict["label_position"]) != 2:
        raise ValueError("`label_position` must be 2 items long [xposition, yposition]")

    if annotation_dict["label_position"][0] in bad_value_list:
        raise ValueError("`label_position_x` must be a number. Please fill-in `label position (x)` field")

    if annotation_dict["label_position"][1] in bad_value_list:
        raise ValueError("`label_position_x` must be a number. Please fill-in `label position (y)` field")

    # check patch position
    if len(annotation_dict["patch_position"]) != 4:
        raise ValueError("`patch_position` must be 4 items long [xmin, ymin, width, height]")

    if annotation_dict["patch_position"][0] in bad_value_list:
        annotation_dict["patch_position"][0] = annotation_dict["label_position"][0]
    if annotation_dict["patch_position"][1] in bad_value_list:
        annotation_dict["patch_position"][1] = annotation_dict["label_position"][1]

    if annotation_dict.get("charge", 1) is None:
        annotation_dict["charge"] = 1

    return annotation_dict


class Annotation:
    """Class containing all metadata about a single annotation"""

    VERSION = 1

    def __init__(self, name, label_position, patch_position, color, kind="1D", **kwargs):

        # type
        self.kind = kind

        # name
        self.name = name

        # label
        self.label = kwargs.get("label", "")
        self.label_position = label_position
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
        self.position = kwargs.get("position", self.label_position[0])
        self.intensity = kwargs.get("intensity", self.label_position[1])

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

    @property
    def span_min(self):
        return self._patch_position[0]

    @property
    def span_max(self):
        return self._patch_position[0] + self._patch_position[2]

    @property
    def width(self):
        return self._patch_position[2]

    @property
    def height(self):
        return self._patch_position[3]

    @property
    def label_position_x(self):
        return self._label_position[0]

    @property
    def label_position_y(self):
        return self._label_position[1]

    def get_arrow_position(self):
        arrow_x_end = self.position
        arrow_dx = arrow_x_end - self.label_position_x
        arrow_y_end = self.intensity
        arrow_dy = arrow_y_end - self.label_position_y

        return [self.label_position_x, self.label_position_y, arrow_dx, arrow_dy], arrow_x_end, arrow_y_end

    def update_annotation(self, **kwargs):
        """Update annotation"""

        # name
        self.name = kwargs.get("name", self.name)

        # label
        self.label = kwargs.get("label", self.label)
        self.label_position = kwargs.get("label_position", self.label_position)
        self.label_show = kwargs.get("label_show", self.label_show)
        self.label_color = kwargs.get("label_color", self.label_color)

        # patch
        self.patch_position = kwargs.get("patch_position", self.patch_position)
        self.patch_show = kwargs.get("patch_show", self.patch_show)
        self.patch_color = kwargs.get("patch_color", self.patch_color)

        # arrow
        self.arrow_show = kwargs.get("arrow_show", self.arrow_show)

        # charge
        self.charge = kwargs.get("charge", self.charge)


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

    def append_annotation(self, annotation_obj):
        if type(annotation_obj).__name__ != "Annotation":
            raise ValueError("Annotation must be of type `Annotation`")

        name = self.check_name(annotation_obj.name)
        self.annotations[name] = annotation_obj

    def check_name(self, name):
        """Check name against all annotations and if duplicate, create alternative"""
        return name

    def check_color(self, color):
        return color

    def update_annotation(self, name, annotation_dict):
        if name in self.annotations:
            print(name, "updating")
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
