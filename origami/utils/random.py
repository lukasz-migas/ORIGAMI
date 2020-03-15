# -*- coding: utf-8 -*-
# __author__ lukasz.g.migas
# Standard library imports
# Standard library imports
# Standard library imports
import random
import string

__all__ = ["random_int_0_to_255", "get_random_int", "randomStringGenerator"]


def random_int_0_to_255():
    return random.randint(0, 255)


def get_random_int(min_int, max_int):
    return random.randint(min_int, max_int)


def randomStringGenerator(size=5, chars=string.ascii_uppercase + string.digits):
    return "".join(random.choice(chars) for _x in range(size))
