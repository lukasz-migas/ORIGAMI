from utils.screen import calculate_window_size


def test_calculate_window_size():
    expected_size_x, expected_size_y = 1920, 1080
    return_size_x, return_size_y = calculate_window_size((expected_size_x, expected_size_y), 0.8)

    assert expected_size_x == return_size_x and expected_size_y == return_size_y


def test_calculate_window_size_convert_proportion():
    expected_size_x, expected_size_y = 1920, 1080
    return_size_x, return_size_y = calculate_window_size((expected_size_x, expected_size_y), 80)

    assert expected_size_x == return_size_x and expected_size_y == return_size_y
