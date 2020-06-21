"""Annotations container"""
# Standard library imports
from typing import Dict
from typing import Tuple
from builtins import isinstance

# Third-party imports
import numpy as np


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
    """Class containing annotation data"""

    VERSION = 1
    NOT_EDITABLE = ("kind",)

    def __init__(
        self,
        name: str,
        label: str,
        label_position: Tuple[float, float],
        patch_position: Tuple[float, float, float, float],
        patch_color: Tuple[float, float, float] = (1, 1, 1),
        kind: str = "1d",
        label_show: bool = True,
        label_color: Tuple[float, float, float] = (1, 1, 1),
        patch_alpha: float = 1.0,
        patch_show: bool = True,
        marker_show: bool = False,
        marker_position: Tuple[float, float] = None,
        arrow_show: bool = False,
        arrow_style: str = "default",
    ):
        # identifiers
        assert kind in ["1d", "2d"], f"Annotation style `{kind}` is not supported."
        self._kind = kind
        self._name = name

        # label parameters
        self._label = label
        self.label_position = label_position
        self._label_show = label_show
        self._label_color = label_color

        # patch
        self.patch_position = patch_position
        self._patch_color = patch_color
        self._patch_alpha = patch_alpha
        self._patch_show = patch_show

        # arrow
        self._arrow_show = arrow_show
        self._arrow_style = arrow_style

        # marker
        self._marker_show = marker_show
        self._marker_position = marker_position

    def __repr__(self):
        return f"{self.__class__.__name__}<label={self._label}>"

    @property
    def name(self):
        """Return the name of the object"""
        return self._name

    @name.setter
    def name(self, value):
        if not isinstance(value, str):
            raise ValueError("Cannot set name")
        self._name = value

    @property
    def label(self):
        """Return the label"""
        return self._label

    @label.setter
    def label(self, value):
        if not isinstance(value, str):
            raise ValueError("Cannot set label")
        self._label = value

    @property
    def label_position(self):
        """Return the label position for the annotation"""
        return self._label_position

    @label_position.setter
    def label_position(self, value):
        if not isinstance(value, (tuple, list)) and len(value) != 2:
            raise ValueError("Cannot set label position")
        self._label_position = value

    @property
    def label_color(self):
        """Return the label color for the annotation"""
        return self._label_color

    @label_color.setter
    def label_color(self, value):
        if not isinstance(value, (tuple, list)) and len(value) != 3:
            raise ValueError("Cannot set label color")
        self._label_color = value

    @property
    def patch_position(self):
        """Return the patch position, width and height for the annotation"""
        return self._patch_position

    @patch_position.setter
    def patch_position(self, value):
        if not isinstance(value, (tuple, list)) and len(value) != 4:
            raise ValueError("Cannot set patch position, width and height")
        self._patch_position = value

    @property
    def patch_color(self):
        """Return the patch color for the annotation"""
        return self._patch_color

    @patch_color.setter
    def patch_color(self, value):
        if not isinstance(value, (tuple, list)) and len(value) != 3:
            raise ValueError("Cannot set label color")
        self._patch_color = value

    @property
    def label_position_x(self):
        """Return the `x` position of the label"""
        return self._label_position[0]

    @label_position_x.setter
    def label_position_x(self, value):
        self._label_position = (value, self.label_position_y)

    @property
    def label_position_y(self):
        """Return the `y` position of the label"""
        return self._label_position[1]

    @label_position_y.setter
    def label_position_y(self, value):
        self._label_position = (self.label_position_x, value)

    @property
    def marker_position_x(self):
        """Return the `x` position of the label"""
        if self._marker_position is not None:
            return self._marker_position[0]
        return self._label_position[0]

    @property
    def marker_position_y(self):
        """Return the `y` position of the label"""
        if self._marker_position is not None:
            return self._marker_position[1]
        return self._label_position[1]

    @property
    def width(self):
        """Return the width of the patch shown on the plot"""
        return self._patch_position[2]

    @property
    def height(self):
        """Return the height of the patch shown on the plot"""
        return self._patch_position[3]

    @height.setter
    def height(self, value):
        """Return the height of the patch shown on the plot"""
        self._patch_position = (self.span_x_min, self.span_y_min, self.width, value)

    @property
    def span_x_min(self):
        """Return the starting position of the patch"""
        return self._patch_position[0]

    @property
    def span_x_max(self):
        """Return the final position of the patch"""
        return self._patch_position[0] + self._patch_position[2]

    @property
    def span_y_min(self):
        """Return the starting position of the patch"""
        return self._patch_position[1]

    @property
    def span_y_max(self):
        """Return the final position of the patch"""
        return self._patch_position[1] + self._patch_position[3]

    @property
    def arrow_show(self):
        """Return the arrow boolean"""
        return self._arrow_show

    @arrow_show.setter
    def arrow_show(self, value):
        if not isinstance(value, bool):
            raise ValueError("`arrow_show` only accepts boolean values")
        self._arrow_show = value

    @property
    def patch_show(self):
        """Return the patch boolean"""
        return self._patch_show

    @patch_show.setter
    def patch_show(self, value):
        if not isinstance(value, bool):
            raise ValueError("`patch_show` only accepts boolean values")
        self._patch_show = value

    def to_dict(self):
        """Output the annotation parameters in a dictionary format"""
        return dict(
            kind=self._kind,
            name=self._name,
            label=self._label,
            label_position=self._label_position,
            label_show=self._label_show,
            label_color=self._label_color,
            patch_position=self._patch_position,
            patch_color=self._patch_color,
            patch_alpha=self._patch_alpha,
            patch_show=self._patch_show,
            arrow_show=self._arrow_show,
            arrow_style=self._arrow_style,
            marker_show=self._marker_show,
            marker_position=self._marker_position,
        )

    # def get_arrow_position(self, position_x=None, position_y=None):
    #     """Get arrow position"""
    #
    #     if position_x is None:
    #         position_x = self.position_x
    #     arrow_dx = position_x - self.label_position_x
    #
    #     if position_y is None:
    #         position_y = self.position_y
    #     arrow_dy = position_y - self.label_position_y
    #
    #     return [self.label_position_x, self.label_position_y, arrow_dx, arrow_dy], position_x, position_y

    # noinspection DuplicatedCode
    def update(self, **kwargs):
        """Update any of the annotation attributes"""
        self._name = kwargs.pop("name", self._name)

        # label
        self._label = kwargs.get("label", self._label)
        self._label_show = kwargs.get("label_show", self._label_show)
        self.label_position = kwargs.get("label_position", self.label_position)
        self.label_color = kwargs.get("label_color", self.label_color)

        # patch
        self._patch_show = kwargs.get("patch_show", self._patch_show)
        self.patch_position = kwargs.get("patch_position", self.patch_position)
        self.patch_color = kwargs.get("patch_color", self.patch_color)
        self._patch_alpha = kwargs.get("patch_alpha", self._patch_alpha)

        # arrow
        self._arrow_show = kwargs.get("arrow_show", self._arrow_show)


