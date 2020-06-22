"""Test annotations.py"""
# Third-party imports
import pytest

# Local imports
from origami.utils.secret import get_short_hash
from origami.objects.annotations import Annotation


def make_annotation():
    """Make annotation"""
    name = get_short_hash()
    annotation = Annotation(
        name=name,
        label="LABEL",
        label_position=(1, 1),
        patch_position=(1, 1, 0, 0),
        marker_position=(2, 2),
        marker_show=True,
        arrow_show=True,
        patch_show=True,
    )

    return name, annotation


class TestAnnotation:
    def test_init(self):
        name, annotation = make_annotation()
        assert isinstance(annotation, Annotation)
        assert annotation.name == name
        assert annotation.arrow_show is True
        assert annotation.patch_show is True
        assert annotation.marker_show is True

    def test_name(self):
        _, annotation = make_annotation()

        # change name
        new_value = "new name"
        annotation.name = new_value
        assert annotation.name == new_value

    @pytest.mark.parametrize("new_value", (123, ["HELLO"]))
    def test_name_fail(self, new_value):
        _, annotation = make_annotation()

        # change name
        with pytest.raises(ValueError):
            annotation.name = new_value

    def test_label(self):
        _, annotation = make_annotation()

        # change label
        new_value = "new label"
        annotation.label = new_value
        assert annotation.label == new_value

    @pytest.mark.parametrize("new_value", (123, ["HELLO"]))
    def test_label_fail(self, new_value):
        _, annotation = make_annotation()

        # change label
        with pytest.raises(ValueError):
            annotation.label = new_value

    @pytest.mark.parametrize("new_value", ((44, 12.2), [42, 32]))
    def test_label_position(self, new_value):
        _, annotation = make_annotation()

        # change position
        annotation.label_position = new_value
        assert annotation.label_position == tuple(new_value)
        assert annotation.label_position_x == new_value[0]
        assert annotation.label_position_y == new_value[1]
        assert isinstance(annotation.label_position, tuple)

    @pytest.mark.parametrize("new_value", ((44, 12.2, 3), [42], [42, "42"]))
    def test_label_position_fail(self, new_value):
        _, annotation = make_annotation()

        # change marker
        with pytest.raises(ValueError):
            annotation.label_position = new_value

    @pytest.mark.parametrize("new_value", ((44, 12.2), [42, 32]))
    def test_label_position_xy(self, new_value):
        _, annotation = make_annotation()

        # change position
        annotation.label_position_x = new_value[0]
        annotation.label_position_y = new_value[1]
        assert annotation.label_position == tuple(new_value)
        assert annotation.label_position_x == new_value[0]
        assert annotation.label_position_y == new_value[1]
        assert isinstance(annotation.marker_position, tuple)

    @pytest.mark.parametrize("new_value", ("42", [12]))
    def test_label_position_xy_fail(self, new_value):
        _, annotation = make_annotation()

        with pytest.raises(ValueError):
            annotation.label_position_x = new_value
        with pytest.raises(ValueError):
            annotation.label_position_y = new_value

    @pytest.mark.parametrize("new_value", ((44, 12.2), [42, 32]))
    def test_marker_position(self, new_value):
        _, annotation = make_annotation()

        # change marker
        annotation.marker_position = new_value
        assert annotation.marker_position == tuple(new_value)
        assert annotation.marker_position_x == new_value[0]
        assert annotation.marker_position_y == new_value[1]
        assert isinstance(annotation.marker_position, tuple)

    @pytest.mark.parametrize("new_value", ((44, 12.2, 3), [42], [42, "42"]))
    def test_marker_position_fail(self, new_value):
        _, annotation = make_annotation()

        # change marker
        with pytest.raises(ValueError):
            annotation.marker_position = new_value

    @pytest.mark.parametrize("new_value", ((44, 12.2, 0, 0), [42, 32, 12, 32]))
    def test_patch_position(self, new_value):
        _, annotation = make_annotation()
        # change
        annotation.patch_position = new_value
        assert annotation.patch_position == tuple(new_value)
        assert annotation.span_x_min == new_value[0]
        assert annotation.span_y_min == new_value[1]
        assert annotation.span_x_max == new_value[0] + new_value[2]
        assert annotation.span_y_max == new_value[1] + new_value[3]
        assert annotation.width == new_value[2]
        assert annotation.height == new_value[3]
        assert isinstance(annotation.patch_position, tuple)

        # test dict method
        out = annotation.to_dict()
        assert isinstance(out, dict)
        assert "name" in out
        assert "arrow_show" in out

    @pytest.mark.parametrize(
        "new_value, result", (((1, 0, 1), (1, 0, 1)), ([0, 1, 0], (0, 1, 0)), ("#FF0000", (1, 0, 0)))
    )
    def test_label_color(self, new_value, result):
        _, annotation = make_annotation()

        annotation.label_color = new_value
        assert annotation.label_color == result

    @pytest.mark.parametrize("new_value", ((1, 0, 1, 0), ([0, 1, 0, 0], "FF0000")))
    def test_label_color_fail(self, new_value):
        _, annotation = make_annotation()

        with pytest.raises(ValueError):
            annotation.label_color = new_value

    @pytest.mark.parametrize(
        "new_value, result", (((1, 0, 1), (1, 0, 1)), ([0, 1, 0], (0, 1, 0)), ("#FF0000", (1, 0, 0)))
    )
    def test_patch_color(self, new_value, result):
        _, annotation = make_annotation()

        annotation.patch_color = new_value
        assert annotation.patch_color == result

    @pytest.mark.parametrize("new_value", ((1, 0, 1, 0), ([0, 1, 0, 0], "FF0000")))
    def test_patch_color_fail(self, new_value):
        _, annotation = make_annotation()

        with pytest.raises(ValueError):
            annotation.patch_color = new_value

    @pytest.mark.parametrize("new_value", (True, False))
    def test_arrow_show(self, new_value):
        _, annotation = make_annotation()

        # change name
        annotation.arrow_show = new_value
        assert annotation.arrow_show is new_value

    @pytest.mark.parametrize("new_value", (0, 1, "true"))
    def test_arrow_show_fail(self, new_value):
        _, annotation = make_annotation()

        # change name
        with pytest.raises(ValueError):
            annotation.arrow_show = new_value

    @pytest.mark.parametrize("new_value", (True, False))
    def test_patch_show(self, new_value):
        _, annotation = make_annotation()

        # change name
        annotation.patch_show = new_value
        assert annotation.patch_show is new_value

    @pytest.mark.parametrize("new_value", (0, 1, "true"))
    def test_patch_show_fail(self, new_value):
        _, annotation = make_annotation()

        # change name
        with pytest.raises(ValueError):
            annotation.patch_show = new_value

    @pytest.mark.parametrize("values", ([(0, 0), (3, 3), -3, -3], [(0, 0), (14, 0), -14, 0], [(3, 3), (0, 0), 3, 3]))
    def test_arrow_position(self, values):
        _, annotation = make_annotation()
        marker_position, label_position, dx, dy = values

        annotation.marker_position = marker_position
        annotation.label_position = label_position

        arrow_pos = annotation.arrow_positions
        assert isinstance(arrow_pos, tuple)
        assert len(arrow_pos) == 4
        assert arrow_pos[0] == label_position[0]
        assert arrow_pos[1] == label_position[1]
        assert arrow_pos[2] == dx
        assert arrow_pos[3] == dy
