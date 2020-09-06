# Standard library imports
import uuid
import hashlib
from typing import Dict
from typing import List
from typing import Tuple
from typing import Union


def get_short_hash():
    """Return short unique id"""
    return str(uuid.uuid4().hex)


def hash_obj(data: Union[List, Dict, Tuple, str, int, float]) -> str:
    """Hash python object"""
    # Prepare the project id hash
    hash_id = hashlib.md5()
    hash_id.update(repr(data).encode("utf-8"))
    return hash_id.hexdigest()
