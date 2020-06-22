"""Annotations container"""
# Standard library imports
from typing import Dict
from typing import Tuple

# Third-party imports
import numpy as np

# Local imports
from origami.utils.color import convert_hex_to_rgb_1


def check_type(lst, types):
    """Check whether all elements in the `lst` are of correct type"""
    return all(isinstance(x, types) for x in lst)


class Annotation:
    """Class containing annotation data"""

    VERSION = 1
    NOT_EDITABLE = ("kind",)

    def __repr__(self):
        return f"{self.__class__.__name__}<label={self._label}>"

    def __init__(
        self,
        name: str,
        label: str,
        label_position: Tuple[float, float],
        patch_position: Tuple[float, float, float, float],
        patch_color: Tuple[float, float, float] = (0, 0, 0),
        label_show: bool = True,
        label_color: Tuple[float, float, float] = (0, 0, 0),
        patch_alpha: float = 1.0,
        patch_show: bool = True,
        marker_show: bool = False,
        marker_position: Tuple[float, float] = None,
        arrow_show: bool = False,
        arrow_style: str = "default",
        kind: str = "1d",
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
        if not isinstance(value, (tuple, list)) or len(value) != 2 or not check_type(value, (int, float)):
            raise ValueError("Cannot set label position")
        self._label_position = tuple(value)

    @property
    def label_position_x(self):
        """Return the `x` position of the label"""
        return self._label_position[0]

    @label_position_x.setter
    def label_position_x(self, value):
        if not isinstance(value, (int, float)):
            raise ValueError("Cannot set `label_position_x` unless the value is an integer or float")
        self._label_position = (value, self.label_position_y)

    @property
    def label_position_y(self):
        """Return the `y` position of the label"""
        return self._label_position[1]

    @label_position_y.setter
    def label_position_y(self, value):
        if not isinstance(value, (int, float)):
            raise ValueError("Cannot set `label_position_y` unless the value is an integer or float")
        self._label_position = (self.label_position_x, value)

    @property
    def label_color(self):
        """Return the label color for the annotation"""
        return self._label_color

    # noinspection DuplicatedCode
    @label_color.setter
    def label_color(self, value):
        # allow conversion of hexadecimal colors
        if isinstance(value, str) and value.startswith("#"):
            value = convert_hex_to_rgb_1(value)
        if not isinstance(value, (tuple, list)) or len(value) != 3 or not check_type(value, (int, float)):
            raise ValueError("Cannot set label color")
        self._label_color = tuple(value)

    @property
    def marker_position(self):
        """Return the label position for the annotation"""
        return self._marker_position

    @marker_position.setter
    def marker_position(self, value):
        if not isinstance(value, (tuple, list)) or len(value) != 2 or not check_type(value, (int, float)):
            raise ValueError("Cannot set marker position")
        self._marker_position = tuple(value)

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
    def marker_show(self):
        """Return the arrow boolean"""
        return self._marker_show

    @property
    def patch_position(self):
        """Return the patch position, width and height for the annotation"""
        return self._patch_position

    @patch_position.setter
    def patch_position(self, value):
        # patch should be in order (x, y, width, height)
        if not isinstance(value, (tuple, list)) or len(value) != 4 or not check_type(value, (int, float)):
            raise ValueError("Cannot set patch position, width and height")
        self._patch_position = tuple(value)

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
    def patch_color(self):
        """Return the patch color for the annotation"""
        return self._patch_color

    # noinspection DuplicatedCode
    @patch_color.setter
    def patch_color(self, value):
        # allow conversion of hexadecimal colors
        if isinstance(value, str) and value.startswith("#"):
            value = convert_hex_to_rgb_1(value)
        if not isinstance(value, (tuple, list)) or len(value) != 3 or not check_type(value, (int, float)):
            raise ValueError("Cannot set label color")
        self._patch_color = tuple(value)

    @property
    def patch_show(self):
        """Return the patch boolean"""
        return self._patch_show

    @patch_show.setter
    def patch_show(self, value):
        if not isinstance(value, bool):
            raise ValueError("`patch_show` only accepts boolean values")
        self._patch_show = value

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
    def arrow_positions(self):
        """Return the patch boolean"""
        return self.get_arrow_position()

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

    def get_arrow_position(self, position_x=None, position_y=None):
        """Get arrow position"""
        if position_x is None:
            position_x = self.marker_position_x
        arrow_dx = position_x - self.label_position_x

        if position_y is None:
            position_y = self.marker_position_y
        arrow_dy = position_y - self.label_position_y

        return self.label_position_x, self.label_position_y, arrow_dx, arrow_dy

    # noinspection DuplicatedCode
    def update(self, **kwargs):
        """Update any of the annotation attributes"""
        self.name = kwargs.pop("name", self.name)

        # label
        self.label = kwargs.get("label", self.label)
        self.label_position = kwargs.get("label_position", self.label_position)
        self.label_color = kwargs.get("label_color", self.label_color)
        self._label_show = kwargs.get("label_show", self._label_show)

        # patch
        self.patch_show = kwargs.get("patch_show", self.patch_show)
        self.patch_position = kwargs.get("patch_position", self.patch_position)
        self.patch_color = kwargs.get("patch_color", self.patch_color)
        self._patch_alpha = kwargs.get("patch_alpha", self._patch_alpha)

        # arrow
        self.arrow_show = kwargs.get("arrow_show", self.arrow_show)

        # marker
        self.marker_position = kwargs.pop("marker_position", self.marker_position)


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
    def label_position_x(self):
        """Get m/z values for all peaks"""
        return np.asarray([annotation.label_position_x for annotation in self.annotations.values()])

    @property
    def label_position_y(self):
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

    @property
    def arrow_show(self):
        """Get full-width half max for all peaks"""
        return np.asarray([annotation.arrow_show for annotation in self.annotations.values()], dtype=np.bool)

    @property
    def arrow_positions(self):
        """Get arrow positions"""
        return np.asarray([annotation.arrow_positions for annotation in self.annotations.values()])

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
