from utils.screen import calculate_window_size


class TestScreen(object):
    @staticmethod
    def test_calculate_window_size():
        return_size_x, return_size_y = calculate_window_size((1920, 1080), 0.8)
        expected_size_x, expected_size_y = 1536, 864

        assert expected_size_x == return_size_x and expected_size_y == return_size_y

        return_size_x, return_size_y = calculate_window_size((1920, 1080), 80)
        expected_size_x, expected_size_y = 1536, 864

        assert expected_size_x == return_size_x and expected_size_y == return_size_y

        return_size_x, return_size_y = calculate_window_size((1920, 1080), [80, 80])
        expected_size_x, expected_size_y = 1536, 864

        assert expected_size_x == return_size_x and expected_size_y == return_size_y
