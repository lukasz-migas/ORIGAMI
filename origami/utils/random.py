import random
import string

__all__ = ["random_int_0_to_255", "randomIntegerGenerator", "randomStringGenerator"]


def random_int_0_to_255():
    return random.randint(0, 255)


def randomIntegerGenerator(min_int, max_int):
    return random.randint(min_int, max_int)


def randomStringGenerator(size=5, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _x in range(size))
