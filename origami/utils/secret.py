# Standard library imports
import uuid


def get_short_hash():
    return str(uuid.uuid4().hex)