class Annotations:
    """Class containing single annotation metadata"""

    VERSION = 1

    def __init__(self, annotations: Dict = None):
        self.annotations: Dict[str, Annotation] = dict()

        if annotations is not None:
            self.init_from_dict(annotations)

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

    def __delitem__(self, *args):
        self.annotations.pop(*args)

    def __contains__(self, item):
        return item in self.annotations

    @property
    def x(self):
        """Get m/z values for all peaks"""
        return np.asarray([annotation.label_position_x for annotation in self.annotations.values()])

    @property
    def y(self):
        """Get intensity values for all peaks"""
        return np.asarray([annotation.label_position_y for annotation in self.annotations.values()])

    @property
    def patch_x_min(self):
        """Get left-hand side edge m/z values for all peaks"""
        return np.asarray([annotation.span_x_min for annotation in self.annotations.values()])

    @property
    def patch_x_max(self):
        """Get right-hand side edge m/z values for all peaks"""
        return np.asarray([annotation.span_x_max for annotation in self.annotations.values()])

    @property
    def patch_y_min(self):
        """Get left-hand side edge m/z values for all peaks"""
        return np.asarray([annotation.span_y_min for annotation in self.annotations.values()])

    @property
    def patch_y_max(self):
        """Get right-hand side edge m/z values for all peaks"""
        return np.asarray([annotation.span_y_max for annotation in self.annotations.values()])

    @property
    def width(self):
        """Get full-width half max for all peaks"""
        return np.asarray([annotation.width for annotation in self.annotations.values()])

    @property
    def height(self):
        """Get full-width half max for all peaks"""
        return np.asarray([annotation.height for annotation in self.annotations.values()])

    @property
    def names(self):
        """Get full-width half max for all peaks"""
        return np.asarray([annotation.name for annotation in self.annotations.values()])

    @property
    def labels(self):
        """Get full-width half max for all peaks"""
        return np.asarray([annotation.label for annotation in self.annotations.values()])

    @property
    def patch_show(self):
        """Get full-width half max for all peaks"""
        return np.asarray([annotation.patch_show for annotation in self.annotations.values()], dtype=np.bool)

    @property
    def patch_colors(self):
        """Get full-width half max for all peaks"""
        return np.asarray([annotation.patch_color for annotation in self.annotations.values()])

    @property
    def label_colors(self):
        """Get full-width half max for all peaks"""
        return np.asarray([annotation.label_color for annotation in self.annotations.values()])

    def add(self, name: str, value: Dict):
        """Add new annotations object"""
        if isinstance(value, Annotation):
            assert name == value.name, "Annotation name must match the name in the dictionary"
            self.annotations[name] = value
        elif isinstance(value, dict):
            assert name == value["name"], "Annotation name must match the name in the dictionary"
            self.annotations[name] = Annotation(**value)

    def init_from_dict(self, annotations: Dict):
        """Instantiate annotation keys from dictionary"""
        for name, value in annotations.items():
            assert isinstance(name, str), "Annotation name must be a string"
            assert isinstance(value, dict), "Annotation value must be a dictionary"
            self.add(name, value)

        return self

    def to_dict(self):
        """Reformat the annotations object into a dictionary that can be conveniently stored"""
        annotations = dict()
        for name, value in self.items():
            annotations[name] = value.to_dict()

        return annotations

    def get(self, key: str, default=None):
        """Return dictionary value"""
        return self.annotations.get(key, default)

    def keys(self):
        """Returns a copy of the annotation's list of keys"""
        return self.annotations.keys()

    def values(self):
        """Returns a copy of the annotation's list of values"""
        return self.annotations.values()

    def items(self):
        """Returns a copy of the annotation's list of keys and values"""
        return self.annotations.items()

    def pop(self, *args):
        """Remove the annotation and return it"""
        return self.annotations.pop(*args)


