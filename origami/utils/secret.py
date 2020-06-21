# Standard library imports
import uuid


def get_short_hash():
    """Return short unique id"""
    return str(uuid.uuid4().hex)
