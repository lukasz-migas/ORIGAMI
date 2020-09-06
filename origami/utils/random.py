"""Get random numbers"""
# Standard library imports
import random

__all__ = ["random_int_0_to_255", "get_random_int"]


def random_int_0_to_255():
    """Get random number in the range from 0-255"""
    return random.randint(0, 255)


def get_random_int(min_int: int = 0, max_int: int = 255):
    """Get random integer"""
    return random.randint(min_int, max_int)
