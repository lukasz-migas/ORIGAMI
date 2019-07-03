# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
"""Annotation object"""


class Annotation:
    """Class containing all metadata about a single annotation"""
    VERSION = 1

    def __init__(self):

        # position
        self.position_x = 0
        self.position_y = 0
        self.position_label_x = 0
        self.position_label_y = 0

        # visual information
        self.color = [1., 1., 1.]
        self.add_arrow = True
        self.show = True

        # meta information
        self.span_min = 0
        self.span_max = 0
        self.charge = 0
        self.label = ''

        # peak information
        self.peak_x = 0
        self.peak_y = 0
        self.peak_width = 0
        self.peak_width_height = 0
        self.left_ips = 0
        self.right_ips = 0
