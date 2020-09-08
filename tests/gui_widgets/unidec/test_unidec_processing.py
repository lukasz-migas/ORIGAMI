"""Test unidec processing functionality"""
# Local imports
from origami.widgets.unidec.processing.utilities import unidec_sort_mw_list


class TestUnidecUtilities:
    def test_unidec_sort_mw_list(self):
        item_list = [
            "MW: 25700.00 (52.00 %) [○]",
            "MW: 26700.00 (6.12 %) [▽]",
            "MW: 107800.00 (100.00 %) [△]",
            "MW: 128000.00 (4.75 %) [▷]",
        ]
        sorted_item_list = unidec_sort_mw_list(item_list, 0)
        for item in item_list:
            assert item in sorted_item_list

        sorted_item_list = unidec_sort_mw_list(item_list, 1)
        for item in item_list:
            assert item in sorted_item_list