# class Annotation_:
#     """Class containing all metadata about a single annotation"""
#
#     VERSION = 1
#
#     def __init__(self, name, label_position, patch_position, patch_color, kind="1D", **kwargs):
#
#         # type
#         self.kind = kind
#
#         # name
#         self.name = name
#
#         # label
#         self.label = kwargs.get("label", "")
#         self.label_position = label_position
#         self.label_show = kwargs.get("label_show", True)
#         self.label_color = kwargs.get("label_color", [1.0, 1.0, 1.0])
#
#         # patch
#         self.patch_position = patch_position
#         self.patch_show = kwargs.get("patch_show", True)
#         self.patch_color = kwargs.get("patch_color", patch_color)
#         self.patch_show = kwargs.get("patch_show", False)
#
#         # arrow
#         self.arrow_show = kwargs.get("arrow_show", True)
#         self.arrow_style = "default"
#
#         # marker
#         self.marker = None
#
#         # meta
#         self.charge = kwargs.get("charge", 0)
#         self.position_x = kwargs.get("position_x", self.label_position[0])
#         self.position_y = kwargs.get("position_y", self.label_position[1])
#
#     def __repr__(self):
#         return (
#             f"Annotation(label={self.label}; \ncolor={self.label_color}; charge={self.charge}"
#             + f"; patch={self.patch_position}; color={self.patch_color}"
#             + f"; arrow={self.arrow_show})"
#         )
#
#     @property
#     def kind(self):
#         return self._kind
#
#     @kind.setter
#     def kind(self, kind):
#         if kind not in ["1D", "2D"]:
#             raise NotImplementedError(f"Annotation of `{kind}` has not been implemented yet.")
#         self._kind = kind
#
#     @property
#     def label_position(self):
#         return self._label_position
#
#     @label_position.setter
#     def label_position(self, label_position):
#         if not isinstance(label_position, (tuple)):
#             label_position = list(label_position)
#         self._label_position = label_position
#
#     @property
#     def patch_position(self):
#         return self._patch_position
#
#     @patch_position.setter
#     def patch_position(self, patch_position):
#         if not isinstance(patch_position, (tuple)):
#             patch_position = list(patch_position)
#         self._patch_position = patch_position
#
#     #         self.position_x = patch_position[0]
#     #         self.position_y = patch_position[1]
#
#     @property
#     def span_min(self):
#         return self._patch_position[0]
#
#     @property
#     def span_max(self):
#         return self._patch_position[0] + self._patch_position[2]
#
#     @property
#     def width(self):
#         return self._patch_position[2]
#
#     @property
#     def height(self):
#         return self._patch_position[3]
#
#     @property
#     def label_position_x(self):
#         return self._label_position[0]
#
#     @property
#     def label_position_y(self):
#         return self._label_position[1]
#
#     def get_arrow_position(self, position_x=None, position_y=None):
#
#         if position_x is None:
#             position_x = self.position_x
#         arrow_dx = position_x - self.label_position_x
#
#         if position_y is None:
#             position_y = self.position_y
#         arrow_dy = position_y - self.label_position_y
#
#         return [self.label_position_x, self.label_position_y, arrow_dx, arrow_dy], position_x, position_y
#
#     def update_annotation(self, **kwargs):
#         """Update annotation"""
#
#         # name
#         self.name = kwargs.get("name", self.name)
#
#         # label
#         self.label = kwargs.get("label", self.label)
#         self.label_position = kwargs.get("label_position", self.label_position)
#         self.label_show = kwargs.get("label_show", self.label_show)
#         self.label_color = kwargs.get("label_color", self.label_color)
#
#         # patch
#         self.patch_position = kwargs.get("patch_position", self.patch_position)
#         self.patch_show = kwargs.get("patch_show", self.patch_show)
#         self.patch_color = kwargs.get("patch_color", self.patch_color)
#         self.patch_show = kwargs.get("patch_show", self.patch_show)
#
#         # position
#         self.position_x = kwargs.get("position_x", self.position_x)
#         self.position_y = kwargs.get("position_y", self.position_y)
#
#         # arrow
#         self.arrow_show = kwargs.get("arrow_show", self.arrow_show)
#
#         # charge
#         self.charge = kwargs.get("charge", self.charge)
#
#
# class Annotations_:
#     """Class containing single annotation metadata"""
#
#     VERSION = 1
#
#     def __init__(self):
#         self.annotations = dict()
#
#     def __len__(self):
#         return len(self.annotations)
#
#     def __repr__(self):
#         return f"Annotations: {len(self)}"
#
#     def __iter__(self):
#         return iter(self.annotations)
#
#     def __setitem__(self, key, item):
#         self.annotations[key] = item
#
#     def __getitem__(self, key):
#         return self.annotations[key]
#
#     def __delitem__(self, *args):
#         self.annotations.pop(*args)
#
#     def __contains__(self, item):
#         return item in self.annotations
#
#     def get(self, key, default):
#         return self.annotations.get(key, default)
#
#     def keys(self):
#         return self.annotations.keys()
#
#     def values(self):
#         return self.annotations.values()
#
#     def items(self):
#         return self.annotations.items()
#
#     def pop(self, *args):
#         return self.annotations.pop(*args)
#
#     def add_annotation(self, name, annotation_dict):
#         """Add annotation"""
#
#         name = self.check_name(name)
#         self.annotations[name] = Annotation(**annotation_dict)
#
#     def add_annotation_from_old_format(self, name, annotation_dict, annotation_version=0):
#         if annotation_version == self.VERSION:
#             self.add_annotation(name, annotation_dict)
#             return
#
#         if annotation_version == 0:
#             annotation_alias_dict_v0 = {
#                 "min": "span_min",
#                 "max": "span_max",
#                 "charge": "charge",
#                 "intensity": "position_y",
#                 "isotopic_x": "position_x",
#                 "isotopic_y": "position_y",
#                 "label": "label",
#                 "color": "color",
#                 "add_arrow": "add_arrow",
#                 "position_label_x": "position_label_x",
#                 "position_label_y": "position_label_y",
#             }
#             annotation_dict_updated = dict()
#             for old_key, new_key in annotation_alias_dict_v0.items():
#                 annotation_dict_updated[new_key] = annotation_dict.pop(old_key)
#
#             self.add_annotation(name, annotation_dict_updated)
#
#     def append_annotation(self, annotation_obj):
#         if type(annotation_obj).__name__ != "Annotation":
#             raise ValueError("Annotation must be of type `Annotation`")
#
#         name = self.check_name(annotation_obj.name)
#         self.annotations[name] = annotation_obj
#
#     def check_name(self, name):
#         """Check name against all annotations and if duplicate, create alternative"""
#         return name
#
#     def check_color(self, color):
#         return color
#
#     def update_annotation(self, name, annotation_dict):
#         if name in self.annotations:
#             self.annotations[name].update_annotation(**annotation_dict)
#
#     def remove_annotation(self, annotation_name):
#         annotations = list(self.annotations.keys())
#         if annotation_name in annotations:
#             del self.annotations[annotation_name]
#
#     def find_annotation_by_keywords(self, **kwargs):
#
#         for name, annotation in self.items():
#             if annotation.span_min == kwargs.get("min", -1) and annotation.span_max == kwargs.get("max", -1):
#                 return name
#
#         return None
